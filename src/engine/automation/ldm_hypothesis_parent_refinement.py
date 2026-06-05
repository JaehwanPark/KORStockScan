"""Build LDM hypothesis refinement pressure for lifecycle parent discovery."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any

from src.engine.automation.ldm_hypothesis_discovery import FORBIDDEN_USES, OBSERVATION_PLAN_SCHEMA_VERSION
from src.utils.constants import DATA_DIR


REPORT_TYPE = "ldm_hypothesis_parent_refinement"
SCHEMA_VERSION = "ldm_hypothesis_parent_refinement_v1"
REPORT_DIR = DATA_DIR / "report" / REPORT_TYPE
PIPELINE_EVENTS_DIR = DATA_DIR / "pipeline_events"
LDM_PLAN_DIR = DATA_DIR / "threshold_cycle" / "ldm_hypothesis_observation_plans"
LIFECYCLE_BUCKET_DIR = DATA_DIR / "report" / "lifecycle_bucket_discovery"

CONSUMER = "lifecycle_bucket_discovery"
DECISION_AUTHORITY = "postclose_lifecycle_parent_refinement_pressure"
REPORT_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


@dataclass
class HypothesisAggregate:
    hypothesis_id: str
    plan_hypothesis: dict[str, Any] = field(default_factory=dict)
    match_count: int = 0
    source_parent_bucket_ids: Counter[str] = field(default_factory=Counter)
    stock_codes: Counter[str] = field(default_factory=Counter)
    stages: Counter[str] = field(default_factory=Counter)
    observable_signatures: Counter[str] = field(default_factory=Counter)
    source_quality_blocked_count: int = 0
    forbidden_contract_violation_count: int = 0
    plan_hypothesis_missing_count: int = 0
    profit_values: list[float] = field(default_factory=list)
    candidate_features: dict[str, Any] = field(default_factory=dict)


def report_paths(target_date: str) -> tuple[Path, Path]:
    base = REPORT_DIR / f"{REPORT_TYPE}_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def observation_plan_path(target_date: str) -> Path:
    return LDM_PLAN_DIR / f"ldm_hypothesis_observation_plan_{target_date}.json"


def latest_observation_plan_path(target_date: str) -> Path:
    exact = observation_plan_path(target_date)
    if exact.exists():
        return exact
    candidates: list[tuple[str, Path]] = []
    if LDM_PLAN_DIR.exists():
        for path in LDM_PLAN_DIR.glob("ldm_hypothesis_observation_plan_*.json"):
            plan_date = path.stem.removeprefix("ldm_hypothesis_observation_plan_")
            if plan_date <= target_date:
                candidates.append((plan_date, path))
    if candidates:
        return sorted(candidates)[-1][1]
    return exact


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _safe_float(value: Any, default: float | None = None) -> float | None:
    try:
        if value in (None, "", "-"):
            return default
        number = float(value)
        if math.isnan(number) or math.isinf(number):
            return default
        return number
    except Exception:
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, "", "-"):
            return default
        return int(float(value))
    except Exception:
        return default


def _truthy(value: Any) -> bool:
    return value is True or str(value).strip().lower() == "true"


def _parse_json_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if not isinstance(value, str) or not value.strip():
        return {}
    try:
        parsed = json.loads(value)
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _pipeline_event_path(target_date: str) -> Path:
    return PIPELINE_EVENTS_DIR / f"pipeline_events_{target_date}.jsonl"


def _iter_pipeline_event_fields(target_date: str):
    path = _pipeline_event_path(target_date)
    try:
        handle = path.open("r", encoding="utf-8", errors="replace")
    except OSError:
        return
    with handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except Exception:
                continue
            fields = payload.get("fields") if isinstance(payload.get("fields"), dict) else {}
            yield payload, fields


def _observable_signature(features: dict[str, Any], requirements: list[dict[str, Any]] | None = None) -> str:
    allowed = {"entry_score_parent", "entry_source_parent", "submit_quality_parent"}
    selected: dict[str, str] = {}
    for key in sorted(allowed):
        value = features.get(key)
        if value not in (None, "", "-"):
            selected[key] = str(value)
    if not selected and requirements:
        for requirement in requirements:
            if not isinstance(requirement, dict):
                continue
            field_name = str(requirement.get("field") or "")
            value = requirement.get("value")
            if field_name in allowed and value not in (None, "", "-"):
                selected[field_name] = str(value)
    raw = json.dumps(selected, ensure_ascii=True, sort_keys=True)
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]
    return f"observable_{digest}"


def _observable_features(features: dict[str, Any], requirements: list[dict[str, Any]] | None = None) -> dict[str, str]:
    selected: dict[str, str] = {}
    for key in ("entry_score_parent", "entry_source_parent", "submit_quality_parent"):
        value = features.get(key)
        if value not in (None, "", "-"):
            selected[key] = str(value)
    if not selected and requirements:
        for requirement in requirements:
            if not isinstance(requirement, dict):
                continue
            field_name = str(requirement.get("field") or "")
            value = requirement.get("value")
            if field_name in {"entry_score_parent", "entry_source_parent", "submit_quality_parent"} and value not in (
                None,
                "",
                "-",
            ):
                selected[field_name] = str(value)
    return selected


def _load_observation_plan(target_date: str) -> dict[str, Any]:
    payload = _load_json(latest_observation_plan_path(target_date))
    if payload.get("schema_version") == OBSERVATION_PLAN_SCHEMA_VERSION:
        return payload
    return {}


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
    paths = sorted(LIFECYCLE_BUCKET_DIR.glob("lifecycle_bucket_discovery_*.json"), reverse=True)
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


def _parent_lookup(lifecycle_report: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    parents: dict[str, dict[str, Any]] = {}
    parent_rows: list[dict[str, Any]] = []
    for parent in lifecycle_report.get("parent_bucket_summaries") or []:
        if not isinstance(parent, dict):
            continue
        parent_id = str(parent.get("source_parent_bucket_id") or parent.get("parent_bucket_id") or "").strip()
        if not parent_id:
            continue
        parents[parent_id] = parent
        parent_rows.append(parent)
    return parents, parent_rows


def _requirements_to_features(requirements: list[dict[str, Any]]) -> dict[str, str]:
    features: dict[str, str] = {}
    for requirement in requirements:
        if not isinstance(requirement, dict):
            continue
        field_name = str(requirement.get("field") or "").strip()
        value = requirement.get("value")
        if field_name and value not in (None, "", "-"):
            features[field_name] = str(value)
    return features


def _matching_parent_ids(features: dict[str, Any], parent_rows: list[dict[str, Any]]) -> list[str]:
    matches: list[str] = []
    for parent in parent_rows:
        dimensions = parent.get("dimension_filters") if isinstance(parent.get("dimension_filters"), dict) else {}
        probes = ("entry_score_parent", "entry_source_parent", "submit_quality_parent")
        comparable = [key for key in probes if str(features.get(key) or "").strip()]
        if len(comparable) < 2:
            continue
        if all(str(dimensions.get(key) or "").strip() == str(features.get(key) or "").strip() for key in comparable):
            parent_id = str(parent.get("source_parent_bucket_id") or parent.get("parent_bucket_id") or "").strip()
            if parent_id:
                matches.append(parent_id)
    return sorted(set(matches))


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


def _previous_status_counts(hypothesis_id: str, target_date: str) -> Counter[str]:
    try:
        target = date.fromisoformat(target_date)
    except ValueError:
        return Counter()
    counts: Counter[str] = Counter()
    for path in sorted(REPORT_DIR.glob(f"{REPORT_TYPE}_*.json"), reverse=True):
        report_date = _date_from_report_path(path)
        if report_date is None or report_date >= target:
            continue
        payload = _load_json(path)
        for item in payload.get("refinement_inputs") or []:
            if not isinstance(item, dict) or str(item.get("soft_hypothesis_id") or "") != hypothesis_id:
                continue
            classification = str(item.get("classification") or "").strip()
            if classification:
                counts[classification] += 1
            if item.get("contrary_sample_need") is True:
                counts["needs_opposite_sample"] += 1
            diagnosis = item.get("repeated_status_diagnosis")
            if isinstance(diagnosis, dict):
                diagnosed_status = str(diagnosis.get("diagnosed_status") or "").strip()
                if diagnosed_status:
                    counts[diagnosed_status] += 1
            closure_bias = str(item.get("recommended_closure_bias") or "").strip()
            if closure_bias:
                counts[closure_bias] += 1
            break
    return counts


def _diagnose_repeated_status(
    *,
    classification: str,
    gap_reason: str,
    contrary_needed: bool,
    aggregate: HypothesisAggregate,
    parent_ids: list[str],
    previous_counts: Counter[str],
) -> dict[str, Any]:
    source_quality_ratio = aggregate.source_quality_blocked_count / max(1, aggregate.match_count)
    retry_count = max(
        previous_counts.get(classification, 0),
        previous_counts.get("needs_opposite_sample", 0) if contrary_needed else 0,
    )
    diagnosed_status = classification
    diagnosis_reason = "initial_or_non_repeated_status"
    recommended_closure_bias = "still_collecting"

    if aggregate.plan_hypothesis_missing_count > 0 or aggregate.forbidden_contract_violation_count > 0:
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
        recommended_closure_bias = "parent_refinement_candidate_created" if parent_ids else "new_parent_candidate_created"
    elif classification == "parent_conflict":
        diagnosed_status = "parent_conflict"
        diagnosis_reason = "hypothesis_parent_ev_divergence_repeated"
        recommended_closure_bias = "parent_refinement_candidate_created"
    elif classification == "parent_support" and contrary_needed:
        diagnosed_status = "parent_support_but_no_contrast"
        diagnosis_reason = "parent_absorbs_hypothesis_but_contrast_still_missing"
        recommended_closure_bias = "absorbed_into_existing_parent" if parent_ids else "rare_observation_only_budget_capped"
    elif contrary_needed:
        diagnosed_status = "needs_opposite_sample"
        diagnosis_reason = "contrast_group_missing"
        recommended_closure_bias = "still_collecting"

    retry_count = max(
        retry_count,
        previous_counts.get(diagnosed_status, 0),
        previous_counts.get(recommended_closure_bias, 0),
    )

    if contrary_needed and retry_count >= 2 and recommended_closure_bias == "still_collecting":
        if aggregate.match_count >= 10 and source_quality_ratio < 0.5:
            diagnosed_status = "needs_more_contrastive_sample"
            diagnosis_reason = "repeated_one_sided_runtime_matches"
            recommended_closure_bias = "rejected_as_structurally_uncontrastable"
        else:
            diagnosed_status = "runtime_match_zero_or_low"
            diagnosis_reason = "repeated_contrast_gap_with_low_or_fragile_runtime_coverage"
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


def _pressure_item(
    *,
    target_date: str,
    aggregate: HypothesisAggregate,
    parent_ids: list[str],
    parent_by_id: dict[str, dict[str, Any]],
    explicit_parent_ids: list[str] | None = None,
) -> dict[str, Any]:
    plan = aggregate.plan_hypothesis
    evidence = plan.get("evidence_summary") if isinstance(plan.get("evidence_summary"), dict) else {}
    contrast = plan.get("contrast_summary") if isinstance(plan.get("contrast_summary"), dict) else {}
    hypothesis_ev = _safe_float(evidence.get("source_quality_adjusted_ev_pct"), None)
    mean_profit = sum(aggregate.profit_values) / len(aggregate.profit_values) if aggregate.profit_values else None
    positive_count = sum(1 for value in aggregate.profit_values if value > 0)
    negative_count = sum(1 for value in aggregate.profit_values if value < 0)
    parent_ev_values = [
        _safe_float(parent_by_id.get(parent_id, {}).get("parent_source_quality_adjusted_ev_pct"), None)
        for parent_id in parent_ids
    ]
    parent_ev_values = [value for value in parent_ev_values if value is not None]
    avg_parent_ev = sum(parent_ev_values) / len(parent_ev_values) if parent_ev_values else None
    ev_delta = (hypothesis_ev - avg_parent_ev) if hypothesis_ev is not None and avg_parent_ev is not None else None

    pressure_reasons: list[str] = []
    classification = "taxonomy_gap_candidate"
    gap_reason = ""
    explicit_parent_ids = explicit_parent_ids or []
    unknown_explicit_parent_ids = [parent_id for parent_id in explicit_parent_ids if parent_id not in parent_by_id]
    if aggregate.plan_hypothesis_missing_count > 0:
        classification = "source_quality_gap"
        gap_reason = "plan_hypothesis_missing"
        pressure_reasons.append("matched_hypothesis_missing_from_observation_plan")
    elif aggregate.forbidden_contract_violation_count > 0:
        classification = "source_quality_gap"
        gap_reason = "forbidden_runtime_authority_violation"
        pressure_reasons.append("matched_event_forbidden_runtime_authority_violation")
    elif aggregate.source_quality_blocked_count >= aggregate.match_count and aggregate.match_count > 0:
        classification = "source_quality_gap"
        gap_reason = "source_quality_blocked"
        pressure_reasons.append("all_matches_source_quality_blocked")
    elif unknown_explicit_parent_ids:
        classification = "taxonomy_gap_candidate"
        gap_reason = "parent_ambiguous" if parent_ids or len(unknown_explicit_parent_ids) > 1 else "parent_not_found"
        pressure_reasons.append(gap_reason)
    elif len(parent_ids) == 1:
        if ev_delta is not None and abs(ev_delta) >= 1.0 and (
            (hypothesis_ev or 0.0) * (avg_parent_ev or 0.0) < 0 or abs(ev_delta) >= 2.0
        ):
            classification = "parent_conflict"
            pressure_reasons.append("hypothesis_parent_ev_divergence")
        else:
            classification = "parent_support"
            pressure_reasons.append("hypothesis_absorbs_into_parent_context")
    elif len(parent_ids) > 1:
        classification = "taxonomy_gap_candidate"
        gap_reason = "parent_ambiguous"
        pressure_reasons.append("multiple_possible_parent_buckets")
    else:
        classification = "taxonomy_gap_candidate"
        gap_reason = "join_key_missing" if not aggregate.candidate_features else "parent_not_found"
        pressure_reasons.append(gap_reason)

    contrary_needed = str(contrast.get("contrast_coverage_status") or "") == "needs_opposite_sample"
    if contrary_needed:
        pressure_reasons.append("needs_opposite_sample")
    if aggregate.match_count < 3:
        pressure_reasons.append("thin_runtime_match_sample")

    fragility_penalty = 1.0 if aggregate.match_count < 3 else 0.0
    source_quality_penalty = min(1.0, aggregate.source_quality_blocked_count / max(1, aggregate.match_count))
    contrast_strength = abs(float(contrast.get("contrast_ev_delta_pct") or 0.0))
    divergence = abs(ev_delta or 0.0)
    refinement_pressure_score = round(
        contrast_strength + divergence + min(2.0, aggregate.match_count / 10.0) - fragility_penalty - source_quality_penalty,
        4,
    )
    repeated_gap_count = _previous_gap_count(aggregate.hypothesis_id, target_date)
    previous_status_counts = _previous_status_counts(aggregate.hypothesis_id, target_date)
    if repeated_gap_count:
        pressure_reasons.append("repeated_taxonomy_gap_seen_before")
    repeated_status_diagnosis = _diagnose_repeated_status(
        classification=classification,
        gap_reason=gap_reason,
        contrary_needed=contrary_needed,
        aggregate=aggregate,
        parent_ids=parent_ids,
        previous_counts=previous_status_counts,
    )
    if repeated_status_diagnosis["retry_count"] >= 2:
        pressure_reasons.append("repeated_status_diagnosed")

    item_id = "ldm_refinement_" + hashlib.sha1(
        f"{target_date}|{aggregate.hypothesis_id}|{','.join(parent_ids)}".encode("utf-8")
    ).hexdigest()[:16]
    return {
        "refinement_input_id": item_id,
        "soft_hypothesis_id": aggregate.hypothesis_id,
        "classification": classification,
        "gap_reason": gap_reason,
        "source_parent_bucket_ids": parent_ids,
        "unmatched_source_parent_bucket_ids": unknown_explicit_parent_ids,
        "runtime_observable_signature": aggregate.observable_signatures.most_common(1)[0][0]
        if aggregate.observable_signatures
        else "",
        "runtime_observable_features": _observable_features(
            aggregate.candidate_features,
            plan.get("observable_requirements") if isinstance(plan.get("observable_requirements"), list) else [],
        ),
        "match_count": aggregate.match_count,
        "positive_count": positive_count,
        "negative_count": negative_count,
        "source_quality_blocked_count": aggregate.source_quality_blocked_count,
        "forbidden_contract_violation_count": aggregate.forbidden_contract_violation_count,
        "plan_hypothesis_missing_count": aggregate.plan_hypothesis_missing_count,
        "mean_runtime_profit_pct": round(mean_profit, 4) if mean_profit is not None else None,
        "hypothesis_ev_pct": hypothesis_ev,
        "parent_ev_pct": round(avg_parent_ev, 4) if avg_parent_ev is not None else None,
        "hypothesis_parent_ev_delta_pct": round(ev_delta, 4) if ev_delta is not None else None,
        "refinement_pressure_score": refinement_pressure_score,
        "pressure_reasons": list(dict.fromkeys(pressure_reasons)),
        "evidence_fragility": "thin_sample" if aggregate.match_count < 3 else "ok",
        "contrary_sample_need": contrary_needed,
        "taxonomy_fit": "matched_parent" if len(parent_ids) == 1 else "ambiguous" if len(parent_ids) > 1 else "gap",
        "repeated_gap_count": repeated_gap_count,
        "diagnosed_status": repeated_status_diagnosis["diagnosed_status"],
        "diagnosis_reason": repeated_status_diagnosis["diagnosis_reason"],
        "diagnosis_evidence": repeated_status_diagnosis["diagnosis_evidence"],
        "retry_count": repeated_status_diagnosis["retry_count"],
        "recommended_closure_bias": repeated_status_diagnosis["recommended_closure_bias"],
        "repeated_status_diagnosis": repeated_status_diagnosis,
        "opposite_sample_absence_diagnosis": repeated_status_diagnosis
        if contrary_needed
        else {
            "diagnosed_status": "not_applicable",
            "diagnosis_reason": "contrast_coverage_not_marked_needs_opposite_sample",
            "diagnosis_evidence": repeated_status_diagnosis["diagnosis_evidence"],
            "retry_count": repeated_status_diagnosis["retry_count"],
            "recommended_closure_bias": repeated_status_diagnosis["recommended_closure_bias"],
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
        },
        "consumer": CONSUMER,
        "consumption_required": True,
        "must_not_be_silent": True,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "forbidden_uses": list(FORBIDDEN_USES),
    }


def build_refinement_report(target_date: str) -> dict[str, Any]:
    target_date = str(target_date).strip()
    plan = _load_observation_plan(target_date)
    hypotheses = {
        str(item.get("soft_hypothesis_id") or ""): item
        for item in (plan.get("hypotheses") or [])
        if isinstance(item, dict) and str(item.get("soft_hypothesis_id") or "").strip()
    }
    lifecycle_report = _latest_lifecycle_bucket_report(target_date)
    parent_by_id, parent_rows = _parent_lookup(lifecycle_report)
    aggregates: dict[str, HypothesisAggregate] = {}
    for payload, fields in _iter_pipeline_event_fields(target_date) or []:
        if not _truthy(fields.get("ldm_hypothesis_matched")):
            continue
        hypothesis_id = str(fields.get("ldm_hypothesis_id") or "").strip()
        if not hypothesis_id:
            continue
        aggregate = aggregates.setdefault(
            hypothesis_id,
            HypothesisAggregate(hypothesis_id=hypothesis_id, plan_hypothesis=hypotheses.get(hypothesis_id, {})),
        )
        aggregate.match_count += 1
        if hypothesis_id not in hypotheses:
            aggregate.plan_hypothesis_missing_count += 1
            aggregate.source_quality_blocked_count += 1
        parent_id = str(fields.get("source_parent_bucket_id") or fields.get("canonical_parent_bucket") or "").strip()
        if parent_id:
            aggregate.source_parent_bucket_ids[parent_id] += 1
        stock_code = str(payload.get("stock_code") or "").strip()
        if stock_code:
            aggregate.stock_codes[stock_code] += 1
        stage = str(payload.get("stage") or "").strip()
        if stage:
            aggregate.stages[stage] += 1
        candidate_features = _parse_json_mapping(fields.get("ldm_hypothesis_candidate_features"))
        if candidate_features:
            aggregate.candidate_features.update(candidate_features)
        requirements = aggregate.plan_hypothesis.get("observable_requirements")
        if not isinstance(requirements, list):
            requirements = []
        aggregate.observable_signatures[_observable_signature(candidate_features, requirements)] += 1
        source_quality = str(fields.get("source_quality_status") or fields.get("source_quality") or "").lower()
        if "block" in source_quality or "fail" in source_quality:
            aggregate.source_quality_blocked_count += 1
        actual_order_value = fields.get("actual_order_submitted")
        broker_forbidden_value = fields.get("broker_order_forbidden")
        authority_contract_missing = actual_order_value in (None, "", "-") or broker_forbidden_value in (None, "", "-")
        if authority_contract_missing or _truthy(actual_order_value) or not _truthy(broker_forbidden_value):
            aggregate.forbidden_contract_violation_count += 1
            aggregate.source_quality_blocked_count += 1
        profit = _safe_float(fields.get("profit_rate"), None)
        if profit is not None:
            aggregate.profit_values.append(profit)

    refinement_inputs: list[dict[str, Any]] = []
    for aggregate in aggregates.values():
        requirements = aggregate.plan_hypothesis.get("observable_requirements")
        requirement_features = _requirements_to_features(requirements if isinstance(requirements, list) else [])
        features = {**requirement_features, **aggregate.candidate_features}
        explicit_parent_ids = sorted(set(aggregate.source_parent_bucket_ids))
        parent_ids = explicit_parent_ids or _matching_parent_ids(features, parent_rows)
        known_parent_ids = [parent_id for parent_id in parent_ids if parent_id in parent_by_id]
        refinement_inputs.append(
            _pressure_item(
                target_date=target_date,
                aggregate=aggregate,
                parent_ids=known_parent_ids,
                parent_by_id=parent_by_id,
                explicit_parent_ids=explicit_parent_ids,
            )
        )

    class_counts = Counter(str(item.get("classification") or "unknown") for item in refinement_inputs)
    report = {
        "schema_version": SCHEMA_VERSION,
        "report_type": REPORT_TYPE,
        "date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "decision_authority": DECISION_AUTHORITY,
        "consumer": CONSUMER,
        "consumption_required": bool(refinement_inputs),
        "must_not_be_silent": bool(refinement_inputs),
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "forbidden_uses": list(FORBIDDEN_USES),
        "source_artifacts": {
            "pipeline_events": str(_pipeline_event_path(target_date)),
            "observation_plan": str(latest_observation_plan_path(target_date)),
            "previous_lifecycle_bucket_discovery": str(
                LIFECYCLE_BUCKET_DIR / f"lifecycle_bucket_discovery_{lifecycle_report.get('date')}.json"
            )
            if lifecycle_report.get("date")
            else "",
        },
        "summary": {
            "hypothesis_match_count": sum(item.match_count for item in aggregates.values()),
            "matched_hypothesis_count": len(aggregates),
            "refinement_input_count": len(refinement_inputs),
            "classification_counts": dict(sorted(class_counts.items())),
            "plan_hypothesis_count": len(hypotheses),
        },
        "refinement_inputs": sorted(
            refinement_inputs,
            key=lambda item: (
                -_safe_int(item.get("match_count")),
                str(item.get("soft_hypothesis_id") or ""),
            ),
        ),
    }
    return report


def render_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    lines = [
        f"# LDM Hypothesis Parent Refinement - {report.get('date')}",
        "",
        "## Contract",
        f"- decision_authority: `{report.get('decision_authority')}`",
        f"- consumer: `{report.get('consumer')}`",
        f"- consumption_required: `{report.get('consumption_required')}`",
        f"- runtime_effect: `{report.get('runtime_effect')}`",
        f"- allowed_runtime_apply: `{report.get('allowed_runtime_apply')}`",
        "",
        "## Summary",
        f"- hypothesis_match_count: `{summary.get('hypothesis_match_count')}`",
        f"- matched_hypothesis_count: `{summary.get('matched_hypothesis_count')}`",
        f"- refinement_input_count: `{summary.get('refinement_input_count')}`",
        f"- classification_counts: `{summary.get('classification_counts') or {}}`",
        "",
        "## Inputs",
    ]
    for item in (report.get("refinement_inputs") or [])[:20]:
        lines.append(
            f"- `{item.get('refinement_input_id')}` hypothesis=`{item.get('soft_hypothesis_id')}` "
            f"classification=`{item.get('classification')}` gap=`{item.get('gap_reason') or '-'}` "
            f"parents=`{item.get('source_parent_bucket_ids') or []}` matches=`{item.get('match_count')}` "
            f"pressure=`{item.get('refinement_pressure_score')}`"
        )
    return "\n".join(lines) + "\n"


def write_report(target_date: str) -> dict[str, Any]:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = build_refinement_report(target_date)
    json_path, md_path = report_paths(target_date)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build LDM hypothesis parent refinement pressure report.")
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    report = write_report(args.date) if args.write else build_refinement_report(args.date)
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
