from __future__ import annotations

from pathlib import Path


# ============================================================
# App Informationen
# ============================================================

APP_NAME = "Trading Scanner 4.0"
APP_SUBTITLE = "Momentum, Trend und Marktstruktur in einem Blick"


# ============================================================
# Projektstruktur / Verzeichnisse
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

PORTFOLIO_DIR = DATA_DIR / "portfolios"
PORTFOLIO_DIR.mkdir(exist_ok=True)

CACHE_DIR = DATA_DIR / "cache"
CACHE_DIR.mkdir(exist_ok=True)

EXPORT_DIR = DATA_DIR / "exports"
EXPORT_DIR.mkdir(exist_ok=True)


# ============================================================
# Portfolio Dateien
# ============================================================

# Alte Standarddatei (Fallback / Kompatibilität)
PORTFOLIO_FILE = DATA_DIR / "portfolio.csv"

# Standardnutzer wenn kein Login aktiv
DEFAULT_PORTFOLIO_USER = "guest"


# ============================================================
# Scanner Einstellungen
# ============================================================

# Maximale Anzahl paralleler API-Requests
SCANNER_MAX_WORKERS = 8

# Historische Daten
DEFAULT_HISTORY_PERIOD = "1y"
DEFAULT_HISTORY_INTERVAL = "1d"

# Mindestanzahl Datenpunkte für Analyse
MIN_HISTORY_LENGTH = 120


# ============================================================
# Marktanalyse Einstellungen
# ============================================================

# Referenzindex für Marktstatus
MARKET_INDEX = "^GSPC"

# Alternativen (für spätere Erweiterung)
MARKET_INDEX_ALTERNATIVES = [
    "^GSPC",   # S&P 500
    "^NDX",    # Nasdaq 100
    "^DJI",    # Dow Jones
]

# Schwellenwerte Marktbreite
BREADTH_BULLISH_THRESHOLD = 65
BREADTH_BEARISH_THRESHOLD = 40


# ============================================================
# Trading Indikatoren
# ============================================================

# Standard Moving Averages
SMA_FAST = 50
SMA_SLOW = 200

# Momentum Lookback (Tage)
MOMENTUM_LOOKBACK = 21

# Relative Stärke Lookback
RELATIVE_STRENGTH_LOOKBACK = 90


# ============================================================
# Stop-Loss / Risikomanagement
# ============================================================

# Minimaler Stop unter Kaufkurs
DEFAULT_STOP_LOSS_PCT = 0.08   # 8 %

# Trailing Stop Abstand
TRAILING_STOP_PCT = 0.10       # 10 %

# Swing Low Lookback
SWING_LOW_LOOKBACK = 20

# Donchian / Tief Lookback
RECENT_LOW_LOOKBACK = 20


# ============================================================
# Trade Score Gewichtung
# ============================================================

# Gewichtung einzelner Faktoren
WEIGHT_TREND = 0.35
WEIGHT_MOMENTUM = 0.30
WEIGHT_RELATIVE_STRENGTH = 0.20
WEIGHT_VOLUME = 0.15


# ============================================================
# Sektor Analyse
# ============================================================

# Mindestanzahl Aktien pro Sektor
MIN_STOCKS_PER_SECTOR = 5

# Lookback für Sektor Momentum
SECTOR_MOMENTUM_LOOKBACK = 60


# ============================================================
# Scanner Filter
# ============================================================

# Minimaler Trade Score
DEFAULT_MIN_TRADE_SCORE = 60

# Maximale Anzahl Top Kandidaten
DEFAULT_TOP_CANDIDATES = 10


# ============================================================
# Live Daten Einstellungen
# ============================================================

# Timeout für Live Preis Abfragen
LIVE_PRICE_TIMEOUT = 10

# Maximale Anzahl Live Preis Abfragen pro Batch
LIVE_PRICE_BATCH_SIZE = 40


# ============================================================
# Streamlit Cache
# ============================================================

# Cache Zeiten (Sekunden)
CACHE_MARKET_DATA = 600
CACHE_PORTFOLIO_DATA = 300
CACHE_LIVE_PRICES = 120


# ============================================================
# Logging
# ============================================================

ENABLE_DEBUG_LOGGING = False


# ============================================================
# Export / Reporting
# ============================================================

ENABLE_EXPORT = True

EXPORT_DEFAULT_FORMAT = "csv"

EXPORT_COLUMNS = [
    "symbol",
    "analysis_price",
    "market_price",
    "momentum",
    "relative_strength",
    "trade_score",
    "target_price",
    "stop_loss",
    "signal",
]


# ============================================================
# Benutzer / Login Vorbereitung
# ============================================================

ENABLE_AUTHENTICATION = False

AUTH_PROVIDER = None

# Beispiel für spätere Nutzung
SUPPORTED_AUTH_PROVIDERS = [
    "google",
    "microsoft",
    "github",
]


# ============================================================
# Anzeige / UI
# ============================================================

DEFAULT_TOP_TRADES = 3

MAX_MARKETTABLE_ROWS = 40

DEFAULT_SHOW_LIVE_PRICES = False


# ============================================================
# Debug / Entwicklung
# ============================================================

DEVELOPMENT_MODE = False

PRINT_API_ERRORS = True