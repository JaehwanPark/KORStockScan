"""Daily-reset live execution state machine for widget advisory signals."""

from __future__ import annotations

import json
import os
import time
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Protocol

from src.engine.monitoring import doosan_widget_contract as doosan_contract
from src.engine.monitoring import hanwha_ocean_widget_contract as hanwha_contract
from src.engine.monitoring import samsung_widget_contract as samsung_contract
from src.engine.monitoring.samsung_widget_contract import KST
from src.engine.risk.manual_control_exclusion import (
    evaluate_manual_control_exclusion,
    manual_control_operator_exclusion_source,
)
from src.engine.trade_pause_control import is_buy_side_paused
from src.trading.order.tick_utils import get_tick_size
from src.trading.widget_auto_trade.gateway import (
    ExecutionSnapshot,
    KiwoomSharedTokenOrderGateway,
    SubmitResult,
)
from src.utils.constants import PROJECT_ROOT

EXECUTION_AUTHORITY = "operator_directed_widget_auto_trade_v1"
STATE_SCHEMA_VERSION = 1
DEFAULT_STATE_PATH = PROJECT_ROOT / "data/runtime/widget_signal_auto_trade_state.json"
DEFAULT_EVENT_DIR = PROJECT_ROOT / "data/report/widget_signal_auto_trade_events"
ACTIONABLE_ENTRY_STATES = frozenset({"ENTRY_CAUTION", "ENTRY_READY"})
FINAL_EXIT_STATE = "EXIT_READY"
ACTIVE_ORDER_STATUSES = frozenset(
    {
        "SUBMITTING",
        "SUBMITTED",
        "AMBIGUOUS",
        "CANCEL_REQUESTED",
        "CANCEL_AMBIGUOUS",
        "CANCEL_FAILED_TERMINAL",
    }
)
MAX_ENTRY_QTY = 100
MAX_CANCEL_ATTEMPTS = 3
MAX_SELL_ATTEMPTS = 3
SELL_RETRY_SEC = 5
TAKE_PROFIT_BPS = 100
MAX_TAKE_PROFIT_FAILURES = 3
OBSERVABILITY_PERSIST_INTERVAL_SEC = 60

ORDER_ROLE_ENTRY_BUY = "ENTRY_BUY"
ORDER_ROLE_TAKE_PROFIT = "TAKE_PROFIT_SELL"
ORDER_ROLE_FINAL_EXIT = "FINAL_EXIT_SELL"

EXECUTION_CONTRACT = {
    "metric_role": "execution_quality_real_only",
    "decision_authority": EXECUTION_AUTHORITY,
    "window_policy": "trade_date_only_reset_without_overnight_management",
    "sample_floor": "one_source_qualified_unique_widget_entry_signal",
    "primary_decision_metric": "broker_filled_widget_owned_quantity",
    "source_quality_gate": (
        "fresh_contract_valid_widget_snapshot_and_unique_signal;"
        "shared_cached_token_only;exact_order_number_fill_reconciliation"
    ),
    "forbidden_uses": [
        "sell_prior_day_widget_quantity",
        "sell_manual_or_other_strategy_quantity",
        "token_issue_or_refresh",
        "orderable_cash_precheck",
        "non_take_profit_non_final_exit_submission",
        "source_signal_threshold_mutation",
        "main_bot_process_control",
    ],
}


class OrderGateway(Protocol):
    def submit_buy(self, *, code: str, qty: int, route: str) -> SubmitResult: ...

    def submit_sell(self, *, code: str, qty: int, route: str) -> SubmitResult: ...

    def submit_limit_sell(
        self, *, code: str, qty: int, route: str, price: int
    ) -> SubmitResult: ...

    def cancel(
        self, *, code: str, order_no: str, qty: int, route: str
    ) -> SubmitResult: ...

    def execution_snapshot(
        self,
        *,
        code: str,
        order_no: str,
        route: str,
        order_date: str,
    ) -> ExecutionSnapshot: ...


@dataclass(frozen=True)
class WidgetSpec:
    code: str
    name: str
    snapshot_path: Path
    contract: Any
    event_based: bool


DEFAULT_WIDGET_SPECS = (
    WidgetSpec(
        samsung_contract.SAMSUNG_CODE,
        samsung_contract.SAMSUNG_NAME,
        samsung_contract.DEFAULT_SNAPSHOT_PATH,
        samsung_contract,
        False,
    ),
    WidgetSpec(
        doosan_contract.DOOSAN_CODE,
        doosan_contract.DOOSAN_NAME,
        doosan_contract.DEFAULT_SNAPSHOT_PATH,
        doosan_contract,
        True,
    ),
    WidgetSpec(
        hanwha_contract.HANWHA_OCEAN_CODE,
        hanwha_contract.HANWHA_OCEAN_NAME,
        hanwha_contract.DEFAULT_SNAPSHOT_PATH,
        hanwha_contract,
        True,
    ),
)

SnapshotLoader = Callable[[Path], dict[str, Any]]


def _now_kst() -> datetime:
    return datetime.now(KST)


def _timestamp(value: object) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value or ""))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(KST)


def _positive_int(value: object) -> int:
    if isinstance(value, bool):
        return 0
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def _take_profit_price(fill_price: int, *, profit_bps: int = TAKE_PROFIT_BPS) -> int:
    """Return the first valid tick at or above the requested gross return."""
    clean_fill = _positive_int(fill_price)
    clean_bps = _positive_int(profit_bps)
    if clean_fill <= 0 or clean_bps <= 0:
        raise ValueError("invalid_take_profit_basis")
    raw_target = (clean_fill * (10_000 + clean_bps) + 9_999) // 10_000
    tick = get_tick_size(raw_target)
    return ((raw_target + tick - 1) // tick) * tick


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, sort_keys=True, indent=2)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)
    try:
        directory_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    except OSError:
        return
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)


class WidgetTradeEventRecorder:
    def __init__(self, output_dir: Path = DEFAULT_EVENT_DIR) -> None:
        self.output_dir = output_dir

    def record(self, event: dict[str, Any], observed_at: datetime) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        path = self.output_dir / (
            f"widget_signal_auto_trade_events_{observed_at.strftime('%Y%m%d')}.jsonl"
        )
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


class WidgetSignalAutoTrader:
    """Submit one configurable order per widget entry episode.

    Broker holdings are intentionally not used to calculate sell quantity.
    Only fills tied to this service's current-trade-date order numbers enter
    the sellable ledger.  At the date boundary any remaining quantity becomes
    unmanaged prior-day inventory and is never sold by the new date's state.
    """

    def __init__(
        self,
        *,
        gateway: OrderGateway | None = None,
        specs: tuple[WidgetSpec, ...] = DEFAULT_WIDGET_SPECS,
        state_path: Path = DEFAULT_STATE_PATH,
        event_recorder: WidgetTradeEventRecorder | None = None,
        snapshot_loader: SnapshotLoader = _load_json,
        entry_qty: int = 1,
        enabled: bool = False,
    ) -> None:
        qty = int(entry_qty)
        if qty < 1 or qty > MAX_ENTRY_QTY:
            raise ValueError(f"entry_qty must be between 1 and {MAX_ENTRY_QTY}")
        self.gateway = gateway or KiwoomSharedTokenOrderGateway()
        self.specs = specs
        self.state_path = state_path
        self.event_recorder = event_recorder or WidgetTradeEventRecorder()
        self.snapshot_loader = snapshot_loader
        self.entry_qty = qty
        self.enabled = bool(enabled)
        self._state = self._load_state()

    def _load_state(self) -> dict[str, Any]:
        state = _load_json(self.state_path)
        if (
            state.get("schema_version") != STATE_SCHEMA_VERSION
            or state.get("execution_authority") != EXECUTION_AUTHORITY
        ):
            return {}
        return state

    @staticmethod
    def _empty_symbol_state(spec: WidgetSpec) -> dict[str, Any]:
        return {
            "code": spec.code,
            "name": spec.name,
            "entry_episode_open": False,
            "entry_signal_id": None,
            "exit_signal_id": None,
            "exit_requested": False,
            "orders": [],
            "sell_attempt_count": 0,
            "last_sell_attempt_at": None,
            "take_profit_failure_count": 0,
            "last_take_profit_attempt_at": None,
            "last_source_state": None,
        }

    def _save(self) -> None:
        self._state.update(
            {
                "schema_version": STATE_SCHEMA_VERSION,
                "execution_authority": EXECUTION_AUTHORITY,
                "runtime_effect": self.enabled,
                "actual_order_submitted": any(
                    order.get("broker_accepted") is True
                    for symbol in (self._state.get("symbols") or {}).values()
                    for order in symbol.get("orders") or []
                ),
                "cash_precheck_performed": False,
                "token_mode": "shared_cache_only_no_issue_no_refresh",
                "entry_qty": self.entry_qty,
                "execution_contract": EXECUTION_CONTRACT,
            }
        )
        _atomic_write(self.state_path, self._state)

    @staticmethod
    def _filled_qty(symbol_state: dict[str, Any], side: str) -> int:
        return sum(
            _positive_int(order.get("filled_qty"))
            for order in symbol_state.get("orders") or []
            if order.get("side") == side and order.get("broker_accepted") is True
        )

    @classmethod
    def _open_qty(cls, symbol_state: dict[str, Any]) -> int:
        return max(
            0,
            cls._filled_qty(symbol_state, "BUY")
            - cls._filled_qty(symbol_state, "SELL"),
        )

    def _activate_date(self, observed_at: datetime) -> None:
        day = observed_at.date().isoformat()
        if self._state.get("active_date") == day:
            symbols = self._state.get("symbols")
            if not isinstance(symbols, dict):
                symbols = {}
                self._state["symbols"] = symbols
            changed = False
            for spec in self.specs:
                if spec.code not in symbols:
                    symbols[spec.code] = self._empty_symbol_state(spec)
                    changed = True
            if changed:
                self._save()
            return
        prior_symbols = self._state.get("symbols") or {}
        history = self._state.get("history")
        history = history if isinstance(history, list) else []
        prior_date = str(self._state.get("active_date") or "")
        if prior_date and isinstance(prior_symbols, dict):
            history.append(
                {
                    "trade_date": prior_date,
                    "reset_at": observed_at.isoformat(),
                    "symbols": {
                        code: {
                            "buy_filled_qty": self._filled_qty(value, "BUY"),
                            "sell_filled_qty": self._filled_qty(value, "SELL"),
                            "unmanaged_overnight_qty": self._open_qty(value),
                            "unresolved_order_count": sum(
                                1
                                for order in value.get("orders") or []
                                if order.get("status") in ACTIVE_ORDER_STATUSES
                            ),
                            "orders": deepcopy(value.get("orders") or []),
                        }
                        for code, value in prior_symbols.items()
                        if isinstance(value, dict)
                    },
                    "overnight_policy": "no_action_daily_reset",
                }
            )
        self._state = {
            "active_date": day,
            "symbols": {
                spec.code: self._empty_symbol_state(spec) for spec in self.specs
            },
            "history": history[-30:],
        }
        self._save()

    def _event(
        self, event_type: str, spec: WidgetSpec, now: datetime, **fields: Any
    ) -> None:
        payload = {
            "event_type": event_type,
            "observed_at": now.isoformat(),
            "trade_date": now.date().isoformat(),
            "symbol": spec.code,
            "name": spec.name,
            "execution_authority": EXECUTION_AUTHORITY,
            "runtime_effect": True,
            "actual_order_submitted": False,
            "broker_order_forbidden": False,
            "cash_precheck_performed": False,
            "token_mode": "shared_cache_only_no_issue_no_refresh",
            **EXECUTION_CONTRACT,
            **fields,
        }
        self.event_recorder.record(payload, now)

    def _record_entry_block_once(
        self,
        *,
        spec: WidgetSpec,
        symbol_state: dict[str, Any],
        signal_id: str,
        reason: str,
        now: datetime,
        **fields: Any,
    ) -> None:
        if (
            symbol_state.get("last_entry_block_signal_id") == signal_id
            and symbol_state.get("last_entry_block_reason") == reason
        ):
            return
        symbol_state["last_entry_block_signal_id"] = signal_id
        symbol_state["last_entry_block_reason"] = reason
        symbol_state["last_entry_block_at"] = now.isoformat()
        self._save()
        self._event(reason, spec, now, signal_id=signal_id, **fields)

    @staticmethod
    def _snapshot_time(payload: dict[str, Any]) -> datetime | None:
        return samsung_contract.snapshot_observed_at(payload)

    def _validated_context(
        self, spec: WidgetSpec, payload: dict[str, Any], now: datetime
    ) -> tuple[Any | None, datetime | None]:
        context = spec.contract.session_context(now)
        snapshot_at = self._snapshot_time(payload)
        expected_profile = str(getattr(spec.contract, "STRATEGY_PROFILE", "") or "")
        if (
            not context.active
            or snapshot_at is None
            or payload.get("status") != "ok"
            or payload.get("symbol") != spec.code
            or payload.get("market_venue") != context.market_venue
            or (
                expected_profile
                and str(payload.get("strategy_profile") or "") != expected_profile
            )
        ):
            return None, None
        fresh = spec.contract.snapshot_is_fresh(payload, now=now)
        return (context, snapshot_at) if fresh else (None, None)

    def _entry_signal(
        self,
        spec: WidgetSpec,
        payload: dict[str, Any],
        now: datetime,
    ) -> tuple[str, str] | None:
        context, snapshot_at = self._validated_context(spec, payload, now)
        if context is None or snapshot_at is None:
            return None
        advisory = payload.get("advisory")
        if not isinstance(advisory, dict):
            return None
        if spec.event_based:
            event = payload.get("entry_event")
            if not isinstance(
                event, dict
            ) or not spec.contract.advisory_event_contract_is_valid(
                event, expected_type="ENTRY", evaluated_at=now
            ):
                return None
            state = str(event.get("state") or "")
            event_id = str(event.get("event_id") or "")
            return (
                (event_id, state)
                if event_id and state in ACTIONABLE_ENTRY_STATES
                else None
            )
        if not spec.contract.advisory_contract_is_valid(
            advisory,
            snapshot_observed_at=snapshot_at,
            context=context,
            evaluated_at=now,
        ):
            return None
        state = str(advisory.get("state") or "")
        if state not in ACTIONABLE_ENTRY_STATES:
            return None
        return (
            f"{spec.code}:{now.date().isoformat()}:ENTRY:{context.name}:"
            f"{advisory.get('observed_at')}",
            state,
        )

    def _exit_signal(
        self,
        spec: WidgetSpec,
        payload: dict[str, Any],
        now: datetime,
    ) -> str | None:
        context, snapshot_at = self._validated_context(spec, payload, now)
        if context is None or snapshot_at is None:
            return None
        if spec.event_based:
            event = payload.get("exit_event")
            if not isinstance(
                event, dict
            ) or not spec.contract.advisory_event_contract_is_valid(
                event, expected_type="EXIT", evaluated_at=now
            ):
                return None
            return str(event.get("event_id") or "") or None
        exit_advisory = payload.get("exit_advisory")
        if (
            not isinstance(exit_advisory, dict)
            or exit_advisory.get("state") != FINAL_EXIT_STATE
            or not spec.contract.exit_advisory_contract_is_valid(
                exit_advisory,
                snapshot_observed_at=snapshot_at,
                context=context,
                evaluated_at=now,
            )
        ):
            return None
        continuity = exit_advisory.get("continuity")
        continuity = continuity if isinstance(continuity, dict) else {}
        return ":".join(
            [
                spec.code,
                now.date().isoformat(),
                "EXIT",
                context.name,
                str(continuity.get("ready_bar") or exit_advisory.get("observed_at")),
            ]
        )

    @staticmethod
    def _route(payload: dict[str, Any]) -> str:
        route = str(payload.get("market_venue") or "").upper()
        return route if route in {"KRX", "NXT"} else ""

    def _order_record(
        self,
        *,
        side: str,
        qty: int,
        route: str,
        signal_id: str,
        now: datetime,
        order_role: str,
        limit_price: int | None = None,
        parent_entry_signal_id: str | None = None,
    ) -> dict[str, Any]:
        return {
            "side": side,
            "requested_qty": qty,
            "filled_qty": 0,
            "remaining_qty": qty,
            "route": route,
            "signal_id": signal_id,
            "order_role": order_role,
            "limit_price": limit_price,
            "parent_entry_signal_id": parent_entry_signal_id,
            "order_date": now.date().isoformat(),
            "intent_created_at": now.isoformat(),
            "status": "SUBMITTING",
            "order_no": "",
            "return_code": "",
            "return_msg": "",
            "fill_price": None,
            "broker_accepted": False,
        }

    def _submit(
        self,
        *,
        spec: WidgetSpec,
        symbol_state: dict[str, Any],
        side: str,
        qty: int,
        route: str,
        signal_id: str,
        now: datetime,
        order_role: str,
        limit_price: int | None = None,
        parent_entry_signal_id: str | None = None,
    ) -> dict[str, Any]:
        order = self._order_record(
            side=side,
            qty=qty,
            route=route,
            signal_id=signal_id,
            now=now,
            order_role=order_role,
            limit_price=limit_price,
            parent_entry_signal_id=parent_entry_signal_id,
        )
        symbol_state.setdefault("orders", []).append(order)
        self._save()  # crash-before/after-submit ambiguity guard
        try:
            if side == "BUY":
                result = self.gateway.submit_buy(code=spec.code, qty=qty, route=route)
            elif order_role == ORDER_ROLE_TAKE_PROFIT and limit_price is not None:
                result = self.gateway.submit_limit_sell(
                    code=spec.code,
                    qty=qty,
                    route=route,
                    price=limit_price,
                )
            else:
                result = self.gateway.submit_sell(code=spec.code, qty=qty, route=route)
        except Exception as exc:
            order.update(
                {
                    "status": "AMBIGUOUS",
                    "return_code": type(exc).__name__,
                    "return_msg": str(exc)[:160],
                }
            )
            self._save()
            self._event(
                "order_submit_ambiguous",
                spec,
                now,
                side=side,
                requested_qty=qty,
                signal_id=signal_id,
                error=type(exc).__name__,
            )
            return order
        order.update(
            {
                "order_no": result.order_no,
                "return_code": result.return_code,
                "return_msg": result.return_msg[:160],
                "status": (
                    "SUBMITTED"
                    if result.accepted
                    else "AMBIGUOUS" if result.ambiguous else "FAILED"
                ),
                "broker_accepted": result.accepted,
                "submitted_at": now.isoformat(),
            }
        )
        self._save()
        self._event(
            "order_submitted" if result.accepted else "order_submit_failed",
            spec,
            now,
            side=side,
            requested_qty=qty,
            signal_id=signal_id,
            route=route,
            order_no=result.order_no,
            return_code=result.return_code,
            ambiguous=result.ambiguous,
            actual_order_submitted=result.accepted,
            order_role=order_role,
            limit_price=limit_price,
        )
        return order

    def _reconcile(
        self, spec: WidgetSpec, symbol_state: dict[str, Any], now: datetime
    ) -> None:
        changed = False
        for order in symbol_state.get("orders") or []:
            if order.get("status") not in {
                "SUBMITTED",
                "CANCEL_REQUESTED",
                "CANCEL_AMBIGUOUS",
                "CANCEL_FAILED_TERMINAL",
            }:
                continue
            order_no = str(order.get("order_no") or "")
            if not order_no:
                continue
            try:
                snapshot = self.gateway.execution_snapshot(
                    code=spec.code,
                    order_no=order_no,
                    route=str(order.get("route") or ""),
                    order_date=str(order.get("order_date") or now.date().isoformat()),
                )
            except Exception as exc:
                order["last_reconcile_error"] = type(exc).__name__
                order["last_reconcile_error_at"] = now.isoformat()
                changed = True
                continue
            if not snapshot.source_ok:
                last_error_at = _timestamp(order.get("last_reconcile_error_at"))
                if (
                    last_error_at is None
                    or (now - last_error_at).total_seconds()
                    >= OBSERVABILITY_PERSIST_INTERVAL_SEC
                ):
                    order["last_reconcile_error"] = snapshot.error or "source_not_ok"
                    order["last_reconcile_error_at"] = now.isoformat()
                    changed = True
                continue
            if not snapshot.found:
                last_not_found_at = _timestamp(order.get("last_reconcile_not_found_at"))
                if (
                    last_not_found_at is None
                    or (now - last_not_found_at).total_seconds()
                    >= OBSERVABILITY_PERSIST_INTERVAL_SEC
                ):
                    order["reconcile_not_found_count"] = (
                        _positive_int(order.get("reconcile_not_found_count")) + 1
                    )
                    order["last_reconcile_not_found_at"] = now.isoformat()
                    changed = True
                continue
            requested = _positive_int(order.get("requested_qty"))
            prior_filled = _positive_int(order.get("filled_qty"))
            prior_status = str(order.get("status") or "")
            filled = min(requested, max(prior_filled, snapshot.filled_qty))
            remaining = min(max(0, requested - filled), snapshot.remaining_qty)
            order["filled_qty"] = filled
            order["remaining_qty"] = remaining
            if snapshot.fill_price is not None:
                order["fill_price"] = snapshot.fill_price
            order["last_reconciled_at"] = now.isoformat()
            if remaining == 0:
                order["status"] = (
                    "FILLED"
                    if filled == requested
                    else "PARTIAL_CANCELED" if filled else "CANCELED"
                )
            changed = True
            if filled != prior_filled or order.get("status") != prior_status:
                self._event(
                    "order_execution_reconciled",
                    spec,
                    now,
                    side=order.get("side"),
                    order_no=order_no,
                    requested_qty=requested,
                    filled_qty=filled,
                    remaining_qty=remaining,
                    order_status=order.get("status"),
                    order_role=order.get("order_role"),
                    limit_price=order.get("limit_price"),
                    parent_entry_signal_id=order.get("parent_entry_signal_id"),
                    actual_order_submitted=True,
                )
        if changed:
            self._save()

    def _cancel_pending_buys(
        self, spec: WidgetSpec, symbol_state: dict[str, Any], now: datetime
    ) -> None:
        for order in symbol_state.get("orders") or []:
            if order.get("side") != "BUY" or order.get("status") != "SUBMITTED":
                continue
            remaining = _positive_int(order.get("remaining_qty"))
            if remaining <= 0:
                continue
            attempts = _positive_int(order.get("cancel_attempt_count"))
            if attempts >= MAX_CANCEL_ATTEMPTS:
                if order.get("status") != "CANCEL_FAILED_TERMINAL":
                    order["status"] = "CANCEL_FAILED_TERMINAL"
                    order["cancel_terminal_at"] = now.isoformat()
                    self._save()
                    self._event(
                        "buy_cancel_terminal_failure",
                        spec,
                        now,
                        order_no=order.get("order_no"),
                        remaining_qty=remaining,
                        cancel_attempt_count=attempts,
                    )
                continue
            last_attempt = _timestamp(order.get("cancel_attempted_at"))
            if (
                last_attempt is not None
                and (now - last_attempt).total_seconds() < SELL_RETRY_SEC
            ):
                continue
            order["cancel_attempt_count"] = attempts + 1
            try:
                result = self.gateway.cancel(
                    code=spec.code,
                    order_no=str(order.get("order_no") or ""),
                    qty=remaining,
                    route=str(order.get("route") or ""),
                )
            except Exception as exc:
                order["cancel_error"] = type(exc).__name__
                order["cancel_attempted_at"] = now.isoformat()
                order["status"] = "CANCEL_AMBIGUOUS"
                self._save()
                self._event(
                    "buy_cancel_ambiguous",
                    spec,
                    now,
                    order_no=order.get("order_no"),
                    remaining_qty=remaining,
                    error=type(exc).__name__,
                )
                continue
            order["cancel_attempted_at"] = now.isoformat()
            order["cancel_return_code"] = result.return_code
            order["cancel_order_no"] = result.order_no
            if result.accepted:
                order["status"] = "CANCEL_REQUESTED"
            elif result.ambiguous:
                order["status"] = "CANCEL_AMBIGUOUS"
            self._save()
            self._event(
                "buy_cancel_requested" if result.accepted else "buy_cancel_failed",
                spec,
                now,
                order_no=order.get("order_no"),
                remaining_qty=remaining,
                return_code=result.return_code,
            )

    @staticmethod
    def _has_pending(symbol_state: dict[str, Any], side: str) -> bool:
        return any(
            order.get("side") == side and order.get("status") in ACTIVE_ORDER_STATUSES
            for order in symbol_state.get("orders") or []
        )

    @staticmethod
    def _take_profit_pending_qty(
        symbol_state: dict[str, Any], parent_entry_signal_id: str
    ) -> int:
        return sum(
            _positive_int(order.get("remaining_qty"))
            for order in symbol_state.get("orders") or []
            if order.get("order_role") == ORDER_ROLE_TAKE_PROFIT
            and order.get("parent_entry_signal_id") == parent_entry_signal_id
            and order.get("status") in ACTIVE_ORDER_STATUSES
        )

    @staticmethod
    def _entry_fill_basis(
        symbol_state: dict[str, Any], entry_signal_id: str
    ) -> tuple[int, int]:
        rows = [
            order
            for order in symbol_state.get("orders") or []
            if order.get("order_role") in {None, "", ORDER_ROLE_ENTRY_BUY}
            and order.get("side") == "BUY"
            and order.get("signal_id") == entry_signal_id
            and order.get("broker_accepted") is True
            and _positive_int(order.get("filled_qty")) > 0
            and _positive_int(order.get("fill_price")) > 0
        ]
        total_qty = sum(_positive_int(order.get("filled_qty")) for order in rows)
        if total_qty <= 0:
            return 0, 0
        total_notional = sum(
            _positive_int(order.get("filled_qty"))
            * _positive_int(order.get("fill_price"))
            for order in rows
        )
        return total_qty, total_notional // total_qty

    def _maybe_submit_take_profit(
        self,
        spec: WidgetSpec,
        symbol_state: dict[str, Any],
        now: datetime,
    ) -> None:
        if symbol_state.get("exit_requested"):
            return
        entry_signal_id = str(symbol_state.get("entry_signal_id") or "")
        if not entry_signal_id or not symbol_state.get("entry_episode_open"):
            return
        if any(
            order.get("order_role") == ORDER_ROLE_TAKE_PROFIT
            and order.get("parent_entry_signal_id") == entry_signal_id
            and order.get("status") in {"SUBMITTING", "AMBIGUOUS"}
            for order in symbol_state.get("orders") or []
        ):
            # A crash/transport ambiguity may already have reached the broker.
            # Never create a second sell until an operator resolves that intent.
            return
        open_qty = self._open_qty(symbol_state)
        pending_qty = self._take_profit_pending_qty(symbol_state, entry_signal_id)
        uncovered_qty = max(0, open_qty - pending_qty)
        if uncovered_qty <= 0:
            return
        filled_qty, average_fill_price = self._entry_fill_basis(
            symbol_state, entry_signal_id
        )
        if filled_qty <= 0 or average_fill_price <= 0:
            if symbol_state.get("take_profit_basis_block_signal_id") != entry_signal_id:
                symbol_state["take_profit_basis_block_signal_id"] = entry_signal_id
                symbol_state["take_profit_basis_blocked_at"] = now.isoformat()
                self._save()
                self._event(
                    "take_profit_blocked_missing_fill_price",
                    spec,
                    now,
                    signal_id=entry_signal_id,
                    current_day_open_qty=open_qty,
                )
            return
        failure_count = _positive_int(symbol_state.get("take_profit_failure_count"))
        if failure_count >= MAX_TAKE_PROFIT_FAILURES:
            if not symbol_state.get("take_profit_terminal_failure_at"):
                symbol_state["take_profit_terminal_failure_at"] = now.isoformat()
                self._save()
                self._event(
                    "take_profit_terminal_failure",
                    spec,
                    now,
                    signal_id=entry_signal_id,
                    current_day_open_qty=open_qty,
                    failure_count=failure_count,
                )
            return
        last_attempt = _timestamp(symbol_state.get("last_take_profit_attempt_at"))
        if (
            last_attempt is not None
            and (now - last_attempt).total_seconds() < SELL_RETRY_SEC
        ):
            return
        # Bind the protective order to the broker-accepted entry route. A later
        # stale/session-transition snapshot must not rewrite order provenance.
        route = str(symbol_state.get("entry_route") or "").upper()
        if route not in {"KRX", "NXT"}:
            return
        target_price = _take_profit_price(average_fill_price)
        symbol_state["take_profit_target_price"] = target_price
        symbol_state["take_profit_basis_fill_price"] = average_fill_price
        symbol_state["take_profit_bps"] = TAKE_PROFIT_BPS
        self._save()
        order = self._submit(
            spec=spec,
            symbol_state=symbol_state,
            side="SELL",
            qty=uncovered_qty,
            route=route,
            signal_id=f"{entry_signal_id}:TP:{target_price}",
            now=now,
            order_role=ORDER_ROLE_TAKE_PROFIT,
            limit_price=target_price,
            parent_entry_signal_id=entry_signal_id,
        )
        if order.get("status") == "FAILED":
            symbol_state["take_profit_failure_count"] = failure_count + 1
            symbol_state["last_take_profit_attempt_at"] = now.isoformat()
            self._save()
        elif order.get("broker_accepted") is True:
            symbol_state["take_profit_last_submitted_at"] = now.isoformat()
            symbol_state["last_take_profit_attempt_at"] = None
            self._save()

    def _cancel_pending_take_profit_sells(
        self, spec: WidgetSpec, symbol_state: dict[str, Any], now: datetime
    ) -> None:
        for order in symbol_state.get("orders") or []:
            if order.get("order_role") != ORDER_ROLE_TAKE_PROFIT or order.get(
                "status"
            ) not in {"SUBMITTED", "CANCEL_AMBIGUOUS"}:
                continue
            remaining = _positive_int(order.get("remaining_qty"))
            if remaining <= 0:
                continue
            attempts = _positive_int(order.get("cancel_attempt_count"))
            if attempts >= MAX_CANCEL_ATTEMPTS:
                if order.get("status") != "CANCEL_FAILED_TERMINAL":
                    order["status"] = "CANCEL_FAILED_TERMINAL"
                    order["cancel_terminal_at"] = now.isoformat()
                    self._save()
                    self._event(
                        "take_profit_cancel_terminal_failure",
                        spec,
                        now,
                        order_no=order.get("order_no"),
                        remaining_qty=remaining,
                        cancel_attempt_count=attempts,
                    )
                continue
            last_attempt = _timestamp(order.get("cancel_attempted_at"))
            if (
                last_attempt is not None
                and (now - last_attempt).total_seconds() < SELL_RETRY_SEC
            ):
                continue
            order["cancel_attempt_count"] = attempts + 1
            try:
                result = self.gateway.cancel(
                    code=spec.code,
                    order_no=str(order.get("order_no") or ""),
                    qty=remaining,
                    route=str(order.get("route") or ""),
                )
            except Exception as exc:
                order["cancel_error"] = type(exc).__name__
                order["cancel_attempted_at"] = now.isoformat()
                order["status"] = "CANCEL_AMBIGUOUS"
                self._save()
                self._event(
                    "take_profit_cancel_ambiguous",
                    spec,
                    now,
                    order_no=order.get("order_no"),
                    remaining_qty=remaining,
                    error=type(exc).__name__,
                )
                continue
            order["cancel_attempted_at"] = now.isoformat()
            order["cancel_return_code"] = result.return_code
            order["cancel_order_no"] = result.order_no
            if result.accepted:
                order["status"] = "CANCEL_REQUESTED"
            elif result.ambiguous:
                order["status"] = "CANCEL_AMBIGUOUS"
            self._save()
            self._event(
                (
                    "take_profit_cancel_requested"
                    if result.accepted
                    else "take_profit_cancel_failed"
                ),
                spec,
                now,
                order_no=order.get("order_no"),
                remaining_qty=remaining,
                return_code=result.return_code,
            )

    def _maybe_submit_exit(
        self,
        spec: WidgetSpec,
        symbol_state: dict[str, Any],
        payload: dict[str, Any],
        now: datetime,
    ) -> None:
        if not symbol_state.get("exit_requested"):
            return
        self._cancel_pending_buys(spec, symbol_state, now)
        self._cancel_pending_take_profit_sells(spec, symbol_state, now)
        if self._has_pending(symbol_state, "BUY") or self._has_pending(
            symbol_state, "SELL"
        ):
            return
        qty = self._open_qty(symbol_state)
        if qty <= 0:
            symbol_state["entry_episode_open"] = False
            symbol_state["exit_requested"] = False
            symbol_state["exit_completed_at"] = now.isoformat()
            symbol_state["sell_attempt_count"] = 0
            symbol_state["last_sell_attempt_at"] = None
            self._save()
            return
        attempts = _positive_int(symbol_state.get("sell_attempt_count"))
        if attempts >= MAX_SELL_ATTEMPTS:
            if not symbol_state.get("sell_terminal_failure_at"):
                symbol_state["sell_terminal_failure_at"] = now.isoformat()
                self._save()
                self._event(
                    "sell_terminal_failure",
                    spec,
                    now,
                    remaining_qty=qty,
                    sell_attempt_count=attempts,
                    exit_signal_id=symbol_state.get("exit_signal_id"),
                )
            return
        last_attempt = _timestamp(symbol_state.get("last_sell_attempt_at"))
        if (
            last_attempt is not None
            and (now - last_attempt).total_seconds() < SELL_RETRY_SEC
        ):
            return
        route = str(symbol_state.get("exit_route") or self._route(payload))
        if route not in {"KRX", "NXT"}:
            return
        symbol_state["sell_attempt_count"] = attempts + 1
        symbol_state["last_sell_attempt_at"] = now.isoformat()
        self._save()
        self._submit(
            spec=spec,
            symbol_state=symbol_state,
            side="SELL",
            qty=qty,
            route=route,
            signal_id=str(symbol_state.get("exit_signal_id") or ""),
            now=now,
            order_role=ORDER_ROLE_FINAL_EXIT,
        )

    def process_payload(
        self, spec: WidgetSpec, payload: dict[str, Any], now: datetime
    ) -> None:
        symbol_state = self._state["symbols"][spec.code]
        self._reconcile(spec, symbol_state, now)

        exit_signal_id = self._exit_signal(spec, payload, now)
        if exit_signal_id and exit_signal_id != symbol_state.get("exit_signal_id"):
            symbol_state.update(
                {
                    "exit_signal_id": exit_signal_id,
                    "exit_requested": True,
                    "exit_route": self._route(payload),
                    "exit_requested_at": now.isoformat(),
                }
            )
            self._save()
            self._event(
                "final_exit_signal_consumed",
                spec,
                now,
                signal_id=exit_signal_id,
                current_day_open_qty=self._open_qty(symbol_state),
            )

        self._maybe_submit_exit(spec, symbol_state, payload, now)
        # A source-qualified final exit dominates any entry payload carried in
        # the same snapshot.  Re-entry is possible only after the producer has
        # cleared that final-exit event and emitted a new entry episode.
        if symbol_state.get("exit_requested") or exit_signal_id:
            return

        self._maybe_submit_take_profit(spec, symbol_state, now)

        entry_signal = self._entry_signal(spec, payload, now)
        if entry_signal is None or symbol_state.get("entry_episode_open"):
            return
        signal_id, source_state = entry_signal
        if signal_id == symbol_state.get("entry_signal_id"):
            return
        route = self._route(payload)
        if route not in {"KRX", "NXT"}:
            return
        exclusion = evaluate_manual_control_exclusion(spec.code)
        operator_source = manual_control_operator_exclusion_source(spec.code)
        if not exclusion.excluded or not operator_source:
            self._record_entry_block_once(
                spec=spec,
                symbol_state=symbol_state,
                signal_id=signal_id,
                reason="entry_blocked_main_bot_ownership_not_excluded",
                now=now,
                exclusion_applied=exclusion.excluded,
                exclusion_source=exclusion.source,
                required_source="manual_operator_or_explicit_env",
            )
            return
        if is_buy_side_paused():
            self._record_entry_block_once(
                spec=spec,
                symbol_state=symbol_state,
                signal_id=signal_id,
                reason="entry_blocked_global_buy_pause",
                now=now,
            )
            return
        for key in (
            "take_profit_basis_block_signal_id",
            "take_profit_basis_blocked_at",
            "take_profit_terminal_failure_at",
            "take_profit_target_price",
            "take_profit_basis_fill_price",
            "take_profit_bps",
        ):
            symbol_state.pop(key, None)
        symbol_state.update(
            {
                "entry_episode_open": True,
                "entry_signal_id": signal_id,
                "entry_source_state": source_state,
                "entry_route": route,
                "entry_consumed_at": now.isoformat(),
                "take_profit_failure_count": 0,
                "last_take_profit_attempt_at": None,
            }
        )
        self._save()
        self._submit(
            spec=spec,
            symbol_state=symbol_state,
            side="BUY",
            qty=self.entry_qty,
            route=route,
            signal_id=signal_id,
            now=now,
            order_role=ORDER_ROLE_ENTRY_BUY,
        )

    def run_once(self, observed_at: datetime | None = None) -> dict[str, Any]:
        now = (observed_at or _now_kst()).astimezone(KST)
        self._activate_date(now)
        if not self.enabled:
            return deepcopy(self._state)
        for spec in self.specs:
            payload = self.snapshot_loader(spec.snapshot_path)
            if payload:
                self.process_payload(spec, payload, now)
        last_cycle_at = _timestamp(self._state.get("last_cycle_at"))
        if (
            last_cycle_at is None
            or (now - last_cycle_at).total_seconds()
            >= OBSERVABILITY_PERSIST_INTERVAL_SEC
        ):
            self._state["last_cycle_at"] = now.isoformat()
            self._save()
        return deepcopy(self._state)

    def run_forever(self, *, interval_sec: float = 1.0) -> None:
        interval = max(0.5, float(interval_sec))
        while True:
            started = time.monotonic()
            self.run_once()
            remaining = interval - (time.monotonic() - started)
            if remaining > 0:
                time.sleep(remaining)
