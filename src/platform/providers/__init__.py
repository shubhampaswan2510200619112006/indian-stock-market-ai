"""
Plug-and-play provider architecture for market, equity, intraday, and options data.
"""

from src.platform.providers.base import BaseDataProvider, ProviderMetadata
from src.platform.providers.daily_provider import DailyProvider
from src.platform.providers.intraday_provider import IntradayProvider
from src.platform.providers.equity_panel_provider import EquityPanelProvider
from src.platform.providers.options_quote_provider import OptionsQuoteProvider

__all__ = [
    "BaseDataProvider",
    "ProviderMetadata",
    "DailyProvider",
    "IntradayProvider",
    "EquityPanelProvider",
    "OptionsQuoteProvider",
]
