"""Fresh-source repair scheduling and guards, without broker/provider I/O."""

from copy import deepcopy
from types import SimpleNamespace

import pytest

from src.engine.scalping import entry_machine_source_recovery as R
from src.tests.test_entry_machine_observation import fixture, NOW, KEY


def source_failure(ws):
    rows = ws["realtime_type_snapshots_by_route"][KEY]
    return dict(
        provider_called=False,
        machine_evaluation_expected=True,
        machine_evaluation_status="source_quality_blocked_before_assessment",
        machine_source_invalid_receipt=True,
        machine_observation_sha256="a" * 64,
        machine_capture_status="captured",
        machine_bundle_sha256="b" * 64,
        evaluation_attempt_id="aims-source-failed",
        ai_input_preflight_realtime_type_provenance=deepcopy(rows),
        ai_input_preflight_source_timing={
            name: dict(freshness_limit_ms=3000)
            for name in ("current_price", "bbo", "tape")
        },
    )


def pending():
    ws, _ = fixture()
    stock = dict(
        code="005930",
        id=101,
        scanner_promotion_id="watch-1",
        scanner_generation_id="generation-1",
        effective_venue="KRX",
    )
    stock[R.STATE_KEY] = R.pending_after_failure(
        stock, source_failure(ws), now=NOW, cooldown_sec=90
    )
    return stock, ws


def advance(ws):
    for kind in ("0B", "0D"):
        ws["realtime_type_snapshots_by_route"][KEY][kind]["observed_epoch"] = NOW + 0.1


def test_only_new_exact_tape_schedules_fresh_calculation():
    stock, ws = pending()
    assert not R.recovery_refresh(stock, ws, now=NOW)["allowed"]
    ws["realtime_type_snapshots_by_route"][KEY]["0D"]["observed_epoch"] = NOW + 0.1
    assert not R.recovery_refresh(stock, ws, now=NOW + 0.2)["allowed"]
    advance(ws)
    before = deepcopy((stock, ws))
    ready = R.recovery_refresh(stock, ws, now=NOW + 0.2)
    assert ready["allowed"] and ready["reason"] == "machine_source_fresh_retry"
    assert ready["actual_order_submitted"] is False
    assert ready["broker_order_forbidden"] is True
    assert (stock, ws) == before


@pytest.mark.parametrize(
    "damage",
    [
        "symbol",
        "route",
        "epoch",
        "bool_epoch",
        "stale_quote",
        "future",
        "missing",
        "provider_late",
        "provider_future",
    ],
)
def test_new_receive_clock_cannot_recover_bad_source(damage):
    stock, ws = pending()
    advance(ws)
    rows = ws["realtime_type_snapshots_by_route"][KEY]
    if damage == "symbol":
        rows["0B"]["item"] = "000660_AL"
    elif damage == "route":
        rows["0D"]["market_route"] = "nxt_only"
    elif damage == "epoch":
        rows["0D"]["transport_epoch"] = 2
    elif damage == "bool_epoch":
        ws["market_data_transport_epoch"] = True
    elif damage == "stale_quote":
        rows["0D"]["observed_epoch"] = NOW - 4
    elif damage == "future":
        rows["0B"]["observed_epoch"] = NOW + 10
    elif damage == "missing":
        rows.pop("0D")
    elif damage == "provider_late":
        rows["0B"].update(
            provider_trade_epoch=NOW - 20, provider_trade_time_precision_ms=1000
        )
    elif damage == "provider_future":
        rows["0B"]["provider_trade_epoch"] = NOW + 20
    result = R.recovery_refresh(stock, ws, now=NOW + 0.2)
    assert not result["allowed"] and result["suppress_normal_refresh"]


@pytest.mark.parametrize(
    "damage",
    [
        "provider",
        "assessed",
        "no_capture",
        "no_policy",
        "no_attempt",
        "missing_provenance",
    ],
)
def test_real_decisions_and_unproven_attempts_keep_normal_cooldown(damage):
    ws, _ = fixture()
    decision = source_failure(ws)
    if damage == "provider":
        decision["provider_called"] = True
    elif damage == "assessed":
        decision["machine_evaluation_status"] = "assessed"
    elif damage == "no_capture":
        decision["machine_observation_sha256"] = ""
    elif damage == "no_policy":
        decision["machine_bundle_sha256"] = ""
    elif damage == "no_attempt":
        decision["evaluation_attempt_id"] = ""
    elif damage == "missing_provenance":
        decision["ai_input_preflight_realtime_type_provenance"] = {}
    assert (
        R.pending_after_failure(dict(code="005930"), decision, now=NOW, cooldown_sec=90)
        is None
    )


def test_retry_budget_and_origin_expiry_do_not_roll_with_each_failure():
    stock, ws = pending()
    origin = stock[R.STATE_KEY]["expires_at"]
    advance(ws)
    stock[R.STATE_KEY] = R.pending_after_failure(
        stock, source_failure(ws), now=NOW + 0.2, cooldown_sec=90
    )
    assert stock[R.STATE_KEY]["expires_at"] == origin
    assert not R.recovery_refresh(stock, ws, now=NOW + 0.3)["allowed"]
    assert R.recovery_refresh(stock, ws, now=origin)["clear"]
    stock["scanner_promotion_id"] = "watch-2"
    assert R.recovery_refresh(stock, ws, now=NOW + 0.3)["clear"]


def test_source_recovery_runs_with_state_change_flag_off_but_keeps_provider_cooldown(
    monkeypatch,
):
    from src.engine import sniper_state_handlers as H

    stock, ws = pending()
    advance(ws)
    monkeypatch.setattr(H, "_rule", lambda *a: False)
    monkeypatch.setattr(H.time, "time", lambda: NOW + 0.2)
    monkeypatch.setattr(H, "WS_MANAGER", None)
    fresh = H._resolve_watching_state_change_refresh(
        stock, ws, now_ts=NOW + 0.2, last_ai_time=0, cooldown_sec=90
    )
    assert fresh["allowed"]
    prior = H._resolve_watching_state_change_refresh(
        stock, ws, now_ts=NOW + 0.2, last_ai_time=NOW - 10, cooldown_sec=90
    )
    assert not prior["allowed"] and prior["suppress_normal_refresh"]
    assert prior["reason"] == "machine_source_wait_completed_decision_cooldown"


def _fixed_watch_recovery(monkeypatch):
    from src.engine import sniper_state_handlers as H
    from src.engine.scalping import main_fixed_watch as fixed
    from src.engine.scalping import reversal_evaluation_context as policy

    stock, ws = pending()
    route = fixed.session_route(NOW, stock["code"])
    stock.update(
        watch_origin="MAIN_FIXED_WATCH",
        status="WATCHING",
        watch_admission_id=fixed.new_admission_id(NOW, route),
        watch_generation_id=fixed.generation_id(NOW, route),
        broker_route="SOR",
        market_session_bucket=route["bucket"],
    )
    stock[R.STATE_KEY] = R.pending_after_failure(
        stock, source_failure(ws), now=NOW, cooldown_sec=90
    )
    advance(ws)
    ws["last_realtime_type_item"] = {"0B": "005930_AL"}
    monkeypatch.setattr(H.time, "time", lambda: NOW + 0.2)
    monkeypatch.setattr(H, "WS_MANAGER", None)
    monkeypatch.setattr(
        policy,
        "prepare",
        lambda **kw: {
            "continuous_reversal": {
                "schema": "continuous_reversal_policy_v6",
                "family_sha256": "f" * 64,
            }
        },
    )
    return H, stock, ws


@pytest.mark.parametrize("signal_ready", [True, False])
def test_fixed_watch_source_recovery_reaches_native_claim_handoff(
    monkeypatch, signal_ready
):
    from src.engine.scalping import reversal_source_diagnostics as native

    H, stock, ws = _fixed_watch_recovery(monkeypatch)
    origin = deepcopy(stock[R.STATE_KEY])
    claim = {
        "token": "fresh-native-claim",
        "snapshot": ({"event_id": "fresh-native-event", "epoch": NOW + 0.1}, {}),
    }
    calls = []

    def claim_current(*args, **kwargs):
        calls.append((args, kwargs))
        return claim if signal_ready else None

    monkeypatch.setattr(native, "claim_snapshot_with_receipt", claim_current)
    result = H._resolve_watching_state_change_refresh(
        stock, ws, now_ts=NOW + 0.2, last_ai_time=0, cooldown_sec=90
    )

    assert len(calls) == 1  # The async fixed-watch consumer requires this claim.
    assert stock[R.STATE_KEY] == origin
    if signal_ready:
        assert result["allowed"] and result["reason"] == "machine_source_fresh_retry"
        assert result["parent_attempt_id"] == origin["parent_attempt_id"]
        assert (
            result["parent_observation_sha256"] == origin["parent_observation_sha256"]
        )
        assert result["source_observed_at"] == NOW + 0.1
        assert stock["_continuous_reversal_pending_claim"] is claim
        assert claim["snapshot"][0]["epoch"] == NOW + 0.1
    else:
        assert not result["allowed"] and result["suppress_normal_refresh"]
        assert result["reason"] == "machine_source_wait_native_signal"
        assert "_continuous_reversal_pending_claim" not in stock


@pytest.mark.parametrize("block", ["completed_decision_cooldown", "stale_quote"])
def test_fixed_watch_recovery_cannot_claim_before_source_and_cooldown_pass(
    monkeypatch, block
):
    from src.engine.scalping import reversal_source_diagnostics as native

    H, stock, ws = _fixed_watch_recovery(monkeypatch)
    last_ai = NOW - 10 if block == "completed_decision_cooldown" else 0
    if block == "stale_quote":
        ws["realtime_type_snapshots_by_route"][KEY]["0D"]["observed_epoch"] = NOW - 4
    monkeypatch.setattr(
        native,
        "claim_snapshot_with_receipt",
        lambda *a, **kw: pytest.fail("blocked recovery must not claim a signal"),
    )

    result = H._resolve_watching_state_change_refresh(
        stock, ws, now_ts=NOW + 0.2, last_ai_time=last_ai, cooldown_sec=90
    )
    assert not result["allowed"] and result["suppress_normal_refresh"]
    assert "_continuous_reversal_pending_claim" not in stock


def test_fixed_watch_recovery_does_not_reuse_requested_signal(monkeypatch):
    from src.engine.scalping import reversal_source_diagnostics as native

    H, stock, ws = _fixed_watch_recovery(monkeypatch)
    stock["_continuous_reversal_last_requested_id"] = "already-requested"
    monkeypatch.setattr(
        native,
        "claim_snapshot_with_receipt",
        lambda *a, **kw: {
            "token": "old-claim",
            "snapshot": ({"event_id": "already-requested"}, {}),
        },
    )
    result = H._resolve_watching_state_change_refresh(
        stock, ws, now_ts=NOW + 0.2, last_ai_time=0, cooldown_sec=90
    )
    assert (
        not result["allowed"]
        and result["reason"] == "machine_source_wait_native_signal"
    )
    assert "_continuous_reversal_pending_claim" not in stock


@pytest.mark.parametrize("aggregate_item", [None, "005930", "005930_NX"])
def test_fixed_watch_recovery_claim_uses_validated_exact_item(
    monkeypatch, aggregate_item
):
    from src.engine.scalping import reversal_source_diagnostics as native

    H, stock, exact = _fixed_watch_recovery(monkeypatch)
    aggregate = deepcopy(exact)
    aggregate["last_realtime_type_item"] = {"0B": aggregate_item}
    # The recovery reader has newer exact data than the caller's aggregate.
    aggregate["realtime_type_snapshots_by_route"][KEY]["0B"]["observed_epoch"] = NOW
    monkeypatch.setattr(
        H,
        "WS_MANAGER",
        SimpleNamespace(get_exact_item_data=lambda code, item: deepcopy(exact)),
    )
    calls = []
    claim = {"token": "exact-native", "snapshot": ({"event_id": "exact-event"}, {})}

    def claim_current(symbol, venue, session, **kwargs):
        calls.append((symbol, venue, session, kwargs["item"]))
        return claim if venue == "SOR" and kwargs["item"] == "005930_AL" else None

    monkeypatch.setattr(native, "claim_snapshot_with_receipt", claim_current)
    result = H._resolve_watching_state_change_refresh(
        stock, aggregate, now_ts=NOW + 0.2, last_ai_time=0, cooldown_sec=90
    )
    assert result["allowed"] and result["reason"] == "machine_source_fresh_retry"
    assert calls == [
        (stock["code"], "SOR", stock["market_session_bucket"], "005930_AL")
    ]
    assert stock["_continuous_reversal_pending_claim"] is claim
    assert aggregate["last_realtime_type_item"]["0B"] == aggregate_item


@pytest.mark.parametrize("damage", ["wrong_item", "stale_quote", "read_error"])
def test_fixed_watch_recovery_rejects_bad_exact_read_without_claim(monkeypatch, damage):
    from src.engine.scalping import reversal_source_diagnostics as native

    H, stock, aggregate = _fixed_watch_recovery(monkeypatch)
    exact = deepcopy(aggregate)
    if damage == "wrong_item":
        exact["realtime_type_snapshots_by_route"][KEY]["0D"]["item"] = "000660_AL"
    elif damage == "stale_quote":
        exact["realtime_type_snapshots_by_route"][KEY]["0D"]["observed_epoch"] = NOW - 4

    def read_exact(*args):
        if damage == "read_error":
            raise OSError("fixture_read_error")
        return exact

    monkeypatch.setattr(
        H, "WS_MANAGER", SimpleNamespace(get_exact_item_data=read_exact)
    )
    monkeypatch.setattr(
        native,
        "claim_snapshot_with_receipt",
        lambda *a, **kw: pytest.fail("invalid exact source must not claim"),
    )
    result = H._resolve_watching_state_change_refresh(
        stock, aggregate, now_ts=NOW + 0.2, last_ai_time=0, cooldown_sec=90
    )
    assert not result["allowed"] and result["suppress_normal_refresh"]
    assert "_continuous_reversal_pending_claim" not in stock


@pytest.mark.parametrize("expired", [False, True])
def test_fixed_watch_recovery_async_admission_preserves_native_deadline(
    monkeypatch, expired
):
    from src.engine.ai.hot_path_ai_dispatcher import HotPathAIDispatcher
    from src.engine.scalping.scanner_async_eval import (
        ScannerAsyncEvalCoordinator,
        FixedWatchGeneration,
    )
    from src.engine.scalping import reversal_source_diagnostics as native

    H, stock, ws = _fixed_watch_recovery(monkeypatch)
    origin = deepcopy(stock[R.STATE_KEY])
    event_epoch = NOW - 5.1 if expired else NOW + 0.1
    claim = {
        "token": "fresh-native-claim",
        "source_registration_receipt": {"sha256": "c" * 64},
        "snapshot": (
            {
                "event_id": "fresh-native-event",
                "epoch": event_epoch,
                "symbol": stock["code"],
                "venue": "SOR",
                "source_item": "005930_AL",
            },
            {},
        ),
    }
    monkeypatch.setattr(native, "claim_snapshot_with_receipt", lambda *a, **kw: claim)
    monkeypatch.setattr(H, "_acknowledge_async_claim", lambda *a, **kw: None)
    monkeypatch.setattr(H, "_log_entry_pipeline", lambda *a, **kw: None)
    refresh = H._resolve_watching_state_change_refresh(
        stock, ws, now_ts=NOW + 0.2, last_ai_time=0, cooldown_sec=90
    )
    assert refresh["allowed"]

    coordinator = ScannerAsyncEvalCoordinator(
        ai_dispatcher=HotPathAIDispatcher(loaded_key_count=1)
    )
    admitted = []

    def capture_request(request):
        # Stop at admission: no worker, provider, account or order I/O.
        admitted.append(request)
        return SimpleNamespace(accepted=True, reason="fixture_admitted")

    monkeypatch.setattr(coordinator, "submit", capture_request)
    try:
        result = H._resolve_scanner_async_entry_ai(
            stock,
            stock["code"],
            ws,
            None,
            {"scanner_async_eval_coordinator": coordinator},
            trigger_reason=refresh["reason"],
            last_ai_time=0,
            current_ai_score=0,
        )
    finally:
        coordinator.shutdown()

    assert stock[R.STATE_KEY] == origin
    if expired:
        assert result == {
            "status": "commit_rejected",
            "reason": "fixed_watch_native_identity_missing_or_expired",
        }
        assert not admitted
        assert "_fixed_watch_async_claim" not in stock
    else:
        assert result["status"] == "dispatched" and len(admitted) == 1
        context = admitted[0].context
        assert isinstance(context.generation, FixedWatchGeneration)
        assert context.deadline_epoch == event_epoch + 5  # Not dispatch time + 5.
        assert (
            context.stock_snapshot[R.STATE_KEY]["parent_observation_sha256"]
            == origin["parent_observation_sha256"]
        )
        assert stock["_fixed_watch_async_claim"]["token"] == claim["token"]


def test_route_price_is_available_even_when_aggregate_curr_is_missing(monkeypatch):
    from src.engine import sniper_state_handlers as H

    ws, context = fixture()
    context["request_code"] = "005930_AL"
    aggregate = dict(
        curr=0, last_ws_update_ts=NOW - 0.01, market_data_transport_epoch=1
    )
    ws["curr"] = 0
    monkeypatch.setattr(H.time, "time", lambda: NOW)
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_PRE_SUBMIT_QUOTE_REFRESH_ENABLED", "true")
    calls = []
    monkeypatch.setattr(
        H,
        "WS_MANAGER",
        SimpleNamespace(
            get_latest_data=lambda _: deepcopy(aggregate),
            get_exact_item_data=lambda code, item: calls.append((code, item))
            or deepcopy(ws),
        ),
    )
    monkeypatch.setattr(
        H, "revalidate_entry_candle_snapshot", lambda c, w, now_ts: deepcopy(c)
    )
    selected, ticks, _, fields = H._refresh_prepared_entry_inputs(
        "005930", ws, [], context
    )
    assert fields["entry_ai_final_ws_snapshot_refresh_applied"]
    assert (
        fields["entry_ai_final_ws_snapshot_refresh_reason"]
        == "latest_locked_observation_only"
    )
    assert (
        selected["curr"] == 275500 and ticks == ws["recent_trade_ticks_by_route"][KEY]
    )
    assert calls and all(item == "005930_AL" for _, item in calls)
    # Final submit has no observation exception and still rejects this input.
    _, submit_fields = H._pre_submit_refresh_real_ws_snapshot(
        "005930", ws, "SCALPING", refresh_even_if_input_fresh=True
    )
    assert submit_fields["pre_submit_ws_snapshot_refresh_applied"] is False


def test_source_retry_cache_key_changes_parent_but_pins_inflight_generation():
    from src.engine import sniper_state_handlers as H

    stock, _ = pending()
    generation = SimpleNamespace(generation_id="g-1")
    key1 = H._scanner_async_entry_cache_key(
        stock,
        generation=generation,
        trigger_reason="machine_source_fresh_retry",
        last_ai_time=0,
    )
    stock[R.STATE_KEY]["parent_observation_sha256"] = "c" * 64
    key2 = H._scanner_async_entry_cache_key(
        stock,
        generation=generation,
        trigger_reason="machine_source_fresh_retry",
        last_ai_time=0,
    )
    assert key1 != key2
    stock.update(_scanner_async_generation_id="g-1", _scanner_async_cache_key=key1)
    assert (
        H._scanner_async_entry_cache_key(
            stock,
            generation=generation,
            trigger_reason="machine_source_fresh_retry",
            last_ai_time=0,
        )
        == key1
    )


def test_failed_input_clock_is_separate_and_valid_recheck_or_provider_result_closes_lease(
    monkeypatch,
):
    from src.engine import sniper_state_handlers as H

    stock, ws = pending()
    clocks = {"005930": NOW - 10}
    monkeypatch.setattr(H, "LAST_AI_CALL_TIMES", clocks)
    source = source_failure(ws)
    stock.pop(R.STATE_KEY)
    H._commit_watching_entry_evaluation(
        stock, "005930", source, completed_at=NOW, cooldown_sec=90, strategy="SCALPING"
    )
    assert R.STATE_KEY in stock and clocks["005930"] == NOW - 10
    # A real machine RECHECK is a completed evaluation, even with no AI call.
    assessed = {
        **source,
        "machine_evaluation_status": "assessed",
        "entry_mechanistic_action": "RECHECK",
    }
    H._commit_watching_entry_evaluation(
        stock,
        "005930",
        assessed,
        completed_at=NOW + 1,
        cooldown_sec=90,
        strategy="SCALPING",
    )
    assert R.STATE_KEY not in stock and clocks["005930"] == NOW + 1
    provider = {**source, "provider_called": True, "entry_ai_advisory_verdict": "VETO"}
    H._commit_watching_entry_evaluation(
        stock,
        "005930",
        provider,
        completed_at=NOW + 2,
        cooldown_sec=90,
        strategy="SCALPING",
    )
    assert R.STATE_KEY not in stock and clocks["005930"] == NOW + 2


def test_expired_lease_cannot_stick_on_manager_error(monkeypatch):
    from src.engine import sniper_state_handlers as H

    stock, ws = pending()
    monkeypatch.setattr(H.time, "time", lambda: NOW + 90)
    monkeypatch.setattr(H, "_rule", lambda *a: False)
    monkeypatch.setattr(
        H,
        "WS_MANAGER",
        SimpleNamespace(
            get_exact_item_data=lambda *a: pytest.fail("expired lease must not read")
        ),
    )
    result = H._resolve_watching_state_change_refresh(
        stock, ws, now_ts=NOW, last_ai_time=0, cooldown_sec=90
    )
    assert R.STATE_KEY not in stock and not result["allowed"]


@pytest.mark.parametrize("damage", ["key", "parent", "scope", "timing"])
def test_corrupt_pending_receipt_cannot_create_retry_or_crash(damage):
    stock, ws = pending()
    advance(ws)
    if damage == "key":
        stock[R.STATE_KEY].pop("selected_key")
    elif damage == "parent":
        stock[R.STATE_KEY]["parent_observation_sha256"] = "bad"
    elif damage == "scope":
        stock[R.STATE_KEY]["scope"] = None
    elif damage == "timing":
        stock[R.STATE_KEY]["source_timing"] = "bad"
    assert not R.recovery_refresh(stock, ws, now=NOW + 0.2)["allowed"]


def quote_pending(monkeypatch, *, missing_quote=False):
    monkeypatch.setattr(R.time, "time", lambda: NOW)
    stock, ws = pending()
    stock.update(status="WATCHING", buy_qty=0)
    rows = ws["realtime_type_snapshots_by_route"][KEY]
    rows["0B"].update(route_sequence=30)
    rows["0D"].update(route_sequence=40, observed_epoch=NOW - 4)
    ws["source_recovery_lease"] = dict(
        schema="entry_source_lease_v1",
        item="005930_AL",
        transport_epoch=1,
        registration_epoch=1,
        registration_sent_at_epoch=NOW - 10,
        realtime_types=["0B", "0D"],
        physical_probe_lease_id=None,
        physical_probe_lease_epoch=None,
        physical_probe_lease_removing=False,
        physical_probe_lease_adopted=False,
        interval_started_epoch=None,
    )
    claim = dict(
        token="original-native-token",
        generation="f" * 64,
        snapshot=[
            dict(
                symbol="005930",
                venue="SOR",
                source_item="005930_AL",
                native_epoch=1,
                native_sequence=30,
                signal_id="root-signal",
                event_id="root-event",
                epoch=NOW - 0.5,
                entry_ask=275500,
                market="AFTER",
            ),
            {},
        ],
    )
    if missing_quote:
        rows.pop("0D")
    decision = source_failure(ws) if not missing_quote else source_failure(fixture()[0])
    preflight = dict(
        blockers=["bbo_missing" if missing_quote else "bbo_stale"], feature_blockers=[]
    )
    decision.update(
        R.capture_quote_failure(
            preflight, ws, claim, deadline_perf=R.time.perf_counter() + 4.5
        )
    )
    stock.pop(R.STATE_KEY)
    stock[R.STATE_KEY] = R.pending_after_failure(
        stock, decision, now=NOW, cooldown_sec=90
    )
    return stock, ws, claim


def receive_quote(ws):
    rows = ws["realtime_type_snapshots_by_route"][KEY]
    quote = deepcopy(
        rows.get("0D") or fixture()[0]["realtime_type_snapshots_by_route"][KEY]["0D"]
    )
    quote.update(route_sequence=41, observed_epoch=NOW + 0.1)
    quote["orderbook"]["asks"][0]["price"] = 275600
    quote["market_source_latency"] = dict(
        schema="market_source_latency_v1",
        item="005930_AL",
        transport_epoch=1,
        route_sequence=41,
        packet_received_epoch=NOW + 0.09,
    )
    rows["0D"] = quote


@pytest.mark.parametrize("missing_quote", [False, True])
def test_exact_quote_only_recovery_preserves_original_signal_and_deadline(
    monkeypatch, missing_quote
):
    stock, ws, claim = quote_pending(monkeypatch, missing_quote=missing_quote)
    pending = deepcopy(stock[R.STATE_KEY])
    assert pending["schema"] == R.QUOTE_SCHEMA
    assert pending["expires_at"] == claim["snapshot"][0]["epoch"] + 5
    receive_quote(ws)
    original_tape = deepcopy(ws["realtime_type_snapshots_by_route"][KEY]["0B"])
    refresh = R.recovery_refresh(stock, ws, now=NOW + 0.2)
    assert refresh["allowed"] and refresh["quote_only"]
    assert refresh["reason"] == "machine_source_quote_fresh_retry"
    assert ws["realtime_type_snapshots_by_route"][KEY]["0B"] == original_tape
    receipt = R.evaluation_quote_receipt(
        dict(claim, entry_quote_recovery_parent=pending),
        ws,
        now=NOW + 0.2,
        evaluation_attempt_id="new-evaluation",
    )
    raw = dict(
        evaluation_attempt_id="new-evaluation",
        entry_source_quote_recovery=receipt,
        quote=dict(
            best_bid=receipt["calculation_best_bid"],
            best_ask=receipt["calculation_best_ask"],
        ),
    )
    R.validate_evaluation_quote_receipt(receipt, claim["snapshot"][0], raw)
    assert receipt["native_entry_ask"] == 275500
    assert receipt["calculation_best_ask"] == 275600
    assert claim["snapshot"][0]["entry_ask"] == 275500
    assert stock[R.STATE_KEY] == pending


@pytest.mark.parametrize(
    "damage",
    [
        "old_packet",
        "no_packet",
        "wrong_packet_sequence",
        "wrong_packet_item",
        "wrong_packet_epoch",
        "future_packet",
        "same_sequence",
        "lease",
        "epoch",
        "stale_tape",
        "changed_tape",
        "expired",
        "provider_late",
        "crossed",
        "zero_quantity",
    ],
)
def test_quote_only_recovery_requires_actual_post_failure_packet_and_unchanged_sources(
    monkeypatch, damage
):
    stock, ws, _ = quote_pending(monkeypatch)
    receive_quote(ws)
    rows = ws["realtime_type_snapshots_by_route"][KEY]
    quote, tape = rows["0D"], rows["0B"]
    now = NOW + 0.2
    if damage == "old_packet":
        quote["market_source_latency"]["packet_received_epoch"] = NOW - 0.1
    elif damage == "no_packet":
        quote["market_source_latency"].pop("packet_received_epoch")
    elif damage == "wrong_packet_sequence":
        quote["market_source_latency"]["route_sequence"] = 40
    elif damage == "wrong_packet_item":
        quote["market_source_latency"]["item"] = "000660_AL"
    elif damage == "wrong_packet_epoch":
        quote["market_source_latency"]["transport_epoch"] = 2
    elif damage == "future_packet":
        quote["market_source_latency"]["packet_received_epoch"] = NOW + 1
    elif damage == "same_sequence":
        quote["route_sequence"] = 40
    elif damage == "lease":
        ws["source_recovery_lease"]["registration_sent_at_epoch"] = NOW + 0.05
    elif damage == "epoch":
        ws["market_data_transport_epoch"] = 2
    elif damage == "stale_tape":
        tape["observed_epoch"] = NOW - 4
    elif damage == "changed_tape":
        tape["current_price"] = 275400
    elif damage == "expired":
        now = NOW + 4.5
    elif damage == "provider_late":
        tape["provider_trade_epoch"] = NOW - 20
    elif damage == "crossed":
        quote["orderbook"]["asks"][0]["price"] = 275400
    elif damage == "zero_quantity":
        quote["orderbook"]["asks"][0]["volume"] = 0
    assert not R.recovery_refresh(stock, ws, now=now)["allowed"]


def test_quote_retry_main_handoff_consumes_once_without_new_native_claim(monkeypatch):
    from src.engine import sniper_state_handlers as H
    from src.engine.scalping import reversal_source_diagnostics as native
    from src.engine.scalping import reversal_current_backend as backend

    stock, ws, original = quote_pending(monkeypatch)
    receive_quote(ws)
    monkeypatch.setattr(H.time, "time", lambda: NOW + 0.2)
    monkeypatch.setattr(H, "WS_MANAGER", None)
    monkeypatch.setattr(
        native,
        "claim_snapshot_with_receipt",
        lambda *a, **kw: pytest.fail("must reuse root"),
    )
    monkeypatch.setattr(
        native, "validate_claim_with_receipt", lambda claim, *a, **kw: claim["snapshot"]
    )
    monkeypatch.setattr(
        backend, "backend", lambda *a: SimpleNamespace(_GENERATION="f" * 64)
    )
    ready = H._resolve_watching_state_change_refresh(
        stock, ws, now_ts=NOW + 0.2, last_ai_time=0, cooldown_sec=90
    )
    assert ready["allowed"] and ready["quote_only"]
    admitted = stock["_continuous_reversal_pending_claim"]
    assert (
        admitted["snapshot"] == original["snapshot"]
        and admitted["token"] == original["token"]
    )
    assert stock[R.STATE_KEY]["retry_count"] == 1
    assert not R.recovery_refresh(stock, ws, now=NOW + 0.3)["allowed"]


def test_pending_quote_wake_is_coalesced_and_does_not_increment_native_counts(
    monkeypatch,
):
    import threading
    from src.engine.monitoring import runtime_performance as metrics

    stock, ws, _ = quote_pending(monkeypatch)
    receive_quote(ws)
    event = threading.Event()
    metrics.set_native_ready_event(event)
    counts = deepcopy(metrics._COVERAGE)
    R.register_pending_target(stock, stock[R.STATE_KEY])
    try:
        assert not R.notify_pending_quote("005930", "005930_NX", ws, now=NOW + 0.2)
        assert not event.is_set()
        assert R.notify_pending_quote("005930", "005930_AL", ws, now=NOW + 0.2)
        event.clear()
        assert not R.notify_pending_quote("005930", "005930_AL", ws, now=NOW + 0.2)
        assert not event.is_set() and metrics._COVERAGE == counts
    finally:
        metrics.set_native_ready_event(None)
        R.register_pending_target(stock, None)


@pytest.mark.parametrize(
    "blocker",
    [
        "tape_stale",
        "current_price_missing",
        "source_time_skew",
        "candle_missing",
        "required_feature_tape_stale",
        "realtime_type_route_conflict",
    ],
)
def test_quote_retry_does_not_generalize_other_source_or_feature_failures(
    monkeypatch, blocker
):
    _stock, ws, claim = quote_pending(monkeypatch)
    assert (
        R.capture_quote_failure(dict(blockers=["bbo_stale", blocker]), ws, claim) == {}
    )


@pytest.mark.parametrize("locked", [False, True])
def test_new_union_calculation_uses_actual_ask_spread_and_geometry_without_rewriting_proof(
    locked,
):
    from src.tests.test_reversal_extended_policy import FIXTURES
    from src.engine.scalping import reversal_extended_union as union

    fixture = deepcopy(next(iter(FIXTURES.values())))
    event, source = fixture["event"], fixture["source"]
    original = deepcopy((event, source))
    arm = union.V1.ARMS[-1]
    root_input, prompt, schema = union.production_request(source, arm, event=event)
    root_result = (
        dict(event=event, signal_set_hash=R._digest(root_input["signals"])),
        root_input,
        prompt,
        schema,
    )
    ask = event["entry_ask"] * 1.002
    bid = ask if locked else event["entry_ask"]
    receipt = dict(
        schema=R.QUOTE_SCHEMA,
        native_entry_ask=event["entry_ask"],
        native_root_event=deepcopy(event),
        calculation_best_ask=ask,
        calculation_best_bid=bid,
        quote_observed_epoch=event["epoch"] + 0.2,
        original_deadline_epoch=event["epoch"] + 5,
        sha256="d" * 64,
    )
    result = R.apply_quote_calculation(root_result, receipt)
    assessment, inp, actual_prompt, actual_schema = result
    assessment["entry_source_quote_recovery"] = receipt
    assert (event, source) == original
    assert inp["common_context"]["entry_ask"] == ask
    assert inp["entry_setup_evidence_v1"]["facts"]["entry_ask"] == ask
    assert inp["common_context"]["entry_geometry"]["target_price"] == pytest.approx(
        ask * 1.004 / 0.9977
    )
    assert (
        inp["signals"][0]["observed_signal"]
        == root_input["signals"][0]["observed_signal"]
    )
    assert [s["ref"] for s in inp["signals"]] == [
        s["ref"] for s in root_input["signals"]
    ]
    assert actual_prompt == prompt
    assert inp["entry_source_quote_recovery"]["native_entry_ask"] == event["entry_ask"]
    assert (
        "ENTRY_SPREAD_CONCERN" in inp["entry_setup_evidence_v1"]["risk_fact_bindings"]
    ) is not locked
    request = dict(input=inp, prompt=actual_prompt, response_schema=actual_schema)
    a, native_request = R.audit_quote_calculation(assessment, request)
    assert native_request == dict(
        input=root_input, prompt=prompt, response_schema=schema
    )
    assert a["signal_set_hash"] == root_result[0]["signal_set_hash"]
    response = dict(
        schema=union.VERSION,
        decision_scope="COMMON_OPPORTUNITY",
        assessed_signal_refs=[s["ref"] for s in inp["signals"]],
        risk_verdict="PASS",
        risk_codes=["NO_BLOCKING_RISK"],
        supporting_fact_ids=["observed_machine_signal"],
        contradicting_fact_ids=[],
        confidence=50,
    )
    assert union.validate_response(response, inp, arm=arm) == []
    wrong = deepcopy(request)
    wrong["input"]["entry_setup_evidence_v1"]["facts"]["entry_ask"] += 1
    with pytest.raises(ValueError, match="calculation_request_invalid"):
        R.audit_quote_calculation(assessment, wrong)


def test_packet_between_failure_and_pending_registration_is_rechecked(monkeypatch):
    from src.engine import sniper_state_handlers as H
    from src.engine.monitoring import runtime_performance as metrics
    import threading

    stock, ws, claim = quote_pending(monkeypatch)
    decision = source_failure(ws)
    decision.update(
        R.capture_quote_failure(
            dict(blockers=["bbo_stale"]),
            ws,
            claim,
            deadline_perf=R.time.perf_counter() + 4.5,
        )
    )
    receive_quote(ws)
    stock.pop(R.STATE_KEY)
    monkeypatch.setattr(H.time, "time", lambda: NOW + 0.2)
    monkeypatch.setattr(
        H, "WS_MANAGER", SimpleNamespace(get_exact_item_data=lambda *a: deepcopy(ws))
    )
    event = threading.Event()
    metrics.set_native_ready_event(event)
    try:
        result = H._commit_watching_entry_evaluation(
            stock,
            "005930",
            decision,
            completed_at=NOW + 0.2,
            cooldown_sec=90,
            strategy="SCALPING",
        )
        assert result["schema"] == R.QUOTE_SCHEMA and result["failed_at"] == NOW
        assert event.is_set()
    finally:
        metrics.set_native_ready_event(None)
        R.register_pending_target(stock, None)


@pytest.mark.parametrize("spread", [0.05, 0.15, 0.4])
def test_current_spread_filters_existing_branches_without_synthesizing_a_signal(
    monkeypatch, spread
):
    from src.engine.scalping import reversal_extended_catalog as catalog

    monkeypatch.setattr(
        catalog,
        "definition",
        lambda bid: dict(filters={"spread_max": {"narrow": 0.1, "wide": 0.3}[bid]}),
    )
    event = dict(
        confirmation_price=100,
        entry_ask=100.05,
        branch_signals={
            bid: dict(
                signal_id=bid,
                entry_ask=100.05,
                confirmation_price=100,
                decision_phase="MOMENTUM_CROSS",
            )
            for bid in ("narrow", "wide")
        },
    )
    snapshot = (event, dict(branch_inputs={"narrow": {}, "wide": {}}))
    original = deepcopy(snapshot)
    receipt = dict(
        native_root_event=deepcopy(event),
        calculation_best_bid=100,
        calculation_best_ask=100 + spread,
    )
    if spread > 0.3:
        with pytest.raises(
            ValueError, match="current_quote_invalidates_native_branches"
        ):
            R.calculation_snapshot(snapshot, receipt)
    else:
        calculation = R.calculation_snapshot(snapshot, receipt)
        expected = ["narrow", "wide"] if spread < 0.1 else ["wide"]
        assert sorted(calculation[0]["branch_signals"]) == expected
        assert receipt["calculation_branch_ids"] == expected
        assert "unconfirmed-third-branch" not in calculation[0]["branch_signals"]
    assert snapshot == original


@pytest.mark.parametrize("version,overlay", [(5, False), (6, False), (6, True)])
def test_actual_native_observation_audits_accept_bound_current_quote_calculation(
    monkeypatch, tmp_path, version, overlay
):
    from datetime import datetime
    from src.engine.scalping import continuous_reversal_policy_v5 as v5
    from src.engine.scalping import continuous_reversal_policy_v6 as v6
    from src.engine.scalping import ai_decision_trace as trace
    from src.engine.scalping import reversal_auxiliary_intraday as overlays
    from src.engine.scalping import reversal_auxiliary_registry as registry
    from src.engine.scalping import continuous_reversal_postclose as common

    if version == 5:
        from src.tests.test_reversal_path_policy import state, feed, row

        bid, detector = state("SA", monkeypatch)
        for i in range(62):
            feed(detector, row(i))
        snapshot = detector.snapshot(feed(detector, row(62, 100.2))[0])
        policy = v5
    else:
        from src.tests.test_reversal_extended_policy import FIXTURES

        fixture = deepcopy(next(iter(FIXTURES.values())))
        snapshot = (fixture["event"], fixture["source"])
        policy = v6
    event, _ = snapshot
    catalog, union = policy.C, policy.A
    key = catalog.cell_key(
        event["symbol"], event["market"], event["confirmation_price"]
    )
    route, arm = event["venue"], union.V1.ARMS[-1]
    day = datetime.fromtimestamp(event["epoch"], policy.K.KST).date().isoformat()
    family = dict(
        schema=policy.SCHEMA,
        family_sha256="f" * 64,
        source_date=day,
        publication_date=day,
        effective_date=day,
        execution_manifest_hash="e" * 64,
        machine_cells={
            key: dict(
                routes={
                    route: dict(
                        backend=f"union_v{version}",
                        payload=dict(
                            branches=[
                                catalog.branch(bid) for bid in event["branch_signals"]
                            ]
                        ),
                        scope_execution_hash="c" * 64,
                    )
                }
            )
        },
        auxiliary_cells={
            key: dict(
                routes={route: dict(payload=dict(arm=arm, binding=union.binding(arm)))}
            )
        },
    )
    monkeypatch.setattr(policy, "validate_family", lambda *a, **kw: None)
    root_result = policy.assess(
        family, snapshot, symbol=event["symbol"], session=event["market"]
    )
    bundle = dict(bundle_sha256="b" * 64, continuous_reversal=family)
    if overlay:
        value = registry.definition(
            arm,
            prompt=union.PROMPT + union.ARM_SUFFIXES[arm] + "Use supplied facts.\n",
            input_version=union.VERSION,
        )
        registry.register(tmp_path, value)
        value = registry.compact_definition(
            value, research_wire_contract={"schema": "fixture_wire_contract"}
        )
        registry.register(tmp_path, value)
        monkeypatch.setattr(
            overlays, "selected_definition", lambda *a, **kw: (value, None)
        )
        monkeypatch.setattr(
            overlays,
            "inherited",
            lambda *a, **kw: {v5.scope_id(key, route): value["registry_sha256"]},
        )
        from src.utils import constants

        monkeypatch.setattr(constants, "DATA_DIR", tmp_path)
        root_result = overlays.apply_request(tmp_path, bundle, snapshot, root_result)
    ask = event["entry_ask"] * 1.00001
    receipt = dict(
        schema=R.QUOTE_SCHEMA,
        parent_attempt_id="source-failure",
        parent_observation_sha256="a" * 64,
        evaluation_attempt_id="quote-calculation",
        native_snapshot_sha256=R._digest(snapshot),
        native_root_event=deepcopy(event),
        native_signal_id=event["signal_id"],
        native_event_id=event["event_id"],
        native_epoch=event["epoch"],
        native_entry_ask=event["entry_ask"],
        original_deadline_epoch=event["epoch"] + 5,
        failed_at=event["epoch"] + 0.05,
        source_item=event["source_item"],
        transport_epoch=event["native_epoch"],
        original_quote_sequence=4,
        quote_sequence=5,
        quote_packet_received_epoch=event["epoch"] + 0.1,
        quote_observed_epoch=event["epoch"] + 0.2,
        evaluated_at=event["epoch"] + 0.3,
        calculation_best_bid=event["entry_ask"],
        calculation_best_ask=ask,
        native_snapshot_rewritten=False,
        provider_called_before_recovery=False,
    )
    receipt["sha256"] = R._digest(receipt)
    assessment, inp, prompt, schema = R.apply_quote_calculation(
        root_result, receipt, data_root=tmp_path
    )
    assessment["entry_source_quote_recovery"] = receipt
    records = []
    monkeypatch.setattr(trace, "trace_enabled", lambda: True)
    monkeypatch.setattr(
        trace,
        "_now",
        lambda: datetime.fromtimestamp(event["epoch"] + 0.4, policy.K.KST),
    )
    monkeypatch.setattr(
        trace, "_append_jsonl", lambda path, record: records.append(record)
    )
    raw = dict(
        stock_code=event["symbol"],
        session_bucket=event["market"],
        evaluation_attempt_id="quote-calculation",
        entry_machine_input_as_of=event["epoch"] + 0.2,
        entry_source_quote_recovery=receipt,
        quote=dict(best_bid=event["entry_ask"], best_ask=ask),
    )
    context = dict(
        family_sha256=family["family_sha256"],
        source_date=day,
        publication_date=day,
        effective_date=day,
        machine_component_sha256=common.digest(family["machine_cells"]),
        auxiliary_component_sha256=common.digest(family["auxiliary_cells"]),
        snapshot_read_at=event["epoch"] + 0.3,
        input_sha256=common.digest(inp),
        prompt_sha256=common.digest(prompt),
        response_schema_sha256=common.digest(schema),
        arm=arm,
    )
    trace.capture_machine_observation(
        exact_payload=raw,
        setup_evidence=inp["entry_setup_evidence_v1"],
        assessment=assessment,
        bundle_sha256=bundle["bundle_sha256"],
        reversal_context=context,
        reversal_request=dict(input=inp, prompt=prompt, response_schema=schema),
    )
    auditor = overlays.audit_observation if overlay else policy.audit_observation
    payload, verified = auditor(bundle, records[0])
    assert payload["branches"] and verified["new_scope_consumption"]
    assert (
        records[0]["source"]["assessment"]["event"]["entry_ask"] == event["entry_ask"]
    )
    assert (
        records[0]["source"]["auxiliary_request"]["input"]["entry_setup_evidence_v1"][
            "facts"
        ]["entry_ask"]
        == ask
    )
    assert records[0]["label_context"]["reference_price"] == ask
    assert (
        records[0]["label_context"]["entry_source_quote_label"]["decision_epoch"]
        == receipt["evaluated_at"]
    )
    import hashlib

    for damage in (
        "facts_ask",
        "common_ask",
        "signal_spread",
        "geometry",
        "spread_unit",
        "spread_duplicate",
    ):
        forged = deepcopy(records[0])
        calculation = forged["source"]["assessment"]["entry_source_quote_calculation"]
        root_input = calculation["root_request"]["input"]
        if damage == "facts_ask":
            root_input["entry_setup_evidence_v1"]["facts"]["entry_ask"] *= 1.1
        elif damage == "common_ask":
            root_input["common_context"]["entry_ask"] *= 1.1
        elif damage == "signal_spread":
            root_input["signals"][0]["facts"]["spread_pct"] = 1234
        elif damage == "geometry":
            root_input["common_context"]["entry_geometry"]["target_price"] *= 1.1
        else:
            spread_fact = next(
                (
                    fact
                    for fact in root_input["entry_setup_evidence_v1"][
                        "contradicting_facts"
                    ]
                    if fact["id"].endswith("/observed_spread")
                ),
                None,
            )
            if spread_fact is None:
                continue
            if damage == "spread_unit":
                spread_fact["unit"] = "basis_points"
            else:
                root_input["entry_setup_evidence_v1"]["contradicting_facts"].append(
                    deepcopy(spread_fact)
                )
        calculation["root_request_sha256"] = R._digest(calculation["root_request"])
        forged["runtime_consumption"]["continuous_reversal"]["assessment_sha256"] = (
            hashlib.sha256(
                trace._json_bytes(forged["source"]["assessment"])
            ).hexdigest()
        )
        with pytest.raises(ValueError):
            auditor(bundle, forged)


@pytest.mark.parametrize("receipt,proof", [(None, {}), ({}, None), (None, None)])
def test_malformed_or_dropped_quote_proof_is_a_bounded_value_error(receipt, proof):
    assessment = dict(
        entry_source_quote_recovery=receipt, entry_source_quote_calculation=proof
    )
    if receipt is not None or proof is not None:
        with pytest.raises(ValueError):
            R.audit_quote_calculation(assessment, {})
    with pytest.raises(ValueError, match="receipt_missing"):
        R.validate_evaluation_quote_receipt(
            None, {}, dict(entry_source_quote_recovery={"schema": R.QUOTE_SCHEMA})
        )


@pytest.mark.parametrize(
    "changed", ["event_id", "entry_ask", "branch_signals", "absent"]
)
def test_observer_root_rejection_retains_both_roots_without_admitting_or_retrying(
    monkeypatch, changed
):
    from src.engine.scalping import reversal_source_diagnostics as diagnostics

    root = dict(
        symbol="005930",
        venue="KRX",
        market="krx_regular",
        event_id="event",
        signal_id="signal",
        epoch=NOW,
        native_epoch=7,
        native_sequence=42,
        source_item="005930",
        entry_ask=100,
        registry_generation="c" * 64,
        confirmation_price=100,
        branch_signals={"G1": {"signal_id": "original"}},
    )
    observation = dict(
        schema="entry_source_quote_observer_v1",
        snapshot=[root, {}],
        family_sha256="a" * 64,
        observer_pid=123,
        observer_start_ticks="456",
        deadline_epoch=NOW + 5,
    )
    current = deepcopy(root)
    if changed == "event_id":
        current["event_id"] = "next"
    elif changed == "entry_ask":
        current["entry_ask"] = 101
    elif changed == "branch_signals":
        current["branch_signals"]["G1"]["signal_id"] = "new"
    selection = dict(
        schema="native_observation_selection_v1",
        observed_epoch=NOW + 0.2,
        reason="native_path_changed" if changed == "absent" else "ready",
    )
    monkeypatch.setattr(diagnostics, "observation_binding_valid", lambda *a, **kw: True)
    monkeypatch.setattr(
        diagnostics,
        "observe_snapshot",
        lambda *a, **kw: (None if changed == "absent" else (current, {}), selection),
    )
    before = deepcopy(observation)
    with pytest.raises(
        ValueError, match="machine_source_quote_observer_native_root_changed"
    ) as caught:
        R.validated_observer_snapshot(observation, now=NOW + 0.2)
    receipt = caught.value.reversal_source_receipt
    assert receipt["original_root"] == root
    assert receipt["current_root"] == (None if changed == "absent" else current)
    assert receipt["native_selection"] == selection
    assert receipt["sha256"] == R._digest(
        {k: v for k, v in receipt.items() if k != "sha256"}
    )
    assert (
        receipt["runtime_effect"]
        is receipt["allowed_runtime_apply"]
        is receipt["actual_order_submitted"]
        is False
    )
    assert receipt["broker_order_forbidden"] is True
    assert observation == before
    from src.engine.scalping.ai_decision_trace import sanitize_ai_trace_value

    safe, redacted = sanitize_ai_trace_value(
        {"continuous_reversal_rejected_claim_receipt": receipt}
    )
    assert (
        safe["continuous_reversal_rejected_claim_receipt"] == receipt and not redacted
    )
