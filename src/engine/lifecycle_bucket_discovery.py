"""Discover lifecycle bucket candidates and classify auto-apply readiness."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Any

from src.utils.constants import DATA_DIR, TRADING_RULES


REPORT_DIR = DATA_DIR / "report" / "lifecycle_bucket_discovery"
LDM_REPORT_DIR = DATA_DIR / "report" / "lifecycle_decision_matrix"
CATALOG_DIR = DATA_DIR / "threshold_cycle" / "lifecycle_bucket_catalog"
SIM_AUTO_APPROVAL_DIR = DATA_DIR / "threshold_cycle" / "sim_auto_approvals"

ENTRY_LIVE_AUTO_FAMILY = "entry_wait6579_score66_69_recovery_gate_v1"
SCALE_IN_LIVE_AUTO_FAMILY = "scale_in_bucket_runtime_policy_v1"
ENTRY_LIVE_AUTO_BUCKET_KEY = (
    "score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|"
    "liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_unknown"
)

DISCOVERY_SCHEMA_VERSION = "lifecycle_bucket_discovery_v1"
AI_REVIEW_SCHEMA_NAME = "lifecycle_bucket_discovery_review_v1"
AI_REVIEW_DEFAULT_PROVIDER = "openai"
AI_REVIEW_MODEL = str(getattr(TRADING_RULES, "GPT_DEEP_MODEL", "gpt-5.4") or "gpt-5.4")
LIVE_AUTO_STATES = {"live_auto_apply_ready"}
AUTO_SURFACE_STATES = {
    "new_bucket_candidate",
    "sim_auto_approved",
    "live_auto_apply_ready",
    "runtime_blocked_contract_gap",
    "code_patch_required",
    "code_review_failed",
    "automation_handoff_gap",
}
FINAL_CLASSIFICATION_STATES = {
    "source_only_keep_collecting",
    "sim_auto_approved",
    "live_auto_apply_ready",
    "runtime_blocked_contract_gap",
    "code_patch_required",
    "code_review_failed",
    "automation_handoff_gap",
    "new_bucket_candidate",
}
FINAL_RELATIONS = {"existing_bucket_refinement", "new_bucket_candidate", "unclear"}
AI_EXPLICIT_BLOCK_TERMS = {
    "contract",
    "schema",
    "source_quality",
    "source quality",
    "env",
    "mapping",
    "hook",
    "attribution",
    "safety",
    "broker",
    "stale",
    "qty",
    "cooldown",
    "provider",
    "cap",
    "forbidden",
    "leak",
    "missing",
}


def discovery_report_path(target_date: str) -> Path:
    return REPORT_DIR / f"lifecycle_bucket_discovery_{target_date}.json"


def discovery_markdown_path(target_date: str) -> Path:
    return REPORT_DIR / f"lifecycle_bucket_discovery_{target_date}.md"


def bucket_catalog_path(target_date: str) -> Path:
    return CATALOG_DIR / f"lifecycle_bucket_catalog_{target_date}.json"


def sim_auto_approval_path(target_date: str) -> Path:
    return SIM_AUTO_APPROVAL_DIR / f"lifecycle_bucket_sim_auto_approval_{target_date}.json"


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _previous_report(target_date: str) -> dict[str, Any]:
    latest: dict[str, Any] = {}
    for path in sorted(REPORT_DIR.glob("lifecycle_bucket_discovery_*.json")):
        report_date = path.stem.removeprefix("lifecycle_bucket_discovery_")
        if report_date >= target_date:
            continue
        payload = _load_json(path)
        if payload:
            latest = payload
    return latest


def _text_hash(payload: Any) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except Exception:
        return default


def _safe_float(value: Any, default: float | None = None) -> float | None:
    try:
        if value in (None, "", "-", "None"):
            return default
        number = float(value)
    except Exception:
        return default
    return number if number == number else default


def _slug(value: Any, *, max_len: int = 96) -> str:
    text = re.sub(r"[^a-zA-Z0-9가-힣]+", "_", str(value or "").strip().lower()).strip("_")
    return text[:max_len] or "unknown"


def _source_dimensions(bucket_type: str, bucket_key: str) -> dict[str, str]:
    if "=" not in bucket_key:
        return {bucket_type: bucket_key}
    dimensions: dict[str, str] = {}
    for part in bucket_key.split("|"):
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        if key.strip():
            dimensions[key.strip()] = value.strip()
    return dimensions or {bucket_type: bucket_key}


def _stable_source_bucket_id(stage: str, bucket_type: str, bucket_key: str) -> str:
    raw = f"{stage}|{bucket_type}|{bucket_key}"
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:10]
    return f"{stage}:{bucket_type}:{_slug(bucket_key, max_len=60)}:{digest}"


def _source_bucket_kind(candidate_state: str, bucket: dict[str, Any]) -> str:
    if candidate_state == "live_auto_apply_ready":
        return "live_auto_candidate"
    if candidate_state == "sim_auto_approved":
        return "sim_auto_policy"
    if bucket.get("unknown_dimension_counts") or "unknown" in str(bucket.get("bucket_key") or ""):
        return "taxonomy_provenance_gap"
    if candidate_state in {"code_patch_required", "automation_handoff_gap", "runtime_blocked_contract_gap"}:
        return "source_quality_gap"
    return "source_only_observation"


def _recommended_resolution(candidate_state: str, bucket: dict[str, Any]) -> str:
    existing = str(bucket.get("recommended_resolution") or "").strip()
    if existing and existing != "none":
        return existing
    if bucket.get("unknown_dimension_counts") or "unknown" in str(bucket.get("bucket_key") or ""):
        return "resolve_unknown_source_dimensions"
    if candidate_state == "live_auto_apply_ready":
        return "preopen_live_auto_bridge"
    if candidate_state == "sim_auto_approved":
        return "next_preopen_sim_policy_input"
    if str(bucket.get("source_quality_gate") or "") != "pass":
        return "keep_collecting_until_sample_floor"
    return "keep_collecting"


def _source_contract_snapshot(ldm: dict[str, Any]) -> dict[str, Any]:
    source_map = ldm.get("sources") if isinstance(ldm.get("sources"), dict) else {}
    sections: dict[str, Any] = {}
    for section_name in (
        "entry_bucket_attribution",
        "scale_in_bucket_attribution",
        "overnight_bucket_attribution",
    ):
        section = ldm.get(section_name) if isinstance(ldm.get(section_name), dict) else {}
        buckets = section.get("buckets") if isinstance(section.get("buckets"), list) else []
        field_names: set[str] = set()
        bucket_types: set[str] = set()
        dimension_keys: set[str] = set()
        for item in buckets:
            if not isinstance(item, dict):
                continue
            field_names.update(str(key) for key in item)
            bucket_types.add(str(item.get("bucket_type") or ""))
            dimension_keys.update(_source_dimensions(str(item.get("bucket_type") or ""), str(item.get("bucket_key") or "")).keys())
        sections[section_name] = {
            "present": bool(section),
            "bucket_count": len([item for item in buckets if isinstance(item, dict)]),
            "bucket_types": sorted(value for value in bucket_types if value),
            "bucket_fields": sorted(field_names),
            "dimension_keys": sorted(dimension_keys),
        }
    policy_entries = ldm.get("policy_entries") if isinstance(ldm.get("policy_entries"), list) else []
    policy_fields = sorted(
        {
            str(key)
            for item in policy_entries
            if isinstance(item, dict)
            for key in item
        }
    )
    return {
        "schema_version": "lifecycle_source_contract_snapshot_v1",
        "source_keys": sorted(str(key) for key, value in source_map.items() if value),
        "sections": sections,
        "policy_entry_count": len([item for item in policy_entries if isinstance(item, dict)]),
        "policy_fields": policy_fields,
    }


def _compare_source_contracts(current: dict[str, Any], previous: dict[str, Any]) -> list[dict[str, Any]]:
    if not previous:
        return []
    changes: list[dict[str, Any]] = []

    def _add(change_type: str, severity: str, subject: str, detail: dict[str, Any]) -> None:
        changes.append(
            {
                "change_type": change_type,
                "severity": severity,
                "subject": subject,
                "detail": detail,
                "decision_authority": "source_contract_drift_detection",
            }
        )

    current_sources = set(current.get("source_keys") or [])
    previous_sources = set(previous.get("source_keys") or [])
    for key in sorted(current_sources - previous_sources):
        _add("source_added", "warning", key, {"source_key": key})
    for key in sorted(previous_sources - current_sources):
        _add("source_removed", "fail", key, {"source_key": key})

    current_sections = current.get("sections") if isinstance(current.get("sections"), dict) else {}
    previous_sections = previous.get("sections") if isinstance(previous.get("sections"), dict) else {}
    for section_name in sorted(set(current_sections) | set(previous_sections)):
        current_section = current_sections.get(section_name) if isinstance(current_sections.get(section_name), dict) else {}
        previous_section = previous_sections.get(section_name) if isinstance(previous_sections.get(section_name), dict) else {}
        for field_name in sorted(set(current_section.get("bucket_fields") or []) - set(previous_section.get("bucket_fields") or [])):
            _add("bucket_field_added", "warning", section_name, {"field": field_name})
        for field_name in sorted(set(previous_section.get("bucket_fields") or []) - set(current_section.get("bucket_fields") or [])):
            _add("bucket_field_removed", "fail", section_name, {"field": field_name})
        for bucket_type in sorted(set(current_section.get("bucket_types") or []) - set(previous_section.get("bucket_types") or [])):
            _add("bucket_type_added", "warning", section_name, {"bucket_type": bucket_type})
        for bucket_type in sorted(set(previous_section.get("bucket_types") or []) - set(current_section.get("bucket_types") or [])):
            _add("bucket_type_removed", "warning", section_name, {"bucket_type": bucket_type})
        for key in sorted(set(current_section.get("dimension_keys") or []) - set(previous_section.get("dimension_keys") or [])):
            _add("dimension_key_added", "warning", section_name, {"dimension_key": key})
        for key in sorted(set(previous_section.get("dimension_keys") or []) - set(current_section.get("dimension_keys") or [])):
            _add("dimension_key_removed", "warning", section_name, {"dimension_key": key})
    return changes


def _relation_for(bucket_type: str, bucket_key: str) -> str:
    if "unknown" in bucket_key or bucket_type.endswith("_unknown"):
        return "new_bucket_candidate"
    if bucket_type.startswith("combo_"):
        return "existing_bucket_refinement"
    return "existing_bucket_refinement"


def _recommended_action(route: str) -> str:
    if route == "candidate_recovery_or_relax":
        return "relax_or_recover"
    if route == "candidate_tighten_or_exclude":
        return "tighten_or_exclude"
    if route == "hold_sample":
        return "keep_collecting"
    if route == "hold_no_edge":
        return "hold_no_edge"
    return route or "observe"


def _live_family_for(stage: str, bucket_type: str, bucket_key: str) -> str | None:
    if stage == "entry" and bucket_type == "combo_entry_spot" and bucket_key == ENTRY_LIVE_AUTO_BUCKET_KEY:
        return ENTRY_LIVE_AUTO_FAMILY
    if stage == "scale_in" and bucket_type in {"arm", "blocker_namespace"} and bucket_key in {"PYRAMID", "AVG_DOWN_ONLY"}:
        return SCALE_IN_LIVE_AUTO_FAMILY
    return None


def _classify_bucket(stage: str, bucket: dict[str, Any]) -> tuple[str, str | None]:
    bucket_type = str(bucket.get("bucket_type") or "")
    bucket_key = str(bucket.get("bucket_key") or "")
    route = str(bucket.get("recommended_route") or "")
    quality = str(bucket.get("source_quality_gate") or "")
    if quality != "pass":
        return "source_only_keep_collecting", None
    live_family = _live_family_for(stage, bucket_type, bucket_key)
    if (
        live_family
        and stage == "entry"
        and route == "candidate_recovery_or_relax"
    ) or (
        live_family
        and stage == "scale_in"
        and route == "candidate_tighten_or_exclude"
    ):
        return "live_auto_apply_ready", live_family
    if "unknown" in bucket_key:
        return "source_only_keep_collecting", None
    if route in {"candidate_recovery_or_relax", "candidate_tighten_or_exclude"}:
        return "sim_auto_approved", None
    return "source_only_keep_collecting", None


def _candidate_from_bucket(stage: str, bucket: dict[str, Any]) -> dict[str, Any]:
    bucket_type = str(bucket.get("bucket_type") or "bucket")
    bucket_key = str(bucket.get("bucket_key") or "unknown")
    state, live_family = _classify_bucket(stage, bucket)
    relation = _relation_for(bucket_type, bucket_key)
    bucket_id = f"{stage}:{bucket_type}:{_slug(bucket_key)}"
    source_bucket_id = _stable_source_bucket_id(stage, bucket_type, bucket_key)
    joined_sample = _safe_int(bucket.get("joined_sample"))
    sample = _safe_int(bucket.get("sample"), joined_sample)
    return {
        "bucket_id": bucket_id,
        "source_bucket_id": source_bucket_id,
        "parent_bucket_id": f"{stage}:{bucket_type}",
        "stage": stage,
        "bucket_type": bucket_type,
        "bucket_key": bucket_key,
        "source_bucket_kind": _source_bucket_kind(state, bucket),
        "bucket_relation": relation,
        "classification_state": state,
        "live_auto_apply_family": live_family,
        "source_dimensions": _source_dimensions(bucket_type, bucket_key),
        "primary_decision_metric": "source_quality_adjusted_ev_pct",
        "sample": sample,
        "joined_sample": joined_sample,
        "join_rate": _safe_float(bucket.get("join_rate"), None),
        "source_quality_adjusted_ev_pct": _safe_float(bucket.get("source_quality_adjusted_ev_pct"), None),
        "equal_weight_avg_profit_pct": _safe_float(bucket.get("equal_weight_avg_profit_pct"), None),
        "diagnostic_win_rate": _safe_float(bucket.get("diagnostic_win_rate"), None),
        "mfe_10m_pct": _safe_float(bucket.get("mfe_10m_pct"), None),
        "mae_10m_pct": _safe_float(bucket.get("mae_10m_pct"), None),
        "mfe_30m_pct": _safe_float(bucket.get("mfe_30m_pct"), None),
        "mae_30m_pct": _safe_float(bucket.get("mae_30m_pct"), None),
        "mfe_60m_pct": _safe_float(bucket.get("mfe_60m_pct"), None),
        "mae_60m_pct": _safe_float(bucket.get("mae_60m_pct"), None),
        "next_day_mfe_pct": _safe_float(bucket.get("next_day_mfe_pct"), None),
        "next_day_mae_pct": _safe_float(bucket.get("next_day_mae_pct"), None),
        "source_quality_gate": bucket.get("source_quality_gate"),
        "recommended_route": bucket.get("recommended_route"),
        "recommended_action": _recommended_action(str(bucket.get("recommended_route") or "")),
        "recommended_resolution": _recommended_resolution(state, bucket),
        "unknown_dimension_counts": bucket.get("unknown_dimension_counts") or {},
        "unknown_reason_counts": bucket.get("unknown_reason_counts") or {},
        "source_field_coverage": bucket.get("source_field_coverage") or {},
        "actual_order_submitted": False,
        "broker_order_forbidden": state != "live_auto_apply_ready",
        "decision_authority": (
            "lifecycle_bucket_discovery_live_auto_apply"
            if state == "live_auto_apply_ready"
            else "lifecycle_bucket_discovery_sim_auto"
            if state == "sim_auto_approved"
            else "lifecycle_bucket_discovery_source_quality"
        ),
        "runtime_effect": state == "live_auto_apply_ready",
        "runtime_effect_after_approval": "live_auto_apply_without_human_approval"
        if state == "live_auto_apply_ready"
        else "sim_only_bucket_policy",
        "forbidden_uses": [
            "hard_safety_bypass",
            "broker_account_order_guard_bypass",
            "stale_quote_submit",
            "provider_route_change",
            "bot_restart_trigger",
            "position_cap_release",
        ],
    }


def _source_drift_candidates(changes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for change in changes:
        if not isinstance(change, dict):
            continue
        change_type = str(change.get("change_type") or "source_contract_change")
        severity = str(change.get("severity") or "warning")
        subject = str(change.get("subject") or "source_contract")
        detail = change.get("detail") if isinstance(change.get("detail"), dict) else {}
        state = "code_patch_required" if severity == "fail" else "new_bucket_candidate"
        if change_type in {"source_removed", "bucket_field_removed"}:
            state = "code_patch_required"
        bucket_id = f"source_contract:{change_type}:{_slug(subject)}:{_slug(json.dumps(detail, ensure_ascii=False, sort_keys=True), max_len=48)}"
        candidates.append(
            {
                "bucket_id": bucket_id,
                "source_bucket_id": _stable_source_bucket_id("source_contract", change_type, subject),
                "parent_bucket_id": "source_contract:schema_drift",
                "stage": "source_contract",
                "bucket_type": change_type,
                "bucket_key": subject,
                "source_bucket_kind": "source_contract_gap",
                "bucket_relation": "new_bucket_candidate",
                "classification_state": state,
                "live_auto_apply_family": None,
                "source_dimensions": {"change_type": change_type, "subject": subject},
                "primary_decision_metric": "source_contract_change",
                "sample": 0,
                "joined_sample": 0,
                "join_rate": None,
                "source_quality_adjusted_ev_pct": None,
                "source_quality_gate": "source_contract_drift",
                "recommended_route": "instrumentation_gap",
                "recommended_action": "update_source_contract_or_taxonomy",
                "recommended_resolution": "update_source_contract_or_taxonomy",
                "unknown_dimension_counts": {},
                "unknown_reason_counts": {},
                "source_field_coverage": {},
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "decision_authority": "source_contract_drift_detection",
                "runtime_effect": False,
                "runtime_effect_after_approval": "none_source_contract_patch_required",
                "source_contract_change": change,
                "forbidden_uses": [
                    "broker_submit",
                    "runtime_threshold_apply",
                    "provider_route_change",
                    "bot_restart_trigger",
                    "position_cap_release",
                ],
            }
        )
    return candidates


def _candidates_from_attribution(payload: dict[str, Any], stage: str, key: str) -> list[dict[str, Any]]:
    attribution = payload.get(key) if isinstance(payload.get(key), dict) else {}
    buckets = attribution.get("buckets") if isinstance(attribution.get("buckets"), list) else []
    candidates = [_candidate_from_bucket(stage, bucket) for bucket in buckets if isinstance(bucket, dict)]
    candidates.sort(
        key=lambda item: (
            0 if item["classification_state"] == "live_auto_apply_ready" else 1,
            0 if item["classification_state"] == "sim_auto_approved" else 1,
            -_safe_int(item.get("joined_sample")),
            item["bucket_id"],
        )
    )
    return candidates


def _policy_stage_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    entries = payload.get("policy_entries") if isinstance(payload.get("policy_entries"), list) else []
    candidates: list[dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        stage = str(entry.get("stage") or "unknown")
        bucket_id = f"{stage}:stage_policy:{_slug(entry.get('policy_key') or stage)}"
        policy_key = str(entry.get("policy_key") or stage)
        state = (
            "sim_auto_approved"
            if str(entry.get("source_quality_gate") or "") == "pass"
            else "source_only_keep_collecting"
        )
        candidates.append(
            {
                "bucket_id": bucket_id,
                "source_bucket_id": _stable_source_bucket_id(stage, "stage_policy", policy_key),
                "parent_bucket_id": f"{stage}:stage_policy",
                "stage": stage,
                "bucket_type": "stage_policy",
                "bucket_key": policy_key,
                "source_bucket_kind": "sim_auto_policy" if state == "sim_auto_approved" else "source_only_observation",
                "bucket_relation": "existing_bucket_refinement",
                "classification_state": state,
                "live_auto_apply_family": None,
                "source_dimensions": {"policy_key": str(entry.get("policy_key") or stage)},
                "primary_decision_metric": "stage_ev_composite_pct",
                "sample": _safe_int(entry.get("sample")),
                "joined_sample": _safe_int(entry.get("joined_sample")),
                "join_rate": _safe_float(entry.get("join_rate"), None),
                "source_quality_adjusted_ev_pct": _safe_float(entry.get("stage_ev_composite_pct"), None),
                "source_quality_gate": entry.get("source_quality_gate"),
                "recommended_action": str(entry.get("selected_action") or "NO_CHANGE"),
                "recommended_resolution": "next_preopen_sim_policy_input"
                if state == "sim_auto_approved"
                else "keep_collecting_until_sample_floor",
                "unknown_dimension_counts": {},
                "unknown_reason_counts": {},
                "source_field_coverage": {},
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "decision_authority": "lifecycle_bucket_discovery_stage_policy_sim_auto",
                "runtime_effect": False,
                "runtime_effect_after_approval": "sim_only_stage_policy",
                "forbidden_uses": [
                    "hard_safety_bypass",
                    "broker_submit",
                    "provider_route_change",
                    "bot_restart_trigger",
                    "position_cap_release",
                ],
            }
        )
    return candidates


def _build_ai_review_context(report: dict[str, Any]) -> dict[str, Any]:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    surfaced = report.get("surfaced_candidates") if isinstance(report.get("surfaced_candidates"), list) else []
    compact_candidates = [
        {
            "bucket_id": item.get("bucket_id"),
            "stage": item.get("stage"),
            "bucket_type": item.get("bucket_type"),
            "bucket_key": item.get("bucket_key"),
            "bucket_relation": item.get("bucket_relation"),
            "classification_state": item.get("classification_state"),
            "live_auto_apply_family": item.get("live_auto_apply_family"),
            "source_dimensions": item.get("source_dimensions"),
            "primary_decision_metric": item.get("primary_decision_metric"),
            "joined_sample": item.get("joined_sample"),
            "join_rate": item.get("join_rate"),
            "source_quality_adjusted_ev_pct": item.get("source_quality_adjusted_ev_pct"),
            "recommended_route": item.get("recommended_route"),
            "recommended_action": item.get("recommended_action"),
            "source_quality_gate": item.get("source_quality_gate"),
        }
        for item in surfaced[:60]
        if isinstance(item, dict)
    ]
    return {
        "review_task": "two_pass_lifecycle_bucket_discovery_review",
        "pass_1": "Interpret whether each surfaced bucket is a refinement of an existing taxonomy bucket or a genuinely new bucket candidate.",
        "pass_2": "Audit the pass_1 interpretation and produce final_conclusions. Do not block deterministic live candidates just because the edge is small, new, or ambiguous.",
        "authority": "review_only_no_broker_order_no_provider_route_no_bot_restart_no_cap_release",
        "review_policy": {
            "language": "English only. Keep explanations concise to reduce tokens.",
            "no_promotion_authority": "You cannot promote a non-live deterministic candidate to live_auto_apply_ready.",
            "non_conservative_live_policy": (
                "If a deterministic live_auto_apply_ready candidate has any plausible positive effect, including only 1%, "
                "do not block it solely for low effect size, low confidence, novelty, or ambiguity. Keep live and rely on post-apply verification."
            ),
            "block_only_for_explicit_gaps": (
                "Block or downgrade a deterministic live candidate only for explicit source-quality, schema, env mapping, runtime hook, "
                "post-apply attribution, safety, broker, stale quote, qty/cooldown, provider, cap, forbidden-use, leakage, or missing-contract gaps."
            ),
        },
        "date": report.get("date"),
        "summary": summary,
        "source_contract": report.get("source_contract"),
        "source_contract_changes": report.get("source_contract_changes") or [],
        "surfaced_candidates": compact_candidates,
        "allowed_final_states": sorted(FINAL_CLASSIFICATION_STATES),
        "allowed_relations": sorted(FINAL_RELATIONS),
        "safety_rule": (
            "AI may block or downgrade a deterministic live bucket only for explicit contract/source-quality/safety gaps, "
            "and may not create live_auto_apply_ready unless the input candidate is already live_auto_apply_ready "
            "and has a live_auto_apply_family."
        ),
    }


def _build_ai_review_instructions() -> str:
    return (
        "You are the tier3 lifecycle bucket discovery reviewer.\n"
        "Use English only and keep wording concise to reduce tokens.\n"
        "Your job is a two-pass review: first interpret bucket taxonomy, then audit that interpretation.\n"
        "Return only strict JSON using lifecycle_bucket_discovery_review_v1.\n"
        "Do not approve broker orders, provider route changes, bot restarts, cap release, or intraday threshold mutation.\n"
        "Classify existing_bucket_refinement when a bucket is a child/refinement of a known stage taxonomy.\n"
        "Classify new_bucket_candidate when existing taxonomy cannot explain the source dimensions or source contract drift.\n"
        "Do not be conservative by default. A deterministic live candidate with even a 1% plausible positive effect should not be blocked solely for small effect size, novelty, low confidence, or ambiguity.\n"
        "When the decision is ambiguous, keep deterministic live candidates live and rely on post-apply verification.\n"
        "Use runtime_blocked_contract_gap or code_patch_required only for explicit source-quality, source schema, env mapping, runtime hook, post-apply attribution, safety, broker, stale quote, qty/cooldown, provider, cap, forbidden-use, leakage, or missing-contract gaps.\n"
        "live_auto_apply_ready is allowed only if the input bucket already has live_auto_apply_family and deterministic live_auto_apply_ready.\n"
    )


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
    interpretation = payload.get("interpretation") if isinstance(payload.get("interpretation"), dict) else {}
    audit = payload.get("audit") if isinstance(payload.get("audit"), dict) else {}
    conclusions = payload.get("final_conclusions") if isinstance(payload.get("final_conclusions"), list) else []
    if not interpretation:
        warnings.append("ai_review_interpretation_missing")
    if not audit:
        warnings.append("ai_review_audit_missing")
    if not isinstance(conclusions, list):
        warnings.append("ai_review_final_conclusions_invalid")
    for item in conclusions:
        if not isinstance(item, dict):
            warnings.append("ai_review_final_conclusion_non_dict")
            continue
        if str(item.get("final_bucket_relation") or "") not in FINAL_RELATIONS:
            warnings.append(f"ai_review_invalid_relation:{item.get('bucket_id')}")
        if str(item.get("final_classification_state") or "") not in FINAL_CLASSIFICATION_STATES:
            warnings.append(f"ai_review_invalid_state:{item.get('bucket_id')}")
    if warnings:
        return "parse_rejected", payload, warnings
    return "parsed", payload, []


def _call_openai_ai_review(input_context: dict[str, Any]) -> tuple[Any | None, dict[str, Any]]:
    try:
        from openai import OpenAI, RateLimitError
        from src.engine.ai_response_contracts import build_openai_response_text_format
        from src.engine.daily_threshold_cycle_report import (
            _extract_openai_response_text,
            _load_threshold_ai_openai_keys,
        )
    except Exception as exc:
        return None, {"provider": "openai", "status": "unavailable", "reason": f"openai import failed: {exc}"}

    api_keys = _load_threshold_ai_openai_keys()
    if not api_keys:
        return None, {"provider": "openai", "status": "unavailable", "reason": "OPENAI_API_KEY not configured"}

    prompt = json.dumps(input_context, ensure_ascii=False, indent=2, default=str)
    errors: list[dict[str, str]] = []
    for attempt_index, (key_name, api_key) in enumerate(api_keys, start=1):
        try:
            client = OpenAI(api_key=api_key)
            response = client.responses.create(
                model=AI_REVIEW_MODEL,
                instructions=_build_ai_review_instructions(),
                input=prompt,
                text={
                    "format": build_openai_response_text_format(AI_REVIEW_SCHEMA_NAME),
                    "verbosity": "low",
                },
                reasoning={"effort": "high"},
                store=False,
                metadata={
                    "endpoint_name": "lifecycle_bucket_discovery_review",
                    "schema_name": AI_REVIEW_SCHEMA_NAME,
                    "report_type": "lifecycle_bucket_discovery",
                },
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
                "reasoning_effort": "high",
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
        "model": AI_REVIEW_MODEL,
        "errors": errors[-3:],
    }


def _candidate_index(candidates: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        str(item.get("bucket_id")): item
        for item in candidates
        if isinstance(item, dict) and item.get("bucket_id")
    }


def _explicit_ai_block_allowed(reason: str, final_state: str) -> bool:
    if final_state not in {
        "runtime_blocked_contract_gap",
        "code_patch_required",
        "code_review_failed",
        "automation_handoff_gap",
    }:
        return False
    text = reason.lower()
    return any(term in text for term in AI_EXPLICIT_BLOCK_TERMS)


def _apply_ai_review(
    candidates: list[dict[str, Any]],
    *,
    ai_status: str,
    ai_payload: dict[str, Any],
    warnings: list[str],
) -> list[dict[str, Any]]:
    updated = [dict(item) for item in candidates]
    by_id = _candidate_index(updated)
    if ai_status != "parsed":
        for item in updated:
            if item.get("classification_state") == "live_auto_apply_ready":
                item["ai_review_status"] = ai_status
                item["ai_review_followup_required"] = "post_apply_verification"
        if any(item.get("ai_review_followup_required") for item in updated):
            warnings.append(f"ai_two_pass_review_{ai_status}_live_auto_deferred_to_post_apply")
        return updated

    conclusions = ai_payload.get("final_conclusions") if isinstance(ai_payload.get("final_conclusions"), list) else []
    for conclusion in conclusions:
        if not isinstance(conclusion, dict):
            continue
        item = by_id.get(str(conclusion.get("bucket_id") or ""))
        if not item:
            continue
        final_relation = str(conclusion.get("final_bucket_relation") or "")
        final_state = str(conclusion.get("final_classification_state") or "")
        final_decision = str(conclusion.get("final_decision") or "")
        final_reason = str(conclusion.get("reason") or "")
        if final_relation in FINAL_RELATIONS and final_relation != "unclear":
            item["bucket_relation"] = final_relation
        item["ai_final_bucket_relation"] = final_relation
        item["ai_final_classification_state"] = final_state
        item["ai_final_decision"] = final_decision
        item["ai_final_reason"] = final_reason
        if final_state not in FINAL_CLASSIFICATION_STATES or final_decision == "keep":
            continue
        if final_state == "live_auto_apply_ready":
            if item.get("classification_state") == "live_auto_apply_ready" and item.get("live_auto_apply_family"):
                continue
            item["classification_state"] = "runtime_blocked_contract_gap"
            item["runtime_effect"] = False
            item["broker_order_forbidden"] = True
            item["ai_review_blocked_reason"] = "ai_live_auto_without_deterministic_contract"
            continue
        if final_state in {
            "source_only_keep_collecting",
            "sim_auto_approved",
            "runtime_blocked_contract_gap",
            "code_patch_required",
            "code_review_failed",
            "automation_handoff_gap",
            "new_bucket_candidate",
        }:
            if (
                item.get("classification_state") == "live_auto_apply_ready"
                and item.get("live_auto_apply_family")
                and not _explicit_ai_block_allowed(final_reason, final_state)
            ):
                item["ai_review_block_ignored_reason"] = (
                    "ambiguous_or_non_contract_gap_live_then_verify"
                )
                item["ai_review_followup_required"] = "post_apply_verification"
                warnings.append("ai_review_ambiguous_live_candidate_kept_for_post_apply")
                continue
            item["classification_state"] = final_state
            item["runtime_effect"] = False if final_state != "live_auto_apply_ready" else item.get("runtime_effect")
            item["broker_order_forbidden"] = final_state != "live_auto_apply_ready"
    return updated


def _finalize_report(
    report: dict[str, Any],
    candidates: list[dict[str, Any]],
    warnings: list[str],
) -> dict[str, Any]:
    state_counts = Counter(str(item.get("classification_state") or "unknown") for item in candidates)
    stage_counts = Counter(str(item.get("stage") or "unknown") for item in candidates)
    source_bucket_kind_counts = Counter(str(item.get("source_bucket_kind") or "unknown") for item in candidates)
    unknown_reason_counts: Counter[str] = Counter()
    for item in candidates:
        counts = item.get("unknown_reason_counts") if isinstance(item.get("unknown_reason_counts"), dict) else {}
        for key, value in counts.items():
            unknown_reason_counts[str(key)] += _safe_int(value)
    surfaced = [
        item
        for item in candidates
        if str(item.get("classification_state") or "") in AUTO_SURFACE_STATES
    ]
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    summary.update(
        {
            "candidate_count": len(candidates),
            "surfaced_candidate_count": len(surfaced),
            "sim_auto_approved_count": state_counts.get("sim_auto_approved", 0),
            "live_auto_apply_ready_count": state_counts.get("live_auto_apply_ready", 0),
            "new_bucket_candidate_count": state_counts.get("new_bucket_candidate", 0),
            "code_patch_required_count": state_counts.get("code_patch_required", 0),
            "automation_handoff_gap_count": state_counts.get("automation_handoff_gap", 0),
            "state_counts": dict(state_counts),
            "stage_counts": dict(stage_counts),
            "source_bucket_kind_counts": dict(source_bucket_kind_counts),
            "unknown_reason_counts": dict(unknown_reason_counts),
            "human_intervention_required": False,
            "warnings": warnings,
        }
    )
    report["summary"] = summary
    report["candidates"] = candidates[:500]
    report["surfaced_candidates"] = surfaced[:200]
    report["live_auto_apply_candidates"] = [
        item for item in candidates if item.get("classification_state") == "live_auto_apply_ready"
    ]
    report["sim_auto_approved_candidates"] = [
        item for item in candidates if item.get("classification_state") == "sim_auto_approved"
    ][:200]
    report["warnings"] = warnings
    return report


def build_lifecycle_bucket_discovery_report(
    target_date: str,
    *,
    ai_review_provider: str | None = None,
    ai_raw_response: Any | None = None,
) -> dict[str, Any]:
    target_date = str(target_date).strip()
    ldm_path = LDM_REPORT_DIR / f"lifecycle_decision_matrix_{target_date}.json"
    ldm = _load_json(ldm_path)
    warnings: list[str] = []
    if not ldm:
        warnings.append("lifecycle_decision_matrix_missing")
    candidates: list[dict[str, Any]] = []
    source_contract = _source_contract_snapshot(ldm) if ldm else {}
    previous = _previous_report(target_date)
    previous_contract = (
        previous.get("source_contract")
        if isinstance(previous.get("source_contract"), dict)
        else {}
    )
    source_contract_changes = _compare_source_contracts(source_contract, previous_contract)
    if ldm:
        candidates.extend(_candidates_from_attribution(ldm, "entry", "entry_bucket_attribution"))
        candidates.extend(_candidates_from_attribution(ldm, "scale_in", "scale_in_bucket_attribution"))
        candidates.extend(_candidates_from_attribution(ldm, "overnight", "overnight_bucket_attribution"))
        candidates.extend(_policy_stage_candidates(ldm))
        candidates.extend(_source_drift_candidates(source_contract_changes))
    source_contract_status = (
        "fail"
        if any(str(item.get("severity")) == "fail" for item in source_contract_changes)
        else "warning"
        if source_contract_changes
        else "pass"
    )
    if source_contract_status != "pass":
        warnings.append(f"source_contract_drift_{source_contract_status}")
    report = {
        "schema_version": DISCOVERY_SCHEMA_VERSION,
        "date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "report_type": "lifecycle_bucket_discovery",
        "runtime_effect": False,
        "decision_authority": "postclose_lifecycle_bucket_discovery_classifier",
        "metric_role": "primary_ev",
        "window_policy": "daily_lifecycle_bucket_discovery_with_preopen_auto_apply",
        "sample_floor": "source_bucket_sample_floor",
        "primary_decision_metric": "source_quality_adjusted_ev_pct",
        "source_quality_gate": "exact_joined_lifecycle_rows_or_source_bucket_quality",
        "forbidden_uses": [
            "hard_safety_bypass",
            "broker_account_order_guard_bypass",
            "stale_quote_submit",
            "provider_route_change",
            "bot_restart_trigger",
            "position_cap_release",
        ],
        "sources": {
            "lifecycle_decision_matrix": str(ldm_path) if ldm_path.exists() else None,
        },
        "source_contract": source_contract,
        "source_contract_previous_hash": _text_hash(previous_contract) if previous_contract else None,
        "source_contract_hash": _text_hash(source_contract) if source_contract else None,
        "source_contract_changes": source_contract_changes,
        "summary": {
            "human_intervention_required": False,
            "status": "pass" if ldm else "fail",
            "source_contract_status": source_contract_status,
            "source_contract_change_count": len(source_contract_changes),
            "warnings": warnings,
        },
        "warnings": warnings,
    }
    report = _finalize_report(report, candidates, warnings)

    provider = str(
        ai_review_provider
        if ai_review_provider is not None
        else os.getenv("KORSTOCKSCAN_LIFECYCLE_BUCKET_DISCOVERY_AI_REVIEW_PROVIDER", AI_REVIEW_DEFAULT_PROVIDER)
    ).strip().lower() or "none"
    ai_context = _build_ai_review_context(report)
    raw_response = ai_raw_response
    provider_status: dict[str, Any] = {
        "provider": provider,
        "status": "disabled" if provider in {"none", "off", "false", "0"} else "not_called",
        "model": AI_REVIEW_MODEL if provider not in {"none", "off", "false", "0"} else None,
        "schema_name": AI_REVIEW_SCHEMA_NAME,
        "input_context_hash": _text_hash(ai_context),
    }
    if raw_response is None and provider == "openai":
        raw_response, provider_status = _call_openai_ai_review(ai_context)
    ai_status, ai_payload, ai_warnings = _parse_ai_review_response(raw_response)
    if provider in {"none", "off", "false", "0"} and raw_response is None:
        ai_status = "disabled"
        ai_payload = {}
        ai_warnings = ["ai_review_provider_disabled"]
    warnings.extend(ai_warnings)
    report["ai_two_pass_review"] = {
        "provider": provider,
        "status": ai_status,
        "model": provider_status.get("model") or (AI_REVIEW_MODEL if provider == "openai" else None),
        "model_tier": "tier3",
        "schema_name": AI_REVIEW_SCHEMA_NAME,
        "provider_status": provider_status,
        "input_context_hash": _text_hash(ai_context),
        "interpretation": ai_payload.get("interpretation") if isinstance(ai_payload.get("interpretation"), dict) else {},
        "audit": ai_payload.get("audit") if isinstance(ai_payload.get("audit"), dict) else {},
        "final_conclusions": ai_payload.get("final_conclusions") if isinstance(ai_payload.get("final_conclusions"), list) else [],
        "warnings": ai_warnings,
    }
    candidates_after_ai = _apply_ai_review(
        report.get("candidates") if isinstance(report.get("candidates"), list) else [],
        ai_status=ai_status,
        ai_payload=ai_payload,
        warnings=warnings,
    )
    report = _finalize_report(report, candidates_after_ai, warnings)
    report["summary"]["ai_two_pass_review_status"] = ai_status
    report["summary"]["ai_two_pass_review_required"] = True
    return report


def _render_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    ai_review = report.get("ai_two_pass_review") if isinstance(report.get("ai_two_pass_review"), dict) else {}
    lines = [
        f"# Lifecycle Bucket Discovery - {report.get('date')}",
        "",
        "## 판정",
        f"- status: `{summary.get('status')}`",
        f"- source_contract_status: `{summary.get('source_contract_status')}` / changes: `{summary.get('source_contract_change_count')}`",
        f"- ai_two_pass_review: `{summary.get('ai_two_pass_review_status')}` / model: `{ai_review.get('model') or '-'}` / tier: `{ai_review.get('model_tier') or '-'}`",
        f"- surfaced_candidate_count: `{summary.get('surfaced_candidate_count')}`",
        f"- sim_auto_approved_count: `{summary.get('sim_auto_approved_count')}`",
        f"- live_auto_apply_ready_count: `{summary.get('live_auto_apply_ready_count')}`",
        f"- human_intervention_required: `{summary.get('human_intervention_required')}`",
        f"- warnings: `{summary.get('warnings') or []}`",
        "",
        "## 근거",
        "",
    ]
    if report.get("source_contract_changes"):
        lines.append("### Source Contract Changes")
        for change in (report.get("source_contract_changes") or [])[:12]:
            if isinstance(change, dict):
                lines.append(
                    f"- `{change.get('change_type')}` severity=`{change.get('severity')}` "
                    f"subject=`{change.get('subject')}` detail=`{change.get('detail') or {}}`"
                )
        lines.append("")
    if ai_review:
        audit = ai_review.get("audit") if isinstance(ai_review.get("audit"), dict) else {}
        lines.extend(
            [
                "### AI Two-Pass Review",
                f"- interpretation_count: `{len(((ai_review.get('interpretation') or {}).get('bucket_reviews') or []) if isinstance(ai_review.get('interpretation'), dict) else [])}`",
                f"- audit_status: `{audit.get('status') or '-'}`",
                f"- audit_issues: `{audit.get('issues') or []}`",
                f"- audit_reason: `{audit.get('reason') or '-'}`",
                "",
            ]
        )
    for item in (report.get("surfaced_candidates") or [])[:20]:
        lines.append(
            f"- `{item.get('bucket_id')}` stage=`{item.get('stage')}` "
            f"state=`{item.get('classification_state')}` action=`{item.get('recommended_action')}` "
            f"relation=`{item.get('bucket_relation')}` joined=`{item.get('joined_sample')}` "
            f"ev=`{item.get('source_quality_adjusted_ev_pct')}` ai_final=`{item.get('ai_final_decision') or '-'}`"
        )
    lines.extend(
        [
            "",
            "## 다음 액션",
            "- `sim_auto_approved` bucket은 다음 PREOPEN sim policy에 자동 반영한다.",
            "- `live_auto_apply_ready` bucket은 deterministic contract와 AI 2-pass 검증을 모두 통과한 경우에만 approval artifact 없이 다음 PREOPEN live auto apply 후보로 소비한다.",
            "- source contract drift는 `new_bucket_candidate` 또는 `code_patch_required`로 surfaced 하며 LDM/downstream 누락 감리에 들어간다.",
            "- downstream 누락은 postclose verifier에서 `automation_handoff_gap`으로 닫는다.",
        ]
    )
    return "\n".join(lines) + "\n"


def _write_catalog(report: dict[str, Any]) -> None:
    target_date = str(report.get("date") or "")
    CATALOG_DIR.mkdir(parents=True, exist_ok=True)
    catalog = {
        "schema_version": "lifecycle_bucket_catalog_v1",
        "date": target_date,
        "generated_at": report.get("generated_at"),
        "active_bucket_count": len(report.get("surfaced_candidates") or []),
        "buckets": report.get("surfaced_candidates") or [],
    }
    bucket_catalog_path(target_date).write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_sim_auto_approval(report: dict[str, Any]) -> None:
    target_date = str(report.get("date") or "")
    SIM_AUTO_APPROVAL_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "lifecycle_bucket_sim_auto_approval_v1",
        "date": target_date,
        "generated_at": report.get("generated_at"),
        "policy_id": "lifecycle_bucket_discovery_sim_auto_approval",
        "approved": True,
        "human_approval_required": False,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "decision_authority": "postclose_lifecycle_bucket_discovery_sim_auto",
        "policy_file": str(bucket_catalog_path(target_date)),
        "approved_bucket_ids": [
            str(item.get("bucket_id"))
            for item in (report.get("sim_auto_approved_candidates") or [])
            if item.get("bucket_id")
        ],
        "forbidden_uses": [
            "broker_submit",
            "runtime_threshold_apply",
            "provider_route_change",
            "bot_restart_trigger",
            "position_cap_release",
        ],
    }
    sim_auto_approval_path(target_date).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def write_lifecycle_bucket_discovery_report(
    target_date: str,
    *,
    ai_review_provider: str | None = None,
    ai_raw_response: Any | None = None,
) -> dict[str, Any]:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = build_lifecycle_bucket_discovery_report(
        target_date,
        ai_review_provider=ai_review_provider,
        ai_raw_response=ai_raw_response,
    )
    discovery_report_path(target_date).write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    discovery_markdown_path(target_date).write_text(_render_markdown(report), encoding="utf-8")
    _write_catalog(report)
    _write_sim_auto_approval(report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build lifecycle bucket discovery/classifier report.")
    parser.add_argument("--date", dest="target_date", default=date.today().isoformat())
    parser.add_argument(
        "--ai-review-provider",
        default=os.getenv("KORSTOCKSCAN_LIFECYCLE_BUCKET_DISCOVERY_AI_REVIEW_PROVIDER", AI_REVIEW_DEFAULT_PROVIDER),
        choices=["openai", "none", "off", "false", "0"],
        help="Provider for tier3 two-pass bucket interpretation/audit.",
    )
    args = parser.parse_args(argv)
    report = write_lifecycle_bucket_discovery_report(
        args.target_date,
        ai_review_provider=args.ai_review_provider,
    )
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report.get("summary", {}).get("status") == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
