import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from src.engine.monitoring import entry_turn_point_replay as mod
from src.engine.monitoring import rising_missed_intraday_feedback as feedback
from src.engine import sniper_state_handlers as handlers

KST = timezone(timedelta(hours=9))


def _observation(epoch: float, bid: float, ask: float) -> dict:
    return {
        "observed_at": datetime.fromtimestamp(epoch, tz=KST).isoformat(),
        "observed_epoch": epoch,
        "event_epoch": epoch,
        "best_bid": bid,
        "best_ask": ask,
        "spread_bps": (ask - bid) / ask * 10_000.0,
        "quote_age_ms": 0.0,
        "source": "market_data_effective_bbo",
        "source_provenance": "ws",
        "stage": "fixture_bbo",
        "stock_code": "000001",
        "venue": "KRX",
        "market_session_bucket": "krx_regular",
        "scanner_promotion_id": "PROM-1",
    }


def _event(
    stage: str,
    when: datetime,
    *,
    bid: float | None = None,
    ask: float | None = None,
    evaluation_id: str = "eval-1",
) -> dict:
    fields = {
        "effective_venue": "KRX",
        "market_session_bucket": "krx_regular",
        "scanner_promotion_id": "PROM-1",
    }
    if bid is not None and ask is not None:
        fields.update(
            {
                "market_data_effective_best_bid": bid,
                "market_data_effective_best_ask": ask,
                "market_data_effective_quote_age_ms": 0.0,
                "market_data_effective_quote_observed_epoch": when.timestamp(),
                "market_data_effective_price_source": "ws",
            }
        )
    if stage == "rising_missed_tp1_counterfactual_submit_safety":
        fields.update(
            {
                "rising_missed_tp1_evaluation_id": evaluation_id,
                "rising_missed_tp1_candidate_lane": "acceleration",
                "selector_reason": "rising_missed_tp1_insufficient_positive_support",
            }
        )
    return {
        "stage": stage,
        "stock_code": "000001",
        "stock_name": "fixture",
        "emitted_at": when.isoformat(),
        "fields": fields,
    }


class _VerifiedCommonMaster:
    def lookup(self, symbol, *, as_of):
        assert symbol == "000001"
        assert as_of.isoformat() == "2026-09-02"
        return SimpleNamespace(
            status=SimpleNamespace(value="verified"),
            economic_metadata_allowed=True,
            record=SimpleNamespace(
                instrument_type=SimpleNamespace(value="EQUITY"),
                listing_market=SimpleNamespace(value="KOSPI"),
            ),
        )


class _VerifiedEtfMaster(_VerifiedCommonMaster):
    def lookup(self, symbol, *, as_of):
        result = super().lookup(symbol, as_of=as_of)
        result.record.instrument_type.value = "ETF"
        return result


def test_explicit_symbol_master_path_requires_nonfuture_dated_filename(tmp_path):
    undated = tmp_path / "symbol_master.json"
    future = tmp_path / "micro_reversion_symbol_master_2026-09-03.json"

    undated_master, undated_binding = mod.load_verified_symbol_master(
        "2026-09-02", symbol_master_path=undated
    )
    future_master, future_binding = mod.load_verified_symbol_master(
        "2026-09-02", symbol_master_path=future
    )

    assert undated_master is None
    assert undated_binding["error"] == ("symbol_master_source_date_missing_or_invalid")
    assert future_master is None
    assert future_binding["error"] == "symbol_master_source_date_after_target_date"


def test_venue_conflict_or_sor_provenance_fails_closed():
    assert (
        mod._venue(
            {
                "rising_missed_effective_venue": "KRX",
                "effective_venue": "KRX",
                "venue": "KRX",
                "venue_resolution": "conflicting_explicit:venue",
            }
        )
        == "UNKNOWN"
    )
    assert (
        mod._venue(
            {
                "rising_missed_effective_venue": "KRX",
                "effective_venue": "SOR",
            }
        )
        == "UNKNOWN"
    )


def test_turn_profile_detects_pause_then_causal_momentum_confirmation():
    base = datetime(2026, 9, 2, 9, 0, tzinfo=KST).timestamp()
    history = [
        _observation(base, 99.9, 100.0),
        _observation(base + 5, 100.0, 100.1),
        _observation(base + 10, 100.1, 100.2),
        _observation(base + 15, 100.3, 100.4),
    ]

    profile, evidence = mod._turn_profile(history)

    assert profile == "momentum_turn_entry"
    assert evidence["executable_confirmation_move_pct"] > 0.1
    assert evidence["reason"] == ("pause_then_two_sample_executable_bid_acceleration")


def test_turn_profile_detects_drawdown_low_then_rebound_confirmation():
    base = datetime(2026, 9, 2, 9, 0, tzinfo=KST).timestamp()
    history = [
        _observation(base, 100.0, 100.1),
        _observation(base + 5, 99.7, 99.8),
        _observation(base + 10, 99.4, 99.5),
        _observation(base + 15, 99.5, 99.6),
        _observation(base + 20, 99.7, 99.8),
    ]

    profile, evidence = mod._turn_profile(history)

    assert profile == "rebound_turn_entry"
    assert evidence["prior_drawdown_pct"] <= -0.3
    assert evidence["recovery_from_low_pct"] >= 0.15


def test_turn_profile_never_uses_a_peak_that_occurred_after_the_low():
    base = datetime(2026, 9, 2, 9, 0, tzinfo=KST).timestamp()
    history = [
        _observation(base, 99.0, 99.1),
        _observation(base + 5, 99.4, 99.5),
        _observation(base + 10, 100.0, 100.1),
        _observation(base + 15, 99.6, 99.7),
        _observation(base + 20, 99.8, 99.9),
    ]

    profile, _evidence = mod._turn_profile(history)

    assert profile != "rebound_turn_entry"


def test_turn_profile_still_checks_momentum_when_rebound_has_no_prior_peak():
    base = datetime(2026, 9, 2, 9, 0, tzinfo=KST).timestamp()
    history = [
        _observation(base, 99.8, 99.9),
        _observation(base + 5, 99.9, 100.0),
        _observation(base + 10, 100.0, 100.1),
        _observation(base + 15, 100.1, 100.2),
        _observation(base + 20, 100.3, 100.4),
    ]

    profile, evidence = mod._turn_profile(history)

    assert profile == "momentum_turn_entry"
    assert evidence["reason"] == "pause_then_two_sample_executable_bid_acceleration"


def test_rebound_never_uses_a_peak_before_an_internal_bbo_gap():
    base = datetime(2026, 9, 2, 9, 0, tzinfo=KST).timestamp()
    history = [
        _observation(base, 100.0, 100.1),
        _observation(base + 100, 99.4, 99.5),
        _observation(base + 105, 99.5, 99.6),
        _observation(base + 110, 99.55, 99.65),
        _observation(base + 115, 99.6, 99.7),
        _observation(base + 120, 99.7, 99.8),
    ]

    profile, _evidence = mod._turn_profile(history)

    assert profile != "rebound_turn_entry"


def test_causal_bucket_treats_cost_negative_timeout_as_uneconomic():
    candidate = {
        "candidate_epoch": 100.0,
        "current_outcome_source_quality_status": "pass",
    }
    turn = {
        "trigger_epoch": 90.0,
        "entry_spread_bps": 10.0,
        "profile": "momentum_turn_entry",
    }

    bucket = mod._causal_bucket(
        candidate=candidate,
        turn=turn,
        milestones={},
        primary_outcome={"label": "timeout_exit", "cost_adjusted_return_pct": -0.1},
    )

    assert bucket == "uneconomic_spread_or_fill"


def test_replay_uses_exact_ws_bbo_costs_and_attributes_discovery_lag():
    start = datetime(2026, 9, 2, 9, 0, tzinfo=KST)
    events = [
        _event("fixture_bbo", start, bid=99.9, ask=100.0),
        _event("fixture_bbo", start + timedelta(seconds=5), bid=100.0, ask=100.1),
        _event("fixture_bbo", start + timedelta(seconds=10), bid=100.1, ask=100.2),
        _event("fixture_bbo", start + timedelta(seconds=15), bid=100.3, ask=100.4),
        _event("scalping_scanner_candidate_promoted", start + timedelta(seconds=18)),
        _event(
            "rising_missed_tp1_counterfactual_submit_safety",
            start + timedelta(seconds=20),
            bid=100.3,
            ask=100.4,
        ),
        _event("fixture_bbo", start + timedelta(seconds=25), bid=101.0, ask=101.1),
    ]

    report = mod.build_entry_turn_point_replay(
        events,
        target_date="2026-09-02",
        current_label_rows=[
            {
                "evaluation_id": "eval-1",
                "gross_first_hit_label": "gross_target_first",
                "entry_executable_best_ask": 100.4,
                "entry_executable_bbo_state": "pass",
                "first_hit_price_source": "market_data_effective_bbo:best_bid",
            }
        ],
        observation_watermark=start + timedelta(minutes=21),
        symbol_master=_VerifiedCommonMaster(),
        symbol_master_binding={"status": "verified", "artifact_sha256": "a" * 64},
    )

    row = report["rows"][0]
    assert row["turn"]["profile"] == "momentum_turn_entry"
    assert row["turn_lag_vs_candidate_sec"] == -5.0
    assert row["causal_bucket"] == "discovery_late"
    assert row["primary_outcome"]["label"] == "target_first"
    assert row["primary_outcome"]["cost_adjusted_return_pct"] > 0
    assert report["comparison_cost_contract"]["round_trip_cost_bps"] == 23.0
    assert report["exact_ws_bbo_join_coverage_pct"] == 100.0
    assert report["pre_anchor_bbo_coverage_pct"] == 100.0
    assert report["acceptance"]["all_floors_met"] is False
    assert report["runtime_effect"] is False
    assert report["allowed_runtime_apply"] is False
    assert report["promotion_allowed"] is False


def test_replay_counts_repeated_evaluations_as_one_promotion_scope():
    start = datetime(2026, 9, 2, 9, 0, tzinfo=KST)
    events = [
        _event("fixture_bbo", start, bid=99.9, ask=100.0),
        _event("fixture_bbo", start + timedelta(seconds=5), bid=100.0, ask=100.1),
        _event("fixture_bbo", start + timedelta(seconds=10), bid=100.1, ask=100.2),
        _event("fixture_bbo", start + timedelta(seconds=15), bid=100.3, ask=100.4),
        _event(
            "rising_missed_tp1_counterfactual_submit_safety",
            start + timedelta(seconds=20),
            bid=100.3,
            ask=100.4,
            evaluation_id="eval-first",
        ),
        _event(
            "rising_missed_tp1_counterfactual_submit_safety",
            start + timedelta(seconds=25),
            bid=100.4,
            ask=100.5,
            evaluation_id="eval-repeat",
        ),
        _event("fixture_bbo", start + timedelta(seconds=30), bid=101.0, ask=101.1),
    ]

    report = mod.build_entry_turn_point_replay(
        events,
        target_date="2026-09-02",
        current_label_rows=[],
        observation_watermark=start + timedelta(minutes=21),
        symbol_master=_VerifiedCommonMaster(),
        symbol_master_binding={"status": "verified", "artifact_sha256": "a" * 64},
    )

    assert report["candidate_evaluation_count"] == 2
    assert report["candidate_count"] == 1
    assert report["candidate_unit"] == "scanner_promotion_symbol_venue_session"
    assert report["rows"][0]["evaluation_id"] == "eval-first"
    assert report["profile_counts"] == {"momentum_turn_entry": 1}


def test_future_turn_keeps_its_full_forward_outcome_horizon():
    start = datetime(2026, 9, 2, 9, 0, tzinfo=KST)
    events = [
        _event(
            "rising_missed_tp1_counterfactual_submit_safety",
            start,
            bid=100.0,
            ask=100.1,
        ),
        _event("fixture_bbo", start + timedelta(seconds=90), bid=99.9, ask=100.0),
        _event("fixture_bbo", start + timedelta(seconds=95), bid=100.0, ask=100.1),
        _event("fixture_bbo", start + timedelta(seconds=100), bid=100.1, ask=100.2),
        _event("fixture_bbo", start + timedelta(seconds=105), bid=100.3, ask=100.4),
        _event("fixture_bbo", start + timedelta(seconds=1250), bid=101.0, ask=101.1),
    ]

    report = mod.build_entry_turn_point_replay(
        events,
        target_date="2026-09-02",
        current_label_rows=[],
        observation_watermark=start + timedelta(seconds=1400),
        symbol_master=_VerifiedCommonMaster(),
        symbol_master_binding={"status": "verified"},
    )

    row = report["rows"][0]
    assert row["turn_lag_vs_candidate_sec"] == 105.0
    assert row["primary_outcome"]["label"] == "target_first"
    assert row["primary_outcome"]["elapsed_sec"] == 1145.0


def test_bundled_pre_anchor_path_is_scope_checked_and_replayed():
    start = datetime(2026, 9, 2, 9, 0, tzinfo=KST)
    bundle = _event(
        "rising_missed_entry_turn_pre_anchor_bbo_path",
        start + timedelta(seconds=20),
    )
    bundle["fields"].update(
        {
            "rising_missed_tp1_evaluation_id": "eval-1",
            "rising_missed_entry_turn_bbo_samples": [
                {
                    "observed_epoch": (start + timedelta(seconds=offset)).timestamp(),
                    "recorded_epoch": (start + timedelta(seconds=offset)).timestamp(),
                    "best_bid": bid,
                    "best_ask": ask,
                    "quote_age_ms": 0.0,
                    "source_provenance": "existing_ws_route_scoped_0d_snapshot",
                    "effective_venue": "KRX",
                    "market_session_bucket": "krx_regular",
                    "observed_venue": "KRX",
                    "route_scope_status": "exact_0d_route_snapshot",
                    "scanner_promotion_id": "PROM-1",
                }
                for offset, bid, ask in (
                    (0, 99.9, 100.0),
                    (5, 100.0, 100.1),
                    (10, 100.1, 100.2),
                    (15, 100.3, 100.4),
                    (20, 100.3, 100.4),
                )
            ],
        }
    )
    events = [
        bundle,
        _event(
            "rising_missed_tp1_counterfactual_submit_safety",
            start + timedelta(seconds=20),
        ),
        _event("fixture_bbo", start + timedelta(seconds=25), bid=101.0, ask=101.1),
    ]

    report = mod.build_entry_turn_point_replay(
        events,
        target_date="2026-09-02",
        current_label_rows=[],
        observation_watermark=start + timedelta(minutes=21),
        symbol_master=_VerifiedCommonMaster(),
        symbol_master_binding={"status": "verified"},
    )

    assert report["rows"][0]["turn"]["profile"] == "momentum_turn_entry"
    assert report["rows"][0]["pre_anchor_ws_bbo_observation_count"] >= 4
    assert report["rows"][0]["candidate_entry_bbo_source"] == (
        "entry_turn_pre_anchor_bbo_ring"
    )
    assert report["exact_ws_bbo_join_coverage_pct"] == 100.0
    assert report["bbo_extraction_gap_counts"] == {}


def test_feedback_projection_preserves_bounded_pre_anchor_bundle(tmp_path):
    start = datetime(2026, 9, 2, 9, 0, tzinfo=KST)
    bundle = _event(
        "rising_missed_entry_turn_pre_anchor_bbo_path",
        start + timedelta(seconds=5),
    )
    bundle["fields"].update(
        {
            "rising_missed_tp1_evaluation_id": "eval-1",
            "rising_missed_entry_turn_bbo_samples": [
                {
                    "observed_epoch": start.timestamp(),
                    "recorded_epoch": start.timestamp(),
                    "best_bid": 100.0,
                    "best_ask": 100.1,
                    "quote_age_ms": 0.0,
                    "source_provenance": "existing_ws_route_scoped_0d_snapshot",
                    "effective_venue": "KRX",
                    "market_session_bucket": "krx_regular",
                    "observed_venue": "KRX",
                    "route_scope_status": "exact_0d_route_snapshot",
                    "scanner_promotion_id": "PROM-1",
                }
            ],
        }
    )
    candidate = _event(
        "rising_missed_tp1_counterfactual_submit_safety",
        start + timedelta(seconds=5),
        bid=100.0,
        ask=100.1,
    )
    pipeline_path = tmp_path / "pipeline.jsonl"
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in (bundle, candidate)) + "\n",
        encoding="utf-8",
    )

    projected, _watermark = feedback._load_tp1_label_event_projection(pipeline_path)

    bundled_rows = [
        row
        for row in projected
        if row["stage"] == "rising_missed_entry_turn_pre_anchor_bbo_path"
    ]
    assert len(bundled_rows) == 1
    assert len(bundled_rows[0]["fields"]["rising_missed_entry_turn_bbo_samples"]) == 1


def test_runtime_bbo_ring_is_bounded_source_only_and_evaluation_deduped(monkeypatch):
    observed_at = datetime(2026, 9, 2, 9, 1, tzinfo=KST).timestamp()
    stock = {
        "id": 1,
        "name": "fixture",
        "code": "000001",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "scanner_promotion_id": "PROM-1",
        "effective_venue": "KRX",
        "venue": "KRX",
        "market_session_bucket": "krx_regular",
    }
    ws_data = {
        "last_realtime_type_market_route": {"0D": "krx_regular"},
        "realtime_type_snapshots_by_route": {
            "000001|krx_regular": {
                "0D": {
                    "observed_epoch": observed_at,
                    "item": "000001",
                    "market_route": "krx_regular",
                    "effective_venue": "KRX",
                    "orderbook": {
                        "asks": [{"price": 1001, "volume": 10}],
                        "bids": [{"price": 1000, "volume": 12}],
                    },
                }
            }
        },
    }
    emitted = []
    monkeypatch.setattr(handlers.time, "time", lambda: observed_at + 0.2)
    monkeypatch.setattr(
        handlers,
        "_log_entry_pipeline",
        lambda stock, code, stage, **fields: emitted.append(
            {"stage": stage, "fields": fields}
        ),
    )

    capture = handlers._capture_rising_missed_entry_turn_bbo(
        stock,
        "000001",
        ws_data,
        now_ts=observed_at + 0.2,
    )
    decision_fields = {
        "rising_missed_tp1_evaluation_id": "eval-1",
        "scanner_promotion_id": "PROM-1",
        "rising_missed_effective_venue": "KRX",
        "rising_missed_market_session_bucket": "krx_regular",
    }

    assert capture == {
        "captured": True,
        "reason": "fresh_exact_route_ws_bbo",
        "sample_count": 1,
    }
    assert handlers._emit_rising_missed_entry_turn_pre_anchor_bbo_path(
        stock, "000001", decision_fields
    )
    assert not handlers._emit_rising_missed_entry_turn_pre_anchor_bbo_path(
        stock, "000001", decision_fields
    )
    path = emitted[0]
    assert path["stage"] == "rising_missed_entry_turn_pre_anchor_bbo_path"
    assert path["fields"]["rising_missed_entry_turn_bbo_sample_count"] == 1
    assert (
        path["fields"]["rising_missed_entry_turn_bbo_samples"][0]["source_provenance"]
        == "existing_ws_route_scoped_0d_snapshot"
    )
    assert path["fields"]["runtime_effect"] is False
    assert path["fields"]["allowed_runtime_apply"] is False
    assert path["fields"]["actual_order_submitted"] is False
    assert path["fields"]["broker_order_forbidden"] is True


def test_runtime_bbo_ring_uses_tp1_nxt_session_scope():
    observed_at = datetime(2026, 9, 2, 16, 11, tzinfo=KST).timestamp()
    stock = {
        "code": "000001",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "scanner_promotion_id": "PROM-NXT",
        "effective_venue": "NXT",
        "venue": "NXT",
    }
    ws_data = {
        "last_realtime_type_market_route": {"0D": "nxt_only"},
        "realtime_type_snapshots_by_route": {
            "000001_NX|nxt_only": {
                "0D": {
                    "observed_epoch": observed_at,
                    "item": "000001_NX",
                    "market_route": "nxt_only",
                    "effective_venue": "NXT",
                    "orderbook": {
                        "asks": [{"price": 1001, "volume": 10}],
                        "bids": [{"price": 1000, "volume": 12}],
                    },
                }
            }
        },
    }

    capture = handlers._capture_rising_missed_entry_turn_bbo(
        stock,
        "000001",
        ws_data,
        now_ts=observed_at + 0.1,
    )

    assert capture["captured"] is True
    sample = stock[handlers._RISING_MISSED_ENTRY_TURN_BBO_RING_KEY][0]
    assert sample["effective_venue"] == "NXT"
    assert sample["market_session_bucket"] == "nxt_entry_window"
    assert sample["market_route"] == "nxt_only"


def test_runtime_bbo_ring_rejects_integrated_sor_as_krx(monkeypatch):
    observed_at = datetime(2026, 9, 2, 9, 1, tzinfo=KST).timestamp()
    stock = {
        "code": "000001",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "scanner_promotion_id": "PROM-KRX",
        "effective_venue": "KRX",
        "venue": "KRX",
    }
    monkeypatch.setattr(
        handlers,
        "_risky_micro_route_scoped_0d_bbo",
        lambda *args, **kwargs: (
            {
                "best_bid": 1000,
                "best_ask": 1001,
                "last_ws_update_ts": observed_at,
            },
            {
                "risky_micro_episode_horizon_observer_route_scope_eligible": True,
                "risky_micro_episode_horizon_observer_route_scope_status": (
                    "exact_0d_integrated_sor_execution_route"
                ),
                "risky_micro_episode_horizon_observer_observed_venue": "SOR",
            },
        ),
    )

    capture = handlers._capture_rising_missed_entry_turn_bbo(
        stock,
        "000001",
        {"last_realtime_type_market_route": {"0D": "krx_nxt_integrated"}},
        now_ts=observed_at + 0.1,
    )

    assert capture["captured"] is False
    assert capture["reason"] == "exact_route_venue_provenance_invalid"
    assert handlers._RISING_MISSED_ENTRY_TURN_BBO_RING_KEY not in stock


def test_runtime_bbo_ring_throttle_preserves_spacing_anchor(monkeypatch):
    base = datetime(2026, 9, 2, 9, 1, tzinfo=KST).timestamp()
    stock = {
        "code": "000001",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "scanner_promotion_id": "PROM-KRX",
        "effective_venue": "KRX",
        "venue": "KRX",
    }

    def _scoped(ws_data, **kwargs):
        return (
            {
                "best_bid": 1000,
                "best_ask": 1001,
                "last_ws_update_ts": ws_data["epoch"],
            },
            {
                "risky_micro_episode_horizon_observer_route_scope_eligible": True,
                "risky_micro_episode_horizon_observer_route_scope_status": (
                    "exact_0d_route_snapshot"
                ),
                "risky_micro_episode_horizon_observer_observed_venue": "KRX",
            },
        )

    monkeypatch.setattr(handlers, "_risky_micro_route_scoped_0d_bbo", _scoped)
    for offset in (0.0, 0.2, 0.4, 0.6):
        handlers._capture_rising_missed_entry_turn_bbo(
            stock,
            "000001",
            {"epoch": base + offset},
            now_ts=base + offset + 0.1,
        )

    epochs = [
        sample["observed_epoch"]
        for sample in stock[handlers._RISING_MISSED_ENTRY_TURN_BBO_RING_KEY]
    ]
    assert epochs == [base, base + 0.6]


def test_source_only_capture_failure_cannot_interrupt_public_precheck(monkeypatch):
    captures = []
    emitted = []
    stock = {
        "code": "000001",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "scanner_promotion_id": "PROM-1",
    }

    def _raise_capture(*args, **kwargs):
        captures.append((args, kwargs))
        raise RuntimeError("fixture")

    monkeypatch.setattr(
        handlers,
        "_capture_rising_missed_entry_turn_bbo_impl",
        _raise_capture,
    )
    monkeypatch.setattr(
        handlers,
        "_scanner_fast_precheck_fields",
        lambda *args, **kwargs: {
            "fast_precheck_result": "source_quality_blocked",
            "fast_precheck_reason": "fixture",
        },
    )
    monkeypatch.setattr(
        handlers,
        "_log_entry_pipeline",
        lambda *args, **kwargs: emitted.append((args, kwargs)),
    )

    assert handlers.emit_scanner_fast_precheck(
        stock,
        "000001",
        now_ts=100.0,
        ws_data={},
        throttle_sec=0,
    )
    assert len(captures) == 1
    assert stock[handlers._RISING_MISSED_ENTRY_TURN_BBO_LAST_CAPTURE_KEY] == {
        "captured": False,
        "reason": "source_only_capture_internal_error",
        "sample_count": 0,
        "error_class": "RuntimeError",
        "capture_attempt_epoch": 100.0,
    }
    assert len(emitted) == 1


def test_replay_excludes_rest_bbo_and_does_not_impute_missing_pre_anchor_path():
    start = datetime(2026, 9, 2, 9, 0, tzinfo=KST)
    candidate = _event(
        "rising_missed_tp1_counterfactual_submit_safety",
        start,
        bid=100.0,
        ask=100.1,
    )
    candidate["fields"]["market_data_effective_price_source"] = "ka10004_rest_orderbook"

    report = mod.build_entry_turn_point_replay(
        [candidate],
        target_date="2026-09-02",
        current_label_rows=[
            {
                "evaluation_id": "eval-1",
                "gross_first_hit_label": "adverse_stop_first",
            }
        ],
        observation_watermark=start + timedelta(minutes=21),
        symbol_master=_VerifiedCommonMaster(),
        symbol_master_binding={"status": "verified"},
    )

    assert report["exact_ws_bbo_joined_count"] == 0
    assert (
        report["source_quality_gap_counts"]["exact_venue_session_ws_bbo_missing"] == 1
    )
    assert (
        report["source_quality_gap_counts"][
            "current_outcome_non_executable_or_unresolved"
        ]
        == 1
    )
    assert report["rows"][0]["causal_bucket"] == "source_quality_unresolved"
    assert report["rows"][0]["primary_outcome"] is None
    assert report["status"] == "source_quality_blocked"


def test_replay_rejects_quote_age_timestamp_mismatch():
    start = datetime(2026, 9, 2, 9, 0, tzinfo=KST)
    candidate = _event(
        "rising_missed_tp1_counterfactual_submit_safety",
        start,
        bid=100.0,
        ask=100.1,
    )
    candidate["fields"]["market_data_effective_quote_observed_epoch"] = (
        start - timedelta(seconds=30)
    ).timestamp()

    report = mod.build_entry_turn_point_replay(
        [candidate],
        target_date="2026-09-02",
        current_label_rows=[],
        observation_watermark=start + timedelta(minutes=21),
        symbol_master=_VerifiedCommonMaster(),
        symbol_master_binding={"status": "verified", "artifact_sha256": "a" * 64},
    )

    assert report["exact_ws_bbo_join_coverage_pct"] == 0.0
    assert report["bbo_extraction_gap_counts"] == {
        "market_data_effective_bbo:observation_time_stale": 1
    }


def test_replay_never_joins_another_scanner_promotion_for_same_symbol():
    start = datetime(2026, 9, 2, 9, 0, tzinfo=KST)
    other_promotion_events = [
        _event("fixture_bbo", start, bid=99.9, ask=100.0),
        _event("fixture_bbo", start + timedelta(seconds=5), bid=100.0, ask=100.1),
        _event("fixture_bbo", start + timedelta(seconds=10), bid=100.1, ask=100.2),
        _event("fixture_bbo", start + timedelta(seconds=15), bid=100.3, ask=100.4),
        _event("fixture_bbo", start + timedelta(seconds=25), bid=101.0, ask=101.1),
    ]
    for event in other_promotion_events:
        event["fields"]["scanner_promotion_id"] = "PROM-OTHER"
    candidate = _event(
        "rising_missed_tp1_counterfactual_submit_safety",
        start + timedelta(seconds=20),
        bid=100.3,
        ask=100.4,
    )

    report = mod.build_entry_turn_point_replay(
        [*other_promotion_events, candidate],
        target_date="2026-09-02",
        current_label_rows=[],
        observation_watermark=start + timedelta(minutes=21),
        symbol_master=_VerifiedCommonMaster(),
        symbol_master_binding={"status": "verified"},
    )

    row = report["rows"][0]
    assert row["turn"] is None
    assert row["exact_ws_bbo_observation_count"] == 1
    assert row["causal_bucket"] == "source_quality_unresolved"


def test_replay_excludes_verified_non_common_instrument_from_economics():
    start = datetime(2026, 9, 2, 9, 0, tzinfo=KST)
    candidate = _event(
        "rising_missed_tp1_counterfactual_submit_safety",
        start,
        bid=100.0,
        ask=100.1,
    )

    report = mod.build_entry_turn_point_replay(
        [candidate],
        target_date="2026-09-02",
        current_label_rows=[
            {"evaluation_id": "eval-1", "gross_first_hit_label": "gross_target_first"}
        ],
        observation_watermark=start + timedelta(minutes=21),
        symbol_master=_VerifiedEtfMaster(),
        symbol_master_binding={"status": "verified"},
    )

    assert report["verified_official_common_stock_candidate_count"] == 0
    assert (
        report["source_quality_gap_counts"][
            "symbol_master:excluded_instrument_type:ETF"
        ]
        == 1
    )
    assert report["rows"][0]["official_symbol_master_status"] == (
        "excluded_instrument_type:ETF"
    )


def test_rising_missed_report_connects_projected_milestones_to_turn_replay(
    tmp_path, monkeypatch
):
    start = datetime(2026, 9, 2, 9, 0, tzinfo=KST)
    events = [
        _event("fixture_bbo", start, bid=99.9, ask=100.0),
        _event("fixture_bbo", start + timedelta(seconds=5), bid=100.0, ask=100.1),
        _event("fixture_bbo", start + timedelta(seconds=10), bid=100.1, ask=100.2),
        _event("fixture_bbo", start + timedelta(seconds=15), bid=100.3, ask=100.4),
        _event("scalping_scanner_candidate_promoted", start + timedelta(seconds=18)),
        _event(
            "rising_missed_tp1_counterfactual_submit_safety",
            start + timedelta(seconds=20),
            bid=100.3,
            ask=100.4,
        ),
        _event("fixture_bbo", start + timedelta(seconds=25), bid=101.0, ask=101.1),
    ]
    pipeline_path = tmp_path / "pipeline.jsonl"
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in events) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        feedback,
        "load_entry_turn_verified_symbol_master",
        lambda target_date, symbol_master_path=None: (
            _VerifiedCommonMaster(),
            {"status": "verified", "artifact_sha256": "a" * 64},
        ),
    )

    report = feedback.build_report(
        "2026-09-02",
        pipeline_path=pipeline_path,
        generated_at="2026-09-02T15:40:00+09:00",
    )

    replay = report["entry_turn_point_replay"]
    assert report["metric_contracts"]["entry_turn_point_replay"] == mod.METRIC_CONTRACT
    assert replay["candidate_count"] == 1
    assert replay["rows"][0]["turn"]["profile"] == "momentum_turn_entry"
    assert "scalping_scanner_candidate_promoted" in replay["rows"][0]["milestones"]
    assert report["summary"]["entry_turn_point_replay"]["runtime_effect"] is False
    coverage_orders = [
        order
        for order in report["code_improvement_orders"]
        if order["order_id"] == "order_rising_missed_entry_turn_bbo_coverage"
    ]
    assert len(coverage_orders) == 1
    assert coverage_orders[0]["implementation_status"] == (
        "implemented_but_waiting_sample"
    )
    assert coverage_orders[0]["implementation_provenance"]["sample_status"] == (
        "waiting_next_pid_natural_sample"
    )
