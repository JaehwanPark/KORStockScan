"""Persistent state machine for one Samsung morning round trip per KST day."""

from __future__ import annotations

import json
import os
import tempfile
import time as time_module
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Callable, Protocol
from zoneinfo import ZoneInfo

from src.engine.risk.manual_control_exclusion import (
    manual_control_operator_exclusion_source,
)
from src.trading.samsung_morning_one_share.gateway import (
    ExecutionSnapshot,
    OpenPriceSnapshot,
    SubmitResult,
)
from src.trading.samsung_morning_one_share.policy import (
    DEFAULT_POLICY,
    EntryWindow,
    MorningOneSharePolicy,
)
from src.utils.constants import DATA_DIR

KST = ZoneInfo("Asia/Seoul")
DEFAULT_STATE_PATH = DATA_DIR / "runtime" / "samsung_morning_one_share_state.json"


class OneShareGateway(Protocol):
    def opening_price(self, *, route: str, trade_date: date) -> OpenPriceSnapshot: ...

    def submit_limit_buy(self, *, route: str, price: int) -> SubmitResult: ...

    def submit_limit_sell(self, *, route: str, price: int) -> SubmitResult: ...

    def submit_best_sell(self, *, route: str) -> SubmitResult: ...

    def cancel(self, *, route: str, order_no: str) -> SubmitResult: ...

    def execution_snapshot(
        self, *, route: str, order_no: str, order_date: str
    ) -> ExecutionSnapshot: ...


def _iso(now: datetime) -> str:
    return now.astimezone(KST).isoformat()


def _parse_datetime(value: object) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value or ""))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=KST)
    return parsed.astimezone(KST)


def _fresh_state(trade_date: date) -> dict:
    return {
        "schema": "samsung_morning_one_share_state_v1",
        "trade_date": trade_date.isoformat(),
        "status": "READY",
        "nxt_resolved_without_fill": False,
        "daily_trade_consumed": False,
        "route": "",
        "entry_price": 0,
        "buy_order_no": "",
        "buy_submitted_at": "",
        "buy_cancel_requested": False,
        "fill_price": 0,
        "buy_filled_at": "",
        "position_qty": 0,
        "target_price": 0,
        "target_order_no": "",
        "target_cancel_requested": False,
        "exit_order_no": "",
        "blocked_reason": "",
        "owned_order_nos": [],
        "last_action": "initialized",
        "audit": [],
    }


class SamsungMorningOneShareMachine:
    """Independent one-share executor; existing strategy decisions are not inputs."""

    def __init__(
        self,
        *,
        gateway: OneShareGateway,
        state_path: Path = DEFAULT_STATE_PATH,
        policy: MorningOneSharePolicy = DEFAULT_POLICY,
        live_enabled: bool = False,
        ownership_source: Callable[[object], str] = (
            manual_control_operator_exclusion_source
        ),
    ) -> None:
        self.gateway = gateway
        self.state_path = Path(state_path)
        self.policy = policy
        self.live_enabled = bool(live_enabled)
        self.ownership_source = ownership_source
        self._state = self._load_state()

    def _load_state(self) -> dict:
        try:
            payload = json.loads(self.state_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return {}
        except (OSError, json.JSONDecodeError) as exc:
            return {
                "schema": "samsung_morning_one_share_state_v1",
                "trade_date": "",
                "status": "BLOCKED",
                "position_qty": 0,
                "blocked_reason": f"state_unreadable:{type(exc).__name__}",
                "last_action": "blocked_state_load",
                "audit": [],
            }
        if not isinstance(payload, dict) or payload.get("schema") != (
            "samsung_morning_one_share_state_v1"
        ):
            return {
                "schema": "samsung_morning_one_share_state_v1",
                "trade_date": "",
                "status": "BLOCKED",
                "position_qty": 0,
                "blocked_reason": "state_schema_invalid",
                "last_action": "blocked_state_load",
                "audit": [],
            }
        return payload

    def _save(self) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(
            prefix=f".{self.state_path.name}.", dir=self.state_path.parent
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(
                    self._state, handle, ensure_ascii=False, indent=2, sort_keys=True
                )
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, self.state_path)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)

    def _record(self, now: datetime, action: str, **fields: object) -> None:
        self._state["last_action"] = action
        audit = self._state.setdefault("audit", [])
        audit.append({"at_kst": _iso(now), "action": action, **fields})
        self._state["audit"] = audit[-100:]
        self._save()

    def _own_order(self, order_no: str) -> None:
        clean = str(order_no or "").strip()
        owned = {str(item) for item in self._state.get("owned_order_nos", []) if item}
        if clean:
            owned.add(clean)
        self._state["owned_order_nos"] = sorted(owned)

    def _owns_order(self, order_no: str) -> bool:
        clean = str(order_no or "").strip()
        return bool(
            clean
            and clean
            in {
                str(item).strip()
                for item in self._state.get("owned_order_nos", [])
                if item
            }
        )

    def _block(self, now: datetime, reason: str) -> dict:
        self._state["status"] = "BLOCKED"
        self._state["blocked_reason"] = reason
        self._record(now, "blocked", reason=reason)
        return self.snapshot()

    def snapshot(self) -> dict:
        return json.loads(json.dumps(self._state, ensure_ascii=False))

    def _roll_date(self, now: datetime) -> bool:
        today = now.date()
        if not self._state:
            self._state = _fresh_state(today)
            self._save()
            return True
        if self._state.get("trade_date") == today.isoformat():
            return True
        status = str(self._state.get("status") or "")
        unresolved = bool(
            int(self._state.get("position_qty", 0) or 0)
            or status not in {"READY", "COMPLETE", "NO_TRADE"}
        )
        if unresolved:
            self._state["status"] = "BLOCKED"
            self._state["blocked_reason"] = "previous_day_order_or_position_unresolved"
            self._record(now, "blocked_date_rollover")
            return False
        self._state = _fresh_state(today)
        self._record(now, "daily_state_initialized")
        return True

    def _execution(self, order_no: str) -> ExecutionSnapshot:
        return self.gateway.execution_snapshot(
            route=str(self._state.get("route") or ""),
            order_no=order_no,
            order_date=str(self._state.get("trade_date") or ""),
        )

    def _submit_target(self, now: datetime) -> dict:
        if int(self._state.get("position_qty", 0) or 0) != 1:
            return self._block(now, "target_requires_exact_owned_one_share")
        if not self._owns_order(str(self._state.get("buy_order_no") or "")):
            return self._block(now, "filled_buy_not_owned_by_one_share_machine")
        fill_price = int(self._state.get("fill_price", 0) or 0)
        if fill_price <= 0:
            return self._block(now, "confirmed_fill_price_missing")
        target_price = self.policy.target_price(fill_price)
        self._state["status"] = "TARGET_SUBMITTING"
        self._record(now, "target_submit_intent", target_price=target_price)
        result = self.gateway.submit_limit_sell(
            route=str(self._state["route"]), price=target_price
        )
        if result.ambiguous:
            return self._block(now, "target_submit_ambiguous_reconciliation_required")
        if not result.accepted:
            self._state["status"] = "POSITION_OPEN"
            self._record(
                now,
                "target_submit_rejected_retryable",
                return_code=result.return_code,
            )
            return self.snapshot()
        self._state.update(
            {
                "status": "TARGET_OPEN",
                "target_price": target_price,
                "target_order_no": result.order_no,
                "target_cancel_requested": False,
            }
        )
        self._own_order(result.order_no)
        self._record(now, "target_submitted", target_price=target_price)
        return self.snapshot()

    def _reconcile_buy(self, now: datetime) -> dict:
        order_no = str(self._state.get("buy_order_no") or "")
        if not self._owns_order(order_no):
            return self._block(now, "buy_order_not_owned_by_one_share_machine")
        snapshot = self._execution(order_no)
        if not snapshot.source_ok:
            self._record(now, "buy_reconciliation_wait", error=snapshot.error)
            return self.snapshot()
        if snapshot.found and snapshot.filled_qty == 1:
            if snapshot.fill_price is None or snapshot.fill_price <= 0:
                return self._block(now, "buy_fill_price_missing")
            self._state.update(
                {
                    "daily_trade_consumed": True,
                    "position_qty": 1,
                    "fill_price": snapshot.fill_price,
                    "buy_filled_at": _iso(now),
                    "status": "POSITION_OPEN",
                }
            )
            self._record(now, "buy_fill_confirmed", fill_price=snapshot.fill_price)
            return self._submit_target(now)
        if snapshot.found and snapshot.filled_qty == 0 and snapshot.remaining_qty == 0:
            route = str(self._state.get("route") or "")
            self._state.update(
                {
                    "status": "READY" if route == "NXT" else "NO_TRADE",
                    "nxt_resolved_without_fill": route == "NXT",
                    "buy_cancel_requested": False,
                }
            )
            self._record(now, "buy_resolved_without_fill", route=route)
            return self.snapshot()

        route = str(self._state.get("route") or "")
        deadline = (
            self.policy.nxt.deadline if route == "NXT" else self.policy.krx.deadline
        )
        if now.time() <= deadline:
            self._record(now, "buy_open_wait")
            return self.snapshot()
        if bool(self._state.get("buy_cancel_requested")):
            self._record(now, "buy_cancel_reconciliation_wait")
            return self.snapshot()
        self._state["status"] = "BUY_CANCEL_SUBMITTING"
        self._record(now, "buy_cancel_intent")
        result = self.gateway.cancel(route=route, order_no=order_no)
        if result.ambiguous:
            return self._block(now, "buy_cancel_ambiguous_reconciliation_required")
        if not result.accepted:
            self._state["status"] = "BUY_OPEN"
            self._record(
                now,
                "buy_cancel_rejected_retryable",
                return_code=result.return_code,
            )
            return self.snapshot()
        self._state["status"] = "BUY_CANCEL_PENDING"
        self._state["buy_cancel_requested"] = True
        self._own_order(result.order_no)
        self._record(now, "buy_cancel_submitted")
        return self.snapshot()

    def _reconcile_target(self, now: datetime) -> dict:
        order_no = str(self._state.get("target_order_no") or "")
        if not self._owns_order(order_no):
            return self._block(now, "target_order_not_owned_by_one_share_machine")
        snapshot = self._execution(order_no)
        if not snapshot.source_ok:
            self._record(now, "target_reconciliation_wait", error=snapshot.error)
            return self.snapshot()
        if snapshot.found and snapshot.filled_qty == 1:
            self._state.update(
                {"position_qty": 0, "status": "COMPLETE", "blocked_reason": ""}
            )
            self._record(now, "target_fill_confirmed")
            return self.snapshot()
        if snapshot.found and snapshot.filled_qty == 0 and snapshot.remaining_qty == 0:
            if not bool(self._state.get("target_cancel_requested")):
                return self._block(now, "target_disappeared_before_machine_cancel")
            self._state["status"] = "EXIT_SUBMITTING"
            self._record(now, "final_exit_submit_intent")
            result = self.gateway.submit_best_sell(route=str(self._state["route"]))
            if result.ambiguous:
                return self._block(now, "final_exit_submit_ambiguous")
            if not result.accepted:
                self._state["status"] = "TARGET_CANCEL_PENDING"
                self._record(
                    now,
                    "final_exit_submit_rejected_retryable",
                    return_code=result.return_code,
                )
                return self.snapshot()
            self._state.update(
                {"status": "EXIT_OPEN", "exit_order_no": result.order_no}
            )
            self._own_order(result.order_no)
            self._record(now, "final_exit_submitted")
            return self.snapshot()

        filled_at = _parse_datetime(self._state.get("buy_filled_at"))
        if filled_at is None:
            return self._block(now, "buy_fill_timestamp_missing")
        deadline = filled_at + timedelta(minutes=self.policy.max_hold_minutes)
        if now <= deadline:
            self._record(now, "target_open_wait")
            return self.snapshot()
        if bool(self._state.get("target_cancel_requested")):
            self._record(now, "target_cancel_reconciliation_wait")
            return self.snapshot()
        self._state["status"] = "TARGET_CANCEL_SUBMITTING"
        self._record(now, "target_cancel_intent")
        result = self.gateway.cancel(route=str(self._state["route"]), order_no=order_no)
        if result.ambiguous:
            return self._block(now, "target_cancel_ambiguous_reconciliation_required")
        if not result.accepted:
            self._state["status"] = "TARGET_OPEN"
            self._record(
                now,
                "target_cancel_rejected_retryable",
                return_code=result.return_code,
            )
            return self.snapshot()
        self._state["status"] = "TARGET_CANCEL_PENDING"
        self._state["target_cancel_requested"] = True
        self._own_order(result.order_no)
        self._record(now, "target_cancel_submitted")
        return self.snapshot()

    def _reconcile_exit(self, now: datetime) -> dict:
        order_no = str(self._state.get("exit_order_no") or "")
        if not self._owns_order(order_no):
            return self._block(now, "exit_order_not_owned_by_one_share_machine")
        snapshot = self._execution(order_no)
        if not snapshot.source_ok or not snapshot.found:
            self._record(now, "final_exit_reconciliation_wait", error=snapshot.error)
            return self.snapshot()
        if snapshot.filled_qty == 1:
            self._state.update(
                {"position_qty": 0, "status": "COMPLETE", "blocked_reason": ""}
            )
            self._record(now, "final_exit_fill_confirmed")
            return self.snapshot()
        if snapshot.remaining_qty == 0:
            return self._block(now, "final_exit_closed_without_fill")
        self._record(now, "final_exit_open_wait")
        return self.snapshot()

    def _submit_entry(self, now: datetime, window: EntryWindow) -> dict:
        source = str(self.ownership_source(self.policy.symbol) or "")
        if self.live_enabled and not source:
            self._state["last_action"] = "operator_exclusion_required"
            self._state["blocked_reason"] = "005930_not_excluded_from_primary_bot"
            self._save()
            return self.snapshot()
        opening = self.gateway.opening_price(route=window.route, trade_date=now.date())
        if not opening.source_ok or not opening.price:
            self._state["last_action"] = "opening_price_wait"
            self._state["blocked_reason"] = opening.error
            self._save()
            return self.snapshot()
        entry_price = self.policy.entry_price(opening.price, window.drawdown_pct)
        if not self.live_enabled:
            self._state["last_action"] = f"would_submit_{window.route.lower()}_buy"
            self._state["blocked_reason"] = "live_authority_disabled"
            self._state["preview"] = {
                "route": window.route,
                "open_price": opening.price,
                "entry_price": entry_price,
                "quantity": 1,
                "operator_exclusion_ready": bool(source),
                "parallel_widget_orders_allowed": True,
            }
            self._save()
            return self.snapshot()
        self._state.update(
            {
                "status": "BUY_SUBMITTING",
                "route": window.route,
                "entry_price": entry_price,
                "blocked_reason": "",
            }
        )
        self._record(
            now,
            "buy_submit_intent",
            route=window.route,
            open_price=opening.price,
            entry_price=entry_price,
        )
        result = self.gateway.submit_limit_buy(route=window.route, price=entry_price)
        if result.ambiguous:
            return self._block(now, "buy_submit_ambiguous_reconciliation_required")
        if not result.accepted:
            self._state["status"] = "READY"
            self._state["last_action"] = "buy_submit_rejected"
            self._state["blocked_reason"] = result.return_code
            self._save()
            return self.snapshot()
        self._state.update(
            {
                "status": "BUY_OPEN",
                "route": window.route,
                "entry_price": entry_price,
                "buy_order_no": result.order_no,
                "buy_submitted_at": _iso(now),
                "buy_cancel_requested": False,
                "blocked_reason": "",
            }
        )
        self._own_order(result.order_no)
        self._record(
            now,
            "buy_submitted",
            route=window.route,
            open_price=opening.price,
            entry_price=entry_price,
        )
        return self.snapshot()

    def run_once(self, now: datetime | None = None) -> dict:
        now = (now or datetime.now(tz=KST)).astimezone(KST)
        if not self._roll_date(now):
            return self.snapshot()
        status = str(self._state.get("status") or "")
        if status == "BLOCKED":
            return self.snapshot()
        if status in {
            "BUY_SUBMITTING",
            "BUY_CANCEL_SUBMITTING",
            "TARGET_SUBMITTING",
            "TARGET_CANCEL_SUBMITTING",
            "EXIT_SUBMITTING",
        }:
            return self._block(now, f"broker_write_interrupted:{status.lower()}")
        if status in {"BUY_OPEN", "BUY_CANCEL_PENDING"}:
            return self._reconcile_buy(now)
        if status == "POSITION_OPEN":
            return self._submit_target(now)
        if status in {"TARGET_OPEN", "TARGET_CANCEL_PENDING"}:
            return self._reconcile_target(now)
        if status == "EXIT_OPEN":
            return self._reconcile_exit(now)
        if status in {"COMPLETE", "NO_TRADE"} or bool(
            self._state.get("daily_trade_consumed")
        ):
            return self.snapshot()

        current = now.time()
        if not bool(self._state.get("nxt_resolved_without_fill")):
            if self.policy.nxt.open_time <= current <= self.policy.nxt.deadline:
                return self._submit_entry(now, self.policy.nxt)
            if current > self.policy.nxt.deadline:
                self._state["nxt_resolved_without_fill"] = True
                self._record(now, "nxt_window_skipped_or_expired")
            else:
                self._state["last_action"] = "waiting_for_nxt_window"
                self._save()
                return self.snapshot()

        if self.policy.krx.open_time <= current <= self.policy.krx.deadline:
            return self._submit_entry(now, self.policy.krx)
        if current > self.policy.krx.deadline:
            self._state["status"] = "NO_TRADE"
            self._record(now, "krx_window_expired_without_fill")
        else:
            self._state["last_action"] = "waiting_for_krx_window"
            self._save()
        return self.snapshot()

    def run_forever(self, *, interval_sec: float = 1.0) -> None:
        while True:
            self.run_once()
            time_module.sleep(max(0.2, float(interval_sec)))

    def run_until_terminal(self, *, interval_sec: float = 2.0) -> dict:
        while True:
            state = self.run_once()
            if state.get("status") in {"COMPLETE", "NO_TRADE", "BLOCKED"}:
                return state
            time_module.sleep(max(0.2, float(interval_sec)))
