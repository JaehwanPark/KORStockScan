"""Persistent state machine for the independent Samsung morning two-leg episode."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Callable

from src.engine.risk.manual_control_exclusion import (
    manual_control_operator_exclusion_source,
)
from src.trading.order.regular_two_leg_machine import KST, SamsungRegularTwoLegMachine
from src.trading.samsung_morning_one_share.policy import (
    DEFAULT_POLICY,
    EntryWindow,
    MorningOneSharePolicy,
)
from src.utils.constants import DATA_DIR

DEFAULT_STATE_PATH = DATA_DIR / "runtime" / "samsung_morning_one_share_state.json"


def _morning_leg(plan: dict, route: str) -> dict:
    return {
        **plan,
        "quantity": 1,
        "route": route,
        "status": "PLANNED",
        "buy_order_no": "",
        "buy_order_date": "",
        "buy_cancel_requested": False,
        "fill_price": 0,
        "buy_filled_at": "",
        "position_qty": 0,
        "target_price": 0,
        "target_order_no": "",
        "target_order_date": "",
        "target_filled_qty": 0,
    }


class SamsungMorningOneShareMachine(SamsungRegularTwoLegMachine):
    """Compatibility class name; runtime authority is two one-share legs."""

    LEG_IDS = ("base_plus_1tick", "base")

    def __init__(
        self,
        *,
        gateway,
        state_path: Path = DEFAULT_STATE_PATH,
        policy: MorningOneSharePolicy = DEFAULT_POLICY,
        live_enabled: bool = False,
        ownership_source: Callable[
            [object], str
        ] = manual_control_operator_exclusion_source,
    ) -> None:
        super().__init__(
            gateway=gateway,
            state_path=state_path,
            policy=policy,
            strategy_name="morning",
            schema="samsung_morning_two_leg_state_v2",
            legacy_schema="samsung_morning_one_share_state_v1",
            live_enabled=live_enabled,
            ownership_source=ownership_source,
        )

    def _validate_state_contract(self, now: datetime) -> bool:
        if not super()._validate_state_contract(now):
            return False
        for leg in self._state.get("legs", []):
            if leg.get("route") not in {"NXT", "SOR"}:
                self._block(now, "state_leg_route_invalid")
                return False
        return True

    def _execution(self, leg: dict, order_key: str):
        order_no = str(leg.get(order_key) or "")
        if not self._owns_order(order_no):
            raise ValueError(f"{order_key}_not_owned")
        date_key = (
            "buy_order_date" if order_key == "buy_order_no" else "target_order_date"
        )
        return self.gateway.execution_snapshot(
            route=str(leg["route"]),
            order_no=order_no,
            order_date=str(leg.get(date_key) or ""),
        )

    def _submit_target(self, now: datetime, leg: dict) -> None:
        if (
            int(leg.get("position_qty", 0) or 0) != 1
            or int(leg.get("fill_price", 0) or 0) <= 0
        ):
            self._block(now, f"target_requires_confirmed_leg_fill:{leg.get('leg_id')}")
            return
        leg["status"] = "TARGET_SUBMITTING"
        target_price = self.policy.target_price(int(leg["fill_price"]))
        self._record(
            now,
            "target_submit_intent",
            leg_id=leg["leg_id"],
            route=leg["route"],
            target_price=target_price,
        )
        result = self.gateway.submit_limit_sell(
            route=str(leg["route"]), price=target_price
        )
        if result.ambiguous:
            self._block(now, f"target_submit_ambiguous:{leg['leg_id']}")
            return
        if not result.accepted:
            leg["status"] = "POSITION_OPEN"
            self._record(
                now,
                "target_submit_rejected_retryable",
                leg_id=leg["leg_id"],
                return_code=result.return_code,
            )
            return
        leg.update(
            {
                "status": "TARGET_OPEN",
                "target_price": target_price,
                "target_order_no": result.order_no,
                "target_order_date": now.date().isoformat(),
            }
        )
        self._own_order(result.order_no)
        self._record(
            now,
            "target_submitted",
            leg_id=leg["leg_id"],
            route=leg["route"],
            target_price=target_price,
        )

    def _completed_bars_after_signal(self, now: datetime) -> int | None:
        return 0

    def _window(self, route: str) -> EntryWindow:
        return self.policy.nxt if route == "NXT" else self.policy.sor

    def _move_to_sor(self, now: datetime, leg: dict) -> None:
        leg.update(
            {
                "route": "SOR",
                "status": "PLANNED",
                "entry_price": 0,
                "buy_order_no": "",
                "buy_order_date": "",
                "buy_cancel_requested": False,
            }
        )
        self._record(now, "nxt_leg_released_for_sor_fallback", leg_id=leg["leg_id"])

    def _cancel_buy(self, now: datetime, leg: dict, elapsed: int) -> None:
        leg["status"] = "BUY_CANCEL_SUBMITTING"
        self._record(now, "buy_cancel_intent", leg_id=leg["leg_id"], route=leg["route"])
        result = self.gateway.cancel(
            route=str(leg["route"]), order_no=str(leg["buy_order_no"])
        )
        if result.ambiguous:
            self._block(now, f"buy_cancel_ambiguous:{leg['leg_id']}")
            return
        if not result.accepted:
            leg["status"] = "BUY_OPEN"
            self._record(
                now,
                "buy_cancel_rejected_retryable",
                leg_id=leg["leg_id"],
                return_code=result.return_code,
            )
            return
        leg.update({"status": "BUY_CANCEL_PENDING", "buy_cancel_requested": True})
        self._own_order(result.order_no)
        self._record(
            now, "buy_cancel_submitted", leg_id=leg["leg_id"], route=leg["route"]
        )

    def _reconcile_buy(self, now: datetime, leg: dict, elapsed: int | None) -> None:
        try:
            snapshot = self._execution(leg, "buy_order_no")
        except ValueError:
            self._block(now, f"buy_order_not_owned:{leg.get('leg_id')}")
            return
        if not snapshot.source_ok:
            self._record(
                now,
                "buy_reconciliation_wait",
                leg_id=leg["leg_id"],
                error=snapshot.error,
            )
            return
        if snapshot.found and snapshot.filled_qty == 1:
            if not snapshot.fill_price:
                self._block(now, f"buy_fill_price_missing:{leg['leg_id']}")
                return
            leg.update(
                {
                    "position_qty": 1,
                    "fill_price": snapshot.fill_price,
                    "buy_filled_at": now.astimezone(KST).isoformat(),
                    "status": "POSITION_OPEN",
                }
            )
            self._record(
                now,
                "buy_fill_confirmed",
                leg_id=leg["leg_id"],
                route=leg["route"],
                fill_price=snapshot.fill_price,
            )
            self._submit_target(now, leg)
            return
        if snapshot.found and snapshot.filled_qty == 0 and snapshot.remaining_qty == 0:
            if leg["route"] == "NXT":
                self._move_to_sor(now, leg)
            else:
                leg.update({"status": "NO_FILL", "buy_cancel_requested": False})
                self._record(
                    now, "buy_resolved_without_fill", leg_id=leg["leg_id"], route="SOR"
                )
            return
        deadline = self._window(str(leg["route"])).deadline
        if leg.get("buy_cancel_requested"):
            self._record(now, "buy_cancel_reconciliation_wait", leg_id=leg["leg_id"])
        elif now.time() >= deadline:
            self._cancel_buy(now, leg, 0)
        else:
            self._record(now, "buy_open_wait", leg_id=leg["leg_id"], route=leg["route"])

    def _price_sor_leg(self, now: datetime, leg: dict) -> bool:
        opening = self.gateway.opening_price(route="SOR", trade_date=now.date())
        if not opening.source_ok or not opening.price:
            self._record(
                now, "sor_open_price_wait", leg_id=leg["leg_id"], error=opening.error
            )
            return False
        plans = {
            plan["leg_id"]: plan
            for plan in self.policy.entry_legs(
                opening.price, self.policy.sor.drawdown_pct
            )
        }
        leg["entry_price"] = int(plans[str(leg["leg_id"])]["entry_price"])
        return True

    def _submit_planned_buys(self, now: datetime) -> None:
        for leg in self._state.get("legs", []):
            if leg.get("status") != "PLANNED" or self._state.get("status") == "BLOCKED":
                continue
            route = str(leg["route"])
            window = self._window(route)
            if now.time() < window.open_time:
                continue
            if now.time() >= window.deadline:
                leg["status"] = "NO_FILL"
                self._record(
                    now,
                    "entry_window_elapsed_without_submit",
                    leg_id=leg["leg_id"],
                    route=route,
                )
                continue
            if (
                route == "SOR"
                and int(leg.get("entry_price", 0) or 0) <= 0
                and not self._price_sor_leg(now, leg)
            ):
                continue
            leg["status"] = "BUY_SUBMITTING"
            self._record(
                now,
                "buy_submit_intent",
                leg_id=leg["leg_id"],
                route=route,
                entry_price=leg["entry_price"],
            )
            result = self.gateway.submit_limit_buy(
                route=route, price=int(leg["entry_price"])
            )
            if result.ambiguous:
                self._block(now, f"buy_submit_ambiguous:{leg['leg_id']}")
                return
            if not result.accepted:
                leg["status"] = "NO_FILL"
                self._record(
                    now,
                    "buy_submit_rejected",
                    leg_id=leg["leg_id"],
                    route=route,
                    return_code=result.return_code,
                )
                continue
            leg.update(
                {
                    "status": "BUY_OPEN",
                    "buy_order_no": result.order_no,
                    "buy_order_date": now.date().isoformat(),
                }
            )
            self._own_order(result.order_no)
            self._record(
                now,
                "buy_submitted",
                leg_id=leg["leg_id"],
                route=route,
                entry_price=leg["entry_price"],
            )

    def _consider_entry(self, now: datetime) -> dict:
        if now.time() < self.policy.nxt.open_time:
            self._state.update(
                {"last_action": "waiting_for_nxt_premarket", "blocked_reason": ""}
            )
            self._save()
            return self.snapshot()
        if now.time() >= self.policy.sor.deadline:
            self._state["status"] = "NO_TRADE"
            self._record(now, "morning_scan_window_closed")
            return self.snapshot()
        source_owner = str(self.ownership_source(self.policy.symbol) or "")
        route = "NXT" if now.time() < self.policy.nxt.deadline else "SOR"
        opening = None
        if route == "NXT" or now.time() >= self.policy.sor.open_time:
            opening = self.gateway.opening_price(route=route, trade_date=now.date())
            if not opening.source_ok or not opening.price:
                self._state.update(
                    {
                        "last_action": f"{route.lower()}_open_price_wait",
                        "blocked_reason": opening.error,
                    }
                )
                self._save()
                return self.snapshot()
            window = self._window(route)
            plans = self.policy.entry_legs(opening.price, window.drawdown_pct)
            open_price = opening.price
            signal_bar = opening.source_timestamp
        else:
            plans = [
                {
                    "leg_id": "base_plus_1tick",
                    "price_role": "aggressive_50pct",
                    "entry_price": 0,
                },
                {
                    "leg_id": "base",
                    "price_role": "conservative_50pct",
                    "entry_price": 0,
                },
            ]
            open_price = 0
            signal_bar = now.isoformat()
        if not self.live_enabled:
            self._state.update(
                {
                    "last_action": f"would_submit_{route.lower()}_two_leg_buy",
                    "blocked_reason": "live_authority_disabled",
                    "preview": {
                        "route": route,
                        "open_price": open_price,
                        "total_quantity": 2,
                        "legs": plans,
                        "operator_exclusion_ready": bool(source_owner),
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
                "attempt_consumed": True,
                "signal_bar": signal_bar,
                "signal_close": open_price,
                "legs": [_morning_leg(plan, route) for plan in plans],
                "blocked_reason": "",
            }
        )
        self._sync_aggregate()
        self._record(
            now, "morning_two_leg_entry_armed", route=route, open_price=open_price
        )
        self._submit_planned_buys(now)
        self._sync_aggregate()
        self._save()
        return self.snapshot()
