import os
from datetime import datetime
from typing import Optional, Dict, Any
from serpapi import GoogleSearch
from mcp.server.fastmcp import FastMCP

from utils.google_flights_utils import parse_flights
from utils.google_finance_utils import (
    MarketTrend, GraphPeriod, NewsCategory, Window,
    normalize_query, create_error_response, create_success_response
)
from dotenv import load_dotenv

load_dotenv()

SERP_API_KEY = os.getenv("SERP_API_KEY")

mcp = FastMCP(name="Utility_tools_WxO_Server")

# ------------------- Common GoogleSearch Helper ------------------- #
async def search_google(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Centralized function to call GoogleSearch with error handling.
    All finance tools should use this function to fetch data.
    
    Args:
        params: Dictionary of SerpAPI parameters
    
    Returns:
        Dictionary containing either the results or an 'error' key
    """
    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        if "error" in results:
            return {"error": results["error"]}
        return results
    except Exception as e:
        return {"error": str(e)}


# ------------------- Google Flights Tool ------------------- #
TRAVEL_CLASS_MAP = {
    "economy": 1,
    "eco": 1,
    "coach": 1,

    "premium": 2,
    "premium economy": 2,
    "premium_economy": 2,

    "business": 3,
    "business class": 3,
    "business_class": 3,

    "first": 4,
    "first class": 4,
    "first_class": 4,
    "luxury": 4
}

@mcp.tool()
async def google_flights(
    departure_airport: str,
    arrival_airport: str,
    departure_date: str,
    return_date: Optional[str] = None,
    airline_name: Optional[str] = None,
    travel_class: Optional[str] = "economy",  # user enters string
    max_price: Optional[int] = None,
    max_results: int = 5,
    passengers: Optional[int] = 1,
) -> Dict[str, Any]:
    """
    Search for flights using Google Flights API and return detailed information in a formatted manner.
    
    Args:
        departure_airport (str): IATA code of the departure airport.
        arrival_airport (str): IATA code of the arrival airport.
        departure_date (str): Departure date in YYYY-MM-DD format.
        return_date (Optional[str]): Return date in YYYY-MM-DD format.
        airline_name (Optional[str]): Filter results by airline.
        travel_class (Optional[str]): Travel class (economy, premium economy, business, first).
        max_price (Optional[int]): Maximum price in USD.
        max_results (int): Maximum number of results to return.
        passengers (Optional[int]): Number of passengers.

    Returns:
        Dict[str, Any]: Formatted flight summaries and full detailed flight data.
    """
    passengers = int(passengers) if passengers else 1

    # normalize travel class
    travel_class_key = travel_class.lower().replace("-", "_").strip() if travel_class else "economy"
    if travel_class_key not in TRAVEL_CLASS_MAP:
        return {"error": f"Invalid travel_class '{travel_class}'. Must be one of {list(TRAVEL_CLASS_MAP.keys())}"}
    travel_class_int = TRAVEL_CLASS_MAP[travel_class_key]

    params = {
        "engine": "google_flights",
        "departure_id": departure_airport.upper(),
        "arrival_id": arrival_airport.upper(),
        "outbound_date": departure_date,
        "adults": passengers,
        "travel_class": travel_class_int,   # 👈 integer mapped value
        "hl": "en"
    }

    if return_date:
        params["return_date"] = return_date
        params["type"] = "1"  # roundtrip
    else:
        params["type"] = "2"  # oneway

    if max_price:
        params["max_price"] = max_price
    if airline_name:
        params["airline_name"] = airline_name

    api_key = SERP_API_KEY
    if not api_key:
        return {"error": "SERP_API_KEY environment variable is required"}
    params["api_key"] = api_key

    try:
        results = await search_google(params)

        if "error" in results:
            return {"error": f"SerpAPI error: {results['error']}"}

        best_flights = results.get("best_flights", [])
        if not best_flights:
            return {"message": "No flights found."}

        parsed_flights = parse_flights(best_flights[:max_results])

        return {
            "best_flights": parsed_flights
        }

    except Exception as e:
        return {"error": f"Error searching flights: {str(e)}"}


# ------------------- Google Finance Tools ------------------- #
@mcp.tool()
async def get_stock_quote(q: str, gl: Optional[str] = None, hl: Optional[str] = None) -> Dict[str, Any]:
    """Get comprehensive stock information - returns complete API response"""
    if not q.strip():
        return create_error_response(q, "Query cannot be empty")
    api_key = SERP_API_KEY
    if not api_key:
        return create_error_response(q, "SERP_API_KEY not configured")

    params = {
        "engine": "google_finance",
        "q": normalize_query(q),
        "api_key": api_key
    }
    if gl:
        params["gl"] = gl
    if hl:
        params["hl"] = hl

    data = await search_google(params)
    if "error" in data:
        return create_error_response(q, f"API Error: {data['error']}", "stock_quote")
    return create_success_response(q, data, "stock_quote")


@mcp.tool()
async def get_market_data(trend: str = "indexes", gl: Optional[str] = None, hl: Optional[str] = None) -> Dict[str, Any]:
    """Get market trends, indexes, and active stocks - returns complete API response"""
    valid_trends = ["indexes", "most-active", "gainers", "losers", "climate-leaders", "cryptocurrencies", "currencies"]
    if trend not in valid_trends:
        return create_error_response(trend, f"Invalid trend '{trend}'. Valid trends: {', '.join(valid_trends)}", "market_data")
    api_key = SERP_API_KEY
    if not api_key:
        return create_error_response(trend, "SERP_API_KEY not configured", "market_data")

    params = {
        "engine": "google_finance_markets",
        "trend": trend,
        "api_key": api_key
    }
    if gl:
        params["gl"] = gl
    if hl:
        params["hl"] = hl

    data = await search_google(params)
    if "error" in data:
        return create_error_response(trend, f"API Error: {data['error']}", "market_data")
    return create_success_response(trend, data, "market_data")


@mcp.tool()
async def get_graph_data(q: str, period: str = "1d", gl: Optional[str] = None, hl: Optional[str] = None) -> Dict[str, Any]:
    """Get historical price data and graph information - returns complete API response"""
    valid_periods = ["1d", "5d", "1m", "6m", "ytd", "1y", "5y", "max"]
    if period not in valid_periods:
        return create_error_response(q, f"Invalid period '{period}'. Valid periods: {', '.join(valid_periods)}", "graph_data")
    api_key = SERP_API_KEY
    if not api_key:
        return create_error_response(q, "SERP_API_KEY not configured", "graph_data")

    params = {
        "engine": "google_finance",
        "q": q,
        "period": period,
        "api_key": api_key
    }
    if gl:
        params["gl"] = gl
    if hl:
        params["hl"] = hl

    data = await search_google(params)
    if "error" in data:
        return create_error_response(q, f"API Error: {data['error']}", "graph_data")
    return create_success_response(q, data, "graph_data")


@mcp.tool()
async def compare_stocks(q: str, period: str = "1d", gl: Optional[str] = None, hl: Optional[str] = None) -> Dict[str, Any]:
    """Compare multiple stocks - returns complete API response"""
    valid_periods = ["1d", "5d", "1m", "6m", "ytd", "1y", "5y", "max"]
    if period not in valid_periods:
        return create_error_response(q, f"Invalid period '{period}'. Valid periods: {', '.join(valid_periods)}", "comparison")
    api_key = SERP_API_KEY
    if not api_key:
        return create_error_response(q, "SERP_API_KEY not configured", "comparison")

    params = {
        "engine": "google_finance",
        "q": q,
        "period": period,
        "api_key": api_key
    }
    if gl:
        params["gl"] = gl
    if hl:
        params["hl"] = hl

    data = await search_google(params)
    if "error" in data:
        return create_error_response(q, f"API Error: {data['error']}", "comparison")
    return create_success_response(q, data, "comparison")


@mcp.tool()
async def get_financials(q: str, window: Optional[str] = None, gl: Optional[str] = None, hl: Optional[str] = None) -> Dict[str, Any]:
    """Get detailed financial statements - returns complete API response"""
    valid_windows = ["week", "month", "3month", "6month", "year"]
    if window and window not in valid_windows:
        return create_error_response(q, f"Invalid window '{window}'. Valid windows: {', '.join(valid_windows)}", "financials")
    api_key = os.getenv("SERP_API_K EY")
    if not api_key:
        return create_error_response(q, "SERP_API_KEY not configured", "financials")

    params = {
        "engine": "google_finance",
        "q": q,
        "api_key": api_key
    }
    if window:
        params["window"] = window
    if gl:
        params["gl"] = gl
    if hl:
        params["hl"] = hl

    data = await search_google(params)
    if "error" in data:
        return create_error_response(q, f"API Error: {data['error']}", "financials")
    return create_success_response(q, data, "financials")


@mcp.tool()
async def get_stock_news(q: str, category: Optional[str] = None, num: int = 10, start: Optional[int] = None, gl: Optional[str] = None, hl: Optional[str] = None) -> Dict[str, Any]:
    """Get latest news for a stock - returns complete API response"""
    if num < 1 or num > 100:
        return create_error_response(q, "Number of news items must be between 1 and 100", "news")
    valid_categories = ["all", "latest", "opinion", "press_releases"]
    if category and category not in valid_categories:
        return create_error_response(q, f"Invalid category '{category}'. Valid categories: {', '.join(valid_categories)}", "news")
    api_key = SERP_API_KEY
    if not api_key:
        return create_error_response(q, "SERP_API_KEY not configured", "news")

    params = {
        "engine": "google_finance",
        "q": q,
        "api_key": api_key
    }
    if category and category != "all":
        params["category"] = category
    if num != 10:
        params["num"] = num
    if start:
        params["start"] = start
    if gl:
        params["gl"] = gl
    if hl:
        params["hl"] = hl

    data = await search_google(params)
    if "error" in data:
        return create_error_response(q, f"API Error: {data['error']}", "news")
    return create_success_response(q, data, "news")


@mcp.tool()
async def debug_api_response(q: str, engine: str = "google_finance", gl: Optional[str] = None, hl: Optional[str] = None) -> Dict[str, Any]:
    """Debug tool to inspect raw API responses"""
    api_key = SERP_API_KEY
    if not api_key:
        return create_error_response(q, "SERP_API_KEY not configured", "debug")

    params = {"engine": engine, "api_key": api_key}
    if engine == "google_finance":
        params["q"] = q
    elif engine == "google_finance_markets":
        params["trend"] = q
    if gl:
        params["gl"] = gl
    if hl:
        params["hl"] = hl

    data = await search_google(params)
    if "error" in data:
        return create_error_response(q, f"Debug API Error: {data['error']}", "debug")
    
    return {
        "tool": "debug",
        "query": q,
        "engine": engine,
        "timestamp": datetime.now().isoformat(),
        "success": True,
        "api_response": data
    }


# ------------------- Help and Main ------------------- #
@mcp.resource("resource://finance/help")
async def get_help() -> str:
    """Complete documentation for Google Finance MCP server"""
    return """
    Google Finance MCP Server
    
    Returns complete API responses without extraction for better debugging
    
    Tools:
    1. get_stock_quote(q, gl, hl) - Complete stock information
    2. get_market_data(trend, gl, hl) - Complete market data
    3. get_graph_data(q, period, gl, hl) - Complete historical data
    4. compare_stocks(q, period, gl, hl) - Complete comparison data
    5. get_financials(q, window, gl, hl) - Complete financial data
    6. get_stock_news(q, category, num, start, gl, hl) - Complete news data
    7. debug_api_response(q, engine, gl, hl) - Debug raw API responses
    
    All responses now include:
    - tool: Tool type used
    - query: Original query
    - timestamp: Response timestamp
    - success: Boolean success status
    - api_response: Complete raw API response (on success)
    - error: Error message (on failure)
    
    Parameters Usage:
    - period: Used in get_graph_data() and compare_stocks()
    - window: Used in get_financials()
    - category, num, start: Used in get_stock_news()
    - gl, hl: Used in all tools for localization
    
    Set SERP_API_KEY environment variable for API access.
    
    Examples:
    - get_stock_quote("AAPL")
    - debug_api_response("AAPL")
    - get_market_data(MarketTrend.GAINERS)
    """

def main():
    """Main entry point for the server."""
    print("Starting Utility Tools MCP Server...")
    mcp.run()


if __name__ == "__main__":
    main()
