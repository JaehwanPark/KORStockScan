"""Exact-scope, next-PREOPEN authority for causal machine rebound entries.

Standing operator direction: 2026-09-06.  A report is never an apply receipt.
This family cannot change cancellation, sizing, targets, or broker guards.
"""

from __future__ import annotations

import hashlib
import json
import math
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from src.utils.constants import DATA_DIR
from src.utils.market_day import is_krx_trading_day

KST = ZoneInfo("Asia/Seoul")
SCHEMA = "machine_rebound_reentry_applied_v1"
AUTHORITY = "operator_20260906_bounded_rebound_auto_preopen"
REPLAY_VERSION = "machine_rebound_reentry_paired_v1"
DEFAULT_POLICY_DIR = DATA_DIR / "runtime" / "machine_rebound_reentry_policy"
SCOPE_FIELDS = (
    "owner",
    "scope_id",
    "symbol",
    "listing_market",
    "venue",
    "session",
    "entry_state",
)
MIN_DAYS = 5
MIN_PAIRS = 8
MIN_COVERAGE_PCT = 85.0
MIN_UPLIFT_PCT = 0.005
MAX_P10_DETERIORATION_PCT = 0.01
AUTO_ARM = "fresh_owner_rebound_during_weakness"
SOURCE_AUTHORITY = {
    "runtime_effect": False,
    "allowed_runtime_apply": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
    "decision_authority": "source_only_rebound_reentry_evaluation",
}


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def next_session(source: date) -> date:
    candidate = source + timedelta(days=1)
    while not is_krx_trading_day(candidate):
        candidate += timedelta(days=1)
    return candidate


def scope_identity(value: dict[str, Any]) -> dict[str, str]:
    return {key: str(value.get(key) or "") for key in SCOPE_FIELDS}


def policy_path(target: date, root: Path = DEFAULT_POLICY_DIR) -> Path:
    return root / f"machine_rebound_reentry_{target.isoformat()}.json"


def numeric(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (ValueError, TypeError):
        return None


def load_policy(
    *, now: datetime, scope: dict[str, Any], root: Path = DEFAULT_POLICY_DIR
) -> tuple[dict[str, Any] | None, str]:
    """Reject stale dates, modified evidence, unknown scope, and unreviewed arms."""
    try:
        if now.tzinfo is None:
            return None, "naive_runtime_time"
        target = now.astimezone(KST).date()
        payload = json.loads(policy_path(target, root).read_text())
        source = date.fromisoformat(payload["source_date"])
        applied_at = datetime.fromisoformat(payload["applied_at"])
        candidate = payload["candidate"]
        if not isinstance(candidate, dict) or not valid_candidate(candidate):
            return None, "candidate_floors_invalid"
        if (
            payload.get("schema") != SCHEMA
            or payload.get("authority") != AUTHORITY
            or payload.get("target_date") != target.isoformat()
            or source < date(2026, 6, 5)
            or next_session(source) != target
            or applied_at.tzinfo is None
            or applied_at.astimezone(KST).date() != target
            or applied_at.astimezone(KST).hour >= 8
            or applied_at > now
            or payload.get("policy_hash") != digest(candidate)
            or candidate.get("arm") != AUTO_ARM
            or candidate.get("replay_version") != REPLAY_VERSION
            or candidate.get("source_through_date") != source.isoformat()
            or scope_identity(candidate) != scope_identity(scope)
            or not all(scope_identity(scope).values())
            or payload.get("same_stage_clear") is not True
            or payload.get("runtime_effect") is not True
            or payload.get("allowed_runtime_apply") is not True
            or payload.get("actual_order_submitted") is not False
            or payload.get("broker_order_forbidden") is not False
            or payload.get(
                "cancel_quantity_target_exit_provider_broker_guards_unchanged"
            )
            is not True
        ):
            return None, "applied_contract_invalid"
        evidence_path = Path(payload["evidence_snapshot"])
        evidence = json.loads(evidence_path.read_text())
        if not isinstance(evidence, dict):
            return None, "evidence_contract_invalid"
        if digest(evidence) != payload["evidence_sha256"]:
            return None, "evidence_hash_mismatch"
        if evidence.get("selected_candidate") != candidate:
            return None, "candidate_evidence_mismatch"
        return payload, "applied_exact_scope"
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        return None, "policy_missing_or_invalid"


def valid_candidate(candidate: dict[str, Any]) -> bool:
    """Defense in depth: hashes alone never replace bounds validation."""
    try:
        scope = scope_identity(candidate)
        executable = candidate.get("executable_confirmation") or {}
        runtime_cost = numeric(executable.get("round_trip_cost_pct"))
        cost_hash = str(executable.get("cost_contract_sha256") or "")
        source_through = date.fromisoformat(str(candidate.get("source_through_date")))
        cost_trade_date = date.fromisoformat(str(executable.get("cost_trade_date")))
        if (
            candidate.get("status") != "candidate_ready"
            or candidate.get("blockers") != []
            or candidate.get("arm") != AUTO_ARM
            or candidate.get("replay_version") != REPLAY_VERSION
            or scope["owner"] != "episode"
            or scope["entry_state"] != "FLAT_NEW_ENTRY"
            or scope["listing_market"] not in {"KOSPI", "KOSDAQ"}
            or scope["venue"] not in {"SOR", "KRX", "NXT"}
            or not all(scope.values())
            or (numeric(candidate.get("unique_days")) or 0) < MIN_DAYS
            or (numeric(candidate.get("coverage_pct")) or 0) < MIN_COVERAGE_PCT
            or len(str(candidate.get("owner_contract_sha256") or "")) != 64
            or source_through < date(2026, 6, 5)
            or next_session(source_through) != cost_trade_date
            or executable.get("mode") != "fresh_rebound_checkpoint0"
            or runtime_cost is None
            or runtime_cost < 0
            or len(cost_hash) != 64
            or any(char not in "0123456789abcdef" for char in cost_hash)
        ):
            return False
        for name, stats in (
            ("cumulative", candidate.get("primary_ev") or {}),
            ("rolling5", (candidate.get("rolling") or {}).get("5") or {}),
            ("holdout", candidate.get("holdout") or {}),
        ):
            uplift = numeric(stats.get("source_quality_adjusted_ev_pct"))
            absolute = numeric(stats.get("candidate_ev_pct"))
            p10 = numeric(stats.get("p10_deterioration_pct"))
            if (
                uplift is None
                or (uplift < MIN_UPLIFT_PCT if name == "cumulative" else uplift <= 0)
                or absolute is None
                or absolute <= 0
                or p10 is None
                or p10 > MAX_P10_DETERIORATION_PCT
            ):
                return False
        return (
            numeric((candidate.get("primary_ev") or {}).get("pairs")) or 0
        ) >= MIN_PAIRS
    except (TypeError, ValueError, AttributeError):
        return False
