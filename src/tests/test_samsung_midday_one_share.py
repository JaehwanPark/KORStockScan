from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from src.trading.order.entry_liquidity_guard import (
    EntryExecutionVelocitySnapshot,
    EntryLiquiditySnapshot,
)

from src.trading.samsung_midday_one_share import gateway as gateway_module
from src.trading.samsung_midday_one_share.gateway import (
    ExecutionSnapshot,
    KiwoomMiddayOneShareGateway,
    MinuteBarsSnapshot,
    SubmitResult,
)
from src.trading.samsung_midday_one_share.machine import (
    KST,
    SamsungMiddayOneShareMachine,
)
from src.trading.samsung_midday_one_share.policy import DEFAULT_POLICY, MinuteBar
from src.trading.samsung_midday_one_share import service as service_module
from src.trading.samsung_morning_one_share.machine import (
    DEFAULT_STATE_PATH as MORNING_STATE_PATH,
)
from src.trading.samsung_afternoon_one_share.machine import (
    DEFAULT_STATE_PATH as AFTERNOON_STATE_PATH,
)


def _at(day: int, hour: int, minute: int = 0, second: int = 10) -> datetime:
    return datetime(2026, 8, day, hour, minute, second, tzinfo=KST)


def _scan_at(day: int, minute_offset: int = 0, second: int = 10) -> datetime:
    return _at(day, 13, 15, 0) + timedelta(minutes=minute_offset, seconds=second)


def _signal_bars(day: int = 12, *, through: int = 0) -> tuple[MinuteBar, ...]:
    signal_at = _scan_at(day, second=0)
    start = signal_at - timedelta(minutes=29)
    bars = [
        MinuteBar(start + timedelta(minutes=index), 100_000, 100_000, 99_000, 100_000)
        for index in range(29)
    ]
    bars.append(MinuteBar(signal_at, 99_000, 99_000, 98_000, 98_100))
    for minute in range(1, through + 1):
        bars.append(
            MinuteBar(
                signal_at + timedelta(minutes=minute),
                98_100,
                98_200,
                98_000,
                98_100,
            )
        )
    return tuple(bars)


class FakeGateway:
    def __init__(self) -> None:
        self.bars = _signal_bars()
        self.buy_calls: list[int] = []
        self.sell_calls: list[int] = []
        self.sell_quantities: list[int] = []
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
            observed_at_kst="2026-08-12T13:15:10+09:00",
            print_times=("131510",) * 10,
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
        self.sell_quantities.append(quantity)
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
    return SamsungMiddayOneShareMachine(
        gateway=gateway,
        state_path=tmp_path / "midday.json",
        live_enabled=live,
        ownership_source=lambda code: "manual_operator",
    )


def test_policy_uses_fixed_sor_research_thresholds_and_two_leg_allocation():
    signal = DEFAULT_POLICY.evaluate(list(_signal_bars()))
    assert DEFAULT_POLICY.symbol == "005930"
    assert DEFAULT_POLICY.route == "SOR"
    assert DEFAULT_POLICY.quantity == 20
    assert DEFAULT_POLICY.scan_start.isoformat() == "13:15:00"
    assert DEFAULT_POLICY.scan_last_bar.isoformat() == "13:54:00"
    assert DEFAULT_POLICY.entry_valid_completed_bars == 5
    assert signal is not None
    assert signal.entry_price == 98_000
    assert DEFAULT_POLICY.entry_legs(signal.signal_bar.close_price) == [
        {
            "leg_id": "signal_close",
            "price_role": "aggressive_50pct",
            "entry_price": 98_100,
        },
        {
            "leg_id": "signal_close_minus_1tick",
            "price_role": "conservative_50pct",
            "entry_price": 98_000,
        },
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


def test_policy_matches_half_open_1315_1355_research_window():
    bars = list(_signal_bars())
    through_1354 = [
        MinuteBar(
            bar.timestamp + timedelta(minutes=39),
            bar.open_price,
            bar.high_price,
            bar.low_price,
            bar.close_price,
        )
        for bar in bars
    ]
    through_1355 = [
        MinuteBar(
            bar.timestamp + timedelta(minutes=40),
            bar.open_price,
            bar.high_price,
            bar.low_price,
            bar.close_price,
        )
        for bar in bars
    ]
    assert DEFAULT_POLICY.evaluate(through_1354) is not None
    assert DEFAULT_POLICY.evaluate(through_1355) is None


def test_latest_completed_signal_submits_two_independent_sor_buys_once(tmp_path):
    gateway = FakeGateway()
    machine = _machine(tmp_path, gateway)
    state = machine.run_once(_scan_at(12, 1))
    assert state["status"] == "BUY_OPEN"
    assert state["attempt_consumed"] is True
    assert gateway.buy_calls == [98_100, 98_000]
    assert [leg["quantity"] for leg in state["legs"]] == [10, 10]
    machine.run_once(_scan_at(12, 2))
    assert gateway.buy_calls == [98_100, 98_000]


def test_buy_expires_only_after_five_completed_bars_and_exact_order_is_cancelled(
    tmp_path,
):
    gateway = FakeGateway()
    machine = _machine(tmp_path, gateway)
    machine.run_once(_scan_at(12, 1))
    gateway.bars = _signal_bars(through=4)
    waiting = machine.run_once(_scan_at(12, 5))
    assert waiting["status"] == "BUY_OPEN"
    assert gateway.cancel_calls == []
    gateway.bars = _signal_bars(through=5)
    pending = machine.run_once(_scan_at(12, 6))
    assert pending["status"] == "BUY_CANCEL_PENDING"
    assert gateway.cancel_calls == ["B1", "B2"]


def test_each_fill_submits_own_two_tick_target_and_completes(tmp_path):
    gateway = FakeGateway()
    machine = _machine(tmp_path, gateway)
    machine.run_once(_scan_at(12, 1))
    gateway.snapshots["B1"] = ExecutionSnapshot(True, True, 1, 0, 1, 98_100)
    gateway.snapshots["B2"] = ExecutionSnapshot(True, True, 1, 0, 1, 98_000)
    filled = machine.run_once(_scan_at(12, 2))
    assert filled["position_qty"] == 20
    assert filled["status"] == "TARGET_OPEN"
    assert gateway.sell_calls == [98_300, 98_200]
    gateway.snapshots["T3"] = ExecutionSnapshot(True, True, 1, 0, 1, 98_300)
    gateway.snapshots["T4"] = ExecutionSnapshot(True, True, 1, 0, 1, 98_200)
    complete = machine.run_once(_scan_at(12, 3))
    assert complete["status"] == "COMPLETE"
    assert complete["position_qty"] == 0
    assert [leg["target_fill_price"] for leg in complete["legs"]] == [98_300, 98_200]
    assert all(leg["target_filled_at"] for leg in complete["legs"])


def test_partial_buy_cancels_remainder_then_sells_only_confirmed_quantity(tmp_path):
    gateway = FakeGateway()
    machine = _machine(tmp_path, gateway)
    machine.run_once(_scan_at(12, 1))
    gateway.snapshots["B1"] = ExecutionSnapshot(True, True, 3, 7, 10, 98_100)

    cancel_pending = machine.run_once(_scan_at(12, 2))

    signal_leg = next(
        leg for leg in cancel_pending["legs"] if leg["leg_id"] == "signal_close"
    )
    assert signal_leg["status"] == "BUY_CANCEL_PENDING"
    assert cancel_pending["position_qty"] == 3
    assert gateway.cancel_calls == ["B1"]
    assert gateway.sell_calls == []

    gateway.snapshots["B1"] = ExecutionSnapshot(True, True, 4, 0, 10, 98_100)
    target_open = machine.run_once(_scan_at(12, 3))

    assert target_open["position_qty"] == 4
    assert gateway.sell_quantities == [4]
    target_order = next(
        leg["target_order_no"]
        for leg in target_open["legs"]
        if leg["leg_id"] == "signal_close"
    )
    gateway.snapshots[target_order] = ExecutionSnapshot(True, True, 2, 2, 4, 98_300)
    partially_sold = machine.run_once(_scan_at(12, 4))

    signal_leg = next(
        leg for leg in partially_sold["legs"] if leg["leg_id"] == "signal_close"
    )
    assert signal_leg["status"] == "TARGET_OPEN"
    assert signal_leg["position_qty"] == 2
    assert signal_leg["target_filled_qty"] == 2
    assert signal_leg["target_fill_price"] == 98_300


def test_one_filled_leg_keeps_target_while_other_leg_expires(tmp_path):
    gateway = FakeGateway()
    machine = _machine(tmp_path, gateway)
    machine.run_once(_scan_at(12, 1))
    gateway.snapshots["B1"] = ExecutionSnapshot(True, True, 1, 0, 1, 98_100)
    partial = machine.run_once(_scan_at(12, 2))
    assert partial["position_qty"] == 10
    assert partial["status"] == "BUY_OPEN"
    assert gateway.sell_calls == [98_300]

    gateway.bars = _signal_bars(through=5)
    pending = machine.run_once(_scan_at(12, 6))
    assert pending["status"] == "BUY_CANCEL_PENDING"
    assert gateway.cancel_calls == ["B2"]
    gateway.snapshots["B2"] = ExecutionSnapshot(True, True, 0, 0, 1)
    target_only = machine.run_once(_scan_at(12, 7))
    assert target_only["status"] == "TARGET_OPEN"
    assert target_only["position_qty"] == 10


def test_target_has_no_timeout_cancel_and_reconciles_original_order_across_date(
    tmp_path,
):
    gateway = FakeGateway()
    machine = _machine(tmp_path, gateway)
    machine.run_once(_scan_at(12, 1))
    gateway.snapshots["B1"] = ExecutionSnapshot(True, True, 1, 0, 1, 98_100)
    gateway.snapshots["B2"] = ExecutionSnapshot(True, True, 0, 0, 1)
    machine.run_once(_scan_at(12, 2))
    carried = machine.run_once(_at(13, 9, 0))
    assert carried["status"] == "TARGET_OPEN"
    assert carried["position_qty"] == 10
    assert gateway.cancel_calls == []
    assert gateway.buy_calls == [98_100, 98_000]


def test_target_closed_unfilled_becomes_held_without_forced_sell(tmp_path):
    gateway = FakeGateway()
    machine = _machine(tmp_path, gateway)
    machine.run_once(_scan_at(12, 1))
    gateway.snapshots["B1"] = ExecutionSnapshot(True, True, 1, 0, 1, 98_100)
    gateway.snapshots["B2"] = ExecutionSnapshot(True, True, 0, 0, 1)
    machine.run_once(_scan_at(12, 2))
    gateway.snapshots["T3"] = ExecutionSnapshot(True, True, 0, 0, 1)
    held = machine.run_once(_at(12, 15, 20))
    assert held["status"] == "HELD"
    assert held["position_qty"] == 10
    assert gateway.cancel_calls == []
    assert gateway.sell_calls == [98_300]


def test_foreign_order_number_cannot_enter_midday_ledger(tmp_path):
    gateway = FakeGateway()
    state_path = tmp_path / "midday.json"
    machine = _machine(tmp_path, gateway)
    machine.run_once(_scan_at(12, 1))
    payload = machine.snapshot()
    payload["legs"][0]["buy_order_no"] = "MORNING-OR-WIDGET-77"
    state_path.write_text(json.dumps(payload), encoding="utf-8")
    restarted = _machine(tmp_path, gateway)
    blocked = restarted.run_once(_scan_at(12, 2))
    assert blocked["status"] == "BLOCKED"
    assert blocked["blocked_reason"] == "state_buy_order_no_ownership_invalid"
    assert gateway.cancel_calls == []


def test_cross_leg_order_number_collision_fails_closed(tmp_path):
    gateway = FakeGateway()
    state_path = tmp_path / "midday.json"
    machine = _machine(tmp_path, gateway)
    machine.run_once(_scan_at(12, 1))
    payload = machine.snapshot()
    payload["legs"][1]["buy_order_no"] = payload["legs"][0]["buy_order_no"]
    state_path.write_text(json.dumps(payload), encoding="utf-8")
    blocked = _machine(tmp_path, gateway).run_once(_scan_at(12, 2))
    assert blocked["status"] == "BLOCKED"
    assert blocked["blocked_reason"] == "state_leg_order_identity_collision"


def test_state_position_status_invariant_fails_closed(tmp_path):
    gateway = FakeGateway()
    state_path = tmp_path / "midday.json"
    machine = _machine(tmp_path, gateway)
    machine.run_once(_scan_at(12, 1))
    payload = machine.snapshot()
    payload.update({"status": "COMPLETE"})
    state_path.write_text(json.dumps(payload), encoding="utf-8")
    blocked = _machine(tmp_path, gateway).run_once(_scan_at(12, 2))
    assert blocked["status"] == "BLOCKED"
    assert blocked["blocked_reason"] == "state_aggregate_status_mismatch"


def test_mixed_legacy_and_current_leg_quantities_fail_closed(tmp_path):
    gateway = FakeGateway()
    state_path = tmp_path / "midday.json"
    machine = _machine(tmp_path, gateway)
    machine.run_once(_scan_at(12, 1))
    payload = machine.snapshot()
    payload["legs"][1]["quantity"] = 1
    state_path.write_text(json.dumps(payload), encoding="utf-8")

    blocked = _machine(tmp_path, gateway).run_once(_scan_at(12, 2))

    assert blocked["status"] == "BLOCKED"
    assert blocked["blocked_reason"] == "state_mixed_leg_quantities_invalid"


def test_invalid_previous_day_quantity_fails_closed_before_date_rollover(tmp_path):
    gateway = FakeGateway()
    state_path = tmp_path / "midday.json"
    machine = _machine(tmp_path, gateway)
    machine.run_once(_scan_at(12, -1))
    payload = machine.snapshot()
    payload["position_qty"] = "not-an-integer"
    state_path.write_text(json.dumps(payload), encoding="utf-8")
    blocked = _machine(tmp_path, gateway).run_once(_scan_at(13, -1))
    assert blocked["status"] == "BLOCKED"
    assert blocked["blocked_reason"] == "state_date_or_quantity_invalid"


def test_malformed_legacy_quantity_fails_closed_on_load(tmp_path):
    state_path = tmp_path / "midday.json"
    state_path.write_text(
        json.dumps(
            {
                "schema": "samsung_midday_one_share_state_v1",
                "trade_date": "2026-08-12",
                "status": "COMPLETE",
                "position_qty": "invalid",
            }
        ),
        encoding="utf-8",
    )
    blocked = _machine(tmp_path, FakeGateway()).run_once(_scan_at(12, 1))
    assert blocked["status"] == "BLOCKED"
    assert blocked["blocked_reason"] == "legacy_position_quantity_invalid"


def test_terminal_legacy_state_migrates_but_active_legacy_state_blocks(tmp_path):
    state_path = tmp_path / "midday.json"
    terminal = {
        "schema": "samsung_midday_one_share_state_v1",
        "trade_date": "2026-08-12",
        "status": "COMPLETE",
        "position_qty": 0,
        "attempt_consumed": True,
    }
    state_path.write_text(json.dumps(terminal), encoding="utf-8")
    migrated = _machine(tmp_path, FakeGateway()).run_once(_scan_at(12, 1))
    assert migrated["schema"] == "samsung_midday_two_leg_state_v2"
    assert migrated["status"] == "COMPLETE"
    assert migrated["last_action"] == "legacy_terminal_state_migrated"

    active = {**terminal, "status": "BUY_OPEN"}
    state_path.write_text(json.dumps(active), encoding="utf-8")
    blocked = _machine(tmp_path, FakeGateway()).run_once(_scan_at(12, 1))
    assert blocked["status"] == "BLOCKED"
    assert (
        blocked["blocked_reason"]
        == "legacy_active_state_manual_reconciliation_required"
    )


def test_leg_position_status_mismatch_fails_closed(tmp_path):
    gateway = FakeGateway()
    state_path = tmp_path / "midday.json"
    machine = _machine(tmp_path, gateway)
    machine.run_once(_scan_at(12, 1))
    payload = machine.snapshot()
    payload["legs"][0]["position_qty"] = 1
    payload["legs"][0]["fill_price"] = 98_100
    payload["position_qty"] = 1
    state_path.write_text(json.dumps(payload), encoding="utf-8")
    blocked = _machine(tmp_path, gateway).run_once(_scan_at(12, 2))
    assert blocked["status"] == "BLOCKED"
    assert blocked["blocked_reason"] == "state_leg_fill_position_mismatch"


def test_dry_run_previews_but_never_writes_broker(tmp_path):
    gateway = FakeGateway()
    state = _machine(tmp_path, gateway, live=False).run_once(_scan_at(12, 1))
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
    machine = SamsungMiddayOneShareMachine(
        gateway=gateway,
        state_path=tmp_path / "midday.json",
        live_enabled=True,
        ownership_source=lambda code: "",
    )
    state = machine.run_once(_scan_at(12, 1))
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
        machine.run_once(_scan_at(12, 1))
    blocked = _machine(tmp_path, gateway).run_once(_scan_at(12, 2))
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
            "cntr_tm": "20260812131500",
            "open_pric": "100000",
            "high_pric": "100100",
            "low_pric": "99900",
            "cur_prc": "100000",
        },
        {
            "cntr_tm": "20260812131600",
            "open_pric": "100000",
            "high_pric": "100100",
            "low_pric": "99900",
            "cur_prc": "100000",
        },
    ]
    session = FakeSession(
        [FakeResponse({"return_code": 0, "stk_min_pole_chart_qry": rows})]
    )
    gateway = KiwoomMiddayOneShareGateway(
        request_session=session, token_loader=lambda: "TOKEN"
    )
    snapshot = gateway.completed_sor_minute_bars(
        trade_date=_scan_at(12, 1).date(), now=_scan_at(12, 1, 30)
    )
    assert snapshot.source_ok is True
    assert [bar.timestamp.minute for bar in snapshot.bars] == [15]
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
    gateway = KiwoomMiddayOneShareGateway(
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


def test_gateway_requires_explicit_authority_and_production_for_all_writes():
    disabled = KiwoomMiddayOneShareGateway(token_loader=lambda: "TOKEN")
    with pytest.raises(PermissionError, match="authority_disabled"):
        disabled.submit_limit_buy(price=98_000, quantity=10)
    demo = KiwoomMiddayOneShareGateway(
        token_loader=lambda: "TOKEN",
        order_authority=True,
        base_url="https://mockapi.kiwoom.com",
    )
    with pytest.raises(PermissionError, match="production_endpoint"):
        demo.submit_limit_sell(price=98_200, quantity=10)
    with pytest.raises(PermissionError, match="production_endpoint"):
        demo.cancel_buy(order_no="123")


def test_gateway_hardcodes_sor_one_share_sell_and_exact_buy_cancel():
    session = FakeSession(
        [
            FakeResponse({"return_code": 0, "ord_no": "S1"}),
            FakeResponse({"return_code": 0, "ord_no": "C1"}),
        ]
    )
    gateway = KiwoomMiddayOneShareGateway(
        request_session=session, token_loader=lambda: "TOKEN", order_authority=True
    )
    assert gateway.submit_limit_sell(price=98_200, quantity=10).accepted is True
    assert gateway.cancel_buy(order_no="B1").accepted is True
    _, sell_call = session.calls[0]
    assert sell_call["headers"]["api-id"] == "kt10001"
    assert sell_call["json"] == {
        "dmst_stex_tp": "SOR",
        "stk_cd": "005930",
        "ord_qty": "10",
        "ord_uv": "98200",
        "trde_tp": "0",
        "cond_uv": "",
    }
    _, cancel_call = session.calls[1]
    assert cancel_call["headers"]["api-id"] == "kt10003"
    assert cancel_call["json"] == {
        "dmst_stex_tp": "SOR",
        "orig_ord_no": "B1",
        "stk_cd": "005930",
        "cncl_qty": "0",
    }


def test_execution_snapshot_follows_continuation_and_matches_exact_owned_order():
    session = FakeSession(
        [
            FakeResponse(
                {
                    "return_code": 0,
                    "ord_cntr_dtl": [
                        {
                            "ord_no": "999",
                            "stk_cd": "A005930",
                            "ord_qty": "1",
                            "cntr_qty": "0",
                            "ord_remnq": "1",
                        }
                    ],
                },
                headers={"cont-yn": "Y", "next-key": "NEXT"},
            ),
            FakeResponse(
                {
                    "return_code": 0,
                    "ord_cntr_dtl": [
                        {
                            "ord_no": "000123",
                            "stk_cd": "A005930",
                            "ord_qty": "1",
                            "cntr_qty": "1",
                            "ord_remnq": "0",
                            "cntr_uv": "98000",
                        }
                    ],
                }
            ),
        ]
    )
    gateway = KiwoomMiddayOneShareGateway(
        request_session=session, token_loader=lambda: "TOKEN"
    )
    snapshot = gateway.execution_snapshot(
        order_no="123", order_date="2026-08-12", expected_order_qty=1
    )
    assert snapshot == ExecutionSnapshot(True, True, 1, 0, 1, 98_000)
    _, second_call = session.calls[1]
    assert second_call["headers"]["cont-yn"] == "Y"
    assert second_call["headers"]["next-key"] == "NEXT"
    assert second_call["headers"]["api-id"] == "kt00007"
    assert second_call["json"]["dmst_stex_tp"] == "SOR"


def test_execution_snapshot_rejects_quantity_outside_expected_episode_contract():
    session = FakeSession(
        [
            FakeResponse(
                {
                    "return_code": 0,
                    "ord_cntr_dtl": [
                        {
                            "ord_no": "123",
                            "stk_cd": "005930",
                            "ord_qty": "2",
                            "cntr_qty": "1",
                            "ord_remnq": "1",
                            "cntr_uv": "98000",
                        }
                    ],
                }
            )
        ]
    )
    gateway = KiwoomMiddayOneShareGateway(
        request_session=session, token_loader=lambda: "TOKEN"
    )
    snapshot = gateway.execution_snapshot(
        order_no="123", order_date="20260812", expected_order_qty=10
    )
    assert snapshot.source_ok is False
    assert snapshot.error == "invalid_episode_execution_contract"


def test_midday_state_and_gateway_surface_are_independent_from_other_machines():
    from src.trading.samsung_midday_one_share.machine import DEFAULT_STATE_PATH

    assert DEFAULT_STATE_PATH != MORNING_STATE_PATH
    assert DEFAULT_STATE_PATH != AFTERNOON_STATE_PATH
    assert "midday" in DEFAULT_STATE_PATH.name
    assert not hasattr(KiwoomMiddayOneShareGateway, "submit_best_sell")
    assert not hasattr(KiwoomMiddayOneShareGateway, "cancel_target")


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
        / "deploy/systemd/korstockscan-samsung-midday-one-share-preflight.service"
    ).read_text(encoding="utf-8")
    live_unit = (
        project_root / "deploy/systemd/korstockscan-samsung-midday-one-share.service"
    ).read_text(encoding="utf-8")
    assert "PrivateTmp=true" not in preflight_unit
    assert "PrivateTmp=true" in live_unit

    preflight_timer = (
        project_root
        / "deploy/systemd/korstockscan-samsung-midday-one-share-preflight.timer"
    ).read_text(encoding="utf-8")
    live_timer = (
        project_root / "deploy/systemd/korstockscan-samsung-midday-one-share.timer"
    ).read_text(encoding="utf-8")
    assert "13:12:00 Asia/Seoul" in preflight_timer
    assert "13:14:00 Asia/Seoul" in live_timer
    assert service_module.LIVE_CONFIRMATION in live_unit
