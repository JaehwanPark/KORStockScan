from __future__ import annotations

import re
import subprocess
from typing import Any

_TRUE_VALUES = {"1", "true", "yes", "on"}


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
