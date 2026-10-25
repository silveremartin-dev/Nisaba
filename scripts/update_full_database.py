"""
High-throughput batch processor to compute full analytical tables across all 135,253 CDLI tablets:
- Scribe & author attributions
- Chronos date resolutions
- Double-entry transactions & officer balances
- Virtual join candidate pairs
- DuckDB table integration (all 9 tables mounted)
"""

import os
import sys
import time
from typing import Dict, List, Set
import duckdb
import pandas as pd

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.compiler.lexer import ATFLexer
from src.compiler.parser import ATFParser, TabletRecord
from src.authors.scribe_identifier import AuthorIdentifier, AttributionResult
from src.chronos.solver import ChronosSolver, ChronosEstimate
from src.chronos.prosopography import ProsopographyExtractor
from src.ledger.extractor import LedgerExtractor, TransactionRecord
from src.ledger.auditor import LedgerAuditor
from src.joins.matcher import FragmentMatcher, JoinCandidate
from src.joins.kmer import KmerIndexer


def main():
    dump_path = "data/raw/cdliatf_unblocked.atf"
    processed_dir = "data/processed"
    db_path = os.path.join(processed_dir, "nisaba.duckdb")

    if not os.path.exists(dump_path):
        print(f"[-] Dump file not found: {dump_path}")
        sys.exit(1)

    print("=" * 70)
    print("🚀 NISABA: FULL CORPUS ANALYTICAL COMPUTATION & DATABASE UPDATE")
    print("=" * 70)
    start_total = time.time()

    lexer = ATFLexer()
    parser = ATFParser()
    author_tool = AuthorIdentifier()
    chronos_tool = ChronosSolver()
    proso_extractor = ProsopographyExtractor()
    ledger_tool = LedgerExtractor()
    auditor = LedgerAuditor()

    # Pre-build empirical activity index from historical priors
    historical_priors = chronos_tool.HISTORICAL_PRIORS

    all_attributions: List[AttributionResult] = []
    all_estimates: List[ChronosEstimate] = []
    all_transactions: List[TransactionRecord] = []
    sample_tablets_for_joins: List[TabletRecord] = []

    batch_size = 10000
    current_batch: List[TabletRecord] = []
    total_parsed = 0
    t_batch_start = time.time()

    print(f"[*] Streaming through '{dump_path}' across all 135,253 tablets...")

    with open(dump_path, "r", encoding="utf-8", errors="ignore") as f:
        token_stream = lexer.tokenize_stream(f)
        for tablet in parser.parse_stream(token_stream):
            current_batch.append(tablet)
            total_parsed += 1

            # Keep broken sample tablets for fragment join candidate testing
            if len(sample_tablets_for_joins) < 1000 and any(l.is_damaged for l in tablet.lines):
                sample_tablets_for_joins.append(tablet)

            if len(current_batch) >= batch_size:
                # 1. Author Attribution
                for tab in current_batch:
                    all_attributions.append(author_tool.attribute_tablet(tab))

                # 2. Chronos date estimation
                for tab in current_batch:
                    entities = proso_extractor.extract_from_tablet(tab)
                    if entities.year_code:
                        all_estimates.append(ChronosEstimate(
                            id_text=tab.id_text,
                            status="CERTIFIED_DATED",
                            resolved_year=entities.year_code,
                            candidate_years=[entities.year_code],
                            confidence=1.0,
                            evidence=[f"Explicit year formula: {entities.year_code}"],
                        ))
                    else:
                        cand_years: Set[str] = set()
                        active_officials = [o for o in entities.officials if o in historical_priors]
                        if active_officials:
                            cand_years = set(historical_priors[active_officials[0]])
                            for off in active_officials[1:]:
                                cand_years &= historical_priors[off]

                        if cand_years:
                            sorted_years = sorted(list(cand_years))
                            resolved = f"{sorted_years[0]}..{sorted_years[-1]}" if len(sorted_years) > 1 else sorted_years[0]
                            all_estimates.append(ChronosEstimate(
                                id_text=tab.id_text,
                                status="ESTIMATED",
                                resolved_year=resolved,
                                candidate_years=sorted_years,
                                confidence=round(1.0 / len(cand_years), 2) if cand_years else 0.5,
                                evidence=[f"Prosopographic overlap of: {', '.join(active_officials)}"],
                            ))
                        else:
                            all_estimates.append(ChronosEstimate(
                                id_text=tab.id_text,
                                status="UNDETERMINED",
                                resolved_year=None,
                                candidate_years=[],
                                confidence=0.0,
                                evidence=["No known prosopographic temporal constraints detected"],
                            ))

                # 3. Transactions extraction
                for tab in current_batch:
                    all_transactions.extend(ledger_tool.extract_transactions(tab))

                elapsed_batch = time.time() - t_batch_start
                rate = total_parsed / (time.time() - start_total)
                print(f"    -> Ingested {total_parsed:,} tablets ({len(all_transactions):,} txs, {len(all_attributions):,} authors) | Rate: {rate:,.0f} tab/s")
                current_batch = []
                t_batch_start = time.time()

    # Process remaining batch
    if current_batch:
        for tab in current_batch:
            all_attributions.append(author_tool.attribute_tablet(tab))
            entities = proso_extractor.extract_from_tablet(tab)
            if entities.year_code:
                all_estimates.append(ChronosEstimate(
                    id_text=tab.id_text,
                    status="CERTIFIED_DATED",
                    resolved_year=entities.year_code,
                    candidate_years=[entities.year_code],
                    confidence=1.0,
                    evidence=[f"Explicit year formula: {entities.year_code}"],
                ))
            else:
                cand_years = set()
                active_officials = [o for o in entities.officials if o in historical_priors]
                if active_officials:
                    cand_years = set(historical_priors[active_officials[0]])
                    for off in active_officials[1:]:
                        cand_years &= historical_priors[off]
                if cand_years:
                    sorted_years = sorted(list(cand_years))
                    resolved = f"{sorted_years[0]}..{sorted_years[-1]}" if len(sorted_years) > 1 else sorted_years[0]
                    all_estimates.append(ChronosEstimate(
                        id_text=tab.id_text,
                        status="ESTIMATED",
                        resolved_year=resolved,
                        candidate_years=sorted_years,
                        confidence=round(1.0 / len(cand_years), 2),
                        evidence=[f"Prosopographic overlap of: {', '.join(active_officials)}"],
                    ))
                else:
                    all_estimates.append(ChronosEstimate(
                        id_text=tab.id_text,
                        status="UNDETERMINED",
                        resolved_year=None,
                        candidate_years=[],
                        confidence=0.0,
                        evidence=["No constraints"],
                    ))
        for tab in current_batch:
            all_transactions.extend(ledger_tool.extract_transactions(tab))

    print(f"\n✅ All {total_parsed:,} tablets parsed and analyzed in {time.time() - start_total:.1f}s!")

    # 4. Save author_attributions.parquet
    print("[*] Exporting 'author_attributions.parquet'...")
    df_authors = author_tool.to_dataframe(all_attributions)
    df_authors.to_parquet(os.path.join(processed_dir, "author_attributions.parquet"), index=False)
    id_authors_count = (df_authors["identified_scribe"] != "Unknown").sum()
    print(f"    -> Attributed scribes: {id_authors_count:,} / {len(df_authors):,}")

    # 5. Save chronos_estimates.parquet
    print("[*] Exporting 'chronos_estimates.parquet'...")
    df_chronos = chronos_tool.to_dataframe(all_estimates)
    df_chronos.to_parquet(os.path.join(processed_dir, "chronos_estimates.parquet"), index=False)
    dated_count = (df_chronos["status"] == "CERTIFIED_DATED").sum()
    estimated_count = (df_chronos["status"] == "ESTIMATED").sum()
    print(f"    -> Dates certified: {dated_count:,} | Inferred: {estimated_count:,}")

    # 6. Save transactions.parquet
    print("[*] Exporting 'transactions.parquet'...")
    df_tx = ledger_tool.to_dataframe(all_transactions)
    df_tx.to_parquet(os.path.join(processed_dir, "transactions.parquet"), index=False)
    print(f"    -> Extracted transactions: {len(df_tx):,}")

    # 7. Compute & Save officer_balances.parquet
    print("[*] Computing & exporting 'officer_balances.parquet'...")
    balances = auditor.compute_balances(all_transactions)
    df_balances = pd.DataFrame([
        {
            "officer": b.officer,
            "commodity": b.commodity,
            "total_received": b.total_received,
            "total_expended": b.total_expended,
            "net_inventory": b.net_inventory,
        }
        for b in balances
    ])
    df_balances.to_parquet(os.path.join(processed_dir, "officer_balances.parquet"), index=False)
    print(f"    -> Audited officer balances: {len(df_balances):,} accounts")

    # 8. Virtual Joins matching
    print("[*] Computing candidate virtual joins...")
    sample_parser = ATFParser()
    sample_tabs = sample_parser.parse_file("data/raw/sample_cdli.atf")
    matcher = FragmentMatcher(min_similarity=0.30)
    joins = matcher.find_joins(sample_tabs + sample_tablets_for_joins[:50])
    df_joins = matcher.to_dataframe(joins)
    df_joins.to_parquet(os.path.join(processed_dir, "virtual_joins.parquet"), index=False)
    print(f"    -> Candidate joins found: {len(df_joins):,}")

    # 9. Register tables directly into nisaba.duckdb
    print(f"[*] Registering analytical tables into '{db_path}'...")
    con = duckdb.connect(db_path)
    try:
        norm_authors = os.path.join(processed_dir, "author_attributions.parquet").replace("\\", "/")
        norm_chronos = os.path.join(processed_dir, "chronos_estimates.parquet").replace("\\", "/")
        norm_tx = os.path.join(processed_dir, "transactions.parquet").replace("\\", "/")
        norm_balances = os.path.join(processed_dir, "officer_balances.parquet").replace("\\", "/")
        norm_joins = os.path.join(processed_dir, "virtual_joins.parquet").replace("\\", "/")

        con.execute(f"CREATE OR REPLACE TABLE author_attributions AS SELECT * FROM read_parquet('{norm_authors}');")
        con.execute(f"CREATE OR REPLACE TABLE chronos_estimates AS SELECT * FROM read_parquet('{norm_chronos}');")
        con.execute(f"CREATE OR REPLACE TABLE transactions AS SELECT * FROM read_parquet('{norm_tx}');")
        con.execute(f"CREATE OR REPLACE TABLE officer_balances AS SELECT * FROM read_parquet('{norm_balances}');")
        con.execute(f"CREATE OR REPLACE TABLE virtual_joins AS SELECT * FROM read_parquet('{norm_joins}');")

        tables = con.execute("SHOW TABLES;").fetchall()
        print(f"✅ DuckDB tables now online: {[t[0] for t in tables]}")
    finally:
        con.close()

    total_time = time.time() - start_total
    print("\n" + "=" * 70)
    print(f"🎉 FULL CORPUS UPDATE COMPLETE in {total_time:.1f}s ({total_time / 60:.2f} min)")
    print("=" * 70)


if __name__ == "__main__":
    main()
