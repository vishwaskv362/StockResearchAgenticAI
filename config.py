"""
Configuration settings for Stock Research Assistant
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # ==========================================
    # LLM Configuration
    # ==========================================
    mistral_api_key: str = Field(default="", env="MISTRAL_API_KEY")
    llm_model: str = Field(default="mistral/mistral-large-latest", env="LLM_MODEL")
    llm_temperature: float = Field(default=0.7, env="LLM_TEMPERATURE")
    llm_timeout: int = Field(default=600, env="LLM_TIMEOUT")
    llm_max_retries: int = Field(default=3, env="LLM_MAX_RETRIES")
    llm_retry_delay: int = Field(default=5, env="LLM_RETRY_DELAY")
    
    # ==========================================
    # Telegram Bot Configuration
    # ==========================================
    telegram_bot_token: str = Field(default="", env="TELEGRAM_BOT_TOKEN")
    telegram_admin_ids: str = Field(default="", env="TELEGRAM_ADMIN_IDS")
    
    # ==========================================
    # Cache Configuration
    # ==========================================
    cache_ttl_minutes: int = Field(default=15, env="CACHE_TTL_MINUTES")
    
    # ==========================================
    # Rate Limiting
    # ==========================================
    max_requests_per_minute: int = Field(default=10, env="MAX_REQUESTS_PER_MINUTE")
    
    # ==========================================
    # Logging
    # ==========================================
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # ==========================================
    # File Paths
    # ==========================================
    base_dir: Path = Path(__file__).parent
    data_dir: Path = base_dir / "data"
    reports_dir: Path = data_dir / "reports"
    cache_dir: Path = data_dir / "cache"
    
    @property
    def admin_ids(self) -> list[int]:
        """Parse admin IDs from comma-separated string."""
        if not self.telegram_admin_ids:
            return []
        ids = []
        for item in self.telegram_admin_ids.split(","):
            item = item.strip()
            if item.isdigit():
                ids.append(int(item))
        return ids
    
    def ensure_dirs(self):
        """Create necessary directories if they don't exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# ==========================================
# Indian Market Configuration
# ==========================================

# Major Indian Stock Indices
INDIAN_INDICES = {
    "NIFTY50": "^NSEI",
    "BANKNIFTY": "^NSEBANK",
    "NIFTYIT": "^CNXIT",
    "SENSEX": "^BSESN",
}

# Popular Large Cap Stocks for Quick Analysis
NIFTY50_STOCKS = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
    "HINDUNILVR", "SBIN", "BHARTIARTL", "ITC", "KOTAKBANK",
    "LT", "AXISBANK", "ASIANPAINT", "MARUTI", "BAJFINANCE",
    "TITAN", "SUNPHARMA", "ULTRACEMCO", "NESTLEIND", "WIPRO",
    "HCLTECH", "M&M", "NTPC", "POWERGRID", "TECHM",
    "TATASTEEL", "JSWSTEEL", "ADANIENT", "ADANIPORTS", "BAJAJFINSV",
    "TATAMOTORS", "ONGC", "COALINDIA", "BRITANNIA", "HINDALCO",
    "DRREDDY", "CIPLA", "APOLLOHOSP", "EICHERMOT", "GRASIM",
    "DIVISLAB", "BPCL", "TATACONSUM", "HEROMOTOCO", "INDUSINDBK",
    "SBILIFE", "HDFCLIFE", "UPL", "BAJAJ-AUTO", "SHREECEM",
]

# Sector Classification
SECTORS = {
    "IT": ["TCS", "INFY", "WIPRO", "HCLTECH", "TECHM", "LTIM", "MPHASIS", "COFORGE"],
    "BANKING": ["HDFCBANK", "ICICIBANK", "SBIN", "KOTAKBANK", "AXISBANK", "INDUSINDBK", "BANDHANBNK"],
    "PHARMA": ["SUNPHARMA", "DRREDDY", "CIPLA", "DIVISLAB", "APOLLOHOSP", "BIOCON", "LUPIN"],
    "AUTO": ["MARUTI", "TATAMOTORS", "M&M", "BAJAJ-AUTO", "HEROMOTOCO", "EICHERMOT", "ASHOKLEY"],
    "FMCG": ["HINDUNILVR", "ITC", "NESTLEIND", "BRITANNIA", "TATACONSUM", "DABUR", "MARICO"],
    "METALS": ["TATASTEEL", "JSWSTEEL", "HINDALCO", "VEDL", "NMDC", "SAIL", "JINDALSTEL"],
    "ENERGY": ["RELIANCE", "ONGC", "BPCL", "NTPC", "POWERGRID", "COALINDIA", "GAIL", "IOC"],
    "FINANCE": ["BAJFINANCE", "BAJAJFINSV", "SBILIFE", "HDFCLIFE", "ICICIPRULI", "CHOLAFIN"],
    "REALTY": ["DLF", "GODREJPROP", "OBEROIRLTY", "PRESTIGE", "BRIGADE", "SOBHA"],
    "TELECOM": ["BHARTIARTL", "IDEA", "TATACOMM"],
}

# Sector Valuation Benchmarks
# Based on typical multiples for each sector in Indian markets
SECTOR_VALUATION_BENCHMARKS = {
    "IT": {
        "pe_range": (20, 30),
        "pb_range": (4, 8),
        "ev_ebitda_range": (12, 20),
        "roe_min": 18,
        "description": "High-margin, asset-light, consistent cash flows",
    },
    "BANKING": {
        "pe_range": (10, 18),
        "pb_range": (1.5, 3.5),
        "ev_ebitda_range": None,  # Not applicable for banks
        "roe_min": 12,
        "description": "Regulated, leverage-intensive, sensitive to NPAs",
    },
    "PHARMA": {
        "pe_range": (18, 28),
        "pb_range": (3, 6),
        "ev_ebitda_range": (10, 18),
        "roe_min": 15,
        "description": "R&D intensive, regulatory risks, patent exposure",
    },
    "AUTO": {
        "pe_range": (12, 22),
        "pb_range": (2, 4),
        "ev_ebitda_range": (8, 15),
        "roe_min": 12,
        "description": "Cyclical, capital intensive, commodity exposure",
    },
    "FMCG": {
        "pe_range": (35, 55),
        "pb_range": (8, 15),
        "ev_ebitda_range": (20, 35),
        "roe_min": 20,
        "description": "Premium valuations, stable demand, brand moats",
    },
    "METALS": {
        "pe_range": (5, 12),
        "pb_range": (0.8, 2),
        "ev_ebitda_range": (4, 8),
        "roe_min": 10,
        "description": "Commodity cyclical, low margins, volatile earnings",
    },
    "ENERGY": {
        "pe_range": (8, 16),
        "pb_range": (1, 2.5),
        "ev_ebitda_range": (5, 10),
        "roe_min": 10,
        "description": "Capital intensive, commodity linked, regulated",
    },
    "FINANCE": {
        "pe_range": (15, 30),
        "pb_range": (2, 5),
        "ev_ebitda_range": None,  # Not applicable for financials
        "roe_min": 15,
        "description": "NBFCs and insurance, growth premium to banks",
    },
    "REALTY": {
        "pe_range": (10, 20),
        "pb_range": (0.5, 1.5),
        "ev_ebitda_range": (8, 15),
        "roe_min": 8,
        "description": "Cyclical, project-based, working capital intensive",
    },
    "TELECOM": {
        "pe_range": (15, 25),
        "pb_range": (1.5, 3),
        "ev_ebitda_range": (6, 12),
        "roe_min": 10,
        "description": "Capital intensive, regulatory risk, pricing pressure",
    },
}

# News Sources for Scraping
NEWS_SOURCES = {
    "moneycontrol": {
        "base_url": "https://www.moneycontrol.com",
        "news_url": "https://www.moneycontrol.com/news/business/stocks/",
        "search_url": "https://www.moneycontrol.com/news/tags/{stock}.html",
    },
    "economictimes": {
        "base_url": "https://economictimes.indiatimes.com",
        "news_url": "https://economictimes.indiatimes.com/markets/stocks/news",
        "search_url": "https://economictimes.indiatimes.com/topic/{stock}",
    },
    "businessstandard": {
        "base_url": "https://www.business-standard.com",
        "news_url": "https://www.business-standard.com/markets/news",
    },
}

# ==========================================
# Analysis Configuration
# ==========================================

# Technical Analysis Parameters
TECHNICAL_CONFIG = {
    "short_ma": 20,
    "medium_ma": 50,
    "long_ma": 200,
    "rsi_period": 14,
    "rsi_oversold": 30,
    "rsi_overbought": 70,
    "macd_fast": 12,
    "macd_slow": 26,
    "macd_signal": 9,
    "bollinger_period": 20,
    "bollinger_std": 2,
    "atr_period": 14,
}

# Fundamental Analysis Thresholds
FUNDAMENTAL_THRESHOLDS = {
    "pe_ratio_low": 15,
    "pe_ratio_high": 30,
    "pb_ratio_low": 1,
    "pb_ratio_high": 5,
    "debt_equity_max": 1.5,
    "roe_min": 15,
    "roce_min": 15,
    "dividend_yield_min": 1,
    "earnings_growth_min": 10,
}

# Report Configuration
REPORT_CONFIG = {
    "include_charts": True,
    "include_peer_comparison": True,
    "include_risk_assessment": True,
    "historical_years": 5,
    "forecast_years": 2,
}


# Global settings instance
settings = Settings()
settings.ensure_dirs()
