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
    return (
        greenfield_authority_active()
        and bool(_read_policy(os.getenv(POLICY_FILE_ENV, "")))
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


def evaluate_greenfield_authority(
    *,
    stage: str,
    action: str,
    strategy: str | None = None,
    hard_safety: bool = False,
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
    for row in _stage_rows(policy, stage_name):
        if not _strategy_matches(row.get("strategy_scope"), strategy):
            continue
        if not _action_matches(row.get("action"), action_name):
            continue
        if str(row.get("source_quality_gate") or "pass") != "pass":
            continue
        if str(row.get("ai_tier2_status") or "parsed") != "parsed":
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
        )
    return GreenfieldDecision(
        True,
        False,
        stage_name,
        action_name,
        "unpromoted_bucket_blocked",
        policy_version,
        policy_file,
    )
