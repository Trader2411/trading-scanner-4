from __future__ import annotations

from typing import Dict, Optional

import pandas as pd

try:
    from config import MIN_STOCKS_PER_SECTOR
except Exception:
    MIN_STOCKS_PER_SECTOR = 5


# ============================================================
# Interne Hilfsfunktionen
# ============================================================

def _safe_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def _round_or_none(value, digits: int = 2):
    try:
        if value is None or pd.isna(value):
            return None
        return round(float(value), digits)
    except Exception:
        return None


# ============================================================
# Sektor-Ranking
# ============================================================

def rank_sectors(
    scan_df: pd.DataFrame,
    min_stocks_per_sector: int = MIN_STOCKS_PER_SECTOR,
) -> pd.DataFrame:
    """
    Aggregiert Scanner-Daten auf Sektorebene.

    Erwartete Eingabespalten möglichst:
    - sector
    - trade_score
    - momentum
    - relative_strength
    - golden_cross
    - analysis_price
    - sma50
    """
    if scan_df is None or scan_df.empty:
        return pd.DataFrame()

    df = scan_df.copy()

    if "status" in df.columns:
        df = df[df["status"] == "ok"]

    if df.empty or "sector" not in df.columns:
        return pd.DataFrame()

    df["sector"] = df["sector"].fillna("Sonstige").astype(str)

    numeric_cols = [
        "trade_score",
        "momentum",
        "relative_strength",
        "analysis_price",
        "sma50",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = _safe_numeric(df[col])

    if "golden_cross" in df.columns:
        df["golden_cross"] = df["golden_cross"].fillna(False).astype(bool)
    else:
        df["golden_cross"] = False

    if "analysis_price" in df.columns and "sma50" in df.columns:
        df["above_sma50"] = (
            df["analysis_price"].notna()
            & df["sma50"].notna()
            & (df["analysis_price"] > df["sma50"])
        )
    else:
        df["above_sma50"] = False

    grouped = df.groupby("sector", dropna=False)

    summary = grouped.agg(
        anzahl_aktien=("sector", "size"),
        durchschnitt_trade_score=("trade_score", "mean"),
        durchschnitt_momentum=("momentum", "mean"),
        durchschnitt_relative_strength=("relative_strength", "mean"),
        anteil_golden_cross=("golden_cross", "mean"),
        anteil_ueber_sma50=("above_sma50", "mean"),
    ).reset_index()

    summary = summary[summary["anzahl_aktien"] >= int(min_stocks_per_sector)].copy()

    if summary.empty:
        return pd.DataFrame()

    summary["anteil_golden_cross"] = summary["anteil_golden_cross"] * 100.0
    summary["anteil_ueber_sma50"] = summary["anteil_ueber_sma50"] * 100.0

    # Gesamtsektorwertung
    summary["sektor_score"] = (
        summary["durchschnitt_trade_score"].fillna(0) * 0.40
        + summary["durchschnitt_momentum"].fillna(0).clip(lower=-10, upper=25).add(10).div(35).mul(100) * 0.20
        + summary["durchschnitt_relative_strength"].fillna(0) * 0.20
        + summary["anteil_golden_cross"].fillna(0) * 0.10
        + summary["anteil_ueber_sma50"].fillna(0) * 0.10
    )

    summary["sektor_score"] = summary["sektor_score"].clip(lower=0, upper=100)

    summary = summary.rename(
        columns={
            "sector": "Sektor",
            "anzahl_aktien": "Anzahl Aktien",
            "durchschnitt_trade_score": "Ø Trade Score",
            "durchschnitt_momentum": "Ø Momentum",
            "durchschnitt_relative_strength": "Ø Relative Stärke",
            "anteil_golden_cross": "Golden Cross %",
            "anteil_ueber_sma50": "Über SMA50 %",
            "sektor_score": "Sektor Score",
        }
    )

    for col in [
        "Ø Trade Score",
        "Ø Momentum",
        "Ø Relative Stärke",
        "Golden Cross %",
        "Über SMA50 %",
        "Sektor Score",
    ]:
        summary[col] = summary[col].apply(_round_or_none)

    summary = summary.sort_values(
        by=["Sektor Score", "Ø Trade Score", "Sektor"],
        ascending=[False, False, True],
        na_position="last",
    ).reset_index(drop=True)

    return summary


# ============================================================
# Top-Sektor
# ============================================================

def get_top_sector_label(scan_df: pd.DataFrame) -> str:
    """
    Gibt den Namen des aktuell stärksten Sektors zurück.
    """
    ranked = rank_sectors(scan_df)

    if ranked is None or ranked.empty:
        return "Kein klarer Leader"

    try:
        return str(ranked.iloc[0]["Sektor"])
    except Exception:
        return "Kein klarer Leader"


# ============================================================
# Zusatzfunktion für spätere UI-Erweiterungen
# ============================================================

def summarize_sector_strength(scan_df: pd.DataFrame) -> Dict:
    ranked = rank_sectors(scan_df)

    if ranked is None or ranked.empty:
        return {
            "top_sector": "Kein klarer Leader",
            "sector_count": 0,
            "top_score": None,
        }

    return {
        "top_sector": str(ranked.iloc[0]["Sektor"]),
        "sector_count": int(len(ranked)),
        "top_score": _round_or_none(ranked.iloc[0]["Sektor Score"]),
    }