# indicators.py

from __future__ import annotations

from typing import Dict, Optional
import numpy as np
import pandas as pd

from config import DEFAULT_STOP_LOSS_PCT, DEFAULT_TARGET_PCT, ATR_STOP_MULTIPLIER


def sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window).mean()


def atr(df: pd.DataFrame, window: int = 14) -> pd.Series:
    high = df["High"]
    low = df["Low"]
    close = df["Close"]

    prev_close = close.shift(1)
    tr = pd.concat(
        [
            (high - low),
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    return tr.rolling(window).mean()


def calc_momentum(close: pd.Series, lookback: int = 63) -> Optional[float]:
    if len(close) <= lookback:
        return None
    start = close.iloc[-lookback - 1]
    end = close.iloc[-1]
    if start == 0 or pd.isna(start) or pd.isna(end):
        return None
    return float(((end / start) - 1.0) * 100.0)


def calc_relative_strength(close: pd.Series, benchmark_close: Optional[pd.Series] = None) -> Optional[float]:
    mom = calc_momentum(close, 63)
    if mom is None:
        return None

    if benchmark_close is not None and len(benchmark_close.dropna()) >= 64:
        bench_mom = calc_momentum(benchmark_close.dropna(), 63)
        if bench_mom is not None:
            rs = 50 + (mom - bench_mom) * 2
            return float(max(0, min(100, rs)))

    rs = 50 + mom * 2
    return float(max(0, min(100, rs)))


def calc_golden_cross(close: pd.Series) -> bool:
    sma50 = close.rolling(50).mean()
    sma200 = close.rolling(200).mean()

    if len(close) < 200 or pd.isna(sma50.iloc[-1]) or pd.isna(sma200.iloc[-1]):
        return False

    return bool(sma50.iloc[-1] > sma200.iloc[-1])


def calc_trend_strength(close: pd.Series) -> Optional[float]:
    if len(close) < 200:
        return None

    sma20 = close.rolling(20).mean().iloc[-1]
    sma50 = close.rolling(50).mean().iloc[-1]
    sma200 = close.rolling(200).mean().iloc[-1]
    price = close.iloc[-1]

    if any(pd.isna(x) for x in [sma20, sma50, sma200]):
        return None

    score = 0.0
    if price > sma20:
        score += 33.3
    if sma20 > sma50:
        score += 33.3
    if sma50 > sma200:
        score += 33.4
    return round(score, 2)


def calc_distance_to_52w_high(close: pd.Series, window: int = 252) -> Optional[float]:
    if len(close) < min(60, window):
        return None
    high_52 = close.tail(window).max()
    current = close.iloc[-1]
    if high_52 == 0 or pd.isna(high_52) or pd.isna(current):
        return None
    return float(((current / high_52) - 1.0) * 100.0)


def calc_target_price(analysis_price: float, momentum: Optional[float], atr_value: Optional[float]) -> Optional[float]:
    if analysis_price is None:
        return None

    if atr_value is not None and not pd.isna(atr_value):
        return round(analysis_price + (atr_value * 3.0), 2)

    if momentum is not None and momentum > 10:
        return round(analysis_price * 1.18, 2)

    return round(analysis_price * (1.0 + DEFAULT_TARGET_PCT), 2)


def calc_stop_loss(analysis_price: float, atr_value: Optional[float], recent_low: Optional[float]) -> Optional[float]:
    if analysis_price is None:
        return None

    candidates = [round(analysis_price * (1.0 - DEFAULT_STOP_LOSS_PCT), 2)]

    if atr_value is not None and not pd.isna(atr_value):
        candidates.append(round(analysis_price - (ATR_STOP_MULTIPLIER * atr_value), 2))

    if recent_low is not None and not pd.isna(recent_low):
        candidates.append(round(recent_low * 0.995, 2))

    candidates = [c for c in candidates if c > 0]
    if not candidates:
        return None

    return round(max(candidates), 2)


def calculate_indicators(df: pd.DataFrame, benchmark_close: Optional[pd.Series] = None) -> Dict:
    if df is None or df.empty:
        return {}

    close = df["Close"].dropna()
    low = df["Low"].dropna()

    if close.empty:
        return {}

    analysis_price = float(close.iloc[-1])
    sma20_last = sma(close, 20).iloc[-1] if len(close) >= 20 else np.nan
    sma50_last = sma(close, 50).iloc[-1] if len(close) >= 50 else np.nan
    sma200_last = sma(close, 200).iloc[-1] if len(close) >= 200 else np.nan

    atr_series = atr(df, 14)
    atr_last = atr_series.iloc[-1] if len(atr_series.dropna()) > 0 else np.nan

    momentum = calc_momentum(close, 63)
    rs = calc_relative_strength(close, benchmark_close)
    golden_cross = calc_golden_cross(close)
    trend_strength = calc_trend_strength(close)
    distance_to_high = calc_distance_to_52w_high(close)

    recent_low = low.tail(20).min() if len(low) >= 20 else low.min()
    target_price = calc_target_price(analysis_price, momentum, atr_last)
    stop_loss = calc_stop_loss(analysis_price, atr_last, recent_low)

    return {
        "analysis_price": round(analysis_price, 2),
        "sma20": round(float(sma20_last), 2) if pd.notna(sma20_last) else None,
        "sma50": round(float(sma50_last), 2) if pd.notna(sma50_last) else None,
        "sma200": round(float(sma200_last), 2) if pd.notna(sma200_last) else None,
        "atr14": round(float(atr_last), 2) if pd.notna(atr_last) else None,
        "momentum": round(momentum, 2) if momentum is not None else None,
        "relative_strength": round(rs, 2) if rs is not None else None,
        "golden_cross": golden_cross,
        "trend_strength": round(trend_strength, 2) if trend_strength is not None else None,
        "distance_to_52w_high_pct": round(distance_to_high, 2) if distance_to_high is not None else None,
        "target_price": target_price,
        "stop_loss": stop_loss,
    }