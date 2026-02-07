"""Tests for Telegram Bot (bot/telegram_bot.py)"""

import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime


@pytest.fixture
def bot_instance():
    with patch.dict("os.environ", {"MISTRAL_API_KEY": "test_key"}):
        from bot.telegram_bot import StockResearchBot

        return StockResearchBot(token="test_token_12345678:ABC")


@pytest.fixture
def mock_update():
    update = MagicMock()
    update.effective_user.id = 12345
    update.effective_user.first_name = "TestUser"
    update.effective_chat.id = 12345
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()
    update.message.text = "RELIANCE"
    update.callback_query = None
    return update


@pytest.fixture
def mock_context():
    context = MagicMock()
    context.args = []
    context.bot.send_chat_action = AsyncMock()
    return context


# ---------------------------------------------------------------------------
# Initialization tests
# ---------------------------------------------------------------------------
class TestStockResearchBotInit:
    """Tests for bot initialization."""

    @pytest.mark.unit
    def test_bot_stores_token(self, bot_instance):
        """Test that StockResearchBot stores the provided token."""
        assert bot_instance.token == "test_token_12345678:ABC"

    @pytest.mark.unit
    def test_bot_application_initially_none(self, bot_instance):
        """Test bot application is None before run()."""
        assert bot_instance.application is None

    @pytest.mark.unit
    def test_bot_has_all_handler_methods(self, bot_instance):
        """Test bot exposes all expected handler methods."""
        expected = [
            "start",
            "help_command",
            "analyze_command",
            "quick_command",
            "technical_command",
            "fundamental_command",
            "news_command",
            "market_command",
            "nifty50_command",
            "sectors_command",
            "handle_callback",
            "handle_message",
            "_send_long_message",
            "setup_commands",
        ]
        for method_name in expected:
            assert hasattr(bot_instance, method_name), f"Missing method: {method_name}"


# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------
class TestModuleConstants:
    """Tests for module-level constants and the run_bot function."""

    @pytest.mark.unit
    def test_request_cooldown_value(self):
        with patch.dict("os.environ", {"MISTRAL_API_KEY": "test_key"}):
            from bot.telegram_bot import REQUEST_COOLDOWN

            assert REQUEST_COOLDOWN == 30

    @pytest.mark.unit
    def test_user_last_request_is_dict(self):
        with patch.dict("os.environ", {"MISTRAL_API_KEY": "test_key"}):
            from bot.telegram_bot import user_last_request

            assert isinstance(user_last_request, dict)


# ---------------------------------------------------------------------------
# /start command
# ---------------------------------------------------------------------------
class TestStartCommand:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_start_sends_welcome_message(self, bot_instance, mock_update, mock_context):
        """Test /start sends a welcome message with user's name."""
        await bot_instance.start(mock_update, mock_context)
        mock_update.message.reply_text.assert_awaited_once()
        call_args = mock_update.message.reply_text.call_args
        text = call_args[0][0] if call_args[0] else call_args[1].get("text", "")
        assert "TestUser" in text
        assert "Namaste" in text


# ---------------------------------------------------------------------------
# /help command
# ---------------------------------------------------------------------------
class TestHelpCommand:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_help_sends_guide(self, bot_instance, mock_update, mock_context):
        """Test /help replies with help guide containing all commands."""
        await bot_instance.help_command(mock_update, mock_context)
        mock_update.message.reply_text.assert_awaited_once()
        text = mock_update.message.reply_text.call_args[0][0]
        for cmd in ["/analyze", "/quick", "/technical", "/fundamental", "/news", "/market"]:
            assert cmd in text


# ---------------------------------------------------------------------------
# /analyze command
# ---------------------------------------------------------------------------
class TestAnalyzeCommand:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_analyze_no_symbol(self, bot_instance, mock_update, mock_context):
        """Test /analyze with no symbol returns error prompt."""
        mock_context.args = []
        await bot_instance.analyze_command(mock_update, mock_context)
        text = mock_update.message.reply_text.call_args[0][0]
        assert "Please provide a stock symbol" in text

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_analyze_rate_limited(self, bot_instance, mock_update, mock_context):
        """Test /analyze is rate limited within cooldown window."""
        from bot.telegram_bot import user_last_request

        mock_context.args = ["RELIANCE"]
        user_last_request[12345] = datetime.now().timestamp()
        try:
            await bot_instance.analyze_command(mock_update, mock_context)
            text = mock_update.message.reply_text.call_args[0][0]
            assert "wait" in text.lower()
        finally:
            user_last_request.pop(12345, None)

    @pytest.mark.unit
    @pytest.mark.asyncio
    @patch("bot.telegram_bot.analyze_stock_sync")
    async def test_analyze_success(self, mock_sync, bot_instance, mock_update, mock_context):
        """Test /analyze succeeds and sends the report."""
        from bot.telegram_bot import user_last_request

        user_last_request.pop(12345, None)

        mock_sync.return_value = "Full analysis report for RELIANCE"
        mock_context.args = ["RELIANCE"]
        status_msg = AsyncMock()
        # reply_text is called first for status, then for final report
        mock_update.message.reply_text = AsyncMock(side_effect=[status_msg, None])
        try:
            await bot_instance.analyze_command(mock_update, mock_context)
            mock_sync.assert_called_once_with("RELIANCE", "full")
            status_msg.delete.assert_awaited_once()
        finally:
            user_last_request.pop(12345, None)

    @pytest.mark.unit
    @pytest.mark.asyncio
    @patch("bot.telegram_bot.analyze_stock_sync", side_effect=RuntimeError("API down"))
    async def test_analyze_handles_error(self, mock_sync, bot_instance, mock_update, mock_context):
        """Test /analyze handles exceptions gracefully."""
        from bot.telegram_bot import user_last_request

        user_last_request.pop(12345, None)

        mock_context.args = ["INFY"]
        status_msg = AsyncMock()
        mock_update.message.reply_text = AsyncMock(return_value=status_msg)
        try:
            await bot_instance.analyze_command(mock_update, mock_context)
            status_msg.edit_text.assert_awaited_once()
            edit_text = status_msg.edit_text.call_args[0][0]
            assert "Error" in edit_text
        finally:
            user_last_request.pop(12345, None)


# ---------------------------------------------------------------------------
# /quick command
# ---------------------------------------------------------------------------
class TestQuickCommand:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_quick_no_symbol(self, bot_instance, mock_update, mock_context):
        """Test /quick with no args returns usage hint."""
        mock_context.args = []
        await bot_instance.quick_command(mock_update, mock_context)
        text = mock_update.message.reply_text.call_args[0][0]
        assert "Please provide a stock symbol" in text

    @pytest.mark.unit
    @pytest.mark.asyncio
    @patch("bot.telegram_bot.get_stock_info")
    @patch("bot.telegram_bot.get_stock_price")
    async def test_quick_success(self, mock_price, mock_info, bot_instance, mock_update, mock_context):
        """Test /quick with valid symbol returns formatted price data."""
        mock_price.run.return_value = json.dumps({
            "current_price": 2847.50,
            "change": 25.30,
            "change_percent": 0.89,
            "high": 2860.00,
            "low": 2820.00,
            "52_week_high": 3000.00,
            "52_week_low": 2200.00,
            "volume": 5000000,
        })
        mock_info.run.return_value = json.dumps({
            "sector": "Energy",
            "industry": "Oil & Gas",
            "market_cap_category": "Large Cap",
        })
        mock_context.args = ["RELIANCE"]
        await bot_instance.quick_command(mock_update, mock_context)
        text = mock_update.message.reply_text.call_args[0][0]
        assert "RELIANCE" in text
        assert "2,847.50" in text

    @pytest.mark.unit
    @pytest.mark.asyncio
    @patch("bot.telegram_bot.get_stock_info")
    @patch("bot.telegram_bot.get_stock_price")
    async def test_quick_error_in_data(self, mock_price, mock_info, bot_instance, mock_update, mock_context):
        """Test /quick when API returns an error key."""
        mock_price.run.return_value = json.dumps({"error": "No data found"})
        mock_info.run.return_value = json.dumps({})
        mock_context.args = ["FAKESYM"]
        await bot_instance.quick_command(mock_update, mock_context)
        text = mock_update.message.reply_text.call_args[0][0]
        assert "Could not find data" in text


# ---------------------------------------------------------------------------
# /technical command
# ---------------------------------------------------------------------------
class TestTechnicalCommand:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_technical_no_symbol(self, bot_instance, mock_update, mock_context):
        """Test /technical with no symbol returns usage hint."""
        mock_context.args = []
        await bot_instance.technical_command(mock_update, mock_context)
        text = mock_update.message.reply_text.call_args[0][0]
        assert "Please provide a stock symbol" in text

    @pytest.mark.unit
    @pytest.mark.asyncio
    @patch("bot.telegram_bot.calculate_technical_indicators")
    async def test_technical_success(self, mock_tech, bot_instance, mock_update, mock_context):
        """Test /technical returns formatted technical analysis."""
        mock_tech.run.return_value = json.dumps({
            "current_price": 1500.0,
            "overall_signal": "BULLISH",
            "moving_averages": {"sma_20": 1480, "sma_50": 1450, "sma_200": 1300, "price_vs_sma20": "ABOVE"},
            "momentum": {"rsi_14": 62, "rsi_interpretation": "Neutral", "macd_line": 5.2, "macd_signal": 3.1},
            "volatility": {"bb_position": "Middle", "atr_percent": 1.8},
            "support_resistance": {"resistance_1": 1520, "support_1": 1470, "pivot": 1495},
            "trend": {"short_term": "UP", "medium_term": "UP", "long_term": "UP"},
            "signals": [{"indicator": "RSI", "signal": "Neutral"}],
        })
        mock_context.args = ["INFY"]
        await bot_instance.technical_command(mock_update, mock_context)
        text = mock_update.message.reply_text.call_args[0][0]
        assert "INFY" in text
        assert "BULLISH" in text

    @pytest.mark.unit
    @pytest.mark.asyncio
    @patch("bot.telegram_bot.calculate_technical_indicators")
    async def test_technical_error_in_response(self, mock_tech, bot_instance, mock_update, mock_context):
        """Test /technical handles error key in tool response."""
        mock_tech.run.return_value = json.dumps({"error": "Insufficient data"})
        mock_context.args = ["BADSTOCK"]
        await bot_instance.technical_command(mock_update, mock_context)
        text = mock_update.message.reply_text.call_args[0][0]
        assert "Insufficient data" in text


# ---------------------------------------------------------------------------
# /fundamental command
# ---------------------------------------------------------------------------
class TestFundamentalCommand:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_fundamental_no_symbol(self, bot_instance, mock_update, mock_context):
        """Test /fundamental with no symbol returns usage hint."""
        mock_context.args = []
        await bot_instance.fundamental_command(mock_update, mock_context)
        text = mock_update.message.reply_text.call_args[0][0]
        assert "Please provide a stock symbol" in text

    @pytest.mark.unit
    @pytest.mark.asyncio
    @patch("bot.telegram_bot.get_fundamental_metrics")
    async def test_fundamental_success(self, mock_fund, bot_instance, mock_update, mock_context):
        """Test /fundamental returns formatted fundamentals."""
        mock_fund.run.return_value = json.dumps({
            "company_name": "HDFC Bank",
            "sector": "Banking",
            "overall_rating": "BUY",
            "score": 78,
            "valuation": {"pe_ratio": 22, "forward_pe": 20, "pb_ratio": 3.5, "ev_ebitda": 15},
            "profitability": {"roe": 17, "roa": 2, "profit_margin": 25},
            "financial_health": {"debt_to_equity": 0.8, "current_ratio": 1.2, "debt_status": "Moderate"},
            "growth": {"earnings_growth": 18, "revenue_growth": 14},
            "dividends": {"dividend_yield": 1.2, "payout_ratio": 24},
            "size": {"market_cap": "8.5T", "revenue": "1.2T"},
        })
        mock_context.args = ["HDFCBANK"]
        await bot_instance.fundamental_command(mock_update, mock_context)
        text = mock_update.message.reply_text.call_args[0][0]
        assert "HDFCBANK" in text
        assert "BUY" in text


# ---------------------------------------------------------------------------
# /news command
# ---------------------------------------------------------------------------
class TestNewsCommand:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_news_no_symbol(self, bot_instance, mock_update, mock_context):
        """Test /news with no symbol returns usage hint."""
        mock_context.args = []
        await bot_instance.news_command(mock_update, mock_context)
        text = mock_update.message.reply_text.call_args[0][0]
        assert "Please provide a stock symbol" in text

    @pytest.mark.unit
    @pytest.mark.asyncio
    @patch("bot.telegram_bot.get_stock_news")
    async def test_news_success_with_articles(self, mock_news, bot_instance, mock_update, mock_context):
        """Test /news returns formatted articles."""
        mock_news.run.return_value = json.dumps({
            "articles": [
                {"title": "Reliance Q3 beats estimates", "source": "ET", "url": "https://example.com/1"},
                {"title": "Jio adds 10M users", "source": "MC", "url": ""},
            ]
        })
        mock_context.args = ["RELIANCE"]
        await bot_instance.news_command(mock_update, mock_context)
        text = mock_update.message.reply_text.call_args[0][0]
        assert "RELIANCE" in text
        assert "Reliance Q3 beats estimates" in text

    @pytest.mark.unit
    @pytest.mark.asyncio
    @patch("bot.telegram_bot.get_stock_news")
    async def test_news_no_articles(self, mock_news, bot_instance, mock_update, mock_context):
        """Test /news when no articles are found."""
        mock_news.run.return_value = json.dumps({"articles": []})
        mock_context.args = ["OBSCURE"]
        await bot_instance.news_command(mock_update, mock_context)
        text = mock_update.message.reply_text.call_args[0][0]
        assert "No recent news" in text


# ---------------------------------------------------------------------------
# /market command
# ---------------------------------------------------------------------------
class TestMarketCommand:
    @pytest.mark.unit
    @pytest.mark.asyncio
    @patch("bot.telegram_bot.get_index_data")
    async def test_market_overview(self, mock_idx, bot_instance, mock_update, mock_context):
        """Test /market returns market overview with index data."""
        mock_idx.run.return_value = json.dumps({
            "NIFTY50": {"value": 22500, "change": 125, "change_percent": 0.56},
            "SENSEX": {"value": 74000, "change": -200, "change_percent": -0.27},
        })
        await bot_instance.market_command(mock_update, mock_context)
        text = mock_update.message.reply_text.call_args[0][0]
        assert "Market Overview" in text


# ---------------------------------------------------------------------------
# /nifty50 command
# ---------------------------------------------------------------------------
class TestNifty50Command:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_nifty50_lists_stocks(self, bot_instance, mock_update, mock_context):
        """Test /nifty50 replies with stock list containing RELIANCE."""
        await bot_instance.nifty50_command(mock_update, mock_context)
        text = mock_update.message.reply_text.call_args[0][0]
        assert "NIFTY 50" in text
        assert "RELIANCE" in text


# ---------------------------------------------------------------------------
# /sectors command
# ---------------------------------------------------------------------------
class TestSectorsCommand:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sectors_lists_sectors(self, bot_instance, mock_update, mock_context):
        """Test /sectors replies with sector information."""
        await bot_instance.sectors_command(mock_update, mock_context)
        text = mock_update.message.reply_text.call_args[0][0]
        assert "Sector" in text
        assert "IT" in text or "BANKING" in text


# ---------------------------------------------------------------------------
# _get_reply_message (static)
# ---------------------------------------------------------------------------
class TestGetReplyMessage:
    @pytest.mark.unit
    def test_returns_message_when_no_callback(self, bot_instance):
        """Test returns update.message when no callback_query."""
        update = MagicMock()
        update.callback_query = None
        update.message = MagicMock(name="direct_message")
        result = bot_instance._get_reply_message(update)
        assert result is update.message

    @pytest.mark.unit
    def test_returns_callback_message_when_callback(self, bot_instance):
        """Test returns callback_query.message when callback_query exists."""
        update = MagicMock()
        update.callback_query = MagicMock()
        update.callback_query.message = MagicMock(name="callback_message")
        result = bot_instance._get_reply_message(update)
        assert result is update.callback_query.message


# ---------------------------------------------------------------------------
# _format_nifty50_list (instance)
# ---------------------------------------------------------------------------
class TestFormatNifty50List:
    @pytest.mark.unit
    def test_format_nifty50_list_content(self, bot_instance):
        """Test _format_nifty50_list returns markdown with stock symbols."""
        text = bot_instance._format_nifty50_list()
        assert "NIFTY 50" in text
        assert "RELIANCE" in text
        assert "TCS" in text


# ---------------------------------------------------------------------------
# _send_long_message
# ---------------------------------------------------------------------------
class TestSendLongMessage:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_short_message_single_send(self, bot_instance, mock_update):
        """Test short message (< 4000 chars) is sent as a single message."""
        short_text = "A short analysis report."
        await bot_instance._send_long_message(mock_update, short_text)
        mock_update.message.reply_text.assert_awaited_once()
        sent_text = mock_update.message.reply_text.call_args[0][0]
        assert sent_text == short_text

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_long_message_split(self, bot_instance, mock_update):
        """Test long message (> 4000 chars) is split into multiple messages."""
        # Build a string with many paragraphs that exceeds 4000 chars
        paragraphs = [f"Paragraph {i}: " + "x" * 200 for i in range(30)]
        long_text = "\n\n".join(paragraphs)
        assert len(long_text) > 4000

        await bot_instance._send_long_message(mock_update, long_text)
        assert mock_update.message.reply_text.await_count >= 2


# ---------------------------------------------------------------------------
# handle_callback
# ---------------------------------------------------------------------------
class TestHandleCallback:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_callback_action_analyze(self, bot_instance, mock_update, mock_context):
        """Test callback for action_analyze replies with instructions."""
        query = AsyncMock()
        query.data = "action_analyze"
        query.message = MagicMock()
        query.message.reply_text = AsyncMock()
        mock_update.callback_query = query
        await bot_instance.handle_callback(mock_update, mock_context)
        query.answer.assert_awaited_once()
        text = query.message.reply_text.call_args[0][0]
        assert "Analyze" in text

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_callback_action_help(self, bot_instance, mock_update, mock_context):
        """Test callback for action_help replies with help hint."""
        query = AsyncMock()
        query.data = "action_help"
        query.message = MagicMock()
        query.message.reply_text = AsyncMock()
        mock_update.callback_query = query
        await bot_instance.handle_callback(mock_update, mock_context)
        query.answer.assert_awaited_once()
        text = query.message.reply_text.call_args[0][0]
        assert "/help" in text

    @pytest.mark.unit
    @pytest.mark.asyncio
    @patch("bot.telegram_bot.calculate_technical_indicators")
    async def test_callback_technical_dispatches(self, mock_tech, bot_instance, mock_update, mock_context):
        """Test callback technical_SYMBOL dispatches to technical_command."""
        mock_tech.run.return_value = json.dumps({
            "current_price": 3400,
            "overall_signal": "NEUTRAL",
            "moving_averages": {},
            "momentum": {},
            "volatility": {},
            "support_resistance": {},
            "trend": {},
            "signals": [],
        })
        query = AsyncMock()
        query.data = "technical_TCS"
        query.message = MagicMock()
        query.message.reply_text = AsyncMock()
        mock_update.callback_query = query
        await bot_instance.handle_callback(mock_update, mock_context)
        query.answer.assert_awaited_once()
        assert mock_context.args == ["TCS"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_callback_action_nifty50(self, bot_instance, mock_update, mock_context):
        """Test callback for action_nifty50 replies with NIFTY 50 list."""
        query = AsyncMock()
        query.data = "action_nifty50"
        query.message = MagicMock()
        query.message.reply_text = AsyncMock()
        mock_update.callback_query = query
        await bot_instance.handle_callback(mock_update, mock_context)
        query.answer.assert_awaited_once()
        text = query.message.reply_text.call_args[0][0]
        assert "NIFTY 50" in text


# ---------------------------------------------------------------------------
# handle_message
# ---------------------------------------------------------------------------
class TestHandleMessage:
    @pytest.mark.unit
    @pytest.mark.asyncio
    @patch("bot.telegram_bot.get_stock_info")
    @patch("bot.telegram_bot.get_stock_price")
    async def test_alphanumeric_dispatches_quick(self, mock_price, mock_info, bot_instance, mock_update, mock_context):
        """Test short alphanumeric text dispatches to quick_command."""
        mock_price.run.return_value = json.dumps({
            "current_price": 2800,
            "change": 10,
            "change_percent": 0.36,
            "high": 2850,
            "low": 2780,
            "52_week_high": 3000,
            "52_week_low": 2200,
            "volume": 1000000,
        })
        mock_info.run.return_value = json.dumps({
            "sector": "Energy",
            "industry": "Oil & Gas",
            "market_cap_category": "Large Cap",
        })
        mock_update.message.text = "RELIANCE"
        await bot_instance.handle_message(mock_update, mock_context)
        # quick_command should have been called, which calls reply_text
        mock_update.message.reply_text.assert_awaited()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_long_text_shows_help(self, bot_instance, mock_update, mock_context):
        """Test long non-symbol text shows help hint."""
        mock_update.message.text = "tell me everything about the stock market in India"
        await bot_instance.handle_message(mock_update, mock_context)
        text = mock_update.message.reply_text.call_args[0][0]
        assert "didn't understand" in text


# ---------------------------------------------------------------------------
# setup_commands
# ---------------------------------------------------------------------------
class TestSetupCommands:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_setup_commands_sets_commands(self, bot_instance):
        """Test setup_commands calls set_my_commands on the application bot."""
        app = MagicMock()
        app.bot.set_my_commands = AsyncMock()
        await bot_instance.setup_commands(app)
        app.bot.set_my_commands.assert_awaited_once()
        commands = app.bot.set_my_commands.call_args[0][0]
        assert len(commands) == 10  # 10 bot commands


# ---------------------------------------------------------------------------
# run() method
# ---------------------------------------------------------------------------
class TestRunMethod:
    @pytest.mark.unit
    def test_run_builds_application_and_adds_handlers(self, bot_instance):
        """Test run() creates Application with handlers."""
        mock_app = MagicMock()
        mock_builder = MagicMock()
        mock_builder.token.return_value = mock_builder
        mock_builder.build.return_value = mock_app

        with patch("bot.telegram_bot.Application") as MockApp:
            MockApp.builder.return_value = mock_builder
            bot_instance.run()

            mock_builder.token.assert_called_once_with("test_token_12345678:ABC")
            mock_builder.build.assert_called_once()
            # 10 command handlers + 1 callback + 1 message = 12
            assert mock_app.add_handler.call_count == 12
            mock_app.run_polling.assert_called_once()


# ---------------------------------------------------------------------------
# run_bot() module function
# ---------------------------------------------------------------------------
class TestRunBotFunction:
    @pytest.mark.unit
    def test_run_bot_no_token_returns_none(self, capsys):
        """Test run_bot prints error and returns when token is empty."""
        with patch.dict("os.environ", {"MISTRAL_API_KEY": "k", "TELEGRAM_BOT_TOKEN": ""}):
            with patch("bot.telegram_bot.settings") as mock_settings:
                mock_settings.telegram_bot_token = ""
                from bot.telegram_bot import run_bot

                result = run_bot()
                assert result is None

    @pytest.mark.unit
    def test_run_bot_with_token_creates_bot(self):
        """Test run_bot creates and runs a StockResearchBot when token is set."""
        with patch.dict("os.environ", {"MISTRAL_API_KEY": "k"}):
            with patch("bot.telegram_bot.settings") as mock_settings:
                mock_settings.telegram_bot_token = "real_token_123:XYZ"
                with patch("bot.telegram_bot.StockResearchBot") as MockBot:
                    mock_bot_inst = MagicMock()
                    MockBot.return_value = mock_bot_inst
                    from bot.telegram_bot import run_bot

                    run_bot()
                    MockBot.assert_called_once_with("real_token_123:XYZ")
                    mock_bot_inst.run.assert_called_once()


# ---------------------------------------------------------------------------
# Command exception handlers
# ---------------------------------------------------------------------------
class TestCommandExceptionHandlers:
    """Tests for exception handling in bot commands."""

    @pytest.fixture
    def bot_instance(self):
        with patch.dict("os.environ", {"MISTRAL_API_KEY": "test"}):
            from bot.telegram_bot import StockResearchBot
            return StockResearchBot(token="12345:ABCtest")

    @pytest.fixture
    def mock_update(self):
        update = AsyncMock()
        update.effective_user.id = 12345
        update.effective_user.first_name = "Test"
        update.effective_chat.id = 12345
        update.message.reply_text = AsyncMock()
        update.callback_query = None
        return update

    @pytest.fixture
    def mock_context(self):
        context = AsyncMock()
        context.args = ["RELIANCE"]
        context.bot.send_chat_action = AsyncMock()
        return context

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_quick_command_exception(self, bot_instance, mock_update, mock_context):
        """Test quick_command handles exceptions gracefully (lines 322-324)."""
        with patch("bot.telegram_bot.get_stock_price") as mock_price:
            mock_price.run = MagicMock(side_effect=ConnectionError("API down"))
            await bot_instance.quick_command(mock_update, mock_context)
        reply_text_calls = mock_update.message.reply_text.call_args_list
        assert any("Error" in str(c) or "error" in str(c).lower() for c in reply_text_calls)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_technical_command_exception(self, bot_instance, mock_update, mock_context):
        """Test technical_command handles exceptions (lines 405-407)."""
        with patch("bot.telegram_bot.calculate_technical_indicators") as mock_tech:
            mock_tech.run = MagicMock(side_effect=ValueError("No data"))
            await bot_instance.technical_command(mock_update, mock_context)
        reply_text_calls = mock_update.message.reply_text.call_args_list
        assert any("Error" in str(c) or "error" in str(c).lower() for c in reply_text_calls)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_fundamental_command_error_data(self, bot_instance, mock_update, mock_context):
        """Test fundamental_command handles error in fund_data (lines 431-432)."""
        with patch("bot.telegram_bot.get_fundamental_metrics") as mock_fund:
            mock_fund.run = MagicMock(return_value=json.dumps({"error": "Symbol not found"}))
            await bot_instance.fundamental_command(mock_update, mock_context)
        reply_text_calls = mock_update.message.reply_text.call_args_list
        assert any("Error" in str(c) or "error" in str(c).lower() for c in reply_text_calls)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_fundamental_command_exception(self, bot_instance, mock_update, mock_context):
        """Test fundamental_command handles exception (lines 493-495)."""
        with patch("bot.telegram_bot.get_fundamental_metrics") as mock_fund:
            mock_fund.run = MagicMock(side_effect=RuntimeError("API error"))
            await bot_instance.fundamental_command(mock_update, mock_context)
        reply_text_calls = mock_update.message.reply_text.call_args_list
        assert any("Error" in str(c) or "error" in str(c).lower() for c in reply_text_calls)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_news_command_exception(self, bot_instance, mock_update, mock_context):
        """Test news_command handles exception (lines 548-550)."""
        with patch("bot.telegram_bot.get_stock_news") as mock_news:
            mock_news.run = MagicMock(side_effect=ConnectionError("Timeout"))
            await bot_instance.news_command(mock_update, mock_context)
        reply_text_calls = mock_update.message.reply_text.call_args_list
        assert any("Error" in str(c) or "error" in str(c).lower() for c in reply_text_calls)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_market_command_exception(self, bot_instance, mock_update, mock_context):
        """Test market_command handles exception (lines 614-616)."""
        with patch("bot.telegram_bot.get_index_data") as mock_idx:
            mock_idx.run = MagicMock(side_effect=RuntimeError("NSE down"))
            await bot_instance.market_command(mock_update, mock_context)
        reply_text_calls = mock_update.message.reply_text.call_args_list
        assert any("Error" in str(c) or "error" in str(c).lower() for c in reply_text_calls)


# ---------------------------------------------------------------------------
# Callback edge cases
# ---------------------------------------------------------------------------
class TestCallbackEdgeCases:
    """Tests for additional callback handler branches."""

    @pytest.fixture
    def bot_instance(self):
        with patch.dict("os.environ", {"MISTRAL_API_KEY": "test"}):
            from bot.telegram_bot import StockResearchBot
            return StockResearchBot(token="12345:ABCtest")

    @pytest.fixture
    def mock_update(self):
        update = AsyncMock()
        update.effective_user.id = 12345
        update.effective_chat.id = 12345
        query = AsyncMock()
        query.message = AsyncMock()
        query.message.reply_text = AsyncMock()
        query.data = ""
        query.answer = AsyncMock()
        update.callback_query = query
        update.message = None
        return update

    @pytest.fixture
    def mock_context(self):
        context = AsyncMock()
        context.args = []
        context.bot.send_chat_action = AsyncMock()
        return context

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_callback_action_quick(self, bot_instance, mock_update, mock_context):
        """Test action_quick callback (line 668)."""
        mock_update.callback_query.data = "action_quick"
        await bot_instance.handle_callback(mock_update, mock_context)
        mock_update.callback_query.message.reply_text.assert_called()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_callback_action_market(self, bot_instance, mock_update, mock_context):
        """Test action_market callback dispatches to market_command (lines 676-677)."""
        mock_update.callback_query.data = "action_market"
        with patch("bot.telegram_bot.get_index_data") as mock_idx:
            mock_idx.run = MagicMock(return_value=json.dumps({
                "NIFTY50": {"value": 22500, "change": 125, "change_percent": 0.56},
            }))
            await bot_instance.handle_callback(mock_update, mock_context)
        mock_update.callback_query.answer.assert_called()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_callback_analyze_prefix(self, bot_instance, mock_update, mock_context):
        """Test analyze_ callback prefix dispatches to analyze_command."""
        mock_update.callback_query.data = "analyze_INFY"
        with patch("bot.telegram_bot.analyze_stock_sync", return_value="## INFY Report\nTest report"):
            await bot_instance.handle_callback(mock_update, mock_context)
        mock_update.callback_query.message.reply_text.assert_called()
        call_str = str(mock_update.callback_query.message.reply_text.call_args)
        assert "INFY" in call_str

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_callback_fundamental_prefix(self, bot_instance, mock_update, mock_context):
        """Test fundamental_ callback prefix (lines 700-703)."""
        mock_update.callback_query.data = "fundamental_RELIANCE"
        with patch("bot.telegram_bot.get_fundamental_metrics") as mock_fund:
            mock_fund.run = MagicMock(return_value=json.dumps({
                "overall_rating": "BUY",
                "score": 78,
                "company_name": "Reliance Industries",
                "sector": "Energy",
                "valuation": {"pe_ratio": "25.0", "forward_pe": "22", "pb_ratio": "3.0", "ev_ebitda": "15"},
                "profitability": {"roe": "18%", "roa": "8%", "profit_margin": "12%"},
                "financial_health": {"debt_to_equity": "0.5", "current_ratio": "1.2", "debt_status": "Low"},
                "dividends": {"dividend_yield": "1.5%", "payout_ratio": "30%"},
                "growth": {"earnings_growth": "12%", "revenue_growth": "10%"},
                "size": {"market_cap": "10L Cr", "revenue": "5L Cr"},
            }))
            await bot_instance.handle_callback(mock_update, mock_context)
        assert mock_update.callback_query.answer.called
        assert mock_context.args == ["RELIANCE"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_callback_news_prefix(self, bot_instance, mock_update, mock_context):
        """Test news_ callback prefix (lines 704-707)."""
        mock_update.callback_query.data = "news_TCS"
        with patch("bot.telegram_bot.get_stock_news") as mock_news:
            mock_news.run = MagicMock(return_value=json.dumps({
                "articles": [{"title": "TCS wins deal", "source": "ET", "url": "https://example.com"}],
                "total_articles": 1,
            }))
            await bot_instance.handle_callback(mock_update, mock_context)
        assert mock_update.callback_query.answer.called
        assert mock_context.args == ["TCS"]


# ---------------------------------------------------------------------------
# Market status time branches
# ---------------------------------------------------------------------------
class TestMarketStatusBranches:
    """Tests for market status time-based branches (lines 590-595)."""

    @pytest.fixture
    def bot_instance(self):
        with patch.dict("os.environ", {"MISTRAL_API_KEY": "test"}):
            from bot.telegram_bot import StockResearchBot
            return StockResearchBot(token="12345:ABCtest")

    @pytest.fixture
    def mock_update(self):
        update = AsyncMock()
        update.effective_user.id = 12345
        update.effective_chat.id = 12345
        update.message.reply_text = AsyncMock()
        update.callback_query = None
        return update

    @pytest.fixture
    def mock_context(self):
        context = AsyncMock()
        context.args = []
        context.bot.send_chat_action = AsyncMock()
        return context

    def _make_index_json(self):
        return json.dumps({
            "NIFTY50": {"value": 22500, "change": 150, "change_percent": 0.67},
            "SENSEX": {"value": 74000, "change": 400, "change_percent": 0.54},
        })

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_market_weekend(self, bot_instance, mock_update, mock_context):
        """Market should show closed on weekend (line 589)."""
        # Saturday: weekday() == 5
        weekend_dt = datetime(2026, 2, 7, 12, 0)  # Saturday Feb 7 2026
        with patch("bot.telegram_bot.get_index_data") as mock_idx, \
             patch("bot.telegram_bot.datetime") as mock_dt:
            mock_idx.run = MagicMock(return_value=self._make_index_json())
            mock_dt.now.return_value = weekend_dt
            mock_dt.side_effect = lambda *a, **k: datetime(*a, **k)
            await bot_instance.market_command(mock_update, mock_context)
        call_str = str(mock_update.message.reply_text.call_args)
        assert "Weekend" in call_str

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_market_pre_market(self, bot_instance, mock_update, mock_context):
        """Market should show pre-market before 9:15 on a weekday (line 590-591)."""
        # Monday 8:30 AM
        pre_market_dt = datetime(2026, 2, 9, 8, 30)  # Monday
        with patch("bot.telegram_bot.get_index_data") as mock_idx, \
             patch("bot.telegram_bot.datetime") as mock_dt:
            mock_idx.run = MagicMock(return_value=self._make_index_json())
            mock_dt.now.return_value = pre_market_dt
            mock_dt.side_effect = lambda *a, **k: datetime(*a, **k)
            await bot_instance.market_command(mock_update, mock_context)
        call_str = str(mock_update.message.reply_text.call_args)
        assert "Pre-Market" in call_str

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_market_open(self, bot_instance, mock_update, mock_context):
        """Market should show open during trading hours (lines 592-593)."""
        # Monday 11:00 AM
        open_dt = datetime(2026, 2, 9, 11, 0)
        with patch("bot.telegram_bot.get_index_data") as mock_idx, \
             patch("bot.telegram_bot.datetime") as mock_dt:
            mock_idx.run = MagicMock(return_value=self._make_index_json())
            mock_dt.now.return_value = open_dt
            mock_dt.side_effect = lambda *a, **k: datetime(*a, **k)
            await bot_instance.market_command(mock_update, mock_context)
        call_str = str(mock_update.message.reply_text.call_args)
        assert "Market Open" in call_str

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_market_closed_after_hours(self, bot_instance, mock_update, mock_context):
        """Market should show closed after 15:30 on a weekday (lines 594-595)."""
        # Monday 4:00 PM
        closed_dt = datetime(2026, 2, 9, 16, 0)
        with patch("bot.telegram_bot.get_index_data") as mock_idx, \
             patch("bot.telegram_bot.datetime") as mock_dt:
            mock_idx.run = MagicMock(return_value=self._make_index_json())
            mock_dt.now.return_value = closed_dt
            mock_dt.side_effect = lambda *a, **k: datetime(*a, **k)
            await bot_instance.market_command(mock_update, mock_context)
        call_str = str(mock_update.message.reply_text.call_args)
        assert "Market Closed" in call_str
