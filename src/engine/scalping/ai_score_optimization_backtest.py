"""Aggregate AI score/action optimization evidence into bounded runtime candidates."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from src.engine.automation.source_quality_clean_baseline import (
    clean_baseline_policy,
    filter_allowed_dates,
)
from src.utils.constants import DATA_DIR
from src.utils.jsonl_io import existing_or_gzip_path, open_text_auto
from src.utils.market_day import is_krx_trading_day


REPORT_TYPE = "ai_score_optimization_backtest"
SCHEMA_VERSION = 1
REPORT_DIR = DATA_DIR / "report" / REPORT_TYPE
ENTRY_AI_GATE_BACKTEST_DIR = DATA_DIR / "report" / "entry_ai_gate_backtest"
RISING_MISSED_FIRST_TOUCH_CALIBRATION_DIR = (
    DATA_DIR / "report" / "rising_missed_first_touch_calibration"
)
SCALPING_PYRAMID_QUALITY_CALIBRATION_DIR = (
    DATA_DIR / "report" / "scalping_pyramid_quality_calibration"
)
PIPELINE_EVENTS_DIR = DATA_DIR / "pipeline_events"
POST_SELL_DIR = DATA_DIR / "post_sell"
LIFECYCLE_DECISION_MATRIX_DIR = DATA_DIR / "report" / "lifecycle_decision_matrix"

ENTRY_OPPORTUNITY_RECHECK_FAMILY = "entry_opportunity_recheck_runtime"
SCORE65_74_RECOVERY_PROBE_FAMILY = "score65_74_recovery_probe"
FIRST_TOUCH_FAMILY = "rising_missed_first_touch_avgdown_decision_gate"
PYRAMID_FAMILY = "scalping_pyramid_quality_gate"

KNOWN_AUTO_APPLY_FAMILIES = {
    ENTRY_OPPORTUNITY_RECHECK_FAMILY,
    SCORE65_74_RECOVERY_PROBE_FAMILY,
    FIRST_TOUCH_FAMILY,
    PYRAMID_FAMILY,
    "soft_stop_whipsaw_confirmation",
    "profit_stagnation_exit_runtime",
}

FORBIDDEN_USES = [
    "intraday_threshold_mutation",
    "provider_route_change",
    "bot_restart",
    "broker_guard_bypass",
    "stale_quote_submit_bypass",
    "quantity_or_cap_change",
    "hard_safety_bypass",
]

ENTRY_RECHECK_TARGET_ENV_KEYS = [
    "ENTRY_OPPORTUNITY_RECHECK_ENABLED",
    "ENTRY_OPPORTUNITY_RECHECK_MIN_AI_SCORE",
    "ENTRY_OPPORTUNITY_RECHECK_MAX_AI_SCORE",
]
PIPELINE_SURFACE_COUNT_MAX_DATES = 5
PIPELINE_SURFACE_COUNT_MAX_LINES_PER_DATE = 20_000


def report_paths(target_date: str) -> tuple[Path, Path]:
    base = REPORT_DIR / f"{REPORT_TYPE}_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, "", "null", "none", "-"):
            return default
        return int(float(value))
    except Exception:
        return default


def _safe_float(value: Any, default: float | None = 0.0) -> float | None:
    try:
        if value in (None, "", "null", "none", "-"):
            return default
        return float(value)
    except Exception:
        return default


def _safe_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return value != 0
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on", "pass"}


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


def _load_json(path: Path) -> dict[str, Any]:
    actual = existing_or_gzip_path(path)
    if not actual.exists():
        return {}
    try:
        with open_text_auto(actual) as handle:
            payload = json.loads(handle.read())
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _latest_existing_report(base_dir: Path, report_type: str, source_dates: list[str]) -> tuple[dict[str, Any], Path | None]:
    for source_date in reversed(source_dates):
        path = base_dir / f"{report_type}_{source_date}.json"
        payload = _load_json(path)
        if payload:
            return payload, path
    return {}, None


def _candidate_list(payload: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = payload.get("calibration_candidates")
    if not isinstance(candidates, list):
        candidate = payload.get("calibration_candidate")
        candidates = [candidate] if isinstance(candidate, dict) else []
    return [item for item in candidates if isinstance(item, dict)]


def _source_quality_pass(candidate: dict[str, Any]) -> bool:
    gate = str(candidate.get("source_quality_gate") or candidate.get("source_quality_status") or "").lower()
    if gate and gate not in {"pass", "ok", "clean", "source_quality_pass"}:
        return False
    if candidate.get("source_quality_blocked") or candidate.get("source_quality_blocker"):
        return False
    blockers = candidate.get("source_quality_blockers")
    return not (isinstance(blockers, list) and blockers)


def _sample_floor_passed(candidate: dict[str, Any]) -> bool:
    if "sample_floor_passed" in candidate:
        return _safe_bool(candidate.get("sample_floor_passed"))
    if str(candidate.get("calibration_state") or "") == "hold_sample":
        return False
    return bool(candidate.get("allowed_runtime_apply"))


def _with_required_candidate_fields(
    candidate: dict[str, Any],
    *,
    source_report_type: str,
    source_path: Path | None,
    default_stage: str,
) -> dict[str, Any]:
    family = str(candidate.get("family") or "")
    normalized = dict(candidate)
    normalized.setdefault("stage", default_stage)
    normalized.setdefault("target_env_keys", [])
    normalized.setdefault("current_values", {})
    normalized.setdefault("recommended_values", {})
    normalized.setdefault("same_stage_owner_stage", normalized.get("stage"))
    normalized.setdefault("forbidden_uses", FORBIDDEN_USES)
    normalized.setdefault("sample_floor_passed", _sample_floor_passed(candidate))
    normalized.setdefault("source_quality_gate", "pass" if _source_quality_pass(candidate) else "blocked")
    normalized["ai_score_optimization_source_report_type"] = source_report_type
    normalized["ai_score_optimization_source_path"] = str(source_path) if source_path else None
    if family not in KNOWN_AUTO_APPLY_FAMILIES:
        normalized["allowed_runtime_apply"] = False
        normalized.setdefault("apply_block_reason", "blocked_no_env_mapping")
    elif not _safe_bool(normalized.get("allowed_runtime_apply")):
        normalized["allowed_runtime_apply"] = False
    elif not _sample_floor_passed(normalized):
        normalized["allowed_runtime_apply"] = False
        normalized.setdefault("apply_block_reason", "hold_sample")
    elif not _source_quality_pass(normalized):
        normalized["allowed_runtime_apply"] = False
        normalized.setdefault("apply_block_reason", "source_quality_blocked")
    elif not normalized.get("target_env_keys"):
        normalized["allowed_runtime_apply"] = False
        normalized.setdefault("apply_block_reason", "blocked_no_env_mapping")
    return normalized


def _entry_recheck_candidate(entry_report: dict[str, Any], source_path: Path | None) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    diagnostics: list[dict[str, Any]] = []
    calibration: list[dict[str, Any]] = []
    best_apply = entry_report.get("best_apply_candidate")
    if isinstance(best_apply, dict) and best_apply:
        policy = str(best_apply.get("policy") or "")
        threshold = _safe_int(best_apply.get("threshold"), 0)
        realized = best_apply.get("realized") if isinstance(best_apply.get("realized"), dict) else {}
        counterfactual = best_apply.get("counterfactual") if isinstance(best_apply.get("counterfactual"), dict) else {}
        if policy == "supported_wait_recovery" and threshold:
            calibration.append(
                {
                    "family": ENTRY_OPPORTUNITY_RECHECK_FAMILY,
                    "stage": "entry",
                    "priority": 42,
                    "threshold_version": f"entry_opportunity_recheck_runtime:{entry_report.get('target_date')}:{threshold}",
                    "calibration_state": "adjust_down",
                    "calibration_reason": "entry_ai_gate_backtest_supported_wait_recovery_positive_ev",
                    "target_env_keys": ENTRY_RECHECK_TARGET_ENV_KEYS,
                    "current_values": {
                        "enabled": False,
                        "min_ai_score": 75,
                        "max_ai_score": 100,
                    },
                    "recommended_values": {
                        "enabled": True,
                        "min_ai_score": threshold,
                        "max_ai_score": 74,
                    },
                    "source_metrics": {
                        "policy": policy,
                        "realized": realized,
                        "counterfactual": counterfactual,
                    },
                    "sample_floor_passed": _safe_bool(best_apply.get("sample_floor_passed")),
                    "source_quality_gate": "pass",
                    "allowed_runtime_apply": _safe_bool(best_apply.get("allowed_runtime_apply")),
                    "forbidden_uses": FORBIDDEN_USES + ["broad_buy_score_threshold_relaxation"],
                }
            )
    for key in ("best_diagnostic_score_only_candidate", "best_positive_realized_diagnostic_candidate"):
        item = entry_report.get(key)
        if isinstance(item, dict) and item:
            diagnostics.append(
                {
                    "surface": "entry",
                    "diagnostic_key": key,
                    "policy": item.get("policy"),
                    "threshold": item.get("threshold"),
                    "realized": item.get("realized"),
                    "counterfactual": item.get("counterfactual"),
                    "sample_floor_passed": _safe_bool(item.get("sample_floor_passed")),
                    "allowed_runtime_apply": False,
                    "apply_block_reason": "diagnostic_score_only",
                    "source_path": str(source_path) if source_path else None,
                }
            )
    return calibration, diagnostics


def _copy_calibration_candidates(
    payload: dict[str, Any],
    *,
    source_report_type: str,
    source_path: Path | None,
    default_stage: str,
) -> list[dict[str, Any]]:
    return [
        _with_required_candidate_fields(
            item,
            source_report_type=source_report_type,
            source_path=source_path,
            default_stage=default_stage,
        )
        for item in _candidate_list(payload)
    ]


def _pipeline_surface_counts(source_dates: list[str]) -> dict[str, Any]:
    counts: dict[str, int] = {
        "holding_score_v2": 0,
        "holding_flow": 0,
        "entry_price": 0,
        "avg_down": 0,
        "reversal_add": 0,
        "pyramid": 0,
        "exit": 0,
    }
    scan_meta = {
        "scanned_dates": [],
        "max_dates": PIPELINE_SURFACE_COUNT_MAX_DATES,
        "max_lines_per_date": PIPELINE_SURFACE_COUNT_MAX_LINES_PER_DATE,
        "truncated": False,
    }
    for source_date in source_dates[-PIPELINE_SURFACE_COUNT_MAX_DATES:]:
        path = existing_or_gzip_path(PIPELINE_EVENTS_DIR / f"pipeline_events_{source_date}.jsonl")
        if not path.exists():
            continue
        try:
            scanned_lines = 0
            with open_text_auto(path) as handle:
                for line in handle:
                    scanned_lines += 1
                    if scanned_lines > PIPELINE_SURFACE_COUNT_MAX_LINES_PER_DATE:
                        scan_meta["truncated"] = True
                        break
                    if not line.strip():
                        continue
                    text = line.lower()
                    if "holding_score_v2" in text:
                        counts["holding_score_v2"] += 1
                    if "holding_flow" in text:
                        counts["holding_flow"] += 1
                    if "entry_price" in text:
                        counts["entry_price"] += 1
                    if "avg_down" in text:
                        counts["avg_down"] += 1
                    if "reversal_add" in text:
                        counts["reversal_add"] += 1
                    if "pyramid" in text:
                        counts["pyramid"] += 1
                    if "exit" in text or "sell" in text:
                        counts["exit"] += 1
            scan_meta["scanned_dates"].append({"date": source_date, "lines": scanned_lines, "path": str(path)})
        except Exception:
            continue
    counts["_scan_meta"] = scan_meta
    return counts


def build_report(target_date: str, *, start_date: str | None = None, end_date: str | None = None) -> dict[str, Any]:
    target_date = str(target_date).strip()
    start = str(start_date or target_date).strip()
    end = str(end_date or target_date).strip()
    policy = clean_baseline_policy()
    source_dates, excluded_dates = filter_allowed_dates(_date_range(start, end), policy)
    source_paths: dict[str, Any] = {}
    calibration_candidates: list[dict[str, Any]] = []
    diagnostic_only_candidates: list[dict[str, Any]] = []

    entry_report, entry_path = _latest_existing_report(
        ENTRY_AI_GATE_BACKTEST_DIR,
        "entry_ai_gate_backtest",
        source_dates,
    )
    if entry_path:
        source_paths["entry_ai_gate_backtest"] = str(entry_path)
        entry_candidates, entry_diagnostics = _entry_recheck_candidate(entry_report, entry_path)
        calibration_candidates.extend(
            _with_required_candidate_fields(
                item,
                source_report_type="entry_ai_gate_backtest",
                source_path=entry_path,
                default_stage="entry",
            )
            for item in entry_candidates
        )
        diagnostic_only_candidates.extend(entry_diagnostics)

    first_touch_report, first_touch_path = _latest_existing_report(
        RISING_MISSED_FIRST_TOUCH_CALIBRATION_DIR,
        "rising_missed_first_touch_calibration",
        source_dates,
    )
    if first_touch_path:
        source_paths["rising_missed_first_touch_calibration"] = str(first_touch_path)
        calibration_candidates.extend(
            _copy_calibration_candidates(
                first_touch_report,
                source_report_type="rising_missed_first_touch_calibration",
                source_path=first_touch_path,
                default_stage="scale_in",
            )
        )

    pyramid_report, pyramid_path = _latest_existing_report(
        SCALPING_PYRAMID_QUALITY_CALIBRATION_DIR,
        "scalping_pyramid_quality_calibration",
        source_dates,
    )
    if pyramid_path:
        source_paths["scalping_pyramid_quality_calibration"] = str(pyramid_path)
        calibration_candidates.extend(
            _copy_calibration_candidates(
                pyramid_report,
                source_report_type="scalping_pyramid_quality_calibration",
                source_path=pyramid_path,
                default_stage="scale_in",
            )
        )

    surface_counts = _pipeline_surface_counts(source_dates)
    backtest_coverage_status = {
        "analyze_target_entry": {
            "status": "backtested",
            "producer": "entry_ai_gate_backtest",
            "auto_apply_family_scope": [ENTRY_OPPORTUNITY_RECHECK_FAMILY, SCORE65_74_RECOVERY_PROBE_FAMILY],
            "broad_buy_score_threshold_apply": False,
        },
        "entry_price": {
            "status": "source_only_instrumentation_gap",
            "producer": None,
            "auto_apply_family_scope": [],
            "reason": "entry_price action/confidence outcomes are inventoried but no fill/slippage/cancel/requote EV sweep is implemented in v1",
        },
        "holding_score_v2": {
            "status": "source_only_instrumentation_gap",
            "producer": None,
            "auto_apply_family_scope": [],
            "reason": "holding score role-gated provenance is inventoried but no holding-state EV replay sweep is implemented in v1",
        },
        "holding_flow": {
            "status": "source_only_instrumentation_gap",
            "producer": None,
            "auto_apply_family_scope": [],
            "reason": "holding_flow override/recheck outcomes are inventoried but no mapped bounded calibration candidate is implemented in v1",
        },
        "first_touch_avg_down": {
            "status": "backtested_if_source_present",
            "producer": "rising_missed_first_touch_calibration",
            "auto_apply_family_scope": [FIRST_TOUCH_FAMILY],
        },
        "pyramid": {
            "status": "backtested_if_source_present",
            "producer": "scalping_pyramid_quality_calibration",
            "auto_apply_family_scope": [PYRAMID_FAMILY],
        },
        "general_avg_down_reversal_add": {
            "status": "source_only_instrumentation_gap",
            "producer": None,
            "auto_apply_family_scope": [],
            "reason": "REVERSAL_ADD/AVG_DOWN env mapping and sample-floor producer are not confirmed in v1",
        },
        "overnight_swing_score": {
            "status": "sim_source_only",
            "producer": None,
            "auto_apply_family_scope": [],
            "reason": "v1 forbids real env candidates for overnight/swing score surfaces",
        },
    }
    source_only_surfaces = [
        {
            "surface": "entry_price",
            "stage": "entry_price",
            "status": "source_only",
            "observed_event_count": surface_counts.get("entry_price", 0),
            "allowed_runtime_apply": False,
            "apply_block_reason": "provider_route_and_price_resolver_guard_out_of_scope_v1",
        },
        {
            "surface": "holding_exit",
            "stage": "holding",
            "status": "source_only",
            "observed_event_count": surface_counts.get("holding_score_v2", 0) + surface_counts.get("holding_flow", 0),
            "allowed_runtime_apply": False,
            "apply_block_reason": "only_existing_holding_exit_family_mapping_can_apply",
        },
        {
            "surface": "general_avg_down_reversal_add",
            "stage": "scale_in",
            "status": "source_only",
            "observed_event_count": surface_counts.get("avg_down", 0) + surface_counts.get("reversal_add", 0),
            "allowed_runtime_apply": False,
            "apply_block_reason": "missing_confirmed_reversal_add_env_mapping_or_floor",
        },
        {
            "surface": "overnight_swing_score",
            "stage": "overnight_swing",
            "status": "sim_source_only",
            "observed_event_count": 0,
            "allowed_runtime_apply": False,
            "apply_block_reason": "v1_no_real_env_candidate",
        },
    ]

    allowed_candidates = [item for item in calibration_candidates if _safe_bool(item.get("allowed_runtime_apply"))]
    blocked_by_reason: dict[str, int] = {}
    for item in calibration_candidates:
        if _safe_bool(item.get("allowed_runtime_apply")):
            continue
        reason = str(item.get("apply_block_reason") or item.get("calibration_state") or "runtime_apply_not_allowed")
        blocked_by_reason[reason] = blocked_by_reason.get(reason, 0) + 1

    return {
        "schema_version": SCHEMA_VERSION,
        "report_type": REPORT_TYPE,
        "target_date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "clean_baseline_policy": policy,
        "source_dates": source_dates,
        "excluded_dates": excluded_dates,
        "source_paths": {
            **source_paths,
            "pipeline_events": str(PIPELINE_EVENTS_DIR),
            "post_sell": str(POST_SELL_DIR),
            "lifecycle_decision_matrix": str(LIFECYCLE_DECISION_MATRIX_DIR),
        },
        "metric_contract": {
            "metric_role": "primary_ev",
            "decision_authority": "postclose_ai_score_optimization_candidate",
            "window_policy": f"{start}_to_{end}",
            "sample_floor": "surface_specific_existing_calibration_floor",
            "primary_decision_metric": "source_quality_adjusted_ev_pct",
            "source_quality_gate": "clean_baseline_and_surface_source_quality_gate",
            "forbidden_uses": FORBIDDEN_USES,
        },
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "allowed_runtime_apply": bool(allowed_candidates),
        "calibration_state": "candidate_ready" if allowed_candidates else "hold_sample",
        "summary": {
            "calibration_candidate_count": len(calibration_candidates),
            "allowed_runtime_apply_candidate_count": len(allowed_candidates),
            "diagnostic_only_candidate_count": len(diagnostic_only_candidates),
            "blocked_by_reason": blocked_by_reason,
            "surface_event_counts": surface_counts,
            "backtest_coverage_status": backtest_coverage_status,
        },
        "surface_summaries": {
            "entry": (entry_report.get("summary") if isinstance(entry_report.get("summary"), dict) else {}),
            "first_touch_avg_down": {
                "status": "loaded" if first_touch_path else "missing",
                "path": str(first_touch_path) if first_touch_path else None,
            },
            "pyramid": {
                "status": "loaded" if pyramid_path else "missing",
                "path": str(pyramid_path) if pyramid_path else None,
            },
            "source_only_surfaces": source_only_surfaces,
            "backtest_coverage_status": backtest_coverage_status,
        },
        "calibration_candidates": calibration_candidates,
        "diagnostic_only_candidates": diagnostic_only_candidates,
        "forbidden_uses": FORBIDDEN_USES,
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    lines = [
        f"# AI Score Optimization Backtest - {report.get('target_date')}",
        "",
        f"- calibration_state: `{report.get('calibration_state')}`",
        f"- allowed_runtime_apply: `{report.get('allowed_runtime_apply')}`",
        f"- calibration_candidate_count: `{summary.get('calibration_candidate_count')}`",
        f"- allowed_runtime_apply_candidate_count: `{summary.get('allowed_runtime_apply_candidate_count')}`",
        f"- diagnostic_only_candidate_count: `{summary.get('diagnostic_only_candidate_count')}`",
        "",
        "## Blocked Reasons",
        "",
    ]
    for reason, count in sorted((summary.get("blocked_by_reason") or {}).items()):
        lines.append(f"- `{reason}`: `{count}`")
    lines.extend(["", "## Calibration Candidates", "", "```json"])
    lines.append(json.dumps(report.get("calibration_candidates") or [], ensure_ascii=False, indent=2, default=str))
    lines.extend(["```", ""])
    return "\n".join(lines)


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
