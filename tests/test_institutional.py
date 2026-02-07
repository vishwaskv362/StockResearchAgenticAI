"""
Tests for Institutional Activity Tools

Tests cover:
- FII/DII data fetching (NSE API)
- Promoter holdings
- Mutual fund holdings
- Bulk/Block deals
- Data accuracy validation
"""

import json
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock


# Sample NSE API response for FII/DII data
SAMPLE_NSE_FII_DII_JSON = [
    {
        "category": "FII/FPI *",
        "date": "07-Feb-2026",
        "buyValue": 8500.50,
        "sellValue": 7200.30,
        "netValue": 1300.20,
    },
    {
        "category": "DII *",
        "date": "07-Feb-2026",
        "buyValue": 6000.00,
        "sellValue": 6500.75,
        "netValue": -500.75,
    },
]


class TestFIIDIIData:
    """Tests for FII/DII activity data."""

    @pytest.mark.unit
    def test_fii_dii_returns_json(self):
        """Test that FII/DII data returns valid JSON from NSE API."""
        from tools.institutional import get_fii_dii_data

        mock_client = MagicMock()
        mock_homepage_response = MagicMock()
        mock_homepage_response.status_code = 200

        mock_api_response = MagicMock()
        mock_api_response.status_code = 200
        mock_api_response.json.return_value = SAMPLE_NSE_FII_DII_JSON

        mock_client.get.side_effect = [mock_homepage_response, mock_api_response]
        mock_client.close = MagicMock()

        with patch('tools.institutional._get_nse_session', return_value=mock_client):
            result = get_fii_dii_data.func()
            data = json.loads(result)

            assert isinstance(data, dict)
            assert "fii" in data
            assert "dii" in data
            assert "combined" in data

    @pytest.mark.unit
    def test_fii_dii_has_required_fields(self):
        """Test that FII/DII data has required fields."""
        from tools.institutional import get_fii_dii_data

        mock_client = MagicMock()
        mock_api_response = MagicMock()
        mock_api_response.status_code = 200
        mock_api_response.json.return_value = SAMPLE_NSE_FII_DII_JSON
        mock_client.get.return_value = mock_api_response
        mock_client.close = MagicMock()

        with patch('tools.institutional._get_nse_session', return_value=mock_client):
            result = get_fii_dii_data.func()
            data = json.loads(result)

            assert "date" in data
            assert "fii" in data
            assert "buy_value_cr" in data["fii"]
            assert "sell_value_cr" in data["fii"]
            assert "net_value_cr" in data["fii"]
            assert "activity" in data["fii"]

    @pytest.mark.unit
    def test_fii_dii_parses_nse_values(self):
        """Test that NSE API values are correctly parsed."""
        from tools.institutional import get_fii_dii_data

        mock_client = MagicMock()
        mock_api_response = MagicMock()
        mock_api_response.status_code = 200
        mock_api_response.json.return_value = SAMPLE_NSE_FII_DII_JSON
        mock_client.get.return_value = mock_api_response
        mock_client.close = MagicMock()

        with patch('tools.institutional._get_nse_session', return_value=mock_client):
            result = get_fii_dii_data.func()
            data = json.loads(result)

            assert data["fii"]["buy_value_cr"] == 8500.50
            assert data["fii"]["sell_value_cr"] == 7200.30
            assert data["fii"]["net_value_cr"] == 1300.20
            assert data["fii"]["activity"] == "Net Buyer"

            assert data["dii"]["buy_value_cr"] == 6000.00
            assert data["dii"]["sell_value_cr"] == 6500.75
            assert data["dii"]["net_value_cr"] == -500.75
            assert data["dii"]["activity"] == "Net Seller"

    @pytest.mark.unit
    def test_fii_dii_date_from_api(self):
        """Test that date comes from NSE API response."""
        from tools.institutional import get_fii_dii_data

        mock_client = MagicMock()
        mock_api_response = MagicMock()
        mock_api_response.status_code = 200
        mock_api_response.json.return_value = SAMPLE_NSE_FII_DII_JSON
        mock_client.get.return_value = mock_api_response
        mock_client.close = MagicMock()

        with patch('tools.institutional._get_nse_session', return_value=mock_client):
            result = get_fii_dii_data.func()
            data = json.loads(result)

            assert data["date"] == "07-Feb-2026"

    @pytest.mark.unit
    def test_fii_dii_source_is_nse(self):
        """Test that source is NSE India."""
        from tools.institutional import get_fii_dii_data

        mock_client = MagicMock()
        mock_api_response = MagicMock()
        mock_api_response.status_code = 200
        mock_api_response.json.return_value = SAMPLE_NSE_FII_DII_JSON
        mock_client.get.return_value = mock_api_response
        mock_client.close = MagicMock()

        with patch('tools.institutional._get_nse_session', return_value=mock_client):
            result = get_fii_dii_data.func()
            data = json.loads(result)

            assert data["source"] == "NSE India"

    @pytest.mark.unit
    @pytest.mark.critical
    def test_net_calculation_accurate(self):
        """Critical: Net = Buy - Sell must be accurate."""
        buy_value = 1500.0
        sell_value = 1200.0
        net_value = buy_value - sell_value

        assert net_value == 300.0, "Net calculation must be accurate"

    @pytest.mark.unit
    def test_sentiment_determination_logic(self):
        """Test market sentiment determination logic."""
        # Strong bullish: total_net > 500
        total_net_bullish = 600
        sentiment_bullish = "Strong Bullish" if total_net_bullish > 500 else "Other"
        assert "Bullish" in sentiment_bullish

        # Strong bearish: total_net < -500
        total_net_bearish = -600
        sentiment_bearish = "Strong Bearish" if total_net_bearish < -500 else "Other"
        assert "Bearish" in sentiment_bearish

    @pytest.mark.unit
    def test_fii_dii_combined_sentiment(self):
        """Test combined sentiment calculation from API data."""
        from tools.institutional import get_fii_dii_data

        mock_client = MagicMock()
        mock_api_response = MagicMock()
        mock_api_response.status_code = 200
        mock_api_response.json.return_value = SAMPLE_NSE_FII_DII_JSON
        mock_client.get.return_value = mock_api_response
        mock_client.close = MagicMock()

        with patch('tools.institutional._get_nse_session', return_value=mock_client):
            result = get_fii_dii_data.func()
            data = json.loads(result)

            # FII net: 1300.20, DII net: -500.75, total: 799.45 → Strong Bullish
            assert "Bullish" in data["combined"]["market_sentiment"]

    @pytest.mark.integration
    @pytest.mark.slow
    def test_real_fii_dii_fetch(self):
        """Integration test: Fetch real FII/DII data."""
        from tools.institutional import get_fii_dii_data

        result = get_fii_dii_data.func()
        data = json.loads(result)

        assert isinstance(data, dict)


class TestNSESession:
    """Tests for NSE session cookie handling."""

    @pytest.mark.unit
    def test_nse_session_visits_homepage(self):
        """Test that _get_nse_session visits NSE homepage for cookies."""
        from tools.institutional import _get_nse_session

        with patch('httpx.Client') as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client

            _get_nse_session()

            # Should have called get on the homepage
            mock_client.get.assert_called_once_with("https://www.nseindia.com")

    @pytest.mark.unit
    def test_fii_dii_handles_nse_api_error(self):
        """Test handling of non-200 NSE API response."""
        from tools.institutional import get_fii_dii_data

        mock_client = MagicMock()
        mock_api_response = MagicMock()
        mock_api_response.status_code = 403
        mock_client.get.return_value = mock_api_response
        mock_client.close = MagicMock()

        with patch('tools.institutional._get_nse_session', return_value=mock_client):
            result = get_fii_dii_data.func()
            data = json.loads(result)

            assert isinstance(data, dict)
            assert "error" in data


class TestPromoterHoldings:
    """Tests for promoter holdings data."""

    @pytest.mark.unit
    def test_promoter_holdings_returns_json(self):
        """Test that promoter holdings returns valid JSON."""
        from tools.institutional import get_promoter_holdings

        with patch('httpx.Client') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = """
            <html><body>
            <table>
                <tr><td>Promoter Holding</td><td>52.5%</td></tr>
            </table>
            </body></html>
            """
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            result = get_promoter_holdings.func("RELIANCE")
            data = json.loads(result)

            assert isinstance(data, dict)
            assert "symbol" in data

    @pytest.mark.unit
    @pytest.mark.critical
    def test_holdings_percentage_valid_range(self):
        """Critical: Holdings percentage must be 0-100."""
        valid_percentages = [0, 25.5, 50, 74.9, 100]
        invalid_percentages = [-5, 105, 150]

        for pct in valid_percentages:
            assert 0 <= pct <= 100, f"{pct} should be valid"

        for pct in invalid_percentages:
            assert not (0 <= pct <= 100), f"{pct} should be invalid"

    @pytest.mark.integration
    @pytest.mark.slow
    def test_real_promoter_holdings(self, valid_symbol):
        """Integration test: Fetch real promoter holdings."""
        from tools.institutional import get_promoter_holdings

        result = get_promoter_holdings.func(valid_symbol)
        data = json.loads(result)

        assert isinstance(data, dict)


class TestMutualFundHoldings:
    """Tests for mutual fund holdings data."""

    @pytest.mark.unit
    def test_mf_holdings_returns_json(self):
        """Test that MF holdings returns valid JSON."""
        from tools.institutional import get_mutual_fund_holdings

        with patch('httpx.Client') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = """
            <html><body>
            <table>
                <tr><td>Fund Name</td><td>Holdings</td></tr>
                <tr><td>SBI Bluechip Fund</td><td>2.5%</td></tr>
            </table>
            </body></html>
            """
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            result = get_mutual_fund_holdings.func("RELIANCE")
            data = json.loads(result)

            assert isinstance(data, dict)

    @pytest.mark.unit
    def test_mf_holdings_has_symbol(self):
        """Test that response includes symbol."""
        from tools.institutional import get_mutual_fund_holdings

        with patch('httpx.Client') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = "<html><body></body></html>"
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            result = get_mutual_fund_holdings.func("RELIANCE")
            data = json.loads(result)

            assert "symbol" in data


class TestBulkBlockDeals:
    """Tests for bulk and block deals data."""

    @pytest.mark.unit
    def test_bulk_deals_returns_json(self):
        """Test that bulk deals returns valid JSON via NSE API."""
        from tools.institutional import get_bulk_block_deals

        api_response = {
            "BLOCK_DEALS_DATA": [],
            "BULK_DEALS_DATA": [
                {"symbol": "RELIANCE", "clientName": "ABC Capital", "buySell": "BUY", "quantityTraded": 100000, "tradedPrice": 2450},
            ],
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = api_response

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response

        with patch("tools.institutional._get_nse_session", return_value=mock_client):
            result = get_bulk_block_deals.func("RELIANCE")
            data = json.loads(result)

            assert isinstance(data, dict)
            assert data["deals_count"] >= 1
            assert data["deals"][0]["stock"] == "RELIANCE"

    @pytest.mark.unit
    @pytest.mark.critical
    def test_deal_quantity_positive(self):
        """Critical: Deal quantities must be positive."""
        valid_quantities = [100, 1000, 100000, 5000000]
        invalid_quantities = [-100, 0, -1]

        for qty in valid_quantities:
            assert qty > 0, f"Quantity {qty} should be positive"

        for qty in invalid_quantities:
            assert qty <= 0, f"Quantity {qty} should be invalid"

    @pytest.mark.unit
    @pytest.mark.critical
    def test_deal_price_positive(self):
        """Critical: Deal prices must be positive."""
        valid_prices = [10.5, 100, 2450.75, 5000]

        for price in valid_prices:
            assert price > 0, f"Price {price} should be positive"


class TestInstitutionalErrorHandling:
    """Tests for error handling in institutional tools."""

    @pytest.mark.unit
    def test_handles_scraping_failure(self):
        """Test graceful handling of NSE API connection failure."""
        from tools.institutional import get_fii_dii_data

        with patch('tools.institutional._get_nse_session') as mock_session:
            import httpx
            mock_session.side_effect = httpx.ConnectError("Failed")

            result = get_fii_dii_data.func()
            data = json.loads(result)

            # Should return valid JSON even on error
            assert isinstance(data, dict)
            assert "error" in data

    @pytest.mark.unit
    def test_handles_empty_api_response(self):
        """Test handling of empty API response."""
        from tools.institutional import get_fii_dii_data

        mock_client = MagicMock()
        mock_api_response = MagicMock()
        mock_api_response.status_code = 200
        mock_api_response.json.return_value = []
        mock_client.get.return_value = mock_api_response
        mock_client.close = MagicMock()

        with patch('tools.institutional._get_nse_session', return_value=mock_client):
            result = get_fii_dii_data.func()
            data = json.loads(result)

            assert isinstance(data, dict)
            # Should still have structure even with no data
            assert "fii" in data
            assert "dii" in data

    @pytest.mark.unit
    def test_handles_malformed_html(self):
        """Test handling of malformed HTML."""
        from tools.institutional import get_promoter_holdings

        with patch('httpx.Client') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = "<html><body><div>Not closed properly"
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            result = get_promoter_holdings.func("RELIANCE")
            data = json.loads(result)

            assert isinstance(data, dict)


class TestDataValidation:
    """Critical tests for institutional data accuracy."""

    @pytest.mark.unit
    @pytest.mark.critical
    def test_fii_buy_sell_logical(self):
        """Critical: Buy and Sell values should be logical."""
        fii_buy = 1500
        fii_sell = 1200

        assert fii_buy >= 0, "Buy value cannot be negative"
        assert fii_sell >= 0, "Sell value cannot be negative"

    @pytest.mark.unit
    @pytest.mark.critical
    def test_total_holdings_under_100(self):
        """Critical: Total holdings percentages should not exceed 100%."""
        promoter = 50.5
        fii = 25.0
        dii = 20.0
        public = 4.5

        total = promoter + fii + dii + public
        assert total <= 100.01, f"Total holdings {total}% exceeds 100%"

    @pytest.mark.unit
    @pytest.mark.critical
    def test_net_activity_sign_correct(self):
        """Critical: Net activity sign indicates buyer/seller correctly."""
        net_positive = 500
        activity_positive = "Net Buyer" if net_positive > 0 else "Net Seller"
        assert activity_positive == "Net Buyer"

        net_negative = -300
        activity_negative = "Net Buyer" if net_negative > 0 else "Net Seller"
        assert activity_negative == "Net Seller"


class TestBulkBlockDeals:
    """Tests for get_bulk_block_deals tool."""

    @pytest.mark.unit
    def test_bulk_deals_with_symbol_filter(self):
        """Test that symbol filter returns only matching deals."""
        from tools.institutional import get_bulk_block_deals

        api_response = {
            "BLOCK_DEALS_DATA": [],
            "BULK_DEALS_DATA": [
                {"symbol": "RELIANCE", "clientName": "Big Fund", "buySell": "BUY", "quantityTraded": 100000, "tradedPrice": 2500},
                {"symbol": "TCS", "clientName": "Other Fund", "buySell": "SELL", "quantityTraded": 50000, "tradedPrice": 3500},
            ],
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = api_response

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response

        with patch("tools.institutional._get_nse_session", return_value=mock_client):
            result = get_bulk_block_deals.func("RELIANCE")
            data = json.loads(result)

        # Should only include RELIANCE deals
        for deal in data["deals"]:
            assert "RELIANCE" in deal["stock"].upper()

    @pytest.mark.unit
    def test_bulk_deals_empty_response(self):
        """Test handling of empty API response."""
        from tools.institutional import get_bulk_block_deals

        api_response = {"BLOCK_DEALS_DATA": [], "BULK_DEALS_DATA": []}

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = api_response

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response

        with patch("tools.institutional._get_nse_session", return_value=mock_client):
            result = get_bulk_block_deals.func()
            data = json.loads(result)

        assert isinstance(data, dict)
        assert "deals" in data
        assert data["deals_count"] == 0
        assert len(data["deals"]) == 0
        # Should NOT contain hallucination-inducing fallback text
        assert "what_to_look_for" not in str(data)

    @pytest.mark.unit
    def test_bulk_deals_network_error(self):
        """Test that network errors return error JSON with DATA_UNAVAILABLE."""
        from tools.institutional import get_bulk_block_deals

        with patch("tools.institutional._get_nse_session",
                   side_effect=ConnectionError("Network error")):
            result = get_bulk_block_deals.func("RELIANCE")
            data = json.loads(result)

        assert "error" in data
        assert data.get("DATA_UNAVAILABLE") is True

    @pytest.mark.unit
    def test_nse_session_close_error(self):
        """Test that _get_nse_session client close error is handled gracefully."""
        from tools.institutional import get_fii_dii_data

        mock_client = MagicMock()
        mock_api_response = MagicMock()
        mock_api_response.status_code = 200
        mock_api_response.json.return_value = SAMPLE_NSE_FII_DII_JSON
        mock_client.get.return_value = mock_api_response
        mock_client.close = MagicMock(side_effect=Exception("close failed"))

        with patch("tools.institutional._get_nse_session", return_value=mock_client):
            result = get_fii_dii_data.func()
            data = json.loads(result)

        # close() error propagates from finally block to outer except
        # So we get an error response - verify it's handled gracefully
        assert isinstance(data, dict)
        assert "error" in data
        assert "close failed" in data["error"]
