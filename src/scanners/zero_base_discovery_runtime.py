"""Durable discovery/probe orchestration; no order or WATCHING authority."""

from __future__ import annotations

import json
import os
from pathlib import Path
from queue import Empty, SimpleQueue
import re
import time
from datetime import datetime

from src.trading.market import session_contract

from src.scanners.zero_base_discovery_queue import DiscoveryQueue, RESULTS
from src.scanners.zero_base_discovery_source import fetch_discovery_panels


PROBE_REQUEST_EVENT = "ZERO_BASE_PROBE_REQUESTED"
PROBE_RESULT_EVENT = "ZERO_BASE_PROBE_RESULT"
MACHINE_ENTER_EVENT = "ZERO_BASE_MACHINE_ENTER"
MAX_CLAIMS_PER_CYCLE = 12
MAX_DISCOVERY_OBSERVATION_AGE_SEC = 120


class ZeroBaseDiscoveryRuntime:
    def __init__(self, *, event_bus, session_date: str, state_path: Path):
        self.event_bus = event_bus
        self.state_path = Path(state_path)
        self.queue = self._restore(session_date)
        self._results = SimpleQueue()
        self.event_bus.subscribe(PROBE_RESULT_EVENT, self._receive_result)

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
        if isinstance(result, dict):
            self._results.put(dict(result))

    def close(self):
        self.event_bus.unsubscribe(PROBE_RESULT_EVENT, self._receive_result)

    def drain_results(self, *, now_epoch=None) -> list[dict]:
        now_epoch = time.time() if now_epoch is None else float(now_epoch)
        accepted = []
        promotions = []
        while True:
            try:
                result = self._results.get_nowait()
            except Empty:
                break
            claim = result.get("claim")
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
        if accepted:
            self._persist()
        for result in promotions:
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
        abandoned = self.queue.abandon_expired_claims(
            now_epoch=now_epoch, timeout_sec=60,
        )
        claims = self.queue.claim(
            now_epoch=now_epoch, limit=MAX_CLAIMS_PER_CYCLE,
            min_interval_sec=5,
            max_observation_age_sec=MAX_DISCOVERY_OBSERVATION_AGE_SEC,
            eligible_routes=eligible_routes,
            activity_claims_per_gainer=(
                7 if regime == session_contract.MARKET_SESSION_REGIME_KRX_NXT_AFTERMARKET
                else 3
            ),
        )
        self._persist()  # Persist claims before an asynchronous callback can arrive.
        for claim in claims:
            self.event_bus.publish(
                PROBE_REQUEST_EVENT,
                {"claim": claim, "candidate": claim},
            )
        return {
            "probe_requested_count": len(claims),
            "probe_timeout_count": abandoned,
            "stale_candidate_count": self.queue.stale_candidate_count(
                now_epoch=now_epoch,
                max_observation_age_sec=MAX_DISCOVERY_OBSERVATION_AGE_SEC,
            ),
            "queue_count": len(self.queue.snapshot()["candidates"]),
        }

    def scan_once(self, token, *, fetcher=fetch_discovery_panels, now_epoch=None) -> dict:
        panel = fetcher(token)
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
