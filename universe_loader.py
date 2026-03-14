from __future__ import annotations

from typing import Dict, List
import copy


# ============================================================
# Universumsnamen
# ============================================================

ALL_UNIVERSE_NAME = "Alle"
NASDAQ_UNIVERSE_NAME = "Nasdaq 100"
SP500_UNIVERSE_NAME = "S&P 500"
EUROPE_UNIVERSE_NAME = "Europa Listings"
EM_UNIVERSE_NAME = "Emerging Markets"
SMALL_CAP_UNIVERSE_NAME = "Small Caps"
COMMODITIES_UNIVERSE_NAME = "Rohstoffe"
TOP_LIQUID_UNIVERSE_NAME = "Top Liquid USA"
US_LARGE_CAP_UNIVERSE_NAME = "US Large Caps"


# ============================================================
# Symbol-Universen
# ============================================================

NASDAQ_100_SYMBOLS: List[str] = [
    "AAPL", "ABNB", "ADBE", "ADI", "ADP", "ADSK", "AEP", "AMAT", "AMD", "AMGN",
    "AMZN", "ANSS", "APP", "ARM", "ASML", "AVGO", "AXON", "AZN", "BIIB", "BKNG",
    "BKR", "CDNS", "CEG", "CHTR", "CMCSA", "COST", "CPRT", "CRWD", "CSCO", "CSX",
    "CTAS", "DDOG", "DLTR", "DXCM", "EA", "EXC", "FANG", "FAST", "FTNT", "GFS",
    "GILD", "GOOG", "GOOGL", "HON", "IDXX", "INTC", "INTU", "ISRG", "KDP", "KHC",
    "KLAC", "LIN", "LRCX", "LULU", "MAR", "MCHP", "MDB", "MDLZ", "MELI", "META",
    "MNST", "MRVL", "MSFT", "MU", "NFLX", "NVDA", "ODFL", "ON", "ORLY", "PANW",
    "PAYX", "PCAR", "PDD", "PEP", "PLTR", "PYPL", "QCOM", "REGN", "ROST", "SBUX",
    "SNPS", "TEAM", "TMUS", "TSLA", "TTD", "TTWO", "TXN", "VRTX", "WBD", "WDAY",
    "XEL", "ZS",
]

SP500_SYMBOLS: List[str] = [
    "AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "GOOG", "BRK-B", "LLY", "AVGO",
    "JPM", "V", "XOM", "UNH", "MA", "PG", "COST", "HD", "MRK", "ABBV",
    "KO", "PEP", "ADBE", "CRM", "INTU", "NOW", "TMO", "ACN", "WMT", "LIN",
    "CSCO", "DHR", "TXN", "MCD", "ABT", "PM", "NEE", "ORCL", "UPS", "LOW",
    "SPGI", "AMD", "HON", "AMGN", "IBM", "GS", "RTX", "BLK", "MS", "GE",
    "BA", "DE", "CVX", "T", "VZ", "F", "GM", "UBER", "BKNG", "AMAT",
    "QCOM", "NFLX", "PANW", "ISRG", "ADI", "LRCX", "KLAC", "MU", "MDT", "SYK",
    "C", "SCHW", "MMC", "PGR", "AXP", "CB", "COP", "SLB", "EOG", "SO",
    "DUK", "VRTX", "GILD", "REGN", "ZTS", "BSX", "TJX", "NKE", "TGT", "CMCSA",
    "DIS", "TMUS", "PLD", "ADP", "MO", "LMT", "INTC", "CAT", "ETN", "CI",
    "HCA", "ELV", "CVS", "PFE", "BMY", "PYPL", "KKR", "BX", "AON", "ICE",
]

EUROPE_SYMBOLS: List[str] = [
    "ASML.AS", "ADYEN.AS", "PRX.AS", "PHIA.AS", "INGA.AS", "WKL.AS", "RAND.AS",
    "MC.PA", "OR.PA", "AI.PA", "SAN.PA", "RMS.PA", "DG.PA", "SU.PA", "BN.PA",
    "AIR.PA", "CAP.PA", "GLE.PA", "BNP.PA", "ACA.PA", "ENGI.PA", "KER.PA", "CS.PA",
    "EL.PA", "RI.PA", "STM.PA",
    "NESN.SW", "ROG.SW", "NOVN.SW", "ABBN.SW", "SCMN.SW", "UHR.SW", "ZURN.SW",
    "SHEL.L", "AZN.L", "ULVR.L", "BP.L", "RIO.L", "BATS.L", "DGE.L", "REL.L",
    "GSK.L", "HSBA.L", "BARC.L", "LSEG.L", "NG.L", "RR.L", "AAL.L",
    "ENI.MI", "ISP.MI", "ENEL.MI", "RACE.MI",
    "IBE.MC", "ITX.MC", "SAN.MC", "BBVA.MC", "FER.MC", "AMS.MC",
    "NOKIA.HE", "KNEBV.HE", "NDA-FI.HE",
]

EM_SYMBOLS: List[str] = [
    "TSM", "INFY", "VALE", "PBR", "ITUB", "HDB", "MELI", "NU", "BAP", "WIT",
    "SBSW", "GFI", "EC", "CIB", "YPF", "BBD", "AU", "SSL", "ASX",
    "BABA", "JD", "PDD", "BIDU", "TME", "NTES", "LI", "NIO", "XPEV",
]

SMALL_CAP_SYMBOLS: List[str] = [
    "UPWK", "FVRR", "SOFI", "PLUG", "RUN", "OPEN", "LMND", "AFRM", "HOOD",
    "COIN", "ASTS", "RKLB", "IONQ", "DNA", "BBAI", "SOUN", "JOBY", "ACHR",
    "ENVX", "QS", "LAZR", "SPCE", "U", "PATH", "DOCN", "CELH", "ONON",
]

COMMODITY_SYMBOLS: List[str] = [
    "GC=F",
    "SI=F",
    "PL=F",
    "PA=F",
    "CL=F",
    "BZ=F",
    "NG=F",
    "HG=F",
    "ZW=F",
    "ZC=F",
    "ZS=F",
    "KC=F",
    "SB=F",
    "CC=F",
]

TOP_LIQUID_USA_SYMBOLS: List[str] = [
    "AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "GOOG", "TSLA", "AMD", "NFLX",
    "AVGO", "QCOM", "MU", "INTC", "PLTR", "ARM", "ADBE", "CRM", "ORCL", "CSCO",
    "AMAT", "LRCX", "KLAC", "PANW", "CRWD", "DDOG", "SHOP", "UBER", "ABNB", "SNOW",
    "JPM", "V", "MA", "GS", "MS", "AXP", "BLK", "SCHW", "BAC", "C",
    "XOM", "CVX", "COP", "SLB", "EOG", "FANG", "OXY",
    "LLY", "UNH", "ABBV", "MRK", "PFE", "TMO", "ISRG", "BSX", "SYK", "MDT",
    "WMT", "COST", "HD", "LOW", "NKE", "SBUX", "MCD", "PEP", "KO", "PG",
    "CAT", "DE", "GE", "RTX", "LMT", "ETN", "HON", "PH",
    "TMUS", "VZ", "T", "CMCSA", "DIS", "PYPL", "COIN", "HOOD", "SOFI", "AFRM",
]

US_LARGE_CAP_SYMBOLS: List[str] = sorted(list({
    *NASDAQ_100_SYMBOLS,
    *SP500_SYMBOLS,
    *TOP_LIQUID_USA_SYMBOLS,
    "SNOW", "SHOP", "ANET", "MSTR", "RIVN", "SMCI", "NET", "MDB",
    "NOW", "WDAY", "TEAM", "APP", "CEG", "KKR", "BX", "APO",
    "TJX", "ADP", "PGR", "MMC", "CB", "AON", "ICE", "SPGI",
}))


# ============================================================
# Metadaten
# ============================================================

COMMODITY_META: Dict[str, Dict[str, str]] = {
    "GC=F": {"name": "Gold", "wkn": "-", "sector": "Metals"},
    "SI=F": {"name": "Silber", "wkn": "-", "sector": "Metals"},
    "PL=F": {"name": "Platin", "wkn": "-", "sector": "Metals"},
    "PA=F": {"name": "Palladium", "wkn": "-", "sector": "Metals"},
    "CL=F": {"name": "WTI Rohöl", "wkn": "-", "sector": "Energy"},
    "BZ=F": {"name": "Brent Rohöl", "wkn": "-", "sector": "Energy"},
    "NG=F": {"name": "Erdgas", "wkn": "-", "sector": "Energy"},
    "HG=F": {"name": "Kupfer", "wkn": "-", "sector": "Metals"},
    "ZW=F": {"name": "Weizen", "wkn": "-", "sector": "Agriculture"},
    "ZC=F": {"name": "Mais", "wkn": "-", "sector": "Agriculture"},
    "ZS=F": {"name": "Sojabohnen", "wkn": "-", "sector": "Agriculture"},
    "KC=F": {"name": "Kaffee", "wkn": "-", "sector": "Agriculture"},
    "SB=F": {"name": "Zucker", "wkn": "-", "sector": "Agriculture"},
    "CC=F": {"name": "Kakao", "wkn": "-", "sector": "Agriculture"},
}

SYMBOL_META: Dict[str, Dict[str, str]] = {
    "SSL": {"name": "Sasol", "wkn": "865164", "sector": "Energy"},
    "NOKIA.HE": {"name": "Nokia", "wkn": "-", "sector": "Technology"},
    "ENI.MI": {"name": "Eni", "wkn": "897791", "sector": "Energy"},
    "SHEL.L": {"name": "Shell plc", "wkn": "-", "sector": "Energy"},
    "ASML.AS": {"name": "ASML", "wkn": "-", "sector": "Technology"},
    "MC.PA": {"name": "LVMH", "wkn": "-", "sector": "Luxury"},
    "RACE.MI": {"name": "Ferrari", "wkn": "-", "sector": "Automotive"},

    "AAPL": {"name": "Apple", "wkn": "865985", "sector": "Technology"},
    "MSFT": {"name": "Microsoft", "wkn": "870747", "sector": "Technology"},
    "NVDA": {"name": "NVIDIA", "wkn": "918422", "sector": "Technology"},
    "AMZN": {"name": "Amazon", "wkn": "906866", "sector": "Consumer"},
    "META": {"name": "Meta Platforms", "wkn": "-", "sector": "Technology"},
    "GOOGL": {"name": "Alphabet A", "wkn": "A14Y6F", "sector": "Technology"},
    "GOOG": {"name": "Alphabet C", "wkn": "A14Y6H", "sector": "Technology"},
    "TSLA": {"name": "Tesla", "wkn": "A1CX3T", "sector": "Automotive"},
    "AMD": {"name": "AMD", "wkn": "863186", "sector": "Technology"},
    "NFLX": {"name": "Netflix", "wkn": "552484", "sector": "Communication"},
    "PLTR": {"name": "Palantir", "wkn": "A2QA4J", "sector": "Technology"},
    "COIN": {"name": "Coinbase", "wkn": "-", "sector": "Financials"},
    "HOOD": {"name": "Robinhood", "wkn": "-", "sector": "Financials"},
    "SOFI": {"name": "SoFi Technologies", "wkn": "-", "sector": "Financials"},
    "AFRM": {"name": "Affirm", "wkn": "-", "sector": "Financials"},
    "RKLB": {"name": "Rocket Lab", "wkn": "-", "sector": "Aerospace"},
    "IONQ": {"name": "IonQ", "wkn": "-", "sector": "Technology"},
    "ASTS": {"name": "AST SpaceMobile", "wkn": "-", "sector": "Communication"},
    "SOUN": {"name": "SoundHound AI", "wkn": "-", "sector": "Technology"},
    "JOBY": {"name": "Joby Aviation", "wkn": "-", "sector": "Aerospace"},
    "ACHR": {"name": "Archer Aviation", "wkn": "-", "sector": "Aerospace"},
    "QS": {"name": "QuantumScape", "wkn": "-", "sector": "Automotive"},
    "ENVX": {"name": "Enovix", "wkn": "-", "sector": "Technology"},
    "DOCN": {"name": "DigitalOcean", "wkn": "-", "sector": "Technology"},
    "PATH": {"name": "UiPath", "wkn": "-", "sector": "Technology"},
    "CELH": {"name": "Celsius Holdings", "wkn": "-", "sector": "Consumer"},
    "ONON": {"name": "On Holding", "wkn": "-", "sector": "Consumer"},

    "XOM": {"name": "Exxon Mobil", "wkn": "852549", "sector": "Energy"},
    "CVX": {"name": "Chevron", "wkn": "852552", "sector": "Energy"},
    "COP": {"name": "ConocoPhillips", "wkn": "575302", "sector": "Energy"},
    "SLB": {"name": "Schlumberger", "wkn": "853390", "sector": "Energy"},
    "EOG": {"name": "EOG Resources", "wkn": "-", "sector": "Energy"},
    "FANG": {"name": "Diamondback Energy", "wkn": "-", "sector": "Energy"},
    "OXY": {"name": "Occidental Petroleum", "wkn": "851921", "sector": "Energy"},
}


# ============================================================
# Hilfsfunktionen
# ============================================================

def _normalize_symbol(symbol: str) -> str:
    return str(symbol).strip().upper()


def _dedupe_keep_order(symbols: List[str]) -> List[str]:
    seen = set()
    result: List[str] = []

    for symbol in symbols:
        clean = _normalize_symbol(symbol)
        if clean and clean not in seen:
            seen.add(clean)
            result.append(clean)

    return result


def _merge_universes(*universes: List[str]) -> List[str]:
    merged: List[str] = []
    for universe in universes:
        merged.extend(universe)
    return _dedupe_keep_order(merged)


# ============================================================
# Universe Mapping
# ============================================================

UNIVERSE_MAP: Dict[str, List[str]] = {
    NASDAQ_UNIVERSE_NAME: _dedupe_keep_order(NASDAQ_100_SYMBOLS),
    SP500_UNIVERSE_NAME: _dedupe_keep_order(SP500_SYMBOLS),
    EUROPE_UNIVERSE_NAME: _dedupe_keep_order(EUROPE_SYMBOLS),
    EM_UNIVERSE_NAME: _dedupe_keep_order(EM_SYMBOLS),
    SMALL_CAP_UNIVERSE_NAME: _dedupe_keep_order(SMALL_CAP_SYMBOLS),
    COMMODITIES_UNIVERSE_NAME: _dedupe_keep_order(COMMODITY_SYMBOLS),
    TOP_LIQUID_UNIVERSE_NAME: _dedupe_keep_order(TOP_LIQUID_USA_SYMBOLS),
    US_LARGE_CAP_UNIVERSE_NAME: _dedupe_keep_order(US_LARGE_CAP_SYMBOLS),
}


# ============================================================
# Öffentliche API
# ============================================================

def get_available_universes() -> List[str]:
    universes = [
        ALL_UNIVERSE_NAME,
        NASDAQ_UNIVERSE_NAME,
        SP500_UNIVERSE_NAME,
        TOP_LIQUID_UNIVERSE_NAME,
        US_LARGE_CAP_UNIVERSE_NAME,
        EUROPE_UNIVERSE_NAME,
        EM_UNIVERSE_NAME,
        SMALL_CAP_UNIVERSE_NAME,
        COMMODITIES_UNIVERSE_NAME,
    ]
    return universes


def load_universe(
    name: str,
    include_europe_listings: bool = True,
    include_commodities_in_all: bool = False,
) -> List[str]:
    if name == ALL_UNIVERSE_NAME:
        symbols: List[str] = []

        symbols.extend(NASDAQ_100_SYMBOLS)
        symbols.extend(SP500_SYMBOLS)
        symbols.extend(TOP_LIQUID_USA_SYMBOLS)
        symbols.extend(US_LARGE_CAP_SYMBOLS)
        symbols.extend(EM_SYMBOLS)
        symbols.extend(SMALL_CAP_SYMBOLS)

        if include_europe_listings:
            symbols.extend(EUROPE_SYMBOLS)

        if include_commodities_in_all:
            symbols.extend(COMMODITY_SYMBOLS)

        return copy.deepcopy(_dedupe_keep_order(symbols))

    universe = UNIVERSE_MAP.get(name, [])
    return copy.deepcopy(_dedupe_keep_order(universe))


def get_symbol_meta(symbol: str) -> Dict[str, str]:
    clean = _normalize_symbol(symbol)

    if clean in COMMODITY_META:
        return copy.deepcopy(COMMODITY_META[clean])

    meta = SYMBOL_META.get(clean, {})
    return {
        "name": meta.get("name", clean),
        "wkn": meta.get("wkn", "-"),
        "sector": meta.get("sector", "Sonstige"),
    }


def get_symbol_name(symbol: str) -> str:
    return get_symbol_meta(symbol).get("name", _normalize_symbol(symbol))


def get_symbol_wkn(symbol: str) -> str:
    return get_symbol_meta(symbol).get("wkn", "-")