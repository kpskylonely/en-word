from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.db import Database

db = Database()


class ReviewBody(BaseModel):
    word_id: str
    book_id: str
    mode: str
    result: str


def create_app(static_dir: Optional[Path] = None) -> FastAPI:
    app = FastAPI(title="EnWord API")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/books")
    def list_books():
        return db.list_books()

    @app.get("/api/books/{book_id}")
    def get_book(book_id: str):
        book = db.get_book(book_id)
        if not book:
            raise HTTPException(status_code=404, detail="book not found")
        return book

    @app.get("/api/books/{book_id}/units")
    def list_units(book_id: str):
        return db.list_units(book_id)

    @app.get("/api/books/{book_id}/words")
    def browse_words(
        book_id: str,
        unit: Optional[str] = None,
        offset: int = 0,
        limit: int = 30,
    ):
        return db.browse_words(book_id, unit, offset, limit)

    @app.get("/api/books/{book_id}/due")
    def get_due_words(book_id: str, limit: int = Query(default=20)):
        return db.get_due_words(book_id, limit)

    @app.get("/api/books/{book_id}/new")
    def get_new_words(book_id: str, limit: int = Query(default=20)):
        return db.get_new_words(book_id, limit)

    @app.get("/api/books/{book_id}/quiz")
    def get_quiz(
        book_id: str,
        mode: str,
        count: int = Query(default=10),
        source: str = Query(default="book"),
    ):
        return db.get_quiz_questions(book_id, mode, count, source)

    @app.get("/api/books/{book_id}/spelling")
    def get_spelling(
        book_id: str,
        count: int = Query(default=10),
        source: str = Query(default="book"),
    ):
        return db.get_spelling_words(book_id, count, source)

    @app.get("/api/books/{book_id}/wrong")
    def get_wrong_words(book_id: str):
        return db.get_wrong_words(book_id)

    @app.get("/api/wrong")
    def get_all_wrong_words():
        return db.get_all_wrong_words()

    @app.get("/api/books/{book_id}/stats")
    def get_stats(book_id: str):
        return db.get_stats(book_id)

    @app.get("/api/progress/books")
    def get_book_progress():
        return db.get_leaf_book_progress()

    @app.get("/api/stats/books")
    def get_studied_books_stats():
        return db.get_studied_books_stats()

    @app.get("/api/stats/overview")
    def get_stats_overview():
        return db.get_stats_overview()

    @app.post("/api/review")
    def submit_review(body: ReviewBody):
        db.submit_review(body.word_id, body.book_id, body.mode, body.result)
        return {"ok": True}

    @app.post("/api/books/{book_id}/reset")
    def reset_progress(book_id: str):
        db.reset_book_progress(book_id)
        return {"ok": True}

    @app.post("/api/progress/reset")
    def reset_all_progress():
        db.reset_all_progress()
        return {"ok": True}

    if static_dir and static_dir.exists():
        app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

    return app
