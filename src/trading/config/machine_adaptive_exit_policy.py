"""Research-only approval contract; no live registry, policy writer or loader.

The initial risk envelope has not been approved. Research readiness therefore
cannot become PREOPEN eligibility. Floors are supplied by an independently
frozen evaluation contract, never by a candidate choosing its own validator.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import hashlib
import json
from typing import Any, Mapping
from collections import deque

from src.trading.order.adaptive_exit.models import finite, positive_int

FAMILY = "machine_adaptive_exit_v1"
EVIDENCE_SCHEMA = "machine_adaptive_exit_evidence_v1"
AUTHORITY = {
    "runtime_effect": False,
    "allowed_runtime_apply": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
}


def canonical_sha256(payload: Mapping[str, Any]) -> str:
    """Hash the child only; the containing report's byte hash is external."""
    return hashlib.sha256(
        json.dumps(
            {k: v for k, v in payload.items() if k != "canonical_sha256"},
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class EvaluationContract:
    contract_hash: str
    scope_key: str
    policy_hash: str
    train_end: str
    holdout_start: str
    holdout_end: str
    # Includes zero-yield trading dates and expiry; not positive days only.
    minimum_unique_episodes: int
    minimum_holdout_episodes: int
    minimum_observed_days: int
    minimum_resolved_coverage_pct: float
    maximum_censored_pct: float
    minimum_absolute_uplift_pct_points: float
    maximum_p10_deterioration_pct_points: float

    def __post_init__(self) -> None:
        if not all(
            isinstance(v, str) and v
            for v in (self.contract_hash, self.scope_key, self.policy_hash)
        ):
            raise ValueError("missing_frozen_evaluation_identity")
        dates = [
            date.fromisoformat(v)
            for v in (self.train_end, self.holdout_start, self.holdout_end)
        ]
        if not date(2026, 6, 5) <= dates[0] < dates[1] <= dates[2]:
            raise ValueError("invalid_clean_chronological_split")
        if not all(
            positive_int(v)
            for v in (
                self.minimum_unique_episodes,
                self.minimum_holdout_episodes,
                self.minimum_observed_days,
            )
        ):
            raise ValueError("invalid_sample_floors")
        if self.minimum_holdout_episodes > self.minimum_unique_episodes:
            raise ValueError("holdout_floor_exceeds_total")
        if (
            not finite(self.minimum_resolved_coverage_pct)
            or not 0 < self.minimum_resolved_coverage_pct <= 100
        ):
            raise ValueError("invalid_coverage_floor")
        if (
            not finite(self.maximum_censored_pct)
            or not 0 <= self.maximum_censored_pct < 100
        ):
            raise ValueError("invalid_censor_bound")
        if (
            not finite(self.minimum_absolute_uplift_pct_points)
            or self.minimum_absolute_uplift_pct_points <= 0
        ):
            raise ValueError("positive_absolute_uplift_required")
        if (
            not finite(self.maximum_p10_deterioration_pct_points)
            or self.maximum_p10_deterioration_pct_points < 0
        ):
            raise ValueError("invalid_tail_bound")


def assess_research_evidence(
    evidence: Mapping[str, Any],
    contract: EvaluationContract,
) -> dict[str, Any]:
    """Validate a summary produced from isolated, purged same-scope episodes.

    This is a necessary, not sufficient, economic review. Uncertainty/stress
    studies and execution readiness are separate blockers for live activation.
    """
    errors: list[str] = []
    if evidence.get("schema") != EVIDENCE_SCHEMA:
        errors.append("evidence_schema_invalid")
    authority = evidence.get("authority")
    if (
        not isinstance(authority, Mapping)
        or authority != AUTHORITY
        or any(authority.get(k) is not v for k, v in AUTHORITY.items())
    ):
        errors.append("source_only_authority_invalid")
    try:
        digest = canonical_sha256(evidence)
    except (TypeError, ValueError):
        digest = None
    if digest is None or evidence.get("canonical_sha256") != digest:
        errors.append("evidence_digest_invalid")
    for key, expected in (
        ("evaluation_contract_hash", contract.contract_hash),
        ("scope_key", contract.scope_key),
        ("policy_hash", contract.policy_hash),
        ("holdout_start", contract.holdout_start),
        ("holdout_end", contract.holdout_end),
    ):
        if evidence.get(key) != expected:
            errors.append(key + "_mismatch")
    for flag in ("source_quality_valid", "cost_contract_valid", "purged_split_valid"):
        if evidence.get(flag) is not True:
            errors.append(flag + "_required")
    for key, floor in (
        ("unique_episodes", contract.minimum_unique_episodes),
        ("holdout_unique_episodes", contract.minimum_holdout_episodes),
        ("observed_days", contract.minimum_observed_days),
    ):
        value = evidence.get(key)
        if not positive_int(value) or value < floor:
            errors.append(key + "_floor")
    total, held_out = evidence.get("unique_episodes"), evidence.get(
        "holdout_unique_episodes"
    )
    if positive_int(total) and positive_int(held_out) and held_out > total:
        errors.append("holdout_count_exceeds_unique_population")
    for key, bound, above in (
        ("resolved_coverage_pct", contract.minimum_resolved_coverage_pct, True),
        ("right_censored_pct", contract.maximum_censored_pct, False),
        (
            "p10_deterioration_pct_points",
            contract.maximum_p10_deterioration_pct_points,
            False,
        ),
    ):
        value = evidence.get(key)
        if not finite(value) or (value < bound if above else value > bound):
            errors.append(key + "_bound")
        elif key.endswith("_pct") and not 0 <= value <= 100:
            errors.append(key + "_invalid")
    # No relative-uplift division by a zero/negative baseline; no simultaneous
    # 5/10/20-day positive requirement and no per-trade positive-return gate.
    for prefix in ("primary", "holdout"):
        uplift = evidence.get(prefix + "_paired_net_ev_uplift_pct_points")
        pnl = evidence.get(prefix + "_paired_net_pnl_uplift_krw")
        ev = evidence.get(prefix + "_candidate_net_ev_pct")
        required_uplift = (
            contract.minimum_absolute_uplift_pct_points if prefix == "primary" else 0
        )
        if not finite(uplift) or uplift < required_uplift:
            errors.append(prefix + "_absolute_ev_uplift")
        if not finite(pnl) or (pnl <= 0 if prefix == "primary" else pnl < 0):
            errors.append(prefix + "_net_profit_uplift")
        if not finite(ev) or ev <= 0:
            errors.append(prefix + "_positive_candidate_net_ev")
    return {
        "decision": "research_ready" if not errors else "research_blocked",
        "errors": errors,
        "eligible_for_next_preopen": False,
        "runtime_blocker": "blocked_missing_initial_authority_and_owner_adapter",
        "authority": dict(AUTHORITY),
    }


def assess_sample_attainability(
    *,
    daily_mature_unique_counts: tuple[int, ...],
    minimum: int,
    rolling_trading_days: int,
    daily_hard_capacity: int | None,
) -> dict[str, Any]:
    """Conditional ETA using mature arrivals, zero days, and rolling expiry.

    Callers must supply every consecutive observed trading date, one count per
    already mature unique episode (not leg/tick). A rate projection is not a
    promise, evidence of positive EV, or permission to lower the sample floor.
    A structural claim requires an explicit hard capacity, not merely low flow.
    """
    if (
        not positive_int(minimum)
        or not positive_int(rolling_trading_days)
        or (
            not isinstance(daily_mature_unique_counts, tuple)
            or len(daily_mature_unique_counts) > rolling_trading_days
            or any(type(v) is not int or v < 0 for v in daily_mature_unique_counts)
            or daily_hard_capacity is not None
            and not positive_int(daily_hard_capacity)
        )
    ):
        raise ValueError("invalid_same_denominator_yield_contract")
    if daily_hard_capacity is not None and any(
        v > daily_hard_capacity for v in daily_mature_unique_counts
    ):
        raise ValueError("observed_yield_exceeds_declared_hard_capacity")
    current = sum(daily_mature_unique_counts)
    result = {
        "current": current,
        "required": minimum,
        "deficit": max(0, minimum - current),
        "projected_trading_days_to_floor": None,
        "includes_zero_days_and_rolling_expiry": True,
        "projection_is_conditional_not_guaranteed": True,
    }
    if current >= minimum:
        return result | {"status": "sample_floor_met_not_economic_approval"}
    if (
        daily_hard_capacity is not None
        and daily_hard_capacity * rolling_trading_days < minimum
    ):
        return result | {
            "status": "structural_population_exhaustion",
            "reason": "declared_capacity_below_floor",
        }
    if not daily_mature_unique_counts or current == 0:
        return result | {
            "status": "blocked_missing_evidence",
            "reason": "no_positive_mature_arrival_rate",
        }
    # Integer-scaled projection avoids inventing fractional observed episodes
    # and float rounding at an exactly attainable boundary.
    divisor = len(daily_mature_unique_counts)
    window = deque(
        (v * divisor for v in daily_mature_unique_counts), maxlen=rolling_trading_days
    )
    for step in range(1, rolling_trading_days + 1):
        window.append(current)
        if sum(window) >= minimum * divisor:
            return result | {
                "status": "time_resolvable_shortage_projection",
                "projected_trading_days_to_floor": step,
            }
    return result | {
        "status": "blocked_missing_evidence",
        "reason": "rolling_floor_unreachable_at_observed_rate",
    }
