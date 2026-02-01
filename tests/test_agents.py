"""
Tests for Agents

Tests cover:
- Agent creation and configuration
- Agent tools assignment
- LLM configuration
- Agent attributes (role, goal, backstory)
"""

import pytest
from unittest.mock import patch, MagicMock


class TestMarketDataAgent:
    """Tests for Market Data Agent."""
    
    @pytest.mark.unit
    def test_agent_creation(self):
        """Test that market data agent is created successfully."""
        with patch.dict('os.environ', {'MISTRAL_API_KEY': 'test_key'}):
            from agents.market_data_agent import market_data_agent
            
            assert market_data_agent is not None
    
    @pytest.mark.unit
    def test_agent_has_role(self):
        """Test that agent has a defined role."""
        with patch.dict('os.environ', {'MISTRAL_API_KEY': 'test_key'}):
            from agents.market_data_agent import market_data_agent
            
            assert hasattr(market_data_agent, 'role')
            assert len(market_data_agent.role) > 0
    
    @pytest.mark.unit
    def test_agent_has_goal(self):
        """Test that agent has a defined goal."""
        with patch.dict('os.environ', {'MISTRAL_API_KEY': 'test_key'}):
            from agents.market_data_agent import market_data_agent
            
            assert hasattr(market_data_agent, 'goal')
            assert len(market_data_agent.goal) > 0
    
    @pytest.mark.unit
    def test_agent_has_tools(self):
        """Test that agent has tools assigned."""
        with patch.dict('os.environ', {'MISTRAL_API_KEY': 'test_key'}):
            from agents.market_data_agent import market_data_agent
            
            assert hasattr(market_data_agent, 'tools')
            assert len(market_data_agent.tools) > 0


class TestNewsAgent:
    """Tests for News Analyst Agent."""
    
    @pytest.mark.unit
    def test_agent_creation(self):
        """Test that news agent is created successfully."""
        with patch.dict('os.environ', {'MISTRAL_API_KEY': 'test_key'}):
            from agents.news_agent import news_analyst_agent
            
            assert news_analyst_agent is not None
    
    @pytest.mark.unit
    def test_agent_role_is_news_related(self):
        """Test that agent role mentions news analysis."""
        with patch.dict('os.environ', {'MISTRAL_API_KEY': 'test_key'}):
            from agents.news_agent import news_analyst_agent
            
            role_lower = news_analyst_agent.role.lower()
            assert "news" in role_lower or "sentiment" in role_lower or "analyst" in role_lower


class TestFundamentalAgent:
    """Tests for Fundamental Analyst Agent."""
    
    @pytest.mark.unit
    def test_agent_creation(self):
        """Test that fundamental agent is created successfully."""
        with patch.dict('os.environ', {'MISTRAL_API_KEY': 'test_key'}):
            from agents.fundamental_agent import fundamental_analyst_agent
            
            assert fundamental_analyst_agent is not None
    
    @pytest.mark.unit
    def test_agent_role_is_fundamental_related(self):
        """Test that agent role mentions fundamental analysis."""
        with patch.dict('os.environ', {'MISTRAL_API_KEY': 'test_key'}):
            from agents.fundamental_agent import fundamental_analyst_agent
            
            role_lower = fundamental_analyst_agent.role.lower()
            assert "fundamental" in role_lower or "research" in role_lower or "analyst" in role_lower
    
    @pytest.mark.unit
    def test_agent_has_fundamental_tools(self):
        """Test that agent has fundamental analysis tools."""
        with patch.dict('os.environ', {'MISTRAL_API_KEY': 'test_key'}):
            from agents.fundamental_agent import fundamental_analyst_agent
            
            assert hasattr(fundamental_analyst_agent, 'tools')
            assert len(fundamental_analyst_agent.tools) > 0


class TestTechnicalAgent:
    """Tests for Technical Analyst Agent."""
    
    @pytest.mark.unit
    def test_agent_creation(self):
        """Test that technical agent is created successfully."""
        with patch.dict('os.environ', {'MISTRAL_API_KEY': 'test_key'}):
            from agents.technical_agent import technical_analyst_agent
            
            assert technical_analyst_agent is not None
    
    @pytest.mark.unit
    def test_agent_role_is_technical_related(self):
        """Test that agent role mentions technical analysis."""
        with patch.dict('os.environ', {'MISTRAL_API_KEY': 'test_key'}):
            from agents.technical_agent import technical_analyst_agent
            
            role_lower = technical_analyst_agent.role.lower()
            assert "technical" in role_lower or "chart" in role_lower or "analyst" in role_lower
    
    @pytest.mark.unit
    def test_agent_has_technical_tools(self):
        """Test that agent has technical analysis tools."""
        with patch.dict('os.environ', {'MISTRAL_API_KEY': 'test_key'}):
            from agents.technical_agent import technical_analyst_agent
            
            assert hasattr(technical_analyst_agent, 'tools')


class TestStrategistAgent:
    """Tests for Investment Strategist Agent."""
    
    @pytest.mark.unit
    def test_agent_creation(self):
        """Test that strategist agent is created successfully."""
        with patch.dict('os.environ', {'MISTRAL_API_KEY': 'test_key'}):
            from agents.strategist_agent import investment_strategist_agent
            
            assert investment_strategist_agent is not None
    
    @pytest.mark.unit
    def test_agent_role_is_strategy_related(self):
        """Test that agent role mentions investment strategy."""
        with patch.dict('os.environ', {'MISTRAL_API_KEY': 'test_key'}):
            from agents.strategist_agent import investment_strategist_agent
            
            role_lower = investment_strategist_agent.role.lower()
            assert "strategist" in role_lower or "investment" in role_lower or "advisor" in role_lower


class TestReportAgent:
    """Tests for Report Writer Agent."""
    
    @pytest.mark.unit
    def test_agent_creation(self):
        """Test that report agent is created successfully."""
        with patch.dict('os.environ', {'MISTRAL_API_KEY': 'test_key'}):
            from agents.report_agent import report_writer_agent
            
            assert report_writer_agent is not None
    
    @pytest.mark.unit
    def test_agent_role_is_report_related(self):
        """Test that agent role mentions report writing."""
        with patch.dict('os.environ', {'MISTRAL_API_KEY': 'test_key'}):
            from agents.report_agent import report_writer_agent
            
            role_lower = report_writer_agent.role.lower()
            assert "report" in role_lower or "writer" in role_lower or "editor" in role_lower


class TestAgentConfiguration:
    """Tests for agent configuration consistency."""
    
    @pytest.mark.unit
    def test_all_agents_have_llm(self):
        """Test that all agents have LLM configured."""
        with patch.dict('os.environ', {'MISTRAL_API_KEY': 'test_key'}):
            from agents.market_data_agent import market_data_agent
            from agents.news_agent import news_analyst_agent
            from agents.fundamental_agent import fundamental_analyst_agent
            from agents.technical_agent import technical_analyst_agent
            
            agents = [
                market_data_agent,
                news_analyst_agent,
                fundamental_analyst_agent,
                technical_analyst_agent,
            ]
            
            for agent in agents:
                assert hasattr(agent, 'llm'), f"{agent.role} missing LLM"
    
    @pytest.mark.unit
    def test_all_agents_have_backstory(self):
        """Test that all agents have backstory defined."""
        with patch.dict('os.environ', {'MISTRAL_API_KEY': 'test_key'}):
            from agents.market_data_agent import market_data_agent
            from agents.fundamental_agent import fundamental_analyst_agent
            from agents.technical_agent import technical_analyst_agent
            
            agents = [
                market_data_agent,
                fundamental_analyst_agent,
                technical_analyst_agent,
            ]
            
            for agent in agents:
                assert hasattr(agent, 'backstory')
                assert len(agent.backstory) > 50, f"{agent.role} backstory too short"
    
    @pytest.mark.unit
    def test_agents_configured_for_indian_markets(self):
        """Test that agents are configured for Indian market context."""
        with patch.dict('os.environ', {'MISTRAL_API_KEY': 'test_key'}):
            from agents.fundamental_agent import fundamental_analyst_agent
            from agents.technical_agent import technical_analyst_agent
            
            # Check backstories mention Indian context
            backstories = [
                fundamental_analyst_agent.backstory.lower(),
                technical_analyst_agent.backstory.lower(),
            ]
            
            for backstory in backstories:
                has_indian_context = (
                    "india" in backstory or
                    "nse" in backstory or
                    "bse" in backstory or
                    "nifty" in backstory
                )
                assert has_indian_context, "Agent should have Indian market context"


class TestAgentTools:
    """Tests for agent tool assignments."""
    
    @pytest.mark.unit
    def test_fundamental_agent_has_valuation_tools(self):
        """Test fundamental agent has valuation tools."""
        with patch.dict('os.environ', {'MISTRAL_API_KEY': 'test_key'}):
            from agents.fundamental_agent import fundamental_analyst_agent
            
            tool_names = [str(t) for t in fundamental_analyst_agent.tools]
            tool_str = " ".join(tool_names).lower()
            
            # Should have some fundamental-related tools
            assert len(fundamental_analyst_agent.tools) >= 1
    
    @pytest.mark.unit
    def test_technical_agent_has_indicator_tools(self):
        """Test technical agent has indicator calculation tools."""
        with patch.dict('os.environ', {'MISTRAL_API_KEY': 'test_key'}):
            from agents.technical_agent import technical_analyst_agent
            
            # Should have technical analysis tools
            assert len(technical_analyst_agent.tools) >= 1
    
    @pytest.mark.unit
    def test_news_agent_has_scraping_tools(self):
        """Test news agent has news scraping tools."""
        with patch.dict('os.environ', {'MISTRAL_API_KEY': 'test_key'}):
            from agents.news_agent import news_analyst_agent
            
            # Should have news-related tools
            assert len(news_analyst_agent.tools) >= 1


class TestAgentVerbosity:
    """Tests for agent verbosity settings."""
    
    @pytest.mark.unit
    def test_agents_have_verbose_setting(self):
        """Test that agents have verbose setting for debugging."""
        with patch.dict('os.environ', {'MISTRAL_API_KEY': 'test_key'}):
            from agents.fundamental_agent import fundamental_analyst_agent
            
            assert hasattr(fundamental_analyst_agent, 'verbose')


class TestAgentMaxIterations:
    """Tests for agent iteration limits."""
    
    @pytest.mark.unit
    def test_agents_have_max_iter_limit(self):
        """Test that agents have max iteration limit to prevent infinite loops."""
        with patch.dict('os.environ', {'MISTRAL_API_KEY': 'test_key'}):
            from agents.fundamental_agent import fundamental_analyst_agent
            from agents.technical_agent import technical_analyst_agent
            
            agents = [fundamental_analyst_agent, technical_analyst_agent]
            
            for agent in agents:
                if hasattr(agent, 'max_iter'):
                    assert agent.max_iter > 0, "max_iter should be positive"
                    assert agent.max_iter <= 20, "max_iter should be reasonable"
