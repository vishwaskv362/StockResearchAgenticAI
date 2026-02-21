"""
Stock Research Crew
Orchestrates all agents to produce comprehensive stock analysis
"""

import os
from datetime import datetime
from typing import Optional
from crewai import Crew, Task, Process

# Configure LiteLLM for better error handling
os.environ["LITELLM_DROP_PARAMS"] = "true"
os.environ["LITELLM_LOG"] = "ERROR"

# ---------------------------------------------------------------------------
# Patch: Mistral API returns content as list of blocks (text, reference)
# instead of a plain string. LiteLLM 1.75.x can't parse this.
# Flatten list-format content to a string before LiteLLM's pydantic model
# tries to validate it. See: https://github.com/BerriAI/litellm/issues/13416
# ---------------------------------------------------------------------------
import litellm
import litellm.litellm_core_utils.llm_response_utils.convert_dict_to_response as _llm_resp

# Configure LiteLLM with retry logic
litellm.num_retries = 3
litellm.request_timeout = 600
litellm.drop_params = True

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
from agents.guardian_agent import guardian_agent
from agents.valuation_agent import valuation_agent
from agents.risk_agent import risk_agent
from agents.critic_agent import critic_agent


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
        Highlight any unusual activity (volume spikes, price gaps, etc.)

        IMPORTANT: Report the exact numbers returned by each tool call.
        If a tool returns an error, state "data unavailable" for that section.
        Do not estimate or guess any data points.""",
        expected_output=f"""A comprehensive market data report for {symbol} including:
        - Current price (exact value from Get Stock Price tool)
        - Day's trading range (open, high, low from tool output)
        - Volume compared to average
        - Key company metrics (market cap, sector, etc.)
        - 52-week high and low from tool output
        - Historical performance summary
        - Any notable observations""",
        agent=market_data_agent,
    )
    
    # ==========================================
    # Task 2: Data Quality Validation (NEW)
    # ==========================================
    guardian_task = Task(
        description=f"""Validate all market data collected for {symbol} before analysis proceeds:

        1. Run "Validate Symbol Existence" to confirm {symbol} is valid and traded
        2. Run "Cross-Validate Price Sources" to check Yahoo Finance vs NSE consistency
        3. Run "Sanity Check Metrics" to flag any extreme values (PE > 500, negative market cap)
        4. Run "Calculate Data Quality Score" to get overall completeness score (0-100)

        Interpret the results:
        - Quality score >= 80: HIGH CONFIDENCE - proceed with full analysis
        - Quality score 60-79: MODERATE CONFIDENCE - note limitations
        - Quality score 40-59: LOW CONFIDENCE - warn about data gaps
        - Quality score < 40: VERY LOW CONFIDENCE - recommend limited analysis

        Flag specific issues:
        - Price discrepancies between sources (>2% difference)
        - Metrics outside reasonable bounds
        - Missing critical data fields

        CRITICAL: If symbol is invalid or current price unavailable, recommend ABORT.
        Otherwise, provide quality assessment for downstream agents to consider.""",
        expected_output=f"""A TEXT DATA QUALITY VALIDATION REPORT for {symbol}.

After running all validation tools, provide a clear TEXT summary (not tool calls):

=== DATA QUALITY REPORT: {symbol} ===
Symbol Status: [VALID/INVALID]
Price Validation: [PASS/FAIL - Yahoo vs NSE within 2%]
Metric Sanity: [PASS/FAIL - any extreme values?]
Data Quality Score: [X/100]
Confidence Tier: [HIGH/MODERATE/LOW/VERY LOW]

Issues Found:
- [List any specific issues, or "None"]

Recommendation: [PROCEED WITH HIGH CONFIDENCE / PROCEED WITH CAUTION / ABORT]

Provide this as a TEXT report, NOT as tool calls.""",
        agent=guardian_agent,
        context=[market_data_task],
    )
    
    # ==========================================
    # Task 3: Analyze News & Sentiment
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
    # Task 5: Valuation Modeling (NEW)
    # ==========================================
    valuation_task = Task(
        description=f"""Build a structured relative valuation model for {symbol}:

        1. Run "Get Sector Valuation Multiples" to identify sector and compare to peers
           - Compare PE, PB, EV/EBITDA to sector median
           - Calculate percentile ranks (is stock premium or discount to sector?)

        2. Run "Calculate Relative Valuation" to derive fair value range
           - Apply sector median multiples to stock's fundamentals
           - Use multiple methods (PE-based, PB-based, Forward PE-based)
           - Show fair value as a RANGE, not a single point

        3. Run "Build Scenario Valuations" for bull/base/bear cases
           - Bull case: +20% earnings growth, PE expands 10%
           - Base case: +5% earnings growth, PE stable
           - Bear case: -15% earnings, PE contracts 10%
           - Calculate target prices and risk-reward ratio

        4. Run "Identify Multiple Drivers" to explain valuation premium/discount
           - ROE vs peers (quality premium justified?)
           - Margin differences
           - Factors that would drive PE expansion or compression

        Show all assumptions explicitly. Fair value is a range based on peer comparison.""",
        expected_output=f"""A valuation analysis report for {symbol} containing:
        - Sector classification and peer comparison table
        - Fair value range (minimum, average, maximum) with methodology
        - Current price vs fair value (undervalued/fairly valued/overvalued)
        - Upside/downside percentages
        - Bull/base/bear scenario target prices with explicit assumptions
        - Risk-reward ratio (bull upside / bear downside)
        - Multiple expansion/compression drivers
        - Quality metrics justifying premium/discount (ROE, margins)""",
        agent=valuation_agent,
        context=[fundamental_task, guardian_task],
    )
    
    # ==========================================
    # Task 6: Technical Analysis
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
        context=[guardian_task],  # Use validated data from guardian
    )
    
    # ==========================================
    # Task 7: Risk Management (NEW)
    # ==========================================
    risk_task = Task(
        description=f"""Conduct comprehensive downside-focused risk analysis for {symbol}:

        1. Run "Calculate Value at Risk" to quantify maximum loss at 95% confidence
           - Interpret: "In worst 5% of scenarios, expect to lose X% over 30 days"
           - Assess annual volatility (Low <20%, Moderate 20-35%, High >35%)

        2. Run "Analyze Downside Risk Metrics" for drawdown and Sortino analysis
           - Maximum historical drawdown (worst peak-to-trough decline)
           - Recovery time from past drawdowns
           - Sortino ratio (reward per unit of downside risk)

        3. Run "Assess Leverage Risk" to evaluate financial stability
           - Debt/equity ratio assessment
           - Interest coverage (can company service debt?)
           - Refinancing risks

        4. Run "Calculate Stop Loss Levels" for risk management
           - Conservative stop (3x ATR, for long-term holders)
           - Moderate stop (2x ATR, for swing traders)
           - Aggressive stop (1.5x ATR, for active traders)

        5. Run "Model Scenario Risks" for stress testing
           - Rate hike scenario (+100 bps repo rate)
           - Commodity shock (oil +20%, input costs surge)
           - Demand shock (revenue -15%)
           - Sector-specific headwinds

        CRITICAL REQUIREMENTS:
        - List MINIMUM 3 specific risks (not generic "market risk")
        - Each risk needs: description, probability estimate, potential impact
        - Define THESIS INVALIDATION conditions:
          * "Exit if price breaks below ₹X"
          * "Reassess if debt/equity exceeds Y"
          * "Review if earnings decline 2 consecutive quarters"

        For BUY recommendations, ensure risk-reward ratio > 1.5:1.""",
        expected_output=f"""A comprehensive risk analysis report for {symbol} containing:
        - Overall risk score (1-10 scale) and risk category
        - Value at Risk: 95% confidence, 30-day horizon (percentage)
        - Annual volatility and risk level classification
        - Maximum drawdown history and recovery time
        - Sortino ratio (risk-adjusted returns)
        - Leverage risk assessment (debt/equity, interest coverage)
        - Stop-loss levels: conservative, moderate, aggressive (with prices)
        - Scenario analysis table showing impact of rate/commodity/demand shocks
        - Minimum 3 specific risk factors with probability and impact
        - Thesis invalidation conditions (clear exit triggers)
        - Risk mitigation recommendations""",
        agent=risk_agent,
        context=[technical_task, fundamental_task, valuation_task, guardian_task],
    )
    
    # ==========================================
    # Task 8: Investment Strategy
    # ==========================================
    strategy_task = Task(
        description=f"""Synthesize all research and formulate investment recommendation for {symbol}:
        
        1. Review fundamental analysis findings
        2. Consider valuation model (fair value range, scenarios)
        3. Review technical analysis signals
        4. Factor in news sentiment
        5. CRITICALLY: Review comprehensive risk analysis
        6. Check FII/DII activity for market context
        7. Look for any bulk/block deals in the stock
        8. Assess overall market conditions (index levels)
        9. Consider data quality score from guardian
        
        Formulate a clear recommendation considering:
        - Risk-reward ratio from valuation (must be > 1.5:1 for BUY)
        - Investment horizon (short/medium/long term)
        - Position sizing guidance based on risk score
        - Key risks to monitor (from risk analysis)
        - Trigger points for review
        
        MANDATORY FOR BUY RECOMMENDATIONS:
        - Must cite at least 3 specific risks from risk analysis
        - Must include thesis invalidation condition from risk report
        - Must specify stop-loss level (from risk analysis)
        - Entry price, target price from valuation scenarios
        
        Think from the perspective of an Indian retail investor with moderate risk appetite.""",
        expected_output=f"""An investment strategy report for {symbol} containing:
        - Clear recommendation (Buy/Hold/Sell)
        - Conviction level (High/Medium/Low)
        - Entry price and target price (from valuation)
        - Stop-loss level (from risk analysis)
        - FOR BUY: Minimum 3 specific risks + thesis invalidation condition
        - Suggested position size based on risk score
        - Investment horizon
        - Risk-reward ratio justification
        - Key levels to watch
        - When to review the position""",
        agent=investment_strategist_agent,
        context=[fundamental_task, technical_task, news_analysis_task, valuation_task, risk_task, guardian_task],
    )
    
    # ==========================================
    # Task 9: Investment Committee Critic Review
    # ==========================================
    critic_task = Task(
        description=f"""Challenge the investment thesis for {symbol} with rigorous adversarial review:
        
        Review the strategist's recommendation and provide:
        1. **Top 5 Counterarguments**: Specific challenges across:
           - Valuation risks (overpaying, multiple contraction)
           - Execution risks (management, capital allocation)
           - Sector/macro risks (regulatory, competitive, cyclical)
           - Competitive risks (market share, pricing power)
           - Financial risks (leverage, cash flow, working capital)
        
        2. **Thesis Invalidation Conditions**: What would prove the thesis wrong?
           - Specific price levels that invalidate valuation case
           - Fundamental triggers (earnings miss, margin compression)
           - Management actions (governance issues, poor capital allocation)
           - Macro/sector developments (regulatory changes, competition)
        
        3. **Missing Evidence**: What critical data points are absent?
           - Key metrics not analyzed
           - Important risks not addressed
           - Alternative scenarios not considered
        
        4. **Vulnerability Rating**: Overall thesis strength
           - LOW: Robust thesis with limited vulnerabilities
           - MEDIUM: Solid case but meaningful risks present
           - HIGH: Thesis has significant weaknesses or unknowns
        
        Your job is to stress-test the recommendation through devil's advocacy.
        Think like a contrarian analyst who has seen Enron, Satyam, Yes Bank, IL&FS.
        Force intellectual honesty and prevent groupthink.""",
        expected_output=f"""Investment Committee Critic's Challenge Report for {symbol}:
        
        **TOP 5 COUNTERARGUMENTS:**
        1. [Valuation Risk] - Specific concern with numbers
        2. [Execution Risk] - Specific concern with evidence
        3. [Sector/Macro Risk] - Specific concern with context
        4. [Competitive Risk] - Specific concern with positioning
        5. [Financial Risk] - Specific concern with metrics
        
        **THESIS INVALIDATION CONDITIONS:**
        - Price Triggers: Levels that break valuation case
        - Fundamental Triggers: Events that invalidate investment thesis
        - Management Triggers: Actions that signal problems
        - Macro Triggers: External developments that derail thesis
        
        **MISSING EVIDENCE:**
        - Critical data points not analyzed
        - Important risks not addressed
        - Alternative scenarios not modeled
        
        **VULNERABILITY RATING:** [LOW/MEDIUM/HIGH]
        - Justification for rating with specific concerns
        - Overall assessment of thesis robustness""",
        agent=critic_agent,
        context=[strategy_task],  # Reviews strategist's recommendation
    )
    
    # ==========================================
    # Task 10: Write Final Report
    # ==========================================
    report_task = Task(
        description=f"""Create a comprehensive, well-structured research report for {symbol}:

        STEP 1 - VERIFY DATA (MANDATORY):
        Before writing anything, call "Get Stock Price" for {symbol} to get the
        verified current price. This is your ground truth. Every price mention
        in the report must be consistent with this verified price.

        STEP 2 - Compile all findings from the other agents:
        - Data Quality Assessment (from Guardian)
        - Market Data Analysis
        - News & Sentiment Analysis
        - Fundamental Analysis
        - Valuation Model (from Valuation Agent)
        - Technical Analysis
        - Risk Analysis (from Risk Manager)
        - Investment Strategy
        - Critic's Challenge (from Investment Committee Critic)

        STEP 3 - Structure the report with these sections:
        1. **Executive Summary** - Key takeaways in 3-4 bullet points
        2. **Data Quality** - Quality score and confidence level from Guardian
        3. **Company Snapshot** - Brief overview with sector and market cap
        4. **Valuation** - Fair value range, current price, upside/downside
        5. **Fundamental Highlights** - Key metrics and sector comparison
        6. **Technical View** - Trend, indicators, and key levels
        7. **Risk Assessment** - VaR, drawdown, leverage, stop-loss levels
        8. **News & Sentiment** - Recent developments and sentiment
        9. **Recommendation** - Clear action with entry, target, stop-loss, risks
        10. **Critic's Challenge** - Top counterarguments from Investment Committee Critic
        11. **Thesis Invalidation** - Exit conditions from risk analysis and critic review

        Formatting guidelines:
        - Use markdown with clear section headings
        - Keep sections concise and focused
        - Highlight key numbers (prices, ratios, percentages)
        - Include specific price levels for entry, target, and stop-loss
        - Use Indian number format (lakhs, crores) for large values

        DATA INTEGRITY RULES (NON-NEGOTIABLE):
        1. The current price MUST match the "Get Stock Price" tool output exactly.
        2. Support/resistance levels must come from technical analysis tool data.
        3. Do NOT invent AUM, expense ratio, or other metrics not in the data.
        4. If a data point is unavailable, write "Data not available".
        5. Do not introduce new statistics or price targets beyond what the
           analysis contains.

        End with a clear action statement and a standard investment disclaimer.""",
        expected_output=f"""A professional research report for {symbol} with:
        - Data quality score and confidence level (from Guardian)
        - Current price verified against Get Stock Price tool output
        - Fair value range and valuation verdict (undervalued/fairly valued/overvalued)
        - Risk metrics: VaR, max drawdown, leverage assessment
        - FOR BUY: Minimum 3 risks + invalidation condition prominently displayed
        - Clear markdown structure with section headings
        - Executive summary at the top
        - All key analysis points from previous agents covered
        - Specific actionable recommendation
        - Price targets and stop-loss levels from technical analysis
        - Standard investment disclaimer""",
        agent=report_writer_agent,
        context=[guardian_task, market_data_task, news_analysis_task, fundamental_task, valuation_task, technical_task, risk_task, strategy_task, critic_task],
    )
    
    # ==========================================
    # Select tasks based on analysis type
    # ==========================================
    if analysis_type == "quick":
        tasks = [
            market_data_task,
            guardian_task,
            fundamental_task,
            valuation_task,
            strategy_task,
            critic_task,
            report_task,
        ]
    elif analysis_type == "technical-only":
        tasks = [
            market_data_task,
            guardian_task,
            technical_task,
            risk_task,
            report_task,
        ]
    else:  # full analysis
        tasks = [
            market_data_task,
            guardian_task,
            news_analysis_task,
            fundamental_task,
            valuation_task,
            technical_task,
            risk_task,
            strategy_task,
            critic_task,
            report_task,
        ]
    
    # ==========================================
    # Create and return the crew
    # ==========================================
    crew = Crew(
        agents=[
            market_data_agent,
            guardian_agent,
            news_analyst_agent,
            fundamental_analyst_agent,
            valuation_agent,
            technical_analyst_agent,
            risk_agent,
            investment_strategist_agent,
            critic_agent,
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
