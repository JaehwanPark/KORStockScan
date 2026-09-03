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
        if clean_action not in {"NEW", "CANCEL"} or int(quantity) < 0:
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
            if clean_action == "CANCEL":
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
                if int(original.get("filled_qty") or 0) >= int(
                    original.get("quantity") or 0
                ):
                    raise OwnerRegistryConflict(
                        "owner_registry_cancel_original_no_remaining_quantity"
                    )
                duplicate_cancel = [
                    row
                    for row in state.values()
                    if row.get("account_key") == broker_account_key()
                    and row.get("order_date") == clean_date
                    and row.get("action") == "CANCEL"
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
                            open_sell_commitment += max(
                                0, int(row.get("quantity") or 0) - filled
                            )
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
                        open_sell_commitment += max(
                            0, int(row.get("quantity") or 0) - filled
                        )
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
            if filled == prior_qty and amount == prior_amount:
                return
            if filled > int(current.get("quantity") or 0):
                raise OwnerRegistryConflict("owner_registry_overfill")
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
        migration_tail = str(
            migration_receipt.get("registry_tail_hash") or ""
        ).strip().lower()
        snapshot_hash = str(
            migration_receipt.get("broker_snapshot_sha256") or ""
        ).strip().lower()
        broker_orders = sorted(
            {str(value or "").strip() for value in migration_receipt.get(
                "broker_open_order_nos", []
            )}
        )
        registered_orders = sorted(
            {str(value or "").strip() for value in migration_receipt.get(
                "registered_open_order_nos", []
            )}
        )
        if (
            migration_receipt.get("schema")
            != "owner_custody_migration_receipt_v1"
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
                raise OwnerRegistryConflict(
                    "owner_registry_policy_activation_conflict"
                )

            current_tail = (
                str(events[-1].get("event_hash")) if events else "0" * 64
            )
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
            if (
                reconciliation["registered_owner_quantity"]
                != int(migration_receipt.get("registered_owner_quantity"))
                or reconciliation["external_manual_remainder"]
                != int(migration_receipt.get("external_manual_remainder"))
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
                    and int(row.get("filled_qty") or 0)
                    < int(row.get("quantity") or 0)
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
                and row.get("account_key")
                == broker_account_key(require_explicit=True)
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
                and row.get("account_key")
                == broker_account_key(require_explicit=True)
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
            broker_snapshot_sha256=getattr(
                decision, "broker_snapshot_sha256", ""
            ),
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
