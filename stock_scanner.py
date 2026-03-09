from __future__ import annotations

from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor
import math

import pandas as pd
import yfinance as yf

from config import MIN_HISTORY_ROWS, SYMBOL_META
from indicators import calculate_indicators
from ranking import add_trade_score
from data_fetcher import get_price_snapshot


BATCH_SIZE = 80


def _get_meta(symbol: str) -> Dict:
    meta = SYMBOL_META.get(symbol, {})
    return {
        "name": meta.get("name", symbol),
        "wkn": meta.get("wkn", "-"),
        "sector": meta.get("sector", "Sonstige"),
    }


def _chunk_list(items: List[str], chunk_size: int) -> List[List[str]]:
    if not items:
        return []
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


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

    result = result.rename(columns=rename_map)
    result = result.sort_index()

    required = {"Open", "High", "Low", "Close", "Volume"}
    if not required.issubset(set(result.columns)):
        return pd.DataFrame()

    result = result.dropna(subset=["Close"]).copy()
    return result


def _download_batch_history(
    symbols: List[str],
    period: str = "1y",
    interval: str = "1d",
) -> Dict[str, pd.DataFrame]:
    """
    Lädt historische Daten blockweise für viele Ticker gleichzeitig.
    """
    if not symbols:
        return {}

    history_map: Dict[str, pd.DataFrame] = {symbol: pd.DataFrame() for symbol in symbols}

    for batch in _chunk_list(symbols, BATCH_SIZE):
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

            if raw is None or raw.empty:
                continue

            # Einzelticker-Fall
            if not isinstance(raw.columns, pd.MultiIndex):
                symbol = batch[0]
                history_map[symbol] = _normalize_single_hist(raw)
                continue

            # Multi-Ticker-Fall
            available_symbols = list(raw.columns.get_level_values(0).unique())

            for symbol in batch:
                if symbol not in available_symbols:
                    history_map[symbol] = pd.DataFrame()
                    continue

                try:
                    sub = raw[symbol].copy()
                    history_map[symbol] = _normalize_single_hist(sub)
                except Exception:
                    history_map[symbol] = pd.DataFrame()

        except Exception:
            for symbol in batch:
                if symbol not in history_map:
                    history_map[symbol] = pd.DataFrame()

    return history_map


def _extract_benchmark_close(
    benchmark_symbol: str = "^GSPC",
    period: str = "1y",
    interval: str = "1d",
) -> Optional[pd.Series]:
    try:
        benchmark_df = yf.download(
            tickers=benchmark_symbol,
            period=period,
            interval=interval,
            auto_adjust=False,
            progress=False,
            threads=False,
        )

        benchmark_df = _normalize_single_hist(benchmark_df)
        if benchmark_df.empty or "Close" not in benchmark_df.columns:
            return None

        close = benchmark_df["Close"]
        if isinstance(close, pd.DataFrame):
            if close.empty:
                return None
            close = close.iloc[:, 0]

        close = pd.to_numeric(close, errors="coerce").dropna()
        if close.empty:
            return None

        return close

    except Exception:
        return None


def _is_valid_indicator_payload(indicator_data: Dict) -> bool:
    if not indicator_data:
        return False

    keys = [
        "analysis_price",
        "momentum",
        "relative_strength",
        "target_price",
        "stop_loss",
    ]

    for key in keys:
        value = indicator_data.get(key)
        if value is not None and not pd.isna(value):
            return True

    return False


def scan_single_symbol(
    symbol: str,
    hist: pd.DataFrame,
    benchmark_close: Optional[pd.Series] = None,
    fetch_live_price: bool = False,
) -> Dict:
    meta = _get_meta(symbol)

    if hist is None or hist.empty or "Close" not in hist.columns or len(hist) < MIN_HISTORY_ROWS:
        return {
            "symbol": symbol,
            "name": meta["name"],
            "wkn": meta["wkn"],
            "sector": meta["sector"],
            "status": "insufficient_data",
        }

    indicator_data = calculate_indicators(hist, benchmark_close=benchmark_close)

    if not _is_valid_indicator_payload(indicator_data):
        return {
            "symbol": symbol,
            "name": meta["name"],
            "wkn": meta["wkn"],
            "sector": meta["sector"],
            "status": "invalid_indicator_data",
        }

    price_data = get_price_snapshot(
        symbol,
        hist,
        fetch_live_price=fetch_live_price,
    )

    row = {
        "symbol": symbol,
        "name": meta["name"],
        "wkn": meta["wkn"],
        "sector": meta["sector"],
        **indicator_data,
        **price_data,
        "status": "ok",
    }

    row = add_trade_score(row)
    return row


def scan_symbols(
    symbols: List[str],
    benchmark_symbol: str = "^GSPC",
    period: str = "1y",
    interval: str = "1d",
    max_workers: int = 8,
    fetch_live_prices: bool = False,
) -> pd.DataFrame:
    if not symbols:
        return pd.DataFrame()

    # Dedupe, Reihenfolge behalten
    seen = set()
    clean_symbols: List[str] = []
    for symbol in symbols:
        if symbol not in seen:
            seen.add(symbol)
            clean_symbols.append(symbol)

    benchmark_close = _extract_benchmark_close(
        benchmark_symbol=benchmark_symbol,
        period=period,
        interval=interval,
    )

    history_map = _download_batch_history(
        clean_symbols,
        period=period,
        interval=interval,
    )

    def worker(symbol: str) -> Dict:
        hist = history_map.get(symbol, pd.DataFrame())
        try:
            return scan_single_symbol(
                symbol=symbol,
                hist=hist,
                benchmark_close=benchmark_close,
                fetch_live_price=fetch_live_prices,
            )
        except Exception as e:
            meta = _get_meta(symbol)
            return {
                "symbol": symbol,
                "name": meta["name"],
                "wkn": meta["wkn"],
                "sector": meta["sector"],
                "status": "error",
                "error": str(e),
            }

    worker_count = max(1, min(max_workers, len(clean_symbols)))

    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        rows = list(executor.map(worker, clean_symbols))

    df = pd.DataFrame(rows)

    if df.empty:
        return df

    if "trade_score" in df.columns:
        df["trade_score"] = pd.to_numeric(df["trade_score"], errors="coerce")

    df = df.sort_values(
        by="trade_score",
        ascending=False,
        na_position="last",
    ).reset_index(drop=True)

    return df


def filter_top_candidates(
    df: pd.DataFrame,
    min_trade_score: float = 60.0,
    require_golden_cross: bool = False,
    min_rs: Optional[float] = None,
) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    result = df.copy()

    if "status" in result.columns:
        result = result[result["status"] == "ok"]

    if "trade_score" in result.columns:
        result["trade_score"] = pd.to_numeric(result["trade_score"], errors="coerce")
        result = result[result["trade_score"] >= min_trade_score]

    if require_golden_cross and "golden_cross" in result.columns:
        result["golden_cross"] = result["golden_cross"].fillna(False).astype(bool)
        result = result[result["golden_cross"]]

    if min_rs is not None and "relative_strength" in result.columns:
        result["relative_strength"] = pd.to_numeric(result["relative_strength"], errors="coerce")
        result = result[result["relative_strength"] >= min_rs]

    return result.reset_index(drop=True)