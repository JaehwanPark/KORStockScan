from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime
from pathlib import Path

from src.engine.error_detectors.base import (
    BaseDetector,
    DetectionResult,
    register_detector,
)
from src.utils.constants import LOGS_DIR, PROJECT_ROOT, TRADING_RULES
from src.utils import kiwoom_utils

SCAN_STATE_PATH = PROJECT_ROOT / "tmp" / "error_detector_kiwoom_auth_8005_state.json"
RESTART_FLAG_PATH = PROJECT_ROOT / "restart.flag"
HEARTBEAT_PATH = PROJECT_ROOT / "tmp" / "error_detector_heartbeat.json"
PROC_ROOT = Path("/proc")

_EXPLICIT_LOG_NAMES = {
    "bot_history.log",
    "kiwoom_utils_error.log",
    "kiwoom_utils_info.log",
    "kiwoom_websocket_error.log",
    "kiwoom_sniper_v2_error.log",
    "sniper_state_handlers_error.log",
}
_IGNORED_LINE_PATTERNS: list[re.Pattern] = [
    re.compile(r"\[ERROR_DETECTION\]"),
    re.compile(r"\bTEST(?:\b|[:(])"),
    re.compile(r"\b123456\b"),
    re.compile(r"_DummySession"),
    re.compile(r"\brun_error_detection\b"),
]
_LOG_TIMESTAMP_PATTERN = re.compile(r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]")
_AUTH_RECOVERY_PATTERN = re.compile(
    r"\[TOKEN HANDOFF\].*source=(?:api_8005_retry|order_api_8005_retry):"
    r"(?P<api_id>[^:,)\s]+):retry_success"
)
_AUTH_API_ID_PATTERN = re.compile(r"\[(?P<api_id>[A-Za-z][A-Za-z0-9_-]{2,31})\].*8005")
_AUTH_RECOVERY_FAILURE_PATTERNS: tuple[re.Pattern, ...] = (
    re.compile(r"8005 token refresh retry 후에도 인증 실패"),
    re.compile(r"8005 감지 후 Kiwoom token force refresh 실패"),
    re.compile(r"\[WS TOKEN 재발급\] (?:실패|예외)"),
)


def _now_ts() -> float:
    return time.time()


def _today_str() -> str:
    return datetime.now().astimezone().strftime("%Y-%m-%d")


def _cooldown_sec() -> int:
    return int(
        getattr(
            TRADING_RULES,
            "KIWOOM_AUTH_8005_RESTART_COOLDOWN_SEC",
            getattr(TRADING_RULES, "KIWOOM_AUTH_RESTART_COOLDOWN_SEC", 120),
        )
        or 120
    )


def _daily_fail_threshold() -> int:
    return int(
        getattr(TRADING_RULES, "KIWOOM_AUTH_8005_DAILY_RESTART_FAIL_THRESHOLD", 3) or 3
    )


def _get_target_log_files() -> list[Path]:
    if not LOGS_DIR.exists():
        return []

    files: list[Path] = []
    for entry in os.scandir(str(LOGS_DIR)):
        if not entry.is_file():
            continue
        if entry.name.startswith("run_error_detection"):
            continue
        if entry.name in _EXPLICIT_LOG_NAMES:
            files.append(Path(entry.path))
            continue
        if entry.name.startswith("kiwoom_orders") and entry.name.endswith(".log"):
            files.append(Path(entry.path))

    return sorted(set(files), key=lambda p: p.name)


def _is_auth_8005_line(line: str) -> bool:
    if any(pattern.search(line) for pattern in _IGNORED_LINE_PATTERNS):
        return False
    if "8005" not in line:
        return False
    return any(token in line for token in ("Token", "토큰", "인증"))


def _auth_recovery_kind(line: str) -> str | None:
    if any(pattern.search(line) for pattern in _AUTH_RECOVERY_FAILURE_PATTERNS):
        return "failure"
    if _AUTH_RECOVERY_PATTERN.search(line):
        return "success"
    return None


def _extract_auth_api_id(line: str) -> str | None:
    recovery_match = _AUTH_RECOVERY_PATTERN.search(line)
    if recovery_match:
        return recovery_match.group("api_id")
    auth_match = _AUTH_API_ID_PATTERN.search(line)
    return auth_match.group("api_id") if auth_match else None


@register_detector
class KiwoomAuth8005RestartDetector(BaseDetector):
    id = "kiwoom_auth_8005_restart"
    name = "Kiwoom Auth 8005 Restart"
    category = "runtime_auth"

    def check(self) -> DetectionResult:
        state = self._load_state()
        log_files = _get_target_log_files()
        files_state = state.setdefault("files", {})
        state_load_error = bool(state.pop("_state_load_error", False))
        details: dict = {
            "target_logs": [path.name for path in log_files],
            "restart_flag_path": str(RESTART_FLAG_PATH),
            "cooldown_sec": _cooldown_sec(),
            "runtime_effect": "restart_flag_only",
        }

        if not files_state:
            for log_path in log_files:
                self._baseline_file(log_path, files_state)
            details["baseline_initialized"] = True
            if state_load_error:
                details["state_load_error"] = True
            if not self.dry_run:
                self._save_state(state)
            if state_load_error:
                return DetectionResult(
                    detector_id=self.id,
                    category=self.category,
                    severity="warning",
                    summary="Kiwoom auth 8005 detector state could not be loaded; baseline reset without scanning historical logs.",
                    details=details,
                    recommended_action="Verify the detector state file and run the next auth health check.",
                )
            return DetectionResult(
                detector_id=self.id,
                category=self.category,
                severity="pass",
                summary="Kiwoom auth 8005 detector baseline initialized; no historical logs scanned.",
                details=details,
                recommended_action="",
            )

        matches: list[dict] = []
        recovery_events: list[dict] = []
        baselined_new_files: list[str] = []

        for log_path in log_files:
            fname = log_path.name
            if fname not in files_state:
                self._baseline_file(log_path, files_state)
                baselined_new_files.append(fname)
                continue
            file_matches, file_recovery_events, new_position = self._scan_file(
                log_path,
                int(files_state.get(fname, {}).get("position", 0) or 0),
            )
            files_state[fname] = {"position": new_position, "scanned_at": _now_ts()}
            matches.extend(file_matches)
            recovery_events.extend(file_recovery_events)

        if baselined_new_files:
            details["new_files_baselined"] = baselined_new_files

        runtime_identity = _current_runtime_identity()
        if runtime_identity:
            details["current_runtime_pid"] = runtime_identity["pid"]
            details["current_runtime_start_ts"] = runtime_identity["start_ts"]
            details["current_runtime_start_at"] = (
                datetime.fromtimestamp(runtime_identity["start_ts"])
                .astimezone()
                .isoformat(timespec="seconds")
            )
            matches, prior_runtime_matches = _split_prior_runtime_matches(
                matches,
                runtime_start_ts=runtime_identity["start_ts"],
                last_restart_ts=float(state.get("last_restart_ts", 0) or 0),
            )
            if prior_runtime_matches:
                details["prior_runtime_auth_8005_count"] = len(prior_runtime_matches)
                details["prior_runtime_auth_8005_samples"] = prior_runtime_matches[:5]
            recovery_events, _ = _split_prior_runtime_matches(
                recovery_events,
                runtime_start_ts=runtime_identity["start_ts"],
                last_restart_ts=float(state.get("last_restart_ts", 0) or 0),
            )

        if not matches:
            if not self.dry_run:
                self._save_state(state)
            if details.get("prior_runtime_auth_8005_count"):
                return DetectionResult(
                    detector_id=self.id,
                    category=self.category,
                    severity="pass",
                    summary=(
                        "Prior-runtime Kiwoom auth 8005 log entries were consumed after "
                        "PID handoff; no current-runtime auth failure was detected."
                    ),
                    details=details,
                    recommended_action="",
                )
            return DetectionResult(
                detector_id=self.id,
                category=self.category,
                severity="pass",
                summary="No fresh Kiwoom auth 8005 log entries detected.",
                details=details,
                recommended_action="",
            )

        recovered_matches, actionable_matches = _partition_recovered_matches(
            matches,
            recovery_events,
        )
        if recovered_matches and not actionable_matches:
            details.update(
                {
                    "fresh_auth_8005_count": len(matches),
                    "recovered_auth_8005_count": len(recovered_matches),
                    "recovered_auth_8005_samples": recovered_matches[:5],
                    "auth_recovery_events": recovery_events[:10],
                    "would_restart": False,
                    "restart_requested": False,
                    "token_cache_invalidated": False,
                    "recovery_state": "recovered_without_restart",
                    "recovery_reason": "same_runtime_retry_and_handoff_succeeded",
                    "dry_run": self.dry_run,
                }
            )
            if not self.dry_run:
                self._save_state(state)
            return DetectionResult(
                detector_id=self.id,
                category=self.category,
                severity="pass",
                summary=(
                    "Fresh Kiwoom auth 8005 was recovered in-process by a successful "
                    "same-request retry and token handoff; no restart was requested."
                ),
                details=details,
                recommended_action="",
            )

        if recovered_matches:
            details["recovered_auth_8005_count"] = len(recovered_matches)
            details["recovered_auth_8005_samples"] = recovered_matches[:5]
        if recovery_events:
            details["auth_recovery_events"] = recovery_events[:10]

        return self._handle_matches(state, details, actionable_matches)

    def _handle_matches(
        self, state: dict, details: dict, matches: list[dict]
    ) -> DetectionResult:
        now = _now_ts()
        today = _today_str()
        if state.get("restart_count_date") != today:
            state["restart_count_date"] = today
            state["restart_count"] = 0

        last_restart_ts = float(state.get("last_restart_ts", 0) or 0)
        cooldown_remaining = max(0, int(_cooldown_sec() - (now - last_restart_ts)))
        restart_count = int(state.get("restart_count", 0) or 0)
        daily_restart_cap = _daily_fail_threshold()
        restart_cap_reached = restart_count >= daily_restart_cap
        cooldown_active = cooldown_remaining > 0
        suppressed = cooldown_active or restart_cap_reached
        would_restart = not suppressed
        restart_requested = False
        cache_invalidated = False

        if not self.dry_run:
            try:
                cache_invalidated = kiwoom_utils.invalidate_kiwoom_token_cache(
                    reason="error_detector_auth_8005"
                )
            except Exception as exc:
                details["token_cache_invalidation_error"] = str(exc)

        if not suppressed and not self.dry_run:
            RESTART_FLAG_PATH.touch()
            restart_requested = True
            state["last_restart_ts"] = now
            restart_count += 1
            state["restart_count"] = restart_count

        if self.dry_run and not suppressed:
            restart_count += 1

        details.update(
            {
                "fresh_auth_8005_count": len(matches),
                "fresh_auth_8005_samples": matches[:5],
                "would_restart": would_restart,
                "restart_requested": restart_requested,
                "restart_suppressed_by_cooldown": cooldown_active,
                "restart_suppressed_by_daily_cap": restart_cap_reached,
                "daily_restart_cap": daily_restart_cap,
                "token_cache_invalidated": cache_invalidated,
                "cooldown_remaining_sec": cooldown_remaining,
                "restart_count_date": today,
                "restart_count": restart_count,
                "dry_run": self.dry_run,
            }
        )

        if not self.dry_run:
            self._save_state(state)

        severity = "fail" if restart_count >= _daily_fail_threshold() else "warning"
        if restart_cap_reached:
            summary = (
                "Fresh Kiwoom auth 8005 detected, but restart.flag creation was suppressed "
                "because the daily auth restart cap was reached."
            )
            action = "Stop the restart loop. Verify Kiwoom token issuance, account API auth, and WS/REST recovery manually."
        elif suppressed:
            summary = "Fresh Kiwoom auth 8005 detected, but restart.flag creation was suppressed by cooldown."
            action = "Cooldown is active. Verify the last graceful restart completed and check WS/REST recovery."
        elif self.dry_run:
            summary = (
                "Fresh Kiwoom auth 8005 detected; dry-run would create restart.flag."
            )
            action = "Run live detector or allow daemon/cron to create restart.flag if this is a runtime incident."
        else:
            summary = "Fresh Kiwoom auth 8005 detected; restart.flag created for graceful bot restart."
            action = "Verify bot_main exits, run_bot.sh restarts it, and Kiwoom WS/REST data recover."

        if severity == "fail":
            summary = f"{summary} Daily auth restart count is {restart_count}."

        return DetectionResult(
            detector_id=self.id,
            category=self.category,
            severity=severity,
            summary=summary,
            details=details,
            recommended_action=action,
        )

    @staticmethod
    def _baseline_file(log_path: Path, files_state: dict) -> None:
        try:
            position = log_path.stat().st_size
        except OSError:
            position = 0
        files_state[log_path.name] = {"position": position, "scanned_at": _now_ts()}

    @staticmethod
    def _scan_file(log_path: Path, last_pos: int) -> tuple[list[dict], list[dict], int]:
        try:
            file_size = log_path.stat().st_size
        except OSError:
            return [], [], last_pos

        if last_pos < 0 or file_size < last_pos:
            last_pos = 0
        if file_size <= last_pos:
            return [], [], last_pos

        max_bytes = int(
            getattr(TRADING_RULES, "KIWOOM_AUTH_8005_SCAN_MAX_BYTES", 512_000)
            or 512_000
        )
        try:
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                f.seek(max(last_pos, file_size - max_bytes))
                if f.tell() > last_pos:
                    f.readline()
                new_lines = f.readlines()
                new_position = f.tell()
        except OSError:
            return [], [], last_pos

        matches: list[dict] = []
        recovery_events: list[dict] = []
        for idx, line in enumerate(new_lines, start=1):
            line = line.rstrip("\n")
            event = {
                "file": log_path.name,
                "line_offset": idx,
                "message": line[-500:],
                "observed_ts": _extract_log_timestamp(line),
                "api_id": _extract_auth_api_id(line),
            }
            if _is_auth_8005_line(line):
                matches.append(event)
            recovery_kind = _auth_recovery_kind(line)
            if recovery_kind:
                recovery_events.append({**event, "kind": recovery_kind})

        return matches, recovery_events, new_position

    @staticmethod
    def _load_state() -> dict:
        if not SCAN_STATE_PATH.exists():
            return {}
        try:
            return json.loads(SCAN_STATE_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {"_state_load_error": True}

    @staticmethod
    def _save_state(state: dict) -> None:
        SCAN_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        SCAN_STATE_PATH.write_text(
            json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
        )


def _extract_log_timestamp(line: str) -> float | None:
    match = _LOG_TIMESTAMP_PATTERN.search(line)
    if not match:
        return None
    try:
        observed = datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None
    local_tz = datetime.now().astimezone().tzinfo
    return observed.replace(tzinfo=local_tz).timestamp()


def _partition_recovered_matches(
    matches: list[dict], recovery_events: list[dict]
) -> tuple[list[dict], list[dict]]:
    """Suppress restart only when a timestamped retry handoff closes the incident.

    Missing timestamps remain actionable. A recovery failure at or after the
    success marker also keeps the incident actionable. This intentionally uses
    the same-request ``retry_success`` handoff rather than token issuance alone.
    """
    timestamped_matches = [
        item for item in matches if item.get("observed_ts") is not None
    ]
    if len(timestamped_matches) != len(matches):
        return [], matches

    success_events = [
        item
        for item in recovery_events
        if item.get("kind") == "success"
        and item.get("observed_ts") is not None
        and item.get("api_id")
    ]
    if not success_events:
        return [], matches

    failure_events = [
        item
        for item in recovery_events
        if item.get("kind") == "failure" and item.get("observed_ts") is not None
    ]
    valid_success_events = [
        success
        for success in success_events
        if not any(
            _event_at_or_after(failure, success, cross_file_equal=True)
            for failure in failure_events
        )
    ]
    if not valid_success_events:
        return [], matches

    recovered = []
    actionable = []
    for match in timestamped_matches:
        if match.get("api_id") and any(
            success.get("api_id") == match.get("api_id")
            and success.get("file") == match.get("file")
            and _event_at_or_after(success, match)
            for success in valid_success_events
        ):
            recovered.append(match)
        else:
            actionable.append(match)
    return recovered, actionable


def _event_at_or_after(
    candidate: dict,
    reference: dict,
    *,
    cross_file_equal: bool = False,
) -> bool:
    candidate_ts = float(candidate["observed_ts"])
    reference_ts = float(reference["observed_ts"])
    if candidate_ts != reference_ts:
        return candidate_ts > reference_ts
    if candidate.get("file") != reference.get("file"):
        # Cross-file events at one-second log precision have no provable order.
        return cross_file_equal
    return int(candidate.get("line_offset") or 0) >= int(
        reference.get("line_offset") or 0
    )


def _current_runtime_identity() -> dict | None:
    try:
        heartbeat = json.loads(HEARTBEAT_PATH.read_text(encoding="utf-8"))
        pid = int(heartbeat.get("main_loop", {}).get("pid") or 0)
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return None
    if pid <= 0:
        return None

    try:
        proc_dir = PROC_ROOT / str(pid)
        cmdline = (
            (proc_dir / "cmdline")
            .read_bytes()
            .replace(b"\x00", b" ")
            .decode("utf-8", errors="replace")
        )
        if "bot_main.py" not in cmdline:
            return None
        proc_stat = (proc_dir / "stat").read_text(encoding="utf-8")
        stat_fields = proc_stat.rsplit(")", 1)[1].split()
        start_ticks = int(stat_fields[19])
        boot_time_line = next(
            line
            for line in (PROC_ROOT / "stat").read_text(encoding="utf-8").splitlines()
            if line.startswith("btime ")
        )
        boot_time = int(boot_time_line.split()[1])
        clock_ticks = int(os.sysconf("SC_CLK_TCK"))
    except (OSError, StopIteration, IndexError, TypeError, ValueError):
        return None
    if clock_ticks <= 0:
        return None
    return {"pid": pid, "start_ts": boot_time + (start_ticks / clock_ticks)}


def _split_prior_runtime_matches(
    matches: list[dict], *, runtime_start_ts: float, last_restart_ts: float
) -> tuple[list[dict], list[dict]]:
    if last_restart_ts <= 0 or runtime_start_ts < last_restart_ts:
        return matches, []

    current: list[dict] = []
    prior: list[dict] = []
    # Log timestamps have one-second precision. Keep same-second rows current so
    # an auth failure emitted during the new process startup cannot be hidden.
    prior_cutoff = runtime_start_ts - 1.0
    for match in matches:
        observed_ts = match.get("observed_ts")
        if isinstance(observed_ts, (int, float)) and observed_ts < prior_cutoff:
            prior.append(match)
        else:
            current.append(match)
    return current, prior
