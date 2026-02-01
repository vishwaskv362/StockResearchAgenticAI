# 🛠️ Setup Guide - Stock Research Assistant

Complete setup instructions using **uv** (fast Python package manager).

---

## 📋 Prerequisites

- **Python 3.11+** 
- **uv** - Fast Python package manager
- **Mistral AI API Key** - For AI analysis
- **Telegram Bot Token** - (Optional) For Telegram bot

---

## 🚀 Quick Setup (5 minutes)

### Step 1: Install uv

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with Homebrew
brew install uv

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Step 2: Clone & Install Dependencies

```bash
# Navigate to project
cd /Users/vishwas/Documents/projects/stock-research-assistant

# Install all dependencies (uv auto-creates .venv)
uv sync
```

### Step 3: Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit with your API keys
nano .env   # or use any editor
```

**Required `.env` configuration:**
```env
# Mistral AI (Required for AI analysis)
MISTRAL_API_KEY=your_mistral_api_key_here

# Telegram Bot (Optional - only for Telegram bot)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Disable telemetry warnings
CREWAI_TELEMETRY_OPT_OUT=true
OTEL_SDK_DISABLED=true
```

---

## 🔑 Getting API Keys

### Mistral AI API Key

1. Go to [https://console.mistral.ai/](https://console.mistral.ai/)
2. Sign up or log in
3. Navigate to **API Keys** section
4. Click **Create new key**
5. Copy and paste into `.env`

### Telegram Bot Token (Optional)

1. Open Telegram app
2. Search for `@BotFather`
3. Send `/newbot` command
4. Follow the prompts to name your bot
5. Copy the token and paste into `.env`

---

## ▶️ Running the App

### 🌐 Web UI (Streamlit) - Recommended

```bash
cd /Users/vishwas/Documents/projects/stock-research-assistant

# Method 1: Activate venv and run
source .venv/bin/activate
streamlit run app.py

# Method 2: Use uv run with python -m
uv run python -m streamlit run app.py
```

**Access at:** http://localhost:8501

### 💻 Command Line Interface

```bash
cd /Users/vishwas/Documents/projects/stock-research-assistant

# Quick price check (instant, no AI)
uv run python run_analysis.py RELIANCE --quick

# Full AI analysis (2-3 minutes)
uv run python run_analysis.py RELIANCE

# Technical analysis only
uv run python run_analysis.py TCS --type technical-only

# List all available stocks
uv run python run_analysis.py --list

# Show help
uv run python run_analysis.py --help
```

### 🤖 Telegram Bot

```bash
cd /Users/vishwas/Documents/projects/stock-research-assistant

# Start the bot
uv run python run_bot.py
```

Then open Telegram and message your bot!

---

## 📦 UV Commands Reference

| Command | Description |
|---------|-------------|
| `uv sync` | Install/update all dependencies |
| `uv pip install <package>` | Add a new package |
| `uv pip list` | List installed packages |
| `uv run python <script>` | Run Python script in venv |
| `uv venv` | Create new virtual environment |
| `uv pip freeze` | Export requirements |

### Common Workflows

```bash
# Update all dependencies
uv sync --upgrade

# Add a new package
uv pip install pandas-ta

# Check installed packages
uv pip list | grep streamlit

# Clean and reinstall
rm -rf .venv && uv sync
```

---

## 🔧 Troubleshooting

### "Module not found" error

```bash
# Reinstall dependencies
uv sync --reinstall
```

### "API key not configured" error

```bash
# Check if .env exists
cat .env

# Verify key is set
grep MISTRAL_API_KEY .env
```

### Streamlit not found

```bash
# Install streamlit explicitly
uv pip install streamlit

# Run with python -m
uv run python -m streamlit run app.py
```

### Port already in use

```bash
# Use different port
streamlit run app.py --server.port 8502
```

### CrewAI telemetry warnings

Add to `.env`:
```env
CREWAI_TELEMETRY_OPT_OUT=true
OTEL_SDK_DISABLED=true
```

---

## 📁 Project Structure

```
stock-research-assistant/
├── .env                 # Your API keys (create from .env.example)
├── .env.example         # Template for environment variables
├── .venv/               # Virtual environment (auto-created by uv)
├── app.py               # Streamlit web UI
├── run_bot.py           # Telegram bot entry point
├── run_analysis.py      # CLI analysis tool
├── config.py            # Configuration settings
├── pyproject.toml       # Dependencies
├── agents/              # AI Agents
├── bot/                 # Telegram bot code
├── crews/               # CrewAI orchestration
├── tools/               # Market data & analysis tools
└── data/                # Cache and reports
```

---

## ✅ Verify Installation

Run this to verify everything works:

```bash
cd /Users/vishwas/Documents/projects/stock-research-assistant

# Test market data (no API key needed)
uv run python -c "
from tools.market_data import get_stock_price
import json
data = json.loads(get_stock_price.run('TCS'))
print(f'TCS Price: ₹{data.get(\"current_price\", \"N/A\")}')
print('✅ Installation successful!')
"
```

---

## 🆘 Need Help?

- Check the [README.md](README.md) for features and usage
- Ensure Python 3.11+ is installed: `python --version`
- Verify uv is installed: `uv --version`
- Check your API key is valid at [console.mistral.ai](https://console.mistral.ai/)

---

Happy Investing! 🇮🇳 📈
