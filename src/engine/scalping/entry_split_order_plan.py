"""Entry split order plan report and bounded runtime allocator."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Any

from src.engine.automation.source_quality_clean_baseline import clean_baseline_policy, is_date_allowed
from src.trading.order.tick_utils import clamp_price_to_tick
from src.utils.constants import DATA_DIR
from src.utils.jsonl_io import iter_jsonl


SCHEMA_VERSION = "entry_split_order_plan_v1"
POLICY_SCHEMA_VERSION = "entry_split_order_policy_v1"
REPORT_TYPE = "entry_split_order_plan"
RUNTIME_FAMILY = "entry_split_order_plan"
REPORT_DIR = DATA_DIR / "report" / REPORT_TYPE
POLICY_DIR = DATA_DIR / "threshold_cycle" / "entry_split_order_policy"
SAMPLE_FLOOR_REAL = 20
SAMPLE_FLOOR_SIM = 10
ALLOWED_PRICE_CANDIDATES = {
    "resolved_order_price",
    "best_bid",
    "bid-1tick",
    "bid-2tick",
    "reference_target",
    "AI_candidate",
}


def report_paths(target_date: str) -> tuple[Path, Path]:
    base = REPORT_DIR / f"{REPORT_TYPE}_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def policy_path(target_date: str) -> Path:
    return POLICY_DIR / f"entry_split_order_policy_{target_date}.json"


def _pipeline_events_path(target_date: str) -> Path:
    return DATA_DIR / "pipeline_events" / f"pipeline_events_{target_date}.jsonl"


def _threshold_events_path(target_date: str) -> Path:
    return DATA_DIR / "threshold_cycle" / f"threshold_events_{target_date}.jsonl"


def _sim_post_sell_path(target_date: str) -> Path:
    return DATA_DIR / "post_sell" / f"sim_post_sell_evaluations_{target_date}.jsonl"


def _real_post_sell_path(target_date: str) -> Path:
    return DATA_DIR / "post_sell" / f"post_sell_evaluations_{target_date}.jsonl"


def _threshold_cycle_ev_path(target_date: str) -> Path:
    return DATA_DIR / "report" / "threshold_cycle_ev" / f"threshold_cycle_ev_{target_date}.json"


def _source_quality_path(target_date: str) -> Path:
    return DATA_DIR / "report" / "observation_source_quality_audit" / f"observation_source_quality_audit_{target_date}.json"


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, default: float | None = 0.0) -> float | None:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _event_fields(event: dict[str, Any]) -> dict[str, Any]:
    fields = event.get("fields") if isinstance(event.get("fields"), dict) else {}
    return {**event, **fields}


def _event_date(event: dict[str, Any]) -> str:
    for key in ("date", "target_date", "source_date", "trading_date"):
        value = str(event.get(key) or "").strip()
        if len(value) >= 10:
            return value[:10]
    ts = str(event.get("timestamp") or event.get("created_at") or event.get("ts") or "").strip()
    return ts[:10] if len(ts) >= 10 else ""


def _hard_blocking_stages(source_quality: dict[str, Any]) -> set[str]:
    summary = source_quality.get("summary") if isinstance(source_quality.get("summary"), dict) else {}
    raw = summary.get("hard_blocking_stages") or source_quality.get("hard_blocking_stages") or []
    if not isinstance(raw, list):
        raw = [raw]
    return {str(item).strip() for item in raw if str(item).strip()}


def _source_quality_summary(target_date: str) -> dict[str, Any]:
    path = _source_quality_path(target_date)
    payload = _load_json(path)
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    status = str(payload.get("status") or ("missing" if not path.exists() else "loaded"))
    hard_gap_count = _safe_int(summary.get("hard_blocking_contract_gap_count"), 0)
    tuning_input_allowed = summary.get("tuning_input_allowed")
    if tuning_input_allowed is None:
        tuning_input_allowed = status not in {"fail", "missing", "invalid"} and hard_gap_count <= 0
    if status == "fail" or hard_gap_count > 0:
        tuning_input_allowed = False
    return {
        "artifact": str(path) if path.exists() else None,
        "status": status,
        "tuning_input_allowed": bool(tuning_input_allowed),
        "hard_blocking_contract_gap_count": hard_gap_count,
        "hard_blocking_excluded_row_count": _safe_int(summary.get("hard_blocking_excluded_row_count"), 0),
        "raw_row_exclusion_applied": bool(summary.get("raw_row_exclusion_applied") or payload.get("raw_row_exclusion")),
        "hard_blocking_stages": sorted(_hard_blocking_stages(payload)),
    }


def _iter_input_events(target_date: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    clean_policy = clean_baseline_policy()
    events: list[dict[str, Any]] = []
    excluded_pre_baseline = 0
    source_paths = {
        "pipeline_events": _pipeline_events_path(target_date),
        "threshold_events": _threshold_events_path(target_date),
    }
    for source_name, path in source_paths.items():
        for event in iter_jsonl(path):
            fields = _event_fields(event)
            event_date = _event_date(fields) or target_date
            if not is_date_allowed(event_date, clean_policy):
                excluded_pre_baseline += 1
                continue
            fields["source_name"] = source_name
            fields["source_date"] = event_date
            events.append(fields)
    return events, {
        "source_paths": {name: str(path) if path.exists() else None for name, path in source_paths.items()},
        "excluded_pre_baseline_count": excluded_pre_baseline,
        "clean_tuning_baseline": clean_policy,
    }


def _load_sim_ev_values(target_date: str) -> dict[str, list[float]]:
    if not is_date_allowed(target_date, clean_baseline_policy()):
        return {}
    values: dict[str, list[float]] = defaultdict(list)
    path = _sim_post_sell_path(target_date)
    for event in iter_jsonl(path):
        fields = _event_fields(event)
        event_date = _event_date(fields) or str(fields.get("entry_date") or "")[:10]
        if event_date and event_date != target_date:
            continue
        profit = _safe_float(
            fields.get("profit_rate")
            if fields.get("profit_rate") is not None
            else fields.get("sim_profit_rate")
            if fields.get("sim_profit_rate") is not None
            else fields.get("post_sell_profit_rate"),
            None,
        )
        if profit is None:
            continue
        values[_context_bucket(fields)].append(float(profit))
    return values


def _load_real_ev_values(target_date: str) -> dict[str, list[float]]:
    if not is_date_allowed(target_date, clean_baseline_policy()):
        return {}
    values: dict[str, list[float]] = defaultdict(list)
    path = _real_post_sell_path(target_date)
    for event in iter_jsonl(path):
        fields = _event_fields(event)
        event_date = _event_date(fields) or str(fields.get("entry_date") or fields.get("sell_date") or "")[:10]
        if event_date and event_date != target_date:
            continue
        if not _safe_bool(fields.get("actual_order_submitted")):
            continue
        profit = _safe_float(
            fields.get("profit_rate")
            if fields.get("profit_rate") is not None
            else fields.get("post_sell_profit_rate"),
            None,
        )
        if profit is None:
            continue
        values[_context_bucket(fields)].append(float(profit))
    return values


def _context_bucket(fields: dict[str, Any]) -> str:
    spread_bps = _safe_float(fields.get("spread_bps"), None)
    if spread_bps is None:
        spread_ratio = _safe_float(fields.get("spread_ratio"), None)
        spread_bps = float(spread_ratio or 0.0) * 10000.0 if spread_ratio is not None else 0.0
    buy_pressure = _safe_float(fields.get("buy_pressure_10t") or fields.get("tick_buy_pressure_10t"), 0.0) or 0.0
    micro_state = str(fields.get("orderbook_micro_state") or fields.get("micro_state") or "").lower()
    latency_state = str(fields.get("latency_state") or "").upper()
    quote_stale = _safe_bool(fields.get("quote_stale")) or _safe_bool(fields.get("stale_quote_submit_block"))
    if quote_stale or latency_state == "DANGER":
        return "guarded_or_stale"
    if spread_bps <= 12.0 and buy_pressure >= 60.0 and "weak" not in micro_state:
        return "urgent_tight_spread"
    if spread_bps >= 35.0 or buy_pressure <= 45.0 or "weak" in micro_state:
        return "passive_wide_or_weak"
    return "balanced_normal"


def _template_for_bucket(bucket: str) -> dict[str, Any]:
    templates = {
        "urgent_tight_spread": {
            "leg_count": 2,
            "price_offsets_ticks": [0, 1],
            "qty_weight_min": 0.65,
            "qty_weight_max": 0.85,
            "urgency_score": 0.82,
            "passive_edge_score": 0.28,
            "price_candidates": ["resolved_order_price", "best_bid", "bid-1tick"],
        },
        "balanced_normal": {
            "leg_count": 2,
            "price_offsets_ticks": [0, 1],
            "qty_weight_min": 0.55,
            "qty_weight_max": 0.70,
            "urgency_score": 0.55,
            "passive_edge_score": 0.52,
            "price_candidates": ["resolved_order_price", "best_bid", "bid-1tick", "reference_target", "AI_candidate"],
        },
        "passive_wide_or_weak": {
            "leg_count": 3,
            "price_offsets_ticks": [0, 1, 2],
            "qty_weight_min": 0.30,
            "qty_weight_max": 0.50,
            "urgency_score": 0.30,
            "passive_edge_score": 0.78,
            "price_candidates": ["best_bid", "bid-1tick", "bid-2tick", "reference_target"],
        },
        "guarded_or_stale": {
            "leg_count": 1,
            "price_offsets_ticks": [0],
            "qty_weight_min": 1.0,
            "qty_weight_max": 1.0,
            "urgency_score": 0.0,
            "passive_edge_score": 0.0,
            "price_candidates": ["resolved_order_price"],
        },
    }
    return dict(templates.get(bucket) or templates["balanced_normal"])


def _is_real_submit_event(fields: dict[str, Any]) -> bool:
    return _safe_bool(fields.get("actual_order_submitted"))


def _is_sim_event(fields: dict[str, Any]) -> bool:
    stage = str(fields.get("stage") or fields.get("event") or "").strip()
    if str(stage).startswith("scalp_sim_"):
        return True
    decision_authority = str(fields.get("decision_authority") or "").strip()
    if decision_authority in {"sim_observation_only", "swing_sim_exploration_only"}:
        return True
    if _safe_bool(fields.get("broker_order_forbidden")) and ("sim" in stage or "probe" in stage):
        return True
    return False


def _quality_counts(events: list[dict[str, Any]], source_quality: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], int]:
    blocked_stages = set(source_quality.get("hard_blocking_stages") or [])
    buckets: dict[str, dict[str, Any]] = defaultdict(lambda: defaultdict(int))
    excluded_source_quality = 0
    for fields in events:
        stage = str(fields.get("stage") or fields.get("event") or "").strip()
        if stage in blocked_stages:
            excluded_source_quality += 1
            continue
        bucket = _context_bucket(fields)
        row = buckets[bucket]
        if _is_real_submit_event(fields):
            row["real_sample_count"] += 1
            if stage == "order_leg_sent" or _safe_bool(fields.get("broker_order_submitted")):
                row["real_submitted_count"] += 1
            if str(fields.get("fill_status") or "").upper() == "PARTIAL" or _safe_int(fields.get("filled_qty"), 0) > 0:
                row["partial_fill_count"] += 1
            if stage in {"order_leg_fail", "order_bundle_failed"}:
                row["cancel_or_fail_count"] += 1
            if _safe_bool(fields.get("late_fill")) or _safe_bool(fields.get("late_fill_detected")):
                row["late_fill_count"] += 1
        if _is_sim_event(fields):
            row["sim_sample_count"] += 1
            if stage in {"scalp_sim_buy_order_assumed_filled", "scalp_sim_sell_order_assumed_filled"}:
                row["sim_fill_count"] += 1
            if stage in {"scalp_sim_entry_expired", "scalp_sim_entry_unpriced"}:
                row["cancel_or_fail_count"] += 1
    return {key: dict(value) for key, value in buckets.items()}, excluded_source_quality


def _pct(count: int, total: int) -> float:
    return round((count / total) * 100.0, 4) if total > 0 else 0.0


def _build_candidate_grid(
    buckets: dict[str, dict[str, Any]],
    sim_ev_values: dict[str, list[float]],
    real_ev_values: dict[str, list[float]],
) -> list[dict[str, Any]]:
    grid: list[dict[str, Any]] = []
    for bucket in sorted(set(buckets) | set(sim_ev_values) | set(real_ev_values)):
        counts = buckets.get(bucket) or {}
        template = _template_for_bucket(bucket)
        real_count = _safe_int(counts.get("real_sample_count"), 0)
        sim_count = _safe_int(counts.get("sim_sample_count"), 0)
        total = max(1, real_count + sim_count)
        real_ev_list = real_ev_values.get(bucket) or []
        sim_ev_list = sim_ev_values.get(bucket) or []
        real_outcome_count = len(real_ev_list)
        real_ev = round(mean(real_ev_list), 4) if real_ev_list else None
        sim_ev = round(mean(sim_ev_list), 4) if sim_ev_list else None
        primary_ev = real_ev if real_ev is not None else None
        notional_ev = primary_ev
        partial_fill_rate = _pct(_safe_int(counts.get("partial_fill_count"), 0), max(real_count, 1))
        cancel_rate = _pct(_safe_int(counts.get("cancel_or_fail_count"), 0), total)
        late_fill_rate = _pct(_safe_int(counts.get("late_fill_count"), 0), max(real_count, 1))
        downside_source = real_ev_list if real_ev_list else sim_ev_list
        downside = sorted(downside_source)[max(0, int(len(downside_source) * 0.10) - 1)] if downside_source else 0.0
        if real_count < SAMPLE_FLOOR_REAL:
            floor_status = "hold_sample"
            primary_sample_book = "none"
        elif real_ev is not None:
            floor_status = "pass"
            primary_sample_book = "real"
        elif sim_count >= SAMPLE_FLOOR_SIM and sim_ev is not None:
            floor_status = "hold_real_outcome_pending"
            primary_sample_book = "sim_diagnostic"
        else:
            floor_status = "hold_real_outcome_pending"
            primary_sample_book = "real_outcome_pending"
        passed = (
            bucket != "guarded_or_stale"
            and real_count >= SAMPLE_FLOOR_REAL
            and real_ev is not None
            and real_ev > 0
            and downside > -2.0
        )
        grid.append(
            {
                "context_bucket": bucket,
                **template,
                "price_candidates": [item for item in template["price_candidates"] if item in ALLOWED_PRICE_CANDIDATES],
                "real_sample_count": real_count,
                "sim_sample_count": sim_count,
                "real_outcome_joined_sample": real_outcome_count,
                "primary_sample_book": primary_sample_book,
                "fill_quality": round(
                    (_safe_int(counts.get("real_submitted_count"), 0) + _safe_int(counts.get("sim_fill_count"), 0))
                    / total,
                    4,
                ),
                "missed_upside": round(max(0.0, primary_ev or 0.0), 4),
                "source_quality_adjusted_ev_pct": primary_ev,
                "real_source_quality_adjusted_ev_pct": real_ev,
                "diagnostic_sim_ev_pct": sim_ev,
                "notional_weighted_ev_pct": notional_ev,
                "partial_fill_rate": partial_fill_rate,
                "cancel_rate": cancel_rate,
                "late_fill_rate": late_fill_rate,
                "downside_p10_profit_rate": round(float(downside), 4),
                "sample_floor_status": "pass" if passed else floor_status,
                "candidate_passed": passed,
            }
        )
    return grid


def _policy_payload(target_date: str, report_json: Path, candidate_grid: list[dict[str, Any]]) -> dict[str, Any]:
    passed = [item for item in candidate_grid if item.get("candidate_passed")]
    version_seed = json.dumps(passed, sort_keys=True, ensure_ascii=False)
    digest = hashlib.sha1(version_seed.encode("utf-8")).hexdigest()[:10]
    policy_version = f"{RUNTIME_FAMILY}:{target_date}:{digest}"
    return {
        "schema_version": POLICY_SCHEMA_VERSION,
        "policy_version": policy_version,
        "source_date": target_date,
        "source_report": str(report_json),
        "runtime_apply_allowed": False,
        "preopen_guard_required": True,
        "decision_authority": "next_preopen_bounded_entry_split_policy",
        "forbidden_uses": [
            "increase_requested_qty",
            "cap_release",
            "broker_guard_relief",
            "intraday_mutation",
            "provider_route_change",
        ],
        "buckets": {
            str(item["context_bucket"]): {
                "context_bucket": item["context_bucket"],
                "leg_count": item["leg_count"],
                "price_offsets_ticks": item["price_offsets_ticks"],
                "qty_weight_min": item["qty_weight_min"],
                "qty_weight_max": item["qty_weight_max"],
                "urgency_score": item["urgency_score"],
                "passive_edge_score": item["passive_edge_score"],
                "source_quality_adjusted_ev_pct": item["source_quality_adjusted_ev_pct"],
                "notional_weighted_ev_pct": item["notional_weighted_ev_pct"],
                "downside_p10_profit_rate": item["downside_p10_profit_rate"],
            }
            for item in passed
        },
    }


def build_report(target_date: str, *, write: bool = True) -> dict[str, Any]:
    target_date = str(target_date).strip()
    source_quality = _source_quality_summary(target_date)
    events, load_summary = _iter_input_events(target_date)
    counts, excluded_source_quality = _quality_counts(events, source_quality)
    sim_ev_values = _load_sim_ev_values(target_date)
    real_ev_values = _load_real_ev_values(target_date)
    candidate_grid = _build_candidate_grid(counts, sim_ev_values, real_ev_values)
    json_path, md_path = report_paths(target_date)
    policy_json = policy_path(target_date)
    source_quality_allowed = source_quality.get("tuning_input_allowed") is True
    policy = _policy_payload(target_date, json_path, candidate_grid if source_quality_allowed else [])
    recommended_candidates = [
        {**item, "runtime_apply_allowed": False}
        for item in candidate_grid
        if source_quality_allowed and item.get("candidate_passed")
    ]
    report = {
        "schema_version": SCHEMA_VERSION,
        "date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "report_type": REPORT_TYPE,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "metric_contract": {
            "metric_role": "primary_ev",
            "decision_authority": "next_preopen_bounded_entry_split_policy",
            "window_policy": "rolling_10d_with_daily_diagnostic",
            "sample_floor": {"real": SAMPLE_FLOOR_REAL, "sim": SAMPLE_FLOOR_SIM},
            "primary_decision_metric": "source_quality_adjusted_ev_pct",
            "source_quality_gate": "observation_source_quality_audit_hard_block_rows_excluded",
            "forbidden_uses": [
                "requested_qty_increase",
                "real_execution_quality_approval_from_sim",
                "intraday_threshold_mutation",
                "broker_guard_relief",
            ],
        },
        "source_quality": source_quality,
        "input_summary": {
            **load_summary,
            "loaded_event_count": len(events),
            "excluded_source_quality_event_count": excluded_source_quality,
            "sim_post_sell_path": str(_sim_post_sell_path(target_date)) if _sim_post_sell_path(target_date).exists() else None,
            "real_post_sell_path": str(_real_post_sell_path(target_date)) if _real_post_sell_path(target_date).exists() else None,
            "threshold_cycle_ev_path": str(_threshold_cycle_ev_path(target_date)) if _threshold_cycle_ev_path(target_date).exists() else None,
        },
        "candidate_grid": candidate_grid,
        "recommended_policy": {
            "runtime_apply_allowed": False,
            "preopen_guard_required": True,
            "policy_file": str(policy_json),
            "policy_version": policy["policy_version"],
            "candidate_count": len(recommended_candidates),
            "candidates": recommended_candidates,
        },
    }
    if write:
        _write_json(json_path, report)
        _write_json(policy_json, policy)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(_render_markdown(report), encoding="utf-8")
    return report


def _render_markdown(report: dict[str, Any]) -> str:
    rec = report.get("recommended_policy") if isinstance(report.get("recommended_policy"), dict) else {}
    lines = [
        f"# Entry Split Order Plan - {report.get('date')}",
        "",
        "## Summary",
        f"- schema_version: `{report.get('schema_version')}`",
        f"- runtime_effect: `{report.get('runtime_effect')}`",
        f"- recommended_policy_candidates: `{rec.get('candidate_count')}`",
        f"- runtime_apply_allowed: `{rec.get('runtime_apply_allowed')}`",
        f"- policy_file: `{rec.get('policy_file') or '-'}`",
        "",
        "## Candidate Grid",
    ]
    for item in report.get("candidate_grid") or []:
        if not isinstance(item, dict):
            continue
        lines.append(
            "- "
            f"`{item.get('context_bucket')}` legs=`{item.get('leg_count')}` "
            f"real/sim=`{item.get('real_sample_count')}/{item.get('sim_sample_count')}` "
            f"ev=`{item.get('source_quality_adjusted_ev_pct')}` "
            f"cancel=`{item.get('cancel_rate')}` "
            f"pass=`{item.get('candidate_passed')}`"
        )
    return "\n".join(lines) + "\n"


def _load_policy_from_env(policy_file: str | None = None) -> tuple[dict[str, Any], str]:
    enabled = str(os.environ.get("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED", "")).strip().lower()
    if enabled not in {"1", "true", "yes", "on"}:
        return {}, "policy_disabled"
    path_text = str(policy_file or os.environ.get("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_FILE") or "").strip()
    if not path_text:
        return {}, "policy_file_missing"
    path = Path(path_text)
    if not path.exists():
        return {}, "policy_file_not_found"
    payload = _load_json(path)
    if payload.get("schema_version") != POLICY_SCHEMA_VERSION:
        return {}, "invalid_policy_schema"
    if not isinstance(payload.get("buckets"), dict):
        return {}, "invalid_policy_buckets"
    return payload, "loaded"


def _policy_is_stale(policy: dict[str, Any], *, now: datetime | None = None, max_age_days: int = 5) -> bool:
    source_date = str(policy.get("source_date") or "").strip()
    if not source_date:
        return True
    now_date = (now or datetime.now(timezone(timedelta(hours=9)))).date()
    try:
        policy_date = date.fromisoformat(source_date)
    except ValueError:
        return True
    return now_date - policy_date > timedelta(days=max_age_days)


def _max_legs_for_qty(qty: int) -> int:
    if qty <= 1:
        return 1
    if qty == 2:
        return 2
    if 3 <= qty <= 5:
        return 2
    return 3


def _split_qty(total_qty: int, leg_count: int, first_weight: float) -> list[int]:
    leg_count = min(max(1, leg_count), total_qty)
    if leg_count <= 1:
        return [total_qty]
    first_qty = max(1, min(total_qty - (leg_count - 1), int(round(total_qty * first_weight))))
    remaining = total_qty - first_qty
    quantities = [first_qty]
    for idx in range(leg_count - 1):
        legs_left = leg_count - 1 - idx
        qty = max(1, remaining // legs_left)
        quantities.append(qty)
        remaining -= qty
    if sum(quantities) != total_qty:
        quantities[-1] += total_qty - sum(quantities)
    return quantities


def _tick_size(price: int) -> int:
    try:
        from src.utils import kiwoom_utils

        return max(1, int(kiwoom_utils.get_tick_size(price) or 1))
    except Exception:
        return 1


def apply_entry_split_order_policy(
    planned_orders: list[dict[str, Any]] | tuple[dict[str, Any], ...] | None,
    *,
    stock: dict[str, Any] | None = None,
    latency_gate: dict[str, Any] | None = None,
    policy_file: str | None = None,
    now: datetime | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    orders = [dict(item) for item in (planned_orders or []) if isinstance(item, dict)]
    latency_gate = latency_gate if isinstance(latency_gate, dict) else {}
    stock = stock if isinstance(stock, dict) else {}
    total_qty = sum(_safe_int(item.get("qty"), 0) for item in orders)
    fields: dict[str, Any] = {
        "entry_split_order_policy_applied": False,
        "entry_split_order_original_order_count": len(orders),
        "entry_split_order_original_qty": total_qty,
    }
    if total_qty <= 1:
        fields["entry_split_order_skip_reason"] = "qty_lte_1"
        return orders, fields
    if len(orders) != 1:
        fields["entry_split_order_skip_reason"] = "multi_order_input_not_supported_v1"
        return orders, fields
    if _safe_bool(latency_gate.get("quote_stale")) or _safe_bool(latency_gate.get("stale_quote_submit_block")):
        fields["entry_split_order_skip_reason"] = "stale_quote"
        return orders, fields
    if str(latency_gate.get("latency_state") or "").upper() == "DANGER" and not _safe_bool(
        latency_gate.get("latency_canary_applied")
    ):
        fields["entry_split_order_skip_reason"] = "danger_latency_without_approved_relief"
        return orders, fields
    policy, load_status = _load_policy_from_env(policy_file)
    if not policy:
        fields["entry_split_order_skip_reason"] = load_status
        return orders, fields
    if _policy_is_stale(policy, now=now):
        fields["entry_split_order_skip_reason"] = "stale_policy"
        return orders, fields
    bucket = _context_bucket({**stock, **latency_gate})
    bucket_policy = (policy.get("buckets") or {}).get(bucket)
    if not isinstance(bucket_policy, dict):
        fields["entry_split_order_skip_reason"] = "bucket_policy_missing"
        fields["entry_split_order_bucket"] = bucket
        return orders, fields
    max_legs = _max_legs_for_qty(total_qty)
    desired_legs = min(_safe_int(bucket_policy.get("leg_count"), 1), max_legs, total_qty)
    if desired_legs <= 1:
        fields["entry_split_order_skip_reason"] = "single_leg_policy"
        fields["entry_split_order_bucket"] = bucket
        return orders, fields
    base_order = orders[0]
    base_price = _safe_int(
        base_order.get("price")
        or latency_gate.get("order_price")
        or latency_gate.get("resolved_order_price")
        or latency_gate.get("best_bid")
        or stock.get("curr_price"),
        0,
    )
    if base_price <= 0:
        fields["entry_split_order_skip_reason"] = "invalid_base_price"
        fields["entry_split_order_bucket"] = bucket
        return orders, fields
    tick = _tick_size(base_price)
    offsets = [
        _safe_int(item, 0)
        for item in (bucket_policy.get("price_offsets_ticks") or [0])
        if _safe_int(item, 0) in {0, 1, 2}
    ][:desired_legs]
    while len(offsets) < desired_legs:
        offsets.append(offsets[-1] + 1 if offsets else 0)
    first_weight = (_safe_float(bucket_policy.get("qty_weight_min"), 0.5) or 0.5)
    quantities = _split_qty(total_qty, desired_legs, first_weight)
    split_orders: list[dict[str, Any]] = []
    for idx, qty in enumerate(quantities):
        price = clamp_price_to_tick(max(1, base_price - (tick * offsets[idx])))
        split_orders.append(
            {
                **base_order,
                "tag": "entry_split_primary" if idx == 0 else f"entry_split_passive_{idx}",
                "qty": qty,
                "price": price,
                "entry_split_order_leg_index": idx + 1,
                "entry_split_order_policy_version": policy.get("policy_version"),
                "entry_split_order_bucket": bucket,
            }
        )
    if sum(_safe_int(item.get("qty"), 0) for item in split_orders) != total_qty:
        fields["entry_split_order_skip_reason"] = "quantity_conservation_failed"
        return orders, fields
    fields.update(
        {
            "entry_split_order_policy_applied": True,
            "entry_split_order_skip_reason": "",
            "entry_split_order_bucket": bucket,
            "entry_split_order_policy_version": policy.get("policy_version"),
            "entry_split_order_policy_file": policy_file
            or os.environ.get("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_FILE"),
            "entry_split_order_leg_count": len(split_orders),
            "entry_split_order_split_qty": sum(_safe_int(item.get("qty"), 0) for item in split_orders),
        }
    )
    return split_orders, fields


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", "--target-date", dest="target_date", default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args(argv)
    build_report(args.target_date, write=not args.no_write)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
