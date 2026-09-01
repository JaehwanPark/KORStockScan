"""Exact-date 100-share manual BUY add-on mirroring the morning episode.

The normal episode quantity remains independently configured. This process follows only
the normal machine's accepted BUY legs, places two separate 50-share BUY orders
at the same prices/routes, cancels only its own remaining quantity, and never
submits a SELL. Any filled add-on quantity is handed to the operator.
"""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import tempfile
import time as time_module
from datetime import date, datetime, time
from pathlib import Path

from src.engine.risk.manual_control_exclusion import (
    manual_control_operator_exclusion_source,
)
from src.trading.samsung_morning_one_share.gateway import KiwoomOneShareGateway
from src.trading.samsung_morning_one_share.machine import (
    DEFAULT_STATE_PATH as SOURCE_STATE_PATH,
    KST,
)
from src.trading.samsung_morning_one_share.preflight import (
    DEFAULT_AUTHORITY_PATH,
    validate_authority,
)
from src.utils.constants import DATA_DIR

TARGET_DATE = date(2026, 8, 13)
SYMBOL = "005930"
TOTAL_QUANTITY = 100
LEG_QUANTITY = 50
LEG_IDS = ("base_plus_1tick", "base")
ACTIVE_SOURCE_EPISODE_STATUSES = {
    "BUY_OPEN",
    "BUY_CANCEL_PENDING",
    "TARGET_SUBMITTING",
    "TARGET_OPEN",
    "HELD",
}
ACTIVE_SOURCE_LEG_STATUSES = {
    "BUY_OPEN",
    "POSITION_OPEN",
    "TARGET_SUBMITTING",
    "TARGET_OPEN",
    "HELD",
}
NXT_DEADLINE = time(8, 10)
SOR_DEADLINE = time(9, 30)
STATE_PATH = DATA_DIR / "runtime" / "samsung_morning_manual_addon_2026-08-13.json"
LOCK_PATH = STATE_PATH.with_suffix(".lock")
ENABLE_ENV = "KORSTOCKSCAN_SAMSUNG_MORNING_MANUAL_ADDON_20260813_ENABLED"
LIVE_CONFIRMATION = "005930_MORNING_MANUAL_ADDON_100_20260813"
SCHEMA = "samsung_morning_manual_addon_v1"


def _iso(now: datetime) -> str:
    return now.astimezone(KST).isoformat()


def _fresh_state(now: datetime) -> dict:
    return {
        "schema": SCHEMA,
        "target_date": TARGET_DATE.isoformat(),
        "status": "READY",
        "symbol": SYMBOL,
        "total_requested_quantity": TOTAL_QUANTITY,
        "total_filled_quantity": 0,
        "manual_sell_required_quantity": 0,
        "sell_authority": "operator_only_no_machine_sell",
        "source_state_path": str(SOURCE_STATE_PATH),
        "owned_order_nos": [],
        "blocked_reason": "",
        "last_action": "initialized",
        "legs": {
            leg_id: {
                "leg_id": leg_id,
                "requested_quantity": LEG_QUANTITY,
                "filled_quantity": 0,
                "attempts": {},
            }
            for leg_id in LEG_IDS
        },
        "audit": [{"at_kst": _iso(now), "action": "initialized"}],
    }


class SamsungMorningManualAddon:
    def __init__(self, *, gateway, state_path: Path = STATE_PATH) -> None:
        self.gateway = gateway
        self.state_path = Path(state_path)
        self.state = self._load()

    def _load(self) -> dict:
        try:
            payload = json.loads(self.state_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return _fresh_state(datetime.now(tz=KST))
        except (OSError, json.JSONDecodeError) as exc:
            payload = _fresh_state(datetime.now(tz=KST))
            payload.update(
                status="BLOCKED",
                blocked_reason=f"state_unreadable:{type(exc).__name__}",
            )
            return payload
        if (
            not isinstance(payload, dict)
            or payload.get("schema") != SCHEMA
            or payload.get("target_date") != TARGET_DATE.isoformat()
            or payload.get("symbol") != SYMBOL
            or payload.get("total_requested_quantity") != TOTAL_QUANTITY
            or set((payload.get("legs") or {})) != set(LEG_IDS)
            or any(
                not isinstance(leg, dict)
                for leg in (payload.get("legs") or {}).values()
            )
            or any(
                leg.get("requested_quantity") != LEG_QUANTITY
                for leg in (payload.get("legs") or {}).values()
            )
        ):
            payload = _fresh_state(datetime.now(tz=KST))
            payload.update(status="BLOCKED", blocked_reason="state_contract_invalid")
            return payload
        for leg in payload["legs"].values():
            for attempt in (leg.get("attempts") or {}).values():
                if attempt.get("status") in {"SUBMITTING", "CANCEL_SUBMITTING"}:
                    payload.update(
                        status="BLOCKED",
                        blocked_reason=(
                            f"broker_write_interrupted:{leg['leg_id']}:"
                            f"{attempt.get('route')}:{attempt.get('status')}"
                        ),
                    )
                    return payload
        return payload

    def _save(self) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(
            prefix=f".{self.state_path.name}.", dir=self.state_path.parent
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(
                    self.state, handle, ensure_ascii=False, indent=2, sort_keys=True
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
        self.state["last_action"] = action
        audit = list(self.state.get("audit") or [])
        audit.append({"at_kst": _iso(now), "action": action, **fields})
        self.state["audit"] = audit[-100:]
        self._sync_totals()
        self._save()

    def _block(self, now: datetime, reason: str) -> None:
        self.state.update(status="BLOCKED", blocked_reason=reason)
        self._record(now, "blocked", reason=reason)

    def _sync_totals(self) -> None:
        filled = sum(
            int(leg.get("filled_quantity", 0) or 0)
            for leg in self.state["legs"].values()
        )
        self.state["total_filled_quantity"] = filled
        self.state["manual_sell_required_quantity"] = filled

    @staticmethod
    def _read_source() -> dict | None:
        try:
            payload = json.loads(SOURCE_STATE_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if (
            not isinstance(payload, dict)
            or payload.get("schema") != "samsung_morning_two_leg_state_v2"
            or payload.get("trade_date") != TARGET_DATE.isoformat()
        ):
            return None
        legs = payload.get("legs")
        if (
            not isinstance(legs, list)
            or len(legs) != 2
            or any(not isinstance(leg, dict) for leg in legs)
        ):
            return None
        if {str(leg.get("leg_id") or "") for leg in legs} != set(LEG_IDS):
            return None
        owned = payload.get("owned_order_nos")
        if not isinstance(owned, list) or any(
            not isinstance(order_no, str) or not order_no.strip() for order_no in owned
        ):
            return None
        return payload

    def _submit(
        self,
        now: datetime,
        *,
        leg: dict,
        route: str,
        price: int,
        quantity: int,
        source_order_no: str,
    ) -> None:
        attempts = leg.setdefault("attempts", {})
        attempt = {
            "route": route,
            "price": int(price),
            "requested_quantity": int(quantity),
            "filled_quantity": 0,
            "remaining_quantity": int(quantity),
            "status": "SUBMITTING",
            "order_no": "",
            "order_date": TARGET_DATE.isoformat(),
            "cancel_order_no": "",
            "source_order_no": str(source_order_no),
        }
        attempts[route] = attempt
        self._record(
            now,
            "manual_addon_buy_submit_intent",
            leg_id=leg["leg_id"],
            route=route,
            price=price,
            quantity=quantity,
            source_order_no=source_order_no,
        )
        result = self.gateway.submit_manual_addon_limit_buy(
            route=route, price=price, quantity=quantity
        )
        if result.ambiguous:
            self._block(now, f"buy_submit_ambiguous:{leg['leg_id']}:{route}")
            return
        if not result.accepted:
            attempt.update(status="REJECTED", remaining_quantity=0)
            self._record(
                now,
                "manual_addon_buy_rejected",
                leg_id=leg["leg_id"],
                route=route,
                return_code=result.return_code,
            )
            return
        attempt.update(status="OPEN", order_no=result.order_no)
        owned = set(self.state.get("owned_order_nos") or [])
        owned.add(result.order_no)
        self.state["owned_order_nos"] = sorted(owned)
        self._record(
            now,
            "manual_addon_buy_submitted",
            leg_id=leg["leg_id"],
            route=route,
            price=price,
            quantity=quantity,
            order_no=result.order_no,
        )

    def _cancel(self, now: datetime, *, leg: dict, attempt: dict) -> None:
        if attempt.get("order_no") not in set(self.state.get("owned_order_nos") or []):
            self._block(
                now, f"cancel_order_not_owned:{leg['leg_id']}:{attempt['route']}"
            )
            return
        attempt["status"] = "CANCEL_SUBMITTING"
        self._record(
            now,
            "manual_addon_cancel_intent",
            leg_id=leg["leg_id"],
            route=attempt["route"],
            order_no=attempt["order_no"],
        )
        result = self.gateway.cancel_manual_addon_remaining(
            route=attempt["route"], order_no=attempt["order_no"]
        )
        if result.ambiguous:
            self._block(now, f"cancel_ambiguous:{leg['leg_id']}:{attempt['route']}")
            return
        if not result.accepted:
            attempt.update(
                status="OPEN",
                cancel_retry_after_epoch=now.timestamp() + 5.0,
            )
            self._record(
                now,
                "manual_addon_cancel_rejected_retryable",
                leg_id=leg["leg_id"],
                route=attempt["route"],
                return_code=result.return_code,
            )
            return
        attempt.update(status="CANCEL_PENDING", cancel_order_no=result.order_no)
        owned = set(self.state.get("owned_order_nos") or [])
        owned.add(result.order_no)
        self.state["owned_order_nos"] = sorted(owned)
        self._record(
            now,
            "manual_addon_cancel_submitted",
            leg_id=leg["leg_id"],
            route=attempt["route"],
        )

    def _reconcile(self, now: datetime, *, leg: dict, attempt: dict) -> None:
        order_no = str(attempt.get("order_no") or "")
        if order_no not in set(self.state.get("owned_order_nos") or []):
            self._block(now, f"buy_order_not_owned:{leg['leg_id']}:{attempt['route']}")
            return
        requested = int(attempt["requested_quantity"])
        snap = self.gateway.manual_addon_execution_snapshot(
            route=attempt["route"],
            order_no=order_no,
            order_date=attempt["order_date"],
            expected_order_qty=requested,
        )
        if not snap.source_ok or not snap.found:
            self._record(
                now,
                "manual_addon_reconciliation_wait",
                leg_id=leg["leg_id"],
                route=attempt["route"],
                error=snap.error,
            )
            return
        filled = int(snap.filled_qty)
        remaining = int(snap.remaining_qty)
        if (
            snap.order_qty != requested
            or filled < int(attempt.get("filled_quantity", 0) or 0)
            or filled + remaining > requested
        ):
            self._block(
                now,
                f"execution_quantity_contract_invalid:{leg['leg_id']}:{attempt['route']}",
            )
            return
        attempt.update(filled_quantity=filled, remaining_quantity=remaining)
        leg["filled_quantity"] = sum(
            int(item.get("filled_quantity", 0) or 0)
            for item in leg.get("attempts", {}).values()
        )
        if remaining == 0:
            attempt["status"] = "FILLED" if filled == requested else "CLOSED"
        self._sync_totals()
        self._save()

    def run_once(self, now: datetime | None = None) -> dict:
        now = (now or datetime.now(tz=KST)).astimezone(KST)
        if now.date() != TARGET_DATE:
            if self.state.get("status") not in {"COMPLETE", "NO_FILL", "BLOCKED"}:
                self._block(now, "exact_date_authority_expired")
            return json.loads(json.dumps(self.state))
        if self.state.get("status") in {"COMPLETE", "NO_FILL", "BLOCKED"}:
            return json.loads(json.dumps(self.state))
        source = self._read_source()
        source_legs = {leg["leg_id"]: leg for leg in source["legs"]} if source else {}
        source_allows_new_orders = bool(
            source is not None
            and source.get("status") in ACTIVE_SOURCE_EPISODE_STATUSES
        )
        self.state["status"] = "RUNNING"
        for leg_id in LEG_IDS:
            if self.state.get("status") == "BLOCKED":
                break
            leg = self.state["legs"][leg_id]
            source_leg = source_legs.get(leg_id, {})
            for attempt in list(leg.get("attempts", {}).values()):
                if attempt.get("status") in {"OPEN", "CANCEL_PENDING"}:
                    self._reconcile(now, leg=leg, attempt=attempt)
            if self.state.get("status") == "BLOCKED":
                break
            nxt = leg.get("attempts", {}).get("NXT")
            if (
                nxt
                and nxt.get("status") == "OPEN"
                and now.time() >= NXT_DEADLINE
                and now.timestamp()
                >= float(nxt.get("cancel_retry_after_epoch", 0.0) or 0.0)
            ):
                self._cancel(now, leg=leg, attempt=nxt)
            sor = leg.get("attempts", {}).get("SOR")
            if (
                sor
                and sor.get("status") == "OPEN"
                and now.time() >= SOR_DEADLINE
                and now.timestamp()
                >= float(sor.get("cancel_retry_after_epoch", 0.0) or 0.0)
            ):
                self._cancel(now, leg=leg, attempt=sor)
            route = str(source_leg.get("route") or "")
            source_order_no = str(source_leg.get("buy_order_no") or "")
            source_leg_status = str(source_leg.get("status") or "")
            price = int(source_leg.get("entry_price", 0) or 0)
            source_owned_order_nos = (
                set(source.get("owned_order_nos") or []) if source else set()
            )
            if (
                not source_allows_new_orders
                or route not in {"NXT", "SOR"}
                or not source_order_no
                or source_order_no not in source_owned_order_nos
                or source_leg_status not in ACTIVE_SOURCE_LEG_STATUSES
                or price <= 0
            ):
                continue
            if (
                route == "NXT"
                and now.time() < NXT_DEADLINE
                and "NXT" not in leg.get("attempts", {})
            ):
                self._submit(
                    now,
                    leg=leg,
                    route="NXT",
                    price=price,
                    quantity=LEG_QUANTITY,
                    source_order_no=source_order_no,
                )
            elif route == "SOR" and "SOR" not in leg.get("attempts", {}):
                nxt = leg.get("attempts", {}).get("NXT")
                if nxt and int(nxt.get("remaining_quantity", 0) or 0) > 0:
                    continue
                remaining = LEG_QUANTITY - int(leg.get("filled_quantity", 0) or 0)
                if remaining > 0 and now.time() < SOR_DEADLINE:
                    self._submit(
                        now,
                        leg=leg,
                        route="SOR",
                        price=price,
                        quantity=remaining,
                        source_order_no=source_order_no,
                    )
        all_attempts = [
            attempt
            for leg in self.state["legs"].values()
            for attempt in leg.get("attempts", {}).values()
        ]
        if now.time() >= SOR_DEADLINE and all(
            item.get("status") in {"FILLED", "CLOSED", "REJECTED"}
            for item in all_attempts
        ):
            self._sync_totals()
            self.state["status"] = (
                "COMPLETE" if self.state["total_filled_quantity"] else "NO_FILL"
            )
            self._record(now, "manual_addon_terminal_operator_handoff")
        elif source is None and not all_attempts:
            self._record(now, "waiting_for_source_episode")
        else:
            self._sync_totals()
            self._save()
        return json.loads(json.dumps(self.state))

    def run_until_terminal(self, *, interval_sec: float = 2.0) -> dict:
        while True:
            state = self.run_once()
            if state.get("status") in {"COMPLETE", "NO_FILL", "BLOCKED"}:
                return state
            time_module.sleep(max(0.1, float(interval_sec)))


def _acquire_lock(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = path.open("a+", encoding="utf-8")
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        handle.close()
        return None
    handle.seek(0)
    handle.truncate()
    handle.write(str(os.getpid()))
    handle.flush()
    return handle


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--confirm", default="")
    parser.add_argument("--interval-sec", type=float, default=2.0)
    args = parser.parse_args(argv)
    enabled = str(os.getenv(ENABLE_ENV, "false")).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    if not (args.live and enabled and args.confirm == LIVE_CONFIRMATION):
        raise SystemExit(
            f"live authority requires {ENABLE_ENV}=true and --confirm {LIVE_CONFIRMATION}"
        )
    now = datetime.now(tz=KST)
    if now.date() != TARGET_DATE:
        raise SystemExit("exact-date manual add-on authority expired")
    authority_ok, authority_reason = validate_authority(
        DEFAULT_AUTHORITY_PATH,
        now=now,
        require_live_main_bot_runtime=True,
    )
    if not authority_ok:
        print(f"manual add-on blocked by morning authority: {authority_reason}")
        return 4
    if manual_control_operator_exclusion_source(SYMBOL) != "manual_operator":
        print("manual add-on blocked: manual_operator owner missing")
        return 5
    lock = _acquire_lock(LOCK_PATH)
    if lock is None:
        return 3
    gateway = KiwoomOneShareGateway(order_authority=True)
    machine = SamsungMorningManualAddon(gateway=gateway)
    print(
        json.dumps(
            machine.run_until_terminal(interval_sec=args.interval_sec),
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
