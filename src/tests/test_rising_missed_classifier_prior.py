import json

from src.engine.monitoring import rising_missed_classifier_prior as mod


def _write(path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def test_blocker_outcome_prior_routes_positive_thin_sample_to_source_only_probe():
    report = {
        "summary": {
            "rising_missed_nxt_post_block_rolling_blocker_outcome_attribution": [
                {
                    "source_block_stage": "rising_missed_tick_speed_entry_block",
                    "source_block_reason": "tick_acceleration_ratio_lt_1",
                    "completed_sample_count": 2,
                    "gross_target_first_count": 1,
                    "adverse_stop_first_count": 0,
                    "no_hit_within_20m_count": 1,
                    "gross_first_hit_payoff_proxy_pct": 0.65,
                    "equal_weight_avg_mfe_after_block_pct": 1.31,
                    "equal_weight_avg_mae_after_block_pct": -0.33,
                    "source_dates": ["2026-07-29", "2026-08-03"],
                    "clean_tuning_baseline_date": "2026-06-05",
                    "sample_floor": "10_source_quality_pass_completed_samplers_per_blocker",
                    "sample_floor_met": False,
                    "decision_authority": "source_only_no_runtime_mutation",
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "window_policy": "clean_baseline_rolling_latest_20_report_artifacts",
                    "source_quality_gate": "completed_sampler_source_quality_pass",
                },
                {
                    "source_block_stage": "tp1_selector",
                    "source_block_reason": "rising_missed_tp1_hard_negative_evidence",
                    "completed_sample_count": 5,
                    "gross_target_first_count": 0,
                    "adverse_stop_first_count": 3,
                    "no_hit_within_20m_count": 2,
                    "gross_first_hit_payoff_proxy_pct": -0.42,
                    "equal_weight_avg_mfe_after_block_pct": 0.23,
                    "equal_weight_avg_mae_after_block_pct": -0.91,
                    "source_dates": ["2026-07-29", "2026-07-31"],
                    "clean_tuning_baseline_date": "2026-06-05",
                    "decision_authority": "source_only_no_runtime_mutation",
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "source_quality_gate": "completed_sampler_source_quality_pass",
                },
            ]
        }
    }

    rows = mod._build_blocker_outcome_priors(report)

    assert rows[0]["source_block_reason"] == "tick_acceleration_ratio_lt_1"
    assert rows[0]["exploration_assessment"] == "bounded_probe_exploration_candidate"
    assert rows[0]["sample_floor_met"] is False
    assert rows[0]["raw_adverse_first_is_standalone_veto"] is False
    assert rows[0]["metric_role"] == "source_quality_gated_blocker_outcome_attribution"
    assert (
        rows[0]["net_ev_state"] == "unavailable_fee_tax_and_no_hit_exit_outcome_missing"
    )
    assert rows[0]["runtime_effect"] is False
    assert rows[0]["allowed_runtime_apply"] is False
    assert rows[0]["actual_order_submitted"] is False
    assert rows[0]["broker_order_forbidden"] is True
    assert rows[1]["exploration_assessment"] == "hold_loss_dominant"


def test_blocker_outcome_prior_rejects_runtime_authority_leak():
    rows = mod._build_blocker_outcome_priors(
        {
            "summary": {
                "rising_missed_nxt_post_block_rolling_blocker_outcome_attribution": [
                    {
                        "source_block_stage": "tp1_selector",
                        "source_block_reason": "unsafe_row",
                        "completed_sample_count": 12,
                        "gross_target_first_count": 10,
                        "adverse_stop_first_count": 0,
                        "gross_first_hit_payoff_proxy_pct": 1.0,
                        "equal_weight_avg_mfe_after_block_pct": 2.0,
                        "equal_weight_avg_mae_after_block_pct": -0.1,
                        "source_dates": ["2026-08-03"],
                        "clean_tuning_baseline_date": "2026-06-05",
                        "decision_authority": "live_runtime",
                        "runtime_effect": True,
                        "allowed_runtime_apply": True,
                        "source_quality_gate": "completed_sampler_source_quality_pass",
                    }
                ]
            }
        }
    )

    assert rows[0]["exploration_assessment"] == "source_quality_blocked"
    assert rows[0]["runtime_effect"] is False
    assert rows[0]["allowed_runtime_apply"] is False


def test_blocker_outcome_prior_rejects_string_false_authority_flags():
    rows = mod._build_blocker_outcome_priors(
        {
            "summary": {
                "rising_missed_nxt_post_block_rolling_blocker_outcome_attribution": [
                    {
                        "source_block_stage": "tp1_selector",
                        "source_block_reason": "string_flags",
                        "completed_sample_count": 12,
                        "gross_target_first_count": 10,
                        "adverse_stop_first_count": 0,
                        "gross_first_hit_payoff_proxy_pct": 1.0,
                        "equal_weight_avg_mfe_after_block_pct": 2.0,
                        "equal_weight_avg_mae_after_block_pct": -0.1,
                        "source_dates": ["2026-08-03"],
                        "clean_tuning_baseline_date": "2026-06-05",
                        "decision_authority": "source_only_no_runtime_mutation",
                        "runtime_effect": "false",
                        "allowed_runtime_apply": "false",
                        "source_quality_gate": "completed_sampler_source_quality_pass",
                    }
                ]
            }
        }
    )

    assert rows[0]["exploration_assessment"] == "source_quality_blocked"


def test_prior_report_merges_daily_rolling_mtd_and_blocks_child_conflict(tmp_path):
    daily = _write(
        tmp_path / "daily.json",
        {
            "summary": {
                "sim_auto_positive_ev_top": [
                    {
                        "bucket_id": "entry_wait6579_ev_cohort",
                        "joined_sample": 3,
                        "source_quality_adjusted_ev_pct": 0.7,
                    }
                ]
            }
        },
    )
    rolling5d = _write(
        tmp_path / "rolling5d.json",
        {
            "parent_bucket_summaries": [
                {
                    "bucket_id": "entry_wait6579_ev_cohort",
                    "joined_sample": 10,
                    "source_quality_adjusted_ev_pct": 1.1,
                }
            ]
        },
    )
    rolling10d = _write(
        tmp_path / "rolling10d.json",
        {
            "sim_auto_positive_ev_top": [
                {
                    "bucket_id": "entry_wait6579_ev_cohort",
                    "joined_sample": 18,
                    "source_quality_adjusted_ev_pct": 1.4,
                },
                {
                    "bucket_id": "entry_wait6579_ev_cohort_liquidity_high",
                    "joined_sample": 8,
                    "source_quality_adjusted_ev_pct": 1.8,
                    "child_conflict_warning": True,
                },
            ]
        },
    )
    mtd = _write(
        tmp_path / "mtd.json",
        {
            "bucket_summaries": [
                {
                    "bucket_id": "entry_wait6579_ev_cohort",
                    "joined_sample": 21,
                    "equal_weight_avg_profit_pct": 0.9,
                }
            ]
        },
    )
    scout = _write(
        tmp_path / "scout.json",
        {
            "profitable_forced_scout_examples": [
                {
                    "source_signature": "OPEN_TOP,PRICE_JUMP_START",
                    "profit_rate": 1.2,
                }
            ],
            "loss_or_flat_forced_scout_examples": [
                {
                    "source_signature": "OPEN_TOP,PRICE_JUMP_START_LOSS",
                    "profit_rate": -0.4,
                }
            ],
        },
    )
    feedback = _write(
        tmp_path / "feedback.json",
        {
            "records": [
                {
                    "source_signature": "OPEN_TOP,PRICE_JUMP_START",
                    "feedback_label": "rising_missed_initial_quality_fail",
                    "avg_down_ge2_seen": True,
                }
            ]
        },
    )

    report = mod.build_report(
        "2026-07-02",
        source_paths={
            "lifecycle_bucket_discovery_daily": daily,
            "lifecycle_bucket_discovery_rolling5d": rolling5d,
            "lifecycle_bucket_discovery_rolling10d": rolling10d,
            "lifecycle_bucket_discovery_mtd": mtd,
            "lifecycle_decision_matrix": tmp_path / "missing_ldm.json",
            "key_lineage_ledger": tmp_path / "missing_lineage.json",
            "conversion_lane": tmp_path / "missing_conversion.json",
            "rising_missed_scout_workorder": scout,
            "rising_missed_intraday_feedback": feedback,
            "missed_entry_counterfactual": tmp_path / "missing_counterfactual.json",
        },
        generated_at="fixed",
    )

    wait_prior = next(
        row
        for row in report["priors"]
        if row["observable_prefix"]["entry_source_parent"] == "entry_source_wait6579"
        and row["observable_prefix"]["liquidity_bucket"] == "-"
    )
    assert wait_prior["selected_window"] == "rolling10d"
    assert wait_prior["recommendation"] == "positive_prior"
    assert wait_prior["window_metrics"]["daily"]["joined_sample"] == 3
    assert wait_prior["window_metrics"]["rolling5d"]["joined_sample"] == 10
    assert wait_prior["window_metrics"]["rolling10d"]["joined_sample"] == 18
    assert (
        wait_prior["window_metrics"]["mtd"]["ev_metric"]
        == "equal_weight_avg_profit_pct_fallback"
    )

    conflict_prior = next(
        row
        for row in report["priors"]
        if row["observable_prefix"]["liquidity_bucket"] == "liquidity_high"
    )
    assert conflict_prior["recommendation"] == "source_quality_blocked"
    assert conflict_prior["conflict_status"]["child_conflict"] is True

    feedback_prior = next(
        row
        for row in report["priors"]
        if row["observable_prefix"]["source_signature"] == "OPEN_TOP,PRICE_JUMP_START"
    )
    assert feedback_prior["recommendation"] == "quality_risk"
    assert feedback_prior["rising_missed_metrics"]["winner_count"] == 1
    assert feedback_prior["rising_missed_metrics"]["initial_quality_fail_count"] == 1
    assert feedback_prior["rising_missed_metrics"]["avg_down_ge2_count"] == 1

    loser_prior = next(
        row
        for row in report["priors"]
        if row["observable_prefix"]["source_signature"]
        == "OPEN_TOP,PRICE_JUMP_START_LOSS"
    )
    assert loser_prior["recommendation"] == "loss_filter"
    assert (
        report["summary"]["counterfactual_status"]
        == "counterfactual_source_unavailable"
    )
    assert report["runtime_effect"] is False
    assert report["allowed_runtime_apply"] is False


def test_write_outputs_renders_prior_report(tmp_path):
    report = {
        "target_date": "2026-07-02",
        "generated_at": "fixed",
        "summary": {
            "counterfactual_status": "counterfactual_source_unavailable",
            "prior_count": 1,
            "recommendation_counts": {"positive_prior": 1},
        },
        "priors": [
            {
                "prior_key": "entry_source_parent=entry_source_wait6579",
                "recommendation": "positive_prior",
                "confidence": "high",
                "selected_window": "rolling10d",
                "reason": "rolling10d_positive_ev_prior",
            }
        ],
        "code_improvement_orders": [
            {
                "order_id": "order_rising_missed_classifier_prior_bridge",
                "runtime_effect": False,
                "allowed_runtime_apply": False,
            }
        ],
    }

    output_json = tmp_path / "prior.json"
    output_md = tmp_path / "prior.md"
    mod.write_outputs(report, output_json=output_json, output_md=output_md)

    assert (
        json.loads(output_json.read_text(encoding="utf-8"))["summary"]["prior_count"]
        == 1
    )
    markdown = output_md.read_text(encoding="utf-8")
    assert "order_rising_missed_classifier_prior_bridge" in markdown
    assert "runtime_effect: false" in markdown


def test_prior_report_ingests_missed_entry_counterfactual_when_available(tmp_path):
    counterfactual = _write(
        tmp_path / "counterfactual.json",
        {
            "rows": [
                {
                    "source_signature": "OPEN_TOP,PRICE_JUMP_START",
                    "outcome": "MISSED_WINNER",
                },
                {
                    "source_signature": "OPEN_TOP,PRICE_JUMP_START",
                    "outcome": "AVOIDED_LOSER",
                },
                {
                    "source_signature": "OPEN_TOP,PRICE_JUMP_START",
                    "outcome": "MISSED_WINNER",
                },
            ]
        },
    )

    report = mod.build_report(
        "2026-07-02",
        source_paths={
            "lifecycle_bucket_discovery_daily": tmp_path / "missing_daily.json",
            "lifecycle_bucket_discovery_rolling5d": tmp_path / "missing_rolling5d.json",
            "lifecycle_bucket_discovery_rolling10d": tmp_path
            / "missing_rolling10d.json",
            "lifecycle_bucket_discovery_mtd": tmp_path / "missing_mtd.json",
            "lifecycle_decision_matrix": tmp_path / "missing_ldm.json",
            "key_lineage_ledger": tmp_path / "missing_lineage.json",
            "conversion_lane": tmp_path / "missing_conversion.json",
            "rising_missed_scout_workorder": tmp_path / "missing_scout.json",
            "rising_missed_intraday_feedback": tmp_path / "missing_feedback.json",
            "missed_entry_counterfactual": counterfactual,
        },
        generated_at="fixed",
    )

    prior = next(
        row
        for row in report["priors"]
        if row["observable_prefix"]["source_signature"] == "OPEN_TOP,PRICE_JUMP_START"
    )
    assert report["summary"]["counterfactual_status"] == "available"
    assert report["summary"]["counterfactual_missed_winner_count"] == 2
    assert report["summary"]["counterfactual_avoided_loser_count"] == 1
    assert prior["rising_missed_metrics"]["counterfactual_missed_winner_count"] == 2
    assert prior["rising_missed_metrics"]["counterfactual_avoided_loser_count"] == 1
    assert prior["recommendation"] == "hold_sample"
    assert (
        prior["reason"] == "counterfactual_missed_winner_waiting_rolling_confirmation"
    )


def test_counterfactual_rows_do_not_double_count_top_examples(tmp_path):
    counterfactual = _write(
        tmp_path / "counterfactual.json",
        {
            "rows": [
                {
                    "candidate_id": "A",
                    "source_signature": "OPEN_TOP,PRICE_JUMP_START",
                    "outcome": "MISSED_WINNER",
                }
            ],
            "top_missed_winners": [
                {
                    "candidate_id": "A",
                    "source_signature": "OPEN_TOP,PRICE_JUMP_START",
                    "outcome": "MISSED_WINNER",
                }
            ],
        },
    )

    report = mod.build_report(
        "2026-07-02",
        source_paths={
            "lifecycle_bucket_discovery_daily": tmp_path / "missing_daily.json",
            "lifecycle_bucket_discovery_rolling5d": tmp_path / "missing_rolling5d.json",
            "lifecycle_bucket_discovery_rolling10d": tmp_path
            / "missing_rolling10d.json",
            "lifecycle_bucket_discovery_mtd": tmp_path / "missing_mtd.json",
            "lifecycle_decision_matrix": tmp_path / "missing_ldm.json",
            "key_lineage_ledger": tmp_path / "missing_lineage.json",
            "conversion_lane": tmp_path / "missing_conversion.json",
            "rising_missed_scout_workorder": tmp_path / "missing_scout.json",
            "rising_missed_intraday_feedback": tmp_path / "missing_feedback.json",
            "missed_entry_counterfactual": counterfactual,
        },
        generated_at="fixed",
    )

    assert report["summary"]["counterfactual_row_count"] == 1
    assert report["summary"]["counterfactual_missed_winner_count"] == 1
