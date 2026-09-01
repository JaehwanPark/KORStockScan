from __future__ import annotations

import json
import os
import subprocess
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
SAMSUNG_MORNING_AUTHORITY_PATH = (
    PROJECT_ROOT / "data" / "runtime" / "samsung_morning_one_share_authority.json"
)
_HEARTBEAT_LOCK = threading.Lock()
_SNIPER_NORMAL_MARKET_CLOSE_MINUTE = 20 * 60
_SAMSUNG_MORNING_START_MINUTE = 7 * 60 + 57
_SAMSUNG_MORNING_ACCEPTANCE_DEADLINE_MINUTE = 8 * 60 + 5
_SAMSUNG_MORNING_LIVE_UNIT = "korstockscan-samsung-morning-one-share.service"
_SAMSUNG_MORNING_PREFLIGHT_UNIT = "korstockscan-samsung-one-share-preflight.service"
_SAMSUNG_MORNING_TIMER_UNIT = "korstockscan-samsung-morning-one-share.timer"
_SAMSUNG_MORNING_AUTHORITY_SCHEMA = "samsung_morning_two_episode_authority_v7"


def reset_heartbeat():
    """Start a new bot_main heartbeat session and discard stale thread entries."""
    HEARTBEAT_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = HEARTBEAT_PATH.with_suffix(HEARTBEAT_PATH.suffix + ".tmp")
    with _HEARTBEAT_LOCK:
        tmp_path.write_text("{}", encoding="utf-8")
        os.replace(tmp_path, HEARTBEAT_PATH)


def write_heartbeat(
    component: str,
    alive: bool = True,
    *,
    terminal_reason: str | None = None,
):
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
            previous = threads.get(component, {})
            heartbeat = {"last_beat": now_iso, "alive": alive}
            if not alive:
                if terminal_reason:
                    heartbeat["terminal_reason"] = str(terminal_reason)
                elif previous.get("terminal_reason"):
                    # The sniper's finally block repeats alive=False. Preserve an
                    # explicit normal-stop reason written by the owning branch.
                    heartbeat["terminal_reason"] = previous["terminal_reason"]
            threads[component] = heartbeat
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
        samsung_morning = _samsung_morning_runtime_contract(
            datetime.fromtimestamp(now_ts).astimezone()
        )
        result = self._check_main_runtime(
            now_ts=now_ts,
            samsung_morning=samsung_morning,
        )
        result.details["samsung_morning_runtime"] = samsung_morning
        samsung_severity = samsung_morning.get("severity")
        if samsung_severity == "fail":
            samsung_summary = (
                "Samsung morning expected runtime is not healthy: "
                f"{samsung_morning.get('reason') or 'unknown'}."
            )
            if result.severity == "fail":
                result.summary = f"{result.summary} {samsung_summary}"
            else:
                result.summary = samsung_summary
            result.severity = "fail"
            result.recommended_action = (
                f"{result.recommended_action} "
                "Inspect the exact-date authority and preflight/live systemd "
                "transaction; do not bypass runtime-env or broker safety guards."
            ).strip()
        elif samsung_severity == "warning" and result.severity != "fail":
            result.severity = "warning"
            result.summary = (
                f"{result.summary} Samsung morning runtime is still within its "
                "bounded startup acceptance window."
            )
            result.recommended_action = (
                f"{result.recommended_action} Recheck the same systemd transaction "
                "at the 08:05 KST acceptance deadline; do not start a duplicate owner."
            ).strip()
        return result

    def _check_main_runtime(
        self,
        *,
        now_ts: float,
        samsung_morning: dict,
    ) -> DetectionResult:
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
        details["samsung_morning_runtime"] = samsung_morning
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
                expected_start_ts = (
                    now_ts - seconds_since_start
                    if seconds_since_start is not None
                    else None
                )
                heartbeat_predates_expected_start = bool(
                    main_beat is not None
                    and expected_start_ts is not None
                    and main_beat < expected_start_ts
                )
                details["heartbeat_predates_expected_start"] = (
                    heartbeat_predates_expected_start
                )
                if not expected_running:
                    return DetectionResult(
                        detector_id=self.id,
                        category=self.category,
                        severity="pass",
                        summary="bot_main.py PID is dead outside expected runtime window.",
                        details=details,
                    )
                if in_startup_grace:
                    if heartbeat_predates_expected_start:
                        details["main_loop_status"] = (
                            "startup_grace_prior_run_heartbeat"
                        )
                    return DetectionResult(
                        detector_id=self.id,
                        category=self.category,
                        severity="warning",
                        summary=(
                            "No heartbeat from today's bot startup yet; "
                            f"latest heartbeat belongs to prior-run PID {pid}."
                            if heartbeat_predates_expected_start
                            else f"bot_main.py heartbeat PID {pid} is stale during startup grace window."
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
                if heartbeat_predates_expected_start:
                    details["main_loop_status"] = "startup_not_observed"
                    return DetectionResult(
                        detector_id=self.id,
                        category=self.category,
                        severity="fail",
                        summary=(
                            "No heartbeat was observed for today's expected bot startup; "
                            f"latest heartbeat belongs to prior-run PID {pid}."
                        ),
                        details=details,
                        recommended_action=(
                            "Inspect the launcher and PREOPEN handoff verification before "
                            "attempting a guarded bot restart."
                        ),
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
            terminal_reason = str(tdata.get("terminal_reason") or "").strip()
            if terminal_reason:
                details.setdefault("thread_terminal_reason", {})[
                    tname
                ] = terminal_reason
            if not talive:
                if _is_expected_thread_terminal(
                    tname,
                    tdata,
                    now_ts=now_ts,
                ):
                    details.setdefault("expected_stopped_threads", []).append(tname)
                    continue
                details.setdefault("stopped_threads", []).append(tname)
                thread_issues.append(tname)
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

        expected_stopped = details.get("expected_stopped_threads", [])
        details["thread_status"] = "expected_terminal" if expected_stopped else "ok"
        return DetectionResult(
            detector_id=self.id,
            category=self.category,
            severity="pass",
            summary=(
                "All required processes healthy; expected terminal threads: "
                + ", ".join(expected_stopped)
                if expected_stopped
                else "All processes and threads healthy."
            ),
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


def _is_expected_thread_terminal(
    component: str,
    thread_state: dict,
    *,
    now_ts: float,
) -> bool:
    """Recognize only owner-declared, time-valid normal thread completion."""
    if component != "sniper_engine":
        return False
    if str(thread_state.get("terminal_reason") or "") != "market_close":
        return False

    terminal_ts = _parse_iso(str(thread_state.get("last_beat") or ""))
    if terminal_ts is None:
        return False
    now_dt = datetime.fromtimestamp(now_ts).astimezone()
    terminal_dt = datetime.fromtimestamp(terminal_ts).astimezone()
    if terminal_dt.date() != now_dt.date():
        return False

    now_minutes = now_dt.hour * 60 + now_dt.minute
    terminal_minutes = terminal_dt.hour * 60 + terminal_dt.minute
    return (
        now_minutes >= _SNIPER_NORMAL_MARKET_CLOSE_MINUTE
        and terminal_minutes >= _SNIPER_NORMAL_MARKET_CLOSE_MINUTE
    )


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


def _samsung_morning_runtime_contract(now: datetime) -> dict:
    """Read-only expected-set check for the 07:57 Samsung morning owner."""

    target_date = now.date().isoformat()
    current_minute = now.hour * 60 + now.minute
    details: dict = {
        "target_date": target_date,
        "expected_start": "07:57",
        "acceptance_deadline": "08:05",
        "runtime_effect": False,
        "runtime_mutation": "none",
    }
    if not is_krx_trading_day(now.date()):
        return {**details, "severity": "pass", "status": "not_applicable"}
    if current_minute < _SAMSUNG_MORNING_START_MINUTE:
        return {**details, "severity": "pass", "status": "not_yet_due"}

    timer_state = _systemd_unit_state(_SAMSUNG_MORNING_TIMER_UNIT)
    preflight_state = _systemd_unit_state(_SAMSUNG_MORNING_PREFLIGHT_UNIT)
    live_state = _systemd_unit_state(_SAMSUNG_MORNING_LIVE_UNIT)
    details.update(
        {
            "timer": timer_state,
            "preflight": preflight_state,
            "live": live_state,
        }
    )
    authority, authority_error = _load_samsung_morning_authority()
    live_completed_for_target_date = _unit_completed_successfully(
        live_state,
        target_date=target_date,
    )
    authority_ready, authority_contract_reason = _samsung_authority_contract_ready(
        authority,
        authority_error=authority_error,
        target_date=target_date,
        now=now,
        require_bound_main_bot_active=not live_completed_for_target_date,
    )
    details["authority"] = {
        "path": str(SAMSUNG_MORNING_AUTHORITY_PATH),
        "target_date": authority.get("target_date"),
        "status": authority.get("status"),
        "ready": authority_ready,
        "error": authority_error,
        "contract_reason": authority_contract_reason,
    }

    unit_query_errors = [
        state.get("query_error")
        for state in (timer_state, preflight_state, live_state)
        if state.get("query_error")
    ]
    if unit_query_errors:
        reason = "systemd_expected_set_unreadable"
    elif timer_state.get("LoadState") != "loaded":
        reason = "morning_timer_not_installed"
    elif preflight_state.get("LoadState") != "loaded":
        reason = "morning_preflight_not_installed"
    elif live_state.get("LoadState") != "loaded":
        reason = "morning_live_service_not_installed"
    elif timer_state.get("UnitFileState") != "enabled":
        reason = "morning_timer_not_enabled"
    elif (
        _SAMSUNG_MORNING_LIVE_UNIT not in str(timer_state.get("Triggers") or "").split()
    ):
        reason = "morning_timer_trigger_contract_mismatch"
    elif any(
        state.get("User") != "ubuntu" or state.get("Group") != "ubuntu"
        for state in (preflight_state, live_state)
    ):
        reason = "morning_service_credential_contract_mismatch"
    elif timer_state.get("ActiveState") != "active":
        reason = "morning_timer_not_active"
    elif (
        live_state.get("ActiveState") == "failed"
        or live_state.get("Result") == "failed"
    ):
        reason = "morning_live_service_failed"
    elif (
        preflight_state.get("ActiveState") == "failed"
        or preflight_state.get("Result") == "failed"
    ):
        reason = "morning_preflight_failed"
    elif not authority_ready:
        reason = authority_contract_reason
    elif not _unit_started_on_target_date(preflight_state, target_date):
        reason = "morning_preflight_not_started_for_target_date"
    elif _unit_active_running(live_state, target_date=target_date):
        return {
            **details,
            "severity": "pass",
            "status": "healthy_active",
            "reason": "exact_date_authority_and_live_process_ready",
        }
    elif live_completed_for_target_date:
        return {
            **details,
            "severity": "pass",
            "status": "one_shot_completed",
            "reason": "exact_date_authority_and_terminal_service_success",
        }
    else:
        reason = "morning_live_service_not_started"

    waitable_reasons = {
        "exact_date_authority_missing_or_stale",
        "exact_date_authority_not_ready",
        "morning_preflight_not_started_for_target_date",
        "morning_live_service_not_started",
    }
    if (
        current_minute < _SAMSUNG_MORNING_ACCEPTANCE_DEADLINE_MINUTE
        and reason in waitable_reasons
    ):
        return {
            **details,
            "severity": "warning",
            "status": "bounded_wait",
            "reason": reason,
        }
    return {
        **details,
        "severity": "fail",
        "status": "expected_process_not_healthy",
        "reason": reason,
    }


def _systemd_unit_state(unit: str) -> dict[str, str | int | None]:
    properties = (
        "LoadState,UnitFileState,ActiveState,SubState,Result,MainPID,"
        "ExecMainStatus,ExecMainStartTimestamp,Job,JobType,JobState,"
        "Triggers,User,Group"
    )
    try:
        completed = subprocess.run(
            [
                "/bin/systemctl",
                "show",
                unit,
                f"--property={properties}",
                "--no-pager",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=3,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"unit": unit, "query_error": type(exc).__name__}
    if completed.returncode != 0:
        return {
            "unit": unit,
            "query_error": "systemctl_show_failed",
            "returncode": completed.returncode,
        }
    state: dict[str, str | int | None] = {"unit": unit}
    for line in completed.stdout.splitlines():
        key, separator, value = line.partition("=")
        if not separator:
            continue
        if key in {"MainPID", "ExecMainStatus"}:
            try:
                state[key] = int(value)
            except ValueError:
                state[key] = None
        else:
            state[key] = value
    return state


def _load_samsung_morning_authority() -> tuple[dict, str | None]:
    try:
        payload = json.loads(SAMSUNG_MORNING_AUTHORITY_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}, "not_found"
    except json.JSONDecodeError:
        return {}, "invalid_json"
    except OSError as exc:
        return {}, type(exc).__name__
    if not isinstance(payload, dict):
        return {}, "not_object"
    return payload, None


def _samsung_authority_contract_ready(
    authority: dict,
    *,
    authority_error: str | None,
    target_date: str,
    now: datetime,
    require_bound_main_bot_active: bool = True,
) -> tuple[bool, str]:
    if authority_error == "not_found":
        return False, "exact_date_authority_missing_or_stale"
    if authority_error:
        return False, "exact_date_authority_unreadable"
    if authority.get("target_date") != target_date:
        return False, "exact_date_authority_missing_or_stale"
    if authority.get("schema") != _SAMSUNG_MORNING_AUTHORITY_SCHEMA:
        return False, "exact_date_authority_schema_invalid"
    if authority.get("status") != "ready":
        return False, "exact_date_authority_not_ready"
    if (
        authority.get("decision_authority")
        != "explicit_user_directed_morning_two_episode_live_start"
        or authority.get("source_quality_gate") != "PASS"
        or authority.get("runtime_effect") is not True
        or authority.get("actual_order_submitted") is not False
        or authority.get("broker_order_forbidden") is not False
    ):
        return False, "exact_date_authority_runtime_contract_invalid"
    policy = authority.get("policy")
    if (
        not isinstance(policy, dict)
        or policy.get("symbol") != "005930"
        or policy.get("quantity") != 20
        or policy.get("allocation")
        != "ten_shares_base_limit_and_ten_shares_base_plus_1tick"
        or policy.get("maximum_episodes_per_day") != 2
        or policy.get("unfilled_target") != "hold_position_without_forced_exit"
        or "max_hold_minutes" in policy
    ):
        return False, "exact_date_authority_policy_invalid"
    rollback = authority.get("rollback")
    if (
        not isinstance(rollback, dict)
        or rollback.get("action")
        != "fail_closed_and_disable_only_morning_two_leg_timer_and_services"
        or rollback.get("widget_service_effect") != "none"
    ):
        return False, "exact_date_authority_rollback_invalid"
    try:
        observed_at = datetime.fromisoformat(
            str(authority.get("observed_at_kst") or "")
        )
        valid_until = datetime.fromisoformat(
            str(authority.get("valid_until_kst") or "")
        )
    except ValueError:
        return False, "exact_date_authority_time_invalid"
    if observed_at.tzinfo is None or valid_until.tzinfo is None:
        return False, "exact_date_authority_time_invalid"
    observed_at = observed_at.astimezone(now.tzinfo)
    valid_until = valid_until.astimezone(now.tzinfo)
    if observed_at.date().isoformat() != target_date or observed_at > now:
        return False, "exact_date_authority_observation_invalid"
    if now > valid_until or valid_until.date().isoformat() != target_date:
        return False, "exact_date_authority_expired"
    decision = authority.get("decision")
    if not isinstance(decision, dict):
        return False, "exact_date_authority_decision_invalid"
    main_bot_pid = decision.get("main_bot_pid")
    if (
        decision.get("ready") is not True
        or decision.get("target_date") != target_date
        or decision.get("main_bot_active") is not True
        or decision.get("main_bot_runtime_env_verified") is not True
        or decision.get("shared_token_available") is not True
        or not str(decision.get("operator_exclusion_source") or "").strip()
        or decision.get("prior_reentry_state_clear") is not True
        or decision.get("parallel_widget_trading_allowed") is not True
        or decision.get("independent_order_ledger_required") is not True
        or decision.get("blockers") != []
        or isinstance(main_bot_pid, bool)
        or not isinstance(main_bot_pid, int)
        or main_bot_pid <= 0
    ):
        return False, "exact_date_authority_decision_invalid"
    if require_bound_main_bot_active and not _pid_cmdline_contains_bot_main(
        main_bot_pid
    ):
        return False, "exact_date_authority_main_bot_pid_inactive"
    return True, "ready"


def _pid_cmdline_contains_bot_main(
    pid: int, *, proc_root: Path = Path("/proc")
) -> bool:
    try:
        cmdline = (proc_root / str(pid) / "cmdline").read_bytes()
    except OSError:
        return False
    return any(
        Path(token.decode("utf-8", errors="replace")).name == "bot_main.py"
        for token in cmdline.split(b"\0")
        if token
    )


def _unit_started_on_target_date(state: dict, target_date: str) -> bool:
    start_timestamp = str(state.get("ExecMainStartTimestamp") or "")
    return target_date in start_timestamp


def _unit_active_running(state: dict, *, target_date: str) -> bool:
    return bool(
        state.get("ActiveState") == "active"
        and state.get("SubState") == "running"
        and isinstance(state.get("MainPID"), int)
        and state.get("MainPID") > 0
        and _unit_started_on_target_date(state, target_date)
    )


def _unit_completed_successfully(state: dict, *, target_date: str) -> bool:
    return bool(
        state.get("ActiveState") == "inactive"
        and state.get("SubState") == "dead"
        and state.get("Result") == "success"
        and state.get("ExecMainStatus") == 0
        and _unit_started_on_target_date(state, target_date)
    )


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
