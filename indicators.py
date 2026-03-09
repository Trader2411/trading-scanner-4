from __future__ import annotations

from typing import Dict, Optional

import pandas as pd

try:
    from config import (
        DEFAULT_STOP_LOSS_PCT,
        MOMENTUM_LOOKBACK,
        RECENT_LOW_LOOKBACK,
        RELATIVE_STRENGTH_LOOKBACK,
        SMA_FAST,
        SMA_SLOW,
        SWING_LOW_LOOKBACK,
    )
except Exception:
    DEFAULT_STOP_LOSS_PCT = 0.08
    MOMENTUM_LOOKBACK = 21
    RECENT_LOW_LOOKBACK = 20
    RELATIVE_STRENGTH_LOOKBACK = 90
    SMA_FAST = 50
    SMA_SLOW = 200
    SWING_LOW_LOOKBACK = 20


# ============================================================
# Basis-Helfer
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


def _last(series: pd.Series) -> Optional[float]:
    if series is None or series.empty:
        return None
    try:
        value = series.iloc[-1]
        if pd.isna(value):
            return None
        return float(value)
    except Exception:
        return None


def _clamp(value: float, lower: float = 0.0, upper: float = 100.0) -> float:
    return max(lower, min(upper, float(value)))


# ============================================================
# Gleitende Durchschnitte
# ============================================================

def calc_sma(close: pd.Series, window: int) -> Optional[float]:
    if close is None or len(close) < window:
        return None

    value = close.rolling(window).mean().iloc[-1]
    if pd.isna(value):
        return None

    return float(value)


def calc_ema(close: pd.Series, window: int) -> Optional[float]:
    if close is None or len(close) < window:
        return None

    value = close.ewm(span=window, adjust=False).mean().iloc[-1]
    if pd.isna(value):
        return None

    return float(value)


# ============================================================
# Momentum / Relative Strength
# ============================================================

def calc_momentum_pct(close: pd.Series, lookback: int = MOMENTUM_LOOKBACK) -> Optional[float]:
    """
    Prozentuale Kursveränderung über den Lookback.
    """
    if close is None or len(close) <= lookback:
        return None

    start = close.iloc[-lookback - 1]
    end = close.iloc[-1]

    if pd.isna(start) or pd.isna(end) or start == 0:
        return None

    return float(((end / start) - 1.0) * 100.0)


def calc_relative_strength(
    close: pd.Series,
    benchmark_close: Optional[pd.Series],
    lookback: int = RELATIVE_STRENGTH_LOOKBACK,
) -> Optional[float]:
    """
    Relative Strength gegen einen Benchmark.

    Ausgabe als 0-100 Skala:
    - 50 = neutral
    - >50 = besser als Benchmark
    - <50 = schlechter als Benchmark
    """
    if close is None or close.empty or benchmark_close is None or benchmark_close.empty:
        return None

    stock = pd.to_numeric(close, errors="coerce").dropna()
    benchmark = pd.to_numeric(benchmark_close, errors="coerce").dropna()

    combined = pd.concat(
        [stock.rename("stock"), benchmark.rename("benchmark")],
        axis=1,
        join="inner",
    ).dropna()

    if len(combined) <= lookback:
        return None

    stock_start = combined["stock"].iloc[-lookback - 1]
    stock_end = combined["stock"].iloc[-1]
    bench_start = combined["benchmark"].iloc[-lookback - 1]
    bench_end = combined["benchmark"].iloc[-1]

    if min(stock_start, stock_end, bench_start, bench_end) <= 0:
        return None

    stock_return = (stock_end / stock_start) - 1.0
    bench_return = (bench_end / bench_start) - 1.0
    relative_diff = stock_return - bench_return

    # Relative Differenz in eine intuitive 0-100 Skala transformieren
    # -20 % Unterperformance -> ca. 0
    # +20 % Outperformance   -> ca. 100
    scaled = 50.0 + (relative_diff * 250.0)
    return float(_clamp(scaled, 0.0, 100.0))


# ============================================================
# Trend / Marktstruktur
# ============================================================

def calc_golden_cross(sma_fast: Optional[float], sma_slow: Optional[float]) -> bool:
    if sma_fast is None or sma_slow is None:
        return False
    return float(sma_fast) > float(sma_slow)


def calc_distance_to_52w_high_pct(close: pd.Series, lookback: int = 252) -> Optional[float]:
    if close is None or close.empty:
        return None

    tail = close.tail(lookback)
    if tail.empty:
        return None

    high_52w = tail.max()
    current = tail.iloc[-1]

    if pd.isna(high_52w) or pd.isna(current) or high_52w == 0:
        return None

    return float(((current / high_52w) - 1.0) * 100.0)


def calc_trend_strength(
    current_price: Optional[float],
    sma_fast: Optional[float],
    sma_slow: Optional[float],
    ema_fast: Optional[float] = None,
) -> Optional[float]:
    """
    Trendstärke als 0-100 Wert.

    Bewertet:
    - Kurs über SMA50
    - Kurs über SMA200
    - SMA50 über SMA200
    - optional EMA-Unterstützung
    """
    if current_price is None:
        return None

    score = 0.0
    parts = 0

    if sma_fast is not None:
        parts += 1
        if current_price > sma_fast:
            score += 1.0

    if sma_slow is not None:
        parts += 1
        if current_price > sma_slow:
            score += 1.0

    if sma_fast is not None and sma_slow is not None:
        parts += 1
        if sma_fast > sma_slow:
            score += 1.0

    if ema_fast is not None:
        parts += 1
        if current_price > ema_fast:
            score += 1.0

    if parts == 0:
        return None

    return float((score / parts) * 100.0)


# ============================================================
# Swing / Stops / Ziele
# ============================================================

def find_last_swing_low(low: pd.Series, lookback: int = SWING_LOW_LOOKBACK) -> Optional[float]:
    if low is None or low.empty:
        return None

    tail = low.tail(lookback)
    if tail.empty:
        return None

    value = tail.min()
    if pd.isna(value):
        return None

    return float(value)


def calc_recent_low(low: pd.Series, lookback: int = RECENT_LOW_LOOKBACK) -> Optional[float]:
    if low is None or low.empty:
        return None

    tail = low.tail(lookback)
    if tail.empty:
        return None

    value = tail.min()
    if pd.isna(value):
        return None

    return float(value)


def calc_stop_loss(
    analysis_price: Optional[float],
    sma_fast: Optional[float],
    swing_low: Optional[float],
    stop_loss_pct: float = DEFAULT_STOP_LOSS_PCT,
) -> Optional[float]:
    """
    Scanner-Stop-Loss:
    max(
        8 % unter Analysepreis,
        SMA50,
        letztes Swing Low
    )
    """
    candidates = []

    if analysis_price is not None and analysis_price > 0:
        candidates.append(analysis_price * (1.0 - float(stop_loss_pct)))

    if sma_fast is not None and sma_fast > 0:
        candidates.append(sma_fast)

    if swing_low is not None and swing_low > 0:
        candidates.append(swing_low)

    if not candidates:
        return None

    return float(max(candidates))


def calc_target_price(
    analysis_price: Optional[float],
    stop_loss: Optional[float],
    reward_risk_ratio: float = 2.0,
) -> Optional[float]:
    """
    Einfaches Kursziel auf Basis Chance/Risiko.
    """
    if analysis_price is None or stop_loss is None:
        return None

    risk = analysis_price - stop_loss
    if risk <= 0:
        return None

    return float(analysis_price + (risk * reward_risk_ratio))


# ============================================================
# Zusatzkennzahlen
# ============================================================

def calc_atr(df: pd.DataFrame, window: int = 14) -> Optional[float]:
    if df is None or df.empty:
        return None

    high = _safe_series(df, "High")
    low = _safe_series(df, "Low")
    close = _safe_series(df, "Close")

    if high.empty or low.empty or close.empty:
        return None

    aligned = pd.concat(
        [high.rename("High"), low.rename("Low"), close.rename("Close")],
        axis=1,
        join="inner",
    ).dropna()

    if len(aligned) < window + 1:
        return None

    prev_close = aligned["Close"].shift(1)

    tr = pd.concat(
        [
            aligned["High"] - aligned["Low"],
            (aligned["High"] - prev_close).abs(),
            (aligned["Low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    atr = tr.rolling(window).mean().iloc[-1]
    if pd.isna(atr):
        return None

    return float(atr)


# ============================================================
# Hauptfunktion für Scanner
# ============================================================

def calculate_indicators(
    hist: pd.DataFrame,
    benchmark_close: Optional[pd.Series] = None,
) -> Dict:
    """
    Hauptfunktion für den Scanner.

    Erwartete Rückgabe u.a.:
    - analysis_price
    - sma50
    - sma200
    - golden_cross
    - momentum
    - relative_strength
    - trend_strength
    - distance_to_52w_high_pct
    - target_price
    - stop_loss
    """
    if hist is None or hist.empty:
        return {}

    close = _safe_series(hist, "Close")
    low = _safe_series(hist, "Low")
    volume = _safe_series(hist, "Volume")

    if close.empty:
        return {}

    analysis_price = _last(close)
    sma50 = calc_sma(close, SMA_FAST)
    sma200 = calc_sma(close, SMA_SLOW)
    ema21 = calc_ema(close, 21)

    golden_cross = calc_golden_cross(sma50, sma200)
    momentum = calc_momentum_pct(close, MOMENTUM_LOOKBACK)
    relative_strength = calc_relative_strength(
        close=close,
        benchmark_close=benchmark_close,
        lookback=RELATIVE_STRENGTH_LOOKBACK,
    )
    distance_to_52w_high_pct = calc_distance_to_52w_high_pct(close, 252)
    trend_strength = calc_trend_strength(
        current_price=analysis_price,
        sma_fast=sma50,
        sma_slow=sma200,
        ema_fast=ema21,
    )

    swing_low = find_last_swing_low(low, SWING_LOW_LOOKBACK)
    recent_low = calc_recent_low(low, RECENT_LOW_LOOKBACK)
    stop_loss = calc_stop_loss(
        analysis_price=analysis_price,
        sma_fast=sma50,
        swing_low=swing_low,
        stop_loss_pct=DEFAULT_STOP_LOSS_PCT,
    )
    target_price = calc_target_price(
        analysis_price=analysis_price,
        stop_loss=stop_loss,
        reward_risk_ratio=2.0,
    )

    atr14 = calc_atr(hist, 14)

    relative_volume = None
    if not volume.empty and len(volume) >= 20:
        avg_vol_20 = volume.tail(20).mean()
        current_vol = volume.iloc[-1]
        if pd.notna(avg_vol_20) and avg_vol_20 not in [0, None] and pd.notna(current_vol):
            relative_volume = float(current_vol / avg_vol_20)

    volume_score = None
    if relative_volume is not None:
        # 1.0 = neutral (~50), 2.0 = stark (~100)
        volume_score = float(_clamp(relative_volume * 50.0, 0.0, 100.0))

    result = {
        "analysis_price": _round_or_none(analysis_price),
        "sma50": _round_or_none(sma50),
        "sma200": _round_or_none(sma200),
        "ema21": _round_or_none(ema21),
        "golden_cross": bool(golden_cross),
        "momentum": _round_or_none(momentum),
        "relative_strength": _round_or_none(relative_strength),
        "trend_strength": _round_or_none(trend_strength),
        "distance_to_52w_high_pct": _round_or_none(distance_to_52w_high_pct),
        "swing_low": _round_or_none(swing_low),
        "recent_low": _round_or_none(recent_low),
        "stop_loss": _round_or_none(stop_loss),
        "target_price": _round_or_none(target_price),
        "atr14": _round_or_none(atr14),
        "relative_volume": _round_or_none(relative_volume),
        "volume_score": _round_or_none(volume_score),
    }

    return result