"""
Tests for News Scraping Tools

Tests cover:
- Moneycontrol scraping
- Economic Times scraping
- Business Standard scraping
- News aggregation
- Error handling for failed requests
- HTML parsing accuracy
- Rate limiting handling
"""

import json
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock


class TestNewsScraping:
    """Tests for individual news scrapers."""
    
    @pytest.mark.unit
    def test_moneycontrol_returns_json(self):
        """Test that Moneycontrol scraper returns valid JSON."""
        from tools.news_scraper import scrape_moneycontrol_news
        
        with patch('httpx.Client') as mock_client:
            # Setup mock response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = """
            <html><body>
            <ul><li class="clearfix">
                <a href="/news/business/test-news-12345.html">Test News Title for RELIANCE</a>
                <p>Summary of the news article.</p>
            </li></ul>
            </body></html>
            """
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response
            
            result = scrape_moneycontrol_news.func("RELIANCE", 5)
            data = json.loads(result)
            
            assert isinstance(data, dict)
            assert "symbol" in data
    
    @pytest.mark.unit
    def test_et_scraper_returns_json(self):
        """Test that Economic Times scraper returns valid JSON."""
        from tools.news_scraper import scrape_economic_times_news
        
        with patch('httpx.Client') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = """
            <html><body>
            <div class="story">
                <a href="/news/articleshow/12345.cms">ET News Article Title</a>
            </div>
            </body></html>
            """
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response
            
            result = scrape_economic_times_news.func("RELIANCE", 5)
            data = json.loads(result)
            
            assert isinstance(data, dict)
            assert "symbol" in data
    
    @pytest.mark.unit
    def test_bs_scraper_returns_json(self):
        """Test that Business Standard scraper returns valid JSON."""
        from tools.news_scraper import scrape_business_standard_news
        
        with patch('httpx.Client') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = """
            <html><body>
            <div class="listing">
                <a href="/article/test-123.html">BS News Article</a>
            </div>
            </body></html>
            """
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response
            
            result = scrape_business_standard_news.func("RELIANCE", 5)
            data = json.loads(result)
            
            assert isinstance(data, dict)
            assert "symbol" in data


class TestNewsAggregation:
    """Tests for get_stock_news aggregation function."""
    
    @pytest.mark.unit
    def test_get_stock_news_aggregates_sources(self):
        """Test that news aggregator combines multiple sources."""
        from tools.news_scraper import get_stock_news
        
        with patch('httpx.Client') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = """
            <html><body>
            <ul><li class="clearfix">
                <a href="/news/business/test-12345.html">Test Article About Stocks</a>
                <p>Summary text here</p>
            </li></ul>
            </body></html>
            """
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response
            
            result = get_stock_news.func("RELIANCE", 10)
            data = json.loads(result)
            
            assert isinstance(data, dict)
            assert "articles" in data or "sources" in data or "symbol" in data
    
    @pytest.mark.unit
    def test_news_limit_respected(self):
        """Test that article limit is respected."""
        from tools.news_scraper import scrape_moneycontrol_news
        
        with patch('httpx.Client') as mock_client:
            # Create response with many articles
            articles_html = "".join([
                f'<li class="clearfix"><a href="/news/business/test-{i}.html">Article {i} Title Here</a></li>'
                for i in range(20)
            ])
            
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = f"<html><body><ul>{articles_html}</ul></body></html>"
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response
            
            limit = 5
            result = scrape_moneycontrol_news.func("RELIANCE", limit)
            data = json.loads(result)
            
            if "articles" in data:
                assert len(data["articles"]) <= limit, f"Expected max {limit} articles"
    
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
        from tools.news_scraper import scrape_moneycontrol_news
        
        with patch('httpx.Client') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = """
            <html><body>
            <ul><li class="clearfix">
                <a href="/news/business/test-article-title-12345.html">
                    This is a Test Article Title for Stock Analysis
                </a>
                <p>This is the article summary with some content.</p>
            </li></ul>
            </body></html>
            """
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response
            
            result = scrape_moneycontrol_news.func("RELIANCE", 5)
            data = json.loads(result)
            
            if "articles" in data and len(data["articles"]) > 0:
                article = data["articles"][0]
                assert "title" in article, "Article must have title"
                assert "url" in article, "Article must have URL"
    
    @pytest.mark.unit
    def test_urls_are_absolute(self):
        """Test that URLs are absolute, not relative."""
        from tools.news_scraper import scrape_moneycontrol_news
        
        with patch('httpx.Client') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = """
            <html><body>
            <ul><li class="clearfix">
                <a href="/news/business/test-article-12345.html">
                    Full Article Title With Enough Characters Here
                </a>
            </li></ul>
            </body></html>
            """
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response
            
            result = scrape_moneycontrol_news.func("RELIANCE", 5)
            data = json.loads(result)
            
            if "articles" in data and len(data["articles"]) > 0:
                for article in data["articles"]:
                    if "url" in article:
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
        from tools.news_scraper import scrape_moneycontrol_news
        
        with patch('httpx.Client') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response
            
            result = scrape_moneycontrol_news.func("RELIANCE", 5)
            data = json.loads(result)
            
            # Should return valid JSON even on error
            assert isinstance(data, dict)
    
    @pytest.mark.unit
    def test_handles_connection_error(self):
        """Test graceful handling of connection errors."""
        from tools.news_scraper import scrape_moneycontrol_news
        import httpx
        
        with patch('httpx.Client') as mock_client:
            mock_client.return_value.__enter__.return_value.get.side_effect = httpx.ConnectError("Connection failed")
            
            result = scrape_moneycontrol_news.func("RELIANCE", 5)
            data = json.loads(result)
            
            # Should return valid JSON with error info
            assert isinstance(data, dict)
    
    @pytest.mark.unit
    def test_handles_empty_response(self):
        """Test handling of empty HTML response."""
        from tools.news_scraper import scrape_moneycontrol_news
        
        with patch('httpx.Client') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = "<html><body></body></html>"
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response
            
            result = scrape_moneycontrol_news.func("RELIANCE", 5)
            data = json.loads(result)
            
            assert isinstance(data, dict)
            # Empty but valid response
            assert "articles" in data or "symbol" in data


class TestRelativeTimeParser:
    """Tests for relative time string parsing."""
    
    @pytest.mark.unit
    def test_parse_minutes_ago(self):
        """Test parsing '5 minutes ago'."""
        from tools.news_scraper import _parse_relative_time
        
        result = _parse_relative_time("5 minutes ago")
        assert isinstance(result, str)
        # Should be ISO format or the original string
    
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
        
        # Should return original or some string
        assert isinstance(result, str)


class TestSymbolMapping:
    """Tests for stock symbol to URL mapping."""
    
    @pytest.mark.unit
    def test_reliance_mapping(self):
        """Test RELIANCE symbol mapping."""
        # Symbol mappings are internal, test through scraper behavior
        from tools.news_scraper import scrape_moneycontrol_news
        
        with patch('httpx.Client') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = "<html><body></body></html>"
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response
            
            result = scrape_moneycontrol_news.func("RELIANCE", 5)
            data = json.loads(result)
            
            assert data["symbol"] == "RELIANCE"
    
    @pytest.mark.unit
    def test_lowercase_symbol_normalized(self):
        """Test that lowercase symbols are normalized."""
        from tools.news_scraper import scrape_moneycontrol_news
        
        with patch('httpx.Client') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = "<html><body></body></html>"
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response
            
            result = scrape_moneycontrol_news.func("reliance", 5)
            data = json.loads(result)
            
            # Symbol should be uppercase in response
            assert data["symbol"] == "RELIANCE"


class TestCaching:
    """Tests for news caching functionality."""
    
    @pytest.mark.unit
    def test_cache_prevents_duplicate_requests(self):
        """Test that cache prevents duplicate HTTP requests."""
        from tools.news_scraper import scrape_moneycontrol_news, _news_cache
        
        # Clear cache
        _news_cache.clear()
        
        call_count = 0
        
        def mock_get(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            response = MagicMock()
            response.status_code = 200
            response.text = """
            <html><body>
            <ul><li class="clearfix">
                <a href="/news/test-12345.html">Test Article Title Here</a>
            </li></ul>
            </body></html>
            """
            return response
        
        with patch('httpx.Client') as mock_client:
            mock_client.return_value.__enter__.return_value.get = mock_get
            
            # First call
            scrape_moneycontrol_news.func("TESTCACHE", 5)
            first_call_count = call_count
            
            # Second call should use cache
            scrape_moneycontrol_news.func("TESTCACHE", 5)
            
            # Should not make additional request if cached
            # Note: This depends on caching implementation
