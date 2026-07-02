from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from collections.abc import Iterable, Iterator
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[3]
KST = timezone(timedelta(hours=9))
FORCED_REASON = "rising_missed_one_share_entry"
FORBIDDEN_USES = [
    "runtime_threshold_mutation",
    "stale_submit_bypass",
    "broker_guard_bypass",
    "order_guard_relaxation",
    "provider_route_change",
    "bot_restart",
    "forced_one_share_success_counting",
    "real_execution_quality_approval",
]
SCALE_IN_FORBIDDEN_USES = [
    *FORBIDDEN_USES,
    "scale_in_guard_bypass",
    "quantity_guard_relaxation",
    "position_cap_release",
    "real_scale_in_submit_approval",
]


def _safe_float(value: Any) -> float | None:
    if value in (None, "", "-"):
        return None
    try:
        return float(str(value).replace(",", "").replace("+", "").replace("%", ""))
    except ValueError:
        return None


def _boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                yield payload


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return list(_iter_jsonl(path))


def _default_pipeline_path(target_date: str) -> Path:
    return PROJECT_ROOT / "data" / "pipeline_events" / f"pipeline_events_{target_date}.jsonl"


def _default_post_sell_path(target_date: str) -> Path:
    return PROJECT_ROOT / "data" / "post_sell" / f"post_sell_candidates_{target_date}.jsonl"


def _default_diagnostic_path(target_date: str) -> Path:
    return (
        PROJECT_ROOT
        / "data"
        / "report"
        / "intraday_entry_blocker_diagnostics"
        / f"intraday_entry_blocker_diagnostics_{target_date}.json"
    )


def _default_intraday_feedback_path(target_date: str) -> Path:
    return (
        PROJECT_ROOT
        / "data"
        / "report"
        / "rising_missed_intraday_feedback"
        / f"rising_missed_intraday_feedback_{target_date}.json"
    )


def _default_output_paths(target_date: str) -> tuple[Path, Path]:
    base = PROJECT_ROOT / "data" / "report" / "rising_missed_scout_workorder"
    return (
        base / f"rising_missed_scout_workorder_{target_date}.json",
        base / f"rising_missed_scout_workorder_{target_date}.md",
    )


def _is_forced_scout(row: dict[str, Any]) -> bool:
    fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
    return (
        row.get("stage") == "rising_missed_one_share_entry"
        or fields.get("forced_entry_reason") == FORCED_REASON
        or _boolish(fields.get("rising_missed_one_share_entry_forced"))
    )


def _event_features(row: dict[str, Any]) -> dict[str, Any]:
    fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
    return {
        "stock_code": row.get("stock_code"),
        "stock_name": row.get("stock_name"),
        "emitted_at": row.get("emitted_at"),
        "scanner_promotion_id": fields.get("scanner_promotion_id"),
        "scanner_promotion_reason": fields.get("scanner_promotion_reason"),
        "source_signature": fields.get("source_signature"),
        "price_delta_since_first_seen_pct": _safe_float(fields.get("price_delta_since_first_seen_pct")),
        "entry_price": fields.get("rising_missed_one_share_entry_price")
        or fields.get("current_price")
        or fields.get("current_price_observed"),
    }


def _index_forced_scouts(rows: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    forced: dict[str, dict[str, Any]] = {}
    for row in rows:
        record_id = str(row.get("record_id") or "").strip()
        if not record_id or not _is_forced_scout(row):
            continue
        item = forced.setdefault(
            record_id,
            {
                "record_id": record_id,
                "first_forced_event": _event_features(row),
                "forced_event_count": 0,
            },
        )
        item["forced_event_count"] += 1
        if row.get("stage") == "rising_missed_one_share_entry":
            item["first_forced_event"] = _event_features(row)
    return forced


def _joined_scout_outcomes(
    *,
    forced: dict[str, dict[str, Any]],
    stage_counts: dict[str, Counter[str]],
    post_sell_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    outcomes: list[dict[str, Any]] = []
    for sell in post_sell_rows:
        record_id = str(sell.get("recommendation_id") or "").strip()
        if record_id not in forced:
            continue
        profit_rate = _safe_float(sell.get("profit_rate"))
        entry = forced[record_id].get("first_forced_event") or {}
        counts = stage_counts.get(record_id, Counter())
        outcomes.append(
            {
                "record_id": record_id,
                "stock_code": sell.get("stock_code") or entry.get("stock_code"),
                "stock_name": sell.get("stock_name") or entry.get("stock_name"),
                "entry_time": entry.get("emitted_at"),
                "sell_time": sell.get("sell_time"),
                "profit_rate": profit_rate,
                "peak_profit": _safe_float(sell.get("peak_profit")),
                "held_sec": _safe_float(sell.get("held_sec")),
                "exit_rule": sell.get("exit_rule"),
                "scanner_promotion_reason": entry.get("scanner_promotion_reason"),
                "source_signature": entry.get("source_signature"),
                "price_delta_since_first_seen_pct": entry.get("price_delta_since_first_seen_pct"),
                "forced_event_count": forced[record_id].get("forced_event_count", 0),
                "latency_pass_count": counts.get("latency_pass", 0),
                "order_bundle_submitted_count": counts.get("order_bundle_submitted", 0),
                "budget_pass_count": counts.get("budget_pass", 0),
            }
        )
    return outcomes


def _current_missed_summary(diagnostic: dict[str, Any]) -> dict[str, Any]:
    rows = [row for row in diagnostic.get("rising_missed_buy") or [] if isinstance(row, dict)]
    class_counts = Counter(str(row.get("rising_missed_class") or "unknown") for row in rows)
    top_rows = []
    for row in rows[:10]:
        latest = row.get("latest_blocker") if isinstance(row.get("latest_blocker"), dict) else {}
        top_rows.append(
            {
                "stock_code": row.get("stock_code"),
                "stock_name": row.get("stock_name"),
                "rising_missed_class": row.get("rising_missed_class"),
                "rising_missed_one_share_eligible": bool(row.get("rising_missed_one_share_eligible")),
                "max_price_delta_since_first_seen_pct": row.get("max_price_delta_since_first_seen_pct"),
                "latest_stage": latest.get("stage"),
                "latest_reason": latest.get("reason"),
                "stale_or_delayed_eval_category_counts": row.get("stale_or_delayed_eval_category_counts") or {},
            }
        )
    return {
        "count": len(rows),
        "class_counts": [{"class": key, "count": value} for key, value in class_counts.most_common()],
        "eligible_count": sum(1 for row in rows if row.get("rising_missed_one_share_eligible")),
        "top_rows": top_rows,
    }


def _profit_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    values = [row["profit_rate"] for row in rows if row.get("profit_rate") is not None]
    return {
        "sample": len(rows),
        "valid_profit_sample": len(values),
        "avg_profit_rate": round(sum(values) / len(values), 4) if values else None,
        "min_profit_rate": min(values) if values else None,
        "max_profit_rate": max(values) if values else None,
    }


def _signature_counts(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter(str(row.get("source_signature") or "-") for row in rows)
    return [{"source_signature": key, "count": value} for key, value in counts.most_common(10)]


def _counter_rows(counter: Counter[str], *, key_name: str = "reason", limit: int = 10) -> list[dict[str, Any]]:
    return [{key_name: key, "count": value} for key, value in counter.most_common(limit)]


def _counter_text(counter_rows: list[dict[str, Any]], *, key_name: str = "reason") -> str:
    return ",".join(f"{item.get(key_name)}={item.get('count')}" for item in counter_rows) or "-"


def _scale_in_reason(row: dict[str, Any]) -> str:
    fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
    return str(
        fields.get("scale_in_blocker_reason")
        or fields.get("scale_in_gate_reason")
        or fields.get("reason")
        or ""
    )


def _scale_in_action(row: dict[str, Any]) -> str:
    fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
    return str(
        fields.get("scale_in_action_type")
        or fields.get("scale_in_arm")
        or fields.get("chosen_action")
        or "-"
    )


def _scale_in_event_summary(row: dict[str, Any], outcome_by_record: dict[str, dict[str, Any]]) -> dict[str, Any]:
    fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
    record_id = str(row.get("record_id") or "")
    outcome = outcome_by_record.get(record_id) or {}
    return {
        "record_id": record_id,
        "stock_code": row.get("stock_code"),
        "stock_name": row.get("stock_name"),
        "emitted_at": row.get("emitted_at"),
        "stage": row.get("stage"),
        "profit_rate": _safe_float(fields.get("profit_rate")),
        "peak_profit": _safe_float(fields.get("peak_profit")),
        "current_ai_score": _safe_float(fields.get("current_ai_score") or fields.get("ai_score")),
        "scale_in_action_type": _scale_in_action(row),
        "scale_in_gate_allowed": fields.get("scale_in_gate_allowed"),
        "scale_in_reason": _scale_in_reason(row),
        "distance_to_buy_bps": _safe_float(fields.get("distance_to_buy_bps")),
        "outcome_profit_rate": outcome.get("profit_rate"),
        "outcome_peak_profit": outcome.get("peak_profit"),
        "exit_rule": outcome.get("exit_rule"),
    }


def _new_scale_in_accumulator(winners: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "winner_record_ids": {str(row.get("record_id") or "") for row in winners},
        "outcome_by_record": {str(row.get("record_id") or ""): row for row in winners},
        "pyramid_reason_counts": Counter(),
        "price_guard_reason_counts": Counter(),
        "qty_block_reason_counts": Counter(),
        "scale_event_record_ids": set(),
        "pyramid_candidate_record_ids": set(),
        "pyramid_ok_record_ids": set(),
        "price_guard_record_ids": set(),
        "qty_block_record_ids": set(),
        "executed_record_ids": set(),
        "price_guard_examples": [],
        "qty_block_examples": [],
        "executed_examples": [],
        "latest_by_record": {},
        "executed_event_count": 0,
    }


def _update_scale_in_accumulator(accumulator: dict[str, Any], row: dict[str, Any]) -> None:
    if row.get("pipeline") != "HOLDING_PIPELINE":
        return
    record_id = str(row.get("record_id") or "")
    if record_id not in accumulator["winner_record_ids"]:
        return
    stage = str(row.get("stage") or "")
    action = _scale_in_action(row)
    reason = _scale_in_reason(row)
    is_pyramid_snapshot = stage == "stat_action_decision_snapshot" and action == "PYRAMID"
    is_scale_event = is_pyramid_snapshot or stage in {
        "scale_in_price_guard_block",
        "scale_in_qty_block",
        "scale_in_executed",
        "scale_in_price_resolved",
        "scale_in_price_p2_observe",
        "scale_in_quote_consistency_defensive_bypass",
    }
    if not is_scale_event:
        return
    accumulator["scale_event_record_ids"].add(record_id)
    accumulator["latest_by_record"][record_id] = _scale_in_event_summary(row, accumulator["outcome_by_record"])
    if is_pyramid_snapshot:
        accumulator["pyramid_candidate_record_ids"].add(record_id)
        accumulator["pyramid_reason_counts"][reason or "no_reason"] += 1
        if reason == "scalping_pyramid_ok":
            accumulator["pyramid_ok_record_ids"].add(record_id)
    elif stage == "scale_in_price_guard_block":
        accumulator["price_guard_record_ids"].add(record_id)
        accumulator["price_guard_reason_counts"][reason or "no_reason"] += 1
        if len(accumulator["price_guard_examples"]) < 12:
            accumulator["price_guard_examples"].append(
                _scale_in_event_summary(row, accumulator["outcome_by_record"])
            )
    elif stage == "scale_in_qty_block":
        accumulator["qty_block_record_ids"].add(record_id)
        accumulator["qty_block_reason_counts"][reason or "no_reason"] += 1
        if len(accumulator["qty_block_examples"]) < 12:
            accumulator["qty_block_examples"].append(
                _scale_in_event_summary(row, accumulator["outcome_by_record"])
            )
    elif stage == "scale_in_executed":
        accumulator["executed_record_ids"].add(record_id)
        accumulator["executed_event_count"] += 1
        if len(accumulator["executed_examples"]) < 12:
            accumulator["executed_examples"].append(
                _scale_in_event_summary(row, accumulator["outcome_by_record"])
            )


def _finish_scale_in_accumulator(accumulator: dict[str, Any], winners: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "decision_authority": "source_only_scale_in_bottleneck_analysis",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "profitable_forced_scout_record_count": len(winners),
        "record_with_scale_in_event_count": len(accumulator["scale_event_record_ids"]),
        "pyramid_candidate_record_count": len(accumulator["pyramid_candidate_record_ids"]),
        "pyramid_ok_record_count": len(accumulator["pyramid_ok_record_ids"]),
        "scale_in_executed_record_count": len(accumulator["executed_record_ids"]),
        "scale_in_executed_event_count": accumulator["executed_event_count"],
        "price_guard_block_record_count": len(accumulator["price_guard_record_ids"]),
        "qty_block_record_count": len(accumulator["qty_block_record_ids"]),
        "pyramid_reason_counts": _counter_rows(accumulator["pyramid_reason_counts"]),
        "price_guard_reason_counts": _counter_rows(accumulator["price_guard_reason_counts"]),
        "qty_block_reason_counts": _counter_rows(accumulator["qty_block_reason_counts"]),
        "price_guard_examples": accumulator["price_guard_examples"],
        "qty_block_examples": accumulator["qty_block_examples"],
        "executed_examples": accumulator["executed_examples"],
        "latest_scale_in_event_by_record": list(accumulator["latest_by_record"].values())[:20],
        "forbidden_uses": SCALE_IN_FORBIDDEN_USES,
    }


def _pipeline_stage_counts_and_scale_in_summary(
    path: Path,
    *,
    forced_record_ids: set[str],
    winners: list[dict[str, Any]],
) -> tuple[dict[str, Counter[str]], dict[str, Any]]:
    stage_counts: dict[str, Counter[str]] = defaultdict(Counter)
    scale_in_accumulator = _new_scale_in_accumulator(winners)
    for row in _iter_jsonl(path):
        record_id = str(row.get("record_id") or "").strip()
        if record_id in forced_record_ids:
            stage_counts[record_id][str(row.get("stage") or "")] += 1
        _update_scale_in_accumulator(scale_in_accumulator, row)
    return stage_counts, _finish_scale_in_accumulator(scale_in_accumulator, winners)


def _build_operational_workorders(
    *,
    winners: list[dict[str, Any]],
    losers: list[dict[str, Any]],
    current_missed: dict[str, Any],
    scale_in_bottleneck: dict[str, Any],
    intraday_feedback: dict[str, Any],
    source_paths: dict[str, str],
) -> list[dict[str, Any]]:
    orders: list[dict[str, Any]] = []
    feedback_summary = (
        intraday_feedback.get("summary")
        if isinstance(intraday_feedback.get("summary"), dict)
        else {}
    )
    feedback_count = int(feedback_summary.get("rising_missed_avg_down_ge2_count") or 0)
    initial_quality_fail_count = int(feedback_summary.get("initial_quality_fail_count") or 0)
    if feedback_count > 0:
        orders.append(
            {
                "order_id": "order_rising_missed_initial_quality_feedback_loop",
                "title": "rising missed initial quality feedback loop",
                "source_report_type": "rising_missed_scout_workorder",
                "lifecycle_stage": "entry",
                "target_subsystem": "rising_missed_entry_classifier",
                "route": "instrumentation_order",
                "mapped_family": "rising_missed_initial_quality_feedback_loop",
                "threshold_family": "rising_missed_initial_quality_feedback_loop",
                "improvement_type": "source_only_intraday_feedback_workorder",
                "confidence": "same_day_source_only",
                "priority": 1 if initial_quality_fail_count > 0 else 2,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "implementation_status": "implemented",
                "implementation_provenance": {
                    "implementation_type": "rising_missed_avg_down_ge2_intraday_feedback_bridge",
                    "decision_authority": "source_only_intraday_feedback_no_runtime_mutation",
                    "rising_missed_avg_down_ge2_count": feedback_count,
                    "initial_quality_fail_count": initial_quality_fail_count,
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "root_cause_closure_status_hint": "implementation_done",
                },
                "expected_ev_effect": (
                    "Feed same-day rising-missed entries that required at least two average-down attempts back "
                    "into the rising-missed classifier as initial-quality fail/review labels before expansion."
                ),
                "evidence": [
                    f"rising_missed_avg_down_ge2_count={feedback_count}",
                    f"initial_quality_fail_count={initial_quality_fail_count}",
                    "feedback_label_counts="
                    + _counter_text(feedback_summary.get("feedback_label_counts") or [], key_name="feedback_label"),
                    "runtime_effect=false",
                ],
                "source_paths": list(source_paths.values()),
                "files_likely_touched": [
                    "src/engine/monitoring/rising_missed_intraday_feedback.py",
                    "src/engine/scalping/rising_missed_one_share_entry.py",
                    "src/engine/monitoring/intraday_entry_blocker_diagnostics.py",
                ],
                "acceptance_tests": [
                    "PYTHONPATH=. .venv/bin/pytest src/tests/test_rising_missed_intraday_feedback.py src/tests/test_rising_missed_scout_workorder.py src/tests/test_build_code_improvement_workorder.py",
                    "feedback remains source-only and cannot mutate intraday runtime thresholds, broker/order guards, provider route, bot state, or scale-in quantity/caps",
                ],
                "forbidden_uses": SCALE_IN_FORBIDDEN_USES,
            }
        )
    if winners:
        orders.append(
            {
                "order_id": "order_rising_missed_scout_post_sell_bridge",
                "title": "rising missed scout post-sell bridge for normal-entry recheck",
                "source_report_type": "rising_missed_scout_workorder",
                "lifecycle_stage": "entry",
                "target_subsystem": "entry_freshness",
                "route": "instrumentation_order",
                "mapped_family": "rising_missed_scout_post_sell_bridge",
                "threshold_family": "rising_missed_scout_post_sell_bridge",
                "improvement_type": "source_only_operational_workorder",
                "confidence": "same_day_source_only",
                "priority": 2,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "implementation_status": "implemented",
                "implementation_provenance": {
                    "implementation_type": "forced_scout_post_sell_source_bridge",
                    "decision_authority": "source_only_operational_workorder",
                    "joined_post_sell_winner_count": len(winners),
                    "joined_post_sell_loser_count": len(losers),
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "root_cause_closure_status_hint": "implementation_done",
                },
                "expected_ev_effect": (
                    "Use forced-scout post-sell MFE/profit and holding-quality evidence to request a bounded "
                    "normal-entry recheck workorder; do not count forced scouts as normal BUY success."
                ),
                "evidence": [
                    f"winner_count={len(winners)}",
                    f"loser_count={len(losers)}",
                    f"winner_avg_profit_rate={_profit_summary(winners).get('avg_profit_rate')}",
                    f"current_missed_count={current_missed.get('count')}",
                    f"current_missed_eligible_count={current_missed.get('eligible_count')}",
                    "all_winner_rows_had_latency_pass="
                    + str(all((row.get("latency_pass_count") or 0) > 0 for row in winners)),
                    "all_winner_rows_had_order_bundle_submitted="
                    + str(all((row.get("order_bundle_submitted_count") or 0) > 0 for row in winners)),
                ],
                "source_paths": list(source_paths.values()),
                "files_likely_touched": [
                    "src/engine/monitoring/rising_missed_scout_workorder.py",
                    "src/engine/build_code_improvement_workorder.py",
                    "src/engine/sniper_state_handlers.py",
                ],
                "acceptance_tests": [
                    "PYTHONPATH=. .venv/bin/pytest src/tests/test_rising_missed_scout_workorder.py src/tests/test_build_code_improvement_workorder.py",
                    "forced scout remains excluded from normal BUY/submit/fill success counts",
                    "runtime_effect remains false until a separate approved runtime family exists",
                ],
                "forbidden_uses": FORBIDDEN_USES,
            }
        )
    if (scale_in_bottleneck.get("price_guard_block_record_count") or 0) > 0:
        orders.append(
            {
                "order_id": "order_rising_missed_scout_scale_in_price_guard_split",
                "title": "rising missed scout profitable scale-in price guard split",
                "source_report_type": "rising_missed_scout_workorder",
                "lifecycle_stage": "scale_in",
                "target_subsystem": "scale_in_price_guard",
                "route": "instrumentation_order",
                "mapped_family": "rising_missed_scout_scale_in_price_guard_split",
                "threshold_family": "rising_missed_scout_scale_in_price_guard_split",
                "improvement_type": "source_only_scale_in_bottleneck_workorder",
                "confidence": "same_day_source_only",
                "priority": 2,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "implementation_status": "implemented",
                "implementation_provenance": {
                    "implementation_type": "forced_scout_scale_in_price_guard_source_split",
                    "decision_authority": "source_only_scale_in_bottleneck_analysis",
                    "price_guard_block_record_count": scale_in_bottleneck.get(
                        "price_guard_block_record_count"
                    ),
                    "pyramid_ok_record_count": scale_in_bottleneck.get("pyramid_ok_record_count"),
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "root_cause_closure_status_hint": "implementation_done",
                },
                "expected_ev_effect": (
                    "Split profitable forced-scout PYRAMID candidates that reached scale-in price guard into "
                    "micro-vwap and quote-stale repair buckets before any scale-in guard or quantity change."
                ),
                "evidence": [
                    f"profitable_forced_scout_count={len(winners)}",
                    "record_with_scale_in_event_count="
                    + str(scale_in_bottleneck.get("record_with_scale_in_event_count")),
                    "pyramid_ok_record_count=" + str(scale_in_bottleneck.get("pyramid_ok_record_count")),
                    "price_guard_block_record_count="
                    + str(scale_in_bottleneck.get("price_guard_block_record_count")),
                    "scale_in_executed_record_count="
                    + str(scale_in_bottleneck.get("scale_in_executed_record_count")),
                    "price_guard_reason_counts="
                    + _counter_text(scale_in_bottleneck.get("price_guard_reason_counts") or []),
                    "pyramid_reason_counts="
                    + _counter_text(scale_in_bottleneck.get("pyramid_reason_counts") or []),
                ],
                "source_paths": list(source_paths.values()),
                "files_likely_touched": [
                    "src/engine/monitoring/rising_missed_scout_workorder.py",
                    "src/engine/sniper_state_handlers.py",
                ],
                "acceptance_tests": [
                    "PYTHONPATH=. .venv/bin/pytest src/tests/test_rising_missed_scout_workorder.py src/tests/test_build_code_improvement_workorder.py",
                    "price guard split remains source-only and does not bypass stale quote, broker, or order guards",
                ],
                "forbidden_uses": SCALE_IN_FORBIDDEN_USES,
            }
        )
    if (scale_in_bottleneck.get("qty_block_record_count") or 0) > 0:
        orders.append(
            {
                "order_id": "order_rising_missed_scout_scale_in_qty_evidence_split",
                "title": "rising missed scout scale-in quantity and evidence blocker split",
                "source_report_type": "rising_missed_scout_workorder",
                "lifecycle_stage": "scale_in",
                "target_subsystem": "scale_in_quantity_and_evidence",
                "route": "instrumentation_order",
                "mapped_family": "rising_missed_scout_scale_in_qty_evidence_split",
                "threshold_family": "rising_missed_scout_scale_in_qty_evidence_split",
                "improvement_type": "source_only_scale_in_bottleneck_workorder",
                "confidence": "same_day_source_only",
                "priority": 2,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "implementation_status": "implemented",
                "implementation_provenance": {
                    "implementation_type": "forced_scout_scale_in_qty_evidence_source_split",
                    "decision_authority": "source_only_scale_in_bottleneck_analysis",
                    "qty_block_record_count": scale_in_bottleneck.get("qty_block_record_count"),
                    "scale_in_executed_record_count": scale_in_bottleneck.get(
                        "scale_in_executed_record_count"
                    ),
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "root_cause_closure_status_hint": "implementation_done",
                },
                "expected_ev_effect": (
                    "Separate exposure-cap blocks from pyramid evidence-insufficient blocks for profitable "
                    "forced-scout scale-in candidates; no position cap release or real scale-in approval."
                ),
                "evidence": [
                    f"profitable_forced_scout_count={len(winners)}",
                    "qty_block_record_count=" + str(scale_in_bottleneck.get("qty_block_record_count")),
                    "scale_in_executed_record_count="
                    + str(scale_in_bottleneck.get("scale_in_executed_record_count")),
                    "qty_block_reason_counts="
                    + _counter_text(scale_in_bottleneck.get("qty_block_reason_counts") or []),
                    "price_guard_block_record_count="
                    + str(scale_in_bottleneck.get("price_guard_block_record_count")),
                ],
                "source_paths": list(source_paths.values()),
                "files_likely_touched": [
                    "src/engine/monitoring/rising_missed_scout_workorder.py",
                    "src/engine/sniper_state_handlers.py",
                ],
                "acceptance_tests": [
                    "PYTHONPATH=. .venv/bin/pytest src/tests/test_rising_missed_scout_workorder.py src/tests/test_build_code_improvement_workorder.py",
                    "qty/evidence split remains source-only and does not release position cap or quantity guard",
                ],
                "forbidden_uses": SCALE_IN_FORBIDDEN_USES,
            }
        )
    if losers:
        orders.append(
            {
                "order_id": "order_rising_missed_scout_loss_filter",
                "title": "rising missed scout loss filter before any expansion",
                "source_report_type": "rising_missed_scout_workorder",
                "lifecycle_stage": "entry",
                "target_subsystem": "entry_risk_filter",
                "route": "instrumentation_order",
                "mapped_family": "rising_missed_scout_loss_filter",
                "threshold_family": "rising_missed_scout_loss_filter",
                "improvement_type": "source_only_operational_workorder",
                "confidence": "same_day_source_only",
                "priority": 2,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "implementation_status": "implemented",
                "implementation_provenance": {
                    "implementation_type": "forced_scout_loss_filter_source_split",
                    "decision_authority": "source_only_operational_workorder",
                    "joined_post_sell_loser_count": len(losers),
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "root_cause_closure_status_hint": "implementation_done",
                },
                "expected_ev_effect": (
                    "Separate profitable forced-scout examples from stop/soft-stop losers before any normal-entry "
                    "or scout-expansion proposal."
                ),
                "evidence": [
                    f"loser_count={len(losers)}",
                    f"loser_avg_profit_rate={_profit_summary(losers).get('avg_profit_rate')}",
                    "losers_also_had_latency_pass="
                    + str(all((row.get("latency_pass_count") or 0) > 0 for row in losers)),
                    "losers_also_had_order_bundle_submitted="
                    + str(all((row.get("order_bundle_submitted_count") or 0) > 0 for row in losers)),
                ],
                "source_paths": list(source_paths.values()),
                "files_likely_touched": [
                    "src/engine/monitoring/rising_missed_scout_workorder.py",
                    "src/engine/build_code_improvement_workorder.py",
                ],
                "acceptance_tests": [
                    "PYTHONPATH=. .venv/bin/pytest src/tests/test_rising_missed_scout_workorder.py src/tests/test_build_code_improvement_workorder.py",
                    "loss filter is source-only and does not relax stops or broker/order guards",
                ],
                "forbidden_uses": FORBIDDEN_USES,
            }
        )
    return orders


def build_report(
    target_date: str,
    *,
    pipeline_path: Path | None = None,
    post_sell_path: Path | None = None,
    diagnostic_path: Path | None = None,
    intraday_feedback_path: Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    pipeline_path = pipeline_path or _default_pipeline_path(target_date)
    post_sell_path = post_sell_path or _default_post_sell_path(target_date)
    diagnostic_path = diagnostic_path or _default_diagnostic_path(target_date)
    intraday_feedback_path = intraday_feedback_path or _default_intraday_feedback_path(target_date)
    generated_at = generated_at or datetime.now(KST).isoformat(timespec="seconds")

    post_sell_rows = _load_jsonl(post_sell_path)
    diagnostic = _load_json(diagnostic_path)
    intraday_feedback = _load_json(intraday_feedback_path)
    forced = _index_forced_scouts(_iter_jsonl(pipeline_path))
    preliminary_outcomes = _joined_scout_outcomes(
        forced=forced,
        stage_counts={},
        post_sell_rows=post_sell_rows,
    )
    preliminary_winners = [
        row for row in preliminary_outcomes if (row.get("profit_rate") is not None and row["profit_rate"] > 0)
    ]
    stage_counts, scale_in_bottleneck = _pipeline_stage_counts_and_scale_in_summary(
        pipeline_path,
        forced_record_ids=set(forced),
        winners=preliminary_winners,
    )
    outcomes = _joined_scout_outcomes(forced=forced, stage_counts=stage_counts, post_sell_rows=post_sell_rows)
    winners = [row for row in outcomes if (row.get("profit_rate") is not None and row["profit_rate"] > 0)]
    losers = [row for row in outcomes if (row.get("profit_rate") is not None and row["profit_rate"] <= 0)]
    current_missed = _current_missed_summary(diagnostic)
    source_paths = {
        "pipeline_events": str(pipeline_path),
        "post_sell_candidates": str(post_sell_path),
        "intraday_entry_blocker_diagnostics": str(diagnostic_path),
        "rising_missed_intraday_feedback": str(intraday_feedback_path),
    }
    code_improvement_orders = _build_operational_workorders(
        winners=winners,
        losers=losers,
        current_missed=current_missed,
        scale_in_bottleneck=scale_in_bottleneck,
        intraday_feedback=intraday_feedback,
        source_paths=source_paths,
    )
    intraday_feedback_summary = (
        intraday_feedback.get("summary")
        if isinstance(intraday_feedback.get("summary"), dict)
        else {}
    )
    return {
        "schema_version": 1,
        "report_type": "rising_missed_scout_workorder",
        "target_date": target_date,
        "generated_at": generated_at,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "decision_authority": "source_only_operational_workorder",
        "forbidden_uses": FORBIDDEN_USES,
        "metric_contracts": {
            "scale_in_bottleneck_summary": {
                "metric_role": "source_quality_gate",
                "decision_authority": "source_only_scale_in_bottleneck_analysis",
                "window_policy": "same_day_profitable_forced_scout_post_sell_join",
                "sample_floor": "1_profitable_forced_scout_with_scale_in_event",
                "primary_decision_metric": False,
                "source_quality_gate": "record_id_joined_forced_scout_post_sell_and_holding_scale_in_events",
                "forbidden_uses": SCALE_IN_FORBIDDEN_USES,
            }
        },
        "source_paths": source_paths,
        "summary": {
            "forced_scout_record_count": len(forced),
            "forced_scout_with_post_sell_count": len(outcomes),
            "profitable_forced_scout_count": len(winners),
            "loss_or_flat_forced_scout_count": len(losers),
            "winner_profit": _profit_summary(winners),
            "loser_profit": _profit_summary(losers),
            "winner_source_signature_counts": _signature_counts(winners),
            "loser_source_signature_counts": _signature_counts(losers),
            "current_missed_count": current_missed.get("count"),
            "current_missed_class_counts": current_missed.get("class_counts"),
            "scale_in_price_guard_block_record_count": scale_in_bottleneck.get(
                "price_guard_block_record_count"
            ),
            "scale_in_qty_block_record_count": scale_in_bottleneck.get("qty_block_record_count"),
            "scale_in_executed_record_count": scale_in_bottleneck.get("scale_in_executed_record_count"),
            "intraday_feedback_avg_down_ge2_count": intraday_feedback_summary.get(
                "rising_missed_avg_down_ge2_count", 0
            ),
            "intraday_feedback_initial_quality_fail_count": intraday_feedback_summary.get(
                "initial_quality_fail_count", 0
            ),
            "code_improvement_order_count": len(code_improvement_orders),
        },
        "profitable_forced_scout_examples": winners[:20],
        "loss_or_flat_forced_scout_examples": losers[:20],
        "current_missed_summary": current_missed,
        "intraday_feedback_summary": intraday_feedback_summary,
        "scale_in_bottleneck_summary": scale_in_bottleneck,
        "code_improvement_orders": code_improvement_orders,
    }


def write_outputs(report: dict[str, Any], *, output_json: Path, output_md: Path) -> None:
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    lines = [
        f"# {report.get('target_date')} Rising Missed Scout Workorder",
        "",
        f"- generated_at: {report.get('generated_at')}",
        "- decision_authority: source_only_operational_workorder",
        "- runtime_effect: false",
        "- allowed_runtime_apply: false",
        "- forbidden_uses: " + ", ".join(FORBIDDEN_USES),
        "",
        "## Summary",
        "",
        f"- forced_scout_record_count: {summary.get('forced_scout_record_count')}",
        f"- forced_scout_with_post_sell_count: {summary.get('forced_scout_with_post_sell_count')}",
        f"- profitable_forced_scout_count: {summary.get('profitable_forced_scout_count')}",
        f"- loss_or_flat_forced_scout_count: {summary.get('loss_or_flat_forced_scout_count')}",
        f"- winner_avg_profit_rate: {(summary.get('winner_profit') or {}).get('avg_profit_rate')}",
        f"- loser_avg_profit_rate: {(summary.get('loser_profit') or {}).get('avg_profit_rate')}",
        f"- current_missed_count: {summary.get('current_missed_count')}",
        f"- scale_in_price_guard_block_record_count: {summary.get('scale_in_price_guard_block_record_count')}",
        f"- scale_in_qty_block_record_count: {summary.get('scale_in_qty_block_record_count')}",
        f"- scale_in_executed_record_count: {summary.get('scale_in_executed_record_count')}",
        f"- code_improvement_order_count: {summary.get('code_improvement_order_count')}",
        "",
        "## Workorders",
        "",
    ]
    for order in report.get("code_improvement_orders") or []:
        lines.extend(
            [
                f"### {order.get('order_id')}",
                "",
                f"- title: {order.get('title')}",
                f"- mapped_family: {order.get('mapped_family')}",
                f"- runtime_effect: {str(order.get('runtime_effect')).lower()}",
                f"- allowed_runtime_apply: {str(order.get('allowed_runtime_apply')).lower()}",
                "- evidence:",
            ]
        )
        for item in order.get("evidence") or []:
            lines.append(f"  - {item}")
        lines.append("")
    output_md.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build rising missed scout operational workorders.")
    parser.add_argument("--target-date", default=datetime.now(KST).strftime("%Y-%m-%d"))
    parser.add_argument("--pipeline-path", type=Path)
    parser.add_argument("--post-sell-path", type=Path)
    parser.add_argument("--diagnostic-path", type=Path)
    parser.add_argument("--intraday-feedback-path", type=Path)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--generated-at")
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args(argv)
    report = build_report(
        args.target_date,
        pipeline_path=args.pipeline_path,
        post_sell_path=args.post_sell_path,
        diagnostic_path=args.diagnostic_path,
        intraday_feedback_path=args.intraday_feedback_path,
        generated_at=args.generated_at,
    )
    default_json, default_md = _default_output_paths(args.target_date)
    output_json = args.output_json or default_json
    output_md = args.output_md or default_md
    write_outputs(report, output_json=output_json, output_md=output_md)
    if args.print_summary:
        print(json.dumps({"output_json": str(output_json), "output_md": str(output_md), **report["summary"]}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
