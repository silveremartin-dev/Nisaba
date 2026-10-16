"""Tests for DuckDB SQL analytics across compiled cuneiform tables."""

import os
import pytest
from src.compiler.parser import ATFParser
from src.compiler.storage import StorageEngine


def test_duckdb_advanced_sql(tmp_path):
    parser = ATFParser()
    tablets = parser.parse_file("data/raw/sample_cdli.atf")

    db_path = str(tmp_path / "analytics.duckdb")
    storage = StorageEngine(db_path=db_path)
    storage.export_tables(tablets, output_dir=str(tmp_path))

    # 1. Join tablets and lines
    sql_lines_per_tablet = """
        SELECT t.id_text, t.designation, COUNT(l.id_line) as num_lines
        FROM tablets t
        JOIN lines l ON t.id_text = l.id_text
        GROUP BY t.id_text, t.designation
        ORDER BY num_lines DESC;
    """
    df_res = storage.query(sql_lines_per_tablet)
    assert len(df_res) == 15
    assert df_res.iloc[0]["num_lines"] >= 4

    # 2. Sign distribution analysis
    sql_signs = """
        SELECT sign_type, COUNT(*) as count
        FROM signs
        GROUP BY sign_type
        ORDER BY count DESC;
    """
    df_signs = storage.query(sql_signs)
    assert "NUMERIC" in df_signs["sign_type"].values
    assert "SYLLABLE" in df_signs["sign_type"].values
