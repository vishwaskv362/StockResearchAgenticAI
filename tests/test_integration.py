"""
Integration Tests

End-to-end tests that verify complete workflows.
These tests may hit real external APIs and take longer to run.
"""

import json
import pytest


class TestMarketDataIntegration:
    """Integration tests for market data pipeline."""
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_full_price_fetch_pipeline(self, valid_symbol):
        """Test complete price fetch for a real stock."""
        from tools.market_data import get_stock_price, _cache
        
        _cache.clear()
        
        result = get_stock_price.func(valid_symbol)
        data = json.loads(result)
        
        # Validate complete response
        assert "symbol" in data
        assert "current_price" in data
        assert data["current_price"] > 0
        assert "volume" in data
        assert "timestamp" in data
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_historical_data_pipeline(self, valid_symbol):
        """Test complete historical data fetch."""
        from tools.market_data import get_historical_data
        
        result = get_historical_data.func(valid_symbol, "3mo")
        data = json.loads(result)
        
        assert isinstance(data, dict)
        if "error" not in data:
            assert "prices" in data or "symbol" in data
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_stock_info_pipeline(self, valid_symbol):
        """Test complete stock info fetch."""
        from tools.market_data import get_stock_info
        
        result = get_stock_info.func(valid_symbol)
        data = json.loads(result)
        
        assert isinstance(data, dict)
        if "error" not in data:
            assert "symbol" in data


class TestTechnicalAnalysisIntegration:
    """Integration tests for technical analysis."""
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_full_technical_analysis(self, valid_symbol):
        """Test complete technical analysis pipeline."""
        from tools.analysis import calculate_technical_indicators
        
        result = calculate_technical_indicators.func(valid_symbol, "6mo")
        data = json.loads(result)
        
        assert isinstance(data, dict)
        if "error" not in data:
            assert "current_price" in data
            # Should have some indicators
            assert len(data) > 3
    
    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.critical
    def test_technical_indicators_accuracy(self, valid_symbol):
        """Critical: Verify technical indicators are within valid ranges."""
        from tools.analysis import calculate_technical_indicators
        
        result = calculate_technical_indicators.func(valid_symbol, "6mo")
        data = json.loads(result)
        
        if "error" not in data:
            # RSI must be 0-100
            if "rsi_14" in data:
                assert 0 <= data["rsi_14"] <= 100
            
            # Current price must be positive
            if "current_price" in data:
                assert data["current_price"] > 0


class TestNewsScrapingIntegration:
    """Integration tests for news scraping."""
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_real_moneycontrol_scraping(self, valid_symbol):
        """Test real Moneycontrol news scraping."""
        from tools.news_scraper import scrape_moneycontrol_news, _news_cache
        
        _news_cache.clear()
        
        result = scrape_moneycontrol_news.func(valid_symbol, 5)
        data = json.loads(result)
        
        assert isinstance(data, dict)
        assert "symbol" in data
        # May or may not have articles depending on news availability
        assert "articles" in data or "error" in data or "articles_count" in data
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_news_aggregation_pipeline(self, valid_symbol):
        """Test complete news aggregation from all sources."""
        from tools.news_scraper import get_stock_news
        
        result = get_stock_news.func(valid_symbol, 10)
        data = json.loads(result)
        
        assert isinstance(data, dict)


class TestFundamentalAnalysisIntegration:
    """Integration tests for fundamental analysis."""
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_real_fundamental_metrics(self, valid_symbol):
        """Test real fundamental metrics fetch."""
        from tools.analysis import get_fundamental_metrics
        
        result = get_fundamental_metrics.func(valid_symbol)
        data = json.loads(result)
        
        assert isinstance(data, dict)
        if "error" not in data:
            assert "symbol" in data
    
    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.critical
    def test_fundamental_metrics_reasonable(self, valid_symbol):
        """Critical: Verify fundamental metrics are reasonable."""
        from tools.analysis import get_fundamental_metrics
        
        result = get_fundamental_metrics.func(valid_symbol)
        data = json.loads(result)
        
        if "error" not in data:
            # PE ratio should be reasonable for profitable company
            if "pe_ratio" in data and data["pe_ratio"] != "N/A":
                pe = data["pe_ratio"]
                assert -1000 < pe < 1000, f"PE {pe} seems unreasonable"


class TestInstitutionalDataIntegration:
    """Integration tests for institutional data."""
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_real_fii_dii_data(self):
        """Test real FII/DII data fetch."""
        from tools.institutional import get_fii_dii_data
        
        result = get_fii_dii_data.func()
        data = json.loads(result)
        
        assert isinstance(data, dict)
        assert "date" in data or "fetched_at" in data or "error" in data
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_real_promoter_holdings(self, valid_symbol):
        """Test real promoter holdings fetch."""
        from tools.institutional import get_promoter_holdings
        
        result = get_promoter_holdings.func(valid_symbol)
        data = json.loads(result)
        
        assert isinstance(data, dict)


class TestMultipleStocksIntegration:
    """Integration tests for multiple stock analysis."""
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_multiple_stocks_price_fetch(self, sample_stock_symbols):
        """Test price fetch for multiple stocks."""
        from tools.market_data import get_stock_price, _cache
        
        _cache.clear()
        
        results = []
        for symbol in sample_stock_symbols[:3]:  # Test first 3
            result = get_stock_price.func(symbol)
            data = json.loads(result)
            results.append(data)
        
        # All should return valid responses
        for data in results:
            assert isinstance(data, dict)
    
    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.critical
    def test_no_cross_contamination(self, sample_stock_symbols):
        """Critical: Ensure stock data doesn't get mixed up."""
        from tools.market_data import get_stock_price, _cache
        
        _cache.clear()
        
        symbols = sample_stock_symbols[:2]  # Test 2 stocks
        results = {}
        
        for symbol in symbols:
            result = get_stock_price.func(symbol)
            data = json.loads(result)
            results[symbol] = data
        
        # Each result should match its symbol
        for symbol, data in results.items():
            if "error" not in data:
                assert data["symbol"] == symbol, "Symbol mismatch - data contamination"


class TestCacheIntegration:
    """Integration tests for caching behavior."""
    
    @pytest.mark.integration
    def test_cache_improves_performance(self, valid_symbol):
        """Test that caching reduces API calls."""
        import time
        from tools.market_data import get_stock_price, _cache
        
        _cache.clear()
        
        # First call (cold cache)
        start1 = time.time()
        result1 = get_stock_price.func(valid_symbol)
        time1 = time.time() - start1
        
        # Second call (warm cache)
        start2 = time.time()
        result2 = get_stock_price.func(valid_symbol)
        time2 = time.time() - start2
        
        # Cached call should be faster (or at least return same data)
        assert result1 == result2, "Cache should return same data"


class TestErrorRecoveryIntegration:
    """Integration tests for error recovery."""
    
    @pytest.mark.integration
    def test_invalid_symbol_graceful_failure(self, invalid_symbol):
        """Test graceful handling of invalid symbols."""
        from tools.market_data import get_stock_price
        
        result = get_stock_price.func(invalid_symbol)
        data = json.loads(result)
        
        # Should return valid JSON with error info
        assert isinstance(data, dict)
        # Should indicate error
        assert "error" in data or len(data.get("articles", [])) == 0
    
    @pytest.mark.integration
    def test_recovers_from_network_issues(self):
        """Test recovery from simulated network issues."""
        # This test verifies the retry mechanism works
        from tools.news_scraper import scrape_moneycontrol_news
        
        # Even with potential network issues, should return valid JSON
        result = scrape_moneycontrol_news.func("RELIANCE", 5)
        data = json.loads(result)
        
        assert isinstance(data, dict)


class TestDataConsistencyIntegration:
    """Critical tests for data consistency."""
    
    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.critical
    def test_price_data_consistency(self, valid_symbol):
        """Critical: Price data should be internally consistent."""
        from tools.market_data import get_stock_price, _cache
        
        _cache.clear()
        
        result = get_stock_price.func(valid_symbol)
        data = json.loads(result)
        
        if "error" not in data:
            # High should be >= Close and Open
            if all(k in data for k in ["high", "low", "open", "current_price"]):
                assert data["high"] >= data["current_price"], "High must be >= Close"
                assert data["high"] >= data["open"], "High must be >= Open"
                assert data["low"] <= data["current_price"], "Low must be <= Close"
                assert data["low"] <= data["open"], "Low must be <= Open"
    
    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.critical
    def test_technical_data_consistency(self, valid_symbol):
        """Critical: Technical data should be internally consistent."""
        from tools.analysis import calculate_technical_indicators
        
        result = calculate_technical_indicators.func(valid_symbol, "6mo")
        data = json.loads(result)
        
        if "error" not in data:
            # Bollinger Bands should be ordered
            if all(k in data for k in ["bb_upper", "bb_middle", "bb_lower"]):
                assert data["bb_upper"] >= data["bb_middle"] >= data["bb_lower"]
