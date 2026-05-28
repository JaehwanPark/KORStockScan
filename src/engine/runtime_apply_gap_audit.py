"""Audit runtime uptake gaps across discovery, bridge, apply, and attribution."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from dataclasses import replace
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from src.engine.ai.postclose_review_config import PostcloseAIReviewConfig, resolve_postclose_ai_review_config
from src.engine.daily_threshold_cycle_report import REPORT_DIR as BASE_REPORT_DIR
from src.engine.daily_threshold_cycle_report import _extract_openai_response_text, _load_threshold_ai_openai_keys
from src.engine.runtime_apply_bridge import GREENFIELD_REAL_ENV_FAMILY, validate_greenfield_policy_file
from src.utils.constants import DATA_DIR

REPORT_SCHEMA_VERSION = 1
REPORT_DIR = DATA_DIR / "report" / "runtime_apply_gap_audit"
APPLY_PLAN_DIR = DATA_DIR / "threshold_cycle" / "apply_plans"
AI_REVIEW_SCHEMA_NAME = "runtime_apply_gap_ai_review_v1"
AI_REVIEWER_NAME = "runtime_apply_gap_ai_review"
AI_REVIEW_MODEL = "gpt-5.4"
MIN_AI_REVIEW_MODEL = "gpt-5.4"
AI_REVIEW_REASONING_EFFORT = "low"
AI_REVIEW_TIMEOUT_SEC = 180

FINAL_DISPOSITIONS = {
    "live_auto_apply_ready",
    "sim_auto_approved",
    "approval_required",
    "code_patch_required",
    "runtime_blocked_contract_gap",
    "source_quality_blocker",
    "safety_veto",
    "post_apply_attribution_pending",
    "source_only_keep_collecting",
    "source_only_explicit_exclusion",
}
FAILURE_STATES = {
    "pass",
    "fail",
    "retry_pending",
    "blocked_contract",
    "blocked_source_quality",
    "blocked_safety",
}
CORE_ARTIFACT_LABELS = (
    "lifecycle_bucket_discovery",
    "runtime_apply_bridge",
    "runtime_approval_summary",
    "code_improvement_workorder",
)


def runtime_apply_gap_audit_report_path(target_date: str) -> Path:
    return REPORT_DIR / f"runtime_apply_gap_audit_{target_date}.json"


def runtime_apply_gap_audit_markdown_path(target_date: str) -> Path:
    return REPORT_DIR / f"runtime_apply_gap_audit_{target_date}.md"


def _load_json(path: Path) -> dict[str, Any]:
    try:
        if not path.exists():
            return {}
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


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


def _text_hash(payload: Any) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _next_preopen_apply_path(target_date: str) -> Path:
    if APPLY_PLAN_DIR.exists():
        candidates: list[tuple[str, Path]] = []
        for path in APPLY_PLAN_DIR.glob("threshold_apply_*.json"):
            apply_date = path.stem.removeprefix("threshold_apply_")
            if apply_date > target_date:
                candidates.append((apply_date, path))
        if candidates:
            return sorted(candidates)[0][1]
    return APPLY_PLAN_DIR / f"threshold_apply_{_next_day(target_date)}.json"


def _artifact_path(label: str, target_date: str) -> Path:
    file_map = {
        "lifecycle_bucket_discovery": BASE_REPORT_DIR
        / "lifecycle_bucket_discovery"
        / f"lifecycle_bucket_discovery_{target_date}.json",
        "swing_lifecycle_bucket_discovery": BASE_REPORT_DIR
        / "swing_lifecycle_bucket_discovery"
        / f"swing_lifecycle_bucket_discovery_{target_date}.json",
        "runtime_apply_bridge": BASE_REPORT_DIR / "runtime_apply_bridge" / f"runtime_apply_bridge_{target_date}.json",
        "runtime_approval_summary": BASE_REPORT_DIR
        / "runtime_approval_summary"
        / f"runtime_approval_summary_{target_date}.json",
        "code_improvement_workorder": BASE_REPORT_DIR
        / "code_improvement_workorder"
        / f"code_improvement_workorder_{target_date}.json",
        "threshold_cycle_ev": BASE_REPORT_DIR / "threshold_cycle_ev" / f"threshold_cycle_ev_{target_date}.json",
        "lifecycle_decision_matrix": BASE_REPORT_DIR
        / "lifecycle_decision_matrix"
        / f"lifecycle_decision_matrix_{target_date}.json",
        "swing_lifecycle_decision_matrix": BASE_REPORT_DIR
        / "swing_lifecycle_decision_matrix"
        / f"swing_lifecycle_decision_matrix_{target_date}.json",
        "threshold_preopen_apply_next": _next_preopen_apply_path(target_date),
    }
    return file_map[label]


def _artifact_status(target_date: str) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    labels = (
        "lifecycle_bucket_discovery",
        "swing_lifecycle_bucket_discovery",
        "runtime_apply_bridge",
        "runtime_approval_summary",
        "code_improvement_workorder",
        "threshold_cycle_ev",
        "lifecycle_decision_matrix",
        "swing_lifecycle_decision_matrix",
        "threshold_preopen_apply_next",
    )
    status: dict[str, dict[str, Any]] = {}
    payloads: dict[str, dict[str, Any]] = {}
    for label in labels:
        path = _artifact_path(label, target_date)
        exists = path.exists()
        json_valid = False
        payload: dict[str, Any] = {}
        if exists:
            payload = _load_json(path)
            json_valid = bool(payload)
        status[label] = {
            "label": label,
            "path": str(path),
            "exists": exists,
            "json_valid": json_valid,
        }
        payloads[label] = payload
    return status, payloads


def _preopen_apply_consumed_candidate(apply_plan: dict[str, Any], candidate_id: str, family: str) -> bool:
    if not apply_plan:
        return False
    bridge = apply_plan.get("runtime_apply_bridge") if isinstance(apply_plan.get("runtime_apply_bridge"), dict) else {}
    approved = bridge.get("approved_requests") if isinstance(bridge.get("approved_requests"), list) else []
    for item in approved:
        if not isinstance(item, dict):
            continue
        if candidate_id and str(item.get("candidate_id") or item.get("bridge_candidate_id") or "") == candidate_id:
            return True
        if family and str(item.get("family") or item.get("policy_id") or "") == family:
            return True
    selected = apply_plan.get("auto_apply_selected") if isinstance(apply_plan.get("auto_apply_selected"), list) else []
    for item in selected:
        if not isinstance(item, dict):
            continue
        if candidate_id and str(item.get("candidate_id") or item.get("bridge_candidate_id") or "") == candidate_id:
            return True
        if family and str(item.get("family") or item.get("policy_id") or "") == family:
            return True
    return False


def _model_at_least_gpt54(model: str) -> bool:
    match = re.search(r"gpt-(\d+)(?:\.(\d+))?", str(model or "").lower())
    if not match:
        return False
    major = int(match.group(1))
    minor = int(match.group(2) or 0)
    return major > 5 or (major == 5 and minor >= 4)


def _candidate_id(item: dict[str, Any], fallback_prefix: str) -> str:
    for key in ("candidate_id", "bucket_id", "live_auto_apply_family", "family", "order_id"):
        value = str(item.get(key) or "").strip()
        if value:
            return value
    return f"{fallback_prefix}:{_text_hash(item)}"


def _candidate_family(item: dict[str, Any]) -> str:
    for key in ("family", "live_auto_apply_family", "runtime_family", "source_family"):
        value = str(item.get(key) or "").strip()
        if value:
            return value
    candidate_id = str(item.get("candidate_id") or "")
    return candidate_id.split(":", 1)[0] if candidate_id else ""


def _source_quality_gate(item: dict[str, Any]) -> str:
    gate = str(item.get("source_quality_gate") or "").strip()
    if gate:
        return gate
    source_bucket = item.get("source_bucket") if isinstance(item.get("source_bucket"), dict) else {}
    return str(source_bucket.get("source_quality_gate") or "").strip() or "unknown"


def _primary_ev(item: dict[str, Any]) -> float | None:
    for key in (
        "source_quality_adjusted_ev_pct",
        "notional_weighted_ev_pct",
        "equal_weight_avg_profit_pct",
        "primary_ev",
    ):
        value = _safe_float(item.get(key), None)
        if value is not None:
            return value
    source_bucket = item.get("source_bucket") if isinstance(item.get("source_bucket"), dict) else {}
    for key in ("source_quality_adjusted_ev_pct", "notional_weighted_ev_pct", "equal_weight_avg_profit_pct"):
        value = _safe_float(source_bucket.get(key), None)
        if value is not None:
            return value
    return None


def _sample(item: dict[str, Any]) -> int:
    source_bucket = item.get("source_bucket") if isinstance(item.get("source_bucket"), dict) else {}
    return max(
        _safe_int(item.get("sample"), 0),
        _safe_int(item.get("joined_sample"), 0),
        _safe_int(source_bucket.get("sample"), 0),
        _safe_int(source_bucket.get("joined_sample"), 0),
    )


def _source_state_to_disposition(state: str, gate: str) -> str:
    if state in FINAL_DISPOSITIONS:
        return state
    if state == "source_only_keep_collecting":
        return "source_quality_blocker" if gate != "pass" else "post_apply_attribution_pending"
    if state in {"automation_handoff_gap", "code_review_failed", "new_bucket_candidate"}:
        return "code_patch_required"
    if state in {"blocked_source_quality", "source_quality_gap"}:
        return "source_quality_blocker"
    if state in {"blocked_safety", "safety_veto"}:
        return "safety_veto"
    if state in {"blocked_rolling_conflict", "runtime_blocked_contract_gap"}:
        return "runtime_blocked_contract_gap"
    if state == "live_auto_apply_ready":
        return "live_auto_apply_ready"
    if state == "sim_auto_approved":
        return "sim_auto_approved"
    if state in {"bootstrap_pending", "hold_no_edge"}:
        return "source_only_keep_collecting"
    return "code_patch_required"


def _explicit_runtime_exclusion_reason(item: dict[str, Any]) -> str:
    for key in (
        "runtime_exclusion_reason",
        "runtime_apply_exclusion_reason",
        "bridge_exclusion_reason",
        "source_only_exclusion_reason",
        "explicit_runtime_exclusion_reason",
    ):
        value = str(item.get(key) or "").strip()
        if value:
            return value
    if item.get("explicit_runtime_exclusion") is True or item.get("source_only_explicit_exclusion") is True:
        return "source_only_explicit_exclusion"
    stage = str(item.get("stage") or item.get("lifecycle_stage") or "").strip()
    state = str(item.get("classification_state") or item.get("final_disposition") or "").strip()
    source_kind = str(item.get("source_bucket_kind") or "").strip()
    if (
        stage == "lifecycle_flow"
        and state == "source_only_keep_collecting"
        and source_kind in {"taxonomy_provenance_gap", "source_only_observation"}
    ):
        return "greenfield_policy_not_emitted_no_complete_lifecycle_flow"
    return ""


def _comparative_selected_decision(item: dict[str, Any]) -> str:
    review = item.get("comparative_review")
    if not isinstance(review, dict):
        review = item.get("ai_tier2_comparative_review")
    if not isinstance(review, dict):
        return ""
    return str(review.get("selected_decision") or "").strip()


def _greenfield_policy_issue(item: dict[str, Any]) -> str:
    if _candidate_family(item) != GREENFIELD_REAL_ENV_FAMILY:
        return ""
    recommended = item.get("recommended_values") if isinstance(item.get("recommended_values"), dict) else {}
    policy_file = str(recommended.get("policy_file") or item.get("greenfield_policy_file") or "").strip()
    recommended_version = str(recommended.get("policy_version") or item.get("candidate_id") or "")
    return validate_greenfield_policy_file(policy_file, expected_version=recommended_version or None)


def _ledger_from_discovery(
    discovery: dict[str, Any],
    *,
    target_date: str,
    domain: str,
    source_artifact: str,
) -> list[dict[str, Any]]:
    ledger: list[dict[str, Any]] = []
    candidates = discovery.get("surfaced_candidates")
    if not isinstance(candidates, list):
        candidates = discovery.get("candidates") if isinstance(discovery.get("candidates"), list) else []
    for item in candidates:
        if not isinstance(item, dict):
            continue
        candidate_id = _candidate_id(item, f"{domain}_discovery")
        family = _candidate_family(item)
        gate = _source_quality_gate(item)
        state = str(item.get("classification_state") or item.get("final_disposition") or "").strip()
        ev = _primary_ev(item)
        disposition = _source_state_to_disposition(state, gate)
        failure_state = "pass"
        failure_reason = ""
        exclusion_reason = _explicit_runtime_exclusion_reason(item)
        recommended_route = str(item.get("recommended_route") or "").strip()
        selected_decision = _comparative_selected_decision(item)
        if selected_decision == "source_quality_blocker":
            failure_state = "blocked_source_quality"
            failure_reason = "ai_tier2_source_quality_blocker"
            disposition = "source_quality_blocker"
        elif state == "source_only_keep_collecting" and gate == "pass" and ev is not None and ev > 0:
            if exclusion_reason:
                failure_state = "pass"
                failure_reason = ""
                disposition = "source_only_explicit_exclusion"
            else:
                failure_state = "fail"
                failure_reason = "positive_edge_stuck_source_only"
                disposition = "code_patch_required"
        elif gate not in {"pass", ""}:
            failure_state = "blocked_source_quality"
            failure_reason = "source_quality_gate_not_pass"
            disposition = "source_quality_blocker"
        ledger.append(
            {
                "candidate_id": candidate_id,
                "family": family,
                "domain": domain,
                "stage": str(item.get("stage") or "unknown"),
                "source_artifact": source_artifact,
                "producer_state": state or "unknown",
                "consumer_state": "pending_bridge_join" if disposition == "live_auto_apply_ready" else "source_only",
                "sample": _sample(item),
                "primary_ev": ev,
                "source_quality_gate": gate,
                "recommended_route": recommended_route,
                "actual_route": "source_discovery",
                "bridge_state": "not_joined",
                "preopen_apply_state": "not_checked",
                "runtime_hook_state": "not_checked",
                "post_apply_attribution_state": "not_checked",
                "final_disposition": disposition,
                "failure_state": failure_state,
                "failure_reason": failure_reason,
                "retryable": False,
                "retry_reason": "",
                "retry_owner": "",
                "next_retry_stage": "",
                "retry_deadline": "",
                "surface_channel": "runtime_apply_gap_audit",
                "source_bucket_kind": item.get("source_bucket_kind"),
                "ai_selected_decision": selected_decision,
                "explicit_runtime_exclusion": bool(exclusion_reason),
                "runtime_exclusion_reason": exclusion_reason,
            }
        )
    return ledger


def _ledger_from_bridge(
    bridge: dict[str, Any],
    *,
    target_date: str,
    preopen_apply: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    ledger: list[dict[str, Any]] = []
    candidates = bridge.get("candidates") if isinstance(bridge.get("candidates"), list) else []
    for item in candidates:
        if not isinstance(item, dict):
            continue
        state = str(item.get("bridge_candidate_state") or "unknown")
        gate = _source_quality_gate(item)
        family = _candidate_family(item)
        candidate_id = _candidate_id(item, "runtime_apply_bridge")
        preopen_consumed = _preopen_apply_consumed_candidate(preopen_apply or {}, candidate_id, family)
        disposition = _source_state_to_disposition(state, gate)
        failure_state = "pass"
        failure_reason = ""
        exclusion_reason = _explicit_runtime_exclusion_reason(item)
        retryable = False
        retry_reason = ""
        retry_owner = ""
        next_retry_stage = ""
        retry_deadline = ""
        if state == "live_auto_apply_ready":
            disposition = "post_apply_attribution_pending"
            if preopen_consumed:
                failure_state = "pass"
                failure_reason = ""
            else:
                failure_state = "retry_pending"
                failure_reason = "ready_but_not_applied"
                retryable = True
                retry_reason = "candidate must be consumed by the next PREOPEN bounded apply pass"
                retry_owner = "preopen_apply_candidate"
                next_retry_stage = "preopen_apply_candidate"
                retry_deadline = _next_day(target_date)
        elif state in {"runtime_blocked_contract_gap", "blocked_rolling_conflict"}:
            failure_state = "blocked_contract"
            failure_reason = state
            disposition = "runtime_blocked_contract_gap"
            if exclusion_reason:
                disposition = "source_only_explicit_exclusion"
        elif state == "blocked_source_quality":
            failure_state = "blocked_source_quality"
            failure_reason = "source_quality_gate_not_pass"
            disposition = "source_quality_blocker"
        greenfield_policy_issue = _greenfield_policy_issue(item)
        greenfield_policy_state = "not_applicable"
        if family == GREENFIELD_REAL_ENV_FAMILY:
            greenfield_policy_state = greenfield_policy_issue or "pass"
        if state == "live_auto_apply_ready" and greenfield_policy_issue:
            failure_state = "fail"
            failure_reason = greenfield_policy_issue
            disposition = "code_patch_required"
            retryable = True
            retry_reason = "greenfield live authority candidate must publish a valid policy artifact before PREOPEN apply"
            retry_owner = "runtime_apply_bridge"
            next_retry_stage = "runtime_apply_bridge"
            retry_deadline = "immediate_same_date_postclose_rerun"
        ledger.append(
            {
                "candidate_id": candidate_id,
                "family": family,
                "domain": "scalping",
                "stage": str(item.get("stage") or "unknown"),
                "source_artifact": "runtime_apply_bridge",
                "producer_state": state,
                "consumer_state": "runtime_approval_summary_expected",
                "sample": _sample(item),
                "primary_ev": _primary_ev(item),
                "source_quality_gate": gate,
                "recommended_route": "runtime_apply_bridge",
                "actual_route": state,
                "bridge_state": state,
                "preopen_apply_state": (
                    "consumed_by_next_preopen"
                    if preopen_consumed
                    else "pending_next_preopen"
                    if state == "live_auto_apply_ready"
                    else "not_ready"
                ),
                "runtime_hook_state": "mapped" if item.get("target_env_keys") else "env_mapping_missing",
                "post_apply_attribution_state": "pending" if state == "live_auto_apply_ready" else "not_applicable",
                "greenfield_policy_state": greenfield_policy_state,
                "final_disposition": disposition,
                "failure_state": failure_state,
                "failure_reason": failure_reason,
                "retryable": retryable,
                "retry_reason": retry_reason,
                "retry_owner": retry_owner,
                "next_retry_stage": next_retry_stage,
                "retry_deadline": retry_deadline,
                "surface_channel": "runtime_apply_gap_audit + postclose_verifier",
                "target_env_keys": item.get("target_env_keys") if isinstance(item.get("target_env_keys"), list) else [],
                "explicit_runtime_exclusion": bool(exclusion_reason),
                "runtime_exclusion_reason": exclusion_reason,
                "evidence_grade": item.get("evidence_grade"),
                "transition_target": item.get("transition_target"),
                "missing_runtime_source_fields": item.get("missing_runtime_source_fields")
                if isinstance(item.get("missing_runtime_source_fields"), list)
                else [],
            }
        )
    return ledger


def _next_day(target_date: str) -> str:
    try:
        return (date.fromisoformat(target_date) + timedelta(days=1)).isoformat()
    except Exception:
        return target_date


def _merge_ledger_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    rank = {
        "fail": 5,
        "retry_pending": 4,
        "blocked_contract": 3,
        "blocked_source_quality": 2,
        "blocked_safety": 2,
        "pass": 1,
    }
    for row in rows:
        candidate_id = str(row.get("candidate_id") or "")
        key = str(row.get("family") or candidate_id)
        if not key:
            continue
        current = merged.get(key)
        if current is None:
            merged[key] = dict(row)
            continue
        current_sources = current.setdefault("related_source_artifacts", [])
        if row.get("source_artifact") and row.get("source_artifact") not in current_sources:
            current_sources.append(row.get("source_artifact"))
        if rank.get(str(row.get("failure_state")), 0) >= rank.get(str(current.get("failure_state")), 0):
            replacement = dict(row)
            replacement["related_source_artifacts"] = current_sources
            if current.get("source_artifact") and current.get("source_artifact") not in current_sources:
                current_sources.append(current.get("source_artifact"))
            merged[key] = replacement
    return list(merged.values())


def _producer_consumer_contract_drift(
    ledger: list[dict[str, Any]],
    payloads: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    bridge_families = {
        str(item.get("family") or "")
        for item in payloads.get("runtime_apply_bridge", {}).get("candidates", [])
        if isinstance(item, dict)
    }
    drift: list[dict[str, Any]] = []
    for row in ledger:
        family = str(row.get("family") or "")
        if (
            row.get("producer_state") == "live_auto_apply_ready"
            and row.get("source_artifact") in {"lifecycle_bucket_discovery", "swing_lifecycle_bucket_discovery"}
            and family
            and family not in bridge_families
        ):
            row["failure_state"] = "fail"
            row["failure_reason"] = "producer_consumer_handoff_missing"
            row["final_disposition"] = "code_patch_required"
            row["retryable"] = True
            row["retry_reason"] = "runtime_apply_bridge must consume the live candidate or write an explicit exclusion"
            row["retry_owner"] = "runtime_apply_bridge"
            row["next_retry_stage"] = "runtime_apply_bridge"
            row["retry_deadline"] = "immediate_same_date_postclose_rerun"
            row["surface_channel"] = "runtime_apply_gap_audit + postclose_verifier"
            drift.append(
                {
                    "candidate_id": row.get("candidate_id"),
                    "family": family,
                    "drift_type": "producer_consumer_handoff_missing",
                    "producer": row.get("source_artifact"),
                    "consumer": "runtime_apply_bridge",
                    "severity": "fail",
                }
            )
    return drift


def _failure_item(
    *,
    code: str,
    retryable: bool,
    retry_reason: str,
    retry_owner: str,
    next_retry_stage: str,
    retry_deadline: str,
    surface_channel: str,
    candidate_id: str = "",
) -> dict[str, Any]:
    return {
        "candidate_id": candidate_id,
        "failure_code": code,
        "failure_state": "fail" if retryable else "blocked_contract",
        "retryable": retryable,
        "retry_reason": retry_reason,
        "retry_owner": retry_owner,
        "next_retry_stage": next_retry_stage,
        "retry_deadline": retry_deadline,
        "surface_channel": surface_channel,
    }


def _retry_queue_from_failures(ledger: list[dict[str, Any]], artifact_status: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    queue: list[dict[str, Any]] = []
    for label in CORE_ARTIFACT_LABELS:
        status = artifact_status.get(label, {})
        if not status.get("exists") or not status.get("json_valid"):
            queue.append(
                _failure_item(
                    code=f"{label}_missing_artifact",
                    retryable=True,
                    retry_reason="missing or invalid required runtime-apply-chain artifact",
                    retry_owner=label,
                    next_retry_stage=f"rerun_{label}",
                    retry_deadline="immediate_same_date_postclose_rerun",
                    surface_channel="runtime_apply_gap_audit + postclose_verifier",
                )
            )
    for row in ledger:
        if row.get("retryable") is True and row.get("failure_state") in {"fail", "retry_pending"}:
            queue.append(
                {
                    "candidate_id": row.get("candidate_id"),
                    "failure_code": row.get("failure_reason") or row.get("failure_state"),
                    "failure_state": row.get("failure_state"),
                    "retryable": True,
                    "retry_reason": row.get("retry_reason"),
                    "retry_owner": row.get("retry_owner"),
                    "next_retry_stage": row.get("next_retry_stage"),
                    "retry_deadline": row.get("retry_deadline"),
                    "surface_channel": row.get("surface_channel"),
                }
            )
    return queue


def _directive(
    directive_type: str,
    candidate: dict[str, Any],
    *,
    reason: str,
    blocking_contract: str,
) -> dict[str, Any]:
    candidate_id = str(candidate.get("candidate_id") or "")
    return {
        "directive_type": directive_type,
        "candidate_id": candidate_id,
        "goal": f"Close runtime apply gap for {candidate_id}",
        "evidence": {
            "source_artifact": candidate.get("source_artifact"),
            "stage": candidate.get("stage"),
            "primary_ev": candidate.get("primary_ev"),
            "source_quality_gate": candidate.get("source_quality_gate"),
            "failure_reason": candidate.get("failure_reason"),
        },
        "ai_reasoning_summary": candidate.get("ai_reason_en") or reason,
        "blocking_contract": blocking_contract,
        "required_code_changes": [
            "Wire the producer artifact to the next consumer with an explicit source link or exclusion reason.",
            "Keep runtime_effect and allowed_runtime_apply guarded by existing hard safety, broker, stale quote, qty, cooldown, provider, and cap contracts.",
            "Add or update tests that fail when the handoff is missing.",
        ],
        "forbidden_changes": [
            "Do not bypass broker/order guard.",
            "Do not mutate intraday runtime thresholds.",
            "Do not release position cap or provider route without existing approval artifact.",
        ],
        "test_targets": [
            "src/tests/test_runtime_apply_gap_audit.py",
            "src/tests/test_verify_threshold_cycle_postclose_chain.py",
        ],
        "acceptance_criteria": [
            "The candidate has one final_disposition.",
            "Any fail has retryable status, owner, next_retry_stage, deadline, and surface channel.",
            "Postclose verifier fails if the handoff disappears.",
        ],
        "retry_policy": {
            "retryable": bool(candidate.get("retryable")),
            "next_retry_stage": candidate.get("next_retry_stage") or "code_patch_then_postclose_rerun",
            "retry_deadline": candidate.get("retry_deadline") or "next_postclose",
        },
        "body_ko": _directive_body_ko(directive_type, candidate, reason),
    }


def _directive_body_ko(directive_type: str, candidate: dict[str, Any], reason: str) -> str:
    return (
        f"{directive_type}: {candidate.get('candidate_id')} 후보가 {reason} 상태입니다. "
        "생산 artifact에서 소비 artifact까지 source link 또는 명시적 제외 사유를 남기고, "
        "runtime/order/provider/cap guard는 우회하지 마십시오."
    )


def _build_codex_directives(ledger: list[dict[str, Any]], retry_queue: list[dict[str, Any]]) -> list[dict[str, Any]]:
    directives: list[dict[str, Any]] = []
    for row in ledger:
        if row.get("explicit_runtime_exclusion") is True:
            continue
        reason = str(row.get("failure_reason") or "")
        if reason == "positive_edge_stuck_source_only":
            directives.append(
                _directive(
                    "RESOLVE_SOURCE_ONLY_STUCK_POSITIVE_EDGE",
                    row,
                    reason=reason,
                    blocking_contract="positive_edge_must_not_default_to_source_only_keep_collecting",
                )
            )
        elif reason == "producer_consumer_handoff_missing":
            directives.append(
                _directive(
                    "FIX_PRODUCER_CONSUMER_HANDOFF",
                    row,
                    reason=reason,
                    blocking_contract="producer_consumer_contract",
                )
            )
        elif row.get("failure_state") == "blocked_contract":
            directive_type = (
                "IMPLEMENT_SCALE_IN_POLICY_CONTRACT"
                if row.get("stage") == "scale_in"
                else "IMPLEMENT_RUNTIME_BRIDGE_FOR_ENTRY_BUCKET"
            )
            directives.append(
                _directive(
                    directive_type,
                    row,
                    reason=reason or "runtime_contract_gap",
                    blocking_contract="runtime_bridge_contract",
                )
            )
        elif row.get("runtime_hook_state") == "env_mapping_missing":
            directives.append(
                _directive(
                    "IMPLEMENT_RUNTIME_BRIDGE_FOR_ENTRY_BUCKET",
                    row,
                    reason="env_mapping_missing",
                    blocking_contract="env_mapping_contract",
                )
            )
    for item in retry_queue:
        if str(item.get("failure_code") or "").endswith("_missing_artifact"):
            directives.append(
                _directive(
                    "RETRY_MISSING_ARTIFACT_CHAIN",
                    {"candidate_id": item.get("failure_code"), **item},
                    reason=str(item.get("failure_code")),
                    blocking_contract="artifact_availability_contract",
                )
            )
    unique: dict[tuple[str, str], dict[str, Any]] = {}
    for item in directives:
        unique[(str(item.get("directive_type")), str(item.get("candidate_id")))] = item
    return list(unique.values())


def _build_ai_review_prompt_en(context: dict[str, Any]) -> str:
    return (
        "You are runtime_apply_gap_ai_review, an aggressive runtime uptake reviewer.\n"
        "Use English only. Return strict JSON matching runtime_apply_gap_ai_review_v1.\n"
        "Push candidates with positive primary EV toward runtime when source quality and hard safety contracts pass.\n"
        "Do not block a candidate only because the edge is small, confidence is low, the bucket is new, or routing is ambiguous.\n"
        "Block only for explicit source-quality, safety, broker, stale quote, qty, cooldown, provider, cap, env mapping, runtime hook, or post-apply attribution gaps.\n"
        "Never approve broker guard bypass, intraday threshold mutation, provider route change, bot restart, or position cap release.\n"
        "Every failed or ambiguous candidate must include a retry or code directive.\n"
        "Input context JSON follows:\n"
        f"{json.dumps(context, ensure_ascii=True, sort_keys=True, default=str)}"
    )


def _render_ai_input_context_en(ledger: list[dict[str, Any]], drift: list[dict[str, Any]]) -> dict[str, Any]:
    review_candidates = [
        {
            "candidate_id": row.get("candidate_id"),
            "domain": row.get("domain"),
            "stage": row.get("stage"),
            "primary_ev": row.get("primary_ev"),
            "source_quality_gate": row.get("source_quality_gate"),
            "producer_state": row.get("producer_state"),
            "final_disposition": row.get("final_disposition"),
            "failure_state": row.get("failure_state"),
            "failure_reason": row.get("failure_reason"),
        }
        for row in ledger
        if row.get("explicit_runtime_exclusion") is not True
        and (
            row.get("failure_state") != "pass"
        or (
            row.get("primary_ev") is not None
            and float(row.get("primary_ev") or 0.0) > 0
            and row.get("final_disposition") != "live_auto_apply_ready"
        )
        )
    ][:40]
    return {
        "reviewer": AI_REVIEWER_NAME,
        "language": "en",
        "policy": "aggressive_positive_edge_push_without_safety_bypass",
        "candidate_count": len(ledger),
        "review_candidates": review_candidates,
        "producer_consumer_contract_drift": drift[:20],
    }


def _parse_ai_review_response(raw_response: Any | None) -> tuple[str, dict[str, Any], list[str]]:
    if raw_response is None:
        return "unavailable", {}, ["ai_review_response_missing"]
    payload: Any = raw_response
    if isinstance(raw_response, str):
        try:
            payload = json.loads(raw_response)
        except Exception as exc:
            return "parse_rejected", {}, [f"ai_review_json_parse_failed:{exc}"]
    if not isinstance(payload, dict):
        return "parse_rejected", {}, ["ai_review_non_dict"]
    warnings: list[str] = []
    if payload.get("schema_version") != 1:
        warnings.append("ai_review_schema_version_invalid")
    if payload.get("reviewer") != AI_REVIEWER_NAME:
        warnings.append("ai_review_reviewer_invalid")
    reviews = payload.get("candidate_reviews")
    if not isinstance(reviews, list):
        warnings.append("ai_review_candidate_reviews_missing")
    audit = payload.get("audit") if isinstance(payload.get("audit"), dict) else {}
    if not audit:
        warnings.append("ai_review_audit_missing")
    for item in reviews if isinstance(reviews, list) else []:
        if not isinstance(item, dict):
            warnings.append("ai_review_candidate_non_dict")
            continue
        if str(item.get("recommended_disposition") or "") not in FINAL_DISPOSITIONS:
            warnings.append(f"ai_review_invalid_disposition:{item.get('candidate_id')}")
    if warnings:
        return "parse_rejected", payload, warnings
    return "parsed", payload, []


def _legacy_runtime_apply_gap_timeout_default() -> int:
    raw = os.getenv("RUNTIME_APPLY_GAP_AI_REVIEW_TIMEOUT_SEC")
    if raw in (None, ""):
        return AI_REVIEW_TIMEOUT_SEC
    try:
        return int(float(str(raw).strip()))
    except Exception:
        return AI_REVIEW_TIMEOUT_SEC


def _ai_review_config(*, model_override: str | None = None) -> PostcloseAIReviewConfig:
    legacy_model = str(os.getenv("RUNTIME_APPLY_GAP_AI_REVIEW_MODEL") or AI_REVIEW_MODEL).strip() or AI_REVIEW_MODEL
    legacy_reasoning = (
        str(os.getenv("RUNTIME_APPLY_GAP_AI_REVIEW_REASONING_EFFORT") or AI_REVIEW_REASONING_EFFORT).strip()
        or AI_REVIEW_REASONING_EFFORT
    )
    config = resolve_postclose_ai_review_config(
        "RUNTIME_APPLY_GAP_AUDIT",
        default_model=legacy_model,
        default_reasoning_effort=legacy_reasoning,
        default_timeout_sec=_legacy_runtime_apply_gap_timeout_default(),
    )
    if model_override:
        return replace(config, model=str(model_override).strip() or config.model)
    return config


def _call_openai_ai_review(
    input_context: dict[str, Any],
    *,
    config: PostcloseAIReviewConfig,
) -> tuple[Any | None, dict[str, Any]]:
    try:
        from openai import OpenAI, RateLimitError
        from src.engine.ai_response_contracts import build_openai_response_text_format
    except Exception as exc:
        return None, {"provider": "openai", "status": "unavailable", "reason": f"openai import failed: {exc}", **config.provider_status_fields()}
    api_keys = _load_threshold_ai_openai_keys()
    if not api_keys:
        return None, {"provider": "openai", "status": "unavailable", "reason": "OPENAI_API_KEY not configured", **config.provider_status_fields()}
    prompt = _build_ai_review_prompt_en(input_context)
    errors: list[dict[str, str]] = []
    for attempt_index, (key_name, api_key) in enumerate(api_keys, start=1):
        try:
            client = OpenAI(api_key=api_key)
            response = client.responses.create(
                model=config.model,
                instructions="Return only strict JSON for runtime_apply_gap_ai_review_v1.",
                input=prompt,
                text={"format": build_openai_response_text_format(AI_REVIEW_SCHEMA_NAME), "verbosity": "low"},
                reasoning={"effort": config.reasoning_effort},
                store=False,
                metadata={
                    "endpoint_name": "runtime_apply_gap_ai_review",
                    "schema_name": AI_REVIEW_SCHEMA_NAME,
                    "report_type": "runtime_apply_gap_audit",
                },
                timeout=config.timeout_sec,
            )
            raw_text = _extract_openai_response_text(response)
            usage = getattr(response, "usage", None)
            return raw_text, {
                "provider": "openai",
                "status": "success",
                "key_name": key_name,
                "attempt_index": attempt_index,
                "attempted_key_count": len(api_keys),
                "schema_name": AI_REVIEW_SCHEMA_NAME,
                **config.provider_status_fields(),
                "input_context_hash": _text_hash(input_context),
                "input_context_chars": len(prompt),
                "output_chars": len(raw_text),
                "input_tokens": int(getattr(usage, "input_tokens", 0) or 0) if usage else 0,
                "output_tokens": int(getattr(usage, "output_tokens", 0) or 0) if usage else 0,
                "total_tokens": int(getattr(usage, "total_tokens", 0) or 0) if usage else 0,
            }
        except RateLimitError as exc:
            errors.append({"key_name": key_name, "error": f"rate_limit:{exc}"})
        except Exception as exc:
            errors.append({"key_name": key_name, "error": str(exc)})
    return None, {
        "provider": "openai",
        "status": "unavailable",
        "reason": "all OpenAI attempts failed",
        **config.provider_status_fields(),
        "errors": errors[-3:],
    }


def _run_ai_review(
    ledger: list[dict[str, Any]],
    drift: list[dict[str, Any]],
    *,
    provider: str,
    config: PostcloseAIReviewConfig,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    context = _render_ai_input_context_en(ledger, drift)
    prompt = _build_ai_review_prompt_en(context)
    base = {
        "reviewer": AI_REVIEWER_NAME,
        "provider": provider,
        "model": config.model,
        "minimum_model": MIN_AI_REVIEW_MODEL,
        "model_minimum_pass": _model_at_least_gpt54(config.model),
        "reasoning_effort": config.reasoning_effort,
        "timeout_sec": config.timeout_sec,
        "config_env_prefix": config.env_prefix_name,
        "ai_prompt_language": "en",
        "input_context_hash": _text_hash(context),
        "input_context_candidate_count": len(context.get("review_candidates") or []),
        "prompt_hash": _text_hash(prompt),
    }
    retry_items: list[dict[str, Any]] = []
    directives: list[dict[str, Any]] = []
    if not base["model_minimum_pass"]:
        review = {
            **base,
            "status": "fail",
            "failure_code": "ai_review_model_too_low",
            "failure_state": "fail",
            "retryable": False,
            "ai_review_retry_pending": False,
            "warnings": ["ai_review_model_too_low"],
        }
        directives.append(
            _directive(
                "RETRY_FAILED_AI_REVIEW",
                {"candidate_id": "runtime_apply_gap_ai_review", "retryable": False},
                reason="ai_review_model_too_low",
                blocking_contract="ai_model_minimum_contract",
            )
        )
        return review, retry_items, directives
    if not context.get("review_candidates"):
        return {
            **base,
            "status": "not_required",
            "failure_state": "pass",
            "ai_review_retry_pending": False,
            "review_payload": {"schema_version": 1, "reviewer": AI_REVIEWER_NAME, "candidate_reviews": []},
        }, retry_items, directives
    if provider == "none":
        review = {
            **base,
            "status": "disabled",
            "failure_state": "retry_pending",
            "failure_code": "ai_review_unavailable",
            "retryable": True,
            "ai_review_retry_pending": True,
            "warnings": ["ai_review_provider_disabled"],
        }
        retry_items.append(
            _failure_item(
                code="ai_review_unavailable",
                retryable=True,
                retry_reason="AI reviewer disabled while ambiguous runtime uptake candidates exist",
                retry_owner=AI_REVIEWER_NAME,
                next_retry_stage="runtime_apply_gap_ai_review",
                retry_deadline="immediate_same_date_postclose_rerun",
                surface_channel="runtime_apply_gap_audit + postclose_verifier",
            )
        )
        directives.append(
            _directive(
                "RETRY_FAILED_AI_REVIEW",
                {"candidate_id": "runtime_apply_gap_ai_review", "retryable": True},
                reason="ai_review_unavailable",
                blocking_contract="ai_reasoning_review_contract",
            )
        )
        return review, retry_items, directives
    raw_response, provider_status = _call_openai_ai_review(context, config=config)
    parse_status, payload, warnings = _parse_ai_review_response(raw_response)
    if parse_status != "parsed":
        failure_code = "ai_parse_fail" if raw_response is not None else "ai_review_unavailable"
        review = {
            **base,
            "status": "fail",
            "failure_state": "fail",
            "failure_code": failure_code,
            "retryable": True,
            "ai_review_retry_pending": True,
            "provider_status": provider_status,
            "warnings": warnings,
            "raw_response": raw_response if isinstance(raw_response, str) else None,
        }
        retry_items.append(
            _failure_item(
                code=failure_code,
                retryable=True,
                retry_reason="AI review unavailable or schema parse failed",
                retry_owner=AI_REVIEWER_NAME,
                next_retry_stage="runtime_apply_gap_ai_review",
                retry_deadline="immediate_same_date_postclose_rerun",
                surface_channel="runtime_apply_gap_audit + postclose_verifier",
            )
        )
        directives.append(
            _directive(
                "RETRY_FAILED_AI_REVIEW",
                {"candidate_id": "runtime_apply_gap_ai_review", "retryable": True},
                reason=failure_code,
                blocking_contract="ai_reasoning_review_contract",
            )
        )
        return review, retry_items, directives
    return {
        **base,
        "status": "parsed",
        "failure_state": "pass",
        "retryable": False,
        "ai_review_retry_pending": False,
        "provider_status": provider_status,
        "review_payload": payload,
    }, retry_items, directives


def _reason_ko_from_ai_route(route_decision: str, disposition: str) -> str:
    route = str(route_decision or "")
    disposition_text = str(disposition or "")
    if route == "push_runtime":
        return "양수 기대값과 source-quality 통과 조건이 있어 런타임 방향으로 밀어야 합니다."
    if route == "require_code_patch":
        return "런타임 연결 계약이 닫히지 않아 코드 보완 작업지시가 필요합니다."
    if route == "retry_handoff":
        return "생산/소비 handoff가 누락되어 같은 날짜 postclose 재시도가 필요합니다."
    if route == "block_source_quality":
        return "source-quality 계약 미충족으로 런타임 적용이 차단됩니다."
    if route == "block_safety":
        return "hard safety 계약 때문에 런타임 적용이 차단됩니다."
    if route == "require_approval":
        return "final-stage 사용자 승인 또는 pre-final auto-promotion 계약 확인이 필요한 후보입니다."
    return f"AI reviewer 권고 disposition은 {disposition_text or 'unknown'}입니다."


def _apply_ai_review_to_ledger(ledger: list[dict[str, Any]], ai_review: dict[str, Any]) -> None:
    payload = ai_review.get("review_payload") if isinstance(ai_review.get("review_payload"), dict) else {}
    reviews = payload.get("candidate_reviews") if isinstance(payload.get("candidate_reviews"), list) else []
    by_id = {str(row.get("candidate_id")): row for row in ledger}
    for item in reviews:
        if not isinstance(item, dict):
            continue
        row = by_id.get(str(item.get("candidate_id") or ""))
        if row is None:
            continue
        raw_reason = str(item.get("reason") or "").strip()
        row["ai_recommended_disposition"] = item.get("recommended_disposition")
        row["ai_route_decision"] = item.get("route_decision")
        row["ai_reason_en"] = raw_reason
        row["ai_reason_language_violation"] = any(ord(ch) > 127 for ch in raw_reason)
        row["reason_ko"] = _reason_ko_from_ai_route(
            str(item.get("route_decision") or ""),
            str(item.get("recommended_disposition") or ""),
        )


def _runtime_uptake_kpi(ledger: list[dict[str, Any]]) -> dict[str, Any]:
    positive = [
        row
        for row in ledger
        if row.get("primary_ev") is not None
        and float(row.get("primary_ev") or 0.0) > 0
        and row.get("source_quality_gate") == "pass"
    ]
    ready = [row for row in ledger if row.get("final_disposition") == "live_auto_apply_ready"]
    fail = [row for row in ledger if row.get("failure_state") == "fail"]
    retry = [row for row in ledger if row.get("failure_state") == "retry_pending"]
    return {
        "candidate_count": len(ledger),
        "positive_edge_source_quality_pass_count": len(positive),
        "live_auto_apply_ready_count": len(ready),
        "fail_count": len(fail),
        "retry_pending_count": len(retry),
        "runtime_uptake_rate_pct": round((len(ready) / len(positive) * 100.0), 2) if positive else 0.0,
    }


def _aggressive_push_targets(ledger: list[dict[str, Any]]) -> list[dict[str, Any]]:
    targets: list[dict[str, Any]] = []
    for row in ledger:
        ev = row.get("primary_ev")
        if ev is None or float(ev or 0.0) <= 0 or row.get("source_quality_gate") != "pass":
            continue
        if row.get("final_disposition") in {"source_quality_blocker", "safety_veto"}:
            continue
        if row.get("explicit_runtime_exclusion") is True:
            continue
        targets.append(
            {
                "candidate_id": row.get("candidate_id"),
                "family": row.get("family"),
                "stage": row.get("stage"),
                "primary_ev": ev,
                "current_disposition": row.get("final_disposition"),
                "push_direction": (
                    "runtime_bridge"
                    if row.get("stage") in {"entry", "scale_in"}
                    else "sim_policy_or_approval_ready"
                ),
            }
        )
    return targets


def build_runtime_apply_gap_audit(
    target_date: str,
    *,
    ai_review_provider: str | None = None,
    ai_review_model: str | None = None,
) -> dict[str, Any]:
    provider = str(ai_review_provider or os.environ.get("RUNTIME_APPLY_GAP_AI_REVIEW_PROVIDER") or "openai").strip()
    config = _ai_review_config(model_override=ai_review_model)
    artifact_status, payloads = _artifact_status(target_date)
    ledger_rows: list[dict[str, Any]] = []
    discovery = payloads.get("lifecycle_bucket_discovery") or {}
    if discovery:
        ledger_rows.extend(
            _ledger_from_discovery(
                discovery,
                target_date=target_date,
                domain="scalping",
                source_artifact="lifecycle_bucket_discovery",
            )
        )
    swing_discovery = payloads.get("swing_lifecycle_bucket_discovery") or {}
    if swing_discovery:
        ledger_rows.extend(
            _ledger_from_discovery(
                swing_discovery,
                target_date=target_date,
                domain="swing",
                source_artifact="swing_lifecycle_bucket_discovery",
            )
        )
    bridge = payloads.get("runtime_apply_bridge") or {}
    if bridge:
        ledger_rows.extend(
            _ledger_from_bridge(
                bridge,
                target_date=target_date,
                preopen_apply=payloads.get("threshold_preopen_apply_next") or {},
            )
        )
    ledger = _merge_ledger_rows(ledger_rows)
    drift = _producer_consumer_contract_drift(ledger, payloads)
    retry_queue = _retry_queue_from_failures(ledger, artifact_status)
    ai_review, ai_retry, ai_directives = _run_ai_review(ledger, drift, provider=provider, config=config)
    _apply_ai_review_to_ledger(ledger, ai_review)
    retry_queue.extend(ai_retry)
    codex_directives = _build_codex_directives(ledger, retry_queue)
    codex_directives.extend(ai_directives)
    kpi = _runtime_uptake_kpi(ledger)
    critical_failures = [
        row for row in ledger if row.get("failure_state") == "fail"
    ] + [
        {"failure_reason": item.get("failure_code")}
        for item in retry_queue
        if item.get("failure_state") == "fail"
    ]
    if ai_review.get("failure_state") == "fail":
        critical_failures.append({"failure_reason": ai_review.get("failure_code")})
    status = "fail" if critical_failures else "warning" if retry_queue else "pass"
    return {
        "date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "report_type": "runtime_apply_gap_audit",
        "schema_version": REPORT_SCHEMA_VERSION,
        "status": status,
        "ai_prompt_language": "en",
        "user_output_language": "ko",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "decision_authority": "runtime_apply_gap_aggressive_watcher_source_only",
        "sources": {label: status_item["path"] for label, status_item in artifact_status.items()},
        "artifact_status": artifact_status,
        "runtime_uptake_kpi": kpi,
        "candidate_route_ledger": ledger,
        "producer_consumer_contract_drift": drift,
        "aggressive_push_targets": _aggressive_push_targets(ledger),
        "ai_reasoning_review": ai_review,
        "codex_workorder_directives": codex_directives,
        "retry_queue": retry_queue,
        "summary": {
            "status": status,
            "candidate_count": kpi["candidate_count"],
            "positive_edge_source_quality_pass_count": kpi["positive_edge_source_quality_pass_count"],
            "runtime_uptake_rate_pct": kpi["runtime_uptake_rate_pct"],
            "critical_failure_count": len(critical_failures),
            "retry_queue_count": len(retry_queue),
            "codex_directive_count": len(codex_directives),
            "ai_review_status": ai_review.get("status"),
            "ai_review_retry_pending": ai_review.get("ai_review_retry_pending") is True,
        },
    }


def _render_markdown_ko(report: dict[str, Any]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    kpi = report.get("runtime_uptake_kpi") if isinstance(report.get("runtime_uptake_kpi"), dict) else {}
    retry_queue = report.get("retry_queue") if isinstance(report.get("retry_queue"), list) else []
    directives = report.get("codex_workorder_directives") if isinstance(report.get("codex_workorder_directives"), list) else []
    push_targets = report.get("aggressive_push_targets") if isinstance(report.get("aggressive_push_targets"), list) else []
    lines = [
        f"# Runtime Apply Gap Audit - {report.get('date')}",
        "",
        f"- 상태: `{report.get('status')}`",
        f"- 런타임 적용률: `{kpi.get('runtime_uptake_rate_pct', 0)}%`",
        f"- 양수 EV + source-quality pass 후보: `{kpi.get('positive_edge_source_quality_pass_count', 0)}`",
        f"- 실패 표면화: `{summary.get('critical_failure_count', 0)}`",
        f"- 재시도 큐: `{len(retry_queue)}`",
        f"- Codex 작업지시: `{len(directives)}`",
        "",
        "## 공격적 런타임 추진 대상",
    ]
    if push_targets:
        for item in push_targets[:20]:
            lines.append(
                f"- `{item.get('candidate_id')}`: stage={item.get('stage')}, EV={item.get('primary_ev')}, "
                f"방향={item.get('push_direction')}, 현재={item.get('current_disposition')}"
            )
    else:
        lines.append("- 대상 없음")
    lines.extend(["", "## 재시도 큐"])
    if retry_queue:
        for item in retry_queue[:20]:
            lines.append(
                f"- `{item.get('failure_code')}`: owner={item.get('retry_owner')}, "
                f"stage={item.get('next_retry_stage')}, deadline={item.get('retry_deadline')}"
            )
    else:
        lines.append("- 재시도 대상 없음")
    lines.extend(["", "## Codex 작업지시"])
    if directives:
        for item in directives[:20]:
            lines.append(f"- `{item.get('directive_type')}`: {item.get('body_ko')}")
    else:
        lines.append("- 신규 작업지시 없음")
    lines.extend(
        [
            "",
            "## 계약",
            "- 내부 AI 프롬프트 언어: `en`",
            "- 사용자 표시 언어: `ko`",
            "- runtime/env/live order 변경: 금지",
        ]
    )
    return "\n".join(lines) + "\n"


def write_runtime_apply_gap_audit(report: dict[str, Any]) -> tuple[Path, Path]:
    target_date = str(report.get("date"))
    json_path = runtime_apply_gap_audit_report_path(target_date)
    md_path = runtime_apply_gap_audit_markdown_path(target_date)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(_render_markdown_ko(report), encoding="utf-8")
    return json_path, md_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build runtime apply gap audit")
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--ai-review-provider", default=None)
    parser.add_argument("--ai-review-model", default=None)
    args = parser.parse_args(argv)
    report = build_runtime_apply_gap_audit(
        args.date,
        ai_review_provider=args.ai_review_provider,
        ai_review_model=args.ai_review_model,
    )
    json_path, md_path = write_runtime_apply_gap_audit(report)
    print(f"runtime_apply_gap_audit_json={json_path}")
    print(f"runtime_apply_gap_audit_md={md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
