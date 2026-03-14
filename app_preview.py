from __future__ import annotations

import math
from datetime import datetime, timezone

import matplotlib.pyplot as plt
from matplotlib.patches import Wedge, Circle
import pandas as pd
import requests
import streamlit as st

from config import APP_SUBTITLE
from universe_loader import get_available_universes, load_universe
from stock_scanner import scan_symbols, filter_top_candidates
from data_fetcher import enrich_with_live_prices
from market_analysis import analyze_market_regime, derive_risk_level, derive_action_signal
from sector_analysis import rank_sectors, get_top_sector_label


st.set_page_config(
    page_title="Trading Scanner preview",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
:root {
    --space-block: 24px;
    --space-card: 14px;
    --radius-card: 18px;
    --card-dark-bg: linear-gradient(180deg, #071225 0%, #0b1730 100%);
    --card-dark-text: #ffffff;
    --card-dark-soft: #c9d4e5;
}

.block-container {
    padding-top: 1rem;
    padding-bottom: 2rem;
}

.section-gap {
    height: var(--space-block);
}

.app-title {
    font-size: clamp(2rem, 4vw, 3rem);
    font-weight: 800;
    line-height: 1.05;
    margin-bottom: 0.25rem;
}

.app-subtitle {
    font-size: 1rem;
    opacity: 0.85;
    margin-bottom: 0.35rem;
}

.app-note {
    font-size: 0.9rem;
    opacity: 0.8;
    margin-bottom: var(--space-block);
    max-width: 900px;
}

section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] .stCaption,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] div {
    line-height: 1.35 !important;
}

section[data-testid="stSidebar"] .stCheckbox,
section[data-testid="stSidebar"] .stSelectbox,
section[data-testid="stSidebar"] .stSlider {
    margin-bottom: 0.45rem !important;
}

.ts-card-dark {
    background: var(--card-dark-bg);
    color: var(--card-dark-text);
    border-radius: var(--radius-card);
    padding: 1rem;
    box-shadow: 0 6px 18px rgba(7, 18, 37, 0.14);
    margin-bottom: var(--space-card);
}

.ts-metric-card {
    min-height: 96px;
}

.ts-metric-label {
    color: var(--card-dark-soft);
    font-size: 0.8rem;
    margin-bottom: 0.2rem;
}

.ts-metric-value {
    font-size: 1.22rem;
    font-weight: 800;
}

.ts-setup-card {
    min-height: 250px;
}

.ts-setup-symbol {
    font-size: 1.7rem;
    font-weight: 800;
    line-height: 1.1;
    margin-bottom: 0.2rem;
}

.ts-line {
    font-size: 0.92rem;
    line-height: 1.35;
    margin-bottom: 0.12rem;
    color: #f3f6fb;
}

.ts-dot-row {
    display: flex;
    gap: 6px;
    margin-bottom: 10px;
}

.ts-dot-green,
.ts-dot-yellow,
.ts-dot-red {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    display: inline-block;
}

.ts-dot-green { background: #18c964; }
.ts-dot-yellow { background: #f5c451; }
.ts-dot-red { background: #ef5350; }

.ts-info-inline {
    font-size: 0.9rem;
    opacity: 0.78;
    margin-top: 0.35rem;
}

.ts-fg-shell {
    border: 1px solid rgba(120, 130, 150, 0.18);
    border-radius: var(--radius-card);
    padding: 1rem;
    background: rgba(255,255,255,0.03);
}

.ts-fg-title {
    font-size: 1.35rem;
    font-weight: 800;
    margin-bottom: 0.25rem;
}

.ts-fg-sub {
    font-size: 0.88rem;
    opacity: 0.78;
    margin-bottom: 0.85rem;
}

[data-testid="stDataFrame"] {
    border-radius: 14px;
    overflow: hidden;
}

@media (max-width: 900px) {
    :root {
        --space-block: 20px;
        --space-card: 16px;
    }

    .block-container {
        padding-top: 0.9rem;
        padding-left: 0.9rem;
        padding-right: 0.9rem;
    }

    .app-title {
        font-size: 1.95rem;
    }

    .app-subtitle {
        font-size: 0.98rem;
        line-height: 1.4;
    }

    .app-note {
        font-size: 0.92rem;
        line-height: 1.55;
    }

    .ts-card-dark,
    .ts-fg-shell {
        padding: 0.9rem;
    }

    .ts-metric-card,
    .ts-setup-card {
        min-height: auto;
        margin-bottom: var(--space-card);
    }

    .ts-setup-symbol {
        font-size: 1.45rem;
    }

    .ts-line {
        font-size: 0.9rem;
        line-height: 1.45;
    }

    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stCaption,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] div {
        font-size: 0.92rem !important;
    }
}
</style>
""",
    unsafe_allow_html=True,
)


def fmt_value(value, decimals: int = 2, suffix: str = "") -> str:
    if value is None or pd.isna(value):
        return "-"
    return f"{float(value):.{decimals}f}{suffix}"


def get_dot_html(row: pd.Series) -> str:
    dots = []

    if bool(row.get("golden_cross", False)):
        dots.append('<span class="ts-dot-green"></span>')

    try:
        score = float(row.get("trade_score", 0))
    except Exception:
        score = 0.0

    if score >= 80:
        dots.append('<span class="ts-dot-green"></span>')
    elif score >= 65:
        dots.append('<span class="ts-dot-yellow"></span>')
    else:
        dots.append('<span class="ts-dot-red"></span>')

    return f'<div class="ts-dot-row">{"".join(dots)}</div>'


def render_metric(label: str, value: str) -> None:
    st.markdown(
        f"""
<div class="ts-card-dark ts-metric-card">
    <div class="ts-metric-label">{label}</div>
    <div class="ts-metric-value">{value}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_setup_card(row: pd.Series) -> None:
    market_price = row.get("market_price")
    analysis_price = row.get("analysis_price")
    source = row.get("market_price_source")
    signal = row.get("signal", "-")

    if market_price is not None and not pd.isna(market_price):
        price_label = "Aktuell"
        price_value = fmt_value(market_price)
    else:
        price_label = "Analysepreis"
        price_value = fmt_value(analysis_price)

    source_text = source if source not in [None, ""] else "-"

    st.markdown(
        f"""
<div class="ts-card-dark ts-setup-card">
    {get_dot_html(row)}
    <div class="ts-setup-symbol">{row.get("symbol", "-")}</div>
    <div class="ts-line">{row.get("name", "-")}</div>
    <div class="ts-line"><b>Signal:</b> {signal}</div>
    <div class="ts-line"><b>Score:</b> {fmt_value(row.get("trade_score"), 0)}/100</div>
    <div class="ts-line"><b>{price_label}:</b> {price_value}</div>
    <div class="ts-line"><b>Ziel:</b> {fmt_value(row.get("target_price"))}</div>
    <div class="ts-line"><b>Momentum:</b> {fmt_value(row.get("momentum"), 2, "%")}</div>
    <div class="ts-line"><b>Stop:</b> {fmt_value(row.get("stop_loss"))}</div>
    <div class="ts-line"><b>Quelle:</b> {source_text}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def get_valid_rows(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    result = df.copy()
    if "status" in result.columns:
        result = result[result["status"] == "ok"]
    if "trade_score" in result.columns:
        result["trade_score"] = pd.to_numeric(result["trade_score"], errors="coerce")
        result = result.dropna(subset=["trade_score"])
    return result.reset_index(drop=True)


def prepare_visible_cards(df: pd.DataFrame, n: int) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    return enrich_with_live_prices(df.head(n).copy())


def derive_breadth_from_scan(df: pd.DataFrame) -> dict:
    if df is None or df.empty:
        return {"count": 0, "pct_above_sma50": 0.0, "pct_golden_cross": 0.0}

    temp = df.copy()
    if "analysis_price" not in temp.columns or "sma50" not in temp.columns:
        return {"count": len(temp), "pct_above_sma50": 0.0, "pct_golden_cross": 0.0}

    temp["analysis_price"] = pd.to_numeric(temp["analysis_price"], errors="coerce")
    temp["sma50"] = pd.to_numeric(temp["sma50"], errors="coerce")
    valid = temp.dropna(subset=["analysis_price", "sma50"]).copy()

    if valid.empty:
        return {"count": len(temp), "pct_above_sma50": 0.0, "pct_golden_cross": 0.0}

    above_sma50 = (valid["analysis_price"] > valid["sma50"]).mean() * 100.0
    pct_gc = 0.0
    if "golden_cross" in valid.columns:
        pct_gc = valid["golden_cross"].fillna(False).astype(bool).mean() * 100.0

    return {
        "count": len(valid),
        "pct_above_sma50": round(float(above_sma50), 2),
        "pct_golden_cross": round(float(pct_gc), 2),
    }


def _fg_label_from_value(value: float | int | None) -> str:
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


def _fg_color(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "#9ca3af"
    value = float(value)
    if value < 25:
        return "#d64545"
    if value < 45:
        return "#f08a24"
    if value < 55:
        return "#9ca3af"
    if value < 75:
        return "#84cc16"
    return "#22c55e"


def _fg_value_text(entry) -> str:
    if isinstance(entry, dict):
        v = entry.get("score", entry.get("value"))
        t = entry.get("rating", entry.get("valueText"))
        if v is None:
            return "-"
        if t:
            return f"{int(round(float(v)))} · {t}"
        return str(int(round(float(v))))
    if entry is None or pd.isna(entry):
        return "-"
    return str(entry)


@st.cache_data(ttl=900, show_spinner=False)
def load_fear_greed_data() -> dict:
    url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json,text/plain,*/*",
        "Referer": "https://money.cnn.com/data/fear-and-greed/",
    }

    try:
        response = requests.get(url, headers=headers, timeout=12)
        response.raise_for_status()
        data = response.json()
    except Exception:
        return {
            "ok": False,
            "value": None,
            "rating": None,
            "previous_close": None,
            "previous_1_week": None,
            "previous_1_month": None,
            "previous_1_year": None,
            "timestamp": None,
        }

    current = data.get("fear_and_greed", {}) or {}

    def _extract_item(item):
        if isinstance(item, dict):
            return {
                "score": item.get("score", item.get("value")),
                "rating": item.get("rating", item.get("valueText")),
            }
        if item is None:
            return None
        return {"score": item, "rating": None}

    timestamp = current.get("timestamp")
    timestamp_text = None
    if timestamp:
        try:
            timestamp_text = datetime.fromtimestamp(
                float(timestamp) / 1000.0,
                tz=timezone.utc,
            ).strftime("%d.%m.%Y %H:%M UTC")
        except Exception:
            timestamp_text = None

    value = current.get("score", current.get("value"))
    rating = current.get("rating", current.get("valueText"))
    if value is not None and not rating:
        rating = _fg_label_from_value(value)

    return {
        "ok": True,
        "value": value,
        "rating": rating,
        "previous_close": _extract_item(current.get("previous_close")),
        "previous_1_week": _extract_item(current.get("previous_1_week")),
        "previous_1_month": _extract_item(current.get("previous_1_month")),
        "previous_1_year": _extract_item(current.get("previous_1_year")),
        "timestamp": timestamp_text,
    }


def build_fear_greed_gauge(value: float | int | None):
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    ax.set_aspect("equal")
    ax.axis("off")

    center = (0, 0)
    outer_r = 1.0
    width = 0.38

    segments = [
        (180, 144, "#d64545", "EXTREME\nFEAR"),
        (144, 108, "#f08a24", "FEAR"),
        (108, 72, "#9ca3af", "NEUTRAL"),
        (72, 36, "#84cc16", "GREED"),
        (36, 0, "#22c55e", "EXTREME\nGREED"),
    ]

    for theta1, theta2, color, label in segments:
        wedge = Wedge(center, outer_r, theta2, theta1, width=width, facecolor=color, edgecolor="white", lw=2)
        ax.add_patch(wedge)

        angle = math.radians((theta1 + theta2) / 2.0)
        r_text = outer_r - width / 2
        x = r_text * math.cos(angle)
        y = r_text * math.sin(angle)
        ax.text(
            x,
            y,
            label,
            ha="center",
            va="center",
            fontsize=10,
            fontweight="bold",
            rotation=((theta1 + theta2) / 2.0) - 90,
            rotation_mode="anchor",
        )

    for v in [0, 25, 50, 75, 100]:
        angle = math.radians(180 - (v / 100) * 180)
        r = outer_r - width - 0.05
        x = r * math.cos(angle)
        y = r * math.sin(angle)
        ax.text(x, y, str(v), ha="center", va="center", fontsize=9, color="#6b7280")

    if value is not None and not pd.isna(value):
        value = max(0, min(100, float(value)))
        angle = math.radians(180 - (value / 100) * 180)
        needle_r = outer_r - 0.08
        x = needle_r * math.cos(angle)
        y = needle_r * math.sin(angle)
        ax.plot([0, x], [0, y], lw=4, color="#1f2937", solid_capstyle="round")
        ax.add_patch(Circle((0, 0), 0.08, color="#1f2937"))
        ax.add_patch(Circle((0, 0), 0.18, color="white", zorder=3))
        ax.text(0, 0.05, f"{int(round(value))}", ha="center", va="center", fontsize=20, fontweight="bold")
        ax.text(0, -0.12, _fg_label_from_value(value), ha="center", va="center", fontsize=10, color=_fg_color(value), fontweight="bold")
    else:
        ax.add_patch(Circle((0, 0), 0.18, color="white", zorder=3))
        ax.text(0, 0.0, "-", ha="center", va="center", fontsize=20, fontweight="bold")

    ax.set_xlim(-1.1, 1.1)
    ax.set_ylim(-0.2, 1.1)
    fig.tight_layout()
    return fig


def render_fear_greed_section(fg: dict) -> None:
    st.markdown('<div class="ts-fg-shell">', unsafe_allow_html=True)
    st.markdown('<div class="ts-fg-title">Fear & Greed Index</div>', unsafe_allow_html=True)

    ts = fg.get("timestamp")
    if ts:
        st.markdown(f'<div class="ts-fg-sub">Letztes Update: {ts}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="ts-fg-sub">Sentiment-Indikator für den US-Aktienmarkt.</div>', unsafe_allow_html=True)

    if not fg.get("ok") or fg.get("value") is None:
        st.warning("Fear & Greed Index konnte aktuell nicht geladen werden.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    left, right = st.columns([1.8, 1.0])

    with left:
        fig = build_fear_greed_gauge(fg.get("value"))
        st.pyplot(fig, use_container_width=True)

    with right:
        st.metric("Aktuell", _fg_value_text({"score": fg.get("value"), "rating": fg.get("rating")}))
        st.metric("Previous Close", _fg_value_text(fg.get("previous_close")))
        st.metric("1 Woche", _fg_value_text(fg.get("previous_1_week")))
        st.metric("1 Monat", _fg_value_text(fg.get("previous_1_month")))
        st.metric("1 Jahr", _fg_value_text(fg.get("previous_1_year")))

    st.markdown('</div>', unsafe_allow_html=True)


@st.cache_data(ttl=600, show_spinner=False)
def load_core_data(symbols_key: tuple[str, ...]) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    symbols = list(symbols_key)
    scan_df = scan_symbols(symbols, max_workers=8, fetch_live_prices=False)

    rohstoffe = load_universe("Rohstoffe")
    rohstoffe_df = scan_symbols(rohstoffe, max_workers=5, fetch_live_prices=False)

    market = analyze_market_regime()
    return scan_df, rohstoffe_df, market


def get_marketchart_view(df: pd.DataFrame, add_live_prices: bool) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    result = df.copy()
    if add_live_prices:
        top_part = result.head(40).copy()
        rest_part = result.iloc[40:].copy()
        top_part = enrich_with_live_prices(top_part)
        result = pd.concat([top_part, rest_part], ignore_index=True)

    preview_cols = [
        "symbol", "name", "sector", "status", "analysis_price", "market_price",
        "price_gap_pct", "market_price_source", "momentum", "relative_strength",
        "golden_cross", "trade_score", "target_price", "stop_loss", "signal",
    ]
    show = [c for c in preview_cols if c in result.columns]
    return result[show]


with st.sidebar:
    st.markdown("## Steuerung")

    refresh = st.button("🔄 Aktualisieren", use_container_width=True)

    universe_name = st.selectbox("Aktienuniversum", get_available_universes(), index=0)
    include_europe_listings = st.checkbox("Europa Listings", value=True)
    add_live_prices_to_markettable = st.checkbox("Live-Kurse", value=False)
    top_n = st.selectbox("Top-Trades", [3, 5, 10], index=0)
    min_trade_score = st.slider("Mindest-Score", 0, 100, 60)

if refresh:
    st.cache_data.clear()

st.markdown('<div class="app-title">Trading Scanner preview</div>', unsafe_allow_html=True)
st.markdown(f'<div class="app-subtitle">{APP_SUBTITLE}</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="app-note">Diese Vorversion zeigt nur den Markt-Scanner und keine Portfolio-Daten.</div>',
    unsafe_allow_html=True,
)

try:
    symbols = load_universe(
        universe_name,
        include_europe_listings=include_europe_listings,
        include_commodities_in_all=False,
    )

    with st.spinner("Scanner lädt Marktdaten..."):
        scan_df, rohstoffe_df, market = load_core_data(tuple(symbols))
        fg_data = load_fear_greed_data()
        valid_scan_df = get_valid_rows(scan_df)
        valid_rohstoffe_df = get_valid_rows(rohstoffe_df)
        breadth = derive_breadth_from_scan(valid_scan_df)
        sector_df = rank_sectors(valid_scan_df)

    top_trading = filter_top_candidates(valid_scan_df, min_trade_score).head(top_n)
    top_rohstoffe = filter_top_candidates(valid_rohstoffe_df, min_trade_score).head(top_n)

    top_trading_live = prepare_visible_cards(top_trading, top_n)
    top_rohstoffe_live = prepare_visible_cards(top_rohstoffe, top_n)

    market_status = market.get("market_regime", "Neutral")
    risk_level = derive_risk_level(breadth)
    top_sector = get_top_sector_label(valid_scan_df)
    action_signal = derive_action_signal(market_status, breadth)

    render_fear_greed_section(fg_data)
    st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)

    st.header("Marktübersicht")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_metric("Marktstatus", market_status)
    with c2:
        render_metric("Risiko", risk_level)
    with c3:
        render_metric("Top Sektor", top_sector)
    with c4:
        render_metric("Aktivsignal", action_signal)

    st.markdown(
        f'<div class="ts-info-inline">Geladene Aktien im Scanner: {len(valid_scan_df)} | Rohstoffe: {len(valid_rohstoffe_df)}</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)

    st.header(f"Top {top_n} Trading Setups")
    cols = st.columns(top_n)
    for i in range(top_n):
        with cols[i]:
            if i < len(top_trading_live):
                render_setup_card(top_trading_live.iloc[i])

    st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)

    st.header(f"Top {top_n} Rohstoff Setups")
    cols = st.columns(top_n)
    for i in range(top_n):
        with cols[i]:
            if i < len(top_rohstoffe_live):
                render_setup_card(top_rohstoffe_live.iloc[i])

    st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)

    with st.expander("Sektor Ranking anzeigen"):
        if sector_df.empty:
            st.info("Keine gültigen Sektordaten verfügbar.")
        else:
            st.dataframe(sector_df, use_container_width=True, hide_index=True)

    with st.expander("Marktcharts anzeigen"):
        marketchart_df = get_marketchart_view(scan_df, add_live_prices_to_markettable)
        if marketchart_df.empty:
            st.info("Keine Marktdaten verfügbar.")
        else:
            st.dataframe(marketchart_df, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Fehler beim Laden der App: {e}")
    st.exception(e)