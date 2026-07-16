from __future__ import annotations

import argparse
import gzip
import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from src.utils.constants import DATA_DIR, TRADING_RULES

KST = timezone(timedelta(hours=9))
REPORT_TYPE = "scalping_avg_down_recovery_calibration"
FAMILY = "scalping_avg_down_recovery_quality_gate"
STAGE = "scale_in"
REPORT_DIR = DATA_DIR / "report" / REPORT_TYPE
CLEAN_BASELINE_DATE = "2026-06-04"
FORBIDDEN_USES = [
    "intraday_threshold_mutation",
    "hard_safety_relaxation",
    "broker_guard_bypass",
    "order_guard_relaxation",
    "quantity_cap_release",
    "provider_route_change",
    "bot_restart",
]
TARGET_ENV_KEYS = [
    "SHALLOW_VOLATILITY_AVG_DOWN_ENABLED",
    "SHALLOW_VOLATILITY_AVG_DOWN_PNL_MIN",
    "SHALLOW_VOLATILITY_AVG_DOWN_PNL_MAX",
    "SHALLOW_VOLATILITY_AVG_DOWN_MIN_HOLD_SEC",
    "SHALLOW_VOLATILITY_AVG_DOWN_MAX_HOLD_SEC",
    "SHALLOW_VOLATILITY_AVG_DOWN_OBSERVATION_MAX_HOLD_SEC",
    "SHALLOW_VOLATILITY_AVG_DOWN_MIN_BUY_PRESSURE",
    "SHALLOW_VOLATILITY_AVG_DOWN_MIN_TICK_ACCEL",
    "SHALLOW_VOLATILITY_AVG_DOWN_MIN_MICRO_VWAP_BP",
    "SHALLOW_VOLATILITY_AVG_DOWN_MAX_QUOTE_AGE_MS",
    "SHALLOW_VOLATILITY_AVG_DOWN_MAX_PER_POSITION",
    "SHALLOW_VOLATILITY_AVG_DOWN_POST_ADD_TAKE_PROFIT_PCT",
    "DEEP_RECOVERY_AVG_DOWN_ENABLED",
    "DEEP_RECOVERY_AVG_DOWN_PNL_MIN",
    "DEEP_RECOVERY_AVG_DOWN_PNL_MAX",
    "DEEP_RECOVERY_AVG_DOWN_MIN_HOLD_SEC",
    "DEEP_RECOVERY_AVG_DOWN_MAX_HOLD_SEC",
    "DEEP_RECOVERY_AVG_DOWN_MIN_AI_SCORE",
    "DEEP_RECOVERY_AVG_DOWN_MAX_AI_SCORE",
    "DEEP_RECOVERY_AVG_DOWN_MIN_BUY_PRESSURE",
    "DEEP_RECOVERY_AVG_DOWN_MIN_TICK_ACCEL",
    "DEEP_RECOVERY_AVG_DOWN_MIN_MICRO_VWAP_BP",
    "DEEP_RECOVERY_AVG_DOWN_MAX_QUOTE_AGE_MS",
    "DEEP_RECOVERY_AVG_DOWN_MAX_PER_POSITION",
    "DEEP_RECOVERY_AVG_DOWN_POST_ADD_TAKE_PROFIT_PCT",
    "DEEP_RECOVERY_AVG_DOWN_EMERGENCY_PCT",
]


def _safe_float(value: Any, default: float | None = 0.0) -> float | None:
    if value in (None, "", "-"):
        return default
    try:
        return float(str(value).replace("+", "").replace("%", ""))
    except (TypeError, ValueError):
        return default


def _boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _parse_time(value: Any) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=KST)
    return parsed


def _events_path(target_date: str) -> Path:
    return DATA_DIR / "pipeline_events" / f"pipeline_events_{target_date}.jsonl"


def _events_paths_for_date(target_date: str) -> list[Path]:
    path = _events_path(target_date)
    if path.exists():
        return [path]
    gzip_path = path.with_suffix(path.suffix + ".gz")
    return [gzip_path] if gzip_path.exists() else []


def _date_from_events_path(path: Path) -> str | None:
    name = path.name
    prefix = "pipeline_events_"
    for suffix in (".jsonl", ".jsonl.gz"):
        if name.startswith(prefix) and name.endswith(suffix):
            return name.removeprefix(prefix).removesuffix(suffix)
    return None


def _iter_events_paths_for_window(target_date: str) -> list[Path]:
    paths_by_date: dict[str, Path] = {}
    events_dir = DATA_DIR / "pipeline_events"
    for pattern in ("pipeline_events_*.jsonl", "pipeline_events_*.jsonl.gz"):
        for path in sorted(events_dir.glob(pattern)):
            date_part = _date_from_events_path(path)
            if not date_part or not (CLEAN_BASELINE_DATE <= date_part <= target_date):
                continue
            existing = paths_by_date.get(date_part)
            if existing is None or existing.suffix == ".gz":
                paths_by_date[date_part] = path
    for path in _events_paths_for_date(target_date):
        date_part = _date_from_events_path(path)
        if (
            date_part
            and CLEAN_BASELINE_DATE <= date_part <= target_date
            and date_part not in paths_by_date
        ):
            paths_by_date[date_part] = path
    return [paths_by_date[date_part] for date_part in sorted(paths_by_date)]


def _iter_events(paths: list[Path]):
    for source in paths:
        source_date = _date_from_events_path(source)
        opener = gzip.open if str(source).endswith(".gz") else open
        if not source.exists():
            continue
        with opener(source, "rt", encoding="utf-8", errors="ignore") as handle:
            for line in handle:
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                fields = (
                    event.get("fields") if isinstance(event.get("fields"), dict) else {}
                )
                yield {**event, **fields, "_source_event_date": source_date}


def _current_values() -> dict[str, Any]:
    return {
        "shallow_enabled": bool(
            getattr(TRADING_RULES, "SHALLOW_VOLATILITY_AVG_DOWN_ENABLED", True)
        ),
        "shallow_pnl_min": float(
            getattr(TRADING_RULES, "SHALLOW_VOLATILITY_AVG_DOWN_PNL_MIN", -0.7)
        ),
        "shallow_pnl_max": float(
            getattr(TRADING_RULES, "SHALLOW_VOLATILITY_AVG_DOWN_PNL_MAX", -0.3)
        ),
        "shallow_min_hold_sec": int(
            getattr(TRADING_RULES, "SHALLOW_VOLATILITY_AVG_DOWN_MIN_HOLD_SEC", 60)
        ),
        "shallow_max_hold_sec": int(
            getattr(TRADING_RULES, "SHALLOW_VOLATILITY_AVG_DOWN_MAX_HOLD_SEC", 120)
        ),
        "shallow_observation_max_hold_sec": int(
            getattr(
                TRADING_RULES,
                "SHALLOW_VOLATILITY_AVG_DOWN_OBSERVATION_MAX_HOLD_SEC",
                240,
            )
        ),
        "shallow_min_buy_pressure": float(
            getattr(TRADING_RULES, "SHALLOW_VOLATILITY_AVG_DOWN_MIN_BUY_PRESSURE", 85.0)
        ),
        "shallow_min_tick_accel": float(
            getattr(TRADING_RULES, "SHALLOW_VOLATILITY_AVG_DOWN_MIN_TICK_ACCEL", 1.05)
        ),
        "shallow_min_micro_vwap_bp": float(
            getattr(TRADING_RULES, "SHALLOW_VOLATILITY_AVG_DOWN_MIN_MICRO_VWAP_BP", 0.0)
        ),
        "shallow_max_quote_age_ms": float(
            getattr(
                TRADING_RULES, "SHALLOW_VOLATILITY_AVG_DOWN_MAX_QUOTE_AGE_MS", 1500.0
            )
        ),
        "shallow_max_per_position": int(
            getattr(TRADING_RULES, "SHALLOW_VOLATILITY_AVG_DOWN_MAX_PER_POSITION", 2)
        ),
        "shallow_post_add_take_profit_pct": float(
            getattr(
                TRADING_RULES,
                "SHALLOW_VOLATILITY_AVG_DOWN_POST_ADD_TAKE_PROFIT_PCT",
                0.3,
            )
        ),
        "deep_enabled": bool(
            getattr(TRADING_RULES, "DEEP_RECOVERY_AVG_DOWN_ENABLED", True)
        ),
        "deep_pnl_min": float(
            getattr(TRADING_RULES, "DEEP_RECOVERY_AVG_DOWN_PNL_MIN", -4.0)
        ),
        "deep_pnl_max": float(
            getattr(TRADING_RULES, "DEEP_RECOVERY_AVG_DOWN_PNL_MAX", -3.25)
        ),
        "deep_min_hold_sec": int(
            getattr(TRADING_RULES, "DEEP_RECOVERY_AVG_DOWN_MIN_HOLD_SEC", 120)
        ),
        "deep_max_hold_sec": int(
            getattr(TRADING_RULES, "DEEP_RECOVERY_AVG_DOWN_MAX_HOLD_SEC", 480)
        ),
        "deep_min_ai_score": int(
            getattr(TRADING_RULES, "DEEP_RECOVERY_AVG_DOWN_MIN_AI_SCORE", 60)
        ),
        "deep_max_ai_score": int(
            getattr(TRADING_RULES, "DEEP_RECOVERY_AVG_DOWN_MAX_AI_SCORE", 74)
        ),
        "deep_min_buy_pressure": float(
            getattr(TRADING_RULES, "DEEP_RECOVERY_AVG_DOWN_MIN_BUY_PRESSURE", 70.0)
        ),
        "deep_min_tick_accel": float(
            getattr(TRADING_RULES, "DEEP_RECOVERY_AVG_DOWN_MIN_TICK_ACCEL", 1.0)
        ),
        "deep_min_micro_vwap_bp": float(
            getattr(TRADING_RULES, "DEEP_RECOVERY_AVG_DOWN_MIN_MICRO_VWAP_BP", -5.0)
        ),
        "deep_max_quote_age_ms": float(
            getattr(TRADING_RULES, "DEEP_RECOVERY_AVG_DOWN_MAX_QUOTE_AGE_MS", 1500.0)
        ),
        "deep_max_per_position": int(
            getattr(TRADING_RULES, "DEEP_RECOVERY_AVG_DOWN_MAX_PER_POSITION", 1)
        ),
        "deep_post_add_take_profit_pct": float(
            getattr(
                TRADING_RULES, "DEEP_RECOVERY_AVG_DOWN_POST_ADD_TAKE_PROFIT_PCT", 0.3
            )
        ),
        "deep_emergency_pct": float(
            getattr(TRADING_RULES, "DEEP_RECOVERY_AVG_DOWN_EMERGENCY_PCT", -5.5)
        ),
    }


def _row_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "sample_count": 0,
            "hit0_rate": 0.0,
            "hit03_rate": 0.0,
            "avg_mfe_30m_pct": 0.0,
            "avg_mae_30m_pct": 0.0,
        }
    return {
        "sample_count": len(rows),
        "hit0_rate": sum(1 for row in rows if row.get("hit0")) / len(rows),
        "hit03_rate": sum(1 for row in rows if row.get("hit03")) / len(rows),
        "avg_mfe_30m_pct": sum(float(row.get("mfe_30m_pct") or 0.0) for row in rows)
        / len(rows),
        "avg_mae_30m_pct": sum(float(row.get("mae_30m_pct") or 0.0) for row in rows)
        / len(rows),
        "avg_final_30m_pct": sum(float(row.get("final_30m_pct") or 0.0) for row in rows)
        / len(rows),
    }


def _build_rows(paths: list[Path]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    sim_series: dict[str, list[tuple[datetime, float]]] = defaultdict(list)
    sim_flags: dict[str, set[str]] = defaultdict(set)
    sim_candidates: list[dict[str, Any]] = []
    real_series: dict[str, list[tuple[datetime, float]]] = defaultdict(list)
    real_candidates: list[dict[str, Any]] = []
    for event in _iter_events(paths):
        stage = str(event.get("stage") or "")
        event_time = _parse_time(event.get("emitted_at"))
        if not event_time:
            continue
        profit = _safe_float(event.get("profit_rate"), None)
        source_date = str(event.get("_source_event_date") or "")
        raw_sim_id = str(event.get("sim_record_id") or "")
        raw_record_id = str(
            event.get("record_id") or event.get("recommendation_id") or ""
        )
        sim_id = (
            f"{source_date}:{raw_sim_id}" if source_date and raw_sim_id else raw_sim_id
        )
        record_id = (
            f"{source_date}:{raw_record_id}"
            if source_date and raw_record_id
            else raw_record_id
        )
        if sim_id and profit is not None:
            sim_series[sim_id].append((event_time, float(profit)))
        if record_id and profit is not None:
            real_series[record_id].append((event_time, float(profit)))
        if sim_id and stage == "scalp_sim_pre_submit_liquidity_guard_would_pass":
            sim_flags[sim_id].add("liquidity")
        if sim_id and stage == "scalp_sim_pre_submit_overbought_guard_would_pass":
            sim_flags[sim_id].add("overbought")
        if (
            sim_id
            and stage == "scalp_sim_buy_order_assumed_filled"
            and event.get("would_submit_stage") == "order_leg_sent"
        ):
            sim_flags[sim_id].add("filled")
        if (
            sim_id
            and stage == "scalp_sim_scale_in_candidate_funnel"
            and str(event.get("add_type") or event.get("scale_in_arm") or "").upper()
            == "AVG_DOWN"
            and str(event.get("scale_in_candidate_funnel_state") or "") == "eligible"
        ):
            sim_candidates.append(
                {
                    "id": sim_id,
                    "time": event_time,
                    "profit_rate": float(profit or 0.0),
                    "held_sec": _safe_float(event.get("held_sec"), 0.0),
                }
            )
        if (
            record_id
            and stage == "stop_line_touch_mandatory_avg_down_submitted"
            and str(event.get("add_type") or "").upper() == "AVG_DOWN"
            and _boolish(event.get("actual_order_submitted"))
        ):
            real_candidates.append(
                {
                    "id": record_id,
                    "time": event_time,
                    "profit_rate": float(profit or 0.0),
                    "held_sec": _safe_float(event.get("held_sec"), 0.0),
                    "current_ai_score": _safe_float(event.get("current_ai_score"), 0.0),
                }
            )

    def post_add(future_pct: float, decision_pct: float, ratio: float = 0.33) -> float:
        return (
            (1.0 + future_pct / 100.0)
            / (1.0 + (ratio * decision_pct / 100.0) / (1.0 + ratio))
            - 1.0
        ) * 100.0

    shallow_rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in sorted(sim_candidates, key=lambda item: item["time"]):
        if row["id"] in seen or not {"liquidity", "overbought", "filled"}.issubset(
            sim_flags.get(row["id"], set())
        ):
            continue
        seen.add(row["id"])
        p0 = row["profit_rate"]
        future = [
            post_add(p, p0)
            for t, p in sim_series.get(row["id"], [])
            if row["time"] <= t <= row["time"] + timedelta(minutes=30)
        ]
        if not future:
            continue
        shallow_rows.append(
            {
                **row,
                "mfe_30m_pct": max(future),
                "mae_30m_pct": min(future),
                "final_30m_pct": future[-1],
                "hit0": max(future) >= 0.0,
                "hit03": max(future) >= 0.3,
                "post_add_basis": True,
            }
        )

    deep_rows: list[dict[str, Any]] = []
    for row in real_candidates:
        future = [
            p
            for t, p in real_series.get(row["id"], [])
            if row["time"] <= t <= row["time"] + timedelta(minutes=30)
        ]
        if not future:
            continue
        deep_rows.append(
            {
                **row,
                "mfe_30m_pct": max(future),
                "mae_30m_pct": min(future),
                "final_30m_pct": future[-1],
                "hit0": max(future) >= 0.0,
                "hit03": max(future) >= 0.3,
                "post_add_basis": "observed_real_after_add",
            }
        )
    return shallow_rows, deep_rows


def build_report(
    target_date: str, *, generated_at: str | None = None
) -> dict[str, Any]:
    generated_at = generated_at or datetime.now(KST).isoformat(timespec="seconds")
    window_paths = _iter_events_paths_for_window(target_date)
    daily_paths = _events_paths_for_date(target_date)
    shallow_rows, deep_rows = _build_rows(window_paths)
    daily_shallow_rows, daily_deep_rows = _build_rows(daily_paths)
    shallow_primary = [
        r
        for r in shallow_rows
        if -0.70 <= r["profit_rate"] <= -0.30
        and 60 <= float(r.get("held_sec") or 0) <= 120
    ]
    shallow_observation = [
        r
        for r in shallow_rows
        if -0.70 <= r["profit_rate"] <= -0.30
        and 120 < float(r.get("held_sec") or 0) <= 240
    ]
    deep_primary = [
        r
        for r in deep_rows
        if -4.00 <= r["profit_rate"] <= -3.25
        and 120 <= float(r.get("held_sec") or 0) <= 480
        and 60 <= float(r.get("current_ai_score") or 0) <= 74
    ]
    daily_shallow_primary = [
        r
        for r in daily_shallow_rows
        if -0.70 <= r["profit_rate"] <= -0.30
        and 60 <= float(r.get("held_sec") or 0) <= 120
    ]
    daily_deep_primary = [
        r
        for r in daily_deep_rows
        if -4.00 <= r["profit_rate"] <= -3.25
        and 120 <= float(r.get("held_sec") or 0) <= 480
        and 60 <= float(r.get("current_ai_score") or 0) <= 74
    ]
    current = _current_values()
    recommended = {
        **current,
        "shallow_enabled": True,
        "shallow_pnl_min": -0.70,
        "shallow_pnl_max": -0.30,
        "shallow_min_hold_sec": 60,
        "shallow_max_hold_sec": 120,
        "shallow_observation_max_hold_sec": 240,
        "shallow_min_buy_pressure": 85.0,
        "shallow_min_tick_accel": 1.05,
        "shallow_min_micro_vwap_bp": 0.0,
        "shallow_max_quote_age_ms": 1500.0,
        "shallow_max_per_position": 2,
        "shallow_post_add_take_profit_pct": 0.30,
        "deep_enabled": True,
        "deep_pnl_min": -4.00,
        "deep_pnl_max": -3.25,
        "deep_min_hold_sec": 120,
        "deep_max_hold_sec": 480,
        "deep_min_ai_score": 60,
        "deep_max_ai_score": 74,
        "deep_min_buy_pressure": 70.0,
        "deep_min_tick_accel": 1.0,
        "deep_min_micro_vwap_bp": -5.0,
        "deep_max_quote_age_ms": 1500.0,
        "deep_max_per_position": 1,
        "deep_post_add_take_profit_pct": 0.30,
        "deep_emergency_pct": -5.50,
    }
    shallow_metrics = _row_summary(shallow_primary)
    deep_metrics = _row_summary(deep_primary)
    daily_shallow_metrics = _row_summary(daily_shallow_primary)
    daily_deep_metrics = _row_summary(daily_deep_primary)
    sample_floor_met = (
        shallow_metrics["sample_count"] >= 10 and deep_metrics["sample_count"] >= 5
    )
    edge_ok = (
        shallow_metrics["hit03_rate"] >= 0.25 and deep_metrics["hit03_rate"] >= 0.50
    )
    source_available = bool(window_paths)
    state = (
        "adjust_up"
        if source_available and sample_floor_met and edge_ok
        else "hold_sample"
    )
    source_quality_gate = "pass" if source_available else "source_quality_blocked"
    calibration_reason = (
        "post_add_mfe_mae_edge_ok"
        if state == "adjust_up"
        else (
            "source_pipeline_events_missing"
            if not source_available
            else "sample_or_edge_floor_not_met"
        )
    )
    metric_contract = {
        "metric_role": "bounded_tunable_recovery_quality_gate",
        "decision_authority": "postclose_calibration_candidate_preopen_only",
        "window_policy": "rolling_clean_baseline_pipeline_events",
        "clean_baseline_date": CLEAN_BASELINE_DATE,
        "sample_floor": "rolling_shallow_primary>=10 and rolling_deep_primary>=5",
        "primary_decision_metric": "rolling_post_add_mfe_mae_hit03_edge",
        "source_quality_gate": "pipeline_events_present_and_preopen_source_quality_preflight",
        "forbidden_uses": FORBIDDEN_USES,
    }
    candidate = {
        "family": FAMILY,
        "stage": STAGE,
        "priority": 37,
        "family_type": "bounded_tunable_scalping_avg_down_recovery_gate",
        "calibration_state": state,
        "calibration_reason": calibration_reason,
        "threshold_version": f"{FAMILY}:{target_date}:v1",
        "sample_count": shallow_metrics["sample_count"] + deep_metrics["sample_count"],
        "sample_floor": "rolling_shallow_primary>=10 and rolling_deep_primary>=5",
        "sample_floor_passed": bool(sample_floor_met),
        "allowed_runtime_apply": state == "adjust_up",
        "safety_revert_required": False,
        "source_quality_gate": source_quality_gate,
        "current_values": current,
        "recommended_values": recommended,
        "target_env_keys": TARGET_ENV_KEYS if state == "adjust_up" else [],
        "source_event_dates": [_date_from_events_path(path) for path in window_paths],
        "source_event_paths": [str(path) for path in window_paths],
        "metric_contract": metric_contract,
        "source_metrics": {
            "shallow_primary": shallow_metrics,
            "rolling_shallow_primary": shallow_metrics,
            "shallow_observation_extension_post_add": _row_summary(shallow_observation),
            "deep_primary": deep_metrics,
            "rolling_deep_primary": deep_metrics,
            "daily_shallow_primary": daily_shallow_metrics,
            "daily_deep_primary": daily_deep_metrics,
            "shallow_raw_submit_pass_avg_down_count": len(shallow_rows),
            "deep_raw_real_avg_down_count": len(deep_rows),
            "daily_shallow_raw_submit_pass_avg_down_count": len(daily_shallow_rows),
            "daily_deep_raw_real_avg_down_count": len(daily_deep_rows),
        },
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "decision_authority": "postclose_calibration_candidate_preopen_only",
        "forbidden_uses": FORBIDDEN_USES,
    }
    return {
        "schema_version": 1,
        "report_type": REPORT_TYPE,
        "target_date": target_date,
        "generated_at": generated_at,
        "family": FAMILY,
        "stage": STAGE,
        "runtime_effect": False,
        "allowed_runtime_apply": bool(candidate["allowed_runtime_apply"]),
        "decision_authority": "postclose_calibration_candidate_preopen_only",
        "forbidden_uses": FORBIDDEN_USES,
        "metric_contract": metric_contract,
        "source_quality": {
            "status": "pass" if source_available else "missing_input",
            "input": [str(path) for path in window_paths],
            "daily_input": [str(path) for path in daily_paths],
            "clean_baseline_date": CLEAN_BASELINE_DATE,
        },
        "calibration_candidates": [candidate],
    }


def _default_output_paths(target_date: str) -> tuple[Path, Path]:
    base = REPORT_DIR / f"{REPORT_TYPE}_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def write_outputs(
    report: dict[str, Any], *, output_json: Path, output_md: Path
) -> None:
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    candidate = (report.get("calibration_candidates") or [{}])[0]
    metrics = (
        candidate.get("source_metrics")
        if isinstance(candidate.get("source_metrics"), dict)
        else {}
    )
    lines = [
        f"# {report.get('target_date')} Scalping AVG_DOWN Recovery Calibration",
        "",
        f"- calibration_state: `{candidate.get('calibration_state')}`",
        f"- allowed_runtime_apply: `{str(candidate.get('allowed_runtime_apply')).lower()}`",
        "- runtime_effect: `false`",
        f"- window_policy: `{(candidate.get('metric_contract') or {}).get('window_policy')}`",
        f"- shallow_primary: `{metrics.get('shallow_primary')}`",
        f"- daily_shallow_primary: `{metrics.get('daily_shallow_primary')}`",
        f"- shallow_observation_extension_post_add: `{metrics.get('shallow_observation_extension_post_add')}`",
        f"- deep_primary: `{metrics.get('deep_primary')}`",
        f"- daily_deep_primary: `{metrics.get('daily_deep_primary')}`",
    ]
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build scalping AVG_DOWN recovery calibration candidate."
    )
    parser.add_argument("--target-date", default=datetime.now(KST).strftime("%Y-%m-%d"))
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args(argv)
    output_json, output_md = (
        (args.output_json, args.output_md)
        if args.output_json and args.output_md
        else _default_output_paths(args.target_date)
    )
    report = build_report(args.target_date)
    write_outputs(report, output_json=output_json, output_md=output_md)
    if args.print_summary:
        print(
            json.dumps(
                report.get("calibration_candidates", [{}])[0],
                ensure_ascii=False,
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
