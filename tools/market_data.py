"""
Market Data Tools for Indian Stock Market
Fetches real-time and historical data from NSE, BSE, and Yahoo Finance
"""

import json
import threading
from collections import OrderedDict
from datetime import datetime, timedelta
from typing import Optional
import httpx
import yfinance as yf
from crewai.tools import tool
from tenacity import retry, stop_after_attempt, wait_exponential
import pandas as pd

# Thread-safe LRU cache for stock data
_cache_lock = threading.Lock()
_cache: OrderedDict = OrderedDict()
_cache_ttl = 900  # 15 minutes
_cache_max_size = 200


def _get_nse_symbol(symbol: str) -> str:
    """Convert symbol to NSE Yahoo Finance format."""
    symbol = symbol.upper().strip()
    if not symbol.endswith(".NS"):
        return f"{symbol}.NS"
    return symbol


def _is_cache_valid(key: str) -> bool:
    """Check if cached data is still valid (thread-safe)."""
    with _cache_lock:
        if key not in _cache:
            return False
        cached_time = _cache[key].get("timestamp", 0)
        return (datetime.now().timestamp() - cached_time) < _cache_ttl


def _cache_get(key: str) -> dict | None:
    """Thread-safe cache read."""
    with _cache_lock:
        entry = _cache.get(key)
        if entry:
            _cache.move_to_end(key)
        return entry


def _cache_set(key: str, data: dict) -> None:
    """Thread-safe cache write with LRU eviction."""
    with _cache_lock:
        _cache[key] = {"data": data, "timestamp": datetime.now().timestamp()}
        _cache.move_to_end(key)
        while len(_cache) > _cache_max_size:
            _cache.popitem(last=False)


@tool("Get Stock Price")
def get_stock_price(symbol: str) -> str:
    """
    Get current stock price and basic trading info for an Indian stock.
    
    Args:
        symbol: Stock symbol (e.g., 'RELIANCE', 'TCS', 'INFY')
        
    Returns:
        JSON string with current price, change, volume, and other trading data.
    """
    cache_key = f"price_{symbol}"
    if _is_cache_valid(cache_key):
        return json.dumps(_cache_get(cache_key)["data"], indent=2)

    try:
        ticker = yf.Ticker(_get_nse_symbol(symbol))
        info = ticker.info
        
        # Get today's data
        hist = ticker.history(period="2d")
        
        if hist.empty:
            return json.dumps({
                "error": f"No data found for {symbol}",
                "DATA_UNAVAILABLE": True,
                "message": f"No price data returned for {symbol}. The symbol may be invalid. Do NOT guess the price.",
            })
        
        current_price = hist['Close'].iloc[-1]
        prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
        change = current_price - prev_close
        change_pct = (change / prev_close) * 100
        
        data = {
            "symbol": symbol.upper(),
            "current_price": round(current_price, 2),
            "previous_close": round(prev_close, 2),
            "change": round(change, 2),
            "change_percent": round(change_pct, 2),
            "open": round(hist['Open'].iloc[-1], 2),
            "high": round(hist['High'].iloc[-1], 2),
            "low": round(hist['Low'].iloc[-1], 2),
            "volume": int(hist['Volume'].iloc[-1]),
            "market_cap": info.get("marketCap", "N/A"),
            "52_week_high": info.get("fiftyTwoWeekHigh", "N/A"),
            "52_week_low": info.get("fiftyTwoWeekLow", "N/A"),
            "avg_volume": info.get("averageVolume", "N/A"),
            "timestamp": datetime.now().isoformat(),
        }
        
        _cache_set(cache_key, data)

        return json.dumps(data, indent=2)

    except Exception as e:
        return json.dumps({
            "error": str(e),
            "symbol": symbol,
            "DATA_UNAVAILABLE": True,
            "message": f"FAILED to fetch price for {symbol}. Do NOT guess the price.",
        })


@tool("Get Stock Info")
def get_stock_info(symbol: str) -> str:
    """
    Get comprehensive company information for an Indian stock.
    
    Args:
        symbol: Stock symbol (e.g., 'RELIANCE', 'TCS', 'INFY')
        
    Returns:
        JSON string with company info including sector, industry, financials.
    """
    cache_key = f"info_{symbol}"
    if _is_cache_valid(cache_key):
        return json.dumps(_cache_get(cache_key)["data"], indent=2)

    try:
        ticker = yf.Ticker(_get_nse_symbol(symbol))
        info = ticker.info
        
        data = {
            "symbol": symbol.upper(),
            "company_name": info.get("longName", info.get("shortName", "N/A")),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "website": info.get("website", "N/A"),
            "description": info.get("longBusinessSummary", "N/A")[:500] + "..." if info.get("longBusinessSummary") else "N/A",
            "employees": info.get("fullTimeEmployees", "N/A"),
            "market_cap": info.get("marketCap", "N/A"),
            "market_cap_category": _categorize_market_cap(info.get("marketCap", 0)),
            "pe_ratio": info.get("trailingPE", "N/A"),
            "forward_pe": info.get("forwardPE", "N/A"),
            "pb_ratio": info.get("priceToBook", "N/A"),
            "dividend_yield": info.get("dividendYield", 0) * 100 if info.get("dividendYield") else "N/A",
            "eps": info.get("trailingEps", "N/A"),
            "book_value": info.get("bookValue", "N/A"),
            "roe": info.get("returnOnEquity", 0) * 100 if info.get("returnOnEquity") else "N/A",
            "debt_to_equity": info.get("debtToEquity", "N/A"),
            "current_ratio": info.get("currentRatio", "N/A"),
            "revenue": info.get("totalRevenue", "N/A"),
            "profit_margin": info.get("profitMargins", 0) * 100 if info.get("profitMargins") else "N/A",
            "beta": info.get("beta", "N/A"),
            "timestamp": datetime.now().isoformat(),
        }
        
        _cache_set(cache_key, data)

        return json.dumps(data, indent=2)

    except Exception as e:
        return json.dumps({
            "error": str(e),
            "symbol": symbol,
            "DATA_UNAVAILABLE": True,
            "message": f"FAILED to fetch info for {symbol}. Do NOT guess company details.",
        })


@tool("Get Historical Data")
def get_historical_data(symbol: str, period: str = "1y") -> str:
    """
    Get historical OHLCV data for an Indian stock.
    
    Args:
        symbol: Stock symbol (e.g., 'RELIANCE', 'TCS')
        period: Time period - '1mo', '3mo', '6mo', '1y', '2y', '5y'
        
    Returns:
        JSON string with historical price data summary and key statistics.
    """
    valid_periods = ["1mo", "3mo", "6mo", "1y", "2y", "5y"]
    if period not in valid_periods:
        period = "1y"
    
    try:
        ticker = yf.Ticker(_get_nse_symbol(symbol))
        hist = ticker.history(period=period)
        
        if hist.empty:
            return json.dumps({
                "error": f"No historical data for {symbol}",
                "DATA_UNAVAILABLE": True,
                "message": f"No historical data returned for {symbol}. Do NOT guess historical prices.",
            })
        
        # Calculate returns
        returns = hist['Close'].pct_change().dropna()
        
        # Calculate key statistics
        data = {
            "symbol": symbol.upper(),
            "period": period,
            "start_date": hist.index[0].strftime("%Y-%m-%d"),
            "end_date": hist.index[-1].strftime("%Y-%m-%d"),
            "start_price": round(hist['Close'].iloc[0], 2),
            "end_price": round(hist['Close'].iloc[-1], 2),
            "absolute_return": round(hist['Close'].iloc[-1] - hist['Close'].iloc[0], 2),
            "percentage_return": round(((hist['Close'].iloc[-1] / hist['Close'].iloc[0]) - 1) * 100, 2),
            "highest_price": round(hist['High'].max(), 2),
            "highest_date": hist['High'].idxmax().strftime("%Y-%m-%d"),
            "lowest_price": round(hist['Low'].min(), 2),
            "lowest_date": hist['Low'].idxmin().strftime("%Y-%m-%d"),
            "average_price": round(hist['Close'].mean(), 2),
            "volatility": round(returns.std() * (252 ** 0.5) * 100, 2),  # Annualized
            "avg_daily_volume": int(hist['Volume'].mean()),
            "total_trading_days": len(hist),
            "positive_days": int((returns > 0).sum()),
            "negative_days": int((returns < 0).sum()),
            "max_daily_gain": round(returns.max() * 100, 2),
            "max_daily_loss": round(returns.min() * 100, 2),
            "recent_5_days": [
                {
                    "date": idx.strftime("%Y-%m-%d"),
                    "close": round(row['Close'], 2),
                    "volume": int(row['Volume']),
                }
                for idx, row in hist.tail(5).iterrows()
            ],
        }
        
        return json.dumps(data, indent=2)
    
    except Exception as e:
        return json.dumps({
            "error": str(e),
            "symbol": symbol,
            "DATA_UNAVAILABLE": True,
            "message": f"FAILED to fetch historical data for {symbol}. Do NOT guess prices.",
        })


@tool("Get Index Data")
def get_index_data(index_name: str = "NIFTY50") -> str:
    """
    Get current data for major Indian market indices.
    
    Args:
        index_name: Index name - 'NIFTY50', 'BANKNIFTY', 'NIFTYIT', 'SENSEX', or 'ALL'
        
    Returns:
        JSON string with index levels, changes, and key metrics.
    """
    index_symbols = {
        "NIFTY50": "^NSEI",
        "BANKNIFTY": "^NSEBANK",
        "NIFTYIT": "^CNXIT",
        "SENSEX": "^BSESN",
    }
    
    try:
        if index_name.upper() == "ALL":
            indices_to_fetch = index_symbols
        else:
            indices_to_fetch = {index_name.upper(): index_symbols.get(index_name.upper(), "^NSEI")}
        
        results = {}
        for name, symbol in indices_to_fetch.items():
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="2d")
            
            if not hist.empty:
                current = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[-2] if len(hist) > 1 else current
                change = current - prev
                change_pct = (change / prev) * 100
                
                results[name] = {
                    "value": round(current, 2),
                    "change": round(change, 2),
                    "change_percent": round(change_pct, 2),
                    "open": round(hist['Open'].iloc[-1], 2),
                    "high": round(hist['High'].iloc[-1], 2),
                    "low": round(hist['Low'].iloc[-1], 2),
                }
        
        results["timestamp"] = datetime.now().isoformat()
        return json.dumps(results, indent=2)
    
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool("Get NSE Stock Quote")
def get_nse_stock_quote(symbol: str) -> str:
    """
    Get detailed stock quote from NSE India with delivery data and market depth.
    
    Args:
        symbol: Stock symbol (e.g., 'RELIANCE', 'TCS')
        
    Returns:
        JSON string with NSE-specific data including delivery percentage.
    """
    try:
        # Try using nsetools
        from nsetools import Nse
        nse = Nse()
        
        quote = nse.get_quote(symbol.upper())
        
        if quote:
            data = {
                "symbol": symbol.upper(),
                "company_name": quote.get("companyName", "N/A"),
                "last_price": quote.get("lastPrice", "N/A"),
                "change": quote.get("change", "N/A"),
                "change_percent": quote.get("pChange", "N/A"),
                "open": quote.get("open", "N/A"),
                "high": quote.get("dayHigh", "N/A"),
                "low": quote.get("dayLow", "N/A"),
                "previous_close": quote.get("previousClose", "N/A"),
                "total_traded_volume": quote.get("totalTradedVolume", "N/A"),
                "total_traded_value": quote.get("totalTradedValue", "N/A"),
                "52_week_high": quote.get("high52", "N/A"),
                "52_week_low": quote.get("low52", "N/A"),
                "delivery_quantity": quote.get("deliveryQuantity", "N/A"),
                "delivery_percentage": quote.get("deliveryToTradedQuantity", "N/A"),
                "timestamp": datetime.now().isoformat(),
            }
            return json.dumps(data, indent=2)
        else:
            # Fallback to Yahoo Finance
            return get_stock_price(symbol)
    
    except Exception as e:
        # Fallback to Yahoo Finance
        return get_stock_price(symbol)


def _categorize_market_cap(market_cap: int) -> str:
    """Categorize market cap into Large, Mid, Small cap."""
    if not market_cap or market_cap == 0:
        return "Unknown"
    
    # Values in INR Crores (1 Crore = 10 Million)
    market_cap_cr = market_cap / 10_000_000
    
    if market_cap_cr >= 20_000:
        return "Large Cap"
    elif market_cap_cr >= 5_000:
        return "Mid Cap"
    else:
        return "Small Cap"


def get_trending_stocks() -> dict:
    """Get top gainers and losers from NSE (cached, not a CrewAI tool).

    Returns dict with 'gainers' and 'losers' lists.
    Each entry has 'symbol', 'ltp', 'netPrice' (change %).
    Falls back to empty lists on failure.
    """
    cache_key = "trending_stocks"
    if _is_cache_valid(cache_key):
        return _cache_get(cache_key)["data"]

    try:
        from nsetools import Nse
        nse = Nse()

        gainers = nse.get_top_gainers()
        losers = nse.get_top_losers()

        data = {
            "gainers": gainers if isinstance(gainers, list) else [],
            "losers": losers if isinstance(losers, list) else [],
        }
        _cache_set(cache_key, data)
        return data
    except Exception:
        return {"gainers": [], "losers": []}


def get_peer_comparison(symbol: str, sector: str) -> dict:
    """Get comparison with sector peers (helper function, not a tool)."""
    from config import SECTORS
    
    peers = SECTORS.get(sector, [])[:5]  # Get top 5 peers
    if symbol.upper() in peers:
        peers.remove(symbol.upper())
    
    comparison = {}
    for peer in peers[:4]:  # Compare with 4 peers
        try:
            ticker = yf.Ticker(_get_nse_symbol(peer))
            info = ticker.info
            comparison[peer] = {
                "price": info.get("currentPrice", "N/A"),
                "pe_ratio": info.get("trailingPE", "N/A"),
                "market_cap": info.get("marketCap", "N/A"),
            }
        except Exception:
            continue

    return comparison
