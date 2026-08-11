from __future__ import annotations

from datetime import datetime
from pathlib import Path
import pytest

from src.trading.samsung_morning_one_share import gateway as gateway_module
from src.trading.samsung_morning_one_share.gateway import (
    ExecutionSnapshot,
    KiwoomOneShareGateway,
    OpenPriceSnapshot,
    SubmitResult,
)
from src.trading.samsung_morning_one_share.machine import (
    KST,
    SamsungMorningOneShareMachine,
)
from src.trading.samsung_morning_one_share.policy import DEFAULT_POLICY
from src.trading.samsung_morning_one_share import service as service_module


class FakeGateway:
    def __init__(self) -> None:
        self.opens = {"NXT": 300_000, "SOR": 300_000}
        self.buy_calls: list[tuple[str, int]] = []
        self.limit_sell_calls: list[tuple[str, int]] = []
        self.cancel_calls: list[tuple[str, str]] = []
        self.snapshots: dict[str, ExecutionSnapshot] = {}
        self.sequence = 0

    def _accepted(self, prefix: str) -> SubmitResult:
        self.sequence += 1
        return SubmitResult(True, f"{prefix}{self.sequence}", "0", "OK")

    def opening_price(self, *, route, trade_date):
        price = self.opens.get(route)
        return OpenPriceSnapshot(bool(price), price, f"{trade_date:%Y%m%d}080000")

    def submit_limit_buy(self, *, route, price):
        self.buy_calls.append((route, price))
        return self._accepted("B")

    def submit_limit_sell(self, *, route, price):
        self.limit_sell_calls.append((route, price))
        return self._accepted("T")

    def cancel(self, *, route, order_no):
        self.cancel_calls.append((route, order_no))
        return self._accepted("C")

    def execution_snapshot(self, *, route, order_no, order_date):
        return self.snapshots.get(order_no, ExecutionSnapshot(True, True, 0, 1, 1))


def _at(day: int, hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 8, day, hour, minute, tzinfo=KST)


def _machine(tmp_path: Path, gateway: FakeGateway, *, live: bool = True):
    return SamsungMorningOneShareMachine(
        gateway=gateway,
        state_path=tmp_path / "state.json",
        live_enabled=live,
        ownership_source=lambda code: "manual_operator",
    )


def test_policy_prices_are_fixed_to_two_independent_one_share_legs():
    assert DEFAULT_POLICY.quantity == 2
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
    assert filled["position_qty"] == 2
    assert gateway.limit_sell_calls == [("NXT", 292_500), ("NXT", 292_000)]

    gateway.snapshots["T3"] = ExecutionSnapshot(True, True, 1, 0, 1, 292_500)
    gateway.snapshots["T4"] = ExecutionSnapshot(True, True, 1, 0, 1, 292_000)
    closed = machine.run_once(_at(11, 8, 3))
    assert closed["status"] == "COMPLETE"
    assert closed["position_qty"] == 0
    assert len(gateway.buy_calls) == 2


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


def test_late_start_arms_sor_fallback_without_attempting_nxt(tmp_path):
    gateway = FakeGateway()
    machine = _machine(tmp_path, gateway)
    waiting = machine.run_once(_at(11, 8, 30))
    assert waiting["status"] == "BUY_OPEN"
    assert {leg["route"] for leg in waiting["legs"]} == {"SOR"}
    assert {leg["status"] for leg in waiting["legs"]} == {"PLANNED"}
    assert gateway.buy_calls == []

    submitted = machine.run_once(_at(11, 9, 0))
    assert submitted["status"] == "BUY_OPEN"
    assert gateway.buy_calls == [("SOR", 298_000), ("SOR", 297_500)]
    assert submitted["signal_features"]["opening_price"] == 300_000
    assert [
        leg["entry_price"] for leg in submitted["signal_features"]["entry_legs"]
    ] == [298_000, 297_500]


def test_start_during_sor_window_uses_sor_open_directly(tmp_path):
    gateway = FakeGateway()
    state = _machine(tmp_path, gateway).run_once(_at(11, 9, 1))
    assert state["status"] == "BUY_OPEN"
    assert gateway.buy_calls == [("SOR", 298_000), ("SOR", 297_500)]


def test_filled_nxt_leg_keeps_target_while_only_unfilled_leg_falls_back(tmp_path):
    gateway = FakeGateway()
    machine = _machine(tmp_path, gateway)
    machine.run_once(_at(11, 8, 1))
    gateway.snapshots["B1"] = ExecutionSnapshot(True, True, 1, 0, 1, 291_500)
    partial = machine.run_once(_at(11, 8, 2))
    assert partial["position_qty"] == 1
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
    assert still_open["position_qty"] == 2
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
    assert held["position_qty"] == 2
    assert held["last_action"] == "target_closed_unfilled_position_held"
    assert gateway.cancel_calls == []
    assert gateway.buy_calls == [("NXT", 291_500), ("NXT", 291_000)]

    carried = machine.run_once(_at(12, 8, 1))
    assert carried["status"] == "HELD"
    assert carried["position_qty"] == 2
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
    assert carried["position_qty"] == 2
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
    assert state["preview"]["total_quantity"] == 2
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
        def submit_limit_buy(self, *, route, price):
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
    result = gateway.submit_limit_buy(route="NXT", price=291_000)
    assert result.accepted is True
    _, call = session.calls[0]
    assert call["headers"]["authorization"] == "Bearer SHARED_TOKEN"
    assert call["headers"]["api-id"] == "kt10000"
    assert call["json"] == {
        "dmst_stex_tp": "NXT",
        "stk_cd": "005930",
        "ord_qty": "1",
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
    result = gateway.submit_limit_buy(route="SOR", price=297_500)
    assert result.accepted is True
    assert session.calls[0][1]["json"]["dmst_stex_tp"] == "SOR"


def test_gateway_write_is_disabled_without_both_authority_and_production():
    disabled = KiwoomOneShareGateway(
        token_loader=lambda: "token", order_authority=False
    )
    with pytest.raises(PermissionError, match="authority_disabled"):
        disabled.submit_limit_buy(route="SOR", price=297_500)

    wrong_endpoint = KiwoomOneShareGateway(
        token_loader=lambda: "token",
        order_authority=True,
        base_url="https://example.test",
    )
    with pytest.raises(PermissionError, match="production_endpoint"):
        wrong_endpoint.submit_limit_buy(route="SOR", price=297_500)


def test_gateway_rejects_direct_krx_route_for_regular_session(monkeypatch):
    monkeypatch.setattr(gateway_module, "is_buy_side_paused", lambda: False)
    gateway = KiwoomOneShareGateway(
        request_session=FakeSession([]),
        token_loader=lambda: "token",
        order_authority=True,
        base_url="https://api.kiwoom.com",
    )
    with pytest.raises(ValueError, match="invalid_order_route"):
        gateway.submit_limit_buy(route="KRX", price=297_500)


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
        route="NXT", order_no="ONE-SHARE-11", order_date="2026-08-11"
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
    monkeypatch.setenv(service_module.ENABLE_ENV, "true")
    monkeypatch.setattr(
        service_module,
        "validate_authority",
        lambda path: (False, "authority_target_date_mismatch"),
    )
    result = service_module.main(
        ["--live", "--confirm", service_module.LIVE_CONFIRMATION]
    )
    assert result == 4


def test_live_service_fails_closed_without_exact_date_applied_policy(monkeypatch):
    monkeypatch.setenv(service_module.ENABLE_ENV, "true")
    monkeypatch.setattr(
        service_module, "validate_authority", lambda path: (True, "ready")
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


def test_systemd_live_unit_uses_exact_two_leg_confirmation():
    project_root = Path(__file__).resolve().parents[2]
    live_unit = (
        project_root / "deploy/systemd/korstockscan-samsung-morning-one-share.service"
    ).read_text(encoding="utf-8")
    assert service_module.LIVE_CONFIRMATION in live_unit
