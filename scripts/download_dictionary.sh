#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DATA_DIR="$ROOT/dictionary-data"
BASE="https://raw.githubusercontent.com/LinXueyuanStdio/DictionaryData/master"
mkdir -p "$DATA_DIR"
curl -fsSL "$BASE/book.csv" -o "$DATA_DIR/book.csv"
curl -fsSL "$BASE/word.csv" -o "$DATA_DIR/word.csv"
curl -fsSL "$BASE/word_translation.csv" -o "$DATA_DIR/word_translation.csv"
curl -fsSL "$BASE/relation_book_word.zip" -o "$DATA_DIR/relation_book_word.zip"
python3 "$ROOT/scripts/import_dictionary.py"
