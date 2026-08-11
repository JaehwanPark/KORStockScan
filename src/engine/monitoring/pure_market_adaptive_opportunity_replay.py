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
from sklearn.metrics import average_precision_score

from src.engine.monitoring import pure_market_regime_replay as regime
from src.engine.monitoring import pure_market_reversal_replay as base

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
    if krx_wait_budget_decision == "wait_budget_oos_positive":
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
        "schema": "pure_market_adaptive_opportunity_replay_v12",
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
