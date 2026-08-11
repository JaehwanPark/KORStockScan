"""Bounded next-PREOPEN policy contract for lower-price two-leg profiles."""

from __future__ import annotations

import hashlib
import json
import math
import os
import tempfile
from datetime import date, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from src.trading.low_price_two_leg.profiles import PROFILES
from src.utils.constants import DATA_DIR

KST = ZoneInfo("Asia/Seoul")
CANDIDATE_SCHEMA = "low_price_two_leg_policy_candidate_v1"
APPLIED_SCHEMA = "low_price_two_leg_policy_applied_v1"
CANDIDATE_DIR = DATA_DIR / "threshold_cycle" / "low_price_two_leg" / "candidates"
APPLIED_DIR = DATA_DIR / "threshold_cycle" / "low_price_two_leg" / "applied"
MAX_CANDIDATE_AGE_DAYS = 7
CLEAN_BASELINE_DATE = "2026-06-05"


def _baseline_policy(profile_id: str) -> dict[str, Any]:
    policy = PROFILES[profile_id].policy
    return {
        "rolling_high_drawdown_pct": policy.rolling_high_drawdown_pct,
        "rolling_low_proximity_pct": policy.rolling_low_proximity_pct,
        "lookback_bars": policy.lookback_bars,
        "entry_valid_completed_bars": policy.entry_valid_completed_bars,
        "quantity": policy.quantity,
        "target_ticks": policy.target_ticks,
    }


BASELINE_POLICIES = {
    profile_id: _baseline_policy(profile_id) for profile_id in PROFILES
}


def _canonical_hash(payload: Any) -> str:
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def policy_hash(policies: dict[str, Any]) -> str:
    return _canonical_hash(policies)


def _finite_number(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def policy_mutations_between(
    before: dict[str, dict[str, Any]], after: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    mutations: list[dict[str, Any]] = []
    for profile_id, baseline in BASELINE_POLICIES.items():
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


def validate_profile_policy(profile_id: str, policy: Any) -> tuple[bool, str]:
    if profile_id not in BASELINE_POLICIES or not isinstance(policy, dict):
        return False, "profile_or_policy_invalid"
    baseline = BASELINE_POLICIES[profile_id]
    if set(policy) != set(baseline):
        return False, "policy_key_contract_mismatch"
    for key in (
        "lookback_bars",
        "entry_valid_completed_bars",
        "quantity",
        "target_ticks",
    ):
        if policy.get(key) != baseline[key]:
            return False, f"immutable_{key}_mismatch"
    drawdown = _finite_number(policy.get("rolling_high_drawdown_pct"))
    near_low = _finite_number(policy.get("rolling_low_proximity_pct"))
    if drawdown is None or not 1.25 <= drawdown <= 1.50:
        return False, "drawdown_outside_bounded_tightening"
    if near_low is None or not 0.10 <= near_low <= 0.20:
        return False, "near_low_outside_bounded_tightening"
    return True, "valid"


def validate_candidate(payload: Any) -> tuple[bool, str]:
    if not isinstance(payload, dict) or payload.get("schema") != CANDIDATE_SCHEMA:
        return False, "candidate_schema_invalid"
    try:
        source_date = date.fromisoformat(str(payload.get("source_date") or ""))
    except ValueError:
        return False, "candidate_source_date_invalid"
    if source_date < date.fromisoformat(CLEAN_BASELINE_DATE):
        return False, "candidate_source_date_precedes_clean_baseline"
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
        or payload.get("source_report_schema") != "low_price_two_leg_tuning_report_v1"
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
    if not isinstance(profiles, dict) or set(profiles) != set(BASELINE_POLICIES):
        return False, "candidate_profile_set_invalid"
    policies: dict[str, Any] = {}
    for profile_id, item in profiles.items():
        if not isinstance(item, dict):
            return False, f"candidate_{profile_id}_invalid"
        valid, reason = validate_profile_policy(profile_id, item.get("policy"))
        if not valid:
            return False, f"candidate_{profile_id}_{reason}"
        if item.get("allowed_runtime_apply") is not True:
            return False, f"candidate_{profile_id}_apply_authority_missing"
        policies[profile_id] = item["policy"]
    if payload.get("policy_hash") != policy_hash(policies):
        return False, "candidate_policy_hash_mismatch"
    return True, "valid"


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
    profiles = payload.get("profiles")
    if not isinstance(profiles, dict) or set(profiles) != set(BASELINE_POLICIES):
        return False, "applied_profile_set_invalid"
    policies: dict[str, Any] = {}
    for profile_id, item in profiles.items():
        if not isinstance(item, dict):
            return False, f"applied_{profile_id}_invalid"
        valid, reason = validate_profile_policy(profile_id, item.get("policy"))
        if not valid:
            return False, f"applied_{profile_id}_{reason}"
        policies[profile_id] = item["policy"]
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
    policies = {
        profile_id: dict(policy) for profile_id, policy in BASELINE_POLICIES.items()
    }
    return {
        "schema": APPLIED_SCHEMA,
        "target_date": target_date.isoformat(),
        "applied_at_kst": datetime.now(tz=KST).isoformat(timespec="seconds"),
        "source_date": None,
        "source_candidate": None,
        "selection_status": reason,
        "policy_hash": policy_hash(policies),
        "policy_mutations": [],
        "profiles": {
            profile_id: {"selection_status": reason, "policy": policy}
            for profile_id, policy in policies.items()
        },
        "decision_authority": "preopen_safe_baseline_fallback",
        "runtime_effect": True,
        "allowed_runtime_apply": True,
        "actual_order_submitted": False,
        "forbidden_uses": [
            "quantity_target_or_entry_validity_change",
            "stop_loss_or_forced_exit_creation",
            "provider_bot_cap_or_broker_guard_change",
        ],
    }
