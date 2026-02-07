"""
Tools package for Stock Research Assistant
"""

from tools.market_data import (
    get_stock_price,
    get_stock_info,
    get_historical_data,
    get_index_data,
    get_nse_stock_quote,
)
from tools.news_scraper import (
    scrape_et_rss_news,
    scrape_economic_times_news,
    scrape_google_news,
    get_stock_news,
    get_market_news_headlines,
)
from tools.analysis import (
    calculate_technical_indicators,
    get_fundamental_metrics,
    analyze_price_action,
)
from tools.institutional import (
    get_fii_dii_data,
    get_bulk_block_deals,
    get_promoter_holdings,
    get_mutual_fund_holdings,
)

__all__ = [
    "get_stock_price",
    "get_stock_info",
    "get_historical_data",
    "get_index_data",
    "get_nse_stock_quote",
    "scrape_et_rss_news",
    "scrape_economic_times_news",
    "scrape_google_news",
    "get_stock_news",
    "calculate_technical_indicators",
    "get_fundamental_metrics",
    "analyze_price_action",
    "get_fii_dii_data",
    "get_bulk_block_deals",
    "get_market_news_headlines",
    "get_promoter_holdings",
    "get_mutual_fund_holdings",
]
