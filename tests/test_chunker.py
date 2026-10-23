"""
Tests for FileSharder sharding, manifest generation, and on-the-fly reassembly.
"""

import os
import tempfile
import pytest

from src.storage.chunker import FileSharder


def test_file_sharder_split_and_reassemble():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a test binary payload (e.g. 10 MB)
        original_file = os.path.join(tmpdir, "test_database.duckdb")
        payload = b"CUNEIFORM_DATA_BLOCK_" * 500000  # ~10.5 MB
        with open(original_file, "wb") as f:
            f.write(payload)

        shards_dir = os.path.join(tmpdir, "shards")
        sharder = FileSharder()

        # Split with 3 MB chunks to create 4 parts
        manifest = sharder.split_file(
            source_path=original_file,
            output_dir=shards_dir,
            chunk_size_mb=3,
        )

        assert manifest.total_parts >= 3
        assert manifest.total_size_bytes == len(payload)
        assert len(manifest.parts) == manifest.total_parts

        manifest_path = os.path.join(shards_dir, "test_database.duckdb.manifest.json")
        assert os.path.exists(manifest_path)

        # Verify all parts exist and are <= 3MB
        for part in manifest.parts:
            part_path = os.path.join(shards_dir, part["filename"])
            assert os.path.exists(part_path)
            assert os.path.getsize(part_path) <= 3 * 1024 * 1024
            assert os.path.getsize(part_path) > 0

        # Remove original file to test reassembly
        os.remove(original_file)
        assert not os.path.exists(original_file)

        # Reassemble
        reconstructed = sharder.reassemble_file(manifest_path, output_filepath=original_file)
        assert os.path.exists(reconstructed)
        assert os.path.getsize(reconstructed) == len(payload)

        # Byte-for-byte exact equality
        with open(reconstructed, "rb") as f:
            reconstructed_data = f.read()
        assert reconstructed_data == payload
        assert sharder.compute_sha256(reconstructed) == manifest.expected_sha256


def test_auto_bootstrap_database():
    with tempfile.TemporaryDirectory() as tmpdir:
        target_db = os.path.join(tmpdir, "processed", "nisaba.duckdb")
        shards_dir = os.path.join(tmpdir, "shards")

        # Fake a database and shard it
        fake_db = os.path.join(tmpdir, "nisaba.duckdb")
        with open(fake_db, "wb") as f:
            f.write(b"DUCKDB_RAW_BYTES_" * 1000)

        sharder = FileSharder()
        sharder.split_file(fake_db, output_dir=shards_dir, chunk_size_mb=1)

        # Target DB does not exist yet
        assert not os.path.exists(target_db)

        # Auto bootstrap
        success = FileSharder.auto_bootstrap_database(target_db=target_db, shards_dir=shards_dir)
        assert success is True
        assert os.path.exists(target_db)
