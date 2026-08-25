#!/usr/bin/env python3
"""Ensure dictionary.db exists and is up to date."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "dictionary-data"
OUTPUT = ROOT / "data" / "dictionary.db"
IMPORT = ROOT / "scripts" / "import_dictionary.py"


def main() -> None:
    required = [
        DATA_DIR / "book.csv",
        DATA_DIR / "word.csv",
        DATA_DIR / "word_translation.csv",
    ]
    has_zip = (DATA_DIR / "relation_book_word.zip").exists()
    has_relation = (DATA_DIR / "relation_book_word.csv").exists()

    if not all(path.exists() for path in required) or not (has_zip or has_relation):
        if OUTPUT.exists():
            print(f"Using existing database: {OUTPUT}")
            return
        print("Dictionary source files missing. Run download/import first.", file=sys.stderr)
        sys.exit(1)

    source_mtime = max(path.stat().st_mtime for path in required)
    if OUTPUT.exists() and OUTPUT.stat().st_mtime >= source_mtime:
        print(f"Dictionary database is up to date: {OUTPUT}")
        return

    print("Building dictionary database...")
    subprocess.check_call([sys.executable, str(IMPORT)], cwd=ROOT)
    print("Dictionary database ready.")


if __name__ == "__main__":
    main()
