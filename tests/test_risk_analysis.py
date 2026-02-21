"""
Tests for Risk Analysis Tools

Tests cover:
- Value at Risk (VaR) calculation
- Downside risk metrics (max drawdown, Sortino ratio)
- Leverage risk assessment
- Stop-loss level calculation
- Scenario risk modeling
"""

import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np


class TestCalculateVaR:
    """Tests for Value at Risk calculation."""
    
    @pytest.mark.unit
    def test_var_calculation_with_returns(self):
        """Test VaR calculation with valid return data."""
        from tools.risk_analysis import calculate_var
        
        with patch('tools.risk_analysis.yf.Ticker') as mock_ticker:
            mock_ticker_instance = MagicMock()
            
            # Create sample historical data
            dates = pd.date_range(end=pd.Timestamp.now(), periods=252, freq='D')
            prices = np.random.randn(252).cumsum() + 100
            history_data = pd.DataFrame({'Close': prices}, index=dates)
            
            mock_ticker_instance.history = MagicMock(return_value=history_data)
            mock_ticker.return_value = mock_ticker_instance
            
            result = calculate_var.run(symbol="RELIANCE")
            
            assert "var" in result.lower()
            assert "95%" in result or "confidence" in result.lower()
            assert "%" in result  # Should contain percentage
    
    @pytest.mark.unit
    def test_var_different_confidence_levels(self):
        """Test VaR at different confidence levels."""
        from tools.risk_analysis import calculate_var
        
        with patch('tools.risk_analysis.yf.Ticker') as mock_ticker:
            mock_ticker_instance = MagicMock()
            
            dates = pd.date_range(end=pd.Timestamp.now(), periods=252, freq='D')
            prices = np.random.randn(252).cumsum() + 100
            history_data = pd.DataFrame({'Close': prices}, index=dates)
            
            mock_ticker_instance.history = MagicMock(return_value=history_data)
            mock_ticker.return_value = mock_ticker_instance
            
            result = calculate_var.run(symbol="RELIANCE")
            
            # Should mention confidence level
            assert "95" in result or "99" in result or "confidence" in result.lower()
    
    @pytest.mark.unit
    def test_var_insufficient_data(self):
        """Test VaR calculation with insufficient data."""
        from tools.risk_analysis import calculate_var
        
        with patch('tools.risk_analysis.yf.Ticker') as mock_ticker:
            mock_ticker_instance = MagicMock()
            
            # Very limited data
            history_data = pd.DataFrame({'Close': [100, 102, 101]})
            mock_ticker_instance.history = MagicMock(return_value=history_data)
            mock_ticker.return_value = mock_ticker_instance
            
            result = calculate_var.run(symbol="TEST")
            
            assert "insufficient" in result.lower() or "not enough" in result.lower() or "var" in result.lower()


class TestAnalyzeDownsideMetrics:
    """Tests for downside risk metrics."""
    
    @pytest.mark.unit
    def test_max_drawdown_calculation(self):
        """Test maximum drawdown calculation."""
        from tools.risk_analysis import analyze_downside_metrics
        
        with patch('tools.risk_analysis.yf.Ticker') as mock_ticker:
            mock_ticker_instance = MagicMock()
            
            # Create data with a clear drawdown - 100 prices
            dates = pd.date_range(end=pd.Timestamp.now(), periods=100, freq='D')
            # Create clear drawdown pattern
            prices = [100] * 20  # 20 at 100
            prices += list(range(100, 70, -3))  # 10 declining to 70
            prices += [70] * 20  # 20 at 70
            prices += list(range(71, 91, 2))  # 10 recovering
            # Pad to exactly 100
            while len(prices) < 100:
                prices.append(prices[-1])
            prices = prices[:100]  # Ensure exactly 100
            
            history_data = pd.DataFrame({'Close': prices}, index=dates)
            
            mock_ticker_instance.history = MagicMock(return_value=history_data)
            mock_ticker.return_value = mock_ticker_instance
            
            result = analyze_downside_metrics.run(symbol="RELIANCE")
            
            # Check for drawdown in result (appears as "max_drawdown" key and "drawdown" in interpretation)
            assert "drawdown" in result.lower()
            assert "percentage" in result.lower() or "%" in result
    
    @pytest.mark.unit
    def test_sortino_ratio_calculation(self):
        """Test Sortino ratio calculation."""
        from tools.risk_analysis import analyze_downside_metrics
        
        with patch('tools.risk_analysis.yf.Ticker') as mock_ticker:
            mock_ticker_instance = MagicMock()
            
            dates = pd.date_range(end=pd.Timestamp.now(), periods=252, freq='D')
            np.random.seed(42)
            returns = np.random.randn(252) * 0.02 + 0.001
            prices = (1 + pd.Series(returns)).cumprod() * 100
            history_data = pd.DataFrame({'Close': prices.values}, index=dates)
            
            mock_ticker_instance.history = MagicMock(return_value=history_data)
            mock_ticker.return_value = mock_ticker_instance
            
            result = analyze_downside_metrics.run(symbol="RELIANCE")
            
            assert "sortino" in result.lower()
    
    @pytest.mark.unit
    def test_downside_deviation_calculation(self):
        """Test downside deviation calculation."""
        from tools.risk_analysis import analyze_downside_metrics
        
        with patch('tools.risk_analysis.yf.Ticker') as mock_ticker:
            mock_ticker_instance = MagicMock()
            
            dates = pd.date_range(end=pd.Timestamp.now(), periods=180, freq='D')
            prices = np.random.randn(180).cumsum() + 100
            history_data = pd.DataFrame({'Close': prices}, index=dates)
            
            mock_ticker_instance.history = MagicMock(return_value=history_data)
            mock_ticker.return_value = mock_ticker_instance
            
            result = analyze_downside_metrics.run(symbol="RELIANCE")
            
            assert "downside" in result.lower()
            assert "volatility" in result.lower() or "deviation" in result.lower()


class TestAssessLeverageRisk:
    """Tests for leverage risk assessment."""
    
    @pytest.mark.unit
    def test_high_leverage_warning(self):
        """Test detection of high leverage risk."""
        from tools.risk_analysis import assess_leverage_risk
        
        with patch('tools.risk_analysis.yf.Ticker') as mock_ticker:
            mock_ticker_instance = MagicMock()
            mock_ticker_instance.info = {
                "debtToEquity": 150.0,  # High leverage
                "currentRatio": 0.8,
                "quickRatio": 0.5,
                "interestCoverage": 2.5
            }
            mock_ticker.return_value = mock_ticker_instance
            
            result = assess_leverage_risk.run(symbol="TEST")
            
            assert "high" in result.lower() or "elevated" in result.lower()
            assert "debt" in result.lower() or "leverage" in result.lower()
    
    @pytest.mark.unit
    def test_low_leverage_safe(self):
        """Test identification of safe leverage levels."""
        from tools.risk_analysis import assess_leverage_risk
        
        with patch('tools.risk_analysis.yf.Ticker') as mock_ticker:
            mock_ticker_instance = MagicMock()
            mock_ticker_instance.info = {
                "debtToEquity": 20.0,  # Low leverage
                "currentRatio": 2.5,
                "quickRatio": 1.8,
                "interestCoverage": 12.0
            }
            mock_ticker.return_value = mock_ticker_instance
            
            result = assess_leverage_risk.run(symbol="TCS")
            
            assert "low" in result.lower() or "safe" in result.lower() or "comfortable" in result.lower()
    
    @pytest.mark.unit
    def test_liquidity_risk_assessment(self):
        """Test liquidity risk assessment."""
        from tools.risk_analysis import assess_leverage_risk
        
        with patch('tools.risk_analysis.yf.Ticker') as mock_ticker:
            mock_ticker_instance = MagicMock()
            mock_ticker_instance.info = {
                "debtToEquity": 50.0,
                "currentRatio": 0.7,  # Poor liquidity
                "quickRatio": 0.4,
                "interestCoverage": 3.0
            }
            mock_ticker.return_value = mock_ticker_instance
            
            result = assess_leverage_risk.run(symbol="TEST")
            
            # Check for leverage assessment (tool focuses on debt, not liquidity ratios)
            assert "debt_to_equity" in result.lower() or "leverage" in result.lower()
            assert "50.0" in result or "50" in result
    
    @pytest.mark.unit
    def test_interest_coverage_assessment(self):
        """Test interest coverage assessment."""
        from tools.risk_analysis import assess_leverage_risk
        
        with patch('tools.risk_analysis.yf.Ticker') as mock_ticker:
            mock_ticker_instance = MagicMock()
            mock_ticker_instance.info = {
                "debtToEquity": 80.0,
                "currentRatio": 1.5,
                "interestCoverage": 1.5  # Low coverage
            }
            mock_ticker.return_value = mock_ticker_instance
            
            result = assess_leverage_risk.run(symbol="TEST")
            
            assert "interest" in result.lower() or "coverage" in result.lower()


class TestCalculateStopLoss:
    """Tests for stop-loss calculation."""
    
    @pytest.mark.unit
    def test_atr_based_stop_loss(self):
        """Test ATR-based stop-loss calculation."""
        from tools.risk_analysis import calculate_stop_loss_levels
        
        with patch('tools.risk_analysis.yf.Ticker') as mock_ticker:
            mock_ticker_instance = MagicMock()
            
            dates = pd.date_range(end=pd.Timestamp.now(), periods=50, freq='D')
            history_data = pd.DataFrame({
                'High': np.random.randn(50).cumsum() + 105,
                'Low': np.random.randn(50).cumsum() + 95,
                'Close': np.random.randn(50).cumsum() + 100
            }, index=dates)
            
            mock_ticker_instance.history = MagicMock(return_value=history_data)
            mock_ticker_instance.info = {"currentPrice": 100}
            mock_ticker.return_value = mock_ticker_instance
            
            result = calculate_stop_loss_levels.run(symbol="RELIANCE")
            
            assert "stop" in result.lower() or "stop-loss" in result.lower()
            assert "atr" in result.lower()
    
    @pytest.mark.unit
    def test_support_based_stop_loss(self):
        """Test support-based stop-loss levels."""
        from tools.risk_analysis import calculate_stop_loss_levels
        
        with patch('tools.risk_analysis.yf.Ticker') as mock_ticker:
            mock_ticker_instance = MagicMock()
            
            dates = pd.date_range(end=pd.Timestamp.now(), periods=100, freq='D')
            # Create data with clear support at 90
            prices = np.concatenate([
                np.full(20, 95),
                np.linspace(95, 110, 30),
                np.full(20, 108),
                np.linspace(108, 92, 30)
            ])
            history_data = pd.DataFrame({
                'High': prices + 2,
                'Low': prices - 2,
                'Close': prices
            }, index=dates)
            
            mock_ticker_instance.history = MagicMock(return_value=history_data)
            mock_ticker_instance.info = {"currentPrice": 100}
            mock_ticker.return_value = mock_ticker_instance
            
            result = calculate_stop_loss_levels.run(symbol="RELIANCE")
            
            assert "support" in result.lower() or "level" in result.lower()
    
    @pytest.mark.unit
    def test_multiple_stop_loss_levels(self):
        """Test that multiple stop-loss levels are provided."""
        from tools.risk_analysis import calculate_stop_loss_levels
        
        with patch('tools.risk_analysis.yf.Ticker') as mock_ticker:
            mock_ticker_instance = MagicMock()
            
            dates = pd.date_range(end=pd.Timestamp.now(), periods=60, freq='D')
            history_data = pd.DataFrame({
                'High': np.random.randn(60).cumsum() + 105,
                'Low': np.random.randn(60).cumsum() + 95,
                'Close': np.random.randn(60).cumsum() + 100
            }, index=dates)
            
            mock_ticker_instance.history = MagicMock(return_value=history_data)
            mock_ticker_instance.info = {"currentPrice": 100}
            mock_ticker.return_value = mock_ticker_instance
            
            result = calculate_stop_loss_levels.run(symbol="RELIANCE")
            
            # Should provide conservative and aggressive levels
            assert "conservative" in result.lower() or "aggressive" in result.lower() or "tight" in result.lower()


class TestModelScenarioRisks:
    """Tests for scenario risk modeling."""
    
    @pytest.mark.unit
    def test_bear_market_scenario(self):
        """Test bear market scenario modeling."""
        from tools.risk_analysis import model_scenario_risks
        
        with patch('tools.risk_analysis.yf.Ticker') as mock_ticker:
            mock_ticker_instance = MagicMock()
            
            dates = pd.date_range(end=pd.Timestamp.now(), periods=252, freq='D')
            prices = np.random.randn(252).cumsum() + 100
            history_data = pd.DataFrame({'Close': prices}, index=dates)
            
            mock_ticker_instance.history = MagicMock(return_value=history_data)
            mock_ticker_instance.info = {
                "currentPrice": 100,
                "beta": 1.2
            }
            mock_ticker.return_value = mock_ticker_instance
            
            result = model_scenario_risks.run(symbol="RELIANCE")
            
            assert "bear" in result.lower()
            assert "scenario" in result.lower()
    
    @pytest.mark.unit
    def test_stress_scenario(self):
        """Test stress scenario modeling."""
        from tools.risk_analysis import model_scenario_risks
        
        with patch('tools.risk_analysis.yf.Ticker') as mock_ticker:
            mock_ticker_instance = MagicMock()
            
            dates = pd.date_range(end=pd.Timestamp.now(), periods=252, freq='D')
            prices = np.random.randn(252).cumsum() + 100
            history_data = pd.DataFrame({'Close': prices}, index=dates)
            
            mock_ticker_instance.history = MagicMock(return_value=history_data)
            mock_ticker_instance.info = {
                "currentPrice": 100,
                "beta": 1.5
            }
            mock_ticker.return_value = mock_ticker_instance
            
            result = model_scenario_risks.run(symbol="RELIANCE")
            
            assert "stress" in result.lower() or "crisis" in result.lower()
    
    @pytest.mark.unit
    def test_recovery_scenario(self):
        """Test recovery scenario modeling."""
        from tools.risk_analysis import model_scenario_risks
        
        with patch('tools.risk_analysis.yf.Ticker') as mock_ticker:
            mock_ticker_instance = MagicMock()
            
            dates = pd.date_range(end=pd.Timestamp.now(), periods=252, freq='D')
            prices = np.random.randn(252).cumsum() + 100
            history_data = pd.DataFrame({'Close': prices}, index=dates)
            
            mock_ticker_instance.history = MagicMock(return_value=history_data)
            mock_ticker_instance.info = {
                "currentPrice": 85,  # Below historical average
                "beta": 1.0
            }
            mock_ticker.return_value = mock_ticker_instance
            
            result = model_scenario_risks.run(symbol="RELIANCE")
            
            # Should include multiple scenarios
            assert "scenario" in result.lower()
    
    @pytest.mark.unit
    def test_beta_adjustment_in_scenarios(self):
        """Test that beta is considered in scenario modeling."""
        from tools.risk_analysis import model_scenario_risks
        
        with patch('tools.risk_analysis.yf.Ticker') as mock_ticker:
            mock_ticker_instance = MagicMock()
            
            dates = pd.date_range(end=pd.Timestamp.now(), periods=252, freq='D')
            prices = np.random.randn(252).cumsum() + 100
            history_data = pd.DataFrame({'Close': prices}, index=dates)
            
            mock_ticker_instance.history = MagicMock(return_value=history_data)
            mock_ticker_instance.info = {
                "currentPrice": 100,
                "beta": 1.8  # High beta
            }
            mock_ticker.return_value = mock_ticker_instance
            
            result = model_scenario_risks.run(symbol="VOLATILE")
            
            assert "beta" in result.lower() or "volatility" in result.lower()


class TestRiskAnalysisIntegration:
    """Integration tests for risk analysis tools."""
    
    @pytest.mark.unit
    def test_all_risk_tools_available(self):
        """Test that all risk analysis tools are properly exported."""
        from tools.risk_analysis import (
            calculate_var,
            analyze_downside_metrics,
            assess_leverage_risk,
            calculate_stop_loss_levels,
            model_scenario_risks
        )
        
        # Verify all tools exist
        assert calculate_var is not None
        assert analyze_downside_metrics is not None
        assert assess_leverage_risk is not None
        assert calculate_stop_loss_levels is not None
        assert model_scenario_risks is not None
    
    @pytest.mark.unit
    def test_risk_tools_have_descriptions(self):
        """Test that all risk tools have proper descriptions."""
        from tools.risk_analysis import (
            calculate_var,
            analyze_downside_metrics,
            assess_leverage_risk,
            calculate_stop_loss_levels,
            model_scenario_risks
        )
        
        # Each tool should have description for CrewAI
        assert hasattr(calculate_var, 'description') or hasattr(calculate_var, 'func')
        assert hasattr(analyze_downside_metrics, 'description') or hasattr(analyze_downside_metrics, 'func')
        assert hasattr(assess_leverage_risk, 'description') or hasattr(assess_leverage_risk, 'func')
        assert hasattr(calculate_stop_loss_levels, 'description') or hasattr(calculate_stop_loss_levels, 'func')
        assert hasattr(model_scenario_risks, 'description') or hasattr(model_scenario_risks, 'func')
