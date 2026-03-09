from __future__ import annotations

from typing import Dict, List
import pandas as pd

from data_fetcher import get_historical_data


def _safe_last_scalar(value):
    """
    Wandelt pandas Series / DataFrame / numpy scalar robust in einen float um.
    Gibt None zurück, wenn kein sauberer Wert extrahiert werden kann.
    """
    try:
        if value is None:
            return None

        if isinstance(value, pd.DataFrame):
            if value.empty:
                return None
            value = value.iloc[-1, 0]

        elif isinstance(value, pd.Series):
            if value.empty:
                return None
            value = value.iloc[-1]

        if pd.isna(value):
            return None

        return float(value)
    except Exception:
        return None


def analyze_market_regime(
    benchmark_symbol: str = "^GSPC",
    period: str = "1y",
    interval: str = "1d",
) -> Dict:
    df = get_historical_data(benchmark_symbol, period=period, interval=interval)

    if df is None or df.empty or "Close" not in df.columns:
        return {
            "benchmark": benchmark_symbol,
            "market_regime": "Neutral",
            "status": "no_data",
            "analysis_price": None,
            "sma50": None,
            "sma200": None,
        }

    close = df["Close"]

    if isinstance(close, pd.DataFrame):
        if close.empty:
            return {
                "benchmark": benchmark_symbol,
                "market_regime": "Neutral",
                "status": "no_data",
                "analysis_price": None,
                "sma50": None,
                "sma200": None,
            }
        close = close.iloc[:, 0]

    close = close.dropna()

    if close.empty:
        return {
            "benchmark": benchmark_symbol,
            "market_regime": "Neutral",
            "status": "no_data",
            "analysis_price": None,
            "sma50": None,
            "sma200": None,
        }

    price = _safe_last_scalar(close)
    sma50 = _safe_last_scalar(close.rolling(50).mean())
    sma200 = _safe_last_scalar(close.rolling(200).mean())

    if price is None or sma50 is None or sma200 is None:
        regime = "Neutral"
    elif price > sma50 > sma200:
        regime = "Bullish"
    elif price < sma50 < sma200:
        regime = "Bearish"
    else:
        regime = "Neutral"

    return {
        "benchmark": benchmark_symbol,
        "analysis_price": round(price, 2) if price is not None else None,
        "sma50": round(sma50, 2) if sma50 is not None else None,
        "sma200": round(sma200, 2) if sma200 is not None else None,
        "market_regime": regime,
        "status": "ok",
    }


def analyze_universe_market_breadth(
    symbols: List[str],
    period: str = "6mo",
    interval: str = "1d",
) -> Dict:
    if not symbols:
        return {
            "count": 0,
            "pct_above_sma50": 0.0,
            "pct_golden_cross": 0.0,
        }

    total = 0
    above_sma50 = 0
    golden_cross = 0

    for symbol in symbols:
        df = get_historical_data(symbol, period=period, interval=interval)

        if df is None or df.empty or "Close" not in df.columns:
            continue

        close = df["Close"]

        if isinstance(close, pd.DataFrame):
            if close.empty:
                continue
            close = close.iloc[:, 0]

        close = close.dropna()

        if close.empty:
            continue

        price = _safe_last_scalar(close)
        sma50 = _safe_last_scalar(close.rolling(50).mean())
        sma200 = _safe_last_scalar(close.rolling(200).mean())

        if price is None:
            continue

        total += 1

        if sma50 is not None and price > sma50:
            above_sma50 += 1

        if sma50 is not None and sma200 is not None and sma50 > sma200:
            golden_cross += 1

    if total == 0:
        return {
            "count": 0,
            "pct_above_sma50": 0.0,
            "pct_golden_cross": 0.0,
        }

    return {
        "count": total,
        "pct_above_sma50": round((above_sma50 / total) * 100.0, 2),
        "pct_golden_cross": round((golden_cross / total) * 100.0, 2),
    }


def derive_risk_level(breadth: Dict) -> str:
    pct = breadth.get("pct_above_sma50", 0)

    if pct >= 70:
        return "Niedrig"
    if pct >= 45:
        return "Mittel"
    return "Hoch"


def derive_action_signal(regime: str, breadth: Dict) -> str:
    pct = breadth.get("pct_above_sma50", 0)

    if regime == "Bullish" and pct >= 60:
        return "Longs bevorzugen"
    if regime == "Bearish":
        return "Defensiv bleiben"
    return "Gewinne sichern"