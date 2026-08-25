#!/usr/bin/env python3
"""Create a small sample dictionary.db for local development."""

from __future__ import annotations

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "dictionary.db"

SCHEMA = """
CREATE TABLE books (
    id TEXT PRIMARY KEY,
    parent_id TEXT NOT NULL,
    level INTEGER NOT NULL,
    sort_order REAL NOT NULL,
    name TEXT NOT NULL,
    full_name TEXT,
    word_count INTEGER NOT NULL DEFAULT 0,
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
    translation TEXT NOT NULL
);

CREATE TABLE book_words (
    id TEXT PRIMARY KEY,
    book_id TEXT NOT NULL,
    word_id TEXT NOT NULL,
    unit_tag TEXT,
    unit_order INTEGER NOT NULL DEFAULT 0,
    flag TEXT
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
"""

BOOKS = [
    ("root", "0", 0, 0, "示例分类", "示例分类", 0, "", "", ""),
    (
        "book-demo",
        "root",
        1,
        1,
        "示例单词书",
        "离线背单词示例单词书",
        8,
        "Demo",
        "Local",
        "用于开发调试的示例词书",
    ),
]

WORDS = [
    ("w1", "apple", "[ˈæpl]", "[ˈæpl]", 0.1, 1, 0.9),
    ("w2", "book", "[bʊk]", "[bʊk]", 0.2, 1, 0.88),
    ("w3", "computer", "[kəmˈpjuːtə(r)]", "[kəmˈpjuːtər]", 0.15, 2, 0.75),
    ("w4", "dictionary", "[ˈdɪkʃənri]", "[ˈdɪkʃəneri]", 0.05, 2, 0.7),
    ("w5", "education", "[ˌedʒuˈkeɪʃn]", "[ˌedʒuˈkeɪʃn]", 0.08, 2, 0.68),
    ("w6", "future", "[ˈfjuːtʃə(r)]", "[ˈfjuːtʃər]", 0.07, 2, 0.66),
    ("w7", "language", "[ˈlæŋɡwɪdʒ]", "[ˈlæŋɡwɪdʒ]", 0.09, 2, 0.72),
    ("w8", "memory", "[ˈmeməri]", "[ˈmeməri]", 0.06, 2, 0.65),
]

TRANSLATIONS = [
    ("w1", "n.苹果"),
    ("w2", "n.书，书籍"),
    ("w3", "n.计算机，电脑"),
    ("w4", "n.词典，字典"),
    ("w5", "n.教育"),
    ("w6", "n.未来"),
    ("w7", "n.语言"),
    ("w8", "n.记忆，记忆力"),
]

RELATIONS = [
    ("bw1", "book-demo", "w1", "Unit 1", 1, ""),
    ("bw2", "book-demo", "w2", "Unit 1", 2, ""),
    ("bw3", "book-demo", "w3", "Unit 1", 3, ""),
    ("bw4", "book-demo", "w4", "Unit 2", 1, ""),
    ("bw5", "book-demo", "w5", "Unit 2", 2, ""),
    ("bw6", "book-demo", "w6", "Unit 2", 3, ""),
    ("bw7", "book-demo", "w7", "Unit 2", 4, ""),
    ("bw8", "book-demo", "w8", "Unit 2", 5, ""),
]


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    if OUTPUT.exists():
        OUTPUT.unlink()

    conn = sqlite3.connect(OUTPUT)
    conn.executescript(SCHEMA)
    conn.executemany(
        "INSERT INTO books VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        BOOKS,
    )
    conn.executemany(
        "INSERT INTO words VALUES (?, ?, ?, ?, ?, ?, ?)",
        WORDS,
    )
    conn.executemany(
        "INSERT INTO translations (word_id, translation) VALUES (?, ?)",
        TRANSLATIONS,
    )
    conn.executemany(
        "INSERT INTO book_words VALUES (?, ?, ?, ?, ?, ?)",
        RELATIONS,
    )
    conn.commit()
    conn.close()
    print(f"Sample database created: {OUTPUT}")


if __name__ == "__main__":
    main()
