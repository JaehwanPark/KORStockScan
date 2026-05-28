"""Runtime policy guard for promoted lifecycle buckets.

The guard is deliberately inert unless the PREOPEN runtime env enables it and
points to a readable policy file. This keeps code deploys separate from
intraday runtime mutation while allowing the next bot start to enforce the
greenfield real-environment contract.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ENABLED_ENV = "KORSTOCKSCAN_GREENFIELD_REAL_ENV_AUTHORITY_ENABLED"
SCOPE_ENV = "KORSTOCKSCAN_GREENFIELD_REAL_ENV_AUTHORITY_SCOPE"
POLICY_FILE_ENV = "KORSTOCKSCAN_GREENFIELD_REAL_ENV_AUTHORITY_POLICY_FILE"
POLICY_VERSION_ENV = "KORSTOCKSCAN_GREENFIELD_REAL_ENV_AUTHORITY_POLICY_VERSION"
TELEGRAM_ENV = "KORSTOCKSCAN_GREENFIELD_REAL_ENV_TELEGRAM_ENABLED"

FULL_LIFECYCLE_SCOPE = "full_lifecycle"
STAGES = ("entry", "submit", "holding", "scale_in", "exit")
REQUIRED_FULL_LIFECYCLE_STAGES = ("entry", "submit", "holding", "exit")
WILDCARD_ACTIONS = {"*", "ANY", "NO_CHANGE"}


@dataclass(frozen=True)
class GreenfieldDecision:
    active: bool
    allowed: bool
    stage: str
    action: str
    reason: str
    policy_version: str = "-"
    policy_file: str = "-"
    matched_bucket_id: str = "-"
    matched_family: str = "-"
    observed_bucket_id: str = "-"
    hard_safety_override: bool = False

    def as_fields(self) -> dict[str, Any]:
        return {
            "greenfield_real_env_authority_enabled": self.active,
            "greenfield_stage": self.stage,
            "greenfield_action": self.action,
            "greenfield_allowed": self.allowed,
            "greenfield_reason": self.reason,
            "greenfield_policy_version": self.policy_version,
            "greenfield_policy_file": self.policy_file,
            "greenfield_policy_bucket_id": self.matched_bucket_id,
            "greenfield_observed_bucket_id": self.observed_bucket_id,
            "greenfield_bucket_id": self.matched_bucket_id,
            "greenfield_family": self.matched_family,
            "greenfield_hard_safety_override": self.hard_safety_override,
            "decision_authority": "greenfield_real_environment_authority",
        }


def _bool_env(name: str, default: bool = False) -> bool:
    raw = str(os.getenv(name, "") or "").strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on", "y"}


def _read_policy(path: str) -> dict[str, Any]:
    if not path:
        return {}
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def greenfield_authority_active() -> bool:
    if not _bool_env(ENABLED_ENV, False):
        return False
    return str(os.getenv(SCOPE_ENV, FULL_LIFECYCLE_SCOPE) or "").strip() == FULL_LIFECYCLE_SCOPE


def greenfield_stage_telegram_enabled() -> bool:
    policy = _read_policy(os.getenv(POLICY_FILE_ENV, ""))
    return (
        greenfield_authority_active()
        and bool(policy)
        and not validate_greenfield_policy_contract(policy)
        and _bool_env(TELEGRAM_ENV, False)
    )


def _normalize_stage(stage: Any) -> str:
    value = str(stage or "").strip().lower()
    return value if value in STAGES else "unknown"


def _normalize_action(action: Any) -> str:
    return str(action or "NO_CHANGE").strip().upper() or "NO_CHANGE"


def _strategy_matches(row_scope: Any, strategy: Any) -> bool:
    scope = str(row_scope or "all").strip().lower()
    current = str(strategy or "").strip().lower()
    if scope in {"", "all", "full_lifecycle", "*"}:
        return True
    if scope in {current, current.replace("_", "-")}:
        return True
    if scope == "scalping" and current in {"scalp", "scalping"}:
        return True
    if scope == "swing" and current in {"kospi_ml", "kosdaq_ml", "swing"}:
        return True
    return False


def _action_matches(row_action: Any, action: str) -> bool:
    current = _normalize_action(row_action)
    return current in WILDCARD_ACTIONS or current == action


def _stage_rows(policy: dict[str, Any], stage: str) -> list[dict[str, Any]]:
    stages = policy.get("stages") if isinstance(policy.get("stages"), dict) else {}
    rows = stages.get(stage)
    if isinstance(rows, list):
        return [row for row in rows if isinstance(row, dict)]
    allowlist = policy.get("allowlist") if isinstance(policy.get("allowlist"), list) else []
    return [
        row
        for row in allowlist
        if isinstance(row, dict) and _normalize_stage(row.get("stage")) == stage
    ]


def _stage_has_baseline_passthrough(policy: dict[str, Any], stage: str) -> bool:
    stage_contract = policy.get("stage_contract") if isinstance(policy.get("stage_contract"), dict) else {}
    contract = stage_contract.get(stage) if isinstance(stage_contract.get(stage), dict) else {}
    if bool(contract.get("baseline_passthrough") or contract.get("baseline_passthrough_allowed")):
        return True
    return any(
        bool(row.get("baseline_passthrough"))
        or str(row.get("authority_mode") or "").strip().lower() == "baseline_passthrough"
        for row in _stage_rows(policy, stage)
    )


def validate_greenfield_policy_contract(policy: dict[str, Any], *, expected_version: str | None = None) -> str:
    if not policy:
        return "greenfield_policy_file_invalid"
    if str(policy.get("scope") or "") != FULL_LIFECYCLE_SCOPE:
        return "greenfield_policy_scope_invalid"
    policy_version = str(policy.get("policy_version") or policy.get("version") or "")
    if expected_version and policy_version and expected_version != policy_version:
        return "greenfield_policy_version_mismatch"
    allowlist = policy.get("allowlist") if isinstance(policy.get("allowlist"), list) else []
    if not allowlist:
        return "greenfield_policy_allowlist_empty"
    for row in allowlist:
        if not isinstance(row, dict):
            return "greenfield_policy_allowlist_invalid"
        stage = _normalize_stage(row.get("stage"))
        if stage == "unknown":
            return "greenfield_policy_allowlist_invalid_stage"
        if not str(row.get("action") or "").strip():
            return "greenfield_policy_allowlist_missing_action"
        if str(row.get("source_quality_gate") or "pass") != "pass":
            return "greenfield_policy_source_quality_not_pass"
        if str(row.get("ai_tier2_status") or "parsed") != "parsed":
            return "greenfield_policy_ai_tier2_not_parsed"
    for stage in REQUIRED_FULL_LIFECYCLE_STAGES:
        if _stage_rows(policy, stage) or _stage_has_baseline_passthrough(policy, stage):
            continue
        return "incomplete_lifecycle_bundle"
    return ""


def evaluate_greenfield_authority(
    *,
    stage: str,
    action: str,
    strategy: str | None = None,
    hard_safety: bool = False,
    observed_bucket_id: str | None = None,
) -> GreenfieldDecision:
    stage_name = _normalize_stage(stage)
    action_name = _normalize_action(action)
    policy_file = str(os.getenv(POLICY_FILE_ENV, "") or "")
    policy_version = str(os.getenv(POLICY_VERSION_ENV, "") or "")
    if not _bool_env(ENABLED_ENV, False):
        return GreenfieldDecision(False, True, stage_name, action_name, "greenfield_inactive")
    if str(os.getenv(SCOPE_ENV, FULL_LIFECYCLE_SCOPE) or "").strip() != FULL_LIFECYCLE_SCOPE:
        return GreenfieldDecision(False, True, stage_name, action_name, "greenfield_scope_not_full_lifecycle")
    if hard_safety:
        return GreenfieldDecision(
            True,
            True,
            stage_name,
            action_name,
            "hard_safety_passthrough",
            policy_version or "-",
            policy_file or "-",
            hard_safety_override=True,
        )
    policy = _read_policy(policy_file)
    if not policy:
        return GreenfieldDecision(
            True,
            False,
            stage_name,
            action_name,
            "greenfield_policy_missing_or_invalid",
            policy_version or "-",
            policy_file or "-",
        )
    policy_version = policy_version or str(policy.get("policy_version") or policy.get("version") or "-")
    contract_issue = validate_greenfield_policy_contract(
        policy,
        expected_version=policy_version if policy_version != "-" else None,
    )
    if contract_issue:
        return GreenfieldDecision(
            True,
            False,
            stage_name,
            action_name,
            contract_issue,
            policy_version,
            policy_file,
            observed_bucket_id=str(observed_bucket_id or "-"),
        )
    eligible_rows: list[dict[str, Any]] = []
    for row in _stage_rows(policy, stage_name):
        if not _strategy_matches(row.get("strategy_scope"), strategy):
            continue
        if not _action_matches(row.get("action"), action_name):
            continue
        if str(row.get("source_quality_gate") or "pass") != "pass":
            continue
        if str(row.get("ai_tier2_status") or "parsed") != "parsed":
            continue
        eligible_rows.append(row)
    observed = str(observed_bucket_id or "").strip()
    if observed:
        for row in eligible_rows:
            if str(row.get("bucket_id") or "-") != observed:
                continue
            return GreenfieldDecision(
                True,
                True,
                stage_name,
                action_name,
                "promoted_bucket_allowed",
                policy_version,
                policy_file,
                str(row.get("bucket_id") or "-"),
                str(row.get("family") or "-"),
                observed_bucket_id=observed,
            )
        if eligible_rows:
            row = eligible_rows[0]
            return GreenfieldDecision(
                True,
                False,
                stage_name,
                action_name,
                "observed_bucket_policy_mismatch",
                policy_version,
                policy_file,
                str(row.get("bucket_id") or "-"),
                str(row.get("family") or "-"),
                observed_bucket_id=observed,
            )
    elif stage_name == "entry" and eligible_rows:
        row = eligible_rows[0]
        return GreenfieldDecision(
            True,
            False,
            stage_name,
            action_name,
            "observed_bucket_missing",
            policy_version,
            policy_file,
            str(row.get("bucket_id") or "-"),
            str(row.get("family") or "-"),
            observed_bucket_id="-",
        )
    for row in eligible_rows:
        return GreenfieldDecision(
            True,
            True,
            stage_name,
            action_name,
            "promoted_bucket_allowed",
            policy_version,
            policy_file,
            str(row.get("bucket_id") or "-"),
            str(row.get("family") or "-"),
            observed_bucket_id=str(observed_bucket_id or "-"),
        )
    return GreenfieldDecision(
        True,
        False,
        stage_name,
        action_name,
        "unpromoted_bucket_blocked",
        policy_version,
        policy_file,
        observed_bucket_id=str(observed_bucket_id or "-"),
    )
