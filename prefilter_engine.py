from __future__ import annotations

from typing import Dict, List, Optional

import pandas as pd
import yfinance as yf

from config import DEFAULT_HISTORY_INTERVAL, DEFAULT_HISTORY_PERIOD


# ============================================================
# Hilfsfunktionen
# ============================================================

def _normalize_symbol_list(symbols: List[str]) -> List[str]:
    seen = set()
    result: List[str] = []

    for symbol in symbols:
        if symbol is None:
            continue
        clean = str(symbol).strip().upper()
        if not clean or clean in seen:
            continue
        seen.add(clean)
        result.append(clean)

    return result


def _chunk_list(items: List[str], chunk_size: int) -> List[List[str]]:
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


def _safe_series(value) -> pd.Series:
    if value is None:
        return pd.Series(dtype=float)

    if isinstance(value, pd.DataFrame):
        if value.empty:
            return pd.Series(dtype=float)
        value = value.iloc[:, 0]

    return pd.to_numeric(value, errors="coerce").dropna()


def _normalize_single_hist(df: pd.DataFrame) -> pd.DataFrame:
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

    result = result.rename(columns=rename_map).sort_index()

    required = {"Open", "High", "Low", "Close", "Volume"}
    if not required.issubset(result.columns):
        return pd.DataFrame()

    return result.dropna(subset=["Close"]).copy()


# ============================================================
# Schnell-Download
# ============================================================

def _download_batch_history(
    symbols: List[str],
    period: str = DEFAULT_HISTORY_PERIOD,
    interval: str = DEFAULT_HISTORY_INTERVAL,
    batch_size: int = 200,
) -> Dict[str, pd.DataFrame]:
    result: Dict[str, pd.DataFrame] = {}
    clean_symbols = _normalize_symbol_list(symbols)

    for batch in _chunk_list(clean_symbols, batch_size):
        try:
            raw = yf.download(
                tickers=batch,
                period=period,
                interval=interval,
                auto_adjust=False,
                progress=False,
                threads=True,
                group_by="ticker",
            )
        except Exception:
            raw = pd.DataFrame()

        if raw is None or raw.empty:
            for symbol in batch:
                result[symbol] = pd.DataFrame()
            continue

        if not isinstance(raw.columns, pd.MultiIndex):
            symbol = batch[0]
            result[symbol] = _normalize_single_hist(raw)
            continue

        available_symbols = list(raw.columns.get_level_values(0).unique())

        for symbol in batch:
            if symbol not in available_symbols:
                result[symbol] = pd.DataFrame()
                continue

            try:
                result[symbol] = _normalize_single_hist(raw[symbol].copy())
            except Exception:
                result[symbol] = pd.DataFrame()

    return result


# ============================================================
# Smart Prefilter
# ============================================================

def _calc_prefilter_score(hist: pd.DataFrame) -> Optional[Dict]:
    if hist is None or hist.empty or "Close" not in hist.columns:
        return None

    close = _safe_series(hist["Close"])
    volume = _safe_series(hist["Volume"]) if "Volume" in hist.columns else pd.Series(dtype=float)

    if len(close) < 80:
        return None

    last_price = float(close.iloc[-1])

    sma20 = close.rolling(20).mean().iloc[-1] if len(close) >= 20 else None
    sma50 = close.rolling(50).mean().iloc[-1] if len(close) >= 50 else None

    if pd.isna(sma20):
        sma20 = None
    if pd.isna(sma50):
        sma50 = None

    momentum_20 = None
    if len(close) > 20 and close.iloc[-21] != 0:
        momentum_20 = ((close.iloc[-1] / close.iloc[-21]) - 1.0) * 100.0

    avg_volume_20 = None
    if not volume.empty and len(volume) >= 20:
        avg_volume_20 = float(volume.tail(20).mean())

    score = 0.0

    if sma20 is not None and last_price > sma20:
        score += 25.0

    if sma50 is not None and last_price > sma50:
        score += 30.0

    if sma20 is not None and sma50 is not None and sma20 > sma50:
        score += 15.0

    if momentum_20 is not None:
        if momentum_20 > 0:
            score += min(20.0, momentum_20)
        else:
            score += max(-10.0, momentum_20 / 2.0)

    if avg_volume_20 is not None:
        if avg_volume_20 > 5_000_000:
            score += 10.0
        elif avg_volume_20 > 1_000_000:
            score += 6.0
        elif avg_volume_20 > 250_000:
            score += 3.0

    return {
        "last_price": round(last_price, 2),
        "sma20": round(float(sma20), 2) if sma20 is not None else None,
        "sma50": round(float(sma50), 2) if sma50 is not None else None,
        "momentum_20": round(float(momentum_20), 2) if momentum_20 is not None else None,
        "avg_volume_20": round(float(avg_volume_20), 0) if avg_volume_20 is not None else None,
        "prefilter_score": round(score, 2),
    }


def prefilter_symbols_fast(
    symbols: List[str],
    top_n: int = 120,
    period: str = DEFAULT_HISTORY_PERIOD,
    interval: str = DEFAULT_HISTORY_INTERVAL,
    batch_size: int = 200,
) -> pd.DataFrame:
    clean_symbols = _normalize_symbol_list(symbols)
    if not clean_symbols:
        return pd.DataFrame()

    history_map = _download_batch_history(
        symbols=clean_symbols,
        period=period,
        interval=interval,
        batch_size=batch_size,
    )

    rows = []

    for symbol in clean_symbols:
        hist = history_map.get(symbol)
        payload = _calc_prefilter_score(hist)
        if not payload:
            continue

        rows.append({
            "symbol": symbol,
            **payload,
        })

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df["prefilter_score"] = pd.to_numeric(df["prefilter_score"], errors="coerce")
    df["momentum_20"] = pd.to_numeric(df["momentum_20"], errors="coerce")

    df = df.sort_values(
        by=["prefilter_score", "momentum_20", "symbol"],
        ascending=[False, False, True],
        na_position="last",
    ).reset_index(drop=True)

    if top_n and top_n > 0:
        df = df.head(int(top_n)).copy()

    return df