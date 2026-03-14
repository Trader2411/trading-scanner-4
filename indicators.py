from __future__ import annotations

from typing import Dict, Optional, Tuple

import numpy as np
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
# Helfer
# ============================================================

def _safe_series(df: pd.DataFrame, column: str) -> pd.Series:
    if df is None or df.empty or column not in df.columns:
        return pd.Series(dtype=float)

    s = df[column]

    if isinstance(s, pd.DataFrame):
        s = s.iloc[:, 0]

    return pd.to_numeric(s, errors="coerce").dropna()


def _last(series: pd.Series) -> Optional[float]:
    if series is None or series.empty:
        return None
    value = series.iloc[-1]
    if pd.isna(value):
        return None
    return float(value)


def _round_or_none(value, digits=2):
    if value is None:
        return None
    try:
        return round(float(value), digits)
    except Exception:
        return None


def _clamp(v, lo=0, hi=100):
    return max(lo, min(hi, float(v)))


# ============================================================
# Moving Averages
# ============================================================

def calc_sma(close: pd.Series, window: int):

    if close is None or len(close) < window:
        return None

    return float(close.rolling(window).mean().iloc[-1])


def calc_ema(close: pd.Series, window: int):

    if close is None or len(close) < window:
        return None

    return float(close.ewm(span=window, adjust=False).mean().iloc[-1])


# ============================================================
# Momentum
# ============================================================

def calc_momentum_pct(close: pd.Series, lookback=MOMENTUM_LOOKBACK):

    if close is None or len(close) <= lookback:
        return None

    start = close.iloc[-lookback - 1]
    end = close.iloc[-1]

    if start == 0 or pd.isna(start) or pd.isna(end):
        return None

    return float(((end / start) - 1) * 100)


# ============================================================
# Relative Strength
# ============================================================

def calc_relative_strength(close, benchmark_close, lookback=RELATIVE_STRENGTH_LOOKBACK):

    if close is None or benchmark_close is None:
        return None

    df = pd.concat(
        [close.rename("s"), benchmark_close.rename("b")],
        axis=1,
        join="inner",
    ).dropna()

    if len(df) <= lookback:
        return None

    s1 = df["s"].iloc[-lookback]
    s2 = df["s"].iloc[-1]

    b1 = df["b"].iloc[-lookback]
    b2 = df["b"].iloc[-1]

    if min(s1, s2, b1, b2) <= 0:
        return None

    stock_return = (s2 / s1) - 1
    bench_return = (b2 / b1) - 1

    diff = stock_return - bench_return

    return _clamp(50 + diff * 250)


# ============================================================
# RSI
# ============================================================

def calc_rsi(close, window=14):

    if close is None or len(close) < window + 1:
        return None

    delta = close.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(window).mean()
    avg_loss = loss.rolling(window).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)

    rsi = 100 - (100 / (1 + rs))

    return float(rsi.iloc[-1])


def calc_rsi_signal(rsi):

    if rsi is None:
        return None

    if rsi < 30:
        return "Oversold"

    if rsi > 70:
        return "Overbought"

    if 45 <= rsi <= 60:
        return "Bullish Zone"

    return "Neutral"


# ============================================================
# MACD
# ============================================================

def calc_macd(close):

    if close is None or len(close) < 35:
        return {
            "macd_line": None,
            "macd_signal": None,
            "macd_hist": None,
            "macd_trend": None,
        }

    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()

    macd = ema12 - ema26

    signal = macd.ewm(span=9, adjust=False).mean()

    hist = macd - signal

    macd_value = macd.iloc[-1]
    signal_value = signal.iloc[-1]
    hist_value = hist.iloc[-1]

    trend = None

    if macd_value > signal_value:
        trend = "Bullish"
    else:
        trend = "Bearish"

    return {
        "macd_line": float(macd_value),
        "macd_signal": float(signal_value),
        "macd_hist": float(hist_value),
        "macd_trend": trend,
    }


# ============================================================
# Bollinger
# ============================================================

def calc_bollinger_bands(close, window=20):

    if close is None or len(close) < window:
        return {}

    mean = close.rolling(window).mean()

    std = close.rolling(window).std()

    mid = mean.iloc[-1]
    upper = mid + 2 * std.iloc[-1]
    lower = mid - 2 * std.iloc[-1]

    current = close.iloc[-1]

    width = (upper - lower) / mid * 100

    position = (current - lower) / (upper - lower) * 100

    return {
        "bb_middle": mid,
        "bb_upper": upper,
        "bb_lower": lower,
        "bb_width_pct": width,
        "bb_position_pct": position,
    }


# ============================================================
# Trend Channel
# ============================================================

def calc_trend_channel(close, window=20):

    if close is None or len(close) < window:
        return {}

    high = close.rolling(window).max()
    low = close.rolling(window).min()

    upper = high.iloc[-1]
    lower = low.iloc[-1]

    mid = (upper + lower) / 2

    current = close.iloc[-1]

    position = (current - lower) / (upper - lower) * 100

    signal = "Mid Channel"

    if position > 80:
        signal = "Upper Breakout Zone"

    if position < 20:
        signal = "Lower Support Zone"

    return {
        "trend_channel_upper": upper,
        "trend_channel_lower": lower,
        "trend_channel_mid": mid,
        "trend_channel_position_pct": position,
        "trend_channel_signal": signal,
    }


# ============================================================
# Stops
# ============================================================

def find_last_swing_low(low, lookback=SWING_LOW_LOOKBACK):

    if low is None or low.empty:
        return None

    return float(low.tail(lookback).min())


def calc_recent_low(low, lookback=RECENT_LOW_LOOKBACK):

    if low is None or low.empty:
        return None

    return float(low.tail(lookback).min())


# ============================================================
# Hauptfunktion
# ============================================================

def calculate_indicators(hist, benchmark_close=None):

    if hist is None or hist.empty:
        return {}

    close = _safe_series(hist, "Close")
    high = _safe_series(hist, "High")
    low = _safe_series(hist, "Low")
    volume = _safe_series(hist, "Volume")

    if close.empty:
        return {}

    analysis_price = _last(close)

    sma50 = calc_sma(close, SMA_FAST)
    sma200 = calc_sma(close, SMA_SLOW)
    ema21 = calc_ema(close, 21)

    momentum = calc_momentum_pct(close)

    rs = calc_relative_strength(close, benchmark_close)

    rsi = calc_rsi(close)
    rsi_signal = calc_rsi_signal(rsi)

    macd = calc_macd(close)

    bb = calc_bollinger_bands(close)

    trend = calc_trend_channel(close)

    swing_low = find_last_swing_low(low)

    stop_loss = None
    if analysis_price and swing_low:
        stop_loss = max(
            analysis_price * (1 - DEFAULT_STOP_LOSS_PCT),
            swing_low,
        )

    result = {
        "analysis_price": analysis_price,
        "sma50": sma50,
        "sma200": sma200,
        "ema21": ema21,
        "momentum": momentum,
        "relative_strength": rs,
        "rsi": rsi,
        "rsi_signal": rsi_signal,
        "stop_loss": stop_loss,
    }

    result.update(macd)
    result.update(bb)
    result.update(trend)

    return result