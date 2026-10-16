"""End-to-end integration test for the Nisaba pipeline."""

import os
import pytest
from src.pipeline import run_pipeline


def test_full_pipeline_run(tmp_path):
    out_dir = str(tmp_path / "processed")
    run_pipeline(
        input_atf="data/raw/sample_cdli.atf",
        output_dir=out_dir,
        generate_browser=True,
    )

    # Verify that all certified output artifacts exist
    assert os.path.exists(os.path.join(out_dir, "tablets.parquet"))
    assert os.path.exists(os.path.join(out_dir, "lines.parquet"))
    assert os.path.exists(os.path.join(out_dir, "signs.parquet"))
    assert os.path.exists(os.path.join(out_dir, "nisaba.duckdb"))
    assert os.path.exists(os.path.join(out_dir, "chronos_estimates.parquet"))
    assert os.path.exists(os.path.join(out_dir, "author_attributions.parquet"))
    assert os.path.exists(os.path.join(out_dir, "transactions.parquet"))
    assert os.path.exists(os.path.join(out_dir, "officer_balances.parquet"))
    assert os.path.exists(os.path.join(out_dir, "browser.html"))


def test_selective_tool_runs(tmp_path):
    out_dir = str(tmp_path / "proc_tools")
    # Test Tool 1: kmer-parquet
    run_pipeline(
        input_atf="data/raw/sample_cdli.atf",
        output_dir=out_dir,
        generate_browser=False,
        tool="kmer-parquet",
    )
    assert os.path.exists(os.path.join(out_dir, "kmers.parquet"))
    assert os.path.exists(os.path.join(out_dir, "nisaba.duckdb"))

    # Test Tool 4: ledger
    run_pipeline(
        input_atf="data/raw/sample_cdli.atf",
        output_dir=out_dir,
        generate_browser=False,
        tool="ledger",
    )
    assert os.path.exists(os.path.join(out_dir, "transactions.parquet"))
    assert os.path.exists(os.path.join(out_dir, "officer_balances.parquet"))
