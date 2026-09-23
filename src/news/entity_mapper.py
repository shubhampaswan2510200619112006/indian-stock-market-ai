"""
News Entity & Ticker Mapper (Phase 7).
Maps raw news headlines to Indian market entities (NIFTY, BANKNIFTY, RELIANCE, TCS, etc.) and sectors.
"""

from typing import Tuple


class EntityMapper:
    """Maps text to security ticker and sector."""

    ENTITY_RULES = {
        "NIFTY": ("NIFTY", "INDEX"),
        "BANKNIFTY": ("BANKNIFTY", "BANKING"),
        "BANK NIFTY": ("BANKNIFTY", "BANKING"),
        "SENSEX": ("SENSEX", "INDEX"),
        "RELIANCE": ("RELIANCE", "ENERGY"),
        "TCS": ("TCS", "TECHNOLOGY"),
        "INFOSYS": ("INFY", "TECHNOLOGY"),
        "INFY": ("INFY", "TECHNOLOGY"),
        "HDFC": ("HDFCBANK", "BANKING"),
        "ICICI": ("ICICIBANK", "BANKING"),
        "RBI": ("NIFTY", "MACRO"),
        "INFLATION": ("NIFTY", "MACRO"),
        "SEBI": ("NIFTY", "REGULATORY"),
    }

    @classmethod
    def map_entity_and_sector(cls, title: str) -> Tuple[str, str]:
        upper_title = title.upper()
        for kw, (ent, sec) in cls.ENTITY_RULES.items():
            if kw in upper_title:
                return ent, sec
        return "NIFTY", "INDEX"
