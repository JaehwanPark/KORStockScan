import gzip
import json
from dataclasses import replace
from datetime import datetime

import pytest

from src.engine.lifecycle.archive import (
    scalp_entry_action_decision_matrix_readers as mod,
)
from src.engine import scalp_entry_adm_runtime as runtime_mod
from src.engine.scalping import entry_ai_gate as entry_gate_mod
from src.engine.scalping import entry_observation_events as observations


def _write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )


def _write_gzip_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


@pytest.mark.parametrize("storage", ["plain", "gzip", "coexist", "snapshot"])
def test_entry_observation_consumers_share_scoped_source(
    tmp_path, monkeypatch, storage
):
    from src.engine import scalp_entry_action_decision_matrix as compat
    from src.engine.scalping import entry_observation_source as source
    from src.utils import constants

    day = "2026-09-23"
    pipeline = tmp_path / "pipeline_events"
    threshold = tmp_path / "threshold_cycle"
    snapshots = threshold / "snapshots"
    monkeypatch.setattr(constants, "DATA_DIR", tmp_path)
    monkeypatch.setattr(observations, "PIPELINE_EVENT_DIR", pipeline)
    monkeypatch.setattr(observations, "THRESHOLD_EVENT_DIR", threshold)
    monkeypatch.setattr(observations, "THRESHOLD_SNAPSHOT_DIR", snapshots)
    accepted = {
        "stage": "ai_confirmed",
        "stock_code": "005930",
        "record_id": "r1",
        "emitted_date": day,
        "emitted_at": f"{day}T09:10:00+09:00",
        "fields": {"record_id": "r1", "ai_score": 72, "action": "BUY"},
    }
    rows = [
        accepted,
        dict(accepted, emitted_date="2026-09-22", record_id="wrong-date"),
        dict(
            accepted,
            record_id="retry",
            fields={
                "ai_call_trigger_reason": "early_accel_recheck",
            },
        ),
        dict(
            accepted,
            record_id="cancel",
            fields={
                "runtime_family": "entry_cancel_wait_runtime",
            },
        ),
    ]
    path = pipeline / f"pipeline_events_{day}.jsonl"
    if storage == "snapshot":
        path = snapshots / f"pipeline_events_{day}_postclose.jsonl.gz"
    elif storage == "gzip":
        path = path.with_suffix(".jsonl.gz")
    writer = _write_gzip_jsonl if path.suffix == ".gz" else _write_jsonl
    writer(path, rows)
    if storage == "coexist":
        _write_gzip_jsonl(path.with_suffix(".jsonl.gz"), rows)
    # A repeated source snapshot must not create a second observation.
    _write_jsonl(snapshots / f"threshold_events_{day}_later.jsonl", rows)

    events = list(compat._iter_relevant_events(day))
    assert [event["record_id"] for event in events] == ["r1"]
    assert events[0]["_source_path"] == str(path)
    assert events == list(observations._iter_relevant_events(day))
    result = source.load_entry_observations(day)
    assert result["status"] == "pass"
    assert len(result["rows"]) == 1
    row = result["rows"][0]
    assert (row["record_id"], row["ai_score"], row["chosen_action"]) == (
        "r1",
        72,
        "BUY_NOW",
    )
    assert result["decision_authority"] == "source_only"
    assert result["runtime_effect"] is False
    assert result["allowed_runtime_apply"] is False


@pytest.mark.parametrize("payload", [None, "", 'scalp-not-json\n["scalp"]\n'])
def test_entry_observation_empty_source_keeps_existing_status(
    tmp_path, monkeypatch, payload
):
    from src.engine.scalping import entry_observation_source as source
    from src.utils import constants

    day = "2026-09-23"
    monkeypatch.setattr(constants, "DATA_DIR", tmp_path)
    monkeypatch.setattr(observations, "PIPELINE_EVENT_DIR", tmp_path)
    monkeypatch.setattr(observations, "THRESHOLD_EVENT_DIR", tmp_path / "threshold")
    monkeypatch.setattr(observations, "THRESHOLD_SNAPSHOT_DIR", tmp_path / "snapshots")
    if payload is not None:
        (tmp_path / f"pipeline_events_{day}.jsonl").write_text(payload)
    result = source.load_entry_observations(day)
    assert result["status"] == "no_observations"
    assert result["rows"] == []
    assert result["allowed_runtime_apply"] is False


def test_entry_adm_excludes_early_accel_recheck_retry_rows(tmp_path, monkeypatch):
    pipeline_dir = tmp_path / "pipeline_events"
    threshold_dir = tmp_path / "threshold_cycle"
    snapshot_dir = threshold_dir / "snapshots"
    monkeypatch.setattr(observations, "PIPELINE_EVENT_DIR", pipeline_dir)
    monkeypatch.setattr(observations, "THRESHOLD_EVENT_DIR", threshold_dir)
    monkeypatch.setattr(observations, "THRESHOLD_SNAPSHOT_DIR", snapshot_dir)

    _write_jsonl(
        pipeline_dir / "pipeline_events_2026-05-18.jsonl",
        [
            {
                "stage": "blocked_ai_score",
                "stock_code": "111111",
                "record_id": "R1",
                "emitted_at": "2026-05-18T09:10:00",
                "emitted_date": "2026-05-18",
                "fields": {
                    "ai_score": "62",
                    "ai_call_trigger_reason": "early_accel_recheck",
                    "tuning_authority_excluded_reason": "early_accel_recheck_operator_retry",
                },
            },
            {
                "stage": "scalp_entry_action_decision_snapshot",
                "stock_code": "111111",
                "record_id": "R1",
                "emitted_at": "2026-05-18T09:10:01",
                "emitted_date": "2026-05-18",
                "fields": {
                    "source_stage": "blocked_ai_score",
                    "chosen_action": "NO_BUY_AI",
                    "ai_score": "62",
                    "ai_call_trigger_reason": "early_accel_recheck",
                    "tuning_authority_excluded_reason": "early_accel_recheck_operator_retry",
                },
            },
            {
                "stage": "order_bundle_submitted",
                "stock_code": "111111",
                "record_id": "R1",
                "emitted_at": "2026-05-18T09:10:02",
                "emitted_date": "2026-05-18",
                "fields": {
                    "actual_order_submitted": "true",
                    "broker_order_submitted": "true",
                    "ai_call_trigger_reason": "early_accel_recheck",
                    "tuning_authority_excluded_reason": "early_accel_recheck_operator_retry",
                },
            },
            {
                "stage": "blocked_ai_score",
                "stock_code": "222222",
                "record_id": "R2",
                "emitted_at": "2026-05-18T09:11:00",
                "emitted_date": "2026-05-18",
                "fields": {"ai_score": "63"},
            },
        ],
    )

    rows = list(observations._iter_relevant_events("2026-05-18"))

    assert len(rows) == 1
    assert rows[0]["stock_code"] == "222222"


def test_scalp_entry_adm_loads_gzip_sim_evaluations(tmp_path, monkeypatch):
    post_sell_dir = tmp_path / "post_sell"
    monkeypatch.setattr(mod, "POST_SELL_DIR", post_sell_dir)
    _write_gzip_jsonl(
        post_sell_dir / "sim_post_sell_evaluations_2026-05-18.jsonl.gz",
        [{"sim_record_id": "SIM1", "candidate_id": "ADM1", "profit_rate": 1.25}],
    )

    rows, meta = mod._load_sim_evaluations("2026-05-18")

    assert meta["artifact"].endswith(".jsonl.gz")
    assert meta["rows"] == 1
    assert rows["SIM1"]["profit_rate"] == 1.25


def test_outcome_join_diagnostic_excludes_non_entry_terminal_evaluations():
    entry_evaluation = {
        "candidate_id": "ADM-ENTRY-1",
        "_post_sell_evaluation_id": "POST-ENTRY-1",
    }
    non_entry_evaluation = {
        "sim_record_id": "SCALPSIM-TERMINAL-ONLY",
        "_post_sell_evaluation_id": "POST-TERMINAL-ONLY",
    }
    aggregate_row = {
        "candidate_id": "ADM-ENTRY-1",
        "sim_record_id": "SCALPSIM-ENTRY-1",
        "outcome_joined": True,
        "post_sell_evaluation_id": "POST-ENTRY-1",
    }

    diagnostic = mod._outcome_join_diagnostic(
        rows=[
            aggregate_row,
            {
                "stage": "scalp_sim_sell_order_assumed_filled",
                "sim_record_id": "SCALPSIM-TERMINAL-ONLY",
                "outcome_joined": True,
                "post_sell_evaluation_id": "POST-TERMINAL-ONLY",
            },
        ],
        aggregate_rows=[aggregate_row],
        evaluations={
            "ADM-ENTRY-1": entry_evaluation,
            "SCALPSIM-ENTRY-1": entry_evaluation,
            "SCALPSIM-TERMINAL-ONLY": non_entry_evaluation,
        },
        eval_summary={"rows": 2, "join_keys": 3},
    )

    assert diagnostic["coverage_state"] == "source_outcome_underproduction"
    assert diagnostic["entry_adm_relevant_post_sell_evaluation_rows"] == 1
    assert diagnostic["non_entry_or_unmatched_post_sell_evaluation_rows"] == 1
    assert diagnostic["unmatched_entry_adm_relevant_post_sell_evaluation_rows"] == 0
    assert diagnostic["matched_post_sell_evaluation_rows"] == 1
    assert diagnostic["post_sell_evaluation_match_rate"] == 1.0


def test_scalp_entry_adm_event_paths_include_gzip_threshold_events(
    tmp_path, monkeypatch
):
    threshold_dir = tmp_path / "threshold_cycle"
    monkeypatch.setattr(observations, "THRESHOLD_EVENT_DIR", threshold_dir)
    monkeypatch.setattr(
        observations, "PIPELINE_EVENT_DIR", tmp_path / "pipeline_events"
    )
    monkeypatch.setattr(
        observations, "THRESHOLD_SNAPSHOT_DIR", threshold_dir / "snapshots"
    )
    _write_gzip_jsonl(
        threshold_dir / "threshold_events_2026-05-18.jsonl.gz",
        [{"stage": "scalp_entry_action_decision_snapshot", "fields": {}}],
    )

    assert observations._event_paths("2026-05-18") == [
        threshold_dir / "threshold_events_2026-05-18.jsonl.gz"
    ]


def test_scalp_entry_adm_normalizes_submitted_snapshot_action():
    fields = {
        "source_stage": "order_bundle_submitted",
        "chosen_action": "NO_BUY_AI",
        "actual_order_submitted": True,
        "broker_order_submitted": True,
        "broker_order_no": "0046858",
        "order_no": "0046858",
        "ord_no": "0046858",
        "broker_order_no_list": "0046858,0046859",
        "order_response_ord_no": "0046858",
        "submit_attempt_id": "005930:1781160000000:0046858",
        "price_resolution_reason": "defensive_order_price",
    }

    assert (
        observations._chosen_action("scalp_entry_action_decision_snapshot", fields)
        == "BUY_DEFENSIVE"
    )
    row = observations._base_row(
        {
            "stage": "scalp_entry_action_decision_snapshot",
            "stock_code": "005930",
            "stock_name": "TEST",
            "fields": fields,
        }
    )
    assert row["source_stage"] == "order_bundle_submitted"
    assert row["raw_chosen_action"] == "NO_BUY_AI"
    assert row["chosen_action"] == "BUY_DEFENSIVE"
    assert row["action_normalized"] is True
    assert (
        row["action_normalization_reason"]
        == "submitted_or_latency_pass_non_buy_action_normalized"
    )
    assert row["broker_order_submitted"] is True
    assert row["broker_order_no"] == "0046858"
    assert row["order_no"] == "0046858"
    assert row["ord_no"] == "0046858"
    assert row["broker_order_no_list"] == "0046858,0046859"
    assert row["order_response_ord_no"] == "0046858"
    assert row["submit_attempt_id"] == "005930:1781160000000:0046858"
    assert (
        observations._chosen_action(
            "scalp_entry_action_decision_snapshot",
            {
                "source_stage": "entry_submit_revalidation_warning",
                "chosen_action": "WAIT_REQUOTE",
            },
        )
        == "WAIT_REQUOTE"
    )


def test_scalp_entry_adm_preserves_sim_candidate_original_score_on_price_skip():
    row = observations._base_row(
        {
            "stage": "scalp_sim_entry_ai_price_skip_order",
            "stock_code": "005930",
            "emitted_at": "2026-07-29T09:10:00",
            "fields": {
                "scalp_sim_candidate_window_original_score": "56.0",
                "scalp_sim_candidate_window_original_action": "BUY",
                "ai_entry_price_canary_action": "SKIP",
                "ai_entry_price_canary_reason": "ai_input_preflight_blocked",
            },
        }
    )

    assert row["ai_score"] == 56.0
    assert row["score_source_value"] == 56.0
    assert row["score_bucket"] == "score50_64"
    assert row["chosen_action"] == "SKIP_PRE_SUBMIT_SAFETY"
    assert (
        observations._score_source(
            {
                "ai_score": "70",
                "scalp_sim_candidate_window_original_score": "56",
            }
        )
        == "70"
    )


def test_scalp_entry_adm_uses_current_ai_score_on_price_skip():
    row = observations._base_row(
        {
            "stage": "scalp_sim_entry_ai_price_skip_order",
            "stock_code": "005930",
            "emitted_at": "2026-07-31T09:10:00",
            "fields": {
                "current_ai_score": 68.0,
                "ai_entry_price_canary_action": "SKIP",
                "ai_entry_price_canary_reason": "low_fillability",
            },
        }
    )

    assert row["ai_score"] == 68.0
    assert row["score_source_value"] == 68.0
    assert row["score_bucket"] == "score65_74"


def test_scalp_entry_adm_ai_confirmed_uses_score_as_prior_not_hard_gate(monkeypatch):
    monkeypatch.setattr(
        entry_gate_mod,
        "TRADING_RULES",
        replace(entry_gate_mod.TRADING_RULES, BUY_SCORE_THRESHOLD=70),
    )

    assert (
        observations._chosen_action("ai_confirmed", {"action": "BUY", "ai_score": "72"})
        == "BUY_NOW"
    )
    assert (
        observations._chosen_action("ai_confirmed", {"action": "BUY", "ai_score": "69"})
        == "BUY_NOW"
    )
    assert (
        observations._chosen_action(
            "ai_confirmed", {"action": "WAIT", "ai_score": "90"}
        )
        == "NO_BUY_AI"
    )


def test_scalp_entry_adm_preserves_submit_refresh_provenance():
    row = observations._base_row(
        {
            "stage": "order_bundle_submitted",
            "stock_code": "005930",
            "stock_name": "TEST",
            "record_id": "R1",
            "emitted_at": "2026-05-18T09:10:02",
            "fields": {
                "actual_order_submitted": "true",
                "broker_order_submitted": "true",
                "broker_order_no": "0046858",
                "entry_submit_revalidation_warning": "stale_context_or_quote",
                "quote_age_at_submit_ms": "2628",
                "best_bid_at_submit": "16860",
                "best_ask_at_submit": "16910",
                "submitted_order_price": "16830",
                "latency_state": "SAFE",
                "latency_danger_reasons": "spread_too_wide",
                "pre_submit_quote_refresh_enabled": "true",
                "pre_submit_quote_refresh_applied": "false",
                "pre_submit_quote_refresh_reason": "observer_quote_stale",
                "pre_submit_quote_refresh_source": "orderbook_micro_observer",
                "pre_submit_quote_refresh_quote_age_ms": "1500",
                "pre_submit_quote_refresh_strategy_id": "KOSPI_ML",
                "pre_submit_quote_refresh_env_value": "true",
                "pre_submit_ws_snapshot_refresh_enabled": "true",
                "pre_submit_ws_snapshot_refresh_applied": "true",
                "pre_submit_ws_snapshot_refresh_reason": "latest_ws_snapshot_fresh",
                "pre_submit_ws_snapshot_refresh_source": "ws_manager_latest_data",
                "pre_submit_ws_snapshot_refresh_age_ms": "12",
            },
        }
    )

    assert row["entry_submit_revalidation_warning"] == "stale_context_or_quote"
    assert row["quote_age_ms"] == 2628.0
    assert row["best_bid"] == 16860.0
    assert row["best_ask"] == 16910.0
    assert row["resolved_order_price"] == 16830.0
    assert row["latency_state"] == "SAFE"
    assert row["latency_reason"] == "spread_too_wide"
    assert row["pre_submit_quote_refresh_enabled"] is True
    assert row["pre_submit_quote_refresh_applied"] is False
    assert row["pre_submit_quote_refresh_reason"] == "observer_quote_stale"
    assert row["pre_submit_quote_refresh_source"] == "orderbook_micro_observer"
    assert row["pre_submit_quote_refresh_quote_age_ms"] == 1500.0
    assert row["pre_submit_quote_refresh_strategy_id"] == "KOSPI_ML"
    assert row["pre_submit_quote_refresh_env_value"] == "true"
    assert row["pre_submit_ws_snapshot_refresh_enabled"] is True
    assert row["pre_submit_ws_snapshot_refresh_applied"] is True
    assert row["pre_submit_ws_snapshot_refresh_reason"] == "latest_ws_snapshot_fresh"
    assert row["pre_submit_ws_snapshot_refresh_source"] == "ws_manager_latest_data"
    assert row["pre_submit_ws_snapshot_refresh_age_ms"] == 12.0


def test_scalp_entry_adm_runtime_context_adds_prompt_and_cache_token(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report" / "scalp_entry_action_decision_matrix"
    report_dir.mkdir(parents=True)
    monkeypatch.setattr(runtime_mod, "ADM_DIR", report_dir)
    bucket_token = "score75_84|strong_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1400_close"
    (report_dir / "scalp_entry_action_decision_matrix_2026-05-18.json").write_text(
        json.dumps(
            {
                "date": "2026-05-18",
                "matrix_version": "scalp_entry_adm_v1_2026-05-18",
                "bucket_summary": [
                    {
                        "bucket_token": bucket_token,
                        "dominant_action": "BUY_NOW",
                        "sample_count": 25,
                        "joined_sample": 21,
                        "source_quality_adjusted_ev_pct": 0.42,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    context = runtime_mod.build_scalp_entry_adm_runtime_context(
        prompt_profile="watching",
        ws_data={
            "latest_strength": 151,
            "quote_age_ms": 300,
            "curr": 10000,
            "volume": 100000,
            "intraday_range_pct": 4.0,
            "best_ask": 10010,
        },
        advisory_enabled=True,
        now=datetime(2026, 5, 18, 16, 30),
        ai_score=78,
    )
    assert context["applied"] is False
    assert context["prompt_context"] == ""


def test_scalp_entry_adm_runtime_bias_forces_wait_on_negative_buy_bucket(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report" / "scalp_entry_action_decision_matrix"
    report_dir.mkdir(parents=True)
    monkeypatch.setattr(runtime_mod, "ADM_DIR", report_dir)
    monkeypatch.setattr(
        runtime_mod,
        "TRADING_RULES",
        replace(runtime_mod.TRADING_RULES, SCALP_ENTRY_ADM_RUNTIME_BIAS_ENABLED=True),
    )
    bucket_token = "score75_84|strong_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1400_close"
    (report_dir / "scalp_entry_action_decision_matrix_2026-05-18.json").write_text(
        json.dumps(
            {
                "date": "2026-05-18",
                "matrix_version": "scalp_entry_adm_v1_2026-05-18",
                "bucket_summary": [
                    {
                        "bucket_token": bucket_token,
                        "dominant_action": "BUY_NOW",
                        "sample_count": 20,
                        "joined_sample": 10,
                        "source_quality_adjusted_ev_pct": -2.54,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    context = runtime_mod.build_scalp_entry_adm_runtime_context(
        prompt_profile="watching",
        ws_data={
            "latest_strength": 151,
            "quote_age_ms": 300,
            "curr": 10000,
            "volume": 100000,
            "intraday_range_pct": 4.0,
            "best_ask": 10010,
        },
        advisory_enabled=True,
        now=datetime(2026, 5, 18, 16, 30),
        ai_score=78,
    )
    assert context["applied"] is False
    assert context["prompt_context"] == ""


def test_scalp_entry_adm_runtime_maps_runtime_context_without_unknown_buckets(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report" / "scalp_entry_action_decision_matrix"
    report_dir.mkdir(parents=True)
    monkeypatch.setattr(runtime_mod, "ADM_DIR", report_dir)
    (report_dir / "scalp_entry_action_decision_matrix_2026-05-18.json").write_text(
        json.dumps(
            {
                "date": "2026-05-18",
                "matrix_version": "scalp_entry_adm_v1_2026-05-18",
                "bucket_summary": [],
            }
        ),
        encoding="utf-8",
    )

    context = runtime_mod.build_scalp_entry_adm_runtime_context(
        prompt_profile="watching",
        ws_data={
            "current_ai_score": 62.0,
            "latest_strength": 70,
            "buy_pressure_10t": 35,
            "quote_stale": "False",
            "curr": 10_000,
            "volume": 100_000,
            "orderbook": {"asks": [{"price": 10_010}], "bids": [{"price": 9_990}]},
            "scalp_pre_ai_gate_context": {
                "strength_momentum": {
                    "risk_state": "weak_momentum_context",
                    "gate_action": "risk_context_only",
                },
                "overbought": {
                    "risk_state": "pullback_observed",
                    "risk_bucket": "pullback_candidate",
                },
            },
        },
        advisory_enabled=True,
        now=datetime(2026, 5, 18, 16, 30),
    )

    fields = context["fields"]
    assert fields["entry_adm_score_bucket"] == "score50_64"
    assert fields["entry_adm_risk_context_bucket"] == "weak_strength_momentum"
    assert fields["entry_adm_market_regime_continuous_bucket"] == "-"
    assert fields["entry_adm_stale_bucket"] == "fresh"
    assert fields["entry_adm_price_resolution_bucket"] == "quote_based"
    assert fields["entry_adm_liquidity_bucket"] == "liquidity_high"
    assert fields["entry_adm_overbought_bucket"] == "overbought_ok"
    assert "unknown" not in fields["entry_adm_bucket_token"]


def test_scalp_entry_adm_row_preserves_live_entry_replay_context_fields():
    row = observations._base_row(
        {
            "stage": "scalp_entry_action_decision_snapshot",
            "stock_code": "123456",
            "stock_name": "CTX",
            "record_id": "RCTX",
            "emitted_at": "2026-05-18T09:10:00",
            "fields": {
                "source_stage": "ai_confirmed",
                "chosen_action": "BUY_NOW",
                "ai_score": "78",
                "entry_recheck_contract_status": "pass",
                "entry_recheck_edge_state": "EDGE",
                "entry_recheck_probe_intent": "true",
                "entry_recheck_probe_intent_status": "eligible_wait_probe",
                "entry_recheck_recovery_trigger": "recovery_required",
                "scalp_feature_packet_version": "scalp_feature_packet_v2",
                "ai_input_schema": "entry_screen_hot_v1",
                "ai_input_contract_mode": "structured_json",
                "ai_input_source_quality_status": "evaluated",
                "ai_input_source_quality_reason": "tick_audit_present",
                "entry_liquidity_score": "84.0",
                "entry_liquidity_status": "good",
                "fillability_score": "74.0",
                "would_fill_now": "true",
                "top1_bid_notional": "30300000",
                "top1_ask_notional": "45450000",
                "top3_bid_notional": "121200000",
                "top3_ask_notional": "166650000",
                "quote_depth_present": "true",
                "quote_fresh_for_entry": "true",
                "order_flow_pressure_score": "79.5",
                "entry_order_flow_status": "supportive",
                "order_flow_pressure_source": "trusted_aggressor",
                "entry_momentum_score": "88.0",
                "entry_momentum_status": "accelerating",
                "entry_context_quality": "complete",
                "entry_context_missing_features": "",
                "latest_strength": "151.2",
                "buy_pressure_10t": "73.5",
                "net_aggressive_delta_10t": "41",
                "same_price_buy_absorption": "6",
                "tick_acceleration_ratio": "2.25",
                "tick_acceleration_ratio_raw": "2.11",
                "tick_accel_effective_recent_5tick_seconds": "1.2",
                "recent_5tick_seconds": "1.2",
                "prev_5tick_seconds": "2.7",
                "tick_sample_count": "10",
                "tick_window_span_sec": "4.2",
                "tick_aggressor_pressure_usable": "true",
                "tick_aggressor_trusted_count": "7",
                "tick_context_quality": "trusted_orderbook_touch",
                "tick_context_stale": "false",
                "tick_accel_source": "recent_ticks",
                "quote_age_source": "ws_snapshot",
                "curr_vs_micro_vwap_bp": "18.4",
                "curr_vs_ma5_bp": "9.5",
                "micro_vwap_available": "true",
                "ma5_available": "true",
                "minute_candle_context_quality": "fresh",
                "minute_candle_window_fresh": "true",
                "micro_vwap_value": "10010",
                "ma5_value": "10002",
                "top1_depth_ratio": "0.91",
                "top3_depth_ratio": "0.84",
                "orderbook_total_ratio": "0.92",
                "microprice_edge_bp": "2.4",
                "ask_depth_ratio": "0.45",
                "net_ask_depth": "-1200",
                "spread_bp": "4.1",
                "volume_ratio_pct": "220.5",
                "distance_from_day_high_pct": "-0.35",
                "intraday_range_pct": "8.2",
                "large_sell_print_detected": "false",
                "large_buy_print_detected": "true",
                "microstructure_reaction_context_status": "ok",
                "microstructure_reaction_entry_reaction_quality": "supportive",
                "microstructure_reaction_source_quality": "fresh",
                "microstructure_reaction_tick_trade_value_recent_sum": "1500000",
                "microstructure_reaction_tick_trade_value_prev_sum": "700000",
                "microstructure_reaction_ask_sweep_score": "2",
                "microstructure_reaction_post_sweep_hold_score": "3",
                "microstructure_reaction_bid_replenishment_score": "4",
                "microstructure_reaction_wall_replenishment_risk_score": "1",
                "microstructure_reaction_vi_proximity_risk": "0",
            },
        }
    )

    assert row["scalp_feature_packet_version"] == "scalp_feature_packet_v2"
    assert row["ai_input_schema"] == "entry_screen_hot_v1"
    assert row["ai_input_contract_mode"] == "structured_json"
    assert row["decision_quality_contract_status"] == "pass"
    assert row["edge_state"] == "EDGE"
    assert row["entry_probe_intent"] is True
    assert row["entry_probe_intent_status"] == "eligible_wait_probe"
    assert row["entry_recheck_recovery_trigger"] == "recovery_required"
    assert row["evidence_trigger"] == "recovery_required"
    assert row["entry_liquidity_score"] == 84.0
    assert row["entry_liquidity_status"] == "good"
    assert row["fillability_score"] == 74.0
    assert row["would_fill_now"] is True
    assert row["quote_depth_present"] is True
    assert row["quote_fresh_for_entry"] is True
    assert row["order_flow_pressure_score"] == 79.5
    assert row["entry_order_flow_status"] == "supportive"
    assert row["order_flow_pressure_source"] == "trusted_aggressor"
    assert row["entry_momentum_score"] == 88.0
    assert row["entry_momentum_status"] == "accelerating"
    assert row["entry_context_quality"] == "complete"
    assert row["buy_pressure_10t"] == 73.5
    assert row["tick_acceleration_ratio"] == 2.25
    assert row["curr_vs_micro_vwap_bp"] == 18.4
    assert row["top1_depth_ratio"] == 0.91
    assert row["top3_depth_ratio"] == 0.84
    assert row["microprice_edge_bp"] == 2.4
    assert row["tick_aggressor_pressure_usable"] is True
    assert row["tick_context_stale"] is False
    assert row["micro_vwap_available"] is True
    assert row["large_buy_print_detected"] is True
    assert row["microstructure_reaction_entry_reaction_quality"] == "supportive"
    assert row["microstructure_reaction_tick_trade_value_recent_sum"] == 1500000.0
    assert row["microstructure_reaction_bid_replenishment_score"] == 4.0


def test_scalp_entry_adm_runtime_ignores_pressure_without_trusted_aggressor_provenance():
    assert (
        runtime_mod._risk_context_bucket(
            {
                "buy_pressure_10t": 85,
                "tick_aggressor_pressure_usable": False,
                "tick_aggressor_trusted_count": 0,
            }
        )
        == "risk_unknown"
    )
    assert (
        runtime_mod._risk_context_bucket(
            {
                "buy_pressure_10t": 85,
                "tick_aggressor_pressure_usable": "stale",
                "tick_aggressor_trusted_count": 0,
            }
        )
        == "risk_unknown"
    )


def test_scalp_entry_adm_runtime_uses_pressure_with_trusted_aggressor_provenance():
    assert (
        runtime_mod._risk_context_bucket(
            {
                "buy_pressure_10t": 85,
                "tick_aggressor_pressure_usable": True,
                "tick_aggressor_trusted_count": 1,
            }
        )
        == "strong_strength_momentum"
    )
    assert (
        runtime_mod._risk_context_bucket(
            {
                "buy_pressure_10t": 35,
                "tick_aggressor_pressure_usable": "false",
                "tick_aggressor_trusted_count": 2,
            }
        )
        == "weak_strength_momentum"
    )


def test_scalp_entry_adm_runtime_strength_bucket_still_works_without_pressure_provenance():
    assert (
        runtime_mod._risk_context_bucket(
            {
                "latest_strength": 145,
                "buy_pressure_10t": 20,
                "tick_aggressor_pressure_usable": False,
                "tick_aggressor_trusted_count": 0,
            }
        )
        == "strong_strength_momentum"
    )
    assert (
        runtime_mod._risk_context_bucket(
            {
                "latest_strength": 75,
                "buy_pressure_10t": 90,
                "tick_aggressor_pressure_usable": False,
                "tick_aggressor_trusted_count": 0,
            }
        )
        == "weak_strength_momentum"
    )


def test_scalp_entry_adm_bucket_sample_floor_blocks_force_wait(tmp_path, monkeypatch):
    report_dir = tmp_path / "report" / "scalp_entry_action_decision_matrix"
    report_dir.mkdir(parents=True)
    monkeypatch.setattr(runtime_mod, "ADM_DIR", report_dir)
    monkeypatch.setattr(
        runtime_mod,
        "TRADING_RULES",
        replace(runtime_mod.TRADING_RULES, SCALP_ENTRY_ADM_RUNTIME_BIAS_ENABLED=True),
    )
    bucket_token = "score75_84|strong_strength_momentum|-|fresh|quote_based|liquidity_high|overbought_normal|time_1400_close"
    (report_dir / "scalp_entry_action_decision_matrix_2026-05-18.json").write_text(
        json.dumps(
            {
                "date": "2026-05-18",
                "matrix_version": "scalp_entry_adm_v1_2026-05-18",
                "bucket_summary": [
                    {
                        "bucket_token": bucket_token,
                        "dominant_action": "WAIT_REQUOTE",
                        "sample_count": 4,
                        "joined_sample": 1,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    context = runtime_mod.build_scalp_entry_adm_runtime_context(
        prompt_profile="watching",
        ws_data={
            "latest_strength": 151,
            "quote_age_ms": 300,
            "curr": 10000,
            "volume": 100000,
            "intraday_range_pct": 4.0,
            "best_ask": 10010,
        },
        advisory_enabled=True,
        now=datetime(2026, 5, 18, 16, 30),
        ai_score=78,
    )
    assert context["applied"] is False
    assert context["prompt_context"] == ""


def test_scalp_entry_adm_hypothesis_fallback_is_provenance_only_by_default(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report" / "scalp_entry_action_decision_matrix"
    report_dir.mkdir(parents=True)
    monkeypatch.setattr(runtime_mod, "ADM_DIR", report_dir)
    monkeypatch.setattr(
        runtime_mod,
        "TRADING_RULES",
        replace(runtime_mod.TRADING_RULES, SCALP_ENTRY_ADM_RUNTIME_BIAS_ENABLED=True),
    )
    (report_dir / "scalp_entry_action_decision_matrix_2026-05-18.json").write_text(
        json.dumps(
            {
                "date": "2026-05-18",
                "matrix_version": "scalp_entry_adm_v1_2026-05-18",
                "bucket_summary": [],
            }
        ),
        encoding="utf-8",
    )
    context = runtime_mod.build_scalp_entry_adm_runtime_context(
        prompt_profile="watching",
        ws_data={
            "latest_strength": 70,
            "buy_pressure": 35,
            "quote_age_ms": 300,
            "curr": 10000,
            "volume": 100000,
            "intraday_range_pct": 19.0,
            "distance_from_day_high_pct": -0.3,
            "best_ask": 10010,
        },
        advisory_enabled=True,
        now=datetime(2026, 5, 18, 16, 30),
        ai_score=78,
    )
    assert context["applied"] is False
    assert context["prompt_context"] == ""


def test_scalp_entry_adm_unknown_bucket_summary_splits_context_root_causes():
    summary = mod._unknown_bucket_summary(
        [
            {
                "stage": "scalp_entry_action_decision_snapshot",
                "stock_code": "111111",
                "risk_context_bucket": "risk_unknown",
                "price_resolution_bucket": "quote_based",
                "score_bucket": "score65_74",
                "bucket_field_provenance": {"risk_context_bucket": "raw_recomputed"},
            },
            {
                "stage": "holding",
                "stock_code": "222222",
                "risk_context_bucket": "neutral_strength_momentum",
                "price_resolution_bucket": "price_unknown",
                "score_bucket": "score_not_available",
                "bucket_field_provenance": {
                    "price_resolution_bucket": "raw_recomputed"
                },
            },
        ]
    )

    assert (
        summary["unknown_root_cause_counts"]["risk_context_bucket:source_field_missing"]
        == 1
    )
    assert (
        summary["unknown_root_cause_counts"][
            "price_resolution_bucket:post_submit_or_exit_not_required"
        ]
        == 1
    )
    assert summary["unknown_root_cause_detail_counts"] == {
        "risk_context_bucket:source_field_missing": 1,
        "price_resolution_bucket:post_submit_or_exit_not_required": 1,
    }
    assert summary["unknown_resolution_route_counts"] == {
        "source_field_missing": 1,
        "post_submit_or_exit_not_required": 1,
    }
    assert summary["source_quality_gate"] == "source_quality_blocker"
    assert summary["recommended_route"] == "source_quality_workorder"
    assert summary["actionable_unknown_route_counts"] == {
        "risk_context_bucket:source_field_missing": 1,
    }
    assert not any(
        "risk_context_source_missing" in key
        for key in summary["unknown_root_cause_counts"]
    )
    assert not any(
        "price_context_source_missing" in key
        for key in summary["unknown_root_cause_counts"]
    )


def test_entry_adm_clean_baseline_cumulative_join_floor_uses_exact_lineage(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "ADM_REPORT_DIR", tmp_path)
    monkeypatch.setattr(
        mod,
        "clean_baseline_policy",
        lambda: {"clean_tuning_baseline_date": "2026-06-05"},
    )
    prior_rows = [
        {
            "candidate_id": f"ADM-{index}",
            "stock_code": f"{index:06d}",
            "outcome_joined": True,
            "profit_rate": 0.1,
        }
        for index in range(20)
    ]
    (tmp_path / "scalp_entry_action_decision_matrix_2026-08-21.json").write_text(
        json.dumps({"rows": prior_rows}), encoding="utf-8"
    )

    summary = mod._joined_sample_cumulative_summary("2026-08-24", [])

    assert summary["sample_count"] == 20
    assert summary["sample_floor_met"] is True
    assert summary["observed_dates"] == ["2026-08-21"]
    assert summary["runtime_effect"] is False


def test_entry_adm_cumulative_join_floor_excludes_terminal_only_and_dedupes_outcome(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "ADM_REPORT_DIR", tmp_path)
    monkeypatch.setattr(
        mod,
        "clean_baseline_policy",
        lambda: {"clean_tuning_baseline_date": "2026-06-05"},
    )
    current_rows = [
        {
            "stage": "scalp_sim_pre_submit_liquidity_guard_would_block",
            "candidate_id": "ADM-1",
            "sim_record_id": "SCALPSIM-1",
            "post_sell_evaluation_id": "POST-1",
            "stock_code": "005930",
            "outcome_joined": True,
            "profit_rate": 0.1,
        },
        {
            "stage": "scalp_sim_sell_order_assumed_filled",
            "candidate_id": "SCALPSIM-1",
            "sim_record_id": "SCALPSIM-1",
            "post_sell_evaluation_id": "POST-1",
            "stock_code": "005930",
            "outcome_joined": True,
            "profit_rate": 0.1,
        },
    ]

    summary = mod._joined_sample_cumulative_summary("2026-08-24", current_rows)

    assert summary["sample_count"] == 1
    assert summary["sample_floor_met"] is False


def test_entry_adm_backfills_exact_sim_lineage_without_symbol_time_guess():
    rows = [
        {
            "candidate_id": "ADM-005930-R1",
            "entry_adm_candidate_id": "ADM-005930-R1",
            "sim_record_id": "SCALPSIM-005930-1",
        },
        {
            "candidate_id": "ADM-005930-R1",
            "entry_adm_candidate_id": "ADM-005930-R1",
            "sim_record_id": "",
        },
        {
            "candidate_id": "SCALPSIM-005930-1",
            "entry_adm_candidate_id": "",
            "sim_record_id": "SCALPSIM-005930-1",
        },
        {
            "candidate_id": "ADM-005930-OTHER",
            "entry_adm_candidate_id": "ADM-005930-OTHER",
            "sim_record_id": "",
        },
    ]

    observations._backfill_sim_lineage(rows)

    assert rows[1]["sim_record_id"] == "SCALPSIM-005930-1"
    assert rows[1]["sim_lineage_backfill_source"] == "exact_entry_adm_candidate_id"
    assert rows[2]["entry_adm_candidate_id"] == "ADM-005930-R1"
    assert rows[3]["sim_record_id"] == ""


def test_entry_adm_revalidation_block_backfills_score_and_canary_context_is_optional():
    score_event = observations._base_row(
        {
            "stage": "blocked_ai_score",
            "stock_code": "005930",
            "record_id": "R1",
            "emitted_at": "2026-08-24T09:00:00+09:00",
            "fields": {"ai_score": 68},
        }
    )
    block_event = observations._base_row(
        {
            "stage": "entry_submit_revalidation_block",
            "stock_code": "005930",
            "record_id": "R1",
            "emitted_at": "2026-08-24T09:00:01+09:00",
            "fields": {"entry_submit_revalidation_block": True},
        }
    )
    canary_event = observations._base_row(
        {
            "stage": "scalp_entry_action_decision_snapshot",
            "stock_code": "000660",
            "record_id": "R2",
            "emitted_at": "2026-08-24T09:01:00+09:00",
            "fields": {
                "source_stage": "entry_price_canary_submit_block",
                "chosen_action": "SKIP_PRE_SUBMIT_SAFETY",
            },
        }
    )

    observations._backfill_score_context(
        [block_event], source_rows=[score_event, block_event]
    )

    assert block_event["score_bucket"] == "score65_74"
    assert block_event["score_backfill_match_type"] == "exact_key"
    assert canary_event["risk_context_bucket"] == "risk_context_not_available"
    assert canary_event["price_resolution_bucket"] == ("price_not_available_pre_submit")


def test_scalp_entry_adm_non_actionable_context_unknown_does_not_create_source_quality_workorder():
    summary = mod._unknown_bucket_summary(
        [
            {
                "stage": "holding",
                "stock_code": "222222",
                "risk_context_bucket": "risk_unknown",
                "price_resolution_bucket": "price_unknown",
                "score_bucket": "score_not_available",
                "bucket_field_provenance": {
                    "risk_context_bucket": "raw_recomputed",
                    "price_resolution_bucket": "raw_recomputed",
                },
            }
        ]
    )

    assert summary["affected_rows"] == 1
    assert summary["source_quality_gate"] == "classified_non_actionable"
    assert summary["recommended_route"] == "classified_not_applicable_no_workorder"
    assert summary["actionable_unknown_route_counts"] == {}
    assert summary["unknown_resolution_route_counts"] == {
        "post_submit_or_exit_not_required": 2
    }


def test_scalp_entry_adm_explicit_runtime_block_context_is_not_available():
    row = observations._base_row(
        {
            "stage": "scalp_entry_action_decision_snapshot",
            "stock_code": "950260",
            "record_id": "R1",
            "emitted_at": "2026-08-25T12:08:32+09:00",
            "fields": {
                "source_stage": "real_weak_ai_micro_entry_block",
                "chosen_action": "NO_BUY_AI",
                "buy_pressure_10t": "not_evaluated_runtime_block",
            },
        }
    )

    assert row["risk_context_bucket"] == "risk_context_not_available"
    summary = mod._unknown_bucket_summary([row])
    assert "risk_context_bucket" not in summary["dimension_counts"]
    assert summary["not_available_dimension_counts"]["risk_context_bucket"] == 1


def test_entry_price_skip_followup_cumulative_uses_clean_daily_reports(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "report" / "scalp_entry_action_decision_matrix"
    report_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "ADM_REPORT_DIR", report_dir)

    prior_rows = []
    for index in range(20):
        prior_rows.append(
            {
                "stage": "scalp_sim_entry_ai_price_skip_order",
                "stock_code": f"{index:06d}",
                "sim_record_id": f"SIM-{index}",
                "entry_price_skip_followup_30s_mfe_bps": 40.0 + index,
                "entry_price_skip_followup_30s_mae_bps": -10.0,
                "entry_price_skip_followup_90s_mfe_bps": 80.0 + index,
                "entry_price_skip_followup_90s_mae_bps": -20.0,
            }
        )
    prior_rows.append(
        {
            "stage": "scalp_sim_entry_ai_price_skip_order",
            "stock_code": "999999",
            "sim_record_id": "SIM-NAN",
            "entry_price_skip_followup_90s_mfe_bps": float("nan"),
            "entry_price_skip_followup_90s_mae_bps": -20.0,
        }
    )
    (report_dir / "scalp_entry_action_decision_matrix_2026-07-30.json").write_text(
        json.dumps({"rows": prior_rows}), encoding="utf-8"
    )
    (report_dir / "scalp_entry_action_decision_matrix_2026-06-04.json").write_text(
        json.dumps({"rows": prior_rows}), encoding="utf-8"
    )

    summary = mod._entry_price_skip_followup_cumulative_summary("2026-07-31", [])

    assert summary["status"] == "ready_for_offline_counterfactual_review"
    assert summary["sample_floor_met"] is True
    assert summary["intervals"]["90s"] == {
        "mature_paired_sample_count": 20,
        "equal_weight_avg_mfe_bps": 89.5,
        "equal_weight_avg_mae_bps": -20.0,
    }
    assert summary["provenance"]["source_dates"] == ["2026-07-30"]
    assert summary["runtime_effect"] is False
    assert summary["allowed_runtime_apply"] is False
    assert summary["max_runtime_apply_count"] == 0


def test_entry_price_skip_followup_cumulative_blocks_pre_clean_baseline_current_rows(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        mod,
        "ADM_REPORT_DIR",
        tmp_path / "report" / "scalp_entry_action_decision_matrix",
    )
    current_rows = [
        {
            "stage": "scalp_sim_entry_ai_price_skip_order",
            "stock_code": "005930",
            "sim_record_id": "SIM-1",
            "entry_price_skip_followup_90s_mfe_bps": 100.0,
            "entry_price_skip_followup_90s_mae_bps": -10.0,
        }
        for _ in range(20)
    ]

    summary = mod._entry_price_skip_followup_cumulative_summary(
        "2026-06-04", current_rows
    )

    assert summary["status"] == "source_quality_blocked_pre_clean_baseline"
    assert summary["candidate_count"] == 0
    assert summary["sample_floor_met"] is False
    assert summary["provenance"]["target_date_allowed"] is False


def test_scalp_entry_adm_runtime_pre_submit_missing_context_is_not_available():
    context = runtime_mod.build_scalp_entry_adm_runtime_context(
        prompt_profile="watching",
        ws_data={
            "stage": "latency_block",
            "current_ai_score": 66,
        },
        now=datetime(2026, 5, 18, 9, 10),
        advisory_enabled=False,
    )
    fields = context["fields"]

    assert fields["entry_adm_risk_context_bucket"] == "risk_context_not_available"
    assert (
        fields["entry_adm_price_resolution_bucket"] == "price_not_available_pre_submit"
    )


def test_scalp_entry_adm_hypothesis_force_requires_explicit_flag(tmp_path, monkeypatch):
    report_dir = tmp_path / "report" / "scalp_entry_action_decision_matrix"
    report_dir.mkdir(parents=True)
    monkeypatch.setattr(runtime_mod, "ADM_DIR", report_dir)
    monkeypatch.setattr(
        runtime_mod,
        "TRADING_RULES",
        replace(
            runtime_mod.TRADING_RULES,
            SCALP_ENTRY_ADM_RUNTIME_BIAS_ENABLED=True,
            SCALP_ENTRY_ADM_HYPOTHESIS_FORCE_ENABLED=True,
        ),
    )
    (report_dir / "scalp_entry_action_decision_matrix_2026-05-18.json").write_text(
        json.dumps(
            {
                "date": "2026-05-18",
                "matrix_version": "scalp_entry_adm_v1_2026-05-18",
                "bucket_summary": [],
            }
        ),
        encoding="utf-8",
    )
    context = runtime_mod.build_scalp_entry_adm_runtime_context(
        prompt_profile="watching",
        ws_data={
            "latest_strength": 70,
            "buy_pressure": 35,
            "quote_age_ms": 300,
            "curr": 10000,
            "volume": 100000,
            "intraday_range_pct": 19.0,
            "distance_from_day_high_pct": -0.3,
            "best_ask": 10010,
        },
        advisory_enabled=True,
        now=datetime(2026, 5, 18, 16, 30),
        ai_score=78,
    )
    assert context["applied"] is False
    assert context["prompt_context"] == ""


def test_adm_bucket_lookup_status_matched_prior_bucket():
    from src.engine.scalp_entry_adm_runtime import _bucket_lookup_status

    payload = {
        "bucket_summary": [
            {"bucket_token": "tk", "sample_count": 114, "joined_sample": 32}
        ]
    }
    matched = {"bucket_token": "tk", "sample_count": 114, "joined_sample": 32}
    assert _bucket_lookup_status(payload, matched) == "matched_prior_bucket"


def test_adm_bucket_lookup_status_new_or_unseen_token():
    from src.engine.scalp_entry_adm_runtime import _bucket_lookup_status

    payload = {"bucket_summary": [{"bucket_token": "other"}]}
    assert _bucket_lookup_status(payload, {}) == "new_or_unseen_token_vs_prior_adm"


def test_adm_bucket_lookup_status_prior_bucket_missing_sample():
    from src.engine.scalp_entry_adm_runtime import _bucket_lookup_status

    payload = {
        "bucket_summary": [
            {"bucket_token": "tk", "sample_count": 0, "joined_sample": 0}
        ]
    }
    matched = {"bucket_token": "tk", "sample_count": 0, "joined_sample": 0}
    assert (
        _bucket_lookup_status(payload, matched)
        == "prior_bucket_present_but_runtime_sample_missing"
    )


def test_adm_bucket_lookup_status_no_payload():
    from src.engine.scalp_entry_adm_runtime import _bucket_lookup_status

    assert _bucket_lookup_status({}, {}) == "bucket_lookup_not_performed"


def test_adm_lookup_none_is_classified_for_advisory_only_stage():
    from src.engine.lifecycle.archive.scalp_entry_action_decision_matrix_readers import (
        _classify_adm_lookup_not_applicable,
    )

    rows = [
        {
            "stage": "ai_confirmed",
            "entry_adm_bucket_token": "score50_64|weak_strength_momentum|-|fresh",
            "entry_adm_bucket_token_recomputed": "score50_64|weak_strength_momentum|-|fresh",
            "entry_adm_bucket_lookup_status": "",
        },
        {
            "stage": "scalp_entry_action_decision_snapshot",
            "entry_adm_bucket_token": "score65_74|weak_strength_momentum|-|fresh",
            "entry_adm_bucket_lookup_status": "",
        },
    ]

    _classify_adm_lookup_not_applicable(rows)

    assert (
        rows[0]["entry_adm_bucket_lookup_status"]
        == "advisory_only_stage_without_prior_lookup"
    )
    assert rows[0]["entry_adm_bucket_joined_sample"] == 0
    assert rows[1]["entry_adm_bucket_lookup_status"] == ""


def test_adm_lookup_closure_splits_new_bucket_and_producer_context_missing():
    from src.engine.lifecycle.archive.scalp_entry_action_decision_matrix_readers import (
        _adm_lookup_closure_summary,
    )

    rows = [
        {
            "stage": "scalp_entry_action_decision_snapshot",
            "entry_adm_bucket_lookup_status": "new_or_unseen_token_vs_prior_adm",
            "entry_adm_bucket_token_recomputed": "score70p|strong|-|fresh|quote_based|liquidity_high",
        },
        {
            "stage": "blocked_ai_score",
            "entry_adm_bucket_lookup_status": "new_or_unseen_token_vs_prior_adm",
            "entry_adm_bucket_token_recomputed": "score50_64|weak|-|fresh|price_not_available_pre_submit|liquidity_not_available",
        },
        {
            "stage": "ai_confirmed",
            "entry_adm_bucket_lookup_status": "new_or_unseen_token_vs_prior_adm",
            "entry_adm_bucket_token_recomputed": "score50_64|weak|-|fresh|quote_based|liquidity_mid",
        },
    ]

    summary = _adm_lookup_closure_summary(rows)

    assert summary["closure_status"] == "closed_with_producer_followup"
    assert summary["followup_required"] is True
    assert summary["status_counts"] == {
        "new_bucket_candidate_waiting_prior_rollup": 1,
        "producer_context_missing": 1,
        "advisory_or_not_applicable_stage": 1,
    }
    assert summary["producer_context_missing_counts"] == {
        "price_not_available_pre_submit": 1,
        "liquidity_not_available": 1,
    }


def test_retired_current_producer_preserves_prior_and_has_no_authority(
    tmp_path, monkeypatch, capsys
):
    import importlib

    current = importlib.import_module("src.engine.scalp_entry_action_decision_matrix")
    prior = tmp_path / "prior.json"
    prior.write_text("original")

    def forbidden(*a, **kw):
        raise AssertionError("retired producer accessed storage")

    monkeypatch.setattr(type(prior), "write_text", forbidden)
    monkeypatch.setattr(type(prior), "read_text", forbidden)
    result = current.build_scalp_entry_action_decision_matrix_report("2026-10-12")
    assert result["status"] == "retired" and result["allowed_runtime_apply"] is False
    assert current.render_scalp_entry_action_decision_matrix_markdown(result) == result
    assert current.main([]) == 0
    assert json.loads(capsys.readouterr().out) == result
