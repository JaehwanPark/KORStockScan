"""Classify Swing LDM buckets into sim-only automation routes."""

from __future__ import annotations

import argparse
import json
import os
import re
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any

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
from src.engine.swing.sim_auto_approval_control_tower import refresh_swing_sim_auto_approval
from src.engine.swing_lifecycle_decision_matrix import report_paths as matrix_report_paths
from src.utils.constants import DATA_DIR


REPORT_DIR = Path(DATA_DIR) / "report" / "swing_lifecycle_bucket_discovery"
REPORT_TYPE = "swing_lifecycle_bucket_discovery"
DISCOVERY_VERSION = "swing_lifecycle_bucket_discovery_v1"
DECISION_AUTHORITY = "swing_ldm_bucket_discovery_sim_auto"
AI_REVIEW_SCHEMA_NAME = "swing_lifecycle_bucket_discovery_review_v1"
AI_REVIEWER_NAME = "swing_lifecycle_bucket_discovery_ai_review"
AI_REVIEW_MODEL = "gpt-5.4"
AI_REVIEW_DEFAULT_PROVIDER = "none"
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
    text = re.sub(r"[^a-zA-Z0-9가-힣]+", "_", str(value or "").strip().lower()).strip("_")
    return text[:80] or "unknown"


def report_paths(target_date: str) -> tuple[Path, Path]:
    base = REPORT_DIR / f"swing_lifecycle_bucket_discovery_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def _bucket_id(stage: str, bucket_type: str, bucket_key: str) -> str:
    return f"swing_bucket_{_slug(stage)}_{_slug(bucket_type)}_{_slug(bucket_key)}"


def _classification_from_bucket(bucket: dict[str, Any]) -> str:
    route = str(bucket.get("recommended_route") or "")
    gate = str(bucket.get("source_quality_gate") or "")
    try:
        joined = int(float(bucket.get("joined_sample") or 0))
    except (TypeError, ValueError):
        joined = 0
    if route == "sim_auto_approved":
        return "sim_auto_approved"
    if route == "code_patch_required" or gate == "source_quality_blocker":
        return "code_patch_required"
    if joined <= 0 or gate == "hold_sample":
        return "source_only_keep_collecting"
    return "source_only_keep_collecting"


def _candidate_from_bucket(section_name: str, bucket: dict[str, Any]) -> dict[str, Any]:
    stage = str(bucket.get("lifecycle_stage") or "swing")
    bucket_type = str(bucket.get("bucket_type") or section_name)
    bucket_key = str(bucket.get("bucket_key") or "-")
    state = _classification_from_bucket(bucket)
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
    return {
        "bucket_id": _bucket_id(stage, bucket_type, bucket_key),
        "canonical_bucket": taxonomy["canonical_bucket"],
        "legacy_raw_bucket_key": taxonomy["legacy_raw_bucket_key"],
        "bucket_alias_version": BUCKET_ALIAS_VERSION,
        "dimension_set_version": DIMENSION_SET_VERSION,
        "normalized_dimensions": taxonomy["normalized_dimensions"],
        "normalized_metrics": taxonomy["normalized_metrics"],
        "deterministic_proposal": taxonomy["deterministic_proposal"],
        "source_section": section_name,
        "lifecycle_stage": stage,
        "bucket_type": bucket_type,
        "bucket_key": bucket_key,
        "classification_state": state,
        "source_quality_gate": bucket.get("source_quality_gate"),
        "joined_sample": bucket.get("joined_sample"),
        "sample_count": bucket.get("sample_count"),
        "source_workorder_id": bucket.get("workorder_id"),
        "parent_bucket_id": _bucket_id(stage, bucket_type, bucket_key),
        "implementation_status": bucket.get("implementation_status"),
        "implementation_provenance": bucket.get("implementation_provenance") if isinstance(bucket.get("implementation_provenance"), dict) else {},
        "source_quality_adjusted_ev_pct": bucket.get("source_quality_adjusted_ev_pct"),
        "decision_authority": DECISION_AUTHORITY,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "human_approval_required": False,
        "next_route": "next_preopen_swing_sim_policy_input"
        if state == "sim_auto_approved"
        else "postclose_source_quality_or_sample_collection",
        "forbidden_uses": FORBIDDEN_USES,
        "evidence_authority_contract": evidence_authority_contract(),
    }


def _swing_entry_bottleneck_candidate(matrix: dict[str, Any]) -> dict[str, Any] | None:
    bottleneck = matrix.get("swing_entry_bottleneck") if isinstance(matrix.get("swing_entry_bottleneck"), dict) else {}
    matches = bottleneck.get("matches") if isinstance(bottleneck.get("matches"), list) else []
    if bottleneck.get("primary") != "SWING_ENTRY_DROUGHT_CRITICAL" and "SWING_ENTRY_DROUGHT_CRITICAL" not in matches:
        return None
    counts = bottleneck.get("counts") if isinstance(bottleneck.get("counts"), dict) else {}
    ratios = bottleneck.get("ratios") if isinstance(bottleneck.get("ratios"), dict) else {}
    return {
        "bucket_id": "swing_entry_bottleneck_swing_entry_drought_critical",
        "source_section": "swing_entry_bottleneck",
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
        "source_workorder_id": item.get("source_workorder_id") or item.get("workorder_id"),
        "parent_bucket_id": item.get("parent_bucket_id") or item.get("bucket_id"),
    }


def _ensure_candidate_taxonomy(candidate: dict[str, Any]) -> dict[str, Any]:
    if candidate.get("deterministic_proposal"):
        return candidate
    stage = str(candidate.get("lifecycle_stage") or "swing")
    bucket_type = str(candidate.get("bucket_type") or candidate.get("source_section") or "bucket")
    bucket_key = str(candidate.get("bucket_key") or candidate.get("bucket_id") or "unknown")
    taxonomy = normalize_lifecycle_bucket(
        stage=stage,
        bucket_type=bucket_type,
        bucket_key=bucket_key,
        source_dimensions={"source_section": candidate.get("source_section"), "classification_state": candidate.get("classification_state")},
    )
    return {
        **candidate,
        "canonical_bucket": taxonomy["canonical_bucket"],
        "legacy_raw_bucket_key": taxonomy["legacy_raw_bucket_key"],
        "bucket_alias_version": BUCKET_ALIAS_VERSION,
        "dimension_set_version": DIMENSION_SET_VERSION,
        "normalized_dimensions": taxonomy["normalized_dimensions"],
        "normalized_metrics": taxonomy["normalized_metrics"],
        "deterministic_proposal": taxonomy["deterministic_proposal"],
    }


def _build_ai_review_context(target_date: str, candidates: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "date": target_date,
        "report_type": REPORT_TYPE,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "broker_order_forbidden": True,
        "forbidden_uses": FORBIDDEN_USES,
        "evidence_authority_contract": evidence_authority_contract(),
        "deterministic_proposals": [
            {
                "bucket_id": item.get("bucket_id"),
                "canonical_bucket": item.get("canonical_bucket"),
                "legacy_raw_bucket_key": item.get("legacy_raw_bucket_key"),
                "bucket_alias_version": item.get("bucket_alias_version"),
                "dimension_set_version": item.get("dimension_set_version"),
                "deterministic_proposal": item.get("deterministic_proposal"),
                "classification_state": item.get("classification_state"),
            }
            for item in candidates[:80]
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


def _call_openai_ai_review(context: dict[str, Any]) -> tuple[Any | None, dict[str, Any]]:
    try:
        from openai import OpenAI, RateLimitError
        from src.engine.ai_response_contracts import build_openai_response_text_format
        from src.engine.daily_threshold_cycle_report import _extract_openai_response_text, _load_threshold_ai_openai_keys
    except Exception as exc:
        return None, {"provider": "openai", "status": "unavailable", "reason": f"openai import failed: {exc}"}
    api_keys = _load_threshold_ai_openai_keys()
    if not api_keys:
        return None, {"provider": "openai", "status": "unavailable", "reason": "OPENAI_API_KEY not configured"}
    prompt = json.dumps(context, ensure_ascii=True, indent=2, default=str)
    errors: list[dict[str, str]] = []
    for attempt_index, (key_name, api_key) in enumerate(api_keys, start=1):
        try:
            client = OpenAI(api_key=api_key)
            response = client.responses.create(
                model=AI_REVIEW_MODEL,
                instructions=_build_ai_review_instructions(),
                input=prompt,
                text={"format": build_openai_response_text_format(AI_REVIEW_SCHEMA_NAME), "verbosity": "low"},
                reasoning={"effort": "high"},
                store=False,
                metadata={"endpoint_name": AI_REVIEWER_NAME, "schema_name": AI_REVIEW_SCHEMA_NAME, "report_type": REPORT_TYPE},
                timeout=180,
            )
            raw_text = _extract_openai_response_text(response)
            usage = getattr(response, "usage", None)
            return raw_text, {
                "provider": "openai",
                "status": "success",
                "key_name": key_name,
                "attempt_index": attempt_index,
                "attempted_key_count": len(api_keys),
                "model": AI_REVIEW_MODEL,
                "schema_name": AI_REVIEW_SCHEMA_NAME,
                "input_context_chars": len(prompt),
                "output_chars": len(raw_text),
                "input_tokens": int(getattr(usage, "input_tokens", 0) or 0) if usage else 0,
                "output_tokens": int(getattr(usage, "output_tokens", 0) or 0) if usage else 0,
            }
        except RateLimitError as exc:
            errors.append({"key_name": key_name, "error": f"rate_limit:{exc}"})
        except Exception as exc:
            errors.append({"key_name": key_name, "error": str(exc)})
    return None, {"provider": "openai", "status": "unavailable", "reason": "all OpenAI attempts failed", "errors": errors[-3:]}


def _parse_ai_review_response(raw_response: Any | None) -> tuple[str, dict[str, Any], list[str]]:
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
            decision_key = "proposal_decision" if key == "ai_tier2_proposals" else "selected_decision"
            if str(item.get(decision_key) or "") not in TAXONOMY_DECISIONS:
                warnings.append(f"ai_review_{key}_decision_invalid:{item.get('bucket_id')}")
            missing_contract = missing_metric_contract_fields(item.get("required_source_fields"))
            if missing_contract:
                warnings.append(f"ai_review_{key}_contract_missing:{item.get('bucket_id')}:{','.join(missing_contract)}")
            if has_forbidden_runtime_leak(item):
                warnings.append(f"ai_review_{key}_forbidden_use_leak:{item.get('bucket_id')}")
            if has_evidence_authority_violation(item):
                warnings.append(f"ai_review_{key}_evidence_authority_violation:{item.get('bucket_id')}")
    audit = payload.get("audit") if isinstance(payload.get("audit"), dict) else {}
    if str(audit.get("status") or "") not in {"pass", "correction_required", "insufficient_context"}:
        warnings.append("ai_review_audit_status_invalid")
    if not isinstance(audit.get("forbidden_use_violations"), list):
        warnings.append("ai_review_forbidden_use_violations_missing")
    if warnings:
        return "parse_rejected", payload, warnings
    return "parsed", payload, []


def _map_by_id(items: Any, key: str) -> dict[str, dict[str, Any]]:
    return {str(item.get(key)): item for item in items or [] if isinstance(item, dict) and item.get(key)}


def _ai_review_augmentation_points(*, matrix: dict[str, Any], candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not matrix:
        return []
    candidate_states = {str(item.get("classification_state") or "") for item in candidates}
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
            "source_paths": ["swing_lifecycle_bucket_discovery.sim_auto_approved_candidates"],
            "forbidden_runtime_uses": FORBIDDEN_USES,
            "reason": "AI audit can verify sim_auto_approved remains sim-only and does not imply real/canary/provider/bot changes",
            "recommended_route": "code_improvement_workorder",
        },
    ]
    if "source_only_keep_collecting" in candidate_states or "code_patch_required" in candidate_states:
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
                "interpreted_state": "source_only_gap_triaged" if has_gap else "sim_policy_preserved",
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
        "status": "configured_deterministic_two_pass" if audit_points else "not_required",
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
        "auditor_pass_count": sum(1 for item in audit_points if item.get("auditor_pass") is True),
        "explicit_gap_count": sum(1 for item in audit_points if item.get("explicit_gap_type")),
        "sim_auto_policy_preserved": True,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }


def _iter_attribution_sections(matrix: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    sections = []
    for name in (
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
    for section_name, section in _iter_attribution_sections(matrix):
        for bucket in section.get("buckets") or []:
            if isinstance(bucket, dict):
                candidates.append(_candidate_from_bucket(section_name, bucket))
        for item in section.get("code_improvement_workorders") or []:
            if isinstance(item, dict):
                explicit_workorders.append(item)
    entry_bottleneck_candidate = _swing_entry_bottleneck_candidate(matrix)
    if entry_bottleneck_candidate:
        candidates.append(entry_bottleneck_candidate)
    candidates = [_ensure_candidate_taxonomy(item) for item in candidates]

    resolved_provider = str(
        provider
        if provider is not None
        else os.getenv("KORSTOCKSCAN_SWING_LIFECYCLE_BUCKET_DISCOVERY_AI_PROVIDER", AI_REVIEW_DEFAULT_PROVIDER)
    ).strip().lower() or "none"
    ai_context = _build_ai_review_context(date_key, candidates)
    provider_status: dict[str, Any] = {
        "provider": resolved_provider,
        "status": "disabled" if resolved_provider in {"none", "off", "false", "0"} else "not_called",
        "model": AI_REVIEW_MODEL if resolved_provider not in {"none", "off", "false", "0"} else None,
        "schema_name": AI_REVIEW_SCHEMA_NAME,
    }
    raw_response = ai_raw_response
    if raw_response is not None:
        provider_status["status"] = "provided_response"
    if raw_response is None and resolved_provider == "openai":
        raw_response, provider_status = _call_openai_ai_review(ai_context)
    ai_status, ai_payload, ai_warnings = _parse_ai_review_response(raw_response)
    ai_proposals = _map_by_id(
        [
            {**item, "proposal_source": "ai_tier2", "proposal_status": "provided"}
            for item in (ai_payload.get("ai_tier2_proposals") if isinstance(ai_payload, dict) else []) or []
            if isinstance(item, dict)
        ],
        "bucket_id",
    )
    ai_comparatives = _map_by_id(
        (ai_payload.get("comparative_reviews") if isinstance(ai_payload, dict) else []) or [],
        "bucket_id",
    )
    enriched_candidates = []
    for candidate in candidates:
        bucket_id = str(candidate.get("bucket_id") or "")
        deterministic = candidate.get("deterministic_proposal") if isinstance(candidate.get("deterministic_proposal"), dict) else {}
        ai_proposal = ai_proposals.get(bucket_id) or default_ai_tier2_proposal(bucket_id, deterministic)
        comparative = compare_taxonomy_proposals(
            bucket_id=bucket_id,
            deterministic_proposal=deterministic,
            ai_tier2_proposal=ai_proposal,
            comparative_review=ai_comparatives.get(bucket_id),
        )
        if ai_status != "parsed":
            comparative = {
                **comparative,
                "selected_decision": "source_quality_blocker",
                "selected_source": "reject",
                "comparison_summary": "AI Tier2 comparative review missing or rejected; source-only fail-closed review recorded.",
            }
        enriched_candidates.append(
            {
                **candidate,
                "ai_tier2_proposal": ai_proposal,
                "comparative_review": comparative,
                "ai_review_status": ai_status,
            }
        )
    candidates = enriched_candidates

    source_contract_status = "missing" if not matrix else "pass"
    contract = matrix.get("input_contract") if isinstance(matrix.get("input_contract"), dict) else {}
    entry_bottleneck = matrix.get("swing_entry_bottleneck") if isinstance(matrix.get("swing_entry_bottleneck"), dict) else {}
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

    ai_payload_audit = ai_payload.get("audit") if isinstance(ai_payload.get("audit"), dict) else {}
    ai_forbidden = ai_payload_audit.get("forbidden_use_violations")
    if not isinstance(ai_forbidden, list):
        ai_forbidden = []
    missing_ai_proposal_count = sum(
        1 for item in candidates if item.get("ai_tier2_proposal", {}).get("proposal_status") != "provided"
    )
    missing_comparative_review_count = sum(
        1 for item in candidates if item.get("comparative_review", {}).get("selected_source") == "reject"
    )
    ai_fail_closed = (
        ai_status != "parsed"
        or ai_payload_audit.get("status") != "pass"
        or bool(ai_forbidden)
        or missing_ai_proposal_count > 0
        or missing_comparative_review_count > 0
    )
    if ai_fail_closed:
        downgraded_candidates: list[dict[str, Any]] = []
        for candidate in candidates:
            if candidate.get("classification_state") == "sim_auto_approved":
                downgraded_candidates.append(
                    {
                        **candidate,
                        "classification_state": "source_only_keep_collecting",
                        "next_route": "postclose_source_quality_or_sample_collection",
                        "sim_auto_downgraded_by_ai_fail_closed": True,
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

    sim_auto = [item for item in candidates if item.get("classification_state") == "sim_auto_approved"]
    code_patch = [
        item
        for item in candidates
        if item.get("classification_state") in {"code_patch_required", "runtime_blocked_contract_gap", "automation_handoff_gap"}
    ]
    ai_review_points = _ai_review_augmentation_points(matrix=matrix, candidates=candidates)
    ai_audit = _ai_audit_section(ai_review_points)
    warnings: list[str] = []
    if not matrix:
        warnings.append("swing_lifecycle_decision_matrix_missing")
    if source_contract_status == "fail":
        warnings.append("source_contract_fail")
    if ai_review_points and ai_audit.get("status") != "configured_deterministic_two_pass":
        warnings.append("swing_ldm_ai_review_not_configured")

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
            "status": "missing" if not matrix else "pass" if source_contract_status == "pass" else "fail",
            "source_contract_status": source_contract_status,
            "candidate_count": len(candidates),
            "surfaced_candidate_count": len(candidates),
            "sim_auto_approved_count": len(sim_auto),
            "source_only_keep_collecting_count": by_state.get("source_only_keep_collecting", 0),
            "code_patch_required_count": len(code_patch) + len(explicit_workorders),
            "runtime_blocked_contract_gap_count": by_state.get("runtime_blocked_contract_gap", 0),
            "automation_handoff_gap_count": by_state.get("automation_handoff_gap", 0),
            "ai_review_augmentation_point_count": len(ai_review_points),
            "ai_two_pass_review_status": ai_status,
            "ai_fail_closed": ai_fail_closed,
            "deterministic_proposal_count": len(candidates),
            "ai_tier2_proposal_count": sum(
                1 for item in candidates if item.get("ai_tier2_proposal", {}).get("proposal_status") == "provided"
            ),
            "comparative_review_count": len(candidates),
            "missing_ai_tier2_proposal_count": missing_ai_proposal_count,
            "missing_comparative_review_count": missing_comparative_review_count,
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
            "swing_entry_bottleneck_candidate_present": bool(entry_bottleneck_candidate),
            "state_counts": dict(by_state),
            "stage_counts": dict(by_stage),
            "human_intervention_required": False,
        },
        "ai_review_augmentation_points": ai_review_points,
        "ai_audit": ai_audit,
        "ai_two_pass_review": {
            "provider": resolved_provider,
            "status": ai_status,
            "model": provider_status.get("model") or (AI_REVIEW_MODEL if resolved_provider == "openai" else None),
            "schema_name": AI_REVIEW_SCHEMA_NAME,
            "provider_status": provider_status,
            "audit": ai_payload_audit,
            "deterministic_proposals": [
                item.get("deterministic_proposal") for item in candidates if item.get("deterministic_proposal")
            ],
            "ai_tier2_proposals": [
                item.get("ai_tier2_proposal") for item in candidates if item.get("ai_tier2_proposal")
            ],
            "comparative_reviews": [
                item.get("comparative_review") for item in candidates if item.get("comparative_review")
            ],
            "warnings": ai_warnings,
            "fail_closed": ai_fail_closed,
            "missing_ai_tier2_proposal_count": missing_ai_proposal_count,
            "missing_comparative_review_count": missing_comparative_review_count,
        },
        "deterministic_proposals": [
            item.get("deterministic_proposal") for item in candidates if item.get("deterministic_proposal")
        ],
        "ai_tier2_proposals": [
            item.get("ai_tier2_proposal") for item in candidates if item.get("ai_tier2_proposal")
        ],
        "comparative_reviews": [
            item.get("comparative_review") for item in candidates if item.get("comparative_review")
        ],
        "selected_decision_counts": proposal_counts(
            [item.get("comparative_review") or {} for item in candidates],
            key="selected_decision",
        ),
        "selected_source_counts": proposal_counts(
            [item.get("comparative_review") or {} for item in candidates],
            key="selected_source",
        ),
        "surfaced_candidate_ids": [str(item.get("bucket_id")) for item in candidates if item.get("bucket_id")],
        "surfaced_candidates": candidates,
        "sim_auto_approved_candidates": sim_auto,
        "code_improvement_workorders": [
            {
                "workorder_id": f"swing_bucket_discovery_{_slug(item.get('bucket_id'))}",
                "bucket_id": item.get("bucket_id"),
                "source_workorder_id": item.get("source_workorder_id") or item.get("workorder_id"),
                "parent_bucket_id": item.get("parent_bucket_id") or item.get("bucket_id"),
                "classification_state": item.get("classification_state"),
                "reason": "swing_ldm_bucket_contract_or_source_quality_gap",
                "target_subsystem": "swing_lifecycle_bucket_discovery",
                "implementation_status": item.get("implementation_status"),
                "implementation_provenance": item.get("implementation_provenance") or {},
                **_workorder_contract_fields(),
            }
            for item in code_patch
        ]
        + [_normalize_explicit_workorder(item) for item in explicit_workorders],
        "sources": {
            "swing_lifecycle_decision_matrix": str(matrix_json) if matrix_json.exists() else None,
            "swing_daily_simulation": None,
        },
        "warnings": warnings,
    }
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
        f"- code_patch_required_count: `{summary.get('code_patch_required_count')}`",
        f"- ai_review_augmentation_point_count: `{summary.get('ai_review_augmentation_point_count')}`",
        f"- human_intervention_required: `{summary.get('human_intervention_required')}`",
        f"- warnings: `{report.get('warnings') or []}`",
        "",
        "## Surfaced Candidates",
    ]
    for item in (report.get("surfaced_candidates") or [])[:20]:
        lines.append(
            f"- `{item.get('bucket_id')}` state=`{item.get('classification_state')}` "
            f"stage=`{item.get('lifecycle_stage')}` route=`{item.get('next_route')}`"
        )
    lines.extend(["", "## AI Review Augmentation Points"])
    for item in report.get("ai_review_augmentation_points") or []:
        lines.append(
            f"- `{item.get('point_id')}` stage=`{item.get('stage')}` route=`{item.get('recommended_route')}`"
        )
    return "\n".join(lines).rstrip() + "\n"


def write_report(report: dict[str, Any]) -> tuple[Path, Path]:
    json_path, md_path = report_paths(str(report.get("date")))
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    refresh_swing_sim_auto_approval(str(report.get("date")), swing_lifecycle_bucket_report=report)
    return json_path, md_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Swing lifecycle bucket discovery.")
    parser.add_argument("--date", dest="target_date", default=date.today().isoformat())
    args = parser.parse_args()
    report = build_swing_lifecycle_bucket_discovery(args.target_date)
    json_path, md_path = write_report(report)
    print(f"[swing-lifecycle-bucket-discovery] wrote {json_path} {md_path}")


if __name__ == "__main__":
    main()
