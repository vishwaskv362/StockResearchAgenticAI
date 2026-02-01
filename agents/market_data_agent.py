"""
Market Data Collection Agent
Responsible for gathering real-time and historical market data
"""

from crewai import Agent, LLM

from config import settings
from tools.market_data import (
    get_stock_price,
    get_stock_info,
    get_historical_data,
    get_index_data,
    get_nse_stock_quote,
)


def create_market_data_agent() -> Agent:
    """Create the Market Data Collection Agent."""
    
    llm = LLM(
        model=settings.llm_model,
        api_key=settings.mistral_api_key,
        temperature=0.3,  # Lower temperature for factual data
    )
    
    return Agent(
        role="Market Data Analyst",
        goal="""Collect comprehensive and accurate market data for Indian stocks 
        from NSE and BSE. Gather current prices, historical data, trading volumes, 
        and key market statistics to provide a complete data picture.""",
        backstory="""You are a seasoned market data specialist with 15 years of 
        experience in Indian equity markets. You have deep expertise in NSE and BSE 
        data systems and understand the nuances of Indian market data including 
        circuit limits, delivery percentages, and trading sessions.
        
        You are meticulous about data accuracy and always cross-verify information 
        from multiple sources. You understand the importance of timing - knowing 
        when markets are open, when data is most reliable, and how to interpret 
        pre-market and after-hours data.
        
        Your role is foundational - other analysts depend on the accuracy of your 
        data to make their assessments.""",
        tools=[
            get_stock_price,
            get_stock_info,
            get_historical_data,
            get_index_data,
            get_nse_stock_quote,
        ],
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=5,
    )


# Create singleton instance
market_data_agent = create_market_data_agent()
