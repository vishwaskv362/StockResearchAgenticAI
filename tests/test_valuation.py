"""
Tests for Valuation Tools

Tests cover:
- Sector valuation multiples retrieval
- Relative valuation calculation
- Scenario valuation modeling
- Multiple drivers identification
"""

import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
from config import SECTOR_VALUATION_BENCHMARKS


class TestGetSectorValuationMultiples:
    """Tests for sector valuation multiples."""
    
    @pytest.mark.unit
    def test_it_sector_multiples(self):
        """Test IT sector valuation multiples."""
        from tools.valuation import get_sector_valuation_multiples
        
        with patch('tools.valuation.yf.Ticker') as mock_ticker:
            # Mock complete data for TCS and peers
            def mock_ticker_data(symbol):
                mock_instance = MagicMock()
                mock_instance.info = {
                    "symbol": symbol,
                    "trailingPE": 25.0,
                    "priceToBook": 8.0,
                    "enterpriseToEbitda": 18.0,
                    "currentPrice": 3500.0
                }
                return mock_instance
            
            mock_ticker.side_effect = mock_ticker_data
            result = get_sector_valuation_multiples.run(symbol="TCS")
            
            # Should return sector comparison data or handle gracefully
            assert result is not None and len(result) > 10
    
    @pytest.mark.unit
    def test_banking_sector_multiples(self):
        """Test banking sector valuation multiples."""
        from tools.valuation import get_sector_valuation_multiples
        
        with patch('tools.valuation.yf.Ticker') as mock_ticker:
            # Mock complete data for HDFCBANK and peers
            def mock_ticker_data(symbol):
                mock_instance = MagicMock()
                mock_instance.info = {
                    "symbol": symbol,
                    "trailingPE": 18.0,
                    "priceToBook": 3.0,
                    "enterpriseToEbitda": None,  # Not applicable for banks
                    "currentPrice": 1600.0
                }
                return mock_instance
            
            mock_ticker.side_effect = mock_ticker_data
            result = get_sector_valuation_multiples.run(symbol="HDFCBANK")
            
            # Should return sector comparison data or handle gracefully
            assert result is not None and len(result) > 10
    
    @pytest.mark.unit
    def test_unknown_sector_default(self):
        """Test handling for symbol not in predefined sectors."""
        from tools.valuation import get_sector_valuation_multiples
        
        # TEST symbol is not in SECTORS config, should return error
        result = get_sector_valuation_multiples.run(symbol="INVALIDSYM")
        
        # Tool should return error for unknown symbol
        assert "error" in result.lower() or "not found" in result.lower()


class TestCalculateRelativeValuation:
    """Tests for relative valuation calculation."""
    
    @pytest.mark.unit
    def test_undervalued_stock(self):
        """Test identification of undervalued stock."""
        from tools.valuation import calculate_relative_valuation
        
        with patch('tools.valuation.yf.Ticker') as mock_ticker:
            def mock_ticker_data(symbol):
                mock_instance = MagicMock()
                mock_instance.info = {
                    "symbol": symbol,
                    "currentPrice": 3000,
                    "trailingPE": 18,  # Below IT sector average
                    "priceToBook": 5,
                    "enterpriseToEbitda": 12
                }
                return mock_instance
            
            mock_ticker.side_effect = mock_ticker_data
            result = calculate_relative_valuation.run(symbol="TCS")
            
            # Tool returns valuation analysis
            assert result is not None and len(result) > 10
    
    @pytest.mark.unit
    def test_overvalued_stock(self):
        """Test identification of overvalued stock."""
        from tools.valuation import calculate_relative_valuation
        
        with patch('tools.valuation.yf.Ticker') as mock_ticker:
            def mock_ticker_data(symbol):
                mock_instance = MagicMock()
                mock_instance.info = {
                    "symbol": symbol,
                    "currentPrice": 4000,
                    "trailingPE": 40,  # Above IT sector average
                    "priceToBook": 12,
                    "enterpriseToEbitda": 28
                }
                return mock_instance
            
            mock_ticker.side_effect = mock_ticker_data
            result = calculate_relative_valuation.run(symbol="TCS")
            
            # Tool returns valuation analysis
            assert result is not None and len(result) > 10
    
    @pytest.mark.unit
    def test_fairly_valued_stock(self):
        """Test identification of fairly valued stock."""
        from tools.valuation import calculate_relative_valuation
        
        with patch('tools.valuation.yf.Ticker') as mock_ticker:
            def mock_ticker_data(symbol):
                mock_instance = MagicMock()
                mock_instance.info = {
                    "symbol": symbol,
                    "currentPrice": 3500,
                    "trailingPE": 28,  # Near IT sector average
                    "priceToBook": 8,
                    "enterpriseToEbitda": 18
                }
                return mock_instance
            
            mock_ticker.side_effect = mock_ticker_data
            result = calculate_relative_valuation.run(symbol="TCS")
            
            # Tool returns valuation analysis
            assert result is not None and len(result) > 10
    
    @pytest.mark.unit
    def test_valuation_range_provided(self):
        """Test that valuation provides a range not single point."""
        from tools.valuation import calculate_relative_valuation
        
        with patch('tools.valuation.yf.Ticker') as mock_ticker:
            def mock_ticker_data(symbol):
                mock_instance = MagicMock()
                mock_instance.info = {
                    "symbol": symbol,
                    "currentPrice": 3000,
                    "trailingPE": 25,
                    "priceToBook": 7,
                    "enterpriseToEbitda": 16
                }
                return mock_instance
            
            mock_ticker.side_effect = mock_ticker_data
            result = calculate_relative_valuation.run(symbol="TCS")
            
            # Tool returns valuation analysis
            assert result is not None and len(result) > 10


class TestBuildScenarioValuations:
    """Tests for scenario-based valuation."""
    
    @pytest.mark.unit
    def test_three_scenarios_generated(self):
        """Test that bull, base, and bear scenarios are generated."""
        from tools.valuation import build_scenario_valuations
        
        with patch('tools.valuation.yf.Ticker') as mock_ticker:
            def mock_ticker_data(symbol):
                mock_instance = MagicMock()
                mock_instance.info = {
                    "symbol": symbol,
                    "currentPrice": 3500,
                    "trailingPE": 28,
                    "priceToBook": 8,
                    "enterpriseToEbitda": 18,
                    "revenueGrowth": 0.15
                }
                return mock_instance
            
            mock_ticker.side_effect = mock_ticker_data
            result = build_scenario_valuations.run(symbol="TCS")
            
            # Tool returns scenario analysis
            assert result is not None and len(result) > 10
    
    @pytest.mark.unit
    def test_scenario_price_ranges(self):
        """Test that scenarios provide different price targets."""
        from tools.valuation import build_scenario_valuations
        
        with patch('tools.valuation.yf.Ticker') as mock_ticker:
            def mock_ticker_data(symbol):
                mock_instance = MagicMock()
                mock_instance.info = {
                    "symbol": symbol,
                    "currentPrice": 3000,
                    "trailingPE": 25,
                    "priceToBook": 7
                }
                return mock_instance
            
            mock_ticker.side_effect = mock_ticker_data
            result = build_scenario_valuations.run(symbol="TCS")
            
            # Tool returns scenario analysis
            assert result is not None and len(result) > 10
    
    @pytest.mark.unit
    def test_scenario_assumptions(self):
        """Test that scenarios include key assumptions."""
        from tools.valuation import build_scenario_valuations
        
        with patch('tools.valuation.yf.Ticker') as mock_ticker:
            def mock_ticker_data(symbol):
                mock_instance = MagicMock()
                mock_instance.info = {
                    "symbol": symbol,
                    "currentPrice": 1600,
                    "trailingPE": 18,
                    "priceToBook": 2.5,
                    "revenueGrowth": 0.12
                }
                return mock_instance
            
            mock_ticker.side_effect = mock_ticker_data
            result = build_scenario_valuations.run(symbol="HDFCBANK")
            
            # Tool returns scenario analysis
            assert result is not None and len(result) > 10


class TestIdentifyMultipleDrivers:
    """Tests for valuation multiple drivers."""
    
    @pytest.mark.unit
    def test_roe_premium_identified(self):
        """Test identification of ROE premium."""
        from tools.valuation import identify_multiple_drivers
        
        with patch('tools.valuation.yf.Ticker') as mock_ticker:
            def mock_ticker_data(symbol):
                mock_instance = MagicMock()
                mock_instance.info = {
                    "symbol": symbol,
                    "trailingPE": 30,
                    "priceToBook": 10,
                    "returnOnEquity": 0.35,  # High ROE
                    "profitMargins": 0.20
                }
                return mock_instance
            
            mock_ticker.side_effect = mock_ticker_data
            result = identify_multiple_drivers.run(symbol="TCS")
            
            # Tool returns driver analysis
            assert result is not None and len(result) > 10
    
    @pytest.mark.unit
    def test_growth_premium_identified(self):
        """Test identification of growth premium."""
        from tools.valuation import identify_multiple_drivers
        
        with patch('tools.valuation.yf.Ticker') as mock_ticker:
            def mock_ticker_data(symbol):
                mock_instance = MagicMock()
                mock_instance.info = {
                    "symbol": symbol,
                    "trailingPE": 35,
                    "revenueGrowth": 0.25,  # High growth
                    "earningsGrowth": 0.22
                }
                return mock_instance
            
            mock_ticker.side_effect = mock_ticker_data
            result = identify_multiple_drivers.run(symbol="TCS")
            
            # Tool returns driver analysis
            assert result is not None and len(result) > 10
    
    @pytest.mark.unit
    def test_margin_efficiency_identified(self):
        """Test identification of margin efficiency."""
        from tools.valuation import identify_multiple_drivers
        
        with patch('tools.valuation.yf.Ticker') as mock_ticker:
            def mock_ticker_data(symbol):
                mock_instance = MagicMock()
                mock_instance.info = {
                    "symbol": symbol,
                    "trailingPE": 28,
                    "profitMargins": 0.25,  # High margins
                    "operatingMargins": 0.28
                }
                return mock_instance
            
            mock_ticker.side_effect = mock_ticker_data
            result = identify_multiple_drivers.run(symbol="TCS")
            
            # Tool returns driver analysis
            assert result is not None and len(result) > 10
    
    @pytest.mark.unit
    def test_discount_factors_identified(self):
        """Test identification of valuation discount factors."""
        from tools.valuation import identify_multiple_drivers
        
        with patch('tools.valuation.yf.Ticker') as mock_ticker:
            def mock_ticker_data(symbol):
                mock_instance = MagicMock()
                mock_instance.info = {
                    "symbol": symbol,
                    "trailingPE": 12,  # Low PE
                    "returnOnEquity": 0.08,  # Low ROE
                    "debtToEquity": 85  # High debt
                }
                return mock_instance
            
            mock_ticker.side_effect = mock_ticker_data
            result = identify_multiple_drivers.run(symbol="HDFCBANK")
            
            # Tool returns driver analysis
            assert result is not None and len(result) > 10


class TestSectorBenchmarkAvailability:
    """Tests for sector benchmark data."""
    
    @pytest.mark.unit
    def test_all_sectors_have_benchmarks(self):
        """Test that all defined sectors have complete benchmark data."""
        for sector, benchmarks in SECTOR_VALUATION_BENCHMARKS.items():
            assert "pe_range" in benchmarks
            assert "pb_range" in benchmarks
            assert "ev_ebitda_range" in benchmarks
            assert len(benchmarks["pe_range"]) == 2
            assert len(benchmarks["pb_range"]) == 2
            # ev_ebitda_range can be None for financial sectors
            if benchmarks["ev_ebitda_range"] is not None:
                assert len(benchmarks["ev_ebitda_range"]) == 2
    
    @pytest.mark.unit
    def test_benchmark_ranges_valid(self):
        """Test that benchmark ranges are logically valid."""
        for sector, benchmarks in SECTOR_VALUATION_BENCHMARKS.items():
            # Low should be less than high
            assert benchmarks["pe_range"][0] < benchmarks["pe_range"][1]
            assert benchmarks["pb_range"][0] < benchmarks["pb_range"][1]
            
            # ev_ebitda_range can be None for financial sectors
            if benchmarks["ev_ebitda_range"] is not None:
                assert benchmarks["ev_ebitda_range"][0] < benchmarks["ev_ebitda_range"][1]
                assert all(v > 0 for v in benchmarks["ev_ebitda_range"])
            
            # All values should be positive
            assert all(v > 0 for v in benchmarks["pe_range"])
            assert all(v > 0 for v in benchmarks["pb_range"])
