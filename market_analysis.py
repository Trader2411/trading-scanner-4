from __future__ import annotations

from typing import Dict, Optional

import pandas as pd

from config import (
    BREADTH_BEARISH_THRESHOLD,
    BREADTH_BULLISH_THRESHOLD,
    DEFAULT_HISTORY_INTERVAL,
    DEFAULT_HISTORY_PERIOD,
    MARKET_INDEX,
)
from data_fetcher import get_historical_data, get_live_price_payload


# ============================================================
# Interne Hilfsfunktionen
# ============================================================

def _safe_series(df: pd.DataFrame, column: str) -> pd.Series:
    if df is None or df.empty or column not in df.columns:
        return pd.Series(dtype=float)

    series = df[column]

    if isinstance(series, pd.DataFrame):
        if series.empty:
            return pd.Series(dtype=float)
        series = series.iloc[:, 0]

    return pd.to_numeric(series, errors="coerce").dropna()


def _safe_float(value) -> Optional[float]:
    try:
        if value is None or pd.isna(value):
            return None
        return float(value)
    except Exception:
        return None


def _round_or_none(value: Optional[float], digits: int = 2) -> Optional[float]:
    if value is None:
        return None
    try:
        return round(float(value), digits)
    except Exception:
        return None


def _calc_sma(close: pd.Series, window: int) -> Optional[float]:
    if close is None or len(close) < window:
        return None

    value = close.rolling(window).mean().iloc[-1]
    if pd.isna(value):
        return None

    return float(value)


def _calc_momentum(close: pd.Series, lookback: int = 21) -> Optional[float]:
    if close is None or len(close) <= lookback:
        return None

    start = close.iloc[-lookback - 1]
    end = close.iloc[-1]

    if pd.isna(start) or pd.isna(end) or start == 0:
        return None

    return float(((end / start) - 1.0) * 100.0)


# ============================================================
# Marktanalyse
# ============================================================

def analyze_market_regime(
    benchmark_symbol: str = MARKET_INDEX,
    period: str = DEFAULT_HISTORY_PERIOD,
    interval: str = DEFAULT_HISTORY_INTERVAL,
) -> Dict:
    """
    Analysiert den allgemeinen Marktstatus auf Basis eines Referenzindex.
    Rückgabe ist bewusst kompakt und app-freundlich.
    """
    hist = get_historical_data(
        symbol=benchmark_symbol,
        period=period,
        interval=interval,
    )

    if hist is None or hist.empty:
        return {
            "benchmark_symbol": benchmark_symbol,
            "market_regime": "Neutral",
            "market_signal": "Keine Daten",
            "market_price": None,
            "analysis_price": None,
            "sma50": None,
            "sma200": None,
            "momentum": None,
            "trend_ok": False,
            "data_status": "no_data",
        }

    close = _safe_series(hist, "Close")
    if close.empty:
        return {
            "benchmark_symbol": benchmark_symbol,
            "market_regime": "Neutral",
            "market_signal": "Keine Daten",
            "market_price": None,
            "analysis_price": None,
            "sma50": None,
            "sma200": None,
            "momentum": None,
            "trend_ok": False,
            "data_status": "no_close_data",
        }

    analysis_price = _safe_float(close.iloc[-1])
    sma50 = _calc_sma(close, 50)
    sma200 = _calc_sma(close, 200)
    momentum = _calc_momentum(close, 21)

    live = get_live_price_payload(benchmark_symbol)
    market_price = _safe_float(live.get("market_price"))
    market_price_source = live.get("market_price_source")

    price_for_regime = market_price if market_price is not None else analysis_price

    above_sma50 = (
        price_for_regime is not None and sma50 is not None and price_for_regime > sma50
    )
    above_sma200 = (
        price_for_regime is not None and sma200 is not None and price_for_regime > sma200
    )
    sma50_above_sma200 = (
        sma50 is not None and sma200 is not None and sma50 > sma200
    )
    momentum_positive = (
        momentum is not None and momentum > 0
    )

    bullish_count = sum(
        [
            1 if above_sma50 else 0,
            1 if above_sma200 else 0,
            1 if sma50_above_sma200 else 0,
            1 if momentum_positive else 0,
        ]
    )

    if bullish_count >= 3:
        market_regime = "Bullish"
        market_signal = "Trendmarkt intakt"
    elif bullish_count <= 1:
        market_regime = "Bearish"
        market_signal = "Defensiv bleiben"
    else:
        market_regime = "Neutral"
        market_signal = "Selektiv vorgehen"

    return {
        "benchmark_symbol": benchmark_symbol,
        "market_regime": market_regime,
        "market_signal": market_signal,
        "market_price": _round_or_none(market_price),
        "analysis_price": _round_or_none(analysis_price),
        "market_price_source": market_price_source,
        "sma50": _round_or_none(sma50),
        "sma200": _round_or_none(sma200),
        "momentum": _round_or_none(momentum),
        "trend_ok": bool(above_sma50 and sma50_above_sma200),
        "data_status": "ok",
    }


# ============================================================
# Marktbreite / Risiko
# ============================================================

def derive_risk_level(breadth: Dict) -> str:
    """
    Leitet eine einfache Risikostufe aus Marktbreiten-Daten ab.
    Erwartet z. B.:
    {
        "pct_above_sma50": 63.5,
        "pct_golden_cross": 41.0,
        ...
    }
    """
    pct_above_sma50 = _safe_float(breadth.get("pct_above_sma50"))
    pct_golden_cross = _safe_float(breadth.get("pct_golden_cross"))

    if pct_above_sma50 is None:
        return "Unbekannt"

    if pct_above_sma50 >= BREADTH_BULLISH_THRESHOLD and (pct_golden_cross or 0) >= 35:
        return "Niedrig"

    if pct_above_sma50 <= BREADTH_BEARISH_THRESHOLD:
        return "Hoch"

    return "Mittel"


def derive_action_signal(
    market_status: str,
    breadth: Dict,
) -> str:
    """
    Liefert ein kompaktes Aktivsignal für die App-Kachel.
    """
    pct_above_sma50 = _safe_float(breadth.get("pct_above_sma50"))
    pct_golden_cross = _safe_float(breadth.get("pct_golden_cross"))

    if market_status == "Bullish":
        if pct_above_sma50 is not None and pct_above_sma50 >= BREADTH_BULLISH_THRESHOLD:
            return "Offensiv"
        return "Selektiv Long"

    if market_status == "Bearish":
        return "Defensiv"

    if pct_golden_cross is not None and pct_golden_cross >= 35:
        return "Chancen prüfen"

    return "Abwarten"


# ============================================================
# Zusatzfunktion für spätere Erweiterungen
# ============================================================

def summarize_market_view(
    breadth: Dict,
    benchmark_symbol: str = MARKET_INDEX,
) -> Dict:
    """
    Kombiniert Marktregime und Risiko in einer Gesamtübersicht.
    """
    regime = analyze_market_regime(benchmark_symbol=benchmark_symbol)
    risk = derive_risk_level(breadth)
    action = derive_action_signal(regime.get("market_regime", "Neutral"), breadth)

    return {
        **regime,
        "risk_level": risk,
        "action_signal": action,
    }