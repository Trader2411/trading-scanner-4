# ranking.py

from __future__ import annotations

from typing import Dict

from config import (
    WEIGHT_MOMENTUM,
    WEIGHT_RS,
    WEIGHT_GOLDEN_CROSS,
    WEIGHT_TREND,
    WEIGHT_DISTANCE_TO_HIGH,
)


def _score_momentum(value):
    if value is None:
        return 0.0
    if value >= 25:
        return 100.0
    if value <= -10:
        return 0.0
    return max(0.0, min(100.0, (value + 10) / 35 * 100))


def _score_rs(value):
    if value is None:
        return 0.0
    return max(0.0, min(100.0, float(value)))


def _score_golden_cross(value: bool):
    return 100.0 if value else 0.0


def _score_trend(value):
    if value is None:
        return 0.0
    return max(0.0, min(100.0, float(value)))


def _score_distance_to_high(value):
    if value is None:
        return 0.0
    if value >= 0:
        return 100.0
    if value <= -30:
        return 0.0
    return max(0.0, min(100.0, (value + 30) / 30 * 100))


def calculate_trade_score(row: Dict) -> float:
    momentum_score = _score_momentum(row.get("momentum"))
    rs_score = _score_rs(row.get("relative_strength"))
    gc_score = _score_golden_cross(row.get("golden_cross", False))
    trend_score = _score_trend(row.get("trend_strength"))
    high_score = _score_distance_to_high(row.get("distance_to_52w_high_pct"))

    total = (
        momentum_score * WEIGHT_MOMENTUM
        + rs_score * WEIGHT_RS
        + gc_score * WEIGHT_GOLDEN_CROSS
        + trend_score * WEIGHT_TREND
        + high_score * WEIGHT_DISTANCE_TO_HIGH
    )

    return round(total, 2)


def classify_signal(trade_score: float) -> str:
    if trade_score >= 80:
        return "Neues Kaufsignal"
    if trade_score >= 65:
        return "Beobachten"
    if trade_score >= 50:
        return "Neutral"
    return "Meiden"


def add_trade_score(row: Dict) -> Dict:
    row = dict(row)
    row["trade_score"] = calculate_trade_score(row)
    row["signal"] = classify_signal(row["trade_score"])
    return row