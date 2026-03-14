from __future__ import annotations

import math
from datetime import datetime, timezone

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Wedge
import pandas as pd
import requests
import streamlit as st

from alerts import alerts_config_complete, get_alert_settings, process_alerts
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
    save_current_stop,
    update_position_fields,
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
    --space-block: 24px;
    --space-card: 14px;
    --radius-card: 18px;
    --card-dark-bg: linear-gradient(180deg, #071225 0%, #0b1730 100%);
    --card-dark-text: #ffffff;
    --card-dark-soft: #c9d4e5;
    --signal-green: #1f8f45;
    --signal-yellow: #c58a00;
    --signal-red: #c93636;
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
section[data-testid="stSidebar"] .stSlider,
section[data-testid="stSidebar"] .stTextInput,
section[data-testid="stSidebar"] .stTextArea,
section[data-testid="stSidebar"] .stNumberInput {
    margin-bottom: 0.45rem !important;
}

.ts-card-dark {
    background: linear-gradient(180deg, #071225 0%, #0b1730 100%);
    color: #ffffff;
    border-radius: 18px;
    padding: 1rem;
    box-shadow: 0 6px 18px rgba(7, 18, 37, 0.14);
    margin-bottom: 14px;
}

.ts-metric-card { min-height: 96px; }
.ts-metric-label { color: #c9d4e5; font-size: 0.8rem; margin-bottom: 0.2rem; }
.ts-metric-value { font-size: 1.22rem; font-weight: 800; }

.ts-setup-card { min-height: 320px; }
.ts-setup-symbol {
    font-size: 1.7rem;
    font-weight: 800;
    line-height: 1.1;
    margin-bottom: 0.18rem;
}
.ts-line {
    font-size: 0.92rem;
    line-height: 1.35;
    margin-bottom: 0.12rem;
    color: #f3f6fb;
}
.ts-dot-row { display: flex; gap: 6px; margin-bottom: 10px; }
.ts-dot-green, .ts-dot-yellow, .ts-dot-red {
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

.ts-shell {
    border: 1px solid rgba(120, 130, 150, 0.18);
    border-radius: 18px;
    padding: 1rem;
    background: rgba(255,255,255,0.03);
    backdrop-filter: blur(2px);
}
.ts-shell-note {
    font-size: 0.88rem;
    opacity: 0.78;
    margin-bottom: 0.7rem;
}

.ts-signal-chip {
    display: inline-block;
    border-radius: 999px;
    padding: 0.22rem 0.6rem;
    font-size: 0.74rem;
    font-weight: 700;
    color: white;
    margin-bottom: 0.5rem;
}
.ts-signal-green { background: #1f8f45; }
.ts-signal-yellow { background: #c58a00; }
.ts-signal-red { background: #c93636; }
.ts-signal-gray { background: #6b7280; }

.ts-hint-card { min-height: 180px; }
.ts-hint-title {
    font-size: 1.14rem;
    font-weight: 800;
    margin-bottom: 0.25rem;
}
.ts-hint-reason {
    font-size: 0.84rem;
    color: #c9d4e5;
    margin-top: 0.25rem;
    line-height: 1.35;
}

.ts-fg-shell {
    border: 1px solid rgba(120, 130, 150, 0.18);
    border-radius: 18px;
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

.ts-sector-badge {
    display: inline-block;
    border-radius: 999px;
    padding: 0.18rem 0.6rem;
    font-size: 0.72rem;
    font-weight: 700;
    color: #ffffff;
    white-space: nowrap;
}
.ts-sector-note {
    font-size: 0.84rem;
    opacity: 0.8;
    margin-bottom: 0.7rem;
}

.ts-link-inline {
    color: #8ec5ff !important;
    text-decoration: none !important;
    font-weight: 700;
}
.ts-link-inline:hover {
    text-decoration: underline !important;
}

[data-testid="stDataFrame"] {
    border-radius: 14px;
    overflow: hidden;
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


def safe_float(value):
    try:
        if value is None or pd.isna(value):
            return None
        return float(value)
    except Exception:
        return None


def build_wkn_link(wkn: str) -> str:
    if not wkn or wkn == "-":
        return "#"
    return f"https://www.onvista.de/suche?searchValue={wkn}"


def build_chart_link(symbol: str) -> str:
    if not symbol:
        return "#"
    return f"https://finance.yahoo.com/quote/{symbol}"


def build_company_link(symbol: str, name: str | None = None, wkn: str | None = None) -> str:
    query = wkn if (wkn and wkn != "-") else (name or symbol)
    return f"https://www.onvista.de/suche?searchValue={query}"


def get_dot_html(row: pd.Series) -> str:
    dots = []

    if bool(row.get("golden_cross", False)):
        dots.append('<span class="ts-dot-green"></span>')

    score = safe_float(row.get("trade_score")) or 0.0
    if score >= 80:
        dots.append('<span class="ts-dot-green"></span>')
    elif score >= 65:
        dots.append('<span class="ts-dot-yellow"></span>')
    else:
        dots.append('<span class="ts-dot-red"></span>')

    rsi = safe_float(row.get("rsi"))
    if rsi is not None:
        if rsi < 30:
            dots.append('<span class="ts-dot-green"></span>')
        elif rsi > 70:
            dots.append('<span class="ts-dot-red"></span>')
        else:
            dots.append('<span class="ts-dot-yellow"></span>')

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
    symbol = row.get("symbol", "-")
    name = row.get("name", "-")
    wkn = row.get("wkn", "-")

    price_label = "Aktuell" if market_price is not None and not pd.isna(market_price) else "Analysepreis"
    price_value = fmt_value(
        market_price if market_price is not None and not pd.isna(market_price) else analysis_price
    )
    source_text = source if source not in [None, ""] else "-"

    clean_symbol = str(symbol).strip() if symbol not in [None, ""] else "-"
    clean_name = str(name).strip() if name not in [None, ""] else clean_symbol
    clean_wkn = str(wkn).strip() if wkn not in [None, ""] else "-"

    company_link = build_company_link(clean_symbol, clean_name, clean_wkn)

    if clean_name not in ["", "-"]:
        name_html = f'<a class="ts-link-inline" href="{company_link}" target="_blank">{clean_name}</a>'
    else:
        name_html = clean_symbol

    if clean_wkn not in ["", "-"]:
        wkn_html = f'<a class="ts-link-inline" href="{build_wkn_link(clean_wkn)}" target="_blank">{clean_wkn}</a>'
    else:
        wkn_html = "-"

    rsi_text = row.get("rsi_signal")
    if rsi_text in [None, "", "-"]:
        rsi_value = safe_float(row.get("rsi"))
        rsi_text = fmt_value(rsi_value, 1) if rsi_value is not None else "-"

    macd_text = row.get("macd_trend")
    if macd_text in [None, "", "-"]:
        macd_text = "-"

    trend_channel_text = row.get("trend_channel_signal")
    if trend_channel_text in [None, "", "-"]:
        trend_value = safe_float(row.get("trend_channel_position_pct"))
        trend_channel_text = fmt_value(trend_value, 0, "%") if trend_value is not None else "-"

    html = f"""<div class="ts-card-dark ts-setup-card">
{get_dot_html(row)}
<div class="ts-setup-symbol">{clean_symbol}</div>
<div class="ts-line">{name_html}</div>
<div class="ts-line"><b>WKN:</b> {wkn_html}</div>
<div class="ts-line"><b>Signal:</b> {signal}</div>
<div class="ts-line"><b>Score:</b> {fmt_value(row.get("trade_score"), 0)}/100</div>
<div class="ts-line"><b>{price_label}:</b> {price_value}</div>
<div class="ts-line"><b>Ziel:</b> {fmt_value(row.get("target_price"))}</div>
<div class="ts-line"><b>Stop:</b> {fmt_value(row.get("stop_loss"))}</div>
<div class="ts-line"><b>Momentum:</b> {fmt_value(row.get("momentum"), 2, "%")}</div>
<div class="ts-line"><b>RSI:</b> {rsi_text}</div>
<div class="ts-line"><b>MACD:</b> {macd_text}</div>
<div class="ts-line"><b>Trendkanal:</b> {trend_channel_text}</div>
<div class="ts-line"><b>Quelle:</b> {source_text}</div>
</div>"""
    st.markdown(html, unsafe_allow_html=True)


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
            "Rot": "ts-signal-red",
            "Gelb": "ts-signal-yellow",
            "Grün": "ts-signal-green",
        }.get(str(row.get("signal_color", "Grau")), "ts-signal-gray")

        with cols[idx]:
            st.markdown(
                f"""
<div class="ts-card-dark ts-hint-card">
    <span class="ts-signal-chip {css_class}">{row.get("exit_signal", "-")}</span>
    <div class="ts-hint-title">{row.get("symbol", "-")}</div>
    <div class="ts-line"><b>Kurs:</b> {fmt_value(row.get("market_price"))}</div>
    <div class="ts-line"><b>PnL:</b> {fmt_value(row.get("pnl_pct"), 2, "%")}</div>
    <div class="ts-line"><b>Trailing:</b> {fmt_value(row.get("trailing_stop"))}</div>
    <div class="ts-hint-reason">{row.get("signal_reason", "-")}</div>
</div>
""",
                unsafe_allow_html=True,
            )


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


@st.cache_data(ttl=900, show_spinner=False)
def load_fear_greed_data() -> dict:
    urls = [
        "https://production.dataviz.cnn.io/index/fearandgreed/graphdata",
        "https://production.dataviz.cnn.io/index/fearandgreed/graphdata/",
    ]
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json,text/plain,*/*",
        "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://www.cnn.com/markets/fear-and-greed",
        "Origin": "https://www.cnn.com",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }

    empty_payload = {"ok": False, "value": None, "rating": None, "timestamp": None}

    def _safe_num(value):
        try:
            if value is None or pd.isna(value) or value == "":
                return None
            return float(value)
        except Exception:
            return None

    def _extract_current_payload(data):
        if not isinstance(data, dict):
            return None

        candidates = [
            data.get("fear_and_greed"),
            data.get("fearAndGreed"),
            data.get("fear_greed"),
            data.get("fgi"),
            data.get("data"),
            data,
        ]

        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue

            nested_candidates = [
                candidate,
                candidate.get("now") if isinstance(candidate.get("now"), dict) else None,
                candidate.get("current") if isinstance(candidate.get("current"), dict) else None,
            ]

            for current in nested_candidates:
                if not isinstance(current, dict):
                    continue

                value = _safe_num(current.get("score", current.get("value")))
                if value is None and current is candidate:
                    for alt_key in ("now", "current"):
                        alt_value = candidate.get(alt_key)
                        if isinstance(alt_value, dict):
                            value = _safe_num(alt_value.get("score", alt_value.get("value")))
                            if value is not None:
                                current = alt_value
                                break

                if value is None:
                    continue

                rating = current.get("rating", current.get("valueText")) or _fg_label_from_value(value)
                timestamp = current.get("timestamp") or candidate.get("timestamp")

                timestamp_text = None
                if timestamp not in [None, ""]:
                    try:
                        ts_num = float(timestamp)
                        if ts_num > 10_000_000_000:
                            ts_num = ts_num / 1000.0
                        timestamp_text = datetime.fromtimestamp(ts_num, tz=timezone.utc).strftime("%d.%m.%Y %H:%M UTC")
                    except Exception:
                        try:
                            timestamp_text = pd.to_datetime(timestamp, utc=True).strftime("%d.%m.%Y %H:%M UTC")
                        except Exception:
                            timestamp_text = None

                return {"ok": True, "value": value, "rating": rating, "timestamp": timestamp_text}

        return None

    try:
        session = requests.Session()
        session.headers.update(headers)

        last_error = None
        for url in urls:
            try:
                response = session.get(url, timeout=12)
                response.raise_for_status()
                payload = _extract_current_payload(response.json())
                if payload is not None:
                    return payload
            except Exception:
                last_error = True
                continue

        if last_error:
            return empty_payload
    except Exception:
        return empty_payload

    return empty_payload


def build_fear_greed_gauge(value: float | int | None):
    fig, ax = plt.subplots(figsize=(5.6, 3.2))
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
            fontsize=9,
            fontweight="bold",
            rotation=((theta1 + theta2) / 2.0) - 90,
            rotation_mode="anchor",
        )

    for v in [0, 25, 50, 75, 100]:
        angle = math.radians(180 - (v / 100) * 180)
        r = outer_r - width - 0.05
        x = r * math.cos(angle)
        y = r * math.sin(angle)
        ax.text(x, y, str(v), ha="center", va="center", fontsize=8, color="#6b7280")

    if value is not None and not pd.isna(value):
        value = max(0, min(100, float(value)))
        angle = math.radians(180 - (value / 100) * 180)
        needle_r = outer_r - 0.08
        x = needle_r * math.cos(angle)
        y = needle_r * math.sin(angle)
        ax.plot([0, x], [0, y], lw=3.5, color="#1f2937", solid_capstyle="round")
        ax.add_patch(Circle((0, 0), 0.07, color="#1f2937"))
        ax.add_patch(Circle((0, 0), 0.18, color="white", zorder=3))
        ax.text(0, 0.05, f"{int(round(value))}", ha="center", va="center", fontsize=18, fontweight="bold")
        ax.text(
            0,
            -0.12,
            _fg_label_from_value(value),
            ha="center",
            va="center",
            fontsize=9,
            color=_fg_color(value),
            fontweight="bold",
        )
    else:
        ax.add_patch(Circle((0, 0), 0.18, color="white", zorder=3))
        ax.text(0, 0.0, "-", ha="center", va="center", fontsize=18, fontweight="bold")

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
        st.markdown("</div>", unsafe_allow_html=True)
        return

    fig = build_fear_greed_gauge(fg.get("value"))
    st.pyplot(fig, use_container_width=False)
    st.markdown("</div>", unsafe_allow_html=True)


def _sector_fg_label(value: int | float | None) -> str:
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


def _sector_fg_badge_html(value: int | float | None) -> str:
    label = _sector_fg_label(value)
    color = _fg_color(value)
    value_text = "-" if value is None or pd.isna(value) else str(int(round(float(value))))
    return f'<span class="ts-sector-badge" style="background:{color};">FG {value_text} · {label}</span>'


def prepare_sector_ranking_view(sector_df: pd.DataFrame) -> pd.DataFrame:
    if sector_df is None or sector_df.empty:
        return pd.DataFrame()

    result = sector_df.copy()

    if "Sector Fear & Greed" not in result.columns:
        result["Sector Fear & Greed"] = None

    if "Sector Sentiment" not in result.columns:
        result["Sector Sentiment"] = result["Sector Fear & Greed"].apply(_sector_fg_label)

    display_cols = [
        "Sektor",
        "Sector Fear & Greed",
        "Sector Sentiment",
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
        "Sektor Score",
    ]
    existing = [col for col in display_cols if col in result.columns]
    return result[existing].reset_index(drop=True)


def render_sector_ranking_section(sector_df: pd.DataFrame) -> None:
    prepared = prepare_sector_ranking_view(sector_df)
    if prepared.empty:
        st.info("Keine gültigen Sektordaten verfügbar.")
        return

    st.markdown(
        '<div class="ts-sector-note">Der kleine Sector Fear & Greed Wert wird direkt aus der aktuellen Sektorverfassung des Scans abgeleitet.</div>',
        unsafe_allow_html=True,
    )

    option_map = {
        idx: f'{row.get("Sektor", "-")} · FG {int(row.get("Sector Fear & Greed")) if pd.notna(row.get("Sector Fear & Greed")) else "-"} · {row.get("Sector Sentiment", "-")}'
        for idx, row in prepared.iterrows()
    }

    selected_idx = st.selectbox(
        "Branche auswählen",
        options=list(option_map.keys()),
        format_func=lambda idx: option_map.get(idx, str(idx)),
        key="sector_ranking_select",
    )

    selected_row = prepared.iloc[int(selected_idx)]
    c1, c2 = st.columns([3.0, 1.0])
    with c1:
        st.markdown(f'**{selected_row.get("Sektor", "-")}**')
    with c2:
        st.markdown(_sector_fg_badge_html(selected_row.get("Sector Fear & Greed")), unsafe_allow_html=True)

    st.dataframe(prepared, use_container_width=True, hide_index=True)


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
    st.markdown('<div class="ts-shell">', unsafe_allow_html=True)
    st.subheader("Neue Position")
    st.markdown('<div class="ts-shell-note">Neue Käufe erfassen und direkt überwachen.</div>', unsafe_allow_html=True)

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

    st.markdown("</div>", unsafe_allow_html=True)


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


def render_manage_existing_position(raw_portfolio_df: pd.DataFrame, portfolio_df: pd.DataFrame) -> None:
    st.markdown('<div class="ts-shell">', unsafe_allow_html=True)
    st.subheader("Bestehende Position verwalten")
    st.markdown(
        '<div class="ts-shell-note">Eine Position auswählen und direkt bearbeiten, Stop speichern, löschen oder den Chart ansehen.</div>',
        unsafe_allow_html=True,
    )

    if raw_portfolio_df is None or raw_portfolio_df.empty:
        st.info("Keine Positionen vorhanden.")
        st.markdown("</div>", unsafe_allow_html=True)
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

    st.markdown("</div>", unsafe_allow_html=True)


def _apply_provider_defaults(provider: str) -> None:
    provider = str(provider).strip().lower()

    if provider == "gmx":
        st.session_state["ALERT_SMTP_HOST"] = "mail.gmx.net"
        st.session_state["ALERT_SMTP_PORT"] = 587
        st.session_state["ALERT_SMTP_USE_TLS"] = True
        st.session_state["ALERT_SMTP_USE_SSL"] = False
    elif provider == "gmail":
        st.session_state["ALERT_SMTP_HOST"] = "smtp.gmail.com"
        st.session_state["ALERT_SMTP_PORT"] = 587
        st.session_state["ALERT_SMTP_USE_TLS"] = True
        st.session_state["ALERT_SMTP_USE_SSL"] = False
    elif provider == "outlook":
        st.session_state["ALERT_SMTP_HOST"] = "smtp.office365.com"
        st.session_state["ALERT_SMTP_PORT"] = 587
        st.session_state["ALERT_SMTP_USE_TLS"] = True
        st.session_state["ALERT_SMTP_USE_SSL"] = False


def _init_alert_state() -> None:
    settings = get_alert_settings()

    defaults = {
        "ALERT_ENABLED": settings["enabled"],
        "ALERT_SMTP_HOST": settings["smtp_host"],
        "ALERT_SMTP_PORT": settings["smtp_port"],
        "ALERT_SMTP_USERNAME": settings["smtp_username"],
        "ALERT_SMTP_PASSWORD": settings["smtp_password"],
        "ALERT_SMTP_USE_TLS": settings["smtp_use_tls"],
        "ALERT_SMTP_USE_SSL": settings["smtp_use_ssl"],
        "ALERT_FROM_EMAIL": settings["from_email"],
        "ALERT_FROM_NAME": settings["from_name"],
        "ALERT_RECIPIENTS": ", ".join(settings["recipients"]) if settings["recipients"] else "",
        "ALERT_BUY_SIGNAL_NAME": settings["buy_signal_name"],
        "ALERT_PORTFOLIO_SELL_SIGNAL_NAME": settings["portfolio_sell_signal_name"],
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_alert_sidebar(scan_df: pd.DataFrame | None, portfolio_df: pd.DataFrame | None) -> None:
    _init_alert_state()

    with st.sidebar.expander("Mail Alerts", expanded=False):
        provider = st.selectbox(
            "Mail-Anbieter",
            ["GMX", "Gmail", "Outlook", "Custom"],
            index=0,
            key="alert_provider_select",
        )

        if st.button("SMTP-Vorschläge übernehmen", use_container_width=True, key="apply_provider_defaults_btn"):
            _apply_provider_defaults(provider)
            st.rerun()

        st.checkbox("Alerts aktivieren", key="ALERT_ENABLED")
        st.text_input("Absender-Mail", key="ALERT_FROM_EMAIL", placeholder="z. B. deinname@gmx.de")
        st.text_input("Absender-Name", key="ALERT_FROM_NAME", placeholder=APP_NAME)
        st.text_input("SMTP Benutzername", key="ALERT_SMTP_USERNAME", placeholder="oft identisch mit Mailadresse")
        st.text_input("SMTP Passwort / App-Passwort", key="ALERT_SMTP_PASSWORD", type="password")
        st.text_input("SMTP Host", key="ALERT_SMTP_HOST", placeholder="z. B. mail.gmx.net")
        st.number_input("SMTP Port", min_value=1, max_value=65535, step=1, key="ALERT_SMTP_PORT")
        st.checkbox("STARTTLS / TLS", key="ALERT_SMTP_USE_TLS")
        st.checkbox("SSL", key="ALERT_SMTP_USE_SSL")

        st.text_area(
            "Empfänger",
            key="ALERT_RECIPIENTS",
            help="Mehrere Mailadressen mit Komma trennen, z. B. max@gmx.de, lisa@gmail.com",
            height=80,
        )

        st.text_input("Kaufsignal-Name", key="ALERT_BUY_SIGNAL_NAME")
        st.text_input("Portfolio-Verkaufssignal", key="ALERT_PORTFOLIO_SELL_SIGNAL_NAME")

        if alerts_config_complete():
            st.success("Mail-Konfiguration ist vollständig.")
        else:
            st.info("Mail-Konfiguration noch unvollständig oder Alerts deaktiviert.")

        if st.button("Alerts prüfen & senden", use_container_width=True, key="process_alerts_btn"):
            result = process_alerts(scan_df=scan_df, portfolio_df=portfolio_df)
            if result.get("ok"):
                st.success(result.get("message", "OK"))
            else:
                st.warning(result.get("message", "Keine neuen Signale oder Fehler"))

        st.caption("Für Streamlit Cloud später besser SMTP-Zugangsdaten in Secrets speichern.")


@st.cache_data(ttl=600, show_spinner=False)
def load_core_data(symbols_key: tuple[str, ...]) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    symbols = list(symbols_key)
    scan_df = scan_symbols(symbols, max_workers=8, fetch_live_prices=False, include_fundamentals=False)

    rohstoffe = load_universe("Rohstoffe")
    rohstoffe_df = scan_symbols(rohstoffe, max_workers=5, fetch_live_prices=False, include_fundamentals=False)

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
        top_part = result.head(50).copy()
        rest_part = result.iloc[50:].copy()
        top_part = enrich_with_live_prices(top_part)
        result = pd.concat([top_part, rest_part], ignore_index=True)

    preview_cols = [
        "symbol", "name", "wkn", "sector", "status", "analysis_price", "market_price",
        "price_gap_pct", "market_price_source", "momentum", "relative_strength",
        "rsi", "macd_trend", "volatility_pct", "trend_channel_position_pct",
        "golden_cross", "trade_score", "target_price", "stop_loss", "signal",
    ]
    show = [c for c in preview_cols if c in result.columns]
    return result[show]


with st.sidebar:
    st.markdown("## Steuerung")

    refresh = st.button("🔄 Aktualisieren", use_container_width=True)

    universe_name = st.selectbox("Aktienuniversum", get_available_universes(), index=0)
    include_europe_listings = st.checkbox("Europa Listings", value=True)
    load_portfolio_monitor = st.checkbox("Portfolio Monitor", value=True)
    add_live_prices_to_markettable = st.checkbox("Live-Kurse", value=False)
    top_n = st.selectbox("Top-Trades", [3, 5, 10], index=0)
    min_trade_score = st.slider("Mindest-Score", 0, 100, 60)

    st.markdown("---")
    st.markdown("### Portfolio-Profil")
    st.text_input(
        "Profilname",
        value=st.session_state.get("portfolio_user_key", "guest"),
        key="portfolio_user_key_input",
        help="Jedes Profil hat eine eigene Portfolio-Datei.",
    )

if refresh:
    st.cache_data.clear()

portfolio_user_key = ensure_portfolio_user_state()

st.markdown(f'<div class="app-title">{APP_NAME}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="app-subtitle">{APP_SUBTITLE}</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="app-note">Historie wird schnell gescannt, Live-Kurse werden nur gezielt nachgeladen.</div>',
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
        portfolio_df = load_portfolio_data(load_portfolio_monitor, portfolio_user_key)
        raw_portfolio_df = load_raw_portfolio_data(load_portfolio_monitor, portfolio_user_key)

        valid_scan_df = get_valid_rows(scan_df)
        valid_rohstoffe_df = get_valid_rows(rohstoffe_df)
        breadth = derive_breadth_from_scan(valid_scan_df)
        sector_df = rank_sectors(valid_scan_df)

    render_alert_sidebar(valid_scan_df, portfolio_df)

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

    if load_portfolio_monitor and portfolio_df is not None and not portfolio_df.empty:
        render_portfolio_signal_cards(portfolio_df)
        st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)

    with st.expander("Sektor Ranking anzeigen"):
        render_sector_ranking_section(sector_df)

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