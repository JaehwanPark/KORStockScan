import json

from src.engine.scalping import microstructure_reaction_context as mod


def test_microstructure_reaction_context_report_preserves_contract_and_keys(
    tmp_path, monkeypatch
):
    event_dir = tmp_path / "pipeline_events"
    report_dir = tmp_path / "report" / "microstructure_reaction_context"
    event_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", event_dir)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)

    event_path = event_dir / "pipeline_events_2026-05-31.jsonl"
    event_path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "stage": "ai_confirmed",
                        "stock_code": "A005930",
                        "stock_name": "Samsung",
                        "record_id": "real-1",
                        "emitted_at": "2026-05-31T09:01:00+09:00",
                        "fields": {
                            "source_event_stage": "ai_confirmed",
                            "actual_order_submitted": True,
                            "broker_order_forbidden": False,
                            "microstructure_reaction_context_version": "microstructure_reaction_context_v1",
                            "microstructure_reaction_context_status": "ok",
                            "microstructure_reaction_ask_sweep_score": 72,
                            "microstructure_reaction_post_sweep_hold_score": 68,
                            "microstructure_reaction_bid_replenishment_score": 61,
                            "microstructure_reaction_wall_replenishment_risk_score": 35,
                            "microstructure_reaction_vi_proximity_risk": 10,
                            "microstructure_reaction_entry_reaction_quality": "favorable_reaction",
                            "microstructure_reaction_source_quality": "fresh_short_window",
                            "microstructure_reaction_context_hash": "abc123",
                            "tick_aggressor_source_counts": "{'kiwoom_0b_signed_trade_volume': 5}",
                            "tick_trade_value_source_counts": "{'1313': 3, 'calc_price_x_1030_1031_sum': 2}",
                            "tick_trade_value_1313_count": 3,
                            "tick_trade_value_1313_missing_count": 2,
                            "trade_volume_source_counts": "{'1030_1031_sum': 5}",
                            "trade_volume_1030_1031_vs_15_evaluable_count": 5,
                            "trade_volume_1030_1031_vs_15_mismatch_count": 1,
                            "kiwoom_0b_aux_observed_count": 10,
                            "kiwoom_0b_1313_present_count": 6,
                            "kiwoom_0b_1313_missing_count": 4,
                            "kiwoom_0b_trade_value_source_counts": "{'1313': 6, 'calc_price_x_1030_1031_sum': 4}",
                            "kiwoom_0b_trade_volume_source_counts": "{'1030_1031_sum': 10}",
                            "kiwoom_0b_1030_1031_vs_15_evaluable_count": 10,
                            "kiwoom_0b_1030_1031_vs_15_mismatch_count": 2,
                            "ka10003_buy_dominance_observation": {
                                "source_counts": {
                                    "1030_1031_split": 2,
                                    "signed_volume": 1,
                                },
                                "trade_value_source_counts": {
                                    "1313": 2,
                                    "calc_price_x_volume": 1,
                                },
                                "inside_spread_count": 1,
                                "split_vs_15_evaluable_count": 2,
                                "split_vs_15_mismatch_count": 1,
                            },
                            "v_pw_now": 131.0,
                            "v_pw_source": "ws_0b",
                            "v_pw_runtime_support_usable": True,
                            "v_pw_ws_value": 131.0,
                            "v_pw_rest_value": 109.0,
                            "ka10046_strength_source": "ka10046_rest_strength_trend",
                            "ka10046_strength_decision_authority": "strength_trend_rest_fallback_source_only",
                            "ka10046_strength_runtime_effect": False,
                            "ka10046_strength_rest_received_ts_ms": 1780000000000,
                            "market_data_signed_tape_state": "sell_dominated",
                            "market_data_signed_tape_sample_count": 3,
                            "market_data_signed_tape_buy_count": 1,
                            "market_data_signed_tape_sell_count": 2,
                            "market_data_signed_tape_buy_volume": 100,
                            "market_data_signed_tape_sell_volume": 350,
                            "market_data_signed_tape_buy_ratio_pct": 22.222,
                            "market_data_rest_signed_tape_pressure_usable": False,
                            "rest_signed_trade_ticks": [
                                {
                                    "signed_trade_volume": "-200",
                                    "rest_signed_tape_source": "ka10084",
                                },
                                {
                                    "signed_trade_volume": "+100",
                                    "rest_signed_tape_source": "ka10084",
                                },
                            ],
                            "latency_true_ofi_direct_canary_signed_tape_sample_count": 3,
                            "latency_true_ofi_direct_canary_signed_tape_buy_count": 1,
                            "latency_true_ofi_direct_canary_signed_tape_sell_count": 2,
                            "latency_true_ofi_direct_canary_signed_tape_buy_volume": 100,
                            "latency_true_ofi_direct_canary_signed_tape_sell_volume": 350,
                            "latency_true_ofi_direct_canary_signed_tape_net_buy_volume": -250,
                            "latency_true_ofi_direct_canary_signed_tape_buy_ratio": 22.222,
                            "latency_true_ofi_direct_canary_signed_tape_latest_side": "SELL",
                            "latency_true_ofi_direct_canary_signed_tape_sell_dominated": True,
                            "latency_true_ofi_direct_canary_signed_tape_latest_buy_single": 0,
                            "latency_true_ofi_direct_canary_signed_tape_latest_sell_single": 200,
                            "latency_true_ofi_direct_canary_signed_tape_latest_single_sell_dominated": True,
                            "latency_true_ofi_direct_canary_tape_block_reason": "signed_tape_sell_dominated",
                            "latency_true_ofi_direct_canary_tape_support_ok": False,
                            "quote_stale": False,
                        },
                    }
                ),
                json.dumps(
                    {
                        "stage": "blocked_liquidity",
                        "stock_code": "A000660",
                        "record_id": "probe-1",
                        "emitted_at": "2026-05-31T09:02:00+09:00",
                        "fields": {
                            "source_event_stage": "blocked_liquidity",
                            "sim_record_id": "sim-1",
                            "sim_parent_record_id": "parent-1",
                            "actual_order_submitted": False,
                            "broker_order_forbidden": True,
                            "microstructure_reaction_context_version": "microstructure_reaction_context_v1",
                            "microstructure_reaction_context_status": "stale",
                            "microstructure_reaction_ask_sweep_score": 50,
                            "microstructure_reaction_post_sweep_hold_score": 50,
                            "microstructure_reaction_bid_replenishment_score": 50,
                            "microstructure_reaction_wall_replenishment_risk_score": 50,
                            "microstructure_reaction_vi_proximity_risk": 0,
                            "microstructure_reaction_entry_reaction_quality": "neutral_unusable",
                            "microstructure_reaction_source_quality": "stale_tick_or_quote",
                            "microstructure_reaction_context_hash": "def456",
                            "tick_aggressor_source_counts": "{'missing_best_quote': 5}",
                            "tick_trade_value_source_counts": "{'calc_price_x_15_abs': 5}",
                            "tick_trade_value_1313_count": 0,
                            "tick_trade_value_1313_missing_count": 5,
                            "trade_volume_source_counts": "{'15_abs': 5}",
                            "trade_volume_1030_1031_vs_15_evaluable_count": 0,
                            "trade_volume_1030_1031_vs_15_mismatch_count": 0,
                            "kiwoom_0b_aux_observed_count": 3,
                            "kiwoom_0b_1313_present_count": 0,
                            "kiwoom_0b_1313_missing_count": 3,
                            "kiwoom_0b_trade_value_source_counts": "{'calc_price_x_15_abs': 3}",
                            "kiwoom_0b_trade_volume_source_counts": "{'15_abs': 3}",
                            "kiwoom_0b_1030_1031_vs_15_evaluable_count": 0,
                            "kiwoom_0b_1030_1031_vs_15_mismatch_count": 0,
                            "ka10003_buy_dominance_observation_source_counts": "{'inside_excluded': 3}",
                            "ka10003_buy_dominance_observation_trade_value_source_counts": "{'calc_price_x_volume': 3}",
                            "ka10003_buy_dominance_observation_inside_spread_count": 3,
                            "ka10003_buy_dominance_observation_split_vs_15_evaluable_count": 0,
                            "ka10003_buy_dominance_observation_split_vs_15_mismatch_count": 0,
                            "v_pw_now": 120.0,
                            "v_pw_source": "ka10046_rest_fallback",
                            "v_pw_runtime_support_usable": False,
                            "v_pw_ws_value": 0.0,
                            "v_pw_rest_value": 120.0,
                            "ka10046_strength_source": "ka10046_rest_strength_trend",
                            "ka10046_strength_decision_authority": "strength_trend_rest_fallback_source_only",
                            "ka10046_strength_runtime_effect": False,
                            "ka10046_strength_rest_received_ts_ms": 1780000001000,
                            "market_data_signed_tape_state": "mixed",
                            "market_data_signed_tape_sample_count": 2,
                            "market_data_signed_tape_buy_count": 1,
                            "market_data_signed_tape_sell_count": 1,
                            "market_data_signed_tape_buy_volume": 90,
                            "market_data_signed_tape_sell_volume": 80,
                            "market_data_signed_tape_buy_ratio_pct": 52.941,
                            "market_data_rest_signed_tape_pressure_usable": False,
                            "rest_signed_trade_ticks": "[{'signed_trade_volume': '-80', 'rest_signed_tape_source': 'ka10084'}]",
                            "latency_true_ofi_direct_canary_signed_tape_sample_count": 2,
                            "latency_true_ofi_direct_canary_signed_tape_buy_count": 1,
                            "latency_true_ofi_direct_canary_signed_tape_sell_count": 1,
                            "latency_true_ofi_direct_canary_signed_tape_buy_volume": 90,
                            "latency_true_ofi_direct_canary_signed_tape_sell_volume": 80,
                            "latency_true_ofi_direct_canary_signed_tape_net_buy_volume": 10,
                            "latency_true_ofi_direct_canary_signed_tape_buy_ratio": 52.941,
                            "latency_true_ofi_direct_canary_signed_tape_latest_side": "BUY",
                            "latency_true_ofi_direct_canary_signed_tape_sell_dominated": False,
                            "latency_true_ofi_direct_canary_signed_tape_latest_buy_single": 90,
                            "latency_true_ofi_direct_canary_signed_tape_latest_sell_single": 0,
                            "latency_true_ofi_direct_canary_signed_tape_latest_single_sell_dominated": False,
                            "latency_true_ofi_direct_canary_tape_support_ok": True,
                            "quote_stale": True,
                        },
                    }
                ),
                json.dumps(
                    {
                        "stage": "latency_block",
                        "stock_code": "A111111",
                        "record_id": "quote-only",
                        "emitted_at": "2026-05-31T09:03:00+09:00",
                        "fields": {
                            "quote_stale": True,
                            "ws_age_ms": 5000,
                        },
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    report = mod.build_microstructure_reaction_context_report("2026-05-31")

    assert report["report_type"] == "microstructure_reaction_context"
    assert report["runtime_effect"] is False
    assert report["decision_authority"] == "entry_confidence_modifier_source_only"
    assert report["metric_role"] == "feature_context"
    assert report["primary_decision_metric"] == "source_quality_adjusted_ev_pct"
    assert "standalone_buy" in report["forbidden_uses"]
    assert "broker_guard_bypass" in report["forbidden_uses"]
    assert report["summary"]["row_count"] == 2
    assert report["summary"]["ok_count"] == 1
    assert report["summary"]["real_submitted_count"] == 1
    assert report["summary"]["v_pw_source_counts"] == {
        "ka10046_rest_fallback": 1,
        "ws_0b": 1,
    }
    assert report["summary"]["v_pw_rest_fallback_count"] == 1
    assert report["summary"]["v_pw_ws_0b_count"] == 1
    assert report["summary"]["v_pw_rest_fallback_rate_pct"] == 50.0
    assert report["summary"]["v_pw_runtime_support_unusable_count"] == 1
    assert report["summary"]["ka10046_rest_fallback_quote_freshness_counts"] == {
        "stale": 1
    }
    assert report["summary"]["ka10046_rest_fallback_with_stale_quote_count"] == 1
    assert report["summary"]["ka10046_strength_runtime_effect_true_count"] == 0
    assert report["summary"]["ka10046_strength_missing_received_ts_count"] == 0
    assert report["summary"]["ka10046_0b_strength_compare_evaluable_count"] == 1
    assert report["summary"]["ka10046_0b_strength_abs_diff_avg"] == 22.0
    assert report["summary"]["ka10046_0b_strength_divergence20_count"] == 1
    assert report["summary"]["ka10046_0b_strength_divergence20_rate_pct"] == 100.0
    assert report["summary"]["market_data_signed_tape_state_counts"] == {
        "mixed": 1,
        "sell_dominated": 1,
    }
    assert report["summary"]["market_data_signed_tape_sample_count_total"] == 5
    assert report["summary"]["market_data_signed_tape_buy_count_total"] == 2
    assert report["summary"]["market_data_signed_tape_sell_count_total"] == 3
    assert report["summary"]["market_data_signed_tape_buy_volume_total"] == 190
    assert report["summary"]["market_data_signed_tape_sell_volume_total"] == 430
    assert (
        report["summary"]["market_data_rest_signed_tape_pressure_usable_true_count"]
        == 0
    )
    assert report["summary"]["rest_signed_trade_ticks_row_count"] == 3
    assert report["summary"]["rest_signed_trade_ticks_source_counts"] == {"ka10084": 3}
    assert (
        report["summary"][
            "latency_true_ofi_direct_canary_signed_tape_sample_count_total"
        ]
        == 5
    )
    assert (
        report["summary"]["latency_true_ofi_direct_canary_signed_tape_buy_count_total"]
        == 2
    )
    assert (
        report["summary"]["latency_true_ofi_direct_canary_signed_tape_sell_count_total"]
        == 3
    )
    assert (
        report["summary"][
            "latency_true_ofi_direct_canary_signed_tape_net_buy_volume_sum"
        ]
        == -240
    )
    assert report["summary"][
        "latency_true_ofi_direct_canary_signed_tape_latest_side_counts"
    ] == {
        "BUY": 1,
        "SELL": 1,
    }
    assert (
        report["summary"][
            "latency_true_ofi_direct_canary_signed_tape_sell_dominated_count"
        ]
        == 1
    )
    assert (
        report["summary"][
            "latency_true_ofi_direct_canary_signed_tape_latest_single_sell_dominated_count"
        ]
        == 1
    )
    assert report["summary"][
        "latency_true_ofi_direct_canary_tape_block_reason_counts"
    ] == {
        "missing": 1,
        "signed_tape_sell_dominated": 1,
    }
    assert report["rows"][0]["stock_code"] == "005930"
    assert report["rows"][1]["sim_record_id"] == "sim-1"
    assert report["rows"][1]["sim_parent_record_id"] == "parent-1"
    assert report["rows"][1]["broker_order_forbidden"] is True
    assert report["summary"]["tick_aggressor_source_counts"] == {
        "kiwoom_0b_signed_trade_volume": 5,
        "missing_best_quote": 5,
    }
    assert report["summary"]["tick_trade_value_1313_missing_count"] == 7
    assert report["summary"]["tick_trade_value_1313_missing_rate_pct"] == 70.0
    assert report["summary"]["trade_volume_1030_1031_vs_15_mismatch_count"] == 1
    assert report["summary"]["trade_volume_1030_1031_vs_15_mismatch_rate_pct"] == 20.0
    assert report["summary"]["kiwoom_0b_aux_observed_count"] == 13
    assert report["summary"]["kiwoom_0b_1313_missing_count"] == 7
    assert report["summary"]["kiwoom_0b_1313_missing_rate_pct"] == 53.846
    assert report["summary"]["kiwoom_0b_trade_value_source_counts"] == {
        "1313": 6,
        "calc_price_x_1030_1031_sum": 4,
        "calc_price_x_15_abs": 3,
    }
    assert report["summary"]["kiwoom_0b_1030_1031_vs_15_mismatch_rate_pct"] == 20.0
    assert report["summary"]["ka10003_buy_dominance_observation_source_counts"] == {
        "1030_1031_split": 2,
        "inside_excluded": 3,
        "signed_volume": 1,
    }
    assert report["summary"][
        "ka10003_buy_dominance_observation_trade_value_source_counts"
    ] == {
        "1313": 2,
        "calc_price_x_volume": 4,
    }
    assert (
        report["summary"]["ka10003_buy_dominance_observation_inside_spread_count"] == 4
    )
    assert (
        report["summary"][
            "ka10003_buy_dominance_observation_split_vs_15_mismatch_count"
        ]
        == 1
    )
    assert (
        report["summary"][
            "ka10003_buy_dominance_observation_split_vs_15_mismatch_rate_pct"
        ]
        == 50.0
    )
    assert report["summary"]["code_improvement_order_count"] == 2
    assert [
        item["order_id"] for item in report["summary"]["top_code_improvement_orders"]
    ] == [
        "order_microstructure_signed_tape_runtime_candidate_review",
        "order_microstructure_ka10003_split_vs_15_observation_review",
    ]
    order_by_id = {
        order["order_id"]: order for order in report["code_improvement_orders"]
    }
    signed_tape_order = order_by_id[
        "order_microstructure_signed_tape_runtime_candidate_review"
    ]
    assert signed_tape_order["route"] == "auto_family_candidate"
    assert "mapped_family" not in signed_tape_order
    assert (
        signed_tape_order["candidate_family"]
        == "microstructure_signed_tape_runtime_candidate"
    )
    assert signed_tape_order["runtime_effect"] is False
    assert signed_tape_order["allowed_runtime_apply"] is False
    assert signed_tape_order["actual_order_submitted"] is False
    assert signed_tape_order["broker_order_forbidden"] is True
    assert (
        signed_tape_order["implementation_provenance"][
            "requires_separate_runtime_apply_candidate"
        ]
        is True
    )
    ka10003_order = order_by_id[
        "order_microstructure_ka10003_split_vs_15_observation_review"
    ]
    assert ka10003_order["route"] == "instrumentation_order"
    assert ka10003_order["runtime_effect"] is False
    assert ka10003_order["allowed_runtime_apply"] is False
    markdown = (report_dir / "microstructure_reaction_context_2026-05-31.md").read_text(
        encoding="utf-8"
    )
    assert "code_improvement_order_count" in markdown
    assert "order_microstructure_signed_tape_runtime_candidate_review" in markdown
    assert (report_dir / "microstructure_reaction_context_2026-05-31.json").exists()
    assert (report_dir / "microstructure_reaction_context_2026-05-31.md").exists()
