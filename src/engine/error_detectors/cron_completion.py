from __future__ import annotations

import os
import re
import time
from datetime import date, datetime, time as dtime, timedelta
from pathlib import Path
from typing import Any

from src.utils.constants import PROJECT_ROOT, TRADING_RULES
from src.utils.market_day import is_krx_trading_day

from src.engine.error_detectors.base import (
    BaseDetector,
    DetectionResult,
    register_detector,
)


def _today_kst() -> str:
    return date.today().isoformat()


def _now_kst_ts() -> float:
    return time.time()


def _kst_time_tuple() -> tuple[int, int]:
    now_kst = datetime.now()
    return now_kst.hour, now_kst.minute


CRON_JOB_REGISTRY: list[dict[str, Any]] = [
    {
        "id": "final_ensemble_scanner",
        "log": "logs/ensemble_scanner.log",
        "window_start": (7, 20),
        "window_end": (8, 0),
        "mode": "once",
        "critical": True,
        "trading_day_only": True,
    },
    {
        "id": "threshold_cycle_preopen",
        "log": "logs/threshold_cycle_preopen_cron.log",
        "window_start": (7, 35),
        "window_end": (7, 50),
        "mode": "once",
        "critical": True,
        "trading_day_only": True,
    },
    {
        "id": "buy_funnel_sentinel",
        "log": "logs/run_buy_funnel_sentinel_cron.log",
        "window_start": (9, 5),
        "window_end": (15, 20),
        "mode": "recurring",
        "interval_min": 5,
        "critical": False,
        "trading_day_only": True,
    },
    {
        "id": "bd_fbuy_accum_pre_intraday",
        "log": "logs/bd_fbuy_accum_pre_intraday_cron.log",
        "window_start": (9, 5),
        "window_end": (15, 20),
        "mode": "recurring",
        "interval_min": 10,
        "critical": False,
        "trading_day_only": True,
    },
    {
        "id": "holding_exit_sentinel",
        "log": "logs/run_holding_exit_sentinel_cron.log",
        "window_start": (9, 5),
        "window_end": (15, 30),
        "mode": "recurring",
        "interval_min": 5,
        "critical": False,
        "trading_day_only": True,
    },
    {
        "id": "panic_sell_defense",
        "log": "logs/run_panic_sell_defense_cron.log",
        "window_start": (9, 5),
        "window_end": (15, 30),
        "mode": "recurring",
        "interval_min": 5,
        "critical": False,
        "trading_day_only": True,
    },
    {
        "id": "panic_buying",
        "log": "logs/run_panic_buying_cron.log",
        "window_start": (9, 5),
        "window_end": (15, 30),
        "mode": "recurring",
        "interval_min": 5,
        "critical": False,
        "trading_day_only": True,
    },
    {
        "id": "buy_pause_guard",
        "log": "logs/buy_pause_guard.log",
        "window_start": (9, 30),
        "window_end": (11, 0),
        "mode": "recurring",
        "interval_min": 5,
        "critical": False,
        "trading_day_only": True,
    },
    {
        "id": "monitor_snapshot",
        "log": "logs/run_monitor_snapshot_cron.log",
        "window_start": (9, 35),
        "window_end": (12, 0),
        "mode": "recurring",
        "interval_min": 20,
        "critical": False,
        "trading_day_only": True,
    },
    {
        "id": "scalp_sim_overnight_preclose",
        "log": "logs/scalp_sim_overnight_preclose_cron.log",
        "window_start": (15, 20),
        "window_end": (15, 35),
        "mode": "once",
        "critical": False,
        "trading_day_only": True,
    },
    {
        "id": "swing_live_dry_run",
        "log": "logs/swing_live_dry_run_cron.log",
        "window_start": (15, 45),
        "window_end": (16, 5),
        "mode": "once",
        "critical": False,
        "trading_day_only": True,
    },
    {
        "id": "threshold_cycle_postclose",
        "log": "logs/threshold_cycle_postclose_cron.log",
        "window_start": (16, 10),
        "window_end": (17, 0),
        "mode": "once",
        "critical": True,
        "trading_day_only": True,
    },
    {
        "id": "swing_model_retrain_postclose",
        "log": "logs/swing_model_retrain_cron.log",
        "window_start": (17, 30),
        "window_end": (18, 30),
        "mode": "once",
        "critical": False,
        "trading_day_only": True,
    },
    {
        "id": "tuning_monitoring_postclose",
        "log": "logs/tuning_monitoring_postclose_cron.log",
        "window_start": (20, 5),
        "window_end": (20, 45),
        "mode": "once",
        "critical": False,
        "trading_day_only": True,
    },
    {
        "id": "update_kospi",
        "log": "logs/update_kospi.log",
        "window_start": (21, 0),
        "window_end": (21, 50),
        "mode": "once",
        "critical": False,
    },
    {
        "id": "dashboard_db_archive",
        "log": "logs/dashboard_db_archive_cron.log",
        "window_start": (23, 10),
        "window_end": (23, 20),
        "mode": "once",
        "critical": False,
    },
    {
        "id": "log_rotation_cleanup",
        "log": "logs/log_rotation_cleanup_cron.log",
        "window_start": (23, 20),
        "window_end": (23, 30),
        "mode": "once",
        "critical": False,
    },
    {
        "id": "system_metric_sampler",
        "log": "logs/system_metric_sampler_cron.log",
        "window_start": (0, 0),
        "window_end": (23, 59),
        "mode": "recurring",
        "interval_min": 1,
        "critical": False,
        "trading_day_only": True,
    },
    {
        "id": "error_detection_full",
        "log": "logs/run_error_detection.log",
        "window_start": (0, 0),
        "window_end": (23, 59),
        "mode": "recurring",
        "interval_min": 5,
        "critical": False,
    },
]

_ERROR_MARKER = re.compile(r"\[(FAIL|ERROR|CRITICAL)\]", re.IGNORECASE)
_DONE_MARKER = re.compile(r"\[(DONE|OK|SUCCESS|COMPLETED)\]", re.IGNORECASE)
_START_MARKER = re.compile(r"\[(START|BEGIN)\]", re.IGNORECASE)
_DATE_PATTERN = re.compile(r"(?:target_date|started_at|finished_at)=(\d{4}-\d{2}-\d{2})")


@register_detector
class CronCompletionDetector(BaseDetector):
    id = "cron_completion"
    name = "Cron Job Completion Detector"
    category = "cron"

    RECENT_MINUTES: int = 60
    MARKER_TAIL_LINES: int = 5000

    def check(self) -> DetectionResult:
        now_h, now_m = _kst_time_tuple()
        now_total = now_h * 60 + now_m
        trading_day = is_krx_trading_day(date.today())
        details: dict = {}
        issues: list[str] = []
        warnings: list[str] = []

        for job in CRON_JOB_REGISTRY:
            log_path = PROJECT_ROOT / job["log"]
            jid = job["id"]
            critical = job.get("critical", False)
            if job.get("trading_day_only", False) and not trading_day:
                details[f"{jid}_status"] = "skip_non_trading_day"
                continue

            ws_h, ws_m = job["window_start"]
            we_h, we_m = job.get("window_end", (23, 59))
            if isinstance(we_h, str):
                we_h, we_m = 23, 59

            ws_total = ws_h * 60 + ws_m
            we_total = we_h * 60 + we_m
            past_window_start = now_total >= ws_total
            past_window_end = now_total > we_total

            if not past_window_start:
                details[f"{jid}_status"] = "not_yet_due"
                details[f"{jid}_window"] = f"{ws_h:02d}:{ws_m:02d}~{we_h:02d}:{we_m:02d}"
                continue

            if not log_path.exists():
                if critical and past_window_end:
                    issues.append(f"{jid}: log file missing after window end")
                    details[f"{jid}_status"] = "fail"
                elif past_window_start:
                    warnings.append(f"{jid}: log file not found (window just opened)")
                    details[f"{jid}_status"] = "warning"
                else:
                    details[f"{jid}_status"] = "not_yet_due"
                continue

            recent_lines = self._read_tail(log_path, self.MARKER_TAIL_LINES)
            today_str = _today_kst()
            today_lines = self._filter_today_lines(recent_lines, today_str)
            has_matching_date = bool(today_lines)
            has_done = bool(_DONE_MARKER.search(today_lines)) if has_matching_date else False
            has_start = bool(_START_MARKER.search(today_lines)) if has_matching_date else False
            has_error = bool(_ERROR_MARKER.search(today_lines)) if has_matching_date else bool(_ERROR_MARKER.search(recent_lines))

            job["mode"] = job.get("mode", "once")
            if job["mode"] == "once":
                if not has_matching_date:
                    if past_window_end:
                        issues.append(f"{jid}: no today marker found after window end")
                        details[f"{jid}_status"] = "fail"
                    elif past_window_start:
                        warnings.append(f"{jid}: no today marker yet (window open)")
                        details[f"{jid}_status"] = "warning"
                    else:
                        details[f"{jid}_status"] = "not_yet_due"
                elif has_done and has_error:
                    last_marker = self._last_terminal_marker(today_lines)
                    if last_marker == "error":
                        issues.append(f"{jid}: last marker is FAIL after DONE")
                        details[f"{jid}_status"] = "fail"
                    else:
                        details[f"{jid}_status"] = "pass"
                        details[f"{jid}_pass_note"] = "done over error (last terminal was DONE)"
                elif has_done:
                    details[f"{jid}_status"] = "pass"
                elif has_error and past_window_end:
                    issues.append(f"{jid}: finished with error after window end")
                    details[f"{jid}_status"] = "fail"
                elif past_window_end:
                    issues.append(f"{jid}: no completion marker after window end")
                    details[f"{jid}_status"] = "fail"
                elif has_start:
                    details[f"{jid}_status"] = "in_progress"
                else:
                    warnings.append(f"{jid}: no start/completion within window")
                    details[f"{jid}_status"] = "warning"
            else:
                if not has_matching_date:
                    details[f"{jid}_status"] = "unknown"
                elif has_error:
                    warnings.append(f"{jid}: recent errors detected")
                    details[f"{jid}_status"] = "warning"
                elif has_done:
                    details[f"{jid}_status"] = "pass"
                else:
                    details[f"{jid}_status"] = "unknown"

            if has_error:
                details[f"{jid}_error_lines"] = self._count_errors(recent_lines)

        severity, summary = self._classify(issues, warnings)
        return DetectionResult(
            detector_id=self.id,
            category=self.category,
            severity=severity,
            summary=summary,
            details=details,
            recommended_action=self._recommend_action(severity, issues),
        )

    @staticmethod
    def _read_tail(path: Path, n: int) -> str:
        paths = CronCompletionDetector._log_bundle_paths(path)
        lines: list[str] = []
        for item in paths:
            lines.extend(CronCompletionDetector._read_tail_lines(item, n))
        return "".join(lines[-n:])

    @staticmethod
    def _log_bundle_paths(path: Path) -> list[Path]:
        rotated: list[tuple[int, Path]] = []
        try:
            candidates = path.parent.glob(f"{path.name}.*")
        except OSError:
            candidates = []
        for candidate in candidates:
            suffix = candidate.name.removeprefix(f"{path.name}.")
            if suffix.isdigit():
                rotated.append((int(suffix), candidate))
        return [item for _, item in sorted(rotated, reverse=True)] + [path]

    @staticmethod
    def _read_tail_lines(path: Path, n: int) -> list[str]:
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
                return lines[-n:]
        except OSError:
            return []

    @staticmethod
    def _count_errors(text: str) -> int:
        return len(_ERROR_MARKER.findall(text))

    @staticmethod
    def _filter_today_lines(text: str, today_str: str) -> str:
        today_lines: list[str] = []
        for line in text.splitlines():
            match = _DATE_PATTERN.search(line)
            if match and match.group(1) == today_str:
                today_lines.append(line)
            elif CronCompletionDetector._line_has_today_timestamp(line, today_str):
                today_lines.append(line)
        return "\n".join(today_lines)

    @staticmethod
    def _line_has_today_timestamp(line: str, today_str: str) -> bool:
        return today_str in line and (
            _DONE_MARKER.search(line) or _ERROR_MARKER.search(line) or _START_MARKER.search(line)
        )

    @staticmethod
    def _last_terminal_marker(today_lines: str) -> str:
        for line in reversed(today_lines.splitlines()):
            if _ERROR_MARKER.search(line):
                return "error"
            if _DONE_MARKER.search(line):
                return "done"
        return "none"

    @staticmethod
    def _classify(
        issues: list[str], warnings: list[str]
    ) -> tuple[str, str]:
        if issues:
            return "fail", f"Cron job failures: {'; '.join(issues[:5])}"
        if warnings:
            return "warning", f"Cron warnings: {'; '.join(warnings[:5])}"
        return "pass", "All cron jobs healthy or not yet due."

    @staticmethod
    def _recommend_action(severity: str, issues: list[str]) -> str:
        if severity == "fail":
            return f"Check logs for failed jobs: {'; '.join(issues[:3])}"
        if severity == "warning":
            return "Monitor warning jobs in next cycle."
        return ""
