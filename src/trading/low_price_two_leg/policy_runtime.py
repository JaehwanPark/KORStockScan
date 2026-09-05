"""Bounded next-PREOPEN policy contract for lower-price two-leg profiles."""

from __future__ import annotations

import hashlib
import json
import math
import os
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from src.trading.low_price_two_leg.economics import (
    ROUND_TRIP_COST_PCT,
    cost_contract,
)
from src.trading.low_price_two_leg.profiles import (
    PRE_RECOMMENDATION_PROFILES,
    PROFILE_REVISION_20260819_EFFECTIVE_DATE,
    PROFILE_REVISION_20260821_EFFECTIVE_DATE,
    PROFILE_REVISION_20260824_EFFECTIVE_DATE,
    PROFILE_REVISION_20260825_EFFECTIVE_DATE,
    PROFILE_REVISION_20260827_EFFECTIVE_DATE,
    PROFILE_REVISION_20260828_EFFECTIVE_DATE,
    PROFILE_REVISION_20260831_EFFECTIVE_DATE,
    PROFILE_REVISION_20260907_EFFECTIVE_DATE,
    PROFILES,
    PROFILES_20260819,
    PROFILES_20260824_PRIOR,
    PROFILES_20260825_PRIOR,
    PROFILES_20260827_PRIOR,
    PROFILES_20260828_PRIOR,
    PROFILES_20260831_PRIOR,
    PROFILES_20260907_PRIOR,
)
from src.utils.constants import DATA_DIR

KST = ZoneInfo("Asia/Seoul")
CANDIDATE_SCHEMA = "low_price_two_leg_policy_candidate_v3"
SUBSET_AUTHORITY_CONTRACT = "low_price_existing_axis_subset_diagnostic_only_v1"
SUPPORTED_CANDIDATE_SCHEMAS = frozenset(
    {
        "low_price_two_leg_policy_candidate_v1",
        "low_price_two_leg_policy_candidate_v2",
        CANDIDATE_SCHEMA,
    }
)
LEGACY_V1_PROFILE_IDS = frozenset(
    {"samsung_heavy_midday", "samsung_heavy_afternoon", "sk_eternix_midday"}
)
LEGACY_V1_LAST_SOURCE_DATE = date(2026, 8, 11)
LEGACY_APPLIED_LAST_TARGET_DATE = date(2026, 8, 12)
LEGACY_TWO_SHARE_APPLIED_LAST_TARGET_DATE = date(2026, 8, 13)
LEGACY_TWO_SHARE_CANDIDATE_LAST_SOURCE_DATE = date(2026, 8, 13)
PRE_EXPANDED_V2_PROFILE_IDS = frozenset(
    {
        "samsung_heavy_midday",
        "samsung_heavy_afternoon",
        "sk_eternix_midday",
        "mirae_asset_morning",
        "jeju_semiconductor_morning",
        "doosan_enerbility_morning",
        "hanwha_ocean_late_morning",
    }
)
PRE_EXPANDED_V2_LAST_SOURCE_DATE = date(2026, 8, 12)
SUPPORTED_SOURCE_REPORT_SCHEMAS = frozenset(
    {
        "low_price_two_leg_tuning_report_v1",
        "low_price_two_leg_tuning_report_v2",
        "low_price_two_leg_tuning_report_v3",
        "low_price_two_leg_tuning_report_v4",
        "low_price_two_leg_tuning_report_v5",
        "low_price_two_leg_tuning_report_v6",
        "low_price_two_leg_tuning_report_v7",
    }
)
APPLIED_SCHEMA = "low_price_two_leg_policy_applied_v1"
CANDIDATE_DIR = DATA_DIR / "threshold_cycle" / "low_price_two_leg" / "candidates"
APPLIED_DIR = DATA_DIR / "threshold_cycle" / "low_price_two_leg" / "applied"
MAX_CANDIDATE_AGE_DAYS = 7
CLEAN_BASELINE_DATE = "2026-06-05"
SOURCE_PROVENANCE_REQUIRED_DATE = date(2026, 9, 5)
PRE_RECOMMENDATION_LAST_TARGET_DATE = (
    PROFILE_REVISION_20260819_EFFECTIVE_DATE - timedelta(days=1)
)
PROFILE_REVISION_20260819_TRANSITION = {
    "effective_target_date": PROFILE_REVISION_20260819_EFFECTIVE_DATE.isoformat(),
    "source_date": "2026-08-18",
    "before_profile_count": 13,
    "after_profile_count": 20,
    "recommendation_count": 14,
    "new_profile_count": 7,
    "logic_revision_count": 7,
    "evidence_path": (
        "data/config/low_price_two_leg_expanded_profile_evidence_2026-08-18.json"
    ),
    "evidence_canonical_sha256": (
        "3f829f002f5ce53615460c55f9fa71211d286c87443794e1bd506f622544d795"
    ),
    "decision_authority": "explicit_user_directed_profile_revision_2026_08_18",
    "existing_order_effect": "none_preserve_prior_policy_custody",
}
PROFILE_REVISION_20260821_TRANSITION = {
    "effective_target_date": PROFILE_REVISION_20260821_EFFECTIVE_DATE.isoformat(),
    "source_date": "2026-08-20",
    "before_profile_count": 20,
    "staged_prior_profile_count": 23,
    "after_profile_count": 27,
    "recommendation_count": 9,
    "new_profile_count": 4,
    "logic_revision_count": 5,
    "approved_profile_ids": [
        "cj_cgv_afternoon",
        "cj_cgv_midday",
        "doosan_enerbility_late_morning",
        "hanse_afternoon",
        "hanse_morning",
        "kakao_late_morning",
        "kakao_midday",
        "samsung_ea_afternoon",
        "samsung_ea_morning",
        "samsung_heavy_morning",
        "sk_eternix_afternoon",
        "sk_telecom_afternoon",
        "sk_telecom_late_morning",
        "tym_afternoon",
        "tym_midday",
    ],
    "evidence_path": (
        "data/config/low_price_two_leg_expanded_profile_evidence_2026-08-20.json"
    ),
    "evidence_canonical_sha256": (
        "36010903a2536f0bd860165e3257eacf967548b68f407522b5fefa54670e86c1"
    ),
    "prior_generation": {
        "source_date": "2026-08-19",
        "recommendation_count": 11,
        "new_profile_count": 3,
        "logic_revision_count": 8,
        "evidence_path": (
            "data/config/low_price_two_leg_expanded_profile_evidence_2026-08-19.json"
        ),
        "evidence_canonical_sha256": (
            "3acf5125074eaf7e48eca0e73c22f037b5e6b1ec354bd5b203cf32f14dea2381"
        ),
        "disposition": "carry_forward_unless_replaced_by_latest_generation",
    },
    "decision_authority": "explicit_user_directed_profile_revision_2026_08_20",
    "existing_order_effect": "none_preserve_prior_policy_custody",
}
PROFILE_REVISION_20260824_TRANSITION = {
    "effective_target_date": PROFILE_REVISION_20260824_EFFECTIVE_DATE.isoformat(),
    "source_date": "2026-08-21",
    "before_profile_count": 27,
    "after_profile_count": 35,
    "recommendation_count": 14,
    "new_profile_count": 8,
    "logic_revision_count": 6,
    "approved_profile_ids": [
        "cj_cgv_afternoon",
        "cj_cgv_late_morning",
        "hanse_afternoon",
        "hanse_late_morning",
        "hanse_midday",
        "hanse_morning",
        "kepco_afternoon",
        "kepco_late_morning",
        "kepco_midday",
        "nhn_afternoon",
        "samsung_ea_late_morning",
        "tym_midday",
        "youngone_afternoon",
        "youngone_morning",
    ],
    "evidence_path": (
        "data/config/low_price_two_leg_expanded_profile_evidence_2026-08-21.json"
    ),
    "evidence_canonical_sha256": (
        "6e25675e9647289bb3313f35dcd8bda9004a17fc7a7c43958f091d3cf18aa0d8"
    ),
    "decision_authority": "explicit_user_directed_profile_revision_2026_08_21",
    "existing_order_effect": "none_preserve_prior_policy_custody",
}
PROFILE_REVISION_20260825_TRANSITION = {
    "effective_target_date": PROFILE_REVISION_20260825_EFFECTIVE_DATE.isoformat(),
    "source_date": "2026-08-24",
    "before_profile_count": 35,
    "after_profile_count": 40,
    "recommendation_count": 12,
    "new_profile_count": 5,
    "logic_revision_count": 7,
    "approved_profile_ids": [
        "cj_cgv_late_morning",
        "hanse_afternoon",
        "hanse_late_morning",
        "hanse_midday",
        "kepco_late_morning",
        "kepco_morning",
        "mirae_asset_late_morning",
        "nhn_afternoon",
        "nhn_late_morning",
        "nhn_morning",
        "sk_eternix_late_morning",
        "youngone_afternoon",
    ],
    "evidence_path": (
        "data/config/low_price_two_leg_expanded_profile_evidence_2026-08-24.json"
    ),
    "evidence_canonical_sha256": (
        "ce447fe0c6d55a5004f821fb450cbe5d6377fc9664f2bee9a5cd6a31ee12d82f"
    ),
    "decision_authority": "explicit_user_directed_profile_revision_2026_08_24",
    "existing_order_effect": "none_preserve_prior_policy_custody",
}
PROFILE_REVISION_20260827_TRANSITION = {
    "effective_target_date": PROFILE_REVISION_20260827_EFFECTIVE_DATE.isoformat(),
    "source_date": "2026-08-26",
    "before_profile_count": 40,
    "after_profile_count": 45,
    "recommendation_count": 12,
    "new_profile_count": 5,
    "logic_revision_count": 7,
    "approved_profile_ids": [
        "cj_cgv_late_morning",
        "doosan_enerbility_afternoon",
        "hanse_late_morning",
        "kepco_morning",
        "mirae_asset_late_morning",
        "nhn_late_morning",
        "samsung_ea_midday",
        "sd_biosensor_late_morning",
        "sd_biosensor_midday",
        "sd_biosensor_morning",
        "sk_eternix_late_morning",
        "sk_telecom_late_morning",
    ],
    "evidence_path": (
        "data/config/low_price_two_leg_expanded_profile_evidence_2026-08-26.json"
    ),
    "evidence_canonical_sha256": (
        "0a7b39dcdf625ed2148bdf7716521e219f70a64f18a9c61892cc67dd42ba6455"
    ),
    "decision_authority": "explicit_user_directed_profile_revision_2026_08_26",
    "existing_order_effect": "none_preserve_prior_policy_custody",
}
PROFILE_REVISION_20260828_TRANSITION = {
    "effective_target_date": PROFILE_REVISION_20260828_EFFECTIVE_DATE.isoformat(),
    "source_date": "2026-08-27",
    "before_profile_count": 45,
    "after_profile_count": 46,
    "recommendation_count": 9,
    "new_profile_count": 1,
    "logic_revision_count": 8,
    "approved_profile_ids": [
        "cj_cgv_midday",
        "hanse_late_morning",
        "kepco_late_morning",
        "mirae_asset_late_morning",
        "samsung_ea_afternoon",
        "samsung_ea_midday",
        "sd_biosensor_late_morning",
        "sd_biosensor_morning",
        "sk_telecom_morning",
    ],
    "evidence_path": (
        "data/config/low_price_two_leg_expanded_profile_evidence_2026-08-27.json"
    ),
    "evidence_canonical_sha256": (
        "12f750f9d719c8d4042574586ac85823f42a4afb429c239c710302d90847be56"
    ),
    "decision_authority": "explicit_user_directed_profile_revision_2026_08_27",
    "existing_order_effect": "none_preserve_prior_policy_custody",
}
PROFILE_REVISION_20260831_TRANSITION = {
    "effective_target_date": PROFILE_REVISION_20260831_EFFECTIVE_DATE.isoformat(),
    "source_date": "2026-08-28",
    "before_profile_count": 46,
    "after_profile_count": 48,
    "recommendation_count": 7,
    "new_profile_count": 2,
    "logic_revision_count": 5,
    "approved_profile_ids": [
        "cj_cgv_midday",
        "fan_ocean_late_morning",
        "fan_ocean_morning",
        "mirae_asset_late_morning",
        "nhn_morning",
        "sk_telecom_morning",
        "tym_midday",
    ],
    "evidence_path": (
        "data/config/low_price_two_leg_expanded_profile_evidence_2026-08-28.json"
    ),
    "evidence_canonical_sha256": (
        "d5f6e6cb6f80e2fa70c1807f39dc18955060f74d14cdf2111821f1a6b9d1e944"
    ),
    "decision_authority": "explicit_user_directed_profile_revision_2026_08_28",
    "existing_order_effect": "none_preserve_prior_policy_custody",
}
PROFILE_REVISION_20260907_TRANSITION = {
    "effective_target_date": PROFILE_REVISION_20260907_EFFECTIVE_DATE.isoformat(),
    "source_date": "2026-09-04",
    "before_profile_count": 48,
    "after_profile_count": 53,
    "recommendation_count": 13,
    "new_profile_count": 5,
    "logic_revision_count": 8,
    "approved_profile_ids": [
        "cj_cgv_morning",
        "doosan_enerbility_afternoon",
        "fan_ocean_afternoon",
        "hanse_morning",
        "hanwha_ocean_late_morning",
        "nhn_afternoon",
        "nhn_late_morning",
        "samsung_ea_afternoon",
        "samsung_ea_midday",
        "samsung_heavy_late_morning",
        "sd_biosensor_midday",
        "sk_telecom_midday",
        "youngone_midday",
    ],
    "runtime_active_profile_count": 50,
    "runtime_profile_exclusions": [
        {
            "profile_id": "cj_cgv_morning",
            "reason": "unified_round_trip_cost_revalidation_nonpositive",
            "source_cost_pct": 0.20,
            "effective_cost_pct": 0.23,
            "source_report": (
                "data/report/low_price_two_leg_expanded_candidate_research/"
                "low_price_two_leg_expanded_candidate_research_2026-09-04.json"
            ),
            "source_profile_id": "existing_079160_morning",
            "revalidated_notional_weighted_ev_pct": {
                "calibration_first_half": -0.004323,
                "calibration_second_half": 0.065530,
                "calibration": 0.030287,
                "holdout": 0.116837,
                "full": 0.054061,
            },
            "release_condition": (
                "new_user_approved_profile_revision_with_positive_calibration_"
                "halves_holdout_and_full_ev_under_current_cost_contract"
            ),
        },
        {
            "profile_id": "youngone_midday",
            "reason": "unified_round_trip_cost_revalidation_nonpositive",
            "source_cost_pct": 0.20,
            "effective_cost_pct": 0.23,
            "source_report": (
                "data/report/low_price_two_leg_expanded_candidate_research/"
                "low_price_two_leg_expanded_candidate_research_2026-09-04.json"
            ),
            "source_profile_id": "existing_111770_midday",
            "revalidated_notional_weighted_ev_pct": {
                "calibration_first_half": 0.020595,
                "calibration_second_half": -0.000262,
                "calibration": 0.009584,
                "holdout": 0.025027,
                "full": 0.012238,
            },
            "release_condition": (
                "new_user_approved_profile_revision_with_positive_calibration_"
                "halves_holdout_and_full_ev_under_current_cost_contract"
            ),
        },
        {
            "profile_id": "sk_telecom_midday",
            "reason": "unified_round_trip_cost_revalidation_nonpositive",
            "source_cost_pct": 0.20,
            "effective_cost_pct": 0.23,
            "source_report": (
                "data/report/low_price_two_leg_expanded_candidate_research/"
                "low_price_two_leg_expanded_candidate_research_2026-09-04.json"
            ),
            "source_profile_id": "existing_017670_midday",
            "revalidated_notional_weighted_ev_pct": {
                "calibration": -0.001478255,
                "holdout": -0.017345954,
                "full": -0.005667687,
            },
            "release_condition": (
                "new_user_approved_profile_revision_with_positive_calibration_"
                "halves_holdout_and_full_ev_under_current_cost_contract"
            ),
        },
    ],
    "evidence_path": (
        "data/config/low_price_two_leg_expanded_profile_evidence_2026-09-04.json"
    ),
    "evidence_canonical_sha256": (
        "aee6d554c5aeaaf69484ac9e90d978174f66adca2a7b5cc88108c8686e3339bd"
    ),
    "decision_authority": "explicit_user_directed_profile_revision_2026_09_04",
    "existing_order_effect": "none_preserve_prior_policy_custody",
}
KAKAO_MORNING_TARGET_TRANSITION = {
    "profile_id": "kakao_morning",
    "axis": "target_ticks",
    "before": 2,
    "after": 3,
    "approved_at_kst": "2026-08-13T10:24:00+09:00",
    "effective_target_date": "2026-08-14",
    "decision_authority": "explicit_user_directed_runtime_policy_transition",
    "reason": "keep_each_sell_above_observed_round_trip_cost_after_shared_average_price",
    "rollback": {
        "trigger": "explicit_user_revert_after_postclose_evidence_review",
        "action": "restore_kakao_morning_target_ticks_2_at_next_preopen",
        "existing_order_effect": "none_do_not_cancel_or_replace_owned_target_orders",
    },
}


def _baseline_policy(profile_id: str, inventory: dict[str, Any]) -> dict[str, Any]:
    policy = inventory[profile_id].policy
    return {
        "rolling_high_drawdown_pct": policy.rolling_high_drawdown_pct,
        "rolling_low_proximity_pct": policy.rolling_low_proximity_pct,
        "lookback_bars": policy.lookback_bars,
        "entry_valid_completed_bars": policy.entry_valid_completed_bars,
        "quantity": policy.quantity,
        "target_ticks": policy.target_ticks,
    }


BASELINE_POLICIES = {
    profile_id: _baseline_policy(profile_id, PROFILES) for profile_id in PROFILES
}
PROFILE_20260819_BASELINE_POLICIES = {
    profile_id: _baseline_policy(profile_id, PROFILES_20260819)
    for profile_id in PROFILES_20260819
}
PROFILE_20260821_BASELINE_POLICIES = {
    profile_id: _baseline_policy(profile_id, PROFILES_20260824_PRIOR)
    for profile_id in PROFILES_20260824_PRIOR
}
PROFILE_20260824_BASELINE_POLICIES = {
    profile_id: _baseline_policy(profile_id, PROFILES_20260825_PRIOR)
    for profile_id in PROFILES_20260825_PRIOR
}
PROFILE_20260825_BASELINE_POLICIES = {
    profile_id: _baseline_policy(profile_id, PROFILES_20260827_PRIOR)
    for profile_id in PROFILES_20260827_PRIOR
}
PROFILE_20260827_BASELINE_POLICIES = {
    profile_id: _baseline_policy(profile_id, PROFILES_20260828_PRIOR)
    for profile_id in PROFILES_20260828_PRIOR
}
PROFILE_20260828_BASELINE_POLICIES = {
    profile_id: _baseline_policy(profile_id, PROFILES_20260831_PRIOR)
    for profile_id in PROFILES_20260831_PRIOR
}
PROFILE_20260907_BASELINE_POLICIES = {
    profile_id: _baseline_policy(profile_id, PROFILES_20260907_PRIOR)
    for profile_id in PROFILES_20260907_PRIOR
}
PRE_RECOMMENDATION_BASELINE_POLICIES = {
    profile_id: _baseline_policy(profile_id, PRE_RECOMMENDATION_PROFILES)
    for profile_id in PRE_RECOMMENDATION_PROFILES
}


def _policy_bounds(policies: dict[str, dict[str, Any]]) -> dict[str, dict[str, float]]:
    return {
        profile_id: {
            "drawdown_min": float(policy["rolling_high_drawdown_pct"]),
            "drawdown_max": round(float(policy["rolling_high_drawdown_pct"]) + 0.25, 6),
            "near_low_min": round(
                max(0.05, float(policy["rolling_low_proximity_pct"]) - 0.10), 6
            ),
            "near_low_max": float(policy["rolling_low_proximity_pct"]),
        }
        for profile_id, policy in policies.items()
    }


POLICY_BOUNDS = _policy_bounds(BASELINE_POLICIES)
PROFILE_20260819_POLICY_BOUNDS = _policy_bounds(PROFILE_20260819_BASELINE_POLICIES)
PROFILE_20260821_POLICY_BOUNDS = _policy_bounds(PROFILE_20260821_BASELINE_POLICIES)
PROFILE_20260824_POLICY_BOUNDS = _policy_bounds(PROFILE_20260824_BASELINE_POLICIES)
PROFILE_20260825_POLICY_BOUNDS = _policy_bounds(PROFILE_20260825_BASELINE_POLICIES)
PROFILE_20260827_POLICY_BOUNDS = _policy_bounds(PROFILE_20260827_BASELINE_POLICIES)
PROFILE_20260828_POLICY_BOUNDS = _policy_bounds(PROFILE_20260828_BASELINE_POLICIES)
PROFILE_20260907_POLICY_BOUNDS = _policy_bounds(PROFILE_20260907_BASELINE_POLICIES)
PRE_RECOMMENDATION_POLICY_BOUNDS = _policy_bounds(PRE_RECOMMENDATION_BASELINE_POLICIES)


def baseline_policies_for_target_date(
    target_date: date,
) -> dict[str, dict[str, Any]]:
    if target_date < PROFILE_REVISION_20260819_EFFECTIVE_DATE:
        return PRE_RECOMMENDATION_BASELINE_POLICIES
    if target_date < PROFILE_REVISION_20260821_EFFECTIVE_DATE:
        return PROFILE_20260819_BASELINE_POLICIES
    if target_date < PROFILE_REVISION_20260824_EFFECTIVE_DATE:
        return PROFILE_20260821_BASELINE_POLICIES
    if target_date < PROFILE_REVISION_20260825_EFFECTIVE_DATE:
        return PROFILE_20260824_BASELINE_POLICIES
    if target_date < PROFILE_REVISION_20260827_EFFECTIVE_DATE:
        return PROFILE_20260825_BASELINE_POLICIES
    if target_date < PROFILE_REVISION_20260828_EFFECTIVE_DATE:
        return PROFILE_20260827_BASELINE_POLICIES
    if target_date < PROFILE_REVISION_20260831_EFFECTIVE_DATE:
        return PROFILE_20260828_BASELINE_POLICIES
    if target_date < PROFILE_REVISION_20260907_EFFECTIVE_DATE:
        return PROFILE_20260907_BASELINE_POLICIES
    return BASELINE_POLICIES


def policy_bounds_for_target_date(target_date: date) -> dict[str, dict[str, float]]:
    if target_date < PROFILE_REVISION_20260819_EFFECTIVE_DATE:
        return PRE_RECOMMENDATION_POLICY_BOUNDS
    if target_date < PROFILE_REVISION_20260821_EFFECTIVE_DATE:
        return PROFILE_20260819_POLICY_BOUNDS
    if target_date < PROFILE_REVISION_20260824_EFFECTIVE_DATE:
        return PROFILE_20260821_POLICY_BOUNDS
    if target_date < PROFILE_REVISION_20260825_EFFECTIVE_DATE:
        return PROFILE_20260824_POLICY_BOUNDS
    if target_date < PROFILE_REVISION_20260827_EFFECTIVE_DATE:
        return PROFILE_20260825_POLICY_BOUNDS
    if target_date < PROFILE_REVISION_20260828_EFFECTIVE_DATE:
        return PROFILE_20260827_POLICY_BOUNDS
    if target_date < PROFILE_REVISION_20260831_EFFECTIVE_DATE:
        return PROFILE_20260828_POLICY_BOUNDS
    if target_date < PROFILE_REVISION_20260907_EFFECTIVE_DATE:
        return PROFILE_20260907_POLICY_BOUNDS
    return POLICY_BOUNDS


def profile_revision_transition(target_date: date) -> dict[str, Any] | None:
    if target_date < PROFILE_REVISION_20260819_EFFECTIVE_DATE:
        return None
    if target_date < PROFILE_REVISION_20260821_EFFECTIVE_DATE:
        return dict(PROFILE_REVISION_20260819_TRANSITION)
    if target_date < PROFILE_REVISION_20260824_EFFECTIVE_DATE:
        return dict(PROFILE_REVISION_20260821_TRANSITION)
    if target_date < PROFILE_REVISION_20260825_EFFECTIVE_DATE:
        return dict(PROFILE_REVISION_20260824_TRANSITION)
    if target_date < PROFILE_REVISION_20260827_EFFECTIVE_DATE:
        return dict(PROFILE_REVISION_20260825_TRANSITION)
    if target_date < PROFILE_REVISION_20260828_EFFECTIVE_DATE:
        return dict(PROFILE_REVISION_20260827_TRANSITION)
    if target_date < PROFILE_REVISION_20260831_EFFECTIVE_DATE:
        return dict(PROFILE_REVISION_20260828_TRANSITION)
    if target_date < PROFILE_REVISION_20260907_EFFECTIVE_DATE:
        return dict(PROFILE_REVISION_20260831_TRANSITION)
    return dict(PROFILE_REVISION_20260907_TRANSITION)


def operator_policy_transitions(target_date: date) -> list[dict[str, Any]]:
    effective_date = date.fromisoformat(
        str(KAKAO_MORNING_TARGET_TRANSITION["effective_target_date"])
    )
    return (
        [dict(KAKAO_MORNING_TARGET_TRANSITION)]
        if (effective_date <= target_date <= PRE_RECOMMENDATION_LAST_TARGET_DATE)
        else []
    )


def apply_operator_policy_transitions(
    policies: dict[str, dict[str, Any]], *, target_date: date
) -> dict[str, dict[str, Any]]:
    """Apply explicit date-scoped operator decisions after candidate selection."""

    transitioned = {profile_id: dict(policy) for profile_id, policy in policies.items()}
    for transition in operator_policy_transitions(target_date):
        profile_id = str(transition["profile_id"])
        axis = str(transition["axis"])
        if profile_id not in transitioned:
            raise ValueError("operator_transition_profile_missing")
        if transitioned[profile_id].get(axis) != transition["before"]:
            raise ValueError("operator_transition_before_value_mismatch")
        transitioned[profile_id][axis] = transition["after"]
    return transitioned


def _canonical_hash(payload: Any) -> str:
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def policy_hash(policies: dict[str, Any]) -> str:
    return _canonical_hash(policies)


def report_artifact_hash(report: dict[str, Any]) -> str:
    canonical = dict(report)
    canonical.pop("artifact_hash", None)
    return _canonical_hash(canonical)


def runtime_policy_binding(
    *, target_date: date, applied_dir: Path = APPLIED_DIR
) -> dict:
    """Bind policy custody to what was applied, never to an unconsumed proposal."""
    path = applied_path(target_date, applied_dir=applied_dir)
    baselines = baseline_policies_for_target_date(target_date)
    if not path.exists():
        return {
            "status": "missing_baseline_only",
            "source_date": target_date.isoformat(),
            "source_path": str(path),
            "policies": {key: dict(value) for key, value in baselines.items()},
        }
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError("source_applied_policy_unreadable") from exc
    valid, reason = validate_applied(payload, target_date=target_date)
    if not valid:
        raise ValueError(f"source_{reason}")
    return {
        "status": "ready",
        "source_date": target_date.isoformat(),
        "source_path": str(path),
        "artifact_hash": _canonical_hash(payload),
        "policies": {
            key: dict(value["policy"]) for key, value in payload["profiles"].items()
        },
    }


def runtime_profile_exclusions(target_date: date) -> list[dict[str, Any]]:
    if target_date < PROFILE_REVISION_20260907_EFFECTIVE_DATE:
        return []
    return json.loads(
        json.dumps(PROFILE_REVISION_20260907_TRANSITION["runtime_profile_exclusions"])
    )


def _finite_number(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def policy_mutations_between(
    before: dict[str, dict[str, Any]], after: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    if set(before) != set(after):
        raise ValueError("policy_mutation_profile_inventory_mismatch")
    mutations: list[dict[str, Any]] = []
    for profile_id in sorted(before):
        baseline = before[profile_id]
        for axis in baseline:
            if before[profile_id][axis] != after[profile_id][axis]:
                mutations.append(
                    {
                        "profile_id": profile_id,
                        "axis": axis,
                        "before": before[profile_id][axis],
                        "after": after[profile_id][axis],
                    }
                )
    return mutations


def _validate_policy_mutations(value: Any) -> tuple[bool, str]:
    if not isinstance(value, list) or len(value) > 1:
        return False, "same_stage_single_axis_contract_invalid"
    if not value:
        return True, "valid"
    item = value[0]
    if not isinstance(item, dict) or set(item) != {
        "profile_id",
        "axis",
        "before",
        "after",
    }:
        return False, "policy_mutation_shape_invalid"
    if item["profile_id"] not in BASELINE_POLICIES or item["axis"] not in {
        "rolling_high_drawdown_pct",
        "rolling_low_proximity_pct",
    }:
        return False, "policy_mutation_axis_invalid"
    before = _finite_number(item["before"])
    after = _finite_number(item["after"])
    if before is None or after is None or before == after:
        return False, "policy_mutation_values_invalid"
    if item["axis"] == "rolling_high_drawdown_pct" and after <= before:
        return False, "policy_mutation_is_not_tightening"
    if item["axis"] == "rolling_low_proximity_pct" and after >= before:
        return False, "policy_mutation_is_not_tightening"
    return True, "valid"


def validate_profile_policy(
    profile_id: str,
    policy: Any,
    *,
    target_date: date | None = None,
    legacy_two_share_candidate: bool = False,
    include_operator_transitions: bool = True,
) -> tuple[bool, str]:
    baselines = (
        BASELINE_POLICIES
        if target_date is None
        else baseline_policies_for_target_date(target_date)
    )
    bounds_by_profile = (
        POLICY_BOUNDS
        if target_date is None
        else policy_bounds_for_target_date(target_date)
    )
    if profile_id not in baselines or not isinstance(policy, dict):
        return False, "profile_or_policy_invalid"
    baseline = baselines[profile_id]
    expected_immutable = dict(baseline)
    if target_date is not None and include_operator_transitions:
        for transition in operator_policy_transitions(target_date):
            if transition["profile_id"] == profile_id:
                expected_immutable[str(transition["axis"])] = transition["after"]
    if set(policy) != set(baseline):
        return False, "policy_key_contract_mismatch"
    for key in (
        "lookback_bars",
        "entry_valid_completed_bars",
        "quantity",
        "target_ticks",
    ):
        if (
            key == "quantity"
            and policy.get(key) == 2
            and (
                legacy_two_share_candidate
                or (
                    target_date is not None
                    and target_date <= LEGACY_TWO_SHARE_APPLIED_LAST_TARGET_DATE
                )
            )
        ):
            continue
        if policy.get(key) != expected_immutable[key]:
            return False, f"immutable_{key}_mismatch"
    drawdown = _finite_number(policy.get("rolling_high_drawdown_pct"))
    near_low = _finite_number(policy.get("rolling_low_proximity_pct"))
    bounds = bounds_by_profile[profile_id]
    if (
        drawdown is None
        or not bounds["drawdown_min"] <= drawdown <= bounds["drawdown_max"]
    ):
        return False, "drawdown_outside_bounded_tightening"
    if (
        near_low is None
        or not bounds["near_low_min"] <= near_low <= bounds["near_low_max"]
    ):
        return False, "near_low_outside_bounded_tightening"
    return True, "valid"


def validate_candidate(
    payload: Any,
    *,
    source_report: dict[str, Any] | None = None,
    require_source_files: bool = False,
) -> tuple[bool, str]:
    if (
        not isinstance(payload, dict)
        or payload.get("schema") not in SUPPORTED_CANDIDATE_SCHEMAS
    ):
        return False, "candidate_schema_invalid"
    try:
        source_date = date.fromisoformat(str(payload.get("source_date") or ""))
    except ValueError:
        return False, "candidate_source_date_invalid"
    if source_date < date.fromisoformat(CLEAN_BASELINE_DATE):
        return False, "candidate_source_date_precedes_clean_baseline"
    if (
        source_date >= SOURCE_PROVENANCE_REQUIRED_DATE
        and payload.get("schema") != CANDIDATE_SCHEMA
    ):
        return False, "candidate_legacy_schema_after_subset_retirement"
    if (
        payload.get("schema") == "low_price_two_leg_policy_candidate_v1"
        and source_date > LEGACY_V1_LAST_SOURCE_DATE
    ):
        return False, "candidate_legacy_schema_after_profile_expansion"
    if (
        payload.get("runtime_effect") is not False
        or payload.get("allowed_runtime_apply") is not False
        or payload.get("actual_order_submitted") is not False
    ):
        return False, "candidate_authority_contract_invalid"
    if payload.get("clean_tuning_baseline_date") != CLEAN_BASELINE_DATE:
        return False, "candidate_clean_baseline_invalid"
    if (
        payload.get("source_report") != "low_price_two_leg_tuning"
        or payload.get("source_report_schema") not in SUPPORTED_SOURCE_REPORT_SCHEMAS
        or payload.get("decision_authority") != "postclose_bounded_candidate_only"
    ):
        return False, "candidate_source_contract_invalid"
    valid, reason = _validate_policy_mutations(payload.get("policy_mutations"))
    if not valid:
        return False, reason
    same_stage_guard = payload.get("same_stage_owner_guard")
    if not isinstance(same_stage_guard, dict) or not isinstance(
        same_stage_guard.get("mutation_present"), bool
    ):
        return False, "candidate_same_stage_owner_guard_invalid"
    if same_stage_guard["mutation_present"] and payload.get("policy_mutations"):
        return False, "candidate_same_stage_owner_conflict"
    profiles = payload.get("profiles")
    source_baselines = baseline_policies_for_target_date(source_date)
    allowed_profile_sets = {frozenset(source_baselines)}
    if payload.get("schema") == "low_price_two_leg_policy_candidate_v1":
        allowed_profile_sets = {LEGACY_V1_PROFILE_IDS}
    elif source_date <= PRE_EXPANDED_V2_LAST_SOURCE_DATE:
        allowed_profile_sets.add(PRE_EXPANDED_V2_PROFILE_IDS)
    if (
        not isinstance(profiles, dict)
        or frozenset(profiles) not in allowed_profile_sets
    ):
        return False, "candidate_profile_set_invalid"
    if any(
        str(item.get("profile_id") or "") not in profiles
        for item in payload.get("policy_mutations") or []
        if isinstance(item, dict)
    ):
        return False, "candidate_mutation_profile_not_in_candidate"
    policies: dict[str, Any] = {}
    for profile_id, item in profiles.items():
        if not isinstance(item, dict):
            return False, f"candidate_{profile_id}_invalid"
        valid, reason = validate_profile_policy(
            profile_id,
            item.get("policy"),
            target_date=source_date,
            include_operator_transitions=False,
            legacy_two_share_candidate=(
                source_date <= LEGACY_TWO_SHARE_CANDIDATE_LAST_SOURCE_DATE
            ),
        )
        if not valid:
            return False, f"candidate_{profile_id}_{reason}"
        if item.get("allowed_runtime_apply") is not True:
            return False, f"candidate_{profile_id}_apply_authority_missing"
        policies[profile_id] = item["policy"]
    if payload.get("policy_hash") != policy_hash(policies):
        return False, "candidate_policy_hash_mismatch"
    if payload.get("schema") == CANDIDATE_SCHEMA:
        # Neither a sample count nor a report/self hash turns an observed-signal
        # subset into a causal counterfactual. Keep actual policy custody only.
        if payload.get("policy_mutations"):
            return False, "candidate_subset_promotion_authority_retired"
        binding = payload.get("source_runtime_policy_binding")
        if (
            payload.get("evaluation_authority_contract") != SUBSET_AUTHORITY_CONTRACT
            or payload.get("source_report_schema")
            != "low_price_two_leg_tuning_report_v7"
            or not isinstance(binding, dict)
            or binding.get("source_date") != source_date.isoformat()
            or binding.get("policies") != policies
        ):
            return False, "candidate_actual_runtime_binding_invalid"
        if binding.get("status") == "missing_baseline_only":
            if policies != source_baselines:
                return False, "candidate_missing_runtime_nonbaseline_policy"
            source_path = Path(str(binding.get("source_path") or ""))
            if (
                source_path.name
                != f"low_price_two_leg_policy_{source_date.isoformat()}.json"
            ):
                return False, "candidate_missing_runtime_source_path_invalid"
            if source_path.exists():
                return False, "candidate_missing_runtime_source_now_present"
        elif binding.get("status") == "ready":
            try:
                applied = json.loads(
                    Path(str(binding.get("source_path") or "")).read_text(
                        encoding="utf-8"
                    )
                )
            except (OSError, ValueError):
                return False, "candidate_actual_runtime_source_unreadable"
            valid, reason = validate_applied(applied, target_date=source_date)
            if (
                not valid
                or _canonical_hash(applied) != binding.get("artifact_hash")
                or {key: item["policy"] for key, item in applied["profiles"].items()}
                != policies
            ):
                return False, "candidate_actual_runtime_source_mismatch"
        else:
            return False, "candidate_actual_runtime_binding_status_invalid"
    if (
        source_date >= SOURCE_PROVENANCE_REQUIRED_DATE
        or payload.get("schema") == CANDIDATE_SCHEMA
    ):
        report_path_text = str(payload.get("source_report_path") or "").strip()
        report_digest = str(payload.get("source_report_artifact_hash") or "")
        source_quality_digest = str(payload.get("source_quality_source_sha256") or "")
        if not report_path_text or len(report_digest) != 64:
            return False, "candidate_source_provenance_missing"
        observed_report = source_report
        if observed_report is None:
            try:
                observed_report = json.loads(
                    Path(report_path_text).read_text(encoding="utf-8")
                )
            except (OSError, json.JSONDecodeError):
                if require_source_files or payload.get("schema") == CANDIDATE_SCHEMA:
                    return False, "candidate_source_report_unreadable"
        if observed_report is not None:
            expected_cost_contract = cost_contract()
            if (
                not isinstance(observed_report, dict)
                or observed_report.get("target_date") != source_date.isoformat()
                or observed_report.get("schema") not in SUPPORTED_SOURCE_REPORT_SCHEMAS
                or observed_report.get("artifact_hash") != report_digest
                or report_artifact_hash(observed_report) != report_digest
            ):
                return False, "candidate_source_report_hash_mismatch"
            if (
                observed_report.get("cost_pct") != ROUND_TRIP_COST_PCT
                or observed_report.get("cost_contract") != expected_cost_contract
            ):
                return False, "candidate_source_cost_contract_invalid"
            if payload.get("schema") == CANDIDATE_SCHEMA and (
                observed_report.get("schema") != payload.get("source_report_schema")
                or observed_report.get("source_runtime_policy_binding")
                != payload.get("source_runtime_policy_binding")
                or observed_report.get("source_quality_preflight")
                != payload.get("source_quality_preflight")
            ):
                return False, "candidate_source_decision_binding_mismatch"
            preflight = observed_report.get("source_quality_preflight") or {}
            tuning_input_allowed = preflight.get("tuning_input_allowed") is True
            if tuning_input_allowed and len(source_quality_digest) != 64:
                return False, "candidate_source_quality_provenance_missing"
            if str(preflight.get("source_sha256") or "") != source_quality_digest:
                return False, "candidate_source_quality_snapshot_mismatch"
            if not tuning_input_allowed and payload.get("policy_mutations"):
                return False, "candidate_source_quality_blocked_mutation_present"
            if require_source_files and tuning_input_allowed:
                try:
                    observed_source_quality_digest = hashlib.sha256(
                        Path(str(preflight.get("source_path") or "")).read_bytes()
                    ).hexdigest()
                except OSError:
                    return False, "candidate_source_quality_unreadable"
                if observed_source_quality_digest != source_quality_digest:
                    return False, "candidate_source_quality_hash_mismatch"
    return True, "valid"


def candidate_policies_with_current_baselines(
    payload: dict[str, Any],
    *,
    target_date: date | None = None,
) -> dict[str, dict[str, Any]]:
    """Normalize a validated candidate across additive profile expansion."""
    valid, reason = validate_candidate(payload)
    if not valid:
        raise ValueError(reason)
    source_date = date.fromisoformat(str(payload["source_date"]))
    effective_target_date = target_date or (source_date + timedelta(days=1))
    target_baselines = baseline_policies_for_target_date(effective_target_date)
    source_baselines = baseline_policies_for_target_date(source_date)
    if source_baselines != target_baselines:
        return {
            profile_id: dict(policy) for profile_id, policy in target_baselines.items()
        }
    normalized: dict[str, dict[str, Any]] = {}
    for profile_id, baseline in target_baselines.items():
        policy = dict(
            (payload.get("profiles") or {}).get(profile_id, {}).get("policy")
            or baseline
        )
        if policy.get("quantity") == 2:
            policy["quantity"] = baseline["quantity"]
        normalized[profile_id] = policy
    return normalized


def validate_applied(payload: Any, *, target_date: date) -> tuple[bool, str]:
    if not isinstance(payload, dict) or payload.get("schema") != APPLIED_SCHEMA:
        return False, "applied_schema_invalid"
    if payload.get("target_date") != target_date.isoformat():
        return False, "applied_target_date_mismatch"
    if (
        payload.get("runtime_effect") is not True
        or payload.get("allowed_runtime_apply") is not True
        or payload.get("actual_order_submitted") is not False
    ):
        return False, "applied_authority_contract_invalid"
    if payload.get("decision_authority") not in {
        "auto_bounded_live_low_price_two_leg_policy",
        "preopen_safe_baseline_fallback",
    }:
        return False, "applied_decision_authority_invalid"
    valid, reason = _validate_policy_mutations(payload.get("policy_mutations"))
    if not valid:
        return False, reason
    expected_transitions = operator_policy_transitions(target_date)
    if list(payload.get("operator_policy_transitions") or []) != expected_transitions:
        return False, "applied_operator_policy_transition_invalid"
    if payload.get("profile_revision_transition") != profile_revision_transition(
        target_date
    ):
        return False, "applied_profile_revision_transition_invalid"
    expected_exclusions = runtime_profile_exclusions(target_date)
    if list(payload.get("runtime_profile_exclusions") or []) != expected_exclusions:
        return False, "applied_runtime_profile_exclusions_invalid"
    profiles = payload.get("profiles")
    if not isinstance(profiles, dict):
        return False, "applied_profile_set_invalid"
    profile_ids = frozenset(profiles)
    allowed_profile_ids = {frozenset(baseline_policies_for_target_date(target_date))}
    if target_date <= LEGACY_APPLIED_LAST_TARGET_DATE:
        allowed_profile_ids.add(LEGACY_V1_PROFILE_IDS)
    if profile_ids not in allowed_profile_ids:
        return False, "applied_profile_set_invalid"
    if any(
        str(item.get("profile_id") or "") not in profiles
        for item in payload.get("policy_mutations") or []
        if isinstance(item, dict)
    ):
        return False, "applied_mutation_profile_not_in_applied"
    policies: dict[str, Any] = {}
    for profile_id, item in profiles.items():
        if not isinstance(item, dict):
            return False, f"applied_{profile_id}_invalid"
        valid, reason = validate_profile_policy(
            profile_id, item.get("policy"), target_date=target_date
        )
        if not valid:
            return False, f"applied_{profile_id}_{reason}"
        policies[profile_id] = item["policy"]
    excluded_ids = {item["profile_id"] for item in expected_exclusions}
    if any(
        profiles[profile_id].get("selection_status")
        != "runtime_quarantined_unified_cost_nonpositive"
        for profile_id in excluded_ids
    ):
        return False, "applied_runtime_profile_exclusion_status_invalid"
    if payload.get("policy_hash") != policy_hash(policies):
        return False, "applied_policy_hash_mismatch"
    return True, "valid"


def applied_path(target_date: date, *, applied_dir: Path = APPLIED_DIR) -> Path:
    return applied_dir / f"low_price_two_leg_policy_{target_date.isoformat()}.json"


def load_applied_profile_policy(
    profile_id: str,
    *,
    target_date: date,
    applied_dir: Path = APPLIED_DIR,
) -> tuple[dict[str, Any] | None, str, str]:
    path = applied_path(target_date, applied_dir=applied_dir)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, "", f"applied_policy_unreadable:{type(exc).__name__}"
    valid, reason = validate_applied(payload, target_date=target_date)
    if not valid:
        return None, "", reason
    exclusion = next(
        (
            item
            for item in runtime_profile_exclusions(target_date)
            if item["profile_id"] == profile_id
        ),
        None,
    )
    if exclusion is not None:
        return None, "", f"runtime_profile_quarantined:{exclusion['reason']}"
    item = payload["profiles"].get(profile_id)
    if not isinstance(item, dict):
        return None, "", "applied_profile_policy_missing"
    return dict(item["policy"]), str(payload["policy_hash"]), "ready"


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp_name, 0o640)
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def baseline_applied_payload(*, target_date: date, reason: str) -> dict[str, Any]:
    baselines = baseline_policies_for_target_date(target_date)
    policies = apply_operator_policy_transitions(
        {profile_id: dict(policy) for profile_id, policy in baselines.items()},
        target_date=target_date,
    )
    exclusions = runtime_profile_exclusions(target_date)
    excluded_ids = {item["profile_id"] for item in exclusions}
    payload = {
        "schema": APPLIED_SCHEMA,
        "target_date": target_date.isoformat(),
        "applied_at_kst": datetime.now(tz=KST).isoformat(timespec="seconds"),
        "source_date": None,
        "source_candidate": None,
        "selection_status": reason,
        "policy_hash": policy_hash(policies),
        "policy_mutations": [],
        "profiles": {
            profile_id: {
                "selection_status": (
                    "runtime_quarantined_unified_cost_nonpositive"
                    if profile_id in excluded_ids
                    else reason
                ),
                "policy": policy,
            }
            for profile_id, policy in policies.items()
        },
        "runtime_profile_exclusions": exclusions,
        "decision_authority": "preopen_safe_baseline_fallback",
        "runtime_effect": True,
        "allowed_runtime_apply": True,
        "actual_order_submitted": False,
        "forbidden_uses": [
            "candidate_quantity_target_or_entry_validity_change",
            "target_change_outside_recorded_operator_policy_transition",
            "stop_loss_or_forced_exit_creation",
            "provider_bot_cap_or_broker_guard_change",
        ],
    }
    transitions = operator_policy_transitions(target_date)
    if transitions:
        payload["operator_policy_transitions"] = transitions
    revision = profile_revision_transition(target_date)
    if revision:
        payload["profile_revision_transition"] = revision
    return payload
