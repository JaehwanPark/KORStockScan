"""Durable discovery/probe orchestration; no order or WATCHING authority."""

from __future__ import annotations

import json
import hashlib
import os
from pathlib import Path
from collections import OrderedDict
from copy import deepcopy
import re
from src.utils.kiwoom_utils import is_canonical_stock_code
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import threading
from math import isfinite

from src.trading.market import session_contract

from src.scanners.zero_base_discovery_queue import ACTIONS, DiscoveryQueue, RESULTS
from src.scanners.zero_base_discovery_source import (
    fetch_discovery_panels,
    discovery_product_filter,
)

PROBE_REQUEST_EVENT = "ZERO_BASE_PROBE_REQUESTED"
PROBE_RESULT_EVENT = "ZERO_BASE_PROBE_RESULT"
MACHINE_ENTER_EVENT = "ZERO_BASE_MACHINE_ENTER"
HANDOFF_ACK_EVENT = "ZERO_BASE_HANDOFF_CLOSED"
MAX_CONCURRENT_PROBES = 5
MAX_CLAIMS_PER_CYCLE = MAX_CONCURRENT_PROBES
MAX_DISCOVERY_OBSERVATION_AGE_SEC = 120
# One physical panel worker per process, including a session-date rollover.
_PANEL_EXECUTOR = ThreadPoolExecutor(
    max_workers=1, thread_name_prefix="discovery_panel"
)


class ZeroBaseDiscoveryRuntime:
    def __init__(
        self,
        *,
        event_bus,
        session_date: str,
        state_path: Path,
        claim_receipt_emitter=None,
        allocation_policy="current",
    ):
        # Explicit offline/candidate configuration only. Neither a restored
        # queue nor WS metadata may select a different service order.
        if type(allocation_policy) is not str or allocation_policy not in {
            "current", "eligible_wait", "service_wait"
        }:
            raise ValueError("zero_base_allocation_policy_invalid")
        self.allocation_policy = allocation_policy
        self.event_bus = event_bus
        self.state_path = Path(state_path)
        self.claim_receipt_emitter = claim_receipt_emitter
        self.queue = self._restore(session_date)
        self._results = OrderedDict()
        self._closed = False
        self._wake_lock = threading.Lock()
        self.wakeup = threading.Event()
        self._panel_future = None
        self._pending_promotions = []
        self._dirty = False
        self._admission_emitted = {}
        self._persisted_state = None
        self.event_bus.subscribe(PROBE_RESULT_EVENT, self._receive_result)
        self.event_bus.subscribe(HANDOFF_ACK_EVENT, self._receive_result)

    def _restore(self, session_date: str) -> DiscoveryQueue:
        self._restored_candidate_count = 0
        if not self.state_path.exists():
            return DiscoveryQueue(session_date)
        try:
            snapshot = json.loads(self.state_path.read_text())
            queue = DiscoveryQueue.restore(snapshot, session_date=session_date)
            self._restored_candidate_count = len(queue._candidates)
            return queue
        except (OSError, ValueError, TypeError, KeyError) as exc:
            # A corrupt ledger cannot silently turn into a fresh queue.
            raise RuntimeError("zero_base_queue_restore_failed") from exc

    def _persist(self):
        payload = json.dumps(self.queue.snapshot(), sort_keys=True)
        digest = hashlib.sha256(payload.encode()).hexdigest()

        def generation():
            try:
                s = self.state_path.stat()
                return (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
            except FileNotFoundError:
                return None

        current_generation = generation()
        if current_generation is not None and self._persisted_state == (
            digest, current_generation
        ):
            return
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.state_path.with_name(
            self.state_path.name + f".tmp.{os.getpid()}"
        )
        try:
            with temporary.open("w") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.state_path)
            directory_fd = os.open(self.state_path.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
            committed_generation = generation()
            self._persisted_state = (
                (digest, committed_generation)
                if committed_generation is not None else None
            )
        finally:
            temporary.unlink(missing_ok=True)

    def _receive_result(self, result):
        with self._wake_lock:
            if not self._closed and isinstance(result, dict):
                if (
                    result.get("handoff_closed") is not None
                    and type(result["handoff_closed"]) is not bool
                ):
                    return
                claim = result.get("claim") or {}
                if not self.queue.matches_claim(claim):
                    return
                row = self.queue._candidates[(claim["code"], claim["route"])]
                closed = result.get("handoff_closed") is True
                if closed:
                    if (
                        not row.handoff_id
                        or result.get("ws_handoff_id") != row.handoff_id
                    ):
                        return
                else:
                    candidate = result.get("candidate")
                    status, action = result.get("result"), result.get(
                        "machine_action", ""
                    )
                    if (
                        not isinstance(candidate, dict)
                        or any(
                            candidate.get(k) != claim.get(k)
                            for k in ("code", "route", "source_sha256")
                        )
                        or not isinstance(status, str)
                        or status not in RESULTS
                        or not isinstance(action, str)
                        or (status == "assessed") != (action in ACTIONS)
                    ):
                        return
                    # Preserve existing pre-worker/legacy no-lease responses.
                    # Supplied lease fields must bind the physical owner.
                    if any(
                        result.get(k) and result[k] != row.handoff_id
                        for k in ("physical_probe_lease_id", "ws_handoff_id")
                    ):
                        return
                key = (row.code, row.route, row.claim_count, closed)
                # At most RESULT + CLOSED for each of five physical leases.
                # Replayed notifications do not grow the callback inbox.
                self._results.setdefault(key, deepcopy(result))
                self.wakeup.set()

    def close(self):
        with self._wake_lock:
            self._closed = True
        self.event_bus.unsubscribe(PROBE_RESULT_EVENT, self._receive_result)
        self.event_bus.unsubscribe(HANDOFF_ACK_EVENT, self._receive_result)
        if self._panel_future is not None:
            self._panel_future.cancel()
        self.wakeup.set()

    def wait(self, timeout):
        with self._wake_lock:
            if self._results or (self._panel_future and self._panel_future.done()):
                return
            self.wakeup.clear()
        self.wakeup.wait(timeout)

    def start_scan(self, token, *, fetcher=fetch_discovery_panels):
        if self._closed or self._panel_future is not None:
            return False
        self._panel_future = _PANEL_EXECUTOR.submit(fetcher, token)

        def notify(_):
            with self._wake_lock:
                self.wakeup.set()

        self._panel_future.add_done_callback(notify)
        return True

    def finish_scan(self, *, now_epoch=None):
        future = self._panel_future
        if self._closed or future is None or not future.done():
            return None
        self._panel_future = None
        return self._apply_panel(future.result(), now_epoch=now_epoch)

    def drain_results(self, *, now_epoch=None) -> list[dict]:
        now_epoch = time.time() if now_epoch is None else float(now_epoch)
        drain_started = time.perf_counter()
        accepted = []
        promotions = self._pending_promotions
        ack_changed = False
        while True:
            with self._wake_lock:
                if not self._results:
                    break
                _, result = self._results.popitem(last=False)
            claim = result.get("claim")
            if result.get("handoff_closed") and isinstance(claim, dict):
                if self.queue.close_handoff(claim, result.get("ws_handoff_id")):
                    ack_changed = True
                continue
            candidate = result.get("candidate")
            status = str(result.get("result") or "")
            machine_action = str(result.get("machine_action") or "")
            if (
                not isinstance(claim, dict)
                or not isinstance(candidate, dict)
                or status not in RESULTS
                or candidate.get("code") != claim.get("code")
                or candidate.get("route") != claim.get("route")
                or candidate.get("source_sha256") != claim.get("source_sha256")
            ):
                continue
            due_sec = {
                "source_unavailable": 60,
                "required_feature_insufficient": 60,
                "pattern_not_matched": 60,
                "observation_incomplete": 60,
                "policy_unavailable": 120,
                "active_conflict": 60,
                "probe_capacity_deferred": 10,
            }.get(
                status,
                {"BLOCK": 180, "RECHECK": 30, "ENTER_NOW": 120}.get(
                    machine_action, 120
                ),
            )
            if not self.queue.resolve(
                claim,
                result=status,
                machine_action=machine_action,
                next_due_epoch=now_epoch + due_sec,
                handoff_id=result.get("physical_probe_lease_id")
                or result.get("ws_handoff_id", ""),
            ):
                continue
            accepted.append(result)
            if status == "assessed" and machine_action == "ENTER_NOW":
                result_epoch = result.get("result_epoch")
                if (
                    isinstance(result_epoch, (int, float))
                    and 0 <= now_epoch - result_epoch <= 5
                    and isinstance(result.get("machine_bundle_sha256"), str)
                    and re.fullmatch(r"[0-9a-f]{64}", result["machine_bundle_sha256"])
                ):
                    promotions.append(result)
        self._dirty = self._dirty or bool(accepted or promotions or ack_changed)
        if self._dirty:
            self._persist()
            self._dirty = False
        while promotions:
            result = promotions.pop(0)
            expected = result.get("native_observation")
            if result.get("physical_probe_lease_id") and expected is None:
                continue
            if expected is not None:
                from src.engine.scalping.reversal_source_diagnostics import (
                    observation_binding_valid,
                )

                # Persistence/retry is part of the original five seconds.
                if not observation_binding_valid(
                    expected, now=now_epoch + time.perf_counter() - drain_started
                ):
                    continue
            self.event_bus.publish(MACHINE_ENTER_EVENT, result)
        return accepted

    def dispatch_due_probes(self, *, now_epoch=None) -> dict:
        frozen_clock = now_epoch is not None
        dispatch_started_perf = time.perf_counter()
        now_epoch = time.time() if now_epoch is None else float(now_epoch)
        regime = session_contract.resolve_market_session(
            datetime.fromtimestamp(now_epoch, tz=session_contract.KST)
        ).session_regime
        eligible_routes = (
            {"nxt_only"}
            if regime == session_contract.MARKET_SESSION_REGIME_LEGACY_PREMARKET
            else (
                {"krx_nxt_integrated"}
                if regime
                in {
                    session_contract.MARKET_SESSION_REGIME_KRX_REGULAR,
                    session_contract.MARKET_SESSION_REGIME_KRX_NXT_AFTERMARKET,
                }
                else set()
            )
        )
        before_admission = deepcopy(self.queue)
        abandoned = self.queue.abandon_expired_claims(
            now_epoch=now_epoch,
            timeout_sec=60,
        )
        active_claims = self.queue.in_flight_count()
        check = getattr(self.event_bus, "consumer_readiness", None)
        readiness = (
            check(PROBE_REQUEST_EVENT)
            if callable(check)
            else {"ready": False, "reason": "consumer_readiness_unobserved"}
        )
        # The callback publishes its snapshot after the dispatch boundary.
        # Validate that observation at callback completion. Queue/claim/lease
        # clocks below remain the original boundary without budget renewal.
        snapshot_checked_epoch = (
            now_epoch + max(0.0, time.perf_counter() - dispatch_started_perf)
            if frozen_clock
            else time.time()
        )
        if self._closed:
            readiness = dict(readiness, ready=False, reason="discovery_runtime_closed")
        consumer_ready = readiness.get("ready") is True
        snapshot = readiness.get("main_target_snapshot")
        valid_snapshot = (
            isinstance(snapshot, dict)
            and snapshot.get("schema") == "zero_base_main_target_snapshot_v1"
            and snapshot.get("status") == "observed"
            and snapshot.get("runtime_effect") is False
            and all(
                snapshot.get(key) == readiness.get(key)
                and snapshot.get(key) is not None
                for key in (
                    "runtime_generation",
                    "process_pid",
                    "process_start_ticks",
                    "date",
                )
            )
            and snapshot.get("date") == self.queue.session_date
            and isinstance(snapshot.get("generation"), str)
            and re.fullmatch("[a-f0-9]{64}", snapshot["generation"]) is not None
            and type(snapshot.get("observed_epoch")) in (int, float)
            and isfinite(snapshot["observed_epoch"])
            and 0 <= snapshot_checked_epoch - snapshot["observed_epoch"] <= 2
            and isinstance(snapshot.get("active_codes"), list)
            and len(snapshot["active_codes"]) <= 512
            and all(is_canonical_stock_code(code) for code in snapshot["active_codes"])
        )
        active_codes = set(snapshot["active_codes"]) if valid_snapshot else set()
        from src.engine.scalping.reversal_source_diagnostics import (
            residence_requirements,
        )

        available_slots = (
            max(0, MAX_CONCURRENT_PROBES - active_claims) if consumer_ready else 0
        )
        rank_before = {
            key: (
                row.market, row.source_kind, row.discovery_volume,
                row.first_seen_epoch, row.last_claim_epoch,
                row.next_due_epoch, row.claim_count,
                row.long_residence_deferred_count,
            ) for key, row in self.queue._candidates.items()
        }
        claims = self.queue.claim(
            now_epoch=now_epoch,
            limit=min(MAX_CLAIMS_PER_CYCLE, available_slots),
            min_interval_sec=5,
            max_observation_age_sec=MAX_DISCOVERY_OBSERVATION_AGE_SEC,
            eligible_routes=eligible_routes,
            residence_requirements=residence_requirements,
            deferred_active_codes=active_codes,
            product_check=discovery_product_filter(self.queue.session_date),
            borrow_idle_short_slot=True,
            allocation_policy=self.allocation_policy,
            activity_claims_per_gainer=(
                7
                if regime == session_contract.MARKET_SESSION_REGIME_KRX_NXT_AFTERMARKET
                else 3
            ),
        )
        try:
            self._persist()  # No worker is admitted before its durable claim.
        except Exception:
            with self._wake_lock:
                self.queue = before_admission
            self._dirty = True
            raise
        dispatched = 0
        not_dispatched = 0
        for claim in claims:
            if self.claim_receipt_emitter is not None:
                self.claim_receipt_emitter(
                    "zero_base_probe_claim",
                    code=claim.get("code"),
                    name=claim.get("name"),
                    fields={
                        "zero_base_source_sha256": claim.get("source_sha256"),
                        "zero_base_route": claim.get("route"),
                        "zero_base_identifier_contract": "verified_common_stock_alphanumeric_v1",
                        "zero_base_product_master_sha256": self.queue.admission_state[
                            (claim["code"], claim["route"])
                        ][1],
                        "zero_base_claim_count": claim.get("claim_count"),
                        "zero_base_claim_observed_epoch": claim.get("observed_epoch"),
                        "zero_base_discovery_volume": claim.get("discovery_volume"),
                        "zero_base_source_kind": claim.get("source_kind"),
                        "physical_probe_lease_id": claim.get("physical_probe_lease_id"),
                    },
                )
            attempted = self.event_bus.publish_with_dispatch_count(
                PROBE_REQUEST_EVENT,
                {"claim": claim, "candidate": claim, "consumer_readiness": readiness},
            )
            if attempted:
                dispatched += 1
            else:
                # A subscriber can disappear during durable reservation I/O.
                # Only zero attempted callbacks proves that no physical WS
                # lease could have been requested by this publication.
                if not self.queue.resolve(
                    claim,
                    result="probe_capacity_deferred",
                    machine_action="",
                    next_due_epoch=now_epoch + 10,
                ):
                    raise RuntimeError("zero_base_unstarted_claim_resolution_failed")
                not_dispatched += 1
        if not_dispatched:
            self._persist()
        # Retain only changed per-symbol admission generations in the existing
        # pipeline. Repeated dispatches do not rewrite the whole durable queue.
        # This evidence is diagnostic; failed emission never changes a lease.
        from src.scanners.scanner_source_census import MAX_ROWS

        pending = {}
        for key, (reason, master_sha) in self.queue.admission_state.items():
            row = self.queue._candidates[key]
            # Rank inputs belong to the admission boundary, before claim mutates
            # last-claim/count and removes the observed eligible-wait clock.
            rank = rank_before[key] + (
                (
                    before_admission._eligible_since.get(key, now_epoch)
                    if reason == "claimed"
                    else self.queue._eligible_since.get(key)
                ),
            )
            state = (
                reason,
                row.observed_epoch,
                row.source_sha256,
                row.next_due_epoch,
                row.claim_count,
                master_sha,
                rank,
            )
            if self._admission_emitted.get(key) != state:
                pending[key] = state
        selected = list(pending.items())[:MAX_ROWS]
        admission_status = "not_configured"
        if self.claim_receipt_emitter is not None:
            try:
                outcome = (
                    self.claim_receipt_emitter(
                        "zero_base_probe_admission",
                        fields={
                            "zero_base_admission_schema": "per_symbol_admission_delta_v1",
                            "zero_base_admission_at_epoch": now_epoch,
                            "zero_base_admission_records": json.dumps(
                                [
                                    dict(
                                        code=key[0],
                                        route=key[1],
                                        reason=value[0],
                                        observed_epoch=value[1],
                                        source_sha256=value[2],
                                        next_due_epoch=value[3],
                                        claim_count=value[4],
                                        master_sha256=value[5],
                                        preclaim_rank=dict(zip(
                                            (
                                                "market", "source_kind", "discovery_volume",
                                                "first_seen_epoch", "last_claim_epoch",
                                                "next_due_epoch", "claim_count",
                                                "long_residence_deferred_count", "eligible_since_epoch",
                                            ),
                                            value[6],
                                        )),
                                    )
                                    for key, value in selected
                                ],
                                separators=(",", ":"),
                                allow_nan=False,
                            ),
                            "zero_base_admission_active_snapshot_generation": (
                                snapshot["generation"] if valid_snapshot else None
                            ),
                            "zero_base_admission_consumer_ready": consumer_ready,
                            "zero_base_admission_consumer_start_ticks": readiness.get(
                                "process_start_ticks"
                            ),
                            "zero_base_admission_available_slots": available_slots,
                            "zero_base_admission_pending_count": len(pending)
                            - len(selected),
                            "zero_base_admission_coverage": "dispatch_samples_only",
                            "zero_base_admission_rank_schema": "preclaim_rank_inputs_v1",
                            "zero_base_admission_claim_sequence_before": before_admission._claim_sequence,
                            "zero_base_admission_allocation_policy": self.allocation_policy,
                        },
                    )
                    if selected
                    else None
                )
                if selected and (
                    not isinstance(outcome, dict)
                    or outcome.get("structured_append_succeeded") is not True
                ):
                    admission_status = "append_unconfirmed"
                else:
                    self._admission_emitted.update(selected)
                    admission_status = "emitted" if selected else "unchanged"
            except Exception as exc:
                admission_status = "emit_failed:" + type(exc).__name__
        return {
            "probe_admission_diagnostic_status": admission_status,
            "probe_requested_count": dispatched,
            "probe_consumer_ready": consumer_ready,
            "probe_readiness": readiness,
            "probe_active_target_snapshot_status": (
                "observed" if valid_snapshot else "fallback"
            ),
            "probe_active_target_snapshot_generation": (
                snapshot["generation"] if valid_snapshot else None
            ),
            "probe_claim_eligibility": dict(self.queue.claim_eligibility),
            "queue_restored_candidate_count": self._restored_candidate_count,
            "probe_residence_deferred": dict(
                getattr(self.queue, "residence_deferred", {})
            ),
            "probe_no_consumer_count": not_dispatched,
            "probe_capacity_limit": MAX_CONCURRENT_PROBES,
            "probe_claims_in_flight_count": self.queue.in_flight_count(),
            "probe_timeout_count": abandoned,
            "stale_candidate_count": self.queue.stale_candidate_count(
                now_epoch=now_epoch,
                max_observation_age_sec=MAX_DISCOVERY_OBSERVATION_AGE_SEC,
            ),
            "queue_count": len(self.queue.snapshot()["candidates"]),
        }

    def scan_once(
        self, token, *, fetcher=fetch_discovery_panels, now_epoch=None
    ) -> dict:
        panel = fetcher(token)
        return self._apply_panel(panel, now_epoch=now_epoch)

    def _apply_panel(self, panel, *, now_epoch=None):
        observed = 0
        for row in panel.get("observations") or []:
            status = self.queue.observe(
                code=row["code"],
                route=row["route"],
                observed_epoch=row["observed_epoch"],
                source_sha256=row["source_sha256"],
                source_scope=row["source_scope"],
                received_epoch=row["observed_epoch"],
                name=row.get("name") or "",
                market=row.get("market") or "",
                venue=row.get("venue") or "",
                discovery_price=int(row.get("price") or 0),
                discovery_volume=int(row.get("volume") or 0),
                source_kind=row.get("source_kind") or "",
            )
            observed += status in {"queued", "updated"}
        dispatch = self.dispatch_due_probes(now_epoch=now_epoch)
        return {
            "panel_count": len(panel.get("panels") or []),
            "panels": list(panel.get("panels") or []),
            "observed_new_generation_count": observed,
            **dispatch,
        }
