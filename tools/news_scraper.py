"""
News Scraping Tools for Indian Stock Market
Scrapes news from Moneycontrol, Economic Times, Business Standard, and other sources
"""

import json
import re
from datetime import datetime, timedelta
from typing import Optional
import httpx
from bs4 import BeautifulSoup
from crewai.tools import tool
from tenacity import retry, stop_after_attempt, wait_exponential

# Common headers for web scraping
# Note: Removed 'br' (brotli) from Accept-Encoding as httpx may not have brotli support
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# News cache
_news_cache = {}
_cache_ttl = 600  # 10 minutes


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
    except:
        pass
    
    return time_str


@tool("Scrape Moneycontrol News")
def scrape_moneycontrol_news(symbol: str, limit: int = 10) -> str:
    """
    Scrape latest news for a stock from Moneycontrol.
    
    Args:
        symbol: Stock symbol (e.g., 'RELIANCE', 'TCS')
        limit: Maximum number of news articles to fetch (default: 10)
        
    Returns:
        JSON string with list of news articles including title, summary, date, and URL.
    """
    cache_key = f"mc_news_{symbol}"
    if cache_key in _news_cache:
        cached = _news_cache[cache_key]
        if (datetime.now().timestamp() - cached["timestamp"]) < _cache_ttl:
            return json.dumps(cached["data"], indent=2)
    
    symbol = symbol.upper().strip()
    
    # Map common symbols to Moneycontrol URLs
    symbol_mappings = {
        "RELIANCE": "reliance-industries",
        "TCS": "tata-consultancy-services",
        "INFY": "infosys",
        "HDFCBANK": "hdfc-bank",
        "ICICIBANK": "icici-bank",
        "HINDUNILVR": "hindustan-unilever",
        "ITC": "itc",
        "SBIN": "state-bank-of-india",
        "BHARTIARTL": "bharti-airtel",
        "KOTAKBANK": "kotak-mahindra-bank",
        "LT": "larsen-toubro",
        "AXISBANK": "axis-bank",
        "WIPRO": "wipro",
        "HCLTECH": "hcl-technologies",
        "TATAMOTORS": "tata-motors",
        "TATASTEEL": "tata-steel",
        "SUNPHARMA": "sun-pharmaceutical-industries",
        "MARUTI": "maruti-suzuki-india",
        "BAJFINANCE": "bajaj-finance",
        "ASIANPAINT": "asian-paints",
    }
    
    mc_symbol = symbol_mappings.get(symbol, symbol.lower().replace("&", "-and-"))
    
    news_articles = []
    
    try:
        # Try stock-specific news page
        url = f"https://www.moneycontrol.com/news/tags/{mc_symbol}.html"
        
        with httpx.Client(headers=HEADERS, timeout=30.0, follow_redirects=True) as client:
            response = client.get(url)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'lxml')
                
                # Find news articles in li.clearfix elements
                articles = soup.find_all('li', class_='clearfix')
                
                for article in articles:
                    if len(news_articles) >= limit:
                        break
                    try:
                        # Find links that contain /news/ in href (actual news links)
                        news_links = article.find_all('a', href=re.compile(r'/news/.*\.html'))
                        
                        for link_elem in news_links:
                            href = link_elem.get('href', '')
                            title = _clean_text(link_elem.get_text())
                            
                            # Skip short titles or non-news links
                            if not title or len(title) < 20:
                                continue
                            
                            # Make sure link is absolute
                            if href and not href.startswith('http'):
                                href = f"https://www.moneycontrol.com{href}"
                            
                            # Extract date/time
                            time_elem = article.find('span', class_='date') or article.find('span', class_='ago')
                            published = ""
                            if time_elem:
                                published = _parse_relative_time(time_elem.get_text())
                            
                            # Extract summary from paragraph
                            summary = ""
                            p_elem = article.find('p')
                            if p_elem:
                                summary = _clean_text(p_elem.get_text()[:200])
                            
                            news_articles.append({
                                "title": title,
                                "summary": summary,
                                "url": href,
                                "published": published,
                                "source": "Moneycontrol",
                            })
                            break  # Only take first valid news link per li
                    
                    except Exception:
                        continue
        
        # If no articles found, try general stock news
        if not news_articles:
            url = "https://www.moneycontrol.com/news/business/stocks/"
            
            with httpx.Client(headers=HEADERS, timeout=30.0, follow_redirects=True) as client:
                response = client.get(url)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'lxml')
                    articles = soup.find_all(['li', 'div'], class_=re.compile(r'clearfix|news'))
                    
                    for article in articles[:limit]:
                        try:
                            title_elem = article.find('a')
                            if not title_elem:
                                continue
                            
                            title = _clean_text(title_elem.get_text())
                            if symbol.lower() in title.lower() or len(news_articles) < 5:
                                link = title_elem.get('href', '')
                                if link and not link.startswith('http'):
                                    link = f"https://www.moneycontrol.com{link}"
                                
                                news_articles.append({
                                    "title": title,
                                    "summary": "",
                                    "url": link,
                                    "published": datetime.now().isoformat(),
                                    "source": "Moneycontrol",
                                })
                        except:
                            continue
        
        result = {
            "symbol": symbol,
            "source": "Moneycontrol",
            "articles_count": len(news_articles),
            "articles": news_articles[:limit],
            "fetched_at": datetime.now().isoformat(),
        }
        
        _news_cache[cache_key] = {"data": result, "timestamp": datetime.now().timestamp()}
        return json.dumps(result, indent=2)
    
    except Exception as e:
        return json.dumps({
            "symbol": symbol,
            "source": "Moneycontrol",
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
    if cache_key in _news_cache:
        cached = _news_cache[cache_key]
        if (datetime.now().timestamp() - cached["timestamp"]) < _cache_ttl:
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
        
        _news_cache[cache_key] = {"data": result, "timestamp": datetime.now().timestamp()}
        return json.dumps(result, indent=2)
    
    except Exception as e:
        return json.dumps({
            "symbol": symbol,
            "source": "Economic Times",
            "error": str(e),
            "articles": [],
        }, indent=2)


@tool("Scrape Business Standard News")
def scrape_business_standard_news(symbol: str, limit: int = 10) -> str:
    """
    Scrape latest news for a stock from Business Standard.
    
    Args:
        symbol: Stock symbol (e.g., 'RELIANCE', 'TCS')
        limit: Maximum number of news articles to fetch
        
    Returns:
        JSON string with list of news articles.
    """
    symbol = symbol.upper().strip()
    news_articles = []
    
    try:
        url = f"https://www.business-standard.com/search?q={symbol}"
        
        with httpx.Client(headers=HEADERS, timeout=30.0, follow_redirects=True) as client:
            response = client.get(url)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'lxml')
                
                articles = soup.find_all(['div', 'article'], class_=re.compile(r'listing|story|article'))
                
                for article in articles[:limit]:
                    try:
                        title_elem = article.find(['h2', 'h3', 'a'])
                        if not title_elem:
                            continue
                        
                        title = _clean_text(title_elem.get_text())
                        if not title or len(title) < 10:
                            continue
                        
                        link_elem = article.find('a')
                        link = link_elem.get('href', '') if link_elem else ''
                        if link and not link.startswith('http'):
                            link = f"https://www.business-standard.com{link}"
                        
                        news_articles.append({
                            "title": title,
                            "summary": "",
                            "url": link,
                            "published": datetime.now().isoformat(),
                            "source": "Business Standard",
                        })
                    
                    except Exception:
                        continue
        
        return json.dumps({
            "symbol": symbol,
            "source": "Business Standard",
            "articles_count": len(news_articles),
            "articles": news_articles[:limit],
            "fetched_at": datetime.now().isoformat(),
        }, indent=2)
    
    except Exception as e:
        return json.dumps({
            "symbol": symbol,
            "source": "Business Standard",
            "error": str(e),
            "articles": [],
        }, indent=2)


@tool("Get Comprehensive Stock News")
def get_stock_news(symbol: str, limit_per_source: int = 5) -> str:
    """
    Get comprehensive news from multiple sources for a stock.
    Aggregates news from Moneycontrol, Economic Times, and Business Standard.
    
    Args:
        symbol: Stock symbol (e.g., 'RELIANCE', 'TCS')
        limit_per_source: Number of articles to fetch per source (default: 5)
        
    Returns:
        JSON string with aggregated news from all sources, sorted by relevance.
    """
    symbol = symbol.upper().strip()
    all_articles = []
    sources_status = {}
    
    # Fetch from Moneycontrol
    try:
        mc_result = json.loads(scrape_moneycontrol_news.run(symbol, limit_per_source))
        if "articles" in mc_result:
            all_articles.extend(mc_result["articles"])
            sources_status["moneycontrol"] = "success"
        else:
            sources_status["moneycontrol"] = mc_result.get("error", "no articles")
    except Exception as e:
        sources_status["moneycontrol"] = str(e)
    
    # Fetch from Economic Times
    try:
        et_result = json.loads(scrape_economic_times_news.run(symbol, limit_per_source))
        if "articles" in et_result:
            all_articles.extend(et_result["articles"])
            sources_status["economic_times"] = "success"
        else:
            sources_status["economic_times"] = et_result.get("error", "no articles")
    except Exception as e:
        sources_status["economic_times"] = str(e)
    
    # Fetch from Business Standard
    try:
        bs_result = json.loads(scrape_business_standard_news.run(symbol, limit_per_source))
        if "articles" in bs_result:
            all_articles.extend(bs_result["articles"])
            sources_status["business_standard"] = "success"
        else:
            sources_status["business_standard"] = bs_result.get("error", "no articles")
    except Exception as e:
        sources_status["business_standard"] = str(e)
    
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
    Get general market news headlines (not stock-specific).
    
    Args:
        category: News category - 'stocks', 'markets', 'economy', 'mutual-funds'
        limit: Maximum number of headlines (default: 15)
        
    Returns:
        JSON string with latest market headlines.
    """
    headlines = []
    
    try:
        url = f"https://www.moneycontrol.com/news/business/{category}/"
        
        with httpx.Client(headers=HEADERS, timeout=30.0, follow_redirects=True) as client:
            response = client.get(url)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'lxml')
                
                # Find headline elements
                headline_elements = soup.find_all(['h2', 'h3'], class_=re.compile(r'title|headline'))
                
                for elem in headline_elements[:limit]:
                    try:
                        link = elem.find('a')
                        if link:
                            title = _clean_text(link.get_text())
                            url = link.get('href', '')
                            if url and not url.startswith('http'):
                                url = f"https://www.moneycontrol.com{url}"
                            
                            if title and len(title) > 15:
                                headlines.append({
                                    "title": title,
                                    "url": url,
                                    "source": "Moneycontrol",
                                })
                    except:
                        continue
        
        return json.dumps({
            "category": category,
            "headlines_count": len(headlines),
            "headlines": headlines,
            "fetched_at": datetime.now().isoformat(),
        }, indent=2)
    
    except Exception as e:
        return json.dumps({
            "category": category,
            "error": str(e),
            "headlines": [],
        }, indent=2)
