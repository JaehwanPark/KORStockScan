from __future__ import annotations

import threading
from typing import Optional, Dict, Any

from src.utils.logger import log_error, log_info
from src.utils.runtime_flags import (
    clear_trading_paused,
    is_trading_paused,
    set_trading_paused,
)

PAUSE_EVENT_TYPE = "BUY_SIDE_PAUSE_CHANGED"
TRADING_PAUSED_EVENT = "TRADING_PAUSED"
PAUSE_STATE_LABEL = "신규 매수 및 추가매수 중단 상태"

_lock = threading.RLock()
_cached_paused: Optional[bool] = None
_bound_bus = None


def _read_file_state() -> bool:
    return is_trading_paused()


def is_buy_side_paused() -> bool:
    """Final truth source is the persistent flag file."""
    global _cached_paused
    paused = _read_file_state()
    with _lock:
        _cached_paused = paused
    return paused


def get_pause_state_label() -> str:
    return PAUSE_STATE_LABEL


def bind_event_bus(event_bus) -> None:
    global _bound_bus
    if event_bus is None:
        return
    with _lock:
        if _bound_bus is event_bus:
            return
        event_bus.subscribe(PAUSE_EVENT_TYPE, _handle_pause_event)
        event_bus.subscribe(TRADING_PAUSED_EVENT, _handle_trading_paused_event)
        _bound_bus = event_bus


def _handle_pause_event(payload: Optional[Dict[str, Any]]) -> None:
    global _cached_paused
    payload = payload or {}
    paused = bool(payload.get("paused"))
    with _lock:
        _cached_paused = paused


def _handle_trading_paused_event(payload: Optional[Dict[str, Any]]) -> None:
    global _cached_paused
    payload = payload or {}
    status = str(payload.get("status", "")).upper()
    if status == "PAUSED":
        paused = True
    elif status == "RESUMED":
        paused = False
    else:
        paused = is_trading_paused()

    with _lock:
        _cached_paused = paused


def set_buy_side_pause(
    paused: bool, *, source: str = "system", reason: str | None = None, event_bus=None
) -> bool:
    """
    Compatibility helper for non-telegram callers.
    Current telegram control path writes the file via runtime_flags.py and publishes EventBus separately.
    Final truth source remains the persistent flag file.
    """
    global _cached_paused
    bind_event_bus(event_bus)
    with _lock:
        before = _read_file_state()
        try:
            if paused:
                set_trading_paused()
            else:
                clear_trading_paused()
        except Exception as exc:
            tag = "TRADING_PAUSED" if paused else "TRADING_RESUMED"
            log_error(
                f"[{tag}] flag update failed source={source} paused={paused}: {exc}"
            )
            raise

        after = _read_file_state()
        _cached_paused = after

    if before != after:
        note = f" reason={reason}" if reason else ""
        tag = "TRADING_PAUSED" if after else "TRADING_RESUMED"
        log_info(f"[{tag}] source={source} paused={after}{note}")

    bus = event_bus or _bound_bus
    if bus is not None:
        try:
            bus.publish(
                PAUSE_EVENT_TYPE,
                {
                    "paused": after,
                    "source": source,
                    "reason": reason,
                    "label": PAUSE_STATE_LABEL,
                },
            )
        except Exception as exc:
            tag = "TRADING_PAUSED" if after else "TRADING_RESUMED"
            log_error(f"[{tag}] event publish failed: {exc}")

    return after
