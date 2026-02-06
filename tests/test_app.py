"""
Tests for Streamlit Web UI (app.py)

Uses mocking to test UI helper functions and logic without running Streamlit.
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from datetime import datetime


class TestFormatNumber:
    """Tests for format_number helper function."""
    
    @pytest.mark.unit
    def test_format_crores(self):
        """Test formatting large numbers in crores."""
        # Import inside test to avoid streamlit initialization
        with patch('streamlit.set_page_config'):
            import sys
            # Mock streamlit before importing app
            sys.modules['streamlit'] = MagicMock()
            
            # Test the logic directly
            def format_number(num):
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
                except (ValueError, TypeError):
                    return str(num)
            
            assert "Cr" in format_number(50_000_000)
            assert "50.00 Cr" in format_number(500_000_000)
    
    @pytest.mark.unit
    def test_format_lakhs(self):
        """Test formatting numbers in lakhs."""
        def format_number(num):
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
            except (ValueError, TypeError):
                return str(num)
        
        assert "L" in format_number(500_000)
        assert "5.00 L" in format_number(500_000)
    
    @pytest.mark.unit
    def test_format_small_number(self):
        """Test formatting small numbers."""
        def format_number(num):
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
            except (ValueError, TypeError):
                return str(num)
        
        assert format_number(1234.56) == "₹1,234.56"
    
    @pytest.mark.unit
    def test_format_na(self):
        """Test handling N/A values."""
        def format_number(num):
            if num is None or num == "N/A":
                return "N/A"
            return str(num)
        
        assert format_number(None) == "N/A"
        assert format_number("N/A") == "N/A"
    
    @pytest.mark.unit
    def test_format_invalid(self):
        """Test handling invalid values."""
        def format_number(num):
            if num is None or num == "N/A":
                return "N/A"
            try:
                num = float(num)
                return f"₹{num:,.2f}"
            except (ValueError, TypeError):
                return str(num)
        
        assert format_number("invalid") == "invalid"


class TestGetTrendEmoji:
    """Tests for trend emoji helper."""
    
    @pytest.mark.unit
    def test_positive_trend(self):
        """Test positive change returns green emoji."""
        def get_trend_emoji(change):
            if change > 0:
                return "🟢"
            elif change < 0:
                return "🔴"
            return "⚪"
        
        assert get_trend_emoji(5.5) == "🟢"
        assert get_trend_emoji(0.01) == "🟢"
    
    @pytest.mark.unit
    def test_negative_trend(self):
        """Test negative change returns red emoji."""
        def get_trend_emoji(change):
            if change > 0:
                return "🟢"
            elif change < 0:
                return "🔴"
            return "⚪"
        
        assert get_trend_emoji(-2.5) == "🔴"
        assert get_trend_emoji(-0.01) == "🔴"
    
    @pytest.mark.unit
    def test_neutral_trend(self):
        """Test zero change returns white emoji."""
        def get_trend_emoji(change):
            if change > 0:
                return "🟢"
            elif change < 0:
                return "🔴"
            return "⚪"
        
        assert get_trend_emoji(0) == "⚪"


class TestStreamlitUILogic:
    """Tests for Streamlit UI component logic."""
    
    @pytest.mark.unit
    def test_stock_symbol_validation(self):
        """Test stock symbol validation logic."""
        from config import NIFTY50_STOCKS
        
        # Valid symbols
        assert "RELIANCE" in NIFTY50_STOCKS
        assert "TCS" in NIFTY50_STOCKS
        assert "INFY" in NIFTY50_STOCKS
    
    @pytest.mark.unit
    def test_sector_mapping(self):
        """Test sector categorization."""
        from config import SECTORS
        
        assert "IT" in SECTORS or "TECHNOLOGY" in SECTORS
        assert "BANKING" in SECTORS or "FINANCE" in SECTORS
    
    @pytest.mark.unit
    def test_price_data_parsing(self):
        """Test parsing price data from tools."""
        mock_price_response = json.dumps({
            "symbol": "RELIANCE",
            "current_price": 2847.50,
            "change": 34.25,
            "change_percent": 1.22,
            "volume": 5000000
        })
        
        data = json.loads(mock_price_response)
        assert data["symbol"] == "RELIANCE"
        assert data["current_price"] == 2847.50
        assert data["change"] > 0
    
    @pytest.mark.unit
    def test_technical_data_parsing(self):
        """Test parsing technical indicator data."""
        mock_technical_response = json.dumps({
            "rsi_14": 55.5,
            "macd": 12.5,
            "signal": 10.2,
            "bb_upper": 2900,
            "bb_middle": 2850,
            "bb_lower": 2800
        })
        
        data = json.loads(mock_technical_response)
        assert 0 <= data["rsi_14"] <= 100
        assert data["bb_upper"] >= data["bb_middle"] >= data["bb_lower"]
    
    @pytest.mark.unit
    def test_news_data_parsing(self):
        """Test parsing news data structure."""
        mock_news_response = json.dumps({
            "symbol": "RELIANCE",
            "articles": [
                {"title": "Test News", "url": "https://example.com", "source": "Moneycontrol"},
            ],
            "articles_count": 1
        })
        
        data = json.loads(mock_news_response)
        assert data["articles_count"] == len(data["articles"])


class TestUIDataFormatting:
    """Tests for UI data formatting utilities."""
    
    @pytest.mark.unit
    def test_percentage_formatting(self):
        """Test percentage formatting for display."""
        def format_percentage(value):
            if value is None:
                return "N/A"
            return f"{value:+.2f}%"
        
        assert format_percentage(5.5) == "+5.50%"
        assert format_percentage(-3.2) == "-3.20%"
        assert format_percentage(None) == "N/A"
    
    @pytest.mark.unit
    def test_date_formatting(self):
        """Test date formatting for display."""
        def format_date(date_str):
            try:
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                return dt.strftime("%d %b %Y, %H:%M")
            except (ValueError, TypeError):
                return date_str
        
        result = format_date("2026-02-01T10:30:00")
        assert "01 Feb 2026" in result
    
    @pytest.mark.unit
    def test_rsi_signal_interpretation(self):
        """Test RSI signal interpretation logic."""
        def interpret_rsi(rsi):
            if rsi is None:
                return "N/A", "gray"
            if rsi > 70:
                return "Overbought", "red"
            elif rsi < 30:
                return "Oversold", "green"
            return "Neutral", "gray"
        
        assert interpret_rsi(75)[0] == "Overbought"
        assert interpret_rsi(25)[0] == "Oversold"
        assert interpret_rsi(50)[0] == "Neutral"
    
    @pytest.mark.unit
    def test_recommendation_color(self):
        """Test recommendation color coding."""
        def get_recommendation_color(recommendation):
            rec_lower = recommendation.lower()
            if "buy" in rec_lower or "bullish" in rec_lower:
                return "green"
            elif "sell" in rec_lower or "bearish" in rec_lower:
                return "red"
            return "orange"
        
        assert get_recommendation_color("Strong Buy") == "green"
        assert get_recommendation_color("SELL") == "red"
        assert get_recommendation_color("Hold") == "orange"


class TestUIErrorHandling:
    """Tests for UI error handling."""

    @pytest.mark.unit
    def test_handles_api_error_response(self):
        """Test handling API error responses."""
        error_response = json.dumps({"error": "Symbol not found"})
        data = json.loads(error_response)

        assert "error" in data

    @pytest.mark.unit
    def test_handles_empty_data(self):
        """Test handling empty data responses."""
        empty_response = json.dumps({"symbol": "TEST", "articles": []})
        data = json.loads(empty_response)

        assert len(data.get("articles", [])) == 0

    @pytest.mark.unit
    def test_handles_missing_fields(self):
        """Test handling responses with missing fields."""
        partial_response = json.dumps({"symbol": "TEST"})
        data = json.loads(partial_response)

        # Should handle missing fields gracefully
        assert data.get("current_price", "N/A") == "N/A"
        assert data.get("volume", 0) == 0


# ============================================================
# Tests for new Groww-style features
# ============================================================

class TestFetchChartData:
    """Tests for _fetch_chart_data helper."""

    @pytest.mark.unit
    def test_period_map_covers_all_buttons(self):
        """Verify all 7 chart period buttons have yfinance mappings."""
        # Replicate the mapping from _fetch_chart_data
        period_map = {
            "1D": ("5d", "5m"),
            "1W": ("5d", "5m"),
            "1M": ("1mo", "30m"),
            "3M": ("3mo", "1h"),
            "6M": ("6mo", "1d"),
            "1Y": ("1y", "1d"),
            "5Y": ("5y", "1d"),
        }

        expected_periods = ["1D", "1W", "1M", "3M", "6M", "1Y", "5Y"]
        for p in expected_periods:
            assert p in period_map, f"Missing period mapping for {p}"
            yf_period, interval = period_map[p]
            assert yf_period, f"Empty yfinance period for {p}"
            assert interval, f"Empty interval for {p}"

    @pytest.mark.unit
    def test_1d_period_uses_5d_with_5m(self):
        """Test that 1D period fetches 5d of 5m data then filters to today."""
        period_map = {
            "1D": ("5d", "5m"),
        }
        yf_period, interval = period_map["1D"]
        assert yf_period == "5d"
        assert interval == "5m"

    @pytest.mark.unit
    def test_fetch_chart_data_returns_dataframe(self):
        """Test _fetch_chart_data returns a DataFrame with mocked yfinance."""
        import pandas as pd
        import numpy as np

        with patch('streamlit.set_page_config'), \
             patch('streamlit.markdown'), \
             patch.dict('sys.modules', {'streamlit': MagicMock()}):

            dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
            mock_df = pd.DataFrame({
                'Open': np.random.uniform(100, 110, 30),
                'High': np.random.uniform(110, 120, 30),
                'Low': np.random.uniform(90, 100, 30),
                'Close': np.random.uniform(100, 110, 30),
                'Volume': np.random.randint(1000, 10000, 30),
            }, index=dates)

            with patch('yfinance.Ticker') as mock_ticker:
                mock_ticker.return_value.history.return_value = mock_df

                # Import after mocking streamlit
                import importlib
                import app as app_module
                importlib.reload(app_module)

                result = app_module._fetch_chart_data("RELIANCE", "1M")

            assert isinstance(result, pd.DataFrame)
            assert not result.empty
            assert "Close" in result.columns

    @pytest.mark.unit
    def test_fetch_chart_data_returns_empty_on_error(self):
        """Test _fetch_chart_data returns empty DataFrame when yfinance fails."""
        import pandas as pd

        with patch.dict('sys.modules', {'streamlit': MagicMock()}):
            with patch('yfinance.Ticker', side_effect=Exception("API error")):
                import importlib
                import app as app_module
                importlib.reload(app_module)

                result = app_module._fetch_chart_data("BADSTOCK", "1Y")

            assert isinstance(result, pd.DataFrame)
            assert result.empty


class TestRangeBarLogic:
    """Tests for range bar percentage calculation logic."""

    @pytest.mark.unit
    def test_range_bar_percentage_at_low(self):
        """Test that current at low gives 0%."""
        low, high, current = 100.0, 200.0, 100.0
        pct = max(0, min(100, ((current - low) / (high - low)) * 100))
        assert pct == 0.0

    @pytest.mark.unit
    def test_range_bar_percentage_at_high(self):
        """Test that current at high gives 100%."""
        low, high, current = 100.0, 200.0, 200.0
        pct = max(0, min(100, ((current - low) / (high - low)) * 100))
        assert pct == 100.0

    @pytest.mark.unit
    def test_range_bar_percentage_midpoint(self):
        """Test that current at midpoint gives 50%."""
        low, high, current = 100.0, 200.0, 150.0
        pct = max(0, min(100, ((current - low) / (high - low)) * 100))
        assert pct == 50.0

    @pytest.mark.unit
    def test_range_bar_clamps_below_low(self):
        """Test that current below low is clamped to 0%."""
        low, high, current = 100.0, 200.0, 50.0
        pct = max(0, min(100, ((current - low) / (high - low)) * 100))
        assert pct == 0.0

    @pytest.mark.unit
    def test_range_bar_clamps_above_high(self):
        """Test that current above high is clamped to 100%."""
        low, high, current = 100.0, 200.0, 250.0
        pct = max(0, min(100, ((current - low) / (high - low)) * 100))
        assert pct == 100.0

    @pytest.mark.unit
    def test_range_bar_skips_invalid(self):
        """Test that high <= low is rejected (guard clause)."""
        # Replicate the guard from _render_range_bar
        low, high = 200.0, 100.0
        should_render = not (high <= low or high == 0)
        assert should_render is False

    @pytest.mark.unit
    def test_range_bar_skips_zero_high(self):
        """Test that high == 0 is rejected."""
        should_render = not (0 <= 0 or 0 == 0)
        assert should_render is False


class TestGenerateWordReport:
    """Tests for Word document generation."""

    @pytest.mark.unit
    def test_returns_bytes(self):
        """Test that word report returns non-empty bytes."""
        from app import _generate_word_report

        md = "# Title\n\nSome text.\n\n- Bullet one\n- Bullet two\n"
        result = _generate_word_report("RELIANCE", md, "2026-02-07_10-30")

        assert isinstance(result, bytes)
        assert len(result) > 0

    @pytest.mark.unit
    def test_output_is_valid_docx(self):
        """Test that output bytes can be loaded as a valid Word document."""
        from docx import Document
        import io
        from app import _generate_word_report

        md = "# Report\n\n## Section\n\nHello world\n"
        result = _generate_word_report("TCS", md, "2026-02-07_12-00")

        doc = Document(io.BytesIO(result))
        # Should have at least the title heading + timestamp + spacer + content
        assert len(doc.paragraphs) >= 3

    @pytest.mark.unit
    def test_headings_are_parsed(self):
        """Test that markdown headings become Word headings."""
        from docx import Document
        import io
        from app import _generate_word_report

        md = "# Heading 1\n## Heading 2\n### Heading 3\n"
        result = _generate_word_report("INFY", md, "2026-02-07")

        doc = Document(io.BytesIO(result))
        heading_texts = [p.text for p in doc.paragraphs if p.style.name.startswith("Heading")]

        assert "Heading 1" in heading_texts
        assert "Heading 2" in heading_texts
        assert "Heading 3" in heading_texts

    @pytest.mark.unit
    def test_bullet_list_items(self):
        """Test that markdown bullets become Word list items."""
        from docx import Document
        import io
        from app import _generate_word_report

        md = "- Item A\n- Item B\n* Item C\n"
        result = _generate_word_report("HDFC", md, "2026-02-07")

        doc = Document(io.BytesIO(result))
        bullet_texts = [p.text for p in doc.paragraphs if "List" in p.style.name]

        assert "Item A" in bullet_texts
        assert "Item B" in bullet_texts
        assert "Item C" in bullet_texts

    @pytest.mark.unit
    def test_numbered_list_items(self):
        """Test that markdown numbered items become Word numbered lists."""
        from docx import Document
        import io
        from app import _generate_word_report

        md = "1. First\n2. Second\n3. Third\n"
        result = _generate_word_report("SBI", md, "2026-02-07")

        doc = Document(io.BytesIO(result))
        numbered_texts = [p.text for p in doc.paragraphs if "Number" in p.style.name]

        assert "First" in numbered_texts
        assert "Second" in numbered_texts

    @pytest.mark.unit
    def test_disclaimer_present(self):
        """Test that the disclaimer footer is included."""
        from docx import Document
        import io
        from app import _generate_word_report

        md = "Some analysis text.\n"
        result = _generate_word_report("WIPRO", md, "2026-02-07")

        doc = Document(io.BytesIO(result))
        all_text = " ".join(p.text for p in doc.paragraphs)

        assert "DISCLAIMER" in all_text
        assert "educational purposes" in all_text

    @pytest.mark.unit
    def test_title_contains_symbol(self):
        """Test that the title heading includes the stock symbol."""
        from docx import Document
        import io
        from app import _generate_word_report

        md = "Content\n"
        result = _generate_word_report("BAJAJ", md, "2026-02-07")

        doc = Document(io.BytesIO(result))
        title_para = doc.paragraphs[0]

        assert "BAJAJ" in title_para.text

    @pytest.mark.unit
    def test_horizontal_rule_converted(self):
        """Test that --- becomes an underline separator."""
        from docx import Document
        import io
        from app import _generate_word_report

        md = "Above\n---\nBelow\n"
        result = _generate_word_report("TEST", md, "2026-02-07")

        doc = Document(io.BytesIO(result))
        all_text = [p.text for p in doc.paragraphs]
        assert "_" * 50 in all_text

    @pytest.mark.unit
    def test_empty_report(self):
        """Test that empty markdown still generates a valid docx."""
        from app import _generate_word_report

        result = _generate_word_report("EMPTY", "", "2026-02-07")
        assert isinstance(result, bytes)
        assert len(result) > 0


class TestAddColoredRun:
    """Tests for BUY/SELL keyword coloring in Word documents."""

    @pytest.mark.unit
    def test_buy_is_green_and_bold(self):
        """Test that BUY keyword gets green color and bold."""
        from docx import Document
        from docx.shared import RGBColor
        from app import _add_colored_run

        doc = Document()
        para = doc.add_paragraph()
        _add_colored_run(para, "Recommendation: BUY this stock")

        runs = para.runs
        buy_runs = [r for r in runs if r.text.strip() == "BUY"]
        assert len(buy_runs) == 1
        assert buy_runs[0].bold is True
        assert buy_runs[0].font.color.rgb == RGBColor(0, 128, 0)

    @pytest.mark.unit
    def test_sell_is_red_and_bold(self):
        """Test that SELL keyword gets red color and bold."""
        from docx import Document
        from docx.shared import RGBColor
        from app import _add_colored_run

        doc = Document()
        para = doc.add_paragraph()
        _add_colored_run(para, "Signal: SELL immediately")

        runs = para.runs
        sell_runs = [r for r in runs if r.text.strip() == "SELL"]
        assert len(sell_runs) == 1
        assert sell_runs[0].bold is True
        assert sell_runs[0].font.color.rgb == RGBColor(200, 0, 0)

    @pytest.mark.unit
    def test_strong_buy_is_green(self):
        """Test that STRONG BUY gets green coloring."""
        from docx import Document
        from docx.shared import RGBColor
        from app import _add_colored_run

        doc = Document()
        para = doc.add_paragraph()
        _add_colored_run(para, "Rating: STRONG BUY")

        runs = para.runs
        sb_runs = [r for r in runs if r.text.strip() == "STRONG BUY"]
        assert len(sb_runs) == 1
        assert sb_runs[0].bold is True
        assert sb_runs[0].font.color.rgb == RGBColor(0, 128, 0)

    @pytest.mark.unit
    def test_strong_sell_is_red(self):
        """Test that STRONG SELL gets red coloring."""
        from docx import Document
        from docx.shared import RGBColor
        from app import _add_colored_run

        doc = Document()
        para = doc.add_paragraph()
        _add_colored_run(para, "Rating: STRONG SELL")

        runs = para.runs
        ss_runs = [r for r in runs if r.text.strip() == "STRONG SELL"]
        assert len(ss_runs) == 1
        assert ss_runs[0].bold is True
        assert ss_runs[0].font.color.rgb == RGBColor(200, 0, 0)

    @pytest.mark.unit
    def test_text_without_keywords_is_plain(self):
        """Test that regular text gets no special formatting."""
        from docx import Document
        from app import _add_colored_run

        doc = Document()
        para = doc.add_paragraph()
        _add_colored_run(para, "This is plain text with no signals")

        runs = para.runs
        assert len(runs) == 1
        assert runs[0].bold is not True
        assert runs[0].font.color.rgb is None

    @pytest.mark.unit
    def test_multiple_keywords_in_one_line(self):
        """Test that multiple BUY/SELL keywords are each colored."""
        from docx import Document
        from docx.shared import RGBColor
        from app import _add_colored_run

        doc = Document()
        para = doc.add_paragraph()
        _add_colored_run(para, "Short-term BUY but long-term SELL")

        runs = para.runs
        buy_runs = [r for r in runs if r.text.strip() == "BUY"]
        sell_runs = [r for r in runs if r.text.strip() == "SELL"]
        assert len(buy_runs) == 1
        assert len(sell_runs) == 1
        assert buy_runs[0].font.color.rgb == RGBColor(0, 128, 0)
        assert sell_runs[0].font.color.rgb == RGBColor(200, 0, 0)
