"""Shared scanner WATCHING-budget ownership and quota policy.

This module allocates observation capacity only.  It has no authority over
orders, cash budgets, quantities, providers, or entry/exit thresholds.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from src.engine.scalping.opening_rotation import EntryConfig, is_watch_candidate

GENERAL_SCALPING = "general_scalping"
OPENING_ROTATION = "opening_rotation"
RISING_MISSED = "rising_missed"
VALID_OWNERS = frozenset({GENERAL_SCALPING, OPENING_ROTATION, RISING_MISSED})

PRIMARY_RISING_SOURCES = frozenset(
    {
        "REALTIME_RANK_START",
        "PRICE_JUMP_START",
        "VOLUME_SURGE_POSITIVE",
        "BID_IMBALANCE_SURGE",
    }
)
RISING_LINEAGE_SOURCES = frozenset({"LOW_REBOUND_RISING_MISSED"})


def _source_tokens(value: Any) -> frozenset[str]:
    if isinstance(value, (set, frozenset, list, tuple)):
        values = value
    else:
        values = str(value or "").replace("|", ",").split(",")
    return frozenset(str(item).strip().upper() for item in values if str(item).strip())


def normalize_owner(value: Any, *, default: str = GENERAL_SCALPING) -> str:
    owner = str(value or "").strip().lower()
    if owner in VALID_OWNERS:
        return owner
    return default if default in VALID_OWNERS else GENERAL_SCALPING


def classify_owner(
    *,
    source_signature: Any,
    rising_missed_lineage: Any = "",
    position_tag: Any = "SCANNER",
    day_change_pct: float = 0.0,
    now_dt: datetime | None = None,
    explicit_owner: Any = "",
    missing_default: str = GENERAL_SCALPING,
    opening_config: EntryConfig | None = None,
) -> str:
    """Classify a scanner candidate without granting trading authority."""

    explicit = str(explicit_owner or "").strip().lower()
    if explicit in VALID_OWNERS:
        return explicit

    tokens = _source_tokens(source_signature)
    if rising_missed_lineage or tokens & RISING_LINEAGE_SOURCES:
        return RISING_MISSED

    now_dt = now_dt or datetime.now()
    config = opening_config or EntryConfig()
    if is_watch_candidate(
        position_tag=position_tag,
        source_signature=tokens,
        day_change_pct=float(day_change_pct or 0.0),
        now_dt=now_dt,
        config=config,
    ):
        return OPENING_ROTATION
    if tokens & PRIMARY_RISING_SOURCES:
        return RISING_MISSED
    return normalize_owner(missing_default)


@dataclass(frozen=True)
class WatchBudgetLimits:
    total: int
    general_max: int
    opening_protected: int
    rising_guaranteed: int
    rising_max_with_borrow: int


def limits(total: int, *, opening_window_active: bool) -> WatchBudgetLimits:
    """Return the 1/general + 3/opening + residual/rising allocation."""

    total = max(1, int(total or 1))
    if total < 4:
        return WatchBudgetLimits(
            total=total,
            general_max=0,
            opening_protected=0,
            rising_guaranteed=total,
            rising_max_with_borrow=total,
        )
    general_max = min(1, total)
    opening_protected = (
        min(3, max(0, total - general_max)) if opening_window_active else 0
    )
    rising_guaranteed = max(0, total - general_max - opening_protected)
    # Rising may borrow only unused opening slots, never the general slot.
    rising_max_with_borrow = max(0, total - general_max)
    return WatchBudgetLimits(
        total=total,
        general_max=general_max,
        opening_protected=opening_protected,
        rising_guaranteed=rising_guaranteed,
        rising_max_with_borrow=rising_max_with_borrow,
    )


def owner_allowances(
    owner_counts: dict[str, int],
    *,
    total: int,
    opening_window_active: bool,
) -> dict[str, int]:
    """Return live owner caps after rising borrows unused opening capacity."""

    policy = limits(total, opening_window_active=opening_window_active)
    opening_count = min(
        max(0, int(owner_counts.get(OPENING_ROTATION, 0))),
        policy.opening_protected,
    )
    unused_opening = max(0, policy.opening_protected - opening_count)
    return {
        GENERAL_SCALPING: policy.general_max,
        OPENING_ROTATION: policy.opening_protected,
        RISING_MISSED: min(
            policy.rising_max_with_borrow,
            policy.rising_guaranteed + unused_opening,
        ),
    }


def slot_type(
    owner: Any,
    owner_index: int,
    *,
    total: int,
    opening_window_active: bool,
) -> str:
    owner = normalize_owner(owner)
    if owner != RISING_MISSED:
        return "protected" if owner == OPENING_ROTATION else "bounded"
    policy = limits(total, opening_window_active=opening_window_active)
    return (
        "borrowed_opening_slot"
        if int(owner_index) > policy.rising_guaranteed
        else "guaranteed"
    )
