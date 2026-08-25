from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta


@dataclass
class Sm2State:
    ease_factor: float
    interval_days: float
    repetitions: int


@dataclass
class Sm2Update:
    ease_factor: float
    interval_days: float
    repetitions: int
    next_review_at: date
    status: str


def sm2_update(state: Sm2State, quality: int) -> Sm2Update:
    q = max(0, min(5, quality))
    ease = state.ease_factor
    interval = state.interval_days
    reps = state.repetitions
    ease = max(1.3, min(2.8, ease + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))))
    if q < 3:
        reps = 0
        interval = 1.0
        status = "learning"
    else:
        reps += 1
        interval = 1.0 if reps == 1 else 6.0 if reps == 2 else round(interval * ease)
        status = "mastered" if reps >= 3 and interval >= 21 else "learning"
    return Sm2Update(
        ease_factor=ease,
        interval_days=float(interval),
        repetitions=reps,
        next_review_at=date.today() + timedelta(days=int(interval)),
        status=status,
    )


def quality_from_result(result: str) -> int:
    return {
        "unknown": 1, "wrong": 1, "fuzzy": 3, "hard": 3,
        "known": 4, "correct": 4, "easy": 5,
    }.get(result, 4)
