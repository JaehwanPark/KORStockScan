import json

from src.engine.monitoring import rising_missed_intraday_feedback as mod


def _event(
    record_id,
    code,
    name,
    stage,
    fields=None,
    emitted_at="2026-07-02T09:00:00",
    pipeline="ENTRY_PIPELINE",
):
    return {
        "pipeline": pipeline,
        "record_id": record_id,
        "stock_code": code,
        "stock_name": name,
        "stage": stage,
        "fields": fields or {},
        "emitted_at": emitted_at,
    }


def test_tp1_label_projection_keeps_only_candidate_symbol_and_global_watermark(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline_events_2026-07-27.jsonl"
    candidate = _event(
        1,
        "000001",
        "candidate",
        "rising_missed_one_share_entry",
        {
            "rising_missed_tp1_selector_active": True,
            "rising_missed_tp1_candidate_allowed": True,
            "rising_missed_tp1_candidate_reason": "rising_missed_tp1_candidate_pass",
            "current_price_observed": 10000,
        },
        emitted_at="2026-07-27T09:00:00+09:00",
    )
    candidate_price = _event(
        1,
        "000001",
        "candidate",
        "holding_observation",
        {"current_price_observed": 10100, "blob": "x" * 10000},
        emitted_at="2026-07-27T09:05:00+09:00",
    )
    irrelevant = _event(
        2,
        "000002",
        "irrelevant",
        "large_unrelated_payload",
        {"current_price_observed": 5000, "blob": "x" * 10000},
        emitted_at="2026-07-27T10:00:00+09:00",
    )
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in (candidate, candidate_price, irrelevant)),
        encoding="utf-8",
    )

    projected, watermark = mod._load_tp1_label_event_projection(pipeline_path)

    assert [row["stock_code"] for row in projected] == ["000001", "000001"]
    assert projected[1]["fields"] == {"current_price_observed": 10100}
    assert watermark.isoformat() == "2026-07-27T10:00:00+09:00"


def test_risky_micro_episode_source_candidates_are_consumed_by_feedback_report(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline_events_2026-08-14.jsonl"
    row = _event(
        "micro-1",
        "475560",
        "THEBORN",
        "risky_micro_episode_source_candidate_observed",
        {
            "risky_micro_episode_status": "recheck_required",
            "risky_micro_episode_reason": "tick_acceleration_confirmation_pending",
            "risky_micro_episode_source_stage": "latency_block",
            "risky_micro_episode_source_block_reason": "wide_spread",
            "risky_micro_episode_best_bid": 16_220,
            "risky_micro_episode_best_ask": 16_310,
            "risky_micro_episode_spread_bps": 55.487,
            "risky_micro_episode_tick_acceleration_ratio": 0.795,
            "risky_micro_episode_tick_window_span_sec": 5.0,
            "risky_micro_episode_positive_micro_support": True,
            "risky_micro_episode_adverse_micro_detected": False,
            "risky_micro_episode_large_sell_detected": False,
            "risky_micro_episode_hypothetical_entry_price": 16_230,
            "risky_micro_episode_hypothetical_target_price": 16_290,
            "risky_micro_episode_gross_target_bps": 33,
            "risky_micro_episode_passive_ttl_sec": 3,
            "risky_micro_episode_max_hold_sec": 20,
            "risky_micro_episode_outcome_join_required": True,
            "risky_micro_episode_outcome_join_status": (
                "pending_executable_fill_and_3_10_20_30_second_path_consumer"
            ),
            "risky_micro_episode_quantity_owner": (
                "position_sizing_dynamic_formula_then_existing_probe_first"
            ),
            "risky_micro_episode_quantity_is_tuning_axis": False,
            "risky_micro_episode_independent_episode_or_widget_owner": False,
        },
        emitted_at="2026-08-14T09:10:00+09:00",
    )
    pipeline_path.write_text(json.dumps(row) + "\n", encoding="utf-8")

    report = mod.build_report("2026-08-14", pipeline_path=pipeline_path)

    assert report["summary"]["risky_micro_episode_observation_count"] == 1
    assert report["summary"]["risky_micro_episode_recheck_required_count"] == 1
    candidate = report["risky_micro_episode_source_candidate_rows"][0]
    assert candidate["stock_code"] == "475560"
    assert candidate["hypothetical_entry_price"] == 16_230
    assert candidate["runtime_effect"] is False
    assert candidate["outcome_join_required"] is True
    assert candidate["quantity_is_tuning_axis"] is False
    assert candidate["independent_episode_or_widget_owner"] is False
    assert candidate["outcome_evaluation_role"] == "diagnostic_recheck_cohort"
    assert report["summary"]["risky_micro_episode_resolved_eligible_episode_count"] == 0
    assert len(report["risky_micro_episode_recheck_diagnostic_rows"]) == 1
    assert (
        report["summary"]["risky_micro_episode_executable_outcome_join_ready"] is False
    )
    assert (
        report["summary"]["risky_micro_episode_outcome_join_consumer_implemented"]
        is True
    )
    assert report["summary"]["risky_micro_episode_source_coverage_complete"] is False
    assert (
        "entry_ai"
        in report["summary"]["risky_micro_episode_unobserved_source_categories"]
    )
    assert report["summary"]["risky_micro_episode_tick_context_gap_reason_counts"] == []


def test_risky_micro_report_preserves_tick_context_gap_owner(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-08-14.jsonl"
    row = _event(
        "micro-gap",
        "475560",
        "THEBORN",
        "risky_micro_episode_source_candidate_observed",
        {
            "risky_micro_episode_status": "source_quality_blocked",
            "risky_micro_episode_reason": "tick_context_missing",
            "risky_micro_episode_source_stage": "latency_block",
            "risky_micro_episode_instrumentation_gap": "tick_context_missing",
            "risky_micro_episode_tick_context_gap_reason": (
                "tp1_signed_tick_sample_floor_not_met"
            ),
            "risky_micro_episode_tick_context_tp1_sample_count": 4,
            "risky_micro_episode_tick_context_tp1_age_sec": 0.2,
            "risky_micro_episode_tick_context_tp1_source": (
                "trusted_ws_signed_0b_10tick_received_ts"
            ),
            "risky_micro_episode_best_bid": 16_220,
            "risky_micro_episode_best_ask": 16_310,
            "risky_micro_episode_quote_age_ms": 100,
        },
        emitted_at="2026-08-14T09:10:00+09:00",
    )
    pipeline_path.write_text(json.dumps(row) + "\n", encoding="utf-8")

    report = mod.build_report("2026-08-14", pipeline_path=pipeline_path)

    candidate = report["risky_micro_episode_source_candidate_rows"][0]
    assert candidate["tick_context_gap_reason"] == (
        "tp1_signed_tick_sample_floor_not_met"
    )
    assert candidate["tick_context_tp1_sample_count"] == 4
    assert report["summary"]["risky_micro_episode_tick_context_gap_reason_counts"] == [
        {"reason": "tp1_signed_tick_sample_floor_not_met", "count": 1}
    ]


def test_risky_micro_episode_joins_passive_fill_and_executable_short_path(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-08-14.jsonl"
    candidate = _event(
        "micro-2",
        "475560",
        "THEBORN",
        "risky_micro_episode_source_candidate_observed",
        {
            "risky_micro_episode_status": "source_only_candidate",
            "risky_micro_episode_reason": "fresh_passive_cost_aware_episode_candidate",
            "risky_micro_episode_source_stage": "latency_block",
            "risky_micro_episode_source_block_reason": "wide_spread",
            "risky_micro_episode_best_bid": 16_220,
            "risky_micro_episode_best_ask": 16_310,
            "risky_micro_episode_quote_age_ms": 100,
            "risky_micro_episode_hypothetical_entry_price": 16_230,
            "risky_micro_episode_hypothetical_target_price": 16_290,
            "risky_micro_episode_hypothetical_adverse_price": 16_170,
            "risky_micro_episode_gross_target_bps": 33,
            "risky_micro_episode_adverse_limit_bps": 33,
            "risky_micro_episode_conservative_total_cost_bps": 23,
            "risky_micro_episode_passive_ttl_sec": 3,
            "risky_micro_episode_max_hold_sec": 20,
            "risky_micro_episode_outcome_join_required": True,
            "effective_venue": "KRX",
            "market_session_bucket": "krx_regular",
            "risky_micro_episode_horizon_observer_registered": True,
            "risky_micro_episode_horizon_observer_status": "registered",
            "risky_micro_episode_horizon_observer_registration_key": (
                "475560|KRX|KRX_REGULAR"
            ),
        },
        emitted_at="2026-08-14T09:10:00+09:00",
    )

    def bbo(second, bid, ask):
        return _event(
            "micro-2",
            "475560",
            "THEBORN",
            "risky_micro_episode_executable_bbo_observed",
            {
                "market_data_effective_best_bid": bid,
                "market_data_effective_best_ask": ask,
                "market_data_effective_quote_age_ms": 100,
                "effective_venue": "KRX",
                "market_session_bucket": "krx_regular",
                "risky_micro_episode_horizon_observer_quote_fresh": True,
            },
            emitted_at=f"2026-08-14T09:10:{second:02d}+09:00",
        )

    rows = [
        candidate,
        bbo(2, 16_220, 16_230),
        bbo(5, 16_240, 16_250),
        bbo(12, 16_290, 16_300),
        bbo(22, 16_300, 16_310),
        bbo(32, 16_310, 16_320),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows),
        encoding="utf-8",
    )

    report = mod.build_report("2026-08-14", pipeline_path=pipeline_path)

    outcome = report["risky_micro_episode_source_candidate_rows"][0]
    assert outcome["fill_feasible"] is True
    assert outcome["outcome_join_status"] == "resolved_target_first"
    assert outcome["net_return_bps"] > 0
    assert [item["horizon_sec"] for item in outcome["horizons"]] == [3, 10, 20, 30]
    assert [item["entry_profile"] for item in outcome["entry_profile_outcomes"]] == [
        "bid_plus_one_ttl_3s",
        "bid_plus_one_ttl_5s",
        "bid_plus_one_ttl_10s",
        "limited_ask_ttl_3s_spread_le_15bps",
    ]
    assert outcome["entry_profile_outcomes"][-1]["entry_profile_eligible"] is False
    assert all(
        item["runtime_effect"] is False
        and item["allowed_runtime_apply"] is False
        and item["actual_order_submitted"] is False
        and item["broker_order_forbidden"] is True
        for item in outcome["entry_profile_outcomes"]
    )
    assert report["summary"]["risky_micro_episode_resolved_eligible_episode_count"] == 1
    assert (
        report["summary"][
            "risky_micro_episode_horizon_observer_registered_candidate_count"
        ]
        == 1
    )
    assert report["summary"]["risky_micro_episode_horizon_observer_event_count"] == 5
    assert (
        report["summary"]["risky_micro_episode_horizon_observer_fresh_bbo_event_count"]
        == 5
    )
    assert (
        report["summary"]["risky_micro_episode_executable_outcome_join_ready"] is True
    )
    assert (
        report["summary"]["risky_micro_episode_daily_source_quality_adjusted_ev_pct"]
        > 0
    )
    assert (
        report["summary"]["risky_micro_episode_source_quality_adjusted_ev_pct"] is None
    )
    assert (
        report["summary"]["risky_micro_episode_ev_decision_authority"]
        == "rolling_source_only_sample_floor_pending_no_runtime_apply"
    )
    outcome_contract = report["metric_contracts"][
        "risky_micro_episode_executable_outcome"
    ]
    assert outcome_contract["decision_authority"] == "source_only_no_runtime_apply"
    assert "official_route_depth_proof" in outcome_contract["source_quality_gate"]
    assert "cross_venue_outcome_join" in outcome_contract["forbidden_uses"]
    observer_contract = report["metric_contracts"][
        "risky_micro_episode_bounded_bbo_observer"
    ]
    assert "depth_proven_venue" in observer_contract["window_policy"]
    assert "official_route_depth_proof" in observer_contract["source_quality_gate"]
    output_json = tmp_path / "report.json"
    output_md = tmp_path / "report.md"
    mod.write_outputs(report, output_json=output_json, output_md=output_md)
    markdown = output_md.read_text(encoding="utf-8")
    assert "risky_micro_episode_unobserved_source_categories" in markdown
    assert "outcome_join=resolved_target_first" in markdown
    assert "venue=KRX session=KRX_REGULAR" in markdown


def test_risky_micro_episode_normalizes_mixed_naive_and_aware_timestamps(tmp_path):
    target_date = "2026-08-14"
    pipeline_path = tmp_path / f"pipeline_events_{target_date}.jsonl"
    candidate_fields = {
        "risky_micro_episode_status": "source_only_candidate",
        "risky_micro_episode_reason": "fresh_passive_cost_aware_episode_candidate",
        "risky_micro_episode_source_stage": "latency_block",
        "risky_micro_episode_best_bid": 10_000,
        "risky_micro_episode_best_ask": 10_020,
        "risky_micro_episode_quote_age_ms": 100,
        "risky_micro_episode_hypothetical_entry_price": 10_010,
        "risky_micro_episode_hypothetical_target_price": 10_040,
        "risky_micro_episode_hypothetical_adverse_price": 9_970,
        "risky_micro_episode_conservative_total_cost_bps": 23,
        "risky_micro_episode_passive_ttl_sec": 3,
        "risky_micro_episode_max_hold_sec": 20,
        "effective_venue": "KRX",
        "market_session_bucket": "krx_regular",
    }
    rows = [
        {
            "ts": f"{target_date}T09:00:00",
            "stage": "risky_micro_episode_source_candidate_observed",
            "code": "000001",
            "fields": candidate_fields,
        },
        {
            "ts": f"{target_date}T09:00:01+09:00",
            "stage": "market_data_observed",
            "code": "000001",
            "fields": {
                "market_data_effective_best_bid": 10_000,
                "market_data_effective_best_ask": 10_010,
                "market_data_effective_quote_age_ms": 10,
                "effective_venue": "KRX",
                "market_session_bucket": "krx_regular",
            },
        },
        {
            "ts": f"{target_date}T09:00:21+09:00",
            "stage": "market_data_observed",
            "code": "000001",
            "fields": {
                "market_data_effective_best_bid": 10_050,
                "market_data_effective_best_ask": 10_060,
                "market_data_effective_quote_age_ms": 10,
                "effective_venue": "KRX",
                "market_session_bucket": "krx_regular",
            },
        },
    ]
    pipeline_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )

    summary, outcomes = mod._build_risky_micro_episode_source_candidates(pipeline_path)

    outcome = outcomes[0]
    assert outcome["outcome_join_status"] == "resolved_target_first"
    assert outcome["decision_authority"] == "source_only_no_runtime_apply"
    assert summary["risky_micro_episode_resolved_eligible_episode_count"] == 1


def test_risky_micro_episode_compares_limited_ask_only_below_15bps(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-08-14.jsonl"
    candidate = _event(
        "micro-narrow",
        "000010",
        "narrow",
        "risky_micro_episode_source_candidate_observed",
        {
            "risky_micro_episode_status": "source_only_candidate",
            "risky_micro_episode_reason": "fresh_passive_cost_aware_episode_candidate",
            "risky_micro_episode_source_stage": "latency_block",
            "risky_micro_episode_best_bid": 10_000,
            "risky_micro_episode_best_ask": 10_010,
            "risky_micro_episode_quote_age_ms": 10,
            "risky_micro_episode_spread_bps": 10,
            "risky_micro_episode_hypothetical_entry_price": 10_000,
            "risky_micro_episode_hypothetical_target_price": 10_040,
            "risky_micro_episode_hypothetical_adverse_price": 9_970,
            "risky_micro_episode_gross_target_bps": 33,
            "risky_micro_episode_adverse_limit_bps": 33,
            "risky_micro_episode_conservative_total_cost_bps": 23,
            "risky_micro_episode_passive_ttl_sec": 3,
            "risky_micro_episode_max_hold_sec": 20,
            "effective_venue": "KRX",
            "market_session_bucket": "krx_regular",
        },
        emitted_at="2026-08-14T09:00:00+09:00",
    )
    terminal = _event(
        "micro-narrow",
        "000010",
        "narrow",
        "market_data_observed",
        {
            "market_data_effective_best_bid": 10_050,
            "market_data_effective_best_ask": 10_060,
            "market_data_effective_quote_age_ms": 10,
            "effective_venue": "KRX",
            "market_session_bucket": "krx_regular",
        },
        emitted_at="2026-08-14T09:00:20+09:00",
    )
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in (candidate, terminal)),
        encoding="utf-8",
    )

    _, outcomes = mod._build_risky_micro_episode_source_candidates(pipeline_path)

    profiles = {
        item["entry_profile"]: item for item in outcomes[0]["entry_profile_outcomes"]
    }
    ask_profile = profiles["limited_ask_ttl_3s_spread_le_15bps"]
    assert ask_profile["entry_profile_eligible"] is True
    assert ask_profile["fill_feasible"] is True
    assert ask_profile["entry_profile_promotion_ev_included"] is False
    assert (
        profiles["bid_plus_one_ttl_3s"]["entry_profile_promotion_ev_included"] is True
    )


def test_risky_micro_rolling_keeps_recheck_out_of_promotion_ev():
    row = {
        "ts": "2026-08-14T09:00:00+09:00",
        "stock_code": "000010",
        "effective_venue": "KRX",
        "market_session_bucket": "KRX_REGULAR",
        "status": "recheck_required",
        "policy_version": mod.RISKY_MICRO_POLICY_VERSION,
        "entry_profile": mod.RISKY_MICRO_PRIMARY_ENTRY_PROFILE,
        "outcome_join_status": "resolved_target_first",
        "fill_feasible": True,
        "net_return_bps": 100,
        "entry_profile_promotion_ev_included": True,
    }

    assert mod._risky_micro_daily_rolling_eligible_rows("2026-08-14", [row]) == []


def test_risky_micro_episode_never_joins_cross_venue_bbo(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-08-14.jsonl"
    candidate = _event(
        "micro-venue",
        "475560",
        "THEBORN",
        "risky_micro_episode_source_candidate_observed",
        {
            "risky_micro_episode_status": "source_only_candidate",
            "risky_micro_episode_reason": "fresh_passive_cost_aware_episode_candidate",
            "risky_micro_episode_source_stage": "latency_block",
            "risky_micro_episode_hypothetical_entry_price": 10_010,
            "risky_micro_episode_hypothetical_target_price": 10_040,
            "risky_micro_episode_hypothetical_adverse_price": 9_970,
            "risky_micro_episode_conservative_total_cost_bps": 23,
            "risky_micro_episode_passive_ttl_sec": 3,
            "risky_micro_episode_max_hold_sec": 20,
            "effective_venue": "KRX",
            "market_session_bucket": "krx_regular",
        },
        emitted_at="2026-08-14T09:00:00+09:00",
    )
    nxt_bbo = _event(
        "micro-venue",
        "475560",
        "THEBORN",
        "market_data_observed",
        {
            "market_data_effective_best_bid": 10_000,
            "market_data_effective_best_ask": 10_010,
            "market_data_effective_quote_age_ms": 10,
            "effective_venue": "NXT",
            "market_session_bucket": "nxt_regular",
        },
        emitted_at="2026-08-14T09:00:01+09:00",
    )
    watermark = _event(
        "watermark",
        "475560",
        "THEBORN",
        "market_data_observed",
        {},
        emitted_at="2026-08-14T09:00:10+09:00",
    )
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in (candidate, nxt_bbo, watermark)),
        encoding="utf-8",
    )

    summary, outcomes = mod._build_risky_micro_episode_source_candidates(pipeline_path)

    assert outcomes[0]["outcome_join_status"] == "pending_fill_horizon"
    assert outcomes[0]["matching_fresh_bbo_observation_count"] == 0
    assert outcomes[0]["matching_fresh_bbo_watermark"] is None
    assert (
        outcomes[0]["outcome_instrumentation_gap"] == "fresh_bbo_fill_horizon_missing"
    )
    assert outcomes[0]["outcome_instrumentation_gap_matured"] is True
    assert summary["risky_micro_episode_matured_pending_outcome_gap_count"] == 1
    assert summary["risky_micro_episode_matured_pending_outcome_gap_counts"] == [
        {"gap": "fresh_bbo_fill_horizon_missing", "count": 1}
    ]


def test_risky_micro_episode_resolves_not_filled_only_with_matching_bbo_watermark(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline_events_2026-08-14.jsonl"
    candidate = _event(
        "micro-no-fill",
        "475560",
        "THEBORN",
        "risky_micro_episode_source_candidate_observed",
        {
            "risky_micro_episode_status": "source_only_candidate",
            "risky_micro_episode_reason": "fresh_passive_cost_aware_episode_candidate",
            "risky_micro_episode_source_stage": "latency_block",
            "risky_micro_episode_hypothetical_entry_price": 10_010,
            "risky_micro_episode_hypothetical_target_price": 10_040,
            "risky_micro_episode_hypothetical_adverse_price": 9_970,
            "risky_micro_episode_conservative_total_cost_bps": 23,
            "risky_micro_episode_passive_ttl_sec": 3,
            "risky_micro_episode_max_hold_sec": 20,
            "effective_venue": "KRX",
            "market_session_bucket": "krx_regular",
        },
        emitted_at="2026-08-14T09:00:00+09:00",
    )
    matching_bbo = _event(
        "micro-no-fill",
        "475560",
        "THEBORN",
        "market_data_observed",
        {
            "market_data_effective_best_bid": 10_020,
            "market_data_effective_best_ask": 10_030,
            "market_data_effective_quote_age_ms": 10,
            "effective_venue": "KRX",
            "market_session_bucket": "krx_regular",
        },
        emitted_at="2026-08-14T09:00:04+09:00",
    )
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in (candidate, matching_bbo)),
        encoding="utf-8",
    )

    _, outcomes = mod._build_risky_micro_episode_source_candidates(pipeline_path)

    assert outcomes[0]["outcome_join_status"] == "resolved_not_filled"
    assert outcomes[0]["matching_fresh_bbo_observation_count"] == 1
    assert outcomes[0]["matching_fresh_bbo_watermark"] == ("2026-08-14T09:00:04+09:00")


def test_risky_micro_episode_derives_tp1_block_source_without_runtime_authority(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline_events_2026-08-14.jsonl"
    tp1_block = _event(
        "tp1-derived",
        "475560",
        "THEBORN",
        "rising_missed_tp1_candidate_blocked",
        {
            "forced_entry_reason": "rising_missed_one_share_entry",
            "rising_missed_tp1_evaluation_id": "tp1-eval-1",
            "rising_missed_tp1_candidate_reason": (
                "rising_missed_tp1_lane_not_eligible"
            ),
            "rising_missed_tp1_positive_support_count": 2,
            "rising_missed_tp1_true_ofi_ewma": 0.1,
            "rising_missed_tp1_top_depth_ratio": 1.5,
            "rising_missed_tp1_tick_acceleration": 1.2,
            "rising_missed_tp1_tick_acceleration_fresh": True,
            "rising_missed_tp1_ws_momentum_window_span_sec": 5,
            "rising_missed_tp1_hard_negative_reasons": "-",
            "market_data_effective_best_bid": 10_000,
            "market_data_effective_best_ask": 10_020,
            "market_data_effective_quote_age_ms": 20,
            "rising_missed_effective_venue": "KRX",
            "rising_missed_market_session_bucket": "krx_regular",
        },
        emitted_at="2026-08-14T09:00:00+09:00",
    )
    fill = _event(
        "tp1-derived",
        "475560",
        "THEBORN",
        "market_data_observed",
        {
            "market_data_effective_best_bid": 10_000,
            "market_data_effective_best_ask": 10_010,
            "market_data_effective_quote_age_ms": 20,
            "effective_venue": "KRX",
            "market_session_bucket": "krx_regular",
        },
        emitted_at="2026-08-14T09:00:01+09:00",
    )
    target = _event(
        "tp1-derived",
        "475560",
        "THEBORN",
        "market_data_observed",
        {
            "market_data_effective_best_bid": 10_050,
            "market_data_effective_best_ask": 10_060,
            "market_data_effective_quote_age_ms": 20,
            "effective_venue": "KRX",
            "market_session_bucket": "krx_regular",
        },
        emitted_at="2026-08-14T09:00:10+09:00",
    )
    watermark = _event(
        "tp1-derived",
        "475560",
        "THEBORN",
        "market_data_observed",
        {},
        emitted_at="2026-08-14T09:00:31+09:00",
    )
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in (tp1_block, fill, target, watermark)),
        encoding="utf-8",
    )

    summary, outcomes = mod._build_risky_micro_episode_source_candidates(pipeline_path)

    derived = next(row for row in outcomes if row["source_category"] == "tp1")
    assert derived["source_projection_origin"] == (
        "postclose_existing_block_event_adapter"
    )
    assert derived["outcome_join_status"] == "resolved_target_first"
    assert derived["runtime_effect"] is False
    assert derived["broker_order_forbidden"] is True
    assert summary["risky_micro_episode_source_instrumentation_complete"] is True
    assert "tp1" not in summary["risky_micro_episode_natural_sample_absent_categories"]


def test_risky_micro_tp1_adapter_preserves_insufficient_window_gap_owner(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-08-14.jsonl"
    tp1_block = _event(
        "tp1-insufficient-window",
        "475560",
        "THEBORN",
        "rising_missed_tp1_candidate_blocked",
        {
            "forced_entry_reason": "rising_missed_one_share_entry",
            "rising_missed_tp1_evaluation_id": "tp1-eval-insufficient",
            "rising_missed_tp1_candidate_reason": "tp1_tick_window_pending",
            "rising_missed_tp1_tick_acceleration": 0.0,
            "rising_missed_tp1_tick_acceleration_fresh": False,
            "rising_missed_tp1_tick_acceleration_source": "missing",
            "rising_missed_tp1_ws_tick_acceleration_source": (
                "trusted_ws_signed_0b_insufficient_10tick_window"
            ),
            "market_data_effective_best_bid": 10_000,
            "market_data_effective_best_ask": 10_020,
            "market_data_effective_quote_age_ms": 20,
            "rising_missed_effective_venue": "KRX",
            "rising_missed_market_session_bucket": "krx_regular",
        },
        emitted_at="2026-08-14T09:00:00+09:00",
    )
    pipeline_path.write_text(json.dumps(tp1_block) + "\n", encoding="utf-8")

    summary, outcomes = mod._build_risky_micro_episode_source_candidates(pipeline_path)

    derived = outcomes[0]
    assert derived["tick_context_gap_reason"] == (
        "tp1_signed_tick_sample_floor_not_met"
    )
    assert derived["tick_context_tp1_source"] == (
        "trusted_ws_signed_0b_insufficient_10tick_window"
    )
    assert derived["tick_context_tp1_sample_count"] == "-"
    assert summary["risky_micro_episode_tick_context_gap_reason_counts"] == [
        {"reason": "tp1_signed_tick_sample_floor_not_met", "count": 1}
    ]


def test_risky_micro_tp1_adapter_preserves_submit_context_sample_floor(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-08-14.jsonl"
    tp1_block = _event(
        "tp1-submit-context-floor",
        "475560",
        "THEBORN",
        "rising_missed_tp1_candidate_deferred",
        {
            "forced_entry_reason": "rising_missed_one_share_entry",
            "rising_missed_tp1_evaluation_id": "tp1-eval-submit-floor",
            "rising_missed_tp1_candidate_reason": "tp1_tick_window_pending",
            "rising_missed_tp1_submit_context_tick_acceleration": 0.5,
            "rising_missed_tp1_submit_context_tick_window_span_sec": 1.2,
            "rising_missed_tp1_submit_context_tick_acceleration_fresh": False,
            "rising_missed_tp1_submit_context_tick_window_sample_count": 4,
            "rising_missed_tp1_submit_context_tick_acceleration_age_sec": 0.2,
            "rising_missed_tp1_submit_context_tick_acceleration_source": (
                "trusted_ws_signed_0b_10tick_received_ts"
            ),
            "market_data_effective_best_bid": 10_000,
            "market_data_effective_best_ask": 10_020,
            "market_data_effective_quote_age_ms": 20,
            "rising_missed_effective_venue": "KRX",
            "rising_missed_market_session_bucket": "krx_regular",
        },
        emitted_at="2026-08-14T09:00:00+09:00",
    )
    pipeline_path.write_text(json.dumps(tp1_block) + "\n", encoding="utf-8")

    _, outcomes = mod._build_risky_micro_episode_source_candidates(pipeline_path)

    derived = outcomes[0]
    assert derived["tick_context_gap_reason"] == (
        "tp1_signed_tick_sample_floor_not_met"
    )
    assert derived["tick_context_tp1_sample_count"] == 4
    assert derived["tick_context_tp1_age_sec"] == 0.2
    assert derived["tick_context_tp1_source"] == (
        "trusted_ws_signed_0b_10tick_received_ts"
    )


def test_risky_micro_tp1_adapter_does_not_label_partial_fresh_context_none():
    row = _event(
        "tp1-partial-fresh",
        "475560",
        "THEBORN",
        "rising_missed_tp1_candidate_blocked",
        {
            "forced_entry_reason": "rising_missed_one_share_entry",
            "rising_missed_tp1_evaluation_id": "tp1-eval-partial-fresh",
            "rising_missed_tp1_tick_acceleration": 1.2,
            "rising_missed_tp1_tick_acceleration_fresh": True,
            "rising_missed_tp1_tick_acceleration_source": (
                "trusted_ws_signed_0b_10tick_received_ts"
            ),
            "market_data_effective_best_bid": 10_000,
            "market_data_effective_best_ask": 10_020,
            "market_data_effective_quote_age_ms": 20,
            "rising_missed_effective_venue": "KRX",
            "rising_missed_market_session_bucket": "krx_regular",
        },
    )

    projected = mod._risky_micro_projection_from_block_event(row)

    assert projected is not None
    assert projected["risky_micro_episode_reason"] == "tick_context_missing"
    assert projected["risky_micro_episode_tick_context_gap_reason"] == (
        "tick_window_span_missing"
    )


def test_risky_micro_projection_uses_entry_price_executable_snapshot_provenance():
    row = _event(
        "entry-price-derived",
        "475560",
        "THEBORN",
        "entry_ai_price_input_preflight_block",
        {
            "forced_entry_reason": "rising_missed_one_share_entry",
            "rising_missed_entry_lineage": True,
            "entry_ai_price_ws_snapshot_refresh_best_bid": 10_000,
            "entry_ai_price_ws_snapshot_refresh_best_ask": 10_020,
            "entry_ai_price_ws_snapshot_refresh_age_ms": 25,
            "rising_missed_tp1_submit_context_tick_acceleration": 1.2,
            "rising_missed_tp1_submit_context_tick_window_span_sec": 5,
            "rising_missed_tp1_submit_context_true_ofi_ewma": 0.1,
            "rising_missed_tp1_submit_context_top_depth_ratio": 1.5,
            "effective_venue": "KRX",
            "market_session_bucket": "krx_regular",
        },
        emitted_at="2026-08-14T09:00:00+09:00",
    )

    projected = mod._risky_micro_projection_from_block_event(row)

    assert projected is not None
    assert projected["risky_micro_episode_bbo_valid"] is True
    assert projected["risky_micro_episode_quote_fresh"] is True
    assert projected["risky_micro_episode_source_bbo_provenance"] == (
        "entry_ai_price_ws_snapshot_refresh_bbo"
    )
    assert projected["risky_micro_episode_instrumentation_gap"] == "none"


def test_risky_micro_rolling_requires_30_resolved_10_symbols_3_dates(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "reports"
    report_dir.mkdir()
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)

    def rows_for(trade_date):
        return [
            {
                "trade_date": trade_date,
                "ts": f"{trade_date}T09:00:{index:02d}+09:00",
                "stock_code": f"{index:06d}",
                "stock_name": f"symbol-{index}",
                "effective_venue": "KRX",
                "market_session_bucket": "KRX_REGULAR",
                "source_category": "tp1",
                "source_stage": "tp1:rising_missed_tp1_candidate_blocked",
                "candidate_status": "source_only_candidate",
                "policy_version": mod.RISKY_MICRO_POLICY_VERSION,
                "entry_profile": mod.RISKY_MICRO_PRIMARY_ENTRY_PROFILE,
                "entry_profile_ttl_sec": 3,
                "entry_profile_promotion_ev_included": True,
                "outcome_join_status": "resolved_target_first",
                "fill_feasible": True,
                "net_return_bps": 10,
                "metric_role": "source_only_counterfactual_outcome",
                "decision_authority": "source_only_no_runtime_apply",
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "rolling_eligible_daily_cap_applied": True,
            }
            for index in range(10)
        ]

    for report_date in ("2026-08-12", "2026-08-13"):
        payload = {
            "report_type": "rising_missed_intraday_feedback",
            "target_date": report_date,
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "risky_micro_episode_rolling_eligible_rows": rows_for(report_date),
        }
        (report_dir / f"rising_missed_intraday_feedback_{report_date}.json").write_text(
            json.dumps(payload), encoding="utf-8"
        )

    summary, rolling_rows = mod._clean_baseline_rolling_risky_micro_outcomes(
        "2026-08-14",
        rows_for("2026-08-14"),
    )

    assert len(rolling_rows) == 30
    assert summary["risky_micro_episode_rolling_resolved_episode_count"] == 30
    assert summary["risky_micro_episode_rolling_unique_symbol_count"] == 10
    assert summary["risky_micro_episode_rolling_trade_date_count"] == 3
    assert summary["risky_micro_episode_promotion_review_sample_floor_met"] is True
    assert summary["risky_micro_episode_resolved_opportunity_sample_floor_met"] is True
    assert summary["risky_micro_episode_filled_terminal_sample_floor_met"] is True
    assert summary["risky_micro_episode_filled_terminal_episode_count"] == 30
    assert summary["risky_micro_episode_real_order_promotion_allowed"] is False
    assert summary["risky_micro_episode_rolling_decision"] == (
        "outcome_join_ready_positive_ev"
    )
    assert summary["risky_micro_episode_source_quality_adjusted_ev_pct"] == 0.1
    assert "no_runtime_apply" in summary["risky_micro_episode_ev_decision_authority"]


def test_risky_micro_rolling_excludes_truncated_legacy_daily_outcomes(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "reports"
    report_dir.mkdir()
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    legacy_row = {
        "ts": "2026-08-13T09:00:00+09:00",
        "stock_code": "475560",
        "stock_name": "THEBORN",
        "effective_venue": "KRX",
        "market_session_bucket": "KRX_REGULAR",
        "source_category": "tp1",
        "source_stage": "tp1:rising_missed_tp1_candidate_blocked",
        "outcome_join_status": "resolved_target_first",
        "net_return_bps": 25,
        "outcome_evaluation_role": "eligible_source_candidate",
    }
    payload = {
        "report_type": "rising_missed_intraday_feedback",
        "target_date": "2026-08-13",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "summary": {"risky_micro_episode_observation_count": 201},
        "risky_micro_episode_source_candidate_rows": [legacy_row] * 200,
    }
    (report_dir / "rising_missed_intraday_feedback_2026-08-13.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )

    summary, rolling_rows = mod._clean_baseline_rolling_risky_micro_outcomes(
        "2026-08-14",
        [],
    )

    assert rolling_rows == []
    assert summary["risky_micro_episode_rolling_resolved_episode_count"] == 0
    assert summary["risky_micro_episode_rolling_window"]["excluded_reports"] == [
        {"target_date": "2026-08-13", "reason": "truncated_daily_outcomes"}
    ]
    assert summary["risky_micro_episode_source_quality_adjusted_ev_pct"] is None


def test_risky_micro_rolling_separates_resolved_and_filled_terminal_floors(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "reports"
    report_dir.mkdir()
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    rows = [
        {
            "trade_date": trade_date,
            "ts": f"{trade_date}T09:00:{index:02d}+09:00",
            "stock_code": f"{index:06d}",
            "effective_venue": "KRX",
            "market_session_bucket": "KRX_REGULAR",
            "candidate_status": "source_only_candidate",
            "policy_version": mod.RISKY_MICRO_POLICY_VERSION,
            "entry_profile": mod.RISKY_MICRO_PRIMARY_ENTRY_PROFILE,
            "entry_profile_promotion_ev_included": True,
            "outcome_join_status": "resolved_not_filled",
            "fill_feasible": False,
            "net_return_bps": 0,
            "runtime_effect": False,
            "allowed_runtime_apply": False,
        }
        for trade_date in ("2026-08-12", "2026-08-13", "2026-08-14")
        for index in range(10)
    ]

    summary, _ = mod._clean_baseline_rolling_risky_micro_outcomes(
        "2026-08-14",
        rows,
    )

    assert summary["risky_micro_episode_resolved_opportunity_sample_floor_met"] is True
    assert summary["risky_micro_episode_filled_terminal_episode_count"] == 0
    assert summary["risky_micro_episode_filled_terminal_sample_floor_met"] is False
    assert summary["risky_micro_episode_promotion_review_sample_floor_met"] is False
    assert summary["risky_micro_episode_real_order_promotion_state"] == (
        "blocked_sample_floor"
    )


def test_tp1_label_projection_preserves_plain_counterfactual_provenance():
    row = _event(
        3,
        "000003",
        "counterfactual",
        "rising_missed_tp1_counterfactual_submit_safety",
        {
            "selector_reason": "freshness_pass",
            "selector_deferred": False,
            "rising_missed_market_session_bucket": "nxt_entry_window",
            "rising_missed_tp1_evaluation_id": "eval-3",
            "current_price_observed": 12000,
            "rising_missed_tp1_unused_diagnostic": "drop-me",
            "large_unrelated_payload": "x" * 10000,
        },
    )

    projected = mod._tp1_label_event_projection(row)

    assert projected["fields"] == {
        "selector_reason": "freshness_pass",
        "selector_deferred": False,
        "rising_missed_market_session_bucket": "nxt_entry_window",
        "rising_missed_tp1_evaluation_id": "eval-3",
        "current_price_observed": 12000,
    }


def test_tp1_first_hit_label_prefers_gross_target_and_requires_actual_costs_for_net(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline_events_2026-07-14.jsonl"
    rows = [
        _event(
            701,
            "000701",
            "tp1",
            "rising_missed_one_share_entry",
            {
                "rising_missed_tp1_selector_active": True,
                "rising_missed_tp1_candidate_allowed": True,
                "rising_missed_tp1_candidate_reason": "rising_missed_tp1_candidate_pass",
                "rising_missed_tp1_candidate_lane": "low_rebound",
                "current_price_observed": 10000,
                "market_data_effective_best_bid": 9990,
                "market_data_effective_best_ask": 10000,
                "venue": "PREMARKET_KRX_LIKE",
                "venue_resolution": "canonicalized:rising_missed_effective_venue",
            },
            emitted_at="2026-07-14T09:00:00+09:00",
        ),
        _event(
            701,
            "000701",
            "tp1",
            "holding_observation",
            {
                "current_price_observed": 10140,
                "market_data_effective_best_bid": 10140,
                "market_data_effective_best_ask": 10150,
            },
            emitted_at="2026-07-14T09:05:00+09:00",
            pipeline="HOLDING_PIPELINE",
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows), encoding="utf-8"
    )

    report = mod.build_report(
        "2026-07-14", pipeline_path=pipeline_path, generated_at="fixed"
    )

    label = report["rising_missed_tp1_first_hit_label_rows"][0]
    assert label["gross_first_hit_label"] == "gross_target_first"
    assert label["first_hit_move_pct"] == 1.4
    assert label["net_label"] == "unavailable_fee_tax_missing"
    assert label["effective_venue"] == "PREMARKET_KRX_LIKE"
    assert label["venue_resolution"] == "canonicalized:rising_missed_effective_venue"
    assert report["summary"]["rising_missed_tp1_net_confirmed_count"] == 0


def test_tp1_counterfactual_preserves_explicit_premarket_venue_provenance(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline_events_2026-07-14.jsonl"
    rows = [
        _event(
            710,
            "000710",
            "premarket",
            "rising_missed_tp1_counterfactual_submit_safety",
            {
                "rising_missed_tp1_evaluation_id": "premarket-eval-1",
                "rising_missed_tp1_effective_price": 10000,
                "venue": "PREMARKET_KRX_LIKE",
                "venue_resolution": ("canonicalized:rising_missed_effective_venue"),
                "market_session_bucket": "krx_like_premarket",
                "selector_reason": "rising_missed_tp1_hard_negative_evidence",
                "rising_missed_tp1_counterfactual_submit_safety_action": (
                    "HARD_VETO_EXPECTED"
                ),
            },
            emitted_at="2026-07-14T08:05:00+09:00",
        ),
        _event(
            999,
            "000999",
            "watermark",
            "holding_observation",
            {"current_price_observed": 10000},
            emitted_at="2026-07-14T08:06:01+09:00",
            pipeline="HOLDING_PIPELINE",
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows), encoding="utf-8"
    )

    report = mod.build_report(
        "2026-07-14", pipeline_path=pipeline_path, generated_at="fixed"
    )

    observation = report["rising_missed_tp1_counterfactual_submit_safety_rows"][0]
    label = report["rising_missed_tp1_counterfactual_first_hit_label_rows"][0]
    for row in (observation, label):
        assert row["effective_venue"] == "PREMARKET_KRX_LIKE"
        assert row["venue_resolution"] == "canonicalized:rising_missed_effective_venue"


def test_nxt_session_observation_separates_micro_state_and_effective_order_type(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline_events_2026-07-14.jsonl"
    common = {
        "rising_missed_tp1_evaluation_id": "nxt-eval-1",
        "rising_missed_market_session_bucket": "nxt_entry_window",
        "rising_missed_market_session_state": "NXT_CONTINUOUS",
        "rising_missed_effective_venue": "NXT",
        "rising_missed_nxt_eligible": True,
        "rising_missed_nxt_flag_source": "stock.is_nxt",
        "rising_missed_ws_0b_route": "krx_nxt_integrated",
        "rising_missed_ws_0d_route": "krx_nxt_integrated",
        "rising_missed_ws_0b_age_ms": 8000.0,
        "rising_missed_ws_0d_age_ms": 200.0,
        "rising_missed_nxt_micro_state": "fresh_trade_quiet",
        "rising_missed_tp1_input_ready": False,
        "market_data_effective_price_source": "ka10004_rest_orderbook",
    }
    rows = [
        _event(
            801,
            "000801",
            "nxt",
            "rising_missed_one_share_entry",
            {
                **common,
                "rising_missed_tp1_selector_active": True,
                "rising_missed_tp1_candidate_allowed": True,
                "rising_missed_tp1_candidate_reason": "rising_missed_tp1_candidate_pass",
            },
            emitted_at="2026-07-14T16:20:00+09:00",
        ),
        _event(
            801,
            "000801",
            "nxt",
            "order_leg_request",
            {
                **common,
                "requested_order_type": "3",
                "effective_order_type": "6",
                "effective_dmst_stex_tp": "NXT",
                "order_type_remapped": True,
                "order_type_remap_reason": "nxt_market_to_best_limit",
            },
            emitted_at="2026-07-14T16:20:01+09:00",
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows), encoding="utf-8"
    )

    report = mod.build_report(
        "2026-07-14", pipeline_path=pipeline_path, generated_at="fixed"
    )

    assert report["summary"]["rising_missed_nxt_evaluation_count"] == 1
    assert report["summary"]["rising_missed_nxt_input_ready_count"] == 0
    assert report["summary"]["rising_missed_nxt_rest_quote_selected_count"] == 1
    assert report["summary"]["rising_missed_nxt_order_request_count"] == 1
    assert report["summary"]["rising_missed_nxt_order_type_remap_count"] == 1
    assert report["summary"]["rising_missed_nxt_micro_state_counts"] == [
        {"nxt_micro_state": "fresh_trade_quiet", "count": 1}
    ]
    assert (
        report["rising_missed_nxt_order_resolution_rows"][0]["order_type_remap_reason"]
        == "nxt_market_to_best_limit"
    )


def test_nxt_post_block_sampler_recovers_counterfactual_first_hit_label(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-14.jsonl"
    common = {
        "rising_missed_tp1_evaluation_id": "nxt-block-1",
        "rising_missed_market_session_bucket": "nxt_entry_window",
        "rising_missed_effective_venue": "NXT",
        "rising_missed_nxt_post_block_source_block_stage": "tp1_selector",
        "rising_missed_nxt_post_block_source_block_reason": (
            "rising_missed_tp1_insufficient_positive_support"
        ),
        "rising_missed_nxt_post_block_entry_price_source": (
            "rising_missed_tp1_effective_price"
        ),
        "rising_missed_nxt_post_block_sampler_runtime_configured": True,
        "rising_missed_nxt_post_block_sampler_runtime_active_date": "2026-07-14",
        "rising_missed_nxt_post_block_sampler_runtime_current_date": "2026-07-14",
        "rising_missed_nxt_post_block_sampler_runtime_active": True,
        "rising_missed_nxt_post_block_sampler_runtime_called": True,
        "rising_missed_nxt_post_block_sampler_runtime_applied": True,
        "rising_missed_nxt_post_block_rest_fallback_runtime_configured": True,
        "rising_missed_nxt_post_block_rest_fallback_runtime_active_date": (
            "2026-07-14"
        ),
        "rising_missed_nxt_post_block_rest_fallback_runtime_current_date": (
            "2026-07-14"
        ),
        "rising_missed_nxt_post_block_rest_fallback_runtime_active": True,
    }
    partial_residual_source = {
        "rising_missed_nxt_post_block_source_block_stage": "residual_blocked",
        "rising_missed_nxt_post_block_source_block_reason": (
            "broker_rejected_after_first_residual_leg"
        ),
        "rising_missed_nxt_post_block_source_block_actual_order_submitted": True,
        "rising_missed_nxt_post_block_source_block_broker_order_forbidden": True,
        "rising_missed_nxt_post_block_source_block_residual_submitted_qty": 3,
        "rising_missed_nxt_post_block_source_block_residual_submitted_leg_count": 1,
    }
    rows = [
        _event(
            901,
            "000901",
            "nxt-block",
            "rising_missed_tp1_counterfactual_submit_safety",
            {
                **common,
                "rising_missed_tp1_effective_price": 10000,
                "market_data_effective_best_bid": 9990,
                "market_data_effective_best_ask": 10000,
                "selector_reason": "rising_missed_tp1_insufficient_positive_support",
                "selector_deferred": False,
                "rising_missed_tp1_counterfactual_submit_safety_action": "RECHECK_REQUIRED",
                "rising_missed_tp1_counterfactual_submit_safety_risks": "momentum_support_weak",
                "rising_missed_tp1_nxt_price_jump_recovery_configured": True,
                "rising_missed_tp1_nxt_price_jump_recovery_enabled": True,
                "rising_missed_tp1_nxt_price_jump_recovery_active_date": "2026-07-14",
                "rising_missed_tp1_nxt_price_jump_recovery_current_date": "2026-07-14",
                "rising_missed_tp1_nxt_price_jump_recovery_runtime_called": True,
                "rising_missed_tp1_nxt_price_jump_recovery_runtime_applied": False,
                "rising_missed_tp1_nxt_price_jump_recovery_runtime_call_reason": (
                    "price_jump_signature_missing"
                ),
            },
            emitted_at="2026-07-14T16:20:00+09:00",
        ),
        _event(
            901,
            "000901",
            "nxt-block",
            "rising_missed_nxt_post_block_sampler_registered",
            {
                **common,
                **partial_residual_source,
                "rising_missed_nxt_post_block_sampler_registration_state": "registered",
            },
            emitted_at="2026-07-14T16:20:00.100000+09:00",
        ),
        _event(
            901,
            "000901",
            "nxt-block",
            "rising_missed_nxt_post_block_price_sample",
            {
                **common,
                **partial_residual_source,
                "current_price_observed": 10130,
                "rising_missed_nxt_post_block_price_observation_state": "fresh_ws_0d_nxt_quote_proxy",
                "rising_missed_nxt_post_block_price_source": "trusted_ws_0d_nxt_executable_bid_proxy",
                "rising_missed_nxt_post_block_price_source_reason": "fresh_absolute_ws_0d_nxt_trade_quiet",
                "rising_missed_nxt_post_block_price_fallback_from_reason": "ws_0b_stale",
                "rising_missed_nxt_post_block_price_basis": "executable_sell_touch_quote_proxy",
                "rising_missed_nxt_post_block_ws_0b_age_ms": 30000.0,
                "rising_missed_nxt_post_block_ws_0b_item": "000901_AL",
                "rising_missed_nxt_post_block_ws_0b_route": "krx_nxt_integrated",
                "rising_missed_nxt_post_block_ws_0d_age_ms": 80.0,
                "rising_missed_nxt_post_block_ws_0d_item": "000901_AL",
                "rising_missed_nxt_post_block_ws_0d_route": "krx_nxt_integrated",
                "rising_missed_nxt_post_block_ws_0d_best_bid": 10130,
                "rising_missed_nxt_post_block_ws_0d_best_ask": 10140,
                "rising_missed_nxt_post_block_ws_0d_quote_proxy_applied": True,
                "rising_missed_nxt_post_block_fresh_sample": True,
                "rising_missed_nxt_post_block_sample_attempt_count": 1,
                "rising_missed_nxt_post_block_fresh_sample_count": 1,
                "rising_missed_nxt_post_block_trade_price_sample_count": 0,
                "rising_missed_nxt_post_block_quote_proxy_sample_count": 1,
                "rising_missed_nxt_post_block_source_gap_sample_count": 0,
                "rising_missed_nxt_post_block_move_pct": 1.3,
            },
            emitted_at="2026-07-14T16:24:00+09:00",
        ),
        _event(
            901,
            "000901",
            "nxt-block",
            "rising_missed_nxt_post_block_price_sample",
            {
                **common,
                **partial_residual_source,
                "current_price_observed": 10140,
                "rising_missed_nxt_post_block_price_observation_state": "fresh_ws_0b_nxt",
                "rising_missed_nxt_post_block_price_source": "trusted_ws_0b_nxt",
                "rising_missed_nxt_post_block_price_source_reason": "fresh_absolute_ws_0b_nxt",
                "rising_missed_nxt_post_block_price_basis": "last_trade_price",
                "rising_missed_nxt_post_block_ws_0b_age_ms": 100.0,
                "rising_missed_nxt_post_block_ws_0b_item": "000901_AL",
                "rising_missed_nxt_post_block_ws_0b_route": "krx_nxt_integrated",
                "rising_missed_nxt_post_block_fresh_sample": True,
                "rising_missed_nxt_post_block_sample_attempt_count": 2,
                "rising_missed_nxt_post_block_fresh_sample_count": 2,
                "rising_missed_nxt_post_block_trade_price_sample_count": 1,
                "rising_missed_nxt_post_block_quote_proxy_sample_count": 1,
                "rising_missed_nxt_post_block_source_gap_sample_count": 0,
                "rising_missed_nxt_post_block_move_pct": 1.4,
            },
            emitted_at="2026-07-14T16:25:00+09:00",
        ),
        _event(
            901,
            "000901",
            "nxt-block",
            "rising_missed_nxt_post_block_price_sample",
            {
                **common,
                **partial_residual_source,
                "rising_missed_nxt_post_block_price_observation_state": "source_gap",
                "rising_missed_nxt_post_block_price_source": "unavailable",
                "rising_missed_nxt_post_block_price_source_reason": "ws_0b_stale",
                "rising_missed_nxt_post_block_fresh_sample": False,
                "rising_missed_nxt_post_block_rest_fallback_enabled": True,
                "rising_missed_nxt_post_block_rest_fallback_attempted": False,
                "rising_missed_nxt_post_block_rest_fallback_applied": False,
                "rising_missed_nxt_post_block_rest_fallback_reason": (
                    "observation_rest_budget_deferred"
                ),
                "rising_missed_nxt_post_block_rest_fetch_state": "not_attempted",
                "rising_missed_nxt_post_block_sample_attempt_count": 3,
                "rising_missed_nxt_post_block_fresh_sample_count": 2,
                "rising_missed_nxt_post_block_trade_price_sample_count": 1,
                "rising_missed_nxt_post_block_quote_proxy_sample_count": 1,
                "rising_missed_nxt_post_block_source_gap_sample_count": 1,
            },
            emitted_at="2026-07-14T16:30:00+09:00",
        ),
        _event(
            901,
            "000901",
            "nxt-block",
            "rising_missed_nxt_post_block_price_sampler_completed",
            {
                **common,
                **partial_residual_source,
                "rising_missed_nxt_post_block_sampler_completion_state": "completed",
                "rising_missed_nxt_post_block_sampler_outcome_label": "gross_target_first",
                "rising_missed_nxt_post_block_sampler_source_quality_state": "pass",
                "rising_missed_nxt_post_block_sample_attempt_count": 80,
                "rising_missed_nxt_post_block_fresh_sample_count": 78,
                "rising_missed_nxt_post_block_trade_price_sample_count": 1,
                "rising_missed_nxt_post_block_quote_proxy_sample_count": 1,
                "rising_missed_nxt_post_block_source_gap_sample_count": 2,
                "rising_missed_nxt_post_block_first_hit_move_pct": 1.3,
                "rising_missed_nxt_post_block_first_hit_price_source": "trusted_ws_0d_nxt_executable_bid_proxy",
                "rising_missed_nxt_post_block_first_hit_price_basis": "executable_sell_touch_quote_proxy",
                "rising_missed_nxt_post_block_max_move_pct": 1.8,
                "rising_missed_nxt_post_block_min_move_pct": -0.2,
            },
            emitted_at="2026-07-14T16:40:00+09:00",
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows), encoding="utf-8"
    )

    report = mod.build_report(
        "2026-07-14", pipeline_path=pipeline_path, generated_at="fixed"
    )

    label = report["rising_missed_tp1_counterfactual_first_hit_label_rows"][0]
    assert label["gross_first_hit_label"] == "gross_target_first"
    assert label["max_move_pct_within_20m"] == 1.8
    assert label["min_move_pct_within_20m"] == -0.2
    summary = report["summary"]
    assert summary["rising_missed_nxt_post_block_sampler_registered_count"] == 1
    assert summary["rising_missed_nxt_post_block_sampler_runtime_called_count"] == 1
    assert summary["rising_missed_nxt_post_block_sampler_runtime_applied_count"] == 1
    assert (
        summary["rising_missed_nxt_post_block_rest_fallback_runtime_called_count"] == 0
    )
    assert summary["rising_missed_nxt_price_jump_recovery_runtime_called_count"] == 1
    assert summary["rising_missed_nxt_price_jump_recovery_runtime_applied_count"] == 0
    assert summary["rising_missed_nxt_post_block_fresh_price_sample_count"] == 2
    assert summary["rising_missed_nxt_post_block_trade_price_sample_count"] == 1
    assert summary["rising_missed_nxt_post_block_quote_proxy_sample_count"] == 1
    assert summary["rising_missed_nxt_post_block_sampler_completed_count"] == 1
    assert summary["rising_missed_nxt_post_block_sampler_outcome_counts"] == [
        {"outcome_label": "gross_target_first", "count": 1}
    ]
    blocker_outcome = summary[
        "rising_missed_nxt_post_block_blocker_outcome_attribution"
    ][0]
    assert blocker_outcome["source_block_stage"] == "residual_blocked"
    assert (
        blocker_outcome["source_block_reason"]
        == "broker_rejected_after_first_residual_leg"
    )
    assert blocker_outcome["completed_sample_count"] == 1
    assert blocker_outcome["gross_target_first_rate_pct"] == 100.0
    assert blocker_outcome["equal_weight_avg_mfe_after_block_pct"] == 1.8
    assert blocker_outcome["equal_weight_avg_mae_after_block_pct"] == -0.2
    assert blocker_outcome["sample_floor_met"] is False
    assert blocker_outcome["runtime_effect"] is False
    assert (
        report["metric_contracts"][
            "rising_missed_nxt_post_block_blocker_outcome_attribution"
        ]["decision_authority"]
        == "source_only_no_runtime_mutation"
    )
    assert summary["rising_missed_nxt_post_block_source_block_stage_counts"] == [
        {"source_block_stage": "residual_blocked", "count": 1}
    ]
    assert (
        summary["rising_missed_nxt_post_block_source_block_order_submitted_count"] == 1
    )
    assert (
        summary["rising_missed_nxt_post_block_source_block_residual_submitted_qty"] == 3
    )
    assert summary["rising_missed_nxt_post_block_rest_fallback_attempted_count"] == 0
    assert summary["rising_missed_nxt_post_block_rest_fallback_applied_count"] == 0
    assert summary["rising_missed_nxt_post_block_rest_budget_deferred_count"] == 1
    completion = report["rising_missed_nxt_post_block_price_sampler_rows"][-1]
    assert completion["first_hit_move_pct"] == 1.3
    assert completion["mfe_after_block_pct"] == 1.8
    assert completion["mae_after_block_pct"] == -0.2
    assert completion["trade_price_sample_count"] == 1
    assert completion["quote_proxy_sample_count"] == 1
    assert completion["source_block_stage"] == "residual_blocked"
    assert completion["source_block_actual_order_submitted"] is True
    assert completion["source_block_residual_submitted_qty"] == 3
    assert completion["entry_price_source"] == "rising_missed_tp1_effective_price"
    assert completion["first_hit_price_source"] == (
        "trusted_ws_0d_nxt_executable_bid_proxy"
    )
    proxy = next(
        item
        for item in report["rising_missed_nxt_post_block_price_sampler_rows"]
        if item.get("ws_0d_quote_proxy_applied")
    )
    assert proxy["current_price_observed"] == 10130.0
    assert proxy["price_basis"] == "executable_sell_touch_quote_proxy"
    assert proxy["ws_0d_route"] == "krx_nxt_integrated"


def test_nxt_session_observation_excludes_non_exact_session_or_venue(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-14.jsonl"
    rows = [
        _event(
            951,
            "000951",
            "wrong-venue",
            "rising_missed_nxt_post_block_sampler_registered",
            {
                "rising_missed_tp1_evaluation_id": "nxt-wrong-venue",
                "rising_missed_market_session_bucket": "nxt_entry_window",
                "rising_missed_effective_venue": "KRX",
            },
            emitted_at="2026-07-14T16:20:00+09:00",
        ),
        _event(
            952,
            "000952",
            "wrong-session",
            "rising_missed_nxt_post_block_sampler_registered",
            {
                "rising_missed_tp1_evaluation_id": "nxt-wrong-session",
                "rising_missed_market_session_bucket": "nxt_preopen_window",
                "rising_missed_effective_venue": "NXT",
            },
            emitted_at="2026-07-14T08:20:00+09:00",
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows), encoding="utf-8"
    )

    report = mod.build_report(
        "2026-07-14", pipeline_path=pipeline_path, generated_at="fixed"
    )

    assert report["summary"]["rising_missed_nxt_evaluation_count"] == 0
    assert (
        report["summary"]["rising_missed_nxt_post_block_sampler_registered_count"] == 0
    )
    assert report["rising_missed_nxt_post_block_price_sampler_rows"] == []


def test_tp1_first_hit_label_marks_adverse_first_and_can_confirm_net_with_costs(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline_events_2026-07-14.jsonl"
    rows = [
        _event(
            702,
            "000702",
            "adverse",
            "rising_missed_tp1_candidate_blocked",
            {
                "rising_missed_tp1_selector_active": True,
                "rising_missed_tp1_candidate_allowed": True,
                "rising_missed_tp1_candidate_reason": "rising_missed_tp1_candidate_pass",
                "current_price_observed": 10000,
                "market_data_effective_best_bid": 9990,
                "market_data_effective_best_ask": 10000,
            },
            emitted_at="2026-07-14T09:00:00+09:00",
        ),
        _event(
            702,
            "000702",
            "adverse",
            "holding_observation",
            {
                "current_price_observed": 9920,
                "market_data_effective_best_bid": 9920,
                "market_data_effective_best_ask": 9930,
            },
            emitted_at="2026-07-14T09:02:00+09:00",
            pipeline="HOLDING_PIPELINE",
        ),
        _event(
            703,
            "000703",
            "net",
            "rising_missed_one_share_entry",
            {
                "rising_missed_tp1_selector_active": True,
                "rising_missed_tp1_candidate_allowed": True,
                "rising_missed_tp1_candidate_reason": "rising_missed_tp1_candidate_pass",
                "current_price_observed": 10000,
                "market_data_effective_best_bid": 9990,
                "market_data_effective_best_ask": 10000,
                "actual_fee_krw": 10,
                "actual_tax_krw": 10,
            },
            emitted_at="2026-07-14T09:10:00+09:00",
        ),
        _event(
            703,
            "000703",
            "net",
            "holding_observation",
            {
                "current_price_observed": 10130,
                "market_data_effective_best_bid": 10130,
                "market_data_effective_best_ask": 10140,
            },
            emitted_at="2026-07-14T09:15:00+09:00",
            pipeline="HOLDING_PIPELINE",
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows), encoding="utf-8"
    )

    report = mod.build_report(
        "2026-07-14", pipeline_path=pipeline_path, generated_at="fixed"
    )
    labels = {
        row["stock_code"]: row
        for row in report["rising_missed_tp1_first_hit_label_rows"]
    }

    assert labels["000702"]["gross_first_hit_label"] == "adverse_stop_first"
    assert labels["000702"]["net_label"] == "unavailable_fee_tax_missing"
    assert labels["000703"]["gross_first_hit_label"] == "gross_target_first"
    assert labels["000703"]["actual_cost_pct"] == 0.2
    assert labels["000703"]["net_label"] == "net_target_confirmed"


def test_tp1_first_hit_label_accepts_explicit_zero_costs_without_closing_pending_horizon(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline_events_2026-07-14.jsonl"
    rows = [
        _event(
            704,
            "000704",
            "pending",
            "rising_missed_one_share_entry",
            {
                "rising_missed_tp1_selector_active": True,
                "rising_missed_tp1_candidate_allowed": True,
                "rising_missed_tp1_candidate_reason": "rising_missed_tp1_candidate_pass",
                "current_price_observed": 10000,
                "market_data_effective_best_bid": 9990,
                "market_data_effective_best_ask": 10000,
                "actual_fee_krw": 0,
                "actual_tax_krw": 0,
            },
            emitted_at="2026-07-14T09:00:00+09:00",
        ),
        _event(
            704,
            "000704",
            "pending",
            "holding_observation",
            {"current_price_observed": 10020},
            emitted_at="2026-07-14T09:05:00+09:00",
            pipeline="HOLDING_PIPELINE",
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows), encoding="utf-8"
    )

    report = mod.build_report(
        "2026-07-14", pipeline_path=pipeline_path, generated_at="fixed"
    )

    label = report["rising_missed_tp1_first_hit_label_rows"][0]
    assert label["gross_first_hit_label"] == "pending_horizon"
    assert label["actual_cost_pct"] == 0.0
    assert label["net_label"] == "pending_horizon"


def test_tp1_first_hit_label_uses_effective_price_and_later_cost_only_event(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-14.jsonl"
    rows = [
        _event(
            705,
            "000705",
            "bridge",
            "rising_missed_normal_buy_bridge_unlocked",
            {
                "rising_missed_tp1_selector_active": True,
                "rising_missed_tp1_candidate_allowed": True,
                "rising_missed_tp1_candidate_reason": "rising_missed_tp1_candidate_pass",
                "rising_missed_tp1_effective_price": 10000,
                "current_price_observed": 9000,
                "market_data_effective_best_bid": 9990,
                "market_data_effective_best_ask": 10000,
                "quantity": 1,
            },
            emitted_at="2026-07-14T09:00:00+09:00",
        ),
        _event(
            705,
            "000705",
            "bridge",
            "holding_observation",
            {
                "current_price_observed": 10130,
                "rising_missed_tp1_effective_price": 10000,
                "market_data_effective_best_bid": 10130,
                "market_data_effective_best_ask": 10140,
            },
            emitted_at="2026-07-14T09:05:00+09:00",
            pipeline="HOLDING_PIPELINE",
        ),
        _event(
            705,
            "000705",
            "bridge",
            "execution_cost_observation",
            {"actual_fee_krw": 10, "actual_tax_krw": 10},
            emitted_at="2026-07-14T09:08:00+09:00",
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows), encoding="utf-8"
    )

    report = mod.build_report(
        "2026-07-14", pipeline_path=pipeline_path, generated_at="fixed"
    )

    label = report["rising_missed_tp1_first_hit_label_rows"][0]
    assert label["entry_price"] == 10000.0
    assert label["entry_price_source"] == "market_data_effective_bbo:best_ask"
    assert label["gross_first_hit_label"] == "gross_target_first"
    assert label["actual_cost_pct"] == 0.2
    assert label["net_label"] == "net_target_confirmed"


def test_tp1_first_hit_label_does_not_reuse_propagated_effective_anchor(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-15.jsonl"
    rows = [
        _event(
            707,
            "000707",
            "nxt",
            "rising_missed_one_share_entry",
            {
                "rising_missed_tp1_evaluation_id": "nxt-anchor-eval",
                "rising_missed_tp1_selector_active": True,
                "rising_missed_tp1_candidate_allowed": True,
                "rising_missed_tp1_candidate_reason": (
                    "rising_missed_tp1_candidate_pass"
                ),
                "rising_missed_tp1_effective_price": 10_000,
                "market_data_effective_best_bid": 9_990,
                "market_data_effective_best_ask": 10_000,
            },
            emitted_at="2026-07-15T18:25:00+09:00",
        ),
        _event(
            707,
            "000707",
            "nxt",
            "holding_ws_freshness_recovered",
            {
                "rising_missed_tp1_evaluation_id": "nxt-anchor-eval",
                "rising_missed_tp1_effective_price": 10_000,
                "holding_ws_recovered_curr": 10_160,
                "market_data_effective_best_bid": 10_160,
                "market_data_effective_best_ask": 10_170,
                "holding_rest_quote_request_code": "000707_NX",
                "holding_rest_quote_effective_venue": "NXT",
                "holding_rest_quote_route_consistent": True,
            },
            emitted_at="2026-07-15T18:25:30+09:00",
            pipeline="HOLDING_PIPELINE",
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows), encoding="utf-8"
    )

    report = mod.build_report(
        "2026-07-15", pipeline_path=pipeline_path, generated_at="fixed"
    )

    label = report["rising_missed_tp1_first_hit_label_rows"][0]
    assert label["entry_price"] == 10_000.0
    assert label["gross_first_hit_label"] == "gross_target_first"
    assert label["first_hit_move_pct"] == 1.6


def test_tp1_first_hit_ignores_unproven_holding_rest_recovery(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-15.jsonl"
    rows = [
        _event(
            707,
            "000707",
            "unproven-rest",
            "rising_missed_one_share_entry",
            {
                "rising_missed_tp1_evaluation_id": "unproven-rest-eval",
                "rising_missed_tp1_selector_active": True,
                "rising_missed_tp1_candidate_allowed": True,
                "rising_missed_tp1_candidate_reason": (
                    "rising_missed_tp1_candidate_pass"
                ),
                "rising_missed_tp1_effective_price": 10_000,
                "market_data_effective_best_bid": 9_990,
                "market_data_effective_best_ask": 10_000,
            },
            emitted_at="2026-07-15T08:18:00+09:00",
        ),
        _event(
            707,
            "000707",
            "unproven-rest",
            "holding_ws_freshness_recovered",
            {
                "holding_ws_recovered_curr": 9_400,
                "holding_ws_recovery_outcome": "rest_quote_applied",
            },
            emitted_at="2026-07-15T08:18:30+09:00",
            pipeline="HOLDING_PIPELINE",
        ),
        _event(
            707,
            "000707",
            "unproven-rest",
            "holding_snapshot",
            {"current_price": 10_050},
            emitted_at="2026-07-15T08:18:40+09:00",
            pipeline="HOLDING_PIPELINE",
        ),
        _event(
            707,
            "000707",
            "unproven-rest",
            "holding_snapshot",
            {"current_price": 10_040},
            emitted_at="2026-07-15T08:18:50+09:00",
            pipeline="HOLDING_PIPELINE",
        ),
        _event(
            999,
            "999999",
            "watermark",
            "unrelated",
            {},
            emitted_at="2026-07-15T08:39:00+09:00",
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows),
        encoding="utf-8",
    )

    report = mod.build_report(
        "2026-07-15",
        pipeline_path=pipeline_path,
        generated_at="fixed",
    )

    label = report["rising_missed_tp1_first_hit_label_rows"][0]
    assert label["gross_first_hit_label"] == ("source_gap_non_executable_price_only")
    assert label["min_move_pct_within_20m"] is None


def test_tp1_first_hit_ignores_rejected_holding_rest_divergence(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-15.jsonl"
    rows = [
        _event(
            708,
            "000708",
            "rest-divergence",
            "rising_missed_one_share_entry",
            {
                "rising_missed_tp1_evaluation_id": "rest-divergence-eval",
                "rising_missed_tp1_selector_active": True,
                "rising_missed_tp1_candidate_allowed": True,
                "rising_missed_tp1_candidate_reason": (
                    "rising_missed_tp1_candidate_pass"
                ),
                "rising_missed_tp1_effective_price": 10_000,
                "market_data_effective_best_bid": 9_990,
                "market_data_effective_best_ask": 10_000,
            },
            emitted_at="2026-07-15T08:18:00+09:00",
        ),
        _event(
            708,
            "000708",
            "rest-divergence",
            "holding_rest_quote_divergence_blocked",
            {
                "holding_ws_recovered_curr": 9_400,
                "holding_ws_curr_price": 9_980,
                "holding_rest_quote_divergence_pct": 5.8,
                "holding_ws_recovery_outcome": "rest_quote_divergence_blocked",
            },
            emitted_at="2026-07-15T08:18:30+09:00",
            pipeline="HOLDING_PIPELINE",
        ),
        _event(
            708,
            "000708",
            "rest-divergence",
            "holding_snapshot",
            {"current_price": 10_050},
            emitted_at="2026-07-15T08:18:40+09:00",
            pipeline="HOLDING_PIPELINE",
        ),
        _event(
            708,
            "000708",
            "rest-divergence",
            "holding_snapshot",
            {"current_price": 10_040},
            emitted_at="2026-07-15T08:18:50+09:00",
            pipeline="HOLDING_PIPELINE",
        ),
        _event(
            999,
            "999999",
            "watermark",
            "unrelated",
            {},
            emitted_at="2026-07-15T08:39:00+09:00",
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows),
        encoding="utf-8",
    )

    report = mod.build_report(
        "2026-07-15",
        pipeline_path=pipeline_path,
        generated_at="fixed",
    )

    label = report["rising_missed_tp1_first_hit_label_rows"][0]
    assert label["gross_first_hit_label"] == ("source_gap_non_executable_price_only")
    assert label["first_hit_ts"] is None
    assert label["max_move_pct_within_20m"] is None
    assert label["min_move_pct_within_20m"] is None


def test_tp1_labels_prefer_effective_candidate_and_fresh_submit_mark_over_stale_scanner_price(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline_events_2026-07-14.jsonl"
    rows = [
        _event(
            706,
            "000706",
            "pass",
            "rising_missed_one_share_entry",
            {
                "rising_missed_tp1_selector_active": True,
                "rising_missed_tp1_candidate_allowed": True,
                "rising_missed_tp1_candidate_reason": "rising_missed_tp1_candidate_pass",
                "rising_missed_tp1_evaluation_id": "pass-eval",
                "rising_missed_tp1_effective_price": 10000,
                "current_price_observed": 9000,
                "market_data_effective_best_bid": 9990,
                "market_data_effective_best_ask": 10000,
            },
            emitted_at="2026-07-14T09:00:00+09:00",
        ),
        _event(
            706,
            "000706",
            "pass",
            "real_weak_ai_micro_entry_block",
            {
                "current_price_observed": 9000,
                "mark_price_at_submit": 10140,
                "best_bid_at_submit": 10140,
                "best_ask_at_submit": 10150,
            },
            emitted_at="2026-07-14T09:01:00+09:00",
        ),
        _event(
            806,
            "000806",
            "counterfactual",
            "rising_missed_tp1_counterfactual_submit_safety",
            {
                "selector_reason": "rising_missed_tp1_lane_not_eligible",
                "selector_deferred": False,
                "rising_missed_tp1_candidate_allowed": False,
                "rising_missed_tp1_evaluation_id": "counterfactual-eval",
                "rising_missed_tp1_effective_price": 20000,
                "current_price_observed": 18000,
                "market_data_effective_best_bid": 19990,
                "market_data_effective_best_ask": 20000,
                "rising_missed_tp1_counterfactual_submit_safety_action": "RECHECK_REQUIRED",
                "rising_missed_tp1_counterfactual_submit_safety_risks": "momentum_support_weak",
            },
            emitted_at="2026-07-14T09:02:00+09:00",
        ),
        _event(
            806,
            "000806",
            "counterfactual",
            "scalping_scanner_promotion_latency_trace",
            {"current_price_observed": 20300, "ws_last_0d_age_ms": 100},
            emitted_at="2026-07-14T09:03:00+09:00",
        ),
        _event(
            806,
            "000806",
            "counterfactual",
            "scalping_scanner_watching_runtime_skip",
            {
                "current_price_observed": 20280,
                "ws_last_0b_age_ms": 100,
                "market_data_effective_best_bid": 20280,
                "market_data_effective_best_ask": 20290,
            },
            emitted_at="2026-07-14T09:04:00+09:00",
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows), encoding="utf-8"
    )

    report = mod.build_report(
        "2026-07-14", pipeline_path=pipeline_path, generated_at="fixed"
    )

    pass_label = report["rising_missed_tp1_first_hit_label_rows"][0]
    assert pass_label["entry_price"] == 10000.0
    assert pass_label["entry_price_source"] == ("market_data_effective_bbo:best_ask")
    assert pass_label["gross_first_hit_label"] == "gross_target_first"
    counterfactual_label = report[
        "rising_missed_tp1_counterfactual_first_hit_label_rows"
    ][0]
    assert counterfactual_label["entry_price"] == 20000.0
    assert (
        counterfactual_label["entry_price_source"]
        == "market_data_effective_bbo:best_ask"
    )
    assert counterfactual_label["gross_first_hit_label"] == "gross_target_first"
    assert counterfactual_label["first_hit_ts"] == "2026-07-14T09:04:00+09:00"
    assert (
        report["summary"]["rising_missed_tp1_counterfactual_gross_target_first_count"]
        == 1
    )
    assert counterfactual_label["actual_order_submitted"] is False
    assert counterfactual_label["broker_order_forbidden"] is True


def test_tp1_label_ignores_unfresh_decision_stage_current_price_before_submit_mark(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline_events_2026-07-14.jsonl"
    rows = [
        _event(
            707,
            "000707",
            "stale-decision-price",
            "rising_missed_one_share_entry",
            {
                "rising_missed_tp1_selector_active": True,
                "rising_missed_tp1_candidate_allowed": True,
                "rising_missed_tp1_candidate_reason": "rising_missed_tp1_candidate_pass",
                "rising_missed_tp1_evaluation_id": "stale-decision-price-eval",
                "rising_missed_tp1_effective_price": 10000,
                "current_price_observed": 11000,
                "market_data_effective_best_bid": 9990,
                "market_data_effective_best_ask": 10000,
            },
            emitted_at="2026-07-14T09:00:00+09:00",
        ),
        _event(
            707,
            "000707",
            "stale-decision-price",
            "budget_pass",
            {"current_price_observed": 11000},
            emitted_at="2026-07-14T09:00:01+09:00",
        ),
        _event(
            707,
            "000707",
            "stale-decision-price",
            "orderbook_stability_observed",
            {"current_price_observed": 11000},
            emitted_at="2026-07-14T09:00:02+09:00",
        ),
        _event(
            707,
            "000707",
            "stale-decision-price",
            "latency_block",
            {
                "current_price_observed": 11000,
                "pre_submit_ws_snapshot_refresh_latest_price": 10050,
                "pre_submit_ws_snapshot_refresh_best_bid": 10040,
                "pre_submit_ws_snapshot_refresh_best_ask": 10050,
                "rising_missed_submit_safety_backoff_lineage": True,
                "reason": "latency_state_danger",
            },
            emitted_at="2026-07-14T09:00:03+09:00",
        ),
        _event(
            707,
            "000707",
            "stale-decision-price",
            "budget_pass",
            {"current_price_observed": 11000},
            emitted_at="2026-07-14T09:00:04+09:00",
        ),
        _event(
            707,
            "000707",
            "stale-decision-price",
            "holding_observation",
            {
                "current_price_observed": 10040,
                "executable_sell_price": 10040,
                "executable_buy_price": 10050,
            },
            emitted_at="2026-07-14T09:00:05+09:00",
            pipeline="HOLDING_PIPELINE",
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows), encoding="utf-8"
    )

    report = mod.build_report(
        "2026-07-14", pipeline_path=pipeline_path, generated_at="fixed"
    )

    label = report["rising_missed_tp1_first_hit_label_rows"][0]
    assert label["entry_price"] == 10000.0
    assert label["gross_first_hit_label"] == "pending_horizon"
    assert label["max_move_pct_within_20m"] == 0.4
    # The effective candidate anchor is not a post-block price observation.
    assert label["observed_price_event_count"] == 2
    blocker = report["submit_safety_blocker_rows"][0]
    assert blocker["block_price"] == 10050.0
    assert blocker["mfe_after_block_pct"] == -0.0995
    assert blocker["mae_after_block_pct"] == -0.0995
    assert blocker["post_block_price_event_count"] == 1


def test_tp1_counterfactual_multi_horizon_marks_late_recovery_after_adverse(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline_events_2026-07-14.jsonl"
    rows = [
        _event(
            811,
            "000811",
            "late-recovery",
            "rising_missed_tp1_counterfactual_submit_safety",
            {
                "rising_missed_tp1_evaluation_id": "late-recovery-eval",
                "rising_missed_tp1_effective_price": 10000,
                "market_data_effective_best_bid": 9990,
                "market_data_effective_best_ask": 10000,
                "selector_reason": "rising_missed_tp1_insufficient_positive_support",
                "selector_deferred": False,
                "rising_missed_tp1_counterfactual_submit_safety_action": (
                    "RECHECK_REQUIRED"
                ),
            },
            emitted_at="2026-07-14T09:00:00+09:00",
        ),
        _event(
            811,
            "000811",
            "late-recovery",
            "holding_observation",
            {
                "current_price_observed": 9900,
                "market_data_effective_best_bid": 9900,
                "market_data_effective_best_ask": 9910,
            },
            emitted_at="2026-07-14T09:00:30+09:00",
            pipeline="HOLDING_PIPELINE",
        ),
        _event(
            811,
            "000811",
            "late-recovery",
            "holding_observation",
            {
                "current_price_observed": 10000,
                "market_data_effective_best_bid": 10000,
                "market_data_effective_best_ask": 10010,
            },
            emitted_at="2026-07-14T09:05:00+09:00",
            pipeline="HOLDING_PIPELINE",
        ),
        _event(
            811,
            "000811",
            "late-recovery",
            "holding_observation",
            {
                "current_price_observed": 10130,
                "market_data_effective_best_bid": 10130,
                "market_data_effective_best_ask": 10140,
            },
            emitted_at="2026-07-14T09:25:00+09:00",
            pipeline="HOLDING_PIPELINE",
        ),
        _event(
            999,
            "000999",
            "watermark",
            "holding_observation",
            {"current_price_observed": 10000},
            emitted_at="2026-07-14T10:01:00+09:00",
            pipeline="HOLDING_PIPELINE",
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows), encoding="utf-8"
    )

    report = mod.build_report(
        "2026-07-14", pipeline_path=pipeline_path, generated_at="fixed"
    )

    label = report["rising_missed_tp1_counterfactual_first_hit_label_rows"][0]
    measurements = {
        item["horizon_min"]: item for item in label["post_block_horizon_measurements"]
    }
    assert measurements[20]["outcome_label"] == "adverse_stop_first"
    assert measurements[20]["source_quality_state"] == "pass"
    assert measurements[30]["outcome_label"] == "adverse_stop_first"
    assert measurements[30]["max_move_pct"] == 1.3
    assert label["post_block_late_recovery_after_adverse"] == {
        "detected": True,
        "first_adverse_ts": "2026-07-14T09:00:30+09:00",
        "first_adverse_move_pct": -1.0,
        "first_target_after_adverse_ts": "2026-07-14T09:25:00+09:00",
        "first_target_after_adverse_move_pct": 1.3,
        "first_recovery_horizon_min": 30,
        "reason": "adverse_first_then_late_target_observed",
    }
    summary = report["summary"]
    assert (
        summary["rising_missed_tp1_counterfactual_late_recovery_after_adverse_count"]
        == 1
    )


def test_tp1_counterfactual_multi_horizon_marks_no_symbol_price_as_source_gap(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline_events_2026-07-14.jsonl"
    rows = [
        _event(
            812,
            "000812",
            "coverage-gap",
            "rising_missed_tp1_counterfactual_submit_safety",
            {
                "rising_missed_tp1_evaluation_id": "coverage-gap-eval",
                "rising_missed_tp1_effective_price": 10000,
                "market_data_effective_best_bid": 9990,
                "market_data_effective_best_ask": 10000,
                "rising_missed_effective_venue": "KRX",
                "selector_reason": "rising_missed_tp1_lane_not_eligible",
                "selector_deferred": False,
                "rising_missed_tp1_counterfactual_submit_safety_action": (
                    "RECHECK_REQUIRED"
                ),
            },
            emitted_at="2026-07-14T09:00:00+09:00",
        ),
        _event(
            999,
            "000999",
            "watermark",
            "holding_observation",
            {"current_price_observed": 10000},
            emitted_at="2026-07-14T10:01:00+09:00",
            pipeline="HOLDING_PIPELINE",
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows), encoding="utf-8"
    )

    report = mod.build_report(
        "2026-07-14", pipeline_path=pipeline_path, generated_at="fixed"
    )

    label = report["rising_missed_tp1_counterfactual_first_hit_label_rows"][0]
    measurement_20m = next(
        item
        for item in label["post_block_horizon_measurements"]
        if item["horizon_min"] == 20
    )
    assert label["gross_first_hit_label"] == "source_gap_no_post_block_price"
    assert label["effective_venue"] == "KRX"
    assert measurement_20m["outcome_label"] == "source_gap_no_post_block_price"
    assert measurement_20m["observed_price_event_count"] == 0
    by_venue = {
        item["effective_venue"]: item
        for item in report["summary"][
            "rising_missed_tp1_counterfactual_multi_horizon_by_effective_venue"
        ]
    }
    assert (
        by_venue["KRX"]["rising_missed_tp1_counterfactual_multi_horizon_labeled_count"]
        == 1
    )


def test_tp1_counterfactual_multi_horizon_rejects_mark_only_price(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-14.jsonl"
    rows = [
        _event(
            815,
            "000815",
            "mark-only",
            "rising_missed_tp1_counterfactual_submit_safety",
            {
                "rising_missed_tp1_evaluation_id": "mark-only-eval",
                "rising_missed_tp1_effective_price": 10000,
                "market_data_effective_best_bid": 9990,
                "market_data_effective_best_ask": 10000,
                "rising_missed_effective_venue": "KRX",
                "selector_reason": "rising_missed_tp1_lane_not_eligible",
                "selector_deferred": False,
                "rising_missed_tp1_counterfactual_submit_safety_action": (
                    "RECHECK_REQUIRED"
                ),
            },
            emitted_at="2026-07-14T09:00:00+09:00",
        ),
        _event(
            815,
            "000815",
            "mark-only",
            "holding_observation",
            {"current_price_observed": 10130},
            emitted_at="2026-07-14T09:01:00+09:00",
            pipeline="HOLDING_PIPELINE",
        ),
        _event(
            999,
            "000999",
            "watermark",
            "holding_observation",
            {"current_price_observed": 10000},
            emitted_at="2026-07-14T10:01:00+09:00",
            pipeline="HOLDING_PIPELINE",
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows), encoding="utf-8"
    )

    report = mod.build_report(
        "2026-07-14", pipeline_path=pipeline_path, generated_at="fixed"
    )

    label = report["rising_missed_tp1_counterfactual_first_hit_label_rows"][0]
    measurement_20m = next(
        item
        for item in label["post_block_horizon_measurements"]
        if item["horizon_min"] == 20
    )
    assert measurement_20m["outcome_label"] == ("source_gap_non_executable_price_only")
    assert measurement_20m["source_quality_state"] == (
        "source_gap_non_executable_price_only"
    )
    assert measurement_20m["observed_price_event_count"] == 0
    assert measurement_20m["non_executable_price_event_count"] == 1
    assert measurement_20m["first_hit_price_source"] is None


def test_tp1_counterfactual_projection_keeps_bbo_only_price_event(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-14.jsonl"
    rows = [
        _event(
            816,
            "000816",
            "bbo-only",
            "rising_missed_tp1_counterfactual_submit_safety",
            {
                "rising_missed_tp1_evaluation_id": "bbo-only-eval",
                "rising_missed_tp1_effective_price": 10000,
                "market_data_effective_best_bid": 9990,
                "market_data_effective_best_ask": 10000,
                "rising_missed_effective_venue": "KRX",
                "selector_reason": "rising_missed_tp1_lane_not_eligible",
                "selector_deferred": False,
                "rising_missed_tp1_counterfactual_submit_safety_action": (
                    "RECHECK_REQUIRED"
                ),
            },
            emitted_at="2026-07-14T09:00:00+09:00",
        ),
        _event(
            816,
            "000816",
            "bbo-only",
            "holding_observation",
            {
                "market_data_effective_best_bid": 10130,
                "market_data_effective_best_ask": 10140,
            },
            emitted_at="2026-07-14T09:01:00+09:00",
            pipeline="HOLDING_PIPELINE",
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows), encoding="utf-8"
    )

    report = mod.build_report(
        "2026-07-14", pipeline_path=pipeline_path, generated_at="fixed"
    )

    label = report["rising_missed_tp1_counterfactual_first_hit_label_rows"][0]
    assert label["gross_first_hit_label"] == "gross_target_first"
    measurement_1m = next(
        item
        for item in label["post_block_horizon_measurements"]
        if item["horizon_min"] == 1
    )
    assert measurement_1m["first_hit_price_source"] == (
        "market_data_effective_bbo:best_bid"
    )


def test_tp1_counterfactual_multi_horizon_rejects_other_nxt_evaluation_samples(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline_events_2026-07-14.jsonl"
    rows = [
        _event(
            814,
            "000814",
            "nxt-evaluation-isolation",
            "rising_missed_tp1_counterfactual_submit_safety",
            {
                "rising_missed_tp1_evaluation_id": "candidate-evaluation",
                "rising_missed_tp1_effective_price": 10000,
                "market_data_effective_best_bid": 9990,
                "market_data_effective_best_ask": 10000,
                "selector_reason": "rising_missed_tp1_lane_not_eligible",
                "selector_deferred": False,
                "rising_missed_tp1_counterfactual_submit_safety_action": (
                    "RECHECK_REQUIRED"
                ),
            },
            emitted_at="2026-07-14T09:00:00+09:00",
        ),
        _event(
            814,
            "000814",
            "nxt-evaluation-isolation",
            "rising_missed_nxt_post_block_price_sample",
            {
                "rising_missed_tp1_evaluation_id": "other-evaluation",
                "current_price_observed": 10130,
                "rising_missed_nxt_post_block_fresh_sample": True,
            },
            emitted_at="2026-07-14T09:05:00+09:00",
        ),
        _event(
            999,
            "000999",
            "watermark",
            "holding_observation",
            {"current_price_observed": 10000},
            emitted_at="2026-07-14T10:01:00+09:00",
            pipeline="HOLDING_PIPELINE",
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows), encoding="utf-8"
    )

    report = mod.build_report(
        "2026-07-14", pipeline_path=pipeline_path, generated_at="fixed"
    )

    label = report["rising_missed_tp1_counterfactual_first_hit_label_rows"][0]
    measurement_20m = next(
        item
        for item in label["post_block_horizon_measurements"]
        if item["horizon_min"] == 20
    )
    assert measurement_20m["outcome_label"] == "source_gap_no_post_block_price"
    assert measurement_20m["observed_price_event_count"] == 0


def test_tp1_counterfactual_multi_horizon_does_not_call_target_first_a_recovery(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline_events_2026-07-14.jsonl"
    rows = [
        _event(
            813,
            "000813",
            "target-first",
            "rising_missed_tp1_counterfactual_submit_safety",
            {
                "rising_missed_tp1_evaluation_id": "target-first-eval",
                "rising_missed_tp1_effective_price": 10000,
                "market_data_effective_best_bid": 9990,
                "market_data_effective_best_ask": 10000,
                "rising_missed_effective_venue": "KRX",
                "rising_missed_market_session_bucket": "krx_regular",
                "selector_reason": "rising_missed_tp1_lane_not_eligible",
                "selector_deferred": False,
                "rising_missed_tp1_counterfactual_submit_safety_action": (
                    "RECHECK_REQUIRED"
                ),
            },
            emitted_at="2026-07-14T09:00:00+09:00",
        ),
        _event(
            813,
            "000813",
            "target-first",
            "holding_observation",
            {
                "current_price_observed": 10130,
                "market_data_effective_best_bid": 10130,
                "market_data_effective_best_ask": 10140,
            },
            emitted_at="2026-07-14T09:01:00+09:00",
            pipeline="HOLDING_PIPELINE",
        ),
        _event(
            813,
            "000813",
            "target-first",
            "holding_observation",
            {
                "current_price_observed": 9900,
                "market_data_effective_best_bid": 9900,
                "market_data_effective_best_ask": 9910,
            },
            emitted_at="2026-07-14T09:05:00+09:00",
            pipeline="HOLDING_PIPELINE",
        ),
        _event(
            999,
            "000999",
            "watermark",
            "holding_observation",
            {"current_price_observed": 10000},
            emitted_at="2026-07-14T10:01:00+09:00",
            pipeline="HOLDING_PIPELINE",
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows), encoding="utf-8"
    )

    report = mod.build_report(
        "2026-07-14", pipeline_path=pipeline_path, generated_at="fixed"
    )

    label = report["rising_missed_tp1_counterfactual_first_hit_label_rows"][0]
    assert label["gross_first_hit_label"] == "gross_target_first"
    assert label["post_block_late_recovery_after_adverse"] == {
        "detected": False,
        "first_adverse_ts": None,
        "first_adverse_move_pct": None,
        "first_target_after_adverse_ts": None,
        "first_target_after_adverse_move_pct": None,
        "first_recovery_horizon_min": None,
        "reason": "not_observed",
    }
    summary = report["summary"]
    assert summary["rising_missed_tp1_counterfactual_direct_target_first_count"] == 1
    assert (
        summary[
            "rising_missed_tp1_counterfactual_direct_target_first_unique_symbol_count"
        ]
        == 1
    )
    assert (
        summary[
            "rising_missed_tp1_counterfactual_direct_target_first_source_quality_gap_count"
        ]
        == 0
    )
    assert (
        summary["rising_missed_tp1_counterfactual_direct_target_first_row_export_count"]
        == 1
    )
    assert (
        summary[
            "rising_missed_tp1_counterfactual_direct_target_first_row_omitted_count"
        ]
        == 0
    )
    assert not summary[
        "rising_missed_tp1_counterfactual_direct_target_first_row_export_truncated"
    ]
    assert summary[
        "rising_missed_tp1_counterfactual_direct_target_first_selector_counts"
    ] == [{"selector_reason": "rising_missed_tp1_lane_not_eligible", "count": 1}]
    assert summary[
        "rising_missed_tp1_counterfactual_direct_target_first_ai_action_counts"
    ] == [{"ai_action": "unknown", "count": 1}]
    assert summary["rising_missed_tp1_counterfactual_detail_row_export_count"] == 1
    assert summary["rising_missed_tp1_counterfactual_detail_row_omitted_count"] == 0
    assert (
        summary["rising_missed_tp1_counterfactual_detail_row_export_truncated"] is False
    )
    direct_rows = report["rising_missed_tp1_counterfactual_direct_target_first_rows"]
    assert len(direct_rows) == 1
    assert direct_rows[0]["stock_code"] == "000813"
    assert direct_rows[0]["entry_price_source"] == (
        "market_data_effective_bbo:best_ask"
    )
    assert direct_rows[0]["first_hit_price_source"] == (
        "market_data_effective_bbo:best_bid"
    )
    assert direct_rows[0]["decision_authority"] == (
        "source_only_tp1_direct_target_first_attribution"
    )
    assert direct_rows[0]["actual_order_submitted"] is False
    assert direct_rows[0]["broker_order_forbidden"] is True


def test_tp1_direct_target_first_attribution_excludes_unknown_venue_session():
    base = {
        "gross_first_hit_label": "gross_target_first",
        "entry_executable_bbo_state": "pass",
        "entry_price_source": "market_data_effective_bbo:best_ask",
        "first_hit_ts": "2026-07-14T09:01:00+09:00",
        "first_hit_price_source": "market_data_effective_bbo:best_bid",
        "stock_code": "000814",
        "effective_venue": "KRX",
        "market_session_bucket": "krx_regular",
    }
    summary, rows = mod._tp1_counterfactual_direct_target_first_attribution(
        [
            base,
            {**base, "stock_code": "000815", "effective_venue": "unknown"},
            {**base, "stock_code": "000816", "first_hit_price_source": None},
        ]
    )

    assert summary["rising_missed_tp1_counterfactual_direct_target_first_count"] == 1
    assert (
        summary[
            "rising_missed_tp1_counterfactual_direct_target_first_source_quality_gap_count"
        ]
        == 2
    )
    assert [row["stock_code"] for row in rows] == ["000814"]


def test_tp1_counterfactual_submit_safety_is_aggregated_without_label_duplication(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline_events_2026-07-14.jsonl"
    rows = [
        _event(
            801,
            "000801",
            "recheck",
            "rising_missed_tp1_counterfactual_submit_safety",
            {
                "selector_reason": "rising_missed_tp1_insufficient_positive_support",
                "selector_deferred": False,
                "rising_missed_tp1_candidate_allowed": False,
                "rising_missed_tp1_counterfactual_submit_safety_action": "RECHECK_REQUIRED",
                "rising_missed_tp1_counterfactual_submit_safety_risks": (
                    "spread_above_candidate_caution,momentum_support_weak"
                ),
                "rising_missed_tp1_positive_support_count": 1,
                "rising_missed_tp1_positive_support_families": "depth",
                "market_data_effective_price_source": "ws",
                "market_data_ws_quote_age_ms": "50",
                "market_data_rest_quote_age_ms": "100",
                "rising_missed_tp1_micro_confidence": "0.85",
                "rising_missed_tp1_true_ofi_ewma": "0.12",
            },
        ),
        _event(
            802,
            "000802",
            "defer",
            "rising_missed_tp1_counterfactual_submit_safety",
            {
                "selector_reason": "tp1_effective_quote_stale",
                "selector_deferred": True,
                "rising_missed_tp1_candidate_allowed": False,
                "rising_missed_tp1_counterfactual_submit_safety_action": (
                    "INPUT_DEFER_EXPECTED"
                ),
                "rising_missed_tp1_counterfactual_submit_safety_risks": "-",
                "rising_missed_tp1_positive_support_count": 0,
                "rising_missed_tp1_positive_support_families": "-",
            },
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows), encoding="utf-8"
    )

    report = mod.build_report(
        "2026-07-14", pipeline_path=pipeline_path, generated_at="fixed"
    )
    summary = report["summary"]

    assert summary["rising_missed_tp1_counterfactual_submit_safety_count"] == 2
    assert summary["rising_missed_tp1_counterfactual_unique_symbol_count"] == 2
    assert summary["rising_missed_tp1_counterfactual_action_counts"] == [
        {"action": "RECHECK_REQUIRED", "count": 1},
        {"action": "INPUT_DEFER_EXPECTED", "count": 1},
    ]
    assert summary["rising_missed_tp1_counterfactual_risk_counts"] == [
        {"risk": "spread_above_candidate_caution", "count": 1},
        {"risk": "momentum_support_weak", "count": 1},
    ]
    assert report["rising_missed_tp1_first_hit_label_rows"] == []
    assert all(
        row["actual_order_submitted"] is False
        and row["broker_order_forbidden"] is True
        and row["runtime_effect"] is False
        for row in report["rising_missed_tp1_counterfactual_submit_safety_rows"]
    )
    context_row = report["rising_missed_tp1_counterfactual_submit_safety_rows"][0]
    assert context_row["effective_price_source"] == "ws"
    assert context_row["ws_quote_age_ms"] == 50.0
    assert context_row["micro_confidence"] == 0.85
    assert context_row["true_ofi_ewma"] == 0.12


def test_submit_safety_source_quality_unknown_breakdown_is_structured(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-15.jsonl"
    pipeline_path.write_text(
        json.dumps(
            _event(
                901,
                "000901",
                "missing-pressure",
                "real_weak_ai_micro_entry_block",
                {
                    "forced_entry_reason": "rising_missed_one_share_entry",
                    "reason": "source_quality_unknown",
                    "source_quality_gate": "weak_ai_micro_context_contract",
                    "weak_ai_micro_entry_block_source_quality_state": "missing",
                    "weak_ai_micro_entry_block_missing_fields": "buy_pressure_10t,tick_aggressor_pressure",
                    "weak_ai_micro_entry_block_buy_pressure_usable": False,
                    "weak_ai_micro_entry_block_tick_aggressor_pressure_usable": False,
                    "weak_ai_micro_entry_block_ai_action": "WAIT",
                    "weak_ai_micro_entry_block_ai_score": "0",
                    "orderbook_micro_state": "neutral",
                    "orderbook_micro_reason": "ready",
                },
            )
        ),
        encoding="utf-8",
    )

    report = mod.build_report(
        "2026-07-15", pipeline_path=pipeline_path, generated_at="fixed"
    )

    block = report["submit_safety_blocker_rows"][0]
    assert block["source_quality_missing_fields"] == [
        "buy_pressure_10t",
        "tick_aggressor_pressure",
    ]
    assert block["ai_action"] == "WAIT"
    assert block["ai_score"] == 0.0
    assert block["buy_pressure_usable"] is False
    assert block["tick_aggressor_pressure_usable"] is False
    assert report["summary"]["submit_safety_source_quality_unknown_gate_counts"] == [
        {"source_quality_gate": "weak_ai_micro_context_contract", "count": 1}
    ]
    assert report["summary"][
        "submit_safety_source_quality_unknown_missing_field_counts"
    ] == [
        {"missing_field": "buy_pressure_10t", "count": 1},
        {"missing_field": "tick_aggressor_pressure", "count": 1},
    ]


def test_submit_safety_blocker_rows_retain_latest_bounded_window(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-15.jsonl"
    rows = [
        _event(
            1_000 + index,
            f"{index:06d}",
            f"block-{index}",
            "real_weak_ai_micro_entry_block",
            {
                "forced_entry_reason": "rising_missed_one_share_entry",
                "reason": "source_quality_unknown",
                "source_quality_gate": "weak_ai_micro_context_contract",
                "weak_ai_micro_entry_block_source_quality_state": "missing",
                "weak_ai_micro_entry_block_missing_fields": "buy_pressure_10t",
                "current_price": 1_000 + index,
            },
            emitted_at=(f"2026-07-15T09:{index // 60:02d}:{index % 60:02d}+09:00"),
        )
        for index in range(205)
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows), encoding="utf-8"
    )

    report = mod.build_report(
        "2026-07-15", pipeline_path=pipeline_path, generated_at="fixed"
    )

    blockers = report["submit_safety_blocker_rows"]
    assert report["summary"]["submit_safety_block_count"] == 205
    assert len(blockers) == 200
    assert blockers[0]["stock_code"] == "000005"
    assert blockers[-1]["stock_code"] == "000204"


def test_build_report_flags_rising_missed_avg_down_ge2_initial_quality_fail(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-02.jsonl"
    rows = [
        _event(
            101,
            "000101",
            "failer",
            "rising_missed_one_share_entry",
            {
                "forced_entry_reason": "rising_missed_one_share_entry",
                "scanner_promotion_reason": "price_jump_start_acceleration",
                "source_signature": "OPEN_TOP,PRICE_JUMP_START",
                "price_delta_since_first_seen_pct": "4.20",
            },
            emitted_at="2026-07-02T09:01:00",
        ),
        _event(
            101,
            "000101",
            "failer",
            "stat_action_decision_snapshot",
            {
                "avg_down_count": "1",
                "profit_rate": "-1.20",
                "peak_profit": "-0.20",
                "scale_in_gate_reason": "avg_down_candidate",
            },
            emitted_at="2026-07-02T09:05:00",
            pipeline="HOLDING_PIPELINE",
        ),
        _event(
            101,
            "000101",
            "failer",
            "stat_action_decision_snapshot",
            {
                "avg_down_count": "2",
                "profit_rate": "-2.10",
                "peak_profit": "-0.20",
                "exit_rule_candidate": "scalp_soft_stop_pct",
                "sell_reason_type": "LOSS",
                "scale_in_gate_reason": "scale_in_cooldown",
            },
            emitted_at="2026-07-02T09:08:00",
            pipeline="HOLDING_PIPELINE",
        ),
        _event(
            202,
            "000202",
            "normal",
            "rising_missed_one_share_entry",
            {"forced_entry_reason": "rising_missed_one_share_entry"},
        ),
        _event(
            202,
            "000202",
            "normal",
            "stat_action_decision_snapshot",
            {"avg_down_count": "1", "profit_rate": "+0.40"},
            pipeline="HOLDING_PIPELINE",
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows), encoding="utf-8"
    )

    report = mod.build_report(
        "2026-07-02", pipeline_path=pipeline_path, generated_at="fixed"
    )

    assert report["summary"]["forced_rising_missed_record_count"] == 2
    assert report["summary"]["rising_missed_avg_down_ge2_count"] == 1
    assert report["summary"]["initial_quality_fail_count"] == 1
    assert report["summary"]["consumer_readiness"] == {
        "scout_workorder_input_ready": True,
        "closed_first_touch_outcome_available": False,
        "code_improvement_order_available": True,
        "state": "actionable_source_rows",
    }
    record = report["records"][0]
    assert record["record_id"] == "101"
    assert record["feedback_label"] == "rising_missed_initial_quality_fail"
    assert record["max_avg_down_count"] == 2
    assert record["min_profit_seen"] == -2.1
    order = report["code_improvement_orders"][0]
    assert order["mapped_family"] == "rising_missed_initial_quality_feedback_loop"
    assert order["runtime_effect"] is False
    assert order["allowed_runtime_apply"] is False
    assert "intraday_runtime_apply" in order["forbidden_uses"]


def test_write_outputs_renders_json_and_markdown(tmp_path):
    report = {
        "target_date": "2026-07-02",
        "generated_at": "fixed",
        "summary": {
            "forced_rising_missed_record_count": 1,
            "holding_record_count": 1,
            "rising_missed_avg_down_ge2_count": 1,
            "initial_quality_fail_count": 1,
            "scale_in_rescue_warning_count": 0,
            "code_improvement_order_count": 1,
            "first_touch_entry_submitted_count": 1,
            "submit_safety_source_quality_unknown_missing_field_counts": [
                {"missing_field": "buy_pressure_10t", "count": 1}
            ],
        },
        "records": [
            {
                "record_id": "101",
                "stock_code": "000101",
                "stock_name": "failer",
                "feedback_label": "rising_missed_initial_quality_fail",
                "max_avg_down_count": 2,
                "latest_profit_rate": -2.1,
                "min_profit_seen": -2.1,
                "max_profit_seen": -1.2,
                "latest_gate_reason": "scale_in_cooldown",
            }
        ],
        "dynamic_age_post_apply_attribution_rows": [
            {
                "ts": "2026-07-02T09:00:00+09:00",
                "stock_code": "000102",
                "stock_name": "dynamic-age",
                "effective_venue": "KRX",
                "dynamic_age_source_stage": "latency_pass",
                "downstream_terminal_stage": "pre_submit_entry_ai_authority_guard_block",
                "entry_executable_best_ask": 1000.0,
                "first_hit": "not_observed",
                "first_hit_elapsed_sec": None,
                "actual_order_submitted": False,
                "horizons": {"1m": {"event_count": 2, "mfe_pct": 0.1, "mae_pct": -0.2}},
                "decision_authority": "source_only_dynamic_age_post_apply_attribution",
            }
        ],
        "rising_missed_tp1_counterfactual_first_hit_label_rows": [
            {
                "candidate_ts": "2026-07-02T09:00:00",
                "stock_code": "000901",
                "stock_name": "context",
                "selector_reason": "rising_missed_tp1_insufficient_positive_support",
                "counterfactual_action": "RECHECK_REQUIRED",
                "counterfactual_risks": ["momentum_support_weak"],
                "gross_first_hit_label": "gross_target_first",
                "entry_price": 1000.0,
                "effective_price_source": "ws",
                "ws_quote_age_ms": 50.0,
                "rest_quote_age_ms": 100.0,
                "ws_rest_gap_bps": 4.0,
                "spread_ratio": 0.001,
                "true_ofi_ewma": 0.12,
                "pressure_ewma": 55.0,
                "depth_imbalance_ewma": 0.1,
                "tick_acceleration": 1.2,
                "micro_source_state": "fresh_ws_order_flow_delta",
            }
        ],
        "rising_missed_tp1_counterfactual_direct_target_first_rows": [
            {
                "candidate_ts": "2026-07-02T09:00:00",
                "stock_code": "000901",
                "stock_name": "context",
                "effective_venue": "KRX",
                "market_session_bucket": "krx_regular",
                "selector_reason": "rising_missed_tp1_lane_not_eligible",
                "ai_action": "WAIT",
                "entry_price": 1000.0,
                "entry_price_source": "market_data_effective_bbo:best_ask",
                "first_hit_ts": "2026-07-02T09:01:00+09:00",
                "first_hit_move_pct": 1.3,
                "first_hit_price_source": "market_data_effective_bbo:best_bid",
                "decision_authority": (
                    "source_only_tp1_direct_target_first_attribution"
                ),
            }
        ],
        "first_touch_regression_rows": [
            {
                "record_id": "101",
                "stock_code": "000101",
                "stock_name": "failer",
                "first_touch_regression_label": "first_touch_loss_or_flat",
                "entry_order_submitted": True,
                "entry_order_submitted_count": 1,
                "first_touch_avg_down_submitted": True,
                "first_touch_profit_rate": -3.1,
                "first_touch_peak_profit": -0.2,
                "first_touch_ai_score": 66.0,
                "final_profit_rate": -2.1,
                "avg_down_submitted_event_count": 2,
                "max_avg_down_count": 2,
                "blocker_counts_before_first_touch": {"blocked_strength_momentum": 1},
            }
        ],
    }
    output_json = tmp_path / "report.json"
    output_md = tmp_path / "report.md"

    mod.write_outputs(report, output_json=output_json, output_md=output_md)

    assert (
        json.loads(output_json.read_text(encoding="utf-8"))["target_date"]
        == "2026-07-02"
    )
    markdown = output_md.read_text(encoding="utf-8")
    assert "rising_missed_avg_down_ge2_count: 1" in markdown
    assert "## First Touch Regression" in markdown
    assert "entry_submitted=True" in markdown
    assert "entry_submit_count=1" in markdown
    assert "avgdown_submitted_count=2" in markdown
    assert "shadow_cap1=-" in markdown
    assert "rising_missed_initial_quality_fail" in markdown
    assert "submit_safety_source_quality_unknown_missing_field_counts" in markdown
    assert "## TP1 Counterfactual First-hit Labels" in markdown
    assert "ws_age_ms=50.0" in markdown
    assert "## TP1 Direct Target-first Attribution" in markdown
    assert "entry_source=market_data_effective_bbo:best_ask" in markdown
    assert "first_hit_source=market_data_effective_bbo:best_bid" in markdown
    assert "## Dynamic-age Post-apply Attribution" in markdown
    assert "horizons=1m:n=2/mfe=0.1/mae=-0.2" in markdown


def test_profit_recovered_sell_order_is_rescue_warning_not_initial_fail(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-02.jsonl"
    rows = [
        _event(
            303,
            "000303",
            "recovered",
            "rising_missed_one_share_entry",
            {"forced_entry_reason": "rising_missed_one_share_entry"},
        ),
        _event(
            303,
            "000303",
            "recovered",
            "stat_action_decision_snapshot",
            {"avg_down_count": "2", "profit_rate": "+0.80", "peak_profit": "+1.30"},
            pipeline="HOLDING_PIPELINE",
        ),
        _event(
            303,
            "000303",
            "recovered",
            "sell_order_sent",
            {
                "avg_down_count": "2",
                "profit_rate": "+1.10",
                "peak_profit": "+1.30",
                "exit_rule_candidate": "scalp_trailing_take_profit",
                "sell_reason_type": "PROFIT",
            },
            pipeline="HOLDING_PIPELINE",
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows), encoding="utf-8"
    )

    report = mod.build_report(
        "2026-07-02", pipeline_path=pipeline_path, generated_at="fixed"
    )

    assert report["summary"]["initial_quality_fail_count"] == 0
    assert report["summary"]["scale_in_rescue_warning_count"] == 1
    assert (
        report["records"][0]["feedback_label"]
        == "rising_missed_scale_in_rescue_warning"
    )


def test_build_report_adds_continuously_updated_first_touch_regression_rows(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-03.jsonl"
    rows = [
        _event(
            401,
            "000401",
            "winner",
            "rising_missed_one_share_entry",
            {
                "forced_entry_reason": "rising_missed_one_share_entry",
                "source_signature": "OPEN_TOP,PRICE_JUMP_START",
            },
            emitted_at="2026-07-03T08:03:00",
        ),
        _event(
            401,
            "000401",
            "winner",
            "blocked_strength_momentum",
            {"block_reason": "below_strength_base"},
            emitted_at="2026-07-03T08:04:00",
        ),
        _event(
            401,
            "000401",
            "winner",
            "stop_line_touch_mandatory_avg_down_candidate",
            {
                "profit_rate": "-3.42",
                "peak_profit": "-0.23",
                "current_ai_score": "65",
                "gate_reason": "ok",
                "first_touch_avgdown_ai_score_usable": True,
                "first_touch_avgdown_ai_score_source": "live",
                "first_touch_avgdown_ai_score_data_quality": "fresh",
            },
            emitted_at="2026-07-03T08:06:00",
            pipeline="HOLDING_PIPELINE",
        ),
        _event(
            401,
            "000401",
            "winner",
            "stop_line_touch_mandatory_avg_down_submitted",
            {
                "profit_rate": "-3.42",
                "peak_profit": "-0.23",
                "current_ai_score": "65",
                "gate_reason": "ok",
            },
            emitted_at="2026-07-03T08:06:01",
            pipeline="HOLDING_PIPELINE",
        ),
        _event(
            401,
            "000401",
            "winner",
            "sell_completed",
            {"profit_rate": "+1.09"},
            emitted_at="2026-07-03T08:07:00",
            pipeline="HOLDING_PIPELINE",
        ),
        _event(
            402,
            "000402",
            "loser",
            "rising_missed_one_share_entry",
            {"forced_entry_reason": "rising_missed_one_share_entry"},
            emitted_at="2026-07-03T08:03:10",
        ),
        _event(
            402,
            "000402",
            "loser",
            "blocked_strength_momentum",
            {"block_reason": "insufficient_history"},
            emitted_at="2026-07-03T08:04:10",
        ),
        _event(
            402,
            "000402",
            "loser",
            "stop_line_touch_mandatory_avg_down_candidate",
            {
                "profit_rate": "-3.33",
                "peak_profit": "-0.23",
                "current_ai_score": "67",
                "gate_reason": "ok",
                "first_touch_avgdown_ai_score_usable": True,
                "first_touch_avgdown_ai_score_source": "live",
                "first_touch_avgdown_ai_score_data_quality": "fresh",
            },
            emitted_at="2026-07-03T08:17:00",
            pipeline="HOLDING_PIPELINE",
        ),
        _event(
            402,
            "000402",
            "loser",
            "stop_line_touch_mandatory_avg_down_submitted",
            {
                "profit_rate": "-3.33",
                "peak_profit": "-0.23",
                "current_ai_score": "67",
                "gate_reason": "ok",
            },
            emitted_at="2026-07-03T08:17:01",
            pipeline="HOLDING_PIPELINE",
        ),
        _event(
            402,
            "000402",
            "loser",
            "stop_line_touch_mandatory_avg_down_submitted",
            {
                "profit_rate": "-3.05",
                "peak_profit": "-0.23",
                "current_ai_score": "67",
                "gate_reason": "ok",
            },
            emitted_at="2026-07-03T08:31:00",
            pipeline="HOLDING_PIPELINE",
        ),
        _event(
            402,
            "000402",
            "loser",
            "sell_completed",
            {"profit_rate": "-4.64"},
            emitted_at="2026-07-03T08:34:00",
            pipeline="HOLDING_PIPELINE",
        ),
        _event(
            403,
            "000403",
            "blocked",
            "rising_missed_one_share_entry",
            {"forced_entry_reason": "rising_missed_one_share_entry"},
            emitted_at="2026-07-03T08:03:20",
        ),
        _event(
            403,
            "000403",
            "blocked",
            "blocked_strength_momentum",
            {"block_reason": "below_strength_base"},
            emitted_at="2026-07-03T08:04:20",
        ),
        _event(
            403,
            "000403",
            "blocked",
            "stop_line_touch_first_touch_avgdown_decision_blocked",
            {
                "profit_rate": "-3.89",
                "peak_profit": "-0.10",
                "current_ai_score": "66",
                "gate_reason": "repeated_blockers_without_recovery",
                "first_touch_avgdown_decision_allowed": False,
                "first_touch_avgdown_decision_reason": "repeated_blockers_without_recovery",
                "first_touch_avgdown_support_signals": "quote_spread_present",
                "first_touch_avgdown_risk_signals": "repeated_blockers_without_support",
                "first_touch_avgdown_repeated_blocker_count": 11,
                "first_touch_avgdown_decision_authority": "real_scalping_first_touch_avgdown_decision_gate",
                "first_touch_avgdown_ai_score_usable": True,
                "first_touch_avgdown_ai_score_source": "live",
                "first_touch_avgdown_ai_score_data_quality": "fresh",
            },
            emitted_at="2026-07-03T08:20:00",
            pipeline="HOLDING_PIPELINE",
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows), encoding="utf-8"
    )

    report = mod.build_report(
        "2026-07-03", pipeline_path=pipeline_path, generated_at="fixed"
    )

    assert report["summary"]["first_touch_regression_record_count"] == 3
    assert report["summary"]["first_touch_entry_submitted_count"] == 0
    assert report["summary"]["first_touch_avg_down_submitted_count"] == 2
    assert report["summary"]["first_touch_avgdown_decision_blocked_count"] == 1
    assert report["summary"]["first_touch_closed_count"] == 2
    assert report["summary"]["first_touch_profitable_count"] == 1
    assert report["summary"]["first_touch_loss_or_flat_count"] == 1
    rows_by_record = {
        row["record_id"]: row for row in report["first_touch_regression_rows"]
    }
    assert (
        rows_by_record["401"]["first_touch_regression_label"]
        == "first_touch_recovered_profit"
    )
    assert rows_by_record["401"]["entry_order_submitted"] is False
    assert rows_by_record["401"]["entry_order_submitted_count"] == 0
    assert rows_by_record["401"]["blocker_counts_before_first_touch"] == {
        "blocked_strength_momentum": 1
    }
    assert (
        rows_by_record["401"]["first_touch_shadow_cap1_decision"]
        == "cap1_first_avg_down_allowed"
    )
    assert (
        rows_by_record["402"]["first_touch_regression_label"]
        == "first_touch_loss_or_flat"
    )
    assert rows_by_record["402"]["avg_down_submitted_event_count"] == 2
    assert (
        rows_by_record["402"]["first_touch_shadow_cap1_decision"]
        == "cap1_extra_avg_down_would_block"
    )
    assert (
        "cap1_extra_avg_down_would_block"
        in rows_by_record["402"]["first_touch_shadow_risk_signals"]
    )
    assert (
        rows_by_record["403"]["first_touch_regression_label"]
        == "first_touch_open_unresolved"
    )
    assert rows_by_record["403"]["first_touch_avgdown_decision_blocked"] is True
    assert rows_by_record["403"]["first_touch_avgdown_decision_allowed"] is False
    assert rows_by_record["403"]["actual_order_submitted"] is False
    assert rows_by_record["403"]["broker_order_forbidden"] is True
    assert (
        rows_by_record["403"]["first_touch_avgdown_decision_reason"]
        == "repeated_blockers_without_recovery"
    )
    assert rows_by_record["403"]["first_touch_avgdown_decision_authority"] == (
        "real_scalping_first_touch_avgdown_decision_gate"
    )
    assert (
        report["metric_contracts"]["rising_missed_first_touch_regression"][
            "decision_authority"
        ]
        == "source_only_first_touch_regression_table"
    )
    assert report["source_quality"]["status"] == "pass"


def test_build_report_captures_real_entry_submit_separately_from_first_touch_avgdown_submit(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline_events_2026-07-08.jsonl"
    rows = [
        _event(
            601,
            "000601",
            "real-entry-only",
            "rising_missed_one_share_entry",
            {"forced_entry_reason": "rising_missed_one_share_entry"},
            emitted_at="2026-07-08T10:00:00",
        ),
        _event(
            601,
            "000601",
            "real-entry-only",
            "order_bundle_submitted",
            {"actual_order_submitted": True, "broker_order_forbidden": False},
            emitted_at="2026-07-08T10:00:05",
        ),
        _event(
            601,
            "000601",
            "real-entry-only",
            "holding_started",
            {"actual_order_submitted": True, "buy_price": "1000", "buy_qty": "1"},
            emitted_at="2026-07-08T10:00:10",
            pipeline="HOLDING_PIPELINE",
        ),
        _event(
            601,
            "000601",
            "real-entry-only",
            "stop_line_touch_first_touch_avgdown_decision_blocked",
            {
                "profit_rate": "-3.10",
                "peak_profit": "0.10",
                "current_ai_score": "57",
                "first_touch_avgdown_decision_allowed": False,
                "first_touch_avgdown_decision_reason": "ai_score_no_submit_authority",
                "first_touch_avgdown_ai_score_usable": False,
                "first_touch_avgdown_ai_score_source": "live",
                "first_touch_avgdown_ai_score_data_quality": "partial",
                "first_touch_reversal_feature_source_quality": "usable",
                "first_touch_reversal_feature_stale": False,
            },
            emitted_at="2026-07-08T10:05:00",
            pipeline="HOLDING_PIPELINE",
        ),
        _event(
            601,
            "000601",
            "real-entry-only",
            "sell_completed",
            {"profit_rate": "-3.14"},
            emitted_at="2026-07-08T10:06:00",
            pipeline="HOLDING_PIPELINE",
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows), encoding="utf-8"
    )

    report = mod.build_report(
        "2026-07-08", pipeline_path=pipeline_path, generated_at="fixed"
    )

    assert report["summary"]["first_touch_entry_submitted_count"] == 1
    row = report["first_touch_regression_rows"][0]
    assert row["entry_order_submitted"] is True
    assert row["entry_order_submitted_count"] == 1
    assert row["entry_fill_seen"] is True
    assert row["entry_fill_seen_count"] == 1
    assert row["first_touch_avg_down_submitted"] is False
    assert row["avg_down_submitted_event_count"] == 0
    assert report["summary"]["rising_missed_submit_lineage_record_count"] == 1
    assert report["summary"]["rising_missed_entry_submitted_count"] == 1
    assert report["summary"]["rising_missed_order_bundle_submitted_count"] == 1
    submit_row = report["rising_missed_submit_lineage_rows"][0]
    assert submit_row["entry_order_submitted"] is True
    assert submit_row["order_bundle_submitted_count"] == 1
    assert submit_row["submit_lineage_join_method"] == "record_id"


def test_build_report_joins_forced_plan_to_submit_by_code_time_when_lineage_fields_missing(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline_events_2026-07-10.jsonl"
    rows = [
        _event(
            701,
            "000701",
            "lineage-missing",
            "rising_missed_one_share_entry",
            {
                "forced_entry_reason": "rising_missed_one_share_entry",
                "source_signature": "OPEN_TOP,REALTIME_RANK_START,VALUE_TOP",
            },
            emitted_at="2026-07-10T10:00:00",
        ),
        _event(
            701,
            "000701",
            "lineage-missing",
            "rising_missed_one_share_entry_order_plan_forced",
            {
                "planned_order_price": "170100",
                "forced_entry_qty": "1",
            },
            emitted_at="2026-07-10T10:00:02",
        ),
        _event(
            999,
            "000701",
            "lineage-missing",
            "order_leg_sent",
            {
                "order_no": "0027316",
                "source_signature": "OPEN_TOP,REALTIME_RANK_START,VALUE_TOP",
            },
            emitted_at="2026-07-10T10:00:05",
        ),
        _event(
            999,
            "000701",
            "lineage-missing",
            "order_bundle_submitted",
            {
                "actual_order_submitted": True,
                "broker_order_forbidden": False,
                "order_no": "0027316",
                "order_price": "170100",
                "source_signature": "OPEN_TOP,REALTIME_RANK_START,VALUE_TOP",
            },
            emitted_at="2026-07-10T10:00:08",
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows), encoding="utf-8"
    )

    report = mod.build_report(
        "2026-07-10", pipeline_path=pipeline_path, generated_at="fixed"
    )

    assert report["summary"]["rising_missed_submit_lineage_record_count"] == 1
    assert report["summary"]["rising_missed_order_plan_forced_count"] == 1
    assert report["summary"]["rising_missed_entry_submitted_count"] == 1
    assert report["summary"]["rising_missed_order_leg_sent_count"] == 1
    row = report["rising_missed_submit_lineage_rows"][0]
    assert row["record_id"] == "701"
    assert row["submit_lineage_join_method"] == "code_time_window"
    assert row["primary_order_no"] == "0027316"
    assert row["submitted_order_price"] == "170100"
    assert row["actual_order_submitted"] is False
    assert row["broker_order_forbidden"] is True
    assert row["decision_authority"] == "source_only_rising_missed_submit_lineage"


def test_first_touch_regression_blocks_source_quality_when_ai_provenance_missing(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline_events_2026-07-03.jsonl"
    rows = [
        _event(
            501,
            "000501",
            "missing-ai-provenance",
            "rising_missed_one_share_entry",
            {"forced_entry_reason": "rising_missed_one_share_entry"},
            emitted_at="2026-07-03T08:03:00",
        ),
        _event(
            501,
            "000501",
            "missing-ai-provenance",
            "stop_line_touch_mandatory_avg_down_candidate",
            {
                "profit_rate": "-3.42",
                "peak_profit": "-0.23",
                "current_ai_score": "65",
                "gate_reason": "ok",
            },
            emitted_at="2026-07-03T08:06:00",
            pipeline="HOLDING_PIPELINE",
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows), encoding="utf-8"
    )

    report = mod.build_report(
        "2026-07-03", pipeline_path=pipeline_path, generated_at="fixed"
    )

    assert report["source_quality"]["status"] == "first_touch_ai_provenance_missing"
    assert report["summary"]["first_touch_ai_provenance_missing_count"] == 1


def test_first_touch_regression_does_not_require_ai_provenance_when_not_eligible(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline_events_2026-07-03.jsonl"
    rows = [
        _event(
            504,
            "000504",
            "deterministic-not-eligible",
            "rising_missed_one_share_entry",
            {"forced_entry_reason": "rising_missed_one_share_entry"},
            emitted_at="2026-07-03T08:03:00",
        ),
        _event(
            504,
            "000504",
            "deterministic-not-eligible",
            "stop_line_touch_mandatory_avg_down_not_eligible",
            {
                "profit_rate": "-3.04",
                "peak_profit": "0.04",
                "current_ai_score": "45",
                "gate_reason": "deep_recovery_pnl_out_of_range",
            },
            emitted_at="2026-07-03T08:06:00",
            pipeline="HOLDING_PIPELINE",
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows), encoding="utf-8"
    )

    report = mod.build_report(
        "2026-07-03", pipeline_path=pipeline_path, generated_at="fixed"
    )

    row = report["first_touch_regression_rows"][0]
    assert row["first_touch_not_eligible_seen"] is True
    assert row["first_touch_not_eligible_reason"] == "deep_recovery_pnl_out_of_range"
    assert report["summary"]["first_touch_ai_provenance_missing_count"] == 0
    assert report["source_quality"]["status"] == "pass"


def test_first_touch_regression_accepts_runtime_usable_holding_ai_not_called_score(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline_events_2026-07-03.jsonl"
    rows = [
        _event(
            505,
            "000505",
            "usable-prior-score",
            "rising_missed_one_share_entry",
            {"forced_entry_reason": "rising_missed_one_share_entry"},
            emitted_at="2026-07-03T08:03:00",
        ),
        _event(
            505,
            "000505",
            "usable-prior-score",
            "stop_line_touch_mandatory_avg_down_candidate",
            {
                "profit_rate": "-3.42",
                "peak_profit": "-0.23",
                "current_ai_score": "65",
                "gate_reason": "ok",
                "first_touch_avgdown_ai_score_usable": True,
                "first_touch_avgdown_ai_score_source": "holding_ai_not_called",
                "first_touch_avgdown_ai_score_data_quality": "fresh",
            },
            emitted_at="2026-07-03T08:06:00",
            pipeline="HOLDING_PIPELINE",
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows), encoding="utf-8"
    )

    report = mod.build_report(
        "2026-07-03", pipeline_path=pipeline_path, generated_at="fixed"
    )

    assert report["source_quality"]["status"] == "pass"
    assert report["summary"]["first_touch_ai_provenance_unusable_count"] == 0


def test_first_touch_regression_blocks_source_quality_when_micro_provenance_unusable(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline_events_2026-07-03.jsonl"
    rows = [
        _event(
            502,
            "000502",
            "stale-micro",
            "rising_missed_one_share_entry",
            {"forced_entry_reason": "rising_missed_one_share_entry"},
            emitted_at="2026-07-03T08:03:00",
        ),
        _event(
            502,
            "000502",
            "stale-micro",
            "stop_line_touch_first_touch_avgdown_decision_blocked",
            {
                "profit_rate": "-3.42",
                "peak_profit": "-0.23",
                "current_ai_score": "65",
                "gate_reason": "micro_context_stale_ignored",
                "first_touch_avgdown_decision_allowed": False,
                "first_touch_avgdown_decision_reason": "insufficient_first_touch_recovery_confirmation",
                "first_touch_avgdown_support_signals": "buy_pressure_support",
                "first_touch_avgdown_risk_signals": "micro_context_stale_ignored",
                "first_touch_avgdown_ai_score_usable": True,
                "first_touch_avgdown_ai_score_source": "live",
                "first_touch_avgdown_ai_score_data_quality": "fresh",
                "first_touch_reversal_feature_source_quality": "stale",
                "first_touch_reversal_feature_stale": True,
                "first_touch_reversal_feature_stale_reason": "micro_vwap_unavailable",
            },
            emitted_at="2026-07-03T08:06:00",
            pipeline="HOLDING_PIPELINE",
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows), encoding="utf-8"
    )

    report = mod.build_report(
        "2026-07-03", pipeline_path=pipeline_path, generated_at="fixed"
    )

    assert report["source_quality"]["status"] == "first_touch_micro_provenance_unusable"
    assert report["summary"]["first_touch_micro_provenance_unusable_count"] == 1


def test_first_touch_regression_blocks_source_quality_when_pressure_provenance_missing(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline_events_2026-07-03.jsonl"
    rows = [
        _event(
            503,
            "000503",
            "missing-pressure",
            "rising_missed_one_share_entry",
            {"forced_entry_reason": "rising_missed_one_share_entry"},
            emitted_at="2026-07-03T08:03:00",
        ),
        _event(
            503,
            "000503",
            "missing-pressure",
            "stop_line_touch_first_touch_avgdown_decision_blocked",
            {
                "profit_rate": "-3.42",
                "peak_profit": "-0.23",
                "current_ai_score": "65",
                "first_touch_avgdown_decision_allowed": False,
                "first_touch_avgdown_decision_reason": "insufficient_first_touch_recovery_confirmation",
                "first_touch_avgdown_support_signals": "buy_pressure_support|tick_accel_support",
                "first_touch_avgdown_risk_signals": "",
                "first_touch_avgdown_ai_score_usable": True,
                "first_touch_avgdown_ai_score_source": "live",
                "first_touch_avgdown_ai_score_data_quality": "fresh",
                "first_touch_reversal_feature_source_quality": "usable",
                "first_touch_reversal_feature_stale": False,
                "buy_pressure_10t": "78.0",
                "tick_acceleration_ratio": "1.25",
            },
            emitted_at="2026-07-03T08:06:00",
            pipeline="HOLDING_PIPELINE",
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows), encoding="utf-8"
    )

    report = mod.build_report(
        "2026-07-03", pipeline_path=pipeline_path, generated_at="fixed"
    )

    assert (
        report["source_quality"]["status"] == "first_touch_pressure_provenance_missing"
    )
    assert report["summary"]["first_touch_pressure_provenance_missing_count"] == 1


def test_first_touch_regression_blocks_source_quality_when_micro_vwap_provenance_missing(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline_events_2026-07-03.jsonl"
    rows = [
        _event(
            504,
            "000504",
            "missing-minute",
            "rising_missed_one_share_entry",
            {"forced_entry_reason": "rising_missed_one_share_entry"},
            emitted_at="2026-07-03T08:03:00",
        ),
        _event(
            504,
            "000504",
            "missing-minute",
            "stop_line_touch_first_touch_avgdown_decision_blocked",
            {
                "profit_rate": "-3.42",
                "peak_profit": "-0.23",
                "current_ai_score": "65",
                "first_touch_avgdown_decision_allowed": False,
                "first_touch_avgdown_decision_reason": "insufficient_first_touch_recovery_confirmation",
                "first_touch_avgdown_support_signals": "micro_vwap_non_negative",
                "first_touch_avgdown_risk_signals": "",
                "first_touch_avgdown_ai_score_usable": True,
                "first_touch_avgdown_ai_score_source": "live",
                "first_touch_avgdown_ai_score_data_quality": "fresh",
                "first_touch_reversal_feature_source_quality": "usable",
                "first_touch_reversal_feature_stale": False,
                "curr_vs_micro_vwap_bp": "12.0",
            },
            emitted_at="2026-07-03T08:06:00",
            pipeline="HOLDING_PIPELINE",
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows), encoding="utf-8"
    )

    report = mod.build_report(
        "2026-07-03", pipeline_path=pipeline_path, generated_at="fixed"
    )

    assert report["source_quality"]["status"] == "first_touch_micro_provenance_missing"
    assert report["summary"]["first_touch_micro_provenance_missing_count"] == 1


def test_submit_safety_breakdown_and_backoff_opportunity_audit_are_source_only(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline_events_2026-07-10.jsonl"
    rows = [
        _event(
            701,
            "000701",
            "stale-ai-wait",
            "rising_missed_scout_quality_guard_blocked",
            {
                "forced_entry_reason": "rising_missed_one_share_entry",
                "block_reason": "stale_quote_with_weak_ai_or_strength",
                "current_price": "1000",
                "price_delta_since_first_seen_pct": "1.20",
                "rising_missed_scout_quality_guard_quote_age_ms": "4500",
                "rising_missed_scout_quality_guard_max_quote_age_ms": "3000",
                "rising_missed_scout_quality_guard_quote_stale": True,
                "rising_missed_scout_quality_guard_weak_evidence": True,
                "rising_missed_scout_quality_guard_ai_action": "WAIT",
                "rising_missed_scout_quality_guard_ai_score": "58",
                "pre_submit_rest_orderbook_refresh_enabled": True,
                "pre_submit_rest_orderbook_refresh_applied": True,
                "pre_submit_rest_orderbook_refresh_reason": "rest_orderbook_fresh",
                "rising_missed_rest_quote_ai_recheck_attempted": True,
                "rising_missed_rest_quote_ai_recheck_success": True,
            },
            emitted_at="2026-07-10T09:00:00",
        ),
        _event(
            701,
            "000701",
            "stale-ai-wait",
            "scalping_scanner_candidate_observed",
            {
                "current_price": "1030",
                "price_delta_since_first_seen_pct": "2.00",
                "ws_last_0b_age_ms": "100",
            },
            emitted_at="2026-07-10T09:01:00",
        ),
        _event(
            706,
            "000706",
            "stale-ai-missing",
            "rising_missed_scout_quality_guard_blocked",
            {
                "forced_entry_reason": "rising_missed_one_share_entry",
                "block_reason": "stale_quote_with_missing_ai_provenance",
                "current_price": "1500",
                "price_delta_since_first_seen_pct": "1.50",
                "rising_missed_scout_quality_guard_quote_age_ms": "6000",
                "rising_missed_scout_quality_guard_max_quote_age_ms": "3000",
                "rising_missed_scout_quality_guard_quote_stale": True,
                "rising_missed_scout_quality_guard_weak_evidence": False,
                "rising_missed_scout_quality_guard_weak_ai": False,
                "rising_missed_scout_quality_guard_ai_action": "-",
                "rising_missed_scout_quality_guard_ai_score": "50.0",
                "rising_missed_scout_quality_guard_ai_provenance_missing": True,
                "rising_missed_scout_quality_guard_ai_score_defaulted_without_action": True,
            },
            emitted_at="2026-07-10T09:01:30",
        ),
        _event(
            706,
            "000706",
            "stale-ai-missing",
            "scalping_scanner_candidate_observed",
            {
                "current_price": "1530",
                "price_delta_since_first_seen_pct": "2.10",
                "ws_last_0b_age_ms": "100",
            },
            emitted_at="2026-07-10T09:01:45",
        ),
        _event(
            702,
            "000702",
            "true-ofi-block",
            "latency_block",
            {
                "forced_entry_reason": "rising_missed_one_share_entry",
                "reason": "latency_state_danger",
                "current_price": "2000",
                "price_delta_since_first_seen_pct": "2.50",
                "ws_age_ms": "40",
                "spread_ratio": "0.007",
                "latency_danger_detail_reason": "spread_above_caution_below_guard_cap",
                "latency_spread_block_spread_bps": "70.0",
                "latency_spread_relief_micro_estimator_reason": "true_ofi_below_floor",
                "latency_spread_relief_micro_estimator_true_ofi_ewma": "-0.12",
                "latency_spread_relief_micro_estimator_true_ofi_sample_count": "120",
            },
            emitted_at="2026-07-10T09:02:00",
        ),
        _event(
            703,
            "000703",
            "ignored-normal",
            "latency_block",
            {"reason": "latency_state_danger", "current_price": "3000"},
            emitted_at="2026-07-10T09:02:30",
        ),
        _event(
            704,
            "000704",
            "recovered",
            "scalping_scanner_fast_precheck",
            {
                "fast_precheck_result": "budget_reallocated",
                "fast_precheck_reason": "scanner_ws_stale_backoff_active",
                "scanner_budget_reallocation_source": "ws_stale_feedback",
                "price_delta_since_first_seen_pct": "1.00",
                "scanner_rising_missed_source_marker_present": True,
            },
            emitted_at="2026-07-10T09:03:00",
        ),
        _event(
            704,
            "000704",
            "recovered",
            "scalping_scanner_fast_precheck",
            {
                "fast_precheck_result": "eligible_for_heavy_entry_eval",
                "fast_precheck_reason": "fast_precheck_pass",
                "price_delta_since_first_seen_pct": "1.40",
            },
            emitted_at="2026-07-10T09:04:00",
        ),
        _event(
            705,
            "000705",
            "not-recovered",
            "scalping_scanner_fast_precheck",
            {
                "fast_precheck_result": "budget_reallocated",
                "fast_precheck_reason": "submit_safety_backoff_active",
                "rising_missed_budget_reallocation_source": "submit_safety_feedback",
                "price_delta_since_first_seen_pct": "1.10",
                "scanner_rising_missed_source_marker_present": True,
            },
            emitted_at="2026-07-10T09:05:00",
        ),
        _event(
            705,
            "000705",
            "not-recovered",
            "scalping_scanner_watching_runtime_skip",
            {"price_delta_since_first_seen_pct": "2.20"},
            emitted_at="2026-07-10T09:06:00",
        ),
        _event(
            799,
            "000799",
            "clock-anchor",
            "scalping_scanner_runtime_target_attach",
            {"price_delta_since_first_seen_pct": "0.00"},
            emitted_at="2026-07-10T09:09:00",
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows), encoding="utf-8"
    )

    report = mod.build_report(
        "2026-07-10", pipeline_path=pipeline_path, generated_at="fixed"
    )

    assert report["summary"]["submit_safety_block_count"] == 3
    assert report["summary"]["potential_backoff_opportunity_loss_count"] == 0
    assert report["summary"]["backoff_mark_price_opportunity_candidate_count"] == 1
    assert report["summary"]["backoff_executable_source_quality_gap_count"] == 1
    bucket_counts = {
        item["blocker_bucket"]: item["count"]
        for item in report["summary"]["submit_safety_bucket_counts"]
    }
    assert bucket_counts == {
        "ai_wait_after_refresh": 1,
        "latency_true_ofi_below_floor": 1,
        "missing_ai_or_fresh_input": 1,
    }
    stale_row = report["submit_safety_blocker_rows"][0]
    assert stale_row["reason"] == "stale_quote_with_weak_ai_or_strength"
    assert stale_row["quote_age_sec"] == 4.5
    assert stale_row["mfe_after_block_pct"] == 3.0
    assert stale_row["runtime_effect"] is False
    missing_ai_row = report["submit_safety_blocker_rows"][1]
    assert missing_ai_row["reason"] == "stale_quote_with_missing_ai_provenance"
    assert missing_ai_row["blocker_bucket"] == "missing_ai_or_fresh_input"
    assert "ai_provenance_missing" in missing_ai_row["components"]
    assert "weak_ai_score" not in missing_ai_row["components"]
    latency_row = report["submit_safety_blocker_rows"][2]
    assert latency_row["true_ofi_reason"] == "true_ofi_below_floor"
    assert latency_row["spread_bps"] == 70.0
    backoff_rows = {
        item["stock_code"]: item for item in report["backoff_opportunity_audit_rows"]
    }
    assert backoff_rows["000704"]["recovered_eval_after_last_backoff"] is True
    assert backoff_rows["000705"]["potential_backoff_opportunity_loss"] is False
    assert backoff_rows["000705"]["mark_price_opportunity_candidate"] is True
    assert (
        backoff_rows["000705"]["backoff_opportunity_classification"]
        == "mark_price_only_unconfirmed"
    )
    assert backoff_rows["000705"]["backoff_observation_state"] == "mature_unrecovered"
    assert report["summary"]["backoff_active_positive_delta_symbol_count"] == 0
    assert (
        report["metric_contracts"]["rising_missed_submit_safety_blocker_breakdown"][
            "decision_authority"
        ]
        == "source_only_submit_safety_blocker_attribution"
    )


def test_backoff_opportunity_requires_executable_target_first_path(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-08-24.jsonl"
    rows = [
        _event(
            705,
            "000705",
            "executable-backoff",
            "scalping_scanner_fast_precheck",
            {
                "fast_precheck_result": "budget_reallocated",
                "fast_precheck_reason": "submit_safety_backoff_active",
                "rising_missed_budget_reallocation_source": "submit_safety_feedback",
                "price_delta_since_first_seen_pct": "1.10",
                "effective_venue": "KRX",
                "market_data_effective_best_bid": 995,
                "market_data_effective_best_ask": 1000,
                "risky_micro_episode_horizon_observer_registered": True,
                "risky_micro_episode_horizon_observer_status": "registered",
            },
            emitted_at="2026-08-24T09:05:00+09:00",
        ),
        _event(
            705,
            "000705",
            "executable-backoff",
            "risky_micro_episode_executable_bbo_observed",
            {
                "effective_venue": "KRX",
                "market_data_effective_best_bid": 998,
                "market_data_effective_best_ask": 1000,
                "risky_micro_episode_horizon_observer_quote_fresh": True,
                "risky_micro_episode_horizon_observer_purpose": (
                    "rising_missed_backoff_executable_outcome"
                ),
            },
            emitted_at="2026-08-24T09:05:15+09:00",
        ),
        _event(
            705,
            "000705",
            "executable-backoff",
            "risky_micro_episode_executable_bbo_observed",
            {
                "effective_venue": "KRX",
                "market_data_effective_best_bid": 1015,
                "market_data_effective_best_ask": 1020,
                "risky_micro_episode_horizon_observer_quote_fresh": True,
                "risky_micro_episode_horizon_observer_purpose": (
                    "rising_missed_backoff_executable_outcome"
                ),
            },
            emitted_at="2026-08-24T09:06:00+09:00",
        ),
        _event(
            799,
            "000799",
            "clock-anchor",
            "scalping_scanner_runtime_target_attach",
            {"price_delta_since_first_seen_pct": "0.00"},
            emitted_at="2026-08-24T09:09:00+09:00",
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows), encoding="utf-8"
    )

    report = mod.build_report(
        "2026-08-24", pipeline_path=pipeline_path, generated_at="fixed"
    )

    assert report["summary"]["potential_backoff_opportunity_loss_count"] == 1
    assert report["summary"]["backoff_executable_source_quality_pass_count"] == 1
    row = report["backoff_opportunity_audit_rows"][0]
    assert row["potential_backoff_opportunity_loss"] is True
    assert row["executable_sampled_first_hit"] == "sampled_gross_target_first"
    assert row["max_executable_bid_move_pct"] == 1.5
    assert row["backoff_opportunity_classification"] == (
        "executable_confirmed_opportunity_loss"
    )


def test_latency_false_negative_review_selects_only_high_mfe_low_mae_latency_blocks(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline_events_2026-07-10.jsonl"
    rows = [
        _event(
            801,
            "000801",
            "true-ofi-candidate",
            "latency_block",
            {
                "forced_entry_reason": "rising_missed_one_share_entry",
                "reason": "latency_state_danger",
                "current_price": "1000",
                "best_bid_at_submit": "995",
                "best_ask_at_submit": "1000",
                "ws_age_ms": "80",
                "latency_danger_detail_reason": "spread_above_caution_below_guard_cap",
                "latency_spread_block_spread_bps": "62.0",
                "latency_spread_relief_micro_estimator_reason": "true_ofi_below_floor",
                "latency_spread_relief_micro_estimator_true_ofi_ewma": "-0.04",
                "latency_spread_relief_micro_estimator_true_ofi_sample_count": "120",
            },
            emitted_at="2026-07-10T09:10:00",
        ),
        _event(
            801,
            "000801",
            "true-ofi-candidate",
            "scalping_scanner_candidate_observed",
            {
                "current_price": "990",
                "best_bid_at_submit": "990",
                "best_ask_at_submit": "995",
                "ws_last_0b_age_ms": "100",
            },
            emitted_at="2026-07-10T09:10:20",
        ),
        _event(
            801,
            "000801",
            "true-ofi-candidate",
            "scalping_scanner_candidate_observed",
            {
                "current_price": "1045",
                "best_bid_at_submit": "1045",
                "best_ask_at_submit": "1050",
                "ws_last_0b_age_ms": "100",
            },
            emitted_at="2026-07-10T09:10:40",
        ),
        _event(
            802,
            "000802",
            "spread-candidate",
            "latency_block",
            {
                "forced_entry_reason": "rising_missed_one_share_entry",
                "reason": "latency_state_danger",
                "current_price": "2000",
                "best_bid_at_submit": "1995",
                "best_ask_at_submit": "2000",
                "ws_age_ms": "70",
                "latency_danger_detail_reason": "spread_above_caution",
                "latency_spread_block_spread_bps": "55.0",
            },
            emitted_at="2026-07-10T09:11:00",
        ),
        _event(
            802,
            "000802",
            "spread-candidate",
            "scalping_scanner_candidate_observed",
            {
                "current_price": "1980",
                "best_bid_at_submit": "1980",
                "best_ask_at_submit": "1985",
                "ws_last_0b_age_ms": "100",
            },
            emitted_at="2026-07-10T09:11:20",
        ),
        _event(
            802,
            "000802",
            "spread-candidate",
            "scalping_scanner_candidate_observed",
            {
                "current_price": "2070",
                "best_bid_at_submit": "2070",
                "best_ask_at_submit": "2075",
                "ws_last_0b_age_ms": "100",
            },
            emitted_at="2026-07-10T09:11:40",
        ),
        _event(
            803,
            "000803",
            "wide-mae",
            "latency_block",
            {
                "forced_entry_reason": "rising_missed_one_share_entry",
                "reason": "latency_state_danger",
                "current_price": "3000",
                "best_bid_at_submit": "2995",
                "best_ask_at_submit": "3000",
                "latency_danger_detail_reason": "spread_above_caution",
                "latency_spread_block_spread_bps": "58.0",
            },
            emitted_at="2026-07-10T09:12:00",
        ),
        _event(
            803,
            "000803",
            "wide-mae",
            "scalping_scanner_candidate_observed",
            {
                "current_price": "2910",
                "best_bid_at_submit": "2910",
                "best_ask_at_submit": "2915",
                "ws_last_0b_age_ms": "100",
            },
            emitted_at="2026-07-10T09:12:20",
        ),
        _event(
            803,
            "000803",
            "wide-mae",
            "scalping_scanner_candidate_observed",
            {
                "current_price": "3120",
                "best_bid_at_submit": "3120",
                "best_ask_at_submit": "3125",
                "ws_last_0b_age_ms": "100",
            },
            emitted_at="2026-07-10T09:12:40",
        ),
        _event(
            804,
            "000804",
            "stale-not-latency",
            "rising_missed_scout_quality_guard_blocked",
            {
                "forced_entry_reason": "rising_missed_one_share_entry",
                "block_reason": "stale_quote_with_weak_ai_or_strength",
                "current_price": "1000",
                "rising_missed_scout_quality_guard_quote_age_ms": "5000",
                "rising_missed_scout_quality_guard_ai_action": "WAIT",
            },
            emitted_at="2026-07-10T09:13:00",
        ),
        _event(
            804,
            "000804",
            "stale-not-latency",
            "scalping_scanner_candidate_observed",
            {"current_price": "1100", "ws_last_0b_age_ms": "100"},
            emitted_at="2026-07-10T09:13:20",
        ),
        _event(
            805,
            "000805",
            "wide-spread-observe",
            "latency_block",
            {
                "forced_entry_reason": "rising_missed_one_share_entry",
                "reason": "latency_state_danger",
                "current_price": "4000",
                "best_bid_at_submit": "3995",
                "best_ask_at_submit": "4000",
                "ws_age_ms": "80",
                "latency_danger_detail_reason": "spread_above_caution",
                "latency_spread_block_spread_bps": "130.0",
            },
            emitted_at="2026-07-10T09:14:00",
        ),
        _event(
            805,
            "000805",
            "wide-spread-observe",
            "scalping_scanner_candidate_observed",
            {
                "current_price": "4000",
                "best_bid_at_submit": "4000",
                "best_ask_at_submit": "4005",
                "ws_last_0b_age_ms": "100",
            },
            emitted_at="2026-07-10T09:14:10",
        ),
        _event(
            805,
            "000805",
            "wide-spread-observe",
            "scalping_scanner_candidate_observed",
            {
                "current_price": "4160",
                "best_bid_at_submit": "4160",
                "best_ask_at_submit": "4165",
                "ws_last_0b_age_ms": "100",
            },
            emitted_at="2026-07-10T09:14:20",
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows), encoding="utf-8"
    )

    report = mod.build_report(
        "2026-07-10", pipeline_path=pipeline_path, generated_at="fixed"
    )

    assert report["summary"]["latency_false_negative_review_count"] == 3
    assert report["summary"]["latency_false_negative_true_ofi_count"] == 1
    assert report["summary"]["latency_false_negative_spread_only_count"] == 2
    rows_by_code = {
        item["stock_code"]: item
        for item in report["latency_false_negative_review_rows"]
    }
    assert set(rows_by_code) == {"000801", "000802", "000805"}
    assert (
        rows_by_code["000801"]["review_bucket"] == "true_ofi_false_negative_candidate"
    )
    assert rows_by_code["000801"]["mfe_after_block_pct"] == 4.5
    assert rows_by_code["000801"]["mae_after_block_pct"] == -1.0
    assert (
        rows_by_code["000802"]["review_bucket"]
        == "spread_caution_false_negative_candidate"
    )
    assert rows_by_code["000802"]["mfe_after_block_pct"] == 3.5
    assert rows_by_code["000802"]["mae_after_block_pct"] == -1.0
    assert rows_by_code["000801"]["runtime_effect"] is False
    assert rows_by_code["000801"]["allowed_runtime_apply"] is False
    assert (
        report["metric_contracts"]["rising_missed_latency_false_negative_review"][
            "decision_authority"
        ]
        == "source_only_latency_false_negative_review"
    )
    canary_rows_by_code = {
        item["stock_code"]: item
        for item in report["latency_false_negative_canary_candidate_rows"]
    }
    assert (
        canary_rows_by_code["000801"]["canary_cohort"]
        == "true_ofi_near_zero_false_negative"
    )
    assert canary_rows_by_code["000801"]["canary_grade"] == "ready_for_recheck"
    assert canary_rows_by_code["000801"]["canary_primary_review_score_pct"] == 3.5
    assert (
        canary_rows_by_code["000802"]["canary_cohort"] == "spread_only_false_negative"
    )
    assert canary_rows_by_code["000802"]["canary_grade"] == "ready_for_recheck"
    assert canary_rows_by_code["000805"]["canary_grade"] == "observe_wide_spread"
    assert report["summary"]["latency_false_negative_canary_candidate_count"] == 3
    assert report["summary"]["latency_false_negative_canary_ready_count"] == 2
    assert (
        report["summary"]["latency_false_negative_canary_observe_wide_spread_count"]
        == 1
    )
    assert (
        report["metric_contracts"][
            "rising_missed_latency_false_negative_canary_candidate"
        ]["decision_authority"]
        == "source_only_latency_false_negative_canary_candidate"
    )


def test_latency_and_tick_counterfactuals_reject_mark_only_mfe(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-08-04.jsonl"
    rows = [
        _event(
            901,
            "000901",
            "mark-only-tick",
            "rising_missed_tick_speed_entry_block",
            {
                "forced_entry_reason": "rising_missed_one_share_entry",
                "reason": "tick_speed_guard",
                "mark_price_at_submit": 1000,
            },
            emitted_at="2026-08-04T09:00:00+09:00",
        ),
        _event(
            901,
            "000901",
            "mark-only-tick",
            "scalping_scanner_candidate_observed",
            {"current_price": 1100, "ws_last_0b_age_ms": 50},
            emitted_at="2026-08-04T09:01:00+09:00",
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows), encoding="utf-8"
    )

    report = mod.build_report(
        "2026-08-04", pipeline_path=pipeline_path, generated_at="fixed"
    )

    block = report["submit_safety_blocker_rows"][0]
    assert block["block_price"] is None
    assert block["mfe_after_block_pct"] is None
    assert block["mae_after_block_pct"] is None
    assert block["executable_bbo_state"] == "source_gap_missing_or_invalid"
    assert block["post_block_executable_bbo_event_count"] == 0
    assert block["post_block_executable_bbo_source_gap_count"] == 1
    assert report["summary"]["submit_safety_executable_bbo_required_count"] == 1
    assert report["summary"]["submit_safety_executable_bbo_entry_source_gap_count"] == 1
    assert report["summary"]["submit_safety_executable_bbo_labeled_count"] == 0


def test_submit_safety_preserves_entry_ai_exact_bbo_freshness_provenance():
    block = mod._submit_safety_block_row(
        _event(
            904,
            "000904",
            "entry-ai-exact-bbo",
            "rising_missed_tick_speed_entry_block",
            {
                "forced_entry_reason": "rising_missed_one_share_entry",
                "reason": "tick_speed_guard",
                "entry_ai_price_ws_snapshot_refresh_best_bid": 1000,
                "entry_ai_price_ws_snapshot_refresh_best_ask": 1005,
                "entry_ai_price_ws_snapshot_refresh_age_ms": 25,
            },
            emitted_at="2026-08-14T09:00:00+09:00",
        )
    )

    assert block["block_price"] == 1005
    assert block["block_price_source"] == (
        "entry_ai_price_ws_snapshot_refresh_bbo:executable_ask"
    )
    assert block["executable_bbo_state"] == "pass"
    assert block["quote_age_ms"] == 25
    assert block["quote_age_sec"] == 0.025


def test_submit_safety_preserves_tick_speed_veto_and_relief_provenance():
    block = mod._submit_safety_block_row(
        _event(
            905,
            "000905",
            "relative-accel-only",
            "rising_missed_tick_speed_entry_block",
            {
                "forced_entry_reason": "rising_missed_one_share_entry",
                "reason": "tick_acceleration_ratio_lt_1",
                "best_bid_at_submit": 5390,
                "best_ask_at_submit": 5410,
                "rising_missed_tick_window_span_sec": 15,
                "rising_missed_tick_window_span_sec_raw": 15,
                "rising_missed_tick_window_max_span_sec": 60,
                "rising_missed_tick_window_slow": False,
                "rising_missed_tick_acceleration_ratio": 0.857,
                "rising_missed_tick_acceleration_ratio_raw": 0.857,
                "rising_missed_min_tick_acceleration_ratio": 1.0,
                "rising_missed_tick_accel_slow": True,
                "rising_missed_tick_absolute_recent_5tick_seconds": 6.0,
                "rising_missed_tick_absolute_sample_count": 10,
                "rising_missed_tick_absolute_quote_age_ms": 1.487,
                "rising_missed_tick_absolute_orderbook_state": "insufficient",
                "rising_missed_tick_absolute_tp1_support_count": 2,
                "rising_missed_tick_absolute_large_sell_detected": False,
                "rising_missed_tick_absolute_throughput_relief_enabled": True,
                "rising_missed_tick_absolute_throughput_relief_active_date": (
                    "2026-08-21"
                ),
                "rising_missed_tick_absolute_throughput_relief_applied": False,
                "rising_missed_tick_absolute_throughput_relief_path": "none",
                "rising_missed_tick_absolute_throughput_relief_checks": (
                    "enabled,active_date,only_relative_accel_slow,fresh_quote,"
                    "fresh_tp1_support,no_large_sell"
                ),
            },
            emitted_at="2026-08-21T14:32:45+09:00",
        )
    )

    assert block["tick_speed_block_profile"] == "relative_acceleration_only"
    assert block["tick_speed_decision_input_complete"] is True
    assert block["tick_speed_window_span_sec"] == 15.0
    assert block["tick_speed_acceleration_ratio"] == 0.857
    assert block["tick_speed_absolute_recent_5tick_seconds"] == 6.0
    assert block["tick_speed_absolute_sample_count"] == 10
    assert block["tick_speed_absolute_relief_applied"] is False
    assert block["tick_speed_absolute_relief_path"] == "none"


def test_blocked_zero_qty_reuses_only_exact_recent_one_share_bbo_for_source_only_outcome(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline_events_2026-08-21.jsonl"
    rows = [
        _event(
            905,
            "000905",
            "position-cap-zero",
            "rising_missed_one_share_entry",
            {
                "forced_entry_reason": "rising_missed_one_share_entry",
                "effective_venue": "PREMARKET_KRX_LIKE",
                "market_data_effective_best_bid": 1000,
                "market_data_effective_best_ask": 1005,
            },
            emitted_at="2026-08-21T08:00:00+09:00",
        ),
        _event(
            905,
            "000905",
            "position-cap-zero",
            "blocked_zero_qty",
            {
                "forced_entry_reason": "rising_missed_one_share_entry",
                "effective_venue": "PREMARKET_KRX_LIKE",
                "binding_caps": "max_position_qty_cap",
                "pre_cap_qty": 1,
                "effective_qty": 0,
                "budget_base": 120000,
                "target_budget": 12000,
                "safe_budget": 11400,
            },
            emitted_at="2026-08-21T08:00:00.250000+09:00",
        ),
        _event(
            905,
            "000905",
            "position-cap-zero",
            "scalping_scanner_fast_precheck",
            {
                "effective_venue": "PREMARKET_KRX_LIKE",
                "market_data_effective_best_bid": 1020,
                "market_data_effective_best_ask": 1025,
            },
            emitted_at="2026-08-21T08:00:03+09:00",
        ),
        _event(
            905,
            "000905",
            "position-cap-zero",
            "scalping_scanner_fast_precheck",
            {
                "effective_venue": "PREMARKET_KRX_LIKE",
                "market_data_effective_best_bid": 995,
                "market_data_effective_best_ask": 1000,
            },
            emitted_at="2026-08-21T08:00:06+09:00",
        ),
        _event(
            905,
            "000905",
            "position-cap-zero",
            "scalping_scanner_fast_precheck",
            {
                "effective_venue": "NXT",
                "market_data_effective_best_bid": 1100,
                "market_data_effective_best_ask": 1105,
            },
            emitted_at="2026-08-21T08:00:09+09:00",
        ),
        _event(
            905,
            "000905",
            "position-cap-zero",
            "scalping_scanner_fast_precheck",
            {
                "effective_venue": "PREMARKET_KRX_LIKE",
                "market_data_effective_best_bid": 1200,
                "market_data_effective_best_ask": 1205,
            },
            emitted_at="2026-08-21T09:00:01+09:00",
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows), encoding="utf-8"
    )

    report = mod.build_report(
        "2026-08-21", pipeline_path=pipeline_path, generated_at="fixed"
    )

    block = report["submit_safety_blocker_rows"][0]
    assert block["stage"] == "blocked_zero_qty"
    assert block["blocker_bucket"] == "quantity_max_position_qty_cap"
    assert block["block_price"] == 1005.0
    assert block["block_price_source"] == (
        "predecessor:rising_missed_one_share_entry:market_data_effective_bbo:"
        "executable_ask"
    )
    assert block["executable_bbo_predecessor_stage"] == (
        "rising_missed_one_share_entry"
    )
    assert block["executable_bbo_predecessor_age_ms"] == 250.0
    assert block["one_share_floor_position_cap_conflict"] is True
    assert block["post_block_executable_bbo_event_count"] == 2
    assert block["post_block_executable_bbo_venue_mismatch_count"] == 1
    assert block["post_block_executable_bbo_out_of_window_count"] == 1
    assert block["mfe_after_block_pct"] == 1.4925
    assert block["mae_after_block_pct"] == -0.995
    assert block["post_block_first_hit"] == "net_target_first"
    assert block["post_block_first_hit_elapsed_sec"] == 2.75
    assert report["blocked_zero_qty_counterfactual_rows"] == [block]
    assert report["summary"]["blocked_zero_qty_count"] == 1
    assert (
        report["summary"][
            "blocked_zero_qty_one_share_floor_position_cap_conflict_count"
        ]
        == 1
    )
    assert report["summary"]["blocked_zero_qty_executable_bbo_labeled_count"] == 1


def test_blocked_zero_qty_does_not_reuse_stale_predecessor_bbo(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-08-21.jsonl"
    rows = [
        _event(
            906,
            "000906",
            "stale-position-cap-zero",
            "rising_missed_one_share_entry",
            {
                "forced_entry_reason": "rising_missed_one_share_entry",
                "effective_venue": "PREMARKET_KRX_LIKE",
                "market_data_effective_best_bid": 1000,
                "market_data_effective_best_ask": 1005,
            },
            emitted_at="2026-08-21T08:00:00+09:00",
        ),
        _event(
            906,
            "000906",
            "stale-position-cap-zero",
            "blocked_zero_qty",
            {
                "forced_entry_reason": "rising_missed_one_share_entry",
                "effective_venue": "PREMARKET_KRX_LIKE",
                "binding_caps": "max_position_qty_cap",
                "pre_cap_qty": 1,
                "effective_qty": 0,
            },
            emitted_at="2026-08-21T08:00:01.001000+09:00",
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows), encoding="utf-8"
    )

    report = mod.build_report(
        "2026-08-21", pipeline_path=pipeline_path, generated_at="fixed"
    )

    block = report["submit_safety_blocker_rows"][0]
    assert block["block_price"] is None
    assert block["executable_bbo_state"] == "source_gap_missing_or_invalid"
    assert block["executable_bbo_predecessor_stage"] is None


def test_blocked_zero_qty_normalizes_naive_pipeline_timestamp_to_kst(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline_events_2026-08-21.jsonl"
    rows = [
        _event(
            907,
            "000907",
            "mixed-timebase-zero",
            "rising_missed_one_share_entry",
            {
                "forced_entry_reason": "rising_missed_one_share_entry",
                "effective_venue": "PREMARKET_KRX_LIKE",
                "market_data_effective_best_bid": 1000,
                "market_data_effective_best_ask": 1005,
            },
            emitted_at="2026-08-21T08:00:00",
        ),
        _event(
            907,
            "000907",
            "mixed-timebase-zero",
            "blocked_zero_qty",
            {
                "forced_entry_reason": "rising_missed_one_share_entry",
                "effective_venue": "PREMARKET_KRX_LIKE",
                "binding_caps": "max_position_qty_cap",
                "pre_cap_qty": 1,
                "effective_qty": 0,
            },
            emitted_at="2026-08-21T08:00:00.250000+09:00",
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows), encoding="utf-8"
    )

    report = mod.build_report(
        "2026-08-21", pipeline_path=pipeline_path, generated_at="fixed"
    )

    block = report["blocked_zero_qty_counterfactual_rows"][0]
    assert block["executable_bbo_state"] == "pass"
    assert block["executable_bbo_predecessor_age_ms"] == 250.0


def test_latency_false_negative_preserves_runtime_dynamic_age_provenance():
    block = mod._submit_safety_block_row(
        _event(
            902,
            "000902",
            "dynamic-age-observed",
            "latency_block",
            {
                "forced_entry_reason": "rising_missed_one_share_entry",
                "reason": "latency_state_danger",
                "best_bid_at_submit": 1000,
                "best_ask_at_submit": 1005,
                "ws_age_ms": 320,
                "latency_spread_block_bucket": "latency_true_ofi_below_floor",
                "latency_spread_block_spread_bps": 49.8,
                "latency_spread_relief_micro_estimator_true_ofi_ewma": 0.03,
                "latency_spread_relief_micro_estimator_true_ofi_sample_count": 120,
                "latency_spread_relief_micro_estimator_reason": "true_ofi_below_floor",
                "latency_true_ofi_direct_canary_enabled": True,
                "latency_true_ofi_direct_canary_applied": False,
                "latency_true_ofi_direct_canary_reason": "ws_age_too_high",
                "latency_true_ofi_direct_canary_ws_age_ms": 325,
                "latency_true_ofi_direct_canary_effective_max_ws_age_ms": 500,
                "latency_true_ofi_direct_canary_dynamic_age_band_enabled": True,
                "latency_true_ofi_direct_canary_dynamic_age_band_active": True,
                "latency_true_ofi_direct_canary_dynamic_age_band_eligible": True,
                "latency_true_ofi_direct_canary_dynamic_age_band_applied": False,
                "latency_true_ofi_direct_canary_dynamic_age_band_max_ws_age_ms": 500,
                "latency_true_ofi_direct_canary_dynamic_age_band_min_samples": 100,
                "latency_true_ofi_direct_canary_dynamic_age_band_max_spread_bps": 60,
                "latency_true_ofi_direct_canary_dynamic_age_band_min_true_ofi": 0,
                "latency_true_ofi_direct_canary_dynamic_age_band_min_signed_tape_buy_ratio": 80,
                "latency_true_ofi_direct_canary_dynamic_age_band_min_signed_tape_samples": 3,
                "latency_true_ofi_direct_canary_signed_tape_sample_count": 5,
                "latency_true_ofi_direct_canary_signed_tape_trusted_ws_count": 5,
                "latency_true_ofi_direct_canary_signed_tape_unknown_source_count": 0,
                "latency_true_ofi_direct_canary_signed_tape_buy_ratio": 100,
                "latency_true_ofi_direct_canary_signed_tape_event_time_latest_side": "BUY",
                "latency_true_ofi_direct_canary_signed_tape_sell_dominated": False,
                "latency_true_ofi_direct_canary_large_sell_print_detected": False,
            },
            emitted_at="2026-08-04T09:00:00+09:00",
        )
    )
    block["mfe_after_block_pct"] = 5.0
    block["mae_after_block_pct"] = -1.0

    review_summary, review_rows = mod._build_latency_false_negative_review([block])
    canary_summary, canary_rows = mod._build_latency_false_negative_canary_candidates(
        review_rows
    )

    assert review_summary["latency_false_negative_review_count"] == 1
    assert review_rows[0]["runtime_dynamic_age_band_eligible"] is True
    assert review_rows[0]["runtime_signed_tape_latest_side"] == "BUY"
    assert canary_rows[0]["canary_grade"] == "hold_sample"
    assert (
        canary_rows[0]["canary_reason"] == "ws_age_not_fresh_enough_for_canary_recheck"
    )
    assert (
        canary_rows[0]["runtime_dynamic_age_band_provenance_state"]
        == "observed_active_eligible_not_applied"
    )
    assert canary_rows[0]["allowed_runtime_apply"] is False
    assert (
        canary_summary["latency_false_negative_runtime_dynamic_age_eligible_count"] == 1
    )
    assert (
        canary_summary["latency_false_negative_runtime_dynamic_age_applied_count"] == 0
    )
    assert (
        canary_summary["latency_false_negative_runtime_dynamic_age_source_gap_count"]
        == 0
    )


def test_dynamic_age_post_apply_attribution_uses_executable_ask_and_future_bid(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline_events_2026-08-12.jsonl"
    rows = [
        _event(
            903,
            "000903",
            "dynamic-age-applied",
            "scalp_entry_action_decision_snapshot",
            {
                "source_stage": "latency_pass",
                "effective_venue": "KRX",
                "ai_decision_trace_id": "dynamic-age-trace-1",
                "latency_true_ofi_direct_canary_dynamic_age_band_applied": True,
                "executable_buy_price": 1000,
                "executable_sell_price": 995,
                "actual_order_submitted": False,
            },
            emitted_at="2026-08-12T10:00:00+09:00",
        ),
        _event(
            903,
            "000903",
            "dynamic-age-applied",
            "scalp_entry_action_decision_snapshot",
            {
                "source_stage": "pre_submit_entry_ai_authority_guard_block",
                "effective_venue": "KRX",
                "ai_decision_trace_id": "dynamic-age-trace-1",
                "latency_true_ofi_direct_canary_dynamic_age_band_applied": True,
                "executable_buy_price": 1000,
                "executable_sell_price": 995,
            },
            emitted_at="2026-08-12T10:00:02+09:00",
        ),
        _event(
            903,
            "000903",
            "dynamic-age-applied",
            "holding_observation",
            {"executable_sell_price": 1012, "executable_buy_price": 1014},
            emitted_at="2026-08-12T10:04:00+09:00",
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n",
        encoding="utf-8",
    )

    summary, _blocks, _backoffs, attribution_rows = (
        mod._build_submit_safety_and_backoff_audit(pipeline_path)
    )

    assert summary["dynamic_age_post_apply_episode_count"] == 1
    assert summary["dynamic_age_post_apply_latency_pass_count"] == 1
    assert summary["dynamic_age_post_apply_actual_order_submitted_count"] == 0
    assert summary["dynamic_age_post_apply_source_quality_pass_count"] == 1
    assert summary["dynamic_age_post_apply_first_hit_counts"] == [
        {"first_hit": "net_target_first", "count": 1}
    ]
    assert attribution_rows[0]["downstream_terminal_stage"] == (
        "pre_submit_entry_ai_authority_guard_block"
    )
    assert attribution_rows[0]["horizons"]["5m"] == {
        "event_count": 2,
        "mfe_pct": 1.2,
        "mae_pct": -0.5,
    }
    assert attribution_rows[0]["first_hit"] == "net_target_first"
    assert attribution_rows[0]["actual_order_submitted"] is False


def test_clean_baseline_rolling_nxt_post_block_outcomes(monkeypatch, tmp_path):
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path)
    prior_row = {
        "source_block_stage": "tp1_selector",
        "source_block_reason": "rising_missed_tp1_lane_not_eligible",
        "completed_sample_count": 13,
        "unique_symbol_count": 6,
        "gross_target_first_count": 0,
        "adverse_stop_first_count": 2,
        "no_hit_within_20m_count": 11,
        "equal_weight_avg_mfe_after_block_pct": 0.158771,
        "equal_weight_avg_mae_after_block_pct": -0.480772,
        "max_mfe_after_block_pct": 0.824176,
        "min_mae_after_block_pct": -0.833333,
    }
    valid_prior = {
        "report_type": "rising_missed_intraday_feedback",
        "target_date": "2026-07-31",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "summary": {
            "rising_missed_nxt_post_block_blocker_outcome_attribution": [prior_row]
        },
    }
    (tmp_path / "rising_missed_intraday_feedback_2026-07-31.json").write_text(
        json.dumps(valid_prior), encoding="utf-8"
    )
    (tmp_path / "rising_missed_intraday_feedback_2026-07-30.json").write_text(
        "not-json", encoding="utf-8"
    )
    # A stale target-date artifact must not be double-counted.
    (tmp_path / "rising_missed_intraday_feedback_2026-08-03.json").write_text(
        json.dumps(valid_prior), encoding="utf-8"
    )
    current_rows = [
        {
            **prior_row,
            "completed_sample_count": 4,
            "unique_symbol_count": 4,
            "gross_target_first_count": 1,
            "adverse_stop_first_count": 1,
            "no_hit_within_20m_count": 2,
            "equal_weight_avg_mfe_after_block_pct": 1.129822,
            "equal_weight_avg_mae_after_block_pct": -0.420203,
            "max_mfe_after_block_pct": 3.663986,
            "min_mae_after_block_pct": -1.029601,
        }
    ]

    rows, window = mod._clean_baseline_rolling_nxt_post_block_outcomes(
        "2026-08-03", current_rows
    )

    assert len(rows) == 1
    row = rows[0]
    assert row["completed_sample_count"] == 17
    assert row["gross_target_first_count"] == 1
    assert row["adverse_stop_first_count"] == 3
    assert row["gross_target_first_rate_pct"] == 5.882353
    assert row["adverse_stop_first_rate_pct"] == 17.647059
    assert row["equal_weight_avg_mfe_after_block_pct"] == 0.387254
    assert row["equal_weight_avg_mae_after_block_pct"] == -0.46652
    assert row["gross_first_hit_payoff_proxy_pct"] == -0.047059
    assert row["net_ev_state"] == (
        "unavailable_fee_tax_and_no_hit_exit_outcome_missing"
    )
    assert row["sample_floor_met"] is True
    assert row["rolling_assessment"] == "hold_no_edge"
    assert row["runtime_effect"] is False
    assert row["allowed_runtime_apply"] is False
    assert row["source_dates"] == ["2026-07-31", "2026-08-03"]
    assert window["clean_tuning_baseline_date"] == "2026-06-05"
    assert window["rolling_report_day_limit"] == 20
    assert window["excluded_report_count"] == 1
    assert window["excluded_reports"] == [
        {"target_date": "2026-07-30", "reason": "report_unreadable"}
    ]


def test_clean_baseline_rolling_nxt_post_block_outcomes_isolates_group_weights(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path)
    current_rows = [
        {
            "source_block_stage": "tp1_selector",
            "source_block_reason": "reason_a",
            "completed_sample_count": 2,
            "unique_symbol_count": 2,
            "gross_target_first_count": 1,
            "adverse_stop_first_count": 0,
            "no_hit_within_20m_count": 1,
            "equal_weight_avg_mfe_after_block_pct": 1.0,
            "equal_weight_avg_mae_after_block_pct": -0.1,
        },
        {
            "source_block_stage": "submit_safety",
            "source_block_reason": "reason_b",
            "completed_sample_count": 3,
            "unique_symbol_count": 3,
            "gross_target_first_count": 0,
            "adverse_stop_first_count": 1,
            "no_hit_within_20m_count": 2,
            "equal_weight_avg_mfe_after_block_pct": 4.0,
            "equal_weight_avg_mae_after_block_pct": -2.0,
        },
    ]

    rows, _ = mod._clean_baseline_rolling_nxt_post_block_outcomes(
        "2026-08-03", current_rows
    )

    assert len(rows) == 2
    by_reason = {row["source_block_reason"]: row for row in rows}
    assert by_reason["reason_a"]["equal_weight_avg_mfe_after_block_pct"] == 1.0
    assert by_reason["reason_a"]["equal_weight_avg_mae_after_block_pct"] == -0.1
    assert by_reason["reason_b"]["equal_weight_avg_mfe_after_block_pct"] == 4.0
    assert by_reason["reason_b"]["equal_weight_avg_mae_after_block_pct"] == -2.0


def test_clean_baseline_rolling_latency_candidates_separates_venue_and_gaps(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path)

    def candidate(venue, session, mfe, mae, grade="ready_for_recheck"):
        return {
            "effective_venue": venue,
            "market_session_bucket": session,
            "canary_cohort": "true_ofi_near_zero_false_negative",
            "canary_grade": grade,
            "mfe_after_block_pct": mfe,
            "mae_after_block_pct": mae,
        }

    prior_rows = [candidate("KRX", "krx_regular", 3.5, -0.4) for _ in range(9)]
    prior_rows.extend(
        [
            candidate("NXT", "nxt_entry_window", 4.0, -0.5),
            candidate("UNKNOWN", "krx_regular", 8.0, -0.1),
        ]
    )
    valid_prior = {
        "report_type": "rising_missed_intraday_feedback",
        "target_date": "2026-08-12",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "latency_false_negative_canary_candidate_rows": prior_rows,
    }
    (tmp_path / "rising_missed_intraday_feedback_2026-08-12.json").write_text(
        json.dumps(valid_prior), encoding="utf-8"
    )
    # Pre-baseline evidence must never enter a tuning window.
    (tmp_path / "rising_missed_intraday_feedback_2026-06-01.json").write_text(
        json.dumps(
            {
                **valid_prior,
                "target_date": "2026-06-01",
                "latency_false_negative_canary_candidate_rows": [
                    candidate("KRX", "krx_regular", 99.0, 0.0)
                ],
            }
        ),
        encoding="utf-8",
    )

    rows, window = mod._clean_baseline_rolling_latency_false_negative_candidates(
        "2026-08-13",
        [candidate("KRX", "krx_regular", 4.5, -0.3)],
    )

    assert len(rows) == 2
    krx = next(row for row in rows if row["effective_venue"] == "KRX")
    nxt = next(row for row in rows if row["effective_venue"] == "NXT")
    assert krx["completed_sample_count"] == 10
    assert krx["low_adverse_opportunity_count"] == 10
    assert krx["rolling_assessment"] == (
        "source_only_next_scanner_loop_feature_review_priority"
    )
    assert krx["runtime_effect"] is False
    assert krx["allowed_runtime_apply"] is False
    assert nxt["completed_sample_count"] == 1
    assert nxt["rolling_assessment"] == "hold_sample"
    assert window["clean_tuning_baseline_date"] == "2026-06-05"
    assert window["source_gap_row_count"] == 1
    assert window["source_quality_state"] == "pass_with_row_exclusions"
    assert window["usable_row_count"] == 11
    assert window["total_input_row_count"] == 12
    assert window["inspected_source_dates"] == ["2026-08-12", "2026-08-13"]
    assert window["source_dates"] == ["2026-08-12", "2026-08-13"]
