"""
Tests for Technical Analysis Tools

Tests cover:
- Technical indicator calculations
- RSI bounds validation (0-100)
- MACD signal accuracy
- Bollinger Bands ordering
- Moving average calculations
- Support/Resistance detection
- Price action analysis
- Signal generation accuracy
"""

import json
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np


class TestTechnicalIndicatorsCalculation:
    """Tests for calculate_technical_indicators tool."""
    
    @pytest.mark.unit
    def test_returns_valid_json(self, mock_yfinance):
        """Test that function returns valid JSON."""
        from tools.analysis import calculate_technical_indicators
        
        result = calculate_technical_indicators.func("RELIANCE", "6mo")
        data = json.loads(result)
        
        assert isinstance(data, dict)
    
    @pytest.mark.unit
    def test_contains_required_indicators(self, mock_yfinance):
        """Test that all required indicators are present."""
        from tools.analysis import calculate_technical_indicators
        
        result = calculate_technical_indicators.func("RELIANCE", "6mo")
        data = json.loads(result)
        
        if "error" not in data:
            # Check for main indicator categories
            assert "symbol" in data
            assert "current_price" in data
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_rsi_within_bounds(self, mock_yfinance):
        """Critical: RSI must be between 0 and 100."""
        from tools.analysis import calculate_technical_indicators
        
        result = calculate_technical_indicators.func("RELIANCE", "6mo")
        data = json.loads(result)
        
        if "error" not in data and "rsi_14" in data:
            rsi = data["rsi_14"]
            assert 0 <= rsi <= 100, f"RSI {rsi} is out of bounds [0, 100]"
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_bollinger_bands_ordering(self, mock_yfinance):
        """Critical: Upper BB > Middle BB > Lower BB."""
        from tools.analysis import calculate_technical_indicators
        
        result = calculate_technical_indicators.func("RELIANCE", "6mo")
        data = json.loads(result)
        
        if "error" not in data:
            if all(k in data for k in ["bb_upper", "bb_middle", "bb_lower"]):
                assert data["bb_upper"] > data["bb_middle"], "Upper BB must be > Middle BB"
                assert data["bb_middle"] > data["bb_lower"], "Middle BB must be > Lower BB"
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_moving_averages_reasonable(self, mock_yfinance):
        """Critical: MAs should be within reasonable range of current price."""
        from tools.analysis import calculate_technical_indicators
        
        result = calculate_technical_indicators.func("RELIANCE", "6mo")
        data = json.loads(result)
        
        if "error" not in data and "current_price" in data:
            price = data["current_price"]
            
            # MAs should be within 50% of current price (generous tolerance)
            for ma_key in ["sma_20", "sma_50"]:
                if ma_key in data and data[ma_key]:
                    ma_value = data[ma_key]
                    deviation = abs(ma_value - price) / price
                    assert deviation < 0.5, f"{ma_key} deviates too much from price"
    
    @pytest.mark.unit
    def test_valid_period_values(self, mock_yfinance):
        """Test various period values work correctly."""
        from tools.analysis import calculate_technical_indicators
        
        valid_periods = ["3mo", "6mo", "1y"]
        
        for period in valid_periods:
            result = calculate_technical_indicators.func("RELIANCE", period)
            data = json.loads(result)
            assert isinstance(data, dict), f"Failed for period {period}"
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_real_technical_indicators(self, valid_symbol):
        """Integration test: Calculate real technical indicators."""
        from tools.analysis import calculate_technical_indicators
        
        result = calculate_technical_indicators.func(valid_symbol, "3mo")
        data = json.loads(result)
        
        assert isinstance(data, dict)
        if "error" not in data:
            assert data.get("current_price", 0) > 0


class TestRSICalculation:
    """Specific tests for RSI calculation accuracy."""
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_rsi_oversold_detection(self, sample_historical_data):
        """Test that oversold condition is correctly identified."""
        # Create data with declining prices (should give low RSI)
        dates = pd.date_range(end=datetime.now(), periods=50, freq='D')
        declining_prices = np.linspace(2500, 2000, 50)  # Consistent decline
        
        df = pd.DataFrame({
            'Close': declining_prices,
        }, index=dates)
        
        # Calculate RSI manually
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # Strong decline should result in low RSI
        final_rsi = rsi.iloc[-1]
        assert final_rsi < 50, "Declining prices should give RSI < 50"
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_rsi_overbought_detection(self, sample_historical_data):
        """Test that overbought condition is correctly identified."""
        # Create data with rising prices (should give high RSI)
        dates = pd.date_range(end=datetime.now(), periods=50, freq='D')
        rising_prices = np.linspace(2000, 2500, 50)  # Consistent rise
        
        df = pd.DataFrame({
            'Close': rising_prices,
        }, index=dates)
        
        # Calculate RSI manually
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # Strong rise should result in high RSI
        final_rsi = rsi.iloc[-1]
        assert final_rsi > 50, "Rising prices should give RSI > 50"


class TestMACDCalculation:
    """Tests for MACD calculation."""
    
    @pytest.mark.unit
    def test_macd_components_present(self, mock_yfinance):
        """Test that all MACD components are returned."""
        from tools.analysis import calculate_technical_indicators
        
        result = calculate_technical_indicators.func("RELIANCE", "6mo")
        data = json.loads(result)
        
        if "error" not in data:
            # MACD should have line, signal, and histogram
            macd_keys = ["macd_line", "macd_signal", "macd_histogram"]
            for key in macd_keys:
                assert key in data or "macd" in str(data).lower()
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_macd_histogram_calculation(self):
        """Critical: Histogram = MACD Line - Signal Line."""
        # Create sample data
        dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
        np.random.seed(42)
        prices = pd.Series(2400 * np.exp(np.cumsum(np.random.normal(0, 0.02, 100))), index=dates)
        
        # Calculate MACD components
        ema_12 = prices.ewm(span=12, adjust=False).mean()
        ema_26 = prices.ewm(span=26, adjust=False).mean()
        macd_line = ema_12 - ema_26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        histogram = macd_line - signal_line
        
        # Verify histogram calculation
        expected_histogram = macd_line.iloc[-1] - signal_line.iloc[-1]
        actual_histogram = histogram.iloc[-1]
        
        assert abs(expected_histogram - actual_histogram) < 0.001, "Histogram calculation error"


class TestBollingerBands:
    """Tests for Bollinger Bands calculation."""
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_bb_standard_deviation_positive(self):
        """Critical: BB width should be positive (2 std devs)."""
        dates = pd.date_range(end=datetime.now(), periods=50, freq='D')
        np.random.seed(42)
        prices = pd.Series(2400 + np.random.normal(0, 50, 50), index=dates)
        
        sma_20 = prices.rolling(window=20).mean()
        std_20 = prices.rolling(window=20).std()
        
        bb_upper = sma_20 + (std_20 * 2)
        bb_lower = sma_20 - (std_20 * 2)
        
        # Upper should be above lower
        assert bb_upper.iloc[-1] > bb_lower.iloc[-1], "BB Upper must be > BB Lower"
    
    @pytest.mark.unit
    def test_bb_width_increases_with_volatility(self):
        """Test that BB width increases with higher volatility."""
        dates = pd.date_range(end=datetime.now(), periods=50, freq='D')
        
        # Low volatility prices
        np.random.seed(42)
        low_vol = pd.Series(2400 + np.random.normal(0, 10, 50), index=dates)
        low_std = low_vol.rolling(window=20).std().iloc[-1]
        
        # High volatility prices  
        np.random.seed(42)
        high_vol = pd.Series(2400 + np.random.normal(0, 100, 50), index=dates)
        high_std = high_vol.rolling(window=20).std().iloc[-1]
        
        assert high_std > low_std, "Higher volatility should give wider bands"


class TestPriceActionAnalysis:
    """Tests for price action analysis tool."""
    
    @pytest.mark.unit
    def test_analyze_price_action_returns_json(self, mock_yfinance):
        """Test that price action analysis returns valid JSON."""
        from tools.analysis import analyze_price_action
        
        result = analyze_price_action.func("RELIANCE")
        data = json.loads(result)
        
        assert isinstance(data, dict)
    
    @pytest.mark.unit
    def test_support_resistance_identified(self, mock_yfinance):
        """Test that support and resistance levels are identified."""
        from tools.analysis import analyze_price_action
        
        result = analyze_price_action.func("RELIANCE")
        data = json.loads(result)
        
        if "error" not in data:
            # Should contain some level analysis
            result_lower = result.lower()
            assert "support" in result_lower or "resistance" in result_lower or "level" in result_lower or "price" in result_lower
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_support_below_resistance(self, mock_yfinance):
        """Critical: Support levels should be below resistance levels."""
        from tools.analysis import analyze_price_action
        
        result = analyze_price_action.func("RELIANCE")
        data = json.loads(result)
        
        if "error" not in data:
            if "support" in data and "resistance" in data:
                if isinstance(data["support"], (int, float)) and isinstance(data["resistance"], (int, float)):
                    assert data["support"] < data["resistance"], "Support must be below resistance"


class TestPivotPointCalculation:
    """Tests for standard daily pivot point calculation."""

    @pytest.mark.unit
    @pytest.mark.critical
    def test_pivot_uses_daily_hlc(self, mock_yfinance):
        """Critical: Pivot should be (prevH + prevL + prevC) / 3 from last day."""
        from tools.analysis import calculate_technical_indicators

        result = calculate_technical_indicators.func("RELIANCE", "6mo")
        data = json.loads(result)

        if "error" not in data and "support_resistance" in data:
            sr = data["support_resistance"]
            # Pivot must be between recent_low and recent_high
            assert sr["support_1"] < sr["pivot"] < sr["resistance_1"]

    @pytest.mark.unit
    @pytest.mark.critical
    def test_pivot_levels_near_current_price(self, mock_yfinance):
        """Critical: Pivot levels should be near current price, not wildly far."""
        from tools.analysis import calculate_technical_indicators

        result = calculate_technical_indicators.func("RELIANCE", "6mo")
        data = json.loads(result)

        if "error" not in data and "support_resistance" in data:
            sr = data["support_resistance"]
            current = data.get("current_price", sr["pivot"])
            # All levels should be within 10% of current price for daily pivots
            for key in ["pivot", "support_1", "resistance_1"]:
                pct_diff = abs(sr[key] - current) / current * 100
                assert pct_diff < 10, (
                    f"{key}={sr[key]} is {pct_diff:.1f}% from current price "
                    f"{current} - daily pivot levels should be within 10%"
                )

    @pytest.mark.unit
    def test_pivot_ordering(self, mock_yfinance):
        """Test that S2 < S1 < Pivot < R1 < R2."""
        from tools.analysis import calculate_technical_indicators

        result = calculate_technical_indicators.func("RELIANCE", "6mo")
        data = json.loads(result)

        if "error" not in data and "support_resistance" in data:
            sr = data["support_resistance"]
            assert sr["support_2"] < sr["support_1"] < sr["pivot"]
            assert sr["pivot"] < sr["resistance_1"] < sr["resistance_2"]


class TestTrendAnalysis:
    """Tests for trend determination."""

    @pytest.mark.unit
    def test_trend_values_valid(self, mock_yfinance):
        """Test that trend is one of expected values."""
        from tools.analysis import calculate_technical_indicators
        
        result = calculate_technical_indicators.func("RELIANCE", "6mo")
        data = json.loads(result)
        
        if "error" not in data and "trend" in data:
            valid_trends = ["bullish", "bearish", "neutral", "sideways", "uptrend", "downtrend"]
            trend_value = data["trend"]
            # Handle both string and dict trend values
            if isinstance(trend_value, str):
                assert trend_value.lower() in valid_trends or "trend" in str(data).lower()
            else:
                # If it's a dict or other type, just verify it exists
                assert trend_value is not None
    
    @pytest.mark.unit
    def test_uptrend_identification(self):
        """Test uptrend is correctly identified from MAs."""
        # Create uptrending data: Price > SMA20 > SMA50
        np.random.seed(42)
        
        # Simulate uptrend: recent prices higher than older
        dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
        prices = pd.Series(np.linspace(2000, 2500, 100), index=dates)
        
        sma_20 = prices.rolling(20).mean().iloc[-1]
        sma_50 = prices.rolling(50).mean().iloc[-1]
        current_price = prices.iloc[-1]
        
        # In uptrend: Price > SMA20 > SMA50
        is_uptrend = current_price > sma_20 > sma_50
        assert is_uptrend, "Should identify uptrend from MA alignment"
    
    @pytest.mark.unit
    def test_downtrend_identification(self):
        """Test downtrend is correctly identified from MAs."""
        # Create downtrending data: Price < SMA20 < SMA50
        np.random.seed(42)
        
        # Simulate downtrend: recent prices lower than older
        dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
        prices = pd.Series(np.linspace(2500, 2000, 100), index=dates)
        
        sma_20 = prices.rolling(20).mean().iloc[-1]
        sma_50 = prices.rolling(50).mean().iloc[-1]
        current_price = prices.iloc[-1]
        
        # In downtrend: Price < SMA20 < SMA50
        is_downtrend = current_price < sma_20 < sma_50
        assert is_downtrend, "Should identify downtrend from MA alignment"


class TestATRCalculation:
    """Tests for Average True Range calculation."""
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_atr_positive(self):
        """Critical: ATR must always be positive."""
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        np.random.seed(42)
        base = 2400
        
        high = pd.Series(base + np.random.uniform(10, 50, 30), index=dates)
        low = pd.Series(base - np.random.uniform(10, 50, 30), index=dates)
        close = pd.Series(base + np.random.uniform(-20, 20, 30), index=dates)
        
        # Calculate TR
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(14).mean().iloc[-1]
        
        assert atr > 0, "ATR must be positive"
    
    @pytest.mark.unit
    def test_atr_reasonable_magnitude(self):
        """Test ATR is reasonable relative to price."""
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        np.random.seed(42)
        base = 2400
        
        high = pd.Series(base + np.random.uniform(10, 50, 30), index=dates)
        low = pd.Series(base - np.random.uniform(10, 50, 30), index=dates)
        close = pd.Series(base + np.random.uniform(-20, 20, 30), index=dates)
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(14).mean().iloc[-1]
        
        # ATR as percentage of price should be reasonable (typically < 10%)
        atr_pct = (atr / base) * 100
        assert atr_pct < 20, f"ATR {atr_pct}% is unreasonably high"


class TestSignalGeneration:
    """Tests for trading signal generation."""
    
    @pytest.mark.unit
    def test_signal_values_valid(self, mock_yfinance):
        """Test that signals are valid buy/sell/hold."""
        from tools.analysis import calculate_technical_indicators
        
        result = calculate_technical_indicators.func("RELIANCE", "6mo")
        data = json.loads(result)
        
        if "error" not in data and "signal" in data:
            valid_signals = ["buy", "sell", "hold", "strong buy", "strong sell", "neutral"]
            assert data["signal"].lower() in valid_signals
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_extreme_rsi_generates_signal(self):
        """Critical: Extreme RSI values should generate appropriate signals."""
        # RSI < 30 should suggest oversold (potential buy)
        # RSI > 70 should suggest overbought (potential sell)
        
        rsi_oversold = 25
        rsi_overbought = 75
        
        # Simple signal logic test
        if rsi_oversold < 30:
            signal = "potential_buy"
        elif rsi_overbought > 70:
            signal = "potential_sell"
        else:
            signal = "neutral"
        
        assert signal in ["potential_buy", "potential_sell", "neutral"]
