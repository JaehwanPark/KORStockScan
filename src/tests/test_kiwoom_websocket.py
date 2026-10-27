import asyncio
import json
import os
from collections import deque
from datetime import datetime, tzinfo
from types import SimpleNamespace

import pytest

import src.engine.kiwoom_websocket as kiwoom_websocket
from src.engine.kiwoom_websocket import KiwoomWSManager

_SESSION_ROUTE_REQUIRED = KiwoomWSManager._integrated_aftermarket_route_required


def test_main_depth_wire_normalization_and_sampler_evidence_detect_actual_local_loss(
    monkeypatch,
):
    from src.engine import sniper_state_handlers as handlers
    from src.engine.monitoring.ws_receive_expectation import (
        classify_delay_quote_collection,
    )

    manager = KiwoomWSManager("test-token")
    clock = [datetime.fromisoformat("2026-10-27T08:00:00+09:00").timestamp()]
    monkeypatch.setattr(kiwoom_websocket.time, "time", lambda: clock[0])
    monkeypatch.setattr(manager, "_maybe_write_dashboard_snapshot", lambda: None)
    manager.market_session_state = "P"
    manager._market_data_transport_epoch = 7
    manager._session_ready.set()
    manager.subscribed_codes.add("196170")
    manager._registered_items_by_code["196170"] = ["196170_NX"]
    manager._registered_item_types["196170_NX"] = ("0B", "0D")
    manager._registered_item_epochs["196170_NX"] = 7
    manager._record_main_source_registration_locked(
        "196170_NX", ("0B", "0D"), source="main-test"
    )

    def receive(values):
        asyncio.run(
            manager._handle_message(
                json.dumps(
                    dict(
                        trnm="REAL",
                        data=[dict(type="0D", item="196170_NX", values=values)],
                    )
                ),
                received_at=datetime.fromtimestamp(clock[0], kiwoom_websocket.KST),
                transport_epoch=7,
            )
        )

    values = {"21": "080100", "41": "100", "51": "99", "61": "10", "71": "10"}
    for _ in range(105):
        clock[0] += 1
        receive(values)
    clock[0] += 0.8
    snapshot = manager.get_pre_submit_delay_depth("196170")
    depth = next(iter(snapshot["realtime_type_snapshots_by_route"].values()))["0D"]
    evidence = depth["delay_collection_evidence"]
    main_depth = next(
        iter(
            manager.get_latest_data("196170")[
                "realtime_type_snapshots_by_route"
            ].values()
        )
    )["0D"]
    assert (
        main_depth["delay_collection_evidence"]["subscription_generation"]
        == evidence["subscription_generation"]
    )
    assert evidence["wire_count"] == evidence["normalized_count"] == 105
    assert evidence["cadence_basis"] == "provisional_p95"
    emitted = []
    monkeypatch.setattr(
        handlers,
        "_log_pre_submit_delay_event",
        lambda *a, **kw: emitted.append(kw) or True,
    )

    def observe(ws):
        handlers._observe_pre_submit_delay_state_quote(
            dict(
                _pre_submit_delay_observation=dict(
                    id="main-source",
                    remaining_sec=[0],
                    committed_at_epoch=clock[0],
                    route="NXT_ONLY",
                    quote_transport_epoch=7,
                    decision_source_sha256="a" * 64,
                )
            ),
            "196170",
            ws,
            now_ts=clock[0],
        )
        return dict(emitted[-1], stock_code="196170")

    first = observe(snapshot)
    assert first["quote_valid"] is False
    assert (
        classify_delay_quote_collection(first, ledger_complete=True)["state"]
        == "expected_wait"
    )
    # This wire receipt is admitted by the same owner but has no values and
    # cannot reach normalization. The next normalized wire proves the loss.
    clock[0] += 1
    receive({})
    clock[0] += 1
    receive(values)
    lost = observe(manager.get_pre_submit_delay_depth("196170"))
    result = classify_delay_quote_collection(lost, ledger_complete=True)
    assert result["state"] == "collection_fault_confirmed"
    assert result["reason"] == "wire_to_normalized_loss"
    assert lost["quote_valid"] is True
    lost_receipt = dict(lost["quote_collection_evidence"])
    clock[0] += 1
    receive(values)
    recovered = observe(manager.get_pre_submit_delay_depth("196170"))
    healthy = classify_delay_quote_collection(recovered, ledger_complete=True)
    assert healthy["state"] == "locally_healthy"
    assert healthy["loss_event_id"] == result["loss_event_id"]
    receipt = recovered["quote_collection_evidence"]
    assert receipt["missing_normalizations"] == 1
    assert (
        receipt["normalized_route_sequence"] == recovered["quote_route_sequence"] == 107
    )
    assert lost["quote_collection_evidence"] == lost_receipt
    assert recovered["quote_valid"] is True
    assert not manager._exact_probe_item_leases


def test_delay_cadence_resets_on_registration_epoch_session_and_remove(monkeypatch):
    manager = KiwoomWSManager("test-token")
    manager.market_session_state = "P"
    manager._market_data_transport_epoch = 7
    manager._registered_items_by_code["196170"] = ["196170_NX"]
    manager._registered_item_epochs["196170_NX"] = 7
    manager._record_main_source_registration_locked(
        "196170_NX", ("0D",), source="main-test"
    )
    original = manager._delay_depth_cadence["196170_NX"]
    at = original.scope["registered_at_epoch"] + 1
    message = dict(type="0D", item="196170_NX")
    manager._record_source_wire_receipt(message, at, transport_epoch=7)
    manager.market_session_state = "Q"
    manager._record_source_wire_receipt(message, at + 1, transport_epoch=7)
    assert manager._delay_depth_cadence["196170_NX"].wire_count == 1
    assert manager._delay_depth_cadence["196170_NX"].scope["session"] == "Q"
    manager._market_data_transport_epoch = 8
    assert manager._record_source_wire_receipt(message, at + 2, transport_epoch=8) is None
    manager._registered_item_epochs["196170_NX"] = 8
    manager._record_main_source_registration_locked(
        "196170_NX", ("0D",), source="main-test"
    )
    assert manager._delay_depth_cadence["196170_NX"].wire_count == 0
    # A packet captured by the prior socket cannot become evidence for the
    # replacement Main registration, even when the item itself is unchanged.
    assert manager._record_source_wire_receipt(
        message, at + 3, transport_epoch=7
    ) is None
    assert manager._delay_depth_cadence["196170_NX"].wire_count == 0
    assert manager._record_source_wire_receipt(
        message, at + 4, transport_epoch=8
    ) is not None
    assert manager._delay_depth_cadence["196170_NX"].wire_count == 1
    manager._registered_items_by_code.clear()
    manager._record_main_source_registration_locked(
        "000660_NX", ("0D",), source="main-test"
    )
    assert "196170_NX" not in manager._delay_depth_cadence


def test_delay_diagnostics_capacity_never_changes_native_registration(monkeypatch):
    from src.engine.scalping import pre_submit_delay_observation as observation

    monkeypatch.setattr(observation, "MAX_ACTIVE", 2)
    manager = KiwoomWSManager("test-token")
    manager.market_session_state = "P"
    manager._market_data_transport_epoch = 7
    for code in ("000001", "000002", "000003"):
        item = code + "_NX"
        manager._registered_items_by_code[code] = [item]
        manager._registered_item_epochs[item] = 7
        manager._record_main_source_registration_locked(
            item, ("0D",), source="capacity-test"
        )
    assert len(manager._delay_depth_cadence) == 2
    assert len(manager._micro_reversion_registration_receipt["items"]) == 3
    assert manager._registered_items_by_code["000003"] == ["000003_NX"]


def test_old_wire_receipt_cannot_normalize_a_replacement_registration():
    manager = KiwoomWSManager("test-token")
    manager.market_session_state = "P"
    manager._market_data_transport_epoch = 7
    manager._registered_items_by_code["196170"] = ["196170_NX"]
    manager._registered_item_epochs["196170_NX"] = 7
    manager._record_main_source_registration_locked("196170_NX", ("0D",), source="old")
    at = manager._delay_depth_cadence["196170_NX"].scope["registered_at_epoch"] + 1
    old = manager._record_source_wire_receipt(dict(item="196170_NX", type="0D"), at, transport_epoch=7)
    manager._record_main_source_registration_locked("196170_NX", ("0D",), source="new")
    assert (
        old[0].scope["subscription_generation"]
        != manager._delay_depth_cadence["196170_NX"].scope["subscription_generation"]
    )
    new = manager._record_source_wire_receipt(dict(item="196170_NX", type="0D"), at + 1, transport_epoch=7)
    manager._record_micro_reversion_registration_receipt(
        item="196170_NX",
        realtime_type="0D",
        observed_at_epoch=at + 1,
        delay_depth_wire_id=old,
    )
    current = manager._delay_depth_cadence["196170_NX"]
    assert current.normalized_count == 0
    manager._record_micro_reversion_registration_receipt(
        item="196170_NX",
        realtime_type="0D",
        observed_at_epoch=at + 1,
        delay_depth_wire_id=new,
    )
    assert current.normalized_count == 1 and current.missing_normalizations == 0


def test_delay_depth_reader_copies_only_existing_0d_and_current_transport():
    manager = KiwoomWSManager("test-token")
    manager._market_data_transport_epoch = 7

    class History:
        def __deepcopy__(self, memo):
            pytest.fail("delay sampler traversed accumulated history")

    book = {"asks": [{"price": 100, "volume": 2}], "bids": [{"price": 99, "volume": 2}]}
    manager.realtime_data["005930"] = dict(
        price_history=History(),
        realtime_type_snapshots_by_route={
            "integrated": {
                "0D": dict(
                    orderbook=book,
                    item="005930_AL",
                    market_route="KRX_NXT_INTEGRATED",
                    transport_epoch=7,
                    observed_epoch=10.0,
                ),
                "0B": {"history": History()},
            }
        },
    )
    value = manager.get_pre_submit_delay_depth("005930")
    assert value["market_data_transport_epoch"] == 7
    assert set(value) == {
        "market_data_transport_epoch",
        "realtime_type_snapshots_by_route",
    }
    value["realtime_type_snapshots_by_route"]["integrated"]["0D"]["orderbook"]["asks"][
        0
    ]["price"] = 999
    assert book["asks"][0]["price"] == 100


def test_retired_vcp_and_s15_conditions_are_absent_from_ws_bootstrap():
    keywords = set(kiwoom_websocket.SCALP_CONDITION_KEYWORDS)
    assert not keywords.intersection(
        {
            "vcp_candid_01",
            "vcp_shooting_01",
            "vcp_shooting_next_01",
            "s15_scan_base_01",
            "s15_trigger_break_01",
        }
    )


def test_exact_item_reader_uses_observation_store_and_current_registration():
    manager = KiwoomWSManager("test-token")
    manager._market_data_transport_epoch = 3
    manager._registered_items_by_code["005930"] = (
        "005930",
        "005930_NX",
        "005930_AL",
    )
    manager._registered_item_epochs.update(
        {
            "005930": 3,
            "005930_NX": 3,
            "005930_AL": 3,
        }
    )
    manager._micro_reversion_observation_only_items.update(
        {
            "005930_NX",
            "005930_AL",
        }
    )
    regular = manager._ensure_target_defaults("005930")
    regular["curr"] = 70000
    nxt = manager._ensure_target_defaults(
        "005930_NX",
        store=manager._micro_reversion_observation_route_data,
    )
    nxt["curr"] = 70050
    integrated = manager._ensure_target_defaults(
        "005930_AL",
        store=manager._micro_reversion_observation_route_data,
    )
    integrated["curr"] = 70100

    assert manager.get_exact_item_data("005930", "005930")["curr"] == 70000
    assert manager.get_exact_item_data("005930", "005930_NX")["curr"] == 70050
    assert manager.get_exact_item_data("005930", "005930_AL")["curr"] == 70100
    assert manager.get_latest_data("005930")["curr"] == 70000

    manager._registered_item_epochs["005930_AL"] = 2
    assert manager.get_exact_item_data("005930", "005930_AL") == {}
    manager._registered_item_epochs["005930_AL"] = 3
    manager._registered_items_by_code["005930"] = ("005930",)
    assert manager.get_exact_item_data("005930", "005930_AL") == {}


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


class _RecordingTransportEpochCollector:
    def __init__(self, order=None):
        self.epochs = []
        self.order = order

    def begin_transport_epoch(self):
        epoch = 1_000 + len(self.epochs)
        self.epochs.append(epoch)
        if self.order is not None:
            self.order.append("transport_epoch")
        return epoch


class _OffsetlessTZ(tzinfo):
    def utcoffset(self, _dt):
        return None

    def dst(self, _dt):
        return None


def _reset_ws_hot_override_cache():
    with kiwoom_websocket._WS_HOT_RUNTIME_OVERRIDES_LOCK:
        kiwoom_websocket._WS_HOT_RUNTIME_OVERRIDES.update(
            {"mtime_ns": None, "values": {}, "next_check_ts": 0.0}
        )


@pytest.fixture(autouse=True)
def _isolate_ws_hot_runtime_override(tmp_path, monkeypatch):
    # Legacy tests model regular-session registration, independent of host time.
    monkeypatch.setattr(
        KiwoomWSManager,
        "_integrated_aftermarket_route_required",
        staticmethod(lambda: False),
    )
    monkeypatch.setattr(
        kiwoom_websocket,
        "_WS_OPERATOR_RUNTIME_OVERRIDE_PATH",
        tmp_path / "missing_operator_runtime_overrides.env",
    )
    _reset_ws_hot_override_cache()
    yield
    _reset_ws_hot_override_cache()


@pytest.mark.parametrize(
    "clock,required",
    [("14:00", False), ("16:00", True), ("19:45", True), ("20:00", False)],
)
def test_integrated_runtime_route_uses_session_owner(monkeypatch, clock, required):
    at = datetime.fromisoformat(f"2026-09-16T{clock}:00+09:00")
    monkeypatch.setattr(
        kiwoom_websocket, "datetime", SimpleNamespace(now=lambda _tz: at)
    )
    assert _SESSION_ROUTE_REQUIRED() is required


def test_aftermarket_default_registers_al_without_nxt_flag(monkeypatch):
    manager = KiwoomWSManager("test-token")
    manager.websocket = _FakeWS([])
    manager._session_ready.set()
    monkeypatch.setattr(manager, "_integrated_aftermarket_route_required", lambda: True)
    monkeypatch.setattr(
        "src.utils.kiwoom_utils.get_effective_kiwoom_code",
        lambda _code: pytest.fail("NXT flag is not the integrated session route owner"),
    )
    asyncio.run(manager._send_reg(["425040"], enforce_item_budget=True))
    packet = json.loads(manager.websocket.sent[0])
    assert packet["refresh"] == "1"
    assert packet["data"][0]["item"] == ["425040_AL"]
    assert manager._runtime_primary_items_by_code == {"425040": "425040_AL"}


def test_runtime_route_transition_adds_al_once_and_preserves_custody(monkeypatch):
    manager = KiwoomWSManager("test-token")
    manager.websocket = _FakeWS([])
    manager._session_ready.set()
    monkeypatch.setattr(
        "src.utils.kiwoom_utils.get_effective_kiwoom_code", lambda code: code
    )
    asyncio.run(manager._send_reg(["425040"]))
    manager.realtime_data["425040"]["curr"] = 9830
    before = manager.get_latest_data("425040")
    manager._micro_reversion_observation_only_codes.add("000001")
    manager._implicit_runtime_route_codes.add("000001")
    manager.subscribed_codes.add("000001")
    monkeypatch.setattr(manager, "_integrated_aftermarket_route_required", lambda: True)
    asyncio.run(manager._reconcile_integrated_runtime_routes())
    asyncio.run(manager._reconcile_integrated_runtime_routes())
    assert len(manager.websocket.sent) == 2
    packet = json.loads(manager.websocket.sent[-1])
    assert packet["refresh"] == "1" and packet["trnm"] == "REG"
    assert packet["data"][0]["item"] == ["425040_AL"]
    assert manager._registered_items_by_code["425040"] == ("425040", "425040_AL")
    after = manager.get_latest_data("425040")
    # Consume-time health ages may advance; routing must not change custody or
    # any producer timestamp/value in the underlying market frame.
    after.pop("market_data_health", None)
    before.pop("market_data_health", None)
    assert after == before
    assert manager._micro_reversion_observation_only_codes == {"000001"}


def test_runtime_route_transition_respects_item_budget(monkeypatch):
    manager = KiwoomWSManager("test-token")
    manager.websocket = _FakeWS([])
    manager._session_ready.set()
    manager.subscribed_codes.add("425040")
    manager._implicit_runtime_route_codes.add("425040")
    manager._registered_items_by_code["425040"] = ("425040",)
    monkeypatch.setattr(manager, "_integrated_aftermarket_route_required", lambda: True)
    monkeypatch.setattr(manager, "_max_registered_item_count", lambda: 1)
    asyncio.run(manager._reconcile_integrated_runtime_routes())
    assert manager.websocket.sent == []
    assert manager._runtime_primary_items_by_code == {}


def test_integrated_runtime_isolates_plain_receipts_without_fabricating_venue(
    monkeypatch,
):
    manager = KiwoomWSManager("test-token")
    manager.subscribed_codes.add("425040")
    manager._runtime_primary_items_by_code["425040"] = "425040_AL"
    manager._runtime_integrated_route_active = True
    monkeypatch.setattr(manager, "_maybe_write_dashboard_snapshot", lambda: None)
    monkeypatch.setattr(
        manager, "_observe_micro_reversion_forward", lambda *_args, **_kwargs: None
    )

    def receive(item, realtime_type, values):
        asyncio.run(
            manager._handle_message(
                json.dumps(
                    {
                        "trnm": "REAL",
                        "data": [
                            {"type": realtime_type, "item": item, "values": values}
                        ],
                    }
                )
            )
        )

    receive("425040_AL", "0B", {"10": "9830", "15": "+1"})
    receive("425040_AL", "0D", {"41": "9840", "61": "100", "51": "9830", "71": "100"})
    before = manager.get_latest_data("425040")
    receive("425040", "0B", {"10": "9900", "15": "+1"})
    receive("425040", "0D", {"41": "9910", "61": "100", "51": "9900", "71": "100"})
    after = manager.get_latest_data("425040")
    after.pop("market_data_health", None)
    before.pop("market_data_health", None)
    assert after == before
    assert before["last_realtime_type_item"]["0B"] == "425040_AL"
    assert before["last_realtime_type_item"]["0D"] == "425040_AL"
    assert before["last_realtime_type_actual_execution_venue"]["0B"] == "UNKNOWN"
    assert manager._micro_reversion_observation_route_data["425040"]["curr"] == 9900
    from src.engine.scalping.ai_market_snapshot import (
        _venue_consistency,
        realtime_type_provenance,
    )

    now = max(before["last_realtime_type_ts"].values())
    valid, blockers = _venue_consistency(
        stock_code="425040",
        venue="KRX_NXT_INTEGRATED",
        session="krx_nxt_aftermarket",
        provenance=realtime_type_provenance(before, now_ts=now),
        now_epoch=now,
    )
    assert valid and blockers == []
    isolated = manager._micro_reversion_observation_route_data["425040"]
    now = max(isolated["last_realtime_type_ts"].values())
    valid, blockers = _venue_consistency(
        stock_code="425040",
        venue="KRX_NXT_INTEGRATED",
        session="krx_nxt_aftermarket",
        provenance=realtime_type_provenance(isolated, now_ts=now),
        now_epoch=now,
    )
    assert not valid and "integrated_market_data_route_required" in blockers


def test_runtime_route_reconcile_promotes_existing_observation_al(monkeypatch):
    manager = KiwoomWSManager("test-token")
    manager.websocket = _FakeWS([])
    manager._session_ready.set()
    manager.subscribed_codes.add("425040")
    manager._implicit_runtime_route_codes.add("425040")
    manager._registered_items_by_code["425040"] = ("425040", "425040_AL")
    manager._micro_reversion_observation_only_items.add("425040_AL")
    monkeypatch.setattr(manager, "_integrated_aftermarket_route_required", lambda: True)
    asyncio.run(manager._reconcile_integrated_runtime_routes())
    assert "425040_AL" not in manager._micro_reversion_observation_only_items
    assert manager._runtime_primary_items_by_code["425040"] == "425040_AL"
    rows = json.loads(manager.websocket.sent[0])["data"]
    assert {typ for row in rows for typ in row["type"]} == {"0B", "0D"}
    assert all(row["item"] == ["425040_AL"] for row in rows)


def test_explicit_nxt_subscription_is_not_auto_migrated(monkeypatch):
    manager = KiwoomWSManager("test-token")
    manager.websocket = _FakeWS([])
    manager._session_ready.set()
    monkeypatch.setattr(manager, "_integrated_aftermarket_route_required", lambda: True)
    asyncio.run(manager._send_reg(["425040_NX"]))
    asyncio.run(manager._reconcile_integrated_runtime_routes())
    assert len(manager.websocket.sent) == 1
    assert manager._implicit_runtime_route_codes == set()
    assert manager._registered_items_by_code["425040"] == ("425040_NX",)


def test_runtime_route_reconcile_does_not_block_receive_loop(monkeypatch):
    manager = KiwoomWSManager("test-token")

    async def blocked_reconcile():
        await asyncio.Event().wait()

    monkeypatch.setattr(
        manager, "_reconcile_integrated_runtime_routes", blocked_reconcile
    )

    async def exercise():
        manager._schedule_integrated_runtime_route_reconcile()
        task = manager._runtime_route_reconcile_task
        await asyncio.sleep(0)
        manager._schedule_integrated_runtime_route_reconcile()
        assert manager._runtime_route_reconcile_task is task
        assert not task.done()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(exercise())


def test_plain_observation_only_registration_keeps_exact_route(monkeypatch):
    manager = KiwoomWSManager("test-token")
    manager.websocket = _FakeWS([])
    manager._session_ready.set()
    monkeypatch.setattr(manager, "_integrated_aftermarket_route_required", lambda: True)
    monkeypatch.setattr(
        "src.utils.kiwoom_utils.get_effective_kiwoom_code", lambda _code: "425040_AL"
    )
    asyncio.run(
        manager._send_reg(
            ["425040"], realtime_types=("0B", "0D"), observation_only=True
        )
    )
    assert json.loads(manager.websocket.sent[0])["data"][0]["item"] == ["425040"]
    assert manager._implicit_runtime_route_codes == set()
    assert manager._runtime_primary_items_by_code == {}


def test_runtime_route_reconcile_rejects_changed_connection_receipt(monkeypatch):
    manager = KiwoomWSManager("test-token")
    manager._session_ready.set()
    manager.subscribed_codes.add("425040")
    manager._implicit_runtime_route_codes.add("425040")
    manager._registered_items_by_code["425040"] = ("425040",)
    monkeypatch.setattr(manager, "_integrated_aftermarket_route_required", lambda: True)

    class ChangingWS(_FakeWS):
        async def send(self, payload):
            await super().send(payload)
            manager.websocket = _FakeWS([])

    manager.websocket = ChangingWS([])
    asyncio.run(manager._reconcile_integrated_runtime_routes())
    assert manager._runtime_primary_items_by_code == {}
    assert manager._registered_items_by_code["425040"] == ("425040",)


def test_login_success_message_helpers():
    success = {"trnm": "LOGIN", "return_code": 0}
    failure = {"trnm": "LOGIN", "return_code": 100}

    assert KiwoomWSManager._is_login_success_message(success) is True
    assert KiwoomWSManager._is_login_failure_message(success) is False
    assert KiwoomWSManager._is_login_success_message(failure) is False
    assert KiwoomWSManager._is_login_failure_message(failure) is True


@pytest.mark.parametrize(
    (
        "raw_state",
        "state_event",
        "state_market_scope",
        "normalized_state",
        "entry_state_usable",
    ),
    [
        ("0", "KRX_PREOPEN", "KRX", "CLOSED", False),
        ("3", "KRX_OPEN", "KRX", "OPEN", True),
        ("2", "KRX_CLOSING_CALL_AUCTION_NOTICE", "KRX", "CALL_AUCTION", False),
        ("4", "KRX_MARKET_CLOSE", "KRX", "CLOSED", False),
        ("8", "KRX_REGULAR_MARKET_CLOSE", "KRX", "CLOSED", False),
        ("9", "ALL_MARKETS_CLOSE", "ALL", "CLOSED", False),
        ("a", "KRX_AFTER_HOURS_CLOSING_PRICE_OPEN", "KRX", "OPEN", True),
        ("b", "KRX_AFTER_HOURS_CLOSING_PRICE_CLOSE", "KRX", "CLOSED", False),
        ("c", "KRX_AFTER_HOURS_CALL_AUCTION_OPEN", "KRX", "CALL_AUCTION", False),
        ("d", "KRX_AFTER_HOURS_CALL_AUCTION_CLOSE", "KRX", "CLOSED", False),
        ("e", "DERIVATIVES_CLOSING_CALL_AUCTION_CLOSE", "DERIVATIVES", "CLOSED", False),
        ("o", "DERIVATIVES_MARKET_OPEN", "DERIVATIVES", "OPEN", False),
        (
            "s",
            "DERIVATIVES_CLOSING_CALL_AUCTION_OPEN",
            "DERIVATIVES",
            "CALL_AUCTION",
            False,
        ),
        ("P", "NXT_PREMARKET_OPEN", "NXT", "OPEN", True),
        ("Q", "NXT_PREMARKET_CLOSE", "NXT", "CLOSED", False),
        ("R", "NXT_MAIN_MARKET_OPEN", "NXT", "OPEN", True),
        ("S", "NXT_MAIN_MARKET_CLOSE", "NXT", "CLOSED", False),
        ("T", "NXT_AFTERMARKET_CALL_AUCTION_OPEN", "NXT", "CALL_AUCTION", False),
        ("U", "NXT_AFTERMARKET_OPEN", "NXT", "OPEN", True),
        ("V", "NXT_AFTERMARKET_CLOSE", "NXT", "CLOSED", False),
    ],
)
def test_official_0s_market_session_states_are_versioned_and_normalized(
    raw_state,
    state_event,
    state_market_scope,
    normalized_state,
    entry_state_usable,
):
    receipt = KiwoomWSManager._normalize_market_session_0s(raw_state)

    assert receipt == {
        "contract_version": "kiwoom_0s_market_operation_v1",
        "raw_state": raw_state,
        "state_event": state_event,
        "state_market_scope": state_market_scope,
        "normalized_state": normalized_state,
        "known": True,
        "entry_state_usable": entry_state_usable,
        "blocker": None,
    }


@pytest.mark.parametrize("raw_state", ["", "B", "W", "X", "VI"])
def test_unknown_0s_market_session_state_preserves_raw_and_fails_closed(raw_state):
    receipt = KiwoomWSManager._normalize_market_session_0s(raw_state)

    assert receipt["raw_state"] == raw_state
    assert receipt["state_event"] == "UNKNOWN"
    assert receipt["state_market_scope"] == "UNKNOWN"
    assert receipt["normalized_state"] == "UNKNOWN"
    assert receipt["known"] is False
    assert receipt["entry_state_usable"] is False
    assert receipt["blocker"] == "kiwoom_0s_state_unknown"


def test_official_0s_notification_without_actionable_state_fails_closed():
    receipt = KiwoomWSManager._normalize_market_session_0s("f")

    assert receipt["raw_state"] == "f"
    assert receipt["state_event"] == "DERIVATIVES_EARLY_OPEN_TIME_NOTICE"
    assert receipt["state_market_scope"] == "DERIVATIVES"
    assert receipt["normalized_state"] == "UNKNOWN"
    assert receipt["known"] is False
    assert receipt["entry_state_usable"] is False
    assert receipt["blocker"] == "kiwoom_0s_state_semantics_not_actionable"


def test_0s_handler_preserves_raw_route_and_packet_timestamps(monkeypatch):
    manager = KiwoomWSManager("test-token")
    events = []
    ingress = datetime(2026, 9, 14, 16, 0, 1, tzinfo=kiwoom_websocket.KST)
    monkeypatch.setattr(
        kiwoom_websocket,
        "append_market_session_event",
        lambda **kwargs: events.append(kwargs),
    )

    asyncio.run(
        manager._handle_message(
            json.dumps(
                {
                    "trnm": "REAL",
                    "data": [
                        {
                            "type": "0s",
                            "name": "장시작시간",
                            "item": "005930_AL",
                            "values": {
                                "20": "160001",
                                "214": "000059",
                                "215": "T",
                            },
                        }
                    ],
                }
            ),
            received_at=ingress,
        )
    )

    assert manager.market_session_state == "T"
    assert manager.market_session_state_event == "NXT_AFTERMARKET_CALL_AUCTION_OPEN"
    assert manager.market_session_state_normalized == "CALL_AUCTION"
    assert manager.market_session_state_known is True
    assert manager.market_session_state_entry_usable is False
    assert events[0]["event"] == {
        "source": "kiwoom_websocket_0s",
        "real_type": "0s",
        "name": "장시작시간",
        "item": "005930_AL",
        "market_data_route": "krx_nxt_integrated",
        "market_session_state": "T",
        "market_session_state_raw": "T",
        "market_session_remaining": "000059",
        "market_session_remaining_raw": "000059",
        "exchange_time_raw": "160001",
        "receive_timestamp": "2026-09-14T16:00:01.000+09:00",
        "receive_time_source": "websocket_packet_ingress",
        "market_session_state_contract_version": "kiwoom_0s_market_operation_v1",
        "market_session_state_event": "NXT_AFTERMARKET_CALL_AUCTION_OPEN",
        "market_session_state_market_scope": "NXT",
        "market_session_state_normalized": "CALL_AUCTION",
        "market_session_state_known": True,
        "market_session_state_entry_usable": False,
        "market_session_state_blocker": None,
        "raw_values": {"20": "160001", "214": "000059", "215": "T"},
    }


def test_raw_tick_snapshot_does_not_traverse_accumulated_history():
    class HistoryMustNotBeCopied:
        def __deepcopy__(self, memo):
            raise AssertionError("ingress copied accumulated history")

    manager = KiwoomWSManager("test-token")
    target = manager._ensure_target_defaults("005930")
    target["recent_trade_ticks"] = HistoryMustNotBeCopied()
    target["last_trade_tick"] = {"price": 100, "values": {"20": "100000"}}
    snapshot = manager._snapshot_target(target, include_history=False)
    assert "recent_trade_ticks" not in snapshot
    target["last_trade_tick"]["values"]["20"] = "100001"
    assert snapshot["last_trade_tick"]["values"]["20"] == "100000"


@pytest.mark.parametrize("realtime_type", ["0B", "0D"])
@pytest.mark.parametrize("trusted", [True, False])
def test_micro_observer_preserves_trusted_trade_ingress_clock(
    monkeypatch, realtime_type, trusted
):
    now = _epoch_at_090010()
    monkeypatch.setattr(kiwoom_websocket.time, "time", lambda: now)
    manager = KiwoomWSManager("test-token")
    manager.subscribed_codes = {"005930"}
    observed = []
    monkeypatch.setattr(manager, "_maybe_write_dashboard_snapshot", lambda: None)
    monkeypatch.setattr(
        manager,
        "_observe_micro_reversion_forward",
        lambda code, data, **kw: observed.append(data),
    )
    ingress = datetime.fromtimestamp(now - 2, tz=kiwoom_websocket.KST)
    monkeypatch.setattr(
        manager, "_micro_reversion_depth_capture_requested", lambda: True
    )
    asyncio.run(
        manager._handle_message(
            json.dumps(
                {
                    "trnm": "REAL",
                    "data": [
                        {
                            "type": realtime_type,
                            "item": "005930",
                            "values": {
                                "10": "10110",
                                "15": "+80",
                                "20": "090010",
                                "21": "090010",
                                "27": "10110",
                                "28": "10100",
                                "41": "10110",
                                "51": "10100",
                                "61": "100",
                                "71": "100",
                            },
                        }
                    ],
                }
            ),
            received_at=ingress if trusted else None,
        )
    )
    assert len(observed) == 1
    snapshot = observed[0]
    assert snapshot["micro_observer_packet_received_at_ms"] == (
        int((now - 2) * 1000) if trusted else None
    )
    tick = snapshot["last_trade_tick" if realtime_type == "0B" else "last_depth_tick"]
    assert tick["received_at_ms"] == int(
        (now - 2 if trusted and realtime_type == "0B" else now) * 1000
    )
    if realtime_type == "0B":
        assert tick["provider_trade_epoch"] == now
        assert tick["provider_trade_time_precision_ms"] == 1000
        assert (
            tick["provider_trade_date_basis"]
            == "local_receive_calendar_date_not_provider_date"
        )
        route = snapshot["realtime_type_snapshots_by_route"]["KRX|krx_only"]["0B"]
        latency = route["market_source_latency"]
        assert latency["packet_to_normalization_ms"] == (2000 if trusted else None)
        assert latency["provider_to_packet_ms"] == (-2000 if trusted else None)
        assert route["observed_epoch"] == (now - 2 if trusted else now)
    assert "micro_observer_packet_received_at_ms" not in manager.realtime_data["005930"]
    route = snapshot["realtime_type_snapshots_by_route"]["KRX|krx_only"][realtime_type]
    latency = route["market_source_latency"]
    assert (
        latency["item"] == "005930"
        and latency["route_sequence"] == route["route_sequence"]
    )
    assert latency["packet_to_normalization_ms"] == (2000 if trusted else None)
    if realtime_type == "0D":
        assert latency["provider_to_packet_ms"] is None
        assert "native_ingest_returned_epoch" not in latency


def test_raw_observation_is_lossless_while_dispatch_keeps_full_latest_history(
    monkeypatch,
):
    manager = KiwoomWSManager("test-token")
    target = manager._ensure_target_defaults("005930")
    observed = []
    monkeypatch.setattr(
        manager,
        "_observe_micro_reversion_forward",
        lambda code, data, *, realtime_type, snapshot_lock_held=False: observed.append(
            (realtime_type, data["curr"])
        ),
    )
    for kind, price in [("0B", 100), ("0D", 101), ("0B", 102)]:
        target["curr"] = price
        target["recent_trade_ticks"].appendleft({"price": price})
        manager._queue_tick_event(
            "005930",
            manager._snapshot_target(target, include_history=False),
            realtime_type=kind,
            observation_only=False,
            snapshot_target=target,
        )
    captured = []

    def publish(event, payload):
        captured.append(payload)
        assert event == "REALTIME_TICK_ARRIVED"
        assert "_snapshot_target" not in payload
        payload["data"]["recent_trade_ticks"][0]["price"] = -1
        manager._stop_event.set()

    manager.event_bus = SimpleNamespace(publish=publish)
    manager._dispatch_tick_events()
    assert observed == [("0B", 100), ("0D", 101), ("0B", 102)]
    assert len(captured) == 1
    assert captured[0]["data"]["curr"] == 102
    assert target["recent_trade_ticks"][0]["price"] == 102


def test_observation_only_event_never_enters_latest_state_dispatch(monkeypatch):
    manager = KiwoomWSManager("test-token")
    observed = []
    monkeypatch.setattr(
        manager,
        "_observe_micro_reversion_forward",
        lambda *a, **k: observed.append(k["realtime_type"]),
    )
    manager._queue_tick_event(
        "005930", {}, realtime_type="0D", observation_only=True, snapshot_target={}
    )
    assert observed == ["0D"]
    assert not manager._pending_tick_events


def test_shared_dashboard_snapshot_interval_defaults_to_one_second(monkeypatch):
    monkeypatch.delenv(
        kiwoom_websocket.WS_DASHBOARD_SNAPSHOT_INTERVAL_SEC_ENV, raising=False
    )
    assert kiwoom_websocket._ws_dashboard_snapshot_interval_sec() == 1.0

    monkeypatch.setenv(kiwoom_websocket.WS_DASHBOARD_SNAPSHOT_INTERVAL_SEC_ENV, "0.01")
    assert kiwoom_websocket._ws_dashboard_snapshot_interval_sec() == 0.25


def test_dashboard_snapshot_freezes_main_and_exact_route_views(monkeypatch):
    manager = KiwoomWSManager("test-token")
    clock = [1000.0]
    monkeypatch.setattr(kiwoom_websocket.time, "time", lambda: clock[0])
    main_target = manager._ensure_target_defaults("005930")
    main_target["curr"] = 70000
    main_target["last_realtime_type_ts"] = {"0D": 1000.4}
    route_target = dict(main_target)
    route_target["curr"] = 70010
    route_target["recent_trade_ticks"] = deque(
        [{"price": 70010, "volume": 2}], maxlen=120
    )
    manager._micro_reversion_observation_route_data["005930_NX"] = route_target
    captured = {}

    def _capture(
        realtime_data,
        *,
        observation_route_data,
        micro_reversion_registration_receipt,
        shared_transport_producer,
        now_ts,
    ):
        captured["main"] = realtime_data
        captured["routes"] = observation_route_data
        captured["receipt"] = micro_reversion_registration_receipt
        captured["now_ts"] = now_ts
        captured["producer"] = shared_transport_producer

    class _ImmediateThread:
        def __init__(self, *, target, name, daemon):
            self.target = target

        def start(self):
            clock[0] = 1000.5  # receipt arrived after worker launch was queued
            self.target()

    monkeypatch.setattr(kiwoom_websocket, "write_ws_snapshot", _capture)
    monkeypatch.setattr(kiwoom_websocket.threading, "Thread", _ImmediateThread)

    manager._maybe_write_dashboard_snapshot()
    main_target["curr"] = 1
    route_target["curr"] = 2
    route_target["recent_trade_ticks"].append({"price": 2, "volume": 1})

    assert captured["main"]["005930"]["curr"] == 70000
    assert (
        captured["producer"]["registration_basis"]
        == "local_sent_registry_not_broker_ack"
    )
    assert captured["routes"]["005930_NX"]["curr"] == 70010
    assert captured["routes"]["005930_NX"]["recent_trade_ticks"] == [
        {"price": 70010, "volume": 2}
    ]
    assert captured["receipt"] == {}
    assert captured["now_ts"] == 1000.5
    assert captured["main"]["005930"]["last_realtime_type_ts"]["0D"] == 1000.4
    assert manager._last_dashboard_snapshot_at == 1000.0  # throttle clock unchanged
    assert manager._dashboard_snapshot_write_inflight is False


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


def test_order_execution_carries_websocket_packet_ingress_timestamp():
    manager = KiwoomWSManager("test-token")
    packet_received_at = datetime(
        2026, 8, 25, 9, 0, 3, 456789, tzinfo=kiwoom_websocket.KST
    )

    asyncio.run(
        manager._handle_message(
            json.dumps(
                {
                    "trnm": "REAL",
                    "data": [
                        {
                            "type": "00",
                            "name": "주문체결",
                            "values": {
                                "9203": "1000001",
                                "9001": "A005930",
                                "913": "체결",
                                "900": "1",
                                "902": "0",
                                "903": "70000",
                                "905": "+매수",
                                "907": "2",
                                "908": "090003",
                                "909": "2000001",
                                "910": "70000",
                                "911": "1",
                                "914": "70000",
                                "915": "1",
                                "2134": "1",
                                "2135": "KRX",
                                "2136": "N",
                            },
                        }
                    ],
                }
            ),
            received_at=packet_received_at,
        )
    )

    queued = []
    while not manager._state_event_queue.empty():
        queued.append(manager._state_event_queue.get_nowait())
    execution_payload = next(
        payload for event_type, payload in queued if event_type == "ORDER_EXECUTED"
    )
    assert execution_payload["broker_execution_received_at"] == (
        packet_received_at.isoformat(timespec="microseconds")
    )
    assert execution_payload["broker_execution_receive_time_source"] == (
        "websocket_packet_ingress"
    )


@pytest.mark.parametrize(
    "received_at",
    [
        None,
        datetime(2026, 8, 25, 9, 0, 3, 456789),
        datetime(2026, 8, 25, 9, 0, 3, 456789, tzinfo=_OffsetlessTZ()),
    ],
    ids=["missing", "timezone_naive", "offsetless_tzinfo"],
)
def test_order_execution_without_aware_ingress_timestamp_is_never_trusted(
    received_at,
):
    manager = KiwoomWSManager("test-token")
    message = json.dumps(
        {
            "trnm": "REAL",
            "data": [
                {
                    "type": "00",
                    "name": "주문체결",
                    "values": {
                        "9203": "1000001",
                        "9001": "A005930",
                        "913": "체결",
                        "900": "1",
                        "902": "0",
                        "903": "70000",
                        "905": "+매수",
                        "907": "2",
                        "908": "090003",
                        "909": "2000001",
                        "910": "70000",
                        "911": "1",
                        "914": "70000",
                        "915": "1",
                        "2134": "1",
                        "2135": "KRX",
                        "2136": "N",
                    },
                }
            ],
        }
    )

    if received_at is None:
        asyncio.run(manager._handle_message(message))
    else:
        asyncio.run(manager._handle_message(message, received_at=received_at))

    queued = []
    while not manager._state_event_queue.empty():
        queued.append(manager._state_event_queue.get_nowait())
    execution_payload = next(
        payload for event_type, payload in queued if event_type == "ORDER_EXECUTED"
    )
    assert execution_payload["broker_execution_receive_time_source"] == (
        "handler_dispatch_fallback_not_packet_ingress"
    )
    assert execution_payload["broker_execution_receive_time_source"] != (
        "websocket_packet_ingress"
    )


def _epoch_at_090010():
    return datetime(2026, 7, 3, 9, 0, 10).timestamp()


def test_realtime_0b_stores_signed_trade_volume_primary_with_touch_provenance(
    monkeypatch,
):
    monkeypatch.setattr(kiwoom_websocket.time, "time", lambda: _epoch_at_090010())
    manager = KiwoomWSManager("test-token")
    manager.subscribed_codes = {"005930"}

    asyncio.run(
        manager._handle_message(
            json.dumps(
                {
                    "trnm": "REAL",
                    "data": [
                        {
                            "type": "0B",
                            "item": "005930",
                            "values": {
                                "10": "10110",
                                "12": "-1.25",
                                "18": "-9900",
                                "15": "+120",
                                "20": "090010",
                                "9081": "1",
                                "27": "10110",
                                "28": "10100",
                                "228": "135.5",
                            },
                        }
                    ],
                }
            )
        )
    )

    latest = manager.get_latest_data("005930")
    tick = latest["recent_trade_ticks"][0]
    assert tick["dir"] == "BUY"
    assert tick["aggressor_source"] == "kiwoom_0b_signed_trade_volume"
    assert tick["aggressor_quality"] == "signed_trade_volume_positive"
    assert tick["aggressor_quote_source"] == "0B_inline_best_quote"
    assert tick["aggressor_tick_sync"] is True
    assert tick["aggressor_cache_used"] is False
    assert tick["aggressor_tob_miss_count"] == 0
    assert tick["aggressor_backoff_active"] is False
    assert tick["aggressor_touch_side"] == "BUY"
    assert tick["aggressor_touch_source"] == "orderbook_touch"
    assert tick["aggressor_touch_quality"] == "touch_or_crossed_ask"
    assert tick["aggressor_touch_confirms_signed"] is True
    assert tick["aggressor_aux_side"] == "BUY"
    assert tick["aggressor_aux_source"] == "weighted_auxiliary_observation"
    assert tick["aggressor_aux_pressure_usable"] is False
    assert tick["aggressor_aux_raw_15"] == "+120"
    assert tick["signed_trade_volume"] == "+120"
    assert tick["best_ask"] == 10110
    assert tick["best_bid"] == 10100
    assert latest["last_trade_tick"]["price"] == 10110
    assert latest["last_trade_tick"]["exchange_time_raw"] == "090010"
    assert latest["last_trade_tick"]["exchange_code_9081"] == "1"


def test_signed_trade_volume_primary_classifies_without_orderbook_touch(monkeypatch):
    monkeypatch.setattr(kiwoom_websocket.time, "time", lambda: _epoch_at_090010())
    manager = KiwoomWSManager("test-token")
    manager.subscribed_codes = {"005930"}

    asyncio.run(
        manager._handle_message(
            json.dumps(
                {
                    "trnm": "REAL",
                    "data": [
                        {
                            "type": "0B",
                            "item": "005930",
                            "values": {
                                "10": "10110",
                                "15": "+80",
                                "20": "090010",
                                "27": "",
                                "28": "",
                            },
                        },
                    ],
                }
            )
        )
    )

    tick = manager.get_latest_data("005930")["recent_trade_ticks"][0]
    assert tick["dir"] == "BUY"
    assert tick["aggressor_side"] == "BUY"
    assert tick["aggressor_source"] == "kiwoom_0b_signed_trade_volume"
    assert tick["aggressor_quality"] == "signed_trade_volume_positive"
    assert tick["aggressor_touch_side"] == "UNKNOWN"
    assert tick["aggressor_touch_source"] == "missing_best_quote"
    assert tick["aggressor_touch_quality"] == "missing_best_quote"
    assert tick["aggressor_touch_confirms_signed"] is None
    assert tick["aggressor_aux_side"] == "BUY"
    assert tick["aggressor_aux_source"] == "weighted_auxiliary_observation"
    assert tick["aggressor_aux_quality"] == "signed_trade_volume_positive_auxiliary"
    assert tick["aggressor_aux_score"] == 3.0
    assert tick["aggressor_aux_pressure_usable"] is False


def test_recent_trade_ticks_are_partitioned_by_subscription_route(monkeypatch):
    monkeypatch.setattr(kiwoom_websocket.time, "time", lambda: _epoch_at_090010())
    manager = KiwoomWSManager("test-token")
    manager.subscribed_codes = {"005930"}

    for item, signed_volume in (("005930", "+10"), ("005930_AL", "+20")):
        asyncio.run(
            manager._handle_message(
                json.dumps(
                    {
                        "trnm": "REAL",
                        "data": [
                            {
                                "type": "0B",
                                "item": item,
                                "values": {
                                    "10": "10110",
                                    "15": signed_volume,
                                    "20": "090010",
                                    "27": "10110",
                                    "28": "10100",
                                },
                            }
                        ],
                    }
                )
            )
        )

    latest = manager.get_latest_data("005930")
    partitions = latest["recent_trade_ticks_by_route"]
    assert set(partitions) == {
        "KRX|krx_only",
        "_AL|krx_nxt_integrated",
    }
    assert partitions["KRX|krx_only"][0]["market_suffix"] == ""
    assert (
        partitions["_AL|krx_nxt_integrated"][0]["market_route"] == "krx_nxt_integrated"
    )


def test_signed_trade_volume_primary_records_orderbook_touch_conflict(monkeypatch):
    monkeypatch.setattr(kiwoom_websocket.time, "time", lambda: _epoch_at_090010())
    manager = KiwoomWSManager("test-token")
    manager.subscribed_codes = {"005930"}

    asyncio.run(
        manager._handle_message(
            json.dumps(
                {
                    "trnm": "REAL",
                    "data": [
                        {
                            "type": "0B",
                            "item": "005930",
                            "values": {
                                "10": "10100",
                                "15": "+80",
                                "20": "090010",
                                "27": "10110",
                                "28": "10100",
                            },
                        },
                    ],
                }
            )
        )
    )

    tick = manager.get_latest_data("005930")["recent_trade_ticks"][0]
    assert tick["dir"] == "BUY"
    assert tick["aggressor_source"] == "kiwoom_0b_signed_trade_volume"
    assert tick["aggressor_quality"] == "signed_trade_volume_positive"
    assert tick["aggressor_touch_side"] == "SELL"
    assert tick["aggressor_touch_source"] == "orderbook_touch"
    assert tick["aggressor_touch_quality"] == "touch_or_crossed_bid"
    assert tick["aggressor_touch_confirms_signed"] is False


def test_0b_auxiliary_fields_prefer_1313_and_use_trusted_tick_volume():
    parsed = KiwoomWSManager._parse_0b_auxiliary_fields(
        {"10": "+1000", "15": "+40", "1030": "20", "1031": "30", "1032": "60.0"},
        trade_price=1000,
    )
    assert parsed["buy_qty"] == 30
    assert parsed["sell_qty"] == 20
    assert parsed["trade_volume"] == 40
    assert parsed["trade_volume_source"] == "15_abs"
    assert parsed["trade_value"] == 40000
    assert parsed["trade_value_source"] == "calc_price_x_15_abs"
    assert parsed["trade_value_fallback_volume_source"] == "15_abs"
    assert parsed["split_qty_advisory_only"] is True
    assert parsed["split_qty_vs_15_mismatch"] is True
    assert parsed["split_qty_vs_15_delta"] == 10

    with_1313 = KiwoomWSManager._parse_0b_auxiliary_fields(
        {"10": "1000", "15": "+40", "1030": "20", "1031": "30", "1313": "123456"},
        trade_price=1000,
    )
    assert with_1313["trade_value"] == 123456
    assert with_1313["trade_value_source"] == "1313"
    assert with_1313["trade_value_fallback_volume_source"] == "none"


def test_0b_auxiliary_fields_fall_back_to_positive_cumulative_volume_delta():
    parsed = KiwoomWSManager._parse_0b_auxiliary_fields(
        {"10": "1000", "13": "107", "15": ""},
        trade_price=1000,
        previous_tick={"cum_volume": 100},
    )
    assert parsed["trade_volume"] == 7
    assert parsed["trade_volume_source"] == "13_delta"
    assert parsed["cum_volume_delta"] == 7
    assert parsed["trade_value"] == 7000
    assert parsed["trade_value_source"] == "calc_price_x_13_delta"

    unavailable = KiwoomWSManager._parse_0b_auxiliary_fields(
        {"10": "1000", "13": "107", "15": "", "1030": "20", "1031": "30"},
        trade_price=1000,
    )
    assert unavailable["trade_volume"] == 0
    assert unavailable["trade_volume_source"] == "unknown"
    assert unavailable["trade_value"] == 0
    assert unavailable["trade_value_source"] == "unknown"


def test_realtime_0b_logs_trade_value_fallback_and_volume_mismatch(monkeypatch):
    monkeypatch.setattr(kiwoom_websocket.time, "time", lambda: _epoch_at_090010())
    manager = KiwoomWSManager("test-token")
    manager.subscribed_codes = {"005930"}

    asyncio.run(
        manager._handle_message(
            json.dumps(
                {
                    "trnm": "REAL",
                    "data": [
                        {
                            "type": "0B",
                            "item": "005930",
                            "values": {
                                "10": "1000",
                                "15": "+40",
                                "20": "090010",
                                "27": "1000",
                                "28": "990",
                                "1030": "20",
                                "1031": "30",
                                "1032": "60.0",
                            },
                        },
                    ],
                }
            )
        )
    )

    latest = manager.get_latest_data("005930")
    tick = latest["recent_trade_ticks"][0]
    momentum = latest["strength_momentum_history"][0]
    assert tick["volume"] == 40
    assert tick["volume_source"] == "15_abs"
    assert tick["buyer_vol"] == 40
    assert tick["seller_vol"] == 0
    assert tick["buy_exec_cum_1031"] == 30
    assert tick["sell_exec_cum_1030"] == 20
    assert tick["tick_trade_value"] == 40000
    assert tick["tick_trade_value_source"] == "calc_price_x_15_abs"
    assert tick["tick_trade_value_fallback_volume_source"] == "15_abs"
    assert tick["trade_volume_1030_1031_vs_15_mismatch"] is True
    assert tick["trade_volume_1030_1031_vs_15_delta"] == 10
    assert latest["tick_trade_value"] == 40000
    assert latest["tick_trade_value_source"] == "calc_price_x_15_abs"
    assert latest["trade_volume_1030_1031_vs_15_mismatch"] is True
    assert latest["kiwoom_0b_aux_observed_count"] == 1
    assert latest["kiwoom_0b_1313_present_count"] == 0
    assert latest["kiwoom_0b_1313_missing_count"] == 1
    assert latest["kiwoom_0b_trade_value_source_counts"] == {"calc_price_x_15_abs": 1}
    assert latest["kiwoom_0b_trade_volume_source_counts"] == {"15_abs": 1}
    assert latest["kiwoom_0b_1030_1031_vs_15_evaluable_count"] == 1
    assert latest["kiwoom_0b_1030_1031_vs_15_mismatch_count"] == 1
    assert momentum["tick_value"] == 40000
    assert momentum["tick_value_source"] == "calc_price_x_15_abs"


def test_trade_auxiliary_score_uses_exec_imbalance_cum_volume_and_prev_price(
    monkeypatch,
):
    now = _epoch_at_090010()
    monkeypatch.setattr(kiwoom_websocket.time, "time", lambda: now)
    manager = KiwoomWSManager("test-token")
    manager.subscribed_codes = {"005930"}

    asyncio.run(
        manager._handle_message(
            json.dumps(
                {
                    "trnm": "REAL",
                    "data": [
                        {
                            "type": "0B",
                            "item": "005930",
                            "values": {
                                "10": "10000",
                                "15": "+10",
                                "20": "090009",
                                "27": "",
                                "28": "",
                                "13": "1000",
                                "1031": "10",
                                "228": "100",
                            },
                        },
                        {
                            "type": "0B",
                            "item": "005930",
                            "values": {
                                "10": "10005",
                                "15": "+40",
                                "20": "090010",
                                "27": "",
                                "28": "",
                                "13": "1040",
                                "1030": "5",
                                "1031": "35",
                                "228": "120",
                            },
                        },
                    ],
                }
            )
        )
    )

    tick = manager.get_latest_data("005930")["recent_trade_ticks"][0]
    assert tick["dir"] == "BUY"
    assert tick["aggressor_source"] == "kiwoom_0b_signed_trade_volume"
    assert tick["aggressor_quality"] == "signed_trade_volume_positive"
    assert tick["aggressor_touch_source"] == "missing_best_quote"
    assert tick["aggressor_aux_side"] == "BUY"
    assert tick["aggressor_aux_quality"] == "weighted_auxiliary_observation"
    assert tick["aggressor_aux_pressure_usable"] is False
    assert tick["aggressor_aux_score"] > 1.5
    assert "exec_qty_imbalance" in tick["aggressor_aux_reason"]
    assert tick["aggressor_aux_components"]["cum_volume_delta"] == 40
    assert tick["aggressor_aux_components"]["prev_trade_price"] == 10000


def test_realtime_0b_uses_fresh_synced_top_of_book_cache(monkeypatch):
    now = _epoch_at_090010()
    monkeypatch.setattr(kiwoom_websocket.time, "time", lambda: now)
    manager = KiwoomWSManager("test-token")
    manager.subscribed_codes = {"005930"}

    asyncio.run(
        manager._handle_message(
            json.dumps(
                {
                    "trnm": "REAL",
                    "data": [
                        {
                            "type": "0D",
                            "item": "005930",
                            "values": {
                                "41": "10110",
                                "61": "100",
                                "51": "10100",
                                "71": "200",
                            },
                        },
                        {
                            "type": "0B",
                            "item": "005930",
                            "values": {
                                "10": "10100",
                                "15": "-80",
                                "20": "090010",
                                "27": "0",
                                "28": "",
                            },
                        },
                    ],
                }
            )
        )
    )

    tick = manager.get_latest_data("005930")["recent_trade_ticks"][0]
    assert tick["dir"] == "SELL"
    assert tick["aggressor_source"] == "kiwoom_0b_signed_trade_volume"
    assert tick["aggressor_quality"] == "signed_trade_volume_negative"
    assert tick["aggressor_cache_used"] is True
    assert tick["aggressor_quote_source"] == "cached_top_of_book_ttl"
    assert tick["aggressor_quote_age_ms"] == 0
    assert tick["aggressor_tick_sync"] is True
    assert tick["aggressor_touch_side"] == "SELL"
    assert tick["aggressor_touch_source"] == "cached_orderbook_touch"
    assert tick["aggressor_touch_quality"] == "cached_quote_touch_or_crossed_bid"
    assert tick["aggressor_touch_confirms_signed"] is True
    assert tick["best_ask"] == 10110
    assert tick["best_bid"] == 10100


def test_realtime_0d_updates_micro_estimator_store(monkeypatch):
    now = _epoch_at_090010()
    monkeypatch.setattr(kiwoom_websocket.time, "time", lambda: now)
    store = kiwoom_websocket.MICRO_ESTIMATOR_STORE.__class__()
    monkeypatch.setattr(kiwoom_websocket, "MICRO_ESTIMATOR_STORE", store)
    manager = KiwoomWSManager("test-token")
    manager.subscribed_codes = {"005930"}

    asyncio.run(
        manager._handle_message(
            json.dumps(
                {
                    "trnm": "REAL",
                    "data": [
                        {
                            "type": "0D",
                            "item": "005930",
                            "values": {
                                "41": "10110",
                                "61": "100",
                                "51": "10100",
                                "71": "100",
                            },
                        },
                        {
                            "type": "0D",
                            "item": "005930",
                            "values": {
                                "41": "10110",
                                "61": "1",
                                "51": "10101",
                                "71": "1000",
                            },
                        },
                    ],
                }
            )
        )
    )

    snapshot = store.snapshot("005930", now_ts=now)
    latest = manager.get_latest_data("005930")
    assert snapshot["source_state"] == "fresh_ws_order_flow_delta"
    assert snapshot["true_ofi_sample_count"] == 1
    assert snapshot["sample_count"] == 2
    assert snapshot["confidence"] >= 0.80
    assert latest["micro_estimator_ws_observation_source"] == "0D_orderbook"
    assert latest["micro_estimator_ws_observation_true_ofi_sample_count"] == 1


def test_0b_cached_top_of_book_age_is_not_refreshed_by_cache_use():
    now = _epoch_at_090010()
    manager = KiwoomWSManager("test-token")
    cache_ts_ms = int(now * 1000)
    manager._update_tob_cache(
        "005930", best_ask=10110, best_bid=10100, now_ms=cache_ts_ms
    )

    first = manager._resolve_0b_touch_quote(
        "005930",
        inline_best_ask=0,
        inline_best_bid=0,
        tick_time="090010",
        received_ts=now + 0.1,
    )
    second = manager._resolve_0b_touch_quote(
        "005930",
        inline_best_ask=0,
        inline_best_bid=0,
        tick_time="090010",
        received_ts=now + 0.35,
    )

    assert first["cache_used"] is True
    assert first["quote_age_ms"] == 100
    assert second["cache_used"] is False
    assert second["quote_age_ms"] == 350
    assert second["quote_source"] == "missing_best_quote"
    assert second["tob_miss_count"] == 1
    assert second["backoff_active"] is True
    assert manager._get_tob_cache("005930")["ts_ms"] == cache_ts_ms


def test_realtime_0b_rejects_stale_or_unsynced_top_of_book_cache(monkeypatch):
    now = _epoch_at_090010() + 0.1
    monkeypatch.setattr(kiwoom_websocket.time, "time", lambda: now)
    manager = KiwoomWSManager("test-token")
    manager.subscribed_codes = {"005930"}
    manager._update_tob_cache(
        "005930",
        best_ask=10110,
        best_bid=10100,
        now_ms=int((now - 0.1) * 1000),
    )

    asyncio.run(
        manager._handle_message(
            json.dumps(
                {
                    "trnm": "REAL",
                    "data": [
                        {
                            "type": "0B",
                            "item": "005930",
                            "values": {
                                "10": "10110",
                                "15": "+80",
                                "20": "090008",
                                "27": "",
                                "28": "",
                            },
                        },
                    ],
                }
            )
        )
    )

    tick = manager.get_latest_data("005930")["recent_trade_ticks"][0]
    assert tick["dir"] == "BUY"
    assert tick["aggressor_source"] == "kiwoom_0b_signed_trade_volume"
    assert tick["aggressor_quality"] == "signed_trade_volume_positive"
    assert tick["aggressor_cache_used"] is False
    assert tick["aggressor_tick_sync"] is False
    assert tick["aggressor_tob_miss_count"] == 1
    assert tick["aggressor_backoff_active"] is True
    assert tick["aggressor_touch_side"] == "UNKNOWN"
    assert tick["aggressor_touch_source"] == "missing_best_quote"


def test_realtime_0b_partial_inline_quote_keeps_signed_primary_without_cache(
    monkeypatch,
):
    monkeypatch.setattr(kiwoom_websocket.time, "time", lambda: _epoch_at_090010())
    manager = KiwoomWSManager("test-token")
    manager.subscribed_codes = {"005930"}

    asyncio.run(
        manager._handle_message(
            json.dumps(
                {
                    "trnm": "REAL",
                    "data": [
                        {
                            "type": "0B",
                            "item": "005930",
                            "values": {
                                "10": "10110",
                                "15": "+80",
                                "20": "090010",
                                "27": "10110",
                                "28": "",
                            },
                        },
                    ],
                }
            )
        )
    )

    tick = manager.get_latest_data("005930")["recent_trade_ticks"][0]
    assert tick["dir"] == "BUY"
    assert tick["aggressor_source"] == "kiwoom_0b_signed_trade_volume"
    assert tick["aggressor_quality"] == "signed_trade_volume_positive"
    assert tick["aggressor_quote_source"] == "partial_inline_best_quote"
    assert tick["aggressor_cache_used"] is False
    assert tick["aggressor_tick_sync"] is True
    assert tick["aggressor_tob_miss_count"] == 1
    assert tick["aggressor_backoff_active"] is True
    assert tick["aggressor_touch_side"] == "UNKNOWN"
    assert tick["aggressor_touch_source"] == "missing_best_quote"
    assert tick["aggressor_touch_quality"] == "missing_best_quote"
    assert tick["best_ask"] == 10110
    assert tick["best_bid"] == 0


def test_realtime_0b_partial_inline_quote_uses_fresh_missing_side_cache(monkeypatch):
    now = _epoch_at_090010()
    monkeypatch.setattr(kiwoom_websocket.time, "time", lambda: now)
    manager = KiwoomWSManager("test-token")
    manager.subscribed_codes = {"005930"}
    manager._update_tob_cache(
        "005930",
        best_ask=10120,
        best_bid=10100,
        now_ms=int((now - 0.1) * 1000),
    )

    asyncio.run(
        manager._handle_message(
            json.dumps(
                {
                    "trnm": "REAL",
                    "data": [
                        {
                            "type": "0B",
                            "item": "005930",
                            "values": {
                                "10": "10110",
                                "15": "+80",
                                "20": "090010",
                                "27": "10110",
                                "28": "",
                            },
                        },
                    ],
                }
            )
        )
    )

    tick = manager.get_latest_data("005930")["recent_trade_ticks"][0]
    assert tick["dir"] == "BUY"
    assert tick["aggressor_source"] == "kiwoom_0b_signed_trade_volume"
    assert tick["aggressor_quality"] == "signed_trade_volume_positive"
    assert tick["aggressor_quote_source"] == "cached_top_of_book_ttl"
    assert tick["aggressor_cache_used"] is True
    assert tick["aggressor_tick_sync"] is True
    assert tick["aggressor_tob_miss_count"] == 0
    assert tick["aggressor_backoff_active"] is False
    assert tick["aggressor_touch_side"] == "BUY"
    assert tick["aggressor_touch_source"] == "cached_orderbook_touch"
    assert tick["aggressor_touch_quality"] == "cached_quote_touch_or_crossed_ask"
    assert tick["aggressor_touch_confirms_signed"] is True
    assert tick["best_ask"] == 10110
    assert tick["best_bid"] == 10100


def test_realtime_0b_incomplete_cache_does_not_create_cached_touch(monkeypatch):
    now = _epoch_at_090010()
    monkeypatch.setattr(kiwoom_websocket.time, "time", lambda: now)
    manager = KiwoomWSManager("test-token")
    manager.subscribed_codes = {"005930"}
    manager._update_tob_cache(
        "005930",
        best_ask=10110,
        best_bid=0,
        now_ms=int((now - 0.1) * 1000),
    )

    asyncio.run(
        manager._handle_message(
            json.dumps(
                {
                    "trnm": "REAL",
                    "data": [
                        {
                            "type": "0B",
                            "item": "005930",
                            "values": {
                                "10": "10110",
                                "15": "+80",
                                "20": "090010",
                                "27": "",
                                "28": "",
                            },
                        },
                    ],
                }
            )
        )
    )

    tick = manager.get_latest_data("005930")["recent_trade_ticks"][0]
    assert tick["dir"] == "BUY"
    assert tick["aggressor_source"] == "kiwoom_0b_signed_trade_volume"
    assert tick["aggressor_quality"] == "signed_trade_volume_positive"
    assert tick["aggressor_quote_source"] == "missing_best_quote"
    assert tick["aggressor_cache_used"] is False
    assert tick["aggressor_tob_miss_count"] == 1
    assert tick["aggressor_touch_side"] == "UNKNOWN"
    assert tick["aggressor_touch_source"] == "missing_best_quote"
    assert tick["aggressor_touch_quality"] == "missing_best_quote"
    assert tick["best_ask"] == 10110
    assert tick["best_bid"] == 0


def test_await_login_ack_raises_on_login_failure():
    manager = KiwoomWSManager("test-token")
    collector = _RecordingTransportEpochCollector()
    manager._micro_reversion_forward_collector = collector
    fake_ws = _FakeWS(
        [
            json.dumps(
                {"trnm": "LOGIN", "return_code": 100013, "return_msg": "login pending"}
            ),
        ]
    )

    with pytest.raises(RuntimeError):
        asyncio.run(manager._await_login_ack(fake_ws, timeout_sec=1.0))

    assert collector.epochs == []


def test_post_login_bootstrap_skips_condition_list_by_default(monkeypatch):
    monkeypatch.delenv("KORSTOCKSCAN_WS_CONDITION_SEARCH_ENABLED", raising=False)
    manager = KiwoomWSManager("test-token")
    collector = _RecordingTransportEpochCollector()
    manager._micro_reversion_forward_collector = collector
    fake_ws = _FakeWS([])
    manager.websocket = fake_ws

    asyncio.run(manager._send_post_login_bootstrap())

    sent = [json.loads(payload) for payload in fake_ws.sent]
    assert not any(payload.get("trnm") == "CNSRLST" for payload in sent)
    assert manager._session_ready.is_set()
    assert collector.epochs == []


def test_zero_base_bootstrap_skips_condition_list_when_swing_off(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_ZERO_BASE_SCANNER_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_WS_CONDITION_SEARCH_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_SWING_REAL_WATCHING_ENABLED", "false")
    manager = KiwoomWSManager("test-token")
    fake_ws = _FakeWS([])
    manager.websocket = fake_ws
    asyncio.run(manager._send_post_login_bootstrap())
    assert not any(
        json.loads(payload).get("trnm") == "CNSRLST" for payload in fake_ws.sent
    )


def test_post_login_bootstrap_restores_symbols_after_readiness_boundary(monkeypatch):
    monkeypatch.delenv("KORSTOCKSCAN_WS_CONDITION_SEARCH_ENABLED", raising=False)
    manager = KiwoomWSManager("test-token")
    boundary_order = []
    collector = _RecordingTransportEpochCollector(boundary_order)
    manager._micro_reversion_forward_collector = collector
    fake_ws = _FakeWS([])
    manager.websocket = fake_ws
    manager.is_reconnected = True
    manager.subscribed_codes.add("005930")
    manager._registered_items_by_code["005930"] = (
        "005930",
        "005930_NX",
        "005930_AL",
    )
    original_enqueue = manager._enqueue_state_event

    def record_enqueue(event_type, payload):
        boundary_order.append(event_type)
        return original_enqueue(event_type, payload)

    manager._enqueue_state_event = record_enqueue

    asyncio.run(manager._send_post_login_bootstrap())

    sent = [json.loads(payload) for payload in fake_ws.sent]
    symbol_regs = [
        payload
        for payload in sent
        if payload.get("trnm") == "REG"
        and any(
            any(str(item).startswith("005930") for item in row.get("item", []))
            for row in payload.get("data", [])
        )
    ]
    assert manager._session_ready.is_set()
    assert len(symbol_regs) == 1
    assert symbol_regs[0]["refresh"] == "1"
    restored_items = {
        item for row in symbol_regs[0]["data"] for item in row.get("item", [])
    }
    assert restored_items == {"005930", "005930_NX", "005930_AL"}
    assert KiwoomWSManager._ws_item_route("005930") == "krx_only"
    assert KiwoomWSManager._ws_item_route("005930_NX") == "nxt_only"
    assert KiwoomWSManager._ws_item_route("005930_AL") == "krx_nxt_integrated"
    assert KiwoomWSManager._ws_item_actual_execution_venue("005930_AL") == "UNKNOWN"
    assert collector.epochs == [1_000]
    assert boundary_order[:2] == ["transport_epoch", "WS_RECONNECTED"]


def test_reconnect_epoch_failure_schedules_cleanup_without_blocking_bootstrap(
    monkeypatch,
):
    monkeypatch.delenv("KORSTOCKSCAN_WS_CONDITION_SEARCH_ENABLED", raising=False)
    manager = KiwoomWSManager("test-token")
    manager.websocket = _FakeWS([])
    manager.is_reconnected = True

    class BrokenCollector:
        def begin_transport_epoch(self):
            raise RuntimeError("synthetic epoch failure")

    manager._micro_reversion_forward_collector = BrokenCollector()
    scheduled = []
    close_calls = []

    class DeferredThread:
        def __init__(self, *, target, name, daemon):
            assert name == "micro-reversion-epoch-failure-close"
            assert daemon is True
            self.target = target

        def start(self):
            scheduled.append(self.target)

    monkeypatch.setattr(kiwoom_websocket.threading, "Thread", DeferredThread)
    monkeypatch.setattr(
        manager,
        "_close_micro_reversion_forward_collector",
        lambda: close_calls.append(True),
    )

    asyncio.run(manager._send_post_login_bootstrap())

    assert manager._session_ready.is_set()
    assert manager._micro_reversion_forward_collector_stop_reason == (
        "transport_epoch_failure:RuntimeError"
    )
    assert len(scheduled) == 1
    assert close_calls == []
    scheduled[0]()
    assert close_calls == [True]


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


def test_zero_base_mode_subscribes_only_independent_swing_condition(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_ZERO_BASE_SCANNER_ENABLED", "true")
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
                        {"seq": "2", "name": "kospi_short_swing_01"},
                    ],
                }
            )
        )
    )
    assert [json.loads(payload)["seq"] for payload in fake_ws.sent] == ["2"]
    assert manager.condition_dict == {"2": "kospi_short_swing_01"}


def test_retired_vcp_s15_conditions_are_not_subscribed(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_WS_CONDITION_SEARCH_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_SWING_REAL_WATCHING_ENABLED", "true")

    async def no_sleep(*args, **kwargs):
        return None

    monkeypatch.setattr(kiwoom_websocket.asyncio, "sleep", no_sleep)
    manager = KiwoomWSManager("test-token")
    fake_ws = _FakeWS([])
    manager.websocket = fake_ws
    names = (
        "vcp_candid_01",
        "vcp_shooting_01",
        "vcp_shooting_next_01",
        "s15_scan_base",
        "s15_trigger_break",
        "s15_scan_base_01",
        "s15_trigger_break_01",
        "scalp_candid_normal_01",
        "kospi_short_swing_01",
    )
    asyncio.run(
        manager._handle_message(
            json.dumps(
                {
                    "trnm": "CNSRLST",
                    "data": [
                        {"seq": str(i), "name": name} for i, name in enumerate(names)
                    ],
                }
            )
        )
    )

    sent = [json.loads(payload) for payload in fake_ws.sent]
    assert [names[int(payload["seq"])] for payload in sent] == [
        "scalp_candid_normal_01",
        "kospi_short_swing_01",
    ]
    assert set(manager.condition_dict.values()) == {
        "scalp_candid_normal_01",
        "kospi_short_swing_01",
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


def test_scalp_condition_init_matches_blocked_outside_buy_window(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_WS_CONDITION_SEARCH_ENABLED", "true")
    monkeypatch.setattr(
        kiwoom_websocket, "is_scalping_buy_time_allowed", lambda now=None: False
    )
    monkeypatch.setattr(
        kiwoom_websocket,
        "scalping_buy_time_block_reason",
        lambda now=None: "outside_scalping_buy_window",
    )
    manager = KiwoomWSManager("test-token")
    manager.condition_dict = {"1": "scalp_candid_normal_01"}

    asyncio.run(
        manager._handle_message(
            json.dumps(
                {
                    "trnm": "CNSRREQ",
                    "seq": "1",
                    "data": [{"jmcode": "A005930"}],
                }
            )
        )
    )

    assert manager._state_event_queue.empty()


def test_scalp_condition_realtime_insert_blocked_outside_buy_window(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_WS_CONDITION_SEARCH_ENABLED", "true")
    monkeypatch.setattr(
        kiwoom_websocket, "is_scalping_buy_time_allowed", lambda now=None: False
    )
    monkeypatch.setattr(
        kiwoom_websocket,
        "scalping_buy_time_block_reason",
        lambda now=None: "outside_scalping_buy_window",
    )
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


def test_scalp_condition_deferred_insert_flushes_when_buy_window_opens(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_WS_CONDITION_SEARCH_ENABLED", "true")
    buy_window_open = {"value": False}
    monkeypatch.setattr(
        kiwoom_websocket,
        "is_scalping_buy_time_allowed",
        lambda now=None: buy_window_open["value"],
    )
    monkeypatch.setattr(
        kiwoom_websocket,
        "scalping_buy_time_block_reason",
        lambda now=None: "outside_scalping_buy_window",
    )
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
    assert len(manager._deferred_scalp_condition_matches) == 1

    buy_window_open["value"] = True
    asyncio.run(manager._handle_message(json.dumps({"trnm": "PING"})))

    event_name, payload = manager._state_event_queue.get_nowait()
    assert event_name == "CONDITION_MATCHED"
    assert payload["code"] == "005930"
    assert payload["type"] == "DEFERRED_BUY_WINDOW"
    assert manager._deferred_scalp_condition_matches == {}


def test_scalp_condition_defer_prewarm_registers_ws_once_without_entry_authority(
    monkeypatch,
):
    monkeypatch.setattr(
        kiwoom_websocket,
        "is_scalping_prewarm_time_allowed",
        lambda now=None: True,
    )
    manager = KiwoomWSManager("test-token")
    calls = []
    monkeypatch.setattr(
        manager,
        "execute_subscribe",
        lambda codes, **kwargs: calls.append((list(codes), kwargs)),
    )
    payload = {
        "code": "005930",
        "condition_name": "scalp_candid_normal_01",
    }

    manager._defer_scalp_condition_match(payload)
    manager._defer_scalp_condition_match(payload)

    assert calls == [
        (
            ["005930"],
            {
                "force": False,
                "source": "scanner_condition_buy_window_prewarm",
                "repair_cycle": "",
                "required_realtime_types": ("0B",),
            },
        )
    ]
    assert list(manager._scalp_condition_prewarm_codes) == ["005930"]
    assert len(manager._deferred_scalp_condition_matches) == 1


def test_scalp_condition_unmatched_drops_deferred_insert(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_WS_CONDITION_SEARCH_ENABLED", "true")
    buy_window_open = {"value": False}
    monkeypatch.setattr(
        kiwoom_websocket,
        "is_scalping_buy_time_allowed",
        lambda now=None: buy_window_open["value"],
    )
    monkeypatch.setattr(
        kiwoom_websocket,
        "scalping_buy_time_block_reason",
        lambda now=None: "outside_scalping_buy_window",
    )
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
    asyncio.run(
        manager._handle_message(
            json.dumps(
                {
                    "trnm": "REAL",
                    "data": [
                        {
                            "type": "02",
                            "name": "조건검색",
                            "values": {"841": "1", "9001": "A005930", "843": "D"},
                        }
                    ],
                }
            )
        )
    )
    manager._state_event_queue.get_nowait()

    buy_window_open["value"] = True
    asyncio.run(manager._handle_message(json.dumps({"trnm": "PING"})))

    assert manager._state_event_queue.empty()
    assert manager._deferred_scalp_condition_matches == {}


def test_scalp_condition_unmatched_after_window_open_drops_before_flush(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_WS_CONDITION_SEARCH_ENABLED", "true")
    buy_window_open = {"value": False}
    monkeypatch.setattr(
        kiwoom_websocket,
        "is_scalping_buy_time_allowed",
        lambda now=None: buy_window_open["value"],
    )
    monkeypatch.setattr(
        kiwoom_websocket,
        "scalping_buy_time_block_reason",
        lambda now=None: "outside_scalping_buy_window",
    )
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

    buy_window_open["value"] = True
    asyncio.run(
        manager._handle_message(
            json.dumps(
                {
                    "trnm": "REAL",
                    "data": [
                        {
                            "type": "02",
                            "name": "조건검색",
                            "values": {"841": "1", "9001": "A005930", "843": "D"},
                        }
                    ],
                }
            )
        )
    )

    event_name, payload = manager._state_event_queue.get_nowait()
    assert event_name == "CONDITION_UNMATCHED"
    assert payload["code"] == "005930"
    assert manager._state_event_queue.empty()
    assert manager._deferred_scalp_condition_matches == {}


def test_scalp_condition_unmatched_still_flows_outside_buy_window(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_WS_CONDITION_SEARCH_ENABLED", "true")
    monkeypatch.setattr(
        kiwoom_websocket, "is_scalping_buy_time_allowed", lambda now=None: False
    )
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
                            "values": {"841": "1", "9001": "A005930", "843": "D"},
                        }
                    ],
                }
            )
        )
    )

    event_name, payload = manager._state_event_queue.get_nowait()
    assert event_name == "CONDITION_UNMATCHED"
    assert payload["code"] == "005930"


def test_swing_condition_insert_not_blocked_by_scalping_buy_window(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_WS_CONDITION_SEARCH_ENABLED", "true")
    monkeypatch.setattr(
        kiwoom_websocket, "is_scalping_buy_time_allowed", lambda now=None: False
    )
    manager = KiwoomWSManager("test-token")
    manager.condition_dict = {"6": "kospi_short_swing_01"}

    asyncio.run(
        manager._handle_message(
            json.dumps(
                {
                    "trnm": "REAL",
                    "data": [
                        {
                            "type": "02",
                            "name": "조건검색",
                            "values": {"841": "6", "9001": "A005930", "843": "I"},
                        }
                    ],
                }
            )
        )
    )

    event_name, payload = manager._state_event_queue.get_nowait()
    assert event_name == "CONDITION_MATCHED"
    assert payload["code"] == "005930"
    assert payload["condition_name"] == "kospi_short_swing_01"


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
    target = manager.get_latest_data("005930")
    assert target["program_subscription_requested_at"] > 0
    assert target["program_missing_reason"] == ("program_0w_awaiting_first_observation")


def test_program_first_observation_closes_missing_provenance(monkeypatch):
    manager = KiwoomWSManager("test-token")
    manager.subscribed_codes.add("005930")
    target = manager._ensure_target_defaults("005930")
    target["program_subscription_requested_at"] = 1000.0
    target["program_missing_reason"] = "program_0w_awaiting_first_observation"
    monkeypatch.setattr(kiwoom_websocket.time, "time", lambda: 1001.25)
    monkeypatch.setattr(manager, "_maybe_write_dashboard_snapshot", lambda: None)

    asyncio.run(
        manager._handle_message(
            json.dumps(
                {
                    "trnm": "REAL",
                    "data": [
                        {
                            "type": "0w",
                            "item": "005930",
                            "values": {"206": "120", "210": "0"},
                        }
                    ],
                }
            )
        )
    )

    snapshot = manager.get_latest_data("005930")
    assert snapshot["program_first_observed_at"] == 1001.25
    assert snapshot["program_first_observed_latency_ms"] == 1250.0
    assert "program_missing_reason" not in snapshot
    assert snapshot["prog_buy_qty"] == 120
    assert snapshot["prog_net_qty"] == 0


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


def test_send_reg_preserves_explicit_nxt_only_item(monkeypatch):
    manager = KiwoomWSManager("test-token")
    fake_ws = _FakeWS([])
    manager.websocket = fake_ws
    manager._session_ready.set()

    monkeypatch.setattr(
        "src.utils.kiwoom_utils.get_effective_kiwoom_code",
        lambda code: code,
    )

    asyncio.run(manager._send_reg(["039490_NX"]))

    payload = json.loads(fake_ws.sent[0])
    assert payload["data"][0]["item"] == ["039490_NX"]
    assert manager.subscribed_codes == {"039490"}
    assert manager._registered_items_by_code["039490"] == ("039490_NX",)


def test_retired_feedback_cannot_send_source_only_reg(monkeypatch):
    manager = KiwoomWSManager("test-token")
    fake_ws = _FakeWS([])
    manager.websocket = fake_ws
    manager._session_ready.set()

    monkeypatch.setattr(
        "src.utils.kiwoom_utils.get_effective_kiwoom_code",
        lambda code: code,
    )

    asyncio.run(
        manager._send_reg(
            ["039490_NX"],
            realtime_types=("0B", "0D"),
            source="micro_reversion_collection_feedback",
        )
    )

    assert fake_ws.sent == []
    assert not manager._registered_items_by_code


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


def test_required_0b_receipt_is_not_masked_by_first_0d():
    manager = KiwoomWSManager("test-token")
    manager.subscribed_codes.add("000001")
    manager._required_realtime_types_by_code["000001"] = ("0B",)
    manager._persistent_repair_no_tick_attempts["000001"] = 2

    asyncio.run(
        manager._handle_message(
            json.dumps(
                {
                    "trnm": "REAL",
                    "data": [
                        {
                            "type": "0D",
                            "item": "000001",
                            "values": {"121": "100", "125": "100"},
                        }
                    ],
                }
            )
        )
    )

    row = manager.get_subscription_freshness_snapshot(["000001"])["rows"][0]
    assert row["required_realtime_types"] == ["0B"]
    assert row["required_realtime_received"] is False
    assert row["required_realtime_missing_types"] == ["0B"]
    assert row["repair_recommended"] is True
    assert row["repair_reason"] == "subscription_required_realtime_missing"
    assert "000001" not in manager._persistent_repair_no_tick_attempts

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

    row = manager.get_subscription_freshness_snapshot(["000001"])["rows"][0]
    assert row["required_realtime_received"] is True
    assert row["required_realtime_missing_types"] == []
    assert "000001" not in manager._persistent_repair_no_tick_attempts


def test_send_reg_respects_registered_item_budget(monkeypatch):
    manager = KiwoomWSManager("test-token")
    fake_ws = _FakeWS([])
    published = []
    manager.websocket = fake_ws
    manager._session_ready.set()
    manager.event_bus = SimpleNamespace(
        publish=lambda name, payload: published.append((name, payload))
    )

    monkeypatch.setenv("KORSTOCKSCAN_WS_MAX_REG_ITEMS", "1")
    monkeypatch.setattr(
        "src.utils.kiwoom_utils.get_effective_kiwoom_code", lambda code: code
    )

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

    monkeypatch.setattr(
        "src.utils.kiwoom_utils.get_effective_kiwoom_code", lambda code: code
    )

    asyncio.run(manager._send_reg(["000001"]))
    manager.execute_unsubscribe(["000001"])

    assert manager.subscribed_codes == set()
    assert manager._registered_items_by_code == {}
    assert "000001" not in manager.realtime_data


def test_execute_unsubscribe_returns_remove_send_completion(monkeypatch):
    from concurrent.futures import Future

    manager = KiwoomWSManager("test-token")
    manager.loop = SimpleNamespace(is_running=lambda: True)
    manager.subscribed_codes = {"000001"}
    manager._registered_items_by_code = {"000001": ("000001_AL",)}
    completion = Future()

    def schedule(coroutine, _loop):
        coroutine.close()
        return completion

    monkeypatch.setattr(
        kiwoom_websocket.asyncio,
        "run_coroutine_threadsafe",
        schedule,
    )
    assert manager.execute_unsubscribe(["000001"]) is completion
    completion.set_result(True)


def test_main_fixed_watch_registers_missing_exact_route_beside_existing_integrated_route(
    monkeypatch,
):
    manager = KiwoomWSManager("test-token")
    manager._started = True
    manager.loop = SimpleNamespace(is_running=lambda: True)
    manager.subscribed_codes.add("005930")
    manager._registered_items_by_code["005930"] = ("005930_AL",)
    manager._registered_item_epochs["005930_AL"] = manager._market_data_transport_epoch
    manager._registered_item_types["005930_AL"] = ("0B", "0D")
    captured = []

    def fake_send_reg(codes, **kwargs):
        captured.append((list(codes), kwargs))

        async def complete():
            return None

        return complete()

    def fake_schedule(coro, loop):
        coro.close()
        return type(
            "FakeFuture", (), {"add_done_callback": lambda self, callback: None}
        )()

    monkeypatch.setattr(manager, "_send_reg", fake_send_reg)
    monkeypatch.setattr(
        kiwoom_websocket.asyncio, "run_coroutine_threadsafe", fake_schedule
    )

    manager.execute_subscribe(
        ["005930_NX"],
        source="main_fixed_watch_admission",
        required_realtime_types=("0B", "0D"),
    )
    assert captured[0][0] == ["005930_NX"]
    assert captured[0][1]["replace_existing"] is False

    manager.execute_subscribe(
        ["005930_AL"],
        source="main_fixed_watch_admission",
        required_realtime_types=("0B", "0D"),
    )
    assert len(captured) == 1


def test_execute_subscribe_preserves_multiple_explicit_routes_for_same_symbol(
    monkeypatch,
):
    manager = KiwoomWSManager("test-token")
    manager._started = True
    manager.loop = SimpleNamespace(is_running=lambda: True)
    captured = []

    def fake_send_reg(codes, **kwargs):
        captured.append((list(codes), kwargs))

        async def complete():
            return None

        return complete()

    def fake_schedule(coro, loop):
        coro.close()
        return type(
            "FakeFuture", (), {"add_done_callback": lambda self, callback: None}
        )()

    monkeypatch.setattr(manager, "_send_reg", fake_send_reg)
    monkeypatch.setattr(
        kiwoom_websocket.asyncio, "run_coroutine_threadsafe", fake_schedule
    )

    manager.execute_subscribe(
        ["222222_NX", "222222_AL"],
        force=True,
        source="post_sell_exact_route_source_only_repair",
        remove_before_reg=False,
        realtime_types=("0B", "0D"),
        observation_only=True,
    )

    assert captured[0][0] == ["222222_NX", "222222_AL"]
    assert captured[0][1]["remove_before_reg"] is False
    assert captured[0][1]["realtime_types"] == ("0B", "0D")


def test_holding_repair_explicitly_requests_alternate_route(monkeypatch):
    manager = KiwoomWSManager("test-token")
    manager._started = True
    manager.loop = SimpleNamespace(is_running=lambda: True)
    captured = []

    def fake_send_reg(codes, **kwargs):
        captured.append((list(codes), kwargs))

        async def complete():
            return None

        return complete()

    def fake_schedule(coro, loop):
        coro.close()
        return type(
            "FakeFuture", (), {"add_done_callback": lambda self, callback: None}
        )()

    monkeypatch.setattr(manager, "_send_reg", fake_send_reg)
    monkeypatch.setattr(
        manager,
        "_filter_alternate_route_targets",
        lambda codes: (list(codes), []),
    )
    monkeypatch.setattr(
        kiwoom_websocket.asyncio, "run_coroutine_threadsafe", fake_schedule
    )

    manager.execute_subscribe(
        ["237690"],
        force=True,
        source="holding_ws_freshness_repair",
        repair_cycle="holding_ws_stale_or_missing",
        include_alternate_route=True,
    )

    assert captured[0][0] == ["237690"]
    assert captured[0][1]["include_alternate_route"] is True
    assert captured[0][1]["alternate_route_codes"] == ["237690"]


def test_reg_event_forwards_explicit_alternate_route_request(monkeypatch):
    manager = KiwoomWSManager("test-token")
    manager._started = True
    subscribed = []
    monkeypatch.setattr(
        manager,
        "execute_subscribe",
        lambda codes, **kwargs: subscribed.append((list(codes), kwargs)),
    )

    manager._handle_reg_event(
        {
            "codes": ["237690"],
            "source": "holding_ws_freshness_repair",
            "force": True,
            "repair_cycle": "holding_ws_stale_or_missing",
            "include_alternate_route": True,
        }
    )

    assert subscribed == [
        (
            ["237690"],
            {
                "force": True,
                "source": "holding_ws_freshness_repair",
                "repair_cycle": "holding_ws_stale_or_missing",
                "include_alternate_route": True,
            },
        )
    ]


def test_send_reg_preserves_existing_plain_and_supplemental_integrated_route(
    monkeypatch,
):
    manager = KiwoomWSManager("test-token")
    fake_ws = _FakeWS([])
    manager.websocket = fake_ws
    manager._session_ready.set()

    asyncio.run(
        manager._send_reg(
            ["222222", "222222_AL"],
            replace_existing=False,
            enforce_item_budget=True,
            source="post_sell_exact_route_source_only_repair",
            realtime_types=("0B", "0D"),
        )
    )

    sent = [json.loads(payload) for payload in fake_ws.sent]
    assert len(sent) == 1
    assert sent[0]["trnm"] == "REG"
    assert sent[0]["refresh"] == "1"
    assert sent[0]["data"] == [
        {"item": ["222222", "222222_AL"], "type": ["0B"]},
        {"item": ["222222", "222222_AL"], "type": ["0D"]},
    ]
    assert manager._registered_items_by_code["222222"] == (
        "222222",
        "222222_AL",
    )


def test_real_subscription_requests_source_only_route_replacement(monkeypatch):
    manager = KiwoomWSManager("test-token")
    manager._started = True
    manager.loop = SimpleNamespace(is_running=lambda: True)
    manager.subscribed_codes = {"111111"}
    manager._registered_items_by_code = {"111111": ("111111_NX",)}
    manager._micro_reversion_observation_items_by_code = {"111111": "111111_NX"}
    manager._micro_reversion_observation_only_codes = {"111111"}
    captured = []

    def fake_send_reg(codes, **kwargs):
        captured.append((list(codes), kwargs))

        async def complete():
            return None

        return complete()

    def fake_schedule(coro, loop):
        coro.close()
        return type(
            "FakeFuture", (), {"add_done_callback": lambda self, callback: None}
        )()

    monkeypatch.setattr(manager, "_send_reg", fake_send_reg)
    monkeypatch.setattr(
        kiwoom_websocket.asyncio, "run_coroutine_threadsafe", fake_schedule
    )

    manager.execute_subscribe(["111111"], source="scanner_runtime_target_attach")

    assert captured[0][0] == ["111111"]
    assert captured[0][1]["remove_before_reg"] is True
    assert manager.is_micro_reversion_observation_only_subscription("111111") is True


def test_successful_replacement_reg_releases_source_only_suppression(monkeypatch):
    manager = KiwoomWSManager("test-token")
    fake_ws = _FakeWS([])
    manager.websocket = fake_ws
    manager._session_ready.set()
    manager.subscribed_codes = {"111111"}
    manager._registered_items_by_code = {"111111": ("111111_NX",)}
    manager._micro_reversion_observation_only_codes = {"111111"}
    monkeypatch.setenv("KORSTOCKSCAN_WS_MAX_REG_ITEMS", "1")
    monkeypatch.setattr(
        "src.utils.kiwoom_utils.get_effective_kiwoom_code",
        lambda code: f"{code}_AL",
    )

    asyncio.run(
        manager._send_reg(
            ["111111"],
            remove_before_reg=True,
            enforce_item_budget=True,
            replacement_codes=("111111",),
            trading_promotion_codes=("111111",),
        )
    )

    sent = [json.loads(payload) for payload in fake_ws.sent]
    assert sent[0]["trnm"] == "REMOVE"
    assert sent[0]["data"][0]["item"] == ["111111_NX"]
    assert sent[1]["trnm"] == "REG"
    assert sent[1]["data"][0]["item"] == ["111111_AL"]
    assert manager.is_micro_reversion_observation_only_subscription("111111") is False


def test_failed_remove_keeps_source_only_suppression_and_blocks_promotion_reg(
    monkeypatch,
):
    manager = KiwoomWSManager("test-token")
    fake_ws = _FakeWS([])
    manager.websocket = fake_ws
    manager._session_ready.set()
    manager.subscribed_codes = {"111111"}
    manager._registered_items_by_code = {"111111": ("111111_NX",)}
    manager._micro_reversion_observation_only_codes = {"111111"}

    async def failed_remove(*args, **kwargs):
        return False

    monkeypatch.setattr(manager, "_send_remove_impl", failed_remove)
    monkeypatch.setattr(
        "src.utils.kiwoom_utils.get_effective_kiwoom_code",
        lambda code: f"{code}_AL",
    )

    asyncio.run(
        manager._send_reg(
            ["111111"],
            remove_before_reg=True,
            replacement_codes=("111111",),
            trading_promotion_codes=("111111",),
        )
    )

    assert fake_ws.sent == []
    assert manager.is_micro_reversion_observation_only_subscription("111111") is True


def test_samsung_non_pinned_route_still_consumes_trading_item_budget(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_WS_MAX_REG_ITEMS", "1")
    monkeypatch.setattr(
        "src.utils.kiwoom_utils.get_effective_kiwoom_code", lambda code: code
    )
    manager = KiwoomWSManager("test-token")
    fake_ws = _FakeWS([])
    manager.websocket = fake_ws
    manager._session_ready.set()

    asyncio.run(manager._send_reg(["000001"], enforce_item_budget=True))
    asyncio.run(manager._send_reg(["005930"], enforce_item_budget=True))

    assert manager.subscribed_codes == {"000001"}
    assert manager._registered_items_by_code == {"000001": ("000001",)}


def test_execute_unsubscribe_removes_samsung_non_pinned_route(monkeypatch):
    manager = KiwoomWSManager("test-token")
    manager.subscribed_codes = {"005930"}
    manager._registered_items_by_code = {"005930": ("005930",)}
    manager.realtime_data = {"005930": {"curr": 242_000}}

    manager.execute_unsubscribe(["005930"])

    assert manager.subscribed_codes == set()
    assert manager._registered_items_by_code == {}
    assert "005930" not in manager.realtime_data


def test_send_reg_preserves_refresh_for_all_batches(monkeypatch):
    manager = KiwoomWSManager("test-token")
    fake_ws = _FakeWS([])
    manager.websocket = fake_ws
    manager._session_ready.set()

    monkeypatch.setattr(
        kiwoom_websocket, "TRADING_RULES", SimpleNamespace(WS_REG_BATCH_SIZE=2)
    )
    monkeypatch.setattr(
        "src.utils.kiwoom_utils.get_effective_kiwoom_code", lambda code: code
    )

    asyncio.run(manager._send_reg(["000001", "000002", "000003", "000004", "000005"]))

    payloads = [json.loads(payload) for payload in fake_ws.sent]
    assert [payload["refresh"] for payload in payloads] == ["1", "1", "1"]
    assert [payload["data"][0]["item"] for payload in payloads] == [
        ["000001", "000002"],
        ["000003", "000004"],
        ["000005"],
    ]
    assert manager.subscribed_codes == {
        "000001",
        "000002",
        "000003",
        "000004",
        "000005",
    }


def test_send_reg_incremental_mode_does_not_replace_existing_group(monkeypatch):
    manager = KiwoomWSManager("test-token")
    fake_ws = _FakeWS([])
    manager.websocket = fake_ws
    manager._session_ready.set()

    monkeypatch.setattr(
        kiwoom_websocket, "TRADING_RULES", SimpleNamespace(WS_REG_BATCH_SIZE=2)
    )
    monkeypatch.setattr(
        "src.utils.kiwoom_utils.get_effective_kiwoom_code", lambda code: code
    )

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

    def fake_execute(
        codes, *, force=False, source="", repair_cycle="", required_realtime_types=None
    ):
        calls.append((codes, force, source, repair_cycle, required_realtime_types))

    monkeypatch.setattr(manager, "execute_subscribe", fake_execute)

    manager._handle_reg_event(
        {"codes": ["240810"], "source": "scanner_watching_ws_snapshot_recovery"}
    )

    assert calls == [
        (
            ["240810"],
            True,
            "scanner_watching_ws_snapshot_recovery",
            "",
            ("0B",),
        )
    ]


def test_command_ws_reg_persistent_repair_passes_repair_cycle(monkeypatch):
    manager = KiwoomWSManager("test-token")
    calls = []

    def fake_execute(
        codes, *, force=False, source="", repair_cycle="", required_realtime_types=None
    ):
        calls.append((codes, force, source, repair_cycle, required_realtime_types))

    monkeypatch.setattr(manager, "execute_subscribe", fake_execute)

    manager._handle_reg_event(
        {
            "codes": ["240810"],
            "source": "scanner_persistent_ws_gap_recovery",
            "force": True,
            "repair_cycle": "persistent_ws_gap",
        }
    )

    assert calls == [
        (
            ["240810"],
            True,
            "scanner_persistent_ws_gap_recovery",
            "persistent_ws_gap",
            ("0B",),
        )
    ]


def test_command_ws_reg_string_false_force_is_not_truthy(monkeypatch):
    manager = KiwoomWSManager("test-token")
    calls = []

    def fake_execute(
        codes, *, force=False, source="", repair_cycle="", required_realtime_types=None
    ):
        calls.append((codes, force, source, repair_cycle, required_realtime_types))

    monkeypatch.setattr(manager, "execute_subscribe", fake_execute)

    manager._handle_reg_event(
        {"codes": ["240810"], "source": "scanner_watch", "force": "false"}
    )

    assert calls == [(["240810"], False, "scanner_watch", "", ("0B",))]


def test_execute_subscribe_string_false_force_does_not_resubscribe(monkeypatch):
    manager = KiwoomWSManager("test-token")
    manager._started = True
    manager.loop = SimpleNamespace(is_running=lambda: True)
    manager.subscribed_codes.add("039490")
    scheduled = []

    def fake_schedule(coro, loop):
        coro.close()
        scheduled.append(coro)
        return type(
            "FakeFuture", (), {"add_done_callback": lambda self, callback: None}
        )()

    monkeypatch.setattr(
        kiwoom_websocket.asyncio, "run_coroutine_threadsafe", fake_schedule
    )

    manager.execute_subscribe(["039490"], force="false")

    assert scheduled == []


def test_recent_reg_filter_skips_non_force_duplicates(monkeypatch):
    manager = KiwoomWSManager("test-token")
    monkeypatch.setenv("KORSTOCKSCAN_WS_REG_RECENT_TTL_SEC", "20")
    monkeypatch.setattr(kiwoom_websocket.time, "time", lambda: 1000.0)

    allowed, skipped = manager._filter_recent_reg_targets(
        ["240810", "039490"], force=False
    )
    assert allowed == ["240810", "039490"]
    assert skipped == []

    allowed, skipped = manager._filter_recent_reg_targets(
        ["240810", "039490"], force=False
    )
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

    assert manager._filter_recent_reg_targets(["240810"], force=False) == (
        ["240810"],
        [],
    )
    now["value"] = 1021.0
    assert manager._filter_recent_reg_targets(["240810"], force=False) == (
        ["240810"],
        [],
    )


def test_alternate_route_filter_limits_codes_per_batch(monkeypatch):
    manager = KiwoomWSManager("test-token")
    monkeypatch.setenv("KORSTOCKSCAN_WS_ALTERNATE_ROUTE_MAX_CODES", "2")
    monkeypatch.setenv("KORSTOCKSCAN_WS_ALTERNATE_ROUTE_TTL_SEC", "180")
    monkeypatch.setattr(kiwoom_websocket.time, "time", lambda: 1000.0)

    allowed, skipped = manager._filter_alternate_route_targets(
        ["000001", "000002", "000003"]
    )

    assert allowed == ["000001", "000002"]
    assert skipped == ["000003"]


def test_alternate_route_filter_throttles_recent_codes(monkeypatch):
    manager = KiwoomWSManager("test-token")
    monkeypatch.setenv("KORSTOCKSCAN_WS_ALTERNATE_ROUTE_MAX_CODES", "2")
    monkeypatch.setenv("KORSTOCKSCAN_WS_ALTERNATE_ROUTE_TTL_SEC", "180")
    now = {"value": 1000.0}
    monkeypatch.setattr(kiwoom_websocket.time, "time", lambda: now["value"])

    assert manager._filter_alternate_route_targets(["000001", "000002"]) == (
        ["000001", "000002"],
        [],
    )
    assert manager._filter_alternate_route_targets(["000001", "000003"]) == (
        ["000003"],
        ["000001"],
    )
    now["value"] = 1181.0
    assert manager._filter_alternate_route_targets(["000001"]) == (["000001"], [])


def test_send_reg_applies_alternate_only_to_allowed_codes(monkeypatch):
    manager = KiwoomWSManager("test-token")
    fake_ws = _FakeWS([])
    manager.websocket = fake_ws
    manager._session_ready.set()

    monkeypatch.setattr(
        "src.utils.kiwoom_utils.get_effective_kiwoom_code", lambda code: code
    )

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


def test_persistent_repair_filter_enforces_global_window_budget(monkeypatch):
    manager = KiwoomWSManager("test-token")
    monkeypatch.setenv("KORSTOCKSCAN_WS_PERSISTENT_REPAIR_MAX_CODES", "8")
    monkeypatch.setenv("KORSTOCKSCAN_WS_PERSISTENT_REPAIR_MAX_CODES_PER_WINDOW", "3")
    monkeypatch.setenv("KORSTOCKSCAN_WS_PERSISTENT_REPAIR_WINDOW_SEC", "60")
    monkeypatch.setenv("KORSTOCKSCAN_WS_PERSISTENT_REPAIR_TTL_SEC", "0")
    now = {"value": 1000.0}
    monkeypatch.setattr(kiwoom_websocket.time, "time", lambda: now["value"])

    assert manager._filter_persistent_repair_targets(
        ["000001", "000002", "000003", "000004"]
    ) == (["000001", "000002", "000003"], ["000004"])
    now["value"] = 1030.0
    assert manager._filter_persistent_repair_targets(["000004"]) == ([], ["000004"])
    now["value"] = 1061.0
    assert manager._filter_persistent_repair_targets(["000004"]) == (["000004"], [])


def test_persistent_repair_rebuild_cannot_bypass_global_window_budget(monkeypatch):
    manager = KiwoomWSManager("test-token")
    manager.subscribed_codes.update({"000001", "000002", "000003"})
    monkeypatch.setenv("KORSTOCKSCAN_WS_PERSISTENT_REPAIR_REBUILD_GROUP_ENABLED", "1")
    monkeypatch.setenv("KORSTOCKSCAN_WS_PERSISTENT_REPAIR_MAX_CODES_PER_WINDOW", "2")
    monkeypatch.setenv("KORSTOCKSCAN_WS_PERSISTENT_REPAIR_WINDOW_SEC", "60")
    monkeypatch.setattr(kiwoom_websocket.time, "time", lambda: 1000.0)
    manager._persistent_repair_window_epochs.append(1000.0)

    rebuild, targets = manager._persistent_repair_rebuild_targets(["000001"])

    assert rebuild is False
    assert targets == ["000001"]
    assert list(manager._persistent_repair_window_epochs) == [1000.0]


def test_persistent_repair_defaults_refresh_stale_scanner_sources_quickly(monkeypatch):
    manager = KiwoomWSManager("test-token")
    monkeypatch.delenv("KORSTOCKSCAN_WS_PERSISTENT_REPAIR_MAX_CODES", raising=False)
    monkeypatch.delenv("KORSTOCKSCAN_WS_PERSISTENT_REPAIR_TTL_SEC", raising=False)
    monkeypatch.delenv(
        "KORSTOCKSCAN_WS_PERSISTENT_REPAIR_REBUILD_GROUP_ENABLED", raising=False
    )
    now = {"value": 1000.0}
    monkeypatch.setattr(kiwoom_websocket.time, "time", lambda: now["value"])

    assert manager._persistent_repair_max_codes() == 8
    assert manager._persistent_repair_ttl_sec() == 30.0
    assert manager._persistent_repair_remove_before_reg_enabled() is False
    assert manager._persistent_repair_rebuild_group_enabled() is False
    assert manager._filter_persistent_repair_targets(["000001"]) == (["000001"], [])
    assert manager._filter_persistent_repair_targets(["000001"]) == ([], ["000001"])
    now["value"] = 1030.0

    assert manager._filter_persistent_repair_targets(["000001"]) == (["000001"], [])


def test_persistent_repair_rebuild_targets_default_off(monkeypatch):
    manager = KiwoomWSManager("test-token")
    manager.subscribed_codes.update({"000001", "000002"})
    monkeypatch.delenv(
        "KORSTOCKSCAN_WS_PERSISTENT_REPAIR_REBUILD_GROUP_ENABLED", raising=False
    )

    rebuild, targets = manager._persistent_repair_rebuild_targets(["000003"])

    assert rebuild is False
    assert targets == ["000003"]


def test_persistent_repair_rebuild_targets_merges_subscribed_when_enabled(monkeypatch):
    manager = KiwoomWSManager("test-token")
    manager.subscribed_codes.update({"000001", "000002"})
    monkeypatch.setenv("KORSTOCKSCAN_WS_PERSISTENT_REPAIR_REBUILD_GROUP_ENABLED", "1")
    monkeypatch.setenv("KORSTOCKSCAN_WS_PERSISTENT_REPAIR_TTL_SEC", "20")
    monkeypatch.setenv(
        "KORSTOCKSCAN_WS_PERSISTENT_REPAIR_REBUILD_GROUP_MIN_INTERVAL_SEC", "30"
    )
    now = {"value": 1000.0}
    monkeypatch.setattr(kiwoom_websocket.time, "time", lambda: now["value"])

    rebuild, targets = manager._persistent_repair_rebuild_targets(["000003", "000001"])

    assert rebuild is True
    assert targets == ["000001", "000002", "000003"]
    assert manager._persistent_repair_request_ts == {
        "000001": 1000.0,
        "000002": 1000.0,
        "000003": 1000.0,
    }

    now["value"] = 1010.0
    assert manager._filter_persistent_repair_targets(["000002"]) == (
        [],
        ["000002"],
    )
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
    monkeypatch.setattr(
        kiwoom_websocket, "_WS_OPERATOR_RUNTIME_OVERRIDE_PATH", override_path
    )
    monkeypatch.setattr(kiwoom_websocket, "_WS_HOT_RUNTIME_OVERRIDE_REFRESH_SEC", 0.0)
    monkeypatch.delenv("KORSTOCKSCAN_WS_ALTERNATE_ROUTE_MAX_CODES", raising=False)
    monkeypatch.delenv("KORSTOCKSCAN_WS_PERSISTENT_REPAIR_MAX_CODES", raising=False)
    _reset_ws_hot_override_cache()

    override_path.write_text(
        "\n".join(
            [
                "export KORSTOCKSCAN_WS_ALTERNATE_ROUTE_MAX_CODES=11",
                "export KORSTOCKSCAN_WS_ALTERNATE_ROUTE_TTL_SEC=30",
                "export KORSTOCKSCAN_WS_FRESHNESS_STALE_SEC=17",
                "export KORSTOCKSCAN_WS_MAX_REG_ITEMS=41",
                "export KORSTOCKSCAN_WS_PERSISTENT_REPAIR_MAX_CODES=17",
                "export KORSTOCKSCAN_WS_PERSISTENT_REPAIR_REMOVE_BEFORE_REG_ENABLED=false",
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
    assert KiwoomWSManager._freshness_stale_sec() == 17.0
    assert KiwoomWSManager._max_registered_item_count() == 41
    assert KiwoomWSManager._persistent_repair_max_codes() == 17
    assert KiwoomWSManager._persistent_repair_remove_before_reg_enabled() is False
    assert KiwoomWSManager._persistent_repair_rebuild_group_enabled() is True
    assert KiwoomWSManager._persistent_repair_rebuild_group_min_interval_sec() == 19.0
    assert KiwoomWSManager._persistent_repair_stuck_cooldown_sec() == 120.0
    assert KiwoomWSManager._persistent_repair_stuck_min_attempts() == 4
    assert KiwoomWSManager._persistent_repair_ttl_sec() == 20.0
    assert (
        kiwoom_websocket._ws_hot_runtime_override_value(
            "KORSTOCKSCAN_BUY_SCORE_THRESHOLD"
        )
        is None
    )

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

    assert manager._filter_persistent_repair_targets(["000001", "000002"]) == (
        ["000001", "000002"],
        [],
    )
    assert manager._filter_persistent_repair_targets(["000001", "000003"]) == (
        ["000003"],
        ["000001"],
    )
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


def test_persistent_repair_quote_only_converges_to_required_0b_cooldown(monkeypatch):
    manager = KiwoomWSManager("test-token")
    monkeypatch.setenv("KORSTOCKSCAN_WS_PERSISTENT_REPAIR_TTL_SEC", "0")
    monkeypatch.setenv("KORSTOCKSCAN_WS_PERSISTENT_REPAIR_STUCK_MIN_ATTEMPTS", "2")
    monkeypatch.setenv("KORSTOCKSCAN_WS_PERSISTENT_REPAIR_STUCK_COOLDOWN_SEC", "120")
    now = {"value": 1000.0}
    monkeypatch.setattr(kiwoom_websocket.time, "time", lambda: now["value"])
    manager.subscribed_codes.add("000001")
    manager._required_realtime_types_by_code["000001"] = ("0B",)
    manager.realtime_data["000001"] = {
        "last_realtime_type_ts": {"0D": 999.0},
        "received_types": {"0D"},
    }

    assert manager._filter_persistent_repair_targets(["000001"]) == (["000001"], [])
    now["value"] = 1001.0
    assert manager._filter_persistent_repair_targets(["000001"]) == (["000001"], [])
    now["value"] = 1002.0

    assert manager._filter_persistent_repair_targets(["000001"]) == ([], ["000001"])


def test_persistent_repair_any_receipt_clears_counter_without_required_type_contract(
    monkeypatch,
):
    manager = KiwoomWSManager("test-token")
    monkeypatch.setenv("KORSTOCKSCAN_WS_PERSISTENT_REPAIR_TTL_SEC", "0")
    monkeypatch.setenv("KORSTOCKSCAN_WS_PERSISTENT_REPAIR_STUCK_MIN_ATTEMPTS", "2")
    monkeypatch.setenv("KORSTOCKSCAN_WS_PERSISTENT_REPAIR_STUCK_COOLDOWN_SEC", "120")
    monkeypatch.setattr(kiwoom_websocket.time, "time", lambda: 1000.0)
    manager.subscribed_codes.add("000001")
    manager._persistent_repair_no_tick_attempts["000001"] = 1
    manager.realtime_data["000001"] = {
        "last_realtime_type_ts": {"0D": 999.0},
        "received_types": {"0D"},
    }

    assert manager._filter_persistent_repair_targets(["000001"]) == (["000001"], [])
    assert manager._persistent_repair_no_tick_attempts.get("000001") is None
    assert manager._persistent_repair_stuck_until_ts.get("000001") is None


def test_command_ws_reg_scanner_defaults_to_required_0b(monkeypatch):
    manager = KiwoomWSManager("test-token")
    captured = {}

    monkeypatch.setattr(
        manager,
        "execute_subscribe",
        lambda codes, **kwargs: captured.update(codes=list(codes), **kwargs),
    )

    manager._handle_reg_event(
        {"codes": ["000001"], "source": "scanner_runtime_target_attach"}
    )

    assert captured["codes"] == ["000001"]
    assert captured["required_realtime_types"] == ("0B",)


def test_command_ws_reg_preserves_explicit_required_realtime_types(monkeypatch):
    manager = KiwoomWSManager("test-token")
    captured = {}

    monkeypatch.setattr(
        manager,
        "execute_subscribe",
        lambda codes, **kwargs: captured.update(codes=list(codes), **kwargs),
    )

    manager._handle_reg_event(
        {
            "codes": ["000001"],
            "source": "scanner_runtime_target_attach",
            "required_realtime_types": ["0B", "0D"],
        }
    )

    assert captured["required_realtime_types"] == ["0B", "0D"]


def test_command_ws_reg_preserves_explicit_wire_realtime_types(monkeypatch):
    manager = KiwoomWSManager("test-token")
    captured = {}

    monkeypatch.setattr(
        manager,
        "execute_subscribe",
        lambda codes, **kwargs: captured.update(codes=list(codes), **kwargs),
    )

    manager._handle_reg_event(
        {
            "codes": ["000001"],
            "source": "explicit_observation_test",
            "required_realtime_types": ["0B", "0D"],
            "realtime_types": ["0B", "0D"],
        }
    )

    assert captured["required_realtime_types"] == ["0B", "0D"]
    assert captured["realtime_types"] == ["0B", "0D"]


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
    assert manager.realtime_data["039490"]["last_ws_item"] == "039490_AL"
    assert manager.realtime_data["039490"]["last_ws_market_suffix"] == "_AL"
    assert (
        manager.realtime_data["039490"]["last_ws_market_route"] == "krx_nxt_integrated"
    )
    assert (
        manager.realtime_data["039490"]["last_realtime_type_item"]["0B"] == "039490_AL"
    )
    assert manager.realtime_data["039490"]["last_realtime_type_market_route"]["0B"] == (
        "krx_nxt_integrated"
    )
    assert (
        manager.realtime_data["039490"]["last_realtime_type_effective_venue"]["0B"]
        == ""
    )
    assert (
        manager.realtime_data["039490"]["last_ws_actual_execution_venue"] == "UNKNOWN"
    )
    assert (
        manager.realtime_data["039490"]["last_realtime_type_actual_execution_venue"][
            "0B"
        ]
        == "UNKNOWN"
    )
    route_snapshot = manager.realtime_data["039490"][
        "realtime_type_snapshots_by_route"
    ]["_AL|krx_nxt_integrated"]["0B"]
    assert route_snapshot["item"] == "039490_AL"
    assert route_snapshot["current_price"] == 10000
    assert route_snapshot["effective_venue"] == ""
    assert route_snapshot["actual_execution_venue"] == "UNKNOWN"


def test_realtime_snapshots_preserve_plain_and_integrated_routes_independently(
    monkeypatch,
):
    clock = [kiwoom_websocket.time.time()]
    monkeypatch.setattr(kiwoom_websocket.time, "time", lambda: clock[0])
    manager = KiwoomWSManager("test-token")
    manager._micro_reversion_forward_collector = SimpleNamespace(
        flags=SimpleNamespace(depth_capture_active=True),
        observe_kiwoom_0b=lambda *_args, **_kwargs: None,
        observe_kiwoom_0d=lambda *_args, **_kwargs: None,
    )
    manager.subscribed_codes.add("039490")
    # Parsing/observer latency must not make the same depth receipt younger.
    monkeypatch.setattr(
        manager,
        "_update_micro_estimator_from_orderbook",
        lambda *_args, **_kwargs: clock.__setitem__(0, clock[0] + 0.1),
    )

    asyncio.run(
        manager._handle_message(
            json.dumps(
                {
                    "trnm": "REAL",
                    "data": [
                        {
                            "type": "0B",
                            "item": "039490_AL",
                            "values": {"10": "10000", "15": "+1"},
                        },
                        {
                            "type": "0D",
                            "item": "039490_AL",
                            "values": {
                                "21": "090001000",
                                "41": "10010",
                                "61": "100",
                                "42": "10020",
                                "62": "120",
                                "43": "10030",
                                "63": "130",
                                "44": "10040",
                                "64": "140",
                                "45": "10050",
                                "65": "150",
                                "51": "10000",
                                "71": "200",
                                "121": "100",
                                "125": "200",
                                "6064": "0",
                                "6065": "0",
                                "6086": "100",
                                "6087": "200",
                            },
                        },
                        {
                            "type": "0B",
                            "item": "039490",
                            "values": {"10": "9990", "15": "-1"},
                        },
                        {
                            "type": "0D",
                            "item": "039490",
                            "values": {
                                "21": "090002000",
                                "41": "10000",
                                "61": "150",
                                "51": "9990",
                                "71": "250",
                                "121": "150",
                                "125": "250",
                            },
                        },
                    ],
                }
            )
        )
    )

    snapshots = manager.realtime_data["039490"]["realtime_type_snapshots_by_route"]
    assert set(snapshots) == {
        "_AL|krx_nxt_integrated",
        "KRX|krx_only",
    }
    assert snapshots["_AL|krx_nxt_integrated"]["0B"]["current_price"] == 10000
    assert (
        snapshots["_AL|krx_nxt_integrated"]["0D"]["orderbook"]["asks"][0]["price"]
        == 10010
    )
    assert snapshots["_AL|krx_nxt_integrated"]["0D"]["route_depth_totals"] == {
        "combined": {"ask": 100, "bid": 200},
        "KRX": {"ask": 0, "bid": 0},
        "NXT": {"ask": 100, "bid": 200},
    }
    assert (
        manager.realtime_data["039490"]["recent_depth_ticks_by_route"][
            "_AL|krx_nxt_integrated"
        ][0]["ask_levels"][0]["price"]
        == 10010
    )
    integrated_depth = manager.realtime_data["039490"]["recent_depth_ticks_by_route"][
        "_AL|krx_nxt_integrated"
    ][0]
    assert integrated_depth["market_route"] == "krx_nxt_integrated"
    assert integrated_depth["market_suffix"] == "_AL"
    assert integrated_depth["route_sequence"] > 0
    assert snapshots["_AL|krx_nxt_integrated"]["0D"]["observed_epoch"] == (
        integrated_depth["received_at_ms"] / 1000
    )
    assert snapshots["KRX|krx_only"]["0B"]["current_price"] == 9990
    assert snapshots["KRX|krx_only"]["0D"]["orderbook"]["bids"][0]["price"] == 9990
    depth = manager.realtime_data["039490"]["last_depth_tick"]
    assert depth["item"] == "039490"
    assert depth["orderbook_time_raw"] == "090002000"
    assert depth["ask_levels"][0] == {
        "level": 1,
        "price": 10000,
        "quantity": 150,
    }
    assert depth["route_depth_totals"]["combined"] == {"ask": 150, "bid": 250}


def test_0d_depth_projection_is_not_built_while_feature_is_off():
    manager = KiwoomWSManager("test-token")
    manager.subscribed_codes.add("039490")

    asyncio.run(
        manager._handle_message(
            json.dumps(
                {
                    "trnm": "REAL",
                    "data": [
                        {
                            "type": "0D",
                            "item": "039490",
                            "values": {
                                "21": "090002000",
                                "41": "10000",
                                "61": "150",
                                "51": "9990",
                                "71": "250",
                                "121": "150",
                                "125": "250",
                            },
                        }
                    ],
                }
            )
        )
    )

    assert "last_depth_tick" not in manager.realtime_data["039490"]


def test_ws_item_effective_venue_does_not_invent_integrated_underlying_venue():
    assert KiwoomWSManager._ws_item_effective_venue("005930") == "KRX"
    assert KiwoomWSManager._ws_item_effective_venue("005930_NX") == "NXT"
    assert KiwoomWSManager._ws_item_effective_venue("005930_AL") == ""
    assert KiwoomWSManager._ws_item_actual_execution_venue("005930") == "UNKNOWN"
    assert KiwoomWSManager._ws_item_actual_execution_venue("005930_NX") == "UNKNOWN"
    assert KiwoomWSManager._ws_item_actual_execution_venue("005930_AL") == "UNKNOWN"


def test_subscription_snapshot_opening_gap_without_verified_state_fails_closed():
    from datetime import datetime

    manager = KiwoomWSManager("test-token")
    manager.subscribed_codes.add("005930")
    manager._registered_items_by_code["005930"] = ("005930_NX",)
    manager._required_realtime_types_by_code["005930"] = ("0B", "0D")
    gap = datetime.fromisoformat("2026-09-10T08:55:00+09:00").timestamp()
    row = manager.get_subscription_freshness_snapshot(["005930"], now_ts=gap)["rows"][0]
    assert row["freshness_state"] == "no_tick"
    assert "observed_freshness_state" not in row
    assert row["repair_recommended"] is True
    assert row["required_realtime_received"] is False
    assert row["required_realtime_missing_types"] == ["0B", "0D"]
    opened = datetime.fromisoformat("2026-09-10T09:00:30+09:00").timestamp()
    row = manager.get_subscription_freshness_snapshot(["005930"], now_ts=opened)[
        "rows"
    ][0]
    assert row["freshness_state"] == "no_tick"
    assert row["repair_recommended"] is True


def test_subscription_freshness_snapshot_classifies_no_tick_stale_and_fresh(
    monkeypatch,
):
    manager = KiwoomWSManager("test-token")
    monkeypatch.setenv("KORSTOCKSCAN_WS_FRESHNESS_STALE_SEC", "30")
    manager.subscribed_codes.update({"000001", "000002", "000003", "000004"})
    manager._registered_items_by_code = {
        "000001": ("000001",),
        "000002": ("000002",),
        "000003": ("000003", "000003_AL"),
        "000004": ("000004",),
    }
    manager.realtime_data["000002"] = {
        "last_ws_update_ts": 950.0,
        "last_realtime_type_ts": {"0B": 950.0},
        "received_types": {"0B"},
    }
    manager.realtime_data["000003"] = {
        "last_ws_update_ts": 995.0,
        "last_realtime_type_ts": {"0B": 995.0, "0D": 996.0},
        "received_types": {"0B", "0D"},
    }
    manager.realtime_data["000004"] = {
        "last_ws_update_ts": 996.0,
        "last_realtime_type_ts": {"0B": 950.0, "0D": 996.0},
        "last_trade_tick": {"ts": 950.0, "cum_volume": "1,234"},
        "received_types": {"0B", "0D"},
    }

    snapshot = manager.get_subscription_freshness_snapshot(now_ts=1000.0)
    rows = {row["stock_code"]: row for row in snapshot["rows"]}

    assert rows["000001"]["freshness_state"] == "no_tick"
    assert rows["000001"]["repair_recommended"] is True
    assert rows["000001"]["repair_reason"] == "subscription_no_tick"
    assert rows["000002"]["freshness_state"] == "stale"
    assert rows["000002"]["last_receive_age_sec"] == 50.0
    assert rows["000002"]["repair_reason"] == "subscription_stale"
    assert rows["000003"]["freshness_state"] == "fresh"
    assert rows["000003"]["last_receive_age_sec"] == 4.0
    assert rows["000003"]["registered_item_count"] == 2
    assert rows["000003"]["registered_item_quota_units"] == 2
    assert rows["000003"]["registered_market_suffixes"] == ["", "_AL"]
    assert rows["000003"]["registered_market_routes"] == [
        "krx_only",
        "krx_nxt_integrated",
    ]
    assert rows["000003"]["registered_route_counts"] == {
        "krx_nxt_integrated": 1,
        "krx_only": 1,
    }
    assert rows["000003"]["multi_route_registered"] is True
    assert (
        rows["000003"]["route_repair_policy"]
        == "remove_then_reg_required_for_route_transition"
    )
    assert rows["000003"]["decision_authority"] == "ws_freshness_source_quality_only"
    assert rows["000003"]["broker_order_forbidden"] is True
    assert rows["000004"]["freshness_state"] == "fresh"
    assert rows["000004"]["last_receive_age_sec"] == 4.0
    assert rows["000004"]["last_0b_age_sec"] == 50.0
    assert rows["000004"]["last_0d_age_sec"] == 4.0
    assert rows["000004"]["last_trade_cum_volume"] == 1234
    assert rows["000004"]["repair_recommended"] is False
    assert rows["000004"]["repair_reason"] == "none"
    assert rows["000004"]["recommended_repair"] == "none"
    assert rows["000004"]["trade_tick_quiet"] is True
    assert (
        rows["000004"]["trade_tick_quiet_reason"]
        == "fresh_non_trade_ws_without_fresh_0b"
    )

    filtered = manager.get_subscription_freshness_snapshot(["999999"], now_ts=1000.0)
    assert filtered["rows"][0]["freshness_state"] == "unsubscribed"
    assert filtered["rows"][0]["repair_recommended"] is False


def test_send_reg_remove_before_reg_removes_existing_route_then_registers_new_route(
    monkeypatch,
):
    manager = KiwoomWSManager("test-token")
    fake_ws = _FakeWS([])
    manager.websocket = fake_ws
    manager._session_ready.set()
    manager.subscribed_codes.add("039490")
    manager._registered_items_by_code["039490"] = ("039490_AL",)

    monkeypatch.setattr(
        "src.utils.kiwoom_utils.get_effective_kiwoom_code", lambda code: code
    )

    asyncio.run(
        manager._send_reg(
            ["039490"],
            remove_before_reg=True,
            source="scanner_persistent_ws_gap_recovery",
            repair_cycle="persistent_ws_gap",
        )
    )

    remove_payload = json.loads(fake_ws.sent[0])
    reg_payload = json.loads(fake_ws.sent[1])
    assert remove_payload["trnm"] == "REMOVE"
    assert remove_payload["data"][0]["item"] == ["039490_AL"]
    assert reg_payload["trnm"] == "REG"
    assert reg_payload["data"][0]["item"] == ["039490"]
    assert manager.subscribed_codes == {"039490"}
    assert manager._registered_items_by_code["039490"] == ("039490",)


def test_send_remove_updates_local_state_when_requested(monkeypatch):
    manager = KiwoomWSManager("test-token")
    fake_ws = _FakeWS([])
    manager.websocket = fake_ws
    manager._session_ready.set()
    manager.subscribed_codes.add("000001")
    manager._registered_items_by_code["000001"] = ("000001", "000001_AL")
    manager.realtime_data["000001"] = {"last_ws_update_ts": 1000.0}
    manager._recent_reg_request_ts["000001"] = 999.0
    manager._persistent_repair_request_ts["000001"] = 999.0

    asyncio.run(
        manager._send_remove(["000001"], update_local_state=True, source="test")
    )

    remove_payload = json.loads(fake_ws.sent[0])
    assert remove_payload["trnm"] == "REMOVE"
    assert remove_payload["data"][0]["item"] == ["000001", "000001_AL"]
    assert "000001" not in manager.subscribed_codes
    assert "000001" not in manager._registered_items_by_code
    assert "000001" not in manager.realtime_data
    assert "000001" not in manager._recent_reg_request_ts
    assert "000001" not in manager._persistent_repair_request_ts


def test_remove_before_reg_string_false_does_not_send_remove(monkeypatch):
    manager = KiwoomWSManager("test-token")
    fake_ws = _FakeWS([])
    manager.websocket = fake_ws
    manager._session_ready.set()
    manager.subscribed_codes.add("039490")
    manager._registered_items_by_code["039490"] = ("039490_AL",)

    monkeypatch.setattr(
        "src.utils.kiwoom_utils.get_effective_kiwoom_code", lambda code: code
    )

    asyncio.run(manager._send_reg(["039490"], remove_before_reg="false"))

    payloads = [json.loads(payload) for payload in fake_ws.sent]
    assert [payload["trnm"] for payload in payloads] == ["REG"]


def test_retired_feedback_has_no_deferred_scheduler():
    manager = KiwoomWSManager("test-token")
    assert not hasattr(manager, "_micro_reversion_deferred_reg_codes")
    assert (
        manager._defer_missing_micro_registration(["005930"], source="retired") is None
    )


def test_premarket_quiet_persistent_repair_keeps_current_registration(monkeypatch):
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 9, 21, 8, 20, tzinfo=tz)

    monkeypatch.setattr(kiwoom_websocket, "datetime", Clock)
    manager = KiwoomWSManager("test-token")
    manager._started = True
    manager.websocket = _FakeWS([])
    manager._session_ready.set()
    manager.subscribed_codes.add("005930")
    manager._registered_items_by_code["005930"] = ("005930_AL",)
    manager._registered_item_epochs["005930_AL"] = manager._market_data_transport_epoch
    manager._registered_item_types["005930_AL"] = ("0B", "0D", "0w", "0F")
    manager.loop = SimpleNamespace(
        is_running=lambda: (_ for _ in ()).throw(
            AssertionError("must not dispatch quiet repair")
        )
    )
    manager.execute_subscribe(
        ["005930"],
        force=True,
        repair_cycle="persistent_ws_gap",
        required_realtime_types=["0B", "0D"],
    )
    assert manager.websocket.sent == []
    # A missing type is a real registration change, and must reach dispatch.
    with pytest.raises(AssertionError, match="dispatch"):
        manager.execute_subscribe(
            ["005930"],
            force=True,
            repair_cycle="persistent_ws_gap",
            required_realtime_types=["0H"],
        )
    manager._market_data_transport_epoch += 1
    with pytest.raises(AssertionError, match="dispatch"):
        manager.execute_subscribe(
            ["005930"], force=True, repair_cycle="persistent_ws_gap"
        )


def test_observation_only_al_demotion_does_not_repromote_runtime_item(monkeypatch):
    manager = KiwoomWSManager("test-token")
    manager.websocket = _FakeWS([])
    manager._session_ready.set()
    manager._implicit_runtime_route_codes.add("005930")
    manager._micro_reversion_observation_only_items.add("005930_AL")
    monkeypatch.setattr(manager, "_integrated_aftermarket_route_required", lambda: True)
    asyncio.run(
        manager._send_reg(
            ["005930_AL"], observation_only=True, realtime_types=["0B", "0D"]
        )
    )
    assert "005930_AL" in manager._micro_reversion_observation_only_items
    assert manager._runtime_primary_items_by_code.get("005930") != "005930_AL"


def _exact_probe_manager():
    manager = KiwoomWSManager("test-token")
    manager.websocket = _FakeWS([])
    manager._session_ready.set()
    manager._market_data_transport_epoch = 8
    manager.subscribed_codes = {"010140"}
    manager._registered_items_by_code["010140"] = ("010140_AL",)
    manager._registered_item_epochs["010140_AL"] = 8
    manager._registered_item_types["010140_AL"] = ("0B", "0D", "0w", "0F")
    manager._ensure_target_defaults("010140")["curr"] = 12345
    return manager


def _zero_base_native_transfer(route="nxt_only"):
    import time
    from src.engine.scalping import reversal_source_diagnostics as D

    manager = KiwoomWSManager("test-token")
    manager.websocket = _FakeWS([])
    manager._session_ready.set()
    manager._market_data_transport_epoch = 8
    code = "010140"
    venue, suffix = ("NXT", "_NX") if route == "nxt_only" else ("SOR", "_AL")
    item = code + suffix
    manager.subscribed_codes = {code}
    manager._registered_items_by_code[code] = (item,)
    manager._registered_item_epochs[item] = 8
    manager._registered_item_types[item] = ("0B", "0D")
    manager._exact_probe_item_leases[item] = {"lease_id": "lease-1", "epoch": 8}
    manager._micro_reversion_observation_only_items.add(item)
    manager._micro_reversion_observation_only_codes.add(code)
    manager._ensure_target_defaults(
        item, store=manager._micro_reversion_observation_route_data
    )["curr"] = 99999
    now = time.time()
    expected = dict(
        snapshot=(
            {
                "symbol": code,
                "venue": venue,
                "source_item": item,
                "native_epoch": 8,
                "epoch": now,
            },
            {},
        ),
        deadline_epoch=now + 5,
        deadline_perf=time.perf_counter() + 5,
        observer_pid=os.getpid(),
        observer_start_ticks=D._PROCESS_START_TICKS,
    )
    payload = dict(
        code=code,
        market_data_route=route,
        ws_handoff_id="lease-1",
        physical_probe_lease_id="lease-1",
        native_observation=expected,
        zero_base_pending_db=True,
    )
    return manager, payload, item


@pytest.mark.parametrize("route", ["nxt_only", "krx_nxt_integrated"])
@pytest.mark.parametrize("borrowed", [False, True])
def test_zero_base_native_transfer_keeps_exact_registration_and_cleanup(
    route, borrowed
):
    manager, payload, item = _zero_base_native_transfer(route)
    if borrowed:
        manager._exact_probe_item_leases.clear()
    other = "010140" if item.endswith("_NX") else "010140_NX"
    manager._registered_items_by_code["010140"] += (other,)
    manager._registered_item_epochs[other] = 8
    manager._registered_item_types[other] = ("0B", "0D")
    manager._micro_reversion_observation_only_items.add(other)
    assert manager.adopt_zero_base_probe_target(payload)
    assert manager._runtime_primary_items_by_code["010140"] == item
    assert item not in manager._micro_reversion_observation_only_items
    assert other in manager._micro_reversion_observation_only_items
    assert manager.get_latest_data("010140") == {}  # No observation-to-executable copy.
    assert manager.get_exact_item_data("010140", item) == {}
    assert asyncio.run(manager._release_exact_probe_item(item, "lease-1"))
    assert manager._registered_item_epochs[item] == 8
    assert manager._registered_item_types[item] == ("0B", "0D")
    assert manager._registered_item_epochs[other] == 8
    assert manager.websocket.sent == []


@pytest.mark.parametrize(
    "gap",
    [
        "expired",
        "wrong_pid",
        "route",
        "symbol",
        "epoch",
        "registered_epoch",
        "missing_0d",
        "lease",
        "lease_epoch",
        "physical_lease",
        "removing",
        "not_ready",
        "stopped",
        "primary_conflict",
        "other_runtime_item",
        "unregistered",
    ],
)
def test_zero_base_native_transfer_rejects_invalid_original_binding(gap):
    import time

    manager, payload, item = _zero_base_native_transfer()
    expected = payload["native_observation"]
    if gap == "expired":
        expected["deadline_perf"] = time.perf_counter() - 1
    elif gap == "wrong_pid":
        expected["observer_pid"] += 1
    elif gap == "route":
        payload["market_data_route"] = "krx_nxt_integrated"
    elif gap == "symbol":
        expected["snapshot"][0]["symbol"] = "005930"
    elif gap == "epoch":
        manager._market_data_transport_epoch = 9
    elif gap == "registered_epoch":
        manager._registered_item_epochs[item] = 7
    elif gap == "missing_0d":
        manager._registered_item_types[item] = ("0B",)
    elif gap == "lease":
        manager._exact_probe_item_leases[item]["lease_id"] = "other"
    elif gap == "lease_epoch":
        manager._exact_probe_item_leases[item]["epoch"] = 7
    elif gap == "physical_lease":
        payload["physical_probe_lease_id"] = "different-physical-lease"
    elif gap == "removing":
        manager._exact_probe_item_leases[item]["removing"] = True
    elif gap == "not_ready":
        manager._session_ready.clear()
    elif gap == "stopped":
        manager._stop_event.set()
    elif gap == "primary_conflict":
        manager._runtime_primary_items_by_code["010140"] = "010140_AL"
    elif gap == "other_runtime_item":
        manager._registered_items_by_code["010140"] += ("010140_AL",)
    elif gap == "unregistered":
        manager._registered_items_by_code["010140"] = ()
    assert not manager.adopt_zero_base_probe_target(payload)
    assert item in manager._micro_reversion_observation_only_items
    assert not manager._exact_probe_item_leases[item].get("adopted")
    assert manager.websocket.sent == []


@pytest.mark.parametrize("route", ["nxt_only", "krx_nxt_integrated"])
def test_zero_base_native_transfer_uses_only_later_real_packets(route):
    manager, payload, item = _zero_base_native_transfer(route)
    assert manager.adopt_zero_base_probe_target(payload)
    before_epoch = manager._market_data_transport_epoch
    asyncio.run(
        manager._handle_message(
            json.dumps(
                {
                    "trnm": "REAL",
                    "data": [
                        {
                            "type": "0B",
                            "item": item,
                            "values": {"10": "10000", "15": "+1", "228": "101.5"},
                        },
                        {
                            "type": "0D",
                            "item": item,
                            "values": {
                                "21": "133500",
                                "41": "10010",
                                "51": "9990",
                                "61": "10",
                                "71": "10",
                            },
                        },
                    ],
                }
            )
        )
    )
    snapshot = manager.get_exact_item_data("010140", item)
    assert snapshot["curr"] == 10000  # Observation-only price was 99999.
    assert snapshot["received_types"] == {"0B", "0D"}
    assert manager._market_data_transport_epoch == before_epoch
    assert manager.websocket.sent == []


def test_exact_probe_adds_nx_preserves_al_and_removes_only_owned_item():
    manager = _exact_probe_manager()

    async def scenario():
        receipt = await manager._acquire_exact_probe_item("010140_NX", "lease-1")
        assert receipt["registered"] is True
        assert manager._registered_items_by_code["010140"] == ("010140_AL", "010140_NX")
        assert manager._registered_item_epochs["010140_NX"] == 8
        assert manager._registered_item_types["010140_NX"] == ("0B", "0D")
        assert "010140" not in manager._micro_reversion_observation_only_codes
        assert manager.get_latest_data("010140")["curr"] == 12345
        repeated = await manager._acquire_exact_probe_item("010140_NX", "lease-1")
        assert repeated["created"] is True
        assert len(manager.websocket.sent) == 1
        assert (await manager._acquire_exact_probe_item("010140_NX", "other"))[
            "registered"
        ] is False
        assert await manager._release_exact_probe_item("010140_NX", "other") is True
        assert len(manager.websocket.sent) == 1
        assert await manager._release_exact_probe_item("010140_NX", "lease-1") is True
        assert manager._registered_items_by_code["010140"] == ("010140_AL",)
        assert manager._registered_item_types["010140_AL"] == ("0B", "0D", "0w", "0F")
        assert "010140_NX" not in manager._micro_reversion_observation_only_items

    asyncio.run(scenario())
    packets = [json.loads(raw) for raw in manager.websocket.sent]
    assert packets[0]["trnm"] == "REG" and packets[0]["refresh"] == "1"
    assert all(row["item"] == ["010140_NX"] for row in packets[0]["data"])
    assert packets[1] == {
        "trnm": "REMOVE",
        "grp_no": "1",
        "data": [{"item": ["010140_NX"], "type": ["0B", "0D"]}],
    }


@pytest.mark.parametrize(
    "condition",
    ["budget", "not_ready", "invalid_existing", "borrowed", "adopted", "reconnect"],
)
def test_exact_probe_budget_borrowing_adoption_and_epoch_boundaries(
    monkeypatch, condition
):
    manager = _exact_probe_manager()

    async def scenario():
        if condition == "budget":
            monkeypatch.setattr(manager, "_max_registered_item_count", lambda: 1)
        elif condition == "not_ready":
            manager._session_ready.clear()
        elif condition in {"invalid_existing", "borrowed"}:
            manager._registered_items_by_code["010140"] += ("010140_NX",)
            manager._registered_item_epochs["010140_NX"] = (
                7 if condition == "invalid_existing" else 8
            )
            manager._registered_item_types["010140_NX"] = ("0B", "0D")
        receipt = await manager._acquire_exact_probe_item("010140_NX", "lease-1")
        if condition in {"budget", "not_ready", "invalid_existing"}:
            assert receipt["registered"] is False
        else:
            assert receipt["registered"] is True
        if condition == "adopted":
            manager._exact_probe_item_leases["010140_NX"]["adopted"] = True
        elif condition == "reconnect":
            manager._market_data_transport_epoch = 9
        before = len(manager.websocket.sent)
        await manager._release_exact_probe_item("010140_NX", "lease-1")
        assert len(manager.websocket.sent) == before
        assert manager._registered_items_by_code["010140"][0] == "010140_AL"
        if condition in {"borrowed", "adopted"}:
            assert "010140_NX" in manager._registered_items_by_code["010140"]
        if condition == "reconnect":
            assert manager._registered_items_by_code["010140"] == ("010140_AL",)

    asyncio.run(scenario())


def test_exact_probe_send_failure_retains_custody_for_item_cleanup(monkeypatch):
    manager = _exact_probe_manager()

    async def uncertain_send(*args, **kwargs):
        return None  # Native transport reports no confirmed registration.

    monkeypatch.setattr(manager, "_send_reg_impl", uncertain_send)

    async def scenario():
        receipt = await manager._acquire_exact_probe_item("010140_NX", "lease-1")
        assert receipt["registered"] is False and receipt["created"] is True
        assert "010140_NX" in manager._exact_probe_item_leases
        await manager._release_exact_probe_item("010140_NX", "lease-1")
        assert manager._registered_items_by_code["010140"] == ("010140_AL",)
        assert "010140_NX" not in manager._exact_probe_item_leases

    asyncio.run(scenario())
    assert json.loads(manager.websocket.sent[0])["trnm"] == "REMOVE"


def test_exact_probe_adoption_during_remove_serializes_restore_without_touching_al(
    monkeypatch,
):
    manager = _exact_probe_manager()
    manager._started = True
    packets = []

    async def scenario():
        manager.loop = asyncio.get_running_loop()
        await manager._acquire_exact_probe_item("010140_NX", "lease-1")

        async def send(raw):
            packet = json.loads(raw)
            packets.append(packet)
            if packet["trnm"] == "REMOVE":
                manager.execute_subscribe(
                    ["010140_NX"],
                    source="other_observation_owner",
                    observation_only=True,
                    realtime_types=("0B", "0D"),
                )

        manager.websocket.send = send
        assert await manager._release_exact_probe_item("010140_NX", "lease-1") is True
        assert "010140_NX" not in manager._registered_item_epochs
        for completion in tuple(manager._pending_loop_futures):
            await asyncio.wrap_future(completion)
        assert manager._registered_item_epochs["010140_NX"] == 8
        assert manager._registered_items_by_code["010140"] == ("010140_AL", "010140_NX")
        assert "010140_NX" not in manager._exact_probe_item_leases

    asyncio.run(scenario())
    assert [packet["trnm"] for packet in packets] == ["REMOVE", "REG"]
    assert all(
        row["item"] == ["010140_NX"] for packet in packets for row in packet["data"]
    )


@pytest.mark.parametrize("symbol", ["005930", "034020", "403870", "196170", "036930"])
def test_dashboard_omits_unused_histories_preserving_exported_route_window(symbol):
    from src.engine.bd_fbuy_accum_pre_scanner import _ws_machine_route_payload

    manager = KiwoomWSManager("test-token")
    target = manager._ensure_target_defaults(symbol)

    class UnusedHistory:
        def __deepcopy__(self, memo):
            pytest.fail("dashboard must not copy unused live history")

    target["price_history"] = UnusedHistory()
    target["recent_trade_ticks_by_route"] = {
        "krx_nxt_integrated": deque(
            [
                {
                    "received_at_ms": 1000000 - i,
                    "transport_epoch": 1,
                    "item": symbol + "_AL",
                    "price": 10000 + i,
                    "volume": 1,
                    "route_sequence": 500 - i,
                }
                for i in range(500)
            ]
        )
    }
    target["recent_depth_ticks_by_route"] = {
        "krx_nxt_integrated": deque(
            [
                {
                    "received_at_ms": 1000000 - i,
                    "transport_epoch": 1,
                    "item": symbol + "_AL",
                    "ask_levels": [{"price": 10001 + i, "quantity": 10}],
                    "bid_levels": [{"price": 10000 + i, "quantity": 10}],
                    "route_sequence": 500 - i,
                }
                for i in range(500)
            ]
        )
    }
    frozen = manager._snapshot_target(target, dashboard_only=True)
    assert "market_data_health" not in frozen  # writer computes health outside WS lock
    assert len(frozen["recent_trade_ticks_by_route"]["krx_nxt_integrated"]) == 120
    assert _ws_machine_route_payload(frozen, now_ts=1000) == _ws_machine_route_payload(
        target, now_ts=1000
    )
    target["recent_trade_ticks_by_route"]["krx_nxt_integrated"][0]["price"] = 1
    assert (
        frozen["recent_trade_ticks_by_route"]["krx_nxt_integrated"][0]["price"] == 10000
    )


def test_dashboard_finishes_projection_outside_ingress_lock(monkeypatch):
    manager = KiwoomWSManager("test-token")
    manager._ensure_target_defaults("005930")
    original = manager._finish_snapshot
    seen = []

    class ImmediateThread:
        def __init__(self, *, target, **kwargs):
            self.target = target

        def start(self):
            self.target()

    # Patch the publisher thread only, keeping an actual probe thread above.
    from threading import Thread

    def finish_without_patched_thread(snapshot, **kwargs):
        acquired = []

        def probe():
            ok = manager.lock.acquire(timeout=0.2)
            acquired.append(ok)
            if ok:
                manager.lock.release()

        thread = Thread(target=probe)
        thread.start()
        thread.join(0.5)
        assert acquired == [True]
        seen.append(True)
        return original(snapshot, **kwargs)

    monkeypatch.setattr(manager, "_finish_snapshot", finish_without_patched_thread)
    monkeypatch.setattr(kiwoom_websocket.threading, "Thread", ImmediateThread)
    monkeypatch.setattr(
        kiwoom_websocket, "write_ws_snapshot", lambda *a, **kw: "fixture"
    )
    manager._maybe_write_dashboard_snapshot()
    assert seen and not manager._dashboard_snapshot_write_inflight


def test_failed_worker_start_resets_publication_guard(monkeypatch):
    manager = KiwoomWSManager("test-token")

    class BrokenThread:
        def __init__(self, **kwargs):
            pass

        def start(self):
            raise RuntimeError("thread unavailable")

    monkeypatch.setattr(kiwoom_websocket.threading, "Thread", BrokenThread)
    with pytest.raises(RuntimeError):
        manager._maybe_write_dashboard_snapshot()
    assert manager._dashboard_snapshot_write_inflight is False


def test_dashboard_uses_capture_clock_when_projection_is_delayed(monkeypatch):
    manager = KiwoomWSManager("test-token")
    clock = [1000.0]
    monkeypatch.setattr(kiwoom_websocket.time, "time", lambda: clock[0])
    row = manager._ensure_target_defaults("034020")
    row["last_realtime_type_ts"] = {"0B": 999.0}
    captured = {}

    class Collector:
        def completed_bar_integrity(self):
            clock[0] = 1003.0
            return {}

    class ImmediateThread:
        def __init__(self, *, target, **kwargs):
            self.target = target

        def start(self):
            self.target()

    def write(frame, **kwargs):
        captured.update(
            now=kwargs["now_ts"], event=frame["034020"]["last_realtime_type_ts"]["0B"]
        )

    manager._micro_reversion_forward_collector = Collector()
    monkeypatch.setattr(kiwoom_websocket.threading, "Thread", ImmediateThread)
    monkeypatch.setattr(kiwoom_websocket, "write_ws_snapshot", write)
    manager._maybe_write_dashboard_snapshot()
    assert captured == {"now": 1000.0, "event": 999.0}
    assert clock[0] == 1003.0


def test_dashboard_preserves_main_projection_without_retired_research(monkeypatch):
    manager = KiwoomWSManager("test-token")
    assert not hasattr(manager, "_capture_episode_research_facts")
    assert not hasattr(manager, "_schedule_episode_research_capture")
    frames = []

    class ImmediateThread:
        def __init__(self, *, target, **kwargs):
            self.target = target

        def start(self):
            self.target()

    monkeypatch.setattr(kiwoom_websocket.threading, "Thread", ImmediateThread)
    monkeypatch.setattr(
        kiwoom_websocket,
        "write_ws_snapshot",
        lambda frame, **kw: frames.append(kw) or "fixture",
    )
    manager._maybe_write_dashboard_snapshot()
    assert not manager._dashboard_snapshot_write_inflight
    assert "episode_research_capture" not in frames[0]["shared_transport_producer"]


def test_frozen_history_keeps_full_tape_and_copies_mutable_children():
    from src.engine.infrastructure.snapshot_copy import (
        freeze_history,
        materialize_history,
    )
    from collections import deque
    from types import SimpleNamespace

    manager = KiwoomWSManager("offline-token")
    target = manager._ensure_target_defaults("005930")
    target["recent_trade_ticks"] = deque(
        (
            freeze_history(
                dict(
                    price=i,
                    volume=1,
                    nested=[{"value": i}],
                    extra=SimpleNamespace(value=i),
                )
            )
            for i in range(500)
        ),
        maxlen=500,
    )
    frozen = manager._snapshot_target(target, _defer_finish=True)
    raw = materialize_history(frozen["recent_trade_ticks"])
    assert isinstance(raw, deque) and raw.maxlen == 500
    target["recent_trade_ticks"].appendleft(freeze_history({"price": 999}))
    first = manager._finish_snapshot(frozen)
    second = manager._finish_snapshot(dict(frozen))
    assert isinstance(
        first["recent_trade_ticks"], list
    )  # Existing final consumer normalization.
    assert (
        len(first["recent_trade_ticks"]) == 500
        and first["recent_trade_ticks"][0]["price"] == 0
    )
    first["recent_trade_ticks"][0]["nested"][0]["value"] = 999
    first["recent_trade_ticks"][0]["extra"].value = 999
    assert second["recent_trade_ticks"][0]["nested"][0]["value"] == 0
    assert second["recent_trade_ticks"][0]["extra"].value == 0


def test_exact_probe_trace_distinguishes_wire_from_normalization_and_freezes_before_release():
    import threading
    from src.engine.kiwoom_websocket import KiwoomWSManager

    manager = KiwoomWSManager.__new__(KiwoomWSManager)
    manager.lock = threading.RLock()
    manager._market_data_transport_epoch = 7
    from src.engine.infrastructure.ws_control_receipts import ControlReceipts

    manager._control_receipts = ControlReceipts()
    manager._exact_probe_item_leases = {"123456_AL": dict(lease_id="lease", epoch=7)}
    manager._micro_reversion_registration_receipt = {
        "items": {
            "123456_AL": dict(registration_transport_epoch=7, receipt_count_by_type={})
        }
    }
    trace = manager.exact_probe_source_trace("123456_AL", "lease")
    assert trace["first_unobserved_boundary_by_type"]["0B"] == "wire_receive"
    manager._record_source_wire_receipt(
        {"item": "123456_AL", "type": "0B", "values": {}}, 100, transport_epoch=7
    )
    trace = manager.exact_probe_source_trace("123456_AL", "lease")
    assert trace["first_unobserved_boundary_by_type"]["0B"] == "normalized_receive"
    assert trace["broker_ack_observed"] is None and trace["order_authority"] is False
    manager._record_source_wire_receipt(
        {"item": "123456_NX", "type": "0D"}, 101, transport_epoch=7
    )
    manager._micro_reversion_registration_receipt["items"]["123456_AL"][
        "receipt_count_by_type"
    ]["0B"] = 1
    complete = manager.exact_probe_source_trace("123456_AL", "lease")
    assert (
        complete["first_unobserved_boundary_by_type"]["0B"]
        == "native_consumer_not_proven_here"
    )
    manager._exact_probe_item_leases.clear()
    manager._micro_reversion_registration_receipt["items"].clear()
    assert complete["lease"]["wire_receipt_count_by_type"] == {"0B": 1}
    assert trace["registration"]["receipt_count_by_type"] == {}
    assert (
        manager.exact_probe_source_trace("123456_AL", "lease")["lease_bound"] is False
    )


@pytest.mark.parametrize("kind", ["0B", "0D"])
@pytest.mark.parametrize(
    "outcome",
    [
        "enqueued",
        "invalid_depth_snapshot",
        "queue_full",
        "disabled",
        "exception",
        "unavailable",
        "unknown",
    ],
)
def test_exact_probe_trace_accounts_for_collector_outcomes(kind, outcome):
    from types import SimpleNamespace
    from src.engine.scalping.micro_reversion.forward_collector import (
        ProducerCanaryResult,
    )

    manager = _exact_probe_manager()
    lease = dict(lease_id="lease", epoch=7, interval_started_epoch=99.0)
    manager._exact_probe_item_leases["123456_AL"] = lease
    manager._market_data_transport_epoch = 7
    source = dict(
        item="123456_AL",
        transport_epoch=7,
        route_sequence=1,
        received_at_ms=100000,
        market_route="krx_nxt_integrated",
    )
    data = {
        "last_realtime_type_item": {kind: "123456_AL"},
        "last_trade_tick" if kind == "0B" else "last_depth_tick": source,
    }

    def observe(*args, **kwargs):
        if outcome == "exception":
            raise RuntimeError("collector failure")
        return None if outcome == "unknown" else ProducerCanaryResult(outcome)

    manager._micro_reversion_forward_collector = (
        None
        if outcome == "unavailable"
        else SimpleNamespace(observe_kiwoom_0b=observe, observe_kiwoom_0d=observe)
    )
    manager._observe_micro_reversion_forward("123456", data, realtime_type=kind)
    result = {
        "exception": "callback_error",
        "unavailable": "collector_unavailable",
        "unknown": "unobservable_result",
    }.get(outcome, outcome)
    trace = manager.exact_probe_source_trace("123456_AL", "lease")
    assert trace["lease"]["collector_result_counts_by_type"] == {kind: {result: 1}}
    assert trace["lease"]["collector_last_result_by_type"][kind] == dict(
        result=result, route_sequence=1, received_at_ms=100000
    )
    # A detached terminal trace survives native lease cleanup.
    lease.clear()
    assert trace["lease"]["collector_result_counts_by_type"][kind][result] == 1
    assert trace["order_authority"] is False


@pytest.mark.parametrize(
    "damage",
    [
        "epoch",
        "item",
        "route",
        "replacement",
        "reconnect",
        "before_registration",
        "missing_interval",
        "bad_clock",
        "lease_id",
    ],
)
def test_collector_outcome_never_credits_another_probe_lease(damage):
    from types import SimpleNamespace
    from src.engine.scalping.micro_reversion.forward_collector import (
        ProducerCanaryResult,
    )

    manager = _exact_probe_manager()
    manager._market_data_transport_epoch = 7
    lease = dict(lease_id="lease", epoch=7, interval_started_epoch=99.0)
    manager._exact_probe_item_leases["123456_AL"] = lease
    source = dict(
        item="123456_AL",
        transport_epoch=7,
        route_sequence=1,
        received_at_ms=100000,
        market_route="krx_nxt_integrated",
    )
    if damage == "epoch":
        source["transport_epoch"] = 6
    if damage == "item":
        source["item"] = "123456_NX"
    if damage == "route":
        source["market_route"] = "nxt_only"
    if damage == "before_registration":
        source["received_at_ms"] = 98000
    if damage == "missing_interval":
        lease.pop("interval_started_epoch")
    if damage == "bad_clock":
        source["received_at_ms"] = float("nan")

    def observe(*args, **kwargs):
        if damage == "replacement":
            manager._exact_probe_item_leases["123456_AL"] = dict(
                lease_id="new", epoch=7
            )
        if damage == "reconnect":
            manager._market_data_transport_epoch = 8
        if damage == "lease_id":
            lease["lease_id"] = "new"
        return ProducerCanaryResult.ENQUEUED

    manager._micro_reversion_forward_collector = SimpleNamespace(
        observe_kiwoom_0d=observe
    )
    manager._observe_micro_reversion_forward(
        "123456",
        {"last_realtime_type_item": {"0D": "123456_AL"}, "last_depth_tick": source},
        realtime_type="0D",
    )
    assert "collector_result_counts_by_type" not in lease
    assert (
        "collector_result_counts_by_type"
        not in manager._exact_probe_item_leases["123456_AL"]
    )


def test_probe_collector_accounting_exceeds_diagnostic_tail_without_growing_keys():
    from types import SimpleNamespace
    from src.engine.scalping.micro_reversion.forward_collector import (
        ProducerCanaryResult,
    )

    manager = _exact_probe_manager()
    manager._market_data_transport_epoch = 7
    lease = dict(lease_id="lease", epoch=7, interval_started_epoch=99.0)
    manager._exact_probe_item_leases["123456_AL"] = lease
    manager._micro_reversion_forward_collector = SimpleNamespace(
        observe_kiwoom_0d=lambda *a, **kw: ProducerCanaryResult.INVALID_DEPTH_SNAPSHOT
    )
    source = dict(
        item="123456_AL",
        transport_epoch=7,
        route_sequence=1,
        received_at_ms=100000,
        market_route="krx_nxt_integrated",
    )
    for sequence in range(1, 201):
        source["route_sequence"] = sequence
        manager._observe_micro_reversion_forward(
            "123456",
            {"last_realtime_type_item": {"0D": "123456_AL"}, "last_depth_tick": source},
            realtime_type="0D",
        )
    assert lease["collector_result_counts_by_type"] == {
        "0D": {"invalid_depth_snapshot": 200}
    }
    assert lease["collector_first_non_enqueued_by_type"]["0D"]["route_sequence"] == 1
    assert lease["collector_last_result_by_type"]["0D"]["route_sequence"] == 200


def test_native_depth_ingress_records_probe_rejection_without_reentering_snapshot_lock(
    monkeypatch,
):
    import threading
    from types import SimpleNamespace
    from src.engine.scalping.micro_reversion.forward_collector import (
        ProducerCanaryResult,
    )

    class NoReentry:
        def __init__(self):
            self.lock = threading.Lock()

        def __enter__(self):
            assert self.lock.acquire(blocking=False), "snapshot lock reentry"

        def __exit__(self, *args):
            self.lock.release()

    manager = _exact_probe_manager()
    monkeypatch.setattr(manager, "_maybe_write_dashboard_snapshot", lambda: None)
    manager.lock = NoReentry()
    manager.subscribed_codes.add("123456")
    now = _epoch_at_090010()
    monkeypatch.setattr(kiwoom_websocket.time, "time", lambda: now)
    manager._exact_probe_item_leases["123456_AL"] = dict(
        lease_id="lease", epoch=8, interval_started_epoch=now - 1
    )
    manager._micro_reversion_observation_only_items.add("123456_AL")
    manager._micro_reversion_forward_collector = SimpleNamespace(
        flags=SimpleNamespace(depth_capture_active=True),
        observe_kiwoom_0d=lambda *a, **kw: ProducerCanaryResult.INVALID_DEPTH_SNAPSHOT,
    )
    asyncio.run(
        manager._handle_message(
            json.dumps(
                {
                    "trnm": "REAL",
                    "data": [
                        {
                            "type": "0D",
                            "item": "123456_AL",
                            "values": {
                                "21": "090010",
                                "41": "10110",
                                "61": "100",
                                "51": "10100",
                                "71": "100",
                            },
                        }
                    ],
                }
            )
        )
    )
    trace = manager.exact_probe_source_trace("123456_AL", "lease")
    assert trace["lease"]["collector_result_counts_by_type"] == {
        "0D": {"invalid_depth_snapshot": 1}
    }


def _fresh_continuity_transfer():
    import time
    from src.engine.scalping.continuous_reversal_postclose import digest

    manager, payload, item = _zero_base_native_transfer("krx_nxt_integrated")
    manager._exact_probe_item_leases[item]["interval_started_epoch"] = (
        time.time() - 0.01
    )

    async def feed():
        for _ in range(4):
            await manager._handle_message(
                json.dumps(
                    {
                        "trnm": "REAL",
                        "data": [
                            {
                                "type": "0D",
                                "item": item,
                                "values": {
                                    "21": "133500",
                                    "41": "10010",
                                    "51": "9990",
                                    "61": "10",
                                    "71": "10",
                                },
                            },
                            {
                                "type": "0B",
                                "item": item,
                                "values": {"10": "10000", "15": "+1", "228": "101.5"},
                            },
                        ],
                    }
                )
            )

    asyncio.run(feed())
    expected = payload["native_observation"]
    event = expected["snapshot"][0]
    event.update(
        epoch=time.time(),
        signal_id="original-signal",
        event_id="original-event",
        native_sequence=4,
    )
    expected["snapshot_sha256"] = digest(expected["snapshot"])
    return manager, payload, item


def test_native_source_continuity_keeps_original_buffer_precheck_and_receive_clocks():
    import time
    from src.engine.scalping.native_source_continuity import source_ready
    from src.engine import sniper_state_handlers as handlers

    manager, payload, item = _fresh_continuity_transfer()
    original = manager.get_exact_item_data(payload["code"], item)
    stored = manager._micro_reversion_observation_route_data[item]
    assert manager.adopt_zero_base_probe_target(payload)
    assert (
        manager.realtime_data[payload["code"]] is stored
    )  # One live writer, no copy/replay.
    assert item not in manager._micro_reversion_observation_route_data
    now = time.time()
    target = {
        **payload,
        "id": 92,
        "strategy": "SCALPING",
        "status": "WATCHING",
        "position_tag": "SCANNER",
        "added_time": now,
        "entry_armed_at_epoch": now,
        "scanner_attach_epoch": now,
        "source_signature": "PRICE_JUMP_START",
    }
    current = manager.get_latest_data(payload["code"])
    assert current["strength_momentum_history"] == original["strength_momentum_history"]
    assert current["last_realtime_type_ts"] == original["last_realtime_type_ts"]
    assert len(current["strength_momentum_history"]) == 4
    assert source_ready(target, current, now=time.time())
    fields = handlers._scanner_fast_precheck_fields(
        target, now_ts=time.time(), code=payload["code"], ws_data=current
    )
    assert fields["scanner_native_source_continuity_ready"] is True
    assert fields["fast_precheck_post_attach_entry_realtime"] is False
    assert fields["fast_precheck_reason"] != "awaiting_first_post_attach_trade_input"
    assert asyncio.run(manager._release_exact_probe_item(item, "lease-1"))
    assert manager.realtime_data[payload["code"]] is stored
    assert manager.websocket.sent == []


@pytest.mark.parametrize(
    "damage",
    [
        "stale",
        "missing_depth",
        "history_epoch",
        "history_route",
        "history_sequence",
        "future",
        "missing_signal",
        "missing_digest",
    ],
)
def test_native_source_continuity_never_promotes_unverified_observation(damage):
    from src.engine.infrastructure.snapshot_copy import (
        freeze_history,
        materialize_history,
    )

    manager, payload, item = _fresh_continuity_transfer()
    source = manager._micro_reversion_observation_route_data[item]
    typed = source["realtime_type_snapshots_by_route"]["_AL|krx_nxt_integrated"]
    if damage == "stale":
        typed["0B"]["observed_epoch"] -= 4
    elif damage == "missing_depth":
        typed.pop("0D")
    elif damage == "future":
        typed["0B"]["observed_epoch"] += 5
    elif damage == "missing_signal":
        payload["native_observation"]["snapshot"][0].pop("signal_id")
    elif damage == "missing_digest":
        payload["native_observation"].pop("snapshot_sha256")
    else:
        rows = materialize_history(freeze_history(source["strength_momentum_history"]))
        key, value = {
            "history_epoch": ("transport_epoch", 7),
            "history_route": ("market_route", "krx_only"),
            "history_sequence": ("route_sequence", 1),
        }[damage]
        rows[-1][key] = value
        source["strength_momentum_history"] = rows
    assert manager.adopt_zero_base_probe_target(payload)  # Local custody only.
    assert "_zero_base_source_continuity" not in payload
    assert manager.get_latest_data(payload["code"]) == {}


@pytest.mark.parametrize(
    "damage",
    ["pid", "epoch", "lease", "route", "signal", "deadline", "stale", "source_receipt"],
)
def test_native_source_continuity_current_readiness_cannot_reuse_old_authority(damage):
    import time
    from copy import deepcopy
    from src.engine.scalping.native_source_continuity import source_ready

    manager, payload, item = _fresh_continuity_transfer()
    assert manager.adopt_zero_base_probe_target(payload)
    data = manager.get_latest_data(payload["code"])
    target = deepcopy(payload)
    now = time.time()
    if damage == "pid":
        target["native_observation"]["observer_pid"] += 1
    elif damage == "epoch":
        data["market_data_transport_epoch"] += 1
    elif damage == "lease":
        target["physical_probe_lease_id"] = "new"
    elif damage == "route":
        target["market_data_route"] = "nxt_only"
    elif damage == "signal":
        target["native_observation"]["snapshot"][0]["signal_id"] = "new"
    elif damage == "deadline":
        target["native_observation"]["deadline_perf"] = time.perf_counter() - 1
    elif damage == "stale":
        now += 3.5
    elif damage == "source_receipt":
        data["_zero_base_source_continuity"]["history_count"] += 1
    assert not source_ready(target, data, now=now)
    assert data["strength_momentum_history"]  # Observed history is not erased.


@pytest.mark.parametrize("kind", ["REG", "REMOVE"])
@pytest.mark.parametrize("code", [0, 1])
def test_control_response_retained_before_send_returns(kind, code):
    manager = _exact_probe_manager()

    async def send(_packet):
        await manager._handle_message(
            json.dumps({"trnm": kind, "return_code": code, "return_msg": "fixture"})
        )

    manager.websocket.send = send
    asyncio.run(
        manager._send_control_packet(
            {
                "trnm": kind,
                "grp_no": "1",
                "data": [{"item": ["010140_AL"], "type": ["0B"]}],
            }
        )
    )
    row = manager._control_receipts.projection(item="010140_AL", epoch=8, kind=kind)
    assert row["broker_ack_observed"] is True
    assert row["broker_result"] == ("success" if code == 0 else "rejected")
    assert row["request"]["send_state"] == "sent"
    assert (
        manager._registered_item_epochs["010140_AL"] == 8
    )  # No unsolicited unsubscribe.


def test_control_ambiguous_bootstrap_duplicate_late_and_old_epoch_are_not_item_ack():
    manager = _exact_probe_manager()

    async def scenario():
        for item, group in (("", "2"), ("", "3"), ("010140_AL", "1")):
            await manager._send_control_packet(
                {
                    "trnm": "REG",
                    "grp_no": group,
                    "data": [{"item": [item], "type": ["0B"]}],
                }
            )
        for _ in range(4):
            await manager._handle_message(json.dumps({"trnm": "REG", "return_code": 0}))
        assert (
            manager._control_receipts.projection(item="010140_AL", epoch=8)[
                "broker_ack_observed"
            ]
            is None
        )
        manager._market_data_transport_epoch = 9
        await manager._send_control_packet(
            {
                "trnm": "REG",
                "grp_no": "1",
                "data": [{"item": ["010140_AL"], "type": ["0B"]}],
            }
        )
        await manager._handle_message(
            json.dumps({"trnm": "REG", "return_code": 1}), transport_epoch=8
        )
        assert (
            manager._control_receipts.projection(item="010140_AL", epoch=9)[
                "broker_ack_observed"
            ]
            is None
        )
        await manager._handle_message(
            json.dumps({"trnm": "REG", "return_code": 0}), transport_epoch=9
        )
        assert (
            manager._control_receipts.projection(item="010140_AL", epoch=9)[
                "broker_result"
            ]
            == "success"
        )

    asyncio.run(scenario())


def test_control_bounded_history_never_makes_evicted_requests_unique():
    manager = _exact_probe_manager()

    async def scenario():
        for _ in range(140):
            await manager._send_control_packet(
                {
                    "trnm": "REG",
                    "grp_no": "1",
                    "data": [{"item": ["010140_AL"], "type": ["0B"]}],
                }
            )
        await manager._handle_message(json.dumps({"trnm": "REG", "return_code": 1}))

    asyncio.run(scenario())
    assert len(manager._control_receipts.requests) == 128
    assert manager._control_receipts.responses[-1]["attribution"] == "unknown"


def test_control_uncertain_send_and_unsolicited_response_cannot_claim_later_success():
    manager = _exact_probe_manager()

    async def fail(_packet):
        raise RuntimeError("fixture uncertain send")

    async def scenario():
        await manager._handle_message(json.dumps({"trnm": "REG", "return_code": 0}))
        manager.websocket.send = fail
        with pytest.raises(RuntimeError):
            await manager._send_control_packet(
                {
                    "trnm": "REG",
                    "grp_no": "1",
                    "data": [{"item": ["010140_AL"], "type": ["0B"]}],
                }
            )
        await manager._handle_message(json.dumps({"trnm": "REG", "return_code": 0}))

    asyncio.run(scenario())
    trace = manager._control_receipts.projection(item="010140_AL", epoch=8)
    assert trace["request"]["send_state"] == "uncertain"
    assert trace["broker_ack_observed"] is None
    assert trace["connection_responses"][-1]["attribution"] == "unknown"


def test_native_continuity_real_after_adoption_appends_once_and_keeps_history():
    manager, payload, item = _fresh_continuity_transfer()
    assert manager.adopt_zero_base_probe_target(payload)
    original = manager.get_latest_data(payload["code"])
    asyncio.run(
        manager._handle_message(
            json.dumps(
                {
                    "trnm": "REAL",
                    "data": [
                        {
                            "type": "0B",
                            "item": item,
                            "values": {"10": "10001", "15": "+2", "228": "102"},
                        }
                    ],
                }
            )
        )
    )
    after = manager.get_latest_data(payload["code"])
    assert (
        after["strength_momentum_history"][:-1] == original["strength_momentum_history"]
    )
    assert len(after["strength_momentum_history"]) == 5
    assert after["strength_momentum_history"][-1]["route_sequence"] == 5
    assert after["curr"] == 10001
    assert item not in manager._micro_reversion_observation_route_data
    assert manager.websocket.sent == []


def test_bound_rejection_preserves_local_registration_and_targets_only_original_lease():
    manager = KiwoomWSManager("test-token")
    manager.websocket = _FakeWS([])
    manager._session_ready.set()
    manager._market_data_transport_epoch = 8

    async def send(_packet):
        await manager._handle_message(
            json.dumps(
                {"trnm": "REG", "return_code": 1, "return_msg": "fixture refusal"}
            )
        )

    manager.websocket.send = send
    result = asyncio.run(
        manager._acquire_exact_probe_item("010140_AL", "original-lease")
    )
    assert result["registered"] is True  # This is still the local-send registry.
    assert result["server_registration_rejected"] is True
    assert (
        manager.exact_probe_control_failure("010140_AL", "original-lease")
        == "exact_probe_registration_rejected"
    )
    assert manager.exact_probe_control_failure("010140_AL", "replacement-lease") == ""
    assert manager._registered_item_epochs["010140_AL"] == 8


def test_connection_projection_preserves_remove_response_after_registry_cleanup():
    manager = _exact_probe_manager()
    manager._exact_probe_item_leases["010140_AL"] = {"lease_id": "lease-1", "epoch": 8}

    async def scenario():
        assert await manager._release_exact_probe_item("010140_AL", "lease-1")
        await manager._handle_message(json.dumps({"trnm": "REMOVE", "return_code": 0}))

    asyncio.run(scenario())
    assert "010140_AL" not in manager._registered_item_epochs
    with manager.lock:
        snapshot = manager._control_receipts.snapshot()
    assert snapshot["requests"][-1]["lease_ids"]["010140_AL"] == "lease-1"
    assert snapshot["responses"][-1]["trnm"] == "REMOVE"
    assert snapshot["responses"][-1]["broker_result"] == "success"
    assert snapshot["order_authority"] is False
    snapshot["responses"][-1]["broker_result"] = "changed-copy"
    assert manager._control_receipts.responses[-1]["broker_result"] == "success"


@pytest.mark.parametrize(
    "item,other",
    [
        ("036930", "036930_NX"),
        ("036930_NX", "036930"),
        ("036930_AL", "036930_NX"),
    ],
)
def test_holding_repair_pins_exact_primary_without_borrowing_other_route(
    monkeypatch, item, other
):
    monkeypatch.setattr(
        "src.utils.kiwoom_utils.get_effective_kiwoom_code",
        lambda code: pytest.fail("eligible exact item rewritten"),
    )
    manager = KiwoomWSManager("test-token")
    manager.websocket = _FakeWS([])
    manager._session_ready.set()
    manager._market_data_transport_epoch = 7
    monkeypatch.setattr(manager, "_integrated_aftermarket_route_required", lambda: True)
    monkeypatch.setattr(manager, "_maybe_write_dashboard_snapshot", lambda: None)
    monkeypatch.setattr(
        manager, "_observe_micro_reversion_forward", lambda *a, **k: None
    )
    asyncio.run(
        manager._send_reg(
            [item],
            source="holding_ws_freshness_repair",
            include_alternate_route=False,
            realtime_types=("0B", "0D"),
        )
    )
    assert manager._runtime_primary_items_by_code["036930"] == item
    assert "036930" not in manager._implicit_runtime_route_codes
    assert json.loads(manager.websocket.sent[-1])["data"][0]["item"] == [item]
    assert manager.get_exact_item_data("036930", item)["curr"] == 0

    def receive(source, price):
        asyncio.run(
            manager._handle_message(
                json.dumps(
                    {
                        "trnm": "REAL",
                        "data": [
                            {
                                "type": "0B",
                                "item": source,
                                "values": {"10": str(price), "15": "+1"},
                            }
                        ],
                    }
                )
            )
        )

    receive(item, 176000)
    before = manager.get_exact_item_data("036930", item)
    receive(other, 180000)
    after = manager.get_exact_item_data("036930", item)
    assert after["curr"] == before["curr"] == 176000
    assert after["last_realtime_type_ts"]["0B"] == before["last_realtime_type_ts"]["0B"]
    assert after["last_realtime_type_item"]["0B"] == item
    assert manager._micro_reversion_observation_route_data[other]["curr"] == 180000
    manager._market_data_transport_epoch = 8
    assert manager.get_exact_item_data("036930", item) == {}
    asyncio.run(manager._send_reg([item], source="runtime_subscription_reconnect"))
    assert json.loads(manager.websocket.sent[-1])["data"][0]["item"] == [item]
    assert manager._registered_item_epochs[item] == 8
    assert "036930" not in manager._implicit_runtime_route_codes
    assert manager._runtime_primary_items_by_code["036930"] == item


def test_probe_connection_activity_keeps_empty_item_unknown_and_rejects_old_transport():
    import threading
    from src.engine.infrastructure.ws_control_receipts import ControlReceipts

    manager = KiwoomWSManager.__new__(KiwoomWSManager)
    manager.lock = threading.RLock()
    manager._market_data_transport_epoch = 7
    manager._control_receipts = ControlReceipts()
    manager._exact_probe_item_leases = {}
    manager._micro_reversion_registration_receipt = {"items": {}}
    peer = {"item": "005930_AL", "type": "0B"}
    manager._record_source_wire_receipt(peer, 90.0, transport_epoch=7)
    manager._exact_probe_item_leases["123456_AL"] = dict(
        lease_id="lease",
        epoch=7,
        interval_started_epoch=100.0,
        connection_wire_baseline=dict(manager._probe_connection_wire_state["counts"]),
    )
    manager._micro_reversion_registration_receipt["items"]["123456_AL"] = dict(
        registration_transport_epoch=7, receipt_count_by_type={}
    )
    manager._record_source_wire_receipt(peer, 101.0, transport_epoch=7)
    asyncio.run(
        manager._handle_message(
            json.dumps({"trnm": "REAL", "data": [{"item": "123456_AL", "type": "0B"}]}),
            transport_epoch=6,
        )
    )
    trace = manager.exact_probe_source_trace("123456_AL", "lease")
    assert trace["first_unobserved_boundary_by_type"]["0B"] == "wire_receive"
    assert trace["broker_ack_observed"] is None
    assert trace["connection_activity"]["counts_by_route_type"] == {
        "krx_nxt_integrated:0B": 1
    }
    assert (
        trace["connection_activity"]["last_by_route_type"]["krx_nxt_integrated:0B"][
            "item"
        ]
        == "005930_AL"
    )
    assert not trace["connection_activity"]["item_ack_proven"]
    manager._market_data_transport_epoch = 8
    manager._record_source_wire_receipt(peer, 103.0, transport_epoch=8)
    assert (
        manager.exact_probe_source_trace("123456_AL", "lease")["connection_activity"]
        is None
    )
    assert (
        trace["connection_activity"]["counts_by_route_type"]["krx_nxt_integrated:0B"]
        == 1
    )
