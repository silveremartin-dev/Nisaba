"""Tests for Parquet export and DuckDB integration."""

import os
import pytest
from src.compiler.parser import ATFParser
from src.compiler.storage import StorageEngine


def test_storage_export_and_query(tmp_path):
    parser = ATFParser()
    tablets = parser.parse_file("data/raw/sample_cdli.atf")

    db_path = str(tmp_path / "test_nisaba.duckdb")
    storage = StorageEngine(db_path=db_path)
    parquet_paths = storage.export_tables(tablets, output_dir=str(tmp_path))

    assert os.path.exists(parquet_paths["tablets"])
    assert os.path.exists(parquet_paths["lines"])
    assert os.path.exists(parquet_paths["signs"])
    assert os.path.exists(parquet_paths["kmers"])
    assert os.path.exists(db_path)

    # Test SQL execution
    df_count = storage.query("SELECT COUNT(*) AS total_tablets FROM tablets;")
    assert df_count.iloc[0]["total_tablets"] == 15

    df_signs = storage.query("SELECT sign_type, COUNT(*) as cnt FROM signs GROUP BY sign_type ORDER BY cnt DESC;")
    assert not df_signs.empty

    df_kmers = storage.query("SELECT kmer, COUNT(*) as freq FROM kmers GROUP BY kmer ORDER BY freq DESC LIMIT 5;")
    assert not df_kmers.empty
    assert len(df_kmers) <= 5
