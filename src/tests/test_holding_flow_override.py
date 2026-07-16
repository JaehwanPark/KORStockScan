from types import SimpleNamespace
from datetime import datetime, time as dt_time, timedelta, timezone

from src.engine import sniper_overnight_gatekeeper as overnight
from src.engine import sniper_state_handlers as handlers


class DummyFlowAI:
    def __init__(self, action):
        self.action = action
        self.calls = []

    def evaluate_scalping_holding_flow(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return {
            "action": self.action,
            "score": 18 if self.action == "HOLD" else 82,
            "flow_state": "흡수" if self.action == "HOLD" else "붕괴",
            "thesis": "flow thesis",
            "evidence": ["tick flow", "minute flow"],
            "reason": f"flow {self.action}",
            "next_review_sec": 45,
            "ai_parse_fail": False,
            "ai_parse_ok": True,
            "ai_response_ms": 1234,
            "ai_prompt_type": "holding_exit_flow",
            "ai_result_source": "live",
            "ai_model": "tier2-model",
            "ai_model_tier": "tier2",
            "cache_mode": "miss",
        }


def _patch_holding_context(monkeypatch, logs):
    monkeypatch.setattr(
        handlers.kiwoom_utils,
        "get_tick_history_ka10003",
        lambda token, code, limit=30: [{"price": 10000, "volume": 10, "side": "BUY"}],
    )
    monkeypatch.setattr(
        handlers.kiwoom_utils,
        "get_minute_candles_ka10080",
        lambda token, code, limit=60: [
            {"close": 9950, "high": 10050, "low": 9900, "volume": 1000},
            {"close": 10000, "high": 10080, "low": 9940, "volume": 1200},
        ],
    )
    monkeypatch.setattr(
        handlers,
        "_log_holding_pipeline",
        lambda stock, code, stage, **fields: logs.append((stage, fields)),
    )
    monkeypatch.setattr(
        handlers,
        "_emit_stat_action_decision_snapshot",
        lambda **kwargs: logs.append(("stat_action_decision_snapshot", kwargs)),
    )


def _stock():
    return {"name": "테스트", "strategy": "SCALPING", "buy_qty": 1}


def _ws():
    return {
        "curr": 10000,
        "v_pw": 120,
        "buy_ratio": 58,
        "orderbook": {"asks": [{"price": 10010}], "bids": [{"price": 9990}]},
    }


def _trailing_continuation_micro_fields():
    return {
        "holding_flow_micro_estimator_source_state": "fresh_ws_order_flow_delta",
        "holding_flow_micro_estimator_confidence": 0.85,
        "holding_flow_micro_estimator_true_ofi_ewma": 0.01,
        "holding_flow_micro_estimator_depth_imbalance_ewma": 0.46,
        "holding_flow_micro_estimator_pressure_ewma": 65.0,
        "holding_flow_micro_estimator_top_depth_ratio": 2.0,
        "holding_flow_micro_estimator_true_ofi_sample_count": 6,
        "holding_flow_micro_estimator_age_sec": 0.2,
    }


def _enable_trailing_continuation_recheck(monkeypatch):
    monkeypatch.setenv(
        "KORSTOCKSCAN_SCALP_TRAILING_CONTINUATION_RECHECK_ENABLED", "true"
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_SCALP_TRAILING_CONTINUATION_RECHECK_ACTIVE_DATE",
        "2026-07-15",
    )
    monkeypatch.setenv("KORSTOCKSCAN_SCALP_TRAILING_CONTINUATION_RECHECK_TTL_SEC", "15")


def _fresh_reversal_features():
    return {
        "tick_context_quality": "fresh_computed",
        "tick_context_stale": False,
        "tick_latest_age_ms": 100,
        "quote_stale": False,
        "quote_age_ms": 100,
        "tick_aggressor_pressure_usable": True,
        "tick_aggressor_trusted_count": 6,
        "large_sell_print_detected": False,
        "micro_vwap_available": True,
        "minute_candle_window_fresh": True,
        "curr_vs_micro_vwap_bp": 3.0,
    }


def test_holding_flow_ofi_prefers_micro_estimator_true_ofi(monkeypatch):
    store = handlers.MicroEstimatorStore()
    monkeypatch.setattr(handlers, "_SCALPING_MICRO_ESTIMATOR_STORE", store)
    monkeypatch.setattr(
        handlers,
        "_ofi_ai_smoothing_config",
        lambda: handlers.OfiSmoothingConfig(
            raw_weight=1.0,
            bullish_threshold=0.45,
            bearish_threshold=-0.45,
            release_threshold=0.15,
            persistence_required=1,
            stale_threshold_ms=700,
        ),
    )
    for idx in range(15):
        store.update_from_ws_quote(
            "005930",
            {
                "best_bid": 10000 + idx,
                "best_ask": 10020,
                "best_bid_qty": 1000 + (idx * 1000),
                "best_ask_qty": 1,
                "quote_age_ms": 100.0,
                "quote_stale": False,
            },
            now_ts=1000.0 + idx,
            tier="hot",
        )

    stock = _stock()
    micro, state = handlers._evaluate_holding_flow_ofi_state(
        stock,
        "005930",
        curr_price=10000,
        now_ts=1014.0,
    )

    assert micro["reason"] == "micro_estimator_true_ofi_primary"
    assert micro["ofi_threshold_source"] == "micro_estimator_state_v1"
    assert micro["ofi_calibration_bucket"] == "true_ofi"
    assert state.reason == "micro_estimator_true_ofi_primary"
    assert state.micro_score_raw == round(handlers.micro_score_raw(micro), 6)
    assert state.regime == handlers.OFI_STABLE_BULLISH
    assert stock["holding_flow_ofi_reason"] == "micro_estimator_true_ofi_primary"


def test_holding_flow_ofi_falls_back_to_legacy_observer_without_micro_state(
    monkeypatch,
):
    monkeypatch.setattr(
        handlers, "_SCALPING_MICRO_ESTIMATOR_STORE", handlers.MicroEstimatorStore()
    )
    monkeypatch.setattr(
        handlers,
        "_ofi_ai_smoothing_config",
        lambda: handlers.OfiSmoothingConfig(
            raw_weight=1.0,
            bullish_threshold=0.45,
            bearish_threshold=-0.45,
            release_threshold=0.15,
            persistence_required=1,
            stale_threshold_ms=700,
        ),
    )
    monkeypatch.setattr(
        handlers,
        "_build_live_orderbook_micro_context",
        lambda code, *, curr_price: {
            "ready": True,
            "reason": "ready",
            "micro_state": "bearish",
            "observer_healthy": True,
            "snapshot_age_ms": 100,
            "ofi_z": -2.0,
            "qi_ewma": 0.38,
        },
    )

    stock = _stock()
    micro, state = handlers._evaluate_holding_flow_ofi_state(
        stock,
        "005930",
        curr_price=10000,
        now_ts=1000.0,
    )

    assert micro["micro_state"] == "bearish"
    assert state.reason == "ready"
    assert state.regime == handlers.OFI_STABLE_BEARISH
    assert stock["holding_flow_ofi_reason"] == "ready"


def test_holding_flow_micro_estimator_reads_nested_orderbook_ws(monkeypatch):
    store = handlers.MicroEstimatorStore()
    monkeypatch.setattr(handlers, "_SCALPING_MICRO_ESTIMATOR_STORE", store)
    monkeypatch.setattr(
        handlers,
        "_ofi_ai_smoothing_config",
        lambda: handlers.OfiSmoothingConfig(
            raw_weight=1.0,
            bullish_threshold=0.45,
            bearish_threshold=-0.45,
            release_threshold=0.15,
            persistence_required=1,
            stale_threshold_ms=700,
        ),
    )
    stock = _stock()
    fields = {}
    for idx in range(15):
        fields = handlers._scalping_micro_estimator_log_fields(
            stock=stock,
            code="005930",
            ws_data={
                "curr": 10000 + idx,
                "orderbook": {
                    "bids": [{"price": 10000 + idx, "volume": 1000 + (idx * 1000)}],
                    "asks": [{"price": 10020, "volume": 1}],
                },
                "quote_age_ms": 100.0,
                "quote_stale": False,
            },
            now_ts=1000.0 + idx,
            prefix="holding_flow_micro_estimator",
            consumer_stage="holding_flow_override",
            tier="hot",
        )

    assert fields["holding_flow_micro_estimator_update_applied"] is True
    assert fields["holding_flow_micro_estimator_update_reason"] == "ws_quote"
    assert fields["holding_flow_micro_estimator_true_ofi_sample_count"] > 0
    micro, state = handlers._evaluate_holding_flow_ofi_state(
        stock,
        "005930",
        curr_price=10000,
        now_ts=1014.0,
    )
    assert micro["reason"] == "micro_estimator_true_ofi_primary"
    assert state.regime == handlers.OFI_STABLE_BULLISH


def test_soft_stop_candidate_with_flow_hold_defers_sell(monkeypatch):
    logs = []
    _patch_holding_context(monkeypatch, logs)
    ai = DummyFlowAI("HOLD")

    proceed = handlers._evaluate_holding_flow_override(
        stock=_stock(),
        code="005930",
        strategy="SCALPING",
        ws_data=_ws(),
        ai_engine=ai,
        exit_rule="scalp_soft_stop_pct",
        sell_reason_type="LOSS",
        reason="soft stop",
        profit_rate=-1.10,
        peak_profit=0.00,
        drawdown=1.10,
        current_ai_score=25,
        held_sec=80,
        curr_price=10000,
        buy_price=10110,
        now_ts=1000.0,
    )

    assert proceed is False
    assert len(ai.calls) == 1
    review = next(
        fields for stage, fields in logs if stage == "holding_flow_override_review"
    )
    assert review["ai_model"] == "tier2-model"
    assert review["ai_model_tier"] == "tier2"
    assert review["ai_prompt_type"] == "holding_exit_flow"
    assert review["ai_response_ms"] == 1234
    assert any(stage == "holding_flow_override_defer_exit" for stage, _ in logs)


def test_bad_entry_candidate_with_flow_exit_allows_sell(monkeypatch):
    logs = []
    _patch_holding_context(monkeypatch, logs)
    ai = DummyFlowAI("EXIT")

    proceed = handlers._evaluate_holding_flow_override(
        stock=_stock(),
        code="005930",
        strategy="SCALPING",
        ws_data=_ws(),
        ai_engine=ai,
        exit_rule="scalp_bad_entry_refined_canary",
        sell_reason_type="LOSS",
        reason="bad entry",
        profit_rate=-1.30,
        peak_profit=0.00,
        drawdown=1.30,
        current_ai_score=30,
        held_sec=190,
        curr_price=10000,
        buy_price=10130,
        now_ts=1000.0,
    )

    assert proceed is True
    assert len(ai.calls) == 1
    assert any(stage == "holding_flow_override_exit_confirmed" for stage, _ in logs)


def test_flow_exit_is_debounced_by_stable_bullish_ofi(monkeypatch):
    logs = []
    _patch_holding_context(monkeypatch, logs)
    monkeypatch.setattr(
        handlers,
        "_evaluate_holding_flow_ofi_state",
        lambda stock, code, *, curr_price, now_ts=None: (
            {
                "ready": True,
                "micro_state": "bullish",
                "observer_healthy": True,
                "snapshot_age_ms": 100,
            },
            handlers.OfiSmoothingState(
                regime=handlers.OFI_STABLE_BULLISH, micro_score_smooth=0.62
            ),
        ),
    )
    ai = DummyFlowAI("EXIT")
    stock = _stock()

    proceed = handlers._evaluate_holding_flow_override(
        stock=stock,
        code="005930",
        strategy="SCALPING",
        ws_data=_ws(),
        ai_engine=ai,
        exit_rule="scalp_soft_stop_pct",
        sell_reason_type="LOSS",
        reason="soft stop",
        profit_rate=-1.10,
        peak_profit=0.00,
        drawdown=1.10,
        current_ai_score=25,
        held_sec=80,
        curr_price=10000,
        buy_price=10110,
        now_ts=1000.0,
    )

    assert proceed is False
    assert stock["holding_flow_ofi_debounce_started_at"] == 1000.0
    assert stock["holding_flow_ofi_debounce_anchor_profit"] == -1.10
    assert stock["holding_flow_ofi_debounce_count"] == 1
    assert stock["holding_flow_ofi_debounce_exit_rule"] == "scalp_soft_stop_pct"
    assert any(
        stage == "holding_flow_ofi_smoothing_applied"
        and fields.get("smoothing_action") == "DEBOUNCE_EXIT"
        for stage, fields in logs
    )
    assert any(
        stage == "stat_action_decision_snapshot"
        and kwargs.get("rejected_actions") == ["exit_now:ofi_stable_bullish_debounce"]
        for stage, kwargs in logs
    )


def test_flow_exit_bullish_ofi_debounce_count_limit_allows_sell(monkeypatch):
    logs = []
    _patch_holding_context(monkeypatch, logs)
    monkeypatch.setattr(
        handlers,
        "_evaluate_holding_flow_ofi_state",
        lambda stock, code, *, curr_price, now_ts=None: (
            {
                "ready": True,
                "micro_state": "bullish",
                "observer_healthy": True,
                "snapshot_age_ms": 100,
            },
            handlers.OfiSmoothingState(
                regime=handlers.OFI_STABLE_BULLISH, micro_score_smooth=0.62
            ),
        ),
    )
    ai = DummyFlowAI("EXIT")
    stock = {
        **_stock(),
        "holding_flow_override_candidate_key": "scalp_soft_stop_pct:LOSS",
        "holding_flow_override_started_at": 990.0,
        "holding_flow_override_candidate_profit": -1.00,
        "holding_flow_ofi_debounce_started_at": 995.0,
        "holding_flow_ofi_debounce_anchor_profit": -1.05,
        "holding_flow_ofi_debounce_count": 2,
        "holding_flow_ofi_debounce_exit_rule": "scalp_soft_stop_pct",
    }

    proceed = handlers._evaluate_holding_flow_override(
        stock=stock,
        code="005930",
        strategy="SCALPING",
        ws_data=_ws(),
        ai_engine=ai,
        exit_rule="scalp_soft_stop_pct",
        sell_reason_type="LOSS",
        reason="soft stop",
        profit_rate=-1.12,
        peak_profit=0.00,
        drawdown=1.12,
        current_ai_score=25,
        held_sec=80,
        curr_price=9988,
        buy_price=10100,
        now_ts=1000.0,
    )

    assert proceed is True
    no_change = next(
        fields
        for stage, fields in logs
        if stage == "holding_flow_ofi_smoothing_applied"
        and fields.get("smoothing_action") == "NO_CHANGE"
    )
    assert no_change["ofi_debounce_allowed"] is False
    assert no_change["ofi_debounce_reason"] == "count_limit_reached"
    assert no_change["ofi_debounce_max_count"] == 2
    assert any(stage == "holding_flow_override_exit_confirmed" for stage, _ in logs)


def test_prior_ofi_debounce_max_defer_force_exit_is_post_debounce_guard(monkeypatch):
    logs = []
    _patch_holding_context(monkeypatch, logs)
    ai = DummyFlowAI("HOLD")
    stock = {
        **_stock(),
        "holding_flow_override_candidate_key": "scalp_soft_stop_pct:LOSS",
        "holding_flow_override_started_at": 900.0,
        "holding_flow_override_candidate_profit": -0.10,
        "holding_flow_ofi_debounce_started_at": 950.0,
        "holding_flow_ofi_debounce_anchor_profit": -0.10,
        "holding_flow_ofi_debounce_count": 1,
        "holding_flow_ofi_debounce_exit_rule": "scalp_soft_stop_pct",
    }

    proceed = handlers._evaluate_holding_flow_override(
        stock=stock,
        code="005930",
        strategy="SCALPING",
        ws_data=_ws(),
        ai_engine=ai,
        exit_rule="scalp_soft_stop_pct",
        sell_reason_type="LOSS",
        reason="soft stop",
        profit_rate=-0.35,
        peak_profit=0.00,
        drawdown=0.35,
        current_ai_score=30,
        held_sec=120,
        curr_price=9965,
        buy_price=10000,
        now_ts=1000.0,
    )

    assert proceed is True
    assert ai.calls == []
    force_exit = next(
        fields
        for stage, fields in logs
        if stage == "holding_flow_override_force_exit"
        and fields.get("force_reason") == "max_defer_sec"
    )
    assert force_exit["ofi_force_exit_phase"] == "post_debounce_guard"
    assert force_exit["ofi_debounce_prior"] is True
    assert force_exit["ofi_debounce_elapsed_sec"] == 50
    assert force_exit["ofi_debounce_profit_delta"] == "-0.25"
    assert force_exit["ofi_force_exit_terminal_reason"] == "max_defer_sec"


def test_max_defer_gets_one_bounded_extension_for_fresh_supportive_composite_micro(
    monkeypatch,
):
    logs = []
    _patch_holding_context(monkeypatch, logs)
    ai = DummyFlowAI("EXIT")
    micro_fields = {
        "holding_flow_micro_estimator_confidence": "0.85",
        "holding_flow_micro_estimator_true_ofi_ewma": "-0.001",
        "holding_flow_micro_estimator_depth_imbalance_ewma": "0.7752",
        "holding_flow_micro_estimator_pressure_ewma": "72.048",
        "holding_flow_micro_estimator_top_depth_ratio": "4.8527",
        "holding_flow_micro_estimator_true_ofi_sample_count": "780",
        "holding_flow_micro_estimator_age_sec": "0.0",
    }
    monkeypatch.setattr(
        handlers,
        "_scalping_micro_estimator_log_fields",
        lambda **kwargs: dict(micro_fields),
    )
    stock = {
        **_stock(),
        "holding_flow_override_candidate_key": "scalp_soft_stop_pct:LOSS",
        "holding_flow_override_started_at": 900.0,
        "holding_flow_override_candidate_profit": -3.55,
    }

    first = handlers._evaluate_holding_flow_override(
        stock=stock,
        code="105560",
        strategy="SCALPING",
        ws_data={**_ws(), "last_ws_update_ts": 999.5},
        ai_engine=ai,
        exit_rule="scalp_soft_stop_pct",
        sell_reason_type="LOSS",
        reason="soft stop",
        profit_rate=-3.72,
        peak_profit=-0.23,
        drawdown=3.49,
        current_ai_score=68,
        held_sec=64_697,
        curr_price=176700,
        buy_price=183100,
        now_ts=1000.0,
    )

    assert first is False
    assert ai.calls == []
    assert stock["holding_flow_max_defer_extension_used"] is True
    assert stock["holding_flow_max_defer_extension_until"] == 1090.0
    extension = next(
        fields
        for stage, fields in logs
        if stage == "holding_flow_max_defer_bullish_extension"
    )
    assert (
        extension["max_defer_extension_support_reason"] == "supportive_composite_micro"
    )
    assert extension["max_defer_extension_trusted_ws"] is True

    second = handlers._evaluate_holding_flow_override(
        stock=stock,
        code="105560",
        strategy="SCALPING",
        ws_data={**_ws(), "last_ws_update_ts": 1090.5},
        ai_engine=ai,
        exit_rule="scalp_soft_stop_pct",
        sell_reason_type="LOSS",
        reason="soft stop",
        profit_rate=-3.70,
        peak_profit=-0.23,
        drawdown=3.47,
        current_ai_score=68,
        held_sec=64_788,
        curr_price=176700,
        buy_price=183100,
        now_ts=1091.0,
    )

    assert second is True
    assert (
        len(
            [
                1
                for stage, _ in logs
                if stage == "holding_flow_max_defer_bullish_extension"
            ]
        )
        == 1
    )
    assert any(
        stage == "holding_flow_override_force_exit"
        and fields.get("force_reason") == "max_defer_sec"
        for stage, fields in logs
    )


def test_stale_ws_force_exit_is_source_quality_guard_without_debounce(monkeypatch):
    logs = []
    _patch_holding_context(monkeypatch, logs)
    monkeypatch.setattr(handlers.time, "time", lambda: 1000.0)
    ai = DummyFlowAI("EXIT")
    ws = {**_ws(), "last_ws_update_ts": 990.0}

    proceed = handlers._evaluate_holding_flow_override(
        stock=_stock(),
        code="005930",
        strategy="SCALPING",
        ws_data=ws,
        ai_engine=ai,
        exit_rule="scalp_soft_stop_pct",
        sell_reason_type="LOSS",
        reason="soft stop",
        profit_rate=-1.10,
        peak_profit=0.00,
        drawdown=1.10,
        current_ai_score=25,
        held_sec=80,
        curr_price=10000,
        buy_price=10110,
        now_ts=1000.0,
    )

    assert proceed is True
    assert ai.calls == []
    assert not any(
        stage == "holding_flow_ofi_smoothing_applied"
        and fields.get("smoothing_action") == "DEBOUNCE_EXIT"
        for stage, fields in logs
    )
    force_exit = next(
        fields
        for stage, fields in logs
        if stage == "holding_flow_override_force_exit"
        and fields.get("force_reason") == "ws_stale"
    )
    assert force_exit["ofi_force_exit_phase"] == "source_quality_guard"
    assert force_exit["ofi_debounce_prior"] is False


def test_no_recent_ticks_force_exit_is_source_quality_guard(monkeypatch):
    logs = []
    _patch_holding_context(monkeypatch, logs)
    monkeypatch.setattr(
        handlers.kiwoom_utils,
        "get_tick_history_ka10003",
        lambda token, code, limit=30: [],
    )
    ai = DummyFlowAI("EXIT")

    proceed = handlers._evaluate_holding_flow_override(
        stock=_stock(),
        code="005930",
        strategy="SCALPING",
        ws_data=_ws(),
        ai_engine=ai,
        exit_rule="scalp_soft_stop_pct",
        sell_reason_type="LOSS",
        reason="soft stop",
        profit_rate=-1.10,
        peak_profit=0.00,
        drawdown=1.10,
        current_ai_score=25,
        held_sec=80,
        curr_price=10000,
        buy_price=10110,
        now_ts=1000.0,
    )

    assert proceed is True
    assert ai.calls == []
    force_exit = next(
        fields
        for stage, fields in logs
        if stage == "holding_flow_override_force_exit"
        and fields.get("force_reason") == "no_recent_ticks"
    )
    assert force_exit["ofi_force_exit_phase"] == "source_quality_guard"


def test_parse_fail_force_exit_is_source_quality_guard(monkeypatch):
    logs = []
    _patch_holding_context(monkeypatch, logs)

    class ParseFailAI(DummyFlowAI):
        def evaluate_scalping_holding_flow(self, *args, **kwargs):
            self.calls.append((args, kwargs))
            return {
                "action": "UNKNOWN",
                "score": 0,
                "flow_state": "-",
                "reason": "parse failed",
                "evidence": [],
                "next_review_sec": 45,
                "ai_parse_fail": True,
            }

    ai = ParseFailAI("EXIT")

    proceed = handlers._evaluate_holding_flow_override(
        stock=_stock(),
        code="005930",
        strategy="SCALPING",
        ws_data=_ws(),
        ai_engine=ai,
        exit_rule="scalp_soft_stop_pct",
        sell_reason_type="LOSS",
        reason="soft stop",
        profit_rate=-1.10,
        peak_profit=0.00,
        drawdown=1.10,
        current_ai_score=25,
        held_sec=80,
        curr_price=10000,
        buy_price=10110,
        now_ts=1000.0,
    )

    assert proceed is True
    assert len(ai.calls) == 1
    force_exit = next(
        fields
        for stage, fields in logs
        if stage == "holding_flow_override_force_exit"
        and fields.get("force_reason") == "parse_fail"
    )
    assert force_exit["ofi_force_exit_phase"] == "source_quality_guard"


def test_flow_hold_is_confirmed_exit_by_stable_bearish_ofi_after_worsen(monkeypatch):
    logs = []
    _patch_holding_context(monkeypatch, logs)
    monkeypatch.setattr(
        handlers,
        "_evaluate_holding_flow_ofi_state",
        lambda stock, code, *, curr_price, now_ts=None: (
            {
                "ready": True,
                "micro_state": "bearish",
                "observer_healthy": True,
                "snapshot_age_ms": 100,
            },
            handlers.OfiSmoothingState(
                regime=handlers.OFI_STABLE_BEARISH, micro_score_smooth=-0.62
            ),
        ),
    )
    ai = DummyFlowAI("HOLD")
    stock = {
        **_stock(),
        "holding_flow_override_candidate_key": "scalp_ai_momentum_decay:MOMENTUM_DECAY",
        "holding_flow_override_started_at": 990.0,
        "holding_flow_override_candidate_profit": 0.00,
    }

    proceed = handlers._evaluate_holding_flow_override(
        stock=stock,
        code="005930",
        strategy="SCALPING",
        ws_data=_ws(),
        ai_engine=ai,
        exit_rule="scalp_ai_momentum_decay",
        sell_reason_type="MOMENTUM_DECAY",
        reason="momentum decay",
        profit_rate=-0.31,
        peak_profit=0.30,
        drawdown=0.61,
        current_ai_score=25,
        held_sec=120,
        curr_price=9969,
        buy_price=10000,
        now_ts=1000.0,
    )

    assert proceed is True
    assert any(
        stage == "holding_flow_ofi_smoothing_applied"
        and fields.get("smoothing_action") == "CONFIRM_EXIT"
        for stage, fields in logs
    )
    assert any(
        stage == "holding_flow_override_exit_confirmed"
        and fields.get("confirm_reason") == "ofi_stable_bearish"
        for stage, fields in logs
    )


def test_low_score_flow_hold_is_not_cut_by_score_band(monkeypatch):
    logs = []
    _patch_holding_context(monkeypatch, logs)
    ai = DummyFlowAI("HOLD")

    proceed = handlers._evaluate_holding_flow_override(
        stock=_stock(),
        code="005930",
        strategy="SCALPING",
        ws_data=_ws(),
        ai_engine=ai,
        exit_rule="scalp_ai_momentum_decay",
        sell_reason_type="MOMENTUM_DECAY",
        reason="low score momentum decay",
        profit_rate=0.70,
        peak_profit=1.40,
        drawdown=0.70,
        current_ai_score=18,
        held_sec=140,
        curr_price=10070,
        buy_price=10000,
        now_ts=1000.0,
    )

    assert proceed is False
    assert any(
        fields.get("flow_score") == 18
        for stage, fields in logs
        if stage == "holding_flow_override_defer_exit"
    )


def test_worsen_floor_stops_defer_and_allows_original_exit(monkeypatch):
    logs = []
    _patch_holding_context(monkeypatch, logs)
    ai = DummyFlowAI("HOLD")
    stock = {
        **_stock(),
        "holding_flow_override_candidate_key": "scalp_soft_stop_pct:LOSS",
        "holding_flow_override_started_at": 990.0,
        "holding_flow_override_candidate_profit": 0.00,
    }

    proceed = handlers._evaluate_holding_flow_override(
        stock=stock,
        code="005930",
        strategy="SCALPING",
        ws_data=_ws(),
        ai_engine=ai,
        exit_rule="scalp_soft_stop_pct",
        sell_reason_type="LOSS",
        reason="soft stop",
        profit_rate=-0.81,
        peak_profit=0.00,
        drawdown=0.81,
        current_ai_score=30,
        held_sec=100,
        curr_price=9919,
        buy_price=10000,
        now_ts=1000.0,
    )

    assert proceed is True
    assert ai.calls == []
    force_exit = next(
        fields
        for stage, fields in logs
        if stage == "holding_flow_override_force_exit"
        and fields.get("force_reason") == "worsen_floor"
    )
    assert force_exit["metric_role"] == "safety_veto"
    assert force_exit["decision_authority"] == "holding_flow_override_safety_exit_guard"
    assert force_exit["window_policy"] == "same_day_intraday_events"
    assert force_exit["sample_floor"] == 1
    assert force_exit["primary_decision_metric"] == "source_quality_gate"
    assert (
        force_exit["source_quality_gate"]
        == "holding_flow_override_force_exit_contract_fields_present"
    )
    assert force_exit["runtime_effect"] is True
    assert force_exit["allowed_runtime_apply"] is False
    assert force_exit["actual_order_submitted"] is False
    assert force_exit["threshold_family"] == "holding_flow_override"
    assert force_exit["runtime_family_candidate"] == "holding_flow_override"
    assert "runtime_apply_bridge" in force_exit["forbidden_uses"]


def test_holding_flow_state_change_review_bypasses_interval_once_enabled(monkeypatch):
    logs = []
    _patch_holding_context(monkeypatch, logs)
    monkeypatch.setattr(
        handlers,
        "TRADING_RULES",
        SimpleNamespace(
            HOLDING_FLOW_STATE_CHANGE_REVIEW_ENABLED=True,
            HOLDING_FLOW_STATE_CHANGE_WORSEN_PCT=0.20,
            HOLDING_FLOW_OFI_SMOOTHING_OVERRIDE_ENABLED=False,
        ),
    )
    ai = DummyFlowAI("HOLD")
    stock = {
        **_stock(),
        "holding_flow_override_candidate_key": "scalp_soft_stop_pct:LOSS",
        "holding_flow_override_started_at": 1000.0,
        "holding_flow_override_candidate_profit": 0.50,
        "holding_flow_override_last_review_at": 1000.0,
        "holding_flow_override_last_review_profit": 0.50,
        "holding_flow_override_last_action": "HOLD",
        "holding_flow_override_last_flow_state": "absorption",
        "holding_flow_override_last_score": 74,
    }

    proceed = handlers._evaluate_holding_flow_override(
        stock=stock,
        code="005930",
        strategy="SCALPING",
        ws_data=_ws(),
        ai_engine=ai,
        exit_rule="scalp_soft_stop_pct",
        sell_reason_type="LOSS",
        reason="soft stop",
        profit_rate=0.20,
        peak_profit=0.70,
        drawdown=0.50,
        current_ai_score=55,
        held_sec=80,
        curr_price=10020,
        buy_price=10000,
        now_ts=1010.0,
    )

    assert proceed is False
    assert len(ai.calls) == 1
    assert any(
        stage == "holding_flow_state_change_review_triggered" for stage, _ in logs
    )
    assert any(stage == "holding_flow_override_review" for stage, _ in logs)


def test_holding_flow_state_change_review_is_disabled_by_default(monkeypatch):
    logs = []
    _patch_holding_context(monkeypatch, logs)
    monkeypatch.setattr(
        handlers,
        "TRADING_RULES",
        SimpleNamespace(
            HOLDING_FLOW_STATE_CHANGE_REVIEW_ENABLED=False,
            HOLDING_FLOW_OFI_SMOOTHING_OVERRIDE_ENABLED=False,
        ),
    )
    ai = DummyFlowAI("HOLD")
    stock = {
        **_stock(),
        "holding_flow_override_candidate_key": "scalp_soft_stop_pct:LOSS",
        "holding_flow_override_started_at": 1000.0,
        "holding_flow_override_candidate_profit": 0.50,
        "holding_flow_override_last_review_at": 1000.0,
        "holding_flow_override_last_review_profit": 0.50,
        "holding_flow_override_last_action": "HOLD",
        "holding_flow_override_last_flow_state": "absorption",
        "holding_flow_override_last_score": 74,
        "holding_flow_override_last_reason": "prior hold",
    }

    proceed = handlers._evaluate_holding_flow_override(
        stock=stock,
        code="005930",
        strategy="SCALPING",
        ws_data=_ws(),
        ai_engine=ai,
        exit_rule="scalp_soft_stop_pct",
        sell_reason_type="LOSS",
        reason="soft stop",
        profit_rate=0.20,
        peak_profit=0.70,
        drawdown=0.50,
        current_ai_score=55,
        held_sec=80,
        curr_price=10020,
        buy_price=10000,
        now_ts=1010.0,
    )

    assert proceed is False
    assert ai.calls == []
    assert any(stage == "holding_flow_override_defer_exit" for stage, _ in logs)
    assert not any(
        stage == "holding_flow_state_change_review_triggered" for stage, _ in logs
    )


def test_review_price_trigger_bypasses_min_interval_reuse(monkeypatch):
    logs = []
    _patch_holding_context(monkeypatch, logs)
    monkeypatch.setattr(
        handlers,
        "TRADING_RULES",
        SimpleNamespace(
            HOLDING_FLOW_OFI_SMOOTHING_OVERRIDE_ENABLED=False,
            HOLDING_FLOW_STATE_CHANGE_REVIEW_ENABLED=False,
            HOLDING_FLOW_REVIEW_MIN_INTERVAL_SEC=30,
            HOLDING_FLOW_REVIEW_MAX_INTERVAL_SEC=90,
            HOLDING_FLOW_REVIEW_PRICE_TRIGGER_PCT=0.35,
        ),
    )
    ai = DummyFlowAI("HOLD")
    stock = {
        **_stock(),
        "holding_flow_override_candidate_key": "scalp_soft_stop_pct:LOSS",
        "holding_flow_override_started_at": 1000.0,
        "holding_flow_override_candidate_profit": 0.50,
        "holding_flow_override_last_review_at": 1000.0,
        "holding_flow_override_last_review_profit": 0.50,
        "holding_flow_override_last_action": "HOLD",
        "holding_flow_override_last_flow_state": "absorption",
        "holding_flow_override_last_score": 74,
        "holding_flow_override_last_reason": "prior hold",
    }

    proceed = handlers._evaluate_holding_flow_override(
        stock=stock,
        code="005930",
        strategy="SCALPING",
        ws_data=_ws(),
        ai_engine=ai,
        exit_rule="scalp_soft_stop_pct",
        sell_reason_type="LOSS",
        reason="soft stop",
        profit_rate=0.10,
        peak_profit=0.70,
        drawdown=0.60,
        current_ai_score=55,
        held_sec=80,
        curr_price=10010,
        buy_price=10000,
        now_ts=1010.0,
    )

    assert proceed is False
    assert len(ai.calls) == 1
    assert any(stage == "holding_flow_override_review" for stage, _ in logs)
    assert not any(
        stage == "holding_flow_override_defer_exit"
        and fields.get("flow_reason") == "prior hold"
        for stage, fields in logs
    )


def test_trailing_peak_worsen_floor_allows_original_exit_without_flow_review(
    monkeypatch,
):
    logs = []
    _patch_holding_context(monkeypatch, logs)
    ai = DummyFlowAI("HOLD")
    stock = {
        **_stock(),
        "holding_flow_override_candidate_key": "scalp_trailing_take_profit:TRAILING",
        "holding_flow_override_started_at": 1000.0,
        "holding_flow_override_candidate_profit": 1.07,
        "holding_flow_override_last_review_at": 1000.0,
        "holding_flow_override_last_review_profit": 1.07,
        "holding_flow_override_last_action": "HOLD",
        "holding_flow_override_last_flow_state": "quiet",
        "holding_flow_override_last_score": 50,
        "holding_flow_override_last_reason": "flow remains balanced",
    }

    proceed = handlers._evaluate_holding_flow_override(
        stock=stock,
        code="000500",
        strategy="SCALPING",
        ws_data=_ws(),
        ai_engine=ai,
        exit_rule="scalp_trailing_take_profit",
        sell_reason_type="TRAILING",
        reason="고점 대비 밀림",
        profit_rate=15.57,
        peak_profit=17.08,
        drawdown=1.51,
        current_ai_score=60,
        held_sec=240,
        curr_price=267000,
        buy_price=230500,
        now_ts=1010.0,
    )

    assert proceed is True
    assert ai.calls == []
    force_exit = next(
        fields
        for stage, fields in logs
        if stage == "holding_flow_override_force_exit"
        and fields.get("force_reason") == "trailing_peak_worsen_floor"
    )
    assert force_exit["trailing_peak_worsen"] == "1.51"
    assert force_exit["trailing_force_worsen_pct"] == "0.40"
    assert force_exit["decision_authority"] == "holding_flow_override_safety_exit_guard"


def test_trailing_continuation_recheck_defers_only_fresh_supportive_shallow_profit(
    monkeypatch,
):
    logs = []
    _patch_holding_context(monkeypatch, logs)
    _enable_trailing_continuation_recheck(monkeypatch)
    micro_fields = _trailing_continuation_micro_fields()
    monkeypatch.setattr(
        handlers,
        "_scalping_micro_estimator_log_fields",
        lambda **kwargs: dict(micro_fields),
    )
    now_ts = datetime(
        2026, 7, 15, 10, 0, tzinfo=timezone(timedelta(hours=9))
    ).timestamp()
    stock = {
        **_stock(),
        "last_reversal_features": _fresh_reversal_features(),
    }
    ws_data = {**_ws(), "last_ws_update_ts": now_ts - 0.1}
    ai = DummyFlowAI("HOLD")

    proceed = handlers._evaluate_holding_flow_override(
        stock=stock,
        code="002990",
        strategy="SCALPING",
        ws_data=ws_data,
        ai_engine=ai,
        exit_rule="scalp_trailing_take_profit",
        sell_reason_type="TRAILING",
        reason="trailing pullback",
        profit_rate=0.13,
        peak_profit=0.83,
        drawdown=0.70,
        current_ai_score=71,
        held_sec=120,
        curr_price=13000,
        buy_price=12953,
        now_ts=now_ts,
    )

    assert proceed is False
    assert ai.calls == []
    assert stock["scalp_trailing_continuation_recheck_until_epoch"] == now_ts + 15
    assert any(
        stage == "scalp_trailing_continuation_recheck"
        and fields["recheck_state"] == "armed"
        and fields["composite_micro_supported"] is True
        for stage, fields in logs
    )

    proceed_after_ttl = handlers._evaluate_holding_flow_override(
        stock=stock,
        code="002990",
        strategy="SCALPING",
        ws_data={**ws_data, "last_ws_update_ts": now_ts + 15.9},
        ai_engine=ai,
        exit_rule="scalp_trailing_take_profit",
        sell_reason_type="TRAILING",
        reason="trailing pullback",
        profit_rate=0.13,
        peak_profit=0.83,
        drawdown=0.70,
        current_ai_score=71,
        held_sec=136,
        curr_price=13000,
        buy_price=12953,
        now_ts=now_ts + 16,
    )

    assert proceed_after_ttl is True
    assert "scalp_trailing_continuation_recheck_started_at" not in stock
    assert any(
        stage == "scalp_trailing_continuation_recheck"
        and fields["recheck_state"] == "ttl_expired"
        for stage, fields in logs
    )
    assert any(
        stage == "holding_flow_override_force_exit"
        and fields.get("force_reason") == "trailing_peak_worsen_floor"
        for stage, fields in logs
    )


def test_trailing_continuation_recheck_fails_closed_without_fresh_signed_tape_features(
    monkeypatch,
):
    logs = []
    _patch_holding_context(monkeypatch, logs)
    _enable_trailing_continuation_recheck(monkeypatch)
    monkeypatch.setattr(
        handlers,
        "_scalping_micro_estimator_log_fields",
        lambda **kwargs: _trailing_continuation_micro_fields(),
    )
    now_ts = datetime(
        2026, 7, 15, 10, 0, tzinfo=timezone(timedelta(hours=9))
    ).timestamp()
    stock = _stock()
    ai = DummyFlowAI("HOLD")

    proceed = handlers._evaluate_holding_flow_override(
        stock=stock,
        code="002990",
        strategy="SCALPING",
        ws_data={**_ws(), "last_ws_update_ts": now_ts - 0.1},
        ai_engine=ai,
        exit_rule="scalp_trailing_take_profit",
        sell_reason_type="TRAILING",
        reason="trailing pullback",
        profit_rate=0.13,
        peak_profit=0.83,
        drawdown=0.70,
        current_ai_score=71,
        held_sec=120,
        curr_price=13000,
        buy_price=12953,
        now_ts=now_ts,
    )

    assert proceed is True
    assert "scalp_trailing_continuation_recheck_started_at" not in stock
    assert not any(stage == "scalp_trailing_continuation_recheck" for stage, _ in logs)
    assert any(
        stage == "holding_flow_override_force_exit"
        and fields.get("force_reason") == "trailing_peak_worsen_floor"
        for stage, fields in logs
    )


def test_trailing_continuation_recheck_rejects_rest_or_feature_only_micro_provenance(
    monkeypatch,
):
    logs = []
    _patch_holding_context(monkeypatch, logs)
    _enable_trailing_continuation_recheck(monkeypatch)
    micro_fields = {
        **_trailing_continuation_micro_fields(),
        "holding_flow_micro_estimator_source_state": "rest_orderbook_delta_estimate",
    }
    monkeypatch.setattr(
        handlers,
        "_scalping_micro_estimator_log_fields",
        lambda **kwargs: micro_fields,
    )
    now_ts = datetime(
        2026, 7, 15, 10, 0, tzinfo=timezone(timedelta(hours=9))
    ).timestamp()
    stock = {**_stock(), "last_reversal_features": _fresh_reversal_features()}

    proceed = handlers._evaluate_holding_flow_override(
        stock=stock,
        code="002990",
        strategy="SCALPING",
        ws_data={**_ws(), "last_ws_update_ts": now_ts - 0.1},
        ai_engine=DummyFlowAI("HOLD"),
        exit_rule="scalp_trailing_take_profit",
        sell_reason_type="TRAILING",
        reason="trailing pullback",
        profit_rate=0.13,
        peak_profit=0.83,
        drawdown=0.70,
        current_ai_score=71,
        held_sec=120,
        curr_price=13000,
        buy_price=12953,
        now_ts=now_ts,
    )

    assert proceed is True
    assert "scalp_trailing_continuation_recheck_started_at" not in stock
    assert not any(stage == "scalp_trailing_continuation_recheck" for stage, _ in logs)


def test_trailing_continuation_recheck_clamps_negative_min_profit_to_positive_floor(
    monkeypatch,
):
    _enable_trailing_continuation_recheck(monkeypatch)
    monkeypatch.setenv(
        "KORSTOCKSCAN_SCALP_TRAILING_CONTINUATION_RECHECK_MIN_PROFIT_PCT", "-1"
    )
    now_ts = datetime(
        2026, 7, 15, 10, 0, tzinfo=timezone(timedelta(hours=9))
    ).timestamp()

    config = handlers._scalp_trailing_continuation_recheck_config(now_ts)

    assert config["active"] is True
    assert config["min_profit_pct"] == 0.01


def test_trailing_continuation_recheck_is_cleared_when_holding_candidate_changes(
    monkeypatch,
):
    logs = []
    _patch_holding_context(monkeypatch, logs)
    monkeypatch.setattr(
        handlers,
        "_scalping_micro_estimator_log_fields",
        lambda **kwargs: _trailing_continuation_micro_fields(),
    )
    stock = {
        **_stock(),
        "holding_flow_override_candidate_key": "scalp_trailing_take_profit:TRAILING",
        "holding_flow_override_started_at": 1000.0,
        "holding_flow_override_candidate_profit": 0.13,
        "scalp_trailing_continuation_recheck_started_at": 1000.0,
        "scalp_trailing_continuation_recheck_until_epoch": 1015.0,
        "scalp_trailing_continuation_recheck_anchor_profit": 0.13,
        "scalp_trailing_continuation_recheck_min_profit": 0.10,
    }

    handlers._evaluate_holding_flow_override(
        stock=stock,
        code="002990",
        strategy="SCALPING",
        ws_data={**_ws(), "last_ws_update_ts": 1001.0},
        ai_engine=DummyFlowAI("HOLD"),
        exit_rule="scalp_soft_stop_pct",
        sell_reason_type="LOSS",
        reason="soft stop",
        profit_rate=0.13,
        peak_profit=0.83,
        drawdown=0.70,
        current_ai_score=71,
        held_sec=120,
        curr_price=13000,
        buy_price=12953,
        now_ts=1001.0,
    )

    assert stock["holding_flow_override_candidate_key"] == "scalp_soft_stop_pct:LOSS"
    assert "scalp_trailing_continuation_recheck_started_at" not in stock
    assert "scalp_trailing_continuation_recheck_until_epoch" not in stock


def test_hard_stop_is_outside_holding_flow_override_scope():
    assert (
        handlers._holding_flow_override_applicable("SCALPING", "scalp_hard_stop_pct")
        is False
    )


def test_exit_decision_source_marks_holding_flow_override_when_candidate_exists():
    stock = {
        "strategy": "SCALPING",
        "holding_flow_override_candidate_key": "scalp_soft_stop_pct:LOSS",
        "holding_flow_override_last_review_at": 1000.0,
    }

    assert (
        handlers._resolve_exit_decision_source(
            stock=stock,
            exit_rule="scalp_soft_stop_pct",
            reason="soft stop",
        )
        == "HOLDING_FLOW_OVERRIDE"
    )


def test_overnight_sell_today_flow_hold_flips_to_hold_overnight(monkeypatch):
    logs = []
    monkeypatch.setattr(
        overnight.kiwoom_utils,
        "get_tick_history_ka10003",
        lambda token, code, limit=30: [{"price": 10000, "volume": 10, "side": "BUY"}],
    )
    monkeypatch.setattr(
        overnight.kiwoom_utils,
        "get_minute_candles_ka10080",
        lambda token, code, limit=60: [
            {"close": 10000, "high": 10050, "low": 9950, "volume": 1000}
        ],
    )
    monkeypatch.setattr(
        overnight,
        "_log_holding_pipeline",
        lambda name, code, stage, **fields: logs.append((stage, fields)),
    )
    ai = DummyFlowAI("HOLD")
    record = SimpleNamespace(
        id=1,
        stock_code="005930",
        stock_name="삼성전자",
        status="HOLDING",
        buy_qty=1,
        buy_price=10000,
    )
    mem_stock = {"name": "삼성전자", "buy_qty": 1}

    decision = overnight._apply_overnight_flow_override(
        record,
        mem_stock,
        {"curr": 10000, "v_pw": 130, "buy_ratio": 60},
        {"avg_price": 10000, "curr_price": 10000, "pnl_pct": 0.0, "score": 45},
        {"action": "SELL_TODAY", "confidence": 35, "reason": "overnight sell"},
        ai,
    )

    assert decision["action"] == "HOLD_OVERNIGHT"
    assert mem_stock["overnight_flow_override_hold"] is True
    assert mem_stock["overnight_flow_override_candidate_profit"] == 0.0
    assert any(stage == "overnight_flow_override_hold" for stage, _ in logs)


def test_overnight_sell_today_flow_trim_keeps_sell_today(monkeypatch):
    logs = []
    monkeypatch.setattr(
        overnight.kiwoom_utils,
        "get_tick_history_ka10003",
        lambda token, code, limit=30: [{"price": 10000, "volume": 10, "side": "SELL"}],
    )
    monkeypatch.setattr(
        overnight.kiwoom_utils,
        "get_minute_candles_ka10080",
        lambda token, code, limit=60: [
            {"close": 9950, "high": 10050, "low": 9900, "volume": 1000}
        ],
    )
    monkeypatch.setattr(
        overnight,
        "_log_holding_pipeline",
        lambda name, code, stage, **fields: logs.append((stage, fields)),
    )
    ai = DummyFlowAI("TRIM")
    record = SimpleNamespace(
        id=1,
        stock_code="005930",
        stock_name="삼성전자",
        status="HOLDING",
        buy_qty=1,
        buy_price=10000,
    )
    mem_stock = {"name": "삼성전자", "buy_qty": 1}

    decision = overnight._apply_overnight_flow_override(
        record,
        mem_stock,
        {"curr": 9900, "v_pw": 95, "buy_ratio": 45},
        {"avg_price": 10000, "curr_price": 9900, "pnl_pct": -1.0, "score": 42},
        {"action": "SELL_TODAY", "confidence": 35, "reason": "overnight sell"},
        ai,
    )

    assert decision["action"] == "SELL_TODAY"
    assert "overnight_flow_override_hold" not in mem_stock
    assert any(
        stage == "overnight_flow_override_exit_confirmed"
        and fields.get("flow_action") == "TRIM"
        and fields.get("force_reason") == "flow_trim_unsupported"
        for stage, fields in logs
    )


def test_overnight_flow_hold_reverts_between_1520_and_1530_on_worsen_floor():
    stock = {
        "overnight_flow_override_hold": True,
        "overnight_flow_override_candidate_profit": 0.10,
        "overnight_flow_override_worsen_pct": 0.80,
    }

    assert (
        handlers._should_revert_overnight_flow_override_hold(
            stock, -0.70, dt_time(15, 25)
        )
        is True
    )
    assert (
        handlers._should_revert_overnight_flow_override_hold(
            stock, -0.69, dt_time(15, 25)
        )
        is False
    )
    assert (
        handlers._should_revert_overnight_flow_override_hold(
            stock, -0.80, dt_time(15, 30)
        )
        is False
    )
