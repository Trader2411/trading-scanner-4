from __future__ import annotations

from typing import Dict, Optional, List
import time

import pandas as pd
import streamlit as st
import yfinance as yf

from config import HIST_CACHE_TTL, LIVE_CACHE_TTL


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    result = df.copy()

    if isinstance(result.columns, pd.MultiIndex):
        result.columns = [col[0] if isinstance(col, tuple) else col for col in result.columns]

    rename_map = {}
    for col in result.columns:
        lc = str(col).lower()
        if lc == "adj close":
            rename_map[col] = "Adj Close"
        elif lc == "open":
            rename_map[col] = "Open"
        elif lc == "high":
            rename_map[col] = "High"
        elif lc == "low":
            rename_map[col] = "Low"
        elif lc == "close":
            rename_map[col] = "Close"
        elif lc == "volume":
            rename_map[col] = "Volume"

    result = result.rename(columns=rename_map)
    result = result.sort_index()
    return result


def _safe_float(value) -> Optional[float]:
    try:
        if value is None or pd.isna(value):
            return None
        return float(value)
    except Exception:
        return None


def _retry_sleep(attempt: int) -> None:
    time.sleep(0.25 * attempt)


def _extract_close_series(df: pd.DataFrame) -> pd.Series:
    if df is None or df.empty or "Close" not in df.columns:
        return pd.Series(dtype=float)

    close = df["Close"]

    if isinstance(close, pd.DataFrame):
        if close.empty:
            return pd.Series(dtype=float)
        close = close.iloc[:, 0]

    close = pd.to_numeric(close, errors="coerce").dropna()
    return close


@st.cache_data(ttl=HIST_CACHE_TTL, show_spinner=False)
def get_historical_data(
    symbol: str,
    period: str = "1y",
    interval: str = "1d",
) -> pd.DataFrame:
    for attempt in range(1, 4):
        try:
            df = yf.download(
                tickers=symbol,
                period=period,
                interval=interval,
                auto_adjust=False,
                progress=False,
                threads=False,
                group_by="column",
            )

            df = _normalize_columns(df)

            required = {"Open", "High", "Low", "Close", "Volume"}
            if df.empty or not required.issubset(set(df.columns)):
                if attempt < 3:
                    _retry_sleep(attempt)
                    continue
                return pd.DataFrame()

            close = _extract_close_series(df)
            if close.empty:
                if attempt < 3:
                    _retry_sleep(attempt)
                    continue
                return pd.DataFrame()

            df = df.loc[close.index].copy()
            return df

        except Exception:
            if attempt < 3:
                _retry_sleep(attempt)

    return pd.DataFrame()


def _extract_from_fast_info(fast_info) -> Dict:
    if not fast_info:
        return {}

    keys = [
        "lastPrice",
        "regularMarketPrice",
        "last_price",
        "previousClose",
        "previous_close",
    ]

    for key in keys:
        try:
            value = _safe_float(fast_info.get(key))
            if value is not None and value > 0:
                return {
                    "market_price": value,
                    "market_price_source": f"fast_info.{key}",
                    "market_price_available": True,
                }
        except Exception:
            continue

    return {}


def _extract_from_info(info: Dict) -> Dict:
    if not info:
        return {}

    keys = [
        "regularMarketPrice",
        "currentPrice",
        "navPrice",
        "bid",
        "ask",
        "previousClose",
    ]

    for key in keys:
        try:
            value = _safe_float(info.get(key))
            if value is not None and value > 0:
                return {
                    "market_price": value,
                    "market_price_source": f"info.{key}",
                    "market_price_available": True,
                }
        except Exception:
            continue

    return {}


def _extract_from_history(ticker: yf.Ticker) -> Dict:
    attempts = [
        {"period": "1d", "interval": "1m", "source": "history.1d.1m.Close"},
        {"period": "5d", "interval": "15m", "source": "history.5d.15m.Close"},
        {"period": "1mo", "interval": "1d", "source": "history.1mo.1d.Close"},
    ]

    for cfg in attempts:
        try:
            hist = ticker.history(
                period=cfg["period"],
                interval=cfg["interval"],
                auto_adjust=False,
            )
            hist = _normalize_columns(hist)

            close = _extract_close_series(hist)
            if close.empty:
                continue

            value = _safe_float(close.iloc[-1])
            if value is not None and value > 0:
                return {
                    "market_price": value,
                    "market_price_source": cfg["source"],
                    "market_price_available": True,
                }
        except Exception:
            continue

    return {}


@st.cache_data(ttl=LIVE_CACHE_TTL, show_spinner=False)
def get_live_price_payload(symbol: str) -> Dict:
    for attempt in range(1, 3):
        try:
            ticker = yf.Ticker(symbol)

            try:
                fast_info = getattr(ticker, "fast_info", None)
                payload = _extract_from_fast_info(fast_info)
                if payload:
                    return payload
            except Exception:
                pass

            try:
                info = getattr(ticker, "info", None)
                payload = _extract_from_info(info or {})
                if payload:
                    return payload
            except Exception:
                pass

            payload = _extract_from_history(ticker)
            if payload:
                return payload

        except Exception:
            if attempt < 2:
                _retry_sleep(attempt)

    return {
        "market_price": None,
        "market_price_source": None,
        "market_price_available": False,
    }


def get_analysis_price(hist: pd.DataFrame) -> Optional[float]:
    close = _extract_close_series(hist)
    if close.empty:
        return None
    return _safe_float(close.iloc[-1])


def get_price_snapshot(
    symbol: str,
    hist: pd.DataFrame,
    fetch_live_price: bool = True,
) -> Dict:
    analysis_price = get_analysis_price(hist)

    market_price = None
    market_price_source = None
    market_price_available = False

    if fetch_live_price:
        live_payload = get_live_price_payload(symbol)
        market_price = _safe_float(live_payload.get("market_price"))
        market_price_source = live_payload.get("market_price_source")
        market_price_available = bool(live_payload.get("market_price_available", False))

    price_gap_pct = None
    if analysis_price not in [None, 0] and market_price not in [None, 0]:
        try:
            price_gap_pct = ((float(market_price) / float(analysis_price)) - 1.0) * 100.0
        except Exception:
            price_gap_pct = None

    return {
        "symbol": symbol,
        "analysis_price": round(analysis_price, 2) if analysis_price is not None else None,
        "market_price": round(market_price, 2) if market_price is not None else None,
        "price_gap_pct": round(price_gap_pct, 2) if price_gap_pct is not None else None,
        "market_price_source": market_price_source,
        "market_price_available": market_price_available,
    }


def enrich_with_live_prices(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty or "symbol" not in df.columns:
        return df

    result = df.copy()

    market_prices: List[Optional[float]] = []
    price_gaps: List[Optional[float]] = []
    sources: List[Optional[str]] = []
    available_flags: List[bool] = []

    for _, row in result.iterrows():
        symbol = row.get("symbol")
        analysis_price = _safe_float(row.get("analysis_price"))

        live = get_live_price_payload(symbol)
        market_price = _safe_float(live.get("market_price"))

        gap = None
        if analysis_price not in [None, 0] and market_price not in [None, 0]:
            try:
                gap = ((market_price / analysis_price) - 1.0) * 100.0
            except Exception:
                gap = None

        market_prices.append(round(market_price, 2) if market_price is not None else None)
        price_gaps.append(round(gap, 2) if gap is not None else None)
        sources.append(live.get("market_price_source"))
        available_flags.append(bool(live.get("market_price_available", False)))

    result["market_price"] = market_prices
    result["price_gap_pct"] = price_gaps
    result["market_price_source"] = sources
    result["market_price_available"] = available_flags

    return result


def enrich_top_rows_with_live_prices(df: pd.DataFrame, top_n: int = 3) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    result = df.head(top_n).copy()
    return enrich_with_live_prices(result)


def batch_get_historical(
    symbols: List[str],
    period: str = "1y",
    interval: str = "1d",
) -> Dict[str, pd.DataFrame]:
    return {
        symbol: get_historical_data(symbol, period, interval)
        for symbol in symbols
    }