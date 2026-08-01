from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class EntryConfig:
    """Centralized tuning knobs for latency-aware entry decisions."""

    entry_deadline_ms: int = 1200

    scout_qty_mode: str = "ONE_SHARE"
    scout_qty_percent: float = 0.1
    scout_min_qty: int = 1

    normal_allowed_slippage_ticks: int = 2
    normal_allowed_slippage_pct: float = 0.002

    caution_allowed_slippage_ticks: int = 3
    caution_allowed_slippage_pct: float = 0.003

    normal_defensive_ticks: int = 1
    latency_override_defensive_ticks: int = 3

    enable_ioc_for_normal: bool = False

    max_spread_ratio_for_safe: float = 0.003
    max_spread_ratio_for_caution: float = 0.005
    max_ws_age_ms_for_safe: int = 250
    max_ws_age_ms_for_caution: int = 700
    max_ws_jitter_ms_for_safe: int = 120
    max_ws_jitter_ms_for_caution: int = 300
    max_order_rtt_avg_ms_for_safe: int = 250
    max_order_rtt_avg_ms_for_caution: int = 600
