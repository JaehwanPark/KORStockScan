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

_EXPLICIT_LOG_NAMES = {
    "bot_history.log",
    "kiwoom_utils_info.log",
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
    return int(getattr(TRADING_RULES, "KIWOOM_AUTH_8005_DAILY_RESTART_FAIL_THRESHOLD", 3) or 3)


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
        baselined_new_files: list[str] = []

        for log_path in log_files:
            fname = log_path.name
            if fname not in files_state:
                self._baseline_file(log_path, files_state)
                baselined_new_files.append(fname)
                continue
            file_matches, new_position = self._scan_file(
                log_path,
                int(files_state.get(fname, {}).get("position", 0) or 0),
            )
            files_state[fname] = {"position": new_position, "scanned_at": _now_ts()}
            matches.extend(file_matches)

        if baselined_new_files:
            details["new_files_baselined"] = baselined_new_files

        if not matches:
            if not self.dry_run:
                self._save_state(state)
            return DetectionResult(
                detector_id=self.id,
                category=self.category,
                severity="pass",
                summary="No fresh Kiwoom auth 8005 log entries detected.",
                details=details,
                recommended_action="",
            )

        return self._handle_matches(state, details, matches)

    def _handle_matches(self, state: dict, details: dict, matches: list[dict]) -> DetectionResult:
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
                cache_invalidated = kiwoom_utils.invalidate_kiwoom_token_cache(reason="error_detector_auth_8005")
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
            summary = (
                "Fresh Kiwoom auth 8005 detected, but restart.flag creation was suppressed by cooldown."
            )
            action = "Cooldown is active. Verify the last graceful restart completed and check WS/REST recovery."
        elif self.dry_run:
            summary = "Fresh Kiwoom auth 8005 detected; dry-run would create restart.flag."
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
    def _scan_file(log_path: Path, last_pos: int) -> tuple[list[dict], int]:
        try:
            file_size = log_path.stat().st_size
        except OSError:
            return [], last_pos

        if last_pos < 0 or file_size < last_pos:
            last_pos = 0
        if file_size <= last_pos:
            return [], last_pos

        max_bytes = int(getattr(TRADING_RULES, "KIWOOM_AUTH_8005_SCAN_MAX_BYTES", 512_000) or 512_000)
        try:
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                f.seek(max(last_pos, file_size - max_bytes))
                if f.tell() > last_pos:
                    f.readline()
                new_lines = f.readlines()
                new_position = f.tell()
        except OSError:
            return [], last_pos

        matches: list[dict] = []
        for idx, line in enumerate(new_lines, start=1):
            line = line.rstrip("\n")
            if not _is_auth_8005_line(line):
                continue
            matches.append(
                {
                    "file": log_path.name,
                    "line_offset": idx,
                    "message": line[-500:],
                }
            )

        return matches, new_position

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
        SCAN_STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
