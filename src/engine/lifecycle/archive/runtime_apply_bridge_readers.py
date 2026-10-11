"""Historical read-only helpers; no active policy publisher or CLI.

Only existing forensic consumers retain these calculations. Live callers use
their native role owners and permanent retirement fences.
"""

from __future__ import annotations


import json


from datetime import date, datetime


from pathlib import Path


from typing import Any


from src.engine.auto_promotion_contracts import (
    primary_ev_uplift_passes,
    tier2_validation_passed,
)


from src.engine.automation.source_quality_clean_baseline import (
    clean_baseline_policy,
    is_date_allowed,
    report_generated_before_clean_baseline,
)


from src.utils.constants import DATA_DIR


from src.engine.lifecycle.archive.lifecycle_bucket_discovery_readers import (
    SCALE_IN_LIVE_AUTO_FAMILY,
)
from src.engine.lifecycle.archive.lifecycle_bucket_discovery_compat_paths import (
    discovery_report_path,
)


from src.engine.lifecycle.greenfield_authority import (
    validate_greenfield_policy_contract,
)


LDM_REPORT_DIR = DATA_DIR / "report" / "lifecycle_decision_matrix"


SCALE_IN_BRIDGE_FAMILY = SCALE_IN_LIVE_AUTO_FAMILY


GREENFIELD_REAL_ENV_FAMILY = "greenfield_real_environment_authority"


SCALE_IN_PYRAMID_BUCKET_TYPE = "arm"


SCALE_IN_PYRAMID_BUCKET_KEY = "PYRAMID"


SCALE_IN_AVG_DOWN_BUCKET_TYPE = "arm"


SCALE_IN_AVG_DOWN_BUCKET_KEY = "AVG_DOWN"


SCALE_IN_SOURCE_ONLY_EXCLUSION_REASON = (
    "paired_add_lifecycle_replay_or_final_label_missing"
)


SCALE_IN_REOPEN_CONDITIONS = [
    "paired_add_lifecycle_replay_implemented",
    "final_scale_in_labels_available",
    "incremental_notional_ev_pct_non_null",
    "source_quality_gate_pass",
    "target_env_keys_mapped",
    "hard_broker_stale_quantity_cooldown_provider_cap_guards_preserved",
]


ARCHIVED_RUNTIME_APPLY_BRIDGE_FAMILIES: set[str] = set()


def _load_json(path: Path) -> dict[str, Any]:
    try:
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def validate_greenfield_policy_payload(
    policy: dict[str, Any], *, expected_version: str | None = None
) -> str:
    if not policy:
        return "greenfield_policy_file_invalid"
    if str(policy.get("policy_id") or "") != GREENFIELD_REAL_ENV_FAMILY:
        return "greenfield_policy_id_mismatch"
    return validate_greenfield_policy_contract(
        policy, expected_version=expected_version
    )


def validate_greenfield_policy_file(
    policy_file: str, *, expected_version: str | None = None
) -> str:
    policy_file = str(policy_file or "").strip()
    if not policy_file:
        return "greenfield_policy_file_missing"
    policy_path = Path(policy_file)
    if not policy_path.exists():
        return "greenfield_policy_file_missing"
    return validate_greenfield_policy_payload(
        _load_json(policy_path), expected_version=expected_version
    )


def _safe_float(value: Any, default: float | None = None) -> float | None:
    try:
        if value in (None, "", "-", "None"):
            return default
        number = float(value)
    except Exception:
        return default
    return number if number == number else default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except Exception:
        return default


def _scale_confirmation_reports(target_date: str) -> list[dict[str, Any]]:
    """Load one independent prior-date canonical MTD confirmation artifact."""
    policy = clean_baseline_policy()
    if not is_date_allowed(target_date, policy):
        return []
    candidates: list[tuple[str, Path]] = []
    for path in LDM_REPORT_DIR.glob("lifecycle_decision_matrix_*_mtd.json"):
        report_date = path.stem.removeprefix("lifecycle_decision_matrix_").removesuffix(
            "_mtd"
        )
        if report_date < target_date and is_date_allowed(report_date, policy):
            candidates.append((report_date, path))
    if not candidates:
        return []
    report_date, path = max(candidates, key=lambda item: item[0])
    if not path.exists() or report_generated_before_clean_baseline(path, policy):
        return []
    payload = _load_json(path)
    attribution = (
        payload.get("scale_in_bucket_attribution")
        if isinstance(payload.get("scale_in_bucket_attribution"), dict)
        else {}
    )
    if str(payload.get("date") or "") != report_date:
        return []
    if str(payload.get("window_policy") or "") != "mtd":
        return []
    if str(attribution.get("window_policy") or "") != "mtd":
        return []
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    source_dates = [
        str(item) for item in (summary.get("source_dates") or []) if str(item)
    ]
    if len(source_dates) < 2:
        return []
    if source_dates[-1] != report_date or any(
        item >= target_date for item in source_dates
    ):
        return []
    if any(not is_date_allowed(item, policy) for item in source_dates):
        return []
    if summary.get("clean_baseline_excluded_source_dates") != []:
        return []
    if summary.get("excluded_daily_report_dates") not in (None, {}):
        return []
    unavailable = [
        str(item)
        for item in (summary.get("unavailable_daily_report_dates") or [])
        if str(item)
    ]
    try:
        if any(date.fromisoformat(item).weekday() < 5 for item in unavailable):
            return []
    except ValueError:
        return []
    return [payload]


def _find_bucket(
    payload: dict[str, Any], section: str, bucket_type: str, bucket_key: str
) -> dict[str, Any]:
    buckets = (
        payload.get(section, {}).get("buckets", [])
        if isinstance(payload.get(section), dict)
        else []
    )
    for item in buckets:
        if not isinstance(item, dict):
            continue
        if (
            str(item.get("bucket_type") or "") == bucket_type
            and str(item.get("bucket_key") or "") == bucket_key
        ):
            return item
    return {}


def _state_for_bucket(
    current: dict[str, Any],
    history: list[dict[str, Any]],
    *,
    section: str,
    bucket_type: str,
    bucket_key: str,
    positive_edge: bool,
) -> tuple[str, dict[str, Any]]:
    if not current or str(current.get("source_quality_gate") or "") != "pass":
        return "blocked_source_quality", {"confirmation_count": 0, "conflict_count": 0}
    route = str(current.get("recommended_route") or "")
    expected_route = (
        "candidate_recovery_or_relax"
        if positive_edge
        else "candidate_tighten_or_exclude"
    )
    if route != expected_route:
        return "blocked_source_quality", {
            "confirmation_count": 0,
            "conflict_count": 0,
            "blocked_route": route or "missing",
            "expected_route": expected_route,
        }
    current_ev = _safe_float(current.get("source_quality_adjusted_ev_pct"), 0.0) or 0.0
    if positive_edge and current_ev <= 0:
        return "blocked_source_quality", {"confirmation_count": 0, "conflict_count": 0}
    if (not positive_edge) and current_ev >= 0:
        return "blocked_source_quality", {"confirmation_count": 0, "conflict_count": 0}
    if not primary_ev_uplift_passes(current_ev, positive_edge=positive_edge):
        return "hold_no_edge", {
            "confirmation_count": 0,
            "conflict_count": 0,
            "primary_ev_uplift_floor_passed": False,
            "primary_ev_uplift_threshold_pct": 1.0,
            "runtime_bridge_exclusion_reason": "primary_ev_uplift_below_live_floor",
        }

    confirmations = 0
    conflicts = 0
    for payload in history:
        bucket = _find_bucket(payload, section, bucket_type, bucket_key)
        if not bucket or str(bucket.get("source_quality_gate") or "") != "pass":
            continue
        if (
            section == "scale_in_bucket_attribution"
            and str(bucket.get("scale_in_ev_coverage_state") or "") != "v2_ready"
        ):
            continue
        if (
            section == "scale_in_bucket_attribution"
            and bucket.get("runtime_authority_ready") is not True
        ):
            continue
        ev = _safe_float(bucket.get("source_quality_adjusted_ev_pct"), None)
        if ev is None:
            continue
        if primary_ev_uplift_passes(ev, positive_edge=positive_edge):
            confirmations += 1
        else:
            conflicts += 1
    meta = {"confirmation_count": confirmations, "conflict_count": conflicts}
    if conflicts:
        return "blocked_rolling_conflict", meta
    if confirmations <= 0:
        meta.update(
            {
                "daily_only_auto_apply": False,
                "runtime_bridge_exclusion_reason": "rolling_authority_confirmation_missing",
            }
        )
        return "hold_rolling_confirmation_missing", meta
    meta["daily_only_auto_apply"] = False
    return "live_auto_apply_ready", meta


def _discovery_scale_bucket_ready(
    discovery: dict[str, Any], *, bucket_type: str, bucket_key: str
) -> bool:
    for item in discovery.get("live_auto_apply_candidates") or []:
        if not _discovery_live_candidate_contract_passed(item):
            continue
        if str(item.get("live_auto_apply_family") or "") != SCALE_IN_BRIDGE_FAMILY:
            continue
        if str(item.get("stage") or "") != "scale_in":
            continue
        if (
            str(item.get("bucket_type") or "") == bucket_type
            and str(item.get("bucket_key") or "") == bucket_key
        ):
            return True
    return False


def _discovery_candidate_tier2_passed(item: dict[str, Any]) -> bool:
    contract = (
        item.get("auto_promotion_contract")
        if isinstance(item.get("auto_promotion_contract"), dict)
        else {}
    )
    status = (
        item.get("ai_review_status")
        or item.get("lifecycle_bucket_discovery_ai_review_status")
        or contract.get("tier2_status")
    )
    return tier2_validation_passed(status)


def _discovery_live_candidate_contract_passed(item: Any) -> bool:
    if not isinstance(item, dict):
        return False
    family = str(item.get("live_auto_apply_family") or "")
    if not family or family in ARCHIVED_RUNTIME_APPLY_BRIDGE_FAMILIES:
        return False
    if str(item.get("classification_state") or "") != "live_auto_apply_ready":
        return False
    if item.get("allowed_runtime_apply") is False:
        return False
    if item.get("broker_order_forbidden") is True:
        return False
    if str(item.get("source_quality_gate") or "pass") != "pass":
        return False
    if str(item.get("stage") or "") == "lifecycle_flow":
        primary_book = str(
            item.get("primary_sample_book")
            or item.get("parent_primary_sample_book")
            or ""
        )
        real_joined = max(
            _safe_int(item.get("real_joined_sample"), 0),
            _safe_int(item.get("parent_real_joined_sample"), 0),
        )
        if primary_book != "real" or real_joined < 10:
            return False
    return _discovery_candidate_tier2_passed(item)


def _discovery_summary_meta(discovery: dict[str, Any]) -> dict[str, Any]:
    summary = (
        discovery.get("summary") if isinstance(discovery.get("summary"), dict) else {}
    )
    return {
        "lifecycle_bucket_discovery_source_contract_status": summary.get(
            "source_contract_status"
        ),
        "lifecycle_bucket_discovery_ai_review_status": summary.get(
            "ai_two_pass_review_status"
        ),
    }


def _discovery_candidate_meta(
    *,
    family: str,
    discovery: dict[str, Any],
    discovery_live_by_family: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    meta = _discovery_summary_meta(discovery)
    item = discovery_live_by_family.get(family) or {}
    if item:
        meta.update(
            {
                "lifecycle_bucket_discovery_bucket_id": item.get("bucket_id"),
                "lifecycle_bucket_discovery_classification_state": item.get(
                    "classification_state"
                ),
                "lifecycle_bucket_discovery_bucket_relation": item.get(
                    "bucket_relation"
                ),
                "lifecycle_bucket_discovery_ai_final_decision": item.get(
                    "ai_final_decision"
                ),
                "lifecycle_bucket_discovery_ai_final_reason": item.get(
                    "ai_final_reason"
                ),
                "lifecycle_bucket_discovery_ai_followup_required": item.get(
                    "ai_review_followup_required"
                ),
                "lifecycle_bucket_discovery_ai_block_ignored_reason": item.get(
                    "ai_review_block_ignored_reason"
                ),
            }
        )
    return {key: value for key, value in meta.items() if value not in (None, "", [])}


def _scale_source(bucket: dict[str, Any], *, role: str) -> dict[str, Any]:
    return {
        "role": role,
        "bucket_type": bucket.get("bucket_type"),
        "bucket_key": bucket.get("bucket_key"),
        "joined_sample": bucket.get("joined_sample"),
        "source_quality_adjusted_ev_pct": bucket.get("source_quality_adjusted_ev_pct"),
        "recommended_route": bucket.get("recommended_route"),
        "source_quality_gate": bucket.get("source_quality_gate"),
        "scale_in_ev_coverage_state": bucket.get("scale_in_ev_coverage_state"),
        "counterfactual_method": bucket.get("counterfactual_method"),
        "runtime_authority_ready": bucket.get("runtime_authority_ready"),
        "runtime_authority_block_reason": bucket.get("runtime_authority_block_reason"),
    }


def _scale_source_link(
    target_date: str, source_buckets: list[dict[str, Any]]
) -> dict[str, Any]:
    source_bucket_keys = [
        str(item.get("bucket_key") or "").strip() for item in source_buckets
    ]
    return {
        "source_artifact": "lifecycle_decision_matrix",
        "source_section": "scale_in_bucket_attribution",
        "source_date": target_date,
        "family": SCALE_IN_BRIDGE_FAMILY,
        "threshold_version": f"{SCALE_IN_BRIDGE_FAMILY}:{target_date}",
        "source_bucket_keys": [key for key in source_bucket_keys if key],
        "source_buckets": [
            {
                "bucket_type": item.get("bucket_type"),
                "bucket_key": item.get("bucket_key"),
                "role": item.get("role"),
                "scale_in_ev_coverage_state": item.get("scale_in_ev_coverage_state"),
                "runtime_authority_ready": item.get("runtime_authority_ready"),
                "runtime_authority_block_reason": item.get(
                    "runtime_authority_block_reason"
                ),
            }
            for item in source_buckets
        ],
    }


def _scale_candidate_legacy_blocked(
    *,
    target_date: str,
    ev_label_version: str,
    pyramid: dict[str, Any],
    avg_down: dict[str, Any],
    discovery: dict[str, Any],
    discovery_live_by_family: dict[str, dict[str, Any]],
    discovery_available: bool,
) -> dict[str, Any]:
    discovery_meta = _discovery_candidate_meta(
        family=SCALE_IN_BRIDGE_FAMILY,
        discovery=discovery,
        discovery_live_by_family=discovery_live_by_family,
    )
    has_v2_observation = ev_label_version == "incremental_counterfactual_v2"
    authority_reasons = [
        str(bucket.get("runtime_authority_block_reason") or "").strip()
        for bucket in (pyramid, avg_down)
        if isinstance(bucket, dict)
        and str(bucket.get("runtime_authority_block_reason") or "").strip()
    ]
    observed_authority_reason = (
        authority_reasons[0]
        if authority_reasons
        else (
            "runtime_authority_sample_not_observed"
            if has_v2_observation
            else "incremental_counterfactual_v2_label_missing"
        )
    )
    blocked_role = (
        "v2_treatment_path_observation_not_runtime_authority"
        if has_v2_observation
        else "legacy_v1_state_profit_frozen_not_runtime_authority"
    )
    source_buckets = []
    if pyramid:
        source_buckets.append(_scale_source(pyramid, role=blocked_role))
    if avg_down:
        source_buckets.append(_scale_source(avg_down, role=blocked_role))
    blocked_state = (
        "collecting_incremental_ev_runtime_authority_sample"
        if has_v2_observation
        and observed_authority_reason
        in {
            "no_natural_sample",
            "evaluated_no_runtime_eligible_sample",
            "runtime_authority_sample_not_observed",
        }
        else (
            "blocked_incremental_ev_runtime_authority"
            if has_v2_observation
            else "blocked_legacy_v1_label_missing_incremental_ev"
        )
    )
    source_bucket_keys = [
        str(item.get("bucket_key") or "").strip() for item in source_buckets
    ]
    return {
        "candidate_id": f"{SCALE_IN_BRIDGE_FAMILY}:{target_date}",
        "family": SCALE_IN_BRIDGE_FAMILY,
        "stage": "scale_in",
        "priority": 39,
        "bridge_candidate_state": blocked_state,
        "approval_required": False,
        "human_approval_required": False,
        "live_auto_apply": False,
        "allowed_runtime_apply": False,
        "runtime_effect": False,
        "runtime_effect_after_approval": (
            "blocked_until_runtime_authority_sample_available"
            if has_v2_observation
            else "blocked_until_incremental_counterfactual_v2_label_available"
        ),
        "target_env_keys": [],
        "recommended_values": {
            "effective_qty_cap": 1,
            "threshold_version": f"{SCALE_IN_BRIDGE_FAMILY}:{target_date}",
            "calibration_state": (
                f"source_only_{observed_authority_reason}"
                if has_v2_observation
                else "blocked_legacy_v1_label"
            ),
            "ev_label_version": ev_label_version or "missing",
            "legacy_state_label_not_runtime_authority": not has_v2_observation,
            "treatment_path_observation_not_runtime_authority": has_v2_observation,
            "source_only_keep_collecting": True,
            "runtime_authority_block_reason": observed_authority_reason,
        },
        "current_values": {
            "effective_qty_cap": 1,
            "scalping_enable_pyramid": True,
            "reversal_add_min_ai_score": 60,
            "reversal_add_min_buy_pressure": 55.0,
            "reversal_add_min_tick_accel": 0.95,
        },
        "source_bucket_keys": [key for key in source_bucket_keys if key],
        "source_buckets": source_buckets,
        "source_link": _scale_source_link(target_date, source_buckets),
        "explicit_runtime_exclusion": True,
        "runtime_exclusion_reason": SCALE_IN_SOURCE_ONLY_EXCLUSION_REASON,
        "bridge_exclusion_reason": SCALE_IN_SOURCE_ONLY_EXCLUSION_REASON,
        "reopen_conditions": SCALE_IN_REOPEN_CONDITIONS,
        "next_review_stage": "next_postclose_runtime_apply_gap_audit",
        "observe_only_reference_buckets": [],
        "rolling_confirmation": (
            {
                "pyramid": {
                    "runtime_authority_ready": False,
                    "block_reason": str(
                        pyramid.get("runtime_authority_block_reason")
                        or observed_authority_reason
                    ),
                },
                "avg_down": {
                    "runtime_authority_ready": False,
                    "block_reason": str(
                        avg_down.get("runtime_authority_block_reason")
                        or observed_authority_reason
                    ),
                },
            }
            if has_v2_observation
            else {
                "pyramid": {"legacy_v1_frozen": True},
                "avg_down": {"legacy_v1_frozen": True},
            }
        ),
        **discovery_meta,
        "primary_decision_metric": "incremental_notional_ev_pct",
        "scale_in_ev_label_version": ev_label_version or "missing",
        "decision_authority": "lifecycle_bucket_discovery_live_auto_apply",
        "forbidden_uses": [
            "scale_in_safety_guard_bypass",
            "intraday_threshold_mutation",
            "provider_route_change",
            "bot_restart_trigger",
        ],
    }


def _scale_candidate(
    payload: dict[str, Any],
    history: list[dict[str, Any]],
    target_date: str,
    *,
    discovery_live_families: set[str],
    discovery_live_by_family: dict[str, dict[str, Any]],
    discovery: dict[str, Any],
    discovery_available: bool,
) -> dict[str, Any]:
    scale_attribution = (
        payload.get("scale_in_bucket_attribution")
        if isinstance(payload.get("scale_in_bucket_attribution"), dict)
        else {}
    )
    ev_label_version = str(scale_attribution.get("scale_in_ev_label_version") or "")

    pyramid = _find_bucket(
        payload,
        "scale_in_bucket_attribution",
        SCALE_IN_PYRAMID_BUCKET_TYPE,
        SCALE_IN_PYRAMID_BUCKET_KEY,
    )
    avg_down = _find_bucket(
        payload,
        "scale_in_bucket_attribution",
        SCALE_IN_AVG_DOWN_BUCKET_TYPE,
        SCALE_IN_AVG_DOWN_BUCKET_KEY,
    )
    pyramid_ev = _safe_float(pyramid.get("source_quality_adjusted_ev_pct"), None)
    avg_ev = _safe_float(avg_down.get("source_quality_adjusted_ev_pct"), None)

    pyramid_ready = (
        str(pyramid.get("scale_in_ev_coverage_state") or "") == "v2_ready"
        and pyramid.get("runtime_authority_ready") is True
    )
    avg_down_ready = (
        str(avg_down.get("scale_in_ev_coverage_state") or "") == "v2_ready"
        and avg_down.get("runtime_authority_ready") is True
    )
    if not pyramid_ready and not avg_down_ready:
        return _scale_candidate_legacy_blocked(
            target_date=target_date,
            ev_label_version=ev_label_version,
            pyramid=pyramid,
            avg_down=avg_down,
            discovery=discovery,
            discovery_live_by_family=discovery_live_by_family,
            discovery_available=discovery_available,
        )

    pyramid_state, pyramid_roll = (
        _state_for_bucket(
            pyramid,
            history,
            section="scale_in_bucket_attribution",
            bucket_type=SCALE_IN_PYRAMID_BUCKET_TYPE,
            bucket_key=SCALE_IN_PYRAMID_BUCKET_KEY,
            positive_edge=bool(pyramid_ev is not None and pyramid_ev > 0),
        )
        if pyramid_ready
        else (
            "blocked_source_quality",
            {
                "scale_in_ev_coverage_state": pyramid.get("scale_in_ev_coverage_state")
                or "missing"
            },
        )
    )
    avg_state, avg_roll = (
        _state_for_bucket(
            avg_down,
            history,
            section="scale_in_bucket_attribution",
            bucket_type=SCALE_IN_AVG_DOWN_BUCKET_TYPE,
            bucket_key=SCALE_IN_AVG_DOWN_BUCKET_KEY,
            positive_edge=bool(avg_ev is not None and avg_ev > 0),
        )
        if avg_down_ready
        else (
            "blocked_source_quality",
            {
                "scale_in_ev_coverage_state": avg_down.get("scale_in_ev_coverage_state")
                or "missing"
            },
        )
    )
    pyramid_discovery_ready = _discovery_scale_bucket_ready(
        discovery,
        bucket_type=SCALE_IN_PYRAMID_BUCKET_TYPE,
        bucket_key=SCALE_IN_PYRAMID_BUCKET_KEY,
    )
    avg_down_discovery_ready = _discovery_scale_bucket_ready(
        discovery,
        bucket_type=SCALE_IN_AVG_DOWN_BUCKET_TYPE,
        bucket_key=SCALE_IN_AVG_DOWN_BUCKET_KEY,
    )
    if pyramid_state == "live_auto_apply_ready" and not pyramid_discovery_ready:
        pyramid_state = "runtime_blocked_contract_gap"
        pyramid_roll = {
            **pyramid_roll,
            "lifecycle_bucket_discovery_gate": "blocked_exact_bucket_missing",
        }
    if avg_state == "live_auto_apply_ready" and not avg_down_discovery_ready:
        avg_state = "runtime_blocked_contract_gap"
        avg_roll = {
            **avg_roll,
            "lifecycle_bucket_discovery_gate": "blocked_exact_bucket_missing",
        }
    ready = (
        pyramid_state == "live_auto_apply_ready" or avg_state == "live_auto_apply_ready"
    )
    blocked_conflict = (
        pyramid_state == "blocked_rolling_conflict"
        or avg_state == "blocked_rolling_conflict"
    )
    blocked_source = (
        pyramid_state == "blocked_source_quality"
        and avg_state == "blocked_source_quality"
    )
    blocked_discovery = (
        pyramid_state == "runtime_blocked_contract_gap"
        or avg_state == "runtime_blocked_contract_gap"
    )
    if ready:
        state = "live_auto_apply_ready"
    elif blocked_discovery:
        state = "runtime_blocked_contract_gap"
        pyramid_roll = {**pyramid_roll, "lifecycle_bucket_discovery_gate": "blocked"}
        avg_roll = {**avg_roll, "lifecycle_bucket_discovery_gate": "blocked"}
        pyramid_roll["lifecycle_bucket_discovery_available"] = bool(discovery_available)
        avg_roll["lifecycle_bucket_discovery_available"] = bool(discovery_available)
    elif blocked_conflict:
        state = "blocked_rolling_conflict"
    elif blocked_source:
        state = "blocked_source_quality"
    else:
        state = "bootstrap_pending"
    discovery_meta = _discovery_candidate_meta(
        family=SCALE_IN_BRIDGE_FAMILY,
        discovery=discovery,
        discovery_live_by_family=discovery_live_by_family,
    )

    target_env_keys: list[str] = []
    recommended_values: dict[str, Any] = {
        "effective_qty_cap": 1,
        "threshold_version": f"{SCALE_IN_BRIDGE_FAMILY}:{target_date}",
        "calibration_state": f"runtime_apply_bridge:{state}",
        "ev_label_version": ev_label_version,
    }
    current_values: dict[str, Any] = {
        "effective_qty_cap": 1,
        "scalping_enable_pyramid": True,
        "reversal_add_min_ai_score": 60,
        "reversal_add_min_buy_pressure": 55.0,
        "reversal_add_min_tick_accel": 0.95,
    }
    if pyramid_state == "live_auto_apply_ready":
        if pyramid_ev is not None and pyramid_ev > 0:
            target_env_keys.append("SCALPING_ENABLE_PYRAMID")
            recommended_values["scalping_enable_pyramid"] = True
            recommended_values["pyramid_direction"] = "maintain_or_relax_positive_ev"
        else:
            target_env_keys.append("SCALPING_ENABLE_PYRAMID")
            recommended_values["scalping_enable_pyramid"] = False
            recommended_values["pyramid_direction"] = "tighten_or_disable_negative_ev"
    if avg_state == "live_auto_apply_ready":
        target_env_keys.extend(
            [
                "REVERSAL_ADD_MIN_AI_SCORE",
                "REVERSAL_ADD_MIN_BUY_PRESSURE",
                "REVERSAL_ADD_MIN_TICK_ACCEL",
            ]
        )
        if avg_ev is not None and avg_ev > 0:
            recommended_values.update(
                {
                    "reversal_add_min_ai_score": 55,
                    "reversal_add_min_buy_pressure": 50.0,
                    "reversal_add_min_tick_accel": 0.85,
                    "avg_down_direction": "limited_recovery_positive_ev",
                }
            )
        else:
            recommended_values.update(
                {
                    "reversal_add_min_ai_score": 65,
                    "reversal_add_min_buy_pressure": 60.0,
                    "reversal_add_min_tick_accel": 1.05,
                    "avg_down_direction": "tighten_or_exclude_negative_ev",
                }
            )

    source_buckets = []
    if pyramid:
        pyramid_role = (
            "pyramid_maintain_or_relax_positive_incremental_ev"
            if (pyramid_ev is not None and pyramid_ev > 0)
            else "pyramid_tighten_or_disable_negative_incremental_ev"
        )
        source_buckets.append(_scale_source(pyramid, role=pyramid_role))
    if avg_down:
        avg_down_role = (
            "avg_down_limited_recovery_positive_incremental_ev"
            if (avg_ev is not None and avg_ev > 0)
            else "avg_down_tighten_or_exclude_negative_incremental_ev"
        )
        source_buckets.append(_scale_source(avg_down, role=avg_down_role))
    positive_refs = []
    for item in payload.get("scale_in_bucket_attribution", {}).get("buckets", []):
        if not isinstance(item, dict):
            continue
        if str(item.get("recommended_route") or "") == "candidate_recovery_or_relax":
            positive_refs.append(_scale_source(item, role="observe_only_reference"))

    return {
        "candidate_id": f"{SCALE_IN_BRIDGE_FAMILY}:{target_date}",
        "family": SCALE_IN_BRIDGE_FAMILY,
        "stage": "scale_in",
        "priority": 39,
        "bridge_candidate_state": state,
        "approval_required": False,
        "human_approval_required": False,
        "live_auto_apply": state == "live_auto_apply_ready",
        "allowed_runtime_apply": state == "live_auto_apply_ready",
        "runtime_effect": False,
        "runtime_effect_after_approval": "bounded_scale_in_policy_tighten_live_auto",
        "target_env_keys": list(dict.fromkeys(target_env_keys)),
        "recommended_values": recommended_values,
        "current_values": current_values,
        "source_bucket_keys": [
            str(item.get("bucket_key") or "") for item in source_buckets
        ],
        "source_buckets": source_buckets,
        "observe_only_reference_buckets": positive_refs[:5],
        "rolling_confirmation": {
            "pyramid": pyramid_roll,
            "avg_down": avg_roll,
            "pyramid_state": pyramid_state,
            "avg_down_state": avg_state,
        },
        **discovery_meta,
        "primary_decision_metric": "incremental_notional_ev_pct",
        "decision_authority": "lifecycle_bucket_discovery_live_auto_apply",
        "forbidden_uses": [
            "scale_in_safety_guard_bypass",
            "intraday_threshold_mutation",
            "provider_route_change",
            "bot_restart_trigger",
        ],
    }
