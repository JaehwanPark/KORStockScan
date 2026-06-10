"""Lifecycle bucket taxonomy normalization helpers.

This module is source-only taxonomy instrumentation.  It never grants runtime
authority; callers decide whether a normalized bucket only becomes a workorder.
"""

from __future__ import annotations

import re
from typing import Any


BUCKET_ALIAS_VERSION = "lifecycle_bucket_alias_v1"
DIMENSION_SET_VERSION = "lifecycle_dimension_set_v1"
ENTRY_SOURCE_PARENT_ALIAS_VERSION = "entry_source_parent_alias_v1"
REQUIRED_METRIC_CONTRACT_FIELDS = (
    "metric_role",
    "decision_authority",
    "window_policy",
    "sample_floor",
    "primary_decision_metric",
    "source_quality_gate",
    "forbidden_uses",
)
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

_NUMERIC_EMBEDDED_RE = re.compile(
    r"^(?P<name>[a-zA-Z_][a-zA-Z0-9_]*?)\((?P<value>[-+]?\d+(?:\.\d+)?)(?P<unit>%|pct|s|sec|seconds|bps)?\)$"
)
_SCORE_LT_RE = re.compile(r"\bscore[_=:]?lt[_-]?(?P<high>\d{1,3})\b")
_SCORE_BUCKET_RE = re.compile(
    r"\bscore(?:[_=:]score)?(?:[_=:])?(?P<low>\d{1,3})(?:[_-](?P<high>\d{1,3}|p))?(?=\D|$)"
)

ENTRY_SOURCE_PARENT_ALIASES = (
    ("first_ai_wait", "entry_source_wait6579", "alias_of_wait6579_counterfactual"),
    ("wait6579", "entry_source_wait6579", "canonical_wait6579_counterfactual"),
    ("blocked_ai_score", "entry_source_blocked_ai_score", "canonical_blocked_ai_score"),
    ("scalp_entry_action_decision", "entry_source_action_decision", "canonical_action_decision"),
    ("action_decision", "entry_source_action_decision", "alias_of_action_decision"),
    ("scalp_sim", "entry_source_scalp_sim", "canonical_scalp_sim"),
    ("panic", "entry_source_panic", "canonical_panic"),
)


def _safe_float(value: Any) -> float | None:
    try:
        number = float(value)
    except Exception:
        return None
    return number if number == number else None


def _duration_bucket(seconds: float) -> str:
    if seconds < 60:
        return "lt_1m"
    if seconds < 300:
        return "1_5m"
    if seconds < 600:
        return "5_10m"
    if seconds < 1800:
        return "10_30m"
    if seconds < 3600:
        return "30_60m"
    return "60m_plus"


def _pct_bucket(value: float) -> str:
    if value <= -5:
        return "minus_5pct_or_lower"
    if value <= -2:
        return "minus_2_to_5pct"
    if value < -1:
        return "minus_1_to_2pct"
    if value < 0:
        return "minus_0_to_1pct"
    if value < 1:
        return "plus_0_to_1pct"
    if value < 2:
        return "plus_1_to_2pct"
    if value < 5:
        return "plus_2_to_5pct"
    return "plus_5pct_or_higher"


def _metric_name_for(base: str, unit: str) -> str:
    if "hold" in base and unit in {"s", "sec", "seconds"}:
        return "hold_sec"
    if "pnl" in base or "profit" in base:
        return "pnl_delta_pct"
    if unit == "bps":
        return f"{base}_bps"
    if unit in {"%", "pct"}:
        return f"{base}_pct"
    return f"{base}_value"


def _score_parent(value: Any) -> str | None:
    text = str(value or "").lower()
    lt_match = _SCORE_LT_RE.search(text)
    if lt_match:
        high = _safe_float(lt_match.group("high"))
        if high is None:
            return None
        return "score_low_observation" if high <= 60 else "score_watch_recovery"
    match = _SCORE_BUCKET_RE.search(text)
    if not match:
        return None
    low = _safe_float(match.group("low"))
    high_raw = match.group("high")
    high = _safe_float(match.group("low")) if high_raw == "p" else _safe_float(high_raw or match.group("low"))
    if low is None or high is None:
        return None
    midpoint = (low + high) / 2.0
    if midpoint < 55:
        return "score_low_observation"
    if midpoint < 65:
        return "score_watch_recovery"
    if midpoint < 75:
        return "score_mid_recovery"
    if midpoint < 85:
        return "score_high_confirmation"
    return "score_extreme_confirmation"


def _stage_parent_from_child(stage: str, value: Any) -> str:
    text = str(value or "").strip()
    score_parent = _score_parent(text)
    if score_parent:
        return score_parent
    if not text or text.lower() in {"none", "missing", "null"}:
        return "none"
    return f"{stage}_observed"


def _is_missing_unknown_dimension_value(value: Any) -> bool:
    text = str(value or "").strip().lower()
    if text in {"", "unknown", "missing", "none", "null"}:
        return True
    return text.endswith(":unknown") or text.endswith(":missing")


def normalize_entry_source_parent(value: Any) -> dict[str, Any]:
    """Normalize runtime/discovery entry source labels without dropping rows."""
    raw = str(value or "").strip()
    text = raw.lower()
    if not text or text in {"-", "missing", "none", "null"}:
        return {
            "parent": "entry_missing",
            "raw_value": raw,
            "alias_version": ENTRY_SOURCE_PARENT_ALIAS_VERSION,
            "contract_state": "missing_source",
            "reason": "entry_source_missing",
            "consume_data": True,
            "runtime_effect_allowed": False,
        }
    for token, parent, reason in ENTRY_SOURCE_PARENT_ALIASES:
        if token in text:
            return {
                "parent": parent,
                "raw_value": raw,
                "alias_version": ENTRY_SOURCE_PARENT_ALIAS_VERSION,
                "contract_state": "canonical_alias" if reason.startswith("alias_") else "canonical",
                "reason": reason,
                "consume_data": True,
                "runtime_effect_allowed": True,
            }
    return {
        "parent": "entry_source_observed_other",
        "raw_value": raw,
        "alias_version": ENTRY_SOURCE_PARENT_ALIAS_VERSION,
        "contract_state": "new_axis_pending_taxonomy",
        "reason": "entry_source_parent_taxonomy_not_declared",
        "consume_data": True,
        "runtime_effect_allowed": False,
    }


def _coarsen_dimensions_for_parent(
    *,
    stage: str,
    bucket_type: str,
    bucket_key: str,
    dimensions: dict[str, Any],
) -> tuple[str, dict[str, Any], str | None]:
    normalized = dict(dimensions)
    score_parent = None
    for key, value in list(dimensions.items()):
        parent = _score_parent(value)
        if parent:
            normalized[f"{key}_detail"] = str(value)
            normalized[f"{key}_parent"] = parent
            score_parent = score_parent or parent
    if not score_parent:
        score_parent = _score_parent(bucket_key)
        if score_parent:
            normalized["score_detail"] = str(bucket_key)
            normalized["score_parent"] = score_parent

    if bucket_type.startswith("combo_") and dimensions:
        parent_parts: list[str] = []
        for key in ("entry", "submit", "holding", "scale_in", "exit"):
            if key not in dimensions:
                continue
            value = dimensions.get(key)
            normalized[f"{key}_detail"] = str(value)
            parent_parts.append(f"{key}={_stage_parent_from_child(key, value)}")
        if parent_parts:
            return "|".join(parent_parts), normalized, "combo_bucket_rolled_up_to_broad_parent_dimensions"

    if score_parent and bucket_key != score_parent:
        normalized["bucket_detail"] = str(bucket_key)
        return score_parent, normalized, "score_bucket_rolled_up_to_parent_score_group"
    return bucket_key, normalized, None


def normalize_lifecycle_bucket(
    *,
    stage: str,
    bucket_type: str,
    bucket_key: str,
    source_dimensions: dict[str, Any] | None = None,
) -> dict[str, Any]:
    dimensions = {str(key): str(value) for key, value in (source_dimensions or {}).items()}
    legacy_raw = str(bucket_key or "unknown")
    canonical_key = legacy_raw
    metrics: dict[str, Any] = {}
    normalized_dimensions: dict[str, Any] = dict(dimensions)
    reason = "keep_existing_bucket"
    decision = "keep_bucket"
    candidate_type = "stable_existing_bucket"
    missing_dimensions: list[str] = []

    match = _NUMERIC_EMBEDDED_RE.match(legacy_raw)
    if match:
        base = match.group("name")
        unit = match.group("unit") or ""
        number = _safe_float(match.group("value"))
        canonical_key = base
        decision = "absorb_as_dimension"
        candidate_type = "numeric_embedded_bucket"
        reason = "numeric_value_moved_from_bucket_key_to_metric_dimension"
        if number is not None:
            metric_name = _metric_name_for(base, unit)
            metrics[metric_name] = number
            if metric_name == "hold_sec":
                normalized_dimensions["hold_duration_bucket"] = _duration_bucket(number)
            elif metric_name.endswith("_pct") or metric_name == "pnl_delta_pct":
                normalized_dimensions[f"{metric_name}_bucket"] = _pct_bucket(number)
            elif metric_name.endswith("_bps"):
                normalized_dimensions[f"{metric_name}_bucket"] = (
                    "not_below_bid"
                    if number <= 0
                    else "0_5bps"
                    if number <= 5
                    else "5_20bps"
                    if number <= 20
                    else "20bps_plus"
                )

    parent_key, parent_dimensions, parent_reason = _coarsen_dimensions_for_parent(
        stage=stage,
        bucket_type=bucket_type,
        bucket_key=canonical_key,
        dimensions=normalized_dimensions,
    )
    if parent_reason:
        canonical_key = parent_key
        normalized_dimensions = parent_dimensions
        decision = "absorb_as_dimension" if decision == "keep_bucket" else decision
        if decision == "merge":
            decision = "absorb_as_dimension"
        candidate_type = "parent_bucket_absorption"
        reason = parent_reason

    if "unknown" in legacy_raw.lower() or any(_is_missing_unknown_dimension_value(value) for value in dimensions.values()):
        missing_dimensions = sorted(
            {
                str(key)
                for key, value in dimensions.items()
                if _is_missing_unknown_dimension_value(value)
            }
        )
        if decision == "keep_bucket":
            decision = "instrumentation_gap"
            candidate_type = "missing_dimension"
            reason = "unknown_dimension_requires_source_contract_or_dimension_fix"

    if bucket_type.startswith("combo_") and decision == "keep_bucket":
        decision = "merge"
        candidate_type = "composite_bucket_refinement"
        reason = "composite_bucket_should_roll_up_to_parent_plus_dimensions"

    canonical_bucket = f"{stage}:{bucket_type}:{canonical_key}"
    proposal = {
        "proposal_source": "deterministic",
        "proposal_decision": decision,
        "candidate_type": candidate_type,
        "recommended_canonical_bucket": canonical_bucket,
        "recommended_metric_or_dimension": sorted([*metrics.keys(), *normalized_dimensions.keys()]),
        "reasoning_summary": reason,
        "confidence": "high" if decision in {"absorb_as_dimension", "merge"} else "medium",
        "required_source_fields": list(REQUIRED_METRIC_CONTRACT_FIELDS),
        "forbidden_uses": [
            "broker_submit",
            "runtime_threshold_apply",
            "provider_route_change",
            "bot_restart_trigger",
            "sizing_formula_runtime_apply_without_guard",
        ],
    }
    return {
        "canonical_bucket": canonical_bucket,
        "legacy_raw_bucket_key": legacy_raw,
        "bucket_alias_version": BUCKET_ALIAS_VERSION,
        "dimension_set_version": DIMENSION_SET_VERSION,
        "bucket_absorption_reason": reason,
        "taxonomy_candidate_type": candidate_type,
        "normalized_dimensions": normalized_dimensions,
        "normalized_metrics": metrics,
        "missing_dimension_keys": missing_dimensions,
        "deterministic_proposal": proposal,
    }


def default_ai_tier2_proposal(bucket_id: str, deterministic_proposal: dict[str, Any]) -> dict[str, Any]:
    return {
        "bucket_id": bucket_id,
        "proposal_source": "ai_tier2",
        "proposal_status": "not_provided",
        "proposal_decision": "reject",
        "recommended_canonical_bucket": deterministic_proposal.get("recommended_canonical_bucket"),
        "recommended_metric_or_dimension": deterministic_proposal.get("recommended_metric_or_dimension") or [],
        "reasoning_summary": "AI Tier2 proposal unavailable; deterministic proposal remains source-only.",
        "confidence": "low",
        "required_source_fields": list(REQUIRED_METRIC_CONTRACT_FIELDS),
        "forbidden_uses": deterministic_proposal.get("forbidden_uses") or [],
    }


def compare_taxonomy_proposals(
    *,
    bucket_id: str,
    deterministic_proposal: dict[str, Any],
    ai_tier2_proposal: dict[str, Any] | None,
    comparative_review: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ai_proposal = ai_tier2_proposal or default_ai_tier2_proposal(bucket_id, deterministic_proposal)
    review = comparative_review or {}
    if review.get("selected_decision"):
        selected_decision = str(review.get("selected_decision"))
    elif ai_proposal.get("proposal_status") == "provided":
        selected_decision = str(ai_proposal.get("proposal_decision") or "keep_bucket")
    else:
        selected_decision = str(deterministic_proposal.get("proposal_decision") or "keep_bucket")
    if selected_decision not in TAXONOMY_DECISIONS:
        selected_decision = "source_quality_blocker"
    selected_source = str(review.get("selected_source") or "")
    if selected_source not in {"deterministic", "ai_tier2", "hybrid", "reject"}:
        selected_source = "deterministic" if ai_proposal.get("proposal_status") != "provided" else "hybrid"
    return {
        "bucket_id": bucket_id,
        "selected_decision": selected_decision,
        "selected_source": selected_source,
        "recommended_canonical_bucket": review.get("recommended_canonical_bucket")
        or ai_proposal.get("recommended_canonical_bucket")
        or deterministic_proposal.get("recommended_canonical_bucket"),
        "recommended_metric_or_dimension": review.get("recommended_metric_or_dimension")
        or ai_proposal.get("recommended_metric_or_dimension")
        or deterministic_proposal.get("recommended_metric_or_dimension")
        or [],
        "comparison_summary": review.get("comparison_summary")
        or "Deterministic taxonomy proposal used because AI comparative review did not override it.",
        "rejected_alternative_reason": review.get("rejected_alternative_reason") or "",
        "confidence": review.get("confidence") or ai_proposal.get("confidence") or deterministic_proposal.get("confidence") or "medium",
        "required_source_fields": review.get("required_source_fields")
        or ai_proposal.get("required_source_fields")
        or deterministic_proposal.get("required_source_fields")
        or list(REQUIRED_METRIC_CONTRACT_FIELDS),
        "forbidden_uses": review.get("forbidden_uses")
        or ai_proposal.get("forbidden_uses")
        or deterministic_proposal.get("forbidden_uses")
        or [],
        "workorder_title": review.get("workorder_title") or f"Review lifecycle bucket taxonomy: {bucket_id}",
        "workorder_priority": review.get("workorder_priority") or "medium",
    }
