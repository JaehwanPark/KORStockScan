"""Exact source delivery races without protocol or native FSM changes."""

import asyncio
from copy import deepcopy
import json
from types import SimpleNamespace

import pytest

from src.engine.scalping import zero_base_probe as probe
from src.engine.scalping import reversal_source_diagnostics as diagnostics


ITEM = "123456_AL"
ROUTE = "krx_nxt_integrated"
KEY = "_AL|krx_nxt_integrated"


def _snapshot(*, depth=True, epoch=3):
    typed = {
        "0B": {"item": ITEM, "market_route": ROUTE, "transport_epoch": epoch,
               "observed_epoch": 11.0, "current_price": 10000},
    }
    if depth:
        typed["0D"] = {
            "item": ITEM, "market_route": ROUTE, "transport_epoch": epoch,
            "observed_epoch": 11.0,
            "orderbook": {"asks": [{"price": 10010, "volume": 10}],
                          "bids": [{"price": 10000, "volume": 10}]},
        }
    return {
        "market_data_transport_epoch": epoch,
        "last_realtime_type_item": {kind: ITEM for kind in typed},
        "last_realtime_type_market_route": {kind: ROUTE for kind in typed},
        "realtime_type_snapshots_by_route": {KEY: typed},
        "recent_trade_ticks_by_route": {KEY: [
            {"received_at_ms": 11000, "item": ITEM, "market_route": ROUTE,
             "transport_epoch": epoch, "route_sequence": 1},
        ]},
    }


@pytest.mark.parametrize("arrival", ["between_check_and_wait", "during_wait"])
@pytest.mark.parametrize("initial_transport", [None, 3])
def test_residence_wait_uses_version_captured_before_source_check(monkeypatch, arrival, initial_transport):
    elapsed = [0.0]
    sequence = [0]
    reads = []
    waits = []
    ready = [False]
    manager = SimpleNamespace(_market_data_transport_epoch=initial_transport)
    monkeypatch.setattr(probe.time, "monotonic", lambda: elapsed[0])
    monkeypatch.setattr(diagnostics, "observation_sequence", lambda _item: sequence[0])
    monkeypatch.setattr(diagnostics, "notify_observation", lambda _item: sequence.__setitem__(0, sequence[0]+1))

    def publish():
        ready[0] = True
        assert probe.notify_exact_probe_source(manager, item=ITEM, transport_epoch=3)

    def read(_code):
        reads.append(None)
        result = _snapshot(depth=ready[0])
        if len(reads) == 2 and arrival == "between_check_and_wait":
            publish()
        return result

    def wait(_item, captured, timeout):
        waits.append((captured, timeout))
        if arrival == "during_wait":
            publish()
        if captured == sequence[0]:
            elapsed[0] += timeout

    manager.get_latest_data = read
    monkeypatch.setattr(diagnostics, "wait_observation", wait)
    data, observation, reason = probe.wait_for_exact_probe_ws_data(
        manager, code="123456", route=ROUTE, after_epoch=10,
        now=lambda: 11+elapsed[0], timeout_sec=0,
        residence_deadline_epoch=13,
    )
    assert data and reason == "ready"
    assert len(reads) == 3 and waits == [(0, 1.0)]
    assert observation["wait_ms"] == 0
    assert probe._SOURCE_WAITERS == {}


@pytest.mark.parametrize("stop", ["timeout", "transport", "policy"])
def test_source_wake_preserves_original_deadline_and_guards(monkeypatch, stop):
    elapsed = [0.0]
    wakes = []
    manager = SimpleNamespace(_market_data_transport_epoch=3)
    monkeypatch.setattr(probe.time, "monotonic", lambda: elapsed[0])
    manager.get_latest_data = lambda _code: _snapshot(
        depth=False, epoch=4 if stop == "transport" and wakes else 3,
    )

    def wait(_item, _sequence, timeout):
        wakes.append(timeout)
        # A spurious wake must rerun the guards and retain the original end.
        elapsed[0] += min(timeout, 0.25)

    monkeypatch.setattr(diagnostics, "wait_observation", wait)
    data, observation, reason = probe.wait_for_exact_probe_ws_data(
        manager, code="123456", route=ROUTE, after_epoch=10,
        now=lambda: 11+elapsed[0], timeout_sec=0,
        residence_deadline_epoch=12,
        readiness_guard=lambda: "policy_changed" if stop == "policy" and wakes else "",
    )
    assert not data
    assert reason == {"timeout": "0D_missing", "transport": "transport_changed_during_source_wait",
                      "policy": "policy_changed"}[stop]
    assert elapsed[0] <= 1.0
    assert observation["residence_deadline_epoch"] == 12
    assert probe._SOURCE_WAITERS == {}


def test_probe_quote_wake_is_exact_coalesced_and_cleans_up(monkeypatch):
    manager = SimpleNamespace()
    other_manager = SimpleNamespace()
    notified = []
    monkeypatch.setattr(diagnostics, "notify_observation", notified.append)
    with probe._ExactProbeSourceWait(manager, ITEM) as source_wait:
        source_wait.sequence(3, active=True)
        for item, epoch, producer in [("123456_NX", 3, manager), (ITEM, 4, manager),
                                      (ITEM, 3, other_manager)]:
            assert not probe.notify_exact_probe_source(producer, item=item, transport_epoch=epoch)
        for _ in range(1000):
            probe.notify_exact_probe_source(manager, item=ITEM, transport_epoch=3)
        assert notified == [ITEM]
        source_wait.sequence(3, active=True)
        assert probe.notify_exact_probe_source(manager, item=ITEM, transport_epoch=3)
        assert notified == [ITEM, ITEM]
    assert not probe.notify_exact_probe_source(manager, item=ITEM, transport_epoch=3)
    assert probe._SOURCE_WAITERS == {}


def test_source_wait_subscription_is_removed_on_exception(monkeypatch):
    monkeypatch.setattr(diagnostics, "observation_sequence", lambda _item: 0)
    with pytest.raises(ValueError):
        with probe._ExactProbeSourceWait(SimpleNamespace(), ITEM) as source_wait:
            source_wait.sequence(3, active=True)
            raise ValueError("source reader failed")
    assert probe._SOURCE_WAITERS == {}


def test_live_0d_publishes_before_exact_wake_without_advancing_native_fsm(monkeypatch):
    from src.engine import kiwoom_websocket as websocket
    from src.engine.scalping import entry_machine_source_recovery as recovery
    from src.engine.scalping import reversal_current_backend as native
    from src.engine.monitoring import runtime_performance as performance

    manager = websocket.KiwoomWSManager("test-token")
    manager._market_data_transport_epoch = 3
    manager.subscribed_codes.add("123456")
    manager._registered_items_by_code["123456"] = (ITEM,)
    manager._registered_item_epochs[ITEM] = 3
    manager._registered_item_types[ITEM] = ("0B", "0D")
    manager._record_main_source_registration_locked(ITEM, ("0B", "0D"), source="test")
    monkeypatch.setattr(manager, "_maybe_write_dashboard_snapshot", lambda: None)
    monkeypatch.setattr(manager, "_queue_tick_event", lambda *_a, **_k: None)
    monkeypatch.setattr(native, "observe_normalized", lambda *_a, **_k: pytest.fail("0D advanced native FSM"))
    monkeypatch.setattr(performance, "record_native_ready", lambda *_a, **_k: pytest.fail("0D counted native ready"))
    pending = []
    notified = []

    def pending_quote(code, item, snapshot, *, now):
        source = snapshot["realtime_type_snapshots_by_route"][KEY]["0D"]
        assert source["item"] == item == ITEM and code == "123456"
        assert source["transport_epoch"] == 3
        assert source["orderbook"]["asks"][0]["price"] == 10010
        assert snapshot["orderbook"]["asks"][:1] == source["orderbook"]["asks"]
        assert snapshot["last_realtime_type_ts"]["0D"] == source["observed_epoch"]
        assert snapshot["last_realtime_type_item"]["0D"] == ITEM
        assert snapshot["last_realtime_type_transport_epoch"]["0D"] == 3
        depth = snapshot["recent_depth_ticks_by_route"][KEY][0]
        assert depth["route_sequence"] == source["route_sequence"]
        assert depth["received_at_ms"] / 1000 == source["observed_epoch"]
        assert source["market_source_latency"]["route_sequence"] == source["route_sequence"]
        assert snapshot["time"]
        assert snapshot["source_recovery_lease"]["registration_sent_at_epoch"] > 0
        pending.append(deepcopy(snapshot["source_recovery_lease"]))
        return False

    monkeypatch.setattr(recovery, "notify_pending_quote", pending_quote, raising=False)
    monkeypatch.setattr(diagnostics, "notify_observation", notified.append)
    with probe._ExactProbeSourceWait(manager, ITEM) as source_wait:
        source_wait.sequence(3, active=True)
        for _ in range(10):
            asyncio.run(manager._handle_message(json.dumps({"trnm": "REAL", "data": [{
                "type": "0D", "item": ITEM,
                "values": {"21": "133500", "41": "10010", "51": "10000", "61": "10", "71": "10"},
            }]})))
    assert notified == [ITEM]
    assert len(pending) == 10  # Recovery owner coalesces its own eligible target.
    snapshot = manager.get_exact_item_data("123456", ITEM)
    assert snapshot["source_recovery_lease"] == pending[-1]
    assert "0B" not in snapshot["realtime_type_snapshots_by_route"][KEY]


@pytest.mark.parametrize("damage", ["item", "route", "epoch", "registration", "type", "unpublished"])
def test_quote_notification_rejects_wrong_identity_or_unpublished_source(monkeypatch, damage):
    from src.engine.kiwoom_websocket import KiwoomWSManager
    manager = KiwoomWSManager("test-token")
    manager._market_data_transport_epoch = 3
    manager._registered_items_by_code["123456"] = (ITEM,)
    manager._registered_item_epochs[ITEM] = 3
    manager._registered_item_types[ITEM] = ("0B", "0D")
    target = _snapshot()
    source = target["realtime_type_snapshots_by_route"][KEY]["0D"]
    source["realtime_type"] = "0D"
    if damage == "item": source["item"] = "123456_NX"
    elif damage == "route": source["market_route"] = "nxt_only"
    elif damage == "epoch": source["transport_epoch"] = 4
    elif damage == "registration": manager._registered_item_epochs[ITEM] = 2
    elif damage == "type": source["realtime_type"] = "0B"
    elif damage == "unpublished": source = dict(source)
    monkeypatch.setattr(probe, "notify_exact_probe_source", lambda *_a, **_k: pytest.fail("invalid source woke probe"))
    manager._notify_published_quote_source_locked("123456", target, source)


def test_source_lease_receipt_tracks_same_transport_reg_and_probe_custody(monkeypatch):
    from src.engine import kiwoom_websocket as websocket
    clock = [10.0]
    monkeypatch.setattr(websocket.time, "time", lambda: clock[0])
    manager = websocket.KiwoomWSManager("test-token")
    manager._market_data_transport_epoch = 3
    manager._registered_item_epochs[ITEM] = 3
    manager._registered_item_types[ITEM] = ("0B", "0D")
    manager._exact_probe_item_leases[ITEM] = {
        "lease_id": "physical-1", "epoch": 3, "interval_started_epoch": 9.0,
        "adopted": False, "removing": False,
    }
    manager._record_main_source_registration_locked(ITEM, ("0B", "0D"), source="test")
    original = manager._source_recovery_lease_locked(ITEM)
    assert original["registration_sent_at_epoch"] == 10
    assert original["physical_probe_lease_epoch"] == 3
    clock[0] = 11.0
    manager._record_main_source_registration_locked(ITEM, ("0B", "0D"), source="test")
    renewed = manager._source_recovery_lease_locked(ITEM)
    assert renewed["registration_sent_at_epoch"] == 11
    assert renewed != original
    manager._exact_probe_item_leases[ITEM]["removing"] = True
    releasing = manager._source_recovery_lease_locked(ITEM)
    assert releasing["physical_probe_lease_removing"] is True
    assert releasing != renewed
    manager._market_data_transport_epoch = 4
    assert manager._source_recovery_lease_locked(ITEM)["registration_sent_at_epoch"] is None


@pytest.mark.parametrize("second_preflight_allowed", [True, False])
def test_actual_probe_engine_recalculates_once_after_quote_only_preflight_failure(monkeypatch, second_preflight_allowed):
    """The real probe and AI preflight reach a new observer-role calculation."""
    from concurrent.futures import Future
    from dataclasses import replace
    from datetime import datetime
    from src.engine import ai_engine_openai as ai
    from src.engine.scalping import reversal_current_backend as backend
    from src.engine.scalping import continuous_reversal_policy_v6 as policy
    from src.engine.scalping import reversal_auxiliary_intraday as overlay
    from src.engine.scalping import ai_decision_trace as trace
    from src.engine.scalping import mechanistic_entry_runtime_policy as machine_policy
    from src.engine.scalping.entry_setup_scalping_rollout import PATH_ENV
    from src.tests.test_reversal_extended_policy import FIXTURES
    from src.tests.test_ai_engine_openai_transport import (
        _build_engine, _sample_ws_data, _sample_candles, _allowed_entry_candle_context,
    )
    fixture = deepcopy(next(value for value in FIXTURES.values() if value["event"]["venue"] == "SOR"))
    native = (fixture["event"], fixture["source"])
    original_native = deepcopy(native)
    event = native[0]
    stamp = event["epoch"] + .2
    clock = [stamp]
    monkeypatch.setattr(probe.time, "time", lambda: clock[0])
    monkeypatch.setattr(diagnostics, "observe_snapshot", lambda *a, **k: (deepcopy(native), {"native_source_current": True}))
    monkeypatch.setattr(diagnostics, "branch_readiness", lambda *a, **k: {})
    monkeypatch.setattr(diagnostics, "claim_snapshot_with_receipt", lambda *a, **k: pytest.fail("probe claimed a native event"))
    monkeypatch.setattr(backend, "backend", lambda *a: SimpleNamespace(_GENERATION="f" * 64))
    key = policy.C.cell_key(event["symbol"], event["market"], event["confirmation_price"])
    arm = policy.A.V1.ARMS[-1]
    family = dict(schema=policy.SCHEMA, family_sha256="f" * 64, execution_manifest_hash="e" * 64,
        machine_cells={key: {"routes": {"SOR": dict(backend="union_v6", scope_execution_hash="c" * 64,
            payload={"branches": [policy.C.branch(bid) for bid in event["branch_signals"]]})}}},
        auxiliary_cells={key: {"routes": {"SOR": {"payload": {"arm": arm, "binding": policy.A.binding(arm)}}}}})
    monkeypatch.setattr(policy, "validate_family", lambda *_a: None)
    monkeypatch.setattr(overlay, "apply_request", lambda _d, _p, _s, result: result)
    live = dict(enabled=True, status="active_bounded_krx_canary",
        selected_prompt_version=machine_policy.AI_VERSION, machine_bundle_sha256="b" * 64,
        primary_decision_owner="mechanistic_entry_adjudicator", ai_role="auxiliary_risk_screen_pass_veto_no_promotion",
        continuous_reversal=family, auxiliary_system_prompt="carrier", auxiliary_system_prompt_sha256="c" * 64)
    monkeypatch.setattr(ai, "resolve_live_prompt_policy", lambda **k: deepcopy(live))
    monkeypatch.setenv(PATH_ENV, "/test-selected-observer-quote")
    monkeypatch.setattr(ai, "TRADING_RULES", replace(ai.TRADING_RULES,
        OPENAI_ANALYZE_TARGET_PROMPT_VERSION="V2.13"))
    engine = _build_engine()
    monkeypatch.setattr(engine, "_call_openai_safe", lambda *a, **k: pytest.fail("probe called provider"))
    monkeypatch.setattr(engine, "_cache_get", lambda *a, **k: pytest.fail("probe reused AI cache"))
    records = []
    monkeypatch.setattr(trace, "trace_enabled", lambda: True)
    monkeypatch.setattr(trace, "_now", lambda: datetime.fromtimestamp(clock[0], policy.K.KST))
    monkeypatch.setattr(trace, "_append_jsonl", lambda _p, record: records.append(deepcopy(record)))
    code, item = event["symbol"], event["source_item"]
    route_key = "_AL|krx_nxt_integrated"
    ws = _sample_ws_data()
    ws.update(stock_code=code, curr=event["confirmation_price"], market_data_transport_epoch=event["native_epoch"],
        last_realtime_type_item={"0B": item, "0D": item},
        last_realtime_type_market_route={"0B": ROUTE, "0D": ROUTE},
        last_realtime_type_market_suffix={"0B": "_AL", "0D": "_AL"})
    typed = {"0B": dict(item=item, market_route=ROUTE, market_suffix="_AL", transport_epoch=event["native_epoch"],
        observed_epoch=stamp, route_sequence=30, current_price=event["confirmation_price"]),
        "0D": dict(item=item, market_route=ROUTE, market_suffix="_AL", transport_epoch=event["native_epoch"],
        observed_epoch=stamp - 2.9, route_sequence=40,
        orderbook={"asks": [{"price": event["entry_ask"], "volume": 10}],
                   "bids": [{"price": event["entry_ask"], "volume": 10}]})}
    ws["realtime_type_snapshots_by_route"] = {route_key: typed}
    ws["orderbook"] = deepcopy(typed["0D"]["orderbook"])
    ws["source_recovery_lease"] = dict(schema="entry_source_lease_v1", item=item,
        transport_epoch=event["native_epoch"], registration_epoch=event["native_epoch"],
        registration_sent_at_epoch=stamp - 4, realtime_types=["0B", "0D"], physical_probe_lease_id=None)
    ws["last_realtime_type_ts"] = {"0B": stamp, "0D": stamp - 2.9}
    ws["recent_trade_ticks_by_route"] = {route_key: [dict(
        item=item, market_route=ROUTE, transport_epoch=event["native_epoch"],
        received_at_ms=stamp * 1000, route_sequence=30,
        price=event["confirmation_price"], volume=10, aggressor_side="BUY",
    )]}
    initial_tape = deepcopy(typed["0B"])
    calls = []

    analyze_target = engine.analyze_target
    def record_analysis(*args, **kwargs):
        calls.append(clock[0])
        if len(calls) == 1:
            clock[0] += .2
        return analyze_target(*args, **kwargs)

    monkeypatch.setattr(engine, "analyze_target", record_analysis)
    built = []
    def context_builder(*_args, **_kwargs):
        built.append(None)
        context = _allowed_entry_candle_context()
        context["ai_market_snapshot_v1"].update(snapshot_id=f"probe-context-{len(built)}", stock_code=code,
            session_bucket=event["market"], effective_venue="SOR",
            sources={name: {"freshness_limit_ms": 3000} for name in ("current_price", "bbo", "tape")})
        allowed = len(built) > 1 and second_preflight_allowed
        context["ai_market_snapshot_v1"]["ai_input_preflight_v1"].update(
            allowed=allowed, source_allowed=allowed, feature_allowed=True,
            blockers=[] if allowed else ["bbo_stale"], feature_blockers=[],
            status="pass" if allowed else "blocked")
        return context

    manager = SimpleNamespace(subscribed_codes={code}, _market_data_transport_epoch=event["native_epoch"],
        _registered_items_by_code={code: (item,)},
        _registered_item_epochs={item: event["native_epoch"]}, _registered_item_types={item: ("0B", "0D")},
        get_exact_item_data=lambda *_a: deepcopy(ws),
        execute_release_exact_probe_item=lambda *_a: None)
    future = Future()
    future.set_result({"registered": True, "interval_started_epoch": stamp - 4})
    manager.execute_acquire_exact_probe_item = lambda *_a: future
    monkeypatch.setattr(probe, "resolve_entry_candle_session", lambda: event["market"])
    monkeypatch.setattr(probe, "_select_recent_ticks_with_source", lambda *_a, **_k: ([], "ws_exact_route", "fixture"))
    monkeypatch.setattr(probe, "exact_probe_rest_source_issue", lambda *_a, **_k: "")

    def wait_quote(_item, _sequence, _timeout):
        clock[0] += .1
        quote = typed["0D"]
        quote["orderbook"]["asks"][0]["price"] = event["entry_ask"] + 1
        quote.update(observed_epoch=clock[0], route_sequence=41,
            market_source_latency=dict(schema="market_source_latency_v1", item=item,
                transport_epoch=event["native_epoch"], route_sequence=41, packet_received_epoch=clock[0]))
        ws["last_realtime_type_ts"]["0D"] = clock[0]
        assert probe.notify_exact_probe_source(manager, item=item, transport_epoch=event["native_epoch"])

    monkeypatch.setattr(diagnostics, "wait_observation", wait_quote)
    result = probe.run_zero_base_probe(
        {"claim": {"code": code, "route": ROUTE, "observed_epoch": stamp - 1},
         "candidate": {"code": code, "route": ROUTE}},
        ws_manager=manager, ai_engine=engine, token="test", now=lambda: clock[0],
        native_wait_deadline_epoch=stamp + 60, ws_wait_min_exact_0b_count=0,
        candle_fetcher=lambda *_a, **_k: (_sample_candles(), {"request_code": item,
            "rest_received_ts_ms": int(clock[0] * 1000)}), context_builder=context_builder,
        tick_fetcher=lambda *_a, **_k: pytest.fail("probe refetched unchanged tape"),
    )
    assert len(calls) == 2
    assert result["quote_recovery_retry_attempt_count"] == 1
    records = [record for record in records if record.get("schema") == "mechanistic_entry_observation_v1"]
    assert len(records) == 2
    assert records[0]["source"]["assessment"]["action"] == "source_invalid"
    assert records[0]["label_context"]["evaluation_attempt_id"] != records[1]["label_context"]["evaluation_attempt_id"]
    assert typed["0B"] == initial_tape and native == original_native
    if not second_preflight_allowed:
        assert result["machine_evaluation_status"] == "source_quality_blocked_before_assessment"
        assert result.get("quote_recovery_recalculation_count", 0) == 0
        assert records[1]["source"]["assessment"]["action"] == "source_invalid"
        return
    assert result.get("machine_evaluation_status") == "assessed", (
        result.get("reason"), result.get("machine_contract_error"))
    assert result["quote_recovery_recalculation_count"] == 1
    assert records[1]["source"]["assessment"]["entry_source_quote_recovery"]["evaluation_role"] == "probe_observation"
    assert records[1]["source"]["auxiliary_request"]["input"]["entry_setup_evidence_v1"]["facts"]["entry_ask"] == event["entry_ask"] + 1
    assert result["native_observation"]["deadline_epoch"] == event["epoch"] + 5
