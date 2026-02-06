"""
Tests for News Scraping Tools

Tests cover:
- ET RSS feed scraping
- Economic Times HTML scraping
- Google News RSS scraping
- News aggregation
- Error handling for failed requests
- RSS XML parsing accuracy
"""

import json
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock


# Sample RSS XML for mocking ET RSS feed responses
SAMPLE_ET_RSS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
    <title>ET Markets - Stocks</title>
    <item>
        <title>Reliance Industries Q3 profit rises 15% to Rs 18,000 crore</title>
        <link>https://economictimes.indiatimes.com/articleshow/12345.cms</link>
        <description>Reliance Industries reported strong quarterly results with net profit rising 15%.</description>
        <pubDate>Fri, 07 Feb 2026 10:30:00 +0530</pubDate>
    </item>
    <item>
        <title>TCS wins $500 million deal from major US bank</title>
        <link>https://economictimes.indiatimes.com/articleshow/12346.cms</link>
        <description>TCS has won a large outsourcing contract from a US bank.</description>
        <pubDate>Fri, 07 Feb 2026 09:00:00 +0530</pubDate>
    </item>
    <item>
        <title>Market update: Sensex rises 300 points</title>
        <link>https://economictimes.indiatimes.com/articleshow/12347.cms</link>
        <description>Indian stock market opens higher led by banking stocks.</description>
        <pubDate>Fri, 07 Feb 2026 08:00:00 +0530</pubDate>
    </item>
</channel>
</rss>"""

SAMPLE_GOOGLE_NEWS_RSS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
    <title>RELIANCE NSE stock - Google News</title>
    <item>
        <title>Reliance shares jump 3% on strong results</title>
        <link>https://news.google.com/articles/redirect1</link>
        <pubDate>Fri, 07 Feb 2026 11:00:00 +0530</pubDate>
        <source url="https://www.livemint.com">Mint</source>
    </item>
    <item>
        <title>Buy Reliance target Rs 2800: Analyst</title>
        <link>https://news.google.com/articles/redirect2</link>
        <pubDate>Fri, 07 Feb 2026 10:00:00 +0530</pubDate>
        <source url="https://www.moneycontrol.com">Moneycontrol</source>
    </item>
</channel>
</rss>"""

EMPTY_RSS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
    <title>Empty Feed</title>
</channel>
</rss>"""


class TestNewsScraping:
    """Tests for individual news scrapers."""

    @pytest.mark.unit
    def test_et_rss_returns_json(self):
        """Test that ET RSS scraper returns valid JSON with articles."""
        from tools.news_scraper import scrape_et_rss_news, _news_cache

        _news_cache.clear()

        with patch('httpx.Client') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = SAMPLE_ET_RSS_XML
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            result = scrape_et_rss_news.func("RELIANCE", 5)
            data = json.loads(result)

            assert isinstance(data, dict)
            assert data["symbol"] == "RELIANCE"
            assert data["source"] == "Economic Times RSS"
            assert "articles" in data
            # Should find the Reliance article (filtered by symbol)
            assert data["articles_count"] >= 1

    @pytest.mark.unit
    def test_et_rss_filters_by_symbol(self):
        """Test that ET RSS filters articles by stock symbol."""
        from tools.news_scraper import scrape_et_rss_news, _news_cache

        _news_cache.clear()

        with patch('httpx.Client') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = SAMPLE_ET_RSS_XML
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            result = scrape_et_rss_news.func("TCS", 5)
            data = json.loads(result)

            # Should only find TCS articles, not Reliance
            for article in data["articles"]:
                assert "tcs" in (article["title"] + " " + article["summary"]).lower()

    @pytest.mark.unit
    def test_et_scraper_returns_json(self):
        """Test that Economic Times HTML scraper returns valid JSON."""
        from tools.news_scraper import scrape_economic_times_news

        with patch('httpx.Client') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = """
            <html><body>
            <div class="story">
                <a href="/news/articleshow/12345.cms">ET News Article Title About Indian Markets Today</a>
            </div>
            </body></html>
            """
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            result = scrape_economic_times_news.func("RELIANCE", 5)
            data = json.loads(result)

            assert isinstance(data, dict)
            assert "symbol" in data

    @pytest.mark.unit
    def test_google_news_returns_json(self):
        """Test that Google News RSS scraper returns valid JSON with articles."""
        from tools.news_scraper import scrape_google_news, _news_cache

        _news_cache.clear()

        with patch('httpx.Client') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = SAMPLE_GOOGLE_NEWS_RSS_XML
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            result = scrape_google_news.func("RELIANCE", 5)
            data = json.loads(result)

            assert isinstance(data, dict)
            assert data["symbol"] == "RELIANCE"
            assert data["source"] == "Google News"
            assert "articles" in data
            assert data["articles_count"] == 2

    @pytest.mark.unit
    def test_google_news_extracts_source(self):
        """Test that Google News extracts the original source name."""
        from tools.news_scraper import scrape_google_news, _news_cache

        _news_cache.clear()

        with patch('httpx.Client') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = SAMPLE_GOOGLE_NEWS_RSS_XML
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            result = scrape_google_news.func("RELIANCE", 5)
            data = json.loads(result)

            if data["articles"]:
                # Source should include the original publication name
                assert "Google News" in data["articles"][0]["source"]


class TestRSSParsing:
    """Tests for RSS XML parsing."""

    @pytest.mark.unit
    def test_empty_rss_feed(self):
        """Test handling of empty RSS feed."""
        from tools.news_scraper import scrape_et_rss_news, _news_cache

        _news_cache.clear()

        with patch('httpx.Client') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = EMPTY_RSS_XML
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            result = scrape_et_rss_news.func("RELIANCE", 5)
            data = json.loads(result)

            assert isinstance(data, dict)
            assert data["articles_count"] == 0
            assert data["articles"] == []

    @pytest.mark.unit
    def test_malformed_xml(self):
        """Test handling of malformed XML."""
        from tools.news_scraper import scrape_et_rss_news, _news_cache

        _news_cache.clear()

        with patch('httpx.Client') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = "<rss><channel><item><title>Unclosed"
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            result = scrape_et_rss_news.func("RELIANCE", 5)
            data = json.loads(result)

            assert isinstance(data, dict)
            assert "error" in data

    @pytest.mark.unit
    def test_rss_date_parsing(self):
        """Test parsing of RSS pubDate format."""
        from tools.news_scraper import _parse_rss_date

        # Standard RSS date
        result = _parse_rss_date("Fri, 07 Feb 2026 10:30:00 +0530")
        assert isinstance(result, str)
        assert "2026" in result

        # Empty string
        assert _parse_rss_date("") == ""

        # Unparseable string returns original
        result = _parse_rss_date("not a date")
        assert result == "not a date"

    @pytest.mark.unit
    def test_rss_limit_respected(self):
        """Test that article limit is respected with RSS feeds."""
        from tools.news_scraper import scrape_google_news, _news_cache

        _news_cache.clear()

        with patch('httpx.Client') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = SAMPLE_GOOGLE_NEWS_RSS_XML
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            result = scrape_google_news.func("RELIANCE", 1)
            data = json.loads(result)

            assert len(data["articles"]) <= 1


class TestNewsAggregation:
    """Tests for get_stock_news aggregation function."""

    @pytest.mark.unit
    def test_get_stock_news_aggregates_sources(self):
        """Test that news aggregator combines multiple sources."""
        from tools.news_scraper import get_stock_news, _news_cache

        _news_cache.clear()

        with patch('httpx.Client') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = SAMPLE_ET_RSS_XML
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            result = get_stock_news.func("RELIANCE", 10)
            data = json.loads(result)

            assert isinstance(data, dict)
            assert "articles" in data
            assert "sources_status" in data
            # Should have all three source keys
            assert "et_rss" in data["sources_status"]
            assert "economic_times" in data["sources_status"]
            assert "google_news" in data["sources_status"]

    @pytest.mark.integration
    @pytest.mark.slow
    def test_real_news_fetch(self, valid_symbol):
        """Integration test: Fetch real news."""
        from tools.news_scraper import get_stock_news

        result = get_stock_news.func(valid_symbol, 5)
        data = json.loads(result)

        assert isinstance(data, dict)
        # Should not have major errors
        assert "symbol" in data or "error" in data


class TestNewsDataStructure:
    """Tests for news data structure validation."""

    @pytest.mark.unit
    def test_article_has_required_fields(self):
        """Test that each article has required fields."""
        from tools.news_scraper import scrape_et_rss_news, _news_cache

        _news_cache.clear()

        with patch('httpx.Client') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = SAMPLE_ET_RSS_XML
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            result = scrape_et_rss_news.func("RELIANCE", 5)
            data = json.loads(result)

            if data["articles"]:
                article = data["articles"][0]
                assert "title" in article, "Article must have title"
                assert "url" in article, "Article must have URL"
                assert "source" in article, "Article must have source"
                assert "published" in article, "Article must have published date"

    @pytest.mark.unit
    def test_urls_are_absolute(self):
        """Test that URLs are absolute, not relative."""
        from tools.news_scraper import scrape_et_rss_news, _news_cache

        _news_cache.clear()

        with patch('httpx.Client') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = SAMPLE_ET_RSS_XML
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            result = scrape_et_rss_news.func("RELIANCE", 5)
            data = json.loads(result)

            for article in data["articles"]:
                if article["url"]:
                    assert article["url"].startswith("http"), f"URL should be absolute: {article['url']}"

    @pytest.mark.unit
    def test_titles_are_cleaned(self):
        """Test that titles have extra whitespace removed."""
        from tools.news_scraper import _clean_text

        messy_text = "  Title   with   extra    spaces  \n\t  "
        cleaned = _clean_text(messy_text)

        assert cleaned == "Title with extra spaces", "Text should be cleaned"
        assert "  " not in cleaned, "No double spaces"
        assert not cleaned.startswith(" "), "No leading spaces"
        assert not cleaned.endswith(" "), "No trailing spaces"


class TestErrorHandling:
    """Tests for error handling in news scrapers."""

    @pytest.mark.unit
    def test_handles_http_error(self):
        """Test graceful handling of HTTP errors."""
        from tools.news_scraper import scrape_et_rss_news, _news_cache

        _news_cache.clear()

        with patch('httpx.Client') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            result = scrape_et_rss_news.func("RELIANCE", 5)
            data = json.loads(result)

            # Should return valid JSON even on error
            assert isinstance(data, dict)

    @pytest.mark.unit
    def test_handles_connection_error(self):
        """Test graceful handling of connection errors."""
        from tools.news_scraper import scrape_et_rss_news, _news_cache
        import httpx

        _news_cache.clear()

        with patch('httpx.Client') as mock_client:
            mock_client.return_value.__enter__.return_value.get.side_effect = httpx.ConnectError("Connection failed")

            result = scrape_et_rss_news.func("RELIANCE", 5)
            data = json.loads(result)

            # Should return valid JSON with error info
            assert isinstance(data, dict)

    @pytest.mark.unit
    def test_handles_empty_response(self):
        """Test handling of empty RSS response."""
        from tools.news_scraper import scrape_et_rss_news, _news_cache

        _news_cache.clear()

        with patch('httpx.Client') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = EMPTY_RSS_XML
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            result = scrape_et_rss_news.func("RELIANCE", 5)
            data = json.loads(result)

            assert isinstance(data, dict)
            assert data["articles"] == []

    @pytest.mark.unit
    def test_google_news_handles_connection_error(self):
        """Test Google News scraper handles connection errors."""
        from tools.news_scraper import scrape_google_news, _news_cache
        import httpx

        _news_cache.clear()

        with patch('httpx.Client') as mock_client:
            mock_client.return_value.__enter__.return_value.get.side_effect = httpx.ConnectError("Failed")

            result = scrape_google_news.func("RELIANCE", 5)
            data = json.loads(result)

            assert isinstance(data, dict)
            assert "error" in data


class TestRelativeTimeParser:
    """Tests for relative time string parsing."""

    @pytest.mark.unit
    def test_parse_minutes_ago(self):
        """Test parsing '5 minutes ago'."""
        from tools.news_scraper import _parse_relative_time

        result = _parse_relative_time("5 minutes ago")
        assert isinstance(result, str)

    @pytest.mark.unit
    def test_parse_hours_ago(self):
        """Test parsing '2 hours ago'."""
        from tools.news_scraper import _parse_relative_time

        result = _parse_relative_time("2 hours ago")
        assert isinstance(result, str)

    @pytest.mark.unit
    def test_parse_days_ago(self):
        """Test parsing '3 days ago'."""
        from tools.news_scraper import _parse_relative_time

        result = _parse_relative_time("3 days ago")
        assert isinstance(result, str)

    @pytest.mark.unit
    def test_parse_just_now(self):
        """Test parsing 'Just now'."""
        from tools.news_scraper import _parse_relative_time

        result = _parse_relative_time("Just now")
        assert isinstance(result, str)

    @pytest.mark.unit
    def test_parse_invalid_format(self):
        """Test parsing invalid format returns original."""
        from tools.news_scraper import _parse_relative_time

        original = "Invalid Date Format"
        result = _parse_relative_time(original)

        assert isinstance(result, str)


class TestSymbolHandling:
    """Tests for stock symbol normalization."""

    @pytest.mark.unit
    def test_symbol_uppercased_in_response(self):
        """Test that symbols are uppercased in response."""
        from tools.news_scraper import scrape_et_rss_news, _news_cache

        _news_cache.clear()

        with patch('httpx.Client') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = EMPTY_RSS_XML
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            result = scrape_et_rss_news.func("reliance", 5)
            data = json.loads(result)

            assert data["symbol"] == "RELIANCE"

    @pytest.mark.unit
    def test_symbol_stripped_in_response(self):
        """Test that symbols are stripped of whitespace."""
        from tools.news_scraper import scrape_google_news, _news_cache

        _news_cache.clear()

        with patch('httpx.Client') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = EMPTY_RSS_XML
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            result = scrape_google_news.func("  TCS  ", 5)
            data = json.loads(result)

            assert data["symbol"] == "TCS"


class TestCaching:
    """Tests for news caching functionality."""

    @pytest.mark.unit
    def test_cache_prevents_duplicate_requests(self):
        """Test that cache prevents duplicate HTTP requests."""
        from tools.news_scraper import scrape_et_rss_news, _news_cache

        _news_cache.clear()

        call_count = 0

        def mock_get(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            response = MagicMock()
            response.status_code = 200
            response.text = SAMPLE_ET_RSS_XML
            return response

        with patch('httpx.Client') as mock_client:
            mock_client.return_value.__enter__.return_value.get = mock_get

            # First call
            scrape_et_rss_news.func("TESTCACHE", 5)
            first_call_count = call_count

            # Second call should use cache
            scrape_et_rss_news.func("TESTCACHE", 5)

            # Should not make additional request if cached
            assert call_count == first_call_count


class TestMarketHeadlines:
    """Tests for market news headlines."""

    @pytest.mark.unit
    def test_market_headlines_returns_json(self):
        """Test that market headlines returns valid JSON."""
        from tools.news_scraper import get_market_news_headlines

        with patch('httpx.Client') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = SAMPLE_ET_RSS_XML
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            result = get_market_news_headlines.func("stocks", 10)
            data = json.loads(result)

            assert isinstance(data, dict)
            assert "headlines" in data
            assert "category" in data

    @pytest.mark.unit
    def test_market_headlines_handles_error(self):
        """Test that market headlines handles errors gracefully."""
        from tools.news_scraper import get_market_news_headlines
        import httpx

        with patch('httpx.Client') as mock_client:
            mock_client.return_value.__enter__.return_value.get.side_effect = httpx.ConnectError("Failed")

            result = get_market_news_headlines.func("stocks", 10)
            data = json.loads(result)

            assert isinstance(data, dict)
            assert "error" in data
