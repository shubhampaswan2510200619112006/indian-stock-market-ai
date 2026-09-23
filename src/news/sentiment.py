"""
News Sentiment Analyzer (Phase 7).
Scores headline sentiment (POSITIVE, NEUTRAL, NEGATIVE, MIXED).
Enforces rule: Sentiment is an input, NOT a conclusion or automated trading signal.
"""

from typing import Tuple
from src.news.models import NewsSentimentType


class NewsSentimentAnalyzer:
    """Rule-assisted sentiment scorer for financial news headlines."""

    BULLISH_KEYWORDS = ["SURGES", "JUMPS", "GAIN", "RALLY", "HIGHER", "GROWTH", "PROFIT RISES", "OUTPERFORM", "BEAT"]
    BEARISH_KEYWORDS = ["PLUNGEST", "DROPS", "FALLS", "LOWER", "LOSS", "DECLINE", "SLUMP", "DOWN", "WARN"]

    @classmethod
    def analyze_sentiment(cls, title: str) -> Tuple[NewsSentimentType, float]:
        upper_title = title.upper()
        pos_hits = sum(1 for kw in cls.BULLISH_KEYWORDS if kw in upper_title)
        neg_hits = sum(1 for kw in cls.BEARISH_KEYWORDS if kw in upper_title)

        if pos_hits > 0 and neg_hits > 0:
            return NewsSentimentType.MIXED, 0.0
        elif pos_hits > 0:
            score = min(1.0, 0.3 + pos_hits * 0.3)
            return NewsSentimentType.POSITIVE, score
        elif neg_hits > 0:
            score = max(-1.0, -0.3 - neg_hits * 0.3)
            return NewsSentimentType.NEGATIVE, score
        else:
            return NewsSentimentType.NEUTRAL, 0.0
