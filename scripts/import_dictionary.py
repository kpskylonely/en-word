#!/usr/bin/env python3
"""Import DictionaryData CSV files into SQLite for offline use."""

from __future__ import annotations

import csv
import sqlite3
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "dictionary-data"
OUTPUT = ROOT / "data" / "dictionary.db"
SEP = ">"


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=SEP))


def read_translation_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def read_relation_csv(data_dir: Path) -> list[dict]:
    csv_path = data_dir / "relation_book_word.csv"
    if csv_path.exists():
        return read_csv(csv_path)

    zip_path = data_dir / "relation_book_word.zip"
    if not zip_path.exists():
        raise FileNotFoundError("relation_book_word.csv or .zip not found")

    with zipfile.ZipFile(zip_path) as zf:
        name = next(n for n in zf.namelist() if n.endswith(".csv"))
        with zf.open(name) as raw:
            text = raw.read().decode("utf-8")
    return list(csv.DictReader(text.splitlines(), delimiter=SEP))


def main() -> None:
    if not DATA_DIR.exists():
        print(f"Missing data directory: {DATA_DIR}", file=sys.stderr)
        print("Run: git clone https://github.com/LinXueyuanStdio/DictionaryData.git dictionary-data")
        sys.exit(1)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    if OUTPUT.exists():
        OUTPUT.unlink()

    conn = sqlite3.connect(OUTPUT)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")

    conn.executescript(
        """
        CREATE TABLE books (
            id TEXT PRIMARY KEY,
            parent_id TEXT NOT NULL,
            level INTEGER NOT NULL,
            sort_order REAL NOT NULL,
            name TEXT NOT NULL,
            full_name TEXT,
            word_count INTEGER NOT NULL DEFAULT 0,
            direct_word_count INTEGER NOT NULL DEFAULT 0,
            author TEXT,
            publisher TEXT,
            comment TEXT
        );

        CREATE TABLE words (
            id TEXT PRIMARY KEY,
            word TEXT NOT NULL,
            phonetic_uk TEXT,
            phonetic_us TEXT,
            frequency REAL,
            difficulty INTEGER,
            acknowledge_rate REAL
        );

        CREATE TABLE translations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word_id TEXT NOT NULL,
            translation TEXT NOT NULL,
            FOREIGN KEY (word_id) REFERENCES words(id)
        );

        CREATE TABLE book_words (
            id TEXT PRIMARY KEY,
            book_id TEXT NOT NULL,
            word_id TEXT NOT NULL,
            unit_tag TEXT,
            unit_order INTEGER NOT NULL DEFAULT 0,
            flag TEXT,
            FOREIGN KEY (book_id) REFERENCES books(id),
            FOREIGN KEY (word_id) REFERENCES words(id)
        );

        CREATE TABLE user_progress (
            word_id TEXT NOT NULL,
            book_id TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'new',
            ease_factor REAL NOT NULL DEFAULT 2.5,
            interval_days REAL NOT NULL DEFAULT 0,
            repetitions INTEGER NOT NULL DEFAULT 0,
            next_review_at TEXT,
            last_review_at TEXT,
            review_count INTEGER NOT NULL DEFAULT 0,
            correct_count INTEGER NOT NULL DEFAULT 0,
            wrong_count INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (word_id, book_id)
        );

        CREATE TABLE review_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word_id TEXT NOT NULL,
            book_id TEXT NOT NULL,
            mode TEXT NOT NULL,
            result TEXT NOT NULL,
            reviewed_at TEXT NOT NULL
        );

        CREATE INDEX idx_words_word ON words(word);
        CREATE INDEX idx_translations_word_id ON translations(word_id);
        CREATE INDEX idx_book_words_book ON book_words(book_id, unit_order);
        CREATE INDEX idx_book_words_word ON book_words(word_id);
        CREATE INDEX idx_progress_review ON user_progress(book_id, next_review_at);
        CREATE INDEX idx_progress_wrong ON user_progress(book_id, wrong_count);
        """
    )

    books = read_csv(DATA_DIR / "book.csv")
    conn.executemany(
        """
        INSERT INTO books (
            id, parent_id, level, sort_order, name, full_name,
            word_count, direct_word_count, author, publisher, comment
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                r["bk_id"],
                r.get("bk_parent_id") or "0",
                int(float(r.get("bk_level") or 0)),
                float(r.get("bk_order") or 0),
                r.get("bk_name") or "",
                r.get("bk_book") or "",
                int(float(r.get("bk_item_num") or 0)),
                int(float(r.get("bk_direct_item_num") or 0)),
                r.get("bk_author") or "",
                r.get("bk_publisher") or "",
                r.get("bk_comment") or "",
            )
            for r in books
        ],
    )
    print(f"Imported {len(books)} books")

    words = read_csv(DATA_DIR / "word.csv")
    conn.executemany(
        """
        INSERT INTO words (
            id, word, phonetic_uk, phonetic_us,
            frequency, difficulty, acknowledge_rate
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                r["vc_id"],
                r.get("vc_vocabulary") or "",
                r.get("vc_phonetic_uk") or "",
                r.get("vc_phonetic_us") or "",
                float(r["vc_frequency"]) if r.get("vc_frequency") else None,
                int(float(r["vc_difficulty"])) if r.get("vc_difficulty") else None,
                float(r["vc_acknowledge_rate"]) if r.get("vc_acknowledge_rate") else None,
            )
            for r in words
        ],
    )
    print(f"Imported {len(words)} words")

    translations = read_translation_csv(DATA_DIR / "word_translation.csv")
    word_ids = {r["vc_id"] for r in words}
    word_by_text: dict[str, str] = {r.get("vc_vocabulary") or "": r["vc_id"] for r in words}
    translation_rows = []
    for r in translations:
        word_text = r.get("word") or ""
        word_id = word_by_text.get(word_text)
        if not word_id:
            continue
        translation_rows.append((word_id, r.get("translation") or ""))

    conn.executemany(
        "INSERT INTO translations (word_id, translation) VALUES (?, ?)",
        translation_rows,
    )
    print(f"Imported {len(translation_rows)} translations")

    relations = read_relation_csv(DATA_DIR)
    conn.executemany(
        """
        INSERT INTO book_words (
            id, book_id, word_id, unit_tag, unit_order, flag
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (
                r["bv_id"],
                r["bv_book_id"],
                r["bv_voc_id"],
                r.get("bv_tag") or "",
                int(float(r.get("bv_order") or 0)),
                r.get("bv_flag") or "",
            )
            for r in relations
            if r.get("bv_voc_id") in word_ids
        ],
    )
    print(f"Imported {len(relations)} book-word relations")

    conn.commit()
    conn.close()
    size_mb = OUTPUT.stat().st_size / (1024 * 1024)
    print(f"Done: {OUTPUT} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
