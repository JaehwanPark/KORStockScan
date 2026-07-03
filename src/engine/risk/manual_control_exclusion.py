"""Operator-controlled stock manual management exclusion.

This guard stops bot control for explicitly excluded symbols so the operator
can manage them manually.
"""

from __future__ import annotations

import os
import re
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from src.utils.constants import DATA_DIR

EXCLUDED_CODES_ENV = "KORSTOCKSCAN_MANUAL_CONTROL_EXCLUDED_CODES"
EXCLUDED_CODES_FILE_ENV = "KORSTOCKSCAN_MANUAL_CONTROL_EXCLUDED_CODES_FILE"
LEGACY_WATCH_EXCLUDED_CODES_ENV = "KORSTOCKSCAN_WATCH_EXCLUDED_CODES"
LEGACY_WATCH_EXCLUDED_CODES_FILE_ENV = "KORSTOCKSCAN_WATCH_EXCLUDED_CODES_FILE"
DEFAULT_EXCLUDED_CODES_FILE = DATA_DIR / "config" / "manual_control_excluded_codes.txt"

_CODE_TOKEN_RE = re.compile(r"[,\s;]+")
_COMMENT_RE = re.compile(r"(?:#|//).*$")
_FILE_CACHE = {
    "path": None,
    "mtime_ns": None,
    "codes": frozenset(),
}
_WRITE_LOCK = threading.Lock()


@dataclass(frozen=True)
class ManualControlExclusionDecision:
    excluded: bool
    code: str
    reason: str
    source: str

    def as_log_fields(self) -> dict[str, object]:
        return {
            "manual_control_exclusion_applied": self.excluded,
            "manual_control_exclusion_code": self.code or "not_applicable_manual_control_exclusion_code",
            "manual_control_exclusion_reason": self.reason
            or "not_applicable_manual_control_exclusion_reason",
            "manual_control_exclusion_source": self.source
            or "not_applicable_manual_control_exclusion_source",
            "metric_role": "operator_runtime_guard",
            "decision_authority": "operator_manual_control_exclusion_no_bot_action",
            "window_policy": "intraday_operator_control",
            "sample_floor": "not_applicable_operator_guard",
            "primary_decision_metric": "operator_manual_control_excluded_symbol_match",
            "source_quality_gate": "not_applicable_operator_config",
            "runtime_effect": True,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "forbidden_uses": (
                "bot_buy_order,bot_sell_order,bot_cancel_order,bot_scale_in_order,"
                "score_threshold_change,provider_route_change,quantity_or_cap_change,"
                "broker_guard_relaxation,real_execution_quality_approval"
            ),
        }


@dataclass(frozen=True)
class ManualControlExclusionRemoval:
    removed: bool
    code: str
    reason: str
    source: str


def normalize_manual_control_exclusion_code(value: object) -> str:
    raw = str(value or "").strip().upper()
    if not raw:
        return ""
    digits = "".join(ch for ch in raw if ch.isdigit())
    if digits:
        return digits[-6:].zfill(6)
    return raw


def _split_codes(raw: str) -> Iterable[str]:
    for token in _CODE_TOKEN_RE.split(str(raw or "")):
        code = normalize_manual_control_exclusion_code(token)
        if code:
            yield code


def _env_codes() -> frozenset[str]:
    return frozenset(
        (
            *_split_codes(os.getenv(EXCLUDED_CODES_ENV, "")),
            *_split_codes(os.getenv(LEGACY_WATCH_EXCLUDED_CODES_ENV, "")),
        )
    )


def _file_path() -> Path:
    raw_path = str(
        os.getenv(EXCLUDED_CODES_FILE_ENV, "")
        or os.getenv(LEGACY_WATCH_EXCLUDED_CODES_FILE_ENV, "")
        or ""
    ).strip()
    return Path(raw_path).expanduser() if raw_path else DEFAULT_EXCLUDED_CODES_FILE


def _invalidate_file_cache() -> None:
    _FILE_CACHE.update({"path": None, "mtime_ns": None, "codes": frozenset()})


def _sanitize_append_comment(value: object) -> str:
    text = re.sub(r"[\r\n#]+", " ", str(value or "")).strip()
    return "".join(ch if 32 <= ord(ch) < 127 else "_" for ch in text)[:160]


def _split_line_comment(line: str) -> tuple[str, str]:
    match = _COMMENT_RE.search(line)
    if not match:
        return line, ""
    return line[: match.start()], line[match.start() :]


def _load_file_codes(path: Path) -> frozenset[str]:
    codes: set[str] = set()
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return frozenset()
    except OSError:
        return frozenset()
    for line in text.splitlines():
        uncommented = _COMMENT_RE.sub("", line)
        codes.update(_split_codes(uncommented))
    return frozenset(codes)


def _file_codes() -> frozenset[str]:
    path = _file_path()
    try:
        stat = path.stat()
        mtime_ns = stat.st_mtime_ns
    except FileNotFoundError:
        mtime_ns = None
    except OSError:
        mtime_ns = None
    cache_path = _FILE_CACHE.get("path")
    if cache_path == path and _FILE_CACHE.get("mtime_ns") == mtime_ns:
        return _FILE_CACHE["codes"]
    codes = _load_file_codes(path) if mtime_ns is not None else frozenset()
    _FILE_CACHE.update({"path": path, "mtime_ns": mtime_ns, "codes": codes})
    return codes


def configured_manual_control_exclusion_codes() -> frozenset[str]:
    return frozenset((*_file_codes(), *_env_codes()))


def evaluate_manual_control_exclusion(code: object) -> ManualControlExclusionDecision:
    norm_code = normalize_manual_control_exclusion_code(code)
    if not norm_code:
        return ManualControlExclusionDecision(False, "", "", "")
    env_codes = _env_codes()
    if norm_code in env_codes:
        return ManualControlExclusionDecision(
            True,
            norm_code,
            "operator_manual_control_excluded_symbol",
            EXCLUDED_CODES_ENV,
        )
    file_codes = _file_codes()
    if norm_code in file_codes:
        return ManualControlExclusionDecision(
            True,
            norm_code,
            "operator_manual_control_excluded_symbol",
            str(_file_path()),
        )
    return ManualControlExclusionDecision(False, norm_code, "", "")


def add_manual_control_exclusion_code(
    code: object,
    *,
    comment: object = "",
) -> ManualControlExclusionDecision:
    norm_code = normalize_manual_control_exclusion_code(code)
    if not norm_code:
        return ManualControlExclusionDecision(False, "", "invalid_manual_control_exclusion_code", "")

    existing = evaluate_manual_control_exclusion(norm_code)
    if existing.excluded:
        return existing

    path = _file_path()
    with _WRITE_LOCK:
        existing = evaluate_manual_control_exclusion(norm_code)
        if existing.excluded:
            return existing
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            suffix = _sanitize_append_comment(comment)
            with path.open("a", encoding="utf-8") as fp:
                fp.write(f"{norm_code}{f' # {suffix}' if suffix else ''}\n")
        except OSError as exc:
            return ManualControlExclusionDecision(
                False,
                norm_code,
                f"manual_control_exclusion_append_failed:{exc.__class__.__name__}",
                str(path),
            )

        _invalidate_file_cache()
    return ManualControlExclusionDecision(
        True,
        norm_code,
        "operator_manual_control_excluded_symbol",
        str(path),
    )


def remove_manual_control_exclusion_code(
    code: object,
    *,
    reason: object = "",
) -> ManualControlExclusionRemoval:
    norm_code = normalize_manual_control_exclusion_code(code)
    if not norm_code:
        return ManualControlExclusionRemoval(
            False,
            "",
            "invalid_manual_control_exclusion_code",
            "",
        )

    path = _file_path()
    with _WRITE_LOCK:
        try:
            original_text = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return ManualControlExclusionRemoval(
                False,
                norm_code,
                "manual_control_exclusion_file_missing",
                str(path),
            )
        except OSError as exc:
            return ManualControlExclusionRemoval(
                False,
                norm_code,
                f"manual_control_exclusion_remove_failed:{exc.__class__.__name__}",
                str(path),
            )

        removed = False
        output_lines: list[str] = []
        for line in original_text.splitlines():
            uncommented, comment = _split_line_comment(line)
            codes = list(_split_codes(uncommented))
            if norm_code not in codes:
                output_lines.append(line)
                continue

            removed = True
            remaining = [item for item in codes if item != norm_code]
            if remaining:
                rebuilt = ",".join(remaining)
                if comment:
                    rebuilt = f"{rebuilt} {comment.strip()}"
                output_lines.append(rebuilt)

        if not removed:
            return ManualControlExclusionRemoval(
                False,
                norm_code,
                "manual_control_exclusion_code_not_in_file",
                str(path),
            )

        try:
            suffix = "\n" if output_lines and original_text.endswith("\n") else ""
            path.write_text("\n".join(output_lines) + suffix, encoding="utf-8")
        except OSError as exc:
            return ManualControlExclusionRemoval(
                False,
                norm_code,
                f"manual_control_exclusion_remove_failed:{exc.__class__.__name__}",
                str(path),
            )

        _invalidate_file_cache()

    suffix = _sanitize_append_comment(reason)
    return ManualControlExclusionRemoval(
        True,
        norm_code,
        f"manual_control_exclusion_removed{f':{suffix}' if suffix else ''}",
        str(path),
    )
