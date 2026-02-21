"""
Data Quality Guardian Agent
Validates all input data for accuracy, completeness, and consistency
"""

from crewai import Agent, LLM

from config import settings
from tools.validation import (
    validate_symbol_existence,
    cross_validate_price_sources,
    sanity_check_metrics,
    calculate_data_quality_score,
)


def create_guardian_agent() -> Agent:
    """Create the Data Quality Guardian Agent."""
    
    llm = LLM(
        model=settings.llm_model,
        api_key=settings.mistral_api_key,
        temperature=0.2,  # Very low temperature for strict validation
    )
    
    return Agent(
        role="Data Quality Guardian",
        goal="""Validate all input data for accuracy, completeness, and consistency
        before any analytical reasoning begins. Ensure data quality meets minimum
        standards for reliable stock analysis.""",
        backstory="""You are a meticulous data quality specialist who serves as
        the first line of defense against bad data. Before any analysis can proceed,
        you must validate:
        
        1. Symbol exists and is actively traded
        2. Prices from different sources match (within 2% tolerance)
        3. Financial metrics are within reasonable bounds (no PE of 50,000 or negative market cap)
        4. Data completeness score meets minimum threshold
        
        You are strict but fair. Your validation tools check:
        - Symbol existence on NSE/BSE exchanges
        - Cross-validation between Yahoo Finance and NSE APIs
        - Sanity bounds on all financial metrics (PE, PB, ROE, debt ratios)
        - Overall data quality score (0-100 scale)
        
        CRITICAL RULES:
        - If quality score < 40, recommend ABORT
        - If quality score 40-59, flag as LOW CONFIDENCE
        - If quality score 60-79, flag as MODERATE CONFIDENCE  
        - If quality score >= 80, approve as HIGH CONFIDENCE
        - If critical data missing (no current price), recommend ABORT
        - If metric anomalies detected (PE > 500, negative market cap), flag for review
        - If prices diverge >2% between sources, note in report
        
        DO NOT proceed with analysis if data quality is insufficient. Your job is
        to protect downstream agents from garbage-in-garbage-out scenarios.
        
        However, recognize that small-cap stocks may have incomplete data - this is
        normal. Provide quality scores honestly, let users decide acceptable risk.""",
        tools=[
            validate_symbol_existence,
            cross_validate_price_sources,
            sanity_check_metrics,
            calculate_data_quality_score,
        ],
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=5,  # Allow enough iterations to run all 4 tools + provide summary
    )


# Create singleton instance
guardian_agent = create_guardian_agent()
