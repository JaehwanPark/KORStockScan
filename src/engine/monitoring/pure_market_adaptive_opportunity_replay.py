"""Adaptive opportunity replay without fixed drawdown/rebound labels.

An ex-post dynamic program discovers the wealth-maximizing long-only sequence
under the configured round-trip cost.  It is an oracle benchmark and label
source only.  A separate walk-forward classifier sees completed causal market
features from prior dates and executes predictions at the next bar open.
Nothing in this module has widget, runtime, account, or order authority.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import tempfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any, Sequence
from zoneinfo import ZoneInfo

import numpy as np
from sklearn.ensemble import (
    HistGradientBoostingClassifier,
    HistGradientBoostingRegressor,
)
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import average_precision_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from src.engine.monitoring import pure_market_regime_replay as regime
from src.engine.monitoring import pure_market_reversal_replay as base
from src.trading.order.tick_utils import clamp_price_to_tick, move_price_up_by_bps

KST = ZoneInfo("Asia/Seoul")
DEFAULT_OUTPUT_DIR = Path("data/report/pure_market_adaptive_opportunity_replay")
FEATURE_NAMES = (
    "return_1m_vol_units",
    "return_3m_vol_units",
    "return_5m_vol_units",
    "return_15m_vol_units",
    "short_long_acceleration_vol_units",
    "drawdown_from_20m_high_range_units",
    "position_in_20m_range",
    "vwap_distance_vol_units",
    "volume_vs_20m_median_log",
    "bar_range_vol_units",
    "kospi_return_3m_vol_units",
    "kospi_return_15m_vol_units",
    "relative_3m_vol_units",
    "relative_15m_vol_units",
    "market_context_available",
    "session_progress",
    "session_is_regular",
)
METRIC_CONTRACT = {
    "metric_role": "adaptive_counterfactual_opportunity_research",
    "decision_authority": "offline_pure_market_adaptive_replay_only",
    "window_policy": "prior_20_qualified_dates_train_then_next_date_evaluate",
    "sample_floor": (
        f"{base.MIN_QUALIFIED_TRADING_DAYS}_coverage_qualified_trading_days_per_venue"
    ),
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "source_quality_gate": (
        "completed_unique_1m_ohlcv_and_exact_timestamp_kospi_context_for_krx"
    ),
    "forbidden_uses": [
        "oracle_action_as_live_input",
        "future_price_or_outcome_as_feature",
        "historic_widget_signal_or_ai_input",
        "automatic_runtime_or_widget_policy_apply",
        "real_order_submission",
        "account_or_quantity_decision",
        "provider_route_or_bot_control",
    ],
}
ORACLE_COST_SENSITIVITY_PCTS = (0.20, 0.40, 0.60, 1.00)
PAIRABILITY_MIN_HISTORY_DATES = 8
PAIRABILITY_MIN_CLASS_SAMPLES = 8
PAIRABILITY_SELECTION_FRACTIONS = (0.15, 0.25, 0.40, 0.60, 0.80, 1.00)
PAIRABILITY_FEATURE_NAMES = (
    *(f"armed_{name}" for name in FEATURE_NAMES),
    *(f"confirmation_{name}" for name in FEATURE_NAMES),
    "armed_buy_probability",
    "armed_sell_probability",
    "confirmation_buy_probability",
    "confirmation_sell_probability",
    "candidate_age_minutes",
    "lane_is_bullish_transition",
)
PAIRABILITY_CONTRACT = {
    "metric_role": "nested_oos_pair_completion_research",
    "decision_authority": "offline_pure_market_pairability_replay_only",
    "window_policy": (
        "base_candidate_models_use_prior_20_dates;pairability_model_uses_only_"
        "prior_base_oos_candidate_episodes"
    ),
    "sample_floor": (
        f"{base.MIN_QUALIFIED_TRADING_DAYS}_coverage_qualified_trading_days_per_venue"
    ),
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "positive_label": (
        "prior_oos_candidate_completed_adaptive_sell_transition_with_"
        "cost_adjusted_profit_gt_zero"
    ),
    "source_quality_gate": METRIC_CONTRACT["source_quality_gate"],
    "forbidden_uses": [
        "current_evaluation_date_outcome_in_model_or_selection_fraction",
        "post_exit_joint_confidence_as_entry_input",
        "same_report_threshold_selection_or_runtime_apply",
        "nxt_partial_context_as_krx_authority",
        "automatic_runtime_or_widget_policy_apply",
        "real_order_submission",
    ],
}
COMPETING_RISK_MIN_HISTORY_DATES = 8
COMPETING_RISK_MIN_EPISODES = 24
COMPETING_RISK_EVENT_LABELS = {
    "adverse_buy_transition": 0,
    "sell_transition": 1,
    "session_end_censored": 2,
}
COMPETING_RISK_CONTRACT = {
    "metric_role": "lane_specific_competing_risk_direct_ev_research",
    "decision_authority": "offline_pure_market_lane_replay_only",
    "window_policy": (
        "base_transition_models_use_prior_20_dates;lane_models_use_only_prior_"
        "base_oos_candidate_episodes;no_duration_cap"
    ),
    "sample_floor": (
        f"{base.MIN_QUALIFIED_TRADING_DAYS}_coverage_qualified_trading_days_per_venue"
    ),
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "event_contract": (
        "first_causal_base_sell_transition_vs_adverse_buy_transition_vs_"
        "session_end_censor_after_confirmed_entry"
    ),
    "selection_contract": "lane_direct_predicted_cost_adjusted_ev_gt_zero",
    "source_quality_gate": METRIC_CONTRACT["source_quality_gate"],
    "forbidden_uses": [
        "oracle_action_or_future_price_as_feature_or_exit_trigger",
        "current_evaluation_date_outcome_in_lane_model",
        "shared_weak_and_bullish_lane_model",
        "fixed_duration_cap_as_entry_or_exit_owner",
        "same_report_threshold_selection_or_runtime_apply",
        "nxt_partial_context_as_krx_authority",
        "automatic_runtime_or_widget_policy_apply",
        "real_order_submission",
    ],
}
ECONOMIC_FIRST_PASSAGE_MIN_HISTORY_DATES = 8
ECONOMIC_FIRST_PASSAGE_MIN_EPISODES = 24
ECONOMIC_TARGET_VOL_MULTIPLIERS = (0.5, 1.0, 1.5, 2.0, 3.0, 4.0)
ECONOMIC_ADVERSE_VOL_MULTIPLIERS = (0.5, 1.0, 1.5, 2.0, 3.0, 4.0)
ECONOMIC_FEATURE_NAMES = (*PAIRABILITY_FEATURE_NAMES, "causal_volatility_scale_pct")
ECONOMIC_FIRST_PASSAGE_EVENT_LABELS = {
    "favorable_first_passage": 0,
    "adverse_first_passage": 1,
    "session_end_censored": 2,
}
ECONOMIC_FIRST_PASSAGE_CONTRACT = {
    "metric_role": "lane_specific_economic_first_passage_direct_ev_research",
    "decision_authority": "offline_pure_market_lane_replay_only",
    "window_policy": (
        "base_candidate_models_use_prior_20_dates;lane_boundary_policy_and_"
        "direct_ev_models_use_only_prior_base_oos_candidate_episodes;no_"
        "fixed_holding_duration"
    ),
    "sample_floor": (
        f"{base.MIN_QUALIFIED_TRADING_DAYS}_coverage_qualified_trading_days_per_venue"
    ),
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "event_contract": (
        "candidate_specific_cost_plus_prior_volatility_favorable_boundary_vs_"
        "prior_volatility_adverse_boundary_with_lane_structural_confirmation_"
        "vs_session_end_censor"
    ),
    "adverse_confirmation_contract": (
        "weak_reversal_requires_two_consecutive_boundary_breaches;bullish_"
        "transition_requires_two_breaches_or_negative_3m_5m_and_acceleration"
    ),
    "diagnostic_thresholds": {
        "post_entry_session_mfe_ge_0_5_pct": (
            "opportunity_density_only_forbidden_as_entry_label"
        )
    },
    "selection_contract": "lane_direct_predicted_cost_adjusted_ev_gt_zero",
    "source_quality_gate": METRIC_CONTRACT["source_quality_gate"],
    "forbidden_uses": [
        "current_evaluation_date_path_in_boundary_or_lane_model",
        "oracle_action_or_future_price_as_entry_feature",
        "common_fixed_entry_or_exit_label",
        "shared_weak_and_bullish_lane_model",
        "fixed_duration_cap_as_entry_or_exit_owner",
        "same_report_boundary_selection_or_runtime_apply",
        "nxt_partial_context_as_krx_authority",
        "automatic_runtime_or_widget_policy_apply",
        "real_order_submission",
    ],
}
RECOVERY_AWARE_MIN_CHECKPOINTS = 24
RECOVERY_WAIT_MINUTES = (5, 10, 20, 40)
RECOVERY_DEEP_ADVERSE_MULTIPLIERS = (1.5, 2.0, 3.0, 4.0)
RECOVERY_TRAILING_VOL_MULTIPLIERS = (0.0, 1.0, 2.0, 3.0)
TRAILING_AWARE_MIN_CHECKPOINTS = 24
RECOVERY_FEATURE_NAMES = (
    *ECONOMIC_FEATURE_NAMES,
    "adverse_return_vol_units",
    "mfe_to_adverse_vol_units",
    "minutes_from_entry",
    "adverse_breach_streak",
    "adverse_return_3m_vol_units",
    "adverse_return_5m_vol_units",
    "adverse_acceleration_vol_units",
    "adverse_vwap_distance_vol_units",
    "adverse_position_in_20m_range",
    "adverse_volume_vs_20m_median_log",
    "adverse_session_progress",
    "distance_to_favorable_vol_units",
)
RECOVERY_AWARE_CONTRACT = {
    "metric_role": "lane_specific_recovery_aware_exit_and_profit_extension_research",
    "decision_authority": "offline_pure_market_recovery_exit_replay_only",
    "window_policy": (
        "same_entry_cohort_as_economic_first_passage;recovery_and_trailing_"
        "models_use_only_prior_base_oos_candidate_episodes"
    ),
    "sample_floor": (
        f"{base.MIN_QUALIFIED_TRADING_DAYS}_coverage_qualified_trading_days_per_venue"
    ),
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "recovery_decision_contract": (
        "defer_adverse_exit_only_when_prior_lane_model_predicts_recovery_"
        "incremental_ev_gt_zero;probability_and_time_are_diagnostics"
    ),
    "profit_extension_contract": (
        "after_favorable_first_passage_use_prior_lane_validation_trailing_"
        "multiple_or_immediate_exit"
    ),
    "source_quality_gate": METRIC_CONTRACT["source_quality_gate"],
    "forbidden_uses": [
        "current_evaluation_date_recovery_or_peak_in_model_or_policy_selection",
        "full_session_mfe_or_mae_as_entry_or_recovery_feature",
        "unbounded_adverse_guard_bypass",
        "shared_weak_and_bullish_recovery_model",
        "same_report_policy_selection_or_runtime_apply",
        "nxt_partial_context_as_krx_authority",
        "automatic_runtime_or_widget_policy_apply",
        "real_order_submission",
    ],
}
TRAILING_FEATURE_NAMES = (
    *ECONOMIC_FEATURE_NAMES,
    "favorable_return_vol_units",
    "minutes_from_entry",
    "favorable_return_3m_vol_units",
    "favorable_return_5m_vol_units",
    "favorable_acceleration_vol_units",
    "favorable_vwap_distance_vol_units",
    "favorable_position_in_20m_range",
    "favorable_volume_vs_20m_median_log",
    "favorable_session_progress",
    "favorable_after_adverse_checkpoint",
)
RECOVERY_TRAILING_AXIS_CONTRACT = {
    "metric_role": "recovery_and_favorable_trailing_axis_separation_research",
    "decision_authority": "offline_pure_market_exit_axis_replay_only",
    "window_policy": (
        "same_economic_selected_entry_cohort;recovery_only_and_trailing_"
        "incremental_ev_models_use_only_prior_base_oos_candidates"
    ),
    "sample_floor": (
        f"{base.MIN_QUALIFIED_TRADING_DAYS}_coverage_qualified_trading_days_per_venue"
    ),
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "arm_contract": [
        "baseline",
        "recovery_only",
        "trailing_only",
        "recovery_plus_trailing",
    ],
    "recovery_contract": (
        "recovery_training_labels_and_policy_forbid_trailing_outcomes;defer_"
        "only_when_predicted_incremental_ev_gt_zero"
    ),
    "trailing_contract": (
        "apply_prior_selected_trailing_multiple_only_when_separate_favorable_"
        "checkpoint_model_predicts_incremental_ev_gt_zero"
    ),
    "source_quality_gate": METRIC_CONTRACT["source_quality_gate"],
    "forbidden_uses": [
        "current_evaluation_date_outcome_in_model_or_policy_selection",
        "full_session_mfe_or_mae_as_entry_recovery_or_trailing_feature",
        "same_report_lane_on_off_or_threshold_selection",
        "different_entry_cohort_between_arms",
        "unbounded_adverse_guard_bypass",
        "nxt_partial_context_as_krx_authority",
        "automatic_runtime_or_widget_policy_apply",
        "real_order_submission",
    ],
}
RECOVERY_ENTRY_UTILITY_MIN_HISTORY_DATES = 8
RECOVERY_ENTRY_UTILITY_MIN_EPISODES = 24
RECOVERY_ENTRY_UTILITY_FEATURE_NAMES = ECONOMIC_FEATURE_NAMES
RECOVERY_ENTRY_UTILITY_CONTRACT = {
    "metric_role": "recovery_only_outcome_direct_entry_utility_research",
    "decision_authority": "offline_pure_market_recovery_entry_replay_only",
    "window_policy": (
        "recovery_exit_models_use_only_prior_base_oos_candidates;entry_utility_"
        "model_uses_only_earlier_dates_already_evaluated_out_of_sample_under_"
        "their_then_prior_recovery_only_policy"
    ),
    "sample_floor": (
        f"{base.MIN_QUALIFIED_TRADING_DAYS}_coverage_qualified_trading_days_per_venue"
    ),
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "selection_contract": (
        "lane_direct_predicted_recovery_only_cost_adjusted_ev_gt_zero"
    ),
    "control_contract": (
        "existing_economic_entry_selector_and_recovery_aware_selector_share_"
        "the_same_oos_recovery_only_exit_policy_on_model_ready_dates"
    ),
    "source_quality_gate": METRIC_CONTRACT["source_quality_gate"],
    "forbidden_uses": [
        "current_evaluation_date_recovery_outcome_in_entry_model",
        "current_axis_result_as_same_report_threshold_or_lane_switch",
        "trailing_outcome_as_recovery_entry_label",
        "full_session_mfe_or_mae_as_entry_feature",
        "shared_weak_and_bullish_entry_model",
        "nxt_partial_context_as_krx_authority",
        "automatic_runtime_or_widget_policy_apply",
        "real_order_submission",
    ],
}
RECOVERY_ENTRY_CALIBRATION_MIN_HISTORY_DATES = 4
RECOVERY_ENTRY_CALIBRATION_MIN_EPISODES = 24
RECOVERY_ENTRY_CALIBRATION_RECENT_DATES = 3
RECOVERY_ENTRY_CALIBRATION_OPPORTUNITY_RETENTION = 0.75
RECOVERY_ENTRY_CALIBRATION_CONTRACT = {
    "metric_role": "prior_only_recovery_entry_calibration_and_capacity_research",
    "decision_authority": "offline_pure_market_recovery_entry_calibration_only",
    "window_policy": (
        "calibrator_uses_only_earlier_recovery_entry_predictions_already_"
        "evaluated_out_of_sample;current_date_is_appended_after_evaluation"
    ),
    "sample_floor": (
        f"{base.MIN_QUALIFIED_TRADING_DAYS}_coverage_qualified_trading_days_per_venue"
    ),
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "calibration_contract": (
        "lane_specific_reliability_shrunk_linear_mean_utility_with_prior_only_"
        "recent_residual_drift;positive_calibrated_mean_ev_is_primary_but_"
        "date_level_raw_recovery_capacity_fallback_prevents_sample_collapse"
    ),
    "capacity_contract": (
        "economic_control_raw_recovery_selector_and_calibrated_selector_share_"
        "the_same_model_ready_dates_and_recovery_only_exit_policy;rejected_"
        "candidates_do_not_consume_capacity"
    ),
    "pareto_contract": (
        "ev_compounded_return_and_pre_exit_mae_not_worse_than_both_controls_"
        f"with_at_least_{RECOVERY_ENTRY_CALIBRATION_OPPORTUNITY_RETENTION:.2f}_"
        "of_raw_recovery_nonoverlap_opportunities"
    ),
    "diagnostic_contract": (
        "prediction_bins_date_drift_and_capacity_loss_are_post_oos_"
        "diagnostics_forbidden_as_same_report_policy_inputs"
    ),
    "source_quality_gate": METRIC_CONTRACT["source_quality_gate"],
    "forbidden_uses": [
        "current_evaluation_date_residual_in_same_date_calibrator",
        "same_report_lane_outcome_as_lane_on_off_switch",
        "positive_lower_confidence_bound_only_zero_sample_gate",
        "trailing_outcome_as_calibration_label",
        "full_session_mfe_or_mae_as_calibration_feature",
        "post_oos_prediction_bin_as_same_report_threshold",
        "nxt_partial_context_as_krx_authority",
        "automatic_runtime_or_widget_policy_apply",
        "real_order_submission",
    ],
}
RECOVERY_ENTRY_TIMING_MIN_HISTORY_DATES = 4
RECOVERY_ENTRY_TIMING_MIN_CONTROL_EPISODES = 12
RECOVERY_ENTRY_TIMING_MAX_WAIT_MINUTES = (3, 5, 10, 20)
RECOVERY_ENTRY_TIMING_OPPORTUNITY_RETENTION = 0.75
RECOVERY_ENTRY_TIMING_ARMS = (
    "confirmation_continuation",
    "first_non_chasing_pullback",
    "vwap_reclaim_hold",
)
RECOVERY_ENTRY_TIMING_CONTRACT = {
    "metric_role": "prior_only_recovery_entry_timing_research",
    "decision_authority": "offline_pure_market_recovery_entry_timing_only",
    "window_policy": (
        "each_timing_arm_outcome_is_generated_on_its_evaluation_date_with_"
        "then_prior_recovery_models;later_policy_selection_uses_only_those_"
        "earlier_oos_arm_outcomes"
    ),
    "sample_floor": (
        f"{base.MIN_QUALIFIED_TRADING_DAYS}_coverage_qualified_trading_days_per_venue"
    ),
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "entry_arms": list(RECOVERY_ENTRY_TIMING_ARMS),
    "control_contract": (
        "raw_recovery_entry_selector_next_open_control_and_all_timing_arms_"
        "share_the_same_recovery_only_exit_owner"
    ),
    "capacity_contract": (
        f"date_level_control_fallback_preserves_at_least_"
        f"{RECOVERY_ENTRY_TIMING_OPPORTUNITY_RETENTION:.2f}_of_raw_selector_"
        "nonoverlap_opportunities"
    ),
    "source_quality_gate": METRIC_CONTRACT["source_quality_gate"],
    "forbidden_uses": [
        "current_evaluation_date_outcome_in_timing_policy_selection",
        "future_bar_beyond_first_causal_trigger_as_entry_feature",
        "same_report_arm_or_wait_selection",
        "fixed_profit_label_as_entry_timing_target",
        "different_exit_owner_between_control_and_timing_arm",
        "nxt_partial_context_as_krx_authority",
        "automatic_runtime_or_widget_policy_apply",
        "real_order_submission",
    ],
}
RECOVERY_ENTRY_TIMING_UTILITY_MIN_HISTORY_DATES = 4
RECOVERY_ENTRY_TIMING_UTILITY_MIN_PAIRS = 16
RECOVERY_ENTRY_TIMING_UTILITY_MIN_TRIGGER_PAIRS = 8
RECOVERY_ENTRY_TIMING_UTILITY_OPPORTUNITY_RETENTION = 0.75
RECOVERY_ENTRY_TIMING_UTILITY_BASE_FEATURE_NAMES = (
    *ECONOMIC_FEATURE_NAMES,
    *(f"timing_arm_{arm}" for arm in RECOVERY_ENTRY_TIMING_ARMS),
    "timing_max_wait_fraction_of_20m",
)
RECOVERY_ENTRY_TIMING_UTILITY_TRIGGER_FEATURE_NAMES = (
    *RECOVERY_ENTRY_TIMING_UTILITY_BASE_FEATURE_NAMES,
    *(f"trigger_confirmation_{name}" for name in FEATURE_NAMES),
    "trigger_buy_probability",
    "trigger_sell_probability",
    "trigger_volatility_scale_pct",
    "trigger_delay_fraction_of_20m",
)
RECOVERY_ENTRY_TIMING_UTILITY_CONTRACT = {
    "metric_role": "candidate_level_recovery_entry_timing_incremental_utility",
    "decision_authority": "offline_pure_market_candidate_timing_replay_only",
    "window_policy": (
        "baseline_wait_model_and_trigger_entry_model_use_only_earlier_pairs_"
        "whose_control_and_timing_outcomes_were_already_generated_oos_with_"
        "then_prior_timing_and_recovery_policies"
    ),
    "sample_floor": (
        f"{base.MIN_QUALIFIED_TRADING_DAYS}_coverage_qualified_trading_days_per_venue"
    ),
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "baseline_decision_contract": (
        "enter_now_or_wait_uses_only_baseline_features_and_prior_selected_arm;"
        "one_wait_is_allowed_only_after_three_enter_now_decisions_with_lane_"
        "budget_carried_across_evaluation_dates"
    ),
    "trigger_decision_contract": (
        "after_wait_only_the_observed_completed_trigger_context_may_choose_"
        "timed_entry_or_skip;no_return_to_past_next_open"
    ),
    "capacity_contract": (
        f"oos_result_must_retain_at_least_"
        f"{RECOVERY_ENTRY_TIMING_UTILITY_OPPORTUNITY_RETENTION:.2f}_of_raw_"
        "recovery_nonoverlap_opportunities_or_cannot_improve"
    ),
    "source_quality_gate": METRIC_CONTRACT["source_quality_gate"],
    "forbidden_uses": [
        "trigger_context_in_baseline_enter_now_or_wait_decision",
        "current_evaluation_date_pair_in_same_date_utility_model",
        "missing_trigger_as_retroactive_raw_next_open_fallback",
        "future_mfe_or_mae_as_utility_feature_or_label",
        "same_report_lane_threshold_or_wait_policy_change",
        "nxt_partial_context_as_krx_authority",
        "automatic_runtime_or_widget_policy_apply",
        "real_order_submission",
    ],
}
TRIGGER_UTILITY_CALIBRATION_MIN_HISTORY_DATES = 1
TRIGGER_UTILITY_CALIBRATION_MIN_PAIRS = 3
TRIGGER_UTILITY_CALIBRATION_SHRINKAGE_PRIOR = 8.0
TRIGGER_UTILITY_CALIBRATION_OPPORTUNITY_RETENTION = 0.75
TRIGGER_UTILITY_CALIBRATION_CONTRACT = {
    "metric_role": "prior_only_timing_trigger_utility_calibration",
    "decision_authority": "offline_pure_market_trigger_calibration_replay_only",
    "window_policy": (
        "each_trigger_prediction_is_generated_oos_on_its_label_date;lane_"
        "calibration_uses_only_predictions_and_residuals_from_earlier_dates"
    ),
    "sample_floor": (
        f"{base.MIN_QUALIFIED_TRADING_DAYS}_coverage_qualified_trading_days_per_venue;"
        f"calibration_starts_at_{TRIGGER_UTILITY_CALIBRATION_MIN_HISTORY_DATES}_prior_"
        f"date_and_{TRIGGER_UTILITY_CALIBRATION_MIN_PAIRS}_trigger_pairs"
    ),
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "calibration_contract": (
        "lane_affine_rank_slope_and_residual_drift_are_shrunk_toward_raw_"
        "prediction_and_zero_adjustment_without_current_date_outcomes"
    ),
    "bounded_exploration_contract": (
        "three_trigger_entries_earn_at_most_one_model_skip_with_lane_budget_"
        "carried_across_dates;therefore_at_least_0.75_of_observed_wait_"
        "triggers_are_entered_before_final_cross_lane_retention_judgment"
    ),
    "source_quality_gate": METRIC_CONTRACT["source_quality_gate"],
    "forbidden_uses": [
        "current_date_trigger_outcome_in_same_date_calibration",
        "future_mfe_or_mae_as_trigger_feature_or_label",
        "missing_trigger_as_retroactive_raw_next_open_fallback",
        "calibration_result_as_same_report_lane_off_switch",
        "different_baseline_wait_or_exit_owner_between_comparison_arms",
        "nxt_partial_context_as_krx_authority",
        "automatic_runtime_or_widget_policy_apply",
        "real_order_submission",
    ],
}
WAIT_BUDGET_ARMS = {
    "enter3_wait1": 3,
    "enter2_wait1": 2,
    "enter1_wait1": 1,
}
WAIT_BUDGET_OPPORTUNITY_RETENTION = 0.75
WAIT_BUDGET_CONTRACT = {
    "metric_role": "candidate_timing_wait_budget_prior_only_comparison",
    "decision_authority": "offline_pure_market_wait_budget_replay_only",
    "window_policy": (
        "each_budget_arm_is_scored_oos_with_models_and_trigger_calibration_"
        "fitted_before_the_evaluation_date;an_executable_selected_arm_may_use_"
        "only_complete_arm_outcomes_from_earlier_evaluation_dates"
    ),
    "sample_floor": (
        f"{base.MIN_QUALIFIED_TRADING_DAYS}_coverage_qualified_trading_days_per_venue;"
        "no_additional_minimum_selected_policy_dates"
    ),
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "arm_contract": (
        "compare_enter3_wait1_enter2_wait1_enter1_wait1_with_identical_"
        "calibrated_trigger_bounded_exploration_and_recovery_only_exit_owner"
    ),
    "capacity_contract": (
        f"each_arm_must_retain_at_least_{WAIT_BUDGET_OPPORTUNITY_RETENTION:.2f}_"
        "of_control_nonoverlap_opportunities_and_observed_trigger_entries"
    ),
    "source_quality_gate": METRIC_CONTRACT["source_quality_gate"],
    "forbidden_uses": [
        "current_date_arm_outcome_as_same_date_budget_selection",
        "future_mfe_or_mae_as_wait_budget_feature_or_label",
        "missing_trigger_as_retroactive_raw_next_open_fallback",
        "different_trigger_calibration_or_exit_owner_between_budget_arms",
        "opportunity_retention_below_0_75",
        "nxt_partial_context_as_krx_authority",
        "automatic_runtime_or_widget_policy_apply",
        "real_order_submission",
    ],
}
FIXED_TP_SPLIT_ARMS: dict[str, dict[str, Any]] = {
    "single_tp0p5": {
        "legs": ((0.0, 1.0),),
        "target_pct": 0.5,
    },
    "two_40_60_add0p5_tp0p4": {
        "legs": ((0.0, 0.4), (-0.5, 0.6)),
        "target_pct": 0.4,
    },
    "two_40_60_add0p5_tp0p5": {
        "legs": ((0.0, 0.4), (-0.5, 0.6)),
        "target_pct": 0.5,
    },
    "two_40_60_add0p8_tp0p5": {
        "legs": ((0.0, 0.4), (-0.8, 0.6)),
        "target_pct": 0.5,
    },
    "three_20_30_50_add0p4_0p8_tp0p5": {
        "legs": ((0.0, 0.2), (-0.4, 0.3), (-0.8, 0.5)),
        "target_pct": 0.5,
    },
    "three_20_30_50_add0p5_1p0_tp0p5": {
        "legs": ((0.0, 0.2), (-0.5, 0.3), (-1.0, 0.5)),
        "target_pct": 0.5,
    },
}
FIXED_TP_SPLIT_CONTROL_ARM = "single_tp0p5"
FIXED_TP_SPLIT_CATASTROPHIC_STOP_PCT = 2.0
FIXED_TP_EQUAL_SHARE_CARRY_ARMS: dict[str, dict[str, Any]] = {
    "single_1_tp0p4": {"add_offsets_pct": (0.0,), "target_pct": 0.4},
    "single_1_tp0p5": {"add_offsets_pct": (0.0,), "target_pct": 0.5},
    "two_equal_add0p5_tp0p4": {
        "add_offsets_pct": (0.0, -0.5),
        "target_pct": 0.4,
    },
    "two_equal_add0p5_tp0p5": {
        "add_offsets_pct": (0.0, -0.5),
        "target_pct": 0.5,
    },
    "two_equal_add0p8_tp0p5": {
        "add_offsets_pct": (0.0, -0.8),
        "target_pct": 0.5,
    },
    "three_equal_add0p4_0p8_tp0p5": {
        "add_offsets_pct": (0.0, -0.4, -0.8),
        "target_pct": 0.5,
    },
    "three_equal_add0p5_1p0_tp0p5": {
        "add_offsets_pct": (0.0, -0.5, -1.0),
        "target_pct": 0.5,
    },
}
FIXED_TP_CARRY_HOLDOUT_DATES = 6
FIXED_TP_CARRY_MIN_CALIBRATION_ENTRIES = 20
FIXED_TP_CARRY_MIN_HOLDOUT_COMPLETIONS = 10
FIXED_TP_EQUAL_SHARE_CARRY_CONTRACT = {
    "metric_role": "one_share_leg_carry_to_fixed_average_target_research",
    "decision_authority": "offline_widget_auto_trade_policy_candidate_only",
    "window_policy": (
        "economic_oos_entries_only;first_evaluation_dates_calibrate_with_prices_"
        "strictly_before_holdout_start;last_6_evaluation_dates_are_untouched_"
        "holdout;runtime_candidate_target_observation_ends_at_trade_date_reset"
    ),
    "sample_floor": (
        f"{base.MIN_QUALIFIED_TRADING_DAYS}_coverage_qualified_days;"
        f"{FIXED_TP_CARRY_MIN_CALIBRATION_ENTRIES}_calibration_entries;"
        f"{FIXED_TP_CARRY_MIN_HOLDOUT_COMPLETIONS}_completed_holdout_entries"
    ),
    "primary_decision_metric": "holdout_completed_trade_count_then_time_and_mae",
    "source_quality_gate": METRIC_CONTRACT["source_quality_gate"],
    "execution_contract": (
        "each_leg_is_one_share;additional_legs_may_fill_only_in_the_original_"
        "entry_session;target_is_tick_rounded_from_equal_share_weighted_average;"
        "target_activates_on_the_bar_after_a_fill;no_ordinary_or_catastrophic_"
        "stop;runtime_candidate_allows_one_active_bundle_per_symbol_and_resets_"
        "at_each_trade_date;unhit_positions_are_right_censored_not_forced_losses"
    ),
    "forbidden_uses": [
        "holdout_outcome_as_calibration_arm_selection",
        "future_bar_as_entry_or_add_trigger_input",
        "same_bar_target_after_initial_or_add_fill",
        "right_censored_position_as_zero_return_or_completed_profit",
        "nxt_partial_context_as_krx_authority",
        "automatic_runtime_or_widget_policy_apply",
        "real_order_submission",
        "provider_or_main_bot_control",
    ],
}
FIXED_TP_SPLIT_CONTRACT = {
    "metric_role": "fixed_entry_cohort_split_buy_fixed_take_profit_comparison",
    "decision_authority": "offline_pure_market_execution_replay_only",
    "window_policy": (
        "economic_first_passage_selected_entries_are_held_fixed;each_evaluation_"
        "date_arm_is_selected_only_from_complete_arm_outcomes_on_earlier_dates"
    ),
    "sample_floor": (
        f"{base.MIN_QUALIFIED_TRADING_DAYS}_coverage_qualified_trading_days_per_venue;"
        "prior_arm_selection_starts_after_one_complete_evaluation_date"
    ),
    "primary_decision_metric": "source_quality_adjusted_ev_pct_on_planned_budget",
    "execution_contract": (
        "capital_fraction_legs_fill_at_limit_or_better;target_is_repriced_from_"
        "weighted_average_and_rounded_up_to_a_valid_tick_after_each_fill_then_"
        "activates_on_the_next_bar;ordinary_adverse_first_has_no_stop;all_arms_"
        "share_initial_entry_minus_2pct_tick_clamped_catastrophic_stop_and_"
        "session_close_liquidation"
    ),
    "same_bar_path_policy": (
        "crossed_add_limits_fill_before_catastrophic_stop_on_the_same_down_bar;"
        "any_add_fill_suppresses_target_on_that_bar;target_fill_uses_valid_tick_"
        "limit_price_without_favorable_gap_improvement"
    ),
    "capital_contract": (
        "primary_return_uses_full_planned_budget;deployed_notional_return_is_"
        "diagnostic_so_unfilled_reserve_cash_is_not_mistaken_for_free_leverage"
    ),
    "artifact_storage_contract": (
        "evaluation_rows_keep_policy_and_trade_counts;full_arm_trade_arrays_are_"
        "omitted_from_the_written_report_because_source_bars_can_replay_them"
    ),
    "source_quality_gate": METRIC_CONTRACT["source_quality_gate"],
    "forbidden_uses": [
        "current_date_arm_outcome_as_same_date_arm_selection",
        "future_bar_as_entry_or_scale_in_feature",
        "historic_widget_signal_or_ai_decision_input",
        "different_entry_cohort_between_arms",
        "same_bar_target_after_initial_or_scale_in_fill",
        "nxt_partial_context_as_krx_authority",
        "automatic_runtime_or_widget_policy_apply",
        "real_order_submission",
        "account_or_quantity_decision",
    ],
}
FIXED_TP_ENTRY_QUALITY_EXECUTION_ARM = "two_40_60_add0p8_tp0p5"
FIXED_TP_ENTRY_QUALITY_OPPORTUNITY_RETENTION = 0.75
FIXED_TP_ENTRY_QUALITY_SHRINKAGE_PRIOR = 8.0
FIXED_TP_ENTRY_QUALITY_FEATURE_NAMES = (
    *ECONOMIC_FEATURE_NAMES,
    "economic_predicted_cost_adjusted_ev_pct",
    "economic_predicted_favorable_probability",
    "economic_predicted_adverse_probability",
    "economic_predicted_censor_probability",
)
FIXED_TP_ENTRY_QUALITY_CONTRACT = {
    "metric_role": "fixed_execution_entry_catastrophic_loss_quality_research",
    "decision_authority": "offline_pure_market_entry_quality_replay_only",
    "window_policy": (
        "the_40_60_add0p8_average_tp0p5_execution_arm_is_fixed;each_entry_"
        "quality_model_uses_all_fixed_arm_counterfactual_outcomes_from_earlier_"
        "evaluation_dates_only"
    ),
    "sample_floor": (
        f"{base.MIN_QUALIFIED_TRADING_DAYS}_coverage_qualified_trading_days_per_venue;"
        "no_additional_date_floor;model_starts_after_both_catastrophic_and_"
        "noncatastrophic_prior_outcomes_exist"
    ),
    "primary_decision_metric": "source_quality_adjusted_ev_pct_on_planned_budget",
    "selection_contract": (
        "reliability_shrunk_catastrophic_probability_is_combined_with_prior_"
        "catastrophic_and_noncatastrophic_planned_budget_returns_to_estimate_"
        "net_ev;there_is_no_probability_threshold_or_hard_gate"
    ),
    "bounded_exploration_contract": (
        "three_prior_entries_on_the_same_evaluation_date_earn_at_most_one_"
        f"subsequent_negative_ev_skip_so_every_observed_prefix_and_cumulative_"
        f"entry_retention_remain_at_least_"
        f"{FIXED_TP_ENTRY_QUALITY_OPPORTUNITY_RETENTION:.2f};otherwise_the_entry_"
        "is_observed_as_bounded_exploration_without_future_candidate_count"
    ),
    "artifact_storage_contract": (
        "evaluation_rows_keep_model_capacity_and_compact_decision_provenance;"
        "full_control_and_selected_trade_arrays_are_omitted_from_the_written_"
        "report_because_source_bars_can_replay_them"
    ),
    "source_quality_gate": METRIC_CONTRACT["source_quality_gate"],
    "forbidden_uses": [
        "current_date_outcome_as_same_date_entry_quality_input",
        "future_mfe_mae_low_high_or_exit_as_entry_feature",
        "catastrophic_probability_as_hard_gate",
        "opportunity_retention_below_0_75",
        "split_take_profit_or_catastrophic_stop_owner_change",
        "historic_widget_signal_or_ai_decision_input",
        "nxt_partial_context_as_krx_authority",
        "automatic_runtime_or_widget_policy_apply",
        "real_order_submission",
        "account_or_quantity_decision",
    ],
}
RECOVERABLE_BASIN_EXECUTION_ARM = FIXED_TP_ENTRY_QUALITY_EXECUTION_ARM
RECOVERABLE_BASIN_OPPORTUNITY_RETENTION = 0.75
RECOVERABLE_BASIN_SHRINKAGE_PRIOR = 16.0
RECOVERABLE_BASIN_FEATURE_NAMES = (
    *FIXED_TP_ENTRY_QUALITY_FEATURE_NAMES,
    "fixed_add_distance_vol_units",
    "fixed_target_distance_vol_units",
    "fixed_catastrophic_distance_vol_units",
)
RECOVERABLE_BASIN_CONTRACT = {
    "metric_role": "broader_causal_candidate_recoverable_basin_direct_ev_research",
    "decision_authority": "offline_pure_market_recoverable_basin_replay_only",
    "window_policy": (
        "all_causal_armed_candidates_from_model_ready_economic_lanes_are_replayed_"
        "with_one_fixed_execution_owner;each_date_direct_ev_model_uses_only_"
        "independent_fixed_arm_counterfactuals_from_earlier_dates"
    ),
    "sample_floor": (
        f"{base.MIN_QUALIFIED_TRADING_DAYS}_coverage_qualified_trading_days_per_venue;"
        "no_additional_date_or_trade_floor;direct_ev_fit_starts_after_one_prior_"
        "candidate_date"
    ),
    "primary_decision_metric": "source_quality_adjusted_ev_pct_on_planned_budget",
    "selection_contract": (
        "regularized_direct_fixed_execution_net_ev_with_prior_mean_shrinkage;"
        "positive_ev_enters_and_negative_ev_remains_bounded_exploration_without_"
        "a_probability_or_score_hard_gate"
    ),
    "state_machine_contract": (
        "candidate_timestamps_are_evaluated_in_order;an_entered_candidate_owns_"
        "the_position_until_its_fixed_execution_exit;skipped_candidates_do_not_"
        "occupy_the_slot_and_the_next_candidate_is_reconsidered"
    ),
    "bounded_exploration_contract": (
        "three_prior_entries_in_the_same_date_and_session_earn_at_most_one_"
        f"subsequent_negative_ev_skip;every_prefix_retains_at_least_"
        f"{RECOVERABLE_BASIN_OPPORTUNITY_RETENTION:.2f}_without_using_future_"
        "candidate_count"
    ),
    "artifact_storage_contract": (
        "evaluation_rows_keep_model_capacity_and_compact_decision_provenance;"
        "full_counterfactual_trade_arrays_are_omitted_because_they_duplicate_"
        "the_replayable_source_bars_and_aggregate_path_summaries"
    ),
    "source_quality_gate": METRIC_CONTRACT["source_quality_gate"],
    "forbidden_uses": [
        "current_date_outcome_as_same_date_model_or_policy_input",
        "future_mfe_mae_session_low_high_or_exit_as_entry_feature",
        "future_candidate_count_as_skip_budget_input",
        "fixed_drawdown_or_rebound_entry_label",
        "opportunity_retention_below_0_75",
        "split_take_profit_or_catastrophic_stop_owner_change",
        "same_report_prediction_diagnostic_as_threshold_selection",
        "historic_widget_signal_or_ai_decision_input",
        "nxt_partial_context_as_krx_authority",
        "automatic_runtime_or_widget_policy_apply",
        "real_order_submission",
        "account_or_quantity_decision",
    ],
}
PARENT_BUCKET_EXECUTION_ARM = RECOVERABLE_BASIN_EXECUTION_ARM
PARENT_BUCKET_OPPORTUNITY_RETENTION = 0.75
PARENT_BUCKET_SHRINKAGE_PRIOR = 12.0
PARENT_BUCKET_AXIS_SPECS: dict[str, dict[str, str]] = {
    "lane_parent": {
        "kind": "categorical",
        "source": "pairability_lane",
    },
    "session_time_parent": {
        "kind": "numeric_tercile",
        "source": "confirmation_session_progress",
    },
    "volatility_parent": {
        "kind": "numeric_tercile",
        "source": "causal_volatility_scale_pct",
    },
    "relative_strength_parent": {
        "kind": "numeric_tercile",
        "source": "confirmation_relative_3m_vol_units",
    },
    "vwap_position_parent": {
        "kind": "numeric_tercile",
        "source": "confirmation_vwap_distance_vol_units",
    },
    "range_position_parent": {
        "kind": "numeric_tercile",
        "source": "confirmation_position_in_20m_range",
    },
}
PARENT_BUCKET_CONTRACT = {
    "metric_role": "coarse_parent_archetype_fixed_execution_attribution_research",
    "decision_authority": "offline_pure_market_parent_bucket_replay_only",
    "window_policy": (
        "each_numeric_parent_uses_tercile_boundaries_from_earlier_candidate_"
        "dates_only;each_bucket_ev_and_each_date_axis_choice_use_only_prior_"
        "fixed_execution_outcomes"
    ),
    "sample_floor": (
        f"{base.MIN_QUALIFIED_TRADING_DAYS}_coverage_qualified_trading_days_per_venue;"
        "no_additional_date_floor;parent_bucket_fit_starts_after_one_prior_"
        "candidate_date_and_axis_choice_starts_after_one_prior_oos_axis_date"
    ),
    "primary_decision_metric": "source_quality_adjusted_ev_pct_on_planned_budget",
    "bucket_contract": (
        "lane_session_time_volatility_relative_strength_vwap_position_and_"
        "range_position_are_evaluated_one_axis_at_a_time;no_child_feature_combo_"
        "owns_a_decision"
    ),
    "selection_contract": (
        "bucket_mean_fixed_execution_ev_is_shrunk_to_the_prior_global_mean;"
        "the_axis_used_on_an_evaluation_date_is_selected_by_prior_axis_ev_then_"
        "prior_compounded_return_then_less_adverse_mae"
    ),
    "bounded_exploration_contract": (
        "three_prior_entries_in_the_same_date_and_session_earn_at_most_one_"
        f"subsequent_negative_parent_ev_skip;every_prefix_retains_at_least_"
        f"{PARENT_BUCKET_OPPORTUNITY_RETENTION:.2f}_without_future_candidate_count"
    ),
    "artifact_storage_contract": (
        "evaluation_rows_keep_prior_boundaries_bucket_statistics_capacity_and_"
        "the_prior_selected_axis_decisions;full_counterfactual_trade_arrays_are_"
        "omitted_as_replayable_source_bar_detail"
    ),
    "source_quality_gate": METRIC_CONTRACT["source_quality_gate"],
    "forbidden_uses": [
        "current_date_outcome_as_same_date_boundary_bucket_or_axis_input",
        "future_mfe_mae_session_low_high_or_exit_as_entry_feature",
        "multi_axis_child_combo_as_parent_bucket_authority",
        "same_report_axis_summary_as_same_date_axis_selection",
        "future_candidate_count_as_skip_budget_input",
        "opportunity_retention_below_0_75",
        "split_take_profit_or_catastrophic_stop_owner_change",
        "historic_widget_signal_or_ai_decision_input",
        "nxt_partial_context_as_krx_authority",
        "automatic_runtime_or_widget_policy_apply",
        "real_order_submission",
        "account_or_quantity_decision",
    ],
}
PARENT_BUCKET_STABILITY_FOCUS_AXIS = "volatility_parent"
PARENT_BUCKET_STABILITY_FOCUS_BUCKET = "middle"
PARENT_BUCKET_STABILITY_ROLLING_DATES = 3
PARENT_BUCKET_STABILITY_CONTRACT = {
    "metric_role": "fixed_parent_oos_date_stability_and_loss_concentration_research",
    "decision_authority": "offline_post_oos_parent_attribution_only",
    "window_policy": (
        "consume_the_unchanged_prior_selected_parent_axis_decisions_from_the_"
        "same_report;group_by_observed_trade_date_without_refitting_boundaries_"
        "buckets_axes_or_entry_actions"
    ),
    "sample_floor": (
        f"{base.MIN_QUALIFIED_TRADING_DAYS}_coverage_qualified_trading_days_per_venue;"
        "no_new_floor;stability_is_reported_for_every_observed_parent_bucket_"
        "and_the_predeclared_volatility_middle_focus"
    ),
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "stability_contract": (
        "report_date_level_ev_three_observed_date_rolling_sign_persistence_"
        "leave_one_date_ev_sensitivity_and_catastrophic_loss_concentration"
    ),
    "focus_contract": (
        "volatility_parent_middle_is_a_predeclared_diagnostic_focus_from_v16_"
        "and_cannot_be_promoted_or_reselected_on_the_same_46_date_sample"
    ),
    "source_quality_gate": METRIC_CONTRACT["source_quality_gate"],
    "forbidden_uses": [
        "same_sample_parent_bucket_or_threshold_reselection",
        "volatility_middle_as_a_same_sample_hard_entry_gate",
        "multi_axis_child_combo_creation",
        "current_date_outcome_as_same_date_entry_input",
        "post_oos_leave_one_date_or_rolling_metric_as_runtime_authority",
        "nxt_partial_context_as_krx_authority",
        "automatic_runtime_or_widget_policy_apply",
        "real_order_submission",
        "account_or_quantity_decision",
    ],
}
PARENT_CATASTROPHIC_AUDIT_MIN_TARGET_COMPARATOR = 20
PARENT_CATASTROPHIC_AUDIT_PAIRWISE_FLOOR = 0.75
PARENT_CATASTROPHIC_AUDIT_LEAVE_ONE_FLOOR = 0.70
PARENT_CATASTROPHIC_AUDIT_TARGET_RETENTION_FLOOR = 0.75
PARENT_CATASTROPHIC_AUDIT_FEATURE_NAMES = (
    "confirmation_return_1m_vol_units",
    "confirmation_return_3m_vol_units",
    "confirmation_return_5m_vol_units",
    "confirmation_short_long_acceleration_vol_units",
    "confirmation_drawdown_from_20m_high_range_units",
    "confirmation_position_in_20m_range",
    "confirmation_vwap_distance_vol_units",
    "confirmation_volume_vs_20m_median_log",
    "confirmation_bar_range_vol_units",
    "confirmation_kospi_return_3m_vol_units",
    "confirmation_relative_3m_vol_units",
    "confirmation_market_context_available",
    "confirmation_session_progress",
    "candidate_age_minutes",
    "causal_volatility_scale_pct",
    "pre_entry_return_1m_pct",
    "pre_entry_return_3m_pct",
    "pre_entry_return_5m_pct",
    "pre_entry_return_10m_pct",
    "pre_entry_negative_step_count_5",
    "pre_entry_down_volume_share_5",
)
PARENT_CATASTROPHIC_AUDIT_COMPARISON_FEATURE_NAMES = tuple(
    name
    for name in PARENT_CATASTROPHIC_AUDIT_FEATURE_NAMES
    if name != "confirmation_market_context_available"
)
PARENT_CATASTROPHIC_AUDIT_CONTRACT = {
    "metric_role": "fixed_parent_catastrophic_pre_entry_episode_audit",
    "decision_authority": "offline_post_oos_loss_signature_research_only",
    "window_policy": (
        "consume_the_unchanged_volatility_middle_enter_decisions_and_join_each_"
        "identity_to_its_original_causal_candidate_and_completed_pre_entry_bars"
    ),
    "sample_floor": (
        f"{base.MIN_QUALIFIED_TRADING_DAYS}_coverage_qualified_trading_days_per_venue;"
        f"all_observed_catastrophic_episodes_and_at_least_"
        f"{PARENT_CATASTROPHIC_AUDIT_MIN_TARGET_COMPARATOR}_fixed_target_comparators"
    ),
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "comparison_contract": (
        "catastrophic_stop_vs_fixed_average_take_profit_outcomes_are_compared_"
        "one_pre_entry_dimension_at_a_time;session_close_is_reported_but_is_not_"
        "a_primary_comparator"
    ),
    "signature_candidate_contract": (
        "diagnostic_only_candidate_requires_all_catastrophic_episodes_on_the_"
        "same_side_of_the_target_median_pairwise_direction_probability_at_least_"
        f"{PARENT_CATASTROPHIC_AUDIT_PAIRWISE_FLOOR:.2f}_and_leave_one_"
        f"catastrophic_direction_probability_at_least_"
        f"{PARENT_CATASTROPHIC_AUDIT_LEAVE_ONE_FLOOR:.2f}_while_hypothetical_"
        f"one_dimension_exclusion_retains_at_least_"
        f"{PARENT_CATASTROPHIC_AUDIT_TARGET_RETENTION_FLOOR:.2f}_of_target_"
        "recoveries;any_candidate_requires_"
        "future_complete_date_validation_before_policy_consideration"
    ),
    "source_quality_gate": METRIC_CONTRACT["source_quality_gate"],
    "forbidden_uses": [
        "post_entry_mfe_mae_low_high_or_exit_as_entry_feature",
        "four_catastrophic_outcomes_as_same_sample_threshold_optimization",
        "multi_axis_child_combo_or_classifier_creation",
        "signature_candidate_as_same_sample_hard_entry_gate",
        "fixed_split_take_profit_or_catastrophic_stop_owner_change",
        "nxt_partial_context_as_krx_authority",
        "automatic_runtime_widget_sim_policy_or_preopen_apply",
        "real_order_submission",
        "account_or_quantity_decision",
        "provider_route_or_bot_control",
    ],
}
PARENT_POST_STOP_HORIZONS_MINUTES = (1, 3, 5, 10, 20, 30, 60)
PARENT_POST_STOP_RECOVERY_DOMINANCE_FLOOR = 0.75
PARENT_POST_STOP_RECOVERY_CONTRACT = {
    "metric_role": "fixed_parent_catastrophic_stop_recovery_path_counterfactual",
    "decision_authority": "offline_post_stop_execution_research_only",
    "window_policy": (
        "consume_only_unchanged_volatility_middle_catastrophic_entries;replay_"
        "the_fixed_40_60_add0p8_average_tp0p5_owner_and_observe_bars_strictly_"
        "after_the_catastrophic_stop_bar_through_session_end"
    ),
    "sample_floor": (
        f"{base.MIN_QUALIFIED_TRADING_DAYS}_coverage_qualified_trading_days_per_venue;"
        "all_observed_fixed_parent_catastrophic_stop_episodes"
    ),
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "counterfactual_contract": (
        "hard_stop_control_and_continue_with_the_same_filled_quantity_until_"
        "the_existing_average_target_or_last_observed_regular_mark_are_separate_"
        "paths;an_exact_krx_close_requires_a_1530_bar_and_an_earlier_terminal_"
        "mark_is_diagnostic_only;"
        "intrastop_bar_recovery_and_additional_drawdown_are_not_inferred"
    ),
    "dominance_contract": (
        f"recoverable_adverse_first_requires_target_recovery_in_at_least_"
        f"{PARENT_POST_STOP_RECOVERY_DOMINANCE_FLOOR:.2f}_of_catastrophic_"
        "episodes_and_both_higher_equal_weight_ev_and_compounded_return_than_"
        "the_hard_stop_control"
    ),
    "source_quality_gate": METRIC_CONTRACT["source_quality_gate"],
    "forbidden_uses": [
        "post_stop_path_as_entry_feature_or_same_sample_entry_threshold",
        "hard_stop_control_plus_counterfactual_profit_summation",
        "intrastop_bar_high_low_order_inference",
        "new_scale_in_leg_quantity_target_or_stop_joint_optimization",
        "automatic_stop_removal_or_runtime_policy_apply",
        "nxt_partial_context_as_krx_authority",
        "automatic_runtime_widget_sim_policy_or_preopen_apply",
        "real_order_submission",
        "account_or_quantity_decision",
        "provider_route_or_bot_control",
    ],
}
PARENT_POST_STOP_GRACE_HORIZONS_MINUTES = (5, 10, 20)
PARENT_POST_STOP_GRACE_CONTRACT = {
    "metric_role": "fixed_parent_catastrophic_stop_bounded_grace_counterfactual",
    "decision_authority": "offline_prospective_candidate_attribution_only",
    "window_policy": (
        "consume_only_the_unchanged_catastrophic_stop_recovery_episodes;start_each_"
        "fixed_5_10_20_minute_grace_arm_after_the_stop_bar;exit_at_the_existing_"
        "average_target_if_hit_first_otherwise_at_the_exact_horizon_bar_close"
    ),
    "sample_floor": (
        f"{base.MIN_QUALIFIED_TRADING_DAYS}_coverage_qualified_trading_days_per_venue;"
        "all_observed_fixed_parent_catastrophic_stop_episodes;thin_episode_results_"
        "remain_prospective_only"
    ),
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "comparison_contract": (
        "each_horizon_is_compared_independently_with_the_same_immediate_stop_"
        "control;all_horizons_that_improve_both_equal_weight_ev_and_compounded_"
        "return_are_listed_without_same_sample_ranking_or_best_arm_selection"
    ),
    "source_quality_gate": METRIC_CONTRACT["source_quality_gate"],
    "forbidden_uses": [
        "sum_returns_across_grace_arms_or_with_the_immediate_stop_control",
        "same_sample_best_horizon_selection_or_runtime_promotion",
        "post_stop_path_as_entry_feature_or_same_sample_entry_threshold",
        "new_scale_in_leg_quantity_target_or_emergency_floor_joint_change",
        "intrastop_bar_high_low_order_inference",
        "pre_1530_terminal_mark_as_exact_krx_close",
        "nxt_partial_context_as_krx_authority",
        "automatic_runtime_widget_sim_policy_or_preopen_apply",
        "real_order_submission",
        "account_or_quantity_decision",
        "provider_route_or_bot_control",
    ],
}
PARENT_POST_STOP_GRACE_PROSPECTIVE_CUTOFF_DATE = date(2026, 8, 10)
PARENT_POST_STOP_GRACE_PROSPECTIVE_START_DATE = date(2026, 8, 11)
PARENT_POST_STOP_GRACE_CALIBRATION_EPISODE_COUNT = 4
PARENT_POST_STOP_GRACE_PROSPECTIVE_HORIZONS_MINUTES = (5, 10, 20)
PARENT_POST_STOP_GRACE_PROSPECTIVE_CONTRACT = {
    "metric_role": "fixed_parent_post_stop_grace_prospective_oos_attribution",
    "decision_authority": "offline_future_episode_observation_only",
    "window_policy": (
        "freeze_candidate_horizons_5_10_20_at_2026_08_10;exclude_all_episodes_"
        "through_2026_08_10_from_prospective_metrics;attribute_only_new_"
        "catastrophic_episodes_from_2026_08_11"
    ),
    "sample_floor": (
        f"{base.MIN_QUALIFIED_TRADING_DAYS}_coverage_qualified_trading_days_per_venue;"
        "zero_new_episode_is_a_valid_observe_state;new_episode_counts_are_reported_"
        "without_single_episode_promotion"
    ),
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "candidate_contract": (
        "candidate_horizons_are_the_frozen_5_10_20_minute_set_from_the_2026_08_10_"
        "calibration_report_and_are_never_reselected_from_prospective_outcomes"
    ),
    "source_quality_gate": METRIC_CONTRACT["source_quality_gate"],
    "forbidden_uses": [
        "calibration_episode_reuse_as_prospective_oos_evidence",
        "prospective_and_calibration_return_mixing",
        "single_new_episode_best_horizon_selection_or_runtime_promotion",
        "sum_returns_across_grace_arms_or_with_the_immediate_stop_control",
        "new_scale_in_leg_quantity_target_emergency_floor_or_entry_threshold_change",
        "nxt_partial_context_as_krx_authority",
        "automatic_runtime_widget_sim_policy_or_preopen_apply",
        "real_order_submission",
        "account_or_quantity_decision",
        "provider_route_or_bot_control",
    ],
}


@dataclass(frozen=True)
class FeatureRow:
    trade_date: date
    venue: str
    session: str
    decision_at: datetime
    execution_at: datetime
    execution_price: float
    session_close_price: float
    features: tuple[float, ...]
    oracle_action: int
    decision_close_price: float = 0.0
    volatility_scale_pct: float = 0.0


def _optimal_actions(
    series: Sequence[base.Bar], *, cost_pct: float
) -> tuple[dict[int, int], list[dict[str, Any]], dict[str, Any]]:
    """Return oracle actions mapped to completed decision-bar indexes.

    Execution points are the next opens plus the final session close.  The
    dynamic program maximizes compounded wealth and uses no drawdown, rebound,
    target, or horizon label threshold.
    """
    if len(series) < 3:
        return {}, [], {"trade_count": 0, "compounded_return_pct": 0.0}
    prices = [float(bar.open) for bar in series[1:]] + [float(series[-1].close)]
    execution_times = [bar.timestamp for bar in series[1:]] + [series[-1].timestamp]
    decision_indexes: list[int | None] = list(range(len(series) - 1)) + [None]
    fee_multiplier = 1.0 - max(0.0, float(cost_pct)) / 100.0
    cash_values = [1.0]
    hold_values = [1.0 / prices[0]]
    cash_predecessors = ["cash"]
    hold_predecessors = ["buy"]
    for index in range(1, len(prices)):
        price = prices[index]
        prior_cash = cash_values[index - 1]
        prior_hold = hold_values[index - 1]
        sell_value = prior_hold * price * fee_multiplier
        if sell_value > prior_cash:
            cash_values.append(sell_value)
            cash_predecessors.append("sell")
        else:
            cash_values.append(prior_cash)
            cash_predecessors.append("cash")
        buy_value = prior_cash / price
        if buy_value > prior_hold:
            hold_values.append(buy_value)
            hold_predecessors.append("buy")
        else:
            hold_values.append(prior_hold)
            hold_predecessors.append("hold")

    state = "cash"
    raw_actions: list[tuple[int, str]] = []
    for index in range(len(prices) - 1, -1, -1):
        if state == "cash":
            predecessor = cash_predecessors[index]
            if predecessor == "sell":
                raw_actions.append((index, "SELL"))
                state = "hold"
        else:
            predecessor = hold_predecessors[index]
            if predecessor == "buy":
                raw_actions.append((index, "BUY"))
                state = "cash"
    raw_actions.reverse()

    action_map: dict[int, int] = {}
    trades: list[dict[str, Any]] = []
    open_trade: tuple[int, float] | None = None
    for execution_index, action in raw_actions:
        decision_index = decision_indexes[execution_index]
        if decision_index is not None:
            action_map[decision_index] = 1 if action == "BUY" else -1
        if action == "BUY":
            open_trade = (execution_index, prices[execution_index])
        elif open_trade is not None:
            entry_index, entry_price = open_trade
            exit_price = prices[execution_index]
            gross_pct = (exit_price / entry_price - 1.0) * 100.0
            net_pct = (exit_price / entry_price * fee_multiplier - 1.0) * 100.0
            trades.append(
                {
                    "entry_at": execution_times[entry_index].isoformat(),
                    "entry_price": entry_price,
                    "exit_at": execution_times[execution_index].isoformat(),
                    "exit_price": exit_price,
                    "gross_profit_pct": round(gross_pct, 6),
                    "net_profit_pct": round(net_pct, 6),
                }
            )
            open_trade = None
    return (
        action_map,
        trades,
        {
            "trade_count": len(trades),
            "compounded_return_pct": round((cash_values[-1] - 1.0) * 100.0, 6),
            "equal_weight_avg_profit_pct": (
                round(statistics.fmean(row["net_profit_pct"] for row in trades), 6)
                if trades
                else None
            ),
        },
    )


def _exact_return(
    bar: base.Bar, by_timestamp: dict[datetime, base.Bar], minutes: int
) -> float | None:
    prior = by_timestamp.get(bar.timestamp - timedelta(minutes=minutes))
    if prior is None or prior.close <= 0:
        return None
    return (bar.close / prior.close - 1.0) * 100.0


def _session_progress(bar: base.Bar) -> float:
    bounds = {
        "NXT_PREMARKET": (time(8, 0), time(8, 50)),
        "KRX_REGULAR": (time(9, 0), time(15, 30)),
        "NXT_REGULAR": (time(9, 0), time(15, 30)),
        "NXT_AFTERMARKET": (time(15, 40), time(20, 0)),
    }
    start, end = bounds.get(bar.session, (time(0, 0), time(23, 59)))
    current_minutes = bar.timestamp.hour * 60 + bar.timestamp.minute
    start_minutes = start.hour * 60 + start.minute
    end_minutes = end.hour * 60 + end.minute
    return min(
        1.0, max(0.0, (current_minutes - start_minutes) / (end_minutes - start_minutes))
    )


def _causal_volatility_scale_pct(
    series: Sequence[base.Bar], index: int
) -> float | None:
    if index < 20 or index >= len(series):
        return None
    trailing = series[index - 20 : index + 1]
    one_minute_returns = [
        (trailing[offset].close / trailing[offset - 1].close - 1.0) * 100.0
        for offset in range(1, len(trailing))
        if trailing[offset - 1].close > 0
    ]
    volatility = statistics.pstdev(one_minute_returns) if one_minute_returns else 0.0
    bar = series[index]
    positive_changes = [
        abs(trailing[offset].close - trailing[offset - 1].close)
        for offset in range(1, len(trailing))
        if trailing[offset].close != trailing[offset - 1].close
    ]
    inferred_tick = min(positive_changes) if positive_changes else 1.0
    tick_pct = max(inferred_tick / bar.close * 100.0, 1e-6)
    return max(volatility, tick_pct)


def _feature_vector(
    series: Sequence[base.Bar],
    index: int,
    *,
    stock_by_timestamp: dict[datetime, base.Bar],
    kospi_by_timestamp: dict[datetime, base.Bar],
) -> tuple[float, ...] | None:
    if index < 20 or index + 1 >= len(series):
        return None
    bar = series[index]
    returns = {
        minutes: _exact_return(bar, stock_by_timestamp, minutes)
        for minutes in (1, 3, 5, 15)
    }
    if any(value is None for value in returns.values()):
        return None
    trailing = series[index - 20 : index + 1]
    scale = _causal_volatility_scale_pct(series, index)
    if scale is None:
        return None
    high20 = max(item.high for item in trailing)
    low20 = min(item.low for item in trailing)
    range20 = max(float(high20 - low20), 1.0)
    total_volume = sum(max(0, item.volume) for item in series[: index + 1])
    vwap = (
        sum(item.close * max(0, item.volume) for item in series[: index + 1])
        / total_volume
        if total_volume > 0
        else float(bar.close)
    )
    median_volume = statistics.median(max(0, item.volume) for item in trailing)
    volume_ratio = (bar.volume + 1.0) / (median_volume + 1.0)
    kospi = kospi_by_timestamp.get(bar.timestamp)
    kospi3 = _exact_return(kospi, kospi_by_timestamp, 3) if kospi else None
    kospi15 = _exact_return(kospi, kospi_by_timestamp, 15) if kospi else None
    context_available = float(kospi3 is not None and kospi15 is not None)
    stock3 = float(returns[3])
    stock15 = float(returns[15])
    normalized_kospi3 = float(kospi3 or 0.0) / scale
    normalized_kospi15 = float(kospi15 or 0.0) / scale
    return (
        float(returns[1]) / scale,
        stock3 / scale,
        float(returns[5]) / scale,
        stock15 / scale,
        (stock3 - stock15) / scale,
        (bar.close - high20) / range20,
        (bar.close - low20) / range20,
        ((bar.close / vwap - 1.0) * 100.0) / scale,
        math.log(volume_ratio),
        ((bar.high - bar.low) / bar.close * 100.0) / scale,
        normalized_kospi3,
        normalized_kospi15,
        (stock3 - float(kospi3 or 0.0)) / scale,
        (stock15 - float(kospi15 or 0.0)) / scale,
        context_available,
        _session_progress(bar),
        float(bar.session in {"KRX_REGULAR", "NXT_REGULAR"}),
    )


def build_feature_rows(
    stock_bars: Sequence[base.Bar],
    kospi_bars: Sequence[base.Bar],
    *,
    cost_pct: float,
) -> tuple[list[FeatureRow], dict[str, Any]]:
    kospi_by_timestamp = {bar.timestamp: bar for bar in kospi_bars}
    rows: list[FeatureRow] = []
    oracle_by_venue: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for (_, venue, session), series in base._group_series(stock_bars).items():
        stock_by_timestamp = {bar.timestamp: bar for bar in series}
        action_map, oracle_trades, oracle_summary = _optimal_actions(
            series, cost_pct=cost_pct
        )
        oracle_by_venue[venue].append(
            {
                "trade_date": series[0].trade_date.isoformat(),
                "session": session,
                "summary": oracle_summary,
                "trades": oracle_trades,
            }
        )
        for index, bar in enumerate(series):
            features = _feature_vector(
                series,
                index,
                stock_by_timestamp=stock_by_timestamp,
                kospi_by_timestamp=kospi_by_timestamp,
            )
            if features is None:
                continue
            volatility_scale_pct = _causal_volatility_scale_pct(series, index)
            if volatility_scale_pct is None:
                continue
            rows.append(
                FeatureRow(
                    trade_date=bar.trade_date,
                    venue=venue,
                    session=session,
                    decision_at=bar.timestamp,
                    execution_at=series[index + 1].timestamp,
                    execution_price=float(series[index + 1].open),
                    session_close_price=float(series[-1].close),
                    features=features,
                    oracle_action=action_map.get(index, 0),
                    decision_close_price=float(bar.close),
                    volatility_scale_pct=float(volatility_scale_pct),
                )
            )
    oracle_summary_by_venue: dict[str, Any] = {}
    for venue in base.COHORTS:
        sessions = oracle_by_venue.get(venue, [])
        trades = [trade for item in sessions for trade in item["trades"]]
        daily_compounded: dict[str, float] = defaultdict(lambda: 1.0)
        for item in sessions:
            daily_compounded[item["trade_date"]] *= (
                1.0 + float(item["summary"]["compounded_return_pct"]) / 100.0
            )
        oracle_summary_by_venue[venue] = {
            "trade_count": len(trades),
            "trading_date_count": len(daily_compounded),
            "avg_trades_per_date": (
                round(len(trades) / len(daily_compounded), 6)
                if daily_compounded
                else None
            ),
            "equal_weight_avg_profit_pct": (
                round(statistics.fmean(row["net_profit_pct"] for row in trades), 6)
                if trades
                else None
            ),
            "avg_daily_oracle_compounded_return_pct": (
                round(
                    statistics.fmean(
                        (value - 1.0) * 100.0 for value in daily_compounded.values()
                    ),
                    6,
                )
                if daily_compounded
                else None
            ),
            "sessions": sessions,
        }
    return rows, oracle_summary_by_venue


def _oracle_cost_sensitivity(
    stock_bars: Sequence[base.Bar],
    *,
    cost_pcts: Sequence[float] = ORACLE_COST_SENSITIVITY_PCTS,
) -> dict[str, list[dict[str, Any]]]:
    """Measure opportunity density under increasingly conservative costs.

    This remains an ex-post upper-bound diagnostic.  It is useful only for
    separating "the tape contained no cost-bearing moves" from "the causal
    execution policy could not select those moves".
    """
    grouped = list(base._group_series(stock_bars).values())
    result: dict[str, list[dict[str, Any]]] = {venue: [] for venue in base.COHORTS}
    for cost_pct in cost_pcts:
        venue_trades: dict[str, list[dict[str, Any]]] = defaultdict(list)
        venue_dates: dict[str, set[date]] = defaultdict(set)
        for series in grouped:
            venue = series[0].venue
            _, trades, _ = _optimal_actions(series, cost_pct=float(cost_pct))
            venue_trades[venue].extend(trades)
            venue_dates[venue].add(series[0].trade_date)
        for venue in base.COHORTS:
            trades = venue_trades.get(venue, [])
            trading_dates = venue_dates.get(venue, set())
            result[venue].append(
                {
                    "round_trip_cost_pct": float(cost_pct),
                    "oracle_trade_count": len(trades),
                    "trading_date_count": len(trading_dates),
                    "avg_oracle_trades_per_date": (
                        round(len(trades) / len(trading_dates), 6)
                        if trading_dates
                        else None
                    ),
                    "equal_weight_avg_profit_pct": (
                        round(
                            statistics.fmean(
                                float(row["net_profit_pct"]) for row in trades
                            ),
                            6,
                        )
                        if trades
                        else None
                    ),
                    "authority": "ex_post_opportunity_density_upper_bound_only",
                }
            )
    return result


def _fit_action_model(
    rows: Sequence[FeatureRow], *, action: int
) -> tuple[HistGradientBoostingClassifier, float, dict[str, Any]] | None:
    labels = np.asarray([int(row.oracle_action == action) for row in rows])
    positive_count = int(labels.sum())
    if positive_count < 10 or positive_count == len(labels):
        return None
    features = np.asarray([row.features for row in rows], dtype=float)
    model = HistGradientBoostingClassifier(
        learning_rate=0.08,
        max_iter=60,
        max_leaf_nodes=15,
        min_samples_leaf=30,
        l2_regularization=1.0,
        class_weight="balanced",
        random_state=0,
    )
    model.fit(features, labels)
    probabilities = model.predict_proba(features)[:, 1]
    prevalence = positive_count / len(labels)
    signal_fraction = min(0.10, max(0.002, prevalence * 1.5))
    threshold = float(np.quantile(probabilities, 1.0 - signal_fraction))
    return (
        model,
        threshold,
        {
            "positive_count": positive_count,
            "row_count": len(labels),
            "prevalence_pct": round(prevalence * 100.0, 6),
            "threshold": round(threshold, 6),
            "threshold_policy": "prior_train_probability_prevalence_quantile",
        },
    )


def _historical_oracle_hold_cap(rows: Sequence[FeatureRow]) -> dict[str, Any] | None:
    grouped: dict[tuple[date, str, str], list[FeatureRow]] = defaultdict(list)
    for row in rows:
        grouped[(row.trade_date, row.venue, row.session)].append(row)
    durations: list[float] = []
    for series in grouped.values():
        entry_at: datetime | None = None
        for row in sorted(series, key=lambda item: item.decision_at):
            if row.oracle_action == 1 and entry_at is None:
                entry_at = row.execution_at
            elif row.oracle_action == -1 and entry_at is not None:
                duration = (row.execution_at - entry_at).total_seconds() / 60.0
                if duration > 0:
                    durations.append(duration)
                entry_at = None
    if not durations:
        return None
    cap = int(math.ceil(float(np.quantile(durations, 0.75, method="higher"))))
    return {
        "max_hold_minutes": max(1, min(30, cap)),
        "source_sample_count": len(durations),
        "selection_policy": "prior_train_oracle_duration_75th_percentile",
        "minimum_minutes": round(min(durations), 3),
        "median_minutes": round(statistics.median(durations), 3),
        "maximum_minutes": round(max(durations), 3),
    }


def _candidate_context(
    armed_candidate: dict[str, Any],
    confirmation_row: FeatureRow,
    *,
    buy_probability: float,
    sell_probability: float,
) -> tuple[str, tuple[float, ...], float]:
    candidate_age_minutes = (
        confirmation_row.execution_at - armed_candidate["armed_execution_at"]
    ).total_seconds() / 60.0
    lane = (
        "weak_reversal"
        if float(armed_candidate["features"][3]) <= 0.0
        else "bullish_transition"
    )
    features = (
        *armed_candidate["features"],
        *confirmation_row.features,
        float(armed_candidate["buy_probability"]),
        float(armed_candidate["sell_probability"]),
        float(buy_probability),
        float(sell_probability),
        float(candidate_age_minutes),
        float(lane == "bullish_transition"),
    )
    normalized = tuple(round(float(value), 8) for value in features)
    return lane, normalized, candidate_age_minutes


def _simulate_evaluation_rows(
    rows: Sequence[FeatureRow],
    *,
    buy_model: HistGradientBoostingClassifier,
    buy_threshold: float,
    sell_model: HistGradientBoostingClassifier,
    sell_threshold: float,
    cost_pct: float,
    max_hold_minutes: int | None = None,
    pairability_model: HistGradientBoostingClassifier | None = None,
    pairability_threshold: float | None = None,
) -> tuple[list[dict[str, Any]], list[tuple[FeatureRow, float, float]]]:
    trades: list[dict[str, Any]] = []
    scored_rows: list[tuple[FeatureRow, float, float]] = []
    grouped: dict[tuple[str, str], list[FeatureRow]] = defaultdict(list)
    for row in rows:
        grouped[(row.venue, row.session)].append(row)
    for (_, _), series in grouped.items():
        ordered = sorted(series, key=lambda row: row.decision_at)
        feature_matrix = np.asarray([row.features for row in ordered], dtype=float)
        buy_probabilities = buy_model.predict_proba(feature_matrix)[:, 1]
        sell_probabilities = sell_model.predict_proba(feature_matrix)[:, 1]
        position: dict[str, Any] | None = None
        armed_candidate: dict[str, Any] | None = None
        for row, buy_probability, sell_probability in zip(
            ordered, buy_probabilities, sell_probabilities
        ):
            scored_rows.append((row, float(buy_probability), float(sell_probability)))
            if position is None:
                if armed_candidate is not None:
                    candidate_age = (
                        row.execution_at - armed_candidate["armed_execution_at"]
                    ).total_seconds() / 60.0
                    candidate_expired = bool(
                        max_hold_minutes is not None
                        and candidate_age > max_hold_minutes
                    )
                    rebound_confirmed = bool(
                        row.features[0] > 0.0
                        and row.features[4]
                        > float(armed_candidate["acceleration_vol_units"])
                    )
                    if candidate_expired:
                        armed_candidate = None
                    elif rebound_confirmed:
                        lane, pairability_features, _ = _candidate_context(
                            armed_candidate,
                            row,
                            buy_probability=float(buy_probability),
                            sell_probability=float(sell_probability),
                        )
                        pairability_probability: float | None = None
                        pairability_selected = True
                        if pairability_model is not None:
                            if pairability_threshold is None:
                                raise ValueError(
                                    "pairability_threshold is required with model"
                                )
                            pairability_probability = float(
                                pairability_model.predict_proba(
                                    np.asarray([pairability_features], dtype=float)
                                )[0, 1]
                            )
                            pairability_selected = bool(
                                pairability_probability >= pairability_threshold
                            )
                        if not pairability_selected:
                            armed_candidate = None
                        else:
                            position = {
                                "entry_at": row.execution_at,
                                "entry_price": row.execution_price,
                                "entry_probability": float(
                                    armed_candidate["buy_probability"]
                                ),
                                "candidate_armed_at": armed_candidate["decision_at"],
                                "pairability_lane": lane,
                                "pairability_features": pairability_features,
                                "pairability_probability": pairability_probability,
                            }
                            armed_candidate = None
                            continue
                if position is None and (
                    buy_probability >= buy_threshold
                    and buy_probability > sell_probability
                ):
                    armed_candidate = {
                        "decision_at": row.decision_at,
                        "armed_execution_at": row.execution_at,
                        "buy_probability": float(buy_probability),
                        "sell_probability": float(sell_probability),
                        "acceleration_vol_units": row.features[4],
                        "features": row.features,
                    }
                continue
            duration_cap_reached = bool(
                max_hold_minutes is not None
                and (row.execution_at - position["entry_at"]).total_seconds() / 60.0
                >= max_hold_minutes
            )
            if sell_probability < sell_threshold and not duration_cap_reached:
                continue
            entry_price = float(position["entry_price"])
            exit_price = row.execution_price
            gross_pct = (exit_price / entry_price - 1.0) * 100.0
            net_pct = (
                exit_price / entry_price * (1.0 - cost_pct / 100.0) - 1.0
            ) * 100.0
            exit_reason = (
                "prior_duration_cap_next_open"
                if duration_cap_reached
                else "adaptive_sell_probability"
            )
            trades.append(
                {
                    "trade_date": row.trade_date.isoformat(),
                    "venue": row.venue,
                    "session": row.session,
                    "candidate_armed_at": position["candidate_armed_at"].isoformat(),
                    "entry_reason": "adaptive_buy_armed_recovery_confirmed",
                    "pairability_lane": position["pairability_lane"],
                    "pairability_features": list(position["pairability_features"]),
                    "pairability_probability": (
                        round(float(position["pairability_probability"]), 6)
                        if position["pairability_probability"] is not None
                        else None
                    ),
                    "pairability_selected": (
                        True if pairability_model is not None else None
                    ),
                    "entry_at": position["entry_at"].isoformat(),
                    "entry_price": entry_price,
                    "exit_at": row.execution_at.isoformat(),
                    "exit_price": exit_price,
                    "exit_reason": exit_reason,
                    "entry_probability": round(float(position["entry_probability"]), 6),
                    "exit_probability": (
                        None
                        if duration_cap_reached
                        else round(float(sell_probability), 6)
                    ),
                    "joint_transition_confidence": (
                        None
                        if duration_cap_reached
                        else round(
                            min(
                                float(position["entry_probability"]),
                                float(sell_probability),
                            ),
                            6,
                        )
                    ),
                    "gross_profit_pct": round(gross_pct, 6),
                    "net_profit_pct": round(net_pct, 6),
                }
            )
            position = None
        if position is not None:
            entry_price = float(position["entry_price"])
            exit_price = float(ordered[-1].session_close_price)
            gross_pct = (exit_price / entry_price - 1.0) * 100.0
            net_pct = (
                exit_price / entry_price * (1.0 - cost_pct / 100.0) - 1.0
            ) * 100.0
            trades.append(
                {
                    "trade_date": ordered[-1].trade_date.isoformat(),
                    "venue": ordered[-1].venue,
                    "session": ordered[-1].session,
                    "candidate_armed_at": position["candidate_armed_at"].isoformat(),
                    "entry_reason": "adaptive_buy_armed_recovery_confirmed",
                    "pairability_lane": position["pairability_lane"],
                    "pairability_features": list(position["pairability_features"]),
                    "pairability_probability": (
                        round(float(position["pairability_probability"]), 6)
                        if position["pairability_probability"] is not None
                        else None
                    ),
                    "pairability_selected": (
                        True if pairability_model is not None else None
                    ),
                    "entry_at": position["entry_at"].isoformat(),
                    "entry_price": entry_price,
                    "exit_at": ordered[-1].execution_at.isoformat(),
                    "exit_price": exit_price,
                    "exit_reason": "session_end_mark_to_market",
                    "entry_probability": round(float(position["entry_probability"]), 6),
                    "exit_probability": None,
                    "joint_transition_confidence": None,
                    "gross_profit_pct": round(gross_pct, 6),
                    "net_profit_pct": round(net_pct, 6),
                }
            )
    return trades, scored_rows


def _pairability_label(trade: dict[str, Any]) -> int:
    return int(
        trade.get("exit_reason") == "adaptive_sell_probability"
        and float(trade.get("net_profit_pct", 0.0)) > 0.0
    )


def _fit_pairability_classifier(
    trades: Sequence[dict[str, Any]],
) -> HistGradientBoostingClassifier | None:
    labels = np.asarray([_pairability_label(row) for row in trades], dtype=int)
    positive_count = int(labels.sum())
    negative_count = len(labels) - positive_count
    if (
        positive_count < PAIRABILITY_MIN_CLASS_SAMPLES
        or negative_count < PAIRABILITY_MIN_CLASS_SAMPLES
    ):
        return None
    features = np.asarray([row["pairability_features"] for row in trades], dtype=float)
    model = HistGradientBoostingClassifier(
        learning_rate=0.06,
        max_iter=80,
        max_leaf_nodes=9,
        min_samples_leaf=12,
        l2_regularization=2.0,
        class_weight="balanced",
        random_state=0,
    )
    model.fit(features, labels)
    return model


def _fit_pairability_model(
    prior_trades: Sequence[dict[str, Any]],
) -> tuple[HistGradientBoostingClassifier, float, dict[str, Any]] | None:
    """Fit a nested prior-only pair completion model and rank policy.

    The selection fraction is chosen on a chronological validation suffix.
    The final model may then consume every prior episode, but neither the
    current evaluation date nor its outcomes enter model or fraction choice.
    """
    dates = sorted({date.fromisoformat(row["trade_date"]) for row in prior_trades})
    if len(dates) < PAIRABILITY_MIN_HISTORY_DATES:
        return None
    validation_date_count = max(2, math.ceil(len(dates) * 0.25))
    fit_dates = set(dates[:-validation_date_count])
    validation_dates = set(dates[-validation_date_count:])
    fit_trades = [
        row
        for row in prior_trades
        if date.fromisoformat(row["trade_date"]) in fit_dates
    ]
    validation_trades = [
        row
        for row in prior_trades
        if date.fromisoformat(row["trade_date"]) in validation_dates
    ]
    selector_model = _fit_pairability_classifier(fit_trades)
    if selector_model is None or len(validation_trades) < 5:
        return None
    validation_features = np.asarray(
        [row["pairability_features"] for row in validation_trades], dtype=float
    )
    validation_probabilities = selector_model.predict_proba(validation_features)[:, 1]
    ranked_validation = sorted(
        zip(validation_probabilities, validation_trades),
        key=lambda item: float(item[0]),
        reverse=True,
    )
    fraction_rows: list[dict[str, Any]] = []
    for fraction in PAIRABILITY_SELECTION_FRACTIONS:
        count = max(5, math.ceil(len(ranked_validation) * fraction))
        selected = ranked_validation[: min(count, len(ranked_validation))]
        net = [float(row["net_profit_pct"]) for _, row in selected]
        fraction_rows.append(
            {
                "selection_fraction": float(fraction),
                "sample_count": len(selected),
                "simple_sum_profit_pct": round(sum(net), 6),
                "equal_weight_avg_profit_pct": round(statistics.fmean(net), 6),
                "diagnostic_win_rate_pct": round(
                    sum(value > 0.0 for value in net) / len(net) * 100.0, 3
                ),
            }
        )
    selected_policy = max(
        fraction_rows,
        key=lambda row: (
            float(row["equal_weight_avg_profit_pct"]),
            float(row["simple_sum_profit_pct"]),
            int(row["sample_count"]),
        ),
    )
    final_model = _fit_pairability_classifier(prior_trades)
    if final_model is None:
        return None
    prior_features = np.asarray(
        [row["pairability_features"] for row in prior_trades], dtype=float
    )
    prior_probabilities = final_model.predict_proba(prior_features)[:, 1]
    selection_fraction = float(selected_policy["selection_fraction"])
    threshold = float(np.quantile(prior_probabilities, 1.0 - selection_fraction))
    labels = [_pairability_label(row) for row in prior_trades]
    return (
        final_model,
        threshold,
        {
            "history_date_count": len(dates),
            "history_episode_count": len(prior_trades),
            "positive_count": sum(labels),
            "negative_count": len(labels) - sum(labels),
            "fit_dates": [item.isoformat() for item in sorted(fit_dates)],
            "validation_dates": [item.isoformat() for item in sorted(validation_dates)],
            "selection_fraction": selection_fraction,
            "probability_threshold": round(threshold, 6),
            "selection_policy": (
                "chronological_prior_validation_max_ev_then_simple_sum"
            ),
            "validation_fraction_results": fraction_rows,
            "selected_validation_result": selected_policy,
        },
    )


def _pairability_lane_summaries(
    trades: Sequence[dict[str, Any]], *, source_quality_passed: bool
) -> dict[str, Any]:
    return {
        lane: _summary(
            [row for row in trades if row.get("pairability_lane") == lane],
            source_quality_passed=source_quality_passed,
        )
        for lane in ("weak_reversal", "bullish_transition")
    }


def _pairability_decision(
    summary: dict[str, Any],
    *,
    sample_floor_passed: bool,
    source_quality_passed: bool,
) -> str:
    if not source_quality_passed:
        return "source_quality_blocked"
    if not sample_floor_passed:
        return "insufficient_coverage_dates"
    if int(summary.get("sample_count", 0)) == 0:
        return "insufficient_pairability_labels"
    ev = summary.get("equal_weight_avg_profit_pct")
    if ev is not None and float(ev) > 0.0:
        return "pairability_oos_positive"
    return "pairability_detected_execution_negative"


def _extract_competing_risk_candidates(
    rows: Sequence[FeatureRow],
    *,
    buy_model: HistGradientBoostingClassifier,
    buy_threshold: float,
    sell_model: HistGradientBoostingClassifier,
    sell_threshold: float,
    cost_pct: float,
) -> list[dict[str, Any]]:
    """Build causal entry candidates and their later first-transition outcomes.

    Buy/sell probabilities use models fitted on prior dates.  Later rows are
    outcome labels only; they never enter the candidate feature vector.
    """
    candidates: list[dict[str, Any]] = []
    grouped: dict[tuple[str, str], list[FeatureRow]] = defaultdict(list)
    for row in rows:
        grouped[(row.venue, row.session)].append(row)
    for ordered_rows in grouped.values():
        ordered = sorted(ordered_rows, key=lambda item: item.decision_at)
        matrix = np.asarray([row.features for row in ordered], dtype=float)
        buy_probabilities = buy_model.predict_proba(matrix)[:, 1]
        sell_probabilities = sell_model.predict_proba(matrix)[:, 1]
        armed_candidate: dict[str, Any] | None = None
        for index, (row, buy_probability, sell_probability) in enumerate(
            zip(ordered, buy_probabilities, sell_probabilities)
        ):
            if armed_candidate is not None:
                rebound_confirmed = bool(
                    row.features[0] > 0.0
                    and row.features[4]
                    > float(armed_candidate["acceleration_vol_units"])
                )
                if rebound_confirmed:
                    lane, features, candidate_age_minutes = _candidate_context(
                        armed_candidate,
                        row,
                        buy_probability=float(buy_probability),
                        sell_probability=float(sell_probability),
                    )
                    first_event = "session_end_censored"
                    exit_at = ordered[-1].execution_at
                    exit_price = float(ordered[-1].session_close_price)
                    for future_row, future_buy, future_sell in zip(
                        ordered[index + 1 :],
                        buy_probabilities[index + 1 :],
                        sell_probabilities[index + 1 :],
                    ):
                        if future_sell >= sell_threshold and future_sell > future_buy:
                            first_event = "sell_transition"
                        elif future_buy >= buy_threshold and future_buy > future_sell:
                            first_event = "adverse_buy_transition"
                        else:
                            continue
                        exit_at = future_row.execution_at
                        exit_price = float(future_row.execution_price)
                        break
                    entry_price = float(row.execution_price)
                    gross_pct = (exit_price / entry_price - 1.0) * 100.0
                    net_pct = (
                        exit_price / entry_price * (1.0 - cost_pct / 100.0) - 1.0
                    ) * 100.0
                    candidates.append(
                        {
                            "trade_date": row.trade_date.isoformat(),
                            "venue": row.venue,
                            "session": row.session,
                            "candidate_armed_at": armed_candidate[
                                "decision_at"
                            ].isoformat(),
                            "entry_at": row.execution_at.isoformat(),
                            "entry_price": entry_price,
                            "exit_at": exit_at.isoformat(),
                            "exit_price": exit_price,
                            "exit_reason": first_event,
                            "first_event": first_event,
                            "first_event_label": COMPETING_RISK_EVENT_LABELS[
                                first_event
                            ],
                            "event_duration_minutes": round(
                                (exit_at - row.execution_at).total_seconds() / 60.0,
                                3,
                            ),
                            "pairability_lane": lane,
                            "competing_risk_features": list(features),
                            "candidate_age_minutes": round(
                                float(candidate_age_minutes), 3
                            ),
                            "gross_profit_pct": round(gross_pct, 6),
                            "net_profit_pct": round(net_pct, 6),
                        }
                    )
                    armed_candidate = None
                    continue
            if buy_probability >= buy_threshold and buy_probability > sell_probability:
                armed_candidate = {
                    "decision_at": row.decision_at,
                    "armed_execution_at": row.execution_at,
                    "buy_probability": float(buy_probability),
                    "sell_probability": float(sell_probability),
                    "acceleration_vol_units": row.features[4],
                    "features": row.features,
                }
    return candidates


def _fit_competing_risk_estimators(
    candidates: Sequence[dict[str, Any]],
) -> tuple[HistGradientBoostingClassifier, HistGradientBoostingRegressor] | None:
    if len(candidates) < COMPETING_RISK_MIN_EPISODES:
        return None
    event_labels = np.asarray(
        [int(row["first_event_label"]) for row in candidates], dtype=int
    )
    event_counts = Counter(int(value) for value in event_labels)
    if len(event_counts) < 2 or sum(count >= 4 for count in event_counts.values()) < 2:
        return None
    features = np.asarray(
        [row["competing_risk_features"] for row in candidates], dtype=float
    )
    event_model = HistGradientBoostingClassifier(
        learning_rate=0.06,
        max_iter=80,
        max_leaf_nodes=9,
        min_samples_leaf=8,
        l2_regularization=2.0,
        class_weight="balanced",
        random_state=0,
    )
    ev_model = HistGradientBoostingRegressor(
        loss="squared_error",
        learning_rate=0.05,
        max_iter=80,
        max_leaf_nodes=9,
        min_samples_leaf=8,
        l2_regularization=2.0,
        random_state=0,
    )
    event_model.fit(features, event_labels)
    ev_model.fit(
        features,
        np.asarray([float(row["net_profit_pct"]) for row in candidates]),
    )
    return event_model, ev_model


def _score_competing_risk_candidates(
    candidates: Sequence[dict[str, Any]],
    *,
    event_model: HistGradientBoostingClassifier,
    ev_model: HistGradientBoostingRegressor,
) -> list[dict[str, Any]]:
    if not candidates:
        return []
    features = np.asarray(
        [row["competing_risk_features"] for row in candidates], dtype=float
    )
    event_probabilities = event_model.predict_proba(features)
    predicted_evs = ev_model.predict(features)
    class_indexes = {
        int(label): index for index, label in enumerate(event_model.classes_)
    }
    scored: list[dict[str, Any]] = []
    for original, probabilities, predicted_ev in zip(
        candidates, event_probabilities, predicted_evs
    ):
        row = dict(original)
        row["predicted_cost_adjusted_ev_pct"] = round(float(predicted_ev), 6)
        row["predicted_event_probabilities"] = {
            event_name: (
                round(float(probabilities[class_indexes[event_label]]), 6)
                if event_label in class_indexes
                else 0.0
            )
            for event_name, event_label in COMPETING_RISK_EVENT_LABELS.items()
        }
        row["competing_risk_selected"] = bool(predicted_ev > 0.0)
        scored.append(row)
    return scored


def _non_overlapping_candidates(
    candidates: Sequence[dict[str, Any]],
    *,
    selected_only: bool,
    selection_key: str = "competing_risk_selected",
) -> list[dict[str, Any]]:
    accepted: list[dict[str, Any]] = []
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in candidates:
        grouped[(str(row["venue"]), str(row["session"]))].append(row)
    for series in grouped.values():
        next_available: datetime | None = None
        for row in sorted(series, key=lambda item: str(item["entry_at"])):
            if selected_only and not row.get(selection_key, False):
                continue
            entry_at = datetime.fromisoformat(str(row["entry_at"]))
            if next_available is not None and entry_at < next_available:
                continue
            accepted.append(row)
            next_available = datetime.fromisoformat(str(row["exit_at"]))
    return accepted


def _entry_identity(row: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(row["trade_date"]),
        str(row["venue"]),
        str(row["session"]),
        str(row["entry_at"]),
    )


def _same_entry_recovery_cohort(
    economic_selected: Sequence[dict[str, Any]],
    recovery_by_entry: dict[tuple[str, str, str, str], dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    baseline = [
        row for row in economic_selected if _entry_identity(row) in recovery_by_entry
    ]
    recovery = [recovery_by_entry[_entry_identity(row)] for row in baseline]
    return baseline, recovery


def _same_entry_axis_cohort(
    economic_selected: Sequence[dict[str, Any]],
    arm_candidates_by_entry: dict[str, dict[tuple[str, str, str, str], dict[str, Any]]],
) -> dict[str, list[dict[str, Any]]]:
    ready_entries = set.intersection(
        *(set(rows) for rows in arm_candidates_by_entry.values())
    )
    baseline = [
        row for row in economic_selected if _entry_identity(row) in ready_entries
    ]
    return {
        "baseline": baseline,
        **{
            arm: [rows[_entry_identity(row)] for row in baseline]
            for arm, rows in arm_candidates_by_entry.items()
        },
    }


def _fit_lane_competing_risk_model(
    prior_candidates: Sequence[dict[str, Any]], *, lane: str
) -> (
    tuple[HistGradientBoostingClassifier, HistGradientBoostingRegressor, dict[str, Any]]
    | None
):
    lane_candidates = [
        row for row in prior_candidates if row.get("pairability_lane") == lane
    ]
    dates = sorted(
        {date.fromisoformat(str(row["trade_date"])) for row in lane_candidates}
    )
    if len(dates) < COMPETING_RISK_MIN_HISTORY_DATES:
        return None
    validation_date_count = max(2, math.ceil(len(dates) * 0.25))
    fit_dates = set(dates[:-validation_date_count])
    validation_dates = set(dates[-validation_date_count:])
    fit_candidates = [
        row
        for row in lane_candidates
        if date.fromisoformat(str(row["trade_date"])) in fit_dates
    ]
    validation_candidates = [
        row
        for row in lane_candidates
        if date.fromisoformat(str(row["trade_date"])) in validation_dates
    ]
    selector_bundle = _fit_competing_risk_estimators(fit_candidates)
    if selector_bundle is None or not validation_candidates:
        return None
    selector_event_model, selector_ev_model = selector_bundle
    validation_scored = _score_competing_risk_candidates(
        validation_candidates,
        event_model=selector_event_model,
        ev_model=selector_ev_model,
    )
    validation_selected = _non_overlapping_candidates(
        validation_scored, selected_only=True
    )
    final_bundle = _fit_competing_risk_estimators(lane_candidates)
    if final_bundle is None:
        return None
    final_event_model, final_ev_model = final_bundle
    validation_event_accuracy = statistics.fmean(
        float(
            max(
                row["predicted_event_probabilities"],
                key=row["predicted_event_probabilities"].get,
            )
            == row["first_event"]
        )
        for row in validation_scored
    )
    return (
        final_event_model,
        final_ev_model,
        {
            "lane": lane,
            "history_date_count": len(dates),
            "history_episode_count": len(lane_candidates),
            "fit_dates": [item.isoformat() for item in sorted(fit_dates)],
            "validation_dates": [item.isoformat() for item in sorted(validation_dates)],
            "event_counts": dict(
                sorted(Counter(row["first_event"] for row in lane_candidates).items())
            ),
            "validation_event_accuracy_pct": round(
                validation_event_accuracy * 100.0, 3
            ),
            "validation_control_summary": _summary(
                _non_overlapping_candidates(validation_candidates, selected_only=False),
                source_quality_passed=True,
            ),
            "validation_selected_summary": _summary(
                validation_selected,
                source_quality_passed=True,
            ),
            "selection_policy": "direct_predicted_cost_adjusted_ev_gt_zero",
        },
    )


def _competing_risk_decision(
    selected_summary: dict[str, Any],
    control_summary: dict[str, Any],
    *,
    sample_floor_passed: bool,
    source_quality_passed: bool,
) -> str:
    if not source_quality_passed:
        return "source_quality_blocked"
    if not sample_floor_passed:
        return "insufficient_coverage_dates"
    # The declared primary metric is source-quality-adjusted EV.  The caller
    # has already failed closed when source quality is unavailable, so do not
    # silently fall back to an unadjusted headline here.
    selected_ev = selected_summary.get("source_quality_adjusted_ev_pct")
    control_ev = control_summary.get("source_quality_adjusted_ev_pct")
    if selected_ev is None:
        return "no_incremental_predictive_value"
    if float(selected_ev) > 0.0:
        return "lane_competing_risk_oos_positive"
    if control_ev is not None and float(selected_ev) > float(control_ev):
        return "lane_ev_improved_but_negative"
    return "no_incremental_predictive_value"


def _extract_economic_first_passage_candidates(
    rows: Sequence[FeatureRow],
    *,
    buy_model: HistGradientBoostingClassifier,
    buy_threshold: float,
    sell_model: HistGradientBoostingClassifier,
    sell_threshold: float,
) -> list[dict[str, Any]]:
    """Extract causal entries while retaining the later close-to-next-open path.

    The retained path is outcome-only research data.  It is removed from
    public trade rows and is never part of the entry feature vector.
    """
    candidates: list[dict[str, Any]] = []
    grouped: dict[tuple[str, str], list[FeatureRow]] = defaultdict(list)
    for row in rows:
        grouped[(row.venue, row.session)].append(row)
    for ordered_rows in grouped.values():
        ordered = sorted(ordered_rows, key=lambda item: item.decision_at)
        matrix = np.asarray([row.features for row in ordered], dtype=float)
        buy_probabilities = buy_model.predict_proba(matrix)[:, 1]
        sell_probabilities = sell_model.predict_proba(matrix)[:, 1]
        armed_candidate: dict[str, Any] | None = None
        for index, (row, buy_probability, sell_probability) in enumerate(
            zip(ordered, buy_probabilities, sell_probabilities)
        ):
            if armed_candidate is not None:
                rebound_confirmed = bool(
                    row.features[0] > 0.0
                    and row.features[4]
                    > float(armed_candidate["acceleration_vol_units"])
                )
                if rebound_confirmed:
                    lane, features, candidate_age_minutes = _candidate_context(
                        armed_candidate,
                        row,
                        buy_probability=float(buy_probability),
                        sell_probability=float(sell_probability),
                    )
                    path = []
                    for future_row, future_buy, future_sell in zip(
                        ordered[index + 1 :],
                        buy_probabilities[index + 1 :],
                        sell_probabilities[index + 1 :],
                        strict=True,
                    ):
                        path.append(
                            {
                                "observed_at": future_row.decision_at.isoformat(),
                                "execution_at": future_row.execution_at.isoformat(),
                                "reference_price": float(
                                    future_row.decision_close_price
                                    or future_row.execution_price
                                ),
                                "execution_price": float(future_row.execution_price),
                                "point_type": "completed_close_next_open",
                                "return_3m_vol_units": float(future_row.features[1]),
                                "return_5m_vol_units": float(future_row.features[2]),
                                "acceleration_vol_units": float(future_row.features[4]),
                                "buy_probability": float(future_buy),
                                "sell_probability": float(future_sell),
                                "volatility_scale_pct": float(
                                    future_row.volatility_scale_pct
                                ),
                                "decision_features": list(future_row.features),
                            }
                        )
                    final_row = ordered[-1]
                    path.append(
                        {
                            "observed_at": final_row.execution_at.isoformat(),
                            "execution_at": final_row.execution_at.isoformat(),
                            "reference_price": float(final_row.session_close_price),
                            "execution_price": float(final_row.session_close_price),
                            "point_type": "session_close_mark",
                            "return_3m_vol_units": None,
                            "return_5m_vol_units": None,
                            "acceleration_vol_units": None,
                            "decision_features": None,
                        }
                    )
                    volatility_scale_pct = max(float(row.volatility_scale_pct), 1e-6)
                    candidates.append(
                        {
                            "trade_date": row.trade_date.isoformat(),
                            "venue": row.venue,
                            "session": row.session,
                            "candidate_armed_at": armed_candidate[
                                "decision_at"
                            ].isoformat(),
                            "candidate_armed_execution_at": armed_candidate[
                                "armed_execution_at"
                            ].isoformat(),
                            "entry_at": row.execution_at.isoformat(),
                            "entry_price": float(row.execution_price),
                            "pairability_lane": lane,
                            "economic_features": [
                                *features,
                                round(volatility_scale_pct, 8),
                            ],
                            "candidate_age_minutes": round(
                                float(candidate_age_minutes), 3
                            ),
                            "volatility_scale_pct": round(volatility_scale_pct, 8),
                            "_economic_path": path,
                        }
                    )
                    armed_candidate = None
                    continue
            if buy_probability >= buy_threshold and buy_probability > sell_probability:
                armed_candidate = {
                    "decision_at": row.decision_at,
                    "armed_execution_at": row.execution_at,
                    "buy_probability": float(buy_probability),
                    "sell_probability": float(sell_probability),
                    "acceleration_vol_units": row.features[4],
                    "features": row.features,
                }
    return candidates


def _adverse_confirmation_reason(
    candidate: dict[str, Any],
    point: dict[str, Any],
    *,
    adverse_breach_streak: int,
) -> str | None:
    if adverse_breach_streak >= 2:
        return "two_consecutive_boundary_breaches"
    trend_damaged = bool(
        point["point_type"] == "completed_close_next_open"
        and float(point["return_3m_vol_units"]) < 0.0
        and float(point["return_5m_vol_units"]) < 0.0
        and float(point["acceleration_vol_units"]) <= 0.0
    )
    if candidate["pairability_lane"] == "bullish_transition" and trend_damaged:
        return "bullish_negative_3m_5m_acceleration"
    return None


def _apply_economic_first_passage_policy(
    candidate: dict[str, Any],
    *,
    target_vol_multiplier: float,
    adverse_vol_multiplier: float,
    cost_pct: float,
) -> dict[str, Any]:
    entry_price = float(candidate["entry_price"])
    scale_pct = max(float(candidate["volatility_scale_pct"]), 1e-6)
    favorable_boundary_pct = max(
        float(cost_pct) + scale_pct * float(target_vol_multiplier),
        float(cost_pct) + 1e-6,
    )
    adverse_boundary_pct = max(
        scale_pct * float(adverse_vol_multiplier),
        1e-6,
    )
    path = list(candidate["_economic_path"])
    path_returns = [
        (float(point["reference_price"]) / entry_price - 1.0) * 100.0 for point in path
    ]
    selected_point = path[-1]
    selected_index = len(path) - 1
    event = "session_end_censored"
    adverse_breach_streak = 0
    adverse_breach_streak_at_exit = 0
    adverse_confirmation_reason: str | None = None
    for point_index, (point, path_return_pct) in enumerate(zip(path, path_returns)):
        if path_return_pct >= favorable_boundary_pct:
            selected_point = point
            selected_index = point_index
            event = "favorable_first_passage"
            break
        if path_return_pct <= -adverse_boundary_pct:
            adverse_breach_streak += 1
            confirmation_reason = _adverse_confirmation_reason(
                candidate,
                point,
                adverse_breach_streak=adverse_breach_streak,
            )
            if confirmation_reason is not None:
                selected_point = point
                selected_index = point_index
                event = "adverse_first_passage"
                adverse_breach_streak_at_exit = adverse_breach_streak
                adverse_confirmation_reason = confirmation_reason
                break
        else:
            adverse_breach_streak = 0
    exit_price = float(selected_point["execution_price"])
    exit_at = datetime.fromisoformat(str(selected_point["execution_at"]))
    entry_at = datetime.fromisoformat(str(candidate["entry_at"]))
    gross_pct = (exit_price / entry_price - 1.0) * 100.0
    net_pct = (exit_price / entry_price * (1.0 - cost_pct / 100.0) - 1.0) * 100.0
    public = {key: value for key, value in candidate.items() if not key.startswith("_")}
    public.update(
        {
            "exit_at": exit_at.isoformat(),
            "exit_price": exit_price,
            "exit_reason": event,
            "economic_first_passage_event": event,
            "economic_event_label": ECONOMIC_FIRST_PASSAGE_EVENT_LABELS[event],
            "target_vol_multiplier": float(target_vol_multiplier),
            "adverse_vol_multiplier": float(adverse_vol_multiplier),
            "favorable_boundary_pct": round(favorable_boundary_pct, 6),
            "adverse_boundary_pct": round(adverse_boundary_pct, 6),
            "adverse_breach_streak_at_exit": adverse_breach_streak_at_exit,
            "adverse_confirmation_reason": adverse_confirmation_reason,
            "event_duration_minutes": round(
                (exit_at - entry_at).total_seconds() / 60.0, 3
            ),
            "mfe_pct": round(max(path_returns[: selected_index + 1]), 6),
            "mae_pct": round(min(path_returns[: selected_index + 1]), 6),
            "post_entry_session_mfe_pct": round(max(path_returns), 6),
            "post_entry_session_mae_pct": round(min(path_returns), 6),
            "gross_profit_pct": round(gross_pct, 6),
            "net_profit_pct": round(net_pct, 6),
        }
    )
    return public


def _compounded_net_return_pct(episodes: Sequence[dict[str, Any]]) -> float:
    wealth = 1.0
    for row in episodes:
        wealth *= 1.0 + float(row["net_profit_pct"]) / 100.0
    return round((wealth - 1.0) * 100.0, 6)


def _fit_economic_first_passage_estimators(
    episodes: Sequence[dict[str, Any]],
) -> tuple[HistGradientBoostingClassifier, HistGradientBoostingRegressor] | None:
    if len(episodes) < ECONOMIC_FIRST_PASSAGE_MIN_EPISODES:
        return None
    labels = np.asarray([int(row["economic_event_label"]) for row in episodes])
    counts = Counter(int(value) for value in labels)
    if len(counts) < 2 or sum(count >= 4 for count in counts.values()) < 2:
        return None
    features = np.asarray([row["economic_features"] for row in episodes], dtype=float)
    event_model = HistGradientBoostingClassifier(
        learning_rate=0.06,
        max_iter=80,
        max_leaf_nodes=9,
        min_samples_leaf=8,
        l2_regularization=2.0,
        class_weight="balanced",
        random_state=0,
    )
    ev_model = HistGradientBoostingRegressor(
        loss="squared_error",
        learning_rate=0.05,
        max_iter=80,
        max_leaf_nodes=9,
        min_samples_leaf=8,
        l2_regularization=2.0,
        random_state=0,
    )
    event_model.fit(features, labels)
    ev_model.fit(
        features,
        np.asarray([float(row["net_profit_pct"]) for row in episodes]),
    )
    return event_model, ev_model


def _score_economic_first_passage_episodes(
    episodes: Sequence[dict[str, Any]],
    *,
    event_model: HistGradientBoostingClassifier,
    ev_model: HistGradientBoostingRegressor,
) -> list[dict[str, Any]]:
    if not episodes:
        return []
    features = np.asarray([row["economic_features"] for row in episodes], dtype=float)
    event_probabilities = event_model.predict_proba(features)
    predicted_evs = ev_model.predict(features)
    class_indexes = {
        int(label): index for index, label in enumerate(event_model.classes_)
    }
    scored: list[dict[str, Any]] = []
    for original, probabilities, predicted_ev in zip(
        episodes, event_probabilities, predicted_evs
    ):
        row = dict(original)
        row["predicted_cost_adjusted_ev_pct"] = round(float(predicted_ev), 6)
        row["predicted_event_probabilities"] = {
            event_name: (
                round(float(probabilities[class_indexes[event_label]]), 6)
                if event_label in class_indexes
                else 0.0
            )
            for event_name, event_label in ECONOMIC_FIRST_PASSAGE_EVENT_LABELS.items()
        }
        row["economic_first_passage_selected"] = bool(predicted_ev > 0.0)
        scored.append(row)
    return scored


def _fit_recovery_entry_utility_model(
    prior_recovery_episodes: Sequence[dict[str, Any]],
    *,
    lane: str,
) -> tuple[HistGradientBoostingRegressor, dict[str, Any]] | None:
    """Fit direct entry utility only from earlier recovery-policy OOS outcomes."""
    lane_episodes = [
        row for row in prior_recovery_episodes if row.get("pairability_lane") == lane
    ]
    dates = sorted(
        {date.fromisoformat(str(row["trade_date"])) for row in lane_episodes}
    )
    if (
        len(dates) < RECOVERY_ENTRY_UTILITY_MIN_HISTORY_DATES
        or len(lane_episodes) < RECOVERY_ENTRY_UTILITY_MIN_EPISODES
    ):
        return None
    if any(
        not row.get("recovery_entry_label_oos")
        or row.get("recovery_entry_label_exit_policy") != "recovery_only"
        or bool(row.get("trailing_applied"))
        or float(row.get("trailing_vol_multiplier", 0.0)) != 0.0
        or date.fromisoformat(str(row["recovery_exit_model_fit_max_date"]))
        >= date.fromisoformat(str(row["trade_date"]))
        for row in lane_episodes
    ):
        raise ValueError(
            "recovery entry utility history must contain prior OOS recovery-only labels"
        )
    model = HistGradientBoostingRegressor(
        loss="squared_error",
        learning_rate=0.05,
        max_iter=80,
        max_leaf_nodes=9,
        min_samples_leaf=8,
        l2_regularization=2.0,
        random_state=0,
    )
    model.fit(
        np.asarray([row["economic_features"] for row in lane_episodes], dtype=float),
        np.asarray([float(row["net_profit_pct"]) for row in lane_episodes]),
    )
    return model, {
        "lane": lane,
        "history_date_count": len(dates),
        "history_episode_count": len(lane_episodes),
        "fit_dates": [item.isoformat() for item in dates],
        "label": "recovery_only_cost_adjusted_net_profit_pct",
        "selection_policy": "direct_predicted_recovery_only_ev_gt_zero",
    }


def _score_recovery_entry_utility_episodes(
    episodes: Sequence[dict[str, Any]],
    *,
    ev_model: HistGradientBoostingRegressor,
) -> list[dict[str, Any]]:
    if not episodes:
        return []
    predicted_evs = ev_model.predict(
        np.asarray([row["economic_features"] for row in episodes], dtype=float)
    )
    scored: list[dict[str, Any]] = []
    for original, predicted_ev in zip(episodes, predicted_evs, strict=True):
        row = dict(original)
        row["predicted_recovery_entry_ev_pct"] = round(float(predicted_ev), 6)
        row["recovery_entry_selected"] = bool(predicted_ev > 0.0)
        scored.append(row)
    return scored


def _fit_recovery_entry_calibrator(
    prior_scored_episodes: Sequence[dict[str, Any]],
    *,
    lane: str,
) -> tuple[dict[str, float], dict[str, Any]] | None:
    lane_episodes = [
        row for row in prior_scored_episodes if row.get("pairability_lane") == lane
    ]
    dates = sorted(
        {date.fromisoformat(str(row["trade_date"])) for row in lane_episodes}
    )
    if (
        len(dates) < RECOVERY_ENTRY_CALIBRATION_MIN_HISTORY_DATES
        or len(lane_episodes) < RECOVERY_ENTRY_CALIBRATION_MIN_EPISODES
    ):
        return None
    if any(
        not row.get("recovery_entry_prediction_oos")
        or date.fromisoformat(str(row["recovery_entry_model_fit_max_date"]))
        >= date.fromisoformat(str(row["trade_date"]))
        or row.get("recovery_entry_label_exit_policy") != "recovery_only"
        or bool(row.get("trailing_applied"))
        or float(row.get("trailing_vol_multiplier", 0.0)) != 0.0
        for row in lane_episodes
    ):
        raise ValueError(
            "recovery entry calibration history must contain prior OOS "
            "recovery-only predictions"
        )
    predictions = np.asarray(
        [float(row["predicted_recovery_entry_ev_pct"]) for row in lane_episodes],
        dtype=float,
    )
    outcomes = np.asarray(
        [float(row["net_profit_pct"]) for row in lane_episodes], dtype=float
    )
    prediction_mean = float(np.mean(predictions))
    outcome_mean = float(np.mean(outcomes))
    centered = predictions - prediction_mean
    prediction_variance = float(np.mean(centered**2))
    raw_slope = (
        float(np.mean(centered * (outcomes - outcome_mean))) / prediction_variance
        if prediction_variance > 1e-12
        else 0.0
    )
    reliability = len(lane_episodes) / (
        len(lane_episodes) + RECOVERY_ENTRY_CALIBRATION_MIN_EPISODES
    )
    slope = max(-1.5, min(1.5, raw_slope * reliability))
    intercept = outcome_mean - slope * prediction_mean
    residuals = outcomes - (intercept + slope * predictions)
    residual_std = float(np.std(residuals))
    recent_dates = set(dates[-RECOVERY_ENTRY_CALIBRATION_RECENT_DATES:])
    recent_residuals = [
        float(residual)
        for row, residual in zip(lane_episodes, residuals, strict=True)
        if date.fromisoformat(str(row["trade_date"])) in recent_dates
    ]
    recent_residual_mean = (
        statistics.fmean(recent_residuals) if recent_residuals else 0.0
    )
    drift_limit = residual_std if residual_std > 0.0 else 0.0
    drift_adjustment = max(
        -drift_limit,
        min(drift_limit, 0.5 * recent_residual_mean),
    )
    intercept += drift_adjustment
    parameters = {
        "intercept": intercept,
        "slope": slope,
        "prediction_mean": prediction_mean,
        "prediction_variance": prediction_variance,
        "residual_std": residual_std,
        "residual_standard_error": residual_std / math.sqrt(len(lane_episodes)),
    }
    return parameters, {
        "lane": lane,
        "history_date_count": len(dates),
        "history_episode_count": len(lane_episodes),
        "fit_dates": [item.isoformat() for item in dates],
        "recent_drift_dates": [item.isoformat() for item in sorted(recent_dates)],
        "raw_slope": round(raw_slope, 6),
        "reliability": round(reliability, 6),
        "shrunk_slope": round(slope, 6),
        "base_intercept": round(outcome_mean - slope * prediction_mean, 6),
        "recent_residual_mean": round(recent_residual_mean, 6),
        "drift_adjustment": round(drift_adjustment, 6),
        "adjusted_intercept": round(intercept, 6),
        "residual_std": round(residual_std, 6),
        "selection_policy": "calibrated_mean_recovery_only_ev_gt_zero",
        "uncertainty_role": "diagnostic_only_not_selection_lower_bound",
    }


def _score_calibrated_recovery_entry_episodes(
    episodes: Sequence[dict[str, Any]],
    *,
    parameters: dict[str, float],
) -> list[dict[str, Any]]:
    scored: list[dict[str, Any]] = []
    variance = max(float(parameters["prediction_variance"]), 1e-12)
    standard_error = float(parameters["residual_standard_error"])
    for original in episodes:
        raw_prediction = float(original["predicted_recovery_entry_ev_pct"])
        calibrated_ev = (
            float(parameters["intercept"]) + float(parameters["slope"]) * raw_prediction
        )
        leverage = 1.0 + (
            (raw_prediction - float(parameters["prediction_mean"])) ** 2 / variance
        )
        uncertainty = standard_error * math.sqrt(leverage)
        row = dict(original)
        row.update(
            {
                "calibrated_recovery_entry_ev_pct": round(calibrated_ev, 6),
                "calibrated_recovery_entry_uncertainty_pct": round(uncertainty, 6),
                "calibrated_recovery_entry_mean_selected": bool(calibrated_ev > 0.0),
                "calibrated_recovery_entry_selected": bool(calibrated_ev > 0.0),
            }
        )
        scored.append(row)
    return scored


def _apply_calibration_capacity_floor(
    raw_nonoverlap: Sequence[dict[str, Any]],
    calibrated_mean_nonoverlap: Sequence[dict[str, Any]],
    calibrated_candidates: Sequence[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    opportunity_floor = (
        max(
            1,
            math.ceil(
                len(raw_nonoverlap) * RECOVERY_ENTRY_CALIBRATION_OPPORTUNITY_RETENTION
            ),
        )
        if raw_nonoverlap
        else 0
    )
    fallback_applied = bool(
        raw_nonoverlap and len(calibrated_mean_nonoverlap) < opportunity_floor
    )
    if fallback_applied:
        calibrated_by_entry = {
            _entry_identity(row): row for row in calibrated_candidates
        }
        selected = []
        for raw_row in raw_nonoverlap:
            row = dict(calibrated_by_entry[_entry_identity(raw_row)])
            row.update(
                {
                    "calibrated_recovery_entry_selected": True,
                    "calibration_capacity_fallback_selected": True,
                    "calibration_selection_reason": (
                        "raw_recovery_capacity_floor_fallback"
                    ),
                }
            )
            selected.append(row)
    else:
        selected = []
        for selected_row in calibrated_mean_nonoverlap:
            row = dict(selected_row)
            row.update(
                {
                    "calibration_capacity_fallback_selected": False,
                    "calibration_selection_reason": "positive_calibrated_mean_ev",
                }
            )
            selected.append(row)
    return selected, {
        "raw_nonoverlap_count": len(raw_nonoverlap),
        "calibrated_mean_nonoverlap_count": len(calibrated_mean_nonoverlap),
        "opportunity_floor_count": opportunity_floor,
        "capacity_fallback_applied": fallback_applied,
        "final_nonoverlap_count": len(selected),
    }


def _derive_recovery_entry_timing_candidate(
    candidate: dict[str, Any],
    *,
    arm: str,
    max_wait_minutes: int,
) -> dict[str, Any] | None:
    """Move entry to the first completed-bar trigger without future lookahead."""
    if arm not in RECOVERY_ENTRY_TIMING_ARMS:
        raise ValueError(f"unknown recovery entry timing arm: {arm}")
    source_entry_at = datetime.fromisoformat(str(candidate["entry_at"]))
    source_entry_price = float(candidate["entry_price"])
    source_scale_pct = max(float(candidate["volatility_scale_pct"]), 1e-6)
    path = list(candidate["_economic_path"])
    selected_index: int | None = None
    prior_vwap_reclaimed = False
    pullback_observed = False
    for point_index, point in enumerate(path):
        if point.get("point_type") != "completed_close_next_open":
            continue
        observed_at = datetime.fromisoformat(str(point["observed_at"]))
        elapsed_minutes = (observed_at - source_entry_at).total_seconds() / 60.0
        if elapsed_minutes < 0.0:
            continue
        if elapsed_minutes > max_wait_minutes:
            break
        features = point.get("decision_features")
        if not isinstance(features, list) or len(features) != len(FEATURE_NAMES):
            raise ValueError("timing path point is missing exact decision features")
        reference_price = float(point["reference_price"])
        return_1m = float(features[0])
        return_3m = float(features[1])
        return_5m = float(features[2])
        acceleration = float(features[4])
        vwap_distance = float(features[7])
        chase_limit = source_entry_price * (1.0 + 0.5 * source_scale_pct / 100.0)
        if arm == "confirmation_continuation":
            matched = bool(
                return_3m > 0.0
                and return_5m >= 0.0
                and acceleration >= 0.0
                and reference_price <= chase_limit
            )
        elif arm == "first_non_chasing_pullback":
            pullback_observed = bool(
                pullback_observed
                or return_1m < 0.0
                or reference_price < source_entry_price
            )
            pullback_limit = source_entry_price * (
                1.0 + 0.15 * source_scale_pct / 100.0
            )
            matched = bool(
                pullback_observed
                and return_1m >= 0.0
                and return_5m >= -0.25
                and vwap_distance >= -0.25
                and reference_price <= pullback_limit
            )
        else:
            matched = bool(
                prior_vwap_reclaimed and vwap_distance >= 0.0 and return_3m >= 0.0
            )
            prior_vwap_reclaimed = bool(vwap_distance >= 0.0)
        if matched:
            selected_index = point_index
            break
    if selected_index is None or selected_index + 1 >= len(path):
        return None
    trigger = path[selected_index]
    remaining_path = path[selected_index + 1 :]
    if not remaining_path:
        return None
    trigger_features = [float(value) for value in trigger["decision_features"]]
    economic_features = list(candidate["economic_features"])
    feature_count = len(FEATURE_NAMES)
    economic_features[feature_count : feature_count * 2] = trigger_features
    economic_features[feature_count * 2 + 2] = float(trigger["buy_probability"])
    economic_features[feature_count * 2 + 3] = float(trigger["sell_probability"])
    armed_execution_at = datetime.fromisoformat(
        str(candidate["candidate_armed_execution_at"])
    )
    new_entry_at = datetime.fromisoformat(str(trigger["execution_at"]))
    candidate_age_minutes = (new_entry_at - armed_execution_at).total_seconds() / 60.0
    volatility_scale_pct = max(float(trigger["volatility_scale_pct"]), 1e-6)
    economic_features[feature_count * 2 + 4] = candidate_age_minutes
    economic_features[-1] = volatility_scale_pct
    timed = dict(candidate)
    timed.update(
        {
            "entry_at": new_entry_at.isoformat(),
            "entry_price": float(trigger["execution_price"]),
            "economic_features": [round(value, 8) for value in economic_features],
            "candidate_age_minutes": round(candidate_age_minutes, 3),
            "volatility_scale_pct": round(volatility_scale_pct, 8),
            "entry_timing_arm": arm,
            "entry_timing_max_wait_minutes": int(max_wait_minutes),
            "entry_timing_source_entry_at": candidate["entry_at"],
            "entry_timing_trigger_observed_at": trigger["observed_at"],
            "entry_timing_delay_minutes": round(
                (new_entry_at - source_entry_at).total_seconds() / 60.0, 3
            ),
            "_economic_path": remaining_path,
        }
    )
    return timed


def _build_recovery_entry_timing_oos_rows(
    candidate: dict[str, Any],
    *,
    control_episode: dict[str, Any],
    policy: dict[str, float],
    cost_pct: float,
    recovery_models: tuple[Any, Any, Any | None, float],
    recovery_fit_max_date: str,
) -> list[dict[str, Any]]:
    source_opportunity_id = "|".join(_entry_identity(control_episode))
    control = dict(control_episode)
    control.update(
        {
            "entry_timing_arm": "next_open_control",
            "entry_timing_max_wait_minutes": 0,
            "entry_timing_source_entry_at": control_episode["entry_at"],
            "entry_timing_label_oos": True,
            "entry_timing_exit_policy": "recovery_only",
            "entry_timing_recovery_fit_max_date": recovery_fit_max_date,
            "entry_timing_source_opportunity_id": source_opportunity_id,
        }
    )
    rows = [control]
    for arm in RECOVERY_ENTRY_TIMING_ARMS:
        for max_wait_minutes in RECOVERY_ENTRY_TIMING_MAX_WAIT_MINUTES:
            timed_candidate = _derive_recovery_entry_timing_candidate(
                candidate,
                arm=arm,
                max_wait_minutes=max_wait_minutes,
            )
            if timed_candidate is None:
                continue
            episode = _simulate_recovery_aware_candidate(
                timed_candidate,
                policy=policy,
                cost_pct=cost_pct,
                recovery_models=recovery_models,
                force_trailing=False,
            )
            episode.update(
                {
                    "entry_timing_label_oos": True,
                    "entry_timing_exit_policy": "recovery_only",
                    "entry_timing_recovery_fit_max_date": recovery_fit_max_date,
                    "entry_timing_source_opportunity_id": source_opportunity_id,
                }
            )
            rows.append(episode)
    return rows


def _fit_recovery_entry_timing_policy(
    prior_timing_rows: Sequence[dict[str, Any]],
    *,
    lane: str,
) -> dict[str, Any] | None:
    lane_rows = [
        row for row in prior_timing_rows if row.get("pairability_lane") == lane
    ]
    control_rows = [
        row for row in lane_rows if row.get("entry_timing_arm") == "next_open_control"
    ]
    dates = sorted({date.fromisoformat(str(row["trade_date"])) for row in control_rows})
    if (
        len(dates) < RECOVERY_ENTRY_TIMING_MIN_HISTORY_DATES
        or len(control_rows) < RECOVERY_ENTRY_TIMING_MIN_CONTROL_EPISODES
    ):
        return None
    if any(
        not row.get("entry_timing_label_oos")
        or row.get("entry_timing_exit_policy") != "recovery_only"
        or date.fromisoformat(str(row["entry_timing_recovery_fit_max_date"]))
        >= date.fromisoformat(str(row["trade_date"]))
        for row in lane_rows
    ):
        raise ValueError("timing history must contain prior OOS recovery-only rows")
    control_nonoverlap = _non_overlapping_candidates(control_rows, selected_only=False)
    opportunity_floor = max(
        1,
        math.ceil(
            len(control_nonoverlap) * RECOVERY_ENTRY_TIMING_OPPORTUNITY_RETENTION
        ),
    )
    grid: list[dict[str, Any]] = []
    for arm in RECOVERY_ENTRY_TIMING_ARMS:
        for max_wait_minutes in RECOVERY_ENTRY_TIMING_MAX_WAIT_MINUTES:
            arm_rows = [
                row
                for row in lane_rows
                if row.get("entry_timing_arm") == arm
                and int(row.get("entry_timing_max_wait_minutes", -1))
                == max_wait_minutes
            ]
            arm_nonoverlap = _non_overlapping_candidates(arm_rows, selected_only=False)
            control_by_date: dict[str, list[dict[str, Any]]] = defaultdict(list)
            arm_by_date: dict[str, list[dict[str, Any]]] = defaultdict(list)
            for row in control_nonoverlap:
                control_by_date[str(row["trade_date"])].append(row)
            for row in arm_nonoverlap:
                arm_by_date[str(row["trade_date"])].append(row)
            capacity_adjusted: list[dict[str, Any]] = []
            fallback_dates: list[str] = []
            for trade_date, date_control in sorted(control_by_date.items()):
                date_arm = arm_by_date.get(trade_date, [])
                date_floor = max(
                    1,
                    math.ceil(
                        len(date_control) * RECOVERY_ENTRY_TIMING_OPPORTUNITY_RETENTION
                    ),
                )
                if len(date_arm) < date_floor:
                    capacity_adjusted.extend(date_control)
                    fallback_dates.append(trade_date)
                else:
                    capacity_adjusted.extend(date_arm)
            summary = _summary(capacity_adjusted, source_quality_passed=True)
            path = _recovery_path_diagnostics(capacity_adjusted)
            grid.append(
                {
                    "arm": arm,
                    "max_wait_minutes": max_wait_minutes,
                    "source_candidate_count": len(arm_rows),
                    "raw_timed_nonoverlap_count": len(arm_nonoverlap),
                    "nonoverlap_count": len(capacity_adjusted),
                    "opportunity_floor_count": opportunity_floor,
                    "opportunity_retention_passed": len(capacity_adjusted)
                    >= opportunity_floor,
                    "capacity_fallback_date_count": len(fallback_dates),
                    "capacity_fallback_dates": fallback_dates,
                    "summary": summary,
                    "compounded_net_return_pct": path["compounded_net_return_pct"],
                    "avg_mae_pct": path.get("avg_mae_pct"),
                }
            )
    eligible = [row for row in grid if row["opportunity_retention_passed"]]
    if not eligible:
        return {
            "status": "no_timing_policy_meets_opportunity_floor",
            "lane": lane,
            "history_dates": [item.isoformat() for item in dates],
            "control_nonoverlap_count": len(control_nonoverlap),
            "opportunity_floor_count": opportunity_floor,
            "grid": grid,
        }
    selected = max(
        eligible,
        key=lambda row: (
            float(row["summary"]["equal_weight_avg_profit_pct"]),
            float(row["compounded_net_return_pct"]),
            int(row["nonoverlap_count"]),
            -int(row["max_wait_minutes"]),
        ),
    )
    arm_policies = {}
    for arm in RECOVERY_ENTRY_TIMING_ARMS:
        arm_eligible = [row for row in eligible if row["arm"] == arm]
        if arm_eligible:
            arm_policies[arm] = max(
                arm_eligible,
                key=lambda row: (
                    float(row["summary"]["equal_weight_avg_profit_pct"]),
                    float(row["compounded_net_return_pct"]),
                    int(row["nonoverlap_count"]),
                    -int(row["max_wait_minutes"]),
                ),
            )
    return {
        "status": "prior_policy_selected",
        "lane": lane,
        "history_dates": [item.isoformat() for item in dates],
        "fit_max_date": dates[-1].isoformat(),
        "history_control_episode_count": len(control_rows),
        "control_nonoverlap_count": len(control_nonoverlap),
        "opportunity_floor_count": opportunity_floor,
        "selected_policy": {
            "arm": selected["arm"],
            "max_wait_minutes": selected["max_wait_minutes"],
        },
        "arm_policies": {
            arm: {
                "arm": row["arm"],
                "max_wait_minutes": row["max_wait_minutes"],
            }
            for arm, row in arm_policies.items()
        },
        "grid": grid,
    }


def _missed_timing_mfe_pct(candidate: dict[str, Any]) -> float | None:
    prices = [
        float(point["reference_price"])
        for point in candidate["_economic_path"]
        if point.get("reference_price") is not None
    ]
    if not prices:
        return None
    return round((max(prices) / float(candidate["entry_price"]) - 1.0) * 100.0, 6)


def _evaluate_recovery_entry_timing_policy(
    raw_candidates: Sequence[dict[str, Any]],
    control_episodes: Sequence[dict[str, Any]],
    *,
    timing_policy: dict[str, Any],
    recovery_policy: dict[str, float],
    cost_pct: float,
    recovery_models: tuple[Any, Any, Any | None, float],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    candidate_by_entry = {_entry_identity(row): row for row in raw_candidates}
    control_nonoverlap = _non_overlapping_candidates(
        control_episodes,
        selected_only=True,
        selection_key="recovery_entry_selected",
    )
    raw_selected = [
        row for row in control_episodes if row.get("recovery_entry_selected")
    ]
    selected_policy = timing_policy["selected_policy"]
    timed_candidates: list[dict[str, Any]] = []
    missed_mfe: list[float] = []
    for control in raw_selected:
        raw = candidate_by_entry[_entry_identity(control)]
        timed = _derive_recovery_entry_timing_candidate(
            raw,
            arm=str(selected_policy["arm"]),
            max_wait_minutes=int(selected_policy["max_wait_minutes"]),
        )
        if timed is None:
            missed = _missed_timing_mfe_pct(raw)
            if missed is not None:
                missed_mfe.append(missed)
            continue
        episode = _simulate_recovery_aware_candidate(
            timed,
            policy=recovery_policy,
            cost_pct=cost_pct,
            recovery_models=recovery_models,
            force_trailing=False,
        )
        episode.update(
            {
                "entry_timing_policy_fit_max_date": timing_policy["fit_max_date"],
                "entry_timing_policy_oos": True,
            }
        )
        timed_candidates.append(episode)
    timed_nonoverlap = _non_overlapping_candidates(
        timed_candidates, selected_only=False
    )
    floor = (
        max(
            1,
            math.ceil(
                len(control_nonoverlap) * RECOVERY_ENTRY_TIMING_OPPORTUNITY_RETENTION
            ),
        )
        if control_nonoverlap
        else 0
    )
    fallback_applied = bool(control_nonoverlap and len(timed_nonoverlap) < floor)
    selected = [
        dict(row)
        for row in (control_nonoverlap if fallback_applied else timed_nonoverlap)
    ]
    for row in selected:
        row.update(
            {
                "entry_timing_capacity_fallback_selected": fallback_applied,
                "entry_timing_selection_reason": (
                    "raw_recovery_capacity_floor_fallback"
                    if fallback_applied
                    else "prior_selected_causal_timing"
                ),
            }
        )
    return selected, {
        "raw_nonoverlap_count": len(control_nonoverlap),
        "timed_nonoverlap_count": len(timed_nonoverlap),
        "opportunity_floor_count": floor,
        "capacity_fallback_applied": fallback_applied,
        "final_nonoverlap_count": len(selected),
        "raw_selected_candidate_count": len(raw_selected),
        "missed_entry_count": len(raw_selected) - len(timed_candidates),
        "missed_entry_avg_post_control_mfe_pct": (
            round(statistics.fmean(missed_mfe), 6) if missed_mfe else None
        ),
        "missed_entry_max_post_control_mfe_pct": (
            max(missed_mfe) if missed_mfe else None
        ),
    }


def _timing_policy_feature_tail(timing_policy: dict[str, Any]) -> list[float]:
    selected = timing_policy["selected_policy"]
    arm = str(selected["arm"])
    max_wait_minutes = int(selected["max_wait_minutes"])
    return [
        *(float(arm == candidate_arm) for candidate_arm in RECOVERY_ENTRY_TIMING_ARMS),
        max_wait_minutes / 20.0,
    ]


def _candidate_timing_base_features(
    candidate: dict[str, Any], timing_policy: dict[str, Any]
) -> list[float]:
    return [
        *(float(value) for value in candidate["economic_features"]),
        *_timing_policy_feature_tail(timing_policy),
    ]


def _candidate_timing_trigger_features(
    candidate: dict[str, Any],
    timed_candidate: dict[str, Any],
    timing_policy: dict[str, Any],
) -> list[float]:
    feature_count = len(FEATURE_NAMES)
    timed_features = [float(value) for value in timed_candidate["economic_features"]]
    return [
        *_candidate_timing_base_features(candidate, timing_policy),
        *timed_features[feature_count : feature_count * 2],
        timed_features[feature_count * 2 + 2],
        timed_features[feature_count * 2 + 3],
        float(timed_candidate["volatility_scale_pct"]),
        float(timed_candidate["entry_timing_delay_minutes"]) / 20.0,
    ]


def _build_candidate_timing_utility_pair(
    candidate: dict[str, Any],
    *,
    control_episode: dict[str, Any],
    timing_policy: dict[str, Any],
    recovery_policy: dict[str, float],
    cost_pct: float,
    recovery_models: tuple[Any, Any, Any | None, float],
    recovery_fit_max_date: str,
) -> dict[str, Any]:
    trade_date = date.fromisoformat(str(control_episode["trade_date"]))
    if date.fromisoformat(str(timing_policy["fit_max_date"])) >= trade_date:
        raise ValueError("candidate timing pair policy must predate its label")
    if date.fromisoformat(str(recovery_fit_max_date)) >= trade_date:
        raise ValueError("candidate timing pair recovery model must predate its label")
    selected_policy = timing_policy["selected_policy"]
    timed_candidate = _derive_recovery_entry_timing_candidate(
        candidate,
        arm=str(selected_policy["arm"]),
        max_wait_minutes=int(selected_policy["max_wait_minutes"]),
    )
    timed_episode: dict[str, Any] | None = None
    if timed_candidate is not None:
        timed_episode = _simulate_recovery_aware_candidate(
            timed_candidate,
            policy=recovery_policy,
            cost_pct=cost_pct,
            recovery_models=recovery_models,
            force_trailing=False,
        )
    timing_net_profit_pct = (
        float(timed_episode["net_profit_pct"]) if timed_episode is not None else 0.0
    )
    control_net_profit_pct = float(control_episode["net_profit_pct"])
    return {
        "trade_date": control_episode["trade_date"],
        "venue": control_episode["venue"],
        "session": control_episode["session"],
        "pairability_lane": control_episode["pairability_lane"],
        "source_entry_at": control_episode["entry_at"],
        "source_opportunity_id": "|".join(_entry_identity(control_episode)),
        "timing_arm": selected_policy["arm"],
        "timing_max_wait_minutes": int(selected_policy["max_wait_minutes"]),
        "timing_available": timed_episode is not None,
        "timing_entry_at": (
            timed_episode["entry_at"] if timed_episode is not None else None
        ),
        "timing_delay_minutes": (
            timed_candidate["entry_timing_delay_minutes"]
            if timed_candidate is not None
            else None
        ),
        "control_net_profit_pct": round(control_net_profit_pct, 6),
        "timing_net_profit_pct": round(timing_net_profit_pct, 6),
        "timing_incremental_net_profit_pct": round(
            timing_net_profit_pct - control_net_profit_pct, 6
        ),
        "baseline_features": _candidate_timing_base_features(candidate, timing_policy),
        "trigger_features": (
            _candidate_timing_trigger_features(
                candidate, timed_candidate, timing_policy
            )
            if timed_candidate is not None
            else None
        ),
        "candidate_timing_pair_oos": True,
        "candidate_timing_exit_policy": "recovery_only",
        "candidate_timing_policy_fit_max_date": timing_policy["fit_max_date"],
        "candidate_timing_recovery_fit_max_date": recovery_fit_max_date,
    }


def _fit_candidate_timing_utility_models(
    prior_pairs: Sequence[dict[str, Any]],
    *,
    lane: str,
) -> (
    tuple[
        HistGradientBoostingRegressor,
        HistGradientBoostingRegressor,
        dict[str, Any],
    ]
    | None
):
    lane_pairs = [row for row in prior_pairs if row.get("pairability_lane") == lane]
    dates = sorted({date.fromisoformat(str(row["trade_date"])) for row in lane_pairs})
    trigger_pairs = [row for row in lane_pairs if row.get("timing_available")]
    if (
        len(dates) < RECOVERY_ENTRY_TIMING_UTILITY_MIN_HISTORY_DATES
        or len(lane_pairs) < RECOVERY_ENTRY_TIMING_UTILITY_MIN_PAIRS
        or len(trigger_pairs) < RECOVERY_ENTRY_TIMING_UTILITY_MIN_TRIGGER_PAIRS
    ):
        return None
    if any(
        not row.get("candidate_timing_pair_oos")
        or row.get("candidate_timing_exit_policy") != "recovery_only"
        or date.fromisoformat(str(row["candidate_timing_policy_fit_max_date"]))
        >= date.fromisoformat(str(row["trade_date"]))
        or date.fromisoformat(str(row["candidate_timing_recovery_fit_max_date"]))
        >= date.fromisoformat(str(row["trade_date"]))
        for row in lane_pairs
    ):
        raise ValueError("candidate timing utility history must be prior OOS")
    baseline_model = HistGradientBoostingRegressor(
        loss="squared_error",
        learning_rate=0.05,
        max_iter=80,
        max_leaf_nodes=9,
        min_samples_leaf=6,
        l2_regularization=2.0,
        random_state=0,
    )
    baseline_model.fit(
        np.asarray([row["baseline_features"] for row in lane_pairs], dtype=float),
        np.asarray(
            [float(row["timing_incremental_net_profit_pct"]) for row in lane_pairs],
            dtype=float,
        ),
    )
    trigger_model = HistGradientBoostingRegressor(
        loss="squared_error",
        learning_rate=0.05,
        max_iter=80,
        max_leaf_nodes=9,
        min_samples_leaf=6,
        l2_regularization=2.0,
        random_state=0,
    )
    trigger_model.fit(
        np.asarray([row["trigger_features"] for row in trigger_pairs], dtype=float),
        np.asarray(
            [float(row["timing_net_profit_pct"]) for row in trigger_pairs],
            dtype=float,
        ),
    )
    return (
        baseline_model,
        trigger_model,
        {
            "lane": lane,
            "history_dates": [item.isoformat() for item in dates],
            "fit_max_date": dates[-1].isoformat(),
            "history_pair_count": len(lane_pairs),
            "history_trigger_pair_count": len(trigger_pairs),
            "avg_timing_incremental_net_profit_pct": round(
                statistics.fmean(
                    float(row["timing_incremental_net_profit_pct"])
                    for row in lane_pairs
                ),
                6,
            ),
            "avg_trigger_net_profit_pct": round(
                statistics.fmean(
                    float(row["timing_net_profit_pct"]) for row in trigger_pairs
                ),
                6,
            ),
            "selection_policy": (
                "baseline_predicted_incremental_ev_gt_zero_with_causal_3_to_1_"
                "enter_now_budget_then_trigger_predicted_net_ev_gt_zero"
            ),
        },
    )


def _build_trigger_utility_prediction_rows(
    pairs: Sequence[dict[str, Any]],
    *,
    trigger_model: HistGradientBoostingRegressor,
    model_fit_max_date: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    fit_date = date.fromisoformat(str(model_fit_max_date))
    for pair in pairs:
        if not pair.get("timing_available"):
            continue
        trade_date = date.fromisoformat(str(pair["trade_date"]))
        if fit_date >= trade_date:
            raise ValueError("trigger prediction model must predate its OOS label")
        trigger_features = pair.get("trigger_features")
        if not isinstance(trigger_features, list):
            raise ValueError("timing-available pair is missing trigger features")
        predicted = float(
            trigger_model.predict(np.asarray([trigger_features], dtype=float))[0]
        )
        realized = float(pair["timing_net_profit_pct"])
        rows.append(
            {
                "trade_date": pair["trade_date"],
                "venue": pair["venue"],
                "session": pair["session"],
                "pairability_lane": pair["pairability_lane"],
                "source_entry_at": pair["source_entry_at"],
                "timing_entry_at": pair["timing_entry_at"],
                "raw_predicted_trigger_net_ev_pct": round(predicted, 6),
                "realized_trigger_net_profit_pct": round(realized, 6),
                "trigger_prediction_residual_pct": round(realized - predicted, 6),
                "trigger_prediction_model_fit_max_date": model_fit_max_date,
                "candidate_timing_policy_fit_max_date": pair[
                    "candidate_timing_policy_fit_max_date"
                ],
                "candidate_timing_recovery_fit_max_date": pair[
                    "candidate_timing_recovery_fit_max_date"
                ],
                "trigger_prediction_oos": True,
                "trigger_prediction_exit_policy": "recovery_only",
            }
        )
    return rows


def _fit_trigger_utility_calibration(
    prior_predictions: Sequence[dict[str, Any]],
    *,
    lane: str,
) -> dict[str, Any] | None:
    lane_rows = [
        row for row in prior_predictions if row.get("pairability_lane") == lane
    ]
    dates = sorted({date.fromisoformat(str(row["trade_date"])) for row in lane_rows})
    if (
        len(dates) < TRIGGER_UTILITY_CALIBRATION_MIN_HISTORY_DATES
        or len(lane_rows) < TRIGGER_UTILITY_CALIBRATION_MIN_PAIRS
    ):
        return None
    if any(
        not row.get("trigger_prediction_oos")
        or row.get("trigger_prediction_exit_policy") != "recovery_only"
        or date.fromisoformat(str(row["trigger_prediction_model_fit_max_date"]))
        >= date.fromisoformat(str(row["trade_date"]))
        or date.fromisoformat(str(row["candidate_timing_policy_fit_max_date"]))
        >= date.fromisoformat(str(row["trade_date"]))
        or date.fromisoformat(str(row["candidate_timing_recovery_fit_max_date"]))
        >= date.fromisoformat(str(row["trade_date"]))
        for row in lane_rows
    ):
        raise ValueError("trigger calibration history must be prior OOS")
    predicted = np.asarray(
        [float(row["raw_predicted_trigger_net_ev_pct"]) for row in lane_rows],
        dtype=float,
    )
    realized = np.asarray(
        [float(row["realized_trigger_net_profit_pct"]) for row in lane_rows],
        dtype=float,
    )
    shrinkage_weight = len(lane_rows) / (
        len(lane_rows) + TRIGGER_UTILITY_CALIBRATION_SHRINKAGE_PRIOR
    )
    predicted_variance = float(np.var(predicted))
    raw_rank_slope = (
        float(np.cov(predicted, realized, ddof=0)[0, 1] / predicted_variance)
        if predicted_variance > 1e-12
        else 1.0
    )
    rank_slope = min(
        2.0,
        max(0.0, 1.0 + shrinkage_weight * (raw_rank_slope - 1.0)),
    )
    residual_intercept = shrinkage_weight * float(
        np.mean(realized - rank_slope * predicted)
    )
    recent_dates = set(dates[-3:])
    recent_rows = [
        row
        for row in lane_rows
        if date.fromisoformat(str(row["trade_date"])) in recent_dates
    ]
    recent_residual = statistics.fmean(
        float(row["realized_trigger_net_profit_pct"])
        - (
            residual_intercept
            + rank_slope * float(row["raw_predicted_trigger_net_ev_pct"])
        )
        for row in recent_rows
    )
    bounded_recent_drift = max(
        -0.5,
        min(0.5, shrinkage_weight * 0.25 * recent_residual),
    )
    return {
        "lane": lane,
        "history_dates": [item.isoformat() for item in dates],
        "fit_max_date": dates[-1].isoformat(),
        "history_pair_count": len(lane_rows),
        "shrinkage_weight": round(shrinkage_weight, 6),
        "raw_rank_slope": round(raw_rank_slope, 6),
        "calibrated_rank_slope": round(rank_slope, 6),
        "residual_intercept_pct": round(residual_intercept, 6),
        "bounded_recent_drift_pct": round(bounded_recent_drift, 6),
        "raw_prediction_mean_pct": round(float(np.mean(predicted)), 6),
        "realized_mean_pct": round(float(np.mean(realized)), 6),
        "selection_policy": (
            "calibrated_mean_gt_zero_with_causal_three_entry_to_one_skip_"
            "bounded_exploration"
        ),
    }


def _calibrated_trigger_net_ev(
    raw_prediction: float, calibration: dict[str, Any]
) -> float:
    return (
        float(calibration["residual_intercept_pct"])
        + float(calibration["bounded_recent_drift_pct"])
        + float(calibration["calibrated_rank_slope"]) * float(raw_prediction)
    )


def _trigger_utility_prediction_diagnostics(
    rows: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    def summarize(items: Sequence[dict[str, Any]]) -> dict[str, Any]:
        if not items:
            return {
                "sample_count": 0,
                "avg_raw_predicted_ev_pct": None,
                "avg_realized_ev_pct": None,
                "avg_residual_pct": None,
            }
        return {
            "sample_count": len(items),
            "avg_raw_predicted_ev_pct": round(
                statistics.fmean(
                    float(row["raw_predicted_trigger_net_ev_pct"]) for row in items
                ),
                6,
            ),
            "avg_realized_ev_pct": round(
                statistics.fmean(
                    float(row["realized_trigger_net_profit_pct"]) for row in items
                ),
                6,
            ),
            "avg_residual_pct": round(
                statistics.fmean(
                    float(row["trigger_prediction_residual_pct"]) for row in items
                ),
                6,
            ),
        }

    ordered = sorted(
        rows, key=lambda row: float(row["raw_predicted_trigger_net_ev_pct"])
    )
    rank_bins: list[dict[str, Any]] = []
    for bin_index in range(4):
        start = len(ordered) * bin_index // 4
        end = len(ordered) * (bin_index + 1) // 4
        bin_rows = ordered[start:end]
        if bin_rows:
            rank_bins.append(
                {
                    "bin": f"rank_q{bin_index + 1}",
                    **summarize(bin_rows),
                }
            )
    return {
        "role": "post_oos_diagnostic_only",
        **summarize(rows),
        "rank_bins": rank_bins,
        "lane_summaries": {
            lane: summarize(
                [row for row in rows if row.get("pairability_lane") == lane]
            )
            for lane in ("weak_reversal", "bullish_transition")
        },
        "date_drift": [
            {
                "trade_date": trade_date,
                **summarize(
                    [row for row in rows if str(row["trade_date"]) == trade_date]
                ),
            }
            for trade_date in sorted({str(row["trade_date"]) for row in rows})
        ],
        "forbidden_use": "same_date_trigger_calibration_or_threshold_change",
    }


def _evaluate_candidate_timing_utility(
    raw_candidates: Sequence[dict[str, Any]],
    control_episodes: Sequence[dict[str, Any]],
    *,
    timing_policy: dict[str, Any],
    recovery_policy: dict[str, float],
    cost_pct: float,
    recovery_models: tuple[Any, Any, Any | None, float],
    baseline_model: HistGradientBoostingRegressor,
    trigger_model: HistGradientBoostingRegressor,
    model_fit_max_date: str,
    prior_enter_now_count: int = 0,
    prior_wait_count: int = 0,
    trigger_calibration: dict[str, Any] | None = None,
    prior_trigger_enter_count: int = 0,
    prior_trigger_skip_count: int = 0,
    wait_budget_enter_per_wait: int = 3,
    wait_budget_arm: str | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    if wait_budget_enter_per_wait < 1:
        raise ValueError("wait budget enter-per-wait ratio must be positive")
    if wait_budget_arm is not None and WAIT_BUDGET_ARMS.get(wait_budget_arm) != int(
        wait_budget_enter_per_wait
    ):
        raise ValueError("wait budget arm and ratio must match the declared contract")
    candidate_by_entry = {_entry_identity(row): row for row in raw_candidates}
    control_nonoverlap = _non_overlapping_candidates(
        control_episodes,
        selected_only=True,
        selection_key="recovery_entry_selected",
    )
    proposals: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    immediate_count = 0
    wait_count = 0
    budget_immediate_count = int(prior_enter_now_count)
    budget_wait_count = int(prior_wait_count)
    trigger_available_count = 0
    trigger_enter_count = 0
    trigger_skip_count = 0
    forced_trigger_exploration_count = 0
    budget_trigger_enter_count = int(prior_trigger_enter_count)
    budget_trigger_skip_count = int(prior_trigger_skip_count)
    missed_mfe: list[float] = []
    selected_policy = timing_policy["selected_policy"]
    for control in sorted(control_nonoverlap, key=lambda row: str(row["entry_at"])):
        raw = candidate_by_entry[_entry_identity(control)]
        baseline_features = _candidate_timing_base_features(raw, timing_policy)
        predicted_incremental_ev = float(
            baseline_model.predict(np.asarray([baseline_features], dtype=float))[0]
        )
        wait_budget_available = budget_immediate_count >= int(
            wait_budget_enter_per_wait
        ) * (budget_wait_count + 1)
        choose_wait = bool(predicted_incremental_ev > 0.0 and wait_budget_available)
        decision = {
            "trade_date": control["trade_date"],
            "venue": control["venue"],
            "session": control["session"],
            "pairability_lane": control["pairability_lane"],
            "source_entry_at": control["entry_at"],
            "predicted_timing_incremental_ev_pct": round(predicted_incremental_ev, 6),
            "wait_budget_available": wait_budget_available,
            "baseline_action": "wait" if choose_wait else "enter_now",
            "timing_arm": selected_policy["arm"],
            "timing_max_wait_minutes": int(selected_policy["max_wait_minutes"]),
            "candidate_timing_utility_model_fit_max_date": model_fit_max_date,
            "candidate_timing_utility_oos": True,
            "wait_budget_enter_per_wait": int(wait_budget_enter_per_wait),
        }
        if wait_budget_arm is not None:
            decision.update(
                {
                    "wait_budget_arm": wait_budget_arm,
                    "wait_budget_oos": True,
                    "wait_budget_exit_policy": "recovery_only",
                }
            )
        if trigger_calibration is not None:
            trigger_calibration_fit_max_date = str(trigger_calibration["fit_max_date"])
            if date.fromisoformat(
                trigger_calibration_fit_max_date
            ) >= date.fromisoformat(str(control["trade_date"])):
                raise ValueError(
                    "trigger utility calibration must predate evaluation date"
                )
            decision.update(
                {
                    "trigger_utility_calibration_fit_max_date": (
                        trigger_calibration_fit_max_date
                    ),
                    "trigger_utility_calibration_oos": True,
                }
            )
        if not choose_wait:
            immediate_count += 1
            budget_immediate_count += 1
            episode = dict(control)
            episode.update(
                {
                    **decision,
                    "candidate_timing_utility_action": "enter_now",
                    "predicted_trigger_net_ev_pct": None,
                }
            )
            proposals.append(episode)
            decisions.append(decision)
            continue
        wait_count += 1
        budget_wait_count += 1
        timed = _derive_recovery_entry_timing_candidate(
            raw,
            arm=str(selected_policy["arm"]),
            max_wait_minutes=int(selected_policy["max_wait_minutes"]),
        )
        if timed is None:
            missed = _missed_timing_mfe_pct(raw)
            if missed is not None:
                missed_mfe.append(missed)
            decision.update(
                {
                    "trigger_action": "no_trigger_no_trade",
                    "predicted_trigger_net_ev_pct": None,
                }
            )
            decisions.append(decision)
            continue
        trigger_available_count += 1
        trigger_features = _candidate_timing_trigger_features(raw, timed, timing_policy)
        raw_predicted_trigger_net_ev = float(
            trigger_model.predict(np.asarray([trigger_features], dtype=float))[0]
        )
        predicted_trigger_net_ev = (
            _calibrated_trigger_net_ev(
                raw_predicted_trigger_net_ev, trigger_calibration
            )
            if trigger_calibration is not None
            else raw_predicted_trigger_net_ev
        )
        trigger_skip_budget_available = budget_trigger_enter_count >= 3 * (
            budget_trigger_skip_count + 1
        )
        force_trigger_exploration = bool(
            trigger_calibration is not None
            and predicted_trigger_net_ev <= 0.0
            and not trigger_skip_budget_available
        )
        if predicted_trigger_net_ev <= 0.0 and not force_trigger_exploration:
            trigger_skip_count += 1
            budget_trigger_skip_count += 1
            decision.update(
                {
                    "trigger_action": "skip_nonpositive_predicted_net_ev",
                    "raw_predicted_trigger_net_ev_pct": round(
                        raw_predicted_trigger_net_ev, 6
                    ),
                    "predicted_trigger_net_ev_pct": round(predicted_trigger_net_ev, 6),
                    "trigger_skip_budget_available": (trigger_skip_budget_available),
                }
            )
            decisions.append(decision)
            continue
        trigger_enter_count += 1
        budget_trigger_enter_count += 1
        if force_trigger_exploration:
            forced_trigger_exploration_count += 1
        episode = _simulate_recovery_aware_candidate(
            timed,
            policy=recovery_policy,
            cost_pct=cost_pct,
            recovery_models=recovery_models,
            force_trailing=False,
        )
        decision.update(
            {
                "trigger_action": "timed_entry",
                "raw_predicted_trigger_net_ev_pct": round(
                    raw_predicted_trigger_net_ev, 6
                ),
                "predicted_trigger_net_ev_pct": round(predicted_trigger_net_ev, 6),
                "trigger_skip_budget_available": trigger_skip_budget_available,
                "trigger_entry_reason": (
                    "bounded_trigger_exploration"
                    if force_trigger_exploration
                    else "positive_predicted_trigger_net_ev"
                ),
                "timing_entry_at": episode["entry_at"],
            }
        )
        episode.update(
            {
                **decision,
                "candidate_timing_utility_action": "timed_entry",
            }
        )
        proposals.append(episode)
        decisions.append(decision)
    selected = _non_overlapping_candidates(proposals, selected_only=False)
    floor = (
        max(
            1,
            math.ceil(
                len(control_nonoverlap)
                * RECOVERY_ENTRY_TIMING_UTILITY_OPPORTUNITY_RETENTION
            ),
        )
        if control_nonoverlap
        else 0
    )
    return (
        selected,
        decisions,
        {
            "raw_nonoverlap_count": len(control_nonoverlap),
            "opportunity_floor_count": floor,
            "final_nonoverlap_count": len(selected),
            "opportunity_retention_passed": len(selected) >= floor,
            "enter_now_decision_count": immediate_count,
            "wait_decision_count": wait_count,
            "prior_enter_now_decision_count": int(prior_enter_now_count),
            "prior_wait_decision_count": int(prior_wait_count),
            "trigger_available_count": trigger_available_count,
            "trigger_enter_count": trigger_enter_count,
            "trigger_skip_or_missing_count": wait_count - trigger_enter_count,
            "trigger_model_skip_count": trigger_skip_count,
            "forced_trigger_exploration_count": forced_trigger_exploration_count,
            "prior_trigger_enter_count": int(prior_trigger_enter_count),
            "prior_trigger_skip_count": int(prior_trigger_skip_count),
            "wait_budget_enter_per_wait": int(wait_budget_enter_per_wait),
            "wait_budget_arm": wait_budget_arm,
            "missed_trigger_post_control_mfe_avg_pct": (
                round(statistics.fmean(missed_mfe), 6) if missed_mfe else None
            ),
            "missed_trigger_post_control_mfe_max_pct": (
                max(missed_mfe) if missed_mfe else None
            ),
        },
    )


def _prediction_calibration_diagnostics(
    episodes: Sequence[dict[str, Any]],
    *,
    prediction_key: str,
) -> dict[str, Any]:
    if not episodes:
        return {
            "role": "post_oos_diagnostic_only",
            "sample_count": 0,
            "prediction_bins": [],
            "lane_summaries": {},
            "date_drift": [],
        }

    def summarize(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
        predicted = [float(row[prediction_key]) for row in rows]
        realized = [float(row["net_profit_pct"]) for row in rows]
        return {
            "sample_count": len(rows),
            "avg_predicted_ev_pct": round(statistics.fmean(predicted), 6),
            "avg_realized_ev_pct": round(statistics.fmean(realized), 6),
            "avg_residual_pct": round(
                statistics.fmean(
                    actual - forecast
                    for actual, forecast in zip(realized, predicted, strict=True)
                ),
                6,
            ),
        }

    ordered = sorted(episodes, key=lambda row: float(row[prediction_key]))
    bins: list[dict[str, Any]] = []
    for bin_index in range(4):
        start = len(ordered) * bin_index // 4
        end = len(ordered) * (bin_index + 1) // 4
        rows = ordered[start:end]
        if not rows:
            continue
        bins.append(
            {
                "bin": f"rank_q{bin_index + 1}",
                "minimum_predicted_ev_pct": round(
                    min(float(row[prediction_key]) for row in rows), 6
                ),
                "maximum_predicted_ev_pct": round(
                    max(float(row[prediction_key]) for row in rows), 6
                ),
                **summarize(rows),
            }
        )
    lane_summaries = {
        lane: summarize(
            [row for row in episodes if row.get("pairability_lane") == lane]
        )
        for lane in ("weak_reversal", "bullish_transition")
        if any(row.get("pairability_lane") == lane for row in episodes)
    }
    date_drift = [
        {
            "trade_date": trade_date,
            **summarize(
                [row for row in episodes if str(row["trade_date"]) == trade_date]
            ),
        }
        for trade_date in sorted({str(row["trade_date"]) for row in episodes})
    ]
    return {
        "role": "post_oos_diagnostic_only",
        "forbidden_use": "same_report_threshold_or_lane_switch",
        "sample_count": len(episodes),
        "prediction_bins": bins,
        "lane_summaries": lane_summaries,
        "date_drift": date_drift,
    }


def _fit_lane_economic_first_passage_model(
    prior_candidates: Sequence[dict[str, Any]],
    *,
    lane: str,
    cost_pct: float,
) -> (
    tuple[
        HistGradientBoostingClassifier,
        HistGradientBoostingRegressor,
        dict[str, float],
        dict[str, Any],
    ]
    | None
):
    lane_candidates = [
        row for row in prior_candidates if row.get("pairability_lane") == lane
    ]
    dates = sorted(
        {date.fromisoformat(str(row["trade_date"])) for row in lane_candidates}
    )
    if len(dates) < ECONOMIC_FIRST_PASSAGE_MIN_HISTORY_DATES:
        return None
    validation_date_count = max(2, math.ceil(len(dates) * 0.25))
    fit_dates = set(dates[:-validation_date_count])
    validation_dates = set(dates[-validation_date_count:])
    validation_candidates = [
        row
        for row in lane_candidates
        if date.fromisoformat(str(row["trade_date"])) in validation_dates
    ]
    policy_results: list[dict[str, Any]] = []
    for target_multiplier in ECONOMIC_TARGET_VOL_MULTIPLIERS:
        for adverse_multiplier in ECONOMIC_ADVERSE_VOL_MULTIPLIERS:
            validation_episodes = [
                _apply_economic_first_passage_policy(
                    row,
                    target_vol_multiplier=target_multiplier,
                    adverse_vol_multiplier=adverse_multiplier,
                    cost_pct=cost_pct,
                )
                for row in validation_candidates
            ]
            non_overlapping = _non_overlapping_candidates(
                validation_episodes, selected_only=False
            )
            summary = _summary(non_overlapping, source_quality_passed=True)
            policy_results.append(
                {
                    "target_vol_multiplier": float(target_multiplier),
                    "adverse_vol_multiplier": float(adverse_multiplier),
                    "sample_count": summary["sample_count"],
                    "equal_weight_avg_profit_pct": summary[
                        "equal_weight_avg_profit_pct"
                    ],
                    "compounded_net_return_pct": _compounded_net_return_pct(
                        non_overlapping
                    ),
                    "diagnostic_win_rate_pct": summary["diagnostic_win_rate_pct"],
                }
            )
    selected_policy = max(
        policy_results,
        key=lambda row: (
            (
                float(row["equal_weight_avg_profit_pct"])
                if row["equal_weight_avg_profit_pct"] is not None
                else -math.inf
            ),
            float(row["compounded_net_return_pct"]),
            int(row["sample_count"]),
        ),
    )
    policy = {
        "target_vol_multiplier": float(selected_policy["target_vol_multiplier"]),
        "adverse_vol_multiplier": float(selected_policy["adverse_vol_multiplier"]),
    }
    prior_episodes = [
        _apply_economic_first_passage_policy(
            row,
            target_vol_multiplier=policy["target_vol_multiplier"],
            adverse_vol_multiplier=policy["adverse_vol_multiplier"],
            cost_pct=cost_pct,
        )
        for row in lane_candidates
    ]
    final_bundle = _fit_economic_first_passage_estimators(prior_episodes)
    if final_bundle is None:
        return None
    event_model, ev_model = final_bundle
    return (
        event_model,
        ev_model,
        policy,
        {
            "lane": lane,
            "history_date_count": len(dates),
            "history_episode_count": len(prior_episodes),
            "fit_dates": [item.isoformat() for item in sorted(fit_dates)],
            "validation_dates": [item.isoformat() for item in sorted(validation_dates)],
            "selected_boundary_policy": selected_policy,
            "boundary_selection_policy": (
                "chronological_prior_validation_max_ev_then_cumulative_net"
            ),
            "event_counts": dict(
                sorted(
                    Counter(
                        row["economic_first_passage_event"] for row in prior_episodes
                    ).items()
                )
            ),
            "policy_grid": policy_results,
            "selection_policy": "direct_predicted_cost_adjusted_ev_gt_zero",
        },
    )


def _economic_first_passage_decision(
    selected_summary: dict[str, Any],
    control_summary: dict[str, Any],
    *,
    sample_floor_passed: bool,
    source_quality_passed: bool,
) -> str:
    if not source_quality_passed:
        return "source_quality_blocked"
    if not sample_floor_passed:
        return "insufficient_coverage_dates"
    selected_ev = selected_summary.get("source_quality_adjusted_ev_pct")
    control_ev = control_summary.get("source_quality_adjusted_ev_pct")
    if selected_ev is None:
        return "no_incremental_predictive_value"
    if float(selected_ev) > 0.0:
        return "economic_first_passage_oos_positive"
    if control_ev is not None and float(selected_ev) > float(control_ev):
        return "economic_first_passage_improved_but_negative"
    return "no_incremental_predictive_value"


def _economic_path_diagnostics(
    episodes: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    if not episodes:
        return {
            "sample_count": 0,
            "compounded_net_return_pct": 0.0,
            "avg_mfe_pct": None,
            "avg_mae_pct": None,
            "avg_post_entry_session_mfe_pct": None,
            "avg_post_entry_session_mae_pct": None,
            "post_entry_session_mfe_ge_0_5_count": 0,
            "post_entry_session_mfe_ge_0_5_pct": None,
            "adverse_first_then_later_favorable_count": 0,
            "adverse_first_then_later_favorable_pct": None,
            "median_event_duration_minutes": None,
            "event_counts": {},
        }
    mfe_ge_half_count = sum(
        float(row["post_entry_session_mfe_pct"]) >= 0.5 for row in episodes
    )
    adverse_then_favorable_count = sum(
        row["economic_first_passage_event"] == "adverse_first_passage"
        and float(row["post_entry_session_mfe_pct"])
        >= float(row["favorable_boundary_pct"])
        for row in episodes
    )
    return {
        "sample_count": len(episodes),
        "compounded_net_return_pct": _compounded_net_return_pct(episodes),
        "avg_mfe_pct": round(
            statistics.fmean(float(row["mfe_pct"]) for row in episodes), 6
        ),
        "avg_mae_pct": round(
            statistics.fmean(float(row["mae_pct"]) for row in episodes), 6
        ),
        "avg_post_entry_session_mfe_pct": round(
            statistics.fmean(
                float(row["post_entry_session_mfe_pct"]) for row in episodes
            ),
            6,
        ),
        "avg_post_entry_session_mae_pct": round(
            statistics.fmean(
                float(row["post_entry_session_mae_pct"]) for row in episodes
            ),
            6,
        ),
        "post_entry_session_mfe_ge_0_5_count": mfe_ge_half_count,
        "post_entry_session_mfe_ge_0_5_pct": round(
            mfe_ge_half_count / len(episodes) * 100.0, 3
        ),
        "adverse_first_then_later_favorable_count": adverse_then_favorable_count,
        "adverse_first_then_later_favorable_pct": round(
            adverse_then_favorable_count / len(episodes) * 100.0, 3
        ),
        "median_event_duration_minutes": round(
            statistics.median(float(row["event_duration_minutes"]) for row in episodes),
            3,
        ),
        "event_counts": dict(
            sorted(
                Counter(
                    str(row["economic_first_passage_event"]) for row in episodes
                ).items()
            )
        ),
    }


def _recovery_checkpoint(
    candidate: dict[str, Any],
    *,
    target_vol_multiplier: float,
    adverse_vol_multiplier: float,
    cost_pct: float,
) -> dict[str, Any] | None:
    entry_price = float(candidate["entry_price"])
    scale_pct = max(float(candidate["volatility_scale_pct"]), 1e-6)
    favorable_boundary_pct = cost_pct + scale_pct * target_vol_multiplier
    adverse_boundary_pct = scale_pct * adverse_vol_multiplier
    path = list(candidate["_economic_path"])
    path_returns = [
        (float(point["reference_price"]) / entry_price - 1.0) * 100.0 for point in path
    ]
    adverse_breach_streak = 0
    for point_index, (point, path_return_pct) in enumerate(zip(path, path_returns)):
        if path_return_pct >= favorable_boundary_pct:
            return None
        if path_return_pct > -adverse_boundary_pct:
            adverse_breach_streak = 0
            continue
        adverse_breach_streak += 1
        confirmation_reason = _adverse_confirmation_reason(
            candidate,
            point,
            adverse_breach_streak=adverse_breach_streak,
        )
        decision_features = point.get("decision_features")
        if confirmation_reason is None or decision_features is None:
            continue
        entry_at = datetime.fromisoformat(str(candidate["entry_at"]))
        checkpoint_at = datetime.fromisoformat(str(point["execution_at"]))
        immediate_exit_price = float(point["execution_price"])
        immediate_net_pct = (
            immediate_exit_price / entry_price * (1.0 - float(cost_pct) / 100.0) - 1.0
        ) * 100.0
        features = [
            *candidate["economic_features"],
            path_return_pct / scale_pct,
            max(path_returns[: point_index + 1]) / scale_pct,
            (checkpoint_at - entry_at).total_seconds() / 60.0,
            float(adverse_breach_streak),
            float(decision_features[1]),
            float(decision_features[2]),
            float(decision_features[4]),
            float(decision_features[7]),
            float(decision_features[6]),
            float(decision_features[8]),
            float(decision_features[15]),
            (favorable_boundary_pct - path_return_pct) / scale_pct,
        ]
        return {
            "trade_date": candidate["trade_date"],
            "venue": candidate["venue"],
            "session": candidate["session"],
            "pairability_lane": candidate["pairability_lane"],
            "entry_at": candidate["entry_at"],
            "checkpoint_at": checkpoint_at.isoformat(),
            "checkpoint_index": point_index,
            "confirmation_reason": confirmation_reason,
            "adverse_breach_streak": adverse_breach_streak,
            "immediate_exit_price": immediate_exit_price,
            "immediate_net_profit_pct": round(immediate_net_pct, 6),
            "recovery_features": [round(float(value), 8) for value in features],
            "favorable_boundary_pct": round(favorable_boundary_pct, 6),
            "adverse_boundary_pct": round(adverse_boundary_pct, 6),
            "_candidate": candidate,
        }
    return None


def _trailing_exit(
    candidate: dict[str, Any],
    *,
    favorable_index: int,
    trailing_vol_multiplier: float,
) -> tuple[dict[str, Any], int, str]:
    path = list(candidate["_economic_path"])
    if trailing_vol_multiplier <= 0.0:
        return path[favorable_index], favorable_index, "favorable_immediate_exit"
    scale_pct = max(float(candidate["volatility_scale_pct"]), 1e-6)
    peak_price = float(path[favorable_index]["reference_price"])
    for point_index in range(favorable_index + 1, len(path)):
        point = path[point_index]
        reference_price = float(point["reference_price"])
        peak_price = max(peak_price, reference_price)
        drawdown_pct = (reference_price / peak_price - 1.0) * 100.0
        if drawdown_pct <= -(scale_pct * trailing_vol_multiplier):
            return point, point_index, "favorable_trailing_exit"
    return path[-1], len(path) - 1, "favorable_trailing_session_end"


def _favorable_checkpoint(
    candidate: dict[str, Any],
    *,
    favorable_index: int,
    cost_pct: float,
    prior_adverse_confirmed: bool = False,
) -> dict[str, Any] | None:
    path = list(candidate["_economic_path"])
    point = path[favorable_index]
    decision_features = point.get("decision_features")
    if decision_features is None:
        return None
    entry_price = float(candidate["entry_price"])
    scale_pct = max(float(candidate["volatility_scale_pct"]), 1e-6)
    entry_at = datetime.fromisoformat(str(candidate["entry_at"]))
    checkpoint_at = datetime.fromisoformat(str(point["execution_at"]))
    favorable_return_pct = (float(point["reference_price"]) / entry_price - 1.0) * 100.0
    immediate_exit_price = float(point["execution_price"])
    immediate_net_pct = (
        immediate_exit_price / entry_price * (1.0 - float(cost_pct) / 100.0) - 1.0
    ) * 100.0
    features = [
        *candidate["economic_features"],
        favorable_return_pct / scale_pct,
        (checkpoint_at - entry_at).total_seconds() / 60.0,
        float(decision_features[1]),
        float(decision_features[2]),
        float(decision_features[4]),
        float(decision_features[7]),
        float(decision_features[6]),
        float(decision_features[8]),
        float(decision_features[15]),
        float(prior_adverse_confirmed),
    ]
    return {
        "trade_date": candidate["trade_date"],
        "venue": candidate["venue"],
        "session": candidate["session"],
        "pairability_lane": candidate["pairability_lane"],
        "entry_at": candidate["entry_at"],
        "checkpoint_at": checkpoint_at.isoformat(),
        "checkpoint_index": favorable_index,
        "immediate_exit_price": immediate_exit_price,
        "immediate_net_profit_pct": round(immediate_net_pct, 6),
        "trailing_features": [round(float(value), 8) for value in features],
        "_candidate": candidate,
    }


def _select_favorable_exit(
    candidate: dict[str, Any],
    *,
    favorable_index: int,
    trailing_vol_multiplier: float,
    target_vol_multiplier: float,
    adverse_vol_multiplier: float,
    cost_pct: float,
    trailing_models: tuple[Any, Any] | None,
    force_trailing: bool | None,
) -> tuple[dict[str, Any], int, str, bool, float | None, float | None]:
    adverse_checkpoint = _recovery_checkpoint(
        candidate,
        target_vol_multiplier=target_vol_multiplier,
        adverse_vol_multiplier=adverse_vol_multiplier,
        cost_pct=cost_pct,
    )
    checkpoint = _favorable_checkpoint(
        candidate,
        favorable_index=favorable_index,
        cost_pct=cost_pct,
        prior_adverse_confirmed=bool(
            adverse_checkpoint is not None
            and int(adverse_checkpoint["checkpoint_index"]) < favorable_index
        ),
    )
    predicted_probability: float | None = None
    predicted_delta_pct: float | None = None
    if checkpoint is not None and trailing_models is not None:
        event_model, delta_model = trailing_models
        matrix = np.asarray([checkpoint["trailing_features"]], dtype=float)
        class_indexes = {
            int(label): index for index, label in enumerate(event_model.classes_)
        }
        probabilities = event_model.predict_proba(matrix)[0]
        predicted_probability = float(
            probabilities[class_indexes[1]] if 1 in class_indexes else 0.0
        )
        predicted_delta_pct = float(delta_model.predict(matrix)[0])
    trailing_applied = bool(
        trailing_vol_multiplier > 0.0
        and checkpoint is not None
        and (
            force_trailing
            if force_trailing is not None
            else (
                predicted_delta_pct > 0.0
                if predicted_delta_pct is not None
                else trailing_models is None
            )
        )
    )
    if not trailing_applied:
        point = list(candidate["_economic_path"])[favorable_index]
        return (
            point,
            favorable_index,
            "favorable_immediate_exit",
            False,
            predicted_probability,
            predicted_delta_pct,
        )
    point, selected_index, reason = _trailing_exit(
        candidate,
        favorable_index=favorable_index,
        trailing_vol_multiplier=trailing_vol_multiplier,
    )
    return (
        point,
        selected_index,
        reason,
        True,
        predicted_probability,
        predicted_delta_pct,
    )


def _simulate_recovery_aware_candidate(
    candidate: dict[str, Any],
    *,
    policy: dict[str, float],
    cost_pct: float,
    recovery_models: tuple[Any, Any, Any | None, float] | None = None,
    force_recovery: bool | None = None,
    trailing_models: tuple[Any, Any] | None = None,
    force_trailing: bool | None = None,
) -> dict[str, Any]:
    entry_price = float(candidate["entry_price"])
    entry_at = datetime.fromisoformat(str(candidate["entry_at"]))
    scale_pct = max(float(candidate["volatility_scale_pct"]), 1e-6)
    favorable_boundary_pct = cost_pct + scale_pct * policy["target_vol_multiplier"]
    adverse_boundary_pct = scale_pct * policy["adverse_vol_multiplier"]
    path = list(candidate["_economic_path"])
    path_returns = [
        (float(point["reference_price"]) / entry_price - 1.0) * 100.0 for point in path
    ]
    selected_point = path[-1]
    selected_index = len(path) - 1
    exit_reason = "session_end_censored"
    checkpoint = _recovery_checkpoint(
        candidate,
        target_vol_multiplier=policy["target_vol_multiplier"],
        adverse_vol_multiplier=policy["adverse_vol_multiplier"],
        cost_pct=cost_pct,
    )
    checkpoint_index = (
        int(checkpoint["checkpoint_index"]) if checkpoint is not None else None
    )
    recovery_deferred = False
    predicted_recovery_probability: float | None = None
    predicted_recovery_delta_pct: float | None = None
    predicted_time_to_recovery_minutes: float | None = None
    recovery_realized_minutes: float | None = None
    trailing_applied = False
    predicted_trailing_probability: float | None = None
    predicted_trailing_delta_pct: float | None = None
    for point_index, (point, path_return_pct) in enumerate(zip(path, path_returns)):
        if path_return_pct >= favorable_boundary_pct:
            (
                selected_point,
                selected_index,
                exit_reason,
                trailing_applied,
                predicted_trailing_probability,
                predicted_trailing_delta_pct,
            ) = _select_favorable_exit(
                candidate,
                favorable_index=point_index,
                trailing_vol_multiplier=policy["trailing_vol_multiplier"],
                target_vol_multiplier=policy["target_vol_multiplier"],
                adverse_vol_multiplier=policy["adverse_vol_multiplier"],
                cost_pct=cost_pct,
                trailing_models=trailing_models,
                force_trailing=force_trailing,
            )
            if checkpoint is not None and point_index > int(
                checkpoint["checkpoint_index"]
            ):
                recovery_realized_minutes = (
                    datetime.fromisoformat(str(point["execution_at"]))
                    - datetime.fromisoformat(str(checkpoint["checkpoint_at"]))
                ).total_seconds() / 60.0
            break
        if checkpoint_index is None or point_index != checkpoint_index:
            continue
        if recovery_models is not None:
            event_model, delta_model, time_model, fallback_time = recovery_models
            matrix = np.asarray([checkpoint["recovery_features"]], dtype=float)
            class_indexes = {
                int(label): index for index, label in enumerate(event_model.classes_)
            }
            probabilities = event_model.predict_proba(matrix)[0]
            predicted_recovery_probability = float(
                probabilities[class_indexes[1]] if 1 in class_indexes else 0.0
            )
            predicted_recovery_delta_pct = float(delta_model.predict(matrix)[0])
            predicted_time_to_recovery_minutes = (
                float(time_model.predict(matrix)[0])
                if time_model is not None
                else float(fallback_time)
            )
        recovery_deferred = bool(
            force_recovery
            if force_recovery is not None
            else (
                predicted_recovery_delta_pct is not None
                and predicted_recovery_delta_pct > 0.0
            )
        )
        if not recovery_deferred:
            selected_point = point
            selected_index = point_index
            exit_reason = "adverse_immediate_exit"
            break
        checkpoint_at = datetime.fromisoformat(str(checkpoint["checkpoint_at"]))
        for recovery_index in range(point_index + 1, len(path)):
            recovery_point = path[recovery_index]
            recovery_return_pct = path_returns[recovery_index]
            if recovery_return_pct >= favorable_boundary_pct:
                (
                    selected_point,
                    selected_index,
                    exit_reason,
                    trailing_applied,
                    predicted_trailing_probability,
                    predicted_trailing_delta_pct,
                ) = _select_favorable_exit(
                    candidate,
                    favorable_index=recovery_index,
                    trailing_vol_multiplier=policy["trailing_vol_multiplier"],
                    target_vol_multiplier=policy["target_vol_multiplier"],
                    adverse_vol_multiplier=policy["adverse_vol_multiplier"],
                    cost_pct=cost_pct,
                    trailing_models=trailing_models,
                    force_trailing=force_trailing,
                )
                recovery_realized_minutes = (
                    datetime.fromisoformat(str(recovery_point["execution_at"]))
                    - checkpoint_at
                ).total_seconds() / 60.0
                break
            if recovery_return_pct <= -(
                adverse_boundary_pct * policy["recovery_deep_adverse_multiplier"]
            ):
                selected_point = recovery_point
                selected_index = recovery_index
                exit_reason = "recovery_deep_adverse_exit"
                break
            recovery_elapsed = (
                datetime.fromisoformat(str(recovery_point["execution_at"]))
                - checkpoint_at
            ).total_seconds() / 60.0
            if recovery_elapsed >= policy["recovery_wait_minutes"]:
                selected_point = recovery_point
                selected_index = recovery_index
                exit_reason = "recovery_timeout_exit"
                break
        break
    exit_price = float(selected_point["execution_price"])
    exit_at = datetime.fromisoformat(str(selected_point["execution_at"]))
    gross_pct = (exit_price / entry_price - 1.0) * 100.0
    net_pct = (exit_price / entry_price * (1.0 - cost_pct / 100.0) - 1.0) * 100.0
    public = {key: value for key, value in candidate.items() if not key.startswith("_")}
    public.update(
        {
            "exit_at": exit_at.isoformat(),
            "exit_price": exit_price,
            "exit_reason": exit_reason,
            "target_vol_multiplier": policy["target_vol_multiplier"],
            "adverse_vol_multiplier": policy["adverse_vol_multiplier"],
            "trailing_vol_multiplier": policy["trailing_vol_multiplier"],
            "recovery_wait_minutes": policy["recovery_wait_minutes"],
            "recovery_deep_adverse_multiplier": policy[
                "recovery_deep_adverse_multiplier"
            ],
            "favorable_boundary_pct": round(favorable_boundary_pct, 6),
            "adverse_boundary_pct": round(adverse_boundary_pct, 6),
            "recovery_checkpoint_at": (
                checkpoint["checkpoint_at"] if checkpoint is not None else None
            ),
            "recovery_confirmation_reason": (
                checkpoint["confirmation_reason"] if checkpoint is not None else None
            ),
            "recovery_deferred": recovery_deferred,
            "predicted_recovery_probability": (
                round(predicted_recovery_probability, 6)
                if predicted_recovery_probability is not None
                else None
            ),
            "predicted_recovery_delta_pct": (
                round(predicted_recovery_delta_pct, 6)
                if predicted_recovery_delta_pct is not None
                else None
            ),
            "predicted_time_to_recovery_minutes": (
                round(max(0.0, predicted_time_to_recovery_minutes), 3)
                if predicted_time_to_recovery_minutes is not None
                else None
            ),
            "recovery_realized_minutes": (
                round(recovery_realized_minutes, 3)
                if recovery_realized_minutes is not None
                else None
            ),
            "trailing_applied": trailing_applied,
            "predicted_trailing_probability": (
                round(predicted_trailing_probability, 6)
                if predicted_trailing_probability is not None
                else None
            ),
            "predicted_trailing_delta_pct": (
                round(predicted_trailing_delta_pct, 6)
                if predicted_trailing_delta_pct is not None
                else None
            ),
            "event_duration_minutes": round(
                (exit_at - entry_at).total_seconds() / 60.0, 3
            ),
            "mfe_pct": round(max(path_returns[: selected_index + 1]), 6),
            "mae_pct": round(min(path_returns[: selected_index + 1]), 6),
            "post_entry_session_mfe_pct": round(max(path_returns), 6),
            "post_entry_session_mae_pct": round(min(path_returns), 6),
            "gross_profit_pct": round(gross_pct, 6),
            "net_profit_pct": round(net_pct, 6),
        }
    )
    return public


def _fit_recovery_estimators(
    checkpoints: Sequence[dict[str, Any]],
    recovered_episodes: Sequence[dict[str, Any]],
) -> tuple[Any, Any, Any | None, float] | None:
    if len(checkpoints) < RECOVERY_AWARE_MIN_CHECKPOINTS:
        return None
    deltas = np.asarray(
        [
            float(episode["net_profit_pct"])
            - float(checkpoint["immediate_net_profit_pct"])
            for checkpoint, episode in zip(checkpoints, recovered_episodes)
        ],
        dtype=float,
    )
    labels = np.asarray(deltas > 0.0, dtype=int)
    counts = Counter(int(value) for value in labels)
    if len(counts) < 2 or min(counts.values()) < 4:
        return None
    features = np.asarray(
        [row["recovery_features"] for row in checkpoints], dtype=float
    )
    event_model = HistGradientBoostingClassifier(
        learning_rate=0.06,
        max_iter=80,
        max_leaf_nodes=9,
        min_samples_leaf=8,
        l2_regularization=2.0,
        class_weight="balanced",
        random_state=0,
    )
    delta_model = HistGradientBoostingRegressor(
        learning_rate=0.05,
        max_iter=80,
        max_leaf_nodes=9,
        min_samples_leaf=8,
        l2_regularization=2.0,
        random_state=0,
    )
    event_model.fit(features, labels)
    delta_model.fit(features, deltas)
    successful = [
        (checkpoint, episode)
        for checkpoint, episode, label in zip(checkpoints, recovered_episodes, labels)
        if label == 1 and episode.get("recovery_realized_minutes") is not None
    ]
    fallback_time = (
        statistics.median(
            float(episode["recovery_realized_minutes"]) for _, episode in successful
        )
        if successful
        else 0.0
    )
    time_model: HistGradientBoostingRegressor | None = None
    if len(successful) >= 8:
        time_model = HistGradientBoostingRegressor(
            learning_rate=0.05,
            max_iter=60,
            max_leaf_nodes=7,
            min_samples_leaf=6,
            l2_regularization=2.0,
            random_state=0,
        )
        time_model.fit(
            np.asarray(
                [checkpoint["recovery_features"] for checkpoint, _ in successful],
                dtype=float,
            ),
            np.asarray(
                [
                    float(episode["recovery_realized_minutes"])
                    for _, episode in successful
                ],
                dtype=float,
            ),
        )
    return event_model, delta_model, time_model, float(fallback_time)


def _baseline_favorable_checkpoint(
    candidate: dict[str, Any],
    *,
    boundary_policy: dict[str, float],
    cost_pct: float,
) -> tuple[dict[str, Any], dict[str, Any]] | None:
    baseline = _apply_economic_first_passage_policy(
        candidate,
        target_vol_multiplier=boundary_policy["target_vol_multiplier"],
        adverse_vol_multiplier=boundary_policy["adverse_vol_multiplier"],
        cost_pct=cost_pct,
    )
    if baseline["economic_first_passage_event"] != "favorable_first_passage":
        return None
    favorable_index = next(
        (
            index
            for index, point in enumerate(candidate["_economic_path"])
            if str(point["execution_at"]) == str(baseline["exit_at"])
        ),
        None,
    )
    if favorable_index is None:
        return None
    checkpoint = _favorable_checkpoint(
        candidate,
        favorable_index=favorable_index,
        cost_pct=cost_pct,
    )
    return (checkpoint, baseline) if checkpoint is not None else None


def _first_favorable_checkpoint(
    candidate: dict[str, Any],
    *,
    boundary_policy: dict[str, float],
    cost_pct: float,
) -> dict[str, Any] | None:
    entry_price = float(candidate["entry_price"])
    scale_pct = max(float(candidate["volatility_scale_pct"]), 1e-6)
    favorable_boundary_pct = float(cost_pct) + scale_pct * float(
        boundary_policy["target_vol_multiplier"]
    )
    favorable_index = next(
        (
            index
            for index, point in enumerate(candidate["_economic_path"])
            if (float(point["reference_price"]) / entry_price - 1.0) * 100.0
            >= favorable_boundary_pct
        ),
        None,
    )
    if favorable_index is None:
        return None
    adverse_checkpoint = _recovery_checkpoint(
        candidate,
        target_vol_multiplier=boundary_policy["target_vol_multiplier"],
        adverse_vol_multiplier=boundary_policy["adverse_vol_multiplier"],
        cost_pct=cost_pct,
    )
    return _favorable_checkpoint(
        candidate,
        favorable_index=favorable_index,
        cost_pct=cost_pct,
        prior_adverse_confirmed=bool(
            adverse_checkpoint is not None
            and int(adverse_checkpoint["checkpoint_index"]) < favorable_index
        ),
    )


def _forced_trailing_episode(
    checkpoint: dict[str, Any],
    *,
    trailing_vol_multiplier: float,
    cost_pct: float,
) -> dict[str, Any]:
    candidate = checkpoint["_candidate"]
    point, selected_index, reason = _trailing_exit(
        candidate,
        favorable_index=int(checkpoint["checkpoint_index"]),
        trailing_vol_multiplier=trailing_vol_multiplier,
    )
    entry_price = float(candidate["entry_price"])
    exit_price = float(point["execution_price"])
    net_pct = (exit_price / entry_price * (1.0 - cost_pct / 100.0) - 1.0) * 100.0
    return {
        "trade_date": candidate["trade_date"],
        "venue": candidate["venue"],
        "session": candidate["session"],
        "pairability_lane": candidate["pairability_lane"],
        "entry_at": candidate["entry_at"],
        "exit_at": point["execution_at"],
        "exit_price": exit_price,
        "exit_reason": reason,
        "selected_path_index": selected_index,
        "net_profit_pct": round(net_pct, 6),
    }


def _fit_trailing_estimators(
    checkpoints: Sequence[dict[str, Any]],
    forced_trailing_episodes: Sequence[dict[str, Any]],
) -> tuple[Any, Any] | None:
    if len(checkpoints) < TRAILING_AWARE_MIN_CHECKPOINTS:
        return None
    deltas = np.asarray(
        [
            float(episode["net_profit_pct"])
            - float(checkpoint["immediate_net_profit_pct"])
            for checkpoint, episode in zip(checkpoints, forced_trailing_episodes)
        ],
        dtype=float,
    )
    labels = np.asarray(deltas > 0.0, dtype=int)
    counts = Counter(int(value) for value in labels)
    if len(counts) < 2 or min(counts.values()) < 4:
        return None
    features = np.asarray(
        [row["trailing_features"] for row in checkpoints], dtype=float
    )
    event_model = HistGradientBoostingClassifier(
        learning_rate=0.06,
        max_iter=80,
        max_leaf_nodes=9,
        min_samples_leaf=8,
        l2_regularization=2.0,
        class_weight="balanced",
        random_state=0,
    )
    delta_model = HistGradientBoostingRegressor(
        learning_rate=0.05,
        max_iter=80,
        max_leaf_nodes=9,
        min_samples_leaf=8,
        l2_regularization=2.0,
        random_state=0,
    )
    event_model.fit(features, labels)
    delta_model.fit(features, deltas)
    return event_model, delta_model


def _fit_lane_trailing_model(
    prior_candidates: Sequence[dict[str, Any]],
    *,
    lane: str,
    boundary_policy: dict[str, float],
    cost_pct: float,
) -> tuple[tuple[Any, Any] | None, float, dict[str, Any]] | None:
    lane_candidates = [
        row for row in prior_candidates if row.get("pairability_lane") == lane
    ]
    dates = sorted(
        {date.fromisoformat(str(row["trade_date"])) for row in lane_candidates}
    )
    if len(dates) < ECONOMIC_FIRST_PASSAGE_MIN_HISTORY_DATES:
        return None
    validation_date_count = max(2, math.ceil(len(dates) * 0.25))
    fit_dates = set(dates[:-validation_date_count])
    validation_dates = set(dates[-validation_date_count:])
    checkpoints = [
        checkpoint
        for row in lane_candidates
        if (
            checkpoint := _first_favorable_checkpoint(
                row,
                boundary_policy=boundary_policy,
                cost_pct=cost_pct,
            )
        )
        is not None
    ]
    if len(checkpoints) < TRAILING_AWARE_MIN_CHECKPOINTS:
        return None
    validation_checkpoints = [
        checkpoint
        for checkpoint in checkpoints
        if date.fromisoformat(str(checkpoint["trade_date"])) in validation_dates
    ]
    if len(validation_checkpoints) < 4:
        return None
    policy_results: list[dict[str, Any]] = []
    for trailing_multiplier in RECOVERY_TRAILING_VOL_MULTIPLIERS:
        deltas: list[float] = []
        for checkpoint in validation_checkpoints:
            if trailing_multiplier <= 0.0:
                deltas.append(0.0)
                continue
            forced = _forced_trailing_episode(
                checkpoint,
                trailing_vol_multiplier=float(trailing_multiplier),
                cost_pct=cost_pct,
            )
            deltas.append(
                float(forced["net_profit_pct"])
                - float(checkpoint["immediate_net_profit_pct"])
            )
        policy_results.append(
            {
                "trailing_vol_multiplier": float(trailing_multiplier),
                "validation_checkpoint_count": len(deltas),
                "avg_incremental_net_profit_pct": round(statistics.fmean(deltas), 6),
                "beneficial_count": sum(value > 0.0 for value in deltas),
            }
        )
    selected = max(
        policy_results,
        key=lambda row: (
            float(row["avg_incremental_net_profit_pct"]),
            -float(row["trailing_vol_multiplier"]),
        ),
    )
    selected_multiplier = float(selected["trailing_vol_multiplier"])
    models: tuple[Any, Any] | None = None
    beneficial_count = 0
    if selected_multiplier > 0.0:
        forced_episodes = []
        for checkpoint in checkpoints:
            forced_episodes.append(
                _forced_trailing_episode(
                    checkpoint,
                    trailing_vol_multiplier=selected_multiplier,
                    cost_pct=cost_pct,
                )
            )
        models = _fit_trailing_estimators(checkpoints, forced_episodes)
        if models is None:
            return None
        beneficial_count = sum(
            float(episode["net_profit_pct"])
            > float(checkpoint["immediate_net_profit_pct"])
            for checkpoint, episode in zip(checkpoints, forced_episodes)
        )
    return (
        models,
        selected_multiplier,
        {
            "lane": lane,
            "history_date_count": len(dates),
            "history_favorable_checkpoint_count": len(checkpoints),
            "history_trailing_beneficial_count": beneficial_count,
            "fit_dates": [item.isoformat() for item in sorted(fit_dates)],
            "validation_dates": [item.isoformat() for item in sorted(validation_dates)],
            "selected_trailing_policy": selected,
            "policy_grid": policy_results,
            "policy_selection": "prior_validation_incremental_ev_with_zero_baseline",
            "trailing_selection": "predicted_incremental_ev_gt_zero",
        },
    )


def _fit_lane_recovery_aware_model(
    prior_candidates: Sequence[dict[str, Any]],
    *,
    lane: str,
    boundary_policy: dict[str, float],
    cost_pct: float,
    trailing_policy_enabled: bool = True,
) -> tuple[tuple[Any, Any, Any | None, float], dict[str, float], dict[str, Any]] | None:
    lane_candidates = [
        row for row in prior_candidates if row.get("pairability_lane") == lane
    ]
    dates = sorted(
        {date.fromisoformat(str(row["trade_date"])) for row in lane_candidates}
    )
    if len(dates) < ECONOMIC_FIRST_PASSAGE_MIN_HISTORY_DATES:
        return None
    validation_date_count = max(2, math.ceil(len(dates) * 0.25))
    fit_dates = set(dates[:-validation_date_count])
    validation_dates = set(dates[-validation_date_count:])
    validation_candidates = [
        row
        for row in lane_candidates
        if date.fromisoformat(str(row["trade_date"])) in validation_dates
    ]
    trail_results: list[dict[str, Any]] = []
    trailing_multipliers = (
        RECOVERY_TRAILING_VOL_MULTIPLIERS if trailing_policy_enabled else (0.0,)
    )
    for trailing_multiplier in trailing_multipliers:
        policy = {
            **boundary_policy,
            "trailing_vol_multiplier": float(trailing_multiplier),
            "recovery_wait_minutes": 5.0,
            "recovery_deep_adverse_multiplier": 1.5,
        }
        episodes = [
            _simulate_recovery_aware_candidate(
                row,
                policy=policy,
                cost_pct=cost_pct,
                force_recovery=False,
            )
            for row in validation_candidates
        ]
        summary = _summary(
            _non_overlapping_candidates(episodes, selected_only=False),
            source_quality_passed=True,
        )
        trail_results.append(
            {
                "trailing_vol_multiplier": float(trailing_multiplier),
                "sample_count": summary["sample_count"],
                "equal_weight_avg_profit_pct": summary["equal_weight_avg_profit_pct"],
            }
        )
    selected_trail = max(
        trail_results,
        key=lambda row: (
            float(row["equal_weight_avg_profit_pct"])
            if row["equal_weight_avg_profit_pct"] is not None
            else -math.inf
        ),
    )
    recovery_results: list[dict[str, Any]] = []
    for wait_minutes in RECOVERY_WAIT_MINUTES:
        for deep_multiplier in RECOVERY_DEEP_ADVERSE_MULTIPLIERS:
            policy = {
                **boundary_policy,
                "trailing_vol_multiplier": float(
                    selected_trail["trailing_vol_multiplier"]
                ),
                "recovery_wait_minutes": float(wait_minutes),
                "recovery_deep_adverse_multiplier": float(deep_multiplier),
            }
            episodes = [
                _simulate_recovery_aware_candidate(
                    row,
                    policy=policy,
                    cost_pct=cost_pct,
                    force_recovery=True,
                )
                for row in validation_candidates
            ]
            summary = _summary(
                _non_overlapping_candidates(episodes, selected_only=False),
                source_quality_passed=True,
            )
            recovery_results.append(
                {
                    "recovery_wait_minutes": float(wait_minutes),
                    "recovery_deep_adverse_multiplier": float(deep_multiplier),
                    "sample_count": summary["sample_count"],
                    "equal_weight_avg_profit_pct": summary[
                        "equal_weight_avg_profit_pct"
                    ],
                }
            )
    selected_recovery = max(
        recovery_results,
        key=lambda row: (
            float(row["equal_weight_avg_profit_pct"])
            if row["equal_weight_avg_profit_pct"] is not None
            else -math.inf
        ),
    )
    policy = {
        **boundary_policy,
        "trailing_vol_multiplier": float(selected_trail["trailing_vol_multiplier"]),
        "recovery_wait_minutes": float(selected_recovery["recovery_wait_minutes"]),
        "recovery_deep_adverse_multiplier": float(
            selected_recovery["recovery_deep_adverse_multiplier"]
        ),
    }
    checkpoints = [
        checkpoint
        for row in lane_candidates
        if (
            checkpoint := _recovery_checkpoint(
                row,
                target_vol_multiplier=policy["target_vol_multiplier"],
                adverse_vol_multiplier=policy["adverse_vol_multiplier"],
                cost_pct=cost_pct,
            )
        )
        is not None
    ]
    recovered_episodes = [
        _simulate_recovery_aware_candidate(
            checkpoint["_candidate"],
            policy=policy,
            cost_pct=cost_pct,
            force_recovery=True,
        )
        for checkpoint in checkpoints
    ]
    models = _fit_recovery_estimators(checkpoints, recovered_episodes)
    if models is None:
        return None
    recovery_beneficial_count = sum(
        float(episode["net_profit_pct"]) > float(checkpoint["immediate_net_profit_pct"])
        for checkpoint, episode in zip(checkpoints, recovered_episodes)
    )
    return (
        models,
        policy,
        {
            "lane": lane,
            "history_date_count": len(dates),
            "history_candidate_count": len(lane_candidates),
            "history_recovery_checkpoint_count": len(checkpoints),
            "history_recovery_beneficial_count": recovery_beneficial_count,
            "fit_dates": [item.isoformat() for item in sorted(fit_dates)],
            "validation_dates": [item.isoformat() for item in sorted(validation_dates)],
            "selected_policy": policy,
            "trailing_policy_results": trail_results,
            "recovery_policy_results": recovery_results,
            "policy_selection": "prior_chronological_validation_ev",
            "recovery_selection": "predicted_incremental_ev_gt_zero",
            "trailing_policy_enabled_in_recovery_labels": trailing_policy_enabled,
        },
    )


def _recovery_aware_decision(
    selected_summary: dict[str, Any],
    baseline_summary: dict[str, Any],
    *,
    sample_floor_passed: bool,
    source_quality_passed: bool,
) -> str:
    if not source_quality_passed:
        return "source_quality_blocked"
    if not sample_floor_passed:
        return "insufficient_coverage_dates"
    if not selected_summary.get("sample_count"):
        return "insufficient_recovery_evaluation"
    selected_ev = selected_summary.get("source_quality_adjusted_ev_pct")
    baseline_ev = baseline_summary.get("source_quality_adjusted_ev_pct")
    if selected_ev is None:
        return "no_incremental_predictive_value"
    if float(selected_ev) > 0.0:
        return "recovery_aware_exit_oos_positive"
    if baseline_ev is not None and float(selected_ev) > float(baseline_ev):
        return "recovery_aware_exit_improved_but_negative"
    return "no_incremental_predictive_value"


def _axis_separation_decision(
    arm_summaries: dict[str, dict[str, Any]],
    *,
    sample_floor_passed: bool,
    source_quality_passed: bool,
) -> str:
    if not source_quality_passed:
        return "source_quality_blocked"
    if not sample_floor_passed:
        return "insufficient_coverage_dates"
    baseline = arm_summaries["baseline"]
    if not baseline.get("sample_count"):
        return "insufficient_axis_evaluation"
    baseline_ev = baseline.get("source_quality_adjusted_ev_pct")
    recovery_ev = arm_summaries["recovery_only"].get("source_quality_adjusted_ev_pct")
    trailing_ev = arm_summaries["trailing_only"].get("source_quality_adjusted_ev_pct")
    combined_ev = arm_summaries["recovery_plus_trailing"].get(
        "source_quality_adjusted_ev_pct"
    )
    if recovery_ev is not None and float(recovery_ev) > 0.0:
        return "recovery_only_oos_positive"
    if (
        trailing_ev is not None
        and baseline_ev is not None
        and float(trailing_ev) > float(baseline_ev)
        and float(trailing_ev) > 0.0
    ):
        return "trailing_incremental_ev_positive"
    comparable = [
        float(value)
        for value in (recovery_ev, trailing_ev, combined_ev)
        if value is not None
    ]
    if baseline_ev is not None and comparable and max(comparable) > float(baseline_ev):
        return "axis_separation_improved_but_negative"
    return "no_incremental_predictive_value"


def _recovery_entry_utility_decision(
    selected_summary: dict[str, Any],
    control_summary: dict[str, Any],
    *,
    sample_floor_passed: bool,
    source_quality_passed: bool,
) -> str:
    if not source_quality_passed:
        return "source_quality_blocked"
    if not sample_floor_passed:
        return "insufficient_coverage_dates"
    if not selected_summary.get("sample_count"):
        return "insufficient_recovery_entry_labels"
    selected_ev = selected_summary.get("source_quality_adjusted_ev_pct")
    control_ev = control_summary.get("source_quality_adjusted_ev_pct")
    if selected_ev is None:
        return "no_incremental_predictive_value"
    if float(selected_ev) > 0.0:
        return "recovery_entry_utility_oos_positive"
    if control_ev is not None and float(selected_ev) > float(control_ev):
        return "recovery_entry_utility_improved_but_negative"
    return "no_incremental_predictive_value"


def _calibrated_recovery_entry_decision(
    calibrated_summary: dict[str, Any],
    raw_summary: dict[str, Any],
    control_summary: dict[str, Any],
    *,
    calibrated_path: dict[str, Any],
    raw_path: dict[str, Any],
    control_path: dict[str, Any],
    evaluation_count: int,
    sample_floor_passed: bool,
    source_quality_passed: bool,
) -> str:
    if not source_quality_passed:
        return "source_quality_blocked"
    if not sample_floor_passed:
        return "insufficient_coverage_dates"
    if evaluation_count <= 0:
        return "insufficient_calibration_history"
    calibrated_ev = calibrated_summary.get("source_quality_adjusted_ev_pct")
    if calibrated_ev is None:
        return "no_incremental_predictive_value"
    raw_ev = raw_summary.get("source_quality_adjusted_ev_pct")
    control_ev = control_summary.get("source_quality_adjusted_ev_pct")
    comparison_evs = [
        float(value) for value in (raw_ev, control_ev) if value is not None
    ]
    comparison_compounded = [
        float(value)
        for value in (
            raw_path.get("compounded_net_return_pct"),
            control_path.get("compounded_net_return_pct"),
        )
        if value is not None
    ]
    comparison_mae = [
        float(value)
        for value in (raw_path.get("avg_mae_pct"), control_path.get("avg_mae_pct"))
        if value is not None
    ]
    raw_count = int(raw_summary.get("sample_count") or 0)
    opportunity_floor = max(
        1,
        math.ceil(raw_count * RECOVERY_ENTRY_CALIBRATION_OPPORTUNITY_RETENTION),
    )
    opportunity_retained = bool(
        int(calibrated_summary.get("sample_count") or 0) >= opportunity_floor
    )
    strict_ev_improvement = bool(raw_ev is None or float(calibrated_ev) > float(raw_ev))
    if float(calibrated_ev) > 0.0 and opportunity_retained and strict_ev_improvement:
        return "calibrated_recovery_entry_oos_positive"
    strictly_improves_raw = bool(
        strict_ev_improvement
        or float(calibrated_path["compounded_net_return_pct"])
        > float(raw_path["compounded_net_return_pct"])
        or (
            calibrated_path.get("avg_mae_pct") is not None
            and raw_path.get("avg_mae_pct") is not None
            and float(calibrated_path["avg_mae_pct"]) > float(raw_path["avg_mae_pct"])
        )
    )
    pareto_improved = bool(
        comparison_evs
        and comparison_compounded
        and comparison_mae
        and float(calibrated_ev) >= max(comparison_evs)
        and float(calibrated_path["compounded_net_return_pct"])
        >= max(comparison_compounded)
        and float(calibrated_path["avg_mae_pct"]) >= max(comparison_mae)
        and opportunity_retained
        and strictly_improves_raw
    )
    if pareto_improved:
        return "calibrated_recovery_entry_pareto_improved"
    return "no_incremental_predictive_value"


def _recovery_entry_timing_decision(
    timing_summary: dict[str, Any],
    control_summary: dict[str, Any],
    *,
    timing_path: dict[str, Any],
    control_path: dict[str, Any],
    evaluation_count: int,
    sample_floor_passed: bool,
    source_quality_passed: bool,
) -> str:
    if not source_quality_passed:
        return "source_quality_blocked"
    if not sample_floor_passed:
        return "insufficient_timing_history"
    if evaluation_count <= 0:
        return "insufficient_timing_history"
    timing_ev = timing_summary.get("source_quality_adjusted_ev_pct")
    control_ev = control_summary.get("source_quality_adjusted_ev_pct")
    if timing_ev is None or control_ev is None:
        return "no_incremental_predictive_value"
    control_count = int(control_summary.get("sample_count") or 0)
    timing_count = int(timing_summary.get("sample_count") or 0)
    opportunity_floor = max(
        1,
        math.ceil(control_count * RECOVERY_ENTRY_TIMING_OPPORTUNITY_RETENTION),
    )
    retained = timing_count >= opportunity_floor
    strict_improvement = bool(
        float(timing_ev) > float(control_ev)
        or float(timing_path["compounded_net_return_pct"])
        > float(control_path["compounded_net_return_pct"])
        or (
            timing_path.get("avg_mae_pct") is not None
            and control_path.get("avg_mae_pct") is not None
            and float(timing_path["avg_mae_pct"]) > float(control_path["avg_mae_pct"])
        )
    )
    if float(timing_ev) > 0.0 and retained and strict_improvement:
        return "entry_timing_oos_positive"
    pareto_improved = bool(
        retained
        and strict_improvement
        and float(timing_ev) >= float(control_ev)
        and float(timing_path["compounded_net_return_pct"])
        >= float(control_path["compounded_net_return_pct"])
        and timing_path.get("avg_mae_pct") is not None
        and control_path.get("avg_mae_pct") is not None
        and float(timing_path["avg_mae_pct"]) >= float(control_path["avg_mae_pct"])
    )
    if pareto_improved:
        return "entry_timing_pareto_improved"
    return "no_incremental_predictive_value"


def _candidate_timing_utility_decision(
    selected_summary: dict[str, Any],
    control_summary: dict[str, Any],
    *,
    selected_path: dict[str, Any],
    control_path: dict[str, Any],
    evaluation_count: int,
    sample_floor_passed: bool,
    source_quality_passed: bool,
) -> str:
    if not source_quality_passed:
        return "source_quality_blocked"
    if not sample_floor_passed or evaluation_count <= 0:
        return "insufficient_timing_pair_history"
    selected_ev = selected_summary.get("source_quality_adjusted_ev_pct")
    control_ev = control_summary.get("source_quality_adjusted_ev_pct")
    if selected_ev is None or control_ev is None:
        return "no_incremental_predictive_value"
    control_count = int(control_summary.get("sample_count") or 0)
    selected_count = int(selected_summary.get("sample_count") or 0)
    opportunity_floor = max(
        1,
        math.ceil(control_count * RECOVERY_ENTRY_TIMING_UTILITY_OPPORTUNITY_RETENTION),
    )
    retained = selected_count >= opportunity_floor
    strict_improvement = bool(
        float(selected_ev) > float(control_ev)
        or float(selected_path["compounded_net_return_pct"])
        > float(control_path["compounded_net_return_pct"])
        or (
            selected_path.get("avg_mae_pct") is not None
            and control_path.get("avg_mae_pct") is not None
            and float(selected_path["avg_mae_pct"]) > float(control_path["avg_mae_pct"])
        )
    )
    if float(selected_ev) > 0.0 and retained and strict_improvement:
        return "candidate_timing_utility_oos_positive"
    if (
        retained
        and strict_improvement
        and float(selected_ev) >= float(control_ev)
        and float(selected_path["compounded_net_return_pct"])
        >= float(control_path["compounded_net_return_pct"])
        and selected_path.get("avg_mae_pct") is not None
        and control_path.get("avg_mae_pct") is not None
        and float(selected_path["avg_mae_pct"]) >= float(control_path["avg_mae_pct"])
    ):
        return "candidate_timing_utility_pareto_improved"
    return "no_incremental_predictive_value"


def _trigger_utility_calibration_decision(
    calibrated_summary: dict[str, Any],
    raw_gate_summary: dict[str, Any],
    control_summary: dict[str, Any],
    *,
    calibrated_path: dict[str, Any],
    raw_gate_path: dict[str, Any],
    control_path: dict[str, Any],
    evaluation_count: int,
    sample_floor_passed: bool,
    source_quality_passed: bool,
) -> str:
    if not source_quality_passed:
        return "source_quality_blocked"
    if not sample_floor_passed or evaluation_count <= 0:
        return "insufficient_trigger_history"
    calibrated_ev = calibrated_summary.get("source_quality_adjusted_ev_pct")
    raw_gate_ev = raw_gate_summary.get("source_quality_adjusted_ev_pct")
    control_ev = control_summary.get("source_quality_adjusted_ev_pct")
    if calibrated_ev is None or raw_gate_ev is None or control_ev is None:
        return "no_incremental_predictive_value"
    control_count = int(control_summary.get("sample_count") or 0)
    opportunity_floor = max(
        1,
        math.ceil(control_count * TRIGGER_UTILITY_CALIBRATION_OPPORTUNITY_RETENTION),
    )
    retained = int(calibrated_summary.get("sample_count") or 0) >= opportunity_floor
    strictly_improves_raw_gate = bool(
        float(calibrated_ev) > float(raw_gate_ev)
        or float(calibrated_path["compounded_net_return_pct"])
        > float(raw_gate_path["compounded_net_return_pct"])
        or (
            calibrated_path.get("avg_mae_pct") is not None
            and raw_gate_path.get("avg_mae_pct") is not None
            and float(calibrated_path["avg_mae_pct"])
            > float(raw_gate_path["avg_mae_pct"])
        )
    )
    if float(calibrated_ev) > 0.0 and retained and strictly_improves_raw_gate:
        return "calibrated_trigger_utility_oos_positive"
    if (
        retained
        and strictly_improves_raw_gate
        and float(calibrated_ev) >= max(float(raw_gate_ev), float(control_ev))
        and float(calibrated_path["compounded_net_return_pct"])
        >= max(
            float(raw_gate_path["compounded_net_return_pct"]),
            float(control_path["compounded_net_return_pct"]),
        )
        and calibrated_path.get("avg_mae_pct") is not None
        and raw_gate_path.get("avg_mae_pct") is not None
        and control_path.get("avg_mae_pct") is not None
        and float(calibrated_path["avg_mae_pct"])
        >= max(
            float(raw_gate_path["avg_mae_pct"]),
            float(control_path["avg_mae_pct"]),
        )
    ):
        return "calibrated_trigger_utility_pareto_improved"
    return "no_incremental_predictive_value"


def _select_wait_budget_policy(
    prior_arm_history: Sequence[dict[str, Any]],
    *,
    lane: str,
) -> dict[str, Any] | None:
    lane_rows = [
        row for row in prior_arm_history if row.get("pairability_lane") == lane
    ]
    if not lane_rows:
        return None
    if any(
        not row.get("wait_budget_oos")
        or row.get("wait_budget_exit_policy") != "recovery_only"
        or row.get("wait_budget_arm") not in WAIT_BUDGET_ARMS
        or int(row.get("wait_budget_enter_per_wait") or 0)
        != WAIT_BUDGET_ARMS[str(row.get("wait_budget_arm"))]
        or date.fromisoformat(str(row["candidate_timing_utility_model_fit_max_date"]))
        >= date.fromisoformat(str(row["trade_date"]))
        or date.fromisoformat(str(row["trigger_utility_calibration_fit_max_date"]))
        >= date.fromisoformat(str(row["trade_date"]))
        for row in lane_rows
    ):
        raise ValueError("wait budget history must be prior OOS and capacity-safe")
    arm_diagnostics: dict[str, dict[str, Any]] = {}
    for arm, enter_per_wait in WAIT_BUDGET_ARMS.items():
        arm_rows = [row for row in lane_rows if row.get("wait_budget_arm") == arm]
        if not arm_rows or not all(
            row.get("wait_budget_opportunity_retention_passed") for row in arm_rows
        ):
            continue
        net_returns = [float(row["net_profit_pct"]) for row in arm_rows]
        arm_diagnostics[arm] = {
            "enter_per_wait": enter_per_wait,
            "history_trade_count": len(arm_rows),
            "history_dates": sorted({str(row["trade_date"]) for row in arm_rows}),
            "source_quality_adjusted_ev_pct": round(statistics.fmean(net_returns), 6),
            "compounded_net_return_pct": round(
                (math.prod(1.0 + value / 100.0 for value in net_returns) - 1.0) * 100.0,
                6,
            ),
            "avg_mae_pct": round(
                statistics.fmean(float(row["mae_pct"]) for row in arm_rows), 6
            ),
        }
    if "enter3_wait1" not in arm_diagnostics:
        return None
    selected_arm = max(
        arm_diagnostics,
        key=lambda arm: (
            float(arm_diagnostics[arm]["source_quality_adjusted_ev_pct"]),
            float(arm_diagnostics[arm]["compounded_net_return_pct"]),
            float(arm_diagnostics[arm]["avg_mae_pct"]),
            WAIT_BUDGET_ARMS[arm],
        ),
    )
    fit_dates = sorted({str(row["trade_date"]) for row in lane_rows})
    return {
        "lane": lane,
        "selected_arm": selected_arm,
        "enter_per_wait": WAIT_BUDGET_ARMS[selected_arm],
        "fit_dates": fit_dates,
        "fit_max_date": fit_dates[-1],
        "selection_metric": "prior_oos_source_quality_adjusted_ev_pct",
        "tie_breakers": [
            "compounded_net_return_pct",
            "avg_mae_pct",
            "more_conservative_enter_per_wait",
        ],
        "arm_diagnostics": arm_diagnostics,
    }


def _wait_budget_prior_decisions(
    prior_arm_decisions: Sequence[dict[str, Any]],
    *,
    prior_baseline_decisions: Sequence[dict[str, Any]],
    prior_trigger_decisions: Sequence[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    first_arm_date = (
        min(
            date.fromisoformat(str(decision["trade_date"]))
            for decision in prior_arm_decisions
        )
        if prior_arm_decisions
        else None
    )

    def seed(decisions: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            decision
            for decision in decisions
            if first_arm_date is None
            or date.fromisoformat(str(decision["trade_date"])) < first_arm_date
        ]

    return (
        [*seed(prior_baseline_decisions), *prior_arm_decisions],
        [*seed(prior_trigger_decisions), *prior_arm_decisions],
    )


def _wait_budget_decision(
    selected_summary: dict[str, Any],
    fixed_summary: dict[str, Any],
    *,
    selected_path: dict[str, Any],
    fixed_path: dict[str, Any],
    arm_evaluation_count: int,
    selected_policy_evaluation_count: int,
    sample_floor_passed: bool,
    source_quality_passed: bool,
) -> str:
    if not source_quality_passed:
        return "source_quality_blocked"
    if not sample_floor_passed or arm_evaluation_count <= 0:
        return "insufficient_wait_budget_history"
    if selected_policy_evaluation_count <= 0:
        return "insufficient_wait_budget_history"
    selected_ev = selected_summary.get("source_quality_adjusted_ev_pct")
    fixed_ev = fixed_summary.get("source_quality_adjusted_ev_pct")
    if selected_ev is None or fixed_ev is None:
        return "no_incremental_predictive_value"
    fixed_count = int(fixed_summary.get("sample_count") or 0)
    retained = int(selected_summary.get("sample_count") or 0) >= max(
        1,
        math.ceil(fixed_count * WAIT_BUDGET_OPPORTUNITY_RETENTION),
    )
    strict_improvement = bool(
        float(selected_ev) > float(fixed_ev)
        or float(selected_path["compounded_net_return_pct"])
        > float(fixed_path["compounded_net_return_pct"])
        or (
            selected_path.get("avg_mae_pct") is not None
            and fixed_path.get("avg_mae_pct") is not None
            and float(selected_path["avg_mae_pct"]) > float(fixed_path["avg_mae_pct"])
        )
    )
    if float(selected_ev) > 0.0 and retained and strict_improvement:
        return "wait_budget_oos_positive"
    if (
        retained
        and strict_improvement
        and float(selected_ev) >= float(fixed_ev)
        and float(selected_path["compounded_net_return_pct"])
        >= float(fixed_path["compounded_net_return_pct"])
        and selected_path.get("avg_mae_pct") is not None
        and fixed_path.get("avg_mae_pct") is not None
        and float(selected_path["avg_mae_pct"]) >= float(fixed_path["avg_mae_pct"])
    ):
        return "wait_budget_pareto_improved"
    return "no_incremental_predictive_value"


def _timestamp_without_timezone(value: datetime | str) -> datetime:
    parsed = value if isinstance(value, datetime) else datetime.fromisoformat(value)
    return parsed.replace(tzinfo=None)


def _simulate_fixed_tp_split_trade(
    entry: dict[str, Any],
    series: Sequence[base.Bar],
    *,
    arm: str,
    cost_pct: float,
) -> dict[str, Any]:
    """Replay one fixed entry with capital-fraction adds and a fixed average TP.

    The first entry is inherited from the already-causal economic selector.  No
    future observation can alter it.  Intrabar ambiguity is deliberately
    adverse: a catastrophic stop is checked before an add, and a bar that fills
    an add cannot also fill the newly repriced target.
    """
    if arm not in FIXED_TP_SPLIT_ARMS:
        raise ValueError(f"unknown fixed TP split arm: {arm}")
    policy = FIXED_TP_SPLIT_ARMS[arm]
    legs = tuple(policy["legs"])
    if not legs or float(legs[0][0]) != 0.0:
        raise ValueError(f"fixed TP split arm must start at the initial entry: {arm}")
    if (
        any(float(weight) <= 0.0 for _, weight in legs)
        or abs(sum(float(weight) for _, weight in legs) - 1.0) > 1e-9
    ):
        raise ValueError(f"fixed TP split arm weights must sum to one: {arm}")
    entry_at = _timestamp_without_timezone(str(entry["entry_at"]))
    entry_price = float(entry["entry_price"])
    if entry_price <= 0:
        raise ValueError("entry price must be positive")
    matching_series = [
        bar for bar in series if _timestamp_without_timezone(bar.timestamp) >= entry_at
    ]
    if not matching_series:
        raise ValueError(f"entry has no market bars: {entry['entry_at']}")

    planned_budget = entry_price
    fills: list[dict[str, Any]] = []

    def add_fill(*, leg_index: int, price: float, filled_at: datetime) -> None:
        allocation = float(legs[leg_index][1])
        fills.append(
            {
                "leg_index": leg_index + 1,
                "allocation": allocation,
                "price": float(price),
                "quantity_units": planned_budget * allocation / float(price),
                "filled_at": _timestamp_without_timezone(filled_at).isoformat(),
            }
        )

    add_fill(leg_index=0, price=entry_price, filled_at=entry_at)
    next_leg_index = 1
    target_eligible_after = entry_at
    catastrophic_stop = float(
        clamp_price_to_tick(
            entry_price * (1.0 - FIXED_TP_SPLIT_CATASTROPHIC_STOP_PCT / 100.0)
        )
    )
    exit_price: float | None = None
    exit_at: datetime | None = None
    exit_reason: str | None = None
    planned_budget_mae_pct = 0.0
    planned_budget_mfe_pct = 0.0

    for bar in matching_series:
        bar_at = _timestamp_without_timezone(bar.timestamp)
        if bar_at < entry_at:
            continue
        total_quantity = sum(float(fill["quantity_units"]) for fill in fills)
        deployed_capital = sum(
            float(fill["quantity_units"]) * float(fill["price"]) for fill in fills
        )
        planned_budget_mae_pct = min(
            planned_budget_mae_pct,
            (float(bar.low) * total_quantity - deployed_capital)
            / planned_budget
            * 100.0,
        )
        planned_budget_mfe_pct = max(
            planned_budget_mfe_pct,
            (float(bar.high) * total_quantity - deployed_capital)
            / planned_budget
            * 100.0,
        )

        added_on_bar = False
        while next_leg_index < len(legs):
            offset_pct = float(legs[next_leg_index][0])
            add_limit = float(
                clamp_price_to_tick(entry_price * (1.0 + offset_pct / 100.0))
            )
            if float(bar.low) > add_limit:
                break
            fill_price = min(float(bar.open), add_limit)
            add_fill(
                leg_index=next_leg_index,
                price=fill_price,
                filled_at=bar_at,
            )
            next_leg_index += 1
            added_on_bar = True
        if added_on_bar:
            total_quantity = sum(float(fill["quantity_units"]) for fill in fills)
            deployed_capital = sum(
                float(fill["quantity_units"]) * float(fill["price"]) for fill in fills
            )
            planned_budget_mae_pct = min(
                planned_budget_mae_pct,
                (float(bar.low) * total_quantity - deployed_capital)
                / planned_budget
                * 100.0,
            )
        if float(bar.open) <= catastrophic_stop:
            exit_price = float(bar.open)
            exit_at = bar_at
            exit_reason = "catastrophic_gap_stop"
            break
        if float(bar.low) <= catastrophic_stop:
            exit_price = catastrophic_stop
            exit_at = bar_at
            exit_reason = "catastrophic_stop"
            break
        if added_on_bar:
            target_eligible_after = bar_at
            continue

        if bar_at <= target_eligible_after:
            continue
        total_quantity = sum(float(fill["quantity_units"]) for fill in fills)
        deployed_capital = sum(
            float(fill["quantity_units"]) * float(fill["price"]) for fill in fills
        )
        average_price = deployed_capital / total_quantity
        target_price = float(
            move_price_up_by_bps(
                average_price,
                int(round(float(policy["target_pct"]) * 100.0)),
            )
        )
        if float(bar.high) >= target_price:
            exit_price = target_price
            exit_at = bar_at
            exit_reason = "fixed_average_take_profit"
            break

    if exit_price is None:
        final_bar = matching_series[-1]
        exit_price = float(final_bar.close)
        exit_at = _timestamp_without_timezone(final_bar.timestamp)
        exit_reason = "session_close"

    total_quantity = sum(float(fill["quantity_units"]) for fill in fills)
    deployed_capital = sum(
        float(fill["quantity_units"]) * float(fill["price"]) for fill in fills
    )
    average_price = deployed_capital / total_quantity
    deployed_fraction = sum(float(fill["allocation"]) for fill in fills)
    gross_planned_pct = (
        (exit_price * total_quantity - deployed_capital) / planned_budget * 100.0
    )
    planned_cost_pct = float(cost_pct) * deployed_fraction
    net_planned_pct = gross_planned_pct - planned_cost_pct
    deployed_net_pct = (exit_price / average_price - 1.0) * 100.0 - float(cost_pct)
    result = {
        **entry,
        "fixed_tp_split_arm": arm,
        "fixed_tp_split_oos": True,
        "entry_price": entry_price,
        "exit_at": exit_at.isoformat(),
        "exit_price": round(exit_price, 6),
        "exit_reason": exit_reason,
        "gross_profit_pct": round(gross_planned_pct, 6),
        "net_profit_pct": round(net_planned_pct, 6),
        "planned_budget_return_pct": round(net_planned_pct, 6),
        "deployed_notional_return_pct": round(deployed_net_pct, 6),
        "planned_budget_mae_pct": round(planned_budget_mae_pct, 6),
        "planned_budget_mfe_pct": round(planned_budget_mfe_pct, 6),
        "deployed_fraction": round(deployed_fraction, 6),
        "filled_leg_count": len(fills),
        "filled_legs": fills,
        "weighted_average_price": round(average_price, 6),
        "average_price_improvement_vs_initial_pct": round(
            (1.0 - average_price / entry_price) * 100.0,
            6,
        ),
        "target_pct_from_average": float(policy["target_pct"]),
        "catastrophic_stop_price": round(catastrophic_stop, 6),
        "exit_below_initial_entry": bool(exit_price < entry_price),
        "same_bar_target_after_fill_allowed": False,
    }
    return result


def _fixed_tp_split_path_diagnostics(
    trades: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    if not trades:
        return {
            "sample_count": 0,
            "compounded_planned_budget_return_pct": 0.0,
            "avg_deployed_notional_return_pct": None,
            "avg_planned_budget_mae_pct": None,
            "avg_planned_budget_mfe_pct": None,
            "avg_deployed_fraction": None,
            "avg_filled_leg_count": None,
            "avg_cost_basis_improvement_pct": None,
            "target_exit_count": 0,
            "catastrophic_stop_count": 0,
            "session_close_count": 0,
            "target_exit_below_initial_count": 0,
        }
    compounded = 1.0
    for trade in trades:
        compounded *= 1.0 + float(trade["planned_budget_return_pct"]) / 100.0
    return {
        "sample_count": len(trades),
        "compounded_planned_budget_return_pct": round((compounded - 1.0) * 100.0, 6),
        "avg_deployed_notional_return_pct": round(
            statistics.fmean(
                float(row["deployed_notional_return_pct"]) for row in trades
            ),
            6,
        ),
        "avg_planned_budget_mae_pct": round(
            statistics.fmean(float(row["planned_budget_mae_pct"]) for row in trades),
            6,
        ),
        "avg_planned_budget_mfe_pct": round(
            statistics.fmean(float(row["planned_budget_mfe_pct"]) for row in trades),
            6,
        ),
        "avg_deployed_fraction": round(
            statistics.fmean(float(row["deployed_fraction"]) for row in trades), 6
        ),
        "avg_filled_leg_count": round(
            statistics.fmean(float(row["filled_leg_count"]) for row in trades), 6
        ),
        "avg_cost_basis_improvement_pct": round(
            statistics.fmean(
                float(row["average_price_improvement_vs_initial_pct"]) for row in trades
            ),
            6,
        ),
        "target_exit_count": sum(
            row["exit_reason"] == "fixed_average_take_profit" for row in trades
        ),
        "catastrophic_stop_count": sum(
            str(row["exit_reason"]).startswith("catastrophic") for row in trades
        ),
        "session_close_count": sum(
            row["exit_reason"] == "session_close" for row in trades
        ),
        "target_exit_below_initial_count": sum(
            row["exit_reason"] == "fixed_average_take_profit"
            and bool(row["exit_below_initial_entry"])
            for row in trades
        ),
    }


def _select_fixed_tp_split_policy(
    prior_arm_trades: Sequence[dict[str, Any]],
) -> dict[str, Any] | None:
    if not prior_arm_trades:
        return None
    invalid = [
        row
        for row in prior_arm_trades
        if not row.get("fixed_tp_split_oos")
        or row.get("fixed_tp_split_arm") not in FIXED_TP_SPLIT_ARMS
    ]
    if invalid:
        raise ValueError("fixed TP split policy history contains invalid rows")
    grouped = {
        arm: [row for row in prior_arm_trades if row["fixed_tp_split_arm"] == arm]
        for arm in FIXED_TP_SPLIT_ARMS
    }
    if any(not rows for rows in grouped.values()):
        return None
    fit_max_date = max(
        date.fromisoformat(str(row["trade_date"])) for row in prior_arm_trades
    )

    def rank(arm: str) -> tuple[float, float, float, int]:
        rows = grouped[arm]
        return (
            statistics.fmean(float(row["net_profit_pct"]) for row in rows),
            statistics.fmean(float(row["planned_budget_mae_pct"]) for row in rows),
            -statistics.fmean(float(row["filled_leg_count"]) for row in rows),
            -list(FIXED_TP_SPLIT_ARMS).index(arm),
        )

    selected_arm = max(FIXED_TP_SPLIT_ARMS, key=rank)
    selected_rows = grouped[selected_arm]
    return {
        "selected_arm": selected_arm,
        "fit_max_date": fit_max_date.isoformat(),
        "prior_trade_count": len(selected_rows),
        "prior_evaluation_date_count": len(
            {str(row["trade_date"]) for row in selected_rows}
        ),
        "prior_planned_budget_ev_pct": round(rank(selected_arm)[0], 6),
        "selection_policy": (
            "max_prior_planned_budget_ev_then_less_adverse_mae_then_fewer_legs"
        ),
    }


def _fixed_tp_split_walk_forward(
    economic_evaluations: Sequence[dict[str, Any]],
    series_by_key: dict[tuple[date, str, str], Sequence[base.Bar]],
    *,
    venue: str,
    cost_pct: float,
    sample_floor_passed: bool,
    source_quality_passed: bool,
) -> dict[str, Any]:
    history: list[dict[str, Any]] = []
    arm_trades: dict[str, list[dict[str, Any]]] = {
        arm: [] for arm in FIXED_TP_SPLIT_ARMS
    }
    selected_trades: list[dict[str, Any]] = []
    selected_control_trades: list[dict[str, Any]] = []
    evaluations: list[dict[str, Any]] = []
    for evaluation in economic_evaluations:
        evaluation_date = date.fromisoformat(str(evaluation["evaluation_date"]))
        entries = list(evaluation.get("selected_trades") or [])
        if not entries:
            evaluations.append(
                {
                    "evaluation_date": evaluation_date.isoformat(),
                    "status": "no_fixed_entry_cohort",
                    "prior_selected_policy": None,
                    "arm_trades": {arm: [] for arm in FIXED_TP_SPLIT_ARMS},
                    "selected_policy_trades": [],
                }
            )
            continue
        policy = _select_fixed_tp_split_policy(history)
        if (
            policy is not None
            and date.fromisoformat(policy["fit_max_date"]) >= evaluation_date
        ):
            raise ValueError("fixed TP split policy uses current or future outcomes")
        current_arms: dict[str, list[dict[str, Any]]] = {
            arm: [] for arm in FIXED_TP_SPLIT_ARMS
        }
        for entry in entries:
            key = (
                evaluation_date,
                venue,
                str(entry["session"]),
            )
            series = series_by_key.get(key)
            if not series:
                raise ValueError(f"fixed TP split entry has no session series: {key}")
            for arm in FIXED_TP_SPLIT_ARMS:
                current_arms[arm].append(
                    _simulate_fixed_tp_split_trade(
                        entry,
                        series,
                        arm=arm,
                        cost_pct=cost_pct,
                    )
                )
        for arm, trades in current_arms.items():
            arm_trades[arm].extend(trades)
        if policy is None:
            selected = []
            selected_control = []
            status = "insufficient_prior_arm_history"
        else:
            selected = current_arms[str(policy["selected_arm"])]
            selected_control = current_arms[FIXED_TP_SPLIT_CONTROL_ARM]
            selected_trades.extend(selected)
            selected_control_trades.extend(selected_control)
            status = "evaluated_prior_selected_arm"
        evaluations.append(
            {
                "evaluation_date": evaluation_date.isoformat(),
                "status": status,
                "entry_count": len(entries),
                "prior_selected_policy": policy,
                "arm_trades": current_arms,
                "selected_policy_trades": selected,
                "selected_control_trades": selected_control,
            }
        )
        history.extend(row for trades in current_arms.values() for row in trades)

    arm_summaries = {
        arm: _summary(trades, source_quality_passed=source_quality_passed)
        for arm, trades in arm_trades.items()
    }
    arm_paths = {
        arm: _fixed_tp_split_path_diagnostics(trades)
        for arm, trades in arm_trades.items()
    }
    selected_summary = _summary(
        selected_trades, source_quality_passed=source_quality_passed
    )
    control_summary = _summary(
        selected_control_trades, source_quality_passed=source_quality_passed
    )
    selected_path = _fixed_tp_split_path_diagnostics(selected_trades)
    control_path = _fixed_tp_split_path_diagnostics(selected_control_trades)
    if not source_quality_passed:
        decision = "source_quality_blocked"
    elif not sample_floor_passed:
        decision = "insufficient_coverage_dates"
    elif not selected_trades:
        decision = "insufficient_prior_arm_history"
    else:
        selected_ev = float(selected_summary["source_quality_adjusted_ev_pct"])
        control_ev = float(control_summary["source_quality_adjusted_ev_pct"])
        selected_compounded = float(
            selected_path["compounded_planned_budget_return_pct"]
        )
        control_compounded = float(control_path["compounded_planned_budget_return_pct"])
        selected_mae = float(selected_path["avg_planned_budget_mae_pct"])
        control_mae = float(control_path["avg_planned_budget_mae_pct"])
        if (
            selected_ev > 0.0
            and selected_ev >= control_ev
            and selected_compounded >= control_compounded
        ):
            decision = "fixed_tp_split_oos_positive"
        elif (
            selected_ev >= control_ev
            and selected_compounded >= control_compounded
            and selected_mae >= control_mae
        ):
            decision = "fixed_tp_split_pareto_improved"
        else:
            decision = "no_incremental_predictive_value"
    return {
        "contract": FIXED_TP_SPLIT_CONTRACT,
        "control_arm": FIXED_TP_SPLIT_CONTROL_ARM,
        "catastrophic_stop_pct_from_initial": FIXED_TP_SPLIT_CATASTROPHIC_STOP_PCT,
        "arm_evaluation_count": sum(
            row["status"]
            in {"insufficient_prior_arm_history", "evaluated_prior_selected_arm"}
            for row in evaluations
        ),
        "selected_policy_evaluation_count": sum(
            row["status"] == "evaluated_prior_selected_arm" for row in evaluations
        ),
        "arm_summaries": arm_summaries,
        "arm_path_diagnostics": arm_paths,
        "prior_selected_policy_summary_same_dates": selected_summary,
        "single_entry_control_summary_same_dates": control_summary,
        "prior_selected_policy_path": selected_path,
        "single_entry_control_path_same_dates": control_path,
        "evaluations": evaluations,
        "decision": decision,
    }


def _simulate_equal_share_carry_trade(
    entry: dict[str, Any],
    chronological_venue_series: Sequence[base.Bar],
    *,
    arm: str,
    cost_pct: float,
    observation_end_exclusive: datetime | None = None,
) -> dict[str, Any]:
    """Replay one-share legs and a fixed average-price target across dates."""
    if arm not in FIXED_TP_EQUAL_SHARE_CARRY_ARMS:
        raise ValueError(f"unknown equal-share carry arm: {arm}")
    policy = FIXED_TP_EQUAL_SHARE_CARRY_ARMS[arm]
    offsets = tuple(float(value) for value in policy["add_offsets_pct"])
    if not offsets or offsets[0] != 0.0 or any(value >= 0 for value in offsets[1:]):
        raise ValueError(f"invalid equal-share carry offsets: {arm}")
    if any(later >= earlier for earlier, later in zip(offsets, offsets[1:])):
        raise ValueError(f"equal-share carry offsets must descend: {arm}")
    entry_at = _timestamp_without_timezone(str(entry["entry_at"]))
    entry_price = float(entry["entry_price"])
    if entry_price <= 0:
        raise ValueError("entry price must be positive")
    path = [
        bar
        for bar in chronological_venue_series
        if _timestamp_without_timezone(bar.timestamp) >= entry_at
        and (
            observation_end_exclusive is None
            or _timestamp_without_timezone(bar.timestamp) < observation_end_exclusive
        )
    ]
    if not path:
        raise ValueError(f"carry entry has no market bars: {entry['entry_at']}")

    fills: list[dict[str, Any]] = [
        {
            "leg_index": 1,
            "quantity": 1,
            "price": entry_price,
            "filled_at": entry_at.isoformat(),
        }
    ]
    next_leg_index = 1
    target_eligible_after = entry_at
    exit_at: datetime | None = None
    exit_price: float | None = None
    target_price: float | None = None
    observed_mae_pct = 0.0
    observed_mfe_pct = 0.0
    observed_dates: set[date] = set()

    for bar in path:
        bar_at = _timestamp_without_timezone(bar.timestamp)
        observed_dates.add(bar.trade_date)
        added_on_bar = False
        if bar.trade_date == entry_at.date() and bar.session == str(entry["session"]):
            while next_leg_index < len(offsets):
                add_limit = float(
                    clamp_price_to_tick(
                        entry_price * (1.0 + offsets[next_leg_index] / 100.0)
                    )
                )
                if float(bar.low) > add_limit:
                    break
                fills.append(
                    {
                        "leg_index": next_leg_index + 1,
                        "quantity": 1,
                        "price": min(float(bar.open), add_limit),
                        "filled_at": bar_at.isoformat(),
                    }
                )
                next_leg_index += 1
                added_on_bar = True
        average_price = statistics.fmean(float(fill["price"]) for fill in fills)
        observed_mae_pct = min(
            observed_mae_pct,
            (float(bar.low) / average_price - 1.0) * 100.0,
        )
        observed_mfe_pct = max(
            observed_mfe_pct,
            (float(bar.high) / average_price - 1.0) * 100.0,
        )
        if added_on_bar:
            target_eligible_after = bar_at
            continue
        if bar_at <= target_eligible_after:
            continue
        target_price = float(
            move_price_up_by_bps(
                average_price,
                int(round(float(policy["target_pct"]) * 100.0)),
            )
        )
        if float(bar.high) >= target_price:
            exit_at = bar_at
            exit_price = target_price
            break

    average_price = statistics.fmean(float(fill["price"]) for fill in fills)
    completed = exit_at is not None and exit_price is not None
    observation_end_at = _timestamp_without_timezone(path[-1].timestamp)
    terminal_price = float(path[-1].close)
    gross_return_pct = (
        (float(exit_price) / average_price - 1.0) * 100.0 if completed else None
    )
    net_return_pct = (
        float(gross_return_pct) - float(cost_pct)
        if gross_return_pct is not None
        else None
    )
    return {
        **entry,
        "carry_arm": arm,
        "carry_policy_oos": True,
        "completed": completed,
        "exit_reason": "fixed_average_take_profit" if completed else "right_censored",
        "exit_at": exit_at.isoformat() if exit_at else None,
        "exit_price": round(float(exit_price), 6) if exit_price else None,
        "target_price": round(float(target_price), 6) if target_price else None,
        "gross_return_pct": (
            round(float(gross_return_pct), 6) if gross_return_pct is not None else None
        ),
        "net_return_pct": (
            round(float(net_return_pct), 6) if net_return_pct is not None else None
        ),
        "round_trip_cost_pct": float(cost_pct),
        "filled_leg_count": len(fills),
        "filled_legs": fills,
        "weighted_average_price": round(average_price, 6),
        "target_pct_from_average": float(policy["target_pct"]),
        "observed_mae_pct": round(observed_mae_pct, 6),
        "observed_mfe_pct": round(observed_mfe_pct, 6),
        "observation_end_at": observation_end_at.isoformat(),
        "terminal_price": round(terminal_price, 6),
        "right_censored_terminal_mark_pct": (
            round((terminal_price / average_price - 1.0) * 100.0, 6)
            if not completed
            else None
        ),
        "calendar_days_to_target": (
            (exit_at.date() - entry_at.date()).days if exit_at else None
        ),
        "observed_trading_day_count": len(observed_dates),
        "same_bar_target_after_fill_allowed": False,
        "additional_leg_window": "original_entry_session_only",
    }


def _equal_share_carry_path_diagnostics(
    trades: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    completed = [row for row in trades if row.get("completed") is True]
    censored = [row for row in trades if row.get("completed") is not True]
    event_rows: list[tuple[datetime, int, int]] = []
    daily_reset_runtime = any(
        trade.get("runtime_position_policy") == "one_active_bundle_daily_reset"
        for trade in trades
    )
    for trade in trades:
        event_rows.extend(
            (
                _timestamp_without_timezone(str(fill["filled_at"])),
                1,
                0,
            )
            for fill in trade.get("filled_legs", [])
        )
        entry_at = _timestamp_without_timezone(str(trade["entry_at"]))
        event_rows.append((entry_at, 0, 1))
        if trade.get("completed") is True:
            exit_at = _timestamp_without_timezone(str(trade["exit_at"]))
            event_rows.append((exit_at, -int(trade["filled_leg_count"]), -1))
        elif trade.get("runtime_position_policy") == "one_active_bundle_daily_reset":
            reset_at = datetime.combine(entry_at.date() + timedelta(days=1), time.min)
            event_rows.append((reset_at, -int(trade["filled_leg_count"]), -1))
    open_shares = 0
    open_bundles = 0
    max_open_shares = 0
    max_open_bundles = 0
    for _, share_delta, bundle_delta in sorted(
        event_rows,
        key=lambda item: (item[0], item[1] > 0, item[2] > 0),
    ):
        open_shares += share_delta
        open_bundles += bundle_delta
        max_open_shares = max(max_open_shares, open_shares)
        max_open_bundles = max(max_open_bundles, open_bundles)
    net_values = [float(row["net_return_pct"]) for row in completed]
    calendar_days = [int(row["calendar_days_to_target"]) for row in completed]
    return {
        "sample_count": len(trades),
        "completed_trade_count": len(completed),
        "right_censored_count": len(censored),
        "target_completion_ratio": (
            round(len(completed) / len(trades), 6) if trades else None
        ),
        "completed_equal_weight_avg_profit_pct": (
            round(statistics.fmean(net_values), 6) if net_values else None
        ),
        "completed_simple_sum_profit_pct": (
            round(sum(net_values), 6) if net_values else None
        ),
        "same_day_target_count": sum(value == 0 for value in calendar_days),
        "cross_day_target_count": sum(value > 0 for value in calendar_days),
        "median_calendar_days_to_target": (
            statistics.median(calendar_days) if calendar_days else None
        ),
        "max_calendar_days_to_target": max(calendar_days) if calendar_days else None,
        "avg_filled_leg_count": (
            round(
                statistics.fmean(float(row["filled_leg_count"]) for row in trades),
                6,
            )
            if trades
            else None
        ),
        "avg_observed_mae_pct": (
            round(
                statistics.fmean(float(row["observed_mae_pct"]) for row in trades),
                6,
            )
            if trades
            else None
        ),
        "worst_observed_mae_pct": (
            min(float(row["observed_mae_pct"]) for row in trades) if trades else None
        ),
        "max_concurrent_bundle_count": max_open_bundles,
        "max_concurrent_share_units": max_open_shares,
        "ending_open_bundle_count": 0 if daily_reset_runtime else len(censored),
        "ending_open_share_units": (
            0
            if daily_reset_runtime
            else sum(int(row["filled_leg_count"]) for row in censored)
        ),
        "cumulative_unmanaged_inventory_bundle_count": (
            len(censored) if daily_reset_runtime else None
        ),
        "cumulative_unmanaged_inventory_share_units": (
            sum(int(row["filled_leg_count"]) for row in censored)
            if daily_reset_runtime
            else None
        ),
        "right_censored_terminal_marks_pct": [
            row.get("right_censored_terminal_mark_pct") for row in censored
        ],
    }


def _simulate_daily_reset_single_bundle_arm(
    entries: Sequence[dict[str, Any]],
    chronological_venue_series: Sequence[base.Bar],
    *,
    arm: str,
    cost_pct: float,
    observation_end_exclusive: datetime | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Replay the actual widget constraint: one active bundle per trade date.

    An uncompleted bundle blocks later entries on that date, then becomes
    unmanaged inventory at the daily state reset.  It does not block the next
    date and a later-day target touch is not counted as an automated exit.
    """
    selected: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    blocked_until_by_date: dict[date, datetime | None] = {}
    for entry in sorted(
        entries, key=lambda row: _timestamp_without_timezone(str(row["entry_at"]))
    ):
        entry_at = _timestamp_without_timezone(str(entry["entry_at"]))
        trade_date = entry_at.date()
        blocked_until = blocked_until_by_date.get(trade_date)
        if trade_date in blocked_until_by_date and (
            blocked_until is None or entry_at <= blocked_until
        ):
            skipped.append(
                {
                    "entry_at": entry_at.isoformat(),
                    "entry_price": entry.get("entry_price"),
                    "session": entry.get("session"),
                    "reason": "single_active_bundle_capacity",
                }
            )
            continue
        next_date = datetime.combine(trade_date + timedelta(days=1), time.min)
        entry_observation_end = next_date
        if (
            observation_end_exclusive is not None
            and observation_end_exclusive < entry_observation_end
        ):
            entry_observation_end = observation_end_exclusive
        trade = _simulate_equal_share_carry_trade(
            entry,
            chronological_venue_series,
            arm=arm,
            cost_pct=cost_pct,
            observation_end_exclusive=entry_observation_end,
        )
        trade["runtime_capacity_selected"] = True
        trade["runtime_position_policy"] = "one_active_bundle_daily_reset"
        selected.append(trade)
        blocked_until_by_date[trade_date] = (
            _timestamp_without_timezone(str(trade["exit_at"]))
            if trade.get("completed") is True
            else None
        )
    return selected, skipped


def _fixed_tp_equal_share_carry_replay(
    economic_evaluations: Sequence[dict[str, Any]],
    series_by_key: dict[tuple[date, str, str], Sequence[base.Bar]],
    *,
    venue: str,
    cost_pct: float,
    sample_floor_passed: bool,
    source_quality_passed: bool,
) -> dict[str, Any]:
    evaluation_dates = sorted(
        date.fromisoformat(str(row["evaluation_date"]))
        for row in economic_evaluations
        if row.get("selected_trades")
    )
    chronological_series = sorted(
        (
            bar
            for (trade_date, key_venue, _), series in series_by_key.items()
            if key_venue == venue
            for bar in series
        ),
        key=lambda bar: bar.timestamp,
    )
    if len(evaluation_dates) <= FIXED_TP_CARRY_HOLDOUT_DATES:
        return {
            "contract": FIXED_TP_EQUAL_SHARE_CARRY_CONTRACT,
            "decision": "insufficient_evaluation_dates",
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
        }
    holdout_dates = evaluation_dates[-FIXED_TP_CARRY_HOLDOUT_DATES:]
    holdout_start = datetime.combine(holdout_dates[0], datetime.min.time())
    calibration_entries = [
        entry
        for evaluation in economic_evaluations
        if date.fromisoformat(str(evaluation["evaluation_date"])) < holdout_dates[0]
        for entry in evaluation.get("selected_trades", [])
    ]
    holdout_entries = [
        entry
        for evaluation in economic_evaluations
        if date.fromisoformat(str(evaluation["evaluation_date"])) >= holdout_dates[0]
        for entry in evaluation.get("selected_trades", [])
    ]
    calibration_arm_results = {
        arm: _simulate_daily_reset_single_bundle_arm(
            calibration_entries,
            chronological_series,
            arm=arm,
            cost_pct=cost_pct,
            observation_end_exclusive=holdout_start,
        )
        for arm in FIXED_TP_EQUAL_SHARE_CARRY_ARMS
    }
    calibration_arm_trades = {
        arm: result[0] for arm, result in calibration_arm_results.items()
    }
    calibration_arm_skipped = {
        arm: result[1] for arm, result in calibration_arm_results.items()
    }
    calibration_summaries = {
        arm: _equal_share_carry_path_diagnostics(trades)
        for arm, trades in calibration_arm_trades.items()
    }

    def rank(arm: str) -> tuple[float, float, float, float, int]:
        summary = calibration_summaries[arm]
        return (
            float(summary["completed_trade_count"]),
            -float(summary["median_calendar_days_to_target"] or 0.0),
            float(summary["avg_observed_mae_pct"] or -999.0),
            -float(summary["avg_filled_leg_count"] or 999.0),
            -list(FIXED_TP_EQUAL_SHARE_CARRY_ARMS).index(arm),
        )

    selected_arm = max(FIXED_TP_EQUAL_SHARE_CARRY_ARMS, key=rank)
    selected_calibration_summary = calibration_summaries[selected_arm]
    holdout_arm_results = {
        arm: _simulate_daily_reset_single_bundle_arm(
            holdout_entries,
            chronological_series,
            arm=arm,
            cost_pct=cost_pct,
        )
        for arm in FIXED_TP_EQUAL_SHARE_CARRY_ARMS
    }
    holdout_arm_trades = {arm: result[0] for arm, result in holdout_arm_results.items()}
    holdout_arm_skipped = {
        arm: result[1] for arm, result in holdout_arm_results.items()
    }
    holdout_summaries = {
        arm: _equal_share_carry_path_diagnostics(trades)
        for arm, trades in holdout_arm_trades.items()
    }
    selected_summary = holdout_summaries[selected_arm]
    if not source_quality_passed:
        decision = "source_quality_blocked"
    elif not sample_floor_passed:
        decision = "insufficient_coverage_dates"
    elif (
        int(selected_calibration_summary["sample_count"])
        < FIXED_TP_CARRY_MIN_CALIBRATION_ENTRIES
    ):
        decision = "insufficient_calibration_entries"
    elif (
        int(selected_summary["completed_trade_count"])
        < FIXED_TP_CARRY_MIN_HOLDOUT_COMPLETIONS
    ):
        decision = "insufficient_holdout_completions"
    elif float(selected_summary["completed_equal_weight_avg_profit_pct"] or 0.0) <= 0:
        decision = "holdout_completed_profit_not_positive"
    else:
        decision = "widget_auto_trade_policy_candidate_ready"
    selected_policy = FIXED_TP_EQUAL_SHARE_CARRY_ARMS[selected_arm]
    return {
        "contract": FIXED_TP_EQUAL_SHARE_CARRY_CONTRACT,
        "evaluation_date_count": len(evaluation_dates),
        "calibration_date_count": len(evaluation_dates) - len(holdout_dates),
        "holdout_date_count": len(holdout_dates),
        "holdout_dates": [value.isoformat() for value in holdout_dates],
        "holdout_start_exclusive_calibration_boundary": holdout_start.isoformat(),
        "calibration_entry_count": len(calibration_entries),
        "holdout_entry_count": len(holdout_entries),
        "calibration_arm_summaries": calibration_summaries,
        "selected_calibration_summary": selected_calibration_summary,
        "calibration_capacity_skipped_counts": {
            arm: len(rows) for arm, rows in calibration_arm_skipped.items()
        },
        "selected_arm": selected_arm,
        "selected_policy": {
            "leg_quantity_each": 1,
            "add_offsets_pct": list(selected_policy["add_offsets_pct"]),
            "target_pct_from_equal_share_average": selected_policy["target_pct"],
            "ordinary_stop": None,
            "catastrophic_stop": None,
            "unhit_policy": "right_censored_hold_without_forced_exit",
            "position_capacity": "one_active_bundle_per_symbol_per_trade_date",
            "daily_reset": "unhit_inventory_unmanaged_next_trade_date",
        },
        "selection_policy": (
            "calibration_completed_count_then_faster_target_then_less_adverse_"
            "mae_then_fewer_equal_share_legs"
        ),
        "holdout_arm_summaries": holdout_summaries,
        "holdout_capacity_skipped_counts": {
            arm: len(rows) for arm, rows in holdout_arm_skipped.items()
        },
        "selected_holdout_summary": selected_summary,
        "selected_holdout_trades": holdout_arm_trades[selected_arm],
        "decision": decision,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def _fixed_tp_entry_quality_features(trade: dict[str, Any]) -> list[float]:
    event_probabilities = dict(trade.get("predicted_event_probabilities") or {})
    values = [
        *(float(value) for value in trade["economic_features"]),
        float(trade["predicted_cost_adjusted_ev_pct"]),
        float(event_probabilities.get("favorable_first_passage") or 0.0),
        float(event_probabilities.get("adverse_first_passage") or 0.0),
        float(event_probabilities.get("session_end_censored") or 0.0),
    ]
    if len(values) != len(FIXED_TP_ENTRY_QUALITY_FEATURE_NAMES) or not all(
        math.isfinite(value) for value in values
    ):
        raise ValueError("fixed TP entry-quality features are invalid")
    return values


def _fit_fixed_tp_entry_quality_model(
    prior_trades: Sequence[dict[str, Any]],
) -> tuple[Any, dict[str, Any]] | None:
    if not prior_trades:
        return None
    labels = np.asarray(
        [
            int(str(row["exit_reason"]).startswith("catastrophic"))
            for row in prior_trades
        ],
        dtype=int,
    )
    if len(set(labels.tolist())) < 2:
        return None
    features = np.asarray(
        [_fixed_tp_entry_quality_features(row) for row in prior_trades],
        dtype=float,
    )
    model = make_pipeline(
        StandardScaler(),
        LogisticRegression(
            C=0.25,
            max_iter=2_000,
            random_state=17,
            solver="liblinear",
        ),
    )
    model.fit(features, labels)
    catastrophic = [
        row
        for row, label in zip(prior_trades, labels.tolist(), strict=True)
        if label == 1
    ]
    noncatastrophic = [
        row
        for row, label in zip(prior_trades, labels.tolist(), strict=True)
        if label == 0
    ]
    fit_max_date = max(
        date.fromisoformat(str(row["trade_date"])) for row in prior_trades
    )
    return model, {
        "fit_max_date": fit_max_date.isoformat(),
        "prior_trade_count": len(prior_trades),
        "prior_evaluation_date_count": len(
            {str(row["trade_date"]) for row in prior_trades}
        ),
        "prior_catastrophic_count": len(catastrophic),
        "prior_noncatastrophic_count": len(noncatastrophic),
        "prior_catastrophic_rate": round(len(catastrophic) / len(prior_trades), 6),
        "prior_catastrophic_ev_pct": round(
            statistics.fmean(float(row["net_profit_pct"]) for row in catastrophic),
            6,
        ),
        "prior_noncatastrophic_ev_pct": round(
            statistics.fmean(float(row["net_profit_pct"]) for row in noncatastrophic),
            6,
        ),
        "probability_shrinkage_prior": FIXED_TP_ENTRY_QUALITY_SHRINKAGE_PRIOR,
    }


def _fixed_tp_split_entry_quality_walk_forward(
    fixed_split_evaluations: Sequence[dict[str, Any]],
    *,
    sample_floor_passed: bool,
    source_quality_passed: bool,
) -> dict[str, Any]:
    history: list[dict[str, Any]] = []
    selected_trades: list[dict[str, Any]] = []
    control_trades: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    evaluations: list[dict[str, Any]] = []
    cumulative_enter_count = 0
    cumulative_skip_count = 0
    for fixed_evaluation in fixed_split_evaluations:
        evaluation_date = date.fromisoformat(str(fixed_evaluation["evaluation_date"]))
        current = list(
            (fixed_evaluation.get("arm_trades") or {}).get(
                FIXED_TP_ENTRY_QUALITY_EXECUTION_ARM, []
            )
        )
        if not current:
            evaluations.append(
                {
                    "evaluation_date": evaluation_date.isoformat(),
                    "status": "no_fixed_entry_cohort",
                    "model": None,
                    "control_trades": [],
                    "selected_trades": [],
                    "decisions": [],
                }
            )
            continue
        fitted = _fit_fixed_tp_entry_quality_model(history)
        if fitted is None:
            cumulative_enter_count += len(current)
            evaluations.append(
                {
                    "evaluation_date": evaluation_date.isoformat(),
                    "status": "insufficient_prior_failure_history",
                    "model": None,
                    "control_trades": [],
                    "selected_trades": [],
                    "decisions": [],
                    "observed_fixed_arm_trade_count": len(current),
                }
            )
            history.extend(current)
            continue
        model, model_meta = fitted
        if date.fromisoformat(str(model_meta["fit_max_date"])) >= evaluation_date:
            raise ValueError("fixed TP entry-quality model uses current outcomes")
        ordered = sorted(current, key=lambda row: str(row["entry_at"]))
        current_floor = max(
            1,
            math.ceil(len(ordered) * FIXED_TP_ENTRY_QUALITY_OPPORTUNITY_RETENTION),
        )
        current_selected: list[dict[str, Any]] = []
        current_decisions: list[dict[str, Any]] = []
        current_skip_count = 0
        current_entries_since_skip = 0
        for trade in ordered:
            raw_probability = float(
                model.predict_proba(
                    np.asarray([_fixed_tp_entry_quality_features(trade)], dtype=float)
                )[0][1]
            )
            reliability = len(history) / (
                len(history) + FIXED_TP_ENTRY_QUALITY_SHRINKAGE_PRIOR
            )
            catastrophic_probability = reliability * raw_probability + (
                1.0 - reliability
            ) * float(model_meta["prior_catastrophic_rate"])
            predicted_net_ev = catastrophic_probability * float(
                model_meta["prior_catastrophic_ev_pct"]
            ) + (1.0 - catastrophic_probability) * float(
                model_meta["prior_noncatastrophic_ev_pct"]
            )
            skip_capacity = current_entries_since_skip >= 3
            if predicted_net_ev < 0.0 and skip_capacity:
                action = "skip_negative_expected_ev"
                current_skip_count += 1
                current_entries_since_skip = 0
            else:
                action = (
                    "enter_positive_expected_ev"
                    if predicted_net_ev >= 0.0
                    else "enter_bounded_exploration"
                )
                selected = {
                    **trade,
                    "entry_quality_oos": True,
                    "entry_quality_action": action,
                    "entry_quality_model_fit_max_date": model_meta["fit_max_date"],
                    "predicted_catastrophic_probability": round(
                        catastrophic_probability, 6
                    ),
                    "predicted_fixed_execution_net_ev_pct": round(predicted_net_ev, 6),
                }
                current_selected.append(selected)
                current_entries_since_skip += 1
            decision = {
                "trade_date": str(trade["trade_date"]),
                "venue": str(trade["venue"]),
                "session": str(trade["session"]),
                "entry_at": str(trade["entry_at"]),
                "entry_price": float(trade["entry_price"]),
                "model_fit_max_date": model_meta["fit_max_date"],
                "raw_catastrophic_probability": round(raw_probability, 6),
                "predicted_catastrophic_probability": round(
                    catastrophic_probability, 6
                ),
                "predicted_fixed_execution_net_ev_pct": round(predicted_net_ev, 6),
                "action": action,
                "skip_capacity_available": skip_capacity,
                "post_oos_outcome_attribution": {
                    "exit_reason": str(trade["exit_reason"]),
                    "planned_budget_return_pct": float(trade["net_profit_pct"]),
                    "catastrophic": bool(
                        str(trade["exit_reason"]).startswith("catastrophic")
                    ),
                },
            }
            current_decisions.append(decision)
            decisions.append(decision)
        if len(current_selected) < current_floor:
            raise ValueError("fixed TP entry-quality current-date retention breached")
        cumulative_enter_count += len(current_selected)
        cumulative_skip_count += current_skip_count
        cumulative_retention = cumulative_enter_count / (
            cumulative_enter_count + cumulative_skip_count
        )
        if cumulative_retention < FIXED_TP_ENTRY_QUALITY_OPPORTUNITY_RETENTION:
            raise ValueError("fixed TP entry-quality cumulative retention breached")
        selected_trades.extend(current_selected)
        control_trades.extend(ordered)
        evaluations.append(
            {
                "evaluation_date": evaluation_date.isoformat(),
                "status": "evaluated_prior_only_entry_quality",
                "model": model_meta,
                "control_trades": ordered,
                "selected_trades": current_selected,
                "decisions": current_decisions,
                "capacity": {
                    "control_count": len(ordered),
                    "opportunity_floor_count": current_floor,
                    "selected_count": len(current_selected),
                    "skip_count": current_skip_count,
                    "current_retention": round(len(current_selected) / len(ordered), 6),
                    "cumulative_enter_count": cumulative_enter_count,
                    "cumulative_skip_count": cumulative_skip_count,
                    "cumulative_retention": round(cumulative_retention, 6),
                },
            }
        )
        history.extend(current)

    selected_summary = _summary(
        selected_trades, source_quality_passed=source_quality_passed
    )
    control_summary = _summary(
        control_trades, source_quality_passed=source_quality_passed
    )
    selected_path = _fixed_tp_split_path_diagnostics(selected_trades)
    control_path = _fixed_tp_split_path_diagnostics(control_trades)
    evaluated_count = sum(
        row["status"] == "evaluated_prior_only_entry_quality" for row in evaluations
    )
    final_retention = (
        len(selected_trades) / len(control_trades) if control_trades else None
    )
    skipped = [row for row in decisions if row["action"] == "skip_negative_expected_ev"]
    prediction_labels = [
        int(bool(row["post_oos_outcome_attribution"]["catastrophic"]))
        for row in decisions
    ]
    prediction_probabilities = [
        float(row["predicted_catastrophic_probability"]) for row in decisions
    ]
    prediction_diagnostics = {
        "metric_role": "post_oos_catastrophic_risk_discrimination_diagnostic",
        "decision_authority": "diagnostic_only_not_same_report_selection",
        "sample_count": len(decisions),
        "catastrophic_count": sum(prediction_labels),
        "catastrophic_prevalence": (
            round(statistics.fmean(prediction_labels), 6) if prediction_labels else None
        ),
        "catastrophic_average_precision": (
            round(
                float(
                    average_precision_score(prediction_labels, prediction_probabilities)
                ),
                6,
            )
            if len(set(prediction_labels)) == 2
            else None
        ),
        "brier_score": (
            round(
                statistics.fmean(
                    (actual - predicted) ** 2
                    for actual, predicted in zip(
                        prediction_labels,
                        prediction_probabilities,
                        strict=True,
                    )
                ),
                6,
            )
            if prediction_labels
            else None
        ),
        "forbidden_uses": [
            "same_report_threshold_or_feature_selection",
            "runtime_or_order_authority",
        ],
    }
    if not source_quality_passed:
        decision = "source_quality_blocked"
    elif not sample_floor_passed:
        decision = "insufficient_coverage_dates"
    elif not selected_trades or not control_trades:
        decision = "insufficient_prior_failure_history"
    else:
        selected_ev = float(selected_summary["source_quality_adjusted_ev_pct"])
        control_ev = float(control_summary["source_quality_adjusted_ev_pct"])
        selected_compounded = float(
            selected_path["compounded_planned_budget_return_pct"]
        )
        control_compounded = float(control_path["compounded_planned_budget_return_pct"])
        selected_catastrophic = int(selected_path["catastrophic_stop_count"])
        control_catastrophic = int(control_path["catastrophic_stop_count"])
        strict_improvement = bool(
            selected_ev > control_ev
            or selected_compounded > control_compounded
            or selected_catastrophic < control_catastrophic
        )
        if (
            final_retention is not None
            and final_retention >= FIXED_TP_ENTRY_QUALITY_OPPORTUNITY_RETENTION
            and selected_ev > 0.0
            and selected_ev >= control_ev
            and selected_compounded >= control_compounded
        ):
            decision = "entry_quality_oos_positive"
        elif (
            final_retention is not None
            and final_retention >= FIXED_TP_ENTRY_QUALITY_OPPORTUNITY_RETENTION
            and strict_improvement
            and selected_ev >= control_ev
            and selected_compounded >= control_compounded
            and selected_catastrophic <= control_catastrophic
        ):
            decision = "entry_quality_pareto_improved"
        else:
            decision = "no_incremental_predictive_value"
    return {
        "contract": FIXED_TP_ENTRY_QUALITY_CONTRACT,
        "feature_names": FIXED_TP_ENTRY_QUALITY_FEATURE_NAMES,
        "fixed_execution_arm": FIXED_TP_ENTRY_QUALITY_EXECUTION_ARM,
        "evaluation_count": evaluated_count,
        "control_summary_same_dates": control_summary,
        "selected_summary": selected_summary,
        "control_path_same_dates": control_path,
        "selected_path": selected_path,
        "capacity_diagnostics": {
            "required_opportunity_retention": (
                FIXED_TP_ENTRY_QUALITY_OPPORTUNITY_RETENTION
            ),
            "control_count": len(control_trades),
            "selected_count": len(selected_trades),
            "skipped_count": len(skipped),
            "selected_vs_control_retention": (
                round(final_retention, 6) if final_retention is not None else None
            ),
            "bounded_exploration_enter_count": sum(
                row["action"] == "enter_bounded_exploration" for row in decisions
            ),
            "positive_expected_ev_enter_count": sum(
                row["action"] == "enter_positive_expected_ev" for row in decisions
            ),
            "skipped_catastrophic_count": sum(
                bool(row["post_oos_outcome_attribution"]["catastrophic"])
                for row in skipped
            ),
            "skipped_noncatastrophic_count": sum(
                not bool(row["post_oos_outcome_attribution"]["catastrophic"])
                for row in skipped
            ),
            "skipped_positive_return_count": sum(
                float(row["post_oos_outcome_attribution"]["planned_budget_return_pct"])
                > 0.0
                for row in skipped
            ),
        },
        "prediction_diagnostics": prediction_diagnostics,
        "evaluations": evaluations,
        "decision": decision,
    }


def _recoverable_basin_features(trade: dict[str, Any]) -> list[float]:
    scale = max(float(trade["volatility_scale_pct"]), 1e-6)
    values = [
        *_fixed_tp_entry_quality_features(trade),
        0.8 / scale,
        0.5 / scale,
        FIXED_TP_SPLIT_CATASTROPHIC_STOP_PCT / scale,
    ]
    if len(values) != len(RECOVERABLE_BASIN_FEATURE_NAMES) or not all(
        math.isfinite(value) for value in values
    ):
        raise ValueError("recoverable-basin features are invalid")
    return values


def _fit_recoverable_basin_model(
    prior_trades: Sequence[dict[str, Any]],
) -> tuple[Any, dict[str, Any]] | None:
    if not prior_trades:
        return None
    features = np.asarray(
        [_recoverable_basin_features(row) for row in prior_trades], dtype=float
    )
    outcomes = np.asarray(
        [float(row["net_profit_pct"]) for row in prior_trades], dtype=float
    )
    model = make_pipeline(StandardScaler(), Ridge(alpha=16.0))
    model.fit(features, outcomes)
    fit_max_date = max(
        date.fromisoformat(str(row["trade_date"])) for row in prior_trades
    )
    return model, {
        "fit_max_date": fit_max_date.isoformat(),
        "prior_trade_count": len(prior_trades),
        "prior_evaluation_date_count": len(
            {str(row["trade_date"]) for row in prior_trades}
        ),
        "prior_mean_fixed_execution_net_ev_pct": round(
            statistics.fmean(outcomes.tolist()), 6
        ),
        "prior_positive_return_count": int(sum(outcomes > 0.0)),
        "prior_catastrophic_count": sum(
            str(row["exit_reason"]).startswith("catastrophic") for row in prior_trades
        ),
        "prediction_shrinkage_prior": RECOVERABLE_BASIN_SHRINKAGE_PRIOR,
        "model": "standardized_ridge_alpha16",
    }


def _simulate_recoverable_basin_candidates(
    candidate_rows: Sequence[dict[str, Any]],
    series_by_key: dict[tuple[date, str, str], Sequence[base.Bar]],
    *,
    venue: str,
    cost_pct: float,
) -> list[dict[str, Any]]:
    simulated: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str]] = set()
    for candidate in sorted(candidate_rows, key=lambda row: str(row["entry_at"])):
        identity = _entry_identity(candidate)
        if identity in seen:
            raise ValueError(f"duplicate recoverable-basin candidate: {identity!r}")
        seen.add(identity)
        trade_date = date.fromisoformat(str(candidate["trade_date"]))
        key = (trade_date, venue, str(candidate["session"]))
        series = series_by_key.get(key)
        if not series:
            raise ValueError(f"recoverable-basin candidate has no series: {key}")
        simulated.append(
            _simulate_fixed_tp_split_trade(
                candidate,
                series,
                arm=RECOVERABLE_BASIN_EXECUTION_ARM,
                cost_pct=cost_pct,
            )
        )
    return simulated


def _recoverable_basin_walk_forward(
    candidate_evaluations: Sequence[dict[str, Any]],
    fixed_split_evaluations: Sequence[dict[str, Any]],
    series_by_key: dict[tuple[date, str, str], Sequence[base.Bar]],
    *,
    venue: str,
    cost_pct: float,
    sample_floor_passed: bool,
    source_quality_passed: bool,
) -> dict[str, Any]:
    economic_baseline_by_date = {
        str(row["evaluation_date"]): list(
            (row.get("arm_trades") or {}).get(RECOVERABLE_BASIN_EXECUTION_ARM, [])
        )
        for row in fixed_split_evaluations
    }
    history: list[dict[str, Any]] = []
    broader_control_trades: list[dict[str, Any]] = []
    economic_baseline_trades: list[dict[str, Any]] = []
    selected_trades: list[dict[str, Any]] = []
    evaluations: list[dict[str, Any]] = []
    all_decisions: list[dict[str, Any]] = []
    for candidate_evaluation in candidate_evaluations:
        evaluation_date = date.fromisoformat(
            str(candidate_evaluation["evaluation_date"])
        )
        candidates = list(candidate_evaluation.get("candidate_trades") or [])
        if not candidates:
            evaluations.append(
                {
                    "evaluation_date": evaluation_date.isoformat(),
                    "status": "no_broader_candidate_universe",
                    "model": None,
                    "raw_candidate_count": 0,
                    "decisions": [],
                }
            )
            continue
        current = _simulate_recoverable_basin_candidates(
            candidates,
            series_by_key,
            venue=venue,
            cost_pct=cost_pct,
        )
        fitted = _fit_recoverable_basin_model(history)
        if fitted is None:
            evaluations.append(
                {
                    "evaluation_date": evaluation_date.isoformat(),
                    "status": "insufficient_prior_candidate_history",
                    "model": None,
                    "raw_candidate_count": len(current),
                    "decisions": [],
                }
            )
            history.extend(current)
            continue
        model, model_meta = fitted
        if date.fromisoformat(str(model_meta["fit_max_date"])) >= evaluation_date:
            raise ValueError("recoverable-basin model uses current outcomes")
        reliability = len(history) / (len(history) + RECOVERABLE_BASIN_SHRINKAGE_PRIOR)
        scored: list[dict[str, Any]] = []
        for trade in current:
            raw_prediction = float(
                model.predict(
                    np.asarray([_recoverable_basin_features(trade)], dtype=float)
                )[0]
            )
            predicted_ev = reliability * raw_prediction + (1.0 - reliability) * float(
                model_meta["prior_mean_fixed_execution_net_ev_pct"]
            )
            scored.append(
                {
                    **trade,
                    "recoverable_basin_oos": True,
                    "recoverable_basin_model_fit_max_date": model_meta["fit_max_date"],
                    "raw_predicted_fixed_execution_net_ev_pct": round(
                        raw_prediction, 6
                    ),
                    "predicted_fixed_execution_net_ev_pct": round(predicted_ev, 6),
                }
            )
        broader_control = _non_overlapping_candidates(scored, selected_only=False)
        current_selected: list[dict[str, Any]] = []
        current_decisions: list[dict[str, Any]] = []
        grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        for row in scored:
            grouped[(str(row["venue"]), str(row["session"]))].append(row)
        for session_rows in grouped.values():
            next_available: datetime | None = None
            entries_since_skip = 0
            for trade in sorted(session_rows, key=lambda row: str(row["entry_at"])):
                entry_at = datetime.fromisoformat(str(trade["entry_at"]))
                predicted_ev = float(trade["predicted_fixed_execution_net_ev_pct"])
                if next_available is not None and entry_at < next_available:
                    action = "position_occupied"
                else:
                    skip_capacity = entries_since_skip >= 3
                    if predicted_ev < 0.0 and skip_capacity:
                        action = "skip_negative_expected_ev"
                        entries_since_skip = 0
                    else:
                        action = (
                            "enter_positive_expected_ev"
                            if predicted_ev >= 0.0
                            else "enter_bounded_exploration"
                        )
                        current_selected.append(trade)
                        entries_since_skip += 1
                        next_available = datetime.fromisoformat(str(trade["exit_at"]))
                decision = {
                    "trade_date": str(trade["trade_date"]),
                    "venue": str(trade["venue"]),
                    "session": str(trade["session"]),
                    "entry_at": str(trade["entry_at"]),
                    "entry_price": float(trade["entry_price"]),
                    "model_fit_max_date": model_meta["fit_max_date"],
                    "predicted_fixed_execution_net_ev_pct": predicted_ev,
                    "action": action,
                    "post_oos_outcome_attribution": {
                        "exit_reason": str(trade["exit_reason"]),
                        "planned_budget_return_pct": float(trade["net_profit_pct"]),
                        "catastrophic": bool(
                            str(trade["exit_reason"]).startswith("catastrophic")
                        ),
                    },
                }
                current_decisions.append(decision)
                all_decisions.append(decision)
        retention = (
            len(current_selected) / len(broader_control) if broader_control else None
        )
        if (
            retention is not None
            and retention < RECOVERABLE_BASIN_OPPORTUNITY_RETENTION
        ):
            raise ValueError("recoverable-basin opportunity retention breached")
        current_economic_baseline = economic_baseline_by_date.get(
            evaluation_date.isoformat(), []
        )
        broader_control_trades.extend(broader_control)
        economic_baseline_trades.extend(current_economic_baseline)
        selected_trades.extend(current_selected)
        evaluations.append(
            {
                "evaluation_date": evaluation_date.isoformat(),
                "status": "evaluated_prior_only_recoverable_basin",
                "model": model_meta,
                "raw_candidate_count": len(current),
                "decisions": current_decisions,
                "trade_detail_storage": "omitted_replayable_from_source_bars",
                "capacity": {
                    "broader_control_count": len(broader_control),
                    "economic_selected_baseline_count": len(current_economic_baseline),
                    "selected_count": len(current_selected),
                    "selected_vs_broader_control_retention": (
                        round(retention, 6) if retention is not None else None
                    ),
                    "model_skip_count": sum(
                        row["action"] == "skip_negative_expected_ev"
                        for row in current_decisions
                    ),
                    "position_occupied_count": sum(
                        row["action"] == "position_occupied"
                        for row in current_decisions
                    ),
                },
            }
        )
        history.extend(current)

    broader_summary = _summary(
        broader_control_trades, source_quality_passed=source_quality_passed
    )
    economic_summary = _summary(
        economic_baseline_trades, source_quality_passed=source_quality_passed
    )
    selected_summary = _summary(
        selected_trades, source_quality_passed=source_quality_passed
    )
    broader_path = _fixed_tp_split_path_diagnostics(broader_control_trades)
    economic_path = _fixed_tp_split_path_diagnostics(economic_baseline_trades)
    selected_path = _fixed_tp_split_path_diagnostics(selected_trades)
    predictions = [
        float(row["predicted_fixed_execution_net_ev_pct"])
        for row in all_decisions
        if row["action"] != "position_occupied"
    ]
    outcomes = [
        float(row["post_oos_outcome_attribution"]["planned_budget_return_pct"])
        for row in all_decisions
        if row["action"] != "position_occupied"
    ]
    prediction_diagnostics = {
        "metric_role": "post_oos_direct_ev_prediction_diagnostic",
        "decision_authority": "diagnostic_only_not_same_report_selection",
        "sample_count": len(predictions),
        "mean_predicted_ev_pct": (
            round(statistics.fmean(predictions), 6) if predictions else None
        ),
        "mean_realized_ev_pct": (
            round(statistics.fmean(outcomes), 6) if outcomes else None
        ),
        "mean_absolute_error_pct": (
            round(
                statistics.fmean(
                    abs(actual - predicted)
                    for actual, predicted in zip(outcomes, predictions, strict=True)
                ),
                6,
            )
            if predictions
            else None
        ),
        "pearson_correlation": (
            round(float(np.corrcoef(predictions, outcomes)[0][1]), 6)
            if len(predictions) > 1
            and statistics.pstdev(predictions) > 0.0
            and statistics.pstdev(outcomes) > 0.0
            else None
        ),
        "predicted_positive_count": sum(value >= 0.0 for value in predictions),
        "predicted_positive_realized_positive_count": sum(
            predicted >= 0.0 and actual > 0.0
            for predicted, actual in zip(predictions, outcomes, strict=True)
        ),
        "forbidden_uses": [
            "same_report_threshold_or_feature_selection",
            "runtime_or_order_authority",
        ],
    }
    evaluated_count = sum(
        row["status"] == "evaluated_prior_only_recoverable_basin" for row in evaluations
    )
    aggregate_retention = (
        len(selected_trades) / len(broader_control_trades)
        if broader_control_trades
        else None
    )
    skipped = [
        row for row in all_decisions if row["action"] == "skip_negative_expected_ev"
    ]
    if not source_quality_passed:
        decision = "source_quality_blocked"
    elif not sample_floor_passed:
        decision = "insufficient_coverage_dates"
    elif not selected_trades or not broader_control_trades:
        decision = "insufficient_prior_candidate_history"
    else:
        selected_ev = float(selected_summary["source_quality_adjusted_ev_pct"])
        broader_ev = float(broader_summary["source_quality_adjusted_ev_pct"])
        economic_ev = float(economic_summary["source_quality_adjusted_ev_pct"])
        selected_compounded = float(
            selected_path["compounded_planned_budget_return_pct"]
        )
        broader_compounded = float(broader_path["compounded_planned_budget_return_pct"])
        economic_compounded = float(
            economic_path["compounded_planned_budget_return_pct"]
        )
        if (
            aggregate_retention is not None
            and aggregate_retention >= RECOVERABLE_BASIN_OPPORTUNITY_RETENTION
            and selected_ev > 0.0
            and selected_compounded > 0.0
        ):
            decision = "recoverable_basin_oos_positive"
        elif (
            aggregate_retention is not None
            and aggregate_retention >= RECOVERABLE_BASIN_OPPORTUNITY_RETENTION
            and selected_ev >= broader_ev
            and selected_ev >= economic_ev
            and selected_compounded >= broader_compounded
            and selected_compounded >= economic_compounded
            and (selected_ev > broader_ev or selected_ev > economic_ev)
        ):
            decision = "recoverable_basin_pareto_improved"
        else:
            decision = "broader_universe_no_incremental_value"
    return {
        "contract": RECOVERABLE_BASIN_CONTRACT,
        "feature_names": RECOVERABLE_BASIN_FEATURE_NAMES,
        "fixed_execution_arm": RECOVERABLE_BASIN_EXECUTION_ARM,
        "evaluation_count": evaluated_count,
        "broader_control_summary_same_dates": broader_summary,
        "economic_selected_baseline_summary_same_dates": economic_summary,
        "selected_summary": selected_summary,
        "path_diagnostics": {
            "broader_control": broader_path,
            "economic_selected_baseline": economic_path,
            "recoverable_basin_selected": selected_path,
        },
        "capacity_diagnostics": {
            "required_opportunity_retention": (RECOVERABLE_BASIN_OPPORTUNITY_RETENTION),
            "raw_candidate_count": len(history),
            "broader_control_count": len(broader_control_trades),
            "economic_selected_baseline_count": len(economic_baseline_trades),
            "selected_count": len(selected_trades),
            "selected_vs_broader_control_retention": (
                round(aggregate_retention, 6)
                if aggregate_retention is not None
                else None
            ),
            "model_skip_count": len(skipped),
            "skipped_positive_return_count": sum(
                float(row["post_oos_outcome_attribution"]["planned_budget_return_pct"])
                > 0.0
                for row in skipped
            ),
            "skipped_catastrophic_count": sum(
                bool(row["post_oos_outcome_attribution"]["catastrophic"])
                for row in skipped
            ),
            "bounded_exploration_enter_count": sum(
                row["action"] == "enter_bounded_exploration" for row in all_decisions
            ),
        },
        "prediction_diagnostics": prediction_diagnostics,
        "evaluations": evaluations,
        "decision": decision,
    }


def _parent_bucket_source_value(
    trade: dict[str, Any],
    source: str,
) -> str | float:
    if source == "pairability_lane":
        return str(trade[source])
    if source == "causal_volatility_scale_pct":
        return float(trade["volatility_scale_pct"])
    try:
        feature_index = ECONOMIC_FEATURE_NAMES.index(source)
    except ValueError as exc:
        raise ValueError(f"unknown parent-bucket source: {source}") from exc
    features = list(trade["economic_features"])
    if feature_index >= len(features):
        raise ValueError(f"parent-bucket source is missing: {source}")
    value = float(features[feature_index])
    if not math.isfinite(value):
        raise ValueError(f"parent-bucket source is non-finite: {source}")
    return value


def _parent_bucket_label(
    value: str | float,
    policy: dict[str, Any],
) -> str:
    if policy["kind"] == "categorical":
        label = str(value)
        return label if label in policy["known_categories"] else "unseen"
    lower, upper = (float(boundary) for boundary in policy["boundaries"])
    numeric = float(value)
    if numeric <= lower:
        return "low"
    if numeric <= upper:
        return "middle"
    return "high"


def _fit_parent_bucket_axis(
    prior_trades: Sequence[dict[str, Any]],
    axis_name: str,
) -> dict[str, Any] | None:
    if not prior_trades:
        return None
    spec = PARENT_BUCKET_AXIS_SPECS[axis_name]
    values = [_parent_bucket_source_value(row, spec["source"]) for row in prior_trades]
    if spec["kind"] == "categorical":
        boundaries: list[float] = []
        known_categories = sorted({str(value) for value in values})
    else:
        numeric_values = np.asarray([float(value) for value in values], dtype=float)
        quantiles = np.quantile(numeric_values, [1.0 / 3.0, 2.0 / 3.0])
        boundaries = [round(float(value), 8) for value in quantiles]
        known_categories = []
    fit_max_date = max(
        date.fromisoformat(str(row["trade_date"])) for row in prior_trades
    )
    policy: dict[str, Any] = {
        "axis": axis_name,
        "kind": spec["kind"],
        "source": spec["source"],
        "fit_max_date": fit_max_date.isoformat(),
        "prior_trade_count": len(prior_trades),
        "prior_evaluation_date_count": len(
            {str(row["trade_date"]) for row in prior_trades}
        ),
        "boundaries": boundaries,
        "known_categories": known_categories,
    }
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for trade, value in zip(prior_trades, values, strict=True):
        grouped[_parent_bucket_label(value, policy)].append(trade)
    global_ev = statistics.fmean(float(row["net_profit_pct"]) for row in prior_trades)
    bucket_statistics: dict[str, dict[str, Any]] = {}
    for label, rows in sorted(grouped.items()):
        bucket_ev = statistics.fmean(float(row["net_profit_pct"]) for row in rows)
        reliability = len(rows) / (len(rows) + PARENT_BUCKET_SHRINKAGE_PRIOR)
        shrunk_ev = reliability * bucket_ev + (1.0 - reliability) * global_ev
        bucket_statistics[label] = {
            "sample_count": len(rows),
            "equal_weight_avg_profit_pct": round(bucket_ev, 6),
            "shrunk_prior_ev_pct": round(shrunk_ev, 6),
            "diagnostic_win_rate_pct": round(
                sum(float(row["net_profit_pct"]) > 0.0 for row in rows)
                / len(rows)
                * 100.0,
                3,
            ),
            "catastrophic_stop_count": sum(
                str(row["exit_reason"]).startswith("catastrophic") for row in rows
            ),
        }
    policy.update(
        {
            "prior_global_ev_pct": round(global_ev, 6),
            "shrinkage_prior": PARENT_BUCKET_SHRINKAGE_PRIOR,
            "bucket_statistics": bucket_statistics,
        }
    )
    return policy


def _score_parent_bucket_axis(
    trades: Sequence[dict[str, Any]],
    policy: dict[str, Any],
) -> list[dict[str, Any]]:
    scored: list[dict[str, Any]] = []
    for trade in trades:
        value = _parent_bucket_source_value(trade, str(policy["source"]))
        label = _parent_bucket_label(value, policy)
        bucket = policy["bucket_statistics"].get(label)
        predicted_ev = (
            float(bucket["shrunk_prior_ev_pct"])
            if bucket is not None
            else float(policy["prior_global_ev_pct"])
        )
        scored.append(
            {
                **trade,
                "parent_bucket_axis": str(policy["axis"]),
                "parent_bucket_label": label,
                "parent_bucket_source_value": value,
                "parent_bucket_prior_sample_count": (
                    int(bucket["sample_count"]) if bucket is not None else 0
                ),
                "predicted_parent_bucket_ev_pct": predicted_ev,
                "parent_bucket_fit_max_date": str(policy["fit_max_date"]),
            }
        )
    return scored


def _apply_parent_bucket_state_machine(
    scored: Sequence[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    control = _non_overlapping_candidates(scored, selected_only=False)
    selected: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in scored:
        grouped[(str(row["venue"]), str(row["session"]))].append(row)
    for session_rows in grouped.values():
        next_available: datetime | None = None
        entries_since_skip = 0
        for trade in sorted(session_rows, key=lambda row: str(row["entry_at"])):
            entry_at = datetime.fromisoformat(str(trade["entry_at"]))
            predicted_ev = float(trade["predicted_parent_bucket_ev_pct"])
            if next_available is not None and entry_at < next_available:
                action = "position_occupied"
            elif predicted_ev < 0.0 and entries_since_skip >= 3:
                action = "skip_negative_parent_ev"
                entries_since_skip = 0
            else:
                action = (
                    "enter_positive_parent_ev"
                    if predicted_ev >= 0.0
                    else "enter_bounded_exploration"
                )
                selected.append(trade)
                entries_since_skip += 1
                next_available = datetime.fromisoformat(str(trade["exit_at"]))
            decisions.append(
                {
                    "trade_date": str(trade["trade_date"]),
                    "venue": str(trade["venue"]),
                    "session": str(trade["session"]),
                    "entry_at": str(trade["entry_at"]),
                    "entry_price": float(trade["entry_price"]),
                    "axis": str(trade["parent_bucket_axis"]),
                    "bucket": str(trade["parent_bucket_label"]),
                    "bucket_source_value": trade["parent_bucket_source_value"],
                    "prior_bucket_sample_count": int(
                        trade["parent_bucket_prior_sample_count"]
                    ),
                    "model_fit_max_date": str(trade["parent_bucket_fit_max_date"]),
                    "predicted_parent_bucket_ev_pct": predicted_ev,
                    "action": action,
                    "post_oos_outcome_attribution": {
                        "exit_reason": str(trade["exit_reason"]),
                        "planned_budget_return_pct": float(trade["net_profit_pct"]),
                        "catastrophic": bool(
                            str(trade["exit_reason"]).startswith("catastrophic")
                        ),
                    },
                }
            )
    retention = len(selected) / len(control) if control else None
    if retention is not None and retention < PARENT_BUCKET_OPPORTUNITY_RETENTION:
        raise ValueError("parent-bucket opportunity retention breached")
    return (
        selected,
        decisions,
        {
            "broader_control_count": len(control),
            "selected_count": len(selected),
            "selected_vs_broader_control_retention": (
                round(retention, 6) if retention is not None else None
            ),
            "model_skip_count": sum(
                row["action"] == "skip_negative_parent_ev" for row in decisions
            ),
            "position_occupied_count": sum(
                row["action"] == "position_occupied" for row in decisions
            ),
            "bounded_exploration_enter_count": sum(
                row["action"] == "enter_bounded_exploration" for row in decisions
            ),
            "positive_parent_ev_enter_count": sum(
                row["action"] == "enter_positive_parent_ev" for row in decisions
            ),
        },
    )


def _select_prior_parent_axis(
    axis_history: dict[str, list[dict[str, Any]]],
) -> dict[str, Any] | None:
    ready = {axis: rows for axis, rows in axis_history.items() if rows}
    if not ready:
        return None

    def rank(item: tuple[str, list[dict[str, Any]]]) -> tuple[float, float, float, int]:
        axis, rows = item
        path = _fixed_tp_split_path_diagnostics(rows)
        return (
            statistics.fmean(float(row["net_profit_pct"]) for row in rows),
            float(path["compounded_planned_budget_return_pct"]),
            float(path["avg_planned_budget_mae_pct"]),
            -list(PARENT_BUCKET_AXIS_SPECS).index(axis),
        )

    selected_axis, selected_rows = max(ready.items(), key=rank)
    selected_path = _fixed_tp_split_path_diagnostics(selected_rows)
    return {
        "selected_axis": selected_axis,
        "fit_max_date": max(str(row["trade_date"]) for row in selected_rows),
        "prior_trade_count": len(selected_rows),
        "prior_evaluation_date_count": len(
            {str(row["trade_date"]) for row in selected_rows}
        ),
        "prior_planned_budget_ev_pct": round(
            rank((selected_axis, selected_rows))[0], 6
        ),
        "prior_compounded_planned_budget_return_pct": selected_path[
            "compounded_planned_budget_return_pct"
        ],
        "prior_avg_planned_budget_mae_pct": selected_path["avg_planned_budget_mae_pct"],
        "selection_policy": (
            "max_prior_axis_ev_then_compounded_return_then_less_adverse_mae"
        ),
    }


def _catastrophic_rate(path: dict[str, Any]) -> float | None:
    sample_count = int(path["sample_count"])
    if sample_count <= 0:
        return None
    return round(int(path["catastrophic_stop_count"]) / sample_count * 100.0, 6)


def _parent_bucket_walk_forward(
    candidate_evaluations: Sequence[dict[str, Any]],
    fixed_split_evaluations: Sequence[dict[str, Any]],
    series_by_key: dict[tuple[date, str, str], Sequence[base.Bar]],
    *,
    venue: str,
    cost_pct: float,
    sample_floor_passed: bool,
    source_quality_passed: bool,
) -> dict[str, Any]:
    economic_baseline_by_date = {
        str(row["evaluation_date"]): list(
            (row.get("arm_trades") or {}).get(PARENT_BUCKET_EXECUTION_ARM, [])
        )
        for row in fixed_split_evaluations
    }
    candidate_history: list[dict[str, Any]] = []
    axis_history: dict[str, list[dict[str, Any]]] = {
        axis: [] for axis in PARENT_BUCKET_AXIS_SPECS
    }
    axis_all_trades: dict[str, list[dict[str, Any]]] = {
        axis: [] for axis in PARENT_BUCKET_AXIS_SPECS
    }
    policy_control_trades: list[dict[str, Any]] = []
    policy_economic_trades: list[dict[str, Any]] = []
    policy_selected_trades: list[dict[str, Any]] = []
    policy_decisions: list[dict[str, Any]] = []
    selected_axis_counts: Counter[str] = Counter()
    evaluations: list[dict[str, Any]] = []
    for candidate_evaluation in candidate_evaluations:
        evaluation_date = date.fromisoformat(
            str(candidate_evaluation["evaluation_date"])
        )
        candidates = list(candidate_evaluation.get("candidate_trades") or [])
        if not candidates:
            evaluations.append(
                {
                    "evaluation_date": evaluation_date.isoformat(),
                    "status": "no_broader_candidate_universe",
                    "raw_candidate_count": 0,
                    "prior_selected_axis": None,
                    "selected_axis_decisions": [],
                }
            )
            continue
        current = _simulate_recoverable_basin_candidates(
            candidates,
            series_by_key,
            venue=venue,
            cost_pct=cost_pct,
        )
        if not candidate_history:
            evaluations.append(
                {
                    "evaluation_date": evaluation_date.isoformat(),
                    "status": "insufficient_prior_parent_history",
                    "raw_candidate_count": len(current),
                    "prior_selected_axis": None,
                    "selected_axis_decisions": [],
                }
            )
            candidate_history.extend(current)
            continue
        axis_outputs: dict[str, dict[str, Any]] = {}
        for axis in PARENT_BUCKET_AXIS_SPECS:
            parent_policy = _fit_parent_bucket_axis(candidate_history, axis)
            if parent_policy is None:
                raise ValueError("parent-bucket prior policy is unexpectedly missing")
            if (
                date.fromisoformat(str(parent_policy["fit_max_date"]))
                >= evaluation_date
            ):
                raise ValueError("parent-bucket policy uses current outcomes")
            scored = _score_parent_bucket_axis(current, parent_policy)
            selected, decisions, capacity = _apply_parent_bucket_state_machine(scored)
            axis_outputs[axis] = {
                "policy": parent_policy,
                "selected": selected,
                "decisions": decisions,
                "capacity": capacity,
            }
            axis_all_trades[axis].extend(selected)
        prior_axis = _select_prior_parent_axis(axis_history)
        broader_control = _non_overlapping_candidates(current, selected_only=False)
        if prior_axis is None:
            status = "insufficient_prior_axis_history"
            selected_axis_decisions: list[dict[str, Any]] = []
        else:
            if date.fromisoformat(str(prior_axis["fit_max_date"])) >= evaluation_date:
                raise ValueError("parent-axis choice uses current outcomes")
            selected_axis = str(prior_axis["selected_axis"])
            selected_output = axis_outputs[selected_axis]
            selected_axis_decisions = list(selected_output["decisions"])
            selected_current = list(selected_output["selected"])
            current_economic = economic_baseline_by_date.get(
                evaluation_date.isoformat(), []
            )
            policy_control_trades.extend(broader_control)
            policy_economic_trades.extend(current_economic)
            policy_selected_trades.extend(selected_current)
            policy_decisions.extend(selected_axis_decisions)
            selected_axis_counts[selected_axis] += 1
            status = "evaluated_prior_only_parent_axis"
        evaluations.append(
            {
                "evaluation_date": evaluation_date.isoformat(),
                "status": status,
                "raw_candidate_count": len(current),
                "prior_selected_axis": prior_axis,
                "axis_models": {
                    axis: {
                        "axis": output["policy"]["axis"],
                        "kind": output["policy"]["kind"],
                        "source": output["policy"]["source"],
                        "fit_max_date": output["policy"]["fit_max_date"],
                        "prior_trade_count": output["policy"]["prior_trade_count"],
                        "prior_evaluation_date_count": output["policy"][
                            "prior_evaluation_date_count"
                        ],
                        "boundaries": output["policy"]["boundaries"],
                        "known_categories": output["policy"]["known_categories"],
                        "prior_global_ev_pct": output["policy"]["prior_global_ev_pct"],
                        "bucket_statistics": output["policy"]["bucket_statistics"],
                        "capacity": output["capacity"],
                        "selected_summary": _summary(
                            output["selected"],
                            source_quality_passed=source_quality_passed,
                        ),
                        "selected_path": _fixed_tp_split_path_diagnostics(
                            output["selected"]
                        ),
                    }
                    for axis, output in axis_outputs.items()
                },
                "selected_axis_decisions": selected_axis_decisions,
                "trade_detail_storage": "omitted_replayable_from_source_bars",
            }
        )
        for axis, output in axis_outputs.items():
            axis_history[axis].extend(output["selected"])
        candidate_history.extend(current)

    control_summary = _summary(
        policy_control_trades, source_quality_passed=source_quality_passed
    )
    economic_summary = _summary(
        policy_economic_trades, source_quality_passed=source_quality_passed
    )
    selected_summary = _summary(
        policy_selected_trades, source_quality_passed=source_quality_passed
    )
    control_path = _fixed_tp_split_path_diagnostics(policy_control_trades)
    economic_path = _fixed_tp_split_path_diagnostics(policy_economic_trades)
    selected_path = _fixed_tp_split_path_diagnostics(policy_selected_trades)
    axis_summaries = {
        axis: {
            "summary": _summary(rows, source_quality_passed=source_quality_passed),
            "path": _fixed_tp_split_path_diagnostics(rows),
            "decision_authority": "diagnostic_only_not_same_date_axis_selection",
        }
        for axis, rows in axis_all_trades.items()
    }
    conflict_evaluation_count = sum(
        any(
            any(
                float(bucket["shrunk_prior_ev_pct"]) > 0.0
                for bucket in model["bucket_statistics"].values()
            )
            and any(
                float(bucket["shrunk_prior_ev_pct"]) < 0.0
                for bucket in model["bucket_statistics"].values()
            )
            for model in evaluation.get("axis_models", {}).values()
        )
        for evaluation in evaluations
    )
    aggregate_retention = (
        len(policy_selected_trades) / len(policy_control_trades)
        if policy_control_trades
        else None
    )
    if not source_quality_passed:
        decision = "source_quality_blocked"
    elif not sample_floor_passed:
        decision = "insufficient_coverage_dates"
    elif not policy_selected_trades or not policy_control_trades:
        decision = "insufficient_parent_history"
    else:
        selected_ev = float(selected_summary["source_quality_adjusted_ev_pct"])
        control_ev = float(control_summary["source_quality_adjusted_ev_pct"])
        economic_ev = float(economic_summary["source_quality_adjusted_ev_pct"])
        selected_compounded = float(
            selected_path["compounded_planned_budget_return_pct"]
        )
        control_compounded = float(control_path["compounded_planned_budget_return_pct"])
        economic_compounded = float(
            economic_path["compounded_planned_budget_return_pct"]
        )
        selected_mae = float(selected_path["avg_planned_budget_mae_pct"])
        control_mae = float(control_path["avg_planned_budget_mae_pct"])
        economic_mae = float(economic_path["avg_planned_budget_mae_pct"])
        selected_catastrophic_rate = float(_catastrophic_rate(selected_path) or 0.0)
        control_catastrophic_rate = float(_catastrophic_rate(control_path) or 0.0)
        economic_catastrophic_rate = float(_catastrophic_rate(economic_path) or 0.0)
        if (
            aggregate_retention is not None
            and aggregate_retention >= PARENT_BUCKET_OPPORTUNITY_RETENTION
            and selected_ev > 0.0
            and selected_compounded > 0.0
        ):
            decision = "parent_bucket_oos_positive"
        elif (
            aggregate_retention is not None
            and aggregate_retention >= PARENT_BUCKET_OPPORTUNITY_RETENTION
            and selected_ev >= control_ev
            and selected_ev >= economic_ev
            and selected_compounded >= control_compounded
            and selected_compounded >= economic_compounded
            and selected_mae >= control_mae
            and selected_mae >= economic_mae
            and selected_catastrophic_rate <= control_catastrophic_rate
            and selected_catastrophic_rate <= economic_catastrophic_rate
            and (selected_ev > control_ev or selected_ev > economic_ev)
        ):
            decision = "parent_bucket_pareto_improved"
        elif conflict_evaluation_count > 0:
            decision = "parent_bucket_conflict_only"
        else:
            decision = "parent_bucket_no_incremental_value"
    skipped = [
        row for row in policy_decisions if row["action"] == "skip_negative_parent_ev"
    ]
    entered_decisions = [
        row for row in policy_decisions if str(row["action"]).startswith("enter_")
    ]
    selected_axis_bucket_attribution: dict[str, dict[str, Any]] = {}
    grouped_decisions: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in entered_decisions:
        grouped_decisions[(str(row["axis"]), str(row["bucket"]))].append(row)
    for (axis, bucket), rows in sorted(grouped_decisions.items()):
        returns = [
            float(row["post_oos_outcome_attribution"]["planned_budget_return_pct"])
            for row in rows
        ]
        selected_axis_bucket_attribution[f"{axis}:{bucket}"] = {
            "axis": axis,
            "bucket": bucket,
            "sample_count": len(rows),
            "equal_weight_avg_profit_pct": round(statistics.fmean(returns), 6),
            "diagnostic_win_rate_pct": round(
                sum(value > 0.0 for value in returns) / len(returns) * 100.0,
                3,
            ),
            "catastrophic_stop_count": sum(
                bool(row["post_oos_outcome_attribution"]["catastrophic"])
                for row in rows
            ),
        }
    return {
        "contract": PARENT_BUCKET_CONTRACT,
        "fixed_execution_arm": PARENT_BUCKET_EXECUTION_ARM,
        "axis_specs": PARENT_BUCKET_AXIS_SPECS,
        "evaluation_count": sum(
            row["status"] == "evaluated_prior_only_parent_axis" for row in evaluations
        ),
        "broader_control_summary_same_dates": control_summary,
        "economic_selected_baseline_summary_same_dates": economic_summary,
        "selected_summary": selected_summary,
        "path_diagnostics": {
            "broader_control": {
                **control_path,
                "catastrophic_stop_rate_pct": _catastrophic_rate(control_path),
            },
            "economic_selected_baseline": {
                **economic_path,
                "catastrophic_stop_rate_pct": _catastrophic_rate(economic_path),
            },
            "prior_selected_parent_axis": {
                **selected_path,
                "catastrophic_stop_rate_pct": _catastrophic_rate(selected_path),
            },
        },
        "axis_summaries": axis_summaries,
        "capacity_diagnostics": {
            "required_opportunity_retention": PARENT_BUCKET_OPPORTUNITY_RETENTION,
            "raw_candidate_count": len(candidate_history),
            "broader_control_count": len(policy_control_trades),
            "economic_selected_baseline_count": len(policy_economic_trades),
            "selected_count": len(policy_selected_trades),
            "selected_vs_broader_control_retention": (
                round(aggregate_retention, 6)
                if aggregate_retention is not None
                else None
            ),
            "selected_axis_evaluation_counts": dict(
                sorted(selected_axis_counts.items())
            ),
            "model_skip_count": len(skipped),
            "skipped_positive_return_count": sum(
                float(row["post_oos_outcome_attribution"]["planned_budget_return_pct"])
                > 0.0
                for row in skipped
            ),
            "skipped_catastrophic_count": sum(
                bool(row["post_oos_outcome_attribution"]["catastrophic"])
                for row in skipped
            ),
            "bounded_exploration_enter_count": sum(
                row["action"] == "enter_bounded_exploration" for row in policy_decisions
            ),
        },
        "conflict_diagnostics": {
            "metric_role": "post_oos_parent_direction_conflict_diagnostic",
            "decision_authority": "diagnostic_only_not_same_date_axis_selection",
            "evaluation_with_mixed_parent_sign_count": conflict_evaluation_count,
            "selected_axis_bucket_attribution": selected_axis_bucket_attribution,
            "forbidden_uses": [
                "same_date_bucket_or_axis_selection",
                "runtime_or_order_authority",
            ],
        },
        "evaluations": evaluations,
        "decision": decision,
    }


def _parent_bucket_stability_summary(
    decisions: Sequence[dict[str, Any]],
    *,
    source_quality_passed: bool,
) -> dict[str, Any]:
    by_date: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in decisions:
        by_date[str(row["trade_date"])].append(row)
    ordered_dates = sorted(by_date)
    returns = [
        float(row["post_oos_outcome_attribution"]["planned_budget_return_pct"])
        for row in decisions
    ]
    date_level: list[dict[str, Any]] = []
    for trade_date in ordered_dates:
        date_returns = [
            float(row["post_oos_outcome_attribution"]["planned_budget_return_pct"])
            for row in by_date[trade_date]
        ]
        date_level.append(
            {
                "trade_date": trade_date,
                "sample_count": len(date_returns),
                "equal_weight_avg_profit_pct": round(statistics.fmean(date_returns), 6),
                "simple_sum_profit_pct": round(sum(date_returns), 6),
                "diagnostic_win_rate_pct": round(
                    sum(value > 0.0 for value in date_returns)
                    / len(date_returns)
                    * 100.0,
                    3,
                ),
                "catastrophic_stop_count": sum(
                    bool(row["post_oos_outcome_attribution"]["catastrophic"])
                    for row in by_date[trade_date]
                ),
            }
        )
    rolling_windows: list[dict[str, Any]] = []
    for end_index in range(
        PARENT_BUCKET_STABILITY_ROLLING_DATES - 1, len(ordered_dates)
    ):
        window_dates = ordered_dates[
            end_index - PARENT_BUCKET_STABILITY_ROLLING_DATES + 1 : end_index + 1
        ]
        window_returns = [
            float(row["post_oos_outcome_attribution"]["planned_budget_return_pct"])
            for trade_date in window_dates
            for row in by_date[trade_date]
        ]
        rolling_windows.append(
            {
                "start_date": window_dates[0],
                "end_date": window_dates[-1],
                "observed_date_count": len(window_dates),
                "sample_count": len(window_returns),
                "equal_weight_avg_profit_pct": round(
                    statistics.fmean(window_returns), 6
                ),
            }
        )
    leave_one_date: list[dict[str, Any]] = []
    if len(ordered_dates) >= 2:
        for omitted_date in ordered_dates:
            retained = [
                float(row["post_oos_outcome_attribution"]["planned_budget_return_pct"])
                for trade_date in ordered_dates
                if trade_date != omitted_date
                for row in by_date[trade_date]
            ]
            leave_one_date.append(
                {
                    "omitted_date": omitted_date,
                    "sample_count": len(retained),
                    "equal_weight_avg_profit_pct": round(statistics.fmean(retained), 6),
                }
            )
    total_negative_magnitude = sum(-value for value in returns if value < 0.0)
    catastrophic_negative_magnitude = sum(
        -min(
            float(row["post_oos_outcome_attribution"]["planned_budget_return_pct"]),
            0.0,
        )
        for row in decisions
        if bool(row["post_oos_outcome_attribution"]["catastrophic"])
    )
    date_negative_magnitudes = {
        trade_date: sum(
            -float(row["post_oos_outcome_attribution"]["planned_budget_return_pct"])
            for row in by_date[trade_date]
            if float(row["post_oos_outcome_attribution"]["planned_budget_return_pct"])
            < 0.0
        )
        for trade_date in ordered_dates
    }
    date_positive_contributions = {
        trade_date: sum(
            float(row["post_oos_outcome_attribution"]["planned_budget_return_pct"])
            for row in by_date[trade_date]
            if float(row["post_oos_outcome_attribution"]["planned_budget_return_pct"])
            > 0.0
        )
        for trade_date in ordered_dates
    }
    total_positive_contribution = sum(date_positive_contributions.values())
    midpoint = len(ordered_dates) // 2

    def period_ev(period_dates: Sequence[str]) -> float | None:
        period_returns = [
            float(row["post_oos_outcome_attribution"]["planned_budget_return_pct"])
            for trade_date in period_dates
            for row in by_date[trade_date]
        ]
        return round(statistics.fmean(period_returns), 6) if period_returns else None

    overall_ev = round(statistics.fmean(returns), 6) if returns else None
    return {
        "sample_count": len(decisions),
        "observed_date_count": len(ordered_dates),
        "equal_weight_avg_profit_pct": overall_ev,
        "source_quality_adjusted_ev_pct": (
            overall_ev if source_quality_passed else None
        ),
        "diagnostic_win_rate_pct": (
            round(sum(value > 0.0 for value in returns) / len(returns) * 100.0, 3)
            if returns
            else None
        ),
        "positive_date_count": sum(
            float(row["equal_weight_avg_profit_pct"]) > 0.0 for row in date_level
        ),
        "positive_date_ratio": (
            round(
                sum(
                    float(row["equal_weight_avg_profit_pct"]) > 0.0
                    for row in date_level
                )
                / len(date_level),
                6,
            )
            if date_level
            else None
        ),
        "first_half_ev_pct": period_ev(ordered_dates[:midpoint]),
        "second_half_ev_pct": period_ev(ordered_dates[midpoint:]),
        "rolling_window_observed_dates": PARENT_BUCKET_STABILITY_ROLLING_DATES,
        "rolling_positive_window_count": sum(
            float(row["equal_weight_avg_profit_pct"]) > 0.0 for row in rolling_windows
        ),
        "rolling_positive_window_ratio": (
            round(
                sum(
                    float(row["equal_weight_avg_profit_pct"]) > 0.0
                    for row in rolling_windows
                )
                / len(rolling_windows),
                6,
            )
            if rolling_windows
            else None
        ),
        "leave_one_date_min_ev_pct": (
            min(float(row["equal_weight_avg_profit_pct"]) for row in leave_one_date)
            if leave_one_date
            else None
        ),
        "leave_one_date_max_ev_pct": (
            max(float(row["equal_weight_avg_profit_pct"]) for row in leave_one_date)
            if leave_one_date
            else None
        ),
        "leave_one_date_all_positive": bool(
            leave_one_date
            and all(
                float(row["equal_weight_avg_profit_pct"]) > 0.0
                for row in leave_one_date
            )
        ),
        "catastrophic_stop_count": sum(
            bool(row["post_oos_outcome_attribution"]["catastrophic"])
            for row in decisions
        ),
        "catastrophic_negative_magnitude_share": (
            round(catastrophic_negative_magnitude / total_negative_magnitude, 6)
            if total_negative_magnitude > 0.0
            else None
        ),
        "worst_date_negative_magnitude_share": (
            round(max(date_negative_magnitudes.values()) / total_negative_magnitude, 6)
            if total_negative_magnitude > 0.0 and date_negative_magnitudes
            else None
        ),
        "best_date_positive_contribution_share": (
            round(
                max(date_positive_contributions.values()) / total_positive_contribution,
                6,
            )
            if total_positive_contribution > 0.0 and date_positive_contributions
            else None
        ),
        "date_level": date_level,
        "rolling_windows": rolling_windows,
        "leave_one_date": leave_one_date,
    }


def _parent_bucket_conflict_stability(
    parent_result: dict[str, Any],
    *,
    source_quality_passed: bool,
) -> dict[str, Any]:
    entered: list[dict[str, Any]] = []
    for evaluation in parent_result.get("evaluations") or []:
        if evaluation.get("status") != "evaluated_prior_only_parent_axis":
            continue
        entered.extend(
            row
            for row in evaluation.get("selected_axis_decisions") or []
            if str(row.get("action", "")).startswith("enter_")
        )
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in entered:
        grouped[(str(row["axis"]), str(row["bucket"]))].append(row)
    bucket_summaries = {
        f"{axis}:{bucket}": {
            "axis": axis,
            "bucket": bucket,
            **_parent_bucket_stability_summary(
                rows,
                source_quality_passed=source_quality_passed,
            ),
        }
        for (axis, bucket), rows in sorted(grouped.items())
    }
    focus_key = (
        f"{PARENT_BUCKET_STABILITY_FOCUS_AXIS}:"
        f"{PARENT_BUCKET_STABILITY_FOCUS_BUCKET}"
    )
    focus = bucket_summaries.get(focus_key)
    if not source_quality_passed:
        decision = "source_quality_blocked"
    elif focus is None or not focus["sample_count"]:
        decision = "no_stable_parent_edge"
    else:
        focus_ev = float(focus["source_quality_adjusted_ev_pct"])
        positive_date_ratio = float(focus["positive_date_ratio"] or 0.0)
        rolling_positive_ratio = float(focus["rolling_positive_window_ratio"] or 0.0)
        second_half_ev = float(focus["second_half_ev_pct"] or 0.0)
        if (
            focus_ev > 0.0
            and bool(focus["leave_one_date_all_positive"])
            and positive_date_ratio >= 0.6
            and rolling_positive_ratio >= 0.6
            and second_half_ev > 0.0
        ):
            decision = "stable_parent_edge_needs_next_date_confirmation"
        elif focus_ev > 0.0:
            decision = "parent_edge_concentrated_not_reproducible"
        elif (
            float(focus["catastrophic_negative_magnitude_share"] or 0.0) >= 0.6
            or float(focus["worst_date_negative_magnitude_share"] or 0.0) >= 0.5
        ):
            decision = "catastrophic_loss_cluster_identified"
        else:
            decision = "no_stable_parent_edge"
    return {
        "contract": PARENT_BUCKET_STABILITY_CONTRACT,
        "focus_axis": PARENT_BUCKET_STABILITY_FOCUS_AXIS,
        "focus_bucket": PARENT_BUCKET_STABILITY_FOCUS_BUCKET,
        "focus_key": focus_key,
        "focus_summary": focus,
        "bucket_summaries": bucket_summaries,
        "input_parent_decision": parent_result.get("decision"),
        "input_evaluation_count": parent_result.get("evaluation_count"),
        "input_decisions_unchanged": True,
        "decision": decision,
    }


def _pre_entry_sequence_features(
    series: Sequence[base.Bar],
    *,
    entry_at: str,
) -> tuple[dict[str, float], dict[str, Any]]:
    normalized = [(_timestamp_without_timezone(bar.timestamp), bar) for bar in series]
    by_timestamp = {timestamp: bar for timestamp, bar in normalized}
    parsed_entry_at = _timestamp_without_timezone(entry_at)
    entry_indexes = [
        index
        for index, (timestamp, _) in enumerate(normalized)
        if timestamp == parsed_entry_at
    ]
    if len(entry_indexes) != 1 or entry_indexes[0] <= 0:
        return {}, {
            "entry_bar_exact_match": False,
            "completed_pre_entry_sequence": False,
            "missing_horizons_minutes": [1, 3, 5, 10],
        }
    decision_index = entry_indexes[0] - 1
    decision_at, decision_bar = normalized[decision_index]
    horizon_returns: dict[int, float] = {}
    missing_horizons: list[int] = []
    for minutes in (1, 3, 5, 10):
        prior = by_timestamp.get(decision_at - timedelta(minutes=minutes))
        if prior is None or float(prior.close) <= 0.0:
            missing_horizons.append(minutes)
            continue
        horizon_returns[minutes] = (
            float(decision_bar.close) / float(prior.close) - 1.0
        ) * 100.0
    trailing_bars = [
        by_timestamp.get(decision_at - timedelta(minutes=offset))
        for offset in range(5, -1, -1)
    ]
    sequence_complete = all(bar is not None for bar in trailing_bars)
    negative_step_count = 0
    down_volume = 0.0
    total_step_volume = 0.0
    if sequence_complete:
        complete_bars = [bar for bar in trailing_bars if bar is not None]
        for previous, current in zip(complete_bars, complete_bars[1:]):
            volume = max(0.0, float(current.volume))
            total_step_volume += volume
            if float(current.close) < float(previous.close):
                negative_step_count += 1
                down_volume += volume
    features = {
        f"pre_entry_return_{minutes}m_pct": round(value, 8)
        for minutes, value in horizon_returns.items()
    }
    if sequence_complete:
        features.update(
            {
                "pre_entry_negative_step_count_5": float(negative_step_count),
                "pre_entry_down_volume_share_5": round(
                    down_volume / total_step_volume if total_step_volume > 0.0 else 0.0,
                    8,
                ),
            }
        )
    return features, {
        "entry_bar_exact_match": True,
        "decision_at": decision_at.isoformat(),
        "completed_pre_entry_sequence": sequence_complete,
        "missing_horizons_minutes": missing_horizons,
    }


def _catastrophic_numeric_feature_summary(
    catastrophic_values: Sequence[float],
    target_values: Sequence[float],
) -> dict[str, Any]:
    catastrophic = [float(value) for value in catastrophic_values]
    target = [float(value) for value in target_values]
    if not catastrophic or not target:
        return {
            "catastrophic_count": len(catastrophic),
            "target_recovery_count": len(target),
            "comparison_available": False,
            "distribution_shift_candidate": False,
            "signature_candidate": False,
        }
    target_median = statistics.median(target)
    pair_count = len(catastrophic) * len(target)
    higher_pair_score = (
        sum(
            (
                1.0
                if catastrophic_value > target_value
                else 0.5 if catastrophic_value == target_value else 0.0
            )
            for catastrophic_value in catastrophic
            for target_value in target
        )
        / pair_count
    )
    if higher_pair_score >= 0.5:
        direction = "catastrophic_higher"
        direction_probability = higher_pair_score
        same_side_count = sum(value > target_median for value in catastrophic)
        target_same_side_count = sum(value > target_median for value in target)
    else:
        direction = "catastrophic_lower"
        direction_probability = 1.0 - higher_pair_score
        same_side_count = sum(value < target_median for value in catastrophic)
        target_same_side_count = sum(value < target_median for value in target)
    leave_one_probabilities: list[float] = []
    if len(catastrophic) >= 2:
        for omitted_index in range(len(catastrophic)):
            retained = [
                value
                for index, value in enumerate(catastrophic)
                if index != omitted_index
            ]
            retained_higher_score = sum(
                (
                    1.0
                    if catastrophic_value > target_value
                    else 0.5 if catastrophic_value == target_value else 0.0
                )
                for catastrophic_value in retained
                for target_value in target
            ) / (len(retained) * len(target))
            leave_one_probabilities.append(
                retained_higher_score
                if direction == "catastrophic_higher"
                else 1.0 - retained_higher_score
            )
    leave_one_min = min(leave_one_probabilities) if leave_one_probabilities else None
    target_recovery_retention = 1.0 - target_same_side_count / len(target)
    distribution_shift_candidate = bool(
        len(target) >= PARENT_CATASTROPHIC_AUDIT_MIN_TARGET_COMPARATOR
        and same_side_count == len(catastrophic)
        and direction_probability >= PARENT_CATASTROPHIC_AUDIT_PAIRWISE_FLOOR
        and leave_one_min is not None
        and leave_one_min >= PARENT_CATASTROPHIC_AUDIT_LEAVE_ONE_FLOOR
    )
    signature_candidate = bool(
        distribution_shift_candidate
        and target_recovery_retention
        >= PARENT_CATASTROPHIC_AUDIT_TARGET_RETENTION_FLOOR
    )
    return {
        "catastrophic_count": len(catastrophic),
        "target_recovery_count": len(target),
        "comparison_available": True,
        "catastrophic_mean": round(statistics.fmean(catastrophic), 8),
        "catastrophic_median": round(statistics.median(catastrophic), 8),
        "catastrophic_min": round(min(catastrophic), 8),
        "catastrophic_max": round(max(catastrophic), 8),
        "target_recovery_mean": round(statistics.fmean(target), 8),
        "target_recovery_median": round(target_median, 8),
        "target_recovery_min": round(min(target), 8),
        "target_recovery_max": round(max(target), 8),
        "median_difference_catastrophic_minus_target": round(
            statistics.median(catastrophic) - target_median,
            8,
        ),
        "direction": direction,
        "direction_pair_probability": round(direction_probability, 8),
        "catastrophic_same_side_of_target_median_count": same_side_count,
        "catastrophic_same_side_of_target_median_ratio": round(
            same_side_count / len(catastrophic),
            8,
        ),
        "target_recovery_same_side_of_target_median_count": target_same_side_count,
        "target_recovery_same_side_of_target_median_ratio": round(
            target_same_side_count / len(target),
            8,
        ),
        "target_recovery_retention_if_signature_side_excluded": round(
            target_recovery_retention,
            8,
        ),
        "leave_one_catastrophic_min_direction_probability": (
            round(leave_one_min, 8) if leave_one_min is not None else None
        ),
        "distribution_shift_candidate": distribution_shift_candidate,
        "signature_candidate": signature_candidate,
    }


def _parent_catastrophic_episode_audit(
    parent_result: dict[str, Any],
    candidate_evaluations: Sequence[dict[str, Any]],
    series_by_key: dict[tuple[date, str, str], Sequence[base.Bar]],
    *,
    venue: str,
    source_quality_passed: bool,
) -> dict[str, Any]:
    focus_decisions = [
        row
        for evaluation in parent_result.get("evaluations") or []
        if evaluation.get("status") == "evaluated_prior_only_parent_axis"
        for row in evaluation.get("selected_axis_decisions") or []
        if str(row.get("action", "")).startswith("enter_")
        and str(row.get("venue")) == venue
        and row.get("axis") == PARENT_BUCKET_STABILITY_FOCUS_AXIS
        and row.get("bucket") == PARENT_BUCKET_STABILITY_FOCUS_BUCKET
    ]
    candidate_by_identity: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    duplicate_candidate_identities: list[tuple[str, str, str, str]] = []
    for evaluation in candidate_evaluations:
        for candidate in evaluation.get("candidate_trades") or []:
            if str(candidate.get("venue")) != venue:
                continue
            identity = _entry_identity(candidate)
            if identity in candidate_by_identity:
                duplicate_candidate_identities.append(identity)
                continue
            candidate_by_identity[identity] = candidate

    episodes: list[dict[str, Any]] = []
    source_gaps: list[dict[str, Any]] = []
    for decision in focus_decisions:
        identity = _entry_identity(decision)
        candidate = candidate_by_identity.get(identity)
        if candidate is None:
            source_gaps.append(
                {"identity": list(identity), "reason": "causal_candidate_missing"}
            )
            continue
        economic_features = list(candidate.get("economic_features") or [])
        if len(economic_features) != len(ECONOMIC_FEATURE_NAMES):
            source_gaps.append(
                {
                    "identity": list(identity),
                    "reason": "economic_feature_contract_mismatch",
                    "expected": len(ECONOMIC_FEATURE_NAMES),
                    "observed": len(economic_features),
                }
            )
            continue
        feature_values = {
            name: round(float(value), 8)
            for name, value in zip(
                ECONOMIC_FEATURE_NAMES,
                economic_features,
                strict=True,
            )
            if name in PARENT_CATASTROPHIC_AUDIT_FEATURE_NAMES
        }
        key = (
            date.fromisoformat(str(decision["trade_date"])),
            str(decision["venue"]),
            str(decision["session"]),
        )
        series = series_by_key.get(key)
        if not series:
            source_gaps.append(
                {"identity": list(identity), "reason": "market_series_missing"}
            )
            continue
        sequence_features, sequence_provenance = _pre_entry_sequence_features(
            series,
            entry_at=str(decision["entry_at"]),
        )
        feature_values.update(sequence_features)
        missing_features = [
            name
            for name in PARENT_CATASTROPHIC_AUDIT_FEATURE_NAMES
            if name not in feature_values
            or not math.isfinite(float(feature_values[name]))
        ]
        if missing_features:
            source_gaps.append(
                {
                    "identity": list(identity),
                    "reason": "required_pre_entry_feature_missing",
                    "features": missing_features,
                    "sequence_provenance": sequence_provenance,
                }
            )
            continue
        outcome = decision["post_oos_outcome_attribution"]
        exit_reason = str(outcome["exit_reason"])
        if bool(outcome["catastrophic"]):
            outcome_class = "catastrophic_stop"
        elif exit_reason == "fixed_average_take_profit":
            outcome_class = "target_recovery"
        else:
            outcome_class = "session_close_other"
        market_context_available = bool(
            feature_values.get("confirmation_market_context_available", 0.0)
        )
        if source_quality_passed and not market_context_available:
            source_gaps.append(
                {
                    "identity": list(identity),
                    "reason": "exact_market_context_unavailable",
                }
            )
            continue
        episodes.append(
            {
                "trade_date": str(decision["trade_date"]),
                "venue": str(decision["venue"]),
                "session": str(decision["session"]),
                "entry_at": str(decision["entry_at"]),
                "decision_at": sequence_provenance.get("decision_at"),
                "entry_price": float(decision["entry_price"]),
                "pairability_lane": str(candidate["pairability_lane"]),
                "outcome_class": outcome_class,
                "exit_reason": exit_reason,
                "planned_budget_return_pct": float(
                    outcome["planned_budget_return_pct"]
                ),
                "feature_values": feature_values,
                "provenance": {
                    **sequence_provenance,
                    "causal_candidate_joined": True,
                    "economic_feature_contract_complete": True,
                    "market_context_available": market_context_available,
                    "future_path_used_as_feature": False,
                },
            }
        )

    focus_returns = [
        float(row["post_oos_outcome_attribution"]["planned_budget_return_pct"])
        for row in focus_decisions
    ]
    focus_ev = round(statistics.fmean(focus_returns), 6) if focus_returns else None
    catastrophic = [
        row for row in episodes if row["outcome_class"] == "catastrophic_stop"
    ]
    target_recovery = [
        row for row in episodes if row["outcome_class"] == "target_recovery"
    ]
    session_close = [
        row for row in episodes if row["outcome_class"] == "session_close_other"
    ]
    numeric_feature_summaries = {
        feature_name: _catastrophic_numeric_feature_summary(
            [row["feature_values"][feature_name] for row in catastrophic],
            [row["feature_values"][feature_name] for row in target_recovery],
        )
        for feature_name in PARENT_CATASTROPHIC_AUDIT_COMPARISON_FEATURE_NAMES
    }
    numeric_signature_candidates = [
        feature_name
        for feature_name, summary in numeric_feature_summaries.items()
        if summary["signature_candidate"]
    ]
    numeric_distribution_shift_candidates = [
        feature_name
        for feature_name, summary in numeric_feature_summaries.items()
        if summary["distribution_shift_candidate"]
    ]
    catastrophic_lanes = Counter(row["pairability_lane"] for row in catastrophic)
    target_lanes = Counter(row["pairability_lane"] for row in target_recovery)
    dominant_lane = (
        catastrophic_lanes.most_common(1)[0][0] if catastrophic_lanes else None
    )
    dominant_lane_catastrophic_count = (
        int(catastrophic_lanes[dominant_lane]) if dominant_lane is not None else 0
    )
    dominant_lane_target_ratio = (
        target_lanes[dominant_lane] / len(target_recovery)
        if dominant_lane is not None and target_recovery
        else None
    )
    lane_signature_candidate = bool(
        catastrophic
        and len(target_recovery) >= PARENT_CATASTROPHIC_AUDIT_MIN_TARGET_COMPARATOR
        and dominant_lane_catastrophic_count == len(catastrophic)
        and dominant_lane_target_ratio is not None
        and dominant_lane_target_ratio
        <= 1.0 - PARENT_CATASTROPHIC_AUDIT_TARGET_RETENTION_FLOOR
    )
    if not source_quality_passed:
        decision = "source_quality_blocked"
    elif duplicate_candidate_identities or source_gaps:
        decision = "source_contract_gap"
    elif not catastrophic or (
        len(target_recovery) < PARENT_CATASTROPHIC_AUDIT_MIN_TARGET_COMPARATOR
    ):
        decision = "loss_signature_not_separable"
    elif numeric_signature_candidates or lane_signature_candidate:
        decision = "repeatable_pre_entry_loss_signature_identified"
    else:
        decision = "loss_signature_not_separable"
    return {
        "contract": PARENT_CATASTROPHIC_AUDIT_CONTRACT,
        "focus_axis": PARENT_BUCKET_STABILITY_FOCUS_AXIS,
        "focus_bucket": PARENT_BUCKET_STABILITY_FOCUS_BUCKET,
        "input_parent_decision": parent_result.get("decision"),
        "input_focus_decision_count": len(focus_decisions),
        "input_decisions_unchanged": True,
        "focus_equal_weight_avg_profit_pct": focus_ev,
        "focus_source_quality_adjusted_ev_pct": (
            focus_ev if source_quality_passed else None
        ),
        "source_quality_passed": source_quality_passed,
        "source_gap_count": len(source_gaps),
        "source_gaps": source_gaps,
        "duplicate_candidate_identity_count": len(duplicate_candidate_identities),
        "duplicate_candidate_identities": [
            list(identity) for identity in duplicate_candidate_identities
        ],
        "episode_counts": {
            "total": len(episodes),
            "catastrophic_stop": len(catastrophic),
            "target_recovery": len(target_recovery),
            "session_close_other": len(session_close),
        },
        "market_context_available_counts": dict(
            sorted(
                Counter(
                    str(row["provenance"]["market_context_available"]).lower()
                    for row in episodes
                ).items()
            )
        ),
        "lane_summary": {
            "catastrophic_counts": dict(sorted(catastrophic_lanes.items())),
            "target_recovery_counts": dict(sorted(target_lanes.items())),
            "dominant_catastrophic_lane": dominant_lane,
            "dominant_catastrophic_lane_count": dominant_lane_catastrophic_count,
            "dominant_lane_target_recovery_ratio": (
                round(dominant_lane_target_ratio, 8)
                if dominant_lane_target_ratio is not None
                else None
            ),
            "signature_candidate": lane_signature_candidate,
        },
        "numeric_feature_summaries": numeric_feature_summaries,
        "numeric_distribution_shift_candidates": (
            numeric_distribution_shift_candidates
        ),
        "numeric_signature_candidates": numeric_signature_candidates,
        "episodes": episodes,
        "decision": decision,
    }


def _planned_budget_mark_return_pct(
    fixed_trade: dict[str, Any],
    *,
    mark_price: float,
    cost_pct: float,
) -> float:
    fills = list(fixed_trade.get("filled_legs") or [])
    if not fills:
        raise ValueError("fixed trade has no filled legs")
    planned_budget = float(fixed_trade["entry_price"])
    if planned_budget <= 0.0 or mark_price <= 0.0:
        raise ValueError("planned budget and mark price must be positive")
    total_quantity = sum(float(fill["quantity_units"]) for fill in fills)
    deployed_capital = sum(
        float(fill["quantity_units"]) * float(fill["price"]) for fill in fills
    )
    deployed_fraction = sum(float(fill["allocation"]) for fill in fills)
    gross_planned_pct = (
        (float(mark_price) * total_quantity - deployed_capital) / planned_budget * 100.0
    )
    return round(gross_planned_pct - float(cost_pct) * deployed_fraction, 6)


def _compounded_return_from_values(values: Sequence[float]) -> float:
    compounded = 1.0
    for value in values:
        compounded *= 1.0 + float(value) / 100.0
    return round((compounded - 1.0) * 100.0, 6)


def _parent_catastrophic_stop_recovery_path(
    parent_result: dict[str, Any],
    candidate_evaluations: Sequence[dict[str, Any]],
    series_by_key: dict[tuple[date, str, str], Sequence[base.Bar]],
    *,
    venue: str,
    cost_pct: float,
    source_quality_passed: bool,
) -> dict[str, Any]:
    catastrophic_decisions = [
        row
        for evaluation in parent_result.get("evaluations") or []
        if evaluation.get("status") == "evaluated_prior_only_parent_axis"
        for row in evaluation.get("selected_axis_decisions") or []
        if str(row.get("action", "")).startswith("enter_")
        and str(row.get("venue")) == venue
        and row.get("axis") == PARENT_BUCKET_STABILITY_FOCUS_AXIS
        and row.get("bucket") == PARENT_BUCKET_STABILITY_FOCUS_BUCKET
        and bool((row.get("post_oos_outcome_attribution") or {}).get("catastrophic"))
    ]
    candidate_by_identity: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    duplicate_candidate_identities: list[tuple[str, str, str, str]] = []
    for evaluation in candidate_evaluations:
        for candidate in evaluation.get("candidate_trades") or []:
            if str(candidate.get("venue")) != venue:
                continue
            identity = _entry_identity(candidate)
            if identity in candidate_by_identity:
                duplicate_candidate_identities.append(identity)
                continue
            candidate_by_identity[identity] = candidate

    episodes: list[dict[str, Any]] = []
    source_gaps: list[dict[str, Any]] = []
    for decision in catastrophic_decisions:
        identity = _entry_identity(decision)
        candidate = candidate_by_identity.get(identity)
        if candidate is None:
            source_gaps.append(
                {"identity": list(identity), "reason": "causal_candidate_missing"}
            )
            continue
        key = (
            date.fromisoformat(str(decision["trade_date"])),
            str(decision["venue"]),
            str(decision["session"]),
        )
        series = series_by_key.get(key)
        if not series:
            source_gaps.append(
                {"identity": list(identity), "reason": "market_series_missing"}
            )
            continue
        fixed_trade = _simulate_fixed_tp_split_trade(
            candidate,
            series,
            arm=PARENT_BUCKET_EXECUTION_ARM,
            cost_pct=cost_pct,
        )
        attributed = decision["post_oos_outcome_attribution"]
        if not str(fixed_trade["exit_reason"]).startswith("catastrophic"):
            source_gaps.append(
                {
                    "identity": list(identity),
                    "reason": "fixed_replay_no_longer_catastrophic",
                    "observed_exit_reason": fixed_trade["exit_reason"],
                }
            )
            continue
        if (
            abs(
                float(fixed_trade["net_profit_pct"])
                - float(attributed["planned_budget_return_pct"])
            )
            > 1e-6
        ):
            source_gaps.append(
                {
                    "identity": list(identity),
                    "reason": "fixed_replay_return_mismatch",
                    "replayed": fixed_trade["net_profit_pct"],
                    "attributed": attributed["planned_budget_return_pct"],
                }
            )
            continue
        stop_at = _timestamp_without_timezone(str(fixed_trade["exit_at"]))
        stop_price = float(fixed_trade["exit_price"])
        post_stop_bars = [
            bar
            for bar in series
            if _timestamp_without_timezone(bar.timestamp) > stop_at
        ]
        if not post_stop_bars:
            source_gaps.append(
                {"identity": list(identity), "reason": "post_stop_market_path_missing"}
            )
            continue
        fixed_fills = list(fixed_trade.get("filled_legs") or [])
        precise_total_quantity = sum(
            float(fill["quantity_units"]) for fill in fixed_fills
        )
        precise_deployed_capital = sum(
            float(fill["quantity_units"]) * float(fill["price"]) for fill in fixed_fills
        )
        if precise_total_quantity <= 0.0:
            source_gaps.append(
                {"identity": list(identity), "reason": "fixed_fill_quantity_invalid"}
            )
            continue
        precise_weighted_average = precise_deployed_capital / precise_total_quantity
        target_price = float(
            move_price_up_by_bps(
                precise_weighted_average,
                int(round(float(fixed_trade["target_pct_from_average"]) * 100.0)),
            )
        )
        target_hit_bar = next(
            (bar for bar in post_stop_bars if float(bar.high) >= target_price),
            None,
        )
        if target_hit_bar is not None:
            continuation_exit_reason = "post_stop_average_target_recovery"
            continuation_exit_at = _timestamp_without_timezone(target_hit_bar.timestamp)
            continuation_exit_price = target_price
            target_recovery_minutes = (
                continuation_exit_at - stop_at
            ).total_seconds() / 60.0
        else:
            continuation_exit_reason = "post_stop_last_observed_regular_mark"
            continuation_exit_at = _timestamp_without_timezone(
                post_stop_bars[-1].timestamp
            )
            continuation_exit_price = float(post_stop_bars[-1].close)
            target_recovery_minutes = None
        continuation_return = _planned_budget_mark_return_pct(
            fixed_trade,
            mark_price=continuation_exit_price,
            cost_pct=cost_pct,
        )
        terminal_observation_at = _timestamp_without_timezone(
            post_stop_bars[-1].timestamp
        )
        terminal_observation_exact_session_close = bool(
            str(decision["session"]) == "KRX_REGULAR"
            and terminal_observation_at.time() >= time(15, 30)
        )
        terminal_mark_return = _planned_budget_mark_return_pct(
            fixed_trade,
            mark_price=float(post_stop_bars[-1].close),
            cost_pct=cost_pct,
        )
        horizon_marks: dict[str, dict[str, Any]] = {}
        bars_by_timestamp = {
            _timestamp_without_timezone(bar.timestamp): bar for bar in post_stop_bars
        }
        for minutes in PARENT_POST_STOP_HORIZONS_MINUTES:
            bar = bars_by_timestamp.get(stop_at + timedelta(minutes=minutes))
            horizon_marks[str(minutes)] = {
                "available": bar is not None,
                "observed_at": (
                    _timestamp_without_timezone(bar.timestamp).isoformat()
                    if bar is not None
                    else None
                ),
                "close_price": float(bar.close) if bar is not None else None,
                "planned_budget_mark_return_pct": (
                    _planned_budget_mark_return_pct(
                        fixed_trade,
                        mark_price=float(bar.close),
                        cost_pct=cost_pct,
                    )
                    if bar is not None
                    else None
                ),
                "price_change_from_stop_pct": (
                    round((float(bar.close) / stop_price - 1.0) * 100.0, 6)
                    if bar is not None
                    else None
                ),
                "target_recovered_by_horizon": bool(
                    target_recovery_minutes is not None
                    and target_recovery_minutes <= minutes
                ),
            }
        minimum_post_stop_low = min(float(bar.low) for bar in post_stop_bars)
        maximum_post_stop_high = max(float(bar.high) for bar in post_stop_bars)
        control_return = float(fixed_trade["net_profit_pct"])
        episodes.append(
            {
                "trade_date": str(decision["trade_date"]),
                "venue": str(decision["venue"]),
                "session": str(decision["session"]),
                "entry_at": str(decision["entry_at"]),
                "entry_price": float(decision["entry_price"]),
                "stop_at": stop_at.isoformat(),
                "stop_price": stop_price,
                "stop_exit_reason": str(fixed_trade["exit_reason"]),
                "hard_stop_control_return_pct": control_return,
                "filled_leg_count": int(fixed_trade["filled_leg_count"]),
                "deployed_fraction": float(fixed_trade["deployed_fraction"]),
                "weighted_average_price": float(fixed_trade["weighted_average_price"]),
                "target_basis_precise_weighted_average_price": round(
                    precise_weighted_average,
                    10,
                ),
                "existing_average_target_price": target_price,
                "continuation_exit_reason": continuation_exit_reason,
                "continuation_exit_at": continuation_exit_at.isoformat(),
                "continuation_exit_price": continuation_exit_price,
                "continue_target_or_terminal_mark_return_pct": continuation_return,
                "incremental_return_vs_hard_stop_pct": round(
                    continuation_return - control_return,
                    6,
                ),
                "target_recovered_after_stop": target_hit_bar is not None,
                "target_recovery_first_hit_minutes": (
                    round(float(target_recovery_minutes), 3)
                    if target_recovery_minutes is not None
                    else None
                ),
                "terminal_observation_at": terminal_observation_at.isoformat(),
                "terminal_observation_price": float(post_stop_bars[-1].close),
                "terminal_observation_return_pct": terminal_mark_return,
                "terminal_observation_exact_session_close": (
                    terminal_observation_exact_session_close
                ),
                "continuation_endpoint_source_quality_complete": bool(
                    target_hit_bar is not None
                    or terminal_observation_exact_session_close
                ),
                "post_stop_min_low": minimum_post_stop_low,
                "post_stop_max_high": maximum_post_stop_high,
                "additional_drawdown_from_stop_price_pct": round(
                    (minimum_post_stop_low / stop_price - 1.0) * 100.0,
                    6,
                ),
                "maximum_rebound_from_stop_price_pct": round(
                    (maximum_post_stop_high / stop_price - 1.0) * 100.0,
                    6,
                ),
                "horizon_marks": horizon_marks,
                "provenance": {
                    "causal_candidate_joined": True,
                    "fixed_execution_replayed": True,
                    "stop_bar_excluded_from_counterfactual_path": True,
                    "post_stop_path_used_as_entry_feature": False,
                    "control_and_counterfactual_summed": False,
                },
            }
        )

    control_returns = [float(row["hard_stop_control_return_pct"]) for row in episodes]
    continuation_returns = [
        float(row["continue_target_or_terminal_mark_return_pct"]) for row in episodes
    ]
    control_ev = (
        round(statistics.fmean(control_returns), 6) if control_returns else None
    )
    continuation_ev = (
        round(statistics.fmean(continuation_returns), 6)
        if continuation_returns
        else None
    )
    target_recovery_count = sum(
        bool(row["target_recovered_after_stop"]) for row in episodes
    )
    continuation_better_count = sum(
        float(row["continue_target_or_terminal_mark_return_pct"])
        > float(row["hard_stop_control_return_pct"])
        for row in episodes
    )
    hard_stop_protected_count = sum(
        float(row["continue_target_or_terminal_mark_return_pct"])
        < float(row["hard_stop_control_return_pct"])
        for row in episodes
    )
    recovery_ratio = target_recovery_count / len(episodes) if episodes else None
    terminal_mark_limited_count = sum(
        not bool(row["continuation_endpoint_source_quality_complete"])
        for row in episodes
    )
    control_compounded = _compounded_return_from_values(control_returns)
    continuation_compounded = _compounded_return_from_values(continuation_returns)
    recovery_by_horizon = {
        str(minutes): sum(
            bool(row["horizon_marks"][str(minutes)]["target_recovered_by_horizon"])
            for row in episodes
        )
        for minutes in PARENT_POST_STOP_HORIZONS_MINUTES
    }
    if not source_quality_passed:
        decision = "source_quality_blocked"
    elif duplicate_candidate_identities or source_gaps or not episodes:
        decision = "source_contract_gap"
    elif (
        terminal_mark_limited_count == 0
        and recovery_ratio is not None
        and recovery_ratio >= PARENT_POST_STOP_RECOVERY_DOMINANCE_FLOOR
        and continuation_ev is not None
        and control_ev is not None
        and continuation_ev > control_ev
        and continuation_compounded > control_compounded
    ):
        decision = "recoverable_adverse_first_dominates"
    elif (
        terminal_mark_limited_count == 0
        and recovery_ratio is not None
        and recovery_ratio <= 1.0 - PARENT_POST_STOP_RECOVERY_DOMINANCE_FLOOR
        and control_ev is not None
        and continuation_ev is not None
        and control_ev >= continuation_ev
        and hard_stop_protected_count
        >= math.ceil(len(episodes) * PARENT_POST_STOP_RECOVERY_DOMINANCE_FLOOR)
    ):
        decision = "catastrophic_stop_terminal_loss_protection_supported"
    else:
        decision = "mixed_post_stop_paths_no_owner_change"
    return {
        "contract": PARENT_POST_STOP_RECOVERY_CONTRACT,
        "fixed_execution_arm": PARENT_BUCKET_EXECUTION_ARM,
        "input_parent_decision": parent_result.get("decision"),
        "input_catastrophic_decision_count": len(catastrophic_decisions),
        "input_decisions_unchanged": True,
        "source_quality_passed": source_quality_passed,
        "source_gap_count": len(source_gaps),
        "source_gaps": source_gaps,
        "duplicate_candidate_identity_count": len(duplicate_candidate_identities),
        "duplicate_candidate_identities": [
            list(identity) for identity in duplicate_candidate_identities
        ],
        "episode_count": len(episodes),
        "hard_stop_control_equal_weight_avg_profit_pct": control_ev,
        "hard_stop_control_source_quality_adjusted_ev_pct": (
            control_ev if source_quality_passed else None
        ),
        "continue_target_or_terminal_mark_equal_weight_avg_profit_pct": (
            continuation_ev
        ),
        "continue_target_or_terminal_mark_source_quality_adjusted_ev_pct": (
            continuation_ev
            if source_quality_passed and terminal_mark_limited_count == 0
            else None
        ),
        "hard_stop_control_compounded_return_pct": control_compounded,
        "continue_target_or_terminal_mark_compounded_return_pct": (
            continuation_compounded
        ),
        "target_recovery_count": target_recovery_count,
        "target_recovery_ratio": (
            round(recovery_ratio, 6) if recovery_ratio is not None else None
        ),
        "continuation_better_count": continuation_better_count,
        "hard_stop_protected_count": hard_stop_protected_count,
        "terminal_mark_limited_count": terminal_mark_limited_count,
        "decision_evidence_complete": bool(
            source_quality_passed
            and not source_gaps
            and not duplicate_candidate_identities
            and terminal_mark_limited_count == 0
        ),
        "recovery_by_horizon_count": recovery_by_horizon,
        "episodes": episodes,
        "decision": decision,
    }


def _parent_post_stop_bounded_grace_arms(
    recovery_result: dict[str, Any],
    series_by_key: dict[tuple[date, str, str], Sequence[base.Bar]],
    *,
    venue: str,
    source_quality_passed: bool,
) -> dict[str, Any]:
    source_gaps: list[dict[str, Any]] = []
    arm_episode_rows: dict[str, list[dict[str, Any]]] = {
        str(minutes): [] for minutes in PARENT_POST_STOP_GRACE_HORIZONS_MINUTES
    }
    recovery_episodes = list(recovery_result.get("episodes") or [])
    for episode in recovery_episodes:
        key = (
            date.fromisoformat(str(episode["trade_date"])),
            str(episode["venue"]),
            str(episode["session"]),
        )
        series = series_by_key.get(key)
        if not series:
            source_gaps.append(
                {
                    "trade_date": episode["trade_date"],
                    "entry_at": episode["entry_at"],
                    "reason": "market_series_missing",
                }
            )
            continue
        stop_at = _timestamp_without_timezone(str(episode["stop_at"]))
        stop_price = float(episode["stop_price"])
        target_recovery_minutes = episode.get("target_recovery_first_hit_minutes")
        target_recovery_at = (
            _timestamp_without_timezone(str(episode["continuation_exit_at"]))
            if target_recovery_minutes is not None
            else None
        )
        post_stop_bars_by_timestamp = {
            _timestamp_without_timezone(bar.timestamp): bar
            for bar in series
            if _timestamp_without_timezone(bar.timestamp) > stop_at
        }
        for minutes in PARENT_POST_STOP_GRACE_HORIZONS_MINUTES:
            arm_key = str(minutes)
            horizon_at = stop_at + timedelta(minutes=minutes)
            target_hit_within_grace = bool(
                target_recovery_at is not None and target_recovery_at <= horizon_at
            )
            if target_hit_within_grace:
                exit_at = target_recovery_at
                exit_price = float(episode["existing_average_target_price"])
                exit_reason = "existing_average_target_recovery"
                arm_return = float(
                    episode["continue_target_or_terminal_mark_return_pct"]
                )
            else:
                horizon_mark = (episode.get("horizon_marks") or {}).get(arm_key) or {}
                horizon_bar = post_stop_bars_by_timestamp.get(horizon_at)
                if (
                    horizon_bar is None
                    or not bool(horizon_mark.get("available"))
                    or horizon_mark.get("planned_budget_mark_return_pct") is None
                ):
                    source_gaps.append(
                        {
                            "trade_date": episode["trade_date"],
                            "entry_at": episode["entry_at"],
                            "arm_minutes": minutes,
                            "reason": "exact_horizon_completed_bar_missing",
                            "expected_at": horizon_at.isoformat(),
                        }
                    )
                    continue
                exit_at = horizon_at
                exit_price = float(horizon_bar.close)
                exit_reason = "exact_grace_horizon_completed_bar_mark"
                arm_return = float(horizon_mark["planned_budget_mark_return_pct"])
            bars_through_exit = [
                bar
                for timestamp, bar in post_stop_bars_by_timestamp.items()
                if timestamp <= exit_at
            ]
            bars_known_before_target = [
                bar
                for timestamp, bar in post_stop_bars_by_timestamp.items()
                if timestamp < exit_at
            ]
            if not bars_through_exit:
                source_gaps.append(
                    {
                        "trade_date": episode["trade_date"],
                        "entry_at": episode["entry_at"],
                        "arm_minutes": minutes,
                        "reason": "post_stop_bars_through_exit_missing",
                    }
                )
                continue
            conservative_min_low = min(float(bar.low) for bar in bars_through_exit)
            known_pre_target_min_low = (
                min(float(bar.low) for bar in bars_known_before_target)
                if target_hit_within_grace and bars_known_before_target
                else conservative_min_low
            )
            control_return = float(episode["hard_stop_control_return_pct"])
            arm_episode_rows[arm_key].append(
                {
                    "trade_date": episode["trade_date"],
                    "venue": episode["venue"],
                    "session": episode["session"],
                    "entry_at": episode["entry_at"],
                    "stop_at": episode["stop_at"],
                    "grace_minutes": minutes,
                    "exit_at": exit_at.isoformat(),
                    "exit_price": exit_price,
                    "exit_reason": exit_reason,
                    "target_recovered_within_grace": target_hit_within_grace,
                    "hard_stop_control_return_pct": control_return,
                    "grace_planned_budget_return_pct": arm_return,
                    "incremental_return_vs_hard_stop_pct": round(
                        arm_return - control_return,
                        6,
                    ),
                    "additional_mae_from_stop_pct_conservative": round(
                        min(
                            0.0,
                            (conservative_min_low / stop_price - 1.0) * 100.0,
                        ),
                        6,
                    ),
                    "additional_mae_known_before_target_bar_pct": round(
                        min(
                            0.0,
                            (known_pre_target_min_low / stop_price - 1.0) * 100.0,
                        ),
                        6,
                    ),
                    "provenance": {
                        "stop_bar_excluded": True,
                        "existing_target_unchanged": True,
                        "filled_quantity_unchanged": True,
                        "target_hit_bar_mae_is_conservative_intrabar_envelope": (
                            target_hit_within_grace
                        ),
                        "same_sample_best_arm_selected": False,
                        "runtime_effect": False,
                    },
                }
            )

    control_ev = recovery_result.get("hard_stop_control_source_quality_adjusted_ev_pct")
    control_compounded = recovery_result.get("hard_stop_control_compounded_return_pct")
    if not recovery_episodes or control_ev is None:
        control_compounded = None
    arm_summaries: dict[str, dict[str, Any]] = {}
    prospective_candidate_horizons: list[int] = []
    expected_episode_count = len(recovery_episodes)
    for minutes in PARENT_POST_STOP_GRACE_HORIZONS_MINUTES:
        arm_key = str(minutes)
        episode_rows = arm_episode_rows[arm_key]
        returns = [
            float(row["grace_planned_budget_return_pct"]) for row in episode_rows
        ]
        arm_ev = round(statistics.fmean(returns), 6) if returns else None
        arm_compounded = _compounded_return_from_values(returns) if returns else None
        arm_source_complete = bool(
            source_quality_passed
            and expected_episode_count > 0
            and len(episode_rows) == expected_episode_count
            and not source_gaps
        )
        source_adjusted_ev = arm_ev if arm_source_complete else None
        improves_both_control_metrics = bool(
            source_adjusted_ev is not None
            and control_ev is not None
            and arm_compounded is not None
            and control_compounded is not None
            and float(source_adjusted_ev) > float(control_ev)
            and float(arm_compounded) > float(control_compounded)
        )
        if improves_both_control_metrics:
            prospective_candidate_horizons.append(minutes)
        conservative_mae_values = [
            float(row["additional_mae_from_stop_pct_conservative"])
            for row in episode_rows
        ]
        arm_summaries[arm_key] = {
            "grace_minutes": minutes,
            "episode_count": len(episode_rows),
            "equal_weight_avg_profit_pct": arm_ev,
            "source_quality_adjusted_ev_pct": source_adjusted_ev,
            "compounded_return_pct": arm_compounded,
            "target_recovery_count": sum(
                bool(row["target_recovered_within_grace"]) for row in episode_rows
            ),
            "improved_episode_count": sum(
                float(row["incremental_return_vs_hard_stop_pct"]) > 0.0
                for row in episode_rows
            ),
            "worsened_episode_count": sum(
                float(row["incremental_return_vs_hard_stop_pct"]) < 0.0
                for row in episode_rows
            ),
            "equal_episode_count": sum(
                float(row["incremental_return_vs_hard_stop_pct"]) == 0.0
                for row in episode_rows
            ),
            "average_additional_mae_from_stop_pct_conservative": (
                round(statistics.fmean(conservative_mae_values), 6)
                if conservative_mae_values
                else None
            ),
            "worst_additional_mae_from_stop_pct_conservative": (
                min(conservative_mae_values) if conservative_mae_values else None
            ),
            "improves_both_control_ev_and_compounded_return": (
                improves_both_control_metrics
            ),
            "prospective_candidate_only": improves_both_control_metrics,
            "episodes": episode_rows,
        }

    if not source_quality_passed or recovery_result.get("decision") == (
        "source_quality_blocked"
    ):
        decision = "source_quality_blocked"
    elif (
        recovery_result.get("source_gap_count")
        or recovery_result.get("duplicate_candidate_identity_count")
        or source_gaps
        or not recovery_episodes
    ):
        decision = "source_contract_gap"
    elif prospective_candidate_horizons:
        decision = "bounded_grace_candidate_for_prospective_only"
    elif all(
        summary["source_quality_adjusted_ev_pct"] is not None
        and control_ev is not None
        and float(summary["source_quality_adjusted_ev_pct"]) <= float(control_ev)
        and summary["compounded_return_pct"] is not None
        and control_compounded is not None
        and float(summary["compounded_return_pct"]) <= float(control_compounded)
        for summary in arm_summaries.values()
    ):
        decision = "immediate_stop_retained"
    else:
        decision = "grace_tradeoff_mixed"
    return {
        "contract": PARENT_POST_STOP_GRACE_CONTRACT,
        "venue": venue,
        "input_recovery_decision": recovery_result.get("decision"),
        "input_episode_count": expected_episode_count,
        "input_episodes_unchanged": True,
        "source_quality_passed": source_quality_passed,
        "source_gap_count": len(source_gaps),
        "source_gaps": source_gaps,
        "hard_stop_control_equal_weight_avg_profit_pct": control_ev,
        "hard_stop_control_compounded_return_pct": control_compounded,
        "arms": arm_summaries,
        "prospective_candidate_horizons_minutes": prospective_candidate_horizons,
        "same_sample_best_arm_selected": False,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "decision": decision,
    }


def _parent_post_stop_grace_prospective_oos(
    grace_result: dict[str, Any],
    *,
    venue: str,
    source_quality_passed: bool,
) -> dict[str, Any]:
    candidate_horizons = list(PARENT_POST_STOP_GRACE_PROSPECTIVE_HORIZONS_MINUTES)
    source_gaps: list[dict[str, Any]] = []
    input_arms = grace_result.get("arms") or {}
    expected_arm_keys = {str(minutes) for minutes in candidate_horizons}
    if set(input_arms) != expected_arm_keys:
        source_gaps.append(
            {
                "reason": "frozen_candidate_horizon_set_mismatch",
                "expected": sorted(expected_arm_keys),
                "observed": sorted(input_arms),
            }
        )

    calibration_identities_by_arm: dict[str, set[tuple[str, str, str]]] = {}
    prospective_rows_by_arm: dict[str, list[dict[str, Any]]] = {}
    for minutes in candidate_horizons:
        arm_key = str(minutes)
        rows = list((input_arms.get(arm_key) or {}).get("episodes") or [])
        calibration_identities_by_arm[arm_key] = {
            (
                str(row["trade_date"]),
                str(row["entry_at"]),
                str(row["stop_at"]),
            )
            for row in rows
            if date.fromisoformat(str(row["trade_date"]))
            <= PARENT_POST_STOP_GRACE_PROSPECTIVE_CUTOFF_DATE
        }
        prospective_rows_by_arm[arm_key] = [
            row
            for row in rows
            if date.fromisoformat(str(row["trade_date"]))
            >= PARENT_POST_STOP_GRACE_PROSPECTIVE_START_DATE
        ]

    calibration_identity_sets = list(calibration_identities_by_arm.values())
    calibration_identities = (
        calibration_identity_sets[0] if calibration_identity_sets else set()
    )
    if any(
        identities != calibration_identities
        for identities in calibration_identity_sets[1:]
    ):
        source_gaps.append(
            {
                "reason": "calibration_episode_identity_mismatch_across_arms",
                "counts": {
                    arm: len(identities)
                    for arm, identities in calibration_identities_by_arm.items()
                },
            }
        )
    if (
        source_quality_passed
        and venue == "KRX"
        and len(calibration_identities)
        != PARENT_POST_STOP_GRACE_CALIBRATION_EPISODE_COUNT
    ):
        source_gaps.append(
            {
                "reason": "frozen_calibration_episode_count_mismatch",
                "expected": PARENT_POST_STOP_GRACE_CALIBRATION_EPISODE_COUNT,
                "observed": len(calibration_identities),
            }
        )

    prospective_identities_by_arm = {
        arm: {
            (
                str(row["trade_date"]),
                str(row["entry_at"]),
                str(row["stop_at"]),
            )
            for row in rows
        }
        for arm, rows in prospective_rows_by_arm.items()
    }
    prospective_identity_sets = list(prospective_identities_by_arm.values())
    prospective_identities = (
        prospective_identity_sets[0] if prospective_identity_sets else set()
    )
    if any(
        identities != prospective_identities
        for identities in prospective_identity_sets[1:]
    ):
        source_gaps.append(
            {
                "reason": "prospective_episode_identity_mismatch_across_arms",
                "counts": {
                    arm: len(identities)
                    for arm, identities in prospective_identities_by_arm.items()
                },
            }
        )

    for gap in grace_result.get("source_gaps") or []:
        trade_date_value = gap.get("trade_date")
        if (
            trade_date_value is None
            or date.fromisoformat(str(trade_date_value))
            >= PARENT_POST_STOP_GRACE_PROSPECTIVE_START_DATE
        ):
            source_gaps.append(
                {
                    **gap,
                    "reason": f"prospective_input_{gap.get('reason', 'source_gap')}",
                }
            )

    control_returns_by_identity: dict[tuple[str, str, str], float] = {}
    for arm_key, rows in prospective_rows_by_arm.items():
        for row in rows:
            identity = (
                str(row["trade_date"]),
                str(row["entry_at"]),
                str(row["stop_at"]),
            )
            control_return = float(row["hard_stop_control_return_pct"])
            prior = control_returns_by_identity.setdefault(identity, control_return)
            if abs(prior - control_return) > 1e-9:
                source_gaps.append(
                    {
                        "reason": "prospective_control_return_mismatch_across_arms",
                        "identity": list(identity),
                        "arm": arm_key,
                        "first": prior,
                        "observed": control_return,
                    }
                )

    control_returns = [
        control_returns_by_identity[identity]
        for identity in sorted(control_returns_by_identity)
    ]
    control_ev = (
        round(statistics.fmean(control_returns), 6) if control_returns else None
    )
    control_compounded = (
        _compounded_return_from_values(control_returns) if control_returns else None
    )
    arm_summaries: dict[str, dict[str, Any]] = {}
    all_arms_improve_control = bool(prospective_identities)
    for minutes in candidate_horizons:
        arm_key = str(minutes)
        rows = prospective_rows_by_arm[arm_key]
        returns = [float(row["grace_planned_budget_return_pct"]) for row in rows]
        arm_ev = round(statistics.fmean(returns), 6) if returns else None
        arm_compounded = _compounded_return_from_values(returns) if returns else None
        source_complete = bool(
            source_quality_passed
            and prospective_identities
            and len(rows) == len(prospective_identities)
            and not source_gaps
        )
        source_adjusted_ev = arm_ev if source_complete else None
        improves_control = bool(
            source_adjusted_ev is not None
            and control_ev is not None
            and arm_compounded is not None
            and control_compounded is not None
            and float(source_adjusted_ev) > float(control_ev)
            and float(arm_compounded) > float(control_compounded)
        )
        all_arms_improve_control = all_arms_improve_control and improves_control
        mae_values = [
            float(row["additional_mae_from_stop_pct_conservative"]) for row in rows
        ]
        arm_summaries[arm_key] = {
            "grace_minutes": minutes,
            "prospective_episode_count": len(rows),
            "equal_weight_avg_profit_pct": arm_ev,
            "source_quality_adjusted_ev_pct": source_adjusted_ev,
            "compounded_return_pct": arm_compounded,
            "target_recovery_count": sum(
                bool(row["target_recovered_within_grace"]) for row in rows
            ),
            "improved_episode_count": sum(
                float(row["incremental_return_vs_hard_stop_pct"]) > 0.0 for row in rows
            ),
            "worsened_episode_count": sum(
                float(row["incremental_return_vs_hard_stop_pct"]) < 0.0 for row in rows
            ),
            "average_additional_mae_from_stop_pct_conservative": (
                round(statistics.fmean(mae_values), 6) if mae_values else None
            ),
            "worst_additional_mae_from_stop_pct_conservative": (
                min(mae_values) if mae_values else None
            ),
            "improves_both_prospective_control_ev_and_compounded_return": (
                improves_control
            ),
            "episodes": rows,
        }

    if not source_quality_passed or grace_result.get("decision") == (
        "source_quality_blocked"
    ):
        decision = "source_quality_blocked"
    elif source_gaps:
        decision = "source_contract_gap"
    elif not prospective_identities:
        decision = "no_new_catastrophic_episode_observe"
    elif all_arms_improve_control:
        decision = "prospective_grace_evidence_accumulating"
    else:
        decision = "prospective_grace_tradeoff_changed"
    return {
        "contract": PARENT_POST_STOP_GRACE_PROSPECTIVE_CONTRACT,
        "venue": venue,
        "candidate_horizons_minutes_frozen": candidate_horizons,
        "candidate_horizons_frozen_at": (
            PARENT_POST_STOP_GRACE_PROSPECTIVE_CUTOFF_DATE.isoformat()
        ),
        "prospective_start_date": (
            PARENT_POST_STOP_GRACE_PROSPECTIVE_START_DATE.isoformat()
        ),
        "calibration_episode_count_excluded": len(calibration_identities),
        "prospective_episode_count": len(prospective_identities),
        "source_quality_passed": source_quality_passed,
        "source_gap_count": len(source_gaps),
        "source_gaps": source_gaps,
        "hard_stop_control_equal_weight_avg_profit_pct": control_ev,
        "hard_stop_control_compounded_return_pct": control_compounded,
        "arms": arm_summaries,
        "same_sample_best_arm_selected": False,
        "calibration_and_prospective_returns_mixed": False,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "decision": decision,
    }


def _compact_fixed_execution_report_payload(
    result: dict[str, Any],
    *,
    split_execution: bool,
) -> dict[str, Any]:
    compact_evaluations: list[dict[str, Any]] = []
    for evaluation in result.get("evaluations") or []:
        compact = dict(evaluation)
        if split_execution:
            arm_trades = compact.pop("arm_trades", {}) or {}
            selected_policy_trades = compact.pop("selected_policy_trades", []) or []
            selected_control_trades = compact.pop("selected_control_trades", []) or []
            compact["arm_trade_counts"] = {
                str(arm): len(trades) for arm, trades in arm_trades.items()
            }
            compact["selected_policy_trade_count"] = len(selected_policy_trades)
            compact["selected_control_trade_count"] = len(selected_control_trades)
        else:
            control_trades = compact.pop("control_trades", []) or []
            selected_trades = compact.pop("selected_trades", []) or []
            compact["control_trade_count"] = len(control_trades)
            compact["selected_trade_count"] = len(selected_trades)
        compact["trade_detail_storage"] = "omitted_replayable_from_source_bars"
        compact_evaluations.append(compact)
    return {**result, "evaluations": compact_evaluations}


def _paired_axis_delta_summary(
    baseline: Sequence[dict[str, Any]],
    arm: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    baseline_by_entry = {_entry_identity(row): row for row in baseline}
    if list(baseline_by_entry) != [_entry_identity(row) for row in arm]:
        raise ValueError("axis arm does not preserve the baseline entry cohort")
    deltas = [
        float(row["net_profit_pct"])
        - float(baseline_by_entry[_entry_identity(row)]["net_profit_pct"])
        for row in arm
    ]
    return {
        "sample_count": len(deltas),
        "avg_incremental_net_profit_pct": (
            round(statistics.fmean(deltas), 6) if deltas else None
        ),
        "improved_count": sum(value > 0.0 for value in deltas),
        "unchanged_count": sum(value == 0.0 for value in deltas),
        "degraded_count": sum(value < 0.0 for value in deltas),
    }


def _recovery_path_diagnostics(
    episodes: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    economic_compatible = [
        {
            **row,
            "economic_first_passage_event": row.get(
                "baseline_economic_first_passage_event", "not_applicable"
            ),
        }
        for row in episodes
    ]
    base_diagnostics = _economic_path_diagnostics(economic_compatible)
    if not episodes:
        return {
            **base_diagnostics,
            "recovery_checkpoint_count": 0,
            "recovery_deferred_count": 0,
            "recovery_deferred_pct": None,
            "recovered_to_favorable_count": 0,
            "trailing_exit_count": 0,
            "deep_adverse_exit_count": 0,
            "timeout_exit_count": 0,
            "avg_positive_mfe_capture_ratio_pct": None,
        }
    deferred = [row for row in episodes if row.get("recovery_deferred")]
    capture_ratios = [
        max(0.0, float(row["gross_profit_pct"]))
        / max(
            float(row["post_entry_session_mfe_pct"]),
            float(row["gross_profit_pct"]),
        )
        * 100.0
        for row in episodes
        if max(
            float(row["post_entry_session_mfe_pct"]),
            float(row["gross_profit_pct"]),
        )
        > 0.0
    ]
    return {
        **base_diagnostics,
        "recovery_checkpoint_count": sum(
            row.get("recovery_checkpoint_at") is not None for row in episodes
        ),
        "recovery_deferred_count": len(deferred),
        "recovery_deferred_pct": round(len(deferred) / len(episodes) * 100.0, 3),
        "recovered_to_favorable_count": sum(
            row.get("recovery_realized_minutes") is not None for row in episodes
        ),
        "trailing_exit_count": sum(
            str(row.get("exit_reason", "")).startswith("favorable_trailing")
            for row in episodes
        ),
        "deep_adverse_exit_count": sum(
            row.get("exit_reason") == "recovery_deep_adverse_exit" for row in episodes
        ),
        "timeout_exit_count": sum(
            row.get("exit_reason") == "recovery_timeout_exit" for row in episodes
        ),
        "avg_positive_mfe_capture_ratio_pct": (
            round(statistics.fmean(capture_ratios), 3) if capture_ratios else None
        ),
    }


def _confidence_diagnostics(
    trades: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    eligible = [
        row for row in trades if row.get("joint_transition_confidence") is not None
    ]
    ordered = sorted(
        eligible,
        key=lambda row: float(row["joint_transition_confidence"]),
        reverse=True,
    )
    top_slices: dict[str, Any] = {}
    for fraction in (0.10, 0.25, 0.50, 1.00):
        count = max(1, math.ceil(len(ordered) * fraction)) if ordered else 0
        selected = ordered[:count]
        key = f"top_{int(fraction * 100)}pct"
        top_slices[key] = {
            "sample_count": len(selected),
            "minimum_joint_transition_confidence": (
                round(
                    min(float(row["joint_transition_confidence"]) for row in selected),
                    6,
                )
                if selected
                else None
            ),
            "equal_weight_avg_profit_pct": (
                round(
                    statistics.fmean(float(row["net_profit_pct"]) for row in selected),
                    6,
                )
                if selected
                else None
            ),
            "diagnostic_win_rate_pct": (
                round(
                    sum(float(row["net_profit_pct"]) > 0 for row in selected)
                    / len(selected)
                    * 100.0,
                    3,
                )
                if selected
                else None
            ),
        }
    return {
        "role": "post_oos_confidence_slice_diagnostic_only",
        "forbidden_use": "same_report_threshold_selection_or_runtime_apply",
        "eligible_trade_count": len(eligible),
        "top_slices": top_slices,
    }


def _summary(
    trades: Sequence[dict[str, Any]], *, source_quality_passed: bool
) -> dict[str, Any]:
    if not trades:
        return {
            "sample_count": 0,
            "equal_weight_avg_profit_pct": None,
            "source_quality_adjusted_ev_pct": None,
            "diagnostic_win_rate_pct": None,
        }
    net = [float(row["net_profit_pct"]) for row in trades]
    ev = statistics.fmean(net)
    return {
        "sample_count": len(trades),
        "trading_date_count": len({row["trade_date"] for row in trades}),
        "equal_weight_avg_profit_pct": round(ev, 6),
        "notional_weighted_ev_pct": round(
            sum(value * float(row["entry_price"]) for value, row in zip(net, trades))
            / sum(float(row["entry_price"]) for row in trades),
            6,
        ),
        "source_quality_adjusted_ev_pct": (
            round(ev, 6) if source_quality_passed else None
        ),
        "diagnostic_win_rate_pct": round(
            sum(value > 0 for value in net) / len(net) * 100.0, 3
        ),
        "exit_reason_counts": dict(
            sorted(Counter(row["exit_reason"] for row in trades).items())
        ),
    }


def _feature_contrasts(
    rows: Sequence[FeatureRow], *, action: int
) -> list[dict[str, Any]]:
    positives = [row for row in rows if row.oracle_action == action]
    negatives = [row for row in rows if row.oracle_action != action]
    if not positives or not negatives:
        return []
    contrasts = []
    for index, name in enumerate(FEATURE_NAMES):
        positive_values = [row.features[index] for row in positives]
        negative_values = [row.features[index] for row in negatives]
        combined_scale = statistics.pstdev(positive_values + negative_values)
        standardized_gap = (
            (statistics.fmean(positive_values) - statistics.fmean(negative_values))
            / combined_scale
            if combined_scale > 0
            else 0.0
        )
        contrasts.append(
            {
                "feature": name,
                "standardized_mean_gap": round(standardized_gap, 6),
                "oracle_action_mean": round(statistics.fmean(positive_values), 6),
                "other_mean": round(statistics.fmean(negative_values), 6),
            }
        )
    return sorted(
        contrasts, key=lambda row: abs(row["standardized_mean_gap"]), reverse=True
    )


def build_report(
    stock_bars: Sequence[base.Bar],
    kospi_bars: Sequence[base.Bar],
    *,
    stock_source_quality: dict[str, Any],
    kospi_source_quality: dict[str, Any],
    training_days: int = 20,
    cost_pct: float = 0.20,
) -> dict[str, Any]:
    coverage = base.assess_date_coverage(stock_bars)
    qualified = base.filter_coverage_qualified_bars(stock_bars, coverage)
    qualified_series_by_key = base._group_series(qualified)
    rows, oracle = build_feature_rows(qualified, kospi_bars, cost_pct=cost_pct)
    oracle_cost_sensitivity = _oracle_cost_sensitivity(qualified)
    cohorts: dict[str, Any] = {}
    for venue in base.COHORTS:
        venue_rows = [row for row in rows if row.venue == venue]
        available_dates = sorted({row.trade_date for row in venue_rows})
        context_index = FEATURE_NAMES.index("market_context_available")
        exact_context_complete = all(
            row.features[context_index] == 1.0 for row in venue_rows
        )
        source_quality_passed = (
            stock_source_quality.get("venue_status", {}).get(venue) == "PASS"
            and venue == "KRX"
            and kospi_source_quality.get("status") == "PASS"
            and exact_context_complete
        )
        evaluations = []
        oos_trades: list[dict[str, Any]] = []
        buy_truth: list[int] = []
        sell_truth: list[int] = []
        buy_scores: list[float] = []
        sell_scores: list[float] = []
        pairability_history: list[dict[str, Any]] = []
        pairability_control_trades: list[dict[str, Any]] = []
        pairability_selected_trades: list[dict[str, Any]] = []
        pairability_evaluations: list[dict[str, Any]] = []
        competing_risk_history: list[dict[str, Any]] = []
        competing_risk_control_trades: list[dict[str, Any]] = []
        competing_risk_selected_trades: list[dict[str, Any]] = []
        competing_risk_evaluations: list[dict[str, Any]] = []
        economic_history: list[dict[str, Any]] = []
        economic_control_trades: list[dict[str, Any]] = []
        economic_selected_trades: list[dict[str, Any]] = []
        economic_evaluations: list[dict[str, Any]] = []
        recoverable_basin_candidate_evaluations: list[dict[str, Any]] = []
        recovery_baseline_selected_trades: list[dict[str, Any]] = []
        recovery_selected_trades: list[dict[str, Any]] = []
        recovery_evaluations: list[dict[str, Any]] = []
        axis_arm_trades: dict[str, list[dict[str, Any]]] = {
            arm: []
            for arm in (
                "baseline",
                "recovery_only",
                "trailing_only",
                "recovery_plus_trailing",
            )
        }
        axis_evaluations: list[dict[str, Any]] = []
        recovery_entry_history: list[dict[str, Any]] = []
        recovery_entry_control_trades: list[dict[str, Any]] = []
        recovery_entry_selected_trades: list[dict[str, Any]] = []
        recovery_entry_evaluations: list[dict[str, Any]] = []
        recovery_entry_calibration_history: list[dict[str, Any]] = []
        calibration_control_trades: list[dict[str, Any]] = []
        calibration_raw_selected_trades: list[dict[str, Any]] = []
        calibration_selected_trades: list[dict[str, Any]] = []
        calibration_scored_oos: list[dict[str, Any]] = []
        calibration_evaluations: list[dict[str, Any]] = []
        recovery_entry_timing_history: list[dict[str, Any]] = []
        recovery_entry_timing_control_trades: list[dict[str, Any]] = []
        recovery_entry_timing_selected_trades: list[dict[str, Any]] = []
        recovery_entry_timing_arm_trades: dict[str, list[dict[str, Any]]] = {
            arm: [] for arm in RECOVERY_ENTRY_TIMING_ARMS
        }
        recovery_entry_timing_evaluations: list[dict[str, Any]] = []
        candidate_timing_utility_history: list[dict[str, Any]] = []
        candidate_timing_utility_control_trades: list[dict[str, Any]] = []
        candidate_timing_utility_selected_trades: list[dict[str, Any]] = []
        candidate_timing_utility_evaluations: list[dict[str, Any]] = []
        trigger_utility_prediction_history: list[dict[str, Any]] = []
        trigger_calibration_control_trades: list[dict[str, Any]] = []
        trigger_calibration_raw_gate_trades: list[dict[str, Any]] = []
        trigger_calibration_selected_trades: list[dict[str, Any]] = []
        trigger_calibration_evaluations: list[dict[str, Any]] = []
        wait_budget_arm_history: list[dict[str, Any]] = []
        wait_budget_arm_trades: dict[str, list[dict[str, Any]]] = {
            arm: [] for arm in WAIT_BUDGET_ARMS
        }
        wait_budget_selected_trades: list[dict[str, Any]] = []
        wait_budget_evaluations: list[dict[str, Any]] = []
        for date_index, evaluation_date in enumerate(available_dates):
            train_dates = available_dates[
                max(0, date_index - training_days) : date_index
            ]
            if len(train_dates) < training_days:
                evaluations.append(
                    {
                        "evaluation_date": evaluation_date.isoformat(),
                        "status": "insufficient_prior_trading_days",
                    }
                )
                continue
            train_rows = [row for row in venue_rows if row.trade_date in train_dates]
            buy_bundle = _fit_action_model(train_rows, action=1)
            sell_bundle = _fit_action_model(train_rows, action=-1)
            if buy_bundle is None or sell_bundle is None:
                evaluations.append(
                    {
                        "evaluation_date": evaluation_date.isoformat(),
                        "status": "insufficient_oracle_action_samples",
                    }
                )
                continue
            buy_model, buy_threshold, buy_meta = buy_bundle
            sell_model, sell_threshold, sell_meta = sell_bundle
            hold_cap = _historical_oracle_hold_cap(train_rows)
            if hold_cap is None:
                evaluations.append(
                    {
                        "evaluation_date": evaluation_date.isoformat(),
                        "status": "insufficient_oracle_duration_samples",
                    }
                )
                continue
            evaluation_rows = [
                row for row in venue_rows if row.trade_date == evaluation_date
            ]
            trades, scored_rows = _simulate_evaluation_rows(
                evaluation_rows,
                buy_model=buy_model,
                buy_threshold=buy_threshold,
                sell_model=sell_model,
                sell_threshold=sell_threshold,
                cost_pct=cost_pct,
                max_hold_minutes=int(hold_cap["max_hold_minutes"]),
            )
            oos_trades.extend(trades)
            buy_truth.extend(int(row.oracle_action == 1) for row, _, _ in scored_rows)
            sell_truth.extend(int(row.oracle_action == -1) for row, _, _ in scored_rows)
            buy_scores.extend(buy_score for _, buy_score, _ in scored_rows)
            sell_scores.extend(sell_score for _, _, sell_score in scored_rows)
            pairability_bundle = _fit_pairability_model(pairability_history)
            if pairability_bundle is None:
                pairability_evaluations.append(
                    {
                        "evaluation_date": evaluation_date.isoformat(),
                        "status": "insufficient_prior_pairability_history",
                        "prior_episode_count": len(pairability_history),
                        "prior_date_count": len(
                            {row["trade_date"] for row in pairability_history}
                        ),
                    }
                )
            else:
                pair_model, pair_threshold, pair_meta = pairability_bundle
                pair_selected, _ = _simulate_evaluation_rows(
                    evaluation_rows,
                    buy_model=buy_model,
                    buy_threshold=buy_threshold,
                    sell_model=sell_model,
                    sell_threshold=sell_threshold,
                    cost_pct=cost_pct,
                    max_hold_minutes=int(hold_cap["max_hold_minutes"]),
                    pairability_model=pair_model,
                    pairability_threshold=pair_threshold,
                )
                pairability_control_trades.extend(trades)
                pairability_selected_trades.extend(pair_selected)
                pairability_evaluations.append(
                    {
                        "evaluation_date": evaluation_date.isoformat(),
                        "status": "evaluated_nested_out_of_sample",
                        "model": pair_meta,
                        "control_trade_count": len(trades),
                        "selected_trade_count": len(pair_selected),
                        "selected_trades": pair_selected,
                    }
                )
            pairability_history.extend(trades)
            current_risk_candidates = _extract_competing_risk_candidates(
                evaluation_rows,
                buy_model=buy_model,
                buy_threshold=buy_threshold,
                sell_model=sell_model,
                sell_threshold=sell_threshold,
                cost_pct=cost_pct,
            )
            lane_models: dict[str, dict[str, Any]] = {}
            eligible_control_candidates: list[dict[str, Any]] = []
            scored_risk_candidates: list[dict[str, Any]] = []
            for lane in ("weak_reversal", "bullish_transition"):
                lane_bundle = _fit_lane_competing_risk_model(
                    competing_risk_history,
                    lane=lane,
                )
                if lane_bundle is None:
                    lane_models[lane] = {"status": "insufficient_prior_lane_history"}
                    continue
                event_model, ev_model, lane_meta = lane_bundle
                lane_current = [
                    row
                    for row in current_risk_candidates
                    if row["pairability_lane"] == lane
                ]
                eligible_control_candidates.extend(lane_current)
                lane_scored = _score_competing_risk_candidates(
                    lane_current,
                    event_model=event_model,
                    ev_model=ev_model,
                )
                scored_risk_candidates.extend(lane_scored)
                lane_models[lane] = {
                    "status": "evaluated_nested_out_of_sample",
                    "model": lane_meta,
                    "candidate_count": len(lane_current),
                    "selected_candidate_count": sum(
                        bool(row["competing_risk_selected"]) for row in lane_scored
                    ),
                }
            if any(
                row["status"] == "evaluated_nested_out_of_sample"
                for row in lane_models.values()
            ):
                risk_control = _non_overlapping_candidates(
                    eligible_control_candidates,
                    selected_only=False,
                )
                risk_selected = _non_overlapping_candidates(
                    scored_risk_candidates,
                    selected_only=True,
                )
                competing_risk_control_trades.extend(risk_control)
                competing_risk_selected_trades.extend(risk_selected)
                competing_status = "evaluated_nested_out_of_sample"
            else:
                risk_control = []
                risk_selected = []
                competing_status = "insufficient_prior_lane_history"
            competing_risk_evaluations.append(
                {
                    "evaluation_date": evaluation_date.isoformat(),
                    "status": competing_status,
                    "lane_models": lane_models,
                    "control_trades": risk_control,
                    "selected_trades": risk_selected,
                }
            )
            competing_risk_history.extend(current_risk_candidates)
            current_economic_candidates = _extract_economic_first_passage_candidates(
                evaluation_rows,
                buy_model=buy_model,
                buy_threshold=buy_threshold,
                sell_model=sell_model,
                sell_threshold=sell_threshold,
            )
            economic_lane_models: dict[str, dict[str, Any]] = {}
            economic_control_candidates: list[dict[str, Any]] = []
            economic_scored_candidates: list[dict[str, Any]] = []
            axis_lane_models: dict[str, dict[str, Any]] = {}
            recovery_entry_lane_models: dict[str, dict[str, Any]] = {}
            current_recovery_entry_history: list[dict[str, Any]] = []
            recovery_entry_control_candidates: list[dict[str, Any]] = []
            recovery_entry_scored_candidates: list[dict[str, Any]] = []
            calibration_lane_models: dict[str, dict[str, Any]] = {}
            current_recovery_entry_calibration_history: list[dict[str, Any]] = []
            calibration_control_candidates: list[dict[str, Any]] = []
            calibration_raw_candidates: list[dict[str, Any]] = []
            calibration_scored_candidates: list[dict[str, Any]] = []
            timing_lane_models: dict[str, dict[str, Any]] = {}
            current_recovery_entry_timing_history: list[dict[str, Any]] = []
            timing_utility_lane_models: dict[str, dict[str, Any]] = {}
            current_candidate_timing_utility_history: list[dict[str, Any]] = []
            timing_utility_control_candidates: list[dict[str, Any]] = []
            timing_utility_selected_candidates: list[dict[str, Any]] = []
            timing_utility_lane_capacities: dict[str, dict[str, Any]] = {}
            timing_utility_decisions: list[dict[str, Any]] = []
            current_trigger_utility_prediction_history: list[dict[str, Any]] = []
            trigger_calibration_lane_models: dict[str, dict[str, Any]] = {}
            trigger_calibration_control_candidates: list[dict[str, Any]] = []
            trigger_calibration_raw_gate_candidates: list[dict[str, Any]] = []
            trigger_calibration_selected_candidates: list[dict[str, Any]] = []
            trigger_calibration_lane_capacities: dict[str, dict[str, Any]] = {}
            trigger_calibration_decisions: list[dict[str, Any]] = []
            wait_budget_lane_models: dict[str, dict[str, Any]] = {}
            wait_budget_arm_candidates: dict[str, list[dict[str, Any]]] = {
                arm: [] for arm in WAIT_BUDGET_ARMS
            }
            wait_budget_arm_decisions: dict[str, list[dict[str, Any]]] = {
                arm: [] for arm in WAIT_BUDGET_ARMS
            }
            wait_budget_lane_arm_capacities: dict[str, dict[str, dict[str, Any]]] = {}
            wait_budget_selected_candidates: list[dict[str, Any]] = []
            timing_control_candidates: list[dict[str, Any]] = []
            timing_selected_candidates: list[dict[str, Any]] = []
            timing_arm_candidates: dict[str, list[dict[str, Any]]] = {
                arm: [] for arm in RECOVERY_ENTRY_TIMING_ARMS
            }
            timing_lane_capacities: dict[str, dict[str, Any]] = {}
            timing_lane_arm_capacities: dict[str, dict[str, dict[str, Any]]] = {}
            axis_candidates_by_entry: dict[
                str, dict[tuple[str, str, str, str], dict[str, Any]]
            ] = {
                "recovery_only": {},
                "trailing_only": {},
                "recovery_plus_trailing": {},
            }
            for lane in ("weak_reversal", "bullish_transition"):
                timing_utility_lane_models[lane] = {
                    "status": "insufficient_prior_timing_pair_history"
                }
                trigger_calibration_lane_models[lane] = {
                    "status": "insufficient_prior_trigger_prediction_history"
                }
                wait_budget_lane_models[lane] = {
                    "status": "insufficient_prior_trigger_prediction_history"
                }
                economic_bundle = _fit_lane_economic_first_passage_model(
                    economic_history,
                    lane=lane,
                    cost_pct=cost_pct,
                )
                if economic_bundle is None:
                    economic_lane_models[lane] = {
                        "status": "insufficient_prior_lane_history"
                    }
                    continue
                event_model, ev_model, boundary_policy, lane_meta = economic_bundle
                lane_current = [
                    row
                    for row in current_economic_candidates
                    if row["pairability_lane"] == lane
                ]
                lane_episodes = [
                    _apply_economic_first_passage_policy(
                        row,
                        target_vol_multiplier=boundary_policy["target_vol_multiplier"],
                        adverse_vol_multiplier=boundary_policy[
                            "adverse_vol_multiplier"
                        ],
                        cost_pct=cost_pct,
                    )
                    for row in lane_current
                ]
                economic_control_candidates.extend(lane_episodes)
                lane_scored = _score_economic_first_passage_episodes(
                    lane_episodes,
                    event_model=event_model,
                    ev_model=ev_model,
                )
                economic_scored_candidates.extend(lane_scored)
                economic_lane_models[lane] = {
                    "status": "evaluated_nested_out_of_sample",
                    "model": lane_meta,
                    "candidate_count": len(lane_current),
                    "selected_candidate_count": sum(
                        bool(row["economic_first_passage_selected"])
                        for row in lane_scored
                    ),
                }
                recovery_bundle = _fit_lane_recovery_aware_model(
                    economic_history,
                    lane=lane,
                    boundary_policy=boundary_policy,
                    cost_pct=cost_pct,
                    trailing_policy_enabled=False,
                )
                if recovery_bundle is None:
                    axis_lane_models[lane] = {
                        "status": "insufficient_prior_recovery_history",
                        "recovery_model": None,
                        "trailing_model": None,
                    }
                    recovery_entry_lane_models[lane] = {
                        "status": "insufficient_prior_recovery_exit_history",
                        "prior_episode_count": len(
                            [
                                row
                                for row in recovery_entry_history
                                if row.get("pairability_lane") == lane
                            ]
                        ),
                    }
                    calibration_lane_models[lane] = {
                        "status": "insufficient_prior_recovery_entry_predictions",
                        "prior_episode_count": len(
                            [
                                row
                                for row in recovery_entry_calibration_history
                                if row.get("pairability_lane") == lane
                            ]
                        ),
                    }
                    timing_lane_models[lane] = {
                        "status": "insufficient_prior_recovery_exit_history"
                    }
                    continue
                recovery_models, recovery_policy, recovery_meta = recovery_bundle
                recovery_fit_dates = [
                    *recovery_meta["fit_dates"],
                    *recovery_meta["validation_dates"],
                ]
                recovery_fit_max_date = max(recovery_fit_dates)
                lane_recovery_episodes: list[dict[str, Any]] = []
                for raw_candidate, baseline_episode in zip(
                    lane_current, lane_scored, strict=True
                ):
                    recovery_episode = _simulate_recovery_aware_candidate(
                        raw_candidate,
                        policy=recovery_policy,
                        cost_pct=cost_pct,
                        recovery_models=recovery_models,
                        force_trailing=False,
                    )
                    recovery_episode.update(
                        {
                            "economic_first_passage_selected": baseline_episode[
                                "economic_first_passage_selected"
                            ],
                            "economic_predicted_cost_adjusted_ev_pct": (
                                baseline_episode["predicted_cost_adjusted_ev_pct"]
                            ),
                            "recovery_entry_label_oos": True,
                            "recovery_entry_label_exit_policy": "recovery_only",
                            "recovery_exit_model_fit_max_date": recovery_fit_max_date,
                        }
                    )
                    lane_recovery_episodes.append(recovery_episode)
                current_recovery_entry_history.extend(lane_recovery_episodes)
                recovery_entry_bundle = _fit_recovery_entry_utility_model(
                    recovery_entry_history,
                    lane=lane,
                )
                if recovery_entry_bundle is None:
                    recovery_entry_lane_models[lane] = {
                        "status": "insufficient_prior_recovery_entry_labels",
                        "prior_episode_count": len(
                            [
                                row
                                for row in recovery_entry_history
                                if row.get("pairability_lane") == lane
                            ]
                        ),
                        "prior_date_count": len(
                            {
                                row["trade_date"]
                                for row in recovery_entry_history
                                if row.get("pairability_lane") == lane
                            }
                        ),
                    }
                    timing_lane_models[lane] = {
                        "status": "insufficient_prior_recovery_entry_labels",
                        "prior_control_episode_count": sum(
                            row.get("pairability_lane") == lane
                            and row.get("entry_timing_arm") == "next_open_control"
                            for row in recovery_entry_timing_history
                        ),
                    }
                    calibration_lane_models[lane] = {
                        "status": "insufficient_prior_recovery_entry_predictions",
                        "prior_episode_count": len(
                            [
                                row
                                for row in recovery_entry_calibration_history
                                if row.get("pairability_lane") == lane
                            ]
                        ),
                    }
                else:
                    recovery_entry_model, recovery_entry_meta = recovery_entry_bundle
                    lane_recovery_scored = _score_recovery_entry_utility_episodes(
                        lane_recovery_episodes,
                        ev_model=recovery_entry_model,
                    )
                    recovery_entry_fit_max_date = max(recovery_entry_meta["fit_dates"])
                    for row in lane_recovery_scored:
                        row.update(
                            {
                                "recovery_entry_prediction_oos": True,
                                "recovery_entry_model_fit_max_date": (
                                    recovery_entry_fit_max_date
                                ),
                            }
                        )
                    current_recovery_entry_calibration_history.extend(
                        lane_recovery_scored
                    )
                    recovery_entry_control_candidates.extend(lane_recovery_episodes)
                    recovery_entry_scored_candidates.extend(lane_recovery_scored)
                    recovery_entry_lane_models[lane] = {
                        "status": "evaluated_nested_out_of_sample",
                        "model": recovery_entry_meta,
                        "candidate_count": len(lane_recovery_episodes),
                        "economic_control_selected_candidate_count": sum(
                            bool(row["economic_first_passage_selected"])
                            for row in lane_recovery_episodes
                        ),
                        "recovery_entry_selected_candidate_count": sum(
                            bool(row["recovery_entry_selected"])
                            for row in lane_recovery_scored
                        ),
                    }
                    selected_timing_pairs = [
                        (raw_candidate, scored_episode)
                        for raw_candidate, scored_episode in zip(
                            lane_current, lane_recovery_scored, strict=True
                        )
                        if scored_episode["recovery_entry_selected"]
                    ]
                    for raw_candidate, scored_episode in selected_timing_pairs:
                        current_recovery_entry_timing_history.extend(
                            _build_recovery_entry_timing_oos_rows(
                                raw_candidate,
                                control_episode=scored_episode,
                                policy=recovery_policy,
                                cost_pct=cost_pct,
                                recovery_models=recovery_models,
                                recovery_fit_max_date=recovery_fit_max_date,
                            )
                        )
                    timing_policy = _fit_recovery_entry_timing_policy(
                        recovery_entry_timing_history,
                        lane=lane,
                    )
                    if (
                        timing_policy is None
                        or timing_policy["status"] != "prior_policy_selected"
                    ):
                        timing_lane_models[lane] = {
                            "status": (
                                "insufficient_prior_timing_history"
                                if timing_policy is None
                                else timing_policy["status"]
                            ),
                            "prior_control_episode_count": sum(
                                row.get("pairability_lane") == lane
                                and row.get("entry_timing_arm") == "next_open_control"
                                for row in recovery_entry_timing_history
                            ),
                            "policy": timing_policy,
                        }
                    else:
                        if (
                            date.fromisoformat(timing_policy["fit_max_date"])
                            >= evaluation_date
                        ):
                            raise ValueError(
                                "entry timing policy must be fitted before evaluation date"
                            )
                        lane_timing_control = [
                            row
                            for row in lane_recovery_scored
                            if row["recovery_entry_selected"]
                        ]
                        lane_timing_selected, lane_timing_capacity = (
                            _evaluate_recovery_entry_timing_policy(
                                lane_current,
                                lane_timing_control,
                                timing_policy=timing_policy,
                                recovery_policy=recovery_policy,
                                cost_pct=cost_pct,
                                recovery_models=recovery_models,
                            )
                        )
                        timing_control_candidates.extend(lane_timing_control)
                        timing_selected_candidates.extend(lane_timing_selected)
                        timing_lane_capacities[lane] = lane_timing_capacity
                        timing_lane_arm_capacities[lane] = {}
                        for arm, arm_policy in timing_policy["arm_policies"].items():
                            lane_arm_selected, lane_arm_capacity = (
                                _evaluate_recovery_entry_timing_policy(
                                    lane_current,
                                    lane_timing_control,
                                    timing_policy={
                                        **timing_policy,
                                        "selected_policy": arm_policy,
                                    },
                                    recovery_policy=recovery_policy,
                                    cost_pct=cost_pct,
                                    recovery_models=recovery_models,
                                )
                            )
                            timing_arm_candidates[arm].extend(lane_arm_selected)
                            timing_lane_arm_capacities[lane][arm] = lane_arm_capacity
                        for raw_candidate, scored_episode in selected_timing_pairs:
                            current_candidate_timing_utility_history.append(
                                _build_candidate_timing_utility_pair(
                                    raw_candidate,
                                    control_episode=scored_episode,
                                    timing_policy=timing_policy,
                                    recovery_policy=recovery_policy,
                                    cost_pct=cost_pct,
                                    recovery_models=recovery_models,
                                    recovery_fit_max_date=recovery_fit_max_date,
                                )
                            )
                        timing_utility_bundle = _fit_candidate_timing_utility_models(
                            candidate_timing_utility_history,
                            lane=lane,
                        )
                        if timing_utility_bundle is not None:
                            (
                                timing_utility_baseline_model,
                                timing_utility_trigger_model,
                                timing_utility_meta,
                            ) = timing_utility_bundle
                            if (
                                date.fromisoformat(
                                    str(timing_utility_meta["fit_max_date"])
                                )
                                >= evaluation_date
                            ):
                                raise ValueError(
                                    "candidate timing utility model must predate "
                                    "evaluation date"
                                )
                            prior_lane_timing_utility_decisions = [
                                decision
                                for prior_evaluation in candidate_timing_utility_evaluations
                                for decision in prior_evaluation["decisions"]
                                if decision.get("pairability_lane") == lane
                            ]
                            (
                                lane_utility_selected,
                                lane_utility_decisions,
                                lane_utility_capacity,
                            ) = _evaluate_candidate_timing_utility(
                                lane_current,
                                lane_timing_control,
                                timing_policy=timing_policy,
                                recovery_policy=recovery_policy,
                                cost_pct=cost_pct,
                                recovery_models=recovery_models,
                                baseline_model=timing_utility_baseline_model,
                                trigger_model=timing_utility_trigger_model,
                                model_fit_max_date=timing_utility_meta["fit_max_date"],
                                prior_enter_now_count=sum(
                                    decision.get("baseline_action") == "enter_now"
                                    for decision in prior_lane_timing_utility_decisions
                                ),
                                prior_wait_count=sum(
                                    decision.get("baseline_action") == "wait"
                                    for decision in prior_lane_timing_utility_decisions
                                ),
                            )
                            timing_utility_control_candidates.extend(
                                lane_timing_control
                            )
                            timing_utility_selected_candidates.extend(
                                lane_utility_selected
                            )
                            timing_utility_decisions.extend(lane_utility_decisions)
                            timing_utility_lane_capacities[lane] = lane_utility_capacity
                            timing_utility_lane_models[lane] = {
                                "status": "evaluated_nested_out_of_sample",
                                "model": timing_utility_meta,
                                "raw_selected_candidate_count": len(
                                    lane_timing_control
                                ),
                                "selected_candidate_count": len(lane_utility_selected),
                            }
                            current_lane_timing_pairs = [
                                pair
                                for pair in current_candidate_timing_utility_history
                                if pair.get("pairability_lane") == lane
                            ]
                            current_trigger_utility_prediction_history.extend(
                                _build_trigger_utility_prediction_rows(
                                    current_lane_timing_pairs,
                                    trigger_model=timing_utility_trigger_model,
                                    model_fit_max_date=timing_utility_meta[
                                        "fit_max_date"
                                    ],
                                )
                            )
                            trigger_calibration = _fit_trigger_utility_calibration(
                                trigger_utility_prediction_history,
                                lane=lane,
                            )
                            if trigger_calibration is not None:
                                if (
                                    date.fromisoformat(
                                        str(trigger_calibration["fit_max_date"])
                                    )
                                    >= evaluation_date
                                ):
                                    raise ValueError(
                                        "trigger utility calibration must predate "
                                        "evaluation date"
                                    )
                                prior_trigger_calibration_decisions = [
                                    decision
                                    for prior_evaluation in trigger_calibration_evaluations
                                    for decision in prior_evaluation["decisions"]
                                    if decision.get("pairability_lane") == lane
                                ]
                                (
                                    lane_trigger_calibrated_selected,
                                    lane_trigger_calibrated_decisions,
                                    lane_trigger_calibrated_capacity,
                                ) = _evaluate_candidate_timing_utility(
                                    lane_current,
                                    lane_timing_control,
                                    timing_policy=timing_policy,
                                    recovery_policy=recovery_policy,
                                    cost_pct=cost_pct,
                                    recovery_models=recovery_models,
                                    baseline_model=timing_utility_baseline_model,
                                    trigger_model=timing_utility_trigger_model,
                                    model_fit_max_date=timing_utility_meta[
                                        "fit_max_date"
                                    ],
                                    prior_enter_now_count=sum(
                                        decision.get("baseline_action") == "enter_now"
                                        for decision in prior_lane_timing_utility_decisions
                                    ),
                                    prior_wait_count=sum(
                                        decision.get("baseline_action") == "wait"
                                        for decision in prior_lane_timing_utility_decisions
                                    ),
                                    trigger_calibration=trigger_calibration,
                                    prior_trigger_enter_count=sum(
                                        decision.get("trigger_action") == "timed_entry"
                                        for decision in prior_trigger_calibration_decisions
                                    ),
                                    prior_trigger_skip_count=sum(
                                        str(
                                            decision.get("trigger_action") or ""
                                        ).startswith("skip_")
                                        for decision in prior_trigger_calibration_decisions
                                    ),
                                )
                                raw_baseline_decisions = [
                                    (
                                        str(decision["source_entry_at"]),
                                        str(decision["baseline_action"]),
                                    )
                                    for decision in lane_utility_decisions
                                ]
                                calibrated_baseline_decisions = [
                                    (
                                        str(decision["source_entry_at"]),
                                        str(decision["baseline_action"]),
                                    )
                                    for decision in lane_trigger_calibrated_decisions
                                ]
                                if (
                                    calibrated_baseline_decisions
                                    != raw_baseline_decisions
                                ):
                                    raise ValueError(
                                        "trigger calibration must preserve baseline "
                                        "timing decisions"
                                    )
                                trigger_calibration_control_candidates.extend(
                                    lane_timing_control
                                )
                                trigger_calibration_raw_gate_candidates.extend(
                                    lane_utility_selected
                                )
                                trigger_calibration_selected_candidates.extend(
                                    lane_trigger_calibrated_selected
                                )
                                trigger_calibration_decisions.extend(
                                    lane_trigger_calibrated_decisions
                                )
                                trigger_calibration_lane_capacities[lane] = (
                                    lane_trigger_calibrated_capacity
                                )
                                trigger_calibration_lane_models[lane] = {
                                    "status": "evaluated_nested_out_of_sample",
                                    "calibration": trigger_calibration,
                                    "raw_gate_selected_candidate_count": len(
                                        lane_utility_selected
                                    ),
                                    "calibrated_selected_candidate_count": len(
                                        lane_trigger_calibrated_selected
                                    ),
                                    "baseline_decision_identity_preserved": True,
                                }
                                wait_budget_policy = _select_wait_budget_policy(
                                    wait_budget_arm_history,
                                    lane=lane,
                                )
                                if wait_budget_policy is not None and (
                                    date.fromisoformat(
                                        str(wait_budget_policy["fit_max_date"])
                                    )
                                    >= evaluation_date
                                ):
                                    raise ValueError(
                                        "wait budget policy must predate evaluation date"
                                    )
                                wait_budget_lane_arm_capacities[lane] = {}
                                lane_wait_budget_results: dict[
                                    str,
                                    tuple[
                                        list[dict[str, Any]],
                                        list[dict[str, Any]],
                                        dict[str, Any],
                                    ],
                                ] = {}
                                for (
                                    wait_budget_arm,
                                    enter_per_wait,
                                ) in WAIT_BUDGET_ARMS.items():
                                    prior_arm_decisions = [
                                        decision
                                        for prior_evaluation in wait_budget_evaluations
                                        for decision in prior_evaluation[
                                            "arm_decisions"
                                        ].get(wait_budget_arm, [])
                                        if decision.get("pairability_lane") == lane
                                    ]
                                    (
                                        prior_budget_decisions,
                                        prior_arm_trigger_decisions,
                                    ) = _wait_budget_prior_decisions(
                                        prior_arm_decisions,
                                        prior_baseline_decisions=(
                                            prior_lane_timing_utility_decisions
                                        ),
                                        prior_trigger_decisions=(
                                            prior_trigger_calibration_decisions
                                        ),
                                    )
                                    arm_result = _evaluate_candidate_timing_utility(
                                        lane_current,
                                        lane_timing_control,
                                        timing_policy=timing_policy,
                                        recovery_policy=recovery_policy,
                                        cost_pct=cost_pct,
                                        recovery_models=recovery_models,
                                        baseline_model=timing_utility_baseline_model,
                                        trigger_model=timing_utility_trigger_model,
                                        model_fit_max_date=timing_utility_meta[
                                            "fit_max_date"
                                        ],
                                        prior_enter_now_count=sum(
                                            decision.get("baseline_action")
                                            == "enter_now"
                                            for decision in prior_budget_decisions
                                        ),
                                        prior_wait_count=sum(
                                            decision.get("baseline_action") == "wait"
                                            for decision in prior_budget_decisions
                                        ),
                                        trigger_calibration=trigger_calibration,
                                        prior_trigger_enter_count=sum(
                                            decision.get("trigger_action")
                                            == "timed_entry"
                                            for decision in prior_arm_trigger_decisions
                                        ),
                                        prior_trigger_skip_count=sum(
                                            str(
                                                decision.get("trigger_action") or ""
                                            ).startswith("skip_")
                                            for decision in prior_arm_trigger_decisions
                                        ),
                                        wait_budget_enter_per_wait=enter_per_wait,
                                        wait_budget_arm=wait_budget_arm,
                                    )
                                    (
                                        arm_selected,
                                        arm_decisions,
                                        arm_capacity,
                                    ) = arm_result
                                    for episode in arm_selected:
                                        episode[
                                            "wait_budget_opportunity_retention_passed"
                                        ] = bool(
                                            arm_capacity["opportunity_retention_passed"]
                                        )
                                    lane_wait_budget_results[wait_budget_arm] = (
                                        arm_selected,
                                        arm_decisions,
                                        arm_capacity,
                                    )
                                    wait_budget_arm_candidates[wait_budget_arm].extend(
                                        arm_selected
                                    )
                                    wait_budget_arm_decisions[wait_budget_arm].extend(
                                        arm_decisions
                                    )
                                    wait_budget_lane_arm_capacities[lane][
                                        wait_budget_arm
                                    ] = arm_capacity
                                fixed_decisions = [
                                    (
                                        str(decision["source_entry_at"]),
                                        str(decision["baseline_action"]),
                                        str(decision.get("trigger_action") or ""),
                                    )
                                    for decision in lane_wait_budget_results[
                                        "enter3_wait1"
                                    ][1]
                                ]
                                calibrated_decisions = [
                                    (
                                        str(decision["source_entry_at"]),
                                        str(decision["baseline_action"]),
                                        str(decision.get("trigger_action") or ""),
                                    )
                                    for decision in lane_trigger_calibrated_decisions
                                ]
                                if fixed_decisions != calibrated_decisions:
                                    raise ValueError(
                                        "fixed 3:1 arm must preserve calibrated v11 "
                                        "decisions"
                                    )
                                if wait_budget_policy is not None:
                                    for episode in lane_wait_budget_results[
                                        str(wait_budget_policy["selected_arm"])
                                    ][0]:
                                        selected_episode = dict(episode)
                                        selected_episode.update(
                                            {
                                                "wait_budget_policy_selected": True,
                                                "wait_budget_policy_fit_max_date": (
                                                    wait_budget_policy["fit_max_date"]
                                                ),
                                            }
                                        )
                                        wait_budget_selected_candidates.append(
                                            selected_episode
                                        )
                                wait_budget_lane_models[lane] = {
                                    "status": "evaluated_oos_arm_comparison",
                                    "trigger_calibration": trigger_calibration,
                                    "prior_selected_policy": wait_budget_policy,
                                    "selected_policy_available": (
                                        wait_budget_policy is not None
                                    ),
                                    "fixed_3_to_1_identity_preserved": True,
                                }
                            else:
                                trigger_calibration_lane_models[lane] = {
                                    "status": (
                                        "insufficient_prior_trigger_prediction_history"
                                    ),
                                    "prior_prediction_count": sum(
                                        row.get("pairability_lane") == lane
                                        for row in trigger_utility_prediction_history
                                    ),
                                    "prior_date_count": len(
                                        {
                                            row["trade_date"]
                                            for row in trigger_utility_prediction_history
                                            if row.get("pairability_lane") == lane
                                        }
                                    ),
                                }
                                wait_budget_lane_models[lane] = {
                                    "status": (
                                        "insufficient_prior_trigger_prediction_history"
                                    )
                                }
                        else:
                            timing_utility_lane_models[lane] = {
                                "status": "insufficient_prior_timing_pair_history",
                                "prior_pair_count": sum(
                                    row.get("pairability_lane") == lane
                                    for row in candidate_timing_utility_history
                                ),
                                "prior_date_count": len(
                                    {
                                        row["trade_date"]
                                        for row in candidate_timing_utility_history
                                        if row.get("pairability_lane") == lane
                                    }
                                ),
                            }
                        timing_lane_models[lane] = {
                            "status": "evaluated_nested_out_of_sample",
                            "policy": timing_policy,
                            "raw_selected_candidate_count": len(lane_timing_control),
                            "timing_selected_candidate_count": len(
                                lane_timing_selected
                            ),
                        }
                    calibration_bundle = _fit_recovery_entry_calibrator(
                        recovery_entry_calibration_history,
                        lane=lane,
                    )
                    if calibration_bundle is None:
                        calibration_lane_models[lane] = {
                            "status": "insufficient_prior_calibration_history",
                            "prior_episode_count": len(
                                [
                                    row
                                    for row in recovery_entry_calibration_history
                                    if row.get("pairability_lane") == lane
                                ]
                            ),
                            "prior_date_count": len(
                                {
                                    row["trade_date"]
                                    for row in recovery_entry_calibration_history
                                    if row.get("pairability_lane") == lane
                                }
                            ),
                        }
                    else:
                        calibration_parameters, calibration_meta = calibration_bundle
                        lane_calibrated = _score_calibrated_recovery_entry_episodes(
                            lane_recovery_scored,
                            parameters=calibration_parameters,
                        )
                        calibration_control_candidates.extend(lane_recovery_scored)
                        calibration_raw_candidates.extend(lane_recovery_scored)
                        calibration_scored_candidates.extend(lane_calibrated)
                        calibration_scored_oos.extend(lane_calibrated)
                        calibration_lane_models[lane] = {
                            "status": "evaluated_nested_out_of_sample",
                            "model": calibration_meta,
                            "candidate_count": len(lane_calibrated),
                            "economic_control_selected_candidate_count": sum(
                                bool(row["economic_first_passage_selected"])
                                for row in lane_recovery_scored
                            ),
                            "raw_recovery_selected_candidate_count": sum(
                                bool(row["recovery_entry_selected"])
                                for row in lane_recovery_scored
                            ),
                            "calibrated_selected_candidate_count": sum(
                                bool(row["calibrated_recovery_entry_selected"])
                                for row in lane_calibrated
                            ),
                        }
                trailing_bundle = _fit_lane_trailing_model(
                    economic_history,
                    lane=lane,
                    boundary_policy=boundary_policy,
                    cost_pct=cost_pct,
                )
                if trailing_bundle is None:
                    axis_lane_models[lane] = {
                        "status": "insufficient_prior_trailing_history",
                        "recovery_model": recovery_meta,
                        "trailing_model": None,
                    }
                    continue
                trailing_models, trailing_multiplier, trailing_meta = trailing_bundle
                axis_policy = {
                    **recovery_policy,
                    "trailing_vol_multiplier": trailing_multiplier,
                }
                axis_lane_models[lane] = {
                    "status": "evaluated_nested_out_of_sample",
                    "recovery_model": recovery_meta,
                    "trailing_model": trailing_meta,
                    "candidate_count": len(lane_current),
                }
                recovery_only_by_entry = {
                    _entry_identity(row): row for row in lane_recovery_episodes
                }
                for raw_candidate, baseline_episode in zip(
                    lane_current, lane_scored, strict=True
                ):
                    recovery_only_episode = recovery_only_by_entry[
                        _entry_identity(baseline_episode)
                    ]
                    arm_episodes = {
                        "recovery_only": dict(recovery_only_episode),
                        "trailing_only": _simulate_recovery_aware_candidate(
                            raw_candidate,
                            policy=axis_policy,
                            cost_pct=cost_pct,
                            force_recovery=False,
                            trailing_models=trailing_models,
                            force_trailing=(False if trailing_models is None else None),
                        ),
                        "recovery_plus_trailing": (
                            _simulate_recovery_aware_candidate(
                                raw_candidate,
                                policy=axis_policy,
                                cost_pct=cost_pct,
                                recovery_models=recovery_models,
                                trailing_models=trailing_models,
                                force_trailing=(
                                    False if trailing_models is None else None
                                ),
                            )
                        ),
                    }
                    entry_key = _entry_identity(baseline_episode)
                    for arm_name, arm_episode in arm_episodes.items():
                        for field in (
                            "predicted_cost_adjusted_ev_pct",
                            "predicted_event_probabilities",
                            "economic_first_passage_selected",
                        ):
                            arm_episode[field] = baseline_episode[field]
                        arm_episode.update(
                            {
                                "axis_arm": arm_name,
                                "baseline_exit_at": baseline_episode["exit_at"],
                                "baseline_exit_price": baseline_episode["exit_price"],
                                "baseline_exit_reason": baseline_episode["exit_reason"],
                                "baseline_economic_first_passage_event": (
                                    baseline_episode["economic_first_passage_event"]
                                ),
                            }
                        )
                        arm_map = axis_candidates_by_entry[arm_name]
                        if entry_key in arm_map:
                            raise ValueError(
                                "duplicate axis candidate entry identity: "
                                + repr((arm_name, entry_key))
                            )
                        arm_map[entry_key] = arm_episode
            if any(
                row["status"] == "evaluated_nested_out_of_sample"
                for row in economic_lane_models.values()
            ):
                economic_control = _non_overlapping_candidates(
                    economic_control_candidates,
                    selected_only=False,
                )
                economic_selected = _non_overlapping_candidates(
                    economic_scored_candidates,
                    selected_only=True,
                    selection_key="economic_first_passage_selected",
                )
                economic_control_trades.extend(economic_control)
                economic_selected_trades.extend(economic_selected)
                economic_status = "evaluated_nested_out_of_sample"
            else:
                economic_control = []
                economic_selected = []
                economic_status = "insufficient_prior_lane_history"
            economic_evaluations.append(
                {
                    "evaluation_date": evaluation_date.isoformat(),
                    "status": economic_status,
                    "lane_models": economic_lane_models,
                    "control_trades": economic_control,
                    "selected_trades": economic_selected,
                }
            )
            recoverable_basin_candidate_evaluations.append(
                {
                    "evaluation_date": evaluation_date.isoformat(),
                    "status": economic_status,
                    "candidate_trades": economic_scored_candidates,
                }
            )
            if any(
                row["status"] == "evaluated_nested_out_of_sample"
                for row in recovery_entry_lane_models.values()
            ):
                recovery_entry_control = _non_overlapping_candidates(
                    recovery_entry_control_candidates,
                    selected_only=True,
                    selection_key="economic_first_passage_selected",
                )
                recovery_entry_selected = _non_overlapping_candidates(
                    recovery_entry_scored_candidates,
                    selected_only=True,
                    selection_key="recovery_entry_selected",
                )
                recovery_entry_control_trades.extend(recovery_entry_control)
                recovery_entry_selected_trades.extend(recovery_entry_selected)
                recovery_entry_status = "evaluated_nested_out_of_sample"
            else:
                recovery_entry_control = []
                recovery_entry_selected = []
                recovery_entry_status = "insufficient_prior_recovery_entry_labels"
            recovery_entry_evaluations.append(
                {
                    "evaluation_date": evaluation_date.isoformat(),
                    "status": recovery_entry_status,
                    "lane_models": recovery_entry_lane_models,
                    "eligible_candidate_count": len(recovery_entry_control_candidates),
                    "economic_control_trades": recovery_entry_control,
                    "recovery_entry_selected_trades": recovery_entry_selected,
                    "shared_exit_policy": "recovery_only",
                }
            )
            if any(
                row["status"] == "evaluated_nested_out_of_sample"
                for row in calibration_lane_models.values()
            ):
                calibration_control = _non_overlapping_candidates(
                    calibration_control_candidates,
                    selected_only=True,
                    selection_key="economic_first_passage_selected",
                )
                calibration_raw_selected = _non_overlapping_candidates(
                    calibration_raw_candidates,
                    selected_only=True,
                    selection_key="recovery_entry_selected",
                )
                calibration_mean_selected = _non_overlapping_candidates(
                    calibration_scored_candidates,
                    selected_only=True,
                    selection_key="calibrated_recovery_entry_mean_selected",
                )
                calibration_selected, calibration_capacity = (
                    _apply_calibration_capacity_floor(
                        calibration_raw_selected,
                        calibration_mean_selected,
                        calibration_scored_candidates,
                    )
                )
                calibration_control_trades.extend(calibration_control)
                calibration_raw_selected_trades.extend(calibration_raw_selected)
                calibration_selected_trades.extend(calibration_selected)
                calibration_status = "evaluated_nested_out_of_sample"
            else:
                calibration_control = []
                calibration_raw_selected = []
                calibration_mean_selected = []
                calibration_selected = []
                calibration_capacity = {
                    "raw_nonoverlap_count": 0,
                    "calibrated_mean_nonoverlap_count": 0,
                    "opportunity_floor_count": 0,
                    "capacity_fallback_applied": False,
                    "final_nonoverlap_count": 0,
                }
                calibration_status = "insufficient_prior_calibration_history"
            calibration_evaluations.append(
                {
                    "evaluation_date": evaluation_date.isoformat(),
                    "status": calibration_status,
                    "lane_models": calibration_lane_models,
                    "eligible_candidate_count": len(calibration_control_candidates),
                    "economic_control_trades": calibration_control,
                    "raw_recovery_entry_trades": calibration_raw_selected,
                    "calibrated_recovery_entry_trades": calibration_selected,
                    "capacity": calibration_capacity,
                    "shared_exit_policy": "recovery_only",
                }
            )
            if any(
                row["status"] == "evaluated_nested_out_of_sample"
                for row in timing_lane_models.values()
            ):
                timing_control = _non_overlapping_candidates(
                    timing_control_candidates,
                    selected_only=True,
                    selection_key="recovery_entry_selected",
                )
                timing_pre_capacity = _non_overlapping_candidates(
                    timing_selected_candidates,
                    selected_only=False,
                )
                timing_floor = (
                    max(
                        1,
                        math.ceil(
                            len(timing_control)
                            * RECOVERY_ENTRY_TIMING_OPPORTUNITY_RETENTION
                        ),
                    )
                    if timing_control
                    else 0
                )
                timing_fallback = bool(
                    timing_control and len(timing_pre_capacity) < timing_floor
                )
                timing_selected = [
                    dict(row)
                    for row in (
                        timing_control if timing_fallback else timing_pre_capacity
                    )
                ]
                if timing_fallback:
                    for row in timing_selected:
                        row.update(
                            {
                                "entry_timing_capacity_fallback_selected": True,
                                "entry_timing_selection_reason": (
                                    "aggregate_raw_recovery_capacity_floor_fallback"
                                ),
                            }
                        )
                timing_capacity = {
                    "raw_nonoverlap_count": len(timing_control),
                    "timed_nonoverlap_count": len(timing_pre_capacity),
                    "opportunity_floor_count": timing_floor,
                    "capacity_fallback_applied": timing_fallback,
                    "final_nonoverlap_count": len(timing_selected),
                    "lane_capacity": timing_lane_capacities,
                }
                current_timing_arms: dict[str, list[dict[str, Any]]] = {}
                arm_capacities: dict[str, dict[str, Any]] = {}
                for arm, arm_candidates in timing_arm_candidates.items():
                    arm_pre_capacity = _non_overlapping_candidates(
                        arm_candidates,
                        selected_only=False,
                    )
                    arm_fallback = bool(
                        timing_control and len(arm_pre_capacity) < timing_floor
                    )
                    arm_selected = [
                        dict(row)
                        for row in (
                            timing_control if arm_fallback else arm_pre_capacity
                        )
                    ]
                    current_timing_arms[arm] = arm_selected
                    recovery_entry_timing_arm_trades[arm].extend(arm_selected)
                    arm_capacities[arm] = {
                        "raw_nonoverlap_count": len(timing_control),
                        "timed_nonoverlap_count": len(arm_pre_capacity),
                        "opportunity_floor_count": timing_floor,
                        "capacity_fallback_applied": arm_fallback,
                        "final_nonoverlap_count": len(arm_selected),
                    }
                recovery_entry_timing_control_trades.extend(timing_control)
                recovery_entry_timing_selected_trades.extend(timing_selected)
                timing_status = "evaluated_nested_out_of_sample"
            else:
                timing_control = []
                timing_selected = []
                timing_capacity = {
                    "raw_nonoverlap_count": 0,
                    "timed_nonoverlap_count": 0,
                    "opportunity_floor_count": 0,
                    "capacity_fallback_applied": False,
                    "final_nonoverlap_count": 0,
                    "lane_capacity": {},
                }
                current_timing_arms = {arm: [] for arm in RECOVERY_ENTRY_TIMING_ARMS}
                arm_capacities = {
                    arm: {
                        "raw_nonoverlap_count": 0,
                        "timed_nonoverlap_count": 0,
                        "opportunity_floor_count": 0,
                        "capacity_fallback_applied": False,
                        "final_nonoverlap_count": 0,
                    }
                    for arm in RECOVERY_ENTRY_TIMING_ARMS
                }
                timing_status = "insufficient_prior_timing_history"
            recovery_entry_timing_evaluations.append(
                {
                    "evaluation_date": evaluation_date.isoformat(),
                    "status": timing_status,
                    "lane_models": timing_lane_models,
                    "raw_recovery_entry_control_trades": timing_control,
                    "prior_selected_timing_trades": timing_selected,
                    "arm_trades": current_timing_arms,
                    "capacity": timing_capacity,
                    "arm_capacities": arm_capacities,
                    "lane_arm_capacities": timing_lane_arm_capacities,
                    "shared_exit_policy": "recovery_only",
                }
            )
            if any(
                row["status"] == "evaluated_nested_out_of_sample"
                for row in timing_utility_lane_models.values()
            ):
                timing_utility_control = _non_overlapping_candidates(
                    timing_utility_control_candidates,
                    selected_only=True,
                    selection_key="recovery_entry_selected",
                )
                timing_utility_selected = _non_overlapping_candidates(
                    timing_utility_selected_candidates,
                    selected_only=False,
                )
                timing_utility_floor = (
                    max(
                        1,
                        math.ceil(
                            len(timing_utility_control)
                            * RECOVERY_ENTRY_TIMING_UTILITY_OPPORTUNITY_RETENTION
                        ),
                    )
                    if timing_utility_control
                    else 0
                )
                timing_utility_capacity = {
                    "raw_nonoverlap_count": len(timing_utility_control),
                    "opportunity_floor_count": timing_utility_floor,
                    "final_nonoverlap_count": len(timing_utility_selected),
                    "opportunity_retention_passed": len(timing_utility_selected)
                    >= timing_utility_floor,
                    "lane_capacity": timing_utility_lane_capacities,
                }
                candidate_timing_utility_control_trades.extend(timing_utility_control)
                candidate_timing_utility_selected_trades.extend(timing_utility_selected)
                timing_utility_status = "evaluated_nested_out_of_sample"
            else:
                timing_utility_control = []
                timing_utility_selected = []
                timing_utility_capacity = {
                    "raw_nonoverlap_count": 0,
                    "opportunity_floor_count": 0,
                    "final_nonoverlap_count": 0,
                    "opportunity_retention_passed": False,
                    "lane_capacity": {},
                }
                timing_utility_status = "insufficient_prior_timing_pair_history"
            candidate_timing_utility_evaluations.append(
                {
                    "evaluation_date": evaluation_date.isoformat(),
                    "status": timing_utility_status,
                    "lane_models": timing_utility_lane_models,
                    "control_trades": timing_utility_control,
                    "selected_trades": timing_utility_selected,
                    "decisions": timing_utility_decisions,
                    "post_oos_outcome_attribution": [
                        {
                            key: pair.get(key)
                            for key in (
                                "trade_date",
                                "venue",
                                "session",
                                "pairability_lane",
                                "source_entry_at",
                                "source_opportunity_id",
                                "timing_arm",
                                "timing_max_wait_minutes",
                                "timing_available",
                                "timing_entry_at",
                                "timing_delay_minutes",
                                "control_net_profit_pct",
                                "timing_net_profit_pct",
                                "timing_incremental_net_profit_pct",
                                "candidate_timing_policy_fit_max_date",
                                "candidate_timing_recovery_fit_max_date",
                            )
                        }
                        for pair in current_candidate_timing_utility_history
                        if pair["source_entry_at"]
                        in {
                            decision["source_entry_at"]
                            for decision in timing_utility_decisions
                        }
                    ],
                    "outcome_attribution_authority": (
                        "post_oos_diagnostic_only_not_same_date_decision_input"
                    ),
                    "capacity": timing_utility_capacity,
                    "shared_exit_policy": "recovery_only",
                    "retroactive_next_open_fallback_used": False,
                }
            )
            if any(
                row["status"] == "evaluated_nested_out_of_sample"
                for row in trigger_calibration_lane_models.values()
            ):
                trigger_calibration_control = _non_overlapping_candidates(
                    trigger_calibration_control_candidates,
                    selected_only=True,
                    selection_key="recovery_entry_selected",
                )
                trigger_calibration_raw_gate = _non_overlapping_candidates(
                    trigger_calibration_raw_gate_candidates,
                    selected_only=False,
                )
                trigger_calibration_selected = _non_overlapping_candidates(
                    trigger_calibration_selected_candidates,
                    selected_only=False,
                )
                trigger_calibration_floor = (
                    max(
                        1,
                        math.ceil(
                            len(trigger_calibration_control)
                            * TRIGGER_UTILITY_CALIBRATION_OPPORTUNITY_RETENTION
                        ),
                    )
                    if trigger_calibration_control
                    else 0
                )
                trigger_calibration_capacity = {
                    "control_nonoverlap_count": len(trigger_calibration_control),
                    "raw_gate_nonoverlap_count": len(trigger_calibration_raw_gate),
                    "calibrated_nonoverlap_count": len(trigger_calibration_selected),
                    "opportunity_floor_count": trigger_calibration_floor,
                    "opportunity_retention_passed": len(trigger_calibration_selected)
                    >= trigger_calibration_floor,
                    "lane_capacity": trigger_calibration_lane_capacities,
                }
                trigger_calibration_control_trades.extend(trigger_calibration_control)
                trigger_calibration_raw_gate_trades.extend(trigger_calibration_raw_gate)
                trigger_calibration_selected_trades.extend(trigger_calibration_selected)
                trigger_calibration_status = "evaluated_nested_out_of_sample"
            else:
                trigger_calibration_control = []
                trigger_calibration_raw_gate = []
                trigger_calibration_selected = []
                trigger_calibration_capacity = {
                    "control_nonoverlap_count": 0,
                    "raw_gate_nonoverlap_count": 0,
                    "calibrated_nonoverlap_count": 0,
                    "opportunity_floor_count": 0,
                    "opportunity_retention_passed": False,
                    "lane_capacity": {},
                }
                trigger_calibration_status = (
                    "insufficient_prior_trigger_prediction_history"
                )
            trigger_calibration_evaluations.append(
                {
                    "evaluation_date": evaluation_date.isoformat(),
                    "status": trigger_calibration_status,
                    "lane_models": trigger_calibration_lane_models,
                    "control_trades": trigger_calibration_control,
                    "raw_trigger_gate_trades": trigger_calibration_raw_gate,
                    "calibrated_trigger_trades": trigger_calibration_selected,
                    "decisions": trigger_calibration_decisions,
                    "post_oos_trigger_prediction_attribution": [
                        row
                        for row in current_trigger_utility_prediction_history
                        if row["source_entry_at"]
                        in {
                            decision["source_entry_at"]
                            for decision in trigger_calibration_decisions
                        }
                    ],
                    "outcome_attribution_authority": (
                        "post_oos_diagnostic_only_not_same_date_calibration_input"
                    ),
                    "capacity": trigger_calibration_capacity,
                    "shared_baseline_wait_policy": True,
                    "shared_exit_policy": "recovery_only",
                    "retroactive_next_open_fallback_used": False,
                }
            )
            if any(
                row["status"] == "evaluated_oos_arm_comparison"
                for row in wait_budget_lane_models.values()
            ):
                current_wait_budget_arms = {
                    arm: _non_overlapping_candidates(
                        candidates,
                        selected_only=False,
                    )
                    for arm, candidates in wait_budget_arm_candidates.items()
                }
                current_wait_budget_selected = _non_overlapping_candidates(
                    wait_budget_selected_candidates,
                    selected_only=False,
                )
                wait_budget_floor = (
                    max(
                        1,
                        math.ceil(
                            len(trigger_calibration_control)
                            * WAIT_BUDGET_OPPORTUNITY_RETENTION
                        ),
                    )
                    if trigger_calibration_control
                    else 0
                )
                wait_budget_arm_capacities = {
                    arm: {
                        "control_nonoverlap_count": len(trigger_calibration_control),
                        "arm_nonoverlap_count": len(arm_trades),
                        "opportunity_floor_count": wait_budget_floor,
                        "opportunity_retention_passed": len(arm_trades)
                        >= wait_budget_floor,
                        "trigger_available_count": sum(
                            int(lane_capacity.get("trigger_available_count") or 0)
                            for lane_capacity in (
                                wait_budget_lane_arm_capacities.get(lane, {}).get(
                                    arm, {}
                                )
                                for lane in wait_budget_lane_arm_capacities
                            )
                        ),
                        "trigger_enter_count": sum(
                            int(lane_capacity.get("trigger_enter_count") or 0)
                            for lane_capacity in (
                                wait_budget_lane_arm_capacities.get(lane, {}).get(
                                    arm, {}
                                )
                                for lane in wait_budget_lane_arm_capacities
                            )
                        ),
                    }
                    for arm, arm_trades in current_wait_budget_arms.items()
                }
                for arm, capacity in wait_budget_arm_capacities.items():
                    trigger_available = int(capacity["trigger_available_count"])
                    trigger_entered = int(capacity["trigger_enter_count"])
                    capacity["trigger_entry_retention"] = (
                        round(trigger_entered / trigger_available, 6)
                        if trigger_available
                        else None
                    )
                    capacity["trigger_retention_passed"] = bool(
                        not trigger_available
                        or trigger_entered
                        >= math.ceil(
                            trigger_available * WAIT_BUDGET_OPPORTUNITY_RETENTION
                        )
                    )
                wait_budget_arm_history.extend(
                    episode
                    for arm_trades in current_wait_budget_arms.values()
                    for episode in arm_trades
                )
                for arm, arm_trades in current_wait_budget_arms.items():
                    wait_budget_arm_trades[arm].extend(arm_trades)
                wait_budget_selected_trades.extend(current_wait_budget_selected)
                wait_budget_status = "evaluated_oos_arm_comparison"
            else:
                current_wait_budget_arms = {arm: [] for arm in WAIT_BUDGET_ARMS}
                current_wait_budget_selected = []
                wait_budget_arm_capacities = {
                    arm: {
                        "control_nonoverlap_count": 0,
                        "arm_nonoverlap_count": 0,
                        "opportunity_floor_count": 0,
                        "opportunity_retention_passed": False,
                        "trigger_available_count": 0,
                        "trigger_enter_count": 0,
                        "trigger_entry_retention": None,
                        "trigger_retention_passed": False,
                    }
                    for arm in WAIT_BUDGET_ARMS
                }
                wait_budget_status = "insufficient_prior_trigger_prediction_history"
            wait_budget_evaluations.append(
                {
                    "evaluation_date": evaluation_date.isoformat(),
                    "status": wait_budget_status,
                    "lane_models": wait_budget_lane_models,
                    "control_trades": trigger_calibration_control,
                    "arm_trades": current_wait_budget_arms,
                    "selected_policy_trades": current_wait_budget_selected,
                    "arm_decisions": wait_budget_arm_decisions,
                    "capacity": {
                        "arms": wait_budget_arm_capacities,
                        "lane_arms": wait_budget_lane_arm_capacities,
                    },
                    "shared_trigger_calibration": True,
                    "shared_trigger_bounded_exploration": True,
                    "shared_exit_policy": "recovery_only",
                    "retroactive_next_open_fallback_used": False,
                }
            )
            if any(
                row["status"] == "evaluated_nested_out_of_sample"
                for row in axis_lane_models.values()
            ):
                current_axis_arms = _same_entry_axis_cohort(
                    economic_selected, axis_candidates_by_entry
                )
                recovery_baseline_selected = current_axis_arms["baseline"]
                recovery_selected = current_axis_arms["recovery_plus_trailing"]
                recovery_baseline_selected_trades.extend(recovery_baseline_selected)
                recovery_selected_trades.extend(recovery_selected)
                for arm_name, arm_trades in current_axis_arms.items():
                    axis_arm_trades[arm_name].extend(arm_trades)
                axis_status = "evaluated_nested_out_of_sample"
            else:
                recovery_baseline_selected = []
                recovery_selected = []
                current_axis_arms = {arm: [] for arm in axis_arm_trades}
                axis_status = "insufficient_prior_axis_history"
            recovery_evaluations.append(
                {
                    "evaluation_date": evaluation_date.isoformat(),
                    "status": axis_status,
                    "baseline_selected_trade_count": len(recovery_baseline_selected),
                    "selected_trade_count": len(recovery_selected),
                    "detail_owner": "recovery_trailing_axis_walk_forward.evaluations",
                    "same_entry_cohort": True,
                }
            )
            axis_evaluations.append(
                {
                    "evaluation_date": evaluation_date.isoformat(),
                    "status": axis_status,
                    "lane_models": axis_lane_models,
                    "arms": current_axis_arms,
                    "same_entry_cohort": True,
                }
            )
            recovery_entry_history.extend(current_recovery_entry_history)
            recovery_entry_calibration_history.extend(
                current_recovery_entry_calibration_history
            )
            recovery_entry_timing_history.extend(current_recovery_entry_timing_history)
            candidate_timing_utility_history.extend(
                current_candidate_timing_utility_history
            )
            trigger_utility_prediction_history.extend(
                current_trigger_utility_prediction_history
            )
            economic_history.extend(current_economic_candidates)
            evaluations.append(
                {
                    "evaluation_date": evaluation_date.isoformat(),
                    "status": "evaluated_out_of_sample",
                    "training_dates": [item.isoformat() for item in train_dates],
                    "buy_model": buy_meta,
                    "sell_model": sell_meta,
                    "holding_policy": hold_cap,
                    "trades": trades,
                }
            )
        sample_floor_passed = base.has_research_sample_floor(available_dates)
        buy_ap = (
            float(average_precision_score(buy_truth, buy_scores))
            if buy_truth and sum(buy_truth) > 0
            else None
        )
        sell_ap = (
            float(average_precision_score(sell_truth, sell_scores))
            if sell_truth and sum(sell_truth) > 0
            else None
        )
        buy_prevalence = sum(buy_truth) / len(buy_truth) if buy_truth else None
        sell_prevalence = sum(sell_truth) / len(sell_truth) if sell_truth else None
        oos_summary = _summary(oos_trades, source_quality_passed=source_quality_passed)
        pairability_control_summary = _summary(
            pairability_control_trades,
            source_quality_passed=source_quality_passed,
        )
        pairability_selected_summary = _summary(
            pairability_selected_trades,
            source_quality_passed=source_quality_passed,
        )
        pairability_decision = _pairability_decision(
            pairability_selected_summary,
            sample_floor_passed=sample_floor_passed,
            source_quality_passed=source_quality_passed,
        )
        competing_control_summary = _summary(
            competing_risk_control_trades,
            source_quality_passed=source_quality_passed,
        )
        competing_selected_summary = _summary(
            competing_risk_selected_trades,
            source_quality_passed=source_quality_passed,
        )
        competing_decision = _competing_risk_decision(
            competing_selected_summary,
            competing_control_summary,
            sample_floor_passed=sample_floor_passed,
            source_quality_passed=source_quality_passed,
        )
        economic_control_summary = _summary(
            economic_control_trades,
            source_quality_passed=source_quality_passed,
        )
        economic_selected_summary = _summary(
            economic_selected_trades,
            source_quality_passed=source_quality_passed,
        )
        economic_decision = _economic_first_passage_decision(
            economic_selected_summary,
            economic_control_summary,
            sample_floor_passed=sample_floor_passed,
            source_quality_passed=source_quality_passed,
        )
        recovery_baseline_summary = _summary(
            recovery_baseline_selected_trades,
            source_quality_passed=source_quality_passed,
        )
        recovery_selected_summary = _summary(
            recovery_selected_trades,
            source_quality_passed=source_quality_passed,
        )
        recovery_decision = _recovery_aware_decision(
            recovery_selected_summary,
            recovery_baseline_summary,
            sample_floor_passed=sample_floor_passed,
            source_quality_passed=source_quality_passed,
        )
        axis_arm_summaries = {
            arm_name: _summary(
                arm_trades,
                source_quality_passed=source_quality_passed,
            )
            for arm_name, arm_trades in axis_arm_trades.items()
        }
        axis_delta_summaries = {
            arm_name: _paired_axis_delta_summary(
                axis_arm_trades["baseline"], arm_trades
            )
            for arm_name, arm_trades in axis_arm_trades.items()
            if arm_name != "baseline"
        }
        axis_decision = _axis_separation_decision(
            axis_arm_summaries,
            sample_floor_passed=sample_floor_passed,
            source_quality_passed=source_quality_passed,
        )
        recovery_entry_control_summary = _summary(
            recovery_entry_control_trades,
            source_quality_passed=source_quality_passed,
        )
        recovery_entry_selected_summary = _summary(
            recovery_entry_selected_trades,
            source_quality_passed=source_quality_passed,
        )
        recovery_entry_decision = _recovery_entry_utility_decision(
            recovery_entry_selected_summary,
            recovery_entry_control_summary,
            sample_floor_passed=sample_floor_passed,
            source_quality_passed=source_quality_passed,
        )
        calibration_control_summary = _summary(
            calibration_control_trades,
            source_quality_passed=source_quality_passed,
        )
        calibration_raw_summary = _summary(
            calibration_raw_selected_trades,
            source_quality_passed=source_quality_passed,
        )
        calibration_selected_summary = _summary(
            calibration_selected_trades,
            source_quality_passed=source_quality_passed,
        )
        calibration_control_path = _recovery_path_diagnostics(
            calibration_control_trades
        )
        calibration_raw_path = _recovery_path_diagnostics(
            calibration_raw_selected_trades
        )
        calibration_selected_path = _recovery_path_diagnostics(
            calibration_selected_trades
        )
        calibration_evaluation_count = sum(
            row["status"] == "evaluated_nested_out_of_sample"
            for row in calibration_evaluations
        )
        calibration_decision = _calibrated_recovery_entry_decision(
            calibration_selected_summary,
            calibration_raw_summary,
            calibration_control_summary,
            calibrated_path=calibration_selected_path,
            raw_path=calibration_raw_path,
            control_path=calibration_control_path,
            evaluation_count=calibration_evaluation_count,
            sample_floor_passed=sample_floor_passed,
            source_quality_passed=source_quality_passed,
        )
        timing_control_summary = _summary(
            recovery_entry_timing_control_trades,
            source_quality_passed=source_quality_passed,
        )
        timing_selected_summary = _summary(
            recovery_entry_timing_selected_trades,
            source_quality_passed=source_quality_passed,
        )
        timing_control_path = _recovery_path_diagnostics(
            recovery_entry_timing_control_trades
        )
        timing_selected_path = _recovery_path_diagnostics(
            recovery_entry_timing_selected_trades
        )
        timing_arm_summaries = {
            arm: _summary(trades, source_quality_passed=source_quality_passed)
            for arm, trades in recovery_entry_timing_arm_trades.items()
        }
        timing_arm_path_diagnostics = {
            arm: _recovery_path_diagnostics(trades)
            for arm, trades in recovery_entry_timing_arm_trades.items()
        }
        timing_evaluation_count = sum(
            row["status"] == "evaluated_nested_out_of_sample"
            for row in recovery_entry_timing_evaluations
        )
        timing_decision = _recovery_entry_timing_decision(
            timing_selected_summary,
            timing_control_summary,
            timing_path=timing_selected_path,
            control_path=timing_control_path,
            evaluation_count=timing_evaluation_count,
            sample_floor_passed=sample_floor_passed,
            source_quality_passed=source_quality_passed,
        )
        evaluated_timing_rows = [
            row
            for row in recovery_entry_timing_evaluations
            if row["status"] == "evaluated_nested_out_of_sample"
        ]
        timing_missed_records = [
            lane
            for row in evaluated_timing_rows
            for lane in row["capacity"]["lane_capacity"].values()
            if int(lane["missed_entry_count"]) > 0
        ]
        timing_missed_count = sum(
            int(row["missed_entry_count"]) for row in timing_missed_records
        )
        timing_fallback_evaluation_count = sum(
            bool(row["capacity"]["capacity_fallback_applied"])
            or any(
                bool(lane["capacity_fallback_applied"])
                for lane in row["capacity"]["lane_capacity"].values()
            )
            for row in evaluated_timing_rows
        )
        timing_utility_control_summary = _summary(
            candidate_timing_utility_control_trades,
            source_quality_passed=source_quality_passed,
        )
        timing_utility_selected_summary = _summary(
            candidate_timing_utility_selected_trades,
            source_quality_passed=source_quality_passed,
        )
        timing_utility_control_path = _recovery_path_diagnostics(
            candidate_timing_utility_control_trades
        )
        timing_utility_selected_path = _recovery_path_diagnostics(
            candidate_timing_utility_selected_trades
        )
        timing_utility_evaluation_count = sum(
            row["status"] == "evaluated_nested_out_of_sample"
            for row in candidate_timing_utility_evaluations
        )
        timing_utility_decision = _candidate_timing_utility_decision(
            timing_utility_selected_summary,
            timing_utility_control_summary,
            selected_path=timing_utility_selected_path,
            control_path=timing_utility_control_path,
            evaluation_count=timing_utility_evaluation_count,
            sample_floor_passed=sample_floor_passed,
            source_quality_passed=source_quality_passed,
        )
        evaluated_timing_utility_rows = [
            row
            for row in candidate_timing_utility_evaluations
            if row["status"] == "evaluated_nested_out_of_sample"
        ]
        trigger_calibration_control_summary = _summary(
            trigger_calibration_control_trades,
            source_quality_passed=source_quality_passed,
        )
        trigger_calibration_raw_gate_summary = _summary(
            trigger_calibration_raw_gate_trades,
            source_quality_passed=source_quality_passed,
        )
        trigger_calibration_selected_summary = _summary(
            trigger_calibration_selected_trades,
            source_quality_passed=source_quality_passed,
        )
        trigger_calibration_control_path = _recovery_path_diagnostics(
            trigger_calibration_control_trades
        )
        trigger_calibration_raw_gate_path = _recovery_path_diagnostics(
            trigger_calibration_raw_gate_trades
        )
        trigger_calibration_selected_path = _recovery_path_diagnostics(
            trigger_calibration_selected_trades
        )
        trigger_calibration_evaluation_count = sum(
            row["status"] == "evaluated_nested_out_of_sample"
            for row in trigger_calibration_evaluations
        )
        trigger_calibration_decision = _trigger_utility_calibration_decision(
            trigger_calibration_selected_summary,
            trigger_calibration_raw_gate_summary,
            trigger_calibration_control_summary,
            calibrated_path=trigger_calibration_selected_path,
            raw_gate_path=trigger_calibration_raw_gate_path,
            control_path=trigger_calibration_control_path,
            evaluation_count=trigger_calibration_evaluation_count,
            sample_floor_passed=sample_floor_passed,
            source_quality_passed=source_quality_passed,
        )
        evaluated_trigger_calibration_rows = [
            row
            for row in trigger_calibration_evaluations
            if row["status"] == "evaluated_nested_out_of_sample"
        ]
        wait_budget_arm_summaries = {
            arm: _summary(trades, source_quality_passed=source_quality_passed)
            for arm, trades in wait_budget_arm_trades.items()
        }
        wait_budget_arm_paths = {
            arm: _recovery_path_diagnostics(trades)
            for arm, trades in wait_budget_arm_trades.items()
        }
        wait_budget_selected_summary = _summary(
            wait_budget_selected_trades,
            source_quality_passed=source_quality_passed,
        )
        wait_budget_selected_path = _recovery_path_diagnostics(
            wait_budget_selected_trades
        )
        wait_budget_arm_evaluation_count = sum(
            row["status"] == "evaluated_oos_arm_comparison"
            for row in wait_budget_evaluations
        )
        wait_budget_selected_policy_evaluation_count = sum(
            row["status"] == "evaluated_oos_arm_comparison"
            and any(
                bool(lane.get("selected_policy_available"))
                for lane in row["lane_models"].values()
            )
            for row in wait_budget_evaluations
        )
        wait_budget_decision = _wait_budget_decision(
            wait_budget_selected_summary,
            wait_budget_arm_summaries["enter3_wait1"],
            selected_path=wait_budget_selected_path,
            fixed_path=wait_budget_arm_paths["enter3_wait1"],
            arm_evaluation_count=wait_budget_arm_evaluation_count,
            selected_policy_evaluation_count=(
                wait_budget_selected_policy_evaluation_count
            ),
            sample_floor_passed=sample_floor_passed,
            source_quality_passed=source_quality_passed,
        )
        evaluated_wait_budget_rows = [
            row
            for row in wait_budget_evaluations
            if row["status"] == "evaluated_oos_arm_comparison"
        ]
        fixed_tp_split = _fixed_tp_split_walk_forward(
            economic_evaluations,
            qualified_series_by_key,
            venue=venue,
            cost_pct=cost_pct,
            sample_floor_passed=sample_floor_passed,
            source_quality_passed=source_quality_passed,
        )
        fixed_tp_equal_share_carry = _fixed_tp_equal_share_carry_replay(
            economic_evaluations,
            qualified_series_by_key,
            venue=venue,
            cost_pct=cost_pct,
            sample_floor_passed=sample_floor_passed,
            source_quality_passed=source_quality_passed,
        )
        fixed_tp_entry_quality = _fixed_tp_split_entry_quality_walk_forward(
            fixed_tp_split["evaluations"],
            sample_floor_passed=sample_floor_passed,
            source_quality_passed=source_quality_passed,
        )
        recoverable_basin = _recoverable_basin_walk_forward(
            recoverable_basin_candidate_evaluations,
            fixed_tp_split["evaluations"],
            qualified_series_by_key,
            venue=venue,
            cost_pct=cost_pct,
            sample_floor_passed=sample_floor_passed,
            source_quality_passed=source_quality_passed,
        )
        parent_bucket = _parent_bucket_walk_forward(
            recoverable_basin_candidate_evaluations,
            fixed_tp_split["evaluations"],
            qualified_series_by_key,
            venue=venue,
            cost_pct=cost_pct,
            sample_floor_passed=sample_floor_passed,
            source_quality_passed=source_quality_passed,
        )
        parent_bucket_stability = _parent_bucket_conflict_stability(
            parent_bucket,
            source_quality_passed=source_quality_passed,
        )
        parent_catastrophic_episode_audit = _parent_catastrophic_episode_audit(
            parent_bucket,
            recoverable_basin_candidate_evaluations,
            qualified_series_by_key,
            venue=venue,
            source_quality_passed=source_quality_passed,
        )
        parent_catastrophic_stop_recovery = _parent_catastrophic_stop_recovery_path(
            parent_bucket,
            recoverable_basin_candidate_evaluations,
            qualified_series_by_key,
            venue=venue,
            cost_pct=cost_pct,
            source_quality_passed=source_quality_passed,
        )
        parent_post_stop_bounded_grace = _parent_post_stop_bounded_grace_arms(
            parent_catastrophic_stop_recovery,
            qualified_series_by_key,
            venue=venue,
            source_quality_passed=source_quality_passed,
        )
        parent_post_stop_grace_prospective = _parent_post_stop_grace_prospective_oos(
            parent_post_stop_bounded_grace,
            venue=venue,
            source_quality_passed=source_quality_passed,
        )
        predictive_structure_found = bool(
            buy_ap is not None
            and sell_ap is not None
            and buy_prevalence
            and sell_prevalence
            and buy_ap > buy_prevalence
            and sell_ap > sell_prevalence
        )
        execution_positive = bool(
            oos_summary["equal_weight_avg_profit_pct"] is not None
            and oos_summary["equal_weight_avg_profit_pct"] > 0
        )
        if predictive_structure_found and not execution_positive:
            evidence_state = "predictive_structure_found_execution_policy_unprofitable"
        elif predictive_structure_found and execution_positive:
            evidence_state = "predictive_structure_and_positive_execution_observed"
        else:
            evidence_state = "common_predictive_structure_not_confirmed"
        cohorts[venue] = {
            "source_quality": "PASS" if source_quality_passed else "PARTIAL_CONTEXT",
            "source_quality_detail": {
                "stock_passed": stock_source_quality.get("venue_status", {}).get(venue)
                == "PASS",
                "kospi_backfill_passed": kospi_source_quality.get("status") == "PASS",
                "exact_context_complete": exact_context_complete,
                "nxt_pre_after_instrument_only": venue == "NXT",
            },
            "available_trading_dates": [item.isoformat() for item in available_dates],
            "sample_floor_passed": sample_floor_passed,
            "oracle_upper_bound": oracle[venue],
            "walk_forward": {
                "evaluation_count": sum(
                    row["status"] == "evaluated_out_of_sample" for row in evaluations
                ),
                "buy_average_precision": (
                    round(buy_ap, 6) if buy_ap is not None else None
                ),
                "sell_average_precision": (
                    round(sell_ap, 6) if sell_ap is not None else None
                ),
                "buy_oracle_prevalence_pct": (
                    round(buy_prevalence * 100.0, 6)
                    if buy_prevalence is not None
                    else None
                ),
                "sell_oracle_prevalence_pct": (
                    round(sell_prevalence * 100.0, 6)
                    if sell_prevalence is not None
                    else None
                ),
                "buy_precision_lift_vs_prevalence": (
                    round(buy_ap / buy_prevalence, 6)
                    if buy_ap is not None and buy_prevalence
                    else None
                ),
                "sell_precision_lift_vs_prevalence": (
                    round(sell_ap / sell_prevalence, 6)
                    if sell_ap is not None and sell_prevalence
                    else None
                ),
                "out_of_sample_summary": oos_summary,
                "confidence_diagnostics": _confidence_diagnostics(oos_trades),
                "trades": oos_trades,
                "evaluations": evaluations,
            },
            "pairability_walk_forward": {
                "contract": PAIRABILITY_CONTRACT,
                "feature_names": PAIRABILITY_FEATURE_NAMES,
                "evaluation_count": sum(
                    row["status"] == "evaluated_nested_out_of_sample"
                    for row in pairability_evaluations
                ),
                "control_summary_same_dates": pairability_control_summary,
                "selected_summary": pairability_selected_summary,
                "selected_lane_summaries": _pairability_lane_summaries(
                    pairability_selected_trades,
                    source_quality_passed=source_quality_passed,
                ),
                "evaluations": pairability_evaluations,
                "decision": pairability_decision,
            },
            "lane_competing_risk_walk_forward": {
                "contract": COMPETING_RISK_CONTRACT,
                "evaluation_count": sum(
                    row["status"] == "evaluated_nested_out_of_sample"
                    for row in competing_risk_evaluations
                ),
                "control_summary_same_dates": competing_control_summary,
                "selected_summary": competing_selected_summary,
                "selected_lane_summaries": _pairability_lane_summaries(
                    competing_risk_selected_trades,
                    source_quality_passed=source_quality_passed,
                ),
                "history_event_counts": dict(
                    sorted(
                        Counter(
                            row["first_event"] for row in competing_risk_history
                        ).items()
                    )
                ),
                "evaluations": competing_risk_evaluations,
                "decision": competing_decision,
            },
            "economic_first_passage_walk_forward": {
                "contract": ECONOMIC_FIRST_PASSAGE_CONTRACT,
                "feature_names": ECONOMIC_FEATURE_NAMES,
                "evaluation_count": sum(
                    row["status"] == "evaluated_nested_out_of_sample"
                    for row in economic_evaluations
                ),
                "control_summary_same_dates": economic_control_summary,
                "selected_summary": economic_selected_summary,
                "selected_lane_summaries": _pairability_lane_summaries(
                    economic_selected_trades,
                    source_quality_passed=source_quality_passed,
                ),
                "control_path_diagnostics": _economic_path_diagnostics(
                    economic_control_trades
                ),
                "selected_path_diagnostics": _economic_path_diagnostics(
                    economic_selected_trades
                ),
                "evaluations": economic_evaluations,
                "decision": economic_decision,
            },
            "recovery_aware_exit_walk_forward": {
                "contract": RECOVERY_AWARE_CONTRACT,
                "feature_names": RECOVERY_FEATURE_NAMES,
                "evaluation_count": sum(
                    row["status"] == "evaluated_nested_out_of_sample"
                    for row in recovery_evaluations
                ),
                "baseline_selected_summary_same_entries": recovery_baseline_summary,
                "selected_summary": recovery_selected_summary,
                "selected_lane_summaries": _pairability_lane_summaries(
                    recovery_selected_trades,
                    source_quality_passed=source_quality_passed,
                ),
                "baseline_path_diagnostics": _economic_path_diagnostics(
                    recovery_baseline_selected_trades
                ),
                "selected_path_diagnostics": _recovery_path_diagnostics(
                    recovery_selected_trades
                ),
                "evaluations": recovery_evaluations,
                "decision": recovery_decision,
            },
            "recovery_trailing_axis_walk_forward": {
                "contract": RECOVERY_TRAILING_AXIS_CONTRACT,
                "recovery_feature_names": RECOVERY_FEATURE_NAMES,
                "trailing_feature_names": TRAILING_FEATURE_NAMES,
                "evaluation_count": sum(
                    row["status"] == "evaluated_nested_out_of_sample"
                    for row in axis_evaluations
                ),
                "arm_summaries": axis_arm_summaries,
                "paired_delta_summaries": axis_delta_summaries,
                "arm_lane_summaries": {
                    arm_name: _pairability_lane_summaries(
                        arm_trades,
                        source_quality_passed=source_quality_passed,
                    )
                    for arm_name, arm_trades in axis_arm_trades.items()
                },
                "arm_path_diagnostics": {
                    "baseline": _economic_path_diagnostics(axis_arm_trades["baseline"]),
                    **{
                        arm_name: _recovery_path_diagnostics(arm_trades)
                        for arm_name, arm_trades in axis_arm_trades.items()
                        if arm_name != "baseline"
                    },
                },
                "evaluations": axis_evaluations,
                "decision": axis_decision,
            },
            "recovery_entry_utility_walk_forward": {
                "contract": RECOVERY_ENTRY_UTILITY_CONTRACT,
                "feature_names": RECOVERY_ENTRY_UTILITY_FEATURE_NAMES,
                "evaluation_count": sum(
                    row["status"] == "evaluated_nested_out_of_sample"
                    for row in recovery_entry_evaluations
                ),
                "eligible_candidate_count": sum(
                    int(row["eligible_candidate_count"])
                    for row in recovery_entry_evaluations
                    if row["status"] == "evaluated_nested_out_of_sample"
                ),
                "economic_control_raw_selected_candidate_count": sum(
                    int(lane_row["economic_control_selected_candidate_count"])
                    for row in recovery_entry_evaluations
                    if row["status"] == "evaluated_nested_out_of_sample"
                    for lane_row in row["lane_models"].values()
                    if lane_row["status"] == "evaluated_nested_out_of_sample"
                ),
                "recovery_entry_raw_selected_candidate_count": sum(
                    int(lane_row["recovery_entry_selected_candidate_count"])
                    for row in recovery_entry_evaluations
                    if row["status"] == "evaluated_nested_out_of_sample"
                    for lane_row in row["lane_models"].values()
                    if lane_row["status"] == "evaluated_nested_out_of_sample"
                ),
                "history_oos_recovery_episode_count": len(recovery_entry_history),
                "control_summary_same_dates_and_exit_policy": (
                    recovery_entry_control_summary
                ),
                "selected_summary": recovery_entry_selected_summary,
                "control_lane_summaries": _pairability_lane_summaries(
                    recovery_entry_control_trades,
                    source_quality_passed=source_quality_passed,
                ),
                "selected_lane_summaries": _pairability_lane_summaries(
                    recovery_entry_selected_trades,
                    source_quality_passed=source_quality_passed,
                ),
                "control_path_diagnostics": _recovery_path_diagnostics(
                    recovery_entry_control_trades
                ),
                "selected_path_diagnostics": _recovery_path_diagnostics(
                    recovery_entry_selected_trades
                ),
                "evaluations": recovery_entry_evaluations,
                "decision": recovery_entry_decision,
            },
            "recovery_entry_calibration_walk_forward": {
                "contract": RECOVERY_ENTRY_CALIBRATION_CONTRACT,
                "evaluation_count": calibration_evaluation_count,
                "eligible_candidate_count": sum(
                    int(row["eligible_candidate_count"])
                    for row in calibration_evaluations
                    if row["status"] == "evaluated_nested_out_of_sample"
                ),
                "history_oos_prediction_count": len(recovery_entry_calibration_history),
                "economic_control_summary_same_dates_and_exit_policy": (
                    calibration_control_summary
                ),
                "raw_recovery_entry_summary_same_dates": calibration_raw_summary,
                "calibrated_selected_summary": calibration_selected_summary,
                "lane_summaries": {
                    "economic_control": _pairability_lane_summaries(
                        calibration_control_trades,
                        source_quality_passed=source_quality_passed,
                    ),
                    "raw_recovery_entry": _pairability_lane_summaries(
                        calibration_raw_selected_trades,
                        source_quality_passed=source_quality_passed,
                    ),
                    "calibrated_recovery_entry": _pairability_lane_summaries(
                        calibration_selected_trades,
                        source_quality_passed=source_quality_passed,
                    ),
                },
                "path_diagnostics": {
                    "economic_control": calibration_control_path,
                    "raw_recovery_entry": calibration_raw_path,
                    "calibrated_recovery_entry": calibration_selected_path,
                },
                "capacity_diagnostics": {
                    "economic_control_raw_selected_candidate_count": sum(
                        int(lane_row["economic_control_selected_candidate_count"])
                        for row in calibration_evaluations
                        if row["status"] == "evaluated_nested_out_of_sample"
                        for lane_row in row["lane_models"].values()
                        if lane_row["status"] == "evaluated_nested_out_of_sample"
                    ),
                    "raw_recovery_selected_candidate_count": sum(
                        int(lane_row["raw_recovery_selected_candidate_count"])
                        for row in calibration_evaluations
                        if row["status"] == "evaluated_nested_out_of_sample"
                        for lane_row in row["lane_models"].values()
                        if lane_row["status"] == "evaluated_nested_out_of_sample"
                    ),
                    "calibrated_mean_positive_candidate_count": sum(
                        int(lane_row["calibrated_selected_candidate_count"])
                        for row in calibration_evaluations
                        if row["status"] == "evaluated_nested_out_of_sample"
                        for lane_row in row["lane_models"].values()
                        if lane_row["status"] == "evaluated_nested_out_of_sample"
                    ),
                    "calibrated_mean_nonoverlap_count": sum(
                        int(row["capacity"]["calibrated_mean_nonoverlap_count"])
                        for row in calibration_evaluations
                        if row["status"] == "evaluated_nested_out_of_sample"
                    ),
                    "capacity_fallback_evaluation_count": sum(
                        bool(row["capacity"]["capacity_fallback_applied"])
                        for row in calibration_evaluations
                        if row["status"] == "evaluated_nested_out_of_sample"
                    ),
                    "economic_control_nonoverlap_count": int(
                        calibration_control_summary.get("sample_count") or 0
                    ),
                    "raw_recovery_nonoverlap_count": int(
                        calibration_raw_summary.get("sample_count") or 0
                    ),
                    "calibrated_nonoverlap_count": int(
                        calibration_selected_summary.get("sample_count") or 0
                    ),
                    "required_opportunity_retention": (
                        RECOVERY_ENTRY_CALIBRATION_OPPORTUNITY_RETENTION
                    ),
                    "calibrated_vs_raw_nonoverlap_retention": (
                        round(
                            int(calibration_selected_summary.get("sample_count") or 0)
                            / int(calibration_raw_summary["sample_count"]),
                            6,
                        )
                        if calibration_raw_summary.get("sample_count")
                        else None
                    ),
                },
                "raw_prediction_diagnostics": _prediction_calibration_diagnostics(
                    calibration_scored_oos,
                    prediction_key="predicted_recovery_entry_ev_pct",
                ),
                "calibrated_prediction_diagnostics": (
                    _prediction_calibration_diagnostics(
                        calibration_scored_oos,
                        prediction_key="calibrated_recovery_entry_ev_pct",
                    )
                ),
                "evaluations": calibration_evaluations,
                "decision": calibration_decision,
            },
            "recovery_entry_timing_walk_forward": {
                "contract": RECOVERY_ENTRY_TIMING_CONTRACT,
                "evaluation_count": timing_evaluation_count,
                "history_oos_row_count": len(recovery_entry_timing_history),
                "history_oos_control_episode_count": sum(
                    row.get("entry_timing_arm") == "next_open_control"
                    for row in recovery_entry_timing_history
                ),
                "raw_recovery_entry_control_summary_same_dates": (
                    timing_control_summary
                ),
                "prior_selected_timing_summary": timing_selected_summary,
                "path_diagnostics": {
                    "raw_next_open_control": timing_control_path,
                    "prior_selected_timing": timing_selected_path,
                },
                "arm_summaries": timing_arm_summaries,
                "arm_path_diagnostics": timing_arm_path_diagnostics,
                "capacity_diagnostics": {
                    "required_opportunity_retention": (
                        RECOVERY_ENTRY_TIMING_OPPORTUNITY_RETENTION
                    ),
                    "raw_nonoverlap_count": int(
                        timing_control_summary.get("sample_count") or 0
                    ),
                    "timing_nonoverlap_count": int(
                        timing_selected_summary.get("sample_count") or 0
                    ),
                    "timing_vs_raw_nonoverlap_retention": (
                        round(
                            int(timing_selected_summary.get("sample_count") or 0)
                            / int(timing_control_summary["sample_count"]),
                            6,
                        )
                        if timing_control_summary.get("sample_count")
                        else None
                    ),
                    "capacity_fallback_evaluation_count": (
                        timing_fallback_evaluation_count
                    ),
                    "missed_entry_count": timing_missed_count,
                    "missed_entry_avg_post_control_mfe_pct": (
                        round(
                            sum(
                                float(row["missed_entry_avg_post_control_mfe_pct"])
                                * int(row["missed_entry_count"])
                                for row in timing_missed_records
                            )
                            / timing_missed_count,
                            6,
                        )
                        if timing_missed_count
                        else None
                    ),
                    "missed_entry_max_post_control_mfe_pct": (
                        max(
                            float(row["missed_entry_max_post_control_mfe_pct"])
                            for row in timing_missed_records
                        )
                        if timing_missed_records
                        else None
                    ),
                    "arm_capacity_fallback_evaluation_counts": {
                        arm: sum(
                            bool(
                                row["arm_capacities"][arm]["capacity_fallback_applied"]
                            )
                            or any(
                                bool(
                                    lane_arms.get(arm, {}).get(
                                        "capacity_fallback_applied", False
                                    )
                                )
                                for lane_arms in row["lane_arm_capacities"].values()
                            )
                            for row in evaluated_timing_rows
                        )
                        for arm in RECOVERY_ENTRY_TIMING_ARMS
                    },
                },
                "evaluations": recovery_entry_timing_evaluations,
                "decision": timing_decision,
            },
            "candidate_timing_utility_walk_forward": {
                "contract": RECOVERY_ENTRY_TIMING_UTILITY_CONTRACT,
                "baseline_feature_names": (
                    RECOVERY_ENTRY_TIMING_UTILITY_BASE_FEATURE_NAMES
                ),
                "trigger_feature_names": (
                    RECOVERY_ENTRY_TIMING_UTILITY_TRIGGER_FEATURE_NAMES
                ),
                "evaluation_count": timing_utility_evaluation_count,
                "history_oos_pair_count": len(candidate_timing_utility_history),
                "history_oos_trigger_pair_count": sum(
                    bool(row.get("timing_available"))
                    for row in candidate_timing_utility_history
                ),
                "control_summary_same_dates": timing_utility_control_summary,
                "selected_summary": timing_utility_selected_summary,
                "path_diagnostics": {
                    "enter_now_control": timing_utility_control_path,
                    "candidate_timing_utility": timing_utility_selected_path,
                },
                "capacity_diagnostics": {
                    "required_opportunity_retention": (
                        RECOVERY_ENTRY_TIMING_UTILITY_OPPORTUNITY_RETENTION
                    ),
                    "control_nonoverlap_count": int(
                        timing_utility_control_summary.get("sample_count") or 0
                    ),
                    "selected_nonoverlap_count": int(
                        timing_utility_selected_summary.get("sample_count") or 0
                    ),
                    "selected_vs_control_nonoverlap_retention": (
                        round(
                            int(
                                timing_utility_selected_summary.get("sample_count") or 0
                            )
                            / int(timing_utility_control_summary["sample_count"]),
                            6,
                        )
                        if timing_utility_control_summary.get("sample_count")
                        else None
                    ),
                    "retention_breach_evaluation_count": sum(
                        not bool(row["capacity"]["opportunity_retention_passed"])
                        for row in evaluated_timing_utility_rows
                    ),
                    **{
                        key: sum(
                            int(lane.get(key) or 0)
                            for row in evaluated_timing_utility_rows
                            for lane in row["capacity"]["lane_capacity"].values()
                        )
                        for key in (
                            "enter_now_decision_count",
                            "wait_decision_count",
                            "trigger_available_count",
                            "trigger_enter_count",
                            "trigger_skip_or_missing_count",
                        )
                    },
                    "retroactive_next_open_fallback_count": sum(
                        bool(row["retroactive_next_open_fallback_used"])
                        for row in evaluated_timing_utility_rows
                    ),
                },
                "evaluations": candidate_timing_utility_evaluations,
                "decision": timing_utility_decision,
            },
            "trigger_utility_calibration_walk_forward": {
                "contract": TRIGGER_UTILITY_CALIBRATION_CONTRACT,
                "evaluation_count": trigger_calibration_evaluation_count,
                "history_oos_prediction_count": len(trigger_utility_prediction_history),
                "history_oos_date_count": len(
                    {row["trade_date"] for row in trigger_utility_prediction_history}
                ),
                "control_summary_same_dates": (trigger_calibration_control_summary),
                "raw_trigger_gate_summary_same_dates": (
                    trigger_calibration_raw_gate_summary
                ),
                "calibrated_trigger_summary": (trigger_calibration_selected_summary),
                "path_diagnostics": {
                    "enter_now_control": trigger_calibration_control_path,
                    "raw_trigger_gate": trigger_calibration_raw_gate_path,
                    "calibrated_bounded_trigger": (trigger_calibration_selected_path),
                },
                "capacity_diagnostics": {
                    "required_opportunity_retention": (
                        TRIGGER_UTILITY_CALIBRATION_OPPORTUNITY_RETENTION
                    ),
                    "control_nonoverlap_count": int(
                        trigger_calibration_control_summary.get("sample_count") or 0
                    ),
                    "raw_gate_nonoverlap_count": int(
                        trigger_calibration_raw_gate_summary.get("sample_count") or 0
                    ),
                    "calibrated_nonoverlap_count": int(
                        trigger_calibration_selected_summary.get("sample_count") or 0
                    ),
                    "calibrated_vs_control_retention": (
                        round(
                            int(
                                trigger_calibration_selected_summary.get("sample_count")
                                or 0
                            )
                            / int(trigger_calibration_control_summary["sample_count"]),
                            6,
                        )
                        if trigger_calibration_control_summary.get("sample_count")
                        else None
                    ),
                    **{
                        key: sum(
                            int(lane.get(key) or 0)
                            for row in evaluated_trigger_calibration_rows
                            for lane in row["capacity"]["lane_capacity"].values()
                        )
                        for key in (
                            "enter_now_decision_count",
                            "wait_decision_count",
                            "trigger_available_count",
                            "trigger_enter_count",
                            "trigger_model_skip_count",
                            "forced_trigger_exploration_count",
                        )
                    },
                    "observed_trigger_entry_retention": (
                        round(
                            sum(
                                int(lane.get("trigger_enter_count") or 0)
                                for row in evaluated_trigger_calibration_rows
                                for lane in row["capacity"]["lane_capacity"].values()
                            )
                            / sum(
                                int(lane.get("trigger_available_count") or 0)
                                for row in evaluated_trigger_calibration_rows
                                for lane in row["capacity"]["lane_capacity"].values()
                            ),
                            6,
                        )
                        if sum(
                            int(lane.get("trigger_available_count") or 0)
                            for row in evaluated_trigger_calibration_rows
                            for lane in row["capacity"]["lane_capacity"].values()
                        )
                        else None
                    ),
                    "retroactive_next_open_fallback_count": sum(
                        bool(row["retroactive_next_open_fallback_used"])
                        for row in evaluated_trigger_calibration_rows
                    ),
                },
                "prediction_diagnostics": (
                    _trigger_utility_prediction_diagnostics(
                        trigger_utility_prediction_history
                    )
                ),
                "evaluations": trigger_calibration_evaluations,
                "decision": trigger_calibration_decision,
            },
            "wait_budget_arm_comparison_walk_forward": {
                "contract": WAIT_BUDGET_CONTRACT,
                "arm_evaluation_count": wait_budget_arm_evaluation_count,
                "selected_policy_evaluation_count": (
                    wait_budget_selected_policy_evaluation_count
                ),
                "arm_summaries": wait_budget_arm_summaries,
                "arm_path_diagnostics": wait_budget_arm_paths,
                "prior_selected_policy_summary": wait_budget_selected_summary,
                "prior_selected_policy_path": wait_budget_selected_path,
                "capacity_diagnostics": {
                    "required_opportunity_retention": (
                        WAIT_BUDGET_OPPORTUNITY_RETENTION
                    ),
                    "arm_counts": {
                        arm: int(summary.get("sample_count") or 0)
                        for arm, summary in wait_budget_arm_summaries.items()
                    },
                    "arm_trigger_entry_retention": {
                        arm: (
                            round(
                                sum(
                                    int(
                                        row["capacity"]["arms"][arm].get(
                                            "trigger_enter_count"
                                        )
                                        or 0
                                    )
                                    for row in evaluated_wait_budget_rows
                                )
                                / sum(
                                    int(
                                        row["capacity"]["arms"][arm].get(
                                            "trigger_available_count"
                                        )
                                        or 0
                                    )
                                    for row in evaluated_wait_budget_rows
                                ),
                                6,
                            )
                            if sum(
                                int(
                                    row["capacity"]["arms"][arm].get(
                                        "trigger_available_count"
                                    )
                                    or 0
                                )
                                for row in evaluated_wait_budget_rows
                            )
                            else None
                        )
                        for arm in WAIT_BUDGET_ARMS
                    },
                    "retention_breach_evaluation_counts": {
                        arm: sum(
                            not bool(
                                row["capacity"]["arms"][arm][
                                    "opportunity_retention_passed"
                                ]
                            )
                            or not bool(
                                row["capacity"]["arms"][arm]["trigger_retention_passed"]
                            )
                            for row in evaluated_wait_budget_rows
                        )
                        for arm in WAIT_BUDGET_ARMS
                    },
                    "retroactive_next_open_fallback_count": sum(
                        bool(row["retroactive_next_open_fallback_used"])
                        for row in evaluated_wait_budget_rows
                    ),
                },
                "evaluations": wait_budget_evaluations,
                "decision": wait_budget_decision,
            },
            "fixed_tp_split_execution_walk_forward": (
                _compact_fixed_execution_report_payload(
                    fixed_tp_split,
                    split_execution=True,
                )
            ),
            "fixed_tp_equal_share_carry_replay": fixed_tp_equal_share_carry,
            "fixed_tp_split_entry_quality_walk_forward": (
                _compact_fixed_execution_report_payload(
                    fixed_tp_entry_quality,
                    split_execution=False,
                )
            ),
            "recoverable_basin_entry_walk_forward": recoverable_basin,
            "parent_bucket_entry_walk_forward": parent_bucket,
            "parent_bucket_conflict_stability": parent_bucket_stability,
            "parent_catastrophic_episode_audit": (parent_catastrophic_episode_audit),
            "parent_catastrophic_stop_recovery_path": (
                parent_catastrophic_stop_recovery
            ),
            "parent_post_stop_bounded_grace_arms": (parent_post_stop_bounded_grace),
            "parent_post_stop_grace_prospective_oos": (
                parent_post_stop_grace_prospective
            ),
            "exploratory_feature_contrasts": {
                "oracle_buy_top": _feature_contrasts(venue_rows, action=1)[:8],
                "oracle_sell_top": _feature_contrasts(venue_rows, action=-1)[:8],
                "authority": "full_sample_exploratory_not_oos_decision_evidence",
            },
            "decision": (
                "research_sample_floor_passed"
                if sample_floor_passed and source_quality_passed and execution_positive
                else evidence_state
            ),
        }
    dates = sorted({row.trade_date for row in rows})
    krx_pairability_decision = (
        cohorts.get("KRX", {}).get("pairability_walk_forward", {}).get("decision")
    )
    krx_competing_decision = (
        cohorts.get("KRX", {})
        .get("lane_competing_risk_walk_forward", {})
        .get("decision")
    )
    krx_economic_decision = (
        cohorts.get("KRX", {})
        .get("economic_first_passage_walk_forward", {})
        .get("decision")
    )
    krx_recovery_decision = (
        cohorts.get("KRX", {})
        .get("recovery_aware_exit_walk_forward", {})
        .get("decision")
    )
    krx_axis_decision = (
        cohorts.get("KRX", {})
        .get("recovery_trailing_axis_walk_forward", {})
        .get("decision")
    )
    krx_recovery_entry_decision = (
        cohorts.get("KRX", {})
        .get("recovery_entry_utility_walk_forward", {})
        .get("decision")
    )
    krx_calibration_decision = (
        cohorts.get("KRX", {})
        .get("recovery_entry_calibration_walk_forward", {})
        .get("decision")
    )
    krx_timing_decision = (
        cohorts.get("KRX", {})
        .get("recovery_entry_timing_walk_forward", {})
        .get("decision")
    )
    krx_timing_utility_decision = (
        cohorts.get("KRX", {})
        .get("candidate_timing_utility_walk_forward", {})
        .get("decision")
    )
    krx_trigger_calibration_decision = (
        cohorts.get("KRX", {})
        .get("trigger_utility_calibration_walk_forward", {})
        .get("decision")
    )
    krx_wait_budget_decision = (
        cohorts.get("KRX", {})
        .get("wait_budget_arm_comparison_walk_forward", {})
        .get("decision")
    )
    krx_fixed_tp_split_decision = (
        cohorts.get("KRX", {})
        .get("fixed_tp_split_execution_walk_forward", {})
        .get("decision")
    )
    krx_fixed_tp_entry_quality_decision = (
        cohorts.get("KRX", {})
        .get("fixed_tp_split_entry_quality_walk_forward", {})
        .get("decision")
    )
    krx_recoverable_basin_decision = (
        cohorts.get("KRX", {})
        .get("recoverable_basin_entry_walk_forward", {})
        .get("decision")
    )
    krx_parent_bucket_decision = (
        cohorts.get("KRX", {})
        .get("parent_bucket_entry_walk_forward", {})
        .get("decision")
    )
    krx_parent_stability_decision = (
        cohorts.get("KRX", {})
        .get("parent_bucket_conflict_stability", {})
        .get("decision")
    )
    krx_parent_catastrophic_audit_decision = (
        cohorts.get("KRX", {})
        .get("parent_catastrophic_episode_audit", {})
        .get("decision")
    )
    krx_parent_stop_recovery_decision = (
        cohorts.get("KRX", {})
        .get("parent_catastrophic_stop_recovery_path", {})
        .get("decision")
    )
    krx_parent_bounded_grace_decision = (
        cohorts.get("KRX", {})
        .get("parent_post_stop_bounded_grace_arms", {})
        .get("decision")
    )
    krx_parent_grace_prospective_decision = (
        cohorts.get("KRX", {})
        .get("parent_post_stop_grace_prospective_oos", {})
        .get("decision")
    )
    if krx_parent_grace_prospective_decision in {
        "prospective_grace_evidence_accumulating",
        "no_new_catastrophic_episode_observe",
        "prospective_grace_tradeoff_changed",
    }:
        overall_decision = str(krx_parent_grace_prospective_decision)
    elif krx_parent_grace_prospective_decision == "source_contract_gap":
        overall_decision = "parent_post_stop_grace_prospective_source_contract_gap"
    elif krx_parent_grace_prospective_decision == "source_quality_blocked":
        overall_decision = "parent_post_stop_grace_prospective_source_quality_blocked"
    elif krx_parent_bounded_grace_decision in {
        "bounded_grace_candidate_for_prospective_only",
        "immediate_stop_retained",
        "grace_tradeoff_mixed",
    }:
        overall_decision = str(krx_parent_bounded_grace_decision)
    elif krx_parent_bounded_grace_decision == "source_contract_gap":
        overall_decision = "parent_post_stop_bounded_grace_source_contract_gap"
    elif krx_parent_bounded_grace_decision == "source_quality_blocked":
        overall_decision = "parent_post_stop_bounded_grace_source_quality_blocked"
    elif krx_parent_stop_recovery_decision in {
        "catastrophic_stop_terminal_loss_protection_supported",
        "recoverable_adverse_first_dominates",
        "mixed_post_stop_paths_no_owner_change",
    }:
        overall_decision = str(krx_parent_stop_recovery_decision)
    elif krx_parent_stop_recovery_decision == "source_contract_gap":
        overall_decision = "parent_post_stop_recovery_source_contract_gap"
    elif krx_parent_stop_recovery_decision == "source_quality_blocked":
        overall_decision = "parent_post_stop_recovery_source_quality_blocked"
    elif (
        krx_parent_catastrophic_audit_decision
        == "repeatable_pre_entry_loss_signature_identified"
    ):
        overall_decision = (
            "repeatable_pre_entry_loss_signature_identified_research_only"
        )
    elif krx_parent_catastrophic_audit_decision == "loss_signature_not_separable":
        overall_decision = "loss_signature_not_separable"
    elif krx_parent_catastrophic_audit_decision == "source_contract_gap":
        overall_decision = "parent_catastrophic_audit_source_contract_gap"
    elif krx_parent_catastrophic_audit_decision == "source_quality_blocked":
        overall_decision = "parent_catastrophic_audit_source_quality_blocked"
    elif (
        krx_parent_stability_decision
        == "stable_parent_edge_needs_next_date_confirmation"
    ):
        overall_decision = "stable_parent_edge_needs_next_date_confirmation"
    elif krx_parent_stability_decision == "parent_edge_concentrated_not_reproducible":
        overall_decision = "parent_edge_concentrated_not_reproducible"
    elif krx_parent_stability_decision == "catastrophic_loss_cluster_identified":
        overall_decision = "catastrophic_loss_cluster_identified"
    elif krx_parent_stability_decision == "no_stable_parent_edge":
        overall_decision = "no_stable_parent_edge"
    elif krx_parent_stability_decision == "source_quality_blocked":
        overall_decision = "parent_stability_source_quality_blocked"
    elif krx_parent_bucket_decision == "parent_bucket_oos_positive":
        overall_decision = "parent_bucket_oos_positive_research_only"
    elif krx_parent_bucket_decision == "parent_bucket_pareto_improved":
        overall_decision = "parent_bucket_pareto_improved"
    elif krx_parent_bucket_decision == "parent_bucket_conflict_only":
        overall_decision = "parent_bucket_conflict_only"
    elif krx_parent_bucket_decision == "parent_bucket_no_incremental_value":
        overall_decision = "parent_bucket_no_incremental_value"
    elif krx_parent_bucket_decision == "source_quality_blocked":
        overall_decision = "parent_bucket_source_quality_blocked"
    elif krx_parent_bucket_decision == "insufficient_parent_history":
        overall_decision = "insufficient_parent_history"
    elif krx_parent_bucket_decision == "insufficient_coverage_dates":
        overall_decision = "parent_bucket_insufficient_coverage_dates"
    elif krx_recoverable_basin_decision == "recoverable_basin_oos_positive":
        overall_decision = "recoverable_basin_oos_positive_research_only"
    elif krx_recoverable_basin_decision == "recoverable_basin_pareto_improved":
        overall_decision = "recoverable_basin_pareto_improved"
    elif krx_recoverable_basin_decision == "broader_universe_no_incremental_value":
        overall_decision = "broader_universe_no_incremental_value"
    elif krx_recoverable_basin_decision == "source_quality_blocked":
        overall_decision = "recoverable_basin_source_quality_blocked"
    elif krx_recoverable_basin_decision == "insufficient_prior_candidate_history":
        overall_decision = "insufficient_prior_candidate_history"
    elif krx_recoverable_basin_decision == "insufficient_coverage_dates":
        overall_decision = "recoverable_basin_insufficient_coverage_dates"
    elif krx_fixed_tp_entry_quality_decision == "entry_quality_oos_positive":
        overall_decision = "entry_quality_oos_positive_research_only"
    elif krx_fixed_tp_entry_quality_decision == "entry_quality_pareto_improved":
        overall_decision = "entry_quality_pareto_improved"
    elif krx_fixed_tp_entry_quality_decision == "no_incremental_predictive_value":
        overall_decision = "entry_quality_no_incremental_predictive_value"
    elif krx_fixed_tp_entry_quality_decision == "source_quality_blocked":
        overall_decision = "entry_quality_source_quality_blocked"
    elif krx_fixed_tp_entry_quality_decision == "insufficient_prior_failure_history":
        overall_decision = "insufficient_prior_failure_history"
    elif krx_fixed_tp_entry_quality_decision == "insufficient_coverage_dates":
        overall_decision = "entry_quality_insufficient_coverage_dates"
    elif krx_fixed_tp_split_decision == "fixed_tp_split_oos_positive":
        overall_decision = "fixed_tp_split_oos_positive_research_only"
    elif krx_fixed_tp_split_decision == "fixed_tp_split_pareto_improved":
        overall_decision = "fixed_tp_split_pareto_improved"
    elif krx_fixed_tp_split_decision == "no_incremental_predictive_value":
        overall_decision = "fixed_tp_split_no_incremental_predictive_value"
    elif krx_fixed_tp_split_decision == "source_quality_blocked":
        overall_decision = "fixed_tp_split_source_quality_blocked"
    elif krx_fixed_tp_split_decision == "insufficient_prior_arm_history":
        overall_decision = "fixed_tp_split_insufficient_prior_arm_history"
    elif krx_fixed_tp_split_decision == "insufficient_coverage_dates":
        overall_decision = "fixed_tp_split_insufficient_coverage_dates"
    elif krx_wait_budget_decision == "wait_budget_oos_positive":
        overall_decision = "wait_budget_oos_positive_research_only"
    elif krx_wait_budget_decision == "wait_budget_pareto_improved":
        overall_decision = "wait_budget_pareto_improved"
    elif krx_wait_budget_decision == "no_incremental_predictive_value":
        overall_decision = "wait_budget_no_incremental_predictive_value"
    elif krx_wait_budget_decision == "source_quality_blocked":
        overall_decision = "wait_budget_source_quality_blocked"
    elif krx_wait_budget_decision == "insufficient_wait_budget_history":
        overall_decision = "insufficient_wait_budget_history"
    elif krx_trigger_calibration_decision == "calibrated_trigger_utility_oos_positive":
        overall_decision = "calibrated_trigger_utility_oos_positive_research_only"
    elif (
        krx_trigger_calibration_decision == "calibrated_trigger_utility_pareto_improved"
    ):
        overall_decision = "calibrated_trigger_utility_pareto_improved"
    elif krx_trigger_calibration_decision == "no_incremental_predictive_value":
        overall_decision = "calibrated_trigger_utility_no_incremental_predictive_value"
    elif krx_trigger_calibration_decision == "source_quality_blocked":
        overall_decision = "calibrated_trigger_utility_source_quality_blocked"
    elif krx_trigger_calibration_decision == "insufficient_trigger_history":
        overall_decision = "insufficient_trigger_history"
    elif krx_timing_utility_decision == "candidate_timing_utility_oos_positive":
        overall_decision = "candidate_timing_utility_oos_positive_research_only"
    elif krx_timing_utility_decision == "candidate_timing_utility_pareto_improved":
        overall_decision = "candidate_timing_utility_pareto_improved"
    elif krx_timing_utility_decision == "no_incremental_predictive_value":
        overall_decision = "candidate_timing_utility_no_incremental_predictive_value"
    elif krx_timing_utility_decision == "source_quality_blocked":
        overall_decision = "candidate_timing_utility_source_quality_blocked"
    elif krx_timing_utility_decision == "insufficient_timing_pair_history":
        overall_decision = "insufficient_timing_pair_history"
    elif krx_timing_decision == "entry_timing_oos_positive":
        overall_decision = "entry_timing_oos_positive_research_only"
    elif krx_timing_decision == "entry_timing_pareto_improved":
        overall_decision = "entry_timing_pareto_improved"
    elif krx_timing_decision == "no_incremental_predictive_value":
        overall_decision = "entry_timing_no_incremental_predictive_value"
    elif krx_timing_decision == "source_quality_blocked":
        overall_decision = "entry_timing_source_quality_blocked"
    elif krx_timing_decision == "insufficient_timing_history":
        overall_decision = "insufficient_timing_history"
    elif krx_calibration_decision == "calibrated_recovery_entry_oos_positive":
        overall_decision = "calibrated_recovery_entry_oos_positive_research_only"
    elif krx_calibration_decision == "calibrated_recovery_entry_pareto_improved":
        overall_decision = "calibrated_recovery_entry_pareto_improved"
    elif krx_calibration_decision == "no_incremental_predictive_value":
        overall_decision = "calibrated_recovery_entry_no_incremental_predictive_value"
    elif krx_calibration_decision == "insufficient_calibration_history":
        overall_decision = "insufficient_calibration_history"
    elif krx_calibration_decision == "source_quality_blocked":
        overall_decision = "recovery_entry_calibration_source_quality_blocked"
    elif krx_calibration_decision == "insufficient_coverage_dates":
        overall_decision = "recovery_entry_calibration_insufficient_coverage_dates"
    elif krx_recovery_entry_decision == "recovery_entry_utility_oos_positive":
        overall_decision = "recovery_entry_utility_oos_positive_research_only"
    elif krx_recovery_entry_decision == "recovery_entry_utility_improved_but_negative":
        overall_decision = "recovery_entry_utility_improved_but_negative"
    elif krx_recovery_entry_decision == "no_incremental_predictive_value":
        overall_decision = "recovery_entry_utility_no_incremental_predictive_value"
    elif krx_recovery_entry_decision == "insufficient_recovery_entry_labels":
        overall_decision = "insufficient_recovery_entry_labels"
    elif krx_recovery_entry_decision == "source_quality_blocked":
        overall_decision = "recovery_entry_utility_source_quality_blocked"
    elif krx_recovery_entry_decision == "insufficient_coverage_dates":
        overall_decision = "recovery_entry_utility_insufficient_coverage_dates"
    elif krx_axis_decision == "recovery_only_oos_positive":
        overall_decision = "recovery_only_oos_positive_research_only"
    elif krx_axis_decision == "trailing_incremental_ev_positive":
        overall_decision = "trailing_incremental_ev_positive_research_only"
    elif krx_axis_decision == "axis_separation_improved_but_negative":
        overall_decision = "axis_separation_improved_but_negative"
    elif krx_axis_decision == "no_incremental_predictive_value":
        overall_decision = "axis_separation_no_incremental_predictive_value"
    elif krx_recovery_decision == "recovery_aware_exit_oos_positive":
        overall_decision = "recovery_aware_exit_oos_positive_research_only"
    elif krx_recovery_decision == "recovery_aware_exit_improved_but_negative":
        overall_decision = "recovery_aware_exit_improved_but_negative"
    elif krx_recovery_decision == "no_incremental_predictive_value":
        overall_decision = "recovery_aware_exit_no_incremental_predictive_value"
    elif krx_economic_decision == "economic_first_passage_oos_positive":
        overall_decision = "economic_first_passage_oos_positive_research_only"
    elif krx_economic_decision == "economic_first_passage_improved_but_negative":
        overall_decision = "economic_first_passage_improved_but_negative"
    elif krx_economic_decision == "no_incremental_predictive_value":
        overall_decision = "economic_first_passage_no_incremental_predictive_value"
    elif krx_competing_decision == "lane_competing_risk_oos_positive":
        overall_decision = "lane_competing_risk_oos_positive_research_only"
    elif krx_competing_decision == "lane_ev_improved_but_negative":
        overall_decision = "lane_ev_improved_but_negative"
    elif krx_competing_decision == "no_incremental_predictive_value":
        overall_decision = "lane_competing_risk_no_incremental_predictive_value"
    elif krx_pairability_decision == "pairability_oos_positive":
        overall_decision = "pairability_oos_positive_research_only"
    elif krx_pairability_decision == "pairability_detected_execution_negative":
        overall_decision = "pairability_detected_execution_negative"
    elif any(
        cohort["decision"] == "predictive_structure_found_execution_policy_unprofitable"
        for cohort in cohorts.values()
    ):
        overall_decision = "predictive_structure_found_execution_policy_unprofitable"
    else:
        overall_decision = "insufficient_for_strategy_or_runtime_judgment"
    return {
        "schema": "pure_market_adaptive_opportunity_replay_v21",
        "generated_at_kst": datetime.now(KST).isoformat(timespec="seconds"),
        "objective": "discover cost-bearing intraday opportunities without fixed drawdown_or_rebound labels and test causal common-state predictability",
        "symbol": base.SAMSUNG_CODE,
        "data_start_date": dates[0].isoformat() if dates else None,
        "data_end_date": dates[-1].isoformat() if dates else None,
        "trading_date_count": len(dates),
        "training_days": training_days,
        "round_trip_cost_pct": cost_pct,
        "feature_names": FEATURE_NAMES,
        "metric_contract": METRIC_CONTRACT,
        "pairability_contract": PAIRABILITY_CONTRACT,
        "competing_risk_contract": COMPETING_RISK_CONTRACT,
        "economic_first_passage_contract": ECONOMIC_FIRST_PASSAGE_CONTRACT,
        "recovery_aware_contract": RECOVERY_AWARE_CONTRACT,
        "recovery_trailing_axis_contract": RECOVERY_TRAILING_AXIS_CONTRACT,
        "recovery_entry_utility_contract": RECOVERY_ENTRY_UTILITY_CONTRACT,
        "recovery_entry_calibration_contract": RECOVERY_ENTRY_CALIBRATION_CONTRACT,
        "recovery_entry_timing_contract": RECOVERY_ENTRY_TIMING_CONTRACT,
        "recovery_entry_timing_utility_contract": (
            RECOVERY_ENTRY_TIMING_UTILITY_CONTRACT
        ),
        "trigger_utility_calibration_contract": (TRIGGER_UTILITY_CALIBRATION_CONTRACT),
        "wait_budget_contract": WAIT_BUDGET_CONTRACT,
        "fixed_tp_split_contract": FIXED_TP_SPLIT_CONTRACT,
        "fixed_tp_equal_share_carry_contract": (FIXED_TP_EQUAL_SHARE_CARRY_CONTRACT),
        "fixed_tp_entry_quality_contract": FIXED_TP_ENTRY_QUALITY_CONTRACT,
        "recoverable_basin_contract": RECOVERABLE_BASIN_CONTRACT,
        "parent_bucket_contract": PARENT_BUCKET_CONTRACT,
        "parent_bucket_stability_contract": PARENT_BUCKET_STABILITY_CONTRACT,
        "parent_catastrophic_episode_audit_contract": (
            PARENT_CATASTROPHIC_AUDIT_CONTRACT
        ),
        "parent_catastrophic_stop_recovery_contract": (
            PARENT_POST_STOP_RECOVERY_CONTRACT
        ),
        "parent_post_stop_bounded_grace_contract": (PARENT_POST_STOP_GRACE_CONTRACT),
        "parent_post_stop_grace_prospective_contract": (
            PARENT_POST_STOP_GRACE_PROSPECTIVE_CONTRACT
        ),
        "stock_source_quality": stock_source_quality,
        "kospi_source_quality": kospi_source_quality,
        "coverage": coverage,
        "oracle_cost_sensitivity": oracle_cost_sensitivity,
        "cohorts": cohorts,
        "decision": overall_decision,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# Pure-market adaptive opportunity replay — {report['data_start_date']} to {report['data_end_date']}",
        "",
        "## Decision",
        "",
        f"- decision: `{report['decision']}`",
        f"- qualified trading dates: `{report['trading_date_count']}` / required `{base.MIN_QUALIFIED_TRADING_DAYS}`",
        f"- round-trip cost: `{report['round_trip_cost_pct']}%`",
        "- fixed drawdown/rebound opportunity labels: `none`",
        "- runtime_effect: `false`",
        "",
        "## Opportunity upper bound and causal walk-forward",
        "",
        "| Venue | Oracle trades | Oracle avg/day | Oracle daily compounded | OOS dates | OOS trades | OOS net EV | Win rate | Buy AP lift | Sell AP lift | Source |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for venue in base.COHORTS:
        cohort = report["cohorts"][venue]
        oracle = cohort["oracle_upper_bound"]
        walk = cohort["walk_forward"]
        summary = walk["out_of_sample_summary"]
        lines.append(
            "| "
            + " | ".join(
                [
                    venue,
                    str(oracle["trade_count"]),
                    str(oracle["avg_trades_per_date"]),
                    str(oracle["avg_daily_oracle_compounded_return_pct"]),
                    str(walk["evaluation_count"]),
                    str(summary["sample_count"]),
                    str(summary["equal_weight_avg_profit_pct"]),
                    str(summary["diagnostic_win_rate_pct"]),
                    str(walk["buy_precision_lift_vs_prevalence"]),
                    str(walk["sell_precision_lift_vs_prevalence"]),
                    cohort["source_quality"],
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Nested pairability walk-forward",
            "",
            "| Venue | Pairability OOS dates | Control trades | Control EV | Selected trades | Selected EV | EV delta | Win rate | Weak-reversal EV | Bullish-transition EV | Decision |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for venue in base.COHORTS:
        pair = report["cohorts"][venue]["pairability_walk_forward"]
        control = pair["control_summary_same_dates"]
        selected = pair["selected_summary"]
        control_ev = control["equal_weight_avg_profit_pct"]
        selected_ev = selected["equal_weight_avg_profit_pct"]
        ev_delta = (
            round(float(selected_ev) - float(control_ev), 6)
            if selected_ev is not None and control_ev is not None
            else None
        )
        lanes = pair["selected_lane_summaries"]
        lines.append(
            "| "
            + " | ".join(
                [
                    venue,
                    str(pair["evaluation_count"]),
                    str(control["sample_count"]),
                    str(control_ev),
                    str(selected["sample_count"]),
                    str(selected_ev),
                    str(ev_delta),
                    str(selected["diagnostic_win_rate_pct"]),
                    str(lanes["weak_reversal"]["equal_weight_avg_profit_pct"]),
                    str(lanes["bullish_transition"]["equal_weight_avg_profit_pct"]),
                    pair["decision"],
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "Pairability uses only candidate episodes from earlier base-model OOS dates. The current date's exit reason and profit are evaluation outcomes only; they do not select the model, selection fraction, or probability cutoff.",
        ]
    )
    lines.extend(
        [
            "",
            "## Lane competing-risk direct-EV walk-forward",
            "",
            "| Venue | OOS dates | Control trades | Control EV | Selected trades | Selected EV | EV delta | Win rate | Weak-reversal EV | Bullish-transition EV | Decision |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for venue in base.COHORTS:
        risk = report["cohorts"][venue]["lane_competing_risk_walk_forward"]
        control = risk["control_summary_same_dates"]
        selected = risk["selected_summary"]
        control_ev = control["equal_weight_avg_profit_pct"]
        selected_ev = selected["equal_weight_avg_profit_pct"]
        ev_delta = (
            round(float(selected_ev) - float(control_ev), 6)
            if selected_ev is not None and control_ev is not None
            else None
        )
        lanes = risk["selected_lane_summaries"]
        lines.append(
            "| "
            + " | ".join(
                [
                    venue,
                    str(risk["evaluation_count"]),
                    str(control["sample_count"]),
                    str(control_ev),
                    str(selected["sample_count"]),
                    str(selected_ev),
                    str(ev_delta),
                    str(selected["diagnostic_win_rate_pct"]),
                    str(lanes["weak_reversal"]["equal_weight_avg_profit_pct"]),
                    str(lanes["bullish_transition"]["equal_weight_avg_profit_pct"]),
                    risk["decision"],
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "This layer removes the common duration cap. Each lane predicts the first causal sell transition, adverse buy transition, or session-end censor and selects only candidates with prior-only predicted cost-adjusted EV above zero.",
        ]
    )
    lines.extend(
        [
            "",
            "## Economic first-passage direct-EV walk-forward",
            "",
            "| Venue | OOS dates | Control trades | Control EV | Selected trades | Selected EV | EV delta | Compounded net | Avg MFE | Avg MAE | Full-session MFE >=0.5 | Adverse-first then target | Median duration | Weak-reversal EV | Bullish-transition EV | Decision |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for venue in base.COHORTS:
        economic = report["cohorts"][venue]["economic_first_passage_walk_forward"]
        control = economic["control_summary_same_dates"]
        selected = economic["selected_summary"]
        diagnostics = economic["selected_path_diagnostics"]
        control_ev = control["equal_weight_avg_profit_pct"]
        selected_ev = selected["equal_weight_avg_profit_pct"]
        ev_delta = (
            round(float(selected_ev) - float(control_ev), 6)
            if selected_ev is not None and control_ev is not None
            else None
        )
        lanes = economic["selected_lane_summaries"]
        lines.append(
            "| "
            + " | ".join(
                [
                    venue,
                    str(economic["evaluation_count"]),
                    str(control["sample_count"]),
                    str(control_ev),
                    str(selected["sample_count"]),
                    str(selected_ev),
                    str(ev_delta),
                    str(diagnostics["compounded_net_return_pct"]),
                    str(diagnostics["avg_mfe_pct"]),
                    str(diagnostics["avg_mae_pct"]),
                    str(diagnostics["post_entry_session_mfe_ge_0_5_count"]),
                    str(diagnostics["adverse_first_then_later_favorable_count"]),
                    str(diagnostics["median_event_duration_minutes"]),
                    str(lanes["weak_reversal"]["equal_weight_avg_profit_pct"]),
                    str(lanes["bullish_transition"]["equal_weight_avg_profit_pct"]),
                    economic["decision"],
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "Favorable boundaries are round-trip cost plus a candidate's causal volatility scale; adverse boundaries use that same scale. Lane-specific multipliers are selected only on an earlier chronological validation suffix. Current-date paths are evaluation outcomes, never entry features or boundary-selection inputs.",
        ]
    )
    lines.extend(
        [
            "",
            "## Recovery-aware exit and favorable trailing walk-forward",
            "",
            "| Venue | OOS dates | Same-entry baseline trades | Baseline EV | Recovery trades | Recovery EV | EV delta | Compounded net | Deferred adverse exits | Recovered to favorable | Trailing exits | MFE capture | Weak-reversal EV | Bullish-transition EV | Decision |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for venue in base.COHORTS:
        recovery = report["cohorts"][venue]["recovery_aware_exit_walk_forward"]
        baseline = recovery["baseline_selected_summary_same_entries"]
        selected = recovery["selected_summary"]
        diagnostics = recovery["selected_path_diagnostics"]
        baseline_ev = baseline["equal_weight_avg_profit_pct"]
        selected_ev = selected["equal_weight_avg_profit_pct"]
        ev_delta = (
            round(float(selected_ev) - float(baseline_ev), 6)
            if selected_ev is not None and baseline_ev is not None
            else None
        )
        lanes = recovery["selected_lane_summaries"]
        lines.append(
            "| "
            + " | ".join(
                [
                    venue,
                    str(recovery["evaluation_count"]),
                    str(baseline["sample_count"]),
                    str(baseline_ev),
                    str(selected["sample_count"]),
                    str(selected_ev),
                    str(ev_delta),
                    str(diagnostics["compounded_net_return_pct"]),
                    str(diagnostics["recovery_deferred_count"]),
                    str(diagnostics["recovered_to_favorable_count"]),
                    str(diagnostics["trailing_exit_count"]),
                    str(diagnostics["avg_positive_mfe_capture_ratio_pct"]),
                    str(lanes["weak_reversal"]["equal_weight_avg_profit_pct"]),
                    str(lanes["bullish_transition"]["equal_weight_avg_profit_pct"]),
                    recovery["decision"],
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "The baseline and recovery rows use the exact same prior-only selected entry timestamps. Adverse exits are deferred only when the prior lane model predicts positive incremental EV; recovery probability and time are diagnostics. Favorable trailing and recovery bounds are selected only from earlier dates.",
        ]
    )
    lines.extend(
        [
            "",
            "## Recovery and favorable-trailing axis separation",
            "",
            "| Venue | OOS dates | Same-entry trades | Baseline EV | Recovery-only EV | Recovery delta | Trailing-only EV | Trailing delta | Combined EV | Combined delta | Recovery-only MAE | Trailing applied | Decision |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for venue in base.COHORTS:
        axis = report["cohorts"][venue]["recovery_trailing_axis_walk_forward"]
        summaries = axis["arm_summaries"]
        deltas = axis["paired_delta_summaries"]
        diagnostics = axis["arm_path_diagnostics"]
        lines.append(
            "| "
            + " | ".join(
                [
                    venue,
                    str(axis["evaluation_count"]),
                    str(summaries["baseline"]["sample_count"]),
                    str(summaries["baseline"]["equal_weight_avg_profit_pct"]),
                    str(summaries["recovery_only"]["equal_weight_avg_profit_pct"]),
                    str(deltas["recovery_only"]["avg_incremental_net_profit_pct"]),
                    str(summaries["trailing_only"]["equal_weight_avg_profit_pct"]),
                    str(deltas["trailing_only"]["avg_incremental_net_profit_pct"]),
                    str(
                        summaries["recovery_plus_trailing"][
                            "equal_weight_avg_profit_pct"
                        ]
                    ),
                    str(
                        deltas["recovery_plus_trailing"][
                            "avg_incremental_net_profit_pct"
                        ]
                    ),
                    str(diagnostics["recovery_only"]["avg_mae_pct"]),
                    str(diagnostics["trailing_only"]["trailing_exit_count"]),
                    axis["decision"],
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "All four arms preserve the exact economic-selected entry timestamps. Recovery labels use immediate favorable exits and contain no trailing outcome. Trailing is decided by a separate prior-only favorable-checkpoint incremental-EV model; a positive external OOS result is never reused as a same-report lane switch.",
        ]
    )
    lines.extend(
        [
            "",
            "## Recovery-only outcome direct entry utility",
            "",
            "| Venue | OOS dates | Eligible candidates | Control trades | Control EV | Selected trades | Selected EV | EV delta | Control compounded | Selected compounded | Selected MAE | Prior OOS labels | Decision |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for venue in base.COHORTS:
        entry_utility = report["cohorts"][venue]["recovery_entry_utility_walk_forward"]
        control = entry_utility["control_summary_same_dates_and_exit_policy"]
        selected = entry_utility["selected_summary"]
        control_ev = control["equal_weight_avg_profit_pct"]
        selected_ev = selected["equal_weight_avg_profit_pct"]
        ev_delta = (
            round(float(selected_ev) - float(control_ev), 6)
            if selected_ev is not None and control_ev is not None
            else None
        )
        control_path = entry_utility["control_path_diagnostics"]
        selected_path = entry_utility["selected_path_diagnostics"]
        lines.append(
            "| "
            + " | ".join(
                [
                    venue,
                    str(entry_utility["evaluation_count"]),
                    str(entry_utility["eligible_candidate_count"]),
                    str(control["sample_count"]),
                    str(control_ev),
                    str(selected["sample_count"]),
                    str(selected_ev),
                    str(ev_delta),
                    str(control_path["compounded_net_return_pct"]),
                    str(selected_path["compounded_net_return_pct"]),
                    str(selected_path["avg_mae_pct"]),
                    str(entry_utility["history_oos_recovery_episode_count"]),
                    entry_utility["decision"],
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "The control keeps the existing economic entry selector while both selectors share each date's prior-only recovery-only exit policy. The new lane model is fitted only on recovery outcomes that were already evaluated out of sample on earlier dates. Current-date outcomes, trailing results, and full-session MFE/MAE cannot enter its features or selection rule.",
        ]
    )
    lines.extend(
        [
            "",
            "## Prior-only recovery-entry calibration and capacity",
            "",
            "| Venue | OOS dates | Eligible | Control n/EV | Raw n/EV | Calibrated n/EV | Cal EV delta vs raw | Control/Raw/Cal compounded | Control/Raw/Cal MAE | Cal mean+/final | Retention | Decision |",
            "| --- | ---: | ---: | --- | --- | --- | ---: | --- | --- | --- | ---: | --- |",
        ]
    )
    for venue in base.COHORTS:
        calibration = report["cohorts"][venue][
            "recovery_entry_calibration_walk_forward"
        ]
        control = calibration["economic_control_summary_same_dates_and_exit_policy"]
        raw = calibration["raw_recovery_entry_summary_same_dates"]
        selected = calibration["calibrated_selected_summary"]
        paths = calibration["path_diagnostics"]
        capacity = calibration["capacity_diagnostics"]
        raw_ev = raw["equal_weight_avg_profit_pct"]
        selected_ev = selected["equal_weight_avg_profit_pct"]
        delta = (
            round(float(selected_ev) - float(raw_ev), 6)
            if selected_ev is not None and raw_ev is not None
            else None
        )
        lines.append(
            "| "
            + " | ".join(
                [
                    venue,
                    str(calibration["evaluation_count"]),
                    str(calibration["eligible_candidate_count"]),
                    f"{control['sample_count']}/{control['equal_weight_avg_profit_pct']}",
                    f"{raw['sample_count']}/{raw_ev}",
                    f"{selected['sample_count']}/{selected_ev}",
                    str(delta),
                    "/".join(
                        str(paths[arm]["compounded_net_return_pct"])
                        for arm in (
                            "economic_control",
                            "raw_recovery_entry",
                            "calibrated_recovery_entry",
                        )
                    ),
                    "/".join(
                        str(paths[arm]["avg_mae_pct"])
                        for arm in (
                            "economic_control",
                            "raw_recovery_entry",
                            "calibrated_recovery_entry",
                        )
                    ),
                    (
                        f"{capacity['calibrated_mean_positive_candidate_count']}/"
                        f"{capacity['calibrated_nonoverlap_count']}"
                    ),
                    str(capacity["calibrated_vs_raw_nonoverlap_retention"]),
                    calibration["decision"],
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "Lane calibrators use only earlier OOS recovery-entry prediction residuals. Reliability-shrunk mean EV, not a positive lower confidence bound, owns selection. Prediction bins, date drift, and capacity losses are post-OOS diagnostics only and cannot change a lane or threshold in the same report.",
        ]
    )
    lines.extend(
        [
            "",
            "## Recovery-entry causal timing nested OOS",
            "",
            "| Venue | OOS dates | Raw n/EV | Timing n/EV | EV delta | Raw/Timing compounded | Raw/Timing MAE | Retention | Fallback dates | Missed entries | Decision |",
            "| --- | ---: | --- | --- | ---: | --- | --- | ---: | ---: | ---: | --- |",
        ]
    )
    for venue in base.COHORTS:
        timing = report["cohorts"][venue]["recovery_entry_timing_walk_forward"]
        control = timing["raw_recovery_entry_control_summary_same_dates"]
        selected = timing["prior_selected_timing_summary"]
        paths = timing["path_diagnostics"]
        capacity = timing["capacity_diagnostics"]
        control_ev = control["equal_weight_avg_profit_pct"]
        selected_ev = selected["equal_weight_avg_profit_pct"]
        delta = (
            round(float(selected_ev) - float(control_ev), 6)
            if selected_ev is not None and control_ev is not None
            else None
        )
        lines.append(
            "| "
            + " | ".join(
                [
                    venue,
                    str(timing["evaluation_count"]),
                    f"{control['sample_count']}/{control_ev}",
                    f"{selected['sample_count']}/{selected_ev}",
                    str(delta),
                    (
                        f"{paths['raw_next_open_control']['compounded_net_return_pct']}/"
                        f"{paths['prior_selected_timing']['compounded_net_return_pct']}"
                    ),
                    (
                        f"{paths['raw_next_open_control']['avg_mae_pct']}/"
                        f"{paths['prior_selected_timing']['avg_mae_pct']}"
                    ),
                    str(capacity["timing_vs_raw_nonoverlap_retention"]),
                    str(capacity["capacity_fallback_evaluation_count"]),
                    str(capacity["missed_entry_count"]),
                    timing["decision"],
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "Each arm is triggered from completed bars and entered at the next open. The arm and maximum wait are selected only from earlier OOS arm outcomes. Current-date outcomes cannot select the current-date timing, all arms retain the recovery-only exit owner, and date-level fallback enforces the 75% raw-opportunity floor.",
            "",
            "| Venue | Arm | OOS trades | Net EV | Compounded | MAE |",
            "| --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for venue in base.COHORTS:
        timing = report["cohorts"][venue]["recovery_entry_timing_walk_forward"]
        for arm in RECOVERY_ENTRY_TIMING_ARMS:
            summary = timing["arm_summaries"][arm]
            path = timing["arm_path_diagnostics"][arm]
            lines.append(
                "| "
                + " | ".join(
                    [
                        venue,
                        arm,
                        str(summary["sample_count"]),
                        str(summary["equal_weight_avg_profit_pct"]),
                        str(path["compounded_net_return_pct"]),
                        str(path["avg_mae_pct"]),
                    ]
                )
                + " |"
            )
    lines.extend(
        [
            "",
            "## Candidate timing incremental utility nested OOS",
            "",
            "| Venue | OOS dates | Control n/EV | Selected n/EV | EV delta | Control/Selected compounded | Control/Selected MAE | Retention | Enter now | Wait | Trigger enter | Decision |",
            "| --- | ---: | --- | --- | ---: | --- | --- | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for venue in base.COHORTS:
        utility = report["cohorts"][venue]["candidate_timing_utility_walk_forward"]
        control = utility["control_summary_same_dates"]
        selected = utility["selected_summary"]
        paths = utility["path_diagnostics"]
        capacity = utility["capacity_diagnostics"]
        control_ev = control["equal_weight_avg_profit_pct"]
        selected_ev = selected["equal_weight_avg_profit_pct"]
        delta = (
            round(float(selected_ev) - float(control_ev), 6)
            if selected_ev is not None and control_ev is not None
            else None
        )
        lines.append(
            "| "
            + " | ".join(
                [
                    venue,
                    str(utility["evaluation_count"]),
                    f"{control['sample_count']}/{control_ev}",
                    f"{selected['sample_count']}/{selected_ev}",
                    str(delta),
                    (
                        f"{paths['enter_now_control']['compounded_net_return_pct']}/"
                        f"{paths['candidate_timing_utility']['compounded_net_return_pct']}"
                    ),
                    (
                        f"{paths['enter_now_control']['avg_mae_pct']}/"
                        f"{paths['candidate_timing_utility']['avg_mae_pct']}"
                    ),
                    str(capacity["selected_vs_control_nonoverlap_retention"]),
                    str(capacity["enter_now_decision_count"]),
                    str(capacity["wait_decision_count"]),
                    str(capacity["trigger_enter_count"]),
                    utility["decision"],
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "The baseline decision uses only features available at the original recovery-entry candidate. A wait decision may use completed-bar trigger features only after that trigger exists, and then chooses timed entry or no trade. There is no retroactive next-open fallback. A causal three-enter-now to one-wait exploration budget preserves at least 75% opportunity capacity before the final cross-lane retention gate.",
            "",
            "## Trigger utility calibration and bounded exploration",
            "",
            "| Venue | OOS dates | Control n/EV | Raw gate n/EV | Calibrated n/EV | Calibrated delta vs raw | Control/Raw/Calibrated compounded | Control/Raw/Calibrated MAE | Opportunity retention | Trigger entry retention | Forced trigger entries | Decision |",
            "| --- | ---: | --- | --- | --- | ---: | --- | --- | ---: | ---: | ---: | --- |",
        ]
    )
    for venue in base.COHORTS:
        calibration = report["cohorts"][venue][
            "trigger_utility_calibration_walk_forward"
        ]
        control = calibration["control_summary_same_dates"]
        raw_gate = calibration["raw_trigger_gate_summary_same_dates"]
        selected = calibration["calibrated_trigger_summary"]
        paths = calibration["path_diagnostics"]
        capacity = calibration["capacity_diagnostics"]
        raw_ev = raw_gate["equal_weight_avg_profit_pct"]
        selected_ev = selected["equal_weight_avg_profit_pct"]
        delta = (
            round(float(selected_ev) - float(raw_ev), 6)
            if selected_ev is not None and raw_ev is not None
            else None
        )
        lines.append(
            "| "
            + " | ".join(
                [
                    venue,
                    str(calibration["evaluation_count"]),
                    (
                        f"{control['sample_count']}/"
                        f"{control['equal_weight_avg_profit_pct']}"
                    ),
                    f"{raw_gate['sample_count']}/{raw_ev}",
                    f"{selected['sample_count']}/{selected_ev}",
                    str(delta),
                    "/".join(
                        str(paths[arm]["compounded_net_return_pct"])
                        for arm in (
                            "enter_now_control",
                            "raw_trigger_gate",
                            "calibrated_bounded_trigger",
                        )
                    ),
                    "/".join(
                        str(paths[arm]["avg_mae_pct"])
                        for arm in (
                            "enter_now_control",
                            "raw_trigger_gate",
                            "calibrated_bounded_trigger",
                        )
                    ),
                    str(capacity["calibrated_vs_control_retention"]),
                    str(capacity["observed_trigger_entry_retention"]),
                    str(capacity["forced_trigger_exploration_count"]),
                    calibration["decision"],
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "Trigger calibration consumes only earlier OOS raw predictions and realized recovery-only outcomes. The affine rank slope, residual intercept, and recent-date drift are shrunk toward the raw forecast. Three observed trigger entries earn at most one model skip, so a nonpositive calibrated forecast cannot eliminate the initial trigger sample. Realized outcomes remain post-OOS diagnostics and cannot update the same-date calibration.",
        ]
    )
    lines.extend(
        [
            "",
            "## Candidate timing wait-budget arm comparison",
            "",
            "| Venue | Arm OOS dates | 3:1 n/EV | 2:1 n/EV | 1:1 n/EV | 3:1/2:1/1:1 compounded | 3:1/2:1/1:1 MAE | Trigger retention 3:1/2:1/1:1 | Prior-selected OOS dates | Decision |",
            "| --- | ---: | --- | --- | --- | --- | --- | --- | ---: | --- |",
        ]
    )
    for venue in base.COHORTS:
        wait_budget = report["cohorts"][venue][
            "wait_budget_arm_comparison_walk_forward"
        ]
        arm_summaries = wait_budget["arm_summaries"]
        arm_paths = wait_budget["arm_path_diagnostics"]
        trigger_retention = wait_budget["capacity_diagnostics"][
            "arm_trigger_entry_retention"
        ]
        lines.append(
            "| "
            + " | ".join(
                [
                    venue,
                    str(wait_budget["arm_evaluation_count"]),
                    *(
                        f"{arm_summaries[arm]['sample_count']}/"
                        f"{arm_summaries[arm]['equal_weight_avg_profit_pct']}"
                        for arm in WAIT_BUDGET_ARMS
                    ),
                    "/".join(
                        str(arm_paths[arm]["compounded_net_return_pct"])
                        for arm in WAIT_BUDGET_ARMS
                    ),
                    "/".join(
                        str(arm_paths[arm]["avg_mae_pct"]) for arm in WAIT_BUDGET_ARMS
                    ),
                    "/".join(str(trigger_retention[arm]) for arm in WAIT_BUDGET_ARMS),
                    str(wait_budget["selected_policy_evaluation_count"]),
                    wait_budget["decision"],
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "All three arms share the same prior-only trigger calibration, bounded trigger exploration, and recovery-only exit owner. The current evaluation date contributes arm outcomes only after all arm decisions are complete. A prior-selected executable arm is absent until at least one earlier complete arm-comparison date exists; same-date best-arm selection is forbidden.",
        ]
    )
    lines.extend(
        [
            "",
            "## Fixed-entry split-buy and fixed-take-profit causal replay",
            "",
            "| Venue | Arm | Trades | Planned-budget EV | Deployed EV | Compounded | Budget MAE | Avg deployed | Avg legs | Basis improvement | TP/Disaster/Close | TP below first entry |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: |",
        ]
    )
    for venue in base.COHORTS:
        split = report["cohorts"][venue]["fixed_tp_split_execution_walk_forward"]
        for arm in FIXED_TP_SPLIT_ARMS:
            summary = split["arm_summaries"][arm]
            path = split["arm_path_diagnostics"][arm]
            lines.append(
                "| "
                + " | ".join(
                    [
                        venue,
                        arm,
                        str(summary["sample_count"]),
                        str(summary["equal_weight_avg_profit_pct"]),
                        str(path["avg_deployed_notional_return_pct"]),
                        str(path["compounded_planned_budget_return_pct"]),
                        str(path["avg_planned_budget_mae_pct"]),
                        str(path["avg_deployed_fraction"]),
                        str(path["avg_filled_leg_count"]),
                        str(path["avg_cost_basis_improvement_pct"]),
                        (
                            f"{path['target_exit_count']}/"
                            f"{path['catastrophic_stop_count']}/"
                            f"{path['session_close_count']}"
                        ),
                        str(path["target_exit_below_initial_count"]),
                    ]
                )
                + " |"
            )
    lines.extend(
        [
            "",
            "| Venue | Arm dates | Prior-selected dates | Selected n/EV | Same-date single control n/EV | Selected/control compounded | Selected/control budget MAE | Decision |",
            "| --- | ---: | ---: | --- | --- | --- | --- | --- |",
        ]
    )
    for venue in base.COHORTS:
        split = report["cohorts"][venue]["fixed_tp_split_execution_walk_forward"]
        selected = split["prior_selected_policy_summary_same_dates"]
        control = split["single_entry_control_summary_same_dates"]
        selected_path = split["prior_selected_policy_path"]
        control_path = split["single_entry_control_path_same_dates"]
        lines.append(
            "| "
            + " | ".join(
                [
                    venue,
                    str(split["arm_evaluation_count"]),
                    str(split["selected_policy_evaluation_count"]),
                    f"{selected['sample_count']}/{selected['equal_weight_avg_profit_pct']}",
                    f"{control['sample_count']}/{control['equal_weight_avg_profit_pct']}",
                    (
                        f"{selected_path['compounded_planned_budget_return_pct']}/"
                        f"{control_path['compounded_planned_budget_return_pct']}"
                    ),
                    (
                        f"{selected_path['avg_planned_budget_mae_pct']}/"
                        f"{control_path['avg_planned_budget_mae_pct']}"
                    ),
                    split["decision"],
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "The economic-selector entry cohort is identical across arms. Split legs use planned-capital fractions, a target repriced from the weighted average, no ordinary adverse-first stop, and one common 2% catastrophic stop from the initial entry. A fill bar cannot also hit the repriced target. Primary EV is measured against the full planned budget; deployed-notional EV is diagnostic only. Arm choice for a date uses complete outcomes from earlier dates only and has no runtime authority.",
        ]
    )
    lines.extend(
        [
            "",
            "## Equal-share carry-to-target widget execution replay",
            "",
            "| Venue | Selected arm | Calibration entries | Holdout dates/entries | Completed/censored | Completion ratio | Completed net avg | Same/cross-day | Median/max days | Avg/worst MAE | Max bundles/shares | Ending bundles/shares | Decision |",
            "| --- | --- | ---: | --- | --- | ---: | ---: | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for venue in base.COHORTS:
        carry = report["cohorts"][venue]["fixed_tp_equal_share_carry_replay"]
        selected = carry.get("selected_holdout_summary") or {}
        lines.append(
            "| "
            + " | ".join(
                [
                    venue,
                    str(carry.get("selected_arm")),
                    str(carry.get("calibration_entry_count")),
                    (
                        f"{carry.get('holdout_date_count')}/"
                        f"{carry.get('holdout_entry_count')}"
                    ),
                    (
                        f"{selected.get('completed_trade_count')}/"
                        f"{selected.get('right_censored_count')}"
                    ),
                    str(selected.get("target_completion_ratio")),
                    str(selected.get("completed_equal_weight_avg_profit_pct")),
                    (
                        f"{selected.get('same_day_target_count')}/"
                        f"{selected.get('cross_day_target_count')}"
                    ),
                    (
                        f"{selected.get('median_calendar_days_to_target')}/"
                        f"{selected.get('max_calendar_days_to_target')}"
                    ),
                    (
                        f"{selected.get('avg_observed_mae_pct')}/"
                        f"{selected.get('worst_observed_mae_pct')}"
                    ),
                    (
                        f"{selected.get('max_concurrent_bundle_count')}/"
                        f"{selected.get('max_concurrent_share_units')}"
                    ),
                    (
                        f"{selected.get('ending_open_bundle_count')}/"
                        f"{selected.get('ending_open_share_units')}"
                    ),
                    str(carry.get("decision")),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "Each execution leg is exactly one share and only one automated bundle may be active per symbol on a trade date. Calibration paths stop strictly before the six-date holdout begins; holdout outcomes cannot select the arm. Additional legs are allowed only in the original entry session. The runtime-candidate target is observed only until the daily reset; unhit positions become unmanaged inventory diagnostics and are never rewritten as zero-return wins or losses. This report does not itself authorize live orders or a widget policy change.",
        ]
    )
    lines.extend(
        [
            "",
            "## Fixed-execution entry catastrophic-risk quality nested OOS",
            "",
            "| Venue | OOS dates | Control n/EV | Selected n/EV | Control/Selected compounded | Control/Selected budget MAE | Control/Selected disaster stops | Retention | Skip disaster/non-disaster/profitable | AP/prevalence/Brier | Bounded exploration | Decision |",
            "| --- | ---: | --- | --- | --- | --- | --- | ---: | --- | --- | ---: | --- |",
        ]
    )
    for venue in base.COHORTS:
        quality = report["cohorts"][venue]["fixed_tp_split_entry_quality_walk_forward"]
        control = quality["control_summary_same_dates"]
        selected = quality["selected_summary"]
        control_path = quality["control_path_same_dates"]
        selected_path = quality["selected_path"]
        capacity = quality["capacity_diagnostics"]
        prediction = quality["prediction_diagnostics"]
        lines.append(
            "| "
            + " | ".join(
                [
                    venue,
                    str(quality["evaluation_count"]),
                    f"{control['sample_count']}/{control['equal_weight_avg_profit_pct']}",
                    f"{selected['sample_count']}/{selected['equal_weight_avg_profit_pct']}",
                    (
                        f"{control_path['compounded_planned_budget_return_pct']}/"
                        f"{selected_path['compounded_planned_budget_return_pct']}"
                    ),
                    (
                        f"{control_path['avg_planned_budget_mae_pct']}/"
                        f"{selected_path['avg_planned_budget_mae_pct']}"
                    ),
                    (
                        f"{control_path['catastrophic_stop_count']}/"
                        f"{selected_path['catastrophic_stop_count']}"
                    ),
                    str(capacity["selected_vs_control_retention"]),
                    (
                        f"{capacity['skipped_catastrophic_count']}/"
                        f"{capacity['skipped_noncatastrophic_count']}/"
                        f"{capacity['skipped_positive_return_count']}"
                    ),
                    (
                        f"{prediction['catastrophic_average_precision']}/"
                        f"{prediction['catastrophic_prevalence']}/"
                        f"{prediction['brier_score']}"
                    ),
                    str(capacity["bounded_exploration_enter_count"]),
                    quality["decision"],
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "The 40/60 add-at-0.8% and average-price +0.5% execution owner is fixed. Entry-time economic features and prior-only fixed-arm outcomes estimate catastrophic-loss-adjusted net EV; catastrophic probability alone never blocks an entry. Negative-EV skips are bounded so both each evaluation date and cumulative opportunity retention remain at least 75%. Skipped realized outcomes are post-OOS attribution only and cannot change the same-date model.",
        ]
    )
    lines.extend(
        [
            "",
            "## Broader-universe recoverable-basin direct-EV nested OOS",
            "",
            "| Venue | OOS dates | Broad control n/EV | Economic baseline n/EV | Basin selected n/EV | Broad/Economic/Selected compounded | Broad/Economic/Selected disaster | Retention | Skip profitable/disaster | Predicted/realized EV | MAE/correlation | Decision |",
            "| --- | ---: | --- | --- | --- | --- | --- | ---: | --- | --- | --- | --- |",
        ]
    )
    for venue in base.COHORTS:
        basin = report["cohorts"][venue]["recoverable_basin_entry_walk_forward"]
        broader = basin["broader_control_summary_same_dates"]
        economic = basin["economic_selected_baseline_summary_same_dates"]
        selected = basin["selected_summary"]
        paths = basin["path_diagnostics"]
        capacity = basin["capacity_diagnostics"]
        prediction = basin["prediction_diagnostics"]
        lines.append(
            "| "
            + " | ".join(
                [
                    venue,
                    str(basin["evaluation_count"]),
                    f"{broader['sample_count']}/{broader['equal_weight_avg_profit_pct']}",
                    f"{economic['sample_count']}/{economic['equal_weight_avg_profit_pct']}",
                    f"{selected['sample_count']}/{selected['equal_weight_avg_profit_pct']}",
                    "/".join(
                        str(paths[arm]["compounded_planned_budget_return_pct"])
                        for arm in (
                            "broader_control",
                            "economic_selected_baseline",
                            "recoverable_basin_selected",
                        )
                    ),
                    "/".join(
                        str(paths[arm]["catastrophic_stop_count"])
                        for arm in (
                            "broader_control",
                            "economic_selected_baseline",
                            "recoverable_basin_selected",
                        )
                    ),
                    str(capacity["selected_vs_broader_control_retention"]),
                    (
                        f"{capacity['skipped_positive_return_count']}/"
                        f"{capacity['skipped_catastrophic_count']}"
                    ),
                    (
                        f"{prediction['mean_predicted_ev_pct']}/"
                        f"{prediction['mean_realized_ev_pct']}"
                    ),
                    (
                        f"{prediction['mean_absolute_error_pct']}/"
                        f"{prediction['pearson_correlation']}"
                    ),
                    basin["decision"],
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "The candidate universe includes every causal armed candidate from model-ready economic lanes, not only economic-selected entries. Each candidate is independently labeled by the fixed 40/60 execution, while the executable state machine considers candidates chronologically, lets an entered position own its slot until fixed exit, and immediately reconsiders later candidates after a model skip. The direct-EV model and shrinkage use prior dates only. Three same-session entries earn at most one later negative-EV skip, so no future candidate count is needed for the 75% prefix retention guarantee.",
        ]
    )
    lines.extend(
        [
            "",
            "## Coarse parent-archetype prior-only attribution",
            "",
            "| Venue | OOS dates | Broad control n/EV | Economic baseline n/EV | Prior-axis selected n/EV | Broad/Economic/Selected compounded | Broad/Economic/Selected disaster rate | Retention | Selected axis dates | Mixed-parent dates | Decision |",
            "| --- | ---: | --- | --- | --- | --- | --- | ---: | --- | ---: | --- |",
        ]
    )
    for venue in base.COHORTS:
        parent = report["cohorts"][venue]["parent_bucket_entry_walk_forward"]
        broader = parent["broader_control_summary_same_dates"]
        economic = parent["economic_selected_baseline_summary_same_dates"]
        selected = parent["selected_summary"]
        paths = parent["path_diagnostics"]
        capacity = parent["capacity_diagnostics"]
        lines.append(
            "| "
            + " | ".join(
                [
                    venue,
                    str(parent["evaluation_count"]),
                    f"{broader['sample_count']}/{broader['equal_weight_avg_profit_pct']}",
                    f"{economic['sample_count']}/{economic['equal_weight_avg_profit_pct']}",
                    f"{selected['sample_count']}/{selected['equal_weight_avg_profit_pct']}",
                    "/".join(
                        str(paths[key]["compounded_planned_budget_return_pct"])
                        for key in (
                            "broader_control",
                            "economic_selected_baseline",
                            "prior_selected_parent_axis",
                        )
                    ),
                    "/".join(
                        str(paths[key]["catastrophic_stop_rate_pct"])
                        for key in (
                            "broader_control",
                            "economic_selected_baseline",
                            "prior_selected_parent_axis",
                        )
                    ),
                    str(capacity["selected_vs_broader_control_retention"]),
                    str(capacity["selected_axis_evaluation_counts"]),
                    str(
                        parent["conflict_diagnostics"][
                            "evaluation_with_mixed_parent_sign_count"
                        ]
                    ),
                    parent["decision"],
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "| Venue | Parent axis | OOS n/EV | Compounded | Budget MAE | Disaster stops |",
            "| --- | --- | --- | ---: | ---: | ---: |",
        ]
    )
    for venue in base.COHORTS:
        parent = report["cohorts"][venue]["parent_bucket_entry_walk_forward"]
        for axis, axis_row in parent["axis_summaries"].items():
            summary = axis_row["summary"]
            path = axis_row["path"]
            lines.append(
                "| "
                + " | ".join(
                    [
                        venue,
                        axis,
                        f"{summary['sample_count']}/{summary['equal_weight_avg_profit_pct']}",
                        str(path["compounded_planned_budget_return_pct"]),
                        str(path["avg_planned_budget_mae_pct"]),
                        str(path["catastrophic_stop_count"]),
                    ]
                )
                + " |"
            )
    lines.extend(
        [
            "",
            "| Venue | Prior-selected axis bucket | OOS n/EV | Win rate | Disaster stops |",
            "| --- | --- | --- | ---: | ---: |",
        ]
    )
    for venue in base.COHORTS:
        parent = report["cohorts"][venue]["parent_bucket_entry_walk_forward"]
        attribution = parent["conflict_diagnostics"]["selected_axis_bucket_attribution"]
        for key, row in attribution.items():
            lines.append(
                "| "
                + " | ".join(
                    [
                        venue,
                        key,
                        f"{row['sample_count']}/{row['equal_weight_avg_profit_pct']}",
                        str(row["diagnostic_win_rate_pct"]),
                        str(row["catastrophic_stop_count"]),
                    ]
                )
                + " |"
            )
    lines.extend(
        [
            "",
            "Each parent axis is evaluated independently; no multi-feature child combination owns a decision. Numeric tercile boundaries, bucket EV shrinkage, and the axis used on an evaluation date are all fitted from earlier dates only. Axis-wide summaries are diagnostic only. The executable comparison uses the prior-selected axis with the unchanged fixed 40/60 execution and the same prefix-safe 75% bounded-exploration contract.",
        ]
    )
    lines.extend(
        [
            "",
            "## Fixed parent conflict stability",
            "",
            "| Venue | Focus | n/dates | EV | Positive dates | First/second half EV | Rolling-positive ratio | Leave-one min/max/all-positive | Catastrophic loss share | Worst-date loss share | Decision |",
            "| --- | --- | --- | ---: | --- | --- | ---: | --- | ---: | ---: | --- |",
        ]
    )
    for venue in base.COHORTS:
        stability = report["cohorts"][venue]["parent_bucket_conflict_stability"]
        focus = stability["focus_summary"] or {}
        lines.append(
            "| "
            + " | ".join(
                [
                    venue,
                    stability["focus_key"],
                    f"{focus.get('sample_count')}/{focus.get('observed_date_count')}",
                    str(focus.get("equal_weight_avg_profit_pct")),
                    f"{focus.get('positive_date_count')}/{focus.get('positive_date_ratio')}",
                    f"{focus.get('first_half_ev_pct')}/{focus.get('second_half_ev_pct')}",
                    str(focus.get("rolling_positive_window_ratio")),
                    (
                        f"{focus.get('leave_one_date_min_ev_pct')}/"
                        f"{focus.get('leave_one_date_max_ev_pct')}/"
                        f"{focus.get('leave_one_date_all_positive')}"
                    ),
                    str(focus.get("catastrophic_negative_magnitude_share")),
                    str(focus.get("worst_date_negative_magnitude_share")),
                    stability["decision"],
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "| Venue | Focus date | n/EV | Simple sum | Win rate | Disaster stops |",
            "| --- | --- | --- | ---: | ---: | ---: |",
        ]
    )
    for venue in base.COHORTS:
        stability = report["cohorts"][venue]["parent_bucket_conflict_stability"]
        focus = stability["focus_summary"] or {}
        for row in focus.get("date_level") or []:
            lines.append(
                "| "
                + " | ".join(
                    [
                        venue,
                        str(row["trade_date"]),
                        f"{row['sample_count']}/{row['equal_weight_avg_profit_pct']}",
                        str(row["simple_sum_profit_pct"]),
                        str(row["diagnostic_win_rate_pct"]),
                        str(row["catastrophic_stop_count"]),
                    ]
                )
                + " |"
            )
    lines.extend(
        [
            "",
            "This section consumes the already completed prior-selected parent decisions without refitting any boundary, bucket, axis, entry action, or execution owner. Rolling, leave-one-date, and concentration metrics are post-OOS diagnostics only. The predeclared volatility-middle focus cannot become a same-sample hard gate or runtime candidate.",
        ]
    )
    lines.extend(
        [
            "",
            "## Fixed parent catastrophic pre-entry episode audit",
            "",
            "| Venue | Focus decisions/EV | Catastrophic/target/session-close | Source gaps | Context available | Distribution shifts | Retention-safe signatures | Lane signature | Decision |",
            "| --- | --- | --- | ---: | --- | --- | --- | --- | --- |",
        ]
    )
    for venue in base.COHORTS:
        audit = report["cohorts"][venue]["parent_catastrophic_episode_audit"]
        counts = audit["episode_counts"]
        lines.append(
            "| "
            + " | ".join(
                [
                    venue,
                    (
                        f"{audit['input_focus_decision_count']}/"
                        f"{audit['focus_source_quality_adjusted_ev_pct']}"
                    ),
                    (
                        f"{counts['catastrophic_stop']}/"
                        f"{counts['target_recovery']}/"
                        f"{counts['session_close_other']}"
                    ),
                    str(audit["source_gap_count"]),
                    str(audit["market_context_available_counts"]),
                    ", ".join(audit["numeric_distribution_shift_candidates"]) or "none",
                    ", ".join(audit["numeric_signature_candidates"]) or "none",
                    str(audit["lane_summary"]["signature_candidate"]),
                    audit["decision"],
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "| Venue | Feature | Cat median | Target median | Direction/probability | Same-side catastrophic | Leave-one minimum | Target retention | Shift/signature |",
            "| --- | --- | ---: | ---: | --- | ---: | ---: | ---: | --- |",
        ]
    )
    for venue in base.COHORTS:
        audit = report["cohorts"][venue]["parent_catastrophic_episode_audit"]
        ranked_features = sorted(
            audit["numeric_feature_summaries"].items(),
            key=lambda item: float(item[1].get("direction_pair_probability") or 0.0),
            reverse=True,
        )
        for feature_name, summary in ranked_features:
            if not summary["comparison_available"]:
                continue
            lines.append(
                "| "
                + " | ".join(
                    [
                        venue,
                        feature_name,
                        str(summary["catastrophic_median"]),
                        str(summary["target_recovery_median"]),
                        (
                            f"{summary['direction']}/"
                            f"{summary['direction_pair_probability']}"
                        ),
                        (
                            f"{summary['catastrophic_same_side_of_target_median_count']}"
                            f"/{summary['catastrophic_count']}"
                        ),
                        str(
                            summary["leave_one_catastrophic_min_direction_probability"]
                        ),
                        str(
                            summary[
                                "target_recovery_retention_if_signature_side_excluded"
                            ]
                        ),
                        (
                            f"{summary['distribution_shift_candidate']}/"
                            f"{summary['signature_candidate']}"
                        ),
                    ]
                )
                + " |"
            )
    lines.extend(
        [
            "",
            "| Venue | Outcome | Entry | Lane | Return | Context |",
            "| --- | --- | --- | --- | ---: | --- |",
        ]
    )
    for venue in base.COHORTS:
        audit = report["cohorts"][venue]["parent_catastrophic_episode_audit"]
        for episode in audit["episodes"]:
            if episode["outcome_class"] != "catastrophic_stop":
                continue
            lines.append(
                "| "
                + " | ".join(
                    [
                        venue,
                        episode["outcome_class"],
                        episode["entry_at"],
                        episode["pairability_lane"],
                        str(episode["planned_budget_return_pct"]),
                        str(episode["provenance"]["market_context_available"]),
                    ]
                )
                + " |"
            )
    lines.extend(
        [
            "",
            "The audit joins unchanged fixed-parent entry identities to their original causal candidate and completed bars immediately preceding entry. Outcome labels only define the comparison groups. No post-entry MFE, MAE, low, high, or exit value is used as a feature. Each diagnostic dimension stands alone; a signature candidate is future-date research input only and cannot become a same-sample hard gate, runtime policy, or order authority.",
        ]
    )
    lines.extend(
        [
            "",
            "## Fixed catastrophic-stop recovery path",
            "",
            "| Venue | Episodes | Stop control EV/compounded | Continue EV/compounded | Target recovery | Continue better/Stop protected | Recovery by 1/3/5/10/20/30/60m | Source gaps/terminal limited | Evidence complete | Decision |",
            "| --- | ---: | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for venue in base.COHORTS:
        recovery = report["cohorts"][venue]["parent_catastrophic_stop_recovery_path"]
        lines.append(
            "| "
            + " | ".join(
                [
                    venue,
                    str(recovery["episode_count"]),
                    (
                        f"{recovery['hard_stop_control_source_quality_adjusted_ev_pct']}"
                        f"/{recovery['hard_stop_control_compounded_return_pct']}"
                    ),
                    (
                        f"{recovery['continue_target_or_terminal_mark_source_quality_adjusted_ev_pct']}"
                        f"/{recovery['continue_target_or_terminal_mark_compounded_return_pct']}"
                    ),
                    (
                        f"{recovery['target_recovery_count']}/"
                        f"{recovery['target_recovery_ratio']}"
                    ),
                    (
                        f"{recovery['continuation_better_count']}/"
                        f"{recovery['hard_stop_protected_count']}"
                    ),
                    "/".join(
                        str(recovery["recovery_by_horizon_count"][str(minutes)])
                        for minutes in PARENT_POST_STOP_HORIZONS_MINUTES
                    ),
                    (
                        f"{recovery['source_gap_count']}/"
                        f"{recovery['terminal_mark_limited_count']}"
                    ),
                    str(recovery["decision_evidence_complete"]),
                    recovery["decision"],
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "| Venue | Entry/Stop | Stop return | Continued exit/reason/return | Target hit minutes | Additional drawdown/Rebound from stop | Terminal mark/time/exact-close |",
            "| --- | --- | ---: | --- | ---: | --- | ---: |",
        ]
    )
    for venue in base.COHORTS:
        recovery = report["cohorts"][venue]["parent_catastrophic_stop_recovery_path"]
        for episode in recovery["episodes"]:
            lines.append(
                "| "
                + " | ".join(
                    [
                        venue,
                        f"{episode['entry_at']}/{episode['stop_at']}",
                        str(episode["hard_stop_control_return_pct"]),
                        (
                            f"{episode['continuation_exit_at']}/"
                            f"{episode['continuation_exit_reason']}/"
                            f"{episode['continue_target_or_terminal_mark_return_pct']}"
                        ),
                        str(episode["target_recovery_first_hit_minutes"]),
                        (
                            f"{episode['additional_drawdown_from_stop_price_pct']}"
                            f"/{episode['maximum_rebound_from_stop_price_pct']}"
                        ),
                        (
                            f"{episode['terminal_observation_return_pct']}/"
                            f"{episode['terminal_observation_at']}/"
                            f"{episode['terminal_observation_exact_session_close']}"
                        ),
                    ]
                )
                + " |"
            )
    lines.extend(
        [
            "",
            "The stop-bar itself is excluded because intrabar high/low order after the stop fill is unknowable. The hard-stop control and same-quantity continuation counterfactual are reported separately and never summed. A KRX terminal mark before 15:30 is diagnostic only, makes continuation source-quality-adjusted EV unavailable for a non-target episode, and cannot support an owner change. Post-stop paths are execution outcomes only, not entry features or same-sample stop-removal authority.",
        ]
    )
    lines.extend(
        [
            "",
            "## Fixed post-stop bounded grace arms",
            "",
            "| Venue | Grace | Episodes | EV/adjusted EV/compounded | Target recovered | Improved/Worsened/Equal | Avg/Worst conservative additional MAE | Prospective only |",
            "| --- | ---: | ---: | --- | ---: | --- | --- | --- |",
        ]
    )
    for venue in base.COHORTS:
        grace = report["cohorts"][venue]["parent_post_stop_bounded_grace_arms"]
        for minutes in PARENT_POST_STOP_GRACE_HORIZONS_MINUTES:
            arm = grace["arms"][str(minutes)]
            lines.append(
                "| "
                + " | ".join(
                    [
                        venue,
                        str(minutes),
                        str(arm["episode_count"]),
                        (
                            f"{arm['equal_weight_avg_profit_pct']}/"
                            f"{arm['source_quality_adjusted_ev_pct']}/"
                            f"{arm['compounded_return_pct']}"
                        ),
                        str(arm["target_recovery_count"]),
                        (
                            f"{arm['improved_episode_count']}/"
                            f"{arm['worsened_episode_count']}/"
                            f"{arm['equal_episode_count']}"
                        ),
                        (
                            f"{arm['average_additional_mae_from_stop_pct_conservative']}/"
                            f"{arm['worst_additional_mae_from_stop_pct_conservative']}"
                        ),
                        str(arm["prospective_candidate_only"]),
                    ]
                )
                + " |"
            )
    lines.extend(
        [
            "",
            "| Venue | Control EV/compounded | Candidate horizons | Same-sample best selected | Source gaps | Decision |",
            "| --- | --- | --- | --- | ---: | --- |",
        ]
    )
    for venue in base.COHORTS:
        grace = report["cohorts"][venue]["parent_post_stop_bounded_grace_arms"]
        lines.append(
            "| "
            + " | ".join(
                [
                    venue,
                    (
                        f"{grace['hard_stop_control_equal_weight_avg_profit_pct']}/"
                        f"{grace['hard_stop_control_compounded_return_pct']}"
                    ),
                    str(grace["prospective_candidate_horizons_minutes"]),
                    str(grace["same_sample_best_arm_selected"]),
                    str(grace["source_gap_count"]),
                    grace["decision"],
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "| Venue | Grace | Trade date | Exit/reason | Grace return | Delta vs stop | Conservative additional MAE |",
            "| --- | ---: | --- | --- | ---: | ---: | ---: |",
        ]
    )
    for venue in base.COHORTS:
        grace = report["cohorts"][venue]["parent_post_stop_bounded_grace_arms"]
        for minutes in PARENT_POST_STOP_GRACE_HORIZONS_MINUTES:
            for episode in grace["arms"][str(minutes)]["episodes"]:
                lines.append(
                    "| "
                    + " | ".join(
                        [
                            venue,
                            str(minutes),
                            str(episode["trade_date"]),
                            f"{episode['exit_at']}/{episode['exit_reason']}",
                            str(episode["grace_planned_budget_return_pct"]),
                            str(episode["incremental_return_vs_hard_stop_pct"]),
                            str(episode["additional_mae_from_stop_pct_conservative"]),
                        ]
                    )
                    + " |"
                )
    lines.extend(
        [
            "",
            "Each 5/10/20-minute arm starts strictly after the catastrophic-stop bar, retains the existing filled quantity and average-price target, and exits at the target if it is hit first or at the exact completed horizon-bar close. Additional MAE includes the target-hit bar as a conservative intrabar envelope; the known pre-target-bar MAE remains available per episode. Arms are never summed or ranked into a same-sample winner. Any improving horizon is prospective attribution only and has no runtime, order, quantity, target, emergency-floor, provider, or bot authority.",
        ]
    )
    lines.extend(
        [
            "",
            "## Fixed grace prospective OOS attribution",
            "",
            "| Venue | Frozen at/Start | Calibration excluded/New OOS | Control EV/compounded | Source gaps | Decision |",
            "| --- | --- | --- | --- | ---: | --- |",
        ]
    )
    for venue in base.COHORTS:
        prospective = report["cohorts"][venue]["parent_post_stop_grace_prospective_oos"]
        lines.append(
            "| "
            + " | ".join(
                [
                    venue,
                    (
                        f"{prospective['candidate_horizons_frozen_at']}/"
                        f"{prospective['prospective_start_date']}"
                    ),
                    (
                        f"{prospective['calibration_episode_count_excluded']}/"
                        f"{prospective['prospective_episode_count']}"
                    ),
                    (
                        f"{prospective['hard_stop_control_equal_weight_avg_profit_pct']}/"
                        f"{prospective['hard_stop_control_compounded_return_pct']}"
                    ),
                    str(prospective["source_gap_count"]),
                    prospective["decision"],
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "| Venue | Grace | New OOS | EV/adjusted EV/compounded | Target recovered | Improved/Worsened | Avg/Worst conservative additional MAE |",
            "| --- | ---: | ---: | --- | ---: | --- | --- |",
        ]
    )
    for venue in base.COHORTS:
        prospective = report["cohorts"][venue]["parent_post_stop_grace_prospective_oos"]
        for minutes in PARENT_POST_STOP_GRACE_HORIZONS_MINUTES:
            arm = prospective["arms"][str(minutes)]
            lines.append(
                "| "
                + " | ".join(
                    [
                        venue,
                        str(minutes),
                        str(arm["prospective_episode_count"]),
                        (
                            f"{arm['equal_weight_avg_profit_pct']}/"
                            f"{arm['source_quality_adjusted_ev_pct']}/"
                            f"{arm['compounded_return_pct']}"
                        ),
                        str(arm["target_recovery_count"]),
                        (
                            f"{arm['improved_episode_count']}/"
                            f"{arm['worsened_episode_count']}"
                        ),
                        (
                            f"{arm['average_additional_mae_from_stop_pct_conservative']}/"
                            f"{arm['worst_additional_mae_from_stop_pct_conservative']}"
                        ),
                    ]
                )
                + " |"
            )
    lines.extend(
        [
            "",
            "The candidate horizons are frozen from the report ending 2026-08-10. Episodes through that date are counted only as excluded calibration provenance and never enter prospective EV. Zero new catastrophic episodes is a valid observe state with null EV, not a zero-return result. Prospective outcomes cannot select a same-sample winner or acquire runtime/order authority.",
        ]
    )
    lines.extend(
        [
            "",
            "## Opportunity-density cost sensitivity",
            "",
            "| Venue | Round-trip cost | Oracle trades | Oracle avg/day | Oracle avg net/trade |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for venue in base.COHORTS:
        for row in report["oracle_cost_sensitivity"][venue]:
            lines.append(
                "| "
                + " | ".join(
                    [
                        venue,
                        str(row["round_trip_cost_pct"]),
                        str(row["oracle_trade_count"]),
                        str(row["avg_oracle_trades_per_date"]),
                        str(row["equal_weight_avg_profit_pct"]),
                    ]
                )
                + " |"
            )
    lines.extend(
        [
            "",
            "This sensitivity table is still perfect-foresight evidence. Its purpose is only to test whether cost-bearing price movement exists after progressively larger execution-cost assumptions.",
            "",
            "## Two-sided transition completion diagnostic",
            "",
            "| Venue | Buy then sell transition completed | Completed-pair net EV | Completed-pair win rate | Prior-duration expiry exits |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for venue in base.COHORTS:
        walk = report["cohorts"][venue]["walk_forward"]
        completed = walk["confidence_diagnostics"]["top_slices"]["top_100pct"]
        exits = walk["out_of_sample_summary"].get("exit_reason_counts", {})
        lines.append(
            "| "
            + " | ".join(
                [
                    venue,
                    str(completed["sample_count"]),
                    str(completed["equal_weight_avg_profit_pct"]),
                    str(completed["diagnostic_win_rate_pct"]),
                    str(exits.get("prior_duration_cap_next_open", 0)),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "The oracle is an unattainable ex-post ceiling, not a strategy result. Average precision must be compared with oracle-action prevalence; OOS net EV is the executable next-open diagnostic. Future prices never enter classifier features or same-day training.",
            "A completed two-sided pair is known only after its sell transition occurs. Its positive diagnostic EV cannot be used at entry. The nested pairability section tests a prior-only predictor and must retain its reported negative result when it fails to make execution EV positive.",
            "",
        ]
    )
    return "\n".join(lines)


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def write_report(
    report: dict[str, Any], *, output_dir: Path = DEFAULT_OUTPUT_DIR
) -> tuple[Path, Path]:
    stem = f"pure_market_adaptive_opportunity_replay_{report['data_start_date']}_{report['data_end_date']}"
    json_path = output_dir / f"{stem}.json"
    markdown_path = output_dir / f"{stem}.md"
    _atomic_write(
        json_path,
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    _atomic_write(markdown_path, render_markdown(report))
    return json_path, markdown_path


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-date", required=True)
    parser.add_argument("--end-date", required=True)
    parser.add_argument("--market-dir", type=Path, default=base.DEFAULT_MARKET_DIR)
    parser.add_argument("--training-days", type=int, default=20)
    parser.add_argument("--round-trip-cost-pct", type=float, default=0.20)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--write", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    start_date = date.fromisoformat(args.start_date)
    end_date = date.fromisoformat(args.end_date)
    if start_date < base.CLEAN_TUNING_BASELINE_DATE:
        raise SystemExit("start-date precedes clean tuning baseline 2026-06-05")
    if end_date >= datetime.now(KST).date():
        raise SystemExit("end-date must be a fully completed prior KST trading date")
    stock_bars, stock_quality = base.load_market_bars(
        market_paths=sorted(args.market_dir.glob("samsung_1m_*.jsonl")),
        widget_observation_dir=None,
        start_date=start_date,
        end_date=end_date,
    )
    kospi_bars, kospi_quality = regime.load_kospi_bars(
        sorted(args.market_dir.glob("kospi_1m_*.jsonl")),
        start_date=start_date,
        end_date=end_date,
    )
    if not stock_bars or not kospi_bars:
        raise SystemExit("complete Samsung and KOSPI market backfills are required")
    report = build_report(
        stock_bars,
        kospi_bars,
        stock_source_quality=stock_quality,
        kospi_source_quality=kospi_quality,
        training_days=max(1, args.training_days),
        cost_pct=max(0.0, args.round_trip_cost_pct),
    )
    if args.write:
        json_path, markdown_path = write_report(report, output_dir=args.output_dir)
        print(
            json.dumps(
                {
                    "status": "complete",
                    "json_path": str(json_path),
                    "markdown_path": str(markdown_path),
                    "decision": report["decision"],
                    "runtime_effect": False,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
