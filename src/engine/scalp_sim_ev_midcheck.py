"""Build an intraday EV snapshot for the scalp live simulator."""

from __future__ import annotations

import argparse
import json
import math
import statistics
from collections import Counter
from datetime import datetime
from pathlib import Path

from src.utils.constants import DATA_DIR
from src.utils.jsonl_io import read_jsonl

SYNTHETIC_NAMES = {"TEST", "DUMMY", "MOCK"}


def _as_float(value, default=None):
    try:
        if value is None:
            return default
        numeric = float(str(value).replace("%", "").replace("+", "").strip())
        return numeric if math.isfinite(numeric) else default
    except (TypeError, ValueError):
        return default


def _load_jsonl(path: Path) -> list[dict]:
    return read_jsonl(path, errors="ignore")


def _is_synthetic_event(row: dict) -> bool:
    name = str(row.get("stock_name") or "").strip().upper()
    code = str(row.get("stock_code") or "").strip()[:6]
    return name in SYNTHETIC_NAMES or code == "123456"


def _percentile(values: list[float], pct: float):
    if not values:
        return None
    ordered = sorted(values)
    k = (len(ordered) - 1) * pct / 100
    lo = math.floor(k)
    hi = math.ceil(k)
    if lo == hi:
        return ordered[int(k)]
    return ordered[lo] * (hi - k) + ordered[hi] * (k - lo)


def _metrics(values: list[float]) -> dict:
    if not values:
        return {
            "sample": 0,
            "sum_profit_pct": 0.0,
            "avg_profit_pct": None,
            "median_profit_pct": None,
            "win_rate_pct": None,
            "loss_rate_pct": None,
            "gross_win_pct": 0.0,
            "gross_loss_pct": 0.0,
            "min_profit_pct": None,
            "max_profit_pct": None,
            "p25_profit_pct": None,
            "p75_profit_pct": None,
            "p90_profit_pct": None,
        }
    return {
        "sample": len(values),
        "sum_profit_pct": round(sum(values), 4),
        "avg_profit_pct": round(statistics.mean(values), 4),
        "median_profit_pct": round(statistics.median(values), 4),
        "win_rate_pct": round(100 * sum(v > 0 for v in values) / len(values), 2),
        "loss_rate_pct": round(100 * sum(v < 0 for v in values) / len(values), 2),
        "gross_win_pct": round(sum(v for v in values if v > 0), 4),
        "gross_loss_pct": round(sum(v for v in values if v < 0), 4),
        "min_profit_pct": round(min(values), 4),
        "max_profit_pct": round(max(values), 4),
        "p25_profit_pct": round(_percentile(values, 25), 4),
        "p75_profit_pct": round(_percentile(values, 75), 4),
        "p90_profit_pct": round(_percentile(values, 90), 4),
    }


def _sim_record_id(row: dict) -> str | None:
    fields = row.get("fields") or {}
    value = fields.get("sim_record_id")
    if value:
        return str(value)
    return None


def _boolish_false(value) -> bool:
    return str(value).strip().lower() in {"false", "0", "no", "none", ""}


def _position_template(row: dict) -> dict:
    fields = row.get("fields") or {}
    return {
        "sim_record_id": fields.get("sim_record_id"),
        "sim_parent_record_id": fields.get("sim_parent_record_id"),
        "stock_name": row.get("stock_name"),
        "stock_code": row.get("stock_code"),
        "events": [],
        "scale_in_filled": [],
        "scale_in_unfilled": [],
        "entry": None,
        "entry_fill": None,
        "completed": None,
        "actual_order_submitted_values": [],
    }


def _position_arm(position: dict) -> str:
    add_types = {
        str(event.get("add_type") or "").upper()
        for event in position.get("scale_in_filled", [])
    }
    has_avg_down = bool(add_types & {"AVG_DOWN", "REVERSAL_ADD"})
    has_pyramid = "PYRAMID" in add_types
    if has_avg_down and has_pyramid:
        return "mixed_scale_in"
    if has_avg_down:
        return "avg_down"
    if has_pyramid:
        return "pyramid"
    return "exit_only"


def _scale_in_event_row(row: dict) -> dict:
    fields = row.get("fields") or {}
    return {
        "emitted_at": row.get("emitted_at"),
        "stock_name": row.get("stock_name"),
        "stock_code": row.get("stock_code"),
        "sim_record_id": fields.get("sim_record_id"),
        "add_type": fields.get("add_type"),
        "qty": _as_float(fields.get("qty")),
        "template_qty": _as_float(fields.get("template_qty")),
        "would_qty": _as_float(fields.get("would_qty")),
        "effective_qty": _as_float(fields.get("effective_qty")),
        "cap_qty": _as_float(fields.get("cap_qty")),
        "qty_reason": fields.get("qty_reason"),
        "actual_order_submitted": fields.get("actual_order_submitted"),
        "runtime_effect": fields.get("runtime_effect"),
    }


def _post_add_metrics(position: dict) -> dict:
    filled = position.get("scale_in_filled") or []
    if not filled:
        return {
            "sample": 0,
            "mfe_after_add_pct": None,
            "mae_after_add_pct": None,
            "final_exit_profit_pct": None,
            "source": "no_scale_in",
        }
    first_add_at = min(str(event.get("emitted_at") or "") for event in filled)
    samples: list[float] = []
    for event in position.get("events") or []:
        if str(event.get("emitted_at") or "") < first_add_at:
            continue
        fields = event.get("fields") or {}
        for key in ("profit_rate", "trigger_profit_rate"):
            value = _as_float(fields.get(key))
            if value is not None:
                samples.append(value)
    completed = position.get("completed") or {}
    final_profit = _as_float((completed.get("fields") or {}).get("profit_rate"))
    return {
        "sample": len(samples),
        "mfe_after_add_pct": round(max(samples), 4) if samples else None,
        "mae_after_add_pct": round(min(samples), 4) if samples else None,
        "final_exit_profit_pct": final_profit,
        "source": (
            "sim_record_profit_fields" if samples else "no_post_add_profit_fields"
        ),
    }


def _build_scale_in_analysis(positions: dict[str, dict]) -> dict:
    arm_values: dict[str, list[float]] = {
        "exit_only": [],
        "avg_down": [],
        "pyramid": [],
        "mixed_scale_in": [],
    }
    rows: list[dict] = []
    completed_filled_events: list[dict] = []
    completed_unfilled_events: list[dict] = []
    all_filled_events: list[dict] = []
    all_unfilled_events: list[dict] = []
    actual_order_values: list[str] = []

    for position in positions.values():
        all_filled_events.extend(position.get("scale_in_filled") or [])
        all_unfilled_events.extend(position.get("scale_in_unfilled") or [])
        actual_order_values.extend(
            str(v) for v in position.get("actual_order_submitted_values") or []
        )
        completed = position.get("completed")
        if not completed:
            continue
        fields = completed.get("fields") or {}
        profit = _as_float(fields.get("profit_rate"))
        arm = _position_arm(position)
        if profit is not None:
            arm_values.setdefault(arm, []).append(profit)
        completed_filled_events.extend(position.get("scale_in_filled") or [])
        completed_unfilled_events.extend(position.get("scale_in_unfilled") or [])
        post_add = _post_add_metrics(position)
        rows.append(
            {
                "sim_record_id": position.get("sim_record_id"),
                "stock_name": position.get("stock_name"),
                "stock_code": position.get("stock_code"),
                "arm": arm,
                "scale_in_filled_count": len(position.get("scale_in_filled") or []),
                "scale_in_unfilled_count": len(position.get("scale_in_unfilled") or []),
                "add_types": sorted(
                    {
                        str(event.get("add_type") or "-")
                        for event in position.get("scale_in_filled", [])
                    }
                ),
                "final_exit_profit_pct": profit,
                "exit_rule": fields.get("exit_rule"),
                "actual_order_submitted": fields.get("actual_order_submitted"),
                **post_add,
            }
        )

    by_add_type: Counter[str] = Counter()
    for event in all_filled_events:
        by_add_type[str(event.get("add_type") or "-")] += 1
    unfilled_by_add_type: Counter[str] = Counter()
    for event in all_unfilled_events:
        unfilled_by_add_type[str(event.get("add_type") or "-")] += 1

    unexpected_actual = sorted(
        {value for value in actual_order_values if not _boolish_false(value)}
    )
    return {
        "arm_metrics": {
            arm: _metrics(values) for arm, values in sorted(arm_values.items())
        },
        "scale_in_counts": {
            "positions_completed": len(rows),
            "positions_with_scale_in": sum(
                1 for row in rows if row["scale_in_filled_count"] > 0
            ),
            "positions_without_scale_in": sum(
                1 for row in rows if row["scale_in_filled_count"] == 0
            ),
            "filled_events": len(all_filled_events),
            "unfilled_events": len(all_unfilled_events),
            "completed_filled_events": len(completed_filled_events),
            "completed_unfilled_events": len(completed_unfilled_events),
            "filled_by_add_type": dict(sorted(by_add_type.items())),
            "unfilled_by_add_type": dict(sorted(unfilled_by_add_type.items())),
        },
        "actual_order_submission_check": {
            "passed": not unexpected_actual,
            "unexpected_values": unexpected_actual,
            "checked_values": len(actual_order_values),
        },
        "positions": sorted(
            rows,
            key=lambda row: (
                row["final_exit_profit_pct"]
                if row["final_exit_profit_pct"] is not None
                else -999
            ),
            reverse=True,
        ),
        "filled_events": all_filled_events,
        "unfilled_events": all_unfilled_events,
    }


def _as_int(value, default=0) -> int:
    numeric = _as_float(value)
    if numeric is None:
        return default
    return int(numeric)


def _build_initial_qty_provenance(positions: dict[str, dict]) -> dict:
    rows: list[dict] = []
    summary = {
        "sample": 0,
        "qty_sum": 0,
        "uncapped_qty_sum": 0,
        "cap_applied_count": 0,
        "uncapped_qty_source_count": 0,
        "virtual_budget_qty_source_count": 0,
        "fixed_qty_source_count": 0,
    }
    for position in positions.values():
        completed = position.get("completed")
        if not completed:
            continue
        completed_fields = completed.get("fields") or {}
        entry = position.get("entry") or {}
        entry_fields = entry.get("fields") or {}
        entry_fill = position.get("entry_fill") or {}
        entry_fill_fields = entry_fill.get("fields") or {}
        profit_rate = _as_float(completed_fields.get("profit_rate"))
        buy_price = _as_float(
            completed_fields.get("buy_price")
            or entry_fill_fields.get("assumed_fill_price")
        )

        sim_qty = _as_int(
            entry_fields.get("qty")
            or entry_fill_fields.get("qty")
            or completed_fields.get("qty"),
            1,
        )
        uncapped_qty = _as_int(
            entry_fields.get("uncapped_qty") or entry_fields.get("qty") or sim_qty,
            sim_qty,
        )
        qty_source = str(entry_fields.get("qty_source") or "-")
        cap_applied = not _boolish_false(entry_fields.get("cap_applied"))
        row = {
            "sim_record_id": position.get("sim_record_id"),
            "stock_name": position.get("stock_name"),
            "stock_code": position.get("stock_code"),
            "profit_rate": profit_rate,
            "buy_price": buy_price,
            "sim_qty": sim_qty,
            "uncapped_qty": uncapped_qty,
            "cap_applied": cap_applied,
            "qty_source": qty_source,
            "qty_reason": entry_fields.get("qty_reason") or "-",
        }
        rows.append(row)
        summary["sample"] += 1
        summary["qty_sum"] += sim_qty
        summary["uncapped_qty_sum"] += uncapped_qty
        summary["cap_applied_count"] += int(cap_applied)
        summary["uncapped_qty_source_count"] += int(
            qty_source == "uncapped_buy_capacity"
        )
        summary["virtual_budget_qty_source_count"] += int(
            qty_source
            in {
                "sim_virtual_budget_dynamic_formula",
                "scalping_position_sizing_allocator",
            }
        )
        summary["fixed_qty_source_count"] += int(qty_source == "fixed_config")

    return {
        "summary": summary,
        "positions": sorted(
            rows,
            key=lambda row: (
                row["profit_rate"] if row["profit_rate"] is not None else -999
            ),
            reverse=True,
        ),
        "method": "actual_sim_qty_provenance_only",
    }


def _ratio_pct(numerator: int, denominator: int):
    if denominator <= 0:
        return None
    return round(100.0 * numerator / denominator, 2)


def build_report(target_date: str) -> dict:
    path = DATA_DIR / "pipeline_events" / f"pipeline_events_{target_date}.jsonl"
    rows = _load_jsonl(path)
    sim_counts: Counter[str] = Counter()
    sim_ai_critical_class_counts: Counter[str] = Counter()
    sim_ai_critical_reason_counts: Counter[str] = Counter()
    completed: list[dict] = []
    expired: list[dict] = []
    real_completed: list[dict] = []
    positions: dict[str, dict] = {}
    latest = None
    synthetic_excluded = 0

    for row in rows:
        latest = row.get("emitted_at") or latest
        stage = str(row.get("stage") or "")
        fields = row.get("fields") or {}
        is_sim = (
            stage.startswith("scalp_sim_")
            or fields.get("simulation_book") == "scalp_ai_buy_all"
        )
        if is_sim and _is_synthetic_event(row):
            synthetic_excluded += 1
            continue
        if is_sim:
            sim_counts[stage] += 1
            if stage in {
                "scalp_sim_ai_holding_live_call",
                "scalp_sim_ai_holding_reuse",
                "scalp_sim_ai_holding_deferred",
            }:
                critical_class = str(fields.get("critical_class") or "unknown")
                sim_ai_critical_class_counts[critical_class] += 1
                for reason in str(fields.get("critical_reason") or "unknown").split(
                    ","
                ):
                    cleaned = reason.strip() or "unknown"
                    sim_ai_critical_reason_counts[cleaned] += 1
            sim_id = _sim_record_id(row)
            if sim_id:
                position = positions.setdefault(sim_id, _position_template(row))
                position["events"].append(row)
                position["stock_name"] = position.get("stock_name") or row.get(
                    "stock_name"
                )
                position["stock_code"] = position.get("stock_code") or row.get(
                    "stock_code"
                )
                actual_order_submitted = fields.get("actual_order_submitted")
                if actual_order_submitted is not None:
                    position["actual_order_submitted_values"].append(
                        actual_order_submitted
                    )
                if stage == "scalp_sim_scale_in_order_assumed_filled":
                    position["scale_in_filled"].append(_scale_in_event_row(row))
                if stage == "scalp_sim_scale_in_order_unfilled":
                    position["scale_in_unfilled"].append(_scale_in_event_row(row))
                if stage == "scalp_sim_entry_armed":
                    position["entry"] = row
                if stage == "scalp_sim_buy_order_assumed_filled":
                    position["entry_fill"] = row
                if stage == "scalp_sim_sell_order_assumed_filled":
                    position["completed"] = row
        if stage == "scalp_sim_sell_order_assumed_filled" and is_sim:
            completed.append(
                {
                    "emitted_at": row.get("emitted_at"),
                    "stock_name": row.get("stock_name"),
                    "stock_code": row.get("stock_code"),
                    "profit_rate": _as_float(fields.get("profit_rate")),
                    "buy_price": _as_float(fields.get("buy_price")),
                    "assumed_fill_price": _as_float(fields.get("assumed_fill_price")),
                    "sell_reason_type": fields.get("sell_reason_type"),
                    "exit_rule": fields.get("exit_rule"),
                    "exit_decision_source": fields.get("exit_decision_source"),
                    "simulation_fill_policy": fields.get("simulation_fill_policy"),
                    "sim_parent_record_id": fields.get("sim_parent_record_id"),
                }
            )
        if stage == "scalp_sim_entry_expired" and is_sim:
            expired.append(
                {
                    "emitted_at": row.get("emitted_at"),
                    "stock_name": row.get("stock_name"),
                    "stock_code": row.get("stock_code"),
                    "limit_price": fields.get("limit_price"),
                    "sim_parent_record_id": fields.get("sim_parent_record_id"),
                }
            )
        if stage == "sell_completed" and not _is_synthetic_event(row):
            real_completed.append(
                {
                    "emitted_at": row.get("emitted_at"),
                    "stock_name": row.get("stock_name"),
                    "stock_code": row.get("stock_code"),
                    "profit_rate": _as_float(fields.get("profit_rate")),
                    "exit_rule": fields.get("exit_rule"),
                }
            )

    profit_values = [
        row["profit_rate"] for row in completed if row["profit_rate"] is not None
    ]
    scale_in_analysis = _build_scale_in_analysis(positions)
    initial_qty_provenance = _build_initial_qty_provenance(positions)
    ai_live_calls = int(sim_counts.get("scalp_sim_ai_holding_live_call", 0))
    ai_reuse = int(sim_counts.get("scalp_sim_ai_holding_reuse", 0))
    ai_deferred = int(sim_counts.get("scalp_sim_ai_holding_deferred", 0))
    ai_critical_bypass = int(sim_counts.get("sim_ai_critical_bypass", 0))
    overnight_decisions = int(sim_counts.get("scalp_sim_overnight_decision", 0))
    overnight_sell_today = int(sim_counts.get("scalp_sim_overnight_sell_today", 0))
    overnight_hold = int(sim_counts.get("scalp_sim_overnight_hold", 0))
    overnight_sell_filled = sum(
        1
        for row in completed
        if str(row.get("exit_rule") or "") == "scalp_sim_overnight_sell_today"
    )
    return {
        "target_date": target_date,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_path": str(path),
        "latest_event_at": latest,
        "synthetic_excluded": synthetic_excluded,
        "sim_counts": dict(sorted(sim_counts.items())),
        "sim_ai_budget_counts": {
            "scalp_sim_ai_holding_live_call": ai_live_calls,
            "scalp_sim_ai_holding_reuse": ai_reuse,
            "scalp_sim_ai_holding_deferred": ai_deferred,
            "sim_ai_budget_exhausted": int(
                sim_counts.get("sim_ai_budget_exhausted", 0)
            ),
            "sim_ai_critical_bypass": ai_critical_bypass,
            "critical_class_counts": dict(sorted(sim_ai_critical_class_counts.items())),
            "critical_reason_counts": dict(
                sorted(sim_ai_critical_reason_counts.items())
            ),
            "critical_bypass_ratio_pct": _ratio_pct(ai_critical_bypass, ai_live_calls),
            "deferred_ratio_pct": _ratio_pct(ai_deferred, ai_live_calls + ai_deferred),
            "reuse_ratio_pct": _ratio_pct(
                ai_reuse, ai_live_calls + ai_reuse + ai_deferred
            ),
        },
        "overnight_counts": {
            "decision": overnight_decisions,
            "sell_today": overnight_sell_today,
            "hold_overnight": overnight_hold,
            "sell_assumed_filled": overnight_sell_filled,
            "carry_open_count": overnight_hold,
            "runtime_effect": False,
            "decision_authority": "sim_observation_only",
        },
        "metrics": _metrics(profit_values),
        "scale_in_analysis": scale_in_analysis,
        "initial_qty_provenance": initial_qty_provenance,
        "completed": sorted(
            completed,
            key=lambda row: (
                row["profit_rate"] if row["profit_rate"] is not None else -999
            ),
            reverse=True,
        ),
        "expired": expired,
        "real_completed": real_completed,
        "judgement": (
            "positive_ev_midcheck"
            if profit_values and statistics.mean(profit_values) > 0
            else "non_positive_or_no_sample"
        ),
        "runtime_mutation": False,
    }


def _fmt_pct(value) -> str:
    if value is None:
        return "-"
    return f"{float(value):+.2f}%"


def write_outputs(report: dict, output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    target_date = report["target_date"]
    json_path = output_dir / f"scalp_sim_ev_midcheck_{target_date}.json"
    md_path = output_dir / f"scalp_sim_ev_midcheck_{target_date}.md"
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    m = report["metrics"]
    lines = [
        f"# Scalp Sim EV Midcheck {target_date}",
        "",
        f"- generated_at: `{report['generated_at']}`",
        f"- latest_event_at: `{report.get('latest_event_at') or '-'}`",
        f"- source: `{report['source_path']}`",
        f"- judgement: `{report['judgement']}`",
        f"- runtime_mutation: `{str(report['runtime_mutation']).lower()}`",
        f"- synthetic_excluded: `{report['synthetic_excluded']}`",
        "",
        "## Summary",
        "",
        f"- completed: `{m['sample']}`",
        f"- sum_profit_pct: `{_fmt_pct(m['sum_profit_pct'])}`",
        f"- avg_profit_pct: `{_fmt_pct(m['avg_profit_pct'])}`",
        f"- median_profit_pct: `{_fmt_pct(m['median_profit_pct'])}`",
        f"- win_rate_pct: `{m['win_rate_pct'] if m['win_rate_pct'] is not None else '-'}%`",
        f"- gross_win_pct: `{_fmt_pct(m['gross_win_pct'])}`",
        f"- gross_loss_pct: `{_fmt_pct(m['gross_loss_pct'])}`",
        "",
        "## Sim Stage Counts",
        "",
    ]
    lines.extend(
        [
            f"- ai_live_call: `{(report.get('sim_ai_budget_counts') or {}).get('scalp_sim_ai_holding_live_call', 0)}`",
            f"- ai_reuse: `{(report.get('sim_ai_budget_counts') or {}).get('scalp_sim_ai_holding_reuse', 0)}`",
            f"- ai_deferred: `{(report.get('sim_ai_budget_counts') or {}).get('scalp_sim_ai_holding_deferred', 0)}`",
            f"- ai_budget_exhausted: `{(report.get('sim_ai_budget_counts') or {}).get('sim_ai_budget_exhausted', 0)}`",
            f"- ai_critical_bypass: `{(report.get('sim_ai_budget_counts') or {}).get('sim_ai_critical_bypass', 0)}`",
            f"- ai_critical_bypass_ratio_pct: `{(report.get('sim_ai_budget_counts') or {}).get('critical_bypass_ratio_pct', '-')}`",
            f"- ai_deferred_ratio_pct: `{(report.get('sim_ai_budget_counts') or {}).get('deferred_ratio_pct', '-')}`",
            f"- ai_reuse_ratio_pct: `{(report.get('sim_ai_budget_counts') or {}).get('reuse_ratio_pct', '-')}`",
            "",
        ]
    )
    overnight = report.get("overnight_counts") or {}
    lines.extend(
        [
            "## Overnight",
            "",
            f"- decision: `{overnight.get('decision', 0)}`",
            f"- sell_today: `{overnight.get('sell_today', 0)}`",
            f"- hold_overnight: `{overnight.get('hold_overnight', 0)}`",
            f"- sell_assumed_filled: `{overnight.get('sell_assumed_filled', 0)}`",
            f"- carry_open_count: `{overnight.get('carry_open_count', 0)}`",
            f"- decision_authority: `{overnight.get('decision_authority') or '-'}`",
            f"- runtime_effect: `{str(overnight.get('runtime_effect')).lower()}`",
            "",
        ]
    )
    class_counts = (report.get("sim_ai_budget_counts") or {}).get(
        "critical_class_counts"
    ) or {}
    if class_counts:
        lines.extend(["## AI Budget Critical Classes", ""])
        for label, count in class_counts.items():
            lines.append(f"- `{label}`: `{count}`")
        lines.append("")
    reason_counts = (report.get("sim_ai_budget_counts") or {}).get(
        "critical_reason_counts"
    ) or {}
    if reason_counts:
        lines.extend(["## AI Budget Critical Reasons", ""])
        for label, count in reason_counts.items():
            lines.append(f"- `{label}`: `{count}`")
        lines.append("")
    for stage, count in report["sim_counts"].items():
        lines.append(f"- `{stage}`: `{count}`")
    scale = report.get("scale_in_analysis") or {}
    scale_counts = scale.get("scale_in_counts") or {}
    submission_check = scale.get("actual_order_submission_check") or {}
    lines.extend(
        [
            "",
            "## Arm Split",
            "",
            "| arm | completed | avg | median | win_rate | sum |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for arm, metrics in (scale.get("arm_metrics") or {}).items():
        lines.append(
            f"| `{arm}` | {metrics.get('sample', 0)} | {_fmt_pct(metrics.get('avg_profit_pct'))} | "
            f"{_fmt_pct(metrics.get('median_profit_pct'))} | "
            f"{metrics.get('win_rate_pct') if metrics.get('win_rate_pct') is not None else '-'}% | "
            f"{_fmt_pct(metrics.get('sum_profit_pct'))} |"
        )
    lines.extend(
        [
            "",
            "## Scale-In Summary",
            "",
            f"- positions_completed: `{scale_counts.get('positions_completed', 0)}`",
            f"- positions_with_scale_in: `{scale_counts.get('positions_with_scale_in', 0)}`",
            f"- positions_without_scale_in: `{scale_counts.get('positions_without_scale_in', 0)}`",
            f"- filled_events: `{scale_counts.get('filled_events', 0)}`",
            f"- unfilled_events: `{scale_counts.get('unfilled_events', 0)}`",
            f"- completed_filled_events: `{scale_counts.get('completed_filled_events', 0)}`",
            f"- completed_unfilled_events: `{scale_counts.get('completed_unfilled_events', 0)}`",
            f"- filled_by_add_type: `{scale_counts.get('filled_by_add_type', {})}`",
            f"- unfilled_by_add_type: `{scale_counts.get('unfilled_by_add_type', {})}`",
            f"- actual_order_submitted_false_only: `{str(submission_check.get('passed', False)).lower()}`",
            f"- actual_order_checked_values: `{submission_check.get('checked_values', 0)}`",
            "",
            "## Scale-In Position Outcomes",
            "",
            "| 종목 | arm | add filled/unfilled | post-add MFE | post-add MAE | final exit | actual_order |",
            "| --- | --- | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in scale.get("positions") or []:
        lines.append(
            f"| {row['stock_name']}({row['stock_code']}) | `{row.get('arm')}` | "
            f"{row.get('scale_in_filled_count', 0)}/{row.get('scale_in_unfilled_count', 0)} | "
            f"{_fmt_pct(row.get('mfe_after_add_pct'))} | {_fmt_pct(row.get('mae_after_add_pct'))} | "
            f"{_fmt_pct(row.get('final_exit_profit_pct'))} | {row.get('actual_order_submitted') or '-'} |"
        )
    qty_prov = report.get("initial_qty_provenance") or {}
    qty_summary = qty_prov.get("summary") or {}
    lines.extend(
        [
            "",
            "## Initial Qty Provenance",
            "",
            f"- method: `{qty_prov.get('method', '-')}`",
            f"- sample: `{qty_summary.get('sample', 0)}`",
            f"- qty_sum: `{qty_summary.get('qty_sum', 0)}`",
            f"- uncapped_qty_sum: `{qty_summary.get('uncapped_qty_sum', 0)}`",
            f"- cap_applied_count: `{qty_summary.get('cap_applied_count', 0)}`",
            f"- uncapped_qty_source_count: `{qty_summary.get('uncapped_qty_source_count', 0)}`",
            f"- virtual_budget_qty_source_count: `{qty_summary.get('virtual_budget_qty_source_count', 0)}`",
            f"- fixed_qty_source_count: `{qty_summary.get('fixed_qty_source_count', 0)}`",
            "",
            "| 종목 | sim_qty | uncapped_qty | qty_source | cap_applied | final exit |",
            "| --- | ---: | ---: | --- | --- | ---: |",
        ]
    )
    for row in qty_prov.get("positions") or []:
        lines.append(
            f"| {row['stock_name']}({row['stock_code']}) | {row.get('sim_qty', '-')} | "
            f"{row.get('uncapped_qty', '-')} | `{row.get('qty_source') or '-'}` | "
            f"{str(row.get('cap_applied', False)).lower()} | {_fmt_pct(row.get('profit_rate'))} |"
        )
    lines.extend(
        [
            "",
            "## Completed Rows",
            "",
            "| 종목 | 수익률 | exit_rule | source |",
            "| --- | ---: | --- | --- |",
        ]
    )
    for row in report["completed"]:
        lines.append(
            f"| {row['stock_name']}({row['stock_code']}) | {_fmt_pct(row['profit_rate'])} | "
            f"{row.get('exit_rule') or '-'} | {row.get('exit_decision_source') or '-'} |"
        )
    lines.extend(
        [
            "",
            "## Expired Entries",
            "",
            "| 종목 | limit_price | parent |",
            "| --- | ---: | --- |",
        ]
    )
    for row in report["expired"]:
        lines.append(
            f"| {row['stock_name']}({row['stock_code']}) | {row.get('limit_price') or '-'} | "
            f"{row.get('sim_parent_record_id') or '-'} |"
        )
    lines.extend(
        [
            "",
            "## Real Completed Reference",
            "",
            "| 종목 | 수익률 | exit_rule |",
            "| --- | ---: | --- |",
        ]
    )
    for row in report["real_completed"]:
        lines.append(
            f"| {row['stock_name']}({row['stock_code']}) | {_fmt_pct(row['profit_rate'])} | "
            f"{row.get('exit_rule') or '-'} |"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build scalp simulator intraday EV midcheck report."
    )
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument(
        "--output-dir",
        default=str(DATA_DIR / "report" / "scalp_simulator"),
    )
    args = parser.parse_args(argv)
    report = build_report(args.date)
    json_path, md_path = write_outputs(report, Path(args.output_dir))
    print(
        f"[SCALP_SIM_EV_MIDCHECK] json={json_path} md={md_path} judgement={report['judgement']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
