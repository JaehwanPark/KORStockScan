from __future__ import annotations

import json
import datetime as datetime_module
from collections import deque
import os
import re
import time
from datetime import date, datetime, time as datetime_time, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from src.utils.constants import PROJECT_ROOT
from src.utils.market_day import is_krx_trading_day

from src.engine.error_detectors.base import (
    BaseDetector,
    DetectionResult,
    register_detector,
)
from src.engine.error_detectors.schedule_contract import (
    evaluate_schedule_contract,
    load_installed_crontab,
)


def _finalization_self_audit(day: str) -> bool:
    """Only the live finalizer ancestor may defer its own terminal audit."""
    try:
        expected = int(os.environ.get("POSTCLOSE_FINALIZATION_DETECTOR_PARENT_PID", "0"))
        if expected <= 1 or os.environ.get("POSTCLOSE_FINALIZATION_DETECTOR_DATE") != day:
            return False
        pid = os.getppid()
        for _ in range(12):
            if pid == expected:
                argv = Path(f"/proc/{pid}/cmdline").read_bytes().split(b"\0")
                return any(arg.endswith(b"/run_postclose_finalization.sh") for arg in argv)
            if pid <= 1:
                break
            state = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
            pid = int(state[1])
    except (OSError, ValueError, IndexError):
        pass
    return False


def _today_kst() -> str:
    return date.today().isoformat()


def _now_kst_ts() -> float:
    return time.time()


def _kst_time_tuple() -> tuple[int, int]:
    now_kst = datetime.now()
    return now_kst.hour, now_kst.minute


def _disabled_job_ids() -> set[str]:
    raw = os.environ.get("KORSTOCKSCAN_DISABLED_CRON_JOBS", "")
    return {item.strip() for item in raw.split(",") if item.strip()}


def _adjacent_krx_trading_day(day: date, *, step: int) -> date:
    candidate = day
    for _ in range(14):
        candidate += timedelta(days=step)
        if is_krx_trading_day(candidate):
            return candidate
    raise ValueError("adjacent_krx_trading_day_unresolved")


CRON_INSTALL_MARKERS: dict[str, list[str]] = {
    "final_ensemble_scanner": ["final_ensemble_scanner.py"],
    "threshold_cycle_preopen": ["THRESHOLD_CYCLE_PREOPEN"],
    "buy_funnel_sentinel": ["BUY_FUNNEL_SENTINEL_"],
    "bd_fbuy_accum_pre_intraday": ["BD_FBUY_ACCUM_PRE_INTRADAY"],
    "holding_exit_sentinel": ["HOLDING_EXIT_SENTINEL_"],
    "panic_sell_defense": ["PANIC_SELL_DEFENSE_"],
    "buy_pause_guard": ["KOR_BUY_PAUSE_GUARD_"],
    "monitor_snapshot": ["RUN_MONITOR_SNAPSHOT_"],
    "swing_live_dry_run": ["SWING_LIVE_DRY_RUN"],
    "threshold_cycle_postclose": ["THRESHOLD_CYCLE_POSTCLOSE"],
    "postclose_done_controller": ["POSTCLOSE_DONE_CONTROLLER"],
    "swing_model_retrain_postclose": ["SWING_MODEL_RETRAIN_POSTCLOSE"],
    "tuning_monitoring_postclose": ["TUNING_MONITORING_POSTCLOSE"],
    "update_kospi": ["UPDATE_KOSPI_EOD_"],
    "dashboard_db_archive": ["DASHBOARD_DB_ARCHIVE_"],
    "log_rotation_cleanup": ["POSTCLOSE_FINALIZATION_"],
    "postclose_finalization": ["POSTCLOSE_FINALIZATION_"],
    "system_metric_sampler": ["SYSTEM_METRIC_SAMPLER_"],
    "error_detection_full": ["ERROR_DETECTION_FULL"],
}


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
        "status_artifact": "data/report/threshold_cycle_preopen_status/threshold_cycle_preopen_{date}.status.json",
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
        "window_start": (8, 5),
        "window_end": (19, 50),
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
        "id": "swing_live_dry_run",
        "log": "logs/swing_live_dry_run_cron.log",
        "window_start": (20, 15),
        "window_end": (20, 35),
        "mode": "once",
        "critical": False,
        "trading_day_only": True,
    },
    {
        "id": "threshold_cycle_postclose",
        "log": "logs/threshold_cycle_postclose_cron.log",
        "status_artifact": "data/report/threshold_cycle_postclose_status/threshold_cycle_postclose_{date}.status.json",
        "window_start": (20, 10),
        "window_end": (21, 40),
        "running_status_deadline": (23, 20),
        "mode": "once",
        "critical": True,
        "trading_day_only": True,
    },
    {
        "id": "postclose_done_controller",
        "log": "logs/postclose_done_controller_cron.log",
        "status_artifact": "data/report/postclose_done_controller/postclose_done_controller_{date}.json",
        "window_start": (20, 10),
        "window_end": (21, 55),
        "mode": "once",
        "critical": True,
        "trading_day_only": True,
    },
    {
        "id": "swing_model_retrain_postclose",
        "log": "logs/swing_model_retrain_cron.log",
        "window_start": (21, 10),
        "window_end": (21, 35),
        "mode": "once",
        "critical": False,
        "trading_day_only": True,
    },
    {
        "id": "tuning_monitoring_postclose",
        "log": "logs/tuning_monitoring_postclose_cron.log",
        "status_artifact": "data/report/tuning_monitoring/status/tuning_monitoring_postclose_{date}.json",
        "window_start": (20, 10),
        "window_end": (21, 55),
        "mode": "once",
        "critical": False,
        "trading_day_only": True,
    },
    {
        "id": "update_kospi",
        "log": "logs/update_kospi.log",
        "window_start": (20, 5),
        "window_end": (21, 5),
        "mode": "once",
        "critical": False,
    },
    {
        "id": "dashboard_db_archive",
        "log": "logs/dashboard_db_archive_cron.log",
        "window_start": (20, 50),
        # The producer may wait 90 minutes for exact-date EOD, then compress.
        # Keep the 22:35 detector cron after this completion deadline.
        "window_end": (22, 30),
        "mode": "once",
        "critical": False,
        "trading_day_only": True,
        "terminal_error_immediate": True,
    },
    {
        "id": "log_rotation_cleanup",
        "log": "logs/log_rotation_cleanup_cron.log",
        "window_start": (5, 0),
        "window_end": (6, 50),
        "mode": "once",
        "critical": False,
        "trading_day_only": True,
        "source_date_role": "previous_krx_trading_day",
    },
    {
        "id": "postclose_finalization",
        "log": "logs/postclose_finalization_cron.log",
        "window_start": (5, 0),
        "window_end": (6, 50),
        "mode": "once",
        "critical": True,
        "trading_day_only": True,
        "terminal_error_immediate": True,
        "source_date_role": "previous_krx_trading_day",
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
        "window_start": (7, 0),
        "window_end": (21, 59),
        "mode": "recurring",
        "interval_min": 5,
        "critical": False,
    },
]

_ERROR_MARKER = re.compile(r"\[(FAIL|ERROR|CRITICAL)\]", re.IGNORECASE)
_DONE_MARKER = re.compile(r"\[(DONE|OK|SUCCESS|COMPLETED)\]", re.IGNORECASE)
_START_MARKER = re.compile(r"\[(START|BEGIN)\]", re.IGNORECASE)
_DATE_PATTERN = re.compile(
    r"(?:target_date|started_at|finished_at)=(\d{4}-\d{2}-\d{2})"
)
_TARGET_DATE_PATTERN = re.compile(r"\btarget_date=(\d{4}-\d{2}-\d{2})\b")


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
        source_day = getattr(self, "postclose_source_date", None)
        if source_day and source_day < _today_kst():
            now_total = 24 * 60
        trading_day = is_krx_trading_day(
            date.fromisoformat(source_day) if source_day else date.today()
        )
        details: dict = {}
        issues: list[str] = []
        warnings: list[str] = []
        installed_crontab = load_installed_crontab()

        for job in CRON_JOB_REGISTRY:
            log_path = PROJECT_ROOT / job["log"]
            jid = job["id"]
            critical = job.get("critical", False)
            completed_at: datetime | None = None
            today_str = source_day or _today_kst()
            effective_day = date.fromisoformat(_today_kst())
            job_now_total = now_total
            if job.get("source_date_role") == "previous_krx_trading_day":
                job_now_total = now_h * 60 + now_m
                if source_day:
                    today_str = source_day
                    effective_day = _adjacent_krx_trading_day(
                        date.fromisoformat(source_day), step=1
                    )
                else:
                    today_str = _adjacent_krx_trading_day(
                        effective_day, step=-1
                    ).isoformat()
                current_day = date.fromisoformat(_today_kst())
                if current_day < effective_day:
                    job_now_total = -1
                elif current_day > effective_day:
                    job_now_total = 24 * 60
                details[f"{jid}_source_date"] = today_str
                details[f"{jid}_effective_date"] = effective_day.isoformat()
            if jid == "postclose_finalization" and _finalization_self_audit(today_str):
                details[f"{jid}_status"] = "pending_self_audit"
                warnings.append("postclose_finalization: live ancestor awaits this detector; no terminal PASS claimed")
                continue
            artifact_status = self._status_artifact_terminal(job, today_str)
            if jid in _disabled_job_ids():
                details[f"{jid}_status"] = "disabled_by_env"
                continue
            job_trading_day = (
                is_krx_trading_day(effective_day)
                if job.get("source_date_role") == "previous_krx_trading_day"
                else trading_day
            )
            if job.get("trading_day_only", False) and not job_trading_day:
                details[f"{jid}_status"] = "skip_non_trading_day"
                continue
            install_markers = CRON_INSTALL_MARKERS.get(jid)
            if install_markers:
                schedule_status, schedule_details = evaluate_schedule_contract(
                    installed_crontab,
                    markers=install_markers,
                )
                details[f"{jid}_schedule_contract"] = schedule_details
                if schedule_status.startswith("disabled_"):
                    details[f"{jid}_status"] = schedule_status
                    continue
            ws_h, ws_m = job["window_start"]
            we_h, we_m = job.get("window_end", (23, 59))
            if isinstance(we_h, str):
                we_h, we_m = 23, 59

            ws_total = ws_h * 60 + ws_m
            we_total = we_h * 60 + we_m
            past_window_start = job_now_total >= ws_total
            past_window_end = job_now_total > we_total

            if not past_window_start:
                details[f"{jid}_status"] = "not_yet_due"
                details[f"{jid}_window"] = (
                    f"{ws_h:02d}:{ws_m:02d}~{we_h:02d}:{we_m:02d}"
                )
                continue

            if jid == "log_rotation_cleanup":
                blocked = self._cleanup_predecessor_failure(log_path, today_str)
                if blocked:
                    details[f"{jid}_status"] = "blocked_by_finalization"
                    details[f"{jid}_predecessor"] = blocked
                    warnings.append(
                        f"{jid}: not started because postclose_finalization failed "
                        f"before cleanup ({blocked['reason']}); no cleanup PASS claimed"
                    )
                    continue

            if not log_path.exists():
                if job.get("mode", "once") == "once" and artifact_status == "done":
                    details[f"{jid}_status"] = "pass"
                    details[f"{jid}_status_artifact_terminal"] = artifact_status
                    details[f"{jid}_pass_note"] = "status artifact terminal success"
                    continue
                if artifact_status:
                    details[f"{jid}_status_artifact_terminal"] = artifact_status
                if critical and past_window_end:
                    issues.append(f"{jid}: log file missing after window end")
                    details[f"{jid}_status"] = "fail"
                elif past_window_start:
                    warnings.append(f"{jid}: log file not found (window just opened)")
                    details[f"{jid}_status"] = "warning"
                else:
                    details[f"{jid}_status"] = "not_yet_due"
                continue

            recent_lines = (
                self._read_once_markers(log_path, today_str)
                if job.get("mode", "once") == "once"
                else self._read_tail(log_path, self.MARKER_TAIL_LINES)
            )
            today_lines = self._filter_today_lines(recent_lines, today_str)
            has_matching_date = bool(today_lines)
            has_done = (
                bool(_DONE_MARKER.search(today_lines)) if has_matching_date else False
            )
            has_start = (
                bool(_START_MARKER.search(today_lines)) if has_matching_date else False
            )
            has_error = (
                bool(_ERROR_MARKER.search(today_lines))
                if has_matching_date
                else bool(_ERROR_MARKER.search(recent_lines))
            )
            if artifact_status:
                details[f"{jid}_status_artifact_terminal"] = artifact_status

            job["mode"] = job.get("mode", "once")
            if job["mode"] == "once":
                if artifact_status == "done":
                    details[f"{jid}_status"] = "pass"
                    details[f"{jid}_pass_note"] = "status artifact terminal success"
                elif artifact_status == "failed":
                    issues.append(f"{jid}: status artifact failed")
                    details[f"{jid}_status"] = "fail"
                elif job.get("terminal_error_immediate") and has_error:
                    last_marker = self._last_terminal_marker(today_lines)
                    if last_marker == "done":
                        details[f"{jid}_status"] = "pass"
                        details[f"{jid}_pass_note"] = (
                            "done over error (last terminal was DONE)"
                        )
                    else:
                        issues.append(f"{jid}: terminal failure marker observed")
                        details[f"{jid}_status"] = "fail"
                elif not has_matching_date:
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
                        details[f"{jid}_pass_note"] = (
                            "done over error (last terminal was DONE)"
                        )
                elif has_done:
                    details[f"{jid}_status"] = "pass"
                elif has_error and past_window_end:
                    issues.append(f"{jid}: finished with error after window end")
                    details[f"{jid}_status"] = "fail"
                elif self._bounded_postclose_running(job, today_str):
                    warnings.append(f"{jid}: exact-date owner running before effective-date 06:00")
                    details[f"{jid}_status"] = "in_progress"
                    details[f"{jid}_running_deadline"] = "06:00 effective date"
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

            if (job.get("source_date_role") == "previous_krx_trading_day"
                    and details.get(f"{jid}_status") == "pass"):
                owner_done = self._last_owner_done_line(today_lines, jid)
                completed_at = self._marker_finished_at(owner_done)
                cutoff = datetime_module.datetime.combine(
                    effective_day, datetime_time(we_h, we_m), ZoneInfo("Asia/Seoul")
                )
                if completed_at is None:
                    details[f"{jid}_status"] = "fail"
                    issues.append(f"{jid}: terminal completion time missing")
                elif completed_at > cutoff:
                    details[f"{jid}_status"] = "recovered_late"
                    details[f"{jid}_completed_at"] = completed_at.isoformat()
                    warnings.append(
                        f"{jid}: recovered after effective-date {we_h:02d}:{we_m:02d} cutoff"
                    )

            if (jid == "postclose_finalization" and today_str >= "2026-09-28"
                    and details.get(f"{jid}_status") in {"pass", "recovered_late"}):
                from src.engine.automation.postclose_finalization_generation import (
                    finalization_marker_issues,
                )

                done_lines = [
                    line for line in today_lines.splitlines()
                    if re.search(r"\[DONE\]\s+postclose_finalization\b", line)
                ]
                marker = done_lines[-1] if done_lines else ""
                chain = re.search(r"\bchain_sha256=([0-9a-f]{64})\b", marker)
                snapshot = re.search(
                    r"\bsnapshot_generation_sha256=([0-9a-f]{64})\b", marker
                )
                detector_run = re.search(r"\bdetector_run_id=(cron-[A-Za-z0-9-]+)\b", marker)
                detector_sha = re.search(r"\bdetector_report_sha256=([0-9a-f]{64})\b", marker)
                generation_validation = {}
                generation_issues = finalization_marker_issues(
                    PROJECT_ROOT, today_str,
                    chain.group(1) if chain else "",
                    snapshot.group(1) if snapshot else "",
                    validation_details=generation_validation,
                )
                if generation_validation:
                    details[f"{jid}_generation_validation"] = generation_validation
                if not detector_run or not detector_sha:
                    generation_issues.append("final_detector_attempt_unbound")
                if generation_issues:
                    details[f"{jid}_generation_issues"] = generation_issues
                    # The 9/28 receipt was written before this release was selected.
                    # Keep its unresolved lineage visible without failing every new run.
                    historical_unbound = (
                        today_str == "2026-09-28"
                        and not any((chain, snapshot, detector_run, detector_sha))
                        and set(generation_issues) <= {
                            "finalization_generation_unbound",
                            "final_detector_attempt_unbound",
                        }
                        and self._selected_release_after_marker(completed_at)
                    )
                    if historical_unbound:
                        details[f"{jid}_status"] = "historical_gap"
                        details[f"{jid}_historical_receipt_before_selection"] = True
                        warnings.append(
                            f"{jid}: 2026-09-28 historical generation receipt unbound"
                        )
                    else:
                        details[f"{jid}_status"] = "fail"
                        issues.append(
                            f"{jid}: finalization generation invalid ({','.join(generation_issues)})"
                        )

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
    def _bounded_postclose_running(job: dict[str, Any], today: str) -> bool:
        if (
            job.get("id") != "threshold_cycle_postclose"
            or job.get("running_status_deadline") != (23, 20)
            or not job.get("status_artifact")
        ):
            return False
        # Import at call time: artifact freshness already uses this class's
        # marker parser. Both consumers must apply the same strict pending gate.
        from .artifact_freshness import ArtifactFreshnessDetector

        artifact = {
            "id": "threshold_postclose_status",
            "running_status_deadline": job["running_status_deadline"],
            "suppress_missing_while_cron_in_progress": {
                "log": str(PROJECT_ROOT / job["log"]),
                "process_patterns": ["run_threshold_cycle_postclose.sh"],
            },
        }
        return ArtifactFreshnessDetector._is_bounded_postclose_running(
            artifact,
            PROJECT_ROOT / job["status_artifact"].format(date=today),
            today,
            datetime.fromtimestamp(_now_kst_ts()),
        )

    @staticmethod
    def _read_tail(path: Path, n: int) -> str:
        paths = CronCompletionDetector._log_bundle_paths(path)
        lines: list[str] = []
        for item in paths:
            lines.extend(CronCompletionDetector._read_tail_lines(item, n))
        return "".join(lines[-n:])

    @classmethod
    def _cleanup_predecessor_failure(cls, cleanup_path: Path, source_date: str) -> dict | None:
        def generation(path: Path) -> tuple | None:
            try:
                stat = path.stat()
                return (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)
            except FileNotFoundError:
                return ()
            except OSError:
                return None

        parent_path = PROJECT_ROOT / "logs/postclose_finalization_cron.log"
        before = (generation(cleanup_path), generation(parent_path))
        if None in before:
            return None
        # A recorded cleanup run keeps its own success/failure authority.
        if cls._read_once_markers(cleanup_path, source_date):
            return None
        markers = cls._read_once_markers(parent_path, source_date)
        if before != (generation(cleanup_path), generation(parent_path)):
            return None
        if cls._last_terminal_marker(markers) != "error":
            return None
        latest = next(
            (line for line in reversed(markers.splitlines()) if _ERROR_MARKER.search(line)),
            "",
        )
        # Only explicit pre-cleanup terminal failures prove cleanup was withheld.
        # Missing/unknown evidence and failures after cleanup remain independent.
        match = re.match(
            r"\[FAIL\]\s+postclose_finalization\b.*\breason="
            r"(predecessor_terminal_failure|predecessor_timeout|predecessor_check_error|"
            r"effective_date_hard_deadline|finish_by_cutoff_elapsed_before_summary|"
            r"summary_handoff_refresh_failed|controller_terminal_receipt_invalid|"
            r"finalization_generation_invalid|finish_by_cutoff_elapsed_before_cleanup)\b",
            latest,
        )
        if not match:
            return None
        return {
            "job_id": "postclose_finalization",
            "source_date": source_date,
            "reason": match.group(1),
            "log": str(parent_path),
            "terminal_marker": latest,
        }

    @staticmethod
    def _read_once_markers(path: Path, today_str: str) -> str:
        # Verbose report JSON must not evict the wrapper lifecycle markers.
        # Keep bounded marker memory while scanning the same rotated bundle.
        markers: deque[str] = deque(maxlen=128)
        for item in CronCompletionDetector._log_bundle_paths(path):
            try:
                with item.open("r", encoding="utf-8", errors="replace") as stream:
                    for line in stream:
                        marker = re.search(
                            r"\[(START|BEGIN|DONE|OK|SUCCESS|COMPLETED|FAIL|ERROR|CRITICAL)\]",
                            line,
                            re.IGNORECASE,
                        )
                        if marker is None:
                            continue
                        prefix = line[: marker.start()].strip()
                        if prefix and not re.fullmatch(r"[0-9T Z:+.,/\-\[\]]+", prefix):
                            continue  # JSON/text quoting a marker is not a wrapper receipt.
                        if CronCompletionDetector._filter_today_lines(line, today_str):
                            if _START_MARKER.search(line):
                                markers.clear()  # A new run supersedes old terminal evidence.
                            markers.append(line)
            except OSError:
                continue
        return "".join(markers)

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
    def _status_artifact_terminal(job: dict[str, Any], today_str: str) -> str | None:
        artifact_template = job.get("status_artifact")
        if not artifact_template:
            return None
        artifact_path = PROJECT_ROOT / str(artifact_template).format(date=today_str)
        if not artifact_path.exists():
            return None
        try:
            payload = json.loads(artifact_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
        artifact_date = str(payload.get("target_date") or payload.get("date") or "")
        if artifact_date != today_str:
            return None
        try:
            exit_code = int(payload.get("exit_code") or 0)
        except (TypeError, ValueError):
            exit_code = 1
        status = str(payload.get("status") or "").lower()
        manual_recovery = (
            payload.get("manual_recovery")
            if isinstance(payload.get("manual_recovery"), dict)
            else {}
        )
        verification_status = str(
            manual_recovery.get("verification_status") or ""
        ).lower()
        if exit_code == 0 and status in {
            "succeeded",
            "success",
            "passed",
            "pass",
            "completed",
            "done",
            "skipped",
            "skip",
            "disabled",
            "disabled_by_parent",
        }:
            return "done"
        if exit_code == 0 and verification_status == "pass_with_pending_done_marker":
            return "done"
        if status in {"failed", "fail", "error"}:
            return "failed"
        return None

    @staticmethod
    def _filter_today_lines(text: str, today_str: str) -> str:
        today_lines: list[str] = []
        for line in text.splitlines():
            target_match = _TARGET_DATE_PATTERN.search(line)
            if target_match:
                # Recovery can finish after midnight. Explicit source date
                # owns the receipt, regardless of its wall-clock timestamp.
                if target_match.group(1) == today_str:
                    today_lines.append(line)
                continue
            match = _DATE_PATTERN.search(line)
            if match and match.group(1) == today_str:
                today_lines.append(line)
            elif CronCompletionDetector._line_has_today_timestamp(line, today_str):
                today_lines.append(line)
        return "\n".join(today_lines)

    @staticmethod
    def _line_has_today_timestamp(line: str, today_str: str) -> bool:
        return today_str in line and (
            _DONE_MARKER.search(line)
            or _ERROR_MARKER.search(line)
            or _START_MARKER.search(line)
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
    def _last_owner_done_line(today_lines: str, owner: str) -> str:
        pattern = re.compile(rf"^\[DONE\]\s+{re.escape(owner)}\b")
        return next(
            (line for line in reversed(today_lines.splitlines()) if pattern.search(line)),
            "",
        )

    @staticmethod
    def _marker_finished_at(line: str) -> datetime | None:
        match = re.search(r"\bfinished_at=(\S+)", line)
        if match is None:
            return None
        try:
            completed_at = datetime_module.datetime.fromisoformat(match.group(1))
        except ValueError:
            return None
        return completed_at if completed_at.tzinfo is not None else None

    @staticmethod
    def _selected_release_after_marker(completed_at: datetime | None) -> bool:
        if completed_at is None:
            return False
        path = PROJECT_ROOT / "data/runtime/runtime_release_selection.json"
        try:
            selected_at = datetime_module.datetime.fromisoformat(
                json.loads(path.read_text(encoding="utf-8"))["selected_at_kst"]
            )
            return selected_at.tzinfo is not None and completed_at < selected_at
        except (OSError, KeyError, ValueError, TypeError, json.JSONDecodeError):
            return False

    @staticmethod
    def _classify(issues: list[str], warnings: list[str]) -> tuple[str, str]:
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
