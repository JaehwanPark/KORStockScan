"""Crash-durable shared order-owner journal for same-symbol coexistence.

The broker account exposes holdings by symbol, while order and execution
receipts expose exact order numbers.  This append-only journal bridges those
two views without letting a process infer ownership from aggregate holdings.
Every append is serialized with ``flock`` and chained by SHA-256.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import uuid
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from src.trading.config.symbol_owner_policy import ACTIVATION_SCHEMA, normalize_symbol
from src.utils.constants import DATA_DIR

KST = ZoneInfo("Asia/Seoul")
REGISTRY_SCHEMA = "order_owner_registry_event_v1"
REGISTRY_PATH_ENV = "KORSTOCKSCAN_ORDER_OWNER_REGISTRY_PATH"
ACCOUNT_KEY_ENV = "KORSTOCKSCAN_BROKER_ACCOUNT_KEY"
DEFAULT_REGISTRY_PATH = DATA_DIR / "runtime" / "order_owner_registry.jsonl"
_ACTIVE_UNBOUND_STATES = frozenset({"INTENT_RESERVED", "INTENT_AMBIGUOUS"})
_TERMINAL_PROOF_FIELDS = (
    "account_key",
    "intent_id",
    "order_date",
    "broker_order_no",
    "owner_type",
    "owner_id",
    "position_id",
    "client_intent_id",
    "symbol",
    "side",
    "action",
    "route",
    "quantity",
    "filled_qty",
)


def _terminal_proof(row, receipt_sha256):
    return {
        "schema": "order_owner_terminal_reconciliation_v1",
        "source_contract": (
            "machine_adaptive_exit_buy_dated_current_v1"
            if row.get("side") == "BUY"
            else "machine_adaptive_exit_dated_current_v1"
        ),
        **{key: row[key] for key in _TERMINAL_PROOF_FIELDS},
        "receipt_sha256": receipt_sha256,
    }


KIWOOM_OWNER_REGISTRY_OFFICIAL_REFERENCE = {
    "repository": "Kiwoom-Securities/Kiwoom-REST-API",
    "commit_sha": "234560d213acd8871ae344b5481aecd2f30287fa",
    "retrieved_at_kst": "2026-09-03T18:41:14+09:00",
    "inspected_paths": [
        "kiwoom/_data/kiwoom_api_spec.json",
        "kiwoom/specs.py",
        "postman/kiwoom-openapi.postman_collection.json",
    ],
    "request_scope": [
        "kt00018",
        "kt00007",
        "ka10075",
        "kt10000",
        "kt10001",
        "kt10002",
        "kt10003",
    ],
    "verified_contract": (
        "all_venue_inventory_and_unfilled_order_snapshot,seven_digit_order_number,"
        "share_quantity,completed_buy_execution_price_and_remainder,"
        "original_order_number_cancel_binding"
    ),
}


class OwnerRegistryError(RuntimeError):
    """Base fail-closed registry error."""


class OwnerRegistryBusy(OwnerRegistryError):
    """A prior submit for the same symbol/side is unresolved."""


class OwnerRegistryConflict(OwnerRegistryError):
    """An order number or execution conflicts with existing ownership."""


@dataclass(frozen=True)
class OwnerOrderContext:
    owner_type: str
    owner_id: str
    position_id: str
    client_intent_id: str

    def validate(self) -> None:
        allowed = {"main_scalping", "widget_auto_trade", "episode", "manual_operator"}
        if self.owner_type not in allowed:
            raise OwnerRegistryError("owner_type_invalid")
        for name, value in (
            ("owner_id", self.owner_id),
            ("position_id", self.position_id),
            ("client_intent_id", self.client_intent_id),
        ):
            normalized = str(value or "").strip()
            if (
                not normalized
                or len(normalized) > 240
                or any(ch in normalized for ch in "\r\n\t")
            ):
                raise OwnerRegistryError(f"{name}_invalid")
        if self.owner_type == "main_scalping" and (
            not self.owner_id.startswith("main_scalping:")
            or self.position_id != self.owner_id
        ):
            raise OwnerRegistryError("main_owner_position_identity_invalid")


def broker_account_key(*, require_explicit: bool = False) -> str:
    configured = os.getenv(ACCOUNT_KEY_ENV)
    value = str(configured or "default").strip()
    if not value or len(value) > 80 or any(ch in value for ch in "\r\n\t"):
        raise OwnerRegistryError("broker_account_key_invalid")
    if require_explicit and (configured is None or value.lower() == "default"):
        raise OwnerRegistryError("owner_registry_explicit_broker_account_key_required")
    return value


def _registry_symbol(value: object) -> str:
    clean = normalize_symbol(value)
    if not (clean.isdigit() and len(clean) == 6):
        raise OwnerRegistryError("owner_registry_symbol_invalid")
    return clean


def _registry_order_date(value: date | str) -> str:
    clean = value.isoformat() if isinstance(value, date) else str(value or "").strip()
    try:
        parsed = date.fromisoformat(clean)
    except ValueError as exc:
        raise OwnerRegistryError("owner_registry_order_date_invalid") from exc
    if parsed.isoformat() != clean:
        raise OwnerRegistryError("owner_registry_order_date_invalid")
    return clean


def registry_path() -> Path:
    configured = str(os.getenv(REGISTRY_PATH_ENV, "") or "").strip()
    return Path(configured).expanduser() if configured else DEFAULT_REGISTRY_PATH


def main_owner_context(
    stock: dict[str, Any], *, action: str, ordinal: object = "0"
) -> OwnerOrderContext | None:
    target_id = str(stock.get("id") or stock.get("target_id") or "").strip()
    cycle_id = str(stock.get("position_cycle_id") or target_id).strip()
    if not target_id:
        # Legacy/non-coexistence paths do not require an owner context. The
        # central order surface still rejects this ``None`` before transport
        # whenever an exact-date coexistence policy governs the symbol.
        return None
    position_id = f"main_scalping:{target_id}"
    action_token = str(action or "").strip().upper()
    return OwnerOrderContext(
        owner_type="main_scalping",
        owner_id=f"main_scalping:{target_id}",
        position_id=position_id,
        client_intent_id=(
            f"{position_id}:{cycle_id}:{action_token}:{str(ordinal)}:{uuid.uuid4().hex}"
        ),
    )


class OrderOwnerRegistry:
    def __init__(self, path: Path | None = None) -> None:
        self.path = Path(path) if path is not None else registry_path()
        self.lock_path = self.path.with_suffix(self.path.suffix + ".lock")

    @staticmethod
    def _canonical(event: dict[str, Any]) -> bytes:
        content = dict(event)
        content.pop("event_hash", None)
        return json.dumps(
            content, ensure_ascii=True, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")

    def _read_locked(self) -> list[dict[str, Any]]:
        try:
            lines = self.path.read_text(encoding="utf-8").splitlines()
        except FileNotFoundError:
            return []
        except OSError as exc:
            raise OwnerRegistryError(
                f"owner_registry_read_failed:{type(exc).__name__}"
            ) from exc
        events: list[dict[str, Any]] = []
        previous = "0" * 64
        for line_no, line in enumerate(lines, 1):
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError as exc:
                raise OwnerRegistryConflict(
                    f"owner_registry_json_invalid:line={line_no}"
                ) from exc
            if not isinstance(event, dict) or event.get("schema") != REGISTRY_SCHEMA:
                raise OwnerRegistryConflict(
                    f"owner_registry_schema_invalid:line={line_no}"
                )
            if event.get("previous_hash") != previous:
                raise OwnerRegistryConflict(
                    f"owner_registry_chain_invalid:line={line_no}"
                )
            expected = hashlib.sha256(
                previous.encode("ascii") + self._canonical(event)
            ).hexdigest()
            if event.get("event_hash") != expected:
                raise OwnerRegistryConflict(
                    f"owner_registry_hash_invalid:line={line_no}"
                )
            previous = expected
            events.append(event)
        return events

    @staticmethod
    def _state(events: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        state: dict[str, dict[str, Any]] = {}
        for event in events:
            intent_id = str(event.get("intent_id") or "")
            if not intent_id:
                continue
            current = state.setdefault(intent_id, {})
            current.update(event)
            if event.get("event") == "FILL_RECORDED":
                # Keep the immutable fill-event receive time across a later
                # terminal transition. Consumers must not substitute the
                # reconciliation time for the execution receipt time.
                current["fill_observed_at_kst"] = event.get("observed_at_kst")
            if event.get("event") == "SELL_AMEND_RECONCILED":
                parent = state[event["amendment_parent_intent_id"]]
                parent.update(
                    state="ORDER_TERMINAL",
                    filled_qty=event["amendment_parent_filled_qty"],
                    canceled_qty=event["quantity"],
                    amended_to=event["broker_order_no"],
                    event_hash=event["event_hash"],
                )
            if event.get("event") == "SELL_PARTIAL_CANCEL_RECONCILED":
                proof = event["partial_cancel_reconciliation"]
                cancel = state[proof["cancel_intent_id"]]
                # One fsynced event changes both projections. A crash cannot
                # release the target while leaving its cancel retryable.
                cancel.update(
                    state="ORDER_TERMINAL",
                    cancel_reconciliation=proof,
                    event_hash=event["event_hash"],
                )
            if event.get("event") in {
                "SELL_TERMINAL_CANCEL_RECONCILED",
                "BUY_TERMINAL_CANCEL_RECONCILED",
            }:
                proof = event["terminal_cancel_reconciliation"]
                cancel = state[proof["cancel_intent_id"]]
                cancel.update(
                    state="ORDER_TERMINAL",
                    terminal_cancel_reconciliation=proof,
                    event_hash=event["event_hash"],
                )
            # Read-only compatibility for the prior adapter's terminal event.
            # Bind the proof to that event's quantities, never to later fills.
            reason = event.get("reason")
            if (
                "terminal_reconciliation" not in current
                and event.get("event") == "ORDER_TERMINAL"
                and event.get("state") == "ORDER_TERMINAL"
                and event.get("side") == "SELL"
                and event.get("owner_type") in {"episode", "widget_auto_trade"}
                and isinstance(reason, str)
                and reason.startswith("adaptive_exact_terminal:")
                and len(reason.removeprefix("adaptive_exact_terminal:")) == 64
                and all(
                    c in "0123456789abcdef"
                    for c in reason.removeprefix("adaptive_exact_terminal:")
                )
                and all(k in event for k in _TERMINAL_PROOF_FIELDS)
                and type(event.get("quantity")) is int
                and type(event.get("filled_qty")) is int
                and 0 <= event["filled_qty"] <= event["quantity"]
                and event["quantity"] > 0
            ):
                current["terminal_reconciliation"] = _terminal_proof(
                    event, reason.removeprefix("adaptive_exact_terminal:")
                )
        return state

    def _append_locked(
        self, events: list[dict[str, Any]], event: dict[str, Any]
    ) -> dict[str, Any]:
        previous = str(events[-1].get("event_hash")) if events else "0" * 64
        row = {
            "schema": REGISTRY_SCHEMA,
            "event_id": uuid.uuid4().hex,
            "observed_at_kst": datetime.now(tz=KST).isoformat(),
            "previous_hash": previous,
            **event,
        }
        row["event_hash"] = hashlib.sha256(
            previous.encode("ascii") + self._canonical(row)
        ).hexdigest()
        encoded = json.dumps(
            row, ensure_ascii=True, sort_keys=True, separators=(",", ":")
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        registry_existed = self.path.exists()
        with self.path.open("a", encoding="utf-8") as fp:
            fp.write(encoded + "\n")
            fp.flush()
            os.fsync(fp.fileno())
        if not registry_existed:
            directory_fd = os.open(self.path.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        return row

    def _locked(self):
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        lock = self.lock_path.open("a+", encoding="utf-8")
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        return lock

    @staticmethod
    def _matching_migration_intent(
        state: dict[str, dict[str, Any]],
        *,
        account_key: str,
        context: OwnerOrderContext,
        symbol: str,
        quantity: int,
        average_price: int,
        route: str,
        order_date: str,
        broker_order_no: str,
        evidence_sha256: str,
    ) -> str | None:
        """Return an exact prior migration or reject conflicting identity reuse."""

        same_order = [
            row
            for row in state.values()
            if row.get("account_key") == account_key
            and row.get("order_date") == order_date
            and row.get("broker_order_no") == broker_order_no
        ]
        exact = [
            row
            for row in same_order
            if row.get("event") == "MIGRATED_POSITION_REGISTERED"
            and row.get("state") == "ORDER_TERMINAL"
            and row.get("symbol") == symbol
            and row.get("side") == "BUY"
            and row.get("action") == "NEW"
            and int(row.get("quantity") or 0) == quantity
            and int(row.get("filled_qty") or 0) == quantity
            and int(row.get("fill_amount") or 0) == quantity * average_price
            and row.get("route") == route
            and row.get("owner_type") == context.owner_type
            and row.get("owner_id") == context.owner_id
            and row.get("position_id") == context.position_id
            and row.get("client_intent_id") == context.client_intent_id
            and row.get("migration_evidence_sha256") == evidence_sha256
        ]
        if len(exact) == 1 and len(same_order) == 1:
            return str(exact[0]["intent_id"])
        if same_order:
            raise OwnerRegistryConflict("owner_registry_broker_order_no_conflict")
        if any(
            row.get("client_intent_id") == context.client_intent_id
            for row in state.values()
        ):
            raise OwnerRegistryConflict("owner_registry_client_intent_reused")
        return None

    def reserve(
        self,
        *,
        context: OwnerOrderContext,
        symbol: object,
        side: str,
        quantity: int,
        route: str,
        order_date: date | str,
        action: str = "NEW",
        original_order_no: str = "",
        authority_policy_id: str = "",
        authority_policy_hash: str = "",
    ) -> str:
        context.validate()
        clean_symbol = _registry_symbol(symbol)
        clean_side = str(side or "").strip().upper()
        clean_action = str(action or "NEW").strip().upper()
        clean_route = str(route or "").strip().upper()
        clean_date = _registry_order_date(order_date)
        clean_policy_id = str(authority_policy_id or "").strip()
        clean_policy_hash = str(authority_policy_hash or "").strip().lower()
        if not clean_symbol or clean_side not in {"BUY", "SELL"}:
            raise OwnerRegistryError("owner_registry_order_identity_invalid")
        if clean_action not in {"NEW", "CANCEL", "AMEND"} or int(quantity) < 0:
            raise OwnerRegistryError("owner_registry_order_request_invalid")
        if clean_route not in {"KRX", "NXT", "SOR"}:
            raise OwnerRegistryError("owner_registry_route_invalid")
        if bool(clean_policy_id) != bool(clean_policy_hash):
            raise OwnerRegistryError("owner_registry_policy_provenance_incomplete")
        if clean_policy_hash and (
            len(clean_policy_hash) != 64
            or any(ch not in "0123456789abcdef" for ch in clean_policy_hash)
        ):
            raise OwnerRegistryError("owner_registry_policy_hash_invalid")
        lock = self._locked()
        try:
            events = self._read_locked()
            state = self._state(events)
            account_key = broker_account_key()
            same_client = [
                row
                for row in state.values()
                if row.get("client_intent_id") == context.client_intent_id
            ]
            if same_client:
                raise OwnerRegistryConflict("owner_registry_client_intent_reused")
            if clean_action in {"CANCEL", "AMEND"}:
                original = self._assert_owner_from_state(
                    state,
                    context=context,
                    order_date=clean_date,
                    broker_order_no=original_order_no,
                )
                if original.get("state") != "ORDER_BOUND":
                    raise OwnerRegistryConflict(
                        "owner_registry_cancel_original_not_open"
                    )
                remaining = self._remaining_commitment(original)
                if clean_action == "AMEND" and (
                    clean_policy_id != "machine_ws_target_ratchet_v1"
                    or clean_side != "SELL"
                    or context.owner_type not in {"episode", "widget_auto_trade"}
                    or original.get("side") != "SELL"
                    or original.get("action") != "NEW"
                    or original.get("symbol") != clean_symbol
                    or original.get("route") != clean_route
                    or original.get("filled_qty", 0) != 0
                    or original.get("canceled_qty", 0) != 0
                    or type(quantity) is not int
                    or quantity != remaining
                ):
                    raise OwnerRegistryConflict("owner_registry_amend_requires_unfilled_owned_sell")
                if clean_action == "AMEND":
                    ancestor, visited = original, set()
                    while ancestor.get("amendment_parent_intent_id"):
                        ancestor_id = ancestor["amendment_parent_intent_id"]
                        if ancestor_id in visited or ancestor_id not in state:
                            raise OwnerRegistryConflict("owner_registry_amend_lineage_invalid")
                        visited.add(ancestor_id)
                        ancestor = state[ancestor_id]
                        if ancestor.get("filled_qty", 0) != 0:
                            raise OwnerRegistryConflict("owner_registry_amend_ancestor_partially_filled")
                if remaining <= 0:
                    raise OwnerRegistryConflict(
                        "owner_registry_cancel_original_no_remaining_quantity"
                    )
                if original.get("canceled_qty", 0) and int(quantity) > remaining:
                    raise OwnerRegistryConflict(
                        "owner_registry_cancel_exceeds_remainder"
                    )
                duplicate_cancel = [
                    row
                    for row in state.values()
                    if row.get("account_key") == broker_account_key()
                    and row.get("order_date") == clean_date
                    and row.get("action") in {"CANCEL", "AMEND"}
                    and row.get("original_order_no")
                    == str(original_order_no or "").strip()
                    and row.get("state")
                    in {"INTENT_RESERVED", "INTENT_AMBIGUOUS", "ORDER_BOUND"}
                ]
                if duplicate_cancel:
                    raise OwnerRegistryConflict(
                        "owner_registry_cancel_already_pending_or_accepted"
                    )
                clean_side = str(original.get("side") or "").strip().upper()
            elif clean_side == "SELL":
                position_qty = 0
                open_sell_commitment = 0
                for row in state.values():
                    if (
                        row.get("account_key") != account_key
                        or row.get("symbol") != clean_symbol
                        or row.get("position_id") != context.position_id
                        or row.get("action") != "NEW"
                    ):
                        continue
                    filled = int(row.get("filled_qty") or 0)
                    if row.get("side") == "BUY":
                        position_qty += filled
                    elif row.get("side") == "SELL":
                        position_qty -= filled
                        if row.get("state") in {
                            "INTENT_RESERVED",
                            "INTENT_AMBIGUOUS",
                            "ORDER_BOUND",
                        }:
                            open_sell_commitment += self._remaining_commitment(row)
                available = position_qty - open_sell_commitment
                if int(quantity) > available:
                    raise OwnerRegistryConflict(
                        "owner_registry_sell_quantity_exceeds_owner_available:"
                        f"requested={int(quantity)}:available={available}"
                    )
            for row in state.values():
                if (
                    row.get("account_key") == account_key
                    and row.get("order_date") == clean_date
                    and row.get("symbol") == clean_symbol
                    and row.get("side") == clean_side
                    and row.get("state") in _ACTIVE_UNBOUND_STATES
                ):
                    raise OwnerRegistryBusy(
                        "owner_registry_symbol_side_submit_unresolved"
                    )
            intent_id = uuid.uuid4().hex
            self._append_locked(
                events,
                {
                    "event": "INTENT_RESERVED",
                    "state": "INTENT_RESERVED",
                    "intent_id": intent_id,
                    "account_key": account_key,
                    "order_date": clean_date,
                    "symbol": clean_symbol,
                    "side": clean_side,
                    "action": clean_action,
                    "quantity": int(quantity),
                    "route": clean_route,
                    "original_order_no": str(original_order_no or "").strip(),
                    "owner_type": context.owner_type,
                    "owner_id": context.owner_id,
                    "position_id": context.position_id,
                    "client_intent_id": context.client_intent_id,
                    "authority_policy_id": clean_policy_id,
                    "authority_policy_hash": clean_policy_hash,
                },
            )
            return intent_id
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            lock.close()

    def reconcile_sell_amendment(
        self, *, context, intent_id, parent_filled_qty, child_quantity,
        child_filled_qty, child_remaining_qty, receipt_sha256,
    ):
        """Atomically replace commitment only after exact dated/current proof.

        An AMEND reservation/ACK alone never releases the parent's quantity.
        A reconciled child is a normal SELL for existing custody consumers;
        its original-order linkage and immutable amendment proof remain.
        """
        context.validate()
        counts = (parent_filled_qty, child_quantity, child_filled_qty, child_remaining_qty)
        if (any(type(n) is not int or n < 0 for n in counts)
            or child_quantity <= 0
            or child_filled_qty + child_remaining_qty != child_quantity
            or not isinstance(receipt_sha256, str)
            or len(receipt_sha256) != 64
            or any(c not in "0123456789abcdef" for c in receipt_sha256)):
            raise OwnerRegistryConflict("owner_registry_amend_proof_invalid")
        lock = self._locked()
        try:
            events = self._read_locked()
            state = self._state(events)
            child = state.get(intent_id, {})
            parent = self._assert_owner_from_state(
                state, context=context, order_date=child.get("order_date"),
                broker_order_no=child.get("original_order_no"),
            )
            if (child.get("account_key") != broker_account_key(require_explicit=True)
                or any(child.get(k) != getattr(context, k) for k in ("owner_type", "owner_id", "position_id"))
                or child.get("authority_policy_id") != "machine_ws_target_ratchet_v1"
                or child.get("side") != "SELL"
                or child.get("symbol") != parent.get("symbol")
                or child.get("route") != parent.get("route")
                or parent.get("quantity") != parent_filled_qty + child_quantity
                or parent.get("filled_qty", 0) > parent_filled_qty):
                raise OwnerRegistryConflict("owner_registry_amend_binding_invalid")
            if child.get("amendment_receipt_sha256"):
                if (child.get("quantity") != child_quantity
                    or child.get("amendment_parent_filled_qty") != parent_filled_qty):
                    raise OwnerRegistryConflict("owner_registry_amend_replay_conflict")
                return dict(child)
            if (child.get("action") != "AMEND" or child.get("state") != "ORDER_BOUND"
                or parent.get("state") != "ORDER_BOUND"
                or parent.get("canceled_qty", 0) != 0):
                raise OwnerRegistryConflict("owner_registry_amend_not_pending")
            retained = {k: v for k, v in child.items() if k not in {
                "schema", "event_id", "observed_at_kst", "previous_hash", "event_hash",
            }}
            return dict(self._append_locked(events, {
                **retained, "event": "SELL_AMEND_RECONCILED", "action": "NEW",
                "state": "ORDER_TERMINAL" if child_remaining_qty == 0 else "ORDER_BOUND",
                "quantity": child_quantity, "filled_qty": child_filled_qty,
                "amendment_parent_intent_id": parent["intent_id"],
                "amendment_parent_filled_qty": parent_filled_qty,
                "amendment_receipt_sha256": receipt_sha256,
            }))
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            lock.close()

    def transition(
        self,
        intent_id: str,
        *,
        state: str,
        broker_order_no: str = "",
        reason: str = "",
    ) -> None:
        clean_state = str(state or "").strip().upper()
        if clean_state not in {
            "ORDER_BOUND",
            "INTENT_REJECTED",
            "INTENT_AMBIGUOUS",
            "ORDER_TERMINAL",
        }:
            raise OwnerRegistryError("owner_registry_transition_invalid")
        lock = self._locked()
        try:
            events = self._read_locked()
            state_by_intent = self._state(events)
            current = state_by_intent.get(str(intent_id))
            if not current:
                raise OwnerRegistryConflict("owner_registry_intent_missing")
            order_no = str(
                broker_order_no or current.get("broker_order_no") or ""
            ).strip()
            current_state = str(current.get("state") or "").strip().upper()
            if current_state == "ORDER_TERMINAL":
                terminal_order_no = str(current.get("broker_order_no") or "").strip()
                if clean_state in {"ORDER_BOUND", "ORDER_TERMINAL"}:
                    if order_no != terminal_order_no:
                        raise OwnerRegistryConflict(
                            "owner_registry_terminal_order_number_conflict"
                        )
                    # A fill receipt can reach the registry before the
                    # synchronous submit response. Never downgrade an already
                    # terminal order when that later response confirms the
                    # same broker order.
                    return
                # A late reject/timeout cannot rewrite a receipt-confirmed
                # terminal order. The caller must reconcile the contradictory
                # broker outcome and must not submit again.
                raise OwnerRegistryConflict(
                    "owner_registry_terminal_transition_conflict"
                )
            allowed_transitions = {
                "INTENT_RESERVED": {
                    "ORDER_BOUND",
                    "INTENT_REJECTED",
                    "INTENT_AMBIGUOUS",
                },
                "INTENT_AMBIGUOUS": {"ORDER_BOUND", "INTENT_AMBIGUOUS"},
                "ORDER_BOUND": {"ORDER_BOUND", "ORDER_TERMINAL"},
                "INTENT_REJECTED": {"INTENT_REJECTED"},
                "ORDER_TERMINAL": {"ORDER_TERMINAL"},
            }
            if clean_state not in allowed_transitions.get(current_state, set()):
                raise OwnerRegistryConflict(
                    "owner_registry_state_transition_forbidden:"
                    f"{current_state}->{clean_state}"
                )
            if (
                clean_state == current_state
                and order_no == str(current.get("broker_order_no") or "").strip()
            ):
                return
            if clean_state in {"ORDER_BOUND", "ORDER_TERMINAL"}:
                if not (order_no.isdigit() and len(order_no) == 7):
                    raise OwnerRegistryConflict(
                        "owner_registry_broker_order_no_invalid"
                    )
            if clean_state == "ORDER_BOUND":
                for other_id, row in state_by_intent.items():
                    if other_id == intent_id:
                        continue
                    if (
                        row.get("account_key") == current.get("account_key")
                        and row.get("order_date") == current.get("order_date")
                        and row.get("broker_order_no") == order_no
                    ):
                        raise OwnerRegistryConflict(
                            "owner_registry_broker_order_no_conflict"
                        )
            self._append_locked(
                events,
                {
                    **{
                        key: current.get(key)
                        for key in (
                            "intent_id",
                            "account_key",
                            "order_date",
                            "symbol",
                            "side",
                            "action",
                            "quantity",
                            "route",
                            "original_order_no",
                            "owner_type",
                            "owner_id",
                            "position_id",
                            "client_intent_id",
                            "authority_policy_id",
                            "authority_policy_hash",
                        )
                    },
                    "event": clean_state,
                    "state": clean_state,
                    "broker_order_no": order_no,
                    "reason": str(reason or "")[:240],
                    "filled_qty": int(current.get("filled_qty") or 0),
                    "fill_amount": int(current.get("fill_amount") or 0),
                },
            )
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            lock.close()

    def register_migrated_position(
        self,
        *,
        context: OwnerOrderContext,
        symbol: object,
        quantity: int,
        average_price: int,
        route: str,
        order_date: date | str,
        broker_order_no: str,
        evidence_sha256: str,
    ) -> str:
        """Seed exact broker-reconciled custody before coexistence is enabled.

        The method only appends a fully filled historical position to the
        journal. It never calls the broker or mutates account state, and the
        immutable reconciliation evidence digest is mandatory.
        """

        context.validate()
        clean_symbol = _registry_symbol(symbol)
        clean_date = _registry_order_date(order_date)
        clean_route = str(route or "").strip().upper()
        order_no = str(broker_order_no or "").strip()
        evidence_hash = str(evidence_sha256 or "").strip().lower()
        migrated_qty = int(quantity)
        migrated_price = int(average_price)
        if not clean_symbol or migrated_qty <= 0 or migrated_price <= 0:
            raise OwnerRegistryError("owner_registry_migration_position_invalid")
        if clean_route not in {"KRX", "NXT", "SOR"}:
            raise OwnerRegistryError("owner_registry_route_invalid")
        if not (order_no.isdigit() and len(order_no) == 7):
            raise OwnerRegistryError("owner_registry_broker_order_no_invalid")
        if len(evidence_hash) != 64 or any(
            ch not in "0123456789abcdef" for ch in evidence_hash
        ):
            raise OwnerRegistryError("owner_registry_migration_evidence_invalid")
        lock = self._locked()
        try:
            events = self._read_locked()
            state = self._state(events)
            account_key = broker_account_key(require_explicit=True)
            existing_intent = self._matching_migration_intent(
                state,
                account_key=account_key,
                context=context,
                symbol=clean_symbol,
                quantity=migrated_qty,
                average_price=migrated_price,
                route=clean_route,
                order_date=clean_date,
                broker_order_no=order_no,
                evidence_sha256=evidence_hash,
            )
            if existing_intent is not None:
                return existing_intent
            if any(
                row.get("account_key") == account_key
                and row.get("symbol") == clean_symbol
                and row.get("event") == "POLICY_ACTIVATED"
                for row in state.values()
            ):
                raise OwnerRegistryConflict(
                    "owner_registry_migration_after_policy_activation_forbidden"
                )
            intent_id = uuid.uuid4().hex
            self._append_locked(
                events,
                {
                    "event": "MIGRATED_POSITION_REGISTERED",
                    "state": "ORDER_TERMINAL",
                    "intent_id": intent_id,
                    "account_key": account_key,
                    "order_date": clean_date,
                    "symbol": clean_symbol,
                    "side": "BUY",
                    "action": "NEW",
                    "quantity": migrated_qty,
                    "route": clean_route,
                    "original_order_no": "",
                    "owner_type": context.owner_type,
                    "owner_id": context.owner_id,
                    "position_id": context.position_id,
                    "client_intent_id": context.client_intent_id,
                    "broker_order_no": order_no,
                    "filled_qty": migrated_qty,
                    "fill_amount": migrated_qty * migrated_price,
                    "migration_evidence_sha256": evidence_hash,
                },
            )
            return intent_id
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            lock.close()

    def matched_migrated_position_quantity(
        self,
        *,
        context: OwnerOrderContext,
        symbol: object,
        quantity: int,
        average_price: int,
        route: str,
        order_date: date | str,
        broker_order_no: str,
        evidence_sha256: str,
    ) -> int:
        """Return quantity already registered for one exact migration request.

        This read-only lookup makes an interrupted apply resumable without
        counting a migration twice. Conflicting order or intent reuse remains
        a hard failure instead of being interpreted as an absent migration.
        """

        context.validate()
        clean_symbol = _registry_symbol(symbol)
        clean_date = _registry_order_date(order_date)
        clean_route = str(route or "").strip().upper()
        order_no = str(broker_order_no or "").strip()
        evidence_hash = str(evidence_sha256 or "").strip().lower()
        migrated_qty = int(quantity)
        migrated_price = int(average_price)
        if migrated_qty <= 0 or migrated_price <= 0:
            raise OwnerRegistryError("owner_registry_migration_position_invalid")
        if clean_route not in {"KRX", "NXT", "SOR"}:
            raise OwnerRegistryError("owner_registry_route_invalid")
        if not (order_no.isdigit() and len(order_no) == 7):
            raise OwnerRegistryError("owner_registry_broker_order_no_invalid")
        if len(evidence_hash) != 64 or any(
            ch not in "0123456789abcdef" for ch in evidence_hash
        ):
            raise OwnerRegistryError("owner_registry_migration_evidence_invalid")
        lock = self._locked()
        try:
            intent_id = self._matching_migration_intent(
                self._state(self._read_locked()),
                account_key=broker_account_key(require_explicit=True),
                context=context,
                symbol=clean_symbol,
                quantity=migrated_qty,
                average_price=migrated_price,
                route=clean_route,
                order_date=clean_date,
                broker_order_no=order_no,
                evidence_sha256=evidence_hash,
            )
            return migrated_qty if intent_id is not None else 0
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            lock.close()

    def register_reconciled_manual_exit(
        self,
        *,
        custody_context: OwnerOrderContext,
        symbol: object,
        quantity: int,
        average_price: int,
        route: str,
        order_date: date | str,
        broker_order_no: str,
        evidence_sha256: str,
    ) -> str:
        """Append an already-executed manual SELL to one exact custody owner.

        Manual HTS orders cannot be attributed from the broker's aggregate
        symbol balance. An operator/reconciler must first select the exact
        custody owner from broker receipt evidence, then call this read-after-
        execution bridge. This method never submits, cancels, or modifies a
        broker order.
        """

        custody_context.validate()
        clean_symbol = _registry_symbol(symbol)
        clean_date = _registry_order_date(order_date)
        clean_route = str(route or "").strip().upper()
        order_no = str(broker_order_no or "").strip()
        evidence_hash = str(evidence_sha256 or "").strip().lower()
        reconciled_qty = int(quantity)
        reconciled_price = int(average_price)
        if not clean_symbol or reconciled_qty <= 0 or reconciled_price <= 0:
            raise OwnerRegistryError("owner_registry_manual_exit_invalid")
        if clean_route not in {"KRX", "NXT", "SOR"}:
            raise OwnerRegistryError("owner_registry_route_invalid")
        if not (order_no.isdigit() and len(order_no) == 7):
            raise OwnerRegistryError("owner_registry_broker_order_no_invalid")
        if len(evidence_hash) != 64 or any(
            ch not in "0123456789abcdef" for ch in evidence_hash
        ):
            raise OwnerRegistryError("owner_registry_manual_exit_evidence_invalid")

        lock = self._locked()
        try:
            events = self._read_locked()
            state = self._state(events)
            if any(
                row.get("account_key") == broker_account_key()
                and row.get("order_date") == clean_date
                and row.get("broker_order_no") == order_no
                for row in state.values()
            ):
                raise OwnerRegistryConflict("owner_registry_broker_order_no_conflict")
            if any(
                row.get("client_intent_id") == custody_context.client_intent_id
                for row in state.values()
            ):
                raise OwnerRegistryConflict("owner_registry_client_intent_reused")
            position_qty = 0
            open_sell_commitment = 0
            for row in state.values():
                if (
                    row.get("account_key") != broker_account_key()
                    or row.get("symbol") != clean_symbol
                    or row.get("position_id") != custody_context.position_id
                    or row.get("owner_type") != custody_context.owner_type
                    or row.get("owner_id") != custody_context.owner_id
                    or row.get("action") != "NEW"
                ):
                    continue
                filled = int(row.get("filled_qty") or 0)
                if row.get("side") == "BUY":
                    position_qty += filled
                else:
                    position_qty -= filled
                    if row.get("state") in {
                        "INTENT_RESERVED",
                        "INTENT_AMBIGUOUS",
                        "ORDER_BOUND",
                    }:
                        open_sell_commitment += self._remaining_commitment(row)
            available = position_qty - open_sell_commitment
            if reconciled_qty > available:
                raise OwnerRegistryConflict(
                    "owner_registry_manual_exit_exceeds_owner_available:"
                    f"requested={reconciled_qty}:available={available}"
                )
            intent_id = uuid.uuid4().hex
            self._append_locked(
                events,
                {
                    "event": "MANUAL_EXIT_RECONCILED",
                    "state": "ORDER_TERMINAL",
                    "intent_id": intent_id,
                    "account_key": broker_account_key(),
                    "order_date": clean_date,
                    "symbol": clean_symbol,
                    "side": "SELL",
                    "action": "NEW",
                    "quantity": reconciled_qty,
                    "route": clean_route,
                    "original_order_no": "",
                    "owner_type": custody_context.owner_type,
                    "owner_id": custody_context.owner_id,
                    "position_id": custody_context.position_id,
                    "client_intent_id": custody_context.client_intent_id,
                    "execution_owner_type": "manual_operator",
                    "broker_order_no": order_no,
                    "filled_qty": reconciled_qty,
                    "fill_amount": reconciled_qty * reconciled_price,
                    "manual_exit_evidence_sha256": evidence_hash,
                },
            )
            return intent_id
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            lock.close()

    @staticmethod
    def _assert_owner_from_state(
        state: dict[str, dict[str, Any]],
        *,
        context: OwnerOrderContext,
        order_date: str,
        broker_order_no: str,
    ) -> dict[str, Any]:
        matches = [
            row
            for row in state.values()
            if row.get("account_key") == broker_account_key()
            and row.get("order_date") == str(order_date)
            and row.get("broker_order_no") == str(broker_order_no or "").strip()
        ]
        if len(matches) != 1:
            raise OwnerRegistryConflict(
                "owner_registry_exact_order_missing_or_ambiguous"
            )
        row = matches[0]
        if (
            row.get("owner_type") != context.owner_type
            or row.get("owner_id") != context.owner_id
            or row.get("position_id") != context.position_id
        ):
            raise OwnerRegistryConflict("owner_registry_cross_owner_order_forbidden")
        return row

    def assert_owner(
        self,
        *,
        context: OwnerOrderContext,
        order_date: date | str,
        broker_order_no: str,
    ) -> dict[str, Any]:
        context.validate()
        clean_date = _registry_order_date(order_date)
        lock = self._locked()
        try:
            return dict(
                self._assert_owner_from_state(
                    self._state(self._read_locked()),
                    context=context,
                    order_date=clean_date,
                    broker_order_no=broker_order_no,
                )
            )
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            lock.close()

    def intent_for_client(self, *, context: OwnerOrderContext) -> dict[str, Any] | None:
        """Read one durable intent without guessing a broker order from a symbol.

        This does not bind/retry an unacknowledged intent or grant new authority.
        The original account, owner and position must all match after restart.
        """
        context.validate()
        account = broker_account_key(require_explicit=True)
        lock = self._locked()
        try:
            matches = [
                row
                for row in self._state(self._read_locked()).values()
                if row.get("client_intent_id") == context.client_intent_id
            ]
            if not matches:
                return None
            if len(matches) != 1 or any(
                matches[0].get(key) != value
                for key, value in {
                    "account_key": account,
                    "owner_type": context.owner_type,
                    "owner_id": context.owner_id,
                    "position_id": context.position_id,
                }.items()
            ):
                raise OwnerRegistryConflict("owner_registry_client_binding_conflict")
            return dict(matches[0])
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            lock.close()

    def order_owner(
        self, *, order_date: date | str, broker_order_no: str
    ) -> dict[str, Any] | None:
        clean_date = _registry_order_date(order_date)
        lock = self._locked()
        try:
            matches = [
                row
                for row in self._state(self._read_locked()).values()
                if row.get("account_key") == broker_account_key()
                and row.get("order_date") == clean_date
                and row.get("broker_order_no") == str(broker_order_no or "").strip()
            ]
            if len(matches) > 1:
                raise OwnerRegistryConflict("owner_registry_broker_order_no_ambiguous")
            return dict(matches[0]) if matches else None
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            lock.close()

    def bind_unique_pending_receipt(
        self,
        *,
        symbol: object,
        side: str,
        order_date: date | str,
        broker_order_no: str,
        broker_order_qty: int | None = None,
    ) -> dict[str, Any] | None:
        """Bind a fill-before-submit receipt only to one exact pending lane."""

        clean_symbol = _registry_symbol(symbol)
        clean_side = str(side or "").strip().upper()
        clean_date = _registry_order_date(order_date)
        order_no = str(broker_order_no or "").strip()
        if not (order_no.isdigit() and len(order_no) == 7):
            raise OwnerRegistryConflict("owner_registry_broker_order_no_invalid")
        lock = self._locked()
        try:
            events = self._read_locked()
            state = self._state(events)
            already = [
                row
                for row in state.values()
                if row.get("account_key") == broker_account_key()
                and row.get("order_date") == clean_date
                and row.get("broker_order_no") == order_no
            ]
            if len(already) == 1:
                return dict(already[0])
            if len(already) > 1:
                raise OwnerRegistryConflict("owner_registry_broker_order_no_ambiguous")
            candidates = [
                row
                for row in state.values()
                if row.get("account_key") == broker_account_key()
                and row.get("order_date") == clean_date
                and row.get("symbol") == clean_symbol
                and row.get("side") == clean_side
                and row.get("action") == "NEW"
                and row.get("state") in _ACTIVE_UNBOUND_STATES
            ]
            if broker_order_qty is not None:
                candidates = [
                    row
                    for row in candidates
                    if int(row.get("quantity") or 0) == int(broker_order_qty)
                ]
            if len(candidates) != 1:
                return None
            current = candidates[0]
            bound = self._append_locked(
                events,
                {
                    **{
                        key: current.get(key)
                        for key in (
                            "intent_id",
                            "account_key",
                            "order_date",
                            "symbol",
                            "side",
                            "action",
                            "quantity",
                            "route",
                            "original_order_no",
                            "owner_type",
                            "owner_id",
                            "position_id",
                            "client_intent_id",
                            "authority_policy_id",
                            "authority_policy_hash",
                        )
                    },
                    "event": "ORDER_BOUND_FROM_RECEIPT",
                    "state": "ORDER_BOUND",
                    "broker_order_no": order_no,
                    "reason": "unique_symbol_side_quantity_pending_intent",
                    "filled_qty": int(current.get("filled_qty") or 0),
                    "fill_amount": int(current.get("fill_amount") or 0),
                },
            )
            return dict(bound)
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            lock.close()

    def record_fill(
        self,
        *,
        context: OwnerOrderContext,
        symbol: object,
        side: str,
        order_quantity: int,
        order_date: date | str,
        broker_order_no: str,
        cumulative_filled_qty: int,
        cumulative_fill_amount: int | None = None,
        execution_no: str = "",
    ) -> None:
        context.validate()
        clean_symbol = _registry_symbol(symbol)
        clean_side = str(side or "").strip().upper()
        requested = int(order_quantity)
        clean_date = _registry_order_date(order_date)
        filled = int(cumulative_filled_qty)
        supplied_amount = (
            None if cumulative_fill_amount is None else int(cumulative_fill_amount)
        )
        if not clean_symbol or clean_side not in {"BUY", "SELL"} or requested <= 0:
            raise OwnerRegistryError("owner_registry_fill_identity_invalid")
        if filled < 0 or (supplied_amount is not None and supplied_amount < 0):
            raise OwnerRegistryError("owner_registry_fill_negative")
        lock = self._locked()
        try:
            events = self._read_locked()
            state = self._state(events)
            current = self._assert_owner_from_state(
                state,
                context=context,
                order_date=clean_date,
                broker_order_no=broker_order_no,
            )
            if (
                current.get("symbol") != clean_symbol
                or current.get("side") != clean_side
                or current.get("action") != "NEW"
                or int(current.get("quantity") or 0) != requested
            ):
                raise OwnerRegistryConflict(
                    "owner_registry_fill_order_identity_conflict"
                )
            prior_qty = int(current.get("filled_qty") or 0)
            prior_amount = int(current.get("fill_amount") or 0)
            amount = prior_amount if supplied_amount is None else supplied_amount
            if filled < prior_qty or amount < prior_amount:
                raise OwnerRegistryConflict("owner_registry_fill_regression")
            if filled > int(current.get("quantity") or 0) - int(
                current.get("canceled_qty", 0)
            ):
                raise OwnerRegistryConflict("owner_registry_overfill")
            if filled == prior_qty and amount == prior_amount:
                return
            self._append_locked(
                events,
                {
                    **{
                        key: current.get(key)
                        for key in (
                            "intent_id",
                            "account_key",
                            "order_date",
                            "symbol",
                            "side",
                            "action",
                            "quantity",
                            "route",
                            "original_order_no",
                            "owner_type",
                            "owner_id",
                            "position_id",
                            "client_intent_id",
                            "authority_policy_id",
                            "authority_policy_hash",
                            "broker_order_no",
                        )
                    },
                    "event": "FILL_RECORDED",
                    "state": (
                        "ORDER_TERMINAL"
                        if current.get("state") == "ORDER_TERMINAL"
                        else "ORDER_BOUND"
                    ),
                    "filled_qty": filled,
                    "fill_amount": amount,
                    "execution_no": str(execution_no or "")[:80],
                },
            )
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            lock.close()

    @staticmethod
    def _remaining_commitment(row: dict[str, Any]) -> int:
        canceled = row.get("canceled_qty", 0)
        if type(canceled) is not int or canceled < 0:
            raise OwnerRegistryConflict("owner_registry_canceled_quantity_invalid")
        remaining = (
            int(row.get("quantity") or 0) - int(row.get("filled_qty") or 0) - canceled
        )
        if remaining < 0:
            raise OwnerRegistryConflict("owner_registry_quantity_conservation_failed")
        return remaining

    def record_partial_cancel_reconciliation(
        self,
        *,
        context: OwnerOrderContext,
        order_date: str,
        target_order_no: str,
        cancel_order_no: str,
        target_event_hash: str,
        cancel_event_hash: str,
        filled_qty: int,
        remaining_qty: int,
        confirmed_qty: int,
        receipt_sha256: str,
    ) -> None:
        """Consume the adapter's exact full-request confirmation, not its ACK.

        The original target stays open. This is quantity accounting only, not
        a runner allocation, price/cost reconstruction or SELL authorization.
        Compare journal versions under the same lock as the atomic append.
        """
        context.validate()
        clean_date = _registry_order_date(order_date)
        if (
            context.owner_type not in {"widget_auto_trade", "episode"}
            or any(
                type(v) is not int or v < 0
                for v in (filled_qty, remaining_qty, confirmed_qty)
            )
            or remaining_qty <= 0
            or confirmed_qty <= 0
            or target_order_no == cancel_order_no
            or any(
                not isinstance(v, str)
                or len(v) != 64
                or any(c not in "0123456789abcdef" for c in v)
                for v in (target_event_hash, cancel_event_hash, receipt_sha256)
            )
        ):
            raise OwnerRegistryError("owner_registry_partial_cancel_invalid")
        lock = self._locked()
        try:
            events = self._read_locked()
            state = self._state(events)
            target = self._assert_owner_from_state(
                state,
                context=context,
                order_date=clean_date,
                broker_order_no=target_order_no,
            )
            cancel = self._assert_owner_from_state(
                state,
                context=context,
                order_date=clean_date,
                broker_order_no=cancel_order_no,
            )
            if (
                target.get("side") != "SELL"
                or target.get("action") != "NEW"
                or target.get("state") != "ORDER_BOUND"
                or cancel.get("side") != "SELL"
                or cancel.get("action") != "CANCEL"
                or cancel.get("original_order_no") != target_order_no
                or cancel.get("quantity") != confirmed_qty
                or cancel.get("authority_policy_id") != "machine_adaptive_exit_v1"
                or any(cancel.get(k) != target.get(k) for k in ("symbol", "route"))
                or target.get("filled_qty", 0) > filled_qty
            ):
                raise OwnerRegistryConflict(
                    "owner_registry_partial_cancel_identity_conflict"
                )
            previous = cancel.get("cancel_reconciliation")
            already = (
                isinstance(previous, dict)
                and previous.get("confirmed_qty") == confirmed_qty
            )
            total_canceled = target.get("canceled_qty", 0) + (
                0 if already else confirmed_qty
            )
            if target["quantity"] != filled_qty + remaining_qty + total_canceled:
                raise OwnerRegistryConflict(
                    "owner_registry_partial_cancel_quantity_conflict"
                )
            if (
                (previous is not None and not already)
                or cancel.get("state")
                != ("ORDER_TERMINAL" if already else "ORDER_BOUND")
                or target.get("event_hash") != target_event_hash
                or cancel.get("event_hash") != cancel_event_hash
            ):
                raise OwnerRegistryConflict(
                    "owner_registry_partial_cancel_journal_changed"
                )
            if any(
                r.get("account_key") == target["account_key"]
                and r.get("order_date") == clean_date
                and r.get("original_order_no") == target_order_no
                and r.get("intent_id") != cancel["intent_id"]
                and r.get("state")
                in {"INTENT_RESERVED", "INTENT_AMBIGUOUS", "ORDER_BOUND"}
                for r in state.values()
            ):
                raise OwnerRegistryConflict(
                    "owner_registry_partial_cancel_other_pending"
                )
            if already and target.get("filled_qty", 0) == filled_qty:
                # Still validate versions and pending successors on a replay.
                return
            proof = {
                "schema": "order_owner_partial_cancel_reconciliation_v1",
                "source_contract": "machine_adaptive_exit_full_cancel_request_dated_current_v1",
                "target_intent_id": target["intent_id"],
                "cancel_intent_id": cancel["intent_id"],
                "target_order_no": target_order_no,
                "cancel_order_no": cancel_order_no,
                "order_date": clean_date,
                "confirmed_qty": confirmed_qty,
                "filled_qty": filled_qty,
                "remaining_qty": remaining_qty,
                "target_event_hash": target_event_hash,
                "cancel_event_hash": cancel_event_hash,
                "receipt_sha256": receipt_sha256,
            }
            if already:
                # Keep the first immutable cancel proof while refreshing only
                # the target's cumulative fill. The canceled total is unchanged.
                self._append_locked(
                    events,
                    {
                        "intent_id": target["intent_id"],
                        "account_key": target["account_key"],
                        "event": "PARTIAL_CANCEL_TARGET_FILL_REFRESHED",
                        "filled_qty": filled_qty,
                    },
                )
                return
            self._append_locked(
                events,
                {
                    "intent_id": target["intent_id"],
                    "account_key": target["account_key"],
                    "event": "SELL_PARTIAL_CANCEL_RECONCILED",
                    "state": "ORDER_BOUND",
                    "filled_qty": filled_qty,
                    "canceled_qty": total_canceled,
                    "partial_cancel_reconciliation": proof,
                },
            )
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            lock.close()

    def record_terminal_cancel_reconciliation(self, **kwargs) -> None:
        """SELL-only public contract; BUY cancellation has a separate entrypoint."""
        self._record_terminal_cancel_reconciliation(side="SELL", **kwargs)

    def record_buy_terminal_cancel_reconciliation(self, **kwargs) -> None:
        """Existing BUY root/child closure, not new entry or SELL authority."""
        self._record_terminal_cancel_reconciliation(side="BUY", **kwargs)

    def _record_terminal_cancel_reconciliation(
        self,
        *,
        side: str,
        context: OwnerOrderContext,
        order_date: str,
        target_order_no: str,
        cancel_order_no: str,
        target_event_hash: str,
        cancel_event_hash: str,
        filled_qty: int,
        confirmed_qty: int,
        receipt_sha256: str,
        terminal_receipt_sha256: str,
    ) -> None:
        """Atomically terminalize the exact root and confirmed cancel child.

        A target terminal alone does not prove the child cancel terminal. The
        adapter supplies both complete dated/current evidence and a positive
        cnfm_qty, including a smaller confirmation after a late root fill.
        SELL residual remains Q - F; BUY inventory is F. Neither side counts
        canceled shares as fills. The side-specific public entrypoint fixes the
        proof source, so BUY evidence cannot satisfy a SELL terminal consumer.
        """
        context.validate()
        clean_date = _registry_order_date(order_date)
        if (
            side not in {"BUY", "SELL"}
            or context.owner_type not in {"widget_auto_trade", "episode"}
            or type(filled_qty) is not int
            or filled_qty < 0
            or type(confirmed_qty) is not int
            or confirmed_qty <= 0
            or target_order_no == cancel_order_no
            or any(
                not isinstance(v, str)
                or len(v) != 64
                or any(c not in "0123456789abcdef" for c in v)
                for v in (
                    target_event_hash,
                    cancel_event_hash,
                    receipt_sha256,
                    terminal_receipt_sha256,
                )
            )
        ):
            raise OwnerRegistryError("owner_registry_terminal_cancel_invalid")
        lock = self._locked()
        try:
            events = self._read_locked()
            state = self._state(events)
            target = self._assert_owner_from_state(
                state,
                context=context,
                order_date=clean_date,
                broker_order_no=target_order_no,
            )
            cancel = self._assert_owner_from_state(
                state,
                context=context,
                order_date=clean_date,
                broker_order_no=cancel_order_no,
            )
            previous = cancel.get("terminal_cancel_reconciliation")
            if (
                target.get("side") != side
                or target.get("action") != "NEW"
                or target.get("state") not in {"ORDER_BOUND", "ORDER_TERMINAL"}
                or cancel.get("side") != side
                or cancel.get("action") != "CANCEL"
                or cancel.get("original_order_no") != target_order_no
                or type(cancel.get("quantity")) is not int
                or not 0 < confirmed_qty <= cancel["quantity"]
                or cancel.get("authority_policy_id") not in {
                    "machine_adaptive_exit_v1", "machine_profit_stagnation_v1"
                }
                or any(cancel.get(k) != target.get(k) for k in ("symbol", "route"))
                or target.get("filled_qty", 0) > filled_qty
                or target.get("event_hash") != target_event_hash
                or cancel.get("event_hash") != cancel_event_hash
            ):
                raise OwnerRegistryConflict(
                    "owner_registry_terminal_cancel_identity_or_generation_conflict"
                )
            if any(
                r.get("account_key") == target["account_key"]
                and r.get("order_date") == clean_date
                and r.get("original_order_no") == target_order_no
                and r.get("intent_id") != cancel["intent_id"]
                and r.get("state")
                in {"INTENT_RESERVED", "INTENT_AMBIGUOUS", "ORDER_BOUND"}
                for r in state.values()
            ):
                raise OwnerRegistryConflict(
                    "owner_registry_terminal_cancel_other_pending"
                )
            total_canceled = target.get("canceled_qty", 0) + (
                confirmed_qty if previous is None else 0
            )
            if target["quantity"] != filled_qty + total_canceled:
                raise OwnerRegistryConflict(
                    "owner_registry_terminal_cancel_quantity_conflict"
                )
            if previous is not None:
                if (
                    not isinstance(previous, dict)
                    or previous.get("confirmed_qty") != confirmed_qty
                    or previous.get("filled_qty") != filled_qty
                    or previous != target.get("terminal_cancel_reconciliation")
                    or cancel.get("state") != "ORDER_TERMINAL"
                    or target.get("state") != "ORDER_TERMINAL"
                ):
                    raise OwnerRegistryConflict(
                        "owner_registry_terminal_cancel_saved_proof_conflict"
                    )
                return
            if cancel.get("state") != "ORDER_BOUND":
                raise OwnerRegistryConflict(
                    "owner_registry_terminal_cancel_unproved_child_state"
                )
            old_terminal = target.get("terminal_reconciliation")
            if old_terminal is not None and (
                old_terminal.get("filled_qty") != filled_qty
                or old_terminal.get("quantity") != target["quantity"]
            ):
                raise OwnerRegistryConflict(
                    "owner_registry_terminal_cancel_prior_terminal_conflict"
                )
            proof = {
                "schema": "order_owner_terminal_cancel_reconciliation_v1",
                "source_contract": (
                    "machine_adaptive_exit_buy_terminal_cancel_dated_current_v1"
                    if side == "BUY"
                    else "machine_adaptive_exit_terminal_cancel_dated_current_v1"
                ),
                "target_intent_id": target["intent_id"],
                "cancel_intent_id": cancel["intent_id"],
                "target_order_no": target_order_no,
                "cancel_order_no": cancel_order_no,
                "order_date": clean_date,
                "requested_qty": cancel["quantity"],
                "confirmed_qty": confirmed_qty,
                "filled_qty": filled_qty,
                "remaining_qty": 0,
                "target_event_hash": target_event_hash,
                "cancel_event_hash": cancel_event_hash,
                "receipt_sha256": receipt_sha256,
            }
            self._append_locked(
                events,
                {
                    "intent_id": target["intent_id"],
                    "account_key": target["account_key"],
                    "event": side + "_TERMINAL_CANCEL_RECONCILED",
                    "state": "ORDER_TERMINAL",
                    "filled_qty": filled_qty,
                    "canceled_qty": total_canceled,
                    "terminal_cancel_reconciliation": proof,
                    "terminal_reconciliation": old_terminal
                    or _terminal_proof(
                        target | {"filled_qty": filled_qty}, terminal_receipt_sha256
                    ),
                },
            )
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            lock.close()

    def record_terminal_reconciliation(self, **kwargs) -> None:
        self._record_terminal_reconciliation(side="SELL", **kwargs)

    def record_buy_terminal_reconciliation(self, **kwargs) -> None:
        self._record_terminal_reconciliation(side="BUY", **kwargs)

    def _record_terminal_reconciliation(
        self,
        *,
        side: str,
        context: OwnerOrderContext,
        symbol: str,
        order_quantity: int,
        order_date: date | str,
        broker_order_no: str,
        cumulative_filled_qty: int,
        receipt_sha256: str,
    ) -> None:
        """Attach side-specific dated/current evidence without replacing origin.

        The adaptive adapter is the producer; a WS terminal alone is not this
        proof. Validate against the current journal under its lock, including
        any intervening fill. Reobserving the same quantities preserves the
        first proof so downstream immutable terminal receipts stay stable.
        """
        context.validate()
        clean_date = _registry_order_date(order_date)
        if (
            side not in {"BUY", "SELL"}
            or context.owner_type not in {"widget_auto_trade", "episode"}
            or type(order_quantity) is not int
            or type(cumulative_filled_qty) is not int
            or not 0 <= cumulative_filled_qty <= order_quantity
            or order_quantity <= 0
            or not isinstance(receipt_sha256, str)
            or len(receipt_sha256) != 64
            or any(c not in "0123456789abcdef" for c in receipt_sha256)
        ):
            raise OwnerRegistryError("owner_registry_terminal_reconciliation_invalid")
        lock = self._locked()
        try:
            events = self._read_locked()
            current = self._assert_owner_from_state(
                self._state(events),
                context=context,
                order_date=clean_date,
                broker_order_no=broker_order_no,
            )
            if (
                current.get("state") != "ORDER_TERMINAL"
                or current.get("symbol") != _registry_symbol(symbol)
                or current.get("side") != side
                or current.get("action") != "NEW"
                or type(current.get("quantity")) is not int
                or type(current.get("filled_qty")) is not int
                or current.get("quantity") != order_quantity
                or current.get("filled_qty") != cumulative_filled_qty
            ):
                raise OwnerRegistryConflict(
                    "owner_registry_terminal_reconciliation_identity_or_fill_conflict"
                )
            proof = _terminal_proof(current, receipt_sha256)
            previous = current.get("terminal_reconciliation")
            if "terminal_reconciliation" in current:
                if (
                    not isinstance(previous, dict)
                    or {k: v for k, v in previous.items() if k != "receipt_sha256"}
                    != {k: v for k, v in proof.items() if k != "receipt_sha256"}
                    or not isinstance(previous.get("receipt_sha256"), str)
                    or len(previous["receipt_sha256"]) != 64
                    or any(
                        c not in "0123456789abcdef" for c in previous["receipt_sha256"]
                    )
                ):
                    raise OwnerRegistryConflict(
                        "owner_registry_terminal_reconciliation_proof_conflict"
                    )
                return
            self._append_locked(
                events,
                {
                    "intent_id": current["intent_id"],
                    "account_key": current["account_key"],
                    "event": "TERMINAL_RECONCILIATION_RECORDED",
                    "terminal_reconciliation": proof,
                },
            )
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            lock.close()

    def position_intents(
        self, *, context: OwnerOrderContext, symbol: object
    ) -> list[dict[str, Any]]:
        """Read the complete account/position census, including unbound intents.

        Do not filter by date, route, state or owner: a conflicting owner or an
        old unresolved reservation must remain visible to terminal consumers.
        This is registry evidence, not a broker query or execution authority.
        """
        context.validate()
        clean_symbol = _registry_symbol(symbol)
        account_key = broker_account_key(require_explicit=True)
        lock = self._locked()
        try:
            return sorted(
                (
                    row
                    for row in self._state(self._read_locked()).values()
                    if row.get("account_key") == account_key
                    and row.get("position_id") == context.position_id
                    and row.get("symbol") == clean_symbol
                ),
                key=lambda row: row["intent_id"],
            )
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            lock.close()

    def owner_position_qty(self, position_id: str, *, symbol: object) -> int:
        clean_symbol = _registry_symbol(symbol)
        lock = self._locked()
        try:
            rows = self._state(self._read_locked()).values()
            account_key = broker_account_key()
            quantity = 0
            for row in rows:
                if (
                    row.get("account_key") != account_key
                    or row.get("symbol") != clean_symbol
                    or row.get("position_id") != position_id
                    or row.get("action") != "NEW"
                ):
                    continue
                filled = int(row.get("filled_qty") or 0)
                quantity += filled if row.get("side") == "BUY" else -filled
            if quantity < 0:
                raise OwnerRegistryConflict("owner_registry_position_qty_negative")
            return quantity
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            lock.close()

    def symbol_registered(self, symbol: object) -> bool:
        """Return whether this account/symbol ever entered shared custody.

        Registration is intentionally sticky. Once exact multi-owner custody
        has been used, a missing later exact-date policy must not silently
        restore aggregate symbol ownership inference.
        """

        clean_symbol = _registry_symbol(symbol)
        lock = self._locked()
        try:
            rows = [
                row
                for row in self._state(self._read_locked()).values()
                if row.get("symbol") == clean_symbol
            ]
            current_account = broker_account_key()
            if rows and not any(
                row.get("account_key") == current_account for row in rows
            ):
                raise OwnerRegistryConflict(
                    "owner_registry_account_identity_missing_or_mismatched"
                )
            return bool(rows)
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            lock.close()

    @staticmethod
    def _reconcile_symbol_quantity_from_state(
        state: dict[str, dict[str, Any]],
        *,
        account_key: str,
        symbol: str,
        broker_quantity: int,
    ) -> dict[str, Any]:
        by_position: dict[str, int] = {}
        for row in state.values():
            if (
                row.get("account_key") != account_key
                or row.get("symbol") != symbol
                or row.get("action") != "NEW"
            ):
                continue
            filled = int(row.get("filled_qty") or 0)
            delta = filled if row.get("side") == "BUY" else -filled
            position_id = str(row.get("position_id") or "")
            by_position[position_id] = by_position.get(position_id, 0) + delta
        if any(value < 0 for value in by_position.values()):
            raise OwnerRegistryConflict("owner_registry_owner_position_deficit")
        owned = sum(by_position.values())
        external = int(broker_quantity) - owned
        if external < 0:
            raise OwnerRegistryConflict("owner_registry_broker_quantity_deficit")
        return {
            "symbol": symbol,
            "broker_quantity": int(broker_quantity),
            "registered_owner_quantity": owned,
            "external_manual_remainder": external,
            "position_quantities": dict(sorted(by_position.items())),
            "balanced": True,
        }

    def reconcile_symbol_quantity(
        self, *, symbol: object, broker_quantity: int
    ) -> dict[str, Any]:
        clean_symbol = _registry_symbol(symbol)
        lock = self._locked()
        try:
            return self._reconcile_symbol_quantity_from_state(
                self._state(self._read_locked()),
                account_key=broker_account_key(),
                symbol=clean_symbol,
                broker_quantity=int(broker_quantity),
            )
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            lock.close()

    def unresolved_intent_summary(
        self,
        *,
        symbol: object,
        active_date: date | str,
    ) -> dict[str, Any]:
        """Describe same-date unbound intents without changing their state."""

        clean_symbol = _registry_symbol(symbol)
        clean_date = _registry_order_date(active_date)
        lock = self._locked()
        try:
            state = self._state(self._read_locked())
            account_key = broker_account_key(require_explicit=True)
            rows = [
                row
                for row in state.values()
                if row.get("account_key") == account_key
                and row.get("order_date") == clean_date
                and row.get("symbol") == clean_symbol
                and row.get("state") in _ACTIVE_UNBOUND_STATES
            ]
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            lock.close()
        return {
            "symbol": clean_symbol,
            "active_date": clean_date,
            "unresolved_intent_count": len(rows),
            "states": sorted({str(row.get("state") or "") for row in rows}),
            "sides": sorted({str(row.get("side") or "") for row in rows}),
        }

    def migration_receipt(
        self,
        *,
        symbol: object,
        broker_quantity: int,
        active_date: date | str,
        verified_exchanges: set[str] | frozenset[str] | tuple[str, ...],
        broker_open_order_nos: set[str] | frozenset[str] | tuple[str, ...],
        broker_snapshot_sha256: str,
    ) -> dict[str, Any]:
        clean_symbol = _registry_symbol(symbol)
        lock = self._locked()
        try:
            events = self._read_locked()
            state = self._state(events)
            account_key = broker_account_key(require_explicit=True)
            reconciliation = self._reconcile_symbol_quantity_from_state(
                state,
                account_key=account_key,
                symbol=clean_symbol,
                broker_quantity=int(broker_quantity),
            )
            tail_hash = str(events[-1].get("event_hash")) if events else "0" * 64
            clean_date = _registry_order_date(active_date)
            registered_open_order_nos = sorted(
                {
                    str(row.get("broker_order_no") or "").strip()
                    for row in state.values()
                    if row.get("account_key") == account_key
                    and row.get("order_date") == clean_date
                    and row.get("symbol") == reconciliation["symbol"]
                    and row.get("action") == "NEW"
                    and row.get("state") == "ORDER_BOUND"
                    and int(row.get("filled_qty") or 0) < int(row.get("quantity") or 0)
                    and str(row.get("broker_order_no") or "").strip()
                }
            )
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            lock.close()
        normalized_exchanges = sorted(
            {str(item or "").strip().upper() for item in verified_exchanges}
        )
        if not {"KRX", "NXT"}.issubset(normalized_exchanges):
            raise OwnerRegistryConflict(
                "owner_registry_migration_all_venues_not_verified"
            )
        normalized_broker_orders = sorted(
            {
                str(item or "").strip()
                for item in broker_open_order_nos
                if str(item or "").strip()
            }
        )
        if any(
            not (order_no.isdigit() and len(order_no) == 7)
            for order_no in normalized_broker_orders
        ):
            raise OwnerRegistryConflict("owner_registry_migration_order_no_invalid")
        if normalized_broker_orders != registered_open_order_nos:
            raise OwnerRegistryConflict(
                "owner_registry_migration_open_order_set_mismatch"
            )
        snapshot_hash = str(broker_snapshot_sha256 or "").strip().lower()
        if len(snapshot_hash) != 64 or any(
            ch not in "0123456789abcdef" for ch in snapshot_hash
        ):
            raise OwnerRegistryConflict(
                "owner_registry_migration_broker_snapshot_hash_invalid"
            )
        return {
            "schema": "owner_custody_migration_receipt_v1",
            "symbol": reconciliation["symbol"],
            "active_date": clean_date,
            "broker_account_key": account_key,
            "broker_quantity": reconciliation["broker_quantity"],
            "registered_owner_quantity": reconciliation["registered_owner_quantity"],
            "external_manual_remainder": reconciliation["external_manual_remainder"],
            "registry_tail_hash": tail_hash,
            "verified_exchanges": normalized_exchanges,
            "broker_open_order_nos": normalized_broker_orders,
            "registered_open_order_nos": registered_open_order_nos,
            "broker_snapshot_sha256": snapshot_hash,
            "validated": True,
        }

    def activate_policy_entry(
        self,
        *,
        active_date: date | str,
        policy_id: str,
        symbol: object,
        mode: str,
        allowed_owners: tuple[str, ...] | list[str] | set[str],
        migration_receipt: dict[str, Any],
        entry_authority_hash: str,
    ) -> dict[str, Any]:
        """Bind one exact policy entry to the current reconciled registry tail.

        Activation is the serialization point between migration/reconciliation
        and policy publication.  A receipt built from an ancestor registry tail
        cannot activate after any intervening journal mutation.
        """

        clean_date = _registry_order_date(active_date)
        clean_symbol = _registry_symbol(symbol)
        clean_policy_id = str(policy_id or "").strip()
        clean_mode = str(mode or "").strip().upper()
        clean_owners = tuple(
            sorted({str(owner or "").strip().lower() for owner in allowed_owners})
        )
        clean_entry_hash = str(entry_authority_hash or "").strip().lower()
        if (
            not clean_policy_id
            or len(clean_policy_id) > 240
            or any(ch in clean_policy_id for ch in "\r\n\t")
            or clean_mode not in {"COEXIST_ENTRY_ENABLED", "COEXIST_EXIT_ONLY"}
            or "main_scalping" not in clean_owners
            or not {"widget_auto_trade", "episode"}.intersection(clean_owners)
        ):
            raise OwnerRegistryError("owner_registry_policy_activation_input_invalid")
        if len(clean_entry_hash) != 64 or any(
            ch not in "0123456789abcdef" for ch in clean_entry_hash
        ):
            raise OwnerRegistryError(
                "owner_registry_policy_activation_entry_hash_invalid"
            )
        if not isinstance(migration_receipt, dict):
            raise OwnerRegistryError(
                "owner_registry_policy_activation_migration_receipt_invalid"
            )

        account_key = broker_account_key(require_explicit=True)
        migration_tail = (
            str(migration_receipt.get("registry_tail_hash") or "").strip().lower()
        )
        snapshot_hash = (
            str(migration_receipt.get("broker_snapshot_sha256") or "").strip().lower()
        )
        broker_orders = sorted(
            {
                str(value or "").strip()
                for value in migration_receipt.get("broker_open_order_nos", [])
            }
        )
        registered_orders = sorted(
            {
                str(value or "").strip()
                for value in migration_receipt.get("registered_open_order_nos", [])
            }
        )
        if (
            migration_receipt.get("schema") != "owner_custody_migration_receipt_v1"
            or migration_receipt.get("validated") is not True
            or migration_receipt.get("active_date") != clean_date
            or migration_receipt.get("symbol") != clean_symbol
            or migration_receipt.get("broker_account_key") != account_key
            or len(migration_tail) != 64
            or any(ch not in "0123456789abcdef" for ch in migration_tail)
            or len(snapshot_hash) != 64
            or any(ch not in "0123456789abcdef" for ch in snapshot_hash)
            or broker_orders != registered_orders
            or any(
                not (order_no.isdigit() and len(order_no) == 7)
                for order_no in broker_orders
            )
            or not {"KRX", "NXT"}.issubset(
                {
                    str(value or "").strip().upper()
                    for value in migration_receipt.get("verified_exchanges", [])
                }
            )
        ):
            raise OwnerRegistryError(
                "owner_registry_policy_activation_migration_receipt_invalid"
            )

        lock = self._locked()
        try:
            events = self._read_locked()
            state = self._state(events)
            existing = [
                row
                for row in events
                if row.get("event") == "POLICY_ACTIVATED"
                and row.get("account_key") == account_key
                and row.get("order_date") == clean_date
                and row.get("symbol") == clean_symbol
            ]
            exact = [
                row
                for row in existing
                if row.get("policy_id") == clean_policy_id
                and row.get("mode") == clean_mode
                and tuple(row.get("allowed_owners") or ()) == clean_owners
                and row.get("migration_registry_tail_hash") == migration_tail
                and row.get("broker_snapshot_sha256") == snapshot_hash
                and row.get("entry_authority_hash") == clean_entry_hash
            ]
            if len(exact) == 1 and len(existing) == 1:
                activation = exact[0]
                return {
                    "schema": ACTIVATION_SCHEMA,
                    "active_date": clean_date,
                    "policy_id": clean_policy_id,
                    "symbol": clean_symbol,
                    "broker_account_key": account_key,
                    "migration_registry_tail_hash": migration_tail,
                    "broker_snapshot_sha256": snapshot_hash,
                    "entry_authority_hash": clean_entry_hash,
                    "activation_event_hash": activation["event_hash"],
                }
            if existing:
                raise OwnerRegistryConflict("owner_registry_policy_activation_conflict")

            current_tail = str(events[-1].get("event_hash")) if events else "0" * 64
            if current_tail != migration_tail:
                raise OwnerRegistryConflict(
                    "owner_registry_policy_activation_stale_migration_tail"
                )
            reconciliation = self._reconcile_symbol_quantity_from_state(
                state,
                account_key=account_key,
                symbol=clean_symbol,
                broker_quantity=int(migration_receipt.get("broker_quantity")),
            )
            if reconciliation["registered_owner_quantity"] != int(
                migration_receipt.get("registered_owner_quantity")
            ) or reconciliation["external_manual_remainder"] != int(
                migration_receipt.get("external_manual_remainder")
            ):
                raise OwnerRegistryConflict(
                    "owner_registry_policy_activation_quantity_drift"
                )
            current_open_orders = sorted(
                {
                    str(row.get("broker_order_no") or "").strip()
                    for row in state.values()
                    if row.get("account_key") == account_key
                    and row.get("order_date") == clean_date
                    and row.get("symbol") == clean_symbol
                    and row.get("action") == "NEW"
                    and row.get("state") == "ORDER_BOUND"
                    and int(row.get("filled_qty") or 0) < int(row.get("quantity") or 0)
                    and str(row.get("broker_order_no") or "").strip()
                }
            )
            if current_open_orders != registered_orders:
                raise OwnerRegistryConflict(
                    "owner_registry_policy_activation_open_order_drift"
                )
            activation = self._append_locked(
                events,
                {
                    "event": "POLICY_ACTIVATED",
                    "state": "POLICY_ACTIVE",
                    "intent_id": (
                        f"policy-activation:{clean_date}:{clean_symbol}:"
                        f"{clean_policy_id}"
                    ),
                    "account_key": account_key,
                    "order_date": clean_date,
                    "symbol": clean_symbol,
                    "side": "",
                    "action": "POLICY_ACTIVATION",
                    "quantity": 0,
                    "route": "ALL",
                    "original_order_no": "",
                    "owner_type": "manual_operator",
                    "owner_id": "manual_operator:preopen_policy_apply",
                    "position_id": (
                        f"policy:{clean_date}:{clean_symbol}:{clean_policy_id}"
                    ),
                    "client_intent_id": (
                        f"policy-activation:{clean_date}:{clean_symbol}:"
                        f"{clean_policy_id}"
                    ),
                    "policy_id": clean_policy_id,
                    "mode": clean_mode,
                    "allowed_owners": list(clean_owners),
                    "migration_registry_tail_hash": migration_tail,
                    "broker_snapshot_sha256": snapshot_hash,
                    "entry_authority_hash": clean_entry_hash,
                    "migration_receipt": dict(migration_receipt),
                },
            )
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            lock.close()
        return {
            "schema": ACTIVATION_SCHEMA,
            "active_date": clean_date,
            "policy_id": clean_policy_id,
            "symbol": clean_symbol,
            "broker_account_key": account_key,
            "migration_registry_tail_hash": migration_tail,
            "broker_snapshot_sha256": snapshot_hash,
            "entry_authority_hash": clean_entry_hash,
            "activation_event_hash": activation["event_hash"],
        }

    def policy_activation_record(
        self,
        *,
        active_date: date | str,
        policy_id: str,
        symbol: object,
    ) -> dict[str, Any] | None:
        """Return the unique activation used to resume an interrupted publish."""

        clean_date = _registry_order_date(active_date)
        clean_symbol = _registry_symbol(symbol)
        clean_policy_id = str(policy_id or "").strip()
        lock = self._locked()
        try:
            matches = [
                row
                for row in self._read_locked()
                if row.get("event") == "POLICY_ACTIVATED"
                and row.get("state") == "POLICY_ACTIVE"
                and row.get("account_key") == broker_account_key(require_explicit=True)
                and row.get("order_date") == clean_date
                and row.get("symbol") == clean_symbol
                and row.get("policy_id") == clean_policy_id
            ]
            if len(matches) > 1:
                raise OwnerRegistryConflict(
                    "owner_registry_policy_activation_ambiguous"
                )
            return dict(matches[0]) if matches else None
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            lock.close()

    def policy_activation_matches(
        self,
        *,
        activation_event_hash: str,
        active_date: date | str,
        policy_id: str,
        symbol: object,
        mode: str,
        allowed_owners: tuple[str, ...] | list[str] | set[str],
        migration_registry_tail_hash: str,
        broker_snapshot_sha256: str,
        entry_authority_hash: str,
    ) -> bool:
        """Verify that runtime authority is the exact immutable activation."""

        clean_symbol = _registry_symbol(symbol)
        clean_date = _registry_order_date(active_date)
        expected_hash = str(activation_event_hash or "").strip().lower()
        expected_owners = tuple(
            sorted({str(owner or "").strip().lower() for owner in allowed_owners})
        )
        if len(expected_hash) != 64:
            return False
        lock = self._locked()
        try:
            matches = [
                row
                for row in self._read_locked()
                if str(row.get("event_hash") or "").strip().lower() == expected_hash
            ]
            if len(matches) != 1:
                return False
            row = matches[0]
            return bool(
                row.get("event") == "POLICY_ACTIVATED"
                and row.get("state") == "POLICY_ACTIVE"
                and row.get("account_key") == broker_account_key(require_explicit=True)
                and row.get("order_date") == clean_date
                and row.get("symbol") == clean_symbol
                and row.get("policy_id") == str(policy_id or "").strip()
                and row.get("mode") == str(mode or "").strip().upper()
                and tuple(row.get("allowed_owners") or ()) == expected_owners
                and row.get("migration_registry_tail_hash")
                == str(migration_registry_tail_hash or "").strip().lower()
                and row.get("broker_snapshot_sha256")
                == str(broker_snapshot_sha256 or "").strip().lower()
                and row.get("entry_authority_hash")
                == str(entry_authority_hash or "").strip().lower()
            )
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            lock.close()

    def decision_activation_matches(self, decision: Any) -> bool:
        """Verify a resolved coexistence decision without duplicating fields."""

        if not bool(getattr(decision, "coexistence_enabled", False)):
            return False
        return self.policy_activation_matches(
            activation_event_hash=getattr(decision, "activation_event_hash", ""),
            active_date=getattr(decision, "target_date", ""),
            policy_id=getattr(decision, "policy_id", ""),
            symbol=getattr(decision, "symbol", ""),
            mode=getattr(decision, "mode", ""),
            allowed_owners=getattr(decision, "allowed_owners", ()),
            migration_registry_tail_hash=getattr(
                decision, "migration_registry_tail_hash", ""
            ),
            broker_snapshot_sha256=getattr(decision, "broker_snapshot_sha256", ""),
            entry_authority_hash=getattr(decision, "entry_authority_hash", ""),
        )

    def contains_event_hash(self, event_hash: str) -> bool:
        expected = str(event_hash or "").strip().lower()
        lock = self._locked()
        try:
            events = self._read_locked()
            if expected == "0" * 64:
                # The all-zero digest is the immutable genesis anchor and
                # remains an ancestor after later append-only events.
                return True
            return any(
                str(row.get("event_hash") or "").lower() == expected for row in events
            )
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            lock.close()


_DEFAULT_REGISTRY: OrderOwnerRegistry | None = None


def default_order_owner_registry() -> OrderOwnerRegistry:
    global _DEFAULT_REGISTRY
    expected = registry_path()
    if _DEFAULT_REGISTRY is None or _DEFAULT_REGISTRY.path != expected:
        _DEFAULT_REGISTRY = OrderOwnerRegistry(expected)
    return _DEFAULT_REGISTRY
