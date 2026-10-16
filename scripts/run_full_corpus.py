"""
Batch executor to run the complete Nisaba pipeline on the full CDLI corpus.
"""

import os
import sys

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.pipeline import run_pipeline


def main():
    raw_dump = "data/raw/cdliatf_unblocked.atf"
    sample_dump = "data/raw/sample_cdli.atf"

    input_file = raw_dump if os.path.exists(raw_dump) else sample_dump
    if input_file == sample_dump:
        print(f"ℹ️ Full dump '{raw_dump}' not found on disk. Running on sample '{sample_dump}'.")
        print("   To run on the full 140,000 tablets, run: py scripts/download_cdli_dump.py first.\n")

    run_pipeline(
        input_atf=input_file,
        output_dir="data/processed",
        generate_browser=True,
    )


if __name__ == "__main__":
    main()
