"""Source-only dual candidate proposal helpers for automation reports."""

from __future__ import annotations

from collections import Counter
from typing import Any


REQUIRED_METRIC_CONTRACT_FIELDS = (
    "metric_role",
    "decision_authority",
    "window_policy",
    "sample_floor",
    "primary_decision_metric",
    "source_quality_gate",
    "forbidden_uses",
)

EVIDENCE_AUTHORITY_FORBIDDEN_USES = (
    "real_1share_as_preapply_primary_ev",
    "real_one_share_as_preapply_primary_ev",
    "merge_real_pnl_with_sim_probe_ev",
    "runtime_change_from_preapply_real_sample",
)


def evidence_authority_contract() -> dict[str, Any]:
    return {
        "primary_evidence_source": "sim_probe_lifecycle_ev",
        "real_sample_primary_ev_allowed_before_mapped_policy_enabled": False,
        "real_sample_allowed_roles_before_mapped_policy_enabled": [
            "execution_quality_calibration",
            "safety_veto",
            "provenance_validation",
        ],
        "real_sample_allowed_role_after_mapped_policy_enabled": "post_apply_attribution",
        "mapped_runtime_policy_enabled_field": "mapped_runtime_policy_enabled",
        "forbidden_uses": list(EVIDENCE_AUTHORITY_FORBIDDEN_USES),
    }


def with_evidence_authority_forbidden_uses(values: Any) -> list[str]:
    merged: list[str] = []
    for value in list(values or []) + list(EVIDENCE_AUTHORITY_FORBIDDEN_USES):
        text = str(value).strip()
        if text and text not in merged:
            merged.append(text)
    return merged


def proposal_counts(items: list[dict[str, Any]], *, key: str) -> dict[str, int]:
    return dict(Counter(str(item.get(key) or "unknown") for item in items))


def missing_metric_contract_fields(fields: Any) -> list[str]:
    provided = {str(item) for item in fields or []}
    return [field for field in REQUIRED_METRIC_CONTRACT_FIELDS if field not in provided]


def default_comparative_review(
    *,
    candidate_id: str,
    deterministic_proposal: dict[str, Any],
    ai_tier2_proposal: dict[str, Any] | None,
    allowed_decisions: set[str],
    default_decision: str,
    workorder_title: str,
) -> dict[str, Any]:
    ai_proposal = ai_tier2_proposal if isinstance(ai_tier2_proposal, dict) else {}
    if ai_proposal.get("proposal_status") == "provided":
        selected_decision = str(ai_proposal.get("proposal_decision") or default_decision)
        selected_source = "ai_tier2"
        summary = "AI Tier2 proposal selected because no explicit comparative override was supplied."
    else:
        selected_decision = (
            "source_quality_blocker"
            if "source_quality_blocker" in allowed_decisions
            else "source_quality_gap"
            if "source_quality_gap" in allowed_decisions
            else default_decision
        )
        selected_source = "reject"
        summary = "AI Tier2 proposal was unavailable; candidate-level comparative review failed closed."
    if selected_decision not in allowed_decisions:
        selected_decision = "source_quality_blocker" if "source_quality_blocker" in allowed_decisions else default_decision
        selected_source = "reject"
        summary = "Invalid proposal decision forced fail-closed review."
    return {
        "candidate_id": candidate_id,
        "selected_decision": selected_decision,
        "selected_source": selected_source,
        "recommended_canonical_bucket": deterministic_proposal.get("recommended_canonical_bucket", ""),
        "recommended_metric_or_dimension": deterministic_proposal.get("recommended_metric_or_dimension") or [],
        "comparison_summary": summary,
        "rejected_alternative_reason": "",
        "confidence": ai_proposal.get("confidence") or deterministic_proposal.get("confidence") or "medium",
        "required_source_fields": ai_proposal.get("required_source_fields")
        or deterministic_proposal.get("required_source_fields")
        or list(REQUIRED_METRIC_CONTRACT_FIELDS),
        "forbidden_uses": ai_proposal.get("forbidden_uses") or deterministic_proposal.get("forbidden_uses") or [],
        "workorder_title": workorder_title,
        "workorder_priority": deterministic_proposal.get("workorder_priority") or "medium",
    }


def has_forbidden_runtime_leak(payload: dict[str, Any]) -> bool:
    text = " ".join(str(item).lower() for item in payload.get("forbidden_uses") or [])
    return any(
        marker in text
        for marker in (
            "runtime_threshold_mutation_allowed",
            "broker_order_allowed",
            "provider_route_change_allowed",
            "bot_restart_allowed",
            "cap_release_allowed",
        )
    )


def has_evidence_authority_violation(payload: dict[str, Any]) -> bool:
    searchable = {
        key: value
        for key, value in payload.items()
        if key not in {"evidence_authority_contract", "forbidden_uses", "required_source_fields"}
    }
    text = str(searchable).lower().replace("-", "_")
    if "real_sample_primary_ev_allowed" in text and "true" in text:
        return True
    if "mapped_runtime_policy_enabled" in text and "false" in text and "primary_ev" in text and "real" in text:
        return True
    if "preapply_real" in text and "primary_ev" in text:
        return True
    if "pre_apply_real" in text and "primary_ev" in text:
        return True
    if "pre apply real" in text and "primary ev" in text:
        return True
    if "real_1share_primary_ev" in text or "real_one_share_primary_ev" in text:
        return True
    if "real 1_share primary ev" in text or "real one_share primary ev" in text:
        return True
    if "merge_real_pnl_with_sim" in text or "merge real pnl with sim" in text:
        return True
    if "runtime_change_from_preapply_real" in text or "runtime change from preapply real" in text:
        return True
    return False
