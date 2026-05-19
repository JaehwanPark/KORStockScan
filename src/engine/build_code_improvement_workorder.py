"""Build Codex-ready code improvement workorders from postclose automation."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = PROJECT_ROOT / "data" / "report"
PATTERN_LAB_AUTOMATION_DIR = REPORT_DIR / "scalping_pattern_lab_automation"
SWING_IMPROVEMENT_AUTOMATION_DIR = REPORT_DIR / "swing_improvement_automation"
SWING_PATTERN_LAB_AUTOMATION_DIR = REPORT_DIR / "swing_pattern_lab_automation"
SWING_STRATEGY_DISCOVERY_EV_DIR = REPORT_DIR / "swing_strategy_discovery_ev"
THRESHOLD_CYCLE_EV_DIR = REPORT_DIR / "threshold_cycle_ev"
PIPELINE_EVENT_VERBOSITY_DIR = REPORT_DIR / "pipeline_event_verbosity"
OBSERVATION_SOURCE_QUALITY_AUDIT_DIR = REPORT_DIR / "observation_source_quality_audit"
CODEBASE_PERFORMANCE_WORKORDER_DIR = REPORT_DIR / "codebase_performance_workorder"
PATTERN_LAB_CURRENTNESS_AUDIT_DIR = REPORT_DIR / "pattern_lab_currentness_audit"
CODE_IMPROVEMENT_WORKORDER_DIR = PROJECT_ROOT / "docs" / "code-improvement-workorders"
CODE_IMPROVEMENT_WORKORDER_REPORT_DIR = REPORT_DIR / "code_improvement_workorder"
WORKORDER_SCHEMA_VERSION = 1


DECISION_RANK = {
    "implement_now": 0,
    "attach_existing_family": 1,
    "design_family_candidate": 2,
    "defer_evidence": 3,
    "reject": 4,
}


@dataclass(frozen=True)
class ClassifiedOrder:
    order: dict[str, Any]
    decision: str
    reason: str
    mapped_family: str | None
    route: str | None
    confidence: str | None
    automation_reentry: str


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _file_fingerprint(path: Path, label: str) -> dict[str, Any]:
    exists = path.exists()
    payload = b""
    if exists:
        try:
            payload = path.read_bytes()
        except OSError:
            payload = b""
    stat = path.stat() if exists else None
    return {
        "label": label,
        "path": str(path),
        "exists": bool(exists),
        "size_bytes": int(stat.st_size) if stat else 0,
        "mtime_ns": int(stat.st_mtime_ns) if stat else None,
        "sha256": hashlib.sha256(payload).hexdigest() if exists else None,
    }


def _source_fingerprint(source_paths: dict[str, Path]) -> dict[str, Any]:
    files = [_file_fingerprint(path, label) for label, path in sorted(source_paths.items())]
    hash_input = json.dumps(files, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    source_hash = hashlib.sha256(hash_input).hexdigest()
    return {
        "source_hash": source_hash,
        "generation_id": source_hash[:12],
        "files": files,
    }


def _previous_workorder_lineage(previous_report: dict[str, Any], current_orders: list[dict[str, Any]]) -> dict[str, Any]:
    previous_orders = previous_report.get("orders") if isinstance(previous_report.get("orders"), list) else []
    previous_by_id = {
        str(order.get("order_id")): order
        for order in previous_orders
        if isinstance(order, dict) and order.get("order_id") not in (None, "")
    }
    current_by_id = {
        str(order.get("order_id")): order
        for order in current_orders
        if isinstance(order, dict) and order.get("order_id") not in (None, "")
    }
    previous_ids = set(previous_by_id)
    current_ids = set(current_by_id)
    decision_changed = sorted(
        order_id
        for order_id in previous_ids & current_ids
        if previous_by_id[order_id].get("decision") != current_by_id[order_id].get("decision")
    )
    return {
        "previous_exists": bool(previous_report),
        "previous_generation_id": previous_report.get("generation_id"),
        "previous_source_hash": previous_report.get("source_hash"),
        "previous_generated_at": previous_report.get("generated_at"),
        "new_order_ids": sorted(current_ids - previous_ids),
        "removed_order_ids": sorted(previous_ids - current_ids),
        "unchanged_order_ids": sorted(current_ids & previous_ids),
        "decision_changed_order_ids": decision_changed,
    }


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _slug(value: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9가-힣]+", "_", str(value or "").strip().lower()).strip("_")
    return text[:80] or "unknown"


def _next_calendar_day(target_date: str) -> str:
    try:
        return (date.fromisoformat(target_date) + timedelta(days=1)).isoformat()
    except ValueError:
        return target_date


def automation_report_path(target_date: str) -> Path:
    return PATTERN_LAB_AUTOMATION_DIR / f"scalping_pattern_lab_automation_{target_date}.json"


def swing_automation_report_path(target_date: str) -> Path:
    return SWING_IMPROVEMENT_AUTOMATION_DIR / f"swing_improvement_automation_{target_date}.json"


def swing_pattern_lab_automation_report_path(target_date: str) -> Path:
    return SWING_PATTERN_LAB_AUTOMATION_DIR / f"swing_pattern_lab_automation_{target_date}.json"


def threshold_ev_report_path(target_date: str) -> Path:
    return THRESHOLD_CYCLE_EV_DIR / f"threshold_cycle_ev_{target_date}.json"


def swing_strategy_discovery_ev_report_path(target_date: str) -> Path:
    return SWING_STRATEGY_DISCOVERY_EV_DIR / f"swing_strategy_discovery_ev_{target_date}.json"


def code_improvement_workorder_paths(target_date: str) -> tuple[Path, Path]:
    base = f"code_improvement_workorder_{target_date}"
    return (
        CODE_IMPROVEMENT_WORKORDER_REPORT_DIR / f"{base}.json",
        CODE_IMPROVEMENT_WORKORDER_DIR / f"{base}.md",
    )


def pattern_lab_currentness_audit_report_path(target_date: str) -> Path:
    return PATTERN_LAB_CURRENTNESS_AUDIT_DIR / f"pattern_lab_currentness_audit_{target_date}.json"


def _finding_maps(report: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    by_order_id: dict[str, dict[str, Any]] = {}
    by_title_slug: dict[str, dict[str, Any]] = {}
    for section in ("consensus_findings", "solo_findings"):
        for finding in report.get(section) or []:
            if not isinstance(finding, dict):
                continue
            finding_id = str(finding.get("finding_id") or "").strip()
            title = str(finding.get("title") or "").strip()
            if finding_id:
                by_order_id[f"order_{finding_id}"] = finding
            if title:
                by_title_slug[_slug(title)] = finding
    return by_order_id, by_title_slug


def _auto_family_order_ids(report: dict[str, Any]) -> set[str]:
    result: set[str] = set()
    for item in report.get("auto_family_candidates") or []:
        if not isinstance(item, dict):
            continue
        implementation_id = str(item.get("implementation_order_id") or "").strip()
        if implementation_id:
            result.add(implementation_id)
        family_id = str(item.get("family_id") or "").strip()
        if family_id:
            result.add(f"order_{family_id}")
    return result


def _contains_any(text: str, tokens: tuple[str, ...]) -> bool:
    lower = text.lower()
    return any(token in lower for token in tokens)


def _classify_order(
    order: dict[str, Any],
    *,
    finding_by_order_id: dict[str, dict[str, Any]],
    finding_by_title_slug: dict[str, dict[str, Any]],
    auto_family_order_ids: set[str],
    closed_instrumentation_order_families: dict[str, str],
) -> ClassifiedOrder:
    order_id = str(order.get("order_id") or "").strip()
    title = str(order.get("title") or "").strip()
    subsystem = str(order.get("target_subsystem") or "").strip()
    text = f"{order_id} {title} {subsystem}"
    finding = finding_by_order_id.get(order_id) or finding_by_title_slug.get(_slug(title)) or {}
    route = str(finding.get("route") or order.get("route") or "").strip() or None
    mapped_family = str(finding.get("mapped_family") or order.get("mapped_family") or "").strip() or None
    confidence = str(finding.get("confidence") or order.get("confidence") or "").strip() or None
    closed_family = closed_instrumentation_order_families.get(order_id)
    if closed_family:
        return ClassifiedOrder(
            order=order,
            decision="attach_existing_family",
            reason="instrumentation/provenance contract is already implemented; keep as report source for the existing family",
            mapped_family=closed_family,
            route="existing_family",
            confidence=confidence,
            automation_reentry="Next postclose calibration consumes the implemented report/provenance fields; no runtime mutation.",
        )

    if bool(order.get("runtime_effect")):
        return ClassifiedOrder(
            order=order,
            decision="reject",
            reason="automation order must remain runtime_effect=false; runtime_effect=true is treated as artifact error",
            mapped_family=mapped_family,
            route=route,
            confidence=confidence,
            automation_reentry="Reject artifact and regenerate the source automation report before implementation.",
        )

    if (
        str(order.get("implementation_status") or "").strip() == "implemented"
        and order.get("source_report_type") != "codebase_performance_workorder"
    ):
        return ClassifiedOrder(
            order=order,
            decision="attach_existing_family",
            reason=(
                "instrumentation/report/provenance implementation is already present; keep the order as "
                "existing-family source evidence instead of re-implementing"
            ),
            mapped_family=mapped_family or str(order.get("threshold_family") or "").strip() or None,
            route="existing_family",
            confidence=confidence,
            automation_reentry=(
                "Next postclose workorder should preserve implementation_status=implemented and use the "
                "source metrics as provenance only."
            ),
        )

    if order.get("source_report_type") == "pipeline_event_verbosity":
        return ClassifiedOrder(
            order=order,
            decision="implement_now",
            reason="pipeline event compaction V2 is report-only instrumentation; shadow means producer-summary observe mode, not trading shadow",
            mapped_family=mapped_family,
            route=route or "instrumentation_order",
            confidence=confidence,
            automation_reentry="Next postclose pipeline_event_verbosity report must show producer summary freshness and parity status.",
        )

    if order.get("source_report_type") == "codebase_performance_workorder":
        if str(order.get("implementation_status") or "").strip() == "implemented":
            return ClassifiedOrder(
                order=order,
                decision="attach_existing_family",
                reason=(
                    "report-only performance implementation is already present in code; keep the order as provenance "
                    "and validate through regenerated reports/tests instead of re-implementing"
                ),
                mapped_family=mapped_family or "ops_performance_report_only_implemented",
                route=route or "existing_report_only_implementation",
                confidence=confidence,
                automation_reentry="Next postclose codebase performance source report must keep implementation_status=implemented and parity tests green.",
            )
        state = str(order.get("performance_candidate_state") or order.get("candidate_state") or "").strip()
        if state == "accepted":
            return ClassifiedOrder(
                order=order,
                decision="implement_now",
                reason="accepted codebase performance order is logic-preserving and report/workorder-only; implementation still requires parity tests",
                mapped_family=mapped_family,
                route=route or "performance_optimization_order",
                confidence=confidence,
                automation_reentry="After implementation, rerun the same artifact/report parity tests before postclose workorder refresh.",
            )
        if state == "deferred":
            return ClassifiedOrder(
                order=order,
                decision="defer_evidence",
                reason=str(order.get("defer_reason") or "performance order requires manual review before implementation"),
                mapped_family=mapped_family,
                route=route or "performance_optimization_order",
                confidence=confidence,
                automation_reentry="Keep as deferred performance backlog until scope/risk is reviewed separately.",
            )
        return ClassifiedOrder(
            order=order,
            decision="reject",
            reason=str(order.get("defer_reason") or "performance order is outside current no-logic-change scope"),
            mapped_family=mapped_family,
            route=route or "performance_optimization_order",
            confidence=confidence,
            automation_reentry="Do not implement from this workorder source.",
        )

    if order.get("source_report_type") == "pattern_lab_currentness_audit":
        return ClassifiedOrder(
            order=order,
            decision="implement_now",
            reason="pattern lab currentness order is report/source-quality instrumentation only and must remain runtime_effect=false",
            mapped_family=mapped_family,
            route=route or "instrumentation_order",
            confidence=confidence or "consensus",
            automation_reentry="After implementation, rerun pattern labs, currentness audit, workorder, EV, and propagation audit.",
        )

    if _contains_any(text, ("fallback", "shadow")):
        return ClassifiedOrder(
            order=order,
            decision="reject",
            reason="fallback revival or shadow reintroduction conflicts with current Plan Rebase policy",
            mapped_family=mapped_family,
            route=route,
            confidence=confidence,
            automation_reentry="Keep as rejected finding unless translated into report_only_calibration or bounded canary design.",
        )

    if confidence == "solo":
        return ClassifiedOrder(
            order=order,
            decision="defer_evidence",
            reason="single-lab finding; keep as low-confidence backlog until repeated by fresh lab or EV report",
            mapped_family=mapped_family,
            route=route,
            confidence=confidence,
            automation_reentry="Re-evaluate in the next postclose pattern lab automation and daily EV report.",
        )

    if subsystem == "runtime_instrumentation" or route == "instrumentation_order":
        return ClassifiedOrder(
            order=order,
            decision="implement_now",
            reason="instrumentation/provenance work can improve attribution without direct runtime mutation",
            mapped_family=mapped_family,
            route=route,
            confidence=confidence,
            automation_reentry="After implementation, next postclose report must show source freshness or warning reduction.",
        )

    if route == "existing_family" or mapped_family:
        return ClassifiedOrder(
            order=order,
            decision="attach_existing_family",
            reason="finding maps to an existing threshold family and should strengthen source metrics/provenance",
            mapped_family=mapped_family,
            route=route,
            confidence=confidence,
            automation_reentry="After implementation, intraday/postclose calibration should include the updated family input.",
        )

    if route == "auto_family_candidate" or order_id in auto_family_order_ids:
        return ClassifiedOrder(
            order=order,
            decision="design_family_candidate",
            reason="finding needs family design; allowed_runtime_apply remains false until metadata/tests/guards are closed",
            mapped_family=mapped_family,
            route=route,
            confidence=confidence,
            automation_reentry="Create report-only family metadata first; only later can auto_bounded_live consider it.",
        )

    return ClassifiedOrder(
        order=order,
        decision="defer_evidence",
        reason="route is not strong enough for immediate implementation",
        mapped_family=mapped_family,
        route=route,
        confidence=confidence,
        automation_reentry="Keep in generated workorder as deferred context and re-check after next daily EV report.",
    )


def _sort_classified(items: list[ClassifiedOrder]) -> list[ClassifiedOrder]:
    return sorted(
        items,
        key=lambda item: (
            DECISION_RANK.get(item.decision, 99),
            _safe_int(item.order.get("priority"), 999),
            str(item.order.get("order_id") or ""),
        ),
    )


def _threshold_ev_followup_orders(ev_report: dict[str, Any]) -> list[dict[str, Any]]:
    outcome = ev_report.get("calibration_outcome") if isinstance(ev_report.get("calibration_outcome"), dict) else {}
    decisions = outcome.get("decisions") if isinstance(outcome.get("decisions"), list) else []
    orders: list[dict[str, Any]] = []
    for item in decisions:
        if not isinstance(item, dict):
            continue
        family = str(item.get("family") or "").strip()
        state = str(item.get("calibration_state") or "").strip()
        if family != "holding_exit_decision_matrix_advisory" or state != "hold_no_edge":
            continue
        source_metrics = item.get("source_metrics") if isinstance(item.get("source_metrics"), dict) else {}
        if source_metrics.get("instrumentation_status") == "implemented":
            continue
        counterfactual_gap_count = _safe_int(source_metrics.get("counterfactual_gap_count"), 0)
        proxy_sample_snapshots = _safe_int(source_metrics.get("eligible_but_not_chosen_sample_snapshots"), 0)
        proxy_joined_candidates = _safe_int(
            source_metrics.get("eligible_but_not_chosen_post_sell_joined_candidates"),
            0,
        )
        proxy_missing_actions = (
            list(source_metrics.get("counterfactual_proxy_missing_actions") or [])
            if isinstance(source_metrics.get("counterfactual_proxy_missing_actions"), list)
            else []
        )
        instrumentation_gap = not source_metrics or (
            counterfactual_gap_count > 0 or proxy_sample_snapshots <= 0 or proxy_joined_candidates <= 0
        )
        if not instrumentation_gap:
            continue
        evidence = [
            "calibration_state=hold_no_edge",
            f"sample_count={item.get('sample_count')}",
            f"sample_floor={item.get('sample_floor')}",
        ]
        if source_metrics:
            evidence.extend(
                [
                    f"counterfactual_gap_count={counterfactual_gap_count}",
                    f"eligible_snapshot_count={proxy_sample_snapshots}",
                    f"eligible_joined_candidates={proxy_joined_candidates}",
                ]
            )
            if proxy_missing_actions:
                evidence.append(f"proxy_missing_actions={','.join(str(value) for value in proxy_missing_actions)}")
        orders.append(
            {
                "order_id": "order_holding_exit_decision_matrix_edge_counterfactual",
                "title": "holding exit decision matrix edge counterfactual coverage",
                "source_report_type": "threshold_cycle_ev",
                "lifecycle_stage": "holding_exit",
                "target_subsystem": "runtime_instrumentation",
                "route": "instrumentation_order",
                "mapped_family": family,
                "threshold_family": family,
                "improvement_type": "instrumentation",
                "confidence": "consensus",
                "priority": 4,
                "runtime_effect": False,
                "expected_ev_effect": "Break hold_no_edge by separating exit_only/hold_defer/avg_down/pyramid counterfactual outcomes.",
                "evidence": evidence,
                "next_postclose_metric": "holding_exit_decision_matrix_advisory should report per-action edge buckets, non_no_clear_edge_count, and counterfactual coverage.",
                "files_likely_touched": [
                    "src/engine/daily_threshold_cycle_report.py",
                    "src/engine/holding_exit_decision_matrix.py",
                    "src/engine/statistical_action_weight.py",
                ],
                "acceptance_tests": [
                    "pytest holding exit decision matrix/report tests",
                    "threshold EV report includes per-action counterfactual coverage",
                ],
            }
        )
    return orders


def _entry_adm_followup_orders(ev_report: dict[str, Any]) -> list[dict[str, Any]]:
    adm = (
        ev_report.get("scalp_entry_action_decision_matrix")
        if isinstance(ev_report.get("scalp_entry_action_decision_matrix"), dict)
        else {}
    )
    if not adm:
        return []
    joined = _safe_int(adm.get("joined_sample"), 0)
    floor = _safe_int(adm.get("sample_floor"), 20)
    missing_actions = adm.get("missing_actions") if isinstance(adm.get("missing_actions"), list) else []
    prompt_applied_count = _safe_int(adm.get("prompt_applied_count"), 0)
    issues: list[str] = []
    if joined < floor:
        issues.append("joined_sample_below_sample_floor")
    if missing_actions:
        issues.append("missing_action_bucket")
    if prompt_applied_count <= 0:
        issues.append("prompt_context_not_loaded")
    if str(adm.get("status") or "").lower() == "missing":
        issues.append("source_quality_gap")
    if not issues:
        return []
    sources = ev_report.get("sources") if isinstance(ev_report.get("sources"), dict) else {}
    evidence = [
        f"status={adm.get('status')}",
        f"joined_sample={joined}",
        f"sample_floor={floor}",
        f"prompt_applied_count={prompt_applied_count}",
    ]
    if missing_actions:
        evidence.append("missing_actions=" + ",".join(str(value) for value in missing_actions))
    source_path = sources.get("scalp_entry_action_decision_matrix") or adm.get("artifact")
    return [
        {
            "order_id": "order_scalp_entry_adm_daily_tuning_coverage",
            "title": "scalp entry ADM daily tuning coverage",
            "source_report_type": "threshold_cycle_ev",
            "lifecycle_stage": "entry",
            "target_subsystem": "entry_funnel",
            "route": "instrumentation_order",
            "mapped_family": "scalp_entry_action_decision_matrix_advisory",
            "threshold_family": "scalp_entry_action_decision_matrix_advisory",
            "improvement_type": "instrumentation_report_provenance",
            "confidence": "consensus",
            "priority": 3,
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "expected_ev_effect": "Keep BUY_NOW/WAIT_REQUOTE/SKIP_STALE/BUY_DEFENSIVE/NO_BUY_AI/SKIP_SOURCE_QUALITY/SKIP_PRE_SUBMIT_SAFETY action buckets joined to post-sell outcomes and runtime forced_action provenance for daily entry policy tuning.",
            "evidence": evidence,
            "source_paths": [str(source_path)] if source_path else [],
            "next_postclose_metric": "scalp_entry_action_decision_matrix should meet sample_floor, include all action buckets, show prompt_applied_count, and expose entry_adm_runtime_effect/forced_action evidence when runtime bias env is enabled.",
            "files_likely_touched": [
                "src/engine/scalp_entry_action_decision_matrix.py",
                "src/engine/sniper_state_handlers.py",
                "src/engine/scalp_entry_adm_runtime.py",
                "src/engine/threshold_cycle_ev_report.py",
            ],
            "acceptance_tests": [
                "PYTHONPATH=. .venv/bin/pytest src/tests/test_scalp_entry_action_decision_matrix.py src/tests/test_build_code_improvement_workorder.py",
                "runtime_effect remains false and broker submit safety guards remain owner",
            ],
            "adm_issue_types": issues,
        }
    ]


def _pipeline_event_verbosity_report_path(target_date: str) -> Path:
    return PIPELINE_EVENT_VERBOSITY_DIR / f"pipeline_event_verbosity_{target_date}.json"


def _observation_source_quality_audit_path(target_date: str) -> Path:
    return OBSERVATION_SOURCE_QUALITY_AUDIT_DIR / f"observation_source_quality_audit_{target_date}.json"


def _codebase_performance_report_path(target_date: str) -> Path:
    return CODEBASE_PERFORMANCE_WORKORDER_DIR / f"codebase_performance_workorder_{target_date}.json"


def _pipeline_event_verbosity_followup_orders(report: dict[str, Any]) -> list[dict[str, Any]]:
    if not report:
        return []
    state = str(report.get("state") or "").strip()
    recommended = str(report.get("recommended_workorder_state") or "").strip()
    raw_stream = report.get("raw_stream") if isinstance(report.get("raw_stream"), dict) else {}
    parity = report.get("parity") if isinstance(report.get("parity"), dict) else {}
    producer = report.get("producer_summary") if isinstance(report.get("producer_summary"), dict) else {}
    evidence = [
        f"state={state}",
        f"recommended_workorder_state={recommended}",
        f"raw_size_bytes={raw_stream.get('raw_size_bytes')}",
        f"high_volume_line_count={raw_stream.get('high_volume_line_count')}",
        f"high_volume_byte_share_pct={raw_stream.get('high_volume_byte_share_pct')}",
        f"producer_summary_exists={producer.get('exists')}",
        f"parity_ok={parity.get('ok')}",
        f"raw_derived_event_count={parity.get('raw_derived_event_count')}",
        f"producer_event_count={parity.get('producer_event_count')}",
    ]
    base = {
        "source_report_type": "pipeline_event_verbosity",
        "lifecycle_stage": "ops_volume_diagnostic",
        "target_subsystem": "runtime_instrumentation",
        "runtime_effect": False,
        "route": "instrumentation_order",
        "confidence": "consensus",
        "expected_ev_effect": "none_direct_ops_cpu_io_reduction_only",
        "next_postclose_metric": "pipeline_event_verbosity.parity.ok",
    }
    if recommended in {"open_shadow_order", "block_suppress_and_fix_shadow"}:
        return [
            {
                **base,
                "order_id": "order_pipeline_event_compaction_v2_shadow",
                "title": "Pipeline event compaction V2 shadow producer summary",
                "priority": 1,
                "intent": "Keep or repair producer-side high-volume diagnostic summary in shadow mode without raw suppression.",
                "evidence": evidence,
                "files_likely_touched": [
                    "src/utils/pipeline_event_logger.py",
                    "src/engine/pipeline_event_summary.py",
                    "src/engine/pipeline_event_verbosity_report.py",
                ],
                "acceptance_tests": [
                    "pytest src/tests/test_pipeline_event_logger.py src/tests/test_pipeline_event_verbosity_report.py",
                ],
            }
        ]
    if recommended == "open_suppress_guard_order":
        return [
            {
                **base,
                "order_id": "order_pipeline_event_compaction_v2_suppress_guard",
                "title": "Pipeline event compaction V2 suppress guard",
                "priority": 2,
                "intent": "Design default-off suppress guard after repeated shadow parity pass; do not enable suppression automatically.",
                "evidence": evidence,
                "files_likely_touched": [
                    "src/utils/pipeline_event_logger.py",
                    "src/engine/pipeline_event_verbosity_report.py",
                    "docs/time-based-operations-runbook.md",
                ],
                "acceptance_tests": [
                    "pytest src/tests/test_pipeline_event_logger.py src/tests/test_pipeline_event_verbosity_report.py",
                ],
            }
        ]
    return []


def _observation_source_quality_followup_orders(report: dict[str, Any]) -> list[dict[str, Any]]:
    if not report:
        return []
    if str(report.get("status") or "").strip() not in {"warning", "fail"}:
        return []
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    stage_contracts = report.get("stage_contracts") if isinstance(report.get("stage_contracts"), dict) else {}
    high_volume_gaps = (
        report.get("high_volume_no_source_fields")
        if isinstance(report.get("high_volume_no_source_fields"), list)
        else []
    )
    warning_stages = [
        stage
        for stage, result in stage_contracts.items()
        if isinstance(result, dict) and result.get("status") == "warning"
    ]
    evidence = [
        f"status={report.get('status')}",
        f"event_count={summary.get('event_count')}",
        f"warning_stage_count={summary.get('warning_stage_count')}",
        f"warning_stages={','.join(warning_stages[:12])}",
        f"high_volume_no_source_field_stage_count={summary.get('high_volume_no_source_field_stage_count')}",
        "decision_authority=source_quality_only",
        "runtime_effect=false",
    ]
    base = {
        "source_report_type": "observation_source_quality_audit",
        "lifecycle_stage": "source_quality_gate",
        "target_subsystem": "runtime_instrumentation",
        "runtime_effect": False,
        "route": "instrumentation_order",
        "confidence": "audit",
        "expected_ev_effect": "none_direct_source_quality_attribution_only",
        "next_postclose_metric": "observation_source_quality_audit.warning_stage_count and high_volume_no_source_field_stage_count",
    }
    orders: list[dict[str, Any]] = []
    if any(stage in warning_stages for stage in ("ai_confirmed", "blocked_ai_score", "wait65_79_ev_candidate")):
        orders.append(
            {
                **base,
                "order_id": "order_ai_source_quality_not_evaluated_provenance",
                "title": "AI source-quality not-evaluated provenance for cooldown and score50 paths",
                "priority": 1,
                "intent": (
                    "Mark cooldown/score50 AI events as not_evaluated with reason and inherit available "
                    "source-quality snapshots where appropriate, without changing score thresholds or provider route."
                ),
                "evidence": evidence,
                "files_likely_touched": [
                    "src/engine/sniper_state_handlers.py",
                    "src/engine/observation_source_quality_audit.py",
                ],
                "acceptance_tests": [
                    "pytest src/tests/test_observation_source_quality_audit.py src/tests/test_state_handler_fast_signatures.py",
                ],
            }
        )
    if high_volume_gaps:
        gap_stages = [
            str(item.get("stage"))
            for item in high_volume_gaps
            if isinstance(item, dict) and item.get("stage")
        ][:12]
        orders.append(
            {
                **base,
                "order_id": "order_high_volume_diagnostic_stage_contract_labels",
                "title": "High-volume diagnostic stage metric contract labels",
                "priority": 2,
                "intent": (
                    "Label high-volume funnel diagnostics as ops_volume_diagnostic or funnel_count with explicit "
                    "decision_authority, so they cannot be mistaken for threshold/order inputs."
                ),
                "evidence": [*evidence, f"gap_stages={','.join(gap_stages)}"],
                "files_likely_touched": [
                    "src/engine/sniper_state_handlers.py",
                    "src/engine/observation_source_quality_audit.py",
                    "docs/report-based-automation-traceability.md",
                ],
                "acceptance_tests": [
                    "pytest src/tests/test_observation_source_quality_audit.py src/tests/test_build_code_improvement_workorder.py",
                ],
            }
        )
    swing_warning_stages = [
        stage
        for stage in warning_stages
        if stage
        in {
            "swing_probe_state_persisted",
            "scale_in_price_p2_observe",
            "swing_scale_in_micro_context_observed",
            "scale_in_price_resolved",
            "swing_probe_scale_in_order_assumed_filled",
            "swing_sim_scale_in_order_assumed_filled",
        }
    ]
    if swing_warning_stages:
        stage_evidence: list[str] = []
        for stage in swing_warning_stages[:8]:
            contract = stage_contracts.get(stage) if isinstance(stage_contracts.get(stage), dict) else {}
            missing = contract.get("missing_violations") if isinstance(contract.get("missing_violations"), dict) else {}
            missing_fields = ",".join(str(key) for key in list(missing)[:8])
            stage_evidence.append(
                f"{stage}:sample_count={contract.get('sample_count')} missing_fields={missing_fields or '-'}"
            )
        orders.append(
            {
                **base,
                "order_id": "order_swing_source_quality_micro_context_provenance",
                "title": "Swing source-quality micro context provenance",
                "priority": 2,
                "intent": (
                    "Route swing probe-state contract warnings and OFI/QI micro-context observer gaps as "
                    "source-quality workorders, including fresh WS quote provenance where available, without "
                    "changing swing thresholds, order submission, approval gates, or provider route."
                ),
                "evidence": [
                    *evidence,
                    f"swing_warning_stages={','.join(swing_warning_stages)}",
                    *stage_evidence,
                ],
                "files_likely_touched": [
                    "src/engine/sniper_state_handlers.py",
                    "src/engine/observation_source_quality_audit.py",
                    "src/engine/build_code_improvement_workorder.py",
                    "docs/report-based-automation-traceability.md",
                ],
                "acceptance_tests": [
                    "pytest src/tests/test_observation_source_quality_audit.py "
                    "src/tests/test_swing_model_selection_funnel_repair.py "
                    "src/tests/test_build_code_improvement_workorder.py",
                ],
            }
        )
    return orders


def _codebase_performance_followup_orders(report: dict[str, Any]) -> list[dict[str, Any]]:
    if not report:
        return []
    result: list[dict[str, Any]] = []
    for state, section in (
        ("accepted", "accepted_candidates"),
        ("deferred", "deferred_candidates"),
        ("rejected", "rejected_candidates"),
    ):
        candidates = report.get(section) if isinstance(report.get(section), list) else []
        for item in candidates:
            if not isinstance(item, dict):
                continue
            order_id = str(item.get("order_id") or item.get("item_id") or "").strip()
            if not order_id:
                continue
            result.append(
                {
                    "order_id": order_id,
                    "title": item.get("title"),
                    "source_report_type": "codebase_performance_workorder",
                    "lifecycle_stage": item.get("lifecycle_stage") or "ops_performance",
                    "target_subsystem": item.get("target_subsystem"),
                    "route": item.get("route") or "performance_optimization_order",
                    "confidence": item.get("confidence") or "consensus",
                    "priority": item.get("priority"),
                    "runtime_effect": False,
                    "strategy_effect": False,
                    "data_quality_effect": False,
                    "tuning_axis_effect": False,
                    "performance_candidate_state": state,
                    "risk_tier": item.get("risk_tier"),
                    "forbidden_uses": item.get("forbidden_uses") or [],
                    "implementation_status": item.get("implementation_status"),
                    "implementation_checks": item.get("implementation_checks") or [],
                    "implementation_provenance": item.get("implementation_provenance"),
                    "evidence": [
                        f"source_doc_hash={report.get('source_doc_hash')}",
                        f"candidate_state={state}",
                        f"implementation_status={item.get('implementation_status') or 'unknown'}",
                        f"risk_tier={item.get('risk_tier')}",
                        "runtime_effect=false",
                        "strategy_effect=false",
                        "data_quality_effect=false",
                        "tuning_axis_effect=false",
                        f"parity_contract={item.get('parity_contract')}",
                    ],
                    "intent": "Create a user-instructed, parity-tested code performance improvement without changing trading logic.",
                    "expected_ev_effect": "none_direct_ops_cpu_io_reduction_only",
                    "next_postclose_metric": "same report/output parity with lower runtime or CPU/IO overhead",
                    "files_likely_touched": item.get("files_likely_touched") or [],
                    "acceptance_tests": item.get("acceptance_tests") or [],
                    "parity_contract": item.get("parity_contract"),
                    "defer_reason": item.get("defer_reason"),
                }
            )
    return result


def _closed_instrumentation_order_families(ev_report: dict[str, Any]) -> dict[str, str]:
    outcome = ev_report.get("calibration_outcome") if isinstance(ev_report.get("calibration_outcome"), dict) else {}
    decisions = outcome.get("decisions") if isinstance(outcome.get("decisions"), list) else []
    closed: dict[str, str] = {}
    for item in decisions:
        if not isinstance(item, dict):
            continue
        family = str(item.get("family") or "").strip()
        source_metrics = item.get("source_metrics") if isinstance(item.get("source_metrics"), dict) else {}
        if source_metrics.get("instrumentation_status") != "implemented":
            continue
        if family == "pre_submit_price_guard":
            closed["order_latency_guard_miss_ev_recovery"] = family
        elif family == "holding_exit_decision_matrix_advisory":
            closed["order_holding_exit_decision_matrix_edge_counterfactual"] = family
    return closed


def _calibration_report_from_ev(ev_report: dict[str, Any]) -> dict[str, Any]:
    sources = ev_report.get("sources") if isinstance(ev_report.get("sources"), dict) else {}
    path_text = sources.get("calibration")
    if not path_text:
        return {}
    return _load_json(Path(str(path_text)))


def _calibration_report_path_from_ev(ev_report: dict[str, Any]) -> Path | None:
    sources = ev_report.get("sources") if isinstance(ev_report.get("sources"), dict) else {}
    path_text = sources.get("calibration")
    return Path(str(path_text)) if path_text else None


def _window_policy_audit_followup_orders(calibration_report: dict[str, Any]) -> list[dict[str, Any]]:
    audit = (
        calibration_report.get("window_policy_audit")
        if isinstance(calibration_report.get("window_policy_audit"), dict)
        else {}
    )
    issue_counts = audit.get("issue_counts") if isinstance(audit.get("issue_counts"), dict) else {}
    if not issue_counts:
        return []
    items = [item for item in audit.get("items") or [] if isinstance(item, dict) and item.get("issues")]
    if not items:
        return []
    affected = [str(item.get("family") or "") for item in items if item.get("family")]
    evidence = [
        f"issue_counts={json.dumps(issue_counts, ensure_ascii=False, sort_keys=True)}",
        "affected_families=" + ",".join(affected),
    ]
    for item in items[:8]:
        evidence.append(
            "family={family} primary={primary} state={state} primary_sample={sample} "
            "snapshot_sample={snapshot} source_sample={source} issues={issues}".format(
                family=item.get("family"),
                primary=item.get("primary"),
                state=item.get("candidate_state"),
                sample=item.get("primary_sample_count"),
                snapshot=item.get("primary_snapshot_sample_count"),
                source=item.get("primary_source_sample_count"),
                issues=",".join(str(value) for value in item.get("issues") or []),
            )
        )
    return [
        {
            "order_id": "order_threshold_window_policy_source_snapshot_alignment",
            "title": "threshold window policy source snapshot alignment",
            "source_report_type": "threshold_cycle_calibration",
            "lifecycle_stage": "threshold_cycle",
            "target_subsystem": "threshold_cycle_report",
            "route": "instrumentation_order",
            "mapped_family": None,
            "threshold_family": "window_policy_registry",
            "improvement_type": "source_quality_alignment",
            "confidence": "consensus",
            "priority": 3,
            "runtime_effect": False,
            "expected_ev_effect": (
                "Prevent daily-only or snapshot-only calibration blind spots by aligning rolling/cumulative "
                "source metrics, snapshot denominators, AI correction context, and EV/workorder rendering."
            ),
            "evidence": evidence,
            "next_postclose_metric": (
                "window_policy_audit should have no daily_only_leak or rolling_consumer_gap; "
                "rolling_source_snapshot_mismatch must be explained as rendering-only or eliminated."
            ),
            "files_likely_touched": [
                "src/engine/daily_threshold_cycle_report.py",
                "src/engine/threshold_cycle_ev_report.py",
                "src/engine/build_code_improvement_workorder.py",
                "data/threshold_cycle/README.md",
            ],
            "acceptance_tests": [
                "PYTHONPATH=. .venv/bin/pytest src/tests/test_daily_threshold_cycle_report.py src/tests/test_build_code_improvement_workorder.py",
                "threshold_cycle_YYYY-MM-DD.json includes window_policy_audit and calibration_source_bundle_by_window lineage",
            ],
        }
    ]


def _panic_lifecycle_followup_orders(calibration_report: dict[str, Any]) -> list[dict[str, Any]]:
    bundle = (
        calibration_report.get("calibration_source_bundle")
        if isinstance(calibration_report.get("calibration_source_bundle"), dict)
        else {}
    )
    source_metrics = bundle.get("source_metrics") if isinstance(bundle.get("source_metrics"), dict) else {}
    orders: list[dict[str, Any]] = []

    panic_sell = source_metrics.get("panic_sell_defense") if isinstance(source_metrics.get("panic_sell_defense"), dict) else {}
    panic_sell_candidates = panic_sell.get("candidate_status") if isinstance(panic_sell.get("candidate_status"), dict) else {}
    panic_sell_source_quality_blockers = (
        panic_sell.get("source_quality_blockers")
        if isinstance(panic_sell.get("source_quality_blockers"), list)
        else []
    )
    panic_sell_triggered = bool(panic_sell_candidates) or str(panic_sell.get("panic_state") or "") in {
        "PANIC_SELL",
        "RECOVERY_WATCH",
    }
    panic_sell_triggered = panic_sell_triggered or (_safe_int(panic_sell.get("active_sim_probe_positions"), 0) > 0)
    panic_sell_triggered = panic_sell_triggered or bool(panic_sell.get("market_breadth_followup_candidate"))
    panic_sell_triggered = panic_sell_triggered or bool(panic_sell_source_quality_blockers)
    if panic_sell_triggered:
        orders.append(
            {
                "order_id": "order_panic_sell_defense_lifecycle_transition_pack",
                "title": "panic sell defense lifecycle transition pack",
                "source_report_type": "threshold_cycle_calibration_source_bundle",
                "lifecycle_stage": "holding_exit",
                "target_subsystem": "panic_sell_defense",
                "route": "auto_family_candidate",
                "mapped_family": None,
                "threshold_family": "panic_sell_defense",
                "improvement_type": "runtime_transition_design",
                "confidence": "consensus",
                "priority": 6,
                "runtime_effect": False,
                "expected_ev_effect": (
                    "Use panic-sell simulation and post-sell rebound evidence to propose threshold/guard changes, "
                    "then request explicit live-runtime approval without mutating exits automatically."
                ),
                "evidence": [
                    f"panic_state={panic_sell.get('panic_state')}",
                    f"panic_regime_mode={panic_sell.get('panic_regime_mode')}",
                    f"stop_loss_exit_count={panic_sell.get('stop_loss_exit_count')}",
                    f"confirmation_eligible_exit_count={panic_sell.get('confirmation_eligible_exit_count')}",
                    f"active_sim_probe_positions={panic_sell.get('active_sim_probe_positions')}",
                    f"post_sell_rebound_above_sell_10_20m_pct={panic_sell.get('post_sell_rebound_above_sell_10_20m_pct')}",
                    f"microstructure_market_risk_state={panic_sell.get('microstructure_market_risk_state')}",
                    f"microstructure_confirmed_risk_off_advisory={panic_sell.get('microstructure_confirmed_risk_off_advisory')}",
                    f"microstructure_portfolio_local_risk_off_only={panic_sell.get('microstructure_portfolio_local_risk_off_only')}",
                    f"market_breadth_followup_candidate={panic_sell.get('market_breadth_followup_candidate')}",
                    f"source_quality_blockers={panic_sell_source_quality_blockers}",
                    f"candidate_status={panic_sell_candidates}",
                    "allowed_runtime_apply=false",
                ],
                "next_postclose_metric": (
                    "panic_sell_defense should expose simulation EV, rollback guard, approval artifact status, "
                    "market/breadth confirmation, and candidate-specific threshold recommendations before any runtime transition."
                ),
                "files_likely_touched": [
                    "src/engine/panic_sell_defense_report.py",
                    "src/engine/daily_threshold_cycle_report.py",
                    "src/engine/runtime_approval_summary.py",
                    "docs/plan-korStockScanPerformanceOptimization.rebase.md",
                ],
                "acceptance_tests": [
                    "pytest panic sell defense/report lifecycle tests",
                    "pytest src/tests/test_build_code_improvement_workorder.py src/tests/test_runtime_approval_summary.py",
                ],
            }
        )

    panic_buy = source_metrics.get("panic_buying") if isinstance(source_metrics.get("panic_buying"), dict) else {}
    panic_buy_candidates = panic_buy.get("candidate_status") if isinstance(panic_buy.get("candidate_status"), dict) else {}
    panic_buy_source_quality_blockers = (
        panic_buy.get("source_quality_blockers")
        if isinstance(panic_buy.get("source_quality_blockers"), list)
        else []
    )
    panic_buy_triggered = bool(panic_buy_candidates) or (_safe_int(panic_buy.get("panic_buy_active_count"), 0) > 0)
    panic_buy_triggered = panic_buy_triggered or (_safe_int(panic_buy.get("tp_counterfactual_count"), 0) > 0)
    panic_buy_triggered = panic_buy_triggered or (_safe_int(panic_buy.get("trailing_winner_count"), 0) > 0)
    panic_buy_triggered = panic_buy_triggered or bool(panic_buy_source_quality_blockers)
    if panic_buy_triggered:
        source_quality_only = bool(panic_buy_source_quality_blockers)
        orders.append(
            {
                "order_id": (
                    "order_panic_buying_source_quality_market_breadth_micro_coverage"
                    if source_quality_only
                    else "order_panic_buy_runner_tp_canary_lifecycle_pack"
                ),
                "title": (
                    "panic buying source-quality market breadth and micro coverage"
                    if source_quality_only
                    else "panic buy runner TP canary lifecycle pack"
                ),
                "source_report_type": "threshold_cycle_calibration_source_bundle",
                "lifecycle_stage": "source_quality" if source_quality_only else "holding_exit",
                "target_subsystem": "panic_buying",
                "route": "source_quality_blocker" if source_quality_only else "auto_family_candidate",
                "mapped_family": None,
                "threshold_family": None if source_quality_only else "panic_buy_runner_tp_canary",
                "improvement_type": "source_quality_instrumentation" if source_quality_only else "runtime_transition_design",
                "confidence": "consensus",
                "priority": 7,
                "runtime_effect": False,
                "expected_ev_effect": (
                    "Route market breadth and micro coverage gaps as source-quality blockers before any panic-buying runtime candidate."
                    if source_quality_only
                    else (
                        "Use panic-buying TP counterfactuals to reduce missed upside versus full fixed-TP exits, "
                        "while keeping hard/protect/emergency stops and order provenance guards dominant."
                    )
                ),
                "evidence": [
                    f"panic_buy_state={panic_buy.get('panic_buy_state')}",
                    f"panic_buy_regime_mode={panic_buy.get('panic_buy_regime_mode')}",
                    f"panic_buy_active_count={panic_buy.get('panic_buy_active_count')}",
                    f"exhaustion_confirmed_count={panic_buy.get('exhaustion_confirmed_count')}",
                    f"tp_counterfactual_count={panic_buy.get('tp_counterfactual_count')}",
                    f"trailing_winner_count={panic_buy.get('trailing_winner_count')}",
                    f"market_wide_panic_buy_confirmed={panic_buy.get('market_wide_panic_buy_confirmed')}",
                    f"market_breadth_risk_on_advisory={panic_buy.get('market_breadth_risk_on_advisory')}",
                    f"missing_orderbook_count={panic_buy.get('missing_orderbook_count')}",
                    f"missing_trade_aggressor_count={panic_buy.get('missing_trade_aggressor_count')}",
                    f"source_quality_blockers={panic_buy_source_quality_blockers}",
                    f"candidate_status={panic_buy_candidates}",
                    "allowed_runtime_apply=false",
                ],
                "next_postclose_metric": (
                    "panic_buying source-quality blockers must be resolved or explicitly carried before runner TP approval is reviewed."
                    if source_quality_only
                    else (
                        "panic_buying should expose runner-vs-full-TP EV, MAE/giveback/sell-failure rollback guards, "
                        "approval artifact status, panic_buy_regime_mode owner split, and no live TP mutation before approval."
                    )
                ),
                "files_likely_touched": [
                    "src/engine/panic_buying_report.py",
                    "src/engine/daily_threshold_cycle_report.py",
                    "src/engine/runtime_approval_summary.py",
                    "docs/plan-korStockScanPerformanceOptimization.rebase.md",
                    "docs/code-improvement-workorders/panic_buying_regime_mode_v2_2026-05-14.md",
                ],
                "acceptance_tests": [
                    "pytest src/tests/test_panic_buying_report.py",
                    "pytest src/tests/test_build_code_improvement_workorder.py src/tests/test_runtime_approval_summary.py",
                ],
            }
        )

    return orders


def _swing_strategy_discovery_followup_orders(report: dict[str, Any]) -> list[dict[str, Any]]:
    if not report:
        return []
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    warnings = [str(item) for item in (report.get("warnings") or []) if str(item).strip()]
    avoid_count = _safe_int(summary.get("avoid_bucket_count"), 0)
    pending = _safe_int(summary.get("pending_future_quote_count"), 0)
    labeled = _safe_int(summary.get("labeled_sample_count"), 0)
    orders: list[dict[str, Any]] = []
    if warnings or pending:
        orders.append(
            {
                "order_id": "order_swing_strategy_discovery_source_quality_followup",
                "title": "swing strategy discovery label/source quality follow-up",
                "source_report_type": "swing_strategy_discovery_ev",
                "lifecycle_stage": "source_quality",
                "target_subsystem": "swing_strategy_discovery_sim",
                "route": "instrumentation_order",
                "mapped_family": None,
                "threshold_family": None,
                "improvement_type": "source_quality_instrumentation",
                "confidence": "consensus",
                "priority": 6,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "expected_ev_effect": "Improve discovery label coverage and source attribution before any swing strategy policy promotion is discussed.",
                "evidence": [
                    f"labeled_sample_count={labeled}",
                    f"pending_future_quote_count={pending}",
                    f"warnings={warnings}",
                    "decision_authority=swing_sim_exploration_only",
                    "allowed_runtime_apply=false",
                ],
                "next_postclose_metric": "swing_strategy_discovery_ev should reduce pending_future_quotes where matured and keep source-only authority.",
                "files_likely_touched": [
                    "src/engine/swing_strategy_discovery_label_builder.py",
                    "src/engine/swing_strategy_discovery_ev_report.py",
                    "src/engine/swing_sector_theme_source.py",
                ],
                "acceptance_tests": [
                    "PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_strategy_discovery_label_builder.py src/tests/test_swing_strategy_discovery_ev_report.py src/tests/test_swing_sector_theme_source.py",
                ],
            }
        )
    if avoid_count > 0:
        orders.append(
            {
                "order_id": "order_swing_strategy_discovery_avoid_bucket_review",
                "title": "swing strategy discovery avoid bucket report enrichment",
                "source_report_type": "swing_strategy_discovery_ev",
                "lifecycle_stage": "selection",
                "target_subsystem": "swing_strategy_discovery_sim",
                "route": "instrumentation_order",
                "mapped_family": None,
                "threshold_family": None,
                "improvement_type": "analysis_report_provenance",
                "confidence": "consensus",
                "priority": 7,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "expected_ev_effect": "Expose avoid buckets as analysis guidance only; do not mutate swing runtime or recommendation_history.",
                "evidence": [
                    f"avoid_bucket_count={avoid_count}",
                    f"top_surviving_arm={summary.get('top_surviving_arm')}",
                    "runtime_effect=false",
                ],
                "next_postclose_metric": "avoid_buckets should include axis/key/sample/EV/downside with enough sample floor to guide later design.",
                "files_likely_touched": [
                    "src/engine/swing_strategy_discovery_ev_report.py",
                    "docs/swing-strategy-discovery-sim-v1.md",
                ],
                "acceptance_tests": [
                    "PYTHONPATH=. .venv/bin/pytest -q src/tests/test_swing_strategy_discovery_ev_report.py src/tests/test_build_code_improvement_workorder.py",
                ],
            }
        )
    return orders


def build_code_improvement_workorder(target_date: str, *, max_orders: int = 12) -> dict[str, Any]:
    target_date = str(target_date).strip()
    json_path, md_path = code_improvement_workorder_paths(target_date)
    previous_report = _load_json(json_path)
    source_path = automation_report_path(target_date)
    automation = _load_json(source_path)
    swing_source_path = swing_automation_report_path(target_date)
    swing_automation = _load_json(swing_source_path)
    swing_lab_source_path = swing_pattern_lab_automation_report_path(target_date)
    swing_lab_automation = _load_json(swing_lab_source_path)
    swing_discovery_source_path = swing_strategy_discovery_ev_report_path(target_date)
    swing_discovery_ev = _load_json(swing_discovery_source_path)
    ev_path = threshold_ev_report_path(target_date)
    ev_report = _load_json(ev_path)
    pipeline_event_verbosity_path = _pipeline_event_verbosity_report_path(target_date)
    pipeline_event_verbosity = _load_json(pipeline_event_verbosity_path)
    observation_source_quality_path = _observation_source_quality_audit_path(target_date)
    observation_source_quality = _load_json(observation_source_quality_path)
    codebase_performance_path = _codebase_performance_report_path(target_date)
    codebase_performance = _load_json(codebase_performance_path)
    pattern_lab_currentness_path = pattern_lab_currentness_audit_report_path(target_date)
    pattern_lab_currentness = _load_json(pattern_lab_currentness_path)
    calibration_source_path = _calibration_report_path_from_ev(ev_report)
    calibration_report = _calibration_report_from_ev(ev_report)
    source_paths = {
            "pattern_lab_automation": source_path,
            "swing_improvement_automation": swing_source_path,
            "swing_pattern_lab_automation": swing_lab_source_path,
            "swing_strategy_discovery_ev": swing_discovery_source_path,
            "threshold_cycle_ev": ev_path,
            "pipeline_event_verbosity": pipeline_event_verbosity_path,
            "observation_source_quality_audit": observation_source_quality_path,
            "codebase_performance_workorder": codebase_performance_path,
            "pattern_lab_currentness_audit": pattern_lab_currentness_path,
    }
    ev_sources = ev_report.get("sources") if isinstance(ev_report.get("sources"), dict) else {}
    if ev_sources.get("scalp_entry_action_decision_matrix"):
        source_paths["scalp_entry_action_decision_matrix"] = Path(str(ev_sources.get("scalp_entry_action_decision_matrix")))
    if calibration_source_path is not None:
        source_paths["threshold_cycle_calibration"] = calibration_source_path
    source_fingerprint = _source_fingerprint(source_paths)
    finding_by_order_id, finding_by_title_slug = _finding_maps(automation)
    swing_finding_by_order_id, swing_finding_by_title_slug = _finding_maps(swing_automation)
    swing_lab_finding_by_order_id, swing_lab_finding_by_title_slug = _finding_maps(swing_lab_automation)
    finding_by_order_id.update(swing_finding_by_order_id)
    finding_by_order_id.update(swing_lab_finding_by_order_id)
    finding_by_title_slug.update(swing_finding_by_title_slug)
    finding_by_title_slug.update(swing_lab_finding_by_title_slug)
    auto_family_ids = _auto_family_order_ids(automation) | _auto_family_order_ids(swing_automation) | _auto_family_order_ids(swing_lab_automation)
    scalping_orders = [
        {**item, "source_report_type": "scalping_pattern_lab_automation"}
        for item in (automation.get("code_improvement_orders") or [])
        if isinstance(item, dict)
    ]
    swing_orders = [
        {**item, "source_report_type": "swing_improvement_automation"}
        for item in (swing_automation.get("code_improvement_orders") or [])
        if isinstance(item, dict)
    ]
    swing_lab_orders = [
        {**item, "source_report_type": "swing_pattern_lab_automation"}
        for item in (swing_lab_automation.get("code_improvement_orders") or [])
        if isinstance(item, dict)
    ]
    swing_discovery_orders = _swing_strategy_discovery_followup_orders(swing_discovery_ev)
    pattern_lab_currentness_orders = [
        {**item, "source_report_type": "pattern_lab_currentness_audit"}
        for item in (pattern_lab_currentness.get("code_improvement_orders") or [])
        if isinstance(item, dict)
    ]
    threshold_ev_orders = [
        *_threshold_ev_followup_orders(ev_report),
        *_entry_adm_followup_orders(ev_report),
        *_window_policy_audit_followup_orders(calibration_report),
        *_panic_lifecycle_followup_orders(calibration_report),
        *_pipeline_event_verbosity_followup_orders(pipeline_event_verbosity),
        *_observation_source_quality_followup_orders(observation_source_quality),
        *_codebase_performance_followup_orders(codebase_performance),
    ]
    closed_instrumentation_order_families = _closed_instrumentation_order_families(ev_report)
    orders = [
        *scalping_orders,
        *swing_orders,
        *swing_lab_orders,
        *swing_discovery_orders,
        *pattern_lab_currentness_orders,
        *threshold_ev_orders,
    ]
    seen_keys: set[tuple[str, str, str]] = set()
    deduped_orders: list[dict[str, Any]] = []
    collision_warnings: list[str] = []
    for order in orders:
        key = (str(order.get("source_report_type") or ""), str(order.get("lifecycle_stage") or ""), str(order.get("order_id") or ""))
        if key in seen_keys:
            collision_warnings.append(f"duplicate_order_id={order.get('order_id')} source={order.get('source_report_type')} stage={order.get('lifecycle_stage')}")
            continue
        seen_keys.add(key)
        deduped_orders.append(order)
    orders = deduped_orders
    classified = _sort_classified(
        [
            _classify_order(
                order,
                finding_by_order_id=finding_by_order_id,
                finding_by_title_slug=finding_by_title_slug,
                auto_family_order_ids=auto_family_ids,
                closed_instrumentation_order_families=closed_instrumentation_order_families,
            )
            for order in orders
        ]
    )
    selected = classified[: max(1, int(max_orders))]
    counts: dict[str, int] = {}
    for item in classified:
        counts[item.decision] = counts.get(item.decision, 0) + 1
    report = {
        "schema_version": WORKORDER_SCHEMA_VERSION,
        "date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "generation_id": f"{target_date}-{source_fingerprint['generation_id']}",
        "source_hash": source_fingerprint["source_hash"],
        "purpose": "codex_code_improvement_workorder_from_postclose_automation",
        "source": {
            "pattern_lab_automation": str(source_path),
            "swing_improvement_automation": str(swing_source_path) if swing_source_path.exists() else None,
            "swing_pattern_lab_automation": str(swing_lab_source_path) if swing_lab_source_path.exists() else None,
            "swing_strategy_discovery_ev": str(swing_discovery_source_path) if swing_discovery_source_path.exists() else None,
            "threshold_cycle_ev": str(ev_path) if ev_path.exists() else None,
            "scalp_entry_action_decision_matrix": str(source_paths["scalp_entry_action_decision_matrix"])
            if "scalp_entry_action_decision_matrix" in source_paths
            and Path(source_paths["scalp_entry_action_decision_matrix"]).exists()
            else None,
            "pipeline_event_verbosity": str(pipeline_event_verbosity_path)
            if pipeline_event_verbosity_path.exists()
            else None,
            "observation_source_quality_audit": str(observation_source_quality_path)
            if observation_source_quality_path.exists()
            else None,
            "codebase_performance_workorder": str(codebase_performance_path)
            if codebase_performance_path.exists()
            else None,
            "pattern_lab_currentness_audit": str(pattern_lab_currentness_path)
            if pattern_lab_currentness_path.exists()
            else None,
            "threshold_cycle_calibration": str(calibration_source_path)
            if calibration_source_path and calibration_source_path.exists()
            else None,
        },
        "source_fingerprint": source_fingerprint["files"],
        "policy": {
            "runtime_patch_automation": False,
            "user_intervention_point": "paste generated markdown into a Codex session and request implementation",
            "post_implementation_reentry": "postclose reports and daily EV consume the updated source metrics automatically",
            "recommended_operator_instruction": (
                "implement_now를 2-pass로 처리: Pass1 instrumentation/report/provenance 구현, "
                "관련 리포트 재생성 후 workorder diff 확인, 신규 runtime_effect=false 항목만 Pass2 구현, "
                "마지막에 generation_id/source_hash 기준으로 final freeze 보고"
            ),
        },
        "summary": {
            "source_order_count": len(orders),
            "scalping_source_order_count": len(scalping_orders),
            "swing_source_order_count": len(swing_orders),
            "swing_lab_source_order_count": len(swing_lab_orders),
            "swing_strategy_discovery_source_order_count": len(swing_discovery_orders),
            "pattern_lab_currentness_source_order_count": len(pattern_lab_currentness_orders),
            "threshold_ev_source_order_count": len(threshold_ev_orders),
            "pipeline_event_verbosity_source_order_count": len(
                _pipeline_event_verbosity_followup_orders(pipeline_event_verbosity)
            ),
            "observation_source_quality_source_order_count": len(
                _observation_source_quality_followup_orders(observation_source_quality)
            ),
            "codebase_performance_source_order_count": len(
                _codebase_performance_followup_orders(codebase_performance)
            ),
            "panic_lifecycle_source_order_count": len(_panic_lifecycle_followup_orders(calibration_report)),
            "selected_order_count": len(selected),
            "decision_counts": counts,
            "gemini_fresh": ((automation.get("ev_report_summary") or {}).get("gemini_fresh")),
            "claude_fresh": ((automation.get("ev_report_summary") or {}).get("claude_fresh")),
            "swing_lifecycle_audit_available": bool(swing_automation),
            "swing_pattern_lab_automation_available": bool(swing_lab_automation),
            "swing_strategy_discovery_ev_available": bool(swing_discovery_ev),
            "swing_pattern_lab_fresh": ((swing_lab_automation.get("ev_report_summary") or {}).get("deepseek_lab_available")),
            "pattern_lab_currentness_status": pattern_lab_currentness.get("status"),
            "pattern_lab_currentness_fail_count": ((pattern_lab_currentness.get("summary") or {}).get("fail_count")),
            "swing_threshold_ai_status": ((swing_automation.get("ev_report_summary") or {}).get("threshold_ai_status")),
            "daily_ev_available": bool(ev_report),
            "duplicate_order_warnings": collision_warnings,
        },
        "orders": [
            {
                "order_id": item.order.get("order_id"),
                "title": item.order.get("title"),
                "target_subsystem": item.order.get("target_subsystem"),
                "source_report_type": item.order.get("source_report_type"),
                "lifecycle_stage": item.order.get("lifecycle_stage"),
                "threshold_family": item.order.get("threshold_family"),
                "improvement_type": item.order.get("improvement_type"),
                "priority": item.order.get("priority"),
                "decision": item.decision,
                "decision_reason": item.reason,
                "route": item.route,
                "mapped_family": item.mapped_family,
                "confidence": item.confidence,
                "intent": item.order.get("intent"),
                "expected_ev_effect": item.order.get("expected_ev_effect"),
                "evidence": item.order.get("evidence") or [],
                "next_postclose_metric": item.order.get("next_postclose_metric"),
                "files_likely_touched": item.order.get("files_likely_touched") or [],
                "acceptance_tests": item.order.get("acceptance_tests") or [],
                "automation_reentry": item.automation_reentry,
                "runtime_effect": bool(item.order.get("runtime_effect")),
                "strategy_effect": bool(item.order.get("strategy_effect")),
                "data_quality_effect": bool(item.order.get("data_quality_effect")),
                "tuning_axis_effect": bool(item.order.get("tuning_axis_effect")),
                "implementation_status": item.order.get("implementation_status"),
                "implementation_checks": item.order.get("implementation_checks") or [],
                "implementation_provenance": item.order.get("implementation_provenance"),
                "parity_contract": item.order.get("parity_contract"),
            }
            for item in selected
        ],
        "deferred_or_rejected_count": max(0, len(classified) - len(selected)),
        "next_codex_session": {
            "instruction": "Paste the generated markdown into Codex and ask: '이 code improvement workorder를 순서대로 구현하고 검증해줘.'",
            "workorder_markdown": str(code_improvement_workorder_paths(target_date)[1]),
        },
    }
    report["lineage"] = _previous_workorder_lineage(previous_report, report["orders"])
    report["summary"]["new_selected_order_count"] = len(report["lineage"]["new_order_ids"])
    report["summary"]["removed_selected_order_count"] = len(report["lineage"]["removed_order_ids"])
    report["summary"]["decision_changed_order_count"] = len(report["lineage"]["decision_changed_order_ids"])
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_code_improvement_workorder_markdown(report), encoding="utf-8")
    return report


def _format_list(values: Any) -> str:
    items = [str(item) for item in (values or []) if str(item).strip()]
    return ", ".join(f"`{item}`" for item in items) if items else "-"


def render_code_improvement_workorder_markdown(report: dict[str, Any]) -> str:
    date_value = report.get("date") or ""
    next_date = _next_calendar_day(str(date_value))
    source = report.get("source") if isinstance(report.get("source"), dict) else {}
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    policy = report.get("policy") if isinstance(report.get("policy"), dict) else {}
    lineage = report.get("lineage") if isinstance(report.get("lineage"), dict) else {}
    lines = [
        f"# Code Improvement Workorder - {date_value}",
        "",
        "## 목적",
        "",
        "- Postclose 자동화가 생성한 `code_improvement_order`를 Codex 실행용 작업지시서로 변환한다.",
        "- 입력은 scalping pattern lab automation, swing lifecycle improvement automation, swing pattern lab automation을 함께 포함할 수 있다.",
        "- 이 문서는 repo/runtime을 직접 변경하지 않는다. 사용자가 이 문서를 Codex 세션에 넣고 구현을 요청하는 지점만 사람 개입으로 남긴다.",
        "- 구현 후 자동화체인 재투입은 다음 postclose report, threshold calibration, daily EV report가 담당한다.",
        "",
        "## Source",
        "",
        f"- pattern_lab_automation: `{source.get('pattern_lab_automation')}`",
        f"- swing_improvement_automation: `{source.get('swing_improvement_automation') or '-'}`",
        f"- swing_pattern_lab_automation: `{source.get('swing_pattern_lab_automation') or '-'}`",
        f"- swing_strategy_discovery_ev: `{source.get('swing_strategy_discovery_ev') or '-'}`",
        f"- threshold_cycle_ev: `{source.get('threshold_cycle_ev') or '-'}`",
        f"- threshold_cycle_calibration: `{source.get('threshold_cycle_calibration') or '-'}`",
        f"- pipeline_event_verbosity: `{source.get('pipeline_event_verbosity') or '-'}`",
        f"- observation_source_quality_audit: `{source.get('observation_source_quality_audit') or '-'}`",
        f"- codebase_performance_workorder: `{source.get('codebase_performance_workorder') or '-'}`",
        f"- pattern_lab_currentness_audit: `{source.get('pattern_lab_currentness_audit') or '-'}`",
        f"- generated_at: `{report.get('generated_at')}`",
        f"- generation_id: `{report.get('generation_id')}`",
        f"- source_hash: `{report.get('source_hash')}`",
        "",
        "## 운영 원칙",
        "",
        "- `runtime_effect=false` order만 구현 대상으로 본다.",
        "- fallback 재개, shadow 재개, safety guard 우회는 구현하지 않는다.",
        "- runtime 영향이 생길 수 있는 변경은 feature flag, threshold family metadata, provenance, safety guard를 같이 닫는다.",
        "- 새 family는 `allowed_runtime_apply=false`에서 시작하고, 구현/테스트/guard 완료 후에만 auto_bounded_live 후보가 될 수 있다.",
        "- 구현 후에는 관련 테스트와 parser 검증을 실행하고, 다음 postclose daily EV에서 metric을 확인한다.",
        "- 같은 날짜 workorder를 재생성하면 `generation_id`와 `lineage` diff로 신규/삭제/판정변경 order를 먼저 확인한다.",
        "",
        "## 2-Pass 실행 기준",
        "",
        "- Pass 1: `implement_now` 중 instrumentation/report/provenance 구현만 먼저 수행한다.",
        "- Regeneration: 관련 postclose report와 이 workorder를 재생성하고 `lineage` diff를 확인한다.",
        "- Pass 2: 재생성 후 새로 생긴 `runtime_effect=false` order만 추가 구현한다.",
        "- Final freeze: `generation_id`, `source_hash`, 신규/삭제/판정변경 order를 최종 보고에 남긴다.",
        f"- 권장 지시문: `{policy.get('recommended_operator_instruction')}`",
        "",
        "## Snapshot Lineage",
        "",
        f"- previous_exists: `{lineage.get('previous_exists')}`",
        f"- previous_generation_id: `{lineage.get('previous_generation_id') or '-'}`",
        f"- previous_source_hash: `{lineage.get('previous_source_hash') or '-'}`",
        f"- new_order_ids: `{lineage.get('new_order_ids') or []}`",
        f"- removed_order_ids: `{lineage.get('removed_order_ids') or []}`",
        f"- decision_changed_order_ids: `{lineage.get('decision_changed_order_ids') or []}`",
        "",
        "## Summary",
        "",
        f"- source_order_count: `{summary.get('source_order_count')}`",
        f"- scalping_source_order_count: `{summary.get('scalping_source_order_count')}`",
        f"- swing_source_order_count: `{summary.get('swing_source_order_count')}`",
        f"- swing_lab_source_order_count: `{summary.get('swing_lab_source_order_count')}`",
        f"- swing_strategy_discovery_source_order_count: `{summary.get('swing_strategy_discovery_source_order_count')}`",
        f"- pattern_lab_currentness_source_order_count: `{summary.get('pattern_lab_currentness_source_order_count')}`",
        f"- threshold_ev_source_order_count: `{summary.get('threshold_ev_source_order_count')}`",
        f"- pipeline_event_verbosity_source_order_count: `{summary.get('pipeline_event_verbosity_source_order_count')}`",
        f"- observation_source_quality_source_order_count: `{summary.get('observation_source_quality_source_order_count')}`",
        f"- codebase_performance_source_order_count: `{summary.get('codebase_performance_source_order_count')}`",
        f"- panic_lifecycle_source_order_count: `{summary.get('panic_lifecycle_source_order_count')}`",
        f"- selected_order_count: `{summary.get('selected_order_count')}`",
        f"- decision_counts: `{summary.get('decision_counts')}`",
        f"- gemini_fresh: `{summary.get('gemini_fresh')}`",
        f"- claude_fresh: `{summary.get('claude_fresh')}`",
        f"- swing_lifecycle_audit_available: `{summary.get('swing_lifecycle_audit_available')}`",
        f"- swing_pattern_lab_automation_available: `{summary.get('swing_pattern_lab_automation_available')}`",
        f"- swing_pattern_lab_fresh: `{summary.get('swing_pattern_lab_fresh')}`",
        f"- pattern_lab_currentness_status: `{summary.get('pattern_lab_currentness_status')}`",
        f"- pattern_lab_currentness_fail_count: `{summary.get('pattern_lab_currentness_fail_count')}`",
        f"- swing_threshold_ai_status: `{summary.get('swing_threshold_ai_status')}`",
        f"- daily_ev_available: `{summary.get('daily_ev_available')}`",
        "",
    ]
    dup_warnings = summary.get("duplicate_order_warnings") if isinstance(summary.get("duplicate_order_warnings"), list) else []
    if dup_warnings:
        lines.extend(["### Duplicate Order Collisions"])
        for w in dup_warnings:
            lines.append(f"- `{w}`")
        lines.append("")
    lines.extend([
        "## Codex 실행 지시",
        "",
        "아래 order를 위에서부터 순서대로 처리한다. 각 order는 `판정 -> 근거 -> 다음 액션`으로 닫고, 코드 변경 시 관련 문서와 테스트를 함께 갱신한다.",
        "",
        "필수 검증:",
        "",
        "```bash",
        "PYTHONPATH=. .venv/bin/pytest -q <관련 테스트 파일>",
        "PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project --print-backlog-only --limit 500",
        "git diff --check",
        "```",
        "",
        "threshold/postclose 체인 영향 시 추가 검증:",
        "",
        "```bash",
        "bash -n deploy/run_threshold_cycle_preopen.sh deploy/run_threshold_cycle_calibration.sh deploy/run_threshold_cycle_postclose.sh",
        "PYTHONPATH=. .venv/bin/pytest -q src/tests/test_daily_threshold_cycle_report.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_threshold_cycle_ev_report.py",
        "```",
        "",
        "## Implementation Orders",
        "",
    ])
    for index, item in enumerate(report.get("orders") or [], start=1):
        if not isinstance(item, dict):
            continue
        lines.extend(
            [
                f"### {index}. `{item.get('order_id')}`",
                "",
                f"- title: {item.get('title')}",
                f"- decision: `{item.get('decision')}`",
                f"- decision_reason: {item.get('decision_reason')}",
                f"- source_report_type: `{item.get('source_report_type') or '-'}`",
                f"- lifecycle_stage: `{item.get('lifecycle_stage') or '-'}`",
                f"- target_subsystem: `{item.get('target_subsystem')}`",
                f"- route: `{item.get('route') or '-'}`",
                f"- mapped_family: `{item.get('mapped_family') or '-'}`",
                f"- threshold_family: `{item.get('threshold_family') or item.get('mapped_family') or '-'}`",
                f"- improvement_type: `{item.get('improvement_type') or '-'}`",
                f"- confidence: `{item.get('confidence') or '-'}`",
                f"- priority: `{item.get('priority')}`",
                f"- runtime_effect: `{item.get('runtime_effect')}`",
                f"- strategy_effect: `{item.get('strategy_effect')}`",
                f"- data_quality_effect: `{item.get('data_quality_effect')}`",
                f"- tuning_axis_effect: `{item.get('tuning_axis_effect')}`",
                f"- expected_ev_effect: {item.get('expected_ev_effect')}",
                f"- evidence: {_format_list(item.get('evidence'))}",
                f"- parity_contract: {item.get('parity_contract') or '-'}",
                f"- next_postclose_metric: {item.get('next_postclose_metric') or '-'}",
                f"- files_likely_touched: {_format_list(item.get('files_likely_touched'))}",
                f"- acceptance_tests: {_format_list(item.get('acceptance_tests'))}",
                f"- implementation_status: `{item.get('implementation_status') or '-'}`",
                f"- implementation_provenance: `{json.dumps(item.get('implementation_provenance'), ensure_ascii=False, sort_keys=True) if item.get('implementation_provenance') else '-'}`",
                f"- automation_reentry: {item.get('automation_reentry')}",
                "",
                "실행 기준:",
                "",
            ]
        )
        decision = item.get("decision")
        if decision == "implement_now":
            lines.extend(
                [
                    "- instrumentation/provenance/report source 보강을 우선 구현한다.",
                    "- runtime 판단값을 직접 바꾸지 않는다.",
                    "- 다음 postclose report에서 source freshness, warning 감소, sample count가 확인되어야 한다.",
                    "",
                ]
            )
        elif decision == "attach_existing_family":
            lines.extend(
                [
                    "- 기존 threshold family의 source metric/provenance를 보강한다.",
                    "- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.",
                    "- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.",
                    "",
                ]
            )
        elif decision == "design_family_candidate":
            lines.extend(
                [
                    "- 새 family 후보 metadata와 report-only source를 설계한다.",
                    "- `allowed_runtime_apply=false`를 유지한다.",
                    "- sample floor, safety guard, target env key, tests가 닫히기 전 runtime 적용 금지.",
                    "",
                ]
            )
        elif decision == "defer_evidence":
            lines.extend(
                [
                    "- 구현하지 말고 부족한 evidence와 다음 확인 artifact를 명시한다.",
                    "- 필요한 경우 report warning 또는 다음 pattern lab 재평가 항목으로만 남긴다.",
                    "",
                ]
            )
        else:
            lines.extend(
                [
                    "- 구현하지 않는다.",
                    "- reject 사유를 유지하고, 필요하면 report_only_calibration 또는 bounded canary 설계로 번역 가능한지 별도 판단한다.",
                    "",
                ]
            )
    if not report.get("orders"):
        lines.append("- none")
        lines.append("")
    lines.extend(
        [
            "## 자동화체인 재투입",
            "",
            f"- 구현 결과는 `{next_date}` 이후 postclose `threshold_cycle`, `scalping_pattern_lab_automation`, `threshold_cycle_ev`가 자동으로 다시 읽는다.",
            "- 구현자가 수동으로 threshold 값을 바꾸는 것이 아니라, source/report/provenance를 닫아 다음 calibration이 판단하게 한다.",
            f"- 다음 Codex 세션 입력 문구: `{policy.get('user_intervention_point')}`",
            "",
            "## Project/Calendar 동기화",
            "",
            "문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.",
            "",
            "```bash",
            "PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build Codex code improvement workorder from pattern lab automation.")
    parser.add_argument("--date", dest="target_date", default=date.today().isoformat())
    parser.add_argument("--max-orders", type=int, default=12)
    args = parser.parse_args(argv)
    report = build_code_improvement_workorder(args.target_date, max_orders=args.max_orders)
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
