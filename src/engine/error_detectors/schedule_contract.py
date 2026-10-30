from __future__ import annotations

import re
import subprocess
from datetime import date
from pathlib import Path
from typing import Any

_TRUE_VALUES = {"1", "true", "yes", "on"}


def installed_upstream_start(
    crontab_text: str | None, *, upstream: Any, workspace: Path, source_day: str
) -> tuple[tuple[int, int] | None, dict[str, Any]]:
    """Locate a native routed owner's start, without changing its deadline.

    Unknown, conflicting or unsupported schedules retain the original artifact
    expectation. A marker alone cannot establish the command owner.
    """
    details: dict[str, Any] = {"reason": "upstream_schedule_unresolved"}
    if not isinstance(upstream, dict) or crontab_text is None:
        return None, details
    from src.engine.infrastructure.runtime_release_router import (
        OWNED,
        TAGS,
        render_crontab,
    )

    owners = [
        operation
        for operation, (script, log_owner) in OWNED.items()
        if script == upstream.get("id")
        and log_owner == Path(str(upstream.get("log") or "")).stem
    ]
    if len(owners) != 1:
        return None, details
    try:
        rendered = render_crontab(
            crontab_text,
            workspace,
            require_snapshot_group=True,
            require_postclose_stop=True,
        )
    except ValueError:
        return None, {"reason": "native_cron_routing_unverified"}
    if rendered.rstrip() != crontab_text.rstrip():
        return None, {"reason": "native_cron_routing_unverified"}
    operation = owners[0]
    markers = [marker for marker, target in TAGS.items() if target == operation]
    day = date.fromisoformat(source_day)
    starts = []
    timezone = "Asia/Seoul"
    for raw in crontab_text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("CRON_TZ="):
            timezone = line.partition("=")[2].strip("\"'")
            continue
        if line.rsplit("#", 1)[-1].strip() not in markers:
            continue
        fields = line.split(None, 5)
        if len(fields) != 6 or timezone != "Asia/Seoul":
            return None, {"reason": "unsupported_upstream_schedule"}
        minute, hour, dom, month, dow, _command = fields
        if (
            not minute.isdigit()
            or not hour.isdigit()
            or not 0 <= int(minute) < 60
            or not 0 <= int(hour) < 24
            or dom not in {"*", str(day.day)}
            or month not in {"*", str(day.month)}
            or dow not in {"*", "1-5", str(day.isoweekday() % 7)}
            or (dow == "1-5" and day.weekday() >= 5)
        ):
            return None, {"reason": "unsupported_or_other_date_upstream_schedule"}
        starts.append((int(hour), int(minute)))
    if not starts:
        return None, details
    start = min(starts)
    return start, {
        "reason": "installed_native_upstream_start",
        "operation": operation,
        "matching_line_count": len(starts),
        "source_date": source_day,
        "start": list(start),
        "native_cron_routing_verified": True,
    }


def load_installed_crontab() -> str | None:
    """Return the current user's installed crontab, or None when unavailable.

    None intentionally keeps detector expectations enabled. A transient inability to
    inspect crontab must not silently suppress real completion or freshness alerts.
    """

    try:
        completed = subprocess.run(
            ["crontab", "-l"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout


def evaluate_schedule_contract(
    crontab_text: str | None,
    *,
    markers: list[str],
    parent_env_key: str | None = None,
    parent_default_enabled: bool = True,
) -> tuple[str, dict[str, Any]]:
    """Evaluate whether an installed cron-owned producer is expected to run."""

    details: dict[str, Any] = {
        "markers": list(markers),
        "parent_env_key": parent_env_key,
        "parent_default_enabled": parent_default_enabled,
    }
    if crontab_text is None:
        details["reason"] = "installed_crontab_unavailable_expectation_preserved"
        return "unknown", details

    active_lines = [
        line.strip()
        for line in crontab_text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    matching_lines = [
        line for line in active_lines if any(marker in line for marker in markers)
    ]
    details["matching_line_count"] = len(matching_lines)
    if not matching_lines:
        details["reason"] = "no_installed_cron_match"
        return "disabled_not_installed", details

    if not parent_env_key:
        details["reason"] = "installed_cron_match"
        return "enabled", details

    value_pattern = re.compile(
        rf"(?:^|\s){re.escape(parent_env_key)}=(?:'([^']*)'|\"([^\"]*)\"|([^\s]+))"
    )
    explicit_values: list[str] = []
    line_enabled: list[bool] = []
    for line in matching_lines:
        match = value_pattern.search(line)
        if match:
            value = next(group for group in match.groups() if group is not None)
            explicit_values.append(value)
            line_enabled.append(value.strip().lower() in _TRUE_VALUES)
        else:
            line_enabled.append(parent_default_enabled)
    details["parent_explicit_values"] = explicit_values
    if any(line_enabled):
        details["reason"] = "parent_enabled"
        return "enabled", details
    details["reason"] = "parent_disabled"
    return "disabled_by_parent", details
