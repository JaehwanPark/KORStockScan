"""Run the full-day V2.14 entry paired replay as an offline bounded batch."""

from __future__ import annotations

import argparse
import io
import json
import tempfile
import time
from contextlib import redirect_stdout
from datetime import date, datetime, time as dt_time
from pathlib import Path
from typing import Any

from src.engine.ai_prompt_contracts import (
    DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_PROMPT_VERSION,
)
from src.engine.scalping import ai_decision_quality as quality
from src.engine.scalping.entry_setup_live_policy import publish_live_candidate

BATCH_SCHEMA = "ai_entry_setup_paired_replay_batch_v1"
BATCH_DIR = quality.DATA_DIR / "report" / "ai_entry_setup_paired_replay_batch"
DEFAULT_COHORTS = (
    ("KRX", "KRX_REGULAR"),
    ("NXT", "NXT_AFTERMARKET"),
)
FULL_DAY_MATURITY_TIME_KST = dt_time(21, 0)

OFFLINE_BATCH_CONTRACT = {
    "metric_role": "ai_entry_setup_paired_replay_batch_observation",
    "decision_authority": "offline_replay_and_attribution_only",
    "window_policy": "full_day_plus_60m_same_venue_session",
    "sample_floor": "one_exact_payload_updates_cumulative_observation",
    "primary_decision_metric": "candidate_probe_cost_adjusted_ev_pct",
    "source_quality_gate": "exact_payload_fresh_same_route_mature_window",
    "runtime_effect": False,
    "allowed_runtime_apply": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
    "forbidden_uses": [
        "direct_live_prompt_or_threshold_apply",
        "provider_model_price_quantity_or_cap_change",
        "broker_or_safety_guard_bypass",
        "bot_restart",
    ],
}


def batch_status_path(target_date: str) -> Path:
    return BATCH_DIR / f"ai_entry_setup_paired_replay_batch_{target_date}.json"


def predecessor_status_path(target_date: str) -> Path:
    return (
        quality.DATA_DIR
        / "report"
        / "threshold_cycle_postclose_status"
        / f"threshold_cycle_postclose_{target_date}.status.json"
    )


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with open(fd, "w", encoding="utf-8", closefd=True) as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.flush()
        Path(name).replace(path)
    finally:
        Path(name).unlink(missing_ok=True)


def _run_quality_cli(argv: list[str]) -> None:
    sink = io.StringIO()
    with redirect_stdout(sink):
        exit_code = quality.main(argv)
    if exit_code != 0:
        raise RuntimeError(f"ai_decision_quality_exit_code:{exit_code}")


def _full_day_mature(*, target_date: str, as_of: datetime) -> bool:
    target = date.fromisoformat(target_date)
    ready_at = datetime.combine(target, FULL_DAY_MATURITY_TIME_KST, tzinfo=quality.KST)
    return as_of.astimezone(quality.KST) >= ready_at


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _selection_checkpoint_contract_pass(
    selection: dict[str, Any], *, evaluated_request_count: int
) -> bool:
    counts = selection.get("checkpoint_evaluated_setup_state_counts")
    if not isinstance(counts, dict) or not counts:
        return False
    if set(counts) - {"READY", "WAIT_CONFIRMATION", "OTHER"}:
        return False
    try:
        normalized = [int(value) for value in counts.values()]
    except (TypeError, ValueError):
        return False
    return bool(
        all(value >= 0 for value in normalized)
        and sum(normalized) == int(evaluated_request_count)
    )


def _wait_for_predecessor(
    *, target_date: str, wait_sec: int, interval_sec: int
) -> tuple[bool, dict[str, Any]]:
    deadline = time.monotonic() + max(0, int(wait_sec))
    path = predecessor_status_path(target_date)
    while True:
        status = _read_json(path)
        state = str(status.get("status") or "missing").lower()
        if state == "succeeded":
            return True, status
        if time.monotonic() >= deadline:
            return False, status
        time.sleep(max(1, min(int(interval_sec), 60)))


def _cohort_result(
    *,
    target_date: str,
    as_of: datetime,
    venue: str,
    session_bucket: str,
    max_new_requests: int,
    workers: int,
    timeout_sec: float,
) -> dict[str, Any]:
    common = [
        "--date",
        target_date,
        "--venue",
        venue,
        "--session-bucket",
        session_bucket,
        "--write",
    ]
    _run_quality_cli([*common, "--mode", "control"])
    control_path = quality.control_path(
        target_date,
        effective_venue=venue,
        session_bucket=session_bucket,
    )
    control = _read_json(control_path)
    if control.get("status") != "control_manifest_frozen_collect_exact_samples":
        raise RuntimeError(f"control_manifest_not_ready:{venue}:{session_bucket}")
    entry_controls = [
        row
        for row in control.get("controls") or []
        if isinstance(row, dict) and row.get("decision_stage") == "entry"
    ]
    if not entry_controls:
        return {
            "effective_venue": venue,
            "session_bucket": session_bucket,
            "status": "hold_no_exact_entry_control",
            "control_path": str(control_path),
            "entry_control_sample_count": 0,
        }
    if any(
        str(row.get("provider_actual") or "").lower() != "openai"
        for row in entry_controls
    ):
        raise RuntimeError(
            f"entry_control_provider_not_openai:{venue}:{session_bucket}"
        )

    _run_quality_cli(
        [
            *common,
            "--mode",
            "detailed",
            "--as-of",
            as_of.isoformat(),
            "--outcome-price-source",
            "auto",
            "--detailed-candidate-version",
            DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_PROMPT_VERSION,
            "--execute-candidate",
            "--candidate-max-new-requests",
            str(max_new_requests),
            "--candidate-workers",
            str(workers),
            "--candidate-timeout-sec",
            str(timeout_sec),
        ]
    )
    report_path = quality.detailed_paired_path(
        target_date,
        candidate_prompt_version=(
            DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_PROMPT_VERSION
        ),
        effective_venue=venue,
        session_bucket=session_bucket,
    )
    report = _read_json(report_path)
    prepared_count = int(report.get("prepared_request_count") or 0)
    request_count = int(report.get("request_count") or 0)
    result_count = int(report.get("result_count") or 0)
    if prepared_count == 0:
        status = "hold_no_mature_exact_request"
    else:
        selection = report.get("candidate_execution_selection")
        if (
            request_count <= 0
            or result_count != request_count
            or report.get("candidate_execution_performed") is not True
            or report.get("provider_failed_count") != 0
            or report.get("candidate_provider_none_count") != 0
            or not isinstance(selection, dict)
            or not quality.candidate_execution_selection_contract_pass(
                selection,
                max_new_requests=max_new_requests,
            )
            or not _selection_checkpoint_contract_pass(
                selection,
                evaluated_request_count=request_count,
            )
        ):
            raise RuntimeError(
                f"candidate_execution_contract_failed:{venue}:{session_bucket}"
            )
        status = "completed_offline_only"
    return {
        "effective_venue": venue,
        "session_bucket": session_bucket,
        "status": status,
        "control_path": str(control_path),
        "report_path": str(report_path),
        "entry_control_sample_count": sum(
            int(row.get("sample_count") or 0) for row in entry_controls
        ),
        "prepared_request_count": prepared_count,
        "evaluated_request_count": request_count,
        "candidate_exposure_decision_count": report.get(
            "candidate_exposure_decision_count"
        ),
        "candidate_exposure_unique_symbol_count": report.get(
            "candidate_exposure_unique_symbol_count"
        ),
        "candidate_probe_arm_decision_count": report.get(
            "candidate_probe_arm_decision_count"
        ),
        "candidate_probe_arm_unique_symbol_count": report.get(
            "candidate_probe_arm_unique_symbol_count"
        ),
        "candidate_probe_arm_sample_floor": report.get(
            "candidate_probe_arm_sample_floor"
        ),
        "promotion_quality_gate_pass": report.get("promotion_quality_gate_pass"),
        "candidate_exposure_floor_feasibility": report.get(
            "candidate_exposure_floor_feasibility"
        ),
        "candidate_execution_selection": report.get("candidate_execution_selection"),
    }


def run_batch(
    *,
    target_date: str,
    as_of: datetime,
    max_new_requests: int,
    workers: int,
    timeout_sec: float,
    require_predecessor: bool,
    predecessor_wait_sec: int,
    predecessor_interval_sec: int,
    write: bool,
) -> dict[str, Any]:
    started_at = datetime.now(quality.KST)
    report: dict[str, Any] = {
        "schema": BATCH_SCHEMA,
        "target_date": target_date,
        "generated_at": started_at.isoformat(),
        "outcome_as_of": as_of.astimezone(quality.KST).isoformat(),
        "status": "running",
        "candidate_prompt_version": (
            DECISION_QUALITY_V2_14_SETUP_RISK_ADJUDICATOR_PROMPT_VERSION
        ),
        "full_day_maturity_time_kst": "21:00:00",
        "max_new_requests_per_cohort": max_new_requests,
        "cohorts": [],
        **OFFLINE_BATCH_CONTRACT,
    }
    path = batch_status_path(target_date)
    if write:
        _atomic_write_json(path, report)
    if not _full_day_mature(target_date=target_date, as_of=as_of):
        report["status"] = "not_ready_full_day_outcome_maturity"
        report["finished_at"] = datetime.now(quality.KST).isoformat()
        if write:
            _atomic_write_json(path, report)
        return report
    if require_predecessor:
        predecessor_pass, predecessor = _wait_for_predecessor(
            target_date=target_date,
            wait_sec=predecessor_wait_sec,
            interval_sec=predecessor_interval_sec,
        )
        report["predecessor"] = {
            "path": str(predecessor_status_path(target_date)),
            "status": predecessor.get("status") or "missing",
            "pass": predecessor_pass,
        }
        if not predecessor_pass:
            report["status"] = "blocked_predecessor_timeout"
            report["finished_at"] = datetime.now(quality.KST).isoformat()
            if write:
                _atomic_write_json(path, report)
            return report
    if not quality._offline_openai_api_keys():
        report["status"] = "failed_openai_key_unavailable"
        report["provider"] = "openai"
        report["provider_none"] = False
        report["finished_at"] = datetime.now(quality.KST).isoformat()
        if write:
            _atomic_write_json(path, report)
        return report

    try:
        for venue, session_bucket in DEFAULT_COHORTS:
            try:
                cohort = _cohort_result(
                    target_date=target_date,
                    as_of=as_of,
                    venue=venue,
                    session_bucket=session_bucket,
                    max_new_requests=max_new_requests,
                    workers=workers,
                    timeout_sec=timeout_sec,
                )
            except Exception as exc:
                cohort = {
                    "effective_venue": venue,
                    "session_bucket": session_bucket,
                    "status": "failed_offline_cohort",
                    "error_type": type(exc).__name__,
                    "error_code": str(exc).splitlines()[0][:240],
                }
            report["cohorts"].append(cohort)
            if write:
                _atomic_write_json(path, report)
        cohort_failure_count = sum(
            row.get("status") == "failed_offline_cohort"
            for row in report["cohorts"]
            if isinstance(row, dict)
        )
        report["cohort_failure_count"] = cohort_failure_count
        report["status"] = (
            "completed_offline_only"
            if cohort_failure_count == 0
            else "completed_offline_only_with_cohort_failures"
        )
        report["krx_bounded_live_candidate"] = publish_live_candidate(
            source_date=target_date,
            batch_report=report,
            write=write,
        )
    except Exception as exc:
        report["status"] = "failed_offline_batch"
        report["error_type"] = type(exc).__name__
        report["error_code"] = str(exc).splitlines()[0][:240]
    report["provider"] = "openai"
    report["provider_none"] = False
    report["finished_at"] = datetime.now(quality.KST).isoformat()
    if write:
        _atomic_write_json(path, report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run full-day cohort-isolated V2.14 paired replay offline."
    )
    parser.add_argument("--date", required=True)
    parser.add_argument("--as-of")
    parser.add_argument("--max-new-requests-per-cohort", type=int, default=30)
    parser.add_argument("--candidate-workers", type=int, default=2)
    parser.add_argument("--candidate-timeout-sec", type=float, default=45.0)
    parser.add_argument("--predecessor-wait-sec", type=int, default=43200)
    parser.add_argument("--predecessor-interval-sec", type=int, default=30)
    parser.add_argument("--no-require-predecessor", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    if args.max_new_requests_per_cohort <= 0:
        parser.error("--max-new-requests-per-cohort must be positive")
    if not 1 <= args.candidate_workers <= 8:
        parser.error("--candidate-workers must be between 1 and 8")
    if args.candidate_timeout_sec <= 0:
        parser.error("--candidate-timeout-sec must be positive")
    if args.predecessor_wait_sec < 0:
        parser.error("--predecessor-wait-sec must be non-negative")
    if args.predecessor_interval_sec <= 0:
        parser.error("--predecessor-interval-sec must be positive")
    as_of = quality._parse_ts(args.as_of) or datetime.now(quality.KST)
    report = run_batch(
        target_date=args.date,
        as_of=as_of,
        max_new_requests=args.max_new_requests_per_cohort,
        workers=args.candidate_workers,
        timeout_sec=args.candidate_timeout_sec,
        require_predecessor=not args.no_require_predecessor,
        predecessor_wait_sec=args.predecessor_wait_sec,
        predecessor_interval_sec=args.predecessor_interval_sec,
        write=args.write,
    )
    print(json.dumps(report, ensure_ascii=False))
    if report["status"] == "blocked_predecessor_timeout":
        return 3
    return (
        0
        if report["status"]
        in {
            "completed_offline_only",
            "not_ready_full_day_outcome_maturity",
        }
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
