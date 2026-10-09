from types import SimpleNamespace
from concurrent.futures import Future
import time

import pytest

from src.engine.scalping.zero_base_probe import (
    exact_probe_rest_source_issue, exact_probe_rest_sources, exact_probe_ws_data,
    probe_registration_receipt,
    run_zero_base_probe,
    wait_for_exact_probe_ws_data,
)


def _completed_registration():
    future = Future()
    future.set_result(None)
    return future


def _snapshot(route="krx_only", item="123456", epoch=11.0):
    key = {"krx_only": "KRX|krx_only", "nxt_only": "_NX|nxt_only",
           "krx_nxt_integrated": "_AL|krx_nxt_integrated"}[route]
    return {
        "market_data_transport_epoch": 3,
        "last_realtime_type_item": {"0B": item, "0D": item},
        "last_realtime_type_market_route": {"0B": route, "0D": route},
        "realtime_type_snapshots_by_route": {key: {
            "0B": {"item": item, "market_route": route,
                   "transport_epoch": 3, "observed_epoch": epoch,
                   "current_price": 10000},
            "0D": {"item": item, "market_route": route,
                   "transport_epoch": 3, "observed_epoch": epoch,
                   "orderbook": {"asks": [{"price": 10010, "volume": 10}],
                                 "bids": [{"price": 10000, "volume": 10}]}},
        }},
    }


def test_probe_rejects_cross_route_or_old_transport_without_machine_call():
    good, reason = exact_probe_ws_data(_snapshot(), code="123456", route="krx_only", after_epoch=10)
    assert reason == "ready" and good["curr"] == 10000
    missing_transport = _snapshot()
    missing_transport.pop("market_data_transport_epoch")
    missing_transport["realtime_type_snapshots_by_route"]["KRX|krx_only"]["0B"]["transport_epoch"] = None
    missing_transport["realtime_type_snapshots_by_route"]["KRX|krx_only"]["0D"]["transport_epoch"] = None
    assert exact_probe_ws_data(missing_transport, code="123456", route="krx_only", after_epoch=10)[1] == "transport_epoch_missing"
    assert exact_probe_ws_data(_snapshot(epoch=9), code="123456", route="krx_only", after_epoch=10)[1] == "0B_stale_or_route_conflict"
    assert exact_probe_ws_data(_snapshot(route="nxt_only", item="123456_NX"), code="123456", route="krx_only", after_epoch=10)[1] == "route_snapshot_missing"
    mixed = _snapshot()
    mixed["last_realtime_type_item"]["0D"] = "123456_NX"
    assert exact_probe_ws_data(mixed, code="123456", route="krx_only", after_epoch=10)[1] == "aggregate_route_conflict"
    nxt, reason = exact_probe_ws_data(
        _snapshot(route="nxt_only", item="123456_NX"),
        code="123456", route="nxt_only", after_epoch=10,
    )
    assert reason == "ready" and nxt["market_data_route"] == "nxt_only"
    integrated, reason = exact_probe_ws_data(
        _snapshot(route="krx_nxt_integrated", item="123456_AL"),
        code="123456", route="krx_nxt_integrated", after_epoch=10,
    )
    assert reason == "ready" and integrated["effective_venue"] == "SOR"


def test_probe_freshness_allows_three_seconds_but_rejects_older_receipt():
    snapshot = _snapshot(route="nxt_only", item="123456_NX", epoch=10.5)
    ready, reason = exact_probe_ws_data(
        snapshot, code="123456", route="nxt_only", after_epoch=10,
        now_epoch=13.5,
    )
    assert reason == "ready" and ready
    blocked, reason = exact_probe_ws_data(
        snapshot, code="123456", route="nxt_only", after_epoch=10,
        now_epoch=13.501,
    )
    assert not blocked and reason == "0B_age_exceeded"


@pytest.mark.parametrize("route,item,key", [
    ("nxt_only", "123456_NX", "_NX|nxt_only"),
    ("krx_nxt_integrated", "123456_AL", "_AL|krx_nxt_integrated"),
])
def test_exact_probe_feature_ticks_exclude_aggregate_and_old_subscription(
    route, item, key,
):
    snapshot = _snapshot(route=route, item=item)
    snapshot["recent_trade_ticks"] = [
        {"item": "123456", "market_route": "krx_only", "price": 99999}
    ]
    snapshot["recent_trade_ticks_by_route"] = {key: [
        {"item": item, "market_route": route, "transport_epoch": 3,
         "received_at_ms": 10800, "price": 10000},
        {"item": item, "market_route": route, "transport_epoch": 3,
         "received_at_ms": 9900, "price": 10001},
        {"item": item, "market_route": route, "transport_epoch": 2,
         "received_at_ms": 10900, "price": 10002},
        {"item": "123456", "market_route": "krx_only", "transport_epoch": 3,
         "received_at_ms": 10900, "price": 10003},
        {"item": item, "market_route": route, "market_suffix": "_NX"
         if route == "krx_nxt_integrated" else "_AL", "transport_epoch": 3,
         "received_at_ms": 10900, "price": 10004},
    ]}
    data, reason = exact_probe_ws_data(
        snapshot, code="123456", route=route, after_epoch=10,
    )
    assert reason == "ready"
    assert [tick["price"] for tick in data["recent_trade_ticks"]] == [10000]
    assert data["zero_base_probe_exact_tick_source"] == key
    assert data["zero_base_probe_exact_tick_filter"] == {
        "source_row_count": 5, "accepted_row_count": 1,
        "rejected_counts": {"item_or_route": 2, "transport_epoch": 1,
                            "before_registration": 1},
    }
    assert snapshot["recent_trade_ticks"][0]["price"] == 99999


def test_integrated_probe_never_reuses_plain_route_subscription():
    ws = SimpleNamespace(subscribed_codes={"123456"},
                         _registered_items_by_code={"123456": ("123456",)})
    result = run_zero_base_probe(
        {"claim": {"code": "123456", "route": "krx_nxt_integrated",
                   "observed_epoch": 10},
         "candidate": {"code": "123456", "route": "krx_nxt_integrated"}},
        ws_manager=ws, ai_engine=object(), token="token", now=lambda: 11,
    )
    assert result["reason"] == "exact_route_subscription_conflict"
    assert result["result"] == "source_unavailable"


@pytest.mark.parametrize("action", ["ENTER_NOW", "SOURCE_INVALID"])
def test_machine_only_probe_passes_only_exact_fresh_input_and_releases_ws(monkeypatch, action):
    import src.engine.scalping.zero_base_probe as module

    monkeypatch.setattr(module, "resolve_entry_candle_session", lambda: "KRX_REGULAR")
    monkeypatch.setattr(module, "resolve_entry_candle_request_code", lambda *_args, **_kwargs: "123456")
    calls = []
    ws = SimpleNamespace(
        subscribed_codes=set(),
        _registered_items_by_code={},
        _registered_item_epochs={},
        _registered_item_types={},
        _market_data_transport_epoch=3,
        wait_for_data=lambda *args, **kwargs: _snapshot(epoch=11),
        get_latest_data=lambda *_args, **_kwargs: _snapshot(epoch=11),
    )
    def subscribe(*args, **kwargs):
        calls.append((args, kwargs))
        ws.subscribed_codes.add("123456")
        ws._registered_items_by_code["123456"] = ("123456",)
        ws._registered_item_epochs["123456"] = 3
        ws._registered_item_types["123456"] = ("0B", "0D")
        return _completed_registration()
    ws.execute_subscribe = subscribe
    machine_calls = []
    context_calls = []

    class Machine:
        def analyze_target(self, *args, **kwargs):
            machine_calls.append(kwargs)
            return {"machine_evaluation_status": "assessed",
                    "entry_mechanistic_action": action,
                    "machine_bundle_sha256": "a" * 64,
                    "machine_capture_status": "captured",
                    "machine_observation_sha256": "c" * 64,
                    "mechanistic_entry_assessment": {"reason": "test_pass"}}

    result = run_zero_base_probe(
        {"claim": {"code": "123456", "route": "krx_only", "observed_epoch": 10,
                   "source_sha256": "b" * 64},
         "candidate": {"code": "123456", "route": "krx_only", "name": "TEST"}},
        ws_manager=ws, ai_engine=Machine(), token="token", now=lambda: 11,
        tick_fetcher=lambda *_args, **_kwargs: [{
            "price": 10000, "request_code": "123456", "rest_received_ts_ms": 11000,
        }],
        candle_fetcher=lambda *_args, **_kwargs: (
            [{"close": 10000}], {"request_code": "123456", "rest_received_ts_ms": 11000},
        ),
        context_builder=lambda *_args, **kwargs: (
            context_calls.append(kwargs), {"ready": True}
        )[1],
        release_ws=lambda code, item: calls.append(("release", code, item)),
        ws_wait_min_exact_0b_count=0,
    )
    assert result["result"] == ("assessed" if action == "ENTER_NOW" else "source_unavailable")
    assert result["machine_action"] == action
    assert result["machine_observation_id"] == "c" * 64
    assert result["machine_observation_sha256"] == "c" * 64
    assert result["machine_capture_status"] == "captured"
    assert result["actual_order_submitted"] is False
    assert machine_calls[0]["machine_only"] is True
    assert context_calls[0]["source_meta"]["multi_timeframe_auxiliary_fetch"] is False
    assert context_calls[0]["include_investor_source"] is False
    assert calls[-1] == ("release", "123456", "123456")


def test_probe_attach_receipt_keeps_capture_digest_without_order_authority(monkeypatch):
    from src.engine import kiwoom_sniper_v2 as sniper

    emitted = []
    monkeypatch.setattr(sniper, "emit_pipeline_event", lambda *args, **kwargs:
                        emitted.append((args, kwargs)))
    sniper._zero_base_attach_receipt({
        "claim": {"code": "005930", "route": "krx_nxt_integrated",
                  "source_sha256": "a" * 64},
        "machine_observation_sha256": "b" * 64,
    }, outcome="attached", reason="committed")
    assert emitted[-1][0][3] == "zero_base_watch_attach"
    assert emitted[-1][1]["fields"]["machine_observation_sha256"] == "b" * 64
    assert emitted[-1][1]["fields"]["actual_order_submitted"] is False
    sniper._zero_base_inbox_attach_receipt({
        "code": "005930", "market_data_route": "krx_nxt_integrated",
        "source_signature": "ZERO_BASE_DISCOVERY:" + "a" * 64,
        "zero_base_probe_machine_observation_sha256": "b" * 64,
    }, outcome="attached", reason="committed")
    assert emitted[-1][1]["fields"]["machine_observation_sha256"] == "b" * 64


def test_ready_ws_still_observes_minimum_warmup():
    ws = SimpleNamespace(get_latest_data=lambda *_args: _snapshot(epoch=11))
    data, observation, reason = wait_for_exact_probe_ws_data(
        ws, code="123456", route="krx_only", after_epoch=10,
        now=lambda: 11, timeout_sec=0.2, min_warmup_sec=0.04,
        poll_interval_sec=0.005,
    )
    assert reason == "ready" and data
    assert observation["wait_ms"] >= 40
    assert observation["min_warmup_ms"] == 40


def test_warmup_longer_than_lease_never_promotes_early_ready_snapshot():
    ws = SimpleNamespace(get_latest_data=lambda *_args: _snapshot(epoch=11))
    data, observation, reason = wait_for_exact_probe_ws_data(
        ws, code="123456", route="krx_only", after_epoch=10,
        now=lambda: 11, timeout_sec=0.01, min_warmup_sec=0.05,
        poll_interval_sec=0.005,
    )
    assert not data and reason == "warmup_timeout"
    assert observation["wait_reason"] == "warmup_timeout"


def test_recheck_can_retain_owned_exact_subscription_for_one_followup(monkeypatch):
    import src.engine.scalping.zero_base_probe as module

    monkeypatch.setattr(module, "resolve_entry_candle_session", lambda: "KRX_REGULAR")
    monkeypatch.setattr(module, "resolve_entry_candle_request_code", lambda *_args, **_kwargs: "123456")
    ws = SimpleNamespace(
        subscribed_codes=set(), _registered_items_by_code={},
        _registered_item_epochs={}, _registered_item_types={},
        _market_data_transport_epoch=3,
        get_latest_data=lambda *_args: _snapshot(epoch=11),
    )

    def subscribe(*_args, **_kwargs):
        ws.subscribed_codes.add("123456")
        ws._registered_items_by_code["123456"] = ("123456",)
        ws._registered_item_epochs["123456"] = 3
        ws._registered_item_types["123456"] = ("0B", "0D")
        return _completed_registration()

    ws.execute_subscribe = subscribe
    released = []
    result = run_zero_base_probe(
        {"claim": {"code": "123456", "route": "krx_only", "observed_epoch": 10},
         "candidate": {"code": "123456", "route": "krx_only"}},
        ws_manager=ws,
        ai_engine=SimpleNamespace(analyze_target=lambda *_args, **_kwargs: {
            "machine_evaluation_status": "assessed",
            "entry_mechanistic_action": "RECHECK",
            "mechanistic_entry_assessment": {"reason": "wait_for_trigger"},
        }),
        token="token", now=lambda: 11,
        tick_fetcher=lambda *_args, **_kwargs: [{
            "request_code": "123456", "rest_received_ts_ms": 11000,
        }],
        candle_fetcher=lambda *_args, **_kwargs: (
            [{"close": 10000}],
            {"request_code": "123456", "rest_received_ts_ms": 11000},
        ),
        context_builder=lambda *_args, **_kwargs: {"ready": True},
        release_ws=lambda code, item: released.append((code, item)),
        ws_wait_min_exact_0b_count=0,
        retain_ws_on_recheck=True,
    )
    assert result["result"] == "assessed"
    assert result["machine_action"] == "RECHECK"
    assert result["_ws_lease_retained"] is True
    assert released == []


def test_probe_registration_receipt_rejects_silent_send_failure_and_old_transport():
    ws = SimpleNamespace(
        subscribed_codes=set(), _registered_items_by_code={},
        _registered_item_epochs={}, _registered_item_types={},
        _market_data_transport_epoch=3,
        execute_subscribe=lambda *_args, **_kwargs: _completed_registration(),
        get_latest_data=lambda *_args: (_ for _ in ()).throw(
            AssertionError("WS wait must not start without a send receipt")
        ),
    )
    released = []
    request = {
        "claim": {"code": "123456", "route": "krx_only", "observed_epoch": 10},
        "candidate": {"code": "123456", "route": "krx_only"},
    }
    result = run_zero_base_probe(
        request, ws_manager=ws, ai_engine=object(), token="token",
        now=lambda: 11, release_ws=lambda code, item: released.append((code, item)),
    )
    assert result["reason"] == "ws_registration_not_recorded"
    assert released == [("123456", "123456")]
    ws.subscribed_codes.add("123456")
    ws._registered_items_by_code["123456"] = ("123456",)
    ws._registered_item_epochs["123456"] = 2
    ws._registered_item_types["123456"] = ("0B", "0D")
    assert probe_registration_receipt(ws, code="123456", item="123456") == (
        "ws_registration_transport_mismatch"
    )
    ws._registered_item_epochs["123456"] = 3
    ws._registered_item_types["123456"] = ("0B",)
    assert probe_registration_receipt(ws, code="123456", item="123456") == (
        "ws_registration_types_missing"
    )


def test_reused_exact_item_with_old_transport_is_not_reported_as_missing_route():
    item = "123456_NX"
    ws = SimpleNamespace(
        subscribed_codes={"123456"},
        _registered_items_by_code={"123456": (item,)},
        _registered_item_epochs={item: 2},
        _registered_item_types={item: ("0B", "0D")},
        _market_data_transport_epoch=3,
        get_exact_item_data=lambda *_args: (_ for _ in ()).throw(
            AssertionError("stale registration must not start a WS wait")
        ),
    )
    result = run_zero_base_probe(
        {"claim": {"code": "123456", "route": "nxt_only", "observed_epoch": 10},
         "candidate": {"code": "123456", "route": "nxt_only"}},
        ws_manager=ws, ai_engine=object(), token="token", now=lambda: 11,
    )
    assert result["reason"] == "ws_registration_transport_mismatch"
    assert result["result"] == "source_unavailable"


def test_empty_exact_route_rechecks_transport_without_hiding_real_no_receipt():
    item = "123456_NX"
    ws = SimpleNamespace(
        subscribed_codes={"123456"},
        _registered_items_by_code={"123456": (item,)},
        _registered_item_epochs={item: 3},
        _registered_item_types={item: ("0B", "0D")},
        _market_data_transport_epoch=3,
        get_exact_item_data=lambda *_args: {},
    )
    request = {
        "claim": {"code": "123456", "route": "nxt_only", "observed_epoch": 10},
        "candidate": {"code": "123456", "route": "nxt_only"},
    }
    no_receipt = run_zero_base_probe(
        request, ws_manager=ws, ai_engine=object(), token="token",
        now=lambda: 11, ws_wait_timeout_sec=0.01,
    )
    assert no_receipt["reason"] == "route_snapshot_missing"
    assert no_receipt["ws_observation"]["empty_source_flushed"] is True

    def disconnect_during_wait(*_args):
        ws._market_data_transport_epoch = 4
        return {}

    ws.get_exact_item_data = disconnect_during_wait
    disconnected = run_zero_base_probe(
        request, ws_manager=ws, ai_engine=object(), token="token",
        now=lambda: 11, ws_wait_timeout_sec=0.01,
    )
    assert disconnected["reason"] == "ws_registration_transport_mismatch"


def test_missing_bbo_never_calls_machine_and_releases_ws():
    snapshot = _snapshot()
    snapshot["realtime_type_snapshots_by_route"]["KRX|krx_only"].pop("0D")
    released = []
    ws = SimpleNamespace(
        subscribed_codes=set(),
        execute_subscribe=lambda *args, **kwargs: _completed_registration(),
        wait_for_data=lambda *args, **kwargs: snapshot,
        get_latest_data=lambda *_args, **_kwargs: snapshot,
    )
    result = run_zero_base_probe(
        {"claim": {"code": "123456", "route": "krx_only", "observed_epoch": 10},
         "candidate": {"code": "123456", "route": "krx_only"}},
        ws_manager=ws, ai_engine=object(), token="token", now=lambda: 11,
        release_ws=lambda code, item: released.append((code, item)),
        ws_wait_timeout_sec=0.01,
    )
    assert result["result"] == "source_unavailable"
    assert released == [("123456", "123456")]


def test_existing_ws_owner_is_reused_without_changing_registration():
    snapshot = _snapshot()
    snapshot["realtime_type_snapshots_by_route"]["KRX|krx_only"].pop("0D")
    calls = []
    ws = SimpleNamespace(
        subscribed_codes={"123456"},
        execute_subscribe=lambda *_args, **_kwargs: calls.append("reg"),
        get_latest_data=lambda *_args, **_kwargs: snapshot,
    )
    result = run_zero_base_probe(
        {"claim": {"code": "123456", "route": "krx_only", "observed_epoch": 10},
         "candidate": {"code": "123456", "route": "krx_only"}},
        ws_manager=ws, ai_engine=object(), token="token", now=lambda: 11,
        release_ws=lambda *_args: calls.append("remove"),
        ws_wait_timeout_sec=0.01,
    )
    assert result["reason"] == "0D_missing"
    assert calls == []


def test_reused_observation_item_reads_exact_view_through_pre_machine_check(monkeypatch):
    import src.engine.scalping.zero_base_probe as module

    monkeypatch.setattr(module, "resolve_entry_candle_session", lambda: "SOR_AFTERMARKET")
    exact = _snapshot(route="krx_nxt_integrated", item="123456_AL")
    reads = []

    def read_exact(code, item):
        reads.append((code, item))
        return exact

    ws = SimpleNamespace(
        subscribed_codes={"123456"},
        _registered_items_by_code={"123456": ("123456_AL",)},
        get_exact_item_data=read_exact,
        get_latest_data=lambda *_args: (_ for _ in ()).throw(
            AssertionError("generic runtime view must not be used")
        ),
    )
    result = run_zero_base_probe(
        {"claim": {"code": "123456", "route": "krx_nxt_integrated",
                   "observed_epoch": 10},
         "candidate": {"code": "123456", "route": "krx_nxt_integrated"}},
        ws_manager=ws,
        ai_engine=SimpleNamespace(analyze_target=lambda *_args, **_kwargs: {
            "machine_evaluation_status": "assessment_contract_invalid",
            "machine_contract_error": "missing_stock_code",
        }),
        token="token", now=lambda: 11,
        tick_fetcher=lambda *_args, **_kwargs: [{
            "request_code": "123456_AL", "rest_received_ts_ms": 11000,
        }],
        candle_fetcher=lambda *_args, **_kwargs: (
            [{"close": 10000}],
            {"request_code": "123456_AL", "rest_received_ts_ms": 11000},
        ),
        context_builder=lambda *_args, **_kwargs: {"ready": True},
        ws_wait_min_exact_0b_count=0,
    )
    assert result["reason"] != "route_snapshot_missing"
    assert reads == [("123456", "123456_AL")] * 4


@pytest.mark.parametrize("fault", ["empty", "wrong_route", "stale"])
def test_chart_failure_never_spends_followup_tick_budget(monkeypatch, fault):
    import src.engine.scalping.zero_base_probe as module
    snapshot = _snapshot(epoch=11)
    ws = SimpleNamespace(subscribed_codes={"123456"},
        get_latest_data=lambda *_args: snapshot)
    meta = {"request_code": "OTHER" if fault == "wrong_route" else "123456",
            "rest_received_ts_ms": -200000 if fault == "stale" else 11000,
            "read_rate_control_reason": "shared_read_rate_wait_budget_exhausted"}
    result = run_zero_base_probe(
        {"claim": {"code": "123456", "route": "krx_only", "observed_epoch": 10},
         "candidate": {"code": "123456", "route": "krx_only"}},
        ws_manager=ws, ai_engine=object(), token="token", now=lambda: 11,
        candle_fetcher=lambda *a, **k: ([] if fault == "empty" else [{"close": 10000}], meta),
        tick_fetcher=lambda *a, **k: pytest.fail("chart failure must not fetch ticks"),
        ws_wait_min_exact_0b_count=0,
    )
    assert result["result"] != "assessed"
    if fault == "empty":
        assert result["reason"] == result["machine_source_gap_kind"] == "candle_source_missing"
        assert result["rest_source_gap_detail"] == "shared_read_rate_wait_budget_exhausted"


def test_probe_skips_rest_only_for_actual_trusted_exact_feature_window():
    from datetime import datetime
    from zoneinfo import ZoneInfo
    from src.engine.scalping_feature_packet import _select_recent_ticks_with_source
    epoch = datetime(2026, 10, 2, 12, 0, 11, tzinfo=ZoneInfo("Asia/Seoul")).timestamp()
    snapshot = _snapshot(epoch=epoch)
    snapshot["recent_trade_ticks_by_route"] = {"KRX|krx_only": [{
        "item": "123456", "market_route": "krx_only", "transport_epoch": 3,
        "received_at_ms": epoch*1000, "time": "12:00:11", "price": 10000,
        "volume": 10, "volume_source": "15_abs", "aggressor_side": "BUY",
        "aggressor_source": "kiwoom_0b_signed_trade_volume"}]}
    ws = SimpleNamespace(subscribed_codes={"123456"}, get_latest_data=lambda *a: snapshot)
    seen=[]
    def assess(*args, **kwargs):
        selected, source, _ = _select_recent_ticks_with_source(args[1], args[2], now=epoch)
        seen.append((source, selected))
        return {"machine_evaluation_status": "assessed", "entry_mechanistic_action": "RECHECK"}
    result = run_zero_base_probe(
        {"claim": {"code": "123456", "route": "krx_only", "observed_epoch": epoch-1},
         "candidate": {"code": "123456", "route": "krx_only"}},
        ws_manager=ws, ai_engine=SimpleNamespace(analyze_target=assess), token="token",
        now=lambda: epoch,
        candle_fetcher=lambda *a, **k: ([{"close": 10000}], {
            "request_code": "123456", "rest_received_ts_ms": int(epoch*1000)}),
        context_builder=lambda *a, **k: {"ready": True},
        tick_fetcher=lambda *a, **k: pytest.fail("trusted WS must replace REST tick read"),
        ws_wait_min_exact_0b_count=0)
    assert result["result"] == "assessed"
    assert result["tick_read_source"] == seen[0][0] == "ws_exact_route"
    assert len(seen[0][1]) == 1


def test_probe_waits_for_later_exact_0d_after_first_0b():
    first = _snapshot(route="krx_nxt_integrated", item="123456_AL")
    first["realtime_type_snapshots_by_route"]["_AL|krx_nxt_integrated"].pop("0D")
    second = _snapshot(route="krx_nxt_integrated", item="123456_AL")
    snapshots = iter((first, first, second))
    ws = SimpleNamespace(get_latest_data=lambda *_args: next(snapshots))
    data, observation, reason = wait_for_exact_probe_ws_data(
        ws, code="123456", route="krx_nxt_integrated", after_epoch=10,
        now=lambda: 11, timeout_sec=0.2, poll_interval_sec=0.01,
    )
    assert reason == "ready"
    assert data["market_data_route"] == "krx_nxt_integrated"
    assert observation["latest_0b_ms"] == 1000
    assert observation["latest_0d_ms"] == 1000


def test_probe_wait_timeout_retains_exact_route_gap():
    partial = _snapshot(route="krx_nxt_integrated", item="123456_AL")
    partial["realtime_type_snapshots_by_route"]["_AL|krx_nxt_integrated"].pop("0D")
    ws = SimpleNamespace(get_latest_data=lambda *_args: partial)
    data, observation, reason = wait_for_exact_probe_ws_data(
        ws, code="123456", route="krx_nxt_integrated", after_epoch=10,
        now=lambda: 11, timeout_sec=0.02, poll_interval_sec=0.01,
    )
    assert not data and reason == "0D_missing"
    assert observation["wait_ms"] >= 10
    assert observation["latest_0b_ms"] == 1000
    assert observation["latest_0d_ms"] is None


def test_partial_aftermarket_receipt_extends_bounded_wait_for_exact_pair():
    key = "_AL|krx_nxt_integrated"
    partial = _snapshot(route="krx_nxt_integrated", item="123456_AL")
    partial["realtime_type_snapshots_by_route"][key].pop("0D")
    partial["recent_trade_ticks_by_route"] = {key: [
        {"received_at_ms": 10500, "item": "123456_AL", "transport_epoch": 3}
    ]}
    full = _snapshot(route="krx_nxt_integrated", item="123456_AL")
    full["recent_trade_ticks_by_route"] = partial["recent_trade_ticks_by_route"]
    full["recent_depth_ticks_by_route"] = {key: [
        {"received_at_ms": 10600, "item": "123456_AL", "transport_epoch": 3}
    ]}
    started = time.monotonic()
    ws = SimpleNamespace(get_latest_data=lambda *_args: (
        partial if time.monotonic() - started < 0.04 else full
    ))
    data, observation, reason = wait_for_exact_probe_ws_data(
        ws, code="123456", route="krx_nxt_integrated", after_epoch=10,
        now=lambda: 11, timeout_sec=0.01, partial_extension_sec=0.07,
        poll_interval_sec=0.005, min_exact_0b_count=1,
    )
    assert reason == "ready" and data
    assert observation["partial_extension_applied"] is True
    assert observation["wait_ms"] >= 30
    assert observation["base_wait_budget_ms"] == 10
    assert observation["effective_wait_budget_ms"] == 80


def test_empty_receipt_does_not_extend_wait():
    ws = SimpleNamespace(get_latest_data=lambda *_args: {})
    data, observation, _reason = wait_for_exact_probe_ws_data(
        ws, code="123456", route="nxt_only", after_epoch=10,
        now=lambda: 11, timeout_sec=0.01, partial_extension_sec=0.07,
        poll_interval_sec=0.005,
    )
    assert not data
    assert observation["partial_extension_applied"] is False
    assert observation["wait_ms"] < 60
    assert observation["effective_wait_budget_ms"] == 10


def test_empty_exact_source_flushes_before_full_ws_wait():
    ws = SimpleNamespace(get_latest_data=lambda *_args: {})
    data, observation, reason = wait_for_exact_probe_ws_data(
        ws, code="123456", route="krx_nxt_integrated", after_epoch=10,
        now=lambda: 11, timeout_sec=0.2, empty_timeout_sec=0.03,
        poll_interval_sec=0.005,
    )
    assert not data and reason == "route_snapshot_missing"
    assert observation["empty_source_flushed"] is True
    assert 20 <= observation["wait_ms"] < 100
    assert observation["base_wait_budget_ms"] == 200
    assert observation["effective_wait_budget_ms"] == 30


@pytest.mark.parametrize("route,item,warmup,timeout", [
    ("krx_nxt_integrated", "123456_AL", 10.0, 15.0),
    ("nxt_only", "123456_NX", 15.0, 20.0),
])
@pytest.mark.parametrize("ready", [False, True])
def test_exact_source_waits_for_session_probe_floor(
    monkeypatch, route, item, warmup, timeout, ready,
):
    import src.engine.scalping.zero_base_probe as module

    elapsed = [0.0]
    monkeypatch.setattr(module.time, "monotonic", lambda: elapsed[0])
    monkeypatch.setattr(
        module.time, "sleep",
        lambda seconds: elapsed.__setitem__(0, elapsed[0] + seconds),
    )
    ws = SimpleNamespace(
        get_latest_data=lambda *_args: _snapshot(route, item) if ready else {},
    )
    data, observation, reason = wait_for_exact_probe_ws_data(
        ws, code="123456", route=route, after_epoch=10,
        now=lambda: 11, timeout_sec=timeout,
        empty_timeout_sec=warmup, min_warmup_sec=warmup,
    )
    assert (reason == "ready" and bool(data)) is ready
    assert warmup * 1000 <= observation["wait_ms"] < warmup * 1000 + 100
    assert observation["empty_source_flushed"] is not ready


def test_one_exact_stream_keeps_full_ws_wait_budget():
    partial = _snapshot(route="krx_nxt_integrated", item="123456_AL")
    partial["realtime_type_snapshots_by_route"]["_AL|krx_nxt_integrated"].pop("0B")
    partial["recent_depth_ticks_by_route"] = {"_AL|krx_nxt_integrated": [
        {"received_at_ms": 10500, "item": "123456_AL", "transport_epoch": 3}
    ]}
    ws = SimpleNamespace(get_latest_data=lambda *_args: partial)
    data, observation, reason = wait_for_exact_probe_ws_data(
        ws, code="123456", route="krx_nxt_integrated", after_epoch=10,
        now=lambda: 11, timeout_sec=0.05, empty_timeout_sec=0.01,
        poll_interval_sec=0.005,
    )
    assert not data and reason == "0B_missing"
    assert observation["empty_source_flushed"] is False
    assert observation["wait_ms"] >= 40
    assert observation["effective_wait_budget_ms"] == 50


def test_exact_typed_receipt_without_tick_history_is_not_empty_source():
    partial = _snapshot(route="krx_nxt_integrated", item="123456_AL")
    partial["realtime_type_snapshots_by_route"]["_AL|krx_nxt_integrated"].pop("0B")
    ws = SimpleNamespace(get_latest_data=lambda *_args: partial)
    data, observation, reason = wait_for_exact_probe_ws_data(
        ws, code="123456", route="krx_nxt_integrated", after_epoch=10,
        now=lambda: 11, timeout_sec=0.05, empty_timeout_sec=0.01,
        poll_interval_sec=0.005,
    )
    assert not data and reason == "0B_missing"
    assert observation["exact_0d_count"] == 0
    assert observation["latest_0d_ms"] == 1000
    assert observation["empty_source_flushed"] is False
    assert observation["wait_ms"] >= 40


def test_late_exact_pair_arrives_after_initially_empty_ws_snapshot():
    ready = _snapshot(route="krx_nxt_integrated", item="123456_AL")
    key = "_AL|krx_nxt_integrated"
    ready["recent_trade_ticks_by_route"] = {key: [
        {"received_at_ms": 10500, "item": "123456_AL", "transport_epoch": 3}
    ]}
    ready["recent_depth_ticks_by_route"] = {key: [
        {"received_at_ms": 10600, "item": "123456_AL", "transport_epoch": 3}
    ]}
    started = time.monotonic()
    ws = SimpleNamespace(get_latest_data=lambda *_args: (
        {} if time.monotonic() - started < 0.04 else ready
    ))
    data, observation, reason = wait_for_exact_probe_ws_data(
        ws, code="123456", route="krx_nxt_integrated", after_epoch=10,
        now=lambda: 11, timeout_sec=0.1, poll_interval_sec=0.005,
    )
    assert reason == "ready" and data
    assert 35 <= observation["wait_ms"] < 100
    assert observation["partial_extension_applied"] is False


def test_default_empty_wait_accepts_exact_pair_after_three_seconds(monkeypatch):
    import src.engine.scalping.zero_base_probe as module

    elapsed = [0.0]
    monkeypatch.setattr(module.time, "monotonic", lambda: elapsed[0])
    monkeypatch.setattr(
        module.time, "sleep",
        lambda seconds: elapsed.__setitem__(0, elapsed[0] + seconds),
    )
    ready = _snapshot(route="krx_nxt_integrated", item="123456_AL")
    ws = SimpleNamespace(
        get_latest_data=lambda *_args: ready if elapsed[0] >= 4.0 else {}
    )

    data, observation, reason = wait_for_exact_probe_ws_data(
        ws, code="123456", route="krx_nxt_integrated", after_epoch=10,
        now=lambda: 11, timeout_sec=10.0,
    )

    assert reason == "ready" and data
    assert 4000 <= observation["wait_ms"] <= 4100
    assert observation["empty_source_flushed"] is False
    assert observation["base_wait_budget_ms"] == 10000


def test_probe_observation_counts_only_exact_route_and_transport():
    snapshot = _snapshot(route="krx_nxt_integrated", item="123456_AL")
    key = "_AL|krx_nxt_integrated"
    snapshot["recent_trade_ticks_by_route"] = {key: [
        {"received_at_ms": 10500, "item": "123456_AL", "transport_epoch": 3,
         "aggressor_source": "kiwoom_0b_signed_trade_volume", "aggressor_side": "BUY"},
        {"received_at_ms": 10600, "item": "123456_AL", "transport_epoch": 3},
        {"received_at_ms": 10700, "item": "123456", "transport_epoch": 3},
        {"received_at_ms": 10800, "item": "123456_AL", "transport_epoch": 2},
    ]}
    snapshot["recent_depth_ticks_by_route"] = {key: [
        {"received_at_ms": 10400, "item": "123456_AL", "transport_epoch": 3},
    ]}
    ws = SimpleNamespace(get_latest_data=lambda *_args: snapshot)
    _data, observation, reason = wait_for_exact_probe_ws_data(
        ws, code="123456", route="krx_nxt_integrated", after_epoch=10,
        now=lambda: 11, timeout_sec=0,
    )
    assert reason == "ready"
    assert observation["first_0b_ms"] == 500
    assert observation["first_0d_ms"] == 400
    assert observation["exact_0b_count"] == 2
    assert observation["signed_0b_count"] == 1
    assert observation["fifth_0b_ms"] is None


def test_probe_waits_for_five_exact_ticks_within_bounded_cap():
    snapshot = _snapshot(route="krx_nxt_integrated", item="123456_AL")
    key = "_AL|krx_nxt_integrated"
    calls = []
    def latest(_code):
        calls.append(None)
        count = 1 if len(calls) < 3 else 5
        current = dict(snapshot)
        current["recent_trade_ticks_by_route"] = {key: [
            {"received_at_ms": 10100 + index * 100,
             "item": "123456_AL", "transport_epoch": 3}
            for index in range(count)
        ]}
        return current
    data, observation, reason = wait_for_exact_probe_ws_data(
        SimpleNamespace(get_latest_data=latest), code="123456",
        route="krx_nxt_integrated", after_epoch=10, now=lambda: 11,
        timeout_sec=0.2, poll_interval_sec=0.01, min_exact_0b_count=5,
    )
    assert reason == "ready" and data
    assert len(calls) == 3
    assert observation["sample_target_met"] is True
    assert observation["fifth_0b_ms"] == 500


def test_machine_contract_error_is_retained_without_promoting(monkeypatch):
    import src.engine.scalping.zero_base_probe as module

    monkeypatch.setattr(module, "resolve_entry_candle_session", lambda: "KRX_REGULAR")
    monkeypatch.setattr(module, "resolve_entry_candle_request_code", lambda *_args, **_kwargs: "123456")
    ws = SimpleNamespace(
        subscribed_codes={"123456"},
        wait_for_data=lambda *_args, **_kwargs: _snapshot(epoch=11),
        get_latest_data=lambda *_args, **_kwargs: _snapshot(epoch=11),
    )
    machine = SimpleNamespace(analyze_target=lambda *_args, **_kwargs: {
        "machine_evaluation_status": "assessment_contract_invalid",
        "machine_contract_error": "missing_stock_code",
    })
    result = run_zero_base_probe(
        {"claim": {"code": "123456", "route": "krx_only", "observed_epoch": 10},
         "candidate": {"code": "123456", "route": "krx_only"}},
        ws_manager=ws, ai_engine=machine, token="token", now=lambda: 11,
        tick_fetcher=lambda *_args, **_kwargs: [{
            "request_code": "123456", "rest_received_ts_ms": 11000,
        }],
        candle_fetcher=lambda *_args, **_kwargs: (
            [{"close": 10000}], {"request_code": "123456", "rest_received_ts_ms": 11000},
        ),
        context_builder=lambda *_args, **_kwargs: {"ready": True},
        ws_wait_min_exact_0b_count=0,
    )
    assert result["result"] == "policy_unavailable"
    assert result["machine_contract_error"] == "missing_stock_code"
    assert result["machine_action"] == ""


def test_missing_trusted_tape_is_a_feature_gap_not_a_policy_outage(monkeypatch):
    import src.engine.scalping.zero_base_probe as module
    monkeypatch.setattr(module, "resolve_entry_candle_session", lambda: "KRX_REGULAR")
    ws = SimpleNamespace(
        subscribed_codes={"123456"},
        _registered_items_by_code={"123456": ("123456_AL",)},
        wait_for_data=lambda *_args, **_kwargs: _snapshot(
            route="krx_nxt_integrated", item="123456_AL", epoch=11,
        ),
        get_latest_data=lambda *_args, **_kwargs: _snapshot(
            route="krx_nxt_integrated", item="123456_AL", epoch=11,
        ),
    )
    machine = SimpleNamespace(analyze_target=lambda *_args, **_kwargs: {
        "machine_evaluation_status": "assessment_contract_invalid",
        "machine_contract_error": "strategy_tape_score_source_missing",
        "machine_source_gap_kind": "trusted_tape_source_insufficient",
        "machine_feature_source_receipt": {"feature_tick_source": "rest"},
    })
    result = run_zero_base_probe(
        {"claim": {"code": "123456", "route": "krx_nxt_integrated",
                   "observed_epoch": 10},
         "candidate": {"code": "123456", "route": "krx_nxt_integrated"}},
        ws_manager=ws, ai_engine=machine, token="token", now=lambda: 11,
        tick_fetcher=lambda *_args, **_kwargs: [{
            "request_code": "123456_AL", "rest_received_ts_ms": 11000,
        }],
        candle_fetcher=lambda *_args, **_kwargs: (
            [{"close": 10000}],
            {"request_code": "123456_AL", "rest_received_ts_ms": 11000},
        ),
        context_builder=lambda *_args, **_kwargs: {"ready": True},
        ws_wait_min_exact_0b_count=0,
    )
    assert result["result"] == "required_feature_insufficient"
    assert result["machine_contract_error"] == "strategy_tape_score_source_missing"
    assert result["machine_source_gap_kind"] == "trusted_tape_source_insufficient"
    assert result["machine_feature_source_receipt"]["feature_tick_source"] == "rest"
    assert result["machine_action"] == ""


@pytest.mark.parametrize("status,existing_kind,primary,expected", [
    ("source_quality_blocked_before_assessment", None, "runtime_preflight_artifact_not_ready", "runtime_preflight_artifact_not_ready"),
    ("source_quality_blocked_before_assessment", "trusted_tape_source_insufficient", "runtime_preflight_artifact_not_ready", "trusted_tape_source_insufficient"),
    ("source_quality_blocked_before_assessment", None, None, None),
    ("required_feature_blocked_before_assessment", None, "required_feature_provider_trade_late", "required_feature_provider_trade_late"),
])
def test_source_blocked_probe_keeps_exact_identity_and_primary_cause(
    monkeypatch, status, existing_kind, primary, expected,
):
    import src.engine.scalping.zero_base_probe as module

    monkeypatch.setattr(module, "resolve_entry_candle_session", lambda: "KRX_REGULAR")
    ws = SimpleNamespace(
        subscribed_codes={"123456"},
        _registered_items_by_code={"123456": ("123456_AL",)},
        get_latest_data=lambda *_args, **_kwargs: _snapshot(
            route="krx_nxt_integrated", item="123456_AL", epoch=11),
    )
    receipt = {
        "machine_evaluation_status": status,
        "ai_result_source": "input_preflight_blocked",
        "entry_source_invalid_primary_blocker": primary,
        "entry_required_feature_blockers": [primary] if primary else [],
        "machine_source_gap_kind": existing_kind,
        "evaluation_attempt_id": "machine-source-invalid-exact",
        "machine_capture_status": "captured",
        "machine_observation_sha256": "a" * 64,
        "machine_bundle_sha256": "b" * 64,
        "ai_input_runtime_preflight_artifact_status": "artifact_missing",
    }
    result = run_zero_base_probe(
        {"claim": {"code": "123456", "route": "krx_nxt_integrated", "observed_epoch": 10},
         "candidate": {"code": "123456", "route": "krx_nxt_integrated"}},
        ws_manager=ws,
        ai_engine=SimpleNamespace(analyze_target=lambda *_args, **_kwargs: receipt),
        token="token", now=lambda: 11,
        tick_fetcher=lambda *_args, **_kwargs: [
            {"request_code": "123456_AL", "rest_received_ts_ms": 11000}],
        candle_fetcher=lambda *_args, **_kwargs: (
            [{"close": 10000}], {"request_code": "123456_AL", "rest_received_ts_ms": 11000}),
        context_builder=lambda *_args, **_kwargs: {"ready": True},
        ws_wait_min_exact_0b_count=0,
    )
    assert result["result"] == "required_feature_insufficient"
    assert result["reason"] == status
    assert result.get("machine_source_gap_kind") == expected
    assert result["evaluation_attempt_id"] == receipt["evaluation_attempt_id"]
    assert result["machine_observation_sha256"] == receipt["machine_observation_sha256"]
    assert result["machine_bundle_sha256"] == receipt["machine_bundle_sha256"]
    assert result["machine_preflight_artifact_status"] == "artifact_missing"
    assert result["machine_action"] == ""
    assert result["actual_order_submitted"] is False
    assert result["broker_order_forbidden"] is True


def test_late_ws_registration_releases_only_after_registration_finishes():
    pending = Future()
    released = []
    ws = SimpleNamespace(
        subscribed_codes=set(),
        execute_subscribe=lambda *args, **kwargs: pending,
        wait_for_data=lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("wait_for_data must not run before registration")
        ),
    )
    result = run_zero_base_probe(
        {"claim": {"code": "123456", "route": "krx_only", "observed_epoch": 10},
         "candidate": {"code": "123456", "route": "krx_only"}},
        ws_manager=ws, ai_engine=object(), token="token", now=lambda: 11,
        release_ws=lambda code, item: released.append((code, item)),
    )
    assert result["reason"] == "ws_registration_timeout"
    assert released == []
    pending.set_result(None)
    assert released == [("123456", "123456")]


def test_tick_probe_keeps_explicit_krx_route(monkeypatch):
    from src.utils import kiwoom_utils

    requests = []
    monkeypatch.setattr(
        kiwoom_utils, "get_effective_kiwoom_code",
        lambda _code: (_ for _ in ()).throw(AssertionError("route rewritten")),
    )
    monkeypatch.setattr(
        kiwoom_utils, "fetch_kiwoom_api_continuous",
        lambda **kwargs: (requests.append(kwargs), ([], {}))[1],
    )
    assert kiwoom_utils.get_tick_history_ka10003(
        "token", "123456", explicit_request_code=True,
    ) == []
    assert requests[0]["payload"]["stk_cd"] == "123456"


def test_rest_probe_rejects_reused_or_cross_route_feature_rows():
    tick = {"request_code": "123456", "rest_received_ts_ms": 11000}
    candle = {"request_code": "123456", "rest_received_ts_ms": 11000}
    assert exact_probe_rest_sources([tick], candle, request_code="123456", now_epoch=11)
    assert not exact_probe_rest_sources([tick], candle, request_code="123456_NX", now_epoch=11)
    assert not exact_probe_rest_sources([tick], candle, request_code="123456", now_epoch=30)
    assert not exact_probe_rest_sources([], candle, request_code="123456", now_epoch=11)
    assert exact_probe_rest_sources(
        [], candle, request_code="123456", now_epoch=11,
        allow_empty_ticks=True,
    )
    assert not exact_probe_rest_sources(
        [], candle, request_code="123456_NX", now_epoch=11,
        allow_empty_ticks=True,
    )
    assert exact_probe_rest_source_issue(
        [tick], candle, request_code="123456_NX", now_epoch=11,
    ) == "candle_route_mismatch"
    assert exact_probe_rest_source_issue(
        [tick], candle, request_code="123456", now_epoch=22,
    ) == "tick_receive_clock_invalid"


def test_probe_fetches_short_lived_ticks_after_slow_candle_source(monkeypatch):
    import src.engine.scalping.zero_base_probe as module
    monkeypatch.setattr(module, "resolve_entry_candle_session", lambda: "KRX_REGULAR")
    clock = [11.0]
    calls = []
    ws = SimpleNamespace(
        subscribed_codes={"123456"},
        _registered_items_by_code={"123456": ("123456_AL",)},
        get_exact_item_data=lambda *_args: _snapshot(
            route="krx_nxt_integrated", item="123456_AL", epoch=clock[0],
        ),
    )

    def candle_fetcher(*_args, **_kwargs):
        calls.append("candle")
        clock[0] += 11
        return ([{"close": 10000}], {
            "request_code": "123456_AL",
            "rest_received_ts_ms": int(clock[0] * 1000),
        })

    def tick_fetcher(*_args, **_kwargs):
        calls.append("tick")
        return [{
            "request_code": "123456_AL",
            "rest_received_ts_ms": int(clock[0] * 1000),
        }]

    result = run_zero_base_probe(
        {"claim": {"code": "123456", "route": "krx_nxt_integrated",
                   "observed_epoch": 10},
         "candidate": {"code": "123456", "route": "krx_nxt_integrated"}},
        ws_manager=ws,
        ai_engine=SimpleNamespace(analyze_target=lambda *_args, **_kwargs: {
            "machine_evaluation_status": "assessed",
            "entry_mechanistic_action": "RECHECK",
        }),
        token="token", now=lambda: clock[0],
        tick_fetcher=tick_fetcher,
        candle_fetcher=candle_fetcher,
        context_builder=lambda *_args, **_kwargs: {"ready": True},
        ws_wait_min_exact_0b_count=0,
    )
    assert calls == ["candle", "tick"]
    assert result["result"] == "assessed"
    assert result.get("rest_source_gap_detail") is None


def test_probe_uses_exact_ws_tick_when_rest_tick_history_is_empty(monkeypatch):
    import src.engine.scalping.zero_base_probe as module
    monkeypatch.setattr(module, "resolve_entry_candle_session", lambda: "KRX_REGULAR")
    snapshot = _snapshot(epoch=11)
    snapshot["recent_trade_ticks_by_route"] = {"KRX|krx_only": [{
        "item": "123456", "market_route": "krx_only", "transport_epoch": 3,
        "received_at_ms": 11000, "price": 10000, "volume": 1,
    }]}
    ws = SimpleNamespace(
        subscribed_codes={"123456"},
        _registered_items_by_code={"123456": ("123456",)},
        wait_for_data=lambda *_args, **_kwargs: snapshot,
        get_latest_data=lambda *_args, **_kwargs: snapshot,
    )
    received = []
    machine = SimpleNamespace(analyze_target=lambda *args, **kwargs: (
        received.append((args, kwargs)), {
            "machine_evaluation_status": "assessed",
            "entry_mechanistic_action": "BLOCK",
        }
    )[1])
    result = run_zero_base_probe(
        {"claim": {"code": "123456", "route": "krx_only", "observed_epoch": 10},
         "candidate": {"code": "123456", "route": "krx_only"}},
        ws_manager=ws, ai_engine=machine, token="token", now=lambda: 11,
        tick_fetcher=lambda *_args, **_kwargs: [],
        candle_fetcher=lambda *_args, **_kwargs: (
            [{"close": 10000}],
            {"request_code": "123456", "rest_received_ts_ms": 11000},
        ),
        context_builder=lambda *_args, **_kwargs: {"ready": True},
        ws_wait_min_exact_0b_count=0,
    )
    assert received
    assert received[0][0][2] == []
    assert received[0][0][1]["recent_trade_ticks"][0]["price"] == 10000
    assert result["machine_action"] == "BLOCK"


def test_exact_probe_lease_reaches_machine_with_nx_beside_existing_al(monkeypatch):
    import src.engine.scalping.zero_base_probe as module
    from concurrent.futures import Future
    calls = []
    ws = SimpleNamespace(
        subscribed_codes={"123456"},
        _registered_items_by_code={"123456": ("123456_AL",)},
        _registered_item_epochs={"123456_AL": 3},
        _registered_item_types={"123456_AL": ("0B", "0D")},
        _market_data_transport_epoch=3,
        get_exact_item_data=lambda code, item: _snapshot(epoch=11, route="nxt_only", item="123456_NX"),
    )
    def acquire(item, lease_id):
        assert item == "123456_NX"
        ws._registered_items_by_code["123456"] += (item,)
        ws._registered_item_epochs[item] = 3
        ws._registered_item_types[item] = ("0B", "0D")
        calls.append(("acquire", item, lease_id))
        completion = Future()
        completion.set_result({"registered": True, "created": True, "item": item})
        return completion
    ws.execute_acquire_exact_probe_item = acquire
    ws.execute_release_exact_probe_item = lambda item, lease_id: calls.append(("release", item, lease_id))
    monkeypatch.setattr(module, "resolve_entry_candle_session", lambda: "LEGACY_PREMARKET")
    monkeypatch.setattr(module, "resolve_entry_candle_request_code", lambda *a, **kw: "123456_NX")
    engine = SimpleNamespace(analyze_target=lambda *a, **kw: (
        calls.append(("machine", kw["machine_only"])),
        {"machine_evaluation_status": "assessed", "entry_mechanistic_action": "BLOCK",
         "mechanistic_entry_assessment": {"reason": "valid_source"}},
    )[1])
    result = run_zero_base_probe(
        {"claim": {"code": "123456", "route": "nxt_only", "observed_epoch": 10},
         "candidate": {"code": "123456", "route": "nxt_only"}},
        ws_manager=ws, ai_engine=engine, token="test", now=lambda: 11, ws_lease_id="same-probe",
        ws_wait_min_exact_0b_count=0,
        tick_fetcher=lambda *a, **kw: [{"request_code": "123456_NX", "rest_received_ts_ms": 11000}],
        candle_fetcher=lambda *a, **kw: ([{"close": 10000}], {"request_code": "123456_NX", "rest_received_ts_ms": 11000}),
        context_builder=lambda *a, **kw: {"ready": True},
    )
    assert result["result"] == "assessed" and result["machine_action"] == "BLOCK"
    assert ("machine", True) in calls
    assert calls[-1] == ("release", "123456_NX", "same-probe")
    assert ws._registered_items_by_code["123456"][0] == "123456_AL"
    assert result["actual_order_submitted"] is False


def test_exact_probe_late_registration_defers_only_lease_cleanup():
    from concurrent.futures import Future
    from concurrent.futures import TimeoutError
    cleanup = []
    class LateFuture(Future):
        def result(self, timeout=None):
            if timeout is not None:
                raise TimeoutError()
            return super().result()
    completion = LateFuture()
    ws = SimpleNamespace(
        subscribed_codes={"123456"}, _registered_items_by_code={"123456": ("123456_AL",)},
        execute_acquire_exact_probe_item=lambda item, lease: completion,
        execute_release_exact_probe_item=lambda item, lease: cleanup.append((item, lease)),
    )
    result = run_zero_base_probe(
        {"claim": {"code": "123456", "route": "nxt_only", "observed_epoch": 10},
         "candidate": {"code": "123456", "route": "nxt_only"}},
        ws_manager=ws, ai_engine=object(), token="test", now=lambda: 11, ws_lease_id="timed-out",
    )
    assert result["reason"] == "ws_registration_timeout" and result["_ws_cleanup_deferred"] is True
    assert not cleanup
    completion.set_result({"registered": True})
    assert cleanup == [("123456_NX", "timed-out")]
    assert ws._registered_items_by_code["123456"] == ("123456_AL",)
