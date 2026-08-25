from __future__ import annotations

import unittest

from backend.db import Database


class BackendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.db = Database()

    def test_list_books_tree(self) -> None:
        tree = self.db.list_books()
        self.assertTrue(tree)
        self.assertTrue(any(node.get("children") for node in tree))

    def test_quiz_and_wrong_book(self) -> None:
        book_id = self._sample_book_id()
        self.db.reset_book_progress(book_id)
        questions = self.db.get_quiz_questions(book_id, "en_zh", 5)
        self.assertTrue(questions)
        word_id = questions[0]["word_id"]
        self.db.submit_review(word_id, book_id, "en_zh", "wrong")
        wrong = self.db.get_wrong_words(book_id)
        self.assertTrue(any(w["id"] == word_id for w in wrong))

    def test_book_progress_and_stats(self) -> None:
        book_id = self._sample_book_id()
        self.db.reset_book_progress(book_id)
        progress = self.db.get_leaf_book_progress()
        item = next(row for row in progress if row["book_id"] == book_id)
        self.assertEqual(item["learned_words"], 0)
        self.assertIsNone(item["last_study_at"])

        questions = self.db.get_quiz_questions(book_id, "en_zh", 1)
        word_id = questions[0]["word_id"]
        self.db.submit_review(word_id, book_id, "en_zh", "wrong")

        progress = self.db.get_leaf_book_progress()
        item = next(row for row in progress if row["book_id"] == book_id)
        self.assertEqual(item["learned_words"], 1)
        self.assertIsNotNone(item["last_study_at"])

        books = self.db.get_studied_books_stats()
        studied = next(row for row in books if row["id"] == book_id)
        self.assertEqual(studied["learned_words"], 1)
        self.assertGreater(studied["wrong_count"], 0)

        all_wrong = self.db.get_all_wrong_words()
        self.assertTrue(any(w["id"] == word_id and w["book_id"] == book_id for w in all_wrong))

        overview = self.db.get_stats_overview()
        self.assertGreaterEqual(overview["studied_books"], 1)

    def test_reset_all_progress(self) -> None:
        book_id = self._sample_book_id()
        self.db.reset_book_progress(book_id)
        questions = self.db.get_quiz_questions(book_id, "en_zh", 1)
        self.db.submit_review(questions[0]["word_id"], book_id, "en_zh", "wrong")
        self.assertGreater(self.db.get_stats(book_id)["learned_words"], 0)

        self.db.reset_all_progress()
        self.assertEqual(self.db.get_stats(book_id)["learned_words"], 0)
        self.assertEqual(self.db.get_stats_overview()["studied_books"], 0)
        self.assertEqual(self.db.get_all_wrong_words(), [])

    def _sample_book_id(self) -> str:
        def first_leaf(nodes: list[dict]) -> str | None:
            for node in nodes:
                if node.get("direct_word_count", 0) > 0 and not node.get("children"):
                    return node["id"]
                if node.get("children"):
                    found = first_leaf(node["children"])
                    if found:
                        return found
            return None

        book_id = first_leaf(self.db.list_books())
        assert book_id
        return book_id


if __name__ == "__main__":
    unittest.main()
