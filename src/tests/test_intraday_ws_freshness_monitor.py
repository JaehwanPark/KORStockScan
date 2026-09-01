import json
from types import SimpleNamespace

from src.engine.monitoring import intraday_ws_freshness_monitor as mod


def _event(stage, fields, *, code="000001", emitted_at="2026-07-13T09:10:00+09:00"):
    return {
        "pipeline": "ENTRY_PIPELINE",
        "stage": stage,
        "stock_code": code,
        "stock_name": f"NAME{code}",
        "emitted_at": emitted_at,
        "fields": fields,
    }


def _write_jsonl(path, rows):
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )


def _install_verified_symbol_master(monkeypatch):
    class _VerifiedMaster:
        def lookup(self, symbol, *, as_of):
            assert symbol
            assert as_of
            return SimpleNamespace(
                status=SimpleNamespace(value="verified"),
                economic_metadata_allowed=True,
            )

    fixture = (
        _VerifiedMaster(),
        {
            "status": "verified",
            "path": "fixture://symbol-master",
            "artifact_sha256": "a" * 64,
            "symbol_count": 1,
        },
    )
    monkeypatch.setattr(
        mod,
        "_load_verified_symbol_master",
        lambda target_date, symbol_master_path: (
            fixture[0],
            {**fixture[1], "path": f"fixture://symbol-master/{target_date}"},
        ),
    )
    return fixture


def test_build_report_splits_subscription_stale_from_trade_tick_quiet(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-13.jsonl"
    threshold_path = tmp_path / "threshold_events_2026-07-13.jsonl"
    snapshot_path = tmp_path / "ws_snapshot.json"
    _write_jsonl(
        pipeline_path,
        [
            _event(
                "scalping_scanner_fast_precheck",
                {
                    "ws_last_0b_age_ms": "50000",
                    "ws_last_0d_age_ms": "4000",
                    "source_quality_block_reason": "trade_tick_quiet",
                    "last_trade_cum_volume": "1234",
                },
                code="000101",
            ),
            _event(
                "ws_subscription_freshness_snapshot",
                {
                    "freshness_state": "stale",
                    "repair_recommended": "true",
                    "repair_reason": "subscription_stale",
                    "ws_last_0b_age_ms": "61000",
                    "ws_last_0d_age_ms": "61000",
                    "ws_repair_cycle_state": "ws_reg_reissued_waiting_snapshot",
                    "ws_subscription_repair_required": True,
                },
                code="000202",
            ),
        ],
    )
    _write_jsonl(threshold_path, [])
    snapshot_path.write_text(
        json.dumps(
            {
                "rows": [
                    {
                        "stock_code": "000101",
                        "freshness_state": "fresh",
                        "trade_tick_quiet": True,
                        "last_0b_age_sec": 50.0,
                        "last_0d_age_sec": 4.0,
                        "last_trade_cum_volume": 1234,
                        "repair_recommended": False,
                        "repair_reason": "none",
                        "registered_items": ["000101", "000101_AL"],
                        "registered_item_quota_units": 2,
                        "registered_market_suffixes": ["", "_AL"],
                        "registered_market_routes": [
                            "krx_regular",
                            "krx_nxt_integrated",
                        ],
                        "registered_route_counts": {
                            "krx_regular": 1,
                            "krx_nxt_integrated": 1,
                        },
                        "multi_route_registered": True,
                    },
                    {
                        "stock_code": "000202",
                        "freshness_state": "stale",
                        "repair_recommended": True,
                        "repair_reason": "subscription_stale",
                        "last_receive_age_sec": 61.0,
                        "registered_items": ["000202_NX"],
                        "registered_item_quota_units": 1,
                        "registered_market_suffixes": ["_NX"],
                        "registered_market_routes": ["nxt_only"],
                        "registered_route_counts": {"nxt_only": 1},
                        "multi_route_registered": False,
                    },
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    report = mod.build_report(
        "2026-07-13",
        pipeline_path=pipeline_path,
        threshold_path=threshold_path,
        subscription_snapshot_path=snapshot_path,
        generated_at="fixed",
    )

    assert report["metric_contract"]["runtime_effect"] is False
    assert report["input_processing"]["mode"] == "full_streaming_rebuild"
    assert report["input_processing"]["memory_bounded_streaming"] is True
    assert report["input_processing"]["full_event_list_materialized"] is False
    assert report["input_processing"]["aggregated_event_count"] == 2
    assert report["input_processing"]["appended_event_count"] == 2
    assert report["input_processing"]["incremental_state_reason"] == "state_missing"
    assert report["pipeline_counts"]["trade_tick_quiet"] == 1
    assert report["pipeline_counts"]["subscription_stale"] == 1
    assert report["pipeline_counts"]["both_ws_stale"] == 1
    assert report["pipeline_counts"]["fresh_0d_stale_0b"] == 1
    assert report["snapshot_summary"]["trade_tick_quiet_count"] == 1
    assert report["snapshot_summary"][
        "trade_tick_quiet_cumulative_volume_provenance_counts"
    ] == {"cumulative_volume_positive": 1}
    assert report["snapshot_summary"]["repair_recommended_count"] == 1
    assert report["snapshot_summary"]["registered_item_quota_units"] == 3
    assert report["snapshot_summary"]["registered_route_counts"] == {
        "krx_nxt_integrated": 1,
        "krx_regular": 1,
        "nxt_only": 1,
    }
    assert report["snapshot_summary"]["registered_market_suffix_counts"] == {
        "KRX": 1,
        "_AL": 1,
        "_NX": 1,
    }
    assert report["snapshot_summary"]["multi_route_registered_count"] == 1
    assert report["causal_attribution"]["trade_tick_quiet"][
        "cumulative_volume_provenance_counts"
    ] == {"cumulative_volume_positive": 1}
    assert report["causal_attribution"]["both_ws_stale"][
        "repair_cycle_state_counts"
    ] == {"ws_reg_reissued_waiting_snapshot": 1}
    assert (
        report["snapshot_summary"]["route_repair_policy"]
        == "remove_then_reg_required_for_route_transition"
    )
    assert (
        report["snapshot_summary"]["top_multi_route_symbols"][0]["stock_code"]
        == "000101"
    )
    order_ids = {item["order_id"] for item in report["workorder_directives"]}
    assert "order_ws_subscription_stale_repair_observability" in order_ids
    assert "order_ws_trade_tick_quiet_low_liquidity_classification" in order_ids
    assert "order_ws_total_stale_escalation" in order_ids
    assert all(
        item["runtime_effect"] is False for item in report["workorder_directives"]
    )
    assert all(
        item["allowed_runtime_apply"] is False
        for item in report["workorder_directives"]
    )
    decisions = {
        item["order_id"]: item["decision"] for item in report["workorder_directives"]
    }
    assert decisions["order_ws_total_stale_escalation"] == "defer_evidence"
    assert decisions["order_ws_trade_tick_quiet_low_liquidity_classification"] == (
        "defer_evidence"
    )


def test_scanner_unique_funnel_deduplicates_mirrors_and_closes_final_outcome(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline.jsonl"
    threshold_path = tmp_path / "threshold.jsonl"
    promotion_id = "SCANPROM-000101-1000000"
    common = {
        "scanner_promotion_id": promotion_id,
        "scanner_scan_generation_id": "SCANGEN-1000",
        "scanner_scan_rank": 1,
        "scanner_ranked_candidate_count": 2,
        "runtime_record_id": 77,
        "effective_venue": "KRX",
        "market_session_bucket": "krx_regular",
    }
    rows = [
        _event("scalping_scanner_candidate_promoted", common, code="000101"),
        _event(
            "scalping_scanner_runtime_target_attach",
            {
                **common,
                "runtime_target_attach_outcome": "attached",
                "runtime_target_attach_reason": "new_watching_target_attached",
                "scanner_runtime_handoff_epoch": 1000.1,
                "scanner_runtime_handoff_promotion_id": promotion_id,
                "scanner_runtime_instance_id": "scanner-runtime-test",
                "scanner_attach_provenance_version": "scanner_runtime_handoff_v1",
            },
            code="000101",
        ),
        _event(
            "scalping_scanner_fast_precheck",
            {**common, "fast_precheck_result": "eligible_for_heavy_entry_eval"},
            code="000101",
        ),
        _event(
            "scalping_scanner_runtime_queue_lag",
            {**common, "fast_precheck_reason": "scanner_ws_stale_backoff_active"},
            code="000101",
        ),
        _event(
            "scalping_scanner_candidate_pruned",
            {
                "scanner_scan_generation_id": "SCANGEN-1000",
                "scanner_scan_rank": 2,
                "scanner_ranked_candidate_count": 2,
                "scanner_prune_reason": "reentry_cooldown_no_material_upgrade",
                "source_signature": "PRICE_JUMP_START",
                "effective_venue": "KRX",
            },
            code="000202",
        ),
    ]
    _write_jsonl(pipeline_path, rows)
    _write_jsonl(threshold_path, rows)

    report = mod.build_report(
        "2026-07-13",
        pipeline_path=pipeline_path,
        threshold_path=threshold_path,
        generated_at="fixed",
    )

    funnel = report["scanner_unique_funnel"]
    assert funnel["metric_contract"]["primary_decision_metric"] == (
        "eligible_without_heavy_evaluation_count"
    )
    assert funnel["metric_contract"]["primary_decision_metric"] in funnel
    assert funnel["relevant_raw_event_count"] == 10
    assert funnel["duplicate_mirror_event_count"] == 5
    assert funnel["unique_promotion_count"] == 1
    assert funnel["unique_runtime_record_count"] == 1
    assert funnel["unique_symbol_count"] == 1
    assert funnel["unique_pruned_candidate_count"] == 1
    assert funnel["attach_success_count"] == 1
    assert funnel["handoff_provenance_coverage_pct"] == 100.0
    assert funnel["eligible_without_heavy_evaluation_count"] == 1
    assert funnel["final_outcome_counts"] == {"active_queue_lag_right_censored": 1}
    assert funnel["economic_cohorts"]["non_gainer_not_rising_repeat"] == 1
    assert funnel["economic_cohorts"]["executable_bbo_ev_status"] == (
        "source_quality_blocked_official_symbol_master_binding"
    )
    assert (
        funnel["economic_cohorts"]["executable_bbo_attribution"][
            "source_quality_adjusted_ev_pct"
        ]
        is None
    )
    conservation = funnel["scan_generation_conservation"]
    assert conservation["complete_generation_count"] == 1
    assert conservation["incomplete_generation_count"] == 0
    assert conservation["structural_contract_conflict_generation_count"] == 0
    assert conservation["structural_contract_conflict_rows_sample"] == []
    assert funnel["immutable_metadata_conflict_count"] == 0
    assert funnel["immutable_metadata_conflict_rows_sample"] == []
    assert conservation["rows"] == [
        {
            "scan_generation_id": "SCANGEN-1000",
            "ranked_candidate_count": 2,
            "terminal_candidate_count": 2,
            "conservation_delta": 0,
            "outcome_conflict_count": 0,
            "missing_ranked_candidate_count": 0,
            "ranked_count_conflict_count": 0,
            "duplicate_rank_count": 0,
            "missing_rank_count": 0,
            "out_of_range_rank_count": 0,
            "lineage_metadata_conflict_count": 0,
            "metadata_conflict_count": 0,
        }
    ]
    order_ids = {item["order_id"] for item in report["workorder_directives"]}
    assert "order_scanner_eligible_no_heavy_closed_loop" in order_ids
    assert "order_scanner_runtime_handoff_provenance_gap" not in order_ids
    assert "order_scanner_scan_generation_conservation_gap" not in order_ids


def test_scanner_funnel_exact_bbo_join_computes_cost_adjusted_first_hit(
    tmp_path, monkeypatch
):
    _install_verified_symbol_master(monkeypatch)
    pipeline_path = tmp_path / "pipeline.jsonl"
    threshold_path = tmp_path / "threshold.jsonl"
    promotion_id = "SCANPROM-BBO-ECONOMICS"
    common = {
        "scanner_promotion_id": promotion_id,
        "scanner_scan_generation_id": "SCANGEN-BBO-ECONOMICS",
        "scanner_scan_rank": 1,
        "scanner_ranked_candidate_count": 1,
        "effective_venue": "KRX",
        "market_session_bucket": "KRX_REGULAR",
    }
    _write_jsonl(
        pipeline_path,
        [
            _event(
                "scalping_scanner_candidate_promoted",
                {
                    **common,
                    "market_data_effective_best_bid": 100,
                    "market_data_effective_best_ask": 101,
                    "market_data_effective_quote_age_ms": 10,
                    "market_data_effective_price_source": "ws_executable_bbo",
                },
                code="000707",
                emitted_at="2026-08-31T09:10:00+09:00",
            ),
            _event(
                "scalping_scanner_fast_precheck",
                {
                    **common,
                    "fast_precheck_result": "eligible_for_heavy_entry_eval",
                    "market_data_effective_best_bid": 103,
                    "market_data_effective_best_ask": 104,
                    "market_data_effective_quote_age_ms": 15,
                    "market_data_effective_price_source": "ws_executable_bbo",
                },
                code="000707",
                emitted_at="2026-08-31T09:10:02+09:00",
            ),
        ],
    )
    _write_jsonl(threshold_path, [])

    report = mod.build_report(
        "2026-08-31",
        pipeline_path=pipeline_path,
        threshold_path=threshold_path,
        generated_at="fixed",
    )

    attribution = report["scanner_unique_funnel"]["economic_cohorts"][
        "executable_bbo_attribution"
    ]
    assert attribution["status"] == "source_only_economics_available"
    assert attribution["economic_candidate_count"] == 1
    assert attribution["exact_bbo_joined_count"] == 1
    assert attribution["exact_promotion_venue_session_bbo_join_coverage_pct"] == 100.0
    assert attribution["resolved_outcome_count"] == 1
    assert attribution["first_hit_counts"] == {"sampled_gross_target_first": 1}
    assert attribution["round_trip_cost_pct"] == 0.23
    assert attribution["source_quality_adjusted_ev_pct"] == 1.75019802
    assert attribution["aggregate_ev_status"] == "available_single_venue_session"
    assert (
        attribution["comparison_cost_contract"]["metric_contract"]["decision_authority"]
        == "widget_postclose_comparison_cost_only"
    )
    assert (
        attribution["comparison_cost_consumer_binding"]["decision_authority"]
        == "scanner_funnel_executable_bbo_source_only"
    )
    assert attribution["first_hit_observation_contract"] == (
        "sampled_scanner_stage_bbo_event_order_not_continuous_market_path"
    )
    assert attribution["rows"][0]["entry_best_ask"] == 101.0
    assert attribution["rows"][0]["exit_best_bid"] == 103.0
    assert not any(
        item["order_id"] == "order_scanner_funnel_executable_bbo_join"
        for item in report["workorder_directives"]
    )


def test_scanner_funnel_missing_quote_age_stays_blocked_not_zero_ev(
    tmp_path, monkeypatch
):
    _install_verified_symbol_master(monkeypatch)
    pipeline_path = tmp_path / "pipeline.jsonl"
    threshold_path = tmp_path / "threshold.jsonl"
    common = {
        "scanner_promotion_id": "SCANPROM-BBO-GAP",
        "scanner_scan_generation_id": "SCANGEN-BBO-GAP",
        "scanner_scan_rank": 1,
        "scanner_ranked_candidate_count": 1,
        "effective_venue": "NXT",
        "market_session_bucket": "NXT_REGULAR",
    }
    _write_jsonl(
        pipeline_path,
        [
            _event(
                "scalping_scanner_candidate_promoted",
                {
                    **common,
                    "market_data_effective_best_bid": 100,
                    "market_data_effective_best_ask": 101,
                },
                code="000708",
            ),
            _event(
                "scalping_scanner_fast_precheck",
                {**common, "fast_precheck_result": "eligible_for_heavy_entry_eval"},
                code="000708",
                emitted_at="2026-07-13T09:10:01+09:00",
            ),
        ],
    )
    _write_jsonl(threshold_path, [])

    report = mod.build_report(
        "2026-07-13",
        pipeline_path=pipeline_path,
        threshold_path=threshold_path,
        generated_at="fixed",
    )

    attribution = report["scanner_unique_funnel"]["economic_cohorts"][
        "executable_bbo_attribution"
    ]
    assert attribution["exact_bbo_joined_count"] == 0
    assert attribution["source_capture_design_required"] is False
    assert attribution["source_capture_repair_required"] is True
    assert attribution["cohort_source_quality"] == [
        {
            "cohort": "eligible_no_heavy",
            "venue": "NXT",
            "market_session_bucket": "NXT_REGULAR",
            "source_census_count": 1,
            "eligible_verified_common_stock_candidate_count": 1,
            "official_symbol_master_excluded_count": 0,
            "exact_bbo_joined_count": 0,
            "exact_bbo_join_coverage_pct": 0.0,
            "resolved_outcome_count": 0,
            "source_capture_gap_count": 1,
            "source_capture_gap": True,
            "first_depleted_stage": (
                "scanner_lifecycle_event_executable_bbo_provenance"
            ),
            "missing_reason_counts": {"fresh_executable_bbo_missing": 1},
        }
    ]
    assert attribution["source_quality_adjusted_ev_pct"] is None
    assert attribution["rows"][0]["gross_return_pct"] is None
    order = next(
        item
        for item in report["workorder_directives"]
        if item["order_id"] == "order_scanner_funnel_executable_bbo_join"
    )
    assert order["decision"] == "defer_evidence"
    assert order["implementation_state"] == (
        "executable_bbo_join_implemented_waiting_source_quality"
    )
    assert order["decision_authority"] == ("scanner_funnel_executable_bbo_source_only")
    assert "EV" not in order["forbidden_uses"]
    assert "live_auto_promotion" in order["forbidden_uses"]


def test_scanner_funnel_does_not_borrow_lineage_venue_for_bbo_observation(
    tmp_path, monkeypatch
):
    _install_verified_symbol_master(monkeypatch)
    pipeline_path = tmp_path / "pipeline.jsonl"
    threshold_path = tmp_path / "threshold.jsonl"
    common = {
        "scanner_promotion_id": "SCANPROM-BBO-MISSING-VENUE",
        "scanner_scan_generation_id": "SCANGEN-BBO-MISSING-VENUE",
        "scanner_scan_rank": 1,
        "scanner_ranked_candidate_count": 1,
    }
    _write_jsonl(
        pipeline_path,
        [
            _event(
                "scalping_scanner_candidate_promoted",
                {
                    **common,
                    "effective_venue": "KRX",
                    "market_session_bucket": "KRX_REGULAR",
                },
                code="000711",
                emitted_at="2026-08-31T09:10:00+09:00",
            ),
            _event(
                "scalping_scanner_fast_precheck",
                {
                    **common,
                    "fast_precheck_result": "eligible_for_heavy_entry_eval",
                    "market_data_effective_best_bid": 100,
                    "market_data_effective_best_ask": 101,
                    "market_data_effective_quote_age_ms": 10,
                    "market_data_effective_price_source": "ws_executable_bbo",
                },
                code="000711",
                emitted_at="2026-08-31T09:10:02+09:00",
            ),
        ],
    )
    _write_jsonl(threshold_path, [])

    report = mod.build_report(
        "2026-08-31",
        pipeline_path=pipeline_path,
        threshold_path=threshold_path,
        generated_at="fixed",
    )

    attribution = report["scanner_unique_funnel"]["economic_cohorts"][
        "executable_bbo_attribution"
    ]
    assert attribution["exact_bbo_joined_count"] == 0
    assert attribution["source_quality_adjusted_ev_pct"] is None
    assert (
        attribution["missing_reason_counts"][
            "market_data_effective_bbo:authoritative_venue_missing"
        ]
        == 1
    )


def test_scanner_funnel_keeps_venue_session_ev_separate(monkeypatch):
    symbol_master, symbol_master_binding = _install_verified_symbol_master(monkeypatch)

    def _lineage(promotion_id, code, venue, session, exit_bid):
        return {
            "promotion_id": promotion_id,
            "code": code,
            "venue": venue,
            "market_session_bucket": session,
            "eligible_for_heavy_entry_eval": True,
            "stages": {"scalping_scanner_fast_precheck": 1},
            "metadata_conflicts": [],
            "bbo_observations": [
                {
                    "observed_at": "2026-08-31T09:10:00+09:00",
                    "observed_epoch": 1788135000.0,
                    "best_bid": 100.0,
                    "best_ask": 101.0,
                    "quote_age_ms": 10.0,
                    "source": "market_data_effective_bbo",
                    "source_provenance": "ws_executable_bbo",
                    "venue": venue,
                    "market_session_bucket": session,
                },
                {
                    "observed_at": "2026-08-31T09:10:02+09:00",
                    "observed_epoch": 1788135002.0,
                    "best_bid": exit_bid,
                    "best_ask": exit_bid + 1,
                    "quote_age_ms": 10.0,
                    "source": "market_data_effective_bbo",
                    "source_provenance": "ws_executable_bbo",
                    "venue": venue,
                    "market_session_bucket": session,
                },
            ],
        }

    attribution = mod._scanner_bbo_economic_attribution(
        [
            _lineage("SCANPROM-KRX", "000712", "KRX", "KRX_REGULAR", 103.0),
            _lineage("SCANPROM-NXT", "000713", "NXT", "NXT_REGULAR", 99.0),
        ],
        [],
        target_date="2026-08-31",
        symbol_master=symbol_master,
        symbol_master_binding=symbol_master_binding,
    )

    assert attribution["status"] == "source_only_economics_available"
    assert attribution["source_quality_adjusted_ev_pct"] is None
    assert attribution["aggregate_ev_status"] == (
        "not_computed_cross_venue_session_forbidden"
    )
    assert len(attribution["venue_session_economics"]) == 2
    assert all(
        row["source_quality_adjusted_ev_pct"] is not None
        for row in attribution["venue_session_economics"]
    )


def test_scanner_funnel_excludes_unverified_symbol_without_blocking_verified_ev(
    monkeypatch,
):
    class _PartiallyVerifiedMaster:
        def lookup(self, symbol, *, as_of):
            assert as_of
            verified = symbol == "000710"
            return SimpleNamespace(
                status=SimpleNamespace(value="verified" if verified else "missing"),
                economic_metadata_allowed=verified,
            )

    def _lineage(promotion_id, code):
        return {
            "promotion_id": promotion_id,
            "code": code,
            "venue": "KRX",
            "market_session_bucket": "KRX_REGULAR",
            "eligible_for_heavy_entry_eval": True,
            "stages": {"scalping_scanner_fast_precheck": 1},
            "metadata_conflicts": [],
            "bbo_observations": [
                {
                    "observed_at": "2026-08-31T09:10:00+09:00",
                    "observed_epoch": 1788135000.0,
                    "best_bid": 100.0,
                    "best_ask": 101.0,
                    "quote_age_ms": 10.0,
                    "source": "market_data_effective_bbo",
                    "source_provenance": "ws_executable_bbo",
                    "venue": "KRX",
                    "market_session_bucket": "KRX_REGULAR",
                },
                {
                    "observed_at": "2026-08-31T09:10:02+09:00",
                    "observed_epoch": 1788135002.0,
                    "best_bid": 103.0,
                    "best_ask": 104.0,
                    "quote_age_ms": 10.0,
                    "source": "market_data_effective_bbo",
                    "source_provenance": "ws_executable_bbo",
                    "venue": "KRX",
                    "market_session_bucket": "KRX_REGULAR",
                },
            ],
        }

    attribution = mod._scanner_bbo_economic_attribution(
        [
            _lineage("SCANPROM-VERIFIED", "000710"),
            _lineage("SCANPROM-EXCLUDED", "900710"),
        ],
        [],
        target_date="2026-08-31",
        symbol_master=_PartiallyVerifiedMaster(),
        symbol_master_binding={
            "status": "verified",
            "path": "fixture://symbol-master",
            "artifact_sha256": "a" * 64,
            "symbol_count": 1,
        },
    )

    assert attribution["status"] == "source_only_economics_available"
    assert attribution["economic_candidate_count"] == 2
    assert attribution["eligible_verified_common_stock_candidate_count"] == 1
    assert attribution["official_symbol_master_excluded_count"] == 1
    assert attribution["exact_bbo_joined_count"] == 1
    assert attribution["exact_promotion_venue_session_bbo_join_coverage_pct"] == 100.0
    assert attribution["resolved_outcome_count"] == 1
    assert attribution["source_quality_adjusted_ev_pct"] == 1.75019802
    assert attribution["source_capture_design_required"] is False
    excluded = next(row for row in attribution["rows"] if row["stock_code"] == "900710")
    assert excluded["bbo_join_status"] == "excluded_official_symbol_master"
    assert excluded["primary_exclusion_reason"] == "official_symbol_master_missing"


def test_scanner_bbo_prebaseline_cost_contract_is_blocked_not_exception(monkeypatch):
    symbol_master, symbol_master_binding = _install_verified_symbol_master(monkeypatch)
    lineage = {
        "promotion_id": "SCANPROM-PREBASELINE",
        "code": "000709",
        "venue": "KRX",
        "market_session_bucket": "KRX_REGULAR",
        "eligible_for_heavy_entry_eval": True,
        "stages": {"scalping_scanner_fast_precheck": 1},
        "metadata_conflicts": [],
        "bbo_observations": [
            {
                "observed_at": "2026-06-04T09:10:00+09:00",
                "observed_epoch": 1780531800.0,
                "best_bid": 100.0,
                "best_ask": 101.0,
                "quote_age_ms": 10.0,
                "source": "market_data_effective_bbo",
                "source_provenance": "ws_executable_bbo",
                "venue": "KRX",
                "market_session_bucket": "KRX_REGULAR",
            },
            {
                "observed_at": "2026-06-04T09:10:02+09:00",
                "observed_epoch": 1780531802.0,
                "best_bid": 103.0,
                "best_ask": 104.0,
                "quote_age_ms": 10.0,
                "source": "market_data_effective_bbo",
                "source_provenance": "ws_executable_bbo",
                "venue": "KRX",
                "market_session_bucket": "KRX_REGULAR",
            },
        ],
    }

    attribution = mod._scanner_bbo_economic_attribution(
        [lineage],
        [],
        target_date="2026-06-04",
        symbol_master=symbol_master,
        symbol_master_binding=symbol_master_binding,
    )

    assert attribution["status"] == ("source_quality_blocked_comparison_cost_contract")
    assert attribution["comparison_cost_contract_status"] == "blocked"
    assert attribution["source_quality_adjusted_ev_pct"] is None


def test_scanner_generation_flags_multiple_first_blockers_for_same_candidate(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline.jsonl"
    threshold_path = tmp_path / "threshold.jsonl"
    common = {
        "scanner_scan_generation_id": "SCANGEN-CONFLICT",
        "scanner_scan_rank": 1,
        "scanner_ranked_candidate_count": 1,
        "effective_venue": "KRX",
    }
    _write_jsonl(
        pipeline_path,
        [
            _event(
                "scalping_scanner_candidate_pruned",
                {**common, "scanner_prune_reason": "general_slot_limit"},
                code="000303",
            ),
            _event(
                "scalping_scanner_candidate_pruned",
                {**common, "scanner_prune_reason": "owner_quota"},
                code="000303",
            ),
        ],
    )
    _write_jsonl(threshold_path, [])

    report = mod.build_report(
        "2026-07-13",
        pipeline_path=pipeline_path,
        threshold_path=threshold_path,
        generated_at="fixed",
    )

    conservation = report["scanner_unique_funnel"]["scan_generation_conservation"]
    assert conservation["complete_generation_count"] == 0
    assert conservation["incomplete_generation_count"] == 1
    assert conservation["structural_contract_conflict_generation_count"] == 1
    assert conservation["structural_contract_conflict_rows_sample"] == [
        conservation["rows"][0]
    ]
    assert conservation["rows"][0]["conservation_delta"] == 0
    assert conservation["rows"][0]["outcome_conflict_count"] == 1
    orders = {item["order_id"]: item for item in report["workorder_directives"]}
    order = orders["order_scanner_scan_generation_conservation_gap"]
    assert order["decision"] == "implement_now"
    assert order["runtime_effect"] is False
    assert order["allowed_runtime_apply"] is False


def test_scanner_generation_nonstructural_gap_waits_for_natural_receipt_sample(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline.jsonl"
    threshold_path = tmp_path / "threshold.jsonl"
    _write_jsonl(
        pipeline_path,
        [
            _event(
                "scalping_scanner_candidate_pruned",
                {
                    "scanner_scan_generation_id": "SCANGEN-NATURAL-WAIT",
                    "scanner_scan_rank": 1,
                    "scanner_ranked_candidate_count": 2,
                    "scanner_prune_reason": "general_slot_limit",
                    "effective_venue": "KRX",
                    "market_session_bucket": "KRX_REGULAR",
                },
                code="000304",
            )
        ],
    )
    _write_jsonl(threshold_path, [])

    report = mod.build_report(
        "2026-07-13",
        pipeline_path=pipeline_path,
        threshold_path=threshold_path,
        generated_at="fixed",
    )

    conservation = report["scanner_unique_funnel"]["scan_generation_conservation"]
    assert conservation["incomplete_generation_count"] == 1
    assert conservation["structural_contract_conflict_generation_count"] == 0
    order = next(
        item
        for item in report["workorder_directives"]
        if item["order_id"] == "order_scanner_scan_generation_conservation_gap"
    )
    assert order["decision"] == "defer_evidence"
    assert order["implementation_state"] == (
        "scanner_candidate_prune_receipts_implemented_waiting_natural_generation"
    )


def test_scanner_generation_ignores_downstream_not_applicable_rank_metadata(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline.jsonl"
    threshold_path = tmp_path / "threshold.jsonl"
    promotion_id = "SCANPROM-000404-1000000"
    _write_jsonl(
        pipeline_path,
        [
            _event(
                "scalping_scanner_candidate_promoted",
                {
                    "scanner_promotion_id": promotion_id,
                    "scanner_scan_generation_id": "SCANGEN-SENTINEL",
                    "scanner_scan_rank": 1,
                    "scanner_ranked_candidate_count": 1,
                    "effective_venue": "KRX",
                },
                code="000404",
            ),
            _event(
                "scalping_scanner_fast_precheck",
                {
                    "scanner_promotion_id": promotion_id,
                    "scanner_scan_generation_id": (
                        "not_applicable_scanner_scan_generation_id"
                    ),
                    "scanner_scan_rank": "not_applicable_scanner_scan_rank",
                    "scanner_ranked_candidate_count": (
                        "not_applicable_scanner_ranked_candidate_count"
                    ),
                    "fast_precheck_result": "eligible_for_heavy_entry_eval",
                    "effective_venue": "KRX",
                },
                code="000404",
            ),
        ],
    )
    _write_jsonl(threshold_path, [])

    report = mod.build_report(
        "2026-07-13",
        pipeline_path=pipeline_path,
        threshold_path=threshold_path,
        generated_at="fixed",
    )

    conservation = report["scanner_unique_funnel"]["scan_generation_conservation"]
    assert conservation["complete_generation_count"] == 1
    assert conservation["incomplete_generation_count"] == 0
    assert conservation["rows"][0]["scan_generation_id"] == "SCANGEN-SENTINEL"
    assert conservation["rows"][0]["ranked_candidate_count"] == 1
    assert conservation["rows"][0]["missing_rank_count"] == 0
    assert conservation["rows"][0]["lineage_metadata_conflict_count"] == 0
    assert conservation["rows"][0]["metadata_conflict_count"] == 0


def test_scanner_generation_preserves_promotion_metadata_and_flags_conflict(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline.jsonl"
    threshold_path = tmp_path / "threshold.jsonl"
    promotion_id = "SCANPROM-000505-1000000"
    _write_jsonl(
        pipeline_path,
        [
            _event(
                "scalping_scanner_candidate_promoted",
                {
                    "scanner_promotion_id": promotion_id,
                    "scanner_scan_generation_id": "SCANGEN-CONFLICTING-METADATA",
                    "scanner_scan_rank": 1,
                    "scanner_ranked_candidate_count": 1,
                    "effective_venue": "KRX",
                },
                code="000505",
            ),
            _event(
                "scalping_scanner_fast_precheck",
                {
                    "scanner_promotion_id": promotion_id,
                    "scanner_scan_generation_id": "SCANGEN-CONFLICTING-METADATA",
                    "scanner_scan_rank": 2,
                    "scanner_ranked_candidate_count": 2,
                    "fast_precheck_result": "eligible_for_heavy_entry_eval",
                    "effective_venue": "KRX",
                },
                code="000505",
            ),
        ],
    )
    _write_jsonl(threshold_path, [])

    report = mod.build_report(
        "2026-07-13",
        pipeline_path=pipeline_path,
        threshold_path=threshold_path,
        generated_at="fixed",
    )

    conservation = report["scanner_unique_funnel"]["scan_generation_conservation"]
    row = conservation["rows"][0]
    assert row["ranked_candidate_count"] == 1
    assert row["terminal_candidate_count"] == 1
    assert row["lineage_metadata_conflict_count"] == 2
    assert row["metadata_conflict_count"] == 2
    assert conservation["complete_generation_count"] == 0
    assert conservation["incomplete_generation_count"] == 1
    orders = {item["order_id"]: item for item in report["workorder_directives"]}
    order = orders["order_scanner_scan_generation_conservation_gap"]
    assert order["decision"] == "implement_now"
    assert order["runtime_effect"] is False
    assert order["allowed_runtime_apply"] is False


def test_scanner_generation_preserves_promotion_owner_and_venue_metadata(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline.jsonl"
    threshold_path = tmp_path / "threshold.jsonl"
    promotion_id = "SCANPROM-000515-1000000"
    _write_jsonl(
        pipeline_path,
        [
            _event(
                "scalping_scanner_candidate_promoted",
                {
                    "scanner_promotion_id": promotion_id,
                    "scanner_scan_generation_id": "SCANGEN-OWNER-VENUE",
                    "scanner_scan_rank": 1,
                    "scanner_ranked_candidate_count": 1,
                    "effective_venue": "KRX",
                    "market_session_bucket": "KRX_REGULAR",
                },
                code="000515",
            ),
            _event(
                "scalping_scanner_fast_precheck",
                {
                    "scanner_promotion_id": promotion_id,
                    "scanner_scan_generation_id": "SCANGEN-OWNER-VENUE",
                    "scanner_scan_rank": 1,
                    "scanner_ranked_candidate_count": 1,
                    "fast_precheck_result": "eligible_for_heavy_entry_eval",
                    "effective_venue": "NXT",
                    "market_session_bucket": "NXT_REGULAR",
                },
                code="000516",
            ),
        ],
    )
    _write_jsonl(threshold_path, [])

    report = mod.build_report(
        "2026-07-13",
        pipeline_path=pipeline_path,
        threshold_path=threshold_path,
        generated_at="fixed",
    )

    funnel = report["scanner_unique_funnel"]
    row = funnel["scan_generation_conservation"]["rows"][0]
    assert funnel["unique_symbol_count"] == 1
    assert funnel["venue_counts"] == {"KRX": 1}
    assert row["terminal_candidate_count"] == 1
    assert row["lineage_metadata_conflict_count"] == 3
    assert row["metadata_conflict_count"] == 3
    order = next(
        item
        for item in report["workorder_directives"]
        if item["order_id"] == "order_scanner_scan_generation_conservation_gap"
    )
    assert order["decision"] == "implement_now"
    assert order["runtime_effect"] is False


def test_scanner_immutable_metadata_conflict_without_generation_is_not_hidden(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline.jsonl"
    threshold_path = tmp_path / "threshold.jsonl"
    promotion_id = "SCANPROM-000525-1000000"
    _write_jsonl(
        pipeline_path,
        [
            _event(
                "scalping_scanner_candidate_promoted",
                {
                    "scanner_promotion_id": promotion_id,
                    "effective_venue": "KRX",
                    "market_session_bucket": "KRX_REGULAR",
                },
                code="000525",
            ),
            _event(
                "scalping_scanner_fast_precheck",
                {
                    "scanner_promotion_id": promotion_id,
                    "fast_precheck_result": "eligible_for_heavy_entry_eval",
                    "effective_venue": "NXT",
                    "market_session_bucket": "NXT_REGULAR",
                },
                code="000526",
            ),
        ],
    )
    _write_jsonl(threshold_path, [])

    report = mod.build_report(
        "2026-07-13",
        pipeline_path=pipeline_path,
        threshold_path=threshold_path,
        generated_at="fixed",
    )

    funnel = report["scanner_unique_funnel"]
    conservation = funnel["scan_generation_conservation"]
    assert conservation["generation_count"] == 0
    assert conservation["incomplete_generation_count"] == 0
    assert funnel["immutable_metadata_conflict_count"] == 3
    assert funnel["immutable_metadata_conflict_rows_sample"] == [
        {
            "lineage_type": "promotion",
            "promotion_id": promotion_id,
            "scan_generation_id": "",
            "code": "000525",
            "metadata_conflicts": [
                "code:000525!=000526",
                "venue:KRX!=NXT",
                "market_session_bucket:KRX_REGULAR!=NXT_REGULAR",
            ],
        }
    ]
    order = next(
        item
        for item in report["workorder_directives"]
        if item["order_id"] == "order_scanner_scan_generation_conservation_gap"
    )
    assert order["decision"] == "implement_now"
    assert order["runtime_effect"] is False
    assert any(
        evidence == "immutable_metadata_conflict_count=3"
        for evidence in order["evidence"]
    )
    assert "immutable_metadata_conflict_count=0" in order["acceptance_tests"]


def test_scanner_funnel_fingerprint_does_not_hide_mirror_metadata_conflict():
    base = _event(
        "scalping_scanner_candidate_promoted",
        {
            "scanner_promotion_id": "SCANPROM-000606-1000000",
            "scanner_scan_generation_id": "SCANGEN-MIRROR-CONFLICT",
            "scanner_scan_rank": 1,
            "scanner_ranked_candidate_count": 1,
        },
        code="000606",
    )
    conflict = json.loads(json.dumps(base))
    conflict["fields"]["scanner_scan_rank"] = 2

    assert mod._scanner_funnel_event_fingerprint(
        mod._flatten_event(base)
    ) != mod._scanner_funnel_event_fingerprint(mod._flatten_event(conflict))


def test_scanner_structural_conflict_census_is_not_limited_by_report_sample(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline.jsonl"
    threshold_path = tmp_path / "threshold.jsonl"
    rows = []
    for index in range(50):
        rows.append(
            _event(
                "scalping_scanner_candidate_pruned",
                {
                    "scanner_scan_generation_id": f"SCANGEN-INCOMPLETE-{index:02d}",
                    "scanner_scan_rank": 1,
                    "scanner_ranked_candidate_count": 2,
                    "scanner_prune_reason": "max_new_codes_reached",
                },
                code=f"{index + 1:06d}",
            )
        )
    for code in ("100001", "100002"):
        rows.append(
            _event(
                "scalping_scanner_candidate_pruned",
                {
                    "scanner_scan_generation_id": "SCANGEN-STRUCTURAL-ZZZ",
                    "scanner_scan_rank": 1,
                    "scanner_ranked_candidate_count": 1,
                    "scanner_prune_reason": "max_new_codes_reached",
                },
                code=code,
            )
        )
    _write_jsonl(pipeline_path, rows)
    _write_jsonl(threshold_path, [])

    report = mod.build_report(
        "2026-07-13",
        pipeline_path=pipeline_path,
        threshold_path=threshold_path,
        generated_at="fixed",
    )

    conservation = report["scanner_unique_funnel"]["scan_generation_conservation"]
    assert conservation["generation_count"] == 51
    assert conservation["incomplete_generation_count"] == 51
    assert len(conservation["rows"]) == 50
    assert len(conservation["incomplete_rows_sample"]) == 50
    assert conservation["structural_contract_conflict_generation_count"] == 1
    assert (
        conservation["structural_contract_conflict_rows_sample"][0][
            "scan_generation_id"
        ]
        == "SCANGEN-STRUCTURAL-ZZZ"
    )
    order = next(
        item
        for item in report["workorder_directives"]
        if item["order_id"] == "order_scanner_scan_generation_conservation_gap"
    )
    assert order["decision"] == "implement_now"
    assert any(
        evidence == "structural_contract_conflict_generation_count=1"
        for evidence in order["evidence"]
    )


def test_scanner_manual_exclusion_attach_skip_is_terminal_not_right_censored(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline.jsonl"
    threshold_path = tmp_path / "threshold.jsonl"
    promotion_id = "SCANPROM-MANUAL-SKIP"
    _write_jsonl(
        pipeline_path,
        [
            _event(
                "scalping_scanner_runtime_target_attach",
                {
                    "scanner_promotion_id": promotion_id,
                    "runtime_target_attach_outcome": "skipped",
                    "runtime_target_attach_reason": (
                        "operator_manual_control_excluded_symbol"
                    ),
                    "manual_control_exclusion_terminalized": True,
                    "effective_venue": "KRX",
                },
                code="000404",
            )
        ],
    )
    _write_jsonl(threshold_path, [])

    report = mod.build_report(
        "2026-07-13",
        pipeline_path=pipeline_path,
        threshold_path=threshold_path,
        generated_at="fixed",
    )

    funnel = report["scanner_unique_funnel"]
    assert funnel["final_outcome_counts"] == {
        "manual_control_exclusion_attach_skipped": 1
    }
    assert funnel["manual_control_exclusion_attach_skip_count"] == 1
    assert funnel["manual_control_exclusion_terminalized_count"] == 1


def test_scanner_queue_lag_is_not_terminal_when_heavy_ai_later_recovers(tmp_path):
    pipeline_path = tmp_path / "pipeline.jsonl"
    threshold_path = tmp_path / "threshold.jsonl"
    common = {
        "scanner_promotion_id": "SCANPROM-RECOVERED",
        "runtime_record_id": 88,
        "effective_venue": "KRX",
    }
    _write_jsonl(
        pipeline_path,
        [
            _event(
                "scalping_scanner_fast_precheck",
                {**common, "fast_precheck_result": "eligible_for_heavy_entry_eval"},
                code="000505",
            ),
            _event(
                "scalping_scanner_runtime_queue_lag",
                {**common, "fast_precheck_reason": "scanner_ws_stale_backoff_active"},
                code="000505",
            ),
            _event(
                "scalping_scanner_heavy_eval_completion",
                common,
                code="000505",
            ),
            _event("ai_confirmed", common, code="000505"),
        ],
    )
    _write_jsonl(threshold_path, [])

    report = mod.build_report(
        "2026-07-13",
        pipeline_path=pipeline_path,
        threshold_path=threshold_path,
        generated_at="fixed",
    )

    funnel = report["scanner_unique_funnel"]
    assert funnel["final_outcome_counts"] == {"recovered_ai": 1}
    assert funnel["eligible_without_heavy_evaluation_count"] == 0


def test_scanner_submit_remains_terminal_after_watch_eviction(tmp_path):
    pipeline_path = tmp_path / "pipeline.jsonl"
    threshold_path = tmp_path / "threshold.jsonl"
    common = {
        "scanner_promotion_id": "SCANPROM-SUBMITTED",
        "runtime_record_id": 89,
        "effective_venue": "KRX",
    }
    _write_jsonl(
        pipeline_path,
        [
            _event("scalping_scanner_candidate_promoted", common, code="000506"),
            _event("order_bundle_submitted", common, code="000506"),
            _event(
                "scalping_scanner_runtime_target_attach",
                {
                    **common,
                    "runtime_target_attach_outcome": "skipped",
                    "runtime_target_attach_reason": (
                        "operator_manual_control_excluded_symbol"
                    ),
                },
                code="000506",
            ),
            _event(
                "scalping_scanner_watch_eviction",
                {**common, "eviction_reason": "normal_watch_cleanup"},
                code="000506",
            ),
        ],
    )
    _write_jsonl(threshold_path, [])

    report = mod.build_report(
        "2026-07-13",
        pipeline_path=pipeline_path,
        threshold_path=threshold_path,
        generated_at="fixed",
    )

    assert report["scanner_unique_funnel"]["final_outcome_counts"] == {"submitted": 1}


def test_scanner_order_bundle_failure_is_not_labeled_broker_submit_failure(tmp_path):
    pipeline_path = tmp_path / "pipeline.jsonl"
    threshold_path = tmp_path / "threshold.jsonl"
    common = {
        "scanner_promotion_id": "SCANPROM-PRE-BROKER-BLOCK",
        "runtime_record_id": 90,
        "effective_venue": "KRX",
        "order_bundle_failure_mode": "pre_broker_blocked",
        "broker_submit_attempt_count": 0,
    }
    _write_jsonl(
        pipeline_path,
        [
            _event("scalping_scanner_candidate_promoted", common, code="000507"),
            _event("order_bundle_failed", common, code="000507"),
        ],
    )
    _write_jsonl(threshold_path, [])

    report = mod.build_report(
        "2026-07-13",
        pipeline_path=pipeline_path,
        threshold_path=threshold_path,
        generated_at="fixed",
    )

    assert report["scanner_unique_funnel"]["final_outcome_counts"] == {
        "order_bundle_failed": 1
    }


def test_scanner_handoff_gap_defers_for_runtime_reflection_without_auto_apply(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline.jsonl"
    threshold_path = tmp_path / "threshold.jsonl"
    _write_jsonl(
        pipeline_path,
        [
            _event(
                "scalping_scanner_runtime_target_attach",
                {
                    "scanner_promotion_id": "SCANPROM-LEGACY-PID",
                    "runtime_target_attach_outcome": "attached",
                    "runtime_target_attach_reason": "new_watching_target_attached",
                    "effective_venue": "KRX",
                },
                code="000606",
            )
        ],
    )
    _write_jsonl(threshold_path, [])

    report = mod.build_report(
        "2026-07-13",
        pipeline_path=pipeline_path,
        threshold_path=threshold_path,
        generated_at="fixed",
    )

    order = next(
        item
        for item in report["workorder_directives"]
        if item["order_id"] == "order_scanner_runtime_handoff_provenance_gap"
    )
    assert order["decision"] == "defer_evidence"
    assert order["next_action"] == "verify_after_current_runtime_reflection"
    assert order["runtime_effect"] is False
    assert order["allowed_runtime_apply"] is False


def test_build_report_incrementally_aggregates_only_appended_rows(tmp_path):
    pipeline_path = tmp_path / "pipeline.jsonl"
    threshold_path = tmp_path / "threshold.jsonl"
    state_path = tmp_path / "state.json"
    first_event = _event(
        "ws_subscription_freshness_snapshot",
        {
            "freshness_state": "stale",
            "repair_reason": "subscription_stale",
            "ws_last_0b_age_ms": "61000",
            "ws_last_0d_age_ms": "61000",
        },
    )
    second_event = _event(
        "scalping_scanner_fast_precheck",
        {
            "ws_last_0b_age_ms": "50000",
            "ws_last_0d_age_ms": "4000",
            "source_quality_block_reason": "trade_tick_quiet",
        },
        code="000002",
    )
    _write_jsonl(pipeline_path, [first_event])
    _write_jsonl(threshold_path, [])

    initial = mod.build_report(
        "2026-07-13",
        pipeline_path=pipeline_path,
        threshold_path=threshold_path,
        incremental_state_path=state_path,
        generated_at="initial",
    )
    with pipeline_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(second_event, ensure_ascii=False) + "\n")
    incremental = mod.build_report(
        "2026-07-13",
        pipeline_path=pipeline_path,
        threshold_path=threshold_path,
        incremental_state_path=state_path,
        generated_at="incremental",
    )

    assert initial["pipeline_event_count"] == 1
    assert initial["input_processing"]["mode"] == "full_streaming_rebuild"
    assert incremental["pipeline_event_count"] == 2
    assert incremental["pipeline_counts"]["subscription_stale"] == 1
    assert incremental["pipeline_counts"]["trade_tick_quiet"] == 1
    assert (
        incremental["input_processing"]["mode"] == "incremental_streaming_aggregation"
    )
    assert incremental["input_processing"]["appended_event_count"] == 1
    assert incremental["input_processing"]["incremental_state_reason"] == "state_reused"
    assert (
        incremental["input_processing"]["source_offsets"]["pipeline_events"][
            "size_bytes"
        ]
        >= incremental["input_processing"]["source_offsets"]["pipeline_events"][
            "offset"
        ]
    )
    assert (
        incremental["input_processing"]["source_offsets"]["pipeline_events"][
            "source_identity_stable_during_scan"
        ]
        is True
    )


def test_incremental_state_preserves_scanner_bbo_first_hit_lineage(
    tmp_path, monkeypatch
):
    _install_verified_symbol_master(monkeypatch)
    pipeline_path = tmp_path / "pipeline.jsonl"
    threshold_path = tmp_path / "threshold.jsonl"
    state_path = tmp_path / "state.json"
    common = {
        "scanner_promotion_id": "SCANPROM-INCREMENTAL-BBO",
        "scanner_scan_generation_id": "SCANGEN-INCREMENTAL-BBO",
        "scanner_scan_rank": 1,
        "scanner_ranked_candidate_count": 1,
        "effective_venue": "KRX",
        "market_session_bucket": "KRX_REGULAR",
    }
    promotion = _event(
        "scalping_scanner_candidate_promoted",
        {
            **common,
            "scanner_promotion_reanchor_best_bid": 100,
            "scanner_promotion_reanchor_best_ask": 101,
            "scanner_promotion_reanchor_effective_quote_age_ms": 10,
            "scanner_promotion_reanchor_source": "ws_executable_bbo",
            "scanner_promotion_reanchor_source_fresh": True,
        },
        code="000709",
        emitted_at="2026-08-31T09:10:00+09:00",
    )
    precheck = _event(
        "scalping_scanner_fast_precheck",
        {
            **common,
            "fast_precheck_result": "eligible_for_heavy_entry_eval",
            "scanner_promotion_reanchor_best_bid": 103,
            "scanner_promotion_reanchor_best_ask": 104,
            "scanner_promotion_reanchor_effective_quote_age_ms": 10,
            "scanner_promotion_reanchor_source": "ws_executable_bbo",
            "scanner_promotion_reanchor_source_fresh": True,
        },
        code="000709",
        emitted_at="2026-08-31T09:10:02+09:00",
    )
    _write_jsonl(pipeline_path, [promotion])
    _write_jsonl(threshold_path, [])

    mod.build_report(
        "2026-08-31",
        pipeline_path=pipeline_path,
        threshold_path=threshold_path,
        incremental_state_path=state_path,
    )
    with pipeline_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(precheck, ensure_ascii=False) + "\n")
    incremental = mod.build_report(
        "2026-08-31",
        pipeline_path=pipeline_path,
        threshold_path=threshold_path,
        incremental_state_path=state_path,
    )

    attribution = incremental["scanner_unique_funnel"]["economic_cohorts"][
        "executable_bbo_attribution"
    ]
    assert incremental["input_processing"]["mode"] == (
        "incremental_streaming_aggregation"
    )
    assert attribution["status"] == "source_only_economics_available"
    assert attribution["exact_bbo_joined_count"] == 1
    assert attribution["first_hit_counts"] == {"sampled_gross_target_first": 1}


def test_build_report_rebuilds_incremental_state_after_source_truncation(tmp_path):
    pipeline_path = tmp_path / "pipeline.jsonl"
    threshold_path = tmp_path / "threshold.jsonl"
    state_path = tmp_path / "state.json"
    stale_event = _event(
        "ws_subscription_freshness_snapshot",
        {
            "freshness_state": "stale",
            "repair_reason": "subscription_stale",
            "ws_last_0b_age_ms": "61000",
            "ws_last_0d_age_ms": "61000",
        },
    )
    _write_jsonl(pipeline_path, [stale_event, stale_event])
    _write_jsonl(threshold_path, [])
    mod.build_report(
        "2026-07-13",
        pipeline_path=pipeline_path,
        threshold_path=threshold_path,
        incremental_state_path=state_path,
    )
    _write_jsonl(pipeline_path, [stale_event])

    rebuilt = mod.build_report(
        "2026-07-13",
        pipeline_path=pipeline_path,
        threshold_path=threshold_path,
        incremental_state_path=state_path,
    )

    assert rebuilt["pipeline_event_count"] == 1
    assert rebuilt["pipeline_counts"]["subscription_stale"] == 1
    assert rebuilt["input_processing"]["mode"] == "full_streaming_rebuild"
    assert (
        rebuilt["input_processing"]["incremental_state_reason"]
        == "pipeline_events_truncated"
    )


def test_build_report_rebuilds_incremental_state_after_schema_change(tmp_path):
    pipeline_path = tmp_path / "pipeline.jsonl"
    threshold_path = tmp_path / "threshold.jsonl"
    state_path = tmp_path / "state.json"
    event = _event(
        "scalping_scanner_candidate_promoted",
        {
            "scanner_promotion_id": "SCANPROM-000707-1000000",
            "scanner_scan_generation_id": "SCANGEN-SCHEMA-CHANGE",
            "scanner_scan_rank": 1,
            "scanner_ranked_candidate_count": 1,
        },
        code="000707",
    )
    _write_jsonl(pipeline_path, [event])
    _write_jsonl(threshold_path, [])
    mod.build_report(
        "2026-07-13",
        pipeline_path=pipeline_path,
        threshold_path=threshold_path,
        incremental_state_path=state_path,
    )
    stale_state = json.loads(state_path.read_text(encoding="utf-8"))
    stale_state["schema_version"] = "intraday_ws_freshness_incremental_v4"
    state_path.write_text(json.dumps(stale_state), encoding="utf-8")

    rebuilt = mod.build_report(
        "2026-07-13",
        pipeline_path=pipeline_path,
        threshold_path=threshold_path,
        incremental_state_path=state_path,
    )

    assert rebuilt["pipeline_event_count"] == 1
    assert rebuilt["input_processing"]["mode"] == "full_streaming_rebuild"
    assert rebuilt["input_processing"]["incremental_state_reason"] == "schema_changed"


def test_build_report_does_not_advance_offset_past_partial_jsonl_line(tmp_path):
    pipeline_path = tmp_path / "pipeline.jsonl"
    threshold_path = tmp_path / "threshold.jsonl"
    state_path = tmp_path / "state.json"
    event = _event(
        "ws_subscription_freshness_snapshot",
        {
            "freshness_state": "stale",
            "repair_reason": "subscription_stale",
            "ws_last_0b_age_ms": "61000",
            "ws_last_0d_age_ms": "61000",
        },
    )
    pipeline_path.write_text(json.dumps(event), encoding="utf-8")
    _write_jsonl(threshold_path, [])

    partial = mod.build_report(
        "2026-07-13",
        pipeline_path=pipeline_path,
        threshold_path=threshold_path,
        incremental_state_path=state_path,
    )
    with pipeline_path.open("a", encoding="utf-8") as handle:
        handle.write("\n")
    completed = mod.build_report(
        "2026-07-13",
        pipeline_path=pipeline_path,
        threshold_path=threshold_path,
        incremental_state_path=state_path,
    )

    assert partial["pipeline_event_count"] == 0
    assert completed["pipeline_event_count"] == 1
    assert completed["pipeline_counts"]["subscription_stale"] == 1
    assert completed["input_processing"]["appended_event_count"] == 1


def test_build_report_rebuilds_when_incremental_aggregate_state_is_invalid(tmp_path):
    pipeline_path = tmp_path / "pipeline.jsonl"
    threshold_path = tmp_path / "threshold.jsonl"
    state_path = tmp_path / "state.json"
    event = _event(
        "ws_subscription_freshness_snapshot",
        {
            "freshness_state": "stale",
            "repair_reason": "subscription_stale",
            "ws_last_0b_age_ms": "61000",
            "ws_last_0d_age_ms": "61000",
        },
    )
    _write_jsonl(pipeline_path, [event])
    _write_jsonl(threshold_path, [])
    mod.build_report(
        "2026-07-13",
        pipeline_path=pipeline_path,
        threshold_path=threshold_path,
        incremental_state_path=state_path,
    )
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["counts"]["subscription_stale"] = "invalid"
    state_path.write_text(json.dumps(state), encoding="utf-8")

    rebuilt = mod.build_report(
        "2026-07-13",
        pipeline_path=pipeline_path,
        threshold_path=threshold_path,
        incremental_state_path=state_path,
    )

    assert rebuilt["pipeline_event_count"] == 1
    assert rebuilt["pipeline_counts"]["subscription_stale"] == 1
    assert rebuilt["input_processing"]["incremental_state_reason"] == (
        "aggregate_state_invalid"
    )


def test_build_report_uses_same_day_live_dashboard_snapshot_fallback(
    tmp_path, monkeypatch
):
    pipeline_path = tmp_path / "pipeline_events_2026-07-30.jsonl"
    threshold_path = tmp_path / "threshold_events_2026-07-30.jsonl"
    dashboard_path = tmp_path / "latest.json"
    _write_jsonl(pipeline_path, [])
    _write_jsonl(threshold_path, [])
    dashboard_path.write_text(
        json.dumps(
            {
                "schema_version": "kiwoom_ws_dashboard_snapshot_v1",
                "generated_at": "2026-07-30T12:20:00+09:00",
                "decision_authority": "source_quality_only",
                "runtime_effect": False,
                "stocks": {
                    "000101": {
                        "last_realtime_type_ages_ms": {
                            "0B": 120.0,
                            "0D": 80.0,
                        },
                        "last_0b_age_ms": 120.0,
                        "last_ws_market_route": "krx_nxt_integrated",
                        "last_ws_market_suffix": "_AL",
                    },
                    "000202": {
                        "last_realtime_type_ages_ms": {
                            "0B": 45000.0,
                            "0D": 100.0,
                        },
                        "last_0b_age_ms": 45000.0,
                        "last_trade_cum_volume": 1234,
                        "last_ws_market_route": "krx_regular",
                        "last_ws_market_suffix": "",
                    },
                    "000303": {
                        "last_realtime_type_ages_ms": {
                            "0B": 45000.0,
                            "0D": 41000.0,
                        },
                        "last_0b_age_ms": 45000.0,
                        "last_ws_market_route": "nxt_only",
                        "last_ws_market_suffix": "_NX",
                    },
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "DEFAULT_DASHBOARD_SNAPSHOT_PATH", dashboard_path)

    report = mod.build_report(
        "2026-07-30",
        pipeline_path=pipeline_path,
        threshold_path=threshold_path,
        generated_at="fixed",
    )

    assert report["subscription_snapshot_path"] == str(dashboard_path)
    assert report["subscription_snapshot_provenance"] == {
        "source": "same_day_live_dashboard_snapshot_fallback",
        "selected": True,
        "selection_reason": "same_day_schema_match",
        "schema_version": "kiwoom_ws_dashboard_snapshot_v1",
        "generated_at": "2026-07-30T12:20:00+09:00",
        "subscription_state_available": False,
    }
    assert report["snapshot_summary"]["row_count"] == 3
    assert report["snapshot_summary"]["trade_tick_quiet_count"] == 1
    assert (
        report["snapshot_summary"]["top_trade_tick_quiet_symbols"][0][
            "last_trade_cum_volume"
        ]
        == 1234.0
    )
    assert report["snapshot_summary"]["repair_recommended_count"] == 0
    assert report["snapshot_summary"]["subscription_stale_like_count"] == 0
    assert report["snapshot_summary"]["observed_stale_like_count"] == 1
    assert report["snapshot_summary"]["registered_route_counts"] == {}
    assert report["snapshot_summary"]["observed_market_route_counts"] == {
        "krx_nxt_integrated": 1,
        "krx_regular": 1,
        "nxt_only": 1,
    }
    assert report["snapshot_summary"]["observed_market_suffix_counts"] == {
        "_AL": 1,
        "KRX": 1,
        "_NX": 1,
    }
    rendered = mod._render_monitor_markdown(report)
    assert f"- subscription_snapshot_path: `{dashboard_path}`" in rendered
    assert "same_day_live_dashboard_snapshot_fallback" in rendered


def test_build_report_rejects_cross_day_live_dashboard_snapshot_fallback(
    tmp_path, monkeypatch
):
    pipeline_path = tmp_path / "pipeline_events_2026-07-30.jsonl"
    threshold_path = tmp_path / "threshold_events_2026-07-30.jsonl"
    dashboard_path = tmp_path / "latest.json"
    _write_jsonl(pipeline_path, [])
    _write_jsonl(threshold_path, [])
    dashboard_path.write_text(
        json.dumps(
            {
                "schema_version": "kiwoom_ws_dashboard_snapshot_v1",
                "generated_at": "2026-07-29T19:59:59+09:00",
                "stocks": {"000101": {"last_0b_age_ms": 10.0}},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "DEFAULT_DASHBOARD_SNAPSHOT_PATH", dashboard_path)

    report = mod.build_report(
        "2026-07-30",
        pipeline_path=pipeline_path,
        threshold_path=threshold_path,
        generated_at="fixed",
    )

    assert report["subscription_snapshot_path"] == str(dashboard_path)
    assert report["subscription_snapshot_provenance"]["selected"] is False
    assert (
        report["subscription_snapshot_provenance"]["selection_reason"]
        == "default_snapshot_target_date_mismatch"
    )
    assert report["snapshot_summary"]["row_count"] == 0


def test_build_report_surfaces_provider_none_as_separate_incident(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-13.jsonl"
    threshold_path = tmp_path / "threshold_events_2026-07-13.jsonl"
    _write_jsonl(
        pipeline_path,
        [
            _event(
                "ai_confirmed",
                {
                    "ai_provider": "none",
                },
            )
        ],
    )
    _write_jsonl(threshold_path, [])

    report = mod.build_report(
        "2026-07-13",
        pipeline_path=pipeline_path,
        threshold_path=threshold_path,
        generated_at="fixed",
    )

    assert report["pipeline_counts"]["provider_none"] == 1
    assert report["pipeline_counts"].get("both_ws_stale", 0) == 0
    assert report["workorder_summary"]["provider_none_incident_count"] == 1
    assert {item["order_id"] for item in report["workorder_directives"]} == {
        "order_ai_provider_none_intraday_incident"
    }


def test_build_report_surfaces_explicit_scanner_stale_backoff_separately(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-13.jsonl"
    threshold_path = tmp_path / "threshold_events_2026-07-13.jsonl"
    _write_jsonl(
        pipeline_path,
        [
            _event(
                "scalping_scanner_watching_runtime_skip",
                {
                    "skip_reason": "scanner_fast_precheck_budget_reallocated",
                    "fast_precheck_observed_reason": "scanner_ws_stale_backoff_active",
                    "scanner_ws_stale_backoff_reason": "persistent_ws_gap",
                    "ws_repair_cycle_state": "ws_reg_reissued_waiting_snapshot",
                    "scanner_ws_stale_backoff_recheck_reason": (
                        "not_applicable_active_backoff"
                    ),
                    "ws_last_strength_history_age_ms": "7886.226",
                },
                code="047920",
            )
        ],
    )
    _write_jsonl(threshold_path, [])

    report = mod.build_report(
        "2026-07-13",
        pipeline_path=pipeline_path,
        threshold_path=threshold_path,
        generated_at="fixed",
    )

    assert report["pipeline_counts"]["decision_stage_stale_backoff"] == 1
    assert report["pipeline_counts"].get("subscription_stale", 0) == 0
    assert report["by_stage"]["decision_stage_stale_backoff"] == [
        {
            "stage": "scalping_scanner_watching_runtime_skip",
            "count": 1,
        }
    ]
    assert report["by_symbol"]["decision_stage_stale_backoff"] == [
        {"stock_code": "047920", "count": 1}
    ]
    assert {item["order_id"] for item in report["workorder_directives"]} == {
        "order_ws_decision_stage_stale_backoff_attribution"
    }
    contract = report["decision_stage_stale_backoff_metric_contract"]
    assert contract["runtime_effect"] is False
    assert contract["decision_authority"] == "instrumentation_only_no_runtime_mutation"
    attribution = report["causal_attribution"]["decision_stage_stale_backoff"]
    assert attribution["reason_counts"] == {"persistent_ws_gap": 1}
    assert attribution["repair_cycle_state_counts"] == {
        "ws_reg_reissued_waiting_snapshot": 1
    }
    assert attribution["recheck_reason_counts"] == {"not_applicable_active_backoff": 1}
    assert attribution["watchlist_outcome_counts"] == {"decision_stage_only": 1}
    order = report["workorder_directives"][0]
    assert order["decision"] == "defer_evidence"
    assert order["next_action"] == "recheck_after_postclose"
    assert order["implementation_state"] == "implemented_in_source_report"


def test_write_report_outputs_monitor_and_workorder_files(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path / "monitor")
    monkeypatch.setattr(mod, "WORKORDER_REPORT_DIR", tmp_path / "workorder-report")
    monkeypatch.setattr(mod, "WORKORDER_DOC_DIR", tmp_path / "workorder-docs")
    report = {
        "target_date": "2026-07-13",
        "pipeline_event_count": 0,
        "pipeline_counts": {},
        "pipeline_rates": {},
        "snapshot_summary": {},
        "source_missing": [],
        "workorder_directives": [],
        "workorder_summary": {"selected_order_count": 0},
    }

    monitor_json, monitor_md, workorder_json, workorder_md = mod.write_report(report)

    assert monitor_json.exists()
    assert monitor_md.exists()
    assert workorder_json.exists()
    assert workorder_md.exists()
    payload = json.loads(workorder_json.read_text(encoding="utf-8"))
    assert (
        payload["metric_contract"]["decision_authority"]
        == "ws_freshness_intraday_monitor_source_only"
    )
    assert payload["summary"]["selected_order_count"] == 0


def test_write_report_monitor_only_skips_workorder_files(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path / "monitor")
    monkeypatch.setattr(mod, "WORKORDER_REPORT_DIR", tmp_path / "workorder-report")
    monkeypatch.setattr(mod, "WORKORDER_DOC_DIR", tmp_path / "workorder-docs")
    report = {
        "target_date": "2026-07-13",
        "pipeline_event_count": 0,
        "pipeline_counts": {},
        "pipeline_rates": {},
        "snapshot_summary": {},
        "source_missing": [],
        "workorder_directives": [],
        "workorder_summary": {"selected_order_count": 0},
    }

    monitor_json, monitor_md, workorder_json, workorder_md = mod.write_report(
        report, monitor_only=True
    )

    assert monitor_json.exists()
    assert monitor_md.exists()
    assert workorder_json is None
    assert workorder_md is None
    assert not (tmp_path / "workorder-report").exists()
    assert not (tmp_path / "workorder-docs").exists()
