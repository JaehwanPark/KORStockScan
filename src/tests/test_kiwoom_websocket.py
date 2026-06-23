import asyncio
import json
from types import SimpleNamespace

import pytest

import src.engine.kiwoom_websocket as kiwoom_websocket
from src.engine.kiwoom_websocket import KiwoomWSManager


class _FakeWS:
    def __init__(self, messages):
        self._messages = list(messages)
        self.sent = []

    async def recv(self):
        if not self._messages:
            raise asyncio.TimeoutError
        return self._messages.pop(0)

    async def send(self, payload):
        self.sent.append(payload)


def test_login_success_message_helpers():
    success = {"trnm": "LOGIN", "return_code": 0}
    failure = {"trnm": "LOGIN", "return_code": 100}

    assert KiwoomWSManager._is_login_success_message(success) is True
    assert KiwoomWSManager._is_login_failure_message(success) is False
    assert KiwoomWSManager._is_login_success_message(failure) is False
    assert KiwoomWSManager._is_login_failure_message(failure) is True


def test_await_login_ack_handles_ping_then_success():
    manager = KiwoomWSManager("test-token")
    fake_ws = _FakeWS(
        [
            json.dumps({"trnm": "PING"}),
            json.dumps({"trnm": "LOGIN", "return_code": 0, "return_msg": "OK"}),
        ]
    )

    asyncio.run(manager._await_login_ack(fake_ws, timeout_sec=1.0))

    assert fake_ws.sent == [json.dumps({"trnm": "PONG"})]


def test_await_login_ack_raises_on_login_failure():
    manager = KiwoomWSManager("test-token")
    fake_ws = _FakeWS(
        [
            json.dumps({"trnm": "LOGIN", "return_code": 100013, "return_msg": "login pending"}),
        ]
    )

    with pytest.raises(RuntimeError):
        asyncio.run(manager._await_login_ack(fake_ws, timeout_sec=1.0))


@pytest.mark.parametrize(
    "code,message,expected",
    [
        ("8005", "Token이 유효하지 않습니다", True),
        ("805004", "토큰 인증에 실패했습니다 [CODE=8005]", True),
        ("100013", "login pending", False),
    ],
)
def test_is_auth_token_failure(code, message, expected):
    assert KiwoomWSManager._is_auth_token_failure(code, message) is expected


def test_target_defaults_include_intraday_high_low():
    manager = KiwoomWSManager("test-token")

    target = manager._ensure_target_defaults("005930")

    assert target["high"] == 0
    assert target["low"] == 0
    assert target["foreign_broker_net_est_qty"] == 0
    assert target["foreign_broker_net_est_delta_qty"] == 0


def test_send_reg_subscribes_foreign_broker_and_program_types():
    manager = KiwoomWSManager("test-token")
    fake_ws = _FakeWS([])
    manager.websocket = fake_ws
    manager._session_ready.set()

    asyncio.run(manager._send_reg(["005930"]))

    payload = json.loads(fake_ws.sent[0])
    reg_types = [entry["type"][0] for entry in payload["data"]]
    assert "0F" in reg_types
    assert "0w" in reg_types


def test_send_reg_uses_exchange_aware_items_for_nxt(monkeypatch):
    manager = KiwoomWSManager("test-token")
    fake_ws = _FakeWS([])
    manager.websocket = fake_ws
    manager._session_ready.set()

    monkeypatch.setattr(
        "src.utils.kiwoom_utils.get_effective_kiwoom_code",
        lambda code: f"{code}_AL" if code == "039490" else code,
    )

    asyncio.run(manager._send_reg(["039490"]))

    payload = json.loads(fake_ws.sent[0])
    assert payload["data"][0]["item"] == ["039490_AL"]
    assert manager.subscribed_codes == {"039490"}


def test_send_reg_uses_single_effective_route_by_default(monkeypatch):
    manager = KiwoomWSManager("test-token")
    fake_ws = _FakeWS([])
    manager.websocket = fake_ws
    manager._session_ready.set()

    monkeypatch.setattr(
        "src.utils.kiwoom_utils.get_effective_kiwoom_code",
        lambda code: code,
    )

    asyncio.run(manager._send_reg(["240810"]))

    payload = json.loads(fake_ws.sent[0])
    assert payload["data"][0]["item"] == ["240810"]
    assert manager.subscribed_codes == {"240810"}


def test_send_reg_adds_alternate_route_for_persistent_repair(monkeypatch):
    manager = KiwoomWSManager("test-token")
    fake_ws = _FakeWS([])
    manager.websocket = fake_ws
    manager._session_ready.set()

    monkeypatch.setattr(
        "src.utils.kiwoom_utils.get_effective_kiwoom_code",
        lambda code: code,
    )

    asyncio.run(manager._send_reg(["240810"], include_alternate_route=True))

    payload = json.loads(fake_ws.sent[0])
    assert payload["data"][0]["item"] == ["240810", "240810_AL"]
    assert manager.subscribed_codes == {"240810"}


def test_send_reg_respects_registered_item_budget(monkeypatch):
    manager = KiwoomWSManager("test-token")
    fake_ws = _FakeWS([])
    published = []
    manager.websocket = fake_ws
    manager._session_ready.set()
    manager.event_bus = SimpleNamespace(publish=lambda name, payload: published.append((name, payload)))

    monkeypatch.setenv("KORSTOCKSCAN_WS_MAX_REG_ITEMS", "1")
    monkeypatch.setattr("src.utils.kiwoom_utils.get_effective_kiwoom_code", lambda code: code)

    asyncio.run(manager._send_reg(["000001", "000002"], enforce_item_budget=True))

    payload = json.loads(fake_ws.sent[0])
    assert payload["data"][0]["item"] == ["000001"]
    assert manager.subscribed_codes == {"000001"}
    assert manager._registered_items_by_code == {"000001": ("000001",)}
    assert published == [
        (
            "WS_REG_BUDGET_SKIPPED",
            {
                "codes": ["000002"],
                "source": "",
                "max_items": 1,
                "registered_item_count": 0,
            },
        )
    ]


def test_execute_unsubscribe_removes_registered_item_budget_state(monkeypatch):
    manager = KiwoomWSManager("test-token")
    fake_ws = _FakeWS([])
    manager.websocket = fake_ws
    manager._session_ready.set()

    monkeypatch.setattr("src.utils.kiwoom_utils.get_effective_kiwoom_code", lambda code: code)

    asyncio.run(manager._send_reg(["000001"]))
    manager.execute_unsubscribe(["000001"])

    assert manager.subscribed_codes == set()
    assert manager._registered_items_by_code == {}
    assert "000001" not in manager.realtime_data


def test_send_reg_uses_append_refresh_after_first_batch(monkeypatch):
    manager = KiwoomWSManager("test-token")
    fake_ws = _FakeWS([])
    manager.websocket = fake_ws
    manager._session_ready.set()

    monkeypatch.setattr(kiwoom_websocket, "TRADING_RULES", SimpleNamespace(WS_REG_BATCH_SIZE=2))
    monkeypatch.setattr("src.utils.kiwoom_utils.get_effective_kiwoom_code", lambda code: code)

    asyncio.run(manager._send_reg(["000001", "000002", "000003", "000004", "000005"]))

    payloads = [json.loads(payload) for payload in fake_ws.sent]
    assert [payload["refresh"] for payload in payloads] == ["1", "0", "0"]
    assert [payload["data"][0]["item"] for payload in payloads] == [
        ["000001", "000002"],
        ["000003", "000004"],
        ["000005"],
    ]
    assert manager.subscribed_codes == {"000001", "000002", "000003", "000004", "000005"}


def test_send_reg_incremental_mode_does_not_replace_existing_group(monkeypatch):
    manager = KiwoomWSManager("test-token")
    fake_ws = _FakeWS([])
    manager.websocket = fake_ws
    manager._session_ready.set()

    monkeypatch.setattr(kiwoom_websocket, "TRADING_RULES", SimpleNamespace(WS_REG_BATCH_SIZE=2))
    monkeypatch.setattr("src.utils.kiwoom_utils.get_effective_kiwoom_code", lambda code: code)

    asyncio.run(
        manager._send_reg(
            ["000003", "000004", "000005"],
            replace_existing=False,
        )
    )

    payloads = [json.loads(payload) for payload in fake_ws.sent]
    assert [payload["refresh"] for payload in payloads] == ["0", "0"]
    assert [payload["data"][0]["item"] for payload in payloads] == [
        ["000003", "000004"],
        ["000005"],
    ]
    assert manager.subscribed_codes == {"000003", "000004", "000005"}


def test_command_ws_reg_recovery_forces_resubscribe(monkeypatch):
    manager = KiwoomWSManager("test-token")
    calls = []

    def fake_execute(codes, *, force=False, source="", repair_cycle=""):
        calls.append((codes, force, source, repair_cycle))

    monkeypatch.setattr(manager, "execute_subscribe", fake_execute)

    manager._handle_reg_event(
        {"codes": ["240810"], "source": "scanner_watching_ws_snapshot_recovery"}
    )

    assert calls == [(["240810"], True, "scanner_watching_ws_snapshot_recovery", "")]


def test_command_ws_reg_persistent_repair_passes_repair_cycle(monkeypatch):
    manager = KiwoomWSManager("test-token")
    calls = []

    def fake_execute(codes, *, force=False, source="", repair_cycle=""):
        calls.append((codes, force, source, repair_cycle))

    monkeypatch.setattr(manager, "execute_subscribe", fake_execute)

    manager._handle_reg_event(
        {
            "codes": ["240810"],
            "source": "scanner_persistent_ws_gap_recovery",
            "force": True,
            "repair_cycle": "persistent_ws_gap",
        }
    )

    assert calls == [(["240810"], True, "scanner_persistent_ws_gap_recovery", "persistent_ws_gap")]


def test_recent_reg_filter_skips_non_force_duplicates(monkeypatch):
    manager = KiwoomWSManager("test-token")
    monkeypatch.setenv("KORSTOCKSCAN_WS_REG_RECENT_TTL_SEC", "20")
    monkeypatch.setattr(kiwoom_websocket.time, "time", lambda: 1000.0)

    allowed, skipped = manager._filter_recent_reg_targets(["240810", "039490"], force=False)
    assert allowed == ["240810", "039490"]
    assert skipped == []

    allowed, skipped = manager._filter_recent_reg_targets(["240810", "039490"], force=False)
    assert allowed == []
    assert skipped == ["240810", "039490"]


def test_recent_reg_filter_throttles_force_duplicates(monkeypatch):
    manager = KiwoomWSManager("test-token")
    monkeypatch.setenv("KORSTOCKSCAN_WS_REG_RECENT_TTL_SEC", "20")
    monkeypatch.setattr(kiwoom_websocket.time, "time", lambda: 1000.0)

    allowed, skipped = manager._filter_recent_reg_targets(["240810"], force=False)
    assert allowed == ["240810"]
    assert skipped == []

    allowed, skipped = manager._filter_recent_reg_targets(["240810"], force=True)
    assert allowed == []
    assert skipped == ["240810"]


def test_recent_reg_filter_allows_after_ttl(monkeypatch):
    manager = KiwoomWSManager("test-token")
    monkeypatch.setenv("KORSTOCKSCAN_WS_REG_RECENT_TTL_SEC", "20")
    now = {"value": 1000.0}
    monkeypatch.setattr(kiwoom_websocket.time, "time", lambda: now["value"])

    assert manager._filter_recent_reg_targets(["240810"], force=False) == (["240810"], [])
    now["value"] = 1021.0
    assert manager._filter_recent_reg_targets(["240810"], force=False) == (["240810"], [])


def test_alternate_route_filter_limits_codes_per_batch(monkeypatch):
    manager = KiwoomWSManager("test-token")
    monkeypatch.setenv("KORSTOCKSCAN_WS_ALTERNATE_ROUTE_MAX_CODES", "2")
    monkeypatch.setenv("KORSTOCKSCAN_WS_ALTERNATE_ROUTE_TTL_SEC", "180")
    monkeypatch.setattr(kiwoom_websocket.time, "time", lambda: 1000.0)

    allowed, skipped = manager._filter_alternate_route_targets(["000001", "000002", "000003"])

    assert allowed == ["000001", "000002"]
    assert skipped == ["000003"]


def test_alternate_route_filter_throttles_recent_codes(monkeypatch):
    manager = KiwoomWSManager("test-token")
    monkeypatch.setenv("KORSTOCKSCAN_WS_ALTERNATE_ROUTE_MAX_CODES", "2")
    monkeypatch.setenv("KORSTOCKSCAN_WS_ALTERNATE_ROUTE_TTL_SEC", "180")
    now = {"value": 1000.0}
    monkeypatch.setattr(kiwoom_websocket.time, "time", lambda: now["value"])

    assert manager._filter_alternate_route_targets(["000001", "000002"]) == (["000001", "000002"], [])
    assert manager._filter_alternate_route_targets(["000001", "000003"]) == (["000003"], ["000001"])
    now["value"] = 1181.0
    assert manager._filter_alternate_route_targets(["000001"]) == (["000001"], [])


def test_send_reg_applies_alternate_only_to_allowed_codes(monkeypatch):
    manager = KiwoomWSManager("test-token")
    fake_ws = _FakeWS([])
    manager.websocket = fake_ws
    manager._session_ready.set()

    monkeypatch.setattr("src.utils.kiwoom_utils.get_effective_kiwoom_code", lambda code: code)

    asyncio.run(
        manager._send_reg(
            ["000001", "000002", "000003"],
            include_alternate_route=True,
            alternate_route_codes=["000001", "000002"],
        )
    )

    payload = json.loads(fake_ws.sent[0])
    assert payload["data"][0]["item"] == [
        "000001",
        "000001_AL",
        "000002",
        "000002_AL",
        "000003",
    ]


def test_persistent_repair_filter_limits_codes_per_batch(monkeypatch):
    manager = KiwoomWSManager("test-token")
    monkeypatch.setenv("KORSTOCKSCAN_WS_PERSISTENT_REPAIR_MAX_CODES", "3")
    monkeypatch.setenv("KORSTOCKSCAN_WS_PERSISTENT_REPAIR_TTL_SEC", "90")
    monkeypatch.setattr(kiwoom_websocket.time, "time", lambda: 1000.0)

    allowed, skipped = manager._filter_persistent_repair_targets(
        ["000001", "000002", "000003", "000004", "000005"]
    )

    assert allowed == ["000001", "000002", "000003"]
    assert skipped == ["000004", "000005"]


def test_persistent_repair_filter_throttles_recent_codes(monkeypatch):
    manager = KiwoomWSManager("test-token")
    monkeypatch.setenv("KORSTOCKSCAN_WS_PERSISTENT_REPAIR_MAX_CODES", "3")
    monkeypatch.setenv("KORSTOCKSCAN_WS_PERSISTENT_REPAIR_TTL_SEC", "90")
    now = {"value": 1000.0}
    monkeypatch.setattr(kiwoom_websocket.time, "time", lambda: now["value"])

    assert manager._filter_persistent_repair_targets(["000001", "000002"]) == (["000001", "000002"], [])
    assert manager._filter_persistent_repair_targets(["000001", "000003"]) == (["000003"], ["000001"])
    now["value"] = 1091.0
    assert manager._filter_persistent_repair_targets(["000001"]) == (["000001"], [])


def test_real_payload_with_exchange_suffix_updates_canonical_snapshot():
    manager = KiwoomWSManager("test-token")
    manager.subscribed_codes.add("039490")

    asyncio.run(
        manager._handle_message(
            json.dumps(
                {
                    "trnm": "REAL",
                    "data": [
                        {
                            "type": "0B",
                            "item": "039490_AL",
                            "values": {"10": "10000", "15": "+1", "228": "101.5"},
                        }
                    ],
                }
            )
        )
    )

    assert "039490" in manager.realtime_data
    assert "039490_AL" not in manager.realtime_data
    assert manager.realtime_data["039490"]["curr"] == 10000
    assert manager.realtime_data["039490"]["received_types"] == {"0B"}
