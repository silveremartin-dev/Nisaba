"""
Nisaba Central Pipeline CLI Orchestrator.
Executes end-to-end ingestion, compilation, linting, chronology solving, join discovery,
ledger extraction, and interactive visual browser generation.
"""

import argparse
import os
import sys

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.compiler.parser import ATFParser
from src.compiler.storage import StorageEngine
from src.linter.engine import LinterEngine
from src.chronos.solver import ChronosSolver
from src.authors.scribe_identifier import AuthorIdentifier
from src.joins.matcher import FragmentMatcher
from src.ledger.extractor import LedgerExtractor
from src.ledger.auditor import LedgerAuditor
from src.browser.renderer import TabletBrowserRenderer


def run_pipeline(
    input_atf: str = "data/raw/sample_cdli.atf",
    output_dir: str = "data/processed",
    generate_browser: bool = True,
    tool: str = "all",
) -> None:
    """Executes the full Nisaba analytical pipeline or an isolated tool."""
    print("=" * 70)
    print(f"[*] NISABA: Computational Engine for Sumerian Cuneiform [Tool: {tool}]")
    print("=" * 70)

    if not os.path.exists(input_atf):
        print(f"[-] Error: Input file '{input_atf}' not found.")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    # Ingestion is foundational
    parser = ATFParser()
    tablets = parser.parse_file(input_atf)

    # Tool 1: Kmer Parquet Engine (Compilation & Storage)
    if tool in ("all", "kmer-parquet"):
        print(f"\n[Tool 1/5: K-mer Parquet Engine] Compiling ATF: {input_atf}")
        print(f"      -> Ingested {len(tablets)} tablets.")
        db_path = os.path.join(output_dir, "nisaba.duckdb")
        storage = StorageEngine(db_path=db_path)
        parquet_paths = storage.export_tables(tablets, output_dir=output_dir)
        print(f"      -> Exported Columnar Parquet: {list(parquet_paths.keys())}")
        print(f"      -> Mounted DuckDB Database  : {db_path}")

        # Linter sub-audit
        linter = LinterEngine()
        linter_report = linter.audit_corpus(tablets)
        print(f"      -> Morphosyntactic Pass Rate: {linter_report.pass_rate:.1f}%")
    else:
        linter_report = None

    # Tool 2: Orphan Tablet Resolver (Chronos Macro-Chronology + Scribe Identification)
    estimates = None
    attributions = None
    if tool in ("all", "orphan-resolver"):
        print("\n[Tool 2/5: Orphan Tablet Resolver] Solving Dates & Scribe Lineages...")
        solver = ChronosSolver()
        estimates = solver.fit_and_resolve(tablets)
        dated_count = sum(1 for e in estimates if e.status == "CERTIFIED_DATED")
        inferred_count = sum(1 for e in estimates if e.status == "ESTIMATED")
        print(f"      -> Certified Dates  : {dated_count}")
        print(f"      -> Inferred Dates   : {inferred_count}")
        solver.to_dataframe(estimates).to_parquet(os.path.join(output_dir, "chronos_estimates.parquet"), index=False)

        author_id = AuthorIdentifier()
        attributions = author_id.attribute_corpus(tablets)
        attr_count = sum(1 for a in attributions if a.identified_scribe is not None)
        print(f"      -> Attributed Scribes: {attr_count} / {len(tablets)}")
        author_id.to_dataframe(attributions).to_parquet(os.path.join(output_dir, "author_attributions.parquet"), index=False)

    # Tool 3: Tablet Joiner (Sequence Alignment & Virtual Joins)
    joins = None
    if tool in ("all", "joins"):
        print("\n[Tool 3/5: Tablet Joiner] Rapprochement de fragments cassés (k-mer BLAST)...")
        matcher = FragmentMatcher(min_similarity=0.30)
        joins = matcher.find_joins(tablets)
        print(f"      -> Candidate Joins Found: {len(joins)}")
        for j in joins[:3]:
            print(f"         * {j.id_text_a} <-> {j.id_text_b} (sim: {j.similarity_score:.2f}, type: {j.join_type})")
        df_joins = matcher.to_dataframe(joins)
        if not df_joins.empty:
            df_joins.to_parquet(os.path.join(output_dir, "virtual_joins.parquet"), index=False)

    # Tool 4: Ur III Economic Ledger (Double-Entry Balance Auditor)
    transactions = None
    if tool in ("all", "ledger"):
        print("\n[Tool 4/5: Economic Ledger] Réconciliation comptable d'Ur III...")
        extractor = LedgerExtractor()
        transactions = extractor.extract_corpus(tablets)
        auditor = LedgerAuditor()
        balances = auditor.compute_balances(transactions)
        print(f"      -> Transactions Extracted : {len(transactions)}")
        print(f"      -> Audited Officer Balances: {len(balances)}")
        extractor.to_dataframe(transactions).to_parquet(os.path.join(output_dir, "transactions.parquet"), index=False)
        auditor.to_dataframe(balances).to_parquet(os.path.join(output_dir, "officer_balances.parquet"), index=False)

    # Tool 5: Tablet Visual Browser (Interactive HTML)
    if (tool in ("all", "browser")) and generate_browser:
        print("\n[Tool 5/5: Tablet Visual Browser] Generating Interactive Viewer...")
        renderer = TabletBrowserRenderer()
        html_out = os.path.join(output_dir, "browser.html")
        renderer.render_corpus(
            tablets=tablets,
            linter_report=linter_report,
            estimates=estimates,
            joins=joins,
            transactions=transactions,
            attributions=attributions,
            output_filepath=html_out,
        )
        print(f"      -> Browser generated: {html_out}")

    print("\n" + "=" * 70)
    print(f"[OK] NISABA EXECUTION FINISHED: Tool '{tool}' Complete")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Nisaba Cuneiform Computational Suite (5 Tools)")
    parser.add_argument("--tool", default="all", choices=["all", "kmer-parquet", "orphan-resolver", "joins", "ledger", "browser"],
                        help="Select one of the 5 Nisaba tools to execute")
    parser.add_argument("--input", default="data/raw/sample_cdli.atf", help="Path to input CDLI ATF file")
    parser.add_argument("--output_dir", default="data/processed", help="Path to output processed directory")
    parser.add_argument("--no_browser", action="store_true", help="Skip generating HTML browser")
    args = parser.parse_args()

    run_pipeline(
        input_atf=args.input,
        output_dir=args.output_dir,
        generate_browser=not args.no_browser,
        tool=args.tool,
    )


if __name__ == "__main__":
    main()
