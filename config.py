from __future__ import annotations

from pathlib import Path


# ============================================================
# App Informationen
# ============================================================

APP_NAME = "Trading Scanner 5.0"
APP_SUBTITLE = "Momentum, Trend, Marktstruktur und Sektor-Sentiment in einem Blick"


# ============================================================
# Projektstruktur / Verzeichnisse
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

PORTFOLIO_DIR = DATA_DIR / "portfolios"
PORTFOLIO_DIR.mkdir(parents=True, exist_ok=True)

CACHE_DIR = DATA_DIR / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

EXPORT_DIR = DATA_DIR / "exports"
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

ALERTS_DIR = DATA_DIR / "alerts"
ALERTS_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# Portfolio Dateien / Benutzer
# ============================================================

PORTFOLIO_FILE = DATA_DIR / "portfolio.csv"
DEFAULT_PORTFOLIO_USER = "guest"


# ============================================================
# Scanner Performance
# ============================================================

SCANNER_MAX_WORKERS = 16
SCANNER_BATCH_SIZE = 150

DEFAULT_HISTORY_PERIOD = "1y"
DEFAULT_HISTORY_INTERVAL = "1d"
MIN_HISTORY_LENGTH = 120

CACHE_LIVE_PRICES = 120
LIVE_PRICE_TIMEOUT = 10


# ============================================================
# Markt Index / Marktbreite
# ============================================================

MARKET_INDEX = "^GSPC"

MARKET_INDEX_ALTERNATIVES = [
    "^GSPC",
    "^NDX",
    "^DJI",
]

BREADTH_BULLISH_THRESHOLD = 65
BREADTH_BEARISH_THRESHOLD = 40


# ============================================================
# Trading Indikatoren
# ============================================================

SMA_FAST = 50
SMA_SLOW = 200

MOMENTUM_LOOKBACK = 21
RELATIVE_STRENGTH_LOOKBACK = 90

RSI_WINDOW = 14

MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

BOLLINGER_WINDOW = 20
BOLLINGER_STD = 2.0

VOLATILITY_WINDOW = 20
ATR_WINDOW = 14
TREND_CHANNEL_WINDOW = 20


# ============================================================
# Stop-Loss / Risikomanagement
# ============================================================

DEFAULT_STOP_LOSS_PCT = 0.08
TRAILING_STOP_PCT = 0.10
SWING_LOW_LOOKBACK = 20
RECENT_LOW_LOOKBACK = 20
DEFAULT_REWARD_RISK_RATIO = 2.0


# ============================================================
# Sektoranalyse
# ============================================================

MIN_STOCKS_PER_SECTOR = 5


# ============================================================
# Alerts / Email
# ============================================================

ALERT_ENABLED = False

ALERT_FROM_EMAIL = ""
ALERT_FROM_NAME = "Trading Scanner 5.0"

ALERT_RECIPIENTS = []

ALERT_SMTP_HOST = ""
ALERT_SMTP_PORT = 587
ALERT_SMTP_USERNAME = ""
ALERT_SMTP_PASSWORD = ""

ALERT_SMTP_USE_TLS = True
ALERT_SMTP_USE_SSL = False

ALERT_BUY_SIGNAL_NAME = "Kaufsignal"
ALERT_PORTFOLIO_SELL_SIGNAL_NAME = "Verkaufssignal"