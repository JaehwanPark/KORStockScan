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

from src.engine.ai.postclose_review_config import (
    PostcloseAIReviewConfig,
    resolve_postclose_ai_review_config,
)
from src.engine.automation.dual_candidate_review import (
    evidence_authority_contract,
    has_evidence_authority_violation,
    with_evidence_authority_forbidden_uses,
)
from src.engine.auto_promotion_contracts import (
    explicit_tier2_block_allowed,
    pre_final_promotion_contract,
    primary_ev_uplift_passes,
    tier2_fail_closed_reason,
)
from src.engine.lifecycle.bucket_taxonomy import (
    compare_taxonomy_proposals,
    default_ai_tier2_proposal,
    normalize_lifecycle_bucket,
)
from src.utils.constants import DATA_DIR


REPORT_DIR = DATA_DIR / "report" / "lifecycle_bucket_discovery"
LDM_REPORT_DIR = DATA_DIR / "report" / "lifecycle_decision_matrix"
CATALOG_DIR = DATA_DIR / "threshold_cycle" / "lifecycle_bucket_catalog"
SIM_AUTO_APPROVAL_DIR = DATA_DIR / "threshold_cycle" / "sim_auto_approvals"
CONTAMINATION_WINDOW_DIR = DATA_DIR / "threshold_cycle" / "contamination_windows"

ENTRY_LIVE_AUTO_FAMILY = "entry_wait6579_score66_69_recovery_gate_v1"
SCALE_IN_LIVE_AUTO_FAMILY = "scale_in_bucket_runtime_policy_v1"
GREENFIELD_REAL_ENV_FAMILY = "greenfield_real_environment_authority"
ENTRY_LIVE_AUTO_BUCKET_KEY = (
    "score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|"
    "liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_unknown"
)

DISCOVERY_SCHEMA_VERSION = "lifecycle_bucket_discovery_v1"
AI_REVIEW_SCHEMA_NAME = "lifecycle_bucket_discovery_review_v1"
AI_REVIEW_DEFAULT_PROVIDER = "openai"
AI_REVIEW_MODEL = "gpt-5.4"
AI_REVIEW_SOURCE_ONLY_MODEL = "gpt-5.4"
AI_REVIEW_SOURCE_ONLY_REASONING_EFFORT = "low"
LIVE_AUTO_STATES = {"live_auto_apply_ready"}
LIFECYCLE_FLOW_SIM_PROBE_STATE = "lifecycle_flow_sim_probe_candidate"
SIM_APPROVAL_STATES = {
    "sim_auto_approved",
    "entry_only_sim_auto_approved",
    LIFECYCLE_FLOW_SIM_PROBE_STATE,
}
EVIDENCE_GRADE_1_COMPLETED_SIM = "grade_1_completed_sim"
EVIDENCE_GRADE_2_COUNTERFACTUAL = "grade_2_counterfactual"
EVIDENCE_GRADE_MIXED_SOURCE = "mixed_source"
EVIDENCE_GRADE_SOURCE_ONLY = "source_only"
COUNTERFACTUAL_SOURCE_TOKENS = (
    "wait6579_ev_cohort",
    "missed_entry",
    "counterfactual",
)
MIXED_BUCKET_TYPES = {
    "score_band",
    "time_bucket",
    "stale_bucket",
}
AUTO_SURFACE_STATES = {
    "new_bucket_candidate",
    "sim_auto_approved",
    "entry_only_sim_auto_approved",
    LIFECYCLE_FLOW_SIM_PROBE_STATE,
    "entry_only_source_candidate",
    "live_auto_apply_ready",
    "runtime_blocked_contract_gap",
    "code_patch_required",
    "code_review_failed",
    "automation_handoff_gap",
}
FINAL_CLASSIFICATION_STATES = {
    "source_only_keep_collecting",
    "sim_auto_approved",
    "entry_only_sim_auto_approved",
    LIFECYCLE_FLOW_SIM_PROBE_STATE,
    "entry_only_source_candidate",
    "live_auto_apply_ready",
    "runtime_blocked_contract_gap",
    "code_patch_required",
    "code_review_failed",
    "automation_handoff_gap",
    "new_bucket_candidate",
}
FINAL_RELATIONS = {"existing_bucket_refinement", "new_bucket_candidate", "unclear"}
AI_TAXONOMY_DECISIONS = {
    "merge",
    "absorb_as_dimension",
    "create_new_metric",
    "create_new_dimension",
    "keep_bucket",
    "reject",
    "source_quality_blocker",
    "instrumentation_gap",
}
AI_TAXONOMY_SOURCES = {"deterministic", "ai_tier2", "hybrid", "reject"}
REQUIRED_TAXONOMY_CONTRACT_FIELDS = {
    "metric_role",
    "decision_authority",
    "window_policy",
    "sample_floor",
    "primary_decision_metric",
    "source_quality_gate",
    "forbidden_uses",
}
BASE_FORBIDDEN_USES = with_evidence_authority_forbidden_uses(
    [
        "hard_safety_bypass",
        "broker_submit",
        "broker_account_order_guard_bypass",
        "runtime_threshold_apply",
        "stale_quote_submit",
        "provider_route_change",
        "bot_restart_trigger",
        "position_cap_release",
    ]
)
SOURCE_CONTRACT_SCHEMA_VERSION = "lifecycle_source_contract_snapshot_v2"
SOURCE_CONTRACT_SECTION_SCHEMAS: dict[str, dict[str, tuple[str, ...]]] = {
    "lifecycle_flow_bucket_attribution": {
        "bucket_types": ("combo_lifecycle_flow",),
        "bucket_fields": (
            "ai_inference_proposal",
            "attribution_key",
            "bucket_key",
            "bucket_type",
            "child_bucket_ids",
            "complete_flow_count",
            "decision_authority",
            "diagnostic_win_rate",
            "entry_bucket_id",
            "equal_weight_avg_profit_pct",
            "exit_bucket_id",
            "fallback_identity_count",
            "forbidden_uses",
            "holding_bucket_id",
            "incomplete_flow_count",
            "join_rate",
            "joined_sample",
            "lifecycle_flow_bucket_id",
            "metric_scope",
            "recommended_route",
            "rollback_guard",
            "runtime_effect",
            "sample",
            "scale_in_bucket_id",
            "scale_in_bucket_ids",
            "source_quality_adjusted_ev_pct",
            "source_quality_gate",
            "stage_contract",
            "submit_bucket_id",
        ),
        "dimension_keys": ("entry", "exit", "holding", "scale_in", "submit"),
    },
    "entry_bucket_attribution": {
        "bucket_types": (
            "chosen_action",
            "combo_entry_spot",
            "exit_rule",
            "liquidity_bucket",
            "overbought_bucket",
            "score_band",
            "source_stage",
            "stale_bucket",
            "strength_bucket",
            "time_bucket",
        ),
        "bucket_fields": (
            "bucket_key",
            "bucket_type",
            "close_10m_pct",
            "close_30m_pct",
            "close_60m_pct",
            "decision_authority",
            "diagnostic_win_rate",
            "equal_weight_avg_profit_pct",
            "forbidden_uses",
            "join_rate",
            "joined_sample",
            "mae_10m_pct",
            "mae_30m_pct",
            "mae_60m_pct",
            "mfe_10m_pct",
            "mfe_30m_pct",
            "mfe_60m_pct",
            "recommended_resolution",
            "recommended_route",
            "runtime_effect",
            "sample",
            "source_field_coverage",
            "source_quality_adjusted_ev_pct",
            "source_quality_gate",
            "unknown_dimension_counts",
            "unknown_reason_counts",
        ),
        "dimension_keys": (
            "chosen_action",
            "exit_rule",
            "liquidity",
            "liquidity_bucket",
            "overbought",
            "overbought_bucket",
            "score",
            "score_band",
            "source",
            "source_stage",
            "stale",
            "stale_bucket",
            "strength_bucket",
            "time",
            "time_bucket",
        ),
    },
    "submit_bucket_attribution": {
        "bucket_types": (
            "actual_order_submitted",
            "broker_order_forbidden",
            "combo_submit_quality",
            "latency_reason",
            "latency_state",
            "liquidity_bucket",
            "liquidity_guard_action",
            "overbought_bucket",
            "overbought_guard_action",
            "price_below_bid_bucket",
            "price_resolution_bucket",
            "quote_age_bucket",
            "revalidation_state",
            "submit_source_stage",
            "would_limit_fill",
        ),
        "bucket_fields": (
            "allowed_runtime_apply",
            "bucket_key",
            "bucket_type",
            "decision_authority",
            "forbidden_uses",
            "join_rate",
            "joined_sample",
            "recommended_resolution",
            "recommended_route",
            "runtime_effect",
            "sample",
            "source_field_coverage",
            "source_quality_adjusted_ev_pct",
            "source_quality_gate",
            "unknown_dimension_counts",
            "unknown_reason_counts",
        ),
        "dimension_keys": (
            "actual_order_submitted",
            "broker_order_forbidden",
            "fill",
            "latency",
            "latency_reason",
            "latency_state",
            "liquidity",
            "liquidity_bucket",
            "liquidity_guard",
            "liquidity_guard_action",
            "overbought",
            "overbought_bucket",
            "overbought_guard_action",
            "price_below_bid_bucket",
            "price_resolution",
            "price_resolution_bucket",
            "quote_age",
            "quote_age_bucket",
            "revalidation",
            "revalidation_state",
            "source",
            "submit_source_stage",
            "submitted",
            "would_limit_fill",
        ),
    },
    "holding_bucket_attribution": {
        "bucket_types": ("combo_holding_flow", "held_bucket", "holding_action", "holding_source_stage", "profit_band"),
        "bucket_fields": (
            "ai_inference_proposal",
            "allowed_runtime_apply",
            "bucket_key",
            "bucket_type",
            "decision_authority",
            "diagnostic_win_rate",
            "equal_weight_avg_profit_pct",
            "forbidden_uses",
            "join_rate",
            "joined_sample",
            "recommended_resolution",
            "recommended_route",
            "runtime_effect",
            "sample",
            "source_field_coverage",
            "source_quality_adjusted_ev_pct",
            "source_quality_gate",
            "unknown_dimension_counts",
            "unknown_reason_counts",
        ),
        "dimension_keys": ("action", "held", "held_bucket", "holding_action", "holding_source_stage", "profit", "profit_band", "source"),
    },
    "exit_bucket_attribution": {
        "bucket_types": ("combo_exit_result", "exit_outcome", "exit_rule", "exit_source_stage", "profit_band"),
        "bucket_fields": (
            "ai_inference_proposal",
            "allowed_runtime_apply",
            "bucket_key",
            "bucket_type",
            "decision_authority",
            "diagnostic_win_rate",
            "equal_weight_avg_profit_pct",
            "forbidden_uses",
            "join_rate",
            "joined_sample",
            "recommended_resolution",
            "recommended_route",
            "runtime_effect",
            "sample",
            "source_field_coverage",
            "source_quality_adjusted_ev_pct",
            "source_quality_gate",
            "unknown_dimension_counts",
            "unknown_reason_counts",
        ),
        "dimension_keys": ("exit_outcome", "exit_rule", "exit_source_stage", "outcome", "profit", "profit_band", "rule", "source"),
    },
    "scale_in_bucket_attribution": {
        "bucket_types": ("ai_score_band", "ai_score_source", "arm", "blocker_namespace", "blocker_reason"),
        "bucket_fields": (
            "bucket_key",
            "bucket_type",
            "close_10m_pct",
            "decision_authority",
            "diagnostic_win_rate",
            "equal_weight_avg_profit_pct",
            "fixed_threshold_contract_role",
            "join_rate",
            "joined_sample",
            "mae_10m_pct",
            "mfe_10m_pct",
            "recommended_resolution",
            "recommended_route",
            "runtime_effect",
            "sample",
            "source_field_coverage",
            "source_quality_adjusted_ev_pct",
            "source_quality_gate",
            "unknown_dimension_counts",
            "unknown_reason_counts",
        ),
        "dimension_keys": ("ai_score_band", "ai_score_source", "arm", "blocker_namespace", "blocker_reason"),
    },
    "overnight_bucket_attribution": {
        "bucket_types": (
            "combo_overnight_decision",
            "confidence_band",
            "held_bucket",
            "overnight_action",
            "overnight_status",
            "peak_profit_band",
            "price_source",
            "profit_band",
            "source_quality_gate",
            "source_stage",
            "stage",
        ),
        "bucket_fields": (
            "bucket_key",
            "bucket_type",
            "decision_authority",
            "diagnostic_win_rate",
            "equal_weight_avg_profit_pct",
            "fixed_threshold_contract_role",
            "join_rate",
            "joined_sample",
            "next_day_close_pct",
            "next_day_mae_pct",
            "next_day_mfe_pct",
            "recommended_route",
            "runtime_effect",
            "sample",
            "source_quality_adjusted_ev_pct",
            "source_quality_gate",
        ),
        "dimension_keys": (
            "action",
            "confidence",
            "confidence_band",
            "held_bucket",
            "overnight_action",
            "overnight_status",
            "peak_profit_band",
            "price_source",
            "profit",
            "profit_band",
            "source_quality_gate",
            "source_stage",
            "stage",
            "status",
        ),
    },
}

def discovery_report_path(target_date: str) -> Path:
    return REPORT_DIR / f"lifecycle_bucket_discovery_{target_date}.json"


def discovery_markdown_path(target_date: str) -> Path:
    return REPORT_DIR / f"lifecycle_bucket_discovery_{target_date}.md"


def bucket_catalog_path(target_date: str) -> Path:
    return CATALOG_DIR / f"lifecycle_bucket_catalog_{target_date}.json"


def contamination_window_path(target_date: str) -> Path:
    return CONTAMINATION_WINDOW_DIR / f"lifecycle_bucket_quarantine_{target_date}.json"


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


AI_REVIEW_TIMEOUT_SEC = max(
    30,
    _safe_int(os.getenv("KORSTOCKSCAN_LIFECYCLE_BUCKET_DISCOVERY_AI_REVIEW_TIMEOUT_SEC"), 180),
)
AI_REVIEW_MAX_CANDIDATES = max(
    1,
    _safe_int(os.getenv("KORSTOCKSCAN_LIFECYCLE_BUCKET_DISCOVERY_AI_REVIEW_MAX_CANDIDATES"), 20),
)
AI_REVIEW_MAX_FIELD_CHARS = max(
    200,
    _safe_int(os.getenv("KORSTOCKSCAN_LIFECYCLE_BUCKET_DISCOVERY_AI_REVIEW_MAX_FIELD_CHARS"), 500),
)
AI_REVIEW_SHARD_CONTEXT_BUDGET_CHARS = max(
    8_000,
    _safe_int(os.getenv("KORSTOCKSCAN_LIFECYCLE_BUCKET_DISCOVERY_SHARD_CONTEXT_BUDGET_CHARS"), 30_000),
)
AI_REVIEW_SHARD_MAX_CANDIDATES = max(
    1,
    _safe_int(os.getenv("KORSTOCKSCAN_LIFECYCLE_BUCKET_DISCOVERY_SHARD_MAX_CANDIDATES"), 12),
)
AI_REVIEW_SHARD_ORDER = (
    "live_contract_review",
    "lifecycle_flow_review",
    "sim_policy_review",
    "gap_workorder_review",
    "taxonomy_discovery_review",
)
AI_REVIEW_SHARD_PRIORITIES = {
    shard_id: index for index, shard_id in enumerate(AI_REVIEW_SHARD_ORDER)
}
AI_REVIEW_SHARD_AUTHORITIES = {
    "live_contract_review": "explicit_contract_safety_gap_review_for_deterministic_live_candidates",
    "lifecycle_flow_review": "parent_lifecycle_flow_bucket_taxonomy_and_contract_review_only",
    "sim_policy_review": "sim_policy_handoff_source_quality_review_only",
    "gap_workorder_review": "source_contract_and_workorder_gap_review_only",
    "taxonomy_discovery_review": "new_bucket_taxonomy_review_only",
}
AI_REVIEW_REASONING_EFFORT = str(
    os.getenv("KORSTOCKSCAN_LIFECYCLE_BUCKET_DISCOVERY_AI_REVIEW_REASONING_EFFORT", "low")
).strip().lower() or "low"


def _ai_review_config_for_shard(shard_id: str | None) -> PostcloseAIReviewConfig:
    shard = str(shard_id or "unknown")
    generic_model = os.getenv("KORSTOCKSCAN_LIFECYCLE_BUCKET_DISCOVERY_AI_MODEL")
    generic_reasoning = os.getenv("KORSTOCKSCAN_LIFECYCLE_BUCKET_DISCOVERY_AI_REASONING_EFFORT")
    generic_timeout_sec = _safe_int(
        os.getenv("KORSTOCKSCAN_LIFECYCLE_BUCKET_DISCOVERY_AI_TIMEOUT_SEC"),
        AI_REVIEW_TIMEOUT_SEC,
    )
    if shard == "live_contract_review":
        return resolve_postclose_ai_review_config(
            "LIFECYCLE_BUCKET_DISCOVERY",
            default_model=str(generic_model or AI_REVIEW_MODEL),
            default_reasoning_effort=str(generic_reasoning or AI_REVIEW_REASONING_EFFORT),
            default_timeout_sec=generic_timeout_sec,
            env_prefix="KORSTOCKSCAN_LIFECYCLE_BUCKET_DISCOVERY_LIVE_CONTRACT_AI",
        )
    return resolve_postclose_ai_review_config(
        "LIFECYCLE_BUCKET_DISCOVERY",
        default_model=str(generic_model or AI_REVIEW_SOURCE_ONLY_MODEL),
        default_reasoning_effort=str(generic_reasoning or AI_REVIEW_SOURCE_ONLY_REASONING_EFFORT),
        default_timeout_sec=generic_timeout_sec,
        env_prefix="KORSTOCKSCAN_LIFECYCLE_BUCKET_DISCOVERY_SOURCE_ONLY_AI",
    )


def _ai_review_compact_value(value: Any, *, max_chars: int = AI_REVIEW_MAX_FIELD_CHARS) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        text = str(value) if isinstance(value, str) else value
        if isinstance(text, str) and len(text) > max_chars:
            return f"{text[:max_chars]}...[truncated]"
        return text
    encoded = json.dumps(value, ensure_ascii=True, sort_keys=True, default=str)
    if len(encoded) <= max_chars:
        return value
    return {"truncated_json": f"{encoded[:max_chars]}...[truncated]", "original_chars": len(encoded)}


def _ai_review_compact_candidate(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "bucket_id": item.get("bucket_id"),
        "stage": item.get("stage"),
        "bucket_type": item.get("bucket_type"),
        "bucket_key": item.get("bucket_key"),
        "bucket_relation": item.get("bucket_relation"),
        "classification_state": item.get("classification_state"),
        "live_auto_apply_family": item.get("live_auto_apply_family"),
        "evidence_grade": item.get("evidence_grade"),
        "transition_target": item.get("transition_target"),
        "grade_reason": item.get("grade_reason"),
        "full_real_conversion_allowed": item.get("full_real_conversion_allowed"),
        "source_dimensions": _ai_review_compact_value(item.get("source_dimensions")),
        "canonical_bucket": item.get("canonical_bucket"),
        "legacy_raw_bucket_key": item.get("legacy_raw_bucket_key"),
        "bucket_alias_version": item.get("bucket_alias_version"),
        "dimension_set_version": item.get("dimension_set_version"),
        "bucket_absorption_reason": item.get("bucket_absorption_reason"),
        "normalized_dimensions": _ai_review_compact_value(item.get("normalized_dimensions")),
        "normalized_metrics": _ai_review_compact_value(item.get("normalized_metrics")),
        "deterministic_proposal": _ai_review_compact_value(item.get("deterministic_proposal")),
        "ai_inference_proposal": _ai_review_compact_value(item.get("ai_inference_proposal")),
        "current_ai_tier2_proposal": _ai_review_compact_value(item.get("ai_tier2_proposal")),
        "evidence_authority_contract": _ai_review_compact_value(item.get("evidence_authority_contract")),
        "primary_decision_metric": item.get("primary_decision_metric"),
        "sample": item.get("sample"),
        "joined_sample": item.get("joined_sample"),
        "join_rate": item.get("join_rate"),
        "source_quality_adjusted_ev_pct": item.get("source_quality_adjusted_ev_pct"),
        "recommended_route": item.get("recommended_route"),
        "recommended_action": item.get("recommended_action"),
        "source_quality_gate": item.get("source_quality_gate"),
        "forbidden_uses": item.get("forbidden_uses"),
    }


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
    if candidate_state == "entry_only_sim_auto_approved":
        return "entry_only_sim_policy"
    if candidate_state == LIFECYCLE_FLOW_SIM_PROBE_STATE:
        return "lifecycle_flow_sim_probe_policy"
    if candidate_state == "entry_only_source_candidate":
        return "entry_only_source_candidate"
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
    if candidate_state == "entry_only_sim_auto_approved":
        return "entry_only_sim_policy_no_greenfield_live"
    if candidate_state == LIFECYCLE_FLOW_SIM_PROBE_STATE:
        return "next_preopen_lifecycle_flow_sim_probe_policy_input"
    if candidate_state == "entry_only_source_candidate":
        return "entry_only_keep_collecting_no_greenfield_live"
    if str(bucket.get("source_quality_gate") or "") != "pass":
        return "keep_collecting_until_sample_floor"
    return "keep_collecting"


def _decision_authority_for_state(state: str) -> str:
    if state == "live_auto_apply_ready":
        return "lifecycle_bucket_discovery_live_auto_apply"
    if state == "entry_only_sim_auto_approved":
        return "lifecycle_bucket_discovery_entry_only_sim_auto"
    if state == "entry_only_source_candidate":
        return "lifecycle_bucket_discovery_entry_only_source_quality"
    if state == LIFECYCLE_FLOW_SIM_PROBE_STATE:
        return "lifecycle_bucket_discovery_lifecycle_flow_sim_probe"
    if state == "sim_auto_approved":
        return "lifecycle_bucket_discovery_sim_auto"
    return "lifecycle_bucket_discovery_source_quality"


def _runtime_effect_after_approval_for_state(state: str) -> str:
    if state == "live_auto_apply_ready":
        return "live_auto_apply_without_human_approval"
    if state == "entry_only_sim_auto_approved":
        return "entry_only_sim_bucket_policy"
    if state == LIFECYCLE_FLOW_SIM_PROBE_STATE:
        return "lifecycle_flow_sim_probe_policy"
    if state == "entry_only_source_candidate":
        return "none_entry_only_source_candidate"
    if state == "sim_auto_approved":
        return "sim_only_bucket_policy"
    return "none"


def _auto_promotion_contract_state_for_state(state: str) -> str:
    if state == "live_auto_apply_ready":
        return "bounded_live_auto_apply_ready"
    if state == "entry_only_sim_auto_approved":
        return "entry_only_sim_auto_approved"
    if state == "entry_only_source_candidate":
        return "entry_only_source_candidate"
    if state == LIFECYCLE_FLOW_SIM_PROBE_STATE:
        return "lifecycle_flow_sim_probe_candidate"
    if state == "sim_auto_approved":
        return "sim_auto_approved"
    return "source_only"


def _normalize_candidate_runtime_metadata(item: dict[str, Any]) -> None:
    state = str(item.get("classification_state") or "")
    item["source_bucket_kind"] = _source_bucket_kind(state, item)
    item["decision_authority"] = _decision_authority_for_state(state)
    item["runtime_effect_after_approval"] = _runtime_effect_after_approval_for_state(state)
    item["broker_order_forbidden"] = state != "live_auto_apply_ready"
    item["allowed_runtime_apply"] = state == "live_auto_apply_ready"
    item["runtime_effect"] = state == "live_auto_apply_ready"
    item["sim_lifecycle_handoff_allowed"] = state in SIM_APPROVAL_STATES
    item["bounded_live_canary_allowed"] = state == "live_auto_apply_ready"
    if state != "live_auto_apply_ready":
        item["live_auto_apply_family"] = None
    contract = item.get("auto_promotion_contract") if isinstance(item.get("auto_promotion_contract"), dict) else {}
    item["auto_promotion_contract"] = {
        **contract,
        "state": _auto_promotion_contract_state_for_state(state),
        "tier2_required": state == "live_auto_apply_ready",
        "deterministic_contract_required": state == "live_auto_apply_ready",
        "deterministic_contract_components": [
            "source_quality_pass",
            "sample_floor",
            "primary_ev_uplift",
            "env_mapping",
            "runtime_hook",
            "post_apply_attribution",
        ]
        if state == "live_auto_apply_ready"
        else [],
    }


def _source_contract_snapshot(ldm: dict[str, Any]) -> dict[str, Any]:
    source_map = ldm.get("sources") if isinstance(ldm.get("sources"), dict) else {}
    sections: dict[str, Any] = {}
    for section_name in SOURCE_CONTRACT_SECTION_SCHEMAS:
        section = ldm.get(section_name) if isinstance(ldm.get(section_name), dict) else {}
        buckets = section.get("buckets") if isinstance(section.get("buckets"), list) else []
        declared = SOURCE_CONTRACT_SECTION_SCHEMAS[section_name]
        field_names: set[str] = set(str(item) for item in declared.get("bucket_fields", ()))
        bucket_types: set[str] = set(str(item) for item in declared.get("bucket_types", ()))
        dimension_keys: set[str] = set(str(item) for item in declared.get("dimension_keys", ()))
        observed_field_names: set[str] = set()
        observed_bucket_types: set[str] = set()
        observed_dimension_keys: set[str] = set()
        for item in buckets:
            if not isinstance(item, dict):
                continue
            item_fields = {str(key) for key in item}
            item_type = str(item.get("bucket_type") or "")
            item_dimensions = set(_source_dimensions(item_type, str(item.get("bucket_key") or "")).keys())
            observed_field_names.update(item_fields)
            observed_bucket_types.add(item_type)
            observed_dimension_keys.update(item_dimensions)
            field_names.update(item_fields)
            bucket_types.add(item_type)
            dimension_keys.update(item_dimensions)
        sections[section_name] = {
            "present": bool(section),
            "bucket_count": len([item for item in buckets if isinstance(item, dict)]),
            "declared_contract": True,
            "declared_bucket_types": sorted(declared.get("bucket_types", ())),
            "declared_bucket_fields": sorted(declared.get("bucket_fields", ())),
            "declared_dimension_keys": sorted(declared.get("dimension_keys", ())),
            "bucket_types": sorted(value for value in bucket_types if value),
            "observed_bucket_types": sorted(value for value in observed_bucket_types if value),
            "bucket_fields": sorted(field_names),
            "observed_bucket_fields": sorted(observed_field_names),
            "dimension_keys": sorted(dimension_keys),
            "observed_dimension_keys": sorted(observed_dimension_keys),
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
        "schema_version": SOURCE_CONTRACT_SCHEMA_VERSION,
        "compare_policy": "declared_schema_plus_observed_samples",
        "source_keys": sorted(str(key) for key, value in source_map.items() if value),
        "sections": sections,
        "policy_entry_count": len([item for item in policy_entries if isinstance(item, dict)]),
        "policy_fields": policy_fields,
    }


def _normalize_source_contract_for_compare(contract: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(contract, dict) or not contract:
        return {}
    normalized = json.loads(json.dumps(contract, ensure_ascii=False, default=str))
    normalized["schema_version"] = SOURCE_CONTRACT_SCHEMA_VERSION
    normalized["compare_policy"] = "declared_schema_plus_observed_samples"
    sections = normalized.get("sections") if isinstance(normalized.get("sections"), dict) else {}
    normalized["sections"] = sections
    for section_name, declared in SOURCE_CONTRACT_SECTION_SCHEMAS.items():
        section = sections.get(section_name) if isinstance(sections.get(section_name), dict) else {}
        current_fields = set(str(item) for item in (section.get("bucket_fields") or []))
        current_types = set(str(item) for item in (section.get("bucket_types") or []))
        current_dimensions = set(str(item) for item in (section.get("dimension_keys") or []))
        section.update(
            {
                "present": bool(section.get("present", True)),
                "declared_contract": True,
                "declared_bucket_types": sorted(declared.get("bucket_types", ())),
                "declared_bucket_fields": sorted(declared.get("bucket_fields", ())),
                "declared_dimension_keys": sorted(declared.get("dimension_keys", ())),
                "bucket_types": sorted(current_types | set(declared.get("bucket_types", ()))),
                "bucket_fields": sorted(current_fields | set(declared.get("bucket_fields", ()))),
                "dimension_keys": sorted(current_dimensions | set(declared.get("dimension_keys", ()))),
            }
        )
        section.setdefault("bucket_count", 0)
        section.setdefault("observed_bucket_types", [])
        section.setdefault("observed_bucket_fields", [])
        section.setdefault("observed_dimension_keys", [])
        sections[section_name] = section
    return normalized


def _compare_source_contracts(current: dict[str, Any], previous: dict[str, Any]) -> list[dict[str, Any]]:
    if not previous:
        return []
    current = _normalize_source_contract_for_compare(current)
    previous = _normalize_source_contract_for_compare(previous)
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


def _recommended_action(route: str, *, stage: str = "", bucket_type: str = "", ev: float | None = None) -> str:
    if (
        stage == "scale_in"
        and bucket_type == "blocker_reason"
        and route == "candidate_recovery_or_relax"
        and ev is not None
        and ev > 0
    ):
        return "keep_or_tighten_blocker_candidate"
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
    if stage == "lifecycle_flow" and bucket_type == "combo_lifecycle_flow":
        return GREENFIELD_REAL_ENV_FAMILY
    if stage == "scale_in" and bucket_type in {"arm", "blocker_namespace"} and bucket_key in {"PYRAMID", "AVG_DOWN_ONLY"}:
        return SCALE_IN_LIVE_AUTO_FAMILY
    return None


def _is_counterfactual_bucket(bucket_type: str, bucket_key: str, dimensions: dict[str, str]) -> bool:
    haystack = " ".join([bucket_type, bucket_key, *dimensions.values()]).lower()
    return any(token in haystack for token in COUNTERFACTUAL_SOURCE_TOKENS)


def _evidence_grade_for_bucket(stage: str, bucket: dict[str, Any]) -> dict[str, Any]:
    bucket_type = str(bucket.get("bucket_type") or "")
    bucket_key = str(bucket.get("bucket_key") or "")
    dimensions = _source_dimensions(bucket_type, bucket_key)
    joined_sample = _safe_int(bucket.get("joined_sample"))
    sample = _safe_int(bucket.get("sample"), joined_sample)
    join_rate = _safe_float(bucket.get("join_rate"), None)
    quality = str(bucket.get("source_quality_gate") or "")

    if _is_counterfactual_bucket(bucket_type, bucket_key, dimensions):
        return {
            "evidence_grade": EVIDENCE_GRADE_2_COUNTERFACTUAL,
            "transition_target": "sim_lifecycle_handoff",
            "grade_reason": "counterfactual_or_missed_entry_source_not_completed_lifecycle_outcome",
            "source_stage_split_required": False,
        }
    if bucket_type in MIXED_BUCKET_TYPES or (
        stage == "entry"
        and bucket_type.startswith("combo_")
        and not dimensions.get("source")
    ):
        return {
            "evidence_grade": EVIDENCE_GRADE_MIXED_SOURCE,
            "transition_target": "sim_lifecycle_handoff" if (join_rate or 0.0) >= 0.2 else "source_only_keep_collecting",
            "grade_reason": "source_mix_requires_child_source_stage_split_before_live",
            "source_stage_split_required": True,
        }
    if quality == "pass" and joined_sample > 0 and sample >= joined_sample:
        return {
            "evidence_grade": EVIDENCE_GRADE_1_COMPLETED_SIM,
            "transition_target": "bounded_live_canary_candidate",
            "grade_reason": "completed_or_joined_lifecycle_outcome_available",
            "source_stage_split_required": False,
        }
    return {
        "evidence_grade": EVIDENCE_GRADE_SOURCE_ONLY,
        "transition_target": "source_only_keep_collecting",
        "grade_reason": "completed_lifecycle_or_source_quality_evidence_insufficient",
        "source_stage_split_required": False,
    }


def _sim_handoff_allowed(bucket: dict[str, Any], grade: dict[str, Any]) -> bool:
    quality = str(bucket.get("source_quality_gate") or "")
    if quality != "pass":
        return False
    evidence_grade = str(grade.get("evidence_grade") or "")
    sample = _safe_int(bucket.get("sample"), _safe_int(bucket.get("joined_sample")))
    joined_sample = _safe_int(bucket.get("joined_sample"))
    ev = _safe_float(bucket.get("source_quality_adjusted_ev_pct"), None)
    if evidence_grade == EVIDENCE_GRADE_2_COUNTERFACTUAL:
        return sample >= 10 and ev is not None and ev > 1.0
    if evidence_grade == EVIDENCE_GRADE_MIXED_SOURCE:
        join_rate = _safe_float(bucket.get("join_rate"), None) or 0.0
        return joined_sample > 0 and join_rate >= 0.2
    return False


def _classify_bucket(stage: str, bucket: dict[str, Any]) -> tuple[str, str | None, dict[str, Any]]:
    bucket_type = str(bucket.get("bucket_type") or "")
    bucket_key = str(bucket.get("bucket_key") or "")
    route = str(bucket.get("recommended_route") or "")
    quality = str(bucket.get("source_quality_gate") or "")
    grade = _evidence_grade_for_bucket(stage, bucket)
    if quality != "pass":
        return "source_only_keep_collecting", None, grade
    live_family = _live_family_for(stage, bucket_type, bucket_key)
    ev = _safe_float(bucket.get("source_quality_adjusted_ev_pct"), None)
    if stage in {"holding", "exit"}:
        return "source_only_keep_collecting", None, {
            **grade,
            "transition_target": "child_evidence_for_lifecycle_flow_only",
            "grade_reason": "stage_only_holding_exit_bucket_cannot_promote_without_parent_lifecycle_flow",
        }
    if stage == "lifecycle_flow" and bucket_type == "combo_lifecycle_flow":
        if (
            route == "candidate_recovery_or_relax"
            and str(grade.get("evidence_grade") or "") == EVIDENCE_GRADE_1_COMPLETED_SIM
            and primary_ev_uplift_passes(ev, positive_edge=True)
        ):
            return "live_auto_apply_ready", live_family, grade
        if (
            str(grade.get("evidence_grade") or "") == EVIDENCE_GRADE_1_COMPLETED_SIM
            and _safe_int(bucket.get("complete_flow_count")) > 0
            and _safe_int(bucket.get("incomplete_flow_count")) == 0
            and ev is not None
            and ev > 0
        ):
            return LIFECYCLE_FLOW_SIM_PROBE_STATE, None, {
                **grade,
                "transition_target": "lifecycle_flow_sim_probe_handoff",
                "grade_reason": "complete_positive_lifecycle_flow_sim_probe_without_live_auto_contract",
            }
        if _sim_handoff_allowed(bucket, grade):
            return "sim_auto_approved", None, grade
        return "source_only_keep_collecting", None, grade
    if (
        stage == "entry"
        and bucket_type == "combo_entry_spot"
        and bucket_key == ENTRY_LIVE_AUTO_BUCKET_KEY
    ):
        if _sim_handoff_allowed(bucket, grade):
            return "entry_only_sim_auto_approved", None, grade
        return "entry_only_source_candidate", None, grade
    if str(grade.get("evidence_grade") or "") in {EVIDENCE_GRADE_2_COUNTERFACTUAL, EVIDENCE_GRADE_MIXED_SOURCE}:
        if route in {"candidate_recovery_or_relax", "candidate_tighten_or_exclude"} and _sim_handoff_allowed(bucket, grade):
            return "sim_auto_approved", None, grade
        return "source_only_keep_collecting", None, grade
    if (
        live_family
        and stage == "scale_in"
        and route == "candidate_tighten_or_exclude"
        and primary_ev_uplift_passes(ev, positive_edge=False)
    ):
        return "live_auto_apply_ready", live_family, grade
    if "unknown" in bucket_key:
        return (
            "entry_only_source_candidate" if stage == "entry" else "source_only_keep_collecting"
        ), None, grade
    if route in {"candidate_recovery_or_relax", "candidate_tighten_or_exclude"}:
        if stage == "entry":
            return "entry_only_sim_auto_approved", None, grade
        return "sim_auto_approved", None, grade
    return "source_only_keep_collecting", None, grade


def _candidate_from_bucket(stage: str, bucket: dict[str, Any]) -> dict[str, Any]:
    bucket_type = str(bucket.get("bucket_type") or "bucket")
    bucket_key = str(bucket.get("bucket_key") or "unknown")
    state, live_family, grade = _classify_bucket(stage, bucket)
    relation = _relation_for(bucket_type, bucket_key)
    bucket_id = f"{stage}:{bucket_type}:{_slug(bucket_key)}"
    source_bucket_id = _stable_source_bucket_id(stage, bucket_type, bucket_key)
    joined_sample = _safe_int(bucket.get("joined_sample"))
    sample = _safe_int(bucket.get("sample"), joined_sample)
    source_dimensions = _source_dimensions(bucket_type, bucket_key)
    taxonomy = normalize_lifecycle_bucket(
        stage=stage,
        bucket_type=bucket_type,
        bucket_key=bucket_key,
        source_dimensions=source_dimensions,
    )
    deterministic_proposal = taxonomy["deterministic_proposal"]
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
        "evidence_grade": grade.get("evidence_grade"),
        "transition_target": "bounded_live_canary"
        if state == "live_auto_apply_ready"
        else grade.get("transition_target"),
        "grade_reason": grade.get("grade_reason"),
        "full_real_conversion_allowed": False,
        "sim_lifecycle_handoff_allowed": state in SIM_APPROVAL_STATES,
        "bounded_live_canary_allowed": state == "live_auto_apply_ready",
        "source_stage_split_required": bool(grade.get("source_stage_split_required")),
        "archived_live_exception_reason": None,
        "legacy_contract_known_unknown": (
            state == "live_auto_apply_ready"
            and stage == "entry"
            and bucket_type == "combo_entry_spot"
            and bucket_key == ENTRY_LIVE_AUTO_BUCKET_KEY
            and "unknown" in bucket_key
        ),
        "source_dimension_gap": (
            "legacy_contract_known_unknown"
            if (
                state == "live_auto_apply_ready"
                and stage == "entry"
                and bucket_type == "combo_entry_spot"
                and bucket_key == ENTRY_LIVE_AUTO_BUCKET_KEY
                and "unknown" in bucket_key
            )
            else "unknown_source_dimensions"
            if "unknown" in bucket_key
            else ""
        ),
        "source_dimensions": source_dimensions,
        "lifecycle_flow_bucket_id": bucket.get("lifecycle_flow_bucket_id"),
        "metric_scope": bucket.get("metric_scope"),
        "entry_bucket_id": bucket.get("entry_bucket_id"),
        "submit_bucket_id": bucket.get("submit_bucket_id"),
        "holding_bucket_id": bucket.get("holding_bucket_id"),
        "scale_in_bucket_id": bucket.get("scale_in_bucket_id"),
        "scale_in_bucket_ids": bucket.get("scale_in_bucket_ids") or [],
        "exit_bucket_id": bucket.get("exit_bucket_id"),
        "child_bucket_ids": bucket.get("child_bucket_ids") or {},
        "complete_flow_count": _safe_int(bucket.get("complete_flow_count")),
        "incomplete_flow_count": _safe_int(bucket.get("incomplete_flow_count")),
        "stage_contract": bucket.get("stage_contract") or {},
        "attribution_key": bucket.get("attribution_key"),
        "rollback_guard": bucket.get("rollback_guard"),
        "canonical_bucket": taxonomy["canonical_bucket"],
        "legacy_raw_bucket_key": taxonomy["legacy_raw_bucket_key"],
        "bucket_alias_version": taxonomy["bucket_alias_version"],
        "dimension_set_version": taxonomy["dimension_set_version"],
        "bucket_absorption_reason": taxonomy["bucket_absorption_reason"],
        "taxonomy_candidate_type": taxonomy["taxonomy_candidate_type"],
        "normalized_dimensions": taxonomy["normalized_dimensions"],
        "normalized_metrics": taxonomy["normalized_metrics"],
        "missing_dimension_keys": taxonomy["missing_dimension_keys"],
        "deterministic_proposal": deterministic_proposal,
        "ai_inference_proposal": bucket.get("ai_inference_proposal") or {},
        "ai_tier2_proposal": default_ai_tier2_proposal(bucket_id, deterministic_proposal),
        "ai_tier2_comparative_review": compare_taxonomy_proposals(
            bucket_id=bucket_id,
            deterministic_proposal=deterministic_proposal,
            ai_tier2_proposal=None,
        ),
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
        "recommended_action": _recommended_action(
            str(bucket.get("recommended_route") or ""),
            stage=stage,
            bucket_type=bucket_type,
            ev=_safe_float(bucket.get("source_quality_adjusted_ev_pct"), None),
        ),
        "recommended_resolution": _recommended_resolution(state, bucket),
        "unknown_dimension_counts": bucket.get("unknown_dimension_counts") or {},
        "unknown_reason_counts": bucket.get("unknown_reason_counts") or {},
        "source_field_coverage": bucket.get("source_field_coverage") or {},
        "actual_order_submitted": False,
        "broker_order_forbidden": state != "live_auto_apply_ready",
        "allowed_runtime_apply": state == "live_auto_apply_ready",
        "decision_authority": _decision_authority_for_state(state),
        "runtime_effect": state == "live_auto_apply_ready",
        "runtime_effect_after_approval": _runtime_effect_after_approval_for_state(state),
        "auto_promotion_contract": {
            "state": _auto_promotion_contract_state_for_state(state),
            "tier2_required": state == "live_auto_apply_ready",
            "tier2_policy": "fail_closed",
            "primary_ev_uplift_threshold_pct": 1.0,
            "deterministic_contract_required": state == "live_auto_apply_ready",
            "deterministic_contract_components": [
                "source_quality_pass",
                "sample_floor",
                "primary_ev_uplift",
                "env_mapping",
                "runtime_hook",
                "post_apply_attribution",
            ]
            if state == "live_auto_apply_ready"
            else [],
            "final_user_approval_boundary": "full_live_only",
        },
        "forbidden_uses": list(BASE_FORBIDDEN_USES),
        "evidence_authority_contract": evidence_authority_contract(),
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
        source_dimensions = {"change_type": change_type, "subject": subject}
        taxonomy = normalize_lifecycle_bucket(
            stage="source_contract",
            bucket_type=change_type,
            bucket_key=subject,
            source_dimensions=source_dimensions,
        )
        deterministic_proposal = taxonomy["deterministic_proposal"]
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
                "evidence_grade": EVIDENCE_GRADE_SOURCE_ONLY,
                "transition_target": "code_improvement_workorder"
                if state == "code_patch_required"
                else "source_only_keep_collecting",
                "grade_reason": "source_contract_drift_not_strategy_outcome_evidence",
                "full_real_conversion_allowed": False,
                "sim_lifecycle_handoff_allowed": False,
                "bounded_live_canary_allowed": False,
                "source_stage_split_required": False,
                "source_dimensions": source_dimensions,
                "canonical_bucket": taxonomy["canonical_bucket"],
                "legacy_raw_bucket_key": taxonomy["legacy_raw_bucket_key"],
                "bucket_alias_version": taxonomy["bucket_alias_version"],
                "dimension_set_version": taxonomy["dimension_set_version"],
                "bucket_absorption_reason": taxonomy["bucket_absorption_reason"],
                "taxonomy_candidate_type": taxonomy["taxonomy_candidate_type"],
                "normalized_dimensions": taxonomy["normalized_dimensions"],
                "normalized_metrics": taxonomy["normalized_metrics"],
                "missing_dimension_keys": taxonomy["missing_dimension_keys"],
                "deterministic_proposal": deterministic_proposal,
                "ai_tier2_proposal": default_ai_tier2_proposal(bucket_id, deterministic_proposal),
                "ai_tier2_comparative_review": compare_taxonomy_proposals(
                    bucket_id=bucket_id,
                    deterministic_proposal=deterministic_proposal,
                    ai_tier2_proposal=None,
                ),
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
                "allowed_runtime_apply": False,
                "decision_authority": "source_contract_drift_detection",
                "runtime_effect": False,
                "runtime_effect_after_approval": "none_source_contract_patch_required",
                "source_contract_change": change,
                "forbidden_uses": list(BASE_FORBIDDEN_USES),
                "evidence_authority_contract": evidence_authority_contract(),
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
        source_dimensions = {"policy_key": policy_key}
        taxonomy = normalize_lifecycle_bucket(
            stage=stage,
            bucket_type="stage_policy",
            bucket_key=policy_key,
            source_dimensions=source_dimensions,
        )
        deterministic_proposal = taxonomy["deterministic_proposal"]
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
                "evidence_grade": EVIDENCE_GRADE_1_COMPLETED_SIM
                if state == "sim_auto_approved"
                else EVIDENCE_GRADE_SOURCE_ONLY,
                "transition_target": "sim_lifecycle_handoff"
                if state == "sim_auto_approved"
                else "source_only_keep_collecting",
                "grade_reason": "stage_policy_source_quality_pass_without_live_bridge",
                "full_real_conversion_allowed": False,
                "sim_lifecycle_handoff_allowed": state == "sim_auto_approved",
                "bounded_live_canary_allowed": False,
                "source_stage_split_required": False,
                "source_dimensions": source_dimensions,
                "canonical_bucket": taxonomy["canonical_bucket"],
                "legacy_raw_bucket_key": taxonomy["legacy_raw_bucket_key"],
                "bucket_alias_version": taxonomy["bucket_alias_version"],
                "dimension_set_version": taxonomy["dimension_set_version"],
                "bucket_absorption_reason": taxonomy["bucket_absorption_reason"],
                "taxonomy_candidate_type": taxonomy["taxonomy_candidate_type"],
                "normalized_dimensions": taxonomy["normalized_dimensions"],
                "normalized_metrics": taxonomy["normalized_metrics"],
                "missing_dimension_keys": taxonomy["missing_dimension_keys"],
                "deterministic_proposal": deterministic_proposal,
                "ai_tier2_proposal": default_ai_tier2_proposal(bucket_id, deterministic_proposal),
                "ai_tier2_comparative_review": compare_taxonomy_proposals(
                    bucket_id=bucket_id,
                    deterministic_proposal=deterministic_proposal,
                    ai_tier2_proposal=None,
                ),
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
                "allowed_runtime_apply": False,
                "decision_authority": "lifecycle_bucket_discovery_stage_policy_sim_auto",
                "runtime_effect": False,
                "runtime_effect_after_approval": "sim_only_stage_policy",
                "forbidden_uses": list(BASE_FORBIDDEN_USES),
                "evidence_authority_contract": evidence_authority_contract(),
            }
        )
    return candidates


def _build_ai_review_context(
    report: dict[str, Any],
    *,
    shard_id: str = "legacy_bounded_review",
    candidate_items: list[dict[str, Any]] | None = None,
    omitted_candidate_count: int = 0,
    candidate_selection_policy: str = "first_bounded_surfaced_candidates",
    review_authority: str = "contract_gap_review_only",
) -> dict[str, Any]:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    surfaced = report.get("surfaced_candidates") if isinstance(report.get("surfaced_candidates"), list) else []
    selected_items = candidate_items if candidate_items is not None else surfaced[:AI_REVIEW_MAX_CANDIDATES]
    compact_candidates: list[dict[str, Any]] = []
    for item in selected_items:
        if not isinstance(item, dict):
            continue
        compact_candidates.append(_ai_review_compact_candidate(item))
    return {
        "review_task": "two_pass_lifecycle_bucket_discovery_review",
        "pass_1": "Interpret whether each surfaced bucket is a refinement of an existing taxonomy bucket or a genuinely new bucket candidate.",
        "parallel_proposer_task": (
            "For each surfaced candidate, independently propose whether to merge, absorb_as_dimension, "
            "create_new_metric, create_new_dimension, keep_bucket, reject, source_quality_blocker, or instrumentation_gap."
        ),
        "pass_2": (
            "Compare deterministic_proposal and your ai_tier2_proposal side by side. Produce comparative_reviews and "
            "final_conclusions. Do not block deterministic live candidates just because the edge is small, new, or ambiguous."
        ),
        "authority": "review_only_no_broker_order_no_provider_route_no_bot_restart_no_cap_release",
        "review_policy": {
            "language": "English only. Keep explanations concise to reduce tokens.",
            "no_promotion_authority": "You cannot promote a non-live deterministic candidate to live_auto_apply_ready.",
            "grade_policy": (
                "Grade 2 counterfactual and mixed_source candidates cannot become bounded live candidates by AI promotion. "
                "A deterministic entry bridge candidate that is already live_auto_apply_ready is an explicit contract exception "
                "and must stay live unless an explicit contract or safety gap is found."
            ),
            "non_conservative_live_policy": (
                "For Grade 1 completed-sim deterministic live_auto_apply_ready candidates, do not block solely for small effect size, "
                "low confidence, novelty, or ambiguity. Keep live and rely on post-apply verification."
            ),
            "block_only_for_explicit_gaps": (
                "Block or downgrade a deterministic live candidate only for explicit source-quality, schema, env mapping, runtime hook, "
                "post-apply attribution, safety, broker, stale quote, qty/cooldown, provider, cap, forbidden-use, leakage, or missing-contract gaps."
            ),
            "evidence_authority_contract": (
                "Bucket/dimension tuning primary evidence is sim/probe lifecycle EV. Real one-share samples are not "
                "primary EV evidence unless the mapped bucket policy was already enabled for the evaluated post-apply "
                "cohort. Pre-apply real samples may be used only for execution-quality calibration, safety veto, "
                "provenance validation, and broker/fill/slippage source-quality checks. Do not merge real PnL with "
                "sim/probe EV and do not promote runtime threshold/order/provider/cap/bot changes from pre-apply "
                "real one-share outcomes."
            ),
        },
        "review_scope": {
            "shard_id": shard_id,
            "candidate_selection_policy": candidate_selection_policy,
            "review_authority": review_authority,
            "candidate_ids": [
                str(item.get("bucket_id"))
                for item in compact_candidates
                if isinstance(item, dict) and item.get("bucket_id")
            ],
            "reviewed_candidate_count": len(compact_candidates),
            "omitted_candidate_count": max(0, int(omitted_candidate_count or 0)),
            "context_char_budget": AI_REVIEW_SHARD_CONTEXT_BUDGET_CHARS,
        },
        "date": report.get("date"),
        "summary": summary,
        "source_contract": report.get("source_contract"),
        "source_contract_changes": report.get("source_contract_changes") or [],
        "surfaced_candidates": compact_candidates,
        "allowed_final_states": sorted(FINAL_CLASSIFICATION_STATES),
        "allowed_relations": sorted(FINAL_RELATIONS),
        "allowed_taxonomy_decisions": sorted(AI_TAXONOMY_DECISIONS),
        "required_metric_contract_fields": [
            "metric_role",
            "decision_authority",
            "window_policy",
            "sample_floor",
            "primary_decision_metric",
            "source_quality_gate",
            "forbidden_uses",
        ],
        "evidence_authority_contract": evidence_authority_contract(),
        "safety_rule": (
            "AI may block or downgrade a deterministic live bucket only for explicit contract/source-quality/safety gaps, "
            "and may not create live_auto_apply_ready unless the input candidate is already live_auto_apply_ready "
            "and has a live_auto_apply_family."
        ),
    }


def _candidate_review_priority(item: dict[str, Any]) -> tuple[int, int, float]:
    state = str(item.get("classification_state") or "")
    state_priority = {
        "live_auto_apply_ready": 0,
        "runtime_blocked_contract_gap": 1,
        LIFECYCLE_FLOW_SIM_PROBE_STATE: 2,
        "sim_auto_approved": 2,
        "code_patch_required": 3,
        "automation_handoff_gap": 4,
        "new_bucket_candidate": 5,
    }.get(state, 9)
    sample = _safe_int(item.get("joined_sample"), _safe_int(item.get("sample"), 0))
    ev = _safe_float(item.get("source_quality_adjusted_ev_pct"), 0.0) or 0.0
    return (state_priority, -sample, -abs(ev))


def _candidate_matches_ai_shard(item: dict[str, Any], shard_id: str) -> bool:
    state = str(item.get("classification_state") or "")
    stage = str(item.get("stage") or "")
    source_kind = str(item.get("source_bucket_kind") or "")
    if shard_id == "live_contract_review":
        return state in {"live_auto_apply_ready", "runtime_blocked_contract_gap"}
    if shard_id == "lifecycle_flow_review":
        return stage == "lifecycle_flow" and state in {
            "live_auto_apply_ready",
            LIFECYCLE_FLOW_SIM_PROBE_STATE,
            "sim_auto_approved",
            "source_only_keep_collecting",
            "new_bucket_candidate",
            "runtime_blocked_contract_gap",
            "code_patch_required",
            "automation_handoff_gap",
        }
    if shard_id == "sim_policy_review":
        return state in {"sim_auto_approved", "entry_only_sim_auto_approved", LIFECYCLE_FLOW_SIM_PROBE_STATE}
    if shard_id == "gap_workorder_review":
        return state in {"code_patch_required", "automation_handoff_gap"} or stage == "source_contract" or source_kind in {
            "source_contract_gap",
            "source_quality_gap",
        }
    if shard_id == "taxonomy_discovery_review":
        return state == "new_bucket_candidate"
    return False


def _fit_candidates_to_ai_budget(
    report: dict[str, Any],
    *,
    shard_id: str,
    candidates: list[dict[str, Any]],
    candidate_selection_policy: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for item in candidates[:AI_REVIEW_SHARD_MAX_CANDIDATES]:
        selected.append(item)
        context = _build_ai_review_context(
            report,
            shard_id=shard_id,
            candidate_items=selected,
            omitted_candidate_count=max(0, len(candidates) - len(selected)),
            candidate_selection_policy=candidate_selection_policy,
            review_authority=AI_REVIEW_SHARD_AUTHORITIES.get(shard_id, "contract_gap_review_only"),
        )
        context_chars = len(json.dumps(context, ensure_ascii=True, default=str))
        if context_chars > AI_REVIEW_SHARD_CONTEXT_BUDGET_CHARS and len(selected) > 1:
            selected.pop()
            break
    context = _build_ai_review_context(
        report,
        shard_id=shard_id,
        candidate_items=selected,
        omitted_candidate_count=max(0, len(candidates) - len(selected)),
        candidate_selection_policy=candidate_selection_policy,
        review_authority=AI_REVIEW_SHARD_AUTHORITIES.get(shard_id, "contract_gap_review_only"),
    )
    return selected, context


def _build_ai_review_shards(report: dict[str, Any]) -> list[dict[str, Any]]:
    surfaced = [
        item
        for item in (report.get("surfaced_candidates") or [])
        if isinstance(item, dict) and item.get("bucket_id")
    ]
    assigned: set[str] = set()
    shards: list[dict[str, Any]] = []
    for shard_id in AI_REVIEW_SHARD_ORDER:
        candidates = [
            item
            for item in surfaced
            if str(item.get("bucket_id")) not in assigned and _candidate_matches_ai_shard(item, shard_id)
        ]
        candidates.sort(key=_candidate_review_priority)
        selected, context = _fit_candidates_to_ai_budget(
            report,
            shard_id=shard_id,
            candidates=candidates,
            candidate_selection_policy=f"{shard_id}_priority_then_sample_ev",
        )
        reviewed_ids = [str(item.get("bucket_id")) for item in selected if item.get("bucket_id")]
        assigned.update(reviewed_ids)
        context_chars = len(json.dumps(context, ensure_ascii=True, default=str))
        shards.append(
            {
                "shard_id": shard_id,
                "priority": AI_REVIEW_SHARD_PRIORITIES[shard_id],
                "candidate_selection_policy": f"{shard_id}_priority_then_sample_ev",
                "review_authority": AI_REVIEW_SHARD_AUTHORITIES[shard_id],
                "candidate_ids": reviewed_ids,
                "candidate_count": len(reviewed_ids),
                "omitted_candidate_count": max(0, len(candidates) - len(selected)),
                "context": context,
                "context_chars": context_chars,
            }
        )
    return shards


def _build_ai_review_instructions() -> str:
    return (
        "You are the AI Tier2 lifecycle bucket discovery reviewer.\n"
        "Use English only and keep wording concise to reduce tokens.\n"
        "Your job is a two-pass review with a parallel AI proposal: first interpret bucket taxonomy, independently "
        "propose AI Tier2 taxonomy candidates, then compare deterministic_proposal versus ai_tier2_proposal and audit that comparison.\n"
        "Return only strict JSON using lifecycle_bucket_discovery_review_v1.\n"
        "Do not approve broker orders, provider route changes, bot restarts, cap release, or intraday threshold mutation.\n"
        "Classify existing_bucket_refinement when a bucket is a child/refinement of a known stage taxonomy.\n"
        "Classify new_bucket_candidate when existing taxonomy cannot explain the source dimensions or source contract drift.\n"
        "Prefer absorb_as_dimension over new bucket creation when the case is numeric, price-quality, fill-quality, rebound, "
        "prior-soft-stop, or deferred-exit context that can be represented as a shared metric or dimension.\n"
        "Every new metric or dimension proposal must include metric_role, decision_authority, window_policy, sample_floor, "
        "primary_decision_metric, source_quality_gate, and forbidden_uses in required_source_fields or forbidden_uses.\n"
        "In comparative_reviews choose selected_source as deterministic, ai_tier2, hybrid, or reject and selected_decision as "
        "merge, absorb_as_dimension, create_new_metric, create_new_dimension, keep_bucket, reject, source_quality_blocker, or instrumentation_gap.\n"
        "Grade 2 counterfactual and mixed_source candidates cannot become bounded live candidates by AI promotion. "
        "However, if a deterministic entry bridge candidate is already live_auto_apply_ready, keep it live unless an explicit contract or safety gap is found.\n"
        "Do not be conservative by default for Grade 1 completed-sim deterministic live candidates. A Grade 1 deterministic live candidate with even a 1% plausible positive effect should not be blocked solely for small effect size, novelty, low confidence, or ambiguity.\n"
        "When the decision is ambiguous, keep Grade 1 deterministic live candidates live and rely on post-apply verification.\n"
        "Use runtime_blocked_contract_gap or code_patch_required only for explicit source-quality, source schema, env mapping, runtime hook, post-apply attribution, safety, broker, stale quote, qty/cooldown, provider, cap, forbidden-use, leakage, or missing-contract gaps.\n"
        "Evidence authority contract: bucket/dimension tuning primary evidence is sim/probe lifecycle EV. Real one-share samples are not primary EV evidence unless the mapped bucket policy was already enabled for the evaluated post-apply cohort. Pre-apply real samples may be used only for execution-quality calibration, safety veto, provenance validation, and broker/fill/slippage source-quality checks. Do not merge real PnL with sim/probe EV and do not promote runtime threshold/order/provider/cap/bot changes from pre-apply real one-share outcomes. If a proposal violates this contract, choose reject, source_quality_blocker, or instrumentation_gap.\n"
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
    raw_conclusions = payload.get("final_conclusions")
    raw_ai_proposals = payload.get("ai_tier2_proposals")
    raw_comparative_reviews = payload.get("comparative_reviews")
    conclusions = raw_conclusions if isinstance(raw_conclusions, list) else []
    ai_proposals = payload.get("ai_tier2_proposals") if isinstance(payload.get("ai_tier2_proposals"), list) else []
    comparative_reviews = payload.get("comparative_reviews") if isinstance(payload.get("comparative_reviews"), list) else []
    if not interpretation:
        warnings.append("ai_review_interpretation_missing")
    if not audit:
        warnings.append("ai_review_audit_missing")
    if not isinstance(raw_conclusions, list):
        warnings.append("ai_review_final_conclusions_invalid")
    if not isinstance(raw_ai_proposals, list):
        warnings.append("ai_review_ai_tier2_proposals_invalid")
    if not isinstance(raw_comparative_reviews, list):
        warnings.append("ai_review_comparative_reviews_invalid")
    for proposal in ai_proposals:
        if not isinstance(proposal, dict):
            warnings.append("ai_review_ai_tier2_proposal_non_dict")
            continue
        if str(proposal.get("proposal_decision") or "") not in AI_TAXONOMY_DECISIONS:
            warnings.append(f"ai_review_invalid_proposal_decision:{proposal.get('bucket_id')}")
        if str(proposal.get("proposal_decision") or "") in {"create_new_metric", "create_new_dimension"}:
            fields = {str(value) for value in (proposal.get("required_source_fields") or [])}
            if not REQUIRED_TAXONOMY_CONTRACT_FIELDS.issubset(fields):
                warnings.append(f"ai_review_metric_contract_missing:{proposal.get('bucket_id')}")
        if has_evidence_authority_violation(proposal):
            warnings.append(f"ai_review_evidence_authority_violation:{proposal.get('bucket_id')}")
    proposal_ids = {
        str(proposal.get("bucket_id"))
        for proposal in ai_proposals
        if isinstance(proposal, dict) and proposal.get("bucket_id")
    }
    comparative_ids = {
        str(review.get("bucket_id"))
        for review in comparative_reviews
        if isinstance(review, dict) and review.get("bucket_id")
    }
    for missing_id in sorted(proposal_ids - comparative_ids):
        warnings.append(f"ai_review_comparative_review_missing:{missing_id}")
    for review in comparative_reviews:
        if not isinstance(review, dict):
            warnings.append("ai_review_comparative_review_non_dict")
            continue
        if str(review.get("selected_decision") or "") not in AI_TAXONOMY_DECISIONS:
            warnings.append(f"ai_review_invalid_selected_decision:{review.get('bucket_id')}")
        if str(review.get("selected_source") or "") not in AI_TAXONOMY_SOURCES:
            warnings.append(f"ai_review_invalid_selected_source:{review.get('bucket_id')}")
        if str(review.get("selected_decision") or "") in {"create_new_metric", "create_new_dimension"}:
            fields = {str(value) for value in (review.get("required_source_fields") or [])}
            if not REQUIRED_TAXONOMY_CONTRACT_FIELDS.issubset(fields):
                warnings.append(f"ai_review_selected_metric_contract_missing:{review.get('bucket_id')}")
        if has_evidence_authority_violation(review):
            warnings.append(f"ai_review_selected_evidence_authority_violation:{review.get('bucket_id')}")
    for item in conclusions:
        if not isinstance(item, dict):
            warnings.append("ai_review_final_conclusion_non_dict")
            continue
        if str(item.get("final_bucket_relation") or "") not in FINAL_RELATIONS:
            warnings.append(f"ai_review_invalid_relation:{item.get('bucket_id')}")
        if str(item.get("final_classification_state") or "") not in FINAL_CLASSIFICATION_STATES:
            warnings.append(f"ai_review_invalid_state:{item.get('bucket_id')}")
        if has_evidence_authority_violation(item):
            warnings.append(f"ai_review_final_evidence_authority_violation:{item.get('bucket_id')}")
    if warnings:
        return "parse_rejected", payload, warnings
    return "parsed", payload, []


def _call_openai_ai_review(
    input_context: dict[str, Any],
    *,
    shard_id: str | None = None,
    config: PostcloseAIReviewConfig | None = None,
) -> tuple[Any | None, dict[str, Any]]:
    resolved_shard_id = shard_id or str((input_context.get("review_scope") or {}).get("shard_id") or "unknown")
    config = config or _ai_review_config_for_shard(resolved_shard_id)
    try:
        from openai import OpenAI, RateLimitError
        from src.engine.ai_response_contracts import build_openai_response_text_format
        from src.engine.daily_threshold_cycle_report import (
            _extract_openai_response_text,
            _load_threshold_ai_openai_keys,
        )
    except Exception as exc:
        return None, {"provider": "openai", "status": "unavailable", "reason": f"openai import failed: {exc}", "shard_id": resolved_shard_id, **config.provider_status_fields()}

    api_keys = _load_threshold_ai_openai_keys()
    if not api_keys:
        return None, {"provider": "openai", "status": "unavailable", "reason": "OPENAI_API_KEY not configured", "shard_id": resolved_shard_id, **config.provider_status_fields()}

    prompt = json.dumps(input_context, ensure_ascii=True, indent=2, default=str)
    errors: list[dict[str, str]] = []
    for attempt_index, (key_name, api_key) in enumerate(api_keys, start=1):
        try:
            client = OpenAI(api_key=api_key, timeout=config.timeout_sec)
            response = client.responses.create(
                model=config.model,
                instructions=_build_ai_review_instructions(),
                input=prompt,
                text={
                    "format": build_openai_response_text_format(AI_REVIEW_SCHEMA_NAME),
                    "verbosity": "low",
                },
                reasoning={"effort": config.reasoning_effort},
                store=False,
                metadata={
                    "endpoint_name": "lifecycle_bucket_discovery_review",
                    "schema_name": AI_REVIEW_SCHEMA_NAME,
                    "report_type": "lifecycle_bucket_discovery",
                    "shard_id": resolved_shard_id,
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
                "model": config.model,
                "schema_name": AI_REVIEW_SCHEMA_NAME,
                "shard_id": resolved_shard_id,
                "reasoning_effort": config.reasoning_effort,
                "timeout_sec": config.timeout_sec,
                "attempt_role": config.attempt_role,
                "retry_reason": config.retry_reason,
                "config_env_prefix": config.env_prefix_name,
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
        "shard_id": resolved_shard_id,
        **config.provider_status_fields(),
        "errors": errors[-3:],
    }


def _candidate_index(candidates: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        str(item.get("bucket_id")): item
        for item in candidates
        if isinstance(item, dict) and item.get("bucket_id")
    }


def _ai_proposal_by_candidate(ai_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    proposals = ai_payload.get("ai_tier2_proposals") if isinstance(ai_payload.get("ai_tier2_proposals"), list) else []
    result: dict[str, dict[str, Any]] = {}
    for proposal in proposals:
        if isinstance(proposal, dict) and proposal.get("bucket_id"):
            result[str(proposal["bucket_id"])] = {
                **proposal,
                "proposal_source": "ai_tier2",
                "proposal_status": "provided",
            }
    return result


def _comparative_review_by_candidate(ai_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    reviews = ai_payload.get("comparative_reviews") if isinstance(ai_payload.get("comparative_reviews"), list) else []
    result: dict[str, dict[str, Any]] = {}
    for review in reviews:
        if isinstance(review, dict) and review.get("bucket_id"):
            result[str(review["bucket_id"])] = review
    return result


def _apply_ai_review(
    candidates: list[dict[str, Any]],
    *,
    ai_status: str,
    ai_payload: dict[str, Any],
    warnings: list[str],
    reviewed_bucket_ids: set[str] | None = None,
    fail_closed_live: bool = True,
) -> list[dict[str, Any]]:
    updated = [dict(item) for item in candidates]
    by_id = _candidate_index(updated)
    target_ids = reviewed_bucket_ids
    if target_ids is None:
        target_ids = {str(item.get("bucket_id")) for item in updated if item.get("bucket_id")}
    if ai_status != "parsed":
        for item in updated:
            bucket_id = str(item.get("bucket_id") or "")
            if bucket_id not in target_ids:
                item.setdefault("ai_review_coverage", "unreviewed")
                continue
            deterministic = item.get("deterministic_proposal") if isinstance(item.get("deterministic_proposal"), dict) else {}
            item["ai_tier2_proposal"] = default_ai_tier2_proposal(str(item.get("bucket_id") or ""), deterministic)
            item["ai_tier2_comparative_review"] = compare_taxonomy_proposals(
                bucket_id=str(item.get("bucket_id") or ""),
                deterministic_proposal=deterministic,
                ai_tier2_proposal=item["ai_tier2_proposal"],
            )
            item["ai_review_coverage"] = "reviewed"
            item["ai_review_status"] = ai_status
            if fail_closed_live and item.get("classification_state") == "live_auto_apply_ready":
                item["classification_state"] = "runtime_blocked_contract_gap"
                item["runtime_effect"] = False
                item["broker_order_forbidden"] = True
                item["allowed_runtime_apply"] = False
                item["ai_tier2_blocked_reason"] = tier2_fail_closed_reason(ai_status)
                item["recommended_resolution"] = "retry_tier2_review_before_pre_final_auto_apply"
                contract = item.get("auto_promotion_contract") if isinstance(item.get("auto_promotion_contract"), dict) else {}
                item["auto_promotion_contract"] = {
                    **contract,
                    "state": "source_only",
                    "tier2_status": ai_status,
                    "tier2_fail_closed": True,
                }
        if any(item.get("ai_tier2_blocked_reason") for item in updated):
            warnings.append(f"ai_two_pass_review_{ai_status}_fail_closed_live_auto_blocked")
        return updated

    ai_proposals = _ai_proposal_by_candidate(ai_payload)
    comparative_reviews = _comparative_review_by_candidate(ai_payload)
    for item in updated:
        bucket_id = str(item.get("bucket_id") or "")
        if bucket_id not in target_ids:
            item.setdefault("ai_review_coverage", "unreviewed")
            continue
        deterministic = item.get("deterministic_proposal") if isinstance(item.get("deterministic_proposal"), dict) else {}
        ai_proposal = ai_proposals.get(bucket_id) or default_ai_tier2_proposal(bucket_id, deterministic)
        provided_comparative = comparative_reviews.get(bucket_id)
        comparative = compare_taxonomy_proposals(
            bucket_id=bucket_id,
            deterministic_proposal=deterministic,
            ai_tier2_proposal=ai_proposal,
            comparative_review=provided_comparative,
        )
        item["ai_tier2_proposal"] = ai_proposal
        item["ai_tier2_comparative_review"] = comparative
        item["ai_tier2_taxonomy_decision"] = comparative.get("selected_decision")
        item["ai_tier2_selected_source"] = comparative.get("selected_source")
        item["ai_tier2_confidence"] = comparative.get("confidence")
        item["ai_tier2_rejection_reason"] = comparative.get("rejected_alternative_reason")
        item["ai_review_coverage"] = "reviewed"
        item["ai_review_status"] = ai_status
        if provided_comparative and comparative.get("selected_decision") in {"source_quality_blocker", "instrumentation_gap"}:
            selected_decision = str(comparative.get("selected_decision") or "")
            item["recommended_resolution"] = selected_decision
            item["source_quality_gate"] = selected_decision
            if item.get("classification_state") == "live_auto_apply_ready":
                item["classification_state"] = "runtime_blocked_contract_gap"
                item["runtime_effect"] = False
                item["broker_order_forbidden"] = True
                item["allowed_runtime_apply"] = False
                item["ai_review_blocked_reason"] = selected_decision
            elif selected_decision == "source_quality_blocker":
                item["classification_state"] = "code_patch_required"
            else:
                item["classification_state"] = "new_bucket_candidate"

    conclusions = ai_payload.get("final_conclusions") if isinstance(ai_payload.get("final_conclusions"), list) else []
    for conclusion in conclusions:
        if not isinstance(conclusion, dict):
            continue
        bucket_id = str(conclusion.get("bucket_id") or "")
        if bucket_id not in target_ids:
            continue
        item = by_id.get(bucket_id)
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
        if conclusion.get("selected_decision"):
            item["ai_tier2_taxonomy_decision"] = conclusion.get("selected_decision")
        if conclusion.get("selected_source"):
            item["ai_tier2_selected_source"] = conclusion.get("selected_source")
        if conclusion.get("confidence"):
            item["ai_tier2_confidence"] = conclusion.get("confidence")
        if conclusion.get("rejected_alternative_reason"):
            item["ai_tier2_rejection_reason"] = conclusion.get("rejected_alternative_reason")
        if final_state not in FINAL_CLASSIFICATION_STATES or final_decision == "keep":
            continue
        if final_state == "live_auto_apply_ready":
            if item.get("classification_state") == "live_auto_apply_ready" and item.get("live_auto_apply_family"):
                continue
            item["classification_state"] = "runtime_blocked_contract_gap"
            item["runtime_effect"] = False
            item["broker_order_forbidden"] = True
            item["allowed_runtime_apply"] = False
            item["ai_review_blocked_reason"] = "ai_live_auto_without_deterministic_contract"
            continue
        if final_state in {
            "source_only_keep_collecting",
            "sim_auto_approved",
            LIFECYCLE_FLOW_SIM_PROBE_STATE,
            "runtime_blocked_contract_gap",
            "code_patch_required",
            "code_review_failed",
            "automation_handoff_gap",
            "new_bucket_candidate",
        }:
            if (
                item.get("classification_state") == "live_auto_apply_ready"
                and item.get("live_auto_apply_family")
                and not explicit_tier2_block_allowed(final_reason, final_state)
            ):
                item["ai_review_block_ignored_reason"] = (
                    "ambiguous_or_non_contract_gap_live_then_verify"
                )
                item["ai_review_followup_required"] = "post_apply_verification"
                warnings.append("ai_review_ambiguous_live_candidate_kept_for_post_apply")
                continue
            item["classification_state"] = final_state
            _normalize_candidate_runtime_metadata(item)
            if final_state == "live_auto_apply_ready":
                contract = item.get("auto_promotion_contract") if isinstance(item.get("auto_promotion_contract"), dict) else {}
                item["auto_promotion_contract"] = {
                    **contract,
                    "state": "bounded_live_auto_apply_ready",
                    "tier2_status": ai_status,
                    "tier2_fail_closed": False,
                }
    for item in updated:
        _normalize_candidate_runtime_metadata(item)
    for item in updated:
        bucket_id = str(item.get("bucket_id") or "")
        if bucket_id not in target_ids:
            item.setdefault("ai_review_coverage", "unreviewed")
            continue
        if item.get("classification_state") != "live_auto_apply_ready":
            continue
        contract = item.get("auto_promotion_contract") if isinstance(item.get("auto_promotion_contract"), dict) else {}
        item["ai_review_status"] = ai_status
        item["auto_promotion_contract"] = {
            **contract,
            "state": "bounded_live_auto_apply_ready",
            "tier2_status": ai_status,
            "tier2_fail_closed": False,
        }
    return updated


def _raw_response_for_shard(raw_response: Any | None, shard_id: str) -> Any | None:
    if not isinstance(raw_response, dict):
        return raw_response
    shards = raw_response.get("shards")
    if isinstance(shards, dict):
        return shards.get(shard_id)
    if isinstance(shards, list):
        for item in shards:
            if isinstance(item, dict) and item.get("shard_id") == shard_id:
                return item.get("raw_response") if "raw_response" in item else item.get("response")
    if raw_response.get("schema_version") == 1:
        return raw_response
    return raw_response.get(shard_id)


def _apply_contamination_quarantine(
    candidates: list[dict[str, Any]],
    *,
    target_date: str,
    warnings: list[str],
) -> list[dict[str, Any]]:
    payload = _load_json(contamination_window_path(target_date))
    if not payload or not bool(payload.get("exclude_live_auto_apply", True)):
        return candidates
    affected_stages = {str(value) for value in payload.get("affected_stages") or [] if str(value)}
    affected_families = {str(value) for value in payload.get("affected_families") or [] if str(value)}
    affected_bucket_ids = {str(value) for value in payload.get("affected_bucket_ids") or [] if str(value)}
    updated: list[dict[str, Any]] = []
    blocked_count = 0
    for item in candidates:
        row = dict(item)
        if row.get("classification_state") != "live_auto_apply_ready":
            updated.append(row)
            continue
        match_all = not affected_stages and not affected_families and not affected_bucket_ids
        stage_hit = str(row.get("stage") or "") in affected_stages if affected_stages else False
        family_hit = str(row.get("live_auto_apply_family") or "") in affected_families if affected_families else False
        bucket_hit = str(row.get("bucket_id") or "") in affected_bucket_ids if affected_bucket_ids else False
        if not (match_all or stage_hit or family_hit or bucket_hit):
            updated.append(row)
            continue
        row["classification_state"] = "runtime_blocked_contract_gap"
        row["runtime_effect"] = False
        row["broker_order_forbidden"] = True
        row["allowed_runtime_apply"] = False
        row["contamination_quarantine_id"] = payload.get("quarantine_id") or f"lifecycle_bucket_quarantine:{target_date}"
        row["promotion_ev_excluded_reason"] = payload.get("reason") or "contaminated_greenfield_partial_lifecycle_policy"
        row["recommended_resolution"] = "exclude_contaminated_window_from_live_promotion"
        contract = row.get("auto_promotion_contract") if isinstance(row.get("auto_promotion_contract"), dict) else {}
        row["auto_promotion_contract"] = {
            **contract,
            "state": "source_only",
            "contamination_quarantine": True,
        }
        blocked_count += 1
        updated.append(row)
    if blocked_count:
        warnings.append(f"contamination_quarantine_live_auto_blocked:{blocked_count}")
    return updated


def _provider_status_looks_timeout(provider_status: dict[str, Any]) -> bool:
    text = json.dumps(provider_status, ensure_ascii=True, default=str).lower()
    return "timeout" in text or "timed out" in text or "deadline" in text


def _aggregate_ai_review_status(shard_records: list[dict[str, Any]]) -> str:
    statuses = [str(item.get("status") or "") for item in shard_records if item.get("candidate_count")]
    if not statuses:
        return "disabled"
    if all(status == "disabled" for status in statuses):
        return "disabled"
    if all(status == "parsed" for status in statuses):
        return "parsed"
    if any(status == "parsed" for status in statuses):
        return "partial"
    if all(status == "timeout" for status in statuses):
        return "timeout"
    if any(status == "timeout" for status in statuses):
        return "partial"
    if any(status == "parse_rejected" for status in statuses):
        return "parse_rejected"
    return statuses[0] if statuses else "unavailable"


def _run_ai_review_shards(
    report: dict[str, Any],
    *,
    provider: str,
    ai_raw_response: Any | None,
    warnings: list[str],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    candidates = report.get("candidates") if isinstance(report.get("candidates"), list) else []
    updated_candidates = [dict(item) for item in candidates]
    shard_specs = _build_ai_review_shards(report)
    shard_records: list[dict[str, Any]] = []
    combined_payload: dict[str, Any] = {
        "interpretation": {"bucket_reviews": []},
        "audit": {"status": "pass", "issues": [], "reason": "sharded review aggregate"},
        "ai_tier2_proposals": [],
        "comparative_reviews": [],
        "final_conclusions": [],
    }
    disabled = provider in {"none", "off", "false", "0"}
    for shard in shard_specs:
        shard_id = str(shard.get("shard_id") or "")
        shard_config = _ai_review_config_for_shard(shard_id)
        candidate_ids = {str(value) for value in (shard.get("candidate_ids") or []) if str(value)}
        provider_status: dict[str, Any] = {
            "provider": provider,
            "status": "disabled" if disabled else "not_called",
            "schema_name": AI_REVIEW_SCHEMA_NAME,
            "shard_id": shard_id,
            "input_context_hash": _text_hash(shard.get("context")),
            "input_context_chars": shard.get("context_chars"),
            **(shard_config.provider_status_fields() if not disabled else {"model": None}),
        }
        if disabled:
            provider_status.update({"reasoning_effort": None, "timeout_sec": None, "attempt_role": None, "retry_reason": None})
        if not candidate_ids:
            shard_records.append(
                {
                    "shard_id": shard_id,
                    "priority": shard.get("priority"),
                    "candidate_ids": [],
                    "candidate_count": 0,
                    "omitted_candidate_count": shard.get("omitted_candidate_count", 0),
                    "context_chars": shard.get("context_chars"),
                    "context_budget_chars": AI_REVIEW_SHARD_CONTEXT_BUDGET_CHARS,
                    "candidate_selection_policy": shard.get("candidate_selection_policy"),
                    "review_authority": shard.get("review_authority"),
                    "provider_status": {**provider_status, "status": "skipped_empty"},
                    "status": "skipped_empty",
                    "warnings": [],
                }
            )
            continue
        raw_response = _raw_response_for_shard(ai_raw_response, shard_id)
        if raw_response is None and disabled:
            ai_status = "disabled"
            ai_payload: dict[str, Any] = {}
            ai_warnings = ["ai_review_provider_disabled"]
        else:
            if raw_response is None and provider == "openai":
                raw_response, provider_status = _call_openai_ai_review(
                    shard.get("context") if isinstance(shard.get("context"), dict) else {},
                    shard_id=shard_id,
                    config=shard_config,
                )
            elif raw_response is not None:
                provider_status = {
                    **provider_status,
                    "status": "provided_response",
                }
            ai_status, ai_payload, ai_warnings = _parse_ai_review_response(raw_response)
            if ai_status == "unavailable" and _provider_status_looks_timeout(provider_status):
                ai_status = "timeout"
                ai_warnings = ["ai_review_timeout"]
        fail_closed_live = shard_id == "live_contract_review"
        updated_candidates = _apply_ai_review(
            updated_candidates,
            ai_status=ai_status,
            ai_payload=ai_payload,
            warnings=warnings,
            reviewed_bucket_ids=candidate_ids,
            fail_closed_live=fail_closed_live,
        )
        warnings.extend(ai_warnings)
        warnings.extend(f"{shard_id}:{warning}" for warning in ai_warnings)
        if ai_status == "parsed":
            interpretation = ai_payload.get("interpretation") if isinstance(ai_payload.get("interpretation"), dict) else {}
            bucket_reviews = interpretation.get("bucket_reviews") if isinstance(interpretation.get("bucket_reviews"), list) else []
            combined_payload["interpretation"]["bucket_reviews"].extend(bucket_reviews)
            audit = ai_payload.get("audit") if isinstance(ai_payload.get("audit"), dict) else {}
            audit_issues = audit.get("issues") if isinstance(audit.get("issues"), list) else []
            combined_payload["audit"]["issues"].extend(audit_issues)
            for key in ("ai_tier2_proposals", "comparative_reviews", "final_conclusions"):
                values = ai_payload.get(key) if isinstance(ai_payload.get(key), list) else []
                combined_payload[key].extend(values)
        shard_records.append(
            {
                "shard_id": shard_id,
                "priority": shard.get("priority"),
                "candidate_ids": sorted(candidate_ids),
                "candidate_count": len(candidate_ids),
                "omitted_candidate_count": shard.get("omitted_candidate_count", 0),
                "context_chars": shard.get("context_chars"),
                "context_budget_chars": AI_REVIEW_SHARD_CONTEXT_BUDGET_CHARS,
                "candidate_selection_policy": shard.get("candidate_selection_policy"),
                "review_authority": shard.get("review_authority"),
                "provider_status": provider_status,
                "status": ai_status,
                "warnings": ai_warnings,
            }
        )
    aggregate_status = _aggregate_ai_review_status(shard_records)
    reviewed_ids = {
        bucket_id
        for record in shard_records
        for bucket_id in (record.get("candidate_ids") or [])
        if record.get("status") == "parsed"
    }
    for item in updated_candidates:
        bucket_id = str(item.get("bucket_id") or "")
        if bucket_id not in reviewed_ids and item.get("ai_review_coverage") != "reviewed":
            item["ai_review_coverage"] = "unreviewed"
    review = {
        "provider": provider,
        "status": aggregate_status,
        "model": "sharded" if not disabled else None,
        "models_by_shard": {
            str(record.get("shard_id")): (record.get("provider_status") or {}).get("model")
            for record in shard_records
            if record.get("shard_id")
        },
        "reasoning_effort_by_shard": {
            str(record.get("shard_id")): (record.get("provider_status") or {}).get("reasoning_effort")
            for record in shard_records
            if record.get("shard_id")
        },
        "model_tier": "tier2",
        "schema_name": AI_REVIEW_SCHEMA_NAME,
        "sharded": True,
        "shard_count": len(shard_records),
        "parsed_shard_count": sum(1 for item in shard_records if item.get("status") == "parsed"),
        "reviewed_candidate_count": len(
            {
                bucket_id
                for record in shard_records
                if record.get("status") == "parsed"
                for bucket_id in (record.get("candidate_ids") or [])
            }
        ),
        "input_context_hash": _text_hash([record.get("provider_status", {}).get("input_context_hash") for record in shard_records]),
        "interpretation": combined_payload["interpretation"],
        "audit": combined_payload["audit"],
        "ai_tier2_proposals": combined_payload["ai_tier2_proposals"],
        "comparative_reviews": combined_payload["comparative_reviews"],
        "final_conclusions": combined_payload["final_conclusions"],
        "shards": shard_records,
        "warnings": [warning for record in shard_records for warning in (record.get("warnings") or [])],
    }
    return updated_candidates, review


def _finalize_report(
    report: dict[str, Any],
    candidates: list[dict[str, Any]],
    warnings: list[str],
) -> dict[str, Any]:
    state_counts = Counter(str(item.get("classification_state") or "unknown") for item in candidates)
    stage_counts = Counter(str(item.get("stage") or "unknown") for item in candidates)
    source_bucket_kind_counts = Counter(str(item.get("source_bucket_kind") or "unknown") for item in candidates)
    canonical_bucket_count = len({str(item.get("canonical_bucket") or item.get("bucket_id")) for item in candidates})
    legacy_bucket_count = len({str(item.get("legacy_raw_bucket_key") or item.get("bucket_key")) for item in candidates})
    deterministic_proposal_count = sum(1 for item in candidates if isinstance(item.get("deterministic_proposal"), dict))
    ai_tier2_proposal_count = sum(
        1
        for item in candidates
        if isinstance(item.get("ai_tier2_proposal"), dict)
        and item.get("ai_tier2_proposal", {}).get("proposal_status") == "provided"
    )
    selected_source_counts = Counter(
        str(
            (
                item.get("ai_tier2_comparative_review")
                if isinstance(item.get("ai_tier2_comparative_review"), dict)
                else {}
            ).get("selected_source")
            or "deterministic"
        )
        for item in candidates
    )
    selected_decision_counts = Counter(
        str(
            (
                item.get("ai_tier2_comparative_review")
                if isinstance(item.get("ai_tier2_comparative_review"), dict)
                else {}
            ).get("selected_decision")
            or "keep_bucket"
        )
        for item in candidates
    )
    unknown_reason_counts: Counter[str] = Counter()
    for item in candidates:
        counts = item.get("unknown_reason_counts") if isinstance(item.get("unknown_reason_counts"), dict) else {}
        for key, value in counts.items():
            unknown_reason_counts[str(key)] += _safe_int(value)
    surfaced = [
        item
        for item in candidates
        if str(item.get("classification_state") or "") in AUTO_SURFACE_STATES
        or (
            str(item.get("stage") or "") == "lifecycle_flow"
            and str(item.get("classification_state") or "") == "source_only_keep_collecting"
        )
    ]
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    summary.update(
        {
            "candidate_count": len(candidates),
            "surfaced_candidate_count": len(surfaced),
            "sim_auto_approved_count": state_counts.get("sim_auto_approved", 0),
            "entry_only_sim_auto_approved_count": state_counts.get("entry_only_sim_auto_approved", 0),
            "lifecycle_flow_sim_probe_candidate_count": state_counts.get(LIFECYCLE_FLOW_SIM_PROBE_STATE, 0),
            "live_auto_apply_ready_count": state_counts.get("live_auto_apply_ready", 0),
            "new_bucket_candidate_count": state_counts.get("new_bucket_candidate", 0),
            "code_patch_required_count": state_counts.get("code_patch_required", 0),
            "automation_handoff_gap_count": state_counts.get("automation_handoff_gap", 0),
            "state_counts": dict(state_counts),
            "stage_counts": dict(stage_counts),
            "source_bucket_kind_counts": dict(source_bucket_kind_counts),
            "unknown_reason_counts": dict(unknown_reason_counts),
            "canonical_bucket_count": canonical_bucket_count,
            "legacy_bucket_count": legacy_bucket_count,
            "absorbed_bucket_count": selected_decision_counts.get("absorb_as_dimension", 0),
            "deterministic_proposal_count": deterministic_proposal_count,
            "ai_tier2_proposal_count": ai_tier2_proposal_count,
            "reviewer_selected_deterministic_count": selected_source_counts.get("deterministic", 0),
            "reviewer_selected_ai_count": selected_source_counts.get("ai_tier2", 0),
            "reviewer_selected_hybrid_count": selected_source_counts.get("hybrid", 0),
            "reviewer_rejected_count": selected_source_counts.get("reject", 0)
            + selected_decision_counts.get("reject", 0),
            "source_quality_blocker_count": selected_decision_counts.get("source_quality_blocker", 0),
            "taxonomy_selected_decision_counts": dict(selected_decision_counts),
            "taxonomy_selected_source_counts": dict(selected_source_counts),
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
        item for item in candidates if str(item.get("classification_state") or "") in SIM_APPROVAL_STATES
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
    normalized_previous_contract = _normalize_source_contract_for_compare(previous_contract) if previous_contract else {}
    source_contract_changes = _compare_source_contracts(source_contract, previous_contract)
    if ldm:
        candidates.extend(
            _candidates_from_attribution(ldm, "lifecycle_flow", "lifecycle_flow_bucket_attribution")
        )
        candidates.extend(_candidates_from_attribution(ldm, "entry", "entry_bucket_attribution"))
        candidates.extend(_candidates_from_attribution(ldm, "holding", "holding_bucket_attribution"))
        candidates.extend(_candidates_from_attribution(ldm, "exit", "exit_bucket_attribution"))
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
        "forbidden_uses": list(BASE_FORBIDDEN_USES),
        "evidence_authority_contract": evidence_authority_contract(),
        "sources": {
            "lifecycle_decision_matrix": str(ldm_path) if ldm_path.exists() else None,
        },
        "source_contract": source_contract,
        "source_contract_previous_hash": _text_hash(normalized_previous_contract) if normalized_previous_contract else None,
        "source_contract_hash": _text_hash(source_contract) if source_contract else None,
        "source_contract_changes": source_contract_changes,
        "pre_final_auto_promotion_contract": pre_final_promotion_contract(),
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
    candidates_after_ai, ai_review = _run_ai_review_shards(
        report,
        provider=provider,
        ai_raw_response=ai_raw_response,
        warnings=warnings,
    )
    report["ai_two_pass_review"] = ai_review
    candidates_after_ai = _apply_contamination_quarantine(
        candidates_after_ai,
        target_date=target_date,
        warnings=warnings,
    )
    report = _finalize_report(report, candidates_after_ai, warnings)
    report["summary"]["ai_two_pass_review_status"] = ai_review.get("status")
    report["summary"]["ai_two_pass_review_required"] = True
    report["summary"]["ai_two_pass_review_shard_count"] = ai_review.get("shard_count")
    report["summary"]["ai_two_pass_review_parsed_shard_count"] = ai_review.get("parsed_shard_count")
    report["summary"]["ai_two_pass_review_reviewed_candidate_count"] = ai_review.get("reviewed_candidate_count")
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
        f"- ai_review_shards: `{summary.get('ai_two_pass_review_parsed_shard_count')}` / `{summary.get('ai_two_pass_review_shard_count')}` parsed, reviewed_candidates=`{summary.get('ai_two_pass_review_reviewed_candidate_count')}`",
        f"- surfaced_candidate_count: `{summary.get('surfaced_candidate_count')}`",
        f"- canonical/legacy buckets: `{summary.get('canonical_bucket_count')}` / `{summary.get('legacy_bucket_count')}`",
        f"- dual_proposals: deterministic=`{summary.get('deterministic_proposal_count')}` ai=`{summary.get('ai_tier2_proposal_count')}` hybrid_selected=`{summary.get('reviewer_selected_hybrid_count')}`",
        f"- absorbed/source_quality_blocker: `{summary.get('absorbed_bucket_count')}` / `{summary.get('source_quality_blocker_count')}`",
        f"- sim_auto_approved_count: `{summary.get('sim_auto_approved_count')}`",
        f"- lifecycle_flow_sim_probe_candidate_count: `{summary.get('lifecycle_flow_sim_probe_candidate_count')}`",
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
                f"- ai_tier2_proposal_count: `{len(ai_review.get('ai_tier2_proposals') or [])}`",
                f"- comparative_review_count: `{len(ai_review.get('comparative_reviews') or [])}`",
                f"- audit_status: `{audit.get('status') or '-'}`",
                f"- audit_issues: `{audit.get('issues') or []}`",
                f"- audit_reason: `{audit.get('reason') or '-'}`",
                "",
            ]
        )
        shards = ai_review.get("shards") if isinstance(ai_review.get("shards"), list) else []
        if shards:
            lines.append("### AI Review Shards")
            for shard in shards:
                if isinstance(shard, dict):
                    lines.append(
                        f"- `{shard.get('shard_id')}` status=`{shard.get('status')}` "
                        f"candidates=`{shard.get('candidate_count')}` omitted=`{shard.get('omitted_candidate_count')}` "
                        f"context_chars=`{shard.get('context_chars')}`"
                    )
            lines.append("")
    for item in (report.get("surfaced_candidates") or [])[:20]:
        lines.append(
            f"- `{item.get('bucket_id')}` stage=`{item.get('stage')}` "
            f"state=`{item.get('classification_state')}` action=`{item.get('recommended_action')}` "
            f"relation=`{item.get('bucket_relation')}` canonical=`{item.get('canonical_bucket')}` joined=`{item.get('joined_sample')}` "
            f"ev=`{item.get('source_quality_adjusted_ev_pct')}` ai_final=`{item.get('ai_final_decision') or '-'}`"
            f" taxonomy=`{item.get('ai_tier2_taxonomy_decision') or ((item.get('ai_tier2_comparative_review') or {}).get('selected_decision') if isinstance(item.get('ai_tier2_comparative_review'), dict) else '-')}`"
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
    approved_candidates = [
        item
        for item in (report.get("sim_auto_approved_candidates") or [])
        if isinstance(item, dict) and item.get("bucket_id")
    ]
    approved_bucket_ids = [str(item.get("bucket_id")) for item in approved_candidates]
    approved_bucket_rows = [
        {
            "bucket_id": str(item.get("bucket_id") or ""),
            "source_bucket_id": str(item.get("source_bucket_id") or ""),
            "classification_state": item.get("classification_state"),
            "source_bucket_kind": item.get("source_bucket_kind"),
            "stage": item.get("stage"),
            "bucket_type": item.get("bucket_type"),
            "source_quality_adjusted_ev_pct": item.get("source_quality_adjusted_ev_pct"),
            "sample": item.get("sample"),
            "joined_sample": item.get("joined_sample"),
            "complete_flow_count": item.get("complete_flow_count"),
            "incomplete_flow_count": item.get("incomplete_flow_count"),
        }
        for item in approved_candidates
    ]
    approved_source_bucket_ids = [
        str(row.get("source_bucket_id") or row.get("bucket_id") or "")
        for row in approved_bucket_rows
        if str(row.get("source_bucket_id") or row.get("bucket_id") or "").strip()
    ]
    grade_counts = Counter(str(item.get("evidence_grade") or "unknown") for item in approved_candidates)
    state_counts = Counter(str(item.get("classification_state") or "unknown") for item in approved_candidates)
    payload = {
        "schema_version": "lifecycle_bucket_sim_auto_approval_v1",
        "date": target_date,
        "generated_at": report.get("generated_at"),
        "policy_id": "lifecycle_bucket_discovery_sim_auto_approval",
        "approved": bool(approved_bucket_ids),
        "human_approval_required": False,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "decision_authority": "postclose_lifecycle_bucket_discovery_sim_auto",
        "policy_file": str(bucket_catalog_path(target_date)),
        "approved_bucket_ids": approved_bucket_ids,
        "approved_bucket_rows": approved_bucket_rows,
        "approved_bucket_count": len(approved_bucket_ids),
        "approved_unique_source_bucket_count": len(set(approved_source_bucket_ids)),
        "approved_state_counts": dict(sorted(state_counts.items())),
        "approved_lifecycle_flow_sim_probe_count": state_counts.get(LIFECYCLE_FLOW_SIM_PROBE_STATE, 0),
        "approved_evidence_grade_counts": dict(sorted(grade_counts.items())),
        "source_quality_status": "pass" if approved_bucket_ids else "empty",
        "blocked_reasons": [] if approved_bucket_ids else ["sim_auto_approved_bucket_missing"],
        "forbidden_uses": list(BASE_FORBIDDEN_USES),
        "evidence_authority_contract": evidence_authority_contract(),
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
        help="Provider for AI Tier2 two-pass bucket interpretation/audit.",
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
