from __future__ import annotations

import pandas as pd
import streamlit as st

from config import APP_NAME, APP_SUBTITLE
from universe_loader import get_available_universes, load_universe
from stock_scanner import scan_symbols, filter_top_candidates
from data_fetcher import enrich_with_live_prices
from market_analysis import analyze_market_regime, derive_risk_level, derive_action_signal
from sector_analysis import rank_sectors, get_top_sector_label
from portfolio_utils import analyze_portfolio


st.set_page_config(
    page_title=APP_NAME,
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
.main {
    background-color: #f3f5f8;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #141a2b 0%, #1b2337 100%);
}

section[data-testid="stSidebar"] * {
    color: white !important;
}

/* Selectbox lesbar */
section[data-testid="stSidebar"] div[data-baseweb="select"] {
    background: white !important;
    border-radius: 8px !important;
}

section[data-testid="stSidebar"] div[data-baseweb="select"] * {
    color: #0b1220 !important;
}

/* Checkbox / Slider */
section[data-testid="stSidebar"] .stCheckbox label,
section[data-testid="stSidebar"] .stCheckbox div {
    color: white !important;
}

section[data-testid="stSidebar"] .stSlider span {
    color: white !important;
}

/* Buttons */
section[data-testid="stSidebar"] button {
    color: #0b1220 !important;
    background-color: white !important;
    border: 1px solid #d0d7e2 !important;
    font-weight: 700 !important;
}

section[data-testid="stSidebar"] button p {
    color: #0b1220 !important;
}

/* Header */
.app-title {
    font-size: 2.6rem;
    font-weight: 800;
    color: #182033;
    margin-bottom: 0.1rem;
}

.app-subtitle {
    color: #667085;
    font-size: 0.9rem;
    margin-bottom: 1.2rem;
}

.app-note {
    color: #667085;
    font-size: 0.82rem;
    margin-top: -0.3rem;
    margin-bottom: 1rem;
}

/* Metrics */
.metric-card {
    background: linear-gradient(180deg, #02081c 0%, #020816 100%);
    border-radius: 14px;
    padding: 1rem;
    color: white;
    min-height: 88px;
}

.metric-label {
    color: #b9c0d4;
    font-size: 0.8rem;
}

.metric-value {
    font-size: 1.2rem;
    font-weight: 800;
}

/* Setup Cards */
.setup-card {
    background: linear-gradient(180deg, #010716 0%, #010818 100%);
    border-radius: 18px;
    padding: 1rem;
    color: white;
    min-height: 300px;
}

.setup-symbol {
    font-size: 2rem;
    font-weight: 800;
}

.setup-line {
    font-size: 0.92rem;
    margin-bottom: 3px;
}

.dot-row {
    display: flex;
    gap: 6px;
    margin-bottom: 8px;
}

.dot-green, .dot-yellow, .dot-red {
    width: 14px;
    height: 14px;
    border-radius: 50%;
    display: inline-block;
}

.dot-green { background: #19d60a; }
.dot-yellow { background: #f7e000; }
.dot-red { background: #ff3b30; }

.section-gap-small { height: 10px; }
.section-gap-medium { height: 22px; }
.section-gap-large { height: 34px; }

.soft-info {
    color: #667085;
    font-size: 0.82rem;
    margin-top: 0.25rem;
    margin-bottom: 0.6rem;
}

div[data-testid="stExpander"] {
    margin-top: 10px !important;
    margin-bottom: 12px !important;
}
</style>
""",
    unsafe_allow_html=True,
)


def fmt_value(value, decimals: int = 2, suffix: str = "") -> str:
    if value is None or pd.isna(value):
        return "-"
    return f"{value:.{decimals}f}{suffix}"


def get_dot_html(row: pd.Series) -> str:
    dots = []

    if bool(row.get("golden_cross", False)):
        dots.append('<span class="dot-green"></span>')

    score = row.get("trade_score", 0)
    try:
        score = float(score)
    except Exception:
        score = 0.0

    if score >= 80:
        dots.append('<span class="dot-green"></span>')
    elif score >= 65:
        dots.append('<span class="dot-yellow"></span>')
    else:
        dots.append('<span class="dot-red"></span>')

    return f'<div class="dot-row">{"".join(dots)}</div>'


def render_metric(label: str, value: str) -> None:
    st.markdown(
        f"""
<div class="metric-card">
    <div class="metric-label">{label}</div>
    <div class="metric-value">{value}</div>
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
<div class="setup-card">
    {get_dot_html(row)}
    <div class="setup-symbol">{row.get("symbol", "-")}</div>
    <div class="setup-line">{row.get("name", "-")}</div>
    <div class="setup-line"><b>WKN:</b> {row.get("wkn", "-")}</div>
    <div class="setup-line"><b>Signal:</b> {signal}</div>
    <div class="setup-line"><b>Trade Score:</b> {fmt_value(row.get("trade_score"), 0)}/100</div>
    <div class="setup-line"><b>{price_label}:</b> {price_value}</div>
    <div class="setup-line"><b>Analysepreis:</b> {fmt_value(analysis_price)}</div>
    <div class="setup-line"><b>Ziel:</b> {fmt_value(row.get("target_price"))}</div>
    <div class="setup-line"><b>Momentum:</b> {fmt_value(row.get("momentum"), 2, "%")}</div>
    <div class="setup-line"><b>Stop-Loss:</b> {fmt_value(row.get("stop_loss"))}</div>
    <div class="setup-line"><b>Quelle:</b> {source_text}</div>
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

    visible = df.head(n).copy()
    visible = enrich_with_live_prices(visible)
    return visible


def derive_breadth_from_scan(df: pd.DataFrame) -> dict:
    if df is None or df.empty:
        return {
            "count": 0,
            "pct_above_sma50": 0.0,
            "pct_golden_cross": 0.0,
        }

    temp = df.copy()

    if "analysis_price" not in temp.columns or "sma50" not in temp.columns:
        return {
            "count": len(temp),
            "pct_above_sma50": 0.0,
            "pct_golden_cross": 0.0,
        }

    temp["analysis_price"] = pd.to_numeric(temp["analysis_price"], errors="coerce")
    temp["sma50"] = pd.to_numeric(temp["sma50"], errors="coerce")
    valid = temp.dropna(subset=["analysis_price", "sma50"]).copy()

    if valid.empty:
        return {
            "count": len(temp),
            "pct_above_sma50": 0.0,
            "pct_golden_cross": 0.0,
        }

    above_sma50 = (valid["analysis_price"] > valid["sma50"]).mean() * 100.0

    pct_gc = 0.0
    if "golden_cross" in valid.columns:
        pct_gc = valid["golden_cross"].fillna(False).astype(bool).mean() * 100.0

    return {
        "count": len(valid),
        "pct_above_sma50": round(float(above_sma50), 2),
        "pct_golden_cross": round(float(pct_gc), 2),
    }


@st.cache_data(ttl=600, show_spinner=False)
def load_core_data(
    symbols_key: tuple[str, ...],
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    symbols = list(symbols_key)

    scan_df = scan_symbols(
        symbols,
        max_workers=8,
        fetch_live_prices=False,
    )

    rohstoffe = load_universe("Rohstoffe")
    rohstoffe_df = scan_symbols(
        rohstoffe,
        max_workers=5,
        fetch_live_prices=False,
    )

    market = analyze_market_regime()

    return scan_df, rohstoffe_df, market


@st.cache_data(ttl=300, show_spinner=False)
def load_portfolio_data(enabled: bool) -> pd.DataFrame:
    if not enabled:
        return pd.DataFrame()
    return analyze_portfolio()


def get_marketchart_view(df: pd.DataFrame, add_live_prices: bool) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    result = df.copy()

    if add_live_prices:
        # Nur die ersten 40 Zeilen mit Live-Daten anreichern, um die UI flott zu halten
        top_part = result.head(40).copy()
        rest_part = result.iloc[40:].copy()

        top_part = enrich_with_live_prices(top_part)
        result = pd.concat([top_part, rest_part], ignore_index=True)

    preview_cols = [
        "symbol",
        "name",
        "sector",
        "status",
        "analysis_price",
        "market_price",
        "price_gap_pct",
        "market_price_source",
        "momentum",
        "relative_strength",
        "golden_cross",
        "trade_score",
        "target_price",
        "stop_loss",
        "signal",
    ]
    show = [c for c in preview_cols if c in result.columns]
    return result[show]


with st.sidebar:
    st.markdown("## Steuerung")

    refresh = st.button("🔄 Aktualisieren", use_container_width=True)

    universe_name = st.selectbox(
        "Aktienuniversum auswählen",
        get_available_universes(),
        index=0,
    )

    include_europe_listings = st.checkbox(
        "Europa Listings einbeziehen",
        value=True,
    )

    load_portfolio_monitor = st.checkbox(
        "Portfolio Monitor laden",
        value=False,
    )

    add_live_prices_to_markettable = st.checkbox(
        "Live-Kurse in Marktcharts",
        value=False,
    )

    top_n = st.selectbox(
        "Anzahl Top-Trades",
        [3, 5, 10],
        index=0,
    )

    min_trade_score = st.slider(
        "Mindest-Trade-Score",
        0,
        100,
        60,
    )

    st.caption("Live-Kurse und Analysepreise werden getrennt verarbeitet.")

if refresh:
    st.cache_data.clear()

st.markdown(f'<div class="app-title">{APP_NAME}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="app-subtitle">{APP_SUBTITLE}</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="app-note">Ultra-Version: Historie wird schnell gescannt, Live-Kurse werden nur gezielt nachgeladen.</div>',
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
        portfolio_df = load_portfolio_data(load_portfolio_monitor)

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
        f'<div class="soft-info">Geladene Aktien im Scanner: {len(valid_scan_df)} | Rohstoffe: {len(valid_rohstoffe_df)} | Europa Listings: {"an" if include_europe_listings else "aus"}</div>',
        unsafe_allow_html=True,
    )

    st.header(f"Top {top_n} Trading Setups")

    cols = st.columns(top_n)
    for i in range(top_n):
        with cols[i]:
            if i < len(top_trading_live):
                render_setup_card(top_trading_live.iloc[i])

    if top_trading_live.empty:
        st.warning("Für das gewählte Universum wurden aktuell keine gültigen Trading-Setups gefunden.")

    st.markdown('<div class="section-gap-medium"></div>', unsafe_allow_html=True)

    st.header(f"Top {top_n} Rohstoff Setups")

    cols = st.columns(top_n)
    for i in range(top_n):
        with cols[i]:
            if i < len(top_rohstoffe_live):
                render_setup_card(top_rohstoffe_live.iloc[i])

    if top_rohstoffe_live.empty:
        st.warning("Aktuell wurden keine gültigen Rohstoff-Setups gefunden.")

    st.markdown('<div class="section-gap-large"></div>', unsafe_allow_html=True)

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
            if add_live_prices_to_markettable:
                st.caption("Live-Kurse werden aus Performance-Gründen nur für die ersten 40 Zeilen nachgeladen.")
            else:
                st.caption("Marktcharts zeigen standardmäßig nur Analysepreise. Live-Kurse kannst du links optional zuschalten.")
            st.dataframe(marketchart_df, use_container_width=True, hide_index=True)

    st.markdown('<div class="section-gap-small"></div>', unsafe_allow_html=True)

    st.header("Portfolio Monitor")

    if not load_portfolio_monitor:
        st.info("Portfolio Monitor ist deaktiviert. Aktiviere ihn links in der Sidebar, wenn du ihn laden möchtest.")
    elif portfolio_df.empty:
        st.info("Kein Portfolio gefunden. Lege optional eine Datei unter data/portfolio.csv an.")
    else:
        st.dataframe(portfolio_df, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Fehler beim Laden der App: {e}")
    st.exception(e)