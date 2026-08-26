"""Past-only micro-reversion sidecar for Exact V2 AI quality replay.

This module deliberately stays outside the live AI and order paths.  It joins
immutable Exact V2 request provenance to already-persisted 0B/0D observations,
builds a compact tactical context, and keeps future outcomes in a separate
label.  The original provider payload and its hash are never modified.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import math
import os
import shutil
import sqlite3
import stat
import tempfile
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterator, Iterable, Mapping, Sequence
from zoneinfo import ZoneInfo

from src.utils.constants import DATA_DIR
from src.utils.jsonl_io import (
    existing_or_gzip_path,
    iter_jsonl_objects_strict,
    read_json_object_strict,
    write_json_object_generation_safe,
)

from .ask_depletion import (
    ASK_DEPLETION_METRIC_CONTRACT,
    ASK_DEPLETION_SCHEMA,
    DEFAULT_HORIZONS_MS as DEFAULT_ASK_DEPLETION_HORIZONS_MS,
    DEFAULT_TOP_DEPTH_LEVELS as DEFAULT_ASK_DEPLETION_TOP_DEPTH_LEVELS,
    AskDepletionContext,
    build_ask_depletion_report,
)
from .contracts import (
    CLEAN_BASELINE_DATE,
    normalize_symbol,
    normalize_venue,
    registration_item_identity,
)
from .confirmation_window import analyze_confirmation_window
from .depth_join import validate_depth_row
from .onset_quality import (
    ShockOnsetContext,
    ShockTriggerBasis,
    reconstruct_shock_onset_context,
)
from .p2_replay import (
    DEFAULT_SOURCE_EXCLUSION_MANIFEST,
    P2ReplayPoint,
    load_source_exclusion_manifest,
)
from .path_journal import (
    MARKET_STREAM_CONTRACT_ID,
    readable_partition_path_files,
    validate_market_stream_path_provenance,
)
from .path_capture import PATH_CAPTURE_AUTHORITY
from .replay_ablation_contract import (
    CURRENT_ARMS,
    CURRENT_ASK_CANDIDATE_ARM,
    CURRENT_ASK_CONTROL_ARM,
    CURRENT_BASE_CONTROL_ARM,
    CURRENT_DESIGN_ACTIVATION_DATE,
    CURRENT_DESIGN_VERSION,
    LEGACY_ARMS,
    LEGACY_DESIGN_VERSION,
    SOURCE_ONLY_AUTHORITY_CONTRACT as ABLATION_SOURCE_ONLY_AUTHORITY,
    build_current_design_replay_ids,
)
from .tax import (
    InstrumentType,
    ListingMarket,
    normalize_instrument_type,
    normalize_listing_market,
    tax_profile_for,
)

TACTICAL_EVIDENCE_SCHEMA = "tactical_micro_reversion_evidence_v1"
LIFECYCLE_PROJECTION_SCHEMA = "micro_reversion_fast_lifecycle_projection_v1"
OUTCOME_SCHEMA = "micro_reversion_ai_quality_outcome_v1"
OUTCOME_REBUILD_SOURCE_SCHEMA = "micro_reversion_outcome_rebuild_source_ref_v2"
OUTCOME_SOURCE_POOL_SCHEMA = "micro_reversion_outcome_source_pool_v1"
THREE_ARM_SCHEMA = "micro_reversion_ai_quality_three_arm_manifest_v1"
THREE_ARM_REQUEST_SCHEMA = "micro_reversion_ai_quality_three_arm_requests_v1"
REPORT_SCHEMA = "micro_reversion_ai_quality_bridge_v1"
BRIDGE_CONFIG_SCHEMA = "micro_reversion_ai_quality_bridge_config_v1"
BRIDGE_PRODUCER_VERSION = "micro_reversion_ai_quality_bridge_v1_5"
RELEVANT_SOURCE_CACHE_SCHEMA = "micro_reversion_relevant_source_cache_v1"
RELEVANT_SOURCE_CACHE_INDEX_VERSION = "relevant_source_sqlite_v1"
DEFAULT_RELEVANT_SOURCE_CACHE_ROOT = (
    DATA_DIR / "cache" / "micro_reversion_relevant_source_index"
)
DEFAULT_RELEVANT_SOURCE_CACHE_KEEP = 3
DEFAULT_RELEVANT_SOURCE_CACHE_PARTIAL_MAX_AGE_SEC = 24 * 60 * 60
COST_PROFILE_SCHEMA = "micro_reversion_reviewed_cost_profile_v1"
COST_CATALOG_SCHEMA = "micro_reversion_reviewed_cost_catalog_v2"
REVIEWED_COST_POLICY_EFFECTIVE_FROM = date(2026, 8, 18)
CONFIRMATION_WINDOW_SCHEMA = "micro_reversion_confirmation_window_axis_v1"
ASK_DEPLETION_FEATURE_VIEW_SCHEMA = "micro_reversion_ask_depletion_feature_view_v2"

_ECONOMIC_SOURCE_ONLY_FORBIDDEN_USES = [
    "live_prompt_or_threshold_mutation",
    "broker_order_submission_or_cancel",
    "automated_sell_or_position_sizing",
    "provider_route_or_bot_state_change",
    "position_cap_or_cooldown_change",
    "hard_protect_emergency_or_stale_guard_bypass",
    "unverified_cost_or_symbol_promotion",
]
_ECONOMIC_SOURCE_ONLY_AUTHORITY = {
    "decision_authority": "offline_economic_reference_source_only",
    "runtime_effect": False,
    "allowed_runtime_apply": False,
    "trading_runtime_effect": False,
    "trading_decision_effect": False,
    "selection_authority": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
    "provider_call_performed": False,
    "forbidden_uses": _ECONOMIC_SOURCE_ONLY_FORBIDDEN_USES,
}
_EXACT_REVIEWED_LEGACY_COST_FIELDS = frozenset(
    {
        "schema",
        "artifact_id",
        "effective_date",
        "venues",
        "instrument_scope",
        "source",
        "buy_fee_bps",
        "sell_fee_bps",
        "statutory_sell_tax_bps",
        "uncertainty_buffer_bps",
        *_ECONOMIC_SOURCE_ONLY_AUTHORITY,
    }
)
_HISTORICAL_REVIEWED_LEGACY_COST_FIELDS = frozenset(
    {
        "schema",
        "artifact_id",
        "effective_date",
        "venues",
        "instrument_scope",
        "source",
        "buy_fee_bps",
        "sell_fee_bps",
        "statutory_sell_tax_bps",
        "uncertainty_buffer_bps",
    }
)
_CANONICAL_COST_CATALOG_FIELDS = frozenset(
    {
        "schema",
        "artifact_id",
        "target_date",
        "verification_status",
        "verified",
        "profile_count",
        "census",
        "profiles",
        "content_sha256",
        *_ECONOMIC_SOURCE_ONLY_AUTHORITY,
    }
)
_CANONICAL_COST_PROFILE_FIELDS = frozenset(
    {
        "profile_id",
        "effective_from",
        "effective_to",
        "venues",
        "listing_markets",
        "instrument_types",
        "instrument_tax_classes",
        "buy_fee_bps",
        "sell_fee_bps",
        "statutory_sell_tax_bps",
        "uncertainty_buffer_bps",
        "source_bindings",
        "bridge_reviewed_cost_payload",
        "bridge_reviewed_cost_payload_sha256",
        "verification_status",
        "verified",
        "content_sha256",
        *_ECONOMIC_SOURCE_ONLY_AUTHORITY,
    }
)
_CANONICAL_COST_SOURCE_BINDING_FIELDS = frozenset(
    {
        "symbol_master_source_id",
        "symbol_master_source_sha256",
        "broker_fee_source_id",
        "broker_fee_source_sha256",
        "broker_fee_record_sha256",
        "statutory_tax_source_id",
        "statutory_tax_source_sha256",
        "statutory_tax_record_sha256",
    }
)

KST = ZoneInfo("Asia/Seoul")

ASK_DEPLETION_CONTEXT_FIELDS = frozenset(
    {
        "event_id",
        "anchor_role",
        "symbol",
        "venue",
        "session_bucket",
        "sequence_epoch",
        "anchor_event_local_receive_timestamp_ms",
        "event_market_source_sequence",
        "observed_through_local_receive_timestamp_ms",
        "depth_source_complete",
        "market_source_complete",
    }
)
ASK_DEPLETION_HORIZON_FIELDS = frozenset(
    {
        "horizon_ms",
        "mature",
        "source_quality_status",
        "eligible_for_feature_ablation",
        "source_gap_reasons",
        "depth_endpoint_age_ms",
        "depth_observation_count",
        "anchor_best_ask",
        "endpoint_best_ask",
        "initial_anchor_ask_qty",
        "endpoint_anchor_ask_qty",
        "minimum_anchor_ask_qty",
        "max_best_ask_depletion_qty",
        "max_best_ask_depletion_ratio",
        "best_ask_depletion_velocity_qty_per_sec",
        "price_level_cleared",
        "first_price_level_clear_delay_ms",
        "downward_reprice_observed",
        "aggressive_buy_qty_before_max_depletion",
        "aggressive_buy_trade_backed_ratio",
        "unexplained_or_cancel_like_depletion_qty",
        "unexplained_or_cancel_like_depletion_ratio",
        "max_refill_qty",
        "refill_ratio",
        "refill_half_life_ms",
        "top_depth",
    }
)
ASK_DEPLETION_TOP_DEPTH_FIELDS = frozenset(
    {
        "retained_level_count",
        "anchor_price_count",
        "initial_qty",
        "endpoint_qty",
        "minimum_qty",
        "max_depletion_qty",
        "max_depletion_ratio",
    }
)
ASK_DEPLETION_SIDECAR_AUTHORITY = {
    "selection_authority": False,
    "sim_effect": False,
    "runtime_effect": False,
    "trading_runtime_effect": False,
    "trading_decision_effect": False,
    "provider_effect": False,
    "threshold_effect": False,
    "quantity_effect": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
}
ASK_DEPLETION_SIDECAR_RECONSTRUCTION_FIELDS = frozenset(
    {
        "max_depth_age_ms",
        "anchor_depth_age_ms",
        "anchor_source_quality_status",
        "source_quality_status",
        "source_gap_reasons",
        "ignored_cross_scope_depth_row_count",
        "ignored_cross_scope_market_row_count",
    }
)

MARKET_SCHEMAS = {
    "scalp_micro_reversion_market_stream_point_v1",
    "scalp_micro_reversion_market_stream_point_v2",
    "scalp_micro_reversion_market_stream_point_v3",
}
MARKET_CONTRACT_BY_SCHEMA = {
    "scalp_micro_reversion_market_stream_point_v1": (
        "scalp_micro_reversion_market_stream_contract_v1"
    ),
    "scalp_micro_reversion_market_stream_point_v2": (
        "scalp_micro_reversion_market_stream_contract_v2"
    ),
    "scalp_micro_reversion_market_stream_point_v3": MARKET_STREAM_CONTRACT_ID,
}
DEPTH_SCHEMA = "scalp_micro_reversion_market_depth_point_v1"
EVENT_REFERENCE_SCHEMA = "scalp_micro_reversion_path_event_reference_v2"
TRACE_SCHEMA = "ai_decision_trace_v1"
PAYLOAD_SCHEMA = "ai_decision_payload_v1"
INPUT_BUNDLE_VERSION = "scalping_multi_timeframe_context_v1"
ENTRY_CONTEXT_SCHEMA = "entry_candle_context_v1"
HOLDING_CONTEXT_SCHEMA = "holding_decision_context_v1"

METRIC_CONTRACT: dict[str, Any] = {
    "metric_role": "ai_decision_quality_tactical_microstructure_context",
    "decision_authority": "offline_paired_replay_context_only_no_runtime_change",
    "window_policy": (
        "latest_past_same_symbol_venue_session_sequence_epoch_at_or_before_"
        "exact_snapshot_watermark"
    ),
    "sample_floor": (
        "one_valid_row_starts_cumulative_observation_aggregate_promotion_floor_"
        "owned_by_research_gate"
    ),
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "source_quality_gate": (
        "exact_v2_scope_nonfuture_monotonic_fresh_bbo_and_same_basis_depth_"
        "for_economic_capacity_no_imputation"
    ),
    "forbidden_uses": (
        "broker_order_submission",
        "broker_order_cancel",
        "automated_sell",
        "live_buy_tp_stop_trailing_or_threshold_change",
        "provider_or_bot_change",
        "position_sizing_owner_or_cap_replacement",
        "broker_account_order_stale_cooldown_or_hard_safety_bypass",
        "future_cross_symbol_cross_venue_cross_session_or_cross_epoch_join",
        "missing_quote_tape_or_depth_imputation",
        "depth_or_touch_as_real_fill",
        "machine_or_widget_future_performance_as_prompt_input",
        "counterfactual_and_realized_pnl_merge",
    ),
}

AUTHORITY_CONTRACT: dict[str, Any] = {
    "runtime_effect": False,
    "allowed_runtime_apply": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
    "selection_authority": False,
}

CONFIRMATION_WINDOW_METRIC_CONTRACT: dict[str, Any] = {
    "metric_role": "micro_reversion_causal_confirmation_tuning_axis",
    "decision_authority": "offline_micro_reversion_tuning_evidence_only",
    "window_policy": (
        "fixed_post_shock_confirmation_deadline_then_fixed_followthrough_"
        "fresh_top_of_book_proxy_without_imputation"
    ),
    "sample_floor": (
        "one_mature_source_quality_pass_standardized_one_share_outcome_starts_"
        "cumulative_observation_no_promotion_authority"
    ),
    "primary_decision_metric": "equal_weight_avg_profit_pct",
    "source_quality_gate": (
        "same_symbol_venue_session_epoch_monotonic_trade_path_fresh_deadline_"
        "ask_fresh_fixed_followthrough_bid_and_verified_cost_profile"
    ),
    "forbidden_uses": (
        "prompt_input",
        "widget_entry_or_exit_signal_mutation",
        "widget_or_main_bot_order_submission",
        "direct_live_or_sim_runtime_selection",
        "target_stop_trailing_quantity_cap_provider_or_bot_mutation",
        "future_path_or_immature_horizon_imputation",
        "cross_symbol_cross_venue_cross_session_or_cross_epoch_join",
    ),
}

OUTCOME_METRIC_CONTRACT: dict[str, Any] = {
    "metric_role": "counterfactual_outcome_label",
    "decision_authority": "offline_outcome_evaluation_only_no_runtime_change",
    "window_policy": (
        "post_snapshot_same_symbol_venue_session_sequence_epoch_mature_"
        "quantity_sweep_path"
    ),
    "sample_floor": "one_mature_row_starts_cumulative_offline_evaluation",
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "source_quality_gate": (
        "mature_endpoint_continuous_sequence_fresh_bbo_same_basis_depth_"
        "full_quantity_coverage"
    ),
    "forbidden_uses": (
        "prompt_input",
        "live_runtime_apply",
        "realized_and_counterfactual_pnl_merge",
        "unverified_cost_profile_promotion",
    ),
}

REPORT_METRIC_CONTRACT: dict[str, Any] = {
    "metric_role": "ai_decision_quality_micro_reversion_bridge_report",
    "decision_authority": "offline_report_only_no_runtime_change",
    "window_policy": (
        "exact_snapshot_parent_wave_stage_deduplicated_with_separate_"
        "post_snapshot_outcomes"
    ),
    "sample_floor": "one_eligible_parent_wave_stage_row_starts_cumulative_report",
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "source_quality_gate": (
        "exact_context_and_control_response_and_mature_outcome_reported_separately"
    ),
    "forbidden_uses": (
        "direct_live_promotion",
        "provider_or_order_mutation",
        "unverified_cost_profile_as_economic_authority",
    ),
}

# These are the only deterministic, past-only ledgers currently emitted by the
# existing paired-replay request builders.  The bridge validates each ledger's
# declared schema and content hash before preserving it; arbitrary sibling
# objects are never forwarded to a provider.
REPLAY_CANDIDATE_LEDGER_SCHEMAS = frozenset(
    {
        "exact_payload_analysis_v1",
        "anticipatory_reversal_analysis_v1",
        "entry_setup_evidence_v1",
        "entry_price_exact_contract_facts_v1",
        "holding_exact_contract_facts_v1",
    }
)

REPLAY_CANDIDATE_LEDGER_FIELDS: dict[str, frozenset[str]] = {
    "exact_payload_analysis_v1": frozenset(
        {
            "schema",
            "stage",
            "completed_structure",
            "contradictions",
            "deterministic_contract_facts",
            "executable_liquidity",
            "observation_contract",
            "program_flow",
            "source_quality",
            "tape_sample",
            "trigger_state",
            "volume_confirmation",
            "analysis_sha256",
        }
    ),
    "anticipatory_reversal_analysis_v1": frozenset(
        {
            "schema",
            "stage",
            "bounded_opportunity",
            "clean_continuation_probe",
            "confidence_cap",
            "eligible_for_counterfactual_probe",
            "execution_cost",
            "execution_policy",
            "freshness",
            "hard_blockers",
            "learning_contract",
            "observation_contract",
            "precursors",
            "recovery_confirmation_probe",
            "selective_recovery_probe",
            "source_mode",
            "spread",
            "analysis_sha256",
        }
    ),
    "entry_setup_evidence_v1": frozenset(
        {
            "schema",
            "version",
            "setup_family",
            "setup_state",
            "structure_phase",
            "structure_phase_bar_end",
            "structure_phase_policy_version",
            "structure_phase_role",
            "structure_phase_sha256",
            "structure_phase_stable_on_completed_bar",
            "positive_facts",
            "contradicting_facts",
            "invalidation_facts",
            "corroborated_risk_codes",
            "recheck_reasons",
            "context_observations",
            "tail_risk_assessment",
            "execution_readiness_role",
            "execution_readiness_state",
            "symbol_specific_branching",
            "widget_dependency",
            "source_quality",
            "evidence_sha256",
            "metric_role",
            "decision_authority",
            "window_policy",
            "sample_floor",
            "primary_decision_metric",
            "source_quality_gate",
            "forbidden_uses",
            "observation_contract",
            "runtime_effect",
            "allowed_runtime_apply",
            "actual_order_submitted",
            "broker_order_forbidden",
        }
    ),
    "entry_price_exact_contract_facts_v1": frozenset(
        {
            "schema",
            "available_price_count",
            "candidate_prices",
            "control_exposure_selected",
            "control_selected_price",
            "economically_distinct_bases",
            "fresh_quote",
            "max_incremental_chase_cost_bp",
            "minimum_reward_risk_for_aggressive_basis",
            "minimum_upside_for_aggressive_basis_pct",
            "price_cost_baseline",
            "price_delta_from_cost_baseline_bp",
            "setup_invalidated",
            "skip_permitted",
            "skip_reasons",
            "source_blockers",
            "spread_bp",
            "would_fill_now",
        }
    ),
    "holding_exact_contract_facts_v1": frozenset(
        {
            "schema",
            "allowed_worsen_pct",
            "average_entry_price",
            "bbo_fresh",
            "bounded_defer_authority",
            "bounded_defer_checkpoint_horizons_sec",
            "bounded_defer_eligible",
            "candidate_exit_rule",
            "candle_status",
            "completed_bar_count",
            "completed_bars_observed",
            "executable_sell_price",
            "fresh_consistent_core",
            "hard_exit_guard_observed",
            "open_sell_qty",
            "order_consistent",
            "position_observed",
            "position_reconciled",
            "position_valid",
            "remaining_qty",
            "sell_order_or_exit_token_active",
            "soft_exit_candidate",
            "source_quality_status",
            "trim_available",
        }
    ),
}

OUTCOME_ONLY_FIELD_NAMES = frozenset(
    {
        "horizons",
        "first_hit",
        "mfe",
        "mae",
        "future_outcome",
        "outcome_label",
        "target_first",
        "adverse_first",
        "realized_pnl",
        "realized_profit",
        "profit_rate",
        "post_decision_mfe",
        "post_decision_mae",
        "counterfactual_net_mfe_bps",
        "counterfactual_net_mae_bps",
        "confirmation_window_axis",
    }
)


@dataclass(frozen=True, slots=True)
class BridgeConfig:
    context_lookback_sec: int = 30
    active_wave_max_age_sec: int = 180
    max_market_age_ms: int = 2_500
    max_depth_age_ms: int = 1_000
    max_quote_age_ms: int = 1_000
    max_broker_position_age_sec: float = 60.0
    tape_capacity_window_sec: int = 10
    target_liquidation_sec: int = 10
    participation_grid: tuple[float, ...] = (0.02, 0.05, 0.10)
    max_entry_sweep_slippage_bps: float = 10.0
    max_exit_sweep_slippage_bps: float = 10.0
    buy_fee_bps: float = 0.0
    sell_fee_bps: float = 0.0
    statutory_sell_tax_bps: float | None = None
    uncertainty_buffer_bps: float = 3.0
    minimum_net_profit_bps: float = 5.0
    adverse_label_bps: float = -70.0
    max_outcome_endpoint_lag_ms: int = 2_500
    max_outcome_internal_gap_ms: int = 2_500
    outcome_horizons_sec: tuple[int, ...] = (1, 3, 5, 10, 20, 30, 60, 120, 180)
    reversion_confirmation_horizons_sec: tuple[int, ...] = (120, 180)
    reversion_followthrough_horizons_sec: tuple[int, ...] = (30, 60)
    reversion_confirmation_fraction: float = 0.5
    cost_profile_source: str = "missing_verified_instrument_cost_profile"
    cost_profile_verified: bool = False
    cost_profile_artifact_id: str = ""
    cost_profile_artifact_sha256: str = ""
    cost_profile_artifact_payload_json: str = ""
    cost_profile_effective_date: str = ""
    cost_profile_venues: tuple[str, ...] = ()
    cost_profile_catalog_payload_json: str = ""
    cost_profile_catalog_content_sha256: str = ""

    def __post_init__(self) -> None:
        if self.context_lookback_sec <= 0 or self.active_wave_max_age_sec <= 0:
            raise ValueError("context windows must be positive")
        if (
            self.max_market_age_ms < 0
            or self.max_depth_age_ms < 0
            or self.max_quote_age_ms < 0
        ):
            raise ValueError("freshness limits must not be negative")
        if (
            isinstance(self.max_broker_position_age_sec, bool)
            or not isinstance(self.max_broker_position_age_sec, (int, float))
            or not math.isfinite(float(self.max_broker_position_age_sec))
            or self.max_broker_position_age_sec <= 0
        ):
            raise ValueError("broker position freshness limit must be positive")
        if self.tape_capacity_window_sec <= 0 or self.target_liquidation_sec <= 0:
            raise ValueError("liquidation windows must be positive")
        if (
            not self.participation_grid
            or tuple(sorted(set(self.participation_grid))) != self.participation_grid
            or any(not 0 < value <= 1 for value in self.participation_grid)
        ):
            raise ValueError("participation_grid must be sorted, unique, and in (0,1]")
        for field in (
            "max_entry_sweep_slippage_bps",
            "max_exit_sweep_slippage_bps",
            "buy_fee_bps",
            "sell_fee_bps",
            "uncertainty_buffer_bps",
            "minimum_net_profit_bps",
        ):
            value = getattr(self, field)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(float(value))
                or value < 0
            ):
                raise ValueError(f"{field} must not be negative")
        if self.statutory_sell_tax_bps is not None and (
            isinstance(self.statutory_sell_tax_bps, bool)
            or not isinstance(self.statutory_sell_tax_bps, (int, float))
            or not math.isfinite(float(self.statutory_sell_tax_bps))
            or self.statutory_sell_tax_bps < 0
        ):
            raise ValueError("statutory_sell_tax_bps must not be negative")
        if self.cost_profile_verified:
            source = str(self.cost_profile_source or "").strip()
            artifact_id = str(self.cost_profile_artifact_id or "").strip()
            artifact_hash = str(self.cost_profile_artifact_sha256 or "").strip()
            artifact_payload_json = str(
                self.cost_profile_artifact_payload_json or ""
            ).strip()
            effective_date = str(self.cost_profile_effective_date or "").strip()
            normalized_venues = tuple(
                sorted({normalize_venue(value) for value in self.cost_profile_venues})
            )
            catalog_payload_json = str(
                self.cost_profile_catalog_payload_json or ""
            ).strip()
            catalog_content_hash = str(
                self.cost_profile_catalog_content_sha256 or ""
            ).strip()
            catalog_mode = bool(catalog_payload_json or catalog_content_hash)
            if (
                not source
                or source.startswith(("missing_", "operator_"))
                or not artifact_id
                or len(artifact_hash) != 64
                or any(
                    character not in "0123456789abcdef" for character in artifact_hash
                )
                or not artifact_payload_json
                or not effective_date
                or not normalized_venues
                or "UNKNOWN" in normalized_venues
            ):
                raise ValueError(
                    "verified cost profile requires a reviewed artifact hash, "
                    "effective date, and venue scope"
                )
            try:
                date.fromisoformat(effective_date)
            except ValueError as exc:
                raise ValueError("verified cost profile date is invalid") from exc
            if tuple(self.cost_profile_venues) != normalized_venues:
                raise ValueError("verified cost profile venues must be normalized")
            try:
                artifact_payload = json.loads(artifact_payload_json)
            except (TypeError, ValueError) as exc:
                raise ValueError("verified cost profile artifact is invalid") from exc
            if not isinstance(artifact_payload, dict):
                raise ValueError("verified cost profile artifact must be an object")
            if catalog_mode:
                if (
                    not catalog_payload_json
                    or len(catalog_content_hash) != 64
                    or any(
                        character not in "0123456789abcdef"
                        for character in catalog_content_hash
                    )
                    or artifact_payload_json != catalog_payload_json
                    or artifact_payload.get("schema") != COST_CATALOG_SCHEMA
                    or artifact_payload.get("content_sha256") != catalog_content_hash
                ):
                    raise ValueError("verified cost catalog contract invalid")
                _validate_cost_catalog_payload(
                    artifact_payload,
                    target_date=date.fromisoformat(effective_date),
                )
                computed_artifact_hash = _producer_sha256(artifact_payload)
                if computed_artifact_hash != artifact_hash:
                    raise ValueError("verified cost catalog artifact hash mismatch")
            else:
                _validate_exact_reviewed_legacy_cost_profile(
                    artifact_payload,
                    target_date=date.fromisoformat(effective_date),
                )
                expected_artifact_fields = {
                    "artifact_id": artifact_id,
                    "effective_date": effective_date,
                    "venues": list(normalized_venues),
                    "source": source,
                    "buy_fee_bps": self.buy_fee_bps,
                    "sell_fee_bps": self.sell_fee_bps,
                    "statutory_sell_tax_bps": self.statutory_sell_tax_bps,
                    "uncertainty_buffer_bps": self.uncertainty_buffer_bps,
                }
                if any(
                    artifact_payload.get(field) != expected
                    for field, expected in expected_artifact_fields.items()
                ):
                    raise ValueError(
                        "verified cost profile artifact fields do not match config"
                    )
                computed_artifact_hash = hashlib.sha256(
                    json.dumps(
                        artifact_payload,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                        default=str,
                    ).encode("utf-8")
                ).hexdigest()
                if computed_artifact_hash != artifact_hash:
                    raise ValueError("verified cost profile artifact hash mismatch")
        if (
            isinstance(self.adverse_label_bps, bool)
            or not isinstance(self.adverse_label_bps, (int, float))
            or not math.isfinite(float(self.adverse_label_bps))
            or self.adverse_label_bps >= 0
        ):
            raise ValueError("adverse_label_bps must be negative")
        if (
            self.max_outcome_endpoint_lag_ms < 0
            or self.max_outcome_internal_gap_ms <= 0
        ):
            raise ValueError("outcome continuity limits are invalid")
        if (
            not self.outcome_horizons_sec
            or tuple(sorted(set(self.outcome_horizons_sec)))
            != self.outcome_horizons_sec
            or any(
                isinstance(value, bool) or not isinstance(value, int) or value <= 0
                for value in self.outcome_horizons_sec
            )
        ):
            raise ValueError("outcome horizons must be sorted unique positive values")
        if (
            not self.reversion_confirmation_horizons_sec
            or tuple(sorted(set(self.reversion_confirmation_horizons_sec)))
            != self.reversion_confirmation_horizons_sec
            or any(
                isinstance(value, bool) or not isinstance(value, int) or value <= 0
                for value in self.reversion_confirmation_horizons_sec
            )
            or self.reversion_confirmation_horizons_sec[-1]
            > self.active_wave_max_age_sec
        ):
            raise ValueError(
                "reversion confirmation horizons must be sorted unique positive "
                "values within the active wave window"
            )
        if (
            not self.reversion_followthrough_horizons_sec
            or tuple(sorted(set(self.reversion_followthrough_horizons_sec)))
            != self.reversion_followthrough_horizons_sec
            or any(
                isinstance(value, bool) or not isinstance(value, int) or value <= 0
                for value in self.reversion_followthrough_horizons_sec
            )
        ):
            raise ValueError(
                "reversion followthrough horizons must be sorted unique positive "
                "values"
            )
        if (
            isinstance(self.reversion_confirmation_fraction, bool)
            or not isinstance(self.reversion_confirmation_fraction, (int, float))
            or not math.isfinite(float(self.reversion_confirmation_fraction))
            or not 0 < float(self.reversion_confirmation_fraction) <= 1
        ):
            raise ValueError("reversion confirmation fraction must be in (0, 1]")


def _bridge_config_contract(config: BridgeConfig) -> dict[str, Any]:
    body = {
        "schema": BRIDGE_CONFIG_SCHEMA,
        "producer_version": BRIDGE_PRODUCER_VERSION,
        "values": asdict(config),
    }
    return {**body, "config_sha256": _sha256(body)}


def _post_snapshot_source_horizon_sec(config: BridgeConfig) -> int:
    """Return the longest causal source window needed by any outcome axis."""

    return max(
        config.outcome_horizons_sec[-1],
        config.reversion_confirmation_horizons_sec[-1]
        + config.reversion_followthrough_horizons_sec[-1],
    )


def _bridge_config_from_contract(contract: Mapping[str, Any]) -> BridgeConfig:
    body = {key: value for key, value in contract.items() if key != "config_sha256"}
    if (
        contract.get("schema") != BRIDGE_CONFIG_SCHEMA
        or contract.get("producer_version") != BRIDGE_PRODUCER_VERSION
        or contract.get("config_sha256") != _sha256(body)
    ):
        raise ValueError("micro_context_bridge_contract_invalid")
    values = contract.get("values")
    if not isinstance(values, Mapping):
        raise ValueError("micro_context_bridge_contract_invalid")
    expected_fields = set(BridgeConfig.__dataclass_fields__)
    if set(values) != expected_fields:
        raise ValueError("micro_context_bridge_config_fields_invalid")
    normalized = dict(values)
    for field in (
        "participation_grid",
        "outcome_horizons_sec",
        "reversion_confirmation_horizons_sec",
        "reversion_followthrough_horizons_sec",
        "cost_profile_venues",
    ):
        value = normalized.get(field)
        if not isinstance(value, (list, tuple)):
            raise ValueError(f"micro_context_bridge_config_{field}_invalid")
        normalized[field] = tuple(value)
    return BridgeConfig(**normalized)


@dataclass(frozen=True, slots=True)
class ResolvedMicroScope:
    venue: str
    session_bucket: str
    status: str
    reason: str | None = None


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("ascii")


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _is_sha256(value: Any) -> bool:
    text = str(value or "")
    return len(text) == 64 and all(
        character in "0123456789abcdef" for character in text
    )


def _producer_sha256(value: Any) -> str:
    serialized = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


def _validate_economic_source_only_authority(
    payload: Mapping[str, Any], *, error_prefix: str
) -> None:
    for field, expected in _ECONOMIC_SOURCE_ONLY_AUTHORITY.items():
        if payload.get(field) != expected:
            raise ValueError(f"{error_prefix}_authority_invalid:{field}")


def _native_nonnegative_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _validated_cost_number(
    payload: Mapping[str, Any], *, field: str, error_prefix: str
) -> float:
    value = payload.get(field)
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(float(value))
        or float(value) < 0
    ):
        raise ValueError(f"{error_prefix}_numeric_invalid:{field}")
    return float(value)


def _validate_reviewed_policy_values(
    payload: Mapping[str, Any],
    *,
    target_date: date,
    effective_from: date,
    error_prefix: str,
) -> None:
    if target_date < REVIEWED_COST_POLICY_EFFECTIVE_FROM:
        return
    if effective_from < REVIEWED_COST_POLICY_EFFECTIVE_FROM:
        raise ValueError(f"{error_prefix}_effective_before_reviewed_policy")
    expected = {
        "buy_fee_bps": 1.5,
        "sell_fee_bps": 1.5,
        "statutory_sell_tax_bps": 20.0,
        "uncertainty_buffer_bps": 0.0,
    }
    for field, value in expected.items():
        if (
            _validated_cost_number(
                payload,
                field=field,
                error_prefix=error_prefix,
            )
            != value
        ):
            raise ValueError(f"{error_prefix}_reviewed_value_mismatch:{field}")


def _validate_exact_reviewed_legacy_cost_profile(
    payload: Mapping[str, Any], *, target_date: date
) -> None:
    """Validate the exact bridge payload emitted by the reviewed owner."""

    current_policy = target_date >= REVIEWED_COST_POLICY_EFFECTIVE_FROM
    payload_fields = frozenset(payload)
    authority_enhanced_historical = bool(
        not current_policy and payload_fields == _EXACT_REVIEWED_LEGACY_COST_FIELDS
    )
    if (
        current_policy
        and payload_fields != _EXACT_REVIEWED_LEGACY_COST_FIELDS
        or not current_policy
        and payload_fields
        not in {
            _EXACT_REVIEWED_LEGACY_COST_FIELDS,
            _HISTORICAL_REVIEWED_LEGACY_COST_FIELDS,
        }
    ):
        raise ValueError("verified_cost_profile_fields_invalid")
    if payload.get("schema") != COST_PROFILE_SCHEMA:
        raise ValueError("verified_cost_profile_schema_invalid")
    if current_policy or authority_enhanced_historical:
        _validate_economic_source_only_authority(
            payload,
            error_prefix="verified_cost_profile",
        )
    artifact_id = str(payload.get("artifact_id") or "").strip()
    source = str(payload.get("source") or "").strip()
    if (
        not artifact_id
        or not source
        or current_policy
        and source != f"canonical_economic_reference_v2:{artifact_id}"
        or payload.get("instrument_scope") != "domestic_common_or_preferred_stock"
    ):
        raise ValueError("verified_cost_profile_identity_invalid")
    venues = payload.get("venues")
    if (
        not isinstance(venues, list)
        or not venues
        or venues != sorted(set(venues))
        or any(
            not isinstance(venue, str)
            or normalize_venue(venue) != venue
            or venue not in {"KRX", "NXT", "SOR"}
            for venue in venues
        )
    ):
        raise ValueError("verified_cost_profile_venues_invalid")
    for field in (
        "buy_fee_bps",
        "sell_fee_bps",
        "statutory_sell_tax_bps",
        "uncertainty_buffer_bps",
    ):
        _validated_cost_number(
            payload,
            field=field,
            error_prefix="verified_cost_profile",
        )
    try:
        effective_from = date.fromisoformat(str(payload.get("effective_date") or ""))
    except ValueError as exc:
        raise ValueError("verified_cost_profile_date_invalid") from exc
    if target_date < effective_from:
        raise ValueError("verified_cost_profile_not_effective_on_target_date")
    _validate_reviewed_policy_values(
        payload,
        target_date=target_date,
        effective_from=effective_from,
        error_prefix="verified_cost_profile",
    )


def _validated_profile_scope(
    profile: Mapping[str, Any],
    *,
    field: str,
    allowed: frozenset[str],
) -> list[str]:
    values = profile.get(field)
    if (
        not isinstance(values, list)
        or not values
        or values != sorted(set(values))
        or any(not isinstance(value, str) or value not in allowed for value in values)
    ):
        raise ValueError(f"verified_cost_catalog_profile_scope_invalid:{field}")
    return values


def _validate_cost_catalog_payload(
    payload: Mapping[str, Any], *, target_date: date
) -> None:
    if set(payload) != _CANONICAL_COST_CATALOG_FIELDS:
        raise ValueError("verified_cost_catalog_fields_invalid")
    if (
        payload.get("schema") != COST_CATALOG_SCHEMA
        or payload.get("verification_status") != "verified"
        or payload.get("verified") is not True
        or payload.get("target_date") != target_date.isoformat()
        or not str(payload.get("artifact_id") or "").strip()
    ):
        raise ValueError("verified_cost_catalog_header_invalid")
    _validate_economic_source_only_authority(
        payload,
        error_prefix="verified_cost_catalog",
    )
    declared_hash = str(payload.get("content_sha256") or "")
    content = {key: value for key, value in payload.items() if key != "content_sha256"}
    if declared_hash != _producer_sha256(content):
        raise ValueError("verified_cost_catalog_content_sha256_mismatch")
    profiles = payload.get("profiles")
    if not isinstance(profiles, list) or not profiles:
        raise ValueError("verified_cost_catalog_profiles_missing")
    if not _native_nonnegative_int(payload.get("profile_count")) or payload.get(
        "profile_count"
    ) != len(profiles):
        raise ValueError("verified_cost_catalog_profile_count_mismatch")
    census = payload.get("census")
    census_fields = {
        "profile_count",
        "venue_count",
        "listing_market_count",
        "instrument_type_count",
        "instrument_tax_class_count",
    }
    if (
        not isinstance(census, Mapping)
        or set(census) != census_fields
        or not all(
            _native_nonnegative_int(census.get(field)) for field in census_fields
        )
    ):
        raise ValueError("verified_cost_catalog_census_invalid")

    profile_ids: set[str] = set()
    all_venues: set[str] = set()
    all_listing_markets: set[str] = set()
    all_instrument_types: set[str] = set()
    all_tax_classes: set[str] = set()
    for profile in profiles:
        if (
            not isinstance(profile, Mapping)
            or set(profile) != _CANONICAL_COST_PROFILE_FIELDS
        ):
            raise ValueError("verified_cost_catalog_profile_invalid")
        _validate_economic_source_only_authority(
            profile,
            error_prefix="verified_cost_catalog_profile",
        )
        if (
            profile.get("verification_status") != "verified"
            or profile.get("verified") is not True
        ):
            raise ValueError("verified_cost_catalog_profile_verification_invalid")
        profile_id = str(profile.get("profile_id") or "")
        if not profile_id or profile_id in profile_ids:
            raise ValueError("verified_cost_catalog_profile_id_invalid")
        profile_ids.add(profile_id)
        declared_profile_hash = str(profile.get("content_sha256") or "")
        profile_content = {
            key: value for key, value in profile.items() if key != "content_sha256"
        }
        if declared_profile_hash != _producer_sha256(profile_content):
            raise ValueError("verified_cost_catalog_profile_hash_mismatch")

        try:
            effective_from = date.fromisoformat(
                str(profile.get("effective_from") or "")
            )
            effective_to = (
                None
                if profile.get("effective_to") in (None, "")
                else date.fromisoformat(str(profile.get("effective_to")))
            )
        except ValueError as exc:
            raise ValueError("verified_cost_catalog_profile_window_invalid") from exc
        if (
            effective_to is not None
            and effective_to < effective_from
            or target_date < effective_from
            or effective_to is not None
            and target_date > effective_to
        ):
            raise ValueError("verified_cost_catalog_profile_not_effective")

        venues = _validated_profile_scope(
            profile,
            field="venues",
            allowed=frozenset({"KRX", "NXT", "SOR"}),
        )
        listing_markets = _validated_profile_scope(
            profile,
            field="listing_markets",
            allowed=frozenset({"KOSPI", "KOSDAQ"}),
        )
        instrument_types = _validated_profile_scope(
            profile,
            field="instrument_types",
            allowed=frozenset({"EQUITY"}),
        )
        tax_classes = _validated_profile_scope(
            profile,
            field="instrument_tax_classes",
            allowed=frozenset({"ordinary_taxable_equity_20bps"}),
        )
        all_venues.update(venues)
        all_listing_markets.update(listing_markets)
        all_instrument_types.update(instrument_types)
        all_tax_classes.update(tax_classes)

        for numeric_field in (
            "buy_fee_bps",
            "sell_fee_bps",
            "statutory_sell_tax_bps",
            "uncertainty_buffer_bps",
        ):
            _validated_cost_number(
                profile,
                field=numeric_field,
                error_prefix="verified_cost_catalog_profile",
            )
        _validate_reviewed_policy_values(
            profile,
            target_date=target_date,
            effective_from=effective_from,
            error_prefix="verified_cost_catalog_profile",
        )

        source_bindings = profile.get("source_bindings")
        if (
            not isinstance(source_bindings, Mapping)
            or set(source_bindings) != _CANONICAL_COST_SOURCE_BINDING_FIELDS
        ):
            raise ValueError("verified_cost_catalog_source_bindings_invalid")
        for field in _CANONICAL_COST_SOURCE_BINDING_FIELDS:
            value = str(source_bindings.get(field) or "")
            if field.endswith("_sha256"):
                if not _is_sha256(value):
                    raise ValueError(
                        f"verified_cost_catalog_source_binding_invalid:{field}"
                    )
            elif not value:
                raise ValueError(
                    f"verified_cost_catalog_source_binding_invalid:{field}"
                )
        if target_date >= REVIEWED_COST_POLICY_EFFECTIVE_FROM and (
            source_bindings.get("broker_fee_source_id")
            != "operator-reviewed-kiwoom-fee-2026-08-18"
            or source_bindings.get("statutory_tax_source_id")
            != "operator-reviewed-statutory-tax-2026-08-18"
            or not str(source_bindings.get("symbol_master_source_id") or "").startswith(
                "kis-official-common-stock-master-"
            )
        ):
            raise ValueError("verified_cost_catalog_reviewed_source_binding_invalid")

        bridge_payload = profile.get("bridge_reviewed_cost_payload")
        if not isinstance(bridge_payload, Mapping):
            raise ValueError("verified_cost_catalog_bridge_payload_invalid")
        _validate_exact_reviewed_legacy_cost_profile(
            bridge_payload,
            target_date=target_date,
        )
        bridge_expected = {
            "artifact_id": profile_id,
            "effective_date": effective_from.isoformat(),
            "venues": venues,
            "buy_fee_bps": profile.get("buy_fee_bps"),
            "sell_fee_bps": profile.get("sell_fee_bps"),
            "statutory_sell_tax_bps": profile.get("statutory_sell_tax_bps"),
            "uncertainty_buffer_bps": profile.get("uncertainty_buffer_bps"),
        }
        if any(
            bridge_payload.get(field) != expected
            for field, expected in bridge_expected.items()
        ) or profile.get("bridge_reviewed_cost_payload_sha256") != _producer_sha256(
            bridge_payload
        ):
            raise ValueError("verified_cost_catalog_bridge_payload_invalid")

    expected_census = {
        "profile_count": len(profiles),
        "venue_count": len(all_venues),
        "listing_market_count": len(all_listing_markets),
        "instrument_type_count": len(all_instrument_types),
        "instrument_tax_class_count": len(all_tax_classes),
    }
    if dict(census) != expected_census:
        raise ValueError("verified_cost_catalog_census_mismatch")


def _resolved_cost_profile(
    *,
    config: BridgeConfig,
    observed_date: date | None,
    venue: str,
    symbol_metadata: Mapping[str, Any],
) -> Mapping[str, Any] | None:
    if not config.cost_profile_catalog_payload_json:
        if not config.cost_profile_verified:
            return None
        if observed_date is not None:
            effective_from = date.fromisoformat(config.cost_profile_effective_date)
            if observed_date >= effective_from:
                direct_payload = json.loads(config.cost_profile_artifact_payload_json)
                if not isinstance(direct_payload, Mapping):
                    raise ValueError("verified_cost_profile_artifact_invalid")
                _validate_exact_reviewed_legacy_cost_profile(
                    direct_payload,
                    target_date=observed_date,
                )
        return {
            "profile_id": config.cost_profile_artifact_id,
            "profile_content_sha256": config.cost_profile_artifact_sha256,
            "effective_from": config.cost_profile_effective_date,
            "effective_to": None,
            "venues": list(config.cost_profile_venues),
            "listing_markets": [symbol_metadata.get("listing_market")],
            "instrument_types": [symbol_metadata.get("instrument_type")],
            "instrument_tax_classes": [symbol_metadata.get("instrument_tax_class")],
            "buy_fee_bps": config.buy_fee_bps,
            "sell_fee_bps": config.sell_fee_bps,
            "statutory_sell_tax_bps": config.statutory_sell_tax_bps,
            "uncertainty_buffer_bps": config.uncertainty_buffer_bps,
        }
    if observed_date is None:
        return None
    catalog = json.loads(config.cost_profile_catalog_payload_json)
    normalized_venue = normalize_venue(venue)
    listing_market = str(symbol_metadata.get("listing_market") or "")
    instrument_type = str(symbol_metadata.get("instrument_type") or "")
    tax_class = str(symbol_metadata.get("instrument_tax_class") or "")
    matches: list[Mapping[str, Any]] = []
    for profile in catalog.get("profiles") or []:
        if not isinstance(profile, Mapping):
            continue
        try:
            effective_from = date.fromisoformat(
                str(profile.get("effective_from") or "")
            )
            effective_to = (
                None
                if profile.get("effective_to") in (None, "")
                else date.fromisoformat(str(profile.get("effective_to")))
            )
        except ValueError:
            continue
        if (
            effective_from <= observed_date
            and (effective_to is None or observed_date <= effective_to)
            and normalized_venue in (profile.get("venues") or [])
            and listing_market in (profile.get("listing_markets") or [])
            and instrument_type in (profile.get("instrument_types") or [])
            and tax_class in (profile.get("instrument_tax_classes") or [])
        ):
            matches.append(profile)
    if len(matches) > 1:
        raise ValueError("verified_cost_catalog_profile_ambiguous")
    return matches[0] if matches else None


def _stored_semantic_sha256(value: Any) -> str:
    """Hash the sanitized stored value with the trace producer's byte rules."""

    if isinstance(value, bytes):
        payload = value
    elif isinstance(value, str):
        payload = value.encode("utf-8")
    else:
        payload = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _finite_float(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _positive_float(value: Any) -> float | None:
    result = _finite_float(value)
    return result if result is not None and result > 0 else None


def _nonnegative_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        result = int(value)
    except (TypeError, ValueError):
        return None
    return result if result >= 0 else None


def _parse_timestamp(value: Any) -> datetime:
    text = str(value or "").strip()
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include timezone")
    return parsed


def _timestamp_ms(value: Any) -> int:
    return int(_parse_timestamp(value).timestamp() * 1_000)


def _timestamp_us(value: Any) -> int:
    return int(_parse_timestamp(value).timestamp() * 1_000_000)


def _session(value: Any) -> str:
    return str(value or "").strip().upper()


def _route(value: Any) -> str:
    return str(value or "").strip().lower()


def _exact_venue(value: Any) -> str:
    raw = str(value or "").strip().upper()
    if raw == "PREMARKET_KRX_LIKE":
        return raw
    return normalize_venue(raw)


def resolve_micro_scope(trace: Mapping[str, Any]) -> ResolvedMicroScope:
    """Map an Exact V2 route to one explicit persisted micro partition."""

    venue = normalize_venue(trace.get("effective_venue"))
    raw_venue = str(trace.get("effective_venue") or "").strip().upper()
    session = _session(trace.get("session_bucket"))
    market_route = _route(trace.get("market_data_route"))
    if "sor" in market_route or "integrated" in market_route:
        micro_venue = "SOR"
    elif market_route in {"krx", "krx_only", "krx_regular"}:
        micro_venue = "KRX"
    elif market_route in {"nxt", "nxt_only", "nxt_regular"}:
        micro_venue = "NXT"
    elif raw_venue == "PREMARKET_KRX_LIKE" or session == "PREMARKET_KRX_LIKE":
        return ResolvedMicroScope(
            "UNKNOWN",
            "UNKNOWN",
            "source_unavailable",
            "premarket_route_ambiguous",
        )
    else:
        micro_venue = venue
    if micro_venue == "UNKNOWN":
        return ResolvedMicroScope(
            "UNKNOWN",
            "UNKNOWN",
            "source_unavailable",
            "effective_venue_missing",
        )
    if "PREMARKET" in session:
        phase = "PREMARKET"
    elif "AFTERMARKET" in session:
        phase = "AFTERMARKET"
    elif "REGULAR" in session or "OVERLAP" in session:
        phase = "REGULAR_OVERLAP" if micro_venue == "NXT" else "REGULAR"
    else:
        return ResolvedMicroScope(
            micro_venue,
            session or "UNKNOWN",
            "source_unavailable",
            "venue_session_mapping_missing",
        )
    return ResolvedMicroScope(
        micro_venue,
        f"{micro_venue}_{phase}",
        "resolved",
    )


def _walk_objects(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk_objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_objects(child)


def _stored_replay_exact_payload(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    source = (
        payload.get("sanitized_replay_context")
        if payload.get("replay_context_present") is True
        else payload.get("sanitized_user_input")
    )
    if not isinstance(source, dict):
        return None
    nested = source.get("exact_payload")
    if isinstance(nested, dict) and (
        "exact_payload_analysis_v1" in source
        or str(source.get("input_schema") or "").startswith("decision_quality_")
        or TACTICAL_EVIDENCE_SCHEMA in source
    ):
        return nested
    return source


def _expected_context_schema(trace: Mapping[str, Any]) -> str | None:
    stage = (
        str(trace.get("decision_stage") or trace.get("endpoint") or "").strip().lower()
    )
    if stage in {
        "entry",
        "entry_screen",
        "analyze_target",
        "entry_price",
        "post_probe",
    }:
        return ENTRY_CONTEXT_SCHEMA
    if stage in {
        "holding",
        "holding_score",
        "holding_flow",
        "scale_in",
        "exit",
        "overnight",
    }:
        return HOLDING_CONTEXT_SCHEMA
    return None


def _canonical_context_findings(
    trace: Mapping[str, Any],
    payload: Mapping[str, Any],
    exact_payload: Mapping[str, Any] | None,
) -> tuple[str, ...]:
    """Verify the stored context instead of trusting trace summary strings."""

    findings: list[str] = []
    if not str(trace.get("decision_trace_id") or "").strip():
        findings.append("decision_trace_id_missing")
    expected_schema = _expected_context_schema(trace)
    if expected_schema is None:
        return ("decision_stage_context_schema_unknown",)
    capture = payload.get("canonical_context_capture")
    if not isinstance(capture, Mapping):
        findings.append("canonical_context_capture_missing")
    else:
        if capture.get("status") != "exact_completed_bars_captured":
            findings.append("canonical_context_capture_not_exact")
        if capture.get("schema") != expected_schema:
            findings.append("canonical_context_capture_schema_mismatch")
        if capture.get("input_bundle_version") != INPUT_BUNDLE_VERSION:
            findings.append("canonical_context_capture_bundle_mismatch")
        if (_nonnegative_int(capture.get("raw_bar_count")) or 0) <= 0:
            findings.append("canonical_context_capture_raw_bars_missing")
        if (_nonnegative_int(capture.get("completed_bar_count")) or 0) <= 0:
            findings.append("canonical_context_capture_completed_bars_missing")

    owner_keys = (
        ("entry_candle_context", "entry_candle_context_v1")
        if expected_schema == ENTRY_CONTEXT_SCHEMA
        else ("holding_decision_context", "holding_decision_context_v1")
    )
    owner_contexts = []
    owner_roots = [exact_payload] if isinstance(exact_payload, Mapping) else []
    nested_exact = (
        exact_payload.get("exact_payload")
        if isinstance(exact_payload, Mapping)
        else None
    )
    if isinstance(nested_exact, Mapping):
        owner_roots.append(nested_exact)
    for owner_root in owner_roots:
        if owner_root.get("schema") == expected_schema:
            owner_contexts.append(owner_root)
        for key in owner_keys:
            candidate = owner_root.get(key)
            if (
                isinstance(candidate, Mapping)
                and candidate.get("schema") == expected_schema
            ):
                owner_contexts.append(candidate)
    owner_by_hash = {_sha256(row): row for row in owner_contexts}
    contexts = list(owner_by_hash.values())
    if not contexts:
        recursive_by_hash = {
            _sha256(row): row
            for row in _walk_objects(exact_payload)
            if row.get("schema") == expected_schema
        }
        contexts = list(recursive_by_hash.values())
    if len(contexts) != 1:
        findings.append(
            "canonical_context_missing"
            if not contexts
            else "canonical_context_ambiguous"
        )
        return tuple(sorted(set(findings)))
    context = contexts[0]
    candle = (
        context.get("candle") if expected_schema == HOLDING_CONTEXT_SCHEMA else context
    )
    if not isinstance(candle, Mapping):
        findings.append("canonical_candle_context_missing")
        return tuple(sorted(set(findings)))
    if candle.get("input_bundle_version") != INPUT_BUNDLE_VERSION:
        findings.append("canonical_context_bundle_mismatch")
    bars = candle.get("bars")
    if not isinstance(bars, list) or not bars:
        findings.append("canonical_raw_bars_missing")
    else:
        forming_key = (
            "is_forming" if expected_schema == HOLDING_CONTEXT_SCHEMA else "forming"
        )
        completed_count = sum(
            isinstance(bar, Mapping)
            and forming_key in bar
            and bar.get(forming_key) is False
            for bar in bars
        )
        if completed_count <= 0:
            findings.append("canonical_completed_bars_missing")
        if isinstance(capture, Mapping) and (
            _nonnegative_int(capture.get("raw_bar_count")) != len(bars)
            or _nonnegative_int(capture.get("completed_bar_count")) != completed_count
        ):
            findings.append("canonical_context_capture_count_mismatch")
    trace_venue = _exact_venue(trace.get("effective_venue"))
    trace_session = _session(trace.get("session_bucket"))
    scope_context = context if expected_schema == HOLDING_CONTEXT_SCHEMA else candle
    if _exact_venue(scope_context.get("venue")) != trace_venue:
        findings.append("canonical_context_venue_mismatch")
    if _session(scope_context.get("session")) != trace_session:
        findings.append("canonical_context_session_mismatch")
    return tuple(sorted(set(findings)))


def exact_snapshot_watermark(
    trace: Mapping[str, Any], payload: Mapping[str, Any]
) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
    """Return the unique exact market snapshot that precedes provider latency."""

    blockers: list[str] = []
    if trace.get("schema") != TRACE_SCHEMA:
        blockers.append("trace_schema_invalid")
    if payload.get("schema") != PAYLOAD_SCHEMA:
        blockers.append("payload_schema_invalid")
    for trace_field, payload_field in (
        ("payload_sha256", "payload_sha256"),
        ("request_envelope_sha256", "request_envelope_sha256"),
    ):
        if not trace.get(trace_field) or trace.get(trace_field) != payload.get(
            payload_field
        ):
            blockers.append(f"{trace_field}_mismatch")
    if trace.get("payload_replay_exact") is not True:
        blockers.append("trace_payload_not_exact")
    if trace.get("request_capture_status") != "captured":
        blockers.append("request_not_captured")
    if payload.get("replay_exact") is not True:
        blockers.append("payload_store_not_exact")
    sanitized_user_input = payload.get("sanitized_user_input")
    input_format = str(payload.get("input_format") or "")
    stored_semantic_hash = str(payload.get("sanitized_user_input_sha256") or "")
    trace_semantic_hash = str(trace.get("payload_semantic_sha256") or "")
    provider_semantic_verified = False
    if stored_semantic_hash:
        if _stored_semantic_sha256(sanitized_user_input) != stored_semantic_hash:
            blockers.append("provider_payload_semantic_sha256_mismatch")
        if not trace_semantic_hash:
            blockers.append("trace_payload_semantic_sha256_missing")
        elif trace_semantic_hash != stored_semantic_hash:
            blockers.append("trace_payload_semantic_sha256_mismatch")
        else:
            provider_semantic_verified = True
    elif trace_semantic_hash:
        blockers.append("payload_semantic_sha256_missing")
    recomputed_provider_hash = None
    if input_format == "structured":
        recomputed_provider_hash = _producer_sha256(sanitized_user_input)
    elif input_format == "plain_text" and isinstance(sanitized_user_input, str):
        recomputed_provider_hash = hashlib.sha256(
            sanitized_user_input.encode("utf-8")
        ).hexdigest()
    if recomputed_provider_hash is not None and recomputed_provider_hash != str(
        payload.get("payload_sha256") or ""
    ):
        blockers.append("provider_payload_content_sha256_mismatch")
    elif recomputed_provider_hash is not None:
        provider_semantic_verified = True
    trace_replay_present = trace.get("replay_context_present") is True
    payload_replay_present = payload.get("replay_context_present") is True
    if trace_replay_present != payload_replay_present:
        blockers.append("replay_context_presence_mismatch")
    if payload_replay_present and (
        payload.get("replay_context_exact") is not True
        or trace.get("replay_context_exact") is not True
    ):
        blockers.append("replay_context_not_exact")
    if payload_replay_present:
        payload_replay_hash = str(payload.get("replay_context_sha256") or "")
        trace_replay_hash = str(trace.get("replay_context_sha256") or "")
        replay_source = payload.get("sanitized_replay_context")
        replay_input_format = str(payload.get("replay_context_input_format") or "")
        raw_replay_hash_recomputable = replay_input_format in {
            "structured",
            "plain_text",
        }
        replay_semantic_verified = False
        if (
            not payload_replay_hash
            or trace_replay_hash != payload_replay_hash
            or replay_source is None
            or (
                raw_replay_hash_recomputable
                and _stored_semantic_sha256(replay_source) != payload_replay_hash
            )
        ):
            blockers.append("replay_context_sha256_mismatch")
        else:
            replay_semantic_verified = raw_replay_hash_recomputable
        stored_replay_semantic_hash = str(
            payload.get("sanitized_replay_context_sha256") or ""
        )
        trace_replay_semantic_hash = str(
            trace.get("replay_context_semantic_sha256") or ""
        )
        if stored_replay_semantic_hash:
            if (
                replay_source is None
                or _stored_semantic_sha256(replay_source) != stored_replay_semantic_hash
            ):
                blockers.append("replay_context_semantic_sha256_mismatch")
            if not trace_replay_semantic_hash:
                blockers.append("trace_replay_context_semantic_sha256_missing")
            elif trace_replay_semantic_hash != stored_replay_semantic_hash:
                blockers.append("trace_replay_context_semantic_sha256_mismatch")
            else:
                replay_semantic_verified = True
        if trace_replay_semantic_hash and not stored_replay_semantic_hash:
            blockers.append("payload_replay_context_semantic_sha256_missing")
    else:
        replay_semantic_verified = False
    provider_semantic_hash_status = (
        "stored_semantic_hash_verified"
        if provider_semantic_verified
        else "stored_semantic_hash_unverifiable_legacy"
    )
    exact_replay_source_semantic_status = (
        "stored_semantic_hash_verified"
        if (
            replay_semantic_verified
            if payload_replay_present
            else provider_semantic_verified
        )
        else "stored_semantic_hash_unverifiable_legacy"
    )
    envelope = {
        "endpoint": str(payload.get("endpoint") or "generic"),
        "model": str(payload.get("model") or "-"),
        "schema_name": str(payload.get("schema_name") or "-"),
        "require_json": bool(payload.get("require_json")),
        "temperature": payload.get("temperature"),
        "max_output_tokens": payload.get("max_output_tokens"),
        "reasoning_effort": payload.get("reasoning_effort"),
        "prompt_sha256": payload.get("prompt_sha256"),
        "user_input_sha256": payload.get("payload_sha256"),
    }
    if payload_replay_present:
        envelope["replay_context_sha256"] = payload.get("replay_context_sha256")
    if _producer_sha256(envelope) != str(payload.get("request_envelope_sha256") or ""):
        blockers.append("request_envelope_content_sha256_mismatch")
    if str(trace.get("input_preflight_mode") or "") != "exact_v2":
        blockers.append("input_preflight_not_exact_v2")
    if trace.get("input_preflight_allowed") is not True:
        blockers.append("input_preflight_not_allowed")
    if trace.get("venue_consistent") is not True:
        blockers.append("venue_not_consistent")
    if trace.get("input_blockers"):
        blockers.append("input_blockers_present")
    if str(trace.get("provider_actual") or "none").lower() == "none":
        blockers.append("provider_none")
    trace_simulation = bool(
        str(trace.get("sim_record_id") or "").strip()
        or str(trace.get("sim_parent_record_id") or "").strip()
        or str(trace.get("position_reconciliation_mode") or "").strip()
        == "simulation_book"
    )
    payload_simulation = bool(
        str(payload.get("sim_record_id") or "").strip()
        or str(payload.get("sim_parent_record_id") or "").strip()
        or str(payload.get("position_reconciliation_mode") or "").strip()
        == "simulation_book"
    )
    if (
        trace_simulation
        or payload_simulation
        or str(trace.get("position_reconciliation_mode") or "").strip()
        == "simulation_book"
    ):
        blockers.append("simulation_observation_not_natural_cohort")
    if trace_simulation != payload_simulation:
        blockers.append("simulation_provenance_trace_payload_mismatch")
    if str(trace.get("canonical_context_capture_status") or "") != (
        "exact_completed_bars_captured"
    ):
        blockers.append("canonical_completed_bars_not_captured")
    exact_payload = _stored_replay_exact_payload(payload)
    blockers.extend(_canonical_context_findings(trace, payload, exact_payload))
    source = (
        payload.get("sanitized_replay_context")
        if payload.get("replay_context_present") is True
        else payload.get("sanitized_user_input")
    )
    trace_symbol = normalize_symbol(trace.get("stock_code"))
    snapshots = []
    snapshot_objects = [
        row
        for row in _walk_objects(source)
        if row.get("schema") == "ai_market_snapshot_v1"
    ]
    for row in snapshot_objects:
        snapshot_symbol = normalize_symbol(row.get("stock_code"))
        if not snapshot_symbol:
            blockers.append("exact_market_snapshot_symbol_missing")
            continue
        if trace_symbol and snapshot_symbol != trace_symbol:
            blockers.append("exact_market_snapshot_cross_symbol_present")
            continue
        try:
            captured_at_ms = _timestamp_ms(row.get("captured_at"))
            captured_at_us = _timestamp_us(row.get("captured_at"))
        except (TypeError, ValueError):
            blockers.append("exact_market_snapshot_timestamp_invalid")
            continue
        snapshots.append((captured_at_ms, captured_at_us, row))
    unique = {
        (captured_ms, captured_us, _sha256(row)): row
        for captured_ms, captured_us, row in snapshots
    }
    if not unique:
        blockers.append("exact_market_snapshot_missing")
        return None, tuple(sorted(set(blockers)))
    if len(unique) != 1:
        blockers.append("exact_market_snapshot_ambiguous")
        return None, tuple(sorted(set(blockers)))
    (captured_at_ms, captured_at_us, _), snapshot = next(iter(unique.items()))
    try:
        decision_us = _timestamp_us(trace.get("decision_ts"))
    except (TypeError, ValueError):
        blockers.append("trace_decision_timestamp_invalid")
    else:
        if captured_at_us > decision_us:
            blockers.append("snapshot_after_ai_decision")
    snapshot_venue = str(snapshot.get("effective_venue") or "").strip().upper()
    snapshot_session = _session(snapshot.get("session_bucket"))
    trace_venue = str(trace.get("effective_venue") or "").strip().upper()
    trace_session = _session(trace.get("session_bucket"))
    if not snapshot_venue or snapshot_venue != trace_venue:
        blockers.append("snapshot_effective_venue_mismatch")
    if not snapshot_session or snapshot_session != trace_session:
        blockers.append("snapshot_session_bucket_mismatch")
    trace_snapshot_id = str(trace.get("snapshot_id") or "").strip()
    snapshot_id = str(snapshot.get("snapshot_id") or "").strip()
    if not trace_snapshot_id or not snapshot_id or snapshot_id != trace_snapshot_id:
        blockers.append("snapshot_id_mismatch")
    payload_venue = _exact_venue(payload.get("effective_venue"))
    payload_session = _session(payload.get("session_bucket"))
    if normalize_symbol(payload.get("symbol")) != trace_symbol:
        blockers.append("payload_trace_symbol_mismatch")
    if str(payload.get("snapshot_id") or "").strip() != trace_snapshot_id:
        blockers.append("payload_trace_snapshot_id_mismatch")
    if (
        str(payload.get("endpoint") or "").strip()
        != str(trace.get("endpoint") or "").strip()
    ):
        blockers.append("payload_trace_endpoint_mismatch")
    requested_model = str(
        trace.get("model_requested") or trace.get("model") or ""
    ).strip()
    if requested_model and str(payload.get("model") or "").strip() != requested_model:
        blockers.append("payload_trace_requested_model_mismatch")
    if str(payload.get("prompt_sha256") or "") != str(trace.get("prompt_sha256") or ""):
        blockers.append("payload_trace_prompt_sha256_mismatch")
    if payload_venue != _exact_venue(trace.get("effective_venue")):
        blockers.append("payload_trace_venue_mismatch")
    if payload_session != trace_session:
        blockers.append("payload_trace_session_mismatch")
    trace_route = _route(trace.get("market_data_route"))
    snapshot_route = _route(snapshot.get("market_data_route"))
    payload_route = _route(payload.get("market_data_route"))
    if not trace_route or snapshot_route != trace_route:
        blockers.append("snapshot_market_data_route_mismatch")
    if payload_route != trace_route:
        blockers.append("payload_trace_market_data_route_mismatch")
    integrated_sor_route_proven = bool(
        ("integrated" in trace_route or "sor" in trace_route)
        and (
            snapshot.get("integrated_sor_route_proven") is True
            or snapshot.get("nxt_integrated_execution_view_proven") is True
        )
    )
    if ("integrated" in trace_route or "sor" in trace_route) and not (
        integrated_sor_route_proven
    ):
        blockers.append("integrated_route_proof_missing")
    trace_broker_route = str(trace.get("broker_route") or "").strip().upper()
    snapshot_broker_route = str(snapshot.get("broker_route") or "").strip().upper()
    payload_broker_route = str(payload.get("broker_route") or "").strip().upper()
    if not trace_broker_route or snapshot_broker_route != trace_broker_route:
        blockers.append("snapshot_broker_route_mismatch")
    if payload_broker_route != trace_broker_route:
        blockers.append("payload_trace_broker_route_mismatch")
    snapshot_simulation = bool(
        str(snapshot.get("sim_record_id") or "").strip()
        or str(snapshot.get("position_reconciliation_mode") or "").strip()
        == "simulation_book"
        or snapshot.get("simulation_position_reconciled") is True
    )
    if snapshot_simulation:
        blockers.append("simulation_snapshot_not_natural_cohort")
    return {
        "snapshot_id": snapshot.get("snapshot_id") or trace.get("snapshot_id"),
        "captured_at": snapshot.get("captured_at"),
        "captured_at_ms": captured_at_ms,
        "captured_at_us": captured_at_us,
        "stock_code": trace_symbol,
        "effective_venue": snapshot_venue,
        "session_bucket": snapshot_session,
        "trace_market_data_route": trace_route,
        "integrated_sor_route_proven": integrated_sor_route_proven,
        "provider_payload_semantic_hash_status": provider_semantic_hash_status,
        "exact_replay_source_semantic_status": (exact_replay_source_semantic_status),
    }, tuple(sorted(set(blockers)))


def _valid_market_row(row: Mapping[str, Any]) -> tuple[bool, str | None]:
    schema = str(row.get("schema") or "")
    expected_contract = MARKET_CONTRACT_BY_SCHEMA.get(schema)
    if expected_contract is None or row.get("metric_contract_id") != expected_contract:
        return False, "market_schema_invalid"
    stored_symbol = row.get("symbol")
    stored_venue = row.get("venue")
    raw_symbol = str(stored_symbol or "").strip().upper()
    raw_venue = str(stored_venue or "").strip().upper()
    normalized_venue = normalize_venue(raw_venue)
    if (
        not isinstance(stored_symbol, str)
        or stored_symbol != raw_symbol
        or len(raw_symbol) != 6
        or not raw_symbol.isdigit()
        or not isinstance(stored_venue, str)
        or stored_venue != raw_venue
        or raw_venue not in {"KRX", "NXT", "SOR"}
    ):
        return False, "market_item_scope_conflict"
    registration_item = row.get("item")
    if registration_item is None:
        # The canonical v3 path producer validates the Kiwoom registration
        # item before constructing ``PathJournalPoint`` and deliberately
        # persists only its normalized symbol/venue identity.  Older schemas
        # do not carry that producer-side omission contract.
        if schema != "scalp_micro_reversion_market_stream_point_v3":
            return False, "market_item_scope_conflict"
    else:
        item_symbol, item_venue = registration_item_identity(registration_item)
        if item_symbol != raw_symbol or item_venue != normalized_venue:
            return False, "market_item_scope_conflict"
    if (
        row.get("actual_order_submitted") is not False
        or row.get("broker_order_forbidden") is not True
        or row.get("trading_runtime_effect") is not False
    ):
        return False, "market_authority_invalid"
    for field in ("trade_price", "best_bid", "best_ask"):
        value = row.get(field)
        if value is not None and (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
            or float(value) <= 0
        ):
            return False, "market_numeric_contract_invalid"
    trade_qty = row.get("trade_qty")
    if trade_qty is not None and (
        isinstance(trade_qty, bool) or not isinstance(trade_qty, int) or trade_qty < 0
    ):
        return False, "market_numeric_contract_invalid"
    quote_age_ms = row.get("quote_age_ms")
    if quote_age_ms is not None and (
        isinstance(quote_age_ms, bool)
        or not isinstance(quote_age_ms, (int, float))
        or not math.isfinite(float(quote_age_ms))
        or float(quote_age_ms) < 0
    ):
        return False, "market_numeric_contract_invalid"
    try:
        _, consumer_eligible, _ = validate_market_stream_path_provenance(
            path_order_status=str(row.get("path_order_status") or ""),
            path_consumer_eligible=row.get("path_consumer_eligible"),
            exchange_timestamp_regression_ms=row.get(
                "exchange_timestamp_regression_ms"
            ),
        )
        _timestamp_us(row.get("local_receive_timestamp"))
        exchange_ms = _timestamp_us(row.get("exchange_timestamp"))
        receive_ms = _timestamp_us(row.get("local_receive_timestamp"))
    except (TypeError, ValueError):
        return False, "market_provenance_invalid"
    if not consumer_eligible:
        return False, "market_path_consumer_ineligible"
    if receive_ms < exchange_ms:
        return False, "market_receive_precedes_exchange"
    source_sequence = row.get("source_sequence")
    series_sequence = row.get("series_sequence")
    if (
        isinstance(source_sequence, bool)
        or not isinstance(source_sequence, int)
        or source_sequence <= 0
        or isinstance(series_sequence, bool)
        or not isinstance(series_sequence, int)
        or source_sequence != series_sequence
    ):
        return False, "market_sequence_invalid"
    sequence_epoch = row.get("sequence_epoch")
    if (
        isinstance(sequence_epoch, bool)
        or not isinstance(sequence_epoch, int)
        or sequence_epoch <= 0
    ):
        return False, "market_sequence_epoch_invalid"
    if row.get("realtime_type") != "0B":
        return False, "market_realtime_type_invalid"
    bid = _positive_float(row.get("best_bid"))
    ask = _positive_float(row.get("best_ask"))
    if bid is not None and ask is not None and ask < bid:
        return False, "market_bbo_crossed"
    return True, None


def _valid_depth_row(row: Mapping[str, Any]) -> tuple[bool, str | None]:
    try:
        validate_depth_row(dict(row))
    except (TypeError, ValueError):
        return False, "depth_contract_invalid"
    return True, None


def _valid_reference(row: Mapping[str, Any]) -> tuple[bool, str | None]:
    if row.get("schema") != EVENT_REFERENCE_SCHEMA:
        return False, "event_reference_schema_invalid"
    if (
        row.get("actual_order_submitted") is not False
        or row.get("broker_order_forbidden") is not True
        or row.get("trading_runtime_effect") is not False
    ):
        return False, "event_reference_authority_invalid"
    if row.get("decision_authority") != PATH_CAPTURE_AUTHORITY:
        return False, "event_reference_contract_invalid"
    for field in (
        "sequence_epoch",
        "event_detected_at_ms",
        "segment_event_detected_at_ms",
        "shock_horizon_ms",
        "event_sequence_in_wave",
    ):
        value = row.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            return False, "event_reference_identity_invalid"
    if any(
        not str(row.get(field) or "").strip()
        for field in ("parent_wave_id", "path_segment_id", "shock_event_id")
    ):
        return False, "event_reference_identity_invalid"
    try:
        started_ms = _timestamp_ms(row.get("capture_started_at"))
        ended_ms = _timestamp_ms(row.get("capture_ended_at"))
    except (TypeError, ValueError):
        return False, "event_reference_capture_window_invalid"
    segment_ms = int(row.get("segment_event_detected_at_ms") or 0)
    if not started_ms <= segment_ms <= ended_ms:
        return False, "event_reference_capture_window_invalid"
    return True, None


def _scope_key(row: Mapping[str, Any]) -> tuple[str, str, str, int]:
    try:
        sequence_epoch = int(row.get("sequence_epoch") or 0)
    except (TypeError, ValueError):
        sequence_epoch = 0
    return (
        normalize_symbol(row.get("symbol")),
        normalize_venue(row.get("venue")),
        _session(row.get("session_bucket")),
        sequence_epoch,
    )


def _timestamp_kst_date(value: Any) -> str | None:
    try:
        return _parse_timestamp(value).astimezone(KST).date().isoformat()
    except (TypeError, ValueError):
        return None


def _epoch_is_exact(value: Any, expected: int) -> bool:
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and value > 0
        and value == expected
    )


def _canonical_unique_rows(
    rows: Iterable[Mapping[str, Any]],
    *,
    timestamp: Any,
    sequence_field: str | None = "source_sequence",
) -> list[Mapping[str, Any]]:
    """Return a deterministic exact-row census without physical duplicates."""

    unique: dict[str, Mapping[str, Any]] = {}
    for row in rows:
        row_hash = _sha256(row)
        existing = unique.get(row_hash)
        if existing is not None and existing != row:
            raise ValueError("micro_reversion_canonical_source_hash_collision")
        unique.setdefault(row_hash, row)

    def key(row: Mapping[str, Any]) -> tuple[int, int, str]:
        observed = timestamp(row)
        if not isinstance(observed, int) or isinstance(observed, bool):
            raise ValueError("micro_reversion_canonical_source_timestamp_invalid")
        sequence = (
            _nonnegative_int(row.get(sequence_field)) or 0
            if sequence_field is not None
            else 0
        )
        return observed, sequence, _sha256(row)

    return sorted(unique.values(), key=key)


def _normalized_pipeline_session(value: Any) -> str:
    session = _session(value)
    return {
        "KRX_LIKE_PREMARKET": "PREMARKET_KRX_LIKE",
        "KRX_LIKE_AFTERMARKET": "AFTERMARKET_KRX_LIKE",
    }.get(session, session)


def _parse_pipeline_timestamp(value: Any) -> datetime:
    """Parse the pipeline journal's historical naive-KST timestamp contract."""

    text = str(value or "").strip()
    if not text:
        raise ValueError("pipeline timestamp missing")
    parsed = datetime.fromisoformat(text)
    return parsed.replace(tzinfo=KST) if parsed.tzinfo is None else parsed


def _entry_like_decision_stage(value: Any) -> bool:
    return str(value or "").strip().lower() in {
        "entry",
        "entry_screen",
        "analyze_target",
        "gatekeeper",
        "post_probe",
    }


def _canonical_entry_pipeline_rows(
    *,
    evidence: Mapping[str, Any],
    entry_pipeline_rows: Iterable[Mapping[str, Any]],
    future_end_us: int,
) -> list[Mapping[str, Any]]:
    """Select only exact entry-stage allocator rows in the causal outcome window."""

    stage = evidence.get("decision_stage") or (
        evidence.get(LIFECYCLE_PROJECTION_SCHEMA) or {}
    ).get("decision_stage")
    if not _entry_like_decision_stage(stage):
        return []
    trace_id = str(evidence.get("decision_trace_id") or "").strip()
    symbol = normalize_symbol(evidence.get("stock_code"))
    expected_venue = _exact_venue(evidence.get("trace_effective_venue"))
    expected_session = _normalized_pipeline_session(
        evidence.get("trace_session_bucket")
    )
    target_date = _timestamp_kst_date(evidence.get("snapshot_captured_at"))
    try:
        decision_us = _timestamp_us(evidence.get("trace_decision_ts"))
        if target_date is None:
            raise ValueError("snapshot date missing")
        date.fromisoformat(target_date)
    except (TypeError, ValueError):
        return []
    selected: list[Mapping[str, Any]] = []
    for row in entry_pipeline_rows:
        if not isinstance(row, Mapping) or row.get("pipeline") != "ENTRY_PIPELINE":
            continue
        fields = row.get("fields")
        if not isinstance(fields, Mapping):
            continue
        emitted_at = row.get("emitted_at")
        try:
            parsed = _parse_pipeline_timestamp(emitted_at)
            emitted_us = int(parsed.timestamp() * 1_000_000)
        except (TypeError, ValueError):
            continue
        emitted_date = parsed.astimezone(KST).date().isoformat()
        declared_date = str(row.get("emitted_date") or "").strip()
        if (
            emitted_date != target_date
            or declared_date != target_date
            or emitted_us < decision_us
            or emitted_us > future_end_us
            or str(fields.get("ai_decision_trace_id") or "").strip() != trace_id
            or normalize_symbol(row.get("stock_code")) != symbol
            or _exact_venue(fields.get("effective_venue") or fields.get("venue"))
            != expected_venue
            or _normalized_pipeline_session(fields.get("market_session_bucket"))
            != expected_session
        ):
            continue
        selected.append(row)
    return _canonical_unique_rows(
        selected,
        timestamp=lambda row: int(
            _parse_pipeline_timestamp(row.get("emitted_at")).timestamp() * 1_000_000
        ),
        sequence_field="record_id",
    )


def _canonical_tactical_source_rows(
    *,
    target_date: str,
    trace: Mapping[str, Any],
    payload: Mapping[str, Any],
    market_rows: Iterable[Mapping[str, Any]],
    depth_rows: Iterable[Mapping[str, Any]],
    event_references: Iterable[Mapping[str, Any]],
    config: BridgeConfig,
) -> dict[str, Any]:
    """Bound one trace to exact-date/scope/epoch causal source rows.

    Semantically invalid rows remain in the selected epoch so the downstream
    evidence builder can reproduce its source-quality blockers. Rows whose
    timestamp, date, scope, or epoch cannot be proven are never copied into a
    parent or content-addressed source pool.
    """

    watermark, _ = exact_snapshot_watermark(trace, payload)
    scope = resolve_micro_scope(trace)
    symbol = normalize_symbol(trace.get("stock_code"))
    if (
        watermark is None
        or _timestamp_kst_date(watermark.get("captured_at")) != target_date
        or scope.status != "resolved"
        or not symbol
    ):
        return {
            "selected_epoch": 0,
            "market_rows": [],
            "depth_rows": [],
            "event_reference_rows": [],
            "context_start_us": 0,
            "snapshot_us": 0,
            "future_end_us": 0,
        }
    snapshot_us = int(watermark["captured_at_us"])
    context_start_us = max(
        0,
        snapshot_us
        - (config.active_wave_max_age_sec + config.context_lookback_sec) * 1_000_000,
    )
    future_end_us = (
        snapshot_us
        + (
            _post_snapshot_source_horizon_sec(config) * 1_000
            + config.max_outcome_endpoint_lag_ms
        )
        * 1_000
    )
    scope3 = (symbol, scope.venue, scope.session_bucket)

    dated_market: list[Mapping[str, Any]] = []
    for row in market_rows:
        if (
            normalize_symbol(row.get("symbol")),
            normalize_venue(row.get("venue")),
            _session(row.get("session_bucket")),
        ) != scope3 or _timestamp_kst_date(
            row.get("local_receive_timestamp")
        ) != target_date:
            continue
        try:
            observed_us = _timestamp_us(row.get("local_receive_timestamp"))
        except (TypeError, ValueError):
            continue
        if context_start_us <= observed_us <= future_end_us:
            dated_market.append(row)
    dated_depth: list[Mapping[str, Any]] = []
    for row in depth_rows:
        if (
            normalize_symbol(row.get("symbol")),
            normalize_venue(row.get("venue")),
            _session(row.get("session_bucket")),
        ) != scope3 or _timestamp_kst_date(
            row.get("local_receive_timestamp")
        ) != target_date:
            continue
        try:
            observed_us = _timestamp_us(row.get("local_receive_timestamp"))
        except (TypeError, ValueError):
            continue
        if context_start_us <= observed_us <= future_end_us:
            dated_depth.append(row)

    dated_references: list[Mapping[str, Any]] = []
    for row in event_references:
        detected_at_ms = row.get("event_detected_at_ms")
        if (
            (
                normalize_symbol(row.get("symbol")),
                normalize_venue(row.get("venue")),
                _session(row.get("session_bucket")),
            )
            != scope3
            or not isinstance(detected_at_ms, int)
            or isinstance(detected_at_ms, bool)
            or detected_at_ms <= 0
        ):
            continue
        detected_us = detected_at_ms * 1_000
        try:
            detected_date = (
                datetime.fromtimestamp(detected_at_ms / 1_000.0, tz=KST)
                .date()
                .isoformat()
            )
        except (OSError, OverflowError, ValueError):
            continue
        if (
            detected_date == target_date
            and context_start_us <= detected_us <= snapshot_us
        ):
            dated_references.append(row)

    # Epoch is a transport-generation identity, not a semantic-quality result.
    # Fix the newest causal generation across every native transport stream
    # before validating row contents.  A reconnect can deliver 0D depth or an
    # event reference before its first 0B trade; selecting from market rows
    # alone would silently fall back to the previous connection.  Two epochs
    # observed at the exact latest causal timestamp are not orderable by their
    # per-stream source sequences, so fail closed instead of choosing one by
    # hash/order.
    causal_epoch_observations = [
        (
            _timestamp_us(row.get("local_receive_timestamp")),
            int(row["sequence_epoch"]),
        )
        for row in (*dated_market, *dated_depth)
        if _timestamp_us(row.get("local_receive_timestamp")) <= snapshot_us
        and isinstance(row.get("sequence_epoch"), int)
        and not isinstance(row.get("sequence_epoch"), bool)
        and int(row["sequence_epoch"]) > 0
    ]
    causal_epoch_observations.extend(
        (
            int(row["event_detected_at_ms"]) * 1_000,
            int(row["sequence_epoch"]),
        )
        for row in dated_references
        if isinstance(row.get("sequence_epoch"), int)
        and not isinstance(row.get("sequence_epoch"), bool)
        and int(row["sequence_epoch"]) > 0
    )
    latest_causal_us = max(
        (observed_us for observed_us, _epoch in causal_epoch_observations),
        default=None,
    )
    latest_causal_epochs = {
        epoch
        for observed_us, epoch in causal_epoch_observations
        if observed_us == latest_causal_us
    }
    selected_epoch = (
        next(iter(latest_causal_epochs)) if len(latest_causal_epochs) == 1 else 0
    )
    selected_market = [
        row
        for row in dated_market
        if _epoch_is_exact(row.get("sequence_epoch"), selected_epoch)
    ]
    selected_market = _canonical_unique_rows(
        selected_market,
        timestamp=lambda row: _timestamp_us(row.get("local_receive_timestamp")),
    )

    selected_depth = [
        row
        for row in dated_depth
        if _epoch_is_exact(row.get("sequence_epoch"), selected_epoch)
    ]
    selected_depth = _canonical_unique_rows(
        selected_depth,
        timestamp=lambda row: _timestamp_us(row.get("local_receive_timestamp")),
    )

    selected_references = [
        row
        for row in dated_references
        if _epoch_is_exact(row.get("sequence_epoch"), selected_epoch)
    ]
    selected_references = _canonical_unique_rows(
        selected_references,
        timestamp=lambda row: int(row.get("event_detected_at_ms") or 0) * 1_000,
        sequence_field="event_sequence_in_wave",
    )
    return {
        "selected_epoch": selected_epoch,
        "market_rows": selected_market,
        "depth_rows": selected_depth,
        "event_reference_rows": selected_references,
        "context_start_us": context_start_us,
        "snapshot_us": snapshot_us,
        "future_end_us": future_end_us,
    }


def _canonical_future_outcome_source_rows(
    *,
    evidence: Mapping[str, Any],
    market_rows: Iterable[Mapping[str, Any]],
    depth_rows: Iterable[Mapping[str, Any]],
    entry_pipeline_rows: Iterable[Mapping[str, Any]],
    config: BridgeConfig,
) -> dict[str, list[Mapping[str, Any]]]:
    """Return the minimal exact rows capable of rebuilding one future outcome."""

    snapshot_ms = int(evidence.get("snapshot_captured_at_ms") or 0)
    snapshot_us = snapshot_ms * 1_000
    future_end_us = (
        snapshot_us
        + (
            _post_snapshot_source_horizon_sec(config) * 1_000
            + config.max_outcome_endpoint_lag_ms
        )
        * 1_000
    )
    target_date = _timestamp_kst_date(evidence.get("snapshot_captured_at"))
    if target_date is None:
        return {"market": [], "depth": [], "entry_pipeline": []}
    scope4 = (
        normalize_symbol(evidence.get("stock_code")),
        normalize_venue(evidence.get("micro_venue")),
        _session(evidence.get("micro_session_bucket")),
        int(evidence.get("sequence_epoch") or 0),
    )
    selected_market: list[Mapping[str, Any]] = []
    for row in market_rows:
        if (
            _scope_key(row) != scope4
            or not _epoch_is_exact(row.get("sequence_epoch"), scope4[3])
            or _timestamp_kst_date(row.get("local_receive_timestamp")) != target_date
        ):
            continue
        try:
            observed_us = _timestamp_us(row.get("local_receive_timestamp"))
        except (TypeError, ValueError):
            continue
        if snapshot_us < observed_us <= future_end_us:
            selected_market.append(row)
    selected_market = _canonical_unique_rows(
        selected_market,
        timestamp=lambda row: _timestamp_us(row.get("local_receive_timestamp")),
    )

    depth_start_us = max(0, snapshot_us - config.max_depth_age_ms * 1_000)
    selected_depth: list[Mapping[str, Any]] = []
    for row in depth_rows:
        if (
            _scope_key(row) != scope4
            or not _epoch_is_exact(row.get("sequence_epoch"), scope4[3])
            or _timestamp_kst_date(row.get("local_receive_timestamp")) != target_date
        ):
            continue
        try:
            observed_us = _timestamp_us(row.get("local_receive_timestamp"))
        except (TypeError, ValueError):
            continue
        if depth_start_us <= observed_us <= future_end_us:
            selected_depth.append(row)
    selected_depth = _canonical_unique_rows(
        selected_depth,
        timestamp=lambda row: _timestamp_us(row.get("local_receive_timestamp")),
    )
    return {
        "market": selected_market,
        "depth": selected_depth,
        "entry_pipeline": _canonical_entry_pipeline_rows(
            evidence=evidence,
            entry_pipeline_rows=entry_pipeline_rows,
            future_end_us=future_end_us,
        ),
    }


def _levels(value: Any) -> tuple[tuple[int, float, int], ...]:
    if not isinstance(value, list):
        return ()
    result: list[tuple[int, float, int]] = []
    for raw in value:
        if not isinstance(raw, (list, tuple)) or len(raw) != 3:
            return ()
        level = _nonnegative_int(raw[0])
        price = _positive_float(raw[1])
        quantity = _nonnegative_int(raw[2])
        if level is None or level <= 0 or price is None or quantity is None:
            return ()
        result.append((level, price, quantity))
    return tuple(result)


def _capacity_within_slippage(
    levels: Sequence[tuple[int, float, int]], *, side: str, max_slippage_bps: float
) -> int | None:
    if not levels:
        return None
    best = levels[0][1]
    capacity = 0
    for _, price, quantity in levels:
        slippage = (
            (price / best - 1.0) * 10_000.0
            if side == "ask"
            else (best / price - 1.0) * 10_000.0
        )
        if slippage > max_slippage_bps + 1e-9:
            break
        capacity += quantity
    return capacity


def _sweep_vwap(
    levels: Sequence[tuple[int, float, int]], quantity: int
) -> float | None:
    if quantity <= 0 or not levels:
        return None
    remaining = quantity
    notional = 0.0
    filled = 0
    for _, price, available in levels:
        take = min(remaining, available)
        notional += price * take
        filled += take
        remaining -= take
        if remaining <= 0:
            break
    return notional / filled if remaining <= 0 and filled > 0 else None


def _aggressor_quantities(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    buy_qty = 0
    sell_qty = 0
    unknown_qty = 0
    for row in rows:
        quantity = _nonnegative_int(row.get("trade_qty")) or 0
        side = str(row.get("aggressor_side") or "UNKNOWN").upper()
        if side == "BUY":
            buy_qty += quantity
        elif side == "SELL":
            sell_qty += quantity
        else:
            unknown_qty += quantity
    known = buy_qty + sell_qty
    return {
        "buy_qty": buy_qty,
        "sell_qty": sell_qty,
        "unknown_qty": unknown_qty,
        "known_qty": known,
        "buy_ratio": (buy_qty / known if known else None),
        "sell_ratio": (sell_qty / known if known else None),
        "sample_count": len(rows),
    }


def _series_sequence_findings(
    rows: Sequence[Mapping[str, Any]], *, prefix: str
) -> tuple[str, ...]:
    findings: list[str] = []
    previous_sequence = 0
    previous_receive_ms = 0
    for row in rows:
        sequence = int(row.get("source_sequence") or 0)
        receive_ms = _timestamp_us(row.get("local_receive_timestamp"))
        if sequence <= previous_sequence:
            findings.append(f"{prefix}_sequence_duplicate_or_regressed")
        elif previous_sequence and sequence > previous_sequence + 1:
            findings.append(f"{prefix}_sequence_gap")
        if receive_ms < previous_receive_ms:
            findings.append(f"{prefix}_local_receive_time_regressed")
        previous_sequence = sequence
        previous_receive_ms = receive_ms
    return tuple(sorted(set(findings)))


def _p2_point(row: Mapping[str, Any]) -> P2ReplayPoint:
    return P2ReplayPoint(
        exchange_timestamp_ms=_timestamp_ms(row.get("exchange_timestamp")),
        local_receive_timestamp_ms=_timestamp_ms(row.get("local_receive_timestamp")),
        source_sequence=int(row.get("source_sequence") or 0),
        trade_price=_positive_float(row.get("trade_price")),
        trade_qty=_nonnegative_int(row.get("trade_qty")),
        best_bid=_positive_float(row.get("best_bid")),
        best_ask=_positive_float(row.get("best_ask")),
        quote_age_ms=_finite_float(row.get("quote_age_ms")),
        aggressor_side=str(row.get("aggressor_side") or "UNKNOWN").upper(),
    )


def _fresh_market_bbo(row: Mapping[str, Any], *, max_quote_age_ms: int) -> bool:
    bid = _positive_float(row.get("best_bid"))
    ask = _positive_float(row.get("best_ask"))
    quote_age_ms = _finite_float(row.get("quote_age_ms"))
    return bool(
        bid is not None
        and ask is not None
        and ask >= bid
        and quote_age_ms is not None
        and 0 <= quote_age_ms <= max_quote_age_ms
    )


def _confirmation_fixed_followthrough_outcomes(
    *,
    accepted: Sequence[Mapping[str, Any]],
    rejected_at_ms: Sequence[int],
    event_sequence: int,
    confirmation_deadline_ms: int,
    direction_state: str,
    classification_eligible: bool,
    verified_roundtrip_cost_bps: float | None,
    config: BridgeConfig,
) -> list[dict[str, Any]]:
    entry = next(
        (
            row
            for row in accepted
            if confirmation_deadline_ms
            <= _timestamp_ms(row.get("local_receive_timestamp"))
            <= confirmation_deadline_ms + config.max_outcome_endpoint_lag_ms
            and _fresh_market_bbo(row, max_quote_age_ms=config.max_quote_age_ms)
        ),
        None,
    )
    entry_ms = (
        None if entry is None else _timestamp_ms(entry.get("local_receive_timestamp"))
    )
    entry_ask = None if entry is None else _positive_float(entry.get("best_ask"))
    results: list[dict[str, Any]] = []
    for followthrough_sec in config.reversion_followthrough_horizons_sec:
        target_ms = confirmation_deadline_ms + followthrough_sec * 1_000
        raw_marker = next(
            (
                row
                for row in accepted
                if _timestamp_ms(row.get("local_receive_timestamp")) >= target_ms
            ),
            None,
        )
        raw_marker_ms = (
            None
            if raw_marker is None
            else _timestamp_ms(raw_marker.get("local_receive_timestamp"))
        )
        rejected_marker_ms = next(
            (value for value in sorted(rejected_at_ms) if value >= target_ms),
            None,
        )
        maturity_boundary_ms = (
            raw_marker_ms if raw_marker_ms is not None else rejected_marker_ms
        )
        mature = maturity_boundary_ms is not None
        endpoint = next(
            (
                row
                for row in accepted
                if target_ms
                <= _timestamp_ms(row.get("local_receive_timestamp"))
                <= target_ms + config.max_outcome_endpoint_lag_ms
                and _fresh_market_bbo(
                    row,
                    max_quote_age_ms=config.max_quote_age_ms,
                )
            ),
            None,
        )
        endpoint_ms = (
            None
            if endpoint is None
            else _timestamp_ms(endpoint.get("local_receive_timestamp"))
        )
        continuity_boundary_ms = (
            endpoint_ms if endpoint_ms is not None else maturity_boundary_ms
        )
        bounded_rows = [
            row
            for row in accepted
            if continuity_boundary_ms is not None
            and _timestamp_ms(row.get("local_receive_timestamp"))
            <= continuity_boundary_ms
        ]
        source_findings = set(
            _series_sequence_findings(bounded_rows, prefix="confirmation_followthrough")
        )
        if bounded_rows and int(bounded_rows[0].get("source_sequence") or 0) != (
            event_sequence + 1
        ):
            source_findings.add("confirmation_followthrough_anchor_sequence_gap")
        if continuity_boundary_ms is not None and any(
            value <= continuity_boundary_ms for value in rejected_at_ms
        ):
            source_findings.add("confirmation_followthrough_invalid_market_row_in_path")
        if not mature:
            source_findings.add("confirmation_followthrough_horizon_immature")
        if entry is None or entry_ms is None or entry_ask is None:
            source_findings.add("confirmation_signal_fresh_ask_missing")
        if endpoint is None or endpoint_ms is None:
            source_findings.add("confirmation_followthrough_fresh_bid_missing")
        bbo_path = [
            row
            for row in accepted
            if entry_ms is not None
            and endpoint_ms is not None
            and entry_ms
            <= _timestamp_ms(row.get("local_receive_timestamp"))
            <= endpoint_ms
            and _fresh_market_bbo(row, max_quote_age_ms=config.max_quote_age_ms)
        ]
        bbo_times = [
            _timestamp_ms(row.get("local_receive_timestamp")) for row in bbo_path
        ]
        max_bbo_gap_ms = max(
            (
                right - left
                for left, right in zip(bbo_times, bbo_times[1:], strict=False)
            ),
            default=None,
        )
        if (
            bbo_path
            and len(bbo_path) > 1
            and max_bbo_gap_ms is not None
            and max_bbo_gap_ms > config.max_outcome_internal_gap_ms
        ):
            source_findings.add("confirmation_followthrough_bbo_internal_gap")
        tuning_blockers = set(source_findings)
        if direction_state != "REVERSION_CONFIRMED" or not classification_eligible:
            tuning_blockers.add("reversion_confirmation_not_eligible")
        if verified_roundtrip_cost_bps is None:
            tuning_blockers.add("verified_roundtrip_cost_unavailable")
        gross_returns = (
            []
            if entry_ask is None
            else [
                (float(row["best_bid"]) / entry_ask - 1.0) * 10_000.0
                for row in bbo_path
                if _positive_float(row.get("best_bid")) is not None
            ]
        )
        terminal_bid = (
            None if endpoint is None else _positive_float(endpoint.get("best_bid"))
        )
        gross_return_bps = (
            None
            if entry_ask is None or terminal_bid is None
            else (terminal_bid / entry_ask - 1.0) * 10_000.0
        )
        tuning_outcome_eligible = bool(
            not tuning_blockers
            and gross_return_bps is not None
            and gross_returns
            and verified_roundtrip_cost_bps is not None
        )
        results.append(
            {
                "followthrough_sec": followthrough_sec,
                "mature": mature,
                "entry_observed_at_ms": entry_ms,
                "entry_delay_from_confirmation_ms": (
                    None if entry_ms is None else entry_ms - confirmation_deadline_ms
                ),
                "entry_best_ask": entry_ask,
                "endpoint_observed_at_ms": endpoint_ms,
                "endpoint_lag_ms": (
                    None if endpoint_ms is None else endpoint_ms - target_ms
                ),
                "endpoint_best_bid": terminal_bid,
                "fresh_bbo_observation_count": len(bbo_path),
                "max_fresh_bbo_gap_ms": max_bbo_gap_ms,
                "standardized_one_share_gross_return_bps": (
                    None if gross_return_bps is None else round(gross_return_bps, 6)
                ),
                "verified_roundtrip_cost_bps": verified_roundtrip_cost_bps,
                "standardized_one_share_net_return_bps": (
                    None
                    if not tuning_outcome_eligible
                    or gross_return_bps is None
                    or verified_roundtrip_cost_bps is None
                    else round(
                        gross_return_bps - verified_roundtrip_cost_bps,
                        6,
                    )
                ),
                "standardized_one_share_net_mfe_bps": (
                    None
                    if not tuning_outcome_eligible
                    or not gross_returns
                    or verified_roundtrip_cost_bps is None
                    else round(
                        max(gross_returns) - verified_roundtrip_cost_bps,
                        6,
                    )
                ),
                "standardized_one_share_net_mae_bps": (
                    None
                    if not tuning_outcome_eligible
                    or not gross_returns
                    or verified_roundtrip_cost_bps is None
                    else round(
                        min(gross_returns) - verified_roundtrip_cost_bps,
                        6,
                    )
                ),
                "tuning_outcome_eligible": tuning_outcome_eligible,
                "source_quality_blockers": sorted(source_findings),
                "tuning_outcome_blockers": sorted(tuning_blockers),
            }
        )
    return results


def _confirmation_window_outcome_axis(
    *,
    evidence: Mapping[str, Any],
    market_rows: Sequence[Mapping[str, Any]],
    config: BridgeConfig,
) -> dict[str, Any] | None:
    """Label 120/180-second shock response for offline tuning only."""

    event = evidence.get("event")
    event = event if isinstance(event, Mapping) else {}
    event_ms = _nonnegative_int(event.get("event_detected_at_ms"))
    event_sequence = _nonnegative_int(event.get("event_source_sequence"))
    reference_price = _positive_float(event.get("reference_price"))
    shock_price = _positive_float(event.get("shock_price"))
    shock_bps = _finite_float(event.get("shock_bps"))
    epoch = _nonnegative_int(evidence.get("sequence_epoch"))
    if (
        event_ms is None
        or event_ms <= 0
        or event_sequence is None
        or event_sequence <= 0
        or reference_price is None
        or shock_price is None
        or shock_bps is None
        or shock_bps > 0
        or epoch is None
        or epoch <= 0
    ):
        return None
    symbol = normalize_symbol(evidence.get("stock_code"))
    venue = normalize_venue(evidence.get("micro_venue"))
    session = _session(evidence.get("micro_session_bucket"))
    horizons_sec = config.reversion_confirmation_horizons_sec
    confirmation_fraction = float(config.reversion_confirmation_fraction)
    economics = evidence.get("economics")
    economics = economics if isinstance(economics, Mapping) else {}
    cost_components = tuple(
        _finite_float(economics.get(field))
        for field in (
            "buy_fee_bps",
            "sell_fee_bps",
            "statutory_sell_tax_bps",
            "uncertainty_buffer_bps",
        )
    )
    verified_roundtrip_cost_bps = (
        sum(float(value) for value in cost_components if value is not None)
        if economics.get("cost_profile_verified") is True
        and all(value is not None for value in cost_components)
        else None
    )
    upper_ms = (
        event_ms
        + (horizons_sec[-1] + config.reversion_followthrough_horizons_sec[-1]) * 1_000
        + config.max_outcome_endpoint_lag_ms
    )
    accepted: list[Mapping[str, Any]] = []
    rejected_at_ms: list[int] = []
    for row in market_rows:
        if _scope_key(row) != (symbol, venue, session, epoch):
            continue
        try:
            received_ms = _timestamp_ms(row.get("local_receive_timestamp"))
        except (TypeError, ValueError):
            continue
        if not event_ms < received_ms <= upper_ms:
            continue
        valid, _ = _valid_market_row(row)
        if not valid:
            rejected_at_ms.append(received_ms)
            continue
        accepted.append(row)
    accepted.sort(
        key=lambda row: (
            _timestamp_us(row.get("local_receive_timestamp")),
            int(row.get("source_sequence") or 0),
        )
    )
    context = ShockOnsetContext(
        shock_event_id=str(event.get("shock_event_id") or "offline-reconstructed"),
        symbol=symbol,
        venue=venue,
        session_bucket=session,
        sequence_epoch=epoch,
        shock_horizon_ms=int(event.get("shock_horizon_ms") or 1),
        event_exchange_timestamp_ms=event_ms,
        event_local_receive_timestamp_ms=event_ms,
        event_source_sequence=event_sequence,
        reference_price=reference_price,
        shock_price=shock_price,
        shock_return_bps=shock_bps,
        trigger_trade_qty=None,
        trigger_aggressor_side=None,
        trigger_basis=ShockTriggerBasis.UNKNOWN_RECONSTRUCTED,
    )
    try:
        report = analyze_confirmation_window(
            tuple(_p2_point(row) for row in accepted),
            context=context,
            horizons_ms=tuple(horizon * 1_000 for horizon in horizons_sec),
            confirmation_fraction=confirmation_fraction,
            max_terminal_trade_lag_ms=config.max_outcome_endpoint_lag_ms,
            max_quote_age_ms=config.max_quote_age_ms,
        )
    except (TypeError, ValueError):
        report = None
    observations: list[dict[str, Any]] = []
    for horizon_sec in horizons_sec:
        horizon_ms = horizon_sec * 1_000
        horizon = (
            None
            if report is None
            else next(row for row in report if row.horizon_ms == horizon_ms)
        )
        deadline_ms = event_ms + horizon_ms
        marker = next(
            (
                row
                for row in accepted
                if _timestamp_ms(row.get("local_receive_timestamp")) >= deadline_ms
            ),
            None,
        )
        marker_ms = (
            None
            if marker is None
            else _timestamp_ms(marker.get("local_receive_timestamp"))
        )
        rejected_marker_ms = next(
            (value for value in sorted(rejected_at_ms) if value >= deadline_ms),
            None,
        )
        maturity_boundary_ms = (
            marker_ms if marker_ms is not None else rejected_marker_ms
        )
        bounded_rows = [
            row
            for row in accepted
            if maturity_boundary_ms is not None
            and _timestamp_ms(row.get("local_receive_timestamp"))
            <= maturity_boundary_ms
        ]
        findings = set(_series_sequence_findings(bounded_rows, prefix="confirmation"))
        if bounded_rows and int(bounded_rows[0].get("source_sequence") or 0) != (
            event_sequence + 1
        ):
            findings.add("confirmation_anchor_sequence_gap")
        if maturity_boundary_ms is not None and any(
            value <= maturity_boundary_ms for value in rejected_at_ms
        ):
            findings.add("confirmation_invalid_market_row_in_path")
        if report is None:
            findings.add("confirmation_path_reconstruction_failed")
        elif horizon is not None and horizon.direction_state.value == "SOURCE_GAP":
            findings.add("confirmation_endpoint_missing_or_stale")
        direction_state = (
            "SOURCE_GAP"
            if findings
            else ("DATA_WAIT" if horizon is None else horizon.direction_state.value)
        )
        mature = bool(
            (horizon is not None and horizon.mature) or rejected_marker_ms is not None
        )
        classification_eligible = bool(
            horizon is not None
            and mature
            and not findings
            and direction_state in {"REVERSION_CONFIRMED", "CONTINUATION_CONFIRMED"}
        )
        fixed_followthrough_outcomes = _confirmation_fixed_followthrough_outcomes(
            accepted=accepted,
            rejected_at_ms=rejected_at_ms,
            event_sequence=event_sequence,
            confirmation_deadline_ms=deadline_ms,
            direction_state=direction_state,
            classification_eligible=classification_eligible,
            verified_roundtrip_cost_bps=verified_roundtrip_cost_bps,
            config=config,
        )
        observations.append(
            {
                "horizon_sec": horizon_sec,
                "confirmation_fraction": confirmation_fraction,
                "mature": mature,
                "classification_eligible": classification_eligible,
                "post_trade_count": 0 if horizon is None else horizon.post_trade_count,
                "additional_mae_bps": (
                    None if horizon is None else horizon.additional_mae_bps
                ),
                "post_low_delay_ms": (
                    None if horizon is None else horizon.post_low_delay_ms
                ),
                "terminal_trade_return_bps": (
                    None if horizon is None else horizon.terminal_trade_return_bps
                ),
                "max_reclaim_from_post_low_bps": (
                    None if horizon is None else horizon.max_reclaim_from_post_low_bps
                ),
                "half_reclaim_confirmed": bool(
                    horizon is not None and horizon.half_reclaim_confirmed
                ),
                "confirmation_count": (
                    0 if horizon is None else horizon.confirmation_count
                ),
                "recovery_invalidation_count": (
                    0 if horizon is None else horizon.recovery_invalidation_count
                ),
                "active_confirmation_delay_ms": (
                    None if horizon is None else horizon.active_confirmation_delay_ms
                ),
                "active_confirmation_trade_price": (
                    None if horizon is None else horizon.active_confirmation_trade_price
                ),
                "active_confirmation_best_ask": (
                    None if horizon is None else horizon.active_confirmation_best_ask
                ),
                "active_confirmation_quote_age_ms": (
                    None
                    if horizon is None
                    else horizon.active_confirmation_quote_age_ms
                ),
                "confirmation_followthrough_ms": (
                    None if horizon is None else horizon.confirmation_followthrough_ms
                ),
                "confirmation_followthrough_trade_count": (
                    0
                    if horizon is None
                    else horizon.confirmation_followthrough_trade_count
                ),
                "confirmation_fresh_bbo_count": (
                    0 if horizon is None else horizon.confirmation_fresh_bbo_count
                ),
                "confirmation_to_terminal_trade_return_bps": (
                    None
                    if horizon is None
                    else horizon.confirmation_to_terminal_trade_return_bps
                ),
                "confirmation_to_terminal_trade_mfe_bps": (
                    None
                    if horizon is None
                    else horizon.confirmation_to_terminal_trade_mfe_bps
                ),
                "confirmation_to_terminal_trade_mae_bps": (
                    None
                    if horizon is None
                    else horizon.confirmation_to_terminal_trade_mae_bps
                ),
                "confirmation_to_terminal_bbo_proxy_gross_return_bps": (
                    None
                    if horizon is None
                    else horizon.confirmation_to_terminal_bbo_proxy_gross_return_bps
                ),
                "confirmation_to_terminal_bbo_proxy_mfe_bps": (
                    None
                    if horizon is None
                    else horizon.confirmation_to_terminal_bbo_proxy_mfe_bps
                ),
                "confirmation_to_terminal_bbo_proxy_mae_bps": (
                    None
                    if horizon is None
                    else horizon.confirmation_to_terminal_bbo_proxy_mae_bps
                ),
                "fixed_followthrough_outcomes": fixed_followthrough_outcomes,
                "terminal_trade_lag_ms": (
                    None if horizon is None else horizon.terminal_trade_lag_ms
                ),
                "direction_state": direction_state,
                "source_quality_blockers": sorted(findings),
            }
        )
    return {
        "schema": CONFIRMATION_WINDOW_SCHEMA,
        "axis_role": "micro_reversion_tuning_only",
        "horizons_sec": list(horizons_sec),
        "followthrough_horizons_sec": list(config.reversion_followthrough_horizons_sec),
        "confirmation_fraction": confirmation_fraction,
        "max_endpoint_lag_ms": config.max_outcome_endpoint_lag_ms,
        "max_internal_gap_ms": config.max_outcome_internal_gap_ms,
        "max_quote_age_ms": config.max_quote_age_ms,
        "outcome_basis": (
            "standardized_one_share_confirmation_deadline_fresh_ask_to_fixed_"
            "followthrough_fresh_bid_top_of_book_proxy_"
            "after_verified_roundtrip_cost"
        ),
        "observations": observations,
        "included_in_prompt_context": False,
        **CONFIRMATION_WINDOW_METRIC_CONTRACT,
        **AUTHORITY_CONTRACT,
    }


def _validate_confirmation_window_axis(
    axis: Mapping[str, Any] | None,
    *,
    expected_horizons_sec: tuple[int, ...] | None = None,
    expected_followthrough_horizons_sec: tuple[int, ...] | None = None,
    expected_confirmation_fraction: float | None = None,
    expected_max_endpoint_lag_ms: int | None = None,
    expected_max_internal_gap_ms: int | None = None,
    expected_max_quote_age_ms: int | None = None,
) -> None:
    if axis is None:
        return
    allowed_fields = {
        "schema",
        "axis_role",
        "horizons_sec",
        "followthrough_horizons_sec",
        "confirmation_fraction",
        "max_endpoint_lag_ms",
        "max_internal_gap_ms",
        "max_quote_age_ms",
        "outcome_basis",
        "observations",
        "included_in_prompt_context",
        *CONFIRMATION_WINDOW_METRIC_CONTRACT,
        *AUTHORITY_CONTRACT,
    }
    if (
        set(axis) != allowed_fields
        or axis.get("schema") != CONFIRMATION_WINDOW_SCHEMA
        or axis.get("axis_role") != "micro_reversion_tuning_only"
        or axis.get("included_in_prompt_context") is not False
        or axis.get("outcome_basis")
        != (
            "standardized_one_share_confirmation_deadline_fresh_ask_to_fixed_"
            "followthrough_fresh_bid_top_of_book_proxy_"
            "after_verified_roundtrip_cost"
        )
    ):
        raise ValueError("micro_confirmation_window_contract_invalid")
    for field, expected in CONFIRMATION_WINDOW_METRIC_CONTRACT.items():
        if _sha256(axis.get(field)) != _sha256(expected):
            raise ValueError(f"micro_confirmation_window_metric_invalid:{field}")
    for field, expected in AUTHORITY_CONTRACT.items():
        if axis.get(field) is not expected:
            raise ValueError(f"micro_confirmation_window_authority_invalid:{field}")
    horizons_sec = axis.get("horizons_sec")
    followthrough_horizons_sec = axis.get("followthrough_horizons_sec")
    confirmation_fraction = axis.get("confirmation_fraction")
    max_endpoint_lag_ms = axis.get("max_endpoint_lag_ms")
    max_internal_gap_ms = axis.get("max_internal_gap_ms")
    max_quote_age_ms = axis.get("max_quote_age_ms")
    observations = axis.get("observations")
    if (
        not isinstance(horizons_sec, list)
        or not horizons_sec
        or tuple(sorted(set(horizons_sec))) != tuple(horizons_sec)
        or any(
            isinstance(value, bool) or not isinstance(value, int) or value <= 0
            for value in horizons_sec
        )
        or (
            expected_horizons_sec is not None
            and tuple(horizons_sec) != expected_horizons_sec
        )
        or not isinstance(followthrough_horizons_sec, list)
        or not followthrough_horizons_sec
        or tuple(sorted(set(followthrough_horizons_sec)))
        != tuple(followthrough_horizons_sec)
        or any(
            isinstance(value, bool) or not isinstance(value, int) or value <= 0
            for value in followthrough_horizons_sec
        )
        or (
            expected_followthrough_horizons_sec is not None
            and tuple(followthrough_horizons_sec) != expected_followthrough_horizons_sec
        )
        or not isinstance(observations, list)
        or len(observations) != len(horizons_sec)
        or isinstance(confirmation_fraction, bool)
        or not isinstance(confirmation_fraction, (int, float))
        or not math.isfinite(float(confirmation_fraction))
        or not 0 < float(confirmation_fraction) <= 1
        or (
            expected_confirmation_fraction is not None
            and not math.isclose(
                float(confirmation_fraction),
                float(expected_confirmation_fraction),
                rel_tol=0.0,
                abs_tol=1e-12,
            )
        )
        or isinstance(max_endpoint_lag_ms, bool)
        or not isinstance(max_endpoint_lag_ms, int)
        or max_endpoint_lag_ms < 0
        or (
            expected_max_endpoint_lag_ms is not None
            and max_endpoint_lag_ms != expected_max_endpoint_lag_ms
        )
        or isinstance(max_internal_gap_ms, bool)
        or not isinstance(max_internal_gap_ms, int)
        or max_internal_gap_ms <= 0
        or (
            expected_max_internal_gap_ms is not None
            and max_internal_gap_ms != expected_max_internal_gap_ms
        )
        or isinstance(max_quote_age_ms, bool)
        or not isinstance(max_quote_age_ms, int)
        or max_quote_age_ms < 0
        or (
            expected_max_quote_age_ms is not None
            and max_quote_age_ms != expected_max_quote_age_ms
        )
    ):
        raise ValueError("micro_confirmation_window_horizons_invalid")
    observation_fields = {
        "horizon_sec",
        "confirmation_fraction",
        "mature",
        "classification_eligible",
        "post_trade_count",
        "additional_mae_bps",
        "post_low_delay_ms",
        "terminal_trade_return_bps",
        "max_reclaim_from_post_low_bps",
        "half_reclaim_confirmed",
        "confirmation_count",
        "recovery_invalidation_count",
        "active_confirmation_delay_ms",
        "active_confirmation_trade_price",
        "active_confirmation_best_ask",
        "active_confirmation_quote_age_ms",
        "confirmation_followthrough_ms",
        "confirmation_followthrough_trade_count",
        "confirmation_fresh_bbo_count",
        "confirmation_to_terminal_trade_return_bps",
        "confirmation_to_terminal_trade_mfe_bps",
        "confirmation_to_terminal_trade_mae_bps",
        "confirmation_to_terminal_bbo_proxy_gross_return_bps",
        "confirmation_to_terminal_bbo_proxy_mfe_bps",
        "confirmation_to_terminal_bbo_proxy_mae_bps",
        "fixed_followthrough_outcomes",
        "terminal_trade_lag_ms",
        "direction_state",
        "source_quality_blockers",
    }
    direction_states = {
        "DATA_WAIT",
        "SOURCE_GAP",
        "REVERSION_CONFIRMED",
        "CONTINUATION_CONFIRMED",
        "INCONCLUSIVE",
    }
    optional_float_fields = {
        "additional_mae_bps",
        "terminal_trade_return_bps",
        "max_reclaim_from_post_low_bps",
        "active_confirmation_trade_price",
        "active_confirmation_best_ask",
        "active_confirmation_quote_age_ms",
        "confirmation_to_terminal_trade_return_bps",
        "confirmation_to_terminal_trade_mfe_bps",
        "confirmation_to_terminal_trade_mae_bps",
        "confirmation_to_terminal_bbo_proxy_gross_return_bps",
        "confirmation_to_terminal_bbo_proxy_mfe_bps",
        "confirmation_to_terminal_bbo_proxy_mae_bps",
    }
    optional_nonnegative_int_fields = {
        "post_low_delay_ms",
        "active_confirmation_delay_ms",
        "confirmation_followthrough_ms",
        "terminal_trade_lag_ms",
    }
    for expected_horizon, observation in zip(horizons_sec, observations, strict=True):
        blockers = (
            observation.get("source_quality_blockers")
            if isinstance(observation, Mapping)
            else None
        )
        fixed_outcomes = (
            observation.get("fixed_followthrough_outcomes")
            if isinstance(observation, Mapping)
            else None
        )
        if (
            not isinstance(observation, Mapping)
            or set(observation) != observation_fields
            or observation.get("horizon_sec") != expected_horizon
            or not math.isclose(
                float(observation.get("confirmation_fraction") or 0.0),
                float(confirmation_fraction),
                rel_tol=0.0,
                abs_tol=1e-12,
            )
            or observation.get("direction_state") not in direction_states
            or not isinstance(observation.get("mature"), bool)
            or not isinstance(observation.get("classification_eligible"), bool)
            or not isinstance(observation.get("half_reclaim_confirmed"), bool)
            or isinstance(observation.get("post_trade_count"), bool)
            or not isinstance(observation.get("post_trade_count"), int)
            or observation.get("post_trade_count") < 0
            or isinstance(observation.get("confirmation_count"), bool)
            or not isinstance(observation.get("confirmation_count"), int)
            or observation.get("confirmation_count") < 0
            or isinstance(observation.get("recovery_invalidation_count"), bool)
            or not isinstance(observation.get("recovery_invalidation_count"), int)
            or observation.get("recovery_invalidation_count") < 0
            or isinstance(
                observation.get("confirmation_followthrough_trade_count"), bool
            )
            or not isinstance(
                observation.get("confirmation_followthrough_trade_count"), int
            )
            or observation.get("confirmation_followthrough_trade_count") < 0
            or isinstance(observation.get("confirmation_fresh_bbo_count"), bool)
            or not isinstance(observation.get("confirmation_fresh_bbo_count"), int)
            or observation.get("confirmation_fresh_bbo_count") < 0
            or not isinstance(blockers, list)
            or any(not isinstance(value, str) or not value for value in blockers)
            or blockers != sorted(set(blockers))
            or not isinstance(fixed_outcomes, list)
            or len(fixed_outcomes) != len(followthrough_horizons_sec)
            or any(
                value is not None
                and (
                    isinstance(value, bool)
                    or not isinstance(value, (int, float))
                    or not math.isfinite(float(value))
                )
                for value in (observation.get(field) for field in optional_float_fields)
            )
            or any(
                value is not None
                and (isinstance(value, bool) or not isinstance(value, int) or value < 0)
                for value in (
                    observation.get(field) for field in optional_nonnegative_int_fields
                )
            )
        ):
            raise ValueError("micro_confirmation_window_observation_invalid")
        direction_state = observation.get("direction_state")
        expected_eligible = bool(
            observation.get("mature") is True
            and not blockers
            and direction_state in {"REVERSION_CONFIRMED", "CONTINUATION_CONFIRMED"}
        )
        if (
            observation.get("classification_eligible") is not expected_eligible
            or (direction_state == "DATA_WAIT" and observation.get("mature") is True)
            or (direction_state == "DATA_WAIT" and blockers)
            or (direction_state == "SOURCE_GAP" and not blockers)
        ):
            raise ValueError("micro_confirmation_window_eligibility_invalid")
        _validate_fixed_followthrough_outcomes(
            fixed_outcomes,
            expected_horizons_sec=followthrough_horizons_sec,
            reversion_confirmation_eligible=(
                expected_eligible and direction_state == "REVERSION_CONFIRMED"
            ),
        )


def _validate_fixed_followthrough_outcomes(
    outcomes: Sequence[Mapping[str, Any]],
    *,
    expected_horizons_sec: Sequence[int],
    reversion_confirmation_eligible: bool,
) -> None:
    fields = {
        "followthrough_sec",
        "mature",
        "entry_observed_at_ms",
        "entry_delay_from_confirmation_ms",
        "entry_best_ask",
        "endpoint_observed_at_ms",
        "endpoint_lag_ms",
        "endpoint_best_bid",
        "fresh_bbo_observation_count",
        "max_fresh_bbo_gap_ms",
        "standardized_one_share_gross_return_bps",
        "verified_roundtrip_cost_bps",
        "standardized_one_share_net_return_bps",
        "standardized_one_share_net_mfe_bps",
        "standardized_one_share_net_mae_bps",
        "tuning_outcome_eligible",
        "source_quality_blockers",
        "tuning_outcome_blockers",
    }
    optional_numbers = {
        "entry_best_ask",
        "endpoint_best_bid",
        "standardized_one_share_gross_return_bps",
        "verified_roundtrip_cost_bps",
        "standardized_one_share_net_return_bps",
        "standardized_one_share_net_mfe_bps",
        "standardized_one_share_net_mae_bps",
    }
    optional_nonnegative_ints = {
        "entry_observed_at_ms",
        "entry_delay_from_confirmation_ms",
        "endpoint_observed_at_ms",
        "endpoint_lag_ms",
        "max_fresh_bbo_gap_ms",
    }
    for expected_horizon, outcome in zip(expected_horizons_sec, outcomes, strict=True):
        source_blockers = (
            outcome.get("source_quality_blockers")
            if isinstance(outcome, Mapping)
            else None
        )
        tuning_blockers = (
            outcome.get("tuning_outcome_blockers")
            if isinstance(outcome, Mapping)
            else None
        )
        if (
            not isinstance(outcome, Mapping)
            or set(outcome) != fields
            or outcome.get("followthrough_sec") != expected_horizon
            or not isinstance(outcome.get("mature"), bool)
            or not isinstance(outcome.get("tuning_outcome_eligible"), bool)
            or isinstance(outcome.get("fresh_bbo_observation_count"), bool)
            or not isinstance(outcome.get("fresh_bbo_observation_count"), int)
            or outcome.get("fresh_bbo_observation_count") < 0
            or not isinstance(source_blockers, list)
            or source_blockers != sorted(set(source_blockers))
            or any(not isinstance(value, str) or not value for value in source_blockers)
            or not isinstance(tuning_blockers, list)
            or tuning_blockers != sorted(set(tuning_blockers))
            or any(not isinstance(value, str) or not value for value in tuning_blockers)
            or any(
                value is not None
                and (
                    isinstance(value, bool)
                    or not isinstance(value, (int, float))
                    or not math.isfinite(float(value))
                )
                for value in (outcome.get(field) for field in optional_numbers)
            )
            or any(
                outcome.get(field) is not None and outcome.get(field) <= 0
                for field in ("entry_best_ask", "endpoint_best_bid")
            )
            or (
                outcome.get("verified_roundtrip_cost_bps") is not None
                and outcome.get("verified_roundtrip_cost_bps") < 0
            )
            or any(
                value is not None
                and (isinstance(value, bool) or not isinstance(value, int) or value < 0)
                for value in (outcome.get(field) for field in optional_nonnegative_ints)
            )
        ):
            raise ValueError("micro_confirmation_followthrough_outcome_invalid")
        eligible = outcome.get("tuning_outcome_eligible") is True
        expected_eligible = bool(
            reversion_confirmation_eligible
            and outcome.get("mature") is True
            and not source_blockers
            and not tuning_blockers
            and outcome.get("entry_observed_at_ms") is not None
            and outcome.get("entry_best_ask") is not None
            and outcome.get("entry_best_ask") > 0
            and outcome.get("endpoint_observed_at_ms") is not None
            and outcome.get("endpoint_best_bid") is not None
            and outcome.get("endpoint_best_bid") > 0
            and outcome.get("fresh_bbo_observation_count") > 0
            and outcome.get("standardized_one_share_gross_return_bps") is not None
            and outcome.get("verified_roundtrip_cost_bps") is not None
        )
        net_fields = tuple(
            outcome.get(field)
            for field in (
                "standardized_one_share_net_return_bps",
                "standardized_one_share_net_mfe_bps",
                "standardized_one_share_net_mae_bps",
            )
        )
        if (
            eligible is not expected_eligible
            or (eligible and any(value is None for value in net_fields))
            or (not eligible and any(value is not None for value in net_fields))
        ):
            raise ValueError("micro_confirmation_followthrough_eligibility_invalid")
        if eligible:
            gross = float(outcome["standardized_one_share_gross_return_bps"])
            cost = float(outcome["verified_roundtrip_cost_bps"])
            expected_gross = (
                float(outcome["endpoint_best_bid"]) / float(outcome["entry_best_ask"])
                - 1.0
            ) * 10_000.0
            if (
                not math.isclose(gross, expected_gross, abs_tol=1e-6)
                or not math.isclose(
                    float(outcome["standardized_one_share_net_return_bps"]),
                    gross - cost,
                    abs_tol=1e-6,
                )
                or float(outcome["standardized_one_share_net_mfe_bps"])
                < float(outcome["standardized_one_share_net_return_bps"])
                or float(outcome["standardized_one_share_net_mae_bps"])
                > float(outcome["standardized_one_share_net_return_bps"])
            ):
                raise ValueError("micro_confirmation_followthrough_economics_invalid")


def _liquidity_projection(
    *,
    depth: Mapping[str, Any] | None,
    recent_rows: Sequence[Mapping[str, Any]],
    config: BridgeConfig,
) -> dict[str, Any]:
    if depth is None:
        return {
            "capacity_quality_status": "depth_unavailable_not_imputed",
            "counterfactual_liquidity_qty_grid": [],
            "counterfactual_liquidity_qty_ceiling": None,
            "counterfactual_immediate_exit_qty_ceiling": None,
            "snapshot_depth_execution_basis": {
                "bid_levels": [],
                "ask_levels": [],
                "allocator_or_order_quantity_present": False,
            },
        }
    bid_levels = _levels(depth.get("bid_levels"))
    ask_levels = _levels(depth.get("ask_levels"))
    bid_capacity = _capacity_within_slippage(
        bid_levels,
        side="bid",
        max_slippage_bps=config.max_exit_sweep_slippage_bps,
    )
    ask_capacity = _capacity_within_slippage(
        ask_levels,
        side="ask",
        max_slippage_bps=config.max_entry_sweep_slippage_bps,
    )
    aggressive_buy_qty = sum(
        _nonnegative_int(row.get("trade_qty")) or 0
        for row in recent_rows
        if str(row.get("aggressor_side") or "UNKNOWN").upper() == "BUY"
    )
    grid = []
    for participation in config.participation_grid:
        raw_roundtrip_capacity = (
            None
            if bid_capacity is None or ask_capacity is None
            else min(bid_capacity, ask_capacity)
        )
        roundtrip_floor = (
            None
            if raw_roundtrip_capacity is None
            else math.floor(raw_roundtrip_capacity * participation)
        )
        roundtrip_depth_capacity = (
            None
            if roundtrip_floor is None
            else (max(1, roundtrip_floor) if raw_roundtrip_capacity > 0 else 0)
        )
        immediate_exit_floor = (
            None if bid_capacity is None else math.floor(bid_capacity * participation)
        )
        immediate_exit_capacity = (
            None
            if immediate_exit_floor is None
            else max(1, immediate_exit_floor) if bid_capacity > 0 else 0
        )
        passive_ask_fill_support_qty = (
            None
            if aggressive_buy_qty <= 0
            else math.floor(
                aggressive_buy_qty
                / config.tape_capacity_window_sec
                * config.target_liquidation_sec
                * participation
            )
        )
        standardized_probe_qty = (
            1
            if roundtrip_depth_capacity is not None and roundtrip_depth_capacity >= 1
            else None
        )
        entry_vwap = (
            None
            if roundtrip_depth_capacity is None
            else _sweep_vwap(ask_levels, roundtrip_depth_capacity)
        )
        exit_vwap = (
            None
            if roundtrip_depth_capacity is None
            else _sweep_vwap(bid_levels, roundtrip_depth_capacity)
        )
        grid.append(
            {
                "participation_rate": participation,
                "entry_ask_capacity_qty": ask_capacity,
                "depth_only_fast_exit_capacity_qty": bid_capacity,
                "immediate_roundtrip_depth_capacity_qty": (roundtrip_depth_capacity),
                "strict_depth_participation_capacity_qty": roundtrip_floor,
                "immediate_marketable_exit_capacity_qty": (immediate_exit_capacity),
                "one_share_probe_floor_applied": bool(
                    raw_roundtrip_capacity
                    and roundtrip_floor == 0
                    and roundtrip_depth_capacity == 1
                ),
                "immediate_exit_one_share_floor_applied": bool(
                    bid_capacity
                    and immediate_exit_floor == 0
                    and immediate_exit_capacity == 1
                ),
                "passive_ask_fill_support_qty": passive_ask_fill_support_qty,
                "depth_only_roundtrip_capacity_qty": roundtrip_depth_capacity,
                # Compatibility name retained as a depth-only quantity.  It
                # never incorporates payload, allocator, or order quantity.
                "counterfactual_liquidity_bounded_qty": (roundtrip_depth_capacity),
                "standardized_one_share_probe_observation_qty": (
                    standardized_probe_qty
                ),
                "counterfactual_entry_sweep_vwap": entry_vwap,
                "counterfactual_exit_sweep_vwap": exit_vwap,
                "counterfactual_roundtrip_execution_bps": (
                    None
                    if entry_vwap is None or exit_vwap is None
                    else round((entry_vwap / exit_vwap - 1.0) * 10_000.0, 6)
                ),
            }
        )
    conservative = next(
        (row for row in grid if abs(float(row["participation_rate"]) - 0.05) <= 1e-12),
        None,
    )
    ceiling = (
        None
        if conservative is None
        else conservative["depth_only_roundtrip_capacity_qty"]
    )
    exit_ceiling = (
        None
        if conservative is None
        else conservative["immediate_marketable_exit_capacity_qty"]
    )
    return {
        "capacity_quality_status": (
            "immediate_bid_ask_depth_capacity_observed"
            if ceiling is not None
            else "depth_capacity_unavailable"
        ),
        "target_liquidation_sec": config.target_liquidation_sec,
        "recent_tape_window_sec": config.tape_capacity_window_sec,
        "recent_aggressive_buy_qty": (
            aggressive_buy_qty if aggressive_buy_qty > 0 else None
        ),
        "aggressive_buy_role": "passive_ask_exit_support_only_not_bid_sweep_capacity",
        "counterfactual_liquidity_qty_grid": grid,
        "counterfactual_liquidity_qty_ceiling": ceiling,
        "counterfactual_immediate_exit_qty_ceiling": exit_ceiling,
        "standardized_one_share_probe_observation_qty": (
            None
            if conservative is None
            else conservative["standardized_one_share_probe_observation_qty"]
        ),
        "snapshot_depth_execution_basis": {
            "bid_levels": [list(level) for level in bid_levels],
            "ask_levels": [list(level) for level in ask_levels],
            "allocator_or_order_quantity_present": False,
        },
        "quantity_authority_status": "depth_capacity_only_no_order_authority",
    }


def _economics(
    *,
    liquidity: Mapping[str, Any],
    config: BridgeConfig,
    venue: str,
    snapshot_date: str,
    symbol_metadata: Mapping[str, Any],
) -> dict[str, Any]:
    grid = liquidity.get("counterfactual_liquidity_qty_grid")
    grid = grid if isinstance(grid, list) else []
    conservative = next(
        (
            row
            for row in grid
            if isinstance(row, Mapping)
            and abs(float(row.get("participation_rate") or 0.0) - 0.05) <= 1e-12
        ),
        {},
    )
    execution_bps = _finite_float(
        conservative.get("counterfactual_roundtrip_execution_bps")
    )
    normalized_venue = normalize_venue(venue)
    try:
        observed_date = date.fromisoformat(str(snapshot_date or ""))
    except ValueError:
        observed_date = None
    metadata_listing_market = normalize_listing_market(
        symbol_metadata.get("listing_market")
    )
    metadata_instrument_type = normalize_instrument_type(
        symbol_metadata.get("instrument_type")
    )
    metadata_tax_profile = (
        None
        if observed_date is None
        or metadata_listing_market is ListingMarket.UNKNOWN
        or metadata_instrument_type is InstrumentType.UNKNOWN
        else tax_profile_for(
            trade_date=observed_date,
            listing_market=metadata_listing_market,
            instrument_type=metadata_instrument_type,
        )
    )
    resolved_profile = _resolved_cost_profile(
        config=config,
        observed_date=observed_date,
        venue=normalized_venue,
        symbol_metadata=symbol_metadata,
    )
    try:
        effective_date = (
            None
            if resolved_profile is None
            else date.fromisoformat(str(resolved_profile.get("effective_from") or ""))
        )
    except ValueError:
        effective_date = None
    resolved_tax_bps = (
        None
        if resolved_profile is None
        else _finite_float(resolved_profile.get("statutory_sell_tax_bps"))
    )
    tax_scope_matches = bool(
        metadata_tax_profile is not None
        and resolved_tax_bps is not None
        and metadata_tax_profile.statutory_sell_tax_bps == resolved_tax_bps
        and metadata_tax_profile.instrument_tax_class.value
        == symbol_metadata.get("instrument_tax_class")
    )
    verified_scope_applicable = bool(
        config.cost_profile_verified
        and observed_date is not None
        and effective_date is not None
        and observed_date >= effective_date
        and resolved_profile is not None
        and normalized_venue in (resolved_profile.get("venues") or [])
        and symbol_metadata.get("symbol_metadata_status") == "verified"
        and symbol_metadata.get("instrument_type") == InstrumentType.EQUITY.value
        and tax_scope_matches
    )
    resolved_buy_fee_bps = (
        None
        if resolved_profile is None
        else _finite_float(resolved_profile.get("buy_fee_bps"))
    )
    resolved_sell_fee_bps = (
        None
        if resolved_profile is None
        else _finite_float(resolved_profile.get("sell_fee_bps"))
    )
    resolved_uncertainty_bps = (
        None
        if resolved_profile is None
        else _finite_float(resolved_profile.get("uncertainty_buffer_bps"))
    )
    cost_ready = all(
        value is not None
        for value in (
            resolved_buy_fee_bps,
            resolved_sell_fee_bps,
            resolved_tax_bps,
            resolved_uncertainty_bps,
        )
    )
    fixed_cost = (
        None
        if not cost_ready
        else float(resolved_buy_fee_bps)
        + float(resolved_sell_fee_bps)
        + float(resolved_tax_bps)
        + float(resolved_uncertainty_bps)
    )
    all_in = (
        None
        if fixed_cost is None or execution_bps is None
        else fixed_cost + execution_bps
    )
    return {
        "cost_profile_source": config.cost_profile_source,
        "cost_profile_verified": verified_scope_applicable,
        "cost_profile_contract_verified": config.cost_profile_verified,
        "cost_profile_tax_scope_match": tax_scope_matches,
        "cost_profile_scope_status": (
            "reviewed_artifact_applicable"
            if verified_scope_applicable
            else (
                "reviewed_artifact_instrument_type_unverified_or_not_covered"
                if config.cost_profile_verified
                and (
                    symbol_metadata.get("symbol_metadata_status") != "verified"
                    or symbol_metadata.get("instrument_type")
                    != InstrumentType.EQUITY.value
                )
                else (
                    "reviewed_artifact_instrument_tax_scope_mismatch"
                    if config.cost_profile_verified and not tax_scope_matches
                    else (
                        "reviewed_artifact_not_applicable_to_venue_or_date"
                        if config.cost_profile_verified
                        else "unverified_research_cost_profile"
                    )
                )
            )
        ),
        "symbol_metadata_status": symbol_metadata.get("symbol_metadata_status"),
        "symbol_metadata_record_sha256": symbol_metadata.get(
            "symbol_metadata_record_sha256"
        ),
        "symbol_master_artifact_sha256": symbol_metadata.get(
            "symbol_master_artifact_sha256"
        ),
        "symbol_metadata_source": symbol_metadata.get("symbol_metadata_source"),
        "symbol_metadata_source_reference": symbol_metadata.get(
            "symbol_metadata_source_reference"
        ),
        "symbol_metadata_verified_at": symbol_metadata.get(
            "symbol_metadata_verified_at"
        ),
        "listing_market": symbol_metadata.get("listing_market"),
        "instrument_type": symbol_metadata.get("instrument_type"),
        "instrument_tax_class": symbol_metadata.get("instrument_tax_class"),
        "cost_profile_artifact_id": config.cost_profile_artifact_id or None,
        "cost_profile_artifact_sha256": (config.cost_profile_artifact_sha256 or None),
        "cost_profile_effective_date": (
            None if resolved_profile is None else resolved_profile.get("effective_from")
        ),
        "cost_profile_venues": (
            []
            if resolved_profile is None
            else list(resolved_profile.get("venues") or [])
        ),
        "cost_catalog_content_sha256": (
            config.cost_profile_catalog_content_sha256 or None
        ),
        "selected_cost_profile_id": (
            None if resolved_profile is None else resolved_profile.get("profile_id")
        ),
        "selected_cost_profile_content_sha256": (
            None
            if resolved_profile is None
            else resolved_profile.get("content_sha256")
            or resolved_profile.get("profile_content_sha256")
        ),
        "buy_fee_bps": resolved_buy_fee_bps if cost_ready else None,
        "sell_fee_bps": resolved_sell_fee_bps if cost_ready else None,
        "statutory_sell_tax_bps": resolved_tax_bps,
        "uncertainty_buffer_bps": (resolved_uncertainty_bps if cost_ready else None),
        "counterfactual_roundtrip_execution_bps": execution_bps,
        "spread_double_counted": False,
        "all_in_cost_bps": None if all_in is None else round(all_in, 6),
        "minimum_net_profit_bps": config.minimum_net_profit_bps,
        "minimum_gross_target_bps": (
            None if all_in is None else round(all_in + config.minimum_net_profit_bps, 6)
        ),
        "economic_source_quality_status": (
            "verified_cost_profile"
            if cost_ready and verified_scope_applicable
            else (
                "research_cost_assumption_not_promotion_grade"
                if cost_ready
                else "cost_profile_unavailable_no_net_target"
            )
        ),
    }


def _nested_value(source: Any, path: Sequence[str]) -> Any:
    current = source
    for key in path:
        if not isinstance(current, Mapping):
            return None
        current = current.get(key)
    return current


def _position_context(
    payload: Mapping[str, Any], *, max_broker_position_age_sec: float
) -> dict[str, Any]:
    source = _stored_replay_exact_payload(payload)
    roots = [source] if isinstance(source, Mapping) else []
    nested_exact = source.get("exact_payload") if isinstance(source, Mapping) else None
    if isinstance(nested_exact, Mapping):
        roots.append(nested_exact)
    contexts: list[Mapping[str, Any]] = []
    for root in roots:
        if root.get("schema") == HOLDING_CONTEXT_SCHEMA:
            contexts.append(root)
        candidate = root.get("holding_decision_context")
        if isinstance(candidate, Mapping) and candidate.get("schema") == (
            HOLDING_CONTEXT_SCHEMA
        ):
            contexts.append(candidate)
    contexts_by_hash = {_sha256(context): context for context in contexts}
    if len(contexts_by_hash) != 1:
        return {
            "status": "canonical_position_context_unavailable",
            "quantity": None,
            "free_to_sell_quantity": None,
            "average_price": None,
            "quantity_pointer": None,
            "price_pointer": None,
        }
    context = next(iter(contexts_by_hash.values()))
    execution = context.get("execution_pnl")
    execution = execution if isinstance(execution, Mapping) else {}
    lifecycle = context.get("position_lifecycle")
    lifecycle = lifecycle if isinstance(lifecycle, Mapping) else {}
    reconciliation = context.get("order_reconciliation")
    reconciliation = reconciliation if isinstance(reconciliation, Mapping) else {}
    source_quality = context.get("source_quality")
    source_quality = source_quality if isinstance(source_quality, Mapping) else {}
    candidate_exit_rule = ""
    active_hard_guard = ""
    for root in roots:
        decision_type = root.get("decision_type")
        guard_state = root.get("deterministic_guard_state")
        hard_guard_context = root.get("hard_guard_context")
        decision_type = decision_type if isinstance(decision_type, Mapping) else {}
        guard_state = guard_state if isinstance(guard_state, Mapping) else {}
        hard_guard_context = (
            hard_guard_context if isinstance(hard_guard_context, Mapping) else {}
        )
        candidate_exit_rule = (
            candidate_exit_rule
            or str(
                decision_type.get("candidate_exit_rule")
                or guard_state.get("candidate_exit_rule")
                or ""
            ).strip()
        )
        active_hard_guard = (
            active_hard_guard
            or str(hard_guard_context.get("active_hard_guard") or "").strip()
        )
    hard_exit_guard_observed = any(
        token in f"{candidate_exit_rule} {active_hard_guard}".lower()
        for token in ("hard", "protect", "emergency", "mandatory")
    )
    remaining_qty = _nonnegative_int(execution.get("remaining_qty"))
    broker_qty = _nonnegative_int(lifecycle.get("broker_qty"))
    memory_qty = _nonnegative_int(lifecycle.get("memory_qty"))
    quantity_candidates = [
        quantity
        for quantity in (broker_qty, remaining_qty, memory_qty)
        if quantity is not None
    ]
    quantity = quantity_candidates[0] if quantity_candidates else None
    quantity_conflict = bool(
        reconciliation.get("quantity_mismatch") is True
        or reconciliation.get("order_or_quantity_conflict") is True
        or len(set(quantity_candidates)) > 1
    )
    open_sell_qty = _nonnegative_int(reconciliation.get("open_sell_qty"))
    reconciliation_contract_complete = bool(
        broker_qty is not None
        and open_sell_qty is not None
        and isinstance(reconciliation.get("cancel_pending"), bool)
        and isinstance(reconciliation.get("exit_token_active"), bool)
        and isinstance(reconciliation.get("quantity_mismatch"), bool)
        and isinstance(reconciliation.get("order_or_quantity_conflict"), bool)
    )
    broker_snapshot_age_sec = _finite_float(
        reconciliation.get("broker_snapshot_age_sec")
    )
    position_reconciled = source_quality.get("position_reconciled") is True
    position_authority_reconciled = (
        source_quality.get("position_authority_reconciled") is True
    )
    simulation_position_reconciled = (
        source_quality.get("simulation_position_reconciled") is True
    )
    reconciliation_mode = str(
        source_quality.get("position_reconciliation_mode") or ""
    ).strip()
    broker_position_fresh = bool(
        broker_snapshot_age_sec is not None
        and 0.0 <= broker_snapshot_age_sec <= max_broker_position_age_sec
    )
    position_execution_eligible = bool(
        reconciliation_contract_complete
        and position_reconciled
        and position_authority_reconciled
        and not simulation_position_reconciled
        and reconciliation_mode != "simulation_book"
        and broker_position_fresh
    )
    explicit_order_conflict = bool(
        reconciliation.get("cancel_pending") is True
        or reconciliation.get("exit_token_active") is True
        or quantity_conflict
        or (
            quantity is not None
            and open_sell_qty is not None
            and open_sell_qty > quantity
        )
    )
    order_conflict = bool(not position_execution_eligible or explicit_order_conflict)
    free_to_sell_qty = (
        None
        if quantity is None or order_conflict or open_sell_qty > quantity
        else max(0, quantity - open_sell_qty)
    )
    execution_price = _positive_float(execution.get("average_entry_price"))
    lifecycle_price = _positive_float(lifecycle.get("average_entry_price"))
    price = execution_price or lifecycle_price
    return {
        "status": (
            "canonical_position_execution_conflict"
            if explicit_order_conflict
            else (
                "canonical_broker_position_provenance_unusable"
                if not position_execution_eligible
                else (
                    "canonical_position_context_captured"
                    if quantity is not None and quantity > 0
                    else "canonical_position_quantity_unavailable"
                )
            )
        ),
        "quantity": quantity if quantity is not None and quantity > 0 else None,
        "free_to_sell_quantity": (
            free_to_sell_qty
            if free_to_sell_qty is not None and free_to_sell_qty > 0
            else None
        ),
        "average_price": price,
        "open_sell_qty": open_sell_qty,
        "broker_reconciliation_contract_complete": (reconciliation_contract_complete),
        "position_reconciled": position_reconciled,
        "position_authority_reconciled": position_authority_reconciled,
        "position_reconciliation_mode": reconciliation_mode or None,
        "simulation_position_reconciled": simulation_position_reconciled,
        "broker_snapshot_age_sec": broker_snapshot_age_sec,
        "max_broker_position_age_sec": max_broker_position_age_sec,
        "broker_position_fresh": broker_position_fresh,
        "position_execution_eligible": position_execution_eligible,
        "candidate_exit_rule": candidate_exit_rule or None,
        "active_hard_guard": active_hard_guard or None,
        "hard_exit_guard_observed": hard_exit_guard_observed,
        "cancel_pending": reconciliation.get("cancel_pending") is True,
        "exit_token_active": reconciliation.get("exit_token_active") is True,
        "quantity_conflict": quantity_conflict,
        "quantity_pointer": (
            "/holding_decision_context/position_lifecycle/broker_qty"
            if broker_qty is not None
            else (
                "/holding_decision_context/execution_pnl/remaining_qty"
                if remaining_qty is not None
                else (
                    "/holding_decision_context/position_lifecycle/memory_qty"
                    if memory_qty is not None
                    else None
                )
            )
        ),
        "free_to_sell_quantity_formula": "total_position_minus_open_sell_qty",
        "price_pointer": (
            "/holding_decision_context/execution_pnl/average_entry_price"
            if execution_price is not None
            else (
                "/holding_decision_context/position_lifecycle/average_entry_price"
                if lifecycle_price is not None
                else None
            )
        ),
    }


def _lifecycle_projection(
    *,
    trace: Mapping[str, Any],
    payload: Mapping[str, Any],
    capacity_depth: Mapping[str, Any] | None,
    liquidity: Mapping[str, Any],
    economics: Mapping[str, Any],
    max_exit_sweep_slippage_bps: float,
    max_broker_position_age_sec: float,
) -> dict[str, Any]:
    position = _position_context(
        payload,
        max_broker_position_age_sec=max_broker_position_age_sec,
    )
    position_qty = _nonnegative_int(position.get("quantity"))
    free_to_sell_qty = _nonnegative_int(position.get("free_to_sell_quantity"))
    buy_price = _positive_float(position.get("average_price"))
    entry_roundtrip_capacity = _nonnegative_int(
        liquidity.get("counterfactual_liquidity_qty_ceiling")
    )
    immediate_exit_capacity = _nonnegative_int(
        liquidity.get("counterfactual_immediate_exit_qty_ceiling")
    )
    bid_levels = _levels((capacity_depth or {}).get("bid_levels"))
    bid_slippage_capacity = _capacity_within_slippage(
        bid_levels,
        side="bid",
        max_slippage_bps=max_exit_sweep_slippage_bps,
    )
    full_position_exit_vwap = (
        None
        if free_to_sell_qty is None
        or bid_slippage_capacity is None
        or free_to_sell_qty > bid_slippage_capacity
        or immediate_exit_capacity is None
        or free_to_sell_qty > immediate_exit_capacity
        else _sweep_vwap(bid_levels, free_to_sell_qty)
    )
    gross_exit_bps = (
        None
        if buy_price is None or full_position_exit_vwap is None
        else (full_position_exit_vwap / buy_price - 1.0) * 10_000.0
    )
    fixed_cost = None
    if economics.get("statutory_sell_tax_bps") is not None:
        fixed_cost = sum(
            float(economics.get(field) or 0.0)
            for field in (
                "buy_fee_bps",
                "sell_fee_bps",
                "statutory_sell_tax_bps",
                "uncertainty_buffer_bps",
            )
        )
    net_exit_bps = (
        None
        if gross_exit_bps is None or fixed_cost is None
        else gross_exit_bps - fixed_cost
    )
    return {
        "schema": LIFECYCLE_PROJECTION_SCHEMA,
        "objective": (
            "maximize_after_cost_net_profit_with_fast_frequent_bounded_exposure"
        ),
        "decision_stage": trace.get("decision_stage"),
        "entry_projection": {
            "timing_owner": "deterministic_micro_reversion_state_machine_candidate",
            "ai_role": "offline_cost_liquidity_and_tail_risk_adjudication",
            "minimum_gross_target_bps": economics.get("minimum_gross_target_bps"),
            "counterfactual_fast_roundtrip_capacity_qty": (entry_roundtrip_capacity),
            "counterfactual_full_position_exit_sweep_vwap": (full_position_exit_vwap),
            "live_price_or_order_effect": False,
        },
        "holding_projection": {
            "review_cadence": "each_new_0b_or_0d_state_change_not_synchronous_llm",
            "observed_position_qty": position_qty,
            "counterfactual_free_to_sell_qty": free_to_sell_qty,
            "observed_position_average_price": buy_price,
            "position_provenance": position,
            "counterfactual_fast_exit_capacity_qty": immediate_exit_capacity,
            "counterfactual_snapshot_exit_sweep_vwap": full_position_exit_vwap,
            "counterfactual_capacity_coverage_ratio": (
                None
                if free_to_sell_qty in (None, 0) or immediate_exit_capacity is None
                else min(1.0, immediate_exit_capacity / free_to_sell_qty)
            ),
            "counterfactual_uncovered_position_qty": (
                None
                if free_to_sell_qty is None or immediate_exit_capacity is None
                else max(0, free_to_sell_qty - immediate_exit_capacity)
            ),
            "counterfactual_net_executable_pnl_bps": (
                None if net_exit_bps is None else round(net_exit_bps, 6)
            ),
            "scale_in_requires_fresh_recovery_and_verified_exit_capacity": True,
            "hard_protect_emergency_exit_priority_unchanged": True,
        },
        "exit_projection": {
            "profit_basis": ("full_position_bid_sweep_vwap_after_roundtrip_cost"),
            "minimum_net_profit_bps": economics.get("minimum_net_profit_bps"),
            "counterfactual_net_target_reached": (
                None
                if net_exit_bps is None
                else net_exit_bps
                >= float(economics.get("minimum_net_profit_bps") or 0.0)
            ),
            "counterfactual_immediately_executable_qty": (
                None
                if free_to_sell_qty is None or immediate_exit_capacity is None
                else min(free_to_sell_qty, immediate_exit_capacity)
            ),
            "hard_protect_emergency_exit_priority_unchanged": True,
            "live_sell_or_cancel_effect": False,
        },
        **AUTHORITY_CONTRACT,
    }


def _verified_symbol_metadata_context(
    *,
    supplied: Mapping[str, Any] | None,
    symbol: str,
    snapshot_date: str,
) -> dict[str, Any]:
    """Validate an effective-dated symbol-master lookup for cost qualification.

    The raw lookup is never copied to tactical evidence.  Only normalized
    economics fields and immutable hashes are returned.  Missing/conflicting
    lookups remain observation-only; a mapping that claims ``verified`` but
    conflicts with the trace identity fails closed.
    """

    if not isinstance(supplied, Mapping):
        return {
            "symbol_metadata_status": "missing",
            "symbol_metadata_record_sha256": None,
            "symbol_master_artifact_sha256": None,
            "symbol_metadata_source": None,
            "symbol_metadata_source_reference": None,
            "symbol_metadata_verified_at": None,
            "listing_market": None,
            "instrument_type": None,
            "instrument_tax_class": None,
        }
    allowed_lookup_fields = {
        "lookup_status",
        "record",
        "record_sha256",
        "symbol_master_artifact_sha256",
    }
    if set(supplied) - allowed_lookup_fields:
        raise ValueError("verified_symbol_metadata_lookup_fields_invalid")
    lookup_status = str(supplied.get("lookup_status") or "").strip().lower()
    record = supplied.get("record")
    if lookup_status != "verified":
        if record is not None:
            raise ValueError("symbol_metadata_unverified_record_present")
        return {
            "symbol_metadata_status": lookup_status or "missing",
            "symbol_metadata_record_sha256": None,
            "symbol_master_artifact_sha256": None,
            "symbol_metadata_source": None,
            "symbol_metadata_source_reference": None,
            "symbol_metadata_verified_at": None,
            "listing_market": None,
            "instrument_type": None,
            "instrument_tax_class": None,
        }
    if not isinstance(record, Mapping):
        raise ValueError("verified_symbol_metadata_record_missing")
    expected_record_fields = {
        "symbol",
        "listing_market",
        "instrument_type",
        "instrument_tax_class",
        "effective_from",
        "effective_to",
        "metadata_source",
        "source_reference",
        "verified_at",
        "conflict_status",
    }
    if set(record) != expected_record_fields:
        raise ValueError("verified_symbol_metadata_record_fields_invalid")
    normalized_symbol = normalize_symbol(record.get("symbol"))
    if not normalized_symbol or normalized_symbol != normalize_symbol(symbol):
        raise ValueError("verified_symbol_metadata_symbol_mismatch")
    try:
        observed_date = date.fromisoformat(str(snapshot_date or ""))
        effective_from = date.fromisoformat(str(record.get("effective_from") or ""))
        effective_to_raw = record.get("effective_to")
        effective_to = (
            None
            if effective_to_raw in {None, ""}
            else date.fromisoformat(str(effective_to_raw))
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("verified_symbol_metadata_effective_date_invalid") from exc
    if observed_date < effective_from or (
        effective_to is not None and observed_date > effective_to
    ):
        raise ValueError("verified_symbol_metadata_outside_effective_window")
    if str(record.get("conflict_status") or "").strip().lower() != "clean":
        raise ValueError("verified_symbol_metadata_conflict")
    listing_market = normalize_listing_market(record.get("listing_market"))
    instrument_type = normalize_instrument_type(record.get("instrument_type"))
    if listing_market is ListingMarket.UNKNOWN:
        raise ValueError("verified_symbol_metadata_listing_market_unknown")
    if instrument_type is InstrumentType.UNKNOWN:
        raise ValueError("verified_symbol_metadata_instrument_type_unknown")
    metadata_source = str(record.get("metadata_source") or "").strip()
    source_reference = str(record.get("source_reference") or "").strip()
    verified_at = str(record.get("verified_at") or "").strip()
    if not metadata_source or not source_reference:
        raise ValueError("verified_symbol_metadata_provenance_missing")
    verified_at_value = _parse_timestamp(verified_at)
    if verified_at_value.tzinfo is None:
        raise ValueError("verified_symbol_metadata_verified_at_timezone_missing")
    expected_tax_class = tax_profile_for(
        trade_date=observed_date,
        listing_market=listing_market,
        instrument_type=instrument_type,
    ).instrument_tax_class.value
    instrument_tax_class = str(record.get("instrument_tax_class") or "").strip()
    if instrument_tax_class != expected_tax_class:
        raise ValueError("verified_symbol_metadata_tax_class_mismatch")
    normalized_record = {
        "symbol": normalized_symbol,
        "listing_market": listing_market.value,
        "instrument_type": instrument_type.value,
        "instrument_tax_class": instrument_tax_class,
        "effective_from": effective_from.isoformat(),
        "effective_to": None if effective_to is None else effective_to.isoformat(),
        "metadata_source": metadata_source,
        "source_reference": source_reference,
        "verified_at": verified_at,
        "conflict_status": "clean",
    }
    record_sha256 = _sha256(normalized_record)
    declared_record_hash = str(supplied.get("record_sha256") or "").strip()
    if declared_record_hash and declared_record_hash != record_sha256:
        raise ValueError("verified_symbol_metadata_record_sha256_mismatch")
    artifact_hash = str(supplied.get("symbol_master_artifact_sha256") or "").strip()
    if artifact_hash and (
        len(artifact_hash) != 64
        or any(character not in "0123456789abcdef" for character in artifact_hash)
    ):
        raise ValueError("verified_symbol_metadata_artifact_sha256_invalid")
    return {
        "symbol_metadata_status": "verified",
        "symbol_metadata_record_sha256": record_sha256,
        "symbol_master_artifact_sha256": artifact_hash or None,
        "symbol_metadata_source": metadata_source,
        "symbol_metadata_source_reference": source_reference,
        "symbol_metadata_verified_at": verified_at,
        "listing_market": listing_market.value,
        "instrument_type": instrument_type.value,
        "instrument_tax_class": instrument_tax_class,
    }


def _entry_pipeline_allocator_provenance(
    *, evidence: Mapping[str, Any], entry_pipeline_rows: Iterable[Mapping[str, Any]]
) -> dict[str, Any]:
    """Join the central allocator only after provider-visible evidence exists."""

    trace_id = str(evidence.get("decision_trace_id") or "").strip()
    symbol = normalize_symbol(evidence.get("stock_code"))
    trace_venue = _exact_venue(evidence.get("trace_effective_venue"))
    trace_session = _session(evidence.get("trace_session_bucket"))
    trace_route = _route(evidence.get("trace_market_data_route"))
    try:
        decision_ms = _timestamp_ms(evidence.get("trace_decision_ts"))
    except (TypeError, ValueError) as exc:
        raise ValueError("entry_pipeline_trace_decision_timestamp_invalid") from exc

    def session_identity(value: Any) -> str:
        session = _session(value)
        return {
            "KRX_LIKE_PREMARKET": "PREMARKET_KRX_LIKE",
            "KRX_LIKE_AFTERMARKET": "AFTERMARKET_KRX_LIKE",
        }.get(session, session)

    def route_venue(value: Any) -> str:
        route = _route(value)
        if "integrated" in route or "sor" in route:
            return "SOR"
        if route in {"krx", "krx_only", "krx_regular"}:
            return "KRX"
        if route in {"nxt", "nxt_only", "nxt_regular"}:
            return "NXT"
        return "UNKNOWN"

    def submitted_order_quantities(
        *, stage: str, fields: Mapping[str, Any]
    ) -> dict[str, int]:
        """Return exact broker-order quantities carried by one pipeline row.

        Allocator ``effective_qty`` is the planned total.  Probe-first rows keep
        that total while submitting only the first leg, so it must never be
        treated as the quantity that crossed the broker boundary.  Bind only
        explicit order-number/quantity pairs and let the caller deduplicate the
        probe, leg, bundle-summary, and residual views of the same order.
        """

        if stage not in {
            "order_bundle_submitted",
            "order_leg_sent",
            "probe_submitted",
            "residual_submitted",
        } or str(fields.get("actual_order_submitted") or "").strip().lower() not in {
            "1",
            "true",
            "yes",
            "on",
        }:
            return {}

        orders: dict[str, int] = {}

        def add(order_no: Any, quantity: Any) -> None:
            normalized_order_no = str(order_no or "").strip()
            normalized_quantity = _nonnegative_int(quantity)
            if (
                not normalized_order_no
                or normalized_order_no in {"-", "None", "none", "null"}
                or normalized_quantity is None
                or normalized_quantity <= 0
            ):
                return
            previous = orders.get(normalized_order_no)
            if previous is not None and previous != normalized_quantity:
                raise ValueError(
                    "entry_pipeline_allocator_broker_order_qty_conflict"
                )
            orders[normalized_order_no] = normalized_quantity

        order_qty_list = str(fields.get("broker_order_qty_list") or "").strip()
        if order_qty_list:
            for token in order_qty_list.split(","):
                normalized_token = token.strip()
                if not normalized_token:
                    continue
                if ":" not in normalized_token:
                    raise ValueError(
                        "entry_pipeline_allocator_broker_order_qty_list_invalid"
                    )
                order_no, quantity = normalized_token.rsplit(":", 1)
                if (
                    not str(order_no or "").strip()
                    or (_nonnegative_int(quantity) or 0) <= 0
                ):
                    raise ValueError(
                        "entry_pipeline_allocator_broker_order_qty_list_invalid"
                    )
                add(order_no, quantity)

        if stage in {"order_leg_sent", "probe_submitted", "residual_submitted"}:
            direct_order_no = (
                fields.get("broker_order_no")
                or fields.get("order_no")
                or fields.get("ord_no")
            )
            direct_qty = next(
                (
                    fields.get(field)
                    for field in ("submitted_qty", "qty", "requested_qty")
                    if fields.get(field) not in (None, "")
                ),
                None,
            )
            add(
                direct_order_no,
                direct_qty,
            )
            if not orders:
                raise ValueError(
                    "entry_pipeline_allocator_broker_order_qty_missing"
                )
        elif not orders and _nonnegative_int(fields.get("submitted_leg_count")) == 1:
            add(
                fields.get("broker_order_no")
                or fields.get("order_no")
                or fields.get("ord_no"),
                fields.get("submitted_qty"),
            )
        if stage == "order_bundle_submitted" and not orders:
            raise ValueError("entry_pipeline_allocator_broker_order_qty_missing")
        return orders

    expected_route_venue = route_venue(trace_route)
    semantic_events: dict[tuple[str, int, str], dict[str, Any]] = {}
    # Repeated budget/latency observations legitimately carry different
    # planned totals as price and available cash move.  A broker-bound row may
    # still be only the first one-share probe.  Grant allocator outcome
    # authority only after exact, deduplicated broker-order quantities sum to
    # the selected central allocation.  A partial probe/residual submission is
    # useful observation evidence but cannot manufacture full-notional EV.
    broker_bound_semantic_keys: set[tuple[str, int, str]] = set()
    matching_row_count = 0
    for row in entry_pipeline_rows:
        if not isinstance(row, Mapping) or row.get("pipeline") != "ENTRY_PIPELINE":
            continue
        fields = row.get("fields")
        if not isinstance(fields, Mapping):
            continue
        row_trace_id = str(fields.get("ai_decision_trace_id") or "").strip()
        if (
            row_trace_id != trace_id
            or normalize_symbol(row.get("stock_code")) != symbol
        ):
            continue
        formula_version = str(fields.get("formula_version") or "").strip()
        effective_qty = _nonnegative_int(fields.get("effective_qty"))
        if not formula_version or effective_qty is None or effective_qty <= 0:
            continue
        matching_row_count += 1
        if row.get("event_type") != "pipeline_event" or row.get("schema_version") != 1:
            raise ValueError("entry_pipeline_allocator_event_contract_invalid")
        stage = str(row.get("stage") or "").strip()
        record_id = _nonnegative_int(row.get("record_id"))
        emitted_at = str(row.get("emitted_at") or "").strip()
        emitted_date = str(row.get("emitted_date") or "").strip()
        if not stage or record_id is None or record_id <= 0 or not emitted_at:
            raise ValueError("entry_pipeline_allocator_event_identity_invalid")
        try:
            parsed_emitted_at = datetime.fromisoformat(emitted_at)
            if parsed_emitted_at.tzinfo is None:
                parsed_emitted_at = datetime.fromisoformat(f"{emitted_at}+09:00")
            emitted_ms = int(parsed_emitted_at.timestamp() * 1_000)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "entry_pipeline_allocator_event_timestamp_invalid"
            ) from exc
        if emitted_date != parsed_emitted_at.date().isoformat():
            raise ValueError("entry_pipeline_allocator_event_date_mismatch")
        if emitted_ms < decision_ms:
            raise ValueError("entry_pipeline_allocator_event_precedes_ai_decision")
        row_venue = _exact_venue(fields.get("effective_venue") or fields.get("venue"))
        row_session = session_identity(fields.get("market_session_bucket"))
        row_route = (
            fields.get("market_data_route")
            or fields.get("entry_candle_ws_route")
            or fields.get("rising_missed_ws_last_route")
        )
        if row_venue != trace_venue:
            raise ValueError("entry_pipeline_allocator_venue_mismatch")
        if row_session != session_identity(trace_session):
            raise ValueError("entry_pipeline_allocator_session_mismatch")
        observed_route_venue = route_venue(row_route)
        route_binding_source = "explicit_market_data_route"
        if (
            observed_route_venue == "UNKNOWN"
            and expected_route_venue in {"KRX", "NXT"}
            and row_venue == expected_route_venue
        ):
            # Some broker-submission rows retain the exact effective venue but
            # omit the earlier market-data route field. A non-integrated KRX
            # or NXT trace can bind to that same explicit venue; SOR can never
            # use this fallback because it requires integrated-route proof.
            observed_route_venue = row_venue
            route_binding_source = "explicit_event_venue_fallback"
        if (
            expected_route_venue == "UNKNOWN"
            or observed_route_venue != expected_route_venue
        ):
            raise ValueError(
                "entry_pipeline_allocator_route_mismatch:"
                f"trace={trace_id}:expected={expected_route_venue}:"
                f"observed={observed_route_venue}"
            )
        owner_raw = str(
            fields.get("quantity_owner") or fields.get("qty_source") or ""
        ).strip()
        if owner_raw and owner_raw not in {
            "position_sizing_dynamic_formula",
            "scalping_position_sizing_allocator",
        }:
            raise ValueError("entry_pipeline_allocator_owner_invalid")
        owner = "position_sizing_dynamic_formula"
        key = (formula_version, effective_qty, owner)
        semantic = {
            "decision_trace_id": trace_id,
            "stock_code": symbol,
            "formula_version": formula_version,
            "effective_qty": effective_qty,
            "quantity_owner": owner,
        }
        event_identity = {
            "schema_version": 1,
            "event_type": "pipeline_event",
            "pipeline": "ENTRY_PIPELINE",
            "stage": stage,
            "record_id": record_id,
            "stock_code": symbol,
            "emitted_at": parsed_emitted_at.isoformat(),
            "emitted_date": emitted_date,
            "decision_trace_id": trace_id,
            "effective_venue": row_venue,
            "session_bucket": row_session,
            "route_venue": expected_route_venue,
            "route_binding_source": route_binding_source,
            "formula_version": formula_version,
            "effective_qty": effective_qty,
            "quantity_owner": owner,
        }
        row_submitted_orders = submitted_order_quantities(stage=stage, fields=fields)
        if row_submitted_orders:
            event_identity["submitted_order_quantities"] = [
                {
                    "broker_order_no": order_no,
                    "submitted_qty": quantity,
                }
                for order_no, quantity in sorted(row_submitted_orders.items())
            ]
        joined = semantic_events.setdefault(
            key,
            {
                "semantic": semantic,
                "source_event_sha256s": set(),
                "event_timestamps_ms": [],
                "submitted_order_quantities": {},
            },
        )
        joined["source_event_sha256s"].add(_sha256(event_identity))
        joined["event_timestamps_ms"].append(emitted_ms)
        for order_no, submitted_qty in row_submitted_orders.items():
            previous = joined["submitted_order_quantities"].get(order_no)
            if previous is not None and previous != submitted_qty:
                raise ValueError(
                    "entry_pipeline_allocator_broker_order_qty_conflict"
                )
            joined["submitted_order_quantities"][order_no] = submitted_qty
        if row_submitted_orders:
            broker_bound_semantic_keys.add(key)
    if not semantic_events:
        return {
            "status": "allocator_provenance_missing",
            "quantity_authority": "standardized_one_share_observation_only",
            "allocator_event_sha256": None,
            "allocator_source_event_sha256s": [],
            "allocator_first_event_timestamp_ms": None,
            "allocator_last_event_timestamp_ms": None,
            "formula_version": None,
            "effective_qty": None,
            "matching_row_count": 0,
            "deduplicated_event_count": 0,
            "allocator_semantic_count": 0,
            "allocator_submitted_semantic_count": 0,
            "submitted_qty": None,
            "submission_coverage_pct": None,
            "fully_submitted_semantic_count": 0,
            "allocator_provenance_error": None,
        }
    fully_submitted_semantic_keys: set[tuple[str, int, str]] = set()
    submitted_qty_by_key: dict[tuple[str, int, str], int] = {}
    for key, event in semantic_events.items():
        submitted_qty = sum(event["submitted_order_quantities"].values())
        submitted_qty_by_key[key] = submitted_qty
        planned_qty = key[1]
        if submitted_qty > planned_qty:
            raise ValueError("entry_pipeline_allocator_submitted_qty_exceeds_effective")
        if submitted_qty == planned_qty:
            fully_submitted_semantic_keys.add(key)
    selected_key: tuple[str, int, str] | None = None
    if (
        len(fully_submitted_semantic_keys) == 1
        and len(broker_bound_semantic_keys) == 1
        and fully_submitted_semantic_keys == broker_bound_semantic_keys
    ):
        selected_key = next(iter(fully_submitted_semantic_keys))
    if selected_key is None:
        all_source_hashes = sorted(
            {
                source_hash
                for event in semantic_events.values()
                for source_hash in event["source_event_sha256s"]
            }
        )
        all_event_times = sorted(
            timestamp
            for event in semantic_events.values()
            for timestamp in event["event_timestamps_ms"]
        )
        sole_key = next(iter(semantic_events)) if len(semantic_events) == 1 else None
        sole_submitted_qty = (
            submitted_qty_by_key.get(sole_key) if sole_key is not None else None
        )
        sole_planned_qty = sole_key[1] if sole_key is not None else None
        return {
            "status": (
                "allocator_provenance_conflict_observation_only"
                if len(semantic_events) != 1 or len(broker_bound_semantic_keys) > 1
                else (
                    "allocator_provenance_partial_submission_observation_only"
                    if sole_submitted_qty
                    else "allocator_provenance_not_submitted_observation_only"
                )
            ),
            "quantity_authority": "standardized_one_share_observation_only",
            "allocator_event_sha256": None,
            "allocator_source_event_sha256s": all_source_hashes,
            "allocator_first_event_timestamp_ms": all_event_times[0],
            "allocator_last_event_timestamp_ms": all_event_times[-1],
            "formula_version": None,
            "effective_qty": None,
            "matching_row_count": matching_row_count,
            "deduplicated_event_count": len(semantic_events),
            "allocator_semantic_count": len(semantic_events),
            "allocator_submitted_semantic_count": len(broker_bound_semantic_keys),
            "submitted_qty": sole_submitted_qty,
            "submission_coverage_pct": (
                None
                if not sole_planned_qty or sole_submitted_qty is None
                else round(sole_submitted_qty / sole_planned_qty * 100.0, 6)
            ),
            "fully_submitted_semantic_count": len(
                fully_submitted_semantic_keys
            ),
        }
    joined = semantic_events[selected_key]
    semantic = joined["semantic"]
    source_event_sha256s = sorted(joined["source_event_sha256s"])
    event_timestamps_ms = sorted(joined["event_timestamps_ms"])
    allocator_event = {
        **semantic,
        "source_event_sha256s": source_event_sha256s,
        "submitted_order_quantities": [
            {
                "broker_order_no": order_no,
                "submitted_qty": quantity,
            }
            for order_no, quantity in sorted(
                joined["submitted_order_quantities"].items()
            )
        ],
    }
    return {
        "status": "central_allocator_provenance_joined",
        "quantity_authority": "position_sizing_dynamic_formula_outcome_only",
        "allocator_event_sha256": _sha256(allocator_event),
        "allocator_source_event_sha256s": source_event_sha256s,
        "allocator_first_event_timestamp_ms": event_timestamps_ms[0],
        "allocator_last_event_timestamp_ms": event_timestamps_ms[-1],
        "formula_version": semantic["formula_version"],
        "effective_qty": semantic["effective_qty"],
        "matching_row_count": matching_row_count,
        "deduplicated_event_count": 1,
        "allocator_semantic_count": len(semantic_events),
        "allocator_submitted_semantic_count": len(broker_bound_semantic_keys),
        "submitted_qty": submitted_qty_by_key[selected_key],
        "submission_coverage_pct": 100.0,
        "fully_submitted_semantic_count": len(fully_submitted_semantic_keys),
    }


def build_tactical_evidence(
    *,
    trace: Mapping[str, Any],
    payload: Mapping[str, Any],
    market_rows: Iterable[Mapping[str, Any]],
    depth_rows: Iterable[Mapping[str, Any]],
    event_references: Iterable[Mapping[str, Any]],
    config: BridgeConfig | None = None,
    excluded_scopes: set[tuple[str, str, str, int]] | None = None,
    verified_symbol_metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build one nonfuture sidecar without changing the exact provider payload."""

    selected_config = config or BridgeConfig()
    watermark, blockers = exact_snapshot_watermark(trace, payload)
    blocker_list = list(blockers)
    capacity_blockers: list[str] = []
    exact_payload = _stored_replay_exact_payload(payload)
    if exact_payload is None:
        blocker_list.append("stored_exact_payload_missing")
    source_exact_payload_sha256 = (
        _sha256(exact_payload) if exact_payload is not None else None
    )
    scope = resolve_micro_scope(trace)
    if scope.status != "resolved":
        blocker_list.append(scope.reason or "micro_scope_unresolved")
    symbol = normalize_symbol(trace.get("stock_code"))
    if not symbol:
        blocker_list.append("trace_symbol_missing")
    watermark_ms = int((watermark or {}).get("captured_at_ms") or 0)
    watermark_us = int((watermark or {}).get("captured_at_us") or 0)
    snapshot_date = str((watermark or {}).get("captured_at") or "")[:10]
    try:
        date.fromisoformat(snapshot_date)
        snapshot_date_valid = True
    except (TypeError, ValueError):
        snapshot_date_valid = False
    if verified_symbol_metadata is not None and not snapshot_date_valid:
        blocker_list.append("verified_symbol_metadata_snapshot_date_unavailable")
    symbol_metadata = _verified_symbol_metadata_context(
        supplied=(verified_symbol_metadata if snapshot_date_valid else None),
        symbol=symbol,
        snapshot_date=snapshot_date,
    )
    causal_lower_us = max(
        0,
        watermark_us
        - (
            selected_config.active_wave_max_age_sec
            + selected_config.context_lookback_sec
        )
        * 1_000_000,
    )

    accepted_market: list[Mapping[str, Any]] = []
    rejected_market = Counter()
    rejected_market_receive_us: list[int] = []
    for row in market_rows:
        if (
            normalize_symbol(row.get("symbol")) != symbol
            or normalize_venue(row.get("venue")) != scope.venue
            or _session(row.get("session_bucket")) != scope.session_bucket
        ):
            continue
        try:
            received_us = _timestamp_us(row.get("local_receive_timestamp"))
        except (TypeError, ValueError):
            # An unbounded timestamp cannot be proven past and is never part of
            # prompt-visible quality counters.
            continue
        if received_us < causal_lower_us or received_us > watermark_us:
            continue
        valid, reason = _valid_market_row(row)
        if not valid:
            rejected_market[reason or "market_invalid"] += 1
            rejected_market_receive_us.append(received_us)
            continue
        accepted_market.append(row)
    accepted_market.sort(
        key=lambda row: (
            _timestamp_us(row.get("local_receive_timestamp")),
            int(row.get("source_sequence") or 0),
        )
    )
    latest_market = accepted_market[-1] if accepted_market else None
    if latest_market is None:
        blocker_list.append("past_market_row_missing")
        selected_epoch = 0
    else:
        selected_epoch = int(latest_market.get("sequence_epoch") or 0)
        latest_market_us = _timestamp_us(latest_market.get("local_receive_timestamp"))
        if any(
            rejected_us >= latest_market_us
            for rejected_us in rejected_market_receive_us
        ):
            blocker_list.append("market_invalid_row_supersedes_latest_valid")
        market_age_ms = (watermark_us - latest_market_us) / 1_000.0
        if market_age_ms < 0:
            blocker_list.append("future_market_row_selected")
        elif market_age_ms > selected_config.max_market_age_ms:
            blocker_list.append("market_row_stale")
        accepted_market = [
            row
            for row in accepted_market
            if int(row.get("sequence_epoch") or 0) == selected_epoch
        ]
        blocker_list.extend(_series_sequence_findings(accepted_market, prefix="market"))
        market_bid = _positive_float(latest_market.get("best_bid"))
        market_ask = _positive_float(latest_market.get("best_ask"))
        quote_age_ms = _finite_float(latest_market.get("quote_age_ms"))
        if market_bid is None or market_ask is None:
            blocker_list.append("market_bbo_missing")
        if quote_age_ms is None or quote_age_ms < 0:
            blocker_list.append("market_quote_age_missing")
        elif quote_age_ms > selected_config.max_quote_age_ms:
            blocker_list.append("market_bbo_stale")
    trade_scope = (
        str((watermark or {}).get("captured_at") or "")[:10],
        scope.venue,
        scope.session_bucket,
        selected_epoch,
    )
    if excluded_scopes and trade_scope in excluded_scopes:
        blocker_list.append("source_exclusion_scope_matched")

    accepted_depth: list[Mapping[str, Any]] = []
    rejected_depth = Counter()
    rejected_depth_receive_us: list[int] = []
    for row in depth_rows:
        if _scope_key(row) != (
            symbol,
            scope.venue,
            scope.session_bucket,
            selected_epoch,
        ):
            continue
        try:
            received_us = _timestamp_us(row.get("local_receive_timestamp"))
        except (TypeError, ValueError):
            continue
        if received_us < causal_lower_us or received_us > watermark_us:
            continue
        valid, reason = _valid_depth_row(row)
        if not valid:
            rejected_depth[reason or "depth_invalid"] += 1
            rejected_depth_receive_us.append(received_us)
            continue
        accepted_depth.append(row)
    accepted_depth.sort(
        key=lambda row: (
            _timestamp_us(row.get("local_receive_timestamp")),
            int(row.get("source_sequence") or 0),
        )
    )
    latest_depth = accepted_depth[-1] if accepted_depth else None
    capacity_depth = latest_depth
    depth_basis_status = "same_basis"
    depth_age_ms = None
    if latest_depth is None:
        capacity_blockers.append("same_epoch_past_depth_missing")
        depth_basis_status = "same_epoch_past_depth_missing"
    else:
        latest_depth_us = _timestamp_us(latest_depth.get("local_receive_timestamp"))
        if any(
            rejected_us >= latest_depth_us for rejected_us in rejected_depth_receive_us
        ):
            capacity_blockers.append("depth_invalid_row_supersedes_latest_valid")
            capacity_depth = None
            depth_basis_status = "invalid_latest_depth_capacity_unavailable"
        depth_age_ms = (watermark_us - latest_depth_us) / 1_000.0
        if depth_age_ms < 0:
            capacity_blockers.append("future_depth_row_selected")
            capacity_depth = None
            depth_basis_status = "future_depth_capacity_unavailable"
        elif depth_age_ms > selected_config.max_depth_age_ms:
            capacity_blockers.append("depth_row_stale")
            capacity_depth = None
            depth_basis_status = "stale_depth_capacity_unavailable"
        depth_sequence_findings = _series_sequence_findings(
            accepted_depth, prefix="depth"
        )
        capacity_blockers.extend(depth_sequence_findings)
        if depth_sequence_findings:
            capacity_depth = None
            depth_basis_status = "depth_sequence_capacity_unavailable"
        if latest_market is not None and capacity_depth is not None:
            market_bid = _positive_float(latest_market.get("best_bid"))
            market_ask = _positive_float(latest_market.get("best_ask"))
            depth_bid = _positive_float(latest_depth.get("best_bid"))
            depth_ask = _positive_float(latest_depth.get("best_ask"))
            if market_bid != depth_bid or market_ask != depth_ask:
                capacity_depth = None
                depth_basis_status = "market_depth_bbo_conflict_capacity_unavailable"
                capacity_blockers.append(depth_basis_status)

    references: list[Mapping[str, Any]] = []
    rejected_references = Counter()
    for row in event_references:
        if _scope_key(row) != (
            symbol,
            scope.venue,
            scope.session_bucket,
            selected_epoch,
        ):
            continue
        try:
            detected_ms = int(row.get("event_detected_at_ms"))
        except (TypeError, ValueError):
            continue
        if not causal_lower_us <= detected_ms * 1_000 <= watermark_us:
            continue
        valid, reason = _valid_reference(row)
        if not valid:
            rejected_references[reason or "event_reference_invalid"] += 1
            continue
        references.append(row)
    by_wave: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in references:
        by_wave[str(row.get("parent_wave_id"))].append(row)
    wave_rows = [
        min(
            rows,
            key=lambda row: (
                int(row.get("event_detected_at_ms") or 0),
                int(row.get("event_sequence_in_wave") or 0),
                int(row.get("shock_horizon_ms") or 0),
            ),
        )
        for rows in by_wave.values()
    ]
    active_reference = (
        max(wave_rows, key=lambda row: int(row.get("event_detected_at_ms") or 0))
        if wave_rows
        else None
    )
    if active_reference is not None and (
        watermark_ms - int(active_reference.get("event_detected_at_ms") or 0)
        > selected_config.active_wave_max_age_sec * 1_000
    ):
        active_reference = None

    status = "source_unavailable" if blocker_list else "not_applicable"
    event_metrics: dict[str, Any] = {}
    tape: dict[str, Any] = {}
    orderbook: dict[str, Any] = {}
    liquidity: dict[str, Any] = _liquidity_projection(
        depth=capacity_depth,
        recent_rows=(),
        config=selected_config,
    )
    economics = _economics(
        liquidity=liquidity,
        config=selected_config,
        venue=scope.venue,
        snapshot_date=snapshot_date,
        symbol_metadata=symbol_metadata,
    )
    if active_reference is not None and latest_market is not None:
        try:
            causal_points = tuple(_p2_point(row) for row in accepted_market)
            onset = reconstruct_shock_onset_context(
                causal_points,
                reference=dict(active_reference),
                reference_max_lag_ms=2_000,
            )
        except (TypeError, ValueError):
            blocker_list.append("shock_onset_reconstruction_failed")
        else:
            event_ms = onset.event_local_receive_timestamp_ms
            post_rows = [
                row
                for row in accepted_market
                if (
                    _timestamp_ms(row.get("local_receive_timestamp")),
                    int(row.get("source_sequence") or 0),
                )
                >= (event_ms, onset.event_source_sequence)
                and _positive_float(row.get("trade_price")) is not None
            ]
            latest_price = _positive_float(latest_market.get("trade_price"))
            if not post_rows or latest_price is None:
                blocker_list.append("event_price_path_incomplete")
            else:
                reference_price = onset.reference_price
                shock_price = onset.shock_price
                running_low = shock_price
                running_low_row = post_rows[0]
                confirmation_row: Mapping[str, Any] | None = None
                confirmation_low = shock_price
                recovery_invalidation_count = 0
                for row in post_rows[1:]:
                    price = float(row["trade_price"])
                    if price < running_low:
                        running_low = price
                        running_low_row = row
                        if confirmation_row is not None:
                            recovery_invalidation_count += 1
                            confirmation_row = None
                        confirmation_low = running_low
                        continue
                    reclaim_span = reference_price - running_low
                    if (
                        confirmation_row is None
                        and reclaim_span > 0
                        and price >= running_low + 0.5 * reclaim_span
                    ):
                        confirmation_row = row
                        confirmation_low = running_low
                post_low = min(float(row["trade_price"]) for row in post_rows)
                new_low_after_half_reclaim = bool(
                    recovery_invalidation_count > 0 and confirmation_row is None
                )
                shock_size = reference_price - post_low
                reclaim_fraction = (
                    (latest_price - post_low) / shock_size if shock_size > 0 else 0.0
                )
                early_end_ms = min(
                    watermark_ms,
                    event_ms + selected_config.tape_capacity_window_sec * 1_000,
                )
                recent_start_ms = max(
                    event_ms,
                    watermark_ms - selected_config.tape_capacity_window_sec * 1_000,
                )
                early_rows = [
                    row
                    for row in accepted_market
                    if event_ms
                    <= _timestamp_ms(row.get("local_receive_timestamp"))
                    <= early_end_ms
                ]
                recent_rows = [
                    row
                    for row in accepted_market
                    if recent_start_ms
                    <= _timestamp_ms(row.get("local_receive_timestamp"))
                    <= watermark_ms
                ]
                early_tape = _aggressor_quantities(early_rows)
                recent_tape = _aggressor_quantities(recent_rows)
                nonoverlap_windows = early_end_ms < recent_start_ms
                sell_pressure_deceleration = (
                    None
                    if not nonoverlap_windows
                    or early_tape["sell_ratio"] is None
                    or recent_tape["sell_ratio"] is None
                    else round(
                        early_tape["sell_ratio"] - recent_tape["sell_ratio"],
                        6,
                    )
                )
                tape = {
                    "early": early_tape,
                    "recent": recent_tape,
                    "window_sec": selected_config.tape_capacity_window_sec,
                    "early_window_end_ms": early_end_ms,
                    "recent_window_start_ms": recent_start_ms,
                    "deceleration_windows_nonoverlap": nonoverlap_windows,
                    "sell_pressure_deceleration": sell_pressure_deceleration,
                }
                recovery_cycle_support_rows = (
                    []
                    if confirmation_row is None
                    else [
                        row
                        for row in post_rows
                        if (
                            _timestamp_us(row.get("local_receive_timestamp")),
                            int(row.get("source_sequence") or 0),
                        )
                        >= (
                            _timestamp_us(
                                running_low_row.get("local_receive_timestamp")
                            ),
                            int(running_low_row.get("source_sequence") or 0),
                        )
                    ]
                )
                recovery_cycle_support_tape = _aggressor_quantities(
                    recovery_cycle_support_rows
                )
                tape["latest_recovery_cycle_support"] = {
                    **recovery_cycle_support_tape,
                    "cycle_low_source_sequence": running_low_row.get("source_sequence"),
                    "confirmation_source_sequence": (
                        None
                        if confirmation_row is None
                        else confirmation_row.get("source_sequence")
                    ),
                }
                event_depth_rows = [
                    row
                    for row in accepted_depth
                    if event_ms
                    <= _timestamp_ms(row.get("local_receive_timestamp"))
                    <= watermark_ms
                ]
                first_depth = event_depth_rows[0] if event_depth_rows else None
                latest_bid_depth = _nonnegative_int(
                    (capacity_depth or {}).get("bid_depth")
                )
                first_bid_depth = _nonnegative_int((first_depth or {}).get("bid_depth"))
                same_price_depth = bool(
                    first_depth is not None
                    and capacity_depth is not None
                    and all(
                        _positive_float(row.get("best_bid"))
                        == _positive_float(first_depth.get("best_bid"))
                        for row in event_depth_rows
                    )
                    and _positive_float(first_depth.get("best_bid"))
                    == _positive_float(capacity_depth.get("best_bid"))
                )
                bid_replenishment = (
                    None
                    if not same_price_depth
                    or latest_bid_depth is None
                    or first_bid_depth is None
                    else latest_bid_depth - first_bid_depth
                )
                best_bid = _positive_float(latest_market.get("best_bid"))
                best_ask = _positive_float(latest_market.get("best_ask"))
                spread_bps = (
                    None
                    if best_bid is None or best_ask is None
                    else (best_ask / best_bid - 1.0) * 10_000.0
                )
                orderbook = {
                    "best_bid": best_bid,
                    "best_ask": best_ask,
                    "best_bid_qty": _nonnegative_int(
                        (capacity_depth or {}).get("best_bid_qty")
                    ),
                    "best_ask_qty": _nonnegative_int(
                        (capacity_depth or {}).get("best_ask_qty")
                    ),
                    "bid_depth": latest_bid_depth,
                    "ask_depth": _nonnegative_int(
                        (capacity_depth or {}).get("ask_depth")
                    ),
                    "spread_bps": (
                        None if spread_bps is None else round(spread_bps, 6)
                    ),
                    "same_epoch_bid_depth_change_qty": bid_replenishment,
                    "bid_replenishment_same_price_basis": same_price_depth,
                    "bid_replenishment_price_path_status": (
                        "continuous_same_bid_price"
                        if same_price_depth
                        else "price_basis_changed_or_unavailable"
                    ),
                    "depth_age_ms": depth_age_ms,
                    "depth_join_status": (
                        "joined_fresh_past_same_epoch_same_bbo"
                        if capacity_depth is not None
                        and depth_age_ms is not None
                        and depth_age_ms <= selected_config.max_depth_age_ms
                        else depth_basis_status
                    ),
                }
                late_buy_support = (
                    recovery_cycle_support_tape.get("buy_qty", 0) > 0
                    and (recovery_cycle_support_tape.get("buy_ratio") or 0.0) >= 0.5
                )
                sell_decelerated = (sell_pressure_deceleration or 0.0) > 0
                bid_supported = bid_replenishment is not None and bid_replenishment > 0
                if new_low_after_half_reclaim:
                    status = "continuation_blocked"
                elif confirmation_row is not None and (
                    late_buy_support or sell_decelerated or bid_supported
                ):
                    status = "reversion_confirmed"
                elif reclaim_fraction > 0 or confirmation_row is not None:
                    status = "reversion_candidate"
                else:
                    status = "shock_active"
                event_metrics = {
                    "parent_wave_id": active_reference.get("parent_wave_id"),
                    "path_segment_id": active_reference.get("path_segment_id"),
                    "shock_event_id": active_reference.get("shock_event_id"),
                    "shock_horizon_ms": onset.shock_horizon_ms,
                    "event_sequence_in_wave": active_reference.get(
                        "event_sequence_in_wave"
                    ),
                    "event_detected_at_ms": event_ms,
                    "event_source_sequence": onset.event_source_sequence,
                    "reference_price": reference_price,
                    "shock_price": shock_price,
                    "post_shock_low_price": post_low,
                    "asof_trade_price": latest_price,
                    "shock_bps": onset.shock_return_bps,
                    "reclaim_from_low_bps": round(
                        (latest_price / post_low - 1.0) * 10_000.0, 6
                    ),
                    "reclaim_fraction": round(reclaim_fraction, 6),
                    "remaining_to_reference_bps": round(
                        (reference_price / latest_price - 1.0) * 10_000.0,
                        6,
                    ),
                    "half_reclaim_first_source_sequence": (
                        None
                        if confirmation_row is None
                        else confirmation_row.get("source_sequence")
                    ),
                    "half_reclaim_reference_low_price": (
                        None if confirmation_row is None else confirmation_low
                    ),
                    "new_low_after_half_reclaim": new_low_after_half_reclaim,
                    "recovery_invalidation_count": recovery_invalidation_count,
                    "latest_recovery_cycle_reconfirmed": bool(
                        recovery_invalidation_count > 0 and confirmation_row is not None
                    ),
                }
                liquidity = _liquidity_projection(
                    depth=capacity_depth,
                    recent_rows=recent_rows,
                    config=selected_config,
                )
                economics = _economics(
                    liquidity=liquidity,
                    config=selected_config,
                    venue=scope.venue,
                    snapshot_date=snapshot_date,
                    symbol_metadata=symbol_metadata,
                )
    if blocker_list:
        status = "source_unavailable"
    latest_market_payload = latest_market or {}
    source_quality_status = "pass" if not blocker_list else "blocked"
    evidence_without_hash = {
        "schema": TACTICAL_EVIDENCE_SCHEMA,
        "evidence_version": 1,
        "bridge_config_sha256": _bridge_config_contract(selected_config)[
            "config_sha256"
        ],
        "bridge_producer_version": BRIDGE_PRODUCER_VERSION,
        "decision_trace_id": trace.get("decision_trace_id"),
        "request_id": trace.get("request_id"),
        "decision_stage": trace.get("decision_stage"),
        "source_provider_payload_sha256": trace.get("payload_sha256"),
        "source_exact_payload_sha256": source_exact_payload_sha256,
        "source_request_envelope_sha256": trace.get("request_envelope_sha256"),
        "snapshot_id": (watermark or {}).get("snapshot_id"),
        "stock_code": symbol,
        "trace_effective_venue": trace.get("effective_venue"),
        "trace_session_bucket": trace.get("session_bucket"),
        "trace_decision_ts": trace.get("decision_ts"),
        "trace_market_data_route": (watermark or {}).get("trace_market_data_route"),
        "integrated_sor_route_proven": (watermark or {}).get(
            "integrated_sor_route_proven"
        )
        is True,
        "micro_venue": scope.venue,
        "micro_session_bucket": scope.session_bucket,
        "sequence_epoch": selected_epoch or None,
        "snapshot_captured_at": (watermark or {}).get("captured_at"),
        "snapshot_captured_at_ms": watermark_ms or None,
        "provider_payload_semantic_hash_status": (watermark or {}).get(
            "provider_payload_semantic_hash_status"
        ),
        "exact_replay_source_semantic_status": (watermark or {}).get(
            "exact_replay_source_semantic_status"
        ),
        "decision_watermark": {
            "local_receive_timestamp": latest_market_payload.get(
                "local_receive_timestamp"
            ),
            "source_sequence": latest_market_payload.get("source_sequence"),
            "past_only_join": True,
        },
        "depth_watermark": {
            "local_receive_timestamp": (latest_depth or {}).get(
                "local_receive_timestamp"
            ),
            "source_sequence": (latest_depth or {}).get("source_sequence"),
            "past_only_join": True,
        },
        "state": status,
        "event": event_metrics,
        "tape": tape,
        "orderbook": orderbook,
        "economics": economics,
        "liquidity_capacity": liquidity,
        "source_quality": {
            "status": source_quality_status,
            "blockers": sorted(set(blocker_list)),
            "liquidity_capacity_status": (
                "pass" if not capacity_blockers else "blocked"
            ),
            "liquidity_capacity_blockers": sorted(set(capacity_blockers)),
            "rejected_market_reason_counts": dict(rejected_market),
            "rejected_depth_reason_counts": dict(rejected_depth),
            "rejected_reference_reason_counts": dict(rejected_references),
            "parent_wave_reference_count": len(by_wave),
            "parent_wave_deduplicated": True,
            "future_outcome_fields_in_context": False,
        },
        **METRIC_CONTRACT,
        **AUTHORITY_CONTRACT,
    }
    lifecycle = _lifecycle_projection(
        trace=trace,
        payload=payload,
        capacity_depth=capacity_depth,
        liquidity=liquidity,
        economics=economics,
        max_exit_sweep_slippage_bps=selected_config.max_exit_sweep_slippage_bps,
        max_broker_position_age_sec=(selected_config.max_broker_position_age_sec),
    )
    context_without_hash = {
        **evidence_without_hash,
        LIFECYCLE_PROJECTION_SCHEMA: lifecycle,
    }
    return {**context_without_hash, "evidence_sha256": _sha256(context_without_hash)}


def _validated_ask_depletion_evidence_watermark(
    evidence: Mapping[str, Any],
) -> tuple[Mapping[str, Any], int, int, int, int, int]:
    """Return the exact native causal watermark required by ask-depletion."""

    event = evidence.get("event")
    if not isinstance(event, Mapping):
        raise ValueError("ask_depletion_event_missing")
    event_ms = event.get("event_detected_at_ms")
    event_sequence = event.get("event_source_sequence")
    observed_through_ms = evidence.get("snapshot_captured_at_ms")
    sequence_epoch = evidence.get("sequence_epoch")
    if any(
        isinstance(value, bool) or not isinstance(value, int) or value <= 0
        for value in (
            event_ms,
            event_sequence,
            observed_through_ms,
            sequence_epoch,
        )
    ):
        raise ValueError("ask_depletion_event_watermark_invalid")
    snapshot_captured_at = evidence.get("snapshot_captured_at")
    if not isinstance(snapshot_captured_at, str) or not snapshot_captured_at.strip():
        raise ValueError("ask_depletion_event_watermark_invalid")
    try:
        observed_through_us = _timestamp_us(snapshot_captured_at)
    except (TypeError, ValueError) as exc:
        raise ValueError("ask_depletion_event_watermark_invalid") from exc
    if (
        observed_through_ms != observed_through_us // 1_000
        or event_ms > observed_through_ms
    ):
        raise ValueError("ask_depletion_event_watermark_invalid")
    return (
        event,
        event_ms,
        event_sequence,
        observed_through_ms,
        observed_through_us,
        sequence_epoch,
    )


def _validate_ask_depletion_context_native(context: Mapping[str, Any]) -> None:
    if any(
        not isinstance(context.get(field), str) or not context.get(field)
        for field in (
            "event_id",
            "anchor_role",
            "symbol",
            "venue",
            "session_bucket",
        )
    ) or any(
        isinstance(context.get(field), bool)
        or not isinstance(context.get(field), int)
        or context.get(field) <= 0
        for field in (
            "sequence_epoch",
            "anchor_event_local_receive_timestamp_ms",
            "event_market_source_sequence",
            "observed_through_local_receive_timestamp_ms",
        )
    ):
        raise ValueError("ask_depletion_context_native_type_invalid")
    if any(
        not isinstance(context.get(field), bool)
        for field in ("depth_source_complete", "market_source_complete")
    ):
        raise ValueError("ask_depletion_context_native_type_invalid")
    if (
        context["anchor_event_local_receive_timestamp_ms"]
        > context["observed_through_local_receive_timestamp_ms"]
    ):
        raise ValueError("ask_depletion_context_watermark_invalid")


def build_ask_depletion_feature_sidecar(
    *,
    evidence: Mapping[str, Any],
    market_rows: Iterable[Mapping[str, Any]],
    depth_rows: Iterable[Mapping[str, Any]],
    max_depth_age_ms: int = 1_000,
) -> dict[str, Any]:
    """Build the causal ask-depletion sidecar for the current replay design.

    The shock event is the feature anchor and the Exact-V2 snapshot is the
    observation watermark.  Rows after that snapshot are never admitted even
    when the caller supplies a larger outcome window.  Invalid rows make the
    exact source incomplete; they are never silently removed and treated as a
    continuous path.
    """

    _validate_tactical_evidence_shape(evidence)
    if (
        isinstance(max_depth_age_ms, bool)
        or not isinstance(max_depth_age_ms, int)
        or max_depth_age_ms <= 0
    ):
        raise ValueError("ask_depletion_max_depth_age_ms_invalid")
    evidence_hash = str(evidence.get("evidence_sha256") or "")
    evidence_content = {
        key: value for key, value in evidence.items() if key != "evidence_sha256"
    }
    if not evidence_hash or evidence_hash != _sha256(evidence_content):
        raise ValueError("ask_depletion_evidence_sha256_mismatch")
    (
        event,
        event_ms,
        event_sequence,
        observed_through_ms,
        observed_through_us,
        sequence_epoch,
    ) = _validated_ask_depletion_evidence_watermark(evidence)
    event_id = str(event.get("shock_event_id") or "").strip()
    if not event_id:
        raise ValueError("ask_depletion_event_watermark_invalid")
    event_us = event_ms * 1_000
    if observed_through_us < event_us:
        raise ValueError("ask_depletion_event_watermark_invalid")
    symbol = normalize_symbol(evidence.get("stock_code"))
    venue = normalize_venue(evidence.get("micro_venue"))
    session_bucket = _session(evidence.get("micro_session_bucket"))
    scope = (symbol, venue, session_bucket, sequence_epoch)
    if not symbol or venue == "UNKNOWN" or not session_bucket:
        raise ValueError("ask_depletion_scope_invalid")

    market_path: list[Mapping[str, Any]] = []
    market_source_complete = True
    for row in market_rows:
        if not isinstance(row, Mapping) or _scope_key(row) != scope:
            continue
        try:
            received_us = _timestamp_us(row.get("local_receive_timestamp"))
            source_sequence = int(row.get("source_sequence") or 0)
        except (TypeError, ValueError):
            market_source_complete = False
            continue
        if (received_us, source_sequence) < (
            event_us,
            event_sequence,
        ) or received_us > observed_through_us:
            continue
        valid, _reason = _valid_market_row(row)
        if (
            not valid
            or row.get("schema") != "scalp_micro_reversion_market_stream_point_v3"
        ):
            market_source_complete = False
            continue
        market_path.append(row)
    market_path.sort(
        key=lambda row: (
            _timestamp_us(row.get("local_receive_timestamp")),
            int(row.get("source_sequence") or 0),
        )
    )
    if _series_sequence_findings(market_path, prefix="ask_depletion_market"):
        market_source_complete = False

    depth_path: list[Mapping[str, Any]] = []
    depth_source_complete = True
    anchor_lower_us = event_us - max_depth_age_ms * 1_000
    for row in depth_rows:
        if not isinstance(row, Mapping) or _scope_key(row) != scope:
            continue
        try:
            received_us = _timestamp_us(row.get("local_receive_timestamp"))
        except (TypeError, ValueError):
            depth_source_complete = False
            continue
        if not anchor_lower_us <= received_us <= observed_through_us:
            continue
        valid, _reason = _valid_depth_row(row)
        if not valid:
            depth_source_complete = False
            continue
        depth_path.append(row)
    depth_path.sort(
        key=lambda row: (
            _timestamp_us(row.get("local_receive_timestamp")),
            int(row.get("source_sequence") or 0),
        )
    )
    if _series_sequence_findings(depth_path, prefix="ask_depletion_depth"):
        depth_source_complete = False
    anchor_candidates = [
        row
        for row in depth_path
        if _timestamp_us(row.get("local_receive_timestamp")) < event_us
    ]
    anchor_depth = anchor_candidates[-1] if anchor_candidates else None

    report = build_ask_depletion_report(
        context=AskDepletionContext(
            event_id=event_id,
            anchor_role="shock_event",
            symbol=symbol,
            venue=venue,
            session_bucket=session_bucket,
            sequence_epoch=sequence_epoch,
            anchor_event_local_receive_timestamp_ms=event_ms,
            event_market_source_sequence=event_sequence,
            observed_through_local_receive_timestamp_ms=observed_through_ms,
            depth_source_complete=depth_source_complete,
            market_source_complete=market_source_complete,
        ),
        anchor_depth=anchor_depth,
        depth_rows=depth_path,
        market_rows=market_path,
        max_depth_age_ms=max_depth_age_ms,
    ).as_dict()
    contract_sha256 = _sha256(
        {
            "schema": ASK_DEPLETION_SCHEMA,
            **ASK_DEPLETION_METRIC_CONTRACT,
        }
    )
    content = {
        **report,
        "max_depth_age_ms": max_depth_age_ms,
        "tactical_micro_reversion_evidence_sha256": evidence_hash,
        "ask_depletion_contract_sha256": contract_sha256,
    }
    return {
        **content,
        "ask_depletion_context_sha256": _sha256(content),
    }


def _validated_ask_depletion_feature_view(
    sidecar: Mapping[str, Any],
    *,
    evidence: Mapping[str, Any],
) -> dict[str, Any]:
    """Return the complete fixed-horizon view required for provider ablation."""

    _validate_tactical_evidence_shape(evidence)
    evidence_hash = str(evidence.get("evidence_sha256") or "")
    evidence_content = {
        key: value for key, value in evidence.items() if key != "evidence_sha256"
    }
    if not evidence_hash or evidence_hash != _sha256(evidence_content):
        raise ValueError("ask_depletion_evidence_sha256_mismatch")
    (
        event,
        event_ms,
        event_sequence,
        observed_through_ms,
        _observed_through_us,
        sequence_epoch,
    ) = _validated_ask_depletion_evidence_watermark(evidence)
    if sidecar.get("schema") != ASK_DEPLETION_SCHEMA:
        raise ValueError("ask_depletion_sidecar_schema_invalid")
    declared_context_hash = str(sidecar.get("ask_depletion_context_sha256") or "")
    content = {
        key: value
        for key, value in sidecar.items()
        if key != "ask_depletion_context_sha256"
    }
    if not declared_context_hash or declared_context_hash != _sha256(content):
        raise ValueError("ask_depletion_context_sha256_mismatch")
    expected_contract_hash = _sha256(
        {
            "schema": ASK_DEPLETION_SCHEMA,
            **ASK_DEPLETION_METRIC_CONTRACT,
        }
    )
    if sidecar.get("ask_depletion_contract_sha256") != expected_contract_hash:
        raise ValueError("ask_depletion_contract_sha256_mismatch")
    for field, expected in ASK_DEPLETION_METRIC_CONTRACT.items():
        observed = sidecar.get(field)
        if field == "forbidden_uses":
            if not isinstance(observed, (list, tuple)) or tuple(observed) != tuple(
                expected
            ):
                raise ValueError(
                    "ask_depletion_sidecar_metric_contract_invalid:forbidden_uses"
                )
        elif observed != expected:
            raise ValueError(f"ask_depletion_sidecar_metric_contract_invalid:{field}")
    for field, expected in ASK_DEPLETION_SIDECAR_AUTHORITY.items():
        if sidecar.get(field) is not expected:
            raise ValueError(f"ask_depletion_sidecar_authority_invalid:{field}")
    context = sidecar.get("context")
    if not isinstance(context, Mapping):
        raise ValueError("ask_depletion_sidecar_context_invalid")
    if set(context) != ASK_DEPLETION_CONTEXT_FIELDS:
        raise ValueError("ask_depletion_sidecar_context_shape_invalid")
    _validate_ask_depletion_context_native(context)
    expected_context_identity = {
        "event_id": str(event.get("shock_event_id") or ""),
        "anchor_role": "shock_event",
        "symbol": normalize_symbol(evidence.get("stock_code")),
        "venue": normalize_venue(evidence.get("micro_venue")),
        "session_bucket": _session(evidence.get("micro_session_bucket")),
        "sequence_epoch": sequence_epoch,
        "anchor_event_local_receive_timestamp_ms": event_ms,
        "event_market_source_sequence": event_sequence,
        "observed_through_local_receive_timestamp_ms": observed_through_ms,
    }
    if any(
        context.get(field) != expected
        for field, expected in expected_context_identity.items()
    ):
        raise ValueError("ask_depletion_sidecar_context_identity_mismatch")
    if sidecar.get("tactical_micro_reversion_evidence_sha256") != evidence_hash:
        raise ValueError("ask_depletion_tactical_evidence_binding_mismatch")
    top_source_gaps = sidecar.get("source_gap_reasons")
    if (
        isinstance(sidecar.get("anchor_source_sequence"), bool)
        or not isinstance(sidecar.get("anchor_source_sequence"), int)
        or sidecar.get("anchor_source_sequence") <= 0
        or sidecar.get("anchor_source_quality_status")
        != "eligible_source_only_feature_ablation"
        or sidecar.get("source_quality_status")
        != "eligible_source_only_feature_ablation"
        or not isinstance(top_source_gaps, (list, tuple))
        or any(not isinstance(reason, str) or not reason for reason in top_source_gaps)
        or bool(top_source_gaps)
        or context.get("depth_source_complete") is not True
        or context.get("market_source_complete") is not True
    ):
        raise ValueError("ask_depletion_sidecar_source_quality_invalid")
    horizons = sidecar.get("horizons")
    if not isinstance(horizons, (list, tuple)):
        raise ValueError("ask_depletion_horizons_invalid")
    observed_horizons: list[int] = []
    for row in horizons:
        if not isinstance(row, Mapping) or set(row) != ASK_DEPLETION_HORIZON_FIELDS:
            raise ValueError("ask_depletion_horizon_shape_invalid")
        horizon_ms = row.get("horizon_ms")
        source_gaps = row.get("source_gap_reasons")
        if (
            isinstance(horizon_ms, bool)
            or not isinstance(horizon_ms, int)
            or horizon_ms <= 0
            or not isinstance(row.get("mature"), bool)
            or not isinstance(row.get("eligible_for_feature_ablation"), bool)
            or not isinstance(source_gaps, (list, tuple))
            or any(not isinstance(reason, str) or not reason for reason in source_gaps)
        ):
            raise ValueError("ask_depletion_horizon_contract_invalid")
        observed_horizons.append(horizon_ms)
        if (
            row.get("mature") is not True
            or row.get("eligible_for_feature_ablation") is not True
            or observed_through_ms < event_ms + horizon_ms
            or row.get("source_quality_status")
            != "eligible_source_only_feature_ablation"
            or source_gaps
            or isinstance(row.get("depth_observation_count"), bool)
            or not isinstance(row.get("depth_observation_count"), int)
            or row.get("depth_observation_count") <= 0
        ):
            raise ValueError("ask_depletion_complete_horizon_contract_invalid")
    if tuple(observed_horizons) != DEFAULT_ASK_DEPLETION_HORIZONS_MS:
        raise ValueError("ask_depletion_horizon_census_invalid")
    eligible_horizons = [deepcopy(dict(row)) for row in horizons]
    view_without_hash = {
        "schema": ASK_DEPLETION_FEATURE_VIEW_SCHEMA,
        "source_schema": ASK_DEPLETION_SCHEMA,
        "context": deepcopy(sidecar.get("context")),
        "anchor_source_sequence": sidecar.get("anchor_source_sequence"),
        "eligible_horizon_count": len(eligible_horizons),
        "eligible_horizons": eligible_horizons,
        "sidecar_hash_reconstruction": {
            field: deepcopy(sidecar.get(field))
            for field in ASK_DEPLETION_SIDECAR_RECONSTRUCTION_FIELDS
        },
        "tactical_micro_reversion_evidence_sha256": evidence_hash,
        "ask_depletion_contract_sha256": expected_contract_hash,
        "ask_depletion_context_sha256": declared_context_hash,
        **ABLATION_SOURCE_ONLY_AUTHORITY,
    }
    feature_view = {
        **view_without_hash,
        "feature_view_sha256": _sha256(view_without_hash),
    }
    validate_ask_depletion_feature_view(feature_view, evidence=evidence)
    return feature_view


def validate_ask_depletion_feature_view(
    feature_view: Mapping[str, Any], *, evidence: Mapping[str, Any]
) -> None:
    """Revalidate one persisted current-design feature view without its sidecar."""

    _validate_tactical_evidence_shape(evidence)
    evidence_hash = str(evidence.get("evidence_sha256") or "")
    evidence_without_hash = {
        key: value for key, value in evidence.items() if key != "evidence_sha256"
    }
    if not evidence_hash or evidence_hash != _sha256(evidence_without_hash):
        raise ValueError("ask_depletion_feature_evidence_hash_invalid")
    (
        event,
        event_ms,
        event_sequence,
        observed_through_ms,
        _observed_through_us,
        sequence_epoch,
    ) = _validated_ask_depletion_evidence_watermark(evidence)
    expected_fields = {
        "schema",
        "source_schema",
        "context",
        "anchor_source_sequence",
        "eligible_horizon_count",
        "eligible_horizons",
        "sidecar_hash_reconstruction",
        "tactical_micro_reversion_evidence_sha256",
        "ask_depletion_contract_sha256",
        "ask_depletion_context_sha256",
        "feature_view_sha256",
        *ABLATION_SOURCE_ONLY_AUTHORITY,
    }
    if set(feature_view) != expected_fields:
        raise ValueError("ask_depletion_feature_view_shape_invalid")
    feature_without_hash = {
        key: value
        for key, value in feature_view.items()
        if key != "feature_view_sha256"
    }
    if feature_view.get("feature_view_sha256") != _sha256(feature_without_hash):
        raise ValueError("ask_depletion_feature_view_hash_invalid")
    if (
        feature_view.get("schema") != ASK_DEPLETION_FEATURE_VIEW_SCHEMA
        or feature_view.get("source_schema") != ASK_DEPLETION_SCHEMA
        or feature_view.get("tactical_micro_reversion_evidence_sha256") != evidence_hash
        or feature_view.get("ask_depletion_contract_sha256")
        != _sha256(
            {
                "schema": ASK_DEPLETION_SCHEMA,
                **ASK_DEPLETION_METRIC_CONTRACT,
            }
        )
    ):
        raise ValueError("ask_depletion_feature_view_identity_invalid")
    context_hash = str(feature_view.get("ask_depletion_context_sha256") or "")
    if len(context_hash) != 64 or any(
        character not in "0123456789abcdef" for character in context_hash
    ):
        raise ValueError("ask_depletion_feature_context_hash_invalid")
    sidecar_reconstruction = feature_view.get("sidecar_hash_reconstruction")
    max_depth_age_ms = (
        sidecar_reconstruction.get("max_depth_age_ms")
        if isinstance(sidecar_reconstruction, Mapping)
        else None
    )
    anchor_depth_age_ms = (
        sidecar_reconstruction.get("anchor_depth_age_ms")
        if isinstance(sidecar_reconstruction, Mapping)
        else None
    )
    if (
        not isinstance(sidecar_reconstruction, Mapping)
        or set(sidecar_reconstruction) != ASK_DEPLETION_SIDECAR_RECONSTRUCTION_FIELDS
        or isinstance(max_depth_age_ms, bool)
        or not isinstance(max_depth_age_ms, int)
        or max_depth_age_ms <= 0
        or isinstance(anchor_depth_age_ms, bool)
        or not isinstance(anchor_depth_age_ms, (int, float))
        or not math.isfinite(float(anchor_depth_age_ms))
        or not 0 <= float(anchor_depth_age_ms) <= max_depth_age_ms
        or sidecar_reconstruction.get("anchor_source_quality_status")
        != "eligible_source_only_feature_ablation"
        or sidecar_reconstruction.get("source_quality_status")
        != "eligible_source_only_feature_ablation"
        or sidecar_reconstruction.get("source_gap_reasons") not in ([], ())
        or any(
            isinstance(sidecar_reconstruction.get(field), bool)
            or not isinstance(sidecar_reconstruction.get(field), int)
            or sidecar_reconstruction.get(field) < 0
            for field in (
                "ignored_cross_scope_depth_row_count",
                "ignored_cross_scope_market_row_count",
            )
        )
    ):
        raise ValueError("ask_depletion_feature_sidecar_reconstruction_invalid")
    reconstructed_sidecar_content = {
        "context": deepcopy(feature_view.get("context")),
        "anchor_source_sequence": feature_view.get("anchor_source_sequence"),
        **deepcopy(dict(sidecar_reconstruction)),
        "horizons": deepcopy(feature_view.get("eligible_horizons")),
        "schema": ASK_DEPLETION_SCHEMA,
        **ASK_DEPLETION_SIDECAR_AUTHORITY,
        **ASK_DEPLETION_METRIC_CONTRACT,
        "tactical_micro_reversion_evidence_sha256": evidence_hash,
        "ask_depletion_contract_sha256": feature_view.get(
            "ask_depletion_contract_sha256"
        ),
    }
    if _sha256(reconstructed_sidecar_content) != context_hash:
        raise ValueError("ask_depletion_feature_sidecar_hash_rebuild_mismatch")
    for field, expected in ABLATION_SOURCE_ONLY_AUTHORITY.items():
        if feature_view.get(field) is not expected:
            raise ValueError(f"ask_depletion_feature_authority_invalid:{field}")
    context = feature_view.get("context")
    if not isinstance(context, Mapping) or set(context) != ASK_DEPLETION_CONTEXT_FIELDS:
        raise ValueError("ask_depletion_feature_context_invalid")
    _validate_ask_depletion_context_native(context)
    expected_context_identity = {
        "event_id": str(event.get("shock_event_id") or ""),
        "anchor_role": "shock_event",
        "symbol": normalize_symbol(evidence.get("stock_code")),
        "venue": normalize_venue(evidence.get("micro_venue")),
        "session_bucket": _session(evidence.get("micro_session_bucket")),
        "sequence_epoch": sequence_epoch,
        "anchor_event_local_receive_timestamp_ms": event_ms,
        "event_market_source_sequence": event_sequence,
        "observed_through_local_receive_timestamp_ms": observed_through_ms,
        "depth_source_complete": True,
        "market_source_complete": True,
    }
    if any(
        context.get(field) != expected
        for field, expected in expected_context_identity.items()
    ):
        raise ValueError("ask_depletion_feature_context_binding_invalid")
    anchor_sequence = feature_view.get("anchor_source_sequence")
    horizons = feature_view.get("eligible_horizons")
    eligible_horizon_count = feature_view.get("eligible_horizon_count")
    if (
        isinstance(anchor_sequence, bool)
        or not isinstance(anchor_sequence, int)
        or anchor_sequence <= 0
        or not isinstance(horizons, list)
        or isinstance(eligible_horizon_count, bool)
        or not isinstance(eligible_horizon_count, int)
        or eligible_horizon_count != len(horizons)
        or len(horizons) != len(DEFAULT_ASK_DEPLETION_HORIZONS_MS)
    ):
        raise ValueError("ask_depletion_feature_horizon_census_invalid")

    def strict_number(value: Any) -> float | None:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None
        parsed = float(value)
        return parsed if math.isfinite(parsed) else None

    def nonnegative_integer(value: Any) -> int | None:
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            return None
        return value

    def ratio_matches(observed: Any, numerator: int, denominator: int) -> bool:
        if denominator <= 0:
            return numerator == 0 and observed is None
        parsed = strict_number(observed)
        if parsed is None or not 0.0 <= parsed <= 1.0:
            return False
        expected = numerator / denominator
        return abs(parsed - expected) <= 1e-7

    def nonnegative_ratio_matches(
        observed: Any, numerator: int, denominator: int
    ) -> bool:
        parsed = strict_number(observed)
        if parsed is None or parsed < 0.0 or denominator <= 0:
            return False
        return abs(parsed - (numerator / denominator)) <= 1e-7

    observed_horizons: list[int] = []
    for horizon in horizons:
        if (
            not isinstance(horizon, Mapping)
            or set(horizon) != ASK_DEPLETION_HORIZON_FIELDS
        ):
            raise ValueError("ask_depletion_feature_horizon_shape_invalid")
        horizon_ms = horizon.get("horizon_ms")
        source_gaps = horizon.get("source_gap_reasons")
        if (
            isinstance(horizon_ms, bool)
            or not isinstance(horizon_ms, int)
            or horizon.get("mature") is not True
            or horizon.get("eligible_for_feature_ablation") is not True
            or observed_through_ms < event_ms + horizon_ms
            or horizon.get("source_quality_status")
            != "eligible_source_only_feature_ablation"
            or not isinstance(source_gaps, (list, tuple))
            or source_gaps
            or isinstance(horizon.get("depth_observation_count"), bool)
            or not isinstance(horizon.get("depth_observation_count"), int)
            or horizon.get("depth_observation_count") <= 0
        ):
            raise ValueError("ask_depletion_feature_horizon_semantics_invalid")
        prices = tuple(
            strict_number(horizon.get(field))
            for field in ("anchor_best_ask", "endpoint_best_ask")
        )
        quantities = {
            field: nonnegative_integer(horizon.get(field))
            for field in (
                "initial_anchor_ask_qty",
                "endpoint_anchor_ask_qty",
                "minimum_anchor_ask_qty",
                "max_best_ask_depletion_qty",
                "aggressive_buy_qty_before_max_depletion",
                "unexplained_or_cancel_like_depletion_qty",
                "max_refill_qty",
            )
        }
        initial_qty = quantities["initial_anchor_ask_qty"]
        endpoint_qty = quantities["endpoint_anchor_ask_qty"]
        minimum_qty = quantities["minimum_anchor_ask_qty"]
        depletion_qty = quantities["max_best_ask_depletion_qty"]
        aggressive_qty = quantities["aggressive_buy_qty_before_max_depletion"]
        unexplained_qty = quantities["unexplained_or_cancel_like_depletion_qty"]
        refill_qty = quantities["max_refill_qty"]
        velocity = strict_number(horizon.get("best_ask_depletion_velocity_qty_per_sec"))
        endpoint_age = strict_number(horizon.get("depth_endpoint_age_ms"))
        price_level_cleared = horizon.get("price_level_cleared")
        if (
            any(value is None or value <= 0 for value in prices)
            or any(
                value is None
                for value in (
                    initial_qty,
                    endpoint_qty,
                    minimum_qty,
                    depletion_qty,
                    aggressive_qty,
                    refill_qty,
                )
            )
            or initial_qty is None
            or initial_qty <= 0
            or endpoint_qty is None
            or minimum_qty is None
            or depletion_qty is None
            or aggressive_qty is None
            or refill_qty is None
            or minimum_qty > initial_qty
            or endpoint_qty < minimum_qty
            or depletion_qty != initial_qty - minimum_qty
            or refill_qty < endpoint_qty - minimum_qty
            or velocity is None
            or velocity < 0
            or endpoint_age is None
            or not 0 <= endpoint_age <= max_depth_age_ms
            or not isinstance(price_level_cleared, bool)
            or (price_level_cleared and minimum_qty != 0)
            or not isinstance(horizon.get("downward_reprice_observed"), bool)
            or not ratio_matches(
                horizon.get("max_best_ask_depletion_ratio"),
                depletion_qty,
                initial_qty,
            )
        ):
            raise ValueError("ask_depletion_feature_numeric_semantics_invalid")
        aggressive_ratio = strict_number(
            horizon.get("aggressive_buy_trade_backed_ratio")
        )
        unexplained_ratio = horizon.get("unexplained_or_cancel_like_depletion_ratio")
        refill_ratio = horizon.get("refill_ratio")
        if depletion_qty > 0:
            if (
                unexplained_qty != max(0, depletion_qty - aggressive_qty)
                or unexplained_qty is None
                or unexplained_qty > depletion_qty
                or not ratio_matches(
                    aggressive_ratio,
                    min(aggressive_qty, depletion_qty),
                    depletion_qty,
                )
                or not ratio_matches(
                    unexplained_ratio,
                    unexplained_qty,
                    depletion_qty,
                )
                or not nonnegative_ratio_matches(
                    refill_ratio,
                    refill_qty,
                    depletion_qty,
                )
            ):
                raise ValueError("ask_depletion_feature_trade_backing_ratio_invalid")
        elif any(
            value is not None
            for value in (
                aggressive_ratio,
                unexplained_qty,
                unexplained_ratio,
                refill_ratio,
            )
        ):
            raise ValueError("ask_depletion_feature_zero_depletion_semantics_invalid")
        for field in ("first_price_level_clear_delay_ms", "refill_half_life_ms"):
            value = horizon.get(field)
            if value is not None and (
                nonnegative_integer(value) is None or value > horizon_ms
            ):
                raise ValueError(
                    "ask_depletion_feature_optional_delay_semantics_invalid"
                )
        clear_delay = horizon.get("first_price_level_clear_delay_ms")
        if price_level_cleared is not (clear_delay is not None):
            raise ValueError("ask_depletion_feature_clear_delay_binding_invalid")
        refill_half_life_ms = horizon.get("refill_half_life_ms")
        if depletion_qty > 0 and (
            (refill_qty * 2 >= depletion_qty) is not (refill_half_life_ms is not None)
        ):
            raise ValueError("ask_depletion_feature_refill_half_life_binding_invalid")
        if depletion_qty == 0 and refill_half_life_ms is not None:
            raise ValueError("ask_depletion_feature_refill_half_life_binding_invalid")
        top_depth = horizon.get("top_depth")
        if not isinstance(top_depth, (list, tuple)) or len(top_depth) != len(
            DEFAULT_ASK_DEPLETION_TOP_DEPTH_LEVELS
        ):
            raise ValueError("ask_depletion_feature_top_depth_census_invalid")
        observed_levels: list[int] = []
        for depth in top_depth:
            if (
                not isinstance(depth, Mapping)
                or set(depth) != ASK_DEPLETION_TOP_DEPTH_FIELDS
            ):
                raise ValueError("ask_depletion_feature_top_depth_shape_invalid")
            retained = depth.get("retained_level_count")
            anchor_price_count = depth.get("anchor_price_count")
            depth_initial = nonnegative_integer(depth.get("initial_qty"))
            depth_endpoint = nonnegative_integer(depth.get("endpoint_qty"))
            depth_minimum = nonnegative_integer(depth.get("minimum_qty"))
            depth_depletion = nonnegative_integer(depth.get("max_depletion_qty"))
            if (
                isinstance(retained, bool)
                or not isinstance(retained, int)
                or isinstance(anchor_price_count, bool)
                or not isinstance(anchor_price_count, int)
                or anchor_price_count != retained
                or any(
                    value is None
                    for value in (
                        depth_initial,
                        depth_endpoint,
                        depth_minimum,
                        depth_depletion,
                    )
                )
                or depth_initial is None
                or depth_initial <= 0
                or depth_endpoint is None
                or depth_minimum is None
                or depth_depletion is None
                or depth_minimum > depth_initial
                or depth_endpoint < depth_minimum
                or depth_depletion != depth_initial - depth_minimum
                or not ratio_matches(
                    depth.get("max_depletion_ratio"),
                    depth_depletion,
                    depth_initial,
                )
            ):
                raise ValueError("ask_depletion_feature_top_depth_semantics_invalid")
            observed_levels.append(retained)
        if tuple(observed_levels) != DEFAULT_ASK_DEPLETION_TOP_DEPTH_LEVELS:
            raise ValueError("ask_depletion_feature_top_depth_levels_invalid")
        observed_horizons.append(horizon_ms)
    if tuple(observed_horizons) != DEFAULT_ASK_DEPLETION_HORIZONS_MS:
        raise ValueError("ask_depletion_feature_horizon_order_invalid")


def build_future_outcome(
    *,
    evidence: Mapping[str, Any],
    market_rows: Iterable[Mapping[str, Any]],
    depth_rows: Iterable[Mapping[str, Any]] = (),
    entry_pipeline_rows: Iterable[Mapping[str, Any]] = (),
    control_action: str | None = None,
    config: BridgeConfig | None = None,
) -> dict[str, Any]:
    """Label quantity-sweep paths after the snapshot, never prompt input."""

    _validate_tactical_evidence_shape(evidence)
    for field, expected in AUTHORITY_CONTRACT.items():
        if evidence.get(field) is not expected:
            raise ValueError(f"future_outcome_evidence_authority_invalid:{field}")
    for field, expected in METRIC_CONTRACT.items():
        if _sha256(evidence.get(field)) != _sha256(expected):
            raise ValueError(f"future_outcome_evidence_contract_invalid:{field}")
    stored_evidence_hash = str(evidence.get("evidence_sha256") or "")
    evidence_without_hash = {
        key: value for key, value in evidence.items() if key != "evidence_sha256"
    }
    if (
        not stored_evidence_hash
        or _sha256(evidence_without_hash) != stored_evidence_hash
    ):
        raise ValueError("future_outcome_evidence_sha256_mismatch")
    selected_config = config or BridgeConfig()
    market_source_rows = tuple(market_rows)
    depth_source_rows = tuple(depth_rows)
    selected_contract = _bridge_config_contract(selected_config)
    if (
        evidence.get("bridge_producer_version") != BRIDGE_PRODUCER_VERSION
        or evidence.get("bridge_config_sha256") != selected_contract["config_sha256"]
    ):
        raise ValueError("future_outcome_bridge_config_mismatch")
    start_ms = int(evidence.get("snapshot_captured_at_ms") or 0)
    symbol = normalize_symbol(evidence.get("stock_code"))
    venue = normalize_venue(evidence.get("micro_venue"))
    session = _session(evidence.get("micro_session_bucket"))
    epoch = int(evidence.get("sequence_epoch") or 0)
    stage = (
        str(
            evidence.get("decision_stage")
            or (evidence.get(LIFECYCLE_PROJECTION_SCHEMA) or {}).get("decision_stage")
            or ""
        )
        .strip()
        .lower()
    )
    action = str(control_action or "").strip().upper()
    entry_like_stages = {
        "entry",
        "entry_screen",
        "gatekeeper",
        "post_probe",
    }
    position_like_stages = {
        "holding",
        "holding_score",
        "holding_flow",
        "exit",
    }
    grid = (evidence.get("liquidity_capacity") or {}).get(
        "counterfactual_liquidity_qty_grid"
    )
    grid = grid if isinstance(grid, list) else []
    conservative = next(
        (
            row
            for row in grid
            if isinstance(row, Mapping)
            and abs(float(row.get("participation_rate") or 0.0) - 0.05) <= 1e-12
        ),
        {},
    )
    liquidity = evidence.get("liquidity_capacity")
    liquidity = liquidity if isinstance(liquidity, Mapping) else {}
    depth_execution_basis = liquidity.get("snapshot_depth_execution_basis")
    depth_execution_basis = (
        depth_execution_basis if isinstance(depth_execution_basis, Mapping) else {}
    )
    snapshot_ask_levels = _levels(depth_execution_basis.get("ask_levels"))
    lifecycle = evidence.get(LIFECYCLE_PROJECTION_SCHEMA)
    lifecycle = lifecycle if isinstance(lifecycle, Mapping) else {}
    holding_projection = lifecycle.get("holding_projection")
    holding_projection = (
        holding_projection if isinstance(holding_projection, Mapping) else {}
    )
    position_provenance = holding_projection.get("position_provenance")
    position_provenance = (
        position_provenance if isinstance(position_provenance, Mapping) else {}
    )
    allocator_provenance: dict[str, Any] = {
        "status": "not_applicable_to_stage",
        "quantity_authority": "stage_quantity_owner_delegated",
        "allocator_event_sha256": None,
        "allocator_source_event_sha256s": [],
        "allocator_first_event_timestamp_ms": None,
        "allocator_last_event_timestamp_ms": None,
        "formula_version": None,
        "effective_qty": None,
        "matching_row_count": 0,
        "deduplicated_event_count": 0,
        "allocator_semantic_count": 0,
        "allocator_submitted_semantic_count": 0,
        "submitted_qty": None,
        "submission_coverage_pct": None,
        "fully_submitted_semantic_count": 0,
        "allocator_provenance_error": None,
    }
    if stage in entry_like_stages:
        evaluation_basis = "new_or_incremental_entry_ask_sweep_to_future_bid_sweep"
        try:
            allocator_provenance = _entry_pipeline_allocator_provenance(
                evidence=evidence,
                entry_pipeline_rows=entry_pipeline_rows,
            )
        except ValueError as exc:
            error_code = str(exc).split(":", 1)[0]
            if not error_code.startswith("entry_pipeline_allocator_"):
                raise
            # The entry-pipeline artifact has already passed the report-level
            # raw hash/schema/census gate. A causal or scope defect in one
            # trace-symbol join is therefore an exact-row exclusion, not
            # authority to discard unrelated traces for the day.
            allocator_provenance = {
                "status": "allocator_provenance_invalid_observation_only",
                "quantity_authority": "standardized_one_share_observation_only",
                "allocator_event_sha256": None,
                "allocator_source_event_sha256s": [],
                "allocator_first_event_timestamp_ms": None,
                "allocator_last_event_timestamp_ms": None,
                "formula_version": None,
                "effective_qty": None,
                "matching_row_count": 0,
                "deduplicated_event_count": 0,
                "allocator_semantic_count": 0,
                "allocator_submitted_semantic_count": 0,
                "submitted_qty": None,
                "submission_coverage_pct": None,
                "fully_submitted_semantic_count": 0,
                "allocator_provenance_error": error_code,
            }
        depth_capacity = _nonnegative_int(
            conservative.get("strict_depth_participation_capacity_qty")
        )
        allocator_qty = _nonnegative_int(allocator_provenance.get("effective_qty"))
        if allocator_qty is not None and depth_capacity is not None:
            quantity = min(allocator_qty, depth_capacity)
            quantity_basis = (
                "min_central_allocator_effective_qty_and_5pct_depth_capacity"
            )
        else:
            quantity = _nonnegative_int(
                conservative.get("standardized_one_share_probe_observation_qty")
            )
            quantity_basis = "standardized_one_share_observation_only"
        baseline_vwap = (
            None if quantity is None else _sweep_vwap(snapshot_ask_levels, quantity)
        )
        position_average_price = None
    elif stage in position_like_stages:
        evaluation_basis = (
            "hold_or_exit_incremental_future_bid_sweep_vs_snapshot_bid_sweep"
        )
        allocator_provenance["quantity_authority"] = (
            "broker_reconciled_free_to_sell_quantity"
        )
        quantity_basis = "broker_reconciled_free_to_sell_quantity"
        quantity = _nonnegative_int(
            holding_projection.get("counterfactual_free_to_sell_qty")
        )
        baseline_vwap = _positive_float(
            holding_projection.get("counterfactual_snapshot_exit_sweep_vwap")
        )
        position_average_price = _positive_float(
            holding_projection.get("observed_position_average_price")
        )
    elif stage == "entry_price":
        evaluation_basis = "entry_price_selection_evaluation_owned_by_stage_replay"
        quantity = None
        quantity_basis = "entry_price_stage_owner_delegated"
        baseline_vwap = None
        position_average_price = None
    elif stage == "scale_in":
        evaluation_basis = "scale_in_quantity_evaluation_owned_by_stage_replay"
        quantity = None
        quantity_basis = "scale_in_quantity_owner_delegated"
        baseline_vwap = None
        position_average_price = None
    elif stage == "overnight":
        evaluation_basis = "overnight_next_session_evaluation_owned_externally"
        quantity = None
        quantity_basis = "overnight_stage_owner_delegated"
        baseline_vwap = None
        position_average_price = None
    else:
        evaluation_basis = "decision_stage_not_supported"
        quantity = None
        quantity_basis = "unsupported_stage"
        baseline_vwap = None
        position_average_price = None
    rows: list[Mapping[str, Any]] = []
    rejected_market_times_us: list[int] = []
    for row in market_source_rows:
        if _scope_key(row) != (symbol, venue, session, epoch):
            continue
        try:
            received_us = _timestamp_us(row.get("local_receive_timestamp"))
        except (TypeError, ValueError):
            continue
        received_ms = received_us // 1_000
        if (
            start_ms
            < received_ms
            <= (
                start_ms
                + _post_snapshot_source_horizon_sec(selected_config) * 1_000
                + selected_config.max_outcome_endpoint_lag_ms
            )
        ):
            valid, _ = _valid_market_row(row)
            if not valid:
                rejected_market_times_us.append(received_us)
                continue
            rows.append(row)
    rows.sort(
        key=lambda row: (
            _timestamp_us(row.get("local_receive_timestamp")),
            int(row.get("source_sequence") or 0),
        )
    )
    depths: list[Mapping[str, Any]] = []
    rejected_depth_times_us: list[int] = []
    for row in depth_source_rows:
        if _scope_key(row) != (symbol, venue, session, epoch):
            continue
        try:
            received_us = _timestamp_us(row.get("local_receive_timestamp"))
        except (TypeError, ValueError):
            continue
        received_ms = received_us // 1_000
        if (
            start_ms - selected_config.max_depth_age_ms
            <= received_ms
            <= (
                start_ms
                + _post_snapshot_source_horizon_sec(selected_config) * 1_000
                + selected_config.max_outcome_endpoint_lag_ms
            )
        ):
            valid, _ = _valid_depth_row(row)
            if not valid:
                rejected_depth_times_us.append(received_us)
                continue
            depths.append(row)
    depths.sort(
        key=lambda row: (
            _timestamp_us(row.get("local_receive_timestamp")),
            int(row.get("source_sequence") or 0),
        )
    )
    depth_times_us = tuple(
        _timestamp_us(row.get("local_receive_timestamp")) for row in depths
    )
    evidence_economics = evidence.get("economics")
    evidence_economics = (
        evidence_economics if isinstance(evidence_economics, Mapping) else {}
    )
    evidence_cost_parts = [
        _finite_float(evidence_economics.get(field))
        for field in (
            "buy_fee_bps",
            "sell_fee_bps",
            "statutory_sell_tax_bps",
            "uncertainty_buffer_bps",
        )
    ]
    fixed_cost = (
        sum(float(value) for value in evidence_cost_parts if value is not None)
        if evidence_economics.get("cost_profile_verified") is True
        and all(value is not None for value in evidence_cost_parts)
        else None
    )
    outcome_eligibility_blockers: list[str] = []
    evidence_source_quality = evidence.get("source_quality")
    evidence_source_quality = (
        evidence_source_quality if isinstance(evidence_source_quality, Mapping) else {}
    )
    if evidence_source_quality.get("status") != "pass":
        outcome_eligibility_blockers.append("tactical_evidence_source_quality_not_pass")
    if evidence_source_quality.get("liquidity_capacity_status") != "pass":
        outcome_eligibility_blockers.append(
            "tactical_evidence_liquidity_capacity_not_pass"
        )
    if stage == "entry_price":
        outcome_eligibility_blockers.append(
            "entry_price_selection_evaluation_not_implemented_in_micro_bridge"
        )
    elif stage == "scale_in":
        outcome_eligibility_blockers.append("scale_in_quantity_owner_not_connected")
    elif stage == "overnight":
        outcome_eligibility_blockers.append(
            "overnight_next_session_evaluation_not_implemented_in_micro_bridge"
        )
    elif stage not in entry_like_stages | position_like_stages:
        outcome_eligibility_blockers.append("outcome_decision_stage_not_supported")
    if stage in position_like_stages:
        if position_provenance.get("hard_exit_guard_observed") is True:
            outcome_eligibility_blockers.append(
                "hard_safety_control_owned_outcome_excluded"
            )
        if action == "TRIM":
            outcome_eligibility_blockers.append(
                "trim_quantity_evaluation_owned_by_stage_replay"
            )
        elif action not in {"HOLD", "EXIT"}:
            outcome_eligibility_blockers.append(
                "position_control_action_missing_or_invalid"
            )
    if not quantity:
        outcome_eligibility_blockers.append("counterfactual_quantity_unavailable")
    if baseline_vwap is None:
        outcome_eligibility_blockers.append("snapshot_execution_basis_unavailable")
    if stage in entry_like_stages and fixed_cost is None:
        outcome_eligibility_blockers.append("roundtrip_cost_profile_unavailable")
    # observed_at, control-action diagnostic return, action-neutral endpoint
    # return, and position cost-basis return.  Only the neutral primitive is
    # suitable for comparing A/B/C decisions that can choose different actions.
    executable: list[tuple[int, float, float | None, float | None]] = []
    if (
        not outcome_eligibility_blockers
        and quantity
        and baseline_vwap is not None
        and (stage in position_like_stages or fixed_cost is not None)
    ):
        for row in rows:
            quote_age_ms = _finite_float(row.get("quote_age_ms"))
            if (
                quote_age_ms is None
                or quote_age_ms < 0
                or quote_age_ms > selected_config.max_quote_age_ms
            ):
                continue
            market_us = _timestamp_us(row.get("local_receive_timestamp"))
            depth_index = bisect_right(depth_times_us, market_us) - 1
            if depth_index < 0:
                continue
            depth = depths[depth_index]
            depth_age_ms = (market_us - depth_times_us[depth_index]) / 1_000.0
            if depth_age_ms > selected_config.max_depth_age_ms:
                continue
            if _positive_float(row.get("best_bid")) != _positive_float(
                depth.get("best_bid")
            ):
                continue
            bid_levels = _levels(depth.get("bid_levels"))
            bid_capacity = _capacity_within_slippage(
                bid_levels,
                side="bid",
                max_slippage_bps=selected_config.max_exit_sweep_slippage_bps,
            )
            participation_rate = _finite_float(conservative.get("participation_rate"))
            if bid_capacity is None or participation_rate is None:
                future_fast_exit_capacity = None
            else:
                future_participation_floor = math.floor(
                    bid_capacity * participation_rate
                )
                if (
                    stage in entry_like_stages
                    and allocator_provenance.get("status")
                    == "central_allocator_provenance_joined"
                ):
                    # Allocator-backed economics must respect the strict 5%
                    # depth ceiling at every future executable endpoint.  The
                    # standardized one-share floor is observation-only and
                    # cannot manufacture allocator-backed liquidity.
                    future_fast_exit_capacity = future_participation_floor
                else:
                    future_fast_exit_capacity = (
                        max(1, future_participation_floor) if bid_capacity > 0 else 0
                    )
            if (
                future_fast_exit_capacity is None
                or future_fast_exit_capacity < quantity
            ):
                continue
            exit_vwap = _sweep_vwap(bid_levels, quantity)
            if exit_vwap is None:
                continue
            received_ms = _timestamp_ms(row.get("local_receive_timestamp"))
            if stage in entry_like_stages:
                decision_quality_return = (
                    exit_vwap / baseline_vwap - 1.0
                ) * 10_000.0 - float(fixed_cost or 0.0)
                action_neutral_return = (
                    decision_quality_return
                    if (evidence.get("economics") or {}).get("cost_profile_verified")
                    is True
                    else None
                )
            else:
                # Holding/exit compares future executable proceeds with the
                # executable proceeds available at the decision snapshot.  It
                # must never fabricate a new ask-side purchase.
                hold_incremental_return = (exit_vwap / baseline_vwap - 1.0) * 10_000.0
                decision_quality_return = (
                    -hold_incremental_return
                    if action == "EXIT"
                    else hold_incremental_return
                )
                action_neutral_return = hold_incremental_return
            cost_basis_net_return = (
                None
                if position_average_price is None or fixed_cost is None
                else (exit_vwap / position_average_price - 1.0) * 10_000.0 - fixed_cost
            )
            executable.append(
                (
                    received_ms,
                    decision_quality_return,
                    action_neutral_return,
                    cost_basis_net_return,
                )
            )
    horizons: list[dict[str, Any]] = []
    for horizon in selected_config.outcome_horizons_sec:
        endpoint_target_ms = start_ms + horizon * 1_000
        endpoint_candidates = [
            row for row in executable if row[0] >= endpoint_target_ms
        ]
        endpoint = endpoint_candidates[0] if endpoint_candidates else None
        endpoint_lag_ms = None if endpoint is None else endpoint[0] - endpoint_target_ms
        bounded = (
            []
            if endpoint is None
            else [row for row in executable if row[0] <= endpoint[0]]
        )
        bounded_market = (
            []
            if endpoint is None
            else [
                row
                for row in rows
                if _timestamp_ms(row.get("local_receive_timestamp")) <= endpoint[0]
            ]
        )
        bounded_depth = (
            []
            if endpoint is None
            else [
                row
                for row in depths
                if start_ms
                < _timestamp_ms(row.get("local_receive_timestamp"))
                <= endpoint[0]
            ]
        )
        horizon_findings = tuple(
            sorted(
                set(_series_sequence_findings(bounded_market, prefix="outcome_market"))
                | set(_series_sequence_findings(bounded_depth, prefix="outcome_depth"))
            )
        )
        if endpoint is not None:
            endpoint_us = endpoint[0] * 1_000
            if any(
                start_ms * 1_000 < value <= endpoint_us
                for value in rejected_market_times_us
            ):
                horizon_findings = tuple(
                    sorted({*horizon_findings, "outcome_market_invalid_row_in_path"})
                )
            if any(
                start_ms * 1_000 < value <= endpoint_us
                for value in rejected_depth_times_us
            ):
                horizon_findings = tuple(
                    sorted({*horizon_findings, "outcome_depth_invalid_row_in_path"})
                )
        boundary_findings: set[str] = set()
        market_anchor_sequence = _nonnegative_int(
            (evidence.get("decision_watermark") or {}).get("source_sequence")
        )
        depth_anchor_sequence = _nonnegative_int(
            (evidence.get("depth_watermark") or {}).get("source_sequence")
        )
        if bounded_market and market_anchor_sequence is not None:
            if int(bounded_market[0].get("source_sequence") or 0) != (
                market_anchor_sequence + 1
            ):
                boundary_findings.add("outcome_market_anchor_sequence_gap")
        if bounded_depth and depth_anchor_sequence is not None:
            if int(bounded_depth[0].get("source_sequence") or 0) != (
                depth_anchor_sequence + 1
            ):
                boundary_findings.add("outcome_depth_anchor_sequence_gap")
        horizon_findings = tuple(sorted(set(horizon_findings) | boundary_findings))
        path_times = [start_ms, *(row[0] for row in bounded)]
        max_internal_gap_ms = max(
            (
                right - left
                for left, right in zip(path_times, path_times[1:], strict=False)
            ),
            default=None,
        )
        mature = bool(
            endpoint is not None
            and endpoint_lag_ms is not None
            and endpoint_lag_ms <= selected_config.max_outcome_endpoint_lag_ms
            and max_internal_gap_ms is not None
            and max_internal_gap_ms <= selected_config.max_outcome_internal_gap_ms
            and not horizon_findings
        )
        decision_returns = [row[1] for row in bounded] if mature else []
        neutral_returns = (
            [row[2] for row in bounded if row[2] is not None] if mature else []
        )
        cost_basis_returns = (
            [row[3] for row in bounded if row[3] is not None] if mature else []
        )
        neutral_path = [
            {"observed_at_ms": row[0], "return_bps": round(float(row[2]), 6)}
            for row in bounded
            if row[2] is not None
        ]
        neutral_target_ms = next(
            (
                row["observed_at_ms"]
                for row in neutral_path
                if row["return_bps"] >= selected_config.minimum_net_profit_bps
            ),
            None,
        )
        neutral_adverse_ms = next(
            (
                row["observed_at_ms"]
                for row in neutral_path
                if row["return_bps"] <= selected_config.adverse_label_bps
            ),
            None,
        )
        if not mature or not neutral_path:
            neutral_first_hit = "unavailable"
        elif neutral_target_ms is None and neutral_adverse_ms is None:
            neutral_first_hit = "none"
        elif neutral_target_ms is None:
            neutral_first_hit = "adverse_first"
        elif neutral_adverse_ms is None:
            neutral_first_hit = "net_target_first"
        elif neutral_target_ms < neutral_adverse_ms:
            neutral_first_hit = "net_target_first"
        elif neutral_adverse_ms < neutral_target_ms:
            neutral_first_hit = "adverse_first"
        else:
            neutral_first_hit = "ambiguous_same_timestamp"
        horizons.append(
            {
                "horizon_sec": horizon,
                "mature": mature,
                "endpoint_lag_ms": endpoint_lag_ms,
                "endpoint_observed_at_ms": (None if endpoint is None else endpoint[0]),
                "path_continuity_status": (
                    "pass"
                    if mature
                    else (
                        "sequence_gap_or_regression"
                        if horizon_findings
                        else (
                            "endpoint_missing_or_late"
                            if endpoint is None
                            or endpoint_lag_ms is None
                            or endpoint_lag_ms
                            > selected_config.max_outcome_endpoint_lag_ms
                            else "internal_gap_exceeded"
                        )
                    )
                ),
                "max_internal_gap_ms": max_internal_gap_ms,
                "source_quality_blockers": list(horizon_findings),
                "quantity_sweep_observation_count": len(bounded),
                "decision_quality_mfe_bps": (
                    None if not decision_returns else round(max(decision_returns), 6)
                ),
                "decision_quality_mae_bps": (
                    None if not decision_returns else round(min(decision_returns), 6)
                ),
                "action_neutral_executable_end_return_bps": (
                    None
                    if not mature or endpoint is None or endpoint[2] is None
                    else round(float(endpoint[2]), 6)
                ),
                "action_neutral_mfe_bps": (
                    None if not neutral_returns else round(max(neutral_returns), 6)
                ),
                "action_neutral_mae_bps": (
                    None if not neutral_returns else round(min(neutral_returns), 6)
                ),
                "action_neutral_path_sha256": (
                    _sha256(neutral_path) if mature and neutral_path else None
                ),
                "action_neutral_first_hit": neutral_first_hit,
                "action_neutral_target_first_delay_ms": (
                    None
                    if not mature or neutral_target_ms is None
                    else neutral_target_ms - start_ms
                ),
                "action_neutral_adverse_first_delay_ms": (
                    None
                    if not mature or neutral_adverse_ms is None
                    else neutral_adverse_ms - start_ms
                ),
                "position_cost_basis_net_mfe_bps": (
                    None
                    if not cost_basis_returns
                    else round(max(cost_basis_returns), 6)
                ),
                "position_cost_basis_net_mae_bps": (
                    None
                    if not cost_basis_returns
                    else round(min(cost_basis_returns), 6)
                ),
            }
        )
    mature_endpoints = [
        int(row["endpoint_observed_at_ms"]) for row in horizons if row["mature"] is True
    ]
    first_hit_rows = (
        []
        if not mature_endpoints
        else [row for row in executable if row[0] <= max(mature_endpoints)]
    )
    target_first_ms = next(
        (
            observed_ms
            for observed_ms, value, _, _ in first_hit_rows
            if value >= selected_config.minimum_net_profit_bps
        ),
        None,
    )
    adverse_first_ms = next(
        (
            observed_ms
            for observed_ms, value, _, _ in first_hit_rows
            if value <= selected_config.adverse_label_bps
        ),
        None,
    )
    neutral_target_first_ms = next(
        (
            observed_ms
            for observed_ms, _, value, _ in first_hit_rows
            if value is not None and value >= selected_config.minimum_net_profit_bps
        ),
        None,
    )
    neutral_adverse_first_ms = next(
        (
            observed_ms
            for observed_ms, _, value, _ in first_hit_rows
            if value is not None and value <= selected_config.adverse_label_bps
        ),
        None,
    )
    if target_first_ms is None and adverse_first_ms is None:
        first_hit = "none_or_unmatured"
    elif target_first_ms is None:
        first_hit = "adverse_first"
    elif adverse_first_ms is None:
        first_hit = "net_target_first"
    elif target_first_ms < adverse_first_ms:
        first_hit = "net_target_first"
    elif adverse_first_ms < target_first_ms:
        first_hit = "adverse_first"
    else:
        first_hit = "ambiguous_same_timestamp"
    if not first_hit_rows or all(row[2] is None for row in first_hit_rows):
        action_neutral_first_hit = "unavailable"
    elif neutral_target_first_ms is None and neutral_adverse_first_ms is None:
        action_neutral_first_hit = "none"
    elif neutral_target_first_ms is None:
        action_neutral_first_hit = "adverse_first"
    elif neutral_adverse_first_ms is None:
        action_neutral_first_hit = "net_target_first"
    elif neutral_target_first_ms < neutral_adverse_first_ms:
        action_neutral_first_hit = "net_target_first"
    elif neutral_adverse_first_ms < neutral_target_first_ms:
        action_neutral_first_hit = "adverse_first"
    else:
        action_neutral_first_hit = "ambiguous_same_timestamp"
    allocator_joined = (
        allocator_provenance.get("status") == "central_allocator_provenance_joined"
    )
    reviewed_cost_profile = bool(
        (evidence.get("economics") or {}).get("cost_profile_verified") is True
        and fixed_cost is not None
    )
    if stage in position_like_stages:
        action_neutral_cost_treatment = "identical_proportional_exit_cost_cancels"
        action_neutral_economic_grade = "liquidity_adjusted_incremental_exit_value"
        cost_invariant_between_exit_timings = True
    elif reviewed_cost_profile:
        action_neutral_cost_treatment = "reviewed_roundtrip_cost_subtracted"
        action_neutral_economic_grade = (
            "reviewed_after_cost_entry_value"
            if allocator_joined
            else "standardized_one_share_after_cost_observation_only"
        )
        cost_invariant_between_exit_timings = False
    else:
        action_neutral_cost_treatment = "verified_roundtrip_cost_unavailable"
        action_neutral_economic_grade = "research_only_unavailable"
        cost_invariant_between_exit_timings = False
    quantity_authority_eligible = bool(
        (stage in entry_like_stages and allocator_joined)
        or (
            stage in position_like_stages
            and position_provenance.get("position_execution_eligible") is True
        )
    )
    notional_net_profit_eligible = bool(
        quantity_authority_eligible
        and reviewed_cost_profile
        and quantity
        and baseline_vwap is not None
        and not outcome_eligibility_blockers
    )
    economic_promotion_evidence_eligible = bool(
        notional_net_profit_eligible
        and any(horizon.get("mature") is True for horizon in horizons)
    )
    confirmation_window_axis = _confirmation_window_outcome_axis(
        evidence=evidence,
        market_rows=market_source_rows,
        config=selected_config,
    )
    _validate_confirmation_window_axis(
        confirmation_window_axis,
        expected_horizons_sec=selected_config.reversion_confirmation_horizons_sec,
        expected_followthrough_horizons_sec=(
            selected_config.reversion_followthrough_horizons_sec
        ),
        expected_confirmation_fraction=(
            selected_config.reversion_confirmation_fraction
        ),
        expected_max_endpoint_lag_ms=selected_config.max_outcome_endpoint_lag_ms,
        expected_max_internal_gap_ms=selected_config.max_outcome_internal_gap_ms,
        expected_max_quote_age_ms=selected_config.max_quote_age_ms,
    )
    outcome_without_hash = {
        "schema": OUTCOME_SCHEMA,
        "bridge_config_sha256": selected_contract["config_sha256"],
        "bridge_producer_version": BRIDGE_PRODUCER_VERSION,
        "decision_trace_id": evidence.get("decision_trace_id"),
        "evidence_sha256": evidence.get("evidence_sha256"),
        "label_role": "counterfactual_outcome_only_never_prompt_input",
        "decision_stage": stage,
        "control_action": action or None,
        "evaluation_basis": evaluation_basis,
        "execution_basis": (
            "same_epoch_fresh_0b_0d_conservative_participation_full_quantity_sweep"
        ),
        "future_depth_participation_rate": _finite_float(
            conservative.get("participation_rate")
        ),
        "counterfactual_quantity": quantity,
        "counterfactual_quantity_basis": quantity_basis,
        "quantity_authority": allocator_provenance.get("quantity_authority"),
        "allocator_provenance_status": allocator_provenance.get("status"),
        "allocator_event_sha256": allocator_provenance.get("allocator_event_sha256"),
        "allocator_source_event_sha256s": allocator_provenance.get(
            "allocator_source_event_sha256s"
        ),
        "allocator_first_event_timestamp_ms": allocator_provenance.get(
            "allocator_first_event_timestamp_ms"
        ),
        "allocator_last_event_timestamp_ms": allocator_provenance.get(
            "allocator_last_event_timestamp_ms"
        ),
        "formula_version": allocator_provenance.get("formula_version"),
        "effective_qty": allocator_provenance.get("effective_qty"),
        "liquidity_capped_qty": (
            quantity if allocator_joined and stage in entry_like_stages else None
        ),
        "allocator_matching_row_count": allocator_provenance.get("matching_row_count"),
        "allocator_deduplicated_event_count": allocator_provenance.get(
            "deduplicated_event_count"
        ),
        "allocator_semantic_count": allocator_provenance.get(
            "allocator_semantic_count", 0
        ),
        "allocator_submitted_semantic_count": allocator_provenance.get(
            "allocator_submitted_semantic_count", 0
        ),
        "allocator_submitted_qty": allocator_provenance.get("submitted_qty"),
        "allocator_submission_coverage_pct": allocator_provenance.get(
            "submission_coverage_pct"
        ),
        "allocator_fully_submitted_semantic_count": allocator_provenance.get(
            "fully_submitted_semantic_count", 0
        ),
        "allocator_provenance_error": allocator_provenance.get(
            "allocator_provenance_error"
        ),
        "notional_net_profit_eligible": notional_net_profit_eligible,
        "economic_promotion_evidence_eligible": (economic_promotion_evidence_eligible),
        "economic_promotion_authority": False,
        "action_neutral_cost_treatment": action_neutral_cost_treatment,
        "action_neutral_economic_grade": action_neutral_economic_grade,
        "cost_invariant_between_exit_timings": (cost_invariant_between_exit_timings),
        "snapshot_execution_basis_vwap": baseline_vwap,
        "position_average_price": position_average_price,
        "outcome_eligibility": (
            (
                "eligible"
                if allocator_joined or stage in position_like_stages
                else "eligible_observation_only"
            )
            if not outcome_eligibility_blockers
            else "source_unavailable"
        ),
        "outcome_eligibility_blockers": sorted(set(outcome_eligibility_blockers)),
        "economic_evidence_grade": (
            "reviewed_cost_profile_offline_evaluation_only"
            if (evidence.get("economics") or {}).get("cost_profile_verified") is True
            and fixed_cost is not None
            else "research_assumption_only"
        ),
        "source_quality_blockers": sorted(
            set(outcome_eligibility_blockers)
            | {
                blocker
                for horizon in horizons
                for blocker in horizon.get("source_quality_blockers") or []
            }
        ),
        "first_hit": first_hit,
        "action_neutral_first_hit": action_neutral_first_hit,
        "target_first_delay_ms": (
            None if target_first_ms is None else target_first_ms - start_ms
        ),
        "adverse_first_delay_ms": (
            None if adverse_first_ms is None else adverse_first_ms - start_ms
        ),
        "action_neutral_target_first_delay_ms": (
            None
            if neutral_target_first_ms is None
            else neutral_target_first_ms - start_ms
        ),
        "action_neutral_adverse_first_delay_ms": (
            None
            if neutral_adverse_first_ms is None
            else neutral_adverse_first_ms - start_ms
        ),
        "confirmation_window_axis": confirmation_window_axis,
        "horizons": horizons,
        **OUTCOME_METRIC_CONTRACT,
        **AUTHORITY_CONTRACT,
    }
    return {
        **outcome_without_hash,
        "outcome_sha256": _sha256(outcome_without_hash),
    }


def build_future_outcome_rebuild_source(
    *,
    evidence: Mapping[str, Any],
    market_rows: Iterable[Mapping[str, Any]],
    depth_rows: Iterable[Mapping[str, Any]],
    entry_pipeline_rows: Iterable[Mapping[str, Any]],
    control_action: str | None,
    config: BridgeConfig,
    source_pool_rows: dict[str, dict[str, dict[str, Any]]],
) -> dict[str, Any]:
    """Intern one outcome's raw rows and persist only ordered hash references."""

    expected_pool_names = {"market", "depth", "entry_pipeline"}
    if set(source_pool_rows) != expected_pool_names or any(
        not isinstance(source_pool_rows.get(name), dict) for name in expected_pool_names
    ):
        raise ValueError("future_outcome_source_pool_builder_invalid")

    canonical = _canonical_future_outcome_source_rows(
        evidence=evidence,
        market_rows=market_rows,
        depth_rows=depth_rows,
        entry_pipeline_rows=entry_pipeline_rows,
        config=config,
    )

    def intern(name: str, rows: Iterable[Mapping[str, Any]]) -> tuple[list[str], int]:
        pool = source_pool_rows[name]
        references: list[str] = []
        row_count = 0
        for raw_row in rows:
            row = deepcopy(dict(raw_row))
            row_hash = _sha256(row)
            existing = pool.get(row_hash)
            if existing is not None and existing != row:
                raise ValueError("future_outcome_source_pool_hash_collision")
            pool.setdefault(row_hash, row)
            references.append(row_hash)
            row_count += 1
        return references, row_count

    market_refs, market_count = intern("market", canonical["market"])
    depth_refs, depth_count = intern("depth", canonical["depth"])
    entry_pipeline_refs, entry_pipeline_count = intern(
        "entry_pipeline", canonical["entry_pipeline"]
    )
    body = {
        "schema": OUTCOME_REBUILD_SOURCE_SCHEMA,
        "decision_trace_id": evidence.get("decision_trace_id"),
        "evidence_sha256": evidence.get("evidence_sha256"),
        "bridge_config": _bridge_config_contract(config),
        "control_action": str(control_action or "").strip().upper() or None,
        "market_row_count": market_count,
        "market_row_sha256s_sha256": _sha256(market_refs),
        "market_row_sha256s": market_refs,
        "depth_row_count": depth_count,
        "depth_row_sha256s_sha256": _sha256(depth_refs),
        "depth_row_sha256s": depth_refs,
        "entry_pipeline_row_count": entry_pipeline_count,
        "entry_pipeline_row_sha256s_sha256": _sha256(entry_pipeline_refs),
        "entry_pipeline_row_sha256s": entry_pipeline_refs,
        # Filled after the report-wide pool is finalized.  It is deliberately
        # excluded here to avoid a circular hash between the pool and refs.
        "source_pool_content_sha256": None,
        "provider_visible": False,
        "outcome_embedded_in_provider_input": False,
        **AUTHORITY_CONTRACT,
    }
    return {**body, "rebuild_source_sha256": _sha256(body)}


def build_future_outcome_source_pool(
    source_pool_rows: Mapping[str, Mapping[str, Mapping[str, Any]]],
) -> dict[str, Any]:
    """Finalize one report-wide, content-addressed raw outcome source pool."""

    expected_pool_names = ("market", "depth", "entry_pipeline")
    normalized: dict[str, dict[str, dict[str, Any]]] = {}
    counts: dict[str, int] = {}
    for name in expected_pool_names:
        raw_pool = source_pool_rows.get(name)
        if not isinstance(raw_pool, Mapping):
            raise ValueError("future_outcome_source_pool_group_missing")
        pool: dict[str, dict[str, Any]] = {}
        for row_hash, raw_row in raw_pool.items():
            if not isinstance(raw_row, Mapping):
                raise ValueError("future_outcome_source_pool_row_invalid")
            row = deepcopy(dict(raw_row))
            if str(row_hash or "") != _sha256(row):
                raise ValueError("future_outcome_source_pool_row_hash_invalid")
            pool[str(row_hash)] = row
        normalized[name] = pool
        counts[name] = len(pool)
    body = {
        "schema": OUTCOME_SOURCE_POOL_SCHEMA,
        "row_pools": normalized,
        "row_pool_counts": counts,
        "provider_visible": False,
        "outcome_embedded_in_provider_input": False,
        **AUTHORITY_CONTRACT,
    }
    return {**body, "source_pool_content_sha256": _sha256(body)}


def validate_future_outcome_source_pool(
    source_pool: Mapping[str, Any],
) -> dict[str, dict[str, dict[str, Any]]]:
    """Validate and return the exact content-addressed pool groups."""

    body = {
        key: value
        for key, value in source_pool.items()
        if key != "source_pool_content_sha256"
    }
    if (
        source_pool.get("schema") != OUTCOME_SOURCE_POOL_SCHEMA
        or source_pool.get("source_pool_content_sha256") != _sha256(body)
        or source_pool.get("provider_visible") is not False
        or source_pool.get("outcome_embedded_in_provider_input") is not False
    ):
        raise ValueError("future_outcome_source_pool_contract_invalid")
    for field, expected in AUTHORITY_CONTRACT.items():
        if source_pool.get(field) is not expected:
            raise ValueError(f"future_outcome_source_pool_authority_invalid:{field}")
    pools = source_pool.get("row_pools")
    counts = source_pool.get("row_pool_counts")
    if not isinstance(pools, Mapping) or not isinstance(counts, Mapping):
        raise ValueError("future_outcome_source_pool_census_invalid")
    expected_pool_names = {"market", "depth", "entry_pipeline"}
    if set(pools) != expected_pool_names or set(counts) != expected_pool_names:
        raise ValueError("future_outcome_source_pool_census_invalid")
    validated: dict[str, dict[str, dict[str, Any]]] = {}
    for name in sorted(expected_pool_names):
        raw_pool = pools.get(name)
        count = counts.get(name)
        if (
            not isinstance(raw_pool, Mapping)
            or isinstance(count, bool)
            or not isinstance(count, int)
            or count != len(raw_pool)
        ):
            raise ValueError("future_outcome_source_pool_census_invalid")
        pool: dict[str, dict[str, Any]] = {}
        for row_hash, raw_row in raw_pool.items():
            if not isinstance(raw_row, Mapping) or str(row_hash or "") != _sha256(
                raw_row
            ):
                raise ValueError("future_outcome_source_pool_row_hash_invalid")
            pool[str(row_hash)] = dict(raw_row)
        validated[name] = pool
    return validated


def validate_future_outcome_source_pool_reference_census(
    source_pool: Mapping[str, Any],
    rebuild_sources: Iterable[Mapping[str, Any]],
    *,
    _validated_source_pools: (
        Mapping[str, Mapping[str, Mapping[str, Any]]] | None
    ) = None,
) -> None:
    """Require every pooled row to be referenced by at least one report row."""

    pools = (
        _validated_source_pools
        if _validated_source_pools is not None
        else validate_future_outcome_source_pool(source_pool)
    )
    reference_field_by_pool = {
        "market": "market_row_sha256s",
        "depth": "depth_row_sha256s",
        "entry_pipeline": "entry_pipeline_row_sha256s",
    }
    referenced: dict[str, set[str]] = {
        pool_name: set() for pool_name in reference_field_by_pool
    }
    source_pool_hash = source_pool.get("source_pool_content_sha256")
    for rebuild_source in rebuild_sources:
        if not isinstance(rebuild_source, Mapping):
            raise ValueError("future_outcome_rebuild_source_census_invalid")
        body = {
            key: value
            for key, value in rebuild_source.items()
            if key != "rebuild_source_sha256"
        }
        if (
            rebuild_source.get("rebuild_source_sha256") != _sha256(body)
            or rebuild_source.get("source_pool_content_sha256") != source_pool_hash
        ):
            raise ValueError("future_outcome_rebuild_source_census_invalid")
        for pool_name, reference_field in reference_field_by_pool.items():
            references = rebuild_source.get(reference_field)
            if (
                not isinstance(references, list)
                or any(
                    not isinstance(value, str) or not _is_sha256(value)
                    for value in references
                )
                or len(references) != len(set(references))
            ):
                raise ValueError("future_outcome_rebuild_source_census_invalid")
            referenced[pool_name].update(references)
    if any(referenced[name] != set(pools[name]) for name in referenced):
        raise ValueError("future_outcome_source_pool_orphan_or_missing")


def bind_future_outcome_rebuild_source_to_pool(
    rebuild_source: Mapping[str, Any], *, source_pool_content_sha256: str
) -> dict[str, Any]:
    """Bind a compact row-reference proof to the finalized report-wide pool."""

    if not _is_sha256(source_pool_content_sha256):
        raise ValueError("future_outcome_source_pool_hash_invalid")
    body = {
        key: deepcopy(value)
        for key, value in rebuild_source.items()
        if key != "rebuild_source_sha256"
    }
    if body.get("source_pool_content_sha256") not in {None, source_pool_content_sha256}:
        raise ValueError("future_outcome_rebuild_source_pool_rebind_forbidden")
    body["source_pool_content_sha256"] = source_pool_content_sha256
    return {**body, "rebuild_source_sha256": _sha256(body)}


def rebuild_future_outcome_from_source(
    *,
    evidence: Mapping[str, Any],
    rebuild_source: Mapping[str, Any],
    source_pool: Mapping[str, Any],
    _validated_source_pools: (
        Mapping[str, Mapping[str, Mapping[str, Any]]] | None
    ) = None,
) -> dict[str, Any]:
    """Validate compact refs against the bound pool and rebuild one outcome."""

    content = {
        key: value
        for key, value in rebuild_source.items()
        if key != "rebuild_source_sha256"
    }
    if (
        rebuild_source.get("schema") != OUTCOME_REBUILD_SOURCE_SCHEMA
        or rebuild_source.get("rebuild_source_sha256") != _sha256(content)
        or rebuild_source.get("decision_trace_id") != evidence.get("decision_trace_id")
        or rebuild_source.get("evidence_sha256") != evidence.get("evidence_sha256")
        or rebuild_source.get("source_pool_content_sha256")
        != source_pool.get("source_pool_content_sha256")
        or rebuild_source.get("provider_visible") is not False
        or rebuild_source.get("outcome_embedded_in_provider_input") is not False
    ):
        raise ValueError("future_outcome_rebuild_source_contract_invalid")
    for field, expected in AUTHORITY_CONTRACT.items():
        if rebuild_source.get(field) is not expected:
            raise ValueError(f"future_outcome_rebuild_source_authority_invalid:{field}")
    source_pools = (
        _validated_source_pools
        if _validated_source_pools is not None
        else validate_future_outcome_source_pool(source_pool)
    )
    row_groups: dict[str, list[Mapping[str, Any]]] = {}
    for name in ("market", "depth", "entry_pipeline"):
        references = rebuild_source.get(f"{name}_row_sha256s")
        count = rebuild_source.get(f"{name}_row_count")
        if (
            not isinstance(references, list)
            or any(not _is_sha256(row_hash) for row_hash in references)
            or isinstance(count, bool)
            or not isinstance(count, int)
            or count != len(references)
            or rebuild_source.get(f"{name}_row_sha256s_sha256") != _sha256(references)
        ):
            raise ValueError(f"future_outcome_rebuild_source_{name}_census_invalid")
        pool = source_pools[name]
        rows: list[Mapping[str, Any]] = []
        for row_hash in references:
            row = pool.get(row_hash)
            if not isinstance(row, Mapping) or (
                _validated_source_pools is None and _sha256(row) != row_hash
            ):
                raise ValueError(
                    f"future_outcome_rebuild_source_{name}_reference_invalid"
                )
            rows.append(row)
        row_groups[name] = rows
    config_contract = rebuild_source.get("bridge_config")
    if not isinstance(config_contract, Mapping):
        raise ValueError("future_outcome_rebuild_source_config_missing")
    config = _bridge_config_from_contract(config_contract)
    canonical = _canonical_future_outcome_source_rows(
        evidence=evidence,
        market_rows=row_groups["market"],
        depth_rows=row_groups["depth"],
        entry_pipeline_rows=row_groups["entry_pipeline"],
        config=config,
    )
    if any(
        list(row_groups[name]) != canonical[name]
        for name in ("market", "depth", "entry_pipeline")
    ):
        raise ValueError("future_outcome_rebuild_source_noncanonical_rows")
    return build_future_outcome(
        evidence=evidence,
        market_rows=row_groups["market"],
        depth_rows=row_groups["depth"],
        entry_pipeline_rows=row_groups["entry_pipeline"],
        control_action=rebuild_source.get("control_action"),
        config=config,
    )


def _control_decision_findings(
    trace: Mapping[str, Any] | None,
    *,
    control_contract: Mapping[str, Any] | None = None,
) -> tuple[str, ...]:
    if not isinstance(trace, Mapping):
        return ("control_trace_missing",)
    findings: list[str] = []
    if not str(trace.get("decision_trace_id") or "").strip():
        findings.append("control_decision_trace_id_missing")
    if trace.get("provider_called") is not True:
        findings.append("control_provider_not_called")
    if str(trace.get("provider_actual") or "none").lower() == "none":
        findings.append("control_provider_none")
    if trace.get("timeout") is not False:
        findings.append("control_timeout_or_unknown")
    if trace.get("parse_ok") is not True:
        findings.append("control_parse_not_ok")
    if str(trace.get("result_source") or "") != "live":
        findings.append("control_result_not_live")
    if str(trace.get("decision_evaluation_status") or "") != "evaluated":
        findings.append("control_decision_not_evaluated")
    if trace.get("semantic_errors"):
        findings.append("control_semantic_errors_present")
    if trace.get("semantic_validator_applied") is not True:
        findings.append("control_semantic_validator_not_applied")
    if str(trace.get("semantic_validation_status") or "") != "pass":
        findings.append("control_semantic_validation_not_pass")
    if not str(trace.get("semantic_validator_version") or "").strip():
        findings.append("control_semantic_validator_version_missing")
    for field in (
        "endpoint",
        "prompt_version",
        "prompt_sha256",
        "model",
        "transport",
        "response_sha256",
        "request_envelope_sha256",
    ):
        if not str(trace.get(field) or "").strip():
            findings.append(f"control_{field}_missing")
    if not str(trace.get("provider_response_id") or "").strip():
        findings.append("control_provider_response_id_missing")
    if not (
        str(trace.get("response_schema_sha256") or "").strip()
        or str(trace.get("openai_response_schema_mode") or "").strip()
    ):
        findings.append("control_response_schema_contract_missing")
    provider_actual = str(trace.get("provider_actual") or "").strip().lower()
    response_schema_hash = str(trace.get("response_schema_sha256") or "").strip()
    response_schema_mode = str(trace.get("openai_response_schema_mode") or "").strip()
    response_schema_application = str(
        trace.get("response_schema_application") or ""
    ).strip()
    if provider_actual == "openai":
        if response_schema_hash:
            if response_schema_application != "provider_enforced_openai":
                findings.append("control_openai_response_schema_not_enforced")
        elif (
            response_schema_mode != "json_object"
            or response_schema_application != "provider_json_object_openai"
        ):
            findings.append("control_openai_json_contract_not_enforced")
    elif provider_actual == "bedrock":
        if response_schema_application != ("local_expected_only_not_sent_to_bedrock"):
            findings.append("control_bedrock_local_response_contract_missing")
    elif provider_actual:
        findings.append("control_provider_response_contract_unsupported")
    contract = control_contract if isinstance(control_contract, Mapping) else {}
    for field in (
        "schema_name",
        "response_schema_mode",
        "semantic_validator_version",
    ):
        if not str(contract.get(field) or "").strip():
            findings.append(f"control_replay_{field}_missing")
    if contract.get("semantic_validator_version") != trace.get(
        "semantic_validator_version"
    ):
        findings.append("control_replay_semantic_validator_mismatch")
    if _nonnegative_int(contract.get("max_output_tokens")) in (None, 0):
        findings.append("control_replay_max_output_tokens_missing")
    if not isinstance(contract.get("require_json"), bool):
        findings.append("control_replay_require_json_missing")
    if not isinstance(contract.get("response_schema_registry_used"), bool):
        findings.append("control_replay_schema_registry_status_missing")
    stage = str(trace.get("decision_stage") or "").lower()
    actions = {
        "entry_screen": {"BUY", "WAIT", "DROP"},
        "entry": {"BUY", "WAIT", "DROP"},
        "entry_price": {
            "USE_DEFENSIVE",
            "USE_REFERENCE",
            "IMPROVE_LIMIT",
            "SKIP",
        },
        "holding": {"HOLD", "TRIM", "EXIT"},
        "holding_score": {"HOLD", "TRIM", "EXIT"},
        "holding_flow": {"HOLD", "TRIM", "EXIT"},
        "post_probe": {"CONTINUE", "STOP"},
        "scale_in": {"ADD", "NO_ADD"},
        "exit": {"HOLD", "TRIM", "EXIT"},
        "overnight": {"HOLD_OVERNIGHT", "EXIT_BEFORE_CLOSE"},
    }
    action = str(trace.get("action") or "").upper()
    if stage not in actions or action not in actions[stage]:
        findings.append("control_stage_action_invalid")
    if (
        stage in {"entry", "entry_screen"}
        and str(trace.get("decision_quality_contract_status") or "") != "pass"
    ):
        findings.append("control_entry_semantic_contract_not_pass")
    if stage == "entry_price":
        prompt_version = str(trace.get("prompt_version") or "").strip().lower()
        schema_name = str(contract.get("schema_name") or "").strip().lower()
        semantic_version = (
            str(trace.get("semantic_validator_version") or "").strip().lower()
        )
        v2_5_contract = any(
            "v2_5" in value for value in (prompt_version, schema_name, semantic_version)
        )
        v1_contract = (
            prompt_version == "entry_price_v1" or schema_name == "entry_price_v1"
        )
        if v2_5_contract:
            if str(trace.get("entry_price_v2_5_contract_status") or "") != "pass":
                findings.append("control_entry_price_v2_5_contract_not_pass")
        elif v1_contract:
            if semantic_version != "live_entry_price_v1_schema_semantic_v1":
                findings.append("control_entry_price_v1_validator_version_invalid")
            if str(trace.get("entry_price_v1_contract_status") or "") != "pass":
                findings.append("control_entry_price_v1_contract_not_pass")
            if trace.get("entry_price_v1_contract_errors") or trace.get(
                "entry_price_v1_forensic_errors"
            ):
                findings.append("control_entry_price_v1_semantic_errors_present")
        else:
            findings.append("control_entry_price_semantic_contract_unknown")
    return tuple(sorted(set(findings)))


def build_three_arm_manifest(
    *,
    evidence: Mapping[str, Any],
    ablation_design_version: str,
    control_prompt_version: str,
    control_contract: Mapping[str, Any] | None = None,
    control_trace: Mapping[str, Any] | None = None,
    outcome: Mapping[str, Any] | None = None,
    ask_depletion_sidecar: Mapping[str, Any] | None = None,
    current_source_gap_reason: str | None = None,
) -> dict[str, Any]:
    """Describe three replay arms plus a non-comparable captured reference."""

    exact_hash = str(evidence.get("source_exact_payload_sha256") or "")
    evidence_hash = str(evidence.get("evidence_sha256") or "")
    normalized_source_gap_reason = str(current_source_gap_reason or "").strip()
    if ablation_design_version == CURRENT_DESIGN_VERSION:
        if ask_depletion_sidecar is None:
            if not normalized_source_gap_reason:
                raise ValueError("ask_depletion_current_design_sidecar_missing")
            ask_feature_view = None
        else:
            if normalized_source_gap_reason:
                raise ValueError(
                    "ask_depletion_current_design_gap_conflicts_with_sidecar"
                )
            ask_feature_view = _validated_ask_depletion_feature_view(
                ask_depletion_sidecar,
                evidence=evidence,
            )
    elif ablation_design_version == LEGACY_DESIGN_VERSION:
        if ask_depletion_sidecar is not None or normalized_source_gap_reason:
            raise ValueError("ask_depletion_legacy_design_sidecar_forbidden")
        ask_feature_view = None
    else:
        raise ValueError("micro_reversion_ablation_design_version_invalid")
    if ablation_design_version == LEGACY_DESIGN_VERSION:
        design_version = LEGACY_DESIGN_VERSION
        design_arms = LEGACY_ARMS
        base_identity = {"source_exact_payload_sha256": exact_hash}
        enriched_identity = {
            **base_identity,
            "tactical_micro_reversion_evidence_sha256": evidence_hash,
        }
        feature_comparison = "micro_context_effect"
        feature_axis = "tactical_micro_reversion_context_only"
    else:
        design_version = CURRENT_DESIGN_VERSION
        design_arms = CURRENT_ARMS
        base_identity = {
            "source_exact_payload_sha256": exact_hash,
            "tactical_micro_reversion_evidence_sha256": evidence_hash,
        }
        enriched_identity = {
            **base_identity,
            "ask_depletion_contract_sha256": (
                ask_feature_view["ask_depletion_contract_sha256"]
                if ask_feature_view is not None
                else None
            ),
            "ask_depletion_context_sha256": (
                ask_feature_view["ask_depletion_context_sha256"]
                if ask_feature_view is not None
                else None
            ),
        }
        feature_comparison = "ask_depletion_feature_effect"
        feature_axis = "ask_liquidity_depletion_context_only"
    base_pair_hash = _sha256(base_identity)
    enriched_pair_hash = (
        _sha256(enriched_identity) if ask_feature_view is not None else None
    )
    contract = dict(control_contract or {})
    locked_contract = {
        "prompt_sha256": contract.get("prompt_sha256"),
        "provider": contract.get("provider"),
        "model": contract.get("model"),
        "temperature": contract.get("temperature"),
        "reasoning_effort": contract.get("reasoning_effort"),
        "transport": contract.get("transport"),
        "schema_name": contract.get("schema_name"),
        "require_json": contract.get("require_json"),
        "response_schema_mode": contract.get("response_schema_mode"),
        "response_schema_registry_used": contract.get("response_schema_registry_used"),
        "max_output_tokens": contract.get("max_output_tokens"),
        "response_schema_sha256": contract.get("response_schema_sha256"),
        "semantic_validator_version": contract.get("semantic_validator_version"),
    }
    observation_context_eligible = bool(
        (evidence.get("source_quality") or {}).get("status") == "pass"
        and evidence.get("state") not in {"not_applicable", "source_unavailable"}
    )
    semantic_identity_verified = (
        evidence.get("exact_replay_source_semantic_status")
        == "stored_semantic_hash_verified"
    )
    context_eligible = bool(
        observation_context_eligible
        and semantic_identity_verified
        and (ask_feature_view is not None or design_version == LEGACY_DESIGN_VERSION)
    )
    control_findings = _control_decision_findings(
        control_trace,
        control_contract=locked_contract,
    )
    control_eligible = not control_findings
    materialization_blockers = (
        [f"ask_depletion_source_gap:{normalized_source_gap_reason}"]
        if normalized_source_gap_reason
        else []
    )
    replay_arm_materialization_status = (
        "ask_depletion_source_gap_blocked"
        if materialization_blockers
        else "replay_request_materialization_required"
    )
    candidate_arm_materialization_status = (
        "ask_depletion_source_gap_blocked"
        if materialization_blockers
        else "candidate_prompt_contract_required"
    )
    outcome_economic_eligible = False
    if isinstance(outcome, Mapping):
        outcome_without_hash = {
            key: value for key, value in outcome.items() if key != "outcome_sha256"
        }
        if (
            outcome.get("schema") != OUTCOME_SCHEMA
            or outcome.get("evidence_sha256") != evidence_hash
            or outcome.get("decision_trace_id") != evidence.get("decision_trace_id")
            or outcome.get("outcome_sha256") != _sha256(outcome_without_hash)
            or any(
                outcome.get(field) is not expected
                for field, expected in AUTHORITY_CONTRACT.items()
            )
        ):
            raise ValueError("three_arm_outcome_contract_invalid")
        outcome_economic_eligible = bool(
            outcome.get("notional_net_profit_eligible") is True
            and outcome.get("economic_promotion_evidence_eligible") is True
            and outcome.get("economic_promotion_authority") is False
        )
    economic_eligible = bool(
        context_eligible
        and (evidence.get("source_quality") or {}).get("liquidity_capacity_status")
        == "pass"
        and (evidence.get("economics") or {}).get("cost_profile_verified") is True
        and (evidence.get("economics") or {}).get("minimum_gross_target_bps")
        is not None
        and outcome_economic_eligible
        and (evidence.get("economics") or {}).get("cost_profile_artifact_sha256")
        is not None
    )
    return {
        "schema": THREE_ARM_SCHEMA,
        "ablation_design_version": design_version,
        "ablation_arms": list(design_arms),
        "decision_trace_id": evidence.get("decision_trace_id"),
        "captured_natural_reference": {
            "prompt_version": control_prompt_version,
            **locked_contract,
            "action": (control_trace or {}).get("action"),
            "score": (control_trace or {}).get("score"),
            "reason_codes": list((control_trace or {}).get("reason_codes") or []),
            "model_edge_state": (control_trace or {}).get(
                "decision_quality_model_edge_state"
            ),
            "model_evidence": deepcopy(
                (control_trace or {}).get("decision_quality_model_evidence")
            ),
            "response_sha256": (control_trace or {}).get("response_sha256"),
            "provider_user_input_sha256": evidence.get(
                "source_provider_payload_sha256"
            ),
            "request_envelope_sha256": evidence.get("source_request_envelope_sha256"),
            "comparable_as_micro_only_arm": False,
            "reason": "captured_provider_input_representation_differs_from_replay_input",
        },
        "replay_arms": [
            {
                "arm": design_arms[0],
                "prompt_version": control_prompt_version,
                **locked_contract,
                **base_identity,
                "analytical_context_pair_sha256": base_pair_hash,
                "actual_provider_input_identity_sha256": None,
                "materialization_status": replay_arm_materialization_status,
            },
            {
                "arm": design_arms[1],
                "prompt_version": control_prompt_version,
                **locked_contract,
                **enriched_identity,
                "analytical_context_pair_sha256": enriched_pair_hash,
                "actual_provider_input_identity_sha256": None,
                "materialization_status": replay_arm_materialization_status,
            },
            {
                "arm": design_arms[2],
                "prompt_version": None,
                "status": "candidate_prompt_contract_required",
                "provider": contract.get("provider"),
                "model": contract.get("model"),
                "temperature": contract.get("temperature"),
                "reasoning_effort": contract.get("reasoning_effort"),
                "transport": contract.get("transport"),
                "schema_name": contract.get("schema_name"),
                "require_json": contract.get("require_json"),
                "response_schema_mode": contract.get("response_schema_mode"),
                "response_schema_registry_used": contract.get(
                    "response_schema_registry_used"
                ),
                "max_output_tokens": contract.get("max_output_tokens"),
                "response_schema_sha256": contract.get("response_schema_sha256"),
                "semantic_validator_version": contract.get(
                    "semantic_validator_version"
                ),
                **enriched_identity,
                "analytical_context_pair_sha256": enriched_pair_hash,
                "actual_provider_input_identity_sha256": None,
                "materialization_status": candidate_arm_materialization_status,
            },
        ],
        "feature_effect_comparison": f"{design_arms[0]}_vs_{design_arms[1]}",
        "micro_effect_comparison": f"{design_arms[0]}_vs_{design_arms[1]}",
        "feature_effect_comparison_role": feature_comparison,
        "feature_effect_changed_axis": feature_axis,
        "prompt_effect_comparison": f"{design_arms[1]}_vs_{design_arms[2]}",
        "prompt_effect_comparison_role": (
            "prompt_contract_effect_conditional_on_ask_depletion"
            if design_version == CURRENT_DESIGN_VERSION
            else "prompt_contract_effect"
        ),
        "identical_exact_payload_across_replay_arms": True,
        "identical_micro_context_between_enriched_replay_arms": True,
        "actual_provider_input_hash_parity_verified": False,
        "provider_call_performed": False,
        "replay_context_eligible": context_eligible,
        "observation_context_eligible": observation_context_eligible,
        "provider_input_semantic_identity_verified": semantic_identity_verified,
        "control_decision_eligible": control_eligible,
        "control_decision_exclusion_reasons": list(control_findings),
        "paired_decision_quality_eligible": context_eligible and control_eligible,
        "paired_replay_materialization_eligible": (
            context_eligible and control_eligible
        ),
        "materialization_blockers": materialization_blockers,
        "paired_replay_ready": False,
        "net_economic_evaluation_eligible": economic_eligible,
        "promotion_evidence_eligible": False,
        **AUTHORITY_CONTRACT,
    }


def _validate_tactical_evidence_shape(evidence: Mapping[str, Any]) -> None:
    top_level = {
        "schema",
        "evidence_version",
        "bridge_config_sha256",
        "bridge_producer_version",
        "decision_trace_id",
        "request_id",
        "decision_stage",
        "source_provider_payload_sha256",
        "source_exact_payload_sha256",
        "source_request_envelope_sha256",
        "snapshot_id",
        "stock_code",
        "trace_effective_venue",
        "trace_session_bucket",
        "trace_decision_ts",
        "trace_market_data_route",
        "integrated_sor_route_proven",
        "micro_venue",
        "micro_session_bucket",
        "sequence_epoch",
        "snapshot_captured_at",
        "snapshot_captured_at_ms",
        "provider_payload_semantic_hash_status",
        "exact_replay_source_semantic_status",
        "decision_watermark",
        "depth_watermark",
        "state",
        "event",
        "tape",
        "orderbook",
        "economics",
        "liquidity_capacity",
        "source_quality",
        LIFECYCLE_PROJECTION_SCHEMA,
        "evidence_sha256",
        *METRIC_CONTRACT,
        *AUTHORITY_CONTRACT,
    }
    unknown = set(evidence) - top_level
    if unknown:
        raise ValueError(
            "micro_context_unknown_top_level_field:" + ",".join(sorted(unknown))
        )

    # These identities are exact source bindings.  Never allow Python's
    # ``str``/symbol normalization coercions to turn a resealed non-string
    # value into an apparently valid ask-depletion scope.
    for field in ("stock_code", "micro_venue", "micro_session_bucket"):
        value = evidence.get(field)
        if not isinstance(value, str) or value != value.strip():
            raise ValueError(f"micro_context_native_string_invalid:{field}")
    event_identity = evidence.get("event")
    if isinstance(event_identity, Mapping) and "shock_event_id" in event_identity:
        shock_event_id = event_identity.get("shock_event_id")
        if (
            not isinstance(shock_event_id, str)
            or not shock_event_id
            or shock_event_id != shock_event_id.strip()
        ):
            raise ValueError("micro_context_native_string_invalid:event.shock_event_id")

    def require_native_positive_int(
        container: Mapping[str, Any],
        field: str,
        *,
        optional: bool = False,
        allow_zero_for_source_unavailable: bool = False,
    ) -> None:
        value = container.get(field)
        if optional and value is None:
            return
        if (
            allow_zero_for_source_unavailable
            and evidence.get("state") == "source_unavailable"
            and (
                value is None
                or (
                    isinstance(value, int)
                    and not isinstance(value, bool)
                    and value == 0
                )
            )
        ):
            return
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError(f"micro_context_native_positive_int_invalid:{field}")

    require_native_positive_int(
        evidence,
        "sequence_epoch",
        allow_zero_for_source_unavailable=True,
    )
    require_native_positive_int(
        evidence,
        "snapshot_captured_at_ms",
        allow_zero_for_source_unavailable=True,
    )
    if isinstance(event_identity, Mapping):
        for field in ("event_detected_at_ms", "event_source_sequence"):
            require_native_positive_int(event_identity, field, optional=True)
    for watermark_name in ("decision_watermark", "depth_watermark"):
        watermark = evidence.get(watermark_name)
        if isinstance(watermark, Mapping):
            require_native_positive_int(
                watermark,
                "source_sequence",
                optional=True,
            )

    allowed_by_path: dict[tuple[str, ...], set[str]] = {
        ("decision_watermark",): {
            "local_receive_timestamp",
            "source_sequence",
            "past_only_join",
        },
        ("depth_watermark",): {
            "local_receive_timestamp",
            "source_sequence",
            "past_only_join",
        },
        ("event",): {
            "parent_wave_id",
            "path_segment_id",
            "shock_event_id",
            "shock_horizon_ms",
            "event_sequence_in_wave",
            "event_detected_at_ms",
            "event_source_sequence",
            "reference_price",
            "shock_price",
            "post_shock_low_price",
            "asof_trade_price",
            "shock_bps",
            "reclaim_from_low_bps",
            "reclaim_fraction",
            "remaining_to_reference_bps",
            "half_reclaim_first_source_sequence",
            "half_reclaim_reference_low_price",
            "new_low_after_half_reclaim",
            "recovery_invalidation_count",
            "latest_recovery_cycle_reconfirmed",
        },
        ("tape",): {
            "early",
            "recent",
            "latest_recovery_cycle_support",
            "window_sec",
            "early_window_end_ms",
            "recent_window_start_ms",
            "deceleration_windows_nonoverlap",
            "sell_pressure_deceleration",
        },
        ("tape", "early"): {
            "buy_qty",
            "sell_qty",
            "unknown_qty",
            "known_qty",
            "buy_ratio",
            "sell_ratio",
            "sample_count",
        },
        ("tape", "recent"): {
            "buy_qty",
            "sell_qty",
            "unknown_qty",
            "known_qty",
            "buy_ratio",
            "sell_ratio",
            "sample_count",
        },
        ("tape", "latest_recovery_cycle_support"): {
            "buy_qty",
            "sell_qty",
            "unknown_qty",
            "known_qty",
            "buy_ratio",
            "sell_ratio",
            "sample_count",
            "cycle_low_source_sequence",
            "confirmation_source_sequence",
        },
        ("orderbook",): {
            "best_bid",
            "best_ask",
            "best_bid_qty",
            "best_ask_qty",
            "bid_depth",
            "ask_depth",
            "spread_bps",
            "same_epoch_bid_depth_change_qty",
            "bid_replenishment_same_price_basis",
            "bid_replenishment_price_path_status",
            "depth_age_ms",
            "depth_join_status",
        },
        ("economics",): {
            "cost_profile_source",
            "cost_profile_verified",
            "cost_profile_contract_verified",
            "cost_profile_tax_scope_match",
            "cost_profile_scope_status",
            "cost_profile_artifact_id",
            "cost_profile_artifact_sha256",
            "cost_profile_effective_date",
            "cost_profile_venues",
            "cost_catalog_content_sha256",
            "selected_cost_profile_id",
            "selected_cost_profile_content_sha256",
            "symbol_metadata_status",
            "symbol_metadata_record_sha256",
            "symbol_master_artifact_sha256",
            "symbol_metadata_source",
            "symbol_metadata_source_reference",
            "symbol_metadata_verified_at",
            "listing_market",
            "instrument_type",
            "instrument_tax_class",
            "buy_fee_bps",
            "sell_fee_bps",
            "statutory_sell_tax_bps",
            "uncertainty_buffer_bps",
            "counterfactual_roundtrip_execution_bps",
            "spread_double_counted",
            "all_in_cost_bps",
            "minimum_net_profit_bps",
            "minimum_gross_target_bps",
            "economic_source_quality_status",
        },
        ("liquidity_capacity",): {
            "capacity_quality_status",
            "target_liquidation_sec",
            "recent_tape_window_sec",
            "recent_aggressive_buy_qty",
            "aggressive_buy_role",
            "counterfactual_liquidity_qty_grid",
            "counterfactual_liquidity_qty_ceiling",
            "counterfactual_immediate_exit_qty_ceiling",
            "standardized_one_share_probe_observation_qty",
            "snapshot_depth_execution_basis",
            "quantity_authority_status",
        },
        ("liquidity_capacity", "snapshot_depth_execution_basis"): {
            "bid_levels",
            "ask_levels",
            "allocator_or_order_quantity_present",
        },
        ("source_quality",): {
            "status",
            "blockers",
            "liquidity_capacity_status",
            "liquidity_capacity_blockers",
            "rejected_market_reason_counts",
            "rejected_depth_reason_counts",
            "rejected_reference_reason_counts",
            "parent_wave_reference_count",
            "parent_wave_deduplicated",
            "future_outcome_fields_in_context",
        },
        (LIFECYCLE_PROJECTION_SCHEMA,): {
            "schema",
            "objective",
            "decision_stage",
            "entry_projection",
            "holding_projection",
            "exit_projection",
            *AUTHORITY_CONTRACT,
        },
        (LIFECYCLE_PROJECTION_SCHEMA, "entry_projection"): {
            "timing_owner",
            "ai_role",
            "minimum_gross_target_bps",
            "counterfactual_fast_roundtrip_capacity_qty",
            "counterfactual_full_position_exit_sweep_vwap",
            "live_price_or_order_effect",
        },
        (LIFECYCLE_PROJECTION_SCHEMA, "holding_projection"): {
            "review_cadence",
            "observed_position_qty",
            "counterfactual_free_to_sell_qty",
            "observed_position_average_price",
            "position_provenance",
            "counterfactual_fast_exit_capacity_qty",
            "counterfactual_snapshot_exit_sweep_vwap",
            "counterfactual_capacity_coverage_ratio",
            "counterfactual_uncovered_position_qty",
            "counterfactual_net_executable_pnl_bps",
            "scale_in_requires_fresh_recovery_and_verified_exit_capacity",
            "hard_protect_emergency_exit_priority_unchanged",
        },
        (
            LIFECYCLE_PROJECTION_SCHEMA,
            "holding_projection",
            "position_provenance",
        ): {
            "status",
            "quantity",
            "free_to_sell_quantity",
            "average_price",
            "open_sell_qty",
            "broker_reconciliation_contract_complete",
            "position_reconciled",
            "position_authority_reconciled",
            "position_reconciliation_mode",
            "simulation_position_reconciled",
            "broker_snapshot_age_sec",
            "max_broker_position_age_sec",
            "broker_position_fresh",
            "position_execution_eligible",
            "candidate_exit_rule",
            "active_hard_guard",
            "hard_exit_guard_observed",
            "cancel_pending",
            "exit_token_active",
            "quantity_conflict",
            "quantity_pointer",
            "free_to_sell_quantity_formula",
            "price_pointer",
        },
        (LIFECYCLE_PROJECTION_SCHEMA, "exit_projection"): {
            "profit_basis",
            "minimum_net_profit_bps",
            "counterfactual_net_target_reached",
            "counterfactual_immediately_executable_qty",
            "hard_protect_emergency_exit_priority_unchanged",
            "live_sell_or_cancel_effect",
        },
    }
    for path, allowed in allowed_by_path.items():
        value: Any = evidence
        for key in path:
            value = value.get(key) if isinstance(value, Mapping) else None
        if isinstance(value, Mapping):
            unknown = set(value) - allowed
            if unknown:
                raise ValueError(
                    "micro_context_unknown_field:"
                    + "/".join(path)
                    + ":"
                    + ",".join(sorted(unknown))
                )
    if evidence.get("bridge_producer_version") != BRIDGE_PRODUCER_VERSION or not str(
        evidence.get("bridge_config_sha256") or ""
    ):
        raise ValueError("micro_context_bridge_contract_invalid")
    trace_market_data_route = _route(evidence.get("trace_market_data_route"))
    integrated_sor_route_proven = evidence.get("integrated_sor_route_proven")
    micro_venue = normalize_venue(evidence.get("micro_venue"))
    source_quality = evidence.get("source_quality")
    source_quality = source_quality if isinstance(source_quality, Mapping) else {}
    source_blockers = set(source_quality.get("blockers") or [])
    source_unavailable = evidence.get("state") == "source_unavailable"
    if not isinstance(integrated_sor_route_proven, bool):
        raise ValueError("micro_context_route_provenance_invalid")
    if not trace_market_data_route:
        # A row already blocked as source-unavailable may retain an empty
        # route as diagnostic evidence. It cannot become replay/economic
        # eligible, while a usable row still requires exact route provenance.
        if not source_unavailable:
            raise ValueError("micro_context_route_provenance_invalid")
    elif "integrated" in trace_market_data_route or "sor" in trace_market_data_route:
        if micro_venue != "SOR":
            raise ValueError("micro_context_integrated_route_proof_invalid")
        if not integrated_sor_route_proven and (
            not source_unavailable
            or "integrated_route_proof_missing" not in source_blockers
        ):
            raise ValueError("micro_context_integrated_route_proof_invalid")
    elif integrated_sor_route_proven:
        raise ValueError("micro_context_integrated_route_proof_unexpected")
    elif trace_market_data_route in {"krx", "krx_only", "krx_regular"}:
        if micro_venue != "KRX":
            raise ValueError("micro_context_route_venue_mismatch")
    elif trace_market_data_route in {"nxt", "nxt_only", "nxt_regular"}:
        if micro_venue != "NXT":
            raise ValueError("micro_context_route_venue_mismatch")
    elif not source_unavailable:
        raise ValueError("micro_context_route_provenance_invalid")
    grid = (evidence.get("liquidity_capacity") or {}).get(
        "counterfactual_liquidity_qty_grid"
    )
    allowed_grid_fields = {
        "participation_rate",
        "entry_ask_capacity_qty",
        "depth_only_fast_exit_capacity_qty",
        "immediate_roundtrip_depth_capacity_qty",
        "strict_depth_participation_capacity_qty",
        "immediate_marketable_exit_capacity_qty",
        "one_share_probe_floor_applied",
        "immediate_exit_one_share_floor_applied",
        "passive_ask_fill_support_qty",
        "depth_only_roundtrip_capacity_qty",
        "counterfactual_liquidity_bounded_qty",
        "standardized_one_share_probe_observation_qty",
        "counterfactual_entry_sweep_vwap",
        "counterfactual_exit_sweep_vwap",
        "counterfactual_roundtrip_execution_bps",
    }
    if isinstance(grid, list) and any(
        not isinstance(row, Mapping) or set(row) - allowed_grid_fields for row in grid
    ):
        raise ValueError("micro_context_liquidity_grid_schema_invalid")
    depth_execution_basis = (evidence.get("liquidity_capacity") or {}).get(
        "snapshot_depth_execution_basis"
    )
    if not isinstance(depth_execution_basis, Mapping) or (
        depth_execution_basis.get("allocator_or_order_quantity_present") is not False
    ):
        raise ValueError("micro_context_depth_basis_quantity_authority_invalid")
    liquidity = evidence.get("liquidity_capacity") or {}
    if any(
        field in liquidity
        for field in (
            "existing_position_formula_candidate_qty",
            "existing_quantity_provenance",
            "existing_quantity_owner",
            "quantity_owner_status",
            "formula_version",
            "effective_qty",
            "allocator_event_sha256",
        )
    ):
        raise ValueError("micro_context_allocator_authority_leak")


def _validate_replay_candidate_ledgers(
    *,
    candidate_input: Mapping[str, Any],
    exact_payload: Mapping[str, Any],
    request: Mapping[str, Any],
    decision_stage: str,
) -> None:
    """Rebuild every optional ledger from the immutable exact payload."""

    ledger_keys = set(candidate_input) - {"exact_payload"}
    if not ledger_keys:
        return
    # Lazy imports keep the source-only bridge import-independent from the
    # provider replay implementation while still using its canonical builders.
    from src.engine.scalping import ai_decision_quality as quality
    from src.engine.scalping.entry_setup_evidence import build_entry_setup_evidence

    stage = str(request.get("stage") or decision_stage or "").strip().lower()
    normalized_stage = (
        "entry"
        if stage in {"entry", "entry_screen", "gatekeeper", "post_probe"}
        else (
            "holding"
            if stage in {"holding", "holding_score", "holding_flow", "exit"}
            else stage
        )
    )
    expected: dict[str, Mapping[str, Any]] = {}
    if "exact_payload_analysis_v1" in ledger_keys:
        if normalized_stage != "entry":
            raise ValueError("exact_payload_analysis_stage_invalid")
        expected["exact_payload_analysis_v1"] = quality.build_exact_payload_analysis_v1(
            dict(exact_payload), stage="entry"
        )
    if "anticipatory_reversal_analysis_v1" in ledger_keys:
        if normalized_stage != "entry":
            raise ValueError("anticipatory_reversal_analysis_stage_invalid")
        base = quality.build_anticipatory_reversal_analysis_v1(
            dict(exact_payload), stage="entry"
        )
        selective = quality._attach_selective_recovery_probe_contract_v1(base)
        recovery = quality.build_v2_13_recovery_confirmation_analysis_v1(
            dict(exact_payload), stage="entry"
        )
        supplied = candidate_input["anticipatory_reversal_analysis_v1"]
        if not any(
            _sha256(supplied) == _sha256(candidate)
            for candidate in (base, selective, recovery)
        ):
            raise ValueError(
                "candidate_input_ledger_rebuild_mismatch:"
                "anticipatory_reversal_analysis_v1"
            )
        expected["anticipatory_reversal_analysis_v1"] = supplied
    if "holding_exact_contract_facts_v1" in ledger_keys:
        if normalized_stage != "holding":
            raise ValueError("holding_exact_contract_facts_stage_invalid")
        expected["holding_exact_contract_facts_v1"] = quality._holding_contract_facts(
            dict(exact_payload)
        )
    if "entry_price_exact_contract_facts_v1" in ledger_keys:
        if normalized_stage != "entry_price":
            raise ValueError("entry_price_exact_contract_facts_stage_invalid")
        control = request.get("control")
        control = control if isinstance(control, Mapping) else {}
        captured_action = str(control.get("captured_action") or "").upper()
        if not captured_action:
            raise ValueError("entry_price_control_action_missing")
        expected["entry_price_exact_contract_facts_v1"] = (
            quality.build_entry_price_explicit_fill_value_contract(
                dict(exact_payload),
                control_selected_price=control.get("captured_selected_price"),
                control_exposure_selected=captured_action != "SKIP",
            )
        )
    if "entry_setup_evidence_v1" in ledger_keys:
        if normalized_stage != "entry":
            raise ValueError("entry_setup_evidence_stage_invalid")
        exact_analysis = candidate_input.get("exact_payload_analysis_v1")
        recovery_analysis = candidate_input.get("anticipatory_reversal_analysis_v1")
        if not isinstance(exact_analysis, Mapping) or not isinstance(
            recovery_analysis, Mapping
        ):
            raise ValueError("entry_setup_evidence_dependencies_missing")
        expected["entry_setup_evidence_v1"] = build_entry_setup_evidence(
            exact_payload=dict(exact_payload),
            exact_analysis=dict(exact_analysis),
            recovery_analysis=dict(recovery_analysis),
        )
    for ledger_key, expected_ledger in expected.items():
        if _sha256(candidate_input.get(ledger_key)) != _sha256(expected_ledger):
            raise ValueError(f"candidate_input_ledger_rebuild_mismatch:{ledger_key}")


def attach_micro_context_to_replay_request(
    request: Mapping[str, Any],
    evidence: Mapping[str, Any],
    *,
    source_trace: Mapping[str, Any] | None = None,
    source_payload: Mapping[str, Any] | None = None,
    source_market_rows: Iterable[Mapping[str, Any]] = (),
    source_depth_rows: Iterable[Mapping[str, Any]] = (),
    source_event_references: Iterable[Mapping[str, Any]] = (),
    config: BridgeConfig | None = None,
    excluded_scopes: set[tuple[str, str, str, int]] | None = None,
    verified_symbol_metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Opt-in replay enrichment; default Exact V2 request remains unchanged."""

    def contains_outcome_only_field(value: Any) -> bool:
        return any(
            key in OUTCOME_ONLY_FIELD_NAMES
            or key.startswith("post_decision_")
            or key.startswith("realized_")
            for row in _walk_objects(value)
            for key in row
        )

    if contains_outcome_only_field(evidence):
        raise ValueError("future_outcome_field_forbidden_in_context")
    for field, expected in AUTHORITY_CONTRACT.items():
        if field == "selection_authority":
            if field in request and request.get(field) is not expected:
                raise ValueError(f"request_authority_conflict:{field}")
            continue
        if request.get(field) is not expected:
            raise ValueError(f"request_authority_conflict:{field}")
    allowed_request_authorities = {
        "offline_replay_and_attribution_only",
        "offline_replay_no_runtime_change",
        "offline_supplemental_replay_no_runtime_change",
    }
    if request.get("decision_authority") not in allowed_request_authorities:
        raise ValueError("request_decision_authority_invalid")
    if evidence.get("schema") != TACTICAL_EVIDENCE_SCHEMA:
        raise ValueError("micro_context_schema_invalid")
    _validate_tactical_evidence_shape(evidence)
    if not isinstance(source_trace, Mapping) or not isinstance(source_payload, Mapping):
        raise ValueError("micro_context_source_rebuild_required")
    if config is None:
        raise ValueError("micro_context_bridge_config_required")
    if _bridge_config_contract(config)["config_sha256"] != evidence.get(
        "bridge_config_sha256"
    ):
        raise ValueError("micro_context_bridge_config_mismatch")
    rebuilt_evidence = build_tactical_evidence(
        trace=source_trace,
        payload=source_payload,
        market_rows=source_market_rows,
        depth_rows=source_depth_rows,
        event_references=source_event_references,
        config=config,
        excluded_scopes=excluded_scopes,
        verified_symbol_metadata=verified_symbol_metadata,
    )
    if _sha256(rebuilt_evidence) != _sha256(evidence):
        raise ValueError("micro_context_source_rebuild_mismatch")
    for field, expected in AUTHORITY_CONTRACT.items():
        if evidence.get(field) is not expected:
            raise ValueError(f"micro_context_authority_invalid:{field}")
    for field, expected in METRIC_CONTRACT.items():
        if _sha256(evidence.get(field)) != _sha256(expected):
            raise ValueError(f"micro_context_metric_contract_invalid:{field}")
    stored_evidence_hash = str(evidence.get("evidence_sha256") or "")
    evidence_without_hash = {
        key: value for key, value in evidence.items() if key != "evidence_sha256"
    }
    if (
        not stored_evidence_hash
        or _sha256(evidence_without_hash) != stored_evidence_hash
    ):
        raise ValueError("micro_context_evidence_sha256_mismatch")
    expected_trace = str(request.get("decision_trace_id") or "")
    if expected_trace != str(evidence.get("decision_trace_id") or ""):
        raise ValueError("decision_trace_id_mismatch")
    if normalize_symbol(request.get("stock_code")) != normalize_symbol(
        evidence.get("stock_code")
    ):
        raise ValueError("request_stock_code_mismatch")
    if _exact_venue(request.get("effective_venue")) != _exact_venue(
        evidence.get("trace_effective_venue")
    ):
        raise ValueError("request_effective_venue_mismatch")
    if _session(request.get("session_bucket")) != _session(
        evidence.get("trace_session_bucket")
    ):
        raise ValueError("request_session_bucket_mismatch")
    stage_alias = {
        "entry_screen": "entry",
        "holding_score": "holding",
        "holding_flow": "holding",
    }
    request_stage = stage_alias.get(
        str(request.get("stage") or "").lower(),
        str(request.get("stage") or "").lower(),
    )
    evidence_stage = stage_alias.get(
        str(evidence.get("decision_stage") or "").lower(),
        str(evidence.get("decision_stage") or "").lower(),
    )
    if not request_stage or request_stage != evidence_stage:
        raise ValueError("request_decision_stage_mismatch")
    if str(request.get("endpoint") or "") != str(
        source_payload.get("endpoint") or source_trace.get("endpoint") or ""
    ):
        raise ValueError("request_endpoint_mismatch")
    exact_payload = request.get("exact_payload")
    if not isinstance(exact_payload, dict):
        raise ValueError("exact_payload_missing")
    request_exact_hash = str(request.get("source_exact_payload_sha256") or "")
    if not request_exact_hash:
        raise ValueError("source_exact_payload_sha256_missing")
    if request_exact_hash != str(evidence.get("source_exact_payload_sha256") or ""):
        raise ValueError("source_exact_payload_sha256_mismatch")
    if _sha256(exact_payload) != request_exact_hash:
        raise ValueError("exact_payload_sha256_mismatch")
    if str(request.get("payload_sha256") or "") != str(
        evidence.get("source_provider_payload_sha256") or ""
    ):
        raise ValueError("provider_payload_sha256_mismatch")
    if str(request.get("request_envelope_sha256") or "") != str(
        evidence.get("source_request_envelope_sha256") or ""
    ):
        raise ValueError("request_envelope_sha256_mismatch")
    if (evidence.get("source_quality") or {}).get("status") != "pass":
        raise ValueError("micro_context_source_quality_not_pass")
    if evidence.get("state") in {"not_applicable", "source_unavailable", None}:
        raise ValueError("micro_context_state_not_replay_eligible")
    if (
        evidence.get("exact_replay_source_semantic_status")
        != "stored_semantic_hash_verified"
    ):
        raise ValueError("exact_replay_source_semantic_identity_unverified")
    allowed_schemas = {TACTICAL_EVIDENCE_SCHEMA, LIFECYCLE_PROJECTION_SCHEMA}
    if any(
        row.get("schema") not in allowed_schemas
        for row in _walk_objects(evidence)
        if "schema" in row
    ):
        raise ValueError("micro_context_nested_schema_invalid")
    candidate_input = request.get("candidate_input")
    candidate_input = (
        deepcopy(candidate_input)
        if isinstance(candidate_input, dict)
        else {"exact_payload": deepcopy(exact_payload)}
    )
    allowed_candidate_input_keys = {
        "exact_payload",
        *REPLAY_CANDIDATE_LEDGER_SCHEMAS,
    }
    unexpected_keys = set(candidate_input) - allowed_candidate_input_keys
    if unexpected_keys:
        raise ValueError(
            "candidate_input_unknown_ledger:" + ",".join(sorted(unexpected_keys))
        )
    existing_exact = candidate_input.get("exact_payload")
    if not isinstance(existing_exact, dict) or _sha256(existing_exact) != _sha256(
        exact_payload
    ):
        raise ValueError("candidate_input_exact_payload_mismatch")
    for ledger_key in set(candidate_input) - {"exact_payload"}:
        ledger = candidate_input.get(ledger_key)
        if not isinstance(ledger, Mapping) or ledger.get("schema") != ledger_key:
            raise ValueError(f"candidate_input_ledger_schema_invalid:{ledger_key}")
        unexpected_ledger_fields = (
            set(ledger) - REPLAY_CANDIDATE_LEDGER_FIELDS[ledger_key]
        )
        if unexpected_ledger_fields:
            raise ValueError(
                "candidate_input_ledger_unknown_field:"
                + ledger_key
                + ":"
                + ",".join(sorted(unexpected_ledger_fields))
            )
        if any(
            "oracle" in key.lower()
            or key.lower().startswith(("future_", "post_decision_", "realized_"))
            or key.lower() in OUTCOME_ONLY_FIELD_NAMES
            for row in _walk_objects(ledger)
            for key in row
        ):
            raise ValueError(f"candidate_input_ledger_causal_field:{ledger_key}")
        if ledger_key in {
            "exact_payload_analysis_v1",
            "anticipatory_reversal_analysis_v1",
        }:
            stored_hash = str(ledger.get("analysis_sha256") or "")
            without_hash = {
                key: value for key, value in ledger.items() if key != "analysis_sha256"
            }
            if not stored_hash or _sha256(without_hash) != stored_hash:
                raise ValueError(f"candidate_input_ledger_sha256_invalid:{ledger_key}")
        elif ledger_key == "entry_setup_evidence_v1":
            stored_hash = str(ledger.get("evidence_sha256") or "")
            without_hash = {
                key: value for key, value in ledger.items() if key != "evidence_sha256"
            }
            if not stored_hash or _sha256(without_hash) != stored_hash:
                raise ValueError(f"candidate_input_ledger_sha256_invalid:{ledger_key}")
    if any(
        contains_outcome_only_field(value)
        for key, value in candidate_input.items()
        if key != "exact_payload"
    ):
        raise ValueError("candidate_input_future_outcome_forbidden")
    stored_candidate_hash = request.get("candidate_input_sha256")
    if request.get("candidate_input") is not None and not stored_candidate_hash:
        raise ValueError("candidate_input_sha256_missing")
    if stored_candidate_hash and str(stored_candidate_hash) != _sha256(candidate_input):
        raise ValueError("candidate_input_sha256_mismatch")
    _validate_replay_candidate_ledgers(
        candidate_input=candidate_input,
        exact_payload=exact_payload,
        request=request,
        decision_stage=str(evidence.get("decision_stage") or ""),
    )
    candidate_input[TACTICAL_EVIDENCE_SCHEMA] = deepcopy(dict(evidence))
    copied_request = deepcopy(dict(request))
    return {
        **copied_request,
        "exact_payload": deepcopy(exact_payload),
        "candidate_input": candidate_input,
        "candidate_input_sha256": _sha256(candidate_input),
        "tactical_micro_reversion_evidence_sha256": evidence.get("evidence_sha256"),
        "micro_reversion_replay_opt_in": True,
        **AUTHORITY_CONTRACT,
    }


def materialize_micro_reversion_three_arm_requests(
    *,
    replay_control_request: Mapping[str, Any],
    replay_candidate_request: Mapping[str, Any],
    evidence: Mapping[str, Any],
    ablation_design_version: str,
    source_trace: Mapping[str, Any],
    source_payload: Mapping[str, Any],
    source_market_rows: Iterable[Mapping[str, Any]],
    source_depth_rows: Iterable[Mapping[str, Any]],
    source_event_references: Iterable[Mapping[str, Any]],
    config: BridgeConfig,
    ask_depletion_sidecar: Mapping[str, Any] | None = None,
    excluded_scopes: set[tuple[str, str, str, int]] | None = None,
    verified_symbol_metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Materialize fair offline A/B/C requests without calling a provider.

    Historical callers must explicitly select the legacy exact/no-micro
    design.  Current callers use A=current micro, B=current
    micro+ask depletion, C=candidate prompt over the identical B input.  The
    only permitted B/C change is the prompt contract.  This function never
    performs a provider or broker call and never grants runtime authority.
    """

    if ablation_design_version == CURRENT_DESIGN_VERSION:
        if ask_depletion_sidecar is None:
            raise ValueError("ask_depletion_current_design_sidecar_missing")
    elif ablation_design_version == LEGACY_DESIGN_VERSION:
        if ask_depletion_sidecar is not None:
            raise ValueError("ask_depletion_legacy_design_sidecar_forbidden")
    else:
        raise ValueError("micro_reversion_ablation_design_version_invalid")

    def prompt_contract(
        request: Mapping[str, Any], *, stored_control: bool
    ) -> Mapping[str, Any]:
        value = request.get("candidate")
        if not isinstance(value, Mapping):
            raise ValueError("replay_prompt_contract_missing")
        prompt = value.get("system_prompt")
        prompt_hash = str(value.get("system_prompt_sha256") or "")
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("replay_system_prompt_missing")
        expected_prompt_hash = (
            hashlib.sha256(prompt.encode("utf-8")).hexdigest()
            if stored_control
            else _sha256(prompt)
        )
        if not prompt_hash or prompt_hash != expected_prompt_hash:
            raise ValueError("replay_system_prompt_sha256_mismatch")
        for field in ("prompt_version", "provider", "model"):
            if not str(value.get(field) or "").strip():
                raise ValueError(f"replay_prompt_contract_{field}_missing")
        if not str(value.get("transport") or "").strip():
            raise ValueError("replay_prompt_contract_transport_missing")
        if not str(value.get("schema_name") or "").strip():
            raise ValueError("replay_prompt_contract_schema_name_missing")
        if not isinstance(value.get("require_json"), bool):
            raise ValueError("replay_prompt_contract_require_json_missing")
        if not isinstance(value.get("response_schema_registry_used"), bool):
            raise ValueError("replay_prompt_contract_schema_registry_missing")
        if _nonnegative_int(value.get("max_output_tokens")) in (None, 0):
            raise ValueError("replay_prompt_contract_max_output_tokens_missing")
        response_schema = value.get("response_schema")
        response_schema_hash = str(value.get("response_schema_sha256") or "")
        response_schema_mode = str(value.get("response_schema_mode") or "")
        if isinstance(response_schema, Mapping):
            if not response_schema_hash or response_schema_hash != _sha256(
                response_schema
            ):
                raise ValueError("replay_response_schema_sha256_mismatch")
        elif response_schema_mode != "json_object":
            raise ValueError("replay_response_schema_contract_missing")
        if not str(value.get("semantic_validator_version") or "").strip():
            raise ValueError("replay_semantic_validator_version_missing")
        return value

    def base_candidate_input(request: Mapping[str, Any]) -> dict[str, Any]:
        exact_payload = request.get("exact_payload")
        if not isinstance(exact_payload, dict):
            raise ValueError("exact_payload_missing")
        candidate_input = request.get("candidate_input")
        if candidate_input is None:
            if request.get("candidate_input_sha256"):
                raise ValueError("candidate_input_absent_hash_present")
            return {"exact_payload": deepcopy(exact_payload)}
        if not isinstance(candidate_input, dict):
            raise ValueError("candidate_input_invalid")
        stored_hash = str(request.get("candidate_input_sha256") or "")
        if not stored_hash:
            raise ValueError("candidate_input_sha256_missing")
        if stored_hash != _sha256(candidate_input):
            raise ValueError("candidate_input_sha256_mismatch")
        return deepcopy(candidate_input)

    control_prompt = prompt_contract(replay_control_request, stored_control=True)
    candidate_prompt = prompt_contract(replay_candidate_request, stored_control=False)
    source_control_contract = {
        "prompt_version": source_trace.get("prompt_version"),
        "system_prompt_sha256": (
            source_trace.get("prompt_sha256") or source_payload.get("prompt_sha256")
        ),
        "provider": source_trace.get("provider_actual"),
        "model": source_trace.get("model"),
        "temperature": (
            source_trace.get("request_temperature")
            if source_trace.get("request_temperature") is not None
            else source_payload.get("temperature")
        ),
        "reasoning_effort": (
            source_trace.get("request_reasoning_effort")
            or source_payload.get("reasoning_effort")
        ),
        "transport": source_trace.get("transport"),
        "max_output_tokens": (
            source_trace.get("request_max_output_tokens")
            or source_payload.get("max_output_tokens")
        ),
        "schema_name": source_payload.get("schema_name"),
        "require_json": source_payload.get("require_json"),
        "response_schema_mode": source_trace.get("openai_response_schema_mode"),
        "response_schema_registry_used": source_trace.get(
            "openai_response_schema_registry_used"
        ),
        "semantic_validator_version": source_trace.get("semantic_validator_version"),
        "response_schema_sha256": source_trace.get("response_schema_sha256"),
    }
    source_anchor_fields = tuple(source_control_contract)
    if any(
        control_prompt.get(field) != source_control_contract.get(field)
        for field in source_anchor_fields
    ):
        raise ValueError("replay_control_source_contract_mismatch")
    source_schema_hash = str(
        source_control_contract.get("response_schema_sha256") or ""
    )
    source_schema_application = str(
        source_trace.get("response_schema_application") or ""
    )
    source_provider = str(source_control_contract.get("provider") or "").lower()
    if source_trace.get("semantic_validator_applied") is not True:
        raise ValueError("replay_control_semantic_validator_not_applied")
    if str(source_trace.get("semantic_validation_status") or "") != "pass":
        raise ValueError("replay_control_semantic_validation_not_pass")
    if source_provider == "openai":
        if source_schema_hash and source_schema_application != (
            "provider_enforced_openai"
        ):
            raise ValueError("replay_control_response_schema_not_provider_enforced")
        if (
            not source_schema_hash
            and source_control_contract.get("response_schema_mode") != "json_object"
        ):
            raise ValueError("replay_control_response_schema_hash_missing")
        if (
            not source_schema_hash
            and source_schema_application != "provider_json_object_openai"
        ):
            raise ValueError("replay_control_json_contract_not_provider_enforced")
    elif source_provider == "bedrock":
        if source_schema_application != ("local_expected_only_not_sent_to_bedrock"):
            raise ValueError("replay_control_bedrock_local_contract_missing")
    else:
        raise ValueError("replay_control_provider_contract_unsupported")
    identity_fields = (
        "paired_replay_id",
        "decision_trace_id",
        "stage",
        "endpoint",
        "stock_code",
        "effective_venue",
        "session_bucket",
        "payload_sha256",
        "request_envelope_sha256",
        "source_exact_payload_sha256",
    )
    if any(
        replay_control_request.get(field) != replay_candidate_request.get(field)
        for field in identity_fields
    ):
        raise ValueError("three_arm_request_identity_mismatch")
    if _sha256(replay_control_request.get("exact_payload")) != _sha256(
        replay_candidate_request.get("exact_payload")
    ):
        raise ValueError("three_arm_exact_payload_mismatch")
    control_input = base_candidate_input(replay_control_request)
    candidate_input = base_candidate_input(replay_candidate_request)
    if _sha256(control_input) != _sha256(candidate_input):
        raise ValueError("three_arm_base_candidate_input_mismatch")
    execution_fields = (
        "provider",
        "model",
        "temperature",
        "reasoning_effort",
        "transport",
        "max_output_tokens",
        "response_schema_mode",
        "require_json",
        "response_schema_registry_used",
    )
    if any(
        control_prompt.get(field) != candidate_prompt.get(field)
        for field in execution_fields
    ):
        raise ValueError("three_arm_execution_contract_mismatch")
    decision_contract_fields = (
        "prompt_version",
        "system_prompt_sha256",
        "schema_name",
        "response_schema_sha256",
        "semantic_validator_version",
    )
    control_decision_contract = {
        field: control_prompt.get(field) for field in decision_contract_fields
    }
    candidate_decision_contract = {
        field: candidate_prompt.get(field) for field in decision_contract_fields
    }

    base_parent_replay_id = str(
        replay_control_request.get("paired_replay_id")
        or f"micro-pair-{_sha256((evidence.get('decision_trace_id'), evidence.get('evidence_sha256')))[:24]}"
    )

    control_base = {
        **deepcopy(dict(replay_control_request)),
        "candidate_input": control_input,
        "candidate_input_sha256": _sha256(control_input),
    }
    candidate_base = {
        **deepcopy(dict(replay_candidate_request)),
        "candidate_input": candidate_input,
        "candidate_input_sha256": _sha256(candidate_input),
    }
    shared_attach = {
        "evidence": evidence,
        "source_trace": source_trace,
        "source_payload": source_payload,
        "source_market_rows": tuple(source_market_rows),
        "source_depth_rows": tuple(source_depth_rows),
        "source_event_references": tuple(source_event_references),
        "config": config,
        "excluded_scopes": excluded_scopes,
        "verified_symbol_metadata": verified_symbol_metadata,
    }
    enriched_control = attach_micro_context_to_replay_request(
        control_base, **shared_attach
    )
    enriched_candidate = attach_micro_context_to_replay_request(
        candidate_base, **shared_attach
    )
    if enriched_control.get("candidate_input_sha256") != enriched_candidate.get(
        "candidate_input_sha256"
    ):
        raise ValueError("three_arm_enriched_input_hash_mismatch")

    if ablation_design_version == CURRENT_DESIGN_VERSION:
        assert ask_depletion_sidecar is not None
        feature_view = _validated_ask_depletion_feature_view(
            ask_depletion_sidecar,
            evidence=evidence,
        )
        if ask_depletion_sidecar.get(
            "tactical_micro_reversion_evidence_sha256"
        ) != evidence.get("evidence_sha256"):
            raise ValueError("ask_depletion_tactical_evidence_binding_mismatch")

        def attach_ask_feature(request: Mapping[str, Any]) -> dict[str, Any]:
            candidate_input = deepcopy(request.get("candidate_input"))
            if not isinstance(candidate_input, dict):
                raise ValueError("ask_depletion_candidate_input_missing")
            if ASK_DEPLETION_FEATURE_VIEW_SCHEMA in candidate_input:
                raise ValueError("ask_depletion_feature_already_present")
            candidate_input[ASK_DEPLETION_FEATURE_VIEW_SCHEMA] = deepcopy(feature_view)
            return {
                **deepcopy(dict(request)),
                "candidate_input": candidate_input,
                "candidate_input_sha256": _sha256(candidate_input),
                "ask_depletion_contract_sha256": feature_view[
                    "ask_depletion_contract_sha256"
                ],
                "ask_depletion_context_sha256": feature_view[
                    "ask_depletion_context_sha256"
                ],
            }

        ask_control = attach_ask_feature(enriched_control)
        ask_candidate = attach_ask_feature(enriched_candidate)
        if ask_control.get("candidate_input_sha256") != ask_candidate.get(
            "candidate_input_sha256"
        ):
            raise ValueError("ask_depletion_prompt_pair_input_mismatch")
        if enriched_control.get("candidate_input_sha256") == ask_control.get(
            "candidate_input_sha256"
        ):
            raise ValueError("ask_depletion_feature_input_not_distinct")
        replay_ids = build_current_design_replay_ids(base_parent_replay_id)
        request_id_by_arm = dict(replay_ids.request_ids_by_arm)
        current_control = {
            **enriched_control,
            "paired_replay_parent_id": replay_ids.parent_id,
            "paired_replay_id": request_id_by_arm[CURRENT_BASE_CONTROL_ARM],
            "micro_reversion_replay_arm": CURRENT_BASE_CONTROL_ARM,
            "ablation_design_version": CURRENT_DESIGN_VERSION,
            "provider_call_performed": False,
            **ABLATION_SOURCE_ONLY_AUTHORITY,
        }
        ask_control = {
            **ask_control,
            "paired_replay_parent_id": replay_ids.parent_id,
            "paired_replay_id": request_id_by_arm[CURRENT_ASK_CONTROL_ARM],
            "micro_reversion_replay_arm": CURRENT_ASK_CONTROL_ARM,
            "ablation_design_version": CURRENT_DESIGN_VERSION,
            "provider_call_performed": False,
            **ABLATION_SOURCE_ONLY_AUTHORITY,
        }
        ask_candidate = {
            **ask_candidate,
            "paired_replay_parent_id": replay_ids.parent_id,
            "paired_replay_id": request_id_by_arm[CURRENT_ASK_CANDIDATE_ARM],
            "micro_reversion_replay_arm": CURRENT_ASK_CANDIDATE_ARM,
            "ablation_design_version": CURRENT_DESIGN_VERSION,
            "provider_call_performed": False,
            **ABLATION_SOURCE_ONLY_AUTHORITY,
        }
        result_without_hash = {
            "schema": THREE_ARM_REQUEST_SCHEMA,
            "ablation_design_version": CURRENT_DESIGN_VERSION,
            "ablation_arms": list(CURRENT_ARMS),
            "decision_trace_id": evidence.get("decision_trace_id"),
            "source_exact_payload_sha256": evidence.get("source_exact_payload_sha256"),
            "tactical_micro_reversion_evidence_sha256": evidence.get("evidence_sha256"),
            "ask_depletion_contract_sha256": feature_view[
                "ask_depletion_contract_sha256"
            ],
            "ask_depletion_context_sha256": feature_view[
                "ask_depletion_context_sha256"
            ],
            "requests": [current_control, ask_control, ask_candidate],
            "feature_effect_input_hashes_differ_only_by_ask_sidecar": True,
            "prompt_effect_ask_input_hashes_identical": True,
            "candidate_comparison_axis": "prompt_and_response_contract_only",
            "control_decision_contract_sha256": _sha256(control_decision_contract),
            "candidate_decision_contract_sha256": _sha256(candidate_decision_contract),
            "locked_execution_contract_sha256": _sha256(
                {field: control_prompt.get(field) for field in execution_fields}
            ),
            "provider_call_performed": False,
            "paired_replay_materialized": True,
            "paired_replay_ready": True,
            "decision_authority": "offline_replay_no_runtime_change",
            **AUTHORITY_CONTRACT,
            **ABLATION_SOURCE_ONLY_AUTHORITY,
        }
        return {
            **result_without_hash,
            "materialization_sha256": _sha256(result_without_hash),
        }

    exact_control = {
        **control_base,
        "paired_replay_parent_id": base_parent_replay_id,
        "paired_replay_id": f"{base_parent_replay_id}:exact-control",
        "micro_reversion_replay_arm": "replay_control_exact_no_micro",
        "provider_call_performed": False,
        **AUTHORITY_CONTRACT,
    }
    enriched_control = {
        **enriched_control,
        "paired_replay_parent_id": base_parent_replay_id,
        "paired_replay_id": f"{base_parent_replay_id}:micro-control",
        "micro_reversion_replay_arm": "replay_control_exact_plus_micro",
        "provider_call_performed": False,
    }
    enriched_candidate = {
        **enriched_candidate,
        "paired_replay_parent_id": base_parent_replay_id,
        "paired_replay_id": f"{base_parent_replay_id}:micro-candidate",
        "micro_reversion_replay_arm": "replay_candidate_exact_plus_micro",
        "provider_call_performed": False,
    }
    result_without_hash = {
        "schema": THREE_ARM_REQUEST_SCHEMA,
        "decision_trace_id": evidence.get("decision_trace_id"),
        "source_exact_payload_sha256": evidence.get("source_exact_payload_sha256"),
        "tactical_micro_reversion_evidence_sha256": evidence.get("evidence_sha256"),
        "requests": [exact_control, enriched_control, enriched_candidate],
        "micro_effect_input_hashes_differ_only_by_sidecar": True,
        "prompt_effect_enriched_input_hashes_identical": True,
        "candidate_comparison_axis": "prompt_and_response_contract_only",
        "control_decision_contract_sha256": _sha256(control_decision_contract),
        "candidate_decision_contract_sha256": _sha256(candidate_decision_contract),
        "locked_execution_contract_sha256": _sha256(
            {field: control_prompt.get(field) for field in execution_fields}
        ),
        "provider_call_performed": False,
        "paired_replay_materialized": True,
        "paired_replay_ready": True,
        **AUTHORITY_CONTRACT,
    }
    return {
        **result_without_hash,
        "materialization_sha256": _sha256(result_without_hash),
    }


def _payload_indexes(
    payloads: Sequence[Mapping[str, Any]],
) -> tuple[
    dict[str, list[Mapping[str, Any]]],
    dict[str, list[Mapping[str, Any]]],
    dict[str, list[Mapping[str, Any]]],
]:
    by_request: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    by_envelope: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    by_payload_hash: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in payloads:
        if row.get("request_id"):
            by_request[str(row.get("request_id"))].append(row)
        if row.get("request_envelope_sha256"):
            by_envelope[str(row.get("request_envelope_sha256"))].append(row)
        if row.get("payload_sha256"):
            by_payload_hash[str(row.get("payload_sha256"))].append(row)
    return by_request, by_envelope, by_payload_hash


def _consistent_payload_candidate(
    rows: Sequence[Mapping[str, Any]], *, expected_payload_sha256: str
) -> Mapping[str, Any] | None:
    matching = [
        row
        for row in rows
        if not expected_payload_sha256
        or str(row.get("payload_sha256") or "") == expected_payload_sha256
    ]
    if not matching:
        return None
    identities = {
        (
            str(row.get("payload_sha256") or ""),
            str(row.get("request_envelope_sha256") or ""),
            str(row.get("replay_context_sha256") or ""),
        )
        for row in matching
    }
    return matching[0] if len(identities) == 1 else None


def _resolve_payload_for_trace(
    trace: Mapping[str, Any],
    *,
    indexes: tuple[
        dict[str, list[Mapping[str, Any]]],
        dict[str, list[Mapping[str, Any]]],
        dict[str, list[Mapping[str, Any]]],
    ],
) -> tuple[Mapping[str, Any] | None, str]:
    by_request, by_envelope, by_payload_hash = indexes
    payload_hash = str(trace.get("payload_sha256") or "")
    request_id = str(trace.get("request_id") or "")
    if request_id:
        direct = _consistent_payload_candidate(
            by_request.get(request_id, ()), expected_payload_sha256=payload_hash
        )
        if direct is not None:
            return direct, "request_id"
    envelope_hash = str(trace.get("request_envelope_sha256") or "")
    envelope = _consistent_payload_candidate(
        by_envelope.get(envelope_hash, ()), expected_payload_sha256=payload_hash
    )
    if envelope is not None:
        return envelope, "request_envelope_sha256"
    hashed = _consistent_payload_candidate(
        by_payload_hash.get(payload_hash, ()), expected_payload_sha256=payload_hash
    )
    if hashed is not None and len(by_payload_hash.get(payload_hash, ())) == 1:
        return hashed, "unique_payload_sha256"
    return None, "missing_or_ambiguous"


class _SQLiteRelevantSourceStore:
    """Disk-backed relevant-row index used by the broad manual CLI.

    The live process never imports or instantiates this store.  It bounds peak
    RSS by keeping the 0B/0D/reference corpus on disk and materializing only one
    exact trace window at a time.
    """

    _KINDS = frozenset({"market", "depth", "reference"})

    def __init__(
        self,
        path: Path | str,
        *,
        windows: Mapping[tuple[str, str, str], tuple[tuple[int, int], ...]],
        create: bool = True,
        cache_status: str = "ephemeral",
    ) -> None:
        self.path = Path(path) if path else None
        self.cache_status = cache_status
        if create:
            self._connection = sqlite3.connect(path)
            self._connection.execute("PRAGMA journal_mode=OFF")
            self._connection.execute("PRAGMA synchronous=OFF")
            self._connection.execute("PRAGMA temp_store=FILE")
            self._connection.execute("""
                CREATE TABLE source_rows (
                    kind TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    venue TEXT NOT NULL,
                    session_bucket TEXT NOT NULL,
                    observed_us INTEGER NOT NULL,
                    source_sequence INTEGER NOT NULL,
                    payload_json TEXT NOT NULL
                )
                """)
        else:
            if self.path is None or not self.path.is_file():
                raise ValueError("relevant_source_cache_sqlite_missing")
            self._connection = sqlite3.connect(
                f"{self.path.resolve().as_uri()}?mode=ro",
                uri=True,
            )
            self._connection.execute("PRAGMA query_only=ON")
            tables = {
                str(row[0])
                for row in self._connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
            indexes = {
                str(row[0])
                for row in self._connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'index'"
                )
            }
            if "source_rows" not in tables or "source_rows_scope_time" not in indexes:
                self._connection.close()
                raise ValueError("relevant_source_cache_sqlite_schema_invalid")
        self._window_index = {
            key: (tuple(window[0] for window in scope_windows), scope_windows)
            for key, scope_windows in windows.items()
        }
        self.invalid_timestamp_counts: Counter[str] = Counter()
        self.invalid_timestamp_counts_by_scope: Counter[tuple[str, str, str, str]] = (
            Counter()
        )
        self.retained_row_counts: Counter[str] = Counter()
        self._finalized = not create
        if not create:
            self._refresh_retained_counts()

    def __enter__(self) -> _SQLiteRelevantSourceStore:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        self._connection.close()

    def _scope_and_time(
        self,
        row: Mapping[str, Any],
        *,
        reference_rows: bool,
    ) -> tuple[tuple[str, str, str], int | None]:
        key = (
            normalize_symbol(row.get("symbol")),
            normalize_venue(row.get("venue")),
            _session(row.get("session_bucket")),
        )
        if reference_rows:
            detected_at_ms = row.get("event_detected_at_ms")
            observed_us = (
                detected_at_ms * 1_000
                if isinstance(detected_at_ms, int)
                and not isinstance(detected_at_ms, bool)
                and detected_at_ms > 0
                else None
            )
        else:
            try:
                observed_us = _timestamp_us(row.get("local_receive_timestamp"))
            except (TypeError, ValueError):
                observed_us = None
        return key, observed_us

    def _is_relevant(self, key: tuple[str, str, str], observed_us: int) -> bool:
        indexed = self._window_index.get(key)
        if indexed is None:
            return False
        starts, windows = indexed
        observed_ms = observed_us // 1_000
        index = bisect_right(starts, observed_ms) - 1
        return index >= 0 and observed_ms <= windows[index][1]

    def ingest(
        self,
        kind: str,
        rows: Iterable[Mapping[str, Any]],
        *,
        reference_rows: bool = False,
    ) -> None:
        if self._finalized:
            raise RuntimeError("source store is already finalized")
        if kind not in self._KINDS:
            raise ValueError(f"unsupported source kind: {kind}")
        batch: list[tuple[str, str, str, str, int, int, str]] = []
        for row in rows:
            key, observed_us = self._scope_and_time(row, reference_rows=reference_rows)
            if key not in self._window_index:
                continue
            if observed_us is None:
                self.invalid_timestamp_counts[kind] += 1
                self.invalid_timestamp_counts_by_scope[(kind, *key)] += 1
                continue
            if not self._is_relevant(key, observed_us):
                continue
            sequence = _nonnegative_int(row.get("source_sequence")) or 0
            batch.append(
                (
                    kind,
                    key[0],
                    key[1],
                    key[2],
                    observed_us,
                    sequence,
                    json.dumps(
                        row,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                        allow_nan=True,
                        default=str,
                    ),
                )
            )
            if len(batch) >= 2_000:
                self._flush(batch)
                batch.clear()
        if batch:
            self._flush(batch)

    def _flush(self, rows: Sequence[tuple[str, str, str, str, int, int, str]]) -> None:
        self._connection.executemany(
            "INSERT INTO source_rows VALUES (?, ?, ?, ?, ?, ?, ?)", rows
        )
        self._connection.commit()
        self.retained_row_counts.update(row[0] for row in rows)

    def finalize(self) -> None:
        if self._finalized:
            return
        self._connection.execute("""
            CREATE INDEX source_rows_scope_time
            ON source_rows(
                kind, symbol, venue, session_bucket, observed_us, source_sequence
            )
            """)
        self._connection.commit()
        self._finalized = True

    def _refresh_retained_counts(self) -> None:
        self.retained_row_counts.clear()
        for kind in self._KINDS:
            total = 0
            for scope, (_, windows) in self._window_index.items():
                for start_ms, end_ms in windows:
                    row = self._connection.execute(
                        """
                        SELECT COUNT(*)
                        FROM source_rows
                        WHERE kind = ?
                          AND symbol = ?
                          AND venue = ?
                          AND session_bucket = ?
                          AND observed_us BETWEEN ? AND ?
                        """,
                        (
                            kind,
                            *scope,
                            start_ms * 1_000,
                            end_ms * 1_000 + 999,
                        ),
                    ).fetchone()
                    total += int(row[0] if row else 0)
            self.retained_row_counts[kind] = total

    def rows(
        self,
        kind: str,
        scope: tuple[str, str, str],
        *,
        start_us: int,
        end_us: int,
    ) -> list[Mapping[str, Any]]:
        if not self._finalized:
            raise RuntimeError("source store must be finalized before querying")
        if kind not in self._KINDS:
            raise ValueError(f"unsupported source kind: {kind}")
        cursor = self._connection.execute(
            """
            SELECT payload_json
            FROM source_rows
            WHERE kind = ?
              AND symbol = ?
              AND venue = ?
              AND session_bucket = ?
              AND observed_us BETWEEN ? AND ?
            ORDER BY observed_us, source_sequence
            """,
            (kind, *scope, start_us, end_us),
        )
        return [json.loads(row[0]) for row in cursor]


def _stable_file_sha256(path: Path) -> dict[str, Any]:
    """Hash one immutable raw generation and reject concurrent replacement."""

    requested = path.absolute()
    resolved = requested.resolve(strict=True)
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(resolved, flags)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise ValueError("relevant_source_generation_not_regular_file")
        digest = hashlib.sha256()
        byte_count = 0
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            byte_count += len(chunk)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    current = resolved.stat(follow_symlinks=False)
    try:
        resolved_after = requested.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ValueError("relevant_source_generation_path_changed") from exc
    stable_fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns")
    if (
        any(
            getattr(before, field) != getattr(after, field)
            or getattr(after, field) != getattr(current, field)
            for field in stable_fields
        )
        or byte_count != int(after.st_size)
        or resolved_after != resolved
    ):
        raise ValueError("relevant_source_generation_changed_during_hash")
    return {
        "path": str(resolved),
        "stored_bytes": byte_count,
        "stored_sha256": digest.hexdigest(),
    }


def _relevant_source_generation(
    *,
    target_date: str,
    market_paths: Sequence[Path],
    depth_paths: Sequence[Path],
    reference_paths: Sequence[Path],
) -> dict[str, Any]:
    sources: list[dict[str, Any]] = []
    for kind, paths in (
        ("market", market_paths),
        ("depth", depth_paths),
        ("reference", reference_paths),
    ):
        for path in sorted(paths, key=lambda value: str(value.resolve())):
            sources.append({"kind": kind, **_stable_file_sha256(path)})
    sources.sort(key=lambda row: (str(row["kind"]), str(row["path"])))
    body = {
        "schema": "micro_reversion_relevant_source_generation_v1",
        "target_date": target_date,
        "source_count": len(sources),
        "sources": sources,
    }
    return {**body, "source_generation_content_sha256": _producer_sha256(body)}


def _relevant_source_path_census(
    *,
    market_paths: Sequence[Path],
    depth_paths: Sequence[Path],
    reference_paths: Sequence[Path],
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    return tuple(
        (
            kind,
            tuple(sorted(str(path.absolute()) for path in paths)),
        )
        for kind, paths in (
            ("market", market_paths),
            ("depth", depth_paths),
            ("reference", reference_paths),
        )
    )


def _rediscover_relevant_source_paths(
    observation_root: Path, target_date: str
) -> tuple[list[Path], list[Path], list[Path]]:
    return (
        _partition_paths(observation_root, target_date, "market_stream"),
        _partition_paths(observation_root, target_date, "market_depth_stream"),
        _partition_paths(
            observation_root,
            target_date,
            "market_stream_event_references",
        ),
    )


def _assert_relevant_source_generation_unchanged(
    *,
    expected_generation: Mapping[str, Any],
    target_date: str,
    market_paths: Sequence[Path],
    depth_paths: Sequence[Path],
    reference_paths: Sequence[Path],
    observation_root: Path | None,
) -> None:
    current_paths = (market_paths, depth_paths, reference_paths)
    if observation_root is not None:
        discovered = _rediscover_relevant_source_paths(observation_root, target_date)
        if _relevant_source_path_census(
            market_paths=market_paths,
            depth_paths=depth_paths,
            reference_paths=reference_paths,
        ) != _relevant_source_path_census(
            market_paths=discovered[0],
            depth_paths=discovered[1],
            reference_paths=discovered[2],
        ):
            raise ValueError(
                "relevant_source_generation_changed_during_materialization"
            )
        current_paths = discovered
    if (
        _relevant_source_generation(
            target_date=target_date,
            market_paths=current_paths[0],
            depth_paths=current_paths[1],
            reference_paths=current_paths[2],
        )
        != expected_generation
    ):
        raise ValueError("relevant_source_generation_changed_during_materialization")


def _validate_relevant_source_generation(
    value: Mapping[str, Any], *, expected_target_date: str
) -> str:
    body = {
        key: item
        for key, item in value.items()
        if key != "source_generation_content_sha256"
    }
    sources = value.get("sources")
    if (
        value.get("schema") != "micro_reversion_relevant_source_generation_v1"
        or value.get("target_date") != expected_target_date
        or value.get("source_generation_content_sha256") != _producer_sha256(body)
        or not isinstance(sources, list)
        or value.get("source_count") != len(sources)
    ):
        raise ValueError("relevant_source_cache_generation_invalid")
    identities: set[tuple[str, str]] = set()
    previous: tuple[str, str] | None = None
    for source in sources:
        if not isinstance(source, Mapping):
            raise ValueError("relevant_source_cache_generation_invalid")
        kind = str(source.get("kind") or "")
        path = str(source.get("path") or "")
        stored_bytes = source.get("stored_bytes")
        stored_sha256 = str(source.get("stored_sha256") or "")
        identity = (kind, path)
        if (
            set(source) != {"kind", "path", "stored_bytes", "stored_sha256"}
            or kind not in _SQLiteRelevantSourceStore._KINDS
            or not Path(path).is_absolute()
            or isinstance(stored_bytes, bool)
            or not isinstance(stored_bytes, int)
            or stored_bytes < 0
            or len(stored_sha256) != 64
            or any(character not in "0123456789abcdef" for character in stored_sha256)
            or identity in identities
            or (previous is not None and identity <= previous)
        ):
            raise ValueError("relevant_source_cache_generation_invalid")
        identities.add(identity)
        previous = identity
    return str(value["source_generation_content_sha256"])


def _canonical_relevant_source_coverage(
    windows: Mapping[tuple[str, str, str], tuple[tuple[int, int], ...]],
) -> dict[str, Any]:
    rows = [
        {
            "symbol": key[0],
            "venue": key[1],
            "session_bucket": key[2],
            "start_ms": int(start_ms),
            "end_ms": int(end_ms),
        }
        for key, scope_windows in sorted(windows.items())
        for start_ms, end_ms in scope_windows
    ]
    if any(
        not row["symbol"]
        or row["venue"] == "UNKNOWN"
        or row["session_bucket"] == "UNKNOWN"
        or row["start_ms"] < 0
        or row["end_ms"] < row["start_ms"]
        for row in rows
    ):
        raise ValueError("relevant_source_cache_window_invalid")
    body = {
        "schema": "micro_reversion_relevant_source_coverage_v1",
        "window_count": len(rows),
        "windows": rows,
    }
    return {**body, "coverage_content_sha256": _producer_sha256(body)}


def _coverage_windows(
    coverage: Mapping[str, Any],
) -> dict[tuple[str, str, str], tuple[tuple[int, int], ...]]:
    body = {
        key: value
        for key, value in coverage.items()
        if key != "coverage_content_sha256"
    }
    rows = coverage.get("windows")
    if (
        coverage.get("schema") != "micro_reversion_relevant_source_coverage_v1"
        or coverage.get("coverage_content_sha256") != _producer_sha256(body)
        or not isinstance(rows, list)
        or coverage.get("window_count") != len(rows)
    ):
        raise ValueError("relevant_source_cache_coverage_invalid")
    grouped: dict[tuple[str, str, str], list[tuple[int, int]]] = defaultdict(list)
    previous: tuple[str, str, str, int, int] | None = None
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError("relevant_source_cache_coverage_invalid")
        key = (
            str(row.get("symbol") or ""),
            str(row.get("venue") or ""),
            str(row.get("session_bucket") or ""),
        )
        start_ms = row.get("start_ms")
        end_ms = row.get("end_ms")
        current = (*key, start_ms, end_ms)
        if (
            not all(key)
            or "UNKNOWN" in key[1:]
            or isinstance(start_ms, bool)
            or not isinstance(start_ms, int)
            or isinstance(end_ms, bool)
            or not isinstance(end_ms, int)
            or start_ms < 0
            or end_ms < start_ms
            or (previous is not None and current <= previous)
        ):
            raise ValueError("relevant_source_cache_coverage_invalid")
        grouped[key].append((start_ms, end_ms))
        previous = current
    for scope_windows in grouped.values():
        if any(
            next_start <= current_end
            for (_, current_end), (next_start, _) in zip(
                scope_windows, scope_windows[1:]
            )
        ):
            raise ValueError("relevant_source_cache_coverage_invalid")
    return {key: tuple(value) for key, value in grouped.items()}


def _coverage_contains(
    stored: Mapping[tuple[str, str, str], tuple[tuple[int, int], ...]],
    requested: Mapping[tuple[str, str, str], tuple[tuple[int, int], ...]],
) -> bool:
    for key, requested_windows in requested.items():
        stored_windows = stored.get(key, ())
        if any(
            not any(
                stored_start <= requested_start and requested_end <= stored_end
                for stored_start, stored_end in stored_windows
            )
            for requested_start, requested_end in requested_windows
        ):
            return False
    return True


def _cache_metadata_content(value: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: item for key, item in value.items() if key != "metadata_content_sha256"
    }


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                return digest.hexdigest()
            digest.update(chunk)


def _load_relevant_source_cache_metadata(
    cache_dir: Path,
    *,
    target_date: str,
    config_sha256: str,
    source_generation_sha256: str,
    requested_windows: Mapping[tuple[str, str, str], tuple[tuple[int, int], ...]],
) -> dict[str, Any]:
    metadata_path = cache_dir / "metadata.json"
    sqlite_path = cache_dir / "source.sqlite3"
    metadata = read_json_object_strict(metadata_path)
    content = _cache_metadata_content(metadata)
    coverage = metadata.get("coverage")
    source_generation = metadata.get("source_generation")
    validated_source_generation_sha256 = _validate_relevant_source_generation(
        source_generation if isinstance(source_generation, Mapping) else {},
        expected_target_date=target_date,
    )
    stored_windows = _coverage_windows(
        coverage if isinstance(coverage, Mapping) else {}
    )
    if (
        metadata.get("schema") != RELEVANT_SOURCE_CACHE_SCHEMA
        or metadata.get("index_version") != RELEVANT_SOURCE_CACHE_INDEX_VERSION
        or metadata.get("complete") is not True
        or metadata.get("target_date") != target_date
        or metadata.get("bridge_config_sha256") != config_sha256
        or metadata.get("source_generation_content_sha256") != source_generation_sha256
        or validated_source_generation_sha256 != source_generation_sha256
        or metadata.get("metadata_content_sha256") != _producer_sha256(content)
        or not _coverage_contains(stored_windows, requested_windows)
        or not sqlite_path.is_file()
        or metadata.get("sqlite_bytes") != sqlite_path.stat().st_size
        or metadata.get("sqlite_sha256") != _sha256_file(sqlite_path)
    ):
        raise ValueError("relevant_source_cache_contract_invalid")
    with sqlite3.connect(
        f"{sqlite_path.resolve().as_uri()}?mode=ro", uri=True
    ) as connection:
        row = connection.execute("PRAGMA integrity_check").fetchone()
    if row != ("ok",):
        raise ValueError("relevant_source_cache_integrity_invalid")
    return metadata


@contextmanager
def _relevant_source_cache_lock(cache_root: Path) -> Iterator[None]:
    cache_root.mkdir(parents=True, exist_ok=True)
    lock_path = cache_root / ".cache.lock"
    with lock_path.open("a+b") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _remove_cache_only_tree(path: Path, *, cache_root: Path) -> None:
    resolved_root = cache_root.resolve()
    resolved = path.resolve()
    if resolved.parent == resolved_root or resolved_root in resolved.parents:
        shutil.rmtree(resolved)
        return
    raise ValueError("relevant_source_cache_cleanup_scope_invalid")


def _cleanup_relevant_source_cache(
    cache_root: Path,
    *,
    keep_completed: int = DEFAULT_RELEVANT_SOURCE_CACHE_KEEP,
    partial_max_age_sec: int = DEFAULT_RELEVANT_SOURCE_CACHE_PARTIAL_MAX_AGE_SEC,
    now_timestamp: float | None = None,
    protected_paths: set[Path] | None = None,
) -> dict[str, int]:
    if keep_completed < 1 or partial_max_age_sec < 0:
        raise ValueError("relevant_source_cache_retention_invalid")
    if not cache_root.exists():
        return {"partial_removed": 0, "completed_removed": 0}
    now = datetime.now().timestamp() if now_timestamp is None else now_timestamp
    partial_removed = 0
    for path in sorted(cache_root.rglob(".partial-*")):
        if path.is_dir() and now - path.stat().st_mtime >= partial_max_age_sec:
            _remove_cache_only_tree(path, cache_root=cache_root)
            partial_removed += 1
    completed: list[tuple[float, Path]] = []
    for path in sorted(cache_root.glob("????-??-??/cache-*")):
        if not path.is_dir():
            continue
        metadata_path = path / "metadata.json"
        try:
            metadata = read_json_object_strict(metadata_path)
            created = datetime.fromisoformat(
                str(metadata.get("created_at") or "")
            ).timestamp()
        except (EOFError, OSError, TypeError, ValueError):
            created = path.stat().st_mtime
        completed.append((created, path))
    completed_removed = 0
    protected = {path.resolve() for path in (protected_paths or set())}
    retained = set(protected)
    for _, path in sorted(completed, reverse=True):
        if len(retained) >= keep_completed:
            break
        retained.add(path.resolve())
    for _, path in sorted(completed, reverse=True):
        if path.resolve() in retained:
            continue
        _remove_cache_only_tree(path, cache_root=cache_root)
        completed_removed += 1
    return {
        "partial_removed": partial_removed,
        "completed_removed": completed_removed,
    }


def _apply_cache_metadata_diagnostics(
    store: _SQLiteRelevantSourceStore,
    metadata: Mapping[str, Any],
    *,
    requested_windows: Mapping[tuple[str, str, str], tuple[tuple[int, int], ...]],
) -> None:
    requested_scopes = set(requested_windows)
    counts: Counter[str] = Counter()
    rows = metadata.get("invalid_timestamp_counts_by_scope")
    if not isinstance(rows, list):
        raise ValueError("relevant_source_cache_invalid_timestamp_census_invalid")
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError("relevant_source_cache_invalid_timestamp_census_invalid")
        scope = (
            str(row.get("symbol") or ""),
            str(row.get("venue") or ""),
            str(row.get("session_bucket") or ""),
        )
        kind = str(row.get("kind") or "")
        count = row.get("count")
        if (
            kind not in store._KINDS
            or not all(scope)
            or isinstance(count, bool)
            or not isinstance(count, int)
            or count < 0
        ):
            raise ValueError("relevant_source_cache_invalid_timestamp_census_invalid")
        if scope in requested_scopes:
            counts[kind] += count
    store.invalid_timestamp_counts = counts


@contextmanager
def open_relevant_source_store(
    *,
    target_date: str,
    windows: Mapping[tuple[str, str, str], tuple[tuple[int, int], ...]],
    config: BridgeConfig,
    market_paths: Sequence[Path],
    depth_paths: Sequence[Path],
    reference_paths: Sequence[Path],
    persistent_cache: bool,
    observation_root: Path | None = None,
    cache_root: Path = DEFAULT_RELEVANT_SOURCE_CACHE_ROOT,
    keep_completed: int = DEFAULT_RELEVANT_SOURCE_CACHE_KEEP,
) -> Iterator[_SQLiteRelevantSourceStore]:
    """Open a validated reusable source index or build one from exact raw rows."""

    if observation_root is not None:
        discovered = _rediscover_relevant_source_paths(observation_root, target_date)
        if _relevant_source_path_census(
            market_paths=market_paths,
            depth_paths=depth_paths,
            reference_paths=reference_paths,
        ) != _relevant_source_path_census(
            market_paths=discovered[0],
            depth_paths=discovered[1],
            reference_paths=discovered[2],
        ):
            raise ValueError("relevant_source_generation_path_census_changed")
    source_generation = _relevant_source_generation(
        target_date=target_date,
        market_paths=market_paths,
        depth_paths=depth_paths,
        reference_paths=reference_paths,
    )
    if not persistent_cache:
        with _SQLiteRelevantSourceStore("", windows=windows) as source_store:
            source_store.ingest("market", _iter_jsonl(market_paths))
            source_store.ingest("depth", _iter_jsonl(depth_paths))
            source_store.ingest(
                "reference",
                _iter_jsonl(reference_paths),
                reference_rows=True,
            )
            source_store.finalize()
            try:
                yield source_store
            except BaseException:
                raise
            else:
                _assert_relevant_source_generation_unchanged(
                    expected_generation=source_generation,
                    target_date=target_date,
                    market_paths=market_paths,
                    depth_paths=depth_paths,
                    reference_paths=reference_paths,
                    observation_root=observation_root,
                )
        return

    source_generation_sha256 = str(
        source_generation["source_generation_content_sha256"]
    )
    config_sha256 = str(_bridge_config_contract(config)["config_sha256"])
    requested_coverage = _canonical_relevant_source_coverage(windows)
    base_key = _producer_sha256(
        {
            "index_version": RELEVANT_SOURCE_CACHE_INDEX_VERSION,
            "target_date": target_date,
            "bridge_config_sha256": config_sha256,
            "source_generation_content_sha256": source_generation_sha256,
        }
    )
    target_root = cache_root / target_date
    selected_dir: Path | None = None
    selected_metadata: dict[str, Any] | None = None
    cache_status = "cache_reused"
    with _relevant_source_cache_lock(cache_root):
        target_root.mkdir(parents=True, exist_ok=True)
        for candidate in sorted(target_root.glob(f"cache-{base_key}-*")):
            try:
                candidate_metadata = _load_relevant_source_cache_metadata(
                    candidate,
                    target_date=target_date,
                    config_sha256=config_sha256,
                    source_generation_sha256=source_generation_sha256,
                    requested_windows=windows,
                )
            except (EOFError, OSError, sqlite3.DatabaseError, TypeError, ValueError):
                _remove_cache_only_tree(candidate, cache_root=cache_root)
                continue
            selected_dir = candidate
            selected_metadata = candidate_metadata
            break
        if selected_dir is None:
            cache_status = "cache_built"
            staging = Path(tempfile.mkdtemp(prefix=".partial-", dir=str(target_root)))
            sqlite_path = staging / "source.sqlite3"
            try:
                with _SQLiteRelevantSourceStore(
                    sqlite_path,
                    windows=windows,
                    cache_status="cache_building",
                ) as building_store:
                    building_store.ingest("market", _iter_jsonl(market_paths))
                    building_store.ingest("depth", _iter_jsonl(depth_paths))
                    building_store.ingest(
                        "reference",
                        _iter_jsonl(reference_paths),
                        reference_rows=True,
                    )
                    building_store.finalize()
                    invalid_timestamp_counts_by_scope = [
                        {
                            "kind": key[0],
                            "symbol": key[1],
                            "venue": key[2],
                            "session_bucket": key[3],
                            "count": count,
                        }
                        for key, count in sorted(
                            building_store.invalid_timestamp_counts_by_scope.items()
                        )
                    ]
                    retained_row_counts = dict(building_store.retained_row_counts)
                if (
                    _relevant_source_generation(
                        target_date=target_date,
                        market_paths=market_paths,
                        depth_paths=depth_paths,
                        reference_paths=reference_paths,
                    )
                    != source_generation
                ):
                    raise ValueError("relevant_source_generation_changed_during_ingest")
                metadata_body = {
                    "schema": RELEVANT_SOURCE_CACHE_SCHEMA,
                    "index_version": RELEVANT_SOURCE_CACHE_INDEX_VERSION,
                    "complete": True,
                    "target_date": target_date,
                    "created_at": datetime.now().astimezone().isoformat(),
                    "bridge_config_sha256": config_sha256,
                    "source_generation": source_generation,
                    "source_generation_content_sha256": (source_generation_sha256),
                    "coverage": requested_coverage,
                    "sqlite_bytes": sqlite_path.stat().st_size,
                    "sqlite_sha256": _sha256_file(sqlite_path),
                    "retained_row_counts": retained_row_counts,
                    "invalid_timestamp_counts_by_scope": (
                        invalid_timestamp_counts_by_scope
                    ),
                    "cache_only_rebuildable": True,
                    "provider_call_performed": False,
                    "runtime_effect": False,
                    "actual_order_submitted": False,
                }
                selected_metadata = {
                    **metadata_body,
                    "metadata_content_sha256": _producer_sha256(metadata_body),
                }
                _atomic_write_json(staging / "metadata.json", selected_metadata)
                coverage_sha = str(requested_coverage["coverage_content_sha256"])
                selected_dir = target_root / f"cache-{base_key}-{coverage_sha}"
                if selected_dir.exists():
                    _remove_cache_only_tree(selected_dir, cache_root=cache_root)
                os.replace(staging, selected_dir)
            except BaseException:
                if staging.exists():
                    _remove_cache_only_tree(staging, cache_root=cache_root)
                raise
        _cleanup_relevant_source_cache(
            cache_root,
            keep_completed=keep_completed,
            protected_paths={selected_dir},
        )
        assert selected_dir is not None and selected_metadata is not None
        source_store = _SQLiteRelevantSourceStore(
            selected_dir / "source.sqlite3",
            windows=windows,
            create=False,
            cache_status=cache_status,
        )
        _apply_cache_metadata_diagnostics(
            source_store,
            selected_metadata,
            requested_windows=windows,
        )
        source_store.cache_diagnostics = {
            "cache_status": "validated_complete",
            "source_generation_content_sha256": source_generation_sha256,
            "requested_coverage_content_sha256": requested_coverage[
                "coverage_content_sha256"
            ],
            "requested_windows_covered": True,
            "cache_only_rebuildable": True,
        }
    try:
        yield source_store
    except BaseException:
        raise
    else:
        _assert_relevant_source_generation_unchanged(
            expected_generation=source_generation,
            target_date=target_date,
            market_paths=market_paths,
            depth_paths=depth_paths,
            reference_paths=reference_paths,
            observation_root=observation_root,
        )
    finally:
        source_store.close()


def build_bridge_report(
    *,
    target_date: str,
    traces: Iterable[Mapping[str, Any]],
    payloads: Iterable[Mapping[str, Any]],
    market_rows: Iterable[Mapping[str, Any]],
    depth_rows: Iterable[Mapping[str, Any]],
    event_references: Iterable[Mapping[str, Any]],
    config: BridgeConfig | None = None,
    excluded_scopes: set[tuple[str, str, str, int]] | None = None,
    generated_at: datetime | None = None,
    source_store: _SQLiteRelevantSourceStore | None = None,
    entry_pipeline_rows: Iterable[Mapping[str, Any]] = (),
    entry_pipeline_source: Mapping[str, Any] | None = None,
    verified_symbol_metadata_by_trace: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    date_value = date.fromisoformat(target_date)
    if date_value < CLEAN_BASELINE_DATE:
        raise ValueError("target date is before clean tuning baseline")
    selected_config = config or BridgeConfig()
    trace_rows = [row for row in traces if isinstance(row, Mapping)]
    payload_rows = [row for row in payloads if isinstance(row, Mapping)]
    relevant_pipeline_keys = {
        (
            str(trace.get("decision_trace_id") or "").strip(),
            normalize_symbol(trace.get("stock_code")),
        )
        for trace in trace_rows
        if str(trace.get("decision_trace_id") or "").strip()
        and normalize_symbol(trace.get("stock_code"))
    }
    pipeline_census = Counter()
    pipeline_rows_by_trace_symbol: dict[tuple[str, str], list[Mapping[str, Any]]] = (
        defaultdict(list)
    )
    for pipeline_row in entry_pipeline_rows:
        if not isinstance(pipeline_row, Mapping):
            continue
        pipeline_census["json_object_row_count"] += 1
        if pipeline_row.get("pipeline") != "ENTRY_PIPELINE":
            continue
        pipeline_census["entry_pipeline_row_count"] += 1
        pipeline_fields = pipeline_row.get("fields")
        if not isinstance(pipeline_fields, Mapping):
            continue
        pipeline_key = (
            str(pipeline_fields.get("ai_decision_trace_id") or "").strip(),
            normalize_symbol(pipeline_row.get("stock_code")),
        )
        if pipeline_key[0] and pipeline_key[1]:
            if (
                str(pipeline_fields.get("formula_version") or "").strip()
                and (_nonnegative_int(pipeline_fields.get("effective_qty")) or 0) > 0
            ):
                pipeline_census["allocator_contract_row_count"] += 1
            if pipeline_key not in relevant_pipeline_keys:
                continue
            pipeline_census["trace_symbol_linked_row_count"] += 1
            pipeline_rows_by_trace_symbol[pipeline_key].append(pipeline_row)
    pipeline_source = dict(entry_pipeline_source or {})
    pipeline_source_status = str(
        pipeline_source.get("status")
        or (
            "programmatic_rows_source_unspecified"
            if pipeline_census["json_object_row_count"]
            else "not_supplied_observation_only"
        )
    )
    if pipeline_source_status not in {
        "available_hash_verified",
        "missing_observation_only",
        "programmatic_rows_source_unspecified",
        "not_supplied_observation_only",
    }:
        raise ValueError("entry_pipeline_source_status_invalid")
    pipeline_source_sha256 = str(pipeline_source.get("source_sha256") or "")
    if pipeline_source_status == "available_hash_verified" and (
        len(pipeline_source_sha256) != 64
        or any(
            character not in "0123456789abcdef" for character in pipeline_source_sha256
        )
    ):
        raise ValueError("entry_pipeline_source_sha256_invalid")
    if pipeline_source_status != "available_hash_verified" and pipeline_source_sha256:
        raise ValueError("entry_pipeline_unavailable_source_has_sha256")
    extended_source_fields = {
        "logical_source_path",
        "source_compression",
        "source_bytes",
        "source_content_sha256",
        "source_content_bytes",
        "source_line_count",
        "source_nonempty_line_count",
        "source_json_object_row_count",
        "source_snapshot_stable",
    }
    has_extended_source_provenance = any(
        field in pipeline_source for field in extended_source_fields
    )
    if pipeline_source_status == "available_hash_verified" and (
        has_extended_source_provenance
    ):
        missing_source_fields = sorted(
            field for field in extended_source_fields if field not in pipeline_source
        )
        if missing_source_fields:
            raise ValueError(
                "entry_pipeline_extended_source_provenance_incomplete:"
                + ",".join(missing_source_fields)
            )
        source_content_sha256 = str(pipeline_source.get("source_content_sha256") or "")
        if len(source_content_sha256) != 64 or any(
            character not in "0123456789abcdef" for character in source_content_sha256
        ):
            raise ValueError("entry_pipeline_source_content_sha256_invalid")
        source_compression = str(pipeline_source.get("source_compression") or "")
        if source_compression not in {"plain", "gzip"}:
            raise ValueError("entry_pipeline_source_compression_invalid")
        logical_source_path = str(
            pipeline_source.get("logical_source_path") or ""
        ).strip()
        resolved_source_path = str(pipeline_source.get("source_path") or "").strip()
        if not logical_source_path or not resolved_source_path:
            raise ValueError("entry_pipeline_source_path_invalid")
        if (source_compression == "gzip") != resolved_source_path.endswith(".gz"):
            raise ValueError("entry_pipeline_source_compression_path_mismatch")
        if pipeline_source.get("source_snapshot_stable") is not True:
            raise ValueError("entry_pipeline_source_snapshot_unstable")
        count_fields = (
            "source_bytes",
            "source_content_bytes",
            "source_line_count",
            "source_nonempty_line_count",
            "source_json_object_row_count",
        )
        for field in count_fields:
            value = pipeline_source.get(field)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"entry_pipeline_{field}_invalid")
        if (
            pipeline_source["source_line_count"]
            < pipeline_source["source_nonempty_line_count"]
            or pipeline_source["source_nonempty_line_count"]
            < pipeline_source["source_json_object_row_count"]
        ):
            raise ValueError("entry_pipeline_source_census_order_invalid")
        if (
            pipeline_source["source_json_object_row_count"]
            != pipeline_census["json_object_row_count"]
        ):
            raise ValueError("entry_pipeline_source_census_mismatch")
    elif pipeline_source_status != "available_hash_verified" and any(
        field in pipeline_source
        for field in (
            "source_content_sha256",
            "source_content_bytes",
            "source_line_count",
            "source_nonempty_line_count",
            "source_json_object_row_count",
            "source_snapshot_stable",
        )
    ):
        raise ValueError("entry_pipeline_unavailable_source_has_content_provenance")
    verified_pipeline_rows_by_trace_symbol = (
        pipeline_rows_by_trace_symbol
        if pipeline_source_status == "available_hash_verified"
        else {}
    )
    pipeline_source_contract = {
        "status": pipeline_source_status,
        "logical_source_path": (
            str(pipeline_source.get("logical_source_path") or "") or None
        ),
        "source_path": str(pipeline_source.get("source_path") or "") or None,
        "source_compression": (
            str(pipeline_source.get("source_compression") or "") or None
        ),
        "source_bytes": pipeline_source.get("source_bytes"),
        "source_sha256": pipeline_source_sha256 or None,
        "hash_basis": (
            "raw_file_bytes_sha256"
            if pipeline_source_status == "available_hash_verified"
            else None
        ),
        "source_content_sha256": (
            str(pipeline_source.get("source_content_sha256") or "") or None
        ),
        "source_content_hash_basis": (
            "decoded_jsonl_bytes_sha256"
            if pipeline_source_status == "available_hash_verified"
            and pipeline_source.get("source_content_sha256")
            else None
        ),
        "source_content_bytes": pipeline_source.get("source_content_bytes"),
        "source_line_count": pipeline_source.get("source_line_count"),
        "source_nonempty_line_count": pipeline_source.get("source_nonempty_line_count"),
        "source_json_object_row_count": pipeline_source.get(
            "source_json_object_row_count"
        ),
        "source_snapshot_stable": pipeline_source.get("source_snapshot_stable"),
        "json_object_row_count": pipeline_census["json_object_row_count"],
        "entry_pipeline_row_count": pipeline_census["entry_pipeline_row_count"],
        "allocator_contract_row_count": pipeline_census["allocator_contract_row_count"],
        "trace_symbol_linked_row_count": pipeline_census[
            "trace_symbol_linked_row_count"
        ],
        "outcome_join_mode": (
            "exact_broker_submission_quantity_reconciliation"
            if verified_pipeline_rows_by_trace_symbol
            else "standardized_one_share_observation_only"
        ),
        "provider_visible": False,
        "runtime_effect": False,
        "actual_order_submitted": False,
    }
    market = (
        []
        if source_store is not None
        else [row for row in market_rows if isinstance(row, Mapping)]
    )
    depth = (
        []
        if source_store is not None
        else [row for row in depth_rows if isinstance(row, Mapping)]
    )
    references = (
        []
        if source_store is not None
        else [row for row in event_references if isinstance(row, Mapping)]
    )
    payload_indexes = _payload_indexes(payload_rows)
    market_by_scope: dict[tuple[str, str, str], list[Mapping[str, Any]]] = defaultdict(
        list
    )
    for row in market:
        market_by_scope[
            (
                normalize_symbol(row.get("symbol")),
                normalize_venue(row.get("venue")),
                _session(row.get("session_bucket")),
            )
        ].append(row)
    depth_by_scope: dict[tuple[str, str, str], list[Mapping[str, Any]]] = defaultdict(
        list
    )
    for row in depth:
        depth_by_scope[
            (
                normalize_symbol(row.get("symbol")),
                normalize_venue(row.get("venue")),
                _session(row.get("session_bucket")),
            )
        ].append(row)
    references_by_scope: dict[tuple[str, str, str], list[Mapping[str, Any]]] = (
        defaultdict(list)
    )
    for row in references:
        references_by_scope[
            (
                normalize_symbol(row.get("symbol")),
                normalize_venue(row.get("venue")),
                _session(row.get("session_bucket")),
            )
        ].append(row)

    def safe_receive_us(row: Mapping[str, Any]) -> int | None:
        try:
            return _timestamp_us(row.get("local_receive_timestamp"))
        except (TypeError, ValueError):
            return None

    def safe_reference_ms(row: Mapping[str, Any]) -> int | None:
        value = row.get("event_detected_at_ms")
        return (
            value
            if isinstance(value, int) and not isinstance(value, bool) and value > 0
            else None
        )

    invalid_market_by_scope: dict[
        tuple[str, str, str], tuple[Mapping[str, Any], ...]
    ] = {}
    market_times_by_scope: dict[tuple[str, str, str], tuple[int, ...]] = {}
    for key, scoped_rows in market_by_scope.items():
        invalid_market_by_scope[key] = tuple(
            row for row in scoped_rows if safe_receive_us(row) is None
        )
        scoped_rows[:] = [
            row for row in scoped_rows if safe_receive_us(row) is not None
        ]
        scoped_rows.sort(
            key=lambda row: (
                int(safe_receive_us(row) or 0),
                _nonnegative_int(row.get("source_sequence")) or 0,
            )
        )
        market_times_by_scope[key] = tuple(
            int(safe_receive_us(row) or 0) for row in scoped_rows
        )
    invalid_depth_by_scope: dict[
        tuple[str, str, str], tuple[Mapping[str, Any], ...]
    ] = {}
    depth_times_by_scope: dict[tuple[str, str, str], tuple[int, ...]] = {}
    for key, scoped_rows in depth_by_scope.items():
        invalid_depth_by_scope[key] = tuple(
            row for row in scoped_rows if safe_receive_us(row) is None
        )
        scoped_rows[:] = [
            row for row in scoped_rows if safe_receive_us(row) is not None
        ]
        scoped_rows.sort(
            key=lambda row: (
                int(safe_receive_us(row) or 0),
                _nonnegative_int(row.get("source_sequence")) or 0,
            )
        )
        depth_times_by_scope[key] = tuple(
            int(safe_receive_us(row) or 0) for row in scoped_rows
        )
    invalid_references_by_scope: dict[
        tuple[str, str, str], tuple[Mapping[str, Any], ...]
    ] = {}
    reference_times_by_scope: dict[tuple[str, str, str], tuple[int, ...]] = {}
    for key, scoped_rows in references_by_scope.items():
        invalid_references_by_scope[key] = tuple(
            row for row in scoped_rows if safe_reference_ms(row) is None
        )
        scoped_rows[:] = [
            row for row in scoped_rows if safe_reference_ms(row) is not None
        ]
        scoped_rows.sort(key=lambda row: int(safe_reference_ms(row) or 0))
        reference_times_by_scope[key] = tuple(
            int(safe_reference_ms(row) or 0) * 1_000 for row in scoped_rows
        )

    def bounded_rows(
        scoped_rows: Sequence[Mapping[str, Any]],
        times: Sequence[int],
        *,
        start_us: int,
        end_us: int,
    ) -> Sequence[Mapping[str, Any]]:
        left = bisect_left(times, start_us)
        right = bisect_right(times, end_us)
        return scoped_rows[left:right]

    rows = []
    outcome_source_pool_rows: dict[str, dict[str, dict[str, Any]]] = {
        "market": {},
        "depth": {},
        "entry_pipeline": {},
    }
    canonical_entry_pipeline_hashes: set[str] = set()
    exclusions = Counter()
    processed_scope_keys: set[tuple[str, str, str]] = set()
    for trace in trace_rows:
        payload, payload_join_mode = _resolve_payload_for_trace(
            trace, indexes=payload_indexes
        )
        if payload is None:
            exclusions["payload_join_missing_or_ambiguous"] += 1
            continue
        resolved_scope = resolve_micro_scope(trace)
        scope_key = (
            normalize_symbol(trace.get("stock_code")),
            resolved_scope.venue,
            resolved_scope.session_bucket,
        )
        processed_scope_keys.add(scope_key)
        watermark, _ = exact_snapshot_watermark(trace, payload)
        watermark_us = int((watermark or {}).get("captured_at_us") or 0)
        context_start_us = max(
            0,
            watermark_us
            - (
                selected_config.active_wave_max_age_sec
                + selected_config.context_lookback_sec
            )
            * 1_000_000,
        )
        outcome_end_us = (
            watermark_us
            + (
                _post_snapshot_source_horizon_sec(selected_config) * 1_000
                + selected_config.max_outcome_endpoint_lag_ms
            )
            * 1_000
        )
        if source_store is not None:
            trace_market_rows = source_store.rows(
                "market",
                scope_key,
                start_us=context_start_us,
                end_us=outcome_end_us,
            )
            trace_depth_rows = source_store.rows(
                "depth",
                scope_key,
                start_us=context_start_us,
                end_us=outcome_end_us,
            )
            trace_references = source_store.rows(
                "reference",
                scope_key,
                start_us=context_start_us,
                end_us=watermark_us,
            )
        else:
            scoped_market = market_by_scope.get(scope_key, ())
            scoped_depth = depth_by_scope.get(scope_key, ())
            scoped_references = references_by_scope.get(scope_key, ())
            trace_market_rows = list(
                bounded_rows(
                    scoped_market,
                    market_times_by_scope.get(scope_key, ()),
                    start_us=context_start_us,
                    end_us=outcome_end_us,
                )
            )
            trace_depth_rows = list(
                bounded_rows(
                    scoped_depth,
                    depth_times_by_scope.get(scope_key, ()),
                    start_us=context_start_us,
                    end_us=outcome_end_us,
                )
            )
            trace_references = list(
                bounded_rows(
                    scoped_references,
                    reference_times_by_scope.get(scope_key, ()),
                    start_us=context_start_us,
                    end_us=watermark_us,
                )
            )
        canonical_source = _canonical_tactical_source_rows(
            target_date=target_date,
            trace=trace,
            payload=payload,
            market_rows=trace_market_rows,
            depth_rows=trace_depth_rows,
            event_references=trace_references,
            config=selected_config,
        )
        trace_market_rows = canonical_source["market_rows"]
        trace_depth_rows = canonical_source["depth_rows"]
        trace_references = canonical_source["event_reference_rows"]
        evidence_market_rows = [
            row
            for row in trace_market_rows
            if _timestamp_us(row.get("local_receive_timestamp")) <= watermark_us
        ]
        evidence_depth_rows = [
            row
            for row in trace_depth_rows
            if _timestamp_us(row.get("local_receive_timestamp")) <= watermark_us
        ]
        evidence = build_tactical_evidence(
            trace=trace,
            payload=payload,
            market_rows=evidence_market_rows,
            depth_rows=evidence_depth_rows,
            event_references=trace_references,
            config=selected_config,
            excluded_scopes=excluded_scopes,
            verified_symbol_metadata=(verified_symbol_metadata_by_trace or {}).get(
                str(trace.get("decision_trace_id") or "").strip()
            ),
        )
        ask_depletion_sidecar: dict[str, Any] | None = None
        ask_depletion_sidecar_status = "not_eligible"
        try:
            candidate_sidecar = build_ask_depletion_feature_sidecar(
                evidence=evidence,
                market_rows=evidence_market_rows,
                depth_rows=evidence_depth_rows,
                max_depth_age_ms=selected_config.max_depth_age_ms,
            )
            _validated_ask_depletion_feature_view(
                candidate_sidecar,
                evidence=evidence,
            )
        except (TypeError, ValueError) as exc:
            ask_depletion_sidecar_status = str(exc).split(":", 1)[0]
        else:
            ask_depletion_sidecar = candidate_sidecar
            ask_depletion_sidecar_status = "eligible_source_only_feature_ablation"
        state = str(evidence.get("state") or "source_unavailable")
        wave_id = str((evidence.get("event") or {}).get("parent_wave_id") or "")
        wave_key = (
            normalize_symbol(evidence.get("stock_code")),
            str(evidence.get("micro_venue") or ""),
            str(evidence.get("micro_session_bucket") or ""),
            str(trace.get("decision_stage") or ""),
            wave_id,
        )
        trace_entry_pipeline_rows = verified_pipeline_rows_by_trace_symbol.get(
            (
                str(trace.get("decision_trace_id") or "").strip(),
                normalize_symbol(trace.get("stock_code")),
            ),
            (),
        )
        canonical_outcome_source = _canonical_future_outcome_source_rows(
            evidence=evidence,
            market_rows=trace_market_rows,
            depth_rows=trace_depth_rows,
            entry_pipeline_rows=trace_entry_pipeline_rows,
            config=selected_config,
        )
        canonical_entry_pipeline_hashes.update(
            _sha256(row) for row in canonical_outcome_source["entry_pipeline"]
        )
        rebuilt_evidence = build_tactical_evidence(
            trace=trace,
            payload=payload,
            market_rows=evidence_market_rows,
            depth_rows=evidence_depth_rows,
            event_references=trace_references,
            config=selected_config,
            excluded_scopes=excluded_scopes,
            verified_symbol_metadata=(verified_symbol_metadata_by_trace or {}).get(
                str(trace.get("decision_trace_id") or "").strip()
            ),
        )
        if rebuilt_evidence != evidence:
            raise ValueError("tactical_evidence_canonical_rebuild_mismatch")
        if ask_depletion_sidecar is not None:
            rebuilt_sidecar = build_ask_depletion_feature_sidecar(
                evidence=evidence,
                market_rows=evidence_market_rows,
                depth_rows=evidence_depth_rows,
                max_depth_age_ms=selected_config.max_depth_age_ms,
            )
            if rebuilt_sidecar != ask_depletion_sidecar:
                raise ValueError("ask_depletion_canonical_rebuild_mismatch")
        outcome = build_future_outcome(
            evidence=evidence,
            market_rows=canonical_outcome_source["market"],
            depth_rows=canonical_outcome_source["depth"],
            entry_pipeline_rows=canonical_outcome_source["entry_pipeline"],
            control_action=str(trace.get("action") or ""),
            config=selected_config,
        )
        outcome_rebuild_source = build_future_outcome_rebuild_source(
            evidence=evidence,
            market_rows=canonical_outcome_source["market"],
            depth_rows=canonical_outcome_source["depth"],
            entry_pipeline_rows=canonical_outcome_source["entry_pipeline"],
            control_action=str(trace.get("action") or ""),
            config=selected_config,
            source_pool_rows=outcome_source_pool_rows,
        )
        row = {
            "decision_trace_id": trace.get("decision_trace_id"),
            "decision_stage": trace.get("decision_stage"),
            "provider_actual": trace.get("provider_actual"),
            "prompt_version": trace.get("prompt_version"),
            "payload_join_mode": payload_join_mode,
            "_parent_wave_stage_key": wave_key if wave_id else None,
            "primary_parent_wave_stage_row": False,
            "primary_replay_parent_wave_stage_row": False,
            "primary_control_parent_wave_stage_row": False,
            "primary_paired_parent_wave_stage_row": False,
            "primary_economic_parent_wave_stage_row": False,
            "primary_mature_outcome_parent_wave_stage_row": False,
            "same_parent_wave_repeat": False,
            TACTICAL_EVIDENCE_SCHEMA: evidence,
            "ask_depletion_sidecar": ask_depletion_sidecar,
            "ask_depletion_sidecar_status": ask_depletion_sidecar_status,
            "future_outcome": outcome,
            "future_outcome_rebuild_source": outcome_rebuild_source,
            "three_arm_manifest": build_three_arm_manifest(
                evidence=evidence,
                ablation_design_version=CURRENT_DESIGN_VERSION,
                control_prompt_version=str(trace.get("prompt_version") or "unknown"),
                control_trace=trace,
                outcome=outcome,
                ask_depletion_sidecar=ask_depletion_sidecar,
                current_source_gap_reason=(
                    ask_depletion_sidecar_status
                    if ask_depletion_sidecar is None
                    else None
                ),
                control_contract={
                    "prompt_sha256": trace.get("prompt_sha256"),
                    "provider": trace.get("provider_actual"),
                    "model": trace.get("model"),
                    "temperature": trace.get("request_temperature"),
                    "reasoning_effort": trace.get("request_reasoning_effort"),
                    "transport": trace.get("transport"),
                    "schema_name": payload.get("schema_name"),
                    "require_json": payload.get("require_json"),
                    "response_schema_mode": trace.get("openai_response_schema_mode"),
                    "response_schema_registry_used": trace.get(
                        "openai_response_schema_registry_used"
                    ),
                    "max_output_tokens": payload.get("max_output_tokens"),
                    "response_schema_sha256": trace.get("response_schema_sha256"),
                    "semantic_validator_version": trace.get(
                        "semantic_validator_version"
                    ),
                },
            ),
        }
        rows.append(row)
        if ask_depletion_sidecar is None:
            exclusions[f"ask_depletion_source_gap:{ask_depletion_sidecar_status}"] += 1
        if state == "source_unavailable":
            for reason in (evidence.get("source_quality") or {}).get("blockers") or []:
                exclusions[str(reason)] += 1
    future_outcome_source_pool = build_future_outcome_source_pool(
        outcome_source_pool_rows
    )
    future_outcome_source_pool_hash = str(
        future_outcome_source_pool["source_pool_content_sha256"]
    )
    validated_future_outcome_source_pools = validate_future_outcome_source_pool(
        future_outcome_source_pool
    )
    for row in rows:
        rebound_source = bind_future_outcome_rebuild_source_to_pool(
            row["future_outcome_rebuild_source"],
            source_pool_content_sha256=future_outcome_source_pool_hash,
        )
        row["future_outcome_rebuild_source"] = rebound_source
        if (
            rebuild_future_outcome_from_source(
                evidence=row[TACTICAL_EVIDENCE_SCHEMA],
                rebuild_source=rebound_source,
                source_pool=future_outcome_source_pool,
                _validated_source_pools=validated_future_outcome_source_pools,
            )
            != row["future_outcome"]
        ):
            raise ValueError("future_outcome_rebuild_source_producer_mismatch")
    validate_future_outcome_source_pool_reference_census(
        future_outcome_source_pool,
        [row["future_outcome_rebuild_source"] for row in rows],
        _validated_source_pools=validated_future_outcome_source_pools,
    )

    grouped_wave_rows: dict[tuple[str, str, str, str, str], list[int]] = defaultdict(
        list
    )
    for index, row in enumerate(rows):
        wave_key = row.get("_parent_wave_stage_key")
        if isinstance(wave_key, tuple):
            grouped_wave_rows[wave_key].append(index)
    for indexes in grouped_wave_rows.values():
        observation_indexes = [
            index
            for index in indexes
            if (rows[index][TACTICAL_EVIDENCE_SCHEMA].get("source_quality") or {}).get(
                "status"
            )
            == "pass"
            and rows[index][TACTICAL_EVIDENCE_SCHEMA].get("state")
            not in {"not_applicable", "source_unavailable"}
        ]
        ranked_indexes = observation_indexes or indexes
        primary_index = min(
            ranked_indexes,
            key=lambda index: int(
                rows[index][TACTICAL_EVIDENCE_SCHEMA].get("snapshot_captured_at_ms")
                or 0
            ),
        )
        for index in indexes:
            rows[index]["primary_parent_wave_stage_row"] = index == primary_index
            rows[index]["same_parent_wave_repeat"] = index != primary_index
        metric_predicates = {
            "primary_replay_parent_wave_stage_row": lambda row: (
                row["three_arm_manifest"].get("replay_context_eligible") is True
            ),
            "primary_control_parent_wave_stage_row": lambda row: (
                row["three_arm_manifest"].get("control_decision_eligible") is True
            ),
            "primary_paired_parent_wave_stage_row": lambda row: (
                row["three_arm_manifest"].get("paired_decision_quality_eligible")
                is True
            ),
            "primary_economic_parent_wave_stage_row": lambda row: (
                row["three_arm_manifest"].get("net_economic_evaluation_eligible")
                is True
            ),
            "primary_mature_outcome_parent_wave_stage_row": lambda row: any(
                horizon.get("mature") is True
                for horizon in (row.get("future_outcome") or {}).get("horizons") or []
            ),
        }
        for flag, predicate in metric_predicates.items():
            eligible = [index for index in indexes if predicate(rows[index])]
            if not eligible:
                continue
            selected = min(
                eligible,
                key=lambda index: int(
                    rows[index][TACTICAL_EVIDENCE_SCHEMA].get("snapshot_captured_at_ms")
                    or 0
                ),
            )
            rows[selected][flag] = True
    for row in rows:
        row.pop("_parent_wave_stage_key", None)
    state_counts = Counter(
        str((row[TACTICAL_EVIDENCE_SCHEMA] or {}).get("state") or "unknown")
        for row in rows
    )
    stage_counts = Counter(str(row.get("decision_stage") or "unknown") for row in rows)
    observation_context_eligible = sum(
        (row[TACTICAL_EVIDENCE_SCHEMA].get("source_quality") or {}).get("status")
        == "pass"
        and row[TACTICAL_EVIDENCE_SCHEMA].get("state")
        not in {"not_applicable", "source_unavailable"}
        and row.get("primary_parent_wave_stage_row") is True
        for row in rows
    )
    replay_context_eligible = sum(
        row["three_arm_manifest"].get("replay_context_eligible") is True
        and row.get("primary_replay_parent_wave_stage_row") is True
        for row in rows
    )
    economic_eligible = sum(
        row["three_arm_manifest"].get("net_economic_evaluation_eligible") is True
        and row.get("primary_economic_parent_wave_stage_row") is True
        for row in rows
    )
    control_eligible = sum(
        row["three_arm_manifest"].get("control_decision_eligible") is True
        and row.get("primary_control_parent_wave_stage_row") is True
        for row in rows
    )
    paired_eligible = sum(
        row["three_arm_manifest"].get("paired_decision_quality_eligible") is True
        and row.get("primary_paired_parent_wave_stage_row") is True
        for row in rows
    )
    mature_outcome_eligible = sum(
        any(
            horizon.get("mature") is True
            for horizon in (row.get("future_outcome") or {}).get("horizons") or []
        )
        and row.get("primary_mature_outcome_parent_wave_stage_row") is True
        for row in rows
    )
    confirmation_window_direction_counts: dict[str, Counter[str]] = defaultdict(Counter)
    confirmation_window_tuning_outcome_counts: Counter[str] = Counter()
    for row in rows:
        evidence = row[TACTICAL_EVIDENCE_SCHEMA]
        if (
            row.get("primary_parent_wave_stage_row") is not True
            or (evidence.get("source_quality") or {}).get("status") != "pass"
        ):
            continue
        axis = (row.get("future_outcome") or {}).get("confirmation_window_axis") or {}
        for observation in axis.get("observations") or []:
            horizon = str(observation.get("horizon_sec") or "unknown")
            confirmation_window_direction_counts[horizon][
                str(observation.get("direction_state") or "unknown")
            ] += 1
            for fixed_outcome in observation.get("fixed_followthrough_outcomes") or []:
                if fixed_outcome.get("tuning_outcome_eligible") is True:
                    followthrough = str(
                        fixed_outcome.get("followthrough_sec") or "unknown"
                    )
                    policy_key = f"confirm_{horizon}s_follow_{followthrough}s"
                    confirmation_window_tuning_outcome_counts[policy_key] += 1
    allocator_outcome_joined = sum(
        (row.get("future_outcome") or {}).get("allocator_event_sha256") is not None
        for row in rows
    )
    allocator_status_counts = Counter(
        str(
            (row.get("future_outcome") or {}).get("allocator_provenance_status")
            or "unknown"
        )
        for row in rows
    )
    allocator_error_counts = Counter(
        str((row.get("future_outcome") or {}).get("allocator_provenance_error"))
        for row in rows
        if (row.get("future_outcome") or {}).get("allocator_provenance_error")
    )
    allocator_join_contract_gap = bool(sum(allocator_error_counts.values()) > 0)
    allocator_valid_join_available = allocator_outcome_joined > 0
    allocator_all_rows_contract_clean = not allocator_join_contract_gap
    partial_allocator_submission_count = allocator_status_counts.get(
        "allocator_provenance_partial_submission_observation_only", 0
    )
    if verified_pipeline_rows_by_trace_symbol:
        pipeline_source_contract["outcome_join_mode"] = (
            "central_allocator_full_submission_outcome_only"
            if allocator_valid_join_available
            else (
                "partial_submission_standardized_one_share_observation_only"
                if partial_allocator_submission_count > 0
                else "standardized_one_share_observation_only"
            )
        )
    pipeline_missing_observation_only = bool(
        pipeline_source_status == "missing_observation_only"
        and any(
            str(row.get("decision_stage") or "").lower()
            in {"entry", "entry_screen", "gatekeeper", "post_probe"}
            for row in rows
        )
    )
    pipeline_source_contract["canonical_entry_pipeline_row_count"] = len(
        canonical_entry_pipeline_hashes
    )
    pipeline_source_contract["trace_symbol_linked_noncanonical_row_count"] = max(
        0,
        pipeline_census["trace_symbol_linked_row_count"]
        - len(canonical_entry_pipeline_hashes),
    )
    generated = generated_at or datetime.now().astimezone()
    report_without_hash = {
        "schema": REPORT_SCHEMA,
        "bridge_contract": _bridge_config_contract(selected_config),
        "target_date": target_date,
        "generated_at": generated.isoformat(),
        "status": (
            "pass"
            if replay_context_eligible
            and not pipeline_missing_observation_only
            and not allocator_join_contract_gap
            else "warning"
        ),
        "decision": (
            "entry_pipeline_missing_standardized_one_share_observation_only"
            if pipeline_missing_observation_only
            else (
                (
                    "entry_pipeline_allocator_partial_join_valid_rows_only"
                    if allocator_valid_join_available
                    else "entry_pipeline_allocator_join_contract_gap_report_only"
                )
                if allocator_join_contract_gap
                else (
                    "micro_three_arm_paired_replay_materialization_eligible"
                    if paired_eligible
                    else (
                        "micro_replay_context_ready_control_response_excluded"
                        if replay_context_eligible
                        else "micro_context_keep_collecting_or_source_gap"
                    )
                )
            )
        ),
        "optimization_direction": {
            "objective": (
                "maximize_after_cost_net_profit_with_fast_frequent_bounded_exposure"
            ),
            "primary_metrics": [
                "source_quality_adjusted_ev_pct",
                "notional_weighted_ev_pct",
                "net_profit",
            ],
            "diagnostic_metrics": [
                "signals_per_hour",
                "net_target_first_rate",
                "time_to_fill_ms",
                "time_to_net_target_ms",
                "position_duration_ms",
            ],
            "constraints": [
                "severe_tail_mae",
                "p95_execution_slippage_bps",
                "p95_liquidation_time_sec",
                "hard_protect_emergency_guard_unchanged",
            ],
        },
        "summary": {
            "trace_payload_join_count": len(rows),
            "micro_observation_context_eligible_primary_episode_count": (
                observation_context_eligible
            ),
            "micro_context_eligible_primary_episode_count": (replay_context_eligible),
            "control_decision_eligible_primary_episode_count": control_eligible,
            "paired_decision_quality_eligible_primary_episode_count": (paired_eligible),
            "net_economic_eligible_primary_episode_count": economic_eligible,
            "mature_outcome_eligible_primary_episode_count": (mature_outcome_eligible),
            "confirmation_window_primary_episode_direction_counts": {
                horizon: dict(counts)
                for horizon, counts in sorted(
                    confirmation_window_direction_counts.items(),
                    key=lambda item: (int(item[0]) if item[0].isdigit() else math.inf),
                )
            },
            "confirmation_window_primary_episode_tuning_outcome_eligible_counts": (
                dict(
                    sorted(
                        confirmation_window_tuning_outcome_counts.items(),
                        key=lambda item: item[0],
                    )
                )
            ),
            "entry_pipeline_allocator_outcome_joined_count": (allocator_outcome_joined),
            "entry_pipeline_allocator_partial_submission_count": (
                partial_allocator_submission_count
            ),
            "entry_pipeline_allocator_status_counts": dict(allocator_status_counts),
            "entry_pipeline_allocator_error_counts": dict(allocator_error_counts),
            "entry_pipeline_allocator_join_contract_gap": (allocator_join_contract_gap),
            "entry_pipeline_allocator_all_rows_contract_clean": (
                allocator_all_rows_contract_clean
            ),
            "entry_pipeline_allocator_invalid_rows_excluded": (
                allocator_join_contract_gap
            ),
            "entry_pipeline_allocator_tuning_input_allowed": (
                allocator_valid_join_available
            ),
            "entry_pipeline_allocator_decision_authority": (
                "valid_joined_rows_only_invalid_rows_excluded"
                if allocator_join_contract_gap and allocator_valid_join_available
                else (
                    "report_only_contract_gap"
                    if allocator_join_contract_gap
                    else (
                        "source_quality_eligible_full_submission_outcome_only"
                        if allocator_valid_join_available
                        else (
                            "partial_submission_standardized_one_share_observation_only"
                            if partial_allocator_submission_count > 0
                            else "no_allocator_join_standardized_one_share_observation_only"
                        )
                    )
                )
            ),
            "entry_pipeline_source_status": pipeline_source_status,
            "primary_metric_denominator": (
                "eligible_exact_trace_parent_wave_stage_rows"
            ),
            "same_parent_wave_repeat_count": sum(
                row.get("same_parent_wave_repeat") is True for row in rows
            ),
            "state_counts": dict(state_counts),
            "stage_counts": dict(stage_counts),
            "exclusion_counts": dict(exclusions),
            "noncausal_source_diagnostics": {
                "invalid_market_timestamp_row_count": (
                    source_store.invalid_timestamp_counts["market"]
                    if source_store is not None
                    else sum(
                        len(scoped_rows)
                        for key, scoped_rows in invalid_market_by_scope.items()
                        if key in processed_scope_keys
                    )
                ),
                "invalid_depth_timestamp_row_count": (
                    source_store.invalid_timestamp_counts["depth"]
                    if source_store is not None
                    else sum(
                        len(scoped_rows)
                        for key, scoped_rows in invalid_depth_by_scope.items()
                        if key in processed_scope_keys
                    )
                ),
                "invalid_event_reference_timestamp_row_count": (
                    source_store.invalid_timestamp_counts["reference"]
                    if source_store is not None
                    else sum(
                        len(scoped_rows)
                        for key, scoped_rows in invalid_references_by_scope.items()
                        if key in processed_scope_keys
                    )
                ),
                "included_in_prompt_context": False,
            },
        },
        "report_row_count": len(rows),
        "rows": rows,
        "future_outcome_source_pool": future_outcome_source_pool,
        "future_outcome_source_pool_content_sha256": (future_outcome_source_pool_hash),
        "future_outcome_source_pool_artifact_sha256": _sha256(
            future_outcome_source_pool
        ),
        "entry_pipeline_source": pipeline_source_contract,
        "source_materialization": (
            {
                "mode": (
                    "sqlite_persistent_relevant_source_index"
                    if source_store is not None
                    and getattr(source_store, "cache_status", "ephemeral")
                    != "ephemeral"
                    else (
                        "sqlite_bounded_per_trace"
                        if source_store is not None
                        else "in_memory_api"
                    )
                ),
                "cache": deepcopy(getattr(source_store, "cache_diagnostics", None)),
            }
        ),
        "source_exact_payload_mutated": False,
        "future_outcomes_separate_from_prompt_context": True,
        "default_exact_v2_cohort_unchanged": True,
        "provider_call_performed": False,
        "paired_replay_materialized": False,
        "paired_replay_ready": False,
        **REPORT_METRIC_CONTRACT,
        **AUTHORITY_CONTRACT,
        **(
            ABLATION_SOURCE_ONLY_AUTHORITY
            if target_date >= CURRENT_DESIGN_ACTIVATION_DATE
            else {}
        ),
    }
    return {
        **report_without_hash,
        "report_content_sha256": _sha256(report_without_hash),
    }


def _iter_jsonl(paths: Iterable[Path]) -> Iterable[dict[str, Any]]:
    for path in paths:
        yield from iter_jsonl_objects_strict(path)


def _partition_paths(root: Path, target_date: str, name: str) -> list[Path]:
    partition = root / f"trade_date={target_date}"
    selected: list[Path] = []
    for directory in sorted(partition.glob("venue=*/session=*")):
        base = directory / f"{name}.jsonl"
        selected.extend(readable_partition_path_files(base))
    return selected


def _relevant_windows(
    traces: Sequence[Mapping[str, Any]],
    payloads: Sequence[Mapping[str, Any]],
    *,
    config: BridgeConfig,
) -> dict[tuple[str, str, str], tuple[tuple[int, int], ...]]:
    payload_indexes = _payload_indexes(payloads)
    raw_windows: dict[tuple[str, str, str], list[tuple[int, int]]] = defaultdict(list)
    for trace in traces:
        payload, _ = _resolve_payload_for_trace(trace, indexes=payload_indexes)
        if payload is None:
            continue
        watermark, _ = exact_snapshot_watermark(trace, payload)
        if watermark is None:
            continue
        scope = resolve_micro_scope(trace)
        if scope.status != "resolved":
            continue
        key = (
            normalize_symbol(trace.get("stock_code")),
            scope.venue,
            scope.session_bucket,
        )
        watermark_ms = int(watermark["captured_at_ms"])
        start_ms = (
            watermark_ms
            - (config.active_wave_max_age_sec + config.context_lookback_sec) * 1_000
        )
        end_ms = (
            watermark_ms
            + _post_snapshot_source_horizon_sec(config) * 1_000
            + config.max_outcome_endpoint_lag_ms
        )
        raw_windows[key].append((start_ms, end_ms))
    windows: dict[tuple[str, str, str], tuple[tuple[int, int], ...]] = {}
    for key, values in raw_windows.items():
        merged: list[list[int]] = []
        for start_ms, end_ms in sorted(values):
            if not merged or start_ms > merged[-1][1]:
                merged.append([start_ms, end_ms])
            else:
                merged[-1][1] = max(merged[-1][1], end_ms)
        windows[key] = tuple((start, end) for start, end in merged)
    return windows


def _filter_relevant_rows(
    rows: Iterable[Mapping[str, Any]],
    windows: Mapping[tuple[str, str, str], tuple[tuple[int, int], ...]],
    *,
    reference_rows: bool = False,
) -> list[Mapping[str, Any]]:
    selected = []
    window_index = {
        key: (tuple(window[0] for window in scope_windows), scope_windows)
        for key, scope_windows in windows.items()
    }
    for row in rows:
        key = (
            normalize_symbol(row.get("symbol")),
            normalize_venue(row.get("venue")),
            _session(row.get("session_bucket")),
        )
        indexed_windows = window_index.get(key)
        if indexed_windows is None:
            continue
        starts, scope_windows = indexed_windows
        if reference_rows:
            detected_at_ms = row.get("event_detected_at_ms")
            if (
                not isinstance(detected_at_ms, int)
                or isinstance(detected_at_ms, bool)
                or detected_at_ms <= 0
            ):
                continue
            timestamp_ms = detected_at_ms
        else:
            try:
                timestamp_ms = _timestamp_ms(row.get("local_receive_timestamp"))
            except (TypeError, ValueError):
                continue
        index = bisect_right(starts, timestamp_ms) - 1
        if index >= 0 and timestamp_ms <= scope_windows[index][1]:
            selected.append(row)
    return selected


def _excluded_scopes(payload: Mapping[str, Any]) -> set[tuple[str, str, str, int]]:
    return {
        (
            str(row.get("trade_date") or ""),
            normalize_venue(row.get("venue")),
            _session(row.get("session_bucket")),
            int(row.get("sequence_epoch") or 0),
        )
        for row in payload.get("exclusions") or []
        if isinstance(row, Mapping)
    }


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    write_json_object_generation_safe(
        path,
        payload,
        ensure_ascii=False,
        indent=2,
        allow_nan=False,
        trailing_newline=True,
    )


def _iter_jsonl_with_content_provenance(
    path: Path, provenance: dict[str, Any]
) -> Iterable[dict[str, Any]]:
    """Stream one resolved JSONL source and bind its decoded content census.

    ``source_sha256`` continues to identify the bytes stored on disk (including
    gzip framing).  ``source_content_sha256`` identifies the exact decoded
    JSONL bytes consumed by the outcome-only allocator join.  The pre/post stat
    check rejects a concurrently replaced or appended source instead of
    publishing a census that is not reproducible from the declared artifact.
    """

    yield from iter_jsonl_objects_strict(path, provenance=provenance)


def _verified_cost_config_from_path(path: Path, *, target_date: date) -> BridgeConfig:
    payload = read_json_object_strict(path)
    return _verified_cost_config_from_payload(payload, target_date=target_date)


def _verified_cost_config_from_payload(
    payload: object, *, target_date: date
) -> BridgeConfig:
    if not isinstance(payload, dict):
        raise ValueError("verified_cost_profile_schema_invalid")
    if payload.get("schema") == COST_CATALOG_SCHEMA:
        _validate_cost_catalog_payload(payload, target_date=target_date)
        venues = tuple(
            sorted(
                {
                    normalize_venue(venue)
                    for profile in payload.get("profiles") or []
                    for venue in (profile.get("venues") or [])
                }
            )
        )
        canonical_payload_json = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return BridgeConfig(
            statutory_sell_tax_bps=None,
            buy_fee_bps=0.0,
            sell_fee_bps=0.0,
            uncertainty_buffer_bps=0.0,
            cost_profile_source="canonical_economic_reference_v2_catalog",
            cost_profile_verified=True,
            cost_profile_artifact_id=str(payload.get("artifact_id") or ""),
            cost_profile_artifact_sha256=_producer_sha256(payload),
            cost_profile_artifact_payload_json=canonical_payload_json,
            cost_profile_effective_date=target_date.isoformat(),
            cost_profile_venues=venues,
            cost_profile_catalog_payload_json=canonical_payload_json,
            cost_profile_catalog_content_sha256=str(
                payload.get("content_sha256") or ""
            ),
        )
    if payload.get("schema") != COST_PROFILE_SCHEMA:
        raise ValueError("verified_cost_profile_schema_invalid")
    _validate_exact_reviewed_legacy_cost_profile(payload, target_date=target_date)
    numeric_fields: dict[str, float] = {}
    for field in (
        "buy_fee_bps",
        "sell_fee_bps",
        "statutory_sell_tax_bps",
        "uncertainty_buffer_bps",
    ):
        numeric_fields[field] = float(payload[field])
    effective_date = date.fromisoformat(str(payload.get("effective_date") or ""))
    canonical_payload_json = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return BridgeConfig(
        statutory_sell_tax_bps=numeric_fields["statutory_sell_tax_bps"],
        buy_fee_bps=numeric_fields["buy_fee_bps"],
        sell_fee_bps=numeric_fields["sell_fee_bps"],
        uncertainty_buffer_bps=numeric_fields["uncertainty_buffer_bps"],
        cost_profile_source=str(payload.get("source") or ""),
        cost_profile_verified=True,
        cost_profile_artifact_id=str(payload.get("artifact_id") or ""),
        cost_profile_artifact_sha256=_producer_sha256(payload),
        cost_profile_artifact_payload_json=canonical_payload_json,
        cost_profile_effective_date=effective_date.isoformat(),
        cost_profile_venues=tuple(
            sorted({normalize_venue(value) for value in payload.get("venues") or []})
        ),
    )


def _validated_scheduled_prepared_trace_census(
    *,
    target_date: str,
    prepared_artifact: Mapping[str, Any],
    expected_artifact_sha256: str,
    expected_request_count: int,
    traces: Sequence[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Bind scheduled bridge work to one exact prepared trace census."""

    from src.engine.scalping import ai_decision_quality as quality

    target = date.fromisoformat(target_date)
    if _sha256(prepared_artifact) != expected_artifact_sha256:
        raise ValueError("prepared_artifact_outer_sha256_mismatch")
    prepared_requests, _ = quality.validate_micro_reversion_prepared_artifact(
        prepared_artifact,
        expected_target_date=target_date,
    )
    if expected_request_count <= 0 or len(prepared_requests) != expected_request_count:
        raise ValueError("prepared_request_census_mismatch")
    prepared_trace_ids = [
        str(request.get("decision_trace_id") or "") for request in prepared_requests
    ]
    prepared_trace_id_set = set(prepared_trace_ids)
    trace_rows_by_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for trace in traces:
        trace_id = str(trace.get("decision_trace_id") or "")
        if trace_id in prepared_trace_id_set:
            trace_rows_by_id[trace_id].append(trace)
    if any(
        len(trace_rows_by_id.get(trace_id, ())) != 1 for trace_id in prepared_trace_ids
    ):
        raise ValueError("prepared_trace_census_missing_or_duplicated")
    selected_traces = [trace_rows_by_id[trace_id][0] for trace_id in prepared_trace_ids]
    for trace in selected_traces:
        try:
            decision_ts = datetime.fromisoformat(
                str(trace.get("decision_ts") or "").replace("Z", "+00:00")
            )
        except ValueError as exc:
            raise ValueError("prepared_trace_target_date_mismatch") from exc
        if (
            decision_ts.tzinfo is None
            or decision_ts.utcoffset() is None
            or decision_ts.astimezone(KST).date() != target
        ):
            raise ValueError("prepared_trace_target_date_mismatch")
    census = {
        "schema": "micro_reversion_scheduled_prepared_trace_census_v1",
        "target_date": target_date,
        "prepared_artifact_sha256": expected_artifact_sha256,
        "prepared_request_count": len(prepared_trace_ids),
        "decision_trace_ids_sha256": _sha256(prepared_trace_ids),
        "exact_trace_census": True,
        "broad_manual_trace_corpus_used": False,
        "provider_call_performed": False,
        "runtime_effect": False,
        "actual_order_submitted": False,
    }
    return selected_traces, census


def _bind_scheduled_prepared_census_to_report(
    *,
    report: Mapping[str, Any],
    traces: Sequence[Mapping[str, Any]],
    census: Mapping[str, Any],
) -> dict[str, Any]:
    """Seal scheduled census provenance with the bridge artifact hash contract."""

    existing_body = {
        key: value for key, value in report.items() if key != "report_content_sha256"
    }
    bridge_trace_ids = [
        str(row.get("decision_trace_id") or "")
        for row in report.get("rows") or []
        if isinstance(row, Mapping)
    ]
    scheduled_trace_ids = {
        str(trace.get("decision_trace_id") or "") for trace in traces
    }
    if (
        report.get("report_content_sha256") != _sha256(existing_body)
        or census.get("target_date") != report.get("target_date")
        or report.get("report_row_count") != len(bridge_trace_ids)
        or any(not trace_id for trace_id in bridge_trace_ids)
        or len(bridge_trace_ids) != len(set(bridge_trace_ids))
        or not set(bridge_trace_ids).issubset(scheduled_trace_ids)
    ):
        raise ValueError("scheduled_bridge_output_trace_census_invalid")
    bound_census = {
        **dict(census),
        "bridge_joined_trace_count": len(bridge_trace_ids),
        "bridge_joined_trace_ids_sha256": _sha256(bridge_trace_ids),
        "bridge_unjoined_trace_count": len(scheduled_trace_ids) - len(bridge_trace_ids),
    }
    report_body = {
        **existing_body,
        "scheduled_prepared_trace_census": bound_census,
    }
    return {**report_body, "report_content_sha256": _sha256(report_body)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    parser.add_argument(
        "--observation-root",
        type=Path,
        default=DATA_DIR / "observations" / "scalp_micro_reversion_forward",
    )
    parser.add_argument(
        "--source-exclusion-manifest",
        type=Path,
        default=DEFAULT_SOURCE_EXCLUSION_MANIFEST,
    )
    parser.add_argument("--statutory-sell-tax-bps", type=float)
    parser.add_argument("--buy-fee-bps", type=float, default=0.0)
    parser.add_argument("--sell-fee-bps", type=float, default=0.0)
    parser.add_argument("--uncertainty-buffer-bps", type=float, default=3.0)
    parser.add_argument(
        "--cost-profile-source",
        default="operator_supplied_research_assumption",
        help="Research provenance only; CLI values never become promotion grade.",
    )
    parser.add_argument(
        "--verified-cost-profile",
        type=Path,
        help=(
            "Reviewed micro_reversion_reviewed_cost_profile_v1 or canonical "
            "micro_reversion_reviewed_cost_catalog_v2 artifact; "
            "must be paired with --symbol-master."
        ),
    )
    parser.add_argument(
        "--symbol-master",
        type=Path,
        help=(
            "Verified effective-dated symbol master used only to qualify "
            "offline economics."
        ),
    )
    parser.add_argument(
        "--entry-pipeline",
        type=Path,
        help=(
            "ENTRY_PIPELINE JSONL; defaults to "
            "data/pipeline_events/pipeline_events_DATE.jsonl."
        ),
    )
    parser.add_argument(
        "--storage-capacity-status",
        type=Path,
        help=(
            "Canonical exact-date micro-reversion capacity status. Required "
            "for --write; a fresh direct disk snapshot is also enforced."
        ),
    )
    parser.add_argument(
        "--prepared-requests",
        type=Path,
        help=(
            "Exact validated R0 prepared-request census. Scheduled use binds "
            "the bridge to these traces instead of the broad manual corpus."
        ),
    )
    parser.add_argument("--prepared-artifact-sha256")
    parser.add_argument("--prepared-request-count", type=int)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    target = date.fromisoformat(args.date)
    if target < CLEAN_BASELINE_DATE:
        parser.error("date is before clean tuning baseline")
    prepared_binding_args = (
        args.prepared_requests,
        args.prepared_artifact_sha256,
        args.prepared_request_count,
    )
    if any(value is not None for value in prepared_binding_args) and not all(
        value is not None for value in prepared_binding_args
    ):
        parser.error(
            "--prepared-requests, --prepared-artifact-sha256, and "
            "--prepared-request-count must be supplied together"
        )
    if args.prepared_request_count is not None and args.prepared_request_count <= 0:
        parser.error("--prepared-request-count must be positive")
    output = (
        DATA_DIR
        / "report"
        / "micro_reversion_ai_quality_bridge"
        / f"micro_reversion_ai_quality_bridge_{args.date}.json"
    )
    if args.write:
        if args.storage_capacity_status is None:
            parser.error("--write requires --storage-capacity-status")
        expected_capacity_path = (
            DATA_DIR
            / "report"
            / "micro_reversion_storage_capacity"
            / f"micro_reversion_storage_capacity_{args.date}.json"
        ).absolute()
        if args.storage_capacity_status.absolute() != expected_capacity_path:
            parser.error("storage capacity status path is not canonical")
        from .storage_maintenance import evaluate_large_artifact_capacity_gate

        capacity_gate = evaluate_large_artifact_capacity_gate(
            target_date=target,
            capacity_status_path=expected_capacity_path,
            storage_path=output.parent,
        )
        if capacity_gate.get("large_artifact_growth_allowed") is not True:
            parser.error(
                "large artifact capacity blocked:"
                f"{str(capacity_gate.get('status') or 'unknown')}"
            )
    logical_trace_path = (
        DATA_DIR / "ai_decision_trace" / f"ai_decision_trace_{args.date}.jsonl"
    )
    logical_payload_path = (
        DATA_DIR / "ai_decision_payloads" / f"ai_decision_payloads_{args.date}.jsonl"
    )
    trace_path = existing_or_gzip_path(logical_trace_path)
    payload_path = existing_or_gzip_path(logical_payload_path)
    if not (trace_path.exists() or trace_path.is_symlink()) or not (
        payload_path.exists() or payload_path.is_symlink()
    ):
        parser.error("exact trace or payload artifact is missing")
    exclusion_payload = load_source_exclusion_manifest(args.source_exclusion_manifest)
    if bool(args.verified_cost_profile) != bool(args.symbol_master):
        parser.error(
            "--verified-cost-profile and --symbol-master must be supplied together"
        )
    symbol_master = None
    symbol_master_sha256 = ""
    if args.verified_cost_profile:
        from .symbol_master import VerifiedSymbolMaster

        try:
            config = _verified_cost_config_from_path(
                args.verified_cost_profile,
                target_date=target,
            )
            symbol_master_payload = read_json_object_strict(args.symbol_master)
            symbol_master_sha256 = _sha256(symbol_master_payload)
            symbol_master = VerifiedSymbolMaster.from_payload(
                symbol_master_payload,
                require_canonical_owner=(
                    target >= date.fromisoformat(CURRENT_DESIGN_ACTIVATION_DATE)
                ),
            )
        except (EOFError, OSError, TypeError, ValueError) as exc:
            parser.error(str(exc))
    else:
        config = BridgeConfig(
            statutory_sell_tax_bps=args.statutory_sell_tax_bps,
            buy_fee_bps=args.buy_fee_bps,
            sell_fee_bps=args.sell_fee_bps,
            uncertainty_buffer_bps=args.uncertainty_buffer_bps,
            cost_profile_source=args.cost_profile_source,
            # Ad-hoc CLI values remain research-only.
            cost_profile_verified=False,
        )
    traces = list(_iter_jsonl((trace_path,)))
    payloads = list(_iter_jsonl((payload_path,)))
    scheduled_prepared_census: dict[str, Any] | None = None
    if args.prepared_requests is not None:
        try:
            prepared_artifact = read_json_object_strict(args.prepared_requests)
            traces, scheduled_prepared_census = (
                _validated_scheduled_prepared_trace_census(
                    target_date=args.date,
                    prepared_artifact=prepared_artifact,
                    expected_artifact_sha256=args.prepared_artifact_sha256,
                    expected_request_count=args.prepared_request_count,
                    traces=traces,
                )
            )
        except (EOFError, OSError, TypeError, ValueError) as exc:
            parser.error(f"scheduled prepared trace binding invalid:{exc}")
    verified_symbol_metadata_by_trace: dict[str, dict[str, Any]] = {}
    if symbol_master is not None:
        for trace in traces:
            trace_id = str(trace.get("decision_trace_id") or "").strip()
            if not trace_id:
                continue
            lookup = symbol_master.lookup(trace.get("stock_code"), as_of=target)
            verified_symbol_metadata_by_trace[trace_id] = {
                "lookup_status": lookup.status.value,
                "record": (
                    lookup.record.as_dict() if lookup.record is not None else None
                ),
                "symbol_master_artifact_sha256": symbol_master_sha256,
            }
    logical_entry_pipeline_path = args.entry_pipeline or (
        DATA_DIR / "pipeline_events" / f"pipeline_events_{args.date}.jsonl"
    )
    entry_pipeline_path = existing_or_gzip_path(logical_entry_pipeline_path)
    if entry_pipeline_path.exists() or entry_pipeline_path.is_symlink():
        entry_pipeline_source = {
            "status": "available_hash_verified",
            "logical_source_path": str(logical_entry_pipeline_path),
            "source_path": str(entry_pipeline_path),
            "source_compression": (
                "gzip" if entry_pipeline_path.suffix == ".gz" else "plain"
            ),
        }
        entry_pipeline_rows: Iterable[Mapping[str, Any]] = (
            _iter_jsonl_with_content_provenance(
                entry_pipeline_path,
                entry_pipeline_source,
            )
        )
    else:
        entry_pipeline_rows = ()
        entry_pipeline_source = {
            "status": "missing_observation_only",
            "logical_source_path": str(logical_entry_pipeline_path),
            "source_path": str(logical_entry_pipeline_path),
            "source_compression": None,
            "source_sha256": None,
        }
    windows = _relevant_windows(traces, payloads, config=config)
    market_paths = _partition_paths(args.observation_root, args.date, "market_stream")
    depth_paths = _partition_paths(
        args.observation_root, args.date, "market_depth_stream"
    )
    reference_paths = _partition_paths(
        args.observation_root, args.date, "market_stream_event_references"
    )
    with open_relevant_source_store(
        target_date=args.date,
        windows=windows,
        config=config,
        market_paths=market_paths,
        depth_paths=depth_paths,
        reference_paths=reference_paths,
        persistent_cache=args.write,
        observation_root=args.observation_root,
    ) as source_store:
        report = build_bridge_report(
            target_date=args.date,
            traces=traces,
            payloads=payloads,
            market_rows=(),
            depth_rows=(),
            event_references=(),
            config=config,
            excluded_scopes=_excluded_scopes(exclusion_payload),
            source_store=source_store,
            entry_pipeline_rows=entry_pipeline_rows,
            entry_pipeline_source=entry_pipeline_source,
            verified_symbol_metadata_by_trace=(
                verified_symbol_metadata_by_trace or None
            ),
        )
    if scheduled_prepared_census is not None:
        try:
            report = _bind_scheduled_prepared_census_to_report(
                report=report,
                traces=traces,
                census=scheduled_prepared_census,
            )
        except ValueError as exc:
            parser.error(str(exc))
    if args.write:
        _atomic_write_json(output, report)
    print(
        json.dumps(
            {
                "status": report["status"],
                "decision": report["decision"],
                "summary": report["summary"],
                "output": str(output) if args.write else None,
                **AUTHORITY_CONTRACT,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
