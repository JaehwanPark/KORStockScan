import json
from datetime import datetime

import pytest

from src.trading.samsung_morning_one_share import gateway as gateway_module
from src.trading.samsung_morning_one_share.gateway import (
    ExecutionSnapshot,
    KiwoomOneShareGateway,
    SubmitResult,
)
from src.trading.samsung_morning_one_share import manual_addon as addon_module
from src.trading.samsung_morning_one_share.manual_addon import (
    KST,
    SamsungMorningManualAddon,
)


def _at(hour, minute, second=0):
    return datetime(2026, 8, 13, hour, minute, second, tzinfo=KST)


def _source(path, *, route, status="BUY_OPEN", prices=(291_500, 291_000)):
    payload = {
        "schema": "samsung_morning_two_leg_state_v2",
        "trade_date": "2026-08-13",
        "status": status,
        "owned_order_nos": [
            f"NORMAL-{route}-1",
            f"NORMAL-{route}-2",
        ],
        "legs": [
            {
                "leg_id": "base_plus_1tick",
                "route": route,
                "status": "BUY_OPEN",
                "entry_price": prices[0],
                "buy_order_no": f"NORMAL-{route}-1",
            },
            {
                "leg_id": "base",
                "route": route,
                "status": "BUY_OPEN",
                "entry_price": prices[1],
                "buy_order_no": f"NORMAL-{route}-2",
            },
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


class FakeGateway:
    def __init__(self):
        self.buy_calls = []
        self.cancel_calls = []
        self.snapshots = {}
        self.seq = 0

    def submit_manual_addon_limit_buy(self, *, route, price, quantity):
        self.seq += 1
        order_no = f"A{self.seq}"
        self.buy_calls.append((route, price, quantity, order_no))
        return SubmitResult(True, order_no=order_no, return_code="0")

    def cancel_manual_addon_remaining(self, *, route, order_no):
        self.seq += 1
        self.cancel_calls.append((route, order_no))
        return SubmitResult(True, order_no=f"C{self.seq}", return_code="0")

    def manual_addon_execution_snapshot(
        self, *, route, order_no, order_date, expected_order_qty
    ):
        return self.snapshots.get(
            order_no,
            ExecutionSnapshot(True, True, 0, expected_order_qty, expected_order_qty),
        )


def test_addon_mirrors_two_50_share_legs_and_hands_all_fills_to_operator(
    tmp_path, monkeypatch
):
    source = tmp_path / "source.json"
    monkeypatch.setattr(addon_module, "SOURCE_STATE_PATH", source)
    _source(source, route="NXT")
    gateway = FakeGateway()
    machine = SamsungMorningManualAddon(
        gateway=gateway, state_path=tmp_path / "addon.json"
    )

    machine.run_once(_at(8, 1))
    assert gateway.buy_calls == [
        ("NXT", 291_500, 50, "A1"),
        ("NXT", 291_000, 50, "A2"),
    ]

    gateway.snapshots["A1"] = ExecutionSnapshot(True, True, 20, 30, 50, 291_500)
    gateway.snapshots["A2"] = ExecutionSnapshot(True, True, 0, 50, 50)
    machine.run_once(_at(8, 10))
    assert gateway.cancel_calls == [("NXT", "A1"), ("NXT", "A2")]

    gateway.snapshots["A1"] = ExecutionSnapshot(True, True, 20, 0, 50, 291_500)
    gateway.snapshots["A2"] = ExecutionSnapshot(True, True, 0, 0, 50)
    _source(source, route="SOR", prices=(297_500, 297_000))
    machine.run_once(_at(9, 1))
    assert gateway.buy_calls[-2:] == [
        ("SOR", 297_500, 30, "A5"),
        ("SOR", 297_000, 50, "A6"),
    ]

    gateway.snapshots["A5"] = ExecutionSnapshot(True, True, 30, 0, 30, 297_500)
    gateway.snapshots["A6"] = ExecutionSnapshot(True, True, 50, 0, 50, 297_000)
    state = machine.run_once(_at(9, 30))
    assert state["status"] == "COMPLETE"
    assert state["total_filled_quantity"] == 100
    assert state["manual_sell_required_quantity"] == 100
    assert state["sell_authority"] == "operator_only_no_machine_sell"
    assert not hasattr(gateway, "submit_limit_sell")


def test_addon_waits_for_exact_date_source_and_never_submits_independently(
    tmp_path, monkeypatch
):
    source = tmp_path / "source.json"
    monkeypatch.setattr(addon_module, "SOURCE_STATE_PATH", source)
    gateway = FakeGateway()
    machine = SamsungMorningManualAddon(
        gateway=gateway, state_path=tmp_path / "addon.json"
    )
    state = machine.run_once(_at(8, 1))
    assert state["last_action"] == "waiting_for_source_episode"
    assert gateway.buy_calls == []


def test_addon_does_not_open_new_order_from_blocked_source(tmp_path, monkeypatch):
    source = tmp_path / "source.json"
    monkeypatch.setattr(addon_module, "SOURCE_STATE_PATH", source)
    _source(source, route="NXT", status="BLOCKED")
    gateway = FakeGateway()
    machine = SamsungMorningManualAddon(
        gateway=gateway, state_path=tmp_path / "addon.json"
    )
    machine.run_once(_at(8, 1))
    assert gateway.buy_calls == []


@pytest.mark.parametrize("source_status", ["COMPLETE", "NO_TRADE"])
def test_addon_does_not_late_mirror_terminal_source_episode(
    tmp_path, monkeypatch, source_status
):
    source = tmp_path / "source.json"
    monkeypatch.setattr(addon_module, "SOURCE_STATE_PATH", source)
    _source(source, route="NXT", status=source_status)
    payload = json.loads(source.read_text(encoding="utf-8"))
    for leg in payload["legs"]:
        leg["status"] = "COMPLETE"
    source.write_text(json.dumps(payload), encoding="utf-8")
    gateway = FakeGateway()
    machine = SamsungMorningManualAddon(
        gateway=gateway, state_path=tmp_path / "addon.json"
    )

    machine.run_once(_at(8, 1))

    assert gateway.buy_calls == []


def test_addon_requires_source_order_ownership_and_open_episode_status(
    tmp_path, monkeypatch
):
    source = tmp_path / "source.json"
    monkeypatch.setattr(addon_module, "SOURCE_STATE_PATH", source)
    _source(source, route="NXT")
    payload = json.loads(source.read_text(encoding="utf-8"))
    payload["owned_order_nos"] = []
    source.write_text(json.dumps(payload), encoding="utf-8")
    gateway = FakeGateway()
    machine = SamsungMorningManualAddon(
        gateway=gateway, state_path=tmp_path / "addon.json"
    )
    machine.run_once(_at(8, 1))
    assert gateway.buy_calls == []

    payload["owned_order_nos"] = ["NORMAL-NXT-1", "NORMAL-NXT-2"]
    for leg in payload["legs"]:
        leg["status"] = "BUY_CANCEL_PENDING"
    source.write_text(json.dumps(payload), encoding="utf-8")
    machine.run_once(_at(8, 2))
    assert gateway.buy_calls == []


def test_addon_never_opens_new_nxt_order_at_or_after_deadline(tmp_path, monkeypatch):
    source = tmp_path / "source.json"
    monkeypatch.setattr(addon_module, "SOURCE_STATE_PATH", source)
    _source(source, route="NXT")
    gateway = FakeGateway()
    machine = SamsungMorningManualAddon(
        gateway=gateway, state_path=tmp_path / "addon.json"
    )
    machine.run_once(_at(8, 10))
    assert gateway.buy_calls == []


def test_addon_mirrors_fresh_source_order_even_if_one_share_filled_first(
    tmp_path, monkeypatch
):
    source = tmp_path / "source.json"
    monkeypatch.setattr(addon_module, "SOURCE_STATE_PATH", source)
    _source(source, route="NXT", status="TARGET_OPEN")
    payload = json.loads(source.read_text(encoding="utf-8"))
    for leg in payload["legs"]:
        leg["status"] = "TARGET_OPEN"
    source.write_text(json.dumps(payload), encoding="utf-8")
    gateway = FakeGateway()
    machine = SamsungMorningManualAddon(
        gateway=gateway, state_path=tmp_path / "addon.json"
    )
    machine.run_once(_at(8, 1))
    assert [call[:3] for call in gateway.buy_calls] == [
        ("NXT", 291_500, 50),
        ("NXT", 291_000, 50),
    ]


def test_addon_keeps_custody_and_cancels_owned_order_when_source_disappears(
    tmp_path, monkeypatch
):
    source = tmp_path / "source.json"
    monkeypatch.setattr(addon_module, "SOURCE_STATE_PATH", source)
    _source(source, route="NXT")
    gateway = FakeGateway()
    machine = SamsungMorningManualAddon(
        gateway=gateway, state_path=tmp_path / "addon.json"
    )
    machine.run_once(_at(8, 1))
    source.unlink()
    machine.run_once(_at(8, 10))
    assert gateway.cancel_calls == [("NXT", "A1"), ("NXT", "A2")]


def test_addon_restart_blocks_unresolved_submit_intent(tmp_path, monkeypatch):
    source = tmp_path / "source.json"
    monkeypatch.setattr(addon_module, "SOURCE_STATE_PATH", source)
    state_path = tmp_path / "addon.json"
    machine = SamsungMorningManualAddon(gateway=FakeGateway(), state_path=state_path)
    state = machine.state
    state["legs"]["base"]["attempts"]["NXT"] = {
        "route": "NXT",
        "status": "SUBMITTING",
    }
    state_path.write_text(json.dumps(state), encoding="utf-8")
    restarted = SamsungMorningManualAddon(gateway=FakeGateway(), state_path=state_path)
    assert restarted.state["status"] == "BLOCKED"
    assert restarted.state["blocked_reason"].startswith("broker_write_interrupted")


class FakeResponse:
    status_code = 200
    headers = {}

    def __init__(self, body):
        self.body = body

    def json(self):
        return self.body


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.responses.pop(0)


def test_gateway_manual_addon_buy_and_cancel_use_bounded_official_contract(
    monkeypatch,
):
    monkeypatch.setattr(gateway_module, "is_buy_side_paused", lambda: False)
    session = FakeSession(
        [
            FakeResponse({"return_code": 0, "ord_no": "101"}),
            FakeResponse({"return_code": 0, "ord_no": "102"}),
        ]
    )
    gateway = KiwoomOneShareGateway(
        request_session=session,
        token_loader=lambda: "SHARED",
        order_authority=True,
        base_url="https://api.kiwoom.com",
    )
    assert gateway.submit_manual_addon_limit_buy(
        route="NXT", price=291_000, quantity=50
    ).accepted
    assert session.calls[0][1]["headers"]["api-id"] == "kt10000"
    assert session.calls[0][1]["json"]["ord_qty"] == "50"
    assert gateway.cancel_manual_addon_remaining(route="NXT", order_no="101").accepted
    assert session.calls[1][1]["headers"]["api-id"] == "kt10003"
    assert session.calls[1][1]["json"]["cncl_qty"] == "0"

    with pytest.raises(ValueError, match="outside_1_to_50"):
        gateway.submit_manual_addon_limit_buy(route="NXT", price=291_000, quantity=51)


def test_gateway_manual_addon_reconciles_50_share_order_without_widening_normal_contract():
    response_body = {
        "return_code": 0,
        "ord_cntr_dtl": [
            {
                "ord_no": "000101",
                "stk_cd": "A005930",
                "ord_qty": "50",
                "cntr_qty": "20",
                "ord_remnq": "30",
                "cntr_uv": "291000",
            }
        ],
    }
    addon_gateway = KiwoomOneShareGateway(
        request_session=FakeSession([FakeResponse(response_body)]),
        token_loader=lambda: "SHARED",
        base_url="https://api.kiwoom.com",
    )
    assert addon_gateway.manual_addon_execution_snapshot(
        route="NXT",
        order_no="101",
        order_date="2026-08-13",
        expected_order_qty=50,
    ) == ExecutionSnapshot(True, True, 20, 30, 50, 291_000)

    normal_gateway = KiwoomOneShareGateway(
        request_session=FakeSession([FakeResponse(response_body)]),
        token_loader=lambda: "SHARED",
        base_url="https://api.kiwoom.com",
    )
    normal_snapshot = normal_gateway.execution_snapshot(
        route="NXT",
        order_no="101",
        order_date="2026-08-13",
        expected_order_qty=10,
    )
    assert normal_snapshot.source_ok is False
    assert normal_snapshot.error == "invalid_episode_execution_contract"


def test_exact_date_systemd_unit_is_non_persistent_and_has_explicit_live_confirmation():
    unit_dir = addon_module.Path(__file__).resolve().parents[2] / "deploy" / "systemd"
    timer = (
        unit_dir / "korstockscan-samsung-morning-manual-addon-20260813.timer"
    ).read_text()
    service = (
        unit_dir / "korstockscan-samsung-morning-manual-addon-20260813.service"
    ).read_text()
    assert "OnCalendar=2026-08-13 07:59:05 Asia/Seoul" in timer
    assert "Persistent=false" in timer
    assert addon_module.ENABLE_ENV in service
    assert addon_module.LIVE_CONFIRMATION in service
