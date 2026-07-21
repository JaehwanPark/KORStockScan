from datetime import datetime
import inspect
from types import SimpleNamespace

import pytest

from src.engine.scalping.opening_rotation import (
    EntryConfig,
    ExitConfig,
    POSITION_TAG,
    WINDOW_VERSION,
    entry_time_bucket,
    entry_time_bucket_labels,
    entry_window_version,
    evaluate_entry,
    evaluate_exit,
    is_watch_candidate,
    is_watch_source_scope,
)
from src.engine import sniper_state_handlers as handlers
from src.engine import sniper_execution_receipts
from src.engine import sniper_sync
from src.engine.scalping import opening_rotation_backtest as rotation_backtest


def _packet(price: int) -> dict:
    return {
        "curr_price": price,
        "quote_stale": False,
        "quote_age_ms": 120.0,
        "quote_stale_threshold_ms": 3000.0,
        "tick_context_stale": False,
        "tick_context_quality": "fresh_computed",
        "tick_aggressor_pressure_usable": True,
        "spread_bp": 8.0,
        "buy_pressure_10t": 64.0,
        "tick_aggressor_trusted_count": 8,
        "tick_acceleration_ratio": 1.35,
        "price_change_10t_pct": 0.12,
        "volume_ratio_pct": 125.0,
        "micro_vwap_available": True,
        "curr_vs_micro_vwap_bp": 24.0,
        "microstructure_reaction_ask_sweep_score": 72,
        "microstructure_reaction_post_sweep_hold_score": 67,
        "microstructure_reaction_bid_replenishment_score": 61,
        "microstructure_reaction_wall_replenishment_risk_score": 42,
        "microstructure_reaction_vi_proximity_risk": 18,
    }


def test_watch_source_scope_does_not_promote_missing_day_change():
    config = EntryConfig()
    now_dt = datetime(2026, 7, 21, 9, 20)

    assert is_watch_source_scope(
        position_tag="SCANNER",
        source_signature="PRICE_JUMP_START,VOLUME_SURGE_POSITIVE",
        now_dt=now_dt,
        config=config,
    )
    assert not is_watch_source_scope(
        position_tag="SCANNER",
        source_signature="LOW_REBOUND_RISING_MISSED,PRICE_JUMP_START",
        now_dt=now_dt,
        config=config,
    )


def test_opening_rotation_upstream_block_records_unknown_day_change(monkeypatch):
    emitted = []
    stock = {
        "id": 41,
        "name": "테스트",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "source_signature": "PRICE_JUMP_START,VOLUME_SURGE_POSITIVE",
    }
    monkeypatch.setattr(
        handlers,
        "_log_entry_pipeline",
        lambda *args, **fields: emitted.append((args[2], fields)),
    )

    logged = handlers._maybe_log_opening_rotation_upstream_blocked(
        stock,
        "005930",
        skip_reason="ws_snapshot_missing_or_zero",
        now_ts=datetime(2026, 7, 21, 9, 20).timestamp(),
        ws_data={},
    )

    assert logged is True
    stage, fields = emitted[-1]
    assert stage == "opening_rotation_1pct_upstream_blocked"
    assert fields["opening_rotation_upstream_source_scope"] is True
    assert fields["opening_rotation_upstream_exact_candidate_known"] is False
    assert fields["opening_rotation_upstream_exact_candidate"] is False
    assert fields["freshness_envelope_attempted"] is False
    assert fields["actual_order_submitted"] is False
    assert fields["broker_order_forbidden"] is True


def test_opening_rotation_upstream_scope_hydrates_scanner_source(monkeypatch):
    stock = {
        "id": 42,
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
    }
    monkeypatch.setattr(
        handlers,
        "_scanner_promotion_correlation_fields",
        lambda target: {"source_signature": "PRICE_JUMP_START,VOLUME_SURGE_POSITIVE"},
    )

    fields = handlers._opening_rotation_upstream_scope_fields(
        stock,
        {"fluctuation": 3.2},
        now_ts=datetime(2026, 7, 21, 9, 20).timestamp(),
    )

    assert fields["opening_rotation_upstream_source_scope"] is True
    assert fields["opening_rotation_upstream_exact_candidate"] is True


def test_direct_opening_position_is_not_reclassified_by_rising_marker():
    fields = handlers._opening_rotation_upstream_scope_fields(
        {
            "strategy": "SCALPING",
            "position_tag": "OPENING_ROTATION_1PCT",
            "source_signature": "LOW_REBOUND_RISING_MISSED",
        },
        {"fluctuation": 3.2},
        now_ts=datetime(2026, 7, 21, 9, 20).timestamp(),
    )

    assert fields["opening_rotation_upstream_owner_conflict"] is False
    assert fields["opening_rotation_upstream_exact_candidate"] is True


def test_opening_rotation_upstream_handoff_requires_fresh_trusted_ws_tape(
    monkeypatch,
):
    stock = {
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "source_signature": "PRICE_JUMP_START,VOLUME_SURGE_POSITIVE",
    }
    ws_data = {
        "curr": 10_000,
        "fluctuation": 3.2,
        "quote_stale": True,
    }
    monkeypatch.setattr(
        handlers,
        "extract_scalping_feature_packet",
        lambda *args, **kwargs: _packet(10_000),
    )

    allowed = handlers._opening_rotation_upstream_handoff_fields(
        stock,
        ws_data,
        now_ts=datetime(2026, 7, 21, 9, 20).timestamp(),
    )
    assert allowed["opening_rotation_upstream_handoff_allowed"] is True
    assert allowed["opening_rotation_upstream_trusted_tick_count"] == 8

    monkeypatch.setattr(
        handlers,
        "extract_scalping_feature_packet",
        lambda *args, **kwargs: {
            **_packet(10_000),
            "tick_context_stale": True,
        },
    )
    blocked = handlers._opening_rotation_upstream_handoff_fields(
        stock,
        ws_data,
        now_ts=datetime(2026, 7, 21, 9, 20).timestamp(),
    )
    assert blocked["opening_rotation_upstream_handoff_allowed"] is False
    assert (
        blocked["opening_rotation_upstream_handoff_reason"]
        == "fresh_trusted_ws_tape_missing"
    )


def test_opening_rotation_bounded_handoff_can_pass_scanner_stale_backoff(
    monkeypatch,
):
    stock = {
        "id": 42,
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "source_signature": "PRICE_JUMP_START",
        "added_time": 900.0,
    }
    ws_data = {
        "curr": 10_000,
        "fluctuation": 3.2,
        "last_ws_update_ts": 900.0,
    }
    handoff_fields = {
        "opening_rotation_upstream_handoff_allowed": True,
        "opening_rotation_upstream_handoff_reason": (
            "fresh_trusted_ws_tape_to_quote_envelope"
        ),
    }
    monkeypatch.setattr(
        handlers,
        "_opening_rotation_upstream_handoff_fields",
        lambda *args, **kwargs: handoff_fields,
    )
    monkeypatch.setattr(
        handlers,
        "_scanner_ws_stale_backoff_fields",
        lambda *args, **kwargs: {"scanner_ws_stale_backoff_active": True},
    )
    monkeypatch.setattr(
        handlers,
        "_scanner_ws_stale_backoff_strong_promotion_recheck",
        lambda *args, **kwargs: False,
    )
    monkeypatch.setattr(
        handlers,
        "_rising_missed_candidate_gate_backoff_fields",
        lambda *args, **kwargs: {},
    )
    monkeypatch.setattr(
        handlers,
        "_rising_missed_submit_safety_backoff_fields",
        lambda *args, **kwargs: {},
    )
    monkeypatch.setattr(
        handlers,
        "_rising_missed_signed_tape_scanner_backoff_fields",
        lambda *args, **kwargs: {},
    )

    fields = handlers._scanner_fast_precheck_fields(
        stock,
        now_ts=1000.0,
        code="005930",
        ws_data=ws_data,
    )

    assert fields["fast_precheck_result"] == "eligible_for_heavy_entry_eval"
    assert (
        fields["fast_precheck_reason"]
        == "opening_rotation_fresh_tape_quote_envelope_handoff"
    )
    assert fields["opening_rotation_upstream_handoff_allowed"] is True


def test_entry_collects_then_qualifies_on_pullback_reacceleration():
    config = EntryConfig()
    collecting = evaluate_entry(
        previous_state=None,
        feature_packet=_packet(10_000),
        source_signature="PRICE_JUMP_START,VOLUME_SURGE_POSITIVE",
        day_change_pct=3.2,
        intraday_high_price=10_100,
        now_dt=datetime(2026, 7, 20, 9, 9, 0),
        config=config,
    )
    assert collecting["qualified"] is False
    assert collecting["reason"] == "collecting_before_entry_window"
    assert collecting["state"]["pullback_seen"] is True

    qualified = evaluate_entry(
        previous_state=collecting["state"],
        feature_packet=_packet(10_020),
        source_signature="PRICE_JUMP_START,VOLUME_SURGE_POSITIVE",
        day_change_pct=3.4,
        intraday_high_price=10_100,
        now_dt=datetime(2026, 7, 20, 9, 10, 1),
        config=config,
    )
    assert qualified["qualified"] is True
    assert qualified["position_tag"] == POSITION_TAG
    assert qualified["budget_ratio"] == pytest.approx(0.10)
    assert qualified["ai_score_hard_gate"] is False


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("quote_age_ms", "-", "quote_freshness_unavailable"),
        ("quote_stale", True, "stale_market_context"),
        ("spread_bp", 16.0, "spread_too_wide"),
        ("buy_pressure_10t", 57.9, "buy_pressure_below_min"),
        ("tick_acceleration_ratio", 1.14, "tick_acceleration_below_min"),
        (
            "microstructure_reaction_wall_replenishment_risk_score",
            70,
            "wall_replenishment_risk",
        ),
    ],
)
def test_entry_blocks_adverse_or_low_quality_micro_context(field, value, reason):
    packet = _packet(10_020)
    packet[field] = value
    decision = evaluate_entry(
        previous_state={
            "peak_price": 10_100,
            "last_price": 10_000,
            "pullback_seen": True,
        },
        feature_packet=packet,
        source_signature="REALTIME_RANK_START,BID_IMBALANCE_SURGE",
        day_change_pct=4.0,
        intraday_high_price=10_100,
        now_dt=datetime(2026, 7, 20, 9, 20, 0),
    )
    assert decision["qualified"] is False
    assert decision["reason"] == reason


def test_stale_packet_does_not_mutate_pullback_state_or_enable_next_entry():
    stale_packet = _packet(10_000)
    stale_packet.update(
        {
            "quote_stale": True,
            "quote_age_ms": 5_000.0,
            "tick_context_stale": True,
        }
    )
    stale = evaluate_entry(
        previous_state=None,
        feature_packet=stale_packet,
        source_signature="PRICE_JUMP_START",
        day_change_pct=3.0,
        intraday_high_price=10_100,
        now_dt=datetime(2026, 7, 20, 9, 10, 0),
    )
    assert stale["reason"] == "stale_market_context"
    assert stale["state"] == {}

    fresh = evaluate_entry(
        previous_state=stale["state"],
        feature_packet=_packet(10_020),
        source_signature="PRICE_JUMP_START",
        day_change_pct=3.0,
        intraday_high_price=10_100,
        now_dt=datetime(2026, 7, 20, 9, 10, 1),
    )
    assert fresh["qualified"] is False
    assert fresh["reason"] == "reacceleration_not_observed"


def test_qualified_entry_exposes_freshness_contract_fields():
    decision = evaluate_entry(
        previous_state={
            "peak_price": 10_100,
            "last_price": 10_000,
            "pullback_seen": True,
        },
        feature_packet=_packet(10_020),
        source_signature="PRICE_JUMP_START",
        day_change_pct=3.0,
        intraday_high_price=10_100,
        now_dt=datetime(2026, 7, 20, 9, 10, 1),
    )
    assert decision["qualified"] is True
    assert decision["quote_stale"] is False
    assert decision["tick_context_stale"] is False
    assert decision["tick_context_quality"] == "fresh_computed"
    assert decision["tick_aggressor_pressure_usable"] is True
    assert decision["micro_vwap_available"] is True


def test_entry_window_remains_open_until_1500_but_not_after():
    config = EntryConfig()
    assert is_watch_candidate(
        position_tag="SCANNER",
        source_signature="PRICE_JUMP_START",
        day_change_pct=2.0,
        now_dt=datetime(2026, 7, 20, 14, 59, 59),
        config=config,
    )
    assert not is_watch_candidate(
        position_tag="SCANNER",
        source_signature="PRICE_JUMP_START",
        day_change_pct=2.0,
        now_dt=datetime(2026, 7, 20, 15, 0, 1),
        config=config,
    )


def test_rising_missed_source_overlap_is_not_an_opening_rotation_candidate():
    source_signature = (
        "LOW_REBOUND_RISING_MISSED,PRICE_JUMP_START,VOLUME_SURGE_POSITIVE"
    )
    assert not is_watch_candidate(
        position_tag="SCANNER",
        source_signature=source_signature,
        day_change_pct=3.0,
        now_dt=datetime(2026, 7, 20, 9, 20),
        config=EntryConfig(),
    )
    decision = evaluate_entry(
        previous_state=None,
        feature_packet=_packet(10_020),
        source_signature=source_signature,
        day_change_pct=3.0,
        intraday_high_price=10_100,
        now_dt=datetime(2026, 7, 20, 9, 20),
    )
    assert decision["qualified"] is False
    assert decision["reason"] == "entry_owner_rising_missed_scout"


def test_negative_rising_missed_source_token_does_not_take_entry_ownership():
    stock = {
        "position_tag": "SCANNER",
        "source_signature": (
            "NO_LOW_REBOUND_RISING_MISSED,PRICE_JUMP_START,VOLUME_SURGE_POSITIVE"
        ),
    }
    assert handlers._has_rising_missed_watch_source_marker(stock) is False
    assert (
        handlers._opening_rotation_yields_to_rising_missed_owner(
            stock, {"pos_tag": "SCANNER"}
        )
        is False
    )
    assert is_watch_candidate(
        position_tag="SCANNER",
        source_signature=stock["source_signature"],
        day_change_pct=3.0,
        now_dt=datetime(2026, 7, 20, 9, 20),
        config=EntryConfig(),
    )


def test_zero_rising_missed_diagnostics_do_not_take_opening_ownership():
    stock = {
        "position_tag": "SCANNER",
        "source_signature": "PRICE_JUMP_START,VOLUME_SURGE_POSITIVE",
        "low_rebound_pct": 0.0,
        "LowReboundPct": "0.0",
        "rising_entry_relief_eligible": False,
        "rising_missed_buy": "False",
        "_scanner_rising_entry_relief_reason": "not_applicable_rising_entry_relief",
    }

    assert handlers._has_rising_missed_watch_source_marker(stock) is True
    assert (
        handlers._opening_rotation_rising_missed_owner_reason(
            stock, {"pos_tag": "SCANNER"}
        )
        == ""
    )
    assert (
        handlers._opening_rotation_yields_to_rising_missed_owner(
            stock, {"pos_tag": "SCANNER"}
        )
        is False
    )


def test_rising_recheck_hints_do_not_take_opening_ownership():
    stock = {
        "position_tag": "SCANNER",
        "source_signature": "PRICE_JUMP_START,VOLUME_SURGE_POSITIVE",
        "low_rebound_pct": 0.4,
        "rising_entry_relief_eligible": True,
        "_scanner_rising_entry_relief_reason": "reversal_up_watch_recheck_pending",
    }

    assert (
        handlers._opening_rotation_rising_missed_owner_reason(
            stock, {"pos_tag": "SCANNER"}
        )
        == ""
    )


@pytest.mark.parametrize(
    ("field", "value", "expected_reason"),
    [
        (
            "source_signature",
            "LOW_REBOUND_RISING_MISSED,PRICE_JUMP_START",
            "low_rebound_rising_missed_source",
        ),
        ("rising_missed_buy", True, "rising_missed_buy"),
        ("rising_missed_lineage", "normal_buy_bridge", "rising_missed_lineage"),
    ],
)
def test_affirmative_rising_missed_marker_keeps_entry_ownership(
    field, value, expected_reason
):
    stock = {
        "position_tag": "SCANNER",
        "source_signature": "PRICE_JUMP_START",
        field: value,
    }

    assert (
        handlers._opening_rotation_rising_missed_owner_reason(
            stock, {"pos_tag": "SCANNER"}
        )
        == expected_reason
    )
    assert handlers._opening_rotation_yields_to_rising_missed_owner(
        stock, {"pos_tag": "SCANNER"}
    )


def test_runtime_entry_cutoff_defaults_to_1500(monkeypatch):
    monkeypatch.delenv("KORSTOCKSCAN_OPENING_ROTATION_1PCT_ENTRY_END", raising=False)
    assert handlers._opening_rotation_entry_config().entry_end.hour == 15
    assert handlers._opening_rotation_entry_config().entry_end.minute == 0


def test_entry_time_cohorts_are_clock_aligned_and_include_1500_boundary():
    assert entry_window_version() == WINDOW_VERSION
    assert entry_time_bucket(datetime(2026, 7, 20, 9, 10)) == "09:00-09:30"
    assert entry_time_bucket(datetime(2026, 7, 20, 9, 30)) == "09:30-10:00"
    assert entry_time_bucket(datetime(2026, 7, 20, 14, 59, 59)) == "14:30-15:00"
    assert entry_time_bucket(datetime(2026, 7, 20, 15, 0)) == "14:30-15:00"
    assert entry_time_bucket(datetime(2026, 7, 20, 15, 0, 1)) == "outside_entry_window"
    labels = entry_time_bucket_labels()
    assert labels[0] == "09:00-09:30"
    assert labels[-1] == "14:30-15:00"
    assert len(labels) == 12


def test_runtime_entry_cutoff_is_preopen_configurable(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_OPENING_ROTATION_1PCT_ENTRY_END", "10:45")
    config = handlers._opening_rotation_entry_config()
    assert config.entry_end.hour == 10
    assert config.entry_end.minute == 45
    assert entry_window_version(config) == "opening_rotation_0910_1045_custom"


def _fresh_ws_envelope(now_ts=1000.0):
    return {
        "curr": 10_000,
        "best_ask": 10_010,
        "best_bid": 9_990,
        "last_ws_update_ts": now_ts - 0.1,
    }


def _rest_envelope(now_ts=1000.0):
    return {
        "market_data_freshness_state": "rest_enriched",
        "market_data_orderbook_state": "rest_enriched",
        "market_data_effective_price_source": "ka10004_rest_orderbook",
        "market_data_effective_quote_age_ms": 100.0,
        "market_data_effective_age_basis": "absolute_timestamp:rest_received_ts",
        "market_data_effective_best_ask": 10_010,
        "market_data_effective_best_bid": 9_990,
        "curr": 10_000,
        "best_ask": 10_010,
        "best_bid": 9_990,
        "quote_age_ms": 100.0,
        "quote_stale": False,
    }


def test_opening_rotation_fresh_ws_envelope_skips_rest(monkeypatch):
    monkeypatch.setattr(
        handlers,
        "_fetch_rest_orderbook_snapshot_bounded",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("fresh WS must not trigger REST")
        ),
    )

    enriched, fields = handlers._resolve_opening_rotation_freshness_envelope(
        {},
        "005930",
        _fresh_ws_envelope(),
        now_ts=1000.0,
    )

    assert fields["opening_rotation_freshness_envelope_ready"] is True
    assert fields["market_data_freshness_state"] == "fresh_ws"
    assert fields["opening_rotation_freshness_envelope_selected_source"] == "current_ws"
    assert enriched["quote_stale"] is False


def test_opening_rotation_uses_recent_scanner_rest_envelope_for_stale_ws(
    monkeypatch,
):
    cached = _rest_envelope()
    stock = {
        "_scanner_market_data_enrichment_ws_data": cached,
        "_scanner_market_data_enrichment_fields": {
            key: value
            for key, value in cached.items()
            if key.startswith("market_data_")
        },
        "_scanner_market_data_enrichment_stored_at": 999.8,
    }
    monkeypatch.setattr(
        handlers,
        "_fetch_rest_orderbook_snapshot_bounded",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("scanner envelope cache must be reused")
        ),
    )

    enriched, fields = handlers._resolve_opening_rotation_freshness_envelope(
        stock,
        "005930",
        {
            "curr": 9_900,
            "best_ask": 9_910,
            "best_bid": 9_890,
            "last_ws_update_ts": 990.0,
            "quote_stale": True,
        },
        now_ts=1000.0,
    )

    assert fields["opening_rotation_freshness_envelope_ready"] is True
    assert fields["market_data_freshness_state"] == "rest_enriched"
    assert (
        fields["opening_rotation_freshness_envelope_selected_source"]
        == "scanner_envelope_cache"
    )
    assert enriched["quote_age_ms"] == pytest.approx(300.0)


def test_opening_rotation_expired_scanner_rest_envelope_stays_blocked(monkeypatch):
    cached = _rest_envelope()
    stock = {
        "_scanner_market_data_enrichment_ws_data": cached,
        "_scanner_market_data_enrichment_fields": {
            key: value
            for key, value in cached.items()
            if key.startswith("market_data_")
        },
        "_scanner_market_data_enrichment_stored_at": 998.5,
    }
    monkeypatch.setattr(handlers, "KIWOOM_TOKEN", None)

    enriched, fields = handlers._resolve_opening_rotation_freshness_envelope(
        stock,
        "005930",
        {
            "curr": 9_900,
            "best_ask": 9_910,
            "best_bid": 9_890,
            "last_ws_update_ts": 990.0,
            "quote_stale": True,
        },
        now_ts=1000.0,
    )

    assert fields["opening_rotation_freshness_envelope_ready"] is False
    assert fields["market_data_freshness_state"] == "stale"
    assert fields["opening_rotation_freshness_envelope_rest_budget_reason"] == (
        "kiwoom_token_missing"
    )
    assert enriched["quote_stale"] is True


def test_opening_rotation_stale_ws_uses_bounded_rest_quote_only(monkeypatch):
    handlers._OPENING_ROTATION_FRESHNESS_RATE_EPOCHS.clear()
    monkeypatch.setattr(handlers, "KIWOOM_TOKEN", "token")
    monkeypatch.setattr(
        handlers,
        "_fetch_rest_orderbook_snapshot_bounded",
        lambda code, timeout_ms: (
            {
                "source": "ka10004_rest_orderbook",
                "curr": 10_000,
                "best_ask": 10_010,
                "best_bid": 9_990,
                "rest_received_ts": 999.9,
            },
            "ok",
            12.5,
        ),
    )

    enriched, fields = handlers._resolve_opening_rotation_freshness_envelope(
        {},
        "005930",
        {
            "curr": 9_900,
            "best_ask": 9_910,
            "best_bid": 9_890,
            "last_ws_update_ts": 990.0,
            "quote_stale": True,
        },
        now_ts=1000.0,
    )

    assert fields["opening_rotation_freshness_envelope_ready"] is True
    assert fields["market_data_freshness_state"] == "rest_enriched"
    assert fields["opening_rotation_freshness_envelope_rest_attempted"] is True
    assert enriched["curr"] == 10_000
    assert enriched["quote_stale"] is False
    assert "rest_signed_trade_ticks" not in enriched


def test_opening_rotation_unknown_quote_time_basis_remains_blocked(monkeypatch):
    monkeypatch.setattr(handlers, "KIWOOM_TOKEN", None)

    enriched, fields = handlers._resolve_opening_rotation_freshness_envelope(
        {},
        "005930",
        {
            "curr": 10_000,
            "best_ask": 10_010,
            "best_bid": 9_990,
            "quote_age_ms": 10.0,
        },
        now_ts=1000.0,
    )

    assert fields["opening_rotation_freshness_envelope_ready"] is False
    assert fields["opening_rotation_freshness_envelope_rest_budget_reason"] == (
        "kiwoom_token_missing"
    )
    assert enriched["quote_stale"] is True


def test_opening_rotation_recent_conflict_overrides_fresh_ws(monkeypatch):
    conflicted = {
        **_rest_envelope(),
        "market_data_freshness_state": "conflicted",
        "market_data_orderbook_state": "conflicted",
        "market_data_effective_price_source": "ws_rest_conflicted",
    }
    stock = {
        "_scanner_market_data_enrichment_ws_data": conflicted,
        "_scanner_market_data_enrichment_fields": {
            key: value
            for key, value in conflicted.items()
            if key.startswith("market_data_")
        },
        "_scanner_market_data_enrichment_stored_at": 999.9,
    }
    monkeypatch.setattr(
        handlers,
        "_fetch_rest_orderbook_snapshot_bounded",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("active conflict must fail closed without another REST call")
        ),
    )

    enriched, fields = handlers._resolve_opening_rotation_freshness_envelope(
        stock,
        "005930",
        _fresh_ws_envelope(),
        now_ts=1000.0,
    )

    assert fields["opening_rotation_freshness_envelope_ready"] is False
    assert fields["market_data_freshness_state"] == "conflicted"
    assert enriched["quote_stale"] is True


def test_opening_rotation_feature_packet_uses_effective_envelope(monkeypatch):
    captured = {}
    effective_ws = _rest_envelope()
    freshness_fields = {
        **{
            key: value
            for key, value in effective_ws.items()
            if key.startswith("market_data_")
        },
        "opening_rotation_freshness_envelope_ready": True,
        "opening_rotation_freshness_envelope_selected_source": (
            "scanner_envelope_cache"
        ),
    }
    monkeypatch.setattr(
        handlers,
        "_resolve_opening_rotation_freshness_envelope",
        lambda *args, **kwargs: (effective_ws, freshness_fields),
    )
    monkeypatch.setattr(
        handlers.kiwoom_utils,
        "get_tick_history_ka10003",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("ka10003 heuristic tape must not support opening entry")
        ),
    )
    monkeypatch.setattr(
        handlers.kiwoom_utils,
        "get_minute_candles_ka10080",
        lambda *args, **kwargs: [],
    )

    def _extract(ws_data, recent_ticks, recent_candles, *, now):
        captured["ws_data"] = ws_data
        return {"quote_age_ms": 9999.0, "quote_stale": True}

    monkeypatch.setattr(handlers, "extract_scalping_feature_packet", _extract)
    handlers._OPENING_ROTATION_CONTEXT_CACHE.clear()

    packet = handlers._opening_rotation_feature_packet(
        {},
        "005930",
        {"curr": 9_900, "quote_stale": True},
        now_ts=1000.0,
        now_dt=datetime(2026, 7, 20, 9, 20),
    )

    assert captured["ws_data"]["curr"] == 10_000
    assert packet["quote_stale"] is False
    assert packet["quote_age_ms"] == pytest.approx(100.0)
    assert packet["quote_age_source"] == "opening_rotation_freshness_envelope"
    assert packet["market_data_effective_price_source"] == ("ka10004_rest_orderbook")


def test_stale_entry_decision_preserves_envelope_provenance():
    packet = _packet(10_000)
    packet.update(
        {
            "quote_stale": True,
            "market_data_freshness_state": "conflicted",
            "market_data_effective_price_source": "ws_rest_conflicted",
            "opening_rotation_freshness_envelope_ready": False,
            "opening_rotation_freshness_envelope_selected_source": (
                "scanner_envelope_cache"
            ),
        }
    )

    decision = evaluate_entry(
        previous_state=None,
        feature_packet=packet,
        source_signature="PRICE_JUMP_START",
        day_change_pct=3.0,
        intraday_high_price=10_100,
        now_dt=datetime(2026, 7, 20, 9, 20),
    )

    assert decision["reason"] == "stale_market_context"
    assert decision["market_data_freshness_state"] == "conflicted"
    assert decision["market_data_effective_price_source"] == "ws_rest_conflicted"
    assert decision["opening_rotation_freshness_envelope_ready"] is False


def test_entry_contract_has_no_ai_score_input():
    assert "ai_score" not in inspect.signature(evaluate_entry).parameters


@pytest.mark.parametrize(
    ("profit_rate", "held_sec", "exit_rule"),
    [
        (1.0, 40, "opening_rotation_1pct_take_profit"),
        (-0.5, 20, "opening_rotation_tight_stop"),
        (0.1, 300, "opening_rotation_stagnation_exit"),
        (0.4, 600, "opening_rotation_max_hold_exit"),
    ],
)
def test_exit_policy_is_cost_aware_and_deterministic(profit_rate, held_sec, exit_rule):
    decision = evaluate_exit(
        profit_rate=profit_rate,
        held_sec=held_sec,
        config=ExitConfig(),
    )
    assert decision["should_exit"] is True
    assert decision["exit_rule"] == exit_rule
    assert decision["ai_score_hard_gate"] is False


def test_exit_policy_holds_active_position_after_entry_cutoff():
    decision = evaluate_exit(profit_rate=0.45, held_sec=240)
    assert decision["should_exit"] is False
    assert decision["reason"] == "hold"


def test_runtime_branch_uses_mechanical_authority_without_pre_submit_retag(
    monkeypatch,
):
    stock = {
        "id": 7,
        "name": "테스트",
        "position_tag": "SCANNER",
        "source_signature": "PRICE_JUMP_START,VOLUME_SURGE_POSITIVE",
        "intraday_high_price": 10_100,
        "opening_rotation_1pct_state": {
            "peak_price": 10_100,
            "last_price": 10_000,
            "pullback_seen": True,
        },
    }
    runtime = {
        "pos_tag": "SCANNER",
        "now_ts": datetime(2026, 7, 20, 9, 20).timestamp(),
        "now_dt": datetime(2026, 7, 20, 9, 20),
        "fluctuation": 3.5,
        "curr_price": 10_020,
        "is_trigger": False,
    }
    ws_data = {
        "curr": 10_020,
        "fluctuation": 3.5,
        "ask_tot": 80_000,
        "bid_tot": 90_000,
    }
    monkeypatch.setattr(
        handlers,
        "_opening_rotation_feature_packet",
        lambda *args, **kwargs: _packet(10_020),
    )
    entry_logs = []
    monkeypatch.setattr(
        handlers,
        "_log_entry_pipeline",
        lambda *args, **kwargs: entry_logs.append((args, kwargs)),
    )

    handled = handlers._handle_watching_opening_rotation(
        stock,
        "005930",
        ws_data,
        runtime,
        {"MIN_SCALP_LIQUIDITY": 500_000_000},
    )

    assert handled is True
    assert runtime["is_trigger"] is True
    assert runtime["pos_tag"] == POSITION_TAG
    assert runtime["current_ai_score"] == 0.0
    assert runtime["opening_rotation_mechanical_signal_strength"] == pytest.approx(0.8)
    assert runtime["opening_rotation_window_version"] == WINDOW_VERSION
    assert runtime["opening_rotation_decision_time_bucket"] == "09:00-09:30"
    assert stock["position_tag"] == "SCANNER"
    assert stock["opening_rotation_window_version"] == WINDOW_VERSION
    assert stock["opening_rotation_decision_time_bucket"] == "09:00-09:30"
    assert "scale_in_locked" not in stock
    assert "opening_rotation_1pct_live" not in stock
    qualified_log = next(
        fields
        for args, fields in entry_logs
        if args[2] == "opening_rotation_1pct_qualified"
    )
    _, replay = rotation_backtest._canonical_replay_inputs(qualified_log)
    assert replay["missing"] == ()
    assert qualified_log["opening_rotation_window_version"] == WINDOW_VERSION
    assert qualified_log["opening_rotation_decision_time_bucket"] == "09:00-09:30"


def test_full_watching_branch_never_calls_ai_for_rotation_candidate(monkeypatch):
    stock = {
        "id": 8,
        "name": "테스트",
        "position_tag": "SCANNER",
        "source_signature": "REALTIME_RANK_START,BID_IMBALANCE_SURGE",
        "intraday_high_price": 10_100,
        "opening_rotation_1pct_state": {
            "peak_price": 10_100,
            "last_price": 10_000,
            "pullback_seen": True,
        },
    }
    runtime = {
        "strategy": "SCALPING",
        "pos_tag": "SCANNER",
        "now_ts": datetime(2026, 7, 20, 9, 20).timestamp(),
        "now_dt": datetime(2026, 7, 20, 9, 20),
        "curr_price": 10_020,
        "current_vpw": 125.0,
        "fluctuation": 3.5,
        "cooldowns": {},
        "event_bus": None,
        "is_trigger": False,
        "msg": "",
        "ratio": 0.10,
        "liquidity_value": None,
        "current_ai_score": 99.0,
        "ai_prob": 0.99,
        "buy_threshold": 70,
        "strong_vpw": 120,
    }
    ws_data = {
        "curr": 10_020,
        "fluctuation": 3.5,
        "ask_tot": 80_000,
        "bid_tot": 90_000,
    }
    monkeypatch.setattr(
        handlers,
        "_opening_rotation_feature_packet",
        lambda *args, **kwargs: _packet(10_020),
    )
    monkeypatch.setattr(handlers, "_log_entry_pipeline", lambda *args, **kwargs: None)

    class _ForbiddenAI:
        def __getattr__(self, name):
            raise AssertionError(f"AI access is prohibited: {name}")

    handled = handlers._handle_watching_strategy_branch(
        stock,
        "005930",
        ws_data,
        radar=None,
        ai_engine=_ForbiddenAI(),
        runtime=runtime,
        config={"MIN_SCALP_LIQUIDITY": 500_000_000},
    )
    assert handled is True
    assert runtime["is_trigger"] is True
    assert runtime["current_ai_score"] == 0.0


def test_broker_submit_activation_commits_rotation_tag_and_scale_in_lock():
    stock = {
        "position_tag": "SCANNER",
        "opening_rotation_1pct_state": {"phase": "QUALIFIED"},
    }
    handlers._OPENING_ROTATION_CONTEXT_CACHE["005930"] = {"cached_at": 1.0}

    handlers._activate_opening_rotation_after_broker_submit(stock, "005930")

    assert stock["position_tag"] == POSITION_TAG
    assert stock["scale_in_locked"] is True
    assert stock["opening_rotation_1pct_live"] is True
    assert "005930" not in handlers._OPENING_ROTATION_CONTEXT_CACHE


def test_opening_rotation_first_buy_fill_persists_entry_time_cohort(monkeypatch):
    events = []

    class _NoopThread:
        def __init__(self, *args, **kwargs):
            pass

        def start(self):
            return None

    monkeypatch.setattr(sniper_execution_receipts.threading, "Thread", _NoopThread)
    monkeypatch.setattr(
        sniper_execution_receipts,
        "_log_holding_pipeline",
        lambda name, code, target_id, stage, **fields: events.append((stage, fields)),
    )
    sniper_execution_receipts.highest_prices = {}
    stock = {
        "id": 7,
        "name": "테스트",
        "code": "005930",
        "strategy": "SCALPING",
        "position_tag": POSITION_TAG,
        "opening_rotation_window_version": WINDOW_VERSION,
        "pending_entry_orders": [
            {
                "ord_no": "ROT1",
                "qty": 2,
                "filled_qty": 0,
                "price": 10_000,
                "status": "OPEN",
            }
        ],
        "entry_requested_qty": 2,
        "requested_buy_qty": 2,
    }

    sniper_execution_receipts._handle_entry_buy_execution(
        target_id=7,
        target_stock=stock,
        code="005930",
        order_no="ROT1",
        exec_price=10_000,
        exec_qty=1,
        now=datetime(2026, 7, 20, 13, 29, 59),
    )

    assert stock["opening_rotation_entry_time_bucket"] == "13:00-13:30"

    sniper_execution_receipts._handle_entry_buy_execution(
        target_id=7,
        target_stock=stock,
        code="005930",
        order_no="ROT1",
        exec_price=10_010,
        exec_qty=1,
        now=datetime(2026, 7, 20, 13, 30, 1),
    )

    assert stock["opening_rotation_entry_time_bucket"] == "13:00-13:30"
    holding_started = [fields for stage, fields in events if stage == "holding_started"]
    assert holding_started[-1]["opening_rotation_entry_time_bucket"] == "13:00-13:30"
    assert holding_started[-1]["opening_rotation_window_version"] == WINDOW_VERSION


def test_rotation_tag_activation_is_strictly_after_broker_acceptance():
    watch_source = inspect.getsource(handlers._handle_watching_opening_rotation)
    submit_source = inspect.getsource(handlers._submit_watching_triggered_entry)

    assert "_activate_opening_rotation_after_broker_submit" not in watch_source
    send_index = submit_source.index("kiwoom_orders.send_buy_order(")
    reject_guard_index = submit_source.index('if rt_cd != "0":', send_index)
    activate_index = submit_source.index(
        "_activate_opening_rotation_after_broker_submit", reject_guard_index
    )
    stage_index = submit_source.index("_stage_buy_order_submission(", activate_index)
    assert send_index < reject_guard_index < activate_index < stage_index


def test_opening_rotation_scope_skips_preceding_rising_missed_hook(monkeypatch):
    handlers.COOLDOWNS = {}
    handlers.ALERTED_STOCKS = set()
    handlers.EVENT_BUS = None
    monkeypatch.setattr(
        handlers, "_observe_entry_cancel_wait_counterfactuals", lambda *a, **k: None
    )
    monkeypatch.setattr(handlers, "_log_watching_state_debug", lambda *a, **k: None)
    monkeypatch.setattr(
        handlers, "_manual_control_exclusion_blocked", lambda *a, **k: False
    )
    monkeypatch.setattr(handlers, "is_buy_side_paused", lambda: False)
    monkeypatch.setattr(handlers, "is_scalping_buy_time_allowed", lambda value: True)
    monkeypatch.setattr(
        handlers,
        "evaluate_scalp_same_symbol_loss_reentry_guard",
        lambda *a, **k: {"allowed": True},
    )
    monkeypatch.setattr(
        handlers, "_maybe_emit_entry_ai_price_skip_followup", lambda *a, **k: None
    )
    monkeypatch.setattr(
        handlers,
        "_maybe_submit_rising_missed_one_share_entry",
        lambda *a, **k: (_ for _ in ()).throw(
            AssertionError("rising_missed hook must not run")
        ),
    )
    branch_calls = []
    monkeypatch.setattr(
        handlers,
        "_handle_watching_strategy_branch",
        lambda *a, **k: branch_calls.append((a, k)) or False,
    )
    stock = {
        "id": 9,
        "code": "005930",
        "name": "테스트",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "source_signature": "PRICE_JUMP_START,VOLUME_SURGE_POSITIVE",
        "rising_missed_class": "not_rising_missed",
    }

    assert handlers._has_rising_missed_watch_source_marker(stock) is True
    assert (
        handlers._opening_rotation_yields_to_rising_missed_owner(
            stock, {"pos_tag": "SCANNER"}
        )
        is False
    )

    handlers.handle_watching_state(
        stock,
        "005930",
        {"curr": 10_000, "fluctuation": 3.0},
        admin_id=1,
        now_ts=datetime(2026, 7, 20, 9, 20).timestamp(),
        now_dt=datetime(2026, 7, 20, 9, 20),
        radar=None,
        ai_engine=None,
    )
    assert branch_calls


def test_rising_missed_overlap_keeps_scout_hook_ownership(monkeypatch):
    handlers.COOLDOWNS = {}
    handlers.ALERTED_STOCKS = set()
    handlers.EVENT_BUS = None
    monkeypatch.setattr(
        handlers, "_observe_entry_cancel_wait_counterfactuals", lambda *a, **k: None
    )
    monkeypatch.setattr(handlers, "_log_watching_state_debug", lambda *a, **k: None)
    monkeypatch.setattr(
        handlers, "_manual_control_exclusion_blocked", lambda *a, **k: False
    )
    monkeypatch.setattr(handlers, "is_buy_side_paused", lambda: False)
    monkeypatch.setattr(handlers, "is_scalping_buy_time_allowed", lambda value: True)
    monkeypatch.setattr(
        handlers,
        "evaluate_scalp_same_symbol_loss_reentry_guard",
        lambda *a, **k: {"allowed": True},
    )
    monkeypatch.setattr(
        handlers, "_maybe_emit_entry_ai_price_skip_followup", lambda *a, **k: None
    )
    scout_calls = []
    monkeypatch.setattr(
        handlers,
        "_maybe_submit_rising_missed_one_share_entry",
        lambda *a, **k: scout_calls.append((a, k)) or True,
    )
    monkeypatch.setattr(
        handlers,
        "_handle_watching_strategy_branch",
        lambda *a, **k: (_ for _ in ()).throw(
            AssertionError("opening/generic branch must not preempt rising missed")
        ),
    )
    stock = {
        "id": 10,
        "code": "005930",
        "name": "테스트",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "source_signature": (
            "LOW_REBOUND_RISING_MISSED,PRICE_JUMP_START,VOLUME_SURGE_POSITIVE"
        ),
    }

    handlers.handle_watching_state(
        stock,
        "005930",
        {"curr": 10_000, "fluctuation": 3.0},
        admin_id=1,
        now_ts=datetime(2026, 7, 20, 9, 20).timestamp(),
        now_dt=datetime(2026, 7, 20, 9, 20),
        radar=None,
        ai_engine=None,
    )

    assert len(scout_calls) == 1


def test_explicit_rising_missed_class_keeps_rising_missed_entry_ownership():
    stock = {
        "position_tag": "SCANNER",
        "source_signature": "PRICE_JUMP_START,VOLUME_SURGE_POSITIVE",
        "rising_missed_class": "rising_missed_raw",
    }

    assert (
        handlers._opening_rotation_yields_to_rising_missed_owner(
            stock, {"pos_tag": "SCANNER"}
        )
        is True
    )


def test_rising_missed_scout_upgrade_cannot_be_retagged_as_rotation(monkeypatch):
    stock = {
        "id": 11,
        "name": "테스트",
        "status": "HOLDING",
        "position_tag": "SCANNER",
        "source_signature": "PRICE_JUMP_START,VOLUME_SURGE_POSITIVE",
        "rising_missed_one_share_scout": True,
        "opening_rotation_1pct_state": {"phase": "PULLBACK_OBSERVED"},
        "opening_rotation_mechanical_signal_strength": 0.8,
    }
    runtime = {
        "pos_tag": "SCANNER",
        "now_ts": datetime(2026, 7, 20, 9, 20).timestamp(),
        "now_dt": datetime(2026, 7, 20, 9, 20),
        "fluctuation": 3.0,
        "curr_price": 10_000,
        "is_trigger": False,
        "scout_upgrade_entry": True,
    }
    handlers._OPENING_ROTATION_CONTEXT_CACHE["005930"] = {"cached_at": 1.0}
    monkeypatch.setattr(
        handlers,
        "_opening_rotation_feature_packet",
        lambda *a, **k: (_ for _ in ()).throw(
            AssertionError("opening feature path must not run for scout upgrade")
        ),
    )
    monkeypatch.setattr(handlers, "_log_entry_pipeline", lambda *a, **k: None)

    handled = handlers._handle_watching_opening_rotation(
        stock,
        "005930",
        {"curr": 10_000, "fluctuation": 3.0},
        runtime,
        {"MIN_SCALP_LIQUIDITY": 500_000_000},
    )

    assert handled is False
    assert runtime["is_trigger"] is False
    assert stock["position_tag"] == "SCANNER"
    assert "opening_rotation_1pct_state" not in stock
    assert "opening_rotation_mechanical_signal_strength" not in stock
    assert "005930" not in handlers._OPENING_ROTATION_CONTEXT_CACHE


def test_runtime_branch_does_not_fall_back_to_ai_after_1500_entry_window():
    stock = {
        "id": 7,
        "name": "테스트",
        "position_tag": POSITION_TAG,
        "source_signature": "PRICE_JUMP_START",
    }
    runtime = {
        "pos_tag": POSITION_TAG,
        "now_ts": datetime(2026, 7, 20, 15, 1).timestamp(),
        "now_dt": datetime(2026, 7, 20, 15, 1),
        "fluctuation": 3.5,
        "curr_price": 10_000,
        "is_trigger": False,
    }
    handlers._OPENING_ROTATION_CONTEXT_CACHE["005930"] = {"cached_at": 1.0}
    handled = handlers._handle_watching_opening_rotation(
        stock,
        "005930",
        {"curr": 10_000, "fluctuation": 3.5},
        runtime,
        {"MIN_SCALP_LIQUIDITY": 500_000_000},
    )
    assert handled is True
    assert runtime["is_trigger"] is False
    assert "005930" not in handlers._OPENING_ROTATION_CONTEXT_CACHE


def test_account_sync_does_not_attach_legacy_preset_exit_to_rotation_tag(monkeypatch):
    class _DB:
        get_session_calls = 0

        @staticmethod
        def get_latest_marcap(code):
            return 0

        @classmethod
        def get_session(cls):
            cls.get_session_calls += 1
            raise RuntimeError("scale-in history lookup was not expected")

    record = SimpleNamespace(
        id=11,
        stock_code="005930",
        stock_name="테스트",
        strategy="SCALPING",
        trade_type="SCALP",
        position_tag=POSITION_TAG,
        buy_qty=3,
        buy_price=10_000,
        buy_time=datetime(2026, 7, 20, 9, 20),
        scale_in_locked=True,
    )
    sniper_sync.DB = _DB()
    sniper_sync.ACTIVE_TARGETS = []
    sniper_sync.EVENT_BUS = None
    monkeypatch.setattr(sniper_sync, "_recover_order_refs_from_logs", lambda code: {})

    target = sniper_sync._ensure_runtime_target(record)

    assert target["position_tag"] == POSITION_TAG
    assert target["scale_in_locked"] is True
    assert "exit_mode" not in target
    assert _DB.get_session_calls == 0

    existing = dict(target)
    existing["exit_mode"] = "SCALP_PRESET_TP"
    sniper_sync.ACTIVE_TARGETS = [existing]
    refreshed = sniper_sync._ensure_runtime_target(record)
    assert _DB.get_session_calls == 0
    assert "exit_mode" not in refreshed


def test_execution_receipt_does_not_seed_ai_score_for_rotation_tag():
    stock = {
        "strategy": "SCALPING",
        "position_tag": POSITION_TAG,
        "entry_submit_ai_score": 99,
        "pending_entry_orders": [{"ord_no": "123", "ai_score": 88}],
    }
    assert (
        sniper_execution_receipts._resolve_entry_submit_ai_score(stock, "123") is None
    )
