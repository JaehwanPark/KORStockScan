"""Source-bound discovery queue for the replacement SCALPING scanner.

This module owns candidate scheduling only. It never subscribes to market data,
calls a trading policy, attaches WATCHING, or submits an order.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime
from math import isfinite
import re
from zoneinfo import ZoneInfo


SCHEMA = "zero_base_discovery_queue_v1"
ROUTES = {"krx_only", "nxt_only", "krx_nxt_integrated"}
RESULTS = {
    "source_unavailable", "required_feature_insufficient", "policy_unavailable",
    "active_conflict", "probe_capacity_deferred", "assessed",
}
ACTIONS = {"ENTER_NOW", "RECHECK", "BLOCK"}


@dataclass
class Candidate:
    code: str
    route: str
    observed_epoch: float
    source_sha256: str
    source_scope: str
    name: str
    market: str
    venue: str
    discovery_price: int
    first_seen_epoch: float
    last_seen_epoch: float
    next_due_epoch: float
    last_claim_epoch: float = 0.0
    last_result: str = "queued"
    machine_action: str = ""
    claim_count: int = 0
    in_flight: bool = False
    discovery_volume: int = 0
    source_kind: str = ""
    claimed_observed_epoch: float = 0.0
    claimed_source_sha256: str = ""


class DiscoveryQueue:
    """Fair, replayable queue keyed by code and exact market-data route."""

    def __init__(self, session_date: str):
        self.session_date = date.fromisoformat(session_date).isoformat()
        self._candidates: dict[tuple[str, str], Candidate] = {}
        self._claim_sequence = 0

    def observe(
        self,
        *,
        code: str,
        route: str,
        observed_epoch: float,
        source_sha256: str,
        source_scope: str,
        received_epoch: float,
        name: str = "",
        market: str = "",
        venue: str = "",
        discovery_price: int = 0,
        discovery_volume: int = 0,
        source_kind: str = "",
    ) -> str:
        """Accept a fresh, exactly routed observation; never refresh it implicitly."""
        if re.fullmatch(r"\d{6}", code or "") is None:
            return "invalid_code"
        if route not in ROUTES:
            return "route_unknown"
        if re.fullmatch(r"[0-9a-f]{64}", source_sha256 or "") is None:
            return "source_hash_invalid"
        # No upstream producer currently proves whole-market coverage.
        if source_scope != "observed_panel":
            return "source_scope_unknown"
        if source_kind not in {"", "activity", "gainers"}:
            return "source_kind_unknown"
        if type(discovery_volume) is not int or discovery_volume < 0:
            return "source_volume_invalid"
        if not (
            isfinite(observed_epoch)
            and isfinite(received_epoch)
            and 0 < observed_epoch <= received_epoch
        ):
            return "source_clock_invalid"
        try:
            source_date = datetime.fromtimestamp(
                observed_epoch, ZoneInfo("Asia/Seoul")
            ).date().isoformat()
        except (OverflowError, OSError, ValueError):
            return "source_clock_invalid"
        if source_date != self.session_date:
            return "source_date_mismatch"
        key = (code, route)
        current = self._candidates.get(key)
        if current is not None:
            if observed_epoch < current.observed_epoch:
                return "stale_observation"
            if observed_epoch == current.observed_epoch:
                return (
                    "duplicate"
                    if (source_sha256, source_scope)
                    == (current.source_sha256, current.source_scope)
                    else "source_generation_conflict"
                )
            # Refresh the discovery hint without revoking an active WS probe.
            # Its separate claimed source remains exact for result binding.
            current.observed_epoch = observed_epoch
            current.source_sha256 = source_sha256
            current.source_scope = source_scope
            current.last_seen_epoch = received_epoch
            current.name = name or current.name
            current.market = market or current.market
            current.venue = venue or current.venue
            current.discovery_price = discovery_price or current.discovery_price
            current.discovery_volume = discovery_volume
            current.source_kind = source_kind
            # A new source generation makes a prior BLOCK eligible again.
            current.next_due_epoch = min(current.next_due_epoch, received_epoch)
            return "updated"
        self._candidates[key] = Candidate(
            code=code,
            route=route,
            observed_epoch=observed_epoch,
            source_sha256=source_sha256,
            source_scope=source_scope,
            name=name,
            market=market,
            venue=venue,
            discovery_price=discovery_price,
            first_seen_epoch=received_epoch,
            last_seen_epoch=received_epoch,
            next_due_epoch=received_epoch,
            discovery_volume=discovery_volume,
            source_kind=source_kind,
        )
        return "queued"

    def claim(
        self, *, now_epoch: float, limit: int, min_interval_sec: float = 0,
        max_observation_age_sec: float | None = None,
        eligible_routes: set[str] | None = None,
    ) -> list[dict]:
        """Return due generations, oldest last claim first, with a bounded budget."""
        if limit < 0 or min_interval_sec < 0:
            raise ValueError("negative queue budget")
        if max_observation_age_sec is not None and max_observation_age_sec <= 0:
            raise ValueError("invalid observation age budget")
        ready_by_cohort: dict[tuple[str, str, str], list[Candidate]] = {}
        cohort_claims: dict[tuple[str, str, str], int] = {}
        for candidate in self._candidates.values():
            # Activity is a discovery hint, not an entry decision. Reserve one
            # in four claims for other panels so they remain observable.
            kind = "activity" if candidate.source_kind == "activity" else "gainers"
            cohort = (candidate.market, candidate.route, kind)
            cohort_claims[cohort] = cohort_claims.get(cohort, 0) + candidate.claim_count
            if (
                (eligible_routes is None or candidate.route in eligible_routes)
                and
                candidate.next_due_epoch <= now_epoch
                and not candidate.in_flight
                and candidate.last_claim_epoch + min_interval_sec <= now_epoch
                and (
                    max_observation_age_sec is None
                    or 0 <= now_epoch - candidate.observed_epoch <= max_observation_age_sec
                )
            ):
                ready_by_cohort.setdefault(cohort, []).append(candidate)
        for cohort_ready in ready_by_cohort.values():
            cohort_ready.sort(key=lambda row: (
                row.last_claim_epoch,
                row.first_seen_epoch,
                -row.discovery_volume,
                row.code,
            ))
        ready = []
        while len(ready) < limit:
            available = [key for key, rows in ready_by_cohort.items() if rows]
            if not available:
                break
            preferred_kind = (
                "gainers" if (self._claim_sequence + len(ready)) % 4 == 3
                else "activity"
            )
            preferred = [key for key in available if key[2] == preferred_kind]
            cohort = min(preferred or available,
                         key=lambda key: (cohort_claims[key], key))
            ready.append(ready_by_cohort[cohort].pop(0))
            cohort_claims[cohort] += 1
        for candidate in ready:
            candidate.last_claim_epoch = now_epoch
            candidate.claim_count += 1
            candidate.in_flight = True
            candidate.claimed_observed_epoch = candidate.observed_epoch
            candidate.claimed_source_sha256 = candidate.source_sha256
        self._claim_sequence += len(ready)
        return [
            {
                "code": row.code,
                "route": row.route,
                "observed_epoch": row.observed_epoch,
                "source_sha256": row.source_sha256,
                "source_scope": row.source_scope,
                "name": row.name,
                "market": row.market,
                "venue": row.venue,
                "discovery_price": row.discovery_price,
                "discovery_volume": row.discovery_volume,
                "source_kind": row.source_kind,
                "claim_count": row.claim_count,
                "last_claim_epoch": row.last_claim_epoch,
            }
            for row in ready
        ]

    def abandon_expired_claims(self, *, now_epoch: float, timeout_sec: float) -> int:
        if timeout_sec <= 0:
            raise ValueError("invalid probe timeout")
        abandoned = 0
        for row in self._candidates.values():
            if row.in_flight and now_epoch - row.last_claim_epoch >= timeout_sec:
                row.in_flight = False
                row.claim_count += 1  # Invalidate any later result for the old claim.
                row.claimed_observed_epoch = 0.0
                row.claimed_source_sha256 = ""
                row.last_result = "probe_capacity_deferred"
                row.machine_action = ""
                row.next_due_epoch = now_epoch
                abandoned += 1
        return abandoned

    def stale_candidate_count(self, *, now_epoch: float, max_observation_age_sec: float) -> int:
        if max_observation_age_sec <= 0:
            raise ValueError("invalid observation age budget")
        return sum(
            now_epoch - row.observed_epoch > max_observation_age_sec
            for row in self._candidates.values()
        )

    def resolve(
        self,
        claim: dict,
        *,
        result: str,
        next_due_epoch: float,
        machine_action: str = "",
    ) -> bool:
        """Bind an assessment to the exact claimed generation."""
        if result not in RESULTS or (result == "assessed") != (machine_action in ACTIONS):
            raise ValueError("invalid assessment result")
        key = (str(claim.get("code") or ""), str(claim.get("route") or ""))
        row = self._candidates.get(key)
        if row is None or (
            claim.get("observed_epoch") != row.claimed_observed_epoch
            or claim.get("source_sha256") != row.claimed_source_sha256
            or any(
                claim.get(field) != getattr(row, field)
                for field in ("source_scope", "claim_count", "last_claim_epoch")
            )
        ):
            return False
        if (
            not row.in_flight
            or row.last_claim_epoch <= 0
            or not isfinite(next_due_epoch)
            or next_due_epoch < row.last_claim_epoch
        ):
            return False
        row.last_result = result
        row.machine_action = machine_action
        row.next_due_epoch = next_due_epoch
        if row.observed_epoch > row.claimed_observed_epoch:
            row.next_due_epoch = min(row.next_due_epoch, row.last_seen_epoch)
        row.in_flight = False
        row.claimed_observed_epoch = 0.0
        row.claimed_source_sha256 = ""
        return True

    def snapshot(self) -> dict:
        return {
            "schema": SCHEMA,
            "session_date": self.session_date,
            "claim_sequence": self._claim_sequence,
            "candidates": [
                asdict(row)
                for row in sorted(
                    self._candidates.values(), key=lambda row: (row.code, row.route)
                )
            ],
        }

    @classmethod
    def restore(cls, snapshot: dict, *, session_date: str) -> "DiscoveryQueue":
        queue = cls(session_date)
        if snapshot.get("schema") != SCHEMA or snapshot.get("session_date") != queue.session_date:
            raise ValueError("queue snapshot date or schema mismatch")
        sequence = snapshot.get("claim_sequence", 0)
        if type(sequence) is not int or sequence < 0:
            raise ValueError("invalid queue claim sequence")
        queue._claim_sequence = sequence
        for raw in snapshot.get("candidates", []):
            row = Candidate(**raw)
            if (
                re.fullmatch(r"\d{6}", row.code or "") is None
                or row.route not in ROUTES
                or re.fullmatch(r"[0-9a-f]{64}", row.source_sha256 or "") is None
                or row.source_scope != "observed_panel"
                or row.source_kind not in {"", "activity", "gainers"}
                or (row.market and row.market not in {"KOSPI", "KOSDAQ"})
                or (row.venue and row.venue not in {"KRX", "NXT", "SOR"})
                or row.discovery_price < 0
                or type(row.discovery_volume) is not int
                or row.discovery_volume < 0
                or not isfinite(row.claimed_observed_epoch)
                or row.claimed_observed_epoch < 0
                or (row.claimed_source_sha256 and re.fullmatch(
                    r"[0-9a-f]{64}", row.claimed_source_sha256,
                ) is None)
                or (not row.in_flight and (
                    row.claimed_observed_epoch or row.claimed_source_sha256
                ))
                or not all(
                    isfinite(value) and value >= 0
                    for value in (
                        row.observed_epoch,
                        row.first_seen_epoch,
                        row.last_seen_epoch,
                        row.next_due_epoch,
                        row.last_claim_epoch,
                    )
                )
                or row.claim_count < 0
                or row.last_result not in {"queued", *RESULTS}
                or (row.last_result == "assessed") != (row.machine_action in ACTIONS)
                or row.first_seen_epoch > row.last_seen_epoch
                or row.observed_epoch > row.last_seen_epoch
                or (row.in_flight and row.claim_count == 0)
            ):
                raise ValueError("invalid queue snapshot candidate")
            try:
                source_date = datetime.fromtimestamp(
                    row.observed_epoch, ZoneInfo("Asia/Seoul")
                ).date().isoformat()
            except (OverflowError, OSError, ValueError) as exc:
                raise ValueError("invalid queue snapshot source clock") from exc
            if source_date != queue.session_date:
                raise ValueError("queue snapshot source date mismatch")
            key = (row.code, row.route)
            if key in queue._candidates:
                raise ValueError("duplicate queue snapshot candidate")
            if row.in_flight:
                row.in_flight = False
                row.next_due_epoch = min(row.next_due_epoch, row.last_claim_epoch)
                row.claimed_observed_epoch = 0.0
                row.claimed_source_sha256 = ""
            queue._candidates[key] = row
        return queue
