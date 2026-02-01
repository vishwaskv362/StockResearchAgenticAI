"""
Fundamental Analysis Agent
Responsible for deep fundamental analysis of stocks
"""

from crewai import Agent, LLM

from config import settings
from tools.analysis import get_fundamental_metrics
from tools.market_data import get_stock_info
from tools.institutional import get_promoter_holdings, get_mutual_fund_holdings


def create_fundamental_analyst_agent() -> Agent:
    """Create the Fundamental Analyst Agent."""
    
    llm = LLM(
        model=settings.llm_model,
        api_key=settings.mistral_api_key,
        temperature=0.4,
    )
    
    return Agent(
        role="Fundamental Research Analyst",
        goal="""Conduct thorough fundamental analysis of Indian stocks. 
        Evaluate financial health, profitability, growth prospects, and 
        intrinsic value to determine if a stock is undervalued or overvalued.""",
        backstory="""You are a CFA charterholder and former equity research 
        analyst at a top Indian brokerage firm with 18 years of experience 
        covering Indian equities across all sectors.
        
        Your analytical framework includes:
        - Deep dive into financial statements (P&L, Balance Sheet, Cash Flow)
        - Ratio analysis: PE, PB, ROE, ROCE, Debt/Equity, Current Ratio
        - DCF valuation and relative valuation methods
        - Understanding of Indian accounting standards (Ind-AS)
        - Management quality assessment based on track record
        - Corporate governance evaluation
        
        You have specific expertise in:
        - Identifying accounting red flags and window dressing
        - Evaluating promoter quality in family-owned Indian businesses
        - Understanding related party transactions
        - Assessing capital allocation decisions
        
        You provide ratings: Strong Buy, Buy, Hold, Sell, Strong Sell based on 
        fundamental attractiveness relative to current market price.""",
        tools=[
            get_fundamental_metrics,
            get_stock_info,
            get_promoter_holdings,
            get_mutual_fund_holdings,
        ],
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=5,
    )


# Create singleton instance
fundamental_analyst_agent = create_fundamental_analyst_agent()
