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
    oil_pullback_relief: bool = False

    # --- Fear & Greed ---
    fng_value: float = 0.0
    fng_prev: float = 0.0
    fng_description: str = ""
    fng_extreme_fear: bool = False
    fng_recovery: bool = False

    # --- Regime decision ---
    allow_swing_entry: bool = False
    swing_score: int = 0
    swing_entry_recovery_gate_score: int = 0
    recovery_gate_state: str = "UNKNOWN"
    swing_recovery_gate_label: str = "UNKNOWN"
    recovery_gate_reason: str = "unknown"
    oil_only_recovery_prior: bool = False
    market_regime_continuous_score: float = 0.0
    market_regime_continuous_label: str = "NEUTRAL"
    market_regime_component_scores: Dict[str, float] = field(default_factory=dict)
    market_regime_score_version: str = "market_regime_continuous_v1"
    market_regime_source_quality: str = "unknown"
    volatility_mode: str = "NORMAL"   # NORMAL / HIGH / EXTREME
    risk_state: str = "NEUTRAL"       # RISK_ON / NEUTRAL / RISK_OFF

    # --- Diagnostics ---
    reasons: List[str] = field(default_factory=list)
    debug: Dict[str, Any] = field(default_factory=dict)
