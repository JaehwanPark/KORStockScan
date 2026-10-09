"""Pure, shared decision for the main real scalping take-profit exit."""

from __future__ import annotations

import math
from dataclasses import dataclass

EXIT_WAIT_STAGES = frozenset({
    "sell_order_blocked_open_time", "sell_order_blocked_market_closed",
    "sell_submit_pre_call_custody_blocked", "sell_retry_quantity_reconciliation_blocked",
    "sell_cancel_inventory_confirmation_deferred", "sell_restart_receipt_recovery_blocked",
    "scalp_fast_exit_deferred_for_reconciliation", "sell_order_retry_backoff_active",
})


@dataclass(frozen=True)
class TrailingTakeProfitDecision:
    armed: bool
    triggered: bool
    trigger_kind: str
    threshold_key: str
    threshold_pct: float
    drawdown_pct: float
    price_usable: bool


@dataclass(frozen=True)
class ExitDeferralDecision:
    proceeds: bool
    reason: str
    elapsed_sec: float | None
    profit_worsen_pct: float | None


def evaluate_exit_deferral(*, decision: str, now: float, signal_at: float,
                          started_at: float, anchor_profit: float, profit: float,
                          max_defer_sec: float, max_worsen_pct: float,
                          policy_valid: bool = True, quote_fresh: bool = True,
                          safety: bool = False, same_generation: bool = True,
                          same_market: bool = True) -> ExitDeferralDecision:
    """Runtime/replay share bounded permission; invalid evidence never extends a VETO."""
    values = (now, signal_at, started_at, anchor_profit, profit, max_defer_sec, max_worsen_pct)
    if not all(isinstance(x, (int, float)) and not isinstance(x, bool)
               and math.isfinite(x) for x in values) or not 0 < signal_at <= now or not 0 < started_at <= signal_at:
        return ExitDeferralDecision(True, "clock_invalid", None, None)
    elapsed, worsen = now - started_at, anchor_profit - profit
    reason = (
        "decision_proceeds" if decision != "VETO" else
        "policy_invalid" if not policy_valid else
        "generation_changed" if not same_generation else
        "quote_unavailable" if not quote_fresh else
        "safety_priority" if safety else
        "market_changed" if not same_market else
        "defer_timeout" if elapsed >= min(90.0, max_defer_sec) else
        "profit_worsened" if worsen >= max_worsen_pct else "veto_deferred"
    )
    return ExitDeferralDecision(reason != "veto_deferred", reason, elapsed, worsen)


def evaluate_trailing_take_profit(
    *,
    peak_price: float,
    executable_bid: float,
    peak_profit_pct: float,
    start_pct: float,
    strong: bool,
    weak_limit_pct: float,
    strong_limit_pct: float,
    already_armed: bool = False,
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
    armed = bool(
        arm_numeric and peak_price > 0
        and (peak_profit_pct >= start_pct or already_armed)
    )
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
