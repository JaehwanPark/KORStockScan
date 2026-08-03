"""Shared scanner WATCHING-budget ownership and quota policy.

This module allocates observation capacity only.  It has no authority over
orders, cash budgets, quantities, providers, or entry/exit thresholds.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import os
from typing import Any

from src.engine.scalping.opening_rotation import EntryConfig, is_watch_candidate

GENERAL_SCALPING = "general_scalping"
OPENING_ROTATION = "opening_rotation"
RISING_MISSED = "rising_missed"
LIMIT_DOWN_ROTATION = "limit_down_rotation"
MARKET_GAINER_SOURCE = "PREV_CLOSE_GAINER"
VALID_OWNERS = frozenset(
    {GENERAL_SCALPING, OPENING_ROTATION, LIMIT_DOWN_ROTATION, RISING_MISSED}
)

PRIMARY_RISING_SOURCES = frozenset(
    {
        "REALTIME_RANK_START",
        "PRICE_JUMP_START",
        "VOLUME_SURGE_POSITIVE",
        "BID_IMBALANCE_SURGE",
        MARKET_GAINER_SOURCE,
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
    limit_down_protected: int
    rising_guaranteed: int
    rising_max_with_borrow: int


def _limit_down_enabled(value: bool | None = None) -> bool:
    if value is not None:
        return bool(value)
    return str(
        os.getenv("KORSTOCKSCAN_LIMIT_DOWN_WATCH_ENABLED", "false")
    ).strip().lower() in {"1", "true", "yes", "y", "on"}


def policy_version(limit_down_enabled: bool | None = None) -> str:
    return (
        "general1_opening2_limitdown1_rising_residual_v1"
        if _limit_down_enabled(limit_down_enabled)
        else "general1_opening3_rising_residual_v1"
    )


def limits(
    total: int,
    *,
    opening_window_active: bool,
    limit_down_enabled: bool | None = None,
) -> WatchBudgetLimits:
    """Return legacy or limit-down-aware observation allocation."""

    total = max(1, int(total or 1))
    limit_enabled = _limit_down_enabled(limit_down_enabled)
    if total < 4:
        return WatchBudgetLimits(
            total=total,
            general_max=0,
            opening_protected=0,
            limit_down_protected=0,
            rising_guaranteed=total,
            rising_max_with_borrow=total,
        )
    general_max = min(1, total)
    opening_target = 2 if limit_enabled else 3
    opening_protected = (
        min(opening_target, max(0, total - general_max)) if opening_window_active else 0
    )
    limit_down_protected = min(
        1 if limit_enabled else 0,
        max(0, total - general_max - opening_protected),
    )
    rising_guaranteed = max(
        0, total - general_max - opening_protected - limit_down_protected
    )
    # Rising may borrow unused opening/limit-down slots, never the general slot.
    rising_max_with_borrow = max(0, total - general_max)
    return WatchBudgetLimits(
        total=total,
        general_max=general_max,
        opening_protected=opening_protected,
        limit_down_protected=limit_down_protected,
        rising_guaranteed=rising_guaranteed,
        rising_max_with_borrow=rising_max_with_borrow,
    )


def owner_allowances(
    owner_counts: dict[str, int],
    *,
    total: int,
    opening_window_active: bool,
    limit_down_enabled: bool | None = None,
) -> dict[str, int]:
    """Return caps after rising borrows unused opening/limit-down capacity."""

    policy = limits(
        total,
        opening_window_active=opening_window_active,
        limit_down_enabled=limit_down_enabled,
    )
    opening_count = min(
        max(0, int(owner_counts.get(OPENING_ROTATION, 0))),
        policy.opening_protected,
    )
    unused_opening = max(0, policy.opening_protected - opening_count)
    limit_down_count = min(
        max(0, int(owner_counts.get(LIMIT_DOWN_ROTATION, 0))),
        policy.limit_down_protected,
    )
    unused_limit_down = max(0, policy.limit_down_protected - limit_down_count)
    return {
        GENERAL_SCALPING: policy.general_max,
        OPENING_ROTATION: policy.opening_protected,
        LIMIT_DOWN_ROTATION: policy.limit_down_protected,
        RISING_MISSED: min(
            policy.rising_max_with_borrow,
            policy.rising_guaranteed + unused_opening + unused_limit_down,
        ),
    }


def rising_source_reservation(
    total: int,
    *,
    requested_slots: int,
    opening_window_active: bool,
    limit_down_enabled: bool | None = None,
) -> int:
    """Clamp a source sub-allocation to the guaranteed rising budget.

    The reservation never expands the global WATCHING cap and never borrows
    protected general/opening/limit-down capacity.
    """

    policy = limits(
        total,
        opening_window_active=opening_window_active,
        limit_down_enabled=limit_down_enabled,
    )
    return min(
        policy.rising_guaranteed,
        max(0, int(requested_slots or 0)),
    )


def slot_type(
    owner: Any,
    owner_index: int,
    *,
    total: int,
    opening_window_active: bool,
    limit_down_enabled: bool | None = None,
) -> str:
    raw_owner = str(owner or "").strip().lower()
    if raw_owner == LIMIT_DOWN_ROTATION:
        return "protected_limit_down_observation"
    owner = normalize_owner(owner)
    if owner != RISING_MISSED:
        return "protected" if owner == OPENING_ROTATION else "bounded"
    policy = limits(
        total,
        opening_window_active=opening_window_active,
        limit_down_enabled=limit_down_enabled,
    )
    return (
        (
            "borrowed_observation_slot"
            if _limit_down_enabled(limit_down_enabled)
            else "borrowed_opening_slot"
        )
        if int(owner_index) > policy.rising_guaranteed
        else "guaranteed"
    )
