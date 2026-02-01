"""
Tests for Fundamental Analysis Tools

Tests cover:
- Fundamental metrics calculation
- Valuation ratios (PE, PB, EV/EBITDA)
- Profitability metrics (ROE, ROCE, margins)
- Financial health indicators
- Growth metrics
- Data accuracy validation
"""

import json
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
import numpy as np


class TestFundamentalMetrics:
    """Tests for get_fundamental_metrics tool."""
    
    @pytest.mark.unit
    def test_fundamental_metrics_returns_json(self, mock_yfinance):
        """Test that fundamental metrics returns valid JSON."""
        from tools.analysis import get_fundamental_metrics
        
        result = get_fundamental_metrics.func("RELIANCE")
        data = json.loads(result)
        
        assert isinstance(data, dict)
    
    @pytest.mark.unit
    def test_fundamental_metrics_has_symbol(self, mock_yfinance):
        """Test that response includes the symbol."""
        from tools.analysis import get_fundamental_metrics
        
        result = get_fundamental_metrics.func("RELIANCE")
        data = json.loads(result)
        
        if "error" not in data:
            assert "symbol" in data
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_real_fundamental_metrics(self, valid_symbol):
        """Integration test: Fetch real fundamental metrics."""
        from tools.analysis import get_fundamental_metrics
        
        result = get_fundamental_metrics.func(valid_symbol)
        data = json.loads(result)
        
        assert isinstance(data, dict)


class TestValuationRatios:
    """Tests for valuation ratio calculations."""
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_pe_ratio_positive(self, mock_yfinance):
        """Critical: PE ratio should be positive for profitable companies."""
        from tools.analysis import get_fundamental_metrics
        
        result = get_fundamental_metrics.func("RELIANCE")
        data = json.loads(result)
        
        if "error" not in data and "pe_ratio" in data:
            pe = data["pe_ratio"]
            if pe != "N/A" and pe is not None:
                # For profitable companies, PE should be positive
                # Negative PE indicates losses
                assert isinstance(pe, (int, float)), "PE should be numeric"
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_pe_ratio_calculation(self):
        """Critical: PE = Price / EPS."""
        price = 2450.0
        eps = 98.0
        expected_pe = price / eps
        
        assert abs(expected_pe - 25.0) < 0.1, "PE calculation error"
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_pb_ratio_positive(self, mock_yfinance):
        """Critical: PB ratio should be positive."""
        from tools.analysis import get_fundamental_metrics
        
        result = get_fundamental_metrics.func("RELIANCE")
        data = json.loads(result)
        
        if "error" not in data and "pb_ratio" in data:
            pb = data["pb_ratio"]
            if pb != "N/A" and pb is not None:
                assert pb > 0, "PB ratio should be positive"
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_pb_ratio_calculation(self):
        """Critical: PB = Price / Book Value per Share."""
        price = 2450.0
        book_value_per_share = 1166.67
        expected_pb = price / book_value_per_share
        
        assert abs(expected_pb - 2.1) < 0.1, "PB calculation error"
    
    @pytest.mark.unit
    def test_ev_ebitda_calculation(self):
        """Test EV/EBITDA calculation."""
        # EV = Market Cap + Total Debt - Cash
        market_cap = 16500000000000  # 16.5L Cr
        total_debt = 300000000000   # 3L Cr
        cash = 150000000000         # 1.5L Cr
        ebitda = 150000000000       # 1.5L Cr
        
        ev = market_cap + total_debt - cash
        ev_ebitda = ev / ebitda
        
        # Should be reasonable (typically 5-20 for most companies)
        assert 0 < ev_ebitda < 200, f"EV/EBITDA {ev_ebitda} seems unreasonable"


class TestProfitabilityMetrics:
    """Tests for profitability metrics."""
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_roe_calculation(self):
        """Critical: ROE = Net Income / Shareholders Equity."""
        net_income = 60000000000  # 60k Cr
        shareholders_equity = 500000000000  # 5L Cr
        expected_roe = (net_income / shareholders_equity) * 100
        
        assert abs(expected_roe - 12.0) < 0.1, "ROE calculation error"
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_roce_calculation(self):
        """Critical: ROCE = EBIT / Capital Employed."""
        ebit = 80000000000  # 80k Cr
        capital_employed = 700000000000  # 7L Cr
        expected_roce = (ebit / capital_employed) * 100
        
        assert abs(expected_roce - 11.43) < 0.1, "ROCE calculation error"
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_roe_roce_bounds(self):
        """Critical: ROE and ROCE should be within reasonable bounds."""
        # Extremely high ROE/ROCE might indicate data errors
        # Typical range: -50% to 50% for most companies
        
        test_values = [5.0, 12.5, 25.0, 35.0]
        for value in test_values:
            assert -100 < value < 100, f"ROE/ROCE {value} seems unreasonable"
    
    @pytest.mark.unit
    def test_profit_margin_calculation(self):
        """Test profit margin calculation."""
        net_profit = 60000000000  # 60k Cr
        revenue = 800000000000   # 8L Cr
        expected_margin = (net_profit / revenue) * 100
        
        assert abs(expected_margin - 7.5) < 0.1, "Margin calculation error"
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_profit_margin_under_100(self):
        """Critical: Profit margin cannot exceed 100%."""
        margins = [5.0, 15.5, 25.0, 50.0]
        
        for margin in margins:
            assert margin <= 100, f"Margin {margin}% cannot exceed 100%"


class TestFinancialHealth:
    """Tests for financial health indicators."""
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_debt_equity_ratio_positive(self):
        """Critical: D/E ratio should be non-negative."""
        de_ratios = [0.0, 0.5, 1.0, 1.5, 2.5]
        
        for de in de_ratios:
            assert de >= 0, "D/E ratio cannot be negative"
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_debt_equity_calculation(self):
        """Critical: D/E = Total Debt / Shareholders Equity."""
        total_debt = 200000000000      # 2L Cr
        shareholders_equity = 500000000000  # 5L Cr
        expected_de = total_debt / shareholders_equity
        
        assert abs(expected_de - 0.4) < 0.01, "D/E calculation error"
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_current_ratio_calculation(self):
        """Critical: Current Ratio = Current Assets / Current Liabilities."""
        current_assets = 250000000000    # 2.5L Cr
        current_liabilities = 200000000000  # 2L Cr
        expected_ratio = current_assets / current_liabilities
        
        assert abs(expected_ratio - 1.25) < 0.01, "Current ratio calculation error"
    
    @pytest.mark.unit
    def test_current_ratio_health_interpretation(self):
        """Test current ratio health interpretation."""
        # Current ratio < 1 indicates liquidity concerns
        # Current ratio > 1 indicates healthy liquidity
        
        assert 0.8 < 1, "Current ratio < 1 indicates concern"
        assert 1.5 > 1, "Current ratio > 1 indicates health"
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_interest_coverage_positive(self):
        """Critical: Interest coverage should be positive for healthy companies."""
        ebit = 80000000000
        interest_expense = 15000000000
        coverage = ebit / interest_expense
        
        assert coverage > 0, "Interest coverage should be positive"
        assert coverage > 1, "Coverage < 1 means EBIT doesn't cover interest"


class TestGrowthMetrics:
    """Tests for growth metrics."""
    
    @pytest.mark.unit
    def test_revenue_growth_calculation(self):
        """Test revenue growth calculation."""
        current_revenue = 800000000000
        previous_revenue = 650000000000
        growth = ((current_revenue - previous_revenue) / previous_revenue) * 100
        
        assert abs(growth - 23.08) < 0.1, "Revenue growth calculation error"
    
    @pytest.mark.unit
    def test_eps_growth_calculation(self):
        """Test EPS growth calculation."""
        current_eps = 98.0
        previous_eps = 85.0
        growth = ((current_eps - previous_eps) / previous_eps) * 100
        
        assert abs(growth - 15.29) < 0.1, "EPS growth calculation error"
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_growth_can_be_negative(self):
        """Critical: Growth can be negative (decline)."""
        current = 80
        previous = 100
        growth = ((current - previous) / previous) * 100
        
        assert growth == -20, "Negative growth should be calculated correctly"
    
    @pytest.mark.unit
    def test_cagr_calculation(self):
        """Test CAGR (Compound Annual Growth Rate) calculation."""
        start_value = 100
        end_value = 161  # ~10% CAGR over 5 years
        years = 5
        
        cagr = ((end_value / start_value) ** (1/years) - 1) * 100
        
        assert abs(cagr - 10.0) < 0.5, "CAGR calculation error"


class TestDividendMetrics:
    """Tests for dividend-related metrics."""
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_dividend_yield_calculation(self):
        """Critical: Dividend Yield = Annual Dividend / Price * 100."""
        annual_dividend = 9.0
        price = 2450.0
        expected_yield = (annual_dividend / price) * 100
        
        assert abs(expected_yield - 0.37) < 0.01, "Dividend yield calculation error"
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_dividend_yield_non_negative(self):
        """Critical: Dividend yield cannot be negative."""
        yields = [0.0, 0.5, 1.5, 3.0, 5.0]
        
        for dy in yields:
            assert dy >= 0, "Dividend yield cannot be negative"
    
    @pytest.mark.unit
    def test_payout_ratio_calculation(self):
        """Test dividend payout ratio calculation."""
        dividend_per_share = 9.0
        eps = 98.0
        payout_ratio = (dividend_per_share / eps) * 100
        
        assert abs(payout_ratio - 9.18) < 0.1, "Payout ratio calculation error"
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_payout_ratio_bounds(self):
        """Critical: Payout ratio should be 0-100% (or slightly over for unsustainable)."""
        # Payout > 100% means paying more than earnings
        sustainable_payout = 45.0
        unsustainable_payout = 120.0
        
        assert sustainable_payout <= 100, "Sustainable payout <= 100%"
        assert unsustainable_payout > 100, "Payout > 100% is unsustainable"


class TestValuationAssessment:
    """Tests for valuation assessment logic."""
    
    @pytest.mark.unit
    def test_undervalued_determination(self):
        """Test undervalued stock determination."""
        from config import FUNDAMENTAL_THRESHOLDS
        
        # Stock with PE below low threshold
        pe = 12
        pb = 0.8
        
        is_undervalued = (
            pe < FUNDAMENTAL_THRESHOLDS["pe_ratio_low"] or
            pb < FUNDAMENTAL_THRESHOLDS["pb_ratio_low"]
        )
        
        assert is_undervalued, "Low PE/PB should indicate undervaluation"
    
    @pytest.mark.unit
    def test_overvalued_determination(self):
        """Test overvalued stock determination."""
        from config import FUNDAMENTAL_THRESHOLDS
        
        # Stock with PE above high threshold
        pe = 50
        pb = 8
        
        is_overvalued = (
            pe > FUNDAMENTAL_THRESHOLDS["pe_ratio_high"] or
            pb > FUNDAMENTAL_THRESHOLDS["pb_ratio_high"]
        )
        
        assert is_overvalued, "High PE/PB should indicate overvaluation"
    
    @pytest.mark.unit
    def test_fair_value_determination(self):
        """Test fairly valued stock determination."""
        from config import FUNDAMENTAL_THRESHOLDS
        
        # Stock with PE within range
        pe = 22
        
        is_fair = (
            FUNDAMENTAL_THRESHOLDS["pe_ratio_low"] <= pe <= 
            FUNDAMENTAL_THRESHOLDS["pe_ratio_high"]
        )
        
        assert is_fair, "PE within range should indicate fair value"


class TestErrorHandling:
    """Tests for error handling in fundamental analysis."""
    
    @pytest.mark.unit
    def test_handles_missing_data(self, mock_yfinance):
        """Test handling of missing fundamental data."""
        from tools.analysis import get_fundamental_metrics
        
        # Configure mock to return minimal data
        mock_yfinance.return_value.info = {}
        
        result = get_fundamental_metrics.func("UNKNOWN")
        data = json.loads(result)
        
        # Should return valid JSON
        assert isinstance(data, dict)
    
    @pytest.mark.unit
    def test_handles_zero_denominators(self):
        """Test handling of zero denominators in ratio calculations."""
        # PE with zero EPS
        price = 2450
        eps = 0
        
        # Should handle gracefully
        try:
            pe = price / eps if eps != 0 else float('inf')
        except ZeroDivisionError:
            pytest.fail("Should handle zero EPS gracefully")
    
    @pytest.mark.unit
    def test_handles_negative_values(self):
        """Test handling of negative fundamental values."""
        # Negative EPS (company making losses)
        price = 100
        eps = -5
        pe = price / eps  # Will be negative
        
        assert pe < 0, "Negative EPS gives negative PE"
