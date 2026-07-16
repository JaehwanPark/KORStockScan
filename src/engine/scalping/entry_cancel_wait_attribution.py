"""Bounded tunable attribution scorer for entry BUY order cancel wait time.

This module computes `cancel_wait_sec` from per-stock attribution inputs
at the moment of order submission. The output is clamped within a bounded
range and must never bypass hard safety, broker/account/order/quantity/
cooldown, or hard/protect/emergency stop guards.

Phase 1: report/provenance only (computed, logged, but not applied).
Phase 2: real runtime reflection when KORSTOCKSCAN_ENTRY_CANCEL_WAIT_
ATTRIBUTION_ENABLED=true.

The old `entry_timeout_sec_override` is reinterpreted as `suggested_wait_sec`
rather than an unconditional override. The scorer decides the final value
within the min/max range.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

WAIT_POLICY_VERSION = "entry_cancel_wait_attribution_v1"

DEFAULT_BASE_SCALPING = 90
DEFAULT_BASE_BREAKOUT = 120
DEFAULT_BASE_PULLBACK = 600
DEFAULT_BASE_RESERVE = 1200

REAL_STANDARD_MIN_SEC = 60
STALE_PASSIVE_RISK_MAX_SEC = 30

ADJUSTMENT_WEIGHTS = {
    "USE_DEFENSIVE_ACTION": -30,
    "passive_probe_lifecycle": -40,
    "stale_context_high": -25,
    "stale_quote_detect": -30,
    "low_confidence_ai": -10,
    "high_spread_bps": -5,
    "low_liquidity_verdict": -5,
    "favorable_ofi_score": +10,
    "high_ai_confidence": +15,
    "price_below_bid_positive": +10,
    "tight_spread_bps": +5,
    "active_priority_match": +20,
    "partial_fill_progress": -15,
}

ADJUSTMENT_REASON_PREFIXES = {
    "USE_DEFENSIVE_ACTION": "ai_defensive_action",
    "passive_probe_lifecycle": "passive_probe_lifecycle",
    "stale_context_high": "stale_context_high",
    "stale_quote_detect": "stale_quote_detect",
    "low_confidence_ai": "low_confidence_ai",
    "high_spread_bps": "high_spread_bps",
    "low_liquidity_verdict": "low_liquidity_verdict",
    "favorable_ofi_score": "favorable_ofi",
    "high_ai_confidence": "high_ai_confidence",
    "price_below_bid_positive": "price_below_bid",
    "tight_spread_bps": "tight_spread",
    "active_priority_match": "active_priority_match",
    "partial_fill_progress": "partial_fill_progress",
}


@dataclass
class EntryCancelWaitAttributionResult:
    cancel_wait_sec: int
    base_wait_sec: int
    min_wait_sec: int
    max_wait_sec: int
    suggested_wait_sec: int | None
    adjustment_reasons: list[str] = field(default_factory=list)
    decision_authority: str = "bounded_tunable"
    forbidden_uses: str = "hard_safety_bypass"
    wait_policy_version: str = WAIT_POLICY_VERSION
    attribution_context_summary: dict[str, str] = field(default_factory=dict)

    def as_log_fields(self) -> dict[str, str]:
        return {
            "cancel_wait_sec": str(self.cancel_wait_sec),
            "base_wait_sec": str(self.base_wait_sec),
            "min_wait_sec": str(self.min_wait_sec),
            "max_wait_sec": str(self.max_wait_sec),
            "suggested_wait_sec": (
                str(self.suggested_wait_sec)
                if self.suggested_wait_sec is not None
                else "-"
            ),
            "wait_policy_version": str(self.wait_policy_version),
            "wait_adjustment_reasons": (
                "|".join(self.adjustment_reasons) if self.adjustment_reasons else "-"
            ),
            "wait_decision_authority": str(self.decision_authority),
            "wait_forbidden_uses": str(self.forbidden_uses),
        }

    def as_cancel_log_fields(
        self, wait_elapsed_overrun_sec: float = 0.0
    ) -> dict[str, str]:
        fields = self.as_log_fields()
        fields["wait_elapsed_overrun_sec"] = f"{wait_elapsed_overrun_sec:.1f}"
        return fields


def _nonempty_str(value: Any) -> str:
    return str(value or "").strip()


def _coerce_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _coerce_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _resolve_base_wait_sec(position_tag: str, entry_mode: str) -> int:
    tag_upper = _nonempty_str(position_tag).upper()
    mode_upper = _nonempty_str(entry_mode).upper()

    if "RESERVE" in tag_upper or "RESERVE" in mode_upper:
        return DEFAULT_BASE_RESERVE
    if "PULLBACK" in tag_upper or "PULLBACK" in mode_upper:
        return DEFAULT_BASE_PULLBACK
    if "BREAKOUT" in tag_upper or "BREAKOUT" in mode_upper:
        return DEFAULT_BASE_BREAKOUT
    return DEFAULT_BASE_SCALPING


def _resolve_min_max_wait_sec(
    base_wait_sec: int,
    is_report_only: bool,
    real_min_sec: int = REAL_STANDARD_MIN_SEC,
    stale_max_sec: int = STALE_PASSIVE_RISK_MAX_SEC,
    has_stale_or_passive_risk: bool = False,
) -> tuple[int, int]:
    if has_stale_or_passive_risk:
        min_sec = max(30, min(stale_max_sec, real_min_sec))
    else:
        min_sec = max(30, real_min_sec)
    max_sec = max(base_wait_sec, min_sec + 30)
    return min_sec, max_sec


def compute_entry_cancel_wait_attribution(
    *,
    cancelled_or_partial_filled_qty: int = 0,
    requested_qty: int = 0,
    position_tag: str = "",
    entry_mode: str = "",
    entry_order_lifecycle: str = "standard",
    entry_passive_probe_applied: bool = False,
    best_bid: int = 0,
    best_ask: int = 0,
    order_price: int = 0,
    quote_age_ms: int = 0,
    quote_stale_at_submit: bool = False,
    context_age_ms: int = 0,
    context_stale_at_submit: bool = False,
    liquidity_verdict: str = "",
    ai_action: str = "",
    ai_confidence: int = 0,
    score_bucket: str = "",
    ofi_direction_label: str = "",
    active_priority_matched: bool = False,
    suggested_wait_sec: int | None = None,
    is_report_only: bool = True,
    real_min_sec: int = REAL_STANDARD_MIN_SEC,
    stale_max_sec: int = STALE_PASSIVE_RISK_MAX_SEC,
    spread_ratio: float = 0.0,
    overbought_guard_action: str = "",
    profile_base_wait_sec: int | None = None,
) -> EntryCancelWaitAttributionResult:
    base_wait_sec = (
        max(5, min(1200, int(profile_base_wait_sec)))
        if profile_base_wait_sec is not None and int(profile_base_wait_sec) > 0
        else _resolve_base_wait_sec(position_tag, entry_mode)
    )

    has_stale_or_passive = (
        entry_passive_probe_applied
        or _nonempty_str(entry_order_lifecycle).upper() == "PASSIVE_PROBE"
        or quote_stale_at_submit
        or context_stale_at_submit
        or quote_age_ms > 2000
        or context_age_ms > 5000
    )

    min_wait_sec, max_wait_sec = _resolve_min_max_wait_sec(
        base_wait_sec,
        is_report_only=is_report_only,
        real_min_sec=real_min_sec,
        stale_max_sec=stale_max_sec,
        has_stale_or_passive_risk=has_stale_or_passive,
    )

    if suggested_wait_sec is not None and suggested_wait_sec > 0:
        clamped_suggested = max(min_wait_sec, min(max_wait_sec, suggested_wait_sec))
    else:
        clamped_suggested = None

    adjustments: list[tuple[str, int]] = []
    reasons: list[str] = []

    if has_stale_or_passive:
        if (
            entry_passive_probe_applied
            or _nonempty_str(entry_order_lifecycle).upper() == "PASSIVE_PROBE"
        ):
            adjustments.append(
                (
                    "passive_probe_lifecycle",
                    ADJUSTMENT_WEIGHTS["passive_probe_lifecycle"],
                )
            )
        if quote_stale_at_submit:
            adjustments.append(
                ("stale_quote_detect", ADJUSTMENT_WEIGHTS["stale_quote_detect"])
            )
        if context_stale_at_submit:
            adjustments.append(
                ("stale_context_high", ADJUSTMENT_WEIGHTS["stale_context_high"])
            )
        if quote_age_ms > 2000 and not quote_stale_at_submit:
            adjustments.append(
                ("stale_quote_detect", ADJUSTMENT_WEIGHTS["stale_quote_detect"])
            )
        if context_age_ms > 5000 and not context_stale_at_submit:
            adjustments.append(
                ("stale_context_high", ADJUSTMENT_WEIGHTS["stale_context_high"])
            )

    if ai_action == "USE_DEFENSIVE":
        adjustments.append(
            ("USE_DEFENSIVE_ACTION", ADJUSTMENT_WEIGHTS["USE_DEFENSIVE_ACTION"])
        )

    if ai_confidence > 0 and ai_confidence < 40:
        adjustments.append(
            ("low_confidence_ai", ADJUSTMENT_WEIGHTS["low_confidence_ai"])
        )
    elif ai_confidence >= 80:
        adjustments.append(
            ("high_ai_confidence", ADJUSTMENT_WEIGHTS["high_ai_confidence"])
        )

    if spread_ratio > 0.005:
        adjustments.append(("high_spread_bps", ADJUSTMENT_WEIGHTS["high_spread_bps"]))
    elif 0 < spread_ratio <= 0.001:
        adjustments.append(("tight_spread_bps", ADJUSTMENT_WEIGHTS["tight_spread_bps"]))

    liquidity_upper = _nonempty_str(liquidity_verdict).upper()
    if liquidity_upper in ("LOW", "WEAK", "INSUFFICIENT"):
        adjustments.append(
            ("low_liquidity_verdict", ADJUSTMENT_WEIGHTS["low_liquidity_verdict"])
        )

    ofi_upper = _nonempty_str(ofi_direction_label).upper()
    if ofi_upper in ("STABLE_BULLISH",):
        adjustments.append(
            ("favorable_ofi_score", ADJUSTMENT_WEIGHTS["favorable_ofi_score"])
        )

    if best_bid > 0 and best_ask > 0 and order_price > 0:
        if order_price < best_bid:
            adjustments.append(
                (
                    "price_below_bid_positive",
                    ADJUSTMENT_WEIGHTS["price_below_bid_positive"],
                )
            )
        elif order_price < best_ask:
            pass

    if active_priority_matched:
        adjustments.append(
            ("active_priority_match", ADJUSTMENT_WEIGHTS["active_priority_match"])
        )

    if cancelled_or_partial_filled_qty > 0 and requested_qty > 0:
        fill_ratio = min(
            1.0, float(cancelled_or_partial_filled_qty) / float(requested_qty)
        )
        if fill_ratio < 0.5:
            adjustments.append(
                ("partial_fill_progress", ADJUSTMENT_WEIGHTS["partial_fill_progress"])
            )

    net_adjustment = sum(weight for _, weight in adjustments)
    for reason_key, _weight in adjustments:
        prefix = ADJUSTMENT_REASON_PREFIXES.get(reason_key, reason_key.lower())
        reasons.append(prefix)

    if not reasons:
        reasons.append("baseline_no_adjustment")

    # Entry-price AI wait is advisory. It may shorten only stale/passive orders;
    # normal orders retain the independently tuned profile threshold.
    resolve_from = (
        clamped_suggested
        if has_stale_or_passive and clamped_suggested is not None
        else base_wait_sec
    )
    raw_wait_sec = resolve_from + net_adjustment
    effective_min_sec = (
        min_wait_sec if has_stale_or_passive else max(min_wait_sec, base_wait_sec)
    )
    cancel_wait_sec = max(effective_min_sec, min(max_wait_sec, raw_wait_sec))

    attributes = {
        "base_wait_source": (
            "position_tag"
            if position_tag
            else "entry_mode" if entry_mode else "strategy_default"
        ),
        "lifecycle_used": _nonempty_str(entry_order_lifecycle) or "standard",
        "passive_probe_used": str(entry_passive_probe_applied).lower(),
        "ai_action_used": _nonempty_str(ai_action) or "USE_DEFENSIVE",
        "stale_context_used": str(context_stale_at_submit).lower(),
        "stale_quote_used": str(quote_stale_at_submit).lower(),
        "ofi_used": _nonempty_str(ofi_direction_label) or "-",
        "active_priority_match_used": str(active_priority_matched).lower(),
        "has_stale_or_passive_risk": str(has_stale_or_passive).lower(),
    }

    return EntryCancelWaitAttributionResult(
        cancel_wait_sec=cancel_wait_sec,
        base_wait_sec=base_wait_sec,
        min_wait_sec=min_wait_sec,
        max_wait_sec=max_wait_sec,
        suggested_wait_sec=suggested_wait_sec,
        adjustment_reasons=reasons,
        attribution_context_summary=attributes,
    )
