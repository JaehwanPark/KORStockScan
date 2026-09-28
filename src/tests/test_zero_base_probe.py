from types import SimpleNamespace
from concurrent.futures import Future

from src.engine.scalping.zero_base_probe import (
    exact_probe_rest_sources, exact_probe_ws_data, run_zero_base_probe,
)


def _completed_registration():
    future = Future()
    future.set_result(None)
    return future


def _snapshot(route="krx_only", item="123456", epoch=11.0):
    key = "KRX|krx_only" if route == "krx_only" else "_NX|nxt_only"
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
    )
    assert result["result"] == "source_unavailable"
    assert released == [("123456", "123456")]


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
