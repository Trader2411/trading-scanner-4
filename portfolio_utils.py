from __future__ import annotations

from typing import Dict, Optional, List
import pandas as pd

from config import PORTFOLIO_FILE
from data_fetcher import get_historical_data, get_live_price_payload
from indicators import atr


PORTFOLIO_COLUMNS = [
    "symbol",
    "buy_date",
    "buy_price",
    "shares",
    "initial_stop_loss",
    "current_stop_loss",
    "target_price",
    "strategy_tag",
]


def _to_float(value) -> Optional[float]:
    try:
        if value is None or pd.isna(value):
            return None
        return float(value)
    except Exception:
        return None


def _safe_close_series(hist: pd.DataFrame) -> pd.Series:
    if hist is None or hist.empty or "Close" not in hist.columns:
        return pd.Series(dtype=float)

    close = hist["Close"]
    if isinstance(close, pd.DataFrame):
        if close.empty:
            return pd.Series(dtype=float)
        close = close.iloc[:, 0]

    return pd.to_numeric(close, errors="coerce").dropna()


def _safe_low_series(hist: pd.DataFrame) -> pd.Series:
    if hist is None or hist.empty or "Low" not in hist.columns:
        return pd.Series(dtype=float)

    low = hist["Low"]
    if isinstance(low, pd.DataFrame):
        if low.empty:
            return pd.Series(dtype=float)
        low = low.iloc[:, 0]

    return pd.to_numeric(low, errors="coerce").dropna()


def load_portfolio() -> pd.DataFrame:
    if not PORTFOLIO_FILE.exists():
        return pd.DataFrame(columns=PORTFOLIO_COLUMNS)

    try:
        df = pd.read_csv(PORTFOLIO_FILE)
    except Exception:
        return pd.DataFrame(columns=PORTFOLIO_COLUMNS)

    for col in PORTFOLIO_COLUMNS:
        if col not in df.columns:
            df[col] = None

    return df[PORTFOLIO_COLUMNS].copy()


def save_portfolio(df: pd.DataFrame) -> None:
    result = df.copy()

    for col in PORTFOLIO_COLUMNS:
        if col not in result.columns:
            result[col] = None

    result[PORTFOLIO_COLUMNS].to_csv(PORTFOLIO_FILE, index=False)


def update_trailing_stop(position: Dict, hist: pd.DataFrame) -> Optional[float]:
    if hist is None or hist.empty:
        return _to_float(position.get("current_stop_loss"))

    close = _safe_close_series(hist)
    low = _safe_low_series(hist)

    if close.empty:
        return _to_float(position.get("current_stop_loss"))

    sma50 = None
    if len(close) >= 50:
        sma50_val = close.rolling(50).mean().iloc[-1]
        sma50 = _to_float(sma50_val)

    atr14 = None
    try:
        atr_series = atr(hist, 14)
        if atr_series is not None and len(atr_series.dropna()) > 0:
            atr14 = _to_float(atr_series.dropna().iloc[-1])
    except Exception:
        atr14 = None

    recent_low = None
    if not low.empty:
        recent_low = _to_float(low.tail(20).min())

    current_stop = _to_float(position.get("current_stop_loss"))
    initial_stop = _to_float(position.get("initial_stop_loss"))
    last_close = _to_float(close.iloc[-1])

    candidates: List[float] = []

    for x in [current_stop, initial_stop]:
        if x is not None:
            candidates.append(x)

    if sma50 is not None:
        candidates.append(sma50)

    if recent_low is not None:
        candidates.append(recent_low * 0.995)

    if atr14 is not None and last_close is not None:
        atr_stop = last_close - 2.0 * atr14
        if atr_stop > 0:
            candidates.append(atr_stop)

    if not candidates:
        return None

    # Stop nur anheben
    return round(max(candidates), 2)


def evaluate_sell_signals(
    position: Dict,
    hist: Optional[pd.DataFrame] = None,
    live_payload: Optional[Dict] = None,
) -> Dict:
    symbol = position.get("symbol")

    if hist is None:
        hist = get_historical_data(symbol, period="1y", interval="1d")

    if live_payload is None:
        live_payload = get_live_price_payload(symbol)

    market_price = _to_float(live_payload.get("market_price"))

    result = {
        "symbol": symbol,
        "market_price": round(market_price, 2) if market_price is not None else None,
        "market_price_source": live_payload.get("market_price_source"),
        "stop_loss_hit": False,
        "target_hit": False,
        "trend_break": False,
        "below_sma50": False,
        "below_sma200": False,
        "sell_signal": False,
        "sell_reason": "",
        "updated_stop_loss": _to_float(position.get("current_stop_loss")),
    }

    if hist is None or hist.empty or market_price is None:
        result["sell_reason"] = "Keine aktuellen Daten"
        return result

    close = _safe_close_series(hist)
    if close.empty:
        result["sell_reason"] = "Keine aktuellen Daten"
        return result

    sma50 = None
    sma200 = None

    if len(close) >= 50:
        sma50 = _to_float(close.rolling(50).mean().iloc[-1])

    if len(close) >= 200:
        sma200 = _to_float(close.rolling(200).mean().iloc[-1])

    target_price = _to_float(position.get("target_price"))
    updated_stop = update_trailing_stop(position, hist)
    result["updated_stop_loss"] = updated_stop

    reasons: List[str] = []

    if updated_stop is not None and market_price <= updated_stop:
        result["stop_loss_hit"] = True
        reasons.append("Stop-Loss ausgelöst")

    if target_price is not None and market_price >= target_price:
        result["target_hit"] = True
        reasons.append("Zielpreis erreicht")

    if sma50 is not None and market_price < sma50:
        result["below_sma50"] = True
        reasons.append("Unter SMA50")

    if sma200 is not None and market_price < sma200:
        result["below_sma200"] = True
        reasons.append("Unter SMA200")

    if result["below_sma50"] and result["below_sma200"]:
        result["trend_break"] = True

    result["sell_signal"] = bool(
        result["stop_loss_hit"]
        or result["target_hit"]
        or result["trend_break"]
    )
    result["sell_reason"] = ", ".join(reasons)

    return result


def analyze_portfolio() -> pd.DataFrame:
    portfolio = load_portfolio()
    if portfolio.empty:
        return pd.DataFrame()

    rows = []

    for _, position in portfolio.iterrows():
        pos = position.to_dict()
        symbol = pos.get("symbol")

        hist = get_historical_data(symbol, period="1y", interval="1d")
        live_payload = get_live_price_payload(symbol)

        evaluation = evaluate_sell_signals(
            pos,
            hist=hist,
            live_payload=live_payload,
        )

        buy_price = _to_float(pos.get("buy_price"))
        shares = _to_float(pos.get("shares"))
        market_price = _to_float(evaluation.get("market_price"))

        pnl_abs = None
        pnl_pct = None
        position_value = None

        if buy_price is not None and market_price is not None:
            pnl_abs = market_price - buy_price
            if buy_price != 0:
                pnl_pct = ((market_price / buy_price) - 1.0) * 100.0

        if shares is not None and market_price is not None:
            position_value = shares * market_price

        rows.append(
            {
                **pos,
                **evaluation,
                "pnl_abs": round(pnl_abs, 2) if pnl_abs is not None else None,
                "pnl_pct": round(pnl_pct, 2) if pnl_pct is not None else None,
                "position_value": round(position_value, 2) if position_value is not None else None,
            }
        )

    result = pd.DataFrame(rows)

    preferred_cols = [
        "symbol",
        "buy_date",
        "buy_price",
        "shares",
        "market_price",
        "pnl_abs",
        "pnl_pct",
        "position_value",
        "initial_stop_loss",
        "current_stop_loss",
        "updated_stop_loss",
        "target_price",
        "sell_signal",
        "sell_reason",
        "market_price_source",
        "strategy_tag",
    ]

    existing = [c for c in preferred_cols if c in result.columns]
    rest = [c for c in result.columns if c not in existing]

    return result[existing + rest]