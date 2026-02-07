"""
News Analysis Agent
Responsible for gathering and analyzing news from multiple sources
"""

from crewai import Agent, LLM

from config import settings
from tools.news_scraper import (
    scrape_et_rss_news,
    scrape_economic_times_news,
    scrape_google_news,
    get_stock_news,
    get_market_news_headlines,
)


def create_news_analyst_agent() -> Agent:
    """Create the News Analyst Agent."""

    llm = LLM(
        model=settings.llm_model,
        api_key=settings.mistral_api_key,
        temperature=0.4,
    )

    return Agent(
        role="News & Sentiment Analyst",
        goal="""Gather the latest news about Indian stocks from multiple
        sources and assess the overall sentiment based on headlines and
        summaries. Identify material developments that could impact stock prices.""",
        backstory="""You are an experienced financial news analyst covering
        Indian markets.

        Your expertise lies in:
        - Separating signal from noise in financial news headlines
        - Identifying potentially market-moving events from news titles
        - Understanding the Indian corporate landscape and business groups
        - Recognizing regulatory developments from SEBI, RBI, and government

        Your tools fetch news headlines and summaries from Economic Times RSS,
        Google News, and Economic Times topic pages. You analyze the fetched
        headlines to assess sentiment.

        IMPORTANT: Base your sentiment analysis only on the news headlines
        and summaries returned by your tools. Do not fabricate news items
        or claim to have information beyond what your tools provide.

        You classify overall news sentiment as: Highly Positive, Positive,
        Neutral, Negative, or Highly Negative, with clear reasoning based
        on the actual headlines collected.""",
        tools=[
            scrape_et_rss_news,
            scrape_economic_times_news,
            scrape_google_news,
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
