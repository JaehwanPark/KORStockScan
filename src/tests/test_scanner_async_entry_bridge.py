from __future__ import annotations

import time
from datetime import datetime

import pytest

from src.engine.ai.hot_path_ai_dispatcher import HotPathAIDispatcher
from src.engine.scalping.scanner_async_eval import ScannerAsyncEvalCoordinator
from src.engine.scalping.scanner_runtime_scheduler import ScannerGeneration
from src.engine import sniper_state_handlers as handlers


class _FakeAI:
    def analyze_target(self, *args, **kwargs):
        return {"action": "BUY", "score": 77, "reason": "fresh continuation"}


def _generation(venue="KRX"):
    return ScannerGeneration(
        code="005930",
        promotion_id="PROMO-ASYNC",
        revision=1,
        record_id=7,
        venue=venue,
        promotion_epoch=time.time() - 1,
        attach_epoch=time.time() - 0.5,
        observed_price=1000,
        source_signature="VALUE_TOP",
    )


@pytest.mark.parametrize(
    ("venue", "ws_suffix", "ws_route", "expected_request_code"),
    (
        ("KRX", "", "", "005930"),
        ("KRX", "_AL", "krx_nxt_integrated", "005930_AL"),
        ("PREMARKET_KRX_LIKE", "", "", "005930_NX"),
        ("NXT", "", "", "005930_NX"),
    ),
)
def test_async_entry_bridge_prepares_off_thread_then_commits_on_current_state(
    monkeypatch,
    venue,
    ws_suffix,
    ws_route,
    expected_request_code,
):
    monkeypatch.setattr(handlers, "KIWOOM_TOKEN", "token")
    requested_codes = []
    monkeypatch.setattr(
        handlers.kiwoom_utils,
        "get_tick_history_ka10003",
        lambda token, code, **kwargs: (
            requested_codes.append(code) or [{"price": 1000}]
        ),
    )
    monkeypatch.setattr(
        handlers,
        "fetch_entry_candles_with_meta",
        lambda *args, **kwargs: ([{"close": 1000}], {"source": "test"}),
    )
    monkeypatch.setattr(
        handlers,
        "build_entry_candle_context",
        lambda *args, **kwargs: {"schema": "test"},
    )
    monkeypatch.setattr(
        handlers,
        "_extract_ai_overlap_snapshot",
        lambda **kwargs: {},
    )
    monkeypatch.setattr(
        handlers,
        "_update_ai_quote_freshness_fields",
        lambda ws_data: None,
    )
    monkeypatch.setattr(handlers, "_log_entry_pipeline", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        handlers,
        "_has_open_pending_entry_orders",
        lambda stock: False,
    )
    monkeypatch.setattr(handlers, "COOLDOWNS", {})

    dispatcher = HotPathAIDispatcher(loaded_key_count=2)
    coordinator = ScannerAsyncEvalCoordinator(ai_dispatcher=dispatcher)
    generation = _generation(venue)
    stock = {
        "id": 7,
        "code": "005930",
        "name": "삼성전자",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "scanner_generation_id": generation.generation_id,
        "scanner_promotion_id": generation.promotion_id,
        # Promotion reference price is not evidence of an existing position.
        "buy_price": 1000,
        "buy_qty": 0,
        "effective_venue": venue,
        "venue_resolution": f"session_clock_explicit_{venue.lower()}",
        "source_signature": "VALUE_TOP",
    }
    ws_data = {
        "curr": 1001,
        "orderbook": {"ask": 1002, "bid": 1000},
        "last_ws_update_ts": time.time(),
    }
    if ws_suffix:
        ws_data["market_suffix"] = ws_suffix
    if ws_route:
        ws_data["market_route"] = ws_route
    runtime = {
        "scanner_async_eval_coordinator": coordinator,
        "scanner_async_generation": generation,
        "scanner_async_commit_phase": False,
    }
    dispatched = handlers._resolve_scanner_async_entry_ai(
        stock,
        "005930",
        ws_data,
        _FakeAI(),
        runtime,
        trigger_reason="first_call",
        last_ai_time=0,
        current_ai_score=50,
    )
    assert dispatched["status"] == "dispatched"

    deadline = time.time() + 1
    while coordinator.pending_count() and time.time() < deadline:
        coordinator.poll()
        time.sleep(0.005)
    runtime["scanner_async_commit_phase"] = True
    committed = handlers._resolve_scanner_async_entry_ai(
        stock,
        "005930",
        ws_data,
        _FakeAI(),
        runtime,
        trigger_reason="first_call",
        last_ai_time=0,
        current_ai_score=50,
    )
    coordinator.shutdown()

    assert committed["status"] == "completed"
    assert committed["ai_decision"]["action"] == "BUY"
    assert [dict(item) for item in committed["prepared_context"]["recent_ticks"]] == [
        {"price": 1000}
    ]
    assert requested_codes == [expected_request_code]
    assert "_scanner_async_cache_key" not in stock


def test_opening_rotation_context_prepares_off_thread_and_commits_once(monkeypatch):
    monkeypatch.setattr(handlers, "KIWOOM_TOKEN", "token")
    monkeypatch.setattr(
        handlers,
        "_resolve_opening_rotation_freshness_envelope",
        lambda *_args, **_kwargs: (
            {"curr": 1001, "last_ws_update_ts": time.time()},
            {
                "opening_rotation_freshness_envelope_ready": True,
                "market_data_effective_quote_age_ms": 100.0,
                "opening_rotation_freshness_envelope_rest_attempted": False,
            },
        ),
    )
    monkeypatch.setattr(
        handlers,
        "_fetch_opening_rotation_candles_bounded",
        lambda _code: ([{"close": 1000}], "ok"),
    )
    monkeypatch.setattr(
        handlers,
        "extract_scalping_feature_packet",
        lambda *_args, **_kwargs: {"curr": 1001, "quote_stale": False},
    )
    monkeypatch.setattr(
        handlers, "_scanner_async_quote_is_fresh", lambda *_a, **_k: True
    )
    monkeypatch.setattr(
        handlers, "_has_open_pending_entry_orders", lambda _stock: False
    )
    monkeypatch.setattr(handlers, "_log_entry_pipeline", lambda *args, **kwargs: None)
    monkeypatch.setattr(handlers, "COOLDOWNS", {})

    dispatcher = HotPathAIDispatcher(loaded_key_count=1)
    coordinator = ScannerAsyncEvalCoordinator(ai_dispatcher=dispatcher)
    generation = _generation("KRX")
    stock = {
        "id": 7,
        "code": "005930",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "scanner_generation_id": generation.generation_id,
        "scanner_promotion_id": generation.promotion_id,
        "effective_venue": "KRX",
        "venue_resolution": "session_clock_explicit_krx",
        "source_signature": "VALUE_TOP",
    }
    ws_data = {"curr": 1001, "last_ws_update_ts": time.time()}
    runtime = {
        "scanner_async_eval_coordinator": coordinator,
        "scanner_async_generation": generation,
        "scanner_async_commit_phase": False,
    }

    dispatched = handlers._resolve_scanner_async_opening_rotation_context(
        stock, "005930", ws_data, runtime
    )
    assert dispatched["status"] == "dispatched"
    assert "_scanner_opening_rotation_async_cache_key" in stock

    deadline = time.time() + 1
    while coordinator.pending_count() and time.time() < deadline:
        coordinator.poll()
        time.sleep(0.005)
    runtime["scanner_async_commit_phase"] = True
    committed = handlers._resolve_scanner_async_opening_rotation_context(
        stock, "005930", ws_data, runtime
    )
    coordinator.shutdown()

    assert committed["status"] == "completed"
    assert committed["feature_packet"]["curr"] == 1001
    assert "_scanner_opening_rotation_async_cache_key" not in stock


def test_opening_rotation_async_commit_avoids_generic_watching_reentry(monkeypatch):
    generation = _generation("KRX")
    stock = {
        "id": 7,
        "code": "005930",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "scanner_generation_id": generation.generation_id,
        "_scanner_opening_rotation_async_generation_id": generation.generation_id,
        "_scanner_opening_rotation_async_cache_key": "opening_rotation:test",
    }
    monkeypatch.setattr(
        handlers, "_manual_control_exclusion_blocked", lambda *_a, **_k: False
    )
    monkeypatch.setattr(handlers, "is_buy_side_paused", lambda: False)
    monkeypatch.setattr(handlers, "is_scalping_buy_time_allowed", lambda _value: True)
    monkeypatch.setattr(
        handlers,
        "evaluate_scalp_same_symbol_loss_reentry_guard",
        lambda *_a, **_k: (_ for _ in ()).throw(
            AssertionError("commit must not hydrate re-entry history")
        ),
    )
    monkeypatch.setattr(handlers, "COOLDOWNS", {})
    monkeypatch.setattr(handlers, "ALERTED_STOCKS", set())
    opened = []

    def _opening_handler(_stock, _code, _ws_data, runtime, _config):
        opened.append(runtime)
        runtime["is_trigger"] = True
        runtime["opening_rotation_1pct_live"] = True
        return True

    submitted = []
    monkeypatch.setattr(handlers, "_handle_watching_opening_rotation", _opening_handler)
    monkeypatch.setattr(
        handlers,
        "_submit_watching_triggered_entry",
        lambda *args: submitted.append(args),
    )

    assert handlers.handle_scanner_async_opening_rotation_commit(
        stock,
        "005930",
        {"curr": 1001},
        admin_id=1,
        now_ts=time.time(),
        now_dt=datetime.now(),
        scanner_async_generation=generation,
    )
    assert len(opened) == 1
    assert len(submitted) == 1
    assert submitted[0][4]["scanner_async_commit_phase"] is True


def test_opening_rotation_async_commit_does_not_claim_generic_result(monkeypatch):
    generation = _generation("KRX")
    stock = {
        "strategy": "SCALPING",
        "_scanner_opening_rotation_async_generation_id": generation.generation_id,
        "_scanner_opening_rotation_async_cache_key": "opening_rotation:test",
        "_scanner_async_cache_key": "watching:test",
    }
    monkeypatch.setattr(
        handlers,
        "_handle_watching_opening_rotation",
        lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("must not run")),
    )

    assert not handlers.handle_scanner_async_opening_rotation_commit(
        stock,
        "005930",
        {"curr": 1001},
        admin_id=1,
        now_ts=time.time(),
        now_dt=datetime.now(),
        scanner_async_generation=generation,
    )
