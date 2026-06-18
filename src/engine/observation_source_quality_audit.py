from __future__ import annotations

import argparse
import gzip
import json
import shutil
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from src.engine.ai_response_contracts import (
    is_known_flow_state_label,
    is_known_gatekeeper_action_label,
    normalize_flow_state_label,
    normalize_gatekeeper_action_key,
)
from src.engine.monitoring.market_halt_windows import load_market_halt_windows
from src.utils.constants import DATA_DIR
from src.utils.jsonl_io import existing_or_gzip_path, iter_jsonl


REPORT_DIRNAME = "observation_source_quality_audit"
BACKFILL_REPORT_STEM = "observation_source_quality_backfill_audit"


SOURCE_LIKE_TOKENS = (
    "source",
    "metric_role",
    "decision_authority",
    "forbidden_uses",
    "fresh",
    "stale",
    "missing",
    "provenance",
    "authority",
    "forbidden",
    "quality",
    "transport",
    "openai",
    "ws_age",
    "quote",
    "strength",
    "pressure",
    "range",
    "day_high",
    "micro",
    "orderbook",
    "budget_authority",
    "runtime_effect",
    "broker_order",
    "actual_order",
    "submitted",
    "simulated",
)

DEFAULT_BACKFILL_START_DATE = "2026-05-01"

ENTRY_ADM_UNKNOWN_FIELDS = (
    "entry_adm_bucket_token",
    "entry_adm_score_bucket",
    "entry_adm_risk_context_bucket",
    "entry_adm_stale_bucket",
    "entry_adm_price_resolution_bucket",
    "entry_adm_overbought_bucket",
    "entry_adm_liquidity_bucket",
)
SIM_OVERBOUGHT_UNKNOWN_FIELDS = (
    "sim_pre_submit_overbought_reason",
    "sim_overbought_risk_state",
    "sim_overbought_risk_bucket",
    "sim_overbought_context_source",
    "sim_overbought_source_quality",
)
STALE_DERIVED_REPORTS = (
    ("scalp_entry_action_decision_matrix", "scalp_entry_action_decision_matrix"),
    ("lifecycle_decision_matrix", "lifecycle_decision_matrix"),
    ("threshold_cycle_ev", "threshold_cycle_ev"),
    ("runtime_approval_summary", "runtime_approval_summary"),
)
BACKFILL_PREFILTER_TOKENS = (
    "sim",
    "actual_order_submitted",
    "broker_order_forbidden",
    "entry_adm_",
    "lifecycle_matrix_",
    "holding",
    "overbought",
)
BACKFILL_PREFILTER_PATTERN = (
    "sim|actual_order_submitted|broker_order_forbidden|entry_adm_|"
    "lifecycle_matrix_|holding|overbought|assumed_filled|virtual_fill"
)
RAW_ROW_EXCLUSION_DIRNAME = "raw_row_exclusion"
ORDERBOOK_MICRO_LEGACY_UNKNOWN_BUCKET_REVIEW_CUTOFF = "2026-06-08"


@dataclass(frozen=True)
class StageContract:
    required_fields: tuple[str, ...]
    zero_sensitive_fields: tuple[str, ...] = ()
    min_sample: int = 1
    max_missing_rate: float = 0.0
    max_zero_rate: float = 1.0
    decision_authority: str = "source_quality_only"
    forbidden_uses: str = "runtime_threshold_apply/order_submit/provider_route_change/bot_restart"


AI_SOURCE_FIELDS = (
    "tick_source_quality_fields_sent",
    "tick_accel_source",
    "tick_context_quality",
    "quote_age_source",
)

AI_OVERLAP_FIELDS = (
    "latest_strength",
    "buy_pressure_10t",
    "distance_from_day_high_pct",
    "intraday_range_pct",
)

ENTRY_ADM_SNAPSHOT_FIELDS = (
    "candidate_id",
    "entry_adm_candidate_id",
    "ai_score",
    "ai_action",
    "chosen_action",
    "eligible_actions",
    "rejected_actions",
    "source_stage",
    "metric_role",
    "decision_authority",
    "source_quality_gate",
    "runtime_effect",
    "allowed_runtime_apply",
    "actual_order_submitted",
    "broker_order_forbidden",
    "forbidden_uses",
    "tick_acceleration_ratio",
    "tick_acceleration_ratio_raw",
    "tick_accel_source",
    "recent_5tick_seconds",
    "prev_5tick_seconds",
    "tick_accel_effective_recent_5tick_seconds",
    "buy_pressure_10t",
    "curr_vs_micro_vwap_bp",
    "curr_vs_ma5_bp",
)

SIM_PROVENANCE_FIELDS = (
    "actual_order_submitted",
    "broker_order_forbidden",
    "runtime_effect",
)

SCALP_SIM_PROVENANCE_FIELDS = (
    "simulation_book",
    "simulated_order",
    *SIM_PROVENANCE_FIELDS,
    "decision_authority",
    "sim_record_id",
)

SCALP_SIM_SUBMIT_LIQUIDITY_GUARD_FIELDS = (
    *SCALP_SIM_PROVENANCE_FIELDS,
    "threshold_family",
    "sim_pre_submit_liquidity_guard_action",
    "sim_pre_submit_liquidity_reason",
    "sim_liquidity_value",
    "sim_min_liquidity",
    "sim_parent_record_id",
)

SCALP_SIM_SUBMIT_OVERBOUGHT_GUARD_FIELDS = (
    *SCALP_SIM_PROVENANCE_FIELDS,
    "threshold_family",
    "sim_pre_submit_overbought_guard_action",
    "sim_pre_submit_overbought_reason",
    "sim_overbought_risk_state",
    "sim_parent_record_id",
)

SCALP_SIM_AI_BUDGET_FIELDS = (
    "simulation_book",
    "simulated_order",
    *SIM_PROVENANCE_FIELDS,
    "decision_authority",
    "sim_record_id",
    "entry_adm_candidate_id",
)

SCALP_SIM_RISK_CONTEXT_FIELDS = (
    "simulation_book",
    "simulated_order",
    *SIM_PROVENANCE_FIELDS,
    "decision_authority",
    "threshold_family",
    "source_stage",
)

SWING_PROBE_FIELDS = (
    "simulated_order",
    "evidence_quality",
    "source_record_id",
)

ORDERBOOK_MICRO_FIELDS = (
    "orderbook_micro_ready",
    "orderbook_micro_state",
    "orderbook_micro_reason",
    "orderbook_micro_snapshot_age_ms",
    "orderbook_micro_observer_healthy",
)

ADM_ENTRY_CONTRACT_FIELDS = (
    "entry_adm_status",
    "entry_adm_bucket_token",
    "entry_adm_decision_alignment",
    "entry_adm_bucket_joined_sample",
)

LIFECYCLE_BUCKET_CONTRACT_FIELDS = (
    "lifecycle_bucket_match_status",
    "ldm_hypothesis_matched",
    "active_seed_matched",
)

SWING_MICRO_CONTRACT_FIELDS = (
    "swing_micro_ws_quote_source",
    "orderbook_micro_reason",
    "orderbook_micro_ready",
    "orderbook_micro_spread_ticks",
    "orderbook_micro_ofi_norm",
    "orderbook_micro_sample_quote_count",
)

PRE_AI_RISK_CONTEXT_FIELDS = (
    "metric_role",
    "decision_authority",
    "runtime_effect",
    "forbidden_uses",
    "threshold_family",
    "gate_action",
    "allowed_runtime_apply",
    "actual_order_submitted",
)

PRE_SUBMIT_GUARD_FIELDS = (
    "metric_role",
    "decision_authority",
    "runtime_effect",
    "forbidden_uses",
    "threshold_family",
    "gate_action",
    "actual_order_submitted",
    "broker_order_forbidden",
)

LATENCY_SUBMIT_FIELDS = (
    "reason",
    "latency_state",
    "policy_decision",
    "effective_decision",
    "ws_age_ms",
    "ws_jitter_ms",
    "spread_ratio",
    "quote_stale",
    "signal_price",
    "latest_price",
    "latency_canary_applied",
    "latency_canary_reason",
    "threshold_family",
    "runtime_effect",
    "actual_order_submitted",
    "broker_order_forbidden",
)

DIAGNOSTIC_CONTRACT_FIELDS = (
    "metric_role",
    "decision_authority",
    "window_policy",
    "sample_floor",
    "primary_decision_metric",
    "source_quality_gate",
    "runtime_effect",
    "forbidden_uses",
)

REAL_EXECUTION_DIAGNOSTIC_FIELDS = (
    *DIAGNOSTIC_CONTRACT_FIELDS,
    "actual_order_submitted",
    "broker_order_forbidden",
)

ENTRY_SUBMIT_SOURCE_CONTRACT_FIELDS = (
    "broker_order_submitted",
    "broker_order_no",
    "broker_receipt_status",
    "broker_receipt_reason",
    "requested_qty",
    "filled_qty",
    "remaining_qty",
    "fill_quality",
    "post_submit_state",
    "cancel_requested",
    "cancel_result",
    "position_rebased_after_fill",
    "telegram_audience",
    "telegram_event_type",
    "telegram_sent_after_broker_submit",
    "strategy_domain",
    "source_namespace",
    "blocker_namespace",
)

HIGH_VOLUME_DIAGNOSTIC_STAGE_ROLES = {
    "blocked_zero_qty": "funnel_count",
    "initial_entry_qty_cap_applied": "funnel_count",
    "order_bundle_failed": "execution_quality_real_only",
    "order_leg_fail": "execution_quality_real_only",
    "swing_probe_state_restored": "ops_volume_diagnostic",
    "preset_exit_setup": "ops_volume_diagnostic",
    "swing_same_symbol_loss_reentry_cooldowns_restored": "ops_volume_diagnostic",
}

SIM_SUBMIT_GUARD_STAGE_ACTIONS = {
    "scalp_sim_pre_submit_liquidity_guard_would_block": (
        "sim_pre_submit_liquidity_guard_action",
        "WOULD_BLOCK",
    ),
    "scalp_sim_pre_submit_liquidity_guard_would_pass": (
        "sim_pre_submit_liquidity_guard_action",
        "WOULD_PASS",
    ),
    "scalp_sim_pre_submit_liquidity_guard_unknown": (
        "sim_pre_submit_liquidity_guard_action",
        "WOULD_UNKNOWN",
    ),
    "scalp_sim_pre_submit_overbought_guard_would_block": (
        "sim_pre_submit_overbought_guard_action",
        "WOULD_BLOCK",
    ),
    "scalp_sim_pre_submit_overbought_guard_would_pass": (
        "sim_pre_submit_overbought_guard_action",
        "WOULD_PASS",
    ),
}


STAGE_CONTRACTS: dict[str, StageContract] = {
    "scalp_entry_action_decision_snapshot": StageContract(
        required_fields=(*AI_SOURCE_FIELDS, *ENTRY_ADM_SNAPSHOT_FIELDS),
        max_missing_rate=0.10,
    ),
    "ai_confirmed": StageContract(
        required_fields=(*AI_SOURCE_FIELDS, *AI_OVERLAP_FIELDS),
        zero_sensitive_fields=("intraday_range_pct",),
        max_missing_rate=0.25,
        max_zero_rate=0.10,
    ),
    "blocked_ai_score": StageContract(
        required_fields=(*AI_SOURCE_FIELDS, *AI_OVERLAP_FIELDS),
        zero_sensitive_fields=("distance_from_day_high_pct", "intraday_range_pct"),
        max_missing_rate=0.10,
        max_zero_rate=0.10,
    ),
    "wait65_79_ev_candidate": StageContract(
        required_fields=AI_SOURCE_FIELDS,
        max_missing_rate=0.10,
    ),
    "score65_74_recovery_probe_blocked": StageContract(
        required_fields=(
            *DIAGNOSTIC_CONTRACT_FIELDS,
            "actual_order_submitted",
            "broker_order_forbidden",
            "threshold_family",
            "score65_74_recovery_probe_skip_reason",
            "ai_score",
            "buy_pressure",
            "tick_accel",
            "micro_vwap_bp",
            "score65_74_recovery_probe_min_buy_pressure",
            "score65_74_recovery_probe_min_tick_accel",
            "score65_74_recovery_probe_min_micro_vwap_bp",
        ),
        decision_authority="score65_74_recovery_probe_block_observation_only",
    ),
    "scalping_scanner_real_source_guard_block": StageContract(
        required_fields=(
            *REAL_EXECUTION_DIAGNOSTIC_FIELDS,
            "scanner_real_source_guard_applied",
            "scanner_real_source_guard_skip_reason",
            "scanner_real_source_guard_block_event_emitted",
            "source_signature",
            "current_flu_rate",
        ),
        decision_authority="real_scalping_scanner_source_guard_only",
    ),
    "early_accel_recheck_evaluated": StageContract(
        required_fields=(
            *REAL_EXECUTION_DIAGNOSTIC_FIELDS,
            "allowed_runtime_apply",
            "scanner_promotion_reason",
            "promotion_price",
            "current_price",
            "promotion_age_sec",
            "recheck_count",
            "last_ai_elapsed_sec",
            "skip_reason",
            "tick_accel",
            "micro_vwap_bp",
            "quote_stale",
        ),
        decision_authority="operator_runtime_observation_retry_only",
    ),
    "early_accel_recheck_ai_call_allowed": StageContract(
        required_fields=(
            *REAL_EXECUTION_DIAGNOSTIC_FIELDS,
            "allowed_runtime_apply",
            "scanner_promotion_reason",
            "promotion_price",
            "current_price",
            "promotion_age_sec",
            "recheck_count",
            "last_ai_elapsed_sec",
            "skip_reason",
            "tick_accel",
            "micro_vwap_bp",
            "quote_stale",
        ),
        decision_authority="operator_runtime_observation_retry_only",
    ),
    "early_accel_recheck_skipped": StageContract(
        required_fields=(
            *REAL_EXECUTION_DIAGNOSTIC_FIELDS,
            "allowed_runtime_apply",
            "scanner_promotion_reason",
            "promotion_price",
            "current_price",
            "promotion_age_sec",
            "recheck_count",
            "last_ai_elapsed_sec",
            "skip_reason",
            "tick_accel",
            "micro_vwap_bp",
            "quote_stale",
        ),
        decision_authority="operator_runtime_observation_retry_only",
    ),
    "ai_numeric_consistency_recheck_evaluated": StageContract(
        required_fields=(
            *REAL_EXECUTION_DIAGNOSTIC_FIELDS,
            "allowed_runtime_apply",
            "original_action",
            "original_score",
            "original_reason_excerpt",
            "inconsistency_field",
            "inconsistency_reason",
            "position_pass",
            "speed_pass",
            "supply_pass",
            "feature_pass_count",
            "recheck_count",
            "recheck_action",
            "recheck_score",
            "recheck_reason_excerpt",
            "skip_reason",
            "quote_stale",
        ),
        decision_authority="operator_runtime_decision_recheck_only",
    ),
    "ai_numeric_consistency_recheck_allowed": StageContract(
        required_fields=(
            *REAL_EXECUTION_DIAGNOSTIC_FIELDS,
            "allowed_runtime_apply",
            "original_action",
            "original_score",
            "original_reason_excerpt",
            "inconsistency_field",
            "inconsistency_reason",
            "position_pass",
            "speed_pass",
            "supply_pass",
            "feature_pass_count",
            "recheck_count",
            "recheck_action",
            "recheck_score",
            "recheck_reason_excerpt",
            "skip_reason",
            "quote_stale",
        ),
        decision_authority="operator_runtime_decision_recheck_only",
    ),
    "ai_numeric_consistency_recheck_skipped": StageContract(
        required_fields=(
            *REAL_EXECUTION_DIAGNOSTIC_FIELDS,
            "allowed_runtime_apply",
            "original_action",
            "original_score",
            "original_reason_excerpt",
            "inconsistency_field",
            "inconsistency_reason",
            "position_pass",
            "speed_pass",
            "supply_pass",
            "feature_pass_count",
            "recheck_count",
            "recheck_action",
            "recheck_score",
            "recheck_reason_excerpt",
            "skip_reason",
            "quote_stale",
        ),
        decision_authority="operator_runtime_decision_recheck_only",
    ),
    "ai_numeric_consistency_recheck_failed": StageContract(
        required_fields=(
            *REAL_EXECUTION_DIAGNOSTIC_FIELDS,
            "allowed_runtime_apply",
            "original_action",
            "original_score",
            "original_reason_excerpt",
            "inconsistency_field",
            "inconsistency_reason",
            "position_pass",
            "speed_pass",
            "supply_pass",
            "feature_pass_count",
            "recheck_count",
            "recheck_action",
            "recheck_score",
            "recheck_reason_excerpt",
            "skip_reason",
            "quote_stale",
        ),
        decision_authority="operator_runtime_decision_recheck_only",
    ),
    "ai_numeric_consistency_recheck_corrected": StageContract(
        required_fields=(
            *REAL_EXECUTION_DIAGNOSTIC_FIELDS,
            "allowed_runtime_apply",
            "original_action",
            "original_score",
            "original_reason_excerpt",
            "inconsistency_field",
            "inconsistency_reason",
            "position_pass",
            "speed_pass",
            "supply_pass",
            "feature_pass_count",
            "recheck_count",
            "recheck_action",
            "recheck_score",
            "recheck_reason_excerpt",
            "skip_reason",
            "quote_stale",
        ),
        decision_authority="operator_runtime_decision_recheck_only",
    ),
    "early_accel_strong_bundle_recheck_evaluated": StageContract(
        required_fields=(
            *REAL_EXECUTION_DIAGNOSTIC_FIELDS,
            "allowed_runtime_apply",
            "scanner_promotion_reason",
            "source_signature",
            "strong_bundle_pass_count",
            "price_delta_since_first_seen_pct",
            "comparable_flu_delta_since_first_seen",
            "cntr_str_available",
            "cntr_str",
            "tick_acceleration_ratio",
            "curr_vs_micro_vwap_bp",
            "buy_pressure_10t",
            "original_action",
            "original_score",
            "recheck_action",
            "recheck_score",
            "recheck_count",
            "quote_stale",
            "skip_reason",
        ),
        decision_authority="operator_runtime_decision_recheck_only",
    ),
    "early_accel_strong_bundle_recheck_allowed": StageContract(
        required_fields=(
            *REAL_EXECUTION_DIAGNOSTIC_FIELDS,
            "allowed_runtime_apply",
            "scanner_promotion_reason",
            "source_signature",
            "strong_bundle_pass_count",
            "price_delta_since_first_seen_pct",
            "comparable_flu_delta_since_first_seen",
            "cntr_str_available",
            "cntr_str",
            "tick_acceleration_ratio",
            "curr_vs_micro_vwap_bp",
            "buy_pressure_10t",
            "original_action",
            "original_score",
            "recheck_action",
            "recheck_score",
            "recheck_count",
            "quote_stale",
            "skip_reason",
        ),
        decision_authority="operator_runtime_decision_recheck_only",
    ),
    "early_accel_strong_bundle_recheck_skipped": StageContract(
        required_fields=(
            *REAL_EXECUTION_DIAGNOSTIC_FIELDS,
            "allowed_runtime_apply",
            "scanner_promotion_reason",
            "source_signature",
            "strong_bundle_pass_count",
            "price_delta_since_first_seen_pct",
            "comparable_flu_delta_since_first_seen",
            "cntr_str_available",
            "cntr_str",
            "tick_acceleration_ratio",
            "curr_vs_micro_vwap_bp",
            "buy_pressure_10t",
            "original_action",
            "original_score",
            "recheck_action",
            "recheck_score",
            "recheck_count",
            "quote_stale",
            "skip_reason",
        ),
        decision_authority="operator_runtime_decision_recheck_only",
    ),
    "early_accel_strong_bundle_recheck_failed": StageContract(
        required_fields=(
            *REAL_EXECUTION_DIAGNOSTIC_FIELDS,
            "allowed_runtime_apply",
            "scanner_promotion_reason",
            "source_signature",
            "strong_bundle_pass_count",
            "price_delta_since_first_seen_pct",
            "comparable_flu_delta_since_first_seen",
            "cntr_str_available",
            "cntr_str",
            "tick_acceleration_ratio",
            "curr_vs_micro_vwap_bp",
            "buy_pressure_10t",
            "original_action",
            "original_score",
            "recheck_action",
            "recheck_score",
            "recheck_count",
            "quote_stale",
            "skip_reason",
        ),
        decision_authority="operator_runtime_decision_recheck_only",
    ),
    "early_accel_strong_bundle_recheck_corrected": StageContract(
        required_fields=(
            *REAL_EXECUTION_DIAGNOSTIC_FIELDS,
            "allowed_runtime_apply",
            "scanner_promotion_reason",
            "source_signature",
            "strong_bundle_pass_count",
            "price_delta_since_first_seen_pct",
            "comparable_flu_delta_since_first_seen",
            "cntr_str_available",
            "cntr_str",
            "tick_acceleration_ratio",
            "curr_vs_micro_vwap_bp",
            "buy_pressure_10t",
            "original_action",
            "original_score",
            "recheck_action",
            "recheck_score",
            "recheck_count",
            "quote_stale",
            "skip_reason",
        ),
        decision_authority="operator_runtime_decision_recheck_only",
    ),
    "condition_unmatch_guard": StageContract(
        required_fields=(
            *REAL_EXECUTION_DIAGNOSTIC_FIELDS,
            "condition_unmatch_guard_applied",
            "condition_unmatch_guard_action",
            "condition_unmatch_guard_reason",
            "condition_unmatch_age_sec",
            "condition_name",
            "position_tag",
        ),
        decision_authority="real_scalping_condition_unmatch_guard_only",
    ),
    "s15_candidate_armed": StageContract(
        required_fields=(
            *REAL_EXECUTION_DIAGNOSTIC_FIELDS,
            "s15_fast_track_contract_version",
            "s15_condition_role",
            "base_condition",
            "armed_at",
            "expires_at",
            "ttl_sec",
        ),
        decision_authority="real_s15_fast_track_runtime_only",
    ),
    "s15_trigger_received": StageContract(
        required_fields=(
            *REAL_EXECUTION_DIAGNOSTIC_FIELDS,
            "s15_fast_track_contract_version",
            "s15_condition_role",
            "condition_name",
            "armed",
            "reentry_blocked",
            "existing_fast_state",
            "trigger_price",
        ),
        decision_authority="real_s15_fast_track_runtime_only",
    ),
    "s15_trigger_blocked": StageContract(
        required_fields=(
            *REAL_EXECUTION_DIAGNOSTIC_FIELDS,
            "s15_fast_track_contract_version",
            "s15_condition_role",
            "s15_block_reason",
        ),
        decision_authority="real_s15_fast_track_runtime_only",
    ),
    "s15_fast_track_submitted": StageContract(
        required_fields=(
            *REAL_EXECUTION_DIAGNOSTIC_FIELDS,
            "s15_fast_track_contract_version",
            "s15_condition_role",
            "shadow_id",
            "requested_qty",
            "order_price",
            "broker_order_no",
        ),
        decision_authority="real_s15_fast_track_runtime_only",
    ),
    "s15_fast_track_cancelled": StageContract(
        required_fields=(
            *REAL_EXECUTION_DIAGNOSTIC_FIELDS,
            "s15_fast_track_contract_version",
            "s15_condition_role",
            "shadow_id",
            "s15_cancel_reason",
        ),
        decision_authority="real_s15_fast_track_runtime_only",
    ),
    "s15_fast_track_holding": StageContract(
        required_fields=(
            *REAL_EXECUTION_DIAGNOSTIC_FIELDS,
            "s15_fast_track_contract_version",
            "s15_condition_role",
            "shadow_id",
            "avg_buy_price",
            "buy_qty",
            "target_price",
            "stop_price",
        ),
        decision_authority="real_s15_fast_track_runtime_only",
    ),
    "s15_fast_track_completed": StageContract(
        required_fields=(
            *REAL_EXECUTION_DIAGNOSTIC_FIELDS,
            "s15_fast_track_contract_version",
            "s15_condition_role",
            "shadow_id",
            "buy_price",
            "sell_price",
            "buy_qty",
            "profit_rate",
        ),
        decision_authority="real_s15_fast_track_runtime_only",
    ),
    "s15_fast_track_failed": StageContract(
        required_fields=(
            *REAL_EXECUTION_DIAGNOSTIC_FIELDS,
            "s15_fast_track_contract_version",
            "s15_condition_role",
            "s15_block_reason",
        ),
        decision_authority="real_s15_fast_track_runtime_only",
    ),
    "blocked_strength_momentum": StageContract(
        required_fields=(*AI_OVERLAP_FIELDS, *PRE_AI_RISK_CONTEXT_FIELDS),
        zero_sensitive_fields=("intraday_range_pct",),
        max_zero_rate=0.10,
    ),
    "blocked_vpw": StageContract(
        required_fields=(*AI_OVERLAP_FIELDS, *PRE_AI_RISK_CONTEXT_FIELDS),
        zero_sensitive_fields=("distance_from_day_high_pct", "intraday_range_pct"),
        max_zero_rate=0.10,
    ),
    "blocked_overbought": StageContract(
        required_fields=(*AI_OVERLAP_FIELDS, *PRE_AI_RISK_CONTEXT_FIELDS),
        zero_sensitive_fields=("intraday_range_pct",),
        max_zero_rate=0.10,
    ),
    "blocked_liquidity": StageContract(
        required_fields=(*PRE_AI_RISK_CONTEXT_FIELDS, "liquidity_value", "min_liquidity"),
    ),
    "pre_submit_liquidity_guard_block": StageContract(
        required_fields=(*PRE_SUBMIT_GUARD_FIELDS, "liquidity_value", "min_liquidity"),
    ),
    "pre_submit_overbought_pullback_guard_block": StageContract(
        required_fields=(*PRE_SUBMIT_GUARD_FIELDS, "risk_state"),
    ),
    "latency_block": StageContract(
        required_fields=LATENCY_SUBMIT_FIELDS,
        decision_authority="source_quality_only_known_pre_fix_gap",
    ),
    "latency_pass": StageContract(
        required_fields=LATENCY_SUBMIT_FIELDS,
        decision_authority="source_quality_only_known_pre_fix_gap",
    ),
    "order_bundle_submitted": StageContract(
        required_fields=(*LATENCY_SUBMIT_FIELDS, *ENTRY_SUBMIT_SOURCE_CONTRACT_FIELDS),
        decision_authority="source_quality_only_known_pre_fix_gap",
    ),
    "scalp_sim_entry_armed": StageContract(required_fields=SCALP_SIM_PROVENANCE_FIELDS),
    "scalp_sim_duplicate_buy_signal": StageContract(
        required_fields=(*SCALP_SIM_PROVENANCE_FIELDS, "threshold_family", "sim_parent_record_id"),
    ),
    "scalp_sim_pre_submit_liquidity_guard_would_block": StageContract(
        required_fields=SCALP_SIM_SUBMIT_LIQUIDITY_GUARD_FIELDS
    ),
    "scalp_sim_pre_submit_liquidity_guard_would_pass": StageContract(
        required_fields=SCALP_SIM_SUBMIT_LIQUIDITY_GUARD_FIELDS
    ),
    "scalp_sim_pre_submit_liquidity_guard_unknown": StageContract(
        required_fields=SCALP_SIM_SUBMIT_LIQUIDITY_GUARD_FIELDS,
        decision_authority="source_quality_only_known_pre_fix_gap",
    ),
    "scalp_sim_pre_submit_overbought_guard_would_block": StageContract(
        required_fields=SCALP_SIM_SUBMIT_OVERBOUGHT_GUARD_FIELDS
    ),
    "scalp_sim_pre_submit_overbought_guard_would_pass": StageContract(
        required_fields=SCALP_SIM_SUBMIT_OVERBOUGHT_GUARD_FIELDS
    ),
    "scalp_sim_buy_order_virtual_pending": StageContract(required_fields=SCALP_SIM_PROVENANCE_FIELDS),
    "scalp_sim_buy_order_assumed_filled": StageContract(required_fields=SCALP_SIM_PROVENANCE_FIELDS),
    "scalp_sim_entry_ai_price_skip_order": StageContract(required_fields=SCALP_SIM_PROVENANCE_FIELDS),
    "scalp_sim_entry_submit_revalidation_warning": StageContract(
        required_fields=(
            *SCALP_SIM_PROVENANCE_FIELDS,
            "threshold_family",
            "sim_parent_record_id",
            "entry_submit_revalidation_warning",
            "quote_age_at_submit_ms",
            "submitted_order_price",
            "mark_price_at_submit",
        ),
    ),
    "scalp_sim_holding_started": StageContract(required_fields=SCALP_SIM_PROVENANCE_FIELDS),
    "scalp_sim_scale_in_candidate_funnel": StageContract(
        required_fields=(
            *SCALP_SIM_PROVENANCE_FIELDS,
            "scale_in_arm",
            "scale_in_candidate_funnel_state",
            "metric_role",
            "window_policy",
            "primary_decision_metric",
            "source_quality_gate",
            "forbidden_uses",
        )
    ),
    "scalp_sim_scale_in_order_assumed_filled": StageContract(required_fields=SCALP_SIM_PROVENANCE_FIELDS),
    "scalp_sim_scale_in_order_unfilled": StageContract(required_fields=SCALP_SIM_PROVENANCE_FIELDS),
    "scalp_sim_scale_in_counterfactual_started": StageContract(required_fields=SCALP_SIM_PROVENANCE_FIELDS),
    "scalp_sim_sell_order_assumed_filled": StageContract(required_fields=SCALP_SIM_PROVENANCE_FIELDS),
    "scalp_sim_ai_holding_live_call": StageContract(
        required_fields=SCALP_SIM_AI_BUDGET_FIELDS,
        decision_authority="source_quality_only_known_pre_fix_gap",
    ),
    "scalp_sim_ai_holding_deferred": StageContract(
        required_fields=SCALP_SIM_AI_BUDGET_FIELDS,
        decision_authority="source_quality_only_known_pre_fix_gap",
    ),
    "sim_ai_budget_exhausted": StageContract(
        required_fields=SCALP_SIM_AI_BUDGET_FIELDS,
        decision_authority="source_quality_only_known_pre_fix_gap",
    ),
    "sim_ai_critical_bypass": StageContract(
        required_fields=SCALP_SIM_AI_BUDGET_FIELDS,
        decision_authority="source_quality_only_known_pre_fix_gap",
    ),
    "scalp_sim_panic_bottoming_entry_allowed": StageContract(required_fields=SCALP_SIM_RISK_CONTEXT_FIELDS),
    "scalp_sim_panic_level1_entry_observed": StageContract(required_fields=SCALP_SIM_RISK_CONTEXT_FIELDS),
    "scalp_sim_panic_entry_blocked": StageContract(required_fields=SCALP_SIM_RISK_CONTEXT_FIELDS),
    "scalp_sim_panic_scale_in_blocked": StageContract(required_fields=(*SCALP_SIM_RISK_CONTEXT_FIELDS, "sim_record_id")),
    "scalp_sim_panic_action_deduped": StageContract(required_fields=(*SCALP_SIM_RISK_CONTEXT_FIELDS, "sim_record_id")),
    "scalp_sim_partial_sell_order_assumed_filled": StageContract(
        required_fields=(*SCALP_SIM_RISK_CONTEXT_FIELDS, "sim_record_id", "entry_adm_candidate_id")
    ),
    "scalp_sim_euphoria_context_noop": StageContract(required_fields=SCALP_SIM_RISK_CONTEXT_FIELDS),
    "scalp_sim_euphoria_entry_blocked": StageContract(required_fields=SCALP_SIM_RISK_CONTEXT_FIELDS),
    "scalp_sim_euphoria_chase_entry_blocked": StageContract(required_fields=SCALP_SIM_RISK_CONTEXT_FIELDS),
    "scalp_sim_euphoria_retest_starter_allowed": StageContract(required_fields=SCALP_SIM_RISK_CONTEXT_FIELDS),
    "scalp_sim_euphoria_level1_starter_observed": StageContract(required_fields=SCALP_SIM_RISK_CONTEXT_FIELDS),
    "scalp_sim_euphoria_scale_in_blocked": StageContract(required_fields=SCALP_SIM_RISK_CONTEXT_FIELDS),
    "scalp_sim_euphoria_partial_profit_assumed_filled": StageContract(required_fields=SCALP_SIM_RISK_CONTEXT_FIELDS),
    "scalp_sim_euphoria_partial_profit_unpriced": StageContract(required_fields=SCALP_SIM_RISK_CONTEXT_FIELDS),
    "scalp_sim_euphoria_action_deduped": StageContract(required_fields=SCALP_SIM_RISK_CONTEXT_FIELDS),
    "ai_holding_fast_reuse_band": StageContract(
        required_fields=(*DIAGNOSTIC_CONTRACT_FIELDS, "source_quality_route", "telemetry_only", "action"),
        decision_authority="source_quality_only",
    ),
    "soft_stop_expert_shadow": StageContract(
        required_fields=(*DIAGNOSTIC_CONTRACT_FIELDS, "source_quality_route", "shadow_only", "hierarchy"),
        decision_authority="source_quality_only",
    ),
    "holding_flow_override_candidate_cleared": StageContract(
        required_fields=(*DIAGNOSTIC_CONTRACT_FIELDS, "source_quality_route", "reason", "previous_key"),
        decision_authority="source_quality_only",
    ),
    "swing_probe_entry_candidate": StageContract(
        required_fields=(*SIM_PROVENANCE_FIELDS, *SWING_PROBE_FIELDS, "virtual_budget_override", "budget_authority"),
    ),
    "swing_probe_holding_started": StageContract(
        required_fields=(*SIM_PROVENANCE_FIELDS, *SWING_PROBE_FIELDS, "virtual_budget_override", "budget_authority"),
    ),
    "swing_probe_exit_signal": StageContract(required_fields=(*SIM_PROVENANCE_FIELDS, *SWING_PROBE_FIELDS)),
    "swing_probe_sell_order_assumed_filled": StageContract(
        required_fields=(*SIM_PROVENANCE_FIELDS, *SWING_PROBE_FIELDS, *ORDERBOOK_MICRO_FIELDS),
        max_missing_rate=0.05,
    ),
    "swing_probe_scale_in_order_assumed_filled": StageContract(
        required_fields=(*SIM_PROVENANCE_FIELDS, *SWING_PROBE_FIELDS, *ORDERBOOK_MICRO_FIELDS),
        max_missing_rate=0.05,
    ),
    "swing_reentry_counterfactual_after_loss": StageContract(
        required_fields=("simulated_order", "actual_order_submitted", "broker_order_forbidden", "runtime_effect"),
    ),
    "swing_same_symbol_loss_reentry_cooldown": StageContract(
        required_fields=(
            "actual_order_submitted",
            "broker_order_forbidden",
            "source_book",
            "source_probe_id",
            "source_record_id",
            "source_stage",
        ),
    ),
    "swing_probe_state_persisted": StageContract(
        required_fields=(
            "simulation_book",
            "simulation_owner",
            "metric_role",
            "decision_authority",
            "runtime_effect",
            "forbidden_uses",
        ),
    ),
    "swing_probe_discarded": StageContract(
        required_fields=(
            *SIM_PROVENANCE_FIELDS,
            *SWING_PROBE_FIELDS,
            "decision_authority",
            "simulation_book",
            "simulation_owner",
            "probe_origin_stage",
            "discard_reason",
            "blocker_authority",
            "quota_observation_scope",
            "allowed_runtime_apply",
        ),
        decision_authority="swing_sim_exploration_only",
    ),
    "swing_entry_micro_context_observed": StageContract(required_fields=ORDERBOOK_MICRO_FIELDS),
    "swing_scale_in_micro_context_observed": StageContract(required_fields=ORDERBOOK_MICRO_FIELDS),
    "scale_in_price_resolved": StageContract(
        required_fields=("price_source", "virtual_budget_override", "budget_authority", *ORDERBOOK_MICRO_FIELDS),
        max_missing_rate=0.50,
    ),
    "scale_in_price_p2_observe": StageContract(
        required_fields=("price_source", *ORDERBOOK_MICRO_FIELDS),
        max_missing_rate=0.50,
    ),
    "swing_sim_scale_in_order_assumed_filled": StageContract(
        required_fields=("actual_order_submitted", "broker_order_forbidden", "virtual_budget_override", "budget_authority", *ORDERBOOK_MICRO_FIELDS),
        max_missing_rate=0.05,
    ),
    "loss_fallback_probe": StageContract(
        required_fields=("gate_allowed", "gate_reason", "fallback_candidate", "fallback_reason", "profit_rate", "peak_profit"),
        decision_authority="source_quality_only",
    ),
    "soft_stop_whipsaw_confirmation": StageContract(
        required_fields=("threshold_family", "threshold_version", "threshold_calibration_state", "profit_rate", "flow_state", "exit_rule_candidate"),
        decision_authority="source_quality_only",
    ),
    "blocked_gatekeeper_reject": StageContract(
        required_fields=("action", "cooldown_policy"),
        decision_authority="source_quality_only",
    ),
    "entry_armed": StageContract(
        required_fields=("ai_score", "ratio", "target_buy_price", "current_vpw", "reason", "ttl_sec"),
        decision_authority="source_quality_only",
    ),
    "entry_armed_expired_after_wait": StageContract(
        required_fields=("waited_sec", "resume_count", "reason"),
        decision_authority="source_quality_only",
    ),
    "holding_started": StageContract(
        required_fields=REAL_EXECUTION_DIAGNOSTIC_FIELDS,
        decision_authority="broker_receipt_observation_only",
    ),
    "scale_in_executed": StageContract(
        required_fields=REAL_EXECUTION_DIAGNOSTIC_FIELDS,
        decision_authority="broker_receipt_observation_only",
    ),
    "same_symbol_loss_reentry_cooldown": StageContract(
        required_fields=(
            *DIAGNOSTIC_CONTRACT_FIELDS,
            "actual_order_submitted",
            "broker_order_forbidden",
            "source_stage",
            "guard_family",
        ),
        decision_authority="same_symbol_loss_reentry_guard_observation_only",
    ),
    **{
        stage: StageContract(
            required_fields=DIAGNOSTIC_CONTRACT_FIELDS,
            decision_authority="source_quality_only",
        )
        for stage in HIGH_VOLUME_DIAGNOSTIC_STAGE_ROLES
    },
}


def _pipeline_events_path(target_date: str) -> Path:
    return DATA_DIR / "pipeline_events" / f"pipeline_events_{target_date}.jsonl"


def _threshold_events_path(target_date: str) -> Path:
    return DATA_DIR / "threshold_cycle" / f"threshold_events_{target_date}.jsonl"


def report_paths(target_date: str) -> tuple[Path, Path]:
    report_dir = DATA_DIR / "report" / REPORT_DIRNAME
    return (
        report_dir / f"observation_source_quality_audit_{target_date}.json",
        report_dir / f"observation_source_quality_audit_{target_date}.md",
    )


def backfill_report_paths(target_date: str) -> tuple[Path, Path]:
    report_dir = DATA_DIR / "report" / REPORT_DIRNAME
    return (
        report_dir / f"{BACKFILL_REPORT_STEM}_{target_date}.json",
        report_dir / f"{BACKFILL_REPORT_STEM}_{target_date}.md",
    )


def _parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def _date_range(start_date: str, end_date: str) -> list[str]:
    start = _parse_date(start_date)
    end = _parse_date(end_date)
    if start > end:
        raise ValueError(f"start_date must be <= target_date: {start_date} > {end_date}")
    days: list[str] = []
    current = start
    while current <= end:
        days.append(current.isoformat())
        current += timedelta(days=1)
    return days


def _safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except Exception:
        return None


def _is_present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str) and value.strip() in {"", "-", "None", "none", "null"}:
        return False
    return True


def _source_like_field(key: str) -> bool:
    lowered = str(key).lower()
    return any(token in lowered for token in SOURCE_LIKE_TOKENS)


def _unknown_token_present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, (dict, list, tuple, set)):
        try:
            text = json.dumps(value, ensure_ascii=False, sort_keys=True)
        except Exception:
            text = str(value)
    else:
        text = str(value)
    return "unknown" in text.lower()


def _reviewed_unknown_reason(value: Any) -> str | None:
    if isinstance(value, (dict, list, tuple, set)):
        try:
            text = json.dumps(value, ensure_ascii=False, sort_keys=True)
        except Exception:
            text = str(value)
    else:
        text = str(value)
    lowered = text.lower()
    if "unknown" not in lowered:
        return None
    if "sample=insufficient" in lowered or "insufficient_sample" in lowered:
        return "reviewed_insufficient_sample"
    if "not_applicable" in lowered or "not_available" in lowered or "not_evaluated" in lowered:
        return "reviewed_not_available"
    if "unknown_pre_contract" in lowered:
        return "reviewed_pre_contract_placeholder"
    if "panic_context_status" in lowered and "missing" in lowered and "risk_regime" in lowered:
        return "reviewed_missing_risk_regime_context"
    if "panic_level_reason" in lowered and "context_not_ok" in lowered and "market_risk_state" in lowered:
        return "reviewed_missing_risk_regime_context"
    return None


def _reviewed_unknown_reason_for_field(key: str, value: Any, *, emitted_date: str | None = None) -> str | None:
    reviewed_reason = _reviewed_unknown_reason(value)
    if reviewed_reason:
        return reviewed_reason
    field = str(key or "")
    if not field.startswith("orderbook_micro_ofi_"):
        return None
    date_text = str(emitted_date or "")
    if not date_text or date_text > ORDERBOOK_MICRO_LEGACY_UNKNOWN_BUCKET_REVIEW_CUTOFF:
        return None
    text = str(value or "").lower()
    if "unknown" not in text:
        return None
    parts = {part.partition("=")[0]: part.partition("=")[2] for part in text.split("|") if "=" in part}
    if not parts:
        return None
    if any(parts.get(name) == "unknown" for name in ("spread", "price", "depth")):
        return "reviewed_orderbook_micro_legacy_not_available_bucket"
    return None


def _reviewed_unknown_reason_for_stage_field(
    stage: str,
    key: str,
    value: Any,
    normalized: dict[str, Any],
) -> str | None:
    def _field_text(field: str) -> str:
        value = normalized.get(field)
        return "" if value is None else str(value).strip()

    def _is_reviewed_sim_liquidity_not_available() -> bool:
        authority = _field_text("decision_authority")
        source_stage = _field_text("source_stage")
        return (
            authority
            in {
                "sim_submit_path_observation_only",
                "sim_observation_only",
                "entry_advisory_prompt_context_only",
            }
            and (authority != "entry_advisory_prompt_context_only" or source_stage == "scalp_sim_entry_armed")
            and _field_text("actual_order_submitted").lower() in {"false", "0", "no"}
            and _field_text("broker_order_forbidden").lower() in {"true", "1", "yes"}
            and _field_text("sim_pre_submit_liquidity_reason") == "liquidity_not_available"
            and _field_text("sim_liquidity_value") == "not_available"
            and _field_text("sim_min_liquidity") not in {"", "-", "unknown_pre_contract"}
            and _field_text("sim_parent_record_id") not in {"", "-", "unknown_pre_contract"}
        )

    if not _unknown_token_present(value):
        return None
    if str(key or "") == "sim_pre_submit_liquidity_guard_action" and str(value or "").upper() == "WOULD_UNKNOWN":
        if _is_reviewed_sim_liquidity_not_available():
            return "reviewed_sim_liquidity_not_available"
        return None
    if str(key or "") == "__stage" and str(stage or "") == "scalp_sim_pre_submit_liquidity_guard_unknown":
        if _is_reviewed_sim_liquidity_not_available():
            return "reviewed_explicit_sim_liquidity_unknown_stage"
        return None
    if str(key or "") == "fill_quality" and str(value or "").upper() == "UNKNOWN":
        requested_qty_value = (
            normalized.get("requested_qty")
            if normalized.get("requested_qty") is not None
            else normalized.get("entry_requested_qty")
        )
        requested_qty = str(requested_qty_value).strip()
        if str(stage or "") in {"position_rebased_after_fill", "preset_exit_sync_ok"} and requested_qty in {
            "0",
            "0.0",
        }:
            return "reviewed_fill_quality_pre_contract_no_requested_qty"
    return None


def _unknown_scan_values(row: dict[str, Any], normalized: dict[str, Any]) -> dict[str, Any]:
    values = dict(normalized)
    for key in ("stage", "pipeline", "stock_code", "stock_name", "event_type"):
        value = row.get(key)
        if _unknown_token_present(value):
            values[f"__{key}"] = value
    return values


def _iter_events(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    path = existing_or_gzip_path(path)
    if not path.exists():
        return rows
    for payload in iter_jsonl(path):
        if payload.get("event_type") not in (None, "", "pipeline_event"):
            continue
        fields = payload.get("fields")
        payload["fields"] = fields if isinstance(fields, dict) else {}
        rows.append(payload)
    return rows


def _stage_name(row: dict[str, Any]) -> str:
    return str(row.get("stage") or "-")


def _normalized_fields_for_contract(stage: str, fields: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(fields or {})
    contract = STAGE_CONTRACTS.get(stage)
    if contract and "metric_role" in contract.required_fields and stage != "swing_probe_state_persisted":
        normalized.setdefault("window_policy", "same_day_source_quality_audit")
        normalized.setdefault("sample_floor", contract.min_sample)
        normalized.setdefault("primary_decision_metric", "source_quality_gate")
        normalized.setdefault("source_quality_gate", "contract_fields_present")
    if stage == "ai_confirmed":
        for field in AI_SOURCE_FIELDS:
            if not _is_present(normalized.get(field)):
                normalized[field] = "not_evaluated_pre_contract" if field != "tick_source_quality_fields_sent" else False
        normalized.setdefault("ai_input_source_quality_status", "not_evaluated")
        normalized.setdefault("ai_input_source_quality_reason", "pre_contract_or_cooldown_score50_path")
    if stage in {"latency_block", "latency_pass", "order_bundle_submitted"}:
        if not _is_present(normalized.get("policy_decision")):
            normalized["policy_decision"] = normalized.get("decision") or normalized.get("effective_decision") or "unknown_pre_contract"
        if not _is_present(normalized.get("effective_decision")):
            normalized["effective_decision"] = normalized.get("policy_decision") or "unknown_pre_contract"
        for field in ("ws_age_ms", "ws_jitter_ms", "spread_ratio"):
            if not _is_present(normalized.get(field)):
                normalized[field] = "unknown_pre_contract"
        if not _is_present(normalized.get("latency_canary_reason")):
            normalized["latency_canary_reason"] = "not_applicable_or_pre_contract"
    if stage == "order_bundle_submitted":
        submitted = str(
            normalized.get("actual_order_submitted")
            if _is_present(normalized.get("actual_order_submitted"))
            else normalized.get("order_submitted")
            if _is_present(normalized.get("order_submitted"))
            else normalized.get("broker_order_submitted")
        ).strip().lower()
        submitted_bool = submitted not in {"", "0", "false", "none", "no", "unknown_pre_contract"}
        normalized.setdefault("broker_order_submitted", submitted_bool)
        normalized.setdefault(
            "broker_order_no",
            normalized.get("order_no")
            or normalized.get("ord_no")
            or normalized.get("broker_order_id")
            or normalized.get("broker_order_no")
            or "unknown_pre_contract",
        )
        if not _is_present(normalized.get("broker_receipt_status")):
            normalized["broker_receipt_status"] = (
                "submitted_receipt_observed"
                if submitted_bool and normalized.get("broker_order_no") != "unknown_pre_contract"
                else "unknown_pre_contract"
                if submitted_bool
                else "not_submitted"
            )
        normalized.setdefault(
            "broker_receipt_reason",
            normalized.get("reason") or normalized.get("latency_canary_reason") or "source_contract_backfill",
        )
        normalized.setdefault("requested_qty", normalized.get("qty") or normalized.get("order_qty") or "unknown_pre_contract")
        normalized.setdefault("filled_qty", normalized.get("filled_qty") or "unknown_pre_contract")
        normalized.setdefault("remaining_qty", normalized.get("remaining_qty") or "unknown_pre_contract")
        normalized.setdefault("fill_quality", normalized.get("fill_status") or "unknown_pre_contract")
        normalized.setdefault("post_submit_state", normalized.get("order_state") or "submitted_or_pending")
        normalized.setdefault("cancel_requested", False)
        normalized.setdefault("cancel_result", "not_requested")
        normalized.setdefault("position_rebased_after_fill", False)
        normalized.setdefault("telegram_audience", normalized.get("telegram_audience") or "all")
        normalized.setdefault("telegram_event_type", normalized.get("telegram_event_type") or "buy_post_submit")
        normalized.setdefault("telegram_sent_after_broker_submit", submitted_bool)
        normalized.setdefault("strategy_domain", normalized.get("strategy_domain") or normalized.get("strategy") or "scalping")
        normalized.setdefault("source_namespace", normalized.get("source_namespace") or "scalping_entry_submit")
        normalized.setdefault("blocker_namespace", normalized.get("blocker_namespace") or "entry_submit")
    if stage in {"holding_started", "scale_in_executed"}:
        normalized.setdefault("metric_role", "execution_quality_real_only")
        normalized.setdefault("decision_authority", "broker_receipt_observation_only")
        normalized.setdefault("window_policy", "real_execution_event")
        normalized.setdefault("sample_floor", 1)
        normalized.setdefault("primary_decision_metric", "source_quality_gate")
        normalized.setdefault("source_quality_gate", "broker_receipt_observation_only")
        normalized.setdefault("runtime_effect", False)
        normalized.setdefault(
            "forbidden_uses",
            "runtime_threshold_apply/provider_route_change/bot_restart/sim_execution_quality_claim",
        )
        normalized.setdefault("actual_order_submitted", True)
        normalized.setdefault("broker_order_forbidden", False)
    if stage == "same_symbol_loss_reentry_cooldown":
        normalized.setdefault("metric_role", "safety_veto")
        normalized.setdefault("decision_authority", "same_symbol_loss_reentry_guard_observation_only")
        normalized.setdefault("window_policy", "same_symbol_guard_event")
        normalized.setdefault("sample_floor", 1)
        normalized.setdefault("primary_decision_metric", "source_quality_gate")
        normalized.setdefault("source_quality_gate", "same_symbol_loss_reentry_guard_observation_only")
        normalized.setdefault("runtime_effect", False)
        normalized.setdefault(
            "forbidden_uses",
            "runtime_threshold_apply/provider_route_change/bot_restart",
        )
        normalized.setdefault("actual_order_submitted", True)
        normalized.setdefault("broker_order_forbidden", False)
        normalized.setdefault("source_stage", "sell_order_sent")
        normalized.setdefault("guard_family", "same_symbol_loss_reentry_guard")
    if stage in HIGH_VOLUME_DIAGNOSTIC_STAGE_ROLES:
        normalized.setdefault("metric_role", HIGH_VOLUME_DIAGNOSTIC_STAGE_ROLES[stage])
        normalized.setdefault("decision_authority", "source_quality_only")
        normalized.setdefault("window_policy", "same_day_high_volume_diagnostic")
        normalized.setdefault("sample_floor", 1)
        normalized.setdefault("primary_decision_metric", "funnel_count")
        normalized.setdefault("source_quality_gate", "diagnostic_contract_label_present")
        normalized.setdefault("runtime_effect", False)
        normalized.setdefault(
            "forbidden_uses",
            "runtime_threshold_apply/order_submit/provider_route_change/bot_restart",
        )
    if stage == "loss_fallback_probe" and not _is_present(normalized.get("fallback_reason")):
        fallback_candidate = str(normalized.get("fallback_candidate") or "").strip().lower() in {"true", "1", "yes"}
        if not fallback_candidate:
            normalized["fallback_reason"] = normalized.get("gate_reason") or "not_candidate"
    if stage == "soft_stop_whipsaw_confirmation" and not _is_present(normalized.get("flow_state")):
        normalized["flow_state"] = "flow_state_unavailable"
        normalized["flow_state_source"] = "audit_normalized_missing_runtime_flow_state"
    elif _is_present(normalized.get("flow_state")):
        raw_flow_state = normalized.get("flow_state")
        if not is_known_flow_state_label(raw_flow_state):
            normalized["invalid_flow_state_label"] = raw_flow_state
            normalized["source_quality_blocker"] = "unknown_flow_state_label"
        normalized["flow_state"] = normalize_flow_state_label(raw_flow_state)
        if normalized["flow_state"] != raw_flow_state:
            normalized["raw_flow_state"] = raw_flow_state
            normalized["flow_state_source"] = "audit_normalized_legacy_runtime_flow_state"
    if "gatekeeper" in stage or any(
        _is_present(normalized.get(field)) for field in ("action_key", "gatekeeper_action_key", "gatekeeper_action")
    ):
        raw_action = normalized.get("action_key") or normalized.get("gatekeeper_action_key") or normalized.get(
            "gatekeeper_action"
        ) or normalized.get("action")
        if _is_present(raw_action):
            if not is_known_gatekeeper_action_label(raw_action):
                normalized["invalid_gatekeeper_action_label"] = raw_action
                normalized["source_quality_blocker"] = "unknown_gatekeeper_action_label"
            normalized["action_key"] = normalize_gatekeeper_action_key(raw_action)
    return normalized


def _stage_counts(rows: list[dict[str, Any]]) -> Counter[str]:
    return Counter(_stage_name(row) for row in rows)


def _contract_bool(value: Any, expected: bool) -> bool:
    normalized = str(value).strip().lower()
    if expected:
        return normalized in {"1", "true", "yes"}
    return normalized in {"", "0", "false", "none", "no"}


def _sim_submit_guard_contract_violations(stage: str, fields: dict[str, Any]) -> dict[str, bool]:
    action_contract = SIM_SUBMIT_GUARD_STAGE_ACTIONS.get(stage)
    if not action_contract:
        return {}
    action_field, expected_action = action_contract
    action_value = str(fields.get(action_field) or "").strip().upper()
    return {
        "sim_submit_guard_action_contract": action_value != expected_action,
        "sim_submit_guard_authority_contract": str(fields.get("decision_authority") or "").strip()
        != "sim_submit_path_observation_only",
        "sim_submit_guard_actual_order_contract": not _contract_bool(
            fields.get("actual_order_submitted"),
            False,
        ),
        "sim_submit_guard_broker_forbidden_contract": not _contract_bool(
            fields.get("broker_order_forbidden"),
            True,
        ),
        "sim_submit_guard_runtime_effect_contract": not _contract_bool(fields.get("runtime_effect"), False),
    }


def _row_ts(row: dict[str, Any]) -> str | None:
    for key in ("emitted_at", "timestamp", "created_at", "updated_at"):
        value = row.get(key)
        if _is_present(value):
            return str(value)
    return None


def _stage_time_bounds(stage_rows: list[dict[str, Any]]) -> dict[str, str | None]:
    values = sorted(value for row in stage_rows if (value := _row_ts(row)))
    return {
        "first_timestamp": values[0] if values else None,
        "last_timestamp": values[-1] if values else None,
    }


def _row_identity(row: dict[str, Any], *, line_no: int | None = None) -> dict[str, Any]:
    identity = {
        "line_no": line_no,
        "stage": _stage_name(row),
        "emitted_at": row.get("emitted_at"),
        "stock_code": row.get("stock_code"),
        "stock_name": row.get("stock_name"),
        "record_id": row.get("record_id"),
    }
    fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
    for key in ("sim_record_id", "source_probe_id", "source_record_id", "entry_adm_candidate_id"):
        if _is_present(fields.get(key)):
            identity[key] = fields.get(key)
    return identity


def _row_contract_violations(stage: str, row: dict[str, Any], contract: StageContract) -> dict[str, list[str]]:
    fields = _normalized_fields_for_contract(stage, row.get("fields") if isinstance(row.get("fields"), dict) else {})
    missing = [field for field in contract.required_fields if not _is_present(fields.get(field))]
    for field in _conditional_required_fields(stage, fields):
        if not _is_present(fields.get(field)) and field not in missing:
            missing.append(field)
    zero = [
        field
        for field in contract.zero_sensitive_fields
        if (value := _safe_float(fields.get(field))) is not None and abs(value) <= 1e-9
    ]
    invalid: list[str] = []
    if stage == "soft_stop_whipsaw_confirmation" and _is_present(fields.get("invalid_flow_state_label")):
        invalid.append("flow_state")
    if "gatekeeper" in stage and _is_present(fields.get("invalid_gatekeeper_action_label")):
        invalid.append("gatekeeper_action")
    if stage in SIM_SUBMIT_GUARD_STAGE_ACTIONS:
        invalid.extend(
            key
            for key, violated in _sim_submit_guard_contract_violations(stage, fields).items()
            if violated
        )
    return {
        "missing_fields": missing,
        "zero_fields": zero,
        "invalid_fields": invalid,
    }


def _conditional_required_fields(stage: str, fields: dict[str, Any]) -> tuple[str, ...]:
    if stage != "scalping_scanner_real_source_guard_block":
        return ()
    if fields.get("scanner_source_guard_first_seen_required") is True:
        return ("first_seen_flu_rate", "last_promoted_at")
    if str(fields.get("scanner_source_guard_context") or "") == "repeat_guard_with_provenance":
        return ("first_seen_flu_rate", "last_promoted_at")
    reason_candidates = (
        fields.get("scanner_real_source_guard_skip_reason"),
        fields.get("scanner_block_reason"),
        fields.get("scanner_filter_reason"),
    )
    if any(
        str(reason or "") == "value_top_only_repeat_deteriorating_without_strength"
        for reason in reason_candidates
    ):
        return ("first_seen_flu_rate", "last_promoted_at")
    return ()


def _hard_violation_fields_by_stage(contract_result: dict[str, Any]) -> dict[str, dict[str, set[str]]]:
    fields_by_stage: dict[str, dict[str, set[str]]] = {}
    for stage, result in (contract_result.get("stage_contracts") or {}).items():
        if not isinstance(result, dict) or result.get("status") not in {"warning", "fail"}:
            continue
        missing = set((result.get("missing_violations") or {}).keys())
        zero = set((result.get("zero_violations") or {}).keys())
        invalid = set((result.get("invalid_violations") or {}).keys())
        if missing or zero or invalid:
            fields_by_stage[str(stage)] = {
                "missing_fields": missing,
                "zero_fields": zero,
                "invalid_fields": invalid,
            }
    return fields_by_stage


def _hard_blocking_row_exclusions(
    rows: list[dict[str, Any]],
    contract_result: dict[str, Any],
) -> list[dict[str, Any]]:
    hard_fields_by_stage = _hard_violation_fields_by_stage(contract_result)
    exclusions: list[dict[str, Any]] = []
    for line_no, row in enumerate(rows, 1):
        stage = _stage_name(row)
        hard_fields = hard_fields_by_stage.get(stage)
        if not hard_fields:
            continue
        contract = STAGE_CONTRACTS.get(stage)
        if contract is None:
            continue
        violations = _row_contract_violations(stage, row, contract)
        violations = {
            key: [field for field in value if field in hard_fields.get(key, set())]
            for key, value in violations.items()
        }
        if not any(violations.values()):
            continue
        exclusions.append(
            {
                **_row_identity(row, line_no=line_no),
                **violations,
                "reason": "row_contract_gap",
                "exclusion_reasons": _raw_row_exclusion_reasons(row, violations, contract),
                "producer_hint": _producer_hint_for_row(row),
                "tuning_input_allowed": False,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
            }
        )
    return exclusions


def _value_text(value: Any) -> str:
    if isinstance(value, (dict, list, tuple, set)):
        try:
            return json.dumps(value, ensure_ascii=False, sort_keys=True)
        except Exception:
            return str(value)
    return str(value)


def _raw_row_exclusion_reasons(
    row: dict[str, Any],
    violations: dict[str, list[str]],
    contract: StageContract | None,
) -> list[str]:
    fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
    reasons: set[str] = set()
    if violations.get("missing_fields"):
        reasons.add("required_field_missing")
    if violations.get("invalid_fields"):
        reasons.add("invalid_label")
    if violations.get("zero_fields"):
        reasons.add("zero_context_sensitive")
    if contract is None:
        reasons.add("no_contract_stage")
    missing_source_fields = [
        field for field in violations.get("missing_fields", []) if _source_like_field(field)
    ]
    if missing_source_fields:
        reasons.add("provenance_missing")
    for key, value in fields.items():
        text = _value_text(value).lower()
        lowered_key = str(key).lower()
        if "source_quality_block" in text or lowered_key == "source_quality_blocker":
            reasons.add("source_quality_blocker")
        if "not_evaluated" in text:
            reasons.add("not_evaluated_context")
        if "insufficient_history" in text or "insufficient_sample" in text:
            reasons.add("insufficient_history")
        if _unknown_token_present(value):
            reasons.add("unknown_token")
    return sorted(reasons) or ["row_contract_gap"]


def _producer_hint_for_row(row: dict[str, Any]) -> dict[str, Any]:
    stage = _stage_name(row)
    pipeline = str(row.get("pipeline") or "")
    fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
    stage_lower = stage.lower()
    if stage_lower.startswith("swing") or "swing" in pipeline.lower():
        subsystem = "swing_runtime_or_sim_producer"
    elif stage_lower.startswith("scalp") or "entry" in pipeline.lower():
        subsystem = "scalping_entry_or_sim_producer"
    elif "holding" in stage_lower or "exit" in stage_lower:
        subsystem = "holding_exit_runtime_producer"
    else:
        subsystem = "runtime_instrumentation_producer"
    return {
        "stage": stage,
        "pipeline": pipeline or None,
        "subsystem": subsystem,
        "threshold_family": fields.get("threshold_family"),
        "source_stage": fields.get("source_stage"),
    }


def _summarize_raw_row_exclusions(
    excluded_payloads: list[dict[str, Any]],
    exclusions_by_line: dict[int, dict[str, Any]],
    *,
    target_date: str,
) -> dict[str, Any]:
    stage_counts: Counter[str] = Counter()
    field_gap_counts: Counter[str] = Counter()
    reason_counts: Counter[str] = Counter()
    producer_hints: dict[str, dict[str, Any]] = {}
    timestamps: list[str] = []
    sample_rows: list[dict[str, Any]] = []
    for item in excluded_payloads:
        line_no = int(item.get("line_no") or 0)
        payload = item.get("payload") if isinstance(item.get("payload"), dict) else {}
        exclusion = exclusions_by_line.get(line_no, {})
        stage = str(payload.get("stage") or exclusion.get("stage") or "-")
        fields = payload.get("fields") if isinstance(payload.get("fields"), dict) else {}
        stage_counts[stage] += 1
        if timestamp := _row_ts(payload):
            timestamps.append(timestamp)
        reasons = exclusion.get("exclusion_reasons")
        if not isinstance(reasons, list) or not reasons:
            reasons = _raw_row_exclusion_reasons(payload, exclusion, STAGE_CONTRACTS.get(stage))
        for reason in reasons:
            reason_counts[str(reason)] += 1
        for category in ("missing_fields", "zero_fields", "invalid_fields"):
            for field in exclusion.get(category) or []:
                field_gap_counts[f"{category}:{field}"] += 1
        if stage not in producer_hints:
            producer_hints[stage] = {
                **_producer_hint_for_row(payload),
                "count": 0,
                "top_reasons": [],
            }
        producer_hints[stage]["count"] += 1
        if len(sample_rows) < 10:
            sample_rows.append(
                {
                    "line_no": line_no,
                    "stage": stage,
                    "emitted_at": payload.get("emitted_at"),
                    "record_id": payload.get("record_id"),
                    "stock_code": payload.get("stock_code"),
                    "reasons": reasons,
                    "gap_fields": {
                        key: list(exclusion.get(key) or [])
                        for key in ("missing_fields", "zero_fields", "invalid_fields")
                        if exclusion.get(key)
                    },
                    "source_quality_route": fields.get("source_quality_route"),
                    "source_quality_blocker": fields.get("source_quality_blocker"),
                    "threshold_family": fields.get("threshold_family"),
                }
            )
    stage_reason_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for item in excluded_payloads:
        line_no = int(item.get("line_no") or 0)
        payload = item.get("payload") if isinstance(item.get("payload"), dict) else {}
        stage = str(payload.get("stage") or "-")
        exclusion = exclusions_by_line.get(line_no, {})
        for reason in exclusion.get("exclusion_reasons") or []:
            stage_reason_counts[stage][str(reason)] += 1
    for stage, hint in producer_hints.items():
        hint["top_reasons"] = [
            reason for reason, _ in stage_reason_counts.get(stage, Counter()).most_common(5)
        ]
    halt_context = _market_halt_context_for_exclusion_timestamps(target_date, timestamps)
    return {
        "stage_counts": dict(sorted(stage_counts.items())),
        "field_gap_counts": dict(sorted(field_gap_counts.items())),
        "exclusion_reasons": dict(sorted(reason_counts.items())),
        "first_timestamp": min(timestamps) if timestamps else None,
        "last_timestamp": max(timestamps) if timestamps else None,
        **halt_context,
        "sample_rows": sample_rows,
        "producer_hint": sorted(producer_hints.values(), key=lambda item: (-int(item.get("count") or 0), str(item.get("stage") or ""))),
    }


def _market_halt_context_for_exclusion_timestamps(
    target_date: str,
    timestamps: list[str],
) -> dict[str, Any]:
    windows = load_market_halt_windows(target_date, data_dir=DATA_DIR)
    if not windows or not timestamps:
        return {
            "market_halt_or_circuit_window_overlap": False,
            "market_halt_or_circuit_context": None,
        }
    ts_values = sorted(str(ts) for ts in timestamps if ts)
    if not ts_values:
        return {
            "market_halt_or_circuit_window_overlap": False,
            "market_halt_or_circuit_context": None,
        }
    contexts: list[dict[str, Any]] = []
    for window in windows:
        start = str(window.get("halt_started_at") or "")
        end = str(window.get("normal_flow_check_after") or window.get("single_price_order_acceptance_until") or "")
        if not start or not end:
            continue
        overlap_count = sum(1 for ts in ts_values if start <= ts < end)
        after_normal_count = sum(1 for ts in ts_values if ts >= end)
        contexts.append(
            {
                **window,
                "excluded_row_count": len(ts_values),
                "overlap_excluded_row_count": overlap_count,
                "after_normal_flow_excluded_row_count": after_normal_count,
                "overlap_ratio": round(overlap_count / len(ts_values), 6),
                "first_excluded_timestamp": ts_values[0],
                "last_excluded_timestamp": ts_values[-1],
                "classification": (
                    "market_halt_or_circuit_window_overlap"
                    if overlap_count >= max(1, int(len(ts_values) * 0.8))
                    else "no_material_market_halt_overlap"
                ),
                "runtime_effect": False,
                "allowed_runtime_apply": False,
            }
        )
    active_contexts = [
        context
        for context in contexts
        if context.get("classification") == "market_halt_or_circuit_window_overlap"
    ]
    return {
        "market_halt_or_circuit_window_overlap": bool(active_contexts),
        "market_halt_or_circuit_context": active_contexts[0] if active_contexts else None,
    }


def _evaluate_contracts(rows: list[dict[str, Any]], stage_counts: Counter[str]) -> dict[str, Any]:
    by_stage: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_stage[_stage_name(row)].append(row)

    results: dict[str, Any] = {}
    warnings: list[str] = []
    for stage, contract in STAGE_CONTRACTS.items():
        stage_rows = by_stage.get(stage, [])
        total = len(stage_rows)
        if total < contract.min_sample:
            results[stage] = {
                "sample_count": total,
                "status": "sample_below_floor",
                **_stage_time_bounds(stage_rows),
                "required_fields": list(contract.required_fields),
                "metric_role": "source_quality_gate",
                "decision_authority": contract.decision_authority,
                "runtime_effect": False,
                "forbidden_uses": contract.forbidden_uses,
            }
            continue

        missing_counts: dict[str, int] = {}
        zero_counts: dict[str, int] = {}
        invalid_label_counts: dict[str, int] = {}
        for field in contract.required_fields:
            missing_counts[field] = sum(
                1
                for row in stage_rows
                if not _is_present(_normalized_fields_for_contract(stage, row["fields"]).get(field))
            )
        conditional_fields = sorted({
            field
            for row in stage_rows
            for field in _conditional_required_fields(
                stage,
                _normalized_fields_for_contract(stage, row["fields"]),
            )
        })
        for field in conditional_fields:
            missing_counts[field] = sum(
                1
                for row in stage_rows
                if field
                in _conditional_required_fields(
                    stage,
                    _normalized_fields_for_contract(stage, row["fields"]),
                )
                and not _is_present(_normalized_fields_for_contract(stage, row["fields"]).get(field))
            )
        if stage == "soft_stop_whipsaw_confirmation":
            invalid_label_counts["flow_state"] = sum(
                1
                for row in stage_rows
                if _is_present(
                    _normalized_fields_for_contract(stage, row["fields"]).get("invalid_flow_state_label")
                )
            )
        if "gatekeeper" in stage:
            invalid_label_counts["action"] = sum(
                1
                for row in stage_rows
                if _is_present(
                    _normalized_fields_for_contract(stage, row["fields"]).get("invalid_gatekeeper_action_label")
                )
            )
        if stage in SIM_SUBMIT_GUARD_STAGE_ACTIONS:
            for violation_key in (
                "sim_submit_guard_action_contract",
                "sim_submit_guard_authority_contract",
                "sim_submit_guard_actual_order_contract",
                "sim_submit_guard_broker_forbidden_contract",
                "sim_submit_guard_runtime_effect_contract",
            ):
                invalid_label_counts[violation_key] = sum(
                    1
                    for row in stage_rows
                    if _sim_submit_guard_contract_violations(
                        stage,
                        _normalized_fields_for_contract(stage, row["fields"]),
                    ).get(violation_key)
                )
        for field in contract.zero_sensitive_fields:
            zero_counts[field] = sum(
                1
                for row in stage_rows
                if (value := _safe_float(_normalized_fields_for_contract(stage, row["fields"]).get(field)))
                is not None
                and abs(value) <= 1e-9
            )

        missing_rates = {field: round(count / total, 4) for field, count in missing_counts.items()}
        zero_rates = {field: round(count / total, 4) for field, count in zero_counts.items()}
        invalid_label_rates = {field: round(count / total, 4) for field, count in invalid_label_counts.items()}
        missing_violations = {
            field: rate for field, rate in missing_rates.items() if rate > contract.max_missing_rate
        }
        zero_violations = {field: rate for field, rate in zero_rates.items() if rate > contract.max_zero_rate}
        invalid_label_violations = {field: rate for field, rate in invalid_label_rates.items() if rate > 0}
        status = (
            "fail"
            if invalid_label_violations
            else ("pass" if not missing_violations and not zero_violations else "warning")
        )
        if status == "warning":
            warnings.append(stage)
        if status == "fail":
            warnings.append(stage)
        results[stage] = {
            "sample_count": total,
            "status": status,
            **_stage_time_bounds(stage_rows),
            "required_fields": list(contract.required_fields),
            "conditional_required_fields": conditional_fields,
            "missing_counts": missing_counts,
            "missing_rates": missing_rates,
            "zero_sensitive_fields": list(contract.zero_sensitive_fields),
            "zero_counts": zero_counts,
            "zero_rates": zero_rates,
            "invalid_label_counts": invalid_label_counts,
            "invalid_label_rates": invalid_label_rates,
            "missing_violations": missing_violations,
            "zero_violations": zero_violations,
            "invalid_label_violations": invalid_label_violations,
            "metric_role": "source_quality_gate",
            "decision_authority": contract.decision_authority,
            "runtime_effect": False,
            "forbidden_uses": contract.forbidden_uses,
        }

    high_volume_no_source_fields: list[dict[str, Any]] = []
    unknown_token_findings: list[dict[str, Any]] = []
    numeric_consistency_findings: list[dict[str, Any]] = []
    invalid_label_findings: dict[str, dict[str, Any]] = {}
    field_presence: dict[str, Counter[str]] = defaultdict(Counter)
    unknown_counts: dict[str, Counter[str]] = defaultdict(Counter)
    reviewed_unknown_counts: dict[str, Counter[str]] = defaultdict(Counter)
    unknown_examples: dict[tuple[str, str], list[str]] = defaultdict(list)
    reviewed_unknown_examples: dict[tuple[str, str], list[str]] = defaultdict(list)
    numeric_consistency_by_stage: dict[str, list[dict[str, Any]]] = defaultdict(list)
    example_keys: dict[str, list[str]] = {}
    for row in rows:
        stage = _stage_name(row)
        fields = row["fields"]
        normalized = _normalized_fields_for_contract(stage, fields)
        if _is_present(normalized.get("invalid_flow_state_label")):
            key = f"{stage}:flow_state"
            finding = invalid_label_findings.setdefault(
                key,
                {
                    "stage": stage,
                    "field": "flow_state",
                    "count": 0,
                    "examples": [],
                    "routing": "source_quality_blocker",
                },
            )
            finding["count"] += 1
            if len(finding["examples"]) < 5:
                finding["examples"].append(str(normalized.get("invalid_flow_state_label")))
        if _is_present(normalized.get("invalid_gatekeeper_action_label")):
            key = f"{stage}:gatekeeper_action"
            finding = invalid_label_findings.setdefault(
                key,
                {
                    "stage": stage,
                    "field": "gatekeeper_action",
                    "count": 0,
                    "examples": [],
                    "routing": "source_quality_blocker",
                },
            )
            finding["count"] += 1
            if len(finding["examples"]) < 5:
                finding["examples"].append(str(normalized.get("invalid_gatekeeper_action_label")))
        if normalized.get("ai_reason_numeric_inconsistency") is True:
            numeric_consistency_by_stage[stage].append(
                {
                    "field": str(normalized.get("ai_reason_numeric_inconsistency_field") or "tick_acceleration_ratio"),
                    "reason": str(normalized.get("ai_reason_numeric_inconsistency_reason") or "-"),
                    "excerpt": str(normalized.get("ai_reason_numeric_inconsistency_excerpt") or "")[:240],
                    "detected_value": normalized.get("ai_reason_numeric_inconsistency_detected_value"),
                }
            )
        example_keys.setdefault(stage, list(fields.keys())[:30])
        for key, value in normalized.items():
            if _source_like_field(key) and _is_present(value):
                field_presence[stage][key] += 1
        for key, value in _unknown_scan_values(row, normalized).items():
            if _unknown_token_present(value):
                reviewed_reason = _reviewed_unknown_reason_for_field(
                    key,
                    value,
                    emitted_date=str(row.get("emitted_date") or row.get("date") or ""),
                )
                if not reviewed_reason:
                    reviewed_reason = _reviewed_unknown_reason_for_stage_field(stage, key, value, normalized)
                if (
                    not reviewed_reason
                    and stage == "scalp_sim_panic_context_warning"
                    and str(key)
                    in {"panic_epoch_id", "market_risk_state", "liquidity_state", "risk_regime_epoch_id"}
                ):
                    reviewed_reason = "reviewed_missing_risk_regime_context"
                if reviewed_reason:
                    reviewed_key = f"{key}:{reviewed_reason}"
                    reviewed_unknown_counts[stage][reviewed_key] += 1
                    examples = reviewed_unknown_examples[(stage, reviewed_key)]
                    if len(examples) < 5:
                        examples.append(str(value)[:240])
                    continue
                unknown_counts[stage][key] += 1
                examples = unknown_examples[(stage, key)]
                if len(examples) < 5:
                    examples.append(str(value)[:240])
    for stage, count in stage_counts.most_common():
        if count < 50 or field_presence.get(stage) or stage in STAGE_CONTRACTS:
            continue
        stage_rows = by_stage.get(stage, [])
        high_volume_no_source_fields.append(
            {
                "stage": stage,
                "event_count": count,
                **_stage_time_bounds(stage_rows),
                "example_fields": example_keys.get(stage, []),
                "routing": "instrumentation_gap_or_diagnostic_contract_needed",
            }
        )
    for stage, counter in sorted(unknown_counts.items(), key=lambda item: (-stage_counts[item[0]], item[0])):
        total = max(1, stage_counts.get(stage, 0))
        warning_fields = []
        for field, count in counter.most_common():
            rate = round(count / total, 4)
            warning_fields.append(
                {
                    "field": field,
                    "count": count,
                    "rate": rate,
                    "examples": unknown_examples.get((stage, field), []),
                }
            )
        if not warning_fields:
            continue
        unknown_token_findings.append(
            {
                "stage": stage,
                "event_count": stage_counts.get(stage, 0),
                "fields": warning_fields,
                "routing": "source_quality_blocker_or_provenance_backfill",
                "decision_authority": "source_quality_only",
                "runtime_effect": False,
                "forbidden_uses": "runtime_threshold_apply/order_submit/provider_route_change/bot_restart",
            }
        )
    reviewed_unknown_token_findings: list[dict[str, Any]] = []
    for stage, counter in sorted(reviewed_unknown_counts.items(), key=lambda item: (-stage_counts[item[0]], item[0])):
        total = max(1, stage_counts.get(stage, 0))
        fields = []
        for compound_key, count in counter.most_common():
            field, _, reason = compound_key.partition(":")
            fields.append(
                {
                    "field": field,
                    "count": count,
                    "rate": round(count / total, 4),
                    "reviewed_reason": reason or "reviewed_unknown",
                    "examples": reviewed_unknown_examples.get((stage, compound_key), []),
                }
            )
        if fields:
            reviewed_unknown_token_findings.append(
                {
                    "stage": stage,
                    "event_count": stage_counts.get(stage, 0),
                    "fields": fields,
                    "routing": "reviewed_unknown_token_provenance",
                    "decision_authority": "source_quality_only",
                    "runtime_effect": False,
                    "forbidden_uses": "runtime_threshold_apply/order_submit/provider_route_change/bot_restart",
                }
            )
    for stage, rows_with_issue in sorted(numeric_consistency_by_stage.items(), key=lambda item: (-stage_counts[item[0]], item[0])):
        if not rows_with_issue:
            continue
        numeric_consistency_findings.append(
            {
                "stage": stage,
                "event_count": stage_counts.get(stage, 0),
                "finding_count": len(rows_with_issue),
                "rate": round(len(rows_with_issue) / max(1, stage_counts.get(stage, 0)), 4),
                "routing": "source_quality_review_numeric_consistency",
                "decision_authority": "source_quality_only",
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "forbidden_uses": "EV/live-auto/runtime-apply/threshold mutation/order guard mutation/provider_route_change/bot_restart",
                "examples": rows_with_issue[:5],
            }
        )
    return {
        "stage_contracts": results,
        "warning_stages": warnings,
        "invalid_label_findings": list(invalid_label_findings.values()),
        "high_volume_no_source_fields": high_volume_no_source_fields,
        "unknown_token_findings": unknown_token_findings,
        "reviewed_unknown_token_findings": reviewed_unknown_token_findings,
        "numeric_consistency_findings": numeric_consistency_findings,
        "field_presence_top": {
            stage: dict(counter.most_common(20))
            for stage, counter in sorted(field_presence.items(), key=lambda item: (-stage_counts[item[0]], item[0]))
        },
    }


def _hard_gate_summary(contract_result: dict[str, Any]) -> dict[str, Any]:
    gaps: list[dict[str, Any]] = []
    stage_contracts = (
        contract_result.get("stage_contracts") if isinstance(contract_result.get("stage_contracts"), dict) else {}
    )
    for stage, result in stage_contracts.items():
        if not isinstance(result, dict) or result.get("status") not in {"warning", "fail"}:
            continue
        missing = result.get("missing_violations") if isinstance(result.get("missing_violations"), dict) else {}
        zeros = result.get("zero_violations") if isinstance(result.get("zero_violations"), dict) else {}
        invalid = (
            result.get("invalid_label_violations")
            if isinstance(result.get("invalid_label_violations"), dict)
            else {}
        )
        if not (missing or zeros or invalid):
            continue
        gaps.append(
            {
                "stage": stage,
                "reason": "stage_contract_status_warning_or_fail",
                "status": result.get("status"),
                "sample_count": result.get("sample_count"),
                "first_timestamp": result.get("first_timestamp"),
                "last_timestamp": result.get("last_timestamp"),
                "missing_fields": list(missing),
                "missing_violations": missing,
                "zero_violations": zeros,
                "invalid_label_violations": invalid,
                "forbidden_uses": result.get("forbidden_uses"),
                "runtime_effect": False,
                "allowed_runtime_apply": False,
            }
        )
    for item in contract_result.get("invalid_label_findings") or []:
        if not isinstance(item, dict):
            continue
        gaps.append(
            {
                "stage": item.get("stage"),
                "reason": "invalid_label_violation",
                "field": item.get("field"),
                "sample_count": item.get("count"),
                "first_timestamp": item.get("first_timestamp"),
                "last_timestamp": item.get("last_timestamp"),
                "forbidden_uses": "EV/rolling/MTD/cumulative tuning/live-auto promotion/runtime approval until fixed",
                "runtime_effect": False,
                "allowed_runtime_apply": False,
            }
        )
    for item in contract_result.get("high_volume_no_source_fields") or []:
        if not isinstance(item, dict):
            continue
        gaps.append(
            {
                "stage": item.get("stage"),
                "reason": "high_volume_no_source_contract_gap",
                "sample_count": item.get("event_count"),
                "first_timestamp": item.get("first_timestamp"),
                "last_timestamp": item.get("last_timestamp"),
                "missing_fields": ["metric_role", "decision_authority", "source_quality_gate"],
                "forbidden_uses": "EV/rolling/MTD/cumulative tuning/live-auto promotion/runtime approval until fixed",
                "runtime_effect": False,
                "allowed_runtime_apply": False,
            }
        )
    hard_stages = sorted({str(item.get("stage")) for item in gaps if item.get("stage")})
    return {
        "hard_blocking_contract_gap_count": len(gaps),
        "hard_blocking_stages": hard_stages,
        "hard_blocking_contract_gaps": gaps,
        "tuning_input_allowed": not gaps,
        "blocked_reason": "blocked_contract_gap" if gaps else None,
        "review_warning_count": len(contract_result.get("unknown_token_findings") or []) + len(contract_result.get("numeric_consistency_findings") or []),
        "reviewed_unknown_token_stage_count": len(contract_result.get("reviewed_unknown_token_findings") or []),
        "review_warning_stages": [
            item.get("stage")
            for item in contract_result.get("unknown_token_findings") or []
            if isinstance(item, dict) and item.get("stage")
        ] + [
            item.get("stage")
            for item in contract_result.get("numeric_consistency_findings") or []
            if isinstance(item, dict) and item.get("stage")
        ],
    }


def build_observation_source_quality_audit(target_date: str) -> dict[str, Any]:
    raw_path = existing_or_gzip_path(_pipeline_events_path(target_date))
    rows = _iter_events(raw_path)
    stage_counts = _stage_counts(rows)
    contract_result = _evaluate_contracts(rows, stage_counts)
    hard_gate = _hard_gate_summary(contract_result)
    row_exclusions = _hard_blocking_row_exclusions(rows, contract_result)
    status = (
        "fail"
        if any((item.get("status") == "fail") for item in contract_result["stage_contracts"].values())
        or contract_result["invalid_label_findings"]
        else
        "warning"
        if (
            contract_result["warning_stages"]
            or contract_result["high_volume_no_source_fields"]
            or contract_result["unknown_token_findings"]
            or contract_result.get("numeric_consistency_findings")
        )
        else "pass"
    )
    return {
        "report_type": REPORT_DIRNAME,
        "target_date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": status,
        "policy": {
            "metric_role": "source_quality_gate",
            "decision_authority": "source_quality_only",
            "runtime_effect": False,
            "window_policy": "daily_intraday_or_postclose_diagnostic",
            "primary_decision_metric": "contract_field_presence_and_zero_rate",
            "forbidden_uses": [
                "runtime_threshold_apply",
                "order_submit",
                "provider_route_change",
                "bot_restart",
                "real_execution_quality_approval",
            ],
        },
        "source": {"pipeline_events": str(raw_path), "exists": raw_path.exists()},
        "summary": {
            "event_count": len(rows),
            "stage_count": len(stage_counts),
            "top_stages": dict(stage_counts.most_common(20)),
            "warning_stage_count": len(contract_result["warning_stages"]),
            "high_volume_no_source_field_stage_count": len(contract_result["high_volume_no_source_fields"]),
            "unknown_token_stage_count": len(contract_result["unknown_token_findings"]),
            "numeric_consistency_stage_count": len(contract_result.get("numeric_consistency_findings") or []),
            "reviewed_unknown_token_stage_count": len(contract_result.get("reviewed_unknown_token_findings") or []),
            "hard_blocking_excluded_row_count": len(row_exclusions),
            "tuning_input_policy": "exclude_defective_rows_not_full_day_raw",
            **{key: value for key, value in hard_gate.items() if key != "hard_blocking_contract_gaps"},
        },
        "hard_blocking_contract_gaps": hard_gate["hard_blocking_contract_gaps"],
        "hard_blocking_row_exclusions": row_exclusions,
        **contract_result,
    }


def _quarantine_scope(entry_unknown: int, overbought_unknown: int, ldm_unknown: int) -> list[str]:
    scope: list[str] = []
    if entry_unknown:
        scope.append("entry_adm_bucket_dimensions")
    if ldm_unknown:
        scope.append("ldm_bucket_attribution")
    if overbought_unknown:
        scope.append("sim_overbought_context_provenance")
    return scope


def _existing_derived_reports(target_date: str) -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    for report_type, stem in STALE_DERIVED_REPORTS:
        for suffix in ("json", "md"):
            path = DATA_DIR / "report" / report_type / f"{stem}_{target_date}.{suffix}"
            if path.exists():
                reports.append(
                    {
                        "report_type": report_type,
                        "path": str(path),
                        "action": "regenerate_after_source_quality_patch",
                    }
                )
    return reports


def _source_backfill_counts(path: Path) -> Counter[str]:
    counts = Counter()
    resolved = existing_or_gzip_path(path)
    if not resolved.exists():
        return counts
    process = None
    if resolved.suffix == ".gz":
        try:
            process = subprocess.Popen(
                ["zgrep", "-iE", BACKFILL_PREFILTER_PATTERN, str(resolved)],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        except FileNotFoundError:
            opener = gzip.open
            stream_context = opener(resolved, "rt", encoding="utf-8")
            close_stream = True
        else:
            stream_context = process.stdout
            close_stream = False
    else:
        close_stream = False
        try:
            process = subprocess.Popen(
                ["rg", "-i", "--no-filename", BACKFILL_PREFILTER_PATTERN, str(resolved)],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        except FileNotFoundError:
            stream_context = open(resolved, "rt", encoding="utf-8")
            close_stream = True
        else:
            stream_context = process.stdout
    if stream_context is None:
        return counts
    try:
        for line in stream_context:
            lowered = line.lower()
            has_sim = "sim" in lowered or "actual_order_submitted" in lowered
            has_entry_adm = "scalp_entry_action_decision_snapshot" in lowered or "entry_adm_" in lowered
            has_holding = "ai_holding_review" in lowered or "holding" in lowered
            has_ldm = "lifecycle_matrix_" in lowered
            has_overbought = (
                "scalp_sim_pre_submit_overbought" in lowered
                or "sim_pre_submit_overbought" in lowered
                or "sim_overbought_" in lowered
            )
            if not (has_sim or has_entry_adm or has_holding or has_ldm or has_overbought):
                continue
            counts["event_rows"] += 1
            counts["parsed_candidate_rows"] += 1
            has_unknown = "unknown" in lowered
            if has_sim:
                counts["sim_rows"] += 1
            if "assumed_filled" in lowered or "virtual_fill" in lowered:
                counts["sim_filled_rows"] += 1
            if has_entry_adm:
                counts["entry_adm_snapshot_rows"] += 1
                if has_unknown:
                    counts["entry_adm_unknown_rows"] += 1
            if has_holding:
                counts["holding_review_rows"] += 1
            if has_ldm:
                counts["ldm_rows"] += 1
                if has_unknown:
                    counts["ldm_unknown_rows"] += 1
            if has_overbought:
                counts["sim_overbought_context_rows"] += 1
                if has_unknown:
                    counts["sim_overbought_unknown_rows"] += 1
    finally:
        if close_stream:
            stream_context.close()
        elif process is not None:
            process.wait()
    return counts


def _build_backfill_date_row(target_date: str) -> dict[str, Any]:
    source_counts: dict[str, Counter[str]] = defaultdict(Counter)
    totals = Counter()
    for source, path in (
        ("pipeline_events", _pipeline_events_path(target_date)),
        ("threshold_cycle_events", _threshold_events_path(target_date)),
    ):
        counts = _source_backfill_counts(path)
        source_counts[source].update(counts)
        totals.update(counts)

    entry_unknown = totals["entry_adm_unknown_rows"]
    overbought_unknown = totals["sim_overbought_unknown_rows"]
    ldm_unknown = totals["ldm_unknown_rows"]
    quarantine_scope = _quarantine_scope(entry_unknown, overbought_unknown, ldm_unknown)
    stale_reports = _existing_derived_reports(target_date) if quarantine_scope else []
    return {
        "date": target_date,
        "event_rows": totals["event_rows"],
        "parsed_candidate_rows": totals["parsed_candidate_rows"],
        "sim_rows": totals["sim_rows"],
        "sim_filled_rows": totals["sim_filled_rows"],
        "entry_adm_snapshot_rows": totals["entry_adm_snapshot_rows"],
        "entry_adm_unknown_rows": entry_unknown,
        "holding_review_rows": totals["holding_review_rows"],
        "ldm_rows": totals["ldm_rows"],
        "ldm_unknown_rows": ldm_unknown,
        "sim_overbought_context_rows": totals["sim_overbought_context_rows"],
        "sim_overbought_unknown_rows": overbought_unknown,
        "raw_sim_preserved": totals["sim_rows"] > 0,
        "bucket_interpretation_quarantined": bool(quarantine_scope),
        "quarantine_scope": quarantine_scope,
        "stale_derived_reports": stale_reports,
        "recommended_action": (
            "regenerate_derived_reports_with_source_quality_gate" if quarantine_scope else "none"
        ),
        "source_counts": {source: dict(counter) for source, counter in source_counts.items()},
    }


def _first_affected_date(rows: list[dict[str, Any]], key: str) -> str | None:
    for row in rows:
        if int(row.get(key) or 0) > 0:
            return str(row.get("date"))
    return None


def build_observation_source_quality_backfill_audit(
    target_date: str,
    start_date: str = DEFAULT_BACKFILL_START_DATE,
) -> dict[str, Any]:
    date_rows = [_build_backfill_date_row(day) for day in _date_range(start_date, target_date)]
    affected_rows = [row for row in date_rows if row["bucket_interpretation_quarantined"]]
    summary = {
        "date_count": len(date_rows),
        "affected_date_count": len(affected_rows),
        "first_entry_adm_unknown_date": _first_affected_date(date_rows, "entry_adm_unknown_rows"),
        "first_sim_overbought_unknown_date": _first_affected_date(date_rows, "sim_overbought_unknown_rows"),
        "first_ldm_unknown_date": _first_affected_date(date_rows, "ldm_unknown_rows"),
        "raw_sim_total": sum(int(row["sim_rows"]) for row in date_rows),
        "sim_filled_total": sum(int(row["sim_filled_rows"]) for row in date_rows),
        "entry_adm_unknown_total": sum(int(row["entry_adm_unknown_rows"]) for row in date_rows),
        "sim_overbought_unknown_total": sum(int(row["sim_overbought_unknown_rows"]) for row in date_rows),
        "ldm_unknown_total": sum(int(row["ldm_unknown_rows"]) for row in date_rows),
        "stale_derived_report_count": sum(len(row["stale_derived_reports"]) for row in date_rows),
        "decision": "quarantine_derived_bucket_interpretation" if affected_rows else "pass_no_quarantine",
        "operator_action_required": False,
    }
    return {
        "report_type": BACKFILL_REPORT_STEM,
        "target_date": target_date,
        "start_date": start_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": "warning" if affected_rows else "pass",
        "policy": {
            "metric_role": "source_quality_gate",
            "decision_authority": "source_quality_only",
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "window_policy": "historical_backfill_source_quality_audit",
            "primary_decision_metric": "unknown_bucket_provenance_quarantine",
            "forbidden_uses": [
                "runtime_threshold_apply",
                "order_submit",
                "provider_route_change",
                "bot_restart",
                "real_execution_quality_approval",
                "manual_threshold_promotion",
            ],
        },
        "summary": summary,
        "date_impacts": date_rows,
    }


def _write_backfill_markdown(report: dict[str, Any], path: Path) -> None:
    summary = report.get("summary", {})
    lines = [
        f"# Observation Source Quality Backfill Audit - {report.get('target_date')}",
        "",
        f"- status: `{report.get('status')}`",
        f"- start_date: `{report.get('start_date')}`",
        f"- affected_date_count: `{summary.get('affected_date_count')}`",
        f"- decision: `{summary.get('decision')}`",
        f"- operator_action_required: `{summary.get('operator_action_required')}`",
        f"- runtime_effect: `{report.get('policy', {}).get('runtime_effect')}`",
        "",
        "## Contract",
        "",
        "- Raw SIM rows and fill/outcome labels are preserved.",
        "- Entry ADM, LDM, and SIM overbought derived bucket interpretations are quarantined when unknown provenance is present.",
        "- Affected derived reports must be regenerated after the source-quality patch before promotion or tuning evidence reuse.",
        "",
        "## Summary",
        "",
        f"- first_entry_adm_unknown_date: `{summary.get('first_entry_adm_unknown_date')}`",
        f"- first_ldm_unknown_date: `{summary.get('first_ldm_unknown_date')}`",
        f"- first_sim_overbought_unknown_date: `{summary.get('first_sim_overbought_unknown_date')}`",
        f"- raw_sim_total: `{summary.get('raw_sim_total')}`",
        f"- sim_filled_total: `{summary.get('sim_filled_total')}`",
        f"- stale_derived_report_count: `{summary.get('stale_derived_report_count')}`",
        "",
        "## Date Impact",
        "",
        "| date | sim | filled | entry_unknown | ldm_unknown | overbought_unknown | quarantine | action |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for row in report.get("date_impacts", []):
        if not row.get("event_rows") and not row.get("bucket_interpretation_quarantined"):
            continue
        scope = ",".join(row.get("quarantine_scope") or [])
        lines.append(
            "| {date} | {sim} | {filled} | {entry} | {ldm} | {overbought} | {scope} | {action} |".format(
                date=row.get("date"),
                sim=row.get("sim_rows"),
                filled=row.get("sim_filled_rows"),
                entry=row.get("entry_adm_unknown_rows"),
                ldm=row.get("ldm_unknown_rows"),
                overbought=row.get("sim_overbought_unknown_rows"),
                scope=scope or "-",
                action=row.get("recommended_action"),
            )
        )
    lines.extend(["", "## Stale Derived Reports"])
    stale_count = 0
    for row in report.get("date_impacts", []):
        for item in row.get("stale_derived_reports", []):
            stale_count += 1
            lines.append(
                f"- `{row.get('date')}` `{item.get('report_type')}` action=`{item.get('action')}` path=`{item.get('path')}`"
            )
    if not stale_count:
        lines.append("- none")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_backfill_report(
    target_date: str,
    start_date: str = DEFAULT_BACKFILL_START_DATE,
) -> dict[str, Any]:
    report = build_observation_source_quality_backfill_audit(target_date, start_date=start_date)
    json_path, md_path = backfill_report_paths(target_date)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_backfill_markdown(report, md_path)
    return report


def _write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        f"# Observation Source Quality Audit - {report.get('target_date')}",
        "",
        f"- status: `{report.get('status')}`",
        f"- event_count: `{report.get('summary', {}).get('event_count')}`",
        f"- tuning_input_policy: `{report.get('summary', {}).get('tuning_input_policy')}`",
        f"- hard_blocking_excluded_row_count: `{report.get('summary', {}).get('hard_blocking_excluded_row_count')}`",
        f"- tuning_input_allowed: `{report.get('summary', {}).get('tuning_input_allowed')}`",
        f"- decision_authority: `{report.get('policy', {}).get('decision_authority')}`",
        f"- runtime_effect: `{report.get('policy', {}).get('runtime_effect')}`",
        f"- forbidden_uses: `{', '.join(report.get('policy', {}).get('forbidden_uses', []))}`",
        "",
        "## Warning Stages",
    ]
    warnings = report.get("warning_stages") or []
    if warnings:
        for stage in warnings:
            detail = report.get("stage_contracts", {}).get(stage, {})
            lines.append(
                f"- `{stage}` sample=`{detail.get('sample_count')}` missing=`{detail.get('missing_violations')}` zero=`{detail.get('zero_violations')}`"
            )
    else:
        lines.append("- none")
    lines.extend(["", "## Hard Blocking Row Exclusions"])
    row_exclusions = report.get("hard_blocking_row_exclusions") or []
    if row_exclusions:
        for item in row_exclusions[:50]:
            lines.append(
                f"- line=`{item.get('line_no')}` stage=`{item.get('stage')}` code=`{item.get('stock_code')}` "
                f"missing=`{item.get('missing_fields')}` zero=`{item.get('zero_fields')}` invalid=`{item.get('invalid_fields')}`"
            )
    else:
        lines.append("- none")
    lines.extend(["", "## Invalid Label Findings"])
    invalid_labels = report.get("invalid_label_findings") or []
    if invalid_labels:
        for item in invalid_labels:
            lines.append(
                f"- `{item.get('stage')}` field=`{item.get('field')}` count=`{item.get('count')}` routing=`{item.get('routing')}` examples=`{item.get('examples')}`"
            )
    else:
        lines.append("- none")
    lines.extend(["", "## High Volume Stages Without Source-Like Fields"])
    gaps = report.get("high_volume_no_source_fields") or []
    if gaps:
        for item in gaps:
            lines.append(
                f"- `{item.get('stage')}` count=`{item.get('event_count')}` routing=`{item.get('routing')}`"
            )
    else:
        lines.append("- none")
    lines.extend(["", "## Unknown Token Findings"])
    unknown_findings = report.get("unknown_token_findings") or []
    if unknown_findings:
        for item in unknown_findings[:20]:
            field_bits = ", ".join(
                f"{field.get('field')}={field.get('count')}({field.get('rate')})"
                for field in (item.get("fields") or [])[:8]
            )
            lines.append(
                f"- `{item.get('stage')}` count=`{item.get('event_count')}` routing=`{item.get('routing')}` fields=`{field_bits}`"
            )
    else:
        lines.append("- none")
    lines.extend(["", "## Reviewed Unknown Token Findings"])
    reviewed_unknown = report.get("reviewed_unknown_token_findings") or []
    if reviewed_unknown:
        for item in reviewed_unknown[:20]:
            field_bits = ", ".join(
                f"{field.get('field')}={field.get('count')}({field.get('reviewed_reason')})"
                for field in (item.get("fields") or [])[:8]
            )
            lines.append(
                f"- `{item.get('stage')}` count=`{item.get('event_count')}` routing=`{item.get('routing')}` fields=`{field_bits}`"
            )
    else:
        lines.append("- none")
    lines.extend(["", "## Top Stages"])
    for stage, count in (report.get("summary", {}).get("top_stages") or {}).items():
        lines.append(f"- `{stage}`: `{count}`")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _raw_row_exclusion_paths(target_date: str, run_id: str | None = None) -> tuple[Path, Path]:
    if run_id is None:
        run_id = datetime.now().astimezone().strftime("%Y%m%dT%H%M%S%f%z")
    report_dir = DATA_DIR / "source_quality" / RAW_ROW_EXCLUSION_DIRNAME / f"{target_date}_{run_id}"
    return (
        report_dir / "manifest.json",
        report_dir / f"pipeline_events_{target_date}.jsonl",
    )


def _exclude_hard_blocking_rows_from_raw(target_date: str, report: dict[str, Any]) -> dict[str, Any] | None:
    exclusions = report.get("hard_blocking_row_exclusions")
    if not isinstance(exclusions, list) or not exclusions:
        return None
    raw_path = _pipeline_events_path(target_date)
    if not raw_path.exists():
        return None
    excluded_lines = {
        int(item.get("line_no"))
        for item in exclusions
        if isinstance(item, dict) and str(item.get("line_no") or "").isdigit()
    }
    if not excluded_lines:
        return None
    manifest_path, backup_path = _raw_row_exclusion_paths(target_date)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(raw_path, backup_path)
    exclusions_by_line = {
        int(item.get("line_no")): item
        for item in exclusions
        if isinstance(item, dict) and str(item.get("line_no") or "").isdigit()
    }
    kept: list[str] = []
    excluded_payloads: list[dict[str, Any]] = []
    with raw_path.open("r", encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, 1):
            if line_no not in excluded_lines:
                kept.append(line)
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                payload = {"raw": line.rstrip("\n")}
            excluded_payloads.append({"line_no": line_no, "payload": payload})
    exclusion_summary = _summarize_raw_row_exclusions(
        excluded_payloads,
        exclusions_by_line,
        target_date=target_date,
    )
    tmp_path = raw_path.with_suffix(raw_path.suffix + ".tmp_row_exclusion")
    tmp_path.write_text("".join(kept), encoding="utf-8")
    tmp_path.replace(raw_path)
    manifest = {
        "report_type": "raw_row_exclusion",
        "target_date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "policy": "exclude_defective_rows_not_full_day_raw",
        "manifest_path": str(manifest_path),
        "source_path": str(raw_path),
        "backup_path": str(backup_path),
        "excluded_row_count": len(excluded_payloads),
        **exclusion_summary,
        "excluded_lines": sorted(excluded_lines),
        "forbidden_uses": [
            "EV",
            "rolling_tuning",
            "MTD_tuning",
            "cumulative_tuning",
            "live_auto_promotion",
            "runtime_approval",
        ],
        "excluded_rows": excluded_payloads,
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def write_report(target_date: str) -> dict[str, Any]:
    report = build_observation_source_quality_audit(target_date)
    exclusion_manifest = _exclude_hard_blocking_rows_from_raw(target_date, report)
    if exclusion_manifest:
        report = build_observation_source_quality_audit(target_date)
        report["raw_row_exclusion"] = {
            "manifest_path": exclusion_manifest.get("manifest_path"),
            "backup_path": exclusion_manifest.get("backup_path"),
            "excluded_row_count": exclusion_manifest.get("excluded_row_count"),
            "stage_counts": exclusion_manifest.get("stage_counts") or {},
            "field_gap_counts": exclusion_manifest.get("field_gap_counts") or {},
            "exclusion_reasons": exclusion_manifest.get("exclusion_reasons") or {},
            "first_timestamp": exclusion_manifest.get("first_timestamp"),
            "last_timestamp": exclusion_manifest.get("last_timestamp"),
            "market_halt_or_circuit_window_overlap": exclusion_manifest.get(
                "market_halt_or_circuit_window_overlap"
            ),
            "market_halt_or_circuit_context": exclusion_manifest.get(
                "market_halt_or_circuit_context"
            ),
            "sample_rows": exclusion_manifest.get("sample_rows") or [],
            "producer_hint": exclusion_manifest.get("producer_hint") or [],
            "policy": exclusion_manifest.get("policy"),
        }
        report["summary"]["raw_row_exclusion_applied"] = True
        report["summary"]["raw_row_exclusion_manifest"] = exclusion_manifest.get("manifest_path")
    else:
        report["summary"]["raw_row_exclusion_applied"] = False
    json_path, md_path = report_paths(target_date)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_markdown(report, md_path)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit observation source-quality field coverage.")
    parser.add_argument("--target-date", required=True)
    parser.add_argument("--start-date", default=DEFAULT_BACKFILL_START_DATE)
    parser.add_argument("--backfill", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.backfill:
        report = (
            write_backfill_report(args.target_date, start_date=args.start_date)
            if args.write
            else build_observation_source_quality_backfill_audit(args.target_date, start_date=args.start_date)
        )
    else:
        report = write_report(args.target_date) if args.write else build_observation_source_quality_audit(args.target_date)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
