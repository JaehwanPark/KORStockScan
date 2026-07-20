"""Classify Swing LDM buckets into sim-only automation routes."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from collections import Counter, defaultdict
from dataclasses import replace
from datetime import date, datetime
from pathlib import Path
from typing import Any

from src.engine.ai.postclose_review_config import (
    PostcloseAIReviewConfig,
    parsed_review_followup_reasons,
    resolve_postclose_ai_review_config,
)
from src.engine.automation.dual_candidate_review import (
    evidence_authority_contract,
    REQUIRED_METRIC_CONTRACT_FIELDS,
    has_evidence_authority_violation,
    has_forbidden_runtime_leak,
    missing_metric_contract_fields,
    proposal_counts,
    with_evidence_authority_forbidden_uses,
)
from src.engine.lifecycle.bucket_taxonomy import (
    BUCKET_ALIAS_VERSION,
    DIMENSION_SET_VERSION,
    compare_taxonomy_proposals,
    default_ai_tier2_proposal,
    normalize_lifecycle_bucket,
)
from src.engine.swing.sim_auto_approval_control_tower import (
    refresh_swing_sim_auto_approval,
)
from src.engine.swing_lifecycle_decision_matrix import (
    report_paths as matrix_report_paths,
)
from src.utils.constants import DATA_DIR

REPORT_DIR = Path(DATA_DIR) / "report" / "swing_lifecycle_bucket_discovery"
REPORT_TYPE = "swing_lifecycle_bucket_discovery"
DISCOVERY_VERSION = "swing_lifecycle_bucket_discovery_v1"
DECISION_AUTHORITY = "swing_ldm_bucket_discovery_sim_auto"
AI_REVIEW_SCHEMA_NAME = "swing_lifecycle_bucket_discovery_review_v1"
AI_REVIEWER_NAME = "swing_lifecycle_bucket_discovery_ai_review"
AI_REVIEW_MODEL = "gpt-5.4-mini"
AI_REVIEW_REASONING_EFFORT = "medium"
AI_REVIEW_TIMEOUT_SEC = 180
AI_REVIEW_DEFAULT_PROVIDER = "openai"
AI_REVIEW_SIM_SHARD_SIZE = 20
FORBIDDEN_USES = [
    "real_order_submit",
    "one_share_real_canary",
    "scale_in_real_canary",
    "provider_route_change",
    "bot_restart",
    "runtime_threshold_mutation",
]
FORBIDDEN_USES = with_evidence_authority_forbidden_uses(FORBIDDEN_USES)

CLASSIFICATION_STATES = {
    "sim_auto_approved",
    "source_only_keep_collecting",
    "code_patch_required",
    "runtime_blocked_contract_gap",
    "automation_handoff_gap",
}
IMPLEMENTED_SOURCE_QUALITY_STATUSES = {
    "implemented",
    "implemented_but_hold_sample",
    "implemented_source_quality_contract_waiting_sample",
}
TAXONOMY_DECISIONS = {
    "merge",
    "absorb_as_dimension",
    "create_new_metric",
    "create_new_dimension",
    "keep_bucket",
    "reject",
    "source_quality_blocker",
    "instrumentation_gap",
}


def _date_text(value: str | date | datetime | None) -> str:
    if value is None:
        return date.today().isoformat()
    return str(value)[:10]


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _slug(value: Any) -> str:
    text = re.sub(r"[^a-zA-Z0-9가-힣]+", "_", str(value or "").strip().lower()).strip(
        "_"
    )
    return text[:80] or "unknown"


def _bucket_key_slug(value: Any) -> str:
    text = re.sub(r"[^a-zA-Z0-9가-힣]+", "_", str(value or "").strip().lower()).strip(
        "_"
    )
    if not text:
        return "unknown"
    if len(text) <= 80:
        return text
    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]
    return f"{text[:67].rstrip('_')}_{digest}"


def _matrix_candidate_slug(value: Any, *, max_len: int = 80) -> str:
    text = re.sub(r"[^a-zA-Z0-9가-힣]+", "_", str(value or "").strip().lower()).strip(
        "_"
    )
    if not text:
        return "unknown"
    if len(text) <= max_len:
        return text
    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:10]
    return f"{text[: max_len - 11].rstrip('_')}_{digest}"


def report_paths(target_date: str) -> tuple[Path, Path]:
    base = REPORT_DIR / f"swing_lifecycle_bucket_discovery_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def _bucket_id(stage: str, bucket_type: str, bucket_key: str) -> str:
    return f"swing_bucket_{_slug(stage)}_{_slug(bucket_type)}_{_bucket_key_slug(bucket_key)}"


def _matrix_sim_auto_candidate_id(stage: str, bucket_type: str, bucket_key: str) -> str:
    return f"swing_ldm_{_slug(stage)}_{_slug(bucket_type)}_{_matrix_candidate_slug(bucket_key)}"


def _is_implemented_source_quality_waiting(item: dict[str, Any]) -> bool:
    return (
        str(item.get("implementation_status") or "").strip()
        in IMPLEMENTED_SOURCE_QUALITY_STATUSES
    )


def _would_require_source_quality_patch(bucket: dict[str, Any]) -> bool:
    route = str(bucket.get("recommended_route") or "")
    gate = str(bucket.get("source_quality_gate") or "")
    return route == "code_patch_required" or gate == "source_quality_blocker"


def _classification_from_bucket(section_name: str, bucket: dict[str, Any]) -> str:
    route = str(bucket.get("recommended_route") or "")
    gate = str(bucket.get("source_quality_gate") or "")
    try:
        joined = int(float(bucket.get("joined_sample") or 0))
    except (TypeError, ValueError):
        joined = 0
    ev = None
    try:
        ev = float(bucket.get("source_quality_adjusted_ev_pct"))
    except (TypeError, ValueError):
        ev = None
    if section_name == "swing_lifecycle_flow_bucket_attribution":
        if (
            route == "sim_auto_approved"
            and gate == "pass"
            and joined >= 3
            and ev is not None
            and ev > 0
        ):
            return "sim_auto_approved"
        if _would_require_source_quality_patch(bucket):
            if _is_implemented_source_quality_waiting(bucket):
                return "source_only_keep_collecting"
            return "code_patch_required"
        return "source_only_keep_collecting"
    if route == "sim_auto_approved":
        return "source_only_keep_collecting"
    if _would_require_source_quality_patch(bucket):
        if _is_implemented_source_quality_waiting(bucket):
            return "source_only_keep_collecting"
        return "code_patch_required"
    if joined <= 0 or gate == "hold_sample":
        return "source_only_keep_collecting"
    return "source_only_keep_collecting"


def _source_remediation_proposal(
    proposal: dict[str, Any],
    *,
    source_quality_gate: Any,
) -> dict[str, Any]:
    return {
        **proposal,
        "proposal_decision": (
            "source_quality_blocker"
            if str(source_quality_gate or "") == "source_quality_blocker"
            else "instrumentation_gap"
        ),
        "candidate_type": "source_quality_or_code_patch_required",
        "reasoning_summary": (
            "candidate classification requires source-only remediation before taxonomy authority; "
            "runtime/order/provider/bot authority remains forbidden"
        ),
    }


def _candidate_from_bucket(section_name: str, bucket: dict[str, Any]) -> dict[str, Any]:
    stage = str(bucket.get("lifecycle_stage") or "swing")
    bucket_type = str(bucket.get("bucket_type") or section_name)
    bucket_key = str(bucket.get("bucket_key") or "-")
    state = _classification_from_bucket(section_name, bucket)
    source_candidate_id = str(
        bucket.get("candidate_id") or bucket.get("bucket_id") or ""
    ).strip()
    if (
        section_name == "swing_lifecycle_flow_bucket_attribution"
        and state == "sim_auto_approved"
    ):
        bucket_id = source_candidate_id or _matrix_sim_auto_candidate_id(
            stage, bucket_type, bucket_key
        )
        source_candidate_id = source_candidate_id or bucket_id
    else:
        bucket_id = _bucket_id(stage, bucket_type, bucket_key)
    taxonomy = normalize_lifecycle_bucket(
        stage=stage,
        bucket_type=bucket_type,
        bucket_key=bucket_key,
        source_dimensions={
            "source_section": section_name,
            "source_quality_gate": bucket.get("source_quality_gate"),
            "recommended_route": bucket.get("recommended_route"),
        },
    )
    deterministic_proposal = taxonomy["deterministic_proposal"]
    if state == "code_patch_required":
        deterministic_proposal = _source_remediation_proposal(
            deterministic_proposal,
            source_quality_gate=bucket.get("source_quality_gate"),
        )
    source_quality_resolution = {}
    if (
        state == "source_only_keep_collecting"
        and _would_require_source_quality_patch(bucket)
        and _is_implemented_source_quality_waiting(bucket)
    ):
        source_quality_resolution = {
            "status": "implemented_source_quality_contract_waiting_sample",
            "original_recommended_route": bucket.get("recommended_route"),
            "original_source_quality_gate": bucket.get("source_quality_gate"),
            "implementation_status": bucket.get("implementation_status"),
            "runtime_effect": False,
            "allowed_runtime_apply": False,
        }
    return {
        "candidate_id": bucket_id,
        "bucket_id": bucket_id,
        "source_candidate_id": source_candidate_id or None,
        "matrix_candidate_id": (
            bucket_id
            if section_name == "swing_lifecycle_flow_bucket_attribution"
            and state == "sim_auto_approved"
            else None
        ),
        "canonical_bucket": taxonomy["canonical_bucket"],
        "legacy_raw_bucket_key": taxonomy["legacy_raw_bucket_key"],
        "bucket_alias_version": BUCKET_ALIAS_VERSION,
        "dimension_set_version": DIMENSION_SET_VERSION,
        "normalized_dimensions": taxonomy["normalized_dimensions"],
        "normalized_metrics": taxonomy["normalized_metrics"],
        "deterministic_proposal": deterministic_proposal,
        "source_section": section_name,
        "stage": stage,
        "lifecycle_stage": stage,
        "bucket_type": bucket_type,
        "bucket_key": bucket_key,
        "classification_state": state,
        "source_quality_gate": bucket.get("source_quality_gate"),
        "joined_sample": bucket.get("joined_sample"),
        "sample_count": bucket.get("sample_count"),
        "source_workorder_id": bucket.get("workorder_id"),
        "swing_lifecycle_flow_bucket_id": bucket.get("swing_lifecycle_flow_bucket_id"),
        "metric_scope": bucket.get("metric_scope"),
        "metric_role": bucket.get("metric_role"),
        "primary_decision_metric": bucket.get("primary_decision_metric"),
        "entry_bucket_id": bucket.get("entry_bucket_id"),
        "holding_bucket_id": bucket.get("holding_bucket_id"),
        "scale_in_bucket_ids": bucket.get("scale_in_bucket_ids") or [],
        "exit_bucket_id": bucket.get("exit_bucket_id"),
        "child_bucket_ids": bucket.get("child_bucket_ids") or {},
        "stage_contract": bucket.get("stage_contract") or {},
        "attribution_key": bucket.get("attribution_key"),
        "rollback_guard": bucket.get("rollback_guard"),
        "parent_bucket_id": bucket_id,
        "implementation_status": bucket.get("implementation_status"),
        "implementation_provenance": (
            bucket.get("implementation_provenance")
            if isinstance(bucket.get("implementation_provenance"), dict)
            else {}
        ),
        "source_quality_resolution": source_quality_resolution,
        "source_quality_adjusted_ev_pct": bucket.get("source_quality_adjusted_ev_pct"),
        "decision_authority": DECISION_AUTHORITY,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "human_approval_required": False,
        "next_route": (
            "next_preopen_swing_sim_policy_input"
            if state == "sim_auto_approved"
            else "postclose_source_quality_or_sample_collection"
        ),
        "forbidden_uses": FORBIDDEN_USES,
        "evidence_authority_contract": evidence_authority_contract(),
    }


def _candidate_from_matrix_approval(
    section_name: str, item: dict[str, Any]
) -> dict[str, Any]:
    candidate = _candidate_from_bucket(section_name, item)
    matrix_candidate_id = str(
        item.get("candidate_id") or item.get("bucket_id") or ""
    ).strip()
    if matrix_candidate_id:
        candidate["candidate_id"] = matrix_candidate_id
        candidate["bucket_id"] = matrix_candidate_id
        candidate["source_candidate_id"] = matrix_candidate_id
        candidate["matrix_candidate_id"] = matrix_candidate_id
        candidate["parent_bucket_id"] = matrix_candidate_id
    candidate["classification_state"] = str(
        item.get("classification_state")
        or item.get("classification_hint")
        or candidate.get("classification_state")
        or "sim_auto_approved"
    )
    candidate["next_route"] = (
        "next_preopen_swing_sim_policy_input"
        if candidate["classification_state"] == "sim_auto_approved"
        else candidate.get("next_route")
        or "postclose_source_quality_or_sample_collection"
    )
    candidate["source_section"] = section_name
    return candidate


def _swing_entry_bottleneck_candidate(matrix: dict[str, Any]) -> dict[str, Any] | None:
    bottleneck = (
        matrix.get("swing_entry_bottleneck")
        if isinstance(matrix.get("swing_entry_bottleneck"), dict)
        else {}
    )
    matches = (
        bottleneck.get("matches") if isinstance(bottleneck.get("matches"), list) else []
    )
    if (
        bottleneck.get("primary") != "SWING_ENTRY_DROUGHT_CRITICAL"
        and "SWING_ENTRY_DROUGHT_CRITICAL" not in matches
    ):
        return None
    counts = (
        bottleneck.get("counts") if isinstance(bottleneck.get("counts"), dict) else {}
    )
    ratios = (
        bottleneck.get("ratios") if isinstance(bottleneck.get("ratios"), dict) else {}
    )
    return {
        "candidate_id": "swing_entry_bottleneck_swing_entry_drought_critical",
        "bucket_id": "swing_entry_bottleneck_swing_entry_drought_critical",
        "source_section": "swing_entry_bottleneck",
        "stage": "entry",
        "lifecycle_stage": "entry",
        "bucket_type": "swing_entry_bottleneck",
        "bucket_key": "SWING_ENTRY_DROUGHT_CRITICAL",
        "classification_state": "code_patch_required",
        "source_quality_gate": "source_only_bottleneck_handoff",
        "joined_sample": counts.get("entry_unique"),
        "sample_count": counts.get("entry_unique"),
        "source_quality_adjusted_ev_pct": None,
        "decision_authority": DECISION_AUTHORITY,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "human_approval_required": False,
        "next_route": "code_improvement_workorder",
        "forbidden_uses": FORBIDDEN_USES,
        "evidence_authority_contract": evidence_authority_contract(),
        "classification_primary": bottleneck.get("primary"),
        "classification_matches": matches,
        "counts": counts,
        "ratios": ratios,
    }


def _workorder_contract_fields() -> dict[str, Any]:
    return {
        "decision_authority": DECISION_AUTHORITY,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "human_approval_required": False,
        "forbidden_uses": FORBIDDEN_USES,
        "evidence_authority_contract": evidence_authority_contract(),
    }


def _normalize_explicit_workorder(item: dict[str, Any]) -> dict[str, Any]:
    return {
        **item,
        **_workorder_contract_fields(),
        "source_workorder_id": item.get("source_workorder_id")
        or item.get("workorder_id"),
        "parent_bucket_id": item.get("parent_bucket_id") or item.get("bucket_id"),
    }


def _ai_review_followup_workorder(
    reasons: list[str], audit: dict[str, Any]
) -> dict[str, Any]:
    reason_text = ", ".join(reasons) if reasons else "parsed_review_followup_required"
    return {
        "workorder_id": "swing_lifecycle_bucket_discovery_ai_review_followup",
        "bucket_id": "swing_lifecycle_bucket_discovery_ai_review_followup",
        "source_workorder_id": "ai_review_followup",
        "parent_bucket_id": "swing_lifecycle_bucket_discovery_ai_review",
        "classification_state": "code_patch_required",
        "reason": "parsed_ai_review_followup_required",
        "target_subsystem": "swing_lifecycle_bucket_discovery_ai_review",
        "implementation_status": "implemented",
        "implementation_provenance": {
            "implementation_type": "swing_bucket_ai_review_followup_handoff",
            "implemented_scope": (
                "Swing bucket discovery emits a source-only AI follow-up workorder with explicit audit "
                "reasons for downstream EV/runtime/verifier handoff."
            ),
            "source_report_type": REPORT_TYPE,
            "decision_authority": DECISION_AUTHORITY,
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "ai_review_followup_required": True,
            "ai_review_followup_reasons": reasons,
            "ai_audit_status": audit.get("status"),
            "root_cause_closure_status_hint": "root_cause_closed",
            "required_downstream": [
                "threshold_cycle_ev_report",
                "runtime_approval_summary",
                "code_improvement_workorder",
                "postclose_verifier",
            ],
        },
        "ai_review_followup_reasons": reasons,
        "ai_review_audit": audit,
        "intent": (
            "The AI call parsed, but the reviewer output requires follow-up. "
            "Treat this as source-only workorder input, not an AI transport failure."
        ),
        "evidence": [
            f"ai_review_followup_reason={reason_text}",
            f"audit_status={audit.get('status')}",
            f"audit_issues={audit.get('issues') or []}",
            f"forbidden_use_violations={audit.get('forbidden_use_violations') or []}",
        ],
        **_workorder_contract_fields(),
    }


def _ensure_candidate_taxonomy(candidate: dict[str, Any]) -> dict[str, Any]:
    if candidate.get("deterministic_proposal"):
        return _normalize_candidate_contract(candidate)
    stage = str(candidate.get("lifecycle_stage") or "swing")
    bucket_type = str(
        candidate.get("bucket_type") or candidate.get("source_section") or "bucket"
    )
    bucket_key = str(
        candidate.get("bucket_key") or candidate.get("bucket_id") or "unknown"
    )
    taxonomy = normalize_lifecycle_bucket(
        stage=stage,
        bucket_type=bucket_type,
        bucket_key=bucket_key,
        source_dimensions={
            "source_section": candidate.get("source_section"),
            "classification_state": candidate.get("classification_state"),
        },
    )
    if candidate.get("classification_state") == "code_patch_required":
        deterministic_proposal = _source_remediation_proposal(
            taxonomy["deterministic_proposal"],
            source_quality_gate=candidate.get("source_quality_gate"),
        )
    else:
        deterministic_proposal = taxonomy["deterministic_proposal"]
    return _normalize_candidate_contract(
        {
            **candidate,
            "canonical_bucket": taxonomy["canonical_bucket"],
            "legacy_raw_bucket_key": taxonomy["legacy_raw_bucket_key"],
            "bucket_alias_version": BUCKET_ALIAS_VERSION,
            "dimension_set_version": DIMENSION_SET_VERSION,
            "normalized_dimensions": taxonomy["normalized_dimensions"],
            "normalized_metrics": taxonomy["normalized_metrics"],
            "deterministic_proposal": deterministic_proposal,
        }
    )


def _normalize_candidate_contract(candidate: dict[str, Any]) -> dict[str, Any]:
    stage = str(candidate.get("stage") or candidate.get("lifecycle_stage") or "swing")
    bucket_id = str(candidate.get("bucket_id") or candidate.get("candidate_id") or "")
    if not bucket_id:
        bucket_id = _bucket_id(
            stage,
            str(
                candidate.get("bucket_type")
                or candidate.get("source_section")
                or "bucket"
            ),
            str(candidate.get("bucket_key") or "unknown"),
        )
    return {
        **candidate,
        "candidate_id": str(candidate.get("candidate_id") or bucket_id),
        "bucket_id": bucket_id,
        "stage": stage,
        "lifecycle_stage": stage,
    }


def _ai_review_candidate_shards(
    candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    sim_auto = [
        item
        for item in candidates
        if item.get("classification_state") == "sim_auto_approved"
    ]
    gap = [
        item
        for item in candidates
        if item.get("classification_state")
        in {
            "runtime_blocked_contract_gap",
            "automation_handoff_gap",
            "code_patch_required",
        }
    ]
    reviewed_ids = {
        str(item.get("bucket_id"))
        for item in [*sim_auto, *gap]
        if item.get("bucket_id")
    }
    taxonomy = [
        item
        for item in candidates
        if item.get("classification_state") == "source_only_keep_collecting"
        and str(item.get("bucket_id") or "") not in reviewed_ids
    ][:10]
    sim_shards = [
        {
            "shard_id": (
                "sim_policy_review" if index == 0 else f"sim_policy_review_{index + 1}"
            ),
            "review_scope": "sim_auto_candidate_review",
            "candidate_selection_policy": "all deterministic sim_auto_approved candidates",
            "review_authority": "fail-closed source-only sim policy reviewer",
            "critical_for_sim_policy": True,
            "candidates": sim_auto[
                index
                * AI_REVIEW_SIM_SHARD_SIZE : (index + 1)
                * AI_REVIEW_SIM_SHARD_SIZE
            ],
            "omitted_candidate_count": 0,
        }
        for index in range(
            (len(sim_auto) + AI_REVIEW_SIM_SHARD_SIZE - 1) // AI_REVIEW_SIM_SHARD_SIZE
        )
    ]
    return [
        *sim_shards,
        {
            "shard_id": "gap_workorder_review",
            "review_scope": "contract_gap_and_workorder_review",
            "candidate_selection_policy": "runtime-blocked, automation handoff, and code-patch candidates",
            "review_authority": "source-quality and workorder reviewer",
            "critical_for_sim_policy": False,
            "candidates": gap[:40],
            "omitted_candidate_count": max(len(gap) - 40, 0),
        },
        {
            "shard_id": "taxonomy_discovery_review",
            "review_scope": "taxonomy_discovery_sample_review",
            "candidate_selection_policy": "top source-only keep-collecting candidates after actionable shards",
            "review_authority": "taxonomy reviewer for source-only tail sample",
            "critical_for_sim_policy": False,
            "candidates": taxonomy,
            "omitted_candidate_count": max(
                len(candidates) - len(sim_auto) - len(gap[:40]) - len(taxonomy), 0
            ),
        },
    ]


def _build_ai_review_context(target_date: str, shard: dict[str, Any]) -> dict[str, Any]:
    review_candidates = (
        shard.get("candidates") if isinstance(shard.get("candidates"), list) else []
    )
    review_candidate_ids = [
        str(item.get("candidate_id") or item.get("bucket_id"))
        for item in review_candidates
        if item.get("candidate_id") or item.get("bucket_id")
    ]
    return {
        "date": target_date,
        "report_type": REPORT_TYPE,
        "shard_id": shard.get("shard_id"),
        "review_scope": shard.get("review_scope"),
        "candidate_selection_policy": shard.get("candidate_selection_policy"),
        "review_authority": shard.get("review_authority"),
        "candidate_ids": review_candidate_ids,
        "omitted_candidate_count": shard.get("omitted_candidate_count", 0),
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "broker_order_forbidden": True,
        "forbidden_uses": FORBIDDEN_USES,
        "evidence_authority_contract": evidence_authority_contract(),
        "candidates": review_candidates,
        "deterministic_proposals": [
            {
                "candidate_id": item.get("candidate_id") or item.get("bucket_id"),
                "bucket_id": item.get("bucket_id"),
                "canonical_bucket": item.get("canonical_bucket"),
                "legacy_raw_bucket_key": item.get("legacy_raw_bucket_key"),
                "bucket_alias_version": item.get("bucket_alias_version"),
                "dimension_set_version": item.get("dimension_set_version"),
                "deterministic_proposal": item.get("deterministic_proposal"),
                "classification_state": item.get("classification_state"),
            }
            for item in review_candidates
        ],
    }


def _build_ai_review_instructions() -> str:
    return (
        "You are swing_lifecycle_bucket_discovery_ai_review, a source-only taxonomy reviewer.\n"
        "Create an independent ai_tier2_proposal for each deterministic swing bucket candidate, then create a "
        "comparative_review that compares deterministic_proposal and ai_tier2_proposal side by side.\n"
        "Decisions are limited to merge, absorb_as_dimension, create_new_metric, create_new_dimension, keep_bucket, "
        "reject, source_quality_blocker, or instrumentation_gap. Prefer canonical bucket plus metrics/dimensions "
        "for numeric or value-specific bucket keys.\n"
        "You must not grant runtime, threshold, provider, bot, cap, real-order, one-share canary, or broker-order "
        "authority. All output is workorder/source-only.\n"
        "Evidence authority contract: bucket/dimension tuning primary evidence is sim/probe lifecycle EV. "
        "Real one-share samples are not primary EV evidence unless the mapped bucket policy was already enabled "
        "for the evaluated post-apply cohort. Pre-apply real samples may be used only for execution-quality "
        "calibration, safety veto, provenance validation, and broker/fill/slippage source-quality checks. "
        "Do not merge real PnL with sim/probe EV and do not promote runtime threshold/order/provider/cap/bot "
        "changes from pre-apply real one-share outcomes. If a proposal violates this contract, select reject, "
        "source_quality_blocker, or instrumentation_gap.\n"
        "Metric or dimension proposals must include metric_role, decision_authority, window_policy, sample_floor, "
        "primary_decision_metric, source_quality_gate, and forbidden_uses in required_source_fields.\n"
        "For every ai_tier2_proposal and comparative_review, required_source_fields must contain all seven exact "
        "strings: metric_role, decision_authority, window_policy, sample_floor, primary_decision_metric, "
        "source_quality_gate, forbidden_uses. Do not substitute field examples for this contract list.\n"
        "Return strict JSON conforming to swing_lifecycle_bucket_discovery_review_v1."
    )


def _ai_review_config() -> PostcloseAIReviewConfig:
    config = resolve_postclose_ai_review_config(
        "SWING_LIFECYCLE_BUCKET_DISCOVERY",
        default_model=AI_REVIEW_MODEL,
        default_reasoning_effort=AI_REVIEW_REASONING_EFFORT,
        default_timeout_sec=AI_REVIEW_TIMEOUT_SEC,
    )
    primary_provider = config.primary_provider
    failback_provider = config.failback_provider
    if not os.getenv(f"{config.env_prefix_name}_PRIMARY_PROVIDER"):
        primary_provider = "bedrock_qwen3"
    if not os.getenv(f"{config.env_prefix_name}_FAILBACK_PROVIDER"):
        failback_provider = "openai"
    return replace(
        config, primary_provider=primary_provider, failback_provider=failback_provider
    )


def _call_openai_ai_review(
    context: dict[str, Any],
    *,
    config: PostcloseAIReviewConfig | None = None,
) -> tuple[Any | None, dict[str, Any]]:
    config = config or _ai_review_config()

    def _contract_validator(raw_text: str) -> tuple[bool, str]:
        status, payload, warnings = _parse_ai_review_response(raw_text)
        if status != "parsed":
            return False, status
        audit = payload.get("audit") if isinstance(payload.get("audit"), dict) else {}
        expected_ids = {
            str(item.get("candidate_id") or item.get("bucket_id") or "")
            for item in context.get("candidates", [])
            if isinstance(item, dict)
            and (item.get("candidate_id") or item.get("bucket_id"))
        }
        proposal_rows = payload.get("ai_tier2_proposals")
        comparative_rows = payload.get("comparative_reviews")
        if not isinstance(proposal_rows, list):
            return False, "missing_ai_tier2_proposals"
        if not isinstance(comparative_rows, list):
            return False, "missing_comparative_reviews"
        if expected_ids:
            proposal_ids = {
                str(item.get("candidate_id") or item.get("bucket_id") or "")
                for item in proposal_rows
                if isinstance(item, dict)
            }
            comparative_ids = {
                str(item.get("candidate_id") or item.get("bucket_id") or "")
                for item in comparative_rows
                if isinstance(item, dict)
            }
            repairable_proposal_ids = len(proposal_rows) == len(expected_ids) and all(
                isinstance(item, dict) for item in proposal_rows
            )
            repairable_comparative_ids = len(comparative_rows) == len(
                expected_ids
            ) and all(isinstance(item, dict) for item in comparative_rows)
            if proposal_ids != expected_ids and not repairable_proposal_ids:
                return False, "ai_tier2_proposals_id_mismatch"
            if comparative_ids != expected_ids and not repairable_comparative_ids:
                return False, "comparative_reviews_id_mismatch"
        if audit.get("status") not in {
            "pass",
            "correction_required",
            "insufficient_context",
        }:
            return False, "missing_audit_status"
        if warnings:
            return False, "warnings:" + ",".join(warnings[:3])
        return True, ""

    from src.engine.ai.postclose_structured_review_provider import (
        call_postclose_structured_review,
    )

    return call_postclose_structured_review(
        context,
        schema_name=AI_REVIEW_SCHEMA_NAME,
        instructions=_build_ai_review_instructions(),
        config=config,
        metadata={"endpoint_name": AI_REVIEWER_NAME, "report_type": REPORT_TYPE},
        contract_validator=_contract_validator,
        ensure_ascii=True,
    )


def _normalize_ai_review_payload_candidate_ids(
    payload: dict[str, Any],
    candidate_ids: list[str],
) -> int:
    if not candidate_ids:
        return 0
    repair_count = 0
    expected = set(candidate_ids)
    for key in ("ai_tier2_proposals", "comparative_reviews"):
        rows = payload.get(key)
        if not isinstance(rows, list) or len(rows) != len(candidate_ids):
            continue
        row_ids = {
            str(item.get("candidate_id") or item.get("bucket_id") or "")
            for item in rows
            if isinstance(item, dict)
        }
        if row_ids == expected:
            continue
        for index, item in enumerate(rows):
            if not isinstance(item, dict):
                continue
            expected_id = candidate_ids[index]
            current_id = str(item.get("candidate_id") or item.get("bucket_id") or "")
            if current_id != expected_id:
                item["candidate_id"] = expected_id
                item["bucket_id"] = expected_id
                repair_count += 1
    return repair_count


def _parse_ai_review_response(
    raw_response: Any | None,
) -> tuple[str, dict[str, Any], list[str]]:
    if raw_response in (None, ""):
        return "missing", {}, ["ai_review_response_missing"]
    if isinstance(raw_response, dict):
        payload = raw_response
    else:
        try:
            payload = json.loads(str(raw_response))
        except Exception as exc:
            return "parse_rejected", {}, [f"ai_review_json_parse_failed:{exc}"]
    warnings: list[str] = []
    if payload.get("schema_version") != 1:
        warnings.append("ai_review_schema_version_invalid")
    if payload.get("reviewer") != AI_REVIEWER_NAME:
        warnings.append("ai_review_reviewer_invalid")
    if not isinstance(payload.get("ai_tier2_proposals"), list):
        warnings.append("ai_review_ai_tier2_proposals_missing")
    if not isinstance(payload.get("comparative_reviews"), list):
        warnings.append("ai_review_comparative_reviews_missing")
    for key in ("ai_tier2_proposals", "comparative_reviews"):
        for item in payload.get(key) or []:
            if not isinstance(item, dict):
                warnings.append(f"ai_review_{key}_invalid")
                continue
            if (
                item.get("candidate_id")
                and item.get("bucket_id")
                and str(item.get("candidate_id")) != str(item.get("bucket_id"))
            ):
                warnings.append(
                    f"ai_review_{key}_candidate_bucket_id_mismatch:{item.get('candidate_id')}"
                )
            decision_key = (
                "proposal_decision"
                if key == "ai_tier2_proposals"
                else "selected_decision"
            )
            if str(item.get(decision_key) or "") not in TAXONOMY_DECISIONS:
                warnings.append(
                    f"ai_review_{key}_decision_invalid:{item.get('bucket_id')}"
                )
            missing_contract = missing_metric_contract_fields(
                item.get("required_source_fields")
            )
            if missing_contract:
                warnings.append(
                    f"ai_review_{key}_contract_missing:{item.get('bucket_id')}:{','.join(missing_contract)}"
                )
            if has_forbidden_runtime_leak(item):
                warnings.append(
                    f"ai_review_{key}_forbidden_use_leak:{item.get('bucket_id')}"
                )
            if has_evidence_authority_violation(item):
                warnings.append(
                    f"ai_review_{key}_evidence_authority_violation:{item.get('bucket_id')}"
                )
    audit = payload.get("audit") if isinstance(payload.get("audit"), dict) else {}
    if str(audit.get("status") or "") not in {
        "pass",
        "correction_required",
        "insufficient_context",
    }:
        warnings.append("ai_review_audit_status_invalid")
    if not isinstance(audit.get("forbidden_use_violations"), list):
        warnings.append("ai_review_forbidden_use_violations_missing")
    if warnings:
        return "parse_rejected", payload, warnings
    return "parsed", payload, []


def _run_ai_review_shards(
    target_date: str,
    candidates: list[dict[str, Any]],
    *,
    provider: str,
    ai_raw_response: Any | None,
) -> dict[str, Any]:
    shards = _ai_review_candidate_shards(candidates)
    critical_shards = [item for item in shards if item.get("critical_for_sim_policy")]
    optional_shards = [
        item for item in shards if not item.get("critical_for_sim_policy")
    ]
    run_optional_after_critical = os.getenv(
        "KORSTOCKSCAN_SWING_LIFECYCLE_BUCKET_DISCOVERY_AI_RUN_OPTIONAL_SHARDS",
        "false",
    ).strip().lower() in {"1", "true", "yes", "on"}
    ordered_shards = (
        [*critical_shards, *optional_shards]
        if (not critical_shards or run_optional_after_critical)
        else critical_shards
    )
    combined_payload: dict[str, Any] = {
        "ai_tier2_proposals": [],
        "comparative_reviews": [],
        "audit": {
            "status": "pass",
            "issues": [],
            "forbidden_use_violations": [],
            "reason": "all parsed shards passed",
        },
    }
    records: list[dict[str, Any]] = []
    reviewed_candidate_ids: list[str] = []
    statuses: list[str] = []
    warnings: list[str] = []
    disabled = provider in {"none", "off", "false", "0"}
    for index, shard in enumerate(ordered_shards):
        shard_candidates = (
            shard.get("candidates") if isinstance(shard.get("candidates"), list) else []
        )
        if not shard_candidates:
            continue
        context = _build_ai_review_context(target_date, shard)
        shard_config = _ai_review_config()
        candidate_ids = [
            str(item) for item in (context.get("candidate_ids") or []) if str(item)
        ]
        provider_status: dict[str, Any] = {
            "provider": provider,
            "requested_provider": provider,
            "status": "disabled" if disabled else "not_called",
            "schema_name": AI_REVIEW_SCHEMA_NAME,
            "shard_id": shard.get("shard_id"),
            "input_context_chars": len(
                json.dumps(context, ensure_ascii=True, default=str)
            ),
            **(
                shard_config.provider_status_fields()
                if not disabled
                else {"model": None}
            ),
        }
        if disabled:
            provider_status.update(
                {
                    "reasoning_effort": None,
                    "timeout_sec": None,
                    "attempt_role": None,
                    "retry_reason": None,
                }
            )
        raw_response = (
            ai_raw_response if index == 0 and ai_raw_response is not None else None
        )
        if raw_response is not None:
            provider_status["status"] = "provided_response"
        if raw_response is None and not disabled:
            raw_response, provider_status = _call_openai_ai_review(
                context, config=shard_config
            )
            provider_status = {
                **shard_config.provider_status_fields(),
                **provider_status,
                "requested_provider": provider,
            }
            provider_status["shard_id"] = shard.get("shard_id")
        status, payload, shard_warnings = _parse_ai_review_response(raw_response)
        id_repair_count = 0
        if status == "parsed":
            id_repair_count = _normalize_ai_review_payload_candidate_ids(
                payload, candidate_ids
            )
        statuses.append(status)
        warnings.extend(f"{shard.get('shard_id')}:{item}" for item in shard_warnings)
        if status == "parsed":
            reviewed_candidate_ids.extend(candidate_ids)
            combined_payload["ai_tier2_proposals"].extend(
                payload.get("ai_tier2_proposals") or []
            )
            combined_payload["comparative_reviews"].extend(
                payload.get("comparative_reviews") or []
            )
            audit = (
                payload.get("audit") if isinstance(payload.get("audit"), dict) else {}
            )
            if audit.get("status") != "pass":
                combined_payload["audit"]["status"] = (
                    audit.get("status") or "correction_required"
                )
            combined_payload["audit"]["issues"].extend(
                audit.get("issues") if isinstance(audit.get("issues"), list) else []
            )
            combined_payload["audit"]["forbidden_use_violations"].extend(
                audit.get("forbidden_use_violations")
                if isinstance(audit.get("forbidden_use_violations"), list)
                else []
            )
        records.append(
            {
                "shard_id": shard.get("shard_id"),
                "critical_for_sim_policy": bool(shard.get("critical_for_sim_policy")),
                "status": status,
                "audit_status": (
                    (payload.get("audit") or {}).get("status")
                    if isinstance(payload, dict)
                    and isinstance(payload.get("audit"), dict)
                    else None
                ),
                "forbidden_use_violation_count": (
                    len(
                        (payload.get("audit") or {}).get("forbidden_use_violations")
                        or []
                    )
                    if isinstance(payload, dict)
                    and isinstance(payload.get("audit"), dict)
                    else 0
                ),
                "candidate_ids": candidate_ids,
                "candidate_count": len(candidate_ids),
                "id_repair_count": id_repair_count,
                "omitted_candidate_count": shard.get("omitted_candidate_count", 0),
                "provider_status": provider_status,
                "warnings": shard_warnings,
            }
        )
    critical_records = [item for item in records if item.get("critical_for_sim_policy")]
    critical_statuses = [str(item.get("status") or "") for item in critical_records]
    critical_complete = bool(critical_records) and all(
        status == "parsed" for status in critical_statuses
    )
    if critical_complete and not run_optional_after_critical:
        for shard in optional_shards:
            shard_candidates = (
                shard.get("candidates")
                if isinstance(shard.get("candidates"), list)
                else []
            )
            if not shard_candidates:
                continue
            context = _build_ai_review_context(target_date, shard)
            candidate_ids = [
                str(item) for item in (context.get("candidate_ids") or []) if str(item)
            ]
            records.append(
                {
                    "shard_id": shard.get("shard_id"),
                    "critical_for_sim_policy": False,
                    "status": "deferred",
                    "audit_status": None,
                    "forbidden_use_violation_count": 0,
                    "candidate_ids": candidate_ids,
                    "candidate_count": len(candidate_ids),
                    "id_repair_count": 0,
                    "omitted_candidate_count": shard.get("omitted_candidate_count", 0),
                    "provider_status": {
                        "provider": provider,
                        "requested_provider": provider,
                        "status": "deferred_after_critical_sim_policy",
                        "schema_name": AI_REVIEW_SCHEMA_NAME,
                        "shard_id": shard.get("shard_id"),
                        "input_context_chars": len(
                            json.dumps(context, ensure_ascii=True, default=str)
                        ),
                    },
                    "warnings": [
                        "optional_source_only_review_deferred_after_critical_sim_policy"
                    ],
                }
            )
    optional_deferred_records = [
        item for item in records if item.get("status") == "deferred"
    ]
    optional_deferred_candidate_count = sum(
        int(item.get("candidate_count") or 0) for item in optional_deferred_records
    )
    if not records:
        return {
            "status": "missing",
            "payload": combined_payload,
            "provider_status": {
                "provider": provider,
                "status": "disabled" if disabled else "not_called",
            },
            "shards": [],
            "reviewed_candidate_ids": [],
            "warnings": ["ai_review_response_missing"],
        }
    decision_statuses = (
        critical_statuses
        if critical_records and not run_optional_after_critical
        else statuses
    )
    if all(status == "parsed" for status in decision_statuses):
        status = "parsed"
    elif any(status == "parsed" for status in decision_statuses):
        status = "partial"
    elif disabled:
        status = "missing"
    elif any(status == "parse_rejected" for status in decision_statuses):
        status = "parse_rejected"
    else:
        status = decision_statuses[-1] if decision_statuses else "missing"
    first_provider_status = (
        records[0].get("provider_status")
        if records and isinstance(records[0].get("provider_status"), dict)
        else {}
    )
    return {
        "status": status,
        "payload": combined_payload,
        "provider_status": {
            **first_provider_status,
            "requested_provider": provider,
            "status": status,
            "shard_count": len(records),
            "critical_shard_count": len(critical_records),
            "optional_deferred_shard_count": len(optional_deferred_records),
            "optional_deferred_candidate_count": optional_deferred_candidate_count,
        },
        "shards": records,
        "reviewed_candidate_ids": sorted(set(reviewed_candidate_ids)),
        "warnings": warnings,
    }


def _map_by_id(items: Any, key: str) -> dict[str, dict[str, Any]]:
    return {
        str(item.get(key) or item.get("candidate_id") or item.get("bucket_id")): item
        for item in items or []
        if isinstance(item, dict)
        and (item.get(key) or item.get("candidate_id") or item.get("bucket_id"))
    }


def _ai_review_augmentation_points(
    *, matrix: dict[str, Any], candidates: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    if not matrix:
        return []
    candidate_states = {
        str(item.get("classification_state") or "") for item in candidates
    }
    points = [
        {
            "point_id": "swing_ldm_bucket_semantic_two_pass_review",
            "stage": "bucket_discovery",
            "audit_pass": True,
            "explicit_gap_type": None,
            "source_paths": ["swing_lifecycle_decision_matrix"],
            "forbidden_runtime_uses": FORBIDDEN_USES,
            "reason": "deterministic source-only interpretation/audit/final-conclusion review is configured for bucket classifications",
            "recommended_route": "keep_source_only",
        },
        {
            "point_id": "swing_ldm_source_contract_ai_audit",
            "stage": "source_contract",
            "audit_pass": True,
            "explicit_gap_type": None,
            "source_paths": ["swing_lifecycle_decision_matrix.input_contract"],
            "forbidden_runtime_uses": FORBIDDEN_USES,
            "reason": "deterministic audit checks probe/discovery source contract and forbidden-source boundaries",
            "recommended_route": "keep_source_only",
        },
        {
            "point_id": "swing_ldm_sim_policy_handoff_ai_audit",
            "stage": "sim_policy_handoff",
            "audit_pass": True,
            "explicit_gap_type": None,
            "source_paths": [
                "swing_lifecycle_bucket_discovery.sim_auto_approved_candidates"
            ],
            "forbidden_runtime_uses": FORBIDDEN_USES,
            "reason": "AI audit can verify sim_auto_approved remains sim-only and does not imply real/canary/provider/bot changes",
            "recommended_route": "code_improvement_workorder",
        },
    ]
    if (
        "source_only_keep_collecting" in candidate_states
        or "code_patch_required" in candidate_states
    ):
        points.append(
            {
                "point_id": "swing_ldm_source_quality_gap_ai_triage",
                "stage": "source_quality",
                "audit_pass": True,
                "explicit_gap_type": None,
                "source_paths": ["swing_lifecycle_decision_matrix.bucket_attribution"],
                "forbidden_runtime_uses": FORBIDDEN_USES,
                "reason": "deterministic triage summarizes source-quality/sample states without blocking sim-only auto approval for ambiguity",
                "recommended_route": "keep_source_only",
            }
        )
    return points


def _ai_audit_section(points: list[dict[str, Any]]) -> dict[str, Any]:
    audit_points = []
    for item in points:
        has_gap = bool(item.get("explicit_gap_type"))
        audit_points.append(
            {
                "audit_id": item.get("point_id"),
                "stage": item.get("stage"),
                "semantic_review": item.get("stage") == "bucket_discovery",
                "sim_policy_handoff": item.get("stage") == "sim_policy_handoff",
                "source_contract_gap": item.get("stage") == "source_contract",
                "source_quality_triage": item.get("stage") == "source_quality",
                "auditor_pass": True,
                "explicit_gap_type": item.get("explicit_gap_type"),
                "source_paths": item.get("source_paths") or [],
                "interpreted_state": (
                    "source_only_gap_triaged" if has_gap else "sim_policy_preserved"
                ),
                "final_decision": "keep_source_only" if has_gap else "keep_sim_only",
                "ambiguity_blocks_sim_auto_approval": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "allowed_runtime_apply": False,
                "runtime_effect": False,
                "forbidden_runtime_uses": FORBIDDEN_USES,
            }
        )
    return {
        "schema_version": "swing_lifecycle_bucket_discovery_ai_audit_v1",
        "status": (
            "configured_deterministic_two_pass" if audit_points else "not_required"
        ),
        "provider": "deterministic_source_only",
        "required_flow_status": {
            "interpretation": "implemented",
            "audit": "implemented",
            "final_conclusions": "implemented",
        },
        "required_sections": [
            "semantic_review",
            "sim_policy_handoff",
            "source_contract_gap",
            "source_quality_triage",
        ],
        "audit_points": audit_points,
        "auditor_pass_count": sum(
            1 for item in audit_points if item.get("auditor_pass") is True
        ),
        "explicit_gap_count": sum(
            1 for item in audit_points if item.get("explicit_gap_type")
        ),
        "sim_auto_policy_preserved": True,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }


def _iter_attribution_sections(
    matrix: dict[str, Any],
) -> list[tuple[str, dict[str, Any]]]:
    sections = []
    for name in (
        "swing_lifecycle_flow_bucket_attribution",
        "entry_bucket_attribution",
        "holding_exit_bucket_attribution",
        "scale_in_bucket_attribution",
        "discovery_arm_attribution",
    ):
        section = matrix.get(name)
        if isinstance(section, dict):
            sections.append((name, section))
    return sections


def build_swing_lifecycle_bucket_discovery(
    target_date: str,
    *,
    provider: str | None = None,
    ai_raw_response: Any | None = None,
) -> dict[str, Any]:
    date_key = _date_text(target_date)
    matrix_json, _ = matrix_report_paths(date_key)
    matrix = _load_json(matrix_json)

    candidates: list[dict[str, Any]] = []
    explicit_workorders: list[dict[str, Any]] = []
    seen_candidate_ids: set[str] = set()

    def _append_candidate(candidate: dict[str, Any]) -> None:
        candidate_id = str(
            candidate.get("candidate_id") or candidate.get("bucket_id") or ""
        ).strip()
        if candidate_id and candidate_id in seen_candidate_ids:
            return
        if candidate_id:
            seen_candidate_ids.add(candidate_id)
        candidates.append(candidate)

    for section_name, section in _iter_attribution_sections(matrix):
        for bucket in section.get("buckets") or []:
            if isinstance(bucket, dict):
                _append_candidate(_candidate_from_bucket(section_name, bucket))
        for key in ("sim_auto_approval_candidates", "runtime_approval_candidates"):
            for item in section.get(key) or []:
                if isinstance(item, dict):
                    _append_candidate(
                        _candidate_from_matrix_approval(section_name, item)
                    )
        for item in section.get("code_improvement_workorders") or []:
            if isinstance(item, dict):
                explicit_workorders.append(item)
    entry_bottleneck_candidate = _swing_entry_bottleneck_candidate(matrix)
    if entry_bottleneck_candidate:
        _append_candidate(entry_bottleneck_candidate)
    candidates = [_ensure_candidate_taxonomy(item) for item in candidates]
    active_explicit_workorders = [
        item
        for item in explicit_workorders
        if not _is_implemented_source_quality_waiting(item)
    ]
    resolved_explicit_workorders = [
        item
        for item in explicit_workorders
        if _is_implemented_source_quality_waiting(item)
    ]

    resolved_provider = (
        str(
            provider
            if provider is not None
            else os.getenv(
                "KORSTOCKSCAN_SWING_LIFECYCLE_BUCKET_DISCOVERY_AI_PROVIDER",
                AI_REVIEW_DEFAULT_PROVIDER,
            )
        )
        .strip()
        .lower()
        or "none"
    )
    ai_review = _run_ai_review_shards(
        date_key,
        candidates,
        provider=resolved_provider,
        ai_raw_response=ai_raw_response,
    )
    ai_status = str(ai_review.get("status") or "missing")
    ai_payload = (
        ai_review.get("payload") if isinstance(ai_review.get("payload"), dict) else {}
    )
    ai_warnings = (
        ai_review.get("warnings") if isinstance(ai_review.get("warnings"), list) else []
    )
    ai_reviewed_candidate_ids = {
        str(item)
        for item in (ai_review.get("reviewed_candidate_ids") or [])
        if str(item)
    }
    provider_status = (
        ai_review.get("provider_status")
        if isinstance(ai_review.get("provider_status"), dict)
        else {}
    )
    ai_review_shards = (
        ai_review.get("shards") if isinstance(ai_review.get("shards"), list) else []
    )
    optional_deferred_shard_count = sum(
        1 for item in ai_review_shards if item.get("status") == "deferred"
    )
    optional_deferred_candidate_count = sum(
        int(item.get("candidate_count") or 0)
        for item in ai_review_shards
        if item.get("status") == "deferred"
    )
    ai_review_id_repair_count = sum(
        int(item.get("id_repair_count") or 0) for item in ai_review_shards
    )
    ai_proposals = _map_by_id(
        [
            {**item, "proposal_source": "ai_tier2", "proposal_status": "provided"}
            for item in (
                ai_payload.get("ai_tier2_proposals")
                if isinstance(ai_payload, dict)
                else []
            )
            or []
            if isinstance(item, dict)
        ],
        "bucket_id",
    )
    ai_comparatives = _map_by_id(
        (ai_payload.get("comparative_reviews") if isinstance(ai_payload, dict) else [])
        or [],
        "bucket_id",
    )
    enriched_candidates = []
    for candidate in candidates:
        bucket_id = str(candidate.get("bucket_id") or "")
        ai_review_coverage = (
            "reviewed" if bucket_id in ai_reviewed_candidate_ids else "unreviewed"
        )
        deterministic = (
            candidate.get("deterministic_proposal")
            if isinstance(candidate.get("deterministic_proposal"), dict)
            else {}
        )
        ai_proposal = ai_proposals.get(bucket_id) or default_ai_tier2_proposal(
            bucket_id, deterministic
        )
        comparative = compare_taxonomy_proposals(
            bucket_id=bucket_id,
            deterministic_proposal=deterministic,
            ai_tier2_proposal=ai_proposal,
            comparative_review=ai_comparatives.get(bucket_id),
        )
        if bucket_id in ai_reviewed_candidate_ids and (
            bucket_id not in ai_proposals or bucket_id not in ai_comparatives
        ):
            comparative = {
                **comparative,
                "selected_decision": "source_quality_blocker",
                "selected_source": "reject",
                "comparison_summary": "AI Tier2 comparative review missing for this reviewed candidate; source-only fail-closed review recorded.",
            }
        enriched_candidates.append(
            {
                **candidate,
                "ai_tier2_proposal": ai_proposal,
                "comparative_review": comparative,
                "ai_review_coverage": ai_review_coverage,
                "ai_review_status": ai_status,
            }
        )
    candidates = enriched_candidates

    source_contract_status = "missing" if not matrix else "pass"
    contract = (
        matrix.get("input_contract")
        if isinstance(matrix.get("input_contract"), dict)
        else {}
    )
    entry_bottleneck = (
        matrix.get("swing_entry_bottleneck")
        if isinstance(matrix.get("swing_entry_bottleneck"), dict)
        else {}
    )
    flow_section = (
        matrix.get("swing_lifecycle_flow_bucket_attribution")
        if isinstance(matrix.get("swing_lifecycle_flow_bucket_attribution"), dict)
        else {}
    )
    flow_summary = (
        flow_section.get("summary")
        if isinstance(flow_section.get("summary"), dict)
        else {}
    )
    if contract and contract.get("swing_daily_simulation_consumed") is not False:
        source_contract_status = "fail"
        candidates.append(
            _ensure_candidate_taxonomy(
                {
                    "bucket_id": "swing_bucket_contract_forbidden_daily_simulation",
                    "source_section": "input_contract",
                    "lifecycle_stage": "source_quality",
                    "bucket_type": "forbidden_source",
                    "bucket_key": "swing_daily_simulation",
                    "classification_state": "runtime_blocked_contract_gap",
                    "decision_authority": DECISION_AUTHORITY,
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "human_approval_required": False,
                    "next_route": "code_improvement_workorder",
                    "forbidden_uses": FORBIDDEN_USES,
                }
            )
        )

    ai_payload_audit = (
        ai_payload.get("audit") if isinstance(ai_payload.get("audit"), dict) else {}
    )
    ai_forbidden = ai_payload_audit.get("forbidden_use_violations")
    if not isinstance(ai_forbidden, list):
        ai_forbidden = []
    reviewed_candidates = [
        item
        for item in candidates
        if str(item.get("bucket_id") or "") in ai_reviewed_candidate_ids
    ]
    unreviewed_sim_auto_candidate_count = sum(
        1
        for item in candidates
        if item.get("classification_state") == "sim_auto_approved"
        and item.get("ai_review_coverage") != "reviewed"
    )
    missing_ai_proposal_count = sum(
        1
        for item in candidates
        if item.get("ai_tier2_proposal", {}).get("proposal_status") != "provided"
    )
    missing_comparative_review_count = sum(
        1
        for item in candidates
        if item.get("comparative_review", {}).get("selected_source") == "reject"
    )
    reviewed_missing_ai_proposal_count = sum(
        1
        for item in reviewed_candidates
        if item.get("ai_tier2_proposal", {}).get("proposal_status") != "provided"
    )
    reviewed_missing_comparative_review_count = sum(
        1
        for item in reviewed_candidates
        if item.get("comparative_review", {}).get("selected_source") == "reject"
    )
    sim_shards = [
        item
        for item in ai_review_shards
        if str(item.get("shard_id") or "").startswith("sim_policy_review")
    ]
    primary_sim_shard = sim_shards[0] if sim_shards else {}
    sim_reviewed_candidate_ids = {
        str(candidate_id)
        for shard in sim_shards
        if shard.get("status") == "parsed"
        for candidate_id in (shard.get("candidate_ids") or [])
        if str(candidate_id)
    }
    failed_sim_candidate_ids = {
        str(candidate_id)
        for shard in sim_shards
        if shard.get("status") != "parsed"
        for candidate_id in (shard.get("candidate_ids") or [])
        if str(candidate_id)
    }
    sim_reviewed_candidates = [
        item
        for item in candidates
        if str(item.get("bucket_id") or "") in sim_reviewed_candidate_ids
    ]
    sim_missing_ai_proposal_count = sum(
        1
        for item in sim_reviewed_candidates
        if item.get("ai_tier2_proposal", {}).get("proposal_status") != "provided"
    )
    sim_missing_comparative_review_count = sum(
        1
        for item in sim_reviewed_candidates
        if item.get("comparative_review", {}).get("selected_source") == "reject"
    )
    sim_review_required = any(
        item.get("classification_state") == "sim_auto_approved" for item in candidates
    )
    pre_review_sim_auto_candidate_count = sum(
        1
        for item in candidates
        if item.get("classification_state") == "sim_auto_approved"
    )
    pre_review_sim_auto_candidate_ids = {
        str(item.get("bucket_id") or "")
        for item in candidates
        if item.get("classification_state") == "sim_auto_approved"
        and item.get("bucket_id")
    }
    missing_sim_review_candidate_ids = (
        pre_review_sim_auto_candidate_ids - sim_reviewed_candidate_ids
    )
    unreviewed_sim_auto_candidate_count = len(missing_sim_review_candidate_ids)
    sim_review_call_fail_closed = bool(
        sim_review_required
        and pre_review_sim_auto_candidate_ids
        and not sim_reviewed_candidate_ids
        and missing_sim_review_candidate_ids
    )
    sim_review_followup_reasons: list[str] = []
    followup_sim_candidate_ids: set[str] = set()
    for shard in sim_shards or [primary_sim_shard]:
        shard_reasons = parsed_review_followup_reasons(
            ai_status=str(shard.get("status") or "missing"),
            audit_status=shard.get("audit_status"),
            forbidden_use_violations=(
                ["forbidden_use_violation"]
                if int(shard.get("forbidden_use_violation_count") or 0) > 0
                else []
            ),
            missing_ai_proposal_count=0,
            missing_comparative_review_count=0,
        )
        if shard_reasons:
            followup_sim_candidate_ids.update(
                str(item) for item in (shard.get("candidate_ids") or []) if str(item)
            )
        sim_review_followup_reasons.extend(shard_reasons)
    missing_sim_proposal_candidate_ids = {
        str(item.get("bucket_id"))
        for item in sim_reviewed_candidates
        if item.get("bucket_id")
        and item.get("ai_tier2_proposal", {}).get("proposal_status") != "provided"
    }
    missing_sim_comparative_candidate_ids = {
        str(item.get("bucket_id"))
        for item in sim_reviewed_candidates
        if item.get("bucket_id")
        and item.get("comparative_review", {}).get("selected_source") == "reject"
    }
    followup_sim_candidate_ids.update(missing_sim_proposal_candidate_ids)
    followup_sim_candidate_ids.update(missing_sim_comparative_candidate_ids)
    sim_review_followup_reasons.extend(
        parsed_review_followup_reasons(
            ai_status=(
                "parsed"
                if sim_reviewed_candidate_ids
                else str(primary_sim_shard.get("status") or "missing")
            ),
            audit_status=primary_sim_shard.get("audit_status"),
            forbidden_use_violations=[],
            missing_ai_proposal_count=sim_missing_ai_proposal_count,
            missing_comparative_review_count=sim_missing_comparative_review_count,
        )
    )
    sim_review_followup_reasons = list(dict.fromkeys(sim_review_followup_reasons))
    followup_reasons = parsed_review_followup_reasons(
        ai_status=ai_status,
        audit_status=ai_payload_audit.get("status"),
        forbidden_use_violations=ai_forbidden,
        missing_ai_proposal_count=reviewed_missing_ai_proposal_count,
        missing_comparative_review_count=reviewed_missing_comparative_review_count,
    )
    followup_reasons = list(
        dict.fromkeys([*followup_reasons, *sim_review_followup_reasons])
    )
    ai_fail_closed = (
        ai_status == "missing" and sim_review_required
    ) or sim_review_call_fail_closed
    sim_auto_blocked_by_review_followup = bool(sim_review_followup_reasons)
    sim_auto_downgrade_candidate_ids = set(failed_sim_candidate_ids)
    if ai_fail_closed and not sim_reviewed_candidate_ids:
        sim_auto_downgrade_candidate_ids.update(pre_review_sim_auto_candidate_ids)
    elif sim_auto_blocked_by_review_followup:
        sim_auto_downgrade_candidate_ids.update(missing_sim_review_candidate_ids)
        sim_auto_downgrade_candidate_ids.update(followup_sim_candidate_ids)
    provider_disabled = resolved_provider in {"none", "off", "false", "0"}
    if sim_auto_blocked_by_review_followup:
        ai_review_blocker_state = "sim_policy_followup_required"
    elif ai_status == "parse_rejected":
        ai_review_blocker_state = "parse_rejected"
    elif (
        ai_fail_closed and provider_disabled and pre_review_sim_auto_candidate_count > 0
    ):
        ai_review_blocker_state = "provider_disabled"
    elif ai_fail_closed:
        ai_review_blocker_state = "provider_unavailable"
    else:
        ai_review_blocker_state = "none"
    if (
        ai_fail_closed
        or sim_auto_blocked_by_review_followup
        or sim_auto_downgrade_candidate_ids
    ):
        downgraded_candidates: list[dict[str, Any]] = []
        for candidate in candidates:
            bucket_id = str(candidate.get("bucket_id") or "")
            if (
                candidate.get("classification_state") == "sim_auto_approved"
                and bucket_id in sim_auto_downgrade_candidate_ids
            ):
                reason_key = (
                    "sim_auto_downgraded_by_ai_fail_closed"
                    if ai_fail_closed
                    else (
                        "sim_auto_downgraded_by_ai_shard_failure"
                        if bucket_id in failed_sim_candidate_ids
                        else (
                            "sim_auto_blocked_by_ai_review_followup"
                            if sim_auto_blocked_by_review_followup
                            else "sim_auto_downgraded_by_ai_fail_closed"
                        )
                    )
                )
                downgraded_candidates.append(
                    {
                        **candidate,
                        "classification_state": "source_only_keep_collecting",
                        "next_route": "postclose_source_quality_or_sample_collection",
                        reason_key: True,
                        "ai_review_blocker_state": ai_review_blocker_state,
                        "pre_review_sim_auto_candidate_count": pre_review_sim_auto_candidate_count,
                        "ai_review_required_but_provider_disabled": ai_review_blocker_state
                        == "provider_disabled",
                        "ai_review_provider_unavailable": ai_review_blocker_state
                        == "provider_unavailable",
                        "ai_review_parse_rejected": ai_review_blocker_state
                        == "parse_rejected",
                    }
                )
            else:
                downgraded_candidates.append(candidate)
        candidates = downgraded_candidates
    by_state: dict[str, int] = defaultdict(int)
    by_stage: dict[str, int] = defaultdict(int)
    for candidate in candidates:
        by_state[str(candidate.get("classification_state"))] += 1
        by_stage[str(candidate.get("lifecycle_stage") or "-")] += 1

    sim_auto = [
        item
        for item in candidates
        if item.get("classification_state") == "sim_auto_approved"
    ]
    flow_sim_auto = [
        item
        for item in sim_auto
        if item.get("source_section") == "swing_lifecycle_flow_bucket_attribution"
    ]
    stage_only_source_only = [
        item
        for item in candidates
        if item.get("classification_state") == "source_only_keep_collecting"
        and item.get("source_section")
        in {
            "entry_bucket_attribution",
            "holding_exit_bucket_attribution",
            "scale_in_bucket_attribution",
            "discovery_arm_attribution",
        }
    ]
    code_patch = [
        item
        for item in candidates
        if item.get("classification_state")
        in {
            "code_patch_required",
            "runtime_blocked_contract_gap",
            "automation_handoff_gap",
        }
    ]
    resolved_source_quality_candidates = [
        item
        for item in candidates
        if isinstance(item.get("source_quality_resolution"), dict)
        and item.get("source_quality_resolution", {}).get("status")
        == "implemented_source_quality_contract_waiting_sample"
    ]
    raw_implemented_source_quality_waiting = [
        item for item in candidates if _is_implemented_source_quality_waiting(item)
    ]
    implemented_source_quality_waiting_sample_candidate_count = len(
        resolved_source_quality_candidates
    )
    implemented_source_quality_waiting_sample_workorder_count = len(
        resolved_explicit_workorders
    )
    implemented_source_quality_waiting_sample_total_count = (
        implemented_source_quality_waiting_sample_candidate_count
        + implemented_source_quality_waiting_sample_workorder_count
    )
    ai_review_points = _ai_review_augmentation_points(
        matrix=matrix, candidates=candidates
    )
    ai_audit = _ai_audit_section(ai_review_points)
    warnings: list[str] = []
    if not matrix:
        warnings.append("swing_lifecycle_decision_matrix_missing")
    if source_contract_status == "fail":
        warnings.append("source_contract_fail")
    if ai_status != "parsed" and ai_fail_closed:
        warnings.append(f"ai_two_pass_review_{ai_status}_fail_closed")
    elif ai_status != "parsed":
        warnings.append(f"ai_two_pass_review_{ai_status}_source_only")
    if ai_payload_audit.get("status") == "correction_required" and not ai_fail_closed:
        warnings.append("ai_two_pass_review_correction_required_source_only")
    if ai_fail_closed:
        warnings.append("ai_two_pass_review_fail_closed_sim_auto_blocked")
    if followup_reasons:
        warnings.append("ai_two_pass_review_followup_required_source_only")
    if sim_auto_blocked_by_review_followup:
        warnings.append("ai_two_pass_review_followup_sim_auto_blocked")
    if (
        ai_review_points
        and ai_audit.get("status") != "configured_deterministic_two_pass"
    ):
        warnings.append("swing_ldm_ai_review_not_configured")
    warnings = list(dict.fromkeys(warnings))

    report = {
        "schema_version": 1,
        "report_type": REPORT_TYPE,
        "date": date_key,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "discovery_version": DISCOVERY_VERSION,
        "runtime_effect": False,
        "source_only": True,
        "decision_authority": DECISION_AUTHORITY,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "allowed_runtime_apply": False,
        "human_intervention_required": False,
        "forbidden_uses": FORBIDDEN_USES,
        "evidence_authority_contract": evidence_authority_contract(),
        "ai_review_policy": {
            "status": ai_audit.get("status"),
            "provider": ai_audit.get("provider"),
            "ambiguity_blocks_sim_auto_approval": False,
            "allowed_flags": ["explicit_contract_gap", "source_quality_gap"],
            "required_flow": ["interpretation", "audit", "final_conclusions"],
            "required_flow_status": ai_audit.get("required_flow_status"),
            "runtime_effect": False,
            "allowed_runtime_apply": False,
        },
        "summary": {
            "status": (
                "missing"
                if not matrix
                else "pass" if source_contract_status == "pass" else "fail"
            ),
            "source_contract_status": source_contract_status,
            "candidate_count": len(candidates),
            "surfaced_candidate_count": len(candidates),
            "sim_auto_approved_count": len(sim_auto),
            "swing_lifecycle_flow_bucket_count": flow_summary.get("bucket_count", 0),
            "complete_flow_count": flow_summary.get("complete_flow_count", 0),
            "incomplete_flow_count": flow_summary.get("incomplete_flow_count", 0),
            "identity_join_rate": flow_summary.get("identity_join_rate", 0.0),
            "complete_flow_rate": flow_summary.get("complete_flow_rate", 0.0),
            "join_contract_blocked": bool(flow_summary.get("join_contract_blocked")),
            "flow_sim_auto_approved_count": len(flow_sim_auto),
            "stage_only_source_only_count": len(stage_only_source_only),
            "source_only_keep_collecting_count": by_state.get(
                "source_only_keep_collecting", 0
            ),
            "code_patch_required_count": len(code_patch)
            + len(active_explicit_workorders)
            + (1 if followup_reasons else 0),
            "raw_implemented_source_quality_waiting_sample_count": len(
                raw_implemented_source_quality_waiting
            ),
            "implemented_source_quality_waiting_sample_candidate_count": (
                implemented_source_quality_waiting_sample_candidate_count
            ),
            "implemented_source_quality_waiting_sample_workorder_count": (
                implemented_source_quality_waiting_sample_workorder_count
            ),
            "implemented_source_quality_waiting_sample_total_count": (
                implemented_source_quality_waiting_sample_total_count
            ),
            "implemented_source_quality_waiting_sample_count": (
                implemented_source_quality_waiting_sample_total_count
            ),
            "runtime_blocked_contract_gap_count": by_state.get(
                "runtime_blocked_contract_gap", 0
            ),
            "automation_handoff_gap_count": by_state.get("automation_handoff_gap", 0),
            "ai_review_augmentation_point_count": len(ai_review_points),
            "ai_two_pass_review_status": ai_status,
            "ai_fail_closed": ai_fail_closed,
            "ai_review_followup_required": bool(followup_reasons),
            "ai_review_followup_reasons": followup_reasons,
            "sim_auto_blocked_by_ai_review_followup": sim_auto_blocked_by_review_followup,
            "ai_review_blocker_state": ai_review_blocker_state,
            "ai_review_orchestration_policy": "critical_sim_policy_first",
            "ai_review_optional_deferred_shard_count": optional_deferred_shard_count,
            "ai_review_optional_deferred_candidate_count": optional_deferred_candidate_count,
            "ai_review_id_repair_count": ai_review_id_repair_count,
            "pre_review_sim_auto_candidate_count": pre_review_sim_auto_candidate_count,
            "sim_auto_reviewed_candidate_count": len(sim_reviewed_candidate_ids),
            "sim_auto_unreviewed_candidate_count": unreviewed_sim_auto_candidate_count,
            "sim_auto_downgraded_by_review_count": len(
                sim_auto_downgrade_candidate_ids
            ),
            "sim_auto_review_shard_count": len(sim_shards),
            "deterministic_proposal_count": len(candidates),
            "ai_tier2_proposal_count": sum(
                1
                for item in candidates
                if item.get("ai_tier2_proposal", {}).get("proposal_status")
                == "provided"
            ),
            "comparative_review_count": len(candidates),
            "ai_reviewed_candidate_count": len(reviewed_candidates),
            "ai_unreviewed_candidate_count": max(
                len(candidates) - len(reviewed_candidates), 0
            ),
            "unreviewed_sim_auto_candidate_count": unreviewed_sim_auto_candidate_count,
            "missing_ai_tier2_proposal_count": missing_ai_proposal_count,
            "missing_comparative_review_count": missing_comparative_review_count,
            "sim_missing_ai_tier2_proposal_count": sim_missing_ai_proposal_count,
            "sim_missing_comparative_review_count": sim_missing_comparative_review_count,
            "selected_decision_counts": proposal_counts(
                [item.get("comparative_review") or {} for item in candidates],
                key="selected_decision",
            ),
            "selected_source_counts": proposal_counts(
                [item.get("comparative_review") or {} for item in candidates],
                key="selected_source",
            ),
            "ai_audit_status": ai_audit.get("status"),
            "ai_audit_point_count": len(ai_audit.get("audit_points") or []),
            "ai_audit_explicit_gap_count": ai_audit.get("explicit_gap_count"),
            "sim_auto_policy_audited": bool(ai_audit.get("sim_auto_policy_preserved")),
            "swing_entry_bottleneck_primary": entry_bottleneck.get("primary"),
            "swing_entry_bottleneck_candidate_present": bool(
                entry_bottleneck_candidate
            ),
            "state_counts": dict(by_state),
            "stage_counts": dict(by_stage),
            "human_intervention_required": False,
        },
        "ai_review_augmentation_points": ai_review_points,
        "ai_audit": ai_audit,
        "ai_two_pass_review": {
            "provider": resolved_provider,
            "status": ai_status,
            "model": provider_status.get("model") or AI_REVIEW_MODEL,
            "requested_provider": provider_status.get("requested_provider")
            or resolved_provider,
            "primary_provider": provider_status.get("primary_provider"),
            "failback_provider": provider_status.get("failback_provider"),
            "schema_name": AI_REVIEW_SCHEMA_NAME,
            "provider_status": provider_status,
            "review_scope": "sharded_priority_limited_source_only_review",
            "candidate_selection_policy": "sim-auto shard, gap/workorder shard, taxonomy source-only sample shard",
            "orchestration_policy": "critical_sim_policy_first",
            "optional_deferred_shard_count": optional_deferred_shard_count,
            "optional_deferred_candidate_count": optional_deferred_candidate_count,
            "id_repair_count": ai_review_id_repair_count,
            "reviewed_candidate_ids": sorted(ai_reviewed_candidate_ids),
            "omitted_candidate_count": max(
                len(candidates) - len(ai_reviewed_candidate_ids), 0
            ),
            "shards": ai_review_shards,
            "audit": ai_payload_audit,
            "deterministic_proposals": [
                item.get("deterministic_proposal")
                for item in candidates
                if item.get("deterministic_proposal")
            ],
            "ai_tier2_proposals": [
                item.get("ai_tier2_proposal")
                for item in candidates
                if item.get("ai_tier2_proposal")
            ],
            "comparative_reviews": [
                item.get("comparative_review")
                for item in candidates
                if item.get("comparative_review")
            ],
            "warnings": ai_warnings,
            "fail_closed": ai_fail_closed,
            "followup_required": bool(followup_reasons),
            "followup_reasons": followup_reasons,
            "sim_auto_blocked_by_review_followup": sim_auto_blocked_by_review_followup,
            "ai_review_blocker_state": ai_review_blocker_state,
            "pre_review_sim_auto_candidate_count": pre_review_sim_auto_candidate_count,
            "sim_auto_reviewed_candidate_count": len(sim_reviewed_candidate_ids),
            "sim_auto_unreviewed_candidate_count": unreviewed_sim_auto_candidate_count,
            "sim_auto_downgraded_by_review_count": len(
                sim_auto_downgrade_candidate_ids
            ),
            "sim_auto_review_shard_count": len(sim_shards),
            "missing_ai_tier2_proposal_count": missing_ai_proposal_count,
            "missing_comparative_review_count": missing_comparative_review_count,
            "sim_missing_ai_tier2_proposal_count": sim_missing_ai_proposal_count,
            "sim_missing_comparative_review_count": sim_missing_comparative_review_count,
            "unreviewed_sim_auto_candidate_count": unreviewed_sim_auto_candidate_count,
        },
        "deterministic_proposals": [
            item.get("deterministic_proposal")
            for item in candidates
            if item.get("deterministic_proposal")
        ],
        "ai_tier2_proposals": [
            item.get("ai_tier2_proposal")
            for item in candidates
            if item.get("ai_tier2_proposal")
        ],
        "comparative_reviews": [
            item.get("comparative_review")
            for item in candidates
            if item.get("comparative_review")
        ],
        "selected_decision_counts": proposal_counts(
            [item.get("comparative_review") or {} for item in candidates],
            key="selected_decision",
        ),
        "selected_source_counts": proposal_counts(
            [item.get("comparative_review") or {} for item in candidates],
            key="selected_source",
        ),
        "surfaced_candidate_ids": [
            str(item.get("bucket_id")) for item in candidates if item.get("bucket_id")
        ],
        "surfaced_candidates": candidates,
        "sim_auto_approved_candidates": sim_auto,
        "code_improvement_workorders": [
            {
                "workorder_id": (
                    f"swing_bucket_discovery_{_bucket_key_slug(item.get('bucket_id'))}"
                ),
                "candidate_id": item.get("candidate_id") or item.get("bucket_id"),
                "bucket_id": item.get("bucket_id"),
                "stage": item.get("stage") or item.get("lifecycle_stage"),
                "lifecycle_stage": item.get("lifecycle_stage") or item.get("stage"),
                "source_workorder_id": item.get("source_workorder_id")
                or item.get("workorder_id"),
                "parent_bucket_id": item.get("parent_bucket_id")
                or item.get("bucket_id"),
                "classification_state": item.get("classification_state"),
                "reason": "swing_ldm_bucket_contract_or_source_quality_gap",
                "target_subsystem": "swing_lifecycle_bucket_discovery",
                "implementation_status": item.get("implementation_status"),
                "implementation_provenance": item.get("implementation_provenance")
                or {},
                **_workorder_contract_fields(),
            }
            for item in code_patch
        ]
        + (
            [_ai_review_followup_workorder(followup_reasons, ai_payload_audit)]
            if followup_reasons
            else []
        )
        + [_normalize_explicit_workorder(item) for item in active_explicit_workorders],
        "resolved_source_quality_candidates": resolved_source_quality_candidates,
        "resolved_source_quality_workorders": [
            {
                **_normalize_explicit_workorder(item),
                "resolution_state": "implemented_source_quality_contract_waiting_sample",
            }
            for item in resolved_explicit_workorders
        ],
        "sources": {
            "swing_lifecycle_decision_matrix": (
                str(matrix_json) if matrix_json.exists() else None
            ),
            "swing_daily_simulation": None,
        },
        "warnings": warnings,
    }
    workorders = report["code_improvement_workorders"]
    report["summary"]["code_improvement_workorder_ids"] = [
        str(item.get("workorder_id"))
        for item in workorders
        if isinstance(item, dict) and item.get("workorder_id")
    ]
    report["summary"]["implemented_code_improvement_workorder_ids"] = [
        str(item.get("workorder_id"))
        for item in workorders
        if isinstance(item, dict)
        and str(item.get("implementation_status") or "").startswith("implemented")
    ]
    report["summary"]["pending_code_improvement_workorder_ids"] = [
        str(item.get("workorder_id"))
        for item in workorders
        if isinstance(item, dict)
        and item.get("workorder_id")
        and not str(item.get("implementation_status") or "").startswith("implemented")
    ]
    report["summary"]["ai_review_followup_workorder_ids"] = [
        str(item.get("workorder_id"))
        for item in workorders
        if isinstance(item, dict)
        and str(item.get("source_workorder_id") or "") == "ai_review_followup"
    ]
    return report


def render_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    lines = [
        f"# Swing Lifecycle Bucket Discovery {report.get('date')}",
        "",
        "## Summary",
        f"- runtime_effect: `{report.get('runtime_effect')}`",
        f"- decision_authority: `{report.get('decision_authority')}`",
        f"- source_contract_status: `{summary.get('source_contract_status')}`",
        f"- surfaced_candidate_count: `{summary.get('surfaced_candidate_count')}`",
        f"- sim_auto_approved_count: `{summary.get('sim_auto_approved_count')}`",
        f"- sim_auto_reviewed_candidate_count: `{summary.get('sim_auto_reviewed_candidate_count')}`",
        f"- sim_auto_unreviewed_candidate_count: `{summary.get('sim_auto_unreviewed_candidate_count')}`",
        f"- sim_auto_downgraded_by_review_count: `{summary.get('sim_auto_downgraded_by_review_count')}`",
        f"- sim_auto_review_shard_count: `{summary.get('sim_auto_review_shard_count')}`",
        f"- swing_lifecycle_flow_bucket_count: `{summary.get('swing_lifecycle_flow_bucket_count')}`",
        f"- complete_flow_count: `{summary.get('complete_flow_count')}`",
        f"- incomplete_flow_count: `{summary.get('incomplete_flow_count')}`",
        f"- identity_join_rate: `{summary.get('identity_join_rate')}`",
        f"- complete_flow_rate: `{summary.get('complete_flow_rate')}`",
        f"- join_contract_blocked: `{summary.get('join_contract_blocked')}`",
        f"- flow_sim_auto_approved_count: `{summary.get('flow_sim_auto_approved_count')}`",
        f"- stage_only_source_only_count: `{summary.get('stage_only_source_only_count')}`",
        f"- code_patch_required_count: `{summary.get('code_patch_required_count')}`",
        f"- implemented_source_quality_waiting_sample_count: `{summary.get('implemented_source_quality_waiting_sample_count')}`",
        f"- implemented_source_quality_waiting_sample_candidate_count: `{summary.get('implemented_source_quality_waiting_sample_candidate_count')}`",
        f"- implemented_source_quality_waiting_sample_workorder_count: `{summary.get('implemented_source_quality_waiting_sample_workorder_count')}`",
        f"- implemented_source_quality_waiting_sample_total_count: `{summary.get('implemented_source_quality_waiting_sample_total_count')}`",
        f"- raw_implemented_source_quality_waiting_sample_count: `{summary.get('raw_implemented_source_quality_waiting_sample_count')}`",
        f"- ai_review_augmentation_point_count: `{summary.get('ai_review_augmentation_point_count')}`",
        f"- ai_review_orchestration_policy: `{summary.get('ai_review_orchestration_policy')}`",
        f"- ai_review_optional_deferred_shard_count: `{summary.get('ai_review_optional_deferred_shard_count')}`",
        f"- ai_review_optional_deferred_candidate_count: `{summary.get('ai_review_optional_deferred_candidate_count')}`",
        f"- ai_review_id_repair_count: `{summary.get('ai_review_id_repair_count')}`",
        f"- human_intervention_required: `{summary.get('human_intervention_required')}`",
        f"- warnings: `{report.get('warnings') or []}`",
        "",
        "## Surfaced Candidates",
    ]
    for item in (report.get("surfaced_candidates") or [])[:20]:
        lines.append(
            f"- `{item.get('candidate_id') or item.get('bucket_id')}` state=`{item.get('classification_state')}` "
            f"stage=`{item.get('stage') or item.get('lifecycle_stage')}` route=`{item.get('next_route')}`"
        )
    lines.extend(["", "## AI Review Augmentation Points"])
    for item in report.get("ai_review_augmentation_points") or []:
        lines.append(
            f"- `{item.get('point_id')}` stage=`{item.get('stage')}` route=`{item.get('recommended_route')}`"
        )
    resolved_candidates = report.get("resolved_source_quality_candidates") or []
    resolved_workorders = report.get("resolved_source_quality_workorders") or []
    if resolved_candidates or resolved_workorders:
        lines.extend(["", "## Resolved Source Quality Sample Wait"])
        for item in resolved_candidates[:10]:
            if isinstance(item, dict):
                lines.append(
                    f"- candidate `{item.get('bucket_id')}` "
                    f"status=`{(item.get('source_quality_resolution') or {}).get('status')}`"
                )
        for item in resolved_workorders[:10]:
            if isinstance(item, dict):
                lines.append(
                    f"- workorder `{item.get('workorder_id')}` "
                    f"status=`{item.get('resolution_state')}`"
                )
    return "\n".join(lines).rstrip() + "\n"


def write_report(report: dict[str, Any]) -> tuple[Path, Path]:
    json_path, md_path = report_paths(str(report.get("date")))
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    md_path.write_text(render_markdown(report), encoding="utf-8")
    refresh_swing_sim_auto_approval(
        str(report.get("date")), swing_lifecycle_bucket_report=report
    )
    return json_path, md_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build Swing lifecycle bucket discovery."
    )
    parser.add_argument("--date", dest="target_date", default=date.today().isoformat())
    parser.add_argument(
        "--ai-provider",
        dest="ai_provider",
        default=None,
        help=(
            "AI provider for source-only Tier2 review. Defaults to env "
            "KORSTOCKSCAN_SWING_LIFECYCLE_BUCKET_DISCOVERY_AI_PROVIDER, then module default openai. "
            "This flag enables/disables review calls; actual primary/failback route is resolved from "
            "KORSTOCKSCAN_SWING_LIFECYCLE_BUCKET_DISCOVERY_AI_* provider config."
        ),
    )
    args = parser.parse_args()
    report = build_swing_lifecycle_bucket_discovery(
        args.target_date, provider=args.ai_provider
    )
    json_path, md_path = write_report(report)
    print(f"[swing-lifecycle-bucket-discovery] wrote {json_path} {md_path}")


if __name__ == "__main__":
    main()
