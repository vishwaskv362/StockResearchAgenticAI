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


def _get_nse_session() -> httpx.Client:
    """Create an httpx client with NSE session cookies.

    NSE requires a valid session cookie obtained by first visiting the homepage.
    """
    nse_headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nseindia.com/reports/fii-dii",
    }
    client = httpx.Client(headers=nse_headers, timeout=30.0, follow_redirects=True)
    # Visit homepage to get session cookies
    client.get("https://www.nseindia.com")
    return client


@tool("Get FII DII Data")
def get_fii_dii_data() -> str:
    """
    Get latest FII (Foreign Institutional Investors) and DII (Domestic Institutional Investors)
    activity data for Indian stock market from NSE India.

    Returns:
        JSON string with FII/DII buy/sell data in cash segment.
    """
    try:
        client = _get_nse_session()
        try:
            response = client.get("https://www.nseindia.com/api/fiidiiTradeReact")
        finally:
            client.close()

        if response.status_code != 200:
            return json.dumps({
                "error": f"NSE API returned status {response.status_code}",
                "suggestion": "Check https://www.nseindia.com/reports/fii-dii directly",
                "fetched_at": datetime.now().isoformat(),
            }, indent=2)

        api_data = response.json()

        fii_data = {"buy": 0.0, "sell": 0.0, "net": 0.0}
        dii_data = {"buy": 0.0, "sell": 0.0, "net": 0.0}
        data_date = datetime.now().strftime("%Y-%m-%d")

        for entry in api_data:
            category = entry.get("category", "").upper()
            if "FII" in category or "FPI" in category:
                fii_data["buy"] = float(entry.get("buyValue", 0))
                fii_data["sell"] = float(entry.get("sellValue", 0))
                fii_data["net"] = float(entry.get("netValue", fii_data["buy"] - fii_data["sell"]))
                if entry.get("date"):
                    data_date = entry["date"]
            elif "DII" in category:
                dii_data["buy"] = float(entry.get("buyValue", 0))
                dii_data["sell"] = float(entry.get("sellValue", 0))
                dii_data["net"] = float(entry.get("netValue", dii_data["buy"] - dii_data["sell"]))

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
            "date": data_date,
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
            "source": "NSE India",
            "fetched_at": datetime.now().isoformat(),
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "error": str(e),
            "DATA_UNAVAILABLE": True,
            "message": "FAILED to fetch FII/DII data. Do NOT guess institutional flow numbers.",
            "suggestion": "Check https://www.nseindia.com/reports/fii-dii directly",
            "fetched_at": datetime.now().isoformat(),
        }, indent=2)


@tool("Get Bulk Block Deals")
def get_bulk_block_deals(symbol: str = None) -> str:
    """
    Get recent bulk and block deals from NSE India.
    Bulk deals are large transactions (> 0.5% of equity) that must be disclosed.
    Block deals are large trades done through a separate trading window.

    Args:
        symbol: Optional stock symbol to filter deals. If None, returns all recent deals.

    Returns:
        JSON string with bulk and block deal information.
    """
    try:
        client = _get_nse_session()
        deals = []

        try:
            # NSE bulk deals API
            response = client.get("https://www.nseindia.com/api/snapshot-capital-market-largedeal")
        finally:
            client.close()

        if response.status_code == 200:
            api_data = response.json()
            # API returns {"BLOCK_DEALS_DATA": [...], "BULK_DEALS_DATA": [...]}
            for deal_type_key in ["BLOCK_DEALS_DATA", "BULK_DEALS_DATA"]:
                for entry in api_data.get(deal_type_key, []):
                    deal = {
                        "stock": entry.get("symbol", "N/A"),
                        "client": entry.get("clientName", "N/A"),
                        "deal_type": "Block" if "BLOCK" in deal_type_key else "Bulk",
                        "buy_sell": entry.get("buySell", "N/A"),
                        "quantity": entry.get("quantityTraded", "N/A"),
                        "price": entry.get("tradedPrice", "N/A"),
                    }

                    if symbol:
                        if symbol.upper() in deal["stock"].upper():
                            deals.append(deal)
                    else:
                        deals.append(deal)

        return json.dumps({
            "filter_symbol": symbol or "All Stocks",
            "deals_count": len(deals),
            "deals": deals[:15],
            "note": "No bulk/block deals found for this symbol today." if not deals else "",
            "source": "NSE India",
            "fetched_at": datetime.now().isoformat(),
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "error": str(e),
            "symbol": symbol,
            "deals_count": 0,
            "deals": [],
            "DATA_UNAVAILABLE": True,
            "message": "FAILED to fetch bulk/block deals. Do NOT fabricate deal data.",
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
        except Exception:
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
            "DATA_UNAVAILABLE": True,
            "message": f"FAILED to fetch promoter holdings for {symbol}. Do NOT guess shareholding data.",
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
            "DATA_UNAVAILABLE": True,
            "message": f"FAILED to fetch MF holdings for {symbol}. Do NOT guess holding data.",
        }, indent=2)
