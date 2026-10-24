"""Historical read-only helpers; no active policy publisher or CLI.

Only existing forensic consumers retain these calculations. Live callers use
their native role owners and permanent retirement fences.
"""

from __future__ import annotations


import json


import re


from collections import Counter


from dataclasses import dataclass, field


from datetime import date


from pathlib import Path


from typing import Any


from src.utils.constants import DATA_DIR

REPORT_TYPE = "ldm_hypothesis_parent_refinement"


REPORT_DIR = DATA_DIR / "report" / REPORT_TYPE


LIFECYCLE_BUCKET_DIR = DATA_DIR / "report" / "lifecycle_bucket_discovery"


REPORT_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


@dataclass
class HypothesisAggregate:
    hypothesis_id: str
    plan_hypothesis: dict[str, Any] = field(default_factory=dict)
    match_count: int = 0
    runtime_match_count: int = 0
    derived_match_count: int = 0
    raw_ldm_hypothesis_matched: Counter[str] = field(default_factory=Counter)
    raw_ldm_hypothesis_id_present: Counter[str] = field(default_factory=Counter)
    source_event_files: Counter[str] = field(default_factory=Counter)
    source_parent_bucket_ids: Counter[str] = field(default_factory=Counter)
    stock_codes: Counter[str] = field(default_factory=Counter)
    stages: Counter[str] = field(default_factory=Counter)
    observable_signatures: Counter[str] = field(default_factory=Counter)
    source_quality_blocked_count: int = 0
    forbidden_contract_violation_count: int = 0
    plan_hypothesis_missing_count: int = 0
    profit_values: list[float] = field(default_factory=list)
    candidate_features: dict[str, Any] = field(default_factory=dict)


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _date_from_report_path(path: Path) -> date | None:
    match = REPORT_DATE_RE.search(path.name)
    if not match:
        return None
    try:
        return date.fromisoformat(match.group(0))
    except ValueError:
        return None


def _latest_lifecycle_bucket_report(target_date: str) -> dict[str, Any]:
    try:
        target = date.fromisoformat(target_date)
    except ValueError:
        return {}
    paths = sorted(
        LIFECYCLE_BUCKET_DIR.glob("lifecycle_bucket_discovery_*.json"), reverse=True
    )
    for path in paths:
        report_date = _date_from_report_path(path)
        if (
            report_date is None
            or report_date >= target
            or any(suffix in path.name for suffix in ("rolling5d", "rolling10d", "mtd"))
        ):
            continue
        payload = _load_json(path)
        if payload:
            return payload
    return {}


def _previous_gap_count(hypothesis_id: str, target_date: str) -> int:
    try:
        target = date.fromisoformat(target_date)
    except ValueError:
        return 0
    count = 0
    for path in sorted(REPORT_DIR.glob(f"{REPORT_TYPE}_*.json"), reverse=True):
        report_date = _date_from_report_path(path)
        if report_date is None or report_date >= target:
            continue
        payload = _load_json(path)
        for item in payload.get("refinement_inputs") or []:
            if (
                isinstance(item, dict)
                and str(item.get("soft_hypothesis_id") or "") == hypothesis_id
                and str(item.get("classification") or "") == "taxonomy_gap_candidate"
            ):
                count += 1
                break
    return count


def _diagnose_repeated_status(
    *,
    classification: str,
    gap_reason: str,
    contrary_needed: bool,
    aggregate: HypothesisAggregate,
    parent_ids: list[str],
    previous_counts: Counter[str],
) -> dict[str, Any]:
    source_quality_ratio = aggregate.source_quality_blocked_count / max(
        1, aggregate.match_count
    )
    retry_count = max(
        previous_counts.get(classification, 0),
        previous_counts.get("needs_opposite_sample", 0) if contrary_needed else 0,
    )
    diagnosed_status = classification
    diagnosis_reason = "initial_or_non_repeated_status"
    recommended_closure_bias = "still_collecting"

    if (
        aggregate.plan_hypothesis_missing_count > 0
        or aggregate.forbidden_contract_violation_count > 0
    ):
        diagnosed_status = "contract_or_handoff_gap"
        diagnosis_reason = "matched_hypothesis_or_runtime_authority_contract_gap"
        recommended_closure_bias = "contract_handoff_gap_created"
    elif classification == "source_quality_gap" or source_quality_ratio >= 0.8:
        diagnosed_status = "source_quality_gap"
        diagnosis_reason = gap_reason or "source_quality_blocked_ratio_high"
        recommended_closure_bias = "source_quality_gap_created"
    elif aggregate.match_count <= 1:
        diagnosed_status = "rejected_as_fragile"
        diagnosis_reason = "single_or_zero_runtime_match"
        recommended_closure_bias = "rejected_as_fragile"
    elif classification == "taxonomy_gap_candidate":
        diagnosed_status = "taxonomy_gap_candidate"
        diagnosis_reason = gap_reason or "taxonomy_gap_repeated_or_unmapped"
        recommended_closure_bias = (
            "parent_refinement_candidate_created"
            if parent_ids
            else "new_parent_candidate_created"
        )
    elif classification == "parent_conflict":
        diagnosed_status = "parent_conflict"
        diagnosis_reason = "hypothesis_parent_ev_divergence_repeated"
        recommended_closure_bias = "parent_refinement_candidate_created"
    elif classification == "parent_support" and contrary_needed:
        diagnosed_status = "parent_support_but_no_contrast"
        diagnosis_reason = "parent_absorbs_hypothesis_but_contrast_still_missing"
        recommended_closure_bias = (
            "absorbed_into_existing_parent"
            if parent_ids
            else "rare_observation_only_budget_capped"
        )
    elif contrary_needed:
        diagnosed_status = "needs_opposite_sample"
        diagnosis_reason = "contrast_group_missing"
        recommended_closure_bias = "still_collecting"

    retry_count = max(
        retry_count,
        previous_counts.get(diagnosed_status, 0),
        previous_counts.get(recommended_closure_bias, 0),
    )

    if (
        contrary_needed
        and retry_count >= 2
        and recommended_closure_bias == "still_collecting"
    ):
        if aggregate.match_count >= 10 and source_quality_ratio < 0.5:
            diagnosed_status = "needs_more_contrastive_sample"
            diagnosis_reason = "repeated_one_sided_runtime_matches"
            recommended_closure_bias = "rejected_as_structurally_uncontrastable"
        else:
            diagnosed_status = "runtime_match_zero_or_low"
            diagnosis_reason = (
                "repeated_contrast_gap_with_low_or_fragile_runtime_coverage"
            )
            recommended_closure_bias = "rare_observation_only_budget_capped"

    if retry_count < 2 and recommended_closure_bias in {
        "rare_observation_only_budget_capped",
        "rejected_as_structurally_uncontrastable",
    }:
        recommended_closure_bias = "still_collecting"

    evidence = {
        "match_count": aggregate.match_count,
        "source_quality_blocked_count": aggregate.source_quality_blocked_count,
        "source_quality_blocked_ratio": round(source_quality_ratio, 4),
        "forbidden_contract_violation_count": aggregate.forbidden_contract_violation_count,
        "plan_hypothesis_missing_count": aggregate.plan_hypothesis_missing_count,
        "previous_status_counts": dict(sorted(previous_counts.items())),
        "parent_match_count": len(parent_ids),
        "positive_count": sum(1 for value in aggregate.profit_values if value > 0),
        "negative_count": sum(1 for value in aggregate.profit_values if value < 0),
    }
    return {
        "diagnosed_status": diagnosed_status,
        "diagnosis_reason": diagnosis_reason,
        "diagnosis_evidence": evidence,
        "retry_count": retry_count,
        "recommended_closure_bias": recommended_closure_bias,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


from src.engine.lifecycle.archive.ldm_hypothesis_discovery_readers import (
    FORBIDDEN_USES,
    OBSERVATION_PLAN_SCHEMA_VERSION,
)
