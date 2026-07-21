"""Single sizing authority for every scalping buy allocation.

The allocator owns the entry-type tier, budget ratio, budget capacity, and
quantity-cap composition.  Broker, quote, order, and stop guards remain
downstream hard-safety vetoes and may only reduce or reject this quantity.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from datetime import datetime, time
from typing import Any, Iterable
from zoneinfo import ZoneInfo

from src.engine.kiwoom_orders import describe_buy_capacity

FORMULA_VERSION = "entry_type_5stage_cap25_v1"
ROLLBACK_FORMULA_VERSION = "flat_10_fallback"
DEFAULT_TIER_RATIOS = (0.10, 0.15, 0.20, 0.25, 0.25)
TIER_RATIOS = DEFAULT_TIER_RATIOS
MAX_RATIO = 0.25
KST = ZoneInfo("Asia/Seoul")

_INVALID_SOURCE_TOKENS = frozenset(
    {
        "",
        "-",
        "NONE",
        "NULL",
        "UNKNOWN",
        "NOT_APPLICABLE",
        "NOT_APPLICABLE_SOURCE_SIGNATURE",
        "MISSING",
        "N/A",
        "NA",
        "NOT APPLICABLE",
        "NOT APPLICABLE SOURCE SIGNATURE",
    }
)


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError, OverflowError):
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        resolved = float(value)
    except (TypeError, ValueError, OverflowError):
        return default
    return resolved if math.isfinite(resolved) else default


def normalize_source_tokens(source_signature: Any) -> tuple[str, ...]:
    """Return canonical, de-duplicated source tokens."""

    if isinstance(source_signature, str):
        raw_values: Iterable[Any] = (source_signature,)
    elif isinstance(source_signature, (list, tuple, set, frozenset)):
        raw_values = source_signature
    else:
        raw_values = ()
    raw_tokens = (
        token for value in raw_values for token in re.split(r"[,|;]+", str(value or ""))
    )
    normalized = {
        str(token or "").strip().upper()
        for token in raw_tokens
        if str(token or "").strip().upper() not in _INVALID_SOURCE_TOKENS
    }
    return tuple(sorted(normalized))


def _coerce_reference_time(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        resolved = value
    elif isinstance(value, (int, float)):
        try:
            resolved = datetime.fromtimestamp(float(value), tz=KST)
        except (ValueError, OSError, OverflowError):
            return None
    else:
        text = str(value or "").strip()
        if not text:
            return None
        try:
            resolved = datetime.fromisoformat(text)
        except ValueError:
            return None
    if resolved.tzinfo is None:
        return resolved.replace(tzinfo=KST)
    return resolved.astimezone(KST)


def infer_scalping_venue(reference_time: Any, explicit_venue: Any = None) -> str:
    """Resolve KRX/NXT without treating an unknown label as KRX."""

    venue = str(explicit_venue or "").strip().upper()
    if venue == "NXT" or venue.startswith("NXT_"):
        return "NXT"
    if venue == "KRX" or venue.startswith("KRX_"):
        return "KRX"
    resolved = _coerce_reference_time(reference_time)
    if resolved is None:
        return "UNKNOWN"
    current = resolved.time().replace(tzinfo=None)
    if time(8, 0) <= current < time(9, 0):
        return "NXT"
    if time(9, 0) <= current < time(15, 30):
        return "KRX"
    if time(16, 0) <= current < time(20, 0):
        return "NXT"
    return "UNKNOWN"


def _validated_tier_ratios() -> tuple[tuple[float, ...], bool]:
    try:
        ratios = tuple(float(value) for value in TIER_RATIOS)
    except (TypeError, ValueError):
        return DEFAULT_TIER_RATIOS, False
    valid = bool(
        len(ratios) == 5
        and all(0.10 <= value <= MAX_RATIO for value in ratios)
        and all(left <= right for left, right in zip(ratios, ratios[1:]))
    )
    return (ratios, True) if valid else (DEFAULT_TIER_RATIOS, False)


def _time_bucket(reference_time: Any) -> str:
    resolved = _coerce_reference_time(reference_time)
    if resolved is None:
        return "missing_reference_time"
    current = resolved.time().replace(tzinfo=None)
    if time(9, 30) <= current < time(11, 30):
        return "krx_morning_0930_1129"
    if time(13, 30) <= current < time(15, 20):
        return "krx_afternoon_1330_1519"
    return "outside_preferred_krx_window"


@dataclass(frozen=True)
class ScalpingSizingContext:
    allocation_stage: str
    reference_time: Any
    source_signature: Any
    effective_venue: Any
    budget_base_krw: int
    price_krw: int
    safety_ratio: float = 0.95
    absolute_budget_cap_krw: int = 0
    current_position_qty: int = 0
    max_position_qty_cap: int | None = None
    cash_orderable_qty_cap: int | None = None
    remaining_position_qty_cap: int | None = None
    stage_qty_cap: int | None = None
    broker_qty_cap: int | None = None
    min_one_share_floor_enabled: bool = True
    simulation: bool = False
    initial_tier: int | None = None
    initial_formula_version: str | None = None


@dataclass(frozen=True)
class ScalpingSizingDecision:
    formula_version: str
    tier: int
    ratio: float
    tier_reason: str
    source_count: int
    source_tokens: tuple[str, ...]
    time_bucket: str
    reference_time: str
    venue: str
    target_budget: int
    safe_budget: int
    safety_ratio: float
    pre_cap_qty: int
    effective_qty: int
    min_one_share_floor_applied: bool
    binding_caps: tuple[str, ...]
    config_valid: bool
    allocation_stage: str
    simulation: bool

    def event_fields(self) -> dict[str, Any]:
        return {
            "formula_version": self.formula_version,
            "tier": self.tier,
            "ratio": round(self.ratio, 6),
            "tier_reason": self.tier_reason,
            "source_count": self.source_count,
            "source_tokens": ",".join(self.source_tokens) or "-",
            "time_bucket": self.time_bucket,
            "reference_time": self.reference_time,
            "venue": self.venue,
            "target_budget": self.target_budget,
            "safe_budget": self.safe_budget,
            "safety_ratio": round(self.safety_ratio, 6),
            "pre_cap_qty": self.pre_cap_qty,
            "effective_qty": self.effective_qty,
            "min_one_share_floor_applied": self.min_one_share_floor_applied,
            "binding_caps": ",".join(self.binding_caps) or "-",
            "allocation_stage": self.allocation_stage,
            "simulation": self.simulation,
            "sizing_config_valid": self.config_valid,
        }


def _select_tier(
    context: ScalpingSizingContext,
) -> tuple[int, str, int, tuple[str, ...], str, str]:
    resolved_time = _coerce_reference_time(context.reference_time)
    reference_text = resolved_time.isoformat() if resolved_time else "missing"
    venue = infer_scalping_venue(context.reference_time, context.effective_venue)
    tokens = normalize_source_tokens(context.source_signature)
    source_count = len(tokens)
    time_bucket = _time_bucket(context.reference_time)

    if venue == "NXT":
        return 1, "nxt_forced_tier1", source_count, tokens, time_bucket, reference_text
    if venue != "KRX":
        return (
            1,
            "unknown_venue_fallback",
            source_count,
            tokens,
            time_bucket,
            reference_text,
        )
    if (
        context.initial_tier is not None
        and context.initial_formula_version == FORMULA_VERSION
        and 1 <= _safe_int(context.initial_tier, 0) <= 5
    ):
        return (
            _safe_int(context.initial_tier, 1),
            "reused_initial_entry_tier",
            source_count,
            tokens,
            time_bucket,
            reference_text,
        )
    if resolved_time is None:
        return (
            1,
            "missing_reference_time_fallback",
            source_count,
            tokens,
            time_bucket,
            reference_text,
        )
    if source_count <= 0:
        return (
            1,
            "missing_source_signature_fallback",
            source_count,
            tokens,
            time_bucket,
            reference_text,
        )
    if time_bucket == "outside_preferred_krx_window":
        return (
            1,
            "outside_preferred_krx_window",
            source_count,
            tokens,
            time_bucket,
            reference_text,
        )
    if source_count >= 5:
        return (
            2,
            "valid_window_source_count_ge5",
            source_count,
            tokens,
            time_bucket,
            reference_text,
        )
    if source_count <= 2:
        return (
            3,
            "valid_window_source_count_1_2",
            source_count,
            tokens,
            time_bucket,
            reference_text,
        )
    if time_bucket == "krx_morning_0930_1129":
        return (
            4,
            "krx_morning_source_count_3_4",
            source_count,
            tokens,
            time_bucket,
            reference_text,
        )
    return (
        5,
        "krx_afternoon_source_count_3_4",
        source_count,
        tokens,
        time_bucket,
        reference_text,
    )


def resolve_scalping_allocation(
    context: ScalpingSizingContext,
) -> ScalpingSizingDecision:
    """Resolve the only supported scalping sizing decision."""

    ratios, config_valid = _validated_tier_ratios()
    tier, reason, source_count, tokens, time_bucket, reference_text = _select_tier(
        context
    )
    if not config_valid:
        tier = 1
        reason = "invalid_sizing_config_fallback"
    ratio = min(MAX_RATIO, max(0.10, ratios[tier - 1]))
    budget_base = max(0, _safe_int(context.budget_base_krw, 0))
    price = max(0, _safe_int(context.price_krw, 0))
    absolute_cap = max(0, _safe_int(context.absolute_budget_cap_krw, 0))
    uncapped_target_budget = int(float(budget_base) * ratio)
    min_one_share_floor_allowed = bool(
        context.min_one_share_floor_enabled
        and (absolute_cap <= 0 or (price > 0 and absolute_cap >= price))
    )
    target_budget, safe_budget, budget_qty, used_safety_ratio = describe_buy_capacity(
        price,
        budget_base,
        ratio,
        safety_ratio=max(0.0, min(1.0, _safe_float(context.safety_ratio, 0.95))),
        max_budget=absolute_cap,
        allow_min_one_share_over_budget=min_one_share_floor_allowed,
    )
    min_floor_candidate = bool(
        budget_qty == 1 and price > 0 and safe_budget < price and budget_base >= price
    )
    effective_qty = max(0, budget_qty)
    binding_caps: list[str] = []
    absolute_cap_blocks_floor = bool(
        context.min_one_share_floor_enabled
        and absolute_cap > 0
        and price > absolute_cap
        and budget_base >= price
        and budget_qty <= 0
    )
    if absolute_cap > 0 and (
        target_budget < uncapped_target_budget or absolute_cap_blocks_floor
    ):
        binding_caps.append("absolute_budget_cap")

    current_position_qty = max(0, _safe_int(context.current_position_qty, 0))
    max_position_remaining_cap = None
    if context.max_position_qty_cap is not None:
        max_position_remaining_cap = max(
            0,
            _safe_int(context.max_position_qty_cap, 0) - current_position_qty,
        )
    for name, raw_cap in (
        ("cash_orderable_qty_cap", context.cash_orderable_qty_cap),
        ("max_position_qty_cap", max_position_remaining_cap),
        ("remaining_position_qty_cap", context.remaining_position_qty_cap),
        ("stage_qty_cap", context.stage_qty_cap),
        ("broker_qty_cap", context.broker_qty_cap),
    ):
        if raw_cap is None:
            continue
        cap = max(0, _safe_int(raw_cap, 0))
        if cap < effective_qty:
            binding_caps.append(name)
            effective_qty = cap
    min_floor_applied = bool(min_floor_candidate and effective_qty == 1)

    return ScalpingSizingDecision(
        formula_version=FORMULA_VERSION,
        tier=tier,
        ratio=ratio,
        tier_reason=reason,
        source_count=source_count,
        source_tokens=tokens,
        time_bucket=time_bucket,
        reference_time=reference_text,
        venue=infer_scalping_venue(context.reference_time, context.effective_venue),
        target_budget=target_budget,
        safe_budget=safe_budget,
        safety_ratio=used_safety_ratio,
        pre_cap_qty=max(0, budget_qty),
        effective_qty=effective_qty,
        min_one_share_floor_applied=min_floor_applied,
        binding_caps=tuple(binding_caps),
        config_valid=config_valid,
        allocation_stage=str(context.allocation_stage or "unknown"),
        simulation=bool(context.simulation),
    )
