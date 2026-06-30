from __future__ import annotations

import json
import os
import re
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

from src.utils.constants import LOGS_DIR, PROJECT_ROOT, TRADING_RULES

from src.engine.error_detectors.base import (
    BaseDetector,
    DetectionResult,
    register_detector,
)


SCAN_STATE_PATH = PROJECT_ROOT / "tmp" / "error_detector_log_scan_state.json"

_EXCEPTION_PATTERNS: list[tuple[str, re.Pattern]] = []
_IGNORED_LINE_PATTERNS: list[re.Pattern] = [
    re.compile(r"\[ERROR_DETECTION\]"),
    re.compile(r"\bTEST(?:\b|[:(])"),
    re.compile(r"테스트"),
    re.compile(r"\btest\s*:"),
    re.compile(r"\b123456\b"),
    re.compile(r"_DummySession"),
    re.compile(r"\bbus fail\b"),
    re.compile(r"/tmp/pytest-of-[^/\s]+/"),
]
_ERROR_CANDIDATE_PATTERN = re.compile(
    r"(?:\berror\b|\bcritical\b|\bfatal\b|traceback|exception|🚨|❌|에러|오류|실패)",
    re.IGNORECASE,
)


def _register_pattern(name: str, pattern: str):
    _EXCEPTION_PATTERNS.append((name, re.compile(pattern)))


_register_pattern("DB_ERROR", r"(?:db|database|sqlalchemy|psycopg|connection.*refused|query.*fail|db.*error)")
_register_pattern("API_ERROR", r"(?:api.*error|http.*(?:40[13]|50[0-9])|request.*fail|response.*invalid|timeout.*api|api.*timeout)")
_register_pattern("WEBSOCKET_ERROR", r"(?:websocket|ws.*error|ws.*close|ws.*disconnect)")
_register_pattern("PARSE_ERROR", r"(?:parse|schema.*invalid|json.*decode|value.*error|type.*error)")
_register_pattern("TIMEOUT_ERROR", r"(?:timeout|timed? ?out|deadline)")
_register_pattern("KEY_ERROR", r"(?:key.*error|key.*not.*found|missing.*key)")
_register_pattern("OS_ERROR", r"(?:os.*error|file.*not.*found|permission.*denied|disk.*full|no.*space)")
_register_pattern("IMPORT_ERROR", r"(?:import.*error|module.*not.*found|no.*module)")
_register_pattern(
    "MEMORY_ERROR",
    r"(?:\bmemory(?:error)?\b|\boom\b|out\s+of\s+memory|cannot\s+allocate\s+memory)",
)
_register_pattern(
    "ORDER_REJECT",
    r"(?:"
    r"order.*reject|cancel_failed|"
    r"매수거절|매도거절|취소거절|주문\s*거절|추가매수\s*주문\s*거절|"
    r"주문\s*불가능|매도가능수량이\s*부족|"
    r"sor.*주문|원주문이\s*krx주문이\s*아닙니다|원주문이\s*sor주문"
    r")",
)
_register_pattern("UNKNOWN", r"(?:error|exception|critical|fatal)",)


def _get_error_log_files() -> list[Path]:
    if not LOGS_DIR.exists():
        return []
    files: list[Path] = []
    for entry in os.scandir(str(LOGS_DIR)):
        if not entry.is_file():
            continue
        if entry.name.startswith("run_error_detection"):
            continue
        if "_error" in entry.name and entry.name.endswith(".log"):
            files.append(Path(entry.path))
        if entry.name.endswith("_error.log"):
            files.append(Path(entry.path))
    return sorted(set(files), key=lambda p: str(p))


@register_detector
class LogScanner(BaseDetector):
    id = "log_scanner"
    name = "Error Log Scanner"
    category = "log"

    def check(self) -> DetectionResult:
        log_files = _get_error_log_files()
        state = self._load_state()
        details: dict = {}
        total_new_errors = 0
        error_counter: Counter = Counter()
        error_files_with_issues: list[str] = []

        for log_path in log_files:
            fname = log_path.name
            last_pos = state.get(fname, {}).get("position", 0)
            new_errors, new_position, file_errors = self._scan_file(
                log_path, last_pos, error_counter
            )
            total_new_errors += new_errors
            if new_errors > 0:
                state[fname] = {"position": new_position, "scanned_at": time.time()}
            if new_errors > 0:
                error_files_with_issues.append(f"{fname}(+{new_errors})")
            if new_errors > 0:
                details.setdefault("file_new_errors", {})[fname] = new_errors

        if total_new_errors > 0:
            details["error_type_counts"] = dict(error_counter.most_common(10))
            details["files_with_new_errors"] = error_files_with_issues
            if not self.dry_run:
                self._save_state(state)

        severity, summary = self._classify(total_new_errors, error_counter)

        return DetectionResult(
            detector_id=self.id,
            category=self.category,
            severity=severity,
            summary=summary,
            details=details,
            recommended_action=self._recommend_action(severity, error_counter),
        )

    @staticmethod
    def _scan_file(
        path: Path, last_pos: int, counter: Counter
    ) -> tuple[int, int, list[dict]]:
        try:
            file_size = path.stat().st_size
        except OSError:
            return 0, last_pos, []

        if last_pos < 0 or file_size < last_pos:
            last_pos = 0

        if file_size <= last_pos:
            return 0, last_pos, []

        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                f.seek(last_pos)
                new_lines = f.read(
                    int(getattr(TRADING_RULES, "ERROR_DETECTOR_LOG_SCAN_MAX_LINES", 2000)) * 256
                )
                new_position = f.tell()
        except OSError:
            return 0, last_pos, []

        error_count = 0
        for line in new_lines.splitlines():
            if any(pattern.search(line) for pattern in _IGNORED_LINE_PATTERNS):
                continue
            if not _ERROR_CANDIDATE_PATTERN.search(line):
                continue
            lower = line.lower()
            for etype, pattern in _EXCEPTION_PATTERNS:
                if pattern.search(lower) or pattern.search(line):
                    counter[etype] += 1
                    error_count += 1
                    break

        if error_count == 0:
            new_position = last_pos

        return error_count, new_position, []

    @staticmethod
    def _load_state() -> dict:
        if not SCAN_STATE_PATH.exists():
            return {}
        try:
            return json.loads(SCAN_STATE_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    @staticmethod
    def _save_state(state: dict) -> None:
        SCAN_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        SCAN_STATE_PATH.write_text(json.dumps(state, ensure_ascii=True), encoding="utf-8")

    @staticmethod
    def _classify(
        total_new: int, counter: Counter
    ) -> tuple[str, str]:
        if total_new == 0:
            return "pass", "No new error log entries detected."
        if total_new >= int(getattr(TRADING_RULES, "ERROR_DETECTOR_LOG_BURST_THRESHOLD", 4)):
            top = counter.most_common(1)[0]
            return (
                "fail",
                f"Error burst detected: {total_new} new errors since last scan. "
                f"Top type: {top[0]}({top[1]})",
            )
        return (
            "warning",
            f"{total_new} new error(s) detected since last scan.",
        )

    @staticmethod
    def _recommend_action(severity: str, counter: Counter) -> str:
        if severity == "fail":
            top = counter.most_common(3)
            types = ", ".join(f"{t}({c})" for t, c in top)
            return f"Investigate error types: {types}. Check error log files for details."
        if severity == "warning":
            return "Review warning-level errors in next maintenance window."
        return ""
