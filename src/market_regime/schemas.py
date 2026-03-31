from dataclasses import dataclass, field
from typing import Any, Dict, List
from datetime import datetime


@dataclass
class MarketRegimeSnapshot:
    timestamp: datetime

    # --- VIX ---
    vix_close: float = 0.0
    vix_ma3: float = 0.0
    vix_peak_passed: bool = False
    vix_two_day_down: bool = False
    vix_extreme: bool = False

    # --- Oil (WTI 중심) ---
    wti_close: float = 0.0
    wti_rsi: float = 0.0
    wti_macd: float = 0.0
    wti_macd_signal: float = 0.0
    wti_dead_cross: bool = False
    wti_from_recent_high_pct: float = 0.0
    oil_reversal: bool = False

    # --- Fear & Greed ---
    fng_value: float = 0.0
    fng_prev: float = 0.0
    fng_description: str = ""
    fng_extreme_fear: bool = False
    fng_recovery: bool = False

    # --- Regime decision ---
    allow_swing_entry: bool = False
    swing_score: int = 0
    volatility_mode: str = "NORMAL"   # NORMAL / HIGH / EXTREME
    risk_state: str = "NEUTRAL"       # RISK_ON / NEUTRAL / RISK_OFF

    # --- Diagnostics ---
    reasons: List[str] = field(default_factory=list)
    debug: Dict[str, Any] = field(default_factory=dict)