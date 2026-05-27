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
