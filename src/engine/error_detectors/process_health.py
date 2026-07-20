from __future__ import annotations

import json
import os
import threading
import time
from datetime import datetime
from pathlib import Path

from src.utils.constants import PROJECT_ROOT, TRADING_RULES
from src.utils.market_day import is_krx_trading_day

from src.engine.error_detectors.base import (
    BaseDetector,
    DetectionResult,
    register_detector,
)

HEARTBEAT_PATH = PROJECT_ROOT / "tmp" / "error_detector_heartbeat.json"
POSTCLOSE_BOT_ISOLATION_PATH = PROJECT_ROOT / "tmp" / "postclose_bot_isolation.json"
_HEARTBEAT_LOCK = threading.Lock()


def reset_heartbeat():
    """Start a new bot_main heartbeat session and discard stale thread entries."""
    HEARTBEAT_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = HEARTBEAT_PATH.with_suffix(HEARTBEAT_PATH.suffix + ".tmp")
    with _HEARTBEAT_LOCK:
        tmp_path.write_text("{}", encoding="utf-8")
        os.replace(tmp_path, HEARTBEAT_PATH)


def write_heartbeat(component: str, alive: bool = True):
    HEARTBEAT_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = HEARTBEAT_PATH.with_suffix(HEARTBEAT_PATH.suffix + ".tmp")
    with _HEARTBEAT_LOCK:
        state = {}
        if HEARTBEAT_PATH.exists():
            try:
                state = json.loads(HEARTBEAT_PATH.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                state = {}
        now_iso = datetime.now().astimezone().isoformat(timespec="seconds")
        if component == "main_loop":
            state["main_loop"] = {"last_beat": now_iso, "pid": os.getpid()}
        else:
            threads = state.setdefault("threads", {})
            threads[component] = {"last_beat": now_iso, "alive": alive}
        tmp_path.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp_path, HEARTBEAT_PATH)


@register_detector
class ProcessHealthDetector(BaseDetector):
    id = "process_health"
    name = "Process Health Detector"
    category = "process"

    @property
    def main_loop_timeout_sec(self) -> int:
        return int(
            getattr(TRADING_RULES, "ERROR_DETECTOR_PROCESS_MAIN_LOOP_TIMEOUT_SEC", 15)
        )

    @property
    def thread_timeout_sec(self) -> int:
        return int(
            getattr(TRADING_RULES, "ERROR_DETECTOR_PROCESS_THREAD_TIMEOUT_SEC", 7200)
        )

    @property
    def restart_grace_sec(self) -> int:
        return int(
            getattr(TRADING_RULES, "ERROR_DETECTOR_PROCESS_RESTART_GRACE_SEC", 30)
        )

    @property
    def startup_grace_sec(self) -> int:
        return int(getattr(TRADING_RULES, "ERROR_DETECTOR_BOT_STARTUP_GRACE_SEC", 180))

    @property
    def postclose_isolation_max_age_sec(self) -> int:
        return int(
            getattr(
                TRADING_RULES,
                "ERROR_DETECTOR_POSTCLOSE_BOT_ISOLATION_MAX_AGE_SEC",
                28800,
            )
        )

    def check(self) -> DetectionResult:
        now_ts = time.time()
        details: dict = {}
        main_loop_timeout = self.main_loop_timeout_sec
        thread_timeout = self.thread_timeout_sec
        restart_grace = self.restart_grace_sec
        startup_grace = self.startup_grace_sec
        expected_running = _is_bot_expected_running()
        details["bot_expected_running"] = expected_running
        details["bot_expected_window"] = {
            "start": getattr(
                TRADING_RULES, "ERROR_DETECTOR_BOT_EXPECTED_START_HHMM", "07:55"
            ),
            "end": getattr(
                TRADING_RULES, "ERROR_DETECTOR_BOT_EXPECTED_END_HHMM", "20:10"
            ),
        }
        details["restart_grace_sec"] = restart_grace
        details["startup_grace_sec"] = startup_grace
        seconds_since_start = _seconds_since_expected_start()
        if seconds_since_start is not None:
            details["seconds_since_expected_start"] = round(seconds_since_start, 1)
        in_startup_grace = (
            expected_running
            and startup_grace > 0
            and seconds_since_start is not None
            and 0 <= seconds_since_start < startup_grace
        )
        postclose_isolation = _load_postclose_bot_isolation(
            now_ts=now_ts,
            max_age_sec=self.postclose_isolation_max_age_sec,
        )
        if postclose_isolation:
            details["postclose_bot_isolation"] = postclose_isolation

        if not HEARTBEAT_PATH.exists():
            if not expected_running:
                details["main_loop_status"] = "expected_stopped"
                details["heartbeat_path"] = str(HEARTBEAT_PATH)
                return DetectionResult(
                    detector_id=self.id,
                    category=self.category,
                    severity="pass",
                    summary="bot_main.py is outside expected runtime window.",
                    details=details,
                )
            if in_startup_grace:
                details["main_loop_status"] = "startup_grace_waiting"
                details["heartbeat_path"] = str(HEARTBEAT_PATH)
                return DetectionResult(
                    detector_id=self.id,
                    category=self.category,
                    severity="warning",
                    summary="Heartbeat file not found during bot startup grace window.",
                    details=details,
                    recommended_action="Recheck after startup grace before restarting bot_main.py.",
                )
            if postclose_isolation:
                details["main_loop_status"] = "postclose_isolation_no_heartbeat"
                details["heartbeat_path"] = str(HEARTBEAT_PATH)
                return self._postclose_isolation_warning(
                    "Heartbeat file not found while postclose bot resource isolation is active.",
                    details,
                )
            return DetectionResult(
                detector_id=self.id,
                category=self.category,
                severity="fail",
                summary="Heartbeat file not found. bot_main.py may not be running.",
                details={**details, "heartbeat_path": str(HEARTBEAT_PATH)},
                recommended_action="Check bot_main.py process status and restart if needed.",
            )

        try:
            state = json.loads(HEARTBEAT_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            return DetectionResult(
                detector_id=self.id,
                category=self.category,
                severity="fail",
                summary=f"Cannot read heartbeat file: {e}",
                details={"heartbeat_path": str(HEARTBEAT_PATH), "error": str(e)},
                recommended_action="Check file permissions and disk health.",
            )

        main_loop = state.get("main_loop")
        thread_issues: list[str] = []
        pid_ok = True

        if main_loop:
            main_beat = _parse_iso(main_loop.get("last_beat", ""))
            main_age = now_ts - main_beat if main_beat else float("inf")
            details["main_loop_age_sec"] = round(main_age, 1)
            details["main_loop_pid"] = main_loop.get("pid")

            pid = main_loop.get("pid")
            if pid:
                pid_alive = _pid_exists(pid)
                details["main_loop_pid_alive"] = pid_alive
                if not pid_alive:
                    pid_ok = False

            if not pid_ok:
                details["main_loop_status"] = "pid_dead"
                if not expected_running:
                    return DetectionResult(
                        detector_id=self.id,
                        category=self.category,
                        severity="pass",
                        summary="bot_main.py PID is dead outside expected runtime window.",
                        details=details,
                    )
                if in_startup_grace:
                    return DetectionResult(
                        detector_id=self.id,
                        category=self.category,
                        severity="warning",
                        summary=(
                            f"bot_main.py heartbeat PID {pid} is stale during startup grace window."
                        ),
                        details=details,
                        recommended_action="Recheck after startup grace before restarting bot_main.py.",
                    )
                if restart_grace > 0 and main_age <= restart_grace:
                    details["main_loop_status"] = "restart_grace_pid_handoff"
                    return DetectionResult(
                        detector_id=self.id,
                        category=self.category,
                        severity="warning",
                        summary=(
                            f"bot_main.py heartbeat PID {pid} is dead, but heartbeat age "
                            f"{main_age:.0f}s is within restart grace."
                        ),
                        details=details,
                        recommended_action="Recheck shortly; do not restart again unless grace expires.",
                    )
                if postclose_isolation:
                    details["main_loop_status"] = "postclose_isolation_pid_dead"
                    return self._postclose_isolation_warning(
                        f"bot_main.py PID {pid} is intentionally stopped for postclose resource isolation.",
                        details,
                    )
                return DetectionResult(
                    detector_id=self.id,
                    category=self.category,
                    severity="fail",
                    summary=f"bot_main.py PID {pid} is no longer alive. Main process may have died.",
                    details=details,
                    recommended_action="Restart bot_main.py immediately.",
                )
            if main_age > main_loop_timeout:
                details["main_loop_status"] = "stale"
                if not expected_running:
                    return DetectionResult(
                        detector_id=self.id,
                        category=self.category,
                        severity="pass",
                        summary="Main loop heartbeat is stale outside expected runtime window.",
                        details=details,
                    )
                if in_startup_grace:
                    return DetectionResult(
                        detector_id=self.id,
                        category=self.category,
                        severity="warning",
                        summary=f"Main loop heartbeat stale during startup grace window ({main_age:.0f}s).",
                        details=details,
                        recommended_action="Recheck after startup grace before restarting bot_main.py.",
                    )
                if postclose_isolation:
                    details["main_loop_status"] = "postclose_isolation_stale"
                    return self._postclose_isolation_warning(
                        f"Main loop heartbeat stale for {main_age:.0f}s while postclose isolation is active.",
                        details,
                    )
                return DetectionResult(
                    detector_id=self.id,
                    category=self.category,
                    severity="fail",
                    summary=f"Main loop heartbeat stale for {main_age:.0f}s (timeout={main_loop_timeout}s).",
                    details=details,
                    recommended_action="Check main loop for deadlock or crash.",
                )
            details["main_loop_status"] = "ok"
        else:
            if not expected_running:
                details["main_loop_status"] = "expected_stopped"
                return DetectionResult(
                    detector_id=self.id,
                    category=self.category,
                    severity="pass",
                    summary="No main_loop heartbeat entry outside expected runtime window.",
                    details=details,
                )
            if in_startup_grace:
                details["main_loop_status"] = "startup_grace_waiting"
                return DetectionResult(
                    detector_id=self.id,
                    category=self.category,
                    severity="warning",
                    summary="No main_loop heartbeat entry found during startup grace window.",
                    details=details,
                    recommended_action="Recheck after startup grace before restarting bot_main.py.",
                )
            if postclose_isolation:
                details["main_loop_status"] = "postclose_isolation_no_main_loop"
                return self._postclose_isolation_warning(
                    "No main_loop heartbeat entry while postclose bot resource isolation is active.",
                    details,
                )
            return DetectionResult(
                detector_id=self.id,
                category=self.category,
                severity="fail",
                summary="No main_loop heartbeat entry found.",
                details=details,
                recommended_action="Verify bot_main.py is running with heartbeat instrumentation.",
            )

        threads = state.get("threads", {})
        if not threads:
            details["thread_count"] = 0
            details["thread_status"] = "no_threads"
            return DetectionResult(
                detector_id=self.id,
                category=self.category,
                severity="warning",
                summary="No thread heartbeats found. Threads may not have started.",
                details=details,
                recommended_action="Check bot_main.py startup logs for thread launch failures.",
            )

        for tname, tdata in threads.items():
            tbeat = _parse_iso(tdata.get("last_beat", ""))
            tage = now_ts - tbeat if tbeat else float("inf")
            talive = tdata.get("alive", True)
            details.setdefault("thread_age_sec", {})[tname] = round(tage, 1)
            details.setdefault("thread_alive", {})[tname] = talive
            if not talive:
                details.setdefault("stopped_threads", []).append(tname)
            elif tage > thread_timeout:
                thread_issues.append(tname)

        if thread_issues:
            details["stale_threads"] = thread_issues
            details["thread_status"] = "stale"
            return DetectionResult(
                detector_id=self.id,
                category=self.category,
                severity="fail",
                summary=f"Stale or dead threads detected: {', '.join(thread_issues)}",
                details=details,
                recommended_action="Investigate thread health. Restart bot_main.py if needed.",
            )

        details["thread_status"] = "ok"
        return DetectionResult(
            detector_id=self.id,
            category=self.category,
            severity="pass",
            summary="All processes and threads healthy.",
            details=details,
        )

    def _postclose_isolation_warning(
        self, summary: str, details: dict
    ) -> DetectionResult:
        details["postclose_bot_isolation_marker_path"] = str(
            POSTCLOSE_BOT_ISOLATION_PATH
        )
        return DetectionResult(
            detector_id=self.id,
            category=self.category,
            severity="pass",
            summary=summary,
            details=details,
            recommended_action=(
                "No immediate restart. The postclose wrapper owns bot stop/isolation after market close."
            ),
        )


def _parse_iso(iso_str: str) -> float | None:
    if not iso_str:
        return None
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.timestamp()
    except (ValueError, TypeError):
        return None


def _load_postclose_bot_isolation(now_ts: float, max_age_sec: int) -> dict | None:
    if max_age_sec <= 0 or not POSTCLOSE_BOT_ISOLATION_PATH.exists():
        return None
    try:
        payload = json.loads(POSTCLOSE_BOT_ISOLATION_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if not payload.get("active"):
        return None
    started_ts = _parse_iso(str(payload.get("started_at") or ""))
    if started_ts is None:
        return None
    age_sec = now_ts - started_ts
    if age_sec < 0 or age_sec > max_age_sec:
        return None
    return {
        "status": "active",
        "age_sec": round(age_sec, 1),
        "max_age_sec": max_age_sec,
        "target_date": payload.get("target_date"),
        "session": payload.get("session"),
        "action": payload.get("action"),
        "reason": payload.get("reason"),
        "started_at": payload.get("started_at"),
    }


def _is_bot_expected_running(now: datetime | None = None) -> bool:
    enabled = bool(
        getattr(
            TRADING_RULES, "ERROR_DETECTOR_BOT_EXPECTED_RUNTIME_WINDOW_ENABLED", True
        )
    )
    if not enabled:
        return True
    current = now or datetime.now().astimezone()
    if not is_krx_trading_day(current.date()):
        return False
    start = _parse_hhmm(
        getattr(TRADING_RULES, "ERROR_DETECTOR_BOT_EXPECTED_START_HHMM", "07:55")
    )
    end = _parse_hhmm(
        getattr(TRADING_RULES, "ERROR_DETECTOR_BOT_EXPECTED_END_HHMM", "20:10")
    )
    if start is None or end is None:
        return True
    current_minutes = current.hour * 60 + current.minute
    if start <= end:
        return start <= current_minutes < end
    return current_minutes >= start or current_minutes < end


def _seconds_since_expected_start(now: datetime | None = None) -> float | None:
    enabled = bool(
        getattr(
            TRADING_RULES, "ERROR_DETECTOR_BOT_EXPECTED_RUNTIME_WINDOW_ENABLED", True
        )
    )
    if not enabled:
        return None
    current = now or datetime.now().astimezone()
    start = _parse_hhmm(
        getattr(TRADING_RULES, "ERROR_DETECTOR_BOT_EXPECTED_START_HHMM", "07:55")
    )
    if start is None:
        return None
    start_dt = current.replace(
        hour=start // 60, minute=start % 60, second=0, microsecond=0
    )
    return (current - start_dt).total_seconds()


def _parse_hhmm(value: str) -> int | None:
    try:
        hour_raw, minute_raw = str(value).strip().split(":", 1)
        hour = int(hour_raw)
        minute = int(minute_raw)
    except (TypeError, ValueError):
        return None
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        return None
    return hour * 60 + minute


def _pid_exists(pid: int) -> bool:
    if not pid or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False
