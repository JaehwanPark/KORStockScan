from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.engine.monitoring.samsung_widget_contract import KST
from src.trading.widget_auto_trade import engine
from src.trading.widget_auto_trade.engine import WidgetSignalAutoTrader, WidgetSpec
from src.trading.widget_auto_trade.gateway import ExecutionSnapshot, SubmitResult
from src.trading.widget_auto_trade import gateway as gateway_module
from src.trading.widget_auto_trade import service as service_module


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


@dataclass
class FakeRecorder:
    events: list

    def record(self, event, observed_at):
        self.events.append(event)


class FakeGateway:
    def __init__(self):
        self.buy_calls = []
        self.sell_calls = []
        self.cancel_calls = []
        self.snapshots = {}
        self.sequence = 0

    def _accepted(self, prefix):
        self.sequence += 1
        return SubmitResult(True, f"{prefix}{self.sequence}", "0", "OK")

    def submit_buy(self, *, code, qty, route):
        self.buy_calls.append((code, qty, route))
        return self._accepted("B")

    def submit_sell(self, *, code, qty, route):
        self.sell_calls.append((code, qty, route))
        return self._accepted("S")

    def cancel(self, *, code, order_no, qty, route):
        self.cancel_calls.append((code, order_no, qty, route))
        return self._accepted("C")

    def execution_snapshot(self, *, code, order_no, route, order_date):
        return self.snapshots.get(order_no, ExecutionSnapshot(True, False, 0, 0, 0))


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
        entry_qty=qty,
        enabled=True,
    )
    return trader, gateway, recorder


def _fill(gateway, order_no, qty=1, price=1000):
    gateway.snapshots[order_no] = ExecutionSnapshot(
        True, True, qty, 0, qty, fill_price=price
    )


def test_one_order_per_entry_episode_and_rearms_only_after_final_exit(
    tmp_path, monkeypatch
):
    now = _at(10)
    box = {"payload": _payload(now, entry_id="ENTRY-1")}
    trader, gateway, _ = _trader(tmp_path, monkeypatch, box)

    first = trader.run_once(now)
    assert gateway.buy_calls == [("999999", 1, "KRX")]
    assert first["symbols"]["999999"]["orders"][0]["broker_accepted"] is True

    trader.run_once(now)
    assert len(gateway.buy_calls) == 1
    _fill(gateway, "B1")
    trader.run_once(now)

    box["payload"] = _payload(now, exit_id="EXIT-1")
    trader.run_once(now)
    assert gateway.sell_calls == [("999999", 1, "KRX")]
    _fill(gateway, "S2")
    closed = trader.run_once(now)
    assert closed["symbols"]["999999"]["exit_requested"] is False
    assert closed["symbols"]["999999"]["entry_episode_open"] is False

    box["payload"] = _payload(now, entry_id="ENTRY-2", entry_state="ENTRY_READY")
    trader.run_once(now)
    assert len(gateway.buy_calls) == 2


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

    _fill(gateway, "B2")
    trader.run_once(day_two)
    box["payload"] = _payload(day_two, exit_id="DAY2-EXIT")
    trader.run_once(day_two)
    assert gateway.sell_calls == [("999999", 1, "KRX")]


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
    assert gateway.buy_calls == [("999999", 3, "KRX")]


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
    assert gateway.buy_calls == [("999999", 1, "KRX")]


def test_shared_token_gateway_blocks_buy_during_global_pause(monkeypatch):
    class FailIfCalledSession:
        def post(self, *args, **kwargs):
            raise AssertionError("broker API must not be called while paused")

    monkeypatch.setattr(gateway_module, "is_buy_side_paused", lambda: True)
    gateway = gateway_module.KiwoomSharedTokenOrderGateway(
        request_session=FailIfCalledSession(), token_loader=lambda: "cached-token"
    )

    result = gateway.submit_buy(code="005930", qty=1, route="KRX")

    assert result.accepted is False
    assert result.return_code == "TRADING_PAUSED"


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


def test_gateway_rejects_invalid_route_and_quantity_before_broker_call(monkeypatch):
    class FailIfCalledSession:
        def post(self, *args, **kwargs):
            raise AssertionError("invalid input must not reach broker")

    monkeypatch.setattr(gateway_module, "is_buy_side_paused", lambda: False)
    gateway = gateway_module.KiwoomSharedTokenOrderGateway(
        request_session=FailIfCalledSession(), token_loader=lambda: "cached-token"
    )

    with pytest.raises(ValueError, match="invalid_order_route"):
        gateway.submit_buy(code="005930", qty=1, route="SOR")
    with pytest.raises(ValueError, match="invalid_order_quantity"):
        gateway.submit_sell(code="005930", qty=0, route="KRX")


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


def test_systemd_service_is_static_and_daily_timer_is_single_start_owner():
    service = Path(
        "deploy/systemd/korstockscan-widget-signal-auto-trader.service"
    ).read_text(encoding="utf-8")
    timer = Path(
        "deploy/systemd/korstockscan-widget-signal-auto-trader.timer"
    ).read_text(encoding="utf-8")

    assert "WantedBy=multi-user.target" not in service
    assert "OnCalendar=Mon..Fri *-*-* 07:58:00 Asia/Seoul" in timer
    assert "Persistent=true" in timer
    assert "AccuracySec=1s" in timer
    assert "Unit=korstockscan-widget-signal-auto-trader.service" in timer
    assert "WantedBy=timers.target" in timer
