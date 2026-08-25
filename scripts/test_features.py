#!/usr/bin/env python3
"""End-to-end feature tests against dictionary.db."""

from __future__ import annotations

import random
import sqlite3
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "dictionary.db"


class TestFailure(Exception):
    pass


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise TestFailure(message)


def connect() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise TestFailure(f"Missing database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def sample_book_id(conn: sqlite3.Connection) -> str:
    row = conn.execute(
        """
        SELECT b.id FROM books b
        WHERE b.direct_word_count > 0
          AND NOT EXISTS (SELECT 1 FROM books c WHERE c.parent_id = b.id)
        ORDER BY b.sort_order LIMIT 1
        """
    ).fetchone()
    assert_true(row is not None, "should find a leaf word book")
    return row["id"]


def test_category_tree(conn: sqlite3.Connection) -> None:
    roots = conn.execute("SELECT COUNT(*) AS c FROM books WHERE parent_id = '0'").fetchone()["c"]
    leaves = conn.execute(
        """
        SELECT COUNT(*) AS c FROM books b
        WHERE b.direct_word_count > 0
          AND NOT EXISTS (SELECT 1 FROM books c WHERE c.parent_id = b.id)
        """
    ).fetchone()["c"]
    assert_true(roots >= 20, f"expected root categories, got {roots}")
    assert_true(leaves >= 500, f"expected leaf word books, got {leaves}")
    print(f"[ok] category tree: {roots} roots, {leaves} leaf books")


def test_browse_and_units(conn: sqlite3.Connection, book_id: str) -> None:
    units = conn.execute(
        "SELECT DISTINCT unit_tag FROM book_words WHERE book_id = ? AND unit_tag != ''",
        (book_id,),
    ).fetchall()
    assert_true(len(units) > 0, "book should have units")
    words = conn.execute(
        """
        SELECT w.word, t.translation FROM book_words bw
        JOIN words w ON w.id = bw.word_id
        LEFT JOIN translations t ON t.word_id = w.id
        WHERE bw.book_id = ? ORDER BY bw.unit_order LIMIT 20
        """,
        (book_id,),
    ).fetchall()
    assert_true(any(w["translation"] for w in words), "browse should include translations")
    print(f"[ok] browse/units: {len(units)} units")


def fetch_quiz(conn: sqlite3.Connection, book_id: str, mode: str) -> list[dict]:
    rows = conn.execute(
        """
        SELECT w.id, w.word FROM book_words bw
        JOIN words w ON w.id = bw.word_id
        JOIN translations t ON t.word_id = w.id
        WHERE bw.book_id = ? GROUP BY w.id ORDER BY RANDOM() LIMIT 30
        """,
        (book_id,),
    ).fetchall()
    questions = []
    for row in rows:
        word_id, word = row["id"], row["word"]
        translation = conn.execute(
            "SELECT translation FROM translations WHERE word_id = ? LIMIT 1", (word_id,)
        ).fetchone()["translation"]
        if mode == "zh_en":
            distractors = conn.execute(
                """
                SELECT w.id, w.word AS text FROM book_words bw
                JOIN words w ON w.id = bw.word_id
                WHERE bw.book_id = ? AND w.id != ? ORDER BY RANDOM() LIMIT 3
                """,
                (book_id, word_id),
            ).fetchall()
            correct_id, correct_text, prompt = word_id, word, translation
        else:
            distractors = conn.execute(
                """
                SELECT w.id, COALESCE(
                  (SELECT translation FROM translations t WHERE t.word_id = w.id LIMIT 1), ''
                ) AS text FROM book_words bw
                JOIN words w ON w.id = bw.word_id
                WHERE bw.book_id = ? AND w.id != ? ORDER BY RANDOM() LIMIT 3
                """,
                (book_id, word_id),
            ).fetchall()
            correct_id, correct_text, prompt = word_id, translation, word
        distractors = [dict(d) for d in distractors if d["text"]]
        if len(distractors) < 3:
            continue
        options = [{"id": correct_id, "text": correct_text}, *distractors[:3]]
        random.shuffle(options)
        questions.append({"word_id": word_id, "correct_id": correct_id, "options": options})
        if len(questions) >= 5:
            break
    return questions


def sm2_from_state(ease: float, interval: float, reps: int, quality: int) -> tuple[float, float, int]:
    q = max(0, min(5, quality))
    ease = max(1.3, min(2.8, ease + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))))
    if q < 3:
        return ease, 1.0, 0
    reps += 1
    if reps == 1:
        interval = 1.0
    elif reps == 2:
        interval = 6.0
    else:
        interval = max(1.0, round(interval * ease))
    return ease, interval, reps


def submit_review(conn, word_id: str, book_id: str, mode: str, quality: int) -> None:
    row = conn.execute(
        "SELECT ease_factor, interval_days, repetitions FROM user_progress WHERE word_id=? AND book_id=?",
        (word_id, book_id),
    ).fetchone()
    if row:
        ease, interval, reps = sm2_from_state(row["ease_factor"], row["interval_days"], row["repetitions"], quality)
    else:
        ease, interval, reps = sm2_from_state(2.5, 0.0, 0, quality)
    next_review = (date.today() + timedelta(days=int(interval))).isoformat()
    conn.execute(
        """
        INSERT INTO user_progress (
          word_id, book_id, status, ease_factor, interval_days, repetitions,
          next_review_at, last_review_at, review_count, correct_count, wrong_count
        ) VALUES (?, ?, 'learning', ?, ?, ?, ?, datetime('now'), 1, ?, ?)
        ON CONFLICT(word_id, book_id) DO UPDATE SET
          ease_factor=excluded.ease_factor, interval_days=excluded.interval_days,
          repetitions=excluded.repetitions, next_review_at=excluded.next_review_at,
          last_review_at=excluded.last_review_at, review_count=review_count+1,
          correct_count=correct_count+excluded.correct_count,
          wrong_count=wrong_count+excluded.wrong_count
        """,
        (word_id, book_id, ease, interval, reps, next_review, 1 if quality >= 3 else 0, 0 if quality >= 3 else 1),
    )
    conn.execute(
        "INSERT INTO review_logs (word_id, book_id, mode, result, reviewed_at) VALUES (?, ?, ?, ?, datetime('now'))",
        (word_id, book_id, mode, "correct" if quality >= 3 else "wrong"),
    )


def main() -> None:
    conn = connect()
    try:
        book_id = sample_book_id(conn)
        book_name = conn.execute("SELECT name FROM books WHERE id=?", (book_id,)).fetchone()["name"]
        print(f"Testing book: {book_name}")
        test_category_tree(conn)
        test_browse_and_units(conn, book_id)
        for mode in ("en_zh", "zh_en"):
            qs = fetch_quiz(conn, book_id, mode)
            assert_true(qs, f"{mode} should generate questions")
            assert_true(all(len(q["options"]) == 4 for q in qs), f"{mode} needs 4 options")
            print(f"[ok] quiz {mode}: {len(qs)} questions")
        spelling = conn.execute(
            """
            SELECT w.id FROM book_words bw JOIN words w ON w.id=bw.word_id
            JOIN translations t ON t.word_id=w.id WHERE bw.book_id=? GROUP BY w.id LIMIT 5
            """,
            (book_id,),
        ).fetchall()
        assert_true(spelling, "spelling prompts required")
        print(f"[ok] spelling: {len(spelling)} prompts")
        conn.execute("DELETE FROM user_progress WHERE book_id=?", (book_id,))
        conn.execute("DELETE FROM review_logs WHERE book_id=?", (book_id,))
        word_id = spelling[0]["id"]
        submit_review(conn, word_id, book_id, "spelling", 1)
        conn.commit()
        wrong = conn.execute(
            "SELECT COUNT(*) AS c FROM user_progress WHERE book_id=? AND wrong_count>0", (book_id,)
        ).fetchone()["c"]
        assert_true(wrong >= 1, "wrong book should record mistakes")
        print(f"[ok] wrong book: {wrong} entries")
        submit_review(conn, word_id, book_id, "flashcard", 4)
        conn.commit()
        learned = conn.execute(
            "SELECT COUNT(*) AS c FROM user_progress WHERE book_id=?", (book_id,)
        ).fetchone()["c"]
        assert_true(learned >= 1, "flashcard should save progress")
        print(f"[ok] flashcard progress: {learned}")
        print("All feature tests passed.")
    except TestFailure as exc:
        print(f"TEST FAILED: {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
