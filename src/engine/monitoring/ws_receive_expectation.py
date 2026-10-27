"""Verified market-state receive diagnostics; never an execution-health waiver."""

from datetime import datetime, timedelta, timezone
from math import isfinite
from typing import Any, Mapping
from collections import deque
from hashlib import sha256
from ast import literal_eval
import json

KST = timezone(timedelta(hours=9))
CONTRACT_VERSION = "ws_market_state_receive_expectation_v2"
MARKET_SESSION_STATE_CONTRACT_VERSION = "kiwoom_0s_market_operation_v1"
VERIFIED_0S_QUIET_STATES = {
    ("KRX", "2"): "CALL_AUCTION",
    ("KRX", "c"): "CALL_AUCTION",
    ("NXT", "T"): "CALL_AUCTION",
}
ROUTES = {
    "KRX": "KRX",
    "krx_regular": "KRX",
    "krx_only": "KRX",
    "NXT": "NXT",
    "nxt_only": "NXT",
    "SOR": "SOR",
    "krx_nxt_integrated": "SOR",
}
ABSENCE_REASONS = {
    "",
    "none",
    "subscription_no_tick",
    "subscription_stale",
    "subscription_required_realtime_missing",
    "dashboard_snapshot_subscription_state_unavailable",
}

DELAY_COLLECTION_SCHEMA = "delay_quote_collection_v1"


class DepthReceiveCadence:
    """Bounded local 0D accounting; never a quote or subscription authority.

    The WS owner supplies the lock and resets this object on each native REG,
    transport/session transition or REMOVE. Sequence IDs refer to local wire
    admission, not exchange transmission. Quantiles run only in the sampler.
    """

    def __init__(
        self, *, item, epoch, generation, session, registered_at, route_sequence_base=0,
        market_state=None,
    ):
        self.scope = dict(
            item=item,
            transport_epoch=epoch,
            subscription_generation=generation,
            session=session,
            market_state=market_state,
            registered_at_epoch=registered_at,
            source_day=int((registered_at + 9 * 3600) // 86400),
            route_sequence_base=route_sequence_base,
        )
        self.wire_count = self.normalized_count = self.normalized_wire_id = 0
        self.last_wire = self.last_normalized = None
        self.last_normalized_wire = None
        self.normalized_route_sequence = route_sequence_base
        self.clock_invalid = False
        self.missing_normalizations = 0
        self.last_loss_wire_id = 0
        self.last_loss_epoch = None
        self.gaps = deque(maxlen=512)
        self.delivery = deque(maxlen=512)
        self._stats_cache = {}

    def wire(self, at):
        self.wire_count += 1
        if not isinstance(at, (int, float)) or isinstance(at, bool) or not isfinite(at):
            self.clock_invalid = True
            return self.wire_count
        if self.last_wire is not None:
            gap = at - self.last_wire
            if gap < 0:
                self.clock_invalid = True
        self.last_wire = at
        return self.wire_count

    def normalized(self, at, wire_id, source_sequence=None):
        if type(wire_id) is not int or wire_id != self.wire_count:
            self.clock_invalid = True
            return
        if wire_id <= self.normalized_wire_id:
            self.clock_invalid = True
            return
        missing = wire_id - self.normalized_wire_id - 1
        self.missing_normalizations += missing
        if missing:
            self.last_loss_wire_id = wire_id
            self.last_loss_epoch = at
        self.normalized_wire_id = wire_id
        self.normalized_count += 1
        self.normalized_route_sequence = (
            self.scope["route_sequence_base"] + self.normalized_count
            if source_sequence is None
            else source_sequence
        )
        if (
            not isinstance(at, (int, float))
            or isinstance(at, bool)
            or not isfinite(at)
            or self.last_wire is None
            or at + 0.001 < self.last_wire
        ):
            self.clock_invalid = True
            return
        if self.last_normalized_wire is not None and not missing:
            gap = self.last_wire - self.last_normalized_wire
            if gap > 0:
                self.gaps.append((at, gap))
        self.last_normalized_wire = self.last_wire
        self.last_normalized = at
        # Native depth normalization floors local time to milliseconds.
        self.delivery.append((at, at - self.last_wire + 0.001))

    def freeze(self, *, active, required_types, receiver_ready):
        return dict(
            self.scope,
            wire_count=self.wire_count,
            normalized_count=self.normalized_count,
            normalized_wire_id=self.normalized_wire_id,
            normalized_route_sequence=self.normalized_route_sequence,
            last_wire_epoch=self.last_wire,
            last_normalized_epoch=self.last_normalized,
            clock_invalid=self.clock_invalid,
            missing_normalizations=self.missing_normalizations,
            last_loss_wire_id=self.last_loss_wire_id,
            last_loss_epoch=self.last_loss_epoch,
            subscription_active=active,
            required_types=sorted(required_types),
            receiver_ready=receiver_ready,
            gaps=tuple(self.gaps),
            delivery=tuple(self.delivery),
            _cadence_cache=self._stats_cache,
        )


def project_depth_cadence(frozen, now):
    """Past-only scalar projection outside the WS lock; no book/stream scan."""
    result = {
        k: v
        for k, v in frozen.items()
        if k not in {"gaps", "delivery", "_cadence_cache"}
    }
    key = (
        frozen["wire_count"],
        frozen["normalized_count"],
        frozen["normalized_wire_id"],
    )
    cache = frozen["_cadence_cache"]
    saved = cache.get("value")
    if saved is not None and saved[0] == key and saved[1] <= now < saved[2]:
        result.update(saved[3], as_of_epoch=now)
        return result
    gaps = sorted(v for at, v in frozen["gaps"] if now - 600 <= at <= now)
    delivery = sorted(v for at, v in frozen["delivery"] if now - 600 <= at <= now)

    def quantile(values, probability):
        if not values:
            return None
        rank = (len(values) - 1) * probability
        lo = int(rank)
        hi = min(lo + 1, len(values) - 1)
        return values[lo] + (values[hi] - values[lo]) * (rank - lo)

    basis = (
        "p99"
        if len(gaps) >= 500
        else "provisional_p95" if len(gaps) >= 100 else "insufficient"
    )
    cadence = (
        quantile(gaps, 0.99 if basis == "p99" else 0.95)
        if basis != "insufficient"
        else None
    )
    lag = quantile(delivery, 0.99) if len(delivery) >= 100 else None
    result.update(
        schema=DELAY_COLLECTION_SCHEMA,
        as_of_epoch=now,
        cadence_sample_count=len(gaps),
        cadence_basis=basis,
        cadence_upper_sec=cadence,
        delivery_p99_sec=lag,
        expected_wait_upper_sec=(
            cadence + lag if cadence is not None and lag is not None else None
        ),
        decision_authority="report_only",
        runtime_effect=False,
    )
    names = (
        "schema",
        "cadence_sample_count",
        "cadence_basis",
        "cadence_upper_sec",
        "delivery_p99_sec",
        "expected_wait_upper_sec",
        "decision_authority",
        "runtime_effect",
    )
    expiries = [
        at + 600
        for at, _ in (*frozen["gaps"], *frozen["delivery"])
        if now - 600 <= at <= now
    ]
    # One atomic immutable entry. A concurrent older view may evict this
    # cache, but cannot reuse a different source generation or a future window.
    cache["value"] = (
        key,
        now,
        min(expiries, default=float("inf")),
        {name: result[name] for name in names},
    )
    return result


def classify_delay_quote_collection(row, *, ledger_complete):
    """Separate quote eligibility from proven local loss and unproven silence."""

    def number(value):
        try:
            n = float(value)
            return n if not isinstance(value, bool) and isfinite(n) else None
        except (TypeError, ValueError, OverflowError):
            return None

    loss_details = {}

    def verdict(state, reason):
        return dict(state=state, reason=reason, **loss_details)

    reason = str(row.get("quote_source_reason") or "")
    at, depth = number(row.get("quote_observed_at_epoch")), number(
        row.get("ws_last_0d_epoch")
    )
    if at is not None and depth is not None and depth > at:
        return verdict("contract_invalid", "depth_clock_future")
    evidence = row.get("quote_collection_evidence")
    if isinstance(evidence, str):
        try:
            if len(evidence) > 4096:
                return verdict("contract_invalid", "collection_evidence_budget_invalid")
            evidence = json.loads(evidence)
        except (ValueError, RecursionError):
            # Original pipeline rows used str(dict). Read that bounded literal
            # without changing original bytes or weakening the binding checks.
            try:
                evidence = literal_eval(evidence)
            except (ValueError, SyntaxError, TypeError, RecursionError):
                return verdict("contract_invalid", "collection_evidence_json_invalid")
    if not isinstance(evidence, Mapping):
        return verdict("unobservable", "legacy_collection_evidence_missing")
    if (
        evidence.get("schema") != DELAY_COLLECTION_SCHEMA
        or evidence.get("decision_authority") != "report_only"
        or evidence.get("runtime_effect") is not False
    ):
        return verdict("contract_invalid", "collection_contract_invalid")
    if evidence.get("unobservable_reason") == "cadence_capacity_or_uninitialized":
        return verdict("unobservable", "cadence_capacity_or_uninitialized")
    item = str(evidence.get("item") or "")
    suffix = {"NXT_ONLY": "_NX", "KRX_NXT_INTEGRATED": "_AL", "KRX_ONLY": ""}.get(
        str(row.get("quote_route") or "").upper()
    )
    if (
        suffix is None
        or item != str(row.get("stock_code") or "") + suffix
        or str(evidence.get("transport_epoch")) != str(row.get("quote_transport_epoch"))
        or not isinstance(evidence.get("subscription_generation"), str)
        or not evidence.get("subscription_generation")
        or not isinstance(evidence.get("session"), str)
        or not evidence.get("session")
    ):
        return verdict("contract_invalid", "collection_scope_mismatch")
    sampled = number(evidence.get("as_of_epoch"))
    registered = number(evidence.get("registered_at_epoch"))
    required = evidence.get("required_types")
    depth_sha = row.get("route_depth_source_sha256")
    if (
        at is None
        or sampled is None
        or registered is None
        or not 0 < registered <= sampled <= at
        or type(evidence.get("source_day")) is not int
        or evidence["source_day"] != int((at + 9 * 3600) // 86400)
        or not isinstance(required, list)
        or any(not isinstance(kind, str) for kind in required)
        or not isinstance(depth_sha, str)
        or len(depth_sha) != 64
        or any(c not in "0123456789abcdef" for c in depth_sha)
        or evidence.get("depth_source_sha256") != depth_sha
    ):
        return verdict("contract_invalid", "collection_generation_binding_invalid")
    if evidence.get("clock_invalid") is not False:
        return verdict("contract_invalid", "collection_clock_invalid")
    if evidence.get("session") in {"UNKNOWN", "unknown", "-"}:
        return verdict("unobservable", "subscription_session_unproven")
    if evidence.get("subscription_active") is False or "0D" not in (
        evidence.get("required_types") or []
    ):
        return verdict(
            "collection_fault_confirmed", "required_depth_subscription_missing"
        )
    lost = evidence.get("missing_normalizations")
    if type(lost) is not int or lost < 0:
        return verdict("contract_invalid", "normalization_counter_invalid")
    last_loss = evidence.get("last_loss_wire_id")
    if type(last_loss) is not int or last_loss < 0:
        return verdict("contract_invalid", "normalization_loss_marker_invalid")
    wire, normalized, normalized_id = (
        evidence.get(k)
        for k in ("wire_count", "normalized_count", "normalized_wire_id")
    )
    if any(type(n) is not int or n < 0 for n in (wire, normalized, normalized_id)):
        return verdict("contract_invalid", "collection_counter_invalid")
    if (
        normalized > wire
        or normalized_id > wire
        or normalized_id != normalized + lost
        or last_loss > normalized_id
        or bool(lost) != bool(last_loss)
    ):
        return verdict("contract_invalid", "collection_counter_conflict")
    last_wire = number(evidence.get("last_wire_epoch"))
    last_normal = number(evidence.get("last_normalized_epoch"))
    if at is None or depth is None:
        return verdict("contract_invalid", "collection_clock_binding_invalid")
    if not wire or not normalized or last_wire is None or last_normal is None:
        return verdict("unobservable", "first_depth_pending")
    if last_wire > at or last_normal > at:
        return verdict("contract_invalid", "collection_clock_binding_invalid")
    sequence = number(row.get("quote_route_sequence"))
    normalized_sequence = evidence.get("normalized_route_sequence")
    if normalized_sequence is not None and (
        type(normalized_sequence) is not int or normalized_sequence <= 0
    ):
        return verdict("contract_invalid", "collection_sequence_invalid")
    if sequence is None or sequence != normalized_sequence:
        return verdict("unobservable", "snapshot_generation_unproven")
    if (
        not ledger_complete
        or evidence.get("receiver_ready") is not True
        or evidence.get("subscription_active") is not True
        or not wire
        or normalized_id != wire
        or last_normal != depth
    ):
        return verdict("unobservable", "collection_boundary_unproven")
    from src.engine.scalping.pre_submit_delay_observation import SAMPLE_INTERVAL_SEC
    from src.engine.scalping.pre_submit_delay_tuning import MAX_RESEARCH_DEPTH_AGE_SEC

    if at - sampled > SAMPLE_INTERVAL_SEC:
        return verdict("unobservable", "collection_evidence_stale")
    if lost:
        loss_at = number(evidence.get("last_loss_epoch"))
        if loss_at is None or not registered <= loss_at <= last_normal:
            return verdict("contract_invalid", "normalization_loss_clock_invalid")
        identity = [
            item,
            evidence["transport_epoch"],
            evidence["subscription_generation"],
            evidence["session"],
            evidence["source_day"],
            last_loss,
        ]
        loss_details = dict(
            loss_event_id=sha256(
                json.dumps(identity, separators=(",", ":")).encode()
            ).hexdigest(),
            loss_observed_at_epoch=loss_at,
            historical_missing_normalizations=lost,
        )
    if lost and last_loss == normalized_id:
        # Current health and the time-bounded loss event are separate facts.
        return verdict(
            "collection_fault_confirmed",
            "wire_to_normalized_loss",
        )
    if (
        str(row.get("quote_valid")).lower() == "true"
        and at - depth > MAX_RESEARCH_DEPTH_AGE_SEC
        or reason == "depth_stale_or_clock_invalid"
        and at - depth <= MAX_RESEARCH_DEPTH_AGE_SEC
    ):
        return verdict("contract_invalid", "quote_eligibility_clock_conflict")
    if str(row.get("quote_valid")).lower() == "true":
        return verdict("locally_healthy", "exact_local_chain_observed")
    if reason != "depth_stale_or_clock_invalid":
        return verdict("contract_invalid", reason or "quote_invalid")
    upper = number(evidence.get("expected_wait_upper_sec"))
    count = evidence.get("cadence_sample_count")
    cadence, lag = number(evidence.get("cadence_upper_sec")), number(
        evidence.get("delivery_p99_sec")
    )
    basis = evidence.get("cadence_basis")
    if (
        type(count) is not int
        or not 100 <= count <= 512
        or upper is None
        or upper <= 0
        or cadence is None
        or cadence <= 0
        or lag is None
        or lag < 0
        or abs(upper - cadence - lag) > 1e-6
        or not isinstance(basis, str)
        or basis not in {"p99", "provisional_p95"}
        or basis == "p99"
        and count < 500
    ):
        return verdict("unobservable", "cadence_baseline_insufficient")
    return verdict(
        "expected_wait" if at - depth <= upper else "cadence_exceeded_unproven",
        (
            "past_only_cadence_band"
            if at - depth <= upper
            else "cadence_exceeded_not_fault_proof"
        ),
    )


def _aware_kst(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(KST)


def _remaining_seconds(value: Any) -> int | None:
    token = str(value or "").strip()
    if len(token) != 6 or not token.isdigit():
        return None
    hours, minutes, seconds = int(token[:2]), int(token[2:4]), int(token[4:])
    if minutes >= 60 or seconds >= 60:
        return None
    total = hours * 3600 + minutes * 60 + seconds
    return total if total > 0 else None


def _exchange_time(
    receipt: Mapping[str, Any], received_at: datetime
) -> datetime | None:
    token = str(receipt.get("exchange_time_raw") or "").strip()
    if len(token) != 6 or not token.isdigit():
        return None
    hours, minutes, seconds = int(token[:2]), int(token[2:4]), int(token[4:])
    if hours >= 24 or minutes >= 60 or seconds >= 60:
        return None
    exchange_at = received_at.replace(
        hour=hours, minute=minutes, second=seconds, microsecond=0
    )
    return exchange_at if exchange_at <= received_at else None


def _verified_quiet_receipt(
    receipt: Any, *, scope: str, at: datetime
) -> tuple[bool, datetime | None, datetime | None]:
    if not isinstance(receipt, Mapping):
        return False, None, None
    received_at = _aware_kst(receipt.get("receive_timestamp"))
    raw_state = str(receipt.get("market_session_state_raw") or "")
    normalized_state = str(receipt.get("market_session_state_normalized") or "")
    if (
        receipt.get("market_session_state_contract_version")
        != MARKET_SESSION_STATE_CONTRACT_VERSION
        or receipt.get("runtime_effect") is not False
        or receipt.get("allowed_runtime_apply") is not False
        or receipt.get("market_session_state_known") is not True
        or str(receipt.get("market_session_state_market_scope") or "") != scope
        or VERIFIED_0S_QUIET_STATES.get((scope, raw_state)) != normalized_state
        or received_at is None
        or received_at > at
    ):
        return False, received_at, None
    remaining = _remaining_seconds(receipt.get("market_session_remaining_raw"))
    exchange_at = _exchange_time(receipt, received_at)
    if remaining is None or exchange_at is None:
        return False, received_at, None
    valid_until = exchange_at + timedelta(seconds=remaining)
    return at < valid_until, exchange_at, valid_until


def receive_expectation(row: Mapping[str, Any], at: datetime | None) -> dict[str, Any]:
    """Use exact event/as-of time, route, and bounded verified state receipts."""
    result = {
        "contract_version": CONTRACT_VERSION,
        "scheduled_quiet": False,
        "reason": "missing_or_unverified_market_state_quiet_receipt",
        "resume_at": None,
        "required_market_scopes": [],
        "verified_quiet_scopes": [],
        "quiet_started_at": None,
    }
    if at is None or at.tzinfo is None:
        return result
    at = at.astimezone(KST)
    routes = row.get("registered_market_routes")
    if routes is None:
        routes = [
            row[key]
            for key in (
                "observed_market_route",
                "market_data_market_route",
                "market_route",
                "venue",
            )
            if row.get(key)
        ]
    if not isinstance(routes, (list, tuple)) or not routes:
        return result
    normalized = {ROUTES.get(str(route)) for route in routes}
    if None in normalized:
        return result
    required_scopes = set()
    for route in normalized:
        required_scopes.update({"KRX", "NXT"} if route == "SOR" else {route})
    result["required_market_scopes"] = sorted(required_scopes)
    states = row.get("market_session_states_by_scope")
    if not isinstance(states, Mapping):
        return result
    quiet_starts = []
    quiet_ends = []
    verified_scopes = []
    for scope in sorted(required_scopes):
        verified, started_at, valid_until = _verified_quiet_receipt(
            states.get(scope), scope=scope, at=at
        )
        if not verified:
            return result
        verified_scopes.append(scope)
        quiet_starts.append(started_at)
        quiet_ends.append(valid_until)
    quiet_started_at = max(quiet_starts)
    resume_at = min(quiet_ends)
    result.update(
        scheduled_quiet=True,
        reason="verified_market_session_call_auction_or_vi",
        resume_at=resume_at.isoformat(),
        verified_quiet_scopes=verified_scopes,
        quiet_started_at=quiet_started_at.isoformat(),
    )
    return result


def classify_receive_gap(row: Mapping[str, Any], at: datetime | None) -> dict[str, Any]:
    """Preserve raw ages/observations while removing absence-only repair advice."""
    result = dict(row)
    # A persisted diagnostic is not a waiver after the opening boundary.
    prior_expectation = row.get("receive_expectation")
    if isinstance(prior_expectation, dict) and prior_expectation.get(
        "contract_version"
    ) in {CONTRACT_VERSION, "ws_opening_receive_expectation_v1"}:
        prior_reason = str(row.get("repair_reason") or "")
        if (
            "observed_repair_reason" in row
            and prior_reason
            in {
                "verified_market_session_call_auction_or_vi",
                "scheduled_opening_auction_or_nxt_pause",
            }
            and row.get("repair_recommended") is False
            and row.get("recommended_repair") == "none"
        ):
            result["repair_reason"] = row["observed_repair_reason"]
            result["repair_recommended"] = row.get("observed_repair_recommended", False)
            result["recommended_repair"] = row.get(
                "observed_recommended_repair", "none"
            )
        if row.get("freshness_state") == "expected_market_quiet":
            result["freshness_state"] = row.get("observed_freshness_state", "unknown")
            result["trade_tick_quiet"] = row.get("observed_trade_tick_quiet", False)
    row = result
    expectation = receive_expectation(row, at)
    result["receive_expectation"] = expectation
    result["expected_market_quiet"] = False
    age = row.get("last_receive_age_sec")
    if age is not None:
        if (
            isinstance(age, bool)
            or not isinstance(age, (int, float))
            or not isfinite(age)
            or age < 0
        ):
            return result
        # A receive gap already stale before the pause is not explained by it.
        stale_after = row.get("stale_after_sec", 30.0)
        if (
            isinstance(stale_after, bool)
            or not isinstance(stale_after, (int, float))
            or not isfinite(stale_after)
            or stale_after <= 0
        ):
            return result
        if expectation["scheduled_quiet"]:
            quiet_started_at = _aware_kst(expectation.get("quiet_started_at"))
            if quiet_started_at is None:
                return result
            if at.astimezone(KST).timestamp() - age < (
                quiet_started_at.timestamp() - stale_after
            ):
                return result
    missing = row.get("required_realtime_missing_types", [])
    if (
        not expectation["scheduled_quiet"]
        or row.get("subscribed") is False
        or str(row.get("repair_reason") or "") not in ABSENCE_REASONS
        or not isinstance(missing, (list, tuple))
        or not all(isinstance(item, str) for item in missing)
        or set(missing) - {"0B", "0D"}
        or any(
            row.get(key)
            for key in (
                "connection_error",
                "subscription_error",
                "storage_error",
                "parse_error",
                "receive_age_contract_invalid",
            )
        )
        or any(
            row.get(key) is False
            for key in (
                "connected",
                "login_ok",
                "subscription_ack_ok",
                "storage_healthy",
            )
        )
    ):
        return result
    raw_state = str(row.get("freshness_state") or "")
    if raw_state not in {"no_tick", "stale", "fresh"}:
        return result
    if raw_state == "fresh" and not row.get("trade_tick_quiet") and not missing:
        return result
    result.update(
        observed_freshness_state=raw_state,
        observed_trade_tick_quiet=bool(row.get("trade_tick_quiet")),
        observed_repair_reason=row.get("repair_reason"),
        observed_repair_recommended=row.get("repair_recommended", False),
        observed_recommended_repair=row.get("recommended_repair", "none"),
        freshness_state="expected_market_quiet",
        expected_market_quiet=True,
        trade_tick_quiet=False,
        repair_recommended=False,
        repair_reason=expectation["reason"],
        recommended_repair="none",
    )
    return result
