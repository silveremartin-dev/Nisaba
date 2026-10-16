"""
Storage engine for Nisaba.
Serializes parsed AST records into Apache Parquet columnar files and mounts them in DuckDB.
"""

import os
from typing import Dict, List, Optional
import duckdb
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from src.compiler.parser import TabletRecord


class StorageEngine:
    """Manages Parquet and DuckDB persistence for compiled cuneiform corpora."""

    def __init__(self, db_path: str = "data/processed/nisaba.duckdb"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)

    def export_tables(self, tablets: List[TabletRecord], output_dir: str = "data/processed") -> Dict[str, str]:
        """Converts TabletRecords into columnar DataFrames and writes Parquet files."""
        os.makedirs(output_dir, exist_ok=True)

        tablets_data = []
        lines_data = []
        signs_data = []

        for tab in tablets:
            tablets_data.append({
                "id_text": tab.id_text,
                "designation": tab.designation,
                "language": tab.language,
                "period": tab.period,
                "provenance": tab.provenance,
                "line_count": len(tab.lines),
                "has_date": tab.has_date,
            })

            for line in tab.lines:
                lines_data.append({
                    "id_line": line.id_line,
                    "id_text": line.id_text,
                    "surface": line.surface,
                    "line_number": line.line_number,
                    "line_label": line.line_label,
                    "raw_text": line.raw_text,
                    "normalized_text": line.normalized_text,
                    "is_damaged": line.is_damaged,
                    "sign_count": len(line.signs),
                })

                for sign in line.signs:
                    signs_data.append({
                        "id_sign": sign.id_sign,
                        "id_line": sign.id_line,
                        "sign_index": sign.sign_index,
                        "token": sign.token,
                        "clean_value": sign.clean_value,
                        "sign_type": sign.sign_type,
                        "damage_flag": sign.damage_flag or "",
                        "is_broken": sign.is_broken,
                    })

        df_tablets = pd.DataFrame(tablets_data)
        df_lines = pd.DataFrame(lines_data)
        df_signs = pd.DataFrame(signs_data)

        paths = {
            "tablets": os.path.join(output_dir, "tablets.parquet"),
            "lines": os.path.join(output_dir, "lines.parquet"),
            "signs": os.path.join(output_dir, "signs.parquet"),
        }

        df_tablets.to_parquet(paths["tablets"], index=False)
        df_lines.to_parquet(paths["lines"], index=False)
        df_signs.to_parquet(paths["signs"], index=False)

        # Ingest into DuckDB
        self._ingest_to_duckdb(paths)

        return paths

    def _ingest_to_duckdb(self, parquet_paths: Dict[str, str]) -> None:
        """Mounts Parquet files into DuckDB tables."""
        con = duckdb.connect(self.db_path)
        try:
            for table_name, ppath in parquet_paths.items():
                p_normalized = ppath.replace("\\", "/")
                con.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM read_parquet('{p_normalized}');")
        finally:
            con.close()

    def query(self, sql_query: str) -> pd.DataFrame:
        """Executes analytical SQL query against the DuckDB store."""
        con = duckdb.connect(self.db_path)
        try:
            return con.execute(sql_query).df()
        finally:
            con.close()
