from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from src.utils.constants import DATA_DIR, TRADING_RULES

KST = timezone(timedelta(hours=9))
FAMILY = "rising_missed_first_touch_avgdown_decision_gate"
STAGE = "scale_in"
REPORT_TYPE = "rising_missed_first_touch_calibration"
INPUT_REPORT_DIR = DATA_DIR / "report" / "rising_missed_intraday_feedback"
OUTPUT_REPORT_DIR = DATA_DIR / "report" / REPORT_TYPE
CLEAN_BASELINE_DATE = "2026-06-04"
CLOSED_LABELS = {"first_touch_recovered_profit", "first_touch_loss_or_flat"}
FORBIDDEN_USES = [
    "intraday_threshold_mutation",
    "intraday_runtime_apply",
    "hard_safety_relaxation",
    "broker_guard_bypass",
    "order_guard_relaxation",
    "provider_route_change",
    "bot_restart",
    "real_execution_quality_approval",
]
TARGET_ENV_KEYS = [
    "SCALP_FIRST_TOUCH_AVGDOWN_MIN_AI_SUPPORT",
    "SCALP_FIRST_TOUCH_AVGDOWN_MIN_AI_MODERATE",
    "SCALP_FIRST_TOUCH_AVGDOWN_MIN_PRIOR_PEAK_PCT",
    "SCALP_FIRST_TOUCH_AVGDOWN_MAX_REPEATED_BLOCKERS_WITHOUT_SUPPORT",
    "SCALP_FIRST_TOUCH_AVGDOWN_LOW_AI_BLOCK",
    "SCALP_FIRST_TOUCH_AVGDOWN_MAX_SPREAD_BPS",
]


def _safe_float(value: Any, default: float = 0.0) -> float:
    if value in (None, "", "-"):
        return default
    try:
        return float(str(value).replace(",", "").replace("+", "").replace("%", ""))
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(_safe_float(value, float(default)))
    except (TypeError, ValueError):
        return default


def _default_output_paths(target_date: str) -> tuple[Path, Path]:
    return (
        OUTPUT_REPORT_DIR / f"{REPORT_TYPE}_{target_date}.json",
        OUTPUT_REPORT_DIR / f"{REPORT_TYPE}_{target_date}.md",
    )


def _feedback_report_path(target_date: str) -> Path:
    return INPUT_REPORT_DIR / f"rising_missed_intraday_feedback_{target_date}.json"


def _iter_feedback_report_paths(target_date: str) -> list[Path]:
    paths: list[Path] = []
    for path in sorted(INPUT_REPORT_DIR.glob("rising_missed_intraday_feedback_*.json")):
        date_part = path.stem.removeprefix("rising_missed_intraday_feedback_")
        if CLEAN_BASELINE_DATE <= date_part <= target_date:
            paths.append(path)
    explicit = _feedback_report_path(target_date)
    if explicit.exists() and explicit not in paths:
        paths.append(explicit)
    return paths


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _current_values() -> dict[str, Any]:
    return {
        "min_ai_support": float(TRADING_RULES.SCALP_FIRST_TOUCH_AVGDOWN_MIN_AI_SUPPORT),
        "min_ai_moderate": float(
            TRADING_RULES.SCALP_FIRST_TOUCH_AVGDOWN_MIN_AI_MODERATE
        ),
        "min_prior_peak_pct": float(
            TRADING_RULES.SCALP_FIRST_TOUCH_AVGDOWN_MIN_PRIOR_PEAK_PCT
        ),
        "max_repeated_blockers_without_support": int(
            TRADING_RULES.SCALP_FIRST_TOUCH_AVGDOWN_MAX_REPEATED_BLOCKERS_WITHOUT_SUPPORT
        ),
        "low_ai_block": float(TRADING_RULES.SCALP_FIRST_TOUCH_AVGDOWN_LOW_AI_BLOCK),
        "max_spread_bps": float(TRADING_RULES.SCALP_FIRST_TOUCH_AVGDOWN_MAX_SPREAD_BPS),
    }


def _closed_first_touch_rows(reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for report in reports:
        for row in report.get("first_touch_regression_rows") or []:
            if not isinstance(row, dict):
                continue
            if str(row.get("first_touch_regression_label") or "") not in CLOSED_LABELS:
                continue
            rows.append(row)
    return rows


def _provenance_present(rows: list[dict[str, Any]]) -> bool:
    return bool(rows) and all(
        "actual_order_submitted" in row
        and "broker_order_forbidden" in row
        and "runtime_effect" in row
        and "decision_authority" in row
        and "forbidden_uses" in row
        for row in rows
    )


def _row_rates(rows: list[dict[str, Any]]) -> dict[str, Any]:
    sample_count = len(rows)
    recovered = sum(
        1
        for row in rows
        if row.get("first_touch_regression_label") == "first_touch_recovered_profit"
    )
    loss_or_flat = sum(
        1
        for row in rows
        if row.get("first_touch_regression_label") == "first_touch_loss_or_flat"
    )
    label_counts = Counter(
        str(row.get("first_touch_regression_label") or "unknown") for row in rows
    )
    return {
        "sample_count": sample_count,
        "recovered_count": recovered,
        "loss_or_flat_count": loss_or_flat,
        "recovered_rate": recovered / sample_count if sample_count else 0.0,
        "loss_or_flat_rate": loss_or_flat / sample_count if sample_count else 0.0,
        "label_counts": [
            {"label": key, "count": value} for key, value in label_counts.most_common()
        ],
    }


def _one_step_candidate_values(
    current: dict[str, Any], rates: dict[str, Any]
) -> tuple[str, dict[str, Any], str]:
    recommended = dict(current)
    loss_rate = _safe_float(rates.get("loss_or_flat_rate"))
    recovered_rate = _safe_float(rates.get("recovered_rate"))
    if loss_rate >= 0.60:
        recommended["min_ai_moderate"] = min(
            float(current["min_ai_moderate"]) + 5.0, 70.0
        )
        recommended["max_repeated_blockers_without_support"] = max(
            int(current["max_repeated_blockers_without_support"]) - 1,
            5,
        )
        recommended["min_prior_peak_pct"] = min(
            float(current["min_prior_peak_pct"]) + 0.10, 0.60
        )
        recommended["low_ai_block"] = min(float(current["low_ai_block"]) + 5.0, 60.0)
        recommended["max_spread_bps"] = max(
            float(current["max_spread_bps"]) - 10.0, 40.0
        )
        if loss_rate >= 0.75:
            recommended["min_ai_support"] = min(
                float(current["min_ai_support"]) + 5.0, 80.0
            )
        return "adjust_up", recommended, "loss_cluster_tighten_one_step"
    if recovered_rate >= 0.65:
        recommended["min_ai_moderate"] = max(
            float(current["min_ai_moderate"]) - 5.0, 55.0
        )
        recommended["max_repeated_blockers_without_support"] = min(
            int(current["max_repeated_blockers_without_support"]) + 1,
            10,
        )
        recommended["min_prior_peak_pct"] = max(
            float(current["min_prior_peak_pct"]) - 0.10, 0.10
        )
        recommended["max_spread_bps"] = min(
            float(current["max_spread_bps"]) + 10.0, 100.0
        )
        return "adjust_down", recommended, "recovery_cluster_loosen_one_step"
    return "hold", recommended, "mixed_cluster_hold"


def _calibration_candidate(
    *,
    target_date: str,
    reports: list[dict[str, Any]],
    source_paths: list[Path],
) -> dict[str, Any]:
    rows = _closed_first_touch_rows(reports)
    rates = _row_rates(rows)
    source_quality_pass = bool(reports) and all(
        ((report.get("source_quality") or {}).get("status") == "pass")
        for report in reports
    )
    provenance_present = _provenance_present(rows)
    source_contract_pass = bool(source_quality_pass and provenance_present)
    sample_floor_met = int(rates["sample_count"]) >= 10
    current = _current_values()
    blockers: list[str] = []
    if not sample_floor_met:
        blockers.append("rolling_closed_first_touch_rows_lt_10")
    if not source_quality_pass:
        blockers.append("source_quality_not_pass")
    if not provenance_present:
        blockers.append("order_provenance_missing")

    if blockers:
        state = "hold_sample"
        recommended = dict(current)
        reason = ",".join(blockers)
        allowed = False
    else:
        state, recommended, reason = _one_step_candidate_values(current, rates)
        allowed = state in {"adjust_up", "adjust_down"}

    return {
        "family": FAMILY,
        "stage": STAGE,
        "priority": 38,
        "family_type": "bounded_tunable_scale_in_first_touch_gate",
        "calibration_state": state,
        "calibration_reason": reason,
        "threshold_version": f"{FAMILY}:{target_date}:v1",
        "sample_count": rates["sample_count"],
        "sample_floor": 10,
        "allowed_runtime_apply": allowed,
        "safety_revert_required": False,
        "source_quality_gate": (
            "pass" if source_contract_pass else "source_quality_blocked"
        ),
        "source_quality_status": "pass" if source_contract_pass else "blocked",
        "source_quality_blocked": (
            None
            if source_contract_pass
            else ",".join(blockers) or "source_quality_or_provenance_not_pass"
        ),
        "current_values": current,
        "recommended_values": recommended,
        "target_env_keys": TARGET_ENV_KEYS if allowed else [],
        "source_metrics": {
            **rates,
            "source_quality_pass": source_quality_pass,
            "provenance_present": provenance_present,
            "recommended_action": state,
            "recommended_action_reason": reason,
        },
        "source_reports": [str(path) for path in source_paths],
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "decision_authority": "postclose_calibration_candidate_preopen_only",
        "forbidden_uses": FORBIDDEN_USES,
    }


def build_report(
    target_date: str,
    *,
    input_paths: list[Path] | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    generated_at = generated_at or datetime.now(KST).isoformat(timespec="seconds")
    paths = (
        input_paths
        if input_paths is not None
        else _iter_feedback_report_paths(target_date)
    )
    reports = [_load_json(path) for path in paths if path.exists()]
    candidate = _calibration_candidate(
        target_date=target_date, reports=reports, source_paths=paths
    )
    return {
        "schema_version": 1,
        "report_type": REPORT_TYPE,
        "target_date": target_date,
        "generated_at": generated_at,
        "family": FAMILY,
        "stage": STAGE,
        "runtime_effect": False,
        "allowed_runtime_apply": bool(candidate.get("allowed_runtime_apply")),
        "decision_authority": "postclose_calibration_candidate_preopen_only",
        "forbidden_uses": FORBIDDEN_USES,
        "metric_contract": {
            "metric_role": "bounded_tunable_calibration_candidate",
            "decision_authority": "postclose_calibration_candidate_preopen_only",
            "window_policy": "rolling_clean_baseline_first_touch_closed_rows",
            "sample_floor": "rolling_closed_first_touch_rows_ge_10",
            "primary_decision_metric": "loss_or_flat_rate_or_recovered_rate_cluster",
            "source_quality_gate": "all_consumed_intraday_feedback_reports_source_quality_pass_and_provenance_present",
            "forbidden_uses": FORBIDDEN_USES,
        },
        "source_quality": {
            "status": (
                "pass"
                if candidate["source_metrics"]["source_quality_pass"]
                else "blocked"
            ),
            "input_report_count": len(reports),
            "input_paths": [str(path) for path in paths],
            "provenance_present": candidate["source_metrics"]["provenance_present"],
        },
        "calibration_candidates": [candidate],
        "calibration_candidate": candidate,
        "summary": {
            "calibration_state": candidate["calibration_state"],
            "allowed_runtime_apply": candidate["allowed_runtime_apply"],
            "sample_count": candidate["sample_count"],
            "recovered_rate": candidate["source_metrics"]["recovered_rate"],
            "loss_or_flat_rate": candidate["source_metrics"]["loss_or_flat_rate"],
            "calibration_reason": candidate["calibration_reason"],
        },
    }


def write_outputs(
    report: dict[str, Any], *, output_json: Path, output_md: Path
) -> None:
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    candidate = (
        report.get("calibration_candidate")
        if isinstance(report.get("calibration_candidate"), dict)
        else {}
    )
    lines = [
        f"# {report.get('target_date')} Rising Missed First Touch Calibration",
        "",
        f"- generated_at: {report.get('generated_at')}",
        "- family: rising_missed_first_touch_avgdown_decision_gate",
        "- stage: scale_in",
        "- decision_authority: postclose_calibration_candidate_preopen_only",
        "- runtime_effect: false",
        f"- allowed_runtime_apply: {str(summary.get('allowed_runtime_apply')).lower()}",
        "- forbidden_uses: " + ", ".join(FORBIDDEN_USES),
        "",
        "## Summary",
        "",
        f"- calibration_state: {summary.get('calibration_state')}",
        f"- calibration_reason: {summary.get('calibration_reason')}",
        f"- sample_count: {summary.get('sample_count')}",
        f"- recovered_rate: {_safe_float(summary.get('recovered_rate')):.2f}",
        f"- loss_or_flat_rate: {_safe_float(summary.get('loss_or_flat_rate')):.2f}",
        "",
        "## Candidate",
        "",
        f"- target_env_keys: {', '.join(candidate.get('target_env_keys') or []) or '-'}",
        f"- current_values: {json.dumps(candidate.get('current_values') or {}, sort_keys=True)}",
        f"- recommended_values: {json.dumps(candidate.get('recommended_values') or {}, sort_keys=True)}",
    ]
    output_md.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build rising missed first-touch calibration candidate."
    )
    parser.add_argument("--target-date", default=datetime.now(KST).strftime("%Y-%m-%d"))
    parser.add_argument("--input-json", action="append", type=Path)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--generated-at")
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args(argv)
    report = build_report(
        args.target_date, input_paths=args.input_json, generated_at=args.generated_at
    )
    default_json, default_md = _default_output_paths(args.target_date)
    output_json = args.output_json or default_json
    output_md = args.output_md or default_md
    write_outputs(report, output_json=output_json, output_md=output_md)
    if args.print_summary:
        print(
            json.dumps(
                {
                    "output_json": str(output_json),
                    "output_md": str(output_md),
                    **report["summary"],
                },
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
