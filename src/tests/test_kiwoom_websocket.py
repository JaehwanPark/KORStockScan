import asyncio
import json
import os
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


def _reset_ws_hot_override_cache():
    with kiwoom_websocket._WS_HOT_RUNTIME_OVERRIDES_LOCK:
        kiwoom_websocket._WS_HOT_RUNTIME_OVERRIDES.update(
            {"mtime_ns": None, "values": {}, "next_check_ts": 0.0}
        )


@pytest.fixture(autouse=True)
def _isolate_ws_hot_runtime_override(tmp_path, monkeypatch):
    monkeypatch.setattr(
        kiwoom_websocket,
        "_WS_OPERATOR_RUNTIME_OVERRIDE_PATH",
        tmp_path / "missing_operator_runtime_overrides.env",
    )
    _reset_ws_hot_override_cache()
    yield
    _reset_ws_hot_override_cache()


def test_login_success_message_helpers():
    success = {"trnm": "LOGIN", "return_code": 0}
    failure = {"trnm": "LOGIN", "return_code": 100}

    assert KiwoomWSManager._is_login_success_message(success) is True
    assert KiwoomWSManager._is_login_failure_message(success) is False
    assert KiwoomWSManager._is_login_success_message(failure) is False
    assert KiwoomWSManager._is_login_failure_message(failure) is True


def test_await_login_ack_handles_ping_then_success():
    manager = KiwoomWSManager("test-token")
    ping_payload = json.dumps({"trnm": "PING", "ping_id": "abc123"})
    fake_ws = _FakeWS(
        [
            json.dumps(["PING"]),
            ping_payload,
            json.dumps({"trnm": "LOGIN", "return_code": 0, "return_msg": "OK"}),
        ]
    )

    asyncio.run(manager._await_login_ack(fake_ws, timeout_sec=1.0))

    assert fake_ws.sent == [ping_payload]


def test_handle_message_echoes_ping_payload():
    manager = KiwoomWSManager("test-token")
    fake_ws = _FakeWS([])
    manager.websocket = fake_ws
    ping_payload = json.dumps({"trnm": "PING", "seq": "keepalive-1"})

    asyncio.run(manager._handle_message(ping_payload))

    assert fake_ws.sent == [ping_payload]


def test_handle_message_ignores_non_dict_payload():
    manager = KiwoomWSManager("test-token")
    fake_ws = _FakeWS([])
    manager.websocket = fake_ws

    asyncio.run(manager._handle_message(json.dumps(["PING"])))

    assert fake_ws.sent == []


def test_await_login_ack_raises_on_login_failure():
    manager = KiwoomWSManager("test-token")
    fake_ws = _FakeWS(
        [
            json.dumps({"trnm": "LOGIN", "return_code": 100013, "return_msg": "login pending"}),
        ]
    )

    with pytest.raises(RuntimeError):
        asyncio.run(manager._await_login_ack(fake_ws, timeout_sec=1.0))


def test_post_login_bootstrap_skips_condition_list_by_default(monkeypatch):
    monkeypatch.delenv("KORSTOCKSCAN_WS_CONDITION_SEARCH_ENABLED", raising=False)
    manager = KiwoomWSManager("test-token")
    fake_ws = _FakeWS([])
    manager.websocket = fake_ws

    asyncio.run(manager._send_post_login_bootstrap())

    sent = [json.loads(payload) for payload in fake_ws.sent]
    assert not any(payload.get("trnm") == "CNSRLST" for payload in sent)


def test_condition_list_ignored_by_default(monkeypatch):
    monkeypatch.delenv("KORSTOCKSCAN_WS_CONDITION_SEARCH_ENABLED", raising=False)
    monkeypatch.delenv("KORSTOCKSCAN_SWING_REAL_WATCHING_ENABLED", raising=False)

    async def no_sleep(*args, **kwargs):
        return None

    monkeypatch.setattr(kiwoom_websocket.asyncio, "sleep", no_sleep)
    manager = KiwoomWSManager("test-token")
    fake_ws = _FakeWS([])
    manager.websocket = fake_ws

    asyncio.run(
        manager._handle_message(
            json.dumps(
                {
                    "trnm": "CNSRLST",
                    "data": [
                        {"seq": "1", "name": "scalp_candid_normal_01"},
                        {"seq": "6", "name": "kospi_short_swing_01"},
                    ],
                }
            )
        )
    )

    assert fake_ws.sent == []
    assert manager.condition_dict == {}


def test_condition_list_allows_conditions_when_explicitly_enabled(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_WS_CONDITION_SEARCH_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_SWING_REAL_WATCHING_ENABLED", "true")

    async def no_sleep(*args, **kwargs):
        return None

    monkeypatch.setattr(kiwoom_websocket.asyncio, "sleep", no_sleep)
    manager = KiwoomWSManager("test-token")
    fake_ws = _FakeWS([])
    manager.websocket = fake_ws

    asyncio.run(
        manager._handle_message(
            json.dumps(
                {
                    "trnm": "CNSRLST",
                    "data": [
                        {"seq": "1", "name": "scalp_candid_normal_01"},
                        {"seq": "6", "name": "kospi_short_swing_01"},
                    ],
                }
            )
        )
    )

    sent = [json.loads(payload) for payload in fake_ws.sent]
    assert [payload["seq"] for payload in sent] == ["1", "6"]
    assert manager.condition_dict == {
        "1": "scalp_candid_normal_01",
        "6": "kospi_short_swing_01",
    }


def test_condition_realtime_events_ignored_by_default(monkeypatch):
    monkeypatch.delenv("KORSTOCKSCAN_WS_CONDITION_SEARCH_ENABLED", raising=False)
    manager = KiwoomWSManager("test-token")
    manager.condition_dict = {"1": "scalp_candid_normal_01"}

    asyncio.run(
        manager._handle_message(
            json.dumps(
                {
                    "trnm": "REAL",
                    "data": [
                        {
                            "type": "02",
                            "name": "조건검색",
                            "values": {"841": "1", "9001": "A005930", "843": "I"},
                        }
                    ],
                }
            )
        )
    )

    assert manager._state_event_queue.empty()


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
    assert payload["refresh"] == "1"
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


def test_send_reg_preserves_refresh_for_all_batches(monkeypatch):
    manager = KiwoomWSManager("test-token")
    fake_ws = _FakeWS([])
    manager.websocket = fake_ws
    manager._session_ready.set()

    monkeypatch.setattr(kiwoom_websocket, "TRADING_RULES", SimpleNamespace(WS_REG_BATCH_SIZE=2))
    monkeypatch.setattr("src.utils.kiwoom_utils.get_effective_kiwoom_code", lambda code: code)

    asyncio.run(manager._send_reg(["000001", "000002", "000003", "000004", "000005"]))

    payloads = [json.loads(payload) for payload in fake_ws.sent]
    assert [payload["refresh"] for payload in payloads] == ["1", "1", "1"]
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
    assert [payload["refresh"] for payload in payloads] == ["1", "1"]
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


def test_persistent_repair_filter_prioritizes_previous_overflow(monkeypatch):
    manager = KiwoomWSManager("test-token")
    monkeypatch.setenv("KORSTOCKSCAN_WS_PERSISTENT_REPAIR_MAX_CODES", "3")
    monkeypatch.setenv("KORSTOCKSCAN_WS_PERSISTENT_REPAIR_TTL_SEC", "0")
    now = {"value": 1000.0}
    monkeypatch.setattr(kiwoom_websocket.time, "time", lambda: now["value"])

    allowed, skipped = manager._filter_persistent_repair_targets(
        ["000001", "000002", "000003", "000004", "000005"]
    )
    assert allowed == ["000001", "000002", "000003"]
    assert skipped == ["000004", "000005"]

    now["value"] = 1001.0
    allowed, skipped = manager._filter_persistent_repair_targets(
        ["000001", "000002", "000003", "000004", "000005"]
    )

    assert allowed == ["000004", "000005", "000001"]
    assert skipped == ["000002", "000003"]


def test_persistent_repair_defaults_refresh_stale_scanner_sources_quickly(monkeypatch):
    manager = KiwoomWSManager("test-token")
    monkeypatch.delenv("KORSTOCKSCAN_WS_PERSISTENT_REPAIR_MAX_CODES", raising=False)
    monkeypatch.delenv("KORSTOCKSCAN_WS_PERSISTENT_REPAIR_TTL_SEC", raising=False)
    monkeypatch.delenv("KORSTOCKSCAN_WS_PERSISTENT_REPAIR_REBUILD_GROUP_ENABLED", raising=False)
    now = {"value": 1000.0}
    monkeypatch.setattr(kiwoom_websocket.time, "time", lambda: now["value"])

    assert manager._persistent_repair_max_codes() == 8
    assert manager._persistent_repair_ttl_sec() == 30.0
    assert manager._persistent_repair_rebuild_group_enabled() is False
    assert manager._filter_persistent_repair_targets(["000001"]) == (["000001"], [])
    assert manager._filter_persistent_repair_targets(["000001"]) == ([], ["000001"])
    now["value"] = 1030.0

    assert manager._filter_persistent_repair_targets(["000001"]) == (["000001"], [])


def test_persistent_repair_rebuild_targets_default_off(monkeypatch):
    manager = KiwoomWSManager("test-token")
    manager.subscribed_codes.update({"000001", "000002"})
    monkeypatch.delenv("KORSTOCKSCAN_WS_PERSISTENT_REPAIR_REBUILD_GROUP_ENABLED", raising=False)

    rebuild, targets = manager._persistent_repair_rebuild_targets(["000003"])

    assert rebuild is False
    assert targets == ["000003"]


def test_persistent_repair_rebuild_targets_merges_subscribed_when_enabled(monkeypatch):
    manager = KiwoomWSManager("test-token")
    manager.subscribed_codes.update({"000001", "000002"})
    monkeypatch.setenv("KORSTOCKSCAN_WS_PERSISTENT_REPAIR_REBUILD_GROUP_ENABLED", "1")
    monkeypatch.setenv("KORSTOCKSCAN_WS_PERSISTENT_REPAIR_REBUILD_GROUP_MIN_INTERVAL_SEC", "30")
    now = {"value": 1000.0}
    monkeypatch.setattr(kiwoom_websocket.time, "time", lambda: now["value"])

    rebuild, targets = manager._persistent_repair_rebuild_targets(["000003", "000001"])

    assert rebuild is True
    assert targets == ["000001", "000002", "000003"]

    now["value"] = 1010.0
    rebuild, targets = manager._persistent_repair_rebuild_targets(["000004"])
    assert rebuild is False
    assert targets == ["000004"]

    now["value"] = 1031.0
    rebuild, targets = manager._persistent_repair_rebuild_targets(["000004"])
    assert rebuild is True
    assert targets == ["000001", "000002", "000004"]


def test_alternate_route_defaults_cover_more_repair_candidates(monkeypatch):
    monkeypatch.delenv("KORSTOCKSCAN_WS_ALTERNATE_ROUTE_MAX_CODES", raising=False)
    monkeypatch.delenv("KORSTOCKSCAN_WS_ALTERNATE_ROUTE_TTL_SEC", raising=False)

    assert KiwoomWSManager._alternate_route_max_codes() == 6
    assert KiwoomWSManager._alternate_route_ttl_sec() == 45.0


def test_alternate_route_hot_override_allows_rebuild_group_coverage(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_WS_ALTERNATE_ROUTE_MAX_CODES", "28")

    assert KiwoomWSManager._alternate_route_max_codes() == 28


def test_ws_repair_budget_hot_reloads_operator_override_file(tmp_path, monkeypatch):
    override_path = tmp_path / "operator_runtime_overrides.env"
    monkeypatch.setattr(kiwoom_websocket, "_WS_OPERATOR_RUNTIME_OVERRIDE_PATH", override_path)
    monkeypatch.setattr(kiwoom_websocket, "_WS_HOT_RUNTIME_OVERRIDE_REFRESH_SEC", 0.0)
    monkeypatch.delenv("KORSTOCKSCAN_WS_ALTERNATE_ROUTE_MAX_CODES", raising=False)
    monkeypatch.delenv("KORSTOCKSCAN_WS_PERSISTENT_REPAIR_MAX_CODES", raising=False)
    _reset_ws_hot_override_cache()

    override_path.write_text(
        "\n".join(
            [
                "export KORSTOCKSCAN_WS_ALTERNATE_ROUTE_MAX_CODES=11",
                "export KORSTOCKSCAN_WS_ALTERNATE_ROUTE_TTL_SEC=30",
                "export KORSTOCKSCAN_WS_MAX_REG_ITEMS=41",
                "export KORSTOCKSCAN_WS_PERSISTENT_REPAIR_MAX_CODES=17",
                "export KORSTOCKSCAN_WS_PERSISTENT_REPAIR_REBUILD_GROUP_ENABLED=1",
                "export KORSTOCKSCAN_WS_PERSISTENT_REPAIR_REBUILD_GROUP_MIN_INTERVAL_SEC=19",
                "export KORSTOCKSCAN_WS_PERSISTENT_REPAIR_STUCK_COOLDOWN_SEC=120",
                "export KORSTOCKSCAN_WS_PERSISTENT_REPAIR_STUCK_MIN_ATTEMPTS=4",
                "export KORSTOCKSCAN_WS_PERSISTENT_REPAIR_TTL_SEC=20",
                "export KORSTOCKSCAN_BUY_SCORE_THRESHOLD=1",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    os.utime(override_path, ns=(1_000_000_000, 1_000_000_000))

    assert KiwoomWSManager._alternate_route_max_codes() == 11
    assert KiwoomWSManager._alternate_route_ttl_sec() == 30.0
    assert KiwoomWSManager._max_registered_item_count() == 41
    assert KiwoomWSManager._persistent_repair_max_codes() == 17
    assert KiwoomWSManager._persistent_repair_rebuild_group_enabled() is True
    assert KiwoomWSManager._persistent_repair_rebuild_group_min_interval_sec() == 19.0
    assert KiwoomWSManager._persistent_repair_stuck_cooldown_sec() == 120.0
    assert KiwoomWSManager._persistent_repair_stuck_min_attempts() == 4
    assert KiwoomWSManager._persistent_repair_ttl_sec() == 20.0
    assert kiwoom_websocket._ws_hot_runtime_override_value("KORSTOCKSCAN_BUY_SCORE_THRESHOLD") is None

    override_path.write_text(
        "export KORSTOCKSCAN_WS_ALTERNATE_ROUTE_MAX_CODES=9\n",
        encoding="utf-8",
    )
    os.utime(override_path, ns=(2_000_000_000, 2_000_000_000))

    assert KiwoomWSManager._alternate_route_max_codes() == 9


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


def test_persistent_repair_stuck_cooldown_skips_no_tick_code(monkeypatch):
    manager = KiwoomWSManager("test-token")
    monkeypatch.setenv("KORSTOCKSCAN_WS_PERSISTENT_REPAIR_MAX_CODES", "3")
    monkeypatch.setenv("KORSTOCKSCAN_WS_PERSISTENT_REPAIR_TTL_SEC", "0")
    monkeypatch.setenv("KORSTOCKSCAN_WS_PERSISTENT_REPAIR_STUCK_MIN_ATTEMPTS", "2")
    monkeypatch.setenv("KORSTOCKSCAN_WS_PERSISTENT_REPAIR_STUCK_COOLDOWN_SEC", "120")
    now = {"value": 1000.0}
    monkeypatch.setattr(kiwoom_websocket.time, "time", lambda: now["value"])
    manager.subscribed_codes.add("000001")

    assert manager._filter_persistent_repair_targets(["000001"]) == (["000001"], [])
    now["value"] = 1001.0
    assert manager._filter_persistent_repair_targets(["000001"]) == (["000001"], [])
    now["value"] = 1002.0
    assert manager._filter_persistent_repair_targets(["000001", "000002"]) == (
        ["000002"],
        ["000001"],
    )

    now["value"] = 1122.0
    assert manager._filter_persistent_repair_targets(["000001"]) == (["000001"], [])


def test_persistent_repair_attempts_clear_after_first_realtime(monkeypatch):
    manager = KiwoomWSManager("test-token")
    monkeypatch.setenv("KORSTOCKSCAN_WS_PERSISTENT_REPAIR_TTL_SEC", "0")
    monkeypatch.setenv("KORSTOCKSCAN_WS_PERSISTENT_REPAIR_STUCK_MIN_ATTEMPTS", "2")
    monkeypatch.setenv("KORSTOCKSCAN_WS_PERSISTENT_REPAIR_STUCK_COOLDOWN_SEC", "120")
    now = {"value": 1000.0}
    monkeypatch.setattr(kiwoom_websocket.time, "time", lambda: now["value"])
    manager.subscribed_codes.add("000001")

    assert manager._filter_persistent_repair_targets(["000001"]) == (["000001"], [])

    asyncio.run(
        manager._handle_message(
            json.dumps(
                {
                    "trnm": "REAL",
                    "data": [
                        {
                            "type": "0B",
                            "item": "000001",
                            "values": {"10": "10000", "15": "+1", "228": "101.5"},
                        }
                    ],
                }
            )
        )
    )

    assert manager._persistent_repair_no_tick_attempts.get("000001") is None
    now["value"] = 1001.0
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
