import pandas as pd
import yfinance as yf
import streamlit as st

from config import ZEITRAUM_STANDARD, INTERVALL_STANDARD


# --------------------------------------------------
# Einzelne Aktie laden
# --------------------------------------------------

@st.cache_data(ttl=3600)
def lade_einzeldaten(
    ticker,
    zeitraum=ZEITRAUM_STANDARD,
    intervall=INTERVALL_STANDARD
):

    try:

        daten = yf.download(
            tickers=ticker,
            period=zeitraum,
            interval=intervall,
            progress=False,
            auto_adjust=False,
            threads=False
        )

        if daten is None or daten.empty:
            return pd.DataFrame()

        daten = daten.dropna(how="all")

        return daten

    except Exception as e:

        print(f"Fehler beim Laden von {ticker}: {e}")

        return pd.DataFrame()


# --------------------------------------------------
# Mehrere Ticker laden (Batch + Blockweise)
# --------------------------------------------------

@st.cache_data(ttl=3600)
def lade_mehrere_ticker_batch(
    ticker_liste,
    zeitraum=ZEITRAUM_STANDARD,
    intervall=INTERVALL_STANDARD,
    batch_size=50
):

    ergebnisse = {}

    if not ticker_liste:
        return ergebnisse

    # Duplikate entfernen
    bereinigte_ticker = list(set(ticker_liste))

    # In Blöcken laden
    for i in range(0, len(bereinigte_ticker), batch_size):

        batch = bereinigte_ticker[i:i + batch_size]

        try:

            daten = yf.download(
                tickers=batch,
                period=zeitraum,
                interval=intervall,
                group_by="ticker",
                threads=True,
                progress=False,
                auto_adjust=False
            )

            if daten is None or daten.empty:
                continue

            # Spezialfall: nur 1 Ticker
            if len(batch) == 1:

                ticker = batch[0]

                ticker_df = daten.dropna(how="all")

                if not ticker_df.empty:
                    ergebnisse[ticker] = ticker_df

                continue

            # Mehrere Ticker
            for ticker in batch:

                try:

                    if ticker not in daten.columns.get_level_values(0):
                        continue

                    ticker_df = daten[ticker].copy()

                    ticker_df = ticker_df.dropna(how="all")

                    if ticker_df.empty:
                        continue

                    ticker_df = ticker_df.dropna(axis=1, how="all")

                    if ticker_df.empty:
                        continue

                    ergebnisse[ticker] = ticker_df

                except Exception:

                    continue

        except Exception as e:

            print("Batch Fehler:", e)

            continue

    return ergebnisse


# --------------------------------------------------
# Kompatibilitätsfunktion
# --------------------------------------------------

def lade_mehrere_ticker(
    ticker_liste,
    zeitraum=ZEITRAUM_STANDARD,
    intervall=INTERVALL_STANDARD
):

    return lade_mehrere_ticker_batch(
        ticker_liste,
        zeitraum,
        intervall
    )


# --------------------------------------------------
# Hilfsfunktion: Ticker extrahieren
# --------------------------------------------------

def extrahiere_ticker_aus_liste(eintraege):

    ticker_liste = []

    for eintrag in eintraege:

        if not isinstance(eintrag, dict):
            continue

        if "ticker" not in eintrag:
            continue

        ticker = str(eintrag["ticker"]).strip()

        if ticker:
            ticker_liste.append(ticker)

    return ticker_liste