"""Fresh-source repair scheduling and guards, without broker/provider I/O."""

from copy import deepcopy
from types import SimpleNamespace

import pytest

from src.engine.scalping import entry_machine_source_recovery as R
from src.tests.test_entry_machine_observation import fixture, NOW, KEY


def source_failure(ws):
    rows = ws["realtime_type_snapshots_by_route"][KEY]
    return dict(
        provider_called=False, machine_evaluation_expected=True,
        machine_evaluation_status="source_quality_blocked_before_assessment",
        machine_source_invalid_receipt=True, machine_observation_sha256="a" * 64,
        machine_capture_status="captured",
        machine_bundle_sha256="b" * 64, evaluation_attempt_id="aims-source-failed",
        ai_input_preflight_realtime_type_provenance=deepcopy(rows),
        ai_input_preflight_source_timing={name: dict(freshness_limit_ms=3000)
                                        for name in ("current_price", "bbo", "tape")},
    )


def pending():
    ws, _ = fixture()
    stock = dict(code="005930", id=101, scanner_promotion_id="watch-1",
                 scanner_generation_id="generation-1", effective_venue="KRX")
    stock[R.STATE_KEY] = R.pending_after_failure(stock, source_failure(ws), now=NOW, cooldown_sec=90)
    return stock, ws


def advance(ws):
    for kind in ("0B", "0D"):
        ws["realtime_type_snapshots_by_route"][KEY][kind]["observed_epoch"] = NOW + .1


def test_only_new_exact_tape_schedules_fresh_calculation():
    stock, ws = pending()
    assert not R.recovery_refresh(stock, ws, now=NOW)["allowed"]
    ws["realtime_type_snapshots_by_route"][KEY]["0D"]["observed_epoch"] = NOW + .1
    assert not R.recovery_refresh(stock, ws, now=NOW + .2)["allowed"]
    advance(ws)
    before = deepcopy((stock, ws))
    ready = R.recovery_refresh(stock, ws, now=NOW + .2)
    assert ready["allowed"] and ready["reason"] == "machine_source_fresh_retry"
    assert ready["actual_order_submitted"] is False
    assert ready["broker_order_forbidden"] is True
    assert (stock, ws) == before


@pytest.mark.parametrize("damage", ["symbol", "route", "epoch", "bool_epoch", "stale_quote", "future",
                                    "missing", "provider_late", "provider_future"])
def test_new_receive_clock_cannot_recover_bad_source(damage):
    stock, ws = pending()
    advance(ws)
    rows = ws["realtime_type_snapshots_by_route"][KEY]
    if damage == "symbol": rows["0B"]["item"] = "000660_AL"
    elif damage == "route": rows["0D"]["market_route"] = "nxt_only"
    elif damage == "epoch": rows["0D"]["transport_epoch"] = 2
    elif damage == "bool_epoch": ws["market_data_transport_epoch"] = True
    elif damage == "stale_quote": rows["0D"]["observed_epoch"] = NOW - 4
    elif damage == "future": rows["0B"]["observed_epoch"] = NOW + 10
    elif damage == "missing": rows.pop("0D")
    elif damage == "provider_late": rows["0B"].update(provider_trade_epoch=NOW - 20, provider_trade_time_precision_ms=1000)
    elif damage == "provider_future": rows["0B"]["provider_trade_epoch"] = NOW + 20
    result = R.recovery_refresh(stock, ws, now=NOW + .2)
    assert not result["allowed"] and result["suppress_normal_refresh"]


@pytest.mark.parametrize("damage", ["provider", "assessed", "no_capture", "no_policy", "no_attempt", "missing_provenance"])
def test_real_decisions_and_unproven_attempts_keep_normal_cooldown(damage):
    ws, _ = fixture()
    decision = source_failure(ws)
    if damage == "provider": decision["provider_called"] = True
    elif damage == "assessed": decision["machine_evaluation_status"] = "assessed"
    elif damage == "no_capture": decision["machine_observation_sha256"] = ""
    elif damage == "no_policy": decision["machine_bundle_sha256"] = ""
    elif damage == "no_attempt": decision["evaluation_attempt_id"] = ""
    elif damage == "missing_provenance": decision["ai_input_preflight_realtime_type_provenance"] = {}
    assert R.pending_after_failure(dict(code="005930"), decision, now=NOW, cooldown_sec=90) is None


def test_retry_budget_and_origin_expiry_do_not_roll_with_each_failure():
    stock, ws = pending()
    origin = stock[R.STATE_KEY]["expires_at"]
    advance(ws)
    stock[R.STATE_KEY] = R.pending_after_failure(stock, source_failure(ws), now=NOW + .2, cooldown_sec=90)
    assert stock[R.STATE_KEY]["expires_at"] == origin
    assert not R.recovery_refresh(stock, ws, now=NOW + .3)["allowed"]
    assert R.recovery_refresh(stock, ws, now=origin)["clear"]
    stock["scanner_promotion_id"] = "watch-2"
    assert R.recovery_refresh(stock, ws, now=NOW + .3)["clear"]


def test_source_recovery_runs_with_state_change_flag_off_but_keeps_provider_cooldown(monkeypatch):
    from src.engine import sniper_state_handlers as H
    stock, ws = pending()
    advance(ws)
    monkeypatch.setattr(H, "_rule", lambda *a: False)
    monkeypatch.setattr(H.time, "time", lambda: NOW + .2)
    monkeypatch.setattr(H, "WS_MANAGER", None)
    fresh = H._resolve_watching_state_change_refresh(stock, ws, now_ts=NOW + .2, last_ai_time=0, cooldown_sec=90)
    assert fresh["allowed"]
    prior = H._resolve_watching_state_change_refresh(stock, ws, now_ts=NOW + .2, last_ai_time=NOW - 10, cooldown_sec=90)
    assert not prior["allowed"] and prior["suppress_normal_refresh"]
    assert prior["reason"] == "machine_source_wait_completed_decision_cooldown"


def _fixed_watch_recovery(monkeypatch):
    from src.engine import sniper_state_handlers as H
    from src.engine.scalping import main_fixed_watch as fixed
    from src.engine.scalping import reversal_evaluation_context as policy

    stock, ws = pending()
    route = fixed.session_route(NOW, stock["code"])
    stock.update(
        watch_origin="MAIN_FIXED_WATCH", status="WATCHING",
        watch_admission_id=fixed.new_admission_id(NOW, route),
        watch_generation_id=fixed.generation_id(NOW, route),
        broker_route="SOR", market_session_bucket=route["bucket"],
    )
    stock[R.STATE_KEY] = R.pending_after_failure(
        stock, source_failure(ws), now=NOW, cooldown_sec=90)
    advance(ws)
    ws["last_realtime_type_item"] = {"0B": "005930_AL"}
    monkeypatch.setattr(H.time, "time", lambda: NOW + .2)
    monkeypatch.setattr(H, "WS_MANAGER", None)
    monkeypatch.setattr(policy, "prepare", lambda **kw: {
        "continuous_reversal": {
            "schema": "continuous_reversal_policy_v6", "family_sha256": "f" * 64}})
    return H, stock, ws


@pytest.mark.parametrize("signal_ready", [True, False])
def test_fixed_watch_source_recovery_reaches_native_claim_handoff(monkeypatch, signal_ready):
    from src.engine.scalping import reversal_source_diagnostics as native

    H, stock, ws = _fixed_watch_recovery(monkeypatch)
    origin = deepcopy(stock[R.STATE_KEY])
    claim = {
        "token": "fresh-native-claim",
        "snapshot": ({"event_id": "fresh-native-event", "epoch": NOW + .1}, {}),
    }
    calls = []

    def claim_current(*args, **kwargs):
        calls.append((args, kwargs))
        return claim if signal_ready else None

    monkeypatch.setattr(native, "claim_snapshot_with_receipt", claim_current)
    result = H._resolve_watching_state_change_refresh(
        stock, ws, now_ts=NOW + .2, last_ai_time=0, cooldown_sec=90)

    assert len(calls) == 1  # The async fixed-watch consumer requires this claim.
    assert stock[R.STATE_KEY] == origin
    if signal_ready:
        assert result["allowed"] and result["reason"] == "machine_source_fresh_retry"
        assert result["parent_attempt_id"] == origin["parent_attempt_id"]
        assert result["parent_observation_sha256"] == origin["parent_observation_sha256"]
        assert result["source_observed_at"] == NOW + .1
        assert stock["_continuous_reversal_pending_claim"] is claim
        assert claim["snapshot"][0]["epoch"] == NOW + .1
    else:
        assert not result["allowed"] and result["suppress_normal_refresh"]
        assert result["reason"] == "machine_source_wait_native_signal"
        assert "_continuous_reversal_pending_claim" not in stock


@pytest.mark.parametrize("block", ["completed_decision_cooldown", "stale_quote"])
def test_fixed_watch_recovery_cannot_claim_before_source_and_cooldown_pass(monkeypatch, block):
    from src.engine.scalping import reversal_source_diagnostics as native

    H, stock, ws = _fixed_watch_recovery(monkeypatch)
    last_ai = NOW - 10 if block == "completed_decision_cooldown" else 0
    if block == "stale_quote":
        ws["realtime_type_snapshots_by_route"][KEY]["0D"]["observed_epoch"] = NOW - 4
    monkeypatch.setattr(native, "claim_snapshot_with_receipt",
                        lambda *a, **kw: pytest.fail("blocked recovery must not claim a signal"))

    result = H._resolve_watching_state_change_refresh(
        stock, ws, now_ts=NOW + .2, last_ai_time=last_ai, cooldown_sec=90)
    assert not result["allowed"] and result["suppress_normal_refresh"]
    assert "_continuous_reversal_pending_claim" not in stock


def test_fixed_watch_recovery_does_not_reuse_requested_signal(monkeypatch):
    from src.engine.scalping import reversal_source_diagnostics as native

    H, stock, ws = _fixed_watch_recovery(monkeypatch)
    stock["_continuous_reversal_last_requested_id"] = "already-requested"
    monkeypatch.setattr(native, "claim_snapshot_with_receipt", lambda *a, **kw: {
        "token": "old-claim", "snapshot": ({"event_id": "already-requested"}, {})})
    result = H._resolve_watching_state_change_refresh(
        stock, ws, now_ts=NOW + .2, last_ai_time=0, cooldown_sec=90)
    assert not result["allowed"] and result["reason"] == "machine_source_wait_native_signal"
    assert "_continuous_reversal_pending_claim" not in stock


@pytest.mark.parametrize("aggregate_item", [None, "005930", "005930_NX"])
def test_fixed_watch_recovery_claim_uses_validated_exact_item(monkeypatch, aggregate_item):
    from src.engine.scalping import reversal_source_diagnostics as native

    H, stock, exact = _fixed_watch_recovery(monkeypatch)
    aggregate = deepcopy(exact)
    aggregate["last_realtime_type_item"] = {"0B": aggregate_item}
    # The recovery reader has newer exact data than the caller's aggregate.
    aggregate["realtime_type_snapshots_by_route"][KEY]["0B"]["observed_epoch"] = NOW
    monkeypatch.setattr(H, "WS_MANAGER", SimpleNamespace(
        get_exact_item_data=lambda code, item: deepcopy(exact)))
    calls = []
    claim = {"token": "exact-native", "snapshot": ({"event_id": "exact-event"}, {})}

    def claim_current(symbol, venue, session, **kwargs):
        calls.append((symbol, venue, session, kwargs["item"]))
        return claim if venue == "SOR" and kwargs["item"] == "005930_AL" else None

    monkeypatch.setattr(native, "claim_snapshot_with_receipt", claim_current)
    result = H._resolve_watching_state_change_refresh(
        stock, aggregate, now_ts=NOW + .2, last_ai_time=0, cooldown_sec=90)
    assert result["allowed"] and result["reason"] == "machine_source_fresh_retry"
    assert calls == [(stock["code"], "SOR", stock["market_session_bucket"], "005930_AL")]
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

    monkeypatch.setattr(H, "WS_MANAGER", SimpleNamespace(get_exact_item_data=read_exact))
    monkeypatch.setattr(native, "claim_snapshot_with_receipt",
                        lambda *a, **kw: pytest.fail("invalid exact source must not claim"))
    result = H._resolve_watching_state_change_refresh(
        stock, aggregate, now_ts=NOW + .2, last_ai_time=0, cooldown_sec=90)
    assert not result["allowed"] and result["suppress_normal_refresh"]
    assert "_continuous_reversal_pending_claim" not in stock


@pytest.mark.parametrize("expired", [False, True])
def test_fixed_watch_recovery_async_admission_preserves_native_deadline(monkeypatch, expired):
    from src.engine.ai.hot_path_ai_dispatcher import HotPathAIDispatcher
    from src.engine.scalping.scanner_async_eval import ScannerAsyncEvalCoordinator, FixedWatchGeneration
    from src.engine.scalping import reversal_source_diagnostics as native

    H, stock, ws = _fixed_watch_recovery(monkeypatch)
    origin = deepcopy(stock[R.STATE_KEY])
    event_epoch = NOW - 5.1 if expired else NOW + .1
    claim = {
        "token": "fresh-native-claim", "source_registration_receipt": {"sha256": "c" * 64},
        "snapshot": ({"event_id": "fresh-native-event", "epoch": event_epoch,
                      "symbol": stock["code"], "venue": "SOR", "source_item": "005930_AL"}, {}),
    }
    monkeypatch.setattr(native, "claim_snapshot_with_receipt", lambda *a, **kw: claim)
    monkeypatch.setattr(H, "_acknowledge_async_claim", lambda *a, **kw: None)
    monkeypatch.setattr(H, "_log_entry_pipeline", lambda *a, **kw: None)
    refresh = H._resolve_watching_state_change_refresh(
        stock, ws, now_ts=NOW + .2, last_ai_time=0, cooldown_sec=90)
    assert refresh["allowed"]

    coordinator = ScannerAsyncEvalCoordinator(ai_dispatcher=HotPathAIDispatcher(loaded_key_count=1))
    admitted = []

    def capture_request(request):
        # Stop at admission: no worker, provider, account or order I/O.
        admitted.append(request)
        return SimpleNamespace(accepted=True, reason="fixture_admitted")

    monkeypatch.setattr(coordinator, "submit", capture_request)
    try:
        result = H._resolve_scanner_async_entry_ai(
            stock, stock["code"], ws, None, {"scanner_async_eval_coordinator": coordinator},
            trigger_reason=refresh["reason"], last_ai_time=0, current_ai_score=0)
    finally:
        coordinator.shutdown()

    assert stock[R.STATE_KEY] == origin
    if expired:
        assert result == {"status": "commit_rejected",
                          "reason": "fixed_watch_native_identity_missing_or_expired"}
        assert not admitted
        assert "_fixed_watch_async_claim" not in stock
    else:
        assert result["status"] == "dispatched" and len(admitted) == 1
        context = admitted[0].context
        assert isinstance(context.generation, FixedWatchGeneration)
        assert context.deadline_epoch == event_epoch + 5  # Not dispatch time + 5.
        assert context.stock_snapshot[R.STATE_KEY]["parent_observation_sha256"] == origin["parent_observation_sha256"]
        assert stock["_fixed_watch_async_claim"]["token"] == claim["token"]


def test_route_price_is_available_even_when_aggregate_curr_is_missing(monkeypatch):
    from src.engine import sniper_state_handlers as H
    ws, context = fixture()
    context["request_code"] = "005930_AL"
    aggregate = dict(curr=0, last_ws_update_ts=NOW - .01, market_data_transport_epoch=1)
    ws["curr"] = 0
    monkeypatch.setattr(H.time, "time", lambda: NOW)
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_PRE_SUBMIT_QUOTE_REFRESH_ENABLED", "true")
    calls = []
    monkeypatch.setattr(H, "WS_MANAGER", SimpleNamespace(
        get_latest_data=lambda _: deepcopy(aggregate),
        get_exact_item_data=lambda code, item: calls.append((code, item)) or deepcopy(ws),
    ))
    monkeypatch.setattr(H, "revalidate_entry_candle_snapshot", lambda c, w, now_ts: deepcopy(c))
    selected, ticks, _, fields = H._refresh_prepared_entry_inputs("005930", ws, [], context)
    assert fields["entry_ai_final_ws_snapshot_refresh_applied"]
    assert fields["entry_ai_final_ws_snapshot_refresh_reason"] == "latest_locked_observation_only"
    assert selected["curr"] == 275500 and ticks == ws["recent_trade_ticks_by_route"][KEY]
    assert calls and all(item == "005930_AL" for _, item in calls)
    # Final submit has no observation exception and still rejects this input.
    _, submit_fields = H._pre_submit_refresh_real_ws_snapshot("005930", ws, "SCALPING", refresh_even_if_input_fresh=True)
    assert submit_fields["pre_submit_ws_snapshot_refresh_applied"] is False


def test_source_retry_cache_key_changes_parent_but_pins_inflight_generation():
    from src.engine import sniper_state_handlers as H
    stock, _ = pending()
    generation = SimpleNamespace(generation_id="g-1")
    key1 = H._scanner_async_entry_cache_key(stock, generation=generation, trigger_reason="machine_source_fresh_retry", last_ai_time=0)
    stock[R.STATE_KEY]["parent_observation_sha256"] = "c" * 64
    key2 = H._scanner_async_entry_cache_key(stock, generation=generation, trigger_reason="machine_source_fresh_retry", last_ai_time=0)
    assert key1 != key2
    stock.update(_scanner_async_generation_id="g-1", _scanner_async_cache_key=key1)
    assert H._scanner_async_entry_cache_key(stock, generation=generation, trigger_reason="machine_source_fresh_retry", last_ai_time=0) == key1


def test_failed_input_clock_is_separate_and_valid_recheck_or_provider_result_closes_lease(monkeypatch):
    from src.engine import sniper_state_handlers as H
    stock, ws = pending()
    clocks = {"005930": NOW - 10}
    monkeypatch.setattr(H, "LAST_AI_CALL_TIMES", clocks)
    source = source_failure(ws)
    stock.pop(R.STATE_KEY)
    H._commit_watching_entry_evaluation(stock, "005930", source, completed_at=NOW, cooldown_sec=90, strategy="SCALPING")
    assert R.STATE_KEY in stock and clocks["005930"] == NOW - 10
    # A real machine RECHECK is a completed evaluation, even with no AI call.
    assessed = {**source, "machine_evaluation_status": "assessed", "entry_mechanistic_action": "RECHECK"}
    H._commit_watching_entry_evaluation(stock, "005930", assessed, completed_at=NOW + 1, cooldown_sec=90, strategy="SCALPING")
    assert R.STATE_KEY not in stock and clocks["005930"] == NOW + 1
    provider = {**source, "provider_called": True, "entry_ai_advisory_verdict": "VETO"}
    H._commit_watching_entry_evaluation(stock, "005930", provider, completed_at=NOW + 2, cooldown_sec=90, strategy="SCALPING")
    assert R.STATE_KEY not in stock and clocks["005930"] == NOW + 2


def test_expired_lease_cannot_stick_on_manager_error(monkeypatch):
    from src.engine import sniper_state_handlers as H
    stock, ws = pending()
    monkeypatch.setattr(H.time, "time", lambda: NOW + 90)
    monkeypatch.setattr(H, "_rule", lambda *a: False)
    monkeypatch.setattr(H, "WS_MANAGER", SimpleNamespace(get_exact_item_data=lambda *a: pytest.fail("expired lease must not read")))
    result = H._resolve_watching_state_change_refresh(stock, ws, now_ts=NOW, last_ai_time=0, cooldown_sec=90)
    assert R.STATE_KEY not in stock and not result["allowed"]


@pytest.mark.parametrize("damage", ["key", "parent", "scope", "timing"])
def test_corrupt_pending_receipt_cannot_create_retry_or_crash(damage):
    stock, ws = pending()
    advance(ws)
    if damage == "key": stock[R.STATE_KEY].pop("selected_key")
    elif damage == "parent": stock[R.STATE_KEY]["parent_observation_sha256"] = "bad"
    elif damage == "scope": stock[R.STATE_KEY]["scope"] = None
    elif damage == "timing": stock[R.STATE_KEY]["source_timing"] = "bad"
    assert not R.recovery_refresh(stock, ws, now=NOW + .2)["allowed"]
