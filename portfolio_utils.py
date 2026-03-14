from __future__ import annotations

from typing import Dict, List, Optional

import pandas as pd

from config import (
    DEFAULT_STOP_LOSS_PCT,
    MOMENTUM_LOOKBACK,
    RECENT_LOW_LOOKBACK,
    SWING_LOW_LOOKBACK,
    TRAILING_STOP_PCT,
)
from data_fetcher import get_historical_data
from market_analysis import analyze_market_regime
from portfolio_store import load_portfolio

# Nur Funktionen importieren, die sicher in indicators.py vorhanden sind
from indicators import (
    calc_sma,
    calc_momentum_pct,
    find_last_swing_low,
    calc_recent_low,
    calc_rsi,
    calc_macd,
)


# ============================================================
# Interne Hilfsfunktionen
# ============================================================

def _normalize_symbol(symbol) -> Optional[str]:
    if symbol is None:
        return None
    text = str(symbol).strip().upper()
    return text if text else None


def _to_float(value) -> Optional[float]:
    try:
        if value is None or value == "" or pd.isna(value):
            return None
        return float(value)
    except Exception:
        return None


def _round_or_none(value, digits: int = 2) -> Optional[float]:
    try:
        if value is None or pd.isna(value):
            return None
        return round(float(value), digits)
    except Exception:
        return None


def _safe_series(df: pd.DataFrame, column: str) -> pd.Series:
    if df is None or df.empty or column not in df.columns:
        return pd.Series(dtype=float)

    series = df[column]

    if isinstance(series, pd.DataFrame):
        if series.empty:
            return pd.Series(dtype=float)
        series = series.iloc[:, 0]

    return pd.to_numeric(series, errors="coerce").dropna()


def _get_market_price_from_history(symbol: str, hist: Optional[pd.DataFrame] = None) -> Dict:
    if hist is None or hist.empty:
        hist = get_historical_data(symbol, period="1y", interval="1d")

    close = _safe_series(hist, "Close")
    if close.empty:
        return {
            "market_price": None,
            "market_price_source": "history",
        }

    return {
        "market_price": float(close.iloc[-1]),
        "market_price_source": "history",
    }


def calc_recent_20d_low(low: pd.Series) -> Optional[float]:
    return calc_recent_low(low, RECENT_LOW_LOOKBACK)


def calc_volatility_pct(close: pd.Series, window: int = 20) -> Optional[float]:
    if close is None or close.empty or len(close) < window:
        return None

    series = pd.to_numeric(close, errors="coerce").dropna()
    if len(series) < window:
        return None

    returns = series.pct_change().dropna()
    if len(returns) < window:
        return None

    vol = returns.tail(window).std() * 100.0
    if pd.isna(vol):
        return None

    return float(vol)


# ============================================================
# Stop-Logik
# ============================================================

def calc_stop_loss(
    buy_price: Optional[float],
    sma50: Optional[float],
    swing_low: Optional[float],
    initial_stop_loss: Optional[float] = None,
    current_stop_loss: Optional[float] = None,
) -> Optional[float]:
    candidates: List[float] = []

    if buy_price is not None and buy_price > 0:
        candidates.append(buy_price * (1.0 - float(DEFAULT_STOP_LOSS_PCT)))

    if sma50 is not None and sma50 > 0:
        candidates.append(sma50)

    if swing_low is not None and swing_low > 0:
        candidates.append(swing_low)

    if initial_stop_loss is not None and initial_stop_loss > 0:
        candidates.append(initial_stop_loss)

    if current_stop_loss is not None and current_stop_loss > 0:
        candidates.append(current_stop_loss)

    if not candidates:
        return None

    return float(max(candidates))


def calc_trailing_stop(
    stop_loss: Optional[float],
    current_price: Optional[float],
    recent_20d_low: Optional[float],
    current_stop_loss: Optional[float] = None,
) -> Optional[float]:
    candidates: List[float] = []

    if stop_loss is not None and stop_loss > 0:
        candidates.append(stop_loss)

    if current_stop_loss is not None and current_stop_loss > 0:
        candidates.append(current_stop_loss)

    if current_price is not None and current_price > 0:
        candidates.append(current_price * (1.0 - float(TRAILING_STOP_PCT)))

    if recent_20d_low is not None and recent_20d_low > 0:
        candidates.append(recent_20d_low)

    if not candidates:
        return None

    return float(max(candidates))


# ============================================================
# Signal-Logik
# ============================================================

def derive_exit_signal(
    current_price: Optional[float],
    buy_price: Optional[float],
    sma50: Optional[float],
    momentum_pct: Optional[float],
    market_regime: str,
    stop_loss: Optional[float],
    trailing_stop: Optional[float],
    rsi: Optional[float] = None,
    macd_trend: Optional[str] = None,
) -> Dict:
    reasons_red: List[str] = []
    reasons_yellow: List[str] = []

    below_sma50 = (
        current_price is not None and
        sma50 is not None and
        current_price < sma50
    )

    below_stop = (
        current_price is not None and
        stop_loss is not None and
        current_price < stop_loss
    )

    below_trailing = (
        current_price is not None and
        trailing_stop is not None and
        current_price < trailing_stop
    )

    momentum_negative = momentum_pct is not None and momentum_pct < 0
    market_bearish = str(market_regime).strip().lower() == "bearish"
    rsi_overheated = rsi is not None and rsi >= 75
    macd_bearish = str(macd_trend or "").strip().lower() in {"bearish", "weakening"}

    if below_stop:
        reasons_red.append("Kurs unter Stop-Loss")
    if below_trailing:
        reasons_red.append("Kurs unter Trailing-Stop")
    if below_sma50:
        reasons_red.append("Kurs unter SMA50")
    if momentum_negative:
        reasons_red.append("Momentum negativ")
    if market_bearish:
        reasons_red.append("Marktstatus bearish")
    if rsi_overheated:
        reasons_red.append("RSI überhitzt")
    if macd_bearish:
        reasons_red.append("MACD bearish")

    if reasons_red:
        return {
            "exit_signal": "Verkaufen",
            "signal_color": "Rot",
            "signal_reason": ", ".join(reasons_red),
        }

    if trailing_stop is not None and stop_loss is not None and trailing_stop > stop_loss:
        reasons_yellow.append("Stop kann nachgezogen werden")

    if buy_price is not None and current_price is not None and current_price > buy_price:
        reasons_yellow.append("Position im Gewinn")

    if momentum_pct is not None and 0 <= momentum_pct < 3:
        reasons_yellow.append("Momentum flacht ab")

    if str(market_regime).strip().lower() == "neutral":
        reasons_yellow.append("Marktstatus neutral")

    if reasons_yellow:
        return {
            "exit_signal": "Stop nachziehen",
            "signal_color": "Gelb",
            "signal_reason": ", ".join(reasons_yellow),
        }

    return {
        "exit_signal": "Halten",
        "signal_color": "Grün",
        "signal_reason": "Trend intakt, kein Verkaufssignal aktiv",
    }


# ============================================================
# Einzelne Positionsanalyse
# ============================================================

def analyze_position(position: Dict, market_regime: str) -> Dict:
    symbol = _normalize_symbol(position.get("symbol"))
    buy_price = _to_float(position.get("buy_price"))
    shares = _to_float(position.get("shares"))
    initial_stop_loss = _to_float(position.get("initial_stop_loss"))
    current_stop_loss = _to_float(position.get("current_stop_loss"))
    target_price = _to_float(position.get("target_price"))

    result = {
        **position,
        "symbol": symbol,
        "market_regime": market_regime,
        "market_price": None,
        "market_price_source": None,
        "invested_capital": None,
        "position_value": None,
        "pnl_abs_total": None,
        "pnl_pct": None,
        "sma50": None,
        "swing_low": None,
        "recent_20d_low": None,
        "momentum": None,
        "rsi": None,
        "macd_trend": None,
        "volatility_pct": None,
        "stop_loss": None,
        "trailing_stop": None,
        "stop_distance_pct": None,
        "exit_signal": "Keine Daten",
        "signal_color": "Grau",
        "signal_reason": "Keine ausreichenden Kursdaten verfügbar",
        "data_status": "no_data",
    }

    if symbol is None:
        result["signal_reason"] = "Symbol fehlt"
        return result

    hist = get_historical_data(symbol, period="1y", interval="1d")
    price_payload = _get_market_price_from_history(symbol, hist=hist)

    current_price = _to_float(price_payload.get("market_price"))
    result["market_price"] = _round_or_none(current_price)
    result["market_price_source"] = price_payload.get("market_price_source")

    if hist is None or hist.empty:
        result["signal_reason"] = "Keine Historie verfügbar"
        return result

    close = _safe_series(hist, "Close")
    low = _safe_series(hist, "Low")

    if close.empty:
        result["signal_reason"] = "Keine Schlusskurse verfügbar"
        return result

    sma50 = calc_sma(close, 50)
    swing_low = find_last_swing_low(low, SWING_LOW_LOOKBACK)
    recent_20d_low = calc_recent_20d_low(low)
    momentum_pct = calc_momentum_pct(close, MOMENTUM_LOOKBACK)
    rsi = calc_rsi(close, 14)

    macd_data = calc_macd(close)
    macd_trend = macd_data.get("macd_trend") if isinstance(macd_data, dict) else None

    volatility_pct = calc_volatility_pct(close, 20)

    stop_loss = calc_stop_loss(
        buy_price=buy_price,
        sma50=sma50,
        swing_low=swing_low,
        initial_stop_loss=initial_stop_loss,
        current_stop_loss=current_stop_loss,
    )

    trailing_stop = calc_trailing_stop(
        stop_loss=stop_loss,
        current_price=current_price,
        recent_20d_low=recent_20d_low,
        current_stop_loss=current_stop_loss,
    )

    signal = derive_exit_signal(
        current_price=current_price,
        buy_price=buy_price,
        sma50=sma50,
        momentum_pct=momentum_pct,
        market_regime=market_regime,
        stop_loss=stop_loss,
        trailing_stop=trailing_stop,
        rsi=rsi,
        macd_trend=macd_trend,
    )

    invested_capital = None
    position_value = None
    pnl_abs_total = None
    pnl_pct = None
    stop_distance_pct = None

    if buy_price is not None and shares is not None:
        invested_capital = buy_price * shares

    if current_price is not None and shares is not None:
        position_value = current_price * shares

    if invested_capital is not None and position_value is not None:
        pnl_abs_total = position_value - invested_capital

    if buy_price is not None and current_price is not None and buy_price != 0:
        pnl_pct = ((current_price / buy_price) - 1.0) * 100.0

    if current_price is not None and trailing_stop is not None and current_price != 0:
        stop_distance_pct = ((current_price - trailing_stop) / current_price) * 100.0

    result.update(
        {
            "invested_capital": _round_or_none(invested_capital),
            "position_value": _round_or_none(position_value),
            "pnl_abs_total": _round_or_none(pnl_abs_total),
            "pnl_pct": _round_or_none(pnl_pct),
            "sma50": _round_or_none(sma50),
            "swing_low": _round_or_none(swing_low),
            "recent_20d_low": _round_or_none(recent_20d_low),
            "momentum": _round_or_none(momentum_pct),
            "rsi": _round_or_none(rsi),
            "macd_trend": macd_trend,
            "volatility_pct": _round_or_none(volatility_pct),
            "stop_loss": _round_or_none(stop_loss),
            "trailing_stop": _round_or_none(trailing_stop),
            "stop_distance_pct": _round_or_none(stop_distance_pct),
            "exit_signal": signal.get("exit_signal"),
            "signal_color": signal.get("signal_color"),
            "signal_reason": signal.get("signal_reason"),
            "target_price": _round_or_none(target_price),
            "data_status": "ok",
        }
    )

    return result


# ============================================================
# Portfolio-Analyse
# ============================================================

def analyze_portfolio(user_key: Optional[str] = None) -> pd.DataFrame:
    portfolio = load_portfolio(user_key=user_key)

    if portfolio is None or portfolio.empty:
        return pd.DataFrame()

    market = analyze_market_regime()
    market_regime = str(market.get("market_regime", "Neutral"))

    rows: List[Dict] = []
    for _, row in portfolio.iterrows():
        rows.append(analyze_position(row.to_dict(), market_regime=market_regime))

    if not rows:
        return pd.DataFrame()

    result = pd.DataFrame(rows)

    signal_order = {"Rot": 0, "Gelb": 1, "Grün": 2, "Grau": 3}
    if "signal_color" in result.columns:
        result["_signal_order"] = result["signal_color"].map(signal_order).fillna(9)
        result = result.sort_values(
            by=["_signal_order", "pnl_pct", "symbol"],
            ascending=[True, True, True],
            na_position="last",
        ).drop(columns=["_signal_order"])

    return result.reset_index(drop=True)


def summarize_portfolio(portfolio_df: pd.DataFrame) -> Dict:
    if portfolio_df is None or portfolio_df.empty:
        return {
            "positions": 0,
            "portfolio_value": 0.0,
            "pnl_abs_total": 0.0,
            "red_signals": 0,
        }

    result = portfolio_df.copy()

    portfolio_value = pd.to_numeric(result.get("position_value"), errors="coerce").fillna(0).sum()
    pnl_abs_total = pd.to_numeric(result.get("pnl_abs_total"), errors="coerce").fillna(0).sum()
    red_signals = 0
    if "signal_color" in result.columns:
        red_signals = int((result["signal_color"].astype(str) == "Rot").sum())

    return {
        "positions": int(len(result)),
        "portfolio_value": round(float(portfolio_value), 2),
        "pnl_abs_total": round(float(pnl_abs_total), 2),
        "red_signals": red_signals,
    }