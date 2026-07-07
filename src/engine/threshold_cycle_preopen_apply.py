"""Build a preopen threshold apply manifest from the latest postclose report."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
from datetime import date, datetime
from pathlib import Path
from typing import Any

from src.engine.auto_promotion_contracts import tier2_validation_passed
from src.engine.approval_contracts import annotate_approval_request
from src.engine.daily_threshold_cycle_report import REPORT_DIR
from src.engine.runtime_apply_bridge import (
    ARCHIVED_RUNTIME_APPLY_BRIDGE_FAMILIES,
    ENTRY_BRIDGE_FAMILY,
    GREENFIELD_REAL_ENV_FAMILY,
    SCALE_IN_BRIDGE_FAMILY,
    ldm_entry_runtime_bridge_artifact_path,
    ldm_scale_in_runtime_bridge_artifact_path,
    runtime_apply_bridge_report_path,
    validate_greenfield_policy_file,
)
from src.engine.scalping.scalp_sim_auto_approval_control_tower import (
    scalp_sim_auto_approval_path,
    scalp_sim_policy_catalog_path,
)
from src.engine.monitoring import rising_missed_classifier_prior
from src.engine.scalping import scalp_sim_auto_approval_control_tower
from src.engine import lifecycle_bucket_discovery
from src.engine.automation.source_quality_hard_gate import (
    load_source_quality_preflight,
    source_quality_preflight_blocked,
)
from src.engine.lifecycle_bucket_discovery import (
    bucket_catalog_path,
    discovery_report_path,
    sim_auto_approval_path,
)
from src.engine.swing.sim_auto_approval_control_tower import (
    swing_sim_auto_approval_path,
    swing_sim_policy_catalog_path,
)
from src.utils.constants import DATA_DIR


APPLY_PLAN_DIR = DATA_DIR / "threshold_cycle" / "apply_plans"
RUNTIME_ENV_DIR = DATA_DIR / "threshold_cycle" / "runtime_env"
OPERATOR_RUNTIME_ENV_LOCK_DIR = DATA_DIR / "threshold_cycle" / "operator_runtime_env_locks"
AI_REVIEW_DIR = REPORT_DIR / "threshold_cycle_ai_review"
CALIBRATION_REPORT_DIR = REPORT_DIR / "threshold_cycle_calibration"
SWING_RUNTIME_APPROVAL_REPORT_DIR = DATA_DIR / "report" / "swing_runtime_approval"
SWING_RUNTIME_APPROVAL_ARTIFACT_DIR = DATA_DIR / "threshold_cycle" / "approvals"
LATENCY_CLASSIFIER_RECOMMENDATION_DIR = DATA_DIR / "report" / "latency_classifier_recommendation"
RISING_MISSED_FIRST_TOUCH_CALIBRATION_DIR = (
    DATA_DIR / "report" / "rising_missed_first_touch_calibration"
)
SCALPING_PYRAMID_QUALITY_CALIBRATION_DIR = (
    DATA_DIR / "report" / "scalping_pyramid_quality_calibration"
)
AI_SCORE_OPTIMIZATION_BACKTEST_DIR = DATA_DIR / "report" / "ai_score_optimization_backtest"
RUNTIME_GAP_PROVENANCE_DIR = DATA_DIR / "threshold_cycle" / "runtime_gap_provenance"
ENTRY_CANCEL_WAIT_TUNING_DIR = DATA_DIR / "report" / "entry_cancel_wait_tuning"
ENTRY_CANCEL_WAIT_FAMILY = "entry_cancel_wait_runtime"
ENTRY_CANCEL_WAIT_ACTIVATION_DATE = "2026-06-15"

AUTO_APPLY_MODES = {"auto_bounded_live"}
AUTO_APPLY_ALLOWED_STATES = {"adjust_up", "adjust_down"}
AUTO_APPLY_BLOCK_STATES = {"freeze", "hold_sample", "hold_no_edge"}
HOLD_SUB_STATES = frozenset({"hold", "hold_sample", "hold_no_edge"})
HOLD_CARRY_FORWARD_STATES = frozenset({"hold"})
AUTO_APPLY_ROUTE_EXCLUDE_ACTIONS = {"exclude_from_threshold_candidate_review"}
AUTO_APPLY_ALLOWED_ROUTES = {"threshold_candidate", "normal_drift", ""}
NON_LIVE_SELECTABLE_FAMILIES = {
    "panic_lifecycle_actuator",
    "panic_entry_freeze_guard",
    "panic_buy_runner_tp_canary",
}
REMOVED_RUNTIME_ENV_KEYS = {
    "KORSTOCKSCAN_SCALPING_INITIAL_ENTRY_QTY_CAP_ENABLED",
    "KORSTOCKSCAN_SCALPING_INITIAL_ENTRY_MAX_QTY",
    "KORSTOCKSCAN_SCALPING_SCALE_IN_EFFECTIVE_QTY_CAP",
    "KORSTOCKSCAN_WAIT6579_PROBE_CANARY_MAX_BUDGET_KRW",
    "KORSTOCKSCAN_WAIT6579_PROBE_CANARY_MAX_QTY",
}
REMOVED_TARGET_ENV_KEYS = {
    key.removeprefix("KORSTOCKSCAN_")
    for key in REMOVED_RUNTIME_ENV_KEYS
}
REMOVED_CALIBRATION_FAMILIES = {
    "position_sizing_cap_release",
}
ACTIVE_SIM_PRIORITY_OBSERVABLE_PREFIX_KEYS = {
    "entry_score_parent",
    "entry_source_parent",
    "submit_quality_parent",
}
SCALP_SIM_POLICY_STALENESS_CHECK_FILES = (
    Path(lifecycle_bucket_discovery.__file__),
    Path(rising_missed_classifier_prior.__file__),
    Path(scalp_sim_auto_approval_control_tower.__file__),
)
LOCK_ALLOWED_CLOSE_KEYWORDS = {
    "safety_revert",
    "severe_loss",
    "order_provenance",
    "provenance_breach",
    "stale_quote",
    "stale_context_or_quote",
    "hard_stop",
    "protect_stop",
    "emergency_stop",
    "order_failure",
    "receipt_missing",
}
HOLD_CARRY_FORWARD_BLOCK_REASON_KEYS: dict[str, frozenset[str]] = {
    "source_quality_hard_block": frozenset({"source_quality_blocked", "source_quality_blocker"}),
    "severe_loss_guard": frozenset({"severe_loss", "excessive_drawdown"}),
    "order_provenance_breach": frozenset({"provenance_breach", "order_provenance", "order_failure"}),
    "same_stage_owner_conflict": frozenset({"same_stage_owner_conflict"}),
}
RETIRED_RUNTIME_FAMILY_REASONS = {
    "aggressive_entry_price_override_runtime": (
        "retired_runtime_family:entry_price_gap_profile_and_quote_consistency_own_entry_price"
    ),
    "soft_stop_dynamic_grace_runtime": (
        "retired_runtime_family:soft_stop_whipsaw_confirmation_owns_soft_stop_deferral"
    ),
    "preset_tp_soft_stop_runtime": (
        "retired_runtime_family:formal_holding_exit_owner_supersedes_preset_tp_soft_stop_override"
    ),
    "late_entry_price_drift_guard_runtime": (
        "retired_runtime_family:weak_context_late_entry_guard_and_quote_consistency_own_late_entry_drift"
    ),
}

TARGET_ENV_VALUE_KEYS = {
    "SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_ENABLED": "enabled",
    "SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_SEC": "confirm_sec",
    "SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_BUFFER_PCT": "buffer_pct",
    "SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_MAX_WORSEN_PCT": "max_worsen_pct",
    "AI_SCORE65_74_RECOVERY_PROBE_ENABLED": "enabled",
    "AI_SCORE65_74_RECOVERY_PROBE_MIN_SCORE": "min_score",
    "AI_SCORE65_74_RECOVERY_PROBE_MAX_SCORE": "max_score",
    "AI_SCORE65_74_RECOVERY_PROBE_MIN_BUY_PRESSURE": "min_buy_pressure",
    "AI_SCORE65_74_RECOVERY_PROBE_MIN_TICK_ACCEL": "min_tick_accel",
    "AI_SCORE65_74_RECOVERY_PROBE_MIN_MICRO_VWAP_BP": "min_micro_vwap_bp",
    "AI_SCORE65_74_RECOVERY_PROBE_EFFECTIVE_MIN_MICRO_VWAP_FLOOR_BP": "effective_min_micro_vwap_floor_bp",
    "AI_SCORE65_74_RECOVERY_PROBE_THRESHOLD_VERSION": "threshold_version",
    "AI_SCORE65_74_RECOVERY_PROBE_CALIBRATION_STATE": "calibration_state",
    "AI_WAIT6579_PROBE_CANARY_MAX_BUDGET_KRW": "max_budget_krw",
    "AI_WAIT6579_PROBE_CANARY_MAX_QTY": "max_qty",
    "SCALP_FIRST_TOUCH_AVGDOWN_MIN_AI_SUPPORT": "min_ai_support",
    "SCALP_FIRST_TOUCH_AVGDOWN_MIN_AI_MODERATE": "min_ai_moderate",
    "SCALP_FIRST_TOUCH_AVGDOWN_MIN_PRIOR_PEAK_PCT": "min_prior_peak_pct",
    "SCALP_FIRST_TOUCH_AVGDOWN_MAX_REPEATED_BLOCKERS_WITHOUT_SUPPORT": "max_repeated_blockers_without_support",
    "SCALP_FIRST_TOUCH_AVGDOWN_LOW_AI_BLOCK": "low_ai_block",
    "SCALP_FIRST_TOUCH_AVGDOWN_MAX_SPREAD_BPS": "max_spread_bps",
    "SCALPING_PYRAMID_MIN_PROFIT_PCT": "min_profit_pct",
    "SCALPING_PYRAMID_MIN_AI_SCORE": "min_ai_score",
    "SCALPING_PYRAMID_MIN_BUY_PRESSURE": "min_buy_pressure",
    "SCALPING_PYRAMID_MIN_TICK_ACCEL": "min_tick_accel",
    "SCALPING_PYRAMID_MAX_MICRO_VWAP_BPS": "max_micro_vwap_bps",
    "SCALPING_PYRAMID_MAX_SPREAD_BPS": "max_spread_bps",
    "SCALPING_PYRAMID_STRONG_CONTINUATION_ENABLED": "strong_continuation_enabled",
    "SCALPING_PYRAMID_STRONG_CONTINUATION_MIN_PROFIT_PCT": "strong_continuation_min_profit_pct",
    "SCALPING_PYRAMID_STRONG_CONTINUATION_MAX_DRAWDOWN_PCT": "strong_continuation_max_drawdown_pct",
    "SCALPING_ENABLE_PYRAMID": "scalping_enable_pyramid",
    "REVERSAL_ADD_MIN_AI_SCORE": "reversal_add_min_ai_score",
    "REVERSAL_ADD_MIN_BUY_PRESSURE": "reversal_add_min_buy_pressure",
    "REVERSAL_ADD_MIN_TICK_ACCEL": "reversal_add_min_tick_accel",
    "SCALP_BAD_ENTRY_REFINED_CANARY_ENABLED": "enabled",
    "ENTRY_OPPORTUNITY_RECHECK_ENABLED": "enabled",
    "ENTRY_OPPORTUNITY_RECHECK_MIN_AI_SCORE": "min_ai_score",
    "ENTRY_OPPORTUNITY_RECHECK_MAX_AI_SCORE": "max_ai_score",
    "ENTRY_OPPORTUNITY_RECHECK_MAX_RECHECK_PER_SYMBOL": "max_recheck_per_symbol",
    "ENTRY_OPPORTUNITY_RECHECK_MAX_DAILY_RECHECK": "max_daily_recheck",
    "ENTRY_OPPORTUNITY_RECHECK_MAX_DAILY_BUY_RECOVERY": "max_daily_buy_recovery",
    "ENTRY_OPPORTUNITY_RECHECK_MAX_WS_AGE_MS": "max_ws_age_ms",
    "ENTRY_OPPORTUNITY_RECHECK_FORBID_DANGER": "forbid_danger",
    "ENTRY_OPPORTUNITY_RECHECK_REQUIRE_FRESH_QUOTE": "require_fresh_quote",
    "ENTRY_OPPORTUNITY_RECHECK_REQUIRE_EXPLICIT_BUY_ACTION": "require_explicit_buy_action",
    "SCALP_BAD_ENTRY_REFINED_MIN_HOLD_SEC": "min_hold_sec",
    "SCALP_BAD_ENTRY_REFINED_MIN_LOSS_PCT": "min_loss_pct",
    "SCALP_BAD_ENTRY_REFINED_MAX_PEAK_PROFIT_PCT": "max_peak_profit_pct",
    "SCALP_BAD_ENTRY_REFINED_AI_SCORE_LIMIT": "ai_score_limit",
    "SCALP_BAD_ENTRY_REFINED_RECOVERY_PROB_MAX": "recovery_prob_max",
    "OFI_AI_SMOOTHING_STALE_THRESHOLD_MS": "ofi_stale_threshold_ms",
    "OFI_AI_SMOOTHING_PERSISTENCE_REQUIRED": "ofi_persistence_required",
    "HOLDING_FLOW_OFI_BEARISH_CONFIRM_WORSEN_PCT": "holding_bearish_confirm_worsen_pct",
    "HOLDING_FLOW_OVERRIDE_MAX_DEFER_SEC": "max_defer_sec",
    "HOLDING_FLOW_OVERRIDE_WORSEN_PCT": "worsen_floor_pct",
    "SCALP_PROTECT_TRAILING_SMOOTH_WINDOW_SEC": "window_sec",
    "SCALP_PROTECT_TRAILING_SMOOTH_MIN_SPAN_SEC": "min_span_sec",
    "SCALP_PROTECT_TRAILING_SMOOTH_MIN_SAMPLES": "min_samples",
    "SCALP_PROTECT_TRAILING_SMOOTH_BELOW_RATIO": "below_ratio",
    "SCALP_PROTECT_TRAILING_SMOOTH_BUFFER_PCT": "buffer_pct",
    "SCALP_PROTECT_TRAILING_EMERGENCY_PCT": "emergency_pct",
    "SWING_FLOOR_BULL": "floor_bull",
    "SWING_FLOOR_BEAR": "floor_bear",
    "SWING_SELECTION_TOP_K": "top_k",
    "ML_GATEKEEPER_REJECT_COOLDOWN": "reject_cooldown_sec",
    "SWING_MARKET_REGIME_SENSITIVITY": "regime_sensitivity",
    "SCALP_ENTRY_LATENCY_MAX_WS_AGE_MS_FOR_CAUTION": "max_ws_age_ms_for_caution",
    "SCALP_ENTRY_LATENCY_MAX_WS_JITTER_MS_FOR_CAUTION": "max_ws_jitter_ms_for_caution",
    "SCALP_ENTRY_LATENCY_MAX_SPREAD_RATIO_FOR_CAUTION": "max_spread_ratio_for_caution",
    "SCALP_LATENCY_SUBMIT_RECOVERY_CANARY_ENABLED": "recovery_enabled",
    "SCALP_LATENCY_SUBMIT_RECOVERY_MIN_SIGNAL_SCORE": "recovery_min_signal_score",
    "SCALP_LATENCY_SUBMIT_RECOVERY_MAX_WS_AGE_MS": "recovery_max_ws_age_ms",
    "SCALP_LATENCY_SUBMIT_RECOVERY_MAX_WS_JITTER_MS": "recovery_max_ws_jitter_ms",
    "SCALP_LATENCY_SUBMIT_RECOVERY_MAX_SPREAD_RATIO": "recovery_max_spread_ratio",
    "SCALPING_ENTRY_PRICE_RESOLVER_ENABLED": "enabled",
    "SCALPING_ENTRY_PRICE_RESOLVER_MAX_BELOW_BID_BPS": "max_below_bid_bps",
    "SCALPING_NORMAL_DEFENSIVE_TICKS": "normal_defensive_ticks",
    "SCALPING_NORMAL_DEFENSIVE_BPS": "normal_defensive_bps",
    "SCALPING_CONDITIONAL_STRONG_DEFENSIVE_BPS": "conditional_strong_defensive_bps",
    "SCALPING_NORMAL_FAVORABLE_DEFENSIVE_BPS": "normal_favorable_defensive_bps",
    "SCALPING_NORMAL_WEAK_DEFENSIVE_BPS": "normal_weak_defensive_bps",
    "SCALPING_CONDITIONAL_1TICK_REAL_ENABLED": "conditional_1tick_real_enabled",
    "SCALP_AGGRESSIVE_ENTRY_PRICE_OVERRIDE_ENABLED": "enabled",
    "SCALP_AGGRESSIVE_ENTRY_PRICE_OVERRIDE_TYPES": "types",
    "SCALP_SCANNER_REAL_SOURCE_GUARD_ENABLED": "enabled",
    "SCALP_SCANNER_REAL_SOURCE_GUARD_BLOCK_VALUE_TOP_ONLY": "block_value_top_only",
    "SCALP_SCANNER_REAL_SOURCE_GUARD_MAX_DECLINE_PCT": "max_decline_pct",
    "SCALP_SCANNER_REAL_SOURCE_GUARD_BLOCK_LATE_FIRST_SEEN": "block_late_first_seen",
    "SCALP_SCANNER_ACCEL_MIN_RANK_JUMP": "accel_min_rank_jump",
    "SCALP_SCANNER_ACCEL_MIN_SPIKE_RATE": "accel_min_spike_rate",
    "SCALP_SCANNER_ACCEL_MIN_PRIORITY_SCORE": "accel_min_priority_score",
    "SCALP_SCANNER_ACCEL_MIN_CNTR_STR": "accel_min_cntr_str",
    "SCALP_SCANNER_PROBE_MIN_SEC": "probe_min_sec",
    "SCALP_SCANNER_PROBE_MAX_SEC": "probe_max_sec",
    "SCALP_SCANNER_PROBE_MIN_PRICE_DELTA_PCT": "probe_min_price_delta_pct",
    "SCALP_SCANNER_PROBE_MIN_FLU_DELTA_PCT": "probe_min_flu_delta_pct",
    "SCALP_SCANNER_PRIORITY_TIERING_ENABLED": "priority_tiering_enabled",
    "SCALP_SCANNER_PRIORITY_DEMOTE_REALTIME_RANK_ONLY": "priority_demote_realtime_rank_only",
    "SCALP_SCANNER_PRIORITY_DEMOTE_BID_IMBALANCE_ONLY": "priority_demote_bid_imbalance_only",
    "SCALP_SCANNER_DEMOTE_OPEN_PRICE_JUMP_WITHOUT_VOLUME": "demote_open_price_jump_without_volume",
    "EARLY_ACCEL_RECHECK_RUNTIME_ENABLED": "enabled",
    "EARLY_ACCEL_RECHECK_MAX_COUNT": "max_count",
    "EARLY_ACCEL_RECHECK_MIN_INTERVAL_SEC": "min_interval_sec",
    "EARLY_ACCEL_RECHECK_MAX_AGE_SEC": "max_age_sec",
    "EARLY_ACCEL_RECHECK_MIN_TICK_ACCEL": "min_tick_accel",
    "EARLY_ACCEL_RECHECK_MIN_MICRO_VWAP_BP": "min_micro_vwap_bp",
    "EARLY_ACCEL_RECHECK_ALLOW_LIQUIDITY_BLOCKED": "allow_liquidity_blocked",
    "EARLY_ACCEL_RECHECK_ALLOW_STRENGTH_BLOCKED": "allow_strength_blocked",
    "EARLY_ACCEL_STRONG_BUNDLE_RECHECK_ENABLED": "strong_bundle_recheck_enabled",
    "EARLY_ACCEL_STRONG_BUNDLE_RECHECK_MIN_SCORE": "strong_bundle_recheck_min_score",
    "EARLY_ACCEL_STRONG_BUNDLE_RECHECK_MAX_SCORE": "strong_bundle_recheck_max_score",
    "EARLY_ACCEL_STRONG_BUNDLE_RECHECK_BUY_MIN_SCORE": "strong_bundle_recheck_buy_min_score",
    "EARLY_ACCEL_STRONG_BUNDLE_RECHECK_MIN_PASS_COUNT": "strong_bundle_recheck_min_pass_count",
    "EARLY_ACCEL_STRONG_BUNDLE_RECHECK_MAX_PER_SYMBOL": "strong_bundle_recheck_max_per_symbol",
    "AI_NUMERIC_CONSISTENCY_RECHECK_ENABLED": "enabled",
    "AI_NUMERIC_CONSISTENCY_RECHECK_MIN_SCORE": "min_score",
    "AI_NUMERIC_CONSISTENCY_RECHECK_BUY_MIN_SCORE": "buy_min_score",
    "AI_NUMERIC_CONSISTENCY_RECHECK_MIN_FEATURE_PASS_COUNT": "min_feature_pass_count",
    "AI_NUMERIC_CONSISTENCY_RECHECK_MAX_PER_SYMBOL": "max_per_symbol",
    "SCALP_CONDITION_UNMATCH_GUARD_ENABLED": "condition_unmatch_guard_enabled",
    "SCALP_CONDITION_UNMATCH_GUARD_TAGS": "condition_unmatch_guard_tags",
    "SCALP_DEFENSIVE_MISSED_UPSIDE_MIN_ORIGINAL_BPS": "min_original_bps",
    "SCALP_DEFENSIVE_MISSED_UPSIDE_TARGET_MODE": "target_mode",
    "SCALP_DEFENSIVE_MISSED_UPSIDE_NEUTRAL_BID_MINUS_TICKS": "neutral_bid_minus_ticks",
    "SCALP_DEFENSIVE_MISSED_UPSIDE_BULLISH_BID_MINUS_TICKS": "bullish_bid_minus_ticks",
    "SCALP_REFERENCE_TARGET_MISSED_UPSIDE_MIN_BELOW_BID_BPS": "reference_target_min_below_bid_bps",
    "SCALP_REFERENCE_TARGET_MISSED_UPSIDE_TARGET_MODE": "reference_target_target_mode",
    "SCALP_REFERENCE_TARGET_MISSED_UPSIDE_NEUTRAL_BID_MINUS_TICKS": "reference_target_neutral_bid_minus_ticks",
    "SCALP_REFERENCE_TARGET_MISSED_UPSIDE_BULLISH_BID_MINUS_TICKS": "reference_target_bullish_bid_minus_ticks",
    "SCALP_SOFT_STOP_DYNAMIC_GRACE_OVERRIDE_ENABLED": "enabled",
    "SCALP_SOFT_STOP_DYNAMIC_GRACE_WEAK_SEC": "weak_sec",
    "SCALP_SOFT_STOP_DYNAMIC_GRACE_BASE_SEC": "base_sec",
    "SCALP_SOFT_STOP_DYNAMIC_GRACE_STRONG_SEC": "strong_sec",
    "SCALP_SOFT_STOP_DYNAMIC_GRACE_MIN_AI_SCORE": "min_ai_score",
    "SCALP_SOFT_STOP_DYNAMIC_GRACE_EMERGENCY_PCT": "emergency_pct",
    "SCALP_SOFT_STOP_DYNAMIC_GRACE_MAX_WORSEN_PCT": "max_worsen_pct",
    "SCALP_PRESET_TP_SOFT_STOP_OVERRIDE_ENABLED": "enabled",
    "SCALP_PRESET_TP_SOFT_STOP_TRIGGER_PCT": "trigger_pct",
    "SCALP_PRESET_TP_SOFT_STOP_GRACE_SEC": "grace_sec",
    "SCALP_PRESET_TP_SOFT_STOP_EMERGENCY_PCT": "emergency_pct",
    "SCALP_PRESET_TP_SOFT_STOP_MAX_WORSEN_PCT": "max_worsen_pct",
    "SCALP_PRESET_TP_SOFT_STOP_RECOVERY_BUFFER_PCT": "recovery_buffer_pct",
    "LIFECYCLE_DECISION_MATRIX_ENABLED": "enabled",
    "LIFECYCLE_DECISION_MATRIX_POLICY_FILE": "policy_file",
    "LIFECYCLE_DECISION_MATRIX_POLICY_VERSION": "policy_version",
    "LIFECYCLE_DECISION_MATRIX_PROMOTE_ENABLED": "promote_enabled",
    "LIFECYCLE_DECISION_MATRIX_MAX_PROMOTES_PER_DAY": "max_promotes_per_day",
    "LIFECYCLE_DECISION_MATRIX_MIN_STAGE_CONFIDENCE": "min_stage_confidence",
    "LIFECYCLE_DECISION_MATRIX_RUNTIME_EFFECT_ENABLED": "runtime_effect_enabled",
    "LIFECYCLE_AI_CONTEXT_ENABLED": "lifecycle_ai_context_enabled",
    "LIFECYCLE_AI_CONTEXT_FILE": "lifecycle_ai_context_file",
    "LIFECYCLE_AI_CONTEXT_VERSION": "lifecycle_ai_context_version",
    "SCALP_ENTRY_ADM_ADVISORY_ENABLED": "entry_adm_advisory_enabled",
    "SCALP_ENTRY_ADM_RUNTIME_BIAS_ENABLED": "entry_adm_runtime_bias_enabled",
    "HOLDING_EXIT_MATRIX_ADVISORY_ENABLED": "holding_exit_matrix_advisory_enabled",
    "HOLDING_EXIT_MATRIX_RUNTIME_BIAS_ENABLED": "holding_exit_matrix_runtime_bias_enabled",
    "HOLDING_EXIT_MATRIX_SCALE_IN_BIAS_ENABLED": "holding_exit_matrix_scale_in_bias_enabled",
    "SCALP_SIM_SCALE_IN_WINDOW_EXPANSION_ENABLED": "enabled",
    "SCALP_SIM_SCALE_IN_WINDOW_ALLOWED_ARMS": "allowed_arms",
    "SCALP_SIM_SCALE_IN_WINDOW_MIN_PROFIT_PCT": "min_profit_pct",
    "SCALP_SIM_SCALE_IN_WINDOW_MAX_PROFIT_PCT": "max_profit_pct",
    "SCALP_SIM_SCALE_IN_WINDOW_MAX_ORDERS_PER_POSITION": "max_orders_per_position",
    "SCALP_SIM_SCALE_IN_WINDOW_MAX_ORDERS_PER_DAY": "max_orders_per_day",
    "SCALP_SIM_SCALE_IN_EXECUTION_OBSERVATION_ENABLED": "execution_observation_enabled",
    "SCALP_SIM_SCALE_IN_EXECUTION_ARMS": "execution_arms",
    "SCALP_SIM_SCALE_IN_PYRAMID_MAX_ORDERS_PER_POSITION": "pyramid_max_orders_per_position",
    "SCALP_SIM_SCALE_IN_PYRAMID_MAX_ORDERS_PER_DAY": "pyramid_max_orders_per_day",
    "SCALP_SIM_SCALE_IN_AVG_DOWN_MAX_ORDERS_PER_POSITION": "avg_down_max_orders_per_position",
    "SCALP_SIM_SCALE_IN_AVG_DOWN_MAX_ORDERS_PER_DAY": "avg_down_max_orders_per_day",
    "SCALP_SIM_CANDIDATE_WINDOW_MAX_DAILY": "max_daily",
    "SCALP_SIM_CANDIDATE_WINDOW_BLOCKED_AI_SCORE_MAX_SHARE_PCT": "blocked_ai_score_max_share_pct",
    "SCALP_SIM_CANDIDATE_WINDOW_FIRST_AI_WAIT_MIN_SHARE_PCT": "first_ai_wait_min_share_pct",
    "SCALP_SIM_CANDIDATE_WINDOW_TIME_BUCKET_POLICY": "time_bucket_policy",
    "LIFECYCLE_BUCKET_DISCOVERY_ENABLED": "enabled",
    "LIFECYCLE_BUCKET_DISCOVERY_POLICY_FILE": "policy_file",
    "LIFECYCLE_BUCKET_DISCOVERY_POLICY_VERSION": "policy_version",
    "LIFECYCLE_BUCKET_DISCOVERY_LIVE_AUTO_APPLY_ENABLED": "live_auto_apply_enabled",
    "ENTRY_SPLIT_ORDER_POLICY_ENABLED": "enabled",
    "ENTRY_SPLIT_ORDER_POLICY_FILE": "policy_file",
    "ENTRY_SPLIT_ORDER_POLICY_VERSION": "policy_version",
    "SCALP_SIM_AUTO_POLICY_ENABLED": "enabled",
    "SCALP_SIM_AUTO_POLICY_FILE": "policy_file",
    "SCALP_SIM_AUTO_POLICY_VERSION": "policy_version",
    "SCALP_SIM_AUTO_POLICY_SOURCE_DATE": "policy_source_date",
    "SWING_SIM_AUTO_POLICY_ENABLED": "enabled",
    "SWING_SIM_AUTO_POLICY_FILE": "policy_file",
    "SWING_SIM_AUTO_POLICY_VERSION": "policy_version",
    "SWING_SIM_AUTO_BOTTOM_REBOUND_SOURCE_ENABLED": "bottom_rebound_source_enabled",
    "GREENFIELD_REAL_ENV_AUTHORITY_ENABLED": "enabled",
    "GREENFIELD_REAL_ENV_AUTHORITY_SCOPE": "scope",
    "GREENFIELD_REAL_ENV_AUTHORITY_POLICY_FILE": "policy_file",
    "GREENFIELD_REAL_ENV_AUTHORITY_POLICY_VERSION": "policy_version",
    "GREENFIELD_REAL_ENV_TELEGRAM_ENABLED": "telegram_enabled",
}

AGGRESSIVE_ENTRY_PRICE_OVERRIDE_FAMILY = "aggressive_entry_price_override_runtime"
SCALPING_SCANNER_REAL_SOURCE_GUARD_FAMILY = "scalping_scanner_real_source_guard_runtime"
EARLY_ACCEL_RECHECK_FAMILY = "early_accel_recheck_runtime"
AI_NUMERIC_CONSISTENCY_RECHECK_FAMILY = "ai_numeric_consistency_recheck_runtime"
PRE_SUBMIT_LIQUIDITY_RELIEF_FAMILY = "pre_submit_liquidity_relief_runtime"
WEAK_CONTEXT_LATE_ENTRY_GUARD_FAMILY = "weak_context_late_entry_guard_runtime"
ENTRY_OPPORTUNITY_RECHECK_FAMILY = "entry_opportunity_recheck_runtime"
SCORE65_74_STRONG_MICRO_OVERRIDE_FAMILY = "score65_74_recovery_probe_strong_micro_override_runtime"
ENTRY_PRICE_LIVE_TUNING_MARKER_ENV = "KORSTOCKSCAN_ENTRY_PRICE_LIVE_TUNING_SELECTED"
ENTRY_STAGE_LIVE_TUNING_MARKER_ENV = "KORSTOCKSCAN_ENTRY_STAGE_LIVE_TUNING_SELECTED"
REAL_PYRAMID_SCALE_IN_QUALITY_GUARD_FAMILY = "real_pyramid_scale_in_quality_guard_runtime"
SCALE_IN_LIVE_TUNING_MARKER_ENV = "KORSTOCKSCAN_SCALE_IN_LIVE_TUNING_SELECTED"
SOFT_STOP_DYNAMIC_GRACE_FAMILY = "soft_stop_dynamic_grace_runtime"
PRESET_TP_SOFT_STOP_FAMILY = "preset_tp_soft_stop_runtime"
PROFIT_STAGNATION_EXIT_FAMILY = "profit_stagnation_exit_runtime"
NEVER_GREEN_DEFER_CLAMP_FAMILY = "never_green_defer_clamp_runtime"
HOLDING_EXIT_LIVE_TUNING_MARKER_ENV = "KORSTOCKSCAN_HOLDING_EXIT_LIVE_TUNING_SELECTED"
PRESET_TP_EXIT_LIVE_TUNING_MARKER_ENV = "KORSTOCKSCAN_PRESET_TP_EXIT_LIVE_TUNING_SELECTED"
SCALPING_SCANNER_REAL_SOURCE_GUARD_ENV_KEYS = frozenset(
    {
        "KORSTOCKSCAN_SCALP_SCANNER_REAL_SOURCE_GUARD_ENABLED",
        "KORSTOCKSCAN_SCALP_SCANNER_REAL_SOURCE_GUARD_BLOCK_VALUE_TOP_ONLY",
        "KORSTOCKSCAN_SCALP_SCANNER_REAL_SOURCE_GUARD_MAX_DECLINE_PCT",
        "KORSTOCKSCAN_SCALP_SCANNER_REAL_SOURCE_GUARD_BLOCK_LATE_FIRST_SEEN",
        "KORSTOCKSCAN_SCALP_SCANNER_ACCEL_MIN_RANK_JUMP",
        "KORSTOCKSCAN_SCALP_SCANNER_ACCEL_MIN_SPIKE_RATE",
        "KORSTOCKSCAN_SCALP_SCANNER_ACCEL_MIN_PRIORITY_SCORE",
        "KORSTOCKSCAN_SCALP_SCANNER_ACCEL_MIN_CNTR_STR",
        "KORSTOCKSCAN_SCALP_SCANNER_PROBE_MIN_SEC",
        "KORSTOCKSCAN_SCALP_SCANNER_PROBE_MAX_SEC",
        "KORSTOCKSCAN_SCALP_SCANNER_PROBE_MIN_PRICE_DELTA_PCT",
        "KORSTOCKSCAN_SCALP_SCANNER_PROBE_MIN_FLU_DELTA_PCT",
        "KORSTOCKSCAN_SCALP_SCANNER_PRIORITY_TIERING_ENABLED",
        "KORSTOCKSCAN_SCALP_SCANNER_PRIORITY_DEMOTE_REALTIME_RANK_ONLY",
        "KORSTOCKSCAN_SCALP_SCANNER_PRIORITY_DEMOTE_BID_IMBALANCE_ONLY",
        "KORSTOCKSCAN_SCALP_SCANNER_DEMOTE_OPEN_PRICE_JUMP_WITHOUT_VOLUME",
        "KORSTOCKSCAN_SCALP_CONDITION_UNMATCH_GUARD_ENABLED",
        "KORSTOCKSCAN_SCALP_CONDITION_UNMATCH_GUARD_TAGS",
    }
)
SCORE65_74_STRONG_MICRO_OVERRIDE_ENV_KEYS = frozenset(
    {
        "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_STRONG_MICRO_OVERRIDE_ENABLED",
        "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_STRONG_MICRO_MIN_BUY_PRESSURE",
        "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_STRONG_MICRO_MIN_MICRO_VWAP_BP",
    }
)
EARLY_ACCEL_RECHECK_ENV_KEYS = frozenset(
    {
        "KORSTOCKSCAN_EARLY_ACCEL_RECHECK_RUNTIME_ENABLED",
        "KORSTOCKSCAN_EARLY_ACCEL_RECHECK_MAX_COUNT",
        "KORSTOCKSCAN_EARLY_ACCEL_RECHECK_MIN_INTERVAL_SEC",
        "KORSTOCKSCAN_EARLY_ACCEL_RECHECK_MAX_AGE_SEC",
        "KORSTOCKSCAN_EARLY_ACCEL_RECHECK_MIN_TICK_ACCEL",
        "KORSTOCKSCAN_EARLY_ACCEL_RECHECK_MIN_MICRO_VWAP_BP",
        "KORSTOCKSCAN_EARLY_ACCEL_RECHECK_ALLOW_LIQUIDITY_BLOCKED",
        "KORSTOCKSCAN_EARLY_ACCEL_RECHECK_ALLOW_STRENGTH_BLOCKED",
        "KORSTOCKSCAN_EARLY_ACCEL_STRONG_BUNDLE_RECHECK_ENABLED",
        "KORSTOCKSCAN_EARLY_ACCEL_STRONG_BUNDLE_RECHECK_MIN_SCORE",
        "KORSTOCKSCAN_EARLY_ACCEL_STRONG_BUNDLE_RECHECK_MAX_SCORE",
        "KORSTOCKSCAN_EARLY_ACCEL_STRONG_BUNDLE_RECHECK_BUY_MIN_SCORE",
        "KORSTOCKSCAN_EARLY_ACCEL_STRONG_BUNDLE_RECHECK_MIN_PASS_COUNT",
        "KORSTOCKSCAN_EARLY_ACCEL_STRONG_BUNDLE_RECHECK_MAX_PER_SYMBOL",
    }
)
AI_NUMERIC_CONSISTENCY_RECHECK_ENV_KEYS = frozenset(
    {
        "KORSTOCKSCAN_AI_NUMERIC_CONSISTENCY_RECHECK_ENABLED",
        "KORSTOCKSCAN_AI_NUMERIC_CONSISTENCY_RECHECK_MIN_SCORE",
        "KORSTOCKSCAN_AI_NUMERIC_CONSISTENCY_RECHECK_BUY_MIN_SCORE",
        "KORSTOCKSCAN_AI_NUMERIC_CONSISTENCY_RECHECK_MIN_FEATURE_PASS_COUNT",
        "KORSTOCKSCAN_AI_NUMERIC_CONSISTENCY_RECHECK_MAX_PER_SYMBOL",
    }
)
PRE_SUBMIT_LIQUIDITY_RELIEF_ENV_KEYS = frozenset(
    {
        "KORSTOCKSCAN_PRE_SUBMIT_LIQUIDITY_RELIEF_ENABLED",
        "KORSTOCKSCAN_PRE_SUBMIT_LIQUIDITY_RELIEF_MIN_AI_SCORE",
        "KORSTOCKSCAN_PRE_SUBMIT_LIQUIDITY_RELIEF_MIN_TICK_ACCEL",
        "KORSTOCKSCAN_PRE_SUBMIT_LIQUIDITY_RELIEF_MIN_BUY_PRESSURE",
        "KORSTOCKSCAN_PRE_SUBMIT_LIQUIDITY_RELIEF_MIN_MICRO_VWAP_BP",
        "KORSTOCKSCAN_PRE_SUBMIT_LIQUIDITY_RELIEF_MAX_PER_SYMBOL",
    }
)
WEAK_CONTEXT_LATE_ENTRY_GUARD_ENV_KEYS = frozenset(
    {
        "KORSTOCKSCAN_WEAK_CONTEXT_LATE_ENTRY_GUARD_ENABLED",
        "KORSTOCKSCAN_WEAK_CONTEXT_LATE_ENTRY_LOOKBACK_SEC",
        "KORSTOCKSCAN_WEAK_CONTEXT_LATE_ENTRY_MIN_BLOCK_COUNT",
        "KORSTOCKSCAN_WEAK_CONTEXT_LATE_ENTRY_MIN_TICK_ACCEL",
        "KORSTOCKSCAN_WEAK_CONTEXT_LATE_ENTRY_MIN_BUY_PRESSURE",
        "KORSTOCKSCAN_WEAK_CONTEXT_LATE_ENTRY_MIN_MICRO_VWAP_BP",
    }
)
REAL_PYRAMID_SCALE_IN_QUALITY_GUARD_ENV_KEYS = frozenset(
    {
        "KORSTOCKSCAN_REAL_PYRAMID_MICRO_CONTEXT_GUARD_ENABLED",
        "KORSTOCKSCAN_PENDING_SCALE_IN_REVALIDATION_CANCEL_ENABLED",
        "KORSTOCKSCAN_PENDING_SCALE_IN_REVALIDATION_MIN_AI_SCORE",
        "KORSTOCKSCAN_PENDING_SCALE_IN_REVALIDATION_MIN_TICK_ACCEL",
        "KORSTOCKSCAN_PENDING_SCALE_IN_REVALIDATION_MIN_BUY_PRESSURE",
        "KORSTOCKSCAN_PENDING_SCALE_IN_REVALIDATION_MIN_MICRO_VWAP_BP",
        "KORSTOCKSCAN_RECENT_EXIT_CANDIDATE_PYRAMID_BLOCK_ENABLED",
        "KORSTOCKSCAN_RECENT_EXIT_CANDIDATE_PYRAMID_BLOCK_SEC",
    }
)
AGGRESSIVE_ENTRY_PRICE_OVERRIDE_ENV_KEYS = frozenset(
    {
        "KORSTOCKSCAN_SCALP_AGGRESSIVE_ENTRY_PRICE_OVERRIDE_ENABLED",
        "KORSTOCKSCAN_SCALP_AGGRESSIVE_ENTRY_PRICE_OVERRIDE_TYPES",
        "KORSTOCKSCAN_SCALP_DEFENSIVE_MISSED_UPSIDE_MIN_ORIGINAL_BPS",
        "KORSTOCKSCAN_SCALP_DEFENSIVE_MISSED_UPSIDE_TARGET_MODE",
        "KORSTOCKSCAN_SCALP_DEFENSIVE_MISSED_UPSIDE_NEUTRAL_BID_MINUS_TICKS",
        "KORSTOCKSCAN_SCALP_DEFENSIVE_MISSED_UPSIDE_BULLISH_BID_MINUS_TICKS",
        "KORSTOCKSCAN_SCALP_REFERENCE_TARGET_MISSED_UPSIDE_MIN_BELOW_BID_BPS",
        "KORSTOCKSCAN_SCALP_REFERENCE_TARGET_MISSED_UPSIDE_TARGET_MODE",
        "KORSTOCKSCAN_SCALP_REFERENCE_TARGET_MISSED_UPSIDE_NEUTRAL_BID_MINUS_TICKS",
        "KORSTOCKSCAN_SCALP_REFERENCE_TARGET_MISSED_UPSIDE_BULLISH_BID_MINUS_TICKS",
    }
)
NEVER_GREEN_DEFER_CLAMP_ENV_KEYS = frozenset(
    {
        "KORSTOCKSCAN_NEVER_GREEN_DEFER_CLAMP_ENABLED",
        "KORSTOCKSCAN_NEVER_GREEN_DEFER_CLAMP_MAX_PEAK_PROFIT_PCT",
        "KORSTOCKSCAN_NEVER_GREEN_DEFER_CLAMP_MIN_DEFER_COUNT",
        "KORSTOCKSCAN_NEVER_GREEN_DEFER_CLAMP_MAX_MICRO_VWAP_BP",
        "KORSTOCKSCAN_NEVER_GREEN_DEFER_CLAMP_MIN_LOSS_PCT",
    }
)
SOFT_STOP_DYNAMIC_GRACE_ENV_KEYS = frozenset(
    {
        "KORSTOCKSCAN_SCALP_SOFT_STOP_DYNAMIC_GRACE_OVERRIDE_ENABLED",
        "KORSTOCKSCAN_SCALP_SOFT_STOP_DYNAMIC_GRACE_WEAK_SEC",
        "KORSTOCKSCAN_SCALP_SOFT_STOP_DYNAMIC_GRACE_BASE_SEC",
        "KORSTOCKSCAN_SCALP_SOFT_STOP_DYNAMIC_GRACE_STRONG_SEC",
        "KORSTOCKSCAN_SCALP_SOFT_STOP_DYNAMIC_GRACE_MIN_AI_SCORE",
        "KORSTOCKSCAN_SCALP_SOFT_STOP_DYNAMIC_GRACE_EMERGENCY_PCT",
        "KORSTOCKSCAN_SCALP_SOFT_STOP_DYNAMIC_GRACE_MAX_WORSEN_PCT",
    }
)
PRESET_TP_SOFT_STOP_ENV_KEYS = frozenset(
    {
        "KORSTOCKSCAN_SCALP_PRESET_TP_SOFT_STOP_OVERRIDE_ENABLED",
        "KORSTOCKSCAN_SCALP_PRESET_TP_SOFT_STOP_TRIGGER_PCT",
        "KORSTOCKSCAN_SCALP_PRESET_TP_SOFT_STOP_GRACE_SEC",
        "KORSTOCKSCAN_SCALP_PRESET_TP_SOFT_STOP_EMERGENCY_PCT",
        "KORSTOCKSCAN_SCALP_PRESET_TP_SOFT_STOP_MAX_WORSEN_PCT",
        "KORSTOCKSCAN_SCALP_PRESET_TP_SOFT_STOP_RECOVERY_BUFFER_PCT",
    }
)


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _parse_dt(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def _file_sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return ""


def _generator_hashes(paths: tuple[Path, ...]) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in paths:
        digest = _file_sha256(path)
        if digest:
            hashes[path.name] = digest
    return hashes


def _int_or_default(value: Any, default: int) -> int | None:
    if value is None or value == "":
        return int(default)
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _is_swing_pre_final_auto_approved(request: dict[str, Any]) -> bool:
    state = str(request.get("calibration_state") or "").strip()
    contract = request.get("auto_promotion_contract") if isinstance(request.get("auto_promotion_contract"), dict) else {}
    return (
        state == "dry_run_auto_apply_ready"
        and bool(request.get("auto_approval_required"))
        and str(request.get("auto_approval_state") or "") == "ai_tier2_auto_approved"
        and tier2_validation_passed(contract.get("tier2_status"))
        and contract.get("final_user_approval_boundary") == "full_live_only"
    )


def _latest_report_before(target_date: str) -> Path | None:
    candidates: list[tuple[str, Path]] = []
    for path in REPORT_DIR.glob("threshold_cycle_*.json"):
        report_date = path.stem.replace("threshold_cycle_", "")
        if report_date < target_date:
            candidates.append((report_date, path))
    for path in CALIBRATION_REPORT_DIR.glob("threshold_cycle_calibration_*_postclose.json"):
        report_date = path.stem.replace("threshold_cycle_calibration_", "").replace("_postclose", "")
        if report_date < target_date:
            candidates.append((report_date, path))
    if not candidates:
        return None
    return sorted(candidates)[-1][1]


def apply_manifest_path(target_date: str) -> Path:
    return APPLY_PLAN_DIR / f"threshold_apply_{target_date}.json"


def runtime_env_path(target_date: str) -> Path:
    return RUNTIME_ENV_DIR / f"threshold_runtime_env_{target_date}.env"


def runtime_env_manifest_path(target_date: str) -> Path:
    return RUNTIME_ENV_DIR / f"threshold_runtime_env_{target_date}.json"


def runtime_gap_provenance_artifact_path(target_date: str) -> Path:
    return RUNTIME_GAP_PROVENANCE_DIR / f"runtime_gap_provenance_{target_date}.json"


def runtime_env_verify_path(target_date: str) -> Path:
    return RUNTIME_ENV_DIR / f"threshold_runtime_env_verify_{target_date}.json"


def swing_runtime_approval_report_path(source_date: str) -> Path:
    return SWING_RUNTIME_APPROVAL_REPORT_DIR / f"swing_runtime_approval_{source_date}.json"


def swing_runtime_approval_artifact_path(source_date: str) -> Path:
    return SWING_RUNTIME_APPROVAL_ARTIFACT_DIR / f"swing_runtime_approvals_{source_date}.json"


def scalp_sim_scale_in_window_artifact_path(source_date: str) -> Path:
    return SWING_RUNTIME_APPROVAL_ARTIFACT_DIR / f"scalp_sim_scale_in_window_expansion_{source_date}.json"


def _bridge_artifact_path_for_family(family: str, source_date: str) -> Path | None:
    if family == ENTRY_BRIDGE_FAMILY:
        return ldm_entry_runtime_bridge_artifact_path(source_date)
    if family == SCALE_IN_BRIDGE_FAMILY:
        return ldm_scale_in_runtime_bridge_artifact_path(source_date)
    return None


def _greenfield_policy_block_reason(item: dict[str, Any]) -> str:
    recommended = item.get("recommended_values") if isinstance(item.get("recommended_values"), dict) else {}
    policy_file = str(recommended.get("policy_file") or item.get("greenfield_policy_file") or "").strip()
    recommended_version = str(recommended.get("policy_version") or item.get("candidate_id") or "")
    return validate_greenfield_policy_file(policy_file, expected_version=recommended_version or None)


def _bridge_candidate_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return None


def _bridge_source_quality_pass(value: Any) -> bool:
    return str(value or "").strip().lower() in {"pass", "ok", "clean", "source_quality_pass"}


def _runtime_bridge_candidate_contract_blockers(item: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if (
        item.get("source_quality_blocked")
        or item.get("source_quality_blocker")
        or (isinstance(item.get("source_quality_blockers"), list) and item.get("source_quality_blockers"))
    ):
        blockers.append("source_quality_blocked")
    source_quality_gate = item.get("source_quality_gate") or item.get("source_quality_status")
    if source_quality_gate and not _bridge_source_quality_pass(source_quality_gate):
        blockers.append("source_quality_blocked")
    if (
        item.get("forbidden_use_blocked")
        or item.get("forbidden_use_violation")
        or (isinstance(item.get("forbidden_use_violations"), list) and item.get("forbidden_use_violations"))
    ):
        blockers.append("forbidden_use_blocked")

    family = str(item.get("family") or "")
    if family == GREENFIELD_REAL_ENV_FAMILY:
        return list(dict.fromkeys(blockers))

    source_refs: list[dict[str, Any]] = []
    source_bucket = item.get("source_bucket") if isinstance(item.get("source_bucket"), dict) else {}
    if source_bucket:
        source_refs.append(source_bucket)
    source_refs.extend(
        ref for ref in (item.get("source_buckets") or []) if isinstance(ref, dict)
    )
    if source_refs:
        complete_refs = [
            ref
            for ref in source_refs
            if _bridge_source_quality_pass(ref.get("source_quality_gate"))
            and _bridge_candidate_float(ref.get("source_quality_adjusted_ev_pct")) is not None
        ]
        if not any(_bridge_source_quality_pass(ref.get("source_quality_gate")) for ref in source_refs):
            blockers.append("source_bucket_source_quality_blocked")
        if not any(_bridge_candidate_float(ref.get("source_quality_adjusted_ev_pct")) is not None for ref in source_refs):
            blockers.append("source_bucket_primary_ev_missing")
        if not complete_refs:
            blockers.append("source_bucket_contract_incomplete")
    else:
        metric = str(item.get("primary_decision_metric") or "")
        if metric == "source_quality_adjusted_ev_pct":
            if _bridge_candidate_float(item.get("source_quality_adjusted_ev_pct")) is None:
                blockers.append("primary_ev_missing")
            if not source_quality_gate:
                blockers.append("source_quality_gate_missing")
        elif item.get("bridge_candidate_state") == "live_auto_apply_ready":
            blockers.append("source_bucket_contract_missing")
    return list(dict.fromkeys(blockers))


def _candidate_source_quality_contract_blocked(candidate: dict[str, Any]) -> bool:
    source_quality = candidate.get("source_quality") if isinstance(candidate.get("source_quality"), dict) else {}
    source_metrics = candidate.get("source_metrics") if isinstance(candidate.get("source_metrics"), dict) else {}
    if (
        candidate.get("source_quality_blocked")
        or candidate.get("source_quality_blocker")
        or (
            isinstance(candidate.get("source_quality_blockers"), list)
            and candidate["source_quality_blockers"]
        )
    ):
        return True
    for value in (
        candidate.get("source_quality_gate"),
        candidate.get("source_quality_status"),
        source_quality.get("source_quality_gate"),
        source_quality.get("source_quality_status"),
        source_quality.get("status"),
    ):
        text = str(value or "").strip().lower()
        if text and not _bridge_source_quality_pass(text):
            return True
    if source_metrics.get("source_quality_pass") is False:
        return True
    if source_metrics.get("provenance_present") is False:
        return True
    return False


def _candidate_apply_contract_blockers(candidate: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if _candidate_source_quality_contract_blocked(candidate):
        blockers.append("source_quality_blocked")
    if (
        candidate.get("forbidden_use_blocked")
        or candidate.get("forbidden_use_violation")
        or (
            isinstance(candidate.get("forbidden_use_violations"), list)
            and candidate["forbidden_use_violations"]
        )
    ):
        blockers.append("forbidden_use_blocked")
    return list(dict.fromkeys(blockers))


def _report_path_for_date(target_date: str, *, source_phase: str | None = None) -> Path:
    if source_phase == "intraday":
        return CALIBRATION_REPORT_DIR / f"threshold_cycle_calibration_{target_date}_intraday.json"
    if source_phase == "postclose":
        return CALIBRATION_REPORT_DIR / f"threshold_cycle_calibration_{target_date}_postclose.json"
    canonical = REPORT_DIR / f"threshold_cycle_{target_date}.json"
    if canonical.exists():
        return canonical
    postclose = CALIBRATION_REPORT_DIR / f"threshold_cycle_calibration_{target_date}_postclose.json"
    if postclose.exists():
        return postclose
    return canonical


def _ai_review_path_for_date(source_date: str, phase: str) -> Path:
    return AI_REVIEW_DIR / f"threshold_cycle_ai_review_{source_date}_{phase}.json"


def _load_ai_review(source_date: str | None, *, source_phase: str | None = None) -> dict[str, Any]:
    if not source_date:
        return {"status": "missing_source_date", "path": None, "items_by_family": {}}
    postclose_path = _ai_review_path_for_date(source_date, "postclose")
    intraday_path = _ai_review_path_for_date(source_date, "intraday")
    if source_phase == "intraday":
        preferred_paths = [intraday_path]
    else:
        preferred_paths = [postclose_path]
    for path in preferred_paths:
        if not path.exists():
            continue
        payload = _load_json(path)
        if str(payload.get("ai_status") or "").lower() != "parsed":
            if path == postclose_path:
                items = payload.get("items") if isinstance(payload.get("items"), list) else []
                return {
                    "status": str(payload.get("ai_status") or "unknown"),
                    "path": str(path),
                    "phase": "postclose",
                    "model": payload.get("ai_model"),
                    "provider_status": payload.get("ai_provider_status") or {},
                    "items_by_family": {
                        str(item.get("family") or ""): item
                        for item in items
                        if isinstance(item, dict) and item.get("family")
                    },
                }
            continue
        items = payload.get("items") if isinstance(payload.get("items"), list) else []
        return {
            "status": str(payload.get("ai_status") or "unknown"),
            "path": str(path),
            "phase": path.stem.rsplit("_", 1)[-1],
            "model": payload.get("ai_model"),
            "provider_status": payload.get("ai_provider_status") or {},
            "items_by_family": {
                str(item.get("family") or ""): item for item in items if isinstance(item, dict) and item.get("family")
            },
        }
    return {"status": "missing_ai_review", "path": None, "items_by_family": {}}


def _latency_classifier_recommendation_path(source_date: str) -> Path:
    return LATENCY_CLASSIFIER_RECOMMENDATION_DIR / f"latency_classifier_recommendation_{source_date}.json"


def _load_latency_classifier_candidates(source_date: str | None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not source_date:
        return [], {"status": "missing_source_date", "path": None}
    path = _latency_classifier_recommendation_path(source_date)
    if not path.exists():
        return [], {"status": "missing_report", "path": str(path)}
    payload = _load_json(path)
    candidates = payload.get("calibration_candidates")
    if not isinstance(candidates, list):
        candidate = payload.get("calibration_candidate")
        candidates = [candidate] if isinstance(candidate, dict) else []
    normalized = [item for item in candidates if isinstance(item, dict)]
    selected_candidate = normalized[0] if normalized else {}
    selected_metrics = (
        selected_candidate.get("source_metrics")
        if isinstance(selected_candidate.get("source_metrics"), dict)
        else {}
    )
    return normalized, {
        "status": "loaded",
        "path": str(path),
        "latency_block_count": payload.get("latency_block_count"),
        "selected_profile_id": payload.get("selected_profile_id"),
        "profile_generation": payload.get("profile_generation"),
        "recommended_action": selected_metrics.get("recommended_action"),
        "recommended_action_reason": selected_metrics.get("recommended_action_reason"),
        "allowed_runtime_apply": selected_candidate.get("allowed_runtime_apply"),
        "calibration_state": selected_candidate.get("calibration_state"),
    }


def _rising_missed_first_touch_calibration_path(source_date: str) -> Path:
    return RISING_MISSED_FIRST_TOUCH_CALIBRATION_DIR / (
        f"rising_missed_first_touch_calibration_{source_date}.json"
    )


def _load_rising_missed_first_touch_calibration_candidates(
    source_date: str | None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not source_date:
        return [], {"status": "missing_source_date", "path": None}
    path = _rising_missed_first_touch_calibration_path(source_date)
    if not path.exists():
        return [], {"status": "missing_report", "path": str(path)}
    payload = _load_json(path)
    candidates = payload.get("calibration_candidates")
    if not isinstance(candidates, list):
        candidate = payload.get("calibration_candidate")
        candidates = [candidate] if isinstance(candidate, dict) else []
    normalized = [item for item in candidates if isinstance(item, dict)]
    normalized, preflight_status = _block_candidates_by_source_quality_preflight(
        normalized,
        source_date,
        source_report_type="rising_missed_first_touch_calibration",
    )
    selected_candidate = normalized[0] if normalized else {}
    return normalized, {
        "status": "loaded",
        "path": str(path),
        "allowed_runtime_apply": selected_candidate.get("allowed_runtime_apply"),
        "calibration_state": selected_candidate.get("calibration_state"),
        "sample_count": selected_candidate.get("sample_count"),
        "source_quality_preflight": preflight_status,
        "source_quality_blocked": bool(preflight_status.get("blocked")),
    }


def _scalping_pyramid_quality_calibration_path(source_date: str) -> Path:
    return SCALPING_PYRAMID_QUALITY_CALIBRATION_DIR / (
        f"scalping_pyramid_quality_calibration_{source_date}.json"
    )


def _source_quality_preflight_status(source_date: str | None) -> dict[str, Any]:
    if not source_date:
        return {"blocked": True, "reason": "missing_source_date", "preflight": {}}
    preflight = load_source_quality_preflight(source_date)
    blocked = source_quality_preflight_blocked(preflight)
    reason = str(
        preflight.get("blocked_reason")
        or preflight.get("source_quality_gate")
        or "source_quality_blocked"
    )
    return {"blocked": blocked, "reason": reason, "preflight": preflight}


def _block_candidates_by_source_quality_preflight(
    candidates: list[dict[str, Any]],
    source_date: str | None,
    *,
    source_report_type: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    status = _source_quality_preflight_status(source_date)
    if not status["blocked"]:
        return candidates, status
    reason = str(status.get("reason") or "source_quality_blocked")
    blocked_candidates = [
        {
            **item,
            "allowed_runtime_apply": False,
            "source_quality_gate": "source_quality_blocked",
            "source_quality_blocked": str(
                item.get("source_quality_blocked")
                or f"{source_report_type}_source_quality_preflight_blocked:{reason}"
            ),
            "apply_block_reason": "source_quality_blocked",
        }
        for item in candidates
    ]
    return blocked_candidates, status


def _load_scalping_pyramid_quality_calibration_candidates(
    source_date: str | None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not source_date:
        return [], {"status": "missing_source_date", "path": None}
    path = _scalping_pyramid_quality_calibration_path(source_date)
    if not path.exists():
        return [], {"status": "missing_report", "path": str(path)}
    payload = _load_json(path)
    candidates = payload.get("calibration_candidates")
    if not isinstance(candidates, list):
        candidate = payload.get("calibration_candidate")
        candidates = [candidate] if isinstance(candidate, dict) else []
    normalized = [item for item in candidates if isinstance(item, dict)]
    normalized, preflight_status = _block_candidates_by_source_quality_preflight(
        normalized,
        source_date,
        source_report_type="scalping_pyramid_quality_calibration",
    )
    selected_candidate = normalized[0] if normalized else {}
    return normalized, {
        "status": "loaded",
        "path": str(path),
        "allowed_runtime_apply": selected_candidate.get("allowed_runtime_apply"),
        "calibration_state": selected_candidate.get("calibration_state"),
        "sample_count": selected_candidate.get("sample_count"),
        "source_quality_preflight": preflight_status,
        "source_quality_blocked": bool(preflight_status.get("blocked")),
    }


def _ai_score_optimization_backtest_path(source_date: str) -> Path:
    return AI_SCORE_OPTIMIZATION_BACKTEST_DIR / f"ai_score_optimization_backtest_{source_date}.json"


def _ai_score_optimization_payload_source_quality_blocked(payload: dict[str, Any]) -> bool:
    if not isinstance(payload, dict):
        return False
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    if payload.get("source_quality_blocked") or payload.get("source_quality_blocker"):
        return True
    if summary.get("source_quality_blocked") or summary.get("source_quality_blocker"):
        return True
    blockers = payload.get("source_quality_blockers") or summary.get("source_quality_blockers")
    if isinstance(blockers, list) and blockers:
        return True
    for value in (
        payload.get("source_quality_gate"),
        payload.get("source_quality_status"),
        summary.get("source_quality_gate"),
        summary.get("source_quality_status"),
    ):
        text = str(value or "").strip().lower()
        if text and text not in {"pass", "ok", "clean", "source_quality_pass"}:
            return True
    status_text = str(summary.get("status") or payload.get("status") or "").strip().lower()
    return "source_quality_blocked" in status_text or "hard_block" in status_text


def _load_ai_score_optimization_backtest_candidates(
    source_date: str | None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not source_date:
        return [], {"status": "missing_source_date", "path": None}
    path = _ai_score_optimization_backtest_path(source_date)
    if not path.exists():
        return [], {"status": "missing_report", "path": str(path)}
    payload = _load_json(path)
    candidates = payload.get("calibration_candidates")
    if not isinstance(candidates, list):
        candidates = []
    normalized = [item for item in candidates if isinstance(item, dict)]
    source_quality_blocked = _ai_score_optimization_payload_source_quality_blocked(payload)
    preflight_status = _source_quality_preflight_status(source_date)
    if source_quality_blocked or preflight_status.get("blocked"):
        preflight_reason = str(preflight_status.get("reason") or "source_quality_blocked")
        block_reason = (
            "ai_score_optimization_backtest_root_source_quality_blocked"
            if source_quality_blocked
            else f"ai_score_optimization_backtest_source_quality_preflight_blocked:{preflight_reason}"
        )
        normalized = [
            {
                **item,
                "allowed_runtime_apply": False,
                "source_quality_gate": "source_quality_blocked",
                "source_quality_blocked": str(item.get("source_quality_blocked") or block_reason),
                "apply_block_reason": "source_quality_blocked",
            }
            for item in normalized
        ]
        source_quality_blocked = True
    selected_candidate = next(
        (item for item in normalized if bool(item.get("allowed_runtime_apply"))),
        normalized[0] if normalized else {},
    )
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    return normalized, {
        "status": "loaded",
        "path": str(path),
        "allowed_runtime_apply": selected_candidate.get("allowed_runtime_apply"),
        "calibration_state": selected_candidate.get("calibration_state"),
        "candidate_count": len(normalized),
        "allowed_runtime_apply_candidate_count": summary.get("allowed_runtime_apply_candidate_count"),
        "source_quality_blocked": source_quality_blocked,
        "source_quality_preflight": preflight_status,
    }


def _runtime_env_name(target_env_key: str) -> str:
    if target_env_key.startswith("AI_SCORE65_74_RECOVERY_PROBE_"):
        return f"KORSTOCKSCAN_{target_env_key.removeprefix('AI_')}"
    if target_env_key.startswith("AI_WAIT6579_PROBE_CANARY_"):
        return f"KORSTOCKSCAN_{target_env_key.removeprefix('AI_')}"
    return f"KORSTOCKSCAN_{target_env_key}"


def _format_env_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return f"{value:.10g}"
    return str(value)


def _date_in_lock_window(lock: dict[str, Any], source_date: str | None, target_date: str) -> bool:
    source_text = str(source_date or "").strip()
    target_text = str(target_date or "").strip()
    basis_dates = [value for value in (source_text, target_text) if value]
    if not basis_dates:
        return False
    active_from = str(lock.get("active_from_date") or lock.get("created_date") or "").strip()
    if bool(lock.get("lock_until_explicit_close")) or bool(lock.get("explicit_close_required")):
        return not active_from or any(value >= active_from for value in basis_dates)
    active_until = str(
        lock.get("min_observation_until_date")
        or lock.get("expires_after_source_date")
        or lock.get("target_date")
        or ""
    ).strip()
    basis_date = source_text or target_text
    if active_from and basis_date < active_from:
        return False
    if active_until and basis_date > active_until:
        return False
    return True


def _load_operator_runtime_env_locks(source_date: str | None, target_date: str) -> list[dict[str, Any]]:
    locks: list[dict[str, Any]] = []
    if not OPERATOR_RUNTIME_ENV_LOCK_DIR.exists():
        return locks
    for path in sorted(OPERATOR_RUNTIME_ENV_LOCK_DIR.glob("*.json")):
        payload = _load_json(path)
        if not payload or not bool(payload.get("enabled", True)):
            continue
        family = str(payload.get("family") or "").strip()
        env_key = str(payload.get("env_key") or "").strip()
        env_overrides = payload.get("env_overrides") if isinstance(payload.get("env_overrides"), dict) else {}
        if not family or (not env_key and not env_overrides):
            continue
        if not _date_in_lock_window(payload, source_date, target_date):
            continue
        locks.append({**payload, "path": str(path)})
    return locks


def _previous_runtime_date(target_date: str) -> str | None:
    from datetime import timedelta

    try:
        dt = date.fromisoformat(target_date)
    except (ValueError, TypeError):
        return None
    return (dt - timedelta(days=1)).isoformat()


def _load_previous_runtime_env_selected_families(target_date: str) -> tuple[set[str], dict[str, Any]]:
    prev_date = _previous_runtime_date(target_date)
    if not prev_date:
        return set(), {}
    manifest = _load_json(runtime_env_manifest_path(prev_date))
    if not manifest:
        return set(), {}
    families = {
        str(item)
        for item in (manifest.get("selected_families") or [])
        if isinstance(item, str) and item.strip()
    }
    return families, manifest


def _hold_carry_forward_blockers(candidate: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if bool(candidate.get("safety_revert_required")):
        blockers.append("safety_revert_required")
    if (
        str(candidate.get("source_quality_blocked") or "")
        or str(candidate.get("source_quality_blocker") or "")
        or (
            isinstance(candidate.get("source_quality_blockers"), list)
            and candidate["source_quality_blockers"]
        )
    ):
        blockers.append("source_quality_hard_block")
    if (
        bool(candidate.get("severe_loss_guard"))
        or bool(candidate.get("excessive_drawdown"))
    ):
        blockers.append("severe_loss_guard")
    if (
        bool(candidate.get("provenance_breach"))
        or bool(candidate.get("order_provenance_breach"))
        or bool(candidate.get("order_failure"))
    ):
        blockers.append("order_provenance_breach")
    close_reasons_raw = " ".join(_candidate_close_reasons(candidate, ""))
    if any(
        kw in close_reasons_raw.lower()
        for kw in {"severe_loss", "excessive_drawdown"}
    ):
        if "severe_loss_guard" not in blockers:
            blockers.append("severe_loss_guard")
    if any(
        kw in close_reasons_raw.lower()
        for kw in {"provenance_breach", "order_provenance", "order_failure"}
    ):
        if "order_provenance_breach" not in blockers:
            blockers.append("order_provenance_breach")
    return blockers


_FAMILY_ENV_KEY_PREFIXES: dict[str, str] = {
    "entry_cancel_wait_runtime": "KORSTOCKSCAN_ENTRY_CANCEL_WAIT_",
    "quote_consistency_normalization": "KORSTOCKSCAN_QUOTE_CONSISTENCY_",
    "soft_stop_whipsaw_confirmation": "KORSTOCKSCAN_SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_",
    "score65_74_recovery_probe": "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_",
    "rising_missed_first_touch_avgdown_decision_gate": "KORSTOCKSCAN_SCALP_FIRST_TOUCH_AVGDOWN_",
    "scalping_pyramid_quality_gate": "KORSTOCKSCAN_SCALPING_PYRAMID_",
    SCORE65_74_STRONG_MICRO_OVERRIDE_FAMILY: "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_STRONG_MICRO_",
    PRE_SUBMIT_LIQUIDITY_RELIEF_FAMILY: "KORSTOCKSCAN_PRE_SUBMIT_LIQUIDITY_RELIEF_",
    ENTRY_OPPORTUNITY_RECHECK_FAMILY: "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_",
    "scalp_sim_candidate_window_expansion": "KORSTOCKSCAN_SCALP_SIM_CANDIDATE_WINDOW_",
    "scalp_sim_ai_budget_manager": "KORSTOCKSCAN_SCALP_SIM_AI_",
    "lifecycle_decision_matrix_runtime": "KORSTOCKSCAN_LIFECYCLE_DECISION_MATRIX_",
    "scalp_sim_auto_approval": "KORSTOCKSCAN_SCALP_SIM_AUTO_POLICY_",
    "swing_sim_auto_approval": "KORSTOCKSCAN_SWING_SIM_AUTO_POLICY_",
    "scalp_sim_scale_in_window_expansion": "KORSTOCKSCAN_SCALP_SIM_SCALE_IN_",
    "lifecycle_bucket_discovery_sim_auto_approval": "KORSTOCKSCAN_LIFECYCLE_BUCKET_DISCOVERY_",
    "entry_split_order_plan": "KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_",
    PROFIT_STAGNATION_EXIT_FAMILY: "KORSTOCKSCAN_SCALP_PROFIT_STAGNATION_",
}


PROFIT_STAGNATION_EXIT_REQUIRED_ENV_OVERRIDES: dict[str, str] = {
    "KORSTOCKSCAN_SCALP_LOW_PROFIT_STAGNATION_HARD_EXIT_ENABLED": "true",
    "KORSTOCKSCAN_SCALP_LOW_PROFIT_STAGNATION_MIN_ADJUSTED_PROFIT_PCT": "0.20",
    "KORSTOCKSCAN_SCALP_LOW_PROFIT_STAGNATION_MAX_ADJUSTED_PROFIT_PCT": "1.00",
    "KORSTOCKSCAN_SCALP_LOW_PROFIT_STAGNATION_MIN_HOLD_SEC": "1800",
    "KORSTOCKSCAN_SCALP_LOW_PROFIT_STAGNATION_ASSUMED_EXIT_SLIPPAGE_BPS": "15",
}


def _normalize_runtime_env_overrides_for_family(
    family: str,
    env_overrides: dict[str, str],
) -> dict[str, str]:
    normalized = {str(k): str(v) for k, v in (env_overrides or {}).items()}
    if family == PROFIT_STAGNATION_EXIT_FAMILY:
        normalized = {
            **PROFIT_STAGNATION_EXIT_REQUIRED_ENV_OVERRIDES,
            **normalized,
        }
    return normalized


def _previous_runtime_env_overrides_for_family(
    previous_manifest: dict[str, Any],
    family: str,
) -> dict[str, str]:
    env_overrides = previous_manifest.get("env_overrides")
    if not isinstance(env_overrides, dict):
        return {}
    if family == "sell_side_open_time_block_runtime":
        exact_keys = {"KORSTOCKSCAN_SELL_WINDOWS", "KORSTOCKSCAN_SCALPING_SELL_WINDOWS"}
        return {
            str(k): str(v)
            for k, v in env_overrides.items()
            if str(k).startswith("KORSTOCKSCAN_SELL_SIDE_OPEN_TIME_BLOCK_")
            or str(k) in exact_keys
        }
    prefix = _FAMILY_ENV_KEY_PREFIXES.get(family)
    if prefix:
        return _normalize_runtime_env_overrides_for_family(
            family,
            {str(k): str(v) for k, v in env_overrides.items() if str(k).startswith(prefix)},
        )
    return {}


def _lock_env_overrides(lock: dict[str, Any]) -> dict[str, str]:
    family = str(lock.get("family") or "").strip()
    overrides = lock.get("env_overrides") if isinstance(lock.get("env_overrides"), dict) else {}
    if overrides:
        return _normalize_runtime_env_overrides_for_family(
            family,
            {str(key): _format_env_value(value) for key, value in overrides.items()},
        )
    env_key = str(lock.get("env_key") or "").strip()
    if not env_key:
        return {}
    value = lock.get("env_value", "true")
    return _normalize_runtime_env_overrides_for_family(family, {env_key: _format_env_value(value)})


def _candidate_close_reasons(candidate: dict[str, Any], reject_reason: str) -> list[str]:
    reasons: list[str] = []
    if reject_reason:
        reasons.append(reject_reason)
    if bool(candidate.get("safety_revert_required")):
        reasons.append("safety_revert_required")
    for key in (
        "calibration_reason",
        "guard_reject_reason",
        "rollback_reason",
        "decision_reason",
        "source_quality_blocker",
        "source_quality_blockers",
        "source_quality_blocked",
        "block_reasons",
        "safety_reasons",
    ):
        value = candidate.get(key)
        if isinstance(value, list):
            reasons.extend(str(item) for item in value)
        elif value:
            reasons.append(str(value))
    metrics = candidate.get("source_metrics") if isinstance(candidate.get("source_metrics"), dict) else {}
    for key in ("block_reason", "submit_block_reason", "stale_reason", "order_provenance_status"):
        value = metrics.get(key)
        if value:
            reasons.append(str(value))
    return reasons


def _lock_allows_close(lock: dict[str, Any], close_reasons: list[str]) -> bool:
    allowed = {
        str(item).strip().lower()
        for item in (lock.get("allowed_close_reason_keywords") or [])
        if str(item).strip()
    }
    if not allowed:
        allowed = LOCK_ALLOWED_CLOSE_KEYWORDS
    lowered = " ".join(close_reasons).lower()
    return any(keyword in lowered for keyword in allowed)


def _locked_synthetic_candidate(lock: dict[str, Any]) -> dict[str, Any]:
    return {
        "family": lock.get("family"),
        "stage": lock.get("stage") or "entry",
        "priority": int(lock.get("priority") or 10),
        "allowed_runtime_apply": True,
        "safety_revert_required": False,
        "calibration_state": "operator_locked",
        "target_env_keys": [],
        "recommended_values": {"enabled": True},
        "threshold_version": lock.get("threshold_version") or f"{lock.get('family')}:operator_runtime_env_lock",
        "operator_runtime_env_lock_synthetic": True,
    }


def _values_equal(left: Any, right: Any) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return bool(left) == bool(right)
    try:
        return float(left) == float(right)
    except (TypeError, ValueError):
        return str(left) == str(right)


def _env_overrides_for_candidate(candidate: dict[str, Any]) -> dict[str, str]:
    recommended = candidate.get("recommended_values") if isinstance(candidate.get("recommended_values"), dict) else {}
    current = candidate.get("current_values") if isinstance(candidate.get("current_values"), dict) else {}
    calibration_state = str(candidate.get("calibration_state") or "")
    policy_or_family = str(candidate.get("policy_id") or candidate.get("family") or "")
    force_emit = policy_or_family in {
        "latency_classifier_runtime_profile",
        "lifecycle_decision_matrix_runtime",
        ENTRY_BRIDGE_FAMILY,
        SCALE_IN_BRIDGE_FAMILY,
        "lifecycle_bucket_discovery_sim_auto_approval",
        "scalp_sim_auto_approval",
        "swing_sim_auto_approval",
    }
    overrides: dict[str, str] = {}
    for target_key in candidate.get("target_env_keys") or []:
        target_key = str(target_key)
        value_key = TARGET_ENV_VALUE_KEYS.get(target_key)
        if not value_key or value_key not in recommended:
            continue
        value = recommended[value_key]
        if value_key == "enabled" and calibration_state == "adjust_up" and not bool(current.get(value_key)):
            value = True
        if (not force_emit) and _values_equal(current.get(value_key), value):
            continue
        overrides[_runtime_env_name(target_key)] = _format_env_value(value)
    return overrides


def _scrub_removed_contracts(value: Any) -> Any:
    if isinstance(value, dict):
        family = str(value.get("family") or value.get("source_family") or "")
        if family in REMOVED_CALIBRATION_FAMILIES:
            return None
        scrubbed: dict[str, Any] = {}
        for key, item in value.items():
            if key == "target_env_keys" and isinstance(item, list):
                scrubbed[key] = [
                    entry
                    for entry in item
                    if str(entry) not in REMOVED_TARGET_ENV_KEYS
                    and _runtime_env_name(str(entry)) not in REMOVED_RUNTIME_ENV_KEYS
                ]
                continue
            if key in REMOVED_RUNTIME_ENV_KEYS:
                continue
            nested = _scrub_removed_contracts(item)
            if nested is not None:
                scrubbed[key] = nested
        return scrubbed
    if isinstance(value, list):
        scrubbed_list = []
        for item in value:
            if str(item) in REMOVED_TARGET_ENV_KEYS or str(item) in REMOVED_RUNTIME_ENV_KEYS:
                continue
            nested = _scrub_removed_contracts(item)
            if nested is not None:
                scrubbed_list.append(nested)
        return scrubbed_list
    return value


def _dedupe_calibration_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str]] = set()
    for item in candidates:
        if not isinstance(item, dict):
            continue
        family = str(item.get("family") or "")
        threshold_version = str(item.get("threshold_version") or "")
        target_keys = json.dumps(item.get("target_env_keys") or [], sort_keys=True, ensure_ascii=False)
        recommended = json.dumps(item.get("recommended_values") or {}, sort_keys=True, ensure_ascii=False)
        key = (family, threshold_version, target_keys, recommended)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def _score65_74_entry_unlock_candidate(candidate: dict[str, Any]) -> bool:
    if str(candidate.get("family") or "") != "score65_74_recovery_probe":
        return False
    metrics = candidate.get("source_metrics") if isinstance(candidate.get("source_metrics"), dict) else {}
    if bool(metrics.get("entry_unlock_probe_ready")):
        return True
    try:
        sample_count = int(candidate.get("sample_count") or 0)
        sample_floor = int(candidate.get("sample_floor") or 0)
    except Exception:
        return False
    if sample_floor <= 0 or sample_count < sample_floor:
        return False
    try:
        avg_ev = float(
            metrics.get("score60_74_avg_expected_ev_pct")
            if metrics.get("score60_74_avg_expected_ev_pct") is not None
            else metrics.get("score65_74_avg_expected_ev_pct")
            or 0.0
        )
        avg_close = float(
            metrics.get("score60_74_avg_close_10m_pct")
            if metrics.get("score60_74_avg_close_10m_pct") is not None
            else metrics.get("score65_74_avg_close_10m_pct")
            or 0.0
        )
    except Exception:
        return False
    risk_gate = str(metrics.get("risk_regime_gate_state") or "").lower()
    submitted = float(metrics.get("order_bundle_submitted") or 0.0)
    return (
        avg_ev >= 2.0
        and avg_close >= 1.0
        and submitted <= 0.0
        and risk_gate != "confirmed_panic"
    )


def _load_swing_runtime_approval_bundle(source_date: str | None) -> dict[str, Any]:
    if not source_date:
        return {
            "request_report": None,
            "approval_artifact": None,
            "requests": [],
            "approved_requests": [],
            "blocked": ["missing_source_date"],
        }
    request_path = swing_runtime_approval_report_path(source_date)
    artifact_path = swing_runtime_approval_artifact_path(source_date)
    request_report = _load_json(request_path)
    artifact = _load_json(artifact_path)
    requests = request_report.get("approval_requests") if isinstance(request_report.get("approval_requests"), list) else []
    approved_items = artifact.get("approved_requests") if isinstance(artifact.get("approved_requests"), list) else []
    approved_ids = {
        str(item.get("approval_id") or "")
        for item in approved_items
        if isinstance(item, dict) and bool(item.get("approved", True))
    }
    requests_by_id = {
        str(item.get("approval_id") or ""): item
        for item in requests
        if isinstance(item, dict) and item.get("approval_id")
    }
    legacy_real_canary_ids = {
        str(item.get("approval_id") or "")
        for item in requests
        if isinstance(item, dict)
        and str(item.get("policy_id") or item.get("family") or "")
        in {"swing_scale_in_real_canary_phase0", "swing_one_share_real_canary_phase0"}
    }
    runtime_requests = [
        item
        for item in requests
        if isinstance(item, dict)
        and str(item.get("policy_id") or item.get("family") or "") != "swing_scale_in_real_canary_phase0"
        and str(item.get("policy_id") or item.get("family") or "") != "swing_one_share_real_canary_phase0"
    ]
    approved_requests = []
    blocked: list[str] = [
        f"blocked_legacy_real_canary_removed:{approval_id}"
        for approval_id in sorted(legacy_real_canary_ids)
        if approval_id
    ]
    manual_non_scale_requests = [
        item for item in runtime_requests if not _is_swing_pre_final_auto_approved(item)
    ]
    if manual_non_scale_requests and not artifact:
        blocked.append("approval_artifact_missing")
    for item in runtime_requests:
        approval_id = str(item.get("approval_id") or "")
        if approval_id and _is_swing_pre_final_auto_approved(item):
            approved_ids.add(approval_id)
    approved_ids.difference_update(legacy_real_canary_ids)
    for approval_id in sorted(approved_ids):
        request = requests_by_id.get(approval_id)
        if not request:
            blocked.append(f"approval_request_not_found:{approval_id}")
            continue
        request_policy = str(request.get("policy_id") or request.get("family") or "")
        if request_policy in {"swing_one_share_real_canary_phase0", "swing_scale_in_real_canary_phase0"}:
            blocked.append(f"blocked_legacy_real_canary_removed:{approval_id}")
            continue
        approval_state = (
            "ai_tier2_pre_final_auto_approved"
            if _is_swing_pre_final_auto_approved(request)
            else "approved_live"
        )
        approved_requests.append({**request, "approval_state": approval_state})
    return {
        "request_report": str(request_path) if request_path.exists() else None,
        "approval_artifact": str(artifact_path) if artifact_path.exists() else None,
        "legacy_phase0_real_canary_ignored": bool(legacy_real_canary_ids),
        "requests": requests,
        "approved_requests": approved_requests,
        "blocked": blocked,
        "artifact_payload": artifact,
    }


def _select_swing_approved_candidates(bundle: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, str]]:
    selected: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    env_overrides: dict[str, str] = {}
    selected_by_stage: dict[str, str] = {}
    for item in bundle.get("approved_requests") or []:
        if not isinstance(item, dict):
            continue
        family = str(item.get("family") or "")
        is_pre_final_auto = _is_swing_pre_final_auto_approved(item)
        stage = str(item.get("stage") or "unknown")
        candidate = {
            **item,
            "calibration_state": "approved_live",
            "allowed_runtime_apply": True,
            "safety_revert_required": False,
        }
        overrides = _env_overrides_for_candidate(candidate)
        reject_reason = ""
        if bool(item.get("actual_order_submitted")):
            reject_reason = "actual_order_submission_not_allowed"
        elif not bool(item.get("dry_run_required", True)):
            reject_reason = "dry_run_required_missing"
        elif stage in selected_by_stage:
            reject_reason = f"same_stage_owner_conflict:{selected_by_stage[stage]}"
        elif not overrides:
            reject_reason = "no_runtime_env_override"
        decision = {
            "approval_id": item.get("approval_id"),
            "family": family,
            "stage": stage,
            "selected": not bool(reject_reason),
            "decision_reason": reject_reason
            or (
                "ai_tier2_pre_final_auto_approval_accepted"
                if is_pre_final_auto
                else "user_approval_artifact_accepted"
            ),
            "env_overrides": overrides if not reject_reason else {},
            "dry_run_required": True,
        }
        decisions.append(decision)
        if reject_reason:
            continue
        selected_by_stage[stage] = family
        selected.append(candidate)
        env_overrides.update(overrides)
    if env_overrides:
        env_overrides["KORSTOCKSCAN_SWING_LIVE_ORDER_DRY_RUN_ENABLED"] = "true"
    return selected, decisions, env_overrides


def _load_scalp_sim_scale_in_window_approval(source_date: str | None) -> dict[str, Any]:
    if not source_date:
        return {"artifact": None, "approved_request": None, "blocked": ["missing_source_date"]}
    path = scalp_sim_scale_in_window_artifact_path(source_date)
    payload = _load_json(path)
    blocked: list[str] = []
    if not payload:
        blocked.append("approval_artifact_missing")
    elif str(payload.get("policy_id") or payload.get("family") or "") != "scalp_sim_scale_in_window_expansion":
        blocked.append("approval_policy_mismatch")
    elif not bool(payload.get("approved")):
        blocked.append("sim_auto_approval_not_approved")
    elif payload.get("approval_state") != "sim_auto_approved":
        blocked.append("sim_auto_approval_state_invalid")
    elif bool(payload.get("human_approval_required")):
        blocked.append("human_approval_required_not_allowed_for_sim_auto")
    elif bool(payload.get("actual_order_submitted")):
        blocked.append("actual_order_submitted_not_allowed")
    elif payload.get("runtime_effect") is not False:
        blocked.append("runtime_effect_not_allowed")
    elif payload.get("broker_order_forbidden") is not True:
        blocked.append("broker_order_forbidden_contract_missing")
    elif payload.get("source_quality_status") not in {None, "pass"}:
        blocked.append("source_quality_blocked")
    request = None
    if payload and not blocked:
        recommended = payload.get("recommended_values") if isinstance(payload.get("recommended_values"), dict) else {}
        recommended = dict(recommended)
        if "execution_observation_enabled" not in recommended:
            recommended["execution_observation_enabled"] = True
        if not recommended.get("execution_arms"):
            recommended["execution_arms"] = "PASSIVE_BASELINE,MARKETABLE_OBSERVATION"
        target_env_keys = list(payload.get("target_env_keys") or [])
        for key in (
            "SCALP_SIM_SCALE_IN_EXECUTION_OBSERVATION_ENABLED",
            "SCALP_SIM_SCALE_IN_EXECUTION_ARMS",
        ):
            if key not in target_env_keys:
                target_env_keys.append(key)
        request = {
            "family": "scalp_sim_scale_in_window_expansion",
            "policy_id": "scalp_sim_scale_in_window_expansion",
            "stage": "scale_in",
            "calibration_state": "sim_auto_approved",
            "allowed_runtime_apply": True,
            "safety_revert_required": False,
            "target_env_keys": target_env_keys,
            "recommended_values": recommended,
            "current_values": {
                "enabled": False,
                "allowed_arms": "",
                "min_profit_pct": None,
                "max_profit_pct": None,
                "max_orders_per_position": None,
                "max_orders_per_day": None,
            },
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "decision_authority": "sim_auto_approval_only",
        }
    return {
        "artifact": str(path) if path.exists() else None,
        "approved_request": request,
        "blocked": blocked,
        "artifact_payload": payload,
    }


def _select_scalp_sim_scale_in_window_approval(bundle: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, str]]:
    request = bundle.get("approved_request") if isinstance(bundle.get("approved_request"), dict) else None
    if not request:
        return [], [], {}
    overrides = _env_overrides_for_candidate(request)
    reject_reason = ""
    if not overrides:
        reject_reason = "no_runtime_env_override"
    decision = {
        "family": request.get("family"),
        "stage": request.get("stage"),
        "selected": not bool(reject_reason),
        "decision_reason": reject_reason or "sim_auto_approval_artifact_accepted",
        "env_overrides": overrides if not reject_reason else {},
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    return ([request], [decision], overrides) if not reject_reason else ([], [decision], {})


def _artifact_matches_bridge_candidate(artifact: dict[str, Any], candidate: dict[str, Any]) -> bool:
    candidate_id = str(candidate.get("candidate_id") or "")
    explicit_candidate_id = str(artifact.get("candidate_id") or artifact.get("bridge_candidate_id") or "")
    if explicit_candidate_id and explicit_candidate_id != candidate_id:
        return False
    allowed_ids: set[str] = set()
    for key in ("approved_candidate_ids", "approved_bridge_candidate_ids", "approved_request_ids"):
        allowed_ids.update(str(value) for value in artifact.get(key) or [] if str(value or "").strip())
    if allowed_ids and candidate_id not in allowed_ids:
        return False
    return True


def _load_runtime_apply_bridge_approval(source_date: str | None) -> dict[str, Any]:
    if not source_date:
        return {
            "request_report": None,
            "artifacts": {},
            "candidates": [],
            "approved_requests": [],
            "blocked": ["missing_source_date"],
        }
    report_path = runtime_apply_bridge_report_path(source_date)
    report = _load_json(report_path)
    candidates = report.get("candidates") if isinstance(report.get("candidates"), list) else []
    artifacts: dict[str, str | None] = {}
    artifact_payloads: dict[str, dict[str, Any]] = {}
    approved_requests: list[dict[str, Any]] = []
    blocked: list[str] = []
    metadata: list[dict[str, Any]] = []
    bridge_families = {ENTRY_BRIDGE_FAMILY, SCALE_IN_BRIDGE_FAMILY, GREENFIELD_REAL_ENV_FAMILY}
    if not report:
        blocked.append("runtime_apply_bridge_report_missing")

    for item in candidates:
        if not isinstance(item, dict):
            continue
        family = str(item.get("family") or "")
        if family not in bridge_families:
            continue
        if family in ARCHIVED_RUNTIME_APPLY_BRIDGE_FAMILIES:
            blocked.append(f"runtime_apply_bridge_archived_family:{family}")
            continue
        artifact_path = _bridge_artifact_path_for_family(family, source_date)
        artifact = _load_json(artifact_path) if artifact_path else {}
        artifacts[family] = str(artifact_path) if artifact_path and artifact_path.exists() else None
        artifact_payloads[family] = artifact
        candidate_id = str(item.get("candidate_id") or "")
        if (
            family == ENTRY_BRIDGE_FAMILY
            or bool(item.get("metadata_only"))
            or str(item.get("bridge_candidate_state") or "") == "entry_only_bridge_metadata"
        ):
            legacy_source_state = str(item.get("bridge_candidate_state") or "").strip()
            metadata.append(
                {
                    "family": family,
                    "candidate_id": candidate_id,
                    "state": "entry_only_bridge_metadata",
                    "legacy_source_state": legacy_source_state or "entry_only_bridge_metadata",
                    "reason": item.get("bridge_exclusion_reason") or "entry_only_bridge_metadata_not_live_candidate",
                    "allowed_runtime_apply": False,
                    "target_env_keys": [],
                    "runtime_effect": False,
                }
            )
            continue
        contract = annotate_approval_request({"family": family}, source_date)
        item_blocked: list[str] = []
        auto_live = (
            str(item.get("bridge_candidate_state") or "") == "live_auto_apply_ready"
            and bool(item.get("allowed_runtime_apply"))
            and bool(item.get("live_auto_apply"))
            and not bool(item.get("approval_required"))
        )
        tier2_status = (
            item.get("lifecycle_bucket_discovery_ai_review_status")
            or item.get("ai_review_status")
            or (
                item.get("auto_promotion_contract", {}).get("tier2_status")
                if isinstance(item.get("auto_promotion_contract"), dict)
                else None
            )
        )
        if not bool(contract.get("approval_live_ready")):
            item_blocked.append("approval_contract_not_live_ready")
        if not tier2_validation_passed(tier2_status):
            item_blocked.append(f"ai_tier2_validation_not_parsed:{tier2_status or 'missing'}")
        if str(item.get("bridge_candidate_state") or "") != "live_auto_apply_ready":
            item_blocked.append(f"runtime_apply_blocked_bridge_not_ready:{item.get('bridge_candidate_state')}")
        if not bool(item.get("allowed_runtime_apply")):
            item_blocked.append("runtime_apply_not_allowed")
        item_blocked.extend(_runtime_bridge_candidate_contract_blockers(item))
        if not auto_live:
            item_blocked.append("runtime_apply_bridge_auto_live_contract_missing")
        if family == GREENFIELD_REAL_ENV_FAMILY:
            policy_block_reason = _greenfield_policy_block_reason(item)
            if policy_block_reason:
                item_blocked.append(policy_block_reason)
        if item_blocked:
            blocked.extend(f"{reason}:{family}" for reason in item_blocked)
            continue
        recommended = item.get("recommended_values") if isinstance(item.get("recommended_values"), dict) else {}
        approved_requests.append(
            {
                **item,
                "policy_id": family,
                "approval_id": f"{family}:live_auto_apply:{source_date}",
                "approval_state": "auto_live",
                "approval_artifact": None,
                "approval_runtime_scope": contract.get("approval_runtime_scope"),
                "calibration_state": "live_auto_apply",
                "threshold_version": recommended.get("threshold_version") or f"{family}:{source_date}",
                "allowed_runtime_apply": True,
                "safety_revert_required": False,
                "runtime_apply_bridge_family": family,
                "bridge_candidate_id": candidate_id,
                "source_bucket_key": ",".join(str(value) for value in item.get("source_bucket_keys") or []),
                "actual_runtime_effect": item.get("runtime_effect_after_approval"),
                "lifecycle_bucket_discovery_bucket_id": item.get("lifecycle_bucket_discovery_bucket_id"),
                "lifecycle_bucket_discovery_ai_review_status": item.get(
                    "lifecycle_bucket_discovery_ai_review_status"
                ),
                "lifecycle_bucket_discovery_ai_followup_required": item.get(
                    "lifecycle_bucket_discovery_ai_followup_required"
                ),
                "lifecycle_bucket_discovery_ai_block_ignored_reason": item.get(
                    "lifecycle_bucket_discovery_ai_block_ignored_reason"
                ),
                "post_apply_verification_required": bool(
                    item.get("lifecycle_bucket_discovery_ai_followup_required")
                ),
                "actual_order_submitted": False,
                "decision_authority": (
                    "lifecycle_bucket_discovery_live_auto_apply"
                ),
            }
        )
    return {
        "request_report": str(report_path) if report_path.exists() else None,
        "artifacts": artifacts,
        "artifact_payloads": artifact_payloads,
        "candidates": candidates,
        "metadata": metadata,
        "approved_requests": approved_requests,
        "blocked": blocked,
    }


def _select_runtime_apply_bridge_approval(
    bundle: dict[str, Any],
    *,
    include_families: set[str] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, str]]:
    selected: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    env_overrides: dict[str, str] = {}
    selected_by_stage: dict[str, str] = {}
    for item in sorted(bundle.get("approved_requests") or [], key=lambda row: int(row.get("priority") or 999)):
        if not isinstance(item, dict):
            continue
        family = str(item.get("family") or "")
        stage = str(item.get("stage") or "unknown")
        overrides = _env_overrides_for_candidate(item)
        reject_reason = ""
        if family in RETIRED_RUNTIME_FAMILY_REASONS:
            reject_reason = RETIRED_RUNTIME_FAMILY_REASONS[family]
        elif include_families is not None and family not in include_families:
            reject_reason = "operator_family_filter_excluded"
        elif bool(item.get("actual_order_submitted")):
            reject_reason = "actual_order_submission_not_allowed"
        elif not bool(item.get("allowed_runtime_apply")):
            reject_reason = "runtime_apply_not_allowed"
        elif stage in selected_by_stage:
            reject_reason = f"same_stage_owner_conflict:{selected_by_stage[stage]}"
        elif not overrides:
            reject_reason = "no_runtime_env_override"
        decision = {
            "approval_id": item.get("approval_id"),
            "family": family,
            "stage": stage,
            "bridge_candidate_id": item.get("bridge_candidate_id"),
            "runtime_apply_bridge_family": item.get("runtime_apply_bridge_family"),
            "source_bucket_keys": item.get("source_bucket_keys") or [],
            "actual_runtime_effect": item.get("actual_runtime_effect"),
            "lifecycle_bucket_discovery_bucket_id": item.get("lifecycle_bucket_discovery_bucket_id"),
            "lifecycle_bucket_discovery_ai_review_status": item.get(
                "lifecycle_bucket_discovery_ai_review_status"
            ),
            "lifecycle_bucket_discovery_ai_followup_required": item.get(
                "lifecycle_bucket_discovery_ai_followup_required"
            ),
            "lifecycle_bucket_discovery_ai_block_ignored_reason": item.get(
                "lifecycle_bucket_discovery_ai_block_ignored_reason"
            ),
            "post_apply_verification_required": bool(
                item.get("lifecycle_bucket_discovery_ai_followup_required")
            ),
            "selected": not bool(reject_reason),
            "decision_reason": reject_reason
            or (
                "lifecycle_bucket_discovery_live_auto_apply"
                if str(item.get("approval_state") or "") == "auto_live"
                else "user_approval_artifact_accepted_bridge_ready"
            ),
            "env_overrides": overrides if not reject_reason else {},
            "actual_order_submitted": False,
        }
        decisions.append(decision)
        if reject_reason:
            continue
        selected_by_stage[stage] = family
        selected.append(item)
        env_overrides.update(overrides)
    return selected, decisions, env_overrides


def _load_lifecycle_bucket_sim_auto_approval(source_date: str | None) -> dict[str, Any]:
    if not source_date:
        return {"artifact": None, "approved_request": None, "blocked": ["missing_source_date"]}
    artifact_path = sim_auto_approval_path(source_date)
    discovery_path = discovery_report_path(source_date)
    catalog_path = bucket_catalog_path(source_date)
    payload = _load_json(artifact_path)
    blocked: list[str] = []
    if not payload:
        blocked.append("sim_auto_approval_missing")
    elif not bool(payload.get("approved")):
        blocked.append("sim_auto_approval_not_approved")
    elif bool(payload.get("actual_order_submitted")):
        blocked.append("actual_order_submitted_not_allowed")
    elif payload.get("runtime_effect") is not False:
        blocked.append("runtime_effect_not_allowed")
    elif payload.get("allowed_runtime_apply") is not False:
        blocked.append("artifact_allowed_runtime_apply_must_be_false")
    elif payload.get("broker_order_forbidden") is not True:
        blocked.append("broker_order_forbidden_contract_missing")
    elif not payload.get("approved_bucket_ids"):
        blocked.append("sim_auto_approval_empty")
    if not catalog_path.exists():
        blocked.append("bucket_catalog_missing")
    approved_request = None
    if not blocked:
        approved_request = {
            "family": "lifecycle_bucket_discovery_sim_auto_approval",
            "policy_id": "lifecycle_bucket_discovery_sim_auto_approval",
            "stage": "sim_lifecycle",
            "priority": 89,
            "approval_id": f"lifecycle_bucket_discovery_sim_auto_approval:{source_date}",
            "approval_state": "auto_sim",
            "allowed_runtime_apply": True,
            "safety_revert_required": False,
            "calibration_state": "sim_auto_approved",
            "approved_bucket_ids": payload.get("approved_bucket_ids") or [],
            "approved_bucket_count": payload.get("approved_bucket_count"),
            "target_env_keys": [
                "LIFECYCLE_BUCKET_DISCOVERY_ENABLED",
                "LIFECYCLE_BUCKET_DISCOVERY_POLICY_FILE",
                "LIFECYCLE_BUCKET_DISCOVERY_POLICY_VERSION",
                "LIFECYCLE_BUCKET_DISCOVERY_LIVE_AUTO_APPLY_ENABLED",
            ],
            "recommended_values": {
                "enabled": True,
                "policy_file": str(catalog_path),
                "policy_version": f"lifecycle_bucket_discovery:{source_date}",
                "live_auto_apply_enabled": False,
            },
            "current_values": {
                "enabled": False,
                "policy_file": "",
                "policy_version": "",
                "live_auto_apply_enabled": False,
            },
            "actual_order_submitted": False,
            "decision_authority": "postclose_lifecycle_bucket_discovery_sim_auto",
        }
    return {
        "artifact": str(artifact_path) if artifact_path.exists() else None,
        "discovery_report": str(discovery_path) if discovery_path.exists() else None,
        "catalog": str(catalog_path) if catalog_path.exists() else None,
        "approved_request": approved_request,
        "blocked": blocked,
    }


def _select_lifecycle_bucket_sim_auto_approval(bundle: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, str]]:
    item = bundle.get("approved_request")
    decisions: list[dict[str, Any]] = []
    selected: list[dict[str, Any]] = []
    env_overrides: dict[str, str] = {}
    if not isinstance(item, dict):
        decisions.append(
            {
                "family": "lifecycle_bucket_discovery_sim_auto_approval",
                "selected": False,
                "decision_reason": ",".join(str(reason) for reason in bundle.get("blocked") or []) or "sim_auto_approval_missing",
                "env_overrides": {},
                "actual_order_submitted": False,
            }
        )
        return selected, decisions, env_overrides
    overrides = _env_overrides_for_candidate(item)
    reject_reason = ""
    if not bool(item.get("allowed_runtime_apply")):
        reject_reason = "runtime_apply_not_allowed"
    elif bool(item.get("actual_order_submitted")):
        reject_reason = "actual_order_submitted_not_allowed"
    elif not overrides:
        reject_reason = "no_runtime_env_override"
    decision = {
        "approval_id": item.get("approval_id"),
        "family": item.get("family"),
        "stage": item.get("stage"),
        "selected": not bool(reject_reason),
        "decision_reason": reject_reason or "lifecycle_bucket_discovery_sim_auto_apply",
        "env_overrides": overrides if not reject_reason else {},
        "actual_order_submitted": False,
    }
    decisions.append(decision)
    if reject_reason:
        return selected, decisions, env_overrides
    selected.append(item)
    env_overrides.update(overrides)
    return selected, decisions, env_overrides


def _load_scalp_sim_auto_approval(source_date: str | None) -> dict[str, Any]:
    if not source_date:
        return {"artifact": None, "catalog": None, "approved_request": None, "blocked": ["missing_source_date"]}
    artifact_path = scalp_sim_auto_approval_path(source_date)
    catalog_path = scalp_sim_policy_catalog_path(source_date)
    payload = _load_json(artifact_path)
    catalog_payload = _load_json(catalog_path)
    policies = payload.get("approved_policies") if isinstance(payload.get("approved_policies"), list) else []
    approved_source_ids = [str(item) for item in (payload.get("approved_source_ids") or []) if str(item or "").strip()]
    approved_policy_count = _int_or_default(payload.get("approved_policy_count"), 0) or 0
    blocked: list[str] = []
    if not payload:
        blocked.append("scalp_sim_auto_approval_missing")
    elif payload.get("report_type") != "scalp_sim_auto_approval":
        blocked.append("scalp_sim_auto_approval_report_type_invalid")
    elif not bool(payload.get("approved")):
        blocked.append("scalp_sim_auto_approval_not_approved")
    elif bool(payload.get("actual_order_submitted")):
        blocked.append("actual_order_submitted_not_allowed")
    elif payload.get("runtime_effect") is not False:
        blocked.append("runtime_effect_not_allowed")
    elif payload.get("allowed_runtime_apply") is not False:
        blocked.append("artifact_allowed_runtime_apply_must_be_false")
    elif payload.get("broker_order_forbidden") is not True:
        blocked.append("broker_order_forbidden_contract_missing")
    elif bool(payload.get("human_approval_required")):
        blocked.append("human_approval_required_not_allowed_for_sim_auto")
    elif payload.get("decision_authority") not in {None, "scalp_sim_auto_approval_control_tower"}:
        blocked.append("decision_authority_invalid")
    elif not policies or approved_policy_count <= 0 or not approved_source_ids:
        blocked.append("scalp_sim_auto_approval_empty")
    if not catalog_path.exists():
        blocked.append("scalp_sim_policy_catalog_missing")
    elif not catalog_payload:
        blocked.append("scalp_sim_policy_catalog_invalid")
    elif catalog_payload.get("schema_version") != "scalp_sim_policy_catalog_v1":
        blocked.append("scalp_sim_policy_catalog_schema_invalid")
    else:
        generated_at = _parse_dt(catalog_payload.get("generated_at"))
        generator_provenance = (
            catalog_payload.get("generator_provenance")
            if isinstance(catalog_payload.get("generator_provenance"), dict)
            else {}
        )
        catalog_generator_hashes = (
            generator_provenance.get("files") if isinstance(generator_provenance.get("files"), dict) else {}
        )
        current_generator_hashes = _generator_hashes(SCALP_SIM_POLICY_STALENESS_CHECK_FILES)
        if generated_at is None:
            blocked.append("scalp_sim_policy_catalog_generated_at_missing")
        if not catalog_generator_hashes:
            blocked.append("scalp_sim_policy_catalog_generator_provenance_missing")
        elif current_generator_hashes and catalog_generator_hashes != current_generator_hashes:
            blocked.append("scalp_sim_policy_catalog_stale_after_generator_change")
        for seed in catalog_payload.get("active_sim_priority_seeds") or []:
            if not isinstance(seed, dict):
                blocked.append("active_sim_priority_seed_invalid")
                break
            prefix = seed.get("observable_prefix") if isinstance(seed.get("observable_prefix"), dict) else {}
            if not str(seed.get("active_seed_id") or "").strip() or not str(seed.get("source_parent_bucket_id") or "").strip():
                blocked.append("active_sim_priority_seed_key_missing")
                break
            if str(seed.get("status") or "").strip() not in {"active", "cooldown", "retired"}:
                blocked.append("active_sim_priority_seed_status_invalid")
                break
            if str(seed.get("status") or "") == "active" and (
                not str(prefix.get("entry_score_parent") or "").strip()
                or not str(prefix.get("entry_source_parent") or "").strip()
            ):
                blocked.append("active_sim_priority_seed_observable_prefix_missing")
                break
            if any(str(key) not in ACTIVE_SIM_PRIORITY_OBSERVABLE_PREFIX_KEYS for key in prefix):
                blocked.append("active_sim_priority_seed_observable_prefix_forbidden_dimension")
                break
    approved_request = None
    if not blocked:
        active_seed_ids = [
            str(seed.get("active_seed_id") or "").strip()
            for seed in (catalog_payload.get("active_sim_priority_seeds") or [])
            if isinstance(seed, dict)
            and str(seed.get("status") or "") == "active"
            and str(seed.get("active_seed_id") or "").strip()
        ]
        recommended_values = {
            "enabled": True,
            "policy_file": str(catalog_path),
            "policy_version": f"scalp_sim_auto_approval:{source_date}",
            "policy_source_date": str(source_date),
        }
        target_env_keys = [
            "SCALP_SIM_AUTO_POLICY_ENABLED",
            "SCALP_SIM_AUTO_POLICY_FILE",
            "SCALP_SIM_AUTO_POLICY_VERSION",
            "SCALP_SIM_AUTO_POLICY_SOURCE_DATE",
            "LIFECYCLE_BUCKET_DISCOVERY_ENABLED",
        ]
        current_values = {
            "enabled": False,
            "policy_file": "",
            "policy_version": "",
            "policy_source_date": "",
        }
        for policy in policies:
            if not isinstance(policy, dict) or policy.get("policy_id") != "scalp_sim_scale_in_window_expansion":
                continue
            scale_values = policy.get("recommended_values") if isinstance(policy.get("recommended_values"), dict) else {}
            recommended_values.update(scale_values)
            target_env_keys.extend(
                str(item)
                for item in (policy.get("target_env_keys") or [])
                if str(item or "").startswith("SCALP_SIM_SCALE_IN_")
            )
            current_values.update(
                {
                    "allowed_arms": "",
                    "min_profit_pct": None,
                    "max_profit_pct": None,
                    "max_orders_per_position": None,
                    "max_orders_per_day": None,
                }
            )
        approved_request = {
            "family": "scalp_sim_auto_approval",
            "policy_id": "scalp_sim_auto_approval",
            "stage": "scalp_sim_lifecycle",
            "priority": 87,
            "approval_id": f"scalp_sim_auto_approval:{source_date}",
            "approval_state": "auto_sim",
            "allowed_runtime_apply": True,
            "safety_revert_required": False,
            "calibration_state": "sim_auto_approved",
            "target_env_keys": list(dict.fromkeys(target_env_keys)),
            "recommended_values": recommended_values,
            "current_values": current_values,
            "approved_source_ids": approved_source_ids,
            "approved_policy_count": approved_policy_count,
            "active_sim_priority_seed_ids": active_seed_ids,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "decision_authority": "scalp_sim_auto_approval_control_tower",
        }
    return {
        "artifact": str(artifact_path) if artifact_path.exists() else None,
        "catalog": str(catalog_path) if catalog_path.exists() else None,
        "approved_request": approved_request,
        "blocked": blocked,
        "approved_source_ids": payload.get("approved_source_ids") or [],
        "approved_policy_count": payload.get("approved_policy_count"),
    }


def _select_scalp_sim_auto_approval(bundle: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, str]]:
    item = bundle.get("approved_request")
    decisions: list[dict[str, Any]] = []
    selected: list[dict[str, Any]] = []
    env_overrides: dict[str, str] = {}
    if not isinstance(item, dict):
        decisions.append(
            {
                "family": "scalp_sim_auto_approval",
                "selected": False,
                "decision_reason": ",".join(str(reason) for reason in bundle.get("blocked") or [])
                or "scalp_sim_auto_approval_missing",
                "env_overrides": {},
                "actual_order_submitted": False,
            }
        )
        return selected, decisions, env_overrides
    overrides = _env_overrides_for_candidate(item)
    reject_reason = ""
    if not bool(item.get("allowed_runtime_apply")):
        reject_reason = "runtime_apply_not_allowed"
    elif bool(item.get("actual_order_submitted")):
        reject_reason = "actual_order_submitted_not_allowed"
    elif not overrides:
        reject_reason = "no_runtime_env_override"
    decision = {
        "approval_id": item.get("approval_id"),
        "family": item.get("family"),
        "stage": item.get("stage"),
        "approved_source_ids": item.get("approved_source_ids") or [],
        "selected": not bool(reject_reason),
        "decision_reason": reject_reason or "scalp_sim_auto_approval_apply",
        "env_overrides": overrides if not reject_reason else {},
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    decisions.append(decision)
    if reject_reason:
        return selected, decisions, env_overrides
    selected.append(item)
    env_overrides.update(overrides)
    return selected, decisions, env_overrides


def _load_swing_sim_auto_approval(source_date: str | None) -> dict[str, Any]:
    if not source_date:
        return {"artifact": None, "catalog": None, "approved_request": None, "blocked": ["missing_source_date"]}
    artifact_path = swing_sim_auto_approval_path(source_date)
    catalog_path = swing_sim_policy_catalog_path(source_date)
    payload = _load_json(artifact_path)
    blocked: list[str] = []
    if not payload:
        blocked.append("swing_sim_auto_approval_missing")
    elif payload.get("report_type") != "swing_sim_auto_approval":
        blocked.append("swing_sim_auto_approval_report_type_invalid")
    elif not bool(payload.get("approved")):
        blocked.append("swing_sim_auto_approval_not_approved")
    elif bool(payload.get("actual_order_submitted")):
        blocked.append("actual_order_submitted_not_allowed")
    elif payload.get("runtime_effect") is not False:
        blocked.append("runtime_effect_not_allowed")
    elif payload.get("allowed_runtime_apply") is not False:
        blocked.append("artifact_allowed_runtime_apply_must_be_false")
    elif payload.get("broker_order_forbidden") is not True:
        blocked.append("broker_order_forbidden_contract_missing")
    if not catalog_path.exists():
        blocked.append("swing_sim_policy_catalog_missing")
    else:
        catalog_payload = _load_json(catalog_path)
        if not catalog_payload:
            blocked.append("swing_sim_policy_catalog_invalid")
        elif catalog_payload.get("schema_version") != "swing_sim_policy_catalog_v1":
            blocked.append("swing_sim_policy_catalog_schema_invalid")
        else:
            for policy in catalog_payload.get("active_arm_priority_policies") or []:
                if not isinstance(policy, dict):
                    blocked.append("swing_active_arm_priority_policy_invalid")
                    break
                if str(policy.get("status") or "") not in {"active", "cooldown", "retired"}:
                    blocked.append("swing_active_arm_priority_status_invalid")
                    break
                if not str(policy.get("priority_policy_id") or "").strip():
                    blocked.append("swing_active_arm_priority_policy_id_missing")
                    break
                if str(policy.get("status") or "") == "active" and not str(policy.get("priority_arm_id") or policy.get("priority_bucket_id") or "").strip():
                    blocked.append("swing_active_arm_priority_key_missing")
                    break
                if str(policy.get("status") or "") == "active" and not str(policy.get("source_report_date") or "").strip():
                    blocked.append("swing_active_arm_priority_source_date_missing")
                    break
    approved_request = None
    if not blocked:
        approved_source_ids = [str(item) for item in (payload.get("approved_source_ids") or [])]
        active_policy_ids = [
            str(policy.get("priority_policy_id") or "").strip()
            for policy in (catalog_payload.get("active_arm_priority_policies") or [])
            if isinstance(policy, dict)
            and str(policy.get("status") or "") == "active"
            and str(policy.get("priority_policy_id") or "").strip()
        ]
        approved_request = {
            "family": "swing_sim_auto_approval",
            "policy_id": "swing_sim_auto_approval",
            "stage": "swing_sim_lifecycle",
            "priority": 88,
            "approval_id": f"swing_sim_auto_approval:{source_date}",
            "approval_state": "auto_sim",
            "allowed_runtime_apply": True,
            "safety_revert_required": False,
            "calibration_state": "sim_auto_approved",
            "target_env_keys": [
                "SWING_SIM_AUTO_POLICY_ENABLED",
                "SWING_SIM_AUTO_POLICY_FILE",
                "SWING_SIM_AUTO_POLICY_VERSION",
                "SWING_SIM_AUTO_BOTTOM_REBOUND_SOURCE_ENABLED",
            ],
            "recommended_values": {
                "enabled": True,
                "policy_file": str(catalog_path),
                "policy_version": f"swing_sim_auto_approval:{source_date}",
                "bottom_rebound_source_enabled": "bottom_rebound_policy_auto_loop" in set(approved_source_ids),
            },
            "current_values": {
                "enabled": False,
                "policy_file": "",
                "policy_version": "",
                "bottom_rebound_source_enabled": False,
            },
            "approved_source_ids": approved_source_ids,
            "approved_policy_count": int(payload.get("approved_policy_count") or 0),
            "active_arm_priority_policy_ids": active_policy_ids,
            "actual_order_submitted": False,
            "decision_authority": "swing_sim_auto_approval_control_tower",
        }
    return {
        "artifact": str(artifact_path) if artifact_path.exists() else None,
        "catalog": str(catalog_path) if catalog_path.exists() else None,
        "approved_request": approved_request,
        "blocked": blocked,
        "approved_source_ids": payload.get("approved_source_ids") or [],
        "approved_policy_count": payload.get("approved_policy_count"),
    }


def _select_swing_sim_auto_approval(bundle: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, str]]:
    item = bundle.get("approved_request")
    decisions: list[dict[str, Any]] = []
    selected: list[dict[str, Any]] = []
    env_overrides: dict[str, str] = {}
    if not isinstance(item, dict):
        decisions.append(
            {
                "family": "swing_sim_auto_approval",
                "selected": False,
                "decision_reason": ",".join(str(reason) for reason in bundle.get("blocked") or []) or "swing_sim_auto_approval_missing",
                "env_overrides": {},
                "actual_order_submitted": False,
            }
        )
        return selected, decisions, env_overrides
    overrides = _env_overrides_for_candidate(item)
    reject_reason = ""
    if not bool(item.get("allowed_runtime_apply")):
        reject_reason = "runtime_apply_not_allowed"
    elif bool(item.get("actual_order_submitted")):
        reject_reason = "actual_order_submitted_not_allowed"
    elif not overrides:
        reject_reason = "no_runtime_env_override"
    decision = {
        "approval_id": item.get("approval_id"),
        "family": item.get("family"),
        "stage": item.get("stage"),
        "approved_source_ids": item.get("approved_source_ids") or [],
        "selected": not bool(reject_reason),
        "decision_reason": reject_reason or "swing_sim_auto_approval_apply",
        "env_overrides": overrides if not reject_reason else {},
        "actual_order_submitted": False,
    }
    decisions.append(decision)
    if reject_reason:
        return selected, decisions, env_overrides
    selected.append(item)
    env_overrides.update(overrides)
    return selected, decisions, env_overrides


def _ai_guard_allows_candidate(candidate: dict[str, Any], ai_review: dict[str, Any], *, require_ai: bool) -> tuple[bool, str]:
    if str(candidate.get("family") or "") == "latency_classifier_runtime_profile":
        return (True, "deterministic_latency_classifier_recommendation")
    items_by_family = ai_review.get("items_by_family") if isinstance(ai_review.get("items_by_family"), dict) else {}
    item = items_by_family.get(str(candidate.get("family") or ""))
    if not item:
        return (not require_ai, "ai_review_missing" if require_ai else "ai_review_missing_deterministic_allowed")
    guard_decision = item.get("guard_decision") if isinstance(item.get("guard_decision"), dict) else {}
    route_action = str(item.get("route_action") or guard_decision.get("route_action") or "")
    if (
        _score65_74_entry_unlock_candidate(candidate)
        and route_action == "exclude_from_threshold_candidate_review"
        and str(guard_decision.get("anomaly_route") or item.get("ai_anomaly_route") or "") == "instrumentation_gap"
    ):
        return (True, "entry_unlock_probe_ready_overrides_no_applied_probe_gap")
    if str(item.get("guard_decision") or "").lower() != "accept" and not bool(item.get("guard_accepted")):
        return (False, str(item.get("guard_reject_reason") or "ai_guard_rejected"))
    if route_action in AUTO_APPLY_ROUTE_EXCLUDE_ACTIONS:
        return (False, "ai_route_excluded_from_threshold_candidate")
    route = str(item.get("ai_anomaly_route") or "")
    if route not in AUTO_APPLY_ALLOWED_ROUTES:
        return (False, f"ai_route_not_runtime_apply:{route}")
    return (True, "ai_guard_accepted")


def _additive_entry_operator_lock_stage_coexist(
    *,
    family: str,
    stage: str,
    selected_by_stage: dict[str, dict[str, Any]],
    locks_by_family: dict[str, dict[str, Any]],
) -> bool:
    additive_entry_lock_families = {
        SCALPING_SCANNER_REAL_SOURCE_GUARD_FAMILY,
        SCORE65_74_STRONG_MICRO_OVERRIDE_FAMILY,
        EARLY_ACCEL_RECHECK_FAMILY,
        AI_NUMERIC_CONSISTENCY_RECHECK_FAMILY,
        PRE_SUBMIT_LIQUIDITY_RELIEF_FAMILY,
        WEAK_CONTEXT_LATE_ENTRY_GUARD_FAMILY,
        ENTRY_OPPORTUNITY_RECHECK_FAMILY,
    }
    if family not in additive_entry_lock_families or stage not in selected_by_stage:
        return False
    if family not in locks_by_family:
        return False
    previous = selected_by_stage[stage]
    previous_family = str(previous.get("family") or "")
    return (
        str(previous.get("calibration_state") or "") == "operator_locked"
        or previous_family in locks_by_family
    )


def _operator_lock_stage_coexist(
    *,
    family: str,
    stage: str,
    selected_by_stage: dict[str, dict[str, Any]],
    locks_by_family: dict[str, dict[str, Any]],
) -> bool:
    if _additive_entry_operator_lock_stage_coexist(
        family=family,
        stage=stage,
        selected_by_stage=selected_by_stage,
        locks_by_family=locks_by_family,
    ):
        return True
    if stage not in selected_by_stage:
        return False
    previous = selected_by_stage[stage]
    previous_family = str(previous.get("family") or "")
    return (
        stage == "holding_exit"
        and {family, previous_family} == {PRESET_TP_SOFT_STOP_FAMILY, PROFIT_STAGNATION_EXIT_FAMILY}
    )


def _select_auto_apply_candidates(
    calibration_candidates: list[dict[str, Any]],
    *,
    ai_review: dict[str, Any],
    require_ai: bool,
    target_date: str = "",
    include_families: set[str] | None = None,
    operator_locks: list[dict[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, str]]:
    selected_by_stage: dict[str, dict[str, Any]] = {}
    decisions: list[dict[str, Any]] = []
    locks_by_family = {
        str(lock.get("family") or ""): lock
        for lock in (operator_locks or [])
        if isinstance(lock, dict) and lock.get("family")
    }
    candidates = list(calibration_candidates)
    present_families = {str(item.get("family") or "") for item in candidates if isinstance(item, dict)}
    for family, lock in locks_by_family.items():
        if family not in present_families:
            candidates.append(_locked_synthetic_candidate(lock))
    previous_selected_families, previous_runtime_manifest = _load_previous_runtime_env_selected_families(
        target_date
    )
    for candidate in sorted(candidates, key=lambda item: int(item.get("priority") or 999)):
        family = str(candidate.get("family") or "")
        stage = str(candidate.get("stage") or "unknown")
        state = str(candidate.get("calibration_state") or "")
        lock = locks_by_family.get(family)
        allowed, reason = _ai_guard_allows_candidate(candidate, ai_review, require_ai=require_ai)
        contract_blockers = _candidate_apply_contract_blockers(candidate)
        reject_reason = ""
        hold_carry_forward = False
        hold_carry_forward_blockers: list[str] = []
        hold_carry_forward_env_overrides: dict[str, str] = {}
        if family in RETIRED_RUNTIME_FAMILY_REASONS:
            reject_reason = RETIRED_RUNTIME_FAMILY_REASONS[family]
        elif include_families is not None and family not in include_families:
            reject_reason = "operator_family_filter_excluded"
        elif family in NON_LIVE_SELECTABLE_FAMILIES or str(candidate.get("family_type") or "") == "sim_lifecycle_source":
            reject_reason = "non_live_selectable_sim_lifecycle_source"
        elif not bool(candidate.get("allowed_runtime_apply")):
            reject_reason = "runtime_apply_not_allowed"
        elif bool(candidate.get("safety_revert_required")):
            reject_reason = "safety_revert_required"
        elif state in HOLD_CARRY_FORWARD_STATES:
            previously_enabled = family in previous_selected_families
            if not previously_enabled:
                reject_reason = "hold_not_previously_enabled"
            else:
                hold_carry_forward_blockers = _hold_carry_forward_blockers(candidate)
                if stage in selected_by_stage:
                    hold_carry_forward_blockers.append("same_stage_owner_conflict")
                if hold_carry_forward_blockers:
                    reject_reason = (
                        f"hold_carry_forward_blocked:{','.join(hold_carry_forward_blockers)}"
                    )
                else:
                    hold_carry_forward_env_overrides = (
                        _previous_runtime_env_overrides_for_family(
                            previous_runtime_manifest, family
                        )
                    )
                    if not hold_carry_forward_env_overrides:
                        reject_reason = "hold_carry_forward_no_previous_env"
                    else:
                        hold_carry_forward = True
                        reject_reason = ""
                        reason = f"hold_carry_forward_previous_runtime:{family}"
        elif contract_blockers:
            reject_reason = ",".join(contract_blockers)
        elif state in AUTO_APPLY_BLOCK_STATES or state not in AUTO_APPLY_ALLOWED_STATES:
            reject_reason = f"calibration_state_blocked:{state}"
        elif not allowed:
            reject_reason = reason
        elif not _env_overrides_for_candidate(candidate):
            reject_reason = "no_runtime_env_override"
        elif stage in selected_by_stage and not _operator_lock_stage_coexist(
            family=family,
            stage=stage,
            selected_by_stage=selected_by_stage,
            locks_by_family=locks_by_family,
        ):
            reject_reason = f"same_stage_owner_conflict:{selected_by_stage[stage].get('family')}"

        lock_applied = False
        lock_stage_conflict_reason = ""
        if lock and stage in selected_by_stage and not _operator_lock_stage_coexist(
            family=family,
            stage=stage,
            selected_by_stage=selected_by_stage,
            locks_by_family=locks_by_family,
        ):
            lock_stage_conflict_reason = f"same_stage_owner_conflict:{selected_by_stage[stage].get('family')}"
        lock_close_reasons = _candidate_close_reasons(candidate, reject_reason)
        if lock_stage_conflict_reason:
            lock_close_reasons.append(lock_stage_conflict_reason)
        if lock and family not in RETIRED_RUNTIME_FAMILY_REASONS and (
            include_families is None or family in include_families
        ):
            lock_overrides = _lock_env_overrides(lock)
            lock_allowed_close = _lock_allows_close(lock, lock_close_reasons)
            lock_can_preserve = bool(lock_overrides) and not lock_allowed_close and not contract_blockers
            if lock_can_preserve:
                reject_reason = ""
                reason = f"operator_runtime_env_lock_preserved:{lock.get('lock_id') or family}"
                hold_carry_forward = False
                lock_applied = True
            elif bool(lock_overrides):
                if lock_stage_conflict_reason:
                    reject_reason = lock_stage_conflict_reason
                reason = f"operator_runtime_env_lock_allowed_close:{lock.get('lock_id') or family}"

        decision = {
            "family": family,
            "stage": stage,
            "priority": int(candidate.get("priority") or 999),
            "calibration_state": state,
            "threshold_version": candidate.get("threshold_version"),
            "selected": not bool(reject_reason),
            "decision_reason": reject_reason or reason,
            "env_overrides": (
                _lock_env_overrides(lock)
                if lock_applied and lock
                else hold_carry_forward_env_overrides
                if hold_carry_forward
                else _env_overrides_for_candidate(candidate)
                if not reject_reason
                else {}
            ),
        }
        if hold_carry_forward:
            decision["hold_carry_forward"] = {
                "previous_runtime_env_family": family,
                "previous_selected": True,
                "carry_forward_blockers": hold_carry_forward_blockers,
            }
        if lock:
            decision["operator_runtime_env_lock"] = {
                "lock_id": lock.get("lock_id"),
                "path": lock.get("path"),
                "applied": bool(lock_applied),
                "close_reasons": lock_close_reasons,
                "allowed_close": _lock_allows_close(lock, lock_close_reasons),
                "allowed_close_reason_keywords": list(
                    lock.get("allowed_close_reason_keywords") or []
                ),
            }
        if reject_reason:
            decisions.append(decision)
            continue
        selected_by_stage[stage] = candidate
        decisions.append(decision)

    selected_decisions = [decision for decision in decisions if bool(decision.get("selected"))]
    env_overrides: dict[str, str] = {}
    for decision in selected_decisions:
        env_overrides.update(decision.get("env_overrides") or {})
    return selected_decisions, decisions, env_overrides


def _entry_price_live_owner_family(*selected_groups: list[dict[str, Any]]) -> str:
    for group in selected_groups:
        for item in group or []:
            if not isinstance(item, dict):
                continue
            family = str(item.get("family") or "")
            if family in {
                AGGRESSIVE_ENTRY_PRICE_OVERRIDE_FAMILY,
                SCALPING_SCANNER_REAL_SOURCE_GUARD_FAMILY,
                SCORE65_74_STRONG_MICRO_OVERRIDE_FAMILY,
                EARLY_ACCEL_RECHECK_FAMILY,
                AI_NUMERIC_CONSISTENCY_RECHECK_FAMILY,
                PRE_SUBMIT_LIQUIDITY_RELIEF_FAMILY,
                WEAK_CONTEXT_LATE_ENTRY_GUARD_FAMILY,
            }:
                continue
            if str(item.get("stage") or "") == "entry":
                return family
    return ""


def _entry_live_tuning_owner_family(*selected_groups: list[dict[str, Any]]) -> str:
    for group in selected_groups:
        for item in group or []:
            if not isinstance(item, dict):
                continue
            family = str(item.get("family") or "")
            if family in {
                AGGRESSIVE_ENTRY_PRICE_OVERRIDE_FAMILY,
                SCALPING_SCANNER_REAL_SOURCE_GUARD_FAMILY,
                SCORE65_74_STRONG_MICRO_OVERRIDE_FAMILY,
                EARLY_ACCEL_RECHECK_FAMILY,
                AI_NUMERIC_CONSISTENCY_RECHECK_FAMILY,
                PRE_SUBMIT_LIQUIDITY_RELIEF_FAMILY,
                WEAK_CONTEXT_LATE_ENTRY_GUARD_FAMILY,
            }:
                continue
            if str(item.get("stage") or "") != "entry":
                continue
            if str(item.get("calibration_state") or "") == "operator_locked":
                continue
            if isinstance(item.get("operator_runtime_env_lock"), dict):
                continue
            return family
    return ""


def _close_scalping_scanner_real_source_guard_for_live_owner(
    *,
    selected: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
    env_overrides: dict[str, str],
    owner_family: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, str]]:
    if not owner_family:
        return selected, decisions, env_overrides
    reason = f"same_stage_owner_conflict:{owner_family}"
    filtered_selected = [
        item
        for item in selected
        if str(item.get("family") or "") != SCALPING_SCANNER_REAL_SOURCE_GUARD_FAMILY
    ]
    filtered_env = {
        key: value
        for key, value in env_overrides.items()
        if str(key) not in SCALPING_SCANNER_REAL_SOURCE_GUARD_ENV_KEYS
    }
    updated_decisions: list[dict[str, Any]] = []
    for decision in decisions:
        if str(decision.get("family") or "") != SCALPING_SCANNER_REAL_SOURCE_GUARD_FAMILY:
            updated_decisions.append(decision)
            continue
        next_decision = {**decision, "selected": False, "decision_reason": reason, "env_overrides": {}}
        lock = next_decision.get("operator_runtime_env_lock")
        if isinstance(lock, dict):
            close_reasons = list(lock.get("close_reasons") or [])
            if reason not in close_reasons:
                close_reasons.append(reason)
            next_decision["operator_runtime_env_lock"] = {
                **lock,
                "applied": False,
                "close_reasons": close_reasons,
                "allowed_close": _lock_allows_close(lock, close_reasons),
            }
        updated_decisions.append(next_decision)
    return filtered_selected, updated_decisions, filtered_env


def _close_score65_74_strong_micro_override_for_live_owner(
    *,
    selected: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
    env_overrides: dict[str, str],
    owner_family: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, str]]:
    if not owner_family:
        return selected, decisions, env_overrides
    reason = f"same_stage_owner_conflict:{owner_family}"
    filtered_selected = [
        item
        for item in selected
        if str(item.get("family") or "") != SCORE65_74_STRONG_MICRO_OVERRIDE_FAMILY
    ]
    filtered_env = {
        key: value
        for key, value in env_overrides.items()
        if str(key) not in SCORE65_74_STRONG_MICRO_OVERRIDE_ENV_KEYS
    }
    updated_decisions: list[dict[str, Any]] = []
    for decision in decisions:
        if str(decision.get("family") or "") != SCORE65_74_STRONG_MICRO_OVERRIDE_FAMILY:
            updated_decisions.append(decision)
            continue
        next_decision = {**decision, "selected": False, "decision_reason": reason, "env_overrides": {}}
        lock = next_decision.get("operator_runtime_env_lock")
        if isinstance(lock, dict):
            close_reasons = list(lock.get("close_reasons") or [])
            if reason not in close_reasons:
                close_reasons.append(reason)
            next_decision["operator_runtime_env_lock"] = {
                **lock,
                "applied": False,
                "close_reasons": close_reasons,
                "allowed_close": _lock_allows_close(lock, close_reasons),
            }
        updated_decisions.append(next_decision)
    return filtered_selected, updated_decisions, filtered_env


def _close_early_accel_recheck_for_live_owner(
    *,
    selected: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
    env_overrides: dict[str, str],
    owner_family: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, str]]:
    if not owner_family:
        return selected, decisions, env_overrides
    reason = f"same_stage_owner_conflict:{owner_family}"
    filtered_selected = [
        item
        for item in selected
        if str(item.get("family") or "") != EARLY_ACCEL_RECHECK_FAMILY
    ]
    filtered_env = {
        key: value
        for key, value in env_overrides.items()
        if str(key) not in EARLY_ACCEL_RECHECK_ENV_KEYS
    }
    updated_decisions: list[dict[str, Any]] = []
    for decision in decisions:
        if str(decision.get("family") or "") != EARLY_ACCEL_RECHECK_FAMILY:
            updated_decisions.append(decision)
            continue
        next_decision = {**decision, "selected": False, "decision_reason": reason, "env_overrides": {}}
        lock = next_decision.get("operator_runtime_env_lock")
        if isinstance(lock, dict):
            close_reasons = list(lock.get("close_reasons") or [])
            if reason not in close_reasons:
                close_reasons.append(reason)
            next_decision["operator_runtime_env_lock"] = {
                **lock,
                "applied": False,
                "close_reasons": close_reasons,
                "allowed_close": _lock_allows_close(lock, close_reasons),
            }
        updated_decisions.append(next_decision)
    return filtered_selected, updated_decisions, filtered_env


def _close_ai_numeric_consistency_recheck_for_live_owner(
    *,
    selected: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
    env_overrides: dict[str, str],
    owner_family: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, str]]:
    if not owner_family:
        return selected, decisions, env_overrides
    reason = f"same_stage_owner_conflict:{owner_family}"
    filtered_selected = [
        item
        for item in selected
        if str(item.get("family") or "") != AI_NUMERIC_CONSISTENCY_RECHECK_FAMILY
    ]
    filtered_env = {
        key: value
        for key, value in env_overrides.items()
        if str(key) not in AI_NUMERIC_CONSISTENCY_RECHECK_ENV_KEYS
    }
    updated_decisions: list[dict[str, Any]] = []
    for decision in decisions:
        if str(decision.get("family") or "") != AI_NUMERIC_CONSISTENCY_RECHECK_FAMILY:
            updated_decisions.append(decision)
            continue
        next_decision = {**decision, "selected": False, "decision_reason": reason, "env_overrides": {}}
        lock = next_decision.get("operator_runtime_env_lock")
        if isinstance(lock, dict):
            close_reasons = list(lock.get("close_reasons") or [])
            if reason not in close_reasons:
                close_reasons.append(reason)
            next_decision["operator_runtime_env_lock"] = {
                **lock,
                "applied": False,
                "close_reasons": close_reasons,
                "allowed_close": _lock_allows_close(lock, close_reasons),
            }
        updated_decisions.append(next_decision)
    return filtered_selected, updated_decisions, filtered_env


def _close_pre_submit_liquidity_relief_for_live_owner(
    *,
    selected: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
    env_overrides: dict[str, str],
    owner_family: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, str]]:
    if not owner_family:
        return selected, decisions, env_overrides
    reason = f"same_stage_owner_conflict:{owner_family}"
    filtered_selected = [
        item
        for item in selected
        if str(item.get("family") or "") != PRE_SUBMIT_LIQUIDITY_RELIEF_FAMILY
    ]
    filtered_env = {
        key: value
        for key, value in env_overrides.items()
        if str(key) not in PRE_SUBMIT_LIQUIDITY_RELIEF_ENV_KEYS
    }
    updated_decisions: list[dict[str, Any]] = []
    for decision in decisions:
        if str(decision.get("family") or "") != PRE_SUBMIT_LIQUIDITY_RELIEF_FAMILY:
            updated_decisions.append(decision)
            continue
        next_decision = {**decision, "selected": False, "decision_reason": reason, "env_overrides": {}}
        lock = next_decision.get("operator_runtime_env_lock")
        if isinstance(lock, dict):
            close_reasons = list(lock.get("close_reasons") or [])
            if reason not in close_reasons:
                close_reasons.append(reason)
            next_decision["operator_runtime_env_lock"] = {
                **lock,
                "applied": False,
                "close_reasons": close_reasons,
                "allowed_close": _lock_allows_close(lock, close_reasons),
            }
        updated_decisions.append(next_decision)
    return filtered_selected, updated_decisions, filtered_env


def _close_weak_context_late_entry_guard_for_live_owner(
    *,
    selected: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
    env_overrides: dict[str, str],
    owner_family: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, str]]:
    if not owner_family:
        return selected, decisions, env_overrides
    reason = f"same_stage_owner_conflict:{owner_family}"
    filtered_selected = [
        item
        for item in selected
        if str(item.get("family") or "") != WEAK_CONTEXT_LATE_ENTRY_GUARD_FAMILY
    ]
    filtered_env = {
        key: value
        for key, value in env_overrides.items()
        if str(key) not in WEAK_CONTEXT_LATE_ENTRY_GUARD_ENV_KEYS
    }
    updated_decisions: list[dict[str, Any]] = []
    for decision in decisions:
        if str(decision.get("family") or "") != WEAK_CONTEXT_LATE_ENTRY_GUARD_FAMILY:
            updated_decisions.append(decision)
            continue
        next_decision = {**decision, "selected": False, "decision_reason": reason, "env_overrides": {}}
        lock = next_decision.get("operator_runtime_env_lock")
        if isinstance(lock, dict):
            close_reasons = list(lock.get("close_reasons") or [])
            if reason not in close_reasons:
                close_reasons.append(reason)
            next_decision["operator_runtime_env_lock"] = {
                **lock,
                "applied": False,
                "close_reasons": close_reasons,
                "allowed_close": _lock_allows_close(lock, close_reasons),
            }
        updated_decisions.append(next_decision)
    return filtered_selected, updated_decisions, filtered_env


def _holding_exit_live_owner_family(*selected_groups: list[dict[str, Any]]) -> str:
    for group in selected_groups:
        for item in group or []:
            if not isinstance(item, dict):
                continue
            family = str(item.get("family") or "")
            if family in {SOFT_STOP_DYNAMIC_GRACE_FAMILY, PRESET_TP_SOFT_STOP_FAMILY, NEVER_GREEN_DEFER_CLAMP_FAMILY}:
                continue
            stage = str(item.get("stage") or "")
            if stage in {"holding_exit", "holding", "exit"}:
                return family
    return ""


def _scale_in_live_owner_family(*selected_groups: list[dict[str, Any]]) -> str:
    for group in selected_groups:
        for item in group or []:
            if not isinstance(item, dict):
                continue
            family = str(item.get("family") or "")
            if family == REAL_PYRAMID_SCALE_IN_QUALITY_GUARD_FAMILY:
                continue
            stage = str(item.get("stage") or "")
            if stage == "scale_in":
                return family
    return ""


def _preset_tp_exit_live_owner_family(*selected_groups: list[dict[str, Any]]) -> str:
    for group in selected_groups:
        for item in group or []:
            if not isinstance(item, dict):
                continue
            family = str(item.get("family") or "")
            if family in {PRESET_TP_SOFT_STOP_FAMILY, PROFIT_STAGNATION_EXIT_FAMILY}:
                continue
            stage = str(item.get("stage") or "")
            if stage in {"holding_exit", "holding", "exit"}:
                return family
    return ""


def _close_aggressive_entry_price_override_for_live_owner(
    *,
    selected: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
    env_overrides: dict[str, str],
    owner_family: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, str]]:
    if not owner_family:
        return selected, decisions, env_overrides
    reason = f"same_stage_owner_conflict:{owner_family}"
    filtered_selected = [
        item
        for item in selected
        if str(item.get("family") or "") != AGGRESSIVE_ENTRY_PRICE_OVERRIDE_FAMILY
    ]
    filtered_env = {
        key: value
        for key, value in env_overrides.items()
        if str(key) not in AGGRESSIVE_ENTRY_PRICE_OVERRIDE_ENV_KEYS
    }
    updated_decisions: list[dict[str, Any]] = []
    for decision in decisions:
        if str(decision.get("family") or "") != AGGRESSIVE_ENTRY_PRICE_OVERRIDE_FAMILY:
            updated_decisions.append(decision)
            continue
        next_decision = {**decision, "selected": False, "decision_reason": reason, "env_overrides": {}}
        lock = next_decision.get("operator_runtime_env_lock")
        if isinstance(lock, dict):
            close_reasons = list(lock.get("close_reasons") or [])
            if reason not in close_reasons:
                close_reasons.append(reason)
            next_decision["operator_runtime_env_lock"] = {
                **lock,
                "applied": False,
                "close_reasons": close_reasons,
                "allowed_close": True,
            }
        updated_decisions.append(next_decision)
    return filtered_selected, updated_decisions, filtered_env


def _close_never_green_defer_clamp_for_live_owner(
    *,
    selected: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
    env_overrides: dict[str, str],
    owner_family: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, str]]:
    if not owner_family:
        return selected, decisions, env_overrides
    reason = f"same_stage_owner_conflict:{owner_family}"
    filtered_selected = [
        item
        for item in selected
        if str(item.get("family") or "") != NEVER_GREEN_DEFER_CLAMP_FAMILY
    ]
    filtered_env = {
        key: value
        for key, value in env_overrides.items()
        if str(key) not in NEVER_GREEN_DEFER_CLAMP_ENV_KEYS
    }
    updated_decisions: list[dict[str, Any]] = []
    for decision in decisions:
        if str(decision.get("family") or "") != NEVER_GREEN_DEFER_CLAMP_FAMILY:
            updated_decisions.append(decision)
            continue
        next_decision = {**decision, "selected": False, "decision_reason": reason, "env_overrides": {}}
        lock = next_decision.get("operator_runtime_env_lock")
        if isinstance(lock, dict):
            close_reasons = list(lock.get("close_reasons") or [])
            if reason not in close_reasons:
                close_reasons.append(reason)
            next_decision["operator_runtime_env_lock"] = {
                **lock,
                "applied": False,
                "close_reasons": close_reasons,
                "allowed_close": _lock_allows_close(lock, close_reasons),
            }
        updated_decisions.append(next_decision)
    return filtered_selected, updated_decisions, filtered_env


def _close_real_pyramid_scale_in_quality_guard_for_live_owner(
    *,
    selected: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
    env_overrides: dict[str, str],
    owner_family: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, str]]:
    if not owner_family:
        return selected, decisions, env_overrides
    reason = f"same_stage_owner_conflict:{owner_family}"
    filtered_selected = [
        item
        for item in selected
        if str(item.get("family") or "") != REAL_PYRAMID_SCALE_IN_QUALITY_GUARD_FAMILY
    ]
    filtered_env = {
        key: value
        for key, value in env_overrides.items()
        if str(key) not in REAL_PYRAMID_SCALE_IN_QUALITY_GUARD_ENV_KEYS
    }
    updated_decisions: list[dict[str, Any]] = []
    for decision in decisions:
        if str(decision.get("family") or "") != REAL_PYRAMID_SCALE_IN_QUALITY_GUARD_FAMILY:
            updated_decisions.append(decision)
            continue
        next_decision = {**decision, "selected": False, "decision_reason": reason, "env_overrides": {}}
        lock = next_decision.get("operator_runtime_env_lock")
        if isinstance(lock, dict):
            close_reasons = list(lock.get("close_reasons") or [])
            if reason not in close_reasons:
                close_reasons.append(reason)
            next_decision["operator_runtime_env_lock"] = {
                **lock,
                "applied": False,
                "close_reasons": close_reasons,
                "allowed_close": _lock_allows_close(lock, close_reasons),
            }
        updated_decisions.append(next_decision)
    return filtered_selected, updated_decisions, filtered_env


def _close_soft_stop_dynamic_grace_for_live_owner(
    *,
    selected: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
    env_overrides: dict[str, str],
    owner_family: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, str]]:
    if not owner_family:
        return selected, decisions, env_overrides
    reason = f"same_stage_owner_conflict:{owner_family}"
    filtered_selected = [
        item
        for item in selected
        if str(item.get("family") or "") != SOFT_STOP_DYNAMIC_GRACE_FAMILY
    ]
    filtered_env = {
        key: value
        for key, value in env_overrides.items()
        if str(key) not in SOFT_STOP_DYNAMIC_GRACE_ENV_KEYS
    }
    updated_decisions: list[dict[str, Any]] = []
    for decision in decisions:
        if str(decision.get("family") or "") != SOFT_STOP_DYNAMIC_GRACE_FAMILY:
            updated_decisions.append(decision)
            continue
        next_decision = {**decision, "selected": False, "decision_reason": reason, "env_overrides": {}}
        lock = next_decision.get("operator_runtime_env_lock")
        if isinstance(lock, dict):
            close_reasons = list(lock.get("close_reasons") or [])
            if reason not in close_reasons:
                close_reasons.append(reason)
            next_decision["operator_runtime_env_lock"] = {
                **lock,
                "applied": False,
                "close_reasons": close_reasons,
                "allowed_close": _lock_allows_close(lock, close_reasons),
            }
        updated_decisions.append(next_decision)
    return filtered_selected, updated_decisions, filtered_env


def _close_preset_tp_soft_stop_for_live_owner(
    *,
    selected: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
    env_overrides: dict[str, str],
    owner_family: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, str]]:
    if not owner_family:
        return selected, decisions, env_overrides
    reason = f"same_stage_owner_conflict:{owner_family}"
    filtered_selected = [
        item
        for item in selected
        if str(item.get("family") or "") != PRESET_TP_SOFT_STOP_FAMILY
    ]
    filtered_env = {
        key: value
        for key, value in env_overrides.items()
        if str(key) not in PRESET_TP_SOFT_STOP_ENV_KEYS
    }
    updated_decisions: list[dict[str, Any]] = []
    for decision in decisions:
        if str(decision.get("family") or "") != PRESET_TP_SOFT_STOP_FAMILY:
            updated_decisions.append(decision)
            continue
        next_decision = {**decision, "selected": False, "decision_reason": reason, "env_overrides": {}}
        lock = next_decision.get("operator_runtime_env_lock")
        if isinstance(lock, dict):
            close_reasons = list(lock.get("close_reasons") or [])
            if reason not in close_reasons:
                close_reasons.append(reason)
            next_decision["operator_runtime_env_lock"] = {
                **lock,
                "applied": False,
                "close_reasons": close_reasons,
                "allowed_close": _lock_allows_close(lock, close_reasons),
            }
        updated_decisions.append(next_decision)
    return filtered_selected, updated_decisions, filtered_env


def _lifecycle_ai_context_overlay_env(
    calibration_candidates: list[dict[str, Any]],
    *,
    include_families: set[str] | None = None,
) -> tuple[dict[str, Any], dict[str, str]]:
    if include_families is not None and "lifecycle_decision_matrix_runtime" not in include_families:
        return (
            {
                "selected": False,
                "decision_reason": "operator_family_filter_excluded",
                "env_overrides": {},
            },
            {},
        )
    candidate = next(
        (
            item
            for item in calibration_candidates
            if isinstance(item, dict) and str(item.get("family") or "") == "lifecycle_decision_matrix_runtime"
        ),
        None,
    )
    if not candidate:
        return (
            {
                "selected": False,
                "decision_reason": "lifecycle_decision_matrix_runtime_candidate_missing",
                "env_overrides": {},
            },
            {},
        )
    recommended = candidate.get("recommended_values") if isinstance(candidate.get("recommended_values"), dict) else {}
    context_file = str(recommended.get("lifecycle_ai_context_file") or "")
    if not bool(recommended.get("lifecycle_ai_context_enabled")) or not context_file:
        return (
            {
                "selected": False,
                "decision_reason": "lifecycle_ai_context_artifact_missing_or_disabled",
                "env_overrides": {},
            },
            {},
        )

    overlay_values = {
        "LIFECYCLE_DECISION_MATRIX_RUNTIME_EFFECT_ENABLED": False,
        "LIFECYCLE_AI_CONTEXT_ENABLED": True,
        "LIFECYCLE_AI_CONTEXT_FILE": context_file,
        "LIFECYCLE_AI_CONTEXT_VERSION": str(recommended.get("lifecycle_ai_context_version") or ""),
        "SCALP_ENTRY_ADM_ADVISORY_ENABLED": bool(recommended.get("entry_adm_advisory_enabled", True)),
        "SCALP_ENTRY_ADM_RUNTIME_BIAS_ENABLED": False,
        "HOLDING_EXIT_MATRIX_ADVISORY_ENABLED": bool(
            recommended.get("holding_exit_matrix_advisory_enabled", True)
        ),
        "HOLDING_EXIT_MATRIX_RUNTIME_BIAS_ENABLED": False,
        "HOLDING_EXIT_MATRIX_SCALE_IN_BIAS_ENABLED": False,
    }
    env_overrides = {
        _runtime_env_name(key): _format_env_value(value)
        for key, value in overlay_values.items()
        if key in TARGET_ENV_VALUE_KEYS
    }
    decision = {
        "family": "lifecycle_ai_context",
        "source_family": "lifecycle_decision_matrix_runtime",
        "family_type": "context_only_env_overlay",
        "selected": True,
        "decision_reason": "context_only_advisory_prompt_overlay_bias_off",
        "runtime_effect": False,
        "decision_authority": "ai_advisory_prompt_context_only",
        "live_selectable": False,
        "standalone_threshold_family": False,
        "env_overrides": env_overrides,
    }
    return decision, env_overrides


SELECTED_FAMILY_REQUIRED_ENV_KEYS: dict[str, list[str]] = {
    "entry_cancel_wait_runtime": [
        "KORSTOCKSCAN_ENTRY_CANCEL_WAIT_ATTRIBUTION_ENABLED",
        "KORSTOCKSCAN_SCALPING_ENTRY_TIMEOUT_SEC",
        "KORSTOCKSCAN_SCALPING_BREAKOUT_ENTRY_TIMEOUT_SEC",
        "KORSTOCKSCAN_SCALPING_PULLBACK_ENTRY_TIMEOUT_SEC",
        "KORSTOCKSCAN_SCALPING_RESERVE_ENTRY_TIMEOUT_SEC",
    ],
    "soft_stop_whipsaw_confirmation": [
        "KORSTOCKSCAN_SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_ENABLED",
    ],
    "score65_74_recovery_probe": [
        "KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED",
    ],
    "scalp_sim_candidate_window_expansion": [
        "KORSTOCKSCAN_SCALP_SIM_CANDIDATE_WINDOW_EXPANSION_ENABLED",
    ],
    "scalp_sim_ai_budget_manager": [
        "KORSTOCKSCAN_SCALP_SIM_AI_BUDGET_ENABLED",
    ],
    "lifecycle_decision_matrix_runtime": [
        "KORSTOCKSCAN_LIFECYCLE_DECISION_MATRIX_ENABLED",
    ],
    "lifecycle_bucket_discovery_sim_auto_approval": [
        "KORSTOCKSCAN_LIFECYCLE_BUCKET_DISCOVERY_ENABLED",
        "KORSTOCKSCAN_LIFECYCLE_BUCKET_DISCOVERY_POLICY_FILE",
        "KORSTOCKSCAN_LIFECYCLE_BUCKET_DISCOVERY_POLICY_VERSION",
        "KORSTOCKSCAN_LIFECYCLE_BUCKET_DISCOVERY_LIVE_AUTO_APPLY_ENABLED",
    ],
    "scalp_sim_auto_approval": [
        "KORSTOCKSCAN_SCALP_SIM_AUTO_POLICY_ENABLED",
        "KORSTOCKSCAN_SCALP_SIM_AUTO_POLICY_FILE",
        "KORSTOCKSCAN_SCALP_SIM_AUTO_POLICY_VERSION",
        "KORSTOCKSCAN_SCALP_SIM_AUTO_POLICY_SOURCE_DATE",
    ],
    "swing_sim_auto_approval": [
        "KORSTOCKSCAN_SWING_SIM_AUTO_POLICY_ENABLED",
        "KORSTOCKSCAN_SWING_SIM_AUTO_POLICY_FILE",
        "KORSTOCKSCAN_SWING_SIM_AUTO_POLICY_VERSION",
    ],
    "scalp_sim_scale_in_window_expansion": [
        "KORSTOCKSCAN_SCALP_SIM_SCALE_IN_WINDOW_EXPANSION_ENABLED",
        "KORSTOCKSCAN_SCALP_SIM_SCALE_IN_EXECUTION_OBSERVATION_ENABLED",
        "KORSTOCKSCAN_SCALP_SIM_SCALE_IN_EXECUTION_ARMS",
    ],
}


def _read_pid_environ(pid: int) -> dict[str, str]:
    try:
        raw = f"/proc/{pid}/environ"
        text = Path(raw).read_bytes()
        env: dict[str, str] = {}
        for entry in text.split(b"\x00"):
            if not entry:
                continue
            decoded = entry.decode("utf-8", errors="replace")
            if "=" in decoded:
                key, _, value = decoded.partition("=")
                env[key.strip()] = value.strip()
            else:
                env[decoded.strip()] = ""
        return env
    except OSError:
        return {}


def _read_shell_export_env(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if not key:
            continue
        value = value.strip()
        try:
            parts = shlex.split(value, comments=False, posix=True)
            parsed_value = parts[0] if parts else ""
        except ValueError:
            parsed_value = value.strip("\"'")
        values[key] = parsed_value
    return values


def verify_runtime_env_handoff(
    target_date: str,
    *,
    pid: int | None = None,
) -> dict[str, Any]:
    manifest_path = runtime_env_manifest_path(target_date)
    manifest = _load_json(manifest_path) if manifest_path.exists() else {}
    selected_families = [
        str(item)
        for item in (manifest.get("selected_families") or [])
        if isinstance(item, str) and item.strip()
    ]
    env_overrides = manifest.get("env_overrides")
    if not isinstance(env_overrides, dict):
        env_overrides = {}
    operator_override_path = RUNTIME_ENV_DIR / "operator_runtime_overrides.env"
    operator_overrides = _read_shell_export_env(operator_override_path)
    effective_env_overrides = dict(env_overrides)
    effective_env_overrides.update(operator_overrides)
    findings: list[dict[str, Any]] = []
    missing_families: list[str] = []
    for family in selected_families:
        required_keys = SELECTED_FAMILY_REQUIRED_ENV_KEYS.get(family, [])
        if not required_keys:
            continue
        missing = [key for key in required_keys if key not in env_overrides]
        if missing:
            missing_families.append(family)
            findings.append(
                {
                    "family": family,
                    "missing_env_keys": missing,
                    "severity": "runtime_env_handoff_missing",
                    "detail": f"selected family {family} missing required env keys: {','.join(missing)}",
                }
            )
    pid_env: dict[str, str] = {}
    pid_mismatches: list[dict[str, Any]] = []
    pid_missing: list[dict[str, Any]] = []
    if pid is not None:
        pid_env = _read_pid_environ(pid)
        for family in selected_families:
            required_keys = SELECTED_FAMILY_REQUIRED_ENV_KEYS.get(family, [])
            for key in required_keys:
                manifest_value = effective_env_overrides.get(key)
                pid_value = pid_env.get(key)
                if manifest_value is None:
                    continue
                if pid_value is None:
                    pid_missing.append(
                        {
                            "family": family,
                            "env_key": key,
                            "severity": "runtime_env_pid_missing",
                            "manifest_value": manifest_value,
                        }
                    )
                elif manifest_value != pid_value:
                    pid_mismatches.append(
                        {
                            "family": family,
                            "env_key": key,
                            "manifest_value": manifest_value,
                            "pid_value": pid_value,
                            "expected_value_source": (
                                "operator_runtime_overrides"
                                if key in operator_overrides
                                else "threshold_runtime_env_manifest"
                            ),
                        }
                    )
    passed = len(findings) == 0
    pid_passed = len(pid_mismatches) == 0 and len(pid_missing) == 0
    result: dict[str, Any] = {
        "target_date": target_date,
        "manifest_path": str(manifest_path) if manifest_path.exists() else None,
        "selected_families": selected_families,
        "passed": passed,
        "findings": findings,
        "missing_family_count": len(missing_families),
        "pid": pid,
        "pid_env_available": bool(pid_env),
        "pid_passed": pid_passed,
        "pid_mismatches": pid_mismatches,
        "pid_missing": pid_missing,
        "operator_runtime_override_path": (
            str(operator_override_path) if operator_override_path.exists() else None
        ),
        "operator_runtime_override_keys": sorted(operator_overrides),
    }
    if not passed:
        result["status"] = "fail"
        result["fail_reason"] = "runtime_env_handoff_missing"
    elif not pid_passed:
        result["status"] = "fail"
        result["fail_reason"] = "runtime_env_pid_missing"
    else:
        result["status"] = "pass"
    return result


RUNTIME_GAP_WINDOWS_2026_06_11: dict[str, dict[str, Any]] = {
    "score65_74_recovery_probe": {
        "family": "score65_74_recovery_probe",
        "gap_type": "real_probe_attribution_missing",
        "gap_start_kst": "2026-06-11T07:40:00+09:00",
        "gap_end_kst": "2026-06-11T10:51:07+09:00",
        "raw_preserved": True,
        "metric_scope": "real_probe_attribution_only",
        "excluded_metrics": ["real_entry_unlock_event", "real_probe_submit_count"],
        "not_excluded": ["sim_candidate_source_quality", "raw_pipeline_events", "threshold_events"],
        "interpretation_rule": "Do not interpret as probe failure or unlock rate degradation.",
        "runtime_gap_reason": "score65_74_recovery_probe env not in PREOPEN apply until operator override at 10:51:07",
    },
    "lifecycle_bucket_discovery_sim_auto_approval": {
        "family": "lifecycle_bucket_discovery_sim_auto_approval",
        "gap_type": "sim_policy_handoff_missing",
        "gap_start_kst": "2026-06-11T07:40:00+09:00",
        "gap_end_kst": "2026-06-11T10:59:40+09:00",
        "raw_preserved": True,
        "metric_scope": "lifecycle_catalog_match_ldm_bucket_attribution_only",
        "excluded_metrics": ["parent_catalog_match_success", "ldm_bucket_match_count"],
        "not_excluded": ["raw_pipeline_events", "threshold_events", "source_quality_audit"],
        "interpretation_rule": "Do not interpret parent_catalog_missing as bucket success or failure.",
        "runtime_gap_reason": "lifecycle_bucket_discovery_sim_auto_approval policy env overwritten by scalp_sim_auto_approval; restored at 10:59:40",
    },
}


def _parse_gap_end_kst(gap: dict[str, Any]) -> datetime | None:
    end_text = str(gap.get("gap_end_kst") or "")
    return _parse_dt(end_text) if end_text else None


def _parse_gap_start_kst(gap: dict[str, Any]) -> datetime | None:
    start_text = str(gap.get("gap_start_kst") or "")
    return _parse_dt(start_text) if start_text else None


def _gap_windows_for_target(target_date: str, gap_windows: dict[str, dict[str, Any]] | None = None) -> dict[str, dict[str, Any]]:
    window_map = gap_windows or RUNTIME_GAP_WINDOWS_2026_06_11
    target = str(target_date).strip()
    if target != "2026-06-11":
        return {}
    return window_map


def classify_postclose_interpretation_scope(
    event_time_kst: str | datetime | None,
    *,
    gap_windows: dict[str, dict[str, Any]] | None = None,
    target_date: str = "",
) -> dict[str, Any]:
    gap_windows = _gap_windows_for_target(target_date, gap_windows)
    event_dt = _parse_dt(event_time_kst) if isinstance(event_time_kst, str) else event_time_kst
    if event_dt is None:
        return {"target_date": target_date, "scope": "unknown_event_time", "active_gaps": []}
    active_gaps_at_time: list[dict[str, Any]] = []
    for gap_detail in gap_windows.values():
        if not isinstance(gap_detail, dict):
            continue
        gap_start = _parse_gap_start_kst(gap_detail)
        gap_end = _parse_gap_end_kst(gap_detail)
        if gap_start is None or gap_end is None:
            continue
        if gap_start <= event_dt < gap_end:
            active_gaps_at_time.append(
                {
                    "family": str(gap_detail.get("family") or ""),
                    "gap_type": str(gap_detail.get("gap_type") or ""),
                    "metric_scope": str(gap_detail.get("metric_scope") or ""),
                    "excluded_metrics": gap_detail.get("excluded_metrics") or [],
                    "interpretation_rule": str(gap_detail.get("interpretation_rule") or ""),
                }
            )
    scope = "gap_affected" if active_gaps_at_time else "normal_runtime"
    return {
        "target_date": target_date,
        "event_time_kst": event_dt.isoformat(timespec="seconds"),
        "scope": scope,
        "active_gaps": active_gaps_at_time,
        "interpretation_rules": [gap["interpretation_rule"] for gap in active_gaps_at_time],
    }


def build_runtime_gap_provenance_artifact(
    target_date: str,
    *,
    gap_windows: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    gap_windows = _gap_windows_for_target(target_date, gap_windows)
    active_gaps = [
        {
            **detail,
            "gap_active": True,
        }
        for detail in gap_windows.values()
        if isinstance(detail, dict) and bool(detail.get("metric_scope"))
    ]
    post_restore_keys = sorted(
        {
            str(gap.get("gap_end_kst", "")).split("T")[-1]
            for gap in active_gaps
            if isinstance(gap, dict) and gap.get("gap_end_kst")
        }
    )
    return {
        "target_date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "raw_preserved": True,
        "active_gap_count": len(active_gaps),
        "gaps": active_gaps,
        "postclose_interpretation_scope": {
            f"~{gap.get('gap_end_kst','').split('T')[1] if 'T' in str(gap.get('gap_end_kst','')) else gap.get('gap_end_kst','')}": str(
                gap.get("interpretation_rule", "")
            )
            for gap in active_gaps
        },
        "post_restore_normal_window": {
            f"{key} 이후": "normal runtime reflection window; performance evaluation allowed"
            for key in post_restore_keys
        },
    }


def _write_gap_provenance(target_date: str) -> None:
    artifact = build_runtime_gap_provenance_artifact(target_date)
    if not artifact.get("active_gap_count"):
        return
    RUNTIME_GAP_PROVENANCE_DIR.mkdir(parents=True, exist_ok=True)
    out_path = runtime_gap_provenance_artifact_path(target_date)
    out_path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_runtime_env(target_date: str, manifest: dict[str, Any], env_overrides: dict[str, str]) -> None:
    RUNTIME_ENV_DIR.mkdir(parents=True, exist_ok=True)
    env_overrides = {
        key: value
        for key, value in env_overrides.items()
        if str(key) not in REMOVED_RUNTIME_ENV_KEYS
    }
    lines = [
        "# Generated by threshold_cycle_preopen_apply.py",
        f"# target_date={target_date}",
        f"# source_date={manifest.get('source_date')}",
        f"# generated_at={manifest.get('generated_at')}",
        "export KORSTOCKSCAN_THRESHOLD_RUNTIME_AUTO_APPLY_ENABLED=true",
        f"export KORSTOCKSCAN_THRESHOLD_RUNTIME_APPLY_DATE={shlex.quote(target_date)}",
    ]
    for key in sorted(env_overrides):
        lines.append(f"export {key}={shlex.quote(str(env_overrides[key]))}")
    runtime_env_path(target_date).write_text("\n".join(lines) + "\n", encoding="utf-8")
    runtime_env_manifest_path(target_date).write_text(
        json.dumps(
            {
                "schema_version": 1,
                "report_type": "threshold_runtime_env",
                "target_date": target_date,
                "source_date": manifest.get("source_date"),
                "source_report": manifest.get("source_report"),
                "generated_at": manifest.get("generated_at"),
                "env_file": str(runtime_env_path(target_date)),
                "env_overrides": env_overrides,
                "selected_families": [
                    item.get("family")
                    for item in [
                        *(manifest.get("auto_apply_selected") or []),
                        *((manifest.get("swing_runtime_approval") or {}).get("selected") or []),
                        *((manifest.get("scalp_sim_auto_approval") or {}).get("selected") or []),
                        *((manifest.get("scalp_sim_scale_in_window_approval") or {}).get("selected") or []),
                        *((manifest.get("runtime_apply_bridge") or {}).get("selected") or []),
                        *((manifest.get("lifecycle_bucket_discovery") or {}).get("selected") or []),
                        *((manifest.get("swing_sim_auto_approval") or {}).get("selected") or []),
                        *(
                            [manifest.get("entry_cancel_wait_runtime")]
                            if (manifest.get("entry_cancel_wait_runtime") or {}).get("selected")
                            else []
                        ),
                    ]
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def _entry_cancel_wait_standalone_decision(
    source_date: str, target_date: str, operator_locks: list[dict[str, Any]]
) -> tuple[dict[str, Any], dict[str, str]]:
    if target_date < ENTRY_CANCEL_WAIT_ACTIVATION_DATE:
        return ({
            "family": ENTRY_CANCEL_WAIT_FAMILY,
            "selected": False,
            "decision_reason": "before_activation_date",
            "activation_date": ENTRY_CANCEL_WAIT_ACTIVATION_DATE,
            "runtime_effect": False,
            "env_overrides": {},
        }, {})
    defaults = {"standard": 60, "breakout": 120, "pullback": 600, "reserve": 1200}
    report_path = ENTRY_CANCEL_WAIT_TUNING_DIR / f"entry_cancel_wait_tuning_{source_date}.json"
    report = _load_json(report_path) if report_path.exists() else {}
    values = report.get("recommended_thresholds") if isinstance(report.get("recommended_thresholds"), dict) else {}
    _previous_families, previous_manifest = _load_previous_runtime_env_selected_families(target_date)
    previous_env = previous_manifest.get("env_overrides") if isinstance(previous_manifest.get("env_overrides"), dict) else {}
    env_keys = {
        "standard": "KORSTOCKSCAN_SCALPING_ENTRY_TIMEOUT_SEC",
        "breakout": "KORSTOCKSCAN_SCALPING_BREAKOUT_ENTRY_TIMEOUT_SEC",
        "pullback": "KORSTOCKSCAN_SCALPING_PULLBACK_ENTRY_TIMEOUT_SEC",
        "reserve": "KORSTOCKSCAN_SCALPING_RESERVE_ENTRY_TIMEOUT_SEC",
    }
    selected_values: dict[str, int] = {}
    for profile, default in defaults.items():
        value = int(values.get(profile, 0) or 0)
        if value <= 0:
            value = int(previous_env.get(env_keys[profile], 0) or 0)
        selected_values[profile] = value if value > 0 else default

    explicit_off = False
    off_lock_id = ""
    for lock in operator_locks or []:
        if str(lock.get("family") or "") != ENTRY_CANCEL_WAIT_FAMILY:
            continue
        lock_env = _lock_env_overrides(lock)
        enabled = str(lock_env.get("KORSTOCKSCAN_ENTRY_CANCEL_WAIT_ATTRIBUTION_ENABLED", "true")).lower()
        if enabled in {"false", "0", "off"}:
            explicit_off = True
            off_lock_id = str(lock.get("lock_id") or "operator_lock")
            break
    env_overrides = {
        "KORSTOCKSCAN_ENTRY_CANCEL_WAIT_ATTRIBUTION_ENABLED": "false" if explicit_off else "true",
        "KORSTOCKSCAN_ENTRY_CANCEL_WAIT_ATTRIBUTION_REAL_MIN_SEC": "60",
        "KORSTOCKSCAN_ENTRY_CANCEL_WAIT_ATTRIBUTION_STALE_MAX_SEC": "30",
        **{env_keys[profile]: str(value) for profile, value in selected_values.items()},
    }
    decision = {
        "family": ENTRY_CANCEL_WAIT_FAMILY,
        "stage": "entry_cancel_wait_operational",
        "family_type": "standalone_operational_runtime",
        "selected": not explicit_off,
        "decision_reason": (
            f"explicit_operator_off:{off_lock_id}" if explicit_off else "persistent_on_daily_deterministic_ev"
        ),
        "runtime_effect": not explicit_off,
        "allowed_runtime_apply": True,
        "automatic_off_allowed": False,
        "source_artifact": str(report_path) if report_path.exists() else None,
        "source_quality_status": str(report.get("source_quality_status") or "missing_hold_defaults"),
        "selected_thresholds": selected_values,
        "env_overrides": env_overrides,
        "excluded_consumers": ["ADM", "LDM", "lifecycle_bucket", "threshold_cycle_ev", "runtime_apply_bridge"],
    }
    return decision, env_overrides


def build_preopen_apply_manifest(
    target_date: str,
    *,
    source_date: str | None = None,
    apply_mode: str = "manifest_only",
    auto_apply: bool = False,
    require_ai: bool = True,
    source_phase: str | None = None,
    include_families: set[str] | None = None,
) -> dict[str, Any]:
    target_date = str(target_date).strip()
    source_path = _report_path_for_date(source_date, source_phase=source_phase) if source_date else _latest_report_before(target_date)
    if source_path is None or not source_path.exists():
        auto_apply_requested = bool(auto_apply) or apply_mode in AUTO_APPLY_MODES
        operator_runtime_env_locks = _load_operator_runtime_env_locks(source_date, target_date)
        selected, decisions, env_overrides = ([], [], {})
        if auto_apply_requested and operator_runtime_env_locks:
            selected, decisions, env_overrides = _select_auto_apply_candidates(
                [],
                ai_review={},
                require_ai=False,
                target_date=target_date,
                include_families=include_families,
                operator_locks=operator_runtime_env_locks,
            )
        runtime_change = bool(auto_apply_requested and env_overrides)
        manifest = {
            "target_date": target_date,
            "status": (
                "operator_runtime_env_lock_ready_missing_source_report"
                if runtime_change
                else "missing_source_report"
            ),
            "apply_mode": apply_mode,
            "runtime_change": runtime_change,
            "runtime_change_reason": (
                "source report missing; explicit operator runtime env locks preserved"
                if runtime_change
                else "source report missing"
            ),
            "source_report": None,
            "candidates": [],
            "calibration_candidates": [],
            "auto_apply_selected": selected,
            "auto_apply_decisions": decisions,
            "operator_runtime_env_locks": operator_runtime_env_locks,
            "runtime_env_file": str(runtime_env_path(target_date)) if auto_apply_requested else None,
            "runtime_env_overrides": env_overrides,
            "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        }
        if runtime_change:
            _write_runtime_env(target_date, manifest, env_overrides)
            _write_gap_provenance(target_date)
            runtime_env_verification = verify_runtime_env_handoff(target_date)
            manifest["runtime_env_handoff_verification"] = runtime_env_verification
            RUNTIME_ENV_DIR.mkdir(parents=True, exist_ok=True)
            runtime_env_verify_path(target_date).write_text(
                json.dumps(runtime_env_verification, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
    else:
        report = _load_json(source_path)
        candidates = report.get("apply_candidate_list") if isinstance(report.get("apply_candidate_list"), list) else []
        calibration_candidates = (
            report.get("calibration_candidates") if isinstance(report.get("calibration_candidates"), list) else []
        )
        candidates = [
            item
            for item in candidates
            if not (isinstance(item, dict) and str(item.get("family") or "") in REMOVED_CALIBRATION_FAMILIES)
        ]
        calibration_candidates = [
            item
            for item in calibration_candidates
            if not (isinstance(item, dict) and str(item.get("family") or "") in REMOVED_CALIBRATION_FAMILIES)
        ]
        report_source_date = str(report.get("date") or source_date or "")
        latency_candidates, latency_recommendation = _load_latency_classifier_candidates(report_source_date)
        if latency_candidates:
            calibration_candidates = [*calibration_candidates, *latency_candidates]
        rising_missed_first_touch_candidates, rising_missed_first_touch_calibration = (
            _load_rising_missed_first_touch_calibration_candidates(report_source_date)
        )
        if rising_missed_first_touch_candidates:
            calibration_candidates = [
                *calibration_candidates,
                *rising_missed_first_touch_candidates,
            ]
        scalping_pyramid_quality_candidates, scalping_pyramid_quality_calibration = (
            _load_scalping_pyramid_quality_calibration_candidates(report_source_date)
        )
        if scalping_pyramid_quality_candidates:
            calibration_candidates = [
                *calibration_candidates,
                *scalping_pyramid_quality_candidates,
            ]
        ai_score_optimization_candidates, ai_score_optimization_backtest = (
            _load_ai_score_optimization_backtest_candidates(report_source_date)
        )
        if ai_score_optimization_candidates:
            calibration_candidates = [
                *calibration_candidates,
                *ai_score_optimization_candidates,
            ]
        calibration_candidates = _dedupe_calibration_candidates(calibration_candidates)
        calibration_candidates = _scrub_removed_contracts(calibration_candidates) or []
        candidates = _scrub_removed_contracts(candidates) or []
        approval_requests = []
        for item in calibration_candidates:
            if (
                isinstance(item, dict)
                and bool(item.get("human_approval_required"))
                and str(item.get("calibration_state") or "") == "approval_required"
            ):
                approval_requests.append(
                    annotate_approval_request(
                        {
                            "family": item.get("family"),
                            "stage": item.get("stage"),
                            "threshold_version": item.get("threshold_version"),
                            "calibration_state": item.get("calibration_state"),
                            "calibration_reason": item.get("calibration_reason"),
                            "current_values": item.get("current_values"),
                            "recommended_values": item.get("recommended_values"),
                            "sample_count": item.get("sample_count"),
                            "sample_floor": item.get("sample_floor"),
                            "source_reports": item.get("source_reports"),
                        },
                        str(report.get("date") or source_date or ""),
                    )
                )
        approval_contract_gaps = [
            item
            for item in approval_requests
            if isinstance(item, dict) and not bool(item.get("approval_live_ready"))
        ]
        auto_apply_requested = bool(auto_apply) or apply_mode in AUTO_APPLY_MODES
        ai_review = _load_ai_review(report_source_date, source_phase=source_phase)
        intraday_source_auto_apply_blocked = bool(auto_apply_requested and source_phase == "intraday")
        operator_runtime_env_locks = _load_operator_runtime_env_locks(
            report_source_date,
            target_date,
        )
        entry_cancel_wait_decision, entry_cancel_wait_env_overrides = (
            _entry_cancel_wait_standalone_decision(
                report_source_date, target_date, operator_runtime_env_locks
            )
        )
        selected, decisions, env_overrides = ([], [], {})
        lifecycle_context_overlay, lifecycle_context_env_overrides = ({}, {})
        swing_bundle = _load_swing_runtime_approval_bundle(report_source_date)
        swing_selected, swing_decisions, swing_env_overrides = ([], [], {})
        scalp_sim_auto_bundle = _load_scalp_sim_auto_approval(report_source_date)
        scalp_sim_auto_selected, scalp_sim_auto_decisions, scalp_sim_auto_env_overrides = ([], [], {})
        scalp_scale_bundle = _load_scalp_sim_scale_in_window_approval(report_source_date)
        scalp_scale_selected, scalp_scale_decisions, scalp_scale_env_overrides = ([], [], {})
        runtime_bridge_bundle = _load_runtime_apply_bridge_approval(report_source_date)
        runtime_bridge_selected, runtime_bridge_decisions, runtime_bridge_env_overrides = ([], [], {})
        lifecycle_bucket_bundle = _load_lifecycle_bucket_sim_auto_approval(report_source_date)
        lifecycle_bucket_selected, lifecycle_bucket_decisions, lifecycle_bucket_env_overrides = ([], [], {})
        swing_sim_auto_bundle = _load_swing_sim_auto_approval(report_source_date)
        swing_sim_auto_selected, swing_sim_auto_decisions, swing_sim_auto_env_overrides = ([], [], {})
        if auto_apply_requested and not intraday_source_auto_apply_blocked:
            selected, decisions, env_overrides = _select_auto_apply_candidates(
                calibration_candidates,
                ai_review=ai_review,
                require_ai=require_ai,
                target_date=target_date,
                include_families=include_families,
                operator_locks=operator_runtime_env_locks,
            )
            swing_selected, swing_decisions, swing_env_overrides = _select_swing_approved_candidates(swing_bundle)
            scalp_sim_auto_selected, scalp_sim_auto_decisions, scalp_sim_auto_env_overrides = (
                _select_scalp_sim_auto_approval(scalp_sim_auto_bundle)
            )
            if scalp_sim_auto_selected:
                scalp_scale_decisions = [
                    {
                        "family": "scalp_sim_scale_in_window_expansion",
                        "selected": False,
                        "decision_reason": "covered_by_scalp_sim_auto_approval_control_tower",
                        "env_overrides": {},
                        "actual_order_submitted": False,
                    }
                ]
            else:
                scalp_scale_selected, scalp_scale_decisions, scalp_scale_env_overrides = (
                    _select_scalp_sim_scale_in_window_approval(scalp_scale_bundle)
                )
            runtime_bridge_selected, runtime_bridge_decisions, runtime_bridge_env_overrides = (
                _select_runtime_apply_bridge_approval(
                    runtime_bridge_bundle,
                    include_families=include_families,
                )
            )
            lifecycle_bucket_selected, lifecycle_bucket_decisions, lifecycle_bucket_env_overrides = (
                _select_lifecycle_bucket_sim_auto_approval(lifecycle_bucket_bundle)
            )
            swing_sim_auto_selected, swing_sim_auto_decisions, swing_sim_auto_env_overrides = (
                _select_swing_sim_auto_approval(swing_sim_auto_bundle)
            )
            lifecycle_context_overlay, lifecycle_context_env_overrides = _lifecycle_ai_context_overlay_env(
                calibration_candidates,
                include_families=include_families,
            )
            entry_price_live_owner_family = _entry_price_live_owner_family(
                selected,
                runtime_bridge_selected,
            )
            entry_live_tuning_owner_family = _entry_live_tuning_owner_family(
                selected,
                runtime_bridge_selected,
            )
            holding_exit_live_owner_family = _holding_exit_live_owner_family(
                selected,
                runtime_bridge_selected,
            )
            scale_in_live_owner_family = _scale_in_live_owner_family(
                selected,
                runtime_bridge_selected,
            )
            preset_tp_exit_live_owner_family = _preset_tp_exit_live_owner_family(
                selected,
                runtime_bridge_selected,
            )
            selected, decisions, env_overrides = _close_aggressive_entry_price_override_for_live_owner(
                selected=selected,
                decisions=decisions,
                env_overrides=env_overrides,
                owner_family=entry_price_live_owner_family,
            )
            selected, decisions, env_overrides = _close_scalping_scanner_real_source_guard_for_live_owner(
                selected=selected,
                decisions=decisions,
                env_overrides=env_overrides,
                owner_family=entry_live_tuning_owner_family,
            )
            selected, decisions, env_overrides = _close_score65_74_strong_micro_override_for_live_owner(
                selected=selected,
                decisions=decisions,
                env_overrides=env_overrides,
                owner_family=entry_live_tuning_owner_family,
            )
            selected, decisions, env_overrides = _close_early_accel_recheck_for_live_owner(
                selected=selected,
                decisions=decisions,
                env_overrides=env_overrides,
                owner_family=entry_live_tuning_owner_family,
            )
            selected, decisions, env_overrides = _close_pre_submit_liquidity_relief_for_live_owner(
                selected=selected,
                decisions=decisions,
                env_overrides=env_overrides,
                owner_family=entry_live_tuning_owner_family,
            )
            selected, decisions, env_overrides = _close_weak_context_late_entry_guard_for_live_owner(
                selected=selected,
                decisions=decisions,
                env_overrides=env_overrides,
                owner_family=entry_live_tuning_owner_family,
            )
            selected, decisions, env_overrides = _close_ai_numeric_consistency_recheck_for_live_owner(
                selected=selected,
                decisions=decisions,
                env_overrides=env_overrides,
                owner_family=entry_live_tuning_owner_family,
            )
            selected, decisions, env_overrides = _close_real_pyramid_scale_in_quality_guard_for_live_owner(
                selected=selected,
                decisions=decisions,
                env_overrides=env_overrides,
                owner_family=scale_in_live_owner_family,
            )
            selected, decisions, env_overrides = _close_never_green_defer_clamp_for_live_owner(
                selected=selected,
                decisions=decisions,
                env_overrides=env_overrides,
                owner_family=holding_exit_live_owner_family,
            )
            selected, decisions, env_overrides = _close_soft_stop_dynamic_grace_for_live_owner(
                selected=selected,
                decisions=decisions,
                env_overrides=env_overrides,
                owner_family=holding_exit_live_owner_family,
            )
            selected, decisions, env_overrides = _close_preset_tp_soft_stop_for_live_owner(
                selected=selected,
                decisions=decisions,
                env_overrides=env_overrides,
                owner_family=preset_tp_exit_live_owner_family,
            )
            env_overrides = {
                **env_overrides,
                **entry_cancel_wait_env_overrides,
                **lifecycle_context_env_overrides,
                **swing_env_overrides,
                **scalp_sim_auto_env_overrides,
                **scalp_scale_env_overrides,
                **runtime_bridge_env_overrides,
                **lifecycle_bucket_env_overrides,
                **swing_sim_auto_env_overrides,
            }
            env_overrides = {
                key: value
                for key, value in env_overrides.items()
                if str(key) not in REMOVED_RUNTIME_ENV_KEYS
            }
            if any(str(item.get("family") or "") == "dynamic_entry_price_resolver" for item in selected):
                env_overrides["KORSTOCKSCAN_DYNAMIC_ENTRY_PRICE_RESOLVER_LIVE_SELECTED"] = "true"
            if entry_price_live_owner_family:
                env_overrides[ENTRY_PRICE_LIVE_TUNING_MARKER_ENV] = "true"
            if entry_live_tuning_owner_family:
                env_overrides[ENTRY_STAGE_LIVE_TUNING_MARKER_ENV] = "true"
            if scale_in_live_owner_family:
                env_overrides[SCALE_IN_LIVE_TUNING_MARKER_ENV] = "true"
            if holding_exit_live_owner_family:
                env_overrides[HOLDING_EXIT_LIVE_TUNING_MARKER_ENV] = "true"
            if preset_tp_exit_live_owner_family:
                env_overrides[PRESET_TP_EXIT_LIVE_TUNING_MARKER_ENV] = "true"
        runtime_change = bool(auto_apply_requested and env_overrides)
        status = (
            "auto_bounded_live_ready"
            if runtime_change
            else "auto_bounded_live_blocked"
            if auto_apply_requested
            else "efficient_tradeoff_manifest_ready"
            if apply_mode == "efficient_tradeoff_canary_candidate"
            else "calibrated_manifest_ready"
            if apply_mode == "calibrated_apply_candidate"
            else "manifest_ready"
        )
        manifest = {
            "target_date": target_date,
            "source_date": report.get("date"),
            "source_report": str(source_path),
            "status": status,
            "apply_mode": apply_mode,
            "runtime_change": runtime_change,
            "runtime_change_reason": (
                "intraday source phase는 manual forensic/legacy manifest-only이며 runtime env apply 금지"
                if intraday_source_auto_apply_blocked
                else
                "장전 자동 bounded env apply; 장중 threshold mutation은 계속 금지"
                if runtime_change
                else "장전 자동 bounded env apply 후보 없음; 장중 threshold mutation은 계속 금지"
                if auto_apply_requested
                else "장중 자동 mutation 금지; calibrated/efficient trade-off 후보도 승인된 family의 다음 장전 bounded apply 후보만 생성"
            ),
            "candidates": candidates,
            "calibration_candidates": calibration_candidates,
            "source_phase": source_phase or "canonical",
            "source_phase_auto_apply_blocked": intraday_source_auto_apply_blocked,
            "ai_correction_review": {
                "required": bool(require_ai),
                "status": ai_review.get("status"),
                "path": ai_review.get("path"),
                "phase": ai_review.get("phase"),
                "model": ai_review.get("model"),
                "provider_status": ai_review.get("provider_status") or {},
            },
            "latency_classifier_recommendation": latency_recommendation,
            "rising_missed_first_touch_calibration": rising_missed_first_touch_calibration,
            "scalping_pyramid_quality_calibration": scalping_pyramid_quality_calibration,
            "ai_score_optimization_backtest": ai_score_optimization_backtest,
            "auto_apply_selected": selected,
            "auto_apply_decisions": decisions,
            "entry_cancel_wait_runtime": entry_cancel_wait_decision,
            "lifecycle_ai_context_overlay": lifecycle_context_overlay,
            "operator_runtime_env_locks": operator_runtime_env_locks,
            "approval_requests": approval_requests,
            "approval_contract_gaps": approval_contract_gaps,
            "swing_runtime_approval": {
                "request_report": swing_bundle.get("request_report"),
                "approval_artifact": swing_bundle.get("approval_artifact"),
                "legacy_phase0_real_canary_ignored": bool(
                    swing_bundle.get("legacy_phase0_real_canary_ignored")
                ),
                "requested": len(swing_bundle.get("requests") or []),
                "approved": len(swing_bundle.get("approved_requests") or []),
                "blocked": swing_bundle.get("blocked") or [],
                "requests": swing_bundle.get("requests") or [],
                "approved_requests": swing_bundle.get("approved_requests") or [],
                "selected": swing_selected,
                "decisions": swing_decisions,
                "dry_run_forced": bool(swing_env_overrides),
            },
            "scalp_sim_auto_approval": {
                "artifact": scalp_sim_auto_bundle.get("artifact"),
                "catalog": scalp_sim_auto_bundle.get("catalog"),
                "approved": 1 if scalp_sim_auto_bundle.get("approved_request") else 0,
                "approved_policy_count": scalp_sim_auto_bundle.get("approved_policy_count"),
                "approved_source_ids": scalp_sim_auto_bundle.get("approved_source_ids") or [],
                "blocked": scalp_sim_auto_bundle.get("blocked") or [],
                "approved_request": scalp_sim_auto_bundle.get("approved_request"),
                "selected": scalp_sim_auto_selected,
                "decisions": scalp_sim_auto_decisions,
            },
            "scalp_sim_scale_in_window_approval": {
                "artifact": scalp_scale_bundle.get("artifact"),
                "approved": 1 if scalp_scale_bundle.get("approved_request") else 0,
                "blocked": scalp_scale_bundle.get("blocked") or [],
                "approved_request": scalp_scale_bundle.get("approved_request"),
                "selected": scalp_scale_selected,
                "decisions": scalp_scale_decisions,
            },
            "runtime_apply_bridge": {
                "request_report": runtime_bridge_bundle.get("request_report"),
                "artifacts": runtime_bridge_bundle.get("artifacts") or {},
                "candidate_count": len(runtime_bridge_bundle.get("candidates") or []),
                "approved": len(runtime_bridge_bundle.get("approved_requests") or []),
                "blocked": runtime_bridge_bundle.get("blocked") or [],
                "metadata": runtime_bridge_bundle.get("metadata") or [],
                "approved_requests": runtime_bridge_bundle.get("approved_requests") or [],
                "selected": runtime_bridge_selected,
                "decisions": runtime_bridge_decisions,
            },
            "lifecycle_bucket_discovery": {
                "artifact": lifecycle_bucket_bundle.get("artifact"),
                "discovery_report": lifecycle_bucket_bundle.get("discovery_report"),
                "catalog": lifecycle_bucket_bundle.get("catalog"),
                "approved": 1 if lifecycle_bucket_bundle.get("approved_request") else 0,
                "blocked": lifecycle_bucket_bundle.get("blocked") or [],
                "approved_request": lifecycle_bucket_bundle.get("approved_request"),
                "selected": lifecycle_bucket_selected,
                "decisions": lifecycle_bucket_decisions,
            },
            "swing_sim_auto_approval": {
                "artifact": swing_sim_auto_bundle.get("artifact"),
                "catalog": swing_sim_auto_bundle.get("catalog"),
                "approved": 1 if swing_sim_auto_bundle.get("approved_request") else 0,
                "approved_policy_count": swing_sim_auto_bundle.get("approved_policy_count"),
                "approved_source_ids": swing_sim_auto_bundle.get("approved_source_ids") or [],
                "blocked": swing_sim_auto_bundle.get("blocked") or [],
                "approved_request": swing_sim_auto_bundle.get("approved_request"),
                "selected": swing_sim_auto_selected,
                "decisions": swing_sim_auto_decisions,
            },
            "runtime_env_file": (
                str(runtime_env_path(target_date))
                if auto_apply_requested and not intraday_source_auto_apply_blocked
                else None
            ),
            "runtime_env_overrides": env_overrides,
            "threshold_snapshot": _scrub_removed_contracts(report.get("threshold_snapshot") or {}) or {},
            "post_apply_attribution": _scrub_removed_contracts(report.get("post_apply_attribution") or {}) or {},
            "safety_guard_pack": _scrub_removed_contracts(report.get("safety_guard_pack") or []) or [],
            "calibration_trigger_pack": _scrub_removed_contracts(report.get("calibration_trigger_pack") or []) or [],
            "rollback_guard_pack": _scrub_removed_contracts(report.get("rollback_guard_pack") or []) or [],
            "calibration_policy": {
                "condition_miss_action": "calibration_trigger",
                "sample_shortfall_action": "cap_reduce_or_hold_sample_or_max_step_shrink",
                "rollback_policy": "safety_breach_only",
                "intraday_runtime_mutation": False,
                "apply_frequency": "next_preopen_once",
                "human_approval_required": bool(approval_requests),
                "ai_correction_required": bool(require_ai),
                "same_stage_owner_rule": "one_selected_family_per_stage_by_priority",
                "daily_ev_report_only": True,
                "operator_family_filter": sorted(include_families) if include_families is not None else None,
                "intraday_source_auto_apply": False,
            },
            "warnings": ["intraday_source_phase_auto_apply_blocked"] if intraday_source_auto_apply_blocked else [],
            "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        }
        if auto_apply_requested and not intraday_source_auto_apply_blocked:
            _write_runtime_env(target_date, manifest, env_overrides)
            _write_gap_provenance(target_date)
        runtime_env_verification = verify_runtime_env_handoff(target_date)
        manifest["runtime_env_handoff_verification"] = runtime_env_verification
        if auto_apply_requested and not intraday_source_auto_apply_blocked:
            RUNTIME_ENV_DIR.mkdir(parents=True, exist_ok=True)
            runtime_env_verify_path(target_date).write_text(
                json.dumps(runtime_env_verification, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
    APPLY_PLAN_DIR.mkdir(parents=True, exist_ok=True)
    apply_manifest_path(target_date).write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build preopen threshold apply manifest.")
    parser.add_argument(
        "--date",
        "--target-date",
        dest="target_date",
        default=date.today().isoformat(),
        help="Target preopen date",
    )
    parser.add_argument("--source-date", dest="source_date", default=None, help="Postclose report date to apply")
    parser.add_argument(
        "--source-phase",
        choices=["canonical", "intraday", "postclose"],
        default="canonical",
        help="When --source-date is given, choose canonical threshold report or a phase calibration artifact.",
    )
    parser.add_argument(
        "--include-family",
        action="append",
        default=[],
        help="Limit auto-apply selection to the given family. May be repeated for stage-disjoint explicit applies.",
    )
    parser.add_argument(
        "--apply-mode",
        default=os.getenv("THRESHOLD_CYCLE_APPLY_MODE", "manifest_only"),
        choices=[
            "manifest_only",
            "calibrated_apply_candidate",
            "efficient_tradeoff_canary_candidate",
            "auto_bounded_live",
        ],
        help="Apply mode. auto_bounded_live writes next-preopen runtime env under deterministic/AI guards.",
    )
    parser.add_argument(
        "--auto-apply",
        action="store_true",
        default=str(os.getenv("THRESHOLD_CYCLE_AUTO_APPLY", "")).lower() in {"1", "true", "yes", "on"},
        help="Write guarded runtime env overrides for selected candidates.",
    )
    parser.add_argument(
        "--allow-deterministic-without-ai",
        action="store_true",
        default=str(os.getenv("THRESHOLD_CYCLE_AUTO_APPLY_REQUIRE_AI", "true")).lower() in {"0", "false", "no", "off"},
        help="Allow deterministic guards to apply when AI correction review is missing/unavailable.",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        default=False,
        help="Run runtime env handoff verification instead of building manifest.",
    )
    parser.add_argument(
        "--pid",
        type=int,
        default=None,
        help="Bot process PID to verify /proc/<pid>/environ against runtime env manifest.",
    )
    parser.add_argument(
        "--write-verify-artifact",
        action="store_true",
        default=False,
        dest="write_verify_artifact",
        help="Write the verification result to threshold_runtime_env_verify_{date}.json.",
    )
    args = parser.parse_args(argv)
    if args.verify:
        result = verify_runtime_env_handoff(args.target_date, pid=args.pid)
        print(json.dumps(result, ensure_ascii=False))
        if args.write_verify_artifact:
            RUNTIME_ENV_DIR.mkdir(parents=True, exist_ok=True)
            runtime_env_verify_path(args.target_date).write_text(
                json.dumps(result, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        return 0 if result.get("status") == "pass" else 1
    manifest = build_preopen_apply_manifest(
        args.target_date,
        source_date=args.source_date,
        apply_mode=args.apply_mode,
        auto_apply=args.auto_apply,
        require_ai=not args.allow_deterministic_without_ai,
        source_phase=None if args.source_phase == "canonical" else args.source_phase,
        include_families=set(args.include_family) if args.include_family else None,
    )
    print(json.dumps(manifest, ensure_ascii=False))
    return (
        0
        if manifest.get("status")
        in {
            "manifest_ready",
            "calibrated_manifest_ready",
            "efficient_tradeoff_manifest_ready",
            "auto_bounded_live_ready",
            "auto_bounded_live_blocked",
            "operator_runtime_env_lock_ready_missing_source_report",
        }
        else 2
    )


if __name__ == "__main__":
    raise SystemExit(main())
