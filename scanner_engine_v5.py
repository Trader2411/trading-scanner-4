from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional

import pandas as pd
import yfinance as yf

from indicators import calculate_indicators
from ranking import add_trade_score


MAX_WORKERS = 10

COMMODITIES = [
    "GC=F",   # Gold
    "SI=F",   # Silber
    "CL=F",   # WTI
    "BZ=F",   # Brent
    "HG=F",   # Kupfer
    "NG=F",   # Erdgas
    "PL=F",   # Platin
    "PA=F",   # Palladium
    "ZW=F",   # Weizen
    "ZC=F",   # Mais
    "ZS=F",   # Sojabohnen
]


# ============================================================
# Helper
# ============================================================

def _safe_float(value) -> Optional[float]:
    try:
        if value is None:
            return None
        if isinstance(value, pd.Series):
            if value.empty:
                return None
            value = value.iloc[-1]
        if pd.isna(value):
            return None
        return float(value)
    except Exception:
        return None


def _normalize_hist(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    result = df.copy()

    if isinstance(result.columns, pd.MultiIndex):
        flattened = []
        for col in result.columns:
            if isinstance(col, tuple):
                flattened.append(col[0])
            else:
                flattened.append(col)
        result.columns = flattened

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


def _extract_close_price(hist: pd.DataFrame) -> Optional[float]:
    if hist is None or hist.empty or "Close" not in hist.columns:
        return None

    close = hist["Close"]

    if isinstance(close, pd.DataFrame):
        if close.empty:
            return None
        close = close.iloc[:, 0]

    close = pd.to_numeric(close, errors="coerce").dropna()

    if close.empty:
        return None

    return _safe_float(close.iloc[-1])


def _extract_indicator_value(indicators: Dict, key: str) -> Optional[float]:
    if not indicators:
        return None
    return _safe_float(indicators.get(key))


# ============================================================
# Data
# ============================================================

def load_price_history(symbol: str) -> pd.DataFrame:
    try:
        df = yf.download(
            symbol,
            period="1y",
            interval="1d",
            progress=False,
            auto_adjust=False,
            threads=False,
        )

        if df is None or df.empty:
            return pd.DataFrame()

        return _normalize_hist(df)

    except Exception:
        return pd.DataFrame()


def get_company_name(symbol: str) -> str:
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info or {}
        for key in ("shortName", "longName", "displayName"):
            value = info.get(key)
            if value:
                return str(value)
    except Exception:
        pass

    return symbol


# ============================================================
# Target / Stop
# ============================================================

def compute_targets(price: float, indicators: Dict) -> tuple[Optional[float], Optional[float]]:
    sma50 = _extract_indicator_value(indicators, "sma50")
    sma200 = _extract_indicator_value(indicators, "sma200")
    trend_low = _extract_indicator_value(indicators, "trend_channel_lower")
    trend_high = _extract_indicator_value(indicators, "trend_channel_upper")

    stop_candidates: List[float] = []
    target_candidates: List[float] = []

    if price and price > 0:
        stop_candidates.append(price * 0.92)
        target_candidates.append(price * 1.10)

    for value in (sma50, trend_low):
        if value is not None and value > 0 and value < price:
            stop_candidates.append(value)

    for value in (sma200, trend_high):
        if value is not None and value > price:
            target_candidates.append(value)

    stop = max(stop_candidates) if stop_candidates else None
    target = min(target_candidates) if target_candidates else None

    return target, stop


# ============================================================
# Scan one symbol
# ============================================================

def scan_symbol(symbol: str) -> Optional[Dict]:
    hist = load_price_history(symbol)

    if hist is None or hist.empty:
        return None

    indicators = calculate_indicators(hist)

    if not indicators:
        return None

    price = _extract_close_price(hist)

    if price is None:
        return None

    target, stop = compute_targets(price, indicators)

    result = {
        "symbol": symbol,
        "name": get_company_name(symbol),
        "price": price,
        "target": target,
        "stop": stop,
        "source": "yfinance",
    }

    result.update(indicators)
    return result


# ============================================================
# Main scanner
# ============================================================

def scan_symbols(symbols: List[str]) -> pd.DataFrame:
    if not symbols:
        return pd.DataFrame()

    clean_symbols: List[str] = []
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
        return pd.DataFrame()

    results: List[Dict] = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        rows = executor.map(scan_symbol, clean_symbols)
        for row in rows:
            if row is not None:
                results.append(row)

    df = pd.DataFrame(results)

    if df.empty:
        return df

    df = add_trade_score(df)
    return df


# ============================================================
# Commodity scanner
# ============================================================

def scan_commodities() -> pd.DataFrame:
    return scan_symbols(COMMODITIES)