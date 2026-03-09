from pathlib import Path

APP_NAME = "Trading Scanner 4.0"
APP_SUBTITLE = "Systemstatus und Marktanalyse"

DEFAULT_PERIOD = "1y"
DEFAULT_INTERVAL = "1d"

HIST_CACHE_TTL = 1800
LIVE_CACHE_TTL = 30

MIN_HISTORY_ROWS = 220

WEIGHT_MOMENTUM = 0.35
WEIGHT_RS = 0.30
WEIGHT_GOLDEN_CROSS = 0.15
WEIGHT_TREND = 0.10
WEIGHT_DISTANCE_TO_HIGH = 0.10

DEFAULT_STOP_LOSS_PCT = 0.08
DEFAULT_TARGET_PCT = 0.15
ATR_STOP_MULTIPLIER = 2.0

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
PORTFOLIO_FILE = DATA_DIR / "portfolio.csv"

DATA_DIR.mkdir(parents=True, exist_ok=True)

UNIVERSES = {
    "Nasdaq 100": [
        "AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "AVGO", "TSLA", "COST", "ADBE",
        "NFLX", "AMD", "PEP", "CSCO", "TMUS", "INTC", "QCOM", "TXN", "AMGN", "AMAT"
    ],
    "S&P 500": [
        "AAPL", "MSFT", "NVDA", "AMZN", "META", "BRK-B", "GOOGL", "LLY", "AVGO", "JPM",
        "V", "XOM", "UNH", "MA", "PG", "COST", "HD", "MRK", "ABBV", "CAT"
    ],
    "DAX": [
        "SAP.DE", "SIE.DE", "ALV.DE", "BAS.DE", "BAYN.DE", "BMW.DE", "CON.DE", "DTE.DE",
        "DB1.DE", "MBG.DE", "IFX.DE", "MUV2.DE", "RWE.DE", "VOW3.DE", "ADS.DE"
    ],
    "China Large Caps": [
        "BABA", "JD", "PDD", "BIDU", "TME", "NTES", "LI", "NIO", "XPEV", "BEKE"
    ],
    "Emerging Markets": [
        "TSM", "INFY", "VALE", "PBR", "ITUB", "HDB", "MELI", "NU", "BAP", "WIT"
    ],
    "Europa Listings": [
        "AAPL.DE", "MSF.DE", "NVDA.DE", "AMZ.DE", "GOO.DE", "TSL.DE",
        "MC.PA", "OR.PA", "AI.PA", "SAN.PA",
        "ASML.AS", "ADYEN.AS", "PRX.AS",
        "NESN.SW", "ROG.SW", "NOVN.SW",
        "SHEL.L", "AZN.L", "ULVR.L",
        "RMS.PA", "DG.PA", "SU.PA",
        "BMW.DE", "MBG.DE", "SAP.DE", "SIE.DE"
    ],
    "Rohstoffe": [
        "GC=F",   # Gold
        "SI=F",   # Silber
        "HG=F",   # Kupfer
        "PL=F",   # Platin
        "PA=F",   # Palladium
        "CL=F",   # WTI Öl
        "BZ=F",   # Brent Öl
        "NG=F",   # Erdgas
        "ZC=F",   # Mais
        "ZW=F",   # Weizen
        "ZS=F",   # Sojabohnen
        "KC=F",   # Kaffee
        "SB=F",   # Zucker
        "CC=F",   # Kakao
        "CT=F",   # Baumwolle
    ],
}

SYMBOL_META = {
    "AAPL": {"name": "Apple", "wkn": "865985", "sector": "Technologie"},
    "MSFT": {"name": "Microsoft", "wkn": "870747", "sector": "Technologie"},
    "NVDA": {"name": "NVIDIA", "wkn": "918422", "sector": "Technologie"},
    "AMZN": {"name": "Amazon", "wkn": "906866", "sector": "Handel"},
    "META": {"name": "Meta Platforms", "wkn": "A1JWVX", "sector": "Kommunikation"},
    "GOOGL": {"name": "Alphabet", "wkn": "A14Y6F", "sector": "Kommunikation"},
    "AVGO": {"name": "Broadcom", "wkn": "A2JG9Z", "sector": "Technologie"},
    "TSLA": {"name": "Tesla", "wkn": "A1CX3T", "sector": "Automobil"},
    "COST": {"name": "Costco", "wkn": "888351", "sector": "Handel"},
    "ADBE": {"name": "Adobe", "wkn": "871981", "sector": "Technologie"},
    "NFLX": {"name": "Netflix", "wkn": "552484", "sector": "Kommunikation"},
    "AMD": {"name": "AMD", "wkn": "863186", "sector": "Technologie"},
    "PEP": {"name": "PepsiCo", "wkn": "851995", "sector": "Konsum"},
    "CSCO": {"name": "Cisco", "wkn": "878841", "sector": "Technologie"},
    "TMUS": {"name": "T-Mobile US", "wkn": "A1T7LU", "sector": "Telekommunikation"},
    "INTC": {"name": "Intel", "wkn": "855681", "sector": "Technologie"},
    "QCOM": {"name": "Qualcomm", "wkn": "883121", "sector": "Technologie"},
    "TXN": {"name": "Texas Instruments", "wkn": "852654", "sector": "Technologie"},
    "AMGN": {"name": "Amgen", "wkn": "867900", "sector": "Gesundheit"},
    "AMAT": {"name": "Applied Materials", "wkn": "865177", "sector": "Industrie"},
    "BRK-B": {"name": "Berkshire Hathaway B", "wkn": "A0YJQ2", "sector": "Finanzen"},
    "LLY": {"name": "Eli Lilly", "wkn": "858560", "sector": "Gesundheit"},
    "JPM": {"name": "JPMorgan Chase", "wkn": "850628", "sector": "Finanzen"},
    "V": {"name": "Visa", "wkn": "A0NC7B", "sector": "Finanzen"},
    "XOM": {"name": "Exxon Mobil", "wkn": "852549", "sector": "Energie"},
    "UNH": {"name": "UnitedHealth", "wkn": "869561", "sector": "Gesundheit"},
    "MA": {"name": "Mastercard", "wkn": "A0F602", "sector": "Finanzen"},
    "PG": {"name": "Procter & Gamble", "wkn": "852062", "sector": "Konsum"},
    "HD": {"name": "Home Depot", "wkn": "866953", "sector": "Handel"},
    "MRK": {"name": "Merck & Co.", "wkn": "A0YD8Q", "sector": "Gesundheit"},
    "ABBV": {"name": "AbbVie", "wkn": "A1J84E", "sector": "Gesundheit"},
    "CAT": {"name": "Caterpillar", "wkn": "850598", "sector": "Industrie"},

    "SAP.DE": {"name": "SAP", "wkn": "716460", "sector": "Technologie"},
    "SIE.DE": {"name": "Siemens", "wkn": "723610", "sector": "Industrie"},
    "ALV.DE": {"name": "Allianz", "wkn": "840400", "sector": "Finanzen"},
    "BAS.DE": {"name": "BASF", "wkn": "BASF11", "sector": "Chemie"},
    "BAYN.DE": {"name": "Bayer", "wkn": "BAY001", "sector": "Gesundheit"},
    "BMW.DE": {"name": "BMW", "wkn": "519000", "sector": "Automobil"},
    "CON.DE": {"name": "Continental", "wkn": "543900", "sector": "Automobil"},
    "DTE.DE": {"name": "Deutsche Telekom", "wkn": "555750", "sector": "Telekommunikation"},
    "DB1.DE": {"name": "Deutsche Börse", "wkn": "581005", "sector": "Finanzen"},
    "MBG.DE": {"name": "Mercedes-Benz Group", "wkn": "710000", "sector": "Automobil"},
    "IFX.DE": {"name": "Infineon", "wkn": "623100", "sector": "Technologie"},
    "MUV2.DE": {"name": "Munich Re", "wkn": "843002", "sector": "Finanzen"},
    "RWE.DE": {"name": "RWE", "wkn": "703712", "sector": "Energie"},
    "VOW3.DE": {"name": "Volkswagen Vz.", "wkn": "766403", "sector": "Automobil"},
    "ADS.DE": {"name": "Adidas", "wkn": "A1EWWW", "sector": "Konsum"},

    "BABA": {"name": "Alibaba", "wkn": "A117ME", "sector": "Handel"},
    "JD": {"name": "JD.com", "wkn": "A112ST", "sector": "Handel"},
    "PDD": {"name": "PDD Holdings", "wkn": "A2JRK6", "sector": "Handel"},
    "BIDU": {"name": "Baidu", "wkn": "A0F5DE", "sector": "Kommunikation"},
    "TME": {"name": "Tencent Music", "wkn": "A2JCC8", "sector": "Kommunikation"},
    "NTES": {"name": "NetEase", "wkn": "501822", "sector": "Kommunikation"},
    "LI": {"name": "Li Auto", "wkn": "A2P93Z", "sector": "Automobil"},
    "NIO": {"name": "NIO", "wkn": "A2N4PB", "sector": "Automobil"},
    "XPEV": {"name": "XPeng", "wkn": "A2QBX7", "sector": "Automobil"},
    "BEKE": {"name": "KE Holdings", "wkn": "A2QHKZ", "sector": "Immobilien"},
    "TSM": {"name": "Taiwan Semiconductor", "wkn": "909800", "sector": "Technologie"},
    "INFY": {"name": "Infosys", "wkn": "919668", "sector": "Technologie"},
    "VALE": {"name": "Vale", "wkn": "897136", "sector": "Rohstoffe"},
    "PBR": {"name": "Petrobras", "wkn": "932443", "sector": "Energie"},
    "ITUB": {"name": "Itaú Unibanco", "wkn": "A0M4P8", "sector": "Finanzen"},
    "HDB": {"name": "HDFC Bank", "wkn": "A1JCMR", "sector": "Finanzen"},
    "MELI": {"name": "MercadoLibre", "wkn": "A0MYNP", "sector": "Handel"},
    "NU": {"name": "Nu Holdings", "wkn": "A3C82G", "sector": "Finanzen"},
    "BAP": {"name": "Credicorp", "wkn": "766740", "sector": "Finanzen"},
    "WIT": {"name": "Wipro", "wkn": "918584", "sector": "Technologie"},

    "AAPL.DE": {"name": "Apple (DE Listing)", "wkn": "865985", "sector": "Technologie"},
    "MSF.DE": {"name": "Microsoft (DE Listing)", "wkn": "870747", "sector": "Technologie"},
    "NVDA.DE": {"name": "NVIDIA (DE Listing)", "wkn": "918422", "sector": "Technologie"},
    "AMZ.DE": {"name": "Amazon (DE Listing)", "wkn": "906866", "sector": "Handel"},
    "GOO.DE": {"name": "Alphabet (DE Listing)", "wkn": "A14Y6F", "sector": "Kommunikation"},
    "TSL.DE": {"name": "Tesla (DE Listing)", "wkn": "A1CX3T", "sector": "Automobil"},
    "MC.PA": {"name": "LVMH", "wkn": "853292", "sector": "Konsum"},
    "OR.PA": {"name": "L'Oréal", "wkn": "853888", "sector": "Konsum"},
    "AI.PA": {"name": "Air Liquide", "wkn": "850133", "sector": "Industrie"},
    "SAN.PA": {"name": "Sanofi", "wkn": "920657", "sector": "Gesundheit"},
    "ASML.AS": {"name": "ASML", "wkn": "A1J4U4", "sector": "Technologie"},
    "ADYEN.AS": {"name": "Adyen", "wkn": "A2JNF4", "sector": "Finanzen"},
    "PRX.AS": {"name": "Prosus", "wkn": "A2PRDK", "sector": "Technologie"},
    "NESN.SW": {"name": "Nestlé", "wkn": "A0Q4DC", "sector": "Konsum"},
    "ROG.SW": {"name": "Roche", "wkn": "855167", "sector": "Gesundheit"},
    "NOVN.SW": {"name": "Novartis", "wkn": "904278", "sector": "Gesundheit"},
    "SHEL.L": {"name": "Shell", "wkn": "A3C99G", "sector": "Energie"},
    "AZN.L": {"name": "AstraZeneca", "wkn": "886455", "sector": "Gesundheit"},
    "ULVR.L": {"name": "Unilever", "wkn": "A0JNE2", "sector": "Konsum"},
    "RMS.PA": {"name": "Hermès", "wkn": "886670", "sector": "Konsum"},
    "DG.PA": {"name": "Vinci", "wkn": "867475", "sector": "Industrie"},
    "SU.PA": {"name": "Schneider Electric", "wkn": "860180", "sector": "Industrie"},

    "GC=F": {"name": "Gold", "wkn": "-", "sector": "Rohstoffe"},
    "SI=F": {"name": "Silber", "wkn": "-", "sector": "Rohstoffe"},
    "HG=F": {"name": "Kupfer", "wkn": "-", "sector": "Rohstoffe"},
    "PL=F": {"name": "Platin", "wkn": "-", "sector": "Rohstoffe"},
    "PA=F": {"name": "Palladium", "wkn": "-", "sector": "Rohstoffe"},
    "CL=F": {"name": "WTI Öl", "wkn": "-", "sector": "Rohstoffe"},
    "BZ=F": {"name": "Brent Öl", "wkn": "-", "sector": "Rohstoffe"},
    "NG=F": {"name": "Erdgas", "wkn": "-", "sector": "Rohstoffe"},
    "ZC=F": {"name": "Mais", "wkn": "-", "sector": "Rohstoffe"},
    "ZW=F": {"name": "Weizen", "wkn": "-", "sector": "Rohstoffe"},
    "ZS=F": {"name": "Sojabohnen", "wkn": "-", "sector": "Rohstoffe"},
    "KC=F": {"name": "Kaffee", "wkn": "-", "sector": "Rohstoffe"},
    "SB=F": {"name": "Zucker", "wkn": "-", "sector": "Rohstoffe"},
    "CC=F": {"name": "Kakao", "wkn": "-", "sector": "Rohstoffe"},
    "CT=F": {"name": "Baumwolle", "wkn": "-", "sector": "Rohstoffe"},
}