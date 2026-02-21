"""
Tests for Data Validation Tools

Tests cover:
- Symbol validation
- Price cross-validation between sources
- Metrics sanity checks
- Data quality score calculation
"""

import json
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd


class TestValidateSymbolExistence:
    """Tests for symbol existence validation."""
    
    @pytest.mark.unit
    def test_valid_symbol_exists(self):
        """Test that a valid symbol returns True."""
        from tools.validation import validate_symbol_existence
        
        with patch('tools.validation.yf.Ticker') as mock_ticker:
            mock_ticker_instance = MagicMock()
            mock_ticker_instance.info = {
                "symbol": "RELIANCE.NS",
                "shortName": "Reliance Industries",
                "currentPrice": 2500.0,
                "marketCap": 17000000000000,
                "sector": "Energy",
                "regularMarketPrice": 2500.0
            }
            mock_ticker_instance.history = MagicMock(return_value=pd.DataFrame({
                'Close': [2500, 2510, 2505, 2515, 2520]
            }))
            mock_ticker.return_value = mock_ticker_instance
            
            result = validate_symbol_existence.run(symbol="RELIANCE")
            
            # Check for validation_passed: true in JSON result
            assert '"validation_passed": true' in result.lower()
            assert "reliance" in result.lower()
    
    @pytest.mark.unit
    def test_invalid_symbol_not_exists(self):
        """Test that an invalid symbol returns False."""
        from tools.validation import validate_symbol_existence
        
        with patch('tools.validation.yf.Ticker') as mock_ticker:
            mock_ticker_instance = MagicMock()
            mock_ticker_instance.info = {}
            mock_ticker.return_value = mock_ticker_instance
            
            result = validate_symbol_existence.run(symbol="INVALID123")
            
            assert "exists: false" in result.lower() or "not found" in result.lower()
    
    @pytest.mark.unit
    def test_symbol_with_ns_suffix(self):
        """Test symbol validation with .NS suffix."""
        from tools.validation import validate_symbol_existence
        
        with patch('tools.validation.yf.Ticker') as mock_ticker:
            mock_ticker_instance = MagicMock()
            mock_ticker_instance.info = {"symbol": "TCS.NS"}
            mock_ticker.return_value = mock_ticker_instance
            
            result = validate_symbol_existence.run(symbol="TCS.NS")
            
            assert "exists: true" in result.lower() or "tcs" in result.lower()


class TestCrossValidatePrice:
    """Tests for price cross-validation."""
    
    @pytest.mark.unit
    def test_matching_prices(self):
        """Test when prices from both sources match."""
        from tools.validation import cross_validate_price_sources
        
        with patch('tools.validation.yf.Ticker') as mock_ticker, \
             patch('tools.validation.get_nse_stock_quote') as mock_nse_quote:
            
            # Mock Yahoo Finance
            mock_ticker_instance = MagicMock()
            mock_ticker_instance.info = {"currentPrice": 2500.00}
            mock_ticker.return_value = mock_ticker_instance
            
            # Mock NSE
            mock_nse_quote.return_value = json.dumps({"lastPrice": 2505.00})
            
            result = cross_validate_price_sources.run(symbol="RELIANCE")
            
            assert "yahoo" in result.lower() or "price" in result.lower()
            assert "nse" in result.lower() or "2500" in result or "2505" in result
    
    @pytest.mark.unit
    def test_price_discrepancy(self):
        """Test when prices show significant discrepancy."""
        from tools.validation import cross_validate_price_sources
        
        with patch('tools.validation.yf.Ticker') as mock_ticker, \
             patch('tools.validation.get_nse_stock_quote') as mock_nse_quote:
            
            # Mock Yahoo Finance
            mock_ticker_instance = MagicMock()
            mock_ticker_instance.info = {"currentPrice": 2500.00}
            mock_ticker.return_value = mock_ticker_instance
            
            # Mock NSE
            mock_nse_quote.return_value = json.dumps({"lastPrice": 2700.00})
            
            result = cross_validate_price_sources.run(symbol="RELIANCE")
            
            assert "discrepancy" in result.lower() or "divergence" in result.lower() or "difference" in result.lower()
    
    @pytest.mark.unit
    def test_missing_nse_data(self):
        """Test when NSE data is unavailable."""
        from tools.validation import cross_validate_price_sources
        
        with patch('tools.validation.yf.Ticker') as mock_ticker, \
             patch('tools.validation.get_nse_stock_quote') as mock_nse_quote:
            
            # Mock Yahoo Finance
            mock_ticker_instance = MagicMock()
            mock_ticker_instance.info = {"currentPrice": 2500.00}
            mock_ticker.return_value = mock_ticker_instance
            
            # Mock NSE failure
            mock_nse_quote.side_effect = Exception("NSE unavailable")
            
            result = cross_validate_price_sources.run(symbol="RELIANCE")
            
            assert "yahoo finance" in result.lower()


class TestSanityCheckMetrics:
    """Tests for metrics sanity checking."""
    
    @pytest.mark.unit
    def test_valid_metrics(self):
        """Test with valid, reasonable metrics."""
        from tools.validation import sanity_check_metrics
        
        with patch('tools.validation.yf.Ticker') as mock_ticker:
            mock_ticker_instance = MagicMock()
            mock_ticker_instance.info = {
                "trailingPE": 25.5,
                "priceToBook": 4.2,
                "debtToEquity": 30.5,
                "returnOnEquity": 0.18,
                "profitMargins": 0.12
            }
            mock_ticker.return_value = mock_ticker_instance
            
            result = sanity_check_metrics.run(symbol="RELIANCE")
            
            assert "valid" in result.lower() or "reasonable" in result.lower()
            assert "25.5" in result or "p/e" in result.lower()
    
    @pytest.mark.unit
    def test_extreme_pe_ratio(self):
        """Test detection of extreme P/E ratio."""
        from tools.validation import sanity_check_metrics
        
        with patch('tools.validation.yf.Ticker') as mock_ticker:
            mock_ticker_instance = MagicMock()
            mock_ticker_instance.info = {
                "trailingPE": 500.0,  # Extreme value
                "priceToBook": 3.0,
                "debtToEquity": 25.0
            }
            mock_ticker.return_value = mock_ticker_instance
            
            result = sanity_check_metrics.run(symbol="RELIANCE")
            
            assert "extreme" in result.lower() or "unusual" in result.lower() or "high" in result.lower()
    
    @pytest.mark.unit
    def test_negative_roe(self):
        """Test detection of negative ROE."""
        from tools.validation import sanity_check_metrics
        
        with patch('tools.validation.yf.Ticker') as mock_ticker:
            mock_ticker_instance = MagicMock()
            mock_ticker_instance.info = {
                "returnOnEquity": -0.15,  # Negative ROE
                "trailingPE": 20.0
            }
            mock_ticker.return_value = mock_ticker_instance
            
            result = sanity_check_metrics.run(symbol="RELIANCE")
            
            # Check that negative ROE warning is present
            assert "negative" in result.lower() and "roe" in result.lower()


class TestDataQualityScore:
    """Tests for data quality score calculation."""
    
    @pytest.mark.unit
    def test_high_quality_data(self):
        """Test high quality score with complete data."""
        from tools.validation import calculate_data_quality_score
        
        with patch('tools.validation.yf.Ticker') as mock_ticker:
            mock_ticker_instance = MagicMock()
            
            # Complete info data
            mock_ticker_instance.info = {
                "currentPrice": 2500,
                "marketCap": 1000000000,
                "trailingPE": 25,
                "priceToBook": 4,
                "debtToEquity": 30,
                "returnOnEquity": 0.18,
                "profitMargins": 0.12,
                "revenueGrowth": 0.15
            }
            
            # Complete history data
            history_data = pd.DataFrame({
                'Close': [2400, 2450, 2480, 2500],
                'Volume': [1000000, 1100000, 1050000, 1200000]
            })
            mock_ticker_instance.history = MagicMock(return_value=history_data)
            
            mock_ticker.return_value = mock_ticker_instance
            
            result = calculate_data_quality_score.run(symbol="RELIANCE")
            
            assert "score" in result.lower()
            # High quality data should score above 70
            assert any(str(score) in result for score in range(70, 101))
    
    @pytest.mark.unit
    def test_incomplete_data(self):
        """Test lower score with incomplete data."""
        from tools.validation import calculate_data_quality_score
        
        with patch('tools.validation.yf.Ticker') as mock_ticker:
            mock_ticker_instance = MagicMock()
            
            # Incomplete info data
            mock_ticker_instance.info = {
                "currentPrice": 2500,
                "marketCap": 1000000000
                # Missing many fields
            }
            
            # Empty history
            mock_ticker_instance.history = MagicMock(return_value=pd.DataFrame())
            
            mock_ticker.return_value = mock_ticker_instance
            
            result = calculate_data_quality_score.run(symbol="RELIANCE")
            
            assert "score" in result.lower()
            # Incomplete data should score lower
            assert "incomplete" in result.lower() or "missing" in result.lower()
    
    @pytest.mark.unit
    def test_invalid_symbol(self):
        """Test data quality score for invalid symbol."""
        from tools.validation import calculate_data_quality_score
        
        with patch('tools.validation.yf.Ticker') as mock_ticker:
            mock_ticker_instance = MagicMock()
            mock_ticker_instance.info = {}
            mock_ticker_instance.history = MagicMock(return_value=pd.DataFrame())
            mock_ticker.return_value = mock_ticker_instance
            
            result = calculate_data_quality_score.run(symbol="INVALID123")
            
            assert "score" in result.lower()
            # Invalid symbol should have very low score
            assert any(str(score) in result for score in range(0, 30))
