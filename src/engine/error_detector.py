from __future__ import annotations

import argparse
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from src.utils.constants import PROJECT_ROOT, TRADING_RULES
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
    def __init__(self, dry_run: bool = False, mode: str = "full"):
        self.dry_run = dry_run
        self.mode = mode
        self.detectors: list[BaseDetector] = []
        self._init_detectors()

    def _init_detectors(self):
        allowed = MODE_DETECTOR_MAP.get(self.mode) if self.mode != "full" else None
        for detector_id, cls in get_registered_detectors().items():
            if allowed is not None and detector_id not in allowed:
                continue
            try:
                self.detectors.append(cls(dry_run=self.dry_run))
            except Exception as e:
                log_error(f"Error initializing detector {detector_id}: {e}")

    def run_all(self) -> list[DetectionResult]:
        results: list[DetectionResult] = []
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
        return {
            "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
            "summary_severity": self.get_summary_severity(results),
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

    def write_report(self, report: dict):
        if self.dry_run:
            log_info(
                f"[ERROR_DETECTION] dry-run, would write report with severity={report['summary_severity']}"
            )
            return
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        today_str = datetime.now().strftime("%Y-%m-%d")
        report_path = REPORT_DIR / f"error_detection_{today_str}.json"
        report_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        log_info(f"[ERROR_DETECTION] Report written to {report_path}")


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
    args = parser.parse_args()

    if args.daemon:
        _daemon_loop(args.interval, args.dry_run, args.mode)
        return

    engine = ErrorDetectionEngine(dry_run=args.dry_run, mode=args.mode)
    results = engine.run_all()
    report = engine.build_report(results)

    for r in results:
        if r.severity in ("fail", "warning"):
            log_info(
                f"[ERROR_DETECTION] [{r.severity.upper()}] {r.detector_id}: {r.summary}"
            )

    engine.write_report(report)
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
