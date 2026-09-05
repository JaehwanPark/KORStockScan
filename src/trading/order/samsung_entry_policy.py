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

from src.trading.order.episode_quantity import EPISODE_TOTAL_QUANTITY
from src.utils.constants import DATA_DIR

KST = ZoneInfo("Asia/Seoul")
CANDIDATE_SCHEMA = "samsung_machine_entry_policy_candidate_v2"
LEGACY_CANDIDATE_SCHEMA = "samsung_machine_entry_policy_candidate_v1"
SUPPORTED_CANDIDATE_SCHEMAS = frozenset({LEGACY_CANDIDATE_SCHEMA, CANDIDATE_SCHEMA})
SUPPORTED_SOURCE_REPORT_SCHEMAS = frozenset(
    {
        "samsung_machine_entry_tuning_report_v2",
        "samsung_machine_entry_tuning_report_v3",
        "samsung_machine_entry_tuning_report_v4",
        "samsung_machine_entry_tuning_report_v5",
        "samsung_machine_entry_tuning_report_v6",
        "samsung_machine_entry_tuning_report_v7",
        "samsung_machine_entry_tuning_report_v8",
        "samsung_machine_entry_tuning_report_v9",
    }
)
APPLIED_SCHEMA = "samsung_machine_entry_policy_applied_v2"
LEGACY_APPLIED_SCHEMA = "samsung_machine_entry_policy_applied_v1"
SUPPORTED_APPLIED_SCHEMAS = frozenset({LEGACY_APPLIED_SCHEMA, APPLIED_SCHEMA})
CANDIDATE_DIR = (
    DATA_DIR / "threshold_cycle" / "samsung_machine_entry_policy" / "candidates"
)
APPLIED_DIR = DATA_DIR / "threshold_cycle" / "samsung_machine_entry_policy" / "applied"
MAX_CANDIDATE_AGE_DAYS = 7
CLEAN_BASELINE_DATE = "2026-06-05"
LEGACY_TWO_SHARE_CANDIDATE_LAST_SOURCE_DATE = date(2026, 8, 13)
LEGACY_TWO_SHARE_APPLIED_LAST_TARGET_DATE = date(2026, 8, 13)
LEGACY_MUTATING_CANDIDATE_LAST_SOURCE_DATE = date(2026, 8, 13)
SAMSUNG_TARGET_TICKS_OPERATOR_OVERRIDE = {
    "override_id": "samsung_episode_target_ticks_3_20260814",
    "machines": ["morning", "midday", "afternoon"],
    "runtime_scopes": ["morning", "morning_reentry", "midday", "afternoon"],
    "axis": "target_ticks",
    "before": 2,
    "after": 3,
    "approved_at_kst": "2026-08-14T09:21:07+09:00",
    "effective_at_kst": "2026-08-14T09:21:07+09:00",
    "decision_authority": "explicit_user_directed_intraday_operator_override",
    "reason": "operator_accepts_91p43pct_target_reach_for_more_cost_slippage_margin",
    "existing_order_effect": "none_do_not_cancel_or_replace_owned_target_orders",
    "rollback": {
        "trigger": "explicit_user_revert_after_broker_priced_postclose_review",
        "action": "restore_target_ticks_2_for_new_samsung_episode_targets",
        "existing_order_effect": "none_do_not_cancel_or_replace_owned_target_orders",
    },
}
OPERATOR_OVERRIDE_RUNTIME_SOURCE = (
    "exact_date_applied_policy_plus_samsung_target_ticks_3_operator_override"
)

BASELINE_POLICIES: dict[str, dict[str, Any]] = {
    "morning": {
        "nxt_drawdown_pct": 3.0,
        "sor_drawdown_pct": 0.75,
        "quantity": EPISODE_TOTAL_QUANTITY,
        "target_ticks": 2,
    },
    "midday": {
        "rolling_high_drawdown_pct": 1.25,
        "rolling_low_proximity_pct": 0.20,
        "lookback_bars": 30,
        "entry_valid_completed_bars": 5,
        "quantity": EPISODE_TOTAL_QUANTITY,
        "target_ticks": 2,
    },
    "afternoon": {
        "rolling_high_drawdown_pct": 1.25,
        "rolling_low_proximity_pct": 0.20,
        "lookback_bars": 30,
        "entry_valid_completed_bars": 5,
        "quantity": EPISODE_TOTAL_QUANTITY,
        "target_ticks": 2,
    },
}


def operator_target_override(
    *, target_date: date, as_of: datetime | None = None
) -> dict[str, Any] | None:
    """Return the explicit target override only after its effective instant."""

    effective_at = datetime.fromisoformat(
        str(SAMSUNG_TARGET_TICKS_OPERATOR_OVERRIDE["effective_at_kst"])
    ).astimezone(KST)
    if target_date < effective_at.date():
        return None
    if target_date == effective_at.date():
        observed_at = as_of or datetime.now(tz=KST)
        if observed_at.tzinfo is None:
            observed_at = observed_at.replace(tzinfo=KST)
        else:
            observed_at = observed_at.astimezone(KST)
        if observed_at < effective_at:
            return None
    return dict(SAMSUNG_TARGET_TICKS_OPERATOR_OVERRIDE)


def effective_target_ticks(
    machine: str, *, target_date: date, as_of: datetime | None = None
) -> int:
    if machine not in BASELINE_POLICIES:
        raise ValueError("unknown_samsung_machine")
    transition = operator_target_override(target_date=target_date, as_of=as_of)
    return int(
        transition["after"]
        if transition is not None
        else BASELINE_POLICIES[machine]["target_ticks"]
    )


def effective_runtime_policy_source(
    *, target_date: date, as_of: datetime | None = None
) -> str:
    return (
        OPERATOR_OVERRIDE_RUNTIME_SOURCE
        if operator_target_override(target_date=target_date, as_of=as_of) is not None
        else "preopen_applied_policy"
    )


def _effective_applied_policies(
    payload: dict[str, Any], *, target_date: date, as_of: datetime | None
) -> dict[str, dict[str, Any]]:
    policies = {
        machine: dict(payload["machines"][machine]["policy"])
        for machine in BASELINE_POLICIES
    }
    transition = operator_target_override(target_date=target_date, as_of=as_of)
    if transition is None:
        return policies
    for machine in transition["machines"]:
        if policies[machine].get(transition["axis"]) != transition["before"]:
            raise ValueError("operator_target_override_before_value_mismatch")
        policies[machine][transition["axis"]] = transition["after"]
    return policies


def canonical_hash(payload: Any) -> str:
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def report_artifact_hash(payload: dict[str, Any]) -> str:
    return canonical_hash(
        {key: value for key, value in payload.items() if key != "artifact_hash"}
    )


def candidate_artifact_hash(payload: dict[str, Any]) -> str:
    return canonical_hash(
        {key: value for key, value in payload.items() if key != "candidate_hash"}
    )


def _valid_sha256(value: Any) -> bool:
    text = str(value or "")
    return bool(
        len(text) == 64
        and text == text.lower()
        and all(char in "0123456789abcdef" for char in text)
    )


def policy_hash(policies: dict[str, Any]) -> str:
    return canonical_hash(policies)


def policy_mutations_between(
    before: dict[str, dict[str, Any]],
    after: dict[str, dict[str, Any]],
    *,
    include_kind: bool = False,
) -> list[dict[str, Any]]:
    mutations: list[dict[str, Any]] = []
    for machine in BASELINE_POLICIES:
        for axis in BASELINE_POLICIES[machine]:
            if before[machine][axis] != after[machine][axis]:
                mutation = {
                    "machine": machine,
                    "axis": axis,
                    "before": before[machine][axis],
                    "after": after[machine][axis],
                }
                if include_kind:
                    tightening = (
                        axis == "rolling_high_drawdown_pct"
                        and float(after[machine][axis]) > float(before[machine][axis])
                    ) or (
                        axis == "rolling_low_proximity_pct"
                        and float(after[machine][axis]) < float(before[machine][axis])
                    )
                    mutation["kind"] = (
                        "tightening" if tightening else "bounded_rollback"
                    )
                mutations.append(mutation)
    return mutations


def _validate_policy_mutations(
    value: Any, *, allow_bounded_rollback: bool = False, require_kind: bool = False
) -> tuple[bool, str]:
    if not isinstance(value, list) or len(value) > 1:
        return False, "same_stage_single_axis_contract_invalid"
    if not value:
        return True, "valid"
    item = value[0]
    expected_keys = {
        "machine",
        "axis",
        "before",
        "after",
    }
    if require_kind:
        expected_keys.add("kind")
    if not isinstance(item, dict) or set(item) != expected_keys:
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
    tightening = (axis == "rolling_high_drawdown_pct" and after > before) or (
        axis == "rolling_low_proximity_pct" and after < before
    )
    rollback = (axis == "rolling_high_drawdown_pct" and after < before) or (
        axis == "rolling_low_proximity_pct" and after > before
    )
    if require_kind and item.get("kind") not in {"tightening", "bounded_rollback"}:
        return False, "policy_mutation_kind_invalid"
    if tightening and (not require_kind or item.get("kind") == "tightening"):
        return True, "valid"
    if (
        rollback
        and allow_bounded_rollback
        and require_kind
        and item.get("kind") == "bounded_rollback"
    ):
        return True, "valid"
    if rollback:
        return False, "policy_mutation_rollback_not_allowed"
    if require_kind:
        return False, "policy_mutation_kind_direction_mismatch"
    return False, "policy_mutation_is_not_tightening"


def _finite_number(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def validate_machine_policy(
    machine: str,
    policy: Any,
    *,
    target_date: date | None = None,
    legacy_two_share_candidate: bool = False,
) -> tuple[bool, str]:
    if machine not in BASELINE_POLICIES or not isinstance(policy, dict):
        return False, "machine_or_policy_invalid"
    baseline = BASELINE_POLICIES[machine]
    if set(policy) != set(baseline):
        return False, "policy_key_contract_mismatch"
    legacy_quantity_allowed = bool(
        policy.get("quantity") == 2
        and (
            legacy_two_share_candidate
            or (
                target_date is not None
                and target_date <= LEGACY_TWO_SHARE_APPLIED_LAST_TARGET_DATE
            )
        )
    )
    for key in ("quantity", "target_ticks"):
        if key == "quantity" and legacy_quantity_allowed:
            continue
        if policy.get(key) != baseline[key]:
            return False, f"immutable_{key}_mismatch"
    if machine == "morning":
        if any(
            policy.get(key) != value
            for key, value in baseline.items()
            if key != "quantity"
        ):
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


def validate_candidate(
    payload: Any, *, source_report: dict[str, Any] | None = None
) -> tuple[bool, str]:
    if (
        not isinstance(payload, dict)
        or payload.get("schema") not in SUPPORTED_CANDIDATE_SCHEMAS
    ):
        return False, "candidate_schema_invalid"
    schema = str(payload["schema"])
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
    valid, reason = _validate_policy_mutations(
        payload.get("policy_mutations"),
        allow_bounded_rollback=schema == CANDIDATE_SCHEMA,
        require_kind=schema == CANDIDATE_SCHEMA,
    )
    if not valid:
        return False, reason
    if (
        schema == LEGACY_CANDIDATE_SCHEMA
        and source_date > LEGACY_MUTATING_CANDIDATE_LAST_SOURCE_DATE
        and payload.get("policy_mutations")
    ):
        return False, "legacy_mutating_candidate_no_longer_authoritative"
    if schema == CANDIDATE_SCHEMA:
        preflight = payload.get("source_quality_preflight")
        if not isinstance(preflight, dict):
            return False, "candidate_source_quality_preflight_missing"
        source_quality_allowed = bool(
            preflight.get("tuning_input_allowed") is True
            and preflight.get("status") == "pass"
            and preflight.get("audit_status") in {"pass", "warning"}
        )
        source_quality_blocked = bool(
            preflight.get("tuning_input_allowed") is False
            and preflight.get("status") == "blocked"
        )
        if not source_quality_allowed and not source_quality_blocked:
            return False, "candidate_source_quality_preflight_invalid"
        if payload.get("policy_mutations") and not source_quality_allowed:
            return False, "candidate_source_quality_not_allowed_for_mutation"
        if not _valid_sha256(preflight.get("source_sha256")):
            return False, "candidate_source_quality_hash_invalid"
        report_binding = payload.get("source_report_binding")
        if not isinstance(report_binding, dict) or set(report_binding) != {
            "schema",
            "target_date",
            "sha256",
        }:
            return False, "candidate_source_report_binding_invalid"
        if (
            report_binding.get("schema") != payload.get("source_report_schema")
            or report_binding.get("target_date") != source_date.isoformat()
            or not _valid_sha256(report_binding.get("sha256"))
        ):
            return False, "candidate_source_report_binding_mismatch"
    machines = payload.get("machines")
    if not isinstance(machines, dict) or set(machines) != set(BASELINE_POLICIES):
        return False, "candidate_machine_set_invalid"
    policies: dict[str, Any] = {}
    for machine, item in machines.items():
        if not isinstance(item, dict):
            return False, f"candidate_{machine}_invalid"
        policy = item.get("policy")
        valid, reason = validate_machine_policy(
            machine,
            policy,
            legacy_two_share_candidate=(
                source_date <= LEGACY_TWO_SHARE_CANDIDATE_LAST_SOURCE_DATE
            ),
        )
        if not valid:
            return False, f"candidate_{machine}_{reason}"
        if item.get("allowed_runtime_apply") is not True:
            return False, f"candidate_{machine}_apply_authority_missing"
        if schema == CANDIDATE_SCHEMA:
            if not _valid_sha256(item.get("evidence_digest")):
                return False, f"candidate_{machine}_evidence_digest_invalid"
            if item.get("evidence_digest") != canonical_hash(item.get("evidence")):
                return False, f"candidate_{machine}_evidence_digest_mismatch"
        policies[machine] = policy
    if payload.get("policy_hash") != policy_hash(policies):
        return False, "candidate_policy_hash_mismatch"
    if payload.get("source_report_schema") == "samsung_machine_entry_tuning_report_v9":
        binding = payload.get("source_runtime_policy_binding")
        if (
            not isinstance(binding, dict)
            or binding.get("source_date") != source_date.isoformat()
        ):
            return False, "candidate_actual_runtime_binding_missing"
        if binding.get("status") not in {"ready", "missing_baseline_only", "invalid"}:
            return False, "candidate_actual_runtime_binding_invalid"
        starting = binding.get("policies")
        if not isinstance(starting, dict) or set(starting) != set(BASELINE_POLICIES):
            return False, "candidate_actual_runtime_machine_set_invalid"
        for machine, policy in starting.items():
            valid, reason = validate_machine_policy(machine, policy)
            if not valid:
                return False, f"candidate_actual_runtime_{reason}"
        mutations = payload.get("policy_mutations")
        if mutations != policy_mutations_between(starting, policies, include_kind=True):
            return False, "candidate_actual_runtime_mutation_mismatch"
        if any(item.get("kind") != "bounded_rollback" for item in mutations):
            return False, "candidate_subset_tightening_authority_retired"
        if mutations and binding.get("status") != "ready":
            return False, "candidate_mutation_without_actual_runtime_policy"
        if (
            source_report is not None
            and source_report.get("source_runtime_policy_binding") != binding
        ):
            return False, "candidate_actual_runtime_report_binding_mismatch"
    if schema == CANDIDATE_SCHEMA:
        if not _valid_sha256(payload.get("candidate_hash")):
            return False, "candidate_hash_invalid"
        if payload.get("candidate_hash") != candidate_artifact_hash(payload):
            return False, "candidate_hash_mismatch"
        if source_report is not None:
            if source_report.get("artifact_hash") != report_artifact_hash(
                source_report
            ):
                return False, "candidate_source_report_artifact_hash_invalid"
            if (
                source_report.get("schema") != payload.get("source_report_schema")
                or source_report.get("target_date") != source_date.isoformat()
                or source_report.get("artifact_hash")
                != payload["source_report_binding"]["sha256"]
            ):
                return False, "candidate_source_report_artifact_mismatch"
            if source_report.get("source_quality_preflight") != preflight:
                return False, "candidate_source_quality_report_mismatch"
    return True, "valid"


def candidate_policies_with_current_baselines(
    payload: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Validate candidate provenance, then migrate legacy quantity in memory."""

    valid, reason = validate_candidate(payload)
    if not valid:
        raise ValueError(reason)
    normalized: dict[str, dict[str, Any]] = {}
    for machine, baseline in BASELINE_POLICIES.items():
        policy = dict(payload["machines"][machine]["policy"])
        if policy.get("quantity") == 2:
            policy["quantity"] = baseline["quantity"]
        normalized[machine] = policy
    return normalized


def validate_applied(payload: Any, *, target_date: date) -> tuple[bool, str]:
    if (
        not isinstance(payload, dict)
        or payload.get("schema") not in SUPPORTED_APPLIED_SCHEMAS
    ):
        return False, "applied_schema_invalid"
    schema = str(payload["schema"])
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
    valid, reason = _validate_policy_mutations(
        payload.get("policy_mutations"),
        allow_bounded_rollback=schema == APPLIED_SCHEMA,
        require_kind=schema == APPLIED_SCHEMA,
    )
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
        valid, reason = validate_machine_policy(
            machine, policy, target_date=target_date
        )
        if not valid:
            return False, f"applied_{machine}_{reason}"
        policies[machine] = policy
    if payload.get("policy_hash") != policy_hash(policies):
        return False, "applied_policy_hash_mismatch"
    if schema == APPLIED_SCHEMA and payload.get("decision_authority") == (
        "auto_bounded_live_samsung_entry_policy"
    ):
        for key in (
            "source_candidate_hash",
            "source_report_hash",
            "source_quality_artifact_hash",
        ):
            if not _valid_sha256(payload.get(key)):
                return False, f"applied_{key}_invalid"
    return True, "valid"


def applied_path(target_date: date, *, applied_dir: Path = APPLIED_DIR) -> Path:
    return applied_dir / f"samsung_machine_entry_policy_{target_date.isoformat()}.json"


def load_applied_machine_policy(
    machine: str,
    *,
    target_date: date,
    applied_dir: Path = APPLIED_DIR,
    as_of: datetime | None = None,
) -> tuple[dict[str, Any] | None, str, str]:
    path = applied_path(target_date, applied_dir=applied_dir)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, "", f"applied_policy_unreadable:{type(exc).__name__}"
    valid, reason = validate_applied(payload, target_date=target_date)
    if not valid:
        return None, "", reason
    if machine not in BASELINE_POLICIES:
        return None, "", "applied_machine_policy_missing"
    try:
        policies = _effective_applied_policies(
            payload, target_date=target_date, as_of=as_of
        )
    except ValueError as exc:
        return None, "", str(exc)
    override = operator_target_override(target_date=target_date, as_of=as_of)
    return (
        policies[machine],
        policy_hash(policies),
        "ready_operator_override" if override is not None else "ready",
    )


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
