"""Build a source-only two-pass AI review for pattern lab feedback."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from src.engine.ai.postclose_review_config import (
    PostcloseAIReviewConfig,
    first_wave_retry_reason,
    parsed_review_followup_reasons,
    resolve_postclose_ai_review_config,
)
from src.engine.daily_threshold_cycle_report import REPORT_DIR


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT_TYPE = "pattern_lab_ai_review"
REPORT_SCHEMA_VERSION = 1
AI_REVIEW_SCHEMA_NAME = "pattern_lab_ai_review_v1"
AI_REVIEW_MODEL = "gpt-5.4-mini"
AI_REVIEW_REASONING_EFFORT = "medium"
AI_REVIEW_TIMEOUT_SEC = 180
AI_REVIEW_DEFAULT_PROVIDER = "openai"
REPORT_DIRNAME = REPORT_TYPE
FORBIDDEN_USES = [
    "threshold mutation",
    "order guard mutation",
    "provider change",
    "bot restart",
    "broker order submit",
    "runtime env apply",
    "real order enable",
]
FINAL_STATES = {
    "source_only_keep_collecting",
    "automation_handoff_gap",
    "source_quality_gap",
    "ai_review_gap",
    "code_patch_required",
}
FINAL_DECISIONS = {"keep", "surface_workorder", "block_runtime_use"}
GAP_STATES = {"automation_handoff_gap", "source_quality_gap", "ai_review_gap", "code_patch_required"}
LATE_BOUND_FEEDBACK_SOURCE_LABELS = {
    "threshold_cycle_ev",
    "code_improvement_workorder",
}
# Keep this list limited to broad feedback-loop labels. Specific source gaps
# must pass their own source-context predicates before they can be resolved.
GENERIC_FEEDBACK_HANDOFF_REVIEW_IDS = {
    "pattern_lab_ai_review_followup_required",
    "swing_strategy_discovery_pending_quotes",
}


def report_paths(target_date: str) -> tuple[Path, Path]:
    base = REPORT_DIR / REPORT_DIRNAME / f"{REPORT_TYPE}_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _text_hash(payload: Any) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except Exception:
        return default


def _slug(value: Any, *, max_len: int = 80) -> str:
    text = re.sub(r"[^a-zA-Z0-9가-힣]+", "_", str(value or "").strip().lower()).strip("_")
    return text[:max_len] or "unknown"


def _source_rel(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _source_paths(target_date: str) -> dict[str, Path]:
    return {
        "scalping_pattern_lab_automation": REPORT_DIR
        / "scalping_pattern_lab_automation"
        / f"scalping_pattern_lab_automation_{target_date}.json",
        "swing_pattern_lab_automation": REPORT_DIR
        / "swing_pattern_lab_automation"
        / f"swing_pattern_lab_automation_{target_date}.json",
        "pattern_lab_currentness_audit": REPORT_DIR
        / "pattern_lab_currentness_audit"
        / f"pattern_lab_currentness_audit_{target_date}.json",
        "threshold_cycle_ev": REPORT_DIR / "threshold_cycle_ev" / f"threshold_cycle_ev_{target_date}.json",
        "code_improvement_workorder": REPORT_DIR
        / "code_improvement_workorder"
        / f"code_improvement_workorder_{target_date}.json",
        "lifecycle_decision_matrix": REPORT_DIR
        / "lifecycle_decision_matrix"
        / f"lifecycle_decision_matrix_{target_date}.json",
        "lifecycle_bucket_discovery": REPORT_DIR
        / "lifecycle_bucket_discovery"
        / f"lifecycle_bucket_discovery_{target_date}.json",
        "swing_lifecycle_decision_matrix": REPORT_DIR
        / "swing_lifecycle_decision_matrix"
        / f"swing_lifecycle_decision_matrix_{target_date}.json",
        "swing_lifecycle_bucket_discovery": REPORT_DIR
        / "swing_lifecycle_bucket_discovery"
        / f"swing_lifecycle_bucket_discovery_{target_date}.json",
        "swing_strategy_discovery_ev": REPORT_DIR
        / "swing_strategy_discovery_ev"
        / f"swing_strategy_discovery_ev_{target_date}.json",
        "pattern_lab_propagation_audit": REPORT_DIR
        / "pattern_lab_propagation_audit"
        / f"pattern_lab_propagation_audit_{target_date}.json",
    }


def _top_list(value: Any, limit: int = 5) -> list[Any]:
    return list(value[:limit]) if isinstance(value, list) else []


def _summary_for(payload: dict[str, Any]) -> dict[str, Any]:
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    ev_summary = payload.get("ev_report_summary") if isinstance(payload.get("ev_report_summary"), dict) else {}
    data_quality = payload.get("data_quality") if isinstance(payload.get("data_quality"), dict) else {}
    return {
        "status": payload.get("status") or summary.get("status"),
        "runtime_effect": payload.get("runtime_effect"),
        "allowed_runtime_apply": payload.get("allowed_runtime_apply"),
        "decision_authority": payload.get("decision_authority"),
        "summary": summary,
        "ev_report_summary": ev_summary,
        "source_quality_contracts": (
            ev_summary.get("source_quality_contracts")
            if isinstance(ev_summary.get("source_quality_contracts"), dict)
            else data_quality.get("source_quality_contracts")
            if isinstance(data_quality.get("source_quality_contracts"), dict)
            else {}
        ),
        "warnings": _top_list(payload.get("warnings"), 50),
    }


def _feedback_handoff_summary(payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    currentness = payloads.get("pattern_lab_currentness_audit") or {}
    currentness_summary = currentness.get("summary") if isinstance(currentness.get("summary"), dict) else {}
    feedback_labels = [
        "threshold_cycle_ev",
        "lifecycle_decision_matrix",
        "lifecycle_bucket_discovery",
        "swing_lifecycle_decision_matrix",
        "swing_lifecycle_bucket_discovery",
        "swing_strategy_discovery_ev",
    ]
    auxiliary_feedback_labels = [
        "code_improvement_workorder",
        "pattern_lab_propagation_audit",
    ]
    consumed_count = _safe_int(currentness_summary.get("consumed_feedback_source_count"), 0)
    missing_count = _safe_int(currentness_summary.get("missing_feedback_source_count"), 0)

    def _status_for(label: str) -> dict[str, Any]:
        payload = payloads.get(label) or {}
        summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
        return {
            "exists": bool(payload),
            "status": payload.get("status") or summary.get("status"),
            "runtime_effect": payload.get("runtime_effect"),
            "allowed_runtime_apply": payload.get("allowed_runtime_apply"),
            "candidate_count": summary.get("candidate_count")
            or summary.get("surfaced_candidate_count")
            or summary.get("candidate_ledger_count"),
            "workorder_count": summary.get("workorder_count") or summary.get("code_patch_required_count"),
        }

    source_statuses: dict[str, dict[str, Any]] = {}
    for label in feedback_labels:
        source_statuses[label] = _status_for(label)
    auxiliary_source_statuses = {label: _status_for(label) for label in auxiliary_feedback_labels}
    missing_required_labels = [
        label
        for label, item in source_statuses.items()
        if not item["exists"] and label not in LATE_BOUND_FEEDBACK_SOURCE_LABELS
    ]
    missing_late_bound_labels = [
        label
        for label, item in {**source_statuses, **auxiliary_source_statuses}.items()
        if not item["exists"] and label in LATE_BOUND_FEEDBACK_SOURCE_LABELS
    ]
    status = "pass"
    if missing_count > 0:
        status = "warning"
    if missing_required_labels:
        status = "warning"
    return {
        "status": status,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "decision_authority": "pattern_lab_feedback_handoff_source_only",
        "consumed_feedback_source_count": consumed_count,
        "missing_feedback_source_count": missing_count,
        "source_statuses": source_statuses,
        "auxiliary_source_statuses": auxiliary_source_statuses,
        "present_feedback_source_count": sum(1 for item in source_statuses.values() if item["exists"]),
        "present_auxiliary_source_count": sum(1 for item in auxiliary_source_statuses.values() if item["exists"]),
        "missing_feedback_source_labels": [
            label for label, item in source_statuses.items() if not item["exists"]
        ],
        "missing_auxiliary_source_labels": [
            label for label, item in auxiliary_source_statuses.items() if not item["exists"]
        ],
        "missing_required_feedback_source_labels": missing_required_labels,
        "missing_late_bound_source_labels": missing_late_bound_labels,
        "late_bound_source_policy": {
            "labels": sorted(LATE_BOUND_FEEDBACK_SOURCE_LABELS),
            "generation_order": "post_pattern_lab_same_postclose_chain",
            "decision_authority": "pattern_lab_feedback_handoff_source_only",
            "runtime_effect": False,
            "allowed_runtime_apply": False,
        },
        "interpretation_hint": (
            "Currentness audit reports pattern-lab feedback sources consumed; do not classify "
            "automation_handoff_gap unless a listed source is missing or has explicit fail status."
            if status == "pass"
            else "One or more feedback sources are missing or incomplete; source-only follow-up may be required."
        ),
    }


def _swing_micro_context_source_contract(context: dict[str, Any]) -> dict[str, Any]:
    sources = context.get("sources") if isinstance(context.get("sources"), dict) else {}
    swing = sources.get("swing_pattern_lab_automation") if isinstance(sources.get("swing_pattern_lab_automation"), dict) else {}
    summary = swing.get("summary") if isinstance(swing.get("summary"), dict) else {}
    contracts = summary.get("source_quality_contracts") if isinstance(summary.get("source_quality_contracts"), dict) else {}
    contract = contracts.get("swing_micro_context") if isinstance(contracts.get("swing_micro_context"), dict) else {}
    return contract


def _is_resolved_swing_micro_context_gap(item: dict[str, Any], context: dict[str, Any]) -> bool:
    if str(item.get("final_state") or "") != "source_quality_gap":
        return False
    review_id = str(item.get("review_id") or "").lower()
    reason = str(item.get("reason") or "").lower()
    if not any(token in f"{review_id} {reason}" for token in ("micro_context", "micro context", "ofi_qi")):
        return False
    contract = _swing_micro_context_source_contract(context)
    return (
        contract.get("source_contract_status") == "implemented"
        and contract.get("runtime_effect") is False
        and contract.get("allowed_runtime_apply") is False
        and contract.get("decision_authority") == "swing_pattern_lab_analysis_workorder_source_only"
    )


def _swing_lifecycle_bucket_discovery_summary(context: dict[str, Any]) -> dict[str, Any]:
    sources = context.get("sources") if isinstance(context.get("sources"), dict) else {}
    source = (
        sources.get("swing_lifecycle_bucket_discovery")
        if isinstance(sources.get("swing_lifecycle_bucket_discovery"), dict)
        else {}
    )
    summary = source.get("summary") if isinstance(source.get("summary"), dict) else {}
    return summary


def _source_summary(context: dict[str, Any], label: str) -> dict[str, Any]:
    sources = context.get("sources") if isinstance(context.get("sources"), dict) else {}
    source = sources.get(label) if isinstance(sources.get(label), dict) else {}
    summary = source.get("summary") if isinstance(source.get("summary"), dict) else {}
    return summary


def _source_wrapper(context: dict[str, Any], label: str) -> dict[str, Any]:
    sources = context.get("sources") if isinstance(context.get("sources"), dict) else {}
    return sources.get(label) if isinstance(sources.get(label), dict) else {}


def _nested_report_summary(source_summary: dict[str, Any]) -> dict[str, Any]:
    summary = source_summary.get("summary") if isinstance(source_summary.get("summary"), dict) else {}
    return summary


def _is_resolved_swing_lifecycle_bucket_discovery_gap(item: dict[str, Any], context: dict[str, Any]) -> bool:
    if str(item.get("final_state") or "") != "code_patch_required":
        return False
    review_id = str(item.get("review_id") or "").lower()
    reason = str(item.get("reason") or "").lower()
    if not any(
        token in f"{review_id} {reason}"
        for token in ("swing_lifecycle_bucket_discovery", "swing lifecycle bucket discovery")
    ):
        return False
    summary = _swing_lifecycle_bucket_discovery_summary(context)
    source_summary = summary.get("summary") if isinstance(summary.get("summary"), dict) else {}
    warnings = summary.get("warnings") if isinstance(summary.get("warnings"), list) else []
    return (
        source_summary.get("source_contract_status") == "pass"
        and _safe_int(source_summary.get("code_patch_required_count")) == 0
        and source_summary.get("ai_review_followup_required") is False
        and not any("source_contract_drift" in str(item) for item in warnings)
        and summary.get("runtime_effect") is False
        and summary.get("allowed_runtime_apply") is False
    )


def _is_resolved_swing_ai_review_missing_source_only_gap(item: dict[str, Any], context: dict[str, Any]) -> bool:
    if str(item.get("final_state") or "") != "ai_review_gap":
        return False
    review_id = str(item.get("review_id") or "").lower()
    reason = str(item.get("reason") or "").lower()
    if not any(token in review_id for token in ("ai_review_two_pass_missing", "ai_review_gap_missing_contract")) and not (
        "swing_lifecycle_bucket_discovery" in reason and "ai" in reason and "missing" in reason
    ):
        return False
    source_summary = _swing_lifecycle_bucket_discovery_summary(context)
    summary = _nested_report_summary(source_summary)
    sim_auto_unreviewed = _safe_int(summary.get("sim_auto_unreviewed_candidate_count"))
    sim_auto_downgraded = _safe_int(summary.get("sim_auto_downgraded_by_review_count"))
    return (
        summary.get("source_contract_status") == "pass"
        and source_summary.get("runtime_effect") is False
        and source_summary.get("allowed_runtime_apply") is False
        and summary.get("ai_fail_closed") is False
        and summary.get("ai_review_followup_required") is False
        and summary.get("sim_auto_blocked_by_ai_review_followup") is False
        and sim_auto_unreviewed == 0
        and sim_auto_downgraded == 0
    )


def _is_resolved_pattern_lab_code_improvement_pending_source_only_gap(
    item: dict[str, Any],
    context: dict[str, Any],
) -> bool:
    if str(item.get("final_state") or "") != "code_patch_required":
        return False
    if str(item.get("final_decision") or "") == "keep":
        return False
    review_id = str(item.get("review_id") or "").strip().lower()
    reason = str(item.get("reason") or "").lower()
    generic_instrumentation_gap = review_id == "instrumentation_gap" and any(
        token in reason
        for token in (
            "code improvement",
            "code_patch_required",
            "code patches",
            "implementation status",
        )
    )
    if review_id != "code_improvement_order_pending" and not generic_instrumentation_gap:
        return False
    if (
        "pending code improvement" not in reason
        and "pending" not in reason
        and not generic_instrumentation_gap
    ):
        return False
    if not _source_label_status_closed(context, "code_improvement_workorder"):
        return False
    if generic_instrumentation_gap:
        return _feedback_handoff_closed(context)
    orders = [
        item
        for item in (context.get("pattern_lab_workorder_orders") or [])
        if isinstance(item, dict)
    ]
    if not orders:
        return False
    disallowed = [
        order
        for order in orders
        if str(order.get("decision") or "") == "implement_now"
        and str(order.get("order_id") or "") not in {
            "order_pattern_lab_ai_review_ai_review_gap_missing_contract",
            "order_pattern_lab_ai_review_code_improvement_order_pending",
        }
    ]
    return not disallowed


_CLASSIFIED_THRESHOLD_EV_WARNING_PREFIXES = {
    "scalp_entry_adm:joined_sample_below_sample_floor",
    "scalp_entry_adm:unknown_bucket_source_quality_gap",
    "scalp_entry_adm:ai_numeric_consistency_rows_excluded_from_aggregates",
    "lifecycle_bucket_discovery:source_contract_drift_warning",
    "swing_strategy_discovery:pending_future_quotes",
    "swing_strategy_discovery:clean_tuning_baseline_swing_discovery_lookback_filtered",
    "swing_lifecycle_decision_matrix:swing_intraday_live_equiv_probe_missing",
    "swing_lifecycle_decision_matrix:pending_future_quotes",
    "swing_lifecycle_decision_matrix:clean_tuning_baseline_swing_discovery_lookback_filtered",
    "swing_lifecycle_bucket_discovery:ai_two_pass_review_missing_fail_closed",
    "swing_lifecycle_bucket_discovery:ai_two_pass_review_fail_closed_sim_auto_blocked",
    "pattern_lab_ai_review_warning",
    "pattern_lab_ai_review_ai_review_followup_required",
    "pattern_lab_propagation_audit_warning",
    "producer_gap_discovery_ai_review_followup_required",
}


def _threshold_cycle_ev_source_summary(context: dict[str, Any]) -> dict[str, Any]:
    sources = context.get("sources") if isinstance(context.get("sources"), dict) else {}
    source = sources.get("threshold_cycle_ev") if isinstance(sources.get("threshold_cycle_ev"), dict) else {}
    summary = source.get("summary") if isinstance(source.get("summary"), dict) else {}
    return summary


def _threshold_ev_warnings_are_classified_source_only(context: dict[str, Any]) -> bool:
    threshold_summary = _threshold_cycle_ev_source_summary(context)
    if not threshold_summary:
        return False
    if threshold_summary.get("runtime_effect") is True or threshold_summary.get("allowed_runtime_apply") is True:
        return False
    warnings = threshold_summary.get("warnings") if isinstance(threshold_summary.get("warnings"), list) else []
    if not warnings:
        return False
    unknown_warnings = [
        str(warning)
        for warning in warnings
        if not any(str(warning).startswith(prefix) for prefix in _CLASSIFIED_THRESHOLD_EV_WARNING_PREFIXES)
    ]
    if unknown_warnings:
        return False
    return _feedback_handoff_closed(context)


def _classified_source_only_warning_present(context: dict[str, Any], warning: str) -> bool:
    threshold_summary = _threshold_cycle_ev_source_summary(context)
    threshold_warnings = threshold_summary.get("warnings") if isinstance(threshold_summary.get("warnings"), list) else []
    return any(str(item) == warning for item in threshold_warnings)


def _is_resolved_classified_source_quality_warning_gap(item: dict[str, Any], context: dict[str, Any]) -> bool:
    final_state = str(item.get("final_state") or "")
    review_id = str(item.get("review_id") or "").strip().lower()
    reason = str(item.get("reason") or "").lower()
    lifecycle_drift_context = "lifecycle_bucket_discovery" in reason and (
        "source_contract_drift" in reason or "source contract drift" in reason
    )
    swing_strategy_source_only_context = review_id in {
        "swing_strategy_discovery_pending_future_quotes",
        "swing_strategy_discovery_ev",
    } or ("swing_strategy_discovery" in reason and "pending_future_quotes" in reason)
    swing_lifecycle_source_only_context = review_id.startswith("swing_lifecycle_decision_matrix") or (
        "swing_lifecycle_decision_matrix" in reason
        and ("pending_future_quotes" in reason or "swing_intraday_live_equiv_probe_missing" in reason)
    )
    pattern_lab_propagation_source_only_context = review_id.startswith("pattern_lab_propagation_audit") or (
        "pattern_lab_propagation_audit" in reason or "pattern lab propagation" in reason
    )
    swing_bucket_implemented_context = (
        ("swing_lifecycle_bucket_discovery" in reason or "swing lifecycle bucket discovery" in reason)
        and ("code_patch_required" in reason or "code patch" in reason)
    )
    if final_state != "source_quality_gap" and not (
        final_state == "automation_handoff_gap"
        and (
            swing_bucket_implemented_context
            or lifecycle_drift_context
            or swing_strategy_source_only_context
            or swing_lifecycle_source_only_context
            or pattern_lab_propagation_source_only_context
        )
    ):
        return False
    if str(item.get("final_decision") or "") == "keep":
        return False
    if review_id.startswith("threshold_cycle_ev"):
        threshold_summary = _threshold_cycle_ev_source_summary(context)
        nested_summary = _nested_report_summary(threshold_summary)
        return (
            (threshold_summary.get("runtime_effect") is False or nested_summary.get("runtime_effect") is False)
            and threshold_summary.get("allowed_runtime_apply") is not True
            and nested_summary.get("source_quality_status") == "warning"
            and _threshold_ev_warnings_are_classified_source_only(context)
        )
    if pattern_lab_propagation_source_only_context:
        source = _source_summary(context, "pattern_lab_propagation_audit")
        summary = _nested_report_summary(source)
        return (
            (source.get("runtime_effect") is False or summary.get("runtime_effect") is False)
            and source.get("allowed_runtime_apply") is not True
            and source.get("status") == "warning"
            and _classified_source_only_warning_present(context, "pattern_lab_propagation_audit_warning")
        )
    if review_id in {
        "lifecycle_bucket_discovery_source_contract_drift",
        "lifecycle_bucket_discovery",
        "source_contract_drift",
    } or lifecycle_drift_context:
        source_wrapper = _source_wrapper(context, "lifecycle_bucket_discovery")
        source = _source_summary(context, "lifecycle_bucket_discovery")
        summary = _nested_report_summary(source)
        source_warnings = source.get("warnings") if isinstance(source.get("warnings"), list) else []
        return (
            source.get("runtime_effect") is False
            and source.get("allowed_runtime_apply") is not True
            and source_wrapper.get("exists") is True
            and summary.get("source_contract_status") == "warning"
            and "source_contract_drift_warning" in [str(item) for item in source_warnings]
            and _classified_source_only_warning_present(
                context,
                "lifecycle_bucket_discovery:source_contract_drift_warning",
            )
        )
    if swing_strategy_source_only_context:
        source = _source_summary(context, "swing_strategy_discovery_ev")
        return (
            source.get("runtime_effect") is False
            and source.get("allowed_runtime_apply") is False
            and "pending_future_quotes" in [str(item) for item in source.get("warnings", [])]
            and _classified_source_only_warning_present(
                context,
                "swing_strategy_discovery:pending_future_quotes",
            )
        )
    if review_id in {
        "scalping_scalp_entry_adm_status_warning",
        "scalp_entry_adm_status_warning",
        "scalping_pattern_lab_automation",
    } or (
        "scalp_entry_adm_status" in reason or "scalp entry adm" in reason
        or "scalp_entry_adm" in reason
        or "entry adm" in reason
        or "scalping entry admission" in reason
        or "entry admission metric" in reason
    ):
        source = _source_summary(context, "scalping_pattern_lab_automation")
        source_only_warning = any(
            _classified_source_only_warning_present(context, warning)
            for warning in (
                "scalp_entry_adm:ai_numeric_consistency_rows_excluded_from_aggregates",
                "scalp_entry_adm:joined_sample_below_sample_floor",
                "scalp_entry_adm:unknown_bucket_source_quality_gap",
            )
        )
        return (
            source.get("runtime_effect") is False
            and source.get("allowed_runtime_apply") is False
            and source_only_warning
            and _threshold_ev_warnings_are_classified_source_only(context)
        )
    if review_id == "swing_lifecycle_decision_matrix_warnings" or swing_lifecycle_source_only_context or (
        ("pending future quotes" in reason or "pending_future_quotes" in reason)
        and ("intraday live probe" in reason or "swing_intraday_live_equiv_probe_missing" in reason)
    ):
        source = _source_summary(context, "swing_lifecycle_decision_matrix")
        source_warnings = {str(item) for item in source.get("warnings", [])}
        return (
            source.get("runtime_effect") is False
            and source.get("allowed_runtime_apply") is not True
            and bool(source_warnings)
            and source_warnings.issubset(
                {
                    "swing_intraday_live_equiv_probe_missing",
                    "pending_future_quotes",
                    "clean_tuning_baseline_swing_discovery_lookback_filtered",
                }
            )
            and _threshold_ev_warnings_are_classified_source_only(context)
        )
    if review_id == "swing_bucket_discovery_code_patch_required" or swing_bucket_implemented_context:
        source = _source_summary(context, "swing_lifecycle_bucket_discovery")
        summary = _nested_report_summary(source)
        code_patch_required = _safe_int(summary.get("code_patch_required_count"))
        implemented = summary.get("implemented_code_improvement_workorder_ids")
        pending = summary.get("pending_code_improvement_workorder_ids")
        implemented_count = len(implemented) if isinstance(implemented, list) else 0
        pending_count = len(pending) if isinstance(pending, list) else 0
        return (
            source.get("runtime_effect") is False
            and source.get("allowed_runtime_apply") is False
            and summary.get("source_contract_status") == "pass"
            and code_patch_required > 0
            and implemented_count >= code_patch_required
            and pending_count == 0
        )
    return False


def _is_resolved_threshold_cycle_ev_incomplete_gap(item: dict[str, Any], context: dict[str, Any]) -> bool:
    if str(item.get("final_state") or "") != "automation_handoff_gap":
        return False
    review_id = str(item.get("review_id") or "").lower()
    reason = str(item.get("reason") or "").lower()
    if (
        review_id != "threshold_cycle_ev"
        and "threshold_cycle_ev_incomplete" not in review_id
        and "threshold_cycle_ev" not in reason
    ):
        return False
    if not _threshold_ev_warnings_are_classified_source_only(context):
        return False
    threshold_summary = _threshold_cycle_ev_source_summary(context)
    nested_threshold_summary = _nested_report_summary(threshold_summary)
    if (
        review_id == "threshold_cycle_ev"
        and "sim_evidence_present_no_live_bucket" in reason
        and _safe_int(nested_threshold_summary.get("live_auto_ready_count"), 0) == 0
        and threshold_summary.get("runtime_effect") is not True
        and threshold_summary.get("allowed_runtime_apply") is not True
    ):
        return True
    source_summary = _swing_lifecycle_bucket_discovery_summary(context)
    summary = _nested_report_summary(source_summary)
    return (
        summary.get("source_contract_status") == "pass"
        and source_summary.get("runtime_effect") is False
        and source_summary.get("allowed_runtime_apply") is False
        and summary.get("ai_fail_closed") is False
        and summary.get("ai_review_followup_required") is False
        and _safe_int(summary.get("pre_review_sim_auto_candidate_count")) == 0
        and _safe_int(summary.get("sim_auto_unreviewed_candidate_count")) == 0
    )


def _resolved_source_context_conclusion(
    item: dict[str, Any],
    *,
    status: str,
    contract_id: str,
) -> dict[str, Any]:
    return {
        **item,
        "final_state": "source_only_keep_collecting",
        "final_decision": "keep",
        "explicit_gap_type": None,
        "auditor_pass": True,
        "source_context_resolution": {
            "status": status,
            "contract_id": contract_id,
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "decision_authority": "pattern_lab_ai_review_source_only",
        },
    }


def _apply_source_contract_resolutions(payload: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    conclusions = payload.get("final_conclusions") if isinstance(payload.get("final_conclusions"), list) else []
    resolved_ids: list[str] = []
    source_contract_resolution_ids: list[str] = []
    source_context_resolution_ids: list[str] = []
    resolved_conclusions: list[dict[str, Any]] = []
    for item in conclusions:
        if not isinstance(item, dict):
            continue
        if _is_resolved_swing_micro_context_gap(item, context):
            review_id = str(item.get("review_id") or "unknown")
            resolved_ids.append(review_id)
            source_contract_resolution_ids.append(review_id)
            resolved_conclusions.append(
                {
                    **item,
                    "final_state": "source_only_keep_collecting",
                    "final_decision": "keep",
                    "explicit_gap_type": None,
                    "auditor_pass": True,
                    "source_contract_resolution": {
                        "status": "resolved_by_implemented_source_contract",
                        "contract_id": "swing_micro_context_source_quality",
                        "runtime_effect": False,
                        "allowed_runtime_apply": False,
                    },
                }
            )
        elif _is_resolved_swing_lifecycle_bucket_discovery_gap(item, context):
            review_id = str(item.get("review_id") or "unknown")
            resolved_ids.append(review_id)
            source_contract_resolution_ids.append(review_id)
            resolved_conclusions.append(
                {
                    **item,
                    "final_state": "source_only_keep_collecting",
                    "final_decision": "keep",
                    "explicit_gap_type": None,
                    "auditor_pass": True,
                    "source_contract_resolution": {
                        "status": "resolved_by_implemented_source_contract",
                        "contract_id": "swing_lifecycle_bucket_discovery_code_patch_triage",
                        "runtime_effect": False,
                        "allowed_runtime_apply": False,
                    },
                }
            )
        elif _is_resolved_swing_ai_review_missing_source_only_gap(item, context):
            review_id = str(item.get("review_id") or "unknown")
            resolved_ids.append(review_id)
            source_context_resolution_ids.append(review_id)
            resolved_conclusions.append(
                _resolved_source_context_conclusion(
                    item,
                    status="resolved_by_source_only_sim_auto_review_contract",
                    contract_id="swing_lifecycle_bucket_discovery_ai_review_source_only_reviewed",
                )
            )
        elif _is_resolved_threshold_cycle_ev_incomplete_gap(item, context):
            review_id = str(item.get("review_id") or "unknown")
            resolved_ids.append(review_id)
            source_context_resolution_ids.append(review_id)
            resolved_conclusions.append(
                _resolved_source_context_conclusion(
                    item,
                    status="resolved_by_classified_threshold_ev_source_only_warnings",
                    contract_id="threshold_cycle_ev_warning_classification",
                )
            )
        elif _is_resolved_pattern_lab_code_improvement_pending_source_only_gap(item, context):
            review_id = str(item.get("review_id") or "unknown")
            resolved_ids.append(review_id)
            source_context_resolution_ids.append(review_id)
            resolved_conclusions.append(
                _resolved_source_context_conclusion(
                    item,
                    status="resolved_by_current_code_improvement_workorder_self_reference",
                    contract_id="pattern_lab_ai_review_code_improvement_order_pending_source_only",
                )
            )
        elif _is_resolved_classified_source_quality_warning_gap(item, context):
            review_id = str(item.get("review_id") or "unknown")
            resolved_ids.append(review_id)
            source_context_resolution_ids.append(review_id)
            resolved_conclusions.append(
                _resolved_source_context_conclusion(
                    item,
                    status="resolved_by_classified_source_quality_warning",
                    contract_id="pattern_lab_ai_review_classified_source_quality_warning",
                )
            )
        else:
            resolved_conclusions.append(item)
    if not resolved_ids:
        return payload
    audit = payload.get("audit") if isinstance(payload.get("audit"), dict) else {}
    remaining_gap = any(
        isinstance(item, dict)
        and str(item.get("final_state") or "") in GAP_STATES
        and str(item.get("final_decision") or "") != "keep"
        for item in resolved_conclusions
    )
    payload = {**payload, "final_conclusions": resolved_conclusions}
    audit_issues = audit.get("issues") if isinstance(audit.get("issues"), list) else []
    remaining_issues = [issue for issue in audit_issues if str(issue) not in set(resolved_ids)]
    payload["audit"] = {
        **audit,
        "status": "correction_required" if remaining_gap else "pass",
        "source_contract_resolutions": source_contract_resolution_ids,
        "source_context_resolutions": source_context_resolution_ids,
        "issues": remaining_issues if remaining_gap else [],
        "reason": (
            audit.get("reason")
            if remaining_gap
            else "Source-only review gaps were resolved by implemented source contracts; runtime authority remains false."
        ),
    }
    return payload


def _feedback_handoff_closed(context: dict[str, Any]) -> bool:
    handoff = context.get("feedback_handoff_summary") if isinstance(context.get("feedback_handoff_summary"), dict) else {}
    if handoff.get("status") != "pass" or _safe_int(handoff.get("missing_feedback_source_count"), 0) != 0:
        return False
    currentness_failures = [
        item
        for item in context.get("currentness_checks", [])
        if isinstance(item, dict) and str(item.get("status") or "") == "fail"
    ]
    if currentness_failures:
        return False
    source_statuses = handoff.get("source_statuses") if isinstance(handoff.get("source_statuses"), dict) else {}
    return all(
        isinstance(item, dict)
        and item.get("exists") is True
        and str(item.get("status") or "pass") not in {"fail", "failed"}
        for label, item in source_statuses.items()
        if label not in LATE_BOUND_FEEDBACK_SOURCE_LABELS
    )


def _source_label_status_closed(context: dict[str, Any], label: str) -> bool:
    sources = context.get("sources") if isinstance(context.get("sources"), dict) else {}
    source = sources.get(label) if isinstance(sources.get(label), dict) else {}
    if not source:
        return label in LATE_BOUND_FEEDBACK_SOURCE_LABELS and _feedback_handoff_closed(context)
    if source.get("exists") is False or not source.get("path"):
        return label in LATE_BOUND_FEEDBACK_SOURCE_LABELS and _feedback_handoff_closed(context)
    summary = source.get("summary") if isinstance(source.get("summary"), dict) else {}
    status = str(source.get("status") or summary.get("status") or "pass").lower()
    if status in {"fail", "failed"}:
        return False
    return source.get("runtime_effect") is not True and source.get("allowed_runtime_apply") is not True


_FEEDBACK_SOURCE_REVIEW_IDS = {
    "scalping_pattern_lab_automation",
    "swing_pattern_lab_automation",
    "pattern_lab_currentness_audit",
    "threshold_cycle_ev",
    "code_improvement_workorder",
    "pattern_lab_propagation_audit",
}


def _mentioned_feedback_source_labels(item: dict[str, Any]) -> list[str]:
    review_id = str(item.get("review_id") or "").strip().lower()
    reason = str(item.get("reason") or "").lower()
    normalized_reason = reason.replace(" ", "_")
    return [
        label
        for label in _FEEDBACK_SOURCE_REVIEW_IDS
        if review_id == label or label in reason or label in normalized_reason
    ]


def _has_unclosed_mentioned_feedback_source_gap(item: dict[str, Any], context: dict[str, Any]) -> bool:
    reason = str(item.get("reason") or "").lower()
    if not any(token in reason for token in ("missing", "absence", "incomplete", "handoff", "feedback")):
        return False
    return any(
        not _source_label_status_closed(context, label)
        for label in _mentioned_feedback_source_labels(item)
    )


def _is_resolved_feedback_source_missing_gap(item: dict[str, Any], context: dict[str, Any]) -> bool:
    if str(item.get("final_state") or "") not in {"automation_handoff_gap", "ai_review_gap"}:
        return False
    if str(item.get("final_decision") or "") == "keep":
        return False
    if not _feedback_handoff_closed(context):
        return False
    reason = str(item.get("reason") or "").lower()
    matched_labels = _mentioned_feedback_source_labels(item)
    if not matched_labels:
        return False
    if not any(token in reason for token in ("missing", "absence", "incomplete", "handoff", "feedback")):
        return False
    return all(_source_label_status_closed(context, label) for label in matched_labels)


def _is_resolved_closed_feedback_handoff_gap(item: dict[str, Any], context: dict[str, Any]) -> bool:
    if str(item.get("final_state") or "") != "automation_handoff_gap":
        return False
    if str(item.get("final_decision") or "") == "keep":
        return False
    if not _feedback_handoff_closed(context):
        return False
    if _is_resolved_feedback_source_missing_gap(item, context):
        return False
    review_id = str(item.get("review_id") or "").strip().lower()
    reason = str(item.get("reason") or "").lower()
    text = f"{review_id} {reason}"
    if not any(token in text for token in ("ldm", "threshold", "feedback")):
        return False
    if not any(token in text for token in ("missing", "absence", "not properly propagating")):
        return False
    return True


def _is_resolved_code_improvement_workorder_self_review_gap(item: dict[str, Any], context: dict[str, Any]) -> bool:
    if str(item.get("final_state") or "") != "ai_review_gap":
        return False
    if str(item.get("final_decision") or "") == "keep":
        return False
    review_id = str(item.get("review_id") or "").strip().lower()
    reason = str(item.get("reason") or "").lower()
    code_workorder_reason = "code_improvement_workorder" in reason or "code improvement workorder" in reason
    if review_id not in {"code_improvement_workorder", "code_improvement_workorder_ai_review_gap"} and not (
        review_id.startswith("ai_review_followup") and code_workorder_reason
    ):
        return False
    if not _feedback_handoff_closed(context):
        return False
    return _source_label_status_closed(context, "code_improvement_workorder")


def _is_resolved_pattern_lab_ai_review_contract_gap(item: dict[str, Any], context: dict[str, Any]) -> bool:
    if str(item.get("final_state") or "") != "ai_review_gap":
        return False
    if str(item.get("final_decision") or "") == "keep":
        return False
    if _has_unclosed_mentioned_feedback_source_gap(item, context):
        return False
    review_id = str(item.get("review_id") or "").strip().lower()
    reason = str(item.get("reason") or "").lower()
    text = f"{review_id} {reason}"
    if not any(
        token in text
        for token in (
            "two-pass",
            "two_pass",
            "ai reviewer",
            "reviewer contract",
            "ai review contract",
            "review contract",
        )
    ):
        return False
    checks = context.get("currentness_checks") if isinstance(context.get("currentness_checks"), list) else []
    return any(
        isinstance(check, dict)
        and check.get("check_id") == "pattern_lab_ai_review_contract"
        and check.get("status") == "pass"
        for check in checks
    )


def _apply_feedback_handoff_resolutions(payload: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    if not _feedback_handoff_closed(context):
        return payload
    audit = payload.get("audit") if isinstance(payload.get("audit"), dict) else {}
    forbidden = audit.get("forbidden_use_violations") if isinstance(audit.get("forbidden_use_violations"), list) else []
    if forbidden:
        return payload
    conclusions = payload.get("final_conclusions") if isinstance(payload.get("final_conclusions"), list) else []
    resolved_ids: list[str] = []
    resolved_conclusions: list[dict[str, Any]] = []
    for item in conclusions:
        if not isinstance(item, dict):
            continue
        final_state = str(item.get("final_state") or "")
        review_id = str(item.get("review_id") or "unknown")
        generic_review = review_id.startswith("interpretation_") or review_id in GENERIC_FEEDBACK_HANDOFF_REVIEW_IDS
        source_missing_gap = _is_resolved_feedback_source_missing_gap(item, context)
        closed_handoff_gap = _is_resolved_closed_feedback_handoff_gap(item, context)
        self_review_gap = _is_resolved_code_improvement_workorder_self_review_gap(item, context)
        ai_review_contract_gap = _is_resolved_pattern_lab_ai_review_contract_gap(item, context)
        if final_state in {"automation_handoff_gap", "ai_review_gap"} and (
            generic_review or source_missing_gap or closed_handoff_gap or self_review_gap or ai_review_contract_gap
        ):
            resolved_ids.append(review_id)
            resolved_conclusions.append(
                {
                    **item,
                    "final_state": "source_only_keep_collecting",
                    "final_decision": "keep",
                    "explicit_gap_type": None,
                    "auditor_pass": True,
                    "feedback_handoff_resolution": {
                        "status": (
                            "resolved_by_currentness_feedback_handoff_pass"
                            if generic_review
                            else "resolved_by_existing_code_improvement_workorder_context"
                            if self_review_gap
                            else "resolved_by_currentness_feedback_handoff_pass"
                            if closed_handoff_gap
                            else "resolved_by_currentness_ai_review_contract_pass"
                            if ai_review_contract_gap
                            else "resolved_by_existing_feedback_source_context"
                        ),
                        "runtime_effect": False,
                        "allowed_runtime_apply": False,
                        "decision_authority": "pattern_lab_feedback_handoff_source_only",
                    },
                }
            )
        else:
            resolved_conclusions.append(item)
    if not resolved_ids:
        return payload
    audit = payload.get("audit") if isinstance(payload.get("audit"), dict) else {}
    remaining_gap = any(
        isinstance(item, dict)
        and str(item.get("final_state") or "") in GAP_STATES
        and str(item.get("final_decision") or "") != "keep"
        for item in resolved_conclusions
    )
    return {
        **payload,
        "final_conclusions": resolved_conclusions,
        "audit": {
            **audit,
            "status": "correction_required" if remaining_gap else "pass",
            "feedback_handoff_resolutions": resolved_ids,
            "issues": audit.get("issues") if remaining_gap else [],
            "reason": (
                audit.get("reason")
                if remaining_gap
                else "Pattern-lab feedback handoff is closed by currentness audit; generic AI handoff gaps were normalized to source-only keep."
            ),
        },
    }


def _normalize_empty_audit_correction(payload: dict[str, Any]) -> dict[str, Any]:
    audit = payload.get("audit") if isinstance(payload.get("audit"), dict) else {}
    if str(audit.get("status") or "") != "correction_required":
        return payload
    issues = audit.get("issues") if isinstance(audit.get("issues"), list) else []
    forbidden = (
        audit.get("forbidden_use_violations")
        if isinstance(audit.get("forbidden_use_violations"), list)
        else []
    )
    if issues or forbidden:
        return payload
    conclusions = payload.get("final_conclusions") if isinstance(payload.get("final_conclusions"), list) else []
    unresolved_gap = any(
        isinstance(item, dict)
        and str(item.get("final_state") or "") in GAP_STATES
        and str(item.get("final_decision") or "") != "keep"
        for item in conclusions
    )
    if unresolved_gap:
        return payload
    return {
        **payload,
        "audit": {
            **audit,
            "status": "pass",
            "reason": (
                "Empty correction_required audit normalized to pass; explicit final conclusions, "
                "if any, remain source-only workorder inputs."
            ),
        },
    }


def _normalize_audit_resolution_fields(payload: dict[str, Any]) -> dict[str, Any]:
    audit = payload.get("audit") if isinstance(payload.get("audit"), dict) else {}
    conclusions = payload.get("final_conclusions") if isinstance(payload.get("final_conclusions"), list) else []
    if not audit or not conclusions:
        return payload
    source_context_ids = {
        str(item.get("review_id"))
        for item in conclusions
        if isinstance(item, dict) and isinstance(item.get("source_context_resolution"), dict)
    }
    if not source_context_ids:
        return payload
    contract_ids = audit.get("source_contract_resolutions")
    if not isinstance(contract_ids, list):
        contract_ids = []
    context_ids = audit.get("source_context_resolutions")
    if not isinstance(context_ids, list):
        context_ids = []
    normalized_contract_ids = [item for item in contract_ids if str(item) not in source_context_ids]
    normalized_context_ids = list(dict.fromkeys([*context_ids, *sorted(source_context_ids)]))
    reason = audit.get("reason")
    if normalized_context_ids and not normalized_contract_ids:
        reason = "Source-only review gaps were resolved by source-context provenance; runtime authority remains false."
    return {
        **payload,
        "audit": {
            **audit,
            "source_contract_resolutions": normalized_contract_ids,
            "source_context_resolutions": normalized_context_ids,
            "reason": reason,
        },
    }


def _build_input_context(target_date: str) -> dict[str, Any]:
    paths = _source_paths(target_date)
    payloads = {label: _load_json(path) for label, path in paths.items()}
    currentness = payloads["pattern_lab_currentness_audit"]
    currentness_checks = [
        {
            "check_id": item.get("check_id"),
            "status": item.get("status"),
            "severity": item.get("severity"),
            "finding": item.get("finding"),
        }
        for item in currentness.get("checks", [])
        if isinstance(item, dict)
    ][:20]
    workorder = payloads["code_improvement_workorder"]
    workorder_orders = [
        {
            "order_id": item.get("order_id"),
            "title": item.get("title"),
            "source_report_type": item.get("source_report_type"),
            "decision": item.get("decision"),
        }
        for item in workorder.get("orders", [])
        if isinstance(item, dict)
        and str(item.get("source_report_type") or "").startswith("pattern_lab")
    ][:20]
    sources = {
        label: {
            "path": str(path) if path.exists() else None,
            "exists": path.exists(),
            "summary": _summary_for(payloads[label]),
        }
        for label, path in paths.items()
    }
    return {
        "date": target_date,
        "review_authority": "pattern_lab_ai_review_source_only",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "forbidden_uses": FORBIDDEN_USES,
        "sources": sources,
        "feedback_handoff_summary": _feedback_handoff_summary(payloads),
        "currentness_checks": currentness_checks,
        "pattern_lab_workorder_orders": workorder_orders,
    }


def _state_for_check(check: dict[str, Any]) -> str:
    severity = str(check.get("severity") or "")
    if severity == "automation_handoff_gap":
        return "automation_handoff_gap"
    if severity == "ai_review_gap":
        return "ai_review_gap"
    if severity == "source_quality_blocker":
        return "source_quality_gap"
    if str(check.get("status") or "") == "fail":
        return "code_patch_required"
    return "source_only_keep_collecting"


def _domain_for_check(check_id: str) -> str:
    if "swing" in check_id or "deepseek" in check_id:
        return "swing"
    if "scalping" in check_id or "gemini" in check_id or "claude" in check_id:
        return "scalping"
    return "cross_domain"


def _explicit_gap_type(final_state: str) -> str | None:
    if final_state == "automation_handoff_gap":
        return "automation_handoff_gap"
    if final_state == "source_quality_gap":
        return "source_quality_gap"
    if final_state == "ai_review_gap":
        return "ai_review_gap"
    if final_state == "code_patch_required":
        return "code_patch_required"
    return None


def _source_path_labels_for_domain(context: dict[str, Any], domain: str) -> list[str]:
    sources = context.get("sources") if isinstance(context.get("sources"), dict) else {}
    if domain == "scalping":
        labels = [
            "scalping_pattern_lab_automation",
            "pattern_lab_currentness_audit",
            "threshold_cycle_ev",
            "code_improvement_workorder",
            "lifecycle_decision_matrix",
            "lifecycle_bucket_discovery",
            "pattern_lab_propagation_audit",
        ]
    elif domain == "swing":
        labels = [
            "swing_pattern_lab_automation",
            "pattern_lab_currentness_audit",
            "threshold_cycle_ev",
            "code_improvement_workorder",
            "swing_lifecycle_decision_matrix",
            "swing_lifecycle_bucket_discovery",
            "swing_strategy_discovery_ev",
            "pattern_lab_propagation_audit",
        ]
    else:
        labels = list(sources)
    result: list[str] = []
    for label in labels:
        source = sources.get(label) if isinstance(sources.get(label), dict) else {}
        path = source.get("path")
        if path:
            result.append(str(path))
    return result[:12]


def _normalize_final_conclusion(item: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    final_state = str(item.get("final_state") or "source_only_keep_collecting")
    if final_state not in FINAL_STATES:
        final_state = "code_patch_required"
    final_decision = str(item.get("final_decision") or "")
    if final_decision not in FINAL_DECISIONS:
        final_decision = "surface_workorder" if final_state in GAP_STATES else "keep"
    if final_decision == "keep" and final_state in GAP_STATES:
        final_state = "source_only_keep_collecting"
    domain = str(item.get("domain") or "cross_domain")
    auditor_pass = item.get("auditor_pass")
    if auditor_pass is None:
        auditor_pass = final_decision != "block_runtime_use" and final_state not in {"ai_review_gap"}
    if final_decision == "keep" and final_state == "source_only_keep_collecting":
        auditor_pass = True
    explicit_gap_type = item.get("explicit_gap_type") or _explicit_gap_type(final_state)
    source_paths = item.get("source_paths") if isinstance(item.get("source_paths"), list) else []
    if not source_paths:
        source_paths = _source_path_labels_for_domain(context, domain)
    return {
        **item,
        "review_id": str(item.get("review_id") or "unknown"),
        "domain": domain,
        "final_state": final_state,
        "final_decision": final_decision,
        "auditor_pass": bool(auditor_pass),
        "explicit_gap_type": explicit_gap_type,
        "source_paths": [str(path) for path in source_paths][:12],
        "forbidden_runtime_uses": FORBIDDEN_USES,
    }


def _deterministic_two_pass_review(context: dict[str, Any]) -> dict[str, Any]:
    checks = [
        item
        for item in context.get("currentness_checks", [])
        if isinstance(item, dict) and str(item.get("status") or "") == "fail"
    ]
    review_items: list[dict[str, Any]] = []
    for check in checks[:20]:
        check_id = str(check.get("check_id") or "unknown")
        state = _state_for_check(check)
        review_items.append(
            {
                "review_id": f"currentness:{check_id}",
                "domain": _domain_for_check(check_id),
                "interpreted_state": state,
                "confidence": "high" if state in {"automation_handoff_gap", "ai_review_gap"} else "medium",
                "reason": str(check.get("finding") or "currentness audit surfaced a source-quality gap")[:240],
            }
        )
    if not review_items:
        review_items.append(
            {
                "review_id": "pattern_lab_feedback_loop:keep_collecting",
                "domain": "cross_domain",
                "interpreted_state": "source_only_keep_collecting",
                "confidence": "medium",
                "reason": "No currentness failure was present; preserve pattern lab output as source-only feedback.",
            }
        )
    forbidden_violations: list[str] = []
    for source in (context.get("sources") or {}).values():
        if not isinstance(source, dict):
            continue
        summary = source.get("summary") if isinstance(source.get("summary"), dict) else {}
        if summary.get("runtime_effect") is True or summary.get("allowed_runtime_apply") is True:
            forbidden_violations.append(str(source.get("path") or "unknown"))
    audit_status = "correction_required" if forbidden_violations else "pass"
    issue_counts = Counter(str(item.get("interpreted_state") or "") for item in review_items)
    audit_issues = [
        f"{state}:{count}"
        for state, count in sorted(issue_counts.items())
        if state in GAP_STATES and count > 0
    ]
    final_conclusions = [
        _normalize_final_conclusion(
            {
            "review_id": item["review_id"],
            "domain": item["domain"],
            "final_state": item["interpreted_state"],
            "final_decision": (
                "block_runtime_use"
                if forbidden_violations
                else "surface_workorder"
                if item["interpreted_state"] in GAP_STATES
                else "keep"
            ),
            "reason": item["reason"],
            "required_followup": (
                ["preserve_runtime_effect_false", "surface_code_improvement_workorder"]
                if item["interpreted_state"] in GAP_STATES
                else ["keep_collecting"]
            ),
            },
            context,
        )
        for item in review_items
    ]
    return {
        "schema_version": 1,
        "interpretation": {
            "review_items": review_items,
            "source_feedback_status": "warning" if audit_issues else "pass",
        },
        "audit": {
            "status": audit_status,
            "issues": audit_issues,
            "forbidden_use_violations": forbidden_violations,
            "reason": (
                "Audit found forbidden runtime authority in source-only pattern lab flow."
                if forbidden_violations
                else "Second-pass audit preserved source-only authority and surfaced explicit gaps only."
            ),
        },
        "final_conclusions": final_conclusions,
    }


def _build_ai_review_instructions() -> str:
    return (
        "You are the Pattern Lab source-only AI reviewer.\n"
        "Use a mandatory two-pass process: first interpretation, then audit, then final conclusions.\n"
        "Your output is report/workorder source only. Never propose threshold mutation, broker order submit, "
        "provider change, bot restart, runtime env apply, real order enable, cap release, or safety guard bypass.\n"
        "Treat pattern labs as analysis and source-quality workorder inputs. They cannot replace LDM, bucket "
        "discovery, runtime bridge, approval contracts, or deterministic guards.\n"
        "If LDM/threshold feedback is missing from pattern lab inputs, classify it as automation_handoff_gap.\n"
        "If the reviewer contract itself is missing or incomplete, classify it as ai_review_gap.\n"
        "Ambiguity alone must not block sim-only collection; only explicit source-quality, schema, handoff, "
        "forbidden-use, or instrumentation gaps should surface workorders.\n"
        "Return only JSON conforming to pattern_lab_ai_review_v1."
    )


def _ai_review_config(
    *,
    attempt_role: str = "primary",
    retry_reason: str | None = None,
) -> PostcloseAIReviewConfig:
    return resolve_postclose_ai_review_config(
        "PATTERN_LAB_AI_REVIEW",
        default_model=AI_REVIEW_MODEL,
        default_reasoning_effort="low" if attempt_role == "retry" else AI_REVIEW_REASONING_EFFORT,
        default_timeout_sec=AI_REVIEW_TIMEOUT_SEC,
        attempt_role=attempt_role,
        retry_reason=retry_reason,
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
        if not isinstance(payload.get("interpretation"), dict):
            return False, "missing_interpretation"
        if not isinstance(payload.get("final_conclusions"), list):
            return False, "missing_final_conclusions"
        if audit.get("status") not in {"pass", "correction_required", "insufficient_context"}:
            return False, "missing_audit_status"
        if warnings:
            return False, "warnings:" + ",".join(warnings[:3])
        return True, ""

    from src.engine.ai.postclose_structured_review_provider import call_postclose_structured_review

    return call_postclose_structured_review(
        context,
        schema_name=AI_REVIEW_SCHEMA_NAME,
        instructions=_build_ai_review_instructions(),
        config=config,
        metadata={"endpoint_name": "pattern_lab_ai_review", "report_type": REPORT_TYPE},
        contract_validator=_contract_validator,
        ensure_ascii=False,
    )


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
    interpretation = payload.get("interpretation") if isinstance(payload.get("interpretation"), dict) else {}
    audit = payload.get("audit") if isinstance(payload.get("audit"), dict) else {}
    conclusions = payload.get("final_conclusions") if isinstance(payload.get("final_conclusions"), list) else []
    if not isinstance(interpretation.get("review_items"), list):
        warnings.append("ai_review_interpretation_missing_review_items")
    if str(audit.get("status") or "") not in {"pass", "correction_required", "insufficient_context"}:
        warnings.append("ai_review_audit_status_invalid")
    if not isinstance(audit.get("forbidden_use_violations"), list):
        warnings.append("ai_review_audit_forbidden_uses_missing")
    for item in conclusions:
        if not isinstance(item, dict):
            warnings.append("ai_review_final_conclusion_non_dict")
            continue
        if str(item.get("final_state") or "") not in FINAL_STATES:
            warnings.append(f"ai_review_invalid_final_state:{item.get('review_id')}")
        if str(item.get("final_decision") or "") not in FINAL_DECISIONS:
            warnings.append(f"ai_review_invalid_final_decision:{item.get('review_id')}")
    if warnings:
        return "parse_rejected", payload, warnings
    return "parsed", payload, []


def _order_from_conclusion(conclusion: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    review_id = str(conclusion.get("review_id") or "unknown")
    final_state = str(conclusion.get("final_state") or "code_patch_required")
    implementation_status, implementation_provenance = _implementation_marker_for_conclusion(conclusion, context)
    order = {
        "order_id": f"order_{REPORT_TYPE}_{_slug(review_id)}",
        "title": f"Pattern Lab AI review follow-up: {review_id}",
        "source_report_type": REPORT_TYPE,
        "review_id": review_id,
        "lifecycle_stage": "pattern_lab_ai_review",
        "target_subsystem": "pattern_lab",
        "priority": 10,
        "route": "implement_now",
        "confidence": "ai_two_pass_review" if conclusion.get("final_decision") != "keep" else "source_only",
        "intent": str(conclusion.get("reason") or "Pattern lab AI review surfaced a source-only follow-up."),
        "expected_ev_effect": "Improve pattern lab feedback quality without runtime mutation.",
        "evidence": [
            f"review_id={review_id}",
            f"domain={conclusion.get('domain')}",
            f"final_state={final_state}",
            f"final_decision={conclusion.get('final_decision')}",
            f"auditor_pass={conclusion.get('auditor_pass')}",
            f"explicit_gap_type={conclusion.get('explicit_gap_type')}",
            f"source_paths={conclusion.get('source_paths') or []}",
        ],
        "files_likely_touched": [
            "src/engine/pattern_lab_ai_review.py",
            "src/engine/pattern_lab_currentness_audit.py",
            "analysis/gemini_scalping_pattern_lab",
            "analysis/claude_scalping_pattern_lab",
            "analysis/deepseek_swing_pattern_lab",
        ],
        "acceptance_tests": [
            "PYTHONPATH=. .venv/bin/pytest -q src/tests/test_pattern_lab_ai_review.py src/tests/test_pattern_lab_currentness_audit.py",
        ],
        "improvement_type": final_state,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "strategy_effect": False,
        "data_quality_effect": True,
        "tuning_axis_effect": False,
        "next_postclose_metric": f"{REPORT_TYPE}.{review_id}",
        "forbidden_uses": FORBIDDEN_USES,
    }
    if implementation_status:
        order["implementation_status"] = implementation_status
    if implementation_provenance:
        order["implementation_provenance"] = implementation_provenance
    return order


def _implementation_marker_for_conclusion(
    conclusion: dict[str, Any],
    context: dict[str, Any],
) -> tuple[str | None, dict[str, Any] | None]:
    review_id = str(conclusion.get("review_id") or "").strip().lower()
    normalized_review_id = review_id
    order_prefix = f"order_{REPORT_TYPE}_"
    if normalized_review_id.startswith(order_prefix):
        normalized_review_id = normalized_review_id[len(order_prefix) :]
    if review_id == "code_improvement_workorder_duplicate_orders":
        source_summary = _source_summary(context, "code_improvement_workorder")
        nested_summary = _nested_report_summary(source_summary)
        duplicate_warnings = (
            nested_summary.get("duplicate_order_warnings")
            if isinstance(nested_summary.get("duplicate_order_warnings"), list)
            else []
        )
        if duplicate_warnings and str(conclusion.get("final_state") or "") in {"source_quality_gap", "code_patch_required"}:
            return (
                "implemented",
                {
                    "implementation_type": "pattern_lab_code_improvement_workorder_duplicate_warning_provenance",
                    "implemented_scope": (
                        "Code improvement workorder candidate duplicate warnings are surfaced as source-only "
                        "dedupe provenance; final selected order ids remain unique."
                    ),
                    "source_report_type": "code_improvement_workorder",
                    "review_id": review_id,
                    "normalized_review_id": normalized_review_id,
                    "final_state": conclusion.get("final_state"),
                    "final_decision": conclusion.get("final_decision"),
                    "duplicate_order_warning_count": len(duplicate_warnings),
                    "decision_authority": "pattern_lab_ai_review_source_only",
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "requires_separate_runtime_apply_candidate": True,
                    "runtime_mutation_allowed": False,
                    "forbidden_uses": FORBIDDEN_USES,
                    "source_paths": conclusion.get("source_paths") if isinstance(conclusion.get("source_paths"), list) else [],
                    "root_cause_closure_status_hint": "root_cause_closed",
                },
            )
    source_quality_review_ids = {
        "lifecycle_bucket_discovery",
        "pattern_lab_propagation_audit",
        "swing_lifecycle_bucket_discovery",
        "swing_lifecycle_decision_matrix",
        "swing_strategy_discovery_ev",
        "threshold_cycle_ev",
    }
    if (
        normalized_review_id in source_quality_review_ids
        and str(conclusion.get("final_state") or "") in {"source_quality_gap", "code_patch_required"}
    ):
        source_paths = conclusion.get("source_paths") if isinstance(conclusion.get("source_paths"), list) else []
        if source_paths:
            return (
                "implemented",
                {
                    "implementation_type": "pattern_lab_ai_review_source_quality_followup_provenance",
                    "implemented_scope": (
                        "Pattern Lab AI review source-quality follow-up now carries review_id, source paths, "
                        "final decision, gap type, and source-only runtime prohibitions into the workorder surface."
                    ),
                    "source_report_type": "pattern_lab_ai_review",
                    "review_id": review_id,
                    "normalized_review_id": normalized_review_id,
                    "final_state": conclusion.get("final_state"),
                    "final_decision": conclusion.get("final_decision"),
                    "explicit_gap_type": conclusion.get("explicit_gap_type"),
                    "auditor_pass": conclusion.get("auditor_pass"),
                    "decision_authority": "pattern_lab_ai_review_source_only",
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "requires_separate_runtime_apply_candidate": True,
                    "runtime_mutation_allowed": False,
                    "forbidden_uses": FORBIDDEN_USES,
                    "source_paths": source_paths,
                    "root_cause_closure_status_hint": "root_cause_closed",
                },
            )
    if review_id not in {
        "ai_review_gap",
        "swing_lifecycle_bucket_discovery_ai_two_pass_partial",
        "swing_ai_two_pass_review_incomplete",
    }:
        return None, None
    if str(conclusion.get("final_state") or "") != "ai_review_gap":
        return None, None
    source_resolution = (
        conclusion.get("source_context_resolution")
        if isinstance(conclusion.get("source_context_resolution"), dict)
        else {}
    )
    source_summary = (
        source_resolution.get("source_summary")
        if isinstance(source_resolution.get("source_summary"), dict)
        else {}
    )
    if not source_summary:
        source_summary = _swing_lifecycle_bucket_discovery_summary(context)
    nested_source_summary = _nested_report_summary(source_summary)
    if nested_source_summary:
        source_summary = {**nested_source_summary, **source_summary}
    ai_status = str(source_summary.get("ai_two_pass_review_status") or "").strip()
    shard_count = _safe_int(source_summary.get("sim_auto_review_shard_count"), 0)
    reviewed_count = _safe_int(source_summary.get("sim_auto_reviewed_candidate_count"), 0)
    unreviewed_count = _safe_int(source_summary.get("sim_auto_unreviewed_candidate_count"), 0)
    downgraded_count = _safe_int(source_summary.get("sim_auto_downgraded_by_review_count"), 0)
    all_candidate_unreviewed_count = _safe_int(source_summary.get("ai_unreviewed_candidate_count"), 0)
    missing_ai_tier2_proposal_count = _safe_int(source_summary.get("missing_ai_tier2_proposal_count"), 0)
    optional_deferred_candidate_count = _safe_int(source_summary.get("ai_review_optional_deferred_candidate_count"), 0)
    optional_deferred_shard_count = _safe_int(source_summary.get("ai_review_optional_deferred_shard_count"), 0)
    followup_reasons = (
        source_summary.get("ai_review_followup_reasons")
        if isinstance(source_summary.get("ai_review_followup_reasons"), list)
        else []
    )
    if ai_status not in {"partial", "parsed"} or shard_count <= 0 or reviewed_count <= 0:
        return None, None
    return (
        "implemented",
        {
            "implementation_type": (
                "pattern_lab_swing_ai_two_pass_followup_provenance"
                if review_id == "swing_ai_two_pass_review_incomplete"
                else "pattern_lab_swing_generic_ai_gap_two_pass_provenance"
                if review_id == "ai_review_gap"
                else "pattern_lab_swing_bucket_ai_two_pass_partial_provenance"
            ),
            "implemented_scope": (
                "Pattern Lab source-only follow-up now carries the Swing bucket two-pass partial-review "
                "telemetry, deferred broad-candidate review counts, and source paths into the workorder surface."
            ),
            "source_report_type": "swing_lifecycle_bucket_discovery",
            "decision_authority": "pattern_lab_ai_review_source_only",
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "ai_two_pass_review_status": ai_status,
            "sim_auto_review_shard_count": shard_count,
            "sim_auto_reviewed_candidate_count": reviewed_count,
            "sim_auto_unreviewed_candidate_count": unreviewed_count,
            "sim_auto_downgraded_by_review_count": downgraded_count,
            "ai_unreviewed_candidate_count": all_candidate_unreviewed_count,
            "missing_ai_tier2_proposal_count": missing_ai_tier2_proposal_count,
            "ai_review_optional_deferred_candidate_count": optional_deferred_candidate_count,
            "ai_review_optional_deferred_shard_count": optional_deferred_shard_count,
            "ai_review_followup_required": bool(source_summary.get("ai_review_followup_required")),
            "ai_review_followup_reasons": followup_reasons,
            "source_paths": conclusion.get("source_paths") if isinstance(conclusion.get("source_paths"), list) else [],
            "root_cause_closure_status_hint": "root_cause_closed",
        },
    )


def _ai_review_followup_order(*, target_date: str, reasons: list[str], audit: dict[str, Any]) -> dict[str, Any]:
    reason_text = ", ".join(reasons) if reasons else "parsed_review_followup_required"
    return {
        "order_id": f"order_{REPORT_TYPE}_ai_review_followup_{_slug(target_date)}",
        "title": "Resolve Pattern Lab AI review follow-up",
        "source_report_type": REPORT_TYPE,
        "review_id": "ai_review_followup",
        "target_subsystem": "pattern_lab_ai_review",
        "route": "review_ai_output",
        "priority": 2,
        "confidence": "parsed_ai_review_followup",
        "intent": (
            "The AI call parsed, but the reviewer output requires follow-up. "
            "Treat this as source-only workorder input, not an AI transport failure."
        ),
        "expected_ev_effect": "Improve Pattern Lab feedback/source-quality handling without runtime mutation.",
        "evidence": [
            f"ai_review_followup_reason={reason_text}",
            f"audit_status={audit.get('status')}",
            f"audit_issues={audit.get('issues') or []}",
            f"forbidden_use_violations={audit.get('forbidden_use_violations') or []}",
        ],
        "files_likely_touched": [
            "src/engine/pattern_lab_ai_review.py",
            "src/engine/build_code_improvement_workorder.py",
        ],
        "acceptance_tests": [
            "PYTHONPATH=. .venv/bin/pytest -q src/tests/test_pattern_lab_ai_review.py src/tests/test_build_code_improvement_workorder.py",
        ],
        "improvement_type": "ai_review_followup",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "strategy_effect": False,
        "data_quality_effect": True,
        "tuning_axis_effect": False,
        "next_postclose_metric": f"{REPORT_TYPE}.ai_review_followup",
        "forbidden_uses": FORBIDDEN_USES,
        "ai_review_followup_reasons": reasons,
        "ai_review_audit": audit,
    }


def _followup_represented_by_concrete_orders(
    *,
    followup_reasons: list[str],
    audit: dict[str, Any],
    orders: list[dict[str, Any]],
) -> bool:
    if followup_reasons != ["audit_status_correction_required"]:
        return False
    if str(audit.get("status") or "") != "correction_required":
        return False
    forbidden = audit.get("forbidden_use_violations")
    if isinstance(forbidden, list) and forbidden:
        return False
    concrete = [
        order
        for order in orders
        if isinstance(order, dict)
        and str(order.get("improvement_type") or "") != "ai_review_followup"
        and order.get("runtime_effect") is False
        and order.get("allowed_runtime_apply") is False
    ]
    if not concrete:
        return False
    concrete_types = {str(order.get("improvement_type") or "") for order in concrete}
    if not concrete_types & GAP_STATES:
        return False
    return True


def build_pattern_lab_ai_review_report(
    target_date: str,
    *,
    provider: str | None = None,
    ai_raw_response: Any | None = None,
) -> dict[str, Any]:
    target_date = str(target_date).strip()
    resolved_provider = str(
        provider if provider is not None else os.getenv("KORSTOCKSCAN_PATTERN_LAB_AI_REVIEW_PROVIDER", AI_REVIEW_DEFAULT_PROVIDER)
    ).strip().lower() or "none"
    context = _build_input_context(target_date)
    primary_config = _ai_review_config()
    provider_status: dict[str, Any] = {
        "provider": resolved_provider,
        "status": "disabled" if resolved_provider in {"none", "off", "false", "0"} else "not_called",
        "schema_name": AI_REVIEW_SCHEMA_NAME,
        "input_context_hash": _text_hash(context),
        **(primary_config.provider_status_fields() if resolved_provider not in {"none", "off", "false", "0"} else {"model": None}),
        "retry_attempted": False,
    }
    if resolved_provider in {"none", "off", "false", "0"}:
        provider_status.update({"reasoning_effort": None, "timeout_sec": None, "attempt_role": None, "retry_reason": None})
    raw_response = ai_raw_response
    provided_ai_response = raw_response is not None
    if raw_response is not None:
        provider_status["status"] = "provided_response"
    if raw_response is None and resolved_provider == "openai":
        raw_response, provider_status = _call_openai_ai_review(context, config=primary_config)
        provider_status["retry_attempted"] = False
    ai_status, ai_payload, ai_warnings = _parse_ai_review_response(raw_response)
    retry_audit = ai_payload.get("audit") if isinstance(ai_payload.get("audit"), dict) else {}
    retry_forbidden = retry_audit.get("forbidden_use_violations")
    if not isinstance(retry_forbidden, list):
        retry_forbidden = []
    retry_conclusions = ai_payload.get("final_conclusions") if isinstance(ai_payload.get("final_conclusions"), list) else []
    retry_reason = first_wave_retry_reason(
        ai_status=ai_status,
        audit_status=retry_audit.get("status"),
        forbidden_use_violations=retry_forbidden,
        missing_final_conclusion_count=1 if ai_status == "parsed" and not retry_conclusions else 0,
    )
    if retry_reason and resolved_provider == "openai" and not provided_ai_response:
        primary_provider_status = dict(provider_status)
        retry_config = _ai_review_config(attempt_role="retry", retry_reason=retry_reason)
        raw_response, retry_provider_status = _call_openai_ai_review(context, config=retry_config)
        ai_status, ai_payload, ai_warnings = _parse_ai_review_response(raw_response)
        provider_status = {
            **retry_provider_status,
            "retry_attempted": True,
            "primary_attempt": primary_provider_status,
        }
    fallback_used = False
    if ai_status != "parsed":
        fallback_used = True
        ai_payload = _deterministic_two_pass_review(context)
        if resolved_provider in {"none", "off", "false", "0"}:
            ai_status = "disabled_deterministic_review"
        else:
            ai_status = "unavailable_deterministic_review"
    ai_payload = _normalize_empty_audit_correction(
        _apply_feedback_handoff_resolutions(
            _apply_source_contract_resolutions(ai_payload, context),
            context,
        )
    )
    conclusions = (
        ai_payload.get("final_conclusions")
        if isinstance(ai_payload.get("final_conclusions"), list)
        else []
    )
    conclusions = [
        _normalize_final_conclusion(item, context)
        for item in conclusions
        if isinstance(item, dict)
    ]
    ai_payload["final_conclusions"] = conclusions
    ai_payload = _normalize_audit_resolution_fields(ai_payload)
    orders = [
        _order_from_conclusion(item, context)
        for item in conclusions
        if isinstance(item, dict)
        and str(item.get("final_state") or "") in GAP_STATES
        and str(item.get("final_decision") or "") != "keep"
    ]
    audit = ai_payload.get("audit") if isinstance(ai_payload.get("audit"), dict) else {}
    forbidden = audit.get("forbidden_use_violations")
    if not isinstance(forbidden, list):
        forbidden = []
    followup_reasons = parsed_review_followup_reasons(
        ai_status=ai_status,
        audit_status=audit.get("status"),
        forbidden_use_violations=forbidden,
        missing_final_conclusion_count=1 if ai_status == "parsed" and not conclusions else 0,
    )
    generic_followup_resolved = _followup_represented_by_concrete_orders(
        followup_reasons=followup_reasons,
        audit=audit,
        orders=orders,
    )
    if generic_followup_resolved:
        followup_reasons = []
    if followup_reasons and not any(str(order.get("improvement_type") or "") == "ai_review_followup" for order in orders):
        orders.append(_ai_review_followup_order(target_date=target_date, reasons=followup_reasons, audit=audit))
    state_counts = Counter(str(item.get("final_state") or "unknown") for item in conclusions if isinstance(item, dict))
    ai_status_ok = ai_status in {"parsed", "disabled_deterministic_review"}
    status = "warning" if orders or not ai_status_ok or audit.get("status") != "pass" else "pass"
    source_paths = _source_paths(target_date)
    report = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "report_type": REPORT_TYPE,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "runtime_mutation_allowed": False,
        "decision_authority": "pattern_lab_ai_review_source_only",
        "metric_role": "source_quality_gate",
        "window_policy": "same_day_postclose_pattern_lab_feedback_review",
        "sample_floor": "report_only_no_hard_decision",
        "primary_decision_metric": "source_quality_adjusted_ev_pct",
        "source_quality_gate": "pattern_lab_currentness + LDM/threshold feedback re-entry contract",
        "forbidden_uses": FORBIDDEN_USES,
        "feedback_handoff_summary": context.get("feedback_handoff_summary") or {},
        "status": status,
        "sources": {
            label: str(path) if path.exists() else None
            for label, path in source_paths.items()
        },
        "source_context_hash": _text_hash(context),
        "summary": {
            "status": status,
            "ai_two_pass_review_status": ai_status,
            "provider": resolved_provider,
            "model": provider_status.get("model") or (AI_REVIEW_MODEL if resolved_provider == "openai" else None),
            "fallback_used": fallback_used,
            "audit_status": audit.get("status"),
            "ai_review_followup_required": bool(followup_reasons),
            "ai_review_followup_reasons": followup_reasons,
            "generic_ai_review_followup_resolved_by_concrete_orders": generic_followup_resolved,
            "final_conclusion_count": len(conclusions),
            "workorder_count": len(orders),
            "state_counts": dict(state_counts),
            "human_intervention_required": False,
            "feedback_handoff_status": (context.get("feedback_handoff_summary") or {}).get("status"),
            "feedback_handoff_missing_feedback_source_count": (
                context.get("feedback_handoff_summary") or {}
            ).get("missing_feedback_source_count"),
        },
        "ai_two_pass_review": {
            "provider": resolved_provider,
            "status": ai_status,
            "model": provider_status.get("model") or (AI_REVIEW_MODEL if resolved_provider == "openai" else None),
            "model_tier": "tier3" if resolved_provider == "openai" else "deterministic_fallback",
            "schema_name": AI_REVIEW_SCHEMA_NAME,
            "provider_status": provider_status,
            "input_context_hash": _text_hash(context),
            "interpretation": ai_payload.get("interpretation") if isinstance(ai_payload.get("interpretation"), dict) else {},
            "audit": audit,
            "final_conclusions": conclusions,
            "warnings": ai_warnings,
            "followup_required": bool(followup_reasons),
            "followup_reasons": followup_reasons,
        },
        "code_improvement_orders": orders,
    }
    json_path, md_path = report_paths(target_date)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return report


def render_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    review = report.get("ai_two_pass_review") if isinstance(report.get("ai_two_pass_review"), dict) else {}
    audit = review.get("audit") if isinstance(review.get("audit"), dict) else {}
    lines = [
        f"# Pattern Lab AI Review - {report.get('date')}",
        "",
        "## Summary",
        "",
        f"- status: `{report.get('status')}`",
        f"- runtime_effect: `{report.get('runtime_effect')}`",
        f"- allowed_runtime_apply: `{report.get('allowed_runtime_apply')}`",
        f"- decision_authority: `{report.get('decision_authority')}`",
        f"- ai_two_pass_review_status: `{summary.get('ai_two_pass_review_status')}`",
        f"- provider: `{summary.get('provider')}`",
        f"- model: `{summary.get('model') or '-'}`",
        f"- fallback_used: `{summary.get('fallback_used')}`",
        f"- audit_status: `{summary.get('audit_status')}`",
        f"- final_conclusion_count: `{summary.get('final_conclusion_count')}`",
        f"- workorder_count: `{summary.get('workorder_count')}`",
        "",
        "## Two-Pass Review",
        "",
        f"- interpretation_count: `{len(((review.get('interpretation') or {}).get('review_items') or []) if isinstance(review.get('interpretation'), dict) else [])}`",
        f"- audit_issues: `{audit.get('issues') or []}`",
        f"- forbidden_use_violations: `{audit.get('forbidden_use_violations') or []}`",
        f"- source_contract_resolutions: `{audit.get('source_contract_resolutions') or []}`",
        f"- source_context_resolutions: `{audit.get('source_context_resolutions') or []}`",
        "",
        "## Final Conclusions",
        "",
    ]
    for item in (review.get("final_conclusions") or [])[:20]:
        if not isinstance(item, dict):
            continue
        source_resolution = item.get("source_context_resolution")
        contract_resolution = item.get("source_contract_resolution")
        resolution_text = ""
        if isinstance(source_resolution, dict):
            resolution_text = (
                f" source_context_resolution=`{source_resolution.get('status')}` "
                f"contract=`{source_resolution.get('contract_id')}`"
            )
        elif isinstance(contract_resolution, dict):
            resolution_text = (
                f" source_contract_resolution=`{contract_resolution.get('status')}` "
                f"contract=`{contract_resolution.get('contract_id')}`"
            )
        lines.append(
            f"- `{item.get('review_id')}` domain=`{item.get('domain')}` "
            f"state=`{item.get('final_state')}` decision=`{item.get('final_decision')}` "
            f"reason=`{item.get('reason')}`{resolution_text}"
        )
    lines.extend(["", "## Code Improvement Orders", ""])
    for order in report.get("code_improvement_orders") or []:
        if isinstance(order, dict):
            lines.append(f"- `{order.get('order_id')}`: {order.get('title')}")
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    parser.add_argument(
        "--provider",
        default=os.getenv("KORSTOCKSCAN_PATTERN_LAB_AI_REVIEW_PROVIDER", AI_REVIEW_DEFAULT_PROVIDER),
        choices=["openai", "none", "off", "false", "0"],
    )
    args = parser.parse_args(argv)
    report = build_pattern_lab_ai_review_report(args.date, provider=args.provider)
    json_path, md_path = report_paths(args.date)
    print(json.dumps({"status": report.get("status"), "json": str(json_path), "md": str(md_path)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
