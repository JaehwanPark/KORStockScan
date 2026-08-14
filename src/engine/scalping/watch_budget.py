"""Shared scanner WATCHING-budget ownership and quota policy.

This module allocates observation capacity only.  It has no authority over
orders, cash budgets, quantities, providers, or entry/exit thresholds.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any

GENERAL_SCALPING = "general_scalping"
OPENING_ROTATION = "opening_rotation"
RISING_MISSED = "rising_missed"
LIMIT_DOWN_ROTATION = "limit_down_rotation"
MARKET_GAINER_SOURCE = "PREV_CLOSE_GAINER"
VALID_OWNERS = frozenset(
    {GENERAL_SCALPING, LIMIT_DOWN_ROTATION, RISING_MISSED}
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


def _safe_epoch(value: Any) -> float:
    try:
        epoch = float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0
    return epoch if epoch > 0.0 else 0.0


def _boolish_true(value: Any) -> bool:
    if value is True:
        return True
    if value is False or value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def market_gainer_first_ai_retention(
    target: dict[str, Any] | None,
    *,
    now_ts: float,
    max_sec: float | None = None,
) -> dict[str, Any]:
    """Protect a reserved market-gainer row until its first evaluated AI result.

    Heavy scanner evaluation is only a producer step and must not close the
    reservation by itself. A provider/preflight failure also remains pending;
    the reservation closes only after an evaluated live/prior-valid AI result
    or the bounded TTL. This controls WATCHING capacity and ordering only.
    """

    target = target if isinstance(target, dict) else {}
    source_signature = target.get("source_signature") or target.get(
        "scanner_source_signature"
    )
    if MARKET_GAINER_SOURCE not in _source_tokens(source_signature):
        return {
            "market_gainer_first_eval_retention_applicable": False,
            "retention_active": False,
            "market_gainer_first_ai_priority_active": False,
        }

    anchor_epoch = _safe_epoch(
        target.get("scanner_promotion_emitted_epoch")
        or target.get("entry_armed_at_epoch")
    )
    if anchor_epoch <= 0.0:
        return {
            "market_gainer_first_eval_retention_applicable": True,
            "retention_active": False,
            "market_gainer_first_ai_priority_active": False,
            "market_gainer_first_eval_retention_reason": "promotion_anchor_missing",
        }

    if max_sec is None:
        raw_max_sec = os.getenv(
            "KORSTOCKSCAN_SCANNER_MARKET_GAINER_FIRST_EVAL_RETENTION_SEC"
        )
        try:
            max_sec = float(raw_max_sec) if str(raw_max_sec or "").strip() else 180.0
        except (TypeError, ValueError):
            max_sec = 180.0
    try:
        normalized_max_sec = float(max_sec)
    except (TypeError, ValueError):
        normalized_max_sec = 180.0
    bounded_max_sec = max(1.0, min(normalized_max_sec, 600.0))
    heavy_eval_epoch = _safe_epoch(target.get("_scanner_last_heavy_eval_attempt_epoch"))
    attempt_epoch = _safe_epoch(target.get("last_watching_ai_attempt_completed_at"))
    confirmed_epoch = _safe_epoch(target.get("last_watching_ai_confirmed_at"))
    attempt_result_source = (
        str(
            target.get("last_watching_ai_attempt_result_source")
            or target.get("last_watching_ai_result_source")
            or ""
        )
        .strip()
        .lower()
    )
    attempt_evaluation_status = (
        str(target.get("last_watching_ai_attempt_evaluation_status") or "")
        .strip()
        .lower()
    )
    attempt_contract_status = (
        str(target.get("last_watching_ai_attempt_contract_status") or "")
        .strip()
        .lower()
    )
    attempt_trusted_value = target.get("last_watching_ai_attempt_trusted")
    attempt_trusted = (
        _boolish_true(attempt_trusted_value)
        if attempt_trusted_value is not None
        else False
    )
    ai_evaluated_observed = bool(
        confirmed_epoch >= anchor_epoch
        or (
            attempt_epoch >= anchor_epoch
            and attempt_evaluation_status == "evaluated"
            and attempt_result_source in {"live", "prior_valid"}
            and attempt_trusted
        )
    )
    heavy_eval_observed = heavy_eval_epoch >= anchor_epoch
    age_sec = max(0.0, float(now_ts) - anchor_epoch)
    retention_active = bool(age_sec < bounded_max_sec and not ai_evaluated_observed)
    if ai_evaluated_observed:
        reason = "first_ai_evaluated_observed"
    elif age_sec >= bounded_max_sec:
        reason = "bounded_retention_expired"
    elif heavy_eval_observed:
        reason = "heavy_eval_observed_awaiting_first_ai_evaluated"
    else:
        reason = "awaiting_first_ai_evaluated"
    return {
        "market_gainer_first_eval_retention_applicable": True,
        "retention_active": retention_active,
        "retention_reason": reason,
        "market_gainer_first_eval_retention_reason": reason,
        "market_gainer_first_ai_priority_active": retention_active,
        "market_gainer_first_eval_retention_age_sec": round(age_sec, 3),
        "market_gainer_first_eval_retention_max_sec": round(bounded_max_sec, 3),
        "market_gainer_first_eval_retention_anchor_epoch": f"{anchor_epoch:.3f}",
        "market_gainer_first_eval_retention_heavy_eval_observed": (heavy_eval_observed),
        "market_gainer_first_eval_retention_ai_terminal_observed": (
            ai_evaluated_observed
        ),
        "market_gainer_first_ai_evaluated_observed": ai_evaluated_observed,
        "market_gainer_first_ai_attempt_result_source": (
            attempt_result_source or "not_observed"
        ),
        "market_gainer_first_ai_attempt_evaluation_status": (
            attempt_evaluation_status or "not_observed"
        ),
        "market_gainer_first_ai_attempt_contract_status": (
            attempt_contract_status or "not_observed"
        ),
        "market_gainer_first_ai_attempt_trusted": attempt_trusted,
        "metric_role": "scanner_observation_capacity",
        "decision_authority": "market_gainer_reserved_watch_retention_only",
        "window_policy": "promotion_to_first_evaluated_ai_result_bounded",
        "sample_floor": "one_reserved_market_gainer_promotion",
        "primary_decision_metric": "first_ai_reach_rate",
        "source_quality_gate": "existing_runtime_source_quality_guards_unchanged",
        "forbidden_uses": (
            "stale_submit_bypass,heavy_eval_eligibility_bypass,provider_route_change,"
            "score_or_threshold_change,order_price_or_quantity_change,"
            "broker_guard_bypass,position_cap_release"
        ),
        "runtime_effect": retention_active,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


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
    now_dt: Any = None,
    explicit_owner: Any = "",
    missing_default: str = GENERAL_SCALPING,
    opening_config: Any = None,
    effective_venue: Any = "",
    market_session_bucket: Any = "",
) -> str:
    """Classify a scanner candidate without granting trading authority."""

    explicit = str(explicit_owner or "").strip().lower()
    if explicit in VALID_OWNERS:
        return explicit

    tokens = _source_tokens(source_signature)
    # Opening Rotation was permanently retired on 2026-08-14.  Keep the
    # compatibility arguments so older callers and archived replays still
    # parse, but never grant scanner ownership or protected capacity.
    del position_tag, day_change_pct, now_dt, opening_config
    del effective_venue, market_session_bucket
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
        "general1_limitdown1_rising_residual_opening_retired_v3"
        if _limit_down_enabled(limit_down_enabled)
        else "general1_rising_residual_opening_retired_v3"
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
    del opening_window_active
    opening_protected = 0
    limit_down_protected = min(
        1 if limit_enabled else 0,
        max(0, total - general_max - opening_protected),
    )
    rising_guaranteed = max(
        0, total - general_max - opening_protected - limit_down_protected
    )
    # Rising may borrow unused limit-down slots, never the general slot.
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
            policy.rising_guaranteed + unused_limit_down,
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
    protected general/limit-down capacity.
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
        return "bounded"
    policy = limits(
        total,
        opening_window_active=opening_window_active,
        limit_down_enabled=limit_down_enabled,
    )
    return (
        (
            "borrowed_observation_slot"
            if _limit_down_enabled(limit_down_enabled)
            else "borrowed_retired_capacity_slot"
        )
        if int(owner_index) > policy.rising_guaranteed
        else "guaranteed"
    )
