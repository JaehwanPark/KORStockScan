"""Pure, shared decision for the main real scalping take-profit exit."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class TrailingTakeProfitDecision:
    armed: bool
    triggered: bool
    trigger_kind: str
    threshold_key: str
    threshold_pct: float
    drawdown_pct: float
    price_usable: bool


def evaluate_trailing_take_profit(
    *,
    peak_price: float,
    executable_bid: float,
    peak_profit_pct: float,
    start_pct: float,
    strong: bool,
    weak_limit_pct: float,
    strong_limit_pct: float,
) -> TrailingTakeProfitDecision:
    """Arm on peak profit, then compare peak-to-bid drawdown in percent."""

    threshold_key = (
        "SCALP_TRAILING_LIMIT_STRONG" if strong else "SCALP_TRAILING_LIMIT_WEAK"
    )
    threshold = float(strong_limit_pct if strong else weak_limit_pct)
    arm_values = (peak_price, peak_profit_pct, start_pct, threshold)
    arm_numeric = all(
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        for value in arm_values
    )
    armed = bool(arm_numeric and peak_price > 0 and peak_profit_pct >= start_pct)
    bid_numeric = (
        isinstance(executable_bid, (int, float))
        and not isinstance(executable_bid, bool)
        and math.isfinite(executable_bid)
    )
    price_usable = bool(arm_numeric and bid_numeric and peak_price > 0 and executable_bid > 0)
    if not price_usable:
        return TrailingTakeProfitDecision(
            armed=armed,
            triggered=False,
            trigger_kind="",
            threshold_key=threshold_key,
            threshold_pct=threshold,
            drawdown_pct=0.0,
            price_usable=False,
        )
    drawdown_pct = max(0.0, (peak_price - executable_bid) / peak_price * 100.0)
    triggered = bool(armed and drawdown_pct + 1e-9 >= threshold)
    return TrailingTakeProfitDecision(
        armed=armed,
        triggered=triggered,
        trigger_kind="trailing_peak_worsen_floor" if triggered else "",
        threshold_key=threshold_key,
        threshold_pct=threshold,
        drawdown_pct=drawdown_pct,
        price_usable=True,
    )
