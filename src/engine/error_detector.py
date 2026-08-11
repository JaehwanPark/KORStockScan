from __future__ import annotations

import argparse
import json
import os
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from src.utils.constants import PROJECT_ROOT
from src.utils.logger import log_error, log_info

from src.engine.error_detectors import (
    BaseDetector,
    DetectionResult,
    get_registered_detectors,
)
import src.engine.error_detectors.cron_completion  # noqa: F401
import src.engine.error_detectors.log_scanner  # noqa: F401
import src.engine.error_detectors.kiwoom_auth_8005_restart  # noqa: F401
import src.engine.error_detectors.process_health  # noqa: F401
import src.engine.error_detectors.artifact_freshness  # noqa: F401
import src.engine.error_detectors.resource_usage  # noqa: F401
import src.engine.error_detectors.stale_lock  # noqa: F401

REPORT_DIR = PROJECT_ROOT / "data" / "report" / "error_detection"
REPORT_SCHEMA_VERSION = 2
REPORT_TYPE = "system_error_detection"
KST = ZoneInfo("Asia/Seoul")
REQUIRED_DETECTOR_IDS = frozenset(
    {
        "artifact_freshness",
        "cron_completion",
        "kiwoom_auth_8005_restart",
        "log_scanner",
        "process_health",
        "resource_usage",
        "stale_lock",
    }
)
OPERATIONAL_MUTATION_AUTHORITY = (
    "kiwoom_auth_restart_flag",
    "kiwoom_token_cache_invalidation",
    "resource_log_rotation",
    "stale_lock_cleanup",
)


MODE_DETECTOR_MAP = {
    "full": None,
    "health_only": {"process_health"},
    "cron_only": {"cron_completion"},
    "log_only": {"log_scanner"},
    "auth_only": {"kiwoom_auth_8005_restart"},
    "artifact_only": {"artifact_freshness"},
    "resource_only": {"resource_usage"},
}


class ErrorDetectionEngine:
    def __init__(
        self,
        dry_run: bool = False,
        mode: str = "full",
        run_id: str | None = None,
    ):
        if mode not in MODE_DETECTOR_MAP:
            raise ValueError(f"Unsupported error detection mode: {mode}")
        self.dry_run = dry_run
        self.mode = mode
        self.run_id = run_id or uuid.uuid4().hex
        self.detectors: list[BaseDetector] = []
        self.expected_detector_ids: list[str] = []
        self.initialization_failures: list[DetectionResult] = []
        self._init_detectors()

    def _init_detectors(self):
        registered = get_registered_detectors()
        if self.mode == "full":
            expected_ids = REQUIRED_DETECTOR_IDS | set(registered)
        else:
            expected_ids = MODE_DETECTOR_MAP.get(self.mode) or set()
        self.expected_detector_ids = sorted(expected_ids)
        for detector_id in self.expected_detector_ids:
            cls = registered.get(detector_id)
            if cls is None:
                error = RuntimeError("required detector is not registered")
                log_error(f"Error initializing detector {detector_id}: {error}")
                self.initialization_failures.append(
                    self._initialization_failure(detector_id, "system", error)
                )
                continue
            try:
                self.detectors.append(cls(dry_run=self.dry_run))
            except Exception as e:
                log_error(f"Error initializing detector {detector_id}: {e}")
                self.initialization_failures.append(
                    self._initialization_failure(
                        detector_id,
                        str(getattr(cls, "category", "") or "system"),
                        e,
                    )
                )

    @staticmethod
    def _initialization_failure(
        detector_id: str, category: str, error: Exception
    ) -> DetectionResult:
        return DetectionResult(
            detector_id=detector_id,
            category=category,
            severity="fail",
            summary=f"Detector {detector_id} failed during initialization: {error}",
            details={
                "stage": "initialization",
                "error": str(error),
                "error_type": type(error).__name__,
            },
            recommended_action="Repair detector initialization and rerun the same mode.",
        )

    def run_all(self) -> list[DetectionResult]:
        results: list[DetectionResult] = list(self.initialization_failures)
        for detector in self.detectors:
            try:
                result = detector.check()
            except Exception as e:
                result = DetectionResult(
                    detector_id=detector.id,
                    category=detector.category,
                    severity="fail",
                    summary=f"Detector {detector.id} raised exception: {e}",
                    details={"error": str(e)},
                )
            results.append(result)
        return results

    def get_summary_severity(self, results: list[DetectionResult]) -> str:
        if any(r.severity == "fail" for r in results):
            return "fail"
        if any(r.severity == "warning" for r in results):
            return "warning"
        return "pass"

    def build_report(self, results: list[DetectionResult]) -> dict:
        now = datetime.now(KST)
        operational_mutations = self._operational_mutations(results)
        return {
            "schema_version": REPORT_SCHEMA_VERSION,
            "report_type": REPORT_TYPE,
            "target_date": now.date().isoformat(),
            "timestamp": now.isoformat(timespec="seconds"),
            "mode": self.mode,
            "run_id": self.run_id,
            "dry_run": self.dry_run,
            "runtime_effect": False,
            "runtime_mutation": "none",
            "runtime_mutation_scope": "trading_strategy_runtime",
            "operational_mutation_authority": list(OPERATIONAL_MUTATION_AUTHORITY),
            "operational_mutations": operational_mutations,
            "operational_mutation_count": len(operational_mutations),
            "summary_severity": self.get_summary_severity(results),
            "expected_detector_count": len(self.expected_detector_ids),
            "expected_detector_ids": self.expected_detector_ids,
            "initialized_detector_count": len(self.detectors),
            "initialized_detector_ids": [detector.id for detector in self.detectors],
            "initialization_failure_count": len(self.initialization_failures),
            "detector_count": len(results),
            "results": [
                {
                    "detector_id": r.detector_id,
                    "category": r.category,
                    "severity": r.severity,
                    "summary": r.summary,
                    "details": r.details,
                    "recommended_action": r.recommended_action,
                    "checked_at": r.checked_at,
                }
                for r in results
            ],
        }

    @staticmethod
    def _operational_mutations(results: list[DetectionResult]) -> list[str]:
        mutations: list[str] = []
        for result in results:
            details = result.details if isinstance(result.details, dict) else {}
            if result.detector_id == "kiwoom_auth_8005_restart":
                if details.get("restart_requested") is True:
                    mutations.append("kiwoom_auth_restart_flag")
                if details.get("token_cache_invalidated") is True:
                    mutations.append("kiwoom_token_cache_invalidation")
            elif result.detector_id == "resource_usage":
                if details.get("log_rotate_trigger") == "ok":
                    mutations.append("resource_log_rotation")
            elif result.detector_id == "stale_lock":
                if details.get("stale_locks_cleaned"):
                    mutations.append("stale_lock_cleanup")
        return sorted(set(mutations))

    def write_report(
        self, report: dict, report_path: Path | None = None
    ) -> Path | None:
        if self.dry_run:
            log_info(
                f"[ERROR_DETECTION] dry-run, would write report with severity={report['summary_severity']}"
            )
            return None
        if report_path is None:
            target_date = str(report.get("target_date") or datetime.now(KST).date())
            report_path = REPORT_DIR / f"error_detection_{target_date}.json"
        report_path = Path(report_path)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = report_path.with_name(
            f".{report_path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp"
        )
        try:
            tmp_path.write_text(
                json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            os.replace(tmp_path, report_path)
        finally:
            tmp_path.unlink(missing_ok=True)
        log_info(f"[ERROR_DETECTION] Report written to {report_path}")
        return report_path


def validate_report_contract(
    report: dict[str, Any],
    *,
    expected_mode: str,
    expected_run_id: str,
    expected_target_date: str,
) -> list[str]:
    """Return provenance/shape defects that make a wrapper run non-consumable."""

    errors: list[str] = []
    if report.get("schema_version") != REPORT_SCHEMA_VERSION:
        errors.append("schema_version_mismatch")
    if report.get("report_type") != REPORT_TYPE:
        errors.append("report_type_mismatch")
    if report.get("mode") != expected_mode:
        errors.append("mode_mismatch")
    if report.get("run_id") != expected_run_id:
        errors.append("run_id_mismatch")
    if report.get("target_date") != expected_target_date:
        errors.append("target_date_mismatch")
    timestamp = report.get("timestamp")
    try:
        timestamp_dt = datetime.fromisoformat(str(timestamp))
    except (TypeError, ValueError):
        errors.append("timestamp_invalid")
    else:
        if timestamp_dt.tzinfo is None:
            errors.append("timestamp_timezone_missing")
        elif timestamp_dt.astimezone(KST).date().isoformat() != expected_target_date:
            errors.append("timestamp_target_date_mismatch")
    if report.get("runtime_effect") is not False:
        errors.append("runtime_effect_mismatch")
    if report.get("runtime_mutation") != "none":
        errors.append("runtime_mutation_mismatch")
    if report.get("runtime_mutation_scope") != "trading_strategy_runtime":
        errors.append("runtime_mutation_scope_mismatch")
    authority = report.get("operational_mutation_authority")
    if authority != list(OPERATIONAL_MUTATION_AUTHORITY):
        errors.append("operational_mutation_authority_mismatch")
    operational_mutations = report.get("operational_mutations")
    if not isinstance(operational_mutations, list) or not all(
        item in OPERATIONAL_MUTATION_AUTHORITY for item in operational_mutations
    ):
        errors.append("operational_mutations_invalid")
        operational_mutations = []
    if report.get("operational_mutation_count") != len(operational_mutations):
        errors.append("operational_mutation_count_mismatch")

    results = report.get("results")
    if not isinstance(results, list):
        errors.append("results_not_list")
        results = []
    if report.get("detector_count") != len(results):
        errors.append("detector_count_mismatch")

    result_severities: list[str] = []
    for item in results:
        if not isinstance(item, dict):
            errors.append("result_item_invalid")
            continue
        severity = item.get("severity")
        if severity not in {"pass", "warning", "fail"}:
            errors.append("result_severity_invalid")
        else:
            result_severities.append(severity)
        if not isinstance(item.get("summary"), str) or not item.get("summary"):
            errors.append("result_summary_invalid")
    derived_summary_severity = (
        "fail"
        if "fail" in result_severities
        else "warning" if "warning" in result_severities else "pass"
    )
    if report.get("summary_severity") != derived_summary_severity:
        errors.append("summary_severity_mismatch")

    expected_ids = report.get("expected_detector_ids")
    initialized_ids = report.get("initialized_detector_ids")
    initialization_failure_count = report.get("initialization_failure_count")
    if not isinstance(expected_ids, list) or not all(
        isinstance(item, str) and item for item in expected_ids
    ):
        errors.append("expected_detector_ids_invalid")
        expected_ids = []
    if len(set(expected_ids)) != len(expected_ids):
        errors.append("expected_detector_ids_duplicate")
    if report.get("expected_detector_count") != len(expected_ids):
        errors.append("expected_detector_count_mismatch")
    if not isinstance(initialized_ids, list) or not all(
        isinstance(item, str) and item for item in initialized_ids
    ):
        errors.append("initialized_detector_ids_invalid")
        initialized_ids = []
    if report.get("initialized_detector_count") != len(initialized_ids):
        errors.append("initialized_detector_count_mismatch")
    if not isinstance(initialization_failure_count, int):
        errors.append("initialization_failure_count_invalid")
    elif len(initialized_ids) + initialization_failure_count != len(expected_ids):
        errors.append("detector_initialization_accounting_mismatch")

    result_ids = [
        item.get("detector_id")
        for item in results
        if isinstance(item, dict) and isinstance(item.get("detector_id"), str)
    ]
    if sorted(result_ids) != sorted(expected_ids):
        errors.append("result_detector_ids_mismatch")
    return errors


def main():
    parser = argparse.ArgumentParser(description="System Error Detection Engine")
    parser.add_argument(
        "--mode",
        choices=[
            "full",
            "health_only",
            "cron_only",
            "log_only",
            "auth_only",
            "artifact_only",
            "resource_only",
        ],
        default="full",
        help="Detection scope (default: full)",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Do not write report files"
    )
    parser.add_argument(
        "--daemon", action="store_true", help="Run in daemon loop (for bot_main.py)"
    )
    parser.add_argument(
        "--interval", type=int, default=60, help="Daemon check interval in seconds"
    )
    parser.add_argument("--run-id", default="", help="Invocation provenance identifier")
    parser.add_argument(
        "--report-file", default="", help="Explicit output path for this invocation"
    )
    args = parser.parse_args()

    if args.daemon:
        _daemon_loop(args.interval, args.dry_run, args.mode)
        return

    engine = ErrorDetectionEngine(
        dry_run=args.dry_run,
        mode=args.mode,
        run_id=args.run_id or None,
    )
    results = engine.run_all()
    report = engine.build_report(results)

    for r in results:
        if r.severity in ("fail", "warning"):
            log_info(
                f"[ERROR_DETECTION] [{r.severity.upper()}] {r.detector_id}: {r.summary}"
            )

    engine.write_report(report, Path(args.report_file) if args.report_file else None)
    print(json.dumps(report, ensure_ascii=False, indent=2))


def _daemon_loop(interval: int, dry_run: bool, mode: str = "full"):
    log_info(f"[ERROR_DETECTION] Daemon mode started, interval={interval}s mode={mode}")
    while True:
        try:
            engine = ErrorDetectionEngine(dry_run=dry_run, mode=mode)
            results = engine.run_all()
            report = engine.build_report(results)
            engine.write_report(report)
            for r in results:
                if r.severity == "fail":
                    log_error(f"[ERROR_DETECTION] {r.detector_id}: {r.summary}")
        except Exception as e:
            log_error(f"[ERROR_DETECTION] Daemon loop error: {e}")
        time.sleep(interval)


if __name__ == "__main__":
    main()
