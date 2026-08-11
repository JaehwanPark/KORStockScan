"""Persistent state machine for one Samsung afternoon one-share episode."""

from __future__ import annotations

import json
import os
import tempfile
import time as time_module
from datetime import date, datetime
from pathlib import Path
from typing import Callable, Protocol
from zoneinfo import ZoneInfo

from src.engine.risk.manual_control_exclusion import (
    manual_control_operator_exclusion_source,
)
from src.trading.samsung_afternoon_one_share.gateway import (
    ExecutionSnapshot,
    MinuteBarsSnapshot,
    SubmitResult,
)
from src.trading.samsung_afternoon_one_share.policy import (
    DEFAULT_POLICY,
    AfternoonOneSharePolicy,
)
from src.utils.constants import DATA_DIR

KST = ZoneInfo("Asia/Seoul")
DEFAULT_STATE_PATH = DATA_DIR / "runtime" / "samsung_afternoon_one_share_state.json"


class AfternoonGateway(Protocol):
    def completed_sor_minute_bars(
        self, *, trade_date, now: datetime
    ) -> MinuteBarsSnapshot: ...
    def submit_limit_buy(self, *, price: int) -> SubmitResult: ...
    def submit_limit_sell(self, *, price: int) -> SubmitResult: ...
    def cancel_buy(self, *, order_no: str) -> SubmitResult: ...
    def execution_snapshot(
        self, *, order_no: str, order_date: str
    ) -> ExecutionSnapshot: ...


def _iso(now: datetime) -> str:
    return now.astimezone(KST).isoformat()


def _fresh_state(now: datetime) -> dict:
    return {
        "schema": "samsung_afternoon_one_share_state_v1",
        "trade_date": now.date().isoformat(),
        "status": "READY",
        "attempt_consumed": False,
        "last_evaluated_bar": "",
        "signal_bar": "",
        "signal_close": 0,
        "entry_price": 0,
        "buy_order_no": "",
        "buy_order_date": "",
        "buy_cancel_requested": False,
        "fill_price": 0,
        "buy_filled_at": "",
        "position_qty": 0,
        "target_price": 0,
        "target_order_no": "",
        "target_order_date": "",
        "blocked_reason": "",
        "owned_order_nos": [],
        "last_action": "initialized",
        "audit": [],
    }


class SamsungAfternoonOneShareMachine:
    """Owns only its exact order numbers; morning and widget positions are external."""

    def __init__(
        self,
        *,
        gateway: AfternoonGateway,
        state_path: Path = DEFAULT_STATE_PATH,
        policy: AfternoonOneSharePolicy = DEFAULT_POLICY,
        live_enabled: bool = False,
        ownership_source: Callable[
            [object], str
        ] = manual_control_operator_exclusion_source,
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
                "schema": "samsung_afternoon_one_share_state_v1",
                "trade_date": "",
                "status": "BLOCKED",
                "position_qty": 0,
                "blocked_reason": f"state_unreadable:{type(exc).__name__}",
                "last_action": "blocked_state_load",
                "audit": [],
            }
        if (
            not isinstance(payload, dict)
            or payload.get("schema") != "samsung_afternoon_one_share_state_v1"
        ):
            return {
                "schema": "samsung_afternoon_one_share_state_v1",
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
            os.chmod(temp_name, 0o600)
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

    def snapshot(self) -> dict:
        return json.loads(json.dumps(self._state, ensure_ascii=False))

    def _own_order(self, order_no: str) -> None:
        clean = str(order_no or "").strip()
        owned = {
            str(item).strip() for item in self._state.get("owned_order_nos", []) if item
        }
        if clean:
            owned.add(clean)
        self._state["owned_order_nos"] = sorted(owned)

    def _owns_order(self, order_no: str) -> bool:
        return str(order_no or "").strip() in {
            str(item).strip() for item in self._state.get("owned_order_nos", []) if item
        }

    def _block(self, now: datetime, reason: str) -> dict:
        self._state.update({"status": "BLOCKED", "blocked_reason": reason})
        self._record(now, "blocked", reason=reason)
        return self.snapshot()

    def _validate_state_contract(self, now: datetime) -> bool:
        status = str(self._state.get("status") or "")
        allowed = {
            "READY",
            "BUY_SUBMITTING",
            "BUY_OPEN",
            "BUY_CANCEL_SUBMITTING",
            "BUY_CANCEL_PENDING",
            "POSITION_OPEN",
            "TARGET_SUBMITTING",
            "TARGET_OPEN",
            "COMPLETE",
            "NO_TRADE",
            "HELD",
            "BLOCKED",
        }
        try:
            position_qty = int(self._state.get("position_qty", 0) or 0)
        except (TypeError, ValueError):
            self._block(now, "state_position_quantity_invalid")
            return False
        if status not in allowed or position_qty not in {0, 1}:
            self._block(now, "state_status_or_quantity_invalid")
            return False
        try:
            date.fromisoformat(str(self._state.get("trade_date") or ""))
        except ValueError:
            self._block(now, "state_trade_date_invalid")
            return False
        if not isinstance(self._state.get("attempt_consumed"), bool):
            self._block(now, "state_attempt_type_invalid")
            return False
        owned_order_nos = self._state.get("owned_order_nos")
        if not isinstance(owned_order_nos, list) or any(
            not isinstance(order_no, str) or not order_no.strip()
            for order_no in owned_order_nos
        ):
            self._block(now, "state_owned_order_ledger_invalid")
            return False
        position_statuses = {
            "POSITION_OPEN",
            "TARGET_SUBMITTING",
            "TARGET_OPEN",
            "HELD",
        }
        if status != "BLOCKED" and (status in position_statuses) != (position_qty == 1):
            self._block(now, "state_position_status_invariant_breach")
            return False
        buy_owned_statuses = {
            "BUY_OPEN",
            "BUY_CANCEL_SUBMITTING",
            "BUY_CANCEL_PENDING",
            *position_statuses,
        }
        if status in buy_owned_statuses and not self._owns_order(
            str(self._state.get("buy_order_no") or "")
        ):
            self._block(now, "state_buy_ownership_invariant_breach")
            return False
        if status in buy_owned_statuses:
            try:
                date.fromisoformat(str(self._state.get("buy_order_date") or ""))
            except ValueError:
                self._block(now, "state_buy_order_date_invalid")
                return False
        if status in {"TARGET_OPEN", "HELD"} and not self._owns_order(
            str(self._state.get("target_order_no") or "")
        ):
            self._block(now, "state_target_ownership_invariant_breach")
            return False
        if status in {"TARGET_OPEN", "HELD"}:
            try:
                date.fromisoformat(str(self._state.get("target_order_date") or ""))
            except ValueError:
                self._block(now, "state_target_order_date_invalid")
                return False
        if (
            status in buy_owned_statuses
            and self._state.get("attempt_consumed") is not True
        ):
            self._block(now, "state_attempt_invariant_breach")
            return False
        return True

    def _roll_date(self, now: datetime) -> bool:
        if not self._state:
            self._state = _fresh_state(now)
            self._save()
            return True
        if self._state.get("trade_date") == now.date().isoformat():
            return True
        status = str(self._state.get("status") or "")
        position_qty = int(self._state.get("position_qty", 0) or 0)
        if position_qty == 1 and status in {"TARGET_OPEN", "HELD", "POSITION_OPEN"}:
            return True
        if position_qty or status not in {"READY", "COMPLETE", "NO_TRADE"}:
            self._state.update(
                {
                    "status": "BLOCKED",
                    "blocked_reason": "previous_day_order_or_position_unresolved",
                }
            )
            self._record(now, "blocked_date_rollover")
            return False
        self._state = _fresh_state(now)
        self._record(now, "daily_state_initialized")
        return True

    def _execution(self, order_no: str, order_date: str) -> ExecutionSnapshot:
        return self.gateway.execution_snapshot(order_no=order_no, order_date=order_date)

    def _submit_target(self, now: datetime) -> dict:
        if int(self._state.get("position_qty", 0) or 0) != 1:
            return self._block(now, "target_requires_exact_owned_one_share")
        if not self._owns_order(str(self._state.get("buy_order_no") or "")):
            return self._block(now, "filled_buy_not_owned_by_afternoon_machine")
        fill_price = int(self._state.get("fill_price", 0) or 0)
        if fill_price <= 0:
            return self._block(now, "confirmed_fill_price_missing")
        target_price = self.policy.target_price(fill_price)
        self._state["status"] = "TARGET_SUBMITTING"
        self._record(now, "target_submit_intent", target_price=target_price)
        result = self.gateway.submit_limit_sell(price=target_price)
        if result.ambiguous:
            return self._block(now, "target_submit_ambiguous_reconciliation_required")
        if not result.accepted:
            self._state["status"] = "POSITION_OPEN"
            self._record(
                now, "target_submit_rejected_retryable", return_code=result.return_code
            )
            return self.snapshot()
        self._state.update(
            {
                "status": "TARGET_OPEN",
                "target_price": target_price,
                "target_order_no": result.order_no,
                "target_order_date": now.date().isoformat(),
            }
        )
        self._own_order(result.order_no)
        self._record(now, "target_submitted", target_price=target_price)
        return self.snapshot()

    def _reconcile_target(self, now: datetime) -> dict:
        order_no = str(self._state.get("target_order_no") or "")
        if not self._owns_order(order_no):
            return self._block(now, "target_order_not_owned_by_afternoon_machine")
        snapshot = self._execution(
            order_no, str(self._state.get("target_order_date") or "")
        )
        if not snapshot.source_ok:
            self._record(now, "target_reconciliation_wait", error=snapshot.error)
        elif not snapshot.found:
            self._record(now, "target_not_found_reconciliation_wait")
        elif snapshot.filled_qty == 1:
            self._state.update(
                {"position_qty": 0, "status": "COMPLETE", "blocked_reason": ""}
            )
            self._record(now, "target_fill_confirmed")
        elif snapshot.filled_qty == 0 and snapshot.remaining_qty == 0:
            self._state.update({"status": "HELD", "blocked_reason": ""})
            self._record(now, "target_closed_unfilled_position_held")
        else:
            self._record(now, "target_open_wait")
        return self.snapshot()

    def _source(self, now: datetime) -> MinuteBarsSnapshot:
        return self.gateway.completed_sor_minute_bars(trade_date=now.date(), now=now)

    def _completed_bars_after_signal(self, now: datetime) -> int | None:
        source = self._source(now)
        if not source.source_ok:
            self._record(now, "buy_expiry_source_wait", error=source.error)
            return None
        try:
            signal_bar = datetime.fromisoformat(
                str(self._state.get("signal_bar") or "")
            ).astimezone(KST)
        except ValueError:
            self._block(now, "signal_bar_missing_for_buy_expiry")
            return None
        return sum(bar.timestamp > signal_bar for bar in source.bars)

    def _reconcile_buy(self, now: datetime) -> dict:
        order_no = str(self._state.get("buy_order_no") or "")
        if not self._owns_order(order_no):
            return self._block(now, "buy_order_not_owned_by_afternoon_machine")
        snapshot = self._execution(
            order_no, str(self._state.get("buy_order_date") or "")
        )
        if not snapshot.source_ok:
            self._record(now, "buy_reconciliation_wait", error=snapshot.error)
            return self.snapshot()
        if snapshot.found and snapshot.filled_qty == 1:
            if not snapshot.fill_price:
                return self._block(now, "buy_fill_price_missing")
            self._state.update(
                {
                    "position_qty": 1,
                    "fill_price": snapshot.fill_price,
                    "buy_filled_at": _iso(now),
                    "status": "POSITION_OPEN",
                }
            )
            self._record(now, "buy_fill_confirmed", fill_price=snapshot.fill_price)
            return self._submit_target(now)
        if snapshot.found and snapshot.filled_qty == 0 and snapshot.remaining_qty == 0:
            self._state.update({"status": "NO_TRADE", "buy_cancel_requested": False})
            self._record(now, "buy_resolved_without_fill")
            return self.snapshot()
        if bool(self._state.get("buy_cancel_requested")):
            self._record(now, "buy_cancel_reconciliation_wait")
            return self.snapshot()
        elapsed = self._completed_bars_after_signal(now)
        if elapsed is None or self._state.get("status") == "BLOCKED":
            return self.snapshot()
        if elapsed < self.policy.entry_valid_completed_bars:
            self._record(now, "buy_open_wait", completed_bars_after_signal=elapsed)
            return self.snapshot()
        self._state["status"] = "BUY_CANCEL_SUBMITTING"
        self._record(now, "buy_cancel_intent", completed_bars_after_signal=elapsed)
        result = self.gateway.cancel_buy(order_no=order_no)
        if result.ambiguous:
            return self._block(now, "buy_cancel_ambiguous_reconciliation_required")
        if not result.accepted:
            self._state["status"] = "BUY_OPEN"
            self._record(
                now, "buy_cancel_rejected_retryable", return_code=result.return_code
            )
            return self.snapshot()
        self._state.update(
            {"status": "BUY_CANCEL_PENDING", "buy_cancel_requested": True}
        )
        self._own_order(result.order_no)
        self._record(now, "buy_cancel_submitted")
        return self.snapshot()

    def _consider_entry(self, now: datetime) -> dict:
        source = self._source(now)
        if not source.source_ok:
            self._state.update(
                {
                    "last_action": "sor_minute_source_wait",
                    "blocked_reason": source.error,
                }
            )
            self._save()
            return self.snapshot()
        if not source.bars:
            self._state.update(
                {
                    "last_action": "completed_sor_bar_wait",
                    "blocked_reason": source.error,
                }
            )
            self._save()
            return self.snapshot()
        latest = source.bars[-1]
        lag_minutes = int(
            (now.replace(second=0, microsecond=0) - latest.timestamp).total_seconds()
            // 60
        )
        if lag_minutes < 1 or lag_minutes > self.policy.max_source_lag_minutes:
            self._state.update(
                {
                    "last_action": "stale_or_incomplete_sor_bar_wait",
                    "blocked_reason": f"latest_completed_bar_lag:{lag_minutes}",
                }
            )
            self._save()
            return self.snapshot()
        latest_iso = latest.timestamp.isoformat()
        if self._state.get("last_evaluated_bar") == latest_iso:
            return self.snapshot()
        if latest.timestamp.time() > self.policy.scan_last_bar:
            self._state["status"] = "NO_TRADE"
            self._record(now, "afternoon_scan_window_closed")
            return self.snapshot()
        if latest.timestamp.time() < self.policy.scan_start:
            self._state.update(
                {
                    "last_action": "waiting_for_afternoon_scan_window",
                    "blocked_reason": "",
                }
            )
            self._save()
            return self.snapshot()
        self._state["last_evaluated_bar"] = latest_iso
        signal = self.policy.evaluate(list(source.bars))
        if signal is None:
            self._record(now, "bar_evaluated_no_signal", bar=latest_iso)
            return self.snapshot()
        source_owner = str(self.ownership_source(self.policy.symbol) or "")
        entry_price = signal.entry_price
        if not self.live_enabled:
            self._state.update(
                {
                    "last_action": "would_submit_sor_buy",
                    "blocked_reason": "live_authority_disabled",
                    "preview": {
                        "signal_bar": latest_iso,
                        "entry_price": entry_price,
                        "quantity": 1,
                        "operator_exclusion_ready": bool(source_owner),
                        "morning_relationship": "parallel_independent_strategy",
                        "widget_relationship": "parallel_independent_strategy",
                    },
                }
            )
            self._save()
            return self.snapshot()
        if not source_owner:
            self._state.update(
                {
                    "last_action": "operator_exclusion_required",
                    "blocked_reason": "005930_not_excluded_from_primary_bot",
                }
            )
            self._save()
            return self.snapshot()
        self._state.update(
            {
                "status": "BUY_SUBMITTING",
                "attempt_consumed": True,
                "signal_bar": latest_iso,
                "signal_close": latest.close_price,
                "entry_price": entry_price,
                "blocked_reason": "",
            }
        )
        self._record(
            now,
            "buy_submit_intent",
            signal_bar=latest_iso,
            entry_price=entry_price,
            drawdown_pct=signal.drawdown_pct,
            near_low_pct=signal.near_low_pct,
        )
        result = self.gateway.submit_limit_buy(price=entry_price)
        if result.ambiguous:
            return self._block(now, "buy_submit_ambiguous_reconciliation_required")
        if not result.accepted:
            self._state.update(
                {"status": "NO_TRADE", "blocked_reason": result.return_code}
            )
            self._record(now, "buy_submit_rejected", return_code=result.return_code)
            return self.snapshot()
        self._state.update(
            {
                "status": "BUY_OPEN",
                "buy_order_no": result.order_no,
                "buy_order_date": now.date().isoformat(),
            }
        )
        self._own_order(result.order_no)
        self._record(now, "buy_submitted", entry_price=entry_price)
        return self.snapshot()

    def run_once(self, now: datetime | None = None) -> dict:
        now = (now or datetime.now(tz=KST)).astimezone(KST)
        if self._state and self._state.get("status") == "BLOCKED":
            return self.snapshot()
        if self._state and not self._validate_state_contract(now):
            return self.snapshot()
        if not self._roll_date(now):
            return self.snapshot()
        if not self._validate_state_contract(now):
            return self.snapshot()
        status = str(self._state.get("status") or "")
        if status == "BLOCKED":
            return self.snapshot()
        if status in {"BUY_SUBMITTING", "BUY_CANCEL_SUBMITTING", "TARGET_SUBMITTING"}:
            return self._block(now, f"broker_write_interrupted:{status.lower()}")
        if status in {"BUY_OPEN", "BUY_CANCEL_PENDING"}:
            return self._reconcile_buy(now)
        if status == "POSITION_OPEN":
            return self._submit_target(now)
        if status == "TARGET_OPEN":
            return self._reconcile_target(now)
        if status in {"COMPLETE", "NO_TRADE", "HELD"} or bool(
            self._state.get("attempt_consumed")
        ):
            return self.snapshot()
        return self._consider_entry(now)

    def run_forever(self, *, interval_sec: float = 2.0) -> None:
        while True:
            self.run_once()
            time_module.sleep(max(0.2, float(interval_sec)))

    def run_until_terminal(self, *, interval_sec: float = 2.0) -> dict:
        while True:
            state = self.run_once()
            if state.get("status") in {"COMPLETE", "NO_TRADE", "HELD", "BLOCKED"}:
                return state
            time_module.sleep(max(0.2, float(interval_sec)))
