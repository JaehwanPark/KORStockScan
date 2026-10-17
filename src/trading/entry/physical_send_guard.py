"""Call-local Main initial-entry checks at the physical BUY transport boundary.

This is not order authority. Only the Main entry producer creates this context;
subsequent bundle legs and other operations keep their existing lifetimes.
"""

from __future__ import annotations

import hashlib
import json
import math
import time
import threading
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Callable, Mapping, Any

from src.trading.market.quote_consistency import ws_quote_source_receipt
from src.trading.entry.quote_time_policy import active_contract_receipt

_INITIAL_RESULTS = OrderedDict()
_INITIAL_RESULTS_LOCK = threading.Lock()


def retain_initial_native_result(result) -> None:
    """Retain an admitted immutable result for its existing deferred arm only."""
    if not result.native_claim:
        return
    with _INITIAL_RESULTS_LOCK:
        now, perf = time.time(), time.perf_counter()
        for key, value in list(_INITIAL_RESULTS.items()):
            if now >= value.deadline_epoch or perf >= value.deadline_perf:
                _INITIAL_RESULTS.pop(key, None)
        if now >= result.deadline_epoch or perf >= result.deadline_perf:
            return
        _INITIAL_RESULTS[result.request_id] = result
        _INITIAL_RESULTS.move_to_end(result.request_id)
        while len(_INITIAL_RESULTS) > 128:
            _INITIAL_RESULTS.popitem(last=False)


def retained_initial_native_result(request_id):
    with _INITIAL_RESULTS_LOCK:
        result = _INITIAL_RESULTS.get(request_id)
        if result is not None and (time.time() >= result.deadline_epoch
                                  or time.perf_counter() >= result.deadline_perf):
            _INITIAL_RESULTS.pop(request_id, None)
            return None
        return result


def canonical_binding(value: Mapping[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False)


class EntrySendGuardBlocked(ValueError):
    def __init__(self, receipt: dict, *, attempts: int = 0, auth_response=None):
        super().__init__(receipt.get("reason", "entry_send_guard_blocked"))
        self.receipt = receipt
        self.attempts = attempts
        self.auth_response = auth_response

    def response(self) -> dict:
        return {"return_code": "ENTRY_SEND_GUARD_BLOCKED",
                "rt_cd": "ENTRY_SEND_GUARD_BLOCKED", "return_msg": str(self),
                "ord_no": "", "broker_order_attempted": self.attempts > 0,
                "physical_send_attempt_count": self.attempts,
                "entry_send_guard_blocked": True,
                "entry_send_guard_receipt": self.receipt,
                "rejected_auth_response": self.auth_response}


@dataclass(frozen=True, slots=True)
class PhysicalEntrySendContext:
    operation: str
    owner_identity: tuple[str, str, str, str]
    code: str
    quantity: int
    broker_route: str
    order_type: str
    broker_price: str
    evaluation_attempt_id: str
    ai_decision_trace_id: str
    decision_binding: str
    source_policy_binding: str
    source_policy_receipt: str
    source_policy_version: str
    max_quote_age_ms: float
    original_deadline_epoch: float
    original_deadline_perf: float
    source_item: str
    source_market_route: str
    source_transport_epoch: int
    source_type: str
    source_route_sequence: int
    quote_observed_epoch: float
    best_bid: int
    best_ask: int
    current_price: int
    snapshot_reader: Callable[[], Mapping[str, Any]] = field(repr=False, compare=False)
    binding_reader: Callable[[], tuple[str, str]] = field(repr=False, compare=False)

    ai_authority_expires_epoch: float | None = None
    ai_authority_expires_perf: float | None = None

    def check(self, *, api_id, owner_context, payload) -> dict:
        receipt = {"schema": "main_initial_physical_send_guard_v1",
                   "operation": self.operation,
                   "evaluation_attempt_id": self.evaluation_attempt_id,
                   "ai_decision_trace_id": self.ai_decision_trace_id,
                   "client_intent_id": self.owner_identity[3],
                   "source_policy_version": self.source_policy_version,
                   "source_policy_receipt": json.loads(self.source_policy_receipt),
                   "original_deadline_epoch": self.original_deadline_epoch,
                   "original_deadline_perf": self.original_deadline_perf,
                   "max_quote_age_ms": self.max_quote_age_ms,
                   "allowed": False}

        def reject(reason):
            receipt["reason"] = reason
            raise EntrySendGuardBlocked(receipt)

        owner = tuple(getattr(owner_context, key, None) for key in (
            "owner_type", "owner_id", "position_id", "client_intent_id"))
        if (api_id != "kt10000" or self.operation not in {"ENTRY_BUY", "INITIAL_QUANTITY_LEG0"}
                or self.owner_identity[0] != "main_scalping"
                or not all(isinstance(v, str) and v for v in self.owner_identity)
                or owner != self.owner_identity):
            reject("operation_owner_api_binding_invalid")
        try:
            policy_receipt = receipt["source_policy_receipt"]
            allowed_age = policy_receipt["latency_caution_ms"]
            if policy_receipt["consistency_enabled"]:
                allowed_age = min(allowed_age, policy_receipt["consistency_ws_max_age_ms"])
            if (policy_receipt.get("version") != self.source_policy_version
                    or self.max_quote_age_ms != allowed_age
                    or canonical_binding(active_contract_receipt(policy_receipt))
                    != self.source_policy_binding):
                reject("source_time_policy_receipt_binding_invalid")
        except EntrySendGuardBlocked:
            raise
        except (KeyError, TypeError, ValueError, AttributeError):
            reject("source_time_policy_receipt_binding_invalid")
        expected = {"stk_cd": self.code, "ord_qty": str(self.quantity),
                    "dmst_stex_tp": self.broker_route, "trde_tp": self.order_type,
                    "ord_uv": self.broker_price}
        if (type(self.quantity) is not int or self.quantity <= 0
                or any(payload.get(k) != v for k, v in expected.items())):
            reject("order_payload_binding_changed")
        numbers = (self.original_deadline_epoch, self.original_deadline_perf,
                   self.quote_observed_epoch, self.max_quote_age_ms)
        if (any(type(v) not in (int, float) or not math.isfinite(v) or v <= 0
                for v in numbers) or type(self.source_transport_epoch) is not int
                or self.source_transport_epoch <= 0 or not self.source_item
                or not self.source_market_route or not self.source_policy_version
                or self.source_type not in {"0B", "0D"}
                or type(self.source_route_sequence) is not int or self.source_route_sequence <= 0
                or not self.evaluation_attempt_id or not self.ai_decision_trace_id
                or not self.decision_binding or not self.source_policy_binding
                or self.best_bid <= 0 or self.best_ask < self.best_bid
                or self.current_price <= 0):
            reject("entry_context_invalid")
        try:
            decision, policy = self.binding_reader()
            if decision != self.decision_binding or policy != self.source_policy_binding:
                reject("decision_or_time_policy_binding_changed")
            snapshot = self.snapshot_reader()
            now = time.time()
            perf = time.perf_counter()
            receipt.update(checked_epoch=now, checked_perf=perf)
            if now >= self.original_deadline_epoch or perf >= self.original_deadline_perf:
                reject("original_entry_deadline_expired")
            expiry = (self.ai_authority_expires_epoch, self.ai_authority_expires_perf)
            if expiry != (None, None):
                if any(type(v) not in (int, float) or not math.isfinite(v) or v <= 0
                       for v in expiry):
                    reject("ai_authority_expiry_invalid")
                receipt.update(ai_authority_expires_epoch=expiry[0],
                               ai_authority_expires_perf=expiry[1])
                if now > expiry[0] or perf > expiry[1]:
                    reject("ai_authority_expired_before_physical_send")
            quote = ws_quote_source_receipt(snapshot, now_ts=now)
            receipt["quote_source_receipt"] = quote
            if any(snapshot.get(key) for key in (
                    "quote_stale", "context_stale", "price_conflict", "source_conflict")):
                reject("current_quote_explicitly_invalid")
            if (quote.get("source_type") not in {"0B", "0D"}
                    or quote.get("item") != self.source_item
                    or quote.get("market_route") != self.source_market_route
                    or type(quote.get("transport_epoch")) is not int
                    or quote.get("transport_epoch") != self.source_transport_epoch
                    or type(quote.get("route_sequence")) is not int
                    or quote.get("route_sequence") <= 0
                    or (quote.get("source_type") == self.source_type
                        and quote.get("route_sequence") < self.source_route_sequence)
                    or quote.get("observed_epoch", 0) < self.quote_observed_epoch):
                reject("canonical_quote_source_binding_invalid")
            age = (now - quote["observed_epoch"]) * 1000.0
            receipt["canonical_quote_age_ms"] = age
            if not math.isfinite(age) or not 0 <= age <= self.max_quote_age_ms:
                reject("canonical_quote_expired_or_future")
            if (quote.get("best_bid") != self.best_bid
                    or quote.get("best_ask") != self.best_ask
                    or snapshot.get("curr") != self.current_price):
                reject("execution_price_changed_reprice_required")
        except EntrySendGuardBlocked:
            raise
        except Exception as exc:
            receipt["revalidation_error"] = str(exc)[:240]
            native_receipt = getattr(exc, "reversal_source_receipt", None)
            if isinstance(native_receipt, dict):
                receipt["native_source_receipt"] = native_receipt
            reject("entry_context_revalidation_failed:" + type(exc).__name__)
        receipt.update(allowed=True, reason="same_initial_intent_current_quote",
                       decision_binding_sha256=hashlib.sha256(self.decision_binding.encode()).hexdigest(),
                       source_policy_sha256=hashlib.sha256(self.source_policy_binding.encode()).hexdigest())
        return receipt


def check_entry_send_context(context, *, api_id, owner_context, payload):
    if not isinstance(context, PhysicalEntrySendContext):
        raise EntrySendGuardBlocked({"schema": "main_initial_physical_send_guard_v1",
                                     "allowed": False, "reason": "entry_send_context_type_invalid"})
    try:
        return context.check(api_id=api_id, owner_context=owner_context, payload=payload)
    except EntrySendGuardBlocked:
        raise
    except Exception as exc:
        raise EntrySendGuardBlocked({"schema": "main_initial_physical_send_guard_v1",
                                     "allowed": False, "reason":
                                     "entry_send_context_invalid:" + type(exc).__name__}) from exc
