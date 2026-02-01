#!/usr/bin/env python3
"""
Main entry point to run the Telegram bot
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from bot.telegram_bot import run_bot
from config import settings


def main():
    """Run the Stock Research Telegram Bot."""
    print("=" * 50)
    print("🚀 Stock Research Assistant - Telegram Bot")
    print("=" * 50)
    
    # Validate configuration
    if not settings.telegram_bot_token:
        print("\n❌ Error: TELEGRAM_BOT_TOKEN is not set!")
        print("\nPlease:")
        print("1. Create a .env file in the project root")
        print("2. Add: TELEGRAM_BOT_TOKEN=your_bot_token_here")
        print("\nTo get a bot token:")
        print("1. Open Telegram and search for @BotFather")
        print("2. Send /newbot and follow instructions")
        print("3. Copy the token and add it to .env")
        sys.exit(1)
    
    if not settings.mistral_api_key:
        print("\n⚠️  Warning: MISTRAL_API_KEY is not set!")
        print("Full AI analysis will not work.")
        print("\nTo get a Mistral API key:")
        print("1. Go to https://console.mistral.ai/")
        print("2. Create an account and get an API key")
        print("3. Add to .env: MISTRAL_API_KEY=your_key_here")
        print("\nContinuing with limited functionality...\n")
    
    print(f"\n📱 Bot Token: ...{settings.telegram_bot_token[-10:]}")
    print(f"🤖 LLM Model: {settings.llm_model}")
    print(f"📊 Cache TTL: {settings.cache_ttl_minutes} minutes")
    print("\n" + "=" * 50)
    print("Bot is starting... Press Ctrl+C to stop")
    print("=" * 50 + "\n")
    
    try:
        run_bot()
    except KeyboardInterrupt:
        print("\n\n👋 Bot stopped. Goodbye!")


if __name__ == "__main__":
    main()
