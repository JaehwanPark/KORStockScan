from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from src.utils.jsonl_io import existing_or_gzip_path, iter_jsonl


PROJECT_ROOT = Path(__file__).resolve().parents[3]
PIPELINE_EVENTS_DIR = PROJECT_ROOT / "data" / "pipeline_events"
REPORT_DIR = PROJECT_ROOT / "data" / "report" / "rising_missed_intraday_feedback"
KST = timezone(timedelta(hours=9))
FORCED_REASON = "rising_missed_one_share_entry"
AVG_DOWN_FAIL_FLOOR = 2
FORBIDDEN_USES = [
    "runtime_threshold_mutation",
    "intraday_runtime_apply",
    "stale_submit_bypass",
    "broker_guard_bypass",
    "order_guard_relaxation",
    "scale_in_guard_bypass",
    "quantity_guard_relaxation",
    "position_cap_release",
    "provider_route_change",
    "bot_restart",
    "forced_one_share_success_counting",
    "real_execution_quality_approval",
]


def _safe_float(value: Any) -> float | None:
    if value in (None, "", "-"):
        return None
    try:
        return float(str(value).replace(",", "").replace("+", "").replace("%", ""))
    except ValueError:
        return None


def _safe_int(value: Any) -> int:
    numeric = _safe_float(value)
    return int(numeric) if numeric is not None else 0


def _boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _fields(row: dict[str, Any]) -> dict[str, Any]:
    fields = row.get("fields")
    return fields if isinstance(fields, dict) else {}


def _pipeline_path(target_date: str) -> Path:
    return PIPELINE_EVENTS_DIR / f"pipeline_events_{target_date}.jsonl"


def _default_output_paths(target_date: str) -> tuple[Path, Path]:
    return (
        REPORT_DIR / f"rising_missed_intraday_feedback_{target_date}.json",
        REPORT_DIR / f"rising_missed_intraday_feedback_{target_date}.md",
    )


def _is_forced_rising_missed(row: dict[str, Any]) -> bool:
    fields = _fields(row)
    return (
        row.get("stage") == "rising_missed_one_share_entry"
        or str(fields.get("forced_entry_reason") or "") == FORCED_REASON
        or _boolish(fields.get("rising_missed_one_share_entry_forced"))
    )


def _forced_entry_record(row: dict[str, Any]) -> dict[str, Any]:
    fields = _fields(row)
    return {
        "record_id": str(row.get("record_id") or "").strip(),
        "stock_code": row.get("stock_code"),
        "stock_name": row.get("stock_name"),
        "first_rising_ts": row.get("emitted_at"),
        "source_signature": fields.get("source_signature"),
        "scanner_promotion_reason": fields.get("scanner_promotion_reason"),
        "rising_missed_class": fields.get("rising_missed_class"),
        "rising_missed_class_reason": fields.get("rising_missed_class_reason"),
        "price_delta_since_first_seen_pct": _safe_float(
            fields.get("price_delta_since_first_seen_pct")
            or fields.get("rising_missed_one_share_entry_positive_delta_pct")
        ),
    }


def _quality_label(item: dict[str, Any]) -> str:
    latest_profit = item.get("latest_profit_rate")
    max_profit = item.get("max_profit_seen")
    min_profit = item.get("min_profit_seen")
    exit_rule = str(item.get("exit_rule_candidate") or "")
    sell_reason = str(item.get("sell_reason_type") or "").upper()
    if sell_reason == "LOSS" or "stop" in exit_rule:
        return "rising_missed_initial_quality_fail"
    if latest_profit is not None and latest_profit < 0:
        return "rising_missed_initial_quality_fail_open"
    if min_profit is not None and min_profit <= -2.0 and (max_profit is None or max_profit < 0.5):
        return "rising_missed_initial_quality_fail_open"
    if max_profit is not None and max_profit >= 1.0 and (latest_profit is not None and latest_profit >= 0):
        return "rising_missed_scale_in_rescue_warning"
    return "rising_missed_initial_quality_review"


def _update_holding_record(item: dict[str, Any], row: dict[str, Any]) -> None:
    fields = _fields(row)
    profit_rate = _safe_float(fields.get("profit_rate"))
    peak_profit = _safe_float(fields.get("peak_profit"))
    avg_down_count = _safe_int(fields.get("avg_down_count"))
    item["latest_stage"] = row.get("stage")
    item["latest_snapshot_ts"] = row.get("emitted_at")
    item["latest_profit_rate"] = profit_rate
    item["latest_peak_profit"] = peak_profit
    item["latest_buy_qty"] = _safe_int(fields.get("buy_qty"))
    item["latest_reason"] = fields.get("reason") or fields.get("scale_in_action_reason")
    item["latest_gate_reason"] = (
        fields.get("scale_in_gate_reason")
        or fields.get("scale_in_blocker_reason")
        or fields.get("gate_reason")
    )
    item["exit_rule_candidate"] = fields.get("exit_rule_candidate") or fields.get("exit_rule")
    item["sell_reason_type"] = fields.get("sell_reason_type")
    item["max_avg_down_count"] = max(_safe_int(item.get("max_avg_down_count")), avg_down_count)
    if avg_down_count >= AVG_DOWN_FAIL_FLOOR:
        item["avg_down_ge2_seen"] = True
        item["first_avg_down_ge2_ts"] = item.get("first_avg_down_ge2_ts") or row.get("emitted_at")
    if profit_rate is not None:
        item["min_profit_seen"] = (
            profit_rate
            if item.get("min_profit_seen") is None
            else min(float(item["min_profit_seen"]), profit_rate)
        )
        item["max_profit_seen"] = (
            profit_rate
            if item.get("max_profit_seen") is None
            else max(float(item["max_profit_seen"]), profit_rate)
        )


def _regression_label(item: dict[str, Any]) -> str:
    final_profit = item.get("final_profit_rate")
    if final_profit is None:
        return "first_touch_open_unresolved"
    if final_profit > 0:
        return "first_touch_recovered_profit"
    return "first_touch_loss_or_flat"


def _first_touch_shadow_decision(item: dict[str, Any]) -> dict[str, Any]:
    submitted_count = _safe_int(item.get("avg_down_submitted_event_count"))
    touch_ai = _safe_float(item.get("first_touch_ai_score"))
    touch_peak = _safe_float(item.get("first_touch_peak_profit"))
    blocker_counts = item.get("blocker_counts_before_first_touch")
    blocker_counts = blocker_counts if isinstance(blocker_counts, dict) else {}
    repeated_blocker_count = sum(_safe_int(value) for value in blocker_counts.values())
    support_signals: list[str] = []
    risk_signals: list[str] = []
    if touch_peak is not None and touch_peak >= 0.30:
        support_signals.append("prior_peak_recovery_ge_0_30")
    if touch_ai is not None and touch_ai >= 70.0:
        support_signals.append("ai_score_ge_70")
    if repeated_blocker_count >= 8:
        risk_signals.append("repeated_pre_touch_blockers_ge_8")
    if touch_ai is not None and touch_ai < 60.0:
        risk_signals.append("ai_score_lt_60")
    if submitted_count > 1:
        risk_signals.append("cap1_extra_avg_down_would_block")
    cap1_decision = "cap1_not_applicable_no_submit"
    if submitted_count == 1:
        cap1_decision = "cap1_first_avg_down_allowed"
    elif submitted_count > 1:
        cap1_decision = "cap1_extra_avg_down_would_block"
    return {
        "first_touch_shadow_decision_authority": "source_only_no_runtime_effect",
        "first_touch_shadow_cap1_decision": cap1_decision,
        "first_touch_shadow_support_signals": support_signals,
        "first_touch_shadow_risk_signals": risk_signals,
        "first_touch_shadow_repeated_blocker_count": repeated_blocker_count,
    }


def _touch_reason(fields: dict[str, Any]) -> str | None:
    return (
        fields.get("gate_reason")
        or fields.get("block_reason")
        or fields.get("reason")
        or fields.get("scale_in_gate_reason")
        or fields.get("scale_in_blocker_reason")
    )


def _touch_feature(row: dict[str, Any]) -> dict[str, Any]:
    fields = _fields(row)
    return {
        "first_touch_ts": row.get("emitted_at"),
        "first_touch_stage": row.get("stage"),
        "first_touch_profit_rate": _safe_float(fields.get("profit_rate")),
        "first_touch_peak_profit": _safe_float(fields.get("peak_profit")),
        "first_touch_ai_score": _safe_float(fields.get("current_ai_score") or fields.get("ai_score")),
        "first_touch_gate_reason": _touch_reason(fields),
        "first_touch_avgdown_decision_allowed": fields.get("first_touch_avgdown_decision_allowed"),
        "first_touch_avgdown_decision_reason": fields.get("first_touch_avgdown_decision_reason"),
        "first_touch_avgdown_support_signals": fields.get("first_touch_avgdown_support_signals"),
        "first_touch_avgdown_risk_signals": fields.get("first_touch_avgdown_risk_signals"),
        "first_touch_avgdown_repeated_blocker_count": _safe_int(
            fields.get("first_touch_avgdown_repeated_blocker_count")
        ),
        "first_touch_avgdown_decision_authority": fields.get("first_touch_avgdown_decision_authority"),
    }


def _update_first_touch_regression(
    item: dict[str, Any],
    row: dict[str, Any],
    blocker_counts: Counter[str],
    blocker_reason_counts: Counter[str],
) -> None:
    fields = _fields(row)
    stage = str(row.get("stage") or "")
    is_first_touch_stage = (
        "stop_line_touch_mandatory_avg_down" in stage
        or stage == "stop_line_touch_first_touch_avgdown_decision_blocked"
    )
    if is_first_touch_stage and not item.get("first_touch_seen"):
        item["first_touch_seen"] = True
        item.update(_touch_feature(row))
        item["blocker_counts_before_first_touch"] = dict(blocker_counts)
        item["blocker_reason_counts_before_first_touch"] = dict(blocker_reason_counts)
    if stage == "stop_line_touch_first_touch_avgdown_decision_blocked":
        item["first_touch_avgdown_decision_blocked"] = True
    if "stop_line_touch_mandatory_avg_down_submitted" in stage:
        item["first_touch_avg_down_submitted"] = True
        item["first_touch_submitted_ts"] = item.get("first_touch_submitted_ts") or row.get("emitted_at")
        item["avg_down_submitted_event_count"] = _safe_int(item.get("avg_down_submitted_event_count")) + 1
    if "stop_line_touch_mandatory_avg_down_not_eligible" in stage:
        item["first_touch_not_eligible_seen"] = True
        item["first_touch_not_eligible_reason"] = item.get("first_touch_not_eligible_reason") or _touch_reason(fields)
    if stage.startswith("blocked_") and not item.get("first_touch_seen"):
        blocker_counts[stage] += 1
        reason = _touch_reason(fields)
        if reason:
            blocker_reason_counts[str(reason)] += 1
    if stage == "sell_completed":
        profit_rate = _safe_float(fields.get("profit_rate"))
        if profit_rate is not None:
            item["final_profit_rate"] = profit_rate
            item["final_stage"] = stage
            item["final_ts"] = row.get("emitted_at")
    avg_down_count = _safe_int(fields.get("avg_down_count"))
    if avg_down_count:
        item["max_avg_down_count"] = max(_safe_int(item.get("max_avg_down_count")), avg_down_count)


def _build_first_touch_regression_rows(
    forced: dict[str, dict[str, Any]],
    pipeline_path: Path,
) -> list[dict[str, Any]]:
    candidates: dict[str, dict[str, Any]] = {
        record_id: {
            **entry,
            "record_id": record_id,
            "first_touch_seen": False,
            "first_touch_avg_down_submitted": False,
            "first_touch_not_eligible_seen": False,
            "max_avg_down_count": 0,
            "avg_down_submitted_event_count": 0,
        }
        for record_id, entry in forced.items()
    }
    blocker_counts: dict[str, Counter[str]] = {record_id: Counter() for record_id in candidates}
    blocker_reason_counts: dict[str, Counter[str]] = {record_id: Counter() for record_id in candidates}
    for row in iter_jsonl(pipeline_path):
        record_id = str(row.get("record_id") or "").strip()
        if record_id not in candidates:
            continue
        _update_first_touch_regression(
            candidates[record_id],
            row,
            blocker_counts[record_id],
            blocker_reason_counts[record_id],
        )
    rows: list[dict[str, Any]] = []
    for item in candidates.values():
        if not item.get("first_touch_seen"):
            continue
        item["first_touch_regression_label"] = _regression_label(item)
        item.update(_first_touch_shadow_decision(item))
        item["decision_authority"] = "source_only_first_touch_regression_table"
        item["actual_order_submitted"] = False
        item["broker_order_forbidden"] = True
        item["runtime_effect"] = False
        item["allowed_runtime_apply"] = False
        item["forbidden_uses"] = FORBIDDEN_USES
        rows.append(item)
    rows.sort(key=lambda item: (str(item.get("first_touch_ts") or ""), str(item.get("record_id") or "")))
    return rows


def build_report(
    target_date: str,
    *,
    pipeline_path: Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    pipeline_path = pipeline_path or _pipeline_path(target_date)
    resolved_pipeline_path = existing_or_gzip_path(pipeline_path)
    generated_at = generated_at or datetime.now(KST).isoformat(timespec="seconds")
    forced: dict[str, dict[str, Any]] = {}
    holding_by_record: dict[str, dict[str, Any]] = {}
    source_quality_status = "pass" if resolved_pipeline_path.exists() else "missing_pipeline_events"

    for row in iter_jsonl(pipeline_path):
        record_id = str(row.get("record_id") or "").strip()
        if not record_id:
            continue
        if _is_forced_rising_missed(row):
            item = forced.setdefault(record_id, _forced_entry_record(row))
            item["rising_missed_stage_count"] = _safe_int(item.get("rising_missed_stage_count")) + 1
            if row.get("stage") == "rising_missed_one_share_entry":
                first_count = item.get("rising_missed_stage_count", 1)
                item.update(_forced_entry_record(row))
                item["rising_missed_stage_count"] = first_count
        if row.get("pipeline") == "HOLDING_PIPELINE":
            fields = _fields(row)
            if "avg_down_count" not in fields and "profit_rate" not in fields:
                continue
            item = holding_by_record.setdefault(
                record_id,
                {
                    "record_id": record_id,
                    "stock_code": row.get("stock_code"),
                    "stock_name": row.get("stock_name"),
                    "max_avg_down_count": 0,
                    "min_profit_seen": None,
                    "max_profit_seen": None,
                    "avg_down_ge2_seen": False,
                },
            )
            _update_holding_record(item, row)

    rows: list[dict[str, Any]] = []
    for record_id, entry in forced.items():
        holding = holding_by_record.get(record_id)
        if not holding or not holding.get("avg_down_ge2_seen"):
            continue
        item = {**entry, **holding}
        item["feedback_label"] = _quality_label(item)
        item["decision_authority"] = "source_only_intraday_feedback_no_runtime_mutation"
        item["runtime_effect"] = False
        item["allowed_runtime_apply"] = False
        item["forbidden_uses"] = FORBIDDEN_USES
        rows.append(item)

    rows.sort(key=lambda item: (str(item.get("first_avg_down_ge2_ts") or ""), str(item.get("record_id") or "")))
    first_touch_rows = _build_first_touch_regression_rows(forced, pipeline_path)
    label_counts = Counter(str(item.get("feedback_label") or "unknown") for item in rows)
    first_touch_label_counts = Counter(
        str(item.get("first_touch_regression_label") or "unknown") for item in first_touch_rows
    )
    initial_fail_count = sum(
        count
        for label, count in label_counts.items()
        if label in {"rising_missed_initial_quality_fail", "rising_missed_initial_quality_fail_open"}
    )
    code_improvement_orders = []
    if rows:
        code_improvement_orders.append(
            {
                "order_id": "order_rising_missed_initial_quality_feedback_loop",
                "title": "rising missed initial quality feedback loop",
                "source_report_type": "rising_missed_intraday_feedback",
                "lifecycle_stage": "entry",
                "target_subsystem": "rising_missed_entry_classifier",
                "route": "instrumentation_order",
                "mapped_family": "rising_missed_initial_quality_feedback_loop",
                "threshold_family": "rising_missed_initial_quality_feedback_loop",
                "improvement_type": "source_only_intraday_feedback_workorder",
                "confidence": "same_day_source_only",
                "priority": 1 if initial_fail_count else 2,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "decision_authority": "source_only_intraday_feedback_no_runtime_mutation",
                "implementation_status": "implemented",
                "implementation_provenance": {
                    "implementation_type": "rising_missed_avg_down_ge2_intraday_detector",
                    "rising_missed_avg_down_ge2_count": len(rows),
                    "initial_quality_fail_count": initial_fail_count,
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "root_cause_closure_status_hint": "implementation_done",
                },
                "expected_ev_effect": (
                    "Continuously separate rising-missed entries that need two or more average-down attempts "
                    "from profitable scout examples before proposing any classifier expansion."
                ),
                "evidence": [
                    f"rising_missed_avg_down_ge2_count={len(rows)}",
                    f"initial_quality_fail_count={initial_fail_count}",
                    "feedback_label_counts="
                    + ",".join(f"{key}={value}" for key, value in label_counts.most_common()),
                    f"source_quality_status={source_quality_status}",
                ],
                "source_paths": [str(resolved_pipeline_path)],
                "files_likely_touched": [
                    "src/engine/scalping/rising_missed_one_share_entry.py",
                    "src/engine/monitoring/intraday_entry_blocker_diagnostics.py",
                    "src/engine/monitoring/rising_missed_scout_workorder.py",
                ],
                "acceptance_tests": [
                    "PYTHONPATH=. .venv/bin/pytest src/tests/test_rising_missed_intraday_feedback.py src/tests/test_rising_missed_scout_workorder.py src/tests/test_build_code_improvement_workorder.py",
                    "feedback loop remains source-only and does not mutate intraday runtime thresholds, broker/order guards, provider route, bot state, or scale-in quantity/caps",
                ],
                "forbidden_uses": FORBIDDEN_USES,
            }
        )

    return {
        "schema_version": 1,
        "report_type": "rising_missed_intraday_feedback",
        "target_date": target_date,
        "generated_at": generated_at,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "decision_authority": "source_only_intraday_feedback_no_runtime_mutation",
        "forbidden_uses": FORBIDDEN_USES,
        "metric_contracts": {
            "rising_missed_avg_down_ge2_feedback": {
                "metric_role": "entry_quality_intraday_feedback",
                "decision_authority": "source_only_intraday_feedback_no_runtime_mutation",
                "window_policy": "same_day_intraday_pipeline_events",
                "sample_floor": "1_rising_missed_forced_entry_with_avg_down_count_ge2",
                "primary_decision_metric": "rising_missed_avg_down_ge2_count",
                "source_quality_gate": "record_id_joined_forced_rising_missed_entry_and_holding_avg_down_snapshot",
                "forbidden_uses": FORBIDDEN_USES,
            },
            "rising_missed_first_touch_regression": {
                "metric_role": "source_only_first_touch_regression",
                "decision_authority": "source_only_first_touch_regression_table",
                "window_policy": "same_day_intraday_pipeline_events_continuously_updated",
                "sample_floor": "1_rising_missed_forced_entry_with_first_stop_line_touch",
                "primary_decision_metric": "first_touch_regression_label_counts",
                "source_quality_gate": "record_id_joined_forced_rising_missed_entry_and_first_stop_line_touch_event",
                "forbidden_uses": FORBIDDEN_USES,
            }
        },
        "source_paths": {"pipeline_events": str(resolved_pipeline_path)},
        "source_quality": {
            "status": source_quality_status,
            "pipeline_events_exists": resolved_pipeline_path.exists(),
        },
        "summary": {
            "forced_rising_missed_record_count": len(forced),
            "holding_record_count": len(holding_by_record),
            "rising_missed_avg_down_ge2_count": len(rows),
            "first_touch_regression_record_count": len(first_touch_rows),
            "first_touch_avg_down_submitted_count": sum(
                1 for item in first_touch_rows if item.get("first_touch_avg_down_submitted")
            ),
            "first_touch_not_eligible_count": sum(
                1 for item in first_touch_rows if item.get("first_touch_not_eligible_seen")
            ),
            "first_touch_avgdown_decision_blocked_count": sum(
                1 for item in first_touch_rows if item.get("first_touch_avgdown_decision_blocked")
            ),
            "first_touch_closed_count": sum(1 for item in first_touch_rows if item.get("final_profit_rate") is not None),
            "first_touch_profitable_count": first_touch_label_counts.get("first_touch_recovered_profit", 0),
            "first_touch_loss_or_flat_count": first_touch_label_counts.get("first_touch_loss_or_flat", 0),
            "first_touch_regression_label_counts": [
                {"first_touch_regression_label": key, "count": value}
                for key, value in first_touch_label_counts.most_common()
            ],
            "initial_quality_fail_count": initial_fail_count,
            "scale_in_rescue_warning_count": label_counts.get("rising_missed_scale_in_rescue_warning", 0),
            "feedback_label_counts": [
                {"feedback_label": key, "count": value} for key, value in label_counts.most_common()
            ],
            "code_improvement_order_count": len(code_improvement_orders),
        },
        "records": rows[:100],
        "first_touch_regression_rows": first_touch_rows[:200],
        "code_improvement_orders": code_improvement_orders,
    }


def write_outputs(report: dict[str, Any], *, output_json: Path, output_md: Path) -> None:
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    lines = [
        f"# {report.get('target_date')} Rising Missed Intraday Feedback",
        "",
        f"- generated_at: {report.get('generated_at')}",
        "- decision_authority: source_only_intraday_feedback_no_runtime_mutation",
        "- runtime_effect: false",
        "- allowed_runtime_apply: false",
        "- forbidden_uses: " + ", ".join(FORBIDDEN_USES),
        "",
        "## Summary",
        "",
        f"- forced_rising_missed_record_count: {summary.get('forced_rising_missed_record_count')}",
        f"- holding_record_count: {summary.get('holding_record_count')}",
        f"- rising_missed_avg_down_ge2_count: {summary.get('rising_missed_avg_down_ge2_count')}",
        f"- first_touch_regression_record_count: {summary.get('first_touch_regression_record_count')}",
        f"- first_touch_avg_down_submitted_count: {summary.get('first_touch_avg_down_submitted_count')}",
        f"- first_touch_avgdown_decision_blocked_count: {summary.get('first_touch_avgdown_decision_blocked_count')}",
        f"- first_touch_closed_count: {summary.get('first_touch_closed_count')}",
        f"- first_touch_profitable_count: {summary.get('first_touch_profitable_count')}",
        f"- first_touch_loss_or_flat_count: {summary.get('first_touch_loss_or_flat_count')}",
        f"- initial_quality_fail_count: {summary.get('initial_quality_fail_count')}",
        f"- scale_in_rescue_warning_count: {summary.get('scale_in_rescue_warning_count')}",
        f"- code_improvement_order_count: {summary.get('code_improvement_order_count')}",
        "",
        "## First Touch Regression",
        "",
    ]
    for item in report.get("first_touch_regression_rows") or []:
        blocker_counts = item.get("blocker_counts_before_first_touch") or {}
        top_blockers = ",".join(f"{key}={value}" for key, value in list(blocker_counts.items())[:4])
        display_item = {
            **item,
            "final_profit_rate": item.get("final_profit_rate"),
            "first_touch_shadow_cap1_decision": item.get("first_touch_shadow_cap1_decision", "-"),
            "first_touch_avgdown_decision_reason": item.get("first_touch_avgdown_decision_reason") or "-",
            "top_blockers": top_blockers,
        }
        lines.append(
            "- record_id={record_id} code={stock_code} name={stock_name} label={first_touch_regression_label} "
            "submitted={first_touch_avg_down_submitted} touch_profit={first_touch_profit_rate} "
            "touch_peak={first_touch_peak_profit} touch_ai={first_touch_ai_score} "
            "final_profit={final_profit_rate} submitted_count={avg_down_submitted_event_count} "
            "runtime_decision={first_touch_avgdown_decision_reason} shadow_cap1={first_touch_shadow_cap1_decision} "
            "max_avg_down={max_avg_down_count} blockers={top_blockers}".format(**display_item)
        )
    lines.extend(["", "## Records", ""])
    for item in report.get("records") or []:
        lines.append(
            "- record_id={record_id} code={stock_code} name={stock_name} label={feedback_label} "
            "avg_down={max_avg_down_count} latest_profit={latest_profit_rate} min_profit={min_profit_seen} "
            "max_profit={max_profit_seen} latest_gate={latest_gate_reason}".format(**item)
        )
    output_md.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build rising missed intraday feedback report.")
    parser.add_argument("--target-date", default=datetime.now(KST).strftime("%Y-%m-%d"))
    parser.add_argument("--pipeline-path", type=Path)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--generated-at")
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args(argv)
    report = build_report(
        args.target_date,
        pipeline_path=args.pipeline_path,
        generated_at=args.generated_at,
    )
    default_json, default_md = _default_output_paths(args.target_date)
    output_json = args.output_json or default_json
    output_md = args.output_md or default_md
    write_outputs(report, output_json=output_json, output_md=output_md)
    if args.print_summary:
        print(
            json.dumps(
                {"output_json": str(output_json), "output_md": str(output_md), **report["summary"]},
                ensure_ascii=False,
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
