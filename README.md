# 🇮🇳 AI Stock Research Assistant

**AI-Powered Stock Research Assistant for Indian Markets (NSE/BSE)**

A comprehensive, multi-agent AI system built with CrewAI and Mistral AI that provides institutional-quality stock research through Web UI, Telegram bot, and CLI.

![Tests](https://github.com/vishwaskv362/StockResearchAIAgent/actions/workflows/tests.yml/badge.svg)
![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![CrewAI](https://img.shields.io/badge/CrewAI-0.86+-green.svg)
![Mistral AI](https://img.shields.io/badge/Mistral%20AI-Powered-orange.svg)
![Telegram](https://img.shields.io/badge/Telegram-Bot-blue.svg)

---

## 🚀 Quick Start

**→ See [SETUP.md](SETUP.md) for complete installation and setup instructions.**

```bash
# Install dependencies
uv sync

# Configure API keys
cp .env.example .env
# Edit .env with your MISTRAL_API_KEY

# Run Web UI
source .venv/bin/activate && streamlit run app.py

# Or run CLI
uv run python run_analysis.py RELIANCE --quick
```

---

## ✨ Features

### 🤖 AI-Powered Analysis
- **6 Specialized AI Agents** working together:
  - 📊 Market Data Analyst
  - 📰 News & Sentiment Analyst
  - 💰 Fundamental Research Analyst
  - 📈 Technical Analyst
  - 🎯 Investment Strategist
  - 📝 Report Writer

### 📱 Telegram Bot Interface
- Instant price checks
- Full AI-powered research reports
- Technical analysis with indicators
- Fundamental metrics and valuation
- Latest news aggregation
- Market overview with indices

### 📊 Market Data
- Real-time prices from NSE/BSE
- Historical data and charts
- 52-week high/low tracking
- Volume analysis
- Delivery percentage (NSE)

### 📰 News Scraping
- **Moneycontrol** - Latest stock news
- **Economic Times** - Market updates
- **Business Standard** - Analysis
- Sentiment analysis for each article

### 💹 Technical Analysis
- Moving Averages (SMA, EMA)
- RSI, MACD, Bollinger Bands
- Support/Resistance levels
- Trend identification
- Trading signals

### 💰 Fundamental Analysis
- P/E, P/B, EV/EBITDA ratios
- ROE, ROCE, Profit margins
- Debt analysis
- Dividend tracking
- Growth metrics

### 🏦 Institutional Tracking
- FII/DII activity
- Bulk/Block deals
- Promoter holdings
- Mutual fund activity

---

## 🤖 The 6 AI Agents

This project uses **CrewAI** to orchestrate 6 specialized AI agents that work together like a professional research team:

| Agent | Role | Responsibility |
|-------|------|----------------|
| **📊 Market Data Analyst** | Data Collector | Fetches real-time prices, volume, 52-week range, historical data |
| **📰 News & Sentiment Analyst** | News Hunter | Scrapes news from 3 sources, analyzes sentiment (positive/negative/neutral) |
| **💰 Fundamental Analyst** | Value Investor | Evaluates P/E, P/B, ROE, debt ratios, margins, growth metrics |
| **📈 Technical Analyst** | Chart Reader | Calculates RSI, MACD, moving averages, support/resistance, trend signals |
| **🎯 Investment Strategist** | Decision Maker | Combines all analysis → provides BUY/SELL/HOLD with price targets |
| **📝 Report Writer** | Communicator | Compiles everything into a clean, professional research report |

### 🔄 How Agents Work Together (Orchestration)

```
User Request: "Analyze RELIANCE"
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  CREW ORCHESTRATION (Sequential Process)                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Step 1: 📊 Market Data Agent                               │
│          → Fetches price: ₹1,395.40                         │
│          → Gets volume, 52-week high/low                    │
│          → Retrieves 1-year historical data                 │
│                         │                                   │
│                         ▼                                   │
│  Step 2: 📰 News Agent                                      │
│          → Scrapes Moneycontrol, ET, Business Standard      │
│          → Analyzes sentiment of each article               │
│          → Returns: 5 positive, 2 neutral, 1 negative       │
│                         │                                   │
│                         ▼                                   │
│  Step 3: 💰 Fundamental Agent                               │
│          → Analyzes P/E: 25.3 (fair valued)                 │
│          → Checks ROE: 12%, Debt/Equity: 0.4               │
│          → Evaluates growth metrics                         │
│                         │                                   │
│                         ▼                                   │
│  Step 4: 📈 Technical Agent                                 │
│          → Calculates RSI: 55 (neutral)                     │
│          → MACD: Bullish crossover                          │
│          → Price above 200 DMA = Uptrend                    │
│                         │                                   │
│                         ▼                                   │
│  Step 5: 🎯 Strategist Agent                                │
│          → Weighs all inputs                                │
│          → Decision: BUY                                    │
│          → Entry: ₹1,380, Target: ₹1,500, SL: ₹1,320       │
│                         │                                   │
│                         ▼                                   │
│  Step 6: 📝 Report Agent                                    │
│          → Formats everything into readable report          │
│          → Adds risk warnings and action plan               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
   Final Research Report Delivered to User
```

---

## 📡 Data Sources

### Stock Prices & Market Data

| Source | Library | Data Provided |
|--------|---------|---------------|
| **Yahoo Finance** | `yfinance` | Real-time prices, historical OHLCV, fundamentals |
| **NSE India** | `nsetools` | NSE-specific data, delivery percentage |

```python
# Example: How we fetch NSE stocks
import yfinance as yf
ticker = yf.Ticker("RELIANCE.NS")  # .NS suffix for NSE
price = ticker.info["currentPrice"]  # ₹1,395.40
```

### News Sources (Web Scraping)

| Source | URL Pattern | What We Extract |
|--------|-------------|-----------------|
| **Moneycontrol** | `moneycontrol.com/news/tags/{symbol}` | Headlines, summary, date |
| **Economic Times** | `economictimes.com/topic/{symbol}` | Headlines, summary, date |
| **Business Standard** | `business-standard.com/topic/{symbol}` | Headlines, summary, date |

### Technical Indicators (Calculated)

| Indicator | What It Tells You | Library |
|-----------|-------------------|---------|
| **RSI** | Overbought (>70) / Oversold (<30) | `ta` |
| **MACD** | Momentum & trend direction | `ta` |
| **SMA 20/50/200** | Short/Medium/Long term trends | `pandas` |
| **EMA 12/26** | Faster-reacting trends | `ta` |
| **Bollinger Bands** | Volatility & reversals | `ta` |
| **Support/Resistance** | Key price levels | Custom |

### Fundamental Metrics

| Metric | Source | Interpretation |
|--------|--------|----------------|
| P/E Ratio | Yahoo Finance | < 15 cheap, > 30 expensive |
| P/B Ratio | Yahoo Finance | < 1 undervalued |
| ROE | Yahoo Finance | > 15% is good |
| Debt/Equity | Yahoo Finance | < 1 is healthy |
| Profit Margin | Yahoo Finance | Higher is better |
| Dividend Yield | Yahoo Finance | Income potential |

### AI Analysis

| Purpose | Provider | Model |
|---------|----------|-------|
| Sentiment Analysis | Mistral AI | `mistral-large-latest` |
| Investment Recommendations | Mistral AI | `mistral-large-latest` |
| Report Generation | Mistral AI | `mistral-large-latest` |

---

## 📱 Telegram Commands

| Command | Description |
|---------|-------------|
| `/start` | Start the bot and see welcome message |
| `/help` | Show detailed help guide |
| `/analyze SYMBOL` | Full AI-powered research report |
| `/quick SYMBOL` | Quick price and basic info |
| `/technical SYMBOL` | Technical analysis with indicators |
| `/fundamental SYMBOL` | Fundamental metrics |
| `/news SYMBOL` | Latest news from multiple sources |
| `/market` | Market overview with indices |
| `/nifty50` | List all NIFTY 50 stocks |
| `/sectors` | Stocks organized by sector |

### Examples

```
/analyze RELIANCE
/quick TCS
/technical HDFCBANK
/fundamental INFY
/news ICICIBANK
```

Or just type a stock symbol like `RELIANCE` for a quick check!

## 🏗️ Project Structure

```
stock-research-assistant/
├── agents/                     # AI Agents
│   ├── __init__.py
│   ├── market_data_agent.py    # Market data collection
│   ├── news_agent.py           # News & sentiment
│   ├── fundamental_agent.py    # Fundamental analysis
│   ├── technical_agent.py      # Technical analysis
│   ├── strategist_agent.py     # Investment strategy
│   └── report_agent.py         # Report writing
│
├── tools/                      # Custom Tools
│   ├── __init__.py
│   ├── market_data.py          # NSE/BSE data tools
│   ├── news_scraper.py         # News scraping tools
│   ├── analysis.py             # Technical/Fundamental analysis
│   └── institutional.py        # FII/DII tracking
│
├── crews/                      # Crew Orchestration
│   ├── __init__.py
│   └── research_crew.py        # Main research crew
│
├── bot/                        # Telegram Bot
│   ├── __init__.py
│   └── telegram_bot.py         # Bot implementation
│
├── data/                       # Data storage
│   ├── cache/
│   └── reports/
│
├── config.py                   # Configuration
├── app.py                      # Streamlit Web UI
├── pyproject.toml              # Dependencies
├── run_bot.py                  # Run Telegram bot
├── run_analysis.py             # CLI analysis tool
├── .env.example                # Environment template
├── SETUP.md                    # Setup instructions
└── README.md
```

## 🔧 Configuration

See [SETUP.md](SETUP.md) for environment variables and configuration options.

## 📊 Sample Output

### Full Analysis Report

```
📊 RELIANCE - AI Research Report

📈 Executive Summary
• Current Price: ₹2,847.50 (+1.2%)
• Recommendation: BUY with target ₹3,100
• Risk Level: Moderate

💰 Fundamental Highlights
• P/E Ratio: 28.5 (Fair valued)
• ROE: 8.9%
• Debt/Equity: 0.42 (Healthy)

📈 Technical View
• Trend: Bullish (above 200 DMA)
• RSI: 58 (Neutral)
• Support: ₹2,750 | Resistance: ₹2,950

📰 Recent News
• Q3 results beat estimates
• Jio subscriber growth continues
• New energy investments

⚠️ Risks
• Oil price volatility
• Competition in telecom
• Global economic slowdown

🎯 Action Plan
Entry: ₹2,820-2,860
Stop Loss: ₹2,700
Target 1: ₹3,000
Target 2: ₹3,150
```

## 🛠️ Development

See [SETUP.md](SETUP.md) for development commands and adding new agents/tools.

## ⚠️ Disclaimer

**This tool is for educational and research purposes only.**

- Not financial advice
- Not a recommendation to buy/sell securities
- Always do your own research (DYOR)
- Consult a SEBI-registered advisor for investment decisions
- Past performance doesn't guarantee future results

The creators are not responsible for any financial losses incurred from using this tool.

## 📝 License

MIT License - feel free to use and modify!

## 🙏 Acknowledgments

- [CrewAI](https://crewai.com) - Multi-agent framework
- [Mistral AI](https://mistral.ai) - LLM provider
- [yfinance](https://github.com/ranaroussi/yfinance) - Market data
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - Telegram API

---

Made with ❤️ for Indian Investors 🇮🇳
