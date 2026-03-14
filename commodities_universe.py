# ============================================================
# Trading Scanner 5.0
# Rohstoff Universum
# ============================================================

COMMODITIES = {
    "GC=F": "Gold",
    "SI=F": "Silber",
    "PL=F": "Platin",
    "PA=F": "Palladium",

    "CL=F": "WTI Rohöl",
    "BZ=F": "Brent Rohöl",
    "NG=F": "Erdgas",

    "HG=F": "Kupfer",

    "ZW=F": "Weizen",
    "ZC=F": "Mais",
    "ZS=F": "Sojabohnen",

    "KC=F": "Kaffee",
    "SB=F": "Zucker",
    "CC=F": "Kakao",
}


def get_commodity_symbols():
    return list(COMMODITIES.keys())


def get_commodity_name(symbol: str) -> str:
    return COMMODITIES.get(symbol, symbol)