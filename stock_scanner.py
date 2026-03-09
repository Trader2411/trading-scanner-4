from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional

import pandas as pd
import yfinance as yf

from config import (
    DEFAULT_HISTORY_INTERVAL,
    DEFAULT_HISTORY_PERIOD,
    SCANNER_MAX_WORKERS,
    MIN_HISTORY_LENGTH,
    MARKET_INDEX,
    SYMBOL_META,
)
from data_fetcher import get_price_snapshot
from indicators import calculate_indicators
from ranking import add_trade_score


# ============================================================
# Konfiguration
# ============================================================

BATCH_SIZE = 80


# ============================================================
# Interne Hilfsfunktionen
# ============================================================

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


def _normalize_symbol_list(symbols: List[str]) -> List[str]:
    if not symbols:
        return []

    seen = set()
    result: List[str] = []

    for symbol in symbols:
        if symbol is None:
            continue

        clean = str(symbol).strip().upper()
        if not clean:
            continue

        if clean not in seen:
            seen.add(clean)
            result.append(clean)

    return result


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


def _safe_numeric_series(series) -> pd.Series:
    if series is None:
        return pd.Series(dtype=float)

    if isinstance(series, pd.DataFrame):
        if series.empty:
            return pd.Series(dtype=float)
        series = series.iloc[:, 0]

    return pd.to_numeric(series, errors="coerce").dropna()


def _download_batch_history(
    symbols: List[str],
    period: str = DEFAULT_HISTORY_PERIOD,
    interval: str = DEFAULT_HISTORY_INTERVAL,
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
    benchmark_symbol: str = MARKET_INDEX,
    period: str = DEFAULT_HISTORY_PERIOD,
    interval: str = DEFAULT_HISTORY_INTERVAL,
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

        close = _safe_numeric_series(benchmark_df["Close"])
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


def _build_error_row(symbol: str, status: str, error: Optional[str] = None) -> Dict:
    meta = _get_meta(symbol)
    row = {
        "symbol": symbol,
        "name": meta["name"],
        "wkn": meta["wkn"],
        "sector": meta["sector"],
        "status": status,
    }
    if error:
        row["error"] = error
    return row


# ============================================================
# Einzelanalyse
# ============================================================

def scan_single_symbol(
    symbol: str,
    hist: pd.DataFrame,
    benchmark_close: Optional[pd.Series] = None,
    fetch_live_price: bool = False,
) -> Dict:
    meta = _get_meta(symbol)

    if hist is None or hist.empty or "Close" not in hist.columns or len(hist) < MIN_HISTORY_LENGTH:
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
        symbol=symbol,
        hist=hist,
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


# ============================================================
# Mehrfachscan
# ============================================================

def scan_symbols(
    symbols: List[str],
    benchmark_symbol: str = MARKET_INDEX,
    period: str = DEFAULT_HISTORY_PERIOD,
    interval: str = DEFAULT_HISTORY_INTERVAL,
    max_workers: int = SCANNER_MAX_WORKERS,
    fetch_live_prices: bool = False,
) -> pd.DataFrame:
    if not symbols:
        return pd.DataFrame()

    clean_symbols = _normalize_symbol_list(symbols)
    if not clean_symbols:
        return pd.DataFrame()

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
        except Exception as exc:
            return _build_error_row(symbol, status="error", error=str(exc))

    worker_count = max(1, min(max_workers, len(clean_symbols)))

    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        rows = list(executor.map(worker, clean_symbols))

    df = pd.DataFrame(rows)

    if df.empty:
        return df

    if "trade_score" in df.columns:
        df["trade_score"] = pd.to_numeric(df["trade_score"], errors="coerce")

    sort_cols = []
    ascending = []

    if "status" in df.columns:
        df["_status_rank"] = df["status"].map(
            {
                "ok": 0,
                "invalid_indicator_data": 1,
                "insufficient_data": 2,
                "error": 3,
            }
        ).fillna(9)
        sort_cols.append("_status_rank")
        ascending.append(True)

    if "trade_score" in df.columns:
        sort_cols.append("trade_score")
        ascending.append(False)

    if "symbol" in df.columns:
        sort_cols.append("symbol")
        ascending.append(True)

    if sort_cols:
        df = df.sort_values(by=sort_cols, ascending=ascending, na_position="last")

    drop_cols = [col for col in ["_status_rank"] if col in df.columns]
    if drop_cols:
        df = df.drop(columns=drop_cols)

    return df.reset_index(drop=True)


# ============================================================
# Filterlogik
# ============================================================

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

    if result.empty:
        return pd.DataFrame()

    if "trade_score" in result.columns:
        result["trade_score"] = pd.to_numeric(result["trade_score"], errors="coerce")
        result = result[result["trade_score"] >= float(min_trade_score)]

    if require_golden_cross and "golden_cross" in result.columns:
        result["golden_cross"] = result["golden_cross"].fillna(False).astype(bool)
        result = result[result["golden_cross"]]

    if min_rs is not None and "relative_strength" in result.columns:
        result["relative_strength"] = pd.to_numeric(result["relative_strength"], errors="coerce")
        result = result[result["relative_strength"] >= float(min_rs)]

    if result.empty:
        return pd.DataFrame()

    sort_cols = []
    ascending = []

    if "trade_score" in result.columns:
        sort_cols.append("trade_score")
        ascending.append(False)

    if "momentum" in result.columns:
        result["momentum"] = pd.to_numeric(result["momentum"], errors="coerce")
        sort_cols.append("momentum")
        ascending.append(False)

    if "relative_strength" in result.columns:
        result["relative_strength"] = pd.to_numeric(result["relative_strength"], errors="coerce")
        sort_cols.append("relative_strength")
        ascending.append(False)

    if "symbol" in result.columns:
        sort_cols.append("symbol")
        ascending.append(True)

    if sort_cols:
        result = result.sort_values(by=sort_cols, ascending=ascending, na_position="last")

    return result.reset_index(drop=True)


# ============================================================
# Zusatzfunktionen
# ============================================================

def filter_watchlist_candidates(
    df: pd.DataFrame,
    min_trade_score: float = 50.0,
) -> pd.DataFrame:
    """
    Etwas lockerer Filter für Beobachtungskandidaten.
    """
    return filter_top_candidates(
        df=df,
        min_trade_score=min_trade_score,
        require_golden_cross=False,
        min_rs=None,
    )


def summarize_scan_status(df: pd.DataFrame) -> Dict:
    if df is None or df.empty or "status" not in df.columns:
        return {
            "total": 0,
            "ok": 0,
            "insufficient_data": 0,
            "invalid_indicator_data": 0,
            "error": 0,
        }

    status = df["status"].fillna("unknown").astype(str)

    return {
        "total": int(len(df)),
        "ok": int((status == "ok").sum()),
        "insufficient_data": int((status == "insufficient_data").sum()),
        "invalid_indicator_data": int((status == "invalid_indicator_data").sum()),
        "error": int((status == "error").sum()),
    }