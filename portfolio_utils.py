from __future__ import annotations

from typing import Dict, List, Optional

import pandas as pd

from data_fetcher import get_historical_data, get_live_price_payload
from market_analysis import analyze_market_regime

try:
    from portfolio_store import load_portfolio
except Exception:
    # Fallback, falls portfolio_store.py noch nicht eingebunden ist
    from config import PORTFOLIO_FILE

    def load_portfolio(user_key: Optional[str] = None) -> pd.DataFrame:
        columns = [
            "position_id",
            "symbol",
            "buy_date",
            "buy_price",
            "shares",
            "initial_stop_loss",
            "current_stop_loss",
            "target_price",
            "strategy_tag",
            "note",
            "created_at",
            "updated_at",
        ]

        if not PORTFOLIO_FILE.exists():
            return pd.DataFrame(columns=columns)

        try:
            df = pd.read_csv(PORTFOLIO_FILE)
        except Exception:
            return pd.DataFrame(columns=columns)

        for col in columns:
            if col not in df.columns:
                df[col] = None

        return df[columns].copy()


# ============================================================
# Basis-Helfer
# ============================================================

def _to_float(value) -> Optional[float]:
    try:
        if value is None or pd.isna(value) or value == "":
            return None
        return float(value)
    except Exception:
        return None


def _safe_series(hist: pd.DataFrame, column: str) -> pd.Series:
    if hist is None or hist.empty or column not in hist.columns:
        return pd.Series(dtype=float)

    series = hist[column]

    if isinstance(series, pd.DataFrame):
        if series.empty:
            return pd.Series(dtype=float)
        series = series.iloc[:, 0]

    return pd.to_numeric(series, errors="coerce").dropna()


def _safe_last(series: pd.Series) -> Optional[float]:
    if series is None or len(series) == 0:
        return None

    try:
        value = series.iloc[-1]
        if pd.isna(value):
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


def _normalize_symbol(value) -> Optional[str]:
    if value is None or pd.isna(value):
        return None

    text = str(value).strip().upper()
    return text if text else None


# ============================================================
# Kurs- und Indikatorlogik
# ============================================================

def get_market_price(symbol: str, hist: Optional[pd.DataFrame] = None) -> Dict:
    """
    Liefert bevorzugt den Live-/Marktpreis.
    Fällt notfalls auf den letzten Schlusskurs der Historie zurück.
    """
    payload = get_live_price_payload(symbol)
    market_price = _to_float(payload.get("market_price"))
    source = payload.get("market_price_source")

    if market_price is not None and market_price > 0:
        return {
            "market_price": market_price,
            "market_price_source": source,
            "market_price_available": True,
        }

    if hist is None:
        hist = get_historical_data(symbol, period="1y", interval="1d")

    close = _safe_series(hist, "Close")
    fallback_price = _safe_last(close)

    return {
        "market_price": fallback_price,
        "market_price_source": "historical_close_fallback" if fallback_price is not None else None,
        "market_price_available": fallback_price is not None,
    }


def calc_sma(series: pd.Series, window: int) -> Optional[float]:
    if series is None or len(series) < window:
        return None

    sma_val = series.rolling(window).mean().iloc[-1]
    if pd.isna(sma_val):
        return None

    return float(sma_val)


def calc_momentum_pct(close: pd.Series, lookback: int = 21) -> Optional[float]:
    """
    Momentum als prozentuale Veränderung über den Lookback.
    Standard hier bewusst 21 Handelstage (~1 Monat),
    damit Verkaufssignale schneller reagieren.
    """
    if close is None or len(close) <= lookback:
        return None

    start = close.iloc[-lookback - 1]
    end = close.iloc[-1]

    if pd.isna(start) or pd.isna(end) or start == 0:
        return None

    return float(((end / start) - 1.0) * 100.0)


def find_last_swing_low(low: pd.Series, lookback: int = 20) -> Optional[float]:
    """
    Vereinfachte Swing-Low-Logik:
    nimmt das tiefste Tief der letzten n Tage.
    Für Version 1 robust und gut nachvollziehbar.
    """
    if low is None or low.empty:
        return None

    tail = low.tail(lookback)
    if tail.empty:
        return None

    value = tail.min()
    if pd.isna(value):
        return None

    return float(value)


def calc_recent_20d_low(low: pd.Series) -> Optional[float]:
    if low is None or low.empty:
        return None

    value = low.tail(20).min()
    if pd.isna(value):
        return None

    return float(value)


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
    """
    Gewünschte Kernlogik:
    Stop-Loss = max(
        8% unter Kaufkurs,
        SMA50,
        letztes Swing Low
    )

    Zusätzlich werden manuelle / bereits gespeicherte Stops berücksichtigt,
    damit ein einmal enger gesetzter Stop nicht wieder aufgeweicht wird.
    """
    candidates: List[float] = []

    if buy_price is not None and buy_price > 0:
        candidates.append(buy_price * 0.92)

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
    """
    Einfache, robuste Version für V1:
    Trailing-Stop = max(
        Stop-Loss,
        bisheriger aktueller Stop,
        10% unter aktuellem Kurs,
        letztes 20-Tage-Tief
    )
    """
    candidates: List[float] = []

    if stop_loss is not None and stop_loss > 0:
        candidates.append(stop_loss)

    if current_stop_loss is not None and current_stop_loss > 0:
        candidates.append(current_stop_loss)

    if current_price is not None and current_price > 0:
        candidates.append(current_price * 0.90)

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
) -> Dict:
    """
    Ampellogik:
    - Grün  = Halten
    - Gelb  = Stop nachziehen
    - Rot   = Verkaufen

    Rot wenn:
    - Kurs unter Trailing-Stop oder Stop-Loss
    - oder mehrere Warnsignale gleichzeitig aktiv
    """
    reasons_red: List[str] = []
    reasons_yellow: List[str] = []

    below_sma50 = (
        current_price is not None and sma50 is not None and current_price < sma50
    )
    momentum_negative = (
        momentum_pct is not None and momentum_pct < 0
    )
    market_bearish = market_regime == "Bearish"
    below_stop_loss = (
        current_price is not None and stop_loss is not None and current_price < stop_loss
    )
    below_trailing_stop = (
        current_price is not None
        and trailing_stop is not None
        and current_price < trailing_stop
    )

    in_profit = (
        current_price is not None
        and buy_price is not None
        and buy_price > 0
        and current_price > buy_price
    )

    if below_stop_loss:
        reasons_red.append("Kurs unter Stop-Loss")

    if below_trailing_stop:
        reasons_red.append("Kurs unter Trailing-Stop")

    if below_sma50:
        reasons_red.append("Kurs unter SMA50")

    if momentum_negative:
        reasons_red.append("Momentum negativ")

    if market_bearish:
        reasons_red.append("Marktstatus bearisch")

    hard_warning_count = 0
    hard_warning_count += 1 if below_sma50 else 0
    hard_warning_count += 1 if momentum_negative else 0
    hard_warning_count += 1 if market_bearish else 0

    if below_stop_loss or below_trailing_stop or hard_warning_count >= 2:
        reason_text = ", ".join(dict.fromkeys(reasons_red)) if reasons_red else "Verkaufssignal aktiv"
        return {
            "exit_signal": "Verkaufen",
            "signal_color": "Rot",
            "signal_reason": reason_text,
        }

    if in_profit:
        reasons_yellow.append("Position im Gewinn")

    if trailing_stop is not None and stop_loss is not None and trailing_stop > stop_loss:
        reasons_yellow.append("Stop kann nachgezogen werden")

    if momentum_pct is not None and 0 <= momentum_pct < 3:
        reasons_yellow.append("Momentum flacht ab")

    if market_regime == "Neutral":
        reasons_yellow.append("Marktstatus neutral")

    if reasons_yellow:
        reason_text = ", ".join(dict.fromkeys(reasons_yellow))
        return {
            "exit_signal": "Stop nachziehen",
            "signal_color": "Gelb",
            "signal_reason": reason_text,
        }

    return {
        "exit_signal": "Halten",
        "signal_color": "Grün",
        "signal_reason": "Trend intakt, kein Verkaufssignal aktiv",
    }


# ============================================================
# Positionsanalyse
# ============================================================

def analyze_position(
    position: Dict,
    market_regime: str,
) -> Dict:
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
    price_payload = get_market_price(symbol, hist=hist)

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
    swing_low = find_last_swing_low(low, 20)
    recent_20d_low = calc_recent_20d_low(low)
    momentum_pct = calc_momentum_pct(close, 21)

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
            "stop_loss": _round_or_none(stop_loss),
            "trailing_stop": _round_or_none(trailing_stop),
            "stop_distance_pct": _round_or_none(stop_distance_pct),
            "data_status": "ok",
            **signal,
        }
    )

    # Komfort-Feld: PnL je Aktie
    if buy_price is not None and current_price is not None:
        result["pnl_abs"] = _round_or_none(current_price - buy_price)
    else:
        result["pnl_abs"] = None

    # Zusatzlogik: Zielpreis nur informativ übernehmen
    result["target_price"] = _round_or_none(target_price)

    return result


# ============================================================
# Portfolio-Analyse
# ============================================================

def analyze_portfolio(user_key: Optional[str] = None) -> pd.DataFrame:
    """
    Hauptfunktion für die App.
    Lädt die Positionen und berechnet alle Verkaufs- und Absicherungshinweise.
    """
    portfolio = load_portfolio(user_key=user_key)

    if portfolio is None or portfolio.empty:
        return pd.DataFrame()

    market_info = analyze_market_regime()
    market_regime = market_info.get("market_regime", "Neutral")

    rows: List[Dict] = []

    for _, position in portfolio.iterrows():
        analyzed = analyze_position(
            position=position.to_dict(),
            market_regime=market_regime,
        )
        rows.append(analyzed)

    if not rows:
        return pd.DataFrame()

    result = pd.DataFrame(rows)

    preferred_cols = [
        "position_id",
        "symbol",
        "buy_date",
        "buy_price",
        "shares",
        "market_price",
        "invested_capital",
        "position_value",
        "pnl_abs_total",
        "pnl_pct",
        "sma50",
        "swing_low",
        "recent_20d_low",
        "stop_loss",
        "trailing_stop",
        "stop_distance_pct",
        "momentum",
        "market_regime",
        "exit_signal",
        "signal_color",
        "signal_reason",
        "initial_stop_loss",
        "current_stop_loss",
        "target_price",
        "strategy_tag",
        "note",
        "market_price_source",
        "data_status",
        "created_at",
        "updated_at",
    ]

    existing_cols = [col for col in preferred_cols if col in result.columns]
    remaining_cols = [col for col in result.columns if col not in existing_cols]

    result = result[existing_cols + remaining_cols].copy()

    # Sortierung: zuerst Verkaufssignale, dann Warnungen, dann Halten
    signal_order = {"Rot": 0, "Gelb": 1, "Grün": 2, "Grau": 3}
    result["_signal_order"] = result["signal_color"].map(signal_order).fillna(9)

    result["_buy_date_sort"] = pd.to_datetime(result["buy_date"], errors="coerce")
    result = result.sort_values(
        by=["_signal_order", "_buy_date_sort", "symbol"],
        ascending=[True, False, True],
        na_position="last",
    ).drop(columns=["_signal_order", "_buy_date_sort"])

    return result.reset_index(drop=True)


# ============================================================
# Zusatzfunktionen für Kennzahlen in der UI
# ============================================================

def summarize_portfolio(portfolio_df: pd.DataFrame) -> Dict:
    if portfolio_df is None or portfolio_df.empty:
        return {
            "positions": 0,
            "portfolio_value": 0.0,
            "invested_capital": 0.0,
            "pnl_abs_total": 0.0,
            "red_signals": 0,
            "yellow_signals": 0,
            "green_signals": 0,
        }

    value_sum = pd.to_numeric(portfolio_df.get("position_value"), errors="coerce").fillna(0).sum()
    invested_sum = pd.to_numeric(portfolio_df.get("invested_capital"), errors="coerce").fillna(0).sum()
    pnl_sum = pd.to_numeric(portfolio_df.get("pnl_abs_total"), errors="coerce").fillna(0).sum()

    signal_color = portfolio_df.get("signal_color", pd.Series(dtype=str)).fillna("")

    return {
        "positions": int(len(portfolio_df)),
        "portfolio_value": round(float(value_sum), 2),
        "invested_capital": round(float(invested_sum), 2),
        "pnl_abs_total": round(float(pnl_sum), 2),
        "red_signals": int((signal_color == "Rot").sum()),
        "yellow_signals": int((signal_color == "Gelb").sum()),
        "green_signals": int((signal_color == "Grün").sum()),
    }