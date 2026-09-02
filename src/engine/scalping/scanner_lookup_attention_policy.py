"""Fail-closed runtime loader for the scanner lookup-attention weight policy.

The postclose producer owns evidence and policy creation.  This module only
validates the latest prior-trading-day artifact and returns a bounded bonus for
sorting candidates *inside* their existing scanner priority tier.  It never
changes source eligibility, watch-slot ownership, an order, or a safety guard.
"""

from __future__ import annotations

from datetime import date
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path
import re
from typing import Any

from src.utils.market_day import count_krx_trading_days, is_krx_trading_day

PROJECT_ROOT = Path(__file__).resolve().parents[3]
POLICY_DIR = (
    PROJECT_ROOT / "data" / "threshold_cycle" / "scanner_lookup_attention_policy"
)
SOURCE_REPORT_DIR = PROJECT_ROOT / "data" / "report" / "scanner_lookup_attention_tuning"
REPORT_TYPE = "scanner_lookup_attention_auto_promotion_policy"
SCHEMA_VERSION = 1
POLICY_VERSION = "scanner_lookup_attention_weight_v1"
DECISION_AUTHORITY = "user_directed_bounded_scanner_weight_auto_apply"
ACTIVATION_MODE = "latest_valid_prior_trading_date_policy_auto_loaded"
USER_AUTHORITY = "user_directed_lookup_attention_auto_promotion_2026_09_02"
MIN_SCORE = 0.60
MAX_BONUS_POINTS = 200.0
MAX_SOURCE_AGE_SEC = 120.0
MAX_FUTURE_SKEW_SEC = 5.0
MIN_TOTAL_COMPLETED = 20
MIN_COHORT_COMPLETED = 10
MIN_TRADING_DATES = 5
MIN_COHORT_DATES = 3
MIN_EV_UPLIFT_PCT = 0.10
MAX_TAIL_DEGRADATION_PCT = 0.25
MIN_WORST_NET_RETURN_PCT = -5.0
ELIGIBLE_VENUES = ["KRX"]
ELIGIBLE_SESSION_BUCKETS = ["krx_regular"]
NON_LIVE_STATUSES = {
    "hold_sample",
    "hold_no_edge",
    "source_quality_blocked",
    "forward_holdout_armed",
}


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _inactive(reason: str, **extra: Any) -> dict[str, Any]:
    return {
        "active": False,
        "state": "inactive",
        "reason": reason,
        "policy_version": POLICY_VERSION,
        "policy_source_date": "",
        "policy_artifact_sha256": "",
        "min_score": MIN_SCORE,
        "max_bonus_points": MAX_BONUS_POINTS,
        "max_source_age_sec": MAX_SOURCE_AGE_SEC,
        "same_priority_tier_only": True,
        "allowed_runtime_apply": False,
        **extra,
    }


def _finite_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _count_at_least(evidence: dict[str, Any], key: str, minimum: int) -> bool:
    value = _finite_number(evidence.get(key))
    return bool(value is not None and value.is_integer() and value >= minimum)


def _latest_prior_path(target: date, policy_dir: Path) -> tuple[date, Path] | None:
    candidates: list[tuple[date, Path]] = []
    for path in policy_dir.glob("scanner_lookup_attention_policy_*.json"):
        suffix = path.stem.removeprefix("scanner_lookup_attention_policy_")
        try:
            source_date = date.fromisoformat(suffix)
        except ValueError:
            continue
        if source_date < target:
            candidates.append((source_date, path))
    return max(candidates, default=None, key=lambda item: item[0])


def _evidence_valid(evidence: Any) -> bool:
    if not isinstance(evidence, dict):
        return False
    candidate_ev = _finite_number(
        evidence.get("candidate_source_quality_adjusted_ev_pct")
    )
    uplift = _finite_number(evidence.get("candidate_control_ev_uplift_pct"))
    candidate_p10 = _finite_number(evidence.get("candidate_downside_p10_pct"))
    control_p10 = _finite_number(evidence.get("control_downside_p10_pct"))
    candidate_worst = _finite_number(evidence.get("candidate_worst_net_return_pct"))
    holdout_candidate_ev = _finite_number(
        evidence.get("forward_holdout_candidate_source_quality_adjusted_ev_pct")
    )
    holdout_uplift = _finite_number(
        evidence.get("forward_holdout_candidate_control_ev_uplift_pct")
    )
    holdout_candidate_p10 = _finite_number(
        evidence.get("forward_holdout_candidate_downside_p10_pct")
    )
    holdout_control_p10 = _finite_number(
        evidence.get("forward_holdout_control_downside_p10_pct")
    )
    holdout_candidate_worst = _finite_number(
        evidence.get("forward_holdout_candidate_worst_net_return_pct")
    )
    base_and_holdout_valid = bool(
        _count_at_least(evidence, "completed_outcome_count", MIN_TOTAL_COMPLETED)
        and _count_at_least(
            evidence, "candidate_completed_outcome_count", MIN_COHORT_COMPLETED
        )
        and _count_at_least(
            evidence, "control_completed_outcome_count", MIN_COHORT_COMPLETED
        )
        and _count_at_least(evidence, "trading_date_count", MIN_TRADING_DATES)
        and _count_at_least(evidence, "candidate_trading_date_count", MIN_COHORT_DATES)
        and _count_at_least(evidence, "control_trading_date_count", MIN_COHORT_DATES)
        and _count_at_least(
            evidence, "forward_holdout_completed_outcome_count", MIN_TOTAL_COMPLETED
        )
        and _count_at_least(
            evidence, "forward_holdout_trading_date_count", MIN_TRADING_DATES
        )
        and _count_at_least(
            evidence,
            "forward_holdout_candidate_completed_outcome_count",
            MIN_COHORT_COMPLETED,
        )
        and _count_at_least(
            evidence,
            "forward_holdout_control_completed_outcome_count",
            MIN_COHORT_COMPLETED,
        )
        and _count_at_least(
            evidence,
            "forward_holdout_candidate_trading_date_count",
            MIN_COHORT_DATES,
        )
        and _count_at_least(
            evidence,
            "forward_holdout_control_trading_date_count",
            MIN_COHORT_DATES,
        )
        and candidate_ev is not None
        and candidate_ev > 0.0
        and uplift is not None
        and uplift >= MIN_EV_UPLIFT_PCT
        and candidate_p10 is not None
        and control_p10 is not None
        and candidate_p10 >= control_p10 - MAX_TAIL_DEGRADATION_PCT
        and candidate_worst is not None
        and candidate_worst >= MIN_WORST_NET_RETURN_PCT
        and holdout_candidate_ev is not None
        and holdout_candidate_ev > 0.0
        and holdout_uplift is not None
        and holdout_uplift >= MIN_EV_UPLIFT_PCT
        and holdout_candidate_p10 is not None
        and holdout_control_p10 is not None
        and holdout_candidate_p10 >= holdout_control_p10 - MAX_TAIL_DEGRADATION_PCT
        and holdout_candidate_worst is not None
        and holdout_candidate_worst >= MIN_WORST_NET_RETURN_PCT
    )
    if not base_and_holdout_valid:
        return False
    post_apply_mature = evidence.get("post_apply_mature")
    if post_apply_mature is False:
        return True
    if post_apply_mature is not True:
        return False
    post_candidate_ev = _finite_number(
        evidence.get("post_apply_candidate_source_quality_adjusted_ev_pct")
    )
    post_uplift = _finite_number(
        evidence.get("post_apply_candidate_control_ev_uplift_pct")
    )
    post_candidate_p10 = _finite_number(
        evidence.get("post_apply_candidate_downside_p10_pct")
    )
    post_control_p10 = _finite_number(
        evidence.get("post_apply_control_downside_p10_pct")
    )
    post_candidate_worst = _finite_number(
        evidence.get("post_apply_candidate_worst_net_return_pct")
    )
    return bool(
        _count_at_least(
            evidence, "post_apply_completed_outcome_count", MIN_TOTAL_COMPLETED
        )
        and _count_at_least(
            evidence, "post_apply_trading_date_count", MIN_TRADING_DATES
        )
        and _count_at_least(
            evidence,
            "post_apply_candidate_completed_outcome_count",
            MIN_COHORT_COMPLETED,
        )
        and _count_at_least(
            evidence,
            "post_apply_control_completed_outcome_count",
            MIN_COHORT_COMPLETED,
        )
        and _count_at_least(
            evidence, "post_apply_candidate_trading_date_count", MIN_COHORT_DATES
        )
        and _count_at_least(
            evidence, "post_apply_control_trading_date_count", MIN_COHORT_DATES
        )
        and post_candidate_ev is not None
        and post_candidate_ev > 0.0
        and post_uplift is not None
        and post_uplift >= MIN_EV_UPLIFT_PCT
        and post_candidate_p10 is not None
        and post_control_p10 is not None
        and post_candidate_p10 >= post_control_p10 - MAX_TAIL_DEGRADATION_PCT
        and post_candidate_worst is not None
        and post_candidate_worst >= MIN_WORST_NET_RETURN_PCT
    )


def _validate_payload(payload: Any, *, source_date: date) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["policy_payload_not_object"]
    expected_scalar = {
        "schema_version": SCHEMA_VERSION,
        "report_type": REPORT_TYPE,
        "target_date": source_date.isoformat(),
        "status": "live_auto_apply_ready",
        "decision_authority": DECISION_AUTHORITY,
        "activation_mode": ACTIVATION_MODE,
        "user_authority": USER_AUTHORITY,
        "operator_approval_required": False,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "allowed_runtime_apply": True,
        "source_quality_status": "pass",
    }
    for key, expected in expected_scalar.items():
        if payload.get(key) != expected:
            errors.append(f"policy_contract_mismatch:{key}")
    try:
        holdout_armed_since = date.fromisoformat(
            str(payload.get("holdout_armed_since") or "")
        )
    except ValueError:
        errors.append("policy_holdout_armed_since_invalid")
    else:
        if holdout_armed_since > source_date or not is_krx_trading_day(
            holdout_armed_since
        ):
            errors.append("policy_holdout_armed_since_out_of_range")

    policy = payload.get("policy") if isinstance(payload.get("policy"), dict) else {}
    expected_policy = {
        "policy_version": POLICY_VERSION,
        "min_lookup_attention_score": MIN_SCORE,
        "max_bonus_points": MAX_BONUS_POINTS,
        "max_source_age_sec": MAX_SOURCE_AGE_SEC,
        "rollback_bonus_points": 0.0,
        "same_priority_tier_only": True,
        "priority_tier_or_slot_change_allowed": False,
        "weight_formula": "linear_above_min_score_capped_at_max_bonus",
        "eligible_venues": ELIGIBLE_VENUES,
        "eligible_session_buckets": ELIGIBLE_SESSION_BUCKETS,
    }
    for key, expected in expected_policy.items():
        if policy.get(key) != expected:
            errors.append(f"policy_weight_contract_mismatch:{key}")

    if not _evidence_valid(payload.get("evidence")):
        errors.append("policy_evidence_contract_invalid")
    report_hash = str(payload.get("source_report_artifact_sha256") or "")
    if not re.fullmatch(r"[0-9a-f]{64}", report_hash):
        errors.append("policy_source_report_hash_invalid")
    artifact_hash = str(payload.get("artifact_sha256") or "")
    try:
        expected_hash = canonical_sha256(
            {key: value for key, value in payload.items() if key != "artifact_sha256"}
        )
    except (TypeError, ValueError):
        expected_hash = ""
    if not expected_hash or artifact_hash != expected_hash:
        errors.append("policy_artifact_sha256_invalid")
    try:
        forbidden = set(payload.get("forbidden_uses") or [])
    except TypeError:
        forbidden = set()
    required_forbidden = {
        "priority_tier_or_slot_ownership_change",
        "candidate_pool_or_source_eligibility_change",
        "buy_drop_threshold_or_provider_change",
        "order_price_quantity_cap_or_broker_guard_change",
        "stale_conflict_or_hard_safety_bypass",
    }
    if not required_forbidden.issubset(forbidden):
        errors.append("policy_forbidden_uses_incomplete")
    return errors


def validate_policy_payload(payload: Any, *, source_date: date) -> list[str]:
    """Public validation contract shared by runtime and postclose verification."""

    return _validate_payload(payload, source_date=source_date)


def _non_live_payload_valid(payload: Any, *, source_date: date) -> bool:
    if not isinstance(payload, dict) or payload.get("status") not in NON_LIVE_STATUSES:
        return False
    expected = {
        "schema_version": SCHEMA_VERSION,
        "report_type": REPORT_TYPE,
        "target_date": source_date.isoformat(),
        "decision_authority": DECISION_AUTHORITY,
        "activation_mode": ACTIVATION_MODE,
        "user_authority": USER_AUTHORITY,
        "operator_approval_required": False,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "allowed_runtime_apply": False,
    }
    if any(payload.get(key) != value for key, value in expected.items()):
        return False
    policy = payload.get("policy") if isinstance(payload.get("policy"), dict) else {}
    expected_policy = {
        "policy_version": POLICY_VERSION,
        "min_lookup_attention_score": MIN_SCORE,
        "max_bonus_points": MAX_BONUS_POINTS,
        "max_source_age_sec": MAX_SOURCE_AGE_SEC,
        "rollback_bonus_points": 0.0,
        "same_priority_tier_only": True,
        "priority_tier_or_slot_change_allowed": False,
        "weight_formula": "linear_above_min_score_capped_at_max_bonus",
        "eligible_venues": ELIGIBLE_VENUES,
        "eligible_session_buckets": ELIGIBLE_SESSION_BUCKETS,
    }
    if any(policy.get(key) != value for key, value in expected_policy.items()):
        return False
    try:
        expected_hash = canonical_sha256(
            {key: value for key, value in payload.items() if key != "artifact_sha256"}
        )
    except (TypeError, ValueError):
        return False
    return payload.get("artifact_sha256") == expected_hash


def _source_report_valid(
    payload: dict[str, Any], *, source_date: date, report_dir: Path
) -> bool:
    path = (
        report_dir / f"scanner_lookup_attention_tuning_{source_date.isoformat()}.json"
    )
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    if not isinstance(report, dict):
        return False
    try:
        expected_hash = canonical_sha256(
            {key: value for key, value in report.items() if key != "artifact_sha256"}
        )
    except (TypeError, ValueError):
        return False
    source_quality = (
        report.get("source_quality")
        if isinstance(report.get("source_quality"), dict)
        else {}
    )
    symbol_master = (
        report.get("official_symbol_master")
        if isinstance(report.get("official_symbol_master"), dict)
        else {}
    )
    try:
        policy_evidence_hash = canonical_sha256(payload.get("evidence"))
    except (TypeError, ValueError):
        return False
    return bool(
        report.get("schema_version") == 1
        and report.get("report_type") == "scanner_lookup_attention_tuning"
        and report.get("target_date") == source_date.isoformat()
        and report.get("status") == "live_auto_apply_ready"
        and report.get("decision_authority") == DECISION_AUTHORITY
        and report.get("user_authority") == USER_AUTHORITY
        and source_quality.get("status") == "pass"
        and symbol_master.get("status") == "pass"
        and report.get("runtime_policy_provenance_status") == "pass"
        and report.get("policy_evidence_sha256") == policy_evidence_hash
        and report.get("allowed_runtime_apply") is True
        and report.get("runtime_effect") is False
        and report.get("actual_order_submitted") is False
        and report.get("broker_order_forbidden") is True
        and report.get("artifact_sha256") == expected_hash
        and payload.get("source_report_artifact_sha256") == expected_hash
    )


@lru_cache(maxsize=16)
def _load_active_cached(
    target_iso: str, policy_dir_text: str, report_dir_text: str
) -> dict[str, Any]:
    try:
        target = date.fromisoformat(target_iso)
    except ValueError:
        return _inactive("target_date_invalid")
    if not is_krx_trading_day(target):
        return _inactive("target_date_not_krx_trading_day")
    latest = _latest_prior_path(target, Path(policy_dir_text))
    if latest is None:
        return _inactive("prior_policy_missing")
    source_date, path = latest
    if (
        not is_krx_trading_day(source_date)
        or count_krx_trading_days(source_date, target) != 1
    ):
        return _inactive(
            "prior_policy_not_latest_trading_day",
            policy_source_date=source_date.isoformat(),
        )
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _inactive(
            "prior_policy_unreadable",
            policy_source_date=source_date.isoformat(),
        )
    if payload.get("status") != "live_auto_apply_ready":
        if _non_live_payload_valid(payload, source_date=source_date):
            return _inactive(
                "prior_policy_not_live_auto_apply_ready",
                policy_source_date=source_date.isoformat(),
                promotion_status=str(payload.get("status") or ""),
            )
        return _inactive(
            "prior_policy_contract_invalid",
            policy_source_date=source_date.isoformat(),
            validation_errors=["non_live_policy_contract_invalid"],
        )
    errors = _validate_payload(payload, source_date=source_date)
    if errors:
        return _inactive(
            "prior_policy_contract_invalid",
            policy_source_date=source_date.isoformat(),
            validation_errors=errors,
        )
    if not _source_report_valid(
        payload, source_date=source_date, report_dir=Path(report_dir_text)
    ):
        return _inactive(
            "prior_source_report_contract_invalid",
            policy_source_date=source_date.isoformat(),
        )
    policy = payload["policy"]
    return {
        "active": True,
        "state": "live_auto_applied",
        "reason": "latest_prior_trading_date_policy_valid",
        "policy_version": policy["policy_version"],
        "policy_source_date": source_date.isoformat(),
        "policy_artifact_sha256": payload["artifact_sha256"],
        "source_report_artifact_sha256": payload["source_report_artifact_sha256"],
        "min_score": float(policy["min_lookup_attention_score"]),
        "max_bonus_points": float(policy["max_bonus_points"]),
        "max_source_age_sec": float(policy["max_source_age_sec"]),
        "same_priority_tier_only": True,
        "allowed_runtime_apply": True,
    }


def load_active_policy(
    target_date: date | str,
    *,
    policy_dir: Path = POLICY_DIR,
    report_dir: Path = SOURCE_REPORT_DIR,
) -> dict[str, Any]:
    target_iso = (
        target_date.isoformat() if isinstance(target_date, date) else str(target_date)
    )
    return dict(
        _load_active_cached(
            target_iso,
            str(policy_dir.resolve()),
            str(report_dir.resolve()),
        )
    )


def clear_policy_cache() -> None:
    _load_active_cached.cache_clear()


def bounded_bonus(
    lookup_attention_score: Any, policy_state: dict[str, Any]
) -> dict[str, Any]:
    base = {
        "bonus_points": 0.0,
        "applied": False,
        "runtime_effect": False,
        "state": str(policy_state.get("state") or "inactive"),
        "reason": str(policy_state.get("reason") or "policy_inactive"),
    }
    if policy_state.get("active") is not True:
        return base
    score = _finite_number(lookup_attention_score)
    if score is None or not 0.0 <= score <= 1.0:
        return {**base, "state": "source_quality_blocked", "reason": "score_invalid"}
    minimum = float(policy_state["min_score"])
    maximum_bonus = float(policy_state["max_bonus_points"])
    if score < minimum:
        return {
            **base,
            "state": "loaded_below_threshold",
            "reason": "lookup_attention_score_below_policy_minimum",
        }
    denominator = max(1e-9, 1.0 - minimum)
    bonus = min(maximum_bonus, maximum_bonus * (score - minimum) / denominator)
    return {
        **base,
        "bonus_points": round(max(0.0, bonus), 6),
        "applied": bonus > 0.0,
        "runtime_effect": bonus > 0.0,
        "state": "applied_same_priority_tier" if bonus > 0.0 else "loaded_at_floor",
        "reason": "bounded_linear_bonus" if bonus > 0.0 else "policy_floor_zero_bonus",
    }


__all__ = [
    "ACTIVATION_MODE",
    "DECISION_AUTHORITY",
    "ELIGIBLE_SESSION_BUCKETS",
    "ELIGIBLE_VENUES",
    "MAX_BONUS_POINTS",
    "MAX_FUTURE_SKEW_SEC",
    "MAX_SOURCE_AGE_SEC",
    "MAX_TAIL_DEGRADATION_PCT",
    "MIN_COHORT_COMPLETED",
    "MIN_COHORT_DATES",
    "MIN_EV_UPLIFT_PCT",
    "MIN_SCORE",
    "MIN_TOTAL_COMPLETED",
    "MIN_TRADING_DATES",
    "MIN_WORST_NET_RETURN_PCT",
    "POLICY_DIR",
    "POLICY_VERSION",
    "REPORT_TYPE",
    "SCHEMA_VERSION",
    "SOURCE_REPORT_DIR",
    "USER_AUTHORITY",
    "bounded_bonus",
    "canonical_sha256",
    "clear_policy_cache",
    "load_active_policy",
    "validate_policy_payload",
]
