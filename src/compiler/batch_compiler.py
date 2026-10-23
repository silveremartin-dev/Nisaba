"""
Batch and Chunked Streaming Compiler for Large-Scale CDLI Corpora.
Enables processing 100,000+ cuneiform tablets in constant memory using PyArrow ParquetWriter.
"""

import os
import sys
import time
from typing import Dict, Generator, List, Optional
import duckdb
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from src.compiler.lexer import ATFLexer
from src.compiler.parser import ATFParser, TabletRecord
from src.joins.kmer import KmerIndexer


class BatchCompiler:
    """Streams and compiles CDLI ATF archives in incremental batches directly to Parquet and DuckDB."""

    TABLET_SCHEMA = pa.schema([
        ("id_text", pa.string()),
        ("designation", pa.string()),
        ("language", pa.string()),
        ("period", pa.string()),
        ("provenance", pa.string()),
        ("line_count", pa.int64()),
        ("has_date", pa.bool_()),
    ])

    LINE_SCHEMA = pa.schema([
        ("id_line", pa.string()),
        ("id_text", pa.string()),
        ("surface", pa.string()),
        ("line_number", pa.int64()),
        ("line_label", pa.string()),
        ("raw_text", pa.string()),
        ("normalized_text", pa.string()),
        ("is_damaged", pa.bool_()),
        ("sign_count", pa.int64()),
        ("kmer_count", pa.int64()),
    ])

    SIGN_SCHEMA = pa.schema([
        ("id_sign", pa.string()),
        ("id_line", pa.string()),
        ("sign_index", pa.int64()),
        ("token", pa.string()),
        ("clean_value", pa.string()),
        ("sign_type", pa.string()),
        ("damage_flag", pa.string()),
        ("is_broken", pa.bool_()),
    ])

    KMER_SCHEMA = pa.schema([
        ("id_line", pa.string()),
        ("id_text", pa.string()),
        ("kmer", pa.string()),
    ])

    def __init__(self, db_path: str = "data/processed/nisaba.duckdb", batch_size: int = 5000):
        self.db_path = db_path
        self.batch_size = batch_size
        self.indexer = KmerIndexer(k=4)
        self.parser = ATFParser()
        self.lexer = ATFLexer()

    def stream_tablets_from_file(self, filepath: str, limit: Optional[int] = None) -> Generator[TabletRecord, None, None]:
        """Streams TabletRecord objects one-by-one from a large ATF file on disk."""
        count = 0
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            tokens = self.lexer.tokenize_stream((line for line in f))
            for tablet in self.parser.parse_stream(tokens):
                yield tablet
                count += 1
                if limit is not None and count >= limit:
                    break

    def compile_corpus(
        self,
        input_filepath: str,
        output_dir: str = "data/processed",
        limit: Optional[int] = None,
        progress_callback: Optional[callable] = None,
    ) -> Dict[str, any]:
        """
        Incrementally compiles an ATF file to columnar Parquet files and mounts them in DuckDB.
        Memory footprint remains constant regardless of corpus size.
        """
        os.makedirs(output_dir, exist_ok=True)
        paths = {
            "tablets": os.path.join(output_dir, "tablets.parquet"),
            "lines": os.path.join(output_dir, "lines.parquet"),
            "signs": os.path.join(output_dir, "signs.parquet"),
            "kmers": os.path.join(output_dir, "kmers.parquet"),
        }

        # Initialize ParquetWriters
        writer_tablets = pq.ParquetWriter(paths["tablets"], self.TABLET_SCHEMA, compression="snappy")
        writer_lines = pq.ParquetWriter(paths["lines"], self.LINE_SCHEMA, compression="snappy")
        writer_signs = pq.ParquetWriter(paths["signs"], self.SIGN_SCHEMA, compression="snappy")
        writer_kmers = pq.ParquetWriter(paths["kmers"], self.KMER_SCHEMA, compression="snappy")

        total_tablets = 0
        total_lines = 0
        total_signs = 0
        total_kmers = 0
        start_time = time.time()

        tablet_batch: List[dict] = []
        line_batch: List[dict] = []
        sign_batch: List[dict] = []
        kmer_batch: List[dict] = []

        try:
            for tablet in self.stream_tablets_from_file(input_filepath, limit=limit):
                tablet_batch.append({
                    "id_text": tablet.id_text,
                    "designation": tablet.designation,
                    "language": tablet.language,
                    "period": tablet.period,
                    "provenance": tablet.provenance,
                    "line_count": len(tablet.lines),
                    "has_date": tablet.has_date,
                })
                total_tablets += 1

                for line in tablet.lines:
                    line_kmers = self.indexer.extract_char_kmers(line.normalized_text)
                    for km in line_kmers:
                        kmer_batch.append({
                            "id_line": line.id_line,
                            "id_text": line.id_text,
                            "kmer": km,
                        })
                        total_kmers += 1

                    line_batch.append({
                        "id_line": line.id_line,
                        "id_text": line.id_text,
                        "surface": line.surface,
                        "line_number": line.line_number,
                        "line_label": line.line_label,
                        "raw_text": line.raw_text,
                        "normalized_text": line.normalized_text,
                        "is_damaged": line.is_damaged,
                        "sign_count": len(line.signs),
                        "kmer_count": len(line_kmers),
                    })
                    total_lines += 1

                    for sign in line.signs:
                        sign_batch.append({
                            "id_sign": sign.id_sign,
                            "id_line": sign.id_line,
                            "sign_index": sign.sign_index,
                            "token": sign.token,
                            "clean_value": sign.clean_value,
                            "sign_type": sign.sign_type,
                            "damage_flag": sign.damage_flag or "",
                            "is_broken": sign.is_broken,
                        })
                        total_signs += 1

                if len(tablet_batch) >= self.batch_size:
                    self._flush_batches(
                        writer_tablets, writer_lines, writer_signs, writer_kmers,
                        tablet_batch, line_batch, sign_batch, kmer_batch,
                    )
                    tablet_batch.clear()
                    line_batch.clear()
                    sign_batch.clear()
                    kmer_batch.clear()

                    if progress_callback:
                        elapsed = time.time() - start_time
                        progress_callback(total_tablets, total_lines, total_signs, elapsed)

            # Flush remaining records
            if tablet_batch:
                self._flush_batches(
                    writer_tablets, writer_lines, writer_signs, writer_kmers,
                    tablet_batch, line_batch, sign_batch, kmer_batch,
                )
                tablet_batch.clear()
                line_batch.clear()
                sign_batch.clear()
                kmer_batch.clear()

        finally:
            writer_tablets.close()
            writer_lines.close()
            writer_signs.close()
            writer_kmers.close()

        elapsed_total = time.time() - start_time

        # Mount in DuckDB
        self._mount_duckdb(paths)

        return {
            "total_tablets": total_tablets,
            "total_lines": total_lines,
            "total_signs": total_signs,
            "total_kmers": total_kmers,
            "elapsed_seconds": elapsed_total,
            "throughput_tablets_sec": total_tablets / elapsed_total if elapsed_total > 0 else 0,
            "throughput_lines_sec": total_lines / elapsed_total if elapsed_total > 0 else 0,
            "parquet_paths": paths,
            "duckdb_path": self.db_path,
        }

    def _flush_batches(
        self,
        writer_tablets: pq.ParquetWriter,
        writer_lines: pq.ParquetWriter,
        writer_signs: pq.ParquetWriter,
        writer_kmers: pq.ParquetWriter,
        tablet_batch: List[dict],
        line_batch: List[dict],
        sign_batch: List[dict],
        kmer_batch: List[dict],
    ) -> None:
        if tablet_batch:
            table = pa.Table.from_pandas(pd.DataFrame(tablet_batch), schema=self.TABLET_SCHEMA)
            writer_tablets.write_table(table)
        if line_batch:
            table = pa.Table.from_pandas(pd.DataFrame(line_batch), schema=self.LINE_SCHEMA)
            writer_lines.write_table(table)
        if sign_batch:
            table = pa.Table.from_pandas(pd.DataFrame(sign_batch), schema=self.SIGN_SCHEMA)
            writer_signs.write_table(table)
        if kmer_batch:
            table = pa.Table.from_pandas(pd.DataFrame(kmer_batch), schema=self.KMER_SCHEMA)
            writer_kmers.write_table(table)

    def _mount_duckdb(self, paths: Dict[str, str]) -> None:
        """Mounts the created Parquet tables into DuckDB views or tables."""
        con = duckdb.connect(self.db_path)
        try:
            for table_name, ppath in paths.items():
                p_norm = ppath.replace("\\", "/")
                con.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM read_parquet('{p_norm}');")
        finally:
            con.close()
