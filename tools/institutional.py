"""
Institutional Activity Tools
Track FII/DII flows, bulk/block deals, and institutional holdings
"""

import json
import re
from datetime import datetime, timedelta
import httpx
from bs4 import BeautifulSoup
from crewai.tools import tool

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}


@tool("Get FII DII Data")
def get_fii_dii_data() -> str:
    """
    Get latest FII (Foreign Institutional Investors) and DII (Domestic Institutional Investors) 
    activity data for Indian stock market.
    
    Returns:
        JSON string with FII/DII buy/sell data for cash and derivatives segments.
    """
    try:
        # Try to scrape from Moneycontrol
        url = "https://www.moneycontrol.com/stocks/marketstats/fii_dii_activity/index.php"
        
        with httpx.Client(headers=HEADERS, timeout=30.0, follow_redirects=True) as client:
            response = client.get(url)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'lxml')
                
                # Find FII/DII tables
                tables = soup.find_all('table')
                
                fii_data = {"buy": 0, "sell": 0, "net": 0}
                dii_data = {"buy": 0, "sell": 0, "net": 0}
                
                for table in tables:
                    text = table.get_text().lower()
                    if 'fii' in text or 'foreign' in text:
                        # Try to extract numbers
                        numbers = re.findall(r'[\d,]+\.?\d*', table.get_text())
                        if len(numbers) >= 3:
                            try:
                                fii_data["buy"] = float(numbers[0].replace(',', ''))
                                fii_data["sell"] = float(numbers[1].replace(',', ''))
                                fii_data["net"] = fii_data["buy"] - fii_data["sell"]
                            except:
                                pass
                    
                    if 'dii' in text or 'domestic' in text:
                        numbers = re.findall(r'[\d,]+\.?\d*', table.get_text())
                        if len(numbers) >= 3:
                            try:
                                dii_data["buy"] = float(numbers[0].replace(',', ''))
                                dii_data["sell"] = float(numbers[1].replace(',', ''))
                                dii_data["net"] = dii_data["buy"] - dii_data["sell"]
                            except:
                                pass
                
                # Determine market sentiment
                total_net = fii_data["net"] + dii_data["net"]
                if total_net > 500:
                    sentiment = "Strong Bullish (Heavy Buying)"
                elif total_net > 0:
                    sentiment = "Mildly Bullish"
                elif total_net > -500:
                    sentiment = "Mildly Bearish"
                else:
                    sentiment = "Strong Bearish (Heavy Selling)"
                
                return json.dumps({
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "fii": {
                        "buy_value_cr": fii_data["buy"],
                        "sell_value_cr": fii_data["sell"],
                        "net_value_cr": fii_data["net"],
                        "activity": "Net Buyer" if fii_data["net"] > 0 else "Net Seller",
                    },
                    "dii": {
                        "buy_value_cr": dii_data["buy"],
                        "sell_value_cr": dii_data["sell"],
                        "net_value_cr": dii_data["net"],
                        "activity": "Net Buyer" if dii_data["net"] > 0 else "Net Seller",
                    },
                    "combined": {
                        "total_net_cr": total_net,
                        "market_sentiment": sentiment,
                    },
                    "note": "Values in Indian Rupees Crores. Positive net = buying, Negative = selling.",
                    "source": "Market Data",
                    "fetched_at": datetime.now().isoformat(),
                }, indent=2)
        
        # Return sample data if scraping fails
        return json.dumps({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "fii": {
                "note": "Unable to fetch live data. Please check NSE/BSE websites for latest FII/DII data.",
                "typical_range": "FII daily activity ranges from -5000 Cr to +5000 Cr",
            },
            "dii": {
                "note": "DII typically acts as counterbalance to FII activity",
            },
            "where_to_check": [
                "https://www.nseindia.com/reports/fii-dii",
                "https://www.moneycontrol.com/stocks/marketstats/fii_dii_activity/",
            ],
            "fetched_at": datetime.now().isoformat(),
        }, indent=2)
    
    except Exception as e:
        return json.dumps({
            "error": str(e),
            "suggestion": "Check NSE/BSE websites directly for FII/DII data",
        }, indent=2)


@tool("Get Bulk Block Deals")
def get_bulk_block_deals(symbol: str = None) -> str:
    """
    Get recent bulk and block deals from NSE/BSE.
    Bulk deals are large transactions (> 0.5% of equity) that must be disclosed.
    Block deals are large trades done through a separate trading window.
    
    Args:
        symbol: Optional stock symbol to filter deals. If None, returns all recent deals.
        
    Returns:
        JSON string with bulk and block deal information.
    """
    try:
        # Try to scrape bulk deals data
        url = "https://www.moneycontrol.com/stocks/marketstats/bulk-deals/"
        
        deals = []
        
        with httpx.Client(headers=HEADERS, timeout=30.0, follow_redirects=True) as client:
            response = client.get(url)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'lxml')
                
                # Find deal tables
                tables = soup.find_all('table')
                
                for table in tables:
                    rows = table.find_all('tr')[1:]  # Skip header
                    
                    for row in rows[:20]:  # Limit to 20 deals
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 4:
                            deal = {
                                "stock": cells[0].get_text().strip(),
                                "client": cells[1].get_text().strip() if len(cells) > 1 else "N/A",
                                "deal_type": cells[2].get_text().strip() if len(cells) > 2 else "N/A",
                                "quantity": cells[3].get_text().strip() if len(cells) > 3 else "N/A",
                                "price": cells[4].get_text().strip() if len(cells) > 4 else "N/A",
                            }
                            
                            # Filter by symbol if provided
                            if symbol:
                                if symbol.upper() in deal["stock"].upper():
                                    deals.append(deal)
                            else:
                                deals.append(deal)
        
        if not deals:
            # Provide helpful information even if scraping fails
            deals = [{
                "note": "No deals found or unable to fetch live data",
                "what_to_look_for": [
                    "Large investors (FIIs, DIIs, HNIs) buying/selling",
                    "Promoter transactions",
                    "Private equity exits",
                    "Strategic investments",
                ],
                "significance": [
                    "Bulk deals indicate strong institutional interest",
                    "Multiple buy deals = bullish signal",
                    "Promoter buying = positive sign",
                    "Large selling by promoters = red flag",
                ],
            }]
        
        return json.dumps({
            "filter_symbol": symbol or "All Stocks",
            "deals_count": len(deals),
            "deals": deals[:15],  # Return max 15 deals
            "interpretation": {
                "bulk_deal": "Transaction > 0.5% of company's equity, must be disclosed same day",
                "block_deal": "Minimum 5 Lakh shares or Rs 10 Cr transaction, done in special window",
                "significance": "Large institutional transactions indicate strong conviction",
            },
            "where_to_check": [
                "https://www.nseindia.com/market-data/bulk-deals",
                "https://www.bseindia.com/markets/equity/EQReports/BulknBlockDeals.aspx",
            ],
            "fetched_at": datetime.now().isoformat(),
        }, indent=2)
    
    except Exception as e:
        return json.dumps({
            "error": str(e),
            "symbol": symbol,
            "suggestion": "Check NSE/BSE websites for latest bulk/block deal data",
        }, indent=2)


@tool("Get Promoter Holdings")
def get_promoter_holdings(symbol: str) -> str:
    """
    Get promoter and public shareholding pattern for a stock.
    
    Args:
        symbol: Stock symbol (e.g., 'RELIANCE', 'TCS')
        
    Returns:
        JSON string with shareholding pattern breakdown.
    """
    try:
        import yfinance as yf
        
        nse_symbol = f"{symbol.upper()}.NS"
        ticker = yf.Ticker(nse_symbol)
        
        # Get major holders
        try:
            holders = ticker.major_holders
            institutional_holders = ticker.institutional_holders
        except:
            holders = None
            institutional_holders = None
        
        result = {
            "symbol": symbol.upper(),
            "note": "Shareholding data from available sources",
        }
        
        if holders is not None and not holders.empty:
            result["major_holders"] = holders.to_dict()
        
        if institutional_holders is not None and not institutional_holders.empty:
            # Convert to list of dicts for JSON serialization
            inst_list = []
            for _, row in institutional_holders.head(10).iterrows():
                inst_list.append({
                    "holder": str(row.get('Holder', 'N/A')),
                    "shares": int(row.get('Shares', 0)) if row.get('Shares') else 0,
                    "value": float(row.get('Value', 0)) if row.get('Value') else 0,
                })
            result["top_institutional_holders"] = inst_list
        
        # Add interpretation
        result["interpretation"] = {
            "promoter_holding": "Higher promoter holding (>50%) indicates confidence in company",
            "fii_holding": "FII interest shows international investor confidence",
            "dii_holding": "DII holding provides stability during market volatility",
            "changes_to_watch": [
                "Decreasing promoter holding = potential red flag",
                "Increasing FII holding = positive sentiment",
                "Pledge of promoter shares = risk indicator",
            ],
        }
        
        result["where_to_check"] = [
            f"https://www.screener.in/company/{symbol}/",
            "https://www.nseindia.com/companies-listing/corporate-filings-shareholding-pattern",
        ]
        
        result["fetched_at"] = datetime.now().isoformat()
        
        return json.dumps(result, indent=2)
    
    except Exception as e:
        return json.dumps({
            "error": str(e),
            "symbol": symbol,
            "suggestion": "Check Screener.in or company's BSE/NSE page for shareholding pattern",
        }, indent=2)


@tool("Get Mutual Fund Holdings")
def get_mutual_fund_holdings(symbol: str) -> str:
    """
    Get mutual fund holdings information for a stock.
    Shows which mutual funds hold this stock and their holding patterns.
    
    Args:
        symbol: Stock symbol (e.g., 'RELIANCE', 'TCS')
        
    Returns:
        JSON string with mutual fund holding information.
    """
    try:
        url = f"https://www.screener.in/company/{symbol.upper()}/"
        
        with httpx.Client(headers=HEADERS, timeout=30.0, follow_redirects=True) as client:
            response = client.get(url)
            
            mf_info = {
                "symbol": symbol.upper(),
                "note": "Mutual fund holdings summary",
            }
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'lxml')
                
                # Try to find shareholding section
                shareholding_section = soup.find('section', id='shareholding')
                
                if shareholding_section:
                    # Extract MF holding percentage
                    text = shareholding_section.get_text()
                    mf_match = re.search(r'MF[:\s]+(\d+\.?\d*)%', text, re.IGNORECASE)
                    if mf_match:
                        mf_info["mf_holding_percent"] = float(mf_match.group(1))
            
            mf_info["interpretation"] = {
                "high_mf_holding": "> 15% MF holding indicates institutional confidence",
                "increasing_trend": "Rising MF holding is bullish signal",
                "top_schemes": "Check AMFI website for which schemes hold this stock",
            }
            
            mf_info["where_to_check"] = [
                f"https://www.screener.in/company/{symbol}/",
                "https://www.amfiindia.com/",
                f"https://www.tickertape.in/stocks/{symbol.lower()}",
            ]
            
            mf_info["fetched_at"] = datetime.now().isoformat()
            
            return json.dumps(mf_info, indent=2)
    
    except Exception as e:
        return json.dumps({
            "error": str(e),
            "symbol": symbol,
            "suggestion": "Check Screener.in or AMFI website for mutual fund holdings",
        }, indent=2)
