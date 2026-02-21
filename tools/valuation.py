"""
Valuation Modeling Tools
Builds relative valuation models with scenario analysis
"""

import json
from typing import List, Optional, Dict
import yfinance as yf
import pandas as pd
import numpy as np
from crewai.tools import tool

from config import SECTORS


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


def _get_sector_for_symbol(symbol: str) -> Optional[str]:
    """Find which sector a symbol belongs to."""
    symbol = symbol.upper().strip()
    for sector, stocks in SECTORS.items():
        if symbol in stocks:
            return sector
    return None


def _get_peer_stocks(symbol: str, max_peers: int = 4) -> List[str]:
    """Get peer stocks from the same sector."""
    sector = _get_sector_for_symbol(symbol)
    if not sector:
        return []
    
    peers = [s for s in SECTORS[sector] if s != symbol.upper()]
    return peers[:max_peers]


@tool("Get Sector Valuation Multiples")
def get_sector_valuation_multiples(symbol: str) -> str:
    """
    Fetch median valuation multiples (PE, PB, EV/EBITDA) for sector peers.
    Compare the stock's multiples to sector median and return percentile rank.
    
    Args:
        symbol: Stock symbol (e.g., 'RELIANCE', 'TCS')
        
    Returns:
        JSON with sector peer comparison and percentile rankings.
    """
    try:
        symbol = symbol.upper().strip()
        sector = _get_sector_for_symbol(symbol)
        
        if not sector:
            return _safe_json_dumps({
                "error": f"Symbol {symbol} not found in predefined sectors",
                "DATA_UNAVAILABLE": True,
                "message": "Cannot perform peer comparison without sector classification",
            })
        
        peers = _get_peer_stocks(symbol, max_peers=5)
        if not peers:
            return _safe_json_dumps({
                "error": f"No peers found for {symbol} in sector {sector}",
                "DATA_UNAVAILABLE": True,
                "message": "Insufficient peers for comparison",
            })
        
        # Fetch data for all peers + the stock itself
        all_symbols = [symbol] + peers
        peer_data = []
        
        for sym in all_symbols:
            try:
                ticker = yf.Ticker(_get_nse_symbol(sym))
                info = ticker.info
                
                peer_data.append({
                    "symbol": sym,
                    "pe_ratio": info.get('trailingPE'),
                    "forward_pe": info.get('forwardPE'),
                    "pb_ratio": info.get('priceToBook'),
                    "ev_ebitda": info.get('enterpriseToEbitda'),
                    "roe": info.get('returnOnEquity'),
                    "profit_margin": info.get('profitMargins'),
                    "market_cap": info.get('marketCap'),
                })
            except:
                continue
        
        if len(peer_data) < 2:
            return _safe_json_dumps({
                "error": "Insufficient peer data retrieved",
                "DATA_UNAVAILABLE": True,
                "message": "Cannot calculate sector multiples",
            })
        
        # Calculate sector medians (excluding the target stock)
        peer_metrics = [p for p in peer_data if p['symbol'] != symbol]
        
        def safe_median(values):
            valid = [v for v in values if v is not None and not pd.isna(v)]
            return np.median(valid) if valid else None
        
        sector_medians = {
            "pe_ratio": safe_median([p['pe_ratio'] for p in peer_metrics]),
            "forward_pe": safe_median([p['forward_pe'] for p in peer_metrics]),
            "pb_ratio": safe_median([p['pb_ratio'] for p in peer_metrics]),
            "ev_ebitda": safe_median([p['ev_ebitda'] for p in peer_metrics]),
            "roe": safe_median([p['roe'] for p in peer_metrics]),
            "profit_margin": safe_median([p['profit_margin'] for p in peer_metrics]),
        }
        
        # Get target stock metrics
        target_stock = next((p for p in peer_data if p['symbol'] == symbol), None)
        if not target_stock:
            return _safe_json_dumps({
                "error": f"Could not retrieve data for {symbol}",
                "DATA_UNAVAILABLE": True,
            })
        
        # Calculate percentile ranks
        def percentile_rank(value, peer_values):
            if value is None or pd.isna(value):
                return None
            valid_peers = [v for v in peer_values if v is not None and not pd.isna(v)]
            if not valid_peers:
                return None
            below = sum(1 for v in valid_peers if v < value)
            return (below / len(valid_peers)) * 100
        
        percentiles = {
            "pe_ratio": percentile_rank(target_stock['pe_ratio'], [p['pe_ratio'] for p in peer_metrics]),
            "pb_ratio": percentile_rank(target_stock['pb_ratio'], [p['pb_ratio'] for p in peer_metrics]),
            "ev_ebitda": percentile_rank(target_stock['ev_ebitda'], [p['ev_ebitda'] for p in peer_metrics]),
            "roe": percentile_rank(target_stock['roe'], [p['roe'] for p in peer_metrics]),
        }
        
        return _safe_json_dumps({
            "symbol": symbol,
            "sector": sector,
            "peer_count": len(peer_metrics),
            "peers": [p['symbol'] for p in peer_metrics],
            "target_metrics": target_stock,
            "sector_medians": sector_medians,
            "percentile_ranks": percentiles,
            "interpretation": {
                "relative_valuation": (
                    "Premium to sector" if percentiles.get('pe_ratio', 50) > 60
                    else "Discount to sector" if percentiles.get('pe_ratio', 50) < 40
                    else "In-line with sector"
                ),
                "relative_quality": (
                    "Above average quality" if percentiles.get('roe', 50) > 60
                    else "Below average quality" if percentiles.get('roe', 50) < 40
                    else "Average quality"
                ),
            },
        })
        
    except Exception as e:
        return _safe_json_dumps({
            "error": f"Sector valuation error: {str(e)}",
            "DATA_UNAVAILABLE": True,
            "message": "Cannot calculate sector multiples",
        })


@tool("Calculate Relative Valuation")
def calculate_relative_valuation(symbol: str) -> str:
    """
    Calculate fair value range using peer median multiples applied to stock's earnings.
    Returns implied fair value based on sector PE, PB, and EV/EBITDA.
    
    Args:
        symbol: Stock symbol (e.g., 'RELIANCE', 'TCS')
        
    Returns:
        JSON with fair value range and upside/downside percentages.
    """
    try:
        symbol = symbol.upper().strip()
        ticker = yf.Ticker(_get_nse_symbol(symbol))
        info = ticker.info
        
        current_price = info.get('currentPrice') or info.get('regularMarketPrice')
        if not current_price:
            return _safe_json_dumps({
                "error": "Current price not available",
                "DATA_UNAVAILABLE": True,
            })
        
        # Get sector multiples
        sector_data = json.loads(get_sector_valuation_multiples(symbol))
        if sector_data.get("DATA_UNAVAILABLE"):
            return _safe_json_dumps({
                "error": "Cannot calculate valuation without sector comparison",
                "DATA_UNAVAILABLE": True,
            })
        
        sector_medians = sector_data.get('sector_medians', {})
        
        # Calculate fair values using different methodologies
        fair_values = []
        
        # Method 1: PE-based valuation
        eps = info.get('trailingEps')
        sector_pe = sector_medians.get('pe_ratio')
        if eps and sector_pe and eps > 0:
            fair_value_pe = eps * sector_pe
            fair_values.append(('PE-based', fair_value_pe))
        
        # Method 2: PB-based valuation
        book_value = info.get('bookValue')
        sector_pb = sector_medians.get('pb_ratio')
        if book_value and sector_pb and book_value > 0:
            fair_value_pb = book_value * sector_pb
            fair_values.append(('PB-based', fair_value_pb))
        
        # Method 3: Forward PE-based (if available)
        forward_eps = info.get('forwardEps')
        sector_forward_pe = sector_medians.get('forward_pe')
        if forward_eps and sector_forward_pe and forward_eps > 0:
            fair_value_forward = forward_eps * sector_forward_pe
            fair_values.append(('Forward PE-based', fair_value_forward))
        
        if not fair_values:
            return _safe_json_dumps({
                "error": "Insufficient data for valuation calculation",
                "DATA_UNAVAILABLE": True,
            })
        
        # Calculate average fair value and range
        values = [v[1] for v in fair_values]
        avg_fair_value = np.mean(values)
        min_fair_value = min(values)
        max_fair_value = max(values)
        
        # Calculate upside/downside
        upside_pct = ((max_fair_value - current_price) / current_price) * 100
        downside_pct = ((min_fair_value - current_price) / current_price) * 100
        avg_upside_pct = ((avg_fair_value - current_price) / current_price) * 100
        
        return _safe_json_dumps({
            "symbol": symbol,
            "current_price": current_price,
            "fair_value_range": {
                "min": min_fair_value,
                "average": avg_fair_value,
                "max": max_fair_value,
            },
            "valuation_methods": [{"method": m, "fair_value": v} for m, v in fair_values],
            "upside_downside": {
                "to_min": downside_pct,
                "to_average": avg_upside_pct,
                "to_max": upside_pct,
            },
            "valuation_verdict": (
                "Undervalued" if avg_upside_pct > 15
                else "Overvalued" if avg_upside_pct < -15
                else "Fairly valued"
            ),
        })
        
    except Exception as e:
        return _safe_json_dumps({
            "error": f"Valuation calculation error: {str(e)}",
            "DATA_UNAVAILABLE": True,
        })


@tool("Build Scenario Valuations")
def build_scenario_valuations(symbol: str) -> str:
    """
    Build bull/base/bear scenario valuations with explicit assumptions.
    Models impact of earnings growth changes on target price.
    
    Args:
        symbol: Stock symbol (e.g., 'RELIANCE', 'TCS')
        
    Returns:
        JSON with three scenario target prices and assumptions.
    """
    try:
        symbol = symbol.upper().strip()
        ticker = yf.Ticker(_get_nse_symbol(symbol))
        info = ticker.info
        
        current_price = info.get('currentPrice') or info.get('regularMarketPrice')
        current_pe = info.get('trailingPE')
        current_eps = info.get('trailingEps')
        
        if not all([current_price, current_pe, current_eps]):
            return _safe_json_dumps({
                "error": "Insufficient data for scenario modeling",
                "DATA_UNAVAILABLE": True,
                "message": "Need current price, PE, and EPS for scenarios",
            })
        
        # Get historical growth rate if available
        try:
            hist_data = ticker.history(period="2y")
            if not hist_data.empty:
                historical_volatility = hist_data['Close'].pct_change().std() * (252 ** 0.5)
            else:
                historical_volatility = 0.30  # Default 30%
        except:
            historical_volatility = 0.30
        
        # Define scenario assumptions
        scenarios = {
            "bull": {
                "earnings_growth": 0.20,  # +20% earnings
                "pe_multiple_change": 1.10,  # PE expands by 10%
                "probability": 0.25,
                "description": "Strong earnings beat, sector tailwinds, multiple expansion",
            },
            "base": {
                "earnings_growth": 0.05,  # +5% earnings (conservative)
                "pe_multiple_change": 1.00,  # PE stays same
                "probability": 0.50,
                "description": "In-line earnings, stable multiples, no major surprises",
            },
            "bear": {
                "earnings_growth": -0.15,  # -15% earnings
                "pe_multiple_change": 0.90,  # PE contracts by 10%
                "probability": 0.25,
                "description": "Earnings miss, sector headwinds, multiple compression",
            },
        }
        
        # Calculate target prices for each scenario
        results = {}
        for scenario_name, assumptions in scenarios.items():
            future_eps = current_eps * (1 + assumptions['earnings_growth'])
            future_pe = current_pe * assumptions['pe_multiple_change']
            target_price = future_eps * future_pe
            
            upside = ((target_price - current_price) / current_price) * 100
            
            results[scenario_name] = {
                "assumptions": assumptions,
                "future_eps": future_eps,
                "future_pe": future_pe,
                "target_price": target_price,
                "upside_pct": upside,
            }
        
        # Calculate risk-reward ratio
        bull_upside = results['bull']['upside_pct']
        bear_downside = abs(results['bear']['upside_pct'])
        risk_reward = bull_upside / bear_downside if bear_downside > 0 else None
        
        return _safe_json_dumps({
            "symbol": symbol,
            "current_price": current_price,
            "current_pe": current_pe,
            "current_eps": current_eps,
            "scenarios": results,
            "risk_reward_ratio": risk_reward,
            "recommendation": (
                "Attractive" if risk_reward and risk_reward > 2
                else "Neutral" if risk_reward and risk_reward > 1
                else "Unfavorable" if risk_reward
                else "Insufficient data"
            ),
        })
        
    except Exception as e:
        return _safe_json_dumps({
            "error": f"Scenario modeling error: {str(e)}",
            "DATA_UNAVAILABLE": True,
        })


@tool("Identify Multiple Drivers")
def identify_multiple_drivers(symbol: str) -> str:
    """
    Analyze factors that could drive PE multiple expansion or compression.
    Compares quality metrics (ROE, margins) to peers to justify premium/discount.
    
    Args:
        symbol: Stock symbol (e.g., 'RELIANCE', 'TCS')
        
    Returns:
        JSON with drivers of multiple expansion/compression.
    """
    try:
        symbol = symbol.upper().strip()
        
        # Get sector comparison
        sector_data = json.loads(get_sector_valuation_multiples(symbol))
        if sector_data.get("DATA_UNAVAILABLE"):
            return _safe_json_dumps({
                "error": "Cannot analyze without sector comparison",
                "DATA_UNAVAILABLE": True,
            })
        
        target_metrics = sector_data.get('target_metrics', {})
        sector_medians = sector_data.get('sector_medians', {})
        percentiles = sector_data.get('percentile_ranks', {})
        
        # Identify expansion drivers (positive factors)
        expansion_drivers = []
        
        # ROE premium
        roe_percentile = percentiles.get('roe')
        if roe_percentile and roe_percentile > 60:
            expansion_drivers.append({
                "factor": "Superior ROE vs peers",
                "impact": "Positive",
                "details": f"ROE in top {100-roe_percentile:.0f}% of sector justifies premium valuation",
            })
        
        # Margin strength
        target_margin = target_metrics.get('profit_margin')
        sector_margin = sector_medians.get('profit_margin')
        if target_margin and sector_margin and target_margin > sector_margin * 1.1:
            expansion_drivers.append({
                "factor": "Higher profit margins",
                "impact": "Positive",
                "details": f"Margins {(target_margin*100):.1f}% vs sector {(sector_margin*100):.1f}%",
            })
        
        # Identify compression risks (negative factors)
        compression_risks = []
        
        # ROE weakness
        if roe_percentile and roe_percentile < 40:
            compression_risks.append({
                "factor": "Below-average ROE",
                "impact": "Negative",
                "details": f"ROE in bottom {roe_percentile:.0f}% of sector suggests discount warranted",
            })
        
        # Valuation premium without justification
        pe_percentile = percentiles.get('pe_ratio')
        if pe_percentile and roe_percentile and pe_percentile > 70 and roe_percentile < 50:
            compression_risks.append({
                "factor": "Valuation premium not justified by quality",
                "impact": "Negative",
                "details": f"PE in top 30% but ROE below median - risk of de-rating",
            })
        
        # Overall assessment
        net_bias = len(expansion_drivers) - len(compression_risks)
        
        return _safe_json_dumps({
            "symbol": symbol,
            "expansion_drivers": expansion_drivers,
            "compression_risks": compression_risks,
            "driver_count": {
                "positive": len(expansion_drivers),
                "negative": len(compression_risks),
            },
            "multiple_bias": (
                "Expansion likely" if net_bias > 0
                else "Compression risk" if net_bias < 0
                else "Stable"
            ),
            "quality_metrics": {
                "roe_percentile": roe_percentile,
                "pe_percentile": pe_percentile,
                "margin_vs_sector": (
                    ((target_margin / sector_margin) - 1) * 100
                    if target_margin and sector_margin else None
                ),
            },
        })
        
    except Exception as e:
        return _safe_json_dumps({
            "error": f"Multiple driver analysis error: {str(e)}",
            "DATA_UNAVAILABLE": True,
        })
