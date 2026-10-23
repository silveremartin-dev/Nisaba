"""
Unit and integration tests for BatchCompiler.
Verifies chunked streaming compilation to Parquet tables and DuckDB mounting.
"""

import os
import tempfile
import duckdb
import pytest

from src.compiler.batch_compiler import BatchCompiler


def test_batch_compiler_streaming():
    sample_atf = "data/raw/sample_cdli.atf"
    assert os.path.exists(sample_atf)

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_nisaba.duckdb")
        # Use a small batch size of 3 to force multiple flushes
        compiler = BatchCompiler(db_path=db_path, batch_size=3)

        progress_calls = []

        def callback(tabs, lines, signs, elapsed):
            progress_calls.append((tabs, lines, signs))

        metrics = compiler.compile_corpus(
            input_filepath=sample_atf,
            output_dir=tmpdir,
            limit=10,
            progress_callback=callback,
        )

        assert metrics["total_tablets"] == 10
        assert metrics["total_lines"] > 0
        assert metrics["total_signs"] > 0
        assert metrics["total_kmers"] > 0
        assert len(progress_calls) >= 3  # Multiple batches flushed

        # Check Parquet files created
        for tbl in ["tablets", "lines", "signs", "kmers"]:
            pfile = os.path.join(tmpdir, f"{tbl}.parquet")
            assert os.path.exists(pfile)
            assert os.path.getsize(pfile) > 0

        # Check DuckDB tables
        con = duckdb.connect(db_path)
        tables = [r[0] for r in con.execute("SHOW TABLES;").fetchall()]
        assert "tablets" in tables
        assert "lines" in tables
        assert "signs" in tables
        assert "kmers" in tables

        tab_count = con.execute("SELECT COUNT(*) FROM tablets;").fetchone()[0]
        assert tab_count == 10
        con.close()
