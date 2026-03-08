# --------------------------------------------------
# Grundeinstellungen
# --------------------------------------------------

ZEITRAUM_STANDARD = "1y"
INTERVALL_STANDARD = "1d"

MOMENTUM_TAGE = 20


# --------------------------------------------------
# Performance-Perioden
# --------------------------------------------------

PERFORMANCE_1M = 21
PERFORMANCE_3M = 63


# --------------------------------------------------
# Markt-Indizes
# --------------------------------------------------

MARKT_INDIZES = {
    "USA_NASDAQ": {
        "name": "Nasdaq 100",
        "ticker": "^NDX",
        "region": "USA"
    },
    "USA_SP500": {
        "name": "S&P 500",
        "ticker": "^GSPC",
        "region": "USA"
    },
    "DE_DAX": {
        "name": "DAX",
        "ticker": "^GDAXI",
        "region": "Deutschland"
    },
    "CHINA": {
        "name": "Hang Seng",
        "ticker": "^HSI",
        "region": "China"
    },
    "TAIWAN": {
        "name": "Taiwan",
        "ticker": "^TWII",
        "region": "Taiwan"
    }
}


# --------------------------------------------------
# Sektor-ETFs
# --------------------------------------------------

SEKTOREN = {
    "Technologie": {"ticker": "XLK"},
    "Gesundheit": {"ticker": "XLV"},
    "Finanzen": {"ticker": "XLF"},
    "Industrie": {"ticker": "XLI"},
    "Basiskonsum": {"ticker": "XLP"},
    "Nicht-Basiskonsum": {"ticker": "XLY"},
    "Energie": {"ticker": "XLE"},
    "Materialien": {"ticker": "XLB"},
    "Versorger": {"ticker": "XLU"},
    "Kommunikation": {"ticker": "XLC"},
    "Immobilien": {"ticker": "XLRE"}
}


# --------------------------------------------------
# Nasdaq-100 Fallback-Liste
# --------------------------------------------------

NASDAQ100_AKTIEN = [
    {"name": "Microsoft", "ticker": "MSFT", "wkn": "870747", "markt": "USA", "sektor": "Technologie"},
    {"name": "Apple", "ticker": "AAPL", "wkn": "865985", "markt": "USA", "sektor": "Technologie"},
    {"name": "NVIDIA", "ticker": "NVDA", "wkn": "918422", "markt": "USA", "sektor": "Technologie"},
    {"name": "Amazon", "ticker": "AMZN", "wkn": "906866", "markt": "USA", "sektor": "Nicht-Basiskonsum"},
    {"name": "Meta Platforms", "ticker": "META", "wkn": "A1JWVX", "markt": "USA", "sektor": "Kommunikation"},
    {"name": "Alphabet A", "ticker": "GOOGL", "wkn": "A14Y6F", "markt": "USA", "sektor": "Kommunikation"},
    {"name": "Alphabet C", "ticker": "GOOG", "wkn": "A14Y6H", "markt": "USA", "sektor": "Kommunikation"},
    {"name": "Broadcom", "ticker": "AVGO", "wkn": "A2JG9Z", "markt": "USA", "sektor": "Technologie"},
    {"name": "Tesla", "ticker": "TSLA", "wkn": "A1CX3T", "markt": "USA", "sektor": "Nicht-Basiskonsum"},
    {"name": "Costco", "ticker": "COST", "wkn": "888351", "markt": "USA", "sektor": "Basiskonsum"},
    {"name": "Netflix", "ticker": "NFLX", "wkn": "552484", "markt": "USA", "sektor": "Kommunikation"},
    {"name": "Adobe", "ticker": "ADBE", "wkn": "871981", "markt": "USA", "sektor": "Technologie"},
    {"name": "Cisco", "ticker": "CSCO", "wkn": "878841", "markt": "USA", "sektor": "Technologie"},
    {"name": "PepsiCo", "ticker": "PEP", "wkn": "851995", "markt": "USA", "sektor": "Basiskonsum"},
    {"name": "AMD", "ticker": "AMD", "wkn": "863186", "markt": "USA", "sektor": "Technologie"},
    {"name": "Qualcomm", "ticker": "QCOM", "wkn": "883121", "markt": "USA", "sektor": "Technologie"},
    {"name": "Intel", "ticker": "INTC", "wkn": "855681", "markt": "USA", "sektor": "Technologie"},
    {"name": "Intuit", "ticker": "INTU", "wkn": "886053", "markt": "USA", "sektor": "Technologie"},
    {"name": "Applied Materials", "ticker": "AMAT", "wkn": "865177", "markt": "USA", "sektor": "Technologie"},
    {"name": "Micron", "ticker": "MU", "wkn": "869020", "markt": "USA", "sektor": "Technologie"}
]


# --------------------------------------------------
# S&P-500 Proxy-Liste
# --------------------------------------------------

SP500_PROXY_AKTIEN = [
    {"name": "Microsoft", "ticker": "MSFT", "wkn": "870747", "markt": "USA", "sektor": "Technologie"},
    {"name": "Apple", "ticker": "AAPL", "wkn": "865985", "markt": "USA", "sektor": "Technologie"},
    {"name": "Amazon", "ticker": "AMZN", "wkn": "906866", "markt": "USA", "sektor": "Nicht-Basiskonsum"},
    {"name": "NVIDIA", "ticker": "NVDA", "wkn": "918422", "markt": "USA", "sektor": "Technologie"},
    {"name": "Meta Platforms", "ticker": "META", "wkn": "A1JWVX", "markt": "USA", "sektor": "Kommunikation"},
    {"name": "Alphabet A", "ticker": "GOOGL", "wkn": "A14Y6F", "markt": "USA", "sektor": "Kommunikation"},
    {"name": "Alphabet C", "ticker": "GOOG", "wkn": "A14Y6H", "markt": "USA", "sektor": "Kommunikation"},
    {"name": "Berkshire Hathaway B", "ticker": "BRK-B", "wkn": "A0YJQ2", "markt": "USA", "sektor": "Finanzen"},
    {"name": "Eli Lilly", "ticker": "LLY", "wkn": "858560", "markt": "USA", "sektor": "Gesundheit"},
    {"name": "Visa", "ticker": "V", "wkn": "A0NC7B", "markt": "USA", "sektor": "Finanzen"},
    {"name": "Exxon Mobil", "ticker": "XOM", "wkn": "852549", "markt": "USA", "sektor": "Energie"},
    {"name": "UnitedHealth", "ticker": "UNH", "wkn": "869561", "markt": "USA", "sektor": "Gesundheit"},
    {"name": "JPMorgan", "ticker": "JPM", "wkn": "850628", "markt": "USA", "sektor": "Finanzen"},
    {"name": "Johnson & Johnson", "ticker": "JNJ", "wkn": "853260", "markt": "USA", "sektor": "Gesundheit"},
    {"name": "Procter & Gamble", "ticker": "PG", "wkn": "852062", "markt": "USA", "sektor": "Basiskonsum"},
    {"name": "Mastercard", "ticker": "MA", "wkn": "A0F602", "markt": "USA", "sektor": "Finanzen"},
    {"name": "Home Depot", "ticker": "HD", "wkn": "866953", "markt": "USA", "sektor": "Nicht-Basiskonsum"},
    {"name": "AbbVie", "ticker": "ABBV", "wkn": "A1J84E", "markt": "USA", "sektor": "Gesundheit"},
    {"name": "Broadcom", "ticker": "AVGO", "wkn": "A2JG9Z", "markt": "USA", "sektor": "Technologie"},
    {"name": "PepsiCo", "ticker": "PEP", "wkn": "851995", "markt": "USA", "sektor": "Basiskonsum"}
]


# --------------------------------------------------
# DAX-Liste
# --------------------------------------------------

DAX_AKTIEN = [
    {"name": "SAP", "ticker": "SAP.DE", "wkn": "716460", "markt": "Deutschland", "sektor": "Technologie"},
    {"name": "Siemens", "ticker": "SIE.DE", "wkn": "723610", "markt": "Deutschland", "sektor": "Industrie"},
    {"name": "Allianz", "ticker": "ALV.DE", "wkn": "840400", "markt": "Deutschland", "sektor": "Finanzen"},
    {"name": "BASF", "ticker": "BAS.DE", "wkn": "BASF11", "markt": "Deutschland", "sektor": "Materialien"},
    {"name": "Mercedes-Benz", "ticker": "MBG.DE", "wkn": "710000", "markt": "Deutschland", "sektor": "Nicht-Basiskonsum"},
    {"name": "BMW", "ticker": "BMW.DE", "wkn": "519000", "markt": "Deutschland", "sektor": "Nicht-Basiskonsum"},
    {"name": "Volkswagen", "ticker": "VOW3.DE", "wkn": "766403", "markt": "Deutschland", "sektor": "Nicht-Basiskonsum"},
    {"name": "Adidas", "ticker": "ADS.DE", "wkn": "A1EWWW", "markt": "Deutschland", "sektor": "Nicht-Basiskonsum"},
    {"name": "Deutsche Telekom", "ticker": "DTE.DE", "wkn": "555750", "markt": "Deutschland", "sektor": "Kommunikation"},
    {"name": "Infineon", "ticker": "IFX.DE", "wkn": "623100", "markt": "Deutschland", "sektor": "Technologie"}
]


# --------------------------------------------------
# China-Proxy-Universum
# --------------------------------------------------

CHINA_PROXY_AKTIEN = [
    {"name": "Alibaba", "ticker": "BABA", "wkn": "A117ME", "markt": "China", "sektor": "Nicht-Basiskonsum"},
    {"name": "JD.com", "ticker": "JD", "wkn": "A112ST", "markt": "China", "sektor": "Nicht-Basiskonsum"},
    {"name": "Baidu", "ticker": "BIDU", "wkn": "A0F5DE", "markt": "China", "sektor": "Kommunikation"},
    {"name": "PDD Holdings", "ticker": "PDD", "wkn": "", "markt": "China", "sektor": "Nicht-Basiskonsum"},
    {"name": "NetEase", "ticker": "NTES", "wkn": "501822", "markt": "China", "sektor": "Kommunikation"},
    {"name": "Trip.com", "ticker": "TCOM", "wkn": "", "markt": "China", "sektor": "Nicht-Basiskonsum"},
    {"name": "Tencent Music", "ticker": "TME", "wkn": "", "markt": "China", "sektor": "Kommunikation"},
    {"name": "KE Holdings", "ticker": "BEKE", "wkn": "", "markt": "China", "sektor": "Immobilien"},
    {"name": "Li Auto", "ticker": "LI", "wkn": "", "markt": "China", "sektor": "Nicht-Basiskonsum"},
    {"name": "XPeng", "ticker": "XPEV", "wkn": "", "markt": "China", "sektor": "Nicht-Basiskonsum"},
    {"name": "NIO", "ticker": "NIO", "wkn": "", "markt": "China", "sektor": "Nicht-Basiskonsum"},
    {"name": "Yum China", "ticker": "YUMC", "wkn": "", "markt": "China", "sektor": "Nicht-Basiskonsum"},
    {"name": "PetroChina", "ticker": "PTR", "wkn": "", "markt": "China", "sektor": "Energie"},
    {"name": "China Mobile", "ticker": "CHL", "wkn": "", "markt": "China", "sektor": "Kommunikation"}
]


# --------------------------------------------------
# Emerging-Markets-Universum
# --------------------------------------------------

EM_PROXY_AKTIEN = [
    {"name": "Taiwan Semiconductor", "ticker": "TSM", "wkn": "909800", "markt": "EM", "sektor": "Technologie"},
    {"name": "Samsung Electronics", "ticker": "SSNLF", "wkn": "", "markt": "EM", "sektor": "Technologie"},
    {"name": "Infosys", "ticker": "INFY", "wkn": "919668", "markt": "EM", "sektor": "Technologie"},
    {"name": "Wipro", "ticker": "WIT", "wkn": "", "markt": "EM", "sektor": "Technologie"},
    {"name": "ICICI Bank", "ticker": "IBN", "wkn": "", "markt": "EM", "sektor": "Finanzen"},
    {"name": "HDFC Bank", "ticker": "HDB", "wkn": "", "markt": "EM", "sektor": "Finanzen"},
    {"name": "Vale", "ticker": "VALE", "wkn": "897136", "markt": "EM", "sektor": "Materialien"},
    {"name": "Petrobras", "ticker": "PBR", "wkn": "932443", "markt": "EM", "sektor": "Energie"},
    {"name": "Cemex", "ticker": "CX", "wkn": "", "markt": "EM", "sektor": "Materialien"},
    {"name": "Naspers", "ticker": "NPSNY", "wkn": "", "markt": "EM", "sektor": "Kommunikation"},
    {"name": "Itau Unibanco", "ticker": "ITUB", "wkn": "", "markt": "EM", "sektor": "Finanzen"},
    {"name": "America Movil", "ticker": "AMX", "wkn": "", "markt": "EM", "sektor": "Kommunikation"}
]


# --------------------------------------------------
# Rohstoffe (ETFs / ETCs)
# --------------------------------------------------

ROHSTOFFE = [
    {"name": "Gold", "ticker": "GLD", "wkn": "", "gruppe": "Edelmetalle"},
    {"name": "Silber", "ticker": "SLV", "wkn": "", "gruppe": "Edelmetalle"},
    {"name": "Platin", "ticker": "PPLT", "wkn": "", "gruppe": "Edelmetalle"},
    {"name": "Palladium", "ticker": "PALL", "wkn": "", "gruppe": "Edelmetalle"},
    {"name": "Öl (WTI)", "ticker": "USO", "wkn": "", "gruppe": "Energie"},
    {"name": "Erdgas", "ticker": "UNG", "wkn": "", "gruppe": "Energie"},
    {"name": "Benzin", "ticker": "UGA", "wkn": "", "gruppe": "Energie"},
    {"name": "Kupfer", "ticker": "CPER", "wkn": "", "gruppe": "Industriemetalle"},
    {"name": "Aluminium", "ticker": "JJU", "wkn": "", "gruppe": "Industriemetalle"},
    {"name": "Nickel", "ticker": "JJN", "wkn": "", "gruppe": "Industriemetalle"},
    {"name": "Weizen", "ticker": "WEAT", "wkn": "", "gruppe": "Agrar"},
    {"name": "Mais", "ticker": "CORN", "wkn": "", "gruppe": "Agrar"},
    {"name": "Sojabohnen", "ticker": "SOYB", "wkn": "", "gruppe": "Agrar"},
    {"name": "Kaffee", "ticker": "JO", "wkn": "", "gruppe": "Agrar"},
    {"name": "Zucker", "ticker": "SGG", "wkn": "", "gruppe": "Agrar"},
    {"name": "Baumwolle", "ticker": "BAL", "wkn": "", "gruppe": "Agrar"}
]


# --------------------------------------------------
# Textbausteine
# --------------------------------------------------

TEXTBAUSTEINE = {
    "markt_bullish": "Bullish",
    "markt_neutral": "Neutral",
    "markt_bearish": "Bearish",
    "crash_niedrig": "Niedrig",
    "crash_mittel": "Mittel",
    "crash_hoch": "Hoch",
    "halten": "Halten",
    "gewinn_sichern": "Gewinne sichern",
    "ausstieg": "Ausstieg prüfen"
}


# --------------------------------------------------
# Fallback-Universum
# --------------------------------------------------

AKTIEN_UNIVERSUM = NASDAQ100_AKTIEN