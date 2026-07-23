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
        thread = self._thread
        if thread and thread is not threading.current_thread():
            thread.join(timeout=max(0.0, float(timeout)))

    def run_once(self, *, now_ts: float | None = None) -> int:
        observed_at = float(time.time() if now_ts is None else now_ts)
        with self._state_lock:
            targets = [
                target
                for target in self._targets_provider()
                if isinstance(target, dict)
                and str(target.get("status") or "").strip().upper() == "HOLDING"
            ]
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

    def _run(self) -> None:
        while not self._stop_event.is_set():
            started = time.monotonic()
            self.run_once()
            elapsed = max(0.0, time.monotonic() - started)
            self._stop_event.wait(max(0.0, self._interval_sec - elapsed))
