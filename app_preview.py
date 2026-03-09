from __future__ import annotations

import pandas as pd
import streamlit as st

from config import APP_NAME, APP_SUBTITLE
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
    --bg-main: #f4f6f9;
    --bg-card-dark: linear-gradient(180deg, #071225 0%, #0b1730 100%);
    --text-main: #182033;
    --text-soft: #667085;
    --sidebar-bg: linear-gradient(180deg, #11182b 0%, #18213a 100%);
    --green: #18c964;
    --yellow: #f5c451;
    --red: #ef5350;
    --space-block: 22px;
}

.main { background-color: var(--bg-main); }
.block-container { padding-top: 0.9rem; padding-bottom: 2rem; }

header[data-testid="stHeader"] { visibility: hidden; height: 0; }
div[data-testid="stToolbar"] { visibility: hidden; height: 0; position: fixed; }
button[kind="header"] { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }

section[data-testid="stSidebar"] {
    background: var(--sidebar-bg);
    border-right: 1px solid rgba(255,255,255,0.06);
}
section[data-testid="stSidebar"] * { color: #f8fafc !important; }
section[data-testid="stSidebar"] .stTextInput input,
section[data-testid="stSidebar"] .stNumberInput input,
section[data-testid="stSidebar"] .stDateInput input {
    color: #0b1220 !important;
    background: #ffffff !important;
    border-radius: 10px !important;
}
section[data-testid="stSidebar"] div[data-baseweb="select"] {
    background: #ffffff !important;
    border-radius: 10px !important;
}
section[data-testid="stSidebar"] div[data-baseweb="select"] * {
    color: #0b1220 !important;
}
section[data-testid="stSidebar"] button {
    color: #0b1220 !important;
    background: #ffffff !important;
    border: 1px solid #d8e0ea !important;
    font-weight: 700 !important;
    border-radius: 10px !important;
}

.app-title {
    font-size: 2.25rem;
    font-weight: 800;
    color: var(--text-main);
    margin-bottom: 0.15rem;
}
.app-subtitle {
    color: var(--text-soft);
    font-size: 0.95rem;
    margin-bottom: 0.35rem;
}
.app-note {
    color: var(--text-soft);
    font-size: 0.84rem;
    margin-bottom: var(--space-block);
}
.section-gap { height: var(--space-block); }

.metric-card {
    background: var(--bg-card-dark);
    border-radius: 14px;
    padding: 0.95rem 1rem;
    color: white;
    min-height: 86px;
    box-shadow: 0 4px 14px rgba(5, 17, 40, 0.10);
}
.metric-label {
    color: #c3cede;
    font-size: 0.78rem;
    margin-bottom: 0.15rem;
}
.metric-value {
    font-size: 1.08rem;
    font-weight: 800;
    color: white;
}

.setup-card {
    background: var(--bg-card-dark);
    border-radius: 16px;
    padding: 1rem;
    color: white;
    min-height: 245px;
    box-shadow: 0 6px 18px rgba(7, 18, 37, 0.14);
}
.setup-symbol {
    font-size: 1.5rem;
    font-weight: 800;
    color: white;
    line-height: 1.1;
    margin-bottom: 0.2rem;
}
.setup-line {
    font-size: 0.87rem;
    margin-bottom: 0.18rem;
    color: #f3f6fb;
}
.dot-row {
    display: flex;
    gap: 6px;
    margin-bottom: 8px;
}
.dot-green, .dot-yellow, .dot-red {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    display: inline-block;
}
.dot-green { background: var(--green); }
.dot-yellow { background: var(--yellow); }
.dot-red { background: var(--red); }

.info-inline {
    color: var(--text-soft);
    font-size: 0.82rem;
    margin-top: 0.25rem;
    margin-bottom: 0;
}

@media (max-width: 900px) {
    :root { --space-block: 18px; }
    .app-title { font-size: 1.8rem; }
    .setup-card { min-height: auto; padding: 0.85rem; }
    .setup-symbol { font-size: 1.3rem; }
    .setup-line { font-size: 0.83rem; }
    .block-container {
        padding-top: 0.7rem;
        padding-left: 0.8rem;
        padding-right: 0.8rem;
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
        dots.append('<span class="dot-green"></span>')

    try:
        score = float(row.get("trade_score", 0))
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
    <div class="setup-line"><b>Signal:</b> {signal}</div>
    <div class="setup-line"><b>Score:</b> {fmt_value(row.get("trade_score"), 0)}/100</div>
    <div class="setup-line"><b>{price_label}:</b> {price_value}</div>
    <div class="setup-line"><b>Ziel:</b> {fmt_value(row.get("target_price"))}</div>
    <div class="setup-line"><b>Momentum:</b> {fmt_value(row.get("momentum"), 2, "%")}</div>
    <div class="setup-line"><b>Stop:</b> {fmt_value(row.get("stop_loss"))}</div>
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

    universe_name = st.selectbox("Aktienuniversum auswählen", get_available_universes(), index=0)
    include_europe_listings = st.checkbox("Europa Listings einbeziehen", value=True)
    add_live_prices_to_markettable = st.checkbox("Live-Kurse in Marktcharts", value=False)
    top_n = st.selectbox("Anzahl Top-Trades", [3, 5, 10], index=0)
    min_trade_score = st.slider("Mindest-Trade-Score", 0, 100, 60)

if refresh:
    st.cache_data.clear()

st.markdown('<div class="app-title">Trading Scanner preview</div>', unsafe_allow_html=True)
st.markdown(f'<div class="app-subtitle">{APP_SUBTITLE}</div>', unsafe_allow_html=True)
st.markdown('<div class="app-note">Diese Vorversion zeigt nur den Markt-Scanner und keine Portfolio-Daten.</div>', unsafe_allow_html=True)

try:
    symbols = load_universe(universe_name, include_europe_listings=include_europe_listings, include_commodities_in_all=False)

    with st.spinner("Scanner lädt Marktdaten..."):
        scan_df, rohstoffe_df, market = load_core_data(tuple(symbols))
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

    st.markdown(f'<div class="info-inline">Geladene Aktien im Scanner: {len(valid_scan_df)} | Rohstoffe: {len(valid_rohstoffe_df)}</div>', unsafe_allow_html=True)
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