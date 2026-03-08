import streamlit as st

from config import (
    NASDAQ100_AKTIEN,
    SP500_PROXY_AKTIEN,
    DAX_AKTIEN,
    CHINA_PROXY_AKTIEN,
    EM_PROXY_AKTIEN
)


# --------------------------------------------------
# Nasdaq 100
# --------------------------------------------------

@st.cache_data(ttl=86400)
def lade_nasdaq100_universum():
    """
    Nutzt die feste Nasdaq-100-Fallback-Liste aus config.py
    """
    return NASDAQ100_AKTIEN


# --------------------------------------------------
# S&P 500
# --------------------------------------------------

@st.cache_data(ttl=86400)
def lade_sp500_universum():
    """
    Nutzt die feste S&P-500-Proxy-Liste aus config.py
    """
    return SP500_PROXY_AKTIEN


# --------------------------------------------------
# DAX
# --------------------------------------------------

@st.cache_data(ttl=86400)
def lade_dax_universum():
    """
    Nutzt die feste DAX-Liste aus config.py
    """
    return DAX_AKTIEN


# --------------------------------------------------
# China
# --------------------------------------------------

@st.cache_data(ttl=86400)
def lade_china_universum():
    """
    Nutzt die feste China-Proxy-Liste aus config.py
    """
    return CHINA_PROXY_AKTIEN


# --------------------------------------------------
# Emerging Markets
# --------------------------------------------------

@st.cache_data(ttl=86400)
def lade_em_universum():
    """
    Nutzt die feste Emerging-Markets-Proxy-Liste aus config.py
    """
    return EM_PROXY_AKTIEN


# --------------------------------------------------
# Universen kombinieren
# --------------------------------------------------

def kombiniere_universen(lists_of_dicts):
    """
    Führt mehrere Universen zusammen und entfernt doppelte Ticker.
    """
    gesammelt = {}

    for liste in lists_of_dicts:
        for eintrag in liste:
            ticker = str(eintrag.get("ticker", "")).strip()

            if not ticker:
                continue

            if ticker not in gesammelt:
                gesammelt[ticker] = eintrag

    return list(gesammelt.values())