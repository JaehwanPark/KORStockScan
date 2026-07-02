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
    label_counts = Counter(str(item.get("feedback_label") or "unknown") for item in rows)
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
            "initial_quality_fail_count": initial_fail_count,
            "scale_in_rescue_warning_count": label_counts.get("rising_missed_scale_in_rescue_warning", 0),
            "feedback_label_counts": [
                {"feedback_label": key, "count": value} for key, value in label_counts.most_common()
            ],
            "code_improvement_order_count": len(code_improvement_orders),
        },
        "records": rows[:100],
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
        f"- initial_quality_fail_count: {summary.get('initial_quality_fail_count')}",
        f"- scale_in_rescue_warning_count: {summary.get('scale_in_rescue_warning_count')}",
        f"- code_improvement_order_count: {summary.get('code_improvement_order_count')}",
        "",
        "## Records",
        "",
    ]
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
