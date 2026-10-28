"""Source-bound discovery queue for the replacement SCALPING scanner.

This module owns candidate scheduling only. It never subscribes to market data,
calls a trading policy, attaches WATCHING, or submits an order.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from copy import deepcopy
from datetime import date, datetime
from math import isfinite
import re
from src.utils.kiwoom_utils import is_canonical_stock_code
import uuid
from zoneinfo import ZoneInfo

SCHEMA = "zero_base_discovery_queue_v3"
ROUTES = {"krx_only", "nxt_only", "krx_nxt_integrated"}
RESULTS = {
    "source_unavailable",
    "required_feature_insufficient",
    "policy_unavailable",
    "active_conflict",
    "probe_capacity_deferred",
    "assessed",
    "pattern_not_matched",
    "observation_incomplete",
}
ACTIONS = {"ENTER_NOW", "RECHECK", "BLOCK"}
MAX_LONG_PROBES = 4  # Base reservation; runtime may borrow the idle fifth slot.


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
    residence_deadline_epoch: float = 0.0
    lease_phase: str = "closed"
    handoff_id: str = ""
    residence_wait_since_epoch: float = 0.0
    long_residence_deferred_count: int = 0

    def __deepcopy__(self, memo):
        # Native fields are scalar. Retain ordinary deepcopy semantics for
        # unexpected/mutable extensions without walking every scalar value.
        result = type(self).__new__(type(self))
        memo[id(self)] = result
        result.__dict__ = {
            key: (
                value
                if type(value) in (str, int, float, bool, type(None))
                else deepcopy(value, memo)
            )
            for key, value in vars(self).items()
        }
        return result

    def _snapshot(self):
        fields = vars(self)
        if fields.keys() == self.__dataclass_fields__.keys() and all(
            type(value) in (str, int, float, bool, type(None))
            for value in fields.values()
        ):
            return fields.copy()
        return asdict(self)


class DiscoveryQueue:
    """Fair, replayable queue keyed by code and exact market-data route."""

    def __init__(self, session_date: str):
        self.session_date = date.fromisoformat(session_date).isoformat()
        self._candidates: dict[tuple[str, str], Candidate] = {}
        self._claim_sequence = 0
        # First observation of current dispatch eligibility. Never infer this
        # from historical first_seen, and never carry it across process restore.
        self._eligible_since = {}

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
        if not is_canonical_stock_code(code):
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
            source_date = (
                datetime.fromtimestamp(observed_epoch, ZoneInfo("Asia/Seoul"))
                .date()
                .isoformat()
            )
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
            # Refresh an assessed setup, but keep non-assessed retry deadlines.
            if current.last_result in {"queued", "assessed"}:
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
        self,
        *,
        now_epoch: float,
        limit: int,
        min_interval_sec: float = 0,
        max_observation_age_sec: float | None = None,
        eligible_routes: set[str] | None = None,
        activity_claims_per_gainer: int = 3,
        residence_requirements=None,
        deferred_active_codes: set[str] | None = None,
        product_check=None,
        borrow_idle_short_slot: bool = False,
        allocation_policy: str = "current",
    ) -> list[dict]:
        """Return due generations, oldest last claim first, with a bounded budget."""
        from src.utils.kiwoom_utils import is_non_equity_product_name

        if limit < 0 or min_interval_sec < 0:
            raise ValueError("negative queue budget")
        if (
            type(activity_claims_per_gainer) is not int
            or activity_claims_per_gainer < 1
        ):
            raise ValueError("invalid source rotation budget")
        if max_observation_age_sec is not None and max_observation_age_sec <= 0:
            raise ValueError("invalid observation age budget")
        if not isinstance(allocation_policy, str) or allocation_policy not in {
            "current",
            "eligible_wait",
            "service_wait",
        }:
            raise ValueError("invalid allocation policy")
        ready_by_cohort: dict[tuple[str, str, str], list[Candidate]] = {}
        cohort_claims: dict[tuple[str, str, str], int] = {}
        self.claim_eligibility = dict(
            allocation_policy=allocation_policy,
            eligible_due_count=0,
            active_target_deferred_count=0,
            stale_count=0,
            in_flight_count=0,
            retry_not_due_count=0,
            route_ineligible_count=0,
            product_ineligible_count=0,
        )
        eligible_wait = []
        products = {}
        self.admission_state = {}
        for candidate in self._candidates.values():
            # Activity is a discovery hint, not an entry decision. Keep one
            # bounded claim for gainers per source-rotation cycle.
            kind = "activity" if candidate.source_kind == "activity" else "gainers"
            cohort = (candidate.market, candidate.route, kind)
            cohort_claims[cohort] = cohort_claims.get(cohort, 0) + candidate.claim_count
            if product_check is not None and not candidate.in_flight:
                products[(candidate.code, candidate.route)] = product_check(
                    candidate.code, candidate.name, candidate.market
                )
            if candidate.in_flight:
                reason = "in_flight"
                self.claim_eligibility["in_flight_count"] += 1
            elif is_non_equity_product_name(candidate.name):
                reason = "product_ineligible"
                self.claim_eligibility["product_ineligible_count"] += 1
            elif (product_check is None and not candidate.code.isdigit()) or (
                product_check is not None
                and products[(candidate.code, candidate.route)].get("eligible")
                is not True
            ):
                reason = "product_ineligible"
                self.claim_eligibility["product_ineligible_count"] += 1
            elif eligible_routes is not None and candidate.route not in eligible_routes:
                reason = "route_ineligible"
                self.claim_eligibility["route_ineligible_count"] += 1
            elif max_observation_age_sec is not None and not (
                0 <= now_epoch - candidate.observed_epoch <= max_observation_age_sec
            ):
                reason = "stale"
                self.claim_eligibility["stale_count"] += 1
            elif (
                candidate.next_due_epoch > now_epoch
                or candidate.last_claim_epoch + min_interval_sec > now_epoch
            ):
                reason = "retry_not_due"
                self.claim_eligibility["retry_not_due_count"] += 1
            elif candidate.code in (deferred_active_codes or ()):
                reason = "active_target_deferred"
                self.claim_eligibility["active_target_deferred_count"] += 1
            else:
                reason = "eligible_due"
                self.claim_eligibility["eligible_due_count"] += 1
                key = (candidate.code, candidate.route)
                first_eligible = self._eligible_since.setdefault(key, now_epoch)
                eligible_wait.append(max(0.0, now_epoch - first_eligible))
                ready_by_cohort.setdefault(cohort, []).append(candidate)
            key = (candidate.code, candidate.route)
            self.admission_state[key] = (
                reason,
                products.get(key, {}).get("master_sha256"),
            )
            if reason != "eligible_due":
                self._eligible_since.pop(key, None)
        self.claim_eligibility["eligible_due_wait_max_seconds"] = max(
            eligible_wait, default=None
        )
        self.claim_eligibility["wait_basis"] = "observed_fresh_due_at_dispatch"
        self.claim_eligibility["wait_continuity"] = "dispatch_samples_only"
        for cohort_ready in ready_by_cohort.values():
            cohort_ready.sort(
                key=lambda row: (
                    row.last_claim_epoch,
                    row.first_seen_epoch,
                    -row.discovery_volume,
                    row.code,
                )
            )
        ready = []
        requirements = {}
        # Keep the short reservation whenever any currently eligible candidate
        # can use it. Borrow only with explicit runtime admission and no such
        # demand; existing leases are never preempted or given a new deadline.
        long_limit = MAX_LONG_PROBES
        if borrow_idle_short_slot:
            limit = min(limit, max(0, 5 - self.in_flight_count()))
        if borrow_idle_short_slot and limit > 0:
            for rows in ready_by_cohort.values():
                for row in rows:
                    requirements[(row.code, row.route)] = (
                        residence_requirements(row, now_epoch)
                        if residence_requirements
                        else {"minimum_seconds": 0}
                    )
            short_demand = any(
                type(r.get("minimum_seconds")) in (int, float)
                and isfinite(r["minimum_seconds"])
                and 0 <= r["minimum_seconds"] < 60
                for r in requirements.values()
            )
            if not short_demand:
                long_limit += 1
        long_used = sum(
            r.in_flight and r.residence_deadline_epoch - r.last_claim_epoch > 60
            for r in self._candidates.values()
        )
        allocation = {}
        self.residence_deferred = {}

        def age_key(row):
            if allocation_policy == "current":
                return row.last_claim_epoch, row.first_seen_epoch, -row.discovery_volume
            eligible = self._eligible_since[(row.code, row.route)]
            if allocation_policy == "eligible_wait":
                return (
                    bool(row.last_claim_epoch),
                    eligible if not row.last_claim_epoch else row.last_claim_epoch,
                    row.first_seen_epoch,
                    -row.discovery_volume,
                )
            return (
                eligible,
                row.last_claim_epoch,
                row.first_seen_epoch,
                -row.discovery_volume,
            )

        while len(ready) < limit:
            for cohort_key, rows in ready_by_cohort.items():
                # A global fourth turn always coincides with the gainer turn
                # at the 3:1 ratio. Age within each cohort instead.
                age_turn = cohort_claims[cohort_key] % 4 == 3
                # Three activity/liquidity turns and one oldest-service turn.
                # Never-tested rows precede retries; the oldest-service turn
                # prevents an endless stream of active newcomers starving them.
                rows.sort(
                    key=lambda row: (
                        (
                            -row.long_residence_deferred_count
                            if long_used < long_limit
                            else 0
                        ),
                        (
                            age_key(row)
                            if age_turn
                            else (
                                bool(row.last_claim_epoch),
                                -row.discovery_volume,
                                -row.observed_epoch,
                                row.last_claim_epoch,
                                row.first_seen_epoch,
                            )
                        ),
                        row.code,
                    )
                )
                while rows:
                    row = rows[0]
                    key = (row.code, row.route)
                    if key not in requirements:
                        requirements[key] = (
                            residence_requirements(row, now_epoch)
                            if residence_requirements
                            else {"minimum_seconds": 0}
                        )
                    needed = requirements[key].get("minimum_seconds")
                    valid_requirement = (
                        type(needed) in (float, int)
                        and isfinite(needed)
                        and needed >= 0
                    )
                    if (
                        not valid_requirement
                        or needed >= 150
                        or (needed >= 60 and long_used >= long_limit)
                    ):
                        reason = (
                            "requirement_unobservable"
                            if not valid_requirement
                            else (
                                "beyond_residence_limit"
                                if needed >= 150
                                else "long_slot_wait"
                            )
                        )
                        row.residence_wait_since_epoch = (
                            row.residence_wait_since_epoch or now_epoch
                        )
                        self.residence_deferred[reason] = (
                            self.residence_deferred.get(reason, 0) + 1
                        )
                        key = (row.code, row.route)
                        self.admission_state[key] = (
                            reason,
                            self.admission_state[key][1],
                        )
                        rows.pop(0)
                    else:
                        break
            available = [key for key, rows in ready_by_cohort.items() if rows]
            if not available:
                break
            preferred_kind = (
                "gainers"
                if (
                    (self._claim_sequence + len(ready))
                    % (activity_claims_per_gainer + 1)
                    == activity_claims_per_gainer
                )
                else "activity"
            )
            preferred = [key for key in available if key[2] == preferred_kind]
            cohort = min(
                preferred or available, key=lambda key: (cohort_claims[key], key)
            )
            row = ready_by_cohort[cohort].pop(0)
            ready.append(row)
            needed = requirements[(row.code, row.route)]["minimum_seconds"]
            full = requirements[(row.code, row.route)].get(
                "full_input_requirement_seconds", needed
            )
            wants_long = (
                type(full) in (int, float) and isfinite(full) and 60 <= full < 150
            )
            residence = (
                150
                if long_used < long_limit
                and (needed >= 60 or wants_long or residence_requirements is None)
                else 60
            )
            if wants_long:
                row.long_residence_deferred_count = (
                    0 if residence > 60 else row.long_residence_deferred_count + 1
                )
            allocation[(row.code, row.route)] = residence
            long_used += int(residence > 60)
            cohort_claims[cohort] += 1
        for candidate in ready:
            key = (candidate.code, candidate.route)
            self.admission_state[key] = ("claimed", self.admission_state[key][1])
            self._eligible_since.pop((candidate.code, candidate.route), None)
            candidate.last_claim_epoch = now_epoch
            candidate.claim_count += 1
            candidate.in_flight = True
            candidate.claimed_observed_epoch = candidate.observed_epoch
            candidate.claimed_source_sha256 = candidate.source_sha256
            candidate.residence_deadline_epoch = 0.0
            candidate.residence_deadline_epoch = (
                now_epoch + allocation[(candidate.code, candidate.route)]
            )
            candidate.lease_phase = "observing"
            candidate.handoff_id = uuid.uuid4().hex
        self._claim_sequence += len(ready)
        checked = [r.get("minimum_seconds") for r in requirements.values()]
        self.claim_eligibility.update(
            long_slot_limit=long_limit,
            idle_short_slot_borrowed=long_used > MAX_LONG_PROBES,
            residence_requirement_checked_count=len(checked),
            short_capable_checked_count=sum(
                type(v) in (float, int) and isfinite(v) and 0 <= v < 60 for v in checked
            ),
            long_required_checked_count=sum(
                type(v) in (float, int) and isfinite(v) and 60 <= v < 150
                for v in checked
            ),
            requirement_unobservable_checked_count=sum(
                type(v) not in (float, int) or not isfinite(v) or v < 0 for v in checked
            ),
        )
        claims = [
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
                "residence_deadline_epoch": row.residence_deadline_epoch,
                "physical_probe_lease_id": row.handoff_id,
                "observation_requirements": requirements[(row.code, row.route)],
                "product_binding": products.get((row.code, row.route), {}),
                "long_residence_deferred_count": row.long_residence_deferred_count,
                "residence_wait_seconds": (
                    max(0, now_epoch - row.residence_wait_since_epoch)
                    if row.residence_wait_since_epoch
                    else 0
                ),
            }
            for row in ready
        ]
        for row in ready:
            row.residence_wait_since_epoch = 0.0
        return claims

    def abandon_expired_claims(self, *, now_epoch: float, timeout_sec: float) -> int:
        if timeout_sec <= 0:
            raise ValueError("invalid probe timeout")
        abandoned = 0
        for row in self._candidates.values():
            if row.in_flight and now_epoch >= (
                row.residence_deadline_epoch or row.last_claim_epoch + timeout_sec
            ):
                if row.handoff_id:
                    if row.lease_phase != "cleanup_pending":
                        row.lease_phase = "cleanup_pending"
                        abandoned += 1
                    continue  # Physical release acknowledgement owns capacity.
                row.in_flight = False
                row.claim_count += 1  # Invalidate any later result for the old claim.
                row.claimed_observed_epoch = 0.0
                row.claimed_source_sha256 = ""
                row.last_result = "probe_capacity_deferred"
                row.machine_action = ""
                row.next_due_epoch = now_epoch
                row.lease_phase = "cleanup_pending"
                abandoned += 1
        return abandoned

    def stale_candidate_count(
        self, *, now_epoch: float, max_observation_age_sec: float
    ) -> int:
        if max_observation_age_sec <= 0:
            raise ValueError("invalid observation age budget")
        return sum(
            now_epoch - row.observed_epoch > max_observation_age_sec
            for row in self._candidates.values()
        )

    def in_flight_count(self) -> int:
        """Count all claimed probes, including prior-session claims awaiting expiry."""
        return sum(row.in_flight for row in self._candidates.values())

    def matches_claim(self, claim: dict) -> bool:
        """Check the original reservation before an inbox may deduplicate it."""
        if not isinstance(claim, dict) or any(
            not isinstance(claim.get(key), str) for key in ("code", "route")
        ):
            return False
        row = self._candidates.get((claim["code"], claim["route"]))
        return bool(
            row is not None
            and row.in_flight
            and claim.get("observed_epoch") == row.claimed_observed_epoch
            and claim.get("source_sha256") == row.claimed_source_sha256
            and all(
                claim.get(field) == getattr(row, field)
                for field in ("source_scope", "claim_count", "last_claim_epoch")
            )
        )

    def resolve(
        self,
        claim: dict,
        *,
        result: str,
        next_due_epoch: float,
        machine_action: str = "",
        handoff_id: str = "",
    ) -> bool:
        """Bind an assessment to the exact claimed generation."""
        if result not in RESULTS or (result == "assessed") != (
            machine_action in ACTIONS
        ):
            raise ValueError("invalid assessment result")
        if not self.matches_claim(claim):
            return False
        row = self._candidates[(claim["code"], claim["route"])]
        if (
            not row.in_flight
            or row.lease_phase in {"handoff_pending", "cleanup_pending"}
            or (handoff_id and row.handoff_id and handoff_id != row.handoff_id)
            or row.last_claim_epoch <= 0
            or not isfinite(next_due_epoch)
            or next_due_epoch < row.last_claim_epoch
        ):
            return False
        row.last_result = result
        row.lease_phase = "closed"
        row.machine_action = machine_action
        row.next_due_epoch = next_due_epoch
        if row.observed_epoch > row.claimed_observed_epoch and result == "assessed":
            row.next_due_epoch = min(row.next_due_epoch, row.last_seen_epoch)
        row.handoff_id = handoff_id
        if handoff_id:
            row.lease_phase = "handoff_pending"
            return True
        row.in_flight = False
        row.claimed_observed_epoch = 0.0
        row.claimed_source_sha256 = ""
        return True

    def close_handoff(self, claim, handoff_id):
        if not self.matches_claim(claim):
            return False
        row = self._candidates[(claim["code"], claim["route"])]
        if not handoff_id or row.handoff_id != handoff_id:
            return False
        row.in_flight = False
        row.lease_phase = "closed"
        row.handoff_id = ""
        row.claimed_observed_epoch = 0.0
        row.claimed_source_sha256 = ""
        return True

    def snapshot(self) -> dict:
        return {
            "schema": SCHEMA,
            "session_date": self.session_date,
            "claim_sequence": self._claim_sequence,
            "candidates": [
                row._snapshot()
                for row in sorted(
                    self._candidates.values(), key=lambda row: (row.code, row.route)
                )
            ],
        }

    @classmethod
    def restore(cls, snapshot: dict, *, session_date: str) -> "DiscoveryQueue":
        queue = cls(session_date)
        if (
            snapshot.get("schema")
            not in {
                SCHEMA,
                "zero_base_discovery_queue_v1",
                "zero_base_discovery_queue_v2",
            }
            or snapshot.get("session_date") != queue.session_date
        ):
            raise ValueError("queue snapshot date or schema mismatch")
        sequence = snapshot.get("claim_sequence", 0)
        if type(sequence) is not int or sequence < 0:
            raise ValueError("invalid queue claim sequence")
        queue._claim_sequence = sequence
        for raw in snapshot.get("candidates", []):
            row = Candidate(**raw)
            if (
                not is_canonical_stock_code(row.code)
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
                or not isfinite(row.residence_deadline_epoch)
                or row.residence_deadline_epoch < 0
                or row.lease_phase
                not in {"closed", "observing", "handoff_pending", "cleanup_pending"}
                or not isinstance(row.handoff_id, str)
                or (
                    row.claimed_source_sha256
                    and re.fullmatch(
                        r"[0-9a-f]{64}",
                        row.claimed_source_sha256,
                    )
                    is None
                )
                or (
                    not row.in_flight
                    and (row.claimed_observed_epoch or row.claimed_source_sha256)
                )
                or not all(
                    isfinite(value) and value >= 0
                    for value in (
                        row.observed_epoch,
                        row.first_seen_epoch,
                        row.last_seen_epoch,
                        row.next_due_epoch,
                        row.last_claim_epoch,
                        row.residence_wait_since_epoch,
                    )
                )
                or row.claim_count < 0
                or type(row.long_residence_deferred_count) is not int
                or row.long_residence_deferred_count < 0
                or row.last_result not in {"queued", *RESULTS}
                or (row.last_result == "assessed") != (row.machine_action in ACTIONS)
                or row.first_seen_epoch > row.last_seen_epoch
                or row.observed_epoch > row.last_seen_epoch
                or (row.in_flight and row.claim_count == 0)
            ):
                raise ValueError("invalid queue snapshot candidate")
            try:
                source_date = (
                    datetime.fromtimestamp(row.observed_epoch, ZoneInfo("Asia/Seoul"))
                    .date()
                    .isoformat()
                )
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
            row.lease_phase = "closed"
            row.handoff_id = ""
            row.residence_deadline_epoch = 0.0
            queue._candidates[key] = row
        return queue
