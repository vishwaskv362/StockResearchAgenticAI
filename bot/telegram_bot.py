"""
Telegram Bot for Stock Research Assistant
Full-featured bot with commands, inline keyboards, and async processing
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional
import json

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    BotCommand,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from telegram.constants import ParseMode, ChatAction

from config import settings, NIFTY50_STOCKS, SECTORS
from crews.research_crew import analyze_stock_sync
from tools.market_data import get_stock_price, get_index_data, get_stock_info
from tools.news_scraper import get_stock_news
from tools.analysis import calculate_technical_indicators, get_fundamental_metrics

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Rate limiting
user_last_request = {}
REQUEST_COOLDOWN = 30  # seconds between full analyses


class StockResearchBot:
    """Telegram bot for stock research assistance."""
    
    def __init__(self, token: str):
        """Initialize the bot with the given token."""
        self.token = token
        self.application = None
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command."""
        user = update.effective_user
        welcome_message = f"""
🙏 **Namaste {user.first_name}!**

Welcome to the **AI Stock Research Assistant** 🇮🇳

I'm your intelligent research companion for Indian stock markets (NSE/BSE).

**What I can do:**

📊 **Full Analysis** - Complete research report with AI insights
⚡ **Quick Check** - Fast price and key metrics
📈 **Technical Analysis** - Charts, indicators, signals
💰 **Fundamentals** - Valuations, ratios, financial health
📰 **News** - Latest news and sentiment analysis
🏦 **Market Overview** - Index levels, FII/DII activity

**Commands:**
/analyze `SYMBOL` - Full AI-powered research
/quick `SYMBOL` - Quick price check
/technical `SYMBOL` - Technical analysis
/fundamental `SYMBOL` - Fundamental metrics
/news `SYMBOL` - Latest news
/market - Market overview
/nifty50 - NIFTY 50 stocks list
/help - Detailed help

**Examples:**
`/analyze RELIANCE`
`/quick TCS`
`/technical INFY`

Just type a stock symbol or use any command to get started! 🚀

---
⚠️ *Disclaimer: For educational purposes only. Not financial advice.*
"""
        
        keyboard = [
            [
                InlineKeyboardButton("📊 Analyze Stock", callback_data="action_analyze"),
                InlineKeyboardButton("⚡ Quick Check", callback_data="action_quick"),
            ],
            [
                InlineKeyboardButton("📈 Market Overview", callback_data="action_market"),
                InlineKeyboardButton("📚 NIFTY 50 List", callback_data="action_nifty50"),
            ],
            [
                InlineKeyboardButton("❓ Help", callback_data="action_help"),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup,
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command."""
        help_text = """
📚 **Stock Research Assistant - Help Guide**

**Available Commands:**

🔹 `/analyze SYMBOL` 
   Complete AI-powered research report
   Example: `/analyze RELIANCE`
   ⏱️ Takes 2-3 minutes

🔹 `/quick SYMBOL`
   Quick price and basic info
   Example: `/quick TCS`
   ⏱️ Instant

🔹 `/technical SYMBOL`
   Technical analysis with indicators
   Example: `/technical HDFCBANK`
   ⏱️ 30 seconds

🔹 `/fundamental SYMBOL`
   Fundamental metrics and valuation
   Example: `/fundamental INFY`
   ⏱️ 30 seconds

🔹 `/news SYMBOL`
   Latest news from multiple sources
   Example: `/news ICICIBANK`
   ⏱️ 15 seconds

🔹 `/market`
   Overall market snapshot
   NIFTY, SENSEX, FII/DII activity

🔹 `/nifty50`
   List of all NIFTY 50 stocks

🔹 `/sectors`
   Stocks organized by sector

**Tips:**
- Stock symbols should be NSE symbols (e.g., RELIANCE, not RIL)
- Analysis is most relevant during market hours
- Full analysis may take 2-3 minutes

**Supported Stocks:**
All NSE and BSE listed stocks!
NIFTY 50, NIFTY Next 50, NIFTY 500, and more.

---
⚠️ *For educational purposes only. Always do your own research.*
"""
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    
    async def analyze_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /analyze command - Full AI analysis."""
        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a stock symbol.\n\n"
                "Example: `/analyze RELIANCE`",
                parse_mode=ParseMode.MARKDOWN,
            )
            return
        
        symbol = context.args[0].upper().strip()
        user_id = update.effective_user.id
        
        # Rate limiting
        now = datetime.now().timestamp()
        if user_id in user_last_request:
            time_since = now - user_last_request[user_id]
            if time_since < REQUEST_COOLDOWN:
                remaining = int(REQUEST_COOLDOWN - time_since)
                await update.message.reply_text(
                    f"⏳ Please wait {remaining} seconds before requesting another full analysis.\n\n"
                    f"Use `/quick {symbol}` for instant results!",
                    parse_mode=ParseMode.MARKDOWN,
                )
                return
        
        user_last_request[user_id] = now
        
        # Send initial message
        status_msg = await update.message.reply_text(
            f"🔬 **Analyzing {symbol}...**\n\n"
            "⏳ This comprehensive analysis may take 2-3 minutes.\n\n"
            "Our AI agents are working on:\n"
            "📊 Market Data Collection\n"
            "📰 News & Sentiment Analysis\n"
            "💰 Fundamental Research\n"
            "📈 Technical Analysis\n"
            "🎯 Investment Strategy\n\n"
            "_Please wait..._",
            parse_mode=ParseMode.MARKDOWN,
        )
        
        # Show typing indicator
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action=ChatAction.TYPING,
        )
        
        try:
            # Run the analysis in a thread to not block
            loop = asyncio.get_event_loop()
            report = await loop.run_in_executor(
                None,
                analyze_stock_sync,
                symbol,
                "full",
            )
            
            # Delete status message
            await status_msg.delete()
            
            # Send report (may need to split if too long)
            await self._send_long_message(update, report)
            
        except Exception as e:
            logger.error(f"Analysis error for {symbol}: {e}")
            await status_msg.edit_text(
                f"❌ **Error analyzing {symbol}**\n\n"
                f"Error: {str(e)[:200]}\n\n"
                "Please try again or check if the symbol is correct.",
                parse_mode=ParseMode.MARKDOWN,
            )
    
    async def quick_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /quick command - Quick price check."""
        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a stock symbol.\n\n"
                "Example: `/quick TCS`",
                parse_mode=ParseMode.MARKDOWN,
            )
            return
        
        symbol = context.args[0].upper().strip()
        
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action=ChatAction.TYPING,
        )
        
        try:
            # Get price data
            price_data = json.loads(get_stock_price.run(symbol))
            info_data = json.loads(get_stock_info.run(symbol))
            
            if "error" in price_data:
                await update.message.reply_text(
                    f"❌ Could not find data for **{symbol}**\n"
                    "Please check if the symbol is correct.",
                    parse_mode=ParseMode.MARKDOWN,
                )
                return
            
            # Format message
            change = price_data.get("change", 0)
            change_pct = price_data.get("change_percent", 0)
            trend_emoji = "🟢" if change >= 0 else "🔴"
            
            message = f"""
{trend_emoji} **{symbol}** - Quick Overview

💰 **Current Price:** ₹{price_data.get('current_price', 'N/A'):,.2f}
📊 **Change:** ₹{change:+,.2f} ({change_pct:+.2f}%)

📈 **Day's Range:**
   High: ₹{price_data.get('high', 'N/A'):,.2f}
   Low: ₹{price_data.get('low', 'N/A'):,.2f}

📉 **52 Week Range:**
   High: ₹{price_data.get('52_week_high', 'N/A'):,.2f}
   Low: ₹{price_data.get('52_week_low', 'N/A'):,.2f}

📊 **Volume:** {price_data.get('volume', 0):,}

🏢 **Sector:** {info_data.get('sector', 'N/A')}
🏭 **Industry:** {info_data.get('industry', 'N/A')}
📊 **Market Cap:** {info_data.get('market_cap_category', 'N/A')}

---
_Updated: {datetime.now().strftime('%H:%M:%S IST')}_
"""
            
            keyboard = [
                [
                    InlineKeyboardButton("📊 Full Analysis", callback_data=f"analyze_{symbol}"),
                    InlineKeyboardButton("📈 Technical", callback_data=f"technical_{symbol}"),
                ],
                [
                    InlineKeyboardButton("💰 Fundamentals", callback_data=f"fundamental_{symbol}"),
                    InlineKeyboardButton("📰 News", callback_data=f"news_{symbol}"),
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup,
            )
            
        except Exception as e:
            logger.error(f"Quick check error for {symbol}: {e}")
            await update.message.reply_text(
                f"❌ Error fetching data for {symbol}\n{str(e)[:100]}",
            )
    
    async def technical_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /technical command."""
        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a stock symbol.\n\n"
                "Example: `/technical INFY`",
                parse_mode=ParseMode.MARKDOWN,
            )
            return
        
        symbol = context.args[0].upper().strip()
        
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action=ChatAction.TYPING,
        )
        
        try:
            tech_data = json.loads(calculate_technical_indicators.run(symbol))
            
            if "error" in tech_data:
                await update.message.reply_text(f"❌ Error: {tech_data['error']}")
                return
            
            # Format technical analysis message
            ma = tech_data.get("moving_averages", {})
            momentum = tech_data.get("momentum", {})
            volatility = tech_data.get("volatility", {})
            sr = tech_data.get("support_resistance", {})
            trend = tech_data.get("trend", {})
            signals = tech_data.get("signals", [])
            
            signal_emoji = {"BULLISH": "🟢", "BEARISH": "🔴", "NEUTRAL": "🟡"}
            overall = tech_data.get("overall_signal", "NEUTRAL")
            
            message = f"""
📈 **{symbol}** - Technical Analysis

{signal_emoji.get(overall, '🟡')} **Overall Signal: {overall}**

💰 **Current Price:** ₹{tech_data.get('current_price', 'N/A'):,.2f}

📊 **Moving Averages:**
   SMA 20: ₹{ma.get('sma_20', 'N/A')}
   SMA 50: ₹{ma.get('sma_50', 'N/A')}
   SMA 200: ₹{ma.get('sma_200', 'N/A')}
   Price vs SMA20: {ma.get('price_vs_sma20', 'N/A')}

📉 **Momentum Indicators:**
   RSI (14): {momentum.get('rsi_14', 'N/A')} - {momentum.get('rsi_interpretation', '')}
   MACD: {momentum.get('macd_line', 'N/A')}
   Signal: {momentum.get('macd_signal', 'N/A')}

📊 **Volatility:**
   Bollinger Position: {volatility.get('bb_position', 'N/A')}
   ATR: {volatility.get('atr_percent', 'N/A')}

🎯 **Key Levels:**
   Resistance 1: ₹{sr.get('resistance_1', 'N/A')}
   Support 1: ₹{sr.get('support_1', 'N/A')}
   Pivot: ₹{sr.get('pivot', 'N/A')}

📈 **Trend:**
   Short-term: {trend.get('short_term', 'N/A')}
   Medium-term: {trend.get('medium_term', 'N/A')}
   Long-term: {trend.get('long_term', 'N/A')}

**⚡ Signals:**
"""
            for sig in signals[:5]:
                message += f"• {sig.get('indicator', '')}: {sig.get('signal', '')}\n"
            
            message += f"\n---\n_Analysis as of {datetime.now().strftime('%H:%M:%S IST')}_"
            
            await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error(f"Technical analysis error: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)[:100]}")
    
    async def fundamental_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /fundamental command."""
        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a stock symbol.\n\n"
                "Example: `/fundamental HDFCBANK`",
                parse_mode=ParseMode.MARKDOWN,
            )
            return
        
        symbol = context.args[0].upper().strip()
        
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action=ChatAction.TYPING,
        )
        
        try:
            fund_data = json.loads(get_fundamental_metrics.run(symbol))
            
            if "error" in fund_data:
                await update.message.reply_text(f"❌ Error: {fund_data['error']}")
                return
            
            val = fund_data.get("valuation", {})
            prof = fund_data.get("profitability", {})
            health = fund_data.get("financial_health", {})
            div = fund_data.get("dividends", {})
            growth = fund_data.get("growth", {})
            size = fund_data.get("size", {})
            rating = fund_data.get("overall_rating", "N/A")
            
            rating_emoji = {
                "STRONG BUY": "🟢🟢",
                "BUY": "🟢",
                "HOLD": "🟡",
                "SELL": "🔴",
                "STRONG SELL": "🔴🔴",
            }
            
            message = f"""
💰 **{symbol}** - Fundamental Analysis

{rating_emoji.get(rating, '⚪')} **Rating: {rating}**
📊 Score: {fund_data.get('score', 'N/A')}

🏢 **Company:** {fund_data.get('company_name', 'N/A')}
📁 **Sector:** {fund_data.get('sector', 'N/A')}

📊 **Valuation:**
   P/E Ratio: {val.get('pe_ratio', 'N/A')}
   Forward P/E: {val.get('forward_pe', 'N/A')}
   P/B Ratio: {val.get('pb_ratio', 'N/A')}
   EV/EBITDA: {val.get('ev_ebitda', 'N/A')}

💹 **Profitability:**
   ROE: {prof.get('roe', 'N/A')}
   ROA: {prof.get('roa', 'N/A')}
   Profit Margin: {prof.get('profit_margin', 'N/A')}

🏦 **Financial Health:**
   Debt/Equity: {health.get('debt_to_equity', 'N/A')}
   Current Ratio: {health.get('current_ratio', 'N/A')}
   Status: {health.get('debt_status', 'N/A')}

📈 **Growth:**
   Earnings Growth: {growth.get('earnings_growth', 'N/A')}
   Revenue Growth: {growth.get('revenue_growth', 'N/A')}

💵 **Dividends:**
   Yield: {div.get('dividend_yield', 'N/A')}
   Payout Ratio: {div.get('payout_ratio', 'N/A')}

📊 **Size:**
   Market Cap: {size.get('market_cap', 'N/A')}
   Revenue: {size.get('revenue', 'N/A')}

---
_Analysis as of {datetime.now().strftime('%H:%M:%S IST')}_
"""
            
            await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error(f"Fundamental analysis error: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)[:100]}")
    
    async def news_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /news command."""
        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a stock symbol.\n\n"
                "Example: `/news RELIANCE`",
                parse_mode=ParseMode.MARKDOWN,
            )
            return
        
        symbol = context.args[0].upper().strip()
        
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action=ChatAction.TYPING,
        )
        
        try:
            news_data = json.loads(get_stock_news.run(symbol, 5))
            
            articles = news_data.get("articles", [])
            
            if not articles:
                await update.message.reply_text(
                    f"📰 No recent news found for **{symbol}**",
                    parse_mode=ParseMode.MARKDOWN,
                )
                return
            
            message = f"📰 **Latest News for {symbol}**\n\n"
            
            for i, article in enumerate(articles[:7], 1):
                title = article.get("title", "No title")[:100]
                source = article.get("source", "Unknown")
                url = article.get("url", "")
                
                if url:
                    message += f"**{i}.** [{title}]({url})\n"
                else:
                    message += f"**{i}.** {title}\n"
                message += f"   _Source: {source}_\n\n"
            
            message += f"---\n_Fetched: {datetime.now().strftime('%H:%M:%S IST')}_"
            
            await update.message.reply_text(
                message,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
            )
            
        except Exception as e:
            logger.error(f"News fetch error: {e}")
            await update.message.reply_text(f"❌ Error fetching news: {str(e)[:100]}")
    
    async def market_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /market command - Market overview."""
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action=ChatAction.TYPING,
        )
        
        try:
            indices_data = json.loads(get_index_data.run("ALL"))
            
            message = "🏦 **Indian Market Overview**\n\n"
            
            index_names = {
                "NIFTY50": "NIFTY 50",
                "SENSEX": "SENSEX",
                "BANKNIFTY": "BANK NIFTY",
                "NIFTYIT": "NIFTY IT",
            }
            
            for key, name in index_names.items():
                if key in indices_data:
                    data = indices_data[key]
                    value = data.get("value", 0)
                    change = data.get("change", 0)
                    change_pct = data.get("change_percent", 0)
                    emoji = "🟢" if change >= 0 else "🔴"
                    
                    message += f"{emoji} **{name}**\n"
                    message += f"   {value:,.2f} ({change:+,.2f} | {change_pct:+.2f}%)\n\n"
            
            # Add market status
            now = datetime.now()
            hour = now.hour
            minute = now.minute
            
            if now.weekday() >= 5:
                market_status = "🔴 Market Closed (Weekend)"
            elif hour < 9 or (hour == 9 and minute < 15):
                market_status = "🟡 Pre-Market"
            elif hour < 15 or (hour == 15 and minute <= 30):
                market_status = "🟢 Market Open"
            else:
                market_status = "🔴 Market Closed"
            
            message += f"**Status:** {market_status}\n"
            message += f"_Updated: {now.strftime('%H:%M:%S IST')}_"
            
            keyboard = [
                [
                    InlineKeyboardButton("📊 Top Gainers", callback_data="market_gainers"),
                    InlineKeyboardButton("📉 Top Losers", callback_data="market_losers"),
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup,
            )
            
        except Exception as e:
            logger.error(f"Market overview error: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)[:100]}")
    
    async def nifty50_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /nifty50 command - List NIFTY 50 stocks."""
        message = "📊 **NIFTY 50 Stocks**\n\n"
        
        # Format stocks in columns
        for i in range(0, len(NIFTY50_STOCKS), 5):
            row = NIFTY50_STOCKS[i:i+5]
            message += " | ".join(f"`{s}`" for s in row) + "\n"
        
        message += "\n_Use `/quick SYMBOL` to check any stock_"
        
        await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
    
    async def sectors_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /sectors command - Stocks by sector."""
        message = "🏭 **Stocks by Sector**\n\n"
        
        for sector, stocks in SECTORS.items():
            message += f"**{sector}:**\n"
            message += " | ".join(f"`{s}`" for s in stocks[:6])
            message += "\n\n"
        
        message += "_Use `/quick SYMBOL` to check any stock_"
        
        await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle inline button callbacks."""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        # Handle action buttons
        if data == "action_analyze":
            await query.message.reply_text(
                "📊 **Analyze a Stock**\n\n"
                "Send the command with a stock symbol:\n"
                "`/analyze RELIANCE`\n`/analyze TCS`\n`/analyze INFY`",
                parse_mode=ParseMode.MARKDOWN,
            )
        elif data == "action_quick":
            await query.message.reply_text(
                "⚡ **Quick Check**\n\n"
                "Send the command with a stock symbol:\n"
                "`/quick HDFCBANK`\n`/quick ICICIBANK`",
                parse_mode=ParseMode.MARKDOWN,
            )
        elif data == "action_market":
            # Simulate /market command
            context.args = []
            await self.market_command(query, context)
        elif data == "action_nifty50":
            # Simulate /nifty50 command
            await query.message.reply_text(
                self._format_nifty50_list(),
                parse_mode=ParseMode.MARKDOWN,
            )
        elif data == "action_help":
            await query.message.reply_text(
                "Use /help to see all available commands and how to use them.",
            )
        
        # Handle stock-specific callbacks
        elif data.startswith("analyze_"):
            symbol = data.replace("analyze_", "")
            await query.message.reply_text(
                f"Starting full analysis for **{symbol}**...\n"
                f"Use `/analyze {symbol}` to begin.",
                parse_mode=ParseMode.MARKDOWN,
            )
        elif data.startswith("technical_"):
            symbol = data.replace("technical_", "")
            context.args = [symbol]
            await self.technical_command(query, context)
        elif data.startswith("fundamental_"):
            symbol = data.replace("fundamental_", "")
            context.args = [symbol]
            await self.fundamental_command(query, context)
        elif data.startswith("news_"):
            symbol = data.replace("news_", "")
            context.args = [symbol]
            await self.news_command(query, context)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle plain text messages - treat as stock symbol."""
        text = update.message.text.strip().upper()
        
        # Check if it looks like a stock symbol
        if len(text) <= 15 and text.isalnum():
            # Assume it's a stock symbol, do quick check
            context.args = [text]
            await self.quick_command(update, context)
        else:
            await update.message.reply_text(
                "🤔 I didn't understand that.\n\n"
                "**Tips:**\n"
                "• Just type a stock symbol like `RELIANCE` or `TCS`\n"
                "• Use `/help` to see all commands\n"
                "• Use `/analyze SYMBOL` for full analysis",
                parse_mode=ParseMode.MARKDOWN,
            )
    
    def _format_nifty50_list(self) -> str:
        """Format NIFTY 50 list for display."""
        message = "📊 **NIFTY 50 Stocks**\n\n"
        for i in range(0, len(NIFTY50_STOCKS), 5):
            row = NIFTY50_STOCKS[i:i+5]
            message += " | ".join(f"`{s}`" for s in row) + "\n"
        message += "\n_Tap any symbol to analyze_"
        return message
    
    async def _send_long_message(self, update: Update, text: str, max_length: int = 4000) -> None:
        """Send a long message by splitting it into chunks."""
        if len(text) <= max_length:
            await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
            return
        
        # Split by double newlines (paragraphs) to avoid breaking markdown
        paragraphs = text.split("\n\n")
        current_chunk = ""
        
        for para in paragraphs:
            if len(current_chunk) + len(para) + 2 <= max_length:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    await update.message.reply_text(
                        current_chunk.strip(),
                        parse_mode=ParseMode.MARKDOWN,
                    )
                current_chunk = para + "\n\n"
        
        if current_chunk:
            await update.message.reply_text(
                current_chunk.strip(),
                parse_mode=ParseMode.MARKDOWN,
            )
    
    async def setup_commands(self, application: Application) -> None:
        """Set up bot commands for the menu."""
        commands = [
            BotCommand("start", "Start the bot"),
            BotCommand("help", "Show help guide"),
            BotCommand("analyze", "Full AI analysis for a stock"),
            BotCommand("quick", "Quick price check"),
            BotCommand("technical", "Technical analysis"),
            BotCommand("fundamental", "Fundamental analysis"),
            BotCommand("news", "Latest news for a stock"),
            BotCommand("market", "Market overview"),
            BotCommand("nifty50", "List NIFTY 50 stocks"),
            BotCommand("sectors", "Stocks by sector"),
        ]
        await application.bot.set_my_commands(commands)
    
    def run(self) -> None:
        """Run the bot."""
        # Build application
        self.application = Application.builder().token(self.token).build()
        
        # Add handlers
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("analyze", self.analyze_command))
        self.application.add_handler(CommandHandler("quick", self.quick_command))
        self.application.add_handler(CommandHandler("technical", self.technical_command))
        self.application.add_handler(CommandHandler("fundamental", self.fundamental_command))
        self.application.add_handler(CommandHandler("news", self.news_command))
        self.application.add_handler(CommandHandler("market", self.market_command))
        self.application.add_handler(CommandHandler("nifty50", self.nifty50_command))
        self.application.add_handler(CommandHandler("sectors", self.sectors_command))
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        self.application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            self.handle_message,
        ))
        
        # Set up commands menu
        self.application.post_init = self.setup_commands
        
        # Run the bot
        logger.info("Starting Stock Research Bot...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)


def run_bot():
    """Entry point to run the Telegram bot."""
    if not settings.telegram_bot_token:
        print("❌ Error: TELEGRAM_BOT_TOKEN not set in environment")
        print("Please set it in your .env file")
        return
    
    bot = StockResearchBot(settings.telegram_bot_token)
    bot.run()


if __name__ == "__main__":
    run_bot()
