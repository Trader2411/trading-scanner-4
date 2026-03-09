from __future__ import annotations

import pandas as pd


def rank_sectors(df: pd.DataFrame) -> pd.DataFrame:
    """
    Berechnet ein Sektor-Ranking auf Basis von:
    - durchschnittlichem Trade Score
    - durchschnittlichem Momentum
    - durchschnittlicher Relative Strength
    - Anteil Golden Cross in %
    """

    if df is None or df.empty:
        return pd.DataFrame()

    df = df.copy()

    if "sector" not in df.columns:
        return pd.DataFrame()

    # Spalten robust absichern
    if "golden_cross" not in df.columns:
        df["golden_cross"] = False
    else:
        df["golden_cross"] = df["golden_cross"].fillna(False).astype(bool)

    if "momentum" not in df.columns:
        df["momentum"] = 0.0
    else:
        df["momentum"] = pd.to_numeric(df["momentum"], errors="coerce").fillna(0.0)

    if "relative_strength" not in df.columns:
        df["relative_strength"] = 0.0
    else:
        df["relative_strength"] = pd.to_numeric(df["relative_strength"], errors="coerce").fillna(0.0)

    if "trade_score" not in df.columns:
        df["trade_score"] = 0.0
    else:
        df["trade_score"] = pd.to_numeric(df["trade_score"], errors="coerce").fillna(0.0)

    if "symbol" not in df.columns:
        df["symbol"] = ""

    grouped = (
        df.groupby("sector", dropna=False)
        .agg(
            count=("symbol", "count"),
            avg_trade_score=("trade_score", "mean"),
            avg_momentum=("momentum", "mean"),
            avg_relative_strength=("relative_strength", "mean"),
            pct_golden_cross=("golden_cross", "mean"),
        )
        .reset_index()
    )

    # mean(bool) ergibt 0..1 -> in Prozent umrechnen
    grouped["pct_golden_cross"] = grouped["pct_golden_cross"] * 100.0

    grouped["avg_trade_score"] = grouped["avg_trade_score"].round(2)
    grouped["avg_momentum"] = grouped["avg_momentum"].round(2)
    grouped["avg_relative_strength"] = grouped["avg_relative_strength"].round(2)
    grouped["pct_golden_cross"] = grouped["pct_golden_cross"].round(2)

    grouped = grouped.sort_values(
        "avg_trade_score",
        ascending=False,
        na_position="last",
    ).reset_index(drop=True)

    return grouped


def get_top_sector_label(df: pd.DataFrame) -> str:
    """
    Gibt das Label für den Top-Sektor zurück, z.B.:
    'Industrie (4/4)'
    """

    sectors_df = rank_sectors(df)

    if sectors_df.empty:
        return "Keine Daten"

    top = sectors_df.iloc[0]

    pct_gc = top.get("pct_golden_cross", 0)
    try:
        pct_gc = float(pct_gc)
    except Exception:
        pct_gc = 0.0

    strength = int(round((pct_gc / 100.0) * 4))
    strength = max(0, min(4, strength))

    sector_name = top.get("sector", "Unbekannt")
    return f"{sector_name} ({strength}/4)"