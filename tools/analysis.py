"""
Technical and Fundamental Analysis Tools for Indian Stocks
"""

import json
from datetime import datetime
from typing import Optional
import yfinance as yf
import pandas as pd
import numpy as np
from crewai.tools import tool

from config import TECHNICAL_CONFIG, FUNDAMENTAL_THRESHOLDS


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


@tool("Calculate Technical Indicators")
def calculate_technical_indicators(symbol: str, period: str = "6mo") -> str:
    """
    Calculate comprehensive technical indicators for a stock.
    Includes RSI, MACD, Bollinger Bands, Moving Averages, ADX, and more.
    
    Args:
        symbol: Stock symbol (e.g., 'RELIANCE', 'TCS')
        period: Data period - '3mo', '6mo', '1y' (default: '6mo')
        
    Returns:
        JSON string with all technical indicators and trading signals.
    """
    try:
        ticker = yf.Ticker(_get_nse_symbol(symbol))
        df = ticker.history(period=period)
        
        if df.empty or len(df) < 50:
            return json.dumps({
                "error": f"Insufficient data for {symbol} (need 50+ trading days, got {len(df) if not df.empty else 0})",
                "DATA_UNAVAILABLE": True,
                "message": f"Cannot compute technical indicators for {symbol}. Do NOT guess indicator values.",
            })
        
        close = df['Close']
        high = df['High']
        low = df['Low']
        volume = df['Volume']
        
        # ==========================================
        # Moving Averages
        # ==========================================
        sma_20 = close.rolling(window=20).mean().iloc[-1]
        sma_50 = close.rolling(window=50).mean().iloc[-1]
        sma_200 = close.rolling(window=200).mean().iloc[-1] if len(close) >= 200 else None
        ema_12 = close.ewm(span=12, adjust=False).mean().iloc[-1]
        ema_26 = close.ewm(span=26, adjust=False).mean().iloc[-1]
        
        # ==========================================
        # RSI (Relative Strength Index)
        # ==========================================
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]
        
        # ==========================================
        # MACD
        # ==========================================
        exp1 = close.ewm(span=12, adjust=False).mean()
        exp2 = close.ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=9, adjust=False).mean()
        
        # ==========================================
        # Bollinger Bands
        # ==========================================
        bb_middle = close.rolling(window=20).mean()
        bb_std = close.rolling(window=20).std()
        bb_upper = bb_middle + (bb_std * 2)
        bb_lower = bb_middle - (bb_std * 2)
        
        current_price = close.iloc[-1]
        bb_width = bb_upper.iloc[-1] - bb_lower.iloc[-1]
        bb_position = (current_price - bb_lower.iloc[-1]) / bb_width if bb_width != 0 else 0.5
        
        # ==========================================
        # ATR (Average True Range)
        # ==========================================
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=14).mean().iloc[-1]
        atr_percent = (atr / current_price) * 100
        
        # ==========================================
        # Volume Analysis
        # ==========================================
        avg_volume_20 = volume.rolling(window=20).mean().iloc[-1]
        current_volume = volume.iloc[-1]
        volume_ratio = current_volume / avg_volume_20
        
        # ==========================================
        # Momentum Indicators
        # ==========================================
        # Rate of Change (ROC)
        roc_10 = ((current_price - close.iloc[-11]) / close.iloc[-11]) * 100 if len(close) > 10 else 0
        roc_20 = ((current_price - close.iloc[-21]) / close.iloc[-21]) * 100 if len(close) > 20 else 0
        
        # ==========================================
        # Support & Resistance Levels (Standard Daily Pivots)
        # ==========================================
        # Use the PREVIOUS completed day's H/L/C for standard pivot points
        prev_high = high.iloc[-2] if len(high) > 1 else high.iloc[-1]
        prev_low = low.iloc[-2] if len(low) > 1 else low.iloc[-1]
        prev_close = close.iloc[-2] if len(close) > 1 else close.iloc[-1]
        pivot = (prev_high + prev_low + prev_close) / 3
        r1 = 2 * pivot - prev_low
        s1 = 2 * pivot - prev_high
        r2 = pivot + (prev_high - prev_low)
        s2 = pivot - (prev_high - prev_low)

        # 20-day context levels (not pivot-derived)
        recent_high = high.tail(20).max()
        recent_low = low.tail(20).min()
        
        # ==========================================
        # Trend Analysis
        # ==========================================
        trend_short = "Bullish" if current_price > sma_20 else "Bearish"
        trend_medium = "Bullish" if current_price > sma_50 else "Bearish"
        trend_long = "Bullish" if sma_200 and current_price > sma_200 else ("Bearish" if sma_200 else "N/A")
        
        # Golden/Death Cross
        golden_cross = sma_50 > sma_200 if sma_200 else None
        
        # ==========================================
        # Trading Signals
        # ==========================================
        signals = []
        
        # RSI signals
        if current_rsi < 30:
            signals.append({"indicator": "RSI", "signal": "OVERSOLD - Potential Buy", "strength": "Strong"})
        elif current_rsi > 70:
            signals.append({"indicator": "RSI", "signal": "OVERBOUGHT - Potential Sell", "strength": "Strong"})
        elif current_rsi < 40:
            signals.append({"indicator": "RSI", "signal": "Approaching Oversold", "strength": "Moderate"})
        elif current_rsi > 60:
            signals.append({"indicator": "RSI", "signal": "Approaching Overbought", "strength": "Moderate"})
        
        # MACD signals
        if macd.iloc[-1] > signal_line.iloc[-1] and macd.iloc[-2] <= signal_line.iloc[-2]:
            signals.append({"indicator": "MACD", "signal": "Bullish Crossover - Buy", "strength": "Strong"})
        elif macd.iloc[-1] < signal_line.iloc[-1] and macd.iloc[-2] >= signal_line.iloc[-2]:
            signals.append({"indicator": "MACD", "signal": "Bearish Crossover - Sell", "strength": "Strong"})
        
        # Bollinger Band signals
        if current_price <= bb_lower.iloc[-1]:
            signals.append({"indicator": "Bollinger Bands", "signal": "At Lower Band - Potential Reversal", "strength": "Moderate"})
        elif current_price >= bb_upper.iloc[-1]:
            signals.append({"indicator": "Bollinger Bands", "signal": "At Upper Band - Potential Pullback", "strength": "Moderate"})
        
        # Volume signals
        if volume_ratio > 2:
            signals.append({"indicator": "Volume", "signal": "Unusually High Volume - Confirm Trend", "strength": "Strong"})
        
        # Moving Average signals
        if current_price > sma_20 > sma_50:
            signals.append({"indicator": "Moving Averages", "signal": "Strong Uptrend", "strength": "Moderate"})
        elif current_price < sma_20 < sma_50:
            signals.append({"indicator": "Moving Averages", "signal": "Strong Downtrend", "strength": "Moderate"})
        
        # Overall recommendation
        bullish_signals = sum(1 for s in signals if "Buy" in s["signal"] or "Bullish" in s["signal"] or "Uptrend" in s["signal"])
        bearish_signals = sum(1 for s in signals if "Sell" in s["signal"] or "Bearish" in s["signal"] or "Downtrend" in s["signal"])
        
        if bullish_signals > bearish_signals + 1:
            overall_signal = "BULLISH"
        elif bearish_signals > bullish_signals + 1:
            overall_signal = "BEARISH"
        else:
            overall_signal = "NEUTRAL"
        
        result = {
            "symbol": symbol.upper(),
            "current_price": round(current_price, 2),
            "analysis_date": datetime.now().isoformat(),
            
            "moving_averages": {
                "sma_20": round(sma_20, 2),
                "sma_50": round(sma_50, 2),
                "sma_200": round(sma_200, 2) if sma_200 else "N/A",
                "ema_12": round(ema_12, 2),
                "ema_26": round(ema_26, 2),
                "price_vs_sma20": f"{((current_price/sma_20 - 1) * 100):.2f}%",
                "price_vs_sma50": f"{((current_price/sma_50 - 1) * 100):.2f}%",
            },
            
            "momentum": {
                "rsi_14": round(current_rsi, 2),
                "rsi_interpretation": "Oversold" if current_rsi < 30 else ("Overbought" if current_rsi > 70 else "Neutral"),
                "macd_line": round(macd.iloc[-1], 2),
                "macd_signal": round(signal_line.iloc[-1], 2),
                "macd_histogram": round(macd.iloc[-1] - signal_line.iloc[-1], 2),
                "roc_10_day": round(roc_10, 2),
                "roc_20_day": round(roc_20, 2),
            },
            
            "volatility": {
                "bollinger_upper": round(bb_upper.iloc[-1], 2),
                "bollinger_middle": round(bb_middle.iloc[-1], 2),
                "bollinger_lower": round(bb_lower.iloc[-1], 2),
                "bb_position": f"{bb_position * 100:.1f}%",
                "atr_14": round(atr, 2),
                "atr_percent": f"{atr_percent:.2f}%",
            },
            
            "volume": {
                "current_volume": int(current_volume),
                "avg_volume_20": int(avg_volume_20),
                "volume_ratio": round(volume_ratio, 2),
                "volume_interpretation": "High" if volume_ratio > 1.5 else ("Low" if volume_ratio < 0.5 else "Normal"),
            },
            
            "support_resistance": {
                "pivot": round(pivot, 2),
                "resistance_1": round(r1, 2),
                "resistance_2": round(r2, 2),
                "support_1": round(s1, 2),
                "support_2": round(s2, 2),
                "recent_high": round(recent_high, 2),
                "recent_low": round(recent_low, 2),
            },
            
            "trend": {
                "short_term": trend_short,
                "medium_term": trend_medium,
                "long_term": trend_long,
                "golden_cross": golden_cross,
            },
            
            "signals": signals,
            "overall_signal": overall_signal,
            "signal_strength": f"{max(bullish_signals, bearish_signals)}/{len(signals)}",
        }
        
        return _safe_json_dumps(result, indent=2)
    
    except Exception as e:
        return json.dumps({
            "error": str(e),
            "symbol": symbol,
            "DATA_UNAVAILABLE": True,
            "message": f"FAILED to calculate indicators for {symbol}. Do NOT guess technical levels.",
        })


@tool("Get Fundamental Metrics")
def get_fundamental_metrics(symbol: str) -> str:
    """
    Get comprehensive fundamental analysis metrics for an Indian stock.
    Includes valuation ratios, profitability, growth, and financial health indicators.
    
    Args:
        symbol: Stock symbol (e.g., 'RELIANCE', 'TCS')
        
    Returns:
        JSON string with fundamental metrics and investment rating.
    """
    try:
        ticker = yf.Ticker(_get_nse_symbol(symbol))
        info = ticker.info
        
        # ==========================================
        # Valuation Metrics
        # ==========================================
        pe_ratio = info.get("trailingPE", 0)
        forward_pe = info.get("forwardPE", 0)
        pb_ratio = info.get("priceToBook", 0)
        ps_ratio = info.get("priceToSalesTrailing12Months", 0)
        peg_ratio = info.get("pegRatio", 0)
        ev_ebitda = info.get("enterpriseToEbitda", 0)
        
        # ==========================================
        # Profitability Metrics
        # ==========================================
        roe = info.get("returnOnEquity", 0)
        roa = info.get("returnOnAssets", 0)
        profit_margin = info.get("profitMargins", 0)
        operating_margin = info.get("operatingMargins", 0)
        gross_margin = info.get("grossMargins", 0)
        
        # ==========================================
        # Financial Health
        # ==========================================
        debt_equity = info.get("debtToEquity", 0)
        current_ratio = info.get("currentRatio", 0)
        quick_ratio = info.get("quickRatio", 0)
        
        # ==========================================
        # Per Share Metrics
        # ==========================================
        eps = info.get("trailingEps", 0)
        forward_eps = info.get("forwardEps", 0)
        book_value = info.get("bookValue", 0)
        
        # ==========================================
        # Dividend Metrics
        # ==========================================
        dividend_yield = info.get("dividendYield", 0)
        dividend_rate = info.get("dividendRate", 0)
        payout_ratio = info.get("payoutRatio", 0)
        
        # ==========================================
        # Growth Metrics
        # ==========================================
        earnings_growth = info.get("earningsGrowth", 0)
        revenue_growth = info.get("revenueGrowth", 0)
        earnings_quarterly_growth = info.get("earningsQuarterlyGrowth", 0)
        
        # ==========================================
        # Market Data
        # ==========================================
        market_cap = info.get("marketCap", 0)
        enterprise_value = info.get("enterpriseValue", 0)
        revenue = info.get("totalRevenue", 0)
        ebitda = info.get("ebitda", 0)
        
        # ==========================================
        # Valuation Assessment
        # ==========================================
        valuation_signals = []
        score = 0
        max_score = 0
        
        # PE Ratio assessment
        if pe_ratio and pe_ratio > 0:
            max_score += 10
            if pe_ratio < FUNDAMENTAL_THRESHOLDS["pe_ratio_low"]:
                valuation_signals.append({"metric": "PE Ratio", "assessment": "Undervalued", "impact": "Positive"})
                score += 10
            elif pe_ratio > FUNDAMENTAL_THRESHOLDS["pe_ratio_high"]:
                valuation_signals.append({"metric": "PE Ratio", "assessment": "Overvalued", "impact": "Negative"})
            else:
                valuation_signals.append({"metric": "PE Ratio", "assessment": "Fair Valued", "impact": "Neutral"})
                score += 5
        
        # PB Ratio assessment
        if pb_ratio and pb_ratio > 0:
            max_score += 10
            if pb_ratio < FUNDAMENTAL_THRESHOLDS["pb_ratio_low"]:
                valuation_signals.append({"metric": "PB Ratio", "assessment": "Undervalued", "impact": "Positive"})
                score += 10
            elif pb_ratio > FUNDAMENTAL_THRESHOLDS["pb_ratio_high"]:
                valuation_signals.append({"metric": "PB Ratio", "assessment": "Overvalued", "impact": "Negative"})
            else:
                score += 5
        
        # ROE assessment
        if roe and roe > 0:
            max_score += 10
            roe_pct = roe * 100
            if roe_pct >= FUNDAMENTAL_THRESHOLDS["roe_min"]:
                valuation_signals.append({"metric": "ROE", "assessment": "Strong", "impact": "Positive"})
                score += 10
            elif roe_pct >= 10:
                score += 5
        
        # Debt assessment
        if debt_equity and debt_equity > 0:
            max_score += 10
            if debt_equity / 100 <= FUNDAMENTAL_THRESHOLDS["debt_equity_max"]:
                valuation_signals.append({"metric": "Debt/Equity", "assessment": "Healthy", "impact": "Positive"})
                score += 10
            else:
                valuation_signals.append({"metric": "Debt/Equity", "assessment": "High Debt", "impact": "Negative"})
        
        # Earnings Growth assessment
        if earnings_growth and earnings_growth > 0:
            max_score += 10
            eg_pct = earnings_growth * 100
            if eg_pct >= FUNDAMENTAL_THRESHOLDS["earnings_growth_min"]:
                valuation_signals.append({"metric": "Earnings Growth", "assessment": "Strong Growth", "impact": "Positive"})
                score += 10
            elif eg_pct > 0:
                score += 5
        
        # Overall rating
        if max_score > 0:
            rating_pct = (score / max_score) * 100
            if rating_pct >= 70:
                overall_rating = "STRONG BUY"
            elif rating_pct >= 55:
                overall_rating = "BUY"
            elif rating_pct >= 40:
                overall_rating = "HOLD"
            elif rating_pct >= 25:
                overall_rating = "SELL"
            else:
                overall_rating = "STRONG SELL"
        else:
            overall_rating = "INSUFFICIENT DATA"
            rating_pct = 0
        
        # Format values for display
        def format_value(val, is_percent=False, is_currency=False):
            if val is None or val == 0:
                return "N/A"
            if is_percent:
                return f"{val * 100:.2f}%"
            if is_currency:
                if val >= 10_000_000_000:
                    return f"₹{val / 10_000_000:.0f} Cr"
                elif val >= 10_000_000:
                    return f"₹{val / 10_000_000:.2f} Cr"
                else:
                    return f"₹{val:,.0f}"
            return round(val, 2) if isinstance(val, float) else val
        
        result = {
            "symbol": symbol.upper(),
            "company_name": info.get("longName", "N/A"),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "analysis_date": datetime.now().isoformat(),
            
            "valuation": {
                "pe_ratio": format_value(pe_ratio),
                "forward_pe": format_value(forward_pe),
                "pb_ratio": format_value(pb_ratio),
                "ps_ratio": format_value(ps_ratio),
                "peg_ratio": format_value(peg_ratio),
                "ev_ebitda": format_value(ev_ebitda),
            },
            
            "profitability": {
                "roe": format_value(roe, is_percent=True),
                "roa": format_value(roa, is_percent=True),
                "profit_margin": format_value(profit_margin, is_percent=True),
                "operating_margin": format_value(operating_margin, is_percent=True),
                "gross_margin": format_value(gross_margin, is_percent=True),
            },
            
            "financial_health": {
                "debt_to_equity": format_value(debt_equity),
                "current_ratio": format_value(current_ratio),
                "quick_ratio": format_value(quick_ratio),
                "debt_status": "Low" if debt_equity and debt_equity < 50 else ("Moderate" if debt_equity and debt_equity <= 150 else ("High" if debt_equity else "N/A")),
            },
            
            "per_share": {
                "eps": format_value(eps),
                "forward_eps": format_value(forward_eps),
                "book_value": format_value(book_value),
            },
            
            "dividends": {
                "dividend_yield": format_value(dividend_yield, is_percent=True),
                "dividend_rate": format_value(dividend_rate),
                "payout_ratio": format_value(payout_ratio, is_percent=True),
            },
            
            "growth": {
                "earnings_growth": format_value(earnings_growth, is_percent=True),
                "revenue_growth": format_value(revenue_growth, is_percent=True),
                "quarterly_earnings_growth": format_value(earnings_quarterly_growth, is_percent=True),
            },
            
            "size": {
                "market_cap": format_value(market_cap, is_currency=True),
                "enterprise_value": format_value(enterprise_value, is_currency=True),
                "revenue": format_value(revenue, is_currency=True),
                "ebitda": format_value(ebitda, is_currency=True),
            },
            
            "assessment": valuation_signals,
            "overall_rating": overall_rating,
            "score": f"{score}/{max_score}",
            "rating_percentage": f"{rating_pct:.0f}%",
        }
        
        return _safe_json_dumps(result, indent=2)
    
    except Exception as e:
        return json.dumps({
            "error": str(e),
            "symbol": symbol,
            "DATA_UNAVAILABLE": True,
            "message": f"FAILED to get fundamental metrics for {symbol}. Do NOT guess financial ratios.",
        })


@tool("Analyze Price Action")
def analyze_price_action(symbol: str) -> str:
    """
    Analyze recent price action patterns and identify key price levels.
    
    Args:
        symbol: Stock symbol (e.g., 'RELIANCE', 'TCS')
        
    Returns:
        JSON string with price action analysis including patterns and levels.
    """
    try:
        ticker = yf.Ticker(_get_nse_symbol(symbol))
        df = ticker.history(period="3mo")
        
        if df.empty:
            return json.dumps({
                "error": f"No data for {symbol}",
                "DATA_UNAVAILABLE": True,
                "message": f"No price data returned for {symbol}. Do NOT guess price levels.",
            })
        
        close = df['Close']
        high = df['High']
        low = df['Low']
        
        current_price = close.iloc[-1]
        
        # Calculate price levels
        all_time_high = high.max()
        period_low = low.min()
        
        # Recent trend
        price_5d_ago = close.iloc[-6] if len(close) > 5 else close.iloc[0]
        price_20d_ago = close.iloc[-21] if len(close) > 20 else close.iloc[0]
        
        change_5d = ((current_price - price_5d_ago) / price_5d_ago) * 100
        change_20d = ((current_price - price_20d_ago) / price_20d_ago) * 100
        
        # Identify swing highs and lows (simplified)
        swing_highs = []
        swing_lows = []
        
        for i in range(2, len(df) - 2):
            if high.iloc[i] > high.iloc[i-1] and high.iloc[i] > high.iloc[i-2] and \
               high.iloc[i] > high.iloc[i+1] and high.iloc[i] > high.iloc[i+2]:
                swing_highs.append(round(high.iloc[i], 2))
            
            if low.iloc[i] < low.iloc[i-1] and low.iloc[i] < low.iloc[i-2] and \
               low.iloc[i] < low.iloc[i+1] and low.iloc[i] < low.iloc[i+2]:
                swing_lows.append(round(low.iloc[i], 2))
        
        # Distance from key levels
        distance_from_high = ((all_time_high - current_price) / current_price) * 100
        distance_from_low = ((current_price - period_low) / period_low) * 100
        
        # Trend strength
        if change_5d > 0 and change_20d > 0:
            trend = "Strong Uptrend"
        elif change_5d < 0 and change_20d < 0:
            trend = "Strong Downtrend"
        elif change_5d > 0 and change_20d < 0:
            trend = "Recovering"
        else:
            trend = "Weakening"
        
        result = {
            "symbol": symbol.upper(),
            "current_price": round(current_price, 2),
            
            "price_changes": {
                "5_day_change": f"{change_5d:.2f}%",
                "20_day_change": f"{change_20d:.2f}%",
                "trend": trend,
            },
            
            "key_levels": {
                "period_high": round(all_time_high, 2),
                "period_low": round(period_low, 2),
                "distance_from_high": f"{distance_from_high:.2f}%",
                "distance_from_low": f"{distance_from_low:.2f}%",
            },
            
            "swing_points": {
                "recent_swing_highs": swing_highs[-3:] if swing_highs else [],
                "recent_swing_lows": swing_lows[-3:] if swing_lows else [],
            },
            
            "analysis_date": datetime.now().isoformat(),
        }
        
        return _safe_json_dumps(result, indent=2)

    except Exception as e:
        return json.dumps({
            "error": str(e),
            "symbol": symbol,
            "DATA_UNAVAILABLE": True,
            "message": f"FAILED to analyze price action for {symbol}. Do NOT guess price levels.",
        })
