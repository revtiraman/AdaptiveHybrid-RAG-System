"""Feedback-driven adaptation utilities."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FeedbackItem:
    query_id: str
    rating: int
    helpful: bool
    corrected_answer: str | None
    bad_citation_ids: list[str]


class FeedbackLearner:
    """Store and process user feedback for offline tuning."""

    def __init__(self) -> None:
        self.feedback: list[FeedbackItem] = []

    def add_feedback(self, item: FeedbackItem) -> None:
        self.feedback.append(item)

    def hard_negatives(self) -> list[FeedbackItem]:
        return [f for f in self.feedback if f.rating <= 2 or not f.helpful]

    def high_quality(self) -> list[FeedbackItem]:
        return [f for f in self.feedback if f.rating >= 4 and f.helpful]


__all__ = ["FeedbackItem", "FeedbackLearner"]
