"""
Risk Analysis Tools
Quantifies downside risk with VaR, drawdown, leverage, and scenario modeling
"""

import json
from datetime import datetime, timedelta
from typing import Optional
import yfinance as yf
import pandas as pd
import numpy as np
from scipy import stats
from crewai.tools import tool


def _safe_json_dumps(data: dict, **kwargs) -> str:
    """JSON serialize with NaN/Infinity replaced by None."""
    import math

    def _sanitize(obj):
        if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
            return None
        if isinstance(obj, dict):
            return {k: _sanitize(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_sanitize(v) for v in obj]
        return obj

    return json.dumps(_sanitize(data), **kwargs)


def _get_nse_symbol(symbol: str) -> str:
    """Convert symbol to NSE Yahoo Finance format."""
    symbol = symbol.upper().strip()
    if not symbol.endswith(".NS"):
        return f"{symbol}.NS"
    return symbol


@tool("Calculate Value at Risk")
def calculate_var(symbol: str, confidence_level: float = 0.95, period_days: int = 30) -> str:
    """
    Calculate Value at Risk (VaR) - the maximum expected loss at a given confidence level.
    Shows "in worst 5% of scenarios, expect to lose X% over next month".
    
    Args:
        symbol: Stock symbol (e.g., 'RELIANCE', 'TCS')
        confidence_level: Confidence level (default 0.95 for 95%)
        period_days: Holding period in days (default 30)
        
    Returns:
        JSON with VaR estimates using parametric and historical methods.
    """
    try:
        symbol = symbol.upper().strip()
        ticker = yf.Ticker(_get_nse_symbol(symbol))
        
        # Get 1 year of historical data
        hist = ticker.history(period="1y")
        
        if hist.empty or len(hist) < 60:
            return _safe_json_dumps({
                "error": f"Insufficient data for VaR calculation (need 60+ days, got {len(hist)})",
                "DATA_UNAVAILABLE": True,
                "message": "Cannot calculate risk metrics without sufficient history",
            })
        
        # Calculate daily returns
        returns = hist['Close'].pct_change().dropna()
        
        if len(returns) < 50:
            return _safe_json_dumps({
                "error": "Insufficient return history",
                "DATA_UNAVAILABLE": True,
            })
        
        # Method 1: Parametric VaR (assumes normal distribution)
        mean_return = returns.mean()
        std_return = returns.std()
        z_score = stats.norm.ppf(1 - confidence_level)
        
        # Scale to holding period
        period_mean = mean_return * period_days
        period_std = std_return * np.sqrt(period_days)
        
        parametric_var = (period_mean + z_score * period_std) * 100  # Convert to percentage
        
        # Method 2: Historical VaR (actual percentile from data)
        # Generate potential period returns by bootstrapping
        period_returns = []
        for _ in range(1000):
            sample = np.random.choice(returns, size=period_days, replace=True)
            period_return = (1 + sample).prod() - 1
            period_returns.append(period_return)
        
        historical_var = np.percentile(period_returns, (1 - confidence_level) * 100) * 100
        
        # Average VaR
        avg_var = (parametric_var + historical_var) / 2
        
        # Calculate additional risk metrics
        annual_volatility = std_return * np.sqrt(252) * 100  # Annualized
        
        return _safe_json_dumps({
            "symbol": symbol,
            "confidence_level": confidence_level,
            "period_days": period_days,
            "var_estimates": {
                "parametric": parametric_var,
                "historical": historical_var,
                "average": avg_var,
            },
            "interpretation": f"At {confidence_level*100:.0f}% confidence, maximum loss over {period_days} days is {abs(avg_var):.2f}%",
            "annual_volatility": annual_volatility,
            "risk_level": (
                "Low" if annual_volatility < 20
                else "Moderate" if annual_volatility < 35
                else "High" if annual_volatility < 50
                else "Very High"
            ),
        })
        
    except Exception as e:
        return _safe_json_dumps({
            "error": f"VaR calculation error: {str(e)}",
            "DATA_UNAVAILABLE": True,
        })


@tool("Analyze Downside Risk Metrics")
def analyze_downside_metrics(symbol: str) -> str:
    """
    Calculate downside-focused risk metrics: max drawdown, downside deviation,
    Sortino ratio (risk-adjusted returns using only downside volatility).
    
    Args:
        symbol: Stock symbol (e.g., 'RELIANCE', 'TCS')
        
    Returns:
        JSON with maximum drawdown, downside deviation, and Sortino ratio.
    """
    try:
        symbol = symbol.upper().strip()
        ticker = yf.Ticker(_get_nse_symbol(symbol))
        
        # Get 2 years of data for reliable drawdown calculation
        hist = ticker.history(period="2y")
        
        if hist.empty or len(hist) < 100:
            return _safe_json_dumps({
                "error": f"Insufficient data for drawdown analysis (need 100+ days)",
                "DATA_UNAVAILABLE": True,
            })
        
        prices = hist['Close']
        returns = prices.pct_change().dropna()
        
        # Calculate maximum drawdown
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min() * 100  # Convert to percentage
        
        # Find when max drawdown occurred
        max_dd_date = drawdown.idxmin()
        peak_date = running_max[:max_dd_date].idxmax() if max_dd_date in drawdown.index else None
        
        # Days to recover (if already recovered)
        if peak_date and not pd.isna(peak_date):
            peak_price = prices[peak_date]
            future_prices = prices[max_dd_date:]
            recovery_idx = future_prices[future_prices >= peak_price].index
            if len(recovery_idx) > 0:
                recovery_date = recovery_idx[0]
                recovery_days = (recovery_date - max_dd_date).days
            else:
                recovery_days = None  # Not yet recovered
                recovery_date = None
        else:
            recovery_days = None
            recovery_date = None
        
        # Calculate downside deviation (volatility of negative returns only)
        negative_returns = returns[returns < 0]
        downside_deviation = negative_returns.std() * np.sqrt(252) * 100  # Annualized
        
        # Calculate Sortino ratio (reward/downside risk)
        mean_return = returns.mean() * 252  # Annualized
        risk_free_rate = 0.07  # India 10Y G-Sec ~7%
        excess_return = mean_return - risk_free_rate
        
        if downside_deviation > 0:
            sortino_ratio = excess_return / (downside_deviation / 100)
        else:
            sortino_ratio = None
        
        # Current drawdown from all-time high
        current_price = prices.iloc[-1]
        all_time_high = prices.max()
        current_drawdown = ((current_price - all_time_high) / all_time_high) * 100
        
        return _safe_json_dumps({
            "symbol": symbol,
            "max_drawdown": {
                "percentage": max_drawdown,
                "peak_date": peak_date.strftime("%Y-%m-%d") if peak_date and not pd.isna(peak_date) else None,
                "trough_date": max_dd_date.strftime("%Y-%m-%d") if not pd.isna(max_dd_date) else None,
                "recovery_date": recovery_date.strftime("%Y-%m-%d") if recovery_date else "Not recovered",
                "recovery_days": recovery_days,
            },
            "current_drawdown": current_drawdown,
            "downside_deviation": downside_deviation,
            "sortino_ratio": sortino_ratio,
            "interpretation": {
                "max_drawdown": (
                    "Low drawdown risk" if max_drawdown > -15
                    else "Moderate drawdown risk" if max_drawdown > -30
                    else "High drawdown risk"
                ),
                "sortino": (
                    "Excellent risk-adjusted returns" if sortino_ratio and sortino_ratio > 2
                    else "Good risk-adjusted returns" if sortino_ratio and sortino_ratio > 1
                    else "Poor risk-adjusted returns" if sortino_ratio and sortino_ratio > 0
                    else "Negative returns" if sortino_ratio else "N/A"
                ),
            },
        })
        
    except Exception as e:
        return _safe_json_dumps({
            "error": f"Downside metrics error: {str(e)}",
            "DATA_UNAVAILABLE": True,
        })


@tool("Assess Leverage Risk")
def assess_leverage_risk(symbol: str) -> str:
    """
    Evaluate leverage and refinancing risk using debt/equity ratio,
    interest coverage, and debt maturity profile (if available).
    
    Args:
        symbol: Stock symbol (e.g., 'RELIANCE', 'TCS')
        
    Returns:
        JSON with leverage assessment and refinancing risk flags.
    """
    try:
        symbol = symbol.upper().strip()
        ticker = yf.Ticker(_get_nse_symbol(symbol))
        info = ticker.info
        
        # Get leverage metrics
        debt_to_equity = info.get('debtToEquity')
        total_debt = info.get('totalDebt')
        total_equity = info.get('totalStockholderEquity')
        interest_coverage = info.get('interestCoverage')
        
        # Calculate debt/equity if not available but components are
        if not debt_to_equity and total_debt and total_equity and total_equity > 0:
            debt_to_equity = (total_debt / total_equity) * 100
        
        if not debt_to_equity:
            return _safe_json_dumps({
                "error": "Debt metrics not available",
                "DATA_UNAVAILABLE": True,
                "message": "Cannot assess leverage without debt data",
            })
        
        # Assess leverage level
        if debt_to_equity < 50:
            leverage_level = "Low"
            leverage_risk = "Minimal"
        elif debt_to_equity < 100:
            leverage_level = "Moderate"
            leverage_risk = "Manageable"
        elif debt_to_equity < 200:
            leverage_level = "High"
            leverage_risk = "Elevated"
        else:
            leverage_level = "Very High"
            leverage_risk = "Significant distress risk"
        
        # Assess interest coverage
        if interest_coverage:
            if interest_coverage > 5:
                coverage_status = "Strong - can easily service debt"
            elif interest_coverage > 2.5:
                coverage_status = "Adequate - comfortable margin"
            elif interest_coverage > 1:
                coverage_status = "Weak - tight coverage"
            else:
                coverage_status = "Critical - earnings below interest"
        else:
            coverage_status = "Not available"
        
        # Overall leverage risk score (1-10)
        risk_score = 1.0
        
        if debt_to_equity > 200:
            risk_score += 4
        elif debt_to_equity > 100:
            risk_score += 2
        elif debt_to_equity > 50:
            risk_score += 1
        
        if interest_coverage:
            if interest_coverage < 1:
                risk_score += 4
            elif interest_coverage < 2.5:
                risk_score += 2
            elif interest_coverage < 5:
                risk_score += 1
        
        risk_score = min(10, risk_score)
        
        # Refinancing risk flags
        refinancing_risks = []
        if debt_to_equity > 150:
            refinancing_risks.append("High leverage reduces financing flexibility")
        if interest_coverage and interest_coverage < 2:
            refinancing_risks.append("Tight interest coverage - vulnerable to rate hikes")
        if not interest_coverage:
            refinancing_risks.append("Interest coverage not available - unable to assess")
        
        return _safe_json_dumps({
            "symbol": symbol,
            "debt_to_equity": debt_to_equity,
            "total_debt": total_debt,
            "total_equity": total_equity,
            "interest_coverage": interest_coverage,
            "leverage_assessment": {
                "level": leverage_level,
                "risk": leverage_risk,
                "risk_score": risk_score,
            },
            "interest_coverage_status": coverage_status,
            "refinancing_risks": refinancing_risks,
            "recommendation": (
                "Low leverage risk" if risk_score <= 3
                else "Monitor leverage" if risk_score <= 6
                else "High leverage risk - caution advised"
            ),
        })
        
    except Exception as e:
        return _safe_json_dumps({
            "error": f"Leverage assessment error: {str(e)}",
            "DATA_UNAVAILABLE": True,
        })


@tool("Calculate Stop Loss Levels")
def calculate_stop_loss_levels(symbol: str) -> str:
    """
    Calculate stop-loss levels using ATR (Average True Range) and
    support levels from technical analysis.
    
    Args:
        symbol: Stock symbol (e.g., 'RELIANCE', 'TCS')
        
    Returns:
        JSON with conservative, moderate, and aggressive stop-loss prices.
    """
    try:
        symbol = symbol.upper().strip()
        ticker = yf.Ticker(_get_nse_symbol(symbol))
        
        # Get 6 months of data
        hist = ticker.history(period="6mo")
        
        if hist.empty or len(hist) < 50:
            return _safe_json_dumps({
                "error": "Insufficient data for stop-loss calculation",
                "DATA_UNAVAILABLE": True,
            })
        
        current_price = hist['Close'].iloc[-1]
        
        # Calculate ATR (Average True Range)
        high = hist['High']
        low = hist['Low']
        close = hist['Close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = true_range.rolling(window=14).mean().iloc[-1]
        
        # ATR-based stop losses
        conservative_sl = current_price - (3 * atr)  # 3x ATR
        moderate_sl = current_price - (2 * atr)      # 2x ATR
        aggressive_sl = current_price - (1.5 * atr)  # 1.5x ATR
        
        # Support levels (recent lows)
        recent_low_3m = hist['Low'].iloc[-63:].min()  # 3 months
        recent_low_1m = hist['Low'].iloc[-21:].min()  # 1 month
        
        # Recommend stop-loss by combining methods
        conservative_stops = [conservative_sl, recent_low_3m]
        moderate_stops = [moderate_sl, recent_low_1m]
        
        final_conservative = max([s for s in conservative_stops if s > 0])
        final_moderate = max([s for s in moderate_stops if s > 0])
        
        # Calculate percentage below current price
        conservative_pct = ((final_conservative - current_price) / current_price) * 100
        moderate_pct = ((final_moderate - current_price) / current_price) * 100
        aggressive_pct = ((aggressive_sl - current_price) / current_price) * 100
        
        return _safe_json_dumps({
            "symbol": symbol,
            "current_price": current_price,
            "atr": atr,
            "stop_loss_levels": {
                "conservative": {
                    "price": final_conservative,
                    "pct_below": conservative_pct,
                    "description": "Based on 3x ATR and 3-month low",
                },
                "moderate": {
                    "price": final_moderate,
                    "pct_below": moderate_pct,
                    "description": "Based on 2x ATR and 1-month low",
                },
                "aggressive": {
                    "price": aggressive_sl,
                    "pct_below": aggressive_pct,
                    "description": "Based on 1.5x ATR",
                },
            },
            "support_levels": {
                "3_month_low": recent_low_3m,
                "1_month_low": recent_low_1m,
            },
            "recommendation": "Use conservative stop for long-term positions, moderate for swing trades",
        })
        
    except Exception as e:
        return _safe_json_dumps({
            "error": f"Stop-loss calculation error: {str(e)}",
            "DATA_UNAVAILABLE": True,
        })


@tool("Model Scenario Risks")
def model_scenario_risks(symbol: str) -> str:
    """
    Model impact of adverse scenarios: interest rate hikes, commodity shocks,
    demand slowdown. Estimates potential price impact of each scenario.
    
    Args:
        symbol: Stock symbol (e.g., 'RELIANCE', 'TCS')
        
    Returns:
        JSON with scenario impacts and probabilities.
    """
    try:
        symbol = symbol.upper().strip()
        ticker = yf.Ticker(_get_nse_symbol(symbol))
        info = ticker.info
        hist = ticker.history(period="1y")
        
        if hist.empty:
            return _safe_json_dumps({
                "error": "No historical data available",
                "DATA_UNAVAILABLE": True,
            })
        
        current_price = hist['Close'].iloc[-1]
        beta = info.get('beta', 1.0) or 1.0  # Default to market if not available
        
        # Get historical volatility
        returns = hist['Close'].pct_change().dropna()
        annual_vol = returns.std() * np.sqrt(252)
        
        # Define adverse scenarios
        scenarios = {
            "rate_hike": {
                "description": "RBI raises repo rate by 100 bps",
                "probability": 0.15,
                "impact_logic": "Higher rates compress valuations, reduce consumer demand",
                "estimated_impact_pct": -10 * (beta / 1.0),  # Beta-adjusted market impact
            },
            "commodity_shock": {
                "description": "Crude oil rises 20% or key input cost surge",
                "probability": 0.20,
                "impact_logic": "Higher input costs squeeze margins, reduce profitability",
                "estimated_impact_pct": -8 if beta > 1 else -5,  # Cyclicals more exposed
            },
            "demand_shock": {
                "description": "Revenue falls 15% due to demand slowdown",
                "probability": 0.10,
                "impact_logic": "Earnings miss cascades to multiple compression",
                "estimated_impact_pct": -15 * (1 + (annual_vol - 0.25)),  # Higher vol = bigger impact
            },
            "sector_downturn": {
                "description": "Sector-specific headwinds (regulation, competition)",
                "probability": 0.25,
                "impact_logic": "Sector rotation, bearish sector sentiment",
                "estimated_impact_pct": -12,
            },
        }
        
        # Calculate target prices under each scenario
        for scenario_name, scenario in scenarios.items():
            impact_pct = scenario['estimated_impact_pct']
            target_price = current_price * (1 + impact_pct / 100)
            scenario['target_price'] = target_price
            scenario['price_change'] = target_price - current_price
        
        # Calculate worst-case combined scenario (if 2-3 scenarios hit together)
        worst_case_impact = -30  # Multiple shocks compound
        worst_case_price = current_price * (1 + worst_case_impact / 100)
        
        return _safe_json_dumps({
            "symbol": symbol,
            "current_price": current_price,
            "beta": beta,
            "annual_volatility": annual_vol * 100,
            "scenarios": scenarios,
            "worst_case": {
                "description": "Multiple adverse scenarios compound",
                "probability": 0.05,
                "target_price": worst_case_price,
                "impact_pct": worst_case_impact,
            },
            "interpretation": "Model shows potential downside under stress conditions",
        })
        
    except Exception as e:
        return _safe_json_dumps({
            "error": f"Scenario modeling error: {str(e)}",
            "DATA_UNAVAILABLE": True,
        })
