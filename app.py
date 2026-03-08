import streamlit as st

from config import MARKT_INDIZES, SEKTOREN, AKTIEN_UNIVERSUM, ROHSTOFFE
from data_fetcher import lade_einzeldaten, lade_mehrere_ticker_batch
from market_analysis import analysiere_gesamtmarkt
from sector_analysis import analysiere_sektoren
from stock_scanner import scanne_aktien
from universe_loader import (
    lade_sp500_universum,
    lade_nasdaq100_universum,
    lade_dax_universum,
    lade_china_universum,
    lade_em_universum,
    kombiniere_universen
)

st.set_page_config(
    page_title="Trading Scanner 4.0",
    layout="wide"
)

# --------------------------------------------------
# CSS
# --------------------------------------------------

st.markdown(
    """
    <style>
    section[data-testid="stSidebar"] {
        background-color: #1b1f2a;
    }

    section[data-testid="stSidebar"] * {
        color: #f2f2f2;
    }

    div[data-testid="stExpander"] details {
        background: #111827;
        border: 1px solid #2d3748;
        border-radius: 12px;
    }

    div[data-testid="stExpander"] summary {
        background: #111827;
        color: #f2f2f2;
        border-radius: 12px;
    }

    div[data-testid="stExpander"] details > div {
        background: #111827;
        color: #f2f2f2;
    }

    div[data-baseweb="select"] > div {
        background-color: #111827;
        color: #f2f2f2;
    }

    div[data-baseweb="select"] input {
        color: #f2f2f2 !important;
    }

    div[data-baseweb="tag"] {
        background-color: #b91c1c !important;
        color: white !important;
    }

    .stSlider > div[data-baseweb="slider"] {
        color: #f2f2f2;
    }

    .setup-card {
        background: linear-gradient(180deg, #040816 0%, #020611 100%);
        border: 2px solid #cfcfcf;
        border-radius: 22px;
        padding: 24px 24px 22px 24px;
        min-height: 430px;
        color: #f4f4f4;
        box-shadow: 0 8px 24px rgba(0,0,0,0.18);
        margin-bottom: 14px;
    }

    .setup-dots {
        font-size: 40px;
        line-height: 1;
        margin-bottom: 18px;
    }

    .setup-ticker {
        font-size: 34px;
        font-weight: 800;
        margin-bottom: 4px;
        letter-spacing: 0.4px;
        color: #ffffff;
    }

    .setup-name {
        font-size: 18px;
        font-weight: 500;
        color: #d6d6d6;
        margin-bottom: 18px;
        line-height: 1.3;
    }

    .setup-line {
        font-size: 18px;
        line-height: 1.55;
        margin-bottom: 4px;
        color: #f2f2f2;
    }

    .setup-line strong {
        color: #ffffff;
    }

    .section-subtle {
        margin-top: -8px;
        margin-bottom: 18px;
        color: #666666;
        font-size: 14px;
    }

    div[data-testid="stMetric"] {
        background: linear-gradient(180deg, #040816 0%, #020611 100%);
        border-radius: 16px;
        padding: 12px 16px;
        border: 1px solid #2d3748;
        color: #f4f4f4;
        box-shadow: 0 6px 18px rgba(0,0,0,0.18);
    }

    div[data-testid="stMetric"] label {
        color: #cfd8e3 !important;
    }

    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #ffffff !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --------------------------------------------------
# Hilfsfunktionen
# --------------------------------------------------

def formatiere_kurs(wert):
    try:
        return f"{float(wert):.2f}"
    except Exception:
        return "-"


def formatiere_prozent(wert):
    try:
        return f"{float(wert):.2f}%"
    except Exception:
        return "-"


def bestimme_punkte_und_signaltext(signal, trade_score):
    if signal == "Kaufen" and trade_score >= 80:
        return "🟢🟢", "Neues Kaufsignal"
    elif signal == "Kaufen":
        return "🟢", "Kaufen"
    elif signal == "Beobachten":
        return "🟡", "Beobachten"
    else:
        return "🔴", "Kein Einstieg"


def rendere_setup_karte(eintrag):
    ticker = eintrag.get("ticker", "-")
    name = eintrag.get("name", "-")
    wkn = eintrag.get("wkn", "") or "-"
    signal = eintrag.get("signal", "Beobachten")
    trade_score = eintrag.get("trade_score", 0)
    kurs = formatiere_kurs(eintrag.get("aktueller_kurs", "-"))
    ziel = formatiere_kurs(eintrag.get("kursziel", "-"))
    momentum = formatiere_prozent(eintrag.get("momentum_wert", "-"))
    stop_loss = formatiere_kurs(eintrag.get("stop_loss", "-"))

    punkte, signal_text = bestimme_punkte_und_signaltext(signal, trade_score)

    karten_html = f"""
    <div class="setup-card">
        <div class="setup-dots">{punkte}</div>
        <div class="setup-ticker">{ticker}</div>
        <div class="setup-name">{name}</div>
        <div class="setup-line"><strong>WKN:</strong> {wkn}</div>
        <div class="setup-line"><strong>Signal:</strong> {signal_text}</div>
        <div class="setup-line"><strong>Trade Score:</strong> {trade_score}/100</div>
        <div class="setup-line"><strong>Kurs:</strong> {kurs}</div>
        <div class="setup-line"><strong>Ziel:</strong> {ziel}</div>
        <div class="setup-line"><strong>Momentum:</strong> {momentum}</div>
        <div class="setup-line"><strong>Stop-Loss:</strong> {stop_loss}</div>
    </div>
    """
    st.markdown(karten_html, unsafe_allow_html=True)

# --------------------------------------------------
# Titel
# --------------------------------------------------

st.title("Trading Scanner 4.0")

# --------------------------------------------------
# Sidebar
# --------------------------------------------------

with st.sidebar:
    st.header("Steuerung")

    ausgewaehlte_universen = st.multiselect(
        "Aktienuniversen auswählen",
        [
            "Nasdaq 100",
            "S&P 500",
            "DAX 40",
            "China Large Caps",
            "Entwicklungsländer"
        ],
        default=["Nasdaq 100"]
    )

    top_n = st.selectbox(
        "Anzahl Top-Trades",
        [3, 5, 10],
        index=0
    )

    mindest_score = st.slider(
        "Mindest-Trade-Score",
        min_value=0,
        max_value=100,
        value=60,
        step=5
    )

# --------------------------------------------------
# Text
# --------------------------------------------------

st.write("Systemstatus und Marktanalyse")

# --------------------------------------------------
# Marktdaten laden
# --------------------------------------------------

markt_daten = {}

for key, info in MARKT_INDIZES.items():
    ticker = info["ticker"]
    name = info["name"]

    with st.spinner(f"Lade Markt {name}..."):
        daten = lade_einzeldaten(ticker)

    if not daten.empty:
        markt_daten[key] = daten

# --------------------------------------------------
# Sektordaten laden
# --------------------------------------------------

sektor_ticker_map = {name: info["ticker"] for name, info in SEKTOREN.items()}
sektor_ticker_liste = list(sektor_ticker_map.values())

with st.spinner("Lade Sektordaten im Batch-Modus..."):
    sektor_batch = lade_mehrere_ticker_batch(sektor_ticker_liste)

sektor_daten = {}

for sektor_name, ticker in sektor_ticker_map.items():
    if ticker in sektor_batch:
        sektor_daten[sektor_name] = sektor_batch[ticker]

# --------------------------------------------------
# Universen laden
# --------------------------------------------------

universumslisten = []

if "Nasdaq 100" in ausgewaehlte_universen:
    with st.spinner("Lade Nasdaq-100-Universum..."):
        universumslisten.append(lade_nasdaq100_universum())

if "S&P 500" in ausgewaehlte_universen:
    with st.spinner("Lade S&P-500-Universum..."):
        universumslisten.append(lade_sp500_universum())

if "DAX 40" in ausgewaehlte_universen:
    with st.spinner("Lade DAX-40-Universum..."):
        universumslisten.append(lade_dax_universum())

if "China Large Caps" in ausgewaehlte_universen:
    with st.spinner("Lade China-Universum..."):
        universumslisten.append(lade_china_universum())

if "Entwicklungsländer" in ausgewaehlte_universen:
    with st.spinner("Lade EM-Universum..."):
        universumslisten.append(lade_em_universum())

if universumslisten:
    aktien_liste = kombiniere_universen(universumslisten)

    if not aktien_liste:
        st.warning("Universum leer – nutze Fallback-Liste.")
        aktien_liste = AKTIEN_UNIVERSUM
else:
    aktien_liste = AKTIEN_UNIVERSUM

# --------------------------------------------------
# Aktiendaten laden
# --------------------------------------------------

aktien_ticker = [aktie["ticker"] for aktie in aktien_liste]

with st.spinner(f"Lade {len(aktien_ticker)} Aktien im Batch-Modus..."):
    aktien_daten = lade_mehrere_ticker_batch(aktien_ticker)

# --------------------------------------------------
# Rohstoffdaten laden
# --------------------------------------------------

rohstoff_ticker = [rohstoff["ticker"] for rohstoff in ROHSTOFFE]

with st.spinner("Lade Rohstoffdaten im Batch-Modus..."):
    rohstoff_daten = lade_mehrere_ticker_batch(rohstoff_ticker)

# --------------------------------------------------
# Analysen
# --------------------------------------------------

analyse = analysiere_gesamtmarkt(markt_daten)
sektor_analyse = analysiere_sektoren(sektor_daten)

aktien_ranking = scanne_aktien(
    aktien_daten,
    sektor_analyse,
    markt_daten,
    aktien_liste
)

rohstoff_ranking = scanne_aktien(
    rohstoff_daten,
    sektor_analyse,
    markt_daten,
    ROHSTOFFE
)

# --------------------------------------------------
# Score Filter
# --------------------------------------------------

aktien_ranking = [
    eintrag for eintrag in aktien_ranking
    if eintrag.get("trade_score", 0) >= mindest_score
]

rohstoff_ranking = [
    eintrag for eintrag in rohstoff_ranking
    if eintrag.get("trade_score", 0) >= mindest_score
]

# --------------------------------------------------
# Marktübersicht
# --------------------------------------------------

st.header("Marktübersicht")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Marktstatus", analyse.get("marktstatus", "-"))

with col2:
    st.metric("Crashrisiko", analyse.get("crashrisiko", "-"))

with col3:
    if sektor_analyse.get("top_sektor"):
        sektor = sektor_analyse["top_sektor"]["sektor"]
        score = sektor_analyse["top_sektor"]["score"]
        st.metric("Top Sektor", f"{sektor} ({score}/4)")
    else:
        st.metric("Top Sektor", "Keine Daten")

with col4:
    st.metric("Ausstiegssignal", analyse.get("ausstieg", "-"))

st.write(f"Geladene Aktien im Scanner: {len(aktien_liste)}")

# --------------------------------------------------
# Top Trading Setups
# --------------------------------------------------

st.header(f"Top {top_n} Trading Setups")
st.markdown(
    '<div class="section-subtle">Die wichtigsten Signale kompakt und klar dargestellt.</div>',
    unsafe_allow_html=True
)

top_aktien = aktien_ranking[:top_n]

if top_aktien:
    if top_n <= 3:
        spalten = st.columns(top_n)
    else:
        spalten = st.columns(3)

    for i, aktie in enumerate(top_aktien):
        with spalten[i % len(spalten)]:
            rendere_setup_karte(aktie)
else:
    st.write("Keine Aktienergebnisse verfügbar.")

# --------------------------------------------------
# Top Rohstoff Setups
# --------------------------------------------------

st.header("Top 3 Rohstoff Setups")

top_rohstoffe = rohstoff_ranking[:3]

if top_rohstoffe:
    rohstoff_spalten = st.columns(3)

    for i, rohstoff in enumerate(top_rohstoffe):
        with rohstoff_spalten[i]:
            rendere_setup_karte(rohstoff)
else:
    st.write("Keine Rohstoffergebnisse verfügbar.")

# --------------------------------------------------
# Sektor Ranking
# --------------------------------------------------

with st.expander("Sektor Ranking anzeigen"):
    if sektor_analyse.get("ranking"):
        for eintrag in sektor_analyse["ranking"]:
            sektor = eintrag["sektor"]
            score = eintrag["score"]
            st.write(f"{sektor}: {score} / 4")
    else:
        st.write("Keine Sektordaten verfügbar.")

# --------------------------------------------------
# Marktcharts
# --------------------------------------------------

with st.expander("Marktcharts anzeigen"):
    for key, info in MARKT_INDIZES.items():
        name = info["name"]
        region = info["region"]

        st.subheader(f"{name} ({region})")

        if key not in markt_daten:
            st.write("❌ Keine Daten geladen")
            continue

        daten = markt_daten[key]

        try:
            letzter_kurs = float(daten["Close"].iloc[-1])
            st.write(f"Aktueller Kurs: {letzter_kurs:.2f}")
        except Exception:
            st.write("Aktueller Kurs: -")

        if key in analyse.get("details", {}):
            detail = analyse["details"][key]

            st.write(f"Score: {detail['score']} / 3")
            st.write(f"Kurs über SMA50: {'Ja' if detail['kurs_ueber_sma50'] else 'Nein'}")
            st.write(f"Kurs über SMA200: {'Ja' if detail['kurs_ueber_sma200'] else 'Nein'}")
            st.write(f"SMA50 über SMA200: {'Ja' if detail['sma50_ueber_sma200'] else 'Nein'}")

        st.line_chart(daten["Close"])