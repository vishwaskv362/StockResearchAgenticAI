"""
Streamlit Web UI for Stock Research Assistant
Beautiful dashboard for Indian stock market analysis
"""

import streamlit as st
import json
from datetime import datetime
import pandas as pd

# Must be first Streamlit command
st.set_page_config(
    page_title="Stock Research Assistant 🇮🇳",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Import tools after streamlit config
from tools.market_data import get_stock_price, get_stock_info, get_historical_data, get_index_data
from tools.news_scraper import get_stock_news
from tools.analysis import calculate_technical_indicators, get_fundamental_metrics, analyze_price_action
from tools.institutional import get_fii_dii_data, get_bulk_block_deals
from config import NIFTY50_STOCKS, SECTORS


# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #FF9933, #FFFFFF, #138808);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
    }
    .positive { color: #00C851; font-weight: bold; }
    .negative { color: #ff4444; font-weight: bold; }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)


def format_number(num):
    """Format number in Indian style (lakhs, crores)."""
    if num is None or num == "N/A":
        return "N/A"
    try:
        num = float(num)
        if num >= 10_000_000:
            return f"₹{num/10_000_000:.2f} Cr"
        elif num >= 100_000:
            return f"₹{num/100_000:.2f} L"
        else:
            return f"₹{num:,.2f}"
    except:
        return str(num)


def get_trend_emoji(change):
    """Get emoji based on price change."""
    if change > 0:
        return "🟢"
    elif change < 0:
        return "🔴"
    return "⚪"


def render_header():
    """Render the main header."""
    st.markdown('<h1 class="main-header">🇮🇳 Stock Research Assistant</h1>', unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>AI-Powered Research for Indian Markets (NSE/BSE)</p>", unsafe_allow_html=True)
    st.divider()


def render_sidebar():
    """Render sidebar with stock selection."""
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/en/thumb/4/41/Flag_of_India.svg/1200px-Flag_of_India.svg.png", width=50)
        st.title("📊 Navigation")
        
        # Stock input
        st.subheader("🔍 Search Stock")
        symbol = st.text_input(
            "Enter Stock Symbol",
            placeholder="e.g., RELIANCE, TCS, INFY",
            help="Enter NSE stock symbol"
        ).upper().strip()
        
        # Quick select
        st.subheader("⚡ Quick Select")
        selected_stock = st.selectbox(
            "Popular Stocks",
            [""] + NIFTY50_STOCKS[:20],
            format_func=lambda x: "Select a stock..." if x == "" else x
        )
        
        if selected_stock:
            symbol = selected_stock
        
        # Sector filter
        st.subheader("🏭 Browse by Sector")
        selected_sector = st.selectbox(
            "Sector",
            [""] + list(SECTORS.keys()),
            format_func=lambda x: "All Sectors" if x == "" else x
        )
        
        if selected_sector:
            sector_stocks = SECTORS.get(selected_sector, [])
            sector_stock = st.selectbox("Stocks", [""] + sector_stocks)
            if sector_stock:
                symbol = sector_stock
        
        st.divider()
        
        # Market status
        now = datetime.now()
        hour = now.hour
        if now.weekday() >= 5:
            status = "🔴 Market Closed (Weekend)"
        elif hour < 9 or (hour == 9 and now.minute < 15):
            status = "🟡 Pre-Market"
        elif hour < 15 or (hour == 15 and now.minute <= 30):
            status = "🟢 Market Open"
        else:
            status = "🔴 Market Closed"
        
        st.markdown(f"**Market Status:** {status}")
        st.markdown(f"**Last Updated:** {now.strftime('%H:%M:%S IST')}")
        
        st.divider()
        st.caption("⚠️ For educational purposes only. Not financial advice.")
        
        return symbol


def render_market_overview():
    """Render market overview section."""
    st.subheader("🏦 Market Overview")
    
    try:
        indices_data = json.loads(get_index_data.run("ALL"))
        
        col1, col2, col3, col4 = st.columns(4)
        
        index_cols = [
            ("NIFTY50", "NIFTY 50", col1),
            ("SENSEX", "SENSEX", col2),
            ("BANKNIFTY", "BANK NIFTY", col3),
            ("NIFTYIT", "NIFTY IT", col4),
        ]
        
        for key, name, col in index_cols:
            if key in indices_data:
                data = indices_data[key]
                value = data.get("value", 0)
                change = data.get("change", 0)
                change_pct = data.get("change_percent", 0)
                
                with col:
                    st.metric(
                        label=name,
                        value=f"{value:,.2f}",
                        delta=f"{change:+,.2f} ({change_pct:+.2f}%)"
                    )
    except Exception as e:
        st.warning(f"Could not fetch market data: {e}")


def render_stock_overview(symbol: str):
    """Render stock overview."""
    try:
        with st.spinner(f"Fetching data for {symbol}..."):
            price_data = json.loads(get_stock_price.run(symbol))
            info_data = json.loads(get_stock_info.run(symbol))
        
        if "error" in price_data:
            st.error(f"❌ Stock not found: {symbol}")
            return None
        
        # Header with stock info
        change = price_data.get("change", 0)
        change_pct = price_data.get("change_percent", 0)
        trend = get_trend_emoji(change)
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown(f"## {trend} {symbol}")
            st.markdown(f"**{info_data.get('company_name', 'N/A')}**")
            st.caption(f"{info_data.get('sector', 'N/A')} | {info_data.get('industry', 'N/A')}")
        
        with col2:
            st.metric(
                "Current Price",
                f"₹{price_data.get('current_price', 0):,.2f}",
                delta=f"{change:+.2f} ({change_pct:+.2f}%)"
            )
        
        with col3:
            st.metric("Volume", f"{price_data.get('volume', 0):,}")
            st.caption(f"Avg: {price_data.get('avg_volume', 'N/A'):,}" if isinstance(price_data.get('avg_volume'), int) else "")
        
        # Key metrics row
        st.divider()
        
        m1, m2, m3, m4, m5 = st.columns(5)
        
        with m1:
            st.metric("Day High", f"₹{price_data.get('high', 0):,.2f}")
        with m2:
            st.metric("Day Low", f"₹{price_data.get('low', 0):,.2f}")
        with m3:
            st.metric("52W High", f"₹{price_data.get('52_week_high', 'N/A')}")
        with m4:
            st.metric("52W Low", f"₹{price_data.get('52_week_low', 'N/A')}")
        with m5:
            st.metric("Market Cap", info_data.get('market_cap_category', 'N/A'))
        
        return price_data, info_data
    
    except Exception as e:
        st.error(f"Error fetching stock data: {e}")
        return None


def render_technical_analysis(symbol: str):
    """Render technical analysis tab."""
    try:
        with st.spinner("Calculating technical indicators..."):
            tech_data = json.loads(calculate_technical_indicators.run(symbol))
        
        if "error" in tech_data:
            st.error(tech_data["error"])
            return
        
        # Overall signal
        signal = tech_data.get("overall_signal", "NEUTRAL")
        signal_colors = {"BULLISH": "green", "BEARISH": "red", "NEUTRAL": "orange"}
        signal_emoji = {"BULLISH": "🟢", "BEARISH": "🔴", "NEUTRAL": "🟡"}
        
        st.markdown(f"### {signal_emoji.get(signal, '⚪')} Overall Signal: **:{signal_colors.get(signal, 'gray')}[{signal}]**")
        st.caption(f"Signal Strength: {tech_data.get('signal_strength', 'N/A')}")
        
        st.divider()
        
        # Indicators in columns
        col1, col2, col3 = st.columns(3)
        
        ma = tech_data.get("moving_averages", {})
        momentum = tech_data.get("momentum", {})
        volatility = tech_data.get("volatility", {})
        
        with col1:
            st.markdown("#### 📈 Moving Averages")
            st.markdown(f"""
            | Indicator | Value |
            |-----------|-------|
            | SMA 20 | ₹{ma.get('sma_20', 'N/A')} |
            | SMA 50 | ₹{ma.get('sma_50', 'N/A')} |
            | SMA 200 | ₹{ma.get('sma_200', 'N/A')} |
            | vs SMA20 | {ma.get('price_vs_sma20', 'N/A')} |
            | vs SMA50 | {ma.get('price_vs_sma50', 'N/A')} |
            """)
        
        with col2:
            st.markdown("#### 📊 Momentum")
            rsi = momentum.get('rsi_14', 0)
            rsi_color = "red" if rsi > 70 else ("green" if rsi < 30 else "gray")
            st.markdown(f"""
            | Indicator | Value |
            |-----------|-------|
            | RSI (14) | :{rsi_color}[{rsi}] |
            | Interpretation | {momentum.get('rsi_interpretation', 'N/A')} |
            | MACD Line | {momentum.get('macd_line', 'N/A')} |
            | MACD Signal | {momentum.get('macd_signal', 'N/A')} |
            | ROC (10d) | {momentum.get('roc_10_day', 'N/A')}% |
            """)
        
        with col3:
            st.markdown("#### 📉 Volatility")
            st.markdown(f"""
            | Indicator | Value |
            |-----------|-------|
            | BB Upper | ₹{volatility.get('bollinger_upper', 'N/A')} |
            | BB Middle | ₹{volatility.get('bollinger_middle', 'N/A')} |
            | BB Lower | ₹{volatility.get('bollinger_lower', 'N/A')} |
            | BB Position | {volatility.get('bb_position', 'N/A')} |
            | ATR % | {volatility.get('atr_percent', 'N/A')} |
            """)
        
        st.divider()
        
        # Support/Resistance and Trend
        col1, col2 = st.columns(2)
        
        sr = tech_data.get("support_resistance", {})
        trend = tech_data.get("trend", {})
        
        with col1:
            st.markdown("#### 🎯 Support & Resistance")
            st.markdown(f"""
            | Level | Price |
            |-------|-------|
            | Resistance 2 | ₹{sr.get('resistance_2', 'N/A')} |
            | Resistance 1 | ₹{sr.get('resistance_1', 'N/A')} |
            | **Pivot** | **₹{sr.get('pivot', 'N/A')}** |
            | Support 1 | ₹{sr.get('support_1', 'N/A')} |
            | Support 2 | ₹{sr.get('support_2', 'N/A')} |
            """)
        
        with col2:
            st.markdown("#### 📈 Trend Analysis")
            
            def trend_badge(t):
                if t == "Bullish":
                    return "🟢 Bullish"
                elif t == "Bearish":
                    return "🔴 Bearish"
                return "⚪ N/A"
            
            st.markdown(f"""
            | Timeframe | Trend |
            |-----------|-------|
            | Short-term | {trend_badge(trend.get('short_term', 'N/A'))} |
            | Medium-term | {trend_badge(trend.get('medium_term', 'N/A'))} |
            | Long-term | {trend_badge(trend.get('long_term', 'N/A'))} |
            """)
            
            gc = trend.get('golden_cross')
            if gc is True:
                st.success("✨ Golden Cross Active (Bullish)")
            elif gc is False:
                st.warning("💀 Death Cross Active (Bearish)")
        
        # Trading Signals
        st.divider()
        st.markdown("#### ⚡ Active Signals")
        
        signals = tech_data.get("signals", [])
        if signals:
            for sig in signals:
                indicator = sig.get("indicator", "")
                signal_text = sig.get("signal", "")
                strength = sig.get("strength", "")
                
                if "Buy" in signal_text or "Bullish" in signal_text:
                    st.success(f"**{indicator}:** {signal_text} ({strength})")
                elif "Sell" in signal_text or "Bearish" in signal_text:
                    st.error(f"**{indicator}:** {signal_text} ({strength})")
                else:
                    st.info(f"**{indicator}:** {signal_text} ({strength})")
        else:
            st.info("No strong signals at the moment")
    
    except Exception as e:
        st.error(f"Error in technical analysis: {e}")


def render_fundamental_analysis(symbol: str):
    """Render fundamental analysis tab."""
    try:
        with st.spinner("Fetching fundamental metrics..."):
            fund_data = json.loads(get_fundamental_metrics.run(symbol))
        
        if "error" in fund_data:
            st.error(fund_data["error"])
            return
        
        # Rating header
        rating = fund_data.get("overall_rating", "N/A")
        rating_colors = {
            "STRONG BUY": "green",
            "BUY": "green", 
            "HOLD": "orange",
            "SELL": "red",
            "STRONG SELL": "red",
        }
        rating_emojis = {
            "STRONG BUY": "🟢🟢",
            "BUY": "🟢",
            "HOLD": "🟡",
            "SELL": "🔴",
            "STRONG SELL": "🔴🔴",
        }
        
        st.markdown(f"### {rating_emojis.get(rating, '⚪')} Fundamental Rating: **:{rating_colors.get(rating, 'gray')}[{rating}]**")
        st.caption(f"Score: {fund_data.get('score', 'N/A')} | Rating: {fund_data.get('rating_percentage', 'N/A')}")
        
        st.divider()
        
        # Metrics in columns
        col1, col2, col3 = st.columns(3)
        
        val = fund_data.get("valuation", {})
        prof = fund_data.get("profitability", {})
        health = fund_data.get("financial_health", {})
        
        with col1:
            st.markdown("#### 💰 Valuation")
            st.markdown(f"""
            | Metric | Value |
            |--------|-------|
            | P/E Ratio | {val.get('pe_ratio', 'N/A')} |
            | Forward P/E | {val.get('forward_pe', 'N/A')} |
            | P/B Ratio | {val.get('pb_ratio', 'N/A')} |
            | P/S Ratio | {val.get('ps_ratio', 'N/A')} |
            | EV/EBITDA | {val.get('ev_ebitda', 'N/A')} |
            | PEG Ratio | {val.get('peg_ratio', 'N/A')} |
            """)
        
        with col2:
            st.markdown("#### 📈 Profitability")
            st.markdown(f"""
            | Metric | Value |
            |--------|-------|
            | ROE | {prof.get('roe', 'N/A')} |
            | ROA | {prof.get('roa', 'N/A')} |
            | Profit Margin | {prof.get('profit_margin', 'N/A')} |
            | Operating Margin | {prof.get('operating_margin', 'N/A')} |
            | Gross Margin | {prof.get('gross_margin', 'N/A')} |
            """)
        
        with col3:
            st.markdown("#### 🏦 Financial Health")
            debt_status = health.get('debt_status', 'N/A')
            debt_color = "green" if debt_status == "Low" else ("orange" if debt_status == "Moderate" else "red")
            st.markdown(f"""
            | Metric | Value |
            |--------|-------|
            | Debt/Equity | {health.get('debt_to_equity', 'N/A')} |
            | Current Ratio | {health.get('current_ratio', 'N/A')} |
            | Quick Ratio | {health.get('quick_ratio', 'N/A')} |
            | Debt Status | :{debt_color}[{debt_status}] |
            """)
        
        st.divider()
        
        # Growth and Dividends
        col1, col2, col3 = st.columns(3)
        
        growth = fund_data.get("growth", {})
        div = fund_data.get("dividends", {})
        size = fund_data.get("size", {})
        
        with col1:
            st.markdown("#### 📊 Growth")
            st.markdown(f"""
            | Metric | Value |
            |--------|-------|
            | Earnings Growth | {growth.get('earnings_growth', 'N/A')} |
            | Revenue Growth | {growth.get('revenue_growth', 'N/A')} |
            | Quarterly EPS Growth | {growth.get('quarterly_earnings_growth', 'N/A')} |
            """)
        
        with col2:
            st.markdown("#### 💵 Dividends")
            st.markdown(f"""
            | Metric | Value |
            |--------|-------|
            | Dividend Yield | {div.get('dividend_yield', 'N/A')} |
            | Dividend Rate | {div.get('dividend_rate', 'N/A')} |
            | Payout Ratio | {div.get('payout_ratio', 'N/A')} |
            """)
        
        with col3:
            st.markdown("#### 📏 Company Size")
            st.markdown(f"""
            | Metric | Value |
            |--------|-------|
            | Market Cap | {size.get('market_cap', 'N/A')} |
            | Enterprise Value | {size.get('enterprise_value', 'N/A')} |
            | Revenue | {size.get('revenue', 'N/A')} |
            | EBITDA | {size.get('ebitda', 'N/A')} |
            """)
        
        # Assessment
        assessment = fund_data.get("assessment", [])
        if assessment:
            st.divider()
            st.markdown("#### 📋 Key Observations")
            for item in assessment:
                metric = item.get("metric", "")
                assess = item.get("assessment", "")
                impact = item.get("impact", "")
                
                if impact == "Positive":
                    st.success(f"✅ **{metric}:** {assess}")
                elif impact == "Negative":
                    st.error(f"❌ **{metric}:** {assess}")
                else:
                    st.info(f"ℹ️ **{metric}:** {assess}")
    
    except Exception as e:
        st.error(f"Error in fundamental analysis: {e}")


def render_news(symbol: str):
    """Render news tab."""
    try:
        with st.spinner("Fetching latest news..."):
            news_data = json.loads(get_stock_news.run(symbol, 5))
        
        articles = news_data.get("articles", [])
        sources_status = news_data.get("sources_status", {})
        
        # Source status
        st.markdown("#### 📰 News Sources")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if sources_status.get("moneycontrol") == "success":
                st.success("✅ Moneycontrol")
            else:
                st.warning("⚠️ Moneycontrol")
        
        with col2:
            if sources_status.get("economic_times") == "success":
                st.success("✅ Economic Times")
            else:
                st.warning("⚠️ Economic Times")
        
        with col3:
            if sources_status.get("business_standard") == "success":
                st.success("✅ Business Standard")
            else:
                st.warning("⚠️ Business Standard")
        
        st.divider()
        
        if not articles:
            st.info(f"No recent news found for {symbol}")
            return
        
        st.markdown(f"#### 📰 Latest News ({len(articles)} articles)")
        
        for i, article in enumerate(articles, 1):
            title = article.get("title", "No title")
            source = article.get("source", "Unknown")
            url = article.get("url", "")
            published = article.get("published", "")
            summary = article.get("summary", "")
            
            with st.expander(f"**{i}. {title}**", expanded=i<=3):
                st.caption(f"Source: {source} | {published}")
                if summary:
                    st.write(summary)
                if url:
                    st.markdown(f"[Read full article →]({url})")
    
    except Exception as e:
        st.error(f"Error fetching news: {e}")


def render_institutional(symbol: str):
    """Render institutional activity tab."""
    try:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🏦 FII/DII Activity")
            with st.spinner("Fetching FII/DII data..."):
                fii_data = json.loads(get_fii_dii_data.run())
            
            if "error" not in fii_data:
                fii = fii_data.get("fii", {})
                dii = fii_data.get("dii", {})
                combined = fii_data.get("combined", {})
                
                if fii.get("buy_value_cr"):
                    st.markdown(f"""
                    **FII Activity:**
                    - Buy: ₹{fii.get('buy_value_cr', 0):,.0f} Cr
                    - Sell: ₹{fii.get('sell_value_cr', 0):,.0f} Cr
                    - Net: ₹{fii.get('net_value_cr', 0):,.0f} Cr ({fii.get('activity', 'N/A')})
                    
                    **DII Activity:**
                    - Buy: ₹{dii.get('buy_value_cr', 0):,.0f} Cr
                    - Sell: ₹{dii.get('sell_value_cr', 0):,.0f} Cr
                    - Net: ₹{dii.get('net_value_cr', 0):,.0f} Cr ({dii.get('activity', 'N/A')})
                    
                    **Market Sentiment:** {combined.get('market_sentiment', 'N/A')}
                    """)
                else:
                    st.info("Check NSE/BSE websites for latest FII/DII data")
            else:
                st.warning("Could not fetch FII/DII data")
        
        with col2:
            st.markdown(f"#### 📊 Bulk/Block Deals for {symbol}")
            with st.spinner("Fetching deals..."):
                deals_data = json.loads(get_bulk_block_deals.run(symbol))
            
            deals = deals_data.get("deals", [])
            
            if deals and not isinstance(deals[0], dict) or "note" not in deals[0]:
                for deal in deals[:5]:
                    st.markdown(f"""
                    - **{deal.get('stock', 'N/A')}**: {deal.get('deal_type', 'N/A')}
                      - Client: {deal.get('client', 'N/A')}
                      - Qty: {deal.get('quantity', 'N/A')}
                      - Price: {deal.get('price', 'N/A')}
                    """)
            else:
                st.info(f"No recent bulk/block deals for {symbol}")
                st.markdown("""
                **What to look for:**
                - Large investor activity (FIIs, DIIs, HNIs)
                - Promoter transactions
                - Private equity exits
                """)
    
    except Exception as e:
        st.error(f"Error: {e}")


def render_ai_analysis(symbol: str):
    """Render AI analysis tab."""
    st.markdown("#### 🤖 AI-Powered Full Analysis")
    
    st.info("""
    **Full AI Analysis** uses 6 specialized AI agents to create a comprehensive research report:
    
    1. 📊 **Market Data Analyst** - Collects all market data
    2. 📰 **News Analyst** - Analyzes news sentiment
    3. 💰 **Fundamental Analyst** - Deep financial analysis
    4. 📈 **Technical Analyst** - Chart patterns & indicators
    5. 🎯 **Investment Strategist** - Synthesizes recommendations
    6. 📝 **Report Writer** - Creates the final report
    
    **Requirements:**
    - Mistral AI API key in your `.env` file
    - Takes 2-3 minutes to complete
    """)
    
    if st.button(f"🚀 Run Full AI Analysis for {symbol}", type="primary", use_container_width=True):
        try:
            from config import settings
            if not settings.mistral_api_key:
                st.error("❌ Mistral API key not configured. Please add MISTRAL_API_KEY to your .env file.")
                return
            
            from crews.research_crew import analyze_stock_sync
            
            with st.spinner(f"🔬 AI agents analyzing {symbol}... This may take 2-3 minutes."):
                report = analyze_stock_sync(symbol, "full")
            
            st.success("✅ Analysis complete!")
            st.divider()
            st.markdown(report)
            
        except Exception as e:
            st.error(f"Error during AI analysis: {e}")


def main():
    """Main application."""
    render_header()
    
    # Sidebar and get selected symbol
    symbol = render_sidebar()
    
    # Market overview at top
    render_market_overview()
    
    st.divider()
    
    # Main content
    if symbol:
        result = render_stock_overview(symbol)
        
        if result:
            st.divider()
            
            # Tabs for different analyses
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "📈 Technical",
                "💰 Fundamentals", 
                "📰 News",
                "🏦 Institutional",
                "🤖 AI Analysis"
            ])
            
            with tab1:
                render_technical_analysis(symbol)
            
            with tab2:
                render_fundamental_analysis(symbol)
            
            with tab3:
                render_news(symbol)
            
            with tab4:
                render_institutional(symbol)
            
            with tab5:
                render_ai_analysis(symbol)
    else:
        # Landing page when no stock selected
        st.markdown("""
        ### 👋 Welcome to Stock Research Assistant!
        
        **Get started:**
        1. Enter a stock symbol in the sidebar (e.g., `RELIANCE`, `TCS`, `INFY`)
        2. Or select from popular stocks dropdown
        3. Explore Technical, Fundamental, and News analysis
        
        **Features:**
        - 📊 Real-time price data from NSE/BSE
        - 📈 Technical indicators (RSI, MACD, Bollinger Bands)
        - 💰 Fundamental metrics (P/E, ROE, Debt analysis)
        - 📰 News from Moneycontrol, Economic Times, Business Standard
        - 🏦 FII/DII activity tracking
        - 🤖 Full AI-powered research reports
        """)
        
        # Show some popular stocks
        st.subheader("🔥 Popular Stocks")
        
        cols = st.columns(5)
        popular = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK"]
        
        for i, stock in enumerate(popular):
            with cols[i]:
                try:
                    price_data = json.loads(get_stock_price.run(stock))
                    change = price_data.get("change_percent", 0)
                    trend = "🟢" if change >= 0 else "🔴"
                    st.metric(
                        f"{trend} {stock}",
                        f"₹{price_data.get('current_price', 0):,.2f}",
                        f"{change:+.2f}%"
                    )
                except:
                    st.metric(stock, "Loading...")


if __name__ == "__main__":
    main()
