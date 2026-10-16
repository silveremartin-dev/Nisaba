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
from src.joins.matcher import FragmentMatcher
from src.ledger.extractor import LedgerExtractor
from src.ledger.auditor import LedgerAuditor
from src.browser.renderer import TabletBrowserRenderer


def run_pipeline(
    input_atf: str = "data/raw/sample_cdli.atf",
    output_dir: str = "data/processed",
    generate_browser: bool = True,
) -> None:
    """Executes the full Nisaba analytical pipeline."""
    print("=" * 70)
    print("[*] NISABA: Computational Engine for Sumerian Cuneiform")
    print("=" * 70)

    if not os.path.exists(input_atf):
        print(f"❌ Error: Input file '{input_atf}' not found.")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    # 1. Compilation
    print(f"\n[1/6] Ingesting & Compiling ATF: {input_atf}")
    parser = ATFParser()
    tablets = parser.parse_file(input_atf)
    print(f"      -> Ingested {len(tablets)} tablets.")

    db_path = os.path.join(output_dir, "nisaba.duckdb")
    storage = StorageEngine(db_path=db_path)
    parquet_paths = storage.export_tables(tablets, output_dir=output_dir)
    print(f"      -> Exported Parquet: {list(parquet_paths.keys())}")
    print(f"      -> Mounted DuckDB: {db_path}")

    # 2. Linter
    print("\n[2/6] Running Morphosyntactic & Bracket Linter...")
    linter = LinterEngine()
    linter_report = linter.audit_corpus(tablets)
    print(f"      -> Tablets Audited : {linter_report.total_tablets_audited}")
    print(f"      -> Pass Rate        : {linter_report.pass_rate:.1f}%")
    print(f"      -> Errors Detected  : {linter_report.total_errors}")
    print(f"      -> Warnings         : {linter_report.total_warnings}")

    df_issues = linter_report.to_dataframe()
    if not df_issues.empty:
        issues_path = os.path.join(output_dir, "linter_issues.parquet")
        df_issues.to_parquet(issues_path, index=False)
        print(f"      -> Saved issues: {issues_path}")

    # 3. Chronos Macro-Chronology
    print("\n[3/6] Solving Macro-Chronology & Undated Tablets...")
    solver = ChronosSolver()
    estimates = solver.fit_and_resolve(tablets)
    dated_count = sum(1 for e in estimates if e.status == "CERTIFIED_DATED")
    inferred_count = sum(1 for e in estimates if e.status == "ESTIMATED")
    print(f"      -> Certified Dates  : {dated_count}")
    print(f"      -> Inferred Dates   : {inferred_count}")

    df_chronos = solver.to_dataframe(estimates)
    chronos_path = os.path.join(output_dir, "chronos_estimates.parquet")
    df_chronos.to_parquet(chronos_path, index=False)
    print(f"      -> Saved estimates: {chronos_path}")

    # 4. Fragment Joins
    print("\n[4/6] Running Sequence Alignment & Virtual Join Matcher...")
    matcher = FragmentMatcher(min_similarity=0.30)
    joins = matcher.find_joins(tablets)
    print(f"      -> Candidate Joins Found: {len(joins)}")
    for j in joins[:3]:
        print(f"         * {j.id_text_a} <-> {j.id_text_b} (sim: {j.similarity_score:.2f}, type: {j.join_type})")

    df_joins = matcher.to_dataframe(joins)
    if not df_joins.empty:
        joins_path = os.path.join(output_dir, "virtual_joins.parquet")
        df_joins.to_parquet(joins_path, index=False)
        print(f"      -> Saved joins: {joins_path}")

    # 5. Ledger Extraction
    print("\n[5/6] Extracting Ur III Commodity Transactions & Balances...")
    extractor = LedgerExtractor()
    transactions = extractor.extract_corpus(tablets)
    auditor = LedgerAuditor()
    balances = auditor.compute_balances(transactions)
    print(f"      -> Transactions Extracted : {len(transactions)}")
    print(f"      -> Audited Officer Balances: {len(balances)}")

    df_tx = extractor.to_dataframe(transactions)
    df_tx.to_parquet(os.path.join(output_dir, "transactions.parquet"), index=False)
    df_bal = auditor.to_dataframe(balances)
    df_bal.to_parquet(os.path.join(output_dir, "officer_balances.parquet"), index=False)

    # 6. Tablet Visual Browser
    if generate_browser:
        print("\n[6/6] Generating Interactive Tablet Visual Browser...")
        renderer = TabletBrowserRenderer()
        html_out = os.path.join(output_dir, "browser.html")
        renderer.render_corpus(
            tablets=tablets,
            linter_report=linter_report,
            estimates=estimates,
            joins=joins,
            transactions=transactions,
            output_filepath=html_out,
        )
        print(f"      -> Browser generated: {html_out}")

    print("\n" + "=" * 70)
    print("[OK] NISABA PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Nisaba Cuneiform Computational Pipeline")
    parser.add_argument("--input", default="data/raw/sample_cdli.atf", help="Path to input CDLI ATF file")
    parser.add_argument("--output_dir", default="data/processed", help="Path to output processed directory")
    parser.add_argument("--no_browser", action="store_true", help="Skip generating HTML browser")
    args = parser.parse_args()

    run_pipeline(
        input_atf=args.input,
        output_dir=args.output_dir,
        generate_browser=not args.no_browser,
    )


if __name__ == "__main__":
    main()
