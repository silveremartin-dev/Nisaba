"""
Release Packaging & Sharding Utility for Nisaba.
Packages the full DuckDB database for GitHub distribution via:
1. Git-safe shard chunks (< 40 MB each) with SHA-256 manifests for instant on-the-fly reassembly.
2. Compressed tarball archive ready for GitHub Releases upload.
Usage:
    py scripts/package_release.py --mode shard
    py scripts/package_release.py --mode reassemble
    py scripts/package_release.py --mode tarball
"""

import argparse
import os
import sys
import tarfile
import time

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.storage.chunker import FileSharder


def main():
    parser = argparse.ArgumentParser(description="Nisaba Release Packaging & Sharding Utility")
    parser.add_argument("--mode", default="shard", choices=["shard", "reassemble", "tarball", "all"],
                        help="Action to perform: 'shard' (split for Git), 'reassemble' (merge shards), 'tarball' (for GitHub Release), or 'all'")
    parser.add_argument("--db-path", default="data/processed/nisaba.duckdb", help="Path to DuckDB database")
    parser.add_argument("--shards-dir", default="data/shards", help="Directory to store/read shards")
    parser.add_argument("--chunk-size-mb", type=int, default=40, help="Shard chunk size in MB (default 40MB)")
    parser.add_argument("--output-tar", default="data/processed/nisaba_full_release.tar.gz", help="Path to release tarball")
    args = parser.parse_args()

    sharder = FileSharder()

    if args.mode in ("shard", "all"):
        if not os.path.exists(args.db_path):
            print(f"❌ Error: Database '{args.db_path}' not found. Run compilation first.")
            sys.exit(1)

        print(f"[*] Sharding '{args.db_path}' into Git-safe chunks (<= {args.chunk_size_mb} MB)...")
        manifest = sharder.split_file(
            source_path=args.db_path,
            output_dir=args.shards_dir,
            chunk_size_mb=args.chunk_size_mb,
        )
        print("✅ Sharding complete:")
        print(f"   * Original Size : {manifest.total_size_bytes:,} bytes")
        print(f"   * SHA-256       : {manifest.expected_sha256}")
        print(f"   * Total Shards  : {manifest.total_parts} parts in '{args.shards_dir}'")
        for p in manifest.parts:
            print(f"     - {p['filename']}: {p['size_bytes']:,} bytes ({p['sha256'][:12]}...)")

    if args.mode in ("reassemble",):
        manifest_file = os.path.join(args.shards_dir, f"{os.path.basename(args.db_path)}.manifest.json")
        print(f"[*] Reassembling from manifest '{manifest_file}'...")
        out_file = sharder.reassemble_file(manifest_file, output_filepath=args.db_path)
        print(f"✅ Reassembly verified: '{out_file}' ({os.path.getsize(out_file):,} bytes)")

    if args.mode in ("tarball", "all"):
        if not os.path.exists(args.db_path):
            print(f"❌ Error: Database '{args.db_path}' not found.")
            sys.exit(1)

        print(f"[*] Compressing '{args.db_path}' into GitHub Release tarball: '{args.output_tar}'...")
        start_t = time.time()
        with tarfile.open(args.output_tar, "w:gz") as tar:
            tar.add(args.db_path, arcname=os.path.basename(args.db_path))
            for p in ["tablets.parquet", "lines.parquet", "signs.parquet", "kmers.parquet"]:
                ppath = os.path.join(os.path.dirname(args.db_path), p)
                if os.path.exists(ppath):
                    tar.add(ppath, arcname=p)
        elapsed = time.time() - start_t
        print(f"✅ Release tarball created in {elapsed:.1f}s:")
        print(f"   * File : {args.output_tar} ({os.path.getsize(args.output_tar):,} bytes)")


if __name__ == "__main__":
    main()
