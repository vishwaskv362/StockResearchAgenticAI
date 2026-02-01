"""
Pytest Configuration and Fixtures

This module provides common fixtures, mocks, and utilities for all tests.
"""

import json
import pytest
from datetime import datetime
from typing import Generator
from unittest.mock import MagicMock, patch
import pandas as pd
import numpy as np


# ============================================================
# Sample Data Fixtures
# ============================================================

@pytest.fixture
def sample_stock_symbols() -> list[str]:
    """Common Indian stock symbols for testing."""
    return ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK"]


@pytest.fixture
def valid_symbol() -> str:
    """A valid, liquid stock symbol that should always return data."""
    return "RELIANCE"


@pytest.fixture
def invalid_symbol() -> str:
    """An invalid stock symbol for testing error handling."""
    return "INVALIDXYZ123"


@pytest.fixture
def sample_price_data() -> dict:
    """Sample price data structure."""
    return {
        "symbol": "RELIANCE",
        "current_price": 2456.50,
        "previous_close": 2445.30,
        "change": 11.20,
        "change_percent": 0.46,
        "open": 2448.00,
        "high": 2465.75,
        "low": 2442.00,
        "volume": 5678900,
        "market_cap": 16500000000000,
        "52_week_high": 2856.15,
        "52_week_low": 2180.00,
        "timestamp": datetime.now().isoformat(),
    }


@pytest.fixture
def sample_historical_data() -> pd.DataFrame:
    """Sample historical price data for technical analysis."""
    dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
    np.random.seed(42)  # Reproducible random data
    
    # Generate realistic price movement
    base_price = 2400
    returns = np.random.normal(0.0005, 0.02, 100)
    prices = base_price * np.exp(np.cumsum(returns))
    
    df = pd.DataFrame({
        'Open': prices * (1 + np.random.uniform(-0.01, 0.01, 100)),
        'High': prices * (1 + np.random.uniform(0, 0.02, 100)),
        'Low': prices * (1 - np.random.uniform(0, 0.02, 100)),
        'Close': prices,
        'Volume': np.random.randint(1000000, 10000000, 100),
    }, index=dates)
    
    return df


@pytest.fixture
def sample_technical_indicators() -> dict:
    """Sample technical indicators output."""
    return {
        "symbol": "RELIANCE",
        "current_price": 2456.50,
        "indicators": {
            "sma_20": 2435.60,
            "sma_50": 2410.25,
            "sma_200": 2380.90,
            "rsi_14": 58.5,
            "macd_line": 12.45,
            "macd_signal": 10.20,
            "macd_histogram": 2.25,
            "bb_upper": 2520.30,
            "bb_middle": 2435.60,
            "bb_lower": 2350.90,
        },
        "signals": {
            "trend": "Bullish",
            "momentum": "Positive",
            "volatility": "Normal",
            "overall": "BUY",
        },
    }


@pytest.fixture
def sample_fundamental_data() -> dict:
    """Sample fundamental metrics."""
    return {
        "symbol": "RELIANCE",
        "pe_ratio": 25.6,
        "pb_ratio": 2.1,
        "ev_ebitda": 12.5,
        "roe": 12.8,
        "roce": 11.2,
        "debt_to_equity": 0.42,
        "current_ratio": 1.15,
        "dividend_yield": 0.38,
        "eps_growth_5y": 8.5,
        "revenue_growth_5y": 15.2,
    }


@pytest.fixture
def sample_news_data() -> dict:
    """Sample news scraping result."""
    return {
        "symbol": "RELIANCE",
        "source": "Moneycontrol",
        "articles_count": 3,
        "articles": [
            {
                "title": "Reliance Industries Q3 Results: Net profit rises 15%",
                "summary": "Reliance reported strong quarterly results...",
                "url": "https://example.com/news1",
                "published": datetime.now().isoformat(),
                "source": "Moneycontrol",
            },
            {
                "title": "RIL to invest Rs 75,000 crore in new energy business",
                "summary": "The company announced major investments...",
                "url": "https://example.com/news2",
                "published": datetime.now().isoformat(),
                "source": "Moneycontrol",
            },
            {
                "title": "Analysts upgrade Reliance with target of Rs 2,800",
                "summary": "Multiple brokerages have upgraded...",
                "url": "https://example.com/news3",
                "published": datetime.now().isoformat(),
                "source": "Moneycontrol",
            },
        ],
        "fetched_at": datetime.now().isoformat(),
    }


# ============================================================
# Mock Fixtures
# ============================================================

@pytest.fixture
def mock_yfinance():
    """Mock yfinance to avoid real API calls in unit tests."""
    with patch('yfinance.Ticker') as mock_ticker:
        # Create a mock ticker instance
        ticker_instance = MagicMock()
        mock_ticker.return_value = ticker_instance
        
        # Mock info
        ticker_instance.info = {
            "shortName": "Reliance Industries",
            "sector": "Energy",
            "industry": "Oil & Gas Refining & Marketing",
            "marketCap": 16500000000000,
            "fiftyTwoWeekHigh": 2856.15,
            "fiftyTwoWeekLow": 2180.00,
            "averageVolume": 8000000,
            "trailingPE": 25.6,
            "priceToBook": 2.1,
            "returnOnEquity": 0.128,
        }
        
        # Mock history
        dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
        np.random.seed(42)
        base_price = 2400
        returns = np.random.normal(0.0005, 0.02, 100)
        prices = base_price * np.exp(np.cumsum(returns))
        
        ticker_instance.history.return_value = pd.DataFrame({
            'Open': prices * (1 + np.random.uniform(-0.01, 0.01, 100)),
            'High': prices * (1 + np.random.uniform(0, 0.02, 100)),
            'Low': prices * (1 - np.random.uniform(0, 0.02, 100)),
            'Close': prices,
            'Volume': np.random.randint(1000000, 10000000, 100),
        }, index=dates)
        
        yield mock_ticker


@pytest.fixture
def mock_httpx_response():
    """Mock httpx response for web scraping tests."""
    def _create_response(content: str, status_code: int = 200):
        response = MagicMock()
        response.status_code = status_code
        response.text = content
        return response
    return _create_response


@pytest.fixture
def sample_moneycontrol_html() -> str:
    """Sample Moneycontrol HTML for news scraping tests."""
    return """
    <html>
    <body>
        <ul class="news-list">
            <li class="clearfix">
                <a href="/news/business/reliance-q3-results-13781179.html">
                    Reliance Q3 Results: Net profit rises 15%
                </a>
                <p>Reliance Industries reported strong quarterly results with net profit...</p>
                <span class="date">2 hours ago</span>
            </li>
            <li class="clearfix">
                <a href="/news/business/ril-investment-13781180.html">
                    RIL announces Rs 75,000 crore investment in green energy
                </a>
                <p>The company announced major investments in renewable energy...</p>
                <span class="date">5 hours ago</span>
            </li>
        </ul>
    </body>
    </html>
    """


# ============================================================
# Validation Helpers
# ============================================================

@pytest.fixture
def validate_price_data():
    """Validator for price data structure."""
    def _validate(data: dict) -> bool:
        required_fields = [
            "symbol", "current_price", "previous_close", 
            "change", "change_percent", "volume"
        ]
        
        # Check required fields exist
        for field in required_fields:
            if field not in data:
                return False
        
        # Validate price is positive
        if data["current_price"] <= 0:
            return False
        
        # Validate change calculation
        expected_change = data["current_price"] - data["previous_close"]
        if abs(data["change"] - expected_change) > 0.01:
            return False
        
        return True
    
    return _validate


@pytest.fixture
def validate_technical_indicators():
    """Validator for technical indicators."""
    def _validate(data: dict) -> bool:
        # RSI should be between 0 and 100
        if "rsi" in data and not (0 <= data["rsi"] <= 100):
            return False
        
        # Bollinger bands should be ordered correctly
        if all(k in data for k in ["bb_upper", "bb_middle", "bb_lower"]):
            if not (data["bb_upper"] > data["bb_middle"] > data["bb_lower"]):
                return False
        
        return True
    
    return _validate


# ============================================================
# Test Markers and Categories
# ============================================================

def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests (fast, no external deps)")
    config.addinivalue_line("markers", "integration: Integration tests (external APIs)")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "critical: Critical financial accuracy tests")


# ============================================================
# Async Fixtures
# ============================================================

@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
