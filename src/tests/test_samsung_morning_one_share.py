from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path
import pytest

from src.engine.risk.market_weakness_entry_guard import (
    MarketWeaknessEntryDecision,
)
from src.trading.order import regular_two_leg_machine as regular_machine_module
from src.trading.order.entry_liquidity_guard import (
    EntryExecutionVelocitySnapshot,
    EntryLiquiditySnapshot,
)

from src.trading.samsung_morning_one_share import gateway as gateway_module
from src.trading.samsung_morning_one_share.gateway import (
    ExecutionSnapshot,
    KiwoomOneShareGateway,
    MinuteBarsSnapshot,
    OpenPriceSnapshot,
    SubmitResult,
)
from src.trading.samsung_morning_one_share.machine import (
    KST,
    SamsungMorningOneShareMachine,
)
from src.trading.samsung_morning_one_share.policy import DEFAULT_POLICY
from src.trading.samsung_morning_one_share import service as service_module


@pytest.fixture(autouse=True)
def _isolate_market_weakness_counterfactual_writer(monkeypatch):
    monkeypatch.setattr(
        regular_machine_module,
        "record_market_weakness_blocked_entry",
        lambda *_args, **_kwargs: {
            "status": "test_isolated",
            "observation_id": "test-market-weakness-block",
            "path": "test-only",
        },
    )


class FakeGateway:
    def __init__(self) -> None:
        self.opens = {"NXT": 300_000, "SOR": 300_000}
        self.buy_calls: list[tuple[str, int]] = []
        self.limit_sell_calls: list[tuple[str, int]] = []
        self.cancel_calls: list[tuple[str, str]] = []
        self.snapshots: dict[str, ExecutionSnapshot] = {}
        self.sequence = 0
        self.best_bid_qty = 1_000
        self.best_ask_qty = 1_000
        self.liquidity_calls: list[str] = []
        self.execution_velocity_span_ms = 1_000
        self.execution_velocity_calls: list[str] = []

    def _accepted(self, prefix: str) -> SubmitResult:
        self.sequence += 1
        return SubmitResult(True, f"{prefix}{self.sequence}", "0", "OK")

    def opening_price(self, *, route, trade_date):
        price = self.opens.get(route)
        return OpenPriceSnapshot(bool(price), price, f"{trade_date:%Y%m%d}080000")

    def entry_liquidity_snapshot(self, *, route="SOR"):
        self.liquidity_calls.append(route)
        suffix = "NX" if route == "NXT" else "AL"
        return EntryLiquiditySnapshot(
            True,
            "005930",
            route,
            f"005930_{suffix}",
            best_bid=300_000,
            best_ask=300_500,
            best_bid_qty=self.best_bid_qty,
            best_ask_qty=self.best_ask_qty,
            age_ms=0,
            received_ts_ms=1,
        )

    def entry_execution_velocity_snapshot(self, *, route="SOR"):
        self.execution_velocity_calls.append(route)
        suffix = "NX" if route == "NXT" else "AL"
        return EntryExecutionVelocitySnapshot(
            True,
            "005930",
            route,
            f"005930_{suffix}",
            print_count=10,
            recent_print_span_ms=self.execution_velocity_span_ms,
            latest_print_age_ms=0,
            recent_volume=1_000,
            observed_at_kst="2026-08-12T09:00:00+09:00",
            print_times=("090000",) * 10,
            venues=(("NXT",) * 10 if route == "NXT" else ("KRX",) * 10),
        )

    def submit_limit_buy(self, *, price, quantity, route="SOR"):
        assert quantity in {1, 10}
        self.buy_calls.append((route, price))
        return self._accepted("B")

    def submit_limit_sell(self, *, price, quantity, route="SOR"):
        assert 1 <= quantity <= 10
        self.limit_sell_calls.append((route, price))
        return self._accepted("T")

    def cancel(self, *, route, order_no):
        self.cancel_calls.append((route, order_no))
        return self._accepted("C")

    def cancel_buy(self, *, order_no):
        return self.cancel(route="SOR", order_no=order_no)

    def execution_snapshot(
        self, *, order_no, order_date, expected_order_qty, route="SOR"
    ):
        snapshot = self.snapshots.get(
            order_no,
            ExecutionSnapshot(True, True, 0, expected_order_qty, expected_order_qty),
        )
        if snapshot.order_qty == 1 and expected_order_qty == 10:
            return ExecutionSnapshot(
                snapshot.source_ok,
                snapshot.found,
                snapshot.filled_qty * 10,
                snapshot.remaining_qty * 10,
                10,
                snapshot.fill_price,
                snapshot.error,
            )
        return snapshot


def _at(day: int, hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 8, day, hour, minute, tzinfo=KST)


def _machine(tmp_path: Path, gateway: FakeGateway, *, live: bool = True):
    return SamsungMorningOneShareMachine(
        gateway=gateway,
        state_path=tmp_path / "state.json",
        live_enabled=live,
        ownership_source=lambda code: "manual_operator",
    )


def test_policy_prices_are_fixed_to_two_independent_ten_share_legs():
    assert DEFAULT_POLICY.quantity == 20
    assert DEFAULT_POLICY.symbol == "005930"
    assert DEFAULT_POLICY.nxt.route == "NXT"
    assert DEFAULT_POLICY.sor.route == "SOR"
    assert DEFAULT_POLICY.entry_price(300_000, 3.0) == 291_000
    assert DEFAULT_POLICY.entry_price(300_000, 0.75) == 297_500
    assert [leg["entry_price"] for leg in DEFAULT_POLICY.entry_legs(300_000, 3.0)] == [
        291_500,
        291_000,
    ]
    assert DEFAULT_POLICY.target_price(291_000) == 292_000


def test_market_weakness_guard_preserves_morning_attempt_for_release(
    tmp_path, monkeypatch
):
    gateway = FakeGateway()
    machine = _machine(tmp_path, gateway)

    def decision(blocked: bool):
        return MarketWeaknessEntryDecision(
            blocked=blocked,
            reason=(
                "entry_blocked_market_weakness_active"
                if blocked
                else "market_weakness_latch_not_active"
            ),
            symbol="005930",
            owner="episode",
            listing_market="KOSPI",
            phase="active" if blocked else "released",
            active_markets=("KOSPI",) if blocked else (),
            session_key="2026-08-11",
            observation_id="weakness-2",
            observation_as_of="2026-08-11T08:01:00+09:00",
            source_status="test",
            state_path="test-state.json",
            symbol_master_path="test-master.json",
        )

    monkeypatch.setattr(
        regular_machine_module,
        "evaluate_market_weakness_entry_guard",
        lambda **kwargs: decision(True),
    )
    blocked = machine.run_once(_at(11, 8, 1))
    assert blocked["attempt_consumed"] is False
    assert blocked["legs"] == []
    assert gateway.buy_calls == []
    assert blocked["last_action"] == "entry_blocked_market_weakness_active"

    monkeypatch.setattr(
        regular_machine_module,
        "evaluate_market_weakness_entry_guard",
        lambda **kwargs: decision(False),
    )
    released = machine.run_once(_at(11, 8, 1))
    assert released["attempt_consumed"] is True
    assert gateway.buy_calls == [("NXT", 291_500), ("NXT", 291_000)]


def test_market_weakness_cancels_nxt_buys_and_blocks_sor_fallback(
    tmp_path, monkeypatch
):
    gateway = FakeGateway()
    machine = _machine(tmp_path, gateway)
    started_at = _at(11, 8, 1)
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
            owner="episode",
            listing_market="KOSPI",
            phase="active" if active else "released",
            active_markets=("KOSPI",) if active else (),
            session_key=started_at.date().isoformat(),
            observation_id="weakness-morning-cancel-1",
            observation_as_of=started_at.isoformat(),
            source_status="test",
            state_path="test-state.json",
            symbol_master_path="test-master.json",
        )

    monkeypatch.setattr(
        regular_machine_module,
        "evaluate_market_weakness_entry_guard",
        lambda **kwargs: decision(),
    )
    machine.run_once(started_at)
    mode["value"] = "active"

    canceled = machine.run_once(started_at + timedelta(seconds=1))

    assert gateway.cancel_calls == [("NXT", "B1"), ("NXT", "B2")]
    assert {leg["status"] for leg in canceled["legs"]} == {"BUY_CANCEL_PENDING"}
    gateway.snapshots["B1"] = ExecutionSnapshot(True, True, 0, 0, 10)
    gateway.snapshots["B2"] = ExecutionSnapshot(True, True, 0, 0, 10)

    resolved = machine.run_once(started_at + timedelta(seconds=2))

    assert gateway.buy_calls == [("NXT", 291_500), ("NXT", 291_000)]
    assert all(leg["route"] == "SOR" for leg in resolved["legs"])
    assert resolved["last_action"] == "entry_blocked_market_weakness_active"


def test_nxt_fills_submit_independent_two_tick_targets_and_complete(tmp_path):
    gateway = FakeGateway()
    machine = _machine(tmp_path, gateway)

    submitted = machine.run_once(_at(11, 8, 1))
    assert gateway.buy_calls == [("NXT", 291_500), ("NXT", 291_000)]
    assert submitted["status"] == "BUY_OPEN"

    gateway.snapshots["B1"] = ExecutionSnapshot(True, True, 1, 0, 1, 291_500)
    gateway.snapshots["B2"] = ExecutionSnapshot(True, True, 1, 0, 1, 291_000)
    filled = machine.run_once(_at(11, 8, 2))
    assert filled["attempt_consumed"] is True
    assert filled["position_qty"] == 20
    assert gateway.limit_sell_calls == [("NXT", 292_500), ("NXT", 292_000)]

    gateway.snapshots["T3"] = ExecutionSnapshot(True, True, 1, 0, 1, 292_500)
    gateway.snapshots["T4"] = ExecutionSnapshot(True, True, 1, 0, 1, 292_000)
    closed = machine.run_once(_at(11, 8, 3))
    assert closed["status"] == "COMPLETE"
    assert closed["position_qty"] == 0
    assert len(gateway.buy_calls) == 2


def test_nxt_entry_confirmation_delay_changes_only_submission_time(
    tmp_path, monkeypatch
):
    gateway = FakeGateway()
    calls: list[dict] = []

    def timing_policy(**kwargs):
        calls.append(kwargs)
        return (
            3,
            {
                "status": "applied",
                "policy_hash": "a" * 64,
                "target_date": kwargs["target_date"].isoformat(),
            },
        )

    monkeypatch.setattr(
        "src.trading.samsung_morning_one_share.machine.resolve_entry_confirmation_delay",
        timing_policy,
    )
    machine = _machine(tmp_path, gateway)
    armed_at = _at(11, 8, 1)

    armed = machine.run_once(armed_at)
    submitted = machine.run_once(armed_at + timedelta(seconds=3))

    assert armed["status"] == "READY"
    assert armed["attempt_consumed"] is False
    assert armed["pending_entry_confirmation"]["delay_sec"] == 3
    assert gateway.buy_calls == [("NXT", 291_500), ("NXT", 291_000)]
    assert submitted["signal_features"]["signal_decision_at"] == armed_at.isoformat()
    assert submitted["signal_features"]["entry_confirmation_delay_sec"] == 3
    assert all(call["session"] == "NXT_PREMARKET" for call in calls)


def test_nxt_cancel_must_reconcile_before_sor_regular_fallback(tmp_path):
    gateway = FakeGateway()
    machine = _machine(tmp_path, gateway)
    machine.run_once(_at(11, 8, 1))

    cancel_pending = machine.run_once(_at(11, 8, 11))
    assert cancel_pending["status"] == "BUY_CANCEL_PENDING"
    assert gateway.cancel_calls == [("NXT", "B1"), ("NXT", "B2")]

    gateway.snapshots["B1"] = ExecutionSnapshot(True, True, 0, 0, 1)
    gateway.snapshots["B2"] = ExecutionSnapshot(True, True, 0, 0, 1)
    resolved = machine.run_once(_at(11, 8, 12))
    assert {leg["route"] for leg in resolved["legs"]} == {"SOR"}
    assert {leg["status"] for leg in resolved["legs"]} == {"PLANNED"}
    assert gateway.buy_calls == [("NXT", 291_500), ("NXT", 291_000)]

    sor = machine.run_once(_at(11, 9, 0))
    assert {leg["route"] for leg in sor["legs"]} == {"SOR"}
    assert gateway.buy_calls[-2:] == [("SOR", 298_000), ("SOR", 297_500)]
    assert sor["signal_features"]["opening_prices"] == {"SOR": 300_000}
    assert sor["signal_features"]["entry_windows"] == {
        "SOR": {"start": "09:00:00", "deadline": "09:30:00"}
    }
    assert gateway.liquidity_calls == ["NXT", "SOR"]


def test_late_start_arms_sor_fallback_without_attempting_nxt(tmp_path):
    gateway = FakeGateway()
    machine = _machine(tmp_path, gateway)
    waiting = machine.run_once(_at(11, 8, 30))
    assert waiting["status"] == "BUY_OPEN"
    assert {leg["route"] for leg in waiting["legs"]} == {"SOR"}
    assert {leg["status"] for leg in waiting["legs"]} == {"PLANNED"}
    assert gateway.buy_calls == []
    assert gateway.liquidity_calls == []

    submitted = machine.run_once(_at(11, 9, 0))
    assert submitted["status"] == "BUY_OPEN"
    assert gateway.buy_calls == [("SOR", 298_000), ("SOR", 297_500)]
    assert gateway.liquidity_calls == ["SOR"]
    assert submitted["signal_features"]["opening_price"] == 300_000
    assert [
        leg["entry_price"] for leg in submitted["signal_features"]["entry_legs"]
    ] == [298_000, 297_500]


def test_start_during_sor_window_uses_sor_open_directly(tmp_path):
    gateway = FakeGateway()
    state = _machine(tmp_path, gateway).run_once(_at(11, 9, 1))
    assert state["status"] == "BUY_OPEN"
    assert gateway.buy_calls == [("SOR", 298_000), ("SOR", 297_500)]


def test_thin_nxt_book_blocks_both_morning_legs_without_any_buy(tmp_path):
    gateway = FakeGateway()
    gateway.best_bid_qty = 97
    gateway.best_ask_qty = 93

    state = _machine(tmp_path, gateway).run_once(_at(11, 8, 1))

    assert state["status"] == "NO_TRADE"
    assert state["position_qty"] == 0
    assert {leg["status"] for leg in state["legs"]} == {"NO_FILL"}
    assert state["last_action"] == "entry_liquidity_blocked_before_buy"
    assert gateway.liquidity_calls == ["NXT"]
    assert gateway.buy_calls == []


def test_slow_nxt_prints_block_both_morning_legs_without_any_buy(tmp_path):
    gateway = FakeGateway()
    gateway.execution_velocity_span_ms = 29_000

    state = _machine(tmp_path, gateway).run_once(_at(11, 8, 1))

    assert state["status"] == "NO_TRADE"
    assert state["position_qty"] == 0
    assert {leg["status"] for leg in state["legs"]} == {"NO_FILL"}
    assert state["last_action"] == "entry_execution_velocity_blocked_before_buy"
    assert state["blocked_reason"] == "entry_execution_velocity_too_slow"
    assert gateway.liquidity_calls == ["NXT"]
    assert gateway.execution_velocity_calls == ["NXT"]
    assert gateway.buy_calls == []


def test_filled_nxt_leg_keeps_target_while_only_unfilled_leg_falls_back(tmp_path):
    gateway = FakeGateway()
    machine = _machine(tmp_path, gateway)
    machine.run_once(_at(11, 8, 1))
    gateway.snapshots["B1"] = ExecutionSnapshot(True, True, 1, 0, 1, 291_500)
    partial = machine.run_once(_at(11, 8, 2))
    assert partial["position_qty"] == 10
    assert gateway.limit_sell_calls == [("NXT", 292_500)]

    pending = machine.run_once(_at(11, 8, 11))
    assert pending["status"] == "BUY_CANCEL_PENDING"
    assert gateway.cancel_calls == [("NXT", "B2")]
    gateway.snapshots["B2"] = ExecutionSnapshot(True, True, 0, 0, 1)
    machine.run_once(_at(11, 8, 12))
    mixed = machine.run_once(_at(11, 9, 0))
    assert gateway.buy_calls[-1] == ("SOR", 297_500)
    assert gateway.limit_sell_calls == [("NXT", 292_500)]
    assert mixed["signal_features"]["route"] == "MIXED"
    assert mixed["signal_features"]["opening_prices"] == {
        "NXT": 300_000,
        "SOR": 300_000,
    }
    assert mixed["signal_features"]["entry_windows"] == {
        "NXT": {"start": "08:00:00", "deadline": "08:10:00"},
        "SOR": {"start": "09:00:00", "deadline": "09:30:00"},
    }
    assert {leg["route"] for leg in mixed["signal_features"]["entry_legs"]} == {
        "NXT",
        "SOR",
    }


def test_target_has_no_timeout_cancel_or_forced_exit(tmp_path):
    gateway = FakeGateway()
    machine = _machine(tmp_path, gateway)
    machine.run_once(_at(11, 8, 1))
    gateway.snapshots["B1"] = ExecutionSnapshot(True, True, 1, 0, 1, 291_500)
    gateway.snapshots["B2"] = ExecutionSnapshot(True, True, 1, 0, 1, 291_000)
    machine.run_once(_at(11, 8, 2))

    still_open = machine.run_once(_at(11, 8, 15))
    assert still_open["status"] == "TARGET_OPEN"
    assert still_open["position_qty"] == 20
    assert gateway.cancel_calls == []
    assert gateway.limit_sell_calls == [("NXT", 292_500), ("NXT", 292_000)]


def test_target_closed_unfilled_keeps_one_share_held(tmp_path):
    gateway = FakeGateway()
    machine = _machine(tmp_path, gateway)
    machine.run_once(_at(11, 8, 1))
    gateway.snapshots["B1"] = ExecutionSnapshot(True, True, 1, 0, 1, 291_500)
    gateway.snapshots["B2"] = ExecutionSnapshot(True, True, 1, 0, 1, 291_000)
    machine.run_once(_at(11, 8, 2))
    gateway.snapshots["T3"] = ExecutionSnapshot(True, True, 0, 0, 1)
    gateway.snapshots["T4"] = ExecutionSnapshot(True, True, 0, 0, 1)
    held = machine.run_once(_at(11, 20, 1))
    assert held["status"] == "HELD"
    assert held["position_qty"] == 20
    assert held["last_action"] == "target_closed_with_position_held"
    assert gateway.cancel_calls == []
    assert gateway.buy_calls == [("NXT", 291_500), ("NXT", 291_000)]

    carried = machine.run_once(_at(12, 8, 1))
    assert carried["status"] == "HELD"
    assert carried["position_qty"] == 20
    assert gateway.buy_calls == [("NXT", 291_500), ("NXT", 291_000)]


def test_open_target_reconciles_across_trade_date_without_new_entry(tmp_path):
    gateway = FakeGateway()
    machine = _machine(tmp_path, gateway)
    machine.run_once(_at(11, 8, 1))
    gateway.snapshots["B1"] = ExecutionSnapshot(True, True, 1, 0, 1, 291_500)
    gateway.snapshots["B2"] = ExecutionSnapshot(True, True, 1, 0, 1, 291_000)
    machine.run_once(_at(11, 8, 2))

    carried = machine.run_once(_at(12, 8, 1))
    assert carried["status"] == "TARGET_OPEN"
    assert carried["position_qty"] == 20
    assert gateway.buy_calls == [("NXT", 291_500), ("NXT", 291_000)]
    assert gateway.cancel_calls == []


def test_no_operator_exclusion_blocks_new_buy(tmp_path):
    gateway = FakeGateway()
    machine = SamsungMorningOneShareMachine(
        gateway=gateway,
        state_path=tmp_path / "state.json",
        live_enabled=True,
        ownership_source=lambda code: "",
    )
    state = machine.run_once(_at(11, 8, 1))
    assert state["blocked_reason"] == "005930_not_excluded_from_primary_bot"
    assert gateway.buy_calls == []


def test_dry_run_only_previews_and_never_calls_order_gateway(tmp_path):
    gateway = FakeGateway()
    machine = _machine(tmp_path, gateway, live=False)
    state = machine.run_once(_at(11, 8, 1))
    assert state["last_action"] == "would_submit_nxt_two_leg_buy"
    assert state["preview"]["total_quantity"] == 20
    assert [leg["entry_price"] for leg in state["preview"]["legs"]] == [
        291_500,
        291_000,
    ]
    assert state["preview"]["widget_relationship"] == "parallel_independent_strategy"
    assert gateway.buy_calls == []


def test_dry_run_reports_missing_ownership_without_mutating_runtime(tmp_path):
    gateway = FakeGateway()
    machine = SamsungMorningOneShareMachine(
        gateway=gateway,
        state_path=tmp_path / "state.json",
        live_enabled=False,
        ownership_source=lambda code: "",
    )
    state = machine.run_once(_at(11, 8, 1))
    assert state["last_action"] == "would_submit_nxt_two_leg_buy"
    assert state["preview"]["operator_exclusion_ready"] is False
    assert gateway.buy_calls == []


def test_unresolved_previous_day_blocks_rollover(tmp_path):
    gateway = FakeGateway()
    machine = _machine(tmp_path, gateway)
    machine.run_once(_at(11, 8, 1))
    blocked = machine.run_once(_at(12, 8, 1))
    assert blocked["status"] == "BLOCKED"
    assert blocked["blocked_reason"] == "previous_day_order_or_position_unresolved"
    assert len(gateway.buy_calls) == 2


def test_reconciliation_blocks_order_number_not_in_machine_ledger(tmp_path):
    gateway = FakeGateway()
    state_path = tmp_path / "state.json"
    machine = SamsungMorningOneShareMachine(
        gateway=gateway,
        state_path=state_path,
        live_enabled=True,
        ownership_source=lambda code: "manual_operator",
    )
    machine.run_once(_at(11, 8, 1))
    payload = machine.snapshot()
    payload["legs"][0]["buy_order_no"] = "WIDGET-ORDER-77"
    state_path.write_text(__import__("json").dumps(payload), encoding="utf-8")

    restarted = SamsungMorningOneShareMachine(
        gateway=gateway,
        state_path=state_path,
        live_enabled=True,
        ownership_source=lambda code: "manual_operator",
    )
    blocked = restarted.run_once(_at(11, 8, 2))
    assert blocked["status"] == "BLOCKED"
    assert blocked["blocked_reason"] == "state_buy_order_no_ownership_invalid"


def test_restart_after_broker_write_intent_never_repeats_order(tmp_path):
    gateway = FakeGateway()
    state_path = tmp_path / "state.json"
    machine = SamsungMorningOneShareMachine(
        gateway=gateway,
        state_path=state_path,
        live_enabled=True,
        ownership_source=lambda code: "manual_operator",
    )
    machine.run_once(_at(11, 8, 1))
    payload = machine.snapshot()
    payload["status"] = "BUY_SUBMITTING"
    payload["legs"][0]["status"] = "BUY_SUBMITTING"
    payload["legs"][0]["buy_order_no"] = ""
    state_path.write_text(__import__("json").dumps(payload), encoding="utf-8")

    restarted = SamsungMorningOneShareMachine(
        gateway=gateway,
        state_path=state_path,
        live_enabled=True,
        ownership_source=lambda code: "manual_operator",
    )
    blocked = restarted.run_once(_at(11, 8, 2))
    assert blocked["status"] == "BLOCKED"
    assert (
        blocked["blocked_reason"]
        == "broker_write_interrupted:base_plus_1tick:buy_submitting"
    )
    assert gateway.buy_calls == [("NXT", 291_500), ("NXT", 291_000)]


def test_timeout_during_submit_leaves_write_intent_for_fail_closed_restart(tmp_path):
    class TimeoutGateway(FakeGateway):
        def submit_limit_buy(self, *, route, price, quantity):
            self.buy_calls.append((route, price))
            raise TimeoutError("broker response unknown")

    gateway = TimeoutGateway()
    state_path = tmp_path / "state.json"
    machine = SamsungMorningOneShareMachine(
        gateway=gateway,
        state_path=state_path,
        live_enabled=True,
        ownership_source=lambda code: "manual_operator",
    )
    with pytest.raises(TimeoutError):
        machine.run_once(_at(11, 8, 1))

    restarted = SamsungMorningOneShareMachine(
        gateway=gateway,
        state_path=state_path,
        live_enabled=True,
        ownership_source=lambda code: "manual_operator",
    )
    blocked = restarted.run_once(_at(11, 8, 2))
    assert blocked["status"] == "BLOCKED"
    assert (
        blocked["blocked_reason"]
        == "broker_write_interrupted:base_plus_1tick:buy_submitting"
    )
    assert gateway.buy_calls == [("NXT", 291_500)]


class FakeResponse:
    def __init__(self, body, *, status_code=200, headers=None):
        self._body = body
        self.status_code = status_code
        self.headers = headers or {}

    def json(self):
        return self._body


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.responses.pop(0)


def test_gateway_hard_codes_symbol_quantity_limit_order_and_shared_token(monkeypatch):
    monkeypatch.setattr(gateway_module, "is_buy_side_paused", lambda: False)
    session = FakeSession([FakeResponse({"return_code": 0, "ord_no": "123"})])
    gateway = KiwoomOneShareGateway(
        request_session=session,
        token_loader=lambda: "SHARED_TOKEN",
        order_authority=True,
        base_url="https://api.kiwoom.com",
    )
    result = gateway.submit_limit_buy(route="NXT", price=291_000, quantity=10)
    assert result.accepted is True
    _, call = session.calls[0]
    assert call["headers"]["authorization"] == "Bearer SHARED_TOKEN"
    assert call["headers"]["api-id"] == "kt10000"
    assert call["json"] == {
        "dmst_stex_tp": "NXT",
        "stk_cd": "005930",
        "ord_qty": "10",
        "ord_uv": "291000",
        "trde_tp": "0",
        "cond_uv": "",
    }


def test_gateway_supports_sor_regular_limit_orders(monkeypatch):
    monkeypatch.setattr(gateway_module, "is_buy_side_paused", lambda: False)
    session = FakeSession([FakeResponse({"return_code": 0, "ord_no": "124"})])
    gateway = KiwoomOneShareGateway(
        request_session=session,
        token_loader=lambda: "SHARED_TOKEN",
        order_authority=True,
        base_url="https://api.kiwoom.com",
    )
    result = gateway.submit_limit_buy(price=297_500, quantity=10)
    assert result.accepted is True
    assert session.calls[0][1]["json"]["dmst_stex_tp"] == "SOR"


def test_gateway_write_is_disabled_without_both_authority_and_production():
    disabled = KiwoomOneShareGateway(
        token_loader=lambda: "token", order_authority=False
    )
    with pytest.raises(PermissionError, match="authority_disabled"):
        disabled.submit_limit_buy(route="SOR", price=297_500, quantity=10)

    wrong_endpoint = KiwoomOneShareGateway(
        token_loader=lambda: "token",
        order_authority=True,
        base_url="https://example.test",
    )
    with pytest.raises(PermissionError, match="production_endpoint"):
        wrong_endpoint.submit_limit_buy(route="SOR", price=297_500, quantity=10)


def test_gateway_rejects_direct_krx_route_for_regular_session(monkeypatch):
    monkeypatch.setattr(gateway_module, "is_buy_side_paused", lambda: False)
    gateway = KiwoomOneShareGateway(
        request_session=FakeSession([]),
        token_loader=lambda: "token",
        order_authority=True,
        base_url="https://api.kiwoom.com",
    )
    with pytest.raises(ValueError, match="invalid_order_route"):
        gateway.submit_limit_buy(route="KRX", price=297_500, quantity=10)


def test_gateway_open_price_uses_only_official_ka10080_fields():
    session = FakeSession(
        [
            FakeResponse(
                {
                    "return_code": 0,
                    "stk_min_pole_chart_qry": [
                        {"cntr_tm": "20260811080000", "open_pric": "+300000"}
                    ],
                }
            )
        ]
    )
    gateway = KiwoomOneShareGateway(
        request_session=session,
        token_loader=lambda: "token",
        base_url="https://api.kiwoom.com",
    )
    snapshot = gateway.opening_price(route="NXT", trade_date=_at(11, 8).date())
    assert snapshot.source_ok is True
    assert snapshot.price == 300_000
    assert session.calls[0][1]["json"] == {
        "stk_cd": "005930_NX",
        "tic_scope": "1",
        "upd_stkpc_tp": "1",
    }


def test_gateway_completed_sor_bars_uses_official_al_code_and_excludes_current_bar():
    session = FakeSession(
        [
            FakeResponse(
                {
                    "return_code": 0,
                    "stk_min_pole_chart_qry": [
                        {
                            "cntr_tm": "20260811091800",
                            "open_pric": "+100200",
                            "high_pric": "+100400",
                            "low_pric": "+100100",
                            "cur_prc": "+100300",
                        },
                        {
                            "cntr_tm": "20260811091700",
                            "open_pric": "+100100",
                            "high_pric": "+100300",
                            "low_pric": "+100000",
                            "cur_prc": "+100200",
                        },
                    ],
                }
            )
        ]
    )
    gateway = KiwoomOneShareGateway(
        request_session=session,
        token_loader=lambda: "token",
        base_url="https://api.kiwoom.com",
    )

    snapshot = gateway.completed_sor_minute_bars(
        trade_date=date(2026, 8, 11), now=_at(11, 9, 18)
    )

    assert isinstance(snapshot, MinuteBarsSnapshot)
    assert snapshot.source_ok is True
    assert len(snapshot.bars) == 1
    assert snapshot.bars[0].timestamp == _at(11, 9, 17)
    assert session.calls[0][1]["headers"]["api-id"] == "ka10080"
    assert session.calls[0][1]["json"] == {
        "stk_cd": "005930_AL",
        "tic_scope": "1",
        "upd_stkpc_tp": "1",
    }


def test_gateway_reconciles_only_machine_order_among_parallel_widget_orders():
    session = FakeSession(
        [
            FakeResponse(
                {
                    "return_code": 0,
                    "orders": [
                        {
                            "stk_cd": "005930",
                            "ord_no": "WIDGET-77",
                            "ord_qty": "1",
                            "cntr_qty": "1",
                            "ord_remnq": "0",
                            "cntr_uv": "300000",
                        },
                        {
                            "stk_cd": "005930",
                            "ord_no": "ONE-SHARE-11",
                            "ord_qty": "1",
                            "cntr_qty": "0",
                            "ord_remnq": "1",
                            "cntr_uv": "0",
                        },
                    ],
                }
            )
        ]
    )
    gateway = KiwoomOneShareGateway(
        request_session=session,
        token_loader=lambda: "token",
        base_url="https://api.kiwoom.com",
    )
    snapshot = gateway.execution_snapshot(
        route="NXT",
        order_no="ONE-SHARE-11",
        order_date="2026-08-11",
        expected_order_qty=1,
    )
    assert snapshot.source_ok is True
    assert snapshot.found is True
    assert snapshot.filled_qty == 0
    assert snapshot.remaining_qty == 1


def test_live_service_rejects_once_and_custom_state_paths(monkeypatch, tmp_path):
    monkeypatch.setenv(service_module.ENABLE_ENV, "true")
    live_args = ["--live", "--confirm", service_module.LIVE_CONFIRMATION]
    with pytest.raises(SystemExit, match="continuous custody"):
        service_module.main([*live_args, "--once"])
    with pytest.raises(SystemExit, match="custom state"):
        service_module.main([*live_args, "--state-path", str(tmp_path / "other.json")])


def test_live_service_fails_closed_without_daily_authority(monkeypatch):
    validation_calls = []
    monkeypatch.setenv(service_module.ENABLE_ENV, "true")
    monkeypatch.setattr(
        service_module,
        "validate_authority",
        lambda path, **kwargs: validation_calls.append((path, kwargs))
        or (False, "authority_target_date_mismatch"),
    )
    result = service_module.main(
        ["--live", "--confirm", service_module.LIVE_CONFIRMATION]
    )
    assert result == 4
    assert validation_calls == [
        (
            service_module.DEFAULT_AUTHORITY_PATH,
            {"require_live_main_bot_runtime": True},
        )
    ]


def test_live_service_fails_closed_without_exact_date_applied_policy(monkeypatch):
    monkeypatch.setenv(service_module.ENABLE_ENV, "true")
    monkeypatch.setattr(
        service_module, "validate_authority", lambda path, **kwargs: (True, "ready")
    )
    monkeypatch.setattr(
        service_module,
        "load_applied_machine_policy",
        lambda machine, target_date: (None, "", "applied_policy_unreadable"),
    )
    result = service_module.main(
        ["--live", "--confirm", service_module.LIVE_CONFIRMATION]
    )
    assert result == 5


def test_live_service_runs_reentry_only_after_first_episode_complete(monkeypatch):
    calls = []

    class FakeFirstMachine:
        def __init__(self, **kwargs):
            policy = kwargs["policy"]
            calls.append(
                (
                    "first_initialized",
                    policy.target_ticks,
                    policy.runtime_policy_source,
                    policy.runtime_policy_hash,
                )
            )

        def run_until_terminal(self, *, interval_sec):
            calls.append("first_complete")
            return {"status": "COMPLETE"}

    class FakeReentryMachine:
        def __init__(self, **kwargs):
            policy = kwargs["policy"]
            calls.append(
                (
                    "reentry_initialized",
                    policy.target_ticks,
                    policy.runtime_policy_source,
                    policy.runtime_policy_hash,
                )
            )

        def run_until_terminal(self, *, interval_sec):
            calls.append("reentry_terminal")
            return {"status": "NO_TRADE"}

    monkeypatch.setenv(service_module.ENABLE_ENV, "true")
    monkeypatch.setattr(
        service_module, "validate_authority", lambda path, **kwargs: (True, "ready")
    )
    monkeypatch.setattr(
        service_module,
        "runtime_ledgers_allow_service_start",
        lambda **kwargs: (True, "clear"),
    )
    monkeypatch.setattr(
        service_module,
        "load_applied_machine_policy",
        lambda machine, target_date: (
            {
                "nxt_drawdown_pct": 3.0,
                "sor_drawdown_pct": 0.75,
                "target_ticks": 3,
            },
            "policy-hash",
            "ready_operator_override",
        ),
    )
    monkeypatch.setattr(service_module, "_acquire_lock", lambda path: object())
    monkeypatch.setattr(
        service_module, "KiwoomOneShareGateway", lambda **kwargs: object()
    )
    monkeypatch.setattr(
        service_module, "SamsungMorningOneShareMachine", FakeFirstMachine
    )
    monkeypatch.setattr(
        service_module, "SamsungMorningSORReentryMachine", FakeReentryMachine
    )

    result = service_module.main(
        ["--live", "--confirm", service_module.LIVE_CONFIRMATION]
    )

    assert result == 0
    assert calls == [
        (
            "first_initialized",
            3,
            service_module.OPERATOR_OVERRIDE_RUNTIME_SOURCE,
            "policy-hash",
        ),
        "first_complete",
        (
            "reentry_initialized",
            3,
            service_module.OPERATOR_OVERRIDE_RUNTIME_SOURCE,
            "policy-hash",
        ),
        "reentry_terminal",
    ]


def test_systemd_live_unit_uses_exact_two_leg_confirmation():
    project_root = Path(__file__).resolve().parents[2]
    preflight_unit = (
        project_root / "deploy/systemd/korstockscan-samsung-one-share-preflight.service"
    ).read_text(encoding="utf-8")
    live_unit = (
        project_root / "deploy/systemd/korstockscan-samsung-morning-one-share.service"
    ).read_text(encoding="utf-8")
    live_timer = (
        project_root / "deploy/systemd/korstockscan-samsung-morning-one-share.timer"
    ).read_text(encoding="utf-8")
    installer = (
        project_root / "deploy/install_samsung_morning_one_share_systemd.sh"
    ).read_text(encoding="utf-8")
    preflight_script = (
        project_root / "deploy/run_samsung_morning_one_share_preflight.sh"
    ).read_text(encoding="utf-8")
    assert "PrivateTmp=true" not in preflight_unit
    assert "TimeoutStartSec=5400" in preflight_unit
    assert "User=ubuntu" in preflight_unit
    assert "Group=ubuntu" in preflight_unit
    assert "PrivateTmp=true" in live_unit
    assert "User=ubuntu\n" in live_unit
    assert "Group=ubuntu" in live_unit
    assert "Group=www-data" not in preflight_unit
    assert "Group=www-data" not in live_unit
    assert "Requires=korstockscan-samsung-one-share-preflight.service" in live_unit
    assert "RestartPreventExitStatus=4 5 6" in live_unit
    assert service_module.LIVE_CONFIRMATION in live_unit
    assert "OnCalendar=Mon..Fri *-*-* 07:57:00 Asia/Seoul" in live_timer
    assert not (
        project_root / "deploy/systemd/korstockscan-samsung-one-share-preflight.timer"
    ).exists()
    assert (
        'LEGACY_PREFLIGHT_TIMER="korstockscan-samsung-one-share-preflight.timer"'
        in installer
    )
    assert (
        "/bin/systemctl enable --now korstockscan-samsung-morning-one-share.timer"
        in installer
    )
    assert 'installed_group="$(/bin/systemctl show' in installer
    assert 'installed_group" != "ubuntu"' in installer
    assert installer.index('installed_group="$(/bin/systemctl show') < installer.index(
        "/bin/systemctl enable --now korstockscan-samsung-morning-one-share.timer"
    )
    assert "PREFLIGHT_DEADLINE_HHMMSS" in preflight_script
    assert "compact_verify_detail" in preflight_script
    assert "pid_env_read_error" in preflight_script
    assert "detail=$verify_output" not in preflight_script
    assert '--pid "$bot_pid"' in preflight_script
    assert "--write-verify-artifact" in preflight_script
    assert '--main-bot-pid "$bot_pid"' in preflight_script
    assert '--authority-deadline-hhmmss "$PREFLIGHT_DEADLINE_HHMMSS"' in (
        preflight_script
    )
    initial_deadline_guard = preflight_script.index("if deadline_elapsed; then")
    policy_apply = preflight_script.index("samsung_machine_entry_policy_apply")
    polling_verify = preflight_script.index('verify_output="$(')
    polling_verify_end = preflight_script.index(')"; then', polling_verify)
    verify_commit = preflight_script.index('verify_commit_output="$(')
    verify_artifact_write = preflight_script.index("--write-verify-artifact")
    assert initial_deadline_guard < policy_apply
    assert (
        "--write-verify-artifact"
        not in preflight_script[polling_verify:polling_verify_end]
    )
    assert polling_verify_end < verify_commit < verify_artifact_write
