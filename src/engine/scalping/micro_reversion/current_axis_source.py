"""Bounded in-memory copy of normalized collector rows for approved Entry AI.

No protocol parsing, subscriptions, provider calls or order authority. The
collector owns the enqueue/processed barrier; this store cannot certify it.
"""

from __future__ import annotations

from collections import deque
from copy import deepcopy
from datetime import datetime
import threading
from typing import Any
import weakref

_owner_lock = threading.Lock()
_owner: weakref.ReferenceType | None = None
_owner_conflict = False


def register_collector(collector: Any) -> None:
    global _owner, _owner_conflict
    with _owner_lock:
        previous = _owner() if _owner else None
        if previous is not None and previous is not collector and previous._accepting:
            # Multiple concurrent producers cannot silently replace custody.
            _owner_conflict = True
            return
        _owner = weakref.ref(collector)
        _owner_conflict = False


def live_source(symbol: str, *, captured_at_ms: int) -> dict:
    with _owner_lock:
        if _owner_conflict:
            raise ValueError("current_axis_multiple_collector_owners")
        owner = _owner() if _owner else None
    if owner is None:
        raise ValueError("current_axis_collector_not_registered")
    return owner.current_axis_source(symbol, captured_at_ms=captured_at_ms)


class CurrentAxisSourceBuffer:
    """Keep at most 256 scopes / 60,000 total rows / 12,000 per stream.

    Eviction is visible as a coverage boundary, not a silent complete source.
    A damaged/unscoped input clears the buffer; a new clean event may recover
    without a process restart or a permanent cumulative-counter veto.
    """

    def __init__(
        self,
        *,
        max_rows: int = 12_000,
        max_scopes: int = 256,
        max_total_rows: int = 60_000,
    ):
        self.max_rows = max_rows
        self.max_scopes = max_scopes
        self.max_total_rows = max_total_rows
        self._total_rows = 0
        self._lock = threading.Lock()
        self._invalid_lock = threading.Lock()
        self._rows: dict[tuple, dict[str, deque]] = {}
        self._coverage: dict[tuple, dict[str, int]] = {}
        self.generation = 0
        self._seen_generation = 0
        self._dirty_scopes: set[tuple[str, str]] = set()

    def invalidate(self) -> None:
        # Called by producer error counters: never wait for row copying or
        # bulk deallocation on the observer's callback thread.
        with self._invalid_lock:
            self.generation += 1

    def invalidate_scope(self, symbol: str, venue: str) -> None:
        if (
            not isinstance(symbol, str)
            or len(symbol) != 6
            or not symbol.isdigit()
            or venue not in {"KRX", "NXT", "SOR"}
        ):
            self.invalidate()
            return
        with self._invalid_lock:
            if len(self._dirty_scopes) >= 1024:
                self.generation += 1
                self._dirty_scopes.clear()
            self._dirty_scopes.add((symbol, venue))

    def scope_invalid(self, scope: tuple) -> bool:
        with self._invalid_lock:
            return scope[:2] in self._dirty_scopes

    def _flush_invalid_locked(self, scope: tuple) -> None:
        with self._invalid_lock:
            generation = self.generation
            dirty = scope[:2] in self._dirty_scopes
            self._dirty_scopes.discard(scope[:2])
        if generation != self._seen_generation:
            self._rows.clear()
            self._coverage.clear()
            self._total_rows = 0
            self._seen_generation = generation
        elif dirty:
            for key in list(self._rows):
                if key[:2] == scope[:2]:
                    self._total_rows -= sum(
                        len(rows) for rows in self._rows[key].values()
                    )
                    del self._rows[key]
                    del self._coverage[key]

    def add(self, kind: str, row: dict) -> None:
        scope = (
            row["symbol"],
            row["venue"],
            row["session_bucket"],
            row["sequence_epoch"],
        )
        stamp = row.get("local_receive_timestamp") or row.get("capture_started_at")
        timestamp_ms = int(datetime.fromisoformat(stamp).timestamp() * 1000)
        if row.get("path_consumer_eligible") is False:
            self.invalidate_scope(row["symbol"], row["venue"])
            return
        with self._lock:
            self._flush_invalid_locked(scope)
            if scope not in self._rows:
                if len(self._rows) >= self.max_scopes:
                    oldest = next(iter(self._rows))
                    self._total_rows -= sum(
                        len(rows) for rows in self._rows[oldest].values()
                    )
                    del self._rows[oldest]
                    del self._coverage[oldest]
                self._rows[scope] = {
                    name: deque() for name in ("market", "depth", "references")
                }
                self._coverage[scope] = {}
            queue = self._rows[scope][kind]
            if kind not in self._coverage[scope]:
                self._coverage[scope][kind] = (
                    0 if row.get("source_sequence") == 1 else timestamp_ms
                )
            if queue and timestamp_ms < queue[-1][0]:
                self.invalidate_scope(row["symbol"], row["venue"])
                self._total_rows -= (
                    sum(len(rows) for rows in streams.values())
                    if (streams := self._rows.get(scope))
                    else 0
                )
                del self._rows[scope]
                del self._coverage[scope]
                return
            queue.append((timestamp_ms, deepcopy(row)))
            self._total_rows += 1
            while len(queue) > self.max_rows or (
                queue and queue[0][0] < timestamp_ms - 240_000
            ):
                evicted_ms, _ = queue.popleft()
                self._total_rows -= 1
                self._coverage[scope][kind] = max(
                    self._coverage[scope][kind], evicted_ms + 1
                )
            while self._total_rows > self.max_total_rows:
                oldest = next(iter(self._rows))
                self._total_rows -= sum(
                    len(rows) for rows in self._rows[oldest].values()
                )
                del self._rows[oldest]
                del self._coverage[oldest]

    def snapshot(
        self,
        scope: tuple,
        *,
        captured_at_ms: int,
        market_sequence: int,
        depth_sequence: int,
    ) -> dict:
        with self._lock:
            self._flush_invalid_locked(scope)
            streams = self._rows.get(scope)
            if not streams or any(not streams[name] for name in streams):
                raise ValueError("current_axis_causal_source_warming_or_no_event")
            if (
                streams["market"][-1][1]["source_sequence"] != market_sequence
                or streams["depth"][-1][1]["source_sequence"] != depth_sequence
            ):
                raise ValueError("current_axis_collector_processing_pending")
            result = {
                key: [deepcopy(row) for stamp, row in rows if stamp <= captured_at_ms]
                for key, rows in streams.items()
            }
            result.update(
                {
                    "coverage_start_ms": max(
                        self._coverage[scope].get(key, captured_at_ms)
                        for key in ("market", "depth")
                    ),
                    "generation": self._seen_generation,
                    "sequence_epoch": scope[-1],
                    "collector_barrier_verified": True,
                    "provider_call_performed": False,
                    "actual_order_submitted": False,
                }
            )
            return result
