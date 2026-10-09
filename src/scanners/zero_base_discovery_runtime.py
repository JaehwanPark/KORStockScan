"""Durable discovery/probe orchestration; no order or WATCHING authority."""

from __future__ import annotations

import json
import os
from pathlib import Path
from collections import OrderedDict
from copy import deepcopy
import re
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import threading

from src.trading.market import session_contract

from src.scanners.zero_base_discovery_queue import DiscoveryQueue, RESULTS
from src.scanners.zero_base_discovery_source import fetch_discovery_panels


PROBE_REQUEST_EVENT = "ZERO_BASE_PROBE_REQUESTED"
PROBE_RESULT_EVENT = "ZERO_BASE_PROBE_RESULT"
MACHINE_ENTER_EVENT = "ZERO_BASE_MACHINE_ENTER"
HANDOFF_ACK_EVENT = 'ZERO_BASE_HANDOFF_CLOSED'
MAX_CONCURRENT_PROBES = 5
MAX_CLAIMS_PER_CYCLE = MAX_CONCURRENT_PROBES
MAX_DISCOVERY_OBSERVATION_AGE_SEC = 120
# One physical panel worker per process, including a session-date rollover.
_PANEL_EXECUTOR = ThreadPoolExecutor(max_workers=1, thread_name_prefix='discovery_panel')


class ZeroBaseDiscoveryRuntime:
    def __init__(self, *, event_bus, session_date: str, state_path: Path,
                 claim_receipt_emitter=None):
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
        self.event_bus.subscribe(PROBE_RESULT_EVENT, self._receive_result)
        self.event_bus.subscribe(HANDOFF_ACK_EVENT, self._receive_result)

    def _restore(self, session_date: str) -> DiscoveryQueue:
        if not self.state_path.exists():
            return DiscoveryQueue(session_date)
        try:
            snapshot = json.loads(self.state_path.read_text())
            return DiscoveryQueue.restore(snapshot, session_date=session_date)
        except (OSError, ValueError, TypeError, KeyError) as exc:
            # A corrupt ledger cannot silently turn into a fresh queue.
            raise RuntimeError("zero_base_queue_restore_failed") from exc

    def _persist(self):
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.state_path.with_name(
            self.state_path.name + f".tmp.{os.getpid()}"
        )
        try:
            with temporary.open("w") as stream:
                json.dump(self.queue.snapshot(), stream, sort_keys=True)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.state_path)
            directory_fd = os.open(self.state_path.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        finally:
            temporary.unlink(missing_ok=True)

    def _receive_result(self, result):
        with self._wake_lock:
            if not self._closed and isinstance(result, dict):
                claim = result.get('claim') or {}
                row = self.queue._candidates.get((claim.get('code'), claim.get('route')))
                if (row is None or not row.in_flight or row.claim_count != claim.get('claim_count')
                        or row.claimed_source_sha256 != claim.get('source_sha256')):
                    return
                key = (row.code, row.route, row.claim_count, bool(result.get('handoff_closed')))
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
            if result.get('handoff_closed') and isinstance(claim, dict):
                if self.queue.close_handoff(claim, result.get('ws_handoff_id')):
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
                "policy_unavailable": 120,
                "active_conflict": 60,
                "probe_capacity_deferred": 10,
            }.get(status, {"BLOCK": 180, "RECHECK": 30, "ENTER_NOW": 120}.get(machine_action, 120))
            if not self.queue.resolve(
                claim,
                result=status,
                machine_action=machine_action,
                next_due_epoch=now_epoch + due_sec,
                handoff_id=result.get('physical_probe_lease_id') or result.get('ws_handoff_id', ''),
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
            expected = result.get('native_observation')
            if result.get('physical_probe_lease_id') and expected is None:
                continue
            if expected is not None:
                from src.engine.scalping.reversal_source_diagnostics import observation_binding_valid
                # Persistence/retry is part of the original five seconds.
                if not observation_binding_valid(expected,
                        now=now_epoch + time.perf_counter() - drain_started):
                    continue
            self.event_bus.publish(MACHINE_ENTER_EVENT, result)
        return accepted

    def dispatch_due_probes(self, *, now_epoch=None) -> dict:
        now_epoch = time.time() if now_epoch is None else float(now_epoch)
        regime = session_contract.resolve_market_session(
            datetime.fromtimestamp(now_epoch, tz=session_contract.KST)
        ).session_regime
        eligible_routes = (
            {"nxt_only"}
            if regime == session_contract.MARKET_SESSION_REGIME_LEGACY_PREMARKET
            else {"krx_nxt_integrated"}
            if regime in {
                session_contract.MARKET_SESSION_REGIME_KRX_REGULAR,
                session_contract.MARKET_SESSION_REGIME_KRX_NXT_AFTERMARKET,
            }
            else set()
        )
        before_admission = deepcopy(self.queue)
        abandoned = self.queue.abandon_expired_claims(
            now_epoch=now_epoch, timeout_sec=60,
        )
        active_claims = self.queue.in_flight_count()
        available_slots = max(0, MAX_CONCURRENT_PROBES - active_claims)
        claims = self.queue.claim(
            now_epoch=now_epoch,
            limit=min(MAX_CLAIMS_PER_CYCLE, available_slots),
            min_interval_sec=5,
            max_observation_age_sec=MAX_DISCOVERY_OBSERVATION_AGE_SEC,
            eligible_routes=eligible_routes,
            activity_claims_per_gainer=(
                7 if regime == session_contract.MARKET_SESSION_REGIME_KRX_NXT_AFTERMARKET
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
        for claim in claims:
            if self.claim_receipt_emitter is not None:
                self.claim_receipt_emitter(
                    "zero_base_probe_claim",
                    code=claim.get("code"), name=claim.get("name"),
                    fields={
                        "zero_base_source_sha256": claim.get("source_sha256"),
                        "zero_base_route": claim.get("route"),
                        "zero_base_claim_count": claim.get("claim_count"),
                        "zero_base_claim_observed_epoch": claim.get("observed_epoch"),
                    },
                )
            self.event_bus.publish(
                PROBE_REQUEST_EVENT,
                {"claim": claim, "candidate": claim},
            )
        return {
            "probe_requested_count": len(claims),
            "probe_capacity_limit": MAX_CONCURRENT_PROBES,
            "probe_claims_in_flight_count": self.queue.in_flight_count(),
            "probe_timeout_count": abandoned,
            "stale_candidate_count": self.queue.stale_candidate_count(
                now_epoch=now_epoch,
                max_observation_age_sec=MAX_DISCOVERY_OBSERVATION_AGE_SEC,
            ),
            "queue_count": len(self.queue.snapshot()["candidates"]),
        }

    def scan_once(self, token, *, fetcher=fetch_discovery_panels, now_epoch=None) -> dict:
        panel = fetcher(token)
        return self._apply_panel(panel, now_epoch=now_epoch)

    def _apply_panel(self, panel, *, now_epoch=None):
        observed = 0
        for row in panel.get("observations") or []:
            status = self.queue.observe(
                code=row["code"], route=row["route"],
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
