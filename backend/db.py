from __future__ import annotations

import random
import sqlite3
from datetime import date, datetime
from typing import Any

from backend.config import resolve_db_path
from backend.sm2 import Sm2State, quality_from_result, sm2_update


def _row_to_book(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "parent_id": row["parent_id"],
        "level": row["level"],
        "sort_order": row["sort_order"],
        "name": row["name"],
        "full_name": row["full_name"] or "",
        "word_count": row["word_count"],
        "direct_word_count": row["direct_word_count"],
        "author": row["author"] or "",
        "publisher": row["publisher"] or "",
        "comment": row["comment"] or "",
    }


def _build_tree(books: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_parent: dict[str, list[dict[str, Any]]] = {}
    for book in books:
        by_parent.setdefault(book["parent_id"], []).append(book)

    def attach(node: dict[str, Any]) -> dict[str, Any]:
        children = [attach(child) for child in by_parent.get(node["id"], [])]
        return {**node, "children": children}

    return [attach(book) for book in by_parent.get("0", [])]


class Database:
    def __init__(self, db_path: str | None = None) -> None:
        path = db_path or str(resolve_db_path())
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        try:
            self.conn.execute("PRAGMA journal_mode = WAL")
        except sqlite3.OperationalError:
            self.conn.execute("PRAGMA journal_mode = DELETE")

    def list_books(self) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT id, parent_id, level, sort_order, name, full_name,
                   word_count, direct_word_count, author, publisher, comment
            FROM books ORDER BY sort_order, name
            """
        ).fetchall()
        return _build_tree([_row_to_book(row) for row in rows])

    def get_book(self, book_id: str) -> dict[str, Any] | None:
        row = self.conn.execute(
            """
            SELECT id, parent_id, level, sort_order, name, full_name,
                   word_count, direct_word_count, author, publisher, comment
            FROM books WHERE id = ?
            """,
            (book_id,),
        ).fetchone()
        return _row_to_book(row) if row else None

    def list_units(self, book_id: str) -> list[str]:
        rows = self.conn.execute(
            """
            SELECT DISTINCT unit_tag FROM book_words
            WHERE book_id = ? AND unit_tag != ''
            ORDER BY MIN(unit_order)
            """,
            (book_id,),
        ).fetchall()
        return [row["unit_tag"] for row in rows]

    def _fetch_translations(self, word_id: str) -> list[str]:
        rows = self.conn.execute(
            "SELECT translation FROM translations WHERE word_id = ? ORDER BY id",
            (word_id,),
        ).fetchall()
        return [row["translation"] for row in rows]

    def _word_item(self, row: sqlite3.Row) -> dict[str, Any]:
        word_id = row["id"]
        return {
            "id": word_id,
            "word": row["word"],
            "phonetic_uk": row["phonetic_uk"] or "",
            "phonetic_us": row["phonetic_us"] or "",
            "translations": self._fetch_translations(word_id),
            "unit_tag": row["unit_tag"] or "",
            "unit_order": row["unit_order"],
        }

    def browse_words(
        self, book_id: str, unit: str | None, offset: int, limit: int
    ) -> list[dict[str, Any]]:
        if unit:
            rows = self.conn.execute(
                """
                SELECT w.id, w.word, w.phonetic_uk, w.phonetic_us,
                       bw.unit_tag, bw.unit_order
                FROM book_words bw
                JOIN words w ON w.id = bw.word_id
                WHERE bw.book_id = ? AND bw.unit_tag = ?
                ORDER BY bw.unit_order LIMIT ? OFFSET ?
                """,
                (book_id, unit, limit, offset),
            ).fetchall()
        else:
            rows = self.conn.execute(
                """
                SELECT w.id, w.word, w.phonetic_uk, w.phonetic_us,
                       bw.unit_tag, bw.unit_order
                FROM book_words bw
                JOIN words w ON w.id = bw.word_id
                WHERE bw.book_id = ?
                ORDER BY bw.unit_order LIMIT ? OFFSET ?
                """,
                (book_id, limit, offset),
            ).fetchall()
        return [self._word_item(row) for row in rows]

    def get_due_words(self, book_id: str, limit: int) -> list[dict[str, Any]]:
        today = date.today().isoformat()
        rows = self.conn.execute(
            """
            SELECT w.id, w.word, w.phonetic_uk, w.phonetic_us,
                   bw.unit_tag, bw.unit_order
            FROM user_progress up
            JOIN book_words bw ON bw.book_id = up.book_id AND bw.word_id = up.word_id
            JOIN words w ON w.id = up.word_id
            WHERE up.book_id = ? AND up.next_review_at IS NOT NULL
              AND up.next_review_at <= ?
            ORDER BY up.next_review_at LIMIT ?
            """,
            (book_id, today, limit),
        ).fetchall()
        return [self._word_item(row) for row in rows]

    def get_new_words(self, book_id: str, limit: int) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT w.id, w.word, w.phonetic_uk, w.phonetic_us,
                   bw.unit_tag, bw.unit_order
            FROM book_words bw
            JOIN words w ON w.id = bw.word_id
            LEFT JOIN user_progress up
              ON up.book_id = bw.book_id AND up.word_id = bw.word_id
            WHERE bw.book_id = ? AND up.word_id IS NULL
            ORDER BY bw.unit_order LIMIT ?
            """,
            (book_id, limit),
        ).fetchall()
        return [self._word_item(row) for row in rows]

    def _fetch_distractors(
        self, book_id: str, exclude_id: str, mode: str, count: int
    ) -> list[tuple[str, str]]:
        if mode == "zh_en":
            sql = """
                SELECT w.id, w.word AS text FROM book_words bw
                JOIN words w ON w.id = bw.word_id
                WHERE bw.book_id = ? AND w.id != ?
                ORDER BY RANDOM() LIMIT ?
            """
        else:
            sql = """
                SELECT w.id, COALESCE(
                    (SELECT translation FROM translations t WHERE t.word_id = w.id LIMIT 1), ''
                ) AS text
                FROM book_words bw
                JOIN words w ON w.id = bw.word_id
                WHERE bw.book_id = ? AND w.id != ?
                ORDER BY RANDOM() LIMIT ?
            """
        rows = self.conn.execute(sql, (book_id, exclude_id, count)).fetchall()
        return [(row["id"], row["text"]) for row in rows if row["text"]]

    def get_quiz_questions(
        self, book_id: str, mode: str, count: int, source: str = "book"
    ) -> list[dict[str, Any]]:
        fetch_limit = max(count * 5, count)
        if source == "all_wrong":
            rows = self.conn.execute(
                """
                SELECT w.id, w.word, w.phonetic_uk, w.phonetic_us, up.book_id
                FROM user_progress up
                JOIN book_words bw ON bw.book_id = up.book_id AND bw.word_id = up.word_id
                JOIN words w ON w.id = up.word_id
                JOIN translations t ON t.word_id = w.id
                WHERE up.wrong_count > 0
                GROUP BY up.book_id, w.id
                ORDER BY RANDOM() LIMIT ?
                """,
                (fetch_limit,),
            ).fetchall()
        elif source == "wrong":
            rows = self.conn.execute(
                """
                SELECT w.id, w.word, w.phonetic_uk, w.phonetic_us
                FROM user_progress up
                JOIN book_words bw ON bw.book_id = up.book_id AND bw.word_id = up.word_id
                JOIN words w ON w.id = up.word_id
                JOIN translations t ON t.word_id = w.id
                WHERE up.book_id = ? AND up.wrong_count > 0
                GROUP BY w.id
                ORDER BY RANDOM() LIMIT ?
                """,
                (book_id, fetch_limit),
            ).fetchall()
        else:
            rows = self.conn.execute(
                """
                SELECT w.id, w.word, w.phonetic_uk, w.phonetic_us
                FROM book_words bw
                JOIN words w ON w.id = bw.word_id
                JOIN translations t ON t.word_id = w.id
                WHERE bw.book_id = ?
                GROUP BY w.id
                ORDER BY RANDOM() LIMIT ?
                """,
                (book_id, fetch_limit),
            ).fetchall()

        questions: list[dict[str, Any]] = []
        for row in rows:
            word_id = row["id"]
            word = row["word"]
            q_book_id = row["book_id"] if source == "all_wrong" else book_id
            translations = self._fetch_translations(word_id)
            correct_text = translations[0] if translations else ""
            if not correct_text:
                continue
            distractors = self._fetch_distractors(q_book_id, word_id, mode, 3)
            if len(distractors) < 3:
                continue

            if mode == "zh_en":
                options = [{"id": word_id, "text": word}] + [
                    {"id": d_id, "text": text} for d_id, text in distractors
                ]
                prompt, correct_id, answer = correct_text, word_id, word
            else:
                options = [{"id": word_id, "text": correct_text}] + [
                    {"id": d_id, "text": text} for d_id, text in distractors
                ]
                prompt, correct_id, answer = word, word_id, correct_text

            random.shuffle(options)
            question: dict[str, Any] = {
                "word_id": word_id,
                "prompt": prompt,
                "phonetic_uk": row["phonetic_uk"] or "",
                "phonetic_us": row["phonetic_us"] or "",
                "correct_id": correct_id,
                "correct_text": answer,
                "options": options,
                "mode": mode,
            }
            if source in ("wrong", "all_wrong"):
                question["book_id"] = q_book_id
            questions.append(question)
            if len(questions) >= count:
                break
        return questions

    def get_spelling_words(
        self, book_id: str, count: int, source: str = "book"
    ) -> list[dict[str, Any]]:
        fetch_limit = max(count * 5, count)
        if source == "all_wrong":
            rows = self.conn.execute(
                """
                SELECT w.id, w.word, w.phonetic_uk, w.phonetic_us,
                       MIN(t.translation) AS translation, up.book_id
                FROM user_progress up
                JOIN book_words bw ON bw.book_id = up.book_id AND bw.word_id = up.word_id
                JOIN words w ON w.id = up.word_id
                JOIN translations t ON t.word_id = w.id
                WHERE up.wrong_count > 0
                GROUP BY up.book_id, w.id
                ORDER BY RANDOM() LIMIT ?
                """,
                (fetch_limit,),
            ).fetchall()
        elif source == "wrong":
            rows = self.conn.execute(
                """
                SELECT w.id, w.word, w.phonetic_uk, w.phonetic_us,
                       MIN(t.translation) AS translation
                FROM user_progress up
                JOIN book_words bw ON bw.book_id = up.book_id AND bw.word_id = up.word_id
                JOIN words w ON w.id = up.word_id
                JOIN translations t ON t.word_id = w.id
                WHERE up.book_id = ? AND up.wrong_count > 0
                GROUP BY w.id
                ORDER BY RANDOM() LIMIT ?
                """,
                (book_id, fetch_limit),
            ).fetchall()
        else:
            rows = self.conn.execute(
                """
                SELECT w.id, w.word, w.phonetic_uk, w.phonetic_us,
                       MIN(t.translation) AS translation
                FROM book_words bw
                JOIN words w ON w.id = bw.word_id
                JOIN translations t ON t.word_id = w.id
                WHERE bw.book_id = ?
                GROUP BY w.id
                ORDER BY RANDOM() LIMIT ?
                """,
                (book_id, fetch_limit),
            ).fetchall()
        items: list[dict[str, Any]] = []
        for row in rows:
            item: dict[str, Any] = {
                "word_id": row["id"],
                "prompt": row["translation"] or row["word"],
                "answer": row["word"],
                "phonetic_uk": row["phonetic_uk"] or "",
                "phonetic_us": row["phonetic_us"] or "",
            }
            if source in ("wrong", "all_wrong"):
                item["book_id"] = row["book_id"] if source == "all_wrong" else book_id
            items.append(item)
            if len(items) >= count:
                break
        return items

    def get_wrong_words(self, book_id: str) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT w.id, w.word, w.phonetic_uk, w.phonetic_us,
                   bw.unit_tag, bw.unit_order, up.wrong_count
            FROM user_progress up
            JOIN book_words bw ON bw.book_id = up.book_id AND bw.word_id = up.word_id
            JOIN words w ON w.id = up.word_id
            WHERE up.book_id = ? AND up.wrong_count > 0
            ORDER BY up.wrong_count DESC, up.last_review_at DESC
            """,
            (book_id,),
        ).fetchall()
        return [
            {**self._word_item(row), "wrong_count": row["wrong_count"]}
            for row in rows
        ]

    def get_all_wrong_words(self) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT w.id, w.word, w.phonetic_uk, w.phonetic_us,
                   bw.unit_tag, bw.unit_order,
                   b.id AS book_id, b.name AS book_name, up.wrong_count
            FROM user_progress up
            JOIN books b ON b.id = up.book_id
            JOIN book_words bw ON bw.book_id = up.book_id AND bw.word_id = up.word_id
            JOIN words w ON w.id = up.word_id
            WHERE up.wrong_count > 0
            ORDER BY up.wrong_count DESC, up.last_review_at DESC
            """
        ).fetchall()
        return [
            {
                **self._word_item(row),
                "book_id": row["book_id"],
                "book_name": row["book_name"],
                "wrong_count": row["wrong_count"],
            }
            for row in rows
        ]

    def submit_review(
        self, word_id: str, book_id: str, mode: str, result: str
    ) -> None:
        quality = quality_from_result(result)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row = self.conn.execute(
            """
            SELECT ease_factor, interval_days, repetitions
            FROM user_progress WHERE word_id = ? AND book_id = ?
            """,
            (word_id, book_id),
        ).fetchone()
        state = Sm2State(
            ease_factor=row["ease_factor"] if row else 2.5,
            interval_days=row["interval_days"] if row else 0.0,
            repetitions=row["repetitions"] if row else 0,
        )
        updated = sm2_update(state, quality)
        next_review = updated.next_review_at.isoformat()
        self.conn.execute(
            """
            INSERT INTO user_progress (
                word_id, book_id, status, ease_factor, interval_days,
                repetitions, next_review_at, last_review_at,
                review_count, correct_count, wrong_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
            ON CONFLICT(word_id, book_id) DO UPDATE SET
                status = excluded.status,
                ease_factor = excluded.ease_factor,
                interval_days = excluded.interval_days,
                repetitions = excluded.repetitions,
                next_review_at = excluded.next_review_at,
                last_review_at = excluded.last_review_at,
                review_count = review_count + 1,
                correct_count = correct_count + excluded.correct_count,
                wrong_count = wrong_count + excluded.wrong_count
            """,
            (
                word_id,
                book_id,
                updated.status,
                updated.ease_factor,
                updated.interval_days,
                updated.repetitions,
                next_review,
                now,
                1 if quality >= 3 else 0,
                0 if quality >= 3 else 1,
            ),
        )
        self.conn.execute(
            """
            INSERT INTO review_logs (word_id, book_id, mode, result, reviewed_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                word_id,
                book_id,
                mode,
                "correct" if quality >= 3 else "wrong",
                now,
            ),
        )
        self.conn.commit()

    def get_stats(self, book_id: str) -> dict[str, int]:
        today = date.today().isoformat()
        return {
            "total_words": self.conn.execute(
                "SELECT COUNT(*) FROM book_words WHERE book_id = ?", (book_id,)
            ).fetchone()[0],
            "learned_words": self.conn.execute(
                "SELECT COUNT(*) FROM user_progress WHERE book_id = ?", (book_id,)
            ).fetchone()[0],
            "mastered_words": self.conn.execute(
                "SELECT COUNT(*) FROM user_progress WHERE book_id = ? AND status = 'mastered'",
                (book_id,),
            ).fetchone()[0],
            "due_today": self.conn.execute(
                """
                SELECT COUNT(*) FROM user_progress
                WHERE book_id = ? AND next_review_at IS NOT NULL AND next_review_at <= ?
                """,
                (book_id, today),
            ).fetchone()[0],
            "wrong_words": self.conn.execute(
                "SELECT COUNT(*) FROM user_progress WHERE book_id = ? AND wrong_count > 0",
                (book_id,),
            ).fetchone()[0],
        }

    def get_leaf_book_progress(self) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT
                b.id AS book_id,
                COUNT(DISTINCT bw.word_id) AS total_words,
                COUNT(DISTINCT up.word_id) AS learned_words,
                MAX(up.last_review_at) AS last_study_at,
                COALESCE(SUM(up.correct_count), 0) AS correct_count,
                COALESCE(SUM(up.wrong_count), 0) AS wrong_count
            FROM books b
            JOIN book_words bw ON bw.book_id = b.id
            LEFT JOIN user_progress up
              ON up.book_id = b.id AND up.word_id = bw.word_id
            WHERE b.direct_word_count > 0
            GROUP BY b.id
            ORDER BY b.sort_order, b.name
            """
        ).fetchall()
        return [
            {
                "book_id": row["book_id"],
                "total_words": row["total_words"],
                "learned_words": row["learned_words"],
                "last_study_at": row["last_study_at"],
                "correct_count": row["correct_count"],
                "wrong_count": row["wrong_count"],
            }
            for row in rows
        ]

    def get_studied_books_stats(self) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT
                b.id,
                b.name,
                b.full_name,
                (SELECT COUNT(*) FROM book_words WHERE book_id = b.id) AS total_words,
                COUNT(up.word_id) AS learned_words,
                SUM(CASE WHEN up.status = 'mastered' THEN 1 ELSE 0 END) AS mastered_words,
                MAX(up.last_review_at) AS last_study_at,
                COALESCE(SUM(up.review_count), 0) AS review_count,
                COALESCE(SUM(up.correct_count), 0) AS correct_count,
                COALESCE(SUM(up.wrong_count), 0) AS wrong_count
            FROM user_progress up
            JOIN books b ON b.id = up.book_id
            GROUP BY b.id
            ORDER BY last_study_at IS NULL, last_study_at DESC, b.name
            """
        ).fetchall()
        items: list[dict[str, Any]] = []
        for row in rows:
            correct = int(row["correct_count"])
            wrong = int(row["wrong_count"])
            attempts = correct + wrong
            accuracy_rate = round(correct * 100 / attempts, 1) if attempts > 0 else 0.0
            error_rate = round(wrong * 100 / attempts, 1) if attempts > 0 else 0.0
            total_words = int(row["total_words"])
            learned_words = int(row["learned_words"])
            progress_rate = (
                round(learned_words * 100 / total_words, 1) if total_words > 0 else 0.0
            )
            items.append(
                {
                    "id": row["id"],
                    "name": row["name"],
                    "full_name": row["full_name"] or "",
                    "total_words": total_words,
                    "learned_words": learned_words,
                    "mastered_words": int(row["mastered_words"]),
                    "last_study_at": row["last_study_at"],
                    "review_count": int(row["review_count"]),
                    "correct_count": correct,
                    "wrong_count": wrong,
                    "accuracy_rate": accuracy_rate,
                    "error_rate": error_rate,
                    "progress_rate": progress_rate,
                }
            )
        return items

    def get_stats_overview(self) -> dict[str, Any]:
        row = self.conn.execute(
            """
            SELECT
                COUNT(DISTINCT book_id) AS studied_books,
                COALESCE(SUM(review_count), 0) AS total_reviews,
                COALESCE(SUM(correct_count), 0) AS correct_count,
                COALESCE(SUM(wrong_count), 0) AS wrong_count
            FROM user_progress
            """
        ).fetchone()
        correct = int(row["correct_count"])
        wrong = int(row["wrong_count"])
        attempts = correct + wrong
        return {
            "studied_books": int(row["studied_books"]),
            "total_reviews": int(row["total_reviews"]),
            "correct_count": correct,
            "wrong_count": wrong,
            "accuracy_rate": round(correct * 100 / attempts, 1) if attempts > 0 else 0.0,
            "error_rate": round(wrong * 100 / attempts, 1) if attempts > 0 else 0.0,
        }

    def reset_book_progress(self, book_id: str) -> None:
        self.conn.execute("DELETE FROM user_progress WHERE book_id = ?", (book_id,))
        self.conn.execute("DELETE FROM review_logs WHERE book_id = ?", (book_id,))
        self.conn.commit()

    def reset_all_progress(self) -> None:
        self.conn.execute("DELETE FROM user_progress")
        self.conn.execute("DELETE FROM review_logs")
        self.conn.commit()
