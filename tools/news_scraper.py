"""
News Scraping Tools for Indian Stock Market
Uses RSS feeds (Economic Times, Google News) and ET HTML scraping for reliable news data.
"""

import json
import re
import threading
import xml.etree.ElementTree as ET
from collections import OrderedDict
from datetime import datetime, timedelta
from typing import Optional
import httpx
from bs4 import BeautifulSoup
from crewai.tools import tool
from tenacity import retry, stop_after_attempt, wait_exponential

# Common headers for web scraping
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# Thread-safe news cache with LRU eviction
_news_cache_lock = threading.Lock()
_news_cache: OrderedDict = OrderedDict()
_cache_ttl = 600  # 10 minutes
_cache_max_size = 100


def _news_cache_get(key: str) -> dict | None:
    """Thread-safe cache read."""
    with _news_cache_lock:
        if key not in _news_cache:
            return None
        entry = _news_cache[key]
        if (datetime.now().timestamp() - entry["timestamp"]) >= _cache_ttl:
            del _news_cache[key]
            return None
        _news_cache.move_to_end(key)
        return entry


def _news_cache_set(key: str, data: dict) -> None:
    """Thread-safe cache write with LRU eviction."""
    with _news_cache_lock:
        _news_cache[key] = {"data": data, "timestamp": datetime.now().timestamp()}
        _news_cache.move_to_end(key)
        while len(_news_cache) > _cache_max_size:
            _news_cache.popitem(last=False)


def _clean_text(text: str) -> str:
    """Clean and normalize text content."""
    if not text:
        return ""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove special characters but keep punctuation
    text = text.strip()
    return text


def _parse_relative_time(time_str: str) -> str:
    """Parse relative time strings like '2 hours ago' to ISO format."""
    now = datetime.now()
    time_str = time_str.lower().strip()

    if "just now" in time_str or "moment" in time_str:
        return now.isoformat()

    # Extract number and unit
    match = re.search(r'(\d+)\s*(minute|hour|day|week|month)s?\s*ago', time_str)
    if match:
        value = int(match.group(1))
        unit = match.group(2)

        if unit == "minute":
            dt = now - timedelta(minutes=value)
        elif unit == "hour":
            dt = now - timedelta(hours=value)
        elif unit == "day":
            dt = now - timedelta(days=value)
        elif unit == "week":
            dt = now - timedelta(weeks=value)
        elif unit == "month":
            dt = now - timedelta(days=value * 30)
        else:
            dt = now

        return dt.isoformat()

    # If it's already a date string, try to parse it
    try:
        # Try various date formats
        for fmt in ["%B %d, %Y", "%d %B %Y", "%d-%m-%Y", "%Y-%m-%d"]:
            try:
                dt = datetime.strptime(time_str, fmt)
                return dt.isoformat()
            except ValueError:
                continue
    except (ValueError, TypeError):
        pass

    return time_str


def _parse_rss_date(date_str: str) -> str:
    """Parse RSS pubDate format (RFC 822) to ISO format."""
    if not date_str:
        return ""
    date_str = date_str.strip()
    # RSS dates look like: "Fri, 07 Feb 2026 10:30:00 +0530"
    rss_formats = [
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%d %b %Y %H:%M:%S %z",
        "%Y-%m-%dT%H:%M:%S%z",
    ]
    for fmt in rss_formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.isoformat()
        except ValueError:
            continue
    return date_str


@tool("Scrape ET RSS News")
def scrape_et_rss_news(symbol: str, limit: int = 10) -> str:
    """
    Fetch latest stock news from Economic Times RSS feed.

    Args:
        symbol: Stock symbol (e.g., 'RELIANCE', 'TCS')
        limit: Maximum number of news articles to fetch (default: 10)

    Returns:
        JSON string with list of news articles including title, summary, date, and URL.
    """
    cache_key = f"et_rss_{symbol}"
    cached = _news_cache_get(cache_key)
    if cached:
        return json.dumps(cached["data"], indent=2)

    symbol = symbol.upper().strip()
    news_articles = []

    try:
        rss_url = "https://economictimes.indiatimes.com/markets/stocks/rssfeeds/1977021502.cms"

        with httpx.Client(headers=HEADERS, timeout=30.0, follow_redirects=True) as client:
            response = client.get(rss_url)

            if response.status_code == 200:
                root = ET.fromstring(response.text)

                # RSS structure: <rss><channel><item>...</item></channel></rss>
                channel = root.find("channel")
                if channel is not None:
                    items = channel.findall("item")
                else:
                    items = root.findall(".//item")

                for item in items:
                    if len(news_articles) >= limit:
                        break

                    title_elem = item.find("title")
                    link_elem = item.find("link")
                    desc_elem = item.find("description")
                    pub_date_elem = item.find("pubDate")

                    title = title_elem.text if title_elem is not None and title_elem.text else ""
                    link = link_elem.text if link_elem is not None and link_elem.text else ""
                    description = desc_elem.text if desc_elem is not None and desc_elem.text else ""
                    pub_date = pub_date_elem.text if pub_date_elem is not None and pub_date_elem.text else ""

                    title = _clean_text(title)
                    description = _clean_text(description)

                    # Filter: only include items mentioning the symbol or company
                    search_text = (title + " " + description).lower()
                    symbol_lower = symbol.lower()
                    if symbol_lower not in search_text:
                        continue

                    news_articles.append({
                        "title": title,
                        "summary": description[:200] if description else "",
                        "url": link,
                        "published": _parse_rss_date(pub_date),
                        "source": "Economic Times RSS",
                    })

        result = {
            "symbol": symbol,
            "source": "Economic Times RSS",
            "articles_count": len(news_articles),
            "articles": news_articles[:limit],
            "fetched_at": datetime.now().isoformat(),
        }

        _news_cache_set(cache_key, result)
        return json.dumps(result, indent=2)

    except ET.ParseError as e:
        return json.dumps({
            "symbol": symbol,
            "source": "Economic Times RSS",
            "error": f"RSS parse error: {e}",
            "articles": [],
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "symbol": symbol,
            "source": "Economic Times RSS",
            "error": str(e),
            "articles": [],
        }, indent=2)


@tool("Scrape Economic Times News")
def scrape_economic_times_news(symbol: str, limit: int = 10) -> str:
    """
    Scrape latest news for a stock from Economic Times.

    Args:
        symbol: Stock symbol (e.g., 'RELIANCE', 'TCS')
        limit: Maximum number of news articles to fetch (default: 10)

    Returns:
        JSON string with list of news articles.
    """
    cache_key = f"et_news_{symbol}"
    cached = _news_cache_get(cache_key)
    if cached:
        return json.dumps(cached["data"], indent=2)

    symbol = symbol.upper().strip()
    news_articles = []

    try:
        # Search for the company
        search_term = symbol.lower()
        url = f"https://economictimes.indiatimes.com/topic/{search_term}"

        with httpx.Client(headers=HEADERS, timeout=30.0, follow_redirects=True) as client:
            response = client.get(url)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'lxml')

                # Find all articleshow links (ET's article URL pattern)
                seen_titles = set()
                article_links = soup.find_all('a', href=re.compile(r'articleshow'))

                for link_elem in article_links:
                    if len(news_articles) >= limit:
                        break
                    try:
                        title = _clean_text(link_elem.get_text())

                        # Skip short titles, duplicates, or non-article links
                        if not title or len(title) < 25 or title in seen_titles:
                            continue

                        # Skip common non-news items
                        skip_keywords = ['horoscope', 'weather', 'cricket', 'ipl', 'match']
                        if any(kw in title.lower() for kw in skip_keywords):
                            continue

                        seen_titles.add(title)

                        link = link_elem.get('href', '')
                        if link and not link.startswith('http'):
                            link = f"https://economictimes.indiatimes.com{link}"

                        # Try to get date from parent element
                        parent = link_elem.find_parent(['div', 'li', 'article'])
                        published = ""
                        if parent:
                            date_elem = parent.find('time') or parent.find('span', class_=re.compile(r'date|time'))
                            if date_elem:
                                published = _parse_relative_time(date_elem.get_text())

                        news_articles.append({
                            "title": title,
                            "summary": "",
                            "url": link,
                            "published": published,
                            "source": "Economic Times",
                        })

                    except Exception:
                        continue

        result = {
            "symbol": symbol,
            "source": "Economic Times",
            "articles_count": len(news_articles),
            "articles": news_articles[:limit],
            "fetched_at": datetime.now().isoformat(),
        }

        _news_cache_set(cache_key, result)
        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps({
            "symbol": symbol,
            "source": "Economic Times",
            "error": str(e),
            "articles": [],
        }, indent=2)


@tool("Scrape Google News")
def scrape_google_news(symbol: str, limit: int = 10) -> str:
    """
    Fetch latest stock news from Google News RSS feed.
    Searches for stock-specific news from Indian financial publications.

    Args:
        symbol: Stock symbol (e.g., 'RELIANCE', 'TCS')
        limit: Maximum number of news articles to fetch (default: 10)

    Returns:
        JSON string with list of news articles.
    """
    cache_key = f"google_news_{symbol}"
    cached = _news_cache_get(cache_key)
    if cached:
        return json.dumps(cached["data"], indent=2)

    symbol = symbol.upper().strip()
    news_articles = []

    try:
        # Google News RSS search for the stock symbol on NSE
        rss_url = f"https://news.google.com/rss/search?q={symbol}+NSE+stock&hl=en-IN&gl=IN&ceid=IN:en"

        with httpx.Client(headers=HEADERS, timeout=30.0, follow_redirects=True) as client:
            response = client.get(rss_url)

            if response.status_code == 200:
                root = ET.fromstring(response.text)

                channel = root.find("channel")
                if channel is not None:
                    items = channel.findall("item")
                else:
                    items = root.findall(".//item")

                for item in items:
                    if len(news_articles) >= limit:
                        break

                    title_elem = item.find("title")
                    link_elem = item.find("link")
                    pub_date_elem = item.find("pubDate")
                    source_elem = item.find("source")

                    title = title_elem.text if title_elem is not None and title_elem.text else ""
                    link = link_elem.text if link_elem is not None and link_elem.text else ""
                    pub_date = pub_date_elem.text if pub_date_elem is not None and pub_date_elem.text else ""
                    source_name = source_elem.text if source_elem is not None and source_elem.text else "Google News"

                    title = _clean_text(title)
                    if not title:
                        continue

                    news_articles.append({
                        "title": title,
                        "summary": "",
                        "url": link,
                        "published": _parse_rss_date(pub_date),
                        "source": f"Google News ({source_name})",
                    })

        result = {
            "symbol": symbol,
            "source": "Google News",
            "articles_count": len(news_articles),
            "articles": news_articles[:limit],
            "fetched_at": datetime.now().isoformat(),
        }

        _news_cache_set(cache_key, result)
        return json.dumps(result, indent=2)

    except ET.ParseError as e:
        return json.dumps({
            "symbol": symbol,
            "source": "Google News",
            "error": f"RSS parse error: {e}",
            "articles": [],
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "symbol": symbol,
            "source": "Google News",
            "error": str(e),
            "articles": [],
        }, indent=2)


@tool("Get Comprehensive Stock News")
def get_stock_news(symbol: str, limit_per_source: int = 5) -> str:
    """
    Get comprehensive news from multiple sources for a stock.
    Aggregates news from Economic Times RSS, Economic Times, and Google News.

    Args:
        symbol: Stock symbol (e.g., 'RELIANCE', 'TCS')
        limit_per_source: Number of articles to fetch per source (default: 5)

    Returns:
        JSON string with aggregated news from all sources, sorted by relevance.
    """
    symbol = symbol.upper().strip()
    all_articles = []
    sources_status = {}

    # Fetch from ET RSS
    try:
        et_rss_result = json.loads(scrape_et_rss_news.run(symbol, limit_per_source))
        if "articles" in et_rss_result:
            all_articles.extend(et_rss_result["articles"])
            sources_status["et_rss"] = "success"
        else:
            sources_status["et_rss"] = et_rss_result.get("error", "no articles")
    except Exception as e:
        sources_status["et_rss"] = str(e)

    # Fetch from Economic Times HTML
    try:
        et_result = json.loads(scrape_economic_times_news.run(symbol, limit_per_source))
        if "articles" in et_result:
            all_articles.extend(et_result["articles"])
            sources_status["economic_times"] = "success"
        else:
            sources_status["economic_times"] = et_result.get("error", "no articles")
    except Exception as e:
        sources_status["economic_times"] = str(e)

    # Fetch from Google News
    try:
        gn_result = json.loads(scrape_google_news.run(symbol, limit_per_source))
        if "articles" in gn_result:
            all_articles.extend(gn_result["articles"])
            sources_status["google_news"] = "success"
        else:
            sources_status["google_news"] = gn_result.get("error", "no articles")
    except Exception as e:
        sources_status["google_news"] = str(e)

    # Remove duplicates based on title similarity
    unique_articles = []
    seen_titles = set()
    for article in all_articles:
        title_key = article["title"].lower()[:50]
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_articles.append(article)

    # Sort by relevance (articles mentioning symbol first)
    def relevance_score(article):
        score = 0
        title_lower = article["title"].lower()
        if symbol.lower() in title_lower:
            score += 10
        if "buy" in title_lower or "sell" in title_lower:
            score += 5
        if "target" in title_lower or "rating" in title_lower:
            score += 3
        return -score  # Negative for descending sort

    unique_articles.sort(key=relevance_score)

    return json.dumps({
        "symbol": symbol,
        "total_articles": len(unique_articles),
        "sources_status": sources_status,
        "articles": unique_articles,
        "fetched_at": datetime.now().isoformat(),
    }, indent=2)


@tool("Get Market News Headlines")
def get_market_news_headlines(category: str = "stocks", limit: int = 15) -> str:
    """
    Get general market news headlines (not stock-specific) from Economic Times RSS.

    Args:
        category: News category - 'stocks', 'markets', 'economy', 'mutual-funds'
        limit: Maximum number of headlines (default: 15)

    Returns:
        JSON string with latest market headlines.
    """
    headlines = []

    try:
        rss_url = "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"

        with httpx.Client(headers=HEADERS, timeout=30.0, follow_redirects=True) as client:
            response = client.get(rss_url)

            if response.status_code == 200:
                root = ET.fromstring(response.text)

                channel = root.find("channel")
                if channel is not None:
                    items = channel.findall("item")
                else:
                    items = root.findall(".//item")

                for item in items:
                    if len(headlines) >= limit:
                        break

                    title_elem = item.find("title")
                    link_elem = item.find("link")
                    pub_date_elem = item.find("pubDate")

                    title = title_elem.text if title_elem is not None and title_elem.text else ""
                    link = link_elem.text if link_elem is not None and link_elem.text else ""
                    pub_date = pub_date_elem.text if pub_date_elem is not None and pub_date_elem.text else ""

                    title = _clean_text(title)
                    if not title or len(title) < 15:
                        continue

                    headlines.append({
                        "title": title,
                        "url": link,
                        "published": _parse_rss_date(pub_date),
                        "source": "Economic Times",
                    })

        return json.dumps({
            "category": category,
            "headlines_count": len(headlines),
            "headlines": headlines,
            "fetched_at": datetime.now().isoformat(),
        }, indent=2)

    except ET.ParseError as e:
        return json.dumps({
            "category": category,
            "error": f"RSS parse error: {e}",
            "headlines": [],
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "category": category,
            "error": str(e),
            "headlines": [],
        }, indent=2)
