"""Persistent state machine for the independent Samsung morning two-leg episode."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable

from src.engine.risk.manual_control_exclusion import (
    manual_control_operator_exclusion_source,
)
from src.trading.order.episode_quantity import (
    EPISODE_LEG_QUANTITY,
    EPISODE_TOTAL_QUANTITY,
)
from src.trading.order.regular_two_leg_machine import KST, SamsungRegularTwoLegMachine
from src.trading.config.machine_entry_timing_policy import (
    ENTRY_CONFIRMATION_MAX_LATE_SEC,
    resolve_entry_confirmation_delay,
)
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
        "quantity": EPISODE_LEG_QUANTITY,
        "route": route,
        "status": "PLANNED",
        "buy_order_no": "",
        "buy_order_date": "",
        "buy_cancel_requested": False,
        "fill_price": 0,
        "buy_filled_at": "",
        "buy_filled_qty": 0,
        "position_qty": 0,
        "target_price": 0,
        "target_order_no": "",
        "target_order_date": "",
        "target_quantity": 0,
        "target_filled_qty": 0,
        "target_fill_price": 0,
        "target_filled_at": "",
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
            expected_order_qty=(
                int(leg.get("quantity", 0) or 0)
                if order_key == "buy_order_no"
                else int(leg.get("target_quantity", 0) or 0)
            ),
        )

    def _submit_target(self, now: datetime, leg: dict) -> None:
        if (
            int(leg.get("position_qty", 0) or 0) <= 0
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
            quantity=int(leg["position_qty"]),
        )
        target_quantity = int(leg["position_qty"])
        result = self.gateway.submit_limit_sell(
            route=str(leg["route"]), price=target_price, quantity=target_quantity
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
                "target_quantity": target_quantity,
            }
        )
        self._own_order(result.order_no)
        self._record(
            now,
            "target_submitted",
            leg_id=leg["leg_id"],
            route=leg["route"],
            target_price=target_price,
            quantity=target_quantity,
        )

    def _completed_bars_after_signal(self, now: datetime) -> int | None:
        return 0

    def _window(self, route: str) -> EntryWindow:
        return self.policy.nxt if route == "NXT" else self.policy.sor

    def _signal_features(
        self, *, route: str, signal_bar: object, open_price: int, plans: list[dict]
    ) -> dict:
        window = self._window(route)
        return {
            "schema": "samsung_morning_entry_signal_features_v1",
            "strategy": "morning",
            "source": f"kiwoom_005930_{route.lower()}_opening_price",
            "route": route,
            "routes": [route],
            "signal_bar": str(signal_bar),
            "opening_price": int(open_price),
            "opening_prices": {route: int(open_price)},
            "required_drawdown_pct": float(window.drawdown_pct),
            "required_drawdown_pct_by_route": {route: float(window.drawdown_pct)},
            "entry_window_start": window.open_time.isoformat(),
            "entry_window_deadline": window.deadline.isoformat(),
            "entry_windows": {
                route: {
                    "start": window.open_time.isoformat(),
                    "deadline": window.deadline.isoformat(),
                }
            },
            "target_ticks": int(self.policy.target_ticks),
            "runtime_policy_source": str(self.policy.runtime_policy_source),
            "runtime_policy_hash": str(self.policy.runtime_policy_hash),
            "entry_legs": [
                {
                    "leg_id": str(plan["leg_id"]),
                    "price_role": str(plan["price_role"]),
                    "entry_price": int(plan["entry_price"]),
                    "route": route,
                    "quantity": EPISODE_LEG_QUANTITY,
                }
                for plan in plans
            ],
        }

    def _move_to_sor(self, now: datetime, leg: dict) -> None:
        leg.update(
            {
                "route": "SOR",
                "status": "PLANNED",
                "entry_price": 0,
                "buy_order_no": "",
                "buy_order_date": "",
                "buy_cancel_requested": False,
                "buy_cancel_ambiguous": False,
                "buy_cancel_attempt_count": 0,
                "buy_cancel_attempted_at": "",
                "buy_cancel_terminal_failure": False,
                "buy_cancel_reason": "",
                "buy_cancel_provenance": {},
                "last_buy_reconciled_at": "",
                "last_buy_remaining_qty": 0,
                "last_buy_reconcile_source_ok": False,
            }
        )
        self._record(now, "nxt_leg_released_for_sor_fallback", leg_id=leg["leg_id"])

    def _submit_buy_cancel(self, leg: dict):
        return self.gateway.cancel(
            route=str(leg["route"]), order_no=str(leg["buy_order_no"])
        )

    def _buy_cancel_route_fields(self, leg: dict) -> dict[str, object]:
        return {"route": str(leg.get("route") or "")}

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
        if snapshot.found:
            leg["last_buy_reconciled_at"] = now.astimezone(KST).isoformat()
            leg["last_buy_remaining_qty"] = int(snapshot.remaining_qty)
            leg["last_buy_reconcile_source_ok"] = True
        if snapshot.found and snapshot.filled_qty > 0:
            if not snapshot.fill_price:
                self._block(now, f"buy_fill_price_missing:{leg['leg_id']}")
                return
            leg.update(
                {
                    "position_qty": snapshot.filled_qty,
                    "buy_filled_qty": snapshot.filled_qty,
                    "fill_price": snapshot.fill_price,
                    "buy_filled_at": now.astimezone(KST).isoformat(),
                    "status": (
                        "POSITION_OPEN"
                        if snapshot.remaining_qty == 0
                        else (
                            "BUY_CANCEL_PENDING"
                            if leg.get("buy_cancel_requested")
                            else "BUY_OPEN"
                        )
                    ),
                }
            )
            self._record(
                now,
                "buy_fill_confirmed",
                leg_id=leg["leg_id"],
                route=leg["route"],
                fill_price=snapshot.fill_price,
                filled_qty=snapshot.filled_qty,
                remaining_qty=snapshot.remaining_qty,
            )
            if snapshot.remaining_qty == 0:
                leg["buy_cancel_ambiguous"] = False
                self._submit_target(now, leg)
            elif not leg.get("buy_cancel_requested"):
                self._cancel_buy(
                    now,
                    leg,
                    0,
                    cancel_reason="partial_fill_remainder",
                )
            elif leg.get("buy_cancel_ambiguous"):
                self._cancel_buy(
                    now,
                    leg,
                    0,
                    cancel_reason=str(
                        leg.get("buy_cancel_reason") or "entry_validity_expired"
                    ),
                )
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
            if leg.get("buy_cancel_ambiguous"):
                self._cancel_buy(
                    now,
                    leg,
                    0,
                    cancel_reason=str(
                        leg.get("buy_cancel_reason") or "entry_validity_expired"
                    ),
                )
                return
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
        plan_list = self.policy.entry_legs(opening.price, self.policy.sor.drawdown_pct)
        plans = {plan["leg_id"]: plan for plan in plan_list}
        for pending_leg in self._state.get("legs", []):
            if (
                pending_leg.get("route") != "SOR"
                or pending_leg.get("status") != "PLANNED"
            ):
                continue
            plan = plans.get(str(pending_leg.get("leg_id") or ""))
            if plan:
                pending_leg["entry_price"] = int(plan["entry_price"])
        features = dict(self._state.get("signal_features") or {})
        opening_prices = dict(features.get("opening_prices") or {})
        opening_prices["SOR"] = int(opening.price)
        routes = sorted(
            {
                str(item.get("route") or "")
                for item in self._state.get("legs", [])
                if item.get("route")
            }
        )
        opening_prices = {
            route_name: value
            for route_name, value in opening_prices.items()
            if route_name in routes
        }
        entry_windows = {
            route_name: {
                "start": self._window(route_name).open_time.isoformat(),
                "deadline": self._window(route_name).deadline.isoformat(),
            }
            for route_name in routes
        }
        features.update(
            {
                "source": "kiwoom_005930_opening_prices",
                "route": routes[0] if len(routes) == 1 else "MIXED",
                "routes": routes,
                "opening_price": (int(opening.price) if routes == ["SOR"] else 0),
                "opening_prices": opening_prices,
                "required_drawdown_pct": (
                    float(self.policy.sor.drawdown_pct) if routes == ["SOR"] else None
                ),
                "required_drawdown_pct_by_route": {
                    route_name: float(self._window(route_name).drawdown_pct)
                    for route_name in routes
                },
                "entry_window_start": (
                    entry_windows[routes[0]]["start"] if len(routes) == 1 else ""
                ),
                "entry_window_deadline": (
                    entry_windows[routes[0]]["deadline"] if len(routes) == 1 else ""
                ),
                "entry_windows": entry_windows,
                "entry_legs": [
                    {
                        "leg_id": str(item.get("leg_id") or ""),
                        "price_role": str(item.get("price_role") or ""),
                        "entry_price": int(item.get("entry_price", 0) or 0),
                        "route": str(item.get("route") or ""),
                    }
                    for item in self._state.get("legs", [])
                ],
            }
        )
        self._state["signal_features"] = features
        if routes == ["SOR"]:
            self._state.update(
                {
                    "signal_bar": opening.source_timestamp,
                    "signal_close": int(opening.price),
                }
            )
        return True

    def _submit_planned_buys(self, now: datetime) -> None:
        if any(
            leg.get("status") == "PLANNED" for leg in self._state.get("legs", [])
        ) and not self._market_weakness_allows_new_buys(
            now=now,
            signal_bar=str(self._state.get("signal_bar") or ""),
        ):
            return
        approved_routes: set[str] = set()
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
            if route not in approved_routes:
                planned_quantity = sum(
                    int(planned_leg.get("quantity", 0) or 0)
                    for planned_leg in self._state.get("legs", [])
                    if planned_leg.get("status") == "PLANNED"
                    and str(planned_leg.get("route") or "").upper() == route
                )
                if not self._entry_liquidity_allows_planned_buys(
                    now=now,
                    route=route,
                    requested_quantity=planned_quantity,
                ):
                    return
                approved_routes.add(route)
            leg["status"] = "BUY_SUBMITTING"
            self._record(
                now,
                "buy_submit_intent",
                leg_id=leg["leg_id"],
                route=route,
                entry_price=leg["entry_price"],
                quantity=leg["quantity"],
            )
            result = self.gateway.submit_limit_buy(
                route=route,
                price=int(leg["entry_price"]),
                quantity=int(leg["quantity"]),
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
                quantity=leg["quantity"],
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
                        "total_quantity": EPISODE_TOTAL_QUANTITY,
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
        if not self._market_weakness_allows_new_buys(
            now=now,
            signal_bar=str(signal_bar),
            reference_price=int(open_price or 0),
            required_quantity=EPISODE_TOTAL_QUANTITY,
            expected_venues=[route],
            counterfactual_session=(
                "NXT_PREMARKET" if route == "NXT" else "KRX_REGULAR"
            ),
        ):
            return self.snapshot()
        timing_session = "NXT_PREMARKET" if route == "NXT" else "KRX_REGULAR"
        pending_confirmation = self._state.get("pending_entry_confirmation")
        confirmation_delay_sec = 0
        timing_policy_provenance: dict = {}
        signal_decision_at = now.isoformat()
        if isinstance(pending_confirmation, dict):
            same_signal = bool(
                pending_confirmation.get("signal_bar") == str(signal_bar)
                and int(pending_confirmation.get("signal_close") or 0) == open_price
                and pending_confirmation.get("route") == route
                and pending_confirmation.get("session") == timing_session
            )
            if not same_signal:
                self._state["pending_entry_confirmation"] = None
                self._record(
                    now,
                    "entry_confirmation_invalidated",
                    reason="opening_signal_no_longer_same",
                    prior_signal_bar=pending_confirmation.get("signal_bar"),
                    current_signal_bar=str(signal_bar),
                )
                return self.snapshot()
            due_at = datetime.fromisoformat(str(pending_confirmation["due_at"]))
            if now < due_at:
                self._state.update(
                    {"last_action": "entry_confirmation_wait", "blocked_reason": ""}
                )
                self._save()
                return self.snapshot()
            if now > due_at + timedelta(seconds=ENTRY_CONFIRMATION_MAX_LATE_SEC):
                self._state["pending_entry_confirmation"] = None
                self._record(
                    now,
                    "entry_confirmation_invalidated",
                    reason="confirmation_recheck_window_expired",
                    prior_signal_bar=pending_confirmation.get("signal_bar"),
                )
                return self.snapshot()
            confirmation_delay_sec = int(pending_confirmation["delay_sec"])
            timing_policy_provenance = dict(
                pending_confirmation.get("policy_provenance") or {}
            )
            active_delay, active_provenance = resolve_entry_confirmation_delay(
                target_date=now.date(),
                owner=self.entry_timing_owner,
                scope_id=self.entry_timing_scope_id,
                symbol=str(self.policy.symbol),
                session=timing_session,
                entry_state="UNSPECIFIED",
            )
            if (
                active_delay != confirmation_delay_sec
                or active_provenance.get("status") != "applied"
                or active_provenance.get("policy_hash")
                != timing_policy_provenance.get("policy_hash")
            ):
                self._state["pending_entry_confirmation"] = None
                self._record(
                    now,
                    "entry_confirmation_invalidated",
                    reason="entry_timing_policy_revalidation_failed",
                    active_policy_status=active_provenance.get("status"),
                )
                return self.snapshot()
            signal_decision_at = str(pending_confirmation["armed_at"])
        else:
            confirmation_delay_sec, timing_policy_provenance = (
                resolve_entry_confirmation_delay(
                    target_date=now.date(),
                    owner=self.entry_timing_owner,
                    scope_id=self.entry_timing_scope_id,
                    symbol=str(self.policy.symbol),
                    session=timing_session,
                    entry_state="UNSPECIFIED",
                )
            )
            if confirmation_delay_sec > 0:
                due_at = now + timedelta(seconds=confirmation_delay_sec)
                self._state["pending_entry_confirmation"] = {
                    "signal_bar": str(signal_bar),
                    "signal_close": open_price,
                    "route": route,
                    "session": timing_session,
                    "armed_at": signal_decision_at,
                    "due_at": due_at.isoformat(),
                    "delay_sec": confirmation_delay_sec,
                    "policy_provenance": timing_policy_provenance,
                }
                self._record(
                    now,
                    "entry_confirmation_armed",
                    route=route,
                    signal_bar=str(signal_bar),
                    delay_sec=confirmation_delay_sec,
                    due_at=due_at.isoformat(),
                    timing_policy_hash=timing_policy_provenance.get("policy_hash"),
                )
                return self.snapshot()
        signal_features = self._signal_features(
            route=route,
            signal_bar=signal_bar,
            open_price=open_price,
            plans=plans,
        )
        signal_features.update(
            {
                "signal_decision_at": signal_decision_at,
                "entry_confirmation_delay_sec": confirmation_delay_sec,
                "entry_timing_policy_provenance": timing_policy_provenance,
            }
        )
        self._state.update(
            {
                "attempt_consumed": True,
                "pending_entry_confirmation": None,
                "signal_bar": signal_bar,
                "signal_close": open_price,
                "signal_features": signal_features,
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
