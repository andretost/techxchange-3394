from typing import Dict, Any
from datetime import datetime
from enum import Enum

# Enums for API parameters
class MarketTrend(str, Enum):
    """Market trends for google_finance_markets engine"""
    INDEXES = "indexes"
    MOST_ACTIVE = "most-active"
    GAINERS = "gainers"
    LOSERS = "losers"
    CLIMATE_LEADERS = "climate-leaders"
    CRYPTOCURRENCIES = "cryptocurrencies"
    CURRENCIES = "currencies"

class GraphPeriod(str, Enum):
    """Time periods for price graphs"""
    ONE_DAY = "1d"
    FIVE_DAYS = "5d"
    ONE_MONTH = "1m"
    SIX_MONTHS = "6m"
    YEAR_TO_DATE = "ytd"
    ONE_YEAR = "1y"
    FIVE_YEARS = "5y"
    MAX = "max"

class NewsCategory(str, Enum):
    """News categories for filtering"""
    ALL = "all"
    LATEST = "latest"
    OPINION = "opinion"
    PRESS_RELEASES = "press_releases"

class Window(str, Enum):
    """Time windows for moving averages"""
    WEEK = "week"
    MONTH = "month"
    THREE_MONTHS = "3month"
    SIX_MONTHS = "6month"
    YEAR = "year"

def normalize_query(query: str) -> str:
    """
    Normalize stock query to handle both SYMBOL:EXCHANGE and EXCHANGE:SYMBOL formats.
    Returns the query in SYMBOL:EXCHANGE format expected by SerpAPI.
    """
    if ':' in query:
        parts = query.split(':')
        if len(parts) == 2:
            # Check if first part looks like an exchange (all caps, no numbers)
            if parts[0].isupper() and not any(char.isdigit() for char in parts[0]):
                # Swap to symbol:exchange format
                return f"{parts[1]}:{parts[0]}"
    return query

def create_error_response(query: str, error: str, tool_type: str = "stock_quote") -> Dict[str, Any]:
    """Create a standardized error response"""
    return {
        "tool": tool_type,
        "query": query,
        "timestamp": datetime.now().isoformat(),
        "error": error,
        "success": False
    }

def create_success_response(query: str, data: Dict[str, Any], tool_type: str = "stock_quote") -> Dict[str, Any]:
    """Create a standardized success response with complete API data"""
    return {
        "tool": tool_type,
        "query": query,
        "timestamp": datetime.now().isoformat(),
        "success": True,
        "api_response": data  # Complete raw API response
    }