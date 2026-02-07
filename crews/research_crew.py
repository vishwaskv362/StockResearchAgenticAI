"""
Stock Research Crew
Orchestrates all agents to produce comprehensive stock analysis
"""

from datetime import datetime
from typing import Optional
from crewai import Crew, Task, Process

# ---------------------------------------------------------------------------
# Patch: Mistral API returns content as list of blocks (text, reference)
# instead of a plain string. LiteLLM 1.75.x can't parse this.
# Flatten list-format content to a string before LiteLLM's pydantic model
# tries to validate it. See: https://github.com/BerriAI/litellm/issues/13416
# ---------------------------------------------------------------------------
import litellm.litellm_core_utils.llm_response_utils.convert_dict_to_response as _llm_resp

_original_extract = _llm_resp._extract_reasoning_content


def _patched_extract_reasoning_content(message: dict):
    reasoning, content = _original_extract(message)
    if isinstance(content, list):
        # Flatten list of content blocks to a single string
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        content = "".join(parts) if parts else None
    return reasoning, content


_llm_resp._extract_reasoning_content = _patched_extract_reasoning_content
# ---------------------------------------------------------------------------

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

        1. Use the "Get Comprehensive Stock News" tool to fetch news from
           Economic Times RSS, Google News, and Economic Times in one call
        2. Use "Get Market News Headlines" to check for broader market news
        3. Analyze the sentiment of each headline and summary returned
        4. Identify any material news that could impact stock price

        Classify overall news sentiment and highlight the top 5 most important
        news items. Look for: earnings announcements, management changes,
        contract wins, regulatory issues, analyst upgrades/downgrades.""",
        expected_output=f"""A news analysis report for {symbol} containing:
        - List of recent news articles with sentiment assessment per headline
        - Overall sentiment assessment (Bullish/Bearish/Neutral)
        - Key news highlights that could impact price
        - Any red flags or positive catalysts identified""",
        agent=news_analyst_agent,
    )
    
    # ==========================================
    # Task 3: Fundamental Analysis
    # ==========================================
    fundamental_task = Task(
        description=f"""Perform fundamental analysis of {symbol} using your tools:

        1. Use "Get Fundamental Metrics" to get valuation, profitability,
           financial health, growth, and dividend data with overall rating
        2. Use "Get Stock Info" for company overview (sector, industry, description)
        3. Use "Get Promoter Holdings" to check shareholding pattern
        4. Use "Get Mutual Fund Holdings" to gauge institutional interest

        Based on the tool output:
        - Assess if valuation ratios (PE, PB, EV/EBITDA) suggest under/overvaluation
        - Evaluate profitability (ROE, ROA, margins)
        - Check financial health (debt/equity, current ratio)
        - Review growth trends (earnings growth, revenue growth)
        - Analyze promoter and institutional holding patterns

        Only report metrics that your tools return. If a metric is "N/A",
        note it as unavailable. Use the market data from the previous task.""",
        expected_output=f"""A fundamental analysis report for {symbol} including:
        - Valuation assessment with specific metrics from tool output
        - Profitability analysis
        - Financial health evaluation
        - Growth assessment
        - Shareholding pattern analysis
        - Overall fundamental rating (Strong Buy to Strong Sell)""",
        agent=fundamental_analyst_agent,
        context=[market_data_task],
    )
    
    # ==========================================
    # Task 4: Technical Analysis
    # ==========================================
    technical_task = Task(
        description=f"""Perform technical analysis of {symbol} using your tools:

        1. Use "Calculate Technical Indicators" to get RSI, MACD, Bollinger Bands,
           moving averages, ATR, volume ratio, support/resistance, and signals
        2. Use "Analyze Price Action" to get trend direction, swing points,
           and key price levels
        3. Use "Get Historical Data" if you need additional price context

        Based on the tool output:
        - Identify current trend (short, medium, long-term from MA analysis)
        - Interpret indicator signals (RSI, MACD crossovers, BB position)
        - Note support/resistance levels from pivot calculations
        - Check volume confirmation (volume ratio)

        Derive entry, stop-loss, and target prices from the support/resistance
        levels provided by the tools. Do not reference indicators (Stochastic,
        ADX, Fibonacci, candlestick patterns) that are not in your tool output.""",
        expected_output=f"""A technical analysis report for {symbol} containing:
        - Current trend assessment (short/medium/long term)
        - Key indicator readings (RSI, MACD, Bollinger Bands, ATR)
        - Support and resistance levels from pivot calculations
        - Trading signals from the tool's signal analysis
        - Specific entry, stop-loss, and target prices
        - Volume analysis""",
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

        Structure the report with these sections:
        1. **Executive Summary** - Key takeaways in 3-4 bullet points
        2. **Company Snapshot** - Brief overview with sector and market cap
        3. **Fundamental Highlights** - Key metrics and assessment
        4. **Technical View** - Trend, indicators, and key levels
        5. **News & Sentiment** - Recent developments and sentiment
        6. **Risk Assessment** - Key risks to consider
        7. **Recommendation** - Clear action with targets and stop-loss

        Formatting guidelines:
        - Use markdown with clear section headings
        - Keep sections concise and focused
        - Highlight key numbers (prices, ratios, percentages)
        - Include specific price levels for entry, target, and stop-loss
        - Use Indian number format (lakhs, crores) for large values

        IMPORTANT: Only include data and metrics that were provided by the
        other analysts. Do not introduce new statistics or price targets
        beyond what the analysis contains.

        End with a clear action statement and a standard investment disclaimer.""",
        expected_output=f"""A professional research report for {symbol} with:
        - Clear markdown structure with section headings
        - Executive summary at the top
        - All key analysis points from previous agents covered
        - Specific actionable recommendation
        - Price targets and stop-loss levels from technical analysis
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

    Uses asyncio.to_thread to run the synchronous CrewAI kickoff
    without blocking the event loop.

    Args:
        symbol: Stock symbol (e.g., 'RELIANCE')
        analysis_type: 'full', 'quick', or 'technical-only'

    Returns:
        Formatted research report string
    """
    import asyncio
    return await asyncio.to_thread(analyze_stock_sync, symbol, analysis_type)


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
