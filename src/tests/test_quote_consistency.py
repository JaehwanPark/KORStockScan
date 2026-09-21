from __future__ import annotations

import pytest

from src.trading.market.quote_consistency import (
    ws_quote_receive_age_ms,
    build_market_data_health,
    QuoteConsistencyConfig,
    build_quote_consistency_snapshot,
    quote_input_from_rest_orderbook,
    quote_input_from_ws,
)


def _shared_widget_fixture(tmp_path, monkeypatch):
    import json
    from datetime import datetime, time
    from types import SimpleNamespace
    from zoneinfo import ZoneInfo
    from src.engine import bd_fbuy_accum_pre_scanner as publisher
    now = datetime(2026, 9, 21, 10, 0, tzinfo=ZoneInfo("Asia/Seoul")).timestamp()
    path = tmp_path / "latest.json"
    monkeypatch.setenv("KORSTOCKSCAN_RUNTIME_GIT_COMMIT", "a" * 40)
    monkeypatch.setattr(publisher, "WS_SNAPSHOT_PATH", path)
    common = dict(item="005930", market_suffix="", market_route="krx_only", effective_venue="KRX",
                  transport_epoch=1, route_sequence=2, observed_epoch=now - 0.2)
    row = {"market_data_transport_epoch": 1, "realtime_type_snapshots_by_route": {
        "KRX|krx_only": {"0B": {**common, "trade_price": 10000},
            "0D": {**common, "orderbook": {"asks": [{"price": 10010, "volume": 3}],
                                           "bids": [{"price": 9990, "volume": 5}]}}}}}
    publisher.write_ws_snapshot({"005930": row}, now_ts=now,
        shared_transport_producer={"transport_epoch": 1, "registered_items": ["005930"],
            "connection_available": True, "registration_basis": "local_sent_registry_not_broker_ack"})
    context = SimpleNamespace(request_code="005930", name="KRX_REGULAR", start=time(9), end=time(15, 30), active=True)
    return path, context, now, json.loads(path.read_text())


def test_shared_widget_writer_to_independent_reader_preserves_clocks(tmp_path, monkeypatch):
    import json, subprocess, sys
    from pathlib import Path
    from src.trading.market.shared_ws_snapshot import read_shared_widget_quote
    path, context, now, snapshot = _shared_widget_fixture(tmp_path, monkeypatch)
    result = read_shared_widget_quote(context, now_ts=now + 1, path=path)
    assert result["status"] == "valid_ws_comparison_input", result
    assert result["values"]["best_bid_qty"] == 5
    assert result["source_clocks"] == {"0B": now - .2, "0D": now - .2}
    code = """import json,sys
from datetime import time
from types import SimpleNamespace
from src.trading.market.shared_ws_snapshot import read_shared_widget_quote
c=SimpleNamespace(request_code='005930',name='KRX_REGULAR',start=time(9),end=time(15,30),active=True)
print(json.dumps(read_shared_widget_quote(c,now_ts=float(sys.argv[2]),path=sys.argv[1])))
"""
    child = subprocess.run([sys.executable, "-c", code, str(path), str(now+1)],
        cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True, check=True)
    child_result = json.loads(child.stdout.splitlines()[-1])
    assert child_result["status"] == "valid_ws_comparison_input"
    assert child_result["source_sha256"] == result["source_sha256"]
    assert child_result["selected_input"] == "existing_rest"


@pytest.mark.parametrize("suffix,route,venue", [("_NX", "nxt_only", "NXT"), ("_AL", "krx_nxt_integrated", "")])
def test_shared_widget_reader_preserves_exact_non_krx_route(tmp_path, monkeypatch, suffix, route, venue):
    import json
    from src.trading.market.shared_ws_snapshot import read_shared_widget_quote
    path, context, now, snapshot = _shared_widget_fixture(tmp_path, monkeypatch)
    item = "005930" + suffix
    context.request_code = item
    snapshot["shared_transport_producer"]["registered_items"] = [item]
    routes = snapshot["stocks"]["005930"]["machine_confirmation_routes"]
    row = routes.pop("KRX|krx_only")
    for field in row["realtime_types"].values():
        field.update(item=item, market_suffix=suffix, market_route=route, effective_venue=venue)
    routes[suffix + "|" + route] = row
    path.write_text(json.dumps(snapshot))
    result = read_shared_widget_quote(context, now_ts=now, path=path)
    assert result["status"] == "valid_ws_comparison_input", result
    assert result["market_data_route"] == route


@pytest.mark.parametrize("symbol", ["005930", "034020", "042660", "000660"])
@pytest.mark.parametrize("requested_suffix", ["", "_NX", "_AL"])
def test_shared_widget_accepts_integrated_source_for_all_symbols(tmp_path, monkeypatch, symbol, requested_suffix):
    import json
    from datetime import datetime, timezone
    from types import SimpleNamespace
    from src.trading.market.shared_ws_snapshot import read_shared_widget_quote, compare_widget_rest, attach_transport_census
    path, context, now, snapshot = _shared_widget_fixture(tmp_path, monkeypatch)
    context.request_code = symbol + requested_suffix
    item = symbol + "_AL"
    snapshot["shared_transport_producer"]["registered_items"] = [item]
    stock = snapshot["stocks"].pop("005930")
    snapshot["stocks"][symbol] = stock
    for row in stock["machine_confirmation_routes"]["KRX|krx_only"]["realtime_types"].values():
        row.update(item=item, market_suffix="_AL", market_route="krx_nxt_integrated", effective_venue="")
    path.write_text(json.dumps(snapshot))
    source = read_shared_widget_quote(context, now_ts=now, path=path)
    assert source["status"] == "valid_ws_comparison_input", source
    assert source["request_code"] == context.request_code
    assert source["ws_request_code"] == item
    assert source["market_data_route"] == "krx_nxt_integrated"
    assert source["source_clocks"] == {"0B": now - .2, "0D": now - .2}
    stamp = datetime.fromtimestamp(now, timezone.utc)
    compare_widget_rest(source, current_price=10000, bbo=source["values"], quote_received_at=stamp, bbo_received_at=stamp)
    assert source["comparison_status"] == ("matched_fields" if requested_suffix == "_AL" else "different_market_data_scope")
    assert source["same_observation_proven"] is False
    owner = SimpleNamespace(_transport_comparison=source)
    payload = {"observed_at_kst": stamp.isoformat()}
    attach_transport_census(owner, payload)
    first = source["census"]
    attach_transport_census(owner, payload)
    assert next(iter(first["windows"].values()))["ws_source_items"][item]["valid_ws"] == 1
    bucket = next(iter(source["census"]["windows"].values()))
    assert bucket["valid_ws"] == bucket["ws_source_items"][item]["valid_ws"] == 2
    assert source["selected_input"] == "existing_rest"
    assert source["runtime_effect"] is False


@pytest.mark.parametrize("defect", ["stale", "mixed_item", "wrong_symbol", "partial", "wrong_route", "epoch"])
def test_integrated_acceptance_preserves_required_source_guards(tmp_path, monkeypatch, defect):
    import json
    from src.trading.market.shared_ws_snapshot import read_shared_widget_quote
    path, context, now, snapshot = _shared_widget_fixture(tmp_path, monkeypatch)
    snapshot["shared_transport_producer"]["registered_items"] = ["005930_AL"]
    rows = snapshot["stocks"]["005930"]["machine_confirmation_routes"]["KRX|krx_only"]["realtime_types"]
    for row in rows.values():
        row.update(item="005930_AL", market_suffix="_AL", market_route="krx_nxt_integrated", effective_venue="")
    if defect == "stale": rows["0D"]["observed_epoch"] = now - 21
    elif defect == "mixed_item": rows["0D"]["item"] = "005930"
    elif defect == "wrong_symbol":
        for row in rows.values(): row["item"] = "034020_AL"
    elif defect == "partial": rows["0D"]["orderbook"]["asks"][0].pop("volume")
    elif defect == "wrong_route": rows["0D"]["market_route"] = "krx_only"
    elif defect == "epoch": rows["0D"]["transport_epoch"] = 2
    path.write_text(json.dumps(snapshot))
    source = read_shared_widget_quote(context, now_ts=now, path=path)
    assert source["status"] == "source_gap", source
    assert source["selected_input"] == "existing_rest"


def test_integrated_source_selection_keeps_existing_window_denominator(tmp_path, monkeypatch):
    import json
    from copy import deepcopy
    from datetime import datetime, timezone
    from types import SimpleNamespace
    from src.trading.market.shared_ws_snapshot import read_shared_widget_quote, attach_transport_census
    path, context, now, snapshot = _shared_widget_fixture(tmp_path, monkeypatch)
    owner = SimpleNamespace(_transport_comparison=read_shared_widget_quote(context, now_ts=now, path=path))
    payload = {"observed_at_kst": datetime.fromtimestamp(now, timezone.utc).isoformat()}
    attach_transport_census(owner, payload)
    routes = snapshot["stocks"]["005930"]["machine_confirmation_routes"]
    integrated = deepcopy(routes["KRX|krx_only"])
    for row in integrated["realtime_types"].values():
        row.update(item="005930_AL", market_suffix="_AL", market_route="krx_nxt_integrated", effective_venue="")
    routes["|krx_nxt_integrated"] = integrated
    snapshot["shared_transport_producer"]["registered_items"].append("005930_AL")
    path.write_text(json.dumps(snapshot))
    owner._transport_comparison = read_shared_widget_quote(context, now_ts=now, path=path)
    assert owner._transport_comparison["ws_request_code"] == "005930_AL"
    attach_transport_census(owner, payload)
    bucket = next(iter(payload["market_data_transport"]["census"]["windows"].values()))
    assert bucket["expected_comparisons"] == bucket["valid_ws"] == 2
    assert bucket["ws_source_items"] == {
        "005930": {"valid_ws": 1, "ws_source_gap": 0},
        "005930_AL": {"valid_ws": 1, "ws_source_gap": 0},
    }


@pytest.mark.parametrize("defect", ["old_book", "future_trade", "new_epoch", "wrong_route", "wrong_item",
    "partial_book", "crossed_book", "dead_producer", "missing_producer", "not_registered", "duplicate_route",
    "future_file", "wrong_session", "wrong_authority", "bool_epoch", "bool_stock_epoch", "non_object", "wrong_venue", "disconnected"])
def test_shared_widget_reader_rejects_unproven_transport(tmp_path, monkeypatch, defect):
    import json
    from src.trading.market.shared_ws_snapshot import read_shared_widget_quote
    path, context, now, snapshot = _shared_widget_fixture(tmp_path, monkeypatch)
    stock = snapshot["stocks"]["005930"]
    rows = stock["machine_confirmation_routes"]["KRX|krx_only"]["realtime_types"]
    if defect == "old_book": rows["0D"]["observed_epoch"] = now - 21
    elif defect == "future_trade": rows["0B"]["observed_epoch"] = now + 1
    elif defect == "new_epoch": snapshot["shared_transport_producer"]["transport_epoch"] = 2
    elif defect == "wrong_route": rows["0D"]["market_route"] = "nxt_only"
    elif defect == "wrong_venue": rows["0D"]["effective_venue"] = "NXT"
    elif defect == "disconnected": snapshot["shared_transport_producer"]["connection_available"] = False
    elif defect == "wrong_item": rows["0D"]["item"] = "005930_AL"
    elif defect == "partial_book": rows["0D"]["orderbook"]["asks"][0].pop("volume")
    elif defect == "crossed_book": rows["0D"]["orderbook"]["asks"][0]["price"] = 9980
    elif defect == "dead_producer": snapshot["shared_transport_producer"]["process"]["start_ticks"] += 1
    elif defect == "missing_producer": snapshot.pop("shared_transport_producer")
    elif defect == "not_registered": snapshot["shared_transport_producer"]["registered_items"] = []
    elif defect == "duplicate_route": stock["machine_confirmation_routes"]["duplicate"] = {"realtime_types": rows}
    elif defect == "future_file": snapshot["generated_at_epoch"] = now + 2
    elif defect == "wrong_session": context.active = False
    elif defect == "wrong_authority": snapshot["runtime_effect"] = True
    elif defect == "bool_epoch": rows["0D"]["transport_epoch"] = True
    elif defect == "bool_stock_epoch": stock["market_data_transport_epoch"] = True
    elif defect == "non_object": snapshot = []
    path.write_text(json.dumps(snapshot))
    result = read_shared_widget_quote(context, now_ts=now, path=path)
    assert result["status"] == "source_gap", result
    assert result["selected_input"] == "existing_rest"


def test_shared_transport_census_preserves_failed_and_different_observations(tmp_path, monkeypatch):
    from datetime import datetime, timezone
    from types import SimpleNamespace
    from src.trading.market.shared_ws_snapshot import read_shared_widget_quote, compare_widget_rest, attach_transport_census
    path, context, now, _ = _shared_widget_fixture(tmp_path, monkeypatch)
    source = read_shared_widget_quote(context, now_ts=now, path=path)
    owner = SimpleNamespace(_transport_comparison=source)
    payload = {"observed_at_kst": datetime.fromtimestamp(now, timezone.utc).isoformat(), "status": "unavailable"}
    attach_transport_census(owner, payload)
    bbo = {k:v for k,v in source["values"].items() if k!='current_price'}
    stamp = datetime.fromtimestamp(now, timezone.utc)
    compare_widget_rest(source, current_price=10000, bbo=bbo, quote_received_at=stamp, bbo_received_at=stamp)
    assert source["comparison_status"] == "matched_fields"
    assert source["same_observation_proven"] is False
    bbo["best_bid_qty"] = 99
    compare_widget_rest(source, current_price=10000, bbo=bbo, quote_received_at=stamp, bbo_received_at=stamp)
    assert source["comparison_status"] == "different_observations"
    attach_transport_census(owner, payload)
    bucket = next(iter(source["census"]["windows"].values()))
    assert bucket["expected_comparisons"] == bucket["valid_ws"] + bucket["ws_source_gap"] == 2
    assert bucket["rest_not_observed"] == bucket["different_observations"] == 1
    assert bucket["producer_generation_mixed"] is False
    assert bucket["producer_generation_missing"] is False


@pytest.mark.parametrize("change", ["pid", "start_ticks", "boot_id", "source_commit", "transport_epoch", "missing"])
def test_shared_transport_census_marks_mixed_window_without_erasing_gaps(tmp_path, monkeypatch, change):
    from copy import deepcopy
    from datetime import datetime, timezone
    from types import SimpleNamespace
    from src.trading.market.shared_ws_snapshot import read_shared_widget_quote, attach_transport_census
    path, context, now, _ = _shared_widget_fixture(tmp_path, monkeypatch)
    source = read_shared_widget_quote(context, now_ts=now, path=path)
    owner = SimpleNamespace(_transport_comparison=source)
    payload = {"observed_at_kst": datetime.fromtimestamp(now, timezone.utc).isoformat()}
    attach_transport_census(owner, payload)
    original = deepcopy(source["census"]["windows"])
    if change == "missing":
        source.pop("producer")
        source["status"] = "source_gap"
    elif change in {"pid", "start_ticks", "boot_id"}:
        process = source["producer"]["process"]
        process[change] = "new-boot" if change == "boot_id" else process[change] + 1
    else:
        source["producer"][change] = "b" * 40 if change == "source_commit" else 2
    attach_transport_census(owner, payload)
    bucket = next(iter(source["census"]["windows"].values()))
    assert bucket["producer_generation"] == next(iter(original.values()))["producer_generation"]
    assert bucket["producer_generation_mixed"] is True
    assert bucket["producer_generation_missing"] is (change == "missing")
    assert bucket["expected_comparisons"] == bucket["valid_ws"] + bucket["ws_source_gap"] == 2
    assert bucket["rest_not_observed"] == 2
    # A later complete window has its own generation, not a reset of history.
    payload["observed_at_kst"] = datetime.fromtimestamp(now + 900, timezone.utc).isoformat()
    attach_transport_census(owner, payload)
    windows = source["census"]["windows"]
    assert len(windows) == 2
    assert windows[str(int(now))]["producer_generation_mixed"] is True
    assert windows[str(int(now + 900))]["producer_generation_mixed"] is False
    assert source["selected_input"] == "existing_rest"


def test_shared_transport_census_keeps_unknown_generation_and_bounded_history(tmp_path, monkeypatch):
    from datetime import datetime, timezone
    from types import SimpleNamespace
    from src.trading.market.shared_ws_snapshot import read_shared_widget_quote, attach_transport_census
    path, context, now, _ = _shared_widget_fixture(tmp_path, monkeypatch)
    source = read_shared_widget_quote(context, now_ts=now, path=path)
    producer = source.pop("producer")
    source["status"] = "source_gap"
    owner = SimpleNamespace(_transport_comparison=source)
    payload = {"observed_at_kst": datetime.fromtimestamp(now, timezone.utc).isoformat()}
    attach_transport_census(owner, payload)
    source["producer"] = producer
    source["status"] = "valid_ws_comparison_input"
    attach_transport_census(owner, payload)
    bucket = source["census"]["windows"][str(int(now))]
    assert bucket["producer_generation"] is None
    assert bucket["producer_generation_missing"] is True
    assert bucket["producer_generation_mixed"] is True
    assert bucket["expected_comparisons"] == 2
    assert bucket["ws_source_gap"] == bucket["valid_ws"] == 1
    for offset in range(1, 6):
        payload["observed_at_kst"] = datetime.fromtimestamp(now + 900 * offset, timezone.utc).isoformat()
        attach_transport_census(owner, payload)
    windows = source["census"]["windows"]
    assert len(windows) == 4
    assert min(map(int, windows)) == now + 1800


def test_shared_transport_census_does_not_relabel_parent_counts_after_fork(tmp_path, monkeypatch):
    from datetime import datetime, timezone
    from types import SimpleNamespace
    from src.trading.market import shared_ws_snapshot as shared
    path, context, now, _ = _shared_widget_fixture(tmp_path, monkeypatch)
    source = shared.read_shared_widget_quote(context, now_ts=now, path=path)
    owner = SimpleNamespace(_transport_comparison=source)
    payload = {"observed_at_kst": datetime.fromtimestamp(now, timezone.utc).isoformat()}
    shared.attach_transport_census(owner, payload)
    parent = source["census"]
    child = {**parent["consumer_process"], "pid": parent["consumer_process"]["pid"] + 1}
    monkeypatch.setattr(shared.os, "getpid", lambda: child["pid"])
    monkeypatch.setattr(shared, "process_generation", lambda _: child)
    shared.attach_transport_census(owner, payload)
    assert source["census"]["consumer_process"] == child
    bucket = source["census"]["windows"][str(int(now))]
    assert bucket["expected_comparisons"] == 1
    assert parent["consumer_process"] != child
    assert parent["windows"][str(int(now))]["expected_comparisons"] == 1


def test_shared_transport_census_keeps_counts_on_process_provenance_read_failure(tmp_path, monkeypatch):
    from datetime import datetime, timezone
    from types import SimpleNamespace
    from src.trading.market import shared_ws_snapshot as shared
    path, context, now, _ = _shared_widget_fixture(tmp_path, monkeypatch)
    owner = SimpleNamespace(_transport_comparison=shared.read_shared_widget_quote(context, now_ts=now, path=path))
    payload = {"observed_at_kst": datetime.fromtimestamp(now, timezone.utc).isoformat()}
    shared.attach_transport_census(owner, payload)
    def unavailable(_):
        raise OSError("proc_read_unavailable")
    monkeypatch.setattr(shared, "process_generation", unavailable)
    owner._transport_comparison.update(status="source_gap", comparison_status="rest_not_observed")
    shared.attach_transport_census(owner, payload)
    census = payload["market_data_transport"]["census"]
    assert census["consumer_process"]["status"] == "process_provenance_unavailable"
    bucket = census["windows"][str(int(now))]
    assert bucket["expected_comparisons"] == 2
    assert bucket["valid_ws"] == bucket["ws_source_gap"] == 1


@pytest.mark.parametrize(
    "stamp,expected",
    [(100000, 500), (101000, -500), (True, None), ("bad", None), (float("nan"), None)],
)
def test_rest_clock_and_common_health_have_identical_age_without_future_clamp(
    stamp, expected
):
    payload = {
        "source": "ka10004_rest_orderbook",
        "stock_code": "005930",
        "request_code": "005930_NX",
        "rest_freshness_basis": "response_received_epoch_ms",
        "rest_received_ts_ms": stamp,
        "best_bid": 9990,
        "best_ask": 10010,
        "age_ms": 0,
    }
    quote = quote_input_from_rest_orderbook(payload, now_ts=100.5)
    health = build_market_data_health(payload, now_ts=100.5)
    rest = health["rest_quote"]
    assert quote.age_ms == rest["quote_receive_age_ms"] == expected
    assert rest["market_data_scope"] == "NXT"
    assert rest["trade_activity_state"] == "OBSERVATION_UNPROVEN"
    if expected is None or expected < 0:
        assert rest["quote_state"] != "fresh"
        assert not build_quote_consistency_snapshot(
            rest=quote, config=_config()
        ).safety_exit_allowed


def test_program_packet_cannot_refresh_executable_ws_book():
    ws = quote_input_from_ws(
        {
            "curr": 10000,
            "best_bid": 9990,
            "best_ask": 10010,
            "last_ws_update_ts": 100.0,
            "last_realtime_type_ts": {"0D": 90.0, "0w": 100.0},
        },
        now_ts=100.0,
    )
    assert ws.age_ms == 10000
    assert build_quote_consistency_snapshot(ws=ws, config=_config()).entry_blocked


def test_missing_depth_provenance_cannot_use_transport_timestamp():
    ws = quote_input_from_ws(
        {
            "curr": 10000,
            "last_ws_update_ts": 100.0,
            "last_realtime_type_ts": {"0w": 100.0},
        },
        now_ts=100.0,
    )
    assert ws.age_ms is None


def test_market_data_health_keeps_missing_and_cross_epoch_unproven():
    frame = {
        "last_ws_update_ts": 100.0,
        "market_data_transport_epoch": 2,
        "realtime_type_snapshots_by_route": {
            "KRX|krx": {
                "0D": {
                    "item": "005930",
                    "observed_epoch": 100.0,
                    "transport_epoch": 2,
                    "effective_venue": "KRX",
                    "market_route": "krx",
                    "orderbook": {
                        "bids": [{"price": 9990}],
                        "asks": [{"price": 10010}],
                    },
                },
                "0B": {
                    "item": "005930",
                    "observed_epoch": 85.0,
                    "transport_epoch": 1,
                    "effective_venue": "KRX",
                    "market_route": "krx",
                },
            }
        },
    }
    health = build_market_data_health(frame, now_ts=100.0)
    route = health["routes"]["KRX|krx"]
    assert route["quote_state"] == "fresh"
    assert route["trade_activity_state"] == "OBSERVATION_UNPROVEN"
    assert route["quiet_episode_count"] is None
    assert health["transport_receive_age_ms"] == 0
    assert health["decision_authority"] is False


@pytest.mark.parametrize("bad_value", [True, "2", 2.0, -1, 4, None])
def test_serialized_quiet_episode_count_requires_exact_bounded_integer(bad_value):
    from src.trading.market.quote_consistency import build_market_data_health

    quote = {
        "item": "005930",
        "market_route": "krx",
        "effective_venue": "KRX",
        "transport_epoch": 2,
        "observed_epoch": 100.0,
        "orderbook": {"bids": [{"price": 9990}], "asks": [{"price": 10010}]},
    }
    health = build_market_data_health(
        {
            "market_data_transport_epoch": 2,
            "realtime_type_snapshots_by_route": {
                "KRX|krx": {
                    "0D": quote,
                    "0B": {**quote, "observed_epoch": 70.0},
                    "quiet_tape_observation": {
                        "last_quote": 100.0,
                        "last_trade": 70.0,
                        "closed_episodes": bad_value,
                    },
                }
            },
        },
        now_ts=100.0,
    )
    route = health["routes"]["KRX|krx"]
    assert route["quote_state"] == "fresh"
    assert route["trade_activity_state"] == "OBSERVATION_UNPROVEN"
    assert route["quiet_episode_count"] is None


@pytest.mark.parametrize("field", ["0B", "0D"])
def test_boolean_route_epoch_is_not_current_transport_proof(field):
    from src.trading.market.quote_consistency import build_market_data_health

    quote = {
        "item": "005930",
        "market_route": "krx",
        "effective_venue": "KRX",
        "transport_epoch": 1,
        "observed_epoch": 100.0,
        "orderbook": {"bids": [{"price": 9990}], "asks": [{"price": 10010}]},
    }
    records = {
        "0D": dict(quote),
        "0B": {**quote, "observed_epoch": 95.0},
        "quiet_tape_observation": {
            "last_quote": 100.0,
            "last_trade": 95.0,
            "closed_episodes": 0,
        },
    }
    records[field]["transport_epoch"] = True
    health = build_market_data_health(
        {
            "market_data_transport_epoch": 1,
            "realtime_type_snapshots_by_route": {"KRX|krx": records},
        },
        now_ts=100.0,
    )
    assert health["routes"]["KRX|krx"]["trade_activity_state"] == "OBSERVATION_UNPROVEN"
    if field == "0D":
        assert health["routes"]["KRX|krx"]["quote_state"] == "unproven"
        assert health["executable_quote_receive_age_ms"] is None


def test_market_data_health_future_quote_is_not_fresh():
    health = build_market_data_health(
        {
            "market_data_transport_epoch": 2,
            "realtime_type_snapshots_by_route": {
                "KRX|krx": {"0D": {"observed_epoch": 101.0, "transport_epoch": 2}}
            },
        },
        now_ts=100.0,
    )
    assert health["routes"]["KRX|krx"]["quote_state"] == "future"


def test_future_depth_timestamp_cannot_pass_quote_consistency():
    ws = quote_input_from_ws(
        {
            "curr": 10000,
            "best_bid": 9990,
            "best_ask": 10010,
            "last_realtime_type_ts": {"0D": 101.0},
        },
        now_ts=100.0,
    )
    assert ws.age_ms == -1000
    assert build_quote_consistency_snapshot(ws=ws, config=_config()).entry_blocked


def test_exact_inline_trade_quote_remains_usable_without_fresh_depth():
    frame = {
        "best_bid": 9990,
        "best_ask": 10010,
        "last_realtime_type_ts": {"0B": 100.0},
        "last_realtime_type_item": {"0B": "005930"},
        "market_data_transport_epoch": 2,
        "realtime_type_snapshots_by_route": {
            "KRX|krx": {
                "0B": {
                    "item": "005930",
                    "observed_epoch": 100.0,
                    "transport_epoch": 2,
                    "inline_best_bid": 9990,
                    "inline_best_ask": 10010,
                }
            }
        },
    }
    assert ws_quote_receive_age_ms(frame, now_ts=100.1) < 101
    frame["realtime_type_snapshots_by_route"]["KRX|krx"]["0B"]["inline_best_bid"] = 9980
    assert ws_quote_receive_age_ms(frame, now_ts=100.1) is None


def test_serialized_quiet_observation_keeps_pure_counter_and_expiry():
    record = {
        "item": "005930",
        "market_route": "krx",
        "effective_venue": "KRX",
        "transport_epoch": 2,
        "observed_epoch": 110.0,
        "orderbook": {"bids": [{"price": 9990}], "asks": [{"price": 10010}]},
    }
    frame = {
        "market_data_transport_epoch": 2,
        "realtime_type_snapshots_by_route": {
            "KRX|krx": {
                "0D": record,
                "0B": {**record, "observed_epoch": 100.0},
                "quiet_tape_observation": {
                    "last_quote": 110.0,
                    "last_trade": 100.0,
                    "closed_episodes": 0,
                },
            }
        },
    }
    for _ in range(100):
        route = build_market_data_health(frame, now_ts=110.0)["routes"]["KRX|krx"]
        assert route["quiet_episode_count"] == 1
    expired = build_market_data_health(frame, now_ts=114.0)["routes"]["KRX|krx"]
    assert expired["trade_activity_state"] == "OBSERVATION_UNPROVEN"


@pytest.mark.parametrize(
    "route,item,venue,proven",
    [
        ("krx_nxt_integrated", "005930_AL", "UNKNOWN", True),
        ("krx_only", "005930", "UNKNOWN", False),
        ("krx_nxt_integrated", "005930", "UNKNOWN", False),
        ("krx_only", "005930", "KRX", True),
    ],
)
def test_activity_scope_is_not_underlying_integrated_exchange(
    route, item, venue, proven
):
    record = {
        "item": item,
        "market_route": route,
        "effective_venue": venue,
        "transport_epoch": 2,
        "observed_epoch": 110.0,
        "orderbook": {"bids": [{"price": 9990}], "asks": [{"price": 10010}]},
    }
    records = {
        "0D": record,
        "0B": {**record, "observed_epoch": 105.0},
        "quiet_tape_observation": {
            "last_quote": 110.0,
            "last_trade": 105.0,
            "closed_episodes": 0,
        },
    }
    frame = {
        "market_data_transport_epoch": 2,
        "realtime_type_snapshots_by_route": {"scope": records},
    }
    facts = build_market_data_health(frame, now_ts=110.0)["routes"]["scope"]
    assert facts["observation_continuity_proven"] is proven
    assert facts["effective_venue"] == venue
    assert facts["underlying_event_venue_proven"] is (proven and venue == "KRX")
    assert facts["trade_activity_state"] == (
        "RECENT_TRADE" if proven else "OBSERVATION_UNPROVEN"
    )
    # Neither companion timestamps nor cross-epoch records can prove activity.
    records["quiet_tape_observation"]["last_trade"] = 109.0
    assert (
        build_market_data_health(frame, now_ts=110.0)["routes"]["scope"][
            "observation_continuity_proven"
        ]
        is False
    )
    records["quiet_tape_observation"]["last_trade"] = 105.0
    records["0B"]["transport_epoch"] = 1
    assert (
        build_market_data_health(frame, now_ts=110.0)["routes"]["scope"][
            "observation_continuity_proven"
        ]
        is False
    )


def _ws(
    price: int,
    *,
    age_ms: int = 100,
    best_bid: int | None = None,
    best_ask: int | None = None,
):
    best_bid = best_bid if best_bid is not None else price - 10
    best_ask = best_ask if best_ask is not None else price + 10
    return quote_input_from_ws(
        {
            "curr": price,
            "best_bid": best_bid,
            "best_ask": best_ask,
            "quote_consistency_ws_age_ms": age_ms,
        }
    )


def _rest(best_bid: int, best_ask: int, *, age_ms: int = 200, current_price: int = 0):
    return quote_input_from_rest_orderbook(
        {
            "best_bid": best_bid,
            "best_ask": best_ask,
            "rest_current_price": current_price,
            "rest_mid_price": int(round((best_bid + best_ask) / 2.0)),
            "age_ms": age_ms,
        }
    )


def _config() -> QuoteConsistencyConfig:
    return QuoteConsistencyConfig(
        max_ws_age_ms=700,
        max_rest_age_ms=1500,
        ok_gap_bps=30,
        warn_gap_bps=80,
        emergency_rest_timeout_ms=400,
        block_entry_on_divergence=True,
    )


def test_quote_consistency_ok_warning_and_diverged(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_QUOTE_CONSISTENCY_RUNTIME_ENABLED", "true")

    ok = build_quote_consistency_snapshot(
        ws=_ws(10000), rest=_rest(9980, 10020), config=_config()
    )
    assert ok.quality_state == "ok"
    assert ok.entry_blocked is False
    assert ok.executable_buy_price == 10020
    assert ok.passive_buy_price == 9980

    warning = build_quote_consistency_snapshot(
        ws=_ws(10000), rest=_rest(9920, 9960), config=_config()
    )
    assert warning.quality_state == "warning"
    assert warning.entry_blocked is False

    diverged = build_quote_consistency_snapshot(
        ws=_ws(10000), rest=_rest(9700, 9740), config=_config()
    )
    assert diverged.quality_state == "diverged"
    assert diverged.entry_blocked is True
    assert diverged.runtime_action == "block_entry_reprice_scale_in"


def test_quote_consistency_stale_missing_and_single_source(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_QUOTE_CONSISTENCY_RUNTIME_ENABLED", "true")

    ws_only = build_quote_consistency_snapshot(ws=_ws(10000), config=_config())
    assert ws_only.quality_state == "single_source"
    assert ws_only.canonical_mark_price == 10000

    stale = build_quote_consistency_snapshot(
        ws=_ws(10000, age_ms=2000),
        rest=_rest(9980, 10020, age_ms=4000),
        config=_config(),
    )
    assert stale.quality_state == "stale"
    assert stale.entry_blocked is True

    missing = build_quote_consistency_snapshot(config=_config())
    assert missing.quality_state == "missing"
    assert missing.entry_blocked is True


def test_rest_orderbook_age_prefers_received_timestamp_over_static_age_ms():
    rest = quote_input_from_rest_orderbook(
        {
            "best_bid": 9980,
            "best_ask": 10020,
            "rest_mid_price": 10000,
            "age_ms": 0,
            "bid_req_base_tm": "093001",
            "rest_received_ts_ms": 1_000_000,
        },
        now_ts=1002.0,
    )

    assert rest.age_ms == 2000.0


def test_ka10004_rest_orderbook_does_not_trust_static_age_without_received_timestamp():
    rest = quote_input_from_rest_orderbook(
        {
            "source": "ka10004_rest_orderbook",
            "best_bid": 9980,
            "best_ask": 10020,
            "rest_mid_price": 10000,
            "age_ms": 0,
            "bid_req_base_tm": "093001",
            "bid_req_base_tm_authority": "raw_not_freshness_input",
        },
        now_ts=1002.0,
    )

    assert rest.age_ms is None

    snapshot = build_quote_consistency_snapshot(rest=rest, config=_config())
    assert snapshot.quality_state == "stale"
    assert snapshot.entry_blocked is True
    assert snapshot.reason == "quote_stale"


def test_safety_exit_does_not_block_on_divergence_or_late_rest(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_QUOTE_CONSISTENCY_RUNTIME_ENABLED", "true")

    diverged = build_quote_consistency_snapshot(
        ws=_ws(10000),
        rest=_rest(9400, 9440),
        safety_exit=True,
        side="sell",
        config=_config(),
    )
    assert diverged.quality_state == "diverged"
    assert diverged.entry_blocked is False
    assert diverged.safety_exit_allowed is True
    assert diverged.executable_sell_price == 9400

    stale_rest = build_quote_consistency_snapshot(
        ws=_ws(10000),
        rest=_rest(9400, 9440, age_ms=5000),
        safety_exit=True,
        side="sell",
        config=_config(),
    )
    assert stale_rest.quality_state == "single_source"
    assert stale_rest.entry_blocked is False
    assert stale_rest.safety_exit_allowed is True
    assert stale_rest.executable_sell_price > 0
