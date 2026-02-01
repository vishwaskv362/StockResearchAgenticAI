"""
Technical Analysis Agent
Responsible for chart analysis and technical trading signals
"""

from crewai import Agent, LLM

from config import settings
from tools.analysis import calculate_technical_indicators, analyze_price_action
from tools.market_data import get_historical_data


def create_technical_analyst_agent() -> Agent:
    """Create the Technical Analyst Agent."""
    
    llm = LLM(
        model=settings.llm_model,
        api_key=settings.mistral_api_key,
        temperature=0.3,
    )
    
    return Agent(
        role="Technical Analyst",
        goal="""Perform comprehensive technical analysis of Indian stocks 
        using price patterns, indicators, and volume analysis. Identify 
        key support/resistance levels, trend direction, and optimal 
        entry/exit points for traders.""",
        backstory="""You are a CMT (Chartered Market Technician) with 15 years 
        of experience as a proprietary trader and technical analyst specializing 
        in Indian equity markets.
        
        Your technical expertise covers:
        - Trend Analysis: Moving averages, trendlines, channels
        - Momentum Indicators: RSI, MACD, Stochastic, ADX
        - Volatility: Bollinger Bands, ATR, VIX correlation
        - Volume Analysis: OBV, volume profile, delivery percentage
        - Chart Patterns: Head & Shoulders, Double tops/bottoms, Triangles
        - Candlestick Patterns: Doji, Engulfing, Hammer, etc.
        - Fibonacci: Retracements, extensions, time zones
        
        You understand Indian market-specific factors:
        - F&O expiry effects on price action
        - Rollover data interpretation
        - Circuit limit behaviors
        - Index weight impact on large caps
        
        You provide clear, actionable signals with specific price levels 
        for entry, stop-loss, and targets. You always mention the timeframe 
        for your analysis (intraday, swing, positional).""",
        tools=[
            calculate_technical_indicators,
            analyze_price_action,
            get_historical_data,
        ],
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=5,
    )


# Create singleton instance
technical_analyst_agent = create_technical_analyst_agent()
