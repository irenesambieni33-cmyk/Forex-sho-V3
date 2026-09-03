"""Central configuration for Forex AI Analyst."""

from dataclasses import dataclass

APP_NAME = "FOREX AI ANALYST"
APP_SUBTITLE = "Analyse technique multi-timeframe • Aide à la décision • Aucun ordre automatique"
TIMEFRAMES = ("D1", "H4", "H1", "M15", "M5")
TIMEFRAME_WEIGHTS = {"D1": 3, "H4": 3, "H1": 2, "M15": 1, "M5": 1}

INSTRUMENTS = {
    "EUR/USD": {"ticker": "EURUSD=X", "label": "EUR/USD", "proxy": None},
    "XAU/USD": {"ticker": "XAUUSD=X", "label": "XAU/USD", "proxy": "GC=F"},
}

# Yahoo does not expose a native H4 interval through yfinance, so H4 is built from 1h data.
YF_INTERVALS = {"D1": "1d", "H4": "1h", "H1": "1h", "M15": "15m", "M5": "5m"}
PERIODS = {"D1": "max", "H4": "730d", "H1": "730d", "M15": "60d", "M5": "60d"}

EMA_FAST = 20
EMA_SLOW = 50
SMA_LONG = 200
RSI_PERIOD = 14
ATR_PERIOD = 14
ADX_PERIOD = 14
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
BB_PERIOD = 20
BB_STD = 2.0
STOCH_PERIOD = 14
STOCH_K_SMOOTH = 3
STOCH_D_SMOOTH = 3

SWING_LEFT = 3
SWING_RIGHT = 3
MIN_BARS = 80
MIN_SWING_ATR = 0.50
SR_TOLERANCE_ATR = 0.60
SR_MIN_TOUCHES = 2
SR_LOOKBACK = 60
FIB_LEVELS = (0.236, 0.382, 0.500, 0.618, 0.786, 1.272, 1.618)
FIB_CONFLUENCE_ATR = 0.35

RISK_PER_TRADE = 0.01
MAX_OPEN_RISK = 0.02
MIN_RR = 2.0
TP2_RR = 3.0

CACHE_TTL_SECONDS = 300

@dataclass(frozen=True)
class TimeframeResult:
    timeframe: str
    direction: str
    score: float
    confidence: float
    trend: str
    structure: str
