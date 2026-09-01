from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.trading.order.entry_liquidity_guard import (
    EntryExecutionVelocitySnapshot,
    EntryLiquiditySnapshot,
)

from src.engine.monitoring.samsung_widget_contract import KST
from src.engine.risk.market_weakness_entry_guard import (
    MarketWeaknessEntryDecision,
)
from src.trading.widget_auto_trade import engine
from src.trading.widget_auto_trade.engine import WidgetSignalAutoTrader, WidgetSpec
from src.trading.widget_auto_trade.gateway import ExecutionSnapshot, SubmitResult
from src.trading.widget_auto_trade import gateway as gateway_module
from src.trading.widget_auto_trade import service as service_module


@pytest.fixture(autouse=True)
def _isolate_market_weakness_counterfactual_writer(monkeypatch):
    monkeypatch.setattr(
        engine,
        "record_market_weakness_blocked_entry",
        lambda *_args, **_kwargs: {
            "status": "test_isolated",
            "observation_id": "test-market-weakness-block",
            "path": "test-only",
        },
    )


class FakeContract:
    STRATEGY_PROFILE = "TEST_WIDGET_V1"

    @staticmethod
    def session_context(observed_at):
        return SimpleNamespace(active=True, market_venue="KRX", name="KRX_REGULAR")

    @staticmethod
    def snapshot_is_fresh(payload, *, now):
        observed = datetime.fromisoformat(payload["observed_at_kst"])
        return 0 <= (now - observed).total_seconds() <= 30

    @staticmethod
    def advisory_event_contract_is_valid(event, *, expected_type, evaluated_at):
        return bool(
            event.get("valid") is True
            and event.get("event_type") == expected_type
            and event.get("event_id")
        )


class FakeSamsungContractWithoutTopLevelProfile:
    @staticmethod
    def session_context(observed_at):
        return SimpleNamespace(active=True, market_venue="KRX", name="KRX_REGULAR")

    @staticmethod
    def snapshot_is_fresh(payload, *, now):
        return True

    @staticmethod
    def advisory_contract_is_valid(
        advisory, *, snapshot_observed_at, context, evaluated_at
    ):
        return isinstance(advisory, dict) and advisory.get("valid") is True


class FakeSnapshotTimeContract(FakeContract):
    """Mirror the Doosan/Hanwha snapshot-time keyword contract."""

    @staticmethod
    def advisory_contract_is_valid(advisory, *, snapshot_time, context, evaluated_at):
        return bool(
            isinstance(advisory, dict)
            and advisory.get("valid") is True
            and snapshot_time <= evaluated_at
            and context.name == "KRX_REGULAR"
        )


@dataclass
class FakeRecorder:
    events: list

    def record(self, event, observed_at):
        self.events.append(event)


class FakeGateway:
    def __init__(self):
        self.buy_calls = []
        self.sell_calls = []
        self.limit_sell_calls = []
        self.cancel_calls = []
        self.snapshots = {}
        self.sequence = 0
        self.best_bid_qty = 1_000
        self.best_ask_qty = 1_000
        self.liquidity_calls = []
        self.execution_velocity_span_ms = 1_000
        self.execution_velocity_latest_age_ms = 0
        self.execution_velocity_recent_volume = 1_000
        self.execution_velocity_calls = []

    def _accepted(self, prefix):
        self.sequence += 1
        return SubmitResult(True, f"{prefix}{self.sequence}", "0", "OK")

    def entry_liquidity_snapshot(self, *, code, route):
        self.liquidity_calls.append((code, route))
        suffix = "NX" if route == "NXT" else "AL"
        return EntryLiquiditySnapshot(
            True,
            code,
            route,
            f"{code}_{suffix}",
            best_bid=100_000,
            best_ask=100_100,
            best_bid_qty=self.best_bid_qty,
            best_ask_qty=self.best_ask_qty,
            age_ms=0,
            received_ts_ms=1,
        )

    def entry_execution_velocity_snapshot(self, *, code, route):
        self.execution_velocity_calls.append((code, route))
        suffix = "NX" if route == "NXT" else "AL"
        return EntryExecutionVelocitySnapshot(
            True,
            code,
            route,
            f"{code}_{suffix}",
            print_count=10,
            recent_print_span_ms=self.execution_velocity_span_ms,
            latest_print_age_ms=self.execution_velocity_latest_age_ms,
            recent_volume=self.execution_velocity_recent_volume,
            observed_at_kst="2026-08-12T09:30:00+09:00",
            print_times=("093000",) * 10,
            venues=(("NXT",) * 10 if route == "NXT" else ("KRX",) * 10),
        )

    def submit_buy(self, *, code, qty, route):
        self.buy_calls.append((code, qty, route))
        return self._accepted("B")

    def submit_sell(self, *, code, qty, route):
        self.sell_calls.append((code, qty, route))
        return self._accepted("S")

    def submit_limit_sell(self, *, code, qty, route, price):
        self.limit_sell_calls.append((code, qty, route, price))
        return self._accepted("L")

    def cancel(self, *, code, order_no, qty, route):
        self.cancel_calls.append((code, order_no, qty, route))
        return self._accepted("C")

    def execution_snapshot(self, *, code, order_no, route, order_date):
        return self.snapshots.get(order_no, ExecutionSnapshot(True, False, 0, 0, 0))


class RejectFirstBuyGateway(FakeGateway):
    def __init__(self):
        super().__init__()
        self.reject_next_buy = True

    def submit_buy(self, *, code, qty, route):
        self.buy_calls.append((code, qty, route))
        if self.reject_next_buy:
            self.reject_next_buy = False
            return SubmitResult(False, "", "20", "insufficient margin")
        return self._accepted("B")


class FakeEntryActionNotifier:
    def __init__(self, result="sent"):
        self.result = result
        self.calls = []

    def notify_order_accepted(self, **kwargs):
        self.calls.append(kwargs)
        return self.result


def _at(day: int, hour: int = 10, minute: int = 0, second: int = 0):
    return datetime(2026, 8, day, hour, minute, second, tzinfo=KST)


def _payload(now, *, entry_id=None, entry_state="ENTRY_CAUTION", exit_id=None):
    return {
        "status": "ok",
        "symbol": "999999",
        "market_venue": "KRX",
        "strategy_profile": FakeContract.STRATEGY_PROFILE,
        "observed_at_kst": now.isoformat(),
        "advisory": {},
        "entry_event": (
            {
                "valid": True,
                "event_type": "ENTRY",
                "event_id": entry_id,
                "state": entry_state,
            }
            if entry_id
            else None
        ),
        "exit_event": (
            {"valid": True, "event_type": "EXIT", "event_id": exit_id}
            if exit_id
            else None
        ),
    }


def _market_weakness_decision(now, *, mode: str):
    if mode == "active":
        reason = "entry_blocked_market_weakness_active"
        blocked = True
        listing_market = "KOSPI"
        active_markets = ("KOSPI",)
    elif mode == "invalid_scope":
        reason = "entry_blocked_market_weakness_state_invalid"
        blocked = True
        listing_market = "KOSPI"
        active_markets = ()
    else:
        reason = "market_weakness_latch_not_active"
        blocked = False
        listing_market = "KOSPI"
        active_markets = ()
    return MarketWeaknessEntryDecision(
        blocked=blocked,
        reason=reason,
        symbol="999999",
        owner="widget",
        listing_market=listing_market,
        phase="active" if blocked else "released",
        active_markets=active_markets,
        session_key=now.date().isoformat(),
        observation_id="weakness-cancel-1",
        observation_as_of=now.isoformat(),
        source_status="test",
        state_path="test-state.json",
        symbol_master_path="test-master.json",
    )


def _trader(tmp_path, monkeypatch, payload_box, *, qty=1):
    spec = WidgetSpec(
        code="999999",
        name="test",
        snapshot_path=Path("unused.json"),
        contract=FakeContract,
        event_based=True,
    )
    gateway = FakeGateway()
    recorder = FakeRecorder([])
    monkeypatch.setattr(
        engine,
        "evaluate_manual_control_exclusion",
        lambda code: SimpleNamespace(excluded=True, source="test"),
    )
    monkeypatch.setattr(
        engine,
        "manual_control_operator_exclusion_source",
        lambda code: "manual_operator",
    )
    monkeypatch.setattr(engine, "is_buy_side_paused", lambda: False)
    trader = WidgetSignalAutoTrader(
        gateway=gateway,
        specs=(spec,),
        state_path=tmp_path / "state.json",
        event_recorder=recorder,
        snapshot_loader=lambda path: payload_box["payload"],
        policy_loader=FakeDatedPolicyLoader({}),
        entry_qty=qty,
        enabled=True,
    )
    return trader, gateway, recorder


class FakeDatedPolicyLoader:
    def __init__(self, policies):
        self.policies = policies
        self.observed_dates = []

    def resolve_all(self, *, observed_date):
        self.observed_dates.append(observed_date)
        return self.policies


def _dated_policy(
    *,
    force_flat=True,
    cutoff="14:30:00",
    target_bps=100,
    source_exit_action="observe_only_no_forced_sell",
):
    return {
        "policy_id": "dated-policy-v1",
        "symbol": "999999",
        "session": "KRX_REGULAR",
        "market_venue": "KRX",
        "allowed_entry_sessions": ("KRX_REGULAR",),
        "allowed_entry_venues": ("KRX",),
        "allowed_entry_states": ("ENTRY_CAUTION", "ENTRY_READY"),
        "leg_quantity_each": 1,
        "add_trigger_bps_from_initial_fill": (),
        "take_profit_bps_from_equal_share_average": target_bps,
        "max_completed_entries_per_day": 2,
        "reentry_cooldown_minutes": 5,
        "new_entry_cutoff_time": cutoff,
        "force_flat_at_session_end": force_flat,
        "force_exit_time": "15:18:00" if force_flat else None,
        "overnight_forbidden": force_flat,
        "source_final_exit_action": source_exit_action,
        "research_arm": "test",
        "evidence_window": "2026-06-05_2026-08-11",
        "evidence_artifact": "test.json",
    }


def _dated_policy_trader(tmp_path, monkeypatch, payload_box, *, policy=None):
    spec = WidgetSpec(
        code="999999",
        name="test",
        snapshot_path=Path("unused.json"),
        contract=FakeContract,
        event_based=True,
    )
    gateway = FakeGateway()
    recorder = FakeRecorder([])
    monkeypatch.setattr(
        engine,
        "evaluate_manual_control_exclusion",
        lambda code: SimpleNamespace(excluded=True, source="test"),
    )
    monkeypatch.setattr(
        engine,
        "manual_control_operator_exclusion_source",
        lambda code: "manual_operator",
    )
    monkeypatch.setattr(engine, "is_buy_side_paused", lambda: False)
    loader = FakeDatedPolicyLoader(
        {"999999": {"KRX_REGULAR": policy or _dated_policy()}}
    )
    trader = WidgetSignalAutoTrader(
        gateway=gateway,
        specs=(spec,),
        state_path=tmp_path / "dated-state.json",
        event_recorder=recorder,
        snapshot_loader=lambda path: payload_box["payload"],
        policy_loader=loader,
        entry_qty=1,
        enabled=True,
    )
    return trader, gateway, recorder


def _samsung_policy_trader(
    tmp_path, monkeypatch, payload_box, *, entry_action_notifier=None
):
    spec = WidgetSpec(
        code="005930",
        name="Samsung",
        snapshot_path=Path("unused.json"),
        contract=FakeContract,
        event_based=True,
        structural_execution_qualification=True,
        execution_policy_id=engine.SAMSUNG_DAILY_EQUAL_SHARE_POLICY_ID,
    )
    gateway = FakeGateway()
    recorder = FakeRecorder([])
    monkeypatch.setattr(
        engine,
        "evaluate_manual_control_exclusion",
        lambda code: SimpleNamespace(excluded=True, source="test"),
    )
    monkeypatch.setattr(
        engine,
        "manual_control_operator_exclusion_source",
        lambda code: "manual_operator",
    )
    monkeypatch.setattr(engine, "is_buy_side_paused", lambda: False)
    trader = WidgetSignalAutoTrader(
        gateway=gateway,
        specs=(spec,),
        state_path=tmp_path / "state.json",
        event_recorder=recorder,
        snapshot_loader=lambda path: payload_box["payload"],
        entry_action_notifier=entry_action_notifier,
        entry_qty=engine.WIDGET_AUTO_TRADE_LEG_QUANTITY,
        enabled=True,
    )
    return trader, gateway, recorder


def test_samsung_entry_telegram_follows_accepted_machine_action_only(
    tmp_path, monkeypatch
):
    now = _at(10)
    box = {"payload": _samsung_policy_payload(now)}
    notifier = FakeEntryActionNotifier()
    trader, gateway, recorder = _samsung_policy_trader(
        tmp_path,
        monkeypatch,
        box,
        entry_action_notifier=notifier,
    )

    trader.run_once(now)
    trader.run_once(now.replace(second=1))

    assert gateway.buy_calls == [("005930", 10, "SOR")]
    assert len(notifier.calls) == 1
    notified = notifier.calls[0]
    assert notified["order"]["broker_accepted"] is True
    assert notified["order"]["order_role"] == engine.ORDER_ROLE_ENTRY_BUY
    assert notified["order"]["source_advisory_state"] == "ENTRY_CAUTION"
    assert notified["order"]["order_no"] == "B1"
    assert (
        trader._state["symbols"]["005930"]["orders"][0]["entry_telegram_status"]
        == "sent"
    )
    assert recorder.events[-1]["event_type"] == "entry_action_telegram_delivery"
    assert recorder.events[-1]["actual_order_submitted"] is True
    assert recorder.events[-1]["execution_policy_session"] == "KRX_REGULAR"


def test_definitive_entry_rejection_cools_down_distinct_signal_before_retry(
    tmp_path, monkeypatch
):
    now = _at(10)
    box = {"payload": _payload(now, entry_id="ENTRY-1")}
    trader, _, recorder = _trader(tmp_path, monkeypatch, box)
    gateway = RejectFirstBuyGateway()
    trader.gateway = gateway

    rejected = trader.run_once(now)
    symbol_state = rejected["symbols"]["999999"]
    assert symbol_state["entry_episode_open"] is False
    assert symbol_state["entry_signal_id"] == "ENTRY-1"
    assert symbol_state["entry_submit_rejected_return_code"] == "20"
    assert symbol_state["entry_submit_rejected_cooldown_sec"] == 60
    assert recorder.events[-1]["event_type"] == ("entry_episode_closed_submit_rejected")

    # The same source event remains consumed, preventing rejection storms.
    trader.run_once(now.replace(second=1))
    assert gateway.buy_calls == [("999999", 1, "SOR")]

    # A distinct signal inside the bounded cooldown must not hit the broker.
    box["payload"] = _payload(now.replace(second=2), entry_id="ENTRY-2")
    cooled_down = trader.run_once(now.replace(second=2))
    assert gateway.buy_calls == [("999999", 1, "SOR")]
    assert cooled_down["symbols"]["999999"]["entry_episode_open"] is False
    assert recorder.events[-1]["event_type"] == (
        "entry_blocked_recent_broker_rejection"
    )
    assert recorder.events[-1]["actual_order_submitted"] is False

    # A fresh source-qualified signal may retry after the cooldown expires.
    retry_at = now + timedelta(seconds=61)
    box["payload"] = _payload(retry_at, entry_id="ENTRY-3")
    accepted = trader.run_once(retry_at)
    assert gateway.buy_calls == [
        ("999999", 1, "SOR"),
        ("999999", 1, "SOR"),
    ]
    assert accepted["symbols"]["999999"]["entry_episode_open"] is True
    assert accepted["symbols"]["999999"]["orders"][-1]["broker_accepted"] is True
    assert "entry_submit_rejected_at" not in accepted["symbols"]["999999"]
    assert "entry_submit_rejected_signal_id" not in accepted["symbols"]["999999"]
    assert "entry_submit_rejected_return_code" not in accepted["symbols"]["999999"]
    assert "entry_submit_rejected_return_msg" not in accepted["symbols"]["999999"]
    assert "entry_submit_rejected_cooldown_until" not in accepted["symbols"]["999999"]


def test_widget_rechecks_same_signal_after_bounded_entry_delay(tmp_path, monkeypatch):
    now = _at(10)
    box = {"payload": _payload(now, entry_id="ENTRY-1")}
    trader, gateway, recorder = _trader(tmp_path, monkeypatch, box)
    monkeypatch.setattr(
        engine,
        "resolve_entry_confirmation_delay",
        lambda **kwargs: (
            3,
            {
                "status": "applied",
                "policy_hash": "b" * 64,
                "target_date": kwargs["target_date"].isoformat(),
            },
        ),
    )

    armed = trader.run_once(now)
    waiting = trader.run_once(now + timedelta(seconds=2))
    submitted = trader.run_once(now + timedelta(seconds=3))

    assert armed["symbols"]["999999"]["pending_entry_confirmation"]["delay_sec"] == 3
    assert waiting["symbols"]["999999"]["entry_episode_open"] is False
    assert gateway.buy_calls == [("999999", 1, "SOR")]
    symbol_state = submitted["symbols"]["999999"]
    assert symbol_state["entry_episode_open"] is True
    assert symbol_state["entry_confirmation_delay_sec"] == 3
    assert any(
        event["event_type"] == "entry_confirmation_armed" for event in recorder.events
    )


def test_widget_discards_entry_confirmation_after_recheck_window(tmp_path, monkeypatch):
    now = _at(10)
    box = {"payload": _payload(now, entry_id="ENTRY-1")}
    trader, gateway, recorder = _trader(tmp_path, monkeypatch, box)
    monkeypatch.setattr(
        engine,
        "resolve_entry_confirmation_delay",
        lambda **kwargs: (
            3,
            {
                "status": "applied",
                "policy_hash": "b" * 64,
                "target_date": kwargs["target_date"].isoformat(),
            },
        ),
    )

    trader.run_once(now)
    expired_at = now + timedelta(seconds=14)
    box["payload"] = _payload(expired_at, entry_id="ENTRY-1")
    expired = trader.run_once(expired_at)

    assert gateway.buy_calls == []
    assert expired["symbols"]["999999"]["pending_entry_confirmation"] is None
    assert recorder.events[-1]["event_type"] == "entry_confirmation_invalidated"
    assert recorder.events[-1]["reason"] == "confirmation_recheck_window_expired"


def test_widget_discards_malformed_persisted_entry_confirmation(tmp_path, monkeypatch):
    now = _at(10)
    box = {"payload": _payload(now, entry_id="ENTRY-1")}
    trader, gateway, recorder = _trader(tmp_path, monkeypatch, box)
    monkeypatch.setattr(
        engine,
        "resolve_entry_confirmation_delay",
        lambda **kwargs: (
            3,
            {
                "status": "applied",
                "policy_hash": "b" * 64,
                "target_date": kwargs["target_date"].isoformat(),
            },
        ),
    )
    trader.run_once(now)
    trader._state["symbols"]["999999"]["pending_entry_confirmation"][
        "delay_sec"
    ] = "invalid"
    next_at = now + timedelta(seconds=1)
    box["payload"] = _payload(next_at, entry_id="ENTRY-1")

    discarded = trader.run_once(next_at)

    assert gateway.buy_calls == []
    assert discarded["symbols"]["999999"]["pending_entry_confirmation"] is None
    assert recorder.events[-1]["reason"] == "persisted_confirmation_contract_invalid"


def test_persisted_definitive_entry_rejection_is_recovered_on_next_cycle(
    tmp_path, monkeypatch
):
    now = _at(10)
    box = {"payload": _payload(now)}
    trader, gateway, recorder = _trader(tmp_path, monkeypatch, box)
    trader.run_once(now)
    box["payload"] = _payload(now, entry_id="ENTRY-1")
    symbol_state = trader._state["symbols"]["999999"]
    symbol_state.update(
        {
            "entry_episode_open": True,
            "entry_signal_id": "ENTRY-1",
            "entry_consumed_at": now.isoformat(),
            "orders": [
                {
                    "side": "BUY",
                    "order_role": engine.ORDER_ROLE_ENTRY_BUY,
                    "signal_id": "ENTRY-1",
                    "status": "FAILED",
                    "broker_accepted": False,
                    "filled_qty": 0,
                    "remaining_qty": 1,
                    "return_code": "20",
                    "return_msg": "insufficient margin",
                }
            ],
        }
    )
    trader._save()

    recovered = trader.run_once(now.replace(second=1))

    assert gateway.buy_calls == []
    assert recovered["symbols"]["999999"]["entry_episode_open"] is False
    assert recovered["symbols"]["999999"]["entry_submit_rejected_cooldown_sec"] == 60
    assert recorder.events[-1]["event_type"] == (
        "entry_episode_recovered_submit_rejected"
    )


def test_definitive_entry_rejection_cooldown_has_zero_second_rollback(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("KORSTOCKSCAN_WIDGET_ENTRY_REJECT_COOLDOWN_SEC", "0")
    now = _at(10)
    box = {"payload": _payload(now, entry_id="ENTRY-1")}
    trader, _, _ = _trader(tmp_path, monkeypatch, box)
    gateway = RejectFirstBuyGateway()
    trader.gateway = gateway

    rejected = trader.run_once(now)
    assert rejected["symbols"]["999999"]["entry_submit_rejected_cooldown_sec"] == 0

    retry_at = now.replace(second=2)
    box["payload"] = _payload(retry_at, entry_id="ENTRY-2")
    accepted = trader.run_once(retry_at)

    assert gateway.buy_calls == [
        ("999999", 1, "SOR"),
        ("999999", 1, "SOR"),
    ]
    assert accepted["symbols"]["999999"]["entry_episode_open"] is True


def test_ambiguous_entry_submit_keeps_episode_open_for_reconciliation(
    tmp_path, monkeypatch
):
    now = _at(10)
    box = {"payload": _payload(now, entry_id="ENTRY-1")}
    trader, gateway, _ = _trader(tmp_path, monkeypatch, box)
    gateway.submit_buy = lambda **kwargs: SubmitResult(
        False,
        "",
        "ReadTimeout",
        "transport outcome unknown",
        ambiguous=True,
    )

    state = trader.run_once(now)
    symbol_state = state["symbols"]["999999"]

    assert symbol_state["entry_episode_open"] is True
    assert symbol_state["orders"][-1]["status"] == "AMBIGUOUS"
    assert symbol_state["orders"][-1]["broker_accepted"] is False
    assert "entry_submit_rejected_at" not in symbol_state


def test_episode_terminal_event_keeps_entry_session_after_session_transition(
    tmp_path, monkeypatch
):
    now = _at(10)
    box = {"payload": _payload(now)}
    trader, _, recorder = _trader(tmp_path, monkeypatch, box)
    trader.run_once(now)
    symbol_state = trader._state["symbols"]["999999"]
    symbol_state["entry_session"] = "NXT_PREMARKET"

    trader._event(
        "sell_terminal_failure",
        trader.specs[0],
        now,
        remaining_qty=1,
    )

    assert recorder.events[-1]["execution_policy_session"] == "NXT_PREMARKET"


def test_nxt_collector_entry_block_creates_no_machine_action_telegram(
    tmp_path, monkeypatch
):
    now = _at(10)
    box = {"payload": _samsung_policy_payload(now)}
    box["payload"]["market_venue"] = "NXT"
    notifier = FakeEntryActionNotifier()
    monkeypatch.setattr(
        FakeContract,
        "session_context",
        staticmethod(
            lambda observed_at: SimpleNamespace(
                active=True, market_venue="NXT", name="NXT_PREMARKET"
            )
        ),
    )
    trader, gateway, recorder = _samsung_policy_trader(
        tmp_path,
        monkeypatch,
        box,
        entry_action_notifier=notifier,
    )

    trader.run_once(now)

    assert gateway.buy_calls == []
    assert notifier.calls == []
    assert recorder.events[-1]["event_type"] == ("entry_blocked_execution_policy_venue")


def _samsung_policy_payload(now, *, entry_id="ENTRY-1", exit_id=None, price=100_000):
    payload = _payload(now, entry_id=entry_id, exit_id=exit_id)
    payload["symbol"] = "005930"
    payload["current_price"] = price
    payload["advisory"] = {"source_quality": {"status": "PASS"}}
    return payload


def _fill(gateway, order_no, qty=1, price=1000, execution_venue=""):
    gateway.snapshots[order_no] = ExecutionSnapshot(
        True,
        True,
        qty,
        0,
        qty,
        fill_price=price,
        execution_venue=execution_venue,
    )


def test_low_symbol_snapshot_time_contract_keeps_scale_in_loop_alive(
    tmp_path, monkeypatch
):
    now = _at(10)
    payload = _payload(now, entry_id="ENTRY-LOW-1")
    payload["current_price"] = 100_000
    payload["advisory"] = {
        "valid": True,
        "source_quality": {"status": "PASS"},
    }
    box = {"payload": payload}
    policy = _dated_policy(force_flat=False, target_bps=150)
    policy["add_trigger_bps_from_initial_fill"] = (-50, -100)
    spec = WidgetSpec(
        code="999999",
        name="low-symbol-test",
        snapshot_path=Path("unused.json"),
        contract=FakeSnapshotTimeContract,
        event_based=True,
    )
    gateway = FakeGateway()
    monkeypatch.setattr(
        engine,
        "evaluate_manual_control_exclusion",
        lambda code: SimpleNamespace(excluded=True, source="test"),
    )
    monkeypatch.setattr(
        engine,
        "manual_control_operator_exclusion_source",
        lambda code: "manual_operator",
    )
    monkeypatch.setattr(engine, "is_buy_side_paused", lambda: False)
    trader = WidgetSignalAutoTrader(
        gateway=gateway,
        specs=(spec,),
        state_path=tmp_path / "low-symbol-state.json",
        event_recorder=FakeRecorder([]),
        snapshot_loader=lambda path: box["payload"],
        policy_loader=FakeDatedPolicyLoader({"999999": {"KRX_REGULAR": policy}}),
        entry_qty=1,
        enabled=True,
    )

    trader.run_once(now)
    _fill(gateway, "B1", price=100_000)
    trader.run_once(now)
    assert gateway.limit_sell_calls == [("999999", 1, "SOR", 101_500)]

    next_observation = now.replace(second=1)
    box["payload"] = {
        **payload,
        "observed_at_kst": next_observation.isoformat(),
        "current_price": 99_500,
    }
    trader.run_once(next_observation)

    assert gateway.cancel_calls == [("999999", "L2", 1, "SOR")]


def test_one_order_per_entry_episode_and_rearms_only_after_final_exit(
    tmp_path, monkeypatch
):
    now = _at(10)
    box = {"payload": _payload(now, entry_id="ENTRY-1")}
    trader, gateway, _ = _trader(tmp_path, monkeypatch, box)

    first = trader.run_once(now)
    assert gateway.buy_calls == [("999999", 1, "SOR")]
    first_order = first["symbols"]["999999"]["orders"][0]
    assert first_order["broker_accepted"] is True
    assert first_order["market_venue"] == "KRX"
    assert first_order["broker_route"] == "SOR"
    assert first_order["route"] == "SOR"

    trader.run_once(now)
    assert len(gateway.buy_calls) == 1
    _fill(gateway, "B1")
    trader.run_once(now)
    assert gateway.limit_sell_calls == [("999999", 1, "SOR", 1_010)]

    box["payload"] = _payload(now, exit_id="EXIT-1")
    trader.run_once(now)
    assert gateway.cancel_calls == [("999999", "L2", 1, "SOR")]
    assert gateway.sell_calls == []
    gateway.snapshots["L2"] = ExecutionSnapshot(True, True, 0, 0, 1)
    trader.run_once(now)
    assert gateway.sell_calls == [("999999", 1, "SOR")]
    _fill(gateway, "S4")
    closed = trader.run_once(now)
    assert closed["symbols"]["999999"]["exit_requested"] is False
    assert closed["symbols"]["999999"]["entry_episode_open"] is False

    box["payload"] = _payload(now, entry_id="ENTRY-2", entry_state="ENTRY_READY")
    trader.run_once(now)
    assert len(gateway.buy_calls) == 2


def test_thin_touch_depth_blocks_widget_entry_without_order_and_is_not_requeried(
    tmp_path, monkeypatch
):
    now = _at(10)
    box = {"payload": _payload(now, entry_id="THIN-ENTRY")}
    trader, gateway, recorder = _trader(tmp_path, monkeypatch, box, qty=10)
    gateway.best_bid_qty = 97
    gateway.best_ask_qty = 93

    first = trader.run_once(now)
    second = trader.run_once(now.replace(second=1))

    assert gateway.buy_calls == []
    assert gateway.liquidity_calls == [("999999", "KRX")]
    assert first["symbols"]["999999"]["entry_episode_open"] is False
    assert second["symbols"]["999999"]["orders"] == []
    assert recorder.events[-1]["event_type"] == "entry_blocked_liquidity_guard"
    assert recorder.events[-1]["entry_liquidity_required_each_side_quantity"] == 100
    assert recorder.events[-1]["actual_order_submitted"] is False


def test_slow_execution_velocity_blocks_widget_entry_without_order_and_is_not_requeried(
    tmp_path, monkeypatch
):
    now = _at(10)
    box = {"payload": _payload(now, entry_id="SLOW-ENTRY")}
    trader, gateway, recorder = _trader(tmp_path, monkeypatch, box, qty=10)
    gateway.execution_velocity_span_ms = 35_000

    first = trader.run_once(now)
    second = trader.run_once(now.replace(second=1))

    assert gateway.buy_calls == []
    assert gateway.liquidity_calls == [("999999", "KRX")]
    assert gateway.execution_velocity_calls == [("999999", "KRX")]
    assert first["symbols"]["999999"]["entry_episode_open"] is False
    assert second["symbols"]["999999"]["orders"] == []
    assert recorder.events[-1]["event_type"] == (
        "entry_blocked_execution_velocity_guard"
    )
    assert recorder.events[-1]["entry_execution_velocity_reason"] == (
        "entry_execution_velocity_too_slow"
    )
    assert recorder.events[-1]["actual_order_submitted"] is False


def test_daily_reset_archives_but_never_sells_prior_day_quantity(tmp_path, monkeypatch):
    day_one = _at(10)
    box = {"payload": _payload(day_one, entry_id="DAY1-ENTRY")}
    trader, gateway, _ = _trader(tmp_path, monkeypatch, box)
    trader.run_once(day_one)
    _fill(gateway, "B1")
    trader.run_once(day_one)

    day_two = _at(11)
    box["payload"] = _payload(day_two, entry_id="DAY2-ENTRY")
    rolled = trader.run_once(day_two)
    assert rolled["history"][-1]["symbols"]["999999"]["unmanaged_overnight_qty"] == 1
    assert len(gateway.buy_calls) == 2

    _fill(gateway, "B3")
    trader.run_once(day_two)
    assert gateway.limit_sell_calls[-1] == ("999999", 1, "SOR", 1_010)
    box["payload"] = _payload(day_two, exit_id="DAY2-EXIT")
    trader.run_once(day_two)
    take_profit_order_no = next(
        order["order_no"]
        for order in trader._state["symbols"]["999999"]["orders"]
        if order.get("order_role") == engine.ORDER_ROLE_TAKE_PROFIT
    )
    gateway.snapshots[take_profit_order_no] = ExecutionSnapshot(True, True, 0, 0, 1)
    trader.run_once(day_two)
    assert gateway.sell_calls == [("999999", 1, "SOR")]


def test_daily_reset_preserves_older_unmanaged_inventory_across_flat_day(
    tmp_path, monkeypatch
):
    day_one = _at(10)
    box = {"payload": _payload(day_one, entry_id="DAY1-ENTRY")}
    trader, gateway, _ = _trader(tmp_path, monkeypatch, box)
    trader.run_once(day_one)
    _fill(gateway, "B1")
    trader.run_once(day_one)

    day_two = _at(11)
    box["payload"] = _payload(day_two)
    rolled_day_two = trader.run_once(day_two)
    assert rolled_day_two["symbols"]["999999"]["prior_day_unmanaged_qty"] == 1
    assert len(gateway.buy_calls) == 1

    day_three = _at(12)
    box["payload"] = _payload(day_three)
    rolled_day_three = trader.run_once(day_three)

    assert rolled_day_three["symbols"]["999999"]["prior_day_unmanaged_qty"] == 1
    assert rolled_day_three["history"][-1]["symbols"]["999999"][
        "unmanaged_overnight_qty"
    ] == 1
    assert len(gateway.buy_calls) == 1


def test_configurable_quantity_and_non_final_states_do_not_submit(
    tmp_path, monkeypatch
):
    now = _at(10)
    box = {"payload": _payload(now, entry_id="WATCH", entry_state="WATCH")}
    trader, gateway, _ = _trader(tmp_path, monkeypatch, box, qty=3)
    trader.run_once(now)
    assert gateway.buy_calls == []

    box["payload"] = _payload(now, entry_id="READY", entry_state="ENTRY_READY")
    trader.run_once(now)
    assert gateway.buy_calls == [("999999", 3, "SOR")]


@pytest.mark.parametrize(
    ("fill_price", "expected"),
    [
        (1_000, 1_010),
        (199_900, 202_000),
        (234_000, 236_500),
    ],
)
def test_take_profit_price_rounds_up_to_at_least_one_percent(fill_price, expected):
    target = engine._take_profit_price(fill_price)

    assert target == expected
    assert target * 10_000 >= fill_price * 10_100


def test_samsung_equal_share_policy_cancels_targets_adds_two_and_reprices(
    tmp_path, monkeypatch
):
    now = _at(10)
    box = {"payload": _samsung_policy_payload(now)}
    trader, gateway, _ = _samsung_policy_trader(tmp_path, monkeypatch, box)

    trader.run_once(now)
    _fill(gateway, "B1", qty=10, price=100_000)
    trader.run_once(now)
    initial_target = engine._take_profit_price(100_000, profit_bps=50)
    assert gateway.limit_sell_calls == [("005930", 10, "SOR", initial_target)]

    box["payload"] = _samsung_policy_payload(now.replace(second=1), price=99_500)
    trader.run_once(now.replace(second=1))
    assert gateway.cancel_calls == [("005930", "L2", 10, "SOR")]
    assert len(gateway.buy_calls) == 1

    gateway.snapshots["L2"] = ExecutionSnapshot(True, True, 0, 0, 10)
    trader.run_once(now.replace(second=2))
    assert gateway.buy_calls == [("005930", 10, "SOR"), ("005930", 10, "SOR")]

    _fill(gateway, "B4", qty=10, price=99_500)
    trader.run_once(now.replace(second=3))
    repriced_target = engine._take_profit_price(99_750, profit_bps=50)
    assert gateway.limit_sell_calls[-1] == ("005930", 20, "SOR", repriced_target)

    box["payload"] = _samsung_policy_payload(now.replace(second=4), price=99_000)
    trader.run_once(now.replace(second=4))
    assert gateway.cancel_calls[-1][0:2] == ("005930", "L5")
    gateway.snapshots["L5"] = ExecutionSnapshot(True, True, 0, 0, 20)
    trader.run_once(now.replace(second=5))
    assert gateway.buy_calls[-1] == ("005930", 10, "SOR")
    _fill(gateway, "B7", qty=10, price=99_000)
    trader.run_once(now.replace(second=6))
    final_target = engine._take_profit_price(99_500, profit_bps=50)
    assert gateway.limit_sell_calls[-1] == ("005930", 30, "SOR", final_target)
    state = trader._state["symbols"]["005930"]
    assert state["take_profit_bps"] == 50
    assert state["take_profit_basis_fill_price"] == 99_500


def test_samsung_equal_share_policy_observes_source_exit_without_forced_sell(
    tmp_path, monkeypatch
):
    now = _at(10)
    box = {"payload": _samsung_policy_payload(now)}
    trader, gateway, recorder = _samsung_policy_trader(tmp_path, monkeypatch, box)
    trader.run_once(now)
    _fill(gateway, "B1", qty=10, price=100_000)
    trader.run_once(now)

    box["payload"] = _samsung_policy_payload(
        now.replace(second=1), exit_id="EXIT-1", price=99_000
    )
    trader.run_once(now.replace(second=1))

    assert gateway.sell_calls == []
    assert gateway.cancel_calls == []
    assert len(gateway.buy_calls) == 1
    assert recorder.events[-1]["event_type"] == (
        "source_final_exit_observed_without_forced_sell"
    )


def test_samsung_equal_share_policy_requires_pass_source_for_add(tmp_path, monkeypatch):
    now = _at(10)
    box = {"payload": _samsung_policy_payload(now)}
    trader, gateway, _ = _samsung_policy_trader(tmp_path, monkeypatch, box)
    trader.run_once(now)
    _fill(gateway, "B1", qty=10, price=100_000)
    trader.run_once(now)

    box["payload"] = _samsung_policy_payload(now.replace(second=1), price=99_500)
    box["payload"]["advisory"]["source_quality"]["status"] = "STALE"
    trader.run_once(now.replace(second=1))

    assert len(gateway.buy_calls) == 1
    assert gateway.cancel_calls == []


def test_samsung_equal_share_policy_requires_fresh_snapshot_for_add(
    tmp_path, monkeypatch
):
    now = _at(10)
    box = {"payload": _samsung_policy_payload(now)}
    trader, gateway, _ = _samsung_policy_trader(tmp_path, monkeypatch, box)
    trader.run_once(now)
    _fill(gateway, "B1", qty=10, price=100_000)
    trader.run_once(now)

    stale_now = now.replace(minute=1)
    box["payload"] = _samsung_policy_payload(now, price=99_500)
    trader.run_once(stale_now)

    assert len(gateway.buy_calls) == 1
    assert gateway.cancel_calls == []


def test_samsung_equal_share_policy_rechecks_global_buy_pause_before_add(
    tmp_path, monkeypatch
):
    now = _at(10)
    box = {"payload": _samsung_policy_payload(now)}
    trader, gateway, recorder = _samsung_policy_trader(tmp_path, monkeypatch, box)
    trader.run_once(now)
    _fill(gateway, "B1", qty=10, price=100_000)
    trader.run_once(now)

    monkeypatch.setattr(engine, "is_buy_side_paused", lambda: True)
    box["payload"] = _samsung_policy_payload(now.replace(second=1), price=99_500)
    trader.run_once(now.replace(second=1))

    assert len(gateway.buy_calls) == 1
    assert gateway.cancel_calls == []
    assert recorder.events[-1]["event_type"] == "scale_in_blocked_global_buy_pause"


def test_samsung_scale_in_is_new_exposure_blocked_by_market_weakness(
    tmp_path, monkeypatch
):
    now = _at(10)
    box = {"payload": _samsung_policy_payload(now)}
    trader, gateway, recorder = _samsung_policy_trader(tmp_path, monkeypatch, box)
    mode = {"value": "released"}

    def decision():
        active = mode["value"] == "active"
        return MarketWeaknessEntryDecision(
            blocked=active,
            reason=(
                "entry_blocked_market_weakness_active"
                if active
                else "market_weakness_latch_not_active"
            ),
            symbol="005930",
            owner="widget",
            listing_market="KOSPI",
            phase="active" if active else "released",
            active_markets=("KOSPI",) if active else (),
            session_key=now.date().isoformat(),
            observation_id="weakness-scale-in-1",
            observation_as_of=now.isoformat(),
            source_status="test",
            state_path="test-state.json",
            symbol_master_path="test-master.json",
        )

    monkeypatch.setattr(
        engine,
        "evaluate_market_weakness_entry_guard",
        lambda **kwargs: decision(),
    )
    counterfactual_calls = []
    monkeypatch.setattr(
        engine,
        "record_market_weakness_blocked_entry",
        lambda *_args, **kwargs: counterfactual_calls.append(kwargs)
        or {
            "status": "recorded",
            "observation_id": "scale-in-counterfactual",
            "path": "test-only",
        },
    )
    trader.run_once(now)
    _fill(gateway, "B1", qty=10, price=100_000)
    trader.run_once(now)
    assert gateway.limit_sell_calls == [("005930", 10, "SOR", 100_500)]
    mode["value"] = "active"
    box["payload"] = _samsung_policy_payload(now.replace(second=1), price=99_500)

    trader.run_once(now.replace(second=1))

    assert gateway.buy_calls == [("005930", 10, "SOR")]
    assert gateway.cancel_calls == []
    assert recorder.events[-1]["event_type"] == ("entry_blocked_market_weakness_active")
    assert recorder.events[-1]["source_signal_id"].endswith(":ADD1")
    assert len(counterfactual_calls) == 1
    assert counterfactual_calls[0]["scope_id"] == "005930:KRX_REGULAR:SCALE_IN"
    assert counterfactual_calls[0]["reference_price"] == 99_500
    assert counterfactual_calls[0]["target_price"] == 100_500
    assert counterfactual_calls[0]["required_quantity"] == 10
    assert counterfactual_calls[0]["expected_venues"] == ["KRX"]


def test_samsung_scale_in_liquidity_block_keeps_existing_target_open(
    tmp_path, monkeypatch
):
    now = _at(10)
    box = {"payload": _samsung_policy_payload(now)}
    trader, gateway, recorder = _samsung_policy_trader(tmp_path, monkeypatch, box)
    trader.run_once(now)
    _fill(gateway, "B1", qty=10, price=100_000)
    trader.run_once(now)
    assert gateway.limit_sell_calls == [("005930", 10, "SOR", 100_500)]

    gateway.best_bid_qty = 99
    gateway.best_ask_qty = 1_000
    box["payload"] = _samsung_policy_payload(now.replace(second=1), price=99_500)
    trader.run_once(now.replace(second=1))
    trader.run_once(now.replace(second=2))

    assert len(gateway.buy_calls) == 1
    assert gateway.cancel_calls == []
    assert gateway.liquidity_calls == [("005930", "KRX"), ("005930", "KRX")]
    assert recorder.events[-1]["event_type"] == "scale_in_blocked_liquidity_guard"
    assert recorder.events[-1]["actual_order_submitted"] is False


def test_samsung_scale_in_execution_velocity_block_keeps_existing_target_open(
    tmp_path, monkeypatch
):
    now = _at(10)
    box = {"payload": _samsung_policy_payload(now)}
    trader, gateway, recorder = _samsung_policy_trader(tmp_path, monkeypatch, box)
    trader.run_once(now)
    _fill(gateway, "B1", qty=10, price=100_000)
    trader.run_once(now)
    assert gateway.limit_sell_calls == [("005930", 10, "SOR", 100_500)]

    gateway.execution_velocity_span_ms = 35_000
    box["payload"] = _samsung_policy_payload(now.replace(second=1), price=99_500)
    trader.run_once(now.replace(second=1))
    trader.run_once(now.replace(second=2))

    assert len(gateway.buy_calls) == 1
    assert gateway.cancel_calls == []
    assert gateway.execution_velocity_calls == [
        ("005930", "KRX"),
        ("005930", "KRX"),
    ]
    assert recorder.events[-1]["event_type"] == (
        "scale_in_blocked_execution_velocity_guard"
    )
    assert recorder.events[-1]["actual_order_submitted"] is False


def test_samsung_equal_share_policy_requires_existing_target_coverage_before_add(
    tmp_path, monkeypatch
):
    now = _at(10)
    box = {"payload": _samsung_policy_payload(now)}
    trader, gateway, recorder = _samsung_policy_trader(tmp_path, monkeypatch, box)
    trader.run_once(now)
    _fill(gateway, "B1", qty=10, price=100_000)
    trader.run_once(now)
    target_order = trader._state["symbols"]["005930"]["orders"][-1]
    target_order["status"] = "FAILED"
    target_order["broker_accepted"] = False
    trader._save()

    box["payload"] = _samsung_policy_payload(now.replace(second=1), price=99_500)
    trader.run_once(now.replace(second=1))

    assert len(gateway.buy_calls) == 1
    assert gateway.cancel_calls == []
    assert any(
        event["event_type"] == "scale_in_blocked_take_profit_coverage_missing"
        for event in recorder.events
    )


def test_samsung_equal_share_policy_rechecks_manual_ownership_before_add(
    tmp_path, monkeypatch
):
    now = _at(10)
    box = {"payload": _samsung_policy_payload(now)}
    trader, gateway, recorder = _samsung_policy_trader(tmp_path, monkeypatch, box)
    trader.run_once(now)
    _fill(gateway, "B1", qty=10, price=100_000)
    trader.run_once(now)

    monkeypatch.setattr(
        engine,
        "evaluate_manual_control_exclusion",
        lambda code: SimpleNamespace(excluded=False, source="none"),
    )
    monkeypatch.setattr(
        engine, "manual_control_operator_exclusion_source", lambda code: None
    )
    box["payload"] = _samsung_policy_payload(now.replace(second=1), price=99_500)
    trader.run_once(now.replace(second=1))

    assert len(gateway.buy_calls) == 1
    assert gateway.cancel_calls == []
    assert recorder.events[-1]["event_type"] == (
        "scale_in_blocked_main_bot_ownership_not_excluded"
    )


def test_samsung_equal_share_policy_exit_vetoes_new_entry_in_same_snapshot(
    tmp_path, monkeypatch
):
    now = _at(10)
    box = {
        "payload": _samsung_policy_payload(now, entry_id="ENTRY-1", exit_id="EXIT-1")
    }
    trader, gateway, recorder = _samsung_policy_trader(tmp_path, monkeypatch, box)

    trader.run_once(now)

    assert gateway.buy_calls == []
    assert not any(
        event["event_type"] == "source_final_exit_observed_without_forced_sell"
        for event in recorder.events
    )


def test_samsung_policy_requires_ten_share_initial_leg(tmp_path):
    spec = WidgetSpec(
        code="005930",
        name="Samsung",
        snapshot_path=Path("unused.json"),
        contract=FakeContract,
        event_based=True,
        execution_policy_id=engine.SAMSUNG_DAILY_EQUAL_SHARE_POLICY_ID,
    )

    with pytest.raises(ValueError, match="widget_execution_policy_entry_qty_mismatch"):
        WidgetSignalAutoTrader(
            gateway=FakeGateway(),
            specs=(spec,),
            state_path=tmp_path / "state.json",
            event_recorder=FakeRecorder([]),
            entry_qty=1,
            enabled=True,
        )


def test_samsung_runtime_policy_matches_selected_research_arm():
    policy = engine.SAMSUNG_DAILY_EQUAL_SHARE_POLICY

    assert policy["research_arm"] == "three_equal_10share_add0p5_1p0_tp0p5"
    assert policy["leg_quantity_each"] == 10
    assert policy["add_trigger_bps_from_initial_fill"] == (-50, -100)
    assert policy["take_profit_bps_from_equal_share_average"] == 50
    assert policy["allowed_entry_sessions"] == ("KRX_REGULAR",)
    assert policy["allowed_entry_venues"] == ("KRX",)


def test_dated_policy_controls_target_and_observes_source_exit(tmp_path, monkeypatch):
    now = _at(10)
    box = {"payload": _payload(now, entry_id="DATED-ENTRY")}
    trader, gateway, recorder = _dated_policy_trader(
        tmp_path,
        monkeypatch,
        box,
        policy=_dated_policy(force_flat=False, target_bps=70),
    )

    trader.run_once(now)
    _fill(gateway, "B1", price=100_000)
    trader.run_once(now.replace(second=1))
    assert gateway.limit_sell_calls == [
        ("999999", 1, "SOR", engine._take_profit_price(100_000, profit_bps=70))
    ]

    box["payload"] = _payload(now.replace(second=2), exit_id="SOURCE-EXIT")
    trader.run_once(now.replace(second=2))
    assert gateway.sell_calls == []
    assert recorder.events[-1]["event_type"] == (
        "source_final_exit_observed_without_forced_sell"
    )


def test_dated_policy_can_consume_source_exit_for_owned_quantity_only(
    tmp_path, monkeypatch
):
    now = _at(10)
    box = {"payload": _payload(now, entry_id="DATED-ENTRY")}
    trader, gateway, recorder = _dated_policy_trader(
        tmp_path,
        monkeypatch,
        box,
        policy=_dated_policy(source_exit_action="sell_own_filled_quantity"),
    )
    trader.run_once(now)
    _fill(gateway, "B1", price=100_000)
    trader.run_once(now.replace(second=1))

    box["payload"] = _payload(now.replace(second=2), exit_id="SOURCE-EXIT")
    trader.run_once(now.replace(second=2))
    assert gateway.cancel_calls == [("999999", "L2", 1, "SOR")]
    assert gateway.sell_calls == []

    gateway.snapshots["L2"] = ExecutionSnapshot(True, True, 0, 0, 1)
    trader.run_once(now.replace(second=3))
    assert gateway.sell_calls == [("999999", 1, "SOR")]
    assert any(
        event["event_type"] == "final_exit_signal_consumed" for event in recorder.events
    )


def test_unknown_source_exit_action_fails_closed_without_sell_or_new_entry(
    tmp_path, monkeypatch
):
    now = _at(10)
    box = {"payload": _payload(now, entry_id="DATED-ENTRY", exit_id="SOURCE-EXIT")}
    trader, gateway, recorder = _dated_policy_trader(
        tmp_path,
        monkeypatch,
        box,
        policy=_dated_policy(source_exit_action="unknown_action"),
    )

    trader.run_once(now)

    assert gateway.buy_calls == []
    assert gateway.sell_calls == []
    assert recorder.events[-1]["event_type"] == (
        "source_final_exit_blocked_invalid_policy_action"
    )

    trader.run_once(now.replace(second=1))
    blocked_events = [
        event
        for event in recorder.events
        if event["event_type"] == "source_final_exit_blocked_invalid_policy_action"
    ]
    assert len(blocked_events) == 1
    assert (
        trader._state["symbols"]["999999"]["last_blocked_source_exit_signal_id"]
        == "SOURCE-EXIT"
    )


def test_dated_policy_force_flat_cancels_target_and_sells_owned_quantity(
    tmp_path, monkeypatch
):
    entry_at = _at(10)
    box = {"payload": _payload(entry_at, entry_id="DATED-ENTRY")}
    trader, gateway, recorder = _dated_policy_trader(tmp_path, monkeypatch, box)
    trader.run_once(entry_at)
    _fill(gateway, "B1", price=100_000)
    trader.run_once(entry_at.replace(second=1))

    force_at = _at(10, hour=15, minute=18)
    box["payload"] = _payload(force_at)
    trader.run_once(force_at)
    assert gateway.cancel_calls == [("999999", "L2", 1, "SOR")]
    gateway.snapshots["L2"] = ExecutionSnapshot(True, True, 0, 0, 1)
    trader.run_once(force_at.replace(second=1))
    assert gateway.sell_calls == [("999999", 1, "SOR")]
    assert any(
        event["event_type"] == "policy_force_flat_requested"
        for event in recorder.events
    )


def test_dated_policy_blocks_new_entry_after_cutoff(tmp_path, monkeypatch):
    now = _at(10, hour=14, minute=31)
    box = {"payload": _payload(now, entry_id="LATE-ENTRY")}
    trader, gateway, recorder = _dated_policy_trader(tmp_path, monkeypatch, box)

    trader.run_once(now)

    assert gateway.buy_calls == []
    assert recorder.events[-1]["event_type"] == (
        "entry_blocked_execution_policy_cutoff"
    )


def test_dated_policy_blocks_new_entry_while_cumulative_research_is_incomplete(
    tmp_path, monkeypatch
):
    now = _at(10)
    box = {"payload": _payload(now, entry_id="RESEARCH-PENDING")}
    policy = {
        **_dated_policy(),
        "new_entry_runtime_eligible": False,
        "new_entry_runtime_block_reason": (
            "cumulative_research_40_qualified_dates_incomplete"
        ),
    }
    trader, gateway, recorder = _dated_policy_trader(
        tmp_path, monkeypatch, box, policy=policy
    )

    trader.run_once(now)

    assert gateway.buy_calls == []
    assert recorder.events[-1]["event_type"] == (
        "entry_blocked_cumulative_research_gate"
    )
    assert recorder.events[-1]["new_entry_runtime_eligible"] is False
    assert recorder.events[-1]["new_entry_runtime_block_reason"] == (
        "cumulative_research_40_qualified_dates_incomplete"
    )


def test_dated_policy_preserves_nonresearch_runtime_block_reason(tmp_path, monkeypatch):
    now = _at(10)
    box = {"payload": _payload(now, entry_id="SAFETY-BLOCKED")}
    policy = {
        **_dated_policy(),
        "new_entry_runtime_eligible": False,
        "new_entry_runtime_block_reason": "execution_quality_safety_veto",
    }
    trader, gateway, recorder = _dated_policy_trader(
        tmp_path, monkeypatch, box, policy=policy
    )

    trader.run_once(now)

    assert gateway.buy_calls == []
    assert recorder.events[-1]["event_type"] == (
        "entry_blocked_execution_policy_ineligible"
    )
    assert recorder.events[-1]["new_entry_runtime_block_reason"] == (
        "execution_quality_safety_veto"
    )


def test_required_dated_policy_fails_closed_when_artifact_is_missing(
    tmp_path, monkeypatch
):
    now = _at(10)
    box = {"payload": _payload(now, entry_id="NO-POLICY")}
    trader, gateway, recorder = _trader(tmp_path, monkeypatch, box)
    required_spec = replace(trader.specs[0], dated_policy_required=True)
    trader._static_specs = (required_spec,)
    trader.specs = (required_spec,)

    trader.run_once(now)

    assert gateway.buy_calls == []
    assert recorder.events[-1]["event_type"] == (
        "entry_blocked_execution_policy_session_unavailable"
    )


def test_overnight_forbidden_policy_blocks_new_day_exposure(tmp_path, monkeypatch):
    day_one = _at(10)
    box = {"payload": _payload(day_one, entry_id="DAY1")}
    trader, gateway, recorder = _dated_policy_trader(tmp_path, monkeypatch, box)
    trader.run_once(day_one)
    _fill(gateway, "B1", price=100_000)
    trader.run_once(day_one.replace(second=1))

    day_two = _at(11)
    box["payload"] = _payload(day_two, entry_id="DAY2")
    state = trader.run_once(day_two)

    assert gateway.buy_calls == [("999999", 1, "SOR")]
    assert state["symbols"]["999999"]["prior_day_unmanaged_qty"] == 1
    assert recorder.events[-1]["event_type"] == (
        "entry_blocked_prior_day_widget_inventory"
    )


def test_samsung_policy_change_fails_closed_with_same_day_open_quantity(
    tmp_path, monkeypatch
):
    now = _at(10)
    monkeypatch.setattr(engine, "_now_kst", lambda: now)
    state_path = tmp_path / "state.json"
    state_path.write_text(
        json.dumps(
            {
                "schema_version": engine.STATE_SCHEMA_VERSION,
                "execution_authority": engine.EXECUTION_AUTHORITY,
                "active_date": now.date().isoformat(),
                "execution_policies": {},
                "symbols": {
                    "005930": {
                        "orders": [
                            {
                                "side": "BUY",
                                "broker_accepted": True,
                                "filled_qty": 1,
                                "status": "FILLED",
                            }
                        ]
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    spec = WidgetSpec(
        code="005930",
        name="Samsung",
        snapshot_path=Path("unused.json"),
        contract=FakeContract,
        event_based=True,
        execution_policy_id=engine.SAMSUNG_DAILY_EQUAL_SHARE_POLICY_ID,
    )

    with pytest.raises(
        ValueError, match="widget_execution_policy_state_mismatch_with_active_orders"
    ):
        WidgetSignalAutoTrader(
            gateway=FakeGateway(),
            specs=(spec,),
            state_path=state_path,
            event_recorder=FakeRecorder([]),
            entry_qty=engine.WIDGET_AUTO_TRADE_LEG_QUANTITY,
            enabled=True,
        )


def test_ten_share_runtime_preserves_existing_one_share_episode(tmp_path, monkeypatch):
    now = _at(10)
    monkeypatch.setattr(engine, "_now_kst", lambda: now)
    state_path = tmp_path / "state.json"
    policy = _dated_policy(force_flat=False)
    policy.update(
        policy_id="dated-ten-share-policy",
        leg_quantity_each=engine.WIDGET_AUTO_TRADE_LEG_QUANTITY,
    )
    state_path.write_text(
        json.dumps(
            {
                "schema_version": engine.STATE_SCHEMA_VERSION,
                "execution_authority": engine.EXECUTION_AUTHORITY,
                "active_date": now.date().isoformat(),
                "execution_policies": {
                    "999999": {"KRX_REGULAR": "dated-ten-share-policy"}
                },
                "symbols": {
                    "999999": {
                        "entry_episode_open": True,
                        "entry_execution_policy": {
                            **policy,
                            "leg_quantity_each": 1,
                        },
                        "orders": [
                            {
                                "side": "BUY",
                                "broker_accepted": True,
                                "requested_qty": 1,
                                "filled_qty": 1,
                                "remaining_qty": 0,
                                "status": "FILLED",
                            },
                            {
                                "side": "SELL",
                                "broker_accepted": True,
                                "requested_qty": 1,
                                "filled_qty": 0,
                                "remaining_qty": 1,
                                "status": "SUBMITTED",
                            },
                        ],
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    spec = WidgetSpec(
        code="999999",
        name="test",
        snapshot_path=Path("unused.json"),
        contract=FakeContract,
        event_based=True,
    )

    trader = WidgetSignalAutoTrader(
        gateway=FakeGateway(),
        specs=(spec,),
        state_path=state_path,
        event_recorder=FakeRecorder([]),
        snapshot_loader=lambda path: {},
        policy_loader=FakeDatedPolicyLoader({"999999": {"KRX_REGULAR": policy}}),
        entry_qty=engine.WIDGET_AUTO_TRADE_LEG_QUANTITY,
        enabled=True,
    )

    symbol_state = trader._state["symbols"]["999999"]
    assert trader.entry_qty == 10
    assert symbol_state["orders"][0]["requested_qty"] == 1
    assert symbol_state["orders"][1]["remaining_qty"] == 1
    assert symbol_state["entry_execution_policy"]["leg_quantity_each"] == 1


def test_take_profit_is_submitted_only_after_fill_and_not_duplicated_on_restart(
    tmp_path, monkeypatch
):
    now = _at(10)
    box = {"payload": _payload(now, entry_id="ENTRY-1")}
    trader, gateway, recorder = _trader(tmp_path, monkeypatch, box)

    trader.run_once(now)
    assert gateway.limit_sell_calls == []
    _fill(gateway, "B1", price=234_000, execution_venue="NXT")
    state = trader.run_once(now)

    assert gateway.limit_sell_calls == [("999999", 1, "SOR", 236_500)]
    take_profit = state["symbols"]["999999"]["orders"][-1]
    assert take_profit["order_role"] == engine.ORDER_ROLE_TAKE_PROFIT
    assert take_profit["parent_entry_signal_id"] == "ENTRY-1"
    assert take_profit["limit_price"] == 236_500
    entry_order = state["symbols"]["999999"]["orders"][0]
    assert entry_order["market_venue"] == "KRX"
    assert entry_order["broker_route"] == "SOR"
    assert entry_order["broker_execution_venue"] == "NXT"
    assert recorder.events[-1]["schema"] == engine.EVENT_SCHEMA
    assert recorder.events[-1]["order_role"] == engine.ORDER_ROLE_TAKE_PROFIT
    assert recorder.events[-1]["parent_entry_signal_id"] == "ENTRY-1"
    reconciled = next(
        event
        for event in recorder.events
        if event["event_type"] == "order_execution_reconciled"
        and event["order_no"] == "B1"
    )
    assert reconciled["schema"] == engine.EVENT_SCHEMA
    assert reconciled["side"] == "BUY"
    assert reconciled["signal_id"] == "ENTRY-1"
    assert reconciled["fill_price"] == 234_000
    assert reconciled["market_venue"] == "KRX"
    assert reconciled["broker_route"] == "SOR"
    assert reconciled["broker_execution_venue"] == "NXT"
    assert reconciled["submitted_at"] == now.isoformat()

    restarted = WidgetSignalAutoTrader(
        gateway=gateway,
        specs=trader.specs,
        state_path=trader.state_path,
        event_recorder=trader.event_recorder,
        snapshot_loader=trader.snapshot_loader,
        entry_qty=1,
        enabled=True,
    )
    restarted.run_once(now)
    assert gateway.limit_sell_calls == [("999999", 1, "SOR", 236_500)]


def test_execution_venue_change_is_journaled_once_without_fill_change(
    tmp_path, monkeypatch
):
    now = _at(10)
    box = {"payload": _payload(now, entry_id="ENTRY-1")}
    trader, gateway, recorder = _trader(tmp_path, monkeypatch, box)

    trader.run_once(now)
    gateway.snapshots["B1"] = ExecutionSnapshot(
        True, True, 0, 1, 1, execution_venue="NXT"
    )
    trader.run_once(now)
    trader.run_once(now)

    venue_events = [
        event
        for event in recorder.events
        if event["event_type"] == "order_execution_reconciled"
        and event["order_no"] == "B1"
    ]
    assert len(venue_events) == 1
    assert venue_events[0]["filled_qty"] == 0
    assert venue_events[0]["remaining_qty"] == 1
    assert venue_events[0]["broker_execution_venue"] == "NXT"


def test_partial_buy_fills_receive_only_incremental_take_profit_coverage(
    tmp_path, monkeypatch
):
    now = _at(10)
    box = {"payload": _payload(now, entry_id="ENTRY-1")}
    trader, gateway, _ = _trader(tmp_path, monkeypatch, box, qty=3)
    trader.run_once(now)

    gateway.snapshots["B1"] = ExecutionSnapshot(True, True, 1, 2, 3, fill_price=100_000)
    trader.run_once(now)
    assert gateway.limit_sell_calls == [("999999", 1, "SOR", 101_000)]

    gateway.snapshots["B1"] = ExecutionSnapshot(True, True, 3, 0, 3, fill_price=100_000)
    trader.run_once(now)
    assert gateway.limit_sell_calls == [
        ("999999", 1, "SOR", 101_000),
        ("999999", 2, "SOR", 101_000),
    ]


def test_filled_take_profit_never_sells_more_than_widget_owned_quantity(
    tmp_path, monkeypatch
):
    now = _at(10)
    box = {"payload": _payload(now, entry_id="ENTRY-1")}
    trader, gateway, _ = _trader(tmp_path, monkeypatch, box)
    trader.run_once(now)
    _fill(gateway, "B1", price=234_000)
    trader.run_once(now)
    _fill(gateway, "L2", price=236_500)
    state = trader.run_once(now)

    assert trader._open_qty(state["symbols"]["999999"]) == 0
    assert state["symbols"]["999999"]["entry_episode_open"] is False

    box["payload"] = _payload(now, exit_id="EXIT-1")
    closed = trader.run_once(now)
    assert gateway.sell_calls == []
    assert closed["symbols"]["999999"]["entry_episode_open"] is False


def test_ambiguous_take_profit_blocks_duplicate_and_final_exit_oversell(
    tmp_path, monkeypatch
):
    now = _at(10)
    box = {"payload": _payload(now, entry_id="ENTRY-1")}
    trader, gateway, _ = _trader(tmp_path, monkeypatch, box)
    trader.run_once(now)
    _fill(gateway, "B1", price=234_000)

    def ambiguous_limit_sell(**kwargs):
        gateway.limit_sell_calls.append(
            (kwargs["code"], kwargs["qty"], kwargs["route"], kwargs["price"])
        )
        raise TimeoutError("broker response lost")

    gateway.submit_limit_sell = ambiguous_limit_sell
    trader.run_once(now)
    trader.run_once(now)
    assert len(gateway.limit_sell_calls) == 1

    box["payload"] = _payload(now, exit_id="EXIT-1")
    state = trader.run_once(now)
    assert gateway.sell_calls == []
    assert state["symbols"]["999999"]["exit_requested"] is True
    assert any(
        order["status"] == "AMBIGUOUS"
        and order["order_role"] == engine.ORDER_ROLE_TAKE_PROFIT
        for order in state["symbols"]["999999"]["orders"]
    )


def test_final_exit_cancels_partial_take_profit_then_sells_only_remainder(
    tmp_path, monkeypatch
):
    now = _at(10)
    box = {"payload": _payload(now, entry_id="ENTRY-1")}
    trader, gateway, _ = _trader(tmp_path, monkeypatch, box, qty=3)
    trader.run_once(now)
    _fill(gateway, "B1", qty=3, price=100_000)
    trader.run_once(now)
    assert gateway.limit_sell_calls == [("999999", 3, "SOR", 101_000)]

    gateway.snapshots["L2"] = ExecutionSnapshot(True, True, 1, 2, 3, fill_price=101_000)
    box["payload"] = _payload(now, exit_id="EXIT-1")
    trader.run_once(now)
    assert gateway.cancel_calls == [("999999", "L2", 2, "SOR")]
    assert gateway.sell_calls == []

    gateway.snapshots["L2"] = ExecutionSnapshot(True, True, 1, 0, 3, fill_price=101_000)
    trader.run_once(now)
    assert gateway.sell_calls == [("999999", 2, "SOR")]


def test_definite_take_profit_rejection_retries_bounded_and_keeps_final_exit(
    tmp_path, monkeypatch
):
    now = _at(10)
    box = {"payload": _payload(now, entry_id="ENTRY-1")}
    trader, gateway, _ = _trader(tmp_path, monkeypatch, box)
    trader.run_once(now)
    _fill(gateway, "B1", price=100_000)

    def reject_limit_sell(**kwargs):
        gateway.limit_sell_calls.append(
            (kwargs["code"], kwargs["qty"], kwargs["route"], kwargs["price"])
        )
        return SubmitResult(False, "", "BROKER_REJECT", "rejected")

    gateway.submit_limit_sell = reject_limit_sell
    trader.run_once(now)
    trader.run_once(now.replace(second=4))
    trader.run_once(now.replace(second=5))
    trader.run_once(now.replace(second=10))
    terminal = trader.run_once(now.replace(second=15))

    assert len(gateway.limit_sell_calls) == engine.MAX_TAKE_PROFIT_FAILURES
    symbol_state = terminal["symbols"]["999999"]
    assert symbol_state["take_profit_failure_count"] == 3
    assert symbol_state["take_profit_terminal_failure_at"]

    box["payload"] = _payload(now.replace(second=16), exit_id="EXIT-1")
    trader.run_once(now.replace(second=16))
    assert gateway.sell_calls == [("999999", 1, "SOR")]


def test_automatic_exclusion_does_not_transfer_real_order_ownership(
    tmp_path, monkeypatch
):
    now = _at(10)
    box = {"payload": _payload(now, entry_id="ENTRY-1")}
    trader, gateway, recorder = _trader(tmp_path, monkeypatch, box)
    monkeypatch.setattr(
        engine, "manual_control_operator_exclusion_source", lambda code: ""
    )

    trader.run_once(now)

    assert gateway.buy_calls == []
    assert recorder.events[-1]["event_type"] == (
        "entry_blocked_main_bot_ownership_not_excluded"
    )


def test_final_exit_dominates_entry_in_same_snapshot(tmp_path, monkeypatch):
    now = _at(10)
    payload = _payload(now, entry_id="ENTRY-1", exit_id="EXIT-1")
    box = {"payload": payload}
    trader, gateway, _ = _trader(tmp_path, monkeypatch, box)

    trader.run_once(now)

    assert gateway.buy_calls == []
    assert gateway.sell_calls == []


def test_samsung_style_contract_does_not_require_top_level_strategy_profile(
    tmp_path, monkeypatch
):
    now = _at(10)
    box = {"payload": {}}
    trader, _, _ = _trader(tmp_path, monkeypatch, box)
    spec = WidgetSpec(
        code="005930",
        name="Samsung",
        snapshot_path=Path("unused.json"),
        contract=FakeSamsungContractWithoutTopLevelProfile,
        event_based=False,
    )
    payload = {
        "status": "ok",
        "symbol": "005930",
        "market_venue": "KRX",
        "observed_at_kst": now.isoformat(),
    }

    context, snapshot_at = trader._validated_context(spec, payload, now)

    assert context is not None
    assert snapshot_at == now


def test_non_event_signal_identity_survives_snapshot_refresh_but_not_setup_change(
    tmp_path, monkeypatch
):
    now = _at(10)
    box = {"payload": {}}
    trader, _, _ = _trader(tmp_path, monkeypatch, box)
    spec = WidgetSpec(
        code="005930",
        name="Samsung",
        snapshot_path=Path("unused.json"),
        contract=FakeSamsungContractWithoutTopLevelProfile,
        event_based=False,
    )
    payload = {
        "status": "ok",
        "symbol": "005930",
        "market_venue": "KRX",
        "observed_at_kst": now.isoformat(),
        "observation": {"latest_completed_bar": {"source_time": "20260810100000"}},
        "advisory": {
            "valid": True,
            "state": "ENTRY_READY",
            "session": "KRX_REGULAR",
            "observed_at": now.isoformat(),
            "trigger": "confirmed_retest_early_reversal",
            "entry_price_low": 230_000,
            "entry_price_high": 230_500,
            "derived": {
                "confirmed_support": 229_500,
                "recent_resistance": 230_500,
                "recent_resistance_reclaimed": True,
            },
        },
    }

    context = spec.contract.session_context(now)
    first = trader._snapshot_entry_confirmation_identity(
        spec=spec,
        payload=payload,
        advisory=payload["advisory"],
        context=context,
        now=now,
    )
    refreshed = json.loads(json.dumps(payload))
    refreshed_at = now + timedelta(seconds=3)
    refreshed["observed_at_kst"] = refreshed_at.isoformat()
    refreshed["advisory"]["observed_at"] = refreshed_at.isoformat()
    second = trader._snapshot_entry_confirmation_identity(
        spec=spec,
        payload=refreshed,
        advisory=refreshed["advisory"],
        context=spec.contract.session_context(refreshed_at),
        now=refreshed_at,
    )
    changed = json.loads(json.dumps(refreshed))
    changed["advisory"]["entry_price_high"] = 231_000
    third = trader._snapshot_entry_confirmation_identity(
        spec=spec,
        payload=changed,
        advisory=changed["advisory"],
        context=spec.contract.session_context(refreshed_at),
        now=refreshed_at,
    )

    assert first == second
    assert third != first


def test_samsung_execution_blocks_entry_without_recent_resistance_reclaim(
    tmp_path, monkeypatch
):
    now = _at(10)
    box = {"payload": {}}
    trader, _, _ = _trader(tmp_path, monkeypatch, box)
    spec = WidgetSpec(
        code="005930",
        name="Samsung",
        snapshot_path=Path("unused.json"),
        contract=FakeSamsungContractWithoutTopLevelProfile,
        event_based=False,
        structural_execution_qualification=True,
    )
    payload = {
        "status": "ok",
        "symbol": "005930",
        "market_venue": "KRX",
        "observed_at_kst": now.isoformat(),
        "advisory": {
            "valid": True,
            "state": "ENTRY_CAUTION",
            "session": "KRX_REGULAR",
            "observed_at": now.isoformat(),
            "trigger": "confirmed_retest_early_reversal",
            "intraday_regime": {"state": "not_down"},
            "derived": {
                "confirmed_support": 231_000,
                "recent_resistance": 232_000,
                "recent_resistance_reclaimed": False,
                "higher_high_and_low": True,
            },
        },
    }

    signal = trader._entry_signal(spec, payload, now)

    assert signal is not None
    assert signal[2] == "entry_blocked_recent_resistance_not_reclaimed"


def test_samsung_equal_share_policy_does_not_repeat_widget_entry_hard_gates(
    tmp_path, monkeypatch
):
    now = _at(10)
    box = {"payload": {}}
    trader, _, _ = _trader(tmp_path, monkeypatch, box)
    spec = WidgetSpec(
        code="005930",
        name="Samsung",
        snapshot_path=Path("unused.json"),
        contract=FakeSamsungContractWithoutTopLevelProfile,
        event_based=False,
        structural_execution_qualification=True,
        execution_policy_id=engine.SAMSUNG_DAILY_EQUAL_SHARE_POLICY_ID,
    )
    payload = {
        "status": "ok",
        "symbol": "005930",
        "market_venue": "KRX",
        "observed_at_kst": now.isoformat(),
        "advisory": {
            "valid": True,
            "state": "ENTRY_CAUTION",
            "session": "KRX_REGULAR",
            "observed_at": now.isoformat(),
            "intraday_regime": {"state": "down"},
            "derived": {
                "recent_resistance_reclaimed": False,
                "resistance_reclaim_hold_confirmed": False,
                "entry_reward_risk_guard": {"passed": False},
            },
        },
    }

    signal = trader._entry_signal(spec, payload, now)

    assert signal is not None
    assert signal[2] is None


def test_samsung_equal_share_policy_blocks_unvalidated_nxt_entry(tmp_path, monkeypatch):
    now = _at(10)
    box = {"payload": {}}
    trader, _, _ = _trader(tmp_path, monkeypatch, box)
    nxt_contract = SimpleNamespace(
        session_context=lambda observed_at: SimpleNamespace(
            active=True, market_venue="NXT", name="NXT_PREMARKET"
        ),
        snapshot_is_fresh=lambda payload, now: True,
        advisory_contract_is_valid=lambda advisory, snapshot_observed_at, context, evaluated_at: True,
    )
    spec = WidgetSpec(
        code="005930",
        name="Samsung",
        snapshot_path=Path("unused.json"),
        contract=nxt_contract,
        event_based=False,
        structural_execution_qualification=True,
        execution_policy_id=engine.SAMSUNG_DAILY_EQUAL_SHARE_POLICY_ID,
    )
    payload = {
        "status": "ok",
        "symbol": "005930",
        "market_venue": "NXT",
        "observed_at_kst": now.isoformat(),
        "advisory": {
            "valid": True,
            "state": "ENTRY_READY",
            "observed_at": now.isoformat(),
        },
    }

    signal = trader._entry_signal(spec, payload, now)

    assert signal is not None
    assert signal[2] == "entry_blocked_execution_policy_venue"


def test_samsung_execution_allows_completed_structural_recovery(tmp_path, monkeypatch):
    now = _at(10)
    box = {"payload": {}}
    trader, _, _ = _trader(tmp_path, monkeypatch, box)
    spec = WidgetSpec(
        code="005930",
        name="Samsung",
        snapshot_path=Path("unused.json"),
        contract=FakeSamsungContractWithoutTopLevelProfile,
        event_based=False,
        structural_execution_qualification=True,
    )
    payload = {
        "status": "ok",
        "symbol": "005930",
        "market_venue": "KRX",
        "observed_at_kst": now.isoformat(),
        "advisory": {
            "valid": True,
            "state": "ENTRY_CAUTION",
            "session": "KRX_REGULAR",
            "observed_at": now.isoformat(),
            "trigger": "dynamic_support_and_vwap_reclaim",
            "intraday_regime": {"state": "down"},
            "derived": {
                "confirmed_support": 231_000,
                "recent_resistance": 232_000,
                "recent_resistance_reclaimed": True,
                "resistance_reclaim_hold_confirmed": True,
                "higher_high_and_low": True,
                "entry_reward_risk_guard": {"passed": True},
            },
        },
    }

    signal = trader._entry_signal(spec, payload, now)

    assert signal is not None
    assert signal[2] is None


def test_samsung_execution_blocks_entry_below_reward_risk_floor(tmp_path, monkeypatch):
    now = _at(10)
    box = {"payload": {}}
    trader, _, _ = _trader(tmp_path, monkeypatch, box)
    spec = WidgetSpec(
        code="005930",
        name="Samsung",
        snapshot_path=Path("unused.json"),
        contract=FakeSamsungContractWithoutTopLevelProfile,
        event_based=False,
        structural_execution_qualification=True,
    )
    payload = {
        "status": "ok",
        "symbol": "005930",
        "market_venue": "KRX",
        "observed_at_kst": now.isoformat(),
        "advisory": {
            "valid": True,
            "state": "ENTRY_CAUTION",
            "session": "KRX_REGULAR",
            "observed_at": now.isoformat(),
            "trigger": "dynamic_support_and_vwap_reclaim",
            "intraday_regime": {"state": "not_down"},
            "derived": {
                "confirmed_support": 228_000,
                "recent_resistance": 230_000,
                "recent_resistance_reclaimed": True,
                "resistance_reclaim_hold_confirmed": True,
                "higher_high_and_low": True,
                "entry_reward_risk_guard": {"passed": False},
            },
        },
    }

    signal = trader._entry_signal(spec, payload, now)

    assert signal is not None
    assert signal[2] == "entry_blocked_reward_risk_not_qualified"
    payload["advisory"]["derived"].pop("entry_reward_risk_guard")
    missing_signal = trader._entry_signal(spec, payload, now)
    assert missing_signal is not None
    assert missing_signal[2] == "entry_blocked_reward_risk_not_qualified"


def test_samsung_structural_block_is_observable_and_does_not_consume_episode(
    tmp_path, monkeypatch
):
    now = _at(10)
    spec = WidgetSpec(
        code="005930",
        name="Samsung",
        snapshot_path=Path("unused.json"),
        contract=FakeSamsungContractWithoutTopLevelProfile,
        event_based=False,
        structural_execution_qualification=True,
    )
    payload = {
        "status": "ok",
        "symbol": "005930",
        "market_venue": "KRX",
        "observed_at_kst": now.isoformat(),
        "advisory": {
            "valid": True,
            "state": "ENTRY_CAUTION",
            "session": "KRX_REGULAR",
            "observed_at": now.isoformat(),
            "trigger": "confirmed_retest_early_reversal",
            "intraday_regime": {"state": "not_down"},
            "derived": {
                "confirmed_support": 231_000,
                "recent_resistance": 232_000,
                "recent_resistance_reclaimed": False,
                "resistance_reclaim_hold_confirmed": False,
                "higher_high_and_low": True,
            },
        },
    }
    gateway = FakeGateway()
    recorder = FakeRecorder([])
    monkeypatch.setattr(
        engine,
        "evaluate_manual_control_exclusion",
        lambda code: SimpleNamespace(excluded=True, source="test"),
    )
    monkeypatch.setattr(
        engine,
        "manual_control_operator_exclusion_source",
        lambda code: "manual_operator",
    )
    trader = WidgetSignalAutoTrader(
        gateway=gateway,
        specs=(spec,),
        state_path=tmp_path / "state.json",
        event_recorder=recorder,
        snapshot_loader=lambda path: payload,
        enabled=True,
    )

    state = trader.run_once(now)

    assert gateway.buy_calls == []
    assert state["symbols"]["005930"]["entry_episode_open"] is False
    assert recorder.events[-1]["event_type"] == (
        "entry_blocked_recent_resistance_not_reclaimed"
    )


def test_global_buy_pause_does_not_consume_entry_episode(tmp_path, monkeypatch):
    now = _at(10)
    box = {"payload": _payload(now, entry_id="ENTRY-1")}
    trader, gateway, recorder = _trader(tmp_path, monkeypatch, box)
    monkeypatch.setattr(engine, "is_buy_side_paused", lambda: True)

    blocked = trader.run_once(now)
    assert gateway.buy_calls == []
    assert blocked["symbols"]["999999"]["entry_episode_open"] is False
    assert recorder.events[-1]["event_type"] == "entry_blocked_global_buy_pause"

    monkeypatch.setattr(engine, "is_buy_side_paused", lambda: False)
    trader.run_once(now)
    assert gateway.buy_calls == [("999999", 1, "SOR")]


def test_market_weakness_guard_does_not_consume_widget_signal(tmp_path, monkeypatch):
    now = _at(10)
    box = {"payload": _payload(now, entry_id="ENTRY-1")}
    trader, gateway, recorder = _trader(tmp_path, monkeypatch, box)

    def decision(*, blocked):
        return MarketWeaknessEntryDecision(
            blocked=blocked,
            reason=(
                "entry_blocked_market_weakness_active"
                if blocked
                else "market_weakness_latch_not_active"
            ),
            symbol="999999",
            owner="widget",
            listing_market="KOSPI",
            phase="active" if blocked else "released",
            active_markets=("KOSPI",) if blocked else (),
            session_key="2026-08-10",
            observation_id="weakness-2",
            observation_as_of=now.isoformat(),
            source_status="test",
            state_path="test-state.json",
            symbol_master_path="test-master.json",
        )

    monkeypatch.setattr(
        engine,
        "evaluate_market_weakness_entry_guard",
        lambda **kwargs: decision(blocked=True),
    )
    blocked = trader.run_once(now)
    assert gateway.buy_calls == []
    assert blocked["symbols"]["999999"]["entry_episode_open"] is False
    assert recorder.events[-1]["event_type"] == ("entry_blocked_market_weakness_active")

    monkeypatch.setattr(
        engine,
        "evaluate_market_weakness_entry_guard",
        lambda **kwargs: decision(blocked=False),
    )
    trader.run_once(now)
    assert gateway.buy_calls == [("999999", 1, "SOR")]


def test_market_weakness_transition_during_entry_checks_blocks_pre_submit(
    tmp_path, monkeypatch
):
    now = _at(10)
    box = {"payload": _payload(now, entry_id="ENTRY-1")}
    trader, gateway, recorder = _trader(tmp_path, monkeypatch, box)
    decisions = iter((False, True))

    def evaluate(**kwargs):
        blocked = next(decisions)
        return MarketWeaknessEntryDecision(
            blocked=blocked,
            reason=(
                "entry_blocked_market_weakness_active"
                if blocked
                else "market_weakness_latch_not_active"
            ),
            symbol="999999",
            owner="widget",
            listing_market="KOSPI",
            phase="active" if blocked else "released",
            active_markets=("KOSPI",) if blocked else (),
            session_key="2026-08-10",
            observation_id="weakness-transition",
            observation_as_of=now.isoformat(),
            source_status="test",
            state_path="test-state.json",
            symbol_master_path="test-master.json",
        )

    monkeypatch.setattr(engine, "evaluate_market_weakness_entry_guard", evaluate)
    state = trader.run_once(now)

    assert gateway.buy_calls == []
    assert state["symbols"]["999999"]["entry_episode_open"] is False
    assert recorder.events[-1]["event_type"] == ("entry_blocked_market_weakness_active")


def test_market_weakness_cancels_reconciled_widget_buy_without_signal_snapshot(
    tmp_path, monkeypatch
):
    now = _at(10)
    box = {"payload": _payload(now, entry_id="ENTRY-1")}
    trader, gateway, recorder = _trader(tmp_path, monkeypatch, box, qty=10)
    mode = {"value": "released"}
    monkeypatch.setattr(
        engine,
        "evaluate_market_weakness_entry_guard",
        lambda **kwargs: _market_weakness_decision(now, mode=mode["value"]),
    )

    submitted = trader.run_once(now)
    order = submitted["symbols"]["999999"]["orders"][0]
    assert order["order_no"] == "B1"
    gateway.snapshots["B1"] = ExecutionSnapshot(
        True, True, 4, 6, 10, fill_price=100_000
    )
    box["payload"] = None
    mode["value"] = "active"

    canceled = trader.run_once(now + timedelta(seconds=1))

    order = canceled["symbols"]["999999"]["orders"][0]
    assert gateway.cancel_calls == [("999999", "B1", 6, "SOR")]
    assert order["filled_qty"] == 4
    assert order["remaining_qty"] == 6
    assert order["status"] == "CANCEL_REQUESTED"
    assert order["cancel_reason"] == "market_weakness_active_exact_market"
    cancel_event = next(
        event
        for event in reversed(recorder.events)
        if event["event_type"] == "buy_cancel_requested"
    )
    assert cancel_event["order_role"] == "ENTRY_BUY"
    assert cancel_event["market_weakness_open_buy_cancel_allowed"] is True


def test_market_weakness_does_not_cancel_without_fresh_broker_reconciliation(
    tmp_path, monkeypatch
):
    now = _at(10)
    box = {"payload": _payload(now, entry_id="ENTRY-1")}
    trader, gateway, recorder = _trader(tmp_path, monkeypatch, box)
    mode = {"value": "released"}
    monkeypatch.setattr(
        engine,
        "evaluate_market_weakness_entry_guard",
        lambda **kwargs: _market_weakness_decision(now, mode=mode["value"]),
    )
    trader.run_once(now)
    box["payload"] = None
    mode["value"] = "active"

    state = trader.run_once(now + timedelta(seconds=1))

    assert gateway.cancel_calls == []
    assert state["symbols"]["999999"]["orders"][0]["status"] == "SUBMITTED"
    assert any(
        event["event_type"] == "buy_cancel_blocked_reconciliation_not_fresh"
        for event in recorder.events
    )


def test_market_weakness_widget_cancel_ambiguity_reconciles_before_bounded_retry(
    tmp_path, monkeypatch
):
    now = _at(10)
    box = {"payload": _payload(now, entry_id="ENTRY-1")}
    trader, gateway, _ = _trader(tmp_path, monkeypatch, box)
    mode = {"value": "released"}
    monkeypatch.setattr(
        engine,
        "evaluate_market_weakness_entry_guard",
        lambda **kwargs: _market_weakness_decision(now, mode=mode["value"]),
    )
    trader.run_once(now)
    gateway.snapshots["B1"] = ExecutionSnapshot(True, True, 0, 1, 1)
    box["payload"] = None
    mode["value"] = "active"
    cancel_attempts = []

    def flaky_cancel(*, code, order_no, qty, route):
        cancel_attempts.append((code, order_no, qty, route))
        if len(cancel_attempts) == 1:
            raise TimeoutError("ambiguous cancel transport")
        return gateway._accepted("C")

    monkeypatch.setattr(gateway, "cancel", flaky_cancel)

    ambiguous = trader.run_once(now + timedelta(seconds=1))
    throttled = trader.run_once(now + timedelta(seconds=2))
    retried = trader.run_once(now + timedelta(seconds=6))

    assert ambiguous["symbols"]["999999"]["orders"][0]["status"] == ("CANCEL_AMBIGUOUS")
    assert throttled["symbols"]["999999"]["orders"][0]["status"] == ("CANCEL_AMBIGUOUS")
    assert retried["symbols"]["999999"]["orders"][0]["status"] == ("CANCEL_REQUESTED")
    assert cancel_attempts == [
        ("999999", "B1", 1, "SOR"),
        ("999999", "B1", 1, "SOR"),
    ]


def test_market_weakness_invalid_market_scope_never_authorizes_widget_cancel(
    tmp_path, monkeypatch
):
    now = _at(10)
    box = {"payload": _payload(now, entry_id="ENTRY-1")}
    trader, gateway, _ = _trader(tmp_path, monkeypatch, box)
    mode = {"value": "released"}
    monkeypatch.setattr(
        engine,
        "evaluate_market_weakness_entry_guard",
        lambda **kwargs: _market_weakness_decision(now, mode=mode["value"]),
    )
    trader.run_once(now)
    gateway.snapshots["B1"] = ExecutionSnapshot(True, True, 0, 1, 1)
    box["payload"] = None
    mode["value"] = "invalid_scope"

    trader.run_once(now + timedelta(seconds=1))

    assert gateway.cancel_calls == []


def test_shared_token_gateway_blocks_buy_during_global_pause(monkeypatch):
    class FailIfCalledSession:
        def post(self, *args, **kwargs):
            raise AssertionError("broker API must not be called while paused")

    monkeypatch.setattr(gateway_module, "is_buy_side_paused", lambda: True)
    gateway = gateway_module.KiwoomSharedTokenOrderGateway(
        request_session=FailIfCalledSession(), token_loader=lambda: "cached-token"
    )

    result = gateway.submit_buy(code="005930", qty=1, route="KRX")
    limit_result = gateway.submit_limit_buy(
        code="005930", qty=1, route="KRX", price=236_500
    )

    assert result.accepted is False
    assert result.return_code == "TRADING_PAUSED"
    assert limit_result.accepted is False
    assert limit_result.return_code == "TRADING_PAUSED"


def test_gateway_uses_documented_order_contract_without_cash_or_token_issue(
    monkeypatch,
):
    class Response:
        status_code = 200
        headers = {}

        @staticmethod
        def json():
            return {"return_code": 0, "return_msg": "OK", "ord_no": "0001234"}

    class RecordingSession:
        def __init__(self):
            self.calls = []

        def post(self, url, **kwargs):
            self.calls.append((url, kwargs))
            return Response()

    session = RecordingSession()
    monkeypatch.setattr(gateway_module, "is_buy_side_paused", lambda: False)
    gateway = gateway_module.KiwoomSharedTokenOrderGateway(
        request_session=session, token_loader=lambda: "cached-token"
    )

    result = gateway.submit_buy(code="A005930", qty=1, route="NXT")

    assert result.accepted is True
    assert len(session.calls) == 1
    url, request = session.calls[0]
    assert url.endswith("/api/dostk/ordr")
    assert request["headers"]["api-id"] == "kt10000"
    assert request["headers"]["authorization"] == "Bearer cached-token"
    assert request["json"] == {
        "dmst_stex_tp": "NXT",
        "stk_cd": "005930",
        "ord_qty": "1",
        "ord_uv": "",
        "trde_tp": "6",
        "cond_uv": "",
    }
    assert all("oauth2" not in call[0] for call in session.calls)
    assert all(call[1]["headers"]["api-id"] != "kt00001" for call in session.calls)


def test_gateway_liquidity_read_uses_explicit_integrated_or_nxt_book(monkeypatch):
    calls = []

    def fake_orderbook(token, code):
        calls.append((token, code))
        return {
            "source": "ka10004_rest_orderbook",
            "stock_code": "181710",
            "request_code": code,
            "rest_freshness_basis": "response_received_epoch_ms",
            "best_bid": 71_300,
            "best_ask": 71_500,
            "best_bid_qty": 101,
            "best_ask_qty": 102,
            "bid_tot": 1_255,
            "ask_tot": 880,
            "rest_age_ms": 0,
            "rest_received_ts_ms": 1,
        }

    monkeypatch.setattr(
        gateway_module.kiwoom_utils,
        "get_stock_orderbook_ka10004",
        fake_orderbook,
    )
    gateway = gateway_module.KiwoomSharedTokenOrderGateway(
        token_loader=lambda: "cached-token"
    )

    regular = gateway.entry_liquidity_snapshot(code="181710", route="KRX")
    nxt = gateway.entry_liquidity_snapshot(code="181710", route="NXT")

    assert calls == [
        ("cached-token", "181710_AL"),
        ("cached-token", "181710_NX"),
    ]
    assert regular.source_ok and regular.route == "KRX"
    assert nxt.source_ok and nxt.route == "NXT"


def test_gateway_routes_krx_buy_and_final_sell_through_sor(monkeypatch):
    class Response:
        status_code = 200
        headers = {}

        @staticmethod
        def json():
            return {"return_code": 0, "return_msg": "OK", "ord_no": "0001234"}

    class RecordingSession:
        def __init__(self):
            self.calls = []

        def post(self, url, **kwargs):
            self.calls.append((url, kwargs))
            return Response()

    session = RecordingSession()
    monkeypatch.setattr(gateway_module, "is_buy_side_paused", lambda: False)
    gateway = gateway_module.KiwoomSharedTokenOrderGateway(
        request_session=session, token_loader=lambda: "cached-token"
    )

    assert gateway.submit_buy(code="005930", qty=1, route="KRX").accepted is True
    assert gateway.submit_sell(code="005930", qty=1, route="KRX").accepted is True

    buy_payload = session.calls[0][1]["json"]
    sell_payload = session.calls[1][1]["json"]
    assert buy_payload["dmst_stex_tp"] == "SOR"
    assert buy_payload["trde_tp"] == "6"
    assert sell_payload["dmst_stex_tp"] == "SOR"
    assert sell_payload["trde_tp"] == "3"


def test_gateway_routes_krx_limit_sell_through_sor(monkeypatch):
    class Response:
        status_code = 200
        headers = {}

        @staticmethod
        def json():
            return {"return_code": 0, "return_msg": "OK", "ord_no": "0001235"}

    class RecordingSession:
        def __init__(self):
            self.calls = []

        def post(self, url, **kwargs):
            self.calls.append((url, kwargs))
            return Response()

    session = RecordingSession()
    gateway = gateway_module.KiwoomSharedTokenOrderGateway(
        request_session=session, token_loader=lambda: "cached-token"
    )

    result = gateway.submit_limit_sell(code="005930", qty=1, route="KRX", price=236_500)

    assert result.accepted is True
    _, request = session.calls[0]
    assert request["headers"]["api-id"] == "kt10001"
    assert request["json"] == {
        "dmst_stex_tp": "SOR",
        "stk_cd": "005930",
        "ord_qty": "1",
        "ord_uv": "236500",
        "trde_tp": "0",
        "cond_uv": "",
    }


def test_gateway_routes_operator_limit_buy_through_sor(monkeypatch):
    class Response:
        status_code = 200
        headers = {}

        @staticmethod
        def json():
            return {"return_code": 0, "return_msg": "OK", "ord_no": "0001236"}

    class RecordingSession:
        def __init__(self):
            self.calls = []

        def post(self, url, **kwargs):
            self.calls.append((url, kwargs))
            return Response()

    session = RecordingSession()
    monkeypatch.setattr(gateway_module, "is_buy_side_paused", lambda: False)
    gateway = gateway_module.KiwoomSharedTokenOrderGateway(
        request_session=session, token_loader=lambda: "cached-token"
    )

    result = gateway.submit_limit_buy(code="005930", qty=2, route="KRX", price=236_500)

    assert result.accepted is True
    _, request = session.calls[0]
    assert request["headers"]["api-id"] == "kt10000"
    assert request["json"] == {
        "dmst_stex_tp": "SOR",
        "stk_cd": "005930",
        "ord_qty": "2",
        "ord_uv": "236500",
        "trde_tp": "0",
        "cond_uv": "",
    }


def test_gateway_rejects_invalid_route_and_quantity_before_broker_call(monkeypatch):
    class FailIfCalledSession:
        def post(self, *args, **kwargs):
            raise AssertionError("invalid input must not reach broker")

    monkeypatch.setattr(gateway_module, "is_buy_side_paused", lambda: False)
    gateway = gateway_module.KiwoomSharedTokenOrderGateway(
        request_session=FailIfCalledSession(), token_loader=lambda: "cached-token"
    )

    with pytest.raises(ValueError, match="invalid_order_route"):
        gateway.submit_buy(code="005930", qty=1, route="INVALID")
    with pytest.raises(ValueError, match="invalid_order_quantity"):
        gateway.submit_sell(code="005930", qty=0, route="KRX")
    with pytest.raises(ValueError, match="invalid_order_price"):
        gateway.submit_limit_sell(code="005930", qty=1, route="KRX", price=0)
    with pytest.raises(ValueError, match="invalid_order_price"):
        gateway.submit_limit_sell(code="005930", qty=1, route="KRX", price=236_300)


def test_gateway_reconciles_only_exact_documented_order_row():
    class Response:
        status_code = 200
        headers = {}

        @staticmethod
        def json():
            return {
                "acnt_ord_cntr_prps_dtl": [
                    {
                        "ord_no": "0000123",
                        "stk_cd": "A005930",
                        "ord_qty": "0000000003",
                        "cntr_qty": "0000000001",
                        "cntr_uv": "0000234000",
                        "ord_remnq": "0000000002",
                        "dmst_stex_tp": "KRX",
                    },
                    {
                        "ord_no": "0000999",
                        "stk_cd": "A005930",
                        "ord_qty": "0000000010",
                        "cntr_qty": "0000000010",
                        "ord_remnq": "0000000000",
                    },
                ],
                "return_code": 0,
                "return_msg": "OK",
            }

    class Session:
        @staticmethod
        def post(*args, **kwargs):
            return Response()

    gateway = gateway_module.KiwoomSharedTokenOrderGateway(
        request_session=Session(), token_loader=lambda: "cached-token"
    )

    snapshot = gateway.execution_snapshot(
        code="005930", order_no="123", route="KRX", order_date="2026-08-10"
    )

    assert snapshot.source_ok is True
    assert snapshot.found is True
    assert snapshot.order_qty == 3
    assert snapshot.filled_qty == 1
    assert snapshot.remaining_qty == 2
    assert snapshot.fill_price == 234000
    assert snapshot.execution_venue == "KRX"


def test_gateway_reconciles_sor_order_across_actual_execution_venue():
    class Response:
        status_code = 200
        headers = {}

        @staticmethod
        def json():
            return {
                "acnt_ord_cntr_prps_dtl": [
                    {
                        "ord_no": "0064588",
                        "stk_cd": "A005930",
                        "ord_qty": "20",
                        "cntr_qty": "0",
                        "ord_remnq": "20",
                        "dmst_stex_tp": "NXT",
                    },
                    {
                        "ord_no": "0069999",
                        "stk_cd": "A005930",
                        "ord_qty": "20",
                        "cntr_qty": "20",
                        "ord_remnq": "0",
                        "dmst_stex_tp": "KRX",
                    },
                ],
                "return_code": 0,
            }

    class Session:
        def __init__(self):
            self.calls = []

        def post(self, *args, **kwargs):
            self.calls.append(kwargs)
            return Response()

    session = Session()
    gateway = gateway_module.KiwoomSharedTokenOrderGateway(
        request_session=session, token_loader=lambda: "cached-token"
    )

    snapshot = gateway.execution_snapshot(
        code="005930", order_no="0064588", route="SOR", order_date="2026-08-27"
    )

    assert session.calls[0]["json"]["dmst_stex_tp"] == "%"
    assert snapshot.source_ok is True
    assert snapshot.found is True
    assert snapshot.order_qty == 20
    assert snapshot.filled_qty == 0
    assert snapshot.remaining_qty == 20
    assert snapshot.execution_venue == "NXT"


def test_gateway_normalizes_compatible_numeric_execution_venue():
    class Response:
        status_code = 200
        headers = {}

        @staticmethod
        def json():
            return {
                "acnt_ord_cntr_prps_dtl": [
                    {
                        "ord_no": "0064588",
                        "stk_cd": "A005930",
                        "ord_qty": "20",
                        "cntr_qty": "0",
                        "ord_remnq": "20",
                        "stex_tp": "2",
                    }
                ],
                "return_code": 0,
            }

    class Session:
        @staticmethod
        def post(*args, **kwargs):
            return Response()

    gateway = gateway_module.KiwoomSharedTokenOrderGateway(
        request_session=Session(), token_loader=lambda: "cached-token"
    )

    snapshot = gateway.execution_snapshot(
        code="005930", order_no="0064588", route="SOR", order_date="2026-08-27"
    )

    assert snapshot.source_ok is True
    assert snapshot.execution_venue == "NXT"


def test_gateway_fails_closed_on_conflicting_execution_venue_fields():
    class Response:
        status_code = 200
        headers = {}

        @staticmethod
        def json():
            return {
                "acnt_ord_cntr_prps_dtl": [
                    {
                        "ord_no": "0064588",
                        "stk_cd": "A005930",
                        "ord_qty": "20",
                        "cntr_qty": "0",
                        "ord_remnq": "20",
                        "dmst_stex_tp": "KRX",
                        "stex_tp": "2",
                    }
                ],
                "return_code": 0,
            }

    class Session:
        @staticmethod
        def post(*args, **kwargs):
            return Response()

    gateway = gateway_module.KiwoomSharedTokenOrderGateway(
        request_session=Session(), token_loader=lambda: "cached-token"
    )

    snapshot = gateway.execution_snapshot(
        code="005930", order_no="0064588", route="SOR", order_date="2026-08-27"
    )

    assert snapshot.source_ok is False
    assert snapshot.found is True
    assert snapshot.error == "ambiguous_execution_venue"


def test_gateway_fails_closed_on_invalid_execution_venue_field():
    class Response:
        status_code = 200
        headers = {}

        @staticmethod
        def json():
            return {
                "acnt_ord_cntr_prps_dtl": [
                    {
                        "ord_no": "0064588",
                        "stk_cd": "A005930",
                        "ord_qty": "20",
                        "cntr_qty": "0",
                        "ord_remnq": "20",
                        "dmst_stex_tp": "UNKNOWN",
                    }
                ],
                "return_code": 0,
            }

    class Session:
        @staticmethod
        def post(*args, **kwargs):
            return Response()

    gateway = gateway_module.KiwoomSharedTokenOrderGateway(
        request_session=Session(), token_loader=lambda: "cached-token"
    )

    snapshot = gateway.execution_snapshot(
        code="005930", order_no="0064588", route="SOR", order_date="2026-08-27"
    )

    assert snapshot.source_ok is False
    assert snapshot.found is True
    assert snapshot.error == "invalid_execution_venue"


def test_gateway_fails_closed_when_exact_order_spans_multiple_execution_venues():
    class Response:
        status_code = 200
        headers = {}

        @staticmethod
        def json():
            return {
                "acnt_ord_cntr_prps_dtl": [
                    {
                        "ord_no": "0064588",
                        "stk_cd": "A005930",
                        "ord_qty": "20",
                        "cntr_qty": "0",
                        "ord_remnq": "20",
                        "dmst_stex_tp": venue,
                    }
                    for venue in ("KRX", "NXT")
                ],
                "return_code": 0,
            }

    class Session:
        @staticmethod
        def post(*args, **kwargs):
            return Response()

    gateway = gateway_module.KiwoomSharedTokenOrderGateway(
        request_session=Session(), token_loader=lambda: "cached-token"
    )

    snapshot = gateway.execution_snapshot(
        code="005930", order_no="0064588", route="SOR", order_date="2026-08-27"
    )

    assert snapshot.source_ok is False
    assert snapshot.found is True
    assert snapshot.error == "ambiguous_execution_venue"


def test_gateway_fails_closed_when_filled_descendants_span_multiple_venues():
    class Response:
        status_code = 200
        headers = {}

        @staticmethod
        def json():
            return {
                "acnt_ord_cntr_prps_dtl": [
                    {
                        "ord_no": "0040442",
                        "orig_ord_no": "0000000",
                        "stk_cd": "A042660",
                        "ord_qty": "2",
                        "cntr_qty": "0",
                        "ord_remnq": "0",
                        "dmst_stex_tp": "SOR",
                    },
                    {
                        "ord_no": "0041229",
                        "ori_ord": "0040442",
                        "stk_cd": "A042660",
                        "ord_qty": "1",
                        "cntr_qty": "1",
                        "ord_remnq": "0",
                        "dmst_stex_tp": "KRX",
                    },
                    {
                        "ord_no": "0041230",
                        "orig_ord_no": "0040442",
                        "stk_cd": "A042660",
                        "ord_qty": "1",
                        "cntr_qty": "1",
                        "ord_remnq": "0",
                        "dmst_stex_tp": "NXT",
                    },
                ],
                "return_code": 0,
            }

    class Session:
        @staticmethod
        def post(*args, **kwargs):
            return Response()

    gateway = gateway_module.KiwoomSharedTokenOrderGateway(
        request_session=Session(), token_loader=lambda: "cached-token"
    )

    snapshot = gateway.execution_snapshot(
        code="042660", order_no="0040442", route="SOR", order_date="2026-08-27"
    )

    assert snapshot.source_ok is False
    assert snapshot.found is True
    assert snapshot.error == "ambiguous_execution_venue"


def test_gateway_reconciles_filled_same_symbol_successor_order_chain():
    class Response:
        status_code = 200
        headers = {}

        @staticmethod
        def json():
            return {
                "acnt_ord_cntr_prps_dtl": [
                    {
                        "ord_no": "0040442",
                        "orig_ord_no": "0000000",
                        "stk_cd": "A042660",
                        "ord_qty": "1",
                        "cntr_qty": "0",
                        "ord_remnq": "0",
                    },
                    {
                        "ord_no": "0041229",
                        "orig_ord_no": "0040442",
                        "stk_cd": "A042660",
                        "ord_qty": "1",
                        "cntr_qty": "1",
                        "cntr_uv": "90300",
                        "ord_remnq": "0",
                    },
                    {
                        "ord_no": "0099999",
                        "orig_ord_no": "0040442",
                        "stk_cd": "A005930",
                        "ord_qty": "10",
                        "cntr_qty": "10",
                        "ord_remnq": "0",
                    },
                ],
                "return_code": 0,
            }

    class Session:
        @staticmethod
        def post(*args, **kwargs):
            return Response()

    gateway = gateway_module.KiwoomSharedTokenOrderGateway(
        request_session=Session(), token_loader=lambda: "cached-token"
    )

    snapshot = gateway.execution_snapshot(
        code="042660", order_no="0040442", route="SOR", order_date="2026-08-12"
    )

    assert snapshot.source_ok is True
    assert snapshot.found is True
    assert snapshot.order_qty == 1
    assert snapshot.filled_qty == 1
    assert snapshot.remaining_qty == 0
    assert snapshot.fill_price == 90300


def test_gateway_does_not_merge_successor_when_root_is_partially_filled():
    class Response:
        status_code = 200
        headers = {}

        @staticmethod
        def json():
            return {
                "acnt_ord_cntr_prps_dtl": [
                    {
                        "ord_no": "0040442",
                        "orig_ord_no": "0000000",
                        "stk_cd": "A042660",
                        "ord_qty": "2",
                        "cntr_qty": "1",
                        "cntr_uv": "90000",
                        "ord_remnq": "0",
                    },
                    {
                        "ord_no": "0041229",
                        "orig_ord_no": "0040442",
                        "stk_cd": "A042660",
                        "ord_qty": "1",
                        "cntr_qty": "1",
                        "cntr_uv": "90300",
                        "ord_remnq": "0",
                    },
                ],
                "return_code": 0,
            }

    class Session:
        @staticmethod
        def post(*args, **kwargs):
            return Response()

    gateway = gateway_module.KiwoomSharedTokenOrderGateway(
        request_session=Session(), token_loader=lambda: "cached-token"
    )

    snapshot = gateway.execution_snapshot(
        code="042660", order_no="0040442", route="SOR", order_date="2026-08-12"
    )

    assert snapshot.order_qty == 2
    assert snapshot.filled_qty == 1
    assert snapshot.remaining_qty == 0
    assert snapshot.fill_price == 90000


def test_service_single_instance_lock_is_exclusive(tmp_path):
    lock_path = tmp_path / "widget-auto-trader.lock"
    first = service_module._acquire_single_instance_lock(lock_path)
    assert first is not None
    try:
        assert service_module._acquire_single_instance_lock(lock_path) is None
    finally:
        first.close()

    replacement = service_module._acquire_single_instance_lock(lock_path)
    assert replacement is not None
    replacement.close()


def test_service_symbol_allowlist_selects_only_requested_widgets(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_WIDGET_AUTO_TRADER_SYMBOLS", "A005930")
    monkeypatch.setattr(
        service_module.WidgetSymbolRuntimePolicyLoader,
        "resolve_all",
        lambda self, observed_date: {},
    )

    specs = service_module._env_specs()

    assert [spec.code for spec in specs] == ["005930"]


def test_service_adds_only_exact_date_postclose_promoted_widget_symbols(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_WIDGET_AUTO_TRADER_SYMBOLS", "005930")
    monkeypatch.setattr(
        service_module.WidgetSymbolRuntimePolicyLoader,
        "resolve_all",
        lambda self, observed_date: {"006800": {"policy_id": "verified"}},
    )

    specs = service_module._env_specs()

    assert [spec.code for spec in specs] == ["005930", "006800"]


def test_long_running_trader_refreshes_dynamic_specs_at_trade_date_boundary(tmp_path):
    dynamic_spec = WidgetSpec(
        code="888888",
        name="dynamic",
        snapshot_path=Path("unused-dynamic.json"),
        contract=FakeContract,
        event_based=True,
        dated_policy_required=True,
    )
    base_spec = WidgetSpec(
        code="999999",
        name="base",
        snapshot_path=Path("unused-base.json"),
        contract=FakeContract,
        event_based=True,
    )

    class DatePolicyLoader:
        @staticmethod
        def resolve_all(*, observed_date):
            if observed_date.isoformat() != "2026-08-13":
                return {}
            policy = _dated_policy()
            policy.update(
                symbol="888888",
                policy_id="dynamic-2026-08-13",
                leg_quantity_each=engine.WIDGET_AUTO_TRADE_LEG_QUANTITY,
            )
            return {"888888": {"KRX_REGULAR": policy}}

    trader = WidgetSignalAutoTrader(
        gateway=FakeGateway(),
        specs=(base_spec,),
        dynamic_spec_catalog=(dynamic_spec,),
        state_path=tmp_path / "state.json",
        event_recorder=FakeRecorder([]),
        snapshot_loader=lambda path: {},
        policy_loader=DatePolicyLoader(),
        enabled=True,
    )

    trader.run_once(datetime(2026, 8, 12, 10, 0, tzinfo=KST))
    assert [spec.code for spec in trader.specs] == ["999999"]
    trader.run_once(datetime(2026, 8, 13, 10, 0, tzinfo=KST))
    assert [spec.code for spec in trader.specs] == ["999999", "888888"]
    assert trader._state["execution_policies"] == {
        "888888": {"KRX_REGULAR": "dynamic-2026-08-13"}
    }
    assert trader._state["monitored_symbols"] == ["999999", "888888"]
    assert trader._state["policy_execution_eligible_symbols"] == ["888888"]
    assert trader._state["execution_eligible_symbols"] == ["888888"]
    assert trader._state["observation_only_symbols"] == ["999999"]
    assert trader._state["runtime_execution_policy_sessions"] == {
        "888888": ["KRX_REGULAR"]
    }
    trader.enabled = False
    trader._save()
    assert trader._state["policy_execution_eligible_symbols"] == ["888888"]
    assert trader._state["execution_eligible_symbols"] == []
    assert trader._state["observation_only_symbols"] == ["888888", "999999"]
    trader.run_once(datetime(2026, 8, 14, 10, 0, tzinfo=KST))
    assert [spec.code for spec in trader.specs] == ["999999"]


def test_long_running_trader_admits_late_same_day_additive_policy(
    tmp_path, monkeypatch
):
    now = datetime(2026, 8, 18, 8, 0, tzinfo=KST)
    monkeypatch.setattr(engine, "_now_kst", lambda: now)
    dynamic_spec = WidgetSpec(
        code="888888",
        name="dynamic",
        snapshot_path=Path("unused-dynamic.json"),
        contract=FakeContract,
        event_based=True,
        dated_policy_required=True,
    )
    base_spec = WidgetSpec(
        code="999999",
        name="base",
        snapshot_path=Path("unused-base.json"),
        contract=FakeContract,
        event_based=True,
    )
    loader = FakeDatedPolicyLoader({})
    trader = WidgetSignalAutoTrader(
        gateway=FakeGateway(),
        specs=(base_spec,),
        dynamic_spec_catalog=(dynamic_spec,),
        state_path=tmp_path / "state.json",
        event_recorder=FakeRecorder([]),
        snapshot_loader=lambda path: {},
        policy_loader=loader,
        entry_qty=1,
        enabled=True,
    )

    trader.run_once(now)
    assert [spec.code for spec in trader.specs] == ["999999"]

    policy = _dated_policy()
    policy.update(symbol="888888", policy_id="dynamic-same-day")
    loader.policies = {"888888": {"KRX_REGULAR": policy}}
    state = trader.run_once(now.replace(minute=1))

    assert [spec.code for spec in trader.specs] == ["999999", "888888"]
    assert state["execution_policies"] == {
        "888888": {"KRX_REGULAR": "dynamic-same-day"}
    }
    assert state["execution_eligible_symbols"] == ["888888"]
    assert state["last_policy_catalog_additions"] == {"888888": ["KRX_REGULAR"]}
    assert state["symbols"]["999999"]["orders"] == []
    assert state["symbols"]["888888"]["orders"] == []


def test_same_day_additive_policy_restart_preserves_unrelated_open_position(
    tmp_path, monkeypatch
):
    now = datetime(2026, 8, 18, 8, 30, tzinfo=KST)
    monkeypatch.setattr(engine, "_now_kst", lambda: now)
    state_path = tmp_path / "state.json"
    state_path.write_text(
        json.dumps(
            {
                "schema_version": engine.STATE_SCHEMA_VERSION,
                "execution_authority": engine.EXECUTION_AUTHORITY,
                "active_date": now.date().isoformat(),
                "execution_policies": {"999999": {"KRX_REGULAR": "base-policy"}},
                "symbols": {
                    "999999": {
                        "entry_episode_open": True,
                        "orders": [
                            {
                                "side": "BUY",
                                "broker_accepted": True,
                                "filled_qty": 1,
                                "status": "FILLED",
                            }
                        ],
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    base_spec = WidgetSpec(
        code="999999",
        name="base",
        snapshot_path=Path("unused-base.json"),
        contract=FakeContract,
        event_based=True,
        dated_policy_required=True,
    )
    dynamic_spec = WidgetSpec(
        code="888888",
        name="dynamic",
        snapshot_path=Path("unused-dynamic.json"),
        contract=FakeContract,
        event_based=True,
        dated_policy_required=True,
    )
    base_policy = _dated_policy()
    base_policy.update(policy_id="base-policy")
    dynamic_policy = _dated_policy()
    dynamic_policy.update(symbol="888888", policy_id="dynamic-policy")

    trader = WidgetSignalAutoTrader(
        gateway=FakeGateway(),
        specs=(base_spec, dynamic_spec),
        dynamic_spec_catalog=(dynamic_spec,),
        state_path=state_path,
        event_recorder=FakeRecorder([]),
        snapshot_loader=lambda path: {},
        policy_loader=FakeDatedPolicyLoader(
            {
                "999999": {"KRX_REGULAR": base_policy},
                "888888": {"KRX_REGULAR": dynamic_policy},
            }
        ),
        entry_qty=1,
        enabled=True,
    )

    assert trader._state["symbols"]["999999"]["entry_episode_open"] is True
    assert trader._open_qty(trader._state["symbols"]["999999"]) == 1


def test_service_explicit_samsung_execution_policy_is_attached(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_WIDGET_AUTO_TRADER_SYMBOLS", "005930")
    monkeypatch.setenv(
        "KORSTOCKSCAN_WIDGET_AUTO_TRADER_SAMSUNG_EXECUTION_POLICY",
        engine.SAMSUNG_DAILY_EQUAL_SHARE_POLICY_ID,
    )
    monkeypatch.setattr(
        service_module.WidgetSymbolRuntimePolicyLoader,
        "resolve_all",
        lambda self, observed_date: {},
    )

    specs = service_module._env_specs()

    assert len(specs) == 1
    assert specs[0].execution_policy_id == engine.SAMSUNG_DAILY_EQUAL_SHARE_POLICY_ID


def test_service_unknown_samsung_execution_policy_fails_closed(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_WIDGET_AUTO_TRADER_SYMBOLS", "005930")
    monkeypatch.setenv(
        "KORSTOCKSCAN_WIDGET_AUTO_TRADER_SAMSUNG_EXECUTION_POLICY", "UNKNOWN"
    )

    with pytest.raises(ValueError, match="widget_auto_trader_samsung_policy_unknown"):
        service_module._env_specs()


@pytest.mark.parametrize("value", ["", "999999", "005930,999999"])
def test_service_symbol_allowlist_fails_closed_for_invalid_values(monkeypatch, value):
    monkeypatch.setenv("KORSTOCKSCAN_WIDGET_AUTO_TRADER_SYMBOLS", value)
    monkeypatch.setattr(
        service_module.WidgetSymbolRuntimePolicyLoader,
        "resolve_all",
        lambda self, observed_date: {},
    )

    with pytest.raises(ValueError, match="widget_auto_trader_symbols_"):
        service_module._env_specs()


def test_service_symbol_allowlist_omission_preserves_legacy_specs(monkeypatch):
    monkeypatch.delenv("KORSTOCKSCAN_WIDGET_AUTO_TRADER_SYMBOLS", raising=False)
    monkeypatch.delenv(
        "KORSTOCKSCAN_WIDGET_AUTO_TRADER_SAMSUNG_EXECUTION_POLICY", raising=False
    )
    monkeypatch.setattr(
        service_module.WidgetSymbolRuntimePolicyLoader,
        "resolve_all",
        lambda self, observed_date: {},
    )

    assert service_module._env_specs() == engine.DEFAULT_WIDGET_SPECS


def test_service_entry_quantity_defaults_to_ten_and_allows_explicit_ten(monkeypatch):
    monkeypatch.delenv("KORSTOCKSCAN_WIDGET_AUTO_TRADER_ENTRY_QTY", raising=False)
    assert service_module._env_qty() == 10

    monkeypatch.setenv("KORSTOCKSCAN_WIDGET_AUTO_TRADER_ENTRY_QTY", "10")
    assert service_module._env_qty() == 10


def test_systemd_service_is_static_and_daily_timer_is_single_start_owner():
    service = Path(
        "deploy/systemd/korstockscan-widget-signal-auto-trader.service"
    ).read_text(encoding="utf-8")
    timer = Path(
        "deploy/systemd/korstockscan-widget-signal-auto-trader.timer"
    ).read_text(encoding="utf-8")

    assert "WantedBy=multi-user.target" not in service
    assert (
        'Environment="KORSTOCKSCAN_WIDGET_AUTO_TRADER_SYMBOLS=005930,034020,042660"'
        in service
    )
    assert (
        'Environment="KORSTOCKSCAN_WIDGET_AUTO_TRADER_SAMSUNG_EXECUTION_POLICY='
        'SAMSUNG_EQUAL_10_ADD0P5_ADD1P0_TP0P5_V2"' in service
    )
    assert 'Environment="KORSTOCKSCAN_WIDGET_AUTO_TRADER_ENTRY_QTY=10"' in service
    assert "OnCalendar=Mon..Fri *-*-* 07:58:00 Asia/Seoul" in timer
    assert "Persistent=true" in timer
    assert "AccuracySec=1s" in timer
    assert "Unit=korstockscan-widget-signal-auto-trader.service" in timer
    assert "WantedBy=timers.target" in timer


def test_postclose_widget_evaluation_writes_next_day_execution_policy():
    service = Path(
        "deploy/systemd/korstockscan-samsung-widget-evaluation.service"
    ).read_text(encoding="utf-8")
    wrapper = Path("deploy/run_widget_evaluation.sh").read_text(encoding="utf-8")

    assert service.count("ExecStart=") == 1
    assert (
        "ExecStart=/home/ubuntu/KORStockScan/deploy/run_widget_evaluation.sh" in service
    )
    assert "resolve_completed_policy_target_date" in wrapper
    assert "widget_advisory_calibration" in wrapper
    assert '--target-date "$completed_target_date"' in wrapper
    assert '--end-date "$completed_target_date"' in wrapper


def test_widget_evaluation_wrapper_reuses_one_completed_date(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    call_log = tmp_path / "calls.log"
    fake_python = tmp_path / "fake-python"
    fake_python.write_text(
        "#!/usr/bin/env bash\n"
        "set -eu\n"
        'if [[ "${1:-}" == "-c" ]]; then\n'
        "  printf 'dependency startup banner\\n'\n"
        "  printf '2026-08-14\\n'\n"
        "else\n"
        '  printf \'%s\\n\' "$*" >> "$CALL_LOG"\n'
        "fi\n",
        encoding="utf-8",
    )
    fake_python.chmod(0o755)
    monkeypatch.setenv("KORSTOCKSCAN_PROJECT_DIR", str(Path.cwd()))
    monkeypatch.setenv("KORSTOCKSCAN_PYTHON_BIN", str(fake_python))
    monkeypatch.setenv("CALL_LOG", str(call_log))

    completed = subprocess.run(
        ["bash", "deploy/run_widget_evaluation.sh"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    calls = call_log.read_text(encoding="utf-8").splitlines()
    assert calls == [
        "-m src.engine.monitoring.widget_advisory_calibration --target-date 2026-08-14 --write",
        "-m src.engine.monitoring.widget_auto_trade_policy_calibration --target-date 2026-08-14 --write",
        "-m src.engine.monitoring.widget_symbol_signal_policy_research --end-date 2026-08-14 --write",
        "-m src.engine.monitoring.widget_symbol_runtime_policy --target-date 2026-08-14 --write",
    ]
    assert "completed target_date=2026-08-14" in completed.stdout


def test_calibrated_widget_symbol_collector_is_exact_date_policy_gated():
    service = Path(
        "deploy/systemd/korstockscan-widget-symbol-runtime-collector.service"
    ).read_text(encoding="utf-8")
    timer = Path(
        "deploy/systemd/korstockscan-widget-symbol-runtime-collector.timer"
    ).read_text(encoding="utf-8")

    assert "widget_symbol_runtime_policy --check-active" in service
    assert "widget_symbol_runtime_collector --interval-sec 15" in service
    assert "Restart=on-failure" in service
    assert "OnCalendar=Mon..Fri *-*-* 08:57:00 Asia/Seoul" in timer
    assert "Persistent=true" in timer
