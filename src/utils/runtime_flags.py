from __future__ import annotations

import os
from pathlib import Path
from typing import MutableMapping

from src.utils.constants import PROJECT_ROOT

STARTUP_RETIRED_RUNTIME_ENV_KEYS = frozenset(
    {
        # The previous-limit-up entry/observation family was fully retired on
        # 2026-08-14.  A long-lived run_bot supervisor may still carry the old
        # value across child-only graceful restarts, so the child entrypoint
        # must remove it before importing any trading module.
        "KORSTOCKSCAN_UPPER_LIMIT_WATCH_ENABLED",
        # The latency TP1 direct recheck was removed in favor of feeding
        # refreshed inputs through the normal market-data envelope and next
        # scanner loop.  Clear the entire namespace so a long-lived supervisor
        # cannot restore the retired real-submit exception on a child restart.
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_ENABLED",
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_ACTIVE_DATE",
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_MIN_WAIT_SEC",
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_TTL_SEC",
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_SPREAD_WORSEN_BPS",
    }
)


def clear_startup_retired_runtime_env(
    environ: MutableMapping[str, str] | None = None,
) -> tuple[str, ...]:
    """Remove retired inherited runtime authority before engine imports."""

    target = os.environ if environ is None else environ
    removed: list[str] = []
    for key in sorted(STARTUP_RETIRED_RUNTIME_ENV_KEYS):
        if key in target:
            target.pop(key, None)
            removed.append(key)
    return tuple(removed)


def get_pause_flag_path() -> Path:
    """Return the absolute project-root path for the persistent pause flag."""
    return PROJECT_ROOT / "pause.flag"


def is_trading_paused() -> bool:
    """Return True when the persistent pause flag exists."""
    return get_pause_flag_path().exists()


def set_trading_paused() -> Path:
    """
    Create or overwrite the persistent pause flag.

    Raises:
        OSError: If the flag file cannot be created or written.
    """
    flag_path = get_pause_flag_path()
    flag_path.write_text("paused", encoding="utf-8")
    return flag_path


def clear_trading_paused() -> None:
    """
    Remove the persistent pause flag if present.

    Raises:
        OSError: If the flag file exists but cannot be removed.
    """
    flag_path = get_pause_flag_path()
    if flag_path.exists():
        flag_path.unlink()
