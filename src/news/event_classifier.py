"""
News Event Category Classifier (Phase 7).
Classifies headline text into structured categories (EARNINGS, REGULATORY, MACRO, RBI, etc.).
"""

from typing import Tuple
from src.news.models import NewsEventType, NewsMaterialityType


class EventClassifier:
    """Classifies headline into structured event category and materiality level."""

    CLASSIFICATION_RULES = [
        ("EARNINGS", ("Q1", "Q2", "Q3", "Q4", "PROFIT", "NET INCOME", "REVENUE", "RESULTS"), NewsEventType.EARNINGS, NewsMaterialityType.HIGH),
        ("RBI", ("RBI", "REPO RATE", "MONETARY POLICY", "REVERSE REPO", "CENTRAL BANK"), NewsEventType.RBI, NewsMaterialityType.HIGH),
        ("REGULATORY", ("SEBI", "PENALTY", "INSPECTION", "BAN", "INVESTIGATION", "REGULATORY"), NewsEventType.REGULATORY, NewsMaterialityType.HIGH),
        ("DIVIDEND", ("DIVIDEND", "BONUS ISSUE", "SPLIT"), NewsEventType.DIVIDEND, NewsMaterialityType.MEDIUM),
        ("MACRO", ("INFLATION", "CPI", "WPI", "GDP", "EXPORT", "IMPORT"), NewsEventType.MACRO, NewsMaterialityType.MEDIUM),
    ]

    @classmethod
    def classify_headline(cls, title: str) -> Tuple[NewsEventType, NewsMaterialityType, str]:
        upper_title = title.upper()
        for label, keywords, event_type, materiality in cls.CLASSIFICATION_RULES:
            if any(kw in upper_title for kw in keywords):
                return event_type, materiality, f"Headline contains {label} keywords."
        return NewsEventType.UNKNOWN, NewsMaterialityType.LOW, "General market news headline."
