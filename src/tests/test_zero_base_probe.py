from types import SimpleNamespace
from concurrent.futures import Future

from src.engine.scalping.zero_base_probe import (
    exact_probe_rest_sources, exact_probe_ws_data, run_zero_base_probe,
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


def test_machine_only_probe_passes_only_exact_fresh_input_and_releases_ws(monkeypatch):
    import src.engine.scalping.zero_base_probe as module

    monkeypatch.setattr(module, "resolve_entry_candle_session", lambda: "KRX_REGULAR")
    monkeypatch.setattr(module, "resolve_entry_candle_request_code", lambda *_args, **_kwargs: "123456")
    calls = []
    ws = SimpleNamespace(
        subscribed_codes=set(),
        execute_subscribe=lambda *args, **kwargs: (calls.append((args, kwargs)), _completed_registration())[1],
        wait_for_data=lambda *args, **kwargs: _snapshot(epoch=11),
        get_latest_data=lambda *_args, **_kwargs: _snapshot(epoch=11),
    )
    machine_calls = []
    context_calls = []

    class Machine:
        def analyze_target(self, *args, **kwargs):
            machine_calls.append(kwargs)
            return {"machine_evaluation_status": "assessed",
                    "entry_mechanistic_action": "ENTER_NOW",
                    "machine_bundle_sha256": "a" * 64,
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
    )
    assert result["result"] == "assessed"
    assert result["machine_action"] == "ENTER_NOW"
    assert result["actual_order_submitted"] is False
    assert machine_calls[0]["machine_only"] is True
    assert context_calls[0]["source_meta"]["multi_timeframe_auxiliary_fetch"] is False
    assert context_calls[0]["include_investor_source"] is False
    assert calls[-1] == ("release", "123456", "123456")


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
    )
    assert result["result"] == "required_feature_insufficient"
    assert result["machine_contract_error"] == "strategy_tape_score_source_missing"
    assert result["machine_action"] == ""


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
