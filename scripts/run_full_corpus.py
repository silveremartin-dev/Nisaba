"""
Batch executor to run the complete Nisaba pipeline on the full CDLI corpus.
Supports both end-to-end multi-engine runs and high-throughput constant-memory streaming compilation.
"""

import argparse
import os
import sys

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.compiler.batch_compiler import BatchCompiler
from src.pipeline import run_pipeline


def main():
    parser = argparse.ArgumentParser(description="Nisaba Full Corpus Processor & Batch Compiler")
    parser.add_argument("--mode", default="batch-compile", choices=["batch-compile", "pipeline"],
                        help="Execution mode: 'batch-compile' (constant-memory streaming) or 'pipeline' (5-tool suite)")
    parser.add_argument("--input", default=None, help="Path to input CDLI ATF file")
    parser.add_argument("--output_dir", default="data/processed", help="Path to output processed directory")
    parser.add_argument("--batch-size", type=int, default=5000, help="Batch size for incremental parquet flushing")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of tablets to process (None for all)")
    parser.add_argument("--no_browser", action="store_true", help="Skip generating HTML browser in pipeline mode")
    args = parser.parse_args()

    raw_dump = "data/raw/cdliatf_unblocked.atf"
    sample_dump = "data/raw/sample_cdli.atf"

    input_file = args.input or (raw_dump if os.path.exists(raw_dump) else sample_dump)
    if input_file == sample_dump and not args.input:
        print(f"ℹ️ Full dump '{raw_dump}' not found on disk. Falling back to sample '{sample_dump}'.")
        print("   To run on the full 135,000+ tablets, run: py scripts/download_cdli_dump.py first.\n")

    print(f"[*] Nisaba Processing Target: {input_file} (Mode: {args.mode})")

    if args.mode == "batch-compile":
        db_path = os.path.join(args.output_dir, "nisaba.duckdb")
        compiler = BatchCompiler(db_path=db_path, batch_size=args.batch_size)

        def report_progress(tabs, lines, signs, elapsed):
            rate = tabs / elapsed if elapsed > 0 else 0
            print(f"    -> [Streaming] {tabs:,} tablets ({lines:,} lines, {signs:,} signs) in {elapsed:.1f}s ({rate:,.0f} tab/s)")

        print(f"[*] Starting streaming compilation to Parquet & DuckDB (batch size: {args.batch_size})...")
        metrics = compiler.compile_corpus(
            input_filepath=input_file,
            output_dir=args.output_dir,
            limit=args.limit,
            progress_callback=report_progress,
        )
        print("\n" + "=" * 70)
        print("✅ FULL CORPUS BATCH COMPILATION COMPLETE:")
        print(f"   * Tablets Ingested : {metrics['total_tablets']:,}")
        print(f"   * Lines Extracted  : {metrics['total_lines']:,}")
        print(f"   * Signs Classified : {metrics['total_signs']:,}")
        print(f"   * K-mers Generated : {metrics['total_kmers']:,}")
        print(f"   * Total Time       : {metrics['elapsed_seconds']:.2f} s")
        print(f"   * Speed            : {metrics['throughput_tablets_sec']:,.0f} tablets/s ({metrics['throughput_lines_sec']:,.0f} lines/s)")
        print(f"   * DuckDB Database  : {metrics['duckdb_path']}")
        print("=" * 70)

    else:
        run_pipeline(
            input_atf=input_file,
            output_dir=args.output_dir,
            generate_browser=not args.no_browser,
        )


if __name__ == "__main__":
    main()
