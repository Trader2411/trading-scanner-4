from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Dict, Optional
from uuid import uuid4
import re

import pandas as pd

from config import DATA_DIR, PORTFOLIO_FILE


# ============================================================
# Konfiguration
# ============================================================

PORTFOLIO_STORE_DIR = DATA_DIR / "portfolios"

PORTFOLIO_COLUMNS = [
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

LEGACY_COLUMN_DEFAULTS = {
    "position_id": None,
    "symbol": None,
    "buy_date": None,
    "buy_price": None,
    "shares": None,
    "initial_stop_loss": None,
    "current_stop_loss": None,
    "target_price": None,
    "strategy_tag": None,
    "note": None,
    "created_at": None,
    "updated_at": None,
}


# ============================================================
# Interne Hilfsfunktionen
# ============================================================

def _utc_now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat()


def _to_float(value) -> Optional[float]:
    try:
        if value is None or pd.isna(value) or value == "":
            return None
        return float(value)
    except Exception:
        return None


def _normalize_symbol(value) -> Optional[str]:
    if value is None or pd.isna(value):
        return None

    text = str(value).strip().upper()
    return text if text else None


def _normalize_date(value) -> Optional[str]:
    if value is None or pd.isna(value) or value == "":
        return None

    if isinstance(value, datetime):
        return value.date().isoformat()

    if isinstance(value, date):
        return value.isoformat()

    text = str(value).strip()
    if not text:
        return None

    parsed = pd.to_datetime(text, errors="coerce")
    if pd.isna(parsed):
        return text

    return parsed.date().isoformat()


def _normalize_text(value) -> Optional[str]:
    if value is None or pd.isna(value):
        return None

    text = str(value).strip()
    return text if text else None


def _generate_position_id() -> str:
    return uuid4().hex[:12]


def _sanitize_user_key(user_key: Optional[str]) -> str:
    raw = "guest" if user_key is None else str(user_key).strip().lower()

    if not raw:
        raw = "guest"

    sanitized = re.sub(r"[^a-z0-9._@-]+", "_", raw)
    sanitized = sanitized.strip("._-")

    return sanitized or "guest"


def _get_streamlit_user_key_from_runtime() -> Optional[str]:
    try:
        import streamlit as st
    except Exception:
        return None

    try:
        session_user = st.session_state.get("portfolio_user_key")
        if session_user:
            return str(session_user)
    except Exception:
        pass

    try:
        user_obj = getattr(st, "user", None)
        if user_obj is None:
            return None

        for attr in ("email", "sub", "id", "name"):
            value = getattr(user_obj, attr, None)
            if value:
                return str(value)

        if isinstance(user_obj, dict):
            for key in ("email", "sub", "id", "name"):
                value = user_obj.get(key)
                if value:
                    return str(value)
    except Exception:
        return None

    return None


def _ensure_store_dir() -> Path:
    PORTFOLIO_STORE_DIR.mkdir(parents=True, exist_ok=True)
    return PORTFOLIO_STORE_DIR


def _empty_portfolio_df() -> pd.DataFrame:
    return pd.DataFrame(columns=PORTFOLIO_COLUMNS)


def _normalize_portfolio_df(df: Optional[pd.DataFrame]) -> pd.DataFrame:
    if df is None or df.empty:
        return _empty_portfolio_df()

    result = df.copy()

    for col, default_value in LEGACY_COLUMN_DEFAULTS.items():
        if col not in result.columns:
            result[col] = default_value

    result["position_id"] = result["position_id"].apply(
        lambda x: _normalize_text(x) or _generate_position_id()
    )
    result["symbol"] = result["symbol"].apply(_normalize_symbol)
    result["buy_date"] = result["buy_date"].apply(_normalize_date)
    result["buy_price"] = result["buy_price"].apply(_to_float)
    result["shares"] = result["shares"].apply(_to_float)
    result["initial_stop_loss"] = result["initial_stop_loss"].apply(_to_float)
    result["current_stop_loss"] = result["current_stop_loss"].apply(_to_float)
    result["target_price"] = result["target_price"].apply(_to_float)
    result["strategy_tag"] = result["strategy_tag"].apply(_normalize_text)
    result["note"] = result["note"].apply(_normalize_text)
    result["created_at"] = result["created_at"].apply(_normalize_text)
    result["updated_at"] = result["updated_at"].apply(_normalize_text)

    now_iso = _utc_now_iso()
    result["created_at"] = result["created_at"].fillna(now_iso)
    result["updated_at"] = result["updated_at"].fillna(now_iso)

    result = result.dropna(subset=["symbol", "buy_price", "shares"], how="any")
    result = result[result["shares"] > 0].copy()

    result = result[PORTFOLIO_COLUMNS].copy()
    result = result.drop_duplicates(subset=["position_id"], keep="last").reset_index(drop=True)

    return result


def _portfolio_path_for_user(user_key: Optional[str]) -> Path:
    safe_user_key = _sanitize_user_key(user_key)
    store_dir = _ensure_store_dir()
    return store_dir / f"{safe_user_key}.csv"


# ============================================================
# Öffentliche Benutzer-/Pfadfunktionen
# ============================================================

def get_current_portfolio_user(user_key: Optional[str] = None) -> str:
    if user_key is not None and str(user_key).strip():
        return _sanitize_user_key(user_key)

    runtime_user = _get_streamlit_user_key_from_runtime()
    if runtime_user:
        return _sanitize_user_key(runtime_user)

    return "guest"


def get_portfolio_path(user_key: Optional[str] = None) -> Path:
    resolved_user = get_current_portfolio_user(user_key)
    user_path = _portfolio_path_for_user(resolved_user)

    if resolved_user == "guest" and not user_path.exists() and PORTFOLIO_FILE.exists():
        return PORTFOLIO_FILE

    return user_path


# ============================================================
# Laden / Speichern
# ============================================================

def load_portfolio(user_key: Optional[str] = None) -> pd.DataFrame:
    path = get_portfolio_path(user_key)

    if not path.exists():
        return _empty_portfolio_df()

    try:
        df = pd.read_csv(path)
    except Exception:
        return _empty_portfolio_df()

    return _normalize_portfolio_df(df)


def save_portfolio(df: pd.DataFrame, user_key: Optional[str] = None) -> Path:
    resolved_user = get_current_portfolio_user(user_key)
    save_path = _portfolio_path_for_user(resolved_user)

    normalized = _normalize_portfolio_df(df)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    normalized.to_csv(save_path, index=False)

    return save_path


# ============================================================
# Positionsverwaltung
# ============================================================

def build_position_record(
    symbol: str,
    buy_price: float,
    shares: float,
    buy_date,
    initial_stop_loss: Optional[float] = None,
    current_stop_loss: Optional[float] = None,
    target_price: Optional[float] = None,
    strategy_tag: Optional[str] = None,
    note: Optional[str] = None,
    position_id: Optional[str] = None,
    created_at: Optional[str] = None,
) -> Dict:
    now_iso = _utc_now_iso()

    record = {
        "position_id": _normalize_text(position_id) or _generate_position_id(),
        "symbol": _normalize_symbol(symbol),
        "buy_date": _normalize_date(buy_date),
        "buy_price": _to_float(buy_price),
        "shares": _to_float(shares),
        "initial_stop_loss": _to_float(initial_stop_loss),
        "current_stop_loss": _to_float(current_stop_loss),
        "target_price": _to_float(target_price),
        "strategy_tag": _normalize_text(strategy_tag),
        "note": _normalize_text(note),
        "created_at": _normalize_text(created_at) or now_iso,
        "updated_at": now_iso,
    }

    return record


def add_position(position_data: Dict, user_key: Optional[str] = None) -> pd.DataFrame:
    portfolio = load_portfolio(user_key)

    record = build_position_record(
        symbol=position_data.get("symbol"),
        buy_price=position_data.get("buy_price"),
        shares=position_data.get("shares"),
        buy_date=position_data.get("buy_date"),
        initial_stop_loss=position_data.get("initial_stop_loss"),
        current_stop_loss=position_data.get("current_stop_loss"),
        target_price=position_data.get("target_price"),
        strategy_tag=position_data.get("strategy_tag"),
        note=position_data.get("note"),
        position_id=position_data.get("position_id"),
    )

    new_row = pd.DataFrame([record], columns=PORTFOLIO_COLUMNS)
    result = pd.concat([portfolio, new_row], ignore_index=True)
    result = _normalize_portfolio_df(result)

    save_portfolio(result, user_key)
    return result


def upsert_position(position_data: Dict, user_key: Optional[str] = None) -> pd.DataFrame:
    portfolio = load_portfolio(user_key)

    input_position_id = _normalize_text(position_data.get("position_id"))
    existing_mask = (
        portfolio["position_id"].astype(str) == input_position_id
        if input_position_id and not portfolio.empty
        else pd.Series([False] * len(portfolio), index=portfolio.index)
    )

    old_created_at = None
    if input_position_id and existing_mask.any():
        old_created_at = portfolio.loc[existing_mask, "created_at"].iloc[0]
        portfolio = portfolio.loc[~existing_mask].copy()

    record = build_position_record(
        symbol=position_data.get("symbol"),
        buy_price=position_data.get("buy_price"),
        shares=position_data.get("shares"),
        buy_date=position_data.get("buy_date"),
        initial_stop_loss=position_data.get("initial_stop_loss"),
        current_stop_loss=position_data.get("current_stop_loss"),
        target_price=position_data.get("target_price"),
        strategy_tag=position_data.get("strategy_tag"),
        note=position_data.get("note"),
        position_id=input_position_id,
        created_at=old_created_at,
    )

    updated_row = pd.DataFrame([record], columns=PORTFOLIO_COLUMNS)
    result = pd.concat([portfolio, updated_row], ignore_index=True)
    result = _normalize_portfolio_df(result)

    save_portfolio(result, user_key)
    return result


def delete_position(position_id: str, user_key: Optional[str] = None) -> pd.DataFrame:
    portfolio = load_portfolio(user_key)
    normalized_position_id = _normalize_text(position_id)

    if portfolio.empty or not normalized_position_id:
        return portfolio

    result = portfolio.loc[
        portfolio["position_id"].astype(str) != normalized_position_id
    ].copy()

    result = _normalize_portfolio_df(result)
    save_portfolio(result, user_key)

    return result


def update_position_fields(
    position_id: str,
    updates: Dict,
    user_key: Optional[str] = None,
) -> pd.DataFrame:
    portfolio = load_portfolio(user_key)
    normalized_position_id = _normalize_text(position_id)

    if portfolio.empty or not normalized_position_id:
        return portfolio

    mask = portfolio["position_id"].astype(str) == normalized_position_id
    if not mask.any():
        return portfolio

    row = portfolio.loc[mask].iloc[0].to_dict()

    allowed_fields = {
        "symbol",
        "buy_date",
        "buy_price",
        "shares",
        "initial_stop_loss",
        "current_stop_loss",
        "target_price",
        "strategy_tag",
        "note",
    }

    for field, value in updates.items():
        if field in allowed_fields:
            row[field] = value

    row["position_id"] = normalized_position_id
    row["created_at"] = row.get("created_at")

    portfolio = portfolio.loc[~mask].copy()

    record = build_position_record(
        symbol=row.get("symbol"),
        buy_price=row.get("buy_price"),
        shares=row.get("shares"),
        buy_date=row.get("buy_date"),
        initial_stop_loss=row.get("initial_stop_loss"),
        current_stop_loss=row.get("current_stop_loss"),
        target_price=row.get("target_price"),
        strategy_tag=row.get("strategy_tag"),
        note=row.get("note"),
        position_id=row.get("position_id"),
        created_at=row.get("created_at"),
    )

    updated_row = pd.DataFrame([record], columns=PORTFOLIO_COLUMNS)
    result = pd.concat([portfolio, updated_row], ignore_index=True)
    result = _normalize_portfolio_df(result)

    save_portfolio(result, user_key)
    return result


def save_current_stop(
    position_id: str,
    current_stop_loss: Optional[float],
    user_key: Optional[str] = None,
) -> pd.DataFrame:
    return update_position_fields(
        position_id=position_id,
        updates={"current_stop_loss": current_stop_loss},
        user_key=user_key,
    )


def clear_portfolio(user_key: Optional[str] = None) -> Path:
    empty_df = _empty_portfolio_df()
    return save_portfolio(empty_df, user_key)


# ============================================================
# Komfortfunktionen für UI / Weiterverarbeitung
# ============================================================

def get_portfolio_table(user_key: Optional[str] = None) -> pd.DataFrame:
    df = load_portfolio(user_key)
    if df.empty:
        return df

    result = df.copy()

    sort_buy_date = pd.to_datetime(result["buy_date"], errors="coerce")
    result = result.assign(_sort_buy_date=sort_buy_date)
    result = result.sort_values(
        by=["_sort_buy_date", "symbol"],
        ascending=[False, True],
        na_position="last",
    ).drop(columns=["_sort_buy_date"])

    return result.reset_index(drop=True)


def get_position_by_id(position_id: str, user_key: Optional[str] = None) -> Optional[Dict]:
    df = load_portfolio(user_key)
    if df.empty:
        return None

    normalized_position_id = _normalize_text(position_id)
    if not normalized_position_id:
        return None

    mask = df["position_id"].astype(str) == normalized_position_id
    if not mask.any():
        return None

    return df.loc[mask].iloc[0].to_dict()


def portfolio_exists(user_key: Optional[str] = None) -> bool:
    path = get_portfolio_path(user_key)
    return path.exists()