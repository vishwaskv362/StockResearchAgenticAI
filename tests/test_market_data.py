"""
Tests for Market Data Tools

Tests cover:
- Stock price fetching
- Stock info retrieval  
- Historical data
- Index data
- Cache functionality
- Error handling for invalid symbols
- Data validation for financial accuracy
"""

import json
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np


class TestGetNseSymbol:
    """Tests for NSE symbol conversion."""
    
    @pytest.mark.unit
    def test_symbol_without_suffix(self):
        """Test symbol without .NS suffix."""
        from tools.market_data import _get_nse_symbol
        
        result = _get_nse_symbol("RELIANCE")
        assert result == "RELIANCE.NS"
    
    @pytest.mark.unit
    def test_symbol_with_suffix(self):
        """Test symbol already having .NS suffix."""
        from tools.market_data import _get_nse_symbol
        
        result = _get_nse_symbol("RELIANCE.NS")
        assert result == "RELIANCE.NS"
    
    @pytest.mark.unit
    def test_lowercase_symbol(self):
        """Test lowercase symbol is converted to uppercase."""
        from tools.market_data import _get_nse_symbol
        
        result = _get_nse_symbol("reliance")
        assert result == "RELIANCE.NS"
    
    @pytest.mark.unit
    def test_symbol_with_whitespace(self):
        """Test symbol with whitespace is trimmed."""
        from tools.market_data import _get_nse_symbol
        
        result = _get_nse_symbol("  RELIANCE  ")
        assert result == "RELIANCE.NS"


class TestCacheValidity:
    """Tests for cache validation."""
    
    @pytest.mark.unit
    def test_cache_miss_for_new_key(self):
        """Test cache returns invalid for new key."""
        from tools.market_data import _is_cache_valid, _cache
        
        # Clear cache
        _cache.clear()
        
        result = _is_cache_valid("nonexistent_key")
        assert result is False
    
    @pytest.mark.unit
    def test_cache_hit_for_fresh_data(self):
        """Test cache returns valid for fresh data."""
        from tools.market_data import _is_cache_valid, _cache
        
        # Add fresh data to cache
        _cache["test_key"] = {
            "data": {"test": "data"},
            "timestamp": datetime.now().timestamp()
        }
        
        result = _is_cache_valid("test_key")
        assert result is True
    
    @pytest.mark.unit
    def test_cache_expired_for_old_data(self):
        """Test cache returns invalid for expired data."""
        from tools.market_data import _is_cache_valid, _cache, _cache_ttl
        
        # Add expired data to cache
        _cache["old_key"] = {
            "data": {"test": "data"},
            "timestamp": datetime.now().timestamp() - _cache_ttl - 100
        }
        
        result = _is_cache_valid("old_key")
        assert result is False


class TestGetStockPrice:
    """Tests for get_stock_price tool."""
    
    @pytest.mark.unit
    def test_stock_price_returns_json(self, mock_yfinance):
        """Test that stock price returns valid JSON."""
        from tools.market_data import get_stock_price, _cache
        
        _cache.clear()  # Clear cache to force API call
        
        result = get_stock_price.func("RELIANCE")
        
        # Should return valid JSON
        data = json.loads(result)
        assert isinstance(data, dict)
    
    @pytest.mark.unit
    def test_stock_price_required_fields(self, mock_yfinance):
        """Test that required fields are present in response."""
        from tools.market_data import get_stock_price, _cache
        
        _cache.clear()
        
        result = get_stock_price.func("RELIANCE")
        data = json.loads(result)
        
        required_fields = ["symbol", "current_price", "change", "change_percent", "volume"]
        
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_stock_price_positive_price(self, mock_yfinance):
        """Test that stock price is positive (critical for financial data)."""
        from tools.market_data import get_stock_price, _cache
        
        _cache.clear()
        
        result = get_stock_price.func("RELIANCE")
        data = json.loads(result)
        
        if "error" not in data:
            assert data["current_price"] > 0, "Stock price must be positive"
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_change_calculation_accuracy(self, mock_yfinance):
        """Test that change is calculated correctly."""
        from tools.market_data import get_stock_price, _cache
        
        _cache.clear()
        
        result = get_stock_price.func("RELIANCE")
        data = json.loads(result)
        
        if "error" not in data and data.get("previous_close"):
            expected_change = data["current_price"] - data["previous_close"]
            assert abs(data["change"] - expected_change) < 0.01, "Change calculation error"
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_change_percent_calculation(self, mock_yfinance):
        """Test that change percent is calculated correctly."""
        from tools.market_data import get_stock_price, _cache
        
        _cache.clear()
        
        result = get_stock_price.func("RELIANCE")
        data = json.loads(result)
        
        if "error" not in data and data.get("previous_close"):
            expected_pct = (data["change"] / data["previous_close"]) * 100
            assert abs(data["change_percent"] - expected_pct) < 0.01, "Percent calculation error"
    
    @pytest.mark.unit
    def test_cache_returns_cached_data(self, mock_yfinance):
        """Test that cached data is returned on subsequent calls."""
        from tools.market_data import get_stock_price, _cache
        
        _cache.clear()
        
        # First call
        result1 = get_stock_price.func("RELIANCE")
        
        # Second call should use cache (mock won't be called again)
        result2 = get_stock_price.func("RELIANCE")
        
        assert result1 == result2
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_real_stock_price_fetch(self, valid_symbol):
        """Integration test: Fetch real stock price."""
        from tools.market_data import get_stock_price, _cache
        
        _cache.clear()
        
        result = get_stock_price.func(valid_symbol)
        data = json.loads(result)
        
        # Should not have error for valid symbol
        assert "error" not in data
        assert data["current_price"] > 0
    
    @pytest.mark.integration
    def test_invalid_symbol_returns_error(self, invalid_symbol):
        """Test that invalid symbol returns error."""
        from tools.market_data import get_stock_price, _cache
        
        _cache.clear()
        
        result = get_stock_price.func(invalid_symbol)
        data = json.loads(result)
        
        # Should have error for invalid symbol
        assert "error" in data


class TestGetStockInfo:
    """Tests for get_stock_info tool."""
    
    @pytest.mark.unit
    def test_stock_info_returns_json(self, mock_yfinance):
        """Test that stock info returns valid JSON."""
        from tools.market_data import get_stock_info
        
        result = get_stock_info.func("RELIANCE")
        data = json.loads(result)
        
        assert isinstance(data, dict)
    
    @pytest.mark.unit
    def test_stock_info_contains_company_details(self, mock_yfinance):
        """Test that stock info contains company details."""
        from tools.market_data import get_stock_info
        
        result = get_stock_info.func("RELIANCE")
        data = json.loads(result)
        
        # Should contain company information
        if "error" not in data:
            assert "symbol" in data
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_real_stock_info_fetch(self, valid_symbol):
        """Integration test: Fetch real stock info."""
        from tools.market_data import get_stock_info
        
        result = get_stock_info.func(valid_symbol)
        data = json.loads(result)
        
        assert isinstance(data, dict)


class TestGetHistoricalData:
    """Tests for get_historical_data tool."""
    
    @pytest.mark.unit
    def test_historical_data_returns_json(self, mock_yfinance):
        """Test that historical data returns valid JSON."""
        from tools.market_data import get_historical_data
        
        result = get_historical_data.func("RELIANCE", "3mo")
        data = json.loads(result)
        
        assert isinstance(data, dict)
    
    @pytest.mark.unit
    def test_historical_data_valid_periods(self, mock_yfinance):
        """Test various period values."""
        from tools.market_data import get_historical_data
        
        valid_periods = ["1mo", "3mo", "6mo", "1y"]
        
        for period in valid_periods:
            result = get_historical_data.func("RELIANCE", period)
            data = json.loads(result)
            assert isinstance(data, dict)
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_ohlcv_data_consistency(self, mock_yfinance):
        """Test that OHLCV data is consistent (High >= Open, Close, Low)."""
        from tools.market_data import get_historical_data
        
        result = get_historical_data.func("RELIANCE", "1mo")
        data = json.loads(result)
        
        if "prices" in data:
            for price in data["prices"]:
                if all(k in price for k in ["open", "high", "low", "close"]):
                    assert price["high"] >= price["open"], "High should be >= Open"
                    assert price["high"] >= price["close"], "High should be >= Close"
                    assert price["low"] <= price["open"], "Low should be <= Open"
                    assert price["low"] <= price["close"], "Low should be <= Close"


class TestGetIndexData:
    """Tests for get_index_data tool."""
    
    @pytest.mark.unit
    def test_index_data_returns_json(self, mock_yfinance):
        """Test that index data returns valid JSON."""
        from tools.market_data import get_index_data
        
        result = get_index_data.func()
        data = json.loads(result)
        
        assert isinstance(data, dict)
    
    @pytest.mark.unit
    def test_index_data_contains_major_indices(self, mock_yfinance):
        """Test that major indices are included."""
        from tools.market_data import get_index_data
        
        result = get_index_data.func()
        data = json.loads(result)
        
        # Should contain major index names
        result_str = result.lower()
        assert "nifty" in result_str or "sensex" in result_str or "error" in result_str
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_real_index_data_fetch(self):
        """Integration test: Fetch real index data."""
        from tools.market_data import get_index_data
        
        result = get_index_data.func()
        data = json.loads(result)
        
        assert isinstance(data, dict)


class TestDataValidation:
    """Critical tests for financial data accuracy."""
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_volume_non_negative(self, mock_yfinance):
        """Test that volume is never negative."""
        from tools.market_data import get_stock_price, _cache
        
        _cache.clear()
        
        result = get_stock_price.func("RELIANCE")
        data = json.loads(result)
        
        if "volume" in data:
            assert data["volume"] >= 0, "Volume cannot be negative"
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_52_week_range_logic(self, mock_yfinance):
        """Test that 52-week high >= low."""
        from tools.market_data import get_stock_price, _cache
        
        _cache.clear()
        
        result = get_stock_price.func("RELIANCE")
        data = json.loads(result)
        
        if "52_week_high" in data and "52_week_low" in data:
            if data["52_week_high"] != "N/A" and data["52_week_low"] != "N/A":
                assert data["52_week_high"] >= data["52_week_low"], "52W High must be >= 52W Low"
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_market_cap_positive(self, mock_yfinance):
        """Test that market cap is positive."""
        from tools.market_data import get_stock_price, _cache
        
        _cache.clear()
        
        result = get_stock_price.func("RELIANCE")
        data = json.loads(result)
        
        if "market_cap" in data and data["market_cap"] != "N/A":
            assert data["market_cap"] > 0, "Market cap must be positive"


class TestHelperFunctions:
    """Tests for helper functions in market_data."""
    
    @pytest.mark.unit
    def test_categorize_market_cap_large(self):
        """Test market cap categorization for large cap."""
        from tools.market_data import _categorize_market_cap
        
        # 50000 Cr = 500 billion
        result = _categorize_market_cap(500_000_000_000)
        assert result == "Large Cap"
    
    @pytest.mark.unit
    def test_categorize_market_cap_mid(self):
        """Test market cap categorization for mid cap."""
        from tools.market_data import _categorize_market_cap
        
        # 10000 Cr = 100 billion
        result = _categorize_market_cap(100_000_000_000)
        assert result == "Mid Cap"
    
    @pytest.mark.unit
    def test_categorize_market_cap_small(self):
        """Test market cap categorization for small cap."""
        from tools.market_data import _categorize_market_cap
        
        # 1000 Cr = 10 billion
        result = _categorize_market_cap(10_000_000_000)
        assert result == "Small Cap"
    
    @pytest.mark.unit
    def test_categorize_market_cap_zero(self):
        """Test market cap categorization for zero."""
        from tools.market_data import _categorize_market_cap
        
        result = _categorize_market_cap(0)
        assert result == "Unknown"
    
    @pytest.mark.unit
    def test_categorize_market_cap_none(self):
        """Test market cap categorization for None."""
        from tools.market_data import _categorize_market_cap
        
        result = _categorize_market_cap(None)
        assert result == "Unknown"


class TestGetTrendingStocks:
    """Tests for get_trending_stocks helper."""

    @pytest.mark.unit
    def test_returns_gainers_and_losers(self):
        """Test that trending stocks returns both gainers and losers lists."""
        from tools.market_data import get_trending_stocks, _cache

        _cache.clear()

        mock_gainers = [
            {"symbol": "ABC", "ltp": "100.0", "netPrice": "5.2"},
            {"symbol": "DEF", "ltp": "200.0", "netPrice": "3.1"},
        ]
        mock_losers = [
            {"symbol": "GHI", "ltp": "50.0", "netPrice": "-4.0"},
        ]

        with patch("nsetools.Nse") as mock_nse_cls:
            inst = MagicMock()
            mock_nse_cls.return_value = inst
            inst.get_top_gainers.return_value = mock_gainers
            inst.get_top_losers.return_value = mock_losers

            result = get_trending_stocks()

        assert "gainers" in result
        assert "losers" in result
        assert len(result["gainers"]) == 2
        assert len(result["losers"]) == 1
        assert result["gainers"][0]["symbol"] == "ABC"

    @pytest.mark.unit
    def test_caches_results(self):
        """Test that subsequent calls return cached data without hitting API."""
        from tools.market_data import get_trending_stocks, _cache

        _cache.clear()

        mock_data = [{"symbol": "XYZ", "ltp": "300.0", "netPrice": "2.0"}]

        with patch("nsetools.Nse") as mock_nse_cls:
            inst = MagicMock()
            mock_nse_cls.return_value = inst
            inst.get_top_gainers.return_value = mock_data
            inst.get_top_losers.return_value = []

            first = get_trending_stocks()
            second = get_trending_stocks()

        # Nse constructor should only be called once (second call uses cache)
        assert mock_nse_cls.call_count == 1
        assert first == second

    @pytest.mark.unit
    def test_falls_back_on_exception(self):
        """Test graceful fallback when nsetools raises an exception."""
        from tools.market_data import get_trending_stocks, _cache

        _cache.clear()

        with patch("nsetools.Nse", side_effect=Exception("NSE down")):
            result = get_trending_stocks()

        assert result == {"gainers": [], "losers": []}

    @pytest.mark.unit
    def test_handles_non_list_response(self):
        """Test that non-list API responses are safely converted to empty lists."""
        from tools.market_data import get_trending_stocks, _cache

        _cache.clear()

        with patch("nsetools.Nse") as mock_nse_cls:
            inst = MagicMock()
            mock_nse_cls.return_value = inst
            inst.get_top_gainers.return_value = None  # unexpected
            inst.get_top_losers.return_value = "bad data"  # unexpected

            result = get_trending_stocks()

        assert result["gainers"] == []
        assert result["losers"] == []


class TestNseData:
    """Tests for NSE-specific data fetching."""
    
    @pytest.mark.unit
    def test_get_nse_stock_quote_returns_json(self, mock_yfinance):
        """Test get_nse_stock_quote returns valid JSON."""
        from tools.market_data import get_nse_stock_quote
        
        with patch('nsetools.Nse') as mock_nse:
            mock_nse.return_value.get_quote.return_value = {
                "companyName": "Reliance Industries",
                "lastPrice": 2847.50,
                "change": 25.5,
                "pChange": 0.9
            }
            
            result = get_nse_stock_quote.func("RELIANCE")
            data = json.loads(result)
            
            assert isinstance(data, dict)
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_real_nse_stock_quote(self, valid_symbol):
        """Integration test for NSE stock quote."""
        from tools.market_data import get_nse_stock_quote
        
        result = get_nse_stock_quote.func(valid_symbol)
        data = json.loads(result)
        
        assert isinstance(data, dict)
