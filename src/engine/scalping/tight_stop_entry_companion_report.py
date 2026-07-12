"""Build source-only entry quality evidence for tighter stop regimes."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from src.engine.automation.source_quality_clean_baseline import (
    clean_baseline_policy,
    filter_allowed_dates,
)
from src.engine.automation.source_quality_hard_gate import (
    apply_source_quality_preflight_block,
    load_source_quality_preflight,
    source_quality_preflight_blocked,
)
from src.utils.constants import DATA_DIR, TRADING_RULES
from src.utils.jsonl_io import existing_or_gzip_path, open_text_auto
from src.utils.market_day import is_krx_trading_day


REPORT_TYPE = "tight_stop_entry_companion_report"
SCHEMA_VERSION = 1
REPORT_DIR = DATA_DIR / "report" / REPORT_TYPE
PIPELINE_EVENTS_DIR = DATA_DIR / "pipeline_events"
ENTRY_STAGES = {
    "order_bundle_submitted",
    "order_leg_sent",
    "buy_order_submitted",
    "entry_order_submitted",
    "scalp_sim_buy_order_assumed_filled",
}
FORBIDDEN_USES = [
    "direct_buy_score_threshold_tightening",
    "intraday_threshold_mutation",
    "broker_guard_bypass",
    "stale_quote_submit_bypass",
    "order_guard_relaxation",
    "quantity_or_cap_change",
    "provider_route_change",
    "bot_restart",
    "real_execution_quality_approval",
]
TIGHT_STOP_PCT = float(getattr(TRADING_RULES, "SCALP_PRESET_HARD_STOP_PCT", -0.70) or -0.70)
MFE_TARGET_PCT = 0.30
SAMPLE_FLOOR = 20


def report_paths(target_date: str) -> tuple[Path, Path]:
    base = REPORT_DIR / f"{REPORT_TYPE}_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def _safe_float(value: Any, default: float | None = 0.0) -> float | None:
    if value in (None, "", "null", "none", "-", "not_available"):
        return default
    try:
        return float(str(value).replace("+", "").replace("%", ""))
    except (TypeError, ValueError):
        return default


def _is_present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str) and value.strip().lower() in {"", "null", "none", "-", "not_available"}:
        return False
    return True


def _first_present(event: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = event.get(key)
        if _is_present(value):
            return value
    return None


def _boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _parse_time(value: Any) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def _date_range(start_date: str, end_date: str) -> list[str]:
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()
    dates: list[str] = []
    current = start
    while current <= end:
        if is_krx_trading_day(current):
            dates.append(current.isoformat())
        current += timedelta(days=1)
    return dates


def _event_path(source_date: str) -> Path:
    return existing_or_gzip_path(PIPELINE_EVENTS_DIR / f"pipeline_events_{source_date}.jsonl")


def _iter_events(source_dates: list[str], missing: list[dict[str, str]]):
    for source_date in source_dates:
        path = _event_path(source_date)
        if not path.exists():
            missing.append({"date": source_date, "artifact": "pipeline_events", "path": str(path)})
            continue
        with open_text_auto(path) as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(event, dict):
                    continue
                fields = event.get("fields") if isinstance(event.get("fields"), dict) else {}
                yield source_date, {**event, **fields}


def _row_key(source_date: str, event: dict[str, Any]) -> str:
    sim_id = str(event.get("sim_record_id") or "").strip()
    if sim_id:
        return f"{source_date}:sim:{sim_id}"
    record_id = str(event.get("record_id") or event.get("recommendation_id") or event.get("runtime_record_id") or "").strip()
    stock_code = str(event.get("stock_code") or "").strip()
    if record_id:
        return f"{source_date}:real:{record_id}"
    if stock_code:
        return f"{source_date}:stock:{stock_code}"
    return ""


def _is_entry_event(event: dict[str, Any]) -> bool:
    stage = str(event.get("stage") or "")
    stage_lower = stage.lower()
    pipeline = str(event.get("pipeline") or "").strip().upper()
    side = str(event.get("side") or event.get("order_side") or event.get("trade_side") or "").strip().upper()
    action = str(event.get("ai_action") or event.get("action") or event.get("chosen_action") or "").strip().upper()
    if (
        "sell" in stage_lower
        or "exit" in stage_lower
        or side in {"SELL", "S", "매도"}
        or action.startswith("SELL")
        or action in {"EXIT", "STOP_LOSS", "TAKE_PROFIT"}
        or pipeline in {"EXIT_PIPELINE", "SELL_PIPELINE"}
    ):
        return False
    if stage in ENTRY_STAGES:
        return True
    if not _boolish(event.get("actual_order_submitted")):
        return False
    return "buy" in stage_lower or side in {"BUY", "B", "매수"} or action == "BUY" or pipeline == "ENTRY_PIPELINE"


def _score_band(score: float | None) -> str:
    if score is None:
        return "score_unknown"
    if score < 60:
        return "score_lt60"
    if score < 65:
        return "score60_64"
    if score < 70:
        return "score65_69"
    if score < 75:
        return "score70_74"
    return "score75_plus"


def _quote_age_bucket(age_ms: float | None) -> str:
    if age_ms is None:
        return "quote_age_unknown"
    if age_ms <= 300:
        return "quote_age_le300ms"
    if age_ms <= 1000:
        return "quote_age_301_1000ms"
    if age_ms <= 1500:
        return "quote_age_1001_1500ms"
    return "quote_age_gt1500ms"


def _micro_vwap_bucket(value: float | None) -> str:
    if value is None:
        return "micro_vwap_unknown"
    if value >= 10:
        return "micro_vwap_ge10bp"
    if value >= 0:
        return "micro_vwap_0_10bp"
    if value >= -10:
        return "micro_vwap_neg10_0bp"
    return "micro_vwap_lt_neg10bp"


def _pressure_bucket(value: float | None) -> str:
    if value is None:
        return "pressure_unknown"
    if value >= 85:
        return "pressure_ge85"
    if value >= 70:
        return "pressure_70_84"
    if value >= 55:
        return "pressure_55_69"
    return "pressure_lt55"


def _tick_accel_bucket(value: float | None) -> str:
    if value is None:
        return "tick_accel_unknown"
    if value >= 1.20:
        return "tick_accel_ge120"
    if value >= 1.05:
        return "tick_accel_105_119"
    if value >= 0.95:
        return "tick_accel_095_104"
    return "tick_accel_lt095"


def _entry_profile(event: dict[str, Any], source_date: str, key: str, event_time: datetime) -> dict[str, Any]:
    score = _safe_float(_first_present(event, "ai_score", "current_ai_score", "score_source_value"), None)
    buy_pressure = _safe_float(_first_present(event, "buy_pressure_10t", "buy_pressure"), None)
    tick_accel = _safe_float(_first_present(event, "tick_acceleration_ratio", "tick_accel"), None)
    micro_vwap = _safe_float(_first_present(event, "curr_vs_micro_vwap_bp", "micro_vwap_bp"), None)
    quote_age = _safe_float(event.get("quote_age_ms"), None)
    actual_order_submitted = _boolish(event.get("actual_order_submitted"))
    stage = str(event.get("stage") or "")
    row_authority = (
        "real_submitted_path_observation"
        if actual_order_submitted
        else "sim_assumed_fill_path_observation"
        if stage == "scalp_sim_buy_order_assumed_filled"
        else "source_only_entry_path_observation"
    )
    return {
        "key": key,
        "source_date": source_date,
        "entry_time": event_time,
        "stage": stage,
        "row_authority": row_authority,
        "stock_code": str(event.get("stock_code") or ""),
        "stock_name": str(event.get("stock_name") or ""),
        "score": score,
        "score_band": _score_band(score),
        "ai_action": str(event.get("ai_action") or event.get("action") or event.get("chosen_action") or "").upper(),
        "source_signature": str(event.get("source_signature") or ""),
        "scanner_promotion_reason": str(event.get("scanner_promotion_reason") or ""),
        "buy_pressure_10t": buy_pressure,
        "buy_pressure_bucket": _pressure_bucket(buy_pressure),
        "tick_acceleration_ratio": tick_accel,
        "tick_accel_bucket": _tick_accel_bucket(tick_accel),
        "curr_vs_micro_vwap_bp": micro_vwap,
        "micro_vwap_bucket": _micro_vwap_bucket(micro_vwap),
        "quote_age_ms": quote_age,
        "quote_age_bucket": _quote_age_bucket(quote_age),
        "actual_order_submitted": actual_order_submitted,
        "broker_order_forbidden": _boolish(event.get("broker_order_forbidden")),
    }


def _path_metrics(entry: dict[str, Any], series: list[tuple[datetime, float]], window_minutes: int) -> dict[str, Any]:
    end_time = entry["entry_time"] + timedelta(minutes=window_minutes)
    future = [(time, pnl) for time, pnl in series if entry["entry_time"] <= time <= end_time]
    if not future:
        return {
            "sample_present": False,
            "mfe_pct": 0.0,
            "mae_pct": 0.0,
            "final_pct": 0.0,
            "mfe_hit_before_tight_stop": False,
            "tight_stop_touched_before_mfe": False,
        }
    mfe_seen = False
    stop_first = False
    mfe_first = False
    for _, pnl in future:
        if pnl >= MFE_TARGET_PCT:
            mfe_seen = True
            mfe_first = True
            break
        if pnl <= TIGHT_STOP_PCT:
            stop_first = True
            break
    values = [pnl for _, pnl in future]
    return {
        "sample_present": True,
        "mfe_pct": round(max(values), 6),
        "mae_pct": round(min(values), 6),
        "final_pct": round(values[-1], 6),
        "mfe_hit_before_tight_stop": mfe_first,
        "tight_stop_touched_before_mfe": stop_first and not mfe_seen,
    }


def _bucket_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "sample_count": 0,
            "mfe_before_tight_stop_rate": 0.0,
            "tight_stop_first_rate": 0.0,
            "avg_mfe_10m_pct": 0.0,
            "avg_mae_10m_pct": 0.0,
        }
    return {
        "sample_count": len(rows),
        "mfe_before_tight_stop_rate": round(
            sum(1 for row in rows if row.get("mfe_hit_before_tight_stop_10m")) / len(rows),
            6,
        ),
        "tight_stop_first_rate": round(
            sum(1 for row in rows if row.get("tight_stop_touched_before_mfe_10m")) / len(rows),
            6,
        ),
        "avg_mfe_10m_pct": round(sum(float(row.get("mfe_10m_pct") or 0.0) for row in rows) / len(rows), 6),
        "avg_mae_10m_pct": round(sum(float(row.get("mae_10m_pct") or 0.0) for row in rows) / len(rows), 6),
    }


def _summaries(rows: list[dict[str, Any]], bucket_key: str) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get(bucket_key) or "unknown")].append(row)
    result = []
    for bucket, bucket_rows in grouped.items():
        summary = _bucket_summary(bucket_rows)
        result.append({"bucket": bucket, **summary})
    return sorted(result, key=lambda item: (item["sample_count"], item["mfe_before_tight_stop_rate"]), reverse=True)


def _top_companion_candidates(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    dimensions = [
        ("score_band", "buy_pressure_bucket"),
        ("score_band", "tick_accel_bucket"),
        ("score_band", "micro_vwap_bucket"),
        ("buy_pressure_bucket", "tick_accel_bucket"),
        ("tick_accel_bucket", "micro_vwap_bucket"),
    ]
    candidates: list[dict[str, Any]] = []
    for left, right in dimensions:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            grouped[f"{left}={row.get(left)}|{right}={row.get(right)}"].append(row)
        for key, bucket_rows in grouped.items():
            summary = _bucket_summary(bucket_rows)
            if summary["sample_count"] < SAMPLE_FLOOR:
                continue
            edge = summary["mfe_before_tight_stop_rate"] - summary["tight_stop_first_rate"]
            candidates.append(
                {
                    "companion_key": key,
                    "dimensions": [left, right],
                    **summary,
                    "tight_stop_survival_edge": round(edge, 6),
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "decision_authority": "source_only_tight_stop_entry_companion_observation",
                }
            )
    return sorted(
        candidates,
        key=lambda item: (
            item["tight_stop_survival_edge"],
            item["mfe_before_tight_stop_rate"],
            item["sample_count"],
        ),
        reverse=True,
    )[:10]


def _source_date_preflight_entry(source_date: str, preflight: dict[str, Any]) -> dict[str, Any]:
    return {
        "date": source_date,
        "status": preflight.get("status"),
        "tuning_input_allowed": preflight.get("tuning_input_allowed"),
        "allowed_runtime_apply": preflight.get("allowed_runtime_apply"),
        "source_quality_gate": preflight.get("source_quality_gate"),
        "blocked_reason": preflight.get("blocked_reason"),
        "hard_blocking_contract_gap_count": preflight.get("hard_blocking_contract_gap_count"),
        "hard_blocking_excluded_row_count": preflight.get("hard_blocking_excluded_row_count"),
        "raw_row_exclusion_applied": preflight.get("raw_row_exclusion_applied"),
        "artifact": preflight.get("artifact"),
    }


def _filter_source_quality_dates(source_dates: list[str]) -> tuple[list[str], list[dict[str, Any]], list[dict[str, Any]]]:
    usable_dates: list[str] = []
    passed_preflights: list[dict[str, Any]] = []
    blocked_preflights: list[dict[str, Any]] = []
    for source_date in source_dates:
        preflight = load_source_quality_preflight(source_date)
        entry = _source_date_preflight_entry(source_date, preflight)
        if source_quality_preflight_blocked(preflight):
            blocked_preflights.append(entry)
            continue
        usable_dates.append(source_date)
        passed_preflights.append(entry)
    return usable_dates, passed_preflights, blocked_preflights


def _build_rows(source_dates: list[str], missing: list[dict[str, str]]) -> list[dict[str, Any]]:
    entries: dict[str, dict[str, Any]] = {}
    series: dict[str, list[tuple[datetime, float]]] = defaultdict(list)
    for source_date, event in _iter_events(source_dates, missing):
        event_time = _parse_time(event.get("emitted_at"))
        if event_time is None:
            continue
        key = _row_key(source_date, event)
        if not key:
            continue
        pnl = _safe_float(event.get("profit_rate"), None)
        if pnl is not None:
            series[key].append((event_time, pnl))
        if _is_entry_event(event) and key not in entries:
            entries[key] = _entry_profile(event, source_date, key, event_time)
    rows: list[dict[str, Any]] = []
    for key, entry in entries.items():
        path = sorted(series.get(key, []), key=lambda item: item[0])
        metrics_3m = _path_metrics(entry, path, 3)
        metrics_5m = _path_metrics(entry, path, 5)
        metrics_10m = _path_metrics(entry, path, 10)
        if not metrics_10m["sample_present"]:
            continue
        rows.append(
            {
                **{k: v for k, v in entry.items() if k != "entry_time"},
                "entry_time": entry["entry_time"].isoformat(),
                "mfe_3m_pct": metrics_3m["mfe_pct"],
                "mae_3m_pct": metrics_3m["mae_pct"],
                "mfe_5m_pct": metrics_5m["mfe_pct"],
                "mae_5m_pct": metrics_5m["mae_pct"],
                "mfe_10m_pct": metrics_10m["mfe_pct"],
                "mae_10m_pct": metrics_10m["mae_pct"],
                "final_10m_pct": metrics_10m["final_pct"],
                "mfe_hit_before_tight_stop_10m": metrics_10m["mfe_hit_before_tight_stop"],
                "tight_stop_touched_before_mfe_10m": metrics_10m["tight_stop_touched_before_mfe"],
            }
        )
    return rows


def build_report(target_date: str, *, start_date: str | None = None, end_date: str | None = None) -> dict[str, Any]:
    target_date = str(target_date).strip()
    start = str(start_date or target_date).strip()
    end = str(end_date or target_date).strip()
    policy = clean_baseline_policy()
    clean_source_dates, excluded_dates = filter_allowed_dates(_date_range(start, end), policy)
    source_dates, passed_preflights, blocked_preflights = _filter_source_quality_dates(clean_source_dates)
    missing_artifacts: list[dict[str, str]] = []
    rows = _build_rows(source_dates, missing_artifacts)
    candidate_count = len(rows)
    source_quality_blocked = not source_dates or bool(missing_artifacts and not rows)
    source_quality_status = (
        "source_quality_blocked"
        if source_quality_blocked
        else "warning_missing_partial_input_and_source_quality_excluded"
        if missing_artifacts and blocked_preflights
        else "warning_source_quality_excluded"
        if blocked_preflights
        else "warning_missing_partial_input"
        if missing_artifacts
        else "pass"
    )
    companion_candidates = _top_companion_candidates(rows)
    summary = {
        "entry_path_sample_count": candidate_count,
        "tight_stop_pct": TIGHT_STOP_PCT,
        "mfe_target_pct": MFE_TARGET_PCT,
        "sample_floor": SAMPLE_FLOOR,
        "sample_floor_passed": candidate_count >= SAMPLE_FLOOR,
        "overall": _bucket_summary(rows),
        "top_companion_candidate_count": len(companion_candidates),
        "score_band": _summaries(rows, "score_band"),
        "buy_pressure_bucket": _summaries(rows, "buy_pressure_bucket"),
        "tick_accel_bucket": _summaries(rows, "tick_accel_bucket"),
        "micro_vwap_bucket": _summaries(rows, "micro_vwap_bucket"),
        "quote_age_bucket": _summaries(rows, "quote_age_bucket"),
        "stage_counts": dict(Counter(row.get("stage") for row in rows)),
        "row_authority_counts": dict(Counter(row.get("row_authority") for row in rows)),
    }
    report = {
        "schema_version": SCHEMA_VERSION,
        "report_type": REPORT_TYPE,
        "target_date": target_date,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "clean_baseline_policy": policy,
        "source_dates": source_dates,
        "requested_source_dates": clean_source_dates,
        "excluded_dates": excluded_dates,
        "source_paths": {"pipeline_events": str(PIPELINE_EVENTS_DIR)},
        "source_quality": {
            "status": source_quality_status,
            "missing_artifacts": missing_artifacts,
            "source_date_preflight": {
                "requested_count": len(clean_source_dates),
                "passed_count": len(passed_preflights),
                "blocked_count": len(blocked_preflights),
                "passed_dates": [item["date"] for item in passed_preflights],
                "blocked_dates": blocked_preflights,
            },
        },
        "metric_contract": {
            "metric_role": "diagnostic_win_rate",
            "decision_authority": "source_only_tight_stop_entry_companion_observation",
            "window_policy": f"{start}_to_{end}",
            "sample_floor": {"entry_path_rows": SAMPLE_FLOOR},
            "primary_decision_metric": "mfe_before_tight_stop_rate_minus_tight_stop_first_rate",
            "source_quality_gate": "pipeline_events_present_clean_baseline_and_postclose_source_quality_preflight",
            "forbidden_uses": FORBIDDEN_USES,
        },
        "summary": summary,
        "companion_candidates": companion_candidates,
        "entry_path_rows": rows[:500],
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "allowed_runtime_apply": False,
        "decision_authority": "source_only_tight_stop_entry_companion_observation",
        "forbidden_uses": FORBIDDEN_USES,
    }
    target_preflight = load_source_quality_preflight(target_date)
    return apply_source_quality_preflight_block(report, target_preflight)


def render_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    overall = summary.get("overall") if isinstance(summary.get("overall"), dict) else {}
    lines = [
        f"# Tight Stop Entry Companion Report - {report.get('target_date')}",
        "",
        f"- allowed_runtime_apply: `{report.get('allowed_runtime_apply')}`",
        "- runtime_effect: `false`",
        f"- entry_path_sample_count: `{summary.get('entry_path_sample_count')}`",
        f"- tight_stop_pct: `{summary.get('tight_stop_pct')}`",
        f"- mfe_target_pct: `{summary.get('mfe_target_pct')}`",
        f"- mfe_before_tight_stop_rate: `{overall.get('mfe_before_tight_stop_rate')}`",
        f"- tight_stop_first_rate: `{overall.get('tight_stop_first_rate')}`",
        f"- top_companion_candidate_count: `{summary.get('top_companion_candidate_count')}`",
        "",
        "## Top Companion Candidates",
        "",
        "```json",
        json.dumps(report.get("companion_candidates") or [], ensure_ascii=False, indent=2, default=str),
        "```",
    ]
    return "\n".join(lines) + "\n"


def write_report(report: dict[str, Any]) -> tuple[Path, Path]:
    json_path, md_path = report_paths(str(report.get("target_date") or "unknown"))
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, default=str), encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return json_path, md_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-date", required=True)
    parser.add_argument("--start-date")
    parser.add_argument("--end-date")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    report = build_report(args.target_date, start_date=args.start_date, end_date=args.end_date)
    if args.write:
        json_path, md_path = write_report(report)
        print(json.dumps({"json": str(json_path), "md": str(md_path)}, ensure_ascii=False))
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
