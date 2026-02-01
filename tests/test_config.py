"""
Tests for Configuration Module

Tests cover:
- Settings loading from environment
- Default values
- Directory creation
- Configuration constants validation
"""

import os
import pytest
from pathlib import Path


class TestSettings:
    """Tests for Settings class."""
    
    @pytest.mark.unit
    def test_settings_loads_defaults(self):
        """Test that settings loads with default values."""
        from config import Settings
        
        # Create settings without env file
        settings = Settings(_env_file=None)
        
        # Check default values
        assert settings.llm_model == "mistral/mistral-large-latest"
        assert settings.llm_temperature == 0.7
        assert settings.cache_ttl_minutes == 15
        assert settings.max_requests_per_minute == 10
        assert settings.log_level == "INFO"
    
    @pytest.mark.unit
    def test_settings_base_dir_is_valid(self):
        """Test that base_dir points to project root."""
        from config import settings
        
        assert settings.base_dir.exists()
        assert (settings.base_dir / "config.py").exists()
    
    @pytest.mark.unit
    def test_data_directories_exist(self):
        """Test that data directories are created."""
        from config import settings
        
        settings.ensure_dirs()
        
        assert settings.data_dir.exists()
        assert settings.reports_dir.exists()
        assert settings.cache_dir.exists()
    
    @pytest.mark.unit
    def test_admin_ids_parsing_empty(self):
        """Test admin IDs parsing with empty string."""
        from config import Settings
        
        settings = Settings(telegram_admin_ids="", _env_file=None)
        assert settings.admin_ids == []
    
    @pytest.mark.unit
    def test_admin_ids_parsing_single(self):
        """Test admin IDs parsing with single ID."""
        from config import Settings
        
        settings = Settings(telegram_admin_ids="123456789", _env_file=None)
        assert settings.admin_ids == [123456789]
    
    @pytest.mark.unit
    def test_admin_ids_parsing_multiple(self):
        """Test admin IDs parsing with multiple IDs."""
        from config import Settings
        
        settings = Settings(telegram_admin_ids="123, 456, 789", _env_file=None)
        assert settings.admin_ids == [123, 456, 789]


class TestIndianMarketConfig:
    """Tests for Indian market configuration constants."""
    
    @pytest.mark.unit
    def test_indian_indices_defined(self):
        """Test that major Indian indices are configured."""
        from config import INDIAN_INDICES
        
        assert "NIFTY50" in INDIAN_INDICES
        assert "SENSEX" in INDIAN_INDICES
        assert "BANKNIFTY" in INDIAN_INDICES
    
    @pytest.mark.unit
    def test_nifty50_stocks_count(self):
        """Test that NIFTY50 list has expected count."""
        from config import NIFTY50_STOCKS
        
        # NIFTY50 should have exactly 50 stocks
        assert len(NIFTY50_STOCKS) == 50
    
    @pytest.mark.unit
    def test_nifty50_contains_major_stocks(self):
        """Test that NIFTY50 contains major stocks."""
        from config import NIFTY50_STOCKS
        
        major_stocks = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK"]
        for stock in major_stocks:
            assert stock in NIFTY50_STOCKS
    
    @pytest.mark.unit
    def test_sectors_defined(self):
        """Test that sector classification is complete."""
        from config import SECTORS
        
        expected_sectors = ["IT", "BANKING", "PHARMA", "AUTO", "FMCG", "METALS", "ENERGY"]
        for sector in expected_sectors:
            assert sector in SECTORS
            assert len(SECTORS[sector]) > 0
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_nifty50_all_uppercase(self):
        """Test that all stock symbols are uppercase (consistency)."""
        from config import NIFTY50_STOCKS
        
        for stock in NIFTY50_STOCKS:
            assert stock == stock.upper(), f"Stock {stock} should be uppercase"
    
    @pytest.mark.unit
    def test_news_sources_configured(self):
        """Test that news sources are properly configured."""
        from config import NEWS_SOURCES
        
        assert "moneycontrol" in NEWS_SOURCES
        assert "economictimes" in NEWS_SOURCES
        
        # Each source should have base_url
        for source, config in NEWS_SOURCES.items():
            assert "base_url" in config


class TestTechnicalConfig:
    """Tests for technical analysis configuration."""
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_technical_config_valid_periods(self):
        """Test that technical config has valid periods."""
        from config import TECHNICAL_CONFIG
        
        # MA periods should be in ascending order
        assert TECHNICAL_CONFIG["short_ma"] < TECHNICAL_CONFIG["medium_ma"]
        assert TECHNICAL_CONFIG["medium_ma"] < TECHNICAL_CONFIG["long_ma"]
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_rsi_thresholds_valid(self):
        """Test that RSI thresholds are valid."""
        from config import TECHNICAL_CONFIG
        
        # RSI is between 0 and 100
        assert 0 < TECHNICAL_CONFIG["rsi_oversold"] < 50
        assert 50 < TECHNICAL_CONFIG["rsi_overbought"] < 100
        assert TECHNICAL_CONFIG["rsi_oversold"] < TECHNICAL_CONFIG["rsi_overbought"]
    
    @pytest.mark.unit
    def test_macd_parameters_valid(self):
        """Test that MACD parameters follow convention."""
        from config import TECHNICAL_CONFIG
        
        # Standard MACD: fast < slow
        assert TECHNICAL_CONFIG["macd_fast"] < TECHNICAL_CONFIG["macd_slow"]


class TestFundamentalThresholds:
    """Tests for fundamental analysis thresholds."""
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_pe_ratio_thresholds_valid(self):
        """Test that PE ratio thresholds are reasonable."""
        from config import FUNDAMENTAL_THRESHOLDS
        
        # Low should be less than high
        assert FUNDAMENTAL_THRESHOLDS["pe_ratio_low"] < FUNDAMENTAL_THRESHOLDS["pe_ratio_high"]
        # Both should be positive
        assert FUNDAMENTAL_THRESHOLDS["pe_ratio_low"] > 0
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_debt_equity_max_reasonable(self):
        """Test that debt/equity max is reasonable."""
        from config import FUNDAMENTAL_THRESHOLDS
        
        # D/E > 2 is generally considered risky
        assert 0 < FUNDAMENTAL_THRESHOLDS["debt_equity_max"] <= 2
    
    @pytest.mark.unit
    def test_roe_roce_minimums_positive(self):
        """Test that ROE/ROCE minimums are positive."""
        from config import FUNDAMENTAL_THRESHOLDS
        
        assert FUNDAMENTAL_THRESHOLDS["roe_min"] > 0
        assert FUNDAMENTAL_THRESHOLDS["roce_min"] > 0
