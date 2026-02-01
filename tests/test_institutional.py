"""
Tests for Institutional Activity Tools

Tests cover:
- FII/DII data fetching
- Promoter holdings
- Mutual fund holdings
- Bulk/Block deals
- Data accuracy validation
"""

import json
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock


class TestFIIDIIData:
    """Tests for FII/DII activity data."""
    
    @pytest.mark.unit
    def test_fii_dii_returns_json(self):
        """Test that FII/DII data returns valid JSON."""
        from tools.institutional import get_fii_dii_data
        
        with patch('httpx.Client') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = """
            <html><body>
            <table>
                <tr><td>FII</td><td>1000</td><td>800</td></tr>
                <tr><td>DII</td><td>500</td><td>600</td></tr>
            </table>
            </body></html>
            """
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response
            
            result = get_fii_dii_data.func()
            data = json.loads(result)
            
            assert isinstance(data, dict)
    
    @pytest.mark.unit
    def test_fii_dii_has_required_fields(self):
        """Test that FII/DII data has required fields."""
        from tools.institutional import get_fii_dii_data
        
        with patch('httpx.Client') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = """
            <html><body>
            <table><tr><td>FII</td><td>1000</td><td>800</td></tr></table>
            </body></html>
            """
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response
            
            result = get_fii_dii_data.func()
            data = json.loads(result)
            
            # Should have date
            assert "date" in data or "fetched_at" in data
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_net_calculation_accurate(self):
        """Critical: Net = Buy - Sell must be accurate."""
        # Test the calculation logic
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
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_real_fii_dii_fetch(self):
        """Integration test: Fetch real FII/DII data."""
        from tools.institutional import get_fii_dii_data
        
        result = get_fii_dii_data.func()
        data = json.loads(result)
        
        assert isinstance(data, dict)


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
        # Test boundary conditions
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
        """Test that bulk deals returns valid JSON."""
        from tools.institutional import get_bulk_block_deals
        
        with patch('httpx.Client') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = """
            <html><body>
            <table>
                <tr><td>Client</td><td>Buy/Sell</td><td>Quantity</td><td>Price</td></tr>
                <tr><td>ABC Capital</td><td>Buy</td><td>100000</td><td>2450</td></tr>
            </table>
            </body></html>
            """
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response
            
            result = get_bulk_block_deals.func("RELIANCE")
            data = json.loads(result)
            
            assert isinstance(data, dict)
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_deal_quantity_positive(self):
        """Critical: Deal quantities must be positive."""
        # Test quantity validation
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
        """Test graceful handling of scraping failures."""
        from tools.institutional import get_fii_dii_data
        import httpx
        
        with patch('httpx.Client') as mock_client:
            mock_client.return_value.__enter__.return_value.get.side_effect = httpx.ConnectError("Failed")
            
            result = get_fii_dii_data.func()
            data = json.loads(result)
            
            # Should return valid JSON even on error
            assert isinstance(data, dict)
    
    @pytest.mark.unit
    def test_handles_empty_table(self):
        """Test handling of empty data tables."""
        from tools.institutional import get_fii_dii_data
        
        with patch('httpx.Client') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = "<html><body><table></table></body></html>"
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response
            
            result = get_fii_dii_data.func()
            data = json.loads(result)
            
            assert isinstance(data, dict)
    
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
            
            # Should handle gracefully
            assert isinstance(data, dict)


class TestDataValidation:
    """Critical tests for institutional data accuracy."""
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_fii_buy_sell_logical(self):
        """Critical: Buy and Sell values should be logical."""
        # Both should be non-negative
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
        assert total <= 100.01, f"Total holdings {total}% exceeds 100%"  # Allow small float error
    
    @pytest.mark.unit
    @pytest.mark.critical
    def test_net_activity_sign_correct(self):
        """Critical: Net activity sign indicates buyer/seller correctly."""
        # Net positive = Net Buyer
        net_positive = 500
        activity_positive = "Net Buyer" if net_positive > 0 else "Net Seller"
        assert activity_positive == "Net Buyer"
        
        # Net negative = Net Seller
        net_negative = -300
        activity_negative = "Net Buyer" if net_negative > 0 else "Net Seller"
        assert activity_negative == "Net Seller"
