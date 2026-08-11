"""Bounded PREOPEN policy contract for the independent Samsung machines."""

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

from src.utils.constants import DATA_DIR

KST = ZoneInfo("Asia/Seoul")
CANDIDATE_SCHEMA = "samsung_machine_entry_policy_candidate_v1"
SUPPORTED_SOURCE_REPORT_SCHEMAS = frozenset(
    {
        "samsung_machine_entry_tuning_report_v2",
        "samsung_machine_entry_tuning_report_v3",
    }
)
APPLIED_SCHEMA = "samsung_machine_entry_policy_applied_v1"
CANDIDATE_DIR = (
    DATA_DIR / "threshold_cycle" / "samsung_machine_entry_policy" / "candidates"
)
APPLIED_DIR = DATA_DIR / "threshold_cycle" / "samsung_machine_entry_policy" / "applied"
MAX_CANDIDATE_AGE_DAYS = 7
CLEAN_BASELINE_DATE = "2026-06-05"

BASELINE_POLICIES: dict[str, dict[str, Any]] = {
    "morning": {
        "nxt_drawdown_pct": 3.0,
        "sor_drawdown_pct": 0.75,
        "quantity": 2,
        "target_ticks": 2,
    },
    "midday": {
        "rolling_high_drawdown_pct": 1.25,
        "rolling_low_proximity_pct": 0.20,
        "lookback_bars": 30,
        "entry_valid_completed_bars": 5,
        "quantity": 2,
        "target_ticks": 2,
    },
    "afternoon": {
        "rolling_high_drawdown_pct": 1.25,
        "rolling_low_proximity_pct": 0.20,
        "lookback_bars": 30,
        "entry_valid_completed_bars": 5,
        "quantity": 2,
        "target_ticks": 2,
    },
}


def _canonical_hash(payload: Any) -> str:
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def policy_hash(policies: dict[str, Any]) -> str:
    return _canonical_hash(policies)


def policy_mutations_between(
    before: dict[str, dict[str, Any]], after: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    mutations: list[dict[str, Any]] = []
    for machine in BASELINE_POLICIES:
        for axis in BASELINE_POLICIES[machine]:
            if before[machine][axis] != after[machine][axis]:
                mutations.append(
                    {
                        "machine": machine,
                        "axis": axis,
                        "before": before[machine][axis],
                        "after": after[machine][axis],
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
        "machine",
        "axis",
        "before",
        "after",
    }:
        return False, "policy_mutation_shape_invalid"
    machine = item["machine"]
    axis = item["axis"]
    before = _finite_number(item["before"])
    after = _finite_number(item["after"])
    if machine not in {"midday", "afternoon"} or axis not in {
        "rolling_high_drawdown_pct",
        "rolling_low_proximity_pct",
    }:
        return False, "policy_mutation_axis_invalid"
    if before is None or after is None or before == after:
        return False, "policy_mutation_values_invalid"
    if axis == "rolling_high_drawdown_pct" and after <= before:
        return False, "policy_mutation_is_not_tightening"
    if axis == "rolling_low_proximity_pct" and after >= before:
        return False, "policy_mutation_is_not_tightening"
    return True, "valid"


def _finite_number(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def validate_machine_policy(machine: str, policy: Any) -> tuple[bool, str]:
    if machine not in BASELINE_POLICIES or not isinstance(policy, dict):
        return False, "machine_or_policy_invalid"
    baseline = BASELINE_POLICIES[machine]
    if set(policy) != set(baseline):
        return False, "policy_key_contract_mismatch"
    for key in ("quantity", "target_ticks"):
        if policy.get(key) != baseline[key]:
            return False, f"immutable_{key}_mismatch"
    if machine == "morning":
        if policy != baseline:
            return False, "morning_policy_is_baseline_only"
        return True, "valid"
    for key in ("lookback_bars", "entry_valid_completed_bars"):
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
    if payload.get("runtime_effect") is not False:
        return False, "candidate_runtime_effect_invalid"
    if payload.get("allowed_runtime_apply") is not False:
        return False, "candidate_direct_apply_authority_invalid"
    if payload.get("actual_order_submitted") is not False:
        return False, "candidate_order_authority_invalid"
    if payload.get("clean_tuning_baseline_date") != CLEAN_BASELINE_DATE:
        return False, "candidate_clean_baseline_invalid"
    if (
        payload.get("source_report") != "samsung_machine_entry_tuning"
        or payload.get("source_report_schema") not in SUPPORTED_SOURCE_REPORT_SCHEMAS
    ):
        return False, "candidate_source_report_contract_invalid"
    if payload.get("decision_authority") != "postclose_bounded_candidate_only":
        return False, "candidate_decision_authority_invalid"
    valid, reason = _validate_policy_mutations(payload.get("policy_mutations"))
    if not valid:
        return False, reason
    machines = payload.get("machines")
    if not isinstance(machines, dict) or set(machines) != set(BASELINE_POLICIES):
        return False, "candidate_machine_set_invalid"
    policies: dict[str, Any] = {}
    for machine, item in machines.items():
        if not isinstance(item, dict):
            return False, f"candidate_{machine}_invalid"
        policy = item.get("policy")
        valid, reason = validate_machine_policy(machine, policy)
        if not valid:
            return False, f"candidate_{machine}_{reason}"
        if item.get("allowed_runtime_apply") is not True:
            return False, f"candidate_{machine}_apply_authority_missing"
        policies[machine] = policy
    if payload.get("policy_hash") != policy_hash(policies):
        return False, "candidate_policy_hash_mismatch"
    return True, "valid"


def validate_applied(payload: Any, *, target_date: date) -> tuple[bool, str]:
    if not isinstance(payload, dict) or payload.get("schema") != APPLIED_SCHEMA:
        return False, "applied_schema_invalid"
    if payload.get("target_date") != target_date.isoformat():
        return False, "applied_target_date_mismatch"
    if payload.get("runtime_effect") is not True:
        return False, "applied_runtime_effect_missing"
    if payload.get("allowed_runtime_apply") is not True:
        return False, "applied_runtime_authority_missing"
    if payload.get("actual_order_submitted") is not False:
        return False, "applied_order_authority_invalid"
    if payload.get("decision_authority") not in {
        "auto_bounded_live_samsung_entry_policy",
        "preopen_safe_baseline_fallback",
    }:
        return False, "applied_decision_authority_invalid"
    valid, reason = _validate_policy_mutations(payload.get("policy_mutations"))
    if not valid:
        return False, reason
    machines = payload.get("machines")
    if not isinstance(machines, dict) or set(machines) != set(BASELINE_POLICIES):
        return False, "applied_machine_set_invalid"
    policies: dict[str, Any] = {}
    for machine, item in machines.items():
        if not isinstance(item, dict):
            return False, f"applied_{machine}_invalid"
        policy = item.get("policy")
        valid, reason = validate_machine_policy(machine, policy)
        if not valid:
            return False, f"applied_{machine}_{reason}"
        policies[machine] = policy
    if payload.get("policy_hash") != policy_hash(policies):
        return False, "applied_policy_hash_mismatch"
    return True, "valid"


def applied_path(target_date: date, *, applied_dir: Path = APPLIED_DIR) -> Path:
    return applied_dir / f"samsung_machine_entry_policy_{target_date.isoformat()}.json"


def load_applied_machine_policy(
    machine: str,
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
    item = payload["machines"].get(machine)
    if not isinstance(item, dict):
        return None, "", "applied_machine_policy_missing"
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
    policies = {name: dict(policy) for name, policy in BASELINE_POLICIES.items()}
    return {
        "schema": APPLIED_SCHEMA,
        "target_date": target_date.isoformat(),
        "applied_at_kst": datetime.now(tz=KST).isoformat(timespec="seconds"),
        "source_date": None,
        "source_candidate": None,
        "selection_status": reason,
        "policy_hash": policy_hash(policies),
        "policy_mutations": [],
        "machines": {
            machine: {
                "selection_status": reason,
                "policy": policy,
            }
            for machine, policy in policies.items()
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
