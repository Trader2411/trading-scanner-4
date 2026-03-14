from __future__ import annotations

import json
import smtplib
import ssl
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st

from config import (
    ALERTS_DIR,
    ALERT_BUY_SIGNAL_NAME,
    ALERT_ENABLED,
    ALERT_FROM_EMAIL,
    ALERT_FROM_NAME,
    ALERT_PORTFOLIO_SELL_SIGNAL_NAME,
    ALERT_RECIPIENTS,
    ALERT_SMTP_HOST,
    ALERT_SMTP_PASSWORD,
    ALERT_SMTP_PORT,
    ALERT_SMTP_USE_SSL,
    ALERT_SMTP_USE_TLS,
    ALERT_SMTP_USERNAME,
)


APP_ALERT_LABEL = "Trading Scanner 4.4"

ALERTS_STATE_FILE = ALERTS_DIR / "alerts_state.json"
ALERTS_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# Konfig / Priorität:
# session_state > st.secrets > config.py
# ============================================================

def _value_from_sources(key: str, fallback):
    try:
        if key in st.session_state and st.session_state[key] not in [None, ""]:
            return st.session_state[key]
    except Exception:
        pass

    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass

    return fallback


def _clean_str(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalize_recipients(recipients) -> List[str]:
    if recipients is None:
        return []

    if isinstance(recipients, str):
        raw = [x.strip() for x in recipients.split(",")]
        return [x for x in raw if x]

    if isinstance(recipients, (list, tuple, set)):
        result = []
        for item in recipients:
            text = str(item).strip()
            if text:
                result.append(text)
        return result

    return []


def get_alert_settings() -> Dict:
    recipients = _value_from_sources("ALERT_RECIPIENTS", ALERT_RECIPIENTS)

    smtp_username = _clean_str(_value_from_sources("ALERT_SMTP_USERNAME", ALERT_SMTP_USERNAME))
    from_email = _clean_str(_value_from_sources("ALERT_FROM_EMAIL", ALERT_FROM_EMAIL))
    from_name = _clean_str(_value_from_sources("ALERT_FROM_NAME", ALERT_FROM_NAME)) or APP_ALERT_LABEL

    if not smtp_username and from_email:
        smtp_username = from_email

    if not from_email and smtp_username:
        from_email = smtp_username

    settings = {
        "enabled": bool(_value_from_sources("ALERT_ENABLED", ALERT_ENABLED)),
        "smtp_host": _clean_str(_value_from_sources("ALERT_SMTP_HOST", ALERT_SMTP_HOST)),
        "smtp_port": int(_value_from_sources("ALERT_SMTP_PORT", ALERT_SMTP_PORT)),
        "smtp_username": smtp_username,
        "smtp_password": _clean_str(_value_from_sources("ALERT_SMTP_PASSWORD", ALERT_SMTP_PASSWORD)),
        "smtp_use_tls": bool(_value_from_sources("ALERT_SMTP_USE_TLS", ALERT_SMTP_USE_TLS)),
        "smtp_use_ssl": bool(_value_from_sources("ALERT_SMTP_USE_SSL", ALERT_SMTP_USE_SSL)),
        "from_email": from_email,
        "from_name": from_name,
        "recipients": _normalize_recipients(recipients),
        "buy_signal_name": _clean_str(_value_from_sources("ALERT_BUY_SIGNAL_NAME", ALERT_BUY_SIGNAL_NAME)),
        "portfolio_sell_signal_name": _clean_str(
            _value_from_sources(
                "ALERT_PORTFOLIO_SELL_SIGNAL_NAME",
                ALERT_PORTFOLIO_SELL_SIGNAL_NAME,
            )
        ),
    }

    return settings


def alerts_config_complete() -> bool:
    settings = get_alert_settings()
    return bool(
        settings["enabled"]
        and settings["smtp_host"]
        and settings["smtp_port"]
        and settings["smtp_username"]
        and settings["smtp_password"]
        and settings["from_email"]
        and settings["recipients"]
    )


# ============================================================
# Hilfsfunktionen
# ============================================================

def _utc_now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _safe_float(value) -> Optional[float]:
    try:
        if value is None or pd.isna(value):
            return None
        return float(value)
    except Exception:
        return None


def _normalize_symbol(value) -> str:
    if value is None:
        return ""
    return str(value).strip().upper()


def _state_template() -> Dict:
    return {
        "buy_alerts_sent": {},
        "sell_alerts_sent": {},
        "last_run": None,
    }


def load_alert_state() -> Dict:
    if not ALERTS_STATE_FILE.exists():
        return _state_template()

    try:
        with open(ALERTS_STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            return _state_template()

        result = _state_template()
        result.update(data)

        if not isinstance(result.get("buy_alerts_sent"), dict):
            result["buy_alerts_sent"] = {}
        if not isinstance(result.get("sell_alerts_sent"), dict):
            result["sell_alerts_sent"] = {}

        return result
    except Exception:
        return _state_template()


def save_alert_state(state: Dict) -> None:
    state = state or _state_template()
    state["last_run"] = _utc_now_iso()

    with open(ALERTS_STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def _fmt(value, digits: int = 2, suffix: str = "") -> str:
    if value is None:
        return "-"
    return f"{float(value):.{digits}f}{suffix}"


# ============================================================
# Portfolio-Hinweiskarten in der App
# ============================================================

def render_portfolio_signal_cards(portfolio_df: pd.DataFrame) -> None:
    if portfolio_df is None or portfolio_df.empty:
        return

    df = portfolio_df.copy()

    if "exit_signal" not in df.columns:
        return

    settings = get_alert_settings()
    sell_signal_name = str(settings["portfolio_sell_signal_name"]).strip()

    df = df[df["exit_signal"].astype(str) == sell_signal_name].copy()
    if df.empty:
        return

    st.header("Wichtige Hinweise")

    for _, row in df.iterrows():
        symbol = str(row.get("symbol", "-")).strip().upper() or "-"
        market_price = _safe_float(row.get("market_price"))
        pnl_pct = _safe_float(row.get("pnl_pct"))
        trailing_stop = _safe_float(row.get("trailing_stop"))
        stop_loss = _safe_float(row.get("stop_loss"))
        reason = str(row.get("signal_reason", "")).strip() or "Verkaufssignal erkannt"

        stop_text = _fmt(trailing_stop) if trailing_stop is not None else _fmt(stop_loss)

        st.markdown(
            f"""
<div style="
    background: linear-gradient(180deg, #071225 0%, #0b1730 100%);
    color: white;
    border-radius: 18px;
    padding: 1rem;
    box-shadow: 0 6px 18px rgba(7, 18, 37, 0.14);
    margin-bottom: 14px;
">
    <div style="margin-bottom: 8px;">
        <span style="
            display:inline-block;
            background:#ef4444;
            color:white;
            border-radius:999px;
            padding:0.2rem 0.6rem;
            font-size:0.75rem;
            font-weight:700;
        ">Verkaufen</span>
    </div>
    <div style="font-size:1.3rem;font-weight:800;margin-bottom:0.3rem;">{symbol}</div>
    <div style="font-size:0.92rem;line-height:1.45;">
        Kurs: {_fmt(market_price)}<br>
        PnL: {_fmt(pnl_pct, 2, "%")}<br>
        Trailing: {stop_text}<br>
        {reason}
    </div>
</div>
""",
            unsafe_allow_html=True,
        )


# ============================================================
# Signal-Extraktion
# ============================================================

def extract_new_buy_signals(scan_df: pd.DataFrame, state: Dict) -> List[Dict]:
    if scan_df is None or scan_df.empty:
        return []

    settings = get_alert_settings()
    buy_signal_name = str(settings["buy_signal_name"]).strip()
    state_buy = state.get("buy_alerts_sent", {}) if isinstance(state, dict) else {}

    result: List[Dict] = []
    df = scan_df.copy()

    if "status" in df.columns:
        df = df[df["status"] == "ok"]

    if "signal" not in df.columns:
        return []

    df["symbol"] = df["symbol"].astype(str).str.upper()
    df = df[df["signal"].astype(str) == buy_signal_name]

    for _, row in df.iterrows():
        symbol = _normalize_symbol(row.get("symbol"))
        signal = str(row.get("signal", "")).strip()
        score = _safe_float(row.get("trade_score"))
        if not symbol:
            continue

        unique_key = f"{symbol}|{signal}|{int(score) if score is not None else 'na'}"
        if unique_key in state_buy:
            continue

        result.append(
            {
                "key": unique_key,
                "symbol": symbol,
                "name": row.get("name"),
                "wkn": row.get("wkn"),
                "signal": signal,
                "trade_score": score,
                "analysis_price": _safe_float(row.get("analysis_price")),
                "market_price": _safe_float(row.get("market_price")),
                "target_price": _safe_float(row.get("target_price")),
                "stop_loss": _safe_float(row.get("stop_loss")),
            }
        )

    return result


def extract_new_sell_signals(portfolio_df: pd.DataFrame, state: Dict) -> List[Dict]:
    if portfolio_df is None or portfolio_df.empty:
        return []

    settings = get_alert_settings()
    sell_signal_name = str(settings["portfolio_sell_signal_name"]).strip()
    state_sell = state.get("sell_alerts_sent", {}) if isinstance(state, dict) else {}

    result: List[Dict] = []
    df = portfolio_df.copy()

    if "exit_signal" not in df.columns:
        return []

    df["symbol"] = df["symbol"].astype(str).str.upper()
    df = df[df["exit_signal"].astype(str) == sell_signal_name]

    for _, row in df.iterrows():
        symbol = _normalize_symbol(row.get("symbol"))
        signal = str(row.get("exit_signal", "")).strip()
        if not symbol:
            continue

        unique_key = f"{symbol}|{signal}|{row.get('signal_reason', '')}"
        if unique_key in state_sell:
            continue

        result.append(
            {
                "key": unique_key,
                "symbol": symbol,
                "buy_price": _safe_float(row.get("buy_price")),
                "market_price": _safe_float(row.get("market_price")),
                "pnl_pct": _safe_float(row.get("pnl_pct")),
                "stop_loss": _safe_float(row.get("stop_loss")),
                "trailing_stop": _safe_float(row.get("trailing_stop")),
                "signal_reason": row.get("signal_reason"),
                "exit_signal": signal,
            }
        )

    return result


# ============================================================
# Mail-Inhalte
# ============================================================

def build_buy_alert_email(signals: List[Dict]) -> Tuple[str, str, str]:
    subject = f"{APP_ALERT_LABEL}: {len(signals)} neue Kaufsignale"

    text_lines = [
        f"{APP_ALERT_LABEL} – neue Kaufsignale",
        "",
    ]
    html_rows = []

    for item in signals:
        line = (
            f"{item.get('symbol')} | "
            f"Signal: {item.get('signal')} | "
            f"Score: {_fmt(item.get('trade_score'), 0)} | "
            f"Preis: {_fmt(item.get('market_price') or item.get('analysis_price'))} | "
            f"Ziel: {_fmt(item.get('target_price'))} | "
            f"Stop: {_fmt(item.get('stop_loss'))}"
        )
        text_lines.append(line)

        html_rows.append(
            f"""
<tr>
    <td>{item.get("symbol")}</td>
    <td>{item.get("signal")}</td>
    <td>{_fmt(item.get("trade_score"), 0)}</td>
    <td>{_fmt(item.get("market_price") or item.get("analysis_price"))}</td>
    <td>{_fmt(item.get("target_price"))}</td>
    <td>{_fmt(item.get("stop_loss"))}</td>
</tr>
"""
        )

    html_body = f"""
<html>
<body>
<h3>{APP_ALERT_LABEL} – neue Kaufsignale</h3>
<table border="1" cellpadding="6" cellspacing="0">
<tr>
    <th>Symbol</th>
    <th>Signal</th>
    <th>Score</th>
    <th>Preis</th>
    <th>Ziel</th>
    <th>Stop</th>
</tr>
{''.join(html_rows)}
</table>
</body>
</html>
"""
    text_body = "\n".join(text_lines)
    return subject, html_body, text_body


def build_sell_alert_email(signals: List[Dict]) -> Tuple[str, str, str]:
    subject = f"{APP_ALERT_LABEL}: {len(signals)} neue Verkaufssignale"

    text_lines = [
        f"{APP_ALERT_LABEL} – neue Verkaufssignale",
        "",
    ]
    html_rows = []

    for item in signals:
        line = (
            f"{item.get('symbol')} | "
            f"Signal: {item.get('exit_signal')} | "
            f"Kurs: {_fmt(item.get('market_price'))} | "
            f"PnL: {_fmt(item.get('pnl_pct'), 2, '%')} | "
            f"Trailing: {_fmt(item.get('trailing_stop'))} | "
            f"Grund: {item.get('signal_reason') or '-'}"
        )
        text_lines.append(line)

        html_rows.append(
            f"""
<tr>
    <td>{item.get("symbol")}</td>
    <td>{item.get("exit_signal")}</td>
    <td>{_fmt(item.get("market_price"))}</td>
    <td>{_fmt(item.get("pnl_pct"), 2, "%")}</td>
    <td>{_fmt(item.get("trailing_stop"))}</td>
    <td>{item.get("signal_reason") or "-"}</td>
</tr>
"""
        )

    html_body = f"""
<html>
<body>
<h3>{APP_ALERT_LABEL} – neue Verkaufssignale</h3>
<table border="1" cellpadding="6" cellspacing="0">
<tr>
    <th>Symbol</th>
    <th>Signal</th>
    <th>Kurs</th>
    <th>PnL</th>
    <th>Trailing</th>
    <th>Grund</th>
</tr>
{''.join(html_rows)}
</table>
</body>
</html>
"""
    text_body = "\n".join(text_lines)
    return subject, html_body, text_body


# ============================================================
# Mailversand
# ============================================================

def send_email(subject: str, html_body: str, text_body: str) -> Tuple[bool, str]:
    settings = get_alert_settings()

    if not alerts_config_complete():
        return False, "Mail-Konfiguration unvollständig"

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f'{settings["from_name"]} <{settings["from_email"]}>'
        msg["To"] = ", ".join(settings["recipients"])

        msg.attach(MIMEText(text_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        if settings["smtp_use_ssl"]:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(
                settings["smtp_host"],
                settings["smtp_port"],
                context=context,
            ) as server:
                server.login(settings["smtp_username"], settings["smtp_password"])
                server.sendmail(settings["from_email"], settings["recipients"], msg.as_string())
        else:
            with smtplib.SMTP(settings["smtp_host"], settings["smtp_port"]) as server:
                if settings["smtp_use_tls"]:
                    context = ssl.create_default_context()
                    server.starttls(context=context)
                server.login(settings["smtp_username"], settings["smtp_password"])
                server.sendmail(settings["from_email"], settings["recipients"], msg.as_string())

        return True, "gesendet"
    except Exception as e:
        return False, str(e)


# ============================================================
# Hauptfunktion
# ============================================================

def process_alerts(
    scan_df: Optional[pd.DataFrame] = None,
    portfolio_df: Optional[pd.DataFrame] = None,
) -> Dict:
    settings = get_alert_settings()

    if not settings["enabled"]:
        return {
            "ok": False,
            "message": "Alerts sind deaktiviert",
            "buy_signals": 0,
            "sell_signals": 0,
        }

    state = load_alert_state()

    new_buy_signals = extract_new_buy_signals(scan_df, state) if scan_df is not None else []
    new_sell_signals = extract_new_sell_signals(portfolio_df, state) if portfolio_df is not None else []

    sent_messages = []
    success = True

    if new_buy_signals:
        subject, html_body, text_body = build_buy_alert_email(new_buy_signals)
        ok, msg = send_email(subject, html_body, text_body)
        sent_messages.append(f"Kaufsignale: {msg}")
        success = success and ok

        if ok:
            for item in new_buy_signals:
                state["buy_alerts_sent"][item["key"]] = _utc_now_iso()

    if new_sell_signals:
        subject, html_body, text_body = build_sell_alert_email(new_sell_signals)
        ok, msg = send_email(subject, html_body, text_body)
        sent_messages.append(f"Verkaufssignale: {msg}")
        success = success and ok

        if ok:
            for item in new_sell_signals:
                state["sell_alerts_sent"][item["key"]] = _utc_now_iso()

    save_alert_state(state)

    return {
        "ok": success,
        "message": " | ".join(sent_messages) if sent_messages else "Keine neuen Signale",
        "buy_signals": len(new_buy_signals),
        "sell_signals": len(new_sell_signals),
    }