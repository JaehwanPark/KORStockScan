from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from src.trading.order.entry_liquidity_guard import (
    EntryExecutionVelocitySnapshot,
    EntryLiquiditySnapshot,
)

from src.trading.samsung_afternoon_one_share import gateway as gateway_module
from src.trading.samsung_afternoon_one_share.gateway import (
    ExecutionSnapshot,
    KiwoomAfternoonOneShareGateway,
    MinuteBarsSnapshot,
    SubmitResult,
)
from src.trading.samsung_afternoon_one_share.machine import (
    KST,
    SamsungAfternoonOneShareMachine,
)
from src.trading.samsung_afternoon_one_share.policy import DEFAULT_POLICY, MinuteBar
from src.trading.samsung_afternoon_one_share import service as service_module
from src.trading.samsung_morning_one_share.machine import (
    DEFAULT_STATE_PATH as MORNING_STATE_PATH,
)


def _at(day: int, hour: int, minute: int = 0, second: int = 10) -> datetime:
    return datetime(2026, 8, day, hour, minute, second, tzinfo=KST)


def _signal_bars(day: int = 12, *, through: int = 0) -> tuple[MinuteBar, ...]:
    start = _at(day, 13, 31, 0)
    bars = [
        MinuteBar(start + timedelta(minutes=index), 100_000, 100_000, 99_000, 100_000)
        for index in range(29)
    ]
    bars.append(MinuteBar(_at(day, 14, 0, 0), 99_000, 99_000, 98_000, 98_100))
    for minute in range(1, through + 1):
        bars.append(MinuteBar(_at(day, 14, minute, 0), 98_100, 98_200, 98_000, 98_100))
    return tuple(bars)


class FakeGateway:
    def __init__(self) -> None:
        self.bars = _signal_bars()
        self.buy_calls: list[int] = []
        self.sell_calls: list[int] = []
        self.cancel_calls: list[str] = []
        self.snapshots: dict[str, ExecutionSnapshot] = {}
        self.sequence = 0

    def completed_sor_minute_bars(self, *, trade_date, now):
        return MinuteBarsSnapshot(True, self.bars)

    def entry_liquidity_snapshot(self, *, route="SOR"):
        return EntryLiquiditySnapshot(
            True,
            "005930",
            route,
            "005930_AL",
            best_bid=100_000,
            best_ask=100_100,
            best_bid_qty=1_000,
            best_ask_qty=1_000,
            age_ms=0,
            received_ts_ms=1,
        )

    def entry_execution_velocity_snapshot(self, *, route="SOR"):
        return EntryExecutionVelocitySnapshot(
            True,
            "005930",
            route,
            "005930_AL",
            print_count=10,
            recent_print_span_ms=1_000,
            latest_print_age_ms=0,
            recent_volume=1_000,
            observed_at_kst="2026-08-12T14:00:10+09:00",
            print_times=("140010",) * 10,
            venues=("KRX",) * 10,
        )

    def _accepted(self, prefix: str) -> SubmitResult:
        self.sequence += 1
        return SubmitResult(True, f"{prefix}{self.sequence}", "0", "OK")

    def submit_limit_buy(self, *, price, quantity):
        assert quantity in {1, 10}
        self.buy_calls.append(price)
        return self._accepted("B")

    def submit_limit_sell(self, *, price, quantity):
        assert 1 <= quantity <= 10
        self.sell_calls.append(price)
        return self._accepted("T")

    def cancel_buy(self, *, order_no):
        self.cancel_calls.append(order_no)
        return self._accepted("C")

    def execution_snapshot(self, *, order_no, order_date, expected_order_qty):
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


def _machine(tmp_path: Path, gateway: FakeGateway, *, live: bool = True):
    return SamsungAfternoonOneShareMachine(
        gateway=gateway,
        state_path=tmp_path / "afternoon.json",
        live_enabled=live,
        ownership_source=lambda code: "manual_operator",
    )


def test_policy_uses_fixed_sor_research_thresholds_and_two_leg_allocation():
    signal = DEFAULT_POLICY.evaluate(list(_signal_bars()))
    assert DEFAULT_POLICY.symbol == "005930"
    assert DEFAULT_POLICY.route == "SOR"
    assert DEFAULT_POLICY.quantity == 20
    assert DEFAULT_POLICY.entry_valid_completed_bars == 5
    assert signal is not None
    assert signal.entry_price == 98_000
    assert [leg["entry_price"] for leg in DEFAULT_POLICY.entry_legs(98_100)] == [
        98_100,
        98_000,
    ]
    assert signal.drawdown_pct == pytest.approx(1.9)
    assert signal.near_low_pct == pytest.approx(100 / 98_000 * 100)
    assert DEFAULT_POLICY.target_price(98_000) == 98_200


def test_policy_rejects_nonconsecutive_lookback_bars():
    bars = list(_signal_bars())
    bars[-2] = MinuteBar(
        bars[-2].timestamp - timedelta(minutes=1),
        bars[-2].open_price,
        bars[-2].high_price,
        bars[-2].low_price,
        bars[-2].close_price,
    )
    assert DEFAULT_POLICY.evaluate(bars) is None


def test_latest_completed_signal_submits_two_independent_sor_buys_once(tmp_path):
    gateway = FakeGateway()
    machine = _machine(tmp_path, gateway)
    state = machine.run_once(_at(12, 14, 1))
    assert state["status"] == "BUY_OPEN"
    assert state["attempt_consumed"] is True
    assert gateway.buy_calls == [98_100, 98_000]
    assert [leg["quantity"] for leg in state["legs"]] == [10, 10]
    machine.run_once(_at(12, 14, 2))
    assert gateway.buy_calls == [98_100, 98_000]


def test_buy_expires_only_after_five_completed_bars_and_exact_order_is_cancelled(
    tmp_path,
):
    gateway = FakeGateway()
    machine = _machine(tmp_path, gateway)
    machine.run_once(_at(12, 14, 1))
    gateway.bars = _signal_bars(through=4)
    waiting = machine.run_once(_at(12, 14, 5))
    assert waiting["status"] == "BUY_OPEN"
    assert gateway.cancel_calls == []
    gateway.bars = _signal_bars(through=5)
    pending = machine.run_once(_at(12, 14, 6))
    assert pending["status"] == "BUY_CANCEL_PENDING"
    assert gateway.cancel_calls == ["B1", "B2"]


def test_each_fill_submits_own_two_tick_target_and_completes(tmp_path):
    gateway = FakeGateway()
    machine = _machine(tmp_path, gateway)
    machine.run_once(_at(12, 14, 1))
    gateway.snapshots["B1"] = ExecutionSnapshot(True, True, 1, 0, 1, 98_100)
    gateway.snapshots["B2"] = ExecutionSnapshot(True, True, 1, 0, 1, 98_000)
    filled = machine.run_once(_at(12, 14, 2))
    assert filled["position_qty"] == 20
    assert filled["status"] == "TARGET_OPEN"
    assert gateway.sell_calls == [98_300, 98_200]
    gateway.snapshots["T3"] = ExecutionSnapshot(True, True, 1, 0, 1, 98_300)
    gateway.snapshots["T4"] = ExecutionSnapshot(True, True, 1, 0, 1, 98_200)
    complete = machine.run_once(_at(12, 14, 3))
    assert complete["status"] == "COMPLETE"
    assert complete["position_qty"] == 0


def test_target_has_no_timeout_cancel_and_reconciles_original_order_across_date(
    tmp_path,
):
    gateway = FakeGateway()
    machine = _machine(tmp_path, gateway)
    machine.run_once(_at(12, 14, 1))
    gateway.snapshots["B1"] = ExecutionSnapshot(True, True, 1, 0, 1, 98_100)
    gateway.snapshots["B2"] = ExecutionSnapshot(True, True, 0, 0, 1)
    machine.run_once(_at(12, 14, 2))
    carried = machine.run_once(_at(13, 9, 0))
    assert carried["status"] == "TARGET_OPEN"
    assert carried["position_qty"] == 10
    assert gateway.cancel_calls == []
    assert gateway.buy_calls == [98_100, 98_000]


def test_target_closed_unfilled_becomes_held_without_forced_sell(tmp_path):
    gateway = FakeGateway()
    machine = _machine(tmp_path, gateway)
    machine.run_once(_at(12, 14, 1))
    gateway.snapshots["B1"] = ExecutionSnapshot(True, True, 1, 0, 1, 98_100)
    gateway.snapshots["B2"] = ExecutionSnapshot(True, True, 0, 0, 1)
    machine.run_once(_at(12, 14, 2))
    gateway.snapshots["T3"] = ExecutionSnapshot(True, True, 0, 0, 1)
    held = machine.run_once(_at(12, 15, 20))
    assert held["status"] == "HELD"
    assert held["position_qty"] == 10
    assert gateway.cancel_calls == []
    assert gateway.sell_calls == [98_300]


def test_foreign_order_number_cannot_enter_afternoon_ledger(tmp_path):
    gateway = FakeGateway()
    state_path = tmp_path / "afternoon.json"
    machine = _machine(tmp_path, gateway)
    machine.run_once(_at(12, 14, 1))
    payload = machine.snapshot()
    payload["legs"][0]["buy_order_no"] = "MORNING-OR-WIDGET-77"
    state_path.write_text(json.dumps(payload), encoding="utf-8")
    restarted = _machine(tmp_path, gateway)
    blocked = restarted.run_once(_at(12, 14, 2))
    assert blocked["status"] == "BLOCKED"
    assert blocked["blocked_reason"] == "state_buy_order_no_ownership_invalid"
    assert gateway.cancel_calls == []


def test_state_position_status_invariant_fails_closed(tmp_path):
    gateway = FakeGateway()
    state_path = tmp_path / "afternoon.json"
    machine = _machine(tmp_path, gateway)
    machine.run_once(_at(12, 14, 1))
    payload = machine.snapshot()
    payload.update({"status": "COMPLETE"})
    state_path.write_text(json.dumps(payload), encoding="utf-8")
    blocked = _machine(tmp_path, gateway).run_once(_at(12, 14, 2))
    assert blocked["status"] == "BLOCKED"
    assert blocked["blocked_reason"] == "state_aggregate_status_mismatch"


def test_invalid_previous_day_quantity_fails_closed_before_date_rollover(tmp_path):
    gateway = FakeGateway()
    state_path = tmp_path / "afternoon.json"
    machine = _machine(tmp_path, gateway)
    machine.run_once(_at(12, 13, 59))
    payload = machine.snapshot()
    payload["position_qty"] = "not-an-integer"
    state_path.write_text(json.dumps(payload), encoding="utf-8")
    blocked = _machine(tmp_path, gateway).run_once(_at(13, 13, 59))
    assert blocked["status"] == "BLOCKED"
    assert blocked["blocked_reason"] == "state_date_or_quantity_invalid"


def test_dry_run_previews_but_never_writes_broker(tmp_path):
    gateway = FakeGateway()
    state = _machine(tmp_path, gateway, live=False).run_once(_at(12, 14, 1))
    assert state["last_action"] == "would_submit_sor_two_leg_buy"
    assert state["preview"]["total_quantity"] == 20
    assert [leg["entry_price"] for leg in state["preview"]["legs"]] == [
        98_100,
        98_000,
    ]
    assert state["preview"]["strategy_relationship"] == "parallel_independent_strategy"
    assert gateway.buy_calls == []


def test_no_operator_exclusion_blocks_live_buy(tmp_path):
    gateway = FakeGateway()
    machine = SamsungAfternoonOneShareMachine(
        gateway=gateway,
        state_path=tmp_path / "afternoon.json",
        live_enabled=True,
        ownership_source=lambda code: "",
    )
    state = machine.run_once(_at(12, 14, 1))
    assert state["blocked_reason"] == "005930_not_excluded_from_primary_bot"
    assert gateway.buy_calls == []


def test_interrupted_submit_intent_fails_closed_without_duplicate(tmp_path):
    class TimeoutGateway(FakeGateway):
        def submit_limit_buy(self, *, price, quantity):
            self.buy_calls.append(price)
            raise TimeoutError("unknown broker result")

    gateway = TimeoutGateway()
    machine = _machine(tmp_path, gateway)
    with pytest.raises(TimeoutError):
        machine.run_once(_at(12, 14, 1))
    blocked = _machine(tmp_path, gateway).run_once(_at(12, 14, 2))
    assert blocked["status"] == "BLOCKED"
    assert (
        blocked["blocked_reason"]
        == "broker_write_interrupted:signal_close:buy_submitting"
    )
    assert gateway.buy_calls == [98_100]


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


def test_gateway_requests_integrated_sor_completed_minute_bars_only():
    rows = [
        {
            "cntr_tm": "20260812140000",
            "open_pric": "100000",
            "high_pric": "100100",
            "low_pric": "99900",
            "cur_prc": "100000",
        },
        {
            "cntr_tm": "20260812140100",
            "open_pric": "100000",
            "high_pric": "100100",
            "low_pric": "99900",
            "cur_prc": "100000",
        },
    ]
    session = FakeSession(
        [FakeResponse({"return_code": 0, "stk_min_pole_chart_qry": rows})]
    )
    gateway = KiwoomAfternoonOneShareGateway(
        request_session=session, token_loader=lambda: "TOKEN"
    )
    snapshot = gateway.completed_sor_minute_bars(
        trade_date=_at(12, 14, 1).date(), now=_at(12, 14, 1, 30)
    )
    assert snapshot.source_ok is True
    assert [bar.timestamp.minute for bar in snapshot.bars] == [0]
    _, call = session.calls[0]
    assert call["headers"]["api-id"] == "ka10080"
    assert call["json"] == {
        "stk_cd": "005930_AL",
        "tic_scope": "1",
        "upd_stkpc_tp": "1",
    }


def test_gateway_hardcodes_sor_one_share_and_global_buy_pause(monkeypatch):
    monkeypatch.setattr(gateway_module, "is_buy_side_paused", lambda: False)
    session = FakeSession([FakeResponse({"return_code": 0, "ord_no": "123"})])
    gateway = KiwoomAfternoonOneShareGateway(
        request_session=session, token_loader=lambda: "TOKEN", order_authority=True
    )
    result = gateway.submit_limit_buy(price=98_000, quantity=10)
    assert result.accepted is True
    _, call = session.calls[0]
    assert call["json"]["dmst_stex_tp"] == "SOR"
    assert call["json"]["stk_cd"] == "005930"
    assert call["json"]["ord_qty"] == "10"
    monkeypatch.setattr(gateway_module, "is_buy_side_paused", lambda: True)
    assert (
        gateway.submit_limit_buy(price=98_000, quantity=10).return_code
        == "TRADING_PAUSED"
    )
    assert len(session.calls) == 1


def test_afternoon_state_and_gateway_surface_are_independent_from_morning_and_widget():
    from src.trading.samsung_afternoon_one_share.machine import DEFAULT_STATE_PATH

    assert DEFAULT_STATE_PATH != MORNING_STATE_PATH
    assert "afternoon" in DEFAULT_STATE_PATH.name
    assert not hasattr(KiwoomAfternoonOneShareGateway, "submit_best_sell")
    assert not hasattr(KiwoomAfternoonOneShareGateway, "cancel_target")


def test_service_live_requires_continuous_custody_and_exact_confirmation(monkeypatch):
    monkeypatch.delenv(service_module.ENABLE_ENV, raising=False)
    with pytest.raises(SystemExit, match="live authority requires"):
        service_module.main(["--live"])
    monkeypatch.setenv(service_module.ENABLE_ENV, "true")
    with pytest.raises(SystemExit, match="continuous custody"):
        service_module.main(
            ["--live", "--confirm", service_module.LIVE_CONFIRMATION, "--once"]
        )


def test_service_live_fails_closed_without_same_day_authority(monkeypatch):
    monkeypatch.setenv(service_module.ENABLE_ENV, "true")
    monkeypatch.setattr(
        service_module, "validate_authority", lambda path: (False, "missing")
    )
    assert (
        service_module.main(["--live", "--confirm", service_module.LIVE_CONFIRMATION])
        == 4
    )


def test_service_live_fails_closed_without_exact_date_applied_policy(monkeypatch):
    monkeypatch.setenv(service_module.ENABLE_ENV, "true")
    monkeypatch.setattr(
        service_module, "validate_authority", lambda path: (True, "ready")
    )
    monkeypatch.setattr(
        service_module,
        "load_applied_machine_policy",
        lambda machine, target_date: (None, "", "applied_policy_unreadable"),
    )
    assert (
        service_module.main(["--live", "--confirm", service_module.LIVE_CONFIRMATION])
        == 5
    )


def test_preflight_systemd_can_observe_existing_tmux_socket():
    project_root = Path(__file__).resolve().parents[2]
    preflight_unit = (
        project_root
        / "deploy/systemd/korstockscan-samsung-afternoon-one-share-preflight.service"
    ).read_text(encoding="utf-8")
    live_unit = (
        project_root / "deploy/systemd/korstockscan-samsung-afternoon-one-share.service"
    ).read_text(encoding="utf-8")
    assert "PrivateTmp=true" not in preflight_unit
    assert "PrivateTmp=true" in live_unit
    assert service_module.LIVE_CONFIRMATION in live_unit
