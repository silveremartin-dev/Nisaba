"""
Automated downloader for the official CDLI bulk ATF database dump.
Source: https://github.com/cdli-gh/data/raw/master/cdliatf_unblocked.atf
"""

import os
import sys
import requests

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


CDLI_DUMP_URL = "https://github.com/cdli-gh/data/raw/master/cdliatf_unblocked.atf"
DEFAULT_TARGET = "data/raw/cdliatf_unblocked.atf"


def download_dump(target_path: str = DEFAULT_TARGET) -> str:
    """Downloads the full unblocked CDLI ATF dump (~150 MB)."""
    os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
    print(f"📥 Connecting to CDLI data repository: {CDLI_DUMP_URL}")
    print(f"   Target path: {target_path}")

    response = requests.get(CDLI_DUMP_URL, stream=True, timeout=60)
    response.raise_for_status()

    total_bytes = int(response.headers.get("content-length", 0))
    downloaded = 0
    chunk_size = 1024 * 1024  # 1 MB chunks

    with open(target_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if total_bytes > 0:
                    pct = (downloaded / total_bytes) * 100.0
                    print(f"   Downloaded: {downloaded / (1024*1024):.1f} MB / {total_bytes / (1024*1024):.1f} MB ({pct:.1f}%)", end="\r")
                else:
                    print(f"   Downloaded: {downloaded / (1024*1024):.1f} MB", end="\r")

    print(f"\n✅ CDLI dump successfully downloaded to: {target_path}")
    return target_path


if __name__ == "__main__":
    download_dump()
