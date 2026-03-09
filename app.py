from __future__ import annotations

import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

from config import APP_NAME, APP_SUBTITLE
from universe_loader import get_available_universes, load_universe
from stock_scanner import scan_symbols, filter_top_candidates
from data_fetcher import enrich_with_live_prices, get_historical_data
from market_analysis import analyze_market_regime, derive_risk_level, derive_action_signal
from sector_analysis import rank_sectors, get_top_sector_label
from portfolio_utils import analyze_portfolio, summarize_portfolio
from portfolio_store import (
    add_position,
    delete_position,
    get_current_portfolio_user,
    load_portfolio,
    update_position_fields,
    save_current_stop,
)

st.set_page_config(
    page_title=APP_NAME,
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
:root {
    --bg-main: #f4f6f9;
    --bg-card-dark: linear-gradient(180deg, #071225 0%, #0b1730 100%);
    --bg-card-light: #ffffff;
    --border-soft: #dfe5ef;
    --text-main: #182033;
    --text-soft: #667085;
    --sidebar-bg: linear-gradient(180deg, #11182b 0%, #18213a 100%);
    --green: #18c964;
    --yellow: #f5c451;
    --red: #ef5350;
    --space-block: 22px;
    --radius-card: 16px;
}

html, body, [class*="css"] {
    font-family: "Segoe UI", sans-serif;
}

.main {
    background-color: var(--bg-main);
}

.block-container {
    padding-top: 0.9rem;
    padding-bottom: 2rem;
}

header[data-testid="stHeader"] {
    visibility: hidden;
    height: 0;
}

div[data-testid="stToolbar"] {
    visibility: hidden;
    height: 0;
    position: fixed;
}

button[kind="header"] {
    display: none !important;
}

[data-testid="collapsedControl"] {
    display: none !important;
}

section[data-testid="stSidebar"] {
    background: var(--sidebar-bg);
    border-right: 1px solid rgba(255,255,255,0.06);
}

section[data-testid="stSidebar"] * {
    color: #f8fafc !important;
}

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
    line-height: 1.1;
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

.section-gap {
    height: var(--space-block);
}

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
    border-radius: var(--radius-card);
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

.signal-chip {
    display: inline-block;
    border-radius: 999px;
    padding: 0.2rem 0.55rem;
    font-size: 0.74rem;
    font-weight: 700;
    color: white;
    margin-bottom: 0.45rem;
}

.signal-green { background: #1f8f45; }
.signal-yellow { background: #c58a00; }
.signal-red { background: #c93636; }
.signal-gray { background: #6b7280; }

.hint-card {
    background: var(--bg-card-dark);
    border-radius: var(--radius-card);
    padding: 0.95rem;
    color: white;
    min-height: 170px;
    box-shadow: 0 6px 18px rgba(7, 18, 37, 0.14);
}

.hint-title {
    font-size: 1.1rem;
    font-weight: 800;
    color: white;
    margin-bottom: 0.25rem;
}

.hint-line {
    font-size: 0.86rem;
    color: #eef3fb;
    margin-bottom: 0.18rem;
}

.small-muted-dark {
    font-size: 0.8rem;
    color: #d0d9e8;
    margin-top: 0.25rem;
}

.card-shell {
    background: var(--bg-card-light);
    border: 1px solid var(--border-soft);
    border-radius: var(--radius-card);
    padding: 1rem;
}

.card-shell h3, .card-shell h4 {
    color: var(--text-main);
}

.compact-note {
    color: var(--text-soft);
    font-size: 0.82rem;
    margin-bottom: 0.7rem;
}

div[data-testid="stExpander"] {
    margin: 0 !important;
}

[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
}

@media (max-width: 900px) {
    :root {
        --space-block: 18px;
    }

    .app-title {
        font-size: 1.8rem;
    }

    .app-subtitle {
        font-size: 0.9rem;
    }

    .metric-card,
    .setup-card,
    .hint-card,
    .card-shell {
        padding: 0.85rem;
    }

    .setup-card,
    .hint-card {
        min-height: auto;
    }

    .setup-symbol {
        font-size: 1.3rem;
    }

    .setup-line,
    .hint-line {
        font-size: 0.83rem;
    }

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


def fmt_currency(value) -> str:
    if value is None or pd.isna(value):
        return "-"
    return f"{float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


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


def map_signal_emoji(signal_color: str) -> str:
    return {"Rot": "🔴", "Gelb": "🟡", "Grün": "🟢", "Grau": "⚪"}.get(str(signal_color), "⚪")


def build_portfolio_display_table(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    result = df.copy()
    signal_order = {"Rot": 0, "Gelb": 1, "Grün": 2, "Grau": 3}
    result["_signal_order"] = result["signal_color"].map(signal_order).fillna(9)
    result["_buy_date_sort"] = pd.to_datetime(result["buy_date"], errors="coerce")
    result = result.sort_values(
        by=["_signal_order", "_buy_date_sort", "symbol"],
        ascending=[True, False, True],
        na_position="last",
    ).copy()

    result["Ampel"] = result["signal_color"].apply(map_signal_emoji)

    rename_map = {
        "symbol": "Aktie",
        "buy_date": "Kaufdatum",
        "buy_price": "Kaufkurs",
        "shares": "Stück",
        "market_price": "Kurs",
        "pnl_abs_total": "PnL",
        "pnl_pct": "PnL %",
        "current_stop_loss": "Gespeicherter Stop",
        "stop_loss": "Stop",
        "trailing_stop": "Trailing",
        "exit_signal": "Signal",
        "signal_reason": "Hinweis",
    }

    preferred_cols = [
        "Ampel",
        "symbol",
        "buy_date",
        "buy_price",
        "shares",
        "market_price",
        "pnl_abs_total",
        "pnl_pct",
        "current_stop_loss",
        "stop_loss",
        "trailing_stop",
        "exit_signal",
        "signal_reason",
    ]

    existing = [col for col in preferred_cols if col in result.columns]
    return result[existing].copy().rename(columns=rename_map).reset_index(drop=True)


def style_portfolio_table(df: pd.DataFrame):
    if df is None or df.empty:
        return df

    format_map = {
        "Kaufkurs": "{:.2f}",
        "Stück": "{:.2f}",
        "Kurs": "{:.2f}",
        "PnL": "{:.2f}",
        "PnL %": "{:.2f}%",
        "Gespeicherter Stop": "{:.2f}",
        "Stop": "{:.2f}",
        "Trailing": "{:.2f}",
    }

    def color_pnl(val):
        try:
            val = float(val)
        except Exception:
            return ""
        if val > 0:
            return "color: #146c2e; font-weight: 700;"
        if val < 0:
            return "color: #b42318; font-weight: 700;"
        return ""

    styler = df.style.format(format_map, na_rep="-")
    if "PnL" in df.columns:
        styler = styler.map(color_pnl, subset=["PnL"])
    if "PnL %" in df.columns:
        styler = styler.map(color_pnl, subset=["PnL %"])
    return styler


def render_portfolio_summary(portfolio_df: pd.DataFrame) -> None:
    summary = summarize_portfolio(portfolio_df)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Positionen", summary["positions"])
    with c2:
        st.metric("Portfolio-Wert", fmt_currency(summary["portfolio_value"]))
    with c3:
        st.metric("Gesamt-PnL", fmt_currency(summary["pnl_abs_total"]))
    with c4:
        st.metric("Rote Signale", summary["red_signals"])


def render_portfolio_signal_cards(portfolio_df: pd.DataFrame) -> None:
    if portfolio_df is None or portfolio_df.empty:
        return

    st.header("Wichtige Hinweise")
    top_alerts = portfolio_df.head(3).copy()
    cols = st.columns(min(3, len(top_alerts)))

    for idx, (_, row) in enumerate(top_alerts.iterrows()):
        css_class = {
            "Rot": "signal-red",
            "Gelb": "signal-yellow",
            "Grün": "signal-green",
        }.get(str(row.get("signal_color", "Grau")), "signal-gray")

        with cols[idx]:
            st.markdown(
                f"""
<div class="hint-card">
    <span class="signal-chip {css_class}">{row.get("exit_signal", "-")}</span>
    <div class="hint-title">{row.get("symbol", "-")}</div>
    <div class="hint-line"><b>Kurs:</b> {fmt_value(row.get("market_price"))}</div>
    <div class="hint-line"><b>PnL:</b> {fmt_value(row.get("pnl_pct"), 2, "%")}</div>
    <div class="hint-line"><b>Trailing:</b> {fmt_value(row.get("trailing_stop"))}</div>
    <div class="small-muted-dark">{row.get("signal_reason", "-")}</div>
</div>
""",
                unsafe_allow_html=True,
            )


def ensure_portfolio_user_state() -> str:
    if "portfolio_user_key" not in st.session_state:
        st.session_state["portfolio_user_key"] = get_current_portfolio_user()

    sidebar_key = st.session_state.get("portfolio_user_key_input", st.session_state["portfolio_user_key"])
    if sidebar_key != st.session_state["portfolio_user_key"]:
        st.session_state["portfolio_user_key"] = sidebar_key.strip() or "guest"

    return st.session_state["portfolio_user_key"]


def save_new_position_via_form() -> None:
    symbol = str(st.session_state.get("portfolio_symbol", "")).strip().upper()
    buy_price = st.session_state.get("portfolio_buy_price")
    shares = st.session_state.get("portfolio_shares")
    buy_date = st.session_state.get("portfolio_buy_date")

    if not symbol:
        st.error("Bitte ein Symbol eingeben.")
        return
    if buy_price is None or float(buy_price) <= 0:
        st.error("Bitte einen gültigen Kaufkurs eingeben.")
        return
    if shares is None or float(shares) <= 0:
        st.error("Bitte eine gültige Stückzahl eingeben.")
        return

    add_position(
        {
            "symbol": symbol,
            "buy_price": float(buy_price),
            "shares": float(shares),
            "buy_date": buy_date,
            "initial_stop_loss": float(st.session_state.get("portfolio_initial_stop_loss") or 0) or None,
            "strategy_tag": str(st.session_state.get("portfolio_strategy_tag", "")).strip() or None,
            "note": str(st.session_state.get("portfolio_note", "")).strip() or None,
        },
        user_key=st.session_state.get("portfolio_user_key"),
    )

    st.cache_data.clear()
    st.success(f"Position {symbol} wurde gespeichert.")
    st.rerun()


def save_edited_position() -> None:
    position_id = st.session_state.get("manage_position_id")
    if not position_id:
        st.error("Keine Position ausgewählt.")
        return

    symbol = str(st.session_state.get("manage_symbol", "")).strip().upper()
    buy_price = st.session_state.get("manage_buy_price")
    shares = st.session_state.get("manage_shares")

    if not symbol:
        st.error("Bitte ein Symbol eingeben.")
        return
    if buy_price is None or float(buy_price) <= 0:
        st.error("Bitte einen gültigen Kaufkurs eingeben.")
        return
    if shares is None or float(shares) <= 0:
        st.error("Bitte eine gültige Stückzahl eingeben.")
        return

    update_position_fields(
        position_id=position_id,
        updates={
            "symbol": symbol,
            "buy_price": float(buy_price),
            "shares": float(shares),
            "buy_date": st.session_state.get("manage_buy_date"),
            "initial_stop_loss": float(st.session_state.get("manage_initial_stop_loss") or 0) or None,
            "current_stop_loss": float(st.session_state.get("manage_current_stop_loss") or 0) or None,
            "target_price": float(st.session_state.get("manage_target_price") or 0) or None,
            "strategy_tag": str(st.session_state.get("manage_strategy_tag", "")).strip() or None,
            "note": str(st.session_state.get("manage_note", "")).strip() or None,
        },
        user_key=st.session_state.get("portfolio_user_key"),
    )

    st.cache_data.clear()
    st.success(f"Position {symbol} wurde aktualisiert.")
    st.rerun()


def render_add_position_section() -> None:
    st.markdown('<div class="card-shell">', unsafe_allow_html=True)
    st.subheader("Neue Position")
    st.markdown('<div class="compact-note">Neue Käufe erfassen und direkt überwachen.</div>', unsafe_allow_html=True)

    with st.form("portfolio_add_form", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.text_input("Symbol", key="portfolio_symbol", placeholder="z. B. AAPL")
        with c2:
            st.number_input("Kaufkurs", min_value=0.0, step=0.01, format="%.2f", key="portfolio_buy_price")
        with c3:
            st.number_input("Stück", min_value=0.0, step=1.0, format="%.2f", key="portfolio_shares")
        with c4:
            st.date_input("Kaufdatum", key="portfolio_buy_date")

        c5, c6 = st.columns(2)
        with c5:
            st.number_input("Initialer Stop (optional)", min_value=0.0, step=0.01, format="%.2f", key="portfolio_initial_stop_loss")
        with c6:
            st.text_input("Strategie / Tag (optional)", key="portfolio_strategy_tag")

        st.text_area("Notiz (optional)", key="portfolio_note", height=80)

        if st.form_submit_button("Position speichern", use_container_width=True):
            save_new_position_via_form()

    st.markdown('</div>', unsafe_allow_html=True)


def render_manage_existing_position(raw_portfolio_df: pd.DataFrame, portfolio_df: pd.DataFrame) -> None:
    st.markdown('<div class="card-shell">', unsafe_allow_html=True)
    st.subheader("Bestehende Position verwalten")
    st.markdown('<div class="compact-note">Eine Position auswählen und direkt bearbeiten, Stop speichern, löschen oder den Chart ansehen.</div>', unsafe_allow_html=True)

    if raw_portfolio_df is None or raw_portfolio_df.empty:
        st.info("Keine Positionen vorhanden.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    raw_working = raw_portfolio_df.copy()
    raw_working["label"] = (
        raw_working["symbol"].astype(str)
        + " | Kaufkurs "
        + raw_working["buy_price"].astype(str)
        + " | Stück "
        + raw_working["shares"].astype(str)
    )

    options = dict(zip(raw_working["label"], raw_working["position_id"]))
    selected_label = st.selectbox("Position auswählen", list(options.keys()), key="manage_position_select")
    selected_id = options[selected_label]

    raw_row = raw_working.loc[raw_working["position_id"] == selected_id].iloc[0]
    analyzed_row = None
    if portfolio_df is not None and not portfolio_df.empty and "position_id" in portfolio_df.columns:
        match = portfolio_df.loc[portfolio_df["position_id"] == selected_id]
        if not match.empty:
            analyzed_row = match.iloc[0]

    st.session_state["manage_position_id"] = selected_id

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Aktie", str(raw_row.get("symbol", "-")))
    with c2:
        st.metric("Gespeicherter Stop", fmt_value(raw_row.get("current_stop_loss")))
    with c3:
        st.metric("Empf. Stop", fmt_value(analyzed_row.get("stop_loss") if analyzed_row is not None else None))
    with c4:
        st.metric("Trailing", fmt_value(analyzed_row.get("trailing_stop") if analyzed_row is not None else None))

    st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)

    with st.form("manage_existing_position_form"):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.text_input("Symbol", value=str(raw_row.get("symbol", "")), key="manage_symbol")
        with c2:
            st.number_input("Kaufkurs", min_value=0.0, step=0.01, format="%.2f",
                            value=float(raw_row.get("buy_price") or 0.0), key="manage_buy_price")
        with c3:
            st.number_input("Stück", min_value=0.0, step=1.0, format="%.2f",
                            value=float(raw_row.get("shares") or 0.0), key="manage_shares")
        with c4:
            buy_date_value = pd.to_datetime(raw_row.get("buy_date"), errors="coerce")
            default_date = buy_date_value.date() if pd.notna(buy_date_value) else pd.Timestamp.today().date()
            st.date_input("Kaufdatum", value=default_date, key="manage_buy_date")

        c5, c6, c7 = st.columns(3)
        with c5:
            st.number_input("Initialer Stop", min_value=0.0, step=0.01, format="%.2f",
                            value=float(raw_row.get("initial_stop_loss") or 0.0), key="manage_initial_stop_loss")
        with c6:
            st.number_input("Gespeicherter Stop", min_value=0.0, step=0.01, format="%.2f",
                            value=float(raw_row.get("current_stop_loss") or 0.0), key="manage_current_stop_loss")
        with c7:
            st.number_input("Zielpreis", min_value=0.0, step=0.01, format="%.2f",
                            value=float(raw_row.get("target_price") or 0.0), key="manage_target_price")

        st.text_input("Strategie / Tag", value=str(raw_row.get("strategy_tag") or ""), key="manage_strategy_tag")
        st.text_area("Notiz", value=str(raw_row.get("note") or ""), key="manage_note", height=80)

        save_changes = st.form_submit_button("Änderungen speichern", use_container_width=True)
        if save_changes:
            save_edited_position()

    st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)

    with c1:
        recommended_stop = analyzed_row.get("trailing_stop") if analyzed_row is not None else None
        if recommended_stop is None or pd.isna(recommended_stop):
            st.button("Trailing-Stop übernehmen", disabled=True, use_container_width=True)
        else:
            if st.button("Trailing-Stop übernehmen", use_container_width=True):
                save_current_stop(
                    position_id=selected_id,
                    current_stop_loss=float(recommended_stop),
                    user_key=st.session_state.get("portfolio_user_key"),
                )
                st.cache_data.clear()
                st.success("Trailing-Stop wurde gespeichert.")
                st.rerun()

    with c2:
        if st.button("Position löschen", type="secondary", use_container_width=True):
            delete_position(selected_id, user_key=st.session_state.get("portfolio_user_key"))
            st.cache_data.clear()
            st.success("Position wurde gelöscht.")
            st.rerun()

    st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)

    with st.expander("Chart dieser Position anzeigen", expanded=False):
        render_single_position_chart(raw_row, analyzed_row)

    st.markdown('</div>', unsafe_allow_html=True)


def render_single_position_chart(raw_row: pd.Series, analyzed_row: pd.Series | None) -> None:
    symbol = str(raw_row.get("symbol"))

    hist = get_historical_data(symbol, period="1y", interval="1d")
    if hist is None or hist.empty or "Close" not in hist.columns:
        st.warning("Für diese Position konnten keine historischen Kursdaten geladen werden.")
        return

    chart_df = hist.copy()
    chart_df["Close"] = pd.to_numeric(chart_df["Close"], errors="coerce")
    chart_df["SMA50"] = chart_df["Close"].rolling(50).mean()
    chart_df["SMA200"] = chart_df["Close"].rolling(200).mean()
    chart_df = chart_df.dropna(subset=["Close"]).copy()

    fig, ax = plt.subplots(figsize=(11, 4.6))
    ax.plot(chart_df.index, chart_df["Close"], label="Close")
    ax.plot(chart_df.index, chart_df["SMA50"], label="SMA50")
    ax.plot(chart_df.index, chart_df["SMA200"], label="SMA200")

    current_stop_loss = raw_row.get("current_stop_loss")
    buy_price = raw_row.get("buy_price")
    stop_loss = analyzed_row.get("stop_loss") if analyzed_row is not None else None
    trailing_stop = analyzed_row.get("trailing_stop") if analyzed_row is not None else None

    if current_stop_loss is not None and not pd.isna(current_stop_loss):
        ax.axhline(float(current_stop_loss), linestyle="--", label="Gespeicherter Stop")
    if stop_loss is not None and not pd.isna(stop_loss):
        ax.axhline(float(stop_loss), linestyle=":", label="Stop")
    if trailing_stop is not None and not pd.isna(trailing_stop):
        ax.axhline(float(trailing_stop), linestyle="-.", label="Trailing")
    if buy_price is not None and not pd.isna(buy_price):
        ax.axhline(float(buy_price), linestyle="-", label="Kaufkurs")

    ax.set_title(f"{symbol} – Portfolio Chart")
    ax.set_xlabel("Datum")
    ax.set_ylabel("Preis")
    ax.legend()
    ax.grid(True, alpha=0.3)

    st.pyplot(fig, use_container_width=True)


@st.cache_data(ttl=600, show_spinner=False)
def load_core_data(symbols_key: tuple[str, ...]) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    symbols = list(symbols_key)
    scan_df = scan_symbols(symbols, max_workers=8, fetch_live_prices=False)

    rohstoffe = load_universe("Rohstoffe")
    rohstoffe_df = scan_symbols(rohstoffe, max_workers=5, fetch_live_prices=False)

    market = analyze_market_regime()
    return scan_df, rohstoffe_df, market


@st.cache_data(ttl=300, show_spinner=False)
def load_portfolio_data(enabled: bool, user_key: str) -> pd.DataFrame:
    if not enabled:
        return pd.DataFrame()
    return analyze_portfolio(user_key=user_key)


@st.cache_data(ttl=120, show_spinner=False)
def load_raw_portfolio_data(enabled: bool, user_key: str) -> pd.DataFrame:
    if not enabled:
        return pd.DataFrame()
    return load_portfolio(user_key=user_key)


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
    load_portfolio_monitor = st.checkbox("Portfolio Monitor laden", value=True)
    add_live_prices_to_markettable = st.checkbox("Live-Kurse in Marktcharts", value=False)
    top_n = st.selectbox("Anzahl Top-Trades", [3, 5, 10], index=0)
    min_trade_score = st.slider("Mindest-Trade-Score", 0, 100, 60)

    st.markdown("---")
    st.markdown("### Portfolio-Profil")
    st.text_input(
        "Eigenes Profil / Benutzername",
        value=st.session_state.get("portfolio_user_key", "guest"),
        key="portfolio_user_key_input",
        help="Jedes Profil hat eine eigene Portfolio-Datei.",
    )
    st.caption("Live-Kurse und Analysepreise werden getrennt verarbeitet.")

if refresh:
    st.cache_data.clear()

portfolio_user_key = ensure_portfolio_user_state()

st.markdown('<div class="app-title">Trading Scanner 4.2</div>', unsafe_allow_html=True)
st.markdown(f'<div class="app-subtitle">{APP_SUBTITLE}</div>', unsafe_allow_html=True)
st.markdown('<div class="app-note">Historie wird schnell gescannt, Live-Kurse werden nur gezielt nachgeladen.</div>', unsafe_allow_html=True)

try:
    symbols = load_universe(universe_name, include_europe_listings=include_europe_listings, include_commodities_in_all=False)

    with st.spinner("Scanner lädt Marktdaten..."):
        scan_df, rohstoffe_df, market = load_core_data(tuple(symbols))
        portfolio_df = load_portfolio_data(load_portfolio_monitor, portfolio_user_key)
        raw_portfolio_df = load_raw_portfolio_data(load_portfolio_monitor, portfolio_user_key)

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

    if load_portfolio_monitor and portfolio_df is not None and not portfolio_df.empty:
        render_portfolio_signal_cards(portfolio_df)
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

    st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)

    st.header("Portfolio Monitor")
    if not load_portfolio_monitor:
        st.info("Portfolio Monitor ist deaktiviert.")
    else:
        st.caption(f"Aktives Portfolio-Profil: {portfolio_user_key}")

        if portfolio_df.empty:
            st.info("Noch keine Positionen gespeichert.")
        else:
            render_portfolio_summary(portfolio_df)
            st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
            st.subheader("Portfolio-Übersicht")
            st.dataframe(
                style_portfolio_table(build_portfolio_display_table(portfolio_df)),
                use_container_width=True,
                hide_index=True,
            )

        st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)

        render_add_position_section()

        st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)

        render_manage_existing_position(raw_portfolio_df, portfolio_df)

except Exception as e:
    st.error(f"Fehler beim Laden der App: {e}")
    st.exception(e)