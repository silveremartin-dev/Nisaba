"""
Database and Parquet File Sharding & Auto-Reconstitution Utility for Nisaba.
Splits multi-megabyte DuckDB databases into GitHub-compliant chunks (< 45 MB)
and seamlessly reassembles them on-the-fly upon client startup with SHA-256 verification.
"""

from dataclasses import dataclass
import hashlib
import json
import os
import shutil
from typing import Dict, List, Optional


@dataclass
class ShardManifest:
    target_filename: str
    total_size_bytes: int
    expected_sha256: str
    chunk_size_bytes: int
    total_parts: int
    parts: List[Dict[str, any]]


class FileSharder:
    """Handles splitting large database files into Git-safe shards and instant reassembly."""

    DEFAULT_CHUNK_SIZE_MB = 40  # Well below GitHub's 50MB warning and 100MB hard limit

    @staticmethod
    def compute_sha256(filepath: str) -> str:
        """Computes hexadecimal SHA-256 hash of a file."""
        hasher = hashlib.sha256()
        with open(filepath, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    def split_file(
        self,
        source_path: str,
        output_dir: str = "data/shards",
        chunk_size_mb: int = DEFAULT_CHUNK_SIZE_MB,
    ) -> ShardManifest:
        """
        Splits a file into sequential .part001, .part002 chunks and generates a JSON manifest.
        """
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Source file '{source_path}' does not exist.")

        os.makedirs(output_dir, exist_ok=True)
        filename = os.path.basename(source_path)
        total_size = os.path.getsize(source_path)
        full_hash = self.compute_sha256(source_path)
        chunk_size_bytes = chunk_size_mb * 1024 * 1024

        parts: List[Dict[str, any]] = []
        part_idx = 1

        with open(source_path, "rb") as src:
            while True:
                data = src.read(chunk_size_bytes)
                if not data:
                    break

                part_filename = f"{filename}.part{part_idx:03d}"
                part_path = os.path.join(output_dir, part_filename)

                part_hasher = hashlib.sha256(data)
                part_hash = part_hasher.hexdigest()

                with open(part_path, "wb") as dst:
                    dst.write(data)

                parts.append({
                    "part_index": part_idx,
                    "filename": part_filename,
                    "size_bytes": len(data),
                    "sha256": part_hash,
                })
                part_idx += 1

        manifest = ShardManifest(
            target_filename=filename,
            total_size_bytes=total_size,
            expected_sha256=full_hash,
            chunk_size_bytes=chunk_size_bytes,
            total_parts=len(parts),
            parts=parts,
        )

        manifest_path = os.path.join(output_dir, f"{filename}.manifest.json")
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump({
                "target_filename": manifest.target_filename,
                "total_size_bytes": manifest.total_size_bytes,
                "expected_sha256": manifest.expected_sha256,
                "chunk_size_bytes": manifest.chunk_size_bytes,
                "total_parts": manifest.total_parts,
                "parts": manifest.parts,
            }, f, indent=2)

        return manifest

    def reassemble_file(
        self,
        manifest_path: str,
        output_filepath: Optional[str] = None,
        verify_checksum: bool = True,
    ) -> str:
        """
        Reconstructs the original file from shards listed in the manifest.
        """
        if not os.path.exists(manifest_path):
            raise FileNotFoundError(f"Manifest '{manifest_path}' not found.")

        with open(manifest_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        shards_dir = os.path.dirname(os.path.abspath(manifest_path))
        target_name = meta["target_filename"]
        out_path = output_filepath or os.path.join(shards_dir, target_name)
        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)

        temp_out = out_path + ".tmp_reassemble"
        with open(temp_out, "wb") as dst:
            for part in sorted(meta["parts"], key=lambda x: x["part_index"]):
                part_file = os.path.join(shards_dir, part["filename"])
                if not os.path.exists(part_file):
                    raise FileNotFoundError(f"Missing required shard part: '{part_file}'")

                if verify_checksum:
                    actual_part_hash = self.compute_sha256(part_file)
                    if actual_part_hash != part["sha256"]:
                        raise ValueError(f"Checksum mismatch on part '{part['filename']}': expected {part['sha256']}, got {actual_part_hash}")

                with open(part_file, "rb") as src:
                    shutil.copyfileobj(src, dst)

        if verify_checksum:
            final_hash = self.compute_sha256(temp_out)
            if final_hash != meta["expected_sha256"]:
                if os.path.exists(temp_out):
                    os.remove(temp_out)
                raise ValueError(f"Final file integrity check failed! Expected {meta['expected_sha256']}, got {final_hash}")

        # Atomic replace
        if os.path.exists(out_path):
            os.remove(out_path)
        os.rename(temp_out, out_path)

        return out_path

    @classmethod
    def auto_bootstrap_database(
        cls,
        target_db: str = "data/processed/nisaba.duckdb",
        shards_dir: str = "data/shards",
    ) -> bool:
        """
        Checks if the database is missing or empty, and automatically reconstitutes it from local shards.
        Returns True if database is available or successfully reconstituted.
        """
        if os.path.exists(target_db) and os.path.getsize(target_db) > 10240:
            return True

        # Check for manifest in shards directory
        manifest_path = os.path.join(shards_dir, "nisaba.duckdb.manifest.json")
        if os.path.exists(manifest_path):
            print(f"[*] Reassembling '{target_db}' from Git-safe shards in '{shards_dir}'...")
            sharder = cls()
            sharder.reassemble_file(manifest_path, output_filepath=target_db)
            print(f"✅ Successfully reconstituted '{target_db}' ({os.path.getsize(target_db):,} bytes).")
            return True

        return False
