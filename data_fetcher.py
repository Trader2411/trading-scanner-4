from __future__ import annotations

import time
from typing import Dict, List, Optional

import pandas as pd
import streamlit as st
import yfinance as yf

try:
    from config import CACHE_LIVE_PRICES, LIVE_PRICE_TIMEOUT
except Exception:
    CACHE_LIVE_PRICES = 120
    LIVE_PRICE_TIMEOUT = 10


# ============================================================
# Cache / Timeouts
# ============================================================

HIST_CACHE_TTL = 3600
LIVE_CACHE_TTL = int(CACHE_LIVE_PRICES) if CACHE_LIVE_PRICES else 120


# ============================================================
# Interne Hilfsfunktionen
# ============================================================

def _safe_float(value) -> Optional[float]:
    try:
        if value is None or value == "" or pd.isna(value):
            return None
        return float(value)
    except Exception:
        return None


def _retry_sleep(attempt: int) -> None:
    time.sleep(0.25 * max(1, attempt))


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    result = df.copy()

    if isinstance(result.columns, pd.MultiIndex):
        cleaned_cols = []
        for col in result.columns:
            if isinstance(col, tuple):
                cleaned_cols.append(col[0])
            else:
                cleaned_cols.append(col)
        result.columns = cleaned_cols

    rename_map = {}
    for col in result.columns:
        col_l = str(col).strip().lower()
        if col_l == "open":
            rename_map[col] = "Open"
        elif col_l == "high":
            rename_map[col] = "High"
        elif col_l == "low":
            rename_map[col] = "Low"
        elif col_l == "close":
            rename_map[col] = "Close"
        elif col_l == "adj close":
            rename_map[col] = "Adj Close"
        elif col_l == "volume":
            rename_map[col] = "Volume"

    result = result.rename(columns=rename_map)
    result = result.sort_index()
    return result


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


def _extract_low_series(df: pd.DataFrame) -> pd.Series:
    if df is None or df.empty or "Low" not in df.columns:
        return pd.Series(dtype=float)

    low = df["Low"]

    if isinstance(low, pd.DataFrame):
        if low.empty:
            return pd.Series(dtype=float)
        low = low.iloc[:, 0]

    low = pd.to_numeric(low, errors="coerce").dropna()
    return low


def _extract_high_series(df: pd.DataFrame) -> pd.Series:
    if df is None or df.empty or "High" not in df.columns:
        return pd.Series(dtype=float)

    high = df["High"]

    if isinstance(high, pd.DataFrame):
        if high.empty:
            return pd.Series(dtype=float)
        high = high.iloc[:, 0]

    high = pd.to_numeric(high, errors="coerce").dropna()
    return high


def _extract_open_series(df: pd.DataFrame) -> pd.Series:
    if df is None or df.empty or "Open" not in df.columns:
        return pd.Series(dtype=float)

    open_ = df["Open"]

    if isinstance(open_, pd.DataFrame):
        if open_.empty:
            return pd.Series(dtype=float)
        open_ = open_.iloc[:, 0]

    open_ = pd.to_numeric(open_, errors="coerce").dropna()
    return open_


# ============================================================
# Historische Daten
# ============================================================

@st.cache_data(ttl=HIST_CACHE_TTL, show_spinner=False)
def get_historical_data(
    symbol: str,
    period: str = "1y",
    interval: str = "1d",
) -> pd.DataFrame:
    """
    Lädt historische Kursdaten robust über yfinance.
    """
    if not symbol:
        return pd.DataFrame()

    for attempt in range(1, 4):
        try:
            df = yf.download(
                tickers=symbol,
                period=period,
                interval=interval,
                auto_adjust=False,
                progress=False,
                threads=False,
                timeout=LIVE_PRICE_TIMEOUT,
            )

            df = _normalize_columns(df)

            if df is None or df.empty:
                _retry_sleep(attempt)
                continue

            required = {"Open", "High", "Low", "Close", "Volume"}
            if not required.issubset(set(df.columns)):
                _retry_sleep(attempt)
                continue

            df = df.dropna(subset=["Close"]).copy()
            if df.empty:
                _retry_sleep(attempt)
                continue

            return df

        except Exception:
            _retry_sleep(attempt)

    return pd.DataFrame()


# ============================================================
# Live / Market Price
# ============================================================

@st.cache_data(ttl=LIVE_CACHE_TTL, show_spinner=False)
def get_price_snapshot(symbols: List[str]) -> Dict[str, Optional[float]]:
    """
    Liefert ein simples Mapping: Symbol -> letzter Preis
    """
    result: Dict[str, Optional[float]] = {}

    if not symbols:
        return result

    clean_symbols = []
    seen = set()
    for symbol in symbols:
        if symbol is None:
            continue
        text = str(symbol).strip().upper()
        if not text or text in seen:
            continue
        seen.add(text)
        clean_symbols.append(text)

    if not clean_symbols:
        return result

    for symbol in clean_symbols:
        result[symbol] = None

    try:
        tickers = yf.Tickers(" ".join(clean_symbols))

        for symbol in clean_symbols:
            try:
                ticker = tickers.tickers.get(symbol)
                if ticker is None:
                    continue

                fast_info = getattr(ticker, "fast_info", {}) or {}

                price = (
                    fast_info.get("lastPrice")
                    or fast_info.get("last_price")
                    or fast_info.get("regularMarketPrice")
                )

                result[symbol] = _safe_float(price)
            except Exception:
                result[symbol] = None

        return result

    except Exception:
        return result


def get_live_price_payload(symbol: str) -> Dict:
    """
    Einzelner Live-Preis mit Quelle.
    """
    if not symbol:
        return {
            "symbol": symbol,
            "market_price": None,
            "market_price_source": None,
        }

    snapshot = get_price_snapshot([symbol])
    price = _safe_float(snapshot.get(str(symbol).strip().upper()))

    return {
        "symbol": str(symbol).strip().upper(),
        "market_price": price,
        "market_price_source": "live" if price is not None else None,
    }


def get_market_price(symbol: str, hist: Optional[pd.DataFrame] = None) -> Dict:
    """
    Versucht zuerst Live-Preis, fällt sonst auf letzten historischen Schlusskurs zurück.
    """
    payload = get_live_price_payload(symbol)
    market_price = _safe_float(payload.get("market_price"))

    if market_price is not None:
        return payload

    if hist is None or hist.empty:
        hist = get_historical_data(symbol, period="1y", interval="1d")

    close = _extract_close_series(hist)
    fallback_price = _safe_float(close.iloc[-1]) if not close.empty else None

    return {
        "symbol": str(symbol).strip().upper(),
        "market_price": fallback_price,
        "market_price_source": "history" if fallback_price is not None else None,
    }


# ============================================================
# DataFrame anreichern
# ============================================================

def enrich_with_live_prices(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ergänzt market_price, market_price_source und price_gap_pct.
    """
    if df is None or df.empty:
        return df

    result = df.copy()

    if "symbol" not in result.columns:
        return result

    symbols = [
        str(symbol).strip().upper()
        for symbol in result["symbol"].dropna().tolist()
        if str(symbol).strip()
    ]

    live_prices = get_price_snapshot(symbols)

    result["market_price"] = result["symbol"].astype(str).str.upper().map(live_prices)
    result["market_price_source"] = result["market_price"].apply(
        lambda x: "live" if _safe_float(x) is not None else None
    )

    if "analysis_price" in result.columns:
        analysis = pd.to_numeric(result["analysis_price"], errors="coerce")
        market = pd.to_numeric(result["market_price"], errors="coerce")

        result["price_gap_pct"] = None
        valid_mask = analysis.notna() & market.notna() & (analysis != 0)
        result.loc[valid_mask, "price_gap_pct"] = (
            ((market[valid_mask] / analysis[valid_mask]) - 1.0) * 100.0
        ).round(2)

    # Fallback auf history, wenn analysis_price vorhanden aber live fehlt
    if "analysis_price" in result.columns:
        no_live_mask = result["market_price"].isna()
        result.loc[no_live_mask, "market_price_source"] = result.loc[no_live_mask, "market_price_source"].fillna("history")

    return result