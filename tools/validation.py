"""
Data Quality Validation Tools
Validates input data for accuracy, completeness, and consistency
"""

import json
import yfinance as yf
from crewai.tools import tool

from tools.market_data import get_nse_stock_quote


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


@tool("Validate Symbol Existence")
def validate_symbol_existence(symbol: str) -> str:
    """
    Validate that a stock symbol exists and is actively traded on NSE/BSE.
    Checks if ticker returns valid data from Yahoo Finance.
    
    Args:
        symbol: Stock symbol (e.g., 'RELIANCE', 'TCS')
        
    Returns:
        JSON with validation result and status.
    """
    try:
        symbol = symbol.upper().strip()
        ticker = yf.Ticker(_get_nse_symbol(symbol))
        
        # Try to get basic info
        info = ticker.info
        
        # Check if we got meaningful data
        if not info or len(info) < 5:
            return _safe_json_dumps({
                "validation_passed": False,
                "symbol": symbol,
                "issues": ["Symbol not found or no data available"],
                "confidence": 0.0,
                "recommendation": "ABORT - Invalid symbol",
            })
        
        # Check if actively trading
        current_price = info.get('currentPrice') or info.get('regularMarketPrice')
        if not current_price or current_price <= 0:
            return _safe_json_dumps({
                "validation_passed": False,
                "symbol": symbol,
                "issues": ["Symbol exists but has no current price (may be delisted)"],
                "confidence": 0.2,
                "recommendation": "ABORT - Cannot analyze without valid price",
            })
        
        # Get recent history to confirm active trading
        hist = ticker.history(period="5d")
        if hist.empty:
            return _safe_json_dumps({
                "validation_passed": False,
                "symbol": symbol,
                "issues": ["No recent trading history found"],
                "confidence": 0.3,
                "recommendation": "ABORT - Possibly suspended or delisted",
            })
        
        return _safe_json_dumps({
            "validation_passed": True,
            "symbol": symbol,
            "issues": [],
            "confidence": 1.0,
            "company_name": info.get('longName', 'N/A'),
            "exchange": info.get('exchange', 'N/A'),
            "recommendation": "PROCEED",
        })
        
    except Exception as e:
        return _safe_json_dumps({
            "validation_passed": False,
            "symbol": symbol,
            "issues": [f"Validation error: {str(e)}"],
            "confidence": 0.0,
            "recommendation": "ABORT - Symbol validation failed",
        })


@tool("Cross-Validate Price Sources")
def cross_validate_price_sources(symbol: str) -> str:
    """
    Compare stock price from multiple sources (Yahoo Finance vs NSE) to detect discrepancies.
    If prices diverge by >2%, flags a warning for manual review.
    
    Args:
        symbol: Stock symbol (e.g., 'RELIANCE', 'TCS')
        
    Returns:
        JSON with price comparison and validation status.
    """
    try:
        symbol = symbol.upper().strip()
        
        # Get Yahoo Finance price
        ticker = yf.Ticker(_get_nse_symbol(symbol))
        info = ticker.info
        yahoo_price = info.get('currentPrice') or info.get('regularMarketPrice')
        
        if not yahoo_price:
            return _safe_json_dumps({
                "validation_passed": False,
                "symbol": symbol,
                "issues": ["Cannot retrieve Yahoo Finance price"],
                "confidence": 0.3,
                "yahoo_price": None,
                "nse_price": None,
                "divergence_pct": None,
                "recommendation": "Use caution - limited price validation",
            })
        
        # Try to get NSE price (may fail due to rate limiting)
        try:
            nse_result = json.loads(get_nse_stock_quote(symbol))
            if nse_result.get("DATA_UNAVAILABLE"):
                # NSE unavailable, proceed with Yahoo only
                return _safe_json_dumps({
                    "validation_passed": True,
                    "symbol": symbol,
                    "issues": ["NSE price unavailable, using Yahoo Finance only"],
                    "confidence": 0.7,
                    "yahoo_price": yahoo_price,
                    "nse_price": None,
                    "divergence_pct": None,
                    "recommendation": "PROCEED - Single source validated",
                })
            
            nse_price = nse_result.get('lastPrice')
            if not nse_price:
                return _safe_json_dumps({
                    "validation_passed": True,
                    "symbol": symbol,
                    "issues": ["NSE price format unexpected"],
                    "confidence": 0.7,
                    "yahoo_price": yahoo_price,
                    "nse_price": None,
                    "divergence_pct": None,
                    "recommendation": "PROCEED - Yahoo Finance validated",
                })
            
            # Calculate divergence
            divergence_pct = abs(yahoo_price - nse_price) / yahoo_price * 100
            
            if divergence_pct > 2.0:
                return _safe_json_dumps({
                    "validation_passed": False,
                    "symbol": symbol,
                    "issues": [f"Price divergence of {divergence_pct:.2f}% between sources"],
                    "confidence": 0.5,
                    "yahoo_price": yahoo_price,
                    "nse_price": nse_price,
                    "divergence_pct": divergence_pct,
                    "recommendation": "CAUTION - Use most recent price, note discrepancy in report",
                })
            
            # Prices match within tolerance
            return _safe_json_dumps({
                "validation_passed": True,
                "symbol": symbol,
                "issues": [],
                "confidence": 1.0,
                "yahoo_price": yahoo_price,
                "nse_price": nse_price,
                "divergence_pct": divergence_pct,
                "recommendation": "PROCEED - Prices validated across sources",
            })
            
        except Exception as nse_error:
            # NSE fetch failed, not critical
            return _safe_json_dumps({
                "validation_passed": True,
                "symbol": symbol,
                "issues": [f"NSE unavailable ({str(nse_error)[:50]}), using Yahoo Finance"],
                "confidence": 0.7,
                "yahoo_price": yahoo_price,
                "nse_price": None,
                "divergence_pct": None,
                "recommendation": "PROCEED - Yahoo Finance validated",
            })
        
    except Exception as e:
        return _safe_json_dumps({
            "validation_passed": False,
            "symbol": symbol,
            "issues": [f"Price validation error: {str(e)}"],
            "confidence": 0.0,
            "recommendation": "ABORT - Cannot validate any price source",
        })


@tool("Sanity Check Metrics")
def sanity_check_metrics(symbol: str) -> str:
    """
    Validate that financial metrics are within reasonable bounds.
    Flags extreme values like PE > 500, negative market cap, etc.
    
    Args:
        symbol: Stock symbol (e.g., 'RELIANCE', 'TCS')
        
    Returns:
        JSON with sanity check results for各 metrics.
    """
    try:
        symbol = symbol.upper().strip()
        ticker = yf.Ticker(_get_nse_symbol(symbol))
        info = ticker.info
        
        issues = []
        warnings = []
        confidence = 1.0
        
        # Check market cap
        market_cap = info.get('marketCap')
        if market_cap is None:
            warnings.append("Market cap not available")
            confidence -= 0.1
        elif market_cap <= 0:
            issues.append(f"Invalid market cap: {market_cap}")
            confidence -= 0.3
        elif market_cap < 1_000_000:  # < 10 lakh (likely error)
            issues.append(f"Suspiciously low market cap: ₹{market_cap:,.0f}")
            confidence -= 0.2
        
        # Check PE ratio
        pe_ratio = info.get('trailingPE')
        if pe_ratio is not None:
            if pe_ratio < 0:
                warnings.append(f"Negative PE ratio: {pe_ratio:.2f} (company may be loss-making)")
            elif pe_ratio > 500:
                issues.append(f"Extreme PE ratio: {pe_ratio:.2f} (verify if accurate)")
                confidence -= 0.2
            elif pe_ratio > 200:
                warnings.append(f"Very high PE ratio: {pe_ratio:.2f} (growth stock or overvalued)")
        
        # Check PB ratio
        pb_ratio = info.get('priceToBook')
        if pb_ratio is not None:
            if pb_ratio < 0:
                issues.append(f"Negative PB ratio: {pb_ratio:.2f} (negative book value - distress)")
                confidence -= 0.3
            elif pb_ratio > 50:
                issues.append(f"Extreme PB ratio: {pb_ratio:.2f} (verify accuracy)")
                confidence -= 0.1
        
        # Check ROE
        roe = info.get('returnOnEquity')
        if roe is not None:
            roe_pct = roe * 100
            if roe_pct < -100 or roe_pct > 200:
                issues.append(f"Extreme ROE: {roe_pct:.1f}% (verify data quality)")
                confidence -= 0.2
            elif roe_pct < 0:
                warnings.append(f"Negative ROE: {roe_pct:.1f}% (company is loss-making)")
        
        # Check debt to equity
        debt_to_equity = info.get('debtToEquity')
        if debt_to_equity is not None:
            if debt_to_equity < 0:
                issues.append(f"Negative debt-to-equity: {debt_to_equity:.2f} (data error)")
                confidence -= 0.2
            elif debt_to_equity > 1000:
                issues.append(f"Extreme leverage: {debt_to_equity:.2f}x (high distress risk)")
                confidence -= 0.2
        
        # Check current price
        current_price = info.get('currentPrice') or info.get('regularMarketPrice')
        if current_price is not None:
            if current_price <= 0:
                issues.append(f"Invalid price: ₹{current_price}")
                confidence -= 0.4
            elif current_price < 0.01:
                warnings.append(f"Penny stock: ₹{current_price:.4f} (high risk)")
        
        # Check 52-week range
        high_52w = info.get('fiftyTwoWeekHigh')
        low_52w = info.get('fiftyTwoWeekLow')
        if high_52w and low_52w:
            if high_52w < low_52w:
                issues.append(f"Invalid 52W range: High ₹{high_52w} < Low ₹{low_52w}")
                confidence -= 0.2
            elif current_price and (current_price > high_52w * 1.5 or current_price < low_52w * 0.5):
                warnings.append(f"Price outside 52W range: ₹{current_price} vs ₹{low_52w}-₹{high_52w}")
        
        # Determine validation status
        validation_passed = len(issues) == 0
        confidence = max(0.0, min(1.0, confidence))
        
        if not validation_passed:
            recommendation = "CAUTION - Metrics show anomalies, verify data quality"
        elif warnings:
            recommendation = "PROCEED - Minor warnings noted"
        else:
            recommendation = "PROCEED - All metrics within reasonable bounds"
        
        return _safe_json_dumps({
            "validation_passed": validation_passed,
            "symbol": symbol,
            "issues": issues,
            "warnings": warnings,
            "confidence": confidence,
            "metrics_checked": {
                "market_cap": market_cap,
                "pe_ratio": pe_ratio,
                "pb_ratio": pb_ratio,
                "roe_pct": roe * 100 if roe else None,
                "debt_to_equity": debt_to_equity,
                "current_price": current_price,
            },
            "recommendation": recommendation,
        })
        
    except Exception as e:
        return _safe_json_dumps({
            "validation_passed": False,
            "symbol": symbol,
            "issues": [f"Sanity check error: {str(e)}"],
            "confidence": 0.0,
            "recommendation": "ABORT - Cannot validate metrics",
        })


@tool("Calculate Data Quality Score")
def calculate_data_quality_score(symbol: str) -> str:
    """
    Calculate overall data quality score (0-100) based on completeness of available data.
    Checks for presence of price, volume, financials, fundamentals, etc.
    
    Args:
        symbol: Stock symbol (e.g., 'RELIANCE', 'TCS')
        
    Returns:
        JSON with quality score and detailed breakdown.
    """
    try:
        symbol = symbol.upper().strip()
        ticker = yf.Ticker(_get_nse_symbol(symbol))
        info = ticker.info
        
        score = 0
        max_score = 100
        breakdown = {}
        missing_fields = []
        
        # Critical fields (40 points)
        critical_fields = {
            'currentPrice': 10,
            'regularMarketPrice': 10,  # Alternative to currentPrice
            'marketCap': 10,
            'symbol': 10,
        }
        
        current_price_found = False
        for field, points in critical_fields.items():
            if field in ['currentPrice', 'regularMarketPrice']:
                if not current_price_found and info.get(field):
                    score += 10
                    breakdown['current_price'] = 'Available'
                    current_price_found = True
            else:
                if info.get(field):
                    score += points
                    breakdown[field] = 'Available'
                else:
                    missing_fields.append(field)
                    breakdown[field] = 'Missing'
        
        if not current_price_found:
            missing_fields.append('currentPrice/regularMarketPrice')
            breakdown['current_price'] = 'MISSING (Critical)'
        
        # Valuation metrics (30 points)
        valuation_fields = {
            'trailingPE': 6,
            'forwardPE': 4,
            'priceToBook': 6,
            'priceToSalesTrailing12Months': 4,
            'enterpriseValue': 5,
            'enterpriseToEbitda': 5,
        }
        
        for field, points in valuation_fields.items():
            value = info.get(field)
            if value is not None and value != 0:
                score += points
                breakdown[field] = 'Available'
            else:
                missing_fields.append(field)
        
        # Profitability metrics (15 points)
        profitability_fields = {
            'returnOnEquity': 5,
            'returnOnAssets': 5,
            'profitMargins': 5,
        }
        
        for field, points in profitability_fields.items():
            if info.get(field) is not None:
                score += points
                breakdown[field] = 'Available'
            else:
                missing_fields.append(field)
        
        # Financial health (10 points)
        health_fields = {
            'debtToEquity': 5,
            'currentRatio': 5,
        }
        
        for field, points in health_fields.items():
            if info.get(field) is not None:
                score += points
                breakdown[field] = 'Available'
            else:
                missing_fields.append(field)
        
        # Historical data (5 points)
        try:
            hist = ticker.history(period="1mo")
            if not hist.empty and len(hist) >= 10:
                score += 5
                breakdown['historical_data'] = 'Available (1 month)'
            else:
                missing_fields.append('historical_data')
                breakdown['historical_data'] = 'Insufficient'
        except:
            missing_fields.append('historical_data')
            breakdown['historical_data'] = 'Error'
        
        # Determine quality tier
        if score >= 80:
            quality_tier = "HIGH"
            confidence = "Strong"
        elif score >= 60:
            quality_tier = "MEDIUM"
            confidence = "Moderate"
        elif score >= 40:
            quality_tier = "LOW"
            confidence = "Weak"
        else:
            quality_tier = "VERY LOW"
            confidence = "Insufficient"
        
        return _safe_json_dumps({
            "symbol": symbol,
            "quality_score": score,
            "max_score": max_score,
            "quality_tier": quality_tier,
            "confidence": confidence,
            "breakdown": breakdown,
            "missing_fields": missing_fields[:10],  # Top 10 missing
            "recommendation": (
                "PROCEED with high confidence" if score >= 80
                else "PROCEED with caution" if score >= 60
                else "PROCEED with low confidence - limited data" if score >= 40
                else "ABORT or accept very limited analysis"
            ),
        })
        
    except Exception as e:
        return _safe_json_dumps({
            "symbol": symbol,
            "quality_score": 0,
            "max_score": 100,
            "quality_tier": "ERROR",
            "confidence": "None",
            "error": str(e),
            "recommendation": "ABORT - Cannot assess data quality",
        })
