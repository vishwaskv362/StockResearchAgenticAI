"""
News Analysis Agent
Responsible for gathering and analyzing news from multiple sources
"""

from crewai import Agent, LLM

from config import settings
from tools.news_scraper import (
    scrape_moneycontrol_news,
    scrape_economic_times_news,
    get_stock_news,
    get_market_news_headlines,
)


def create_news_analyst_agent() -> Agent:
    """Create the News Analyst Agent."""
    
    llm = LLM(
        model=settings.llm_model,
        api_key=settings.mistral_api_key,
        temperature=0.5,
    )
    
    return Agent(
        role="News & Sentiment Analyst",
        goal="""Gather and analyze the latest news about Indian stocks from 
        multiple reliable sources. Assess news sentiment, identify material 
        developments, and evaluate how news might impact stock prices.""",
        backstory="""You are a veteran financial journalist turned analyst with 
        20 years covering Indian markets for leading publications like Economic 
        Times, Mint, and Business Standard.
        
        Your expertise lies in:
        - Separating signal from noise in financial news
        - Identifying market-moving events before they're priced in
        - Understanding the Indian corporate landscape and business groups
        - Reading between the lines of company announcements
        - Tracking regulatory developments from SEBI, RBI, and government
        
        You have deep connections across Indian business circles and understand 
        the political economy that affects markets. You're skeptical of promotional 
        news and always verify claims from multiple sources.
        
        You classify news as: Highly Positive, Positive, Neutral, Negative, or 
        Highly Negative, with clear reasoning for your assessment.""",
        tools=[
            scrape_moneycontrol_news,
            scrape_economic_times_news,
            get_stock_news,
            get_market_news_headlines,
        ],
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=5,
    )


# Create singleton instance
news_analyst_agent = create_news_analyst_agent()
