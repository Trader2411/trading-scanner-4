from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional

import pandas as pd
import streamlit as st
import yfinance as yf

from commodities_universe import get_commodity_name
from config import (
    DEFAULT_HISTORY_INTERVAL,
    DEFAULT_HISTORY_PERIOD,
    MARKET_INDEX,
    MIN_HISTORY_LENGTH,
    SCANNER_BATCH_SIZE,
    SCANNER_MAX_WORKERS,
)
from data_fetcher import get_price_snapshot
from indicators import calculate_indicators
from ranking import add_trade_score
from universe_loader import get_symbol_meta


# ============================================================
# Hilfsfunktionen
# ============================================================

def _get_meta(symbol: str) -> Dict:
    clean_symbol = str(symbol).strip().upper()
    meta = get_symbol_meta(clean_symbol)

    if "=F" in clean_symbol:
        return {
            "name": get_commodity_name(clean_symbol),
            "wkn": "-",
            "sector": "Rohstoffe",
        }

    return {
        "name": meta.get("name", clean_symbol),
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


def _safe_float(value) -> Optional[float]:
    try:
        if value is None or pd.isna(value) or value == "":
            return None
        return float(value)
    except Exception:
        return None


def _normalize_scalar(value):
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except Exception:
        pass
    return value


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


def _derive_macd_trend(macd_line, macd_signal) -> str:
    line = _safe_float(macd_line)
    signal = _safe_float(macd_signal)

    if line is None or signal is None:
        return "-"

    if line > signal and line > 0:
        return "Bullish"
    if line > signal:
        return "Improving"
    if line < signal and line < 0:
        return "Bearish"
    return "Weakening"


def _derive_signal(row: Dict) -> str:
    score = _safe_float(row.get("trade_score"))
    macd_trend = str(row.get("macd_trend") or "").strip().lower()
    rsi_signal = str(row.get("rsi_signal") or "").strip().lower()

    if score is None:
        return "-"

    if score >= 80 and macd_trend in {"bullish", "improving"}:
        return "Starkes Kaufsignal"
    if score >= 65:
        return "Beobachten"
    if rsi_signal == "oversold":
        return "Rebound möglich"
    return "-"


def _normalize_indicator_payload(indicator_data: Dict) -> Dict:
    raw = dict(indicator_data or {})

    numeric_keys = [
        "analysis_price",
        "sma50",
        "sma200",
        "ema21",
        "momentum",
        "relative_strength",
        "trend_strength",
        "distance_to_52w_high_pct",
        "rsi",
        "macd_line",
        "macd_signal",
        "macd_hist",
        "bb_middle",
        "bb_upper",
        "bb_lower",
        "bb_width_pct",
        "bb_position_pct",
        "ichimoku_tenkan",
        "ichimoku_kijun",
        "ichimoku_senkou_a",
        "ichimoku_senkou_b",
        "ichimoku_chikou",
        "trend_channel_upper",
        "trend_channel_lower",
        "trend_channel_mid",
        "trend_channel_position_pct",
        "swing_low",
        "recent_low",
        "stop_loss",
        "target_price",
        "atr14",
        "volatility_pct",
        "relative_volume",
        "volume_score",
    ]

    for key in numeric_keys:
        raw[key] = _safe_float(raw.get(key))

    raw["golden_cross"] = bool(raw.get("golden_cross", False))
    raw["rsi_signal"] = _normalize_scalar(raw.get("rsi_signal")) or "-"
    raw["ichimoku_signal"] = _normalize_scalar(raw.get("ichimoku_signal")) or "-"
    raw["trend_channel_signal"] = _normalize_scalar(raw.get("trend_channel_signal")) or "-"
    raw["macd_trend"] = _normalize_scalar(raw.get("macd_trend"))

    if raw["macd_trend"] in [None, "", "nan"]:
        raw["macd_trend"] = _derive_macd_trend(raw.get("macd_line"), raw.get("macd_signal"))

    if raw.get("trend_channel_signal") in [None, "", "nan", "-"]:
        pos = raw.get("trend_channel_position_pct")
        if pos is None:
            raw["trend_channel_signal"] = "-"
        elif pos >= 80:
            raw["trend_channel_signal"] = "Upper Breakout Zone"
        elif pos <= 20:
            raw["trend_channel_signal"] = "Lower Support Zone"
        else:
            raw["trend_channel_signal"] = "Mid Channel"

    return raw


def _sanitize_stop_and_target(row: Dict) -> Dict:
    reference_price = _safe_float(row.get("market_price"))
    if reference_price is None:
        reference_price = _safe_float(row.get("analysis_price"))

    stop_loss = _safe_float(row.get("stop_loss"))
    sma50 = _safe_float(row.get("sma50"))
    swing_low = _safe_float(row.get("swing_low"))
    recent_low = _safe_float(row.get("recent_low"))
    trend_low = _safe_float(row.get("trend_channel_lower"))

    if reference_price is not None and reference_price > 0:
        stop_candidates: List[float] = []

        for value in [stop_loss, sma50, swing_low, recent_low, trend_low]:
            if value is not None and value > 0 and value < reference_price:
                stop_candidates.append(value)

        stop_candidates.append(reference_price * 0.93)
        row["stop_loss"] = round(max(stop_candidates), 2)

    target_price = _safe_float(row.get("target_price"))
    sma200 = _safe_float(row.get("sma200"))
    trend_high = _safe_float(row.get("trend_channel_upper"))

    if reference_price is not None and reference_price > 0:
        target_candidates: List[float] = []

        for value in [target_price, sma200, trend_high]:
            if value is not None and value > reference_price:
                target_candidates.append(value)

        target_candidates.append(reference_price * 1.12)
        row["target_price"] = round(min(target_candidates), 2)

    return row


# ============================================================
# Historien / Benchmark
# ============================================================

def _download_raw_batch(
    batch: List[str],
    period: str,
    interval: str,
) -> pd.DataFrame:
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
        if raw is None:
            return pd.DataFrame()
        return raw
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=1800, show_spinner=False)
def _download_batch_history(
    symbols: tuple[str, ...],
    period: str = DEFAULT_HISTORY_PERIOD,
    interval: str = DEFAULT_HISTORY_INTERVAL,
) -> Dict[str, pd.DataFrame]:
    symbol_list = list(symbols)
    if not symbol_list:
        return {}

    history_map: Dict[str, pd.DataFrame] = {symbol: pd.DataFrame() for symbol in symbol_list}
    batch_size = max(25, int(SCANNER_BATCH_SIZE))

    for batch in _chunk_list(symbol_list, batch_size):
        raw = _download_raw_batch(batch, period, interval)

        # Fallback: wenn ein großer Batch fehlschlägt, halbieren
        if raw is None or raw.empty:
            if len(batch) <= 5:
                continue

            half = max(2, len(batch) // 2)
            sub_batches = _chunk_list(batch, half)

            for sub_batch in sub_batches:
                sub_raw = _download_raw_batch(sub_batch, period, interval)

                if sub_raw is None or sub_raw.empty:
                    continue

                if not isinstance(sub_raw.columns, pd.MultiIndex):
                    symbol = sub_batch[0]
                    history_map[symbol] = _normalize_single_hist(sub_raw)
                    continue

                available_symbols = list(sub_raw.columns.get_level_values(0).unique())

                for symbol in sub_batch:
                    if symbol not in available_symbols:
                        history_map[symbol] = pd.DataFrame()
                        continue
                    try:
                        history_map[symbol] = _normalize_single_hist(sub_raw[symbol].copy())
                    except Exception:
                        history_map[symbol] = pd.DataFrame()
            continue

        if not isinstance(raw.columns, pd.MultiIndex):
            symbol = batch[0]
            history_map[symbol] = _normalize_single_hist(raw)
            continue

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

    return history_map


@st.cache_data(ttl=1800, show_spinner=False)
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
            group_by="column",
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


# ============================================================
# Einzelscan
# ============================================================

def scan_single_symbol(
    symbol: str,
    hist: Optional[pd.DataFrame],
    benchmark_close: Optional[pd.Series],
    fetch_live_price: bool = False,
    include_fundamentals: bool = False,
    prefetched_market_price: Optional[float] = None,
) -> Dict:
    meta = _get_meta(symbol)

    if hist is None or hist.empty:
        return _build_error_row(symbol, status="insufficient_data", error="no_history")

    close = _safe_numeric_series(hist.get("Close"))
    if close.empty or len(close) < int(MIN_HISTORY_LENGTH):
        return _build_error_row(symbol, status="insufficient_data", error="history_too_short")

    indicator_data = calculate_indicators(hist, benchmark_close=benchmark_close)
    if not _is_valid_indicator_payload(indicator_data):
        return _build_error_row(symbol, status="invalid_indicator_data")

    row = {
        "symbol": symbol,
        "name": meta["name"],
        "wkn": meta["wkn"],
        "sector": meta["sector"],
        "status": "ok",
    }

    row.update(_normalize_indicator_payload(indicator_data))

    analysis_price = _safe_float(row.get("analysis_price"))
    if analysis_price is None and not close.empty:
        analysis_price = _safe_float(close.iloc[-1])
        row["analysis_price"] = analysis_price

    row["market_price"] = None
    row["market_price_source"] = None
    row["price_gap_pct"] = None

    if fetch_live_price:
        market_price = _safe_float(prefetched_market_price)
        if market_price is not None and market_price > 0:
            row["market_price"] = market_price
            row["market_price_source"] = "live"

    if row.get("market_price") is None and analysis_price is not None:
        row["market_price_source"] = "history"

    if row.get("market_price") is not None and analysis_price is not None and analysis_price != 0:
        row["price_gap_pct"] = round(((float(row["market_price"]) / analysis_price) - 1.0) * 100.0, 2)

    row = _sanitize_stop_and_target(row)
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
    include_fundamentals: bool = False,
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
        tuple(clean_symbols),
        period=period,
        interval=interval,
    )

    live_price_map: Dict[str, Optional[float]] = {}
    if fetch_live_prices:
        try:
            live_price_map = get_price_snapshot(clean_symbols)
        except Exception:
            live_price_map = {}

    def worker(symbol: str) -> Dict:
        hist = history_map.get(symbol, pd.DataFrame())

        try:
            return scan_single_symbol(
                symbol=symbol,
                hist=hist,
                benchmark_close=benchmark_close,
                fetch_live_price=fetch_live_prices,
                include_fundamentals=include_fundamentals,
                prefetched_market_price=_safe_float(live_price_map.get(symbol)),
            )
        except Exception as exc:
            return _build_error_row(symbol, status="error", error=str(exc))

    worker_count = max(1, min(int(max_workers), len(clean_symbols)))

    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        rows = list(executor.map(worker, clean_symbols))

    df = pd.DataFrame(rows)

    if df.empty:
        return df

    df = add_trade_score(df)

    if "status" in df.columns:
        ok_mask = df["status"] == "ok"
        df.loc[ok_mask, "signal"] = df.loc[ok_mask].apply(lambda row: _derive_signal(row.to_dict()), axis=1)

    numeric_cols = [
        "trade_score",
        "momentum",
        "relative_strength",
        "trend_strength",
        "analysis_price",
        "market_price",
        "price_gap_pct",
        "target_price",
        "stop_loss",
        "rsi",
        "macd_line",
        "macd_signal",
        "macd_hist",
        "bb_width_pct",
        "bb_position_pct",
        "volatility_pct",
        "trend_channel_position_pct",
        "distance_to_52w_high_pct",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    text_cols = [
        "signal",
        "macd_trend",
        "rsi_signal",
        "ichimoku_signal",
        "trend_channel_signal",
        "name",
        "wkn",
        "sector",
        "market_price_source",
    ]
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].where(~df[col].isna(), None)

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

    if "momentum" in df.columns:
        sort_cols.append("momentum")
        ascending.append(False)

    if "symbol" in df.columns:
        sort_cols.append("symbol")
        ascending.append(True)

    if sort_cols:
        df = df.sort_values(by=sort_cols, ascending=ascending, na_position="last")

    if "_status_rank" in df.columns:
        df = df.drop(columns=["_status_rank"])

    return df.reset_index(drop=True)


# ============================================================
# Filter
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
        result = result[result["golden_cross"].fillna(False).astype(bool)]

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
        sort_cols.append("momentum")
        ascending.append(False)

    if "relative_strength" in result.columns:
        sort_cols.append("relative_strength")
        ascending.append(False)

    if "symbol" in result.columns:
        sort_cols.append("symbol")
        ascending.append(True)

    if sort_cols:
        result = result.sort_values(by=sort_cols, ascending=ascending, na_position="last")

    return result.reset_index(drop=True)