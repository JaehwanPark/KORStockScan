"""Low-latency polling shell for real scalping exit safety decisions.

The monitor deliberately owns no trading policy and performs no broker I/O.
It samples the already-bound runtime targets and websocket cache, then invokes
the injected evaluator.  The evaluator remains the single owner of quote,
position, order, and safety contracts.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable, Iterable
from typing import Any


class ScalpExitSafetyMonitor:
    """Poll HOLDING targets without waiting for the heavy scanner loop."""

    def __init__(
        self,
        *,
        targets_provider: Callable[[], Iterable[dict[str, Any]]],
        ws_snapshot_provider: Callable[[str], dict[str, Any] | None],
        evaluator: Callable[..., bool],
        state_lock: threading.RLock | threading.Lock,
        interval_sec: float = 0.25,
        error_handler: Callable[[str], None] | None = None,
    ) -> None:
        self._targets_provider = targets_provider
        self._ws_snapshot_provider = ws_snapshot_provider
        self._evaluator = evaluator
        self._state_lock = state_lock
        self._interval_sec = max(0.05, float(interval_sec))
        self._error_handler = error_handler
        self._stop_event = threading.Event()
        self._wakeup_event = threading.Event()
        self._wakeup_lock = threading.Lock()
        self._holding_codes: set[str] = set()
        self._wake_codes: set[str] = set()
        self._wake_overflow = False
        self._thread: threading.Thread | None = None

    @property
    def running(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    def start(self) -> bool:
        if self.running:
            return False
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run,
            daemon=True,
            name="scalp-exit-safety-monitor",
        )
        self._thread.start()
        return True

    def stop(self, timeout: float = 2.0) -> None:
        self._stop_event.set()
        self._wakeup_event.set()
        thread = self._thread
        if thread and thread is not threading.current_thread():
            thread.join(timeout=max(0.0, float(timeout)))

    def run_once(self, *, now_ts: float | None = None,
                 only_codes: set[str] | None = None) -> int:
        observed_at = float(time.time() if now_ts is None else now_ts)
        with self._state_lock:
            targets = [
                target
                for target in self._targets_provider()
                if isinstance(target, dict)
                and str(target.get("status") or "").strip().upper() == "HOLDING"
            ]
        if only_codes is None:
            with self._wakeup_lock:
                self._holding_codes = {
                    str(target.get("code") or target.get("stock_code") or "").strip()[:6]
                    for target in targets
                }
        else:
            targets = [target for target in targets
                       if str(target.get("code") or target.get("stock_code") or "").strip()[:6]
                       in only_codes]
        evaluated = 0
        for target in targets:
            code = str(target.get("code") or target.get("stock_code") or "").strip()[:6]
            if not code:
                continue
            try:
                snapshot = self._ws_snapshot_provider(code) or {}
                self._evaluator(target, code, snapshot, now_ts=observed_at)
                evaluated += 1
            except Exception as exc:  # fail isolated per symbol
                if self._error_handler is not None:
                    self._error_handler(f"{code}: {exc}")
        return evaluated

    def wake(self, code: str) -> None:
        """Coalesce WS notifications; bounded 0B/0D history remains the source."""
        normalized = str(code or "").strip()[:6]
        with self._wakeup_lock:
            if not normalized or normalized not in self._holding_codes:
                return
            if len(self._wake_codes) >= 256:
                self._wake_overflow = True
                self._wake_codes.clear()
            elif not self._wake_overflow:
                self._wake_codes.add(normalized)
            self._wakeup_event.set()

    def _run(self) -> None:
        next_full_poll = 0.0
        while not self._stop_event.is_set():
            if time.monotonic() >= next_full_poll:
                self.run_once()
                next_full_poll = time.monotonic() + self._interval_sec
                continue
            self._wakeup_event.wait(max(0.0, next_full_poll - time.monotonic()))
            with self._wakeup_lock:
                codes = set(self._wake_codes)
                overflow = self._wake_overflow
                self._wake_codes.clear()
                self._wake_overflow = False
                self._wakeup_event.clear()
            if self._stop_event.is_set():
                break
            if overflow:
                self.run_once()
                next_full_poll = time.monotonic() + self._interval_sec
            elif codes:
                self.run_once(only_codes=codes)
