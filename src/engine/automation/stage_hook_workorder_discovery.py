"""Surface stage hook implementation workorders from source-only hook candidates."""

from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from src.engine.automation.dual_candidate_review import (
    evidence_authority_contract,
    REQUIRED_METRIC_CONTRACT_FIELDS,
    default_comparative_review,
    has_evidence_authority_violation,
    has_forbidden_runtime_leak,
    missing_metric_contract_fields,
    proposal_counts,
    with_evidence_authority_forbidden_uses,
)
from src.utils.constants import TRADING_RULES

PROJECT_ROOT = Path(__file__).resolve().parents[3]
REPORT_DIR = PROJECT_ROOT / "data" / "report"
REPORT_TYPE = "stage_hook_workorder_discovery"
REPORT_SCHEMA_VERSION = 1
DISCOVERY_VERSION = "stage_hook_workorder_discovery_v1"
AI_REVIEW_SCHEMA_NAME = "stage_hook_workorder_discovery_ai_review_v1"
AI_REVIEWER_NAME = "stage_hook_workorder_discovery_ai_review"
AI_REVIEW_MODEL = str(getattr(TRADING_RULES, "GPT_DEEP_MODEL", "gpt-5.4") or "gpt-5.4")
AI_REVIEW_DEFAULT_PROVIDER = "openai"
STAGE_HOOK_DUAL_DECISIONS = {
    "new_hook",
    "extend_existing_report_dimension",
    "source_quality_gap",
    "reject",
}

FORBIDDEN_USES = sorted(
    {
        "real order enablement",
        "threshold mutation",
        "provider change",
        "bot restart",
        "position cap release",
        "hard stop override",
        "protect stop override",
        "emergency stop override",
        "broker guard bypass",
        "account guard bypass",
        "order guard bypass",
        "quantity guard bypass",
        "cooldown guard bypass",
        "entry decision override",
        "exit decision override",
        "broker order submit",
    }
)
FORBIDDEN_USES = with_evidence_authority_forbidden_uses(FORBIDDEN_USES)

HOOK_CLASS_BY_PATTERN = {
    "sim_entry_selection_gap_missing": (
        "entry_policy_exception_router_candidate",
        "entry_policy_hook_candidate",
        "entry",
        ["ENTRY_REVIEW", "SIM_HANDOFF", "POLICY_COMPARE"],
        ["sim_entry_selection_bucket_producer", "time_window_regime_counterfactual"],
    ),
    "time_window_policy_exception_missing": (
        "entry_policy_exception_router_candidate",
        "entry_policy_hook_candidate",
        "entry",
        ["ENTRY_REVIEW", "SIM_HANDOFF", "POLICY_COMPARE"],
        ["time_window_regime_counterfactual"],
    ),
    "sim_time_window_exception_gap_missing": (
        "entry_policy_exception_router_candidate",
        "entry_policy_hook_candidate",
        "entry",
        ["ENTRY_REVIEW", "SIM_HANDOFF", "POLICY_COMPARE"],
        ["time_window_regime_counterfactual"],
    ),
    "sim_submit_fill_quality_gap_missing": (
        "submit_reprice_fill_quality_probe",
        "submit_quality_hook_candidate",
        "submit",
        ["SUBMIT_REVIEW", "REPRICE_REVIEW", "FILL_QUALITY_COMPARE"],
        ["submit_fill_quality_counterfactual_producer"],
    ),
    "missed_fill_recovery_counterfactual_missing": (
        "submit_reprice_fill_quality_probe",
        "submit_quality_hook_candidate",
        "submit",
        ["SUBMIT_REVIEW", "REPRICE_REVIEW", "FILL_QUALITY_COMPARE"],
        ["submit_fill_quality_counterfactual_producer"],
    ),
    "sim_holding_runner_gap_missing": (
        "holding_flow_runner_debounce_guard",
        "runtime_arbitration_hook",
        "holding",
        ["EXIT_CONFIRM", "HOLD_REVIEW", "TRIM"],
        ["runner_regime_counterfactual_producer"],
    ),
    "sim_exit_plateau_breakdown_gap_missing": (
        "plateau_breakdown_exit_arbitration_probe",
        "runtime_arbitration_hook",
        "exit",
        ["EXIT_CONFIRM", "TAKE_PROFIT_ON_PLATEAU", "HOLD_REVIEW"],
        ["plateau_breakdown_exit_counterfactual_producer"],
    ),
    "sim_stop_recovery_gap_missing": (
        "stop_recovery_review_probe",
        "runtime_arbitration_hook",
        "exit",
        ["EXIT_CONFIRM", "HOLD_REVIEW"],
        ["sim_stop_recovery_counterfactual_producer"],
    ),
    "sim_scale_in_counterfactual_gap_missing": (
        "scale_in_would_add_policy_probe",
        "scale_in_policy_hook_candidate",
        "scale_in",
        ["SCALE_IN_REVIEW", "WOULD_ADD_COMPARE", "KEEP_OR_TIGHTEN"],
        ["sim_scale_in_would_add_counterfactual_producer"],
    ),
    "scale_in_counterfactual_gap_missing": (
        "scale_in_would_add_policy_probe",
        "scale_in_policy_hook_candidate",
        "scale_in",
        ["SCALE_IN_REVIEW", "WOULD_ADD_COMPARE", "KEEP_OR_TIGHTEN"],
        ["sim_scale_in_would_add_counterfactual_producer"],
    ),
    "sim_source_quality_join_gap_missing": (
        "stage_source_provenance_join_hook",
        "source_schema_provenance_hook",
        "source_quality",
        ["SOURCE_SCHEMA_PATCH", "JOIN_QUALITY_REVIEW"],
        ["stage_source_join_quality_audit"],
    ),
}


def report_paths(target_date: str) -> tuple[Path, Path]:
    base = f"{REPORT_TYPE}_{target_date}"
    return REPORT_DIR / REPORT_TYPE / f"{base}.json", REPORT_DIR / REPORT_TYPE / f"{base}.md"


def producer_gap_report_path(target_date: str) -> Path:
    return REPORT_DIR / "producer_gap_discovery" / f"producer_gap_discovery_{target_date}.json"


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except Exception:
        return default


def _slug(text: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in str(text)).strip("_")[:96] or "unknown"


def _score_from_candidate(candidate: dict[str, Any]) -> tuple[float, dict[str, float], list[str], str]:
    sample_component = min(25.0, _safe_float(candidate.get("sample_count"), 0.0) * 1.5)
    evidence_text = " ".join(str(item) for item in candidate.get("evidence") or []).lower()
    strict = _safe_float(next((item.split("=", 1)[1] for item in candidate.get("evidence") or [] if str(item).startswith("strict_match_count=")), 0.0), 0.0)
    ambiguous = _safe_float(next((item.split("=", 1)[1] for item in candidate.get("evidence") or [] if str(item).startswith("ambiguous_match_count=")), 0.0), 0.0)
    entry_time_field_rate = _safe_float(
        next(
            (item.split("=", 1)[1] for item in candidate.get("evidence") or [] if str(item).startswith("entry_time_field_rate=")),
            1.0,
        ),
        1.0,
    )
    strict_component = min(25.0, strict * 2.0)
    recurrence_component = 15.0 if "top_symbols=" in evidence_text or strict >= 2 else 5.0
    ev_component = 20.0 if any(token in evidence_text for token in ("estimated_uplift", "expected_ev", "positive", "giveback")) else 6.0
    mapping_component = 15.0 if any(token in evidence_text for token in ("required_producer", "required_microstructure", "required_comparison")) else 8.0
    penalties = []
    risk_penalty = 0.0
    if ambiguous > strict and ambiguous > 0:
        risk_penalty += 15.0
        penalties.append("ambiguous_chronology_penalty")
    if "entry_time_field_rate=" in evidence_text and entry_time_field_rate < 0.2:
        risk_penalty += 40.0
        penalties.append("entry_time_provenance_penalty")
    source_quality_score = max(0.0, 100.0 - risk_penalty - min(30.0, ambiguous * 4.0))
    score = max(0.0, min(100.0, sample_component + strict_component + recurrence_component + ev_component + mapping_component - risk_penalty))
    components = {
        "sample": sample_component,
        "strict_chronology": strict_component,
        "recurrence": recurrence_component,
        "ev_signal": ev_component,
        "hook_mapping_readiness": mapping_component,
        "source_quality_score": source_quality_score,
    }
    if "entry_time_provenance_penalty" in penalties or source_quality_score < 55.0:
        tier = "blocked_by_source_quality"
    elif score >= 70.0:
        tier = "implementation_workorder_ready"
    elif score >= 55.0:
        tier = "hook_design_ready"
    elif score >= 35.0:
        tier = "producer_needed"
    else:
        tier = "observe_only"
    return score, components, penalties, tier


def _contract_from_candidate(candidate: dict[str, Any]) -> dict[str, Any] | None:
    pattern_type = str(candidate.get("pattern_type") or "")
    runtime_contract = candidate.get("runtime_hook_candidate_contract")
    if isinstance(runtime_contract, dict) and runtime_contract.get("hook_name"):
        hook_name = str(runtime_contract.get("hook_name"))
        hook_class = "runtime_arbitration_hook"
        stage = str(runtime_contract.get("stage") or candidate.get("lifecycle_stage") or "holding_exit")
        action_namespace = list(runtime_contract.get("action_namespace") or [])
        required_artifacts = list(runtime_contract.get("required_source_artifacts") or [])
    elif pattern_type in HOOK_CLASS_BY_PATTERN:
        hook_name, hook_class, stage, action_namespace, required_artifacts = HOOK_CLASS_BY_PATTERN[pattern_type]
    else:
        return None
    score, components, penalties, tier = _score_from_candidate(candidate)
    if hook_class == "source_schema_provenance_hook" and tier == "implementation_workorder_ready":
        tier = "hook_design_ready"
    return {
        "hook_name": hook_name,
        "hook_class": hook_class,
        "stage": stage,
        "initial_authority": "source_only_proposal",
        "apply_boundary": "postclose_workorder_only_requires_separate_runtime_apply_candidate",
        "action_namespace": action_namespace,
        "action_namespace_scope": "review_only_labels_not_runtime_actions",
        "source_candidate_id": candidate.get("candidate_id"),
        "source_pattern_type": pattern_type,
        "source_report_type": "producer_gap_discovery",
        "required_source_artifacts": required_artifacts,
        "required_mapping_tests": [
            "hook_input_output_contract_test",
            "forbidden_use_authority_test",
            "disabled_initial_runtime_state_test",
        ],
        "rollback_guard_requirements": [
            "hard_safety_veto_preserved",
            "broker_account_order_quantity_cooldown_veto_preserved",
            "post_apply_attribution_breach_guard_defined",
        ],
        "evidence_score": round(score, 4),
        "readiness_tier": tier,
        "score_components": components,
        "risk_penalties": penalties,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "forbidden_action_namespace_runtime_effect": True,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "forbidden_uses": FORBIDDEN_USES,
        "evidence_authority_contract": evidence_authority_contract(),
    }


def _deterministic_proposal(candidate: dict[str, Any]) -> dict[str, Any]:
    candidate_id = str(candidate.get("candidate_id") or "unknown")
    contract = candidate.get("stage_hook_candidate_contract") if isinstance(candidate.get("stage_hook_candidate_contract"), dict) else {}
    readiness = str(contract.get("readiness_tier") or candidate.get("readiness_tier") or "")
    if readiness == "blocked_by_source_quality":
        decision = "source_quality_gap"
    elif readiness == "implementation_workorder_ready":
        decision = "new_hook"
    else:
        decision = "extend_existing_report_dimension"
    return {
        "candidate_id": candidate_id,
        "proposal_source": "deterministic",
        "proposal_decision": decision,
        "recommended_canonical_bucket": f"stage_hook:{contract.get('stage')}:{contract.get('hook_name')}",
        "recommended_metric_or_dimension": [
            "source_quality_adjusted_ev_pct",
            "diagnostic_win_rate",
            f"{contract.get('hook_name')}_source_dimension",
        ],
        "reasoning_summary": "Deterministic stage-hook detector mapped producer gaps to source-only hook workorder readiness.",
        "confidence": "high" if readiness == "implementation_workorder_ready" else "medium",
        "required_source_fields": list(REQUIRED_METRIC_CONTRACT_FIELDS),
        "forbidden_uses": list(FORBIDDEN_USES),
        "evidence_authority_contract": evidence_authority_contract(),
        "workorder_title": f"Review stage hook: {contract.get('hook_name')}",
        "workorder_priority": str(candidate.get("priority") or "medium"),
    }


def _default_ai_proposal(candidate: dict[str, Any]) -> dict[str, Any]:
    deterministic = candidate.get("deterministic_proposal") if isinstance(candidate.get("deterministic_proposal"), dict) else {}
    return {
        "candidate_id": str(candidate.get("candidate_id") or "unknown"),
        "proposal_source": "ai_tier2",
        "proposal_status": "not_provided",
        "proposal_decision": "reject",
        "recommended_canonical_bucket": deterministic.get("recommended_canonical_bucket") or "",
        "recommended_metric_or_dimension": deterministic.get("recommended_metric_or_dimension") or [],
        "reasoning_summary": "AI Tier2 hook proposal unavailable; fail-closed comparative review remains source-only.",
        "confidence": "low",
        "required_source_fields": list(REQUIRED_METRIC_CONTRACT_FIELDS),
        "forbidden_uses": list(FORBIDDEN_USES),
        "evidence_authority_contract": evidence_authority_contract(),
    }


def _attach_deterministic_proposals(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{**candidate, "deterministic_proposal": _deterministic_proposal(candidate)} for candidate in candidates]


def _deterministic_candidates(target_date: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    producer_gap = _load_json(producer_gap_report_path(target_date))
    candidates_by_hook: dict[str, dict[str, Any]] = {}
    consumed_ids = []
    for item in producer_gap.get("producer_gap_candidates") or []:
        if not isinstance(item, dict):
            continue
        contract = _contract_from_candidate(item)
        if not contract:
            continue
        source_candidate_id = str(item.get("candidate_id") or "unknown")
        consumed_ids.append(source_candidate_id)
        hook_name = str(contract["hook_name"])
        existing = candidates_by_hook.get(hook_name)
        if existing:
            existing_contract = existing["stage_hook_candidate_contract"]
            source_ids = list(existing_contract.get("source_candidate_ids") or [])
            if source_candidate_id not in source_ids:
                source_ids.append(source_candidate_id)
            existing_contract["source_candidate_ids"] = source_ids
            existing_contract["source_candidate_id"] = source_ids[0] if source_ids else source_candidate_id
            existing_contract["source_pattern_types"] = sorted(
                set(existing_contract.get("source_pattern_types") or [existing_contract.get("source_pattern_type")])
                | {str(contract.get("source_pattern_type") or "")}
            )
            merged_evidence = list(existing.get("evidence") or [])
            for evidence in list(item.get("evidence") or [])[:16]:
                if evidence not in merged_evidence:
                    merged_evidence.append(evidence)
            existing["evidence"] = merged_evidence[:24]
            existing["source_candidate_ids"] = source_ids
            if contract.get("readiness_tier") == "implementation_workorder_ready":
                existing_contract["readiness_tier"] = "implementation_workorder_ready"
                existing["readiness_tier"] = "implementation_workorder_ready"
                existing["priority"] = "high"
            continue
        contract["source_candidate_ids"] = [source_candidate_id]
        contract["source_pattern_types"] = [str(contract.get("source_pattern_type") or "")]
        candidates_by_hook[hook_name] = {
            "candidate_id": f"stage_hook_{_slug(hook_name)}",
            "hook_name": contract["hook_name"],
            "hook_class": contract["hook_class"],
            "stage": contract["stage"],
            "priority": "high" if contract["readiness_tier"] == "implementation_workorder_ready" else "medium",
            "readiness_tier": contract["readiness_tier"],
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "stage_hook_candidate_contract": contract,
            "source_candidate_ids": [source_candidate_id],
            "evidence": list(item.get("evidence") or [])[:16],
            "source_paths": [str(producer_gap_report_path(target_date))],
        }
    candidates = _attach_deterministic_proposals(list(candidates_by_hook.values()))
    return candidates, {
        "producer_gap_artifact": str(producer_gap_report_path(target_date)),
        "producer_gap_status": producer_gap.get("status"),
        "producer_gap_candidate_count": len(producer_gap.get("producer_gap_candidates") or []),
        "consumed_candidate_ids": consumed_ids,
    }


def _build_ai_review_instructions() -> str:
    return (
        "You are stage_hook_workorder_discovery_ai_review, a Tier2 source-only stage hook reviewer.\n"
        "Use a two-pass process: first interpretation, second review, final conclusion.\n"
        "Review deterministic stage hook candidates and strengthen implementation requirements and acceptance tests.\n"
        "Create an independent ai_tier2_proposal for each deterministic candidate, then create a comparative_review "
        "that compares deterministic_proposal and ai_tier2_proposal side by side.\n"
        "AI proposal decisions are limited to new_hook, extend_existing_report_dimension, source_quality_gap, or reject. "
        "The comparative selected_source must be deterministic, ai_tier2, hybrid, or reject.\n"
        "Metric/dimension absorption requires metric_role, decision_authority, window_policy, sample_floor, "
        "primary_decision_metric, source_quality_gate, and forbidden_uses in required_source_fields.\n"
        "For every ai_tier2_proposal and comparative_review, required_source_fields must contain all seven exact "
        "strings: metric_role, decision_authority, window_policy, sample_floor, primary_decision_metric, "
        "source_quality_gate, forbidden_uses. Do not substitute field examples for this contract list.\n"
        "Do not delete deterministic candidates. Do not grant runtime, threshold, provider, bot, cap, broker order, "
        "entry override, exit override, or safety-bypass authority.\n"
        "Action namespace values are review-only labels when action_namespace_scope is "
        "review_only_labels_not_runtime_actions and allowed_runtime_apply is false; do not treat those labels as "
        "forbidden-use violations unless the contract grants direct runtime authority.\n"
        "Scores are evidence inputs, not hard gates. Treat readiness_tier as a source-only workorder routing state.\n"
        "Evidence authority contract: bucket/dimension tuning primary evidence is sim/probe lifecycle EV. "
        "Real one-share samples are not primary EV evidence unless the mapped bucket policy was already enabled "
        "for the evaluated post-apply cohort. Pre-apply real samples may be used only for execution-quality "
        "calibration, safety veto, provenance validation, and broker/fill/slippage source-quality checks. "
        "Do not merge real PnL with sim/probe EV and do not promote runtime threshold/order/provider/cap/bot "
        "changes from pre-apply real one-share outcomes. If a proposal violates this contract, select reject or "
        "source_quality_gap.\n"
        "If forbidden-use authority is present, report it in audit.forbidden_use_violations.\n"
        "Return strict JSON conforming to stage_hook_workorder_discovery_ai_review_v1."
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
    warnings = []
    if payload.get("schema_version") != 1:
        warnings.append("ai_review_schema_version_invalid")
    if payload.get("reviewer") != AI_REVIEWER_NAME:
        warnings.append("ai_review_reviewer_invalid")
    if not isinstance(payload.get("candidate_reviews"), list):
        warnings.append("ai_review_candidate_reviews_missing")
    if not isinstance(payload.get("ai_tier2_proposals"), list):
        warnings.append("ai_review_ai_tier2_proposals_missing")
    if not isinstance(payload.get("comparative_reviews"), list):
        warnings.append("ai_review_comparative_reviews_missing")
    for item in payload.get("ai_tier2_proposals") or []:
        if not isinstance(item, dict):
            warnings.append("ai_review_ai_tier2_proposal_invalid")
            continue
        if str(item.get("proposal_decision") or "") not in STAGE_HOOK_DUAL_DECISIONS:
            warnings.append(f"ai_review_ai_proposal_decision_invalid:{item.get('candidate_id')}")
        missing_contract = missing_metric_contract_fields(item.get("required_source_fields"))
        if missing_contract:
            warnings.append(f"ai_review_ai_proposal_contract_missing:{item.get('candidate_id')}:{','.join(missing_contract)}")
        if has_forbidden_runtime_leak(item):
            warnings.append(f"ai_review_ai_proposal_forbidden_use_leak:{item.get('candidate_id')}")
        if has_evidence_authority_violation(item):
            warnings.append(f"ai_review_ai_proposal_evidence_authority_violation:{item.get('candidate_id')}")
    proposal_ids = {
        str(item.get("candidate_id"))
        for item in payload.get("ai_tier2_proposals") or []
        if isinstance(item, dict) and item.get("candidate_id")
    }
    review_ids = {
        str(item.get("candidate_id"))
        for item in payload.get("comparative_reviews") or []
        if isinstance(item, dict) and item.get("candidate_id")
    }
    if proposal_ids and proposal_ids - review_ids:
        warnings.append("ai_review_comparative_review_missing_for_ai_proposal")
    for item in payload.get("comparative_reviews") or []:
        if not isinstance(item, dict):
            warnings.append("ai_review_comparative_review_invalid")
            continue
        if str(item.get("selected_decision") or "") not in STAGE_HOOK_DUAL_DECISIONS:
            warnings.append(f"ai_review_comparative_decision_invalid:{item.get('candidate_id')}")
        if str(item.get("selected_source") or "") not in {"deterministic", "ai_tier2", "hybrid", "reject"}:
            warnings.append(f"ai_review_comparative_source_invalid:{item.get('candidate_id')}")
        missing_contract = missing_metric_contract_fields(item.get("required_source_fields"))
        if missing_contract:
            warnings.append(f"ai_review_comparative_contract_missing:{item.get('candidate_id')}:{','.join(missing_contract)}")
        if has_forbidden_runtime_leak(item):
            warnings.append(f"ai_review_comparative_forbidden_use_leak:{item.get('candidate_id')}")
        if has_evidence_authority_violation(item):
            warnings.append(f"ai_review_comparative_evidence_authority_violation:{item.get('candidate_id')}")
    audit = payload.get("audit") if isinstance(payload.get("audit"), dict) else {}
    if str(audit.get("status") or "") not in {"pass", "correction_required", "insufficient_context"}:
        warnings.append("ai_review_audit_status_invalid")
    if not isinstance(audit.get("forbidden_use_violations"), list):
        warnings.append("ai_review_forbidden_use_violations_missing")
    if warnings:
        return "parse_rejected", payload, warnings
    return "parsed", payload, []


def _review_map(ai_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(item.get("candidate_id")): item
        for item in ai_payload.get("candidate_reviews") or []
        if isinstance(item, dict) and item.get("candidate_id")
    }


def _proposal_map(ai_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(item.get("candidate_id")): {**item, "proposal_source": "ai_tier2", "proposal_status": "provided"}
        for item in ai_payload.get("ai_tier2_proposals") or []
        if isinstance(item, dict) and item.get("candidate_id")
    }


def _comparative_map(ai_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(item.get("candidate_id")): item
        for item in ai_payload.get("comparative_reviews") or []
        if isinstance(item, dict) and item.get("candidate_id")
    }


def _order_from_candidate(
    candidate: dict[str, Any],
    review: dict[str, Any],
    *,
    ai_tier2_proposal: dict[str, Any] | None = None,
    comparative_review: dict[str, Any] | None = None,
) -> dict[str, Any]:
    contract = candidate["stage_hook_candidate_contract"]
    priority = str(review.get("priority") or candidate.get("priority") or "high")
    return {
        "order_id": f"order_{REPORT_TYPE}_{_slug(str(candidate.get('candidate_id')))}",
        "title": f"Implement stage hook: {contract['hook_name']}",
        "source_report_type": REPORT_TYPE,
        "lifecycle_stage": contract.get("stage"),
        "target_subsystem": review.get("target_subsystem") or f"stage_hook.{contract['hook_name']}",
        "route": "implement_now",
        "priority": 1 if priority in {"critical", "high"} else 2,
        "stage_hook_priority": priority,
        "confidence": review.get("confidence") or "ai_tier2_review",
        "improvement_type": contract.get("hook_name"),
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "initial_runtime_state": "disabled",
        "requires_separate_runtime_apply_candidate": True,
        "decision_authority": "stage_hook_workorder_source_only",
        "intent": review.get("reason") or "Implement a disabled source-only stage hook scaffold after producer evidence surfaced readiness.",
        "expected_ev_effect": "none_direct_until_separate_runtime_apply_candidate",
        "evidence": list(candidate.get("evidence") or []) + [f"readiness_tier={contract.get('readiness_tier')}"],
        "files_likely_touched": review.get("files_likely_touched")
        or ["src/engine/automation/stage_hook_workorder_discovery.py", "src/engine/build_code_improvement_workorder.py"],
        "acceptance_tests": review.get("acceptance_tests")
        or ["stage hook starts disabled/source-only", "forbidden uses remain blocked"],
        "implementation_requirements": review.get("implementation_requirements") or [],
        "stage_hook_candidate_contract": contract,
        "evidence_authority_contract": evidence_authority_contract(),
        "canonical_bucket": comparative_review.get("recommended_canonical_bucket") if isinstance(comparative_review, dict) else None,
        "legacy_raw_bucket_key": contract.get("hook_name"),
        "deterministic_proposal": candidate.get("deterministic_proposal"),
        "ai_tier2_proposal": ai_tier2_proposal or {},
        "comparative_review": comparative_review or {},
    }


def build_stage_hook_workorder_discovery_report(
    target_date: str,
    *,
    provider: str | None = None,
    ai_raw_response: Any | None = None,
) -> dict[str, Any]:
    target_date = str(target_date).strip()
    resolved_provider = str(provider if provider is not None else os.getenv("KORSTOCKSCAN_STAGE_HOOK_WORKORDER_DISCOVERY_AI_PROVIDER", AI_REVIEW_DEFAULT_PROVIDER)).strip().lower() or "none"
    candidates, context = _deterministic_candidates(target_date)
    provider_status: dict[str, Any] = {"provider": resolved_provider, "status": "disabled" if resolved_provider in {"none", "off", "false", "0"} else "not_called", "model": AI_REVIEW_MODEL if resolved_provider not in {"none", "off", "false", "0"} else None}
    raw_response = ai_raw_response
    if raw_response is None and resolved_provider == "openai":
        raw_response, provider_status = _call_openai_ai_review({"date": target_date, "candidates": candidates, "context": context})
    ai_status, ai_payload, ai_warnings = _parse_ai_review_response(raw_response)
    audit = ai_payload.get("audit") if isinstance(ai_payload.get("audit"), dict) else {}
    forbidden = audit.get("forbidden_use_violations")
    if not isinstance(forbidden, list):
        forbidden = []
    reviews = _review_map(ai_payload) if ai_status == "parsed" else {}
    proposals = _proposal_map(ai_payload) if ai_status == "parsed" else {}
    comparatives = _comparative_map(ai_payload) if ai_status == "parsed" else {}
    candidate_ids = {str(item.get("candidate_id") or "") for item in candidates}
    missing_ai_proposal_count = len([candidate_id for candidate_id in candidate_ids if candidate_id not in proposals])
    missing_comparative_review_count = len([candidate_id for candidate_id in candidate_ids if candidate_id not in comparatives])
    fail_closed = (
        ai_status != "parsed"
        or audit.get("status") != "pass"
        or bool(forbidden)
        or missing_ai_proposal_count > 0
        or missing_comparative_review_count > 0
    )
    reviewed = []
    orders = []
    for candidate in candidates:
        candidate_id = str(candidate.get("candidate_id") or "")
        review = reviews.get(candidate_id) or {}
        deterministic_proposal = (
            candidate.get("deterministic_proposal") if isinstance(candidate.get("deterministic_proposal"), dict) else {}
        )
        ai_tier2_proposal = proposals.get(candidate_id) or _default_ai_proposal(candidate)
        comparative_review = comparatives.get(candidate_id) or default_comparative_review(
            candidate_id=candidate_id,
            deterministic_proposal=deterministic_proposal,
            ai_tier2_proposal=ai_tier2_proposal,
            allowed_decisions=STAGE_HOOK_DUAL_DECISIONS,
            default_decision="extend_existing_report_dimension",
            workorder_title=f"Review stage hook: {candidate.get('hook_name')}",
        )
        if ai_status != "parsed":
            comparative_review = {**comparative_review, "selected_decision": "source_quality_gap", "selected_source": "reject"}
        merged = {
            **candidate,
            "ai_review": review,
            "ai_tier2_proposal": ai_tier2_proposal,
            "comparative_review": comparative_review,
            "ai_review_status": ai_status,
            "ai_priority": review.get("priority") or candidate.get("priority"),
            "ai_recommended_tier": review.get("recommended_readiness_tier")
            or candidate.get("stage_hook_candidate_contract", {}).get("readiness_tier"),
        }
        reviewed.append(merged)
        contract = candidate["stage_hook_candidate_contract"]
        priority = str(merged.get("ai_priority") or "medium")
        if (
            not fail_closed
            and contract.get("readiness_tier") == "implementation_workorder_ready"
            and comparative_review.get("selected_decision") not in {"reject", "source_quality_gap"}
            and priority in {"critical", "high", "medium"}
        ):
            orders.append(_order_from_candidate(candidate, review, ai_tier2_proposal=ai_tier2_proposal, comparative_review=comparative_review))
    status = "fail" if fail_closed else ("warning" if orders else "pass")
    tier_counts = Counter(str(item.get("stage_hook_candidate_contract", {}).get("readiness_tier") or "unknown") for item in candidates)
    class_counts = Counter(str(item.get("hook_class") or "unknown") for item in candidates)
    report = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "report_type": REPORT_TYPE,
        "discovery_version": DISCOVERY_VERSION,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "runtime_mutation_allowed": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "decision_authority": "stage_hook_workorder_discovery_source_only",
        "metric_role": "source_quality_gate",
        "window_policy": "postclose_stage_hook_workorder_review",
        "primary_decision_metric": "source_quality_adjusted_ev_pct",
        "source_quality_gate": "producer gap artifact exists and parsed Tier2 review passed",
        "forbidden_uses": FORBIDDEN_USES,
        "evidence_authority_contract": evidence_authority_contract(),
        "status": status,
        "sources": {"producer_gap_discovery": str(producer_gap_report_path(target_date)) if producer_gap_report_path(target_date).exists() else None},
        "summary": {
            "status": status,
            "candidate_count": len(candidates),
            "workorder_count": len(orders),
            "deterministic_proposal_count": len(candidates),
            "ai_tier2_proposal_count": sum(
                1 for item in reviewed if item.get("ai_tier2_proposal", {}).get("proposal_status") == "provided"
            ),
            "comparative_review_count": len(reviewed),
            "missing_ai_tier2_proposal_count": missing_ai_proposal_count,
            "missing_comparative_review_count": missing_comparative_review_count,
            "selected_decision_counts": proposal_counts(
                [item.get("comparative_review") or {} for item in reviewed],
                key="selected_decision",
            ),
            "selected_source_counts": proposal_counts(
                [item.get("comparative_review") or {} for item in reviewed],
                key="selected_source",
            ),
            "readiness_tier_counts": dict(tier_counts),
            "hook_class_counts": dict(class_counts),
            "ai_two_pass_review_status": ai_status,
            "audit_status": audit.get("status"),
            "ai_fail_closed": fail_closed,
            "provider": resolved_provider,
            "model": provider_status.get("model") or (AI_REVIEW_MODEL if resolved_provider == "openai" else None),
            "human_intervention_required": False,
        },
        "context": context,
        "ai_two_pass_review": {
            "provider": resolved_provider,
            "status": ai_status,
            "model": provider_status.get("model") or (AI_REVIEW_MODEL if resolved_provider == "openai" else None),
            "schema_name": AI_REVIEW_SCHEMA_NAME,
            "provider_status": provider_status,
            "audit": audit,
            "candidate_reviews": ai_payload.get("candidate_reviews") if isinstance(ai_payload.get("candidate_reviews"), list) else [],
            "deterministic_proposals": [
                item.get("deterministic_proposal") for item in reviewed if item.get("deterministic_proposal")
            ],
            "ai_tier2_proposals": [
                item.get("ai_tier2_proposal") for item in reviewed if item.get("ai_tier2_proposal")
            ],
            "comparative_reviews": [
                item.get("comparative_review") for item in reviewed if item.get("comparative_review")
            ],
            "warnings": ai_warnings,
            "fail_closed": fail_closed,
            "missing_ai_tier2_proposal_count": missing_ai_proposal_count,
            "missing_comparative_review_count": missing_comparative_review_count,
        },
        "deterministic_proposals": [
            item.get("deterministic_proposal") for item in reviewed if item.get("deterministic_proposal")
        ],
        "ai_tier2_proposals": [
            item.get("ai_tier2_proposal") for item in reviewed if item.get("ai_tier2_proposal")
        ],
        "comparative_reviews": [
            item.get("comparative_review") for item in reviewed if item.get("comparative_review")
        ],
        "selected_decision_counts": proposal_counts(
            [item.get("comparative_review") or {} for item in reviewed],
            key="selected_decision",
        ),
        "selected_source_counts": proposal_counts(
            [item.get("comparative_review") or {} for item in reviewed],
            key="selected_source",
        ),
        "stage_hook_candidates": reviewed,
        "code_improvement_orders": orders,
    }
    json_path, md_path = report_paths(target_date)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return report


def render_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    lines = [
        f"# Stage Hook Workorder Discovery - {report.get('date')}",
        "",
        "## Summary",
        "",
        f"- status: `{report.get('status')}`",
        f"- runtime_effect: `{report.get('runtime_effect')}`",
        f"- allowed_runtime_apply: `{report.get('allowed_runtime_apply')}`",
        f"- candidates: `{summary.get('candidate_count')}`",
        f"- workorders: `{summary.get('workorder_count')}`",
        f"- ai_two_pass_review_status: `{summary.get('ai_two_pass_review_status')}`",
        f"- audit_status: `{summary.get('audit_status')}`",
        f"- readiness_tier_counts: `{summary.get('readiness_tier_counts') or {}}`",
        "",
        "## Candidates",
        "",
    ]
    for item in report.get("stage_hook_candidates") or []:
        contract = item.get("stage_hook_candidate_contract") if isinstance(item.get("stage_hook_candidate_contract"), dict) else {}
        lines.extend(
            [
                f"### `{item.get('candidate_id')}`",
                f"- hook_name: `{contract.get('hook_name') or '-'}`",
                f"- hook_class: `{contract.get('hook_class') or '-'}`",
                f"- stage: `{contract.get('stage') or '-'}`",
                f"- readiness_tier: `{contract.get('readiness_tier') or '-'}`",
                f"- evidence_score: `{contract.get('evidence_score')}`",
                f"- forbidden_uses: `{', '.join(contract.get('forbidden_uses') or [])}`",
                "",
            ]
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build stage hook workorder discovery report.")
    parser.add_argument("--date", required=True)
    parser.add_argument("--provider", default=os.getenv("KORSTOCKSCAN_STAGE_HOOK_WORKORDER_DISCOVERY_AI_PROVIDER", AI_REVIEW_DEFAULT_PROVIDER))
    parser.add_argument("--ai-response-json", default=None)
    args = parser.parse_args()
    raw = None
    if args.ai_response_json:
        raw = Path(args.ai_response_json).read_text(encoding="utf-8")
    report = build_stage_hook_workorder_discovery_report(args.date, provider=args.provider, ai_raw_response=raw)
    print(json.dumps({"status": report.get("status"), "json": str(report_paths(args.date)[0]), "md": str(report_paths(args.date)[1])}, ensure_ascii=False))
    if report.get("status") == "fail":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
