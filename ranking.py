from __future__ import annotations

from typing import Dict, Optional

try:
    from config import (
        WEIGHT_MOMENTUM,
        WEIGHT_TREND,
    )
except Exception:
    WEIGHT_MOMENTUM = 0.30
    WEIGHT_TREND = 0.35

# Neue Config bevorzugen, alte Namen weiterhin unterstützen
try:
    from config import WEIGHT_RELATIVE_STRENGTH
except Exception:
    try:
        from config import WEIGHT_RS as WEIGHT_RELATIVE_STRENGTH
    except Exception:
        WEIGHT_RELATIVE_STRENGTH = 0.20

try:
    from config import WEIGHT_VOLUME
except Exception:
    WEIGHT_VOLUME = 0.15

try:
    from config import DEFAULT_MIN_TRADE_SCORE
except Exception:
    DEFAULT_MIN_TRADE_SCORE = 60


# ============================================================
# Interne Hilfsfunktionen
# ============================================================

def _safe_float(value) -> Optional[float]:
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def _clamp(value: float, min_value: float = 0.0, max_value: float = 100.0) -> float:
    return max(min_value, min(max_value, float(value)))


# ============================================================
# Einzelscorings
# ============================================================

def _score_momentum(value) -> float:
    """
    Momentum wird auf 0 bis 100 normalisiert.

    Leitplanken:
    - <= -10 %   -> 0
    - >= +25 %   -> 100
    """
    val = _safe_float(value)
    if val is None:
        return 0.0

    if val <= -10:
        return 0.0
    if val >= 25:
        return 100.0

    scaled = ((val + 10.0) / 35.0) * 100.0
    return round(_clamp(scaled), 2)


def _score_relative_strength(value) -> float:
    """
    Relative Strength wird bereits typischerweise als 0-100 Wert geliefert.
    """
    val = _safe_float(value)
    if val is None:
        return 0.0
    return round(_clamp(val), 2)


def _score_trend_strength(value) -> float:
    """
    Trendstärke kommt aus indicators.py bereits als 0-100 ähnliche Kennzahl.
    """
    val = _safe_float(value)
    if val is None:
        return 0.0
    return round(_clamp(val), 2)


def _score_golden_cross(value: bool) -> float:
    return 100.0 if bool(value) else 0.0


def _score_distance_to_high(value) -> float:
    """
    Je näher am 52W Hoch, desto besser.

    - >= 0 %    -> 100
    - <= -30 %  -> 0
    """
    val = _safe_float(value)
    if val is None:
        return 0.0

    if val >= 0:
        return 100.0
    if val <= -30:
        return 0.0

    scaled = ((val + 30.0) / 30.0) * 100.0
    return round(_clamp(scaled), 2)


def _score_volume_quality(row: Dict) -> float:
    """
    Aktuell einfache robuste Platzhalterlogik:
    - wenn kein Volumenfaktor vorhanden ist, neutral mit 50
    - wenn relative_volume existiert, darauf skalieren
    - wenn volume_score existiert, direkt nutzen

    So bleibt das Projekt kompatibel und später erweiterbar.
    """
    direct_score = _safe_float(row.get("volume_score"))
    if direct_score is not None:
        return round(_clamp(direct_score), 2)

    rel_vol = _safe_float(row.get("relative_volume"))
    if rel_vol is not None:
        # 1.0 = neutral, 2.0+ = stark
        scaled = rel_vol * 50.0
        return round(_clamp(scaled), 2)

    return 50.0


# ============================================================
# Gesamtscore
# ============================================================

def calculate_trade_score_components(row: Dict) -> Dict:
    """
    Liefert die einzelnen Score-Bausteine getrennt zurück.
    """
    momentum_score = _score_momentum(row.get("momentum"))
    rs_score = _score_relative_strength(row.get("relative_strength"))
    trend_score = _score_trend_strength(row.get("trend_strength"))

    # Golden Cross und Distanz zum Hoch fließen in den Trendblock ein,
    # damit die neue Config ohne zusätzliche Gewichte sauber funktioniert.
    golden_cross_score = _score_golden_cross(row.get("golden_cross", False))
    high_score = _score_distance_to_high(row.get("distance_to_52w_high_pct"))
    trend_block = (trend_score * 0.50) + (golden_cross_score * 0.25) + (high_score * 0.25)

    volume_score = _score_volume_quality(row)

    return {
        "score_momentum": round(momentum_score, 2),
        "score_relative_strength": round(rs_score, 2),
        "score_trend": round(trend_block, 2),
        "score_volume": round(volume_score, 2),
        "score_golden_cross": round(golden_cross_score, 2),
        "score_distance_to_high": round(high_score, 2),
    }


def calculate_trade_score(row: Dict) -> float:
    components = calculate_trade_score_components(row)

    total = (
        components["score_momentum"] * WEIGHT_MOMENTUM
        + components["score_relative_strength"] * WEIGHT_RELATIVE_STRENGTH
        + components["score_trend"] * WEIGHT_TREND
        + components["score_volume"] * WEIGHT_VOLUME
    )

    return round(_clamp(total), 2)


# ============================================================
# Signal-Logik
# ============================================================

def classify_signal(
    trade_score: float,
    momentum: Optional[float] = None,
    golden_cross: bool = False,
) -> str:
    """
    Klare und für die UI gut lesbare Signaltexte.
    """
    score = _safe_float(trade_score)
    if score is None:
        return "Keine Bewertung"

    mom = _safe_float(momentum)

    if score >= 85:
        if golden_cross:
            return "Starkes Kaufsignal"
        return "Neues Kaufsignal"

    if score >= 70:
        if mom is not None and mom > 0:
            return "Kaufsignal"
        return "Beobachten"

    if score >= 55:
        return "Beobachten"

    if score >= 40:
        return "Neutral"

    return "Meiden"


def derive_rating_bucket(trade_score: float) -> str:
    score = _safe_float(trade_score)
    if score is None:
        return "Keine Daten"

    if score >= 85:
        return "A"
    if score >= 75:
        return "B"
    if score >= 60:
        return "C"
    if score >= 45:
        return "D"
    return "E"


def is_top_candidate(trade_score: float, threshold: float = DEFAULT_MIN_TRADE_SCORE) -> bool:
    score = _safe_float(trade_score)
    if score is None:
        return False
    return score >= float(threshold)


# ============================================================
# Komfortfunktion für Scanner-Zeilen
# ============================================================

def add_trade_score(row: Dict) -> Dict:
    """
    Ergänzt eine Scanner-Zeile um:
    - Trade Score
    - Signal
    - Rating Bucket
    - Einzelscores
    """
    result = dict(row)

    components = calculate_trade_score_components(result)
    trade_score = calculate_trade_score(result)
    signal = classify_signal(
        trade_score=trade_score,
        momentum=result.get("momentum"),
        golden_cross=bool(result.get("golden_cross", False)),
    )
    rating_bucket = derive_rating_bucket(trade_score)

    result.update(components)
    result["trade_score"] = trade_score
    result["signal"] = signal
    result["rating_bucket"] = rating_bucket
    result["is_top_candidate"] = is_top_candidate(trade_score)

    return result