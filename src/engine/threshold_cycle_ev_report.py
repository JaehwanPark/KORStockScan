"""Build the daily EV performance report for unattended threshold calibration."""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

from src.engine.daily_threshold_cycle_report import REPORT_DIR
from src.engine.automation.source_quality_clean_baseline import (
    clean_baseline_policy,
    policy_warning_for_date,
)
from src.engine.automation.source_quality_hard_gate import (
    apply_source_quality_preflight_block,
    load_source_quality_preflight,
    source_quality_preflight_blocked,
)
from src.engine.build_code_improvement_workorder import code_improvement_workorder_paths
from src.engine.approval_contracts import annotate_approval_request
from src.engine.institutional_flow_context import report_paths as institutional_flow_report_paths
from src.engine.lifecycle_ai_context import attribution_report_paths as lifecycle_ai_context_attribution_paths
from src.engine.lifecycle_ai_context import context_report_paths as lifecycle_ai_context_report_paths
from src.engine.lifecycle_bucket_discovery import discovery_report_path as lifecycle_bucket_discovery_report_path
from src.engine.lifecycle_decision_matrix import report_paths as lifecycle_matrix_report_paths
from src.engine.scalping.microstructure_reaction_context import report_paths as microstructure_reaction_report_paths
from src.engine.scalping_pattern_lab_automation import automation_report_paths
from src.engine.scalp_entry_action_decision_matrix import report_paths as scalp_entry_adm_report_paths
from src.engine.swing_lifecycle_bucket_discovery import report_paths as swing_lifecycle_bucket_discovery_paths
from src.engine.swing_lifecycle_decision_matrix import report_paths as swing_lifecycle_matrix_paths
from src.engine.swing_strategy_discovery_ev_report import report_paths as swing_strategy_discovery_ev_paths
from src.engine.swing_pattern_lab_automation import swing_pattern_lab_automation_report_paths
from src.engine.threshold_cycle_preopen_apply import apply_manifest_path


MONITOR_SNAPSHOT_DIR = REPORT_DIR / "monitor_snapshots"
CALIBRATION_REPORT_DIR = REPORT_DIR / "threshold_cycle_calibration"
EV_REPORT_DIR = REPORT_DIR / "threshold_cycle_ev"
LATENCY_CLASSIFIER_RECOMMENDATION_DIR = REPORT_DIR / "latency_classifier_recommendation"
PATTERN_LAB_CURRENTNESS_AUDIT_DIR = REPORT_DIR / "pattern_lab_currentness_audit"
PATTERN_LAB_AI_REVIEW_DIR = REPORT_DIR / "pattern_lab_ai_review"
TIME_WINDOW_REGIME_COUNTERFACTUAL_DIR = REPORT_DIR / "time_window_regime_counterfactual"
PRODUCER_GAP_DISCOVERY_DIR = REPORT_DIR / "producer_gap_discovery"
STAGE_HOOK_WORKORDER_DISCOVERY_DIR = REPORT_DIR / "stage_hook_workorder_discovery"
STAGE_HOOK_RUNTIME_SCAFFOLD_DIR = REPORT_DIR / "stage_hook_runtime_scaffold"
PATTERN_LAB_PROPAGATION_AUDIT_DIR = REPORT_DIR / "pattern_lab_propagation_audit"
BUY_FUNNEL_SENTINEL_DIR = REPORT_DIR / "buy_funnel_sentinel"

_JSON_LOAD_DIAGNOSTICS: list[dict[str, Any]] = []


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except Exception as exc:
        _JSON_LOAD_DIAGNOSTICS.append(
            {
                "path": str(path),
                "status": "parse_error",
                "error": str(exc),
            }
        )
        return {}
    if not isinstance(payload, dict):
        _JSON_LOAD_DIAGNOSTICS.append(
            {
                "path": str(path),
                "status": "non_dict_json",
                "type": type(payload).__name__,
            }
        )
        return {}
    return payload if isinstance(payload, dict) else {}


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _top_level_summary(report: dict[str, Any]) -> dict[str, Any]:
    warnings = report.get("warnings") if isinstance(report.get("warnings"), list) else []
    source_quality = (
        report.get("source_quality_preflight_gate")
        if isinstance(report.get("source_quality_preflight_gate"), dict)
        else {}
    )
    daily_ev = report.get("daily_ev_summary") if isinstance(report.get("daily_ev_summary"), dict) else {}
    scalp_sim = report.get("scalp_simulator") if isinstance(report.get("scalp_simulator"), dict) else {}
    lifecycle_discovery = (
        report.get("lifecycle_bucket_discovery")
        if isinstance(report.get("lifecycle_bucket_discovery"), dict)
        else {}
    )
    live_auto_ready = _safe_int(lifecycle_discovery.get("live_auto_apply_ready_count"), 0)
    source_split = daily_ev.get("source_split") if isinstance(daily_ev.get("source_split"), dict) else {}
    real_split = source_split.get("real") if isinstance(source_split.get("real"), dict) else {}
    sim_split = source_split.get("sim") if isinstance(source_split.get("sim"), dict) else {}
    real_sample = _safe_int(daily_ev.get("completed_trades"), 0) or _safe_int(real_split.get("sample"), 0)
    sim_sample = _safe_int(
        scalp_sim.get("completed_count")
        if scalp_sim.get("completed_count") is not None
        else scalp_sim.get("completed"),
        0,
    ) or _safe_int(sim_split.get("sample"), 0)
    if report.get("status"):
        status = str(report.get("status"))
    elif source_quality_preflight_blocked(source_quality):
        status = "source_quality_blocked"
    elif warnings:
        status = "warning"
    else:
        status = "pass"
    if live_auto_ready > 0:
        primary_verdict = "live_auto_candidate_present"
    elif sim_sample > 0:
        primary_verdict = "sim_evidence_present_no_live_bucket"
    else:
        primary_verdict = "hold_sample"
    return {
        "status": status,
        "warning_count": len(warnings),
        "source_quality_status": source_quality.get("status"),
        "source_quality_tuning_input_allowed": source_quality.get("tuning_input_allowed"),
        "real_sample": real_sample,
        "sim_sample": sim_sample,
        "live_auto_ready_count": live_auto_ready,
        "primary_verdict": primary_verdict,
        "runtime_effect": False,
        "decision_authority": "threshold_cycle_ev_summary_report_only",
    }


def ev_report_paths(target_date: str) -> tuple[Path, Path]:
    base = EV_REPORT_DIR / f"threshold_cycle_ev_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def _latency_classifier_recommendation_path(target_date: str) -> Path:
    return LATENCY_CLASSIFIER_RECOMMENDATION_DIR / f"latency_classifier_recommendation_{target_date}.json"


def _latency_classifier_source_metrics(
    target_date: str,
    calibration: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    recommendation = _load_json(_latency_classifier_recommendation_path(target_date))
    candidate = recommendation.get("calibration_candidate") if isinstance(recommendation, dict) else {}
    if isinstance(candidate, dict):
        metrics = candidate.get("source_metrics")
        if isinstance(metrics, dict):
            merged = dict(metrics)
            for key in ("allowed_runtime_apply", "calibration_state", "calibration_reason"):
                if key in candidate and key not in merged:
                    merged[key] = candidate.get(key)
            return merged, recommendation

    for family in ("latency_classifier_runtime_profile", "dynamic_entry_price_resolver", "pre_submit_price_guard"):
        for item in calibration.get("calibration_candidates") or []:
            if isinstance(item, dict) and item.get("family") == family:
                metrics = item.get("source_metrics")
                if isinstance(metrics, dict):
                    merged = dict(metrics)
                    for key in ("allowed_runtime_apply", "calibration_state", "calibration_reason"):
                        if key in item and key not in merged:
                            merged[key] = item.get(key)
                    return merged, recommendation
    return {}, recommendation


def _calibration_path(target_date: str) -> Path:
    return CALIBRATION_REPORT_DIR / f"threshold_cycle_calibration_{target_date}_postclose.json"


def _wait6579_counterfactual_summary(target_date: str) -> tuple[dict[str, Any], str | None]:
    path = MONITOR_SNAPSHOT_DIR / f"wait6579_ev_cohort_{target_date}.json"
    payload = _load_json(path)
    summary = payload.get("counterfactual_summary") if isinstance(payload.get("counterfactual_summary"), dict) else {}
    metrics = payload.get("metrics") if isinstance(payload.get("metrics"), dict) else {}
    approval = payload.get("approval_gate") if isinstance(payload.get("approval_gate"), dict) else {}
    if not payload:
        return {}, None
    if not summary:
        summary = {
            "book": "scalp_score65_74_probe_counterfactual",
            "role": "missed_buy_probe_counterfactual",
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "runtime_effect": "counterfactual_report_only",
            "calibration_authority": "missed_probe_ev_only_not_broker_execution",
            "total_candidates": _safe_int(metrics.get("total_candidates"), 0),
            "score65_74_probe_candidates": _safe_int(metrics.get("score65_74_probe_candidates"), 0),
            "avg_expected_ev_pct": round(_safe_float(metrics.get("avg_expected_ev_pct"), 0.0), 4),
            "expected_ev_krw_sum": _safe_int(metrics.get("expected_ev_krw_sum"), 0),
            "source_authority": "observe_only_threshold_relaxation_input",
            "real_execution_quality_source": "none",
        }
    summary = dict(summary)
    summary["approval_gate"] = {
        "min_sample_gate_passed": bool(approval.get("min_sample_gate_passed")),
        "threshold_relaxation_approved": bool(approval.get("threshold_relaxation_approved")),
        "full_samples": _safe_int(approval.get("full_samples"), 0),
        "partial_samples": _safe_int(approval.get("partial_samples"), 0),
    }
    return summary, str(path)


def _selected_families(apply_manifest: dict[str, Any]) -> list[str]:
    def _dedupe(values: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for value in values:
            if not value or value in seen:
                continue
            seen.add(value)
            result.append(value)
        return result

    merge = apply_manifest.get("operator_runtime_env_merge")
    preserved = []
    if isinstance(merge, dict):
        preserved = [
            str(value)
            for value in (merge.get("preserved_selected_families") or [])
            if str(value or "").strip()
        ]
    selected = apply_manifest.get("auto_apply_selected")
    bridge_selected = ((apply_manifest.get("runtime_apply_bridge") or {}).get("selected") or [])
    if isinstance(selected, list) and selected:
        families = [str(item.get("family") or "") for item in selected if isinstance(item, dict) and item.get("family")]
        swing_selected = ((apply_manifest.get("swing_runtime_approval") or {}).get("selected") or [])
        families.extend(
            str(item.get("family") or "") for item in swing_selected if isinstance(item, dict) and item.get("family")
        )
        families.extend(
            str(item.get("family") or "") for item in bridge_selected if isinstance(item, dict) and item.get("family")
        )
        families.extend(preserved)
        return _dedupe(families)
    swing_selected = ((apply_manifest.get("swing_runtime_approval") or {}).get("selected") or [])
    if isinstance(swing_selected, list) and swing_selected:
        families = [str(item.get("family") or "") for item in swing_selected if isinstance(item, dict) and item.get("family")]
        families.extend(
            str(item.get("family") or "") for item in bridge_selected if isinstance(item, dict) and item.get("family")
        )
        families.extend(preserved)
        return _dedupe(families)
    if isinstance(bridge_selected, list) and bridge_selected:
        families = [str(item.get("family") or "") for item in bridge_selected if isinstance(item, dict) and item.get("family")]
        families.extend(preserved)
        return _dedupe(families)
    if preserved:
        return _dedupe(preserved)
    env_manifest = apply_manifest.get("runtime_env_overrides")
    if isinstance(env_manifest, dict) and env_manifest:
        return ["runtime_env_override"]
    return []


def _swing_runtime_approval_summary(apply_manifest: dict[str, Any]) -> dict[str, Any]:
    swing = apply_manifest.get("swing_runtime_approval") if isinstance(apply_manifest.get("swing_runtime_approval"), dict) else {}
    requests = swing.get("requests") if isinstance(swing.get("requests"), list) else []
    approved = swing.get("approved_requests") if isinstance(swing.get("approved_requests"), list) else []
    selected = swing.get("selected") if isinstance(swing.get("selected"), list) else []
    decisions = swing.get("decisions") if isinstance(swing.get("decisions"), list) else []
    return {
        "request_report": swing.get("request_report"),
        "approval_artifact": swing.get("approval_artifact"),
        "legacy_phase0_real_canary_ignored": bool(swing.get("legacy_phase0_real_canary_ignored")),
        "requested": _safe_int(swing.get("requested"), len(requests)),
        "approved": _safe_int(swing.get("approved"), len(approved)),
        "selected_live_dry_run": len(selected),
        "dry_run_forced": bool(swing.get("dry_run_forced")),
        "source_quality_blocked_families": (
            swing.get("source_quality_blocked_families")
            if isinstance(swing.get("source_quality_blocked_families"), list)
            else []
        ),
        "blocked": list(swing.get("blocked") or []),
        "requests": [
            {
                "approval_id": item.get("approval_id"),
                "family": item.get("family"),
                "stage": item.get("stage"),
                "tradeoff_score": item.get("tradeoff_score"),
                "target_env_keys": item.get("target_env_keys"),
                "recommended_values": item.get("recommended_values"),
            }
            for item in requests
            if isinstance(item, dict)
        ],
        "decisions": decisions,
    }


def _runtime_apply_bridge_summary(apply_manifest: dict[str, Any]) -> dict[str, Any]:
    bridge = apply_manifest.get("runtime_apply_bridge") if isinstance(apply_manifest.get("runtime_apply_bridge"), dict) else {}
    selected = bridge.get("selected") if isinstance(bridge.get("selected"), list) else []
    decisions = bridge.get("decisions") if isinstance(bridge.get("decisions"), list) else []
    return {
        "request_report": bridge.get("request_report"),
        "artifacts": bridge.get("artifacts") or {},
        "candidate_count": _safe_int(bridge.get("candidate_count"), len(bridge.get("candidates") or [])),
        "approved": _safe_int(bridge.get("approved"), len(bridge.get("approved_requests") or [])),
        "selected_count": len(selected),
        "blocked": bridge.get("blocked") or [],
        "selected": [
            {
                "family": item.get("family"),
                "stage": item.get("stage"),
                "approval_id": item.get("approval_id"),
                "runtime_apply_bridge_family": item.get("runtime_apply_bridge_family"),
                "bridge_candidate_id": item.get("bridge_candidate_id"),
                "source_bucket_key": item.get("source_bucket_key"),
                "actual_runtime_effect": item.get("actual_runtime_effect"),
            }
            for item in selected
            if isinstance(item, dict)
        ],
        "decisions": [
            {
                "family": item.get("family"),
                "stage": item.get("stage"),
                "selected": bool(item.get("selected")),
                "decision_reason": item.get("decision_reason"),
                "approval_id": item.get("approval_id"),
                "bridge_candidate_id": item.get("bridge_candidate_id"),
                "actual_runtime_effect": item.get("actual_runtime_effect"),
            }
            for item in decisions
            if isinstance(item, dict)
        ],
    }


def _enrich_swing_micro_source_quality_blockers(blocked: list[Any], ofi_qi_quality: dict[str, Any]) -> list[dict[str, Any]]:
    reason_counts = ofi_qi_quality.get("reason_counts") if isinstance(ofi_qi_quality.get("reason_counts"), dict) else {}
    readiness_counts = {
        "micro_ready_count": _safe_int(ofi_qi_quality.get("micro_ready_count"), 0),
        "micro_insufficient_samples_count": _safe_int(
            ofi_qi_quality.get("micro_insufficient_samples_count"),
            _safe_int(reason_counts.get("micro_not_ready"), 0),
        ),
        "micro_not_ready_count": _safe_int(reason_counts.get("micro_not_ready"), 0),
        "state_insufficient_count": _safe_int(reason_counts.get("state_insufficient"), 0),
    }
    provenance_gap_count = _safe_int(
        ofi_qi_quality.get("provenance_gap_count"),
        _safe_int(reason_counts.get("provenance_gap"), 0),
    )
    wide_spread_count = _safe_int(ofi_qi_quality.get("wide_spread_count"), 0)
    total = max(
        _safe_int(ofi_qi_quality.get("sample_count"), 0),
        sum(_safe_int(value, 0) for value in reason_counts.values()),
        1,
    )
    spread_quality = {
        "wide_spread_threshold_ticks": 10,
        "wide_spread_count": wide_spread_count,
        "wide_spread_rate": round(wide_spread_count * 100.0 / total, 4) if total else 0.0,
        "max_spread_ticks": _safe_float(ofi_qi_quality.get("max_spread_ticks"), None),
        "hard_block": False,
        "decision_use": "source_quality_adjusted_ev_penalty_or_filter_candidate",
    }
    enriched: list[dict[str, Any]] = []
    for item in blocked:
        if not isinstance(item, dict):
            continue
        enriched.append(
            {
                **item,
                "provenance_gap_count": provenance_gap_count,
                "readiness_counts": readiness_counts,
                "spread_quality": spread_quality,
                "source_quality_reason_stage_split": {
                    "micro_missing": _safe_int(reason_counts.get("micro_missing"), 0),
                    "micro_not_ready": _safe_int(reason_counts.get("micro_not_ready"), 0),
                    "state_insufficient": _safe_int(reason_counts.get("state_insufficient"), 0),
                    "observer_unhealthy": _safe_int(reason_counts.get("observer_unhealthy"), 0),
                    "provenance_gap": provenance_gap_count,
                },
            }
        )
    return enriched


def _lifecycle_bucket_discovery_apply_summary(apply_manifest: dict[str, Any]) -> dict[str, Any]:
    payload = (
        apply_manifest.get("lifecycle_bucket_discovery")
        if isinstance(apply_manifest.get("lifecycle_bucket_discovery"), dict)
        else {}
    )
    selected = payload.get("selected") if isinstance(payload.get("selected"), list) else []
    decisions = payload.get("decisions") if isinstance(payload.get("decisions"), list) else []
    return {
        "artifact": payload.get("artifact"),
        "discovery_report": payload.get("discovery_report"),
        "catalog": payload.get("catalog"),
        "approved": _safe_int(payload.get("approved"), 0),
        "selected_count": len(selected),
        "blocked": payload.get("blocked") or [],
        "selected": [
            {
                "family": item.get("family"),
                "stage": item.get("stage"),
                "approval_id": item.get("approval_id"),
                "decision_authority": item.get("decision_authority"),
            }
            for item in selected
            if isinstance(item, dict)
        ],
        "decisions": [
            {
                "family": item.get("family"),
                "stage": item.get("stage"),
                "selected": bool(item.get("selected")),
                "decision_reason": item.get("decision_reason"),
            }
            for item in decisions
            if isinstance(item, dict)
        ],
    }


def _cohort_decisions(calibration_report: dict[str, Any]) -> list[dict[str, Any]]:
    attribution = calibration_report.get("post_apply_attribution")
    attribution = attribution if isinstance(attribution, dict) else {}
    candidates = calibration_report.get("calibration_candidates")
    candidate_by_family = {
        str(item.get("family") or ""): item for item in candidates if isinstance(item, dict) and item.get("family")
    } if isinstance(candidates, list) else {}

    def _prefer_source_count(item_value: Any, source_value: Any) -> Any:
        item_count = _safe_int(item_value, None)
        source_count = _safe_int(source_value, None)
        if item_count is None:
            return source_value
        if item_count == 0 and (source_count or 0) > 0:
            return source_value
        return item_value

    decisions = attribution.get("calibration_decisions")
    if isinstance(decisions, list):
        merged: list[dict[str, Any]] = []
        for item in decisions:
            if not isinstance(item, dict):
                continue
            family = str(item.get("family") or "")
            source = candidate_by_family.get(family) or {}
            merged.append(
                {
                    **item,
                    "sample_count": _prefer_source_count(item.get("sample_count"), source.get("sample_count")),
                    "source_sample_count": _prefer_source_count(
                        item.get("source_sample_count"),
                        source.get("source_sample_count"),
                    ),
                    "sample_floor": _prefer_source_count(item.get("sample_floor"), source.get("sample_floor")),
                    "sample_floor_status": item.get("sample_floor_status") or source.get("sample_floor_status"),
                    "source_metrics": (
                        item.get("source_metrics")
                        if isinstance(item.get("source_metrics"), dict)
                        else source.get("source_metrics")
                        if isinstance(source.get("source_metrics"), dict)
                        else {}
                    ),
                }
            )
        return merged
    if not isinstance(candidates, list):
        return []
    return [
        {
            "family": item.get("family"),
            "calibration_state": item.get("calibration_state"),
            "calibration_reason": item.get("calibration_reason"),
            "sample_count": item.get("sample_count"),
            "sample_floor": item.get("sample_floor"),
        }
        for item in candidates
        if isinstance(item, dict)
    ]


def _approval_requests(calibration_report: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = calibration_report.get("calibration_candidates")
    if not isinstance(candidates, list):
        return []
    requests: list[dict[str, Any]] = []
    source_date = str(calibration_report.get("date") or "").strip() or None
    for item in candidates:
        if not isinstance(item, dict):
            continue
        if not bool(item.get("human_approval_required")):
            continue
        if str(item.get("calibration_state") or "") != "approval_required":
            continue
        requests.append(
            annotate_approval_request(
                {
                    "family": item.get("family"),
                    "stage": item.get("stage"),
                    "calibration_reason": item.get("calibration_reason"),
                    "current_values": item.get("current_values"),
                    "recommended_values": item.get("recommended_values"),
                    "sample_count": item.get("sample_count"),
                    "sample_floor": item.get("sample_floor"),
                },
                source_date,
            )
        )
    return requests


def _pattern_lab_automation_summary(target_date: str) -> tuple[dict[str, Any], str | None, list[str]]:
    json_path, _ = automation_report_paths(target_date)
    payload = _load_json(json_path)
    if not payload:
        return (
            {
                "available": False,
                "artifact": None,
                "gemini_fresh": False,
                "claude_fresh": False,
                "consensus_count": 0,
                "auto_family_candidate_count": 0,
                "code_improvement_order_count": 0,
                "top_consensus_findings": [],
                "top_code_improvement_orders": [],
            },
            None,
            ["pattern_lab_automation_missing"],
        )
    summary = payload.get("ev_report_summary") if isinstance(payload.get("ev_report_summary"), dict) else {}
    warnings: list[str] = []
    gemini_enabled = bool(summary.get("gemini_enabled", True))
    if gemini_enabled and not bool(summary.get("gemini_fresh")):
        warnings.append("pattern_lab_gemini_stale")
    if not bool(summary.get("claude_fresh")):
        warnings.append("pattern_lab_claude_stale")
    return (
        {
            "available": True,
            "artifact": str(json_path),
            "gemini_enabled": gemini_enabled,
            "gemini_fresh": bool(summary.get("gemini_fresh")),
            "gemini_retired_reason": summary.get("gemini_retired_reason"),
            "claude_fresh": bool(summary.get("claude_fresh")),
            "consensus_count": _safe_int(summary.get("consensus_count"), 0),
            "auto_family_candidate_count": _safe_int(summary.get("auto_family_candidate_count"), 0),
            "code_improvement_order_count": _safe_int(summary.get("code_improvement_order_count"), 0),
            "top_consensus_findings": list(summary.get("top_consensus_findings") or [])[:3],
            "top_code_improvement_orders": list(summary.get("top_code_improvement_orders") or [])[:3],
        },
        str(json_path),
        warnings,
    )


def _swing_pattern_lab_automation_summary(target_date: str) -> tuple[dict[str, Any], str | None, list[str]]:
    json_path, _ = swing_pattern_lab_automation_report_paths(target_date)
    payload = _load_json(json_path)
    if not payload:
        return (
            {
                "available": False,
                "artifact": None,
                "findings_count": 0,
                "code_improvement_order_count": 0,
                "data_quality_warning_count": 0,
                "carryover_warning_count": 0,
                "population_split_available": False,
                "top_findings": [],
                "top_orders": [],
            },
            None,
            ["swing_pattern_lab_automation_missing"],
        )
    summary = payload.get("ev_report_summary") if isinstance(payload.get("ev_report_summary"), dict) else {}
    data_quality = payload.get("data_quality") if isinstance(payload.get("data_quality"), dict) else {}
    source_quality_blocked_families = (
        summary.get("source_quality_blocked_families")
        if isinstance(summary.get("source_quality_blocked_families"), list)
        else data_quality.get("source_quality_blocked_families")
        if isinstance(data_quality.get("source_quality_blocked_families"), list)
        else []
    )
    ofi_qi_quality = data_quality.get("ofi_qi_quality") if isinstance(data_quality.get("ofi_qi_quality"), dict) else {}
    source_quality_blocked_families = _enrich_swing_micro_source_quality_blockers(
        source_quality_blocked_families,
        ofi_qi_quality,
    )
    warnings: list[str] = []
    resolved_dq_warnings: list[str] = []
    dq_warnings = data_quality.get("warnings", [])
    if dq_warnings:
        for warning in dq_warnings if isinstance(dq_warnings, list) else []:
            warning_text = str(warning)
            if warning_text.startswith("OFI/QI stale/missing ratio:") and source_quality_blocked_families:
                resolved_dq_warnings.append(warning_text)
                continue
            warnings.append(f"swing_lab_dq:{warning_text}")
    if summary.get("stale_reason"):
        warnings.append(f"swing_lab_stale:{summary['stale_reason']}")
    carryover_count = _safe_int(summary.get("carryover_warning_count"), 0)
    if carryover_count > 0:
        warnings.append(f"swing_lab_carryover:{carryover_count}")
    return (
        {
            "available": True,
            "artifact": str(json_path),
            "deepseek_lab_available": bool(summary.get("deepseek_lab_available")),
            "findings_count": _safe_int(summary.get("findings_count"), 0),
            "code_improvement_order_count": _safe_int(summary.get("code_improvement_order_count"), 0),
            "data_quality_warning_count": _safe_int(summary.get("data_quality_warning_count"), 0),
            "top_level_data_quality_warning_count": len(warnings),
            "resolved_data_quality_warnings": resolved_dq_warnings,
            "resolved_data_quality_warning_count": len(resolved_dq_warnings),
            "ofi_qi_quality": ofi_qi_quality,
            "source_quality_blocked_families": source_quality_blocked_families,
            "carryover_warning_count": carryover_count,
            "population_split_available": bool(summary.get("population_split_available")),
            "top_findings": [
                {
                    "finding_id": item.get("finding_id"),
                    "title": item.get("title"),
                    "route": item.get("route"),
                }
                for item in (payload.get("consensus_findings") or [])[:3]
                if isinstance(item, dict)
            ],
            "top_orders": [
                {
                    "order_id": item.get("order_id"),
                    "title": item.get("title"),
                    "decision": item.get("decision"),
                }
                for item in (payload.get("code_improvement_orders") or [])[:3]
                if isinstance(item, dict)
            ],
        },
        str(json_path),
        warnings,
    )


def _code_improvement_workorder_summary(target_date: str) -> tuple[dict[str, Any], str | None, list[str]]:
    json_path, md_path = code_improvement_workorder_paths(target_date)
    payload = _load_json(json_path)
    if not payload:
        return (
            {
                "available": False,
                "artifact": None,
                "markdown": str(md_path) if md_path.exists() else None,
                "selected_order_count": 0,
                "decision_counts": {},
                "top_orders": [],
            },
            None,
            ["code_improvement_workorder_missing"],
        )
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    orders = payload.get("orders") if isinstance(payload.get("orders"), list) else []
    return (
        {
            "available": True,
            "artifact": str(json_path),
            "markdown": str(md_path) if md_path.exists() else None,
            "selected_order_count": _safe_int(summary.get("selected_order_count"), 0),
            "decision_counts": summary.get("decision_counts") if isinstance(summary.get("decision_counts"), dict) else {},
            "entry_submit_drought_selected": bool(summary.get("entry_submit_drought_selected")),
            "entry_submit_drought_handoff_missing": bool(summary.get("entry_submit_drought_handoff_missing")),
            "orders": [
                {"order_id": item.get("order_id"), "decision": item.get("decision")}
                for item in orders
                if isinstance(item, dict)
            ],
            "top_orders": [
                {
                    "order_id": item.get("order_id"),
                    "decision": item.get("decision"),
                    "target_subsystem": item.get("target_subsystem"),
                }
                for item in orders[:3]
                if isinstance(item, dict)
            ],
        },
        str(json_path),
        [],
    )


def _scalp_entry_adm_summary(target_date: str) -> tuple[dict[str, Any], str | None, list[str]]:
    json_path, _ = scalp_entry_adm_report_paths(target_date)
    payload = _load_json(json_path)
    if not payload:
        return (
            {
                "available": False,
                "artifact": None,
                "status": "missing",
                "total_candidates": 0,
                "joined_sample": 0,
                "sample_floor": 20,
                "missing_actions": [],
                "zero_sample_actions": [],
                "prompt_applied_count": 0,
                "runtime_bias_applied_count": 0,
                "runtime_effect_counts": {},
                "forced_action_counts": {},
                "raw_action_counts": {},
                "action_normalized_count": 0,
                "action_normalization_counts": {},
                "top_actions": [],
                "runtime_effect": False,
                "decision_authority": "entry_advisory_prompt_context_only",
            },
            None,
            ["scalp_entry_action_decision_matrix_missing"],
        )
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    action_summary = payload.get("action_summary") if isinstance(payload.get("action_summary"), list) else []
    unknown_bucket_summary = (
        summary.get("unknown_bucket_summary")
        if isinstance(summary.get("unknown_bucket_summary"), dict)
        else {}
    )
    warnings = [f"scalp_entry_adm:{item}" for item in (payload.get("warnings") or []) if str(item)]
    return (
        {
            "available": True,
            "artifact": str(json_path),
            "status": payload.get("status"),
            "runtime_effect": bool(payload.get("runtime_effect")),
            "decision_authority": payload.get("decision_authority"),
            "application_mode": payload.get("application_mode"),
            "primary_decision_metric": payload.get("primary_decision_metric"),
            "total_candidates": _safe_int(summary.get("total_candidates"), 0),
            "joined_sample": _safe_int(summary.get("joined_sample"), 0),
            "sample_floor": _safe_int(summary.get("sample_floor"), 20),
            "missing_actions": summary.get("missing_actions") if isinstance(summary.get("missing_actions"), list) else [],
            "zero_sample_actions": summary.get("zero_sample_actions")
            if isinstance(summary.get("zero_sample_actions"), list)
            else [],
            "prompt_applied_count": _safe_int(summary.get("prompt_applied_count"), 0),
            "runtime_bias_applied_count": _safe_int(summary.get("runtime_bias_applied_count"), 0),
            "runtime_effect_counts": summary.get("runtime_effect_counts")
            if isinstance(summary.get("runtime_effect_counts"), dict)
            else {},
            "forced_action_counts": summary.get("forced_action_counts")
            if isinstance(summary.get("forced_action_counts"), dict)
            else {},
            "raw_action_counts": summary.get("raw_action_counts")
            if isinstance(summary.get("raw_action_counts"), dict)
            else {},
            "action_normalized_count": _safe_int(summary.get("action_normalized_count"), 0),
            "action_normalization_counts": summary.get("action_normalization_counts")
            if isinstance(summary.get("action_normalization_counts"), dict)
            else {},
            "unknown_bucket_summary": unknown_bucket_summary,
            "top_actions": [
                {
                    "action": item.get("action"),
                    "sample_count": item.get("sample_count"),
                    "joined_sample": item.get("joined_sample"),
                    "source_quality_adjusted_ev_pct": item.get("source_quality_adjusted_ev_pct"),
                }
                for item in action_summary
                if isinstance(item, dict) and _safe_int(item.get("sample_count"), 0) > 0
            ][:5],
        },
        str(json_path),
        warnings,
    )


def _lifecycle_decision_matrix_summary(target_date: str) -> tuple[dict[str, Any], str | None, list[str]]:
    json_path, _ = lifecycle_matrix_report_paths(target_date)
    payload = _load_json(json_path)
    if not payload:
        return (
            {
                "available": False,
                "artifact": None,
                "status": "missing",
                "total_rows": 0,
                "joined_rows": 0,
                "policy_pass_count": 0,
                "promote_ready_count": 0,
                "fixed_threshold_roles": {},
                "runtime_effect": False,
            },
            None,
            ["lifecycle_decision_matrix_missing"],
        )
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    contract = payload.get("fixed_threshold_contract") if isinstance(payload.get("fixed_threshold_contract"), dict) else {}
    entry_bucket = (
        payload.get("entry_bucket_attribution")
        if isinstance(payload.get("entry_bucket_attribution"), dict)
        else {}
    )
    submit_bucket = (
        payload.get("submit_bucket_attribution")
        if isinstance(payload.get("submit_bucket_attribution"), dict)
        else {}
    )
    holding_bucket = (
        payload.get("holding_bucket_attribution")
        if isinstance(payload.get("holding_bucket_attribution"), dict)
        else {}
    )
    exit_bucket = (
        payload.get("exit_bucket_attribution")
        if isinstance(payload.get("exit_bucket_attribution"), dict)
        else {}
    )
    lifecycle_flow_bucket = (
        payload.get("lifecycle_flow_bucket_attribution")
        if isinstance(payload.get("lifecycle_flow_bucket_attribution"), dict)
        else {}
    )
    scale_in_bucket = (
        payload.get("scale_in_bucket_attribution")
        if isinstance(payload.get("scale_in_bucket_attribution"), dict)
        else {}
    )
    entry_summary = entry_bucket.get("summary") if isinstance(entry_bucket.get("summary"), dict) else {}
    submit_summary = submit_bucket.get("summary") if isinstance(submit_bucket.get("summary"), dict) else {}
    holding_summary = holding_bucket.get("summary") if isinstance(holding_bucket.get("summary"), dict) else {}
    exit_summary = exit_bucket.get("summary") if isinstance(exit_bucket.get("summary"), dict) else {}
    lifecycle_flow_summary = (
        lifecycle_flow_bucket.get("summary")
        if isinstance(lifecycle_flow_bucket.get("summary"), dict)
        else {}
    )
    scale_in_summary = scale_in_bucket.get("summary") if isinstance(scale_in_bucket.get("summary"), dict) else {}
    warnings = [f"lifecycle_decision_matrix:{item}" for item in (payload.get("warnings") or []) if str(item)]
    return (
        {
            "available": True,
            "artifact": str(json_path),
            "status": summary.get("status"),
            "matrix_version": payload.get("matrix_version"),
            "runtime_effect": bool(payload.get("runtime_effect")),
            "decision_authority": payload.get("decision_authority"),
            "primary_decision_metric": payload.get("primary_decision_metric"),
            "total_rows": _safe_int(summary.get("total_rows"), 0),
            "joined_rows": _safe_int(summary.get("joined_rows"), 0),
            "policy_pass_count": _safe_int(summary.get("policy_pass_count"), 0),
            "promote_ready_count": _safe_int(summary.get("promote_ready_count"), 0),
            "lifecycle_flow_bucket_count": _safe_int(
                summary.get("lifecycle_flow_bucket_count"),
                _safe_int(lifecycle_flow_summary.get("bucket_count"), 0),
            ),
            "lifecycle_flow_complete_count": _safe_int(
                summary.get("lifecycle_flow_complete_count"),
                _safe_int(lifecycle_flow_summary.get("complete_flow_count"), 0),
            ),
            "complete_flow_count": _safe_int(
                summary.get("complete_flow_count"),
                _safe_int(lifecycle_flow_summary.get("complete_flow_count"), 0),
            ),
            "incomplete_flow_count": _safe_int(
                summary.get("incomplete_flow_count"),
                _safe_int(lifecycle_flow_summary.get("incomplete_flow_count"), 0),
            ),
            "lifecycle_flow_runtime_candidate_count": _safe_int(
                summary.get("lifecycle_flow_runtime_candidate_count"),
                _safe_int(lifecycle_flow_summary.get("runtime_candidate_count"), 0),
            ),
            "lifecycle_flow_workorder_count": _safe_int(
                summary.get("lifecycle_flow_workorder_count"),
                _safe_int(lifecycle_flow_summary.get("workorder_count"), 0),
            ),
            "lifecycle_flow_runtime_approval_candidates": (
                lifecycle_flow_bucket.get("runtime_approval_candidates")
                if isinstance(lifecycle_flow_bucket.get("runtime_approval_candidates"), list)
                else []
            ),
            "lifecycle_flow_code_improvement_workorders": (
                lifecycle_flow_bucket.get("code_improvement_workorders")
                if isinstance(lifecycle_flow_bucket.get("code_improvement_workorders"), list)
                else []
            ),
            "submit_bucket_attribution_summary": submit_summary,
            "entry_bucket_attribution_summary": entry_summary,
            "entry_bucket_runtime_approval_candidates": (
                entry_bucket.get("runtime_approval_candidates")
                if isinstance(entry_bucket.get("runtime_approval_candidates"), list)
                else []
            ),
            "entry_bucket_code_improvement_workorders": (
                entry_bucket.get("code_improvement_workorders")
                if isinstance(entry_bucket.get("code_improvement_workorders"), list)
                else []
            ),
            "entry_bucket_runtime_candidate_count": _safe_int(
                summary.get("entry_bucket_runtime_candidate_count"),
                _safe_int(entry_summary.get("runtime_candidate_count"), 0),
            ),
            "entry_bucket_workorder_count": _safe_int(
                summary.get("entry_bucket_workorder_count"),
                _safe_int(entry_summary.get("workorder_count"), 0),
            ),
            "submit_bucket_runtime_approval_candidates": (
                submit_bucket.get("runtime_approval_candidates")
                if isinstance(submit_bucket.get("runtime_approval_candidates"), list)
                else []
            ),
            "submit_bucket_code_improvement_workorders": (
                submit_bucket.get("code_improvement_workorders")
                if isinstance(submit_bucket.get("code_improvement_workorders"), list)
                else []
            ),
            "post_submit_contract_gaps": (
                submit_bucket.get("post_submit_contract_gaps")
                if isinstance(submit_bucket.get("post_submit_contract_gaps"), list)
                else []
            ),
            "submit_bucket_workorder_count": _safe_int(summary.get("submit_bucket_workorder_count"), 0),
            "submit_bucket_contract_gap_count": _safe_int(summary.get("submit_bucket_contract_gap_count"), 0),
            "holding_bucket_attribution_summary": holding_summary,
            "holding_bucket_code_improvement_workorders": (
                holding_bucket.get("code_improvement_workorders")
                if isinstance(holding_bucket.get("code_improvement_workorders"), list)
                else []
            ),
            "holding_bucket_count": _safe_int(
                summary.get("holding_bucket_count"),
                _safe_int(holding_summary.get("bucket_count"), 0),
            ),
            "holding_bucket_workorder_count": _safe_int(
                summary.get("holding_bucket_workorder_count"),
                _safe_int(holding_summary.get("workorder_count"), 0),
            ),
            "exit_bucket_attribution_summary": exit_summary,
            "exit_bucket_code_improvement_workorders": (
                exit_bucket.get("code_improvement_workorders")
                if isinstance(exit_bucket.get("code_improvement_workorders"), list)
                else []
            ),
            "exit_bucket_count": _safe_int(
                summary.get("exit_bucket_count"),
                _safe_int(exit_summary.get("bucket_count"), 0),
            ),
            "exit_bucket_workorder_count": _safe_int(
                summary.get("exit_bucket_workorder_count"),
                _safe_int(exit_summary.get("workorder_count"), 0),
            ),
            "scale_in_bucket_attribution_summary": scale_in_summary,
            "scale_in_bucket_runtime_approval_candidates": (
                scale_in_bucket.get("runtime_approval_candidates")
                if isinstance(scale_in_bucket.get("runtime_approval_candidates"), list)
                else []
            ),
            "scale_in_bucket_code_improvement_workorders": (
                scale_in_bucket.get("code_improvement_workorders")
                if isinstance(scale_in_bucket.get("code_improvement_workorders"), list)
                else []
            ),
            "scale_in_bucket_runtime_candidate_count": _safe_int(
                summary.get("scale_in_bucket_runtime_candidate_count"),
                _safe_int(scale_in_summary.get("runtime_candidate_count"), 0),
            ),
            "scale_in_bucket_workorder_count": _safe_int(
                summary.get("scale_in_bucket_workorder_count"),
                _safe_int(scale_in_summary.get("workorder_count"), 0),
            ),
            "identity_missing_count": _safe_int(summary.get("identity_missing_count"), 0),
            "identity_join_rate": summary.get("identity_join_rate"),
            "complete_flow_rate": summary.get("complete_flow_rate"),
            "join_contract_blocked": bool(summary.get("join_contract_blocked") or lifecycle_flow_summary.get("join_contract_blocked")),
            "bundle_ev_tuning_state": (
                summary.get("bundle_ev_tuning_state")
                or lifecycle_flow_summary.get("bundle_ev_tuning_state")
                or "ready_for_bundle_ev_tuning"
            ),
            "top_incomplete_reason": summary.get("top_incomplete_reason") or lifecycle_flow_summary.get("top_incomplete_reason"),
            "incomplete_flow_reason_counts": summary.get("incomplete_flow_reason_counts") or {},
            "policy_entries": [
                {
                    "stage": item.get("stage"),
                    "sample": item.get("sample"),
                    "joined_sample": item.get("joined_sample"),
                    "stage_ev_composite_pct": item.get("stage_ev_composite_pct"),
                    "confidence": item.get("confidence"),
                    "selected_action": item.get("selected_action"),
                    "source_quality_gate": item.get("source_quality_gate"),
                    "promote_ready": item.get("promote_ready"),
                }
                for item in (payload.get("policy_entries") or [])[:5]
                if isinstance(item, dict)
            ],
            "fixed_threshold_roles": contract.get("roles") if isinstance(contract.get("roles"), dict) else {},
        },
        str(json_path),
        warnings,
    )


def _buy_funnel_sentinel_summary(target_date: str) -> tuple[dict[str, Any], str | None, list[str]]:
    path = BUY_FUNNEL_SENTINEL_DIR / f"buy_funnel_sentinel_{target_date}.json"
    payload = _load_json(path)
    if not payload:
        return (
            {
                "available": False,
                "artifact": None,
                "primary": None,
                "matches": [],
                "entry_submit_drought_contract": {},
            },
            None,
            ["buy_funnel_sentinel_missing"],
        )
    classification = payload.get("classification") if isinstance(payload.get("classification"), dict) else {}
    contract = (
        payload.get("entry_submit_drought_contract")
        if isinstance(payload.get("entry_submit_drought_contract"), dict)
        else {}
    )
    return (
        {
            "available": True,
            "artifact": str(path),
            "primary": classification.get("primary"),
            "matches": classification.get("matches") if isinstance(classification.get("matches"), list) else [],
            "entry_submit_drought_contract": contract,
            "weak_contract_matches": contract.get("weak_contract_matches") if isinstance(contract.get("weak_contract_matches"), list) else [],
            "runtime_effect": False,
            "allowed_runtime_apply": False,
        },
        str(path),
        [],
    )


def _lifecycle_ai_context_summary(target_date: str) -> tuple[dict[str, Any], str | None, list[str]]:
    json_path, _ = lifecycle_ai_context_report_paths(target_date)
    payload = _load_json(json_path)
    if not payload:
        return (
            {
                "available": False,
                "artifact": None,
                "context_version": "-",
                "prompt_stage_count": 0,
                "runtime_effect": False,
                "decision_authority": "ai_advisory_prompt_context_only",
            },
            None,
            ["lifecycle_ai_context_missing"],
        )
    stages = payload.get("stage_contexts") if isinstance(payload.get("stage_contexts"), list) else []
    warnings = [f"lifecycle_ai_context:{item}" for item in (payload.get("warnings") or []) if str(item)]
    return (
        {
            "available": True,
            "artifact": str(json_path),
            "context_version": payload.get("context_version"),
            "runtime_effect": bool(payload.get("runtime_effect")),
            "decision_authority": payload.get("decision_authority"),
            "provider_status": payload.get("provider_status") if isinstance(payload.get("provider_status"), dict) else {},
            "prompt_stage_count": sum(1 for item in stages if isinstance(item, dict) and item.get("prompt_injection_allowed")),
            "stage_contexts": [
                {
                    "stage": item.get("stage"),
                    "prompt_injection_allowed": item.get("prompt_injection_allowed"),
                    "policy_key": item.get("policy_key"),
                    "alignment_hint": item.get("alignment_hint"),
                    "context_contribution_score": item.get("context_contribution_score"),
                    "attribution_quality_status": item.get("attribution_quality_status"),
                }
                for item in stages[:5]
                if isinstance(item, dict)
            ],
        },
        str(json_path),
        warnings,
    )


def _lifecycle_ai_context_attribution_summary(target_date: str) -> tuple[dict[str, Any], str | None, list[str]]:
    json_path, _ = lifecycle_ai_context_attribution_paths(target_date)
    payload = _load_json(json_path)
    if not payload:
        return (
            {
                "available": False,
                "artifact": None,
                "context_eligible_count": 0,
                "context_applied_count": 0,
                "runtime_effect": False,
                "decision_authority": "postclose_context_attribution_only",
            },
            None,
            ["lifecycle_ai_context_attribution_missing"],
        )
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    warnings = [f"lifecycle_ai_context_attribution:{item}" for item in (payload.get("warnings") or []) if str(item)]
    stage_map = payload.get("stage_attribution") if isinstance(payload.get("stage_attribution"), dict) else {}
    return (
        {
            "available": True,
            "artifact": str(json_path),
            "runtime_effect": bool(payload.get("runtime_effect")),
            "decision_authority": payload.get("decision_authority"),
            "implementation_status": payload.get("implementation_status"),
            "implementation_checks": payload.get("implementation_checks") or [],
            "implementation_provenance": payload.get("implementation_provenance") or {},
            "context_eligible_count": _safe_int(summary.get("context_eligible_count"), 0),
            "context_applied_count": _safe_int(summary.get("context_applied_count"), 0),
            "context_skipped_count": _safe_int(summary.get("context_skipped_count"), 0),
            "replay_budget": _safe_int(summary.get("replay_budget"), 0),
            "stage_quality_counts": summary.get("stage_quality_counts") or {},
            "stage_attribution": {
                stage: {
                    "context_contribution_score": item.get("context_contribution_score"),
                    "bounded_auxiliary_weight": item.get("bounded_auxiliary_weight"),
                    "attribution_quality_status": item.get("attribution_quality_status"),
                    "source_quality_adjusted_ev_pct": item.get("source_quality_adjusted_ev_pct"),
                    "ai_action_alignment_rate": item.get("ai_action_alignment_rate"),
                    "no_context_replay_observed": item.get("no_context_replay_observed"),
                }
                for stage, item in stage_map.items()
                if isinstance(item, dict)
            },
        },
        str(json_path),
        warnings,
    )


def _swing_strategy_discovery_summary(target_date: str) -> tuple[dict[str, Any], str | None, list[str]]:
    json_path, _ = swing_strategy_discovery_ev_paths(target_date)
    payload = _load_json(json_path)
    if not payload:
        return (
            {
                "available": False,
                "artifact": None,
                "candidate_count": 0,
                "arm_count": 0,
                "labeled_sample_count": 0,
                "pending_future_quote_count": 0,
                "top_surviving_arm": None,
                "avoid_bucket_count": 0,
                "runtime_effect": False,
                "decision_authority": "swing_sim_exploration_only",
            },
            None,
            ["swing_strategy_discovery_ev_missing"],
        )
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    source_quality = (
        payload.get("source_quality_summary") if isinstance(payload.get("source_quality_summary"), dict) else {}
    )
    warnings = [f"swing_strategy_discovery:{item}" for item in (payload.get("warnings") or []) if str(item)]
    return (
        {
            "available": True,
            "artifact": str(json_path),
            "candidate_count": _safe_int(summary.get("candidate_count"), 0),
            "arm_count": _safe_int(summary.get("arm_count"), 0),
            "policy_exit_row_count": _safe_int(summary.get("policy_exit_row_count"), 0),
            "labeled_sample_count": _safe_int(summary.get("labeled_sample_count"), 0),
            "pending_future_quote_count": _safe_int(summary.get("pending_future_quote_count"), 0),
            "top_surviving_arm": summary.get("top_surviving_arm"),
            "surviving_arm_count": _safe_int(summary.get("surviving_arm_count"), 0),
            "avoid_bucket_count": _safe_int(summary.get("avoid_bucket_count"), 0),
            "runtime_effect": bool(payload.get("runtime_effect")),
            "source_only": bool(payload.get("source_only", True)),
            "decision_authority": payload.get("decision_authority"),
            "source_quality_summary": source_quality,
            "implementation_status": source_quality.get("implementation_status"),
            "implementation_checks": source_quality.get("implementation_checks") or [],
            "implementation_provenance": source_quality.get("implementation_provenance") or {},
        },
        str(json_path),
        warnings,
    )


def _swing_lifecycle_matrix_summary(target_date: str) -> tuple[dict[str, Any], str | None, list[str]]:
    json_path, _ = swing_lifecycle_matrix_paths(target_date)
    payload = _load_json(json_path)
    if not payload:
        return (
            {
                "available": False,
                "artifact": None,
                "total_rows": 0,
                "probe_rows": 0,
                "discovery_rows": 0,
                "sim_auto_candidate_count": 0,
                "workorder_count": 0,
                "raw_swing_event_count": 0,
                "ldm_consumed_event_count": 0,
                "ldm_event_coverage_rate": 0.0,
                "unmapped_swing_stage_counts": {},
                "daily_simulation_consumed": False,
                "runtime_effect": False,
                "decision_authority": "swing_ldm_source_only",
            },
            None,
            ["swing_lifecycle_decision_matrix_missing"],
        )
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    entry_bottleneck = payload.get("swing_entry_bottleneck") if isinstance(payload.get("swing_entry_bottleneck"), dict) else {}
    warnings = [f"swing_lifecycle_decision_matrix:{item}" for item in (payload.get("warnings") or []) if str(item)]
    candidate_ids: list[str] = []
    workorder_ids: list[str] = []
    for section_name in (
        "swing_lifecycle_flow_bucket_attribution",
        "entry_bucket_attribution",
        "holding_exit_bucket_attribution",
        "scale_in_bucket_attribution",
        "discovery_arm_attribution",
    ):
        section = payload.get(section_name) if isinstance(payload.get(section_name), dict) else {}
        for item in section.get("sim_auto_approval_candidates") or section.get("runtime_approval_candidates") or []:
            if isinstance(item, dict) and item.get("candidate_id"):
                candidate_ids.append(str(item.get("candidate_id")))
        for item in section.get("code_improvement_workorders") or []:
            if isinstance(item, dict) and (item.get("workorder_id") or item.get("bucket_key")):
                workorder_ids.append(str(item.get("workorder_id") or item.get("bucket_key")))
    return (
        {
            "available": True,
            "artifact": str(json_path),
            "matrix_version": payload.get("matrix_version"),
            "runtime_effect": bool(payload.get("runtime_effect")),
            "source_only": bool(payload.get("source_only", True)),
            "decision_authority": payload.get("decision_authority"),
            "total_rows": _safe_int(summary.get("total_rows"), 0),
            "probe_rows": _safe_int(summary.get("probe_rows"), 0),
            "discovery_rows": _safe_int(summary.get("discovery_rows"), 0),
            "labeled_rows": _safe_int(summary.get("labeled_rows"), 0),
            "pending_future_quote_count": _safe_int(summary.get("pending_future_quote_count"), 0),
            "swing_lifecycle_flow_bucket_count": _safe_int(summary.get("swing_lifecycle_flow_bucket_count"), 0),
            "complete_flow_count": _safe_int(summary.get("complete_flow_count"), 0),
            "incomplete_flow_count": _safe_int(summary.get("incomplete_flow_count"), 0),
            "identity_join_rate": summary.get("identity_join_rate"),
            "complete_flow_rate": summary.get("complete_flow_rate"),
            "join_contract_blocked": bool(summary.get("join_contract_blocked")),
            "sim_auto_candidate_count": _safe_int(summary.get("sim_auto_candidate_count"), 0),
            "workorder_count": _safe_int(summary.get("workorder_count"), 0),
            "raw_swing_event_count": _safe_int(summary.get("raw_swing_event_count"), 0),
            "ldm_consumed_event_count": _safe_int(summary.get("ldm_consumed_event_count"), 0),
            "ldm_event_coverage_rate": summary.get("ldm_event_coverage_rate"),
            "unmapped_swing_stage_counts": summary.get("unmapped_swing_stage_counts")
            if isinstance(summary.get("unmapped_swing_stage_counts"), dict)
            else {},
            "daily_simulation_consumed": bool(summary.get("daily_simulation_consumed")),
            "swing_entry_bottleneck_primary": summary.get("swing_entry_bottleneck_primary")
            or entry_bottleneck.get("primary"),
            "swing_lifecycle_contract_gap_count": _safe_int(summary.get("swing_lifecycle_contract_gap_count"), 0),
            "stage_counts": summary.get("stage_counts") if isinstance(summary.get("stage_counts"), dict) else {},
            "source_book_counts": summary.get("source_book_counts")
            if isinstance(summary.get("source_book_counts"), dict)
            else {},
            "sim_auto_candidate_ids": sorted(set(candidate_ids)),
            "workorder_ids": sorted(set(workorder_ids)),
        },
        str(json_path),
        warnings,
    )


def _swing_lifecycle_bucket_discovery_summary(target_date: str) -> tuple[dict[str, Any], str | None, list[str]]:
    json_path, _ = swing_lifecycle_bucket_discovery_paths(target_date)
    payload = _load_json(json_path)
    if not payload:
        return (
            {
                "available": False,
                "artifact": None,
                "candidate_count": 0,
                "surfaced_candidate_count": 0,
                "sim_auto_approved_count": 0,
                "code_patch_required_count": 0,
                "runtime_effect": False,
                "decision_authority": "swing_ldm_bucket_discovery_sim_auto",
            },
            None,
            ["swing_lifecycle_bucket_discovery_missing"],
        )
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    warnings = [f"swing_lifecycle_bucket_discovery:{item}" for item in (payload.get("warnings") or []) if str(item)]
    ai_review_status = str(summary.get("ai_two_pass_review_status") or "").strip()
    if ai_review_status and ai_review_status != "parsed":
        warnings.append(f"swing_lifecycle_bucket_discovery:ai_two_pass_review_{ai_review_status}_fail_closed")
    if bool(summary.get("ai_fail_closed")):
        warnings.append("swing_lifecycle_bucket_discovery:ai_two_pass_review_fail_closed_sim_auto_blocked")
    if bool(summary.get("ai_review_followup_required")):
        warnings.append("swing_lifecycle_bucket_discovery:ai_review_followup_required")
    if bool(summary.get("sim_auto_blocked_by_ai_review_followup")):
        warnings.append("swing_lifecycle_bucket_discovery:ai_review_followup_sim_auto_blocked")
    warnings = list(dict.fromkeys(warnings))
    return (
        {
            "available": True,
            "artifact": str(json_path),
            "runtime_effect": bool(payload.get("runtime_effect")),
            "source_only": bool(payload.get("source_only", True)),
            "decision_authority": payload.get("decision_authority"),
            "source_contract_status": summary.get("source_contract_status"),
            "ai_two_pass_review_status": ai_review_status or None,
            "ai_fail_closed": bool(summary.get("ai_fail_closed")),
            "ai_review_blocker_state": summary.get("ai_review_blocker_state"),
            "pre_review_sim_auto_candidate_count": _safe_int(summary.get("pre_review_sim_auto_candidate_count"), 0),
            "sim_auto_reviewed_candidate_count": _safe_int(summary.get("sim_auto_reviewed_candidate_count"), 0),
            "sim_auto_unreviewed_candidate_count": _safe_int(summary.get("sim_auto_unreviewed_candidate_count"), 0),
            "sim_auto_downgraded_by_review_count": _safe_int(summary.get("sim_auto_downgraded_by_review_count"), 0),
            "sim_auto_review_shard_count": _safe_int(summary.get("sim_auto_review_shard_count"), 0),
            "ai_review_followup_required": bool(summary.get("ai_review_followup_required")),
            "ai_review_followup_reasons": summary.get("ai_review_followup_reasons")
            if isinstance(summary.get("ai_review_followup_reasons"), list)
            else [],
            "sim_auto_blocked_by_ai_review_followup": bool(summary.get("sim_auto_blocked_by_ai_review_followup")),
            "candidate_count": _safe_int(summary.get("candidate_count"), 0),
            "surfaced_candidate_count": _safe_int(summary.get("surfaced_candidate_count"), 0),
            "sim_auto_approved_count": _safe_int(summary.get("sim_auto_approved_count"), 0),
            "swing_lifecycle_flow_bucket_count": _safe_int(summary.get("swing_lifecycle_flow_bucket_count"), 0),
            "complete_flow_count": _safe_int(summary.get("complete_flow_count"), 0),
            "incomplete_flow_count": _safe_int(summary.get("incomplete_flow_count"), 0),
            "identity_join_rate": summary.get("identity_join_rate"),
            "complete_flow_rate": summary.get("complete_flow_rate"),
            "join_contract_blocked": bool(summary.get("join_contract_blocked")),
            "flow_sim_auto_approved_count": _safe_int(summary.get("flow_sim_auto_approved_count"), 0),
            "stage_only_source_only_count": _safe_int(summary.get("stage_only_source_only_count"), 0),
            "source_only_keep_collecting_count": _safe_int(summary.get("source_only_keep_collecting_count"), 0),
            "code_patch_required_count": _safe_int(summary.get("code_patch_required_count"), 0),
            "runtime_blocked_contract_gap_count": _safe_int(summary.get("runtime_blocked_contract_gap_count"), 0),
            "automation_handoff_gap_count": _safe_int(summary.get("automation_handoff_gap_count"), 0),
            "deterministic_proposal_count": _safe_int(summary.get("deterministic_proposal_count"), 0),
            "ai_tier2_proposal_count": _safe_int(summary.get("ai_tier2_proposal_count"), 0),
            "comparative_review_count": _safe_int(summary.get("comparative_review_count"), 0),
            "selected_decision_counts": summary.get("selected_decision_counts")
            if isinstance(summary.get("selected_decision_counts"), dict)
            else {},
            "selected_source_counts": summary.get("selected_source_counts")
            if isinstance(summary.get("selected_source_counts"), dict)
            else {},
            "swing_entry_bottleneck_primary": summary.get("swing_entry_bottleneck_primary"),
            "swing_entry_bottleneck_candidate_present": any(
                str(item.get("bucket_id") or "") == "swing_entry_bottleneck_swing_entry_drought_critical"
                for item in (payload.get("surfaced_candidates") or [])
                if isinstance(item, dict)
            ),
            "state_counts": summary.get("state_counts") if isinstance(summary.get("state_counts"), dict) else {},
            "stage_counts": summary.get("stage_counts") if isinstance(summary.get("stage_counts"), dict) else {},
            "code_improvement_workorder_ids": [
                str(item) for item in (summary.get("code_improvement_workorder_ids") or []) if str(item)
            ],
            "implemented_code_improvement_workorder_ids": [
                str(item) for item in (summary.get("implemented_code_improvement_workorder_ids") or []) if str(item)
            ],
            "pending_code_improvement_workorder_ids": [
                str(item) for item in (summary.get("pending_code_improvement_workorder_ids") or []) if str(item)
            ],
            "ai_review_followup_workorder_ids": [
                str(item) for item in (summary.get("ai_review_followup_workorder_ids") or []) if str(item)
            ],
            "surfaced_candidate_ids": [
                str(item) for item in (payload.get("surfaced_candidate_ids") or []) if str(item)
            ],
            "warnings": warnings,
        },
        str(json_path),
        warnings,
    )


def _institutional_flow_context_summary(target_date: str) -> tuple[dict[str, Any], str | None, list[str]]:
    json_path, _ = institutional_flow_report_paths(target_date)
    payload = _load_json(json_path)
    if not payload:
        return (
            {
                "available": False,
                "artifact": None,
                "status": "missing",
                "row_count": 0,
                "join_rate_pct": 0.0,
                "status_counts": {},
                "source_mix": {},
                "top_net_buy": [],
                "runtime_effect": False,
                "decision_authority": "source_only_lifecycle_feature",
            },
            None,
            ["institutional_flow_context_missing"],
        )
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    warnings = [f"institutional_flow_context:{item}" for item in (payload.get("warnings") or []) if str(item)]
    return (
        {
            "available": True,
            "artifact": str(json_path),
            "status": "warning" if payload.get("warnings") else "pass",
            "row_count": _safe_int(summary.get("row_count"), 0),
            "ok_count": _safe_int(summary.get("ok_count"), 0),
            "partial_count": _safe_int(summary.get("partial_count"), 0),
            "missing_count": _safe_int(summary.get("missing_count"), 0),
            "token_error_count": _safe_int(summary.get("token_error_count"), 0),
            "join_rate_pct": round(_safe_float(summary.get("join_rate_pct"), 0.0), 2),
            "status_counts": summary.get("status_counts") if isinstance(summary.get("status_counts"), dict) else {},
            "source_mix": summary.get("source_mix") if isinstance(summary.get("source_mix"), dict) else {},
            "top_net_buy": summary.get("top_net_buy") if isinstance(summary.get("top_net_buy"), list) else [],
            "runtime_effect": bool(payload.get("runtime_effect")),
            "decision_authority": payload.get("decision_authority") or "source_only_lifecycle_feature",
        },
        str(json_path),
        warnings,
    )


def _microstructure_reaction_context_summary(target_date: str) -> tuple[dict[str, Any], str | None, list[str]]:
    json_path, _ = microstructure_reaction_report_paths(target_date)
    payload = _load_json(json_path)
    if not payload:
        return (
            {
                "available": False,
                "artifact": None,
                "status": "missing",
                "row_count": 0,
                "ok_count": 0,
                "missing_or_unusable_count": 0,
                "real_submitted_count": 0,
                "status_counts": {},
                "entry_reaction_quality_counts": {},
                "source_quality_counts": {},
                "runtime_effect": False,
                "decision_authority": "entry_confidence_modifier_source_only",
                "forbidden_uses": [
                    "standalone_buy",
                    "broker_guard_bypass",
                    "threshold_mutation",
                    "provider_route_change",
                    "bot_restart",
                    "cap_release",
                ],
            },
            None,
            [],
        )
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    warnings = [f"microstructure_reaction_context:{item}" for item in (payload.get("warnings") or []) if str(item)]
    return (
        {
            "available": True,
            "artifact": str(json_path),
            "status": "warning" if payload.get("warnings") else "pass",
            "row_count": _safe_int(summary.get("row_count"), 0),
            "ok_count": _safe_int(summary.get("ok_count"), 0),
            "missing_or_unusable_count": _safe_int(summary.get("missing_or_unusable_count"), 0),
            "real_submitted_count": _safe_int(summary.get("real_submitted_count"), 0),
            "status_counts": summary.get("status_counts") if isinstance(summary.get("status_counts"), dict) else {},
            "entry_reaction_quality_counts": (
                summary.get("entry_reaction_quality_counts")
                if isinstance(summary.get("entry_reaction_quality_counts"), dict)
                else {}
            ),
            "source_quality_counts": (
                summary.get("source_quality_counts")
                if isinstance(summary.get("source_quality_counts"), dict)
                else {}
            ),
            "avg_ask_sweep_score": summary.get("avg_ask_sweep_score"),
            "avg_post_sweep_hold_score": summary.get("avg_post_sweep_hold_score"),
            "avg_bid_replenishment_score": summary.get("avg_bid_replenishment_score"),
            "max_vi_proximity_risk": _safe_int(summary.get("max_vi_proximity_risk"), 0),
            "runtime_effect": bool(payload.get("runtime_effect")),
            "decision_authority": payload.get("decision_authority") or "entry_confidence_modifier_source_only",
            "metric_role": payload.get("metric_role") or "feature_context",
            "primary_decision_metric": payload.get("primary_decision_metric") or "source_quality_adjusted_ev_pct",
            "forbidden_uses": payload.get("forbidden_uses") if isinstance(payload.get("forbidden_uses"), list) else [],
        },
        str(json_path),
        warnings,
    )


def _pipeline_event_verbosity_summary(target_date: str) -> tuple[dict[str, Any], str | None, list[str]]:
    json_path = REPORT_DIR / "pipeline_event_verbosity" / f"pipeline_event_verbosity_{target_date}.json"
    payload = _load_json(json_path)
    if not payload:
        return (
            {
                "available": False,
                "artifact": None,
                "state": "missing",
                "recommended_workorder_state": "missing",
            },
            None,
            ["pipeline_event_verbosity_missing"],
        )
    raw = payload.get("raw_stream") if isinstance(payload.get("raw_stream"), dict) else {}
    parity = payload.get("parity") if isinstance(payload.get("parity"), dict) else {}
    return (
        {
            "available": True,
            "artifact": str(json_path),
            "state": payload.get("state"),
            "recommended_workorder_state": payload.get("recommended_workorder_state"),
            "raw_size_bytes": raw.get("raw_size_bytes"),
            "high_volume_line_count": raw.get("high_volume_line_count"),
            "high_volume_byte_share_pct": raw.get("high_volume_byte_share_pct"),
            "parity_ok": parity.get("ok"),
            "suppress_eligibility": parity.get("suppress_eligibility"),
            "runtime_effect": ((payload.get("policy") or {}).get("runtime_effect"))
            if isinstance(payload.get("policy"), dict)
            else False,
        },
        str(json_path),
        [],
    )


def _codebase_performance_workorder_summary(target_date: str) -> tuple[dict[str, Any], str | None, list[str]]:
    json_path = REPORT_DIR / "codebase_performance_workorder" / f"codebase_performance_workorder_{target_date}.json"
    payload = _load_json(json_path)
    if not payload:
        return (
            {
                "available": False,
                "artifact": None,
                "accepted_count": 0,
                "deferred_count": 0,
                "rejected_count": 0,
                "runtime_effect": False,
            },
            None,
            ["codebase_performance_workorder_missing"],
        )
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    policy = payload.get("policy") if isinstance(payload.get("policy"), dict) else {}
    return (
        {
            "available": True,
            "artifact": str(json_path),
            "source_doc_hash": payload.get("source_doc_hash"),
            "accepted_count": _safe_int(summary.get("accepted_count"), 0),
            "deferred_count": _safe_int(summary.get("deferred_count"), 0),
            "rejected_count": _safe_int(summary.get("rejected_count"), 0),
            "runtime_effect": bool(policy.get("runtime_effect")),
            "strategy_effect": bool(policy.get("strategy_effect")),
            "data_quality_effect": bool(policy.get("data_quality_effect")),
            "tuning_axis_effect": bool(policy.get("tuning_axis_effect")),
            "decision_authority": policy.get("decision_authority"),
        },
        str(json_path),
        [],
    )


def _audit_summary(target_date: str, report_type: str, report_dir: Path) -> tuple[dict[str, Any], str | None, list[str]]:
    json_path = report_dir / f"{report_type}_{target_date}.json"
    payload = _load_json(json_path)
    if not payload:
        return (
            {
                "available": False,
                "artifact": None,
                "status": "missing",
                "fail_count": 0,
                "warning_count": 0,
                "code_improvement_order_count": 0,
                "runtime_effect": False,
            },
            None,
            [f"{report_type}_missing"],
        )
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    status = str(payload.get("status") or "unknown")
    audit_status = str(summary.get("audit_status") or "")
    ai_fail_closed = bool(summary.get("ai_fail_closed"))
    ai_review_followup_required = bool(summary.get("ai_review_followup_required"))
    ai_review_followup_reasons = (
        summary.get("ai_review_followup_reasons")
        if isinstance(summary.get("ai_review_followup_reasons"), list)
        else []
    )
    fail_count = _safe_int(summary.get("fail_count"), 0)
    source_only_candidate_warning_resolved = (
        report_type in {"producer_gap_discovery", "stage_hook_workorder_discovery"}
        and status == "warning"
        and fail_count == 0
        and audit_status == "pass"
        and not ai_fail_closed
    )
    warnings: list[str] = []
    if status in {"warning", "fail"} and not source_only_candidate_warning_resolved:
        warnings.append(f"{report_type}_{status}")
    if ai_review_followup_required:
        warnings.append(f"{report_type}_ai_review_followup_required")
    return (
        {
            "available": True,
            "artifact": str(json_path),
            "status": status,
            "fail_count": fail_count,
            "warning_count": _safe_int(summary.get("warning_count"), 0),
            "code_improvement_order_count": _safe_int(
                summary.get("code_improvement_order_count"),
                _safe_int(summary.get("order_count"), _safe_int(summary.get("workorder_count"), 0)),
            ),
            "runtime_effect": bool(payload.get("runtime_effect")),
            "decision_authority": payload.get("decision_authority"),
            "source_only_candidate_warning_resolved": source_only_candidate_warning_resolved,
            "audit_status": audit_status or None,
            "ai_fail_closed": ai_fail_closed,
            "ai_review_followup_required": ai_review_followup_required,
            "ai_review_followup_reasons": ai_review_followup_reasons,
            "deterministic_proposal_count": _safe_int(summary.get("deterministic_proposal_count"), 0),
            "ai_tier2_proposal_count": _safe_int(summary.get("ai_tier2_proposal_count"), 0),
            "comparative_review_count": _safe_int(summary.get("comparative_review_count"), 0),
            "selected_decision_counts": summary.get("selected_decision_counts")
            if isinstance(summary.get("selected_decision_counts"), dict)
            else {},
            "selected_source_counts": summary.get("selected_source_counts")
            if isinstance(summary.get("selected_source_counts"), dict)
            else {},
        },
        str(json_path),
        warnings,
    )


def _lifecycle_bucket_discovery_summary(target_date: str) -> tuple[dict[str, Any], str | None, list[str]]:
    json_path = lifecycle_bucket_discovery_report_path(target_date)
    payload = _load_json(json_path)
    if not payload:
        return (
            {
                "available": False,
                "artifact": None,
                "status": "missing",
                "candidate_count": 0,
                "surfaced_candidate_count": 0,
                "sim_auto_approved_count": 0,
                "live_auto_apply_ready_count": 0,
                "new_bucket_candidate_count": 0,
                "human_intervention_required": False,
                "window_role": "new_pattern_detection",
                "window_policy": "daily_only",
            },
            None,
            ["lifecycle_bucket_discovery_missing"],
        )
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    warnings = [f"lifecycle_bucket_discovery:{item}" for item in (payload.get("warnings") or []) if str(item)]
    return (
        {
            "available": True,
            "artifact": str(json_path),
            "status": summary.get("status"),
            "window_role": "new_pattern_detection",
            "window_policy": payload.get("window_policy") or summary.get("source_window_policy") or "daily_only",
            "candidate_count": _safe_int(summary.get("candidate_count"), 0),
            "surfaced_candidate_count": _safe_int(summary.get("surfaced_candidate_count"), 0),
            "sim_auto_approved_count": _safe_int(summary.get("sim_auto_approved_count"), 0),
            "entry_only_sim_auto_approved_count": _safe_int(summary.get("entry_only_sim_auto_approved_count"), 0),
            "lifecycle_flow_sim_probe_candidate_count": _safe_int(
                summary.get("lifecycle_flow_sim_probe_candidate_count"),
                0,
            ),
            "live_auto_apply_ready_count": _safe_int(summary.get("live_auto_apply_ready_count"), 0),
            "new_bucket_candidate_count": _safe_int(summary.get("new_bucket_candidate_count"), 0),
            "code_patch_required_count": _safe_int(summary.get("code_patch_required_count"), 0),
            "automation_handoff_gap_count": _safe_int(summary.get("automation_handoff_gap_count"), 0),
            "parent_bucket_count": _safe_int(summary.get("parent_bucket_count"), 0),
            "selected_parent_level": summary.get("selected_parent_level"),
            "parent_granularity_status": summary.get("parent_granularity_status"),
            "absorbed_child_count": _safe_int(summary.get("absorbed_child_count"), 0),
            "absorbed_sample_count": _safe_int(summary.get("absorbed_sample_count"), 0),
            "child_conflict_warning_count": _safe_int(summary.get("child_conflict_warning_count"), 0),
            "source_contract_status": summary.get("source_contract_status"),
            "ai_two_pass_review_status": summary.get("ai_two_pass_review_status"),
            "deterministic_proposal_count": _safe_int(summary.get("deterministic_proposal_count"), 0),
            "ai_tier2_proposal_count": _safe_int(summary.get("ai_tier2_proposal_count"), 0),
            "comparative_review_count": _safe_int(summary.get("comparative_review_count"), 0),
            "selected_decision_counts": summary.get("selected_decision_counts")
            if isinstance(summary.get("selected_decision_counts"), dict)
            else {},
            "selected_source_counts": summary.get("selected_source_counts")
            if isinstance(summary.get("selected_source_counts"), dict)
            else {},
            "human_intervention_required": bool(summary.get("human_intervention_required")),
            "state_counts": summary.get("state_counts") if isinstance(summary.get("state_counts"), dict) else {},
            "stage_counts": summary.get("stage_counts") if isinstance(summary.get("stage_counts"), dict) else {},
            "top_surfaced": [
                {
                    "bucket_id": item.get("bucket_id"),
                    "stage": item.get("stage"),
                    "classification_state": item.get("classification_state"),
                    "live_auto_apply_family": item.get("live_auto_apply_family"),
                    "recommended_action": item.get("recommended_action"),
                    "joined_sample": item.get("joined_sample"),
                    "source_quality_adjusted_ev_pct": item.get("source_quality_adjusted_ev_pct"),
                }
                for item in (payload.get("surfaced_candidates") or [])[:8]
                if isinstance(item, dict)
            ],
        },
        str(json_path),
        warnings,
    )


def _lifecycle_bucket_window_report_path(target_date: str, suffix: str) -> Path:
    base = lifecycle_bucket_discovery_report_path(target_date)
    safe_suffix = str(suffix or "").strip().replace("/", "_")
    return base.parent / f"lifecycle_bucket_discovery_{target_date}_{safe_suffix}.json"


def _lifecycle_bucket_windows_summary(target_date: str) -> tuple[dict[str, Any], list[str]]:
    windows = ("rolling5d", "rolling10d", "mtd")
    daily, _, daily_warnings = _lifecycle_bucket_discovery_summary(target_date)
    warnings = list(daily_warnings)
    result: dict[str, Any] = {
        "daily": daily,
        "windows": {},
        "promotion_window": "mtd",
        "confirmation_windows": ["rolling5d", "rolling10d"],
        "warnings": [],
    }
    for suffix in windows:
        path = _lifecycle_bucket_window_report_path(target_date, suffix)
        payload = _load_json(path)
        summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
        item = {
            "available": bool(payload),
            "artifact": str(path) if path.exists() else None,
            "window_role": "promotion_confirmation" if suffix == "mtd" else "rolling_confirmation",
            "window_policy": payload.get("window_policy") or summary.get("source_window_policy") or suffix,
            "status": summary.get("status") or ("missing" if not payload else "unknown"),
            "parent_bucket_count": _safe_int(summary.get("parent_bucket_count"), 0),
            "selected_parent_level": summary.get("selected_parent_level"),
            "parent_granularity_status": summary.get("parent_granularity_status"),
            "absorbed_child_count": _safe_int(summary.get("absorbed_child_count"), 0),
            "absorbed_sample_count": _safe_int(summary.get("absorbed_sample_count"), 0),
            "child_conflict_warning_count": _safe_int(summary.get("child_conflict_warning_count"), 0),
            "live_auto_apply_ready_count": _safe_int(summary.get("live_auto_apply_ready_count"), 0),
            "source_contract_status": summary.get("source_contract_status"),
            "ai_two_pass_review_status": summary.get("ai_two_pass_review_status"),
        }
        if not payload:
            warnings.append(f"lifecycle_bucket_windows:{suffix}_missing")
        result["windows"][suffix] = item
    result["warnings"] = warnings
    return result, warnings


def build_threshold_cycle_ev_report(target_date: str) -> dict[str, Any]:
    _JSON_LOAD_DIAGNOSTICS.clear()
    target_date = str(target_date).strip()
    trade_review_path = MONITOR_SNAPSHOT_DIR / f"trade_review_{target_date}.json"
    performance_path = MONITOR_SNAPSHOT_DIR / f"performance_tuning_{target_date}.json"
    calibration_path = _calibration_path(target_date)
    apply_path = apply_manifest_path(target_date)

    trade_review = _load_json(trade_review_path)
    performance = _load_json(performance_path)
    calibration = _load_json(calibration_path)
    apply_manifest = _load_json(apply_path)
    trade_metrics = trade_review.get("metrics") if isinstance(trade_review.get("metrics"), dict) else {}
    perf_metrics = performance.get("metrics") if isinstance(performance.get("metrics"), dict) else {}
    scalp_simulator = calibration.get("scalp_simulator") if isinstance(calibration.get("scalp_simulator"), dict) else {}
    wait6579_counterfactual, wait6579_counterfactual_path = _wait6579_counterfactual_summary(target_date)
    completed_by_source = (
        calibration.get("completed_by_source")
        if isinstance(calibration.get("completed_by_source"), dict)
        else {}
    )
    pattern_lab_summary, pattern_lab_path, pattern_lab_warnings = _pattern_lab_automation_summary(target_date)
    swing_lab_summary, swing_lab_path, swing_lab_warnings = _swing_pattern_lab_automation_summary(target_date)
    scalp_entry_adm_summary, scalp_entry_adm_path, scalp_entry_adm_warnings = _scalp_entry_adm_summary(target_date)
    lifecycle_matrix_summary, lifecycle_matrix_path, lifecycle_matrix_warnings = _lifecycle_decision_matrix_summary(target_date)
    buy_funnel_sentinel_summary, buy_funnel_sentinel_path, buy_funnel_sentinel_warnings = _buy_funnel_sentinel_summary(target_date)
    (
        lifecycle_bucket_discovery_summary,
        lifecycle_bucket_discovery_path,
        lifecycle_bucket_discovery_warnings,
    ) = _lifecycle_bucket_discovery_summary(target_date)
    lifecycle_bucket_windows_summary, lifecycle_bucket_windows_warnings = _lifecycle_bucket_windows_summary(target_date)
    lifecycle_ai_context_summary, lifecycle_ai_context_path, lifecycle_ai_context_warnings = _lifecycle_ai_context_summary(target_date)
    (
        lifecycle_ai_context_attribution_summary,
        lifecycle_ai_context_attribution_path,
        lifecycle_ai_context_attribution_warnings,
    ) = _lifecycle_ai_context_attribution_summary(target_date)
    swing_discovery_summary, swing_discovery_path, swing_discovery_warnings = _swing_strategy_discovery_summary(target_date)
    swing_lifecycle_matrix_summary, swing_lifecycle_matrix_path, swing_lifecycle_matrix_warnings = (
        _swing_lifecycle_matrix_summary(target_date)
    )
    (
        swing_lifecycle_bucket_discovery_summary,
        swing_lifecycle_bucket_discovery_path,
        swing_lifecycle_bucket_discovery_warnings,
    ) = _swing_lifecycle_bucket_discovery_summary(target_date)
    institutional_flow_summary, institutional_flow_path, institutional_flow_warnings = _institutional_flow_context_summary(target_date)
    microstructure_reaction_summary, microstructure_reaction_path, microstructure_reaction_warnings = (
        _microstructure_reaction_context_summary(target_date)
    )
    code_workorder_summary, code_workorder_path, code_workorder_warnings = _code_improvement_workorder_summary(target_date)
    pipeline_verbosity_summary, pipeline_verbosity_path, pipeline_verbosity_warnings = _pipeline_event_verbosity_summary(target_date)
    codebase_perf_summary, codebase_perf_path, codebase_perf_warnings = _codebase_performance_workorder_summary(target_date)
    currentness_audit_summary, currentness_audit_path, currentness_audit_warnings = _audit_summary(
        target_date,
        "pattern_lab_currentness_audit",
        PATTERN_LAB_CURRENTNESS_AUDIT_DIR,
    )
    pattern_lab_ai_review_summary, pattern_lab_ai_review_path, pattern_lab_ai_review_warnings = _audit_summary(
        target_date,
        "pattern_lab_ai_review",
        PATTERN_LAB_AI_REVIEW_DIR,
    )
    time_window_regime_summary, time_window_regime_path, time_window_regime_warnings = _audit_summary(
        target_date,
        "time_window_regime_counterfactual",
        TIME_WINDOW_REGIME_COUNTERFACTUAL_DIR,
    )
    producer_gap_discovery_summary, producer_gap_discovery_path, producer_gap_discovery_warnings = _audit_summary(
        target_date,
        "producer_gap_discovery",
        PRODUCER_GAP_DISCOVERY_DIR,
    )
    stage_hook_workorder_summary, stage_hook_workorder_path, stage_hook_workorder_warnings = _audit_summary(
        target_date,
        "stage_hook_workorder_discovery",
        STAGE_HOOK_WORKORDER_DISCOVERY_DIR,
    )
    stage_hook_scaffold_summary, stage_hook_scaffold_path, stage_hook_scaffold_warnings = _audit_summary(
        target_date,
        "stage_hook_runtime_scaffold",
        STAGE_HOOK_RUNTIME_SCAFFOLD_DIR,
    )
    propagation_audit_summary, propagation_audit_path, propagation_audit_warnings = _audit_summary(
        target_date,
        "pattern_lab_propagation_audit",
        PATTERN_LAB_PROPAGATION_AUDIT_DIR,
    )
    selected_families = _selected_families(apply_manifest)
    swing_runtime_approval = _swing_runtime_approval_summary(apply_manifest)
    completed = _safe_int(trade_metrics.get("completed_trades"), 0)
    win = _safe_int(trade_metrics.get("win_trades"), 0)
    loss = _safe_int(trade_metrics.get("loss_trades"), 0)
    win_rate = round((win / completed) * 100.0, 2) if completed else 0.0
    budget_pass = _safe_int(perf_metrics.get("budget_pass_events"), 0)
    submitted = _safe_int(perf_metrics.get("order_bundle_submitted_events"), 0)
    submitted_rate = round((submitted / budget_pass) * 100.0, 2) if budget_pass else 0.0
    full_fill_completed_avg = _safe_float(perf_metrics.get("full_fill_completed_avg_profit_rate"), 0.0)
    latency_source_metrics, latency_recommendation = _latency_classifier_source_metrics(target_date, calibration)
    latency_recommended_action = str(latency_source_metrics.get("recommended_action") or "")
    latency_recovery_count = _safe_int(latency_source_metrics.get("would_recovery_canary_events"), 0)
    latency_submit_routing = (
        latency_source_metrics.get("latency_submit_routing")
        or (
            "latency_submit_recovery_candidate"
            if latency_recommended_action == "bounded_apply"
            else "latency_submit_recovery_hold"
            if latency_recovery_count > 0
            else "latency_classifier_runtime_semantics_gap"
        )
    )

    source_load_warnings = [
        f"source_load_{item.get('status')}:{Path(str(item.get('path') or '')).name}"
        for item in _JSON_LOAD_DIAGNOSTICS
    ]
    workorder_orders = code_workorder_summary.get("orders") if isinstance(code_workorder_summary.get("orders"), list) else []
    entry_submit_drought_handoff_selected = bool(
        code_workorder_summary.get("entry_submit_drought_selected")
    ) or any(
        isinstance(item, dict) and item.get("order_id") == "order_entry_submit_drought_auto_resolution"
        for item in workorder_orders
    )
    clean_policy = clean_baseline_policy()
    clean_policy_warning = policy_warning_for_date(target_date, clean_policy)
    source_quality_preflight_gate = load_source_quality_preflight(target_date)

    report = {
        "date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "purpose": "daily_ev_performance_report_for_unattended_threshold_calibration",
        "clean_tuning_baseline": clean_policy,
        "source_quality_preflight_gate": source_quality_preflight_gate,
        "runtime_apply": {
            "apply_manifest": str(apply_path) if apply_path.exists() else None,
            "runtime_change": bool(apply_manifest.get("runtime_change")),
            "status": apply_manifest.get("status"),
            "selected_families": selected_families,
            "runtime_env_file": apply_manifest.get("runtime_env_file"),
            "runtime_apply_bridge": _runtime_apply_bridge_summary(apply_manifest),
            "lifecycle_bucket_discovery": _lifecycle_bucket_discovery_apply_summary(apply_manifest),
        },
        "daily_ev_summary": {
            "completed_trades": completed,
            "open_trades": _safe_int(trade_metrics.get("open_trades"), 0),
            "win_trades": win,
            "loss_trades": loss,
            "win_rate_pct": win_rate,
            "avg_profit_rate_pct": round(_safe_float(trade_metrics.get("avg_profit_rate"), 0.0), 4),
            "realized_pnl_krw": _safe_int(trade_metrics.get("realized_pnl_krw"), 0),
            "full_fill_completed_avg_profit_rate_pct": round(full_fill_completed_avg, 4),
            "source_split": completed_by_source,
        },
        "entry_funnel": {
            "budget_pass_events": budget_pass,
            "order_bundle_submitted_events": submitted,
            "budget_pass_to_submitted_rate_pct": submitted_rate,
            "latency_block_events": _safe_int(perf_metrics.get("latency_block_events"), 0),
            "latency_pass_events": _safe_int(perf_metrics.get("latency_pass_events"), 0),
            "latency_submit_routing": latency_submit_routing,
            "latency_classifier_runtime_semantics": latency_source_metrics.get("latency_classifier_runtime_semantics")
            or latency_source_metrics.get("profile_runtime_semantics"),
            "latency_classifier_recommendation_status": "loaded" if latency_recommendation else "missing",
            "latency_classifier_profile_generation": latency_source_metrics.get("latency_classifier_profile_generation")
            or (latency_recommendation.get("profile_generation") if isinstance(latency_recommendation, dict) else {}),
            "recommended_action": latency_recommended_action or None,
            "recommended_action_reason": latency_source_metrics.get("recommended_action_reason"),
            "allowed_runtime_apply": bool(latency_source_metrics.get("allowed_runtime_apply")),
            "calibration_state": latency_source_metrics.get("calibration_state"),
            "would_safe_pass_events": _safe_int(latency_source_metrics.get("would_safe_pass_events"), 0),
            "would_caution_normal_events": _safe_int(
                latency_source_metrics.get("would_caution_normal_events")
                if latency_source_metrics.get("would_caution_normal_events") is not None
                else latency_source_metrics.get("would_caution_reject_events"),
                0,
            ),
            "would_recovery_canary_events": _safe_int(
                latency_source_metrics.get("would_recovery_canary_events"),
                0,
            ),
            "would_recovery_canary_attempts": _safe_int(
                latency_source_metrics.get("would_recovery_canary_attempts"),
                0,
            ),
            "stale_quote_override_events": _safe_int(latency_source_metrics.get("stale_quote_override_events"), 0),
            "broker_guard_bypass_candidates": _safe_int(
                latency_source_metrics.get("broker_guard_bypass_candidates"),
                0,
            ),
            "counterfactual_joined_sample": _safe_int(
                latency_source_metrics.get("counterfactual_joined_sample"),
                0,
            ),
            "counterfactual_ev_pct": latency_source_metrics.get("counterfactual_ev_pct"),
            "missed_winner_recovered": _safe_int(latency_source_metrics.get("missed_winner_recovered"), 0),
            "avoided_loser_lost": _safe_int(latency_source_metrics.get("avoided_loser_lost"), 0),
            "full_fill_events": _safe_int(perf_metrics.get("full_fill_events"), 0),
            "partial_fill_events": _safe_int(perf_metrics.get("partial_fill_events"), 0),
            "buy_funnel_sentinel_primary": buy_funnel_sentinel_summary.get("primary"),
            "entry_submit_drought_handoff_selected": entry_submit_drought_handoff_selected,
            "submit_bucket_attribution_summary": lifecycle_matrix_summary.get("submit_bucket_attribution_summary"),
            "post_submit_contract_gaps": lifecycle_matrix_summary.get("post_submit_contract_gaps"),
        },
        "holding_exit": {
            "holding_reviews": _safe_int(perf_metrics.get("holding_reviews"), 0),
            "exit_signals": _safe_int(perf_metrics.get("exit_signals"), 0),
            "holding_review_ms_p95": round(_safe_float(perf_metrics.get("holding_review_ms_p95"), 0.0), 2),
            "holding_ai_cache_hit_ratio": round(_safe_float(perf_metrics.get("holding_ai_cache_hit_ratio"), 0.0), 4),
        },
        "scalp_simulator": scalp_simulator,
        "missed_probe_counterfactual": wait6579_counterfactual,
        "calibration_outcome": {
            "calibration_report": str(calibration_path) if calibration_path.exists() else None,
            "run_phase": calibration.get("run_phase"),
            "runtime_change": bool(calibration.get("runtime_change")),
            "decisions": _cohort_decisions(calibration),
        },
        "approval_requests": _approval_requests(calibration),
        "swing_runtime_approval": swing_runtime_approval,
        "pattern_lab_automation": pattern_lab_summary,
        "swing_pattern_lab_automation": swing_lab_summary,
        "scalp_entry_action_decision_matrix": scalp_entry_adm_summary,
        "buy_funnel_sentinel": buy_funnel_sentinel_summary,
        "lifecycle_decision_matrix": lifecycle_matrix_summary,
        "lifecycle_bucket_discovery": lifecycle_bucket_discovery_summary,
        "lifecycle_bucket_windows": lifecycle_bucket_windows_summary,
        "lifecycle_ai_context": lifecycle_ai_context_summary,
        "lifecycle_ai_context_attribution": lifecycle_ai_context_attribution_summary,
        "swing_strategy_discovery": swing_discovery_summary,
        "swing_lifecycle_decision_matrix": swing_lifecycle_matrix_summary,
        "swing_lifecycle_bucket_discovery": swing_lifecycle_bucket_discovery_summary,
        "institutional_flow_context": institutional_flow_summary,
        "microstructure_reaction_context": microstructure_reaction_summary,
        "pipeline_event_verbosity": pipeline_verbosity_summary,
        "codebase_performance_workorder": codebase_perf_summary,
        "pattern_lab_currentness_audit": currentness_audit_summary,
        "pattern_lab_ai_review": pattern_lab_ai_review_summary,
        "time_window_regime_counterfactual": time_window_regime_summary,
        "producer_gap_discovery": producer_gap_discovery_summary,
        "stage_hook_workorder_discovery": stage_hook_workorder_summary,
        "stage_hook_runtime_scaffold": stage_hook_scaffold_summary,
        "pattern_lab_propagation_audit": propagation_audit_summary,
        "code_improvement_workorder": code_workorder_summary,
        "sources": {
            "trade_review": str(trade_review_path) if trade_review_path.exists() else None,
            "performance_tuning": str(performance_path) if performance_path.exists() else None,
            "calibration": str(calibration_path) if calibration_path.exists() else None,
            "apply_manifest": str(apply_path) if apply_path.exists() else None,
            "pattern_lab_automation": pattern_lab_path,
            "swing_pattern_lab_automation": swing_lab_path,
            "scalp_entry_action_decision_matrix": scalp_entry_adm_path,
            "buy_funnel_sentinel": buy_funnel_sentinel_path,
            "lifecycle_decision_matrix": lifecycle_matrix_path,
            "lifecycle_bucket_discovery": lifecycle_bucket_discovery_path,
            "lifecycle_bucket_windows": lifecycle_bucket_windows_summary,
            "lifecycle_ai_context": lifecycle_ai_context_path,
            "lifecycle_ai_context_attribution": lifecycle_ai_context_attribution_path,
            "swing_strategy_discovery": swing_discovery_path,
            "swing_lifecycle_decision_matrix": swing_lifecycle_matrix_path,
            "swing_lifecycle_bucket_discovery": swing_lifecycle_bucket_discovery_path,
            "institutional_flow_context": institutional_flow_path,
            "microstructure_reaction_context": microstructure_reaction_path,
            "pipeline_event_verbosity": pipeline_verbosity_path,
            "codebase_performance_workorder": codebase_perf_path,
            "pattern_lab_currentness_audit": currentness_audit_path,
            "pattern_lab_ai_review": pattern_lab_ai_review_path,
            "time_window_regime_counterfactual": time_window_regime_path,
            "producer_gap_discovery": producer_gap_discovery_path,
            "stage_hook_workorder_discovery": stage_hook_workorder_path,
            "stage_hook_runtime_scaffold": stage_hook_scaffold_path,
            "pattern_lab_propagation_audit": propagation_audit_path,
            "code_improvement_workorder": code_workorder_path,
            "missed_probe_counterfactual": wait6579_counterfactual_path,
            "observation_source_quality_audit": source_quality_preflight_gate.get("artifact"),
        },
        "source_load_diagnostics": _JSON_LOAD_DIAGNOSTICS.copy(),
        "warnings": [
            message
            for message in [
                "trade_review_missing" if not trade_review_path.exists() else "",
                "performance_tuning_missing" if not performance_path.exists() else "",
                "calibration_report_missing" if not calibration_path.exists() else "",
                "apply_manifest_missing" if not apply_path.exists() else "",
                *pattern_lab_warnings,
                *swing_lab_warnings,
                *scalp_entry_adm_warnings,
                *buy_funnel_sentinel_warnings,
                *lifecycle_matrix_warnings,
                *lifecycle_bucket_discovery_warnings,
                *lifecycle_bucket_windows_warnings,
                *lifecycle_ai_context_warnings,
                *lifecycle_ai_context_attribution_warnings,
                *swing_discovery_warnings,
                *swing_lifecycle_matrix_warnings,
                *swing_lifecycle_bucket_discovery_warnings,
                *institutional_flow_warnings,
                *microstructure_reaction_warnings,
                *pipeline_verbosity_warnings,
                *codebase_perf_warnings,
                *currentness_audit_warnings,
                *pattern_lab_ai_review_warnings,
                *time_window_regime_warnings,
                *producer_gap_discovery_warnings,
            *stage_hook_workorder_warnings,
            *stage_hook_scaffold_warnings,
            *propagation_audit_warnings,
                *code_workorder_warnings,
                *source_load_warnings,
                clean_policy_warning or "",
                "source_quality_blocked_contract_gap"
                if source_quality_preflight_blocked(source_quality_preflight_gate)
                else "",
            ]
            if message
        ],
    }
    report["summary"] = _top_level_summary(report)
    report = apply_source_quality_preflight_block(report, source_quality_preflight_gate)
    report["summary"] = _top_level_summary(report)
    EV_REPORT_DIR.mkdir(parents=True, exist_ok=True)
    json_path, md_path = ev_report_paths(target_date)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_threshold_cycle_ev_markdown(report), encoding="utf-8")
    return report


def render_threshold_cycle_ev_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    ev = report.get("daily_ev_summary") if isinstance(report.get("daily_ev_summary"), dict) else {}
    funnel = report.get("entry_funnel") if isinstance(report.get("entry_funnel"), dict) else {}
    holding = report.get("holding_exit") if isinstance(report.get("holding_exit"), dict) else {}
    scalp_sim = report.get("scalp_simulator") if isinstance(report.get("scalp_simulator"), dict) else {}
    missed_probe = report.get("missed_probe_counterfactual") if isinstance(report.get("missed_probe_counterfactual"), dict) else {}
    runtime = report.get("runtime_apply") if isinstance(report.get("runtime_apply"), dict) else {}
    pattern_lab = report.get("pattern_lab_automation") if isinstance(report.get("pattern_lab_automation"), dict) else {}
    swing_lab = report.get("swing_pattern_lab_automation") if isinstance(report.get("swing_pattern_lab_automation"), dict) else {}
    scalp_entry_adm = report.get("scalp_entry_action_decision_matrix") if isinstance(report.get("scalp_entry_action_decision_matrix"), dict) else {}
    lifecycle_matrix = report.get("lifecycle_decision_matrix") if isinstance(report.get("lifecycle_decision_matrix"), dict) else {}
    lifecycle_bucket_discovery = (
        report.get("lifecycle_bucket_discovery")
        if isinstance(report.get("lifecycle_bucket_discovery"), dict)
        else {}
    )
    lifecycle_ai_context = report.get("lifecycle_ai_context") if isinstance(report.get("lifecycle_ai_context"), dict) else {}
    lifecycle_ai_context_attribution = (
        report.get("lifecycle_ai_context_attribution")
        if isinstance(report.get("lifecycle_ai_context_attribution"), dict)
        else {}
    )
    swing_discovery = report.get("swing_strategy_discovery") if isinstance(report.get("swing_strategy_discovery"), dict) else {}
    institutional_flow = report.get("institutional_flow_context") if isinstance(report.get("institutional_flow_context"), dict) else {}
    pipeline_verbosity = report.get("pipeline_event_verbosity") if isinstance(report.get("pipeline_event_verbosity"), dict) else {}
    codebase_perf = report.get("codebase_performance_workorder") if isinstance(report.get("codebase_performance_workorder"), dict) else {}
    currentness_audit = report.get("pattern_lab_currentness_audit") if isinstance(report.get("pattern_lab_currentness_audit"), dict) else {}
    pattern_lab_ai_review = report.get("pattern_lab_ai_review") if isinstance(report.get("pattern_lab_ai_review"), dict) else {}
    producer_gap_discovery = report.get("producer_gap_discovery") if isinstance(report.get("producer_gap_discovery"), dict) else {}
    propagation_audit = report.get("pattern_lab_propagation_audit") if isinstance(report.get("pattern_lab_propagation_audit"), dict) else {}
    swing_runtime = report.get("swing_runtime_approval") if isinstance(report.get("swing_runtime_approval"), dict) else {}
    code_workorder = report.get("code_improvement_workorder") if isinstance(report.get("code_improvement_workorder"), dict) else {}
    source_load_diagnostics = (
        report.get("source_load_diagnostics") if isinstance(report.get("source_load_diagnostics"), list) else []
    )
    approval_requests = report.get("approval_requests") if isinstance(report.get("approval_requests"), list) else []
    decisions = ((report.get("calibration_outcome") or {}).get("decisions") or []) if isinstance(report.get("calibration_outcome"), dict) else []
    sim_post_sell = scalp_sim.get("post_sell_join") if isinstance(scalp_sim.get("post_sell_join"), dict) else {}
    lines = [
        f"# Threshold Cycle Daily EV Report - {report.get('date')}",
        "",
        "## Summary",
        f"- status: `{summary.get('status')}`",
        f"- warning_count: `{summary.get('warning_count', 0)}`",
        f"- source_quality: status=`{summary.get('source_quality_status')}` allowed=`{summary.get('source_quality_tuning_input_allowed')}`",
        f"- samples real/sim: `{summary.get('real_sample', 0)}` / `{summary.get('sim_sample', 0)}`",
        f"- live_auto_ready_count: `{summary.get('live_auto_ready_count', 0)}`",
        f"- primary_verdict: `{summary.get('primary_verdict')}`",
        "",
        "## Runtime Apply",
        f"- status: `{runtime.get('status')}`",
        f"- runtime_change: `{runtime.get('runtime_change')}`",
        f"- selected_families: `{', '.join(runtime.get('selected_families') or []) or '-'}`",
        "",
        "## Daily EV",
        f"- completed: `{ev.get('completed_trades')}` / open: `{ev.get('open_trades')}`",
        f"- win/loss: `{ev.get('win_trades')}` / `{ev.get('loss_trades')}` (`{ev.get('win_rate_pct')}`%)",
        f"- avg_profit_rate: `{ev.get('avg_profit_rate_pct')}`%",
        f"- realized_pnl_krw: `{ev.get('realized_pnl_krw')}`",
        f"- full_fill_completed_avg_profit_rate: `{ev.get('full_fill_completed_avg_profit_rate_pct')}`%",
        "",
        "## Entry Funnel",
        f"- budget_pass_to_submitted: `{funnel.get('order_bundle_submitted_events')}` / `{funnel.get('budget_pass_events')}` (`{funnel.get('budget_pass_to_submitted_rate_pct')}`%)",
        f"- latency pass/block: `{funnel.get('latency_pass_events')}` / `{funnel.get('latency_block_events')}`",
        f"- latency submit routing: `{funnel.get('latency_submit_routing') or '-'}`",
        f"- latency recommended action: `{funnel.get('recommended_action') or '-'}` (`{funnel.get('recommended_action_reason') or '-'}`)",
        f"- latency profile generation: `{funnel.get('latency_classifier_profile_generation') or {}}`",
        f"- safe/caution_normal/recovery: `{funnel.get('would_safe_pass_events')}` / `{funnel.get('would_caution_normal_events')}` / `{funnel.get('would_recovery_canary_events')}`",
        f"- recovery attempts/cf sample/cf ev: `{funnel.get('would_recovery_canary_attempts')}` / `{funnel.get('counterfactual_joined_sample')}` / `{funnel.get('counterfactual_ev_pct')}`%",
        f"- recovered/lost labels: `{funnel.get('missed_winner_recovered')}` / `{funnel.get('avoided_loser_lost')}`",
        f"- stale/broker override excluded: `{funnel.get('stale_quote_override_events')}` / `{funnel.get('broker_guard_bypass_candidates')}`",
        f"- full/partial fill: `{funnel.get('full_fill_events')}` / `{funnel.get('partial_fill_events')}`",
        "",
        "## Holding Exit",
        f"- holding_reviews: `{holding.get('holding_reviews')}`",
        f"- exit_signals: `{holding.get('exit_signals')}`",
        f"- holding_review_ms_p95: `{holding.get('holding_review_ms_p95')}`",
        "",
        "## Scalp Simulator",
        f"- authority: `{scalp_sim.get('calibration_authority') or '-'}` / fill_policy: `{scalp_sim.get('fill_policy') or '-'}`",
        f"- armed/filled/sold: `{scalp_sim.get('entry_armed')}` / `{scalp_sim.get('buy_filled')}` / `{scalp_sim.get('sell_completed')}`",
        f"- expired/unpriced/duplicate: `{scalp_sim.get('entry_expired')}` / `{scalp_sim.get('entry_unpriced')}` / `{scalp_sim.get('duplicate_buy_signal')}`",
        f"- entry_ai_price applied/skip: `{scalp_sim.get('entry_ai_price_applied')}` / `{scalp_sim.get('entry_ai_price_skip_order')}`",
        f"- submit_revalidation warning/block: `{scalp_sim.get('entry_submit_revalidation_warning')}` / `{scalp_sim.get('entry_submit_revalidation_block')}`",
        f"- scale_in filled/unfilled: `{scalp_sim.get('scale_in_filled')}` / `{scalp_sim.get('scale_in_unfilled')}`",
        f"- overnight decision/sell/hold/carry_restored: `{scalp_sim.get('overnight_decision')}` / `{scalp_sim.get('overnight_sell_today')}` / `{scalp_sim.get('overnight_hold')}` / `{scalp_sim.get('overnight_carry_restored')}`",
        f"- completed_profit_summary: `{scalp_sim.get('completed_profit_summary') or {}}`",
        f"- post_sell_join: joined=`{sim_post_sell.get('joined_completed')}` / pending=`{sim_post_sell.get('pending_completed')}`",
        f"- post_sell_mfe_mae_10m: mfe=`{sim_post_sell.get('avg_mfe_10m_pct')}`% / mae=`{sim_post_sell.get('avg_mae_10m_pct')}`% / close=`{sim_post_sell.get('avg_close_10m_pct')}`%",
        "",
        "## Missed Probe Counterfactual",
        f"- book: `{missed_probe.get('book') or '-'}` / role: `{missed_probe.get('role') or '-'}`",
        f"- total/score65_74: `{missed_probe.get('total_candidates')}` / `{missed_probe.get('score65_74_probe_candidates')}`",
        f"- avg_expected_ev: `{missed_probe.get('avg_expected_ev_pct')}`% / score65_74_avg_expected_ev: `{missed_probe.get('score65_74_avg_expected_ev_pct')}`%",
        f"- actual_order_submitted: `{missed_probe.get('actual_order_submitted')}` / broker_order_forbidden: `{missed_probe.get('broker_order_forbidden')}`",
        f"- authority: `{missed_probe.get('calibration_authority') or '-'}`",
        "",
        "## Scalp Entry ADM",
        f"- artifact: `{scalp_entry_adm.get('artifact') or '-'}`",
        f"- status: `{scalp_entry_adm.get('status')}` / authority: `{scalp_entry_adm.get('decision_authority') or '-'}`",
        f"- total/joined/floor: `{scalp_entry_adm.get('total_candidates')}` / `{scalp_entry_adm.get('joined_sample')}` / `{scalp_entry_adm.get('sample_floor')}`",
        f"- prompt_applied_count: `{scalp_entry_adm.get('prompt_applied_count')}`",
        f"- runtime_bias_applied_count: `{scalp_entry_adm.get('runtime_bias_applied_count')}`",
        f"- runtime_effect_counts: `{scalp_entry_adm.get('runtime_effect_counts') or {}}`",
        f"- forced_action_counts: `{scalp_entry_adm.get('forced_action_counts') or {}}`",
        f"- missing_actions: `{scalp_entry_adm.get('missing_actions') or []}`",
        f"- zero_sample_actions: `{scalp_entry_adm.get('zero_sample_actions') or []}`",
        f"- top_actions: `{scalp_entry_adm.get('top_actions') or []}`",
        "",
        "## Lifecycle Decision Matrix",
        f"- artifact: `{lifecycle_matrix.get('artifact') or '-'}`",
        f"- status: `{lifecycle_matrix.get('status')}` / version: `{lifecycle_matrix.get('matrix_version') or '-'}`",
        f"- total/joined: `{lifecycle_matrix.get('total_rows')}` / `{lifecycle_matrix.get('joined_rows')}`",
        f"- policy_pass/promote_ready: `{lifecycle_matrix.get('policy_pass_count')}` / `{lifecycle_matrix.get('promote_ready_count')}`",
        f"- lifecycle_flow buckets/complete/runtime/workorders: "
        f"`{lifecycle_matrix.get('lifecycle_flow_bucket_count')}` / "
        f"`{lifecycle_matrix.get('lifecycle_flow_complete_count')}` / "
        f"`{lifecycle_matrix.get('lifecycle_flow_runtime_candidate_count')}` / "
        f"`{lifecycle_matrix.get('lifecycle_flow_workorder_count')}`",
        f"- holding/exit buckets: `{lifecycle_matrix.get('holding_bucket_count')}` / `{lifecycle_matrix.get('exit_bucket_count')}`",
        f"- holding/exit workorders: `{lifecycle_matrix.get('holding_bucket_workorder_count')}` / `{lifecycle_matrix.get('exit_bucket_workorder_count')}`",
        f"- lifecycle identity missing/join_rate: `{lifecycle_matrix.get('identity_missing_count')}` / `{lifecycle_matrix.get('identity_join_rate')}`",
        f"- lifecycle complete_flow_rate: `{lifecycle_matrix.get('complete_flow_rate')}`",
        f"- incomplete_flow_reason_counts: `{lifecycle_matrix.get('incomplete_flow_reason_counts') or {}}`",
        f"- fixed_threshold_roles: `{lifecycle_matrix.get('fixed_threshold_roles') or {}}`",
        f"- policy_entries: `{lifecycle_matrix.get('policy_entries') or []}`",
        "",
        "## Lifecycle Bucket Discovery",
        f"- artifact: `{lifecycle_bucket_discovery.get('artifact') or '-'}`",
        f"- status: `{lifecycle_bucket_discovery.get('status')}` / human_intervention_required: `{lifecycle_bucket_discovery.get('human_intervention_required')}`",
        f"- candidates/surfaced: `{lifecycle_bucket_discovery.get('candidate_count')}` / `{lifecycle_bucket_discovery.get('surfaced_candidate_count')}`",
        f"- sim_auto/live_auto/new_bucket: `{lifecycle_bucket_discovery.get('sim_auto_approved_count')}` / `{lifecycle_bucket_discovery.get('live_auto_apply_ready_count')}` / `{lifecycle_bucket_discovery.get('new_bucket_candidate_count')}`",
        f"- role/window: `{lifecycle_bucket_discovery.get('window_role')}` / `{lifecycle_bucket_discovery.get('window_policy')}`",
        f"- parent_count/granularity/conflict: `{lifecycle_bucket_discovery.get('parent_bucket_count')}` / `{lifecycle_bucket_discovery.get('parent_granularity_status')}` / `{lifecycle_bucket_discovery.get('child_conflict_warning_count')}`",
        f"- state_counts: `{lifecycle_bucket_discovery.get('state_counts') or {}}`",
        f"- top_surfaced: `{lifecycle_bucket_discovery.get('top_surfaced') or []}`",
        "",
        "## Lifecycle Bucket Windows",
        f"- promotion_window: `{(report.get('lifecycle_bucket_windows') or {}).get('promotion_window') if isinstance(report.get('lifecycle_bucket_windows'), dict) else '-'}`",
        f"- confirmation_windows: `{(report.get('lifecycle_bucket_windows') or {}).get('confirmation_windows') if isinstance(report.get('lifecycle_bucket_windows'), dict) else []}`",
        f"- windows: `{(report.get('lifecycle_bucket_windows') or {}).get('windows') if isinstance(report.get('lifecycle_bucket_windows'), dict) else {}}`",
        "",
        "## Lifecycle AI Context",
        f"- artifact: `{lifecycle_ai_context.get('artifact') or '-'}`",
        f"- context_version: `{lifecycle_ai_context.get('context_version') or '-'}` / authority: `{lifecycle_ai_context.get('decision_authority') or '-'}`",
        f"- prompt_stage_count: `{lifecycle_ai_context.get('prompt_stage_count')}` / runtime_effect: `{lifecycle_ai_context.get('runtime_effect')}`",
        f"- stage_contexts: `{lifecycle_ai_context.get('stage_contexts') or []}`",
        "",
        "## Lifecycle AI Context Attribution",
        f"- artifact: `{lifecycle_ai_context_attribution.get('artifact') or '-'}`",
        f"- eligible/applied/skipped: `{lifecycle_ai_context_attribution.get('context_eligible_count')}` / `{lifecycle_ai_context_attribution.get('context_applied_count')}` / `{lifecycle_ai_context_attribution.get('context_skipped_count')}`",
        f"- replay_budget: `{lifecycle_ai_context_attribution.get('replay_budget')}`",
        f"- implementation_status: `{lifecycle_ai_context_attribution.get('implementation_status') or '-'}`",
        f"- stage_attribution: `{lifecycle_ai_context_attribution.get('stage_attribution') or {}}`",
        "",
        "## Institutional Flow Context",
        f"- artifact: `{institutional_flow.get('artifact') or '-'}`",
        f"- status: `{institutional_flow.get('status')}` / authority: `{institutional_flow.get('decision_authority') or '-'}`",
        f"- rows ok/partial/missing/token_error: `{institutional_flow.get('ok_count')}` / `{institutional_flow.get('partial_count')}` / `{institutional_flow.get('missing_count')}` / `{institutional_flow.get('token_error_count')}`",
        f"- join_rate_pct: `{institutional_flow.get('join_rate_pct')}`",
        f"- source_mix: `{institutional_flow.get('source_mix') or {}}`",
        f"- top_net_buy: `{institutional_flow.get('top_net_buy') or []}`",
        "",
        "## Pattern Lab Automation",
        f"- artifact: `{pattern_lab.get('artifact') or '-'}`",
        f"- fresh: gemini=`{pattern_lab.get('gemini_fresh')}` claude=`{pattern_lab.get('claude_fresh')}`",
        f"- consensus/orders/family_candidates: `{pattern_lab.get('consensus_count')}` / `{pattern_lab.get('code_improvement_order_count')}` / `{pattern_lab.get('auto_family_candidate_count')}`",
        "",
        "## Swing Pattern Lab Automation",
        f"- artifact: `{swing_lab.get('artifact') or '-'}`",
        f"- deepseek_lab_available: `{swing_lab.get('deepseek_lab_available')}`",
        f"- findings/orders: `{swing_lab.get('findings_count')}` / `{swing_lab.get('code_improvement_order_count')}`",
        f"- data_quality_warnings: `{swing_lab.get('data_quality_warning_count')}`",
        f"- top_level_data_quality_warnings: `{swing_lab.get('top_level_data_quality_warning_count')}`",
        f"- resolved_data_quality_warnings: `{swing_lab.get('resolved_data_quality_warning_count')}`",
        f"- ofi_qi_stale_missing_unique_records: `{((swing_lab.get('ofi_qi_quality') or {}).get('stale_missing_unique_record_count')) or 0}`",
        f"- ofi_qi_stale_missing_reasons: `{((swing_lab.get('ofi_qi_quality') or {}).get('reason_counts')) or {}}`",
        f"- ofi_qi_stale_missing_reason_combinations: `{((swing_lab.get('ofi_qi_quality') or {}).get('reason_combination_counts')) or {}}`",
        f"- ofi_qi_stale_missing_reason_combination_unique_records: `{((swing_lab.get('ofi_qi_quality') or {}).get('reason_combination_unique_record_counts')) or {}}`",
        f"- ofi_qi_observer_unhealthy_overlap: `{((swing_lab.get('ofi_qi_quality') or {}).get('observer_unhealthy_overlap')) or {}}`",
        f"- source_quality_blocked_families: `{swing_lab.get('source_quality_blocked_families') or []}`",
        f"- carryover_warnings: `{swing_lab.get('carryover_warning_count')}`",
        f"- population_split_available: `{swing_lab.get('population_split_available')}`",
        "",
        "## Swing Strategy Discovery Sim",
        f"- artifact: `{swing_discovery.get('artifact') or '-'}`",
        f"- authority: `{swing_discovery.get('decision_authority') or '-'}` / source_only: `{swing_discovery.get('source_only')}`",
        f"- candidate/arm/policy_exit_rows: `{swing_discovery.get('candidate_count')}` / `{swing_discovery.get('arm_count')}` / `{swing_discovery.get('policy_exit_row_count')}`",
        f"- labeled/pending_future_quotes: `{swing_discovery.get('labeled_sample_count')}` / `{swing_discovery.get('pending_future_quote_count')}`",
        f"- implementation_status: `{swing_discovery.get('implementation_status') or '-'}`",
        f"- top_surviving_arm: `{swing_discovery.get('top_surviving_arm') or '-'}`",
        f"- surviving/avoid_bucket_count: `{swing_discovery.get('surviving_arm_count')}` / `{swing_discovery.get('avoid_bucket_count')}`",
        f"- runtime_effect: `{swing_discovery.get('runtime_effect')}`",
        "",
        "## Pipeline Event Verbosity",
        f"- artifact: `{pipeline_verbosity.get('artifact') or '-'}`",
        f"- state: `{pipeline_verbosity.get('state') or '-'}`",
        f"- recommended_workorder_state: `{pipeline_verbosity.get('recommended_workorder_state') or '-'}`",
        f"- high_volume_line_count: `{pipeline_verbosity.get('high_volume_line_count')}`",
        f"- high_volume_byte_share_pct: `{pipeline_verbosity.get('high_volume_byte_share_pct')}`",
        f"- parity_ok: `{pipeline_verbosity.get('parity_ok')}`",
        f"- suppress_eligibility: `{pipeline_verbosity.get('suppress_eligibility')}`",
        "",
        "## Codebase Performance Workorder Source",
        f"- artifact: `{codebase_perf.get('artifact') or '-'}`",
        f"- authority: `{codebase_perf.get('decision_authority') or '-'}`",
        f"- accepted/deferred/rejected: `{codebase_perf.get('accepted_count')}` / `{codebase_perf.get('deferred_count')}` / `{codebase_perf.get('rejected_count')}`",
        f"- runtime_effect: `{codebase_perf.get('runtime_effect')}`",
        f"- strategy_effect: `{codebase_perf.get('strategy_effect')}`",
        f"- data_quality_effect: `{codebase_perf.get('data_quality_effect')}`",
        f"- tuning_axis_effect: `{codebase_perf.get('tuning_axis_effect')}`",
        "",
        "## Pattern Lab Audits",
        f"- currentness: status=`{currentness_audit.get('status')}` fail=`{currentness_audit.get('fail_count')}` orders=`{currentness_audit.get('code_improvement_order_count')}` artifact=`{currentness_audit.get('artifact') or '-'}`",
        f"- ai_review: status=`{pattern_lab_ai_review.get('status')}` orders=`{pattern_lab_ai_review.get('code_improvement_order_count')}` artifact=`{pattern_lab_ai_review.get('artifact') or '-'}`",
        f"- time_window_regime_counterfactual: status=`{(report.get('time_window_regime_counterfactual') or {}).get('status')}` artifact=`{(report.get('time_window_regime_counterfactual') or {}).get('artifact') or '-'}`",
        f"- producer_gap_discovery: status=`{producer_gap_discovery.get('status')}` orders=`{producer_gap_discovery.get('code_improvement_order_count')}` artifact=`{producer_gap_discovery.get('artifact') or '-'}`",
        f"- stage_hook_workorder_discovery: status=`{(report.get('stage_hook_workorder_discovery') or {}).get('status')}` orders=`{(report.get('stage_hook_workorder_discovery') or {}).get('code_improvement_order_count')}` artifact=`{(report.get('stage_hook_workorder_discovery') or {}).get('artifact') or '-'}`",
        f"- propagation: status=`{propagation_audit.get('status')}` fail=`{propagation_audit.get('fail_count')}` warnings=`{propagation_audit.get('warning_count')}` artifact=`{propagation_audit.get('artifact') or '-'}`",
        "",
        "## Swing Runtime Approval",
        f"- request_report: `{swing_runtime.get('request_report') or '-'}`",
        f"- approval_artifact: `{swing_runtime.get('approval_artifact') or '-'}`",
        f"- requested/approved/live_dry_run: `{swing_runtime.get('requested')}` / `{swing_runtime.get('approved')}` / `{swing_runtime.get('selected_live_dry_run')}`",
        f"- dry_run_forced: `{swing_runtime.get('dry_run_forced')}`",
        f"- legacy_phase0_real_canary_ignored: `{swing_runtime.get('legacy_phase0_real_canary_ignored')}`",
        f"- blocked: `{swing_runtime.get('blocked') or []}`",
        "",
        "## Code Improvement Workorder",
        f"- artifact: `{code_workorder.get('artifact') or '-'}`",
        f"- markdown: `{code_workorder.get('markdown') or '-'}`",
        f"- selected_order_count: `{code_workorder.get('selected_order_count')}`",
        f"- decision_counts: `{code_workorder.get('decision_counts')}`",
        "",
        "## Approval Requests",
    ]
    if approval_requests:
        for item in approval_requests:
            if isinstance(item, dict):
                lines.append(
                    f"- `{item.get('family')}` sample=`{item.get('sample_count')}/{item.get('sample_floor')}` "
                    f"reason=`{item.get('calibration_reason')}` "
                    f"contract=`{item.get('approval_contract_status')}` "
                    f"live_ready=`{item.get('approval_live_ready')}`"
                )
    else:
        lines.append("- none")
    swing_requests = swing_runtime.get("requests") if isinstance(swing_runtime.get("requests"), list) else []
    lines.extend(["", "## Swing Approval Requests"])
    if swing_requests:
        for item in swing_requests:
            if isinstance(item, dict):
                lines.append(
                    f"- `{item.get('family')}` approval_id=`{item.get('approval_id')}` "
                    f"score=`{item.get('tradeoff_score')}` target_env_keys=`{item.get('target_env_keys')}`"
                )
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Calibration Decisions",
        ]
    )
    top_orders = code_workorder.get("top_orders") if isinstance(code_workorder.get("top_orders"), list) else []
    if top_orders:
        lines.extend(["## Code Improvement Top Orders"])
        for item in top_orders[:3]:
            if isinstance(item, dict):
                lines.append(
                    f"- `{item.get('order_id')}` decision=`{item.get('decision')}` subsystem=`{item.get('target_subsystem')}`"
                )
        lines.append("")
    top_findings = pattern_lab.get("top_consensus_findings") if isinstance(pattern_lab.get("top_consensus_findings"), list) else []
    if top_findings:
        lines.extend(["## Pattern Lab Top Findings"])
        for item in top_findings[:3]:
            if isinstance(item, dict):
                lines.append(
                    f"- `{item.get('title')}` route=`{item.get('route')}` family=`{item.get('mapped_family') or '-'}`"
                )
        lines.append("")
    if decisions:
        for item in decisions:
            if not isinstance(item, dict):
                continue
            lines.append(
                f"- `{item.get('family')}`: `{item.get('calibration_state')}` "
                f"sample=`{item.get('sample_count')}/{item.get('sample_floor')}`"
            )
    else:
        lines.append("- no calibration decisions")
    warnings = report.get("warnings") if isinstance(report.get("warnings"), list) else []
    if warnings:
        lines.extend(["", "## Warnings"])
        lines.extend([f"- `{warning}`" for warning in warnings])
    if source_load_diagnostics:
        lines.extend(["", "## Source Load Diagnostics"])
        for item in source_load_diagnostics:
            if not isinstance(item, dict):
                continue
            lines.append(
                f"- `{Path(str(item.get('path') or '')).name}`: `{item.get('status')}` "
                f"error=`{item.get('error') or item.get('type') or '-'}`"
            )
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build threshold-cycle daily EV performance report.")
    parser.add_argument("--date", dest="target_date", default=date.today().isoformat())
    args = parser.parse_args(argv)
    report = build_threshold_cycle_ev_report(args.target_date)
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
