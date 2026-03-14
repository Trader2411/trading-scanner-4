from __future__ import annotations

from typing import Dict, Optional

import pandas as pd


# ============================================================
# Hilfsfunktionen
# ============================================================

def _safe_float(value) -> Optional[float]:

    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def _clamp(value: float, lo: float = 0, hi: float = 100) -> float:

    return max(lo, min(hi, float(value)))


def _normalize(value, low, high):

    v = _safe_float(value)

    if v is None:
        return None

    if high == low:
        return None

    scaled = (v - low) / (high - low) * 100

    return _clamp(scaled)


def _weighted_average(parts: Dict[str, tuple]):

    total_weight = 0
    weighted_sum = 0

    for key, (value, weight) in parts.items():

        if value is None:
            continue

        weighted_sum += value * weight
        total_weight += weight

    if total_weight == 0:
        return 0

    return round(weighted_sum / total_weight, 2)


# ============================================================
# Einzelbewertungen
# ============================================================

def score_momentum(momentum):

    return _normalize(momentum, -10, 30)


def score_relative_strength(rs):

    v = _safe_float(rs)

    if v is None:
        return None

    return _clamp(v)


def score_trend_strength(price, sma50, sma200):

    p = _safe_float(price)
    s50 = _safe_float(sma50)
    s200 = _safe_float(sma200)

    if p is None or s50 is None or s200 is None:
        return None

    score = 0

    if p > s50:
        score += 50

    if s50 > s200:
        score += 50

    return score


def score_rsi(rsi):

    v = _safe_float(rsi)

    if v is None:
        return None

    if v < 30:
        return 60

    if 40 <= v <= 60:
        return 100

    if 60 < v <= 70:
        return 70

    if v > 80:
        return 20

    return 50


def score_macd(macd_line, macd_signal):

    m = _safe_float(macd_line)
    s = _safe_float(macd_signal)

    if m is None or s is None:
        return None

    if m > s and m > 0:
        return 100

    if m > s:
        return 70

    if m < s and m < 0:
        return 20

    return 40


def score_volatility(volatility_pct):

    v = _safe_float(volatility_pct)

    if v is None:
        return None

    if v < 2:
        return 40

    if v < 4:
        return 80

    if v < 6:
        return 70

    if v < 8:
        return 50

    return 20


# ============================================================
# Hauptfunktion
# ============================================================

def calculate_trade_score(row: pd.Series):

    momentum_score = score_momentum(row.get("momentum"))

    rs_score = score_relative_strength(row.get("relative_strength"))

    trend_score = score_trend_strength(
        row.get("analysis_price"),
        row.get("sma50"),
        row.get("sma200"),
    )

    rsi_score = score_rsi(row.get("rsi"))

    macd_score = score_macd(
        row.get("macd_line"),
        row.get("macd_signal"),
    )

    vol_score = score_volatility(row.get("volatility_pct"))

    parts = {

        "momentum": (momentum_score, 0.25),

        "relative_strength": (rs_score, 0.20),

        "trend": (trend_score, 0.25),

        "rsi": (rsi_score, 0.10),

        "macd": (macd_score, 0.10),

        "volatility": (vol_score, 0.10),

    }

    return _weighted_average(parts)


# ============================================================
# DataFrame Funktion
# ============================================================

def add_trade_score(df: pd.DataFrame) -> pd.DataFrame:

    if df is None or df.empty:
        return df

    result = df.copy()

    scores = []

    for _, row in result.iterrows():

        score = calculate_trade_score(row)

        scores.append(score)

    result["trade_score"] = scores

    result["trade_score"] = result["trade_score"].fillna(0)

    return result