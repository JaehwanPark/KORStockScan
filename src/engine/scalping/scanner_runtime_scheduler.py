"""Deadline-aware work scheduler for promoted SCALPING scanner targets.

The scheduler deliberately owns no trading state.  It stores immutable scanner
generation identifiers and timing metadata only; the sniper main thread remains
the sole owner of ``ACTIVE_TARGETS`` mutation and broker submission.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from enum import Enum
import heapq
import itertools
import threading
from collections import OrderedDict
from collections.abc import Mapping
from queue import Empty
from types import MappingProxyType
from typing import Any, Iterable

SCANNER_DEADLINE_SCHEDULER_VERSION = "scanner_deadline_scheduler_v1"
SCANNER_ASYNC_EVAL_VERSION = "scanner_async_eval_commit_v1"
SUPPORTED_SCANNER_SCHEDULER_MODES = frozenset({"legacy", "deadline_v1", "async_v1"})
SUPPORTED_SCANNER_SCHEDULER_VENUES = frozenset({"KRX", "PREMARKET_KRX_LIKE", "NXT"})


class ScannerLane(str, Enum):
    """Runtime lanes ordered only when absolute deadlines are equal."""

    SAFETY = "safety"
    COMMIT = "commit"
    FAST_PRECHECK = "fast_precheck"
    HOLDING = "holding"
    RECOVERY = "recovery"
    HEAVY_EVAL = "heavy_eval"


@dataclass(frozen=True, slots=True)
class ScannerPromotionEnvelope:
    """Thread-safe immutable handoff from the scanner callback to main runtime."""

    payload: Mapping[str, Any]
    enqueued_epoch: float

    @classmethod
    def from_payload(
        cls, payload: Mapping[str, Any] | None, *, enqueued_epoch: float
    ) -> "ScannerPromotionEnvelope":
        copied = deepcopy(dict(payload or {}))
        return cls(
            payload=MappingProxyType(copied),
            enqueued_epoch=float(enqueued_epoch),
        )


@dataclass(frozen=True, slots=True)
class ScannerPromotionInboxDecision:
    accepted: bool
    reason: str
    depth: int
    superseded_envelope: ScannerPromotionEnvelope | None = None


class ScannerPromotionInbox:
    """Bounded per-symbol coalescing handoff for scanner callback threads."""

    def __init__(self, *, max_active: int) -> None:
        self.max_active = max(1, int(max_active))
        self._lock = threading.Lock()
        self._items: OrderedDict[str, ScannerPromotionEnvelope] = OrderedDict()

    def put(self, envelope: ScannerPromotionEnvelope) -> ScannerPromotionInboxDecision:
        if not isinstance(envelope, ScannerPromotionEnvelope):
            raise TypeError("scanner promotion inbox requires immutable envelope")
        code = str(envelope.payload.get("code") or "").strip()[:6]
        if not code:
            return ScannerPromotionInboxDecision(
                accepted=False,
                reason="missing_code",
                depth=len(self),
            )
        with self._lock:
            superseded = None
            if code in self._items:
                superseded = self._items.pop(code, None)
            elif len(self._items) >= self.max_active:
                return ScannerPromotionInboxDecision(
                    accepted=False,
                    reason="inbox_capacity_reached",
                    depth=len(self._items),
                )
            self._items[code] = envelope
            return ScannerPromotionInboxDecision(
                accepted=True,
                reason=(
                    "latest_symbol_promotion_coalesced"
                    if superseded is not None
                    else "promotion_enqueued"
                ),
                depth=len(self._items),
                superseded_envelope=superseded,
            )

    def get_nowait(self) -> ScannerPromotionEnvelope:
        with self._lock:
            if not self._items:
                raise Empty
            _, envelope = self._items.popitem(last=False)
            return envelope

    def pending_for(self, code: str) -> ScannerPromotionEnvelope | None:
        """Return the immutable pending promotion for a symbol, if any.

        The submit owner uses this read-only snapshot for the final generation
        revalidation.  A callback that arrived during heavy evaluation must
        prevent the older generation from reaching the broker, even before the
        main thread has drained and attached the newer promotion.
        """

        normalized = str(code or "").strip()[:6]
        if not normalized:
            return None
        with self._lock:
            return self._items.get(normalized)

    def __len__(self) -> int:
        with self._lock:
            return len(self._items)


_LANE_TIE_PRIORITY = {
    ScannerLane.SAFETY: 0,
    ScannerLane.COMMIT: 1,
    ScannerLane.FAST_PRECHECK: 2,
    ScannerLane.HOLDING: 3,
    ScannerLane.RECOVERY: 4,
    ScannerLane.HEAVY_EVAL: 5,
}


def normalize_scanner_scheduler_mode(value: Any) -> str:
    normalized = str(value or "legacy").strip().lower()
    return normalized if normalized in SUPPORTED_SCANNER_SCHEDULER_MODES else "legacy"


def normalize_scanner_scheduler_venue(value: Any) -> str:
    normalized = str(value or "").strip().upper()
    aliases = {
        "PREMARKET": "PREMARKET_KRX_LIKE",
        "KRX_LIKE": "PREMARKET_KRX_LIKE",
        "PREMARKET_KRX": "PREMARKET_KRX_LIKE",
    }
    return aliases.get(normalized, normalized)


def parse_scanner_scheduler_venues(value: Any) -> frozenset[str]:
    tokens = {
        normalize_scanner_scheduler_venue(token)
        for token in str(value or "").split(",")
        if str(token).strip()
    }
    return frozenset(
        token for token in tokens if token in SUPPORTED_SCANNER_SCHEDULER_VENUES
    )


@dataclass(frozen=True, slots=True)
class ScannerGeneration:
    """Immutable identity and provenance for one scanner attach/refresh."""

    code: str
    promotion_id: str
    revision: int
    record_id: int | str | None
    venue: str
    promotion_epoch: float
    attach_epoch: float
    observed_price: int
    source_signature: str

    @property
    def generation_id(self) -> str:
        promotion = self.promotion_id or "not_available_promotion"
        return f"{self.code}:{promotion}:r{self.revision}"

    def timing_fields(self, *, now_epoch: float | None = None) -> dict[str, Any]:
        fields: dict[str, Any] = {
            "scheduler_version": SCANNER_DEADLINE_SCHEDULER_VERSION,
            "scanner_generation_id": self.generation_id,
            "scanner_generation_revision": self.revision,
            "scanner_promotion_id": self.promotion_id or "-",
            "scanner_promotion_emitted_epoch": round(self.promotion_epoch, 6),
            "scanner_attach_epoch": round(self.attach_epoch, 6),
            "effective_venue": self.venue or "UNKNOWN",
            "source_signature": self.source_signature or "-",
            "scanner_generation_observed_price": self.observed_price,
            "promotion_to_attach_sec": (
                round(max(0.0, self.attach_epoch - self.promotion_epoch), 6)
                if self.promotion_epoch > 0
                else "not_available_promotion_to_attach_sec"
            ),
        }
        if now_epoch is not None:
            fields["watch_age_sec"] = round(
                max(0.0, float(now_epoch) - self.attach_epoch), 6
            )
        return fields


@dataclass(frozen=True, slots=True)
class ScannerWorkItem:
    generation: ScannerGeneration
    lane: ScannerLane
    owner: str
    enqueued_epoch: float
    deadline_epoch: float
    priority: int = 0
    attempt: int = 1
    precheck_phase: str = "not_applicable"

    @property
    def work_id(self) -> str:
        return f"{self.generation.generation_id}:{self.lane.value}:a{self.attempt}"


@dataclass(frozen=True, slots=True)
class ScannerSchedulerDecision:
    action: str
    reason: str
    decided_epoch: float
    item: ScannerWorkItem | None = None
    superseded_work_ids: tuple[str, ...] = ()
    fields: dict[str, Any] = field(default_factory=dict)


class ScannerRuntimeScheduler:
    """Coalesce per-symbol work and dispatch it by deadline.

    ``next_decision`` returns an explicit ``deadline_expired`` decision instead
    of silently discarding overdue work.  Callers may build a fresh generation
    from current WS context, but an expired generation must never be submitted.
    """

    _DEFAULT_DEADLINE_SEC = {
        ScannerLane.SAFETY: 0.0,
        ScannerLane.COMMIT: 1.0,
        ScannerLane.FAST_PRECHECK: 10.0,
        ScannerLane.HOLDING: 1.0,
        ScannerLane.RECOVERY: 10.0,
        ScannerLane.HEAVY_EVAL: 15.0,
    }

    def __init__(self, *, max_active: int) -> None:
        self.max_active = max(1, int(max_active))
        self._lock = threading.RLock()
        self._sequence = itertools.count()
        self._revisions: dict[str, int] = {}
        self._generations: dict[str, ScannerGeneration] = {}
        self._work_by_id: dict[str, ScannerWorkItem] = {}
        self._heap: list[tuple[float, int, int, int, str]] = []
        self._in_flight: dict[str, ScannerWorkItem] = {}
        self._dispatched_epoch_by_work_id: dict[str, float] = {}
        self._first_precheck_dispatched_generation_ids: set[str] = set()
        self._blocking_heavy_since_precheck = 0

    def current_generation(self, code: str) -> ScannerGeneration | None:
        with self._lock:
            return self._generations.get(str(code or "").strip()[:6])

    def is_current(self, generation: ScannerGeneration | None) -> bool:
        if generation is None:
            return False
        with self._lock:
            current = self._generations.get(generation.code)
            return bool(current and current.generation_id == generation.generation_id)

    def register_generation(
        self,
        *,
        code: str,
        promotion_id: str,
        record_id: int | str | None,
        venue: str,
        promotion_epoch: float,
        attach_epoch: float,
        observed_price: int,
        source_signature: str,
        enqueue_precheck: bool = True,
    ) -> ScannerSchedulerDecision:
        norm_code = str(code or "").strip()[:6]
        if not norm_code:
            raise ValueError("scanner generation requires code")
        normalized_venue = normalize_scanner_scheduler_venue(venue)
        decided_epoch = float(attach_epoch)
        normalized_promotion_id = str(promotion_id or "").strip()
        normalized_promotion_epoch = max(0.0, float(promotion_epoch or 0.0))
        if (
            not normalized_promotion_id
            or normalized_promotion_epoch <= 0
            or decided_epoch <= 0
            or decided_epoch < normalized_promotion_epoch
            or normalized_venue not in SUPPORTED_SCANNER_SCHEDULER_VENUES
        ):
            return ScannerSchedulerDecision(
                action="generation_rejected",
                reason="invalid_generation_provenance",
                decided_epoch=decided_epoch,
                fields={
                    "scheduler_version": SCANNER_DEADLINE_SCHEDULER_VERSION,
                    "scheduler_action": "generation_rejected",
                    "scanner_generation_code": norm_code,
                    "scanner_promotion_id": normalized_promotion_id or "-",
                    "scanner_promotion_emitted_epoch": (
                        round(normalized_promotion_epoch, 6)
                        if normalized_promotion_epoch > 0
                        else "not_available_promotion_epoch"
                    ),
                    "scanner_attach_epoch": (
                        round(decided_epoch, 6)
                        if decided_epoch > 0
                        else "not_available_attach_epoch"
                    ),
                    "effective_venue": normalized_venue or "UNKNOWN",
                },
            )
        with self._lock:
            if (
                norm_code not in self._generations
                and len(self._generations) >= self.max_active
            ):
                return ScannerSchedulerDecision(
                    action="capacity_rejected",
                    reason="scanner_generation_cap_reached",
                    decided_epoch=decided_epoch,
                    fields={
                        "scheduler_version": SCANNER_DEADLINE_SCHEDULER_VERSION,
                        "scheduler_action": "capacity_rejected",
                        "scheduler_generation_count": len(self._generations),
                        "scheduler_max_active": self.max_active,
                        "effective_venue": normalized_venue or "UNKNOWN",
                        "scanner_generation_code": norm_code,
                    },
                )
            revision = self._revisions.get(norm_code, 0) + 1
            self._revisions[norm_code] = revision
            generation = ScannerGeneration(
                code=norm_code,
                promotion_id=normalized_promotion_id,
                revision=revision,
                record_id=record_id,
                venue=normalized_venue or "UNKNOWN",
                promotion_epoch=normalized_promotion_epoch,
                attach_epoch=max(0.0, decided_epoch),
                observed_price=max(0, int(observed_price or 0)),
                source_signature=str(source_signature or "").strip(),
            )
            superseded = self._invalidate_code_locked(norm_code)
            self._generations[norm_code] = generation
            if enqueue_precheck:
                self._enqueue_locked(
                    generation,
                    lane=ScannerLane.FAST_PRECHECK,
                    owner="scanner_runtime_attach",
                    enqueued_epoch=decided_epoch,
                )
            fields = generation.timing_fields(now_epoch=decided_epoch)
            fields.update(
                {
                    "scheduler_action": "generation_registered",
                    "scheduler_queue_depth": len(self._work_by_id),
                    "scheduler_in_flight_count": len(self._in_flight),
                }
            )
            return ScannerSchedulerDecision(
                action="generation_registered",
                reason="latest_generation_wins",
                decided_epoch=decided_epoch,
                item=self._latest_item_locked(generation),
                superseded_work_ids=tuple(superseded),
                fields=fields,
            )

    def enqueue(
        self,
        generation: ScannerGeneration,
        *,
        lane: ScannerLane | str,
        owner: str,
        enqueued_epoch: float,
        deadline_epoch: float | None = None,
        priority: int = 0,
        attempt: int = 1,
    ) -> ScannerSchedulerDecision:
        normalized_lane = (
            lane if isinstance(lane, ScannerLane) else ScannerLane(str(lane))
        )
        now_epoch = float(enqueued_epoch)
        with self._lock:
            if not self.is_current(generation):
                return ScannerSchedulerDecision(
                    action="superseded",
                    reason="generation_not_current",
                    decided_epoch=now_epoch,
                    fields=generation.timing_fields(now_epoch=now_epoch),
                )
            item = self._enqueue_locked(
                generation,
                lane=normalized_lane,
                owner=owner,
                enqueued_epoch=now_epoch,
                deadline_epoch=deadline_epoch,
                priority=priority,
                attempt=attempt,
            )
            return ScannerSchedulerDecision(
                action="enqueued",
                reason="deadline_lane_enqueued",
                decided_epoch=now_epoch,
                item=item,
                fields=self._decision_fields(item, now_epoch=now_epoch),
            )

    def next_decision(
        self,
        *,
        now_epoch: float,
        allowed_lanes: Iterable[ScannerLane | str] | None = None,
    ) -> ScannerSchedulerDecision | None:
        now_value = float(now_epoch)
        allowed = (
            {
                lane if isinstance(lane, ScannerLane) else ScannerLane(str(lane))
                for lane in allowed_lanes
            }
            if allowed_lanes is not None
            else None
        )
        with self._lock:
            deferred: list[tuple[float, int, int, int, str]] = []
            selected: ScannerWorkItem | None = None
            if self._blocking_heavy_since_precheck >= 2 and (
                allowed is None or ScannerLane.FAST_PRECHECK in allowed
            ):
                pending_prechecks = [
                    item
                    for item in self._work_by_id.values()
                    if item.lane is ScannerLane.FAST_PRECHECK
                    and self.is_current(item.generation)
                ]
                if pending_prechecks:
                    selected = min(
                        pending_prechecks,
                        key=self._precheck_selection_key_locked,
                    )
                    self._work_by_id.pop(selected.work_id, None)
                    self._remove_heap_work_id_locked(selected.work_id)
            while self._heap:
                if selected is not None:
                    break
                entry = heapq.heappop(self._heap)
                work_id = entry[-1]
                item = self._work_by_id.get(work_id)
                if item is None:
                    continue
                if not self.is_current(item.generation):
                    self._work_by_id.pop(work_id, None)
                    continue
                if allowed is not None and item.lane not in allowed:
                    deferred.append(entry)
                    continue
                selected = item
                self._work_by_id.pop(work_id, None)
                break
            for entry in deferred:
                heapq.heappush(self._heap, entry)
            if selected is None:
                return None
            if (
                selected.lane is ScannerLane.FAST_PRECHECK
                and selected.precheck_phase == "recheck"
            ):
                pending_initial_prechecks = [
                    item
                    for item in self._work_by_id.values()
                    if item.lane is ScannerLane.FAST_PRECHECK
                    and item.precheck_phase == "initial"
                    and self.is_current(item.generation)
                ]
                if pending_initial_prechecks:
                    reserved = min(
                        pending_initial_prechecks,
                        key=self._precheck_selection_key_locked,
                    )
                    self._work_by_id[selected.work_id] = selected
                    heapq.heappush(
                        self._heap,
                        self._heap_entry_locked(selected),
                    )
                    selected = reserved
                    self._work_by_id.pop(selected.work_id, None)
                    self._remove_heap_work_id_locked(selected.work_id)

            fields = self._decision_fields(selected, now_epoch=now_value)
            if (
                selected.lane is not ScannerLane.SAFETY
                and now_value > selected.deadline_epoch
            ):
                fields["deadline_overrun_sec"] = round(
                    now_value - selected.deadline_epoch, 6
                )
                return ScannerSchedulerDecision(
                    action="deadline_expired",
                    reason="work_deadline_elapsed_before_dispatch",
                    decided_epoch=now_value,
                    item=selected,
                    fields=fields,
                )

            self._in_flight[selected.work_id] = selected
            self._dispatched_epoch_by_work_id[selected.work_id] = now_value
            self._record_dispatch_locked(selected)
            fields["scanner_scheduler_dispatched_epoch"] = round(now_value, 6)
            return ScannerSchedulerDecision(
                action="dispatch",
                reason="earliest_deadline_first",
                decided_epoch=now_value,
                item=selected,
                fields=fields,
            )

    def claim(
        self,
        generation: ScannerGeneration,
        *,
        lane: ScannerLane | str,
        now_epoch: float,
    ) -> ScannerSchedulerDecision:
        """Claim work only when it is the earliest item in the requested lane."""

        normalized_lane = (
            lane if isinstance(lane, ScannerLane) else ScannerLane(str(lane))
        )
        now_value = float(now_epoch)
        with self._lock:
            if not self.is_current(generation):
                return ScannerSchedulerDecision(
                    action="superseded",
                    reason="generation_not_current",
                    decided_epoch=now_value,
                    fields=generation.timing_fields(now_epoch=now_value),
                )
            candidates = [
                item
                for item in self._work_by_id.values()
                if item.lane is normalized_lane and self.is_current(item.generation)
            ]
            if not candidates:
                return ScannerSchedulerDecision(
                    action="missing",
                    reason="generation_lane_not_enqueued",
                    decided_epoch=now_value,
                    fields=generation.timing_fields(now_epoch=now_value),
                )
            if (
                normalized_lane is ScannerLane.HEAVY_EVAL
                and self._blocking_heavy_since_precheck >= 2
            ):
                pending_prechecks = [
                    item
                    for item in self._work_by_id.values()
                    if item.lane is ScannerLane.FAST_PRECHECK
                    and self.is_current(item.generation)
                ]
                if pending_prechecks:
                    selected_precheck = min(
                        pending_prechecks,
                        key=self._precheck_selection_key_locked,
                    )
                    return ScannerSchedulerDecision(
                        action="not_next",
                        reason="fast_precheck_starvation_guard",
                        decided_epoch=now_value,
                        item=selected_precheck,
                        fields=self._decision_fields(
                            selected_precheck, now_epoch=now_value
                        ),
                    )
            selected = min(
                candidates,
                key=(
                    self._precheck_selection_key_locked
                    if normalized_lane is ScannerLane.FAST_PRECHECK
                    else lambda item: (
                        item.deadline_epoch,
                        _LANE_TIE_PRIORITY[item.lane],
                        -item.priority,
                        item.enqueued_epoch,
                        item.work_id,
                    )
                ),
            )
            if selected.generation.generation_id != generation.generation_id:
                return ScannerSchedulerDecision(
                    action="not_next",
                    reason="earlier_deadline_generation_pending",
                    decided_epoch=now_value,
                    item=selected,
                    fields=self._decision_fields(selected, now_epoch=now_value),
                )
            self._work_by_id.pop(selected.work_id, None)
            self._remove_heap_work_id_locked(selected.work_id)
            fields = self._decision_fields(selected, now_epoch=now_value)
            if (
                selected.lane is not ScannerLane.SAFETY
                and now_value > selected.deadline_epoch
            ):
                fields["deadline_overrun_sec"] = round(
                    now_value - selected.deadline_epoch, 6
                )
                return ScannerSchedulerDecision(
                    action="deadline_expired",
                    reason="work_deadline_elapsed_before_dispatch",
                    decided_epoch=now_value,
                    item=selected,
                    fields=fields,
                )
            self._in_flight[selected.work_id] = selected
            self._dispatched_epoch_by_work_id[selected.work_id] = now_value
            self._record_dispatch_locked(selected)
            fields["scanner_scheduler_dispatched_epoch"] = round(now_value, 6)
            return ScannerSchedulerDecision(
                action="dispatch",
                reason="earliest_deadline_first",
                decided_epoch=now_value,
                item=selected,
                fields=fields,
            )

    def complete(
        self,
        item: ScannerWorkItem,
        *,
        completed_epoch: float,
        outcome: str,
    ) -> ScannerSchedulerDecision:
        now_value = float(completed_epoch)
        with self._lock:
            self._in_flight.pop(item.work_id, None)
            dispatched_epoch = self._dispatched_epoch_by_work_id.pop(
                item.work_id, item.enqueued_epoch
            )
            current = self.is_current(item.generation)
            action = "completed" if current else "superseded_result"
            fields = self._decision_fields(item, now_epoch=dispatched_epoch)
            fields.update(
                {
                    "scheduler_outcome": str(outcome or "-"),
                    "work_service_sec": round(
                        max(0.0, now_value - dispatched_epoch), 6
                    ),
                    "scanner_scheduler_dispatched_epoch": round(dispatched_epoch, 6),
                    "scanner_scheduler_completed_epoch": round(now_value, 6),
                    "completion_watch_age_sec": round(
                        max(0.0, now_value - item.generation.attach_epoch), 6
                    ),
                    "result_current_generation": current,
                }
            )
            return ScannerSchedulerDecision(
                action=action,
                reason=(
                    "current_generation_completed"
                    if current
                    else "generation_superseded_while_in_flight"
                ),
                decided_epoch=now_value,
                item=item,
                fields=fields,
            )

    def invalidate(
        self, code: str, *, now_epoch: float, reason: str
    ) -> ScannerSchedulerDecision:
        norm_code = str(code or "").strip()[:6]
        with self._lock:
            superseded = self._invalidate_code_locked(norm_code)
            generation = self._generations.pop(norm_code, None)
            return ScannerSchedulerDecision(
                action="invalidated",
                reason=str(reason or "runtime_target_invalidated"),
                decided_epoch=float(now_epoch),
                superseded_work_ids=tuple(superseded),
                fields=(
                    generation.timing_fields(now_epoch=float(now_epoch))
                    if generation
                    else {
                        "scheduler_version": SCANNER_DEADLINE_SCHEDULER_VERSION,
                        "scanner_generation_id": "not_available_generation",
                    }
                ),
            )

    def snapshot_metrics(self, *, now_epoch: float) -> dict[str, Any]:
        with self._lock:
            oldest = min(
                (item.enqueued_epoch for item in self._work_by_id.values()),
                default=float(now_epoch),
            )
            lane_counts = {
                lane.value: sum(
                    1 for item in self._work_by_id.values() if item.lane is lane
                )
                for lane in ScannerLane
            }
            return {
                "scheduler_version": SCANNER_DEADLINE_SCHEDULER_VERSION,
                "scheduler_queue_depth": len(self._work_by_id),
                "scheduler_heap_depth": len(self._heap),
                "scheduler_in_flight_count": len(self._in_flight),
                "scheduler_generation_count": len(self._generations),
                "scheduler_blocking_heavy_since_precheck": (
                    self._blocking_heavy_since_precheck
                ),
                "scheduler_oldest_wait_sec": round(
                    max(0.0, float(now_epoch) - oldest), 6
                ),
                "scheduler_lane_counts": lane_counts,
            }

    def generation_codes(self) -> frozenset[str]:
        """Return an immutable snapshot for main-thread reconciliation only."""

        with self._lock:
            return frozenset(self._generations)

    def _enqueue_locked(
        self,
        generation: ScannerGeneration,
        *,
        lane: ScannerLane,
        owner: str,
        enqueued_epoch: float,
        deadline_epoch: float | None = None,
        priority: int = 0,
        attempt: int = 1,
    ) -> ScannerWorkItem:
        deadline = (
            float(deadline_epoch)
            if deadline_epoch is not None
            else float(enqueued_epoch) + self._DEFAULT_DEADLINE_SEC[lane]
        )
        item = ScannerWorkItem(
            generation=generation,
            lane=lane,
            owner=str(owner or "unknown"),
            enqueued_epoch=float(enqueued_epoch),
            deadline_epoch=deadline,
            priority=int(priority),
            attempt=max(1, int(attempt)),
            precheck_phase=(
                "initial"
                if (
                    lane is ScannerLane.FAST_PRECHECK
                    and generation.generation_id
                    not in self._first_precheck_dispatched_generation_ids
                )
                else (
                    "recheck"
                    if lane is ScannerLane.FAST_PRECHECK
                    else "not_applicable"
                )
            ),
        )
        # Coalesce repeated scheduling of the same generation/lane.
        for work_id, current in list(self._work_by_id.items()):
            if (
                current.generation.generation_id == generation.generation_id
                and current.lane is lane
            ):
                self._work_by_id.pop(work_id, None)
                self._remove_heap_work_id_locked(work_id)
        self._work_by_id[item.work_id] = item
        heapq.heappush(self._heap, self._heap_entry_locked(item))
        return item

    def _record_dispatch_locked(self, item: ScannerWorkItem) -> None:
        if item.lane is ScannerLane.FAST_PRECHECK:
            if item.precheck_phase == "initial":
                self._first_precheck_dispatched_generation_ids.add(
                    item.generation.generation_id
                )
            self._blocking_heavy_since_precheck = 0
        elif item.lane is ScannerLane.HEAVY_EVAL:
            self._blocking_heavy_since_precheck += 1

    def _invalidate_code_locked(self, code: str) -> list[str]:
        superseded: list[str] = []
        current_generation = self._generations.get(code)
        if current_generation is not None:
            self._first_precheck_dispatched_generation_ids.discard(
                current_generation.generation_id
            )
        for work_id, item in list(self._work_by_id.items()):
            if item.generation.code == code:
                superseded.append(work_id)
                self._work_by_id.pop(work_id, None)
                self._remove_heap_work_id_locked(work_id)
        # In-flight work cannot be killed safely.  Removing it marks any later
        # completion as superseded; the worker may still finish observation.
        for work_id, item in list(self._in_flight.items()):
            if item.generation.code == code:
                superseded.append(work_id)
                self._in_flight.pop(work_id, None)
                self._dispatched_epoch_by_work_id.pop(work_id, None)
        return superseded

    def _heap_entry_locked(
        self, item: ScannerWorkItem
    ) -> tuple[float, int, int, int, str]:
        return (
            item.deadline_epoch,
            _LANE_TIE_PRIORITY[item.lane],
            -item.priority,
            next(self._sequence),
            item.work_id,
        )

    @staticmethod
    def _precheck_selection_key_locked(
        item: ScannerWorkItem,
    ) -> tuple[int, float, int, float, str]:
        # A generation that has never reached its first WS-only precheck owns
        # admission ahead of recurring rechecks.  Deadlines remain EDF within
        # each phase, so one already-observed symbol cannot consume the
        # attach-to-first-precheck budget of newly attached generations.
        return (
            0 if item.precheck_phase == "initial" else 1,
            item.deadline_epoch,
            -item.priority,
            item.enqueued_epoch,
            item.work_id,
        )

    def _remove_heap_work_id_locked(self, work_id: str) -> None:
        if not self._heap:
            return
        retained = [entry for entry in self._heap if entry[-1] != work_id]
        if len(retained) == len(self._heap):
            return
        self._heap = retained
        heapq.heapify(self._heap)

    def _latest_item_locked(
        self, generation: ScannerGeneration
    ) -> ScannerWorkItem | None:
        return next(
            (
                item
                for item in self._work_by_id.values()
                if item.generation.generation_id == generation.generation_id
            ),
            None,
        )

    @staticmethod
    def _decision_fields(item: ScannerWorkItem, *, now_epoch: float) -> dict[str, Any]:
        fields = item.generation.timing_fields(now_epoch=now_epoch)
        fields.update(
            {
                "scanner_scheduler_lane": item.lane.value,
                "scanner_scheduler_owner": item.owner,
                "scanner_scheduler_work_id": item.work_id,
                "scanner_scheduler_attempt": item.attempt,
                "scanner_scheduler_priority": item.priority,
                "scanner_scheduler_precheck_phase": item.precheck_phase,
                "scanner_scheduler_enqueued_epoch": round(item.enqueued_epoch, 6),
                "scanner_scheduler_deadline_epoch": round(item.deadline_epoch, 6),
                "scanner_scheduler_queue_wait_sec": round(
                    max(0.0, now_epoch - item.enqueued_epoch), 6
                ),
            }
        )
        if item.lane is ScannerLane.FAST_PRECHECK:
            if item.precheck_phase == "initial":
                fields["attach_to_first_precheck_sec"] = round(
                    max(0.0, now_epoch - item.generation.attach_epoch), 6
                )
            else:
                fields["precheck_recheck_wait_sec"] = round(
                    max(0.0, now_epoch - item.enqueued_epoch), 6
                )
        elif item.lane is ScannerLane.RECOVERY:
            fields["precheck_to_recovery_sec"] = round(
                max(0.0, now_epoch - item.enqueued_epoch), 6
            )
        elif item.lane is ScannerLane.HEAVY_EVAL:
            fields["precheck_to_heavy_dispatch_sec"] = round(
                max(0.0, now_epoch - item.enqueued_epoch), 6
            )
        return fields
