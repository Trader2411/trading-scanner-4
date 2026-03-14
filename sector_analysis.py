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


def _clamp(value: float, lower: float = 0.0, upper: float = 100.0) -> float:
    return max(lower, min(upper, float(value)))


def _normalize_linear(value, low: float, high: float) -> Optional[float]:
    try:
        if value is None or pd.isna(value):
            return None
        value = float(value)
        if high == low:
            return None
        scaled = ((value - low) / (high - low)) * 100.0
        return _clamp(scaled, 0.0, 100.0)
    except Exception:
        return None


def _safe_mean(series: pd.Series) -> Optional[float]:
    try:
        if series is None or len(series) == 0:
            return None
        value = pd.to_numeric(series, errors="coerce").dropna().mean()
        if pd.isna(value):
            return None
        return float(value)
    except Exception:
        return None


def _safe_bool_mean(series: pd.Series) -> float:
    try:
        if series is None or len(series) == 0:
            return 0.0
        return float(series.fillna(False).astype(bool).mean()) * 100.0
    except Exception:
        return 0.0


def _sector_fg_label(value) -> str:
    try:
        if value is None or pd.isna(value):
            return "-"
        value = float(value)
        if value < 25:
            return "Extreme Fear"
        if value < 45:
            return "Fear"
        if value < 55:
            return "Neutral"
        if value < 75:
            return "Greed"
        return "Extreme Greed"
    except Exception:
        return "-"


# ============================================================
# Sector Fear & Greed Ableitung
# ============================================================

def _derive_sector_fear_greed_from_row(row: pd.Series) -> Optional[float]:
    """
    Konträre Sentiment-Ableitung auf Sektorebene.

    Ziel:
    - niedriger Wert = Fear / potenziell Bodenbildung
    - hoher Wert     = Greed / eher heiß gelaufen

    Die Ableitung basiert auf:
    - Ø Momentum
    - Ø Relative Stärke
    - Golden Cross %
    - Über SMA50 %
    - Abstand zum 52W Hoch
    - RSI
    - Trendkanal
    - Volatilität
    """
    try:
        momentum = row.get("Ø Momentum")
        rs = row.get("Ø Relative Stärke")
        gc = row.get("Golden Cross %")
        above_sma50 = row.get("Über SMA50 %")
        dist_high = row.get("Ø Distanz 52W Hoch %")
        rsi = row.get("Ø RSI")
        trend_channel = row.get("Ø Trendkanal %")
        vol = row.get("Ø Volatilität %")

        momentum_score = _normalize_linear(momentum, -12.0, 25.0)
        rs_score = _normalize_linear(rs, 20.0, 90.0)
        gc_score = _normalize_linear(gc, 0.0, 100.0)
        sma50_score = _normalize_linear(above_sma50, 0.0, 100.0)
        dist_score = _normalize_linear(dist_high, -35.0, 0.0)
        trend_channel_score = _normalize_linear(trend_channel, 0.0, 100.0)

        rsi_score = None
        if rsi is not None and not pd.isna(rsi):
            rsi = float(rsi)
            if rsi < 25:
                rsi_score = 20.0
            elif rsi < 35:
                rsi_score = 35.0
            elif rsi <= 55:
                rsi_score = 55.0
            elif rsi <= 70:
                rsi_score = 75.0
            else:
                rsi_score = 90.0

        vol_score = None
        if vol is not None and not pd.isna(vol):
            vol = float(vol)
            if vol < 12:
                vol_score = 45.0
            elif vol < 22:
                vol_score = 55.0
            elif vol < 35:
                vol_score = 65.0
            else:
                vol_score = 75.0

        pieces = []
        weights = []

        def add_piece(score, weight):
            if score is None:
                return
            pieces.append(float(score) * float(weight))
            weights.append(float(weight))

        add_piece(momentum_score, 0.22)
        add_piece(rs_score, 0.18)
        add_piece(gc_score, 0.12)
        add_piece(sma50_score, 0.12)
        add_piece(dist_score, 0.14)
        add_piece(rsi_score, 0.10)
        add_piece(trend_channel_score, 0.07)
        add_piece(vol_score, 0.05)

        if not weights:
            return None

        hotness = sum(pieces) / sum(weights)
        sector_fg = 100.0 - hotness
        return _clamp(sector_fg, 0.0, 100.0)

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
    - rsi
    - volatility_pct
    - trend_channel_position_pct
    - distance_to_52w_high_pct
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
        "rsi",
        "volatility_pct",
        "trend_channel_position_pct",
        "distance_to_52w_high_pct",
        "score_momentum",
        "score_relative_strength",
        "score_trend_strength",
        "score_rsi",
        "score_macd",
        "score_bollinger",
        "score_ichimoku",
        "score_volume",
        "score_valuation",
        "score_earnings_growth",
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

    # optionale neue Felder
    optional_mean_map = {
        "rsi": "durchschnitt_rsi",
        "volatility_pct": "durchschnitt_volatilitaet",
        "trend_channel_position_pct": "durchschnitt_trendkanal",
        "distance_to_52w_high_pct": "durchschnitt_distanz_52w_hoch",
        "score_momentum": "durchschnitt_score_momentum",
        "score_relative_strength": "durchschnitt_score_relative_strength",
        "score_trend_strength": "durchschnitt_score_trend",
        "score_rsi": "durchschnitt_score_rsi",
        "score_macd": "durchschnitt_score_macd",
        "score_bollinger": "durchschnitt_score_bollinger",
        "score_ichimoku": "durchschnitt_score_ichimoku",
        "score_volume": "durchschnitt_score_volume",
        "score_valuation": "durchschnitt_score_valuation",
        "score_earnings_growth": "durchschnitt_score_earnings_growth",
    }

    for source_col, target_col in optional_mean_map.items():
        if source_col in df.columns:
            extra = grouped[source_col].mean().reset_index(name=target_col)
            summary = summary.merge(extra, on="sector", how="left")

    summary = summary[summary["anzahl_aktien"] >= int(min_stocks_per_sector)].copy()

    if summary.empty:
        return pd.DataFrame()

    summary["anteil_golden_cross"] = summary["anteil_golden_cross"] * 100.0
    summary["anteil_ueber_sma50"] = summary["anteil_ueber_sma50"] * 100.0

    # klassische Sektorwertung
    momentum_norm = summary["durchschnitt_momentum"].fillna(0).clip(lower=-10, upper=25).add(10).div(35).mul(100)
    rs_norm = summary["durchschnitt_relative_strength"].fillna(0).clip(lower=0, upper=100)
    trade_score_norm = summary["durchschnitt_trade_score"].fillna(0).clip(lower=0, upper=100)

    base_sector_score = (
        trade_score_norm * 0.34
        + momentum_norm * 0.16
        + rs_norm * 0.14
        + summary["anteil_golden_cross"].fillna(0) * 0.10
        + summary["anteil_ueber_sma50"].fillna(0) * 0.10
    )

    # neue Scoreblöcke, falls vorhanden
    optional_component_score = 0.0
    optional_weight_sum = 0.0

    optional_weights = {
        "durchschnitt_score_rsi": 0.04,
        "durchschnitt_score_macd": 0.04,
        "durchschnitt_score_bollinger": 0.03,
        "durchschnitt_score_ichimoku": 0.04,
        "durchschnitt_score_volume": 0.03,
        "durchschnitt_score_valuation": 0.01,
        "durchschnitt_score_earnings_growth": 0.01,
    }

    for col, weight in optional_weights.items():
        if col in summary.columns:
            optional_component_score = optional_component_score + summary[col].fillna(0) * weight
            optional_weight_sum += weight

    if optional_weight_sum > 0:
        # Basisteil bewusst auf 0.90 normiert, Rest sind neue Komponenten
        summary["sektor_score"] = (base_sector_score * 0.90) + optional_component_score
    else:
        summary["sektor_score"] = base_sector_score

    summary["sektor_score"] = summary["sektor_score"].clip(lower=0, upper=100)

    # Sector Fear & Greed aus Sektorverfassung ableiten
    summary = summary.rename(
        columns={
            "sector": "Sektor",
            "anzahl_aktien": "Anzahl Aktien",
            "durchschnitt_trade_score": "Ø Trade Score",
            "durchschnitt_momentum": "Ø Momentum",
            "durchschnitt_relative_strength": "Ø Relative Stärke",
            "anteil_golden_cross": "Golden Cross %",
            "anteil_ueber_sma50": "Über SMA50 %",
            "durchschnitt_rsi": "Ø RSI",
            "durchschnitt_volatilitaet": "Ø Volatilität %",
            "durchschnitt_trendkanal": "Ø Trendkanal %",
            "durchschnitt_distanz_52w_hoch": "Ø Distanz 52W Hoch %",
            "sektor_score": "Sektor Score",
        }
    )

    summary["Sector Fear & Greed"] = summary.apply(_derive_sector_fear_greed_from_row, axis=1)
    summary["Sector Sentiment"] = summary["Sector Fear & Greed"].apply(_sector_fg_label)

    display_order = [
        "Sektor",
        "Anzahl Aktien",
        "Ø Trade Score",
        "Ø Momentum",
        "Ø Relative Stärke",
        "Golden Cross %",
        "Über SMA50 %",
        "Ø RSI",
        "Ø Volatilität %",
        "Ø Trendkanal %",
        "Ø Distanz 52W Hoch %",
        "Sector Fear & Greed",
        "Sector Sentiment",
        "Sektor Score",
    ]

    for col in display_order:
        if col not in summary.columns:
            summary[col] = None

    for col in [
        "Ø Trade Score",
        "Ø Momentum",
        "Ø Relative Stärke",
        "Golden Cross %",
        "Über SMA50 %",
        "Ø RSI",
        "Ø Volatilität %",
        "Ø Trendkanal %",
        "Ø Distanz 52W Hoch %",
        "Sector Fear & Greed",
        "Sektor Score",
    ]:
        summary[col] = summary[col].apply(_round_or_none)

    summary = summary[display_order].copy()

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
        sector = str(ranked.iloc[0]["Sektor"])
        fg = ranked.iloc[0].get("Sector Fear & Greed")
        if fg is None or pd.isna(fg):
            return sector
        return f"{sector} (FG {int(round(float(fg)))})"
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
            "top_sector_fear_greed": None,
        }

    return {
        "top_sector": str(ranked.iloc[0]["Sektor"]),
        "sector_count": int(len(ranked)),
        "top_score": _round_or_none(ranked.iloc[0]["Sektor Score"]),
        "top_sector_fear_greed": _round_or_none(ranked.iloc[0].get("Sector Fear & Greed")),
    }