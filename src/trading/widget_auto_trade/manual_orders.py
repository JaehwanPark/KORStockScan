"""Operator-confirmed Samsung widget orders with persistent idempotency.

This owner uses only the existing shared Kiwoom token gateway.  It does not
issue tokens, query an account or orderable cash, infer a quantity, or control
the main bot.  Every request is an explicit Windows-widget operator action.
"""

from __future__ import annotations

import fcntl
import json
import logging
import os
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from src.engine.monitoring.samsung_widget_contract import KST, SAMSUNG_CODE
from src.trading.order.tick_utils import clamp_price_to_tick, move_price_down_by_bps
from src.trading.widget_auto_trade.gateway import (
    KiwoomSharedTokenOrderGateway,
    SubmitResult,
    resolve_widget_broker_route,
)
from src.utils.constants import PROJECT_ROOT

MANUAL_ORDER_AUTHORITY = "operator_widget_manual_order_v1"
STATE_SCHEMA_VERSION = 1
DEFAULT_STATE_PATH = PROJECT_ROOT / "data/runtime/samsung_widget_manual_orders.json"
DEFAULT_EVENT_DIR = PROJECT_ROOT / "data/report/samsung_widget_manual_order_events"
MAX_ORDER_QTY_ENV = "KORSTOCKSCAN_SAMSUNG_WIDGET_MANUAL_MAX_QTY"
DEFAULT_MAX_ORDER_QTY = 100
BUY_DISCOUNT_BPS = 50
ACTIVE_SESSIONS = frozenset({"NXT_PREMARKET", "KRX_REGULAR", "NXT_AFTERMARKET"})
LOGGER = logging.getLogger(__name__)


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, sort_keys=True, indent=2)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _load_state(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except (OSError, ValueError) as exc:
        raise RuntimeError("manual_order_state_unreadable") from exc
    return payload if isinstance(payload, dict) else {}


def _request_id(value: object) -> str:
    text = str(value or "").strip()
    try:
        parsed = UUID(text)
    except (ValueError, AttributeError) as exc:
        raise ValueError("invalid_client_request_id") from exc
    return str(parsed)


def _quantity(value: object, *, maximum: int) -> int:
    if isinstance(value, bool):
        raise ValueError("invalid_order_quantity")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid_order_quantity") from exc
    if parsed <= 0 or parsed > maximum:
        raise ValueError("invalid_order_quantity")
    return parsed


def _positive_price(value: object) -> int:
    if isinstance(value, bool):
        raise ValueError("invalid_reference_price")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid_reference_price") from exc
    if parsed <= 0:
        raise ValueError("invalid_reference_price")
    return parsed


def _result_payload(result: SubmitResult) -> dict[str, Any]:
    return asdict(result)


class ManualWidgetOrderExecutor:
    """Submit one explicit operator request and make retries idempotent."""

    def __init__(
        self,
        *,
        gateway: KiwoomSharedTokenOrderGateway | None = None,
        state_path: Path = DEFAULT_STATE_PATH,
        event_dir: Path = DEFAULT_EVENT_DIR,
        max_order_qty: int | None = None,
    ) -> None:
        self.gateway = gateway or KiwoomSharedTokenOrderGateway()
        self.state_path = state_path
        self.lock_path = state_path.with_suffix(".lock")
        self.event_dir = event_dir
        configured_max = max_order_qty
        if configured_max is None:
            try:
                configured_max = int(
                    os.getenv(MAX_ORDER_QTY_ENV, str(DEFAULT_MAX_ORDER_QTY))
                )
            except ValueError:
                configured_max = DEFAULT_MAX_ORDER_QTY
        self.max_order_qty = max(1, min(10_000, int(configured_max)))

    def _locked_state(self):
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        handle = self.lock_path.open("a+", encoding="utf-8")
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        return handle

    @staticmethod
    def _duplicate_response(
        *, request_id: str, existing: dict[str, Any]
    ) -> dict[str, Any]:
        response = existing.get("response")
        if isinstance(response, dict):
            duplicate = dict(response)
            duplicate["duplicate_request"] = True
            return duplicate
        existing_intent = existing.get("intent")
        if not isinstance(existing_intent, dict):
            existing_intent = {}
        return {
            "status": "ambiguous",
            "reason": "duplicate_request_still_submitting",
            "client_request_id": request_id,
            "symbol": SAMSUNG_CODE,
            "side": str(existing_intent.get("side") or ""),
            "quantity": int(existing_intent.get("quantity") or 0),
            "orders": [],
            "expected_order_count": 0,
            "accepted_order_count": 0,
            "authority": MANUAL_ORDER_AUTHORITY,
            "actual_order_submitted": None,
            "duplicate_request": True,
        }

    def existing_response(
        self, *, client_request_id: object, now: datetime
    ) -> dict[str, Any] | None:
        """Resolve a retry before applying mutable quote/session validations."""
        clean_request_id = _request_id(client_request_id)
        trade_date = now.astimezone(KST).date().isoformat()
        handle = self._locked_state()
        try:
            state = _load_state(self.state_path)
            if state.get("trade_date") != trade_date:
                return None
            existing = state.get("requests", {}).get(clean_request_id)
            if not isinstance(existing, dict):
                return None
            return self._duplicate_response(
                request_id=clean_request_id,
                existing=existing,
            )
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            handle.close()

    def _reserve(
        self,
        *,
        request_id: str,
        trade_date: str,
        intent: dict[str, Any],
    ) -> dict[str, Any] | None:
        handle = self._locked_state()
        try:
            state = _load_state(self.state_path)
            if state.get("trade_date") != trade_date:
                state = {
                    "schema_version": STATE_SCHEMA_VERSION,
                    "trade_date": trade_date,
                    "requests": {},
                }
            requests = state.setdefault("requests", {})
            existing = requests.get(request_id)
            if isinstance(existing, dict):
                return self._duplicate_response(
                    request_id=request_id,
                    existing=existing,
                )
            requests[request_id] = {
                "status": "SUBMITTING",
                "reserved_at": datetime.now(KST).isoformat(),
                "intent": intent,
            }
            _atomic_write(self.state_path, state)
            return None
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            handle.close()

    def _finalize(
        self,
        *,
        request_id: str,
        trade_date: str,
        response: dict[str, Any],
    ) -> None:
        handle = self._locked_state()
        try:
            state = _load_state(self.state_path)
            if state.get("trade_date") != trade_date:
                state = {
                    "schema_version": STATE_SCHEMA_VERSION,
                    "trade_date": trade_date,
                    "requests": {},
                }
            record = state.setdefault("requests", {}).setdefault(request_id, {})
            record["status"] = str(response.get("status") or "unknown").upper()
            record["finalized_at"] = datetime.now(KST).isoformat()
            record["response"] = response
            _atomic_write(self.state_path, state)
            try:
                self.event_dir.mkdir(parents=True, exist_ok=True)
                event_path = self.event_dir / f"manual_orders_{trade_date}.jsonl"
                with event_path.open("a", encoding="utf-8") as event_handle:
                    event_handle.write(json.dumps(response, ensure_ascii=False) + "\n")
                    event_handle.flush()
                    os.fsync(event_handle.fileno())
            except OSError:
                LOGGER.exception("manual widget order event append failed")
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            handle.close()

    def execute(
        self,
        *,
        side: object,
        quantity: object,
        client_request_id: object,
        reference_price: object,
        market_venue: object,
        session: object,
        snapshot_observed_at: str,
        now: datetime,
    ) -> dict[str, Any]:
        clean_side = str(side or "").strip().upper()
        if clean_side not in {"BUY", "SELL"}:
            raise ValueError("invalid_order_side")
        clean_quantity = _quantity(quantity, maximum=self.max_order_qty)
        clean_request_id = _request_id(client_request_id)
        clean_price = _positive_price(reference_price)
        clean_session = str(session or "").strip().upper()
        clean_venue = str(market_venue or "").strip().upper()
        if clean_session not in ACTIVE_SESSIONS:
            raise ValueError("inactive_market_session")
        expected_venue = "KRX" if clean_session == "KRX_REGULAR" else "NXT"
        if clean_venue != expected_venue:
            raise ValueError("market_venue_session_mismatch")
        route = resolve_widget_broker_route(clean_venue)
        trade_date = now.astimezone(KST).date().isoformat()
        normalized_price = clamp_price_to_tick(clean_price)
        intent = {
            "side": clean_side,
            "quantity": clean_quantity,
            "reference_price": clean_price,
            "normalized_price": normalized_price,
            "market_venue": clean_venue,
            "broker_route": route,
            "session": clean_session,
            "snapshot_observed_at": snapshot_observed_at,
        }
        duplicate = self._reserve(
            request_id=clean_request_id,
            trade_date=trade_date,
            intent=intent,
        )
        if duplicate is not None:
            return duplicate

        submitted_at = datetime.now(KST).isoformat()
        base = {
            "client_request_id": clean_request_id,
            "symbol": SAMSUNG_CODE,
            "side": clean_side,
            "quantity": clean_quantity,
            "reference_price": clean_price,
            "market_venue": clean_venue,
            "broker_route": route,
            "session": clean_session,
            "snapshot_observed_at": snapshot_observed_at,
            "submitted_at": submitted_at,
            "authority": MANUAL_ORDER_AUTHORITY,
            "runtime_effect": True,
            "broker_order_forbidden": False,
            "token_mode": "shared_cache_only",
            "account_precheck": False,
            "orderable_cash_precheck": False,
        }
        try:
            if clean_side == "BUY":
                response = self._submit_buy(
                    base=base,
                    quantity=clean_quantity,
                    price=normalized_price,
                    route=route,
                )
            else:
                response = self._submit_sell(
                    base=base,
                    quantity=clean_quantity,
                    price=normalized_price,
                    route=route,
                    session=clean_session,
                )
        except Exception as exc:
            response = {
                **base,
                "status": "ambiguous",
                "reason": f"broker_transport_{type(exc).__name__}",
                "orders": [],
                "actual_order_submitted": None,
            }
        self._finalize(
            request_id=clean_request_id,
            trade_date=trade_date,
            response=response,
        )
        return response

    def _submit_buy(
        self, *, base: dict[str, Any], quantity: int, price: int, route: str
    ) -> dict[str, Any]:
        upper_qty = (quantity + 1) // 2
        lower_qty = quantity // 2
        legs = [("CURRENT", upper_qty, price)]
        if lower_qty:
            legs.append(
                (
                    "MINUS_0P5_PCT",
                    lower_qty,
                    move_price_down_by_bps(price, BUY_DISCOUNT_BPS),
                )
            )
        orders: list[dict[str, Any]] = []
        for role, leg_qty, leg_price in legs:
            try:
                result = self.gateway.submit_limit_buy(
                    code=SAMSUNG_CODE,
                    qty=leg_qty,
                    route=route,
                    price=leg_price,
                )
            except Exception as exc:
                orders.append(
                    {
                        "role": role,
                        "quantity": leg_qty,
                        "price": leg_price,
                        "order_type": "LIMIT",
                        "accepted": False,
                        "order_no": "",
                        "return_code": "TRANSPORT_AMBIGUOUS",
                        "return_msg": type(exc).__name__,
                        "ambiguous": True,
                    }
                )
                break
            orders.append(
                {
                    "role": role,
                    "quantity": leg_qty,
                    "price": leg_price,
                    "order_type": "LIMIT",
                    **_result_payload(result),
                }
            )
            if not result.accepted:
                break
        accepted_count = sum(1 for order in orders if order["accepted"])
        ambiguous_count = sum(1 for order in orders if order.get("ambiguous"))
        expected_count = len(legs)
        if ambiguous_count:
            status = "ambiguous"
        elif accepted_count == expected_count:
            status = "accepted"
        elif accepted_count:
            status = "partial"
        else:
            status = "rejected"
        return {
            **base,
            "status": status,
            "orders": orders,
            "expected_order_count": expected_count,
            "accepted_order_count": accepted_count,
            "actual_order_submitted": (
                True if accepted_count else None if ambiguous_count else False
            ),
        }

    def _submit_sell(
        self,
        *,
        base: dict[str, Any],
        quantity: int,
        price: int,
        route: str,
        session: str,
    ) -> dict[str, Any]:
        if session == "KRX_REGULAR":
            result = self.gateway.submit_sell(
                code=SAMSUNG_CODE,
                qty=quantity,
                route=route,
            )
            order_type = "MARKET"
            order_price = None
        else:
            result = self.gateway.submit_limit_sell(
                code=SAMSUNG_CODE,
                qty=quantity,
                route=route,
                price=price,
            )
            order_type = "LIMIT"
            order_price = price
        order = {
            "role": "MANUAL_SELL",
            "quantity": quantity,
            "price": order_price,
            "order_type": order_type,
            **_result_payload(result),
        }
        status = (
            "ambiguous"
            if result.ambiguous
            else "accepted" if result.accepted else "rejected"
        )
        return {
            **base,
            "status": status,
            "orders": [order],
            "expected_order_count": 1,
            "accepted_order_count": int(result.accepted),
            "actual_order_submitted": None if result.ambiguous else result.accepted,
        }
