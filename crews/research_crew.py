"""
Stock Research Crew
Orchestrates all agents to produce comprehensive stock analysis
"""

from datetime import datetime
from typing import Optional
from crewai import Crew, Task, Process

from agents.market_data_agent import market_data_agent
from agents.news_agent import news_analyst_agent
from agents.fundamental_agent import fundamental_analyst_agent
from agents.technical_agent import technical_analyst_agent
from agents.strategist_agent import investment_strategist_agent
from agents.report_agent import report_writer_agent


def create_stock_research_crew(symbol: str, analysis_type: str = "full") -> Crew:
    """
    Create a research crew for analyzing a stock.
    
    Args:
        symbol: Stock symbol (e.g., 'RELIANCE', 'TCS')
        analysis_type: 'full', 'quick', or 'technical-only'
        
    Returns:
        Configured Crew ready to execute
    """
    symbol = symbol.upper().strip()
    
    # ==========================================
    # Task 1: Collect Market Data
    # ==========================================
    market_data_task = Task(
        description=f"""Collect comprehensive market data for {symbol}:
        
        1. Get the current stock price, volume, and today's trading range
        2. Fetch company information (sector, industry, market cap)
        3. Get historical data for the past 1 year
        4. Check the major index levels (NIFTY50, SENSEX)
        5. Get NSE-specific data if available (delivery percentage)
        
        Compile all data into a structured format that other analysts can use.
        Highlight any unusual activity (volume spikes, price gaps, etc.)""",
        expected_output=f"""A comprehensive market data report for {symbol} including:
        - Current price and day's trading range
        - Volume compared to average
        - Key company metrics (market cap, sector, etc.)
        - Historical performance summary
        - Any notable observations""",
        agent=market_data_agent,
    )
    
    # ==========================================
    # Task 2: Analyze News & Sentiment
    # ==========================================
    news_analysis_task = Task(
        description=f"""Gather and analyze all recent news about {symbol}:
        
        1. Scrape news from Moneycontrol
        2. Scrape news from Economic Times
        3. Get comprehensive news from multiple sources
        4. Analyze sentiment of each news item
        5. Identify any material news that could impact stock price
        
        Classify overall news sentiment and highlight the top 5 most important news items.
        Look for: earnings announcements, management changes, contract wins, regulatory issues,
        analyst upgrades/downgrades, and sector-wide news.""",
        expected_output=f"""A news analysis report for {symbol} containing:
        - List of recent news articles with sentiment scores
        - Overall sentiment assessment (Bullish/Bearish/Neutral)
        - Key news highlights that could impact price
        - Any red flags or positive catalysts identified""",
        agent=news_analyst_agent,
    )
    
    # ==========================================
    # Task 3: Fundamental Analysis
    # ==========================================
    fundamental_task = Task(
        description=f"""Perform deep fundamental analysis of {symbol}:
        
        1. Calculate and analyze all key fundamental metrics
        2. Evaluate valuation (PE, PB, EV/EBITDA)
        3. Assess profitability (ROE, ROCE, margins)
        4. Check financial health (debt levels, current ratio)
        5. Analyze growth metrics
        6. Check promoter and institutional holdings
        
        Compare metrics with sector averages and historical values.
        Identify if the stock is undervalued, fairly valued, or overvalued.
        Use the market data provided by the Market Data Analyst.""",
        expected_output=f"""A fundamental analysis report for {symbol} including:
        - Valuation assessment with specific metrics
        - Profitability analysis
        - Financial health evaluation
        - Growth prospects assessment
        - Shareholding pattern analysis
        - Overall fundamental rating (Strong Buy to Strong Sell)""",
        agent=fundamental_analyst_agent,
        context=[market_data_task],
    )
    
    # ==========================================
    # Task 4: Technical Analysis
    # ==========================================
    technical_task = Task(
        description=f"""Perform comprehensive technical analysis of {symbol}:
        
        1. Calculate all major technical indicators (RSI, MACD, Bollinger Bands)
        2. Identify current trend (short, medium, long-term)
        3. Find key support and resistance levels
        4. Analyze recent price action patterns
        5. Check volume patterns for confirmation
        6. Look for any chart patterns forming
        
        Provide specific price levels for:
        - Entry point(s)
        - Stop-loss level
        - Target prices (short-term and medium-term)
        
        Use the historical data from Market Data Analyst.""",
        expected_output=f"""A technical analysis report for {symbol} containing:
        - Current trend assessment
        - Key indicator readings (RSI, MACD, etc.)
        - Support and resistance levels
        - Trading signals (buy/sell/hold)
        - Specific entry, stop-loss, and target prices
        - Chart pattern observations if any""",
        agent=technical_analyst_agent,
        context=[market_data_task],
    )
    
    # ==========================================
    # Task 5: Investment Strategy
    # ==========================================
    strategy_task = Task(
        description=f"""Synthesize all research and formulate investment recommendation for {symbol}:
        
        1. Review fundamental analysis findings
        2. Consider technical analysis signals
        3. Factor in news sentiment
        4. Check FII/DII activity for market context
        5. Look for any bulk/block deals in the stock
        6. Assess overall market conditions (index levels)
        
        Formulate a clear recommendation considering:
        - Risk-reward ratio
        - Investment horizon (short/medium/long term)
        - Position sizing guidance
        - Key risks to monitor
        - Trigger points for review
        
        Think from the perspective of an Indian retail investor with moderate risk appetite.""",
        expected_output=f"""An investment strategy report for {symbol} containing:
        - Clear recommendation (Buy/Hold/Sell)
        - Conviction level (High/Medium/Low)
        - Suggested position size
        - Investment horizon
        - Risk factors and mitigants
        - Key levels to watch
        - When to review the position""",
        agent=investment_strategist_agent,
        context=[fundamental_task, technical_task, news_analysis_task],
    )
    
    # ==========================================
    # Task 6: Write Final Report
    # ==========================================
    report_task = Task(
        description=f"""Create a comprehensive, well-structured research report for {symbol}:
        
        Compile all findings from:
        - Market Data Analysis
        - News & Sentiment Analysis  
        - Fundamental Analysis
        - Technical Analysis
        - Investment Strategy
        
        Structure the report with:
        1. 📊 **Executive Summary** - Key takeaways in 3-4 bullet points
        2. 🏢 **Company Snapshot** - Brief overview
        3. 💰 **Fundamental Highlights** - Key metrics and assessment
        4. 📈 **Technical View** - Trend and key levels
        5. 📰 **News & Sentiment** - Recent developments
        6. ⚠️ **Risk Assessment** - Key risks to consider
        7. 🎯 **Recommendation** - Clear action with targets
        
        Format for Telegram (use markdown):
        - Use emojis appropriately
        - Keep sections concise
        - Highlight key numbers
        - Include specific price levels
        - Use Indian number format (lakhs, crores)
        
        End with a clear action statement and disclaimer.""",
        expected_output=f"""A professional research report for {symbol} formatted for Telegram with:
        - Clear structure with emoji headings
        - Executive summary at the top
        - All key analysis points covered
        - Specific actionable recommendation
        - Price targets and stop-loss levels
        - Standard investment disclaimer""",
        agent=report_writer_agent,
        context=[market_data_task, news_analysis_task, fundamental_task, technical_task, strategy_task],
    )
    
    # ==========================================
    # Select tasks based on analysis type
    # ==========================================
    if analysis_type == "quick":
        tasks = [market_data_task, technical_task, report_task]
    elif analysis_type == "technical-only":
        tasks = [market_data_task, technical_task]
    else:  # full analysis
        tasks = [
            market_data_task,
            news_analysis_task,
            fundamental_task,
            technical_task,
            strategy_task,
            report_task,
        ]
    
    # ==========================================
    # Create and return the crew
    # ==========================================
    crew = Crew(
        agents=[
            market_data_agent,
            news_analyst_agent,
            fundamental_analyst_agent,
            technical_analyst_agent,
            investment_strategist_agent,
            report_writer_agent,
        ],
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
    )
    
    return crew


async def analyze_stock(symbol: str, analysis_type: str = "full") -> str:
    """
    Run complete stock analysis and return the report.
    
    Args:
        symbol: Stock symbol (e.g., 'RELIANCE')
        analysis_type: 'full', 'quick', or 'technical-only'
        
    Returns:
        Formatted research report string
    """
    crew = create_stock_research_crew(symbol, analysis_type)
    result = crew.kickoff()
    
    # Extract the final output
    if hasattr(result, 'raw'):
        return result.raw
    elif hasattr(result, 'output'):
        return result.output
    else:
        return str(result)


def analyze_stock_sync(symbol: str, analysis_type: str = "full") -> str:
    """
    Synchronous version of stock analysis.
    
    Args:
        symbol: Stock symbol (e.g., 'RELIANCE')
        analysis_type: 'full', 'quick', or 'technical-only'
        
    Returns:
        Formatted research report string
    """
    crew = create_stock_research_crew(symbol, analysis_type)
    result = crew.kickoff()
    
    # Extract the final output
    if hasattr(result, 'raw'):
        return result.raw
    elif hasattr(result, 'output'):
        return result.output
    else:
        return str(result)
