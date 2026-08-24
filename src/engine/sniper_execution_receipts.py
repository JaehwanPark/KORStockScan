"""Order execution receipt handlers for the sniper engine."""

import hashlib
import json
import os
import re
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import and_, or_

from src.database.models import RecommendationHistory
from src.engine.scalping.opening_rotation import (
    POSITION_TAG as OPENING_ROTATION_POSITION_TAG,
    entry_time_bucket as opening_rotation_entry_time_bucket,
    entry_window_version as opening_rotation_entry_window_version,
    profit_target_price as opening_rotation_profit_target_price,
    shadow_ratchet_price as opening_rotation_shadow_ratchet_price,
)
from src.engine.scalping.entry_split_order_plan import (
    recover_probe_submit_contract_for_fill,
    trip_probe_runtime_circuit,
    update_probe_runtime_bundle,
)
from src.engine.scalping.entry_candidate_lifecycle_state import (
    CONTEXT_KEY as ENTRY_CANDIDATE_LIFECYCLE_CONTEXT_KEY,
    observe_candidate_transition_safe,
)
from src.engine.scalping.position_peak_ledger import POSITION_PEAK_LEDGER
from src.engine.scalping.main_lifecycle_journal import (
    pipeline_lifecycle_fields_safe,
    pipeline_lifecycle_stage_mapped,
)
from src.engine.scalping.rising_missed_one_share_entry import (
    scout_ai_execution_attribution_fields,
)
from src.engine.sniper_entry_state import (
    get_terminal_entry_order,
    move_orders_to_terminal,
)
from src.engine.sniper_scale_in_utils import record_add_history_event
from src.engine.sniper_position_tags import (
    default_position_tag_for_strategy,
    is_default_position_tag,
    normalize_position_tag,
    normalize_strategy,
)
from src.engine.trade_profit import (
    calculate_net_profit_rate,
    calculate_net_realized_pnl,
    get_trade_cost_rate,
)
from src.utils.constants import TRADING_RULES
from src.utils import kiwoom_utils
from src.utils.logger import log_error, log_info
from src.utils.pipeline_event_logger import emit_pipeline_event
from src.engine.sniper_time import TIME_15_30
from src.engine.sniper_post_sell_feedback import record_post_sell_candidate

KIWOOM_TOKEN = None
DB = None
event_bus = None
ACTIVE_TARGETS = None
highest_prices = None
_get_fast_state = None
_weighted_avg = None
_now_ts = None
_probe_fill_continuation_callback = None
_scalp_exit_completed_callback = None
_smoothing_non_revive_post_sell_register_callback = None
_broker_snapshot_refresh_callback = None
_persist_fast_state_callback = None
_finalize_fast_state_callback = None

# Receipt module의 임시/DB 작업은 독립 락으로 직렬화하고,
# ACTIVE_TARGETS 같은 shared runtime truth는 주입된 _STATE_LOCK(실운영에서는 ENTRY_LOCK)으로만 만집니다.
# 테스트/단독 사용 시에는 _STATE_LOCK이 없을 수 있으므로 RECEIPT_LOCK을 fallback으로 둡니다.
RECEIPT_LOCK = threading.RLock()
_STATE_LOCK = None
_KST = ZoneInfo("Asia/Seoul")
_BROKER_EXECUTION_RAW_FIELD_KEYS = (
    "main_lifecycle_broker_raw_envelope_schema",
    "main_lifecycle_broker_raw_source_type",
    "9203",
    "9001",
    "913",
    "900",
    "902",
    "903",
    "905",
    "907",
    "908",
    "909",
    "910",
    "911",
    "914",
    "915",
    "919",
    "2134",
    "2135",
    "2136",
)
SELL_RECEIPT_RECOVERY_DIR = Path(
    os.getenv(
        "KORSTOCKSCAN_SELL_RECEIPT_RECOVERY_DIR",
        "data/runtime/sell_receipt_recovery",
    )
)
_SELL_RECEIPT_RECOVERY_SCHEMA = "sell_receipt_recovery_v1"
_SELL_RECEIPT_RECOVERY_MAX_AGE_SEC = 36 * 60 * 60
_SELL_RECEIPT_RECOVERY_ORPHAN_MAX_AGE_SEC = 180 * 24 * 60 * 60
_SELL_RECEIPT_RECOVERY_MAX_BYTES = 1_000_000
_SELL_RECEIPT_RECOVERY_PRUNE_INTERVAL_SEC = 60 * 60
_SELL_RECEIPT_RECOVERY_LAST_PRUNE_AT = 0.0
_EXECUTION_SIGNATURES_PER_ORDER_MAX = 512

_MAIN_LIFECYCLE_GENERATED_PIPELINE_FIELDS = frozenset(
    {
        "attempt_id",
        "main_lifecycle_identity_schema",
        "main_lifecycle_id",
        "main_lifecycle_attempt_id",
        "main_lifecycle_record_id",
        "main_lifecycle_stock_code",
        "main_lifecycle_trade_date",
        "main_lifecycle_observed_at",
        "main_lifecycle_venue",
        "main_lifecycle_venue_source",
        "main_lifecycle_venue_provenance_status",
        "main_lifecycle_session_bucket",
        "main_lifecycle_session_bucket_source",
        "main_lifecycle_session_provenance_status",
        "main_lifecycle_source_pipeline",
        "main_lifecycle_source_stage",
        "main_lifecycle_stage",
        "main_lifecycle_decision_authority",
        "main_lifecycle_runtime_effect",
        "main_lifecycle_order_authority",
        "main_lifecycle_provider_authority",
        "main_lifecycle_market_observation_expected",
        "main_lifecycle_bbo_observed",
        "main_lifecycle_depth_observed",
        "main_lifecycle_heartbeat",
        "main_lifecycle_decision_trace_id",
    }
)


def _active_state_lock():
    """ACTIVE_TARGETS/ordno/pending state mutation에 사용할 소유 락을 반환한다."""
    return _STATE_LOCK or RECEIPT_LOCK


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, "", "-", "None", "none", "null"):
            return float(default)
        return float(value)
    except Exception:
        return float(default)


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, "", "-", "None", "none", "null"):
            return int(default)
        return int(float(value))
    except Exception:
        return int(default)


def _optional_abs_int(value: Any) -> int | None:
    if value is None or not str(value).strip():
        return None
    normalized = str(value).strip()
    if not re.fullmatch(r"[+-]?(?:\d{1,3}(?:,\d{3})+|\d+)", normalized):
        return None
    try:
        return abs(int(normalized.replace(",", "")))
    except (TypeError, ValueError):
        return None


def _broker_execution_context(
    exec_data: dict[str, Any], *, received_at: datetime
) -> tuple[datetime, dict[str, Any]]:
    """Resolve FID 908 on the local trading date and retain venue provenance."""

    raw_time = str(exec_data.get("broker_execution_time_raw", "") or "").strip()
    observed_at = received_at
    time_source = "local_receive_time_fallback"
    if raw_time.isdigit() and len(raw_time) == 6:
        try:
            parsed_time = datetime.strptime(raw_time[:6], "%H%M%S").time()
            candidate = datetime.combine(
                received_at.date(), parsed_time, tzinfo=received_at.tzinfo
            )
            if candidate - received_at > timedelta(hours=12):
                candidate -= timedelta(days=1)
            elif received_at - candidate > timedelta(hours=12):
                candidate += timedelta(days=1)
            observed_at = candidate
            time_source = "official_fid_908"
        except ValueError:
            pass
    actual_venue = str(exec_data.get("actual_execution_venue", "") or "").upper()
    if actual_venue not in {"KRX", "NXT"}:
        actual_venue = ""
    venue_source = (
        "official_fid_2134_2135"
        if actual_venue
        else "official_exchange_fields_ambiguous_or_missing"
    )
    fields = {
        "broker_execution_time_raw": raw_time or "-",
        "broker_execution_time_source": time_source,
        "broker_execution_received_at": received_at.isoformat(),
        "broker_execution_observed_at": observed_at.isoformat(),
        "broker_actual_execution_venue": actual_venue or "UNKNOWN",
        "broker_actual_execution_venue_source": venue_source,
        "broker_actual_exchange_code": str(
            exec_data.get("actual_exchange_code", "") or "-"
        ),
        "broker_actual_exchange_name": str(
            exec_data.get("actual_exchange_name", "") or "-"
        ),
        "broker_sor_flag": str(exec_data.get("sor_flag", "") or "-").upper(),
        "broker_execution_provenance_complete": bool(
            time_source == "official_fid_908" and actual_venue
        ),
        # Overwrite every raw slot on each receipt.  This prevents a partial
        # later packet from inheriting native FIDs from a prior execution and
        # creating a hybrid promotion proof.  These values are telemetry only;
        # custody continues to use the normalized fields above.
        **{key: exec_data.get(key) for key in _BROKER_EXECUTION_RAW_FIELD_KEYS},
    }
    return observed_at, fields


def _safe_bool(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _probe_venue_provenance_fields(stock: dict[str, Any]) -> dict[str, str]:
    effective_venue = (
        str(
            stock.get("entry_execution_cohort")
            or stock.get("rising_missed_effective_venue")
            or stock.get("effective_venue")
            or stock.get(
                "rising_missed_tp1_submit_context_rising_missed_effective_venue"
            )
            or ""
        )
        .strip()
        .upper()
    )
    market_session_bucket = str(
        stock.get("rising_missed_market_session_bucket")
        or stock.get("market_session_bucket")
        or stock.get(
            "rising_missed_tp1_submit_context_rising_missed_market_session_bucket"
        )
        or ""
    ).strip()
    fields: dict[str, str] = {}
    if effective_venue in {"KRX", "NXT", "PREMARKET_KRX_LIKE"}:
        fields["effective_venue"] = effective_venue
        fields["rising_missed_effective_venue"] = effective_venue
    if market_session_bucket:
        fields["market_session_bucket"] = market_session_bucket
        fields["rising_missed_market_session_bucket"] = market_session_bucket
    broker_route = str(stock.get("entry_execution_broker_route") or "").strip().upper()
    if broker_route in {"KRX", "NXT", "SOR"}:
        fields["broker_route"] = broker_route
        fields["entry_execution_broker_route"] = broker_route
        fields["broker_route_resolution"] = str(
            stock.get("entry_execution_broker_route_resolution")
            or "recorded_at_successful_entry_submit"
        )
    return fields


def _probe_observation_contract_fields(stock: dict[str, Any]) -> dict[str, Any]:
    fields: dict[str, Any] = {
        "metric_role": "real_execution_quality",
        "decision_authority": "operator_override_observation_only",
        "window_policy": "same_day_operator_canary",
        "sample_floor": "5_bundles",
        "primary_decision_metric": "probe_fill_to_first_residual_limit_gap_bps",
        "source_quality_gate": "exact_probe_receipt_and_fresh_consistent_bbo",
        "allowed_runtime_apply": False,
        "forbidden_uses": (
            "live_auto_promotion|threshold_mutation|provider_route_change|"
            "quantity_cap_release|broker_guard_bypass|full_live_approval"
        ),
    }
    post_probe_enabled = str(
        os.getenv("KORSTOCKSCAN_DYNAMIC_ENTRY_PRICE_RESOLVER_POST_PROBE_ENABLED", "")
    ).strip().lower() in {"1", "true", "yes", "on"}
    probe_first_enabled = str(
        os.getenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ENABLED", "")
    ).strip().lower() in {"1", "true", "yes", "on"}
    if post_probe_enabled and probe_first_enabled:
        fields.update(
            {
                "decision_authority": "dynamic_entry_price_resolver_p1_post_probe",
                "window_policy": "same_day_probe_fill_ttl",
                "primary_decision_metric": "post_probe_direction_state",
                "source_quality_gate": (
                    "exact_probe_receipt_fresh_bbo_two_direction_groups"
                ),
            }
        )
    fields.update(_probe_venue_provenance_fields(stock))
    fields.update(
        {
            "entry_split_probe_phase": (
                stock.get("entry_split_probe_phase") or "unknown"
            ),
            "entry_split_probe_abort_reason": (
                stock.get("entry_split_probe_abort_reason") or "-"
            ),
            "entry_split_probe_abort_detail_reason": (
                stock.get("entry_split_probe_abort_detail_reason") or "-"
            ),
            "entry_split_probe_wait_contract_at_submit": bool(
                _safe_bool(
                    stock.get("entry_split_probe_wait_contract_at_submit", False)
                )
            ),
            "probe_confirmation_count": max(
                0, _safe_int(stock.get("probe_confirmation_count"), 0)
            ),
            "probe_confirmation_required_count": 2,
            "probe_confirmation_last_state": (
                stock.get("probe_confirmation_last_state") or "UNKNOWN"
            ),
            "probe_expand_forbidden": bool(stock.get("probe_expand_forbidden", False)),
            "entry_split_probe_residual_expand_forbidden": bool(
                stock.get(
                    "entry_split_probe_residual_expand_forbidden",
                    stock.get("probe_expand_forbidden", False),
                )
            ),
            "entry_split_probe_scale_in_forbidden": bool(
                stock.get("entry_split_probe_scale_in_forbidden", False)
            ),
            "entry_split_probe_scale_in_recheck_allowed": bool(
                stock.get("entry_split_probe_scale_in_recheck_allowed", False)
            ),
            "entry_split_probe_scale_in_recheck_origin": (
                stock.get("entry_split_probe_scale_in_recheck_origin") or "-"
            ),
        }
    )
    return fields


_SCOUT_AI_ATTRIBUTION_SNAPSHOT_KEYS = (
    "rising_missed_one_share_entry_forced",
    "rising_missed_one_share_scout",
    "forced_entry_reason",
    "entry_split_probe_bundle_id",
    "entry_split_probe_exit_bundle_id",
    "rising_missed_scout_parent_ai_decision_trace_id",
    "rising_missed_scout_parent_ai_snapshot_id",
    "rising_missed_scout_parent_ai_action",
    "rising_missed_scout_parent_ai_score",
    "rising_missed_scout_parent_ai_result_source",
    "rising_missed_scout_parent_ai_contract_status",
    "rising_missed_scout_parent_ai_prompt_version",
    "rising_missed_scout_parent_ai_probe_intent",
    "rising_missed_scout_parent_ai_probe_intent_status",
    "rising_missed_scout_parent_ai_probe_intent_eligibility_path",
    "rising_missed_scout_parent_ai_probe_intent_after_cost_reward_risk",
)
_ENTRY_CANDIDATE_LIFECYCLE_SNAPSHOT_KEYS = (ENTRY_CANDIDATE_LIFECYCLE_CONTEXT_KEY,)
_MAIN_LIFECYCLE_SNAPSHOT_KEYS = (
    "id",
    "scanner_promotion_id",
    "scanner_generation_id",
    "effective_venue",
    "rising_missed_effective_venue",
    "entry_setup_live_policy_effective_venue",
    "market_session_bucket",
    "rising_missed_market_session_bucket",
    "entry_setup_live_policy_session_bucket",
    "last_watching_ai_decision_trace_id",
    "last_watching_ai_attempt_decision_trace_id",
)
_BROKER_EXECUTION_PROVENANCE_KEYS = (
    "broker_execution_time_raw",
    "broker_execution_time_source",
    "broker_execution_received_at",
    "broker_execution_observed_at",
    "broker_actual_execution_venue",
    "broker_actual_execution_venue_source",
    "broker_actual_exchange_code",
    "broker_actual_exchange_name",
    "broker_sor_flag",
    "broker_execution_provenance_complete",
    *_BROKER_EXECUTION_RAW_FIELD_KEYS,
)
_GENERAL_ENTRY_MARGIN_POSITION_KEYS = (
    "general_entry_margin_authority_reason",
    "general_entry_margin_cash_guard_bypassed",
    "general_entry_margin_credit_order_api_used",
    "general_entry_margin_exact_price_revalidated",
    "general_entry_margin_one_share_authorized",
    "general_entry_margin_orderable_amount",
    "general_entry_margin_orderable_qty_cap",
    "general_entry_margin_order_api",
    "general_entry_margin_order_leg_limit_price",
    "general_entry_margin_order_leg_qty",
    "general_entry_margin_market_order_forbidden",
    "general_entry_margin_quantity_owner",
    "general_entry_margin_rate",
    "general_entry_margin_requested_unit_price",
    "general_entry_margin_scale_in_allowed",
    "general_entry_margin_scale_in_forbidden",
    "general_entry_margin_scope",
)
_BUY_RECEIPT_SNAPSHOT_KEYS = (
    *_ENTRY_CANDIDATE_LIFECYCLE_SNAPSHOT_KEYS,
    *_MAIN_LIFECYCLE_SNAPSHOT_KEYS,
    *_BROKER_EXECUTION_PROVENANCE_KEYS,
    "buy_execution_notified",
    "buy_price",
    "buy_qty",
    "initial_buy_qty",
    "last_entry_receipt_economics_complete",
    "last_entry_receipt_execution_no",
    "scale_in_filled_qty",
    "code",
    "actual_order_submitted",
    *_GENERAL_ENTRY_MARGIN_POSITION_KEYS,
    "msg_audience",
    "name",
    "opening_rotation_entry_time_bucket",
    "opening_rotation_entry_best_bid",
    "opening_rotation_episode_id",
    "opening_rotation_episode_promotion_id",
    "opening_rotation_episode_phase",
    "opening_rotation_margin_authority_reason",
    "opening_rotation_margin_cash_guard_bypassed",
    "opening_rotation_margin_one_share_authorized",
    "opening_rotation_margin_orderable_amount",
    "opening_rotation_margin_orderable_qty_cap",
    "opening_rotation_margin_order_api",
    "opening_rotation_margin_rate",
    "opening_rotation_margin_requested_unit_price",
    "opening_rotation_margin_credit_order_api_used",
    "opening_rotation_profile_id",
    "opening_rotation_policy_hash",
    "opening_rotation_policy_schema_version",
    "opening_rotation_profit_target_price",
    "opening_rotation_profit_target_order_no",
    "opening_rotation_holding_ai_called",
    "opening_rotation_ratchet_shadow_price",
    "opening_rotation_ratchet_shadow_recorded",
    "opening_rotation_window_version",
    "pending_buy_msg",
    "scalp_live_simulator",
    "simulation_book",
    "simulation_owner",
    "swing_live_order_dry_run",
)
_SELL_RECEIPT_SNAPSHOT_KEYS = (
    *_ENTRY_CANDIDATE_LIFECYCLE_SNAPSHOT_KEYS,
    *_MAIN_LIFECYCLE_SNAPSHOT_KEYS,
    *_BROKER_EXECUTION_PROVENANCE_KEYS,
    *_SCOUT_AI_ATTRIBUTION_SNAPSHOT_KEYS,
    "actual_order_submitted",
    "broker_order_forbidden",
    "buy_price",
    "buy_qty",
    "code",
    "fast_exit_decision_mark_price",
    "fast_exit_decision_executable_sell_price",
    "fast_exit_decision_peak_price",
    "fast_exit_decision_quote_state",
    "fast_exit_decision_quote_reason",
    *_GENERAL_ENTRY_MARGIN_POSITION_KEYS,
    "exit_decision_mark_price",
    "exit_decision_executable_sell_price",
    "exit_decision_peak_price",
    "exit_decision_quote_state",
    "exit_decision_quote_reason",
    "last_exit_current_ai_score",
    "last_exit_decision_source",
    "last_exit_held_sec",
    "last_exit_peak_profit",
    "last_exit_rule",
    "last_exit_same_symbol_soft_stop_cooldown_would_block",
    "last_exit_soft_stop_threshold_pct",
    "mae_pct",
    "mfe_pct",
    "msg_audience",
    "name",
    "nxt_rising_missed_tp1_partial_fill_amount",
    "nxt_rising_missed_tp1_partial_filled_qty",
    "nxt_rising_missed_tp1_partial_avg_sell_price",
    "nxt_rising_missed_tp1_partial_realized_pnl_krw",
    "no_scale_in_counterfactual_profit_pct",
    "opening_rotation_entry_time_bucket",
    "opening_rotation_entry_best_bid",
    "opening_rotation_episode_id",
    "opening_rotation_episode_promotion_id",
    "opening_rotation_episode_phase",
    "opening_rotation_margin_authority_reason",
    "opening_rotation_margin_cash_guard_bypassed",
    "opening_rotation_margin_one_share_authorized",
    "opening_rotation_margin_orderable_amount",
    "opening_rotation_margin_orderable_qty_cap",
    "opening_rotation_margin_order_api",
    "opening_rotation_margin_rate",
    "opening_rotation_margin_requested_unit_price",
    "opening_rotation_margin_credit_order_api_used",
    "opening_rotation_profile_id",
    "opening_rotation_policy_hash",
    "opening_rotation_policy_schema_version",
    "opening_rotation_profit_target_price",
    "opening_rotation_profit_target_order_no",
    "opening_rotation_holding_ai_called",
    "opening_rotation_holding_ai_action",
    "opening_rotation_ratchet_shadow_price",
    "opening_rotation_ratchet_shadow_recorded",
    "opening_rotation_window_version",
    "pending_sell_msg",
    "post_add_avg_price",
    "post_add_qty",
    "position_tag",
    "pre_add_avg_price",
    "pre_add_qty",
    "scalp_live_simulator",
    "scalp_trailing_continuation_recheck_consumed_id",
    "scalp_trailing_continuation_recheck_consumed_position_key",
    "scale_in_incremental_realized_delta_pct",
    "sell_execution_order_no",
    "simulation_book",
    "simulation_owner",
    "strategy",
    "swing_live_order_dry_run",
)
_ADD_RECEIPT_SNAPSHOT_KEYS = (
    *_ENTRY_CANDIDATE_LIFECYCLE_SNAPSHOT_KEYS,
    *_MAIN_LIFECYCLE_SNAPSHOT_KEYS,
    *_BROKER_EXECUTION_PROVENANCE_KEYS,
    "actual_order_submitted",
    "add_count",
    "avg_down_count",
    "buy_price",
    "buy_qty",
    "initial_buy_qty",
    "scale_in_filled_qty",
    "code",
    "hard_stop_price",
    "msg_audience",
    "name",
    "pending_add_initial_buy_price",
    "pending_add_initial_buy_qty",
    "post_add_avg_price",
    "post_add_qty",
    "pyramid_count",
    "pre_add_avg_price",
    "pre_add_qty",
    "scale_in_locked",
    "scalp_live_simulator",
    "last_add_reason",
    "last_add_economic_direction",
    "last_add_avg_price_improved",
    "last_add_receipt_economics_complete",
    "last_add_receipt_execution_no",
    "shallow_volatility_avg_down_count",
    "shallow_volatility_avg_down_last_at",
    "simulation_book",
    "simulation_owner",
    "strategy",
    "swing_live_order_dry_run",
    "trailing_stop_price",
)
_PENDING_ADD_META_KEYS = (
    "pending_add_order",
    "pending_add_type",
    "pending_add_reason",
    "pending_add_qty",
    "pending_add_ord_no",
    "pending_add_requested_at",
    "pending_add_counted",
    "pending_add_filled_qty",
    "pending_add_filled_amount",
    "pending_add_initial_buy_price",
    "pending_add_initial_buy_qty",
    "pending_add_execution_notice_pending",
    "pending_add_winner_recovery_ai_thesis_state",
    "pending_add_winner_recovery_ai_parent_action",
    "pending_add_winner_recovery_ai_parent_prompt_version",
    "pending_add_winner_recovery_ai_parent_trace_id",
    "pending_add_winner_recovery_ai_parent_snapshot_id",
    "pending_add_winner_recovery_holding_ai_action",
    "pending_add_winner_recovery_holding_ai_data_quality",
    "pending_add_winner_recovery_holding_ai_input_schema",
    "pending_add_winner_recovery_ai_tape_substitution_applied",
    "_add_receipt_requested_by_order_no",
    "_add_receipt_filled_by_order_no",
    "_add_receipt_filled_amount_by_order_no",
    "_add_receipt_economics_complete_by_order_no",
    "_add_receipt_executions_by_order_no",
    "pending_add_notice_by_order_no",
    "scale_in_receipt_reconciled_before_ordno_bind",
    "add_order_time",
    "add_odno",
)
_FAST_EXIT_DECISION_RESET_KEYS = (
    "fast_exit_decision_mark_price",
    "fast_exit_decision_executable_sell_price",
    "fast_exit_decision_peak_price",
    "fast_exit_decision_quote_state",
    "fast_exit_decision_quote_reason",
)
_EXIT_DECISION_RESET_KEYS = (
    "exit_decision_mark_price",
    "exit_decision_executable_sell_price",
    "exit_decision_peak_price",
    "exit_decision_quote_state",
    "exit_decision_quote_reason",
)
_POSITION_PEAK_RESET_KEYS = (
    "position_peak_cycle_id",
    "position_peak_persisted_price",
    "position_peak_persisted_at",
    "position_peak_restore_reason",
    "position_peak_restored_price",
    "position_peak_runtime_price",
)
_NXT_TP1_PARTIAL_RESET_KEYS = (
    "nxt_rising_missed_tp1_partial_pending",
    "nxt_rising_missed_tp1_partial_applied",
    "nxt_rising_missed_tp1_partial_requested_qty",
    "nxt_rising_missed_tp1_partial_filled_qty",
    "nxt_rising_missed_tp1_partial_fill_amount",
    "nxt_rising_missed_tp1_partial_avg_sell_price",
    "nxt_rising_missed_tp1_partial_original_qty",
    "nxt_rising_missed_tp1_partial_completed_at",
    "nxt_rising_missed_tp1_partial_realized_profit_pct",
    "nxt_rising_missed_tp1_partial_realized_pnl_krw",
    "nxt_rising_missed_tp1_partial_executions_by_no",
)
_SELL_EXECUTION_RECEIPT_STATE_KEY = "_sell_execution_receipt_state"
_SELL_REVIVE_RESET_KEYS = (
    *_NXT_TP1_PARTIAL_RESET_KEYS,
    *_ENTRY_CANDIDATE_LIFECYCLE_SNAPSHOT_KEYS,
    "odno",
    "order_time",
    "order_price",
    "buy_time",
    "target_buy_price",
    "pending_buy_msg",
    "pending_sell_msg",
    "sell_odno",
    "sell_ord_no",
    "sell_order_time",
    "sell_target_price",
    _SELL_EXECUTION_RECEIPT_STATE_KEY,
    "sell_reconciled_remaining_qty",
    "sell_partial_exit_carry_active",
    "sell_partial_exit_recovery_required",
    "exit_requested",
    "exit_order_type",
    "exit_order_time",
    "entry_lifecycle_conflict",
    "entry_lifecycle_conflict_fields",
    "pending_entry_orders",
    "entry_mode",
    "entry_requested_qty",
    "entry_filled_qty",
    "entry_fill_amount",
    "entry_bundle_id",
    "entry_submit_ai_score",
    "holding_entry_ai_score",
    "holding_ai_score_seeded_from_entry",
    "requested_buy_qty",
    "initial_buy_qty",
    "scale_in_filled_qty",
    "scale_in_locked",
    "_entry_receipt_filled_by_order_no",
    "_entry_receipt_requested_by_order_no",
    "_entry_receipt_filled_amount_by_order_no",
    "_entry_receipt_economics_complete_by_order_no",
    "_entry_receipt_executions_by_order_no",
    "entry_receipt_reconciled_before_ordno_bind",
    "entry_partial_fill_notified_qty",
    "entry_partial_fill_deferred_notice",
    "entry_partial_fill_deferred_at",
    "entry_submit_notice_pending",
    "entry_submit_notice_enqueued",
    "buy_execution_notified",
    "trailing_stop_price",
    "hard_stop_price",
    "protect_profit_pct",
    "entry_split_probe_phase",
    "entry_split_probe_bundle_id",
    "entry_split_probe_exit_bundle_id",
    "entry_split_probe_requested_qty",
    "entry_split_probe_continuation",
    "entry_split_probe_submit_best_ask",
    "entry_split_probe_timeout_sec",
    "entry_split_probe_max_slippage_bps",
    "entry_split_probe_anchor_mode",
    "entry_split_probe_submitting_at",
    "entry_split_probe_submitted_at",
    "entry_split_probe_order_no",
    "entry_split_probe_fill_price",
    "entry_split_probe_filled_at",
    "entry_split_probe_residual_claimed",
    "entry_split_probe_recheck_due_at",
    "entry_split_probe_recheck_count",
    "entry_split_probe_deferred_once",
    "entry_split_probe_direction_state",
    "entry_split_probe_direction_reason",
    "entry_split_probe_continuation_action",
    "entry_split_probe_offset_profile",
    "entry_split_probe_nxt_wait_fast_tape_bounded_single_leg",
    "entry_split_probe_bounded_partial_submission",
    "entry_split_probe_scale_in_forbidden",
    "entry_split_probe_soft_abort",
    "entry_split_probe_scale_in_recheck_allowed",
    "entry_split_probe_scale_in_recheck_origin",
    "entry_split_probe_scale_in_recheck_reason",
    "entry_split_probe_source_quality_recheck_released",
    "entry_split_probe_source_quality_recheck_released_at",
    "entry_split_probe_source_quality_recheck_unfilled_qty",
    "entry_split_probe_source_quality_recheck_reason",
    "entry_split_probe_source_quality_recheck_pending",
    "entry_split_probe_abort_reason",
    "entry_split_probe_abort_detail_reason",
    "entry_split_probe_ai_action_at_submit",
    "entry_split_probe_wait_contract_at_submit",
    "entry_split_probe_direction_positive_groups",
    "entry_split_probe_direction_negative_groups",
    "entry_split_probe_direction_evaluated_at",
    "entry_split_probe_direction_evidence_signature",
    "probe_confirmation_count",
    "probe_confirmation_last_at",
    "probe_confirmation_last_state",
    "probe_confirmation_last_signature",
    "entry_split_probe_terminal_at",
    "entry_split_probe_terminal_outcome",
    "entry_split_probe_terminal_abort_reason",
    "entry_split_probe_terminal_abort_detail_reason",
    "entry_split_probe_terminal_direction_state",
    "entry_split_probe_terminal_direction_reason",
    "entry_split_probe_terminal_continuation_action",
    "entry_split_probe_terminal_positive_groups",
    "entry_split_probe_terminal_negative_groups",
    "entry_split_probe_terminal_confirmation_count",
    "entry_split_probe_terminal_failure_signature",
    "probe_expand_forbidden",
    "entry_split_probe_residual_expand_forbidden",
    "peak_rebaseline_pending",
    "peak_basis_qty",
    "peak_basis_avg_price",
    "peak_basis_mark_price",
    "peak_basis_at",
    "exit_token",
    "exit_decided_at",
    "exit_order_sent_at",
    "fast_exit_retry_pending",
    "fast_exit_retry_reason",
    "fast_exit_retry_at",
    "fast_exit_last_error",
    "fast_exit_trigger_kind",
    "fast_exit_rest_retry_after",
    *_GENERAL_ENTRY_MARGIN_POSITION_KEYS,
    *_FAST_EXIT_DECISION_RESET_KEYS,
    *_EXIT_DECISION_RESET_KEYS,
    *_POSITION_PEAK_RESET_KEYS,
    "rising_missed_scout_upgraded",
)
_SELL_COMPLETE_RESET_KEYS = (
    *_NXT_TP1_PARTIAL_RESET_KEYS,
    *_ENTRY_CANDIDATE_LIFECYCLE_SNAPSHOT_KEYS,
    *_SCOUT_AI_ATTRIBUTION_SNAPSHOT_KEYS,
    "smoothing_source_only_path_journals",
    "pending_sell_msg",
    "sell_odno",
    "sell_ord_no",
    "sell_execution_order_no",
    "sell_order_time",
    "sell_target_price",
    _SELL_EXECUTION_RECEIPT_STATE_KEY,
    "sell_reconciled_remaining_qty",
    "sell_partial_exit_carry_active",
    "sell_partial_exit_recovery_required",
    "exit_requested",
    "exit_order_type",
    "exit_order_time",
    "pending_entry_orders",
    "entry_mode",
    "entry_requested_qty",
    "entry_filled_qty",
    "entry_fill_amount",
    "entry_bundle_id",
    "entry_submit_ai_score",
    "holding_entry_ai_score",
    "holding_ai_score_seeded_from_entry",
    "requested_buy_qty",
    "initial_buy_qty",
    "scale_in_filled_qty",
    "_entry_receipt_filled_by_order_no",
    "_entry_receipt_requested_by_order_no",
    "_entry_receipt_filled_amount_by_order_no",
    "_entry_receipt_economics_complete_by_order_no",
    "_entry_receipt_executions_by_order_no",
    "entry_receipt_reconciled_before_ordno_bind",
    "entry_partial_fill_notified_qty",
    "entry_partial_fill_deferred_notice",
    "entry_partial_fill_deferred_at",
    "entry_submit_notice_pending",
    "entry_submit_notice_enqueued",
    "buy_execution_notified",
    "entry_lifecycle_conflict",
    "entry_lifecycle_conflict_fields",
    "trailing_stop_price",
    "hard_stop_price",
    "protect_profit_pct",
    "entry_split_probe_phase",
    "entry_split_probe_bundle_id",
    "entry_split_probe_exit_bundle_id",
    "entry_split_probe_requested_qty",
    "entry_split_probe_continuation",
    "entry_split_probe_submit_best_ask",
    "entry_split_probe_timeout_sec",
    "entry_split_probe_max_slippage_bps",
    "entry_split_probe_anchor_mode",
    "entry_split_probe_submitting_at",
    "entry_split_probe_submitted_at",
    "entry_split_probe_order_no",
    "entry_split_probe_fill_price",
    "entry_split_probe_filled_at",
    "entry_split_probe_residual_claimed",
    "entry_split_probe_recheck_due_at",
    "entry_split_probe_recheck_count",
    "entry_split_probe_deferred_once",
    "entry_split_probe_direction_state",
    "entry_split_probe_direction_reason",
    "entry_split_probe_continuation_action",
    "entry_split_probe_offset_profile",
    "entry_split_probe_nxt_wait_fast_tape_bounded_single_leg",
    "entry_split_probe_bounded_partial_submission",
    "entry_split_probe_scale_in_forbidden",
    "entry_split_probe_soft_abort",
    "entry_split_probe_scale_in_recheck_allowed",
    "entry_split_probe_scale_in_recheck_origin",
    "entry_split_probe_scale_in_recheck_reason",
    "entry_split_probe_source_quality_recheck_released",
    "entry_split_probe_source_quality_recheck_released_at",
    "entry_split_probe_source_quality_recheck_unfilled_qty",
    "entry_split_probe_source_quality_recheck_reason",
    "entry_split_probe_source_quality_recheck_pending",
    "entry_split_probe_abort_reason",
    "entry_split_probe_abort_detail_reason",
    "entry_split_probe_ai_action_at_submit",
    "entry_split_probe_wait_contract_at_submit",
    "entry_split_probe_direction_positive_groups",
    "entry_split_probe_direction_negative_groups",
    "entry_split_probe_direction_evaluated_at",
    "entry_split_probe_direction_evidence_signature",
    "probe_confirmation_count",
    "probe_confirmation_last_at",
    "probe_confirmation_last_state",
    "probe_confirmation_last_signature",
    "entry_split_probe_terminal_at",
    "entry_split_probe_terminal_outcome",
    "entry_split_probe_terminal_abort_reason",
    "entry_split_probe_terminal_abort_detail_reason",
    "entry_split_probe_terminal_direction_state",
    "entry_split_probe_terminal_direction_reason",
    "entry_split_probe_terminal_continuation_action",
    "entry_split_probe_terminal_positive_groups",
    "entry_split_probe_terminal_negative_groups",
    "entry_split_probe_terminal_confirmation_count",
    "entry_split_probe_terminal_failure_signature",
    "probe_expand_forbidden",
    "entry_split_probe_residual_expand_forbidden",
    "peak_rebaseline_pending",
    "peak_basis_qty",
    "peak_basis_avg_price",
    "peak_basis_mark_price",
    "peak_basis_at",
    "exit_token",
    "exit_decided_at",
    "exit_order_sent_at",
    "fast_exit_retry_pending",
    "fast_exit_retry_reason",
    "fast_exit_retry_at",
    "fast_exit_last_error",
    "fast_exit_trigger_kind",
    "fast_exit_rest_retry_after",
    *_GENERAL_ENTRY_MARGIN_POSITION_KEYS,
    *_FAST_EXIT_DECISION_RESET_KEYS,
    *_EXIT_DECISION_RESET_KEYS,
    *_POSITION_PEAK_RESET_KEYS,
    "rising_missed_scout_upgraded",
    "scalp_trailing_continuation_recheck_consumed_id",
    "scalp_trailing_continuation_recheck_consumed_position_key",
    "scalp_trailing_continuation_recheck_second_extension_logged_position_key",
    "scalp_trailing_continuation_runtime_position_token",
)
_ENTRY_RECEIPT_FILLED_BY_ORDER_KEY = "_entry_receipt_filled_by_order_no"
_ENTRY_RECEIPT_REQUESTED_BY_ORDER_KEY = "_entry_receipt_requested_by_order_no"
_ENTRY_RECEIPT_AMOUNT_BY_ORDER_KEY = "_entry_receipt_filled_amount_by_order_no"
_ENTRY_RECEIPT_ECONOMICS_BY_ORDER_KEY = "_entry_receipt_economics_complete_by_order_no"
_ENTRY_RECEIPT_EXECUTIONS_BY_ORDER_KEY = "_entry_receipt_executions_by_order_no"
_ENTRY_RECEIPT_NO_ORDER_KEY = "__entry_without_order_no__"
_ADD_RECEIPT_FILLED_BY_ORDER_KEY = "_add_receipt_filled_by_order_no"
_ADD_RECEIPT_REQUESTED_BY_ORDER_KEY = "_add_receipt_requested_by_order_no"
_ADD_RECEIPT_AMOUNT_BY_ORDER_KEY = "_add_receipt_filled_amount_by_order_no"
_ADD_RECEIPT_ECONOMICS_BY_ORDER_KEY = "_add_receipt_economics_complete_by_order_no"
_ADD_RECEIPT_EXECUTIONS_BY_ORDER_KEY = "_add_receipt_executions_by_order_no"
_ADD_RECEIPT_NO_ORDER_KEY = "__add_without_order_no__"


def bind_execution_dependencies(
    *,
    kiwoom_token=None,
    db=None,
    event_bus_instance=None,
    active_targets=None,
    highest_prices_map=None,
    get_fast_state=None,
    weighted_avg=None,
    now_ts=None,
    state_lock=None,
    probe_fill_continuation_callback=None,
    scalp_exit_completed_callback=None,
    smoothing_non_revive_post_sell_register_callback=None,
    broker_snapshot_refresh_callback=None,
    persist_fast_state_callback=None,
    finalize_fast_state_callback=None,
    state_machine=None,
    **_unused_kwargs,
):
    """Receipt 모듈 의존성 주입.

    lock ownership:
    - `state_lock`: ACTIVE_TARGETS 및 target_stock runtime truth를 보호하는 상위 락
    - `RECEIPT_LOCK`: state_lock 미주입 테스트/단독 경로의 fallback 직렬화 락
    """
    global KIWOOM_TOKEN, DB, event_bus, ACTIVE_TARGETS, highest_prices
    global _get_fast_state, _weighted_avg, _now_ts, _STATE_LOCK
    global _probe_fill_continuation_callback, _scalp_exit_completed_callback
    global _smoothing_non_revive_post_sell_register_callback
    global _broker_snapshot_refresh_callback
    global _persist_fast_state_callback, _finalize_fast_state_callback

    if kiwoom_token is not None:
        KIWOOM_TOKEN = kiwoom_token
    if db is not None:
        DB = db
    if event_bus_instance is not None:
        event_bus = event_bus_instance
    if active_targets is not None:
        ACTIVE_TARGETS = active_targets
    if highest_prices_map is not None:
        highest_prices = highest_prices_map
    if get_fast_state is not None:
        _get_fast_state = get_fast_state
    if weighted_avg is not None:
        _weighted_avg = weighted_avg
    if now_ts is not None:
        _now_ts = now_ts
    if state_lock is not None:
        _STATE_LOCK = state_lock
    if probe_fill_continuation_callback is not None:
        _probe_fill_continuation_callback = probe_fill_continuation_callback
    if scalp_exit_completed_callback is not None:
        _scalp_exit_completed_callback = scalp_exit_completed_callback
    if smoothing_non_revive_post_sell_register_callback is not None:
        _smoothing_non_revive_post_sell_register_callback = (
            smoothing_non_revive_post_sell_register_callback
        )
    if broker_snapshot_refresh_callback is not None:
        _broker_snapshot_refresh_callback = broker_snapshot_refresh_callback
    if persist_fast_state_callback is not None:
        _persist_fast_state_callback = persist_fast_state_callback
    if finalize_fast_state_callback is not None:
        _finalize_fast_state_callback = finalize_fast_state_callback


def _log_holding_pipeline_impl(
    name,
    code,
    target_id,
    stage,
    *,
    candidate_stock=None,
    observed_at=None,
    observe_candidate_lifecycle=True,
    **fields,
):
    lifecycle_stage_mapped = pipeline_lifecycle_stage_mapped(
        pipeline="HOLDING_PIPELINE",
        source_stage=stage,
    )
    for field_name in _MAIN_LIFECYCLE_GENERATED_PIPELINE_FIELDS:
        if field_name != "attempt_id" or lifecycle_stage_mapped:
            fields.pop(field_name, None)
    if isinstance(candidate_stock, dict):
        trusted_observed_at = observed_at
        if isinstance(trusted_observed_at, datetime):
            if trusted_observed_at.tzinfo is None:
                trusted_observed_at = trusted_observed_at.replace(tzinfo=_KST)
            else:
                trusted_observed_at = trusted_observed_at.astimezone(_KST)
        identity_stock = dict(candidate_stock)
        identity_stock.setdefault("id", target_id)
        identity_stock.setdefault("code", code)
        fields.update(
            pipeline_lifecycle_fields_safe(
                identity_stock,
                code,
                pipeline="HOLDING_PIPELINE",
                source_stage=stage,
                source_fields=fields,
                observed_at=trusted_observed_at,
            )
        )
        if observe_candidate_lifecycle:
            observe_candidate_transition_safe(candidate_stock, code, stage, fields)
    emit_pipeline_event(
        "HOLDING_PIPELINE",
        name,
        code,
        stage,
        record_id=target_id,
        fields=fields,
    )


def _log_holding_pipeline(*args, **kwargs):
    """Keep receipt custody independent from optional telemetry failures."""

    try:
        return _log_holding_pipeline_impl(*args, **kwargs)
    except Exception as exc:
        stage = args[3] if len(args) > 3 else kwargs.get("stage", "-")
        code = args[1] if len(args) > 1 else kwargs.get("code", "-")
        log_error(
            f"[HOLDING_PIPELINE_RECEIPT_LOG_FAILED] code={code or '-'} "
            f"stage={stage or '-'}: {exc}"
        )
        return None


def _trailing_continuation_receipt_fields(stock: dict[str, Any]) -> dict[str, Any]:
    """Carry the exact recheck lineage into the terminal broker receipt."""
    return {
        "trailing_continuation_recheck_id": str(
            stock.get("scalp_trailing_continuation_recheck_consumed_id") or "-"
        ),
        "trailing_continuation_position_key": str(
            stock.get("scalp_trailing_continuation_recheck_consumed_position_key")
            or "-"
        ),
    }


def _main_lifecycle_exit_economics_fields(
    stock: dict[str, Any],
    *,
    buy_price: float,
    sell_price: float,
    sell_qty: int,
    realized_net_pnl_krw: float,
    decision_price: float | None = None,
    decision_basis_source: str | None = None,
) -> dict[str, Any]:
    """Return receipt-derived economics without inventing a slippage basis."""

    if buy_price <= 0 or sell_price <= 0 or sell_qty <= 0:
        return {}
    gross_pnl_krw = (sell_price - buy_price) * sell_qty
    fields = {
        "main_lifecycle_realized_net_pnl_krw": round(realized_net_pnl_krw, 4),
    }
    implied_fees_taxes_krw = gross_pnl_krw - realized_net_pnl_krw
    if implied_fees_taxes_krw >= -0.01:
        fields["main_lifecycle_fees_taxes_krw"] = round(
            max(0.0, implied_fees_taxes_krw), 4
        )
    resolved_decision_price = _safe_float(decision_price, 0.0)
    resolved_basis_source = str(decision_basis_source or "").strip()
    if decision_price is None:
        for field_name in (
            "fast_exit_decision_executable_sell_price",
            "exit_decision_executable_sell_price",
        ):
            candidate = _safe_float(stock.get(field_name), 0.0)
            if candidate > 0:
                resolved_decision_price = candidate
                resolved_basis_source = field_name
                break
    if resolved_decision_price > 0:
        fields["main_lifecycle_slippage_krw"] = round(
            max(0.0, (resolved_decision_price - sell_price) * sell_qty), 4
        )
        fields["main_lifecycle_slippage_basis_price"] = round(
            resolved_decision_price, 4
        )
        fields["main_lifecycle_slippage_basis_source"] = (
            resolved_basis_source or "explicit_exit_decision_price"
        )
    return fields


def _resolve_sell_execution_receipt(
    target_stock: dict[str, Any],
    *,
    order_no: str,
    exec_price: int,
    cumulative_exec_qty: int,
    expected_position_qty: int,
    buy_price: float,
    order_qty: int | None,
    remaining_qty: int | None,
    cumulative_exec_amount: int | None,
    execution_no: str,
    unit_exec_price: int | None,
    unit_exec_qty: int | None,
) -> dict[str, Any]:
    """Reconcile one Kiwoom 00 SELL receipt without treating it as final early.

    FID 911 is the order's cumulative fill quantity in observed packets.  FIDs
    900/902 provide the exact order/remaining quantity pair and FID 903 provides
    cumulative fill notional.  Runtime completion is allowed only when the
    cumulative quantity closes the full tracked position; partial receipts stay
    in ``SELL_ORDERED`` and remain broker-receipt observations only.
    """

    normalized_order_no = str(order_no or "").strip()
    if not normalized_order_no:
        return {"status": "invalid", "reason": "sell_receipt_order_number_missing"}
    raw_cumulative_qty = max(0, int(cumulative_exec_qty or 0))
    tracked_position_qty = max(0, int(expected_position_qty or 0))
    official_order_qty = max(0, int(order_qty or 0)) if order_qty is not None else 0
    if raw_cumulative_qty <= 0 or tracked_position_qty <= 0:
        return {"status": "invalid", "reason": "sell_receipt_quantity_missing"}

    raw_state = target_stock.get(_SELL_EXECUTION_RECEIPT_STATE_KEY)
    state = dict(raw_state) if isinstance(raw_state, dict) else {}
    state_position_qty = max(
        0, _safe_int(state.get("position_qty", state.get("expected_qty")), 0)
    )
    if state_position_qty > 0 and state_position_qty != tracked_position_qty:
        return {
            "status": "invalid",
            "reason": "sell_receipt_position_quantity_changed",
        }
    position_qty = state_position_qty or tracked_position_qty
    carried_qty = max(0, _safe_int(state.get("carried_qty"), 0))
    carried_amount = max(0, _safe_int(state.get("carried_amount"), 0))
    carried_net_pnl = _safe_float(state.get("carried_net_pnl_krw"), 0.0)
    carried_economics_complete = bool(state.get("carried_economics_complete", True))
    carried_quantity_contract_complete = bool(
        state.get("carried_quantity_contract_complete", True)
    )
    carried_unit_fill_consistent = bool(state.get("carried_unit_fill_consistent", True))
    prior_orders = state.get("prior_orders")
    prior_orders = dict(prior_orders) if isinstance(prior_orders, dict) else {}
    prior_order = prior_orders.get(normalized_order_no)
    if isinstance(prior_order, dict):
        prior_expected_qty = max(0, _safe_int(prior_order.get("expected_qty"), 0))
        prior_qty = max(0, _safe_int(prior_order.get("cumulative_qty"), 0))
        prior_amount = max(0, _safe_int(prior_order.get("cumulative_amount"), 0))
        prior_remaining = max(0, _safe_int(prior_order.get("remaining_qty"), 0))
        prior_executions = prior_order.get("executions_by_no")
        prior_executions = (
            dict(prior_executions) if isinstance(prior_executions, dict) else {}
        )
        signature = _execution_receipt_signature(
            cumulative_qty=raw_cumulative_qty,
            order_qty=order_qty,
            remaining_qty=remaining_qty,
            cumulative_exec_amount=cumulative_exec_amount,
            unit_exec_price=unit_exec_price,
            unit_exec_qty=unit_exec_qty,
        )
        conflict = _execution_number_conflict_reason(
            {normalized_order_no: prior_executions},
            order_key=normalized_order_no,
            execution_no=execution_no,
            signature=signature,
        )
        if conflict:
            return {"status": "invalid", "reason": conflict}
        delayed = _resolve_cumulative_buy_order_receipt(
            raw_price=exec_price,
            raw_cumulative_qty=raw_cumulative_qty,
            requested_qty=prior_expected_qty,
            previous_qty=prior_qty,
            previous_amount=prior_amount,
            previous_economics_complete=bool(
                prior_order.get("economics_complete", True)
            ),
            order_qty=order_qty,
            remaining_qty=remaining_qty,
            cumulative_exec_amount=cumulative_exec_amount,
            unit_exec_price=unit_exec_price,
            unit_exec_qty=unit_exec_qty,
        )
        if delayed.get("status") == "invalid":
            return {
                **delayed,
                "reason": str(delayed.get("reason") or "").replace(
                    "buy_receipt_", "sell_receipt_terminal_order_", 1
                ),
            }
        if delayed.get("status") == "duplicate":
            return {
                "status": "duplicate",
                "reason": "sell_receipt_terminal_order_duplicate",
                "final": False,
            }

        holder = {normalized_order_no: prior_executions}
        _remember_execution_number(
            holder,
            order_key=normalized_order_no,
            execution_no=execution_no,
            signature=signature,
        )
        updated_prior = dict(prior_order)
        updated_prior.update(
            {
                "expected_qty": max(
                    0, _safe_int(delayed.get("requested_qty"), prior_expected_qty)
                ),
                "cumulative_qty": max(0, _safe_int(delayed.get("cumulative_qty"), 0)),
                "cumulative_amount": max(
                    0, _safe_int(delayed.get("cumulative_amount"), 0)
                ),
                "remaining_qty": max(
                    0, _safe_int(delayed.get("remaining_qty"), prior_remaining)
                ),
                "economics_complete": delayed.get("economics_complete") is True,
                "quantity_contract_complete": (
                    delayed.get("quantity_contract_complete") is True
                ),
                "unit_fill_consistent": (
                    bool(prior_order.get("unit_fill_consistent", True))
                    and delayed.get("unit_fill_consistent") is True
                ),
                "executions_by_no": holder[normalized_order_no],
            }
        )
        prior_orders[normalized_order_no] = updated_prior
        updated_carried_qty = sum(
            max(0, _safe_int(item.get("cumulative_qty"), 0))
            for item in prior_orders.values()
            if isinstance(item, dict)
        )
        updated_carried_amount = sum(
            max(0, _safe_int(item.get("cumulative_amount"), 0))
            for item in prior_orders.values()
            if isinstance(item, dict)
        )
        active_qty = max(0, _safe_int(state.get("cumulative_qty"), 0))
        active_amount = max(0, _safe_int(state.get("cumulative_amount"), 0))
        aggregate_qty = updated_carried_qty + active_qty
        aggregate_amount = updated_carried_amount + active_amount
        if aggregate_qty > position_qty:
            return {
                "status": "invalid",
                "reason": "sell_receipt_terminal_order_aggregate_exceeds_position",
            }
        aggregate_net_pnl = calculate_net_realized_pnl(
            buy_price,
            aggregate_amount / aggregate_qty,
            aggregate_qty,
        )
        carried_net_pnl = calculate_net_realized_pnl(
            buy_price,
            updated_carried_amount / updated_carried_qty,
            updated_carried_qty,
        )
        state_order_no = str(state.get("order_no") or "").strip()
        replacement_reconciliation_required = bool(
            state_order_no
            and state_order_no != normalized_order_no
            and int(delayed.get("incremental_qty") or 0) > 0
        )
        final = bool(
            not state_order_no
            and aggregate_qty == position_qty
            and delayed.get("final") is True
        )
        state.update(
            {
                "prior_orders": prior_orders,
                "carried_qty": updated_carried_qty,
                "carried_amount": updated_carried_amount,
                "carried_net_pnl_krw": round(carried_net_pnl, 4),
                "carried_economics_complete": all(
                    isinstance(item, dict) and item.get("economics_complete") is True
                    for item in prior_orders.values()
                ),
                "carried_quantity_contract_complete": all(
                    isinstance(item, dict)
                    and item.get("quantity_contract_complete") is True
                    for item in prior_orders.values()
                ),
                "carried_unit_fill_consistent": all(
                    isinstance(item, dict) and item.get("unit_fill_consistent") is True
                    for item in prior_orders.values()
                ),
                "aggregate_cumulative_qty": aggregate_qty,
                "aggregate_cumulative_amount": aggregate_amount,
                "cumulative_net_pnl_krw": round(aggregate_net_pnl, 4),
                "remaining_qty": max(0, position_qty - aggregate_qty),
                "final": final,
                "replacement_reconciliation_required": (
                    replacement_reconciliation_required
                ),
                "replacement_order_no": (
                    state_order_no if replacement_reconciliation_required else ""
                ),
                "replacement_invalidated_by_late_order_no": (
                    normalized_order_no if replacement_reconciliation_required else ""
                ),
            }
        )
        target_stock[_SELL_EXECUTION_RECEIPT_STATE_KEY] = state
        previous_aggregate_qty = aggregate_qty - int(delayed["incremental_qty"])
        previous_aggregate_amount = aggregate_amount - int(
            delayed["incremental_amount"]
        )
        previous_net_pnl = (
            calculate_net_realized_pnl(
                buy_price,
                previous_aggregate_amount / previous_aggregate_qty,
                previous_aggregate_qty,
            )
            if previous_aggregate_qty > 0 and previous_aggregate_amount > 0
            else 0.0
        )
        return {
            "status": (
                "replacement_reconcile_required"
                if replacement_reconciliation_required
                else ("final" if final else "partial")
            ),
            "reason": (
                "sell_receipt_terminal_order_late_final"
                if final
                else "sell_receipt_terminal_order_late_fill"
            ),
            "final": final,
            "order_no": normalized_order_no,
            "execution_no": str(execution_no or "").strip(),
            "expected_qty": position_qty,
            "order_expected_qty": prior_expected_qty,
            "remaining_qty": max(0, position_qty - aggregate_qty),
            "order_cumulative_qty": int(delayed["cumulative_qty"]),
            "order_cumulative_amount": int(delayed["cumulative_amount"]),
            "cumulative_qty": aggregate_qty,
            "cumulative_amount": aggregate_amount,
            "cumulative_avg_price": aggregate_amount / aggregate_qty,
            "cumulative_net_pnl_krw": round(aggregate_net_pnl, 4),
            "incremental_qty": int(delayed["incremental_qty"]),
            "incremental_amount": int(delayed["incremental_amount"]),
            "incremental_price": float(delayed["incremental_price"]),
            "incremental_net_pnl_krw": round(aggregate_net_pnl - previous_net_pnl, 4),
            "economics_complete": bool(
                state.get("carried_economics_complete")
                and state.get("economics_complete", True)
            ),
            "quantity_contract_complete": bool(
                state.get("carried_quantity_contract_complete")
                and state.get("quantity_contract_complete", True)
            ),
            "unit_fill_consistent": bool(
                state.get("carried_unit_fill_consistent")
                and state.get("unit_fill_consistent", True)
            ),
            "unit_exec_qty": unit_exec_qty,
            "unit_exec_price": unit_exec_price,
            "unit_qty_matches_delta": delayed.get("unit_qty_matches_delta"),
            "unit_price_matches_delta": delayed.get("unit_price_matches_delta"),
        }

    state_order_no = str(state.get("order_no") or "")
    if state_order_no and state_order_no != normalized_order_no:
        return {
            "status": "invalid",
            "reason": "sell_receipt_order_changed_before_reconciliation",
        }
    expected_active_qty = max(0, position_qty - carried_qty)
    state_expected_active_qty = max(0, _safe_int(state.get("expected_qty"), 0))
    if state_order_no and state_expected_active_qty > 0:
        if state_expected_active_qty != expected_active_qty:
            return {
                "status": "invalid",
                "reason": "sell_receipt_active_order_quantity_changed",
            }
        expected_active_qty = state_expected_active_qty
    if official_order_qty > 0 and official_order_qty != expected_active_qty:
        return {
            "status": "invalid",
            "reason": "sell_receipt_order_position_quantity_mismatch",
        }
    if raw_cumulative_qty > expected_active_qty:
        return {
            "status": "invalid",
            "reason": "sell_receipt_cumulative_quantity_exceeds_position",
        }
    executions = state.get("executions_by_no")
    executions = dict(executions) if isinstance(executions, dict) else {}
    signature = _execution_receipt_signature(
        cumulative_qty=raw_cumulative_qty,
        order_qty=order_qty,
        remaining_qty=remaining_qty,
        cumulative_exec_amount=cumulative_exec_amount,
        unit_exec_price=unit_exec_price,
        unit_exec_qty=unit_exec_qty,
    )
    conflict = _execution_number_conflict_reason(
        {normalized_order_no: executions},
        order_key=normalized_order_no,
        execution_no=execution_no,
        signature=signature,
    )
    if conflict:
        return {"status": "invalid", "reason": conflict}
    official_remaining_qty = (
        max(0, int(remaining_qty)) if remaining_qty is not None else None
    )
    if (
        official_remaining_qty is not None
        and raw_cumulative_qty + official_remaining_qty != expected_active_qty
    ):
        return {
            "status": "invalid",
            "reason": "sell_receipt_remaining_quantity_conflict",
        }

    previous_qty = max(0, _safe_int(state.get("cumulative_qty"), 0))
    previous_amount = max(0, _safe_int(state.get("cumulative_amount"), 0))
    previous_aggregate_qty = carried_qty + previous_qty
    previous_aggregate_amount = carried_amount + previous_amount
    previous_aggregate_net_pnl = (
        calculate_net_realized_pnl(
            buy_price,
            previous_aggregate_amount / previous_aggregate_qty,
            previous_aggregate_qty,
        )
        if previous_aggregate_qty > 0 and previous_aggregate_amount > 0
        else carried_net_pnl
    )
    if raw_cumulative_qty < previous_qty:
        return {
            "status": "invalid",
            "reason": "sell_receipt_cumulative_quantity_regressed",
        }
    incremental_qty = raw_cumulative_qty - previous_qty
    if incremental_qty <= 0:
        if (
            cumulative_exec_amount is not None
            and max(0, int(cumulative_exec_amount)) != previous_amount
        ):
            return {
                "status": "invalid",
                "reason": "sell_receipt_duplicate_quantity_amount_conflict",
            }
        if (
            official_remaining_qty is not None
            and official_remaining_qty != expected_active_qty - previous_qty
        ):
            return {
                "status": "invalid",
                "reason": "sell_receipt_duplicate_quantity_remaining_conflict",
            }
        return {
            "status": "duplicate",
            "reason": "sell_receipt_duplicate_cumulative_quantity",
            "final": bool(state.get("final")),
        }

    official_cumulative_amount = (
        max(0, int(cumulative_exec_amount))
        if cumulative_exec_amount is not None
        else None
    )
    economics_complete = bool(
        state.get("economics_complete", True) and carried_economics_complete
    )
    if official_cumulative_amount is not None:
        if official_cumulative_amount <= previous_amount:
            return {
                "status": "invalid",
                "reason": "sell_receipt_cumulative_amount_not_increasing",
            }
        incremental_amount = official_cumulative_amount - previous_amount
        cumulative_amount = official_cumulative_amount
    else:
        resolved_price = max(0, int(unit_exec_price or exec_price or 0))
        if resolved_price <= 0:
            return {
                "status": "invalid",
                "reason": "sell_receipt_incremental_price_missing",
            }
        incremental_amount = resolved_price * incremental_qty
        cumulative_amount = previous_amount + incremental_amount
        # Quantity can still close custody safely, but missing FID 903 cannot
        # support exact multi-fill economics or R0 promotion evidence.
        economics_complete = False
    if incremental_amount <= 0:
        return {
            "status": "invalid",
            "reason": "sell_receipt_incremental_amount_invalid",
        }
    incremental_price = incremental_amount / incremental_qty
    aggregate_qty = carried_qty + raw_cumulative_qty
    aggregate_amount = carried_amount + cumulative_amount
    aggregate_net_pnl = calculate_net_realized_pnl(
        buy_price,
        aggregate_amount / aggregate_qty,
        aggregate_qty,
    )
    incremental_net_pnl = aggregate_net_pnl - previous_aggregate_net_pnl
    unit_qty_matches_delta = (
        None if unit_exec_qty is None else int(unit_exec_qty) == incremental_qty
    )
    unit_price_matches_delta = (
        None
        if unit_exec_price is None
        else int(unit_exec_price) * incremental_qty == incremental_amount
    )
    unit_fill_consistent = bool(
        carried_unit_fill_consistent
        and unit_qty_matches_delta is True
        and unit_price_matches_delta is True
    )
    quantity_contract_complete = bool(
        carried_quantity_contract_complete
        and official_order_qty > 0
        and official_remaining_qty is not None
    )
    final = bool(
        aggregate_qty == position_qty
        and raw_cumulative_qty == expected_active_qty
        and official_remaining_qty == 0
    )
    state = {
        "order_no": normalized_order_no,
        "position_qty": position_qty,
        "expected_qty": expected_active_qty,
        "cumulative_qty": raw_cumulative_qty,
        "remaining_qty": position_qty - aggregate_qty,
        "cumulative_amount": cumulative_amount,
        "cumulative_net_pnl_krw": round(aggregate_net_pnl, 4),
        "aggregate_cumulative_qty": aggregate_qty,
        "aggregate_cumulative_amount": aggregate_amount,
        "carried_qty": carried_qty,
        "carried_amount": carried_amount,
        "carried_net_pnl_krw": round(carried_net_pnl, 4),
        "carried_economics_complete": carried_economics_complete,
        "carried_quantity_contract_complete": (carried_quantity_contract_complete),
        "carried_unit_fill_consistent": carried_unit_fill_consistent,
        "prior_orders": prior_orders,
        "economics_complete": economics_complete,
        "quantity_contract_complete": quantity_contract_complete,
        "unit_fill_consistent": unit_fill_consistent,
        "final": final,
        "last_execution_no": str(execution_no or "").strip(),
    }
    holder = {normalized_order_no: executions}
    _remember_execution_number(
        holder,
        order_key=normalized_order_no,
        execution_no=execution_no,
        signature=signature,
    )
    state["executions_by_no"] = holder[normalized_order_no]
    target_stock[_SELL_EXECUTION_RECEIPT_STATE_KEY] = state
    return {
        "status": "final" if final else "partial",
        "reason": "sell_receipt_full_position_reconciled"
        if final
        else "sell_receipt_partial_fill",
        "final": final,
        "order_no": normalized_order_no,
        "execution_no": str(execution_no or "").strip(),
        "expected_qty": position_qty,
        "order_expected_qty": expected_active_qty,
        "remaining_qty": (
            official_remaining_qty
            if official_remaining_qty is not None
            else position_qty - aggregate_qty
        ),
        "order_cumulative_qty": raw_cumulative_qty,
        "order_cumulative_amount": cumulative_amount,
        "cumulative_qty": aggregate_qty,
        "cumulative_amount": aggregate_amount,
        "cumulative_avg_price": aggregate_amount / aggregate_qty,
        "cumulative_net_pnl_krw": round(aggregate_net_pnl, 4),
        "incremental_qty": incremental_qty,
        "incremental_amount": incremental_amount,
        "incremental_price": incremental_price,
        "incremental_net_pnl_krw": round(incremental_net_pnl, 4),
        "economics_complete": economics_complete,
        "quantity_contract_complete": quantity_contract_complete,
        "unit_fill_consistent": unit_fill_consistent,
        "unit_exec_qty": unit_exec_qty,
        "unit_exec_price": unit_exec_price,
        "unit_qty_matches_delta": unit_qty_matches_delta,
        "unit_price_matches_delta": unit_price_matches_delta,
    }


def _log_standard_sell_partial_execution(
    target_stock: dict[str, Any],
    *,
    code: str,
    target_id: int,
    now: datetime,
    receipt: dict[str, Any],
    buy_price: float,
) -> None:
    reconciled_remaining_qty = max(0, int(receipt.get("remaining_qty") or 0))
    target_stock["buy_qty"] = reconciled_remaining_qty
    target_stock["sell_reconciled_remaining_qty"] = reconciled_remaining_qty
    target_stock["scale_in_locked"] = True
    target_stock["sell_partial_exit_carry_active"] = True
    try:
        with DB.get_session() as session:
            session.query(RecommendationHistory).filter_by(id=target_id).update(
                {"scale_in_locked": True}
            )
    except Exception as exc:
        log_error(
            f"[SELL_PARTIAL_GUARD_PERSIST_FAILED] "
            f"{target_stock.get('name')}({code}) id={target_id}: {exc}"
        )
    _persist_sell_receipt_recovery_or_interlock(
        target_stock,
        code=code,
        reason="standard_partial_sell_receipt",
    )
    economics_fields: dict[str, Any] = {}
    if receipt.get("economics_complete") is True:
        economics_fields = _main_lifecycle_exit_economics_fields(
            target_stock,
            buy_price=buy_price,
            sell_price=float(receipt["incremental_price"]),
            sell_qty=int(receipt["incremental_qty"]),
            realized_net_pnl_krw=float(receipt["incremental_net_pnl_krw"]),
        )
    _log_holding_pipeline(
        target_stock.get("name"),
        code,
        target_id,
        "sell_partial_fill_progress",
        candidate_stock=target_stock,
        observed_at=now,
        observe_candidate_lifecycle=False,
        order_no=receipt.get("order_no") or "-",
        execution_no=receipt.get("execution_no") or "-",
        sell_price=round(float(receipt["incremental_price"]), 4),
        sell_qty=int(receipt["incremental_qty"]),
        cumulative_sell_qty=int(receipt["cumulative_qty"]),
        remaining_sell_qty=int(receipt["remaining_qty"]),
        main_lifecycle_exit_qty=int(receipt["incremental_qty"]),
        main_lifecycle_exit_price=round(float(receipt["incremental_price"]), 4),
        main_lifecycle_broker_reconciled=False,
        main_lifecycle_reconciled_final_exit=False,
        sell_receipt_economics_complete=bool(receipt.get("economics_complete")),
        sell_receipt_quantity_contract_complete=bool(
            receipt.get("quantity_contract_complete")
        ),
        sell_receipt_unit_fill_consistent=bool(
            receipt.get("unit_fill_consistent", True)
        ),
        sell_receipt_unit_qty_matches_delta=receipt.get("unit_qty_matches_delta"),
        actual_order_submitted=True,
        broker_order_forbidden=False,
        runtime_effect=True,
        **_broker_execution_provenance_fields(target_stock),
        **economics_fields,
    )


def _run_probe_fill_continuation(target_stock: dict[str, Any], code: str) -> None:
    callback = _probe_fill_continuation_callback
    if callback is None:
        return
    try:
        callback(target_stock, code)
    except Exception as exc:
        log_error(
            f"[PROBE_RESIDUAL_IMMEDIATE] {target_stock.get('name')}({code}) "
            f"failed={exc}"
        )


def _request_broker_snapshot_refresh(code: str, *, reason: str) -> None:
    callback = _broker_snapshot_refresh_callback
    if callback is None:
        return
    try:
        callback(code=str(code or "").strip()[:6], reason=str(reason or "execution"))
    except Exception as exc:
        log_error(
            f"[BROKER_SNAPSHOT_REFRESH_REQUEST] code={str(code or '').strip()[:6] or '-'} "
            f"reason={reason or '-'} failed={exc}"
        )


def _receipt_snapshot(
    target_stock: dict[str, Any], keys: tuple[str, ...]
) -> dict[str, Any]:
    return {key: target_stock.get(key) for key in keys}


def _broker_execution_provenance_fields(
    target_stock: dict[str, Any],
) -> dict[str, Any]:
    return {
        key: target_stock.get(key)
        for key in _BROKER_EXECUTION_PROVENANCE_KEYS
        if key in target_stock
    }


def _sell_receipt_recovery_path(target_id: Any) -> Path | None:
    try:
        normalized_id = int(target_id)
    except (TypeError, ValueError):
        return None
    if normalized_id <= 0:
        return None
    return SELL_RECEIPT_RECOVERY_DIR / f"{normalized_id}.json"


def prune_sell_receipt_recovery_files(
    *,
    now_epoch: float | None = None,
    force: bool = False,
    active_target_ids: set[int] | None = None,
) -> None:
    """Bound abandoned exact journals and crash-left atomic temp files."""

    global _SELL_RECEIPT_RECOVERY_LAST_PRUNE_AT
    current_epoch = time.time() if now_epoch is None else float(now_epoch)
    if (
        not force
        and current_epoch - _SELL_RECEIPT_RECOVERY_LAST_PRUNE_AT
        < _SELL_RECEIPT_RECOVERY_PRUNE_INTERVAL_SEC
    ):
        return
    _SELL_RECEIPT_RECOVERY_LAST_PRUNE_AT = current_epoch
    protected_target_ids = {
        int(value) for value in (active_target_ids or set()) if _safe_int(value, 0) > 0
    }
    try:
        candidates = list(SELL_RECEIPT_RECOVERY_DIR.iterdir())
    except Exception:
        return
    for candidate in candidates:
        try:
            if candidate.is_symlink() or not candidate.is_file():
                continue
            name = candidate.name
            is_journal = bool(re.fullmatch(r"[1-9]\d*\.json", name))
            is_atomic_temp = bool(
                re.fullmatch(r"\.[1-9]\d*\.json\.\d+\.\d+\.tmp", name)
            )
            if not (is_journal or is_atomic_temp):
                continue
            if is_journal:
                journal_target_id = _safe_int(name.removesuffix(".json"), 0)
                if journal_target_id in protected_target_ids:
                    continue
                retention_sec = _SELL_RECEIPT_RECOVERY_ORPHAN_MAX_AGE_SEC
            else:
                retention_sec = _SELL_RECEIPT_RECOVERY_MAX_AGE_SEC + 300
            if current_epoch - candidate.stat().st_mtime <= retention_sec:
                continue
            candidate.unlink(missing_ok=True)
        except Exception:
            continue


def persist_sell_receipt_recovery(target_stock: dict[str, Any]) -> bool:
    """Atomically journal one active partial SELL ledger for restart recovery."""

    path = _sell_receipt_recovery_path(target_stock.get("id"))
    state = target_stock.get(_SELL_EXECUTION_RECEIPT_STATE_KEY)
    final_pending_db_commit = bool(
        isinstance(state, dict) and state.get("final_pending_db_commit") is True
    )
    if (
        path is None
        or not isinstance(state, dict)
        or (state.get("final") is True and not final_pending_db_commit)
    ):
        return False
    position_qty = max(0, _safe_int(state.get("position_qty"), 0))
    aggregate_qty = max(
        0,
        _safe_int(
            state.get("aggregate_cumulative_qty"),
            _safe_int(state.get("carried_qty"), 0)
            + _safe_int(state.get("cumulative_qty"), 0),
        ),
    )
    code = str(target_stock.get("code") or "").strip()[:6]
    aggregate_valid = (
        aggregate_qty == position_qty
        if final_pending_db_commit
        else 0 < aggregate_qty < position_qty
    )
    if not code or position_qty <= 0 or not aggregate_valid:
        return False
    payload = {
        "schema": _SELL_RECEIPT_RECOVERY_SCHEMA,
        "target_id": int(target_stock["id"]),
        "code": code,
        "position_qty": position_qty,
        "buy_price": _safe_float(target_stock.get("buy_price"), 0.0),
        "updated_at_epoch": time.time(),
        "updated_at_kst": datetime.now(_KST).isoformat(),
        "receipt_state": state,
    }
    canonical = json.dumps(
        payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    )
    if len(canonical.encode("utf-8")) > _SELL_RECEIPT_RECOVERY_MAX_BYTES:
        log_error(
            f"[SELL_RECEIPT_RECOVERY_PERSIST_BLOCKED] {code} "
            "reason=journal_size_limit_exceeded"
        )
        return False
    document = {
        "payload": payload,
        "payload_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
    }
    encoded = json.dumps(
        document, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    temp_path = path.with_name(
        f".{path.name}.{os.getpid()}.{threading.get_ident()}.tmp"
    )
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.parent.is_symlink() or path.is_symlink():
            raise RuntimeError("sell_receipt_recovery_symlink_forbidden")
        prune_sell_receipt_recovery_files(
            now_epoch=float(payload["updated_at_epoch"]),
            active_target_ids={
                _safe_int(item.get("id"), 0)
                for item in (ACTIVE_TARGETS or [])
                if isinstance(item, dict) and _safe_int(item.get("id"), 0) > 0
            }
            | {int(target_stock["id"])},
        )
        with temp_path.open("xb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
        return True
    except Exception as exc:
        log_error(
            f"[SELL_RECEIPT_RECOVERY_PERSIST_FAILED] {code} "
            f"id={target_stock.get('id')}: {exc}"
        )
        try:
            temp_path.unlink(missing_ok=True)
        except Exception:
            pass
        return False


def _persist_sell_receipt_recovery_or_interlock(
    target_stock: dict[str, Any], *, code: str, reason: str
) -> bool:
    """Persist custody state or prevent every follow-up order mutation."""

    if persist_sell_receipt_recovery(target_stock):
        target_stock.pop("sell_receipt_durability_blocked", None)
        target_stock.pop("sell_receipt_durability_reason", None)
        return True
    target_stock.update(
        {
            "scale_in_locked": True,
            "sell_partial_exit_recovery_required": True,
            "sell_cancel_reconciliation_required": True,
            "sell_cancel_reconciliation_source": (
                f"sell_receipt_durability_failed:{reason}"
            ),
            "sell_receipt_durability_blocked": True,
            "sell_receipt_durability_reason": reason,
        }
    )
    log_error(
        f"[SELL_RECEIPT_DURABILITY_BLOCKED] "
        f"{target_stock.get('name', code)}({code}) id={target_stock.get('id')} "
        f"reason={reason}; replacement/retry/scale-in remain blocked"
    )
    _request_broker_snapshot_refresh(
        code,
        reason=f"sell_receipt_durability_failed:{reason}",
    )
    return False


def load_sell_receipt_recovery(
    *,
    target_id: Any,
    code: str,
    position_qty: int,
    broker_remaining_qty: int,
    now_epoch: float | None = None,
) -> tuple[dict[str, Any] | None, str]:
    """Load a checksum-verified same-cycle ledger matching broker inventory."""

    path = _sell_receipt_recovery_path(target_id)
    if path is None or not path.exists() or not path.is_file() or path.is_symlink():
        return None, "journal_missing"
    try:
        raw = path.read_bytes()
        if len(raw) > _SELL_RECEIPT_RECOVERY_MAX_BYTES:
            return None, "journal_size_limit_exceeded"
        document = json.loads(raw.decode("utf-8"))
        payload = document.get("payload") if isinstance(document, dict) else None
        if not isinstance(payload, dict):
            return None, "journal_payload_invalid"
        canonical = json.dumps(
            payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")
        )
        expected_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        if str(document.get("payload_sha256") or "") != expected_hash:
            return None, "journal_checksum_mismatch"
        if payload.get("schema") != _SELL_RECEIPT_RECOVERY_SCHEMA:
            return None, "journal_schema_mismatch"
        if int(payload.get("target_id") or 0) != int(target_id):
            return None, "journal_target_id_mismatch"
        if str(payload.get("code") or "").strip()[:6] != str(code or "").strip()[:6]:
            return None, "journal_code_mismatch"
        updated_at = float(payload.get("updated_at_epoch") or 0.0)
        current_epoch = time.time() if now_epoch is None else float(now_epoch)
        # Exact active-target journals are custody evidence, not a rolling
        # report cache.  Do not expire them across weekends, holidays, or an
        # extended outage; startup pruning receives the active target IDs and
        # removes only old orphan journals.
        if updated_at <= 0:
            return None, "journal_timestamp_missing"
        if updated_at - current_epoch > 300:
            return None, "journal_future_timestamp"
        state = payload.get("receipt_state")
        final_pending_db_commit = bool(
            isinstance(state, dict) and state.get("final_pending_db_commit") is True
        )
        if not isinstance(state, dict) or (
            state.get("final") is True and not final_pending_db_commit
        ):
            return None, "journal_receipt_state_invalid"
        expected_position_qty = max(0, int(position_qty or 0))
        if (
            max(0, _safe_int(payload.get("position_qty"), 0)) != expected_position_qty
            or max(0, _safe_int(state.get("position_qty"), 0)) != expected_position_qty
        ):
            return None, "journal_position_quantity_mismatch"
        aggregate_qty = max(
            0,
            _safe_int(
                state.get("aggregate_cumulative_qty"),
                _safe_int(state.get("carried_qty"), 0)
                + _safe_int(state.get("cumulative_qty"), 0),
            ),
        )
        if expected_position_qty - aggregate_qty != max(
            0, int(broker_remaining_qty or 0)
        ):
            return None, "journal_broker_remaining_quantity_mismatch"
        return dict(state), "journal_exact_match"
    except Exception as exc:
        return None, f"journal_read_failed:{type(exc).__name__}"


def clear_sell_receipt_recovery(target_id: Any) -> bool:
    path = _sell_receipt_recovery_path(target_id)
    if path is None:
        return False
    try:
        if path.is_symlink():
            raise RuntimeError("sell_receipt_recovery_symlink_forbidden")
        path.unlink(missing_ok=True)
        if path.parent.exists():
            directory_fd = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        return True
    except Exception as exc:
        log_error(f"[SELL_RECEIPT_RECOVERY_CLEAR_FAILED] id={target_id}: {exc}")
        return False


def reconcile_committed_sell_receipt_recovery_files() -> dict[str, int]:
    """Finish post-commit control-plane cleanup after a process crash.

    A final receipt is journaled before the DB transaction.  If the process
    dies after that transaction commits but before the same-symbol re-entry
    callback and journal unlink, the completed DB row is authoritative and no
    broker order may be replayed.  This startup pass performs only the missing
    callback/cleanup against checksum-bound receipt evidence.
    """

    result = {"scanned": 0, "reconciled": 0, "deferred": 0, "invalid": 0}
    if SELL_RECEIPT_RECOVERY_DIR.is_symlink():
        result["invalid"] += 1
        return result
    try:
        candidates = sorted(SELL_RECEIPT_RECOVERY_DIR.glob("*.json"))
    except Exception:
        result["deferred"] += 1
        return result
    for path in candidates:
        result["scanned"] += 1
        if path.is_symlink() or not path.is_file():
            result["invalid"] += 1
            continue
        try:
            raw = path.read_bytes()
            if len(raw) > _SELL_RECEIPT_RECOVERY_MAX_BYTES:
                raise ValueError("journal_size_limit_exceeded")
            document = json.loads(raw.decode("utf-8"))
            payload = document.get("payload") if isinstance(document, dict) else None
            if not isinstance(payload, dict):
                raise ValueError("journal_payload_invalid")
            canonical = json.dumps(
                payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")
            )
            if (
                str(document.get("payload_sha256") or "")
                != hashlib.sha256(canonical.encode("utf-8")).hexdigest()
            ):
                raise ValueError("journal_checksum_mismatch")
            state = payload.get("receipt_state")
            if (
                payload.get("schema") != _SELL_RECEIPT_RECOVERY_SCHEMA
                or not isinstance(state, dict)
                or state.get("final") is not True
                or state.get("final_pending_db_commit") is not True
            ):
                # Active partial journals remain owned by normal inventory
                # reconciliation and are intentionally not touched here.
                continue
            target_id = _safe_int(payload.get("target_id"), 0)
            code = str(payload.get("code") or "").strip()[:6]
            snapshot = state.get("finalization_receipt_snapshot")
            if target_id <= 0 or len(code) != 6 or not isinstance(snapshot, dict):
                raise ValueError("final_journal_identity_invalid")
            with DB.get_session() as session:
                record = (
                    session.query(RecommendationHistory).filter_by(id=target_id).first()
                )
                if (
                    not record
                    or str(record.status or "").strip().upper() != "COMPLETED"
                ):
                    result["deferred"] += 1
                    continue
                if not record.sell_time or _safe_float(record.sell_price, 0.0) <= 0:
                    result["deferred"] += 1
                    continue
                strategy = normalize_strategy(
                    state.get("finalization_strategy")
                    or getattr(record, "strategy", None)
                    or snapshot.get("strategy")
                    or "KOSPI_ML"
                )
                position_tag = normalize_position_tag(
                    strategy,
                    getattr(record, "position_tag", None)
                    or snapshot.get("position_tag"),
                )
                profit_rate = _safe_float(record.profit_rate, 0.0)
                sell_price = _safe_int(record.sell_price, 0)
            if strategy == "SCALPING":
                if not callable(_scalp_exit_completed_callback):
                    result["deferred"] += 1
                    continue
                try:
                    callback_result = _scalp_exit_completed_callback(
                        code,
                        profit_rate=profit_rate,
                        exit_price=sell_price,
                        exit_rule=snapshot.get("last_exit_rule") or "-",
                        completed_at=record.sell_time.timestamp(),
                        position_tag=position_tag,
                    )
                except Exception as exc:
                    result["deferred"] += 1
                    log_error(
                        f"[SELL_POSTCOMMIT_CALLBACK_DEFERRED] id={target_id}: {exc}"
                    )
                    continue
                if not isinstance(callback_result, dict) or (
                    callback_result.get("reconciled") is False
                    and callback_result.get("reason")
                    != "active_reentry_context_missing"
                ):
                    result["deferred"] += 1
                    continue
            if not clear_sell_receipt_recovery(target_id):
                result["deferred"] += 1
                continue
            result["reconciled"] += 1
        except Exception as exc:
            result["invalid"] += 1
            log_error(f"[SELL_POSTCOMMIT_RECOVERY_BLOCKED] path={path.name}: {exc}")
    return result


def _probe_residual_scale_in_receipt_fields(
    target_stock: dict[str, Any],
    *,
    now_ts: float,
) -> dict[str, Any]:
    """Join a later scale-in fill to the terminal probe-residual decision."""

    abort_reason = str(
        target_stock.get("entry_split_probe_terminal_abort_reason")
        or target_stock.get("entry_split_probe_abort_reason")
        or ""
    ).strip()
    terminal_at = _safe_float(target_stock.get("entry_split_probe_terminal_at"), 0.0)
    if not abort_reason and terminal_at <= 0:
        return {}
    return {
        "prior_probe_residual_bundle_id": (
            target_stock.get("entry_split_probe_bundle_id") or "-"
        ),
        "prior_probe_residual_outcome": (
            target_stock.get("entry_split_probe_terminal_outcome")
            or "residual_not_submitted"
        ),
        "prior_probe_residual_abort_reason": abort_reason or "-",
        "prior_probe_residual_abort_detail_reason": (
            target_stock.get("entry_split_probe_terminal_abort_detail_reason")
            or target_stock.get("entry_split_probe_abort_detail_reason")
            or "-"
        ),
        "prior_probe_residual_direction_state": (
            target_stock.get("entry_split_probe_terminal_direction_state") or "UNKNOWN"
        ),
        "prior_probe_residual_direction_reason": (
            target_stock.get("entry_split_probe_terminal_direction_reason") or "-"
        ),
        "prior_probe_residual_positive_groups": (
            target_stock.get("entry_split_probe_terminal_positive_groups") or "-"
        ),
        "prior_probe_residual_negative_groups": (
            target_stock.get("entry_split_probe_terminal_negative_groups") or "-"
        ),
        "prior_probe_residual_confirmation_count": max(
            0,
            _safe_int(
                target_stock.get("entry_split_probe_terminal_confirmation_count"),
                _safe_int(target_stock.get("probe_confirmation_count"), 0),
            ),
        ),
        "prior_probe_residual_confirmation_required_count": 2,
        "prior_probe_residual_observed_at": terminal_at or "-",
        "prior_probe_residual_age_ms": (
            round(max(0.0, (float(now_ts) - terminal_at) * 1000.0), 3)
            if terminal_at > 0
            else "-"
        ),
        "prior_probe_residual_failure_signature": (
            target_stock.get("entry_split_probe_terminal_failure_signature") or "-"
        ),
        "prior_probe_residual_scale_in_recheck_allowed": bool(
            target_stock.get("entry_split_probe_scale_in_recheck_allowed", False)
        ),
        "prior_probe_residual_scale_in_recheck_authority": (
            "evaluation_only_full_scale_in_guards_required"
        ),
        "prior_probe_residual_metric_role": "causal_attribution_dimension",
        "prior_probe_residual_decision_authority": "causal_attribution_only",
        "prior_probe_residual_window_policy": (
            "same_position_cycle_probe_terminal_to_scale_in"
        ),
        "prior_probe_residual_sample_floor": (
            "one_terminal_residual_decision_and_one_scale_in_evaluation"
        ),
        "prior_probe_residual_primary_decision_metric": (
            "source_quality_adjusted_ev_pct"
        ),
        "prior_probe_residual_source_quality_gate": (
            "exact_probe_bundle_terminal_snapshot_and_same_position_cycle"
        ),
        "prior_probe_residual_forbidden_uses": (
            "standalone_scale_in_submit|residual_guard_bypass|ai_guard_bypass|"
            "source_quality_bypass|account_order_quantity_cooldown_bypass"
        ),
    }


def _winner_recovery_ai_receipt_fields(
    target_stock: dict[str, Any],
) -> dict[str, Any]:
    """Freeze decision-time AI provenance before pending metadata is cleared."""

    if (
        str(target_stock.get("pending_add_reason") or "").strip()
        != "post_probe_winner_recovery_first_leg"
    ):
        return {}
    return {
        "post_probe_winner_recovery_ai_thesis_state": (
            target_stock.get("pending_add_winner_recovery_ai_thesis_state")
            or "unreported"
        ),
        "post_probe_winner_recovery_ai_parent_action": (
            target_stock.get("pending_add_winner_recovery_ai_parent_action")
            or "NOT_EVALUATED"
        ),
        "post_probe_winner_recovery_ai_parent_prompt_version": (
            target_stock.get("pending_add_winner_recovery_ai_parent_prompt_version")
            or "-"
        ),
        "post_probe_winner_recovery_ai_parent_trace_id": (
            target_stock.get("pending_add_winner_recovery_ai_parent_trace_id") or "-"
        ),
        "post_probe_winner_recovery_ai_parent_snapshot_id": (
            target_stock.get("pending_add_winner_recovery_ai_parent_snapshot_id")
            or "-"
        ),
        "post_probe_winner_recovery_holding_ai_action": (
            target_stock.get("pending_add_winner_recovery_holding_ai_action")
            or "NOT_EVALUATED"
        ),
        "post_probe_winner_recovery_holding_ai_data_quality": (
            target_stock.get("pending_add_winner_recovery_holding_ai_data_quality")
            or "insufficient"
        ),
        "post_probe_winner_recovery_holding_ai_input_schema": (
            target_stock.get("pending_add_winner_recovery_holding_ai_input_schema")
            or "-"
        ),
        "post_probe_winner_recovery_ai_tape_substitution_applied": bool(
            target_stock.get(
                "pending_add_winner_recovery_ai_tape_substitution_applied"
            )
        ),
    }


def _sell_completion_contract_fields(position_tag: str) -> dict[str, Any]:
    if position_tag == OPENING_ROTATION_POSITION_TAG:
        return {
            "trade_status": "COMPLETED",
            "metric_role": "exact_real_trade_performance_source",
            "decision_authority": "real_execution_observation_only",
            "window_policy": "clean_baseline_completed_trade_event_time",
            "sample_floor": "consumer_owned_no_direct_runtime_authority",
            "primary_decision_metric": "net_profit_rate_and_realized_pnl_krw",
            "source_quality_gate": (
                "completed_db_status_valid_net_profit_real_broker_receipt"
            ),
            "allowed_runtime_apply": False,
            "forbidden_uses": (
                "live_auto_promotion|runtime_apply_bridge|threshold_mutation|"
                "provider_change|order_price_change|quantity_cap_change|"
                "broker_guard_bypass"
            ),
        }
    return {
        "trade_status": "COMPLETED",
        "allowed_runtime_apply": False,
        "forbidden_uses": (
            "EV|rolling|MTD|live_auto_promotion|runtime_apply_bridge|"
            "threshold_mutation|provider_change|order_price_change|"
            "quantity_cap_change|broker_guard_bypass"
        ),
    }


def _resolve_entry_submit_ai_score(
    target_stock: dict[str, Any], order_no: str = ""
) -> float | None:
    """Return the BUY submit score that should seed first holding review state."""
    strategy = normalize_strategy(target_stock.get("strategy"))
    position_tag = normalize_position_tag(strategy, target_stock.get("position_tag"))
    if strategy == "SCALPING" and position_tag == OPENING_ROTATION_POSITION_TAG:
        return None
    pending_orders = target_stock.get("pending_entry_orders") or []
    if isinstance(pending_orders, list):
        for order in pending_orders:
            if not isinstance(order, dict):
                continue
            if (
                order_no
                and str(order.get("ord_no", "") or "").strip() != str(order_no).strip()
            ):
                continue
            score = _safe_float(order.get("ai_score"), 0.0)
            if score > 0:
                return score
    for key in (
        "entry_submit_ai_score",
        "entry_armed_ai_score",
        "last_watching_ai_score",
        "current_ai_score",
        "ai_score",
    ):
        score = _safe_float(target_stock.get(key), 0.0)
        if score > 0:
            return score
    return None


def _receipt_audience(snapshot: dict[str, Any] | None) -> str:
    snapshot = snapshot or {}
    simulated = (
        bool(snapshot.get("swing_live_order_dry_run"))
        or bool(snapshot.get("scalp_live_simulator"))
        or bool(snapshot.get("simulation_book"))
        or bool(snapshot.get("simulation_owner"))
        or snapshot.get("actual_order_submitted") is False
    )
    if simulated:
        return "ADMIN_ONLY"
    return str(snapshot.get("msg_audience") or "ADMIN_ONLY")


def _entry_receipt_order_key(order_no: str) -> str:
    normalized = str(order_no or "").strip()
    return normalized or _ENTRY_RECEIPT_NO_ORDER_KEY


def _add_receipt_order_key(order_no: str) -> str:
    normalized = str(order_no or "").strip()
    return normalized or _ADD_RECEIPT_NO_ORDER_KEY


def _execution_receipt_signature(
    *,
    cumulative_qty: int,
    order_qty: int | None,
    remaining_qty: int | None,
    cumulative_exec_amount: int | None,
    unit_exec_price: int | None,
    unit_exec_qty: int | None,
) -> dict[str, int | None]:
    """Return the immutable quantity/economics identity of one FID 909 fill."""

    return {
        "cumulative_qty": max(0, int(cumulative_qty or 0)),
        "order_qty": None if order_qty is None else max(0, int(order_qty)),
        "remaining_qty": (
            None if remaining_qty is None else max(0, int(remaining_qty))
        ),
        "cumulative_exec_amount": (
            None
            if cumulative_exec_amount is None
            else max(0, int(cumulative_exec_amount))
        ),
        "unit_exec_price": (
            None if unit_exec_price is None else max(0, int(unit_exec_price))
        ),
        "unit_exec_qty": (
            None if unit_exec_qty is None else max(0, int(unit_exec_qty))
        ),
    }


def _execution_number_conflict_reason(
    executions_by_order: dict[str, Any] | None,
    *,
    order_key: str,
    execution_no: str,
    signature: dict[str, int | None],
) -> str | None:
    """Reject reuse of one broker execution number with changed payload truth."""

    normalized_execution_no = str(execution_no or "").strip()
    if not normalized_execution_no:
        return None
    order_executions = (
        executions_by_order.get(order_key)
        if isinstance(executions_by_order, dict)
        else None
    )
    if not isinstance(order_executions, dict):
        return None
    previous_signature = order_executions.get(normalized_execution_no)
    if previous_signature is None:
        if len(order_executions) >= _EXECUTION_SIGNATURES_PER_ORDER_MAX:
            return "receipt_execution_ledger_capacity_exceeded"
        seen_cumulative_qty = [
            _safe_int(item.get("cumulative_qty"), -1)
            for item in order_executions.values()
            if isinstance(item, dict)
        ]
        if seen_cumulative_qty and _safe_int(signature.get("cumulative_qty"), 0) <= max(
            seen_cumulative_qty
        ):
            return "receipt_new_execution_number_without_positive_delta"
        return None
    if previous_signature != signature:
        return "receipt_execution_number_reused_with_changed_payload"
    return None


def _remember_execution_number(
    executions_by_order: dict[str, Any],
    *,
    order_key: str,
    execution_no: str,
    signature: dict[str, int | None],
) -> None:
    normalized_execution_no = str(execution_no or "").strip()
    if not normalized_execution_no:
        return
    order_executions = executions_by_order.get(order_key)
    if not isinstance(order_executions, dict):
        order_executions = {}
        executions_by_order[order_key] = order_executions
    order_executions[normalized_execution_no] = dict(signature)


def _receipt_nested_map(target_stock: dict[str, Any], key: str) -> dict[str, Any]:
    raw_map = target_stock.get(key)
    if not isinstance(raw_map, dict):
        raw_map = {}
        target_stock[key] = raw_map
    return raw_map


def _receipt_known_order_numbers(
    target_stock: dict[str, Any],
    *,
    pending_orders_key: str | None,
    scalar_order_keys: tuple[str, ...],
    ledger_keys: tuple[str, ...],
    missing_order_key: str,
) -> set[str]:
    known: set[str] = set()
    if pending_orders_key:
        pending_orders = target_stock.get(pending_orders_key) or []
        if isinstance(pending_orders, list):
            for pending_order in pending_orders:
                if not isinstance(pending_order, dict):
                    continue
                order_no = str(pending_order.get("ord_no", "") or "").strip()
                if order_no:
                    known.add(order_no)
    for scalar_key in scalar_order_keys:
        raw_value = str(target_stock.get(scalar_key, "") or "").strip()
        known.update(part.strip() for part in raw_value.split(",") if part.strip())
    for ledger_key in ledger_keys:
        raw_map = target_stock.get(ledger_key)
        if not isinstance(raw_map, dict):
            continue
        known.update(
            str(raw_key).strip()
            for raw_key in raw_map
            if str(raw_key).strip() and str(raw_key).strip() != missing_order_key
        )
    return known


def _bind_entry_receipt_identity(
    target_stock: dict[str, Any],
    *,
    code: str,
    order_no: str,
    order_qty: int | None,
    remaining_qty: int | None,
) -> tuple[str | None, dict[str, Any] | None, bool, str | None]:
    """Resolve one BUY receipt to an exact order, binding only an unambiguous race."""

    normalized_order_no = str(order_no or "").strip()
    pending_orders = [
        pending_order
        for pending_order in (target_stock.get("pending_entry_orders") or [])
        if isinstance(pending_order, dict)
    ]
    known_order_nos = _receipt_known_order_numbers(
        target_stock,
        pending_orders_key="pending_entry_orders",
        scalar_order_keys=("odno",),
        ledger_keys=(
            _ENTRY_RECEIPT_REQUESTED_BY_ORDER_KEY,
            _ENTRY_RECEIPT_FILLED_BY_ORDER_KEY,
            _ENTRY_RECEIPT_AMOUNT_BY_ORDER_KEY,
            _ENTRY_RECEIPT_ECONOMICS_BY_ORDER_KEY,
            _ENTRY_RECEIPT_EXECUTIONS_BY_ORDER_KEY,
        ),
        missing_order_key=_ENTRY_RECEIPT_NO_ORDER_KEY,
    )
    blank_pending_orders = [
        pending_order
        for pending_order in pending_orders
        if not str(pending_order.get("ord_no", "") or "").strip()
    ]
    if not normalized_order_no:
        if blank_pending_orders or len(known_order_nos) != 1:
            reason = (
                "entry_receipt_order_number_missing"
                if not known_order_nos and not blank_pending_orders
                else "entry_receipt_order_number_ambiguous"
            )
            return None, None, False, reason
        normalized_order_no = next(iter(known_order_nos))

    exact_pending_order = next(
        (
            pending_order
            for pending_order in pending_orders
            if str(pending_order.get("ord_no", "") or "").strip() == normalized_order_no
        ),
        None,
    )
    terminal_order = get_terminal_entry_order(normalized_order_no)
    terminal_code = str((terminal_order or {}).get("stock_code", "") or "").strip()[:6]
    terminal_target_id = str((terminal_order or {}).get("target_id", "") or "").strip()
    current_target_id = str(target_stock.get("id", "") or "").strip()
    terminal_target_matches = bool(
        terminal_order is not None
        and terminal_code == code
        and terminal_target_id
        and terminal_target_id == current_target_id
        and str(target_stock.get("status", "") or "").strip().upper()
        in {"WATCHING", "BUY_ORDERED", "HOLDING"}
    )
    if (
        exact_pending_order is not None
        or normalized_order_no in known_order_nos
        or terminal_target_matches
    ):
        return normalized_order_no, exact_pending_order, False, None

    # A broker execution can beat the REST/order-notice response. Bind that race
    # only when FID 900/902 identify one exact still-unbound order leg.
    if order_qty is None or int(order_qty) <= 0 or remaining_qty is None:
        return None, None, False, "entry_receipt_unknown_order_number"
    official_order_qty = max(0, int(order_qty))
    blank_candidates = [
        pending_order
        for pending_order in pending_orders
        if not str(pending_order.get("ord_no", "") or "").strip()
        and (
            official_order_qty <= 0
            or max(0, int(pending_order.get("qty", 0) or 0)) == official_order_qty
        )
    ]
    if len(blank_candidates) > 1:
        return None, None, False, "entry_receipt_unbound_order_ambiguous"
    if known_order_nos and not blank_candidates:
        return None, None, False, "entry_receipt_unknown_order_number"
    if len(blank_candidates) != 1:
        return None, None, False, "entry_receipt_unbound_order_not_identified"

    return normalized_order_no, blank_candidates[0], True, None


def _resolve_add_receipt_identity(
    target_stock: dict[str, Any],
    *,
    order_no: str,
    order_qty: int | None,
    remaining_qty: int | None,
) -> tuple[str | None, bool, str | None]:
    """Resolve an add receipt order key without ever using an ambiguous sentinel."""

    normalized_order_no = str(order_no or "").strip()
    known_order_nos = _receipt_known_order_numbers(
        target_stock,
        pending_orders_key=None,
        scalar_order_keys=("pending_add_ord_no", "add_odno"),
        ledger_keys=(
            _ADD_RECEIPT_REQUESTED_BY_ORDER_KEY,
            _ADD_RECEIPT_FILLED_BY_ORDER_KEY,
            _ADD_RECEIPT_AMOUNT_BY_ORDER_KEY,
            _ADD_RECEIPT_ECONOMICS_BY_ORDER_KEY,
            _ADD_RECEIPT_EXECUTIONS_BY_ORDER_KEY,
            "_add_receipt_leg_meta_by_order_no",
        ),
        missing_order_key=_ADD_RECEIPT_NO_ORDER_KEY,
    )
    if not normalized_order_no:
        if len(known_order_nos) != 1:
            reason = (
                "add_receipt_order_number_missing"
                if not known_order_nos
                else "add_receipt_order_number_ambiguous"
            )
            return None, False, reason
        return next(iter(known_order_nos)), False, None
    if normalized_order_no in known_order_nos:
        return normalized_order_no, False, None
    if known_order_nos:
        return None, False, "add_receipt_unknown_order_number"
    if order_qty is None or remaining_qty is None:
        return None, False, "add_receipt_unbound_order_contract_missing"
    if int(order_qty) <= 0:
        return None, False, "add_receipt_unbound_order_quantity_invalid"
    return normalized_order_no, True, None


def _entry_receipt_int_map(target_stock: dict[str, Any], key: str) -> dict[str, int]:
    raw_map = target_stock.get(key)
    if not isinstance(raw_map, dict):
        raw_map = {}
        target_stock[key] = raw_map
    normalized: dict[str, int] = {}
    for raw_key, raw_value in raw_map.items():
        normalized[str(raw_key)] = int(raw_value or 0)
    if normalized is not raw_map:
        target_stock[key] = normalized
    return normalized


def _add_receipt_leg_meta(
    target_stock: dict[str, Any], order_no: str
) -> dict[str, Any]:
    raw_map = target_stock.get("_add_receipt_leg_meta_by_order_no")
    if not isinstance(raw_map, dict):
        return {}
    order_key = _add_receipt_order_key(order_no)
    raw_meta = raw_map.get(order_key) or raw_map.get(str(order_no or "").strip())
    return dict(raw_meta) if isinstance(raw_meta, dict) else {}


def _split_receipt_leg_meta_fields(
    leg_meta: dict[str, Any], *, filled_at_ts: float
) -> dict[str, Any]:
    if not isinstance(leg_meta, dict) or not leg_meta:
        return {
            "split_leg_ttl_sec": "-",
            "split_bundle_hard_ttl_sec": "-",
            "split_leg_role": "-",
            "split_price_offset_pct": "-",
            "split_price_offset_ticks": "-",
            "split_leg_age_sec": "-",
            "split_fill_before_ttl": "-",
            "split_fill_after_ttl": "-",
            "scale_in_split_order_leg_index": "-",
            "scale_in_split_order_market_order_applied": "-",
            "broker_route": "-",
            "broker_route_resolution": "receipt_leg_route_missing",
        }
    ttl_sec = _safe_int(leg_meta.get("split_leg_ttl_sec"), 0)
    sent_at = _safe_float(leg_meta.get("sent_at"), 0.0)
    age_sec = max(0.0, float(filled_at_ts or 0.0) - sent_at) if sent_at > 0 else None
    return {
        "split_leg_ttl_sec": ttl_sec if ttl_sec > 0 else "-",
        "split_bundle_hard_ttl_sec": leg_meta.get("split_bundle_hard_ttl_sec") or "-",
        "split_leg_role": leg_meta.get("split_leg_role") or "-",
        "split_price_offset_pct": (
            leg_meta.get("split_price_offset_pct")
            if leg_meta.get("split_price_offset_pct") is not None
            else "-"
        ),
        "split_price_offset_ticks": (
            leg_meta.get("split_price_offset_ticks")
            if leg_meta.get("split_price_offset_ticks") is not None
            else "-"
        ),
        "split_leg_age_sec": f"{age_sec:.1f}" if age_sec is not None else "-",
        "split_fill_before_ttl": (
            bool(ttl_sec > 0 and age_sec is not None and age_sec < ttl_sec)
            if ttl_sec > 0
            else "-"
        ),
        "split_fill_after_ttl": (
            bool(ttl_sec > 0 and age_sec is not None and age_sec >= ttl_sec)
            if ttl_sec > 0
            else "-"
        ),
        "scale_in_split_order_leg_index": leg_meta.get("scale_in_split_order_leg_index")
        or "-",
        "scale_in_split_order_market_order_applied": bool(
            leg_meta.get("scale_in_split_order_market_order_applied")
        ),
        "broker_route": (
            str(leg_meta.get("broker_route") or "").strip().upper() or "-"
        ),
        "broker_route_resolution": (
            str(leg_meta.get("broker_route_resolution") or "").strip()
            or "receipt_leg_route_missing"
        ),
    }


def _split_receipt_history_note(leg_fields: dict[str, Any]) -> str | None:
    ttl = leg_fields.get("split_leg_ttl_sec")
    if ttl in {None, "", "-"}:
        return None
    return (
        "receipt_confirmed"
        f"|split_leg_ttl_sec={ttl}"
        f"|split_leg_age_sec={leg_fields.get('split_leg_age_sec', '-')}"
        f"|split_fill_before_ttl={leg_fields.get('split_fill_before_ttl', '-')}"
        f"|split_leg_role={leg_fields.get('split_leg_role', '-')}"
        f"|split_price_offset_pct={leg_fields.get('split_price_offset_pct', '-')}"
        f"|split_price_offset_ticks={leg_fields.get('split_price_offset_ticks', '-')}"
    )


def _pending_add_order_numbers(target_stock: dict[str, Any]) -> list[str]:
    raw = str(target_stock.get("pending_add_ord_no", "") or "").strip()
    return [part.strip() for part in raw.split(",") if part.strip()]


def _append_pending_add_order_no(target_stock: dict[str, Any], order_no: str) -> bool:
    normalized = str(order_no or "").strip()
    if not normalized:
        return False
    order_nos = _pending_add_order_numbers(target_stock)
    if normalized in order_nos:
        return False
    order_nos.append(normalized)
    joined = ",".join(order_nos)
    target_stock["pending_add_ord_no"] = joined
    target_stock["add_odno"] = joined
    return True


def _resolve_cumulative_buy_order_receipt(
    *,
    raw_price: int,
    raw_cumulative_qty: int,
    requested_qty: int,
    previous_qty: int,
    previous_amount: int,
    previous_economics_complete: bool,
    order_qty: int | None,
    remaining_qty: int | None,
    cumulative_exec_amount: int | None,
    unit_exec_price: int | None,
    unit_exec_qty: int | None,
) -> dict[str, Any]:
    """Return one exact delta from a Kiwoom 00 cumulative BUY receipt."""

    raw_qty = max(0, int(raw_cumulative_qty or 0))
    known_requested_qty = max(0, int(requested_qty or 0))
    official_order_qty = max(0, int(order_qty or 0)) if order_qty is not None else 0
    if raw_qty <= 0:
        return {"status": "invalid", "reason": "buy_receipt_quantity_missing"}
    if (
        known_requested_qty > 0
        and official_order_qty > 0
        and known_requested_qty != official_order_qty
    ):
        return {
            "status": "invalid",
            "reason": "buy_receipt_requested_quantity_conflict",
        }
    expected_qty = known_requested_qty or official_order_qty
    prior_qty = max(0, int(previous_qty or 0))
    prior_amount = max(0, int(previous_amount or 0))
    official_remaining_qty = (
        max(0, int(remaining_qty)) if remaining_qty is not None else None
    )
    if official_remaining_qty is not None:
        receipt_expected_qty = raw_qty + official_remaining_qty
        if expected_qty > 0 and receipt_expected_qty != expected_qty:
            return {
                "status": "invalid",
                "reason": (
                    "buy_receipt_duplicate_quantity_remaining_conflict"
                    if raw_qty == prior_qty
                    else "buy_receipt_remaining_quantity_conflict"
                ),
            }
        expected_qty = expected_qty or receipt_expected_qty
    if expected_qty > 0 and raw_qty > expected_qty:
        return {
            "status": "invalid",
            "reason": "buy_receipt_cumulative_quantity_exceeds_order",
        }

    if raw_qty < prior_qty:
        return {
            "status": "invalid",
            "reason": "buy_receipt_cumulative_quantity_regressed",
        }

    official_cumulative_amount = (
        max(0, int(cumulative_exec_amount))
        if cumulative_exec_amount is not None
        else None
    )
    if raw_qty == prior_qty:
        if (
            official_cumulative_amount is not None
            and prior_amount > 0
            and official_cumulative_amount != prior_amount
        ):
            return {
                "status": "invalid",
                "reason": "buy_receipt_duplicate_quantity_amount_conflict",
            }
        repaired_amount = official_cumulative_amount or prior_amount
        return {
            "status": "duplicate",
            "reason": "buy_receipt_duplicate_cumulative_quantity",
            "requested_qty": expected_qty,
            "cumulative_qty": raw_qty,
            "remaining_qty": (
                official_remaining_qty
                if official_remaining_qty is not None
                else max(0, expected_qty - raw_qty)
            ),
            "cumulative_amount": repaired_amount,
            "economics_complete": bool(
                previous_economics_complete and repaired_amount > 0
            ),
            "final": bool(expected_qty > 0 and raw_qty == expected_qty),
        }

    incremental_qty = raw_qty - prior_qty
    economics_complete = bool(previous_economics_complete)
    unit_price = max(0, int(unit_exec_price or 0))
    unit_qty_matches_delta = (
        None if unit_exec_qty is None else int(unit_exec_qty) == incremental_qty
    )
    if official_cumulative_amount is not None:
        if prior_amount > 0:
            if official_cumulative_amount <= prior_amount:
                return {
                    "status": "invalid",
                    "reason": "buy_receipt_cumulative_amount_not_increasing",
                }
            incremental_amount = official_cumulative_amount - prior_amount
        elif prior_qty <= 0:
            incremental_amount = official_cumulative_amount
        elif unit_qty_matches_delta is True and unit_price > 0:
            incremental_amount = unit_price * incremental_qty
            if official_cumulative_amount < incremental_amount:
                return {
                    "status": "invalid",
                    "reason": "buy_receipt_cumulative_amount_unit_conflict",
                }
            economics_complete = False
        else:
            return {
                "status": "invalid",
                "reason": "buy_receipt_prior_cumulative_amount_missing",
            }
        cumulative_amount = official_cumulative_amount
    else:
        economics_complete = False
        fallback_price = unit_price if unit_qty_matches_delta is True else 0
        if fallback_price <= 0:
            fallback_price = max(0, int(raw_price or 0))
            economics_complete = False
        if fallback_price <= 0:
            return {
                "status": "invalid",
                "reason": "buy_receipt_incremental_price_missing",
            }
        incremental_amount = fallback_price * incremental_qty
        cumulative_amount = prior_amount + incremental_amount
    if incremental_amount <= 0 or cumulative_amount <= 0:
        return {
            "status": "invalid",
            "reason": "buy_receipt_incremental_amount_invalid",
        }

    unit_price_matches_delta = (
        None
        if unit_exec_price is None
        else int(unit_exec_price) * incremental_qty == incremental_amount
    )
    unit_fill_consistent = bool(
        unit_qty_matches_delta is True and unit_price_matches_delta is True
    )
    quantity_contract_complete = bool(
        official_order_qty > 0 and official_remaining_qty is not None
    )
    final = bool(
        expected_qty > 0 and raw_qty == expected_qty and official_remaining_qty == 0
    )
    return {
        "status": "final" if final else "partial",
        "reason": (
            "buy_receipt_full_order_reconciled" if final else "buy_receipt_partial_fill"
        ),
        "final": final,
        "requested_qty": expected_qty,
        "remaining_qty": (
            official_remaining_qty
            if official_remaining_qty is not None
            else max(0, expected_qty - raw_qty)
        ),
        "cumulative_qty": raw_qty,
        "cumulative_amount": cumulative_amount,
        "incremental_qty": incremental_qty,
        "incremental_amount": incremental_amount,
        "incremental_price": incremental_amount / incremental_qty,
        "economics_complete": economics_complete,
        "quantity_contract_complete": quantity_contract_complete,
        "unit_fill_consistent": unit_fill_consistent,
        "unit_qty_matches_delta": unit_qty_matches_delta,
        "unit_price_matches_delta": unit_price_matches_delta,
    }


def _resolve_fast_sell_execution_receipt(
    state: dict[str, Any],
    *,
    order_no: str,
    exec_price: int,
    cumulative_exec_qty: int,
    order_qty: int | None,
    remaining_qty: int | None,
    cumulative_exec_amount: int | None,
    execution_no: str,
    unit_exec_price: int | None,
    unit_exec_qty: int | None,
) -> dict[str, Any]:
    """Apply one S15 SELL cumulative receipt to a per-order ledger.

    Fast-track cancel/retry orders each restart FID 911/903 at zero. Keeping a
    single global previous cumulative drops fills from the replacement order.
    """

    normalized_order_no = str(order_no or "").strip()
    if not normalized_order_no:
        return {"status": "invalid", "reason": "fast_sell_order_number_missing"}
    raw_ledgers = state.get("sell_receipts_by_order_no")
    ledgers = raw_ledgers if isinstance(raw_ledgers, dict) else {}
    prior_raw = ledgers.get(normalized_order_no)
    prior = dict(prior_raw) if isinstance(prior_raw, dict) else {}
    executions = prior.get("executions_by_no")
    executions = dict(executions) if isinstance(executions, dict) else {}
    signature = _execution_receipt_signature(
        cumulative_qty=cumulative_exec_qty,
        order_qty=order_qty,
        remaining_qty=remaining_qty,
        cumulative_exec_amount=cumulative_exec_amount,
        unit_exec_price=unit_exec_price,
        unit_exec_qty=unit_exec_qty,
    )
    conflict = _execution_number_conflict_reason(
        {normalized_order_no: executions},
        order_key=normalized_order_no,
        execution_no=execution_no,
        signature=signature,
    )
    if conflict:
        return {"status": "invalid", "reason": conflict}

    requested_qty = max(0, _safe_int(prior.get("requested_qty"), 0))
    if requested_qty <= 0 and order_qty is not None:
        requested_qty = max(0, int(order_qty))
    receipt = _resolve_cumulative_buy_order_receipt(
        raw_price=exec_price,
        raw_cumulative_qty=cumulative_exec_qty,
        requested_qty=requested_qty,
        previous_qty=max(0, _safe_int(prior.get("cumulative_qty"), 0)),
        previous_amount=max(0, _safe_int(prior.get("cumulative_amount"), 0)),
        previous_economics_complete=bool(prior.get("economics_complete", True)),
        order_qty=order_qty,
        remaining_qty=remaining_qty,
        cumulative_exec_amount=cumulative_exec_amount,
        unit_exec_price=unit_exec_price,
        unit_exec_qty=unit_exec_qty,
    )
    if receipt.get("status") == "invalid":
        return receipt

    holder = {normalized_order_no: executions}
    _remember_execution_number(
        holder,
        order_key=normalized_order_no,
        execution_no=execution_no,
        signature=signature,
    )
    executions = holder[normalized_order_no]
    if receipt.get("status") == "duplicate":
        return receipt

    next_ledgers = dict(ledgers)
    next_ledgers[normalized_order_no] = {
        "requested_qty": max(0, _safe_int(receipt.get("requested_qty"), 0)),
        "cumulative_qty": max(0, _safe_int(receipt.get("cumulative_qty"), 0)),
        "remaining_qty": max(0, _safe_int(receipt.get("remaining_qty"), 0)),
        "cumulative_amount": max(0, _safe_int(receipt.get("cumulative_amount"), 0)),
        "economics_complete": receipt.get("economics_complete") is True,
        "quantity_contract_complete": (
            receipt.get("quantity_contract_complete") is True
        ),
        "unit_fill_consistent": receipt.get("unit_fill_consistent") is True,
        "executions_by_no": executions,
    }
    aggregate_qty = sum(
        max(0, _safe_int(item.get("cumulative_qty"), 0))
        for item in next_ledgers.values()
        if isinstance(item, dict)
    )
    aggregate_amount = sum(
        max(0, _safe_int(item.get("cumulative_amount"), 0))
        for item in next_ledgers.values()
        if isinstance(item, dict)
    )
    buy_qty = max(0, _safe_int(state.get("cum_buy_qty"), 0))
    if aggregate_qty > buy_qty > 0:
        return {
            "status": "invalid",
            "reason": "fast_sell_aggregate_quantity_exceeds_position",
        }
    quantity_contract_complete = bool(
        next_ledgers
        and all(
            isinstance(item, dict) and item.get("quantity_contract_complete") is True
            for item in next_ledgers.values()
        )
    )
    economics_complete = bool(
        next_ledgers
        and all(
            isinstance(item, dict) and item.get("economics_complete") is True
            for item in next_ledgers.values()
        )
    )
    unit_fill_consistent = bool(
        next_ledgers
        and all(
            isinstance(item, dict) and item.get("unit_fill_consistent") is True
            for item in next_ledgers.values()
        )
    )
    position_complete = bool(
        buy_qty > 0
        and aggregate_qty == buy_qty
        and receipt.get("final") is True
        and quantity_contract_complete
    )
    state["sell_receipts_by_order_no"] = next_ledgers
    state["cum_sell_qty"] = aggregate_qty
    state["cum_sell_amount"] = aggregate_amount
    state["avg_sell_price"] = _avg_from_totals(aggregate_amount, aggregate_qty)
    state["sell_receipt_economics_complete"] = economics_complete
    state["sell_receipt_quantity_contract_complete"] = quantity_contract_complete
    state["sell_receipt_unit_fill_consistent"] = unit_fill_consistent
    state["sell_receipt_position_complete"] = position_complete
    return {
        **receipt,
        "aggregate_cumulative_qty": aggregate_qty,
        "aggregate_cumulative_amount": aggregate_amount,
        "position_complete": position_complete,
    }


def _resolve_entry_effective_fill_qty(
    *,
    target_stock: dict[str, Any],
    code: str,
    order_no: str,
    exec_price: int,
    exec_qty: int,
    order_qty: int | None = None,
    remaining_qty: int | None = None,
    cumulative_exec_amount: int | None = None,
    execution_no: str = "",
    unit_exec_price: int | None = None,
    unit_exec_qty: int | None = None,
) -> dict[str, Any]:
    """Reconcile an entry order's cumulative receipt to one exact fill delta."""

    (
        resolved_order_no,
        pending_order,
        bind_after_validation,
        identity_error,
    ) = _bind_entry_receipt_identity(
        target_stock,
        code=code,
        order_no=order_no,
        order_qty=order_qty,
        remaining_qty=remaining_qty,
    )
    if identity_error:
        return {"status": "invalid", "reason": identity_error}
    terminal_entry_receipt = bool(
        resolved_order_no and get_terminal_entry_order(resolved_order_no) is not None
    )
    order_key = _entry_receipt_order_key(resolved_order_no or "")
    requested_by_order = _entry_receipt_int_map(
        target_stock, _ENTRY_RECEIPT_REQUESTED_BY_ORDER_KEY
    )
    filled_by_order = _entry_receipt_int_map(
        target_stock, _ENTRY_RECEIPT_FILLED_BY_ORDER_KEY
    )
    amount_by_order = _entry_receipt_int_map(
        target_stock, _ENTRY_RECEIPT_AMOUNT_BY_ORDER_KEY
    )
    economics_by_order = _entry_receipt_int_map(
        target_stock, _ENTRY_RECEIPT_ECONOMICS_BY_ORDER_KEY
    )
    executions_by_order = _receipt_nested_map(
        target_stock, _ENTRY_RECEIPT_EXECUTIONS_BY_ORDER_KEY
    )
    execution_signature = _execution_receipt_signature(
        cumulative_qty=exec_qty,
        order_qty=order_qty,
        remaining_qty=remaining_qty,
        cumulative_exec_amount=cumulative_exec_amount,
        unit_exec_price=unit_exec_price,
        unit_exec_qty=unit_exec_qty,
    )
    execution_conflict = _execution_number_conflict_reason(
        executions_by_order,
        order_key=order_key,
        execution_no=execution_no,
        signature=execution_signature,
    )
    if execution_conflict:
        return {"status": "invalid", "reason": execution_conflict}

    ledger_requested_qty = max(0, int(requested_by_order.get(order_key, 0) or 0))
    pending_requested_qty = (
        max(0, int(pending_order.get("qty", 0) or 0))
        if pending_order is not None
        else 0
    )
    if (
        ledger_requested_qty > 0
        and pending_requested_qty > 0
        and ledger_requested_qty != pending_requested_qty
    ):
        return {
            "status": "invalid",
            "reason": "entry_receipt_requested_ledger_conflict",
        }
    requested_qty = ledger_requested_qty or pending_requested_qty
    if requested_qty <= 0 and order_qty is not None:
        requested_qty = max(0, int(order_qty))
    if requested_qty <= 0:
        requested_qty = max(
            0,
            int(
                target_stock.get(
                    "entry_requested_qty",
                    target_stock.get("requested_buy_qty", 0),
                )
                or 0
            ),
        )

    ledger_filled_qty = max(0, int(filled_by_order.get(order_key, 0) or 0))
    pending_filled_qty = (
        max(0, int(pending_order.get("filled_qty", 0) or 0))
        if pending_order is not None
        else 0
    )
    already_filled = max(ledger_filled_qty, pending_filled_qty)
    receipt = _resolve_cumulative_buy_order_receipt(
        raw_price=exec_price,
        raw_cumulative_qty=exec_qty,
        requested_qty=requested_qty,
        previous_qty=already_filled,
        previous_amount=max(0, int(amount_by_order.get(order_key, 0) or 0)),
        previous_economics_complete=bool(economics_by_order.get(order_key, 1)),
        order_qty=order_qty,
        remaining_qty=remaining_qty,
        cumulative_exec_amount=cumulative_exec_amount,
        unit_exec_price=unit_exec_price,
        unit_exec_qty=unit_exec_qty,
    )
    if receipt.get("status") == "invalid":
        return receipt

    cumulative_qty = max(0, int(receipt.get("cumulative_qty") or 0))
    cumulative_amount = max(0, int(receipt.get("cumulative_amount") or 0))
    requested_qty = max(0, int(receipt.get("requested_qty") or requested_qty))
    if receipt.get("status") != "duplicate":
        bundle_requested_qty = max(
            0,
            _safe_int(
                target_stock.get(
                    "entry_requested_qty",
                    target_stock.get("requested_buy_qty", 0),
                ),
                0,
            ),
        )
        bundle_filled_qty = max(0, _safe_int(target_stock.get("entry_filled_qty"), 0))
        if (
            bundle_requested_qty > 0
            and bundle_filled_qty + int(receipt["incremental_qty"])
            > bundle_requested_qty
        ):
            return {
                "status": "invalid",
                "reason": "entry_receipt_bundle_quantity_exceeded",
            }

    _remember_execution_number(
        executions_by_order,
        order_key=order_key,
        execution_no=execution_no,
        signature=execution_signature,
    )

    if bind_after_validation:
        assert pending_order is not None
        pending_order["ord_no"] = str(resolved_order_no or "")
        if not str(target_stock.get("odno", "") or "").strip():
            target_stock["odno"] = str(resolved_order_no or "")
        target_stock["entry_receipt_reconciled_before_ordno_bind"] = True
    requested_by_order[order_key] = requested_qty
    filled_by_order[order_key] = cumulative_qty
    if cumulative_amount > 0:
        amount_by_order[order_key] = cumulative_amount
    economics_by_order[order_key] = int(bool(receipt.get("economics_complete")))
    if pending_order is not None:
        pending_order["filled_qty"] = cumulative_qty
        pending_order["status"] = (
            "FILLED"
            if requested_qty > 0 and cumulative_qty >= requested_qty
            else "PARTIAL"
        )
        pending_order["last_effective_fill_qty"] = int(
            receipt.get("incremental_qty") or 0
        )
    receipt["order_no"] = resolved_order_no
    receipt["terminal_entry_order_receipt"] = terminal_entry_receipt
    return receipt


def _cancel_replacement_buys_after_late_parent_fill(
    target_stock: dict[str, Any], *, code: str, filled_order_no: str
) -> bool:
    """Cancel every active child BUY after a terminal parent fills late.

    A REST cancel acknowledgement does not make the parent terminal.  If the
    parent fills after a replacement was accepted, leaving the child live can
    overbuy the position.  Keep all identities until broker reconciliation.
    """

    candidates = []
    for order in target_stock.get("pending_entry_orders") or ():
        if not isinstance(order, dict):
            continue
        order_no = str(order.get("ord_no") or "").strip()
        if not order_no or order_no == str(filled_order_no or "").strip():
            continue
        requested = max(0, _safe_int(order.get("qty"), 0))
        filled = max(0, _safe_int(order.get("filled_qty"), 0))
        status = str(order.get("status") or "").strip().upper()
        if requested > filled and status not in {"FILLED", "CANCELLED", "REJECTED"}:
            candidates.append(order)
    if not candidates:
        return True

    from src.engine import kiwoom_orders

    all_acknowledged = True
    for order in candidates:
        order_no = str(order.get("ord_no") or "").strip()
        try:
            result = kiwoom_orders.send_cancel_order(
                code=code,
                orig_ord_no=order_no,
                token=KIWOOM_TOKEN,
                qty=0,
                dmst_stex_tp=(
                    order.get("broker_route")
                    or order.get("effective_dmst_stex_tp")
                    or target_stock.get("entry_execution_broker_route")
                ),
            )
            acknowledged = _is_ok_response(result)
        except Exception as exc:
            acknowledged = False
            log_error(
                f"[ENTRY_REPLACEMENT_CANCEL_FAILED] {code} ord_no={order_no}: {exc}"
            )
        order["status"] = "CANCEL_PENDING"
        order["late_parent_fill_cancel_acknowledged"] = bool(acknowledged)
        order["late_parent_fill_cancel_requested_at"] = time.time()
        all_acknowledged = all_acknowledged and acknowledged

    target_stock["entry_cancel_reconciliation_required"] = True
    target_stock["entry_cancel_reconciliation_source"] = (
        "late_parent_fill_replacement_cancel_acknowledged"
        if all_acknowledged
        else "late_parent_fill_replacement_cancel_unconfirmed"
    )
    target_stock["entry_replacement_submit_forbidden"] = True
    target_stock["scale_in_locked"] = True
    _request_broker_snapshot_refresh(
        code, reason="late_parent_fill_replacement_cancel_reconciliation"
    )
    return False


def _resolve_add_effective_fill(
    *,
    target_stock: dict[str, Any],
    code: str,
    order_no: str,
    exec_price: int,
    exec_qty: int,
    order_qty: int | None = None,
    remaining_qty: int | None = None,
    cumulative_exec_amount: int | None = None,
    execution_no: str = "",
    unit_exec_price: int | None = None,
    unit_exec_qty: int | None = None,
) -> dict[str, Any]:
    """Return the add-buy fill delta and effective incremental price.

    Kiwoom add-buy execution notices can arrive as cumulative order fill
    quantity/average price. Keep a per-pending-add ledger so a partial notice
    such as 37 shares followed by cumulative 59 shares mutates runtime truth by
    only the remaining 22 shares, with the incremental price reconstructed from
    cumulative notional.
    """

    raw_qty = max(0, int(exec_qty or 0))
    raw_price = max(0, int(exec_price or 0))
    bundle_requested_qty = int(target_stock.get("pending_add_qty", 0) or 0)
    bundle_already_filled = int(target_stock.get("pending_add_filled_qty", 0) or 0)
    bundle_already_amount = int(target_stock.get("pending_add_filled_amount", 0) or 0)
    if raw_qty <= 0:
        return {"status": "invalid", "reason": "add_receipt_quantity_missing"}

    (
        resolved_order_no,
        reconciled_before_ordno_bind,
        identity_error,
    ) = _resolve_add_receipt_identity(
        target_stock,
        order_no=order_no,
        order_qty=order_qty,
        remaining_qty=remaining_qty,
    )
    if identity_error:
        return {"status": "invalid", "reason": identity_error}
    normalized_order_no = str(resolved_order_no or "").strip()
    order_key = _add_receipt_order_key(normalized_order_no)
    requested_by_order = _entry_receipt_int_map(
        target_stock, _ADD_RECEIPT_REQUESTED_BY_ORDER_KEY
    )
    filled_by_order = _entry_receipt_int_map(
        target_stock, _ADD_RECEIPT_FILLED_BY_ORDER_KEY
    )
    amount_by_order = _entry_receipt_int_map(
        target_stock, _ADD_RECEIPT_AMOUNT_BY_ORDER_KEY
    )
    economics_by_order = _entry_receipt_int_map(
        target_stock, _ADD_RECEIPT_ECONOMICS_BY_ORDER_KEY
    )
    executions_by_order = _receipt_nested_map(
        target_stock, _ADD_RECEIPT_EXECUTIONS_BY_ORDER_KEY
    )
    execution_signature = _execution_receipt_signature(
        cumulative_qty=exec_qty,
        order_qty=order_qty,
        remaining_qty=remaining_qty,
        cumulative_exec_amount=cumulative_exec_amount,
        unit_exec_price=unit_exec_price,
        unit_exec_qty=unit_exec_qty,
    )
    execution_conflict = _execution_number_conflict_reason(
        executions_by_order,
        order_key=order_key,
        execution_no=execution_no,
        signature=execution_signature,
    )
    if execution_conflict:
        return {"status": "invalid", "reason": execution_conflict}
    pending_ord_nos = set(_pending_add_order_numbers(target_stock))

    order_requested_qty = max(0, int(requested_by_order.get(order_key, 0) or 0))
    leg_meta_qty = max(
        0,
        _safe_int(
            _add_receipt_leg_meta(target_stock, normalized_order_no).get("qty"), 0
        ),
    )
    if (
        order_requested_qty > 0
        and leg_meta_qty > 0
        and order_requested_qty != leg_meta_qty
    ):
        return {
            "status": "invalid",
            "reason": "add_receipt_requested_ledger_conflict",
        }
    order_requested_qty = order_requested_qty or leg_meta_qty
    if order_requested_qty <= 0:
        if order_qty is not None:
            order_requested_qty = max(0, int(order_qty))
        elif not normalized_order_no:
            order_requested_qty = bundle_requested_qty
        elif len(pending_ord_nos) <= 1 and bundle_requested_qty > 0:
            order_requested_qty = bundle_requested_qty
        else:
            order_requested_qty = raw_qty

    order_already_filled = int(filled_by_order.get(order_key, 0) or 0)
    order_already_amount = int(amount_by_order.get(order_key, 0) or 0)
    receipt = _resolve_cumulative_buy_order_receipt(
        raw_price=raw_price,
        raw_cumulative_qty=raw_qty,
        requested_qty=order_requested_qty,
        previous_qty=order_already_filled,
        previous_amount=order_already_amount,
        previous_economics_complete=bool(economics_by_order.get(order_key, 1)),
        order_qty=order_qty,
        remaining_qty=remaining_qty,
        cumulative_exec_amount=cumulative_exec_amount,
        unit_exec_price=unit_exec_price,
        unit_exec_qty=unit_exec_qty,
    )
    if receipt.get("status") == "invalid":
        return receipt

    effective_qty = max(0, int(receipt.get("incremental_qty") or 0))
    if (
        receipt.get("status") != "duplicate"
        and bundle_requested_qty > 0
        and bundle_already_filled + effective_qty > bundle_requested_qty
    ):
        return {
            "status": "invalid",
            "reason": "add_receipt_bundle_quantity_exceeded",
        }

    _remember_execution_number(
        executions_by_order,
        order_key=order_key,
        execution_no=execution_no,
        signature=execution_signature,
    )

    order_requested_qty = max(
        0, int(receipt.get("requested_qty") or order_requested_qty)
    )
    new_order_filled = max(0, int(receipt.get("cumulative_qty") or 0))
    new_order_amount = max(0, int(receipt.get("cumulative_amount") or 0))
    requested_by_order[order_key] = order_requested_qty
    filled_by_order[order_key] = new_order_filled
    if new_order_amount > 0:
        amount_by_order[order_key] = new_order_amount
    economics_by_order[order_key] = int(bool(receipt.get("economics_complete")))
    if reconciled_before_ordno_bind:
        _append_pending_add_order_no(target_stock, normalized_order_no)
        target_stock["scale_in_receipt_reconciled_before_ordno_bind"] = True
    if receipt.get("status") == "duplicate":
        receipt.update(
            {
                "bundle_requested_qty": bundle_requested_qty,
                "bundle_filled_qty": bundle_already_filled,
                "order_requested_qty": order_requested_qty,
                "order_filled_qty": new_order_filled,
                "reconciled_before_ordno_bind": reconciled_before_ordno_bind,
                "order_no": normalized_order_no,
            }
        )
        return receipt

    new_bundle_filled = bundle_already_filled + effective_qty
    incremental_amount = max(0, int(receipt.get("incremental_amount") or 0))
    target_stock["pending_add_filled_qty"] = new_bundle_filled
    target_stock["pending_add_filled_amount"] = (
        bundle_already_amount + incremental_amount
    )
    receipt.update(
        {
            "bundle_requested_qty": bundle_requested_qty,
            "bundle_filled_qty": new_bundle_filled,
            "order_requested_qty": order_requested_qty,
            "order_filled_qty": new_order_filled,
            "reconciled_before_ordno_bind": reconciled_before_ordno_bind,
            "order_no": normalized_order_no,
        }
    )
    return receipt


def _clear_runtime_keys(target_stock: dict[str, Any], keys: tuple[str, ...]) -> None:
    for key in keys:
        target_stock.pop(key, None)


def _normalize_sell_pending_message_for_realized_result(
    pending_msg: str,
    *,
    result_label: str,
    profit_rate: float,
) -> str:
    final_msg = (
        pending_msg.replace("매도 전송", "매도 체결 완료")
        .replace("[익절 주문]", result_label)
        .replace("[손절 주문]", result_label)
        .replace("[익절 완료]", result_label)
        .replace("[손절 완료]", result_label)
    )
    if profit_rate > 0:
        final_msg = final_msg.replace("📉 [익절 완료]", "🎊 [익절 완료]")
        normalized_lines = []
        for line in final_msg.splitlines():
            if line.startswith("사유:") and (
                "하드스탑" in line or "손절" in line or "LOSS" in line
            ):
                normalized_lines.append(line.replace("사유:", "청산 신호:", 1))
                normalized_lines.append("실현 결과: `익절 확정`")
                continue
            if line.startswith("현재가 기준 수익:"):
                normalized_lines.append(
                    line.replace("현재가 기준 수익:", "신호 당시 평가손익:", 1)
                )
                continue
            normalized_lines.append(line)
        final_msg = "\n".join(normalized_lines)
    elif profit_rate < 0:
        final_msg = final_msg.replace("🎊 [손절 완료]", "📉 [손절 완료]")
        final_msg = final_msg.replace("💰 [손절 완료]", "📉 [손절 완료]")
    return final_msg


def _publish_sell_execution_message(
    *, name: str, pending_msg: str, audience: str, exec_price: int, profit_rate: float
) -> None:
    try:
        result_label = "[익절 완료]" if profit_rate > 0 else "[손절 완료]"
        if pending_msg:
            final_msg = _normalize_sell_pending_message_for_realized_result(
                pending_msg,
                result_label=result_label,
                profit_rate=profit_rate,
            )
            final_msg += f"\n✅ **실제 체결가:** `{exec_price:,}원` (확정 수익률: `{profit_rate:+.2f}%`)"
            event_bus.publish(
                "TELEGRAM_BROADCAST",
                {"message": final_msg, "audience": audience, "parse_mode": "HTML"},
            )
            return

        sign = f"🎊 {result_label}" if profit_rate > 0 else f"📉 {result_label}"
        event_bus.publish(
            "TELEGRAM_BROADCAST",
            {
                "message": f"{sign} **[{name}]** 매도 체결!\n체결가: `{exec_price:,}원`\n수익률: `{profit_rate:+.2f}%`",
                "audience": audience,
                "parse_mode": "HTML",
            },
        )
    except Exception as exc:
        # Completion custody has already been committed by both callers.  A
        # notification outage must not make them report transaction failure
        # and replay the same broker receipt as an uncommitted sell.
        log_error(
            f"[SELL_COMPLETION_NOTIFICATION_FAILED] {name or '-'} "
            f"price={exec_price} profit_rate={profit_rate}: {exc}"
        )


def _resolve_sell_execution_context(
    target_id: int, target_stock: dict[str, Any], exec_price: int, now_t
):
    try:
        with DB.get_session() as session:
            record = (
                session.query(RecommendationHistory).filter_by(id=target_id).first()
            )
            if not record:
                return None
            safe_buy_price = (
                float(record.buy_price) if record.buy_price is not None else 0.0
            )
            profit_rate = 0.0
            if safe_buy_price <= 0:
                log_error(
                    f"⚠️ [수익률 계산 불가] ID {target_id}의 매수가(buy_price)가 누락되어 수익률을 0%로 처리합니다."
                )
            strategy = normalize_strategy(
                record.strategy or target_stock.get("strategy") or "KOSPI_ML"
            )
            position_tag = normalize_position_tag(
                strategy,
                getattr(record, "position_tag", None)
                or target_stock.get("position_tag"),
            )
            is_scalp_revive = (
                strategy == "SCALPING"
                and now_t < TIME_15_30
                and position_tag != OPENING_ROTATION_POSITION_TAG
            )
            return record, safe_buy_price, profit_rate, strategy, is_scalp_revive
    except Exception as e:
        log_error(f"🚨 [DB 조회 에러] ID {target_id} SELL 처리 중 에러: {e}")
        return None


def _finalize_standard_sell_execution(
    *,
    target_id: int,
    exec_price: int,
    now: datetime,
    target_stock: dict[str, Any],
    strategy: str,
    is_scalp_revive: bool,
    code: str,
    sell_receipt: dict[str, Any],
    order_no: str = "",
) -> None:
    if sell_receipt.get("status") != "final" or sell_receipt.get("final") is not True:
        log_error(
            f"[SELL_RECEIPT_FINALIZE_BLOCKED] {target_stock.get('name', code)}({code}) "
            f"status={sell_receipt.get('status')} reason={sell_receipt.get('reason')}"
        )
        return
    target_stock["sell_execution_order_no"] = str(order_no or "").strip() or "-"
    smoothing_registration = {
        "registered": False,
        "status": "not_applicable",
        "active_arm_count": 0,
        "expires_at_epoch": None,
    }
    if (
        strategy == "SCALPING"
        and not is_scalp_revive
        and callable(_smoothing_non_revive_post_sell_register_callback)
    ):
        try:
            callback_result = _smoothing_non_revive_post_sell_register_callback(
                target_stock,
                code,
                now_ts=now.timestamp(),
            )
            if isinstance(callback_result, dict):
                smoothing_registration.update(callback_result)
        except Exception as exc:
            smoothing_registration["status"] = "registration_callback_error"
            log_error(
                "[SMOOTHING_POST_SELL] non-revive registration failed "
                f"code={code}: {exc}"
            )
    sell_receipt_snapshot = _receipt_snapshot(target_stock, _SELL_RECEIPT_SNAPSHOT_KEYS)
    sell_receipt_snapshot.update(
        {
            "smoothing_non_revive_post_sell_registered": bool(
                smoothing_registration.get("registered")
            ),
            "smoothing_non_revive_post_sell_registration_status": str(
                smoothing_registration.get("status") or "unknown"
            ),
            "smoothing_non_revive_post_sell_active_arm_count": _safe_int(
                smoothing_registration.get("active_arm_count"), 0
            ),
            "smoothing_non_revive_post_sell_expires_at_epoch": (
                smoothing_registration.get("expires_at_epoch")
            ),
            "sell_execution_expected_qty": int(sell_receipt["expected_qty"]),
            "sell_execution_cumulative_qty": int(sell_receipt["cumulative_qty"]),
            "sell_execution_cumulative_amount": int(sell_receipt["cumulative_amount"]),
            "sell_execution_cumulative_net_pnl_krw": float(
                sell_receipt["cumulative_net_pnl_krw"]
            ),
            "sell_execution_final_leg_qty": int(sell_receipt["incremental_qty"]),
            "sell_execution_final_leg_price": float(sell_receipt["incremental_price"]),
            "sell_execution_final_leg_net_pnl_krw": float(
                sell_receipt["incremental_net_pnl_krw"]
            ),
            "sell_execution_execution_no": str(
                sell_receipt.get("execution_no") or ""
            ).strip()
            or "-",
            "sell_execution_receipt_economics_complete": bool(
                sell_receipt.get("economics_complete")
            ),
            "sell_execution_receipt_quantity_contract_complete": bool(
                sell_receipt.get("quantity_contract_complete")
            ),
            "sell_execution_receipt_unit_fill_consistent": bool(
                sell_receipt.get("unit_fill_consistent", True)
            ),
        }
    )
    # The broker-final receipt must remain durable until the DB transaction is
    # committed.  Previously a daemon thread was started only after the journal
    # and runtime state were cleared, so a process kill could lose the only
    # exact quantity/economics evidence while DB still said SELL_ORDERED.
    state = target_stock.get(_SELL_EXECUTION_RECEIPT_STATE_KEY)
    if not isinstance(state, dict):
        state = {}
    state.update(
        {
            "position_qty": int(sell_receipt["expected_qty"]),
            "aggregate_cumulative_qty": int(sell_receipt["cumulative_qty"]),
            "aggregate_cumulative_amount": int(sell_receipt["cumulative_amount"]),
            "cumulative_net_pnl_krw": float(sell_receipt["cumulative_net_pnl_krw"]),
            "remaining_qty": 0,
            "final": True,
            "final_pending_db_commit": True,
            "finalization_exec_price": int(exec_price),
            "finalization_now_iso": now.isoformat(),
            "finalization_strategy": str(strategy),
            "finalization_is_scalp_revive": bool(is_scalp_revive),
            "finalization_order_no": str(order_no or "").strip(),
            "finalization_receipt_snapshot": json.loads(
                json.dumps(sell_receipt_snapshot, ensure_ascii=True, default=str)
            ),
            "receipt_updated_at_epoch": time.time(),
        }
    )
    target_stock[_SELL_EXECUTION_RECEIPT_STATE_KEY] = state
    target_stock.update(
        {
            "status": "SELL_ORDERED",
            "scale_in_locked": True,
            "sell_partial_exit_carry_active": True,
            "sell_partial_exit_recovery_required": True,
            "sell_cancel_reconciliation_required": True,
            "sell_cancel_reconciliation_source": "final_receipt_db_commit_pending",
        }
    )
    if not _persist_sell_receipt_recovery_or_interlock(
        target_stock,
        code=code,
        reason="final_sell_receipt_before_db_commit",
    ):
        log_error(
            f"[SELL_FINAL_DURABILITY_BLOCKED] {target_stock.get('name', code)}({code}) "
            "final receipt journal could not be persisted; DB finalization withheld"
        )
        return
    if not _update_db_for_sell(
        target_id,
        exec_price,
        now,
        sell_receipt_snapshot,
        strategy,
        is_scalp_revive,
    ):
        log_error(
            f"[SELL_FINAL_DB_COMMIT_DEFERRED] {target_stock.get('name', code)}({code}) "
            "durable final receipt retained for startup/periodic recovery"
        )
        return
    _complete_standard_sell_runtime_after_db(
        target_id=target_id,
        target_stock=target_stock,
        code=code,
        now=now,
        order_no=order_no,
    )


def _complete_standard_sell_runtime_after_db(
    *,
    target_id: int,
    target_stock: dict[str, Any],
    code: str,
    now: datetime,
    order_no: str,
) -> None:
    """Publish runtime terminal state only after durable DB completion."""

    try:
        POSITION_PEAK_LEDGER.remove_for_stock(target_stock)
    except Exception as exc:
        log_error(
            f"[SCALP_PEAK_LEDGER] {target_stock.get('name', code)}({code}) "
            f"cleanup failed after sell receipt: {exc}"
        )
    highest_prices.pop(code, None)
    target_stock["status"] = "COMPLETED"
    target_stock["sell_time"] = now.strftime("%H:%M:%S")
    if str(target_stock.get("position_tag") or "").strip().upper() == (
        OPENING_ROTATION_POSITION_TAG
    ):
        target_stock.update(
            {
                "opening_rotation_episode_phase": "COMPLETED",
                "opening_rotation_episode_completed_at": now.isoformat(),
                "opening_rotation_episode_terminal_reason": (
                    target_stock.get("last_exit_rule")
                    or (
                        "profit_target_filled"
                        if order_no
                        == str(
                            target_stock.get("opening_rotation_profit_target_order_no")
                            or ""
                        ).strip()
                        else "sell_receipt_completed"
                    )
                ),
                "opening_rotation_new_episode_blocked": False,
                "opening_rotation_order_ambiguity": False,
            }
        )
    probe_bundle_id = str(
        target_stock.get("entry_split_probe_bundle_id")
        or target_stock.get("entry_split_probe_exit_bundle_id")
        or ""
    ).strip()
    if probe_bundle_id:
        update_probe_runtime_bundle(
            probe_bundle_id,
            phase="complete",
            target_id=target_id,
            close_reason="position_sell_completed",
            sold_at=now.astimezone().isoformat() if now.tzinfo else now.isoformat(),
        )
    move_orders_to_terminal(target_stock, reason="sell_completed_cleanup")
    clear_sell_receipt_recovery(target_id)
    _clear_runtime_keys(target_stock, _SELL_COMPLETE_RESET_KEYS)
    target_stock.pop("pending_sell_msg", None)


def recover_final_sell_receipt(target_stock: dict[str, Any]) -> bool:
    """Finish a crash-surviving broker-final receipt from its exact journal."""

    state = target_stock.get(_SELL_EXECUTION_RECEIPT_STATE_KEY)
    if not isinstance(state, dict) or state.get("final_pending_db_commit") is not True:
        return False
    snapshot = state.get("finalization_receipt_snapshot")
    if not isinstance(snapshot, dict):
        return False
    target_id = _safe_int(target_stock.get("id"), 0)
    code = str(target_stock.get("code") or "").strip()[:6]
    try:
        now = datetime.fromisoformat(str(state.get("finalization_now_iso") or ""))
    except (TypeError, ValueError):
        return False
    exec_price = _safe_int(state.get("finalization_exec_price"), 0)
    strategy = str(state.get("finalization_strategy") or "KOSPI_ML")
    is_scalp_revive = bool(state.get("finalization_is_scalp_revive"))
    if target_id <= 0 or not code or exec_price <= 0:
        return False
    if not _update_db_for_sell(
        target_id,
        exec_price,
        now,
        dict(snapshot),
        strategy,
        is_scalp_revive,
    ):
        return False
    _complete_standard_sell_runtime_after_db(
        target_id=target_id,
        target_stock=target_stock,
        code=code,
        now=now,
        order_no=str(state.get("finalization_order_no") or ""),
    )
    return True


def _handle_nxt_rising_missed_tp1_partial_sell_execution(
    *,
    target_id: int,
    target_stock: dict[str, Any],
    code: str,
    order_no: str,
    exec_price: int,
    exec_qty: int,
    now: datetime,
    safe_buy_price: float,
    order_qty: int | None = None,
    remaining_qty: int | None = None,
    cumulative_exec_amount: int | None = None,
    execution_no: str = "",
    unit_exec_price: int | None = None,
    unit_exec_qty: int | None = None,
) -> None:
    requested_qty = max(
        0,
        _safe_int(target_stock.get("nxt_rising_missed_tp1_partial_requested_qty"), 0),
    )
    filled_before = max(
        0,
        _safe_int(target_stock.get("nxt_rising_missed_tp1_partial_filled_qty"), 0),
    )
    fill_amount_before = max(
        0,
        _safe_int(target_stock.get("nxt_rising_missed_tp1_partial_fill_amount"), 0),
    )
    executions = target_stock.get("nxt_rising_missed_tp1_partial_executions_by_no")
    executions = dict(executions) if isinstance(executions, dict) else {}
    signature = _execution_receipt_signature(
        cumulative_qty=exec_qty,
        order_qty=order_qty,
        remaining_qty=remaining_qty,
        cumulative_exec_amount=cumulative_exec_amount,
        unit_exec_price=unit_exec_price,
        unit_exec_qty=unit_exec_qty,
    )
    execution_conflict = _execution_number_conflict_reason(
        {str(order_no or "").strip(): executions},
        order_key=str(order_no or "").strip(),
        execution_no=execution_no,
        signature=signature,
    )
    if execution_conflict:
        log_error(
            f"[NXT_TP1_PARTIAL_RECEIPT_BLOCKED] {target_stock.get('name')}({code}) "
            f"reason={execution_conflict} ord_no={order_no or '-'}"
        )
        _request_broker_snapshot_refresh(
            code, reason="nxt_tp1_execution_number_conflict"
        )
        return
    receipt = _resolve_cumulative_buy_order_receipt(
        raw_price=exec_price,
        raw_cumulative_qty=exec_qty,
        requested_qty=requested_qty,
        previous_qty=filled_before,
        previous_amount=fill_amount_before,
        previous_economics_complete=True,
        order_qty=order_qty,
        remaining_qty=remaining_qty,
        cumulative_exec_amount=cumulative_exec_amount,
        unit_exec_price=unit_exec_price,
        unit_exec_qty=unit_exec_qty,
    )
    custody_contract_complete = bool(
        receipt.get("status") not in {"invalid", "duplicate"}
        and receipt.get("economics_complete") is True
        and receipt.get("quantity_contract_complete") is True
    )
    source_unit_contract_complete = bool(
        receipt.get("unit_fill_consistent") is True
        and unit_exec_price is not None
        and unit_exec_qty is not None
    )
    source_execution_identity_complete = bool(str(execution_no or "").strip())
    if receipt.get("status") == "duplicate":
        return
    if requested_qty <= 0 or not custody_contract_complete:
        log_error(
            f"[NXT_TP1_PARTIAL_RECEIPT_BLOCKED] {target_stock.get('name')}({code}) "
            f"reason={receipt.get('reason') or 'exact_contract_incomplete'} "
            f"requested={requested_qty} filled={filled_before} exec_qty={exec_qty}"
        )
        _request_broker_snapshot_refresh(code, reason="nxt_tp1_receipt_contract_gap")
        return
    effective_exec_qty = max(0, int(receipt.get("incremental_qty") or 0))
    effective_exec_amount = max(0, int(receipt.get("incremental_amount") or 0))
    effective_exec_price = float(receipt.get("incremental_price") or 0.0)
    if effective_exec_qty <= 0 or effective_exec_amount <= 0:
        return
    holder = {str(order_no or "").strip(): executions}
    if source_execution_identity_complete:
        _remember_execution_number(
            holder,
            order_key=str(order_no or "").strip(),
            execution_no=execution_no,
            signature=signature,
        )
    target_stock["nxt_rising_missed_tp1_partial_executions_by_no"] = holder[
        str(order_no or "").strip()
    ]
    partial_decision_price = _safe_float(target_stock.get("sell_target_price"), 0.0)
    partial_realized_net_pnl_krw = calculate_net_realized_pnl(
        safe_buy_price,
        effective_exec_price,
        effective_exec_qty,
    )
    partial_lifecycle_economics = _main_lifecycle_exit_economics_fields(
        target_stock,
        buy_price=safe_buy_price,
        sell_price=effective_exec_price,
        sell_qty=effective_exec_qty,
        realized_net_pnl_krw=partial_realized_net_pnl_krw,
        decision_price=partial_decision_price,
        decision_basis_source=("nxt_rising_missed_tp1_partial_sell_target_price"),
    )

    filled_qty = int(receipt["cumulative_qty"])
    fill_amount = int(receipt["cumulative_amount"])
    original_qty = max(
        requested_qty,
        _safe_int(
            target_stock.get("nxt_rising_missed_tp1_partial_original_qty"),
            target_stock.get("buy_qty"),
        ),
    )
    runner_qty = max(0, original_qty - filled_qty)
    target_stock["nxt_rising_missed_tp1_partial_filled_qty"] = filled_qty
    target_stock["nxt_rising_missed_tp1_partial_fill_amount"] = fill_amount
    target_stock["nxt_rising_missed_tp1_partial_avg_sell_price"] = _avg_from_totals(
        fill_amount,
        filled_qty,
    )
    target_stock["buy_qty"] = runner_qty
    target_stock["scale_in_locked"] = True
    target_stock["sell_partial_exit_carry_active"] = True
    cumulative_realized_pnl_krw = calculate_net_realized_pnl(
        safe_buy_price,
        fill_amount / filled_qty,
        filled_qty,
    )
    # Journal the in-flight TP1 order as well as the completed TP1 carry.  A
    # restart between cumulative packets must be able to reconstruct the
    # special partial-order consumer instead of leaving a locked DB position
    # with no replay target.
    target_stock[_SELL_EXECUTION_RECEIPT_STATE_KEY] = {
        "order_no": str(order_no or "").strip(),
        "position_qty": original_qty,
        "expected_qty": requested_qty,
        "cumulative_qty": filled_qty,
        "remaining_qty": runner_qty,
        "cumulative_amount": fill_amount,
        "cumulative_net_pnl_krw": round(cumulative_realized_pnl_krw, 4),
        "aggregate_cumulative_qty": filled_qty,
        "aggregate_cumulative_amount": fill_amount,
        "carried_qty": 0,
        "carried_amount": 0,
        "carried_net_pnl_krw": 0.0,
        "carried_economics_complete": True,
        "carried_quantity_contract_complete": True,
        "carried_unit_fill_consistent": source_unit_contract_complete,
        "prior_orders": {},
        "economics_complete": True,
        "quantity_contract_complete": True,
        "unit_fill_consistent": source_unit_contract_complete,
        "execution_identity_complete": source_execution_identity_complete,
        "final": False,
        "last_execution_no": str(execution_no or "").strip(),
        "executions_by_no": holder[str(order_no or "").strip()],
        "partial_order_kind": "nxt_rising_missed_tp1",
        "partial_order_requested_qty": requested_qty,
        "receipt_updated_at_epoch": time.time(),
    }
    target_stock["sell_reconciled_remaining_qty"] = runner_qty
    journal_persisted = _persist_sell_receipt_recovery_or_interlock(
        target_stock,
        code=code,
        reason="nxt_tp1_partial_fill_progress",
    )
    partial_completed = filled_qty >= requested_qty
    try:
        with DB.get_session() as session:
            record = (
                session.query(RecommendationHistory).filter_by(id=target_id).first()
            )
            if record:
                record.status = (
                    "HOLDING"
                    if partial_completed and journal_persisted
                    else "SELL_ORDERED"
                )
                record.scale_in_locked = True
    except Exception as exc:
        log_error(f"🚨 [DB 에러] ID {target_id} NXT TP1 체결수량 반영 실패: {exc}")

    if not partial_completed:
        _log_holding_pipeline(
            target_stock.get("name"),
            code,
            target_id,
            "nxt_rising_missed_tp1_partial_fill_progress",
            candidate_stock=target_stock,
            observed_at=now,
            observe_candidate_lifecycle=False,
            ord_no=order_no or "-",
            fill_qty=effective_exec_qty,
            filled_qty=filled_qty,
            requested_qty=requested_qty,
            runner_qty=runner_qty,
            fill_price=round(effective_exec_price, 4),
            execution_no=execution_no or "-",
            sell_receipt_economics_complete=True,
            sell_receipt_quantity_contract_complete=True,
            sell_receipt_unit_fill_consistent=source_unit_contract_complete,
            main_lifecycle_exit_qty=effective_exec_qty,
            main_lifecycle_exit_price=round(effective_exec_price, 4),
            **partial_lifecycle_economics,
            actual_order_submitted=True,
            broker_order_forbidden=False,
            runtime_effect=True,
            **_broker_execution_provenance_fields(target_stock),
        )
        return

    avg_sell_price = _safe_float(
        target_stock.get("nxt_rising_missed_tp1_partial_avg_sell_price"),
        effective_exec_price,
    )
    realized_profit_pct = (
        calculate_net_profit_rate(safe_buy_price, avg_sell_price)
        if safe_buy_price > 0
        else 0.0
    )
    realized_pnl_krw = calculate_net_realized_pnl(
        safe_buy_price, avg_sell_price, filled_qty
    )
    prior_order = {
        "expected_qty": requested_qty,
        "cumulative_qty": filled_qty,
        "cumulative_amount": fill_amount,
        "remaining_qty": 0,
        "economics_complete": True,
        "quantity_contract_complete": True,
        "unit_fill_consistent": source_unit_contract_complete,
        "execution_identity_complete": source_execution_identity_complete,
        "executions_by_no": holder[str(order_no or "").strip()],
    }
    target_stock[_SELL_EXECUTION_RECEIPT_STATE_KEY] = {
        "order_no": "",
        "position_qty": original_qty,
        "expected_qty": 0,
        "cumulative_qty": 0,
        "remaining_qty": runner_qty,
        "cumulative_amount": 0,
        "cumulative_net_pnl_krw": round(realized_pnl_krw, 4),
        "aggregate_cumulative_qty": filled_qty,
        "aggregate_cumulative_amount": fill_amount,
        "carried_qty": filled_qty,
        "carried_amount": fill_amount,
        "carried_net_pnl_krw": round(realized_pnl_krw, 4),
        "carried_economics_complete": True,
        "carried_quantity_contract_complete": True,
        "carried_unit_fill_consistent": source_unit_contract_complete,
        "prior_orders": {str(order_no or "").strip(): prior_order},
        "economics_complete": True,
        "quantity_contract_complete": True,
        "unit_fill_consistent": source_unit_contract_complete,
        "execution_identity_complete": source_execution_identity_complete,
        "final": False,
        "last_execution_no": "",
        "executions_by_no": {},
        "partial_order_kind": "nxt_rising_missed_tp1",
        "partial_order_requested_qty": requested_qty,
        "receipt_updated_at_epoch": time.time(),
    }
    target_stock["sell_reconciled_remaining_qty"] = runner_qty
    carried_journal_persisted = _persist_sell_receipt_recovery_or_interlock(
        target_stock,
        code=code,
        reason="nxt_tp1_partial_fill_completed",
    )
    if not carried_journal_persisted:
        target_stock["status"] = "SELL_ORDERED"
        target_stock["nxt_rising_missed_tp1_partial_pending"] = False
        target_stock["nxt_rising_missed_tp1_partial_applied"] = False
        return
    try:
        with DB.get_session() as session:
            record = (
                session.query(RecommendationHistory).filter_by(id=target_id).first()
            )
            if record:
                record.status = "HOLDING"
                record.scale_in_locked = True
    except Exception as exc:
        target_stock.update(
            {
                "status": "SELL_ORDERED",
                "sell_cancel_reconciliation_required": True,
                "sell_cancel_reconciliation_source": (
                    "nxt_tp1_carried_db_status_commit_failed"
                ),
            }
        )
        log_error(
            f"[NXT_TP1_CARRY_DB_COMMIT_BLOCKED] "
            f"{target_stock.get('name')}({code}) id={target_id}: {exc}"
        )
        return
    target_stock["status"] = "HOLDING"
    target_stock["nxt_rising_missed_tp1_partial_pending"] = False
    target_stock["nxt_rising_missed_tp1_partial_applied"] = True
    target_stock["nxt_rising_missed_tp1_partial_completed_at"] = now.timestamp()
    target_stock["nxt_rising_missed_tp1_partial_realized_profit_pct"] = round(
        realized_profit_pct,
        6,
    )
    target_stock["nxt_rising_missed_tp1_partial_realized_pnl_krw"] = realized_pnl_krw
    target_stock.pop("sell_odno", None)
    target_stock.pop("sell_order_time", None)
    target_stock.pop("sell_target_price", None)
    pending_msg = str(target_stock.pop("pending_sell_msg", "") or "")

    _log_holding_pipeline(
        target_stock.get("name"),
        code,
        target_id,
        "nxt_rising_missed_tp1_partial_sell_completed",
        candidate_stock=target_stock,
        observed_at=now,
        observe_candidate_lifecycle=False,
        ord_no=order_no or "-",
        execution_no=execution_no or "-",
        sell_price=avg_sell_price,
        sold_qty=filled_qty,
        main_lifecycle_exit_qty=effective_exec_qty,
        main_lifecycle_exit_price=round(effective_exec_price, 4),
        sell_receipt_economics_complete=True,
        sell_receipt_quantity_contract_complete=True,
        sell_receipt_unit_fill_consistent=source_unit_contract_complete,
        **partial_lifecycle_economics,
        runner_qty=runner_qty,
        realized_profit_pct=f"{realized_profit_pct:+.2f}",
        realized_pnl_krw=realized_pnl_krw,
        exit_rule="nxt_rising_missed_tp1_partial_runner",
        actual_order_submitted=True,
        runtime_effect=True,
        decision_authority="nxt_rising_missed_tp1_partial_runner_canary",
        **_broker_execution_provenance_fields(target_stock),
    )
    log_info(
        f"[NXT_TP1_PARTIAL_COMPLETED] {target_stock.get('name')}({code}) "
        f"sold={filled_qty} runner={runner_qty} avg_sell={avg_sell_price} "
        f"profit={realized_profit_pct:+.2f}%"
    )
    if event_bus:
        event_bus.publish(
            "TELEGRAM_BROADCAST",
            {
                "message": (
                    f"{pending_msg}\n"
                    f"✅ **부분익절 체결:** `{avg_sell_price:,}원` "
                    f"(`{realized_profit_pct:+.2f}%`)\n"
                    f"🏃 runner: `{runner_qty}주`"
                ),
                "audience": _receipt_audience(target_stock),
                "parse_mode": "HTML",
            },
        )


def _handle_scalp_revive_sell_execution(
    *,
    target_id: int,
    target_stock: dict[str, Any],
    code: str,
    exec_price: int,
    exec_qty: int,
    now: datetime,
    profit_rate: float,
    safe_buy_price: float,
    strategy: str,
    sell_receipt: dict[str, Any],
    order_no: str = "",
) -> bool:
    if sell_receipt.get("status") != "final" or sell_receipt.get("final") is not True:
        return False
    revived_position_tag = normalize_position_tag(
        "SCALPING",
        target_stock.get("position_tag")
        or default_position_tag_for_strategy("SCALPING"),
    )
    try:
        with DB.get_session() as session:
            record = (
                session.query(RecommendationHistory).filter_by(id=target_id).first()
            )
            if not record:
                return False
            prior_status = str(getattr(record, "status", "") or "").strip().upper()
            if prior_status == "COMPLETED":
                return bool(
                    record.sell_time and _safe_float(record.sell_price, 0.0) > 0
                )
            if prior_status not in {"HOLDING", "SELL_ORDERED"}:
                log_error(
                    f"[SELL_RECEIPT_DB_RECONCILE_BLOCKED] ID {target_id} "
                    f"unexpected_status={prior_status or '-'}"
                )
                return False
            position_buy_qty = int(
                float(
                    getattr(record, "buy_qty", 0) or target_stock.get("buy_qty", 0) or 0
                )
            )
            completed_sell_qty = int(sell_receipt.get("cumulative_qty") or 0)
            if position_buy_qty <= 0 or completed_sell_qty != position_buy_qty:
                log_error(
                    f"[SCALP_REVIVE_SELL_RECONCILE_BLOCKED] {code} "
                    f"filled={completed_sell_qty} position={position_buy_qty}"
                )
                return False
            completed_sell_amount = int(sell_receipt.get("cumulative_amount") or 0)
            position_weighted_sell_price = int(
                round(completed_sell_amount / completed_sell_qty)
            )
            realized_pnl_krw = float(sell_receipt.get("cumulative_net_pnl_krw") or 0.0)
            profit_rate = (
                realized_pnl_krw / (safe_buy_price * completed_sell_qty) * 100.0
                if safe_buy_price > 0
                else 0.0
            )
            record.status = "COMPLETED"
            record.sell_price = position_weighted_sell_price
            record.sell_time = now
            record.profit_rate = profit_rate
            log_info(
                f"🎉 [매매 완료: ID {target_id}] {code} "
                f"실매도가: {position_weighted_sell_price:,}원 / 수익률: {profit_rate}%"
            )

            new_record = RecommendationHistory(
                rec_date=now.date(),
                stock_code=code,
                stock_name=record.stock_name,
                buy_price=0,
                status="WATCHING",
                strategy="SCALPING",
                trade_type="SCALP",
                position_tag=revived_position_tag,
                prob=record.prob,
            )
            session.add(new_record)
            session.flush()
            new_watch_id = new_record.id
            # Persist both the completed position and its replacement WATCHING
            # row before publishing any completion evidence.
            session.commit()

            _publish_sell_execution_message(
                name=target_stock.get("name") or "-",
                pending_msg=target_stock.get("pending_sell_msg") or "",
                audience=_receipt_audience(target_stock),
                exec_price=position_weighted_sell_price,
                profit_rate=profit_rate,
            )
            final_leg_qty = int(sell_receipt.get("incremental_qty") or 0)
            final_leg_price = float(sell_receipt.get("incremental_price") or 0.0)
            final_leg_net_pnl = float(
                sell_receipt.get("incremental_net_pnl_krw") or 0.0
            )
            final_leg_economics = (
                _main_lifecycle_exit_economics_fields(
                    target_stock,
                    buy_price=safe_buy_price,
                    sell_price=final_leg_price,
                    sell_qty=final_leg_qty,
                    realized_net_pnl_krw=final_leg_net_pnl,
                )
                if sell_receipt.get("economics_complete") is True
                else {}
            )
            _log_holding_pipeline(
                target_stock.get("name"),
                code,
                target_id,
                "sell_completed",
                candidate_stock=target_stock,
                observed_at=now,
                order_no=str(order_no or "").strip() or "-",
                execution_no=sell_receipt.get("execution_no") or "-",
                metric_role="execution_quality_real_only",
                decision_authority="broker_sell_fill_observation_only",
                window_policy="same_position_cycle_broker_fill",
                sample_floor="1_confirmed_broker_sell_fill",
                primary_decision_metric="confirmed_sell_fill_price_and_profit_rate",
                source_quality_gate=(
                    "broker_execution_receipt_with_real_submission_provenance"
                ),
                runtime_effect=True,
                actual_order_submitted=True,
                broker_order_forbidden=False,
                forbidden_uses=(
                    "threshold_mutation|provider_route_change|quantity_cap_release|"
                    "broker_guard_bypass|bot_restart"
                ),
                sell_price=position_weighted_sell_price,
                sell_qty=completed_sell_qty,
                main_lifecycle_exit_qty=final_leg_qty,
                main_lifecycle_exit_price=round(final_leg_price, 4),
                main_lifecycle_broker_reconciled=True,
                main_lifecycle_reconciled_final_exit=True,
                buy_price=f"{safe_buy_price:.2f}",
                buy_qty=position_buy_qty,
                realized_pnl_krw=realized_pnl_krw,
                realized_pnl_krw_source="broker_fill_prices_fee_aware",
                profit_rate=f"{profit_rate:+.2f}",
                exit_rule=target_stock.get("last_exit_rule") or "-",
                exit_decision_source=target_stock.get("last_exit_decision_source")
                or "MANUAL",
                revive=True,
                new_watch_id=int(new_watch_id or 0),
                **_broker_execution_provenance_fields(target_stock),
                **_trailing_continuation_receipt_fields(target_stock),
                **final_leg_economics,
                **scout_ai_execution_attribution_fields(
                    target_stock,
                    stage="sell_completed",
                    actual_order_submitted=True,
                ),
            )
            try:
                record_post_sell_candidate(
                    recommendation_id=target_id,
                    stock=target_stock,
                    code=code,
                    sell_time=now,
                    buy_price=safe_buy_price,
                    sell_price=position_weighted_sell_price,
                    profit_rate=profit_rate,
                    buy_qty=int(
                        float(
                            getattr(record, "buy_qty", 0)
                            or target_stock.get("buy_qty", 0)
                            or 0
                        )
                    ),
                    exit_rule=target_stock.get("last_exit_rule") or "-",
                    strategy=strategy,
                    revive=True,
                    peak_profit=target_stock.get("last_exit_peak_profit"),
                    held_sec=target_stock.get("last_exit_held_sec"),
                    current_ai_score=target_stock.get("last_exit_current_ai_score"),
                    soft_stop_threshold_pct=target_stock.get(
                        "last_exit_soft_stop_threshold_pct"
                    ),
                    same_symbol_soft_stop_cooldown_would_block=target_stock.get(
                        "last_exit_same_symbol_soft_stop_cooldown_would_block"
                    ),
                )
            except Exception as exc:
                log_error(
                    f"[POST_SELL] candidate record failed (id={target_id}): {exc}"
                )
    except Exception as e:
        log_error(f"🚨 [DB 에러] ID {target_id} SELL 처리 중 에러: {e}")
        return False

    _apply_scalp_revive_memory_state(
        target_stock=target_stock,
        code=code,
        new_watch_id=new_watch_id,
        revived_position_tag=revived_position_tag,
        revived_at_ts=now.timestamp(),
    )
    clear_sell_receipt_recovery(target_id)
    return True


def _apply_scalp_revive_memory_state(
    *,
    target_stock: dict[str, Any],
    code: str,
    new_watch_id: int,
    revived_position_tag: str,
    revived_at_ts: float | None = None,
) -> None:
    try:
        POSITION_PEAK_LEDGER.remove_for_stock(target_stock)
    except Exception as exc:
        log_error(
            f"[SCALP_PEAK_LEDGER] {target_stock.get('name', code)}({code}) "
            f"cleanup failed before revive: {exc}"
        )
    highest_prices.pop(code, None)
    target_stock["id"] = new_watch_id
    target_stock["status"] = "WATCHING"
    target_stock["buy_price"] = 0
    target_stock["buy_qty"] = 0
    target_stock["added_time"] = time.time()
    target_stock["position_tag"] = revived_position_tag
    # Prevent a pre-sell WS snapshot from becoming the revived watcher's entry input.
    target_stock["_scalp_revive_min_quote_ts"] = float(
        revived_at_ts if revived_at_ts is not None else time.time()
    )
    move_orders_to_terminal(target_stock, reason="sell_revive_cleanup")
    _clear_runtime_keys(target_stock, _SELL_REVIVE_RESET_KEYS)


def _clear_split_entry_shadow_state(target_stock: dict[str, Any]) -> None:
    for key in [
        "_split_entry_rebase_shadow_count",
        "_split_entry_rebase_shadow_last_second",
        "_split_entry_rebase_shadow_same_second_count",
        "_split_entry_first_partial_qty",
        "_split_entry_last_immediate_recheck_rebase_count",
    ]:
        target_stock.pop(key, None)


def _prepare_new_position_exit_authority(
    target_stock: dict[str, Any],
    *,
    code: str,
    target_id: int,
    order_no: str,
) -> None:
    """Fail closed when a fresh BUY fill races unresolved exit authority."""
    active_fields = (
        "exit_requested",
        "exit_order_type",
        "exit_order_time",
        "exit_token",
        "exit_decided_at",
        "exit_order_sent_at",
        "sell_odno",
        "sell_ord_no",
        "sell_order_time",
        "pending_sell_msg",
        "fast_exit_retry_pending",
        "fast_exit_retry_reason",
        "fast_exit_retry_at",
        "fast_exit_last_error",
        "fast_exit_trigger_kind",
        "fast_exit_rest_retry_after",
        *_FAST_EXIT_DECISION_RESET_KEYS,
        *_EXIT_DECISION_RESET_KEYS,
    )
    conflict_fields = [
        key for key in active_fields if target_stock.get(key) not in (None, "", False)
    ]
    if not conflict_fields:
        target_stock.pop("entry_lifecycle_conflict", None)
        target_stock.pop("entry_lifecycle_conflict_fields", None)
        target_stock["exit_requested"] = False
        return

    previous_status = str(target_stock.get("status") or "").strip().upper()
    target_stock.update(
        {
            "entry_lifecycle_conflict": True,
            "entry_lifecycle_conflict_fields": ",".join(conflict_fields),
            "probe_expand_forbidden": True,
            "entry_split_probe_residual_expand_forbidden": True,
            "entry_split_probe_scale_in_forbidden": True,
        }
    )
    _log_holding_pipeline(
        target_stock.get("name"),
        code,
        target_id,
        "entry_position_cycle_exit_authority_conflict",
        previous_status=previous_status or "-",
        previous_exit_token=str(target_stock.get("exit_token") or "-"),
        conflict_fields=",".join(conflict_fields),
        unresolved_exit_authority_field_count=len(conflict_fields),
        entry_order_no=order_no or "-",
        metric_role="safety_veto",
        decision_authority="broker_buy_fill_position_cycle_integrity_fail_closed",
        window_policy="before_probe_residual_callback",
        sample_floor="confirmed_fresh_buy_fill_with_zero_pre_fill_qty",
        primary_decision_metric="unresolved_exit_authority_field_count",
        source_quality_gate="broker_buy_execution_receipt_and_unresolved_exit_state",
        runtime_effect=True,
        actual_order_submitted=True,
        broker_order_forbidden=False,
        forbidden_uses=(
            "active_sell_state_clear|residual_or_scale_in_submit|hard_stop_bypass|"
            "broker_guard_bypass|provider_route_change|quantity_or_cap_change"
        ),
    )


def _find_buy_bundle_match(code: str, normalized_order_no: str):
    return next(
        (
            stock
            for stock in ACTIVE_TARGETS
            if str(stock.get("code", "")).strip()[:6] == code
            and str(stock.get("status", "") or "").strip().upper()
            in {"WATCHING", "BUY_ORDERED", "HOLDING"}
            and any(
                str(order.get("ord_no", "") or "").strip() == normalized_order_no
                for order in (stock.get("pending_entry_orders") or [])
            )
        ),
        None,
    )


def _find_terminal_entry_target(normalized_order_no: str):
    terminal_match = get_terminal_entry_order(normalized_order_no)
    if not terminal_match:
        return None
    stock_code = str(terminal_match.get("stock_code", "") or "").strip()[:6]
    terminal_target_id = str(terminal_match.get("target_id", "") or "").strip()
    if not terminal_target_id:
        return None
    return next(
        (
            stock
            for stock in ACTIVE_TARGETS
            if str(stock.get("code", "")).strip()[:6] == stock_code
            and str(stock.get("id", "") or "").strip() == terminal_target_id
            and str(stock.get("status", "") or "").strip().upper()
            in {"WATCHING", "BUY_ORDERED", "HOLDING"}
        ),
        None,
    )


def _find_add_order_match(code: str, normalized_order_no: str):
    def _pending_add_ord_nos(stock: dict) -> set[str]:
        raw = str(stock.get("pending_add_ord_no", "") or "").strip()
        return {part.strip() for part in raw.split(",") if part.strip()}

    return next(
        (
            stock
            for stock in ACTIVE_TARGETS
            if str(stock.get("code", "")).strip()[:6] == code
            and bool(stock.get("pending_add_order"))
            and normalized_order_no in _pending_add_ord_nos(stock)
        ),
        None,
    )


def _find_execution_target(
    code,
    exec_type,
    order_no,
    *,
    order_qty=None,
    remaining_qty=None,
    cumulative_exec_qty=None,
):
    """실제체결 대상 runtime truth 매칭.

    BUY 우선순위:
    1) split-entry bundle ord_no exact
    2) terminal entry order exact
    3) BUY_ORDERED status + odno exact
    4) HOLDING pending_add_order + pending_add_ord_no exact
    5) 단일 HOLDING pending_add candidate (order_no 없음)
    6) 단일 BUY_ORDERED candidate

    SELL 우선순위:
    1) SELL_ORDERED status + sell_odno exact
    2) 단일 SELL_ORDERED candidate
    """
    normalized_order_no = str(order_no or "").strip()

    if exec_type == "BUY":
        if normalized_order_no:
            bundle_match = _find_buy_bundle_match(code, normalized_order_no)
            if bundle_match:
                return bundle_match

            target = _find_terminal_entry_target(normalized_order_no)
            if target:
                return target

        status_key = "BUY_ORDERED"
        order_key = "odno"
    else:
        if normalized_order_no:
            receipt_ledger_matches = []
            for stock in ACTIVE_TARGETS:
                if str(stock.get("code", "")).strip()[:6] != code:
                    continue
                receipt_state = stock.get(_SELL_EXECUTION_RECEIPT_STATE_KEY)
                if not isinstance(receipt_state, dict):
                    continue
                prior_orders = receipt_state.get("prior_orders")
                known_receipt_orders = {
                    str(receipt_state.get("order_no") or "").strip()
                }
                if isinstance(prior_orders, dict):
                    known_receipt_orders.update(
                        str(item or "").strip() for item in prior_orders
                    )
                if normalized_order_no in known_receipt_orders:
                    receipt_ledger_matches.append(stock)
            if len(receipt_ledger_matches) == 1:
                return receipt_ledger_matches[0]
        opening_target_candidates = [
            stock
            for stock in ACTIVE_TARGETS
            if str(stock.get("code", "")).strip()[:6] == code
            and str(stock.get("position_tag") or "").strip().upper()
            == OPENING_ROTATION_POSITION_TAG
            and str(stock.get("status") or "").strip().upper() == "HOLDING"
        ]
        if normalized_order_no:
            opening_exact = next(
                (
                    stock
                    for stock in opening_target_candidates
                    if normalized_order_no
                    in {
                        str(
                            stock.get("opening_rotation_profit_target_order_no") or ""
                        ).strip(),
                        str(stock.get("preset_tp_ord_no") or "").strip(),
                    }
                ),
                None,
            )
            if opening_exact:
                return opening_exact
        opening_submitting = [
            stock
            for stock in opening_target_candidates
            if bool(stock.get("opening_rotation_profit_target_submit_pending"))
        ]
        if not normalized_order_no and len(opening_submitting) == 1:
            return opening_submitting[0]
        status_key = "SELL_ORDERED"
        order_key = "sell_odno"

    status_candidates = [
        stock
        for stock in ACTIVE_TARGETS
        if str(stock.get("code", "")).strip()[:6] == code
        and stock.get("status") == status_key
    ]

    if normalized_order_no:
        exact_match = next(
            (
                stock
                for stock in status_candidates
                if str(stock.get(order_key, "")).strip() == normalized_order_no
            ),
            None,
        )
        if exact_match:
            return exact_match

        if exec_type == "BUY":
            add_match = _find_add_order_match(code, normalized_order_no)
            if add_match:
                return add_match

    if exec_type == "BUY":
        pending_add_candidates = [
            stock
            for stock in ACTIVE_TARGETS
            if str(stock.get("code", "")).strip()[:6] == code
            and bool(stock.get("pending_add_order"))
            and stock.get("status") == "HOLDING"
        ]
        if len(pending_add_candidates) == 1:
            return pending_add_candidates[0]

    # A broker-provided SELL order number must match the current order or the
    # preserved receipt ledger exactly.  Falling back by symbol can attach a
    # delayed receipt from an older order/generation to the live position.
    if exec_type == "SELL" and normalized_order_no:
        submit_pending_candidates = [
            stock
            for stock in status_candidates
            if bool(stock.get("sell_submit_pending"))
            and _safe_int(stock.get("sell_submit_requested_qty"), 0) > 0
        ]
        if len(submit_pending_candidates) == 1:
            candidate = submit_pending_candidates[0]
            requested_qty = _safe_int(candidate.get("sell_submit_requested_qty"), 0)
            official_qty = _safe_int(order_qty, 0)
            official_remaining = (
                _safe_int(remaining_qty, -1) if remaining_qty is not None else -1
            )
            official_cumulative = _safe_int(cumulative_exec_qty, 0)
            if (
                official_qty == requested_qty
                and official_remaining >= 0
                and official_cumulative > 0
                and official_cumulative + official_remaining == official_qty
            ):
                return candidate
        return None

    if len(status_candidates) == 1:
        return status_candidates[0]

    return None


def _execution_ignore_context(code: str, exec_type: str, order_no: str) -> str:
    normalized_order_no = str(order_no or "").strip()
    matching_code_targets = [
        stock
        for stock in ACTIVE_TARGETS
        if str((stock or {}).get("code", "")).strip()[:6] == code
    ]
    target_summaries = []
    for stock in matching_code_targets[:5]:
        pending_orders = stock.get("pending_entry_orders") or []
        pending_ord_nos = [
            str(order.get("ord_no", "") or "").strip() or "-"
            for order in pending_orders[:3]
        ]
        pending_add_ord_no = str(stock.get("pending_add_ord_no", "") or "-")
        target_summaries.append(
            "{status}:odno={odno}:sell_odno={sell_odno}:pending={pending}:pending_add={pending_add}".format(
                status=str(stock.get("status", "") or "-"),
                odno=str(stock.get("odno", "") or "-"),
                sell_odno=str(stock.get("sell_odno", "") or "-"),
                pending="|".join(pending_ord_nos) if pending_ord_nos else "-",
                pending_add=pending_add_ord_no,
            )
        )
    terminal_present = False
    if exec_type == "BUY" and normalized_order_no:
        terminal_present = get_terminal_entry_order(normalized_order_no) is not None
    return (
        f"active_code_targets={len(matching_code_targets)} "
        f"target_context={';'.join(target_summaries) if target_summaries else '-'} "
        f"terminal_entry_bridge={terminal_present}"
    )


def _find_order_notice_target(code, exec_type, order_no):
    """Resolve notices only against an order identity already owned locally.

    ORDER_NOTICE does not include the 900/902 quantity pair.  It therefore
    cannot safely bind a blank entry/add leg by symbol before ORDER_EXECUTED.
    """

    normalized_order_no = str(order_no or "").strip()
    if not normalized_order_no:
        return None
    if exec_type == "BUY":
        for finder in (
            _find_buy_bundle_match,
            _find_add_order_match,
        ):
            target = finder(code, normalized_order_no)
            if target:
                return target
        target = _find_terminal_entry_target(normalized_order_no)
        if target and str(target.get("code") or "").strip()[:6] == code:
            return target
        exact = [
            stock
            for stock in ACTIVE_TARGETS
            if str(stock.get("code", "")).strip()[:6] == code
            and str(stock.get("odno", "") or "").strip() == normalized_order_no
            and str(stock.get("status", "") or "").strip().upper()
            in {"BUY_ORDERED", "HOLDING"}
        ]
        return exact[0] if len(exact) == 1 else None
    if exec_type == "SELL":
        exact = [
            stock
            for stock in ACTIVE_TARGETS
            if str(stock.get("code", "")).strip()[:6] == code
            and normalized_order_no
            in {
                str(stock.get("sell_odno", "") or "").strip(),
                str(stock.get("sell_ord_no", "") or "").strip(),
                str(stock.get("opening_rotation_profit_target_order_no") or "").strip(),
                str(stock.get("preset_tp_ord_no", "") or "").strip(),
            }
        ]
        return exact[0] if len(exact) == 1 else None
    return None


def _apply_order_notice_to_target(
    target_stock,
    *,
    code,
    exec_type,
    order_no,
    status,
    broker_reject_reason_raw="",
    broker_execution_time_raw="",
):
    changed = False

    if exec_type == "BUY":
        if (
            bool(target_stock.get("pending_add_order"))
            and str(target_stock.get("status") or "") == "HOLDING"
        ):
            if order_no in set(_pending_add_order_numbers(target_stock)):
                notices = target_stock.get("pending_add_notice_by_order_no")
                if not isinstance(notices, dict):
                    notices = {}
                    target_stock["pending_add_notice_by_order_no"] = notices
                notices[str(order_no)] = {
                    "status": status,
                    "notice_at": time.time(),
                    "broker_reject_reason_raw": broker_reject_reason_raw,
                    "broker_execution_time_raw": broker_execution_time_raw,
                }
                changed = True
            if changed:
                log_info(
                    f"[ORDER_NOTICE_BOUND] {target_stock.get('name')}({code}) "
                    f"type={exec_type} status={status} order_no={order_no}"
                )
            return

        pending_orders = [
            pending_order
            for pending_order in (target_stock.get("pending_entry_orders") or [])
            if isinstance(pending_order, dict)
        ]
        exact_match = None
        for order in pending_orders:
            existing_ord_no = str(order.get("ord_no", "") or "").strip()
            if existing_ord_no == order_no:
                exact_match = order
                break
        target_order = exact_match
        if target_order:
            target_order["notice_status"] = status
            target_order["notice_at"] = time.time()
            target_order["notice_broker_reject_reason_raw"] = (
                broker_reject_reason_raw
            )
            target_order["notice_broker_execution_time_raw"] = (
                broker_execution_time_raw
            )
            changed = True

        known_target_order_no = str(target_stock.get("odno", "") or "").strip()
        if order_no == known_target_order_no:
            target_stock["entry_order_notice_status"] = status
            target_stock["entry_order_notice_at"] = time.time()
            target_stock["entry_order_notice_broker_reject_reason_raw"] = (
                broker_reject_reason_raw
            )
            target_stock["entry_order_notice_broker_execution_time_raw"] = (
                broker_execution_time_raw
            )
            changed = True

    elif exec_type == "SELL":
        target_stock["last_sell_order_notice_status"] = status
        target_stock["last_sell_order_notice_at"] = time.time()
        target_stock["last_sell_order_notice_broker_reject_reason_raw"] = (
            broker_reject_reason_raw
        )
        target_stock["last_sell_order_notice_broker_execution_time_raw"] = (
            broker_execution_time_raw
        )
        changed = True
        if (
            str(target_stock.get("position_tag") or "").strip().upper()
            == OPENING_ROTATION_POSITION_TAG
            and str(target_stock.get("status") or "").strip().upper() == "HOLDING"
            and (
                target_stock.get("opening_rotation_profit_target_submit_pending")
                or order_no
                == str(
                    target_stock.get("opening_rotation_profit_target_order_no") or ""
                )
            )
        ):
            target_stock["opening_rotation_profit_target_order_no"] = order_no
            target_stock["preset_tp_ord_no"] = order_no
            target_stock["opening_rotation_profit_target_notice_status"] = status
            target_stock["opening_rotation_profit_target_notice_at"] = time.time()
            changed = True
        elif order_no and not str(target_stock.get("sell_odno", "") or "").strip():
            target_stock["sell_odno"] = order_no
            changed = True

    if changed:
        log_info(
            f"[ORDER_NOTICE_BOUND] {target_stock.get('name')}({code}) "
            f"type={exec_type} status={status} order_no={order_no}"
        )


def _avg_from_totals(total_amount: float, total_qty: int) -> float:
    if total_qty <= 0:
        return 0.0
    return round(float(total_amount) / float(total_qty), 4)


def weighted_avg_price(old_price, old_qty, exec_price, exec_qty):
    if old_qty <= 0:
        return exec_price
    return _avg_from_totals(
        (old_price * old_qty) + (exec_price * exec_qty), old_qty + exec_qty
    )


def handle_order_notice(notice_data):
    code = str(notice_data.get("code", "") or "").strip()[:6]
    exec_type = str(notice_data.get("type", "") or "").upper()
    order_no = str(notice_data.get("order_no", "") or "").strip()
    status = str(notice_data.get("status", "") or "").strip()
    broker_reject_reason_raw = str(
        notice_data.get("broker_reject_reason_raw", "") or ""
    ).strip()
    broker_execution_time_raw = str(
        notice_data.get("broker_execution_time_raw", "") or ""
    ).strip()

    if not code or exec_type not in {"BUY", "SELL"} or not order_no:
        return

    with _active_state_lock():
        target_stock = _find_order_notice_target(code, exec_type, order_no)
        if not target_stock:
            return
        _apply_order_notice_to_target(
            target_stock,
            code=code,
            exec_type=exec_type,
            order_no=order_no,
            status=status,
            broker_reject_reason_raw=broker_reject_reason_raw,
            broker_execution_time_raw=broker_execution_time_raw,
        )

    if status == "거부":
        raw_fields = notice_data.get("broker_execution_raw_fields")
        raw_fields = raw_fields if isinstance(raw_fields, dict) else {}
        _log_holding_pipeline(
            target_stock.get("name") or "-",
            code,
            target_stock.get("id"),
            "broker_order_notice_rejected",
            candidate_stock=target_stock,
            observe_candidate_lifecycle=False,
            order_side=exec_type,
            broker_order_no=order_no,
            broker_order_notice_status=status,
            broker_reject_reason_raw=broker_reject_reason_raw or "-",
            broker_reject_reason_source=(
                "official_fid_919"
                if broker_reject_reason_raw
                else "official_fid_919_missing"
            ),
            broker_execution_time_raw=broker_execution_time_raw or "-",
            **{
                key: raw_fields.get(key)
                for key in _BROKER_EXECUTION_RAW_FIELD_KEYS
            },
            metric_role="execution_quality_real_only",
            decision_authority="broker_order_receipt_provenance_only",
            window_policy="same_exact_broker_order_notice",
            sample_floor="one_official_00_rejected_notice",
            primary_decision_metric="broker_order_reject_reason_raw",
            source_quality_gate="official_type_00_status_and_fid919_preserved_raw",
            runtime_effect=False,
            allowed_runtime_apply=False,
            actual_order_submitted=True,
            broker_order_forbidden=False,
            forbidden_uses=(
                "automatic_retry|quantity_change|route_change|threshold_change|"
                "provider_change|broker_guard_bypass"
            ),
        )


def _clear_pending_add_meta(target_stock):
    _clear_runtime_keys(target_stock, _PENDING_ADD_META_KEYS)


def _apply_scale_in_protection(target_stock, add_type):
    """추가매수 체결 후 보호선 보정(1차 단순 버전)."""
    try:
        raw_strategy = (target_stock.get("strategy") or "KOSPI_ML").upper()
        strategy = "SCALPING" if raw_strategy in ["SCALPING", "SCALP"] else raw_strategy
        avg_price = float(target_stock.get("buy_price") or 0)
        if avg_price <= 0:
            return False

        if add_type == "PYRAMID":
            if strategy == "SCALPING":
                protect_price = avg_price * 1.003
            else:
                protect_price = avg_price * 1.01

            existing = float(target_stock.get("trailing_stop_price") or 0)
            target_stock["trailing_stop_price"] = max(existing, protect_price)
        elif add_type == "AVG_DOWN":
            target_stock.pop("soft_stop_micro_grace_started_at", None)
            target_stock.pop("soft_stop_micro_grace_extension_used", None)
            target_stock["soft_stop_reset_after_avg_down"] = True
        return True
    except Exception as e:
        log_error(f"⚠️ [ADD_PROTECT] 보호선 보정 실패: {e}")
        return False


def _is_ok_response(res):
    if not isinstance(res, dict):
        return bool(res)
    return str(res.get("return_code", res.get("rt_cd", ""))) == "0"


def _extract_order_no(response: Any) -> str:
    if not isinstance(response, dict):
        return ""
    for key in ("ord_no", "odno", "order_no"):
        value = str(response.get(key) or "").strip()
        if value:
            return value
    return ""


def _submit_opening_rotation_profit_order(
    target_stock: dict[str, Any],
    *,
    code: str,
    buy_fill_price: int,
    filled_qty: int,
) -> bool:
    """Place the protected one-share target only after the BUY fill receipt."""

    invalid_fill = False
    # Execution notices may be duplicated or delivered concurrently. Claim
    # target submission under the shared state lock before price calculation
    # or broker I/O so only one BUY receipt can own the sell-side transition.
    with _active_state_lock():
        if str(target_stock.get("position_tag") or "").strip().upper() != (
            OPENING_ROTATION_POSITION_TAG
        ):
            return False
        if str(
            target_stock.get("opening_rotation_profit_target_order_no") or ""
        ).strip():
            return True
        if target_stock.get("opening_rotation_profit_target_submit_pending"):
            return True
        if target_stock.get("opening_rotation_profit_order_protection_failed"):
            return False
        if filled_qty != 1 or buy_fill_price <= 0:
            invalid_fill = True
            target_stock.update(
                {
                    "opening_rotation_profit_order_protection_failed": True,
                    "opening_rotation_new_episode_blocked": True,
                    "opening_rotation_episode_phase": "TARGET_BLOCKED_INVARIANT",
                    "scale_in_locked": True,
                }
            )
        else:
            target_stock["opening_rotation_profit_target_submit_pending"] = True
    if invalid_fill:
        log_error(
            f"[OPENING_ROTATION_TARGET_BLOCK] {target_stock.get('name')}({code}) "
            f"fill_price={buy_fill_price} qty={filled_qty} expected_qty=1"
        )
        return False

    from src.engine import kiwoom_orders

    try:
        trade_cost_rate = get_trade_cost_rate()
        # Resolve the KRX price band from the unrounded target, not the fill. A
        # target can cross a tick-band boundary even when the fill did not.
        raw_target_price = opening_rotation_profit_target_price(
            buy_fill_price,
            trade_cost_rate=trade_cost_rate,
            tick_size=1,
        )
        tick_size = max(
            1,
            _safe_int(kiwoom_utils.get_tick_size(raw_target_price), 1),
        )
        target_price = opening_rotation_profit_target_price(
            buy_fill_price,
            trade_cost_rate=trade_cost_rate,
            tick_size=tick_size,
        )
    except Exception as exc:
        with _active_state_lock():
            target_stock.update(
                {
                    "opening_rotation_profit_target_submit_pending": False,
                    "opening_rotation_profit_order_protection_failed": True,
                    "opening_rotation_new_episode_blocked": True,
                    "opening_rotation_episode_phase": "TARGET_PRICE_RESOLUTION_FAILED",
                    "opening_rotation_profit_target_submit_error": str(exc)[:240],
                    "scale_in_locked": True,
                }
            )
        log_error(
            f"[OPENING_ROTATION_TARGET_PRICE_FAILED] "
            f"{target_stock.get('name')}({code}) error={exc}"
        )
        return False
    if target_price <= buy_fill_price:
        with _active_state_lock():
            target_stock.update(
                {
                    "opening_rotation_profit_target_submit_pending": False,
                    "opening_rotation_profit_order_protection_failed": True,
                    "opening_rotation_new_episode_blocked": True,
                    "opening_rotation_episode_phase": "TARGET_PRICE_INVALID",
                    "scale_in_locked": True,
                }
            )
        return False

    target_stock.update(
        {
            "opening_rotation_episode_phase": "TARGET_SUBMITTING",
            "opening_rotation_profit_target_price": target_price,
            "opening_rotation_profit_target_qty": 1,
            "opening_rotation_profit_target_submit_pending": True,
            "opening_rotation_profit_target_submitted_at": time.time(),
            "opening_rotation_trade_cost_rate": trade_cost_rate,
            "opening_rotation_slippage_budget_rate": 0.001,
            "opening_rotation_net_profit_floor_pct": 0.30,
            "opening_rotation_ratchet_shadow_price": (
                opening_rotation_shadow_ratchet_price(target_price, tick_size=tick_size)
            ),
            "opening_rotation_ratchet_shadow_recorded": False,
            "opening_rotation_ratchet_real_order_enabled": False,
            "scale_in_locked": True,
        }
    )
    try:
        response = kiwoom_orders.send_sell_order_market(
            code=code,
            qty=1,
            token=KIWOOM_TOKEN,
            order_type="00",
            price=target_price,
            reason_type="PROFIT",
            strategy="SCALPING",
            dmst_stex_tp="KRX",
        )
    except Exception as exc:
        response = None
        log_error(
            f"[OPENING_ROTATION_TARGET_SUBMIT_EXCEPTION] "
            f"{target_stock.get('name')}({code}) error={exc}"
        )

    response_order_no = _extract_order_no(response)
    with _active_state_lock():
        notice_order_no = str(
            target_stock.get("opening_rotation_profit_target_order_no") or ""
        ).strip()
        order_no = response_order_no or notice_order_no
        submit_succeeded = bool(
            order_no and (_is_ok_response(response) or notice_order_no)
        )
        if submit_succeeded:
            target_stock.update(
                {
                    "exit_mode": "OPENING_ROTATION_PROTECTED_TP",
                    "opening_rotation_profit_target_submit_pending": False,
                    "opening_rotation_profit_order_protection_failed": False,
                    "opening_rotation_profit_target_order_no": order_no,
                    "opening_rotation_profit_target_broker_route": "KRX",
                    "opening_rotation_episode_phase": "TARGET_ORDERED",
                    # Reuse the established cancel/reload path for any timeout
                    # or holding-AI early exit. Opening never uses legacy TP.
                    "preset_tp_ord_no": order_no,
                    "preset_tp_qty": 1,
                    "preset_tp_price": target_price,
                    "preset_tp_broker_route": "KRX",
                }
            )
        else:
            target_stock.update(
                {
                    "opening_rotation_profit_target_submit_pending": False,
                    "opening_rotation_profit_order_protection_failed": True,
                    "opening_rotation_new_episode_blocked": True,
                    "opening_rotation_episode_phase": "TARGET_SUBMIT_FAILED",
                    "opening_rotation_profit_target_submit_error": str(
                        (response or {}).get("return_msg")
                        if isinstance(response, dict)
                        else response
                    )[:240],
                    "scale_in_locked": True,
                }
            )
    if not submit_succeeded:
        log_error(
            f"[OPENING_ROTATION_TARGET_SUBMIT_FAILED] "
            f"{target_stock.get('name')}({code}) target={target_price}"
        )
        return False
    _log_holding_pipeline(
        target_stock.get("name"),
        code,
        target_stock.get("id"),
        "opening_rotation_profit_target_ordered",
        opening_rotation_episode_id=(
            target_stock.get("opening_rotation_episode_id") or "-"
        ),
        opening_rotation_episode_promotion_id=target_stock.get(
            "opening_rotation_episode_promotion_id", "-"
        ),
        opening_rotation_profile_id=target_stock.get(
            "opening_rotation_profile_id", "-"
        ),
        opening_rotation_policy_hash=target_stock.get(
            "opening_rotation_policy_hash", "-"
        ),
        opening_rotation_policy_schema_version=target_stock.get(
            "opening_rotation_policy_schema_version", "-"
        ),
        opening_rotation_margin_one_share_authorized=bool(
            target_stock.get("opening_rotation_margin_one_share_authorized", False)
        ),
        opening_rotation_margin_authority_reason=target_stock.get(
            "opening_rotation_margin_authority_reason", "not_evaluated"
        ),
        opening_rotation_margin_rate=target_stock.get(
            "opening_rotation_margin_rate", 0
        ),
        opening_rotation_margin_orderable_amount=target_stock.get(
            "opening_rotation_margin_orderable_amount", 0
        ),
        opening_rotation_margin_orderable_qty_cap=target_stock.get(
            "opening_rotation_margin_orderable_qty_cap", 0
        ),
        opening_rotation_margin_requested_unit_price=target_stock.get(
            "opening_rotation_margin_requested_unit_price", 0
        ),
        opening_rotation_margin_cash_guard_bypassed=bool(
            target_stock.get("opening_rotation_margin_cash_guard_bypassed", False)
        ),
        opening_rotation_margin_order_api=target_stock.get(
            "opening_rotation_margin_order_api"
        ),
        opening_rotation_margin_credit_order_api_used=target_stock.get(
            "opening_rotation_margin_credit_order_api_used"
        ),
        buy_fill_price=buy_fill_price,
        target_price=target_price,
        qty=1,
        ord_no=order_no,
        trade_cost_rate=trade_cost_rate,
        slippage_budget_rate=0.001,
        net_profit_floor_pct=0.30,
        gross_target_pct=round((target_price / buy_fill_price - 1.0) * 100.0, 6),
        actual_order_submitted=True,
        broker_order_forbidden=False,
        runtime_effect=True,
    )
    return True


def _refresh_scalp_preset_exit_order(target_stock, code, total_qty):
    """
    Legacy compatibility hook for the removed SCALP preset TP route.

    The runtime exit owner is now the generic SCALPING trailing flow.  This
    helper no longer places a +1.5% preset sell order; it only cancels an
    existing preset order if one is still tracked on the position.
    """
    from src.engine import kiwoom_orders

    preset_ord_no = str(target_stock.get("preset_tp_ord_no", "") or "").strip()

    if preset_ord_no:
        preset_broker_route = (
            str(
                target_stock.get("preset_tp_broker_route")
                or target_stock.get("entry_execution_broker_route")
                or ""
            )
            .strip()
            .upper()
        )
        cancel_res = kiwoom_orders.send_cancel_order(
            code=code,
            orig_ord_no=preset_ord_no,
            token=KIWOOM_TOKEN,
            qty=0,
            dmst_stex_tp=(
                preset_broker_route
                if preset_broker_route in {"KRX", "NXT", "SOR"}
                else None
            ),
        )
        if not _is_ok_response(cancel_res):
            log_error(
                f"⚠️ [SCALP_TRAILING_UNIFIED] {target_stock.get('name')}({code}) "
                "legacy preset TP cancel failed; leaving tracked order number for retry."
            )
            return False
    log_info(
        f"[SCALP_TRAILING_UNIFIED] {target_stock.get('name')}({code}) "
        "preset TP order disabled; exit will be evaluated by scalp_trailing_take_profit."
    )
    target_stock["preset_tp_ord_no"] = ""
    target_stock["preset_tp_qty"] = 0
    target_stock["preset_tp_price"] = 0
    target_stock["protect_profit_pct"] = None
    return True


def _update_db_for_buy(target_id, exec_price, now, receipt_snapshot):
    """비동기로 실행되는 BUY 체결 DB 업데이트 및 알림"""
    try:
        buy_qty = int(receipt_snapshot.get("buy_qty") or 0)
        avg_buy_price = float(receipt_snapshot.get("buy_price") or exec_price or 0)
        with DB.get_session() as session:
            update_fields = {
                "buy_price": avg_buy_price,
                "buy_qty": buy_qty,
                "status": "HOLDING",
                "buy_time": now,
            }
            initial_buy_qty = _safe_int(receipt_snapshot.get("initial_buy_qty"), 0)
            if initial_buy_qty > 0:
                update_fields["initial_buy_qty"] = initial_buy_qty
            nonterminal_monotonic = session.query(RecommendationHistory).filter_by(
                id=target_id
            )
            nonterminal_monotonic = nonterminal_monotonic.filter(
                or_(
                    RecommendationHistory.status.is_(None),
                    and_(
                        # EXPIRED is a scanner/watch lifecycle terminal state,
                        # not broker custody evidence.  An exact BUY receipt
                        # for the still-bound target must revive it to HOLDING.
                        # SELL_ORDERED/COMPLETED remain irreversible here.
                        ~RecommendationHistory.status.in_(
                            ("SELL_ORDERED", "COMPLETED")
                        ),
                        or_(
                            RecommendationHistory.status != "HOLDING",
                            RecommendationHistory.buy_qty.is_(None),
                            RecommendationHistory.buy_qty <= buy_qty,
                        ),
                    ),
                )
            )
            updated_rows = nonterminal_monotonic.update(
                update_fields, synchronize_session=False
            )

        if not updated_rows:
            persisted_state = "unavailable"
            try:
                with DB.get_session() as session:
                    persisted = (
                        session.query(RecommendationHistory)
                        .filter_by(id=target_id)
                        .first()
                    )
                    if persisted is None:
                        persisted_state = "missing"
                    else:
                        persisted_state = (
                            f"status={str(persisted.status or '-').upper()} "
                            f"qty={_safe_int(persisted.buy_qty, 0)} "
                            f"price={_safe_float(persisted.buy_price, 0.0):.2f}"
                        )
            except Exception as state_exc:
                persisted_state = f"lookup_failed:{state_exc}"
            log_info(
                f"[BUY_DB_RECEIPT_STALE_SKIPPED] ID {target_id} "
                f"snapshot_qty={buy_qty} reason=irreversible_or_newer_db_state "
                f"persisted={persisted_state}"
            )
            return

        log_info(
            f"✅ [영수증: ID {target_id}] {receipt_snapshot.get('code')} "
            f"실제 매수 체결 반영 완료! avg={avg_buy_price:,} qty={buy_qty}"
        )

        if not receipt_snapshot.get("buy_execution_notified"):
            pending_msg = receipt_snapshot.get("pending_buy_msg")
            audience = _receipt_audience(receipt_snapshot)
            if pending_msg:
                final_msg = pending_msg.replace(
                    "그물망 투척!", "그물망 매수 체결!"
                ).replace("스나이퍼 포착!", "스나이퍼 매수 체결!")
                final_msg += f"\n✅ **평균 체결가:** `{avg_buy_price:,.0f}원` / **체결수량:** `{buy_qty}주`"
                event_bus.publish(
                    "TELEGRAM_BROADCAST",
                    {
                        "message": final_msg,
                        "audience": audience,
                        "parse_mode": "Markdown",
                    },
                )
            else:
                event_bus.publish(
                    "TELEGRAM_BROADCAST",
                    {
                        "message": (
                            f"🛒 **[{receipt_snapshot.get('name')}]** 매수 체결 완료!\n"
                            f"평균 체결가: `{avg_buy_price:,.0f}원`\n체결수량: `{buy_qty}주`"
                        ),
                        "audience": audience,
                        "parse_mode": "Markdown",
                    },
                )
    except Exception as e:
        log_error(f"🚨 [DB 에러] ID {target_id} BUY 처리 중 에러: {e}")


def _publish_entry_partial_fill_message(
    target_stock: dict[str, Any],
    *,
    avg_buy_price: float,
    cum_filled_qty: int,
    requested_entry_qty: int,
    remaining_qty: int,
    allow_defer: bool = True,
) -> bool:
    if (
        requested_entry_qty <= 0
        or cum_filled_qty <= 0
        or cum_filled_qty >= requested_entry_qty
    ):
        return False

    last_notified_qty = int(target_stock.get("entry_partial_fill_notified_qty", 0) or 0)
    if cum_filled_qty <= last_notified_qty:
        return False

    if (
        allow_defer
        and bool(target_stock.get("entry_submit_notice_pending"))
        and not bool(target_stock.get("entry_submit_notice_enqueued"))
    ):
        target_stock["entry_partial_fill_deferred_notice"] = {
            "avg_buy_price": float(avg_buy_price or 0.0),
            "cum_filled_qty": int(cum_filled_qty or 0),
            "requested_entry_qty": int(requested_entry_qty or 0),
            "remaining_qty": int(remaining_qty or 0),
        }
        target_stock["entry_partial_fill_deferred_at"] = time.time()
        log_info(
            f"[ENTRY_PARTIAL_FILL_NOTICE_DEFERRED_UNTIL_SUBMIT_NOTICE] "
            f"{target_stock.get('name')}({target_stock.get('code')}) "
            f"filled={cum_filled_qty}/{requested_entry_qty} remaining={remaining_qty}"
        )
        return False

    pending_msg = target_stock.get("pending_buy_msg") or ""
    if pending_msg:
        partial_msg = pending_msg
    else:
        partial_msg = f"🛒 **[{target_stock.get('name') or '-'}]** 매수 부분 체결"
    probe_phase = str(target_stock.get("entry_split_probe_phase") or "").strip()
    probe_abort_reason = str(
        target_stock.get("entry_split_probe_abort_reason") or ""
    ).strip()
    probe_abort_detail_reason = str(
        target_stock.get("entry_split_probe_abort_detail_reason") or ""
    ).strip()
    probe_order_no = str(target_stock.get("entry_split_probe_order_no") or "").strip()
    probe_first_fill_with_planned_residual = bool(
        probe_order_no and cum_filled_qty == 1 and remaining_qty > 0
    )
    if probe_first_fill_with_planned_residual:
        partial_msg += (
            f"\n✅ **probe 체결:** `1/1주` / **평균 체결가:** `{avg_buy_price:,.0f}원`"
        )
        if probe_phase == "aborted" and probe_abort_reason:
            displayed_abort_reason = probe_abort_reason
            if probe_abort_detail_reason and probe_abort_detail_reason != "-":
                displayed_abort_reason = (
                    f"{probe_abort_reason}/{probe_abort_detail_reason}"
                )
            partial_msg += (
                f"\n⏸ **계획 잔여:** `{remaining_qty}주 미제출`"
                f" (`{displayed_abort_reason}`)"
            )
        elif probe_phase in {
            "residual_submitting",
            "residual_submitted",
            "residual_partial_submitted",
        }:
            partial_msg += f"\n⏳ **residual:** `{remaining_qty}주 제출·체결 확인 중`"
        else:
            partial_msg += (
                f"\n⏳ **계획 잔여:** `{remaining_qty}주 방향·가격 재검증 중`"
            )
    else:
        partial_msg += (
            f"\n⏳ **부분 체결:** `{cum_filled_qty}/{requested_entry_qty}주`"
            f" / **평균 체결가:** `{avg_buy_price:,.0f}원`"
            f" / **잔여:** `{remaining_qty}주`"
        )
    if event_bus is None:
        log_info(
            f"[ENTRY_PARTIAL_FILL_NOTICE_SKIPPED] {target_stock.get('name')}({target_stock.get('code')}) "
            "reason=event_bus_unavailable"
        )
        return False
    try:
        event_bus.publish(
            "TELEGRAM_BROADCAST",
            {
                "message": partial_msg,
                "audience": _receipt_audience(target_stock),
                "parse_mode": "Markdown",
            },
        )
    except Exception as exc:
        log_error(
            f"[ENTRY_PARTIAL_FILL_NOTICE_FAILED] {target_stock.get('name')}({target_stock.get('code')}) "
            f"error={exc}"
        )
        return False
    target_stock["entry_partial_fill_notified_qty"] = int(cum_filled_qty or 0)
    return True


def flush_deferred_entry_partial_fill_notice(
    target_stock: dict[str, Any] | None,
) -> bool:
    target_stock = target_stock if isinstance(target_stock, dict) else {}
    deferred = target_stock.get("entry_partial_fill_deferred_notice")
    if not isinstance(deferred, dict):
        return False
    target_stock.pop("entry_partial_fill_deferred_notice", None)
    target_stock.pop("entry_partial_fill_deferred_at", None)
    return _publish_entry_partial_fill_message(
        target_stock,
        avg_buy_price=float(deferred.get("avg_buy_price") or 0.0),
        cum_filled_qty=int(deferred.get("cum_filled_qty") or 0),
        requested_entry_qty=int(deferred.get("requested_entry_qty") or 0),
        remaining_qty=int(deferred.get("remaining_qty") or 0),
        allow_defer=False,
    )


def _publish_add_execution_notification(
    receipt_snapshot,
    add_type,
    *,
    fallback_prev_price=0.0,
    fallback_prev_qty=0,
):
    if event_bus is None:
        return False
    _type_kr = {"AVG_DOWN": "물타기", "PYRAMID": "불타기"}.get(add_type, add_type)
    _strategy_kr = {"SCALPING": "스캘핑", "SWING": "스윙"}.get(
        receipt_snapshot.get("strategy", ""), receipt_snapshot.get("strategy", "")
    )
    new_avg = _safe_float(receipt_snapshot.get("buy_price"), 0.0)
    new_qty = _safe_int(receipt_snapshot.get("buy_qty"), 0)
    notice_prev_price = _safe_float(
        receipt_snapshot.get("pending_add_initial_buy_price"), fallback_prev_price
    )
    notice_prev_qty = _safe_int(
        receipt_snapshot.get("pending_add_initial_buy_qty"), fallback_prev_qty
    )
    notice_fill_qty = max(0, new_qty - notice_prev_qty)
    notice_fill_avg = 0.0
    if notice_fill_qty > 0 and notice_prev_qty > 0:
        notice_fill_avg = (
            (new_avg * new_qty) - (notice_prev_price * notice_prev_qty)
        ) / notice_fill_qty
    if notice_fill_avg <= 0:
        notice_fill_avg = _safe_float(receipt_snapshot.get("last_add_fill_price"), 0.0)
    msg = (
        f"➕ 추가매수 체결 완료\n"
        f"종목: {receipt_snapshot.get('name')} ({receipt_snapshot.get('code')})\n"
        f"전략: {_strategy_kr} | 유형: {_type_kr}\n"
        f"기존 평단가: {int(notice_prev_price):,}원 ({notice_prev_qty}주)\n"
        f"추가 체결: {notice_fill_qty}주 (평균 {int(round(notice_fill_avg)):,}원)\n"
        f"새 평단가: {int(new_avg):,}원 | 총 수량: {new_qty}주\n"
        f"누적 추가매수: {_safe_int(receipt_snapshot.get('add_count'), 0)}회"
    )
    event_bus.publish(
        "TELEGRAM_BROADCAST",
        {
            "message": msg,
            "audience": _receipt_audience(receipt_snapshot),
            "parse_mode": None,
        },
    )
    return True


def flush_deferred_add_completion_notice(target_stock: dict[str, Any] | None) -> bool:
    target_stock = target_stock if isinstance(target_stock, dict) else {}
    if not target_stock.get("pending_add_execution_notice_pending"):
        return False
    requested_qty = _safe_int(target_stock.get("pending_add_qty"), 0)
    filled_qty = _safe_int(target_stock.get("pending_add_filled_qty"), 0)
    if requested_qty > 0 and filled_qty < requested_qty:
        return False
    snapshot = _receipt_snapshot(target_stock, _ADD_RECEIPT_SNAPSHOT_KEYS)
    snapshot["last_add_fill_price"] = _safe_int(
        target_stock.get("last_add_fill_price"), 0
    )
    published = _publish_add_execution_notification(
        snapshot,
        str(target_stock.get("pending_add_type") or "").upper(),
    )
    if published:
        target_stock.pop("pending_add_execution_notice_pending", None)
    return published


def _update_db_for_add(
    target_id,
    exec_price,
    exec_qty,
    now,
    receipt_snapshot,
    add_type,
    count_increment,
    publish_notification=None,
):
    """비동기로 실행되는 추가매수 체결 DB 업데이트"""
    try:
        new_avg = float(receipt_snapshot.get("buy_price") or exec_price or 0)
        new_qty = int(receipt_snapshot.get("buy_qty") or 0)
        if new_qty <= 0 or new_avg <= 0:
            log_error(
                f"[ADD_DB_RECEIPT_BLOCKED] ID {target_id} "
                f"invalid snapshot avg={new_avg} qty={new_qty}"
            )
            return
        with DB.get_session() as session:
            record = (
                session.query(RecommendationHistory).filter_by(id=target_id).first()
            )
            if not record:
                return

            old_price = float(record.buy_price) if record.buy_price is not None else 0.0
            old_qty = int(record.buy_qty or 0)
            update_fields: dict[str, Any] = {
                "buy_price": new_avg,
                "buy_qty": new_qty,
                "add_count": int(
                    receipt_snapshot.get("add_count", record.add_count or 0) or 0
                ),
                "avg_down_count": int(
                    receipt_snapshot.get("avg_down_count", record.avg_down_count or 0)
                    or 0
                ),
                "pyramid_count": int(
                    receipt_snapshot.get("pyramid_count", record.pyramid_count or 0)
                    or 0
                ),
                "scale_in_filled_qty": _safe_int(
                    receipt_snapshot.get("scale_in_filled_qty"),
                    _safe_int(getattr(record, "scale_in_filled_qty", 0), 0)
                    + int(exec_qty or 0),
                ),
                "last_add_type": add_type,
                "last_add_reason": str(
                    receipt_snapshot.get("last_add_reason") or ""
                ).strip(),
                "last_add_at": now,
                "shallow_volatility_avg_down_count": int(
                    receipt_snapshot.get(
                        "shallow_volatility_avg_down_count",
                        getattr(record, "shallow_volatility_avg_down_count", 0) or 0,
                    )
                    or 0
                ),
                "scale_in_locked": bool(receipt_snapshot.get("scale_in_locked", False)),
            }
            initial_buy_qty = _safe_int(
                receipt_snapshot.get("initial_buy_qty"),
                _safe_int(getattr(record, "initial_buy_qty", 0), 0),
            )
            if initial_buy_qty > 0:
                update_fields["initial_buy_qty"] = initial_buy_qty
            shallow_last_at = float(
                receipt_snapshot.get("shallow_volatility_avg_down_last_at") or 0.0
            )
            if shallow_last_at > 0:
                update_fields["shallow_volatility_avg_down_last_at"] = (
                    datetime.fromtimestamp(
                        shallow_last_at,
                    )
                )
            # 보호선 보정값을 DB에도 반영 (있을 때만)
            if receipt_snapshot.get("trailing_stop_price") is not None:
                update_fields["trailing_stop_price"] = float(
                    receipt_snapshot.get("trailing_stop_price") or 0
                )
            if receipt_snapshot.get("hard_stop_price") is not None:
                update_fields["hard_stop_price"] = float(
                    receipt_snapshot.get("hard_stop_price") or 0
                )
            monotonic_holding = session.query(RecommendationHistory).filter_by(
                id=target_id
            )
            monotonic_holding = monotonic_holding.filter(
                and_(
                    RecommendationHistory.status == "HOLDING",
                    or_(
                        RecommendationHistory.buy_qty.is_(None),
                        RecommendationHistory.buy_qty < new_qty,
                    ),
                )
            )
            updated_rows = monotonic_holding.update(
                update_fields,
                synchronize_session=False,
            )

        if not updated_rows:
            log_info(
                f"[ADD_DB_RECEIPT_STALE_SKIPPED] ID {target_id} "
                f"snapshot_qty={new_qty} reason=terminal_or_newer_db_state"
            )
            return

        log_info(
            f"✅ [영수증: ID {target_id}] {receipt_snapshot.get('code')} 추가매수 체결 반영 "
            f"(avg={new_avg}, qty={new_qty}, type={add_type})"
        )

        if publish_notification is None:
            publish_notification = bool(count_increment)
        if event_bus and publish_notification:
            receipt_snapshot["last_add_fill_price"] = int(exec_price or 0)
            _publish_add_execution_notification(
                receipt_snapshot,
                add_type,
                fallback_prev_price=old_price,
                fallback_prev_qty=old_qty,
            )
    except Exception as e:
        log_error(f"🚨 [DB 에러] ID {target_id} ADD 처리 중 에러: {e}")


def _update_db_for_sell(
    target_id, exec_price, now, receipt_snapshot, strategy, is_scalp_revive
) -> bool:
    """Commit an exact SELL receipt and report whether the transaction closed."""
    try:
        with DB.get_session() as session:
            record = (
                session.query(RecommendationHistory).filter_by(id=target_id).first()
            )
            if not record:
                return False
            prior_status = str(getattr(record, "status", "") or "").strip().upper()
            if prior_status == "COMPLETED":
                return bool(
                    record.sell_time and _safe_float(record.sell_price, 0.0) > 0
                )
            if prior_status not in {"HOLDING", "SELL_ORDERED"}:
                log_error(
                    f"[SELL_RECEIPT_DB_RECONCILE_BLOCKED] ID {target_id} "
                    f"unexpected_status={prior_status or '-'}"
                )
                return False

            safe_buy_price = (
                float(record.buy_price) if record.buy_price is not None else 0.0
            )
            nxt_partial_qty = _safe_int(
                receipt_snapshot.get("nxt_rising_missed_tp1_partial_filled_qty"), 0
            )
            nxt_partial_amount = _safe_int(
                receipt_snapshot.get("nxt_rising_missed_tp1_partial_fill_amount"), 0
            )
            partial_qty = nxt_partial_qty
            partial_amount = nxt_partial_amount
            if safe_buy_price > 0:
                profit_rate = calculate_net_profit_rate(safe_buy_price, exec_price)
            else:
                profit_rate = 0.0
                log_error(
                    f"⚠️ [수익률 계산 불가] ID {target_id}의 매수가(buy_price)가 누락되어 수익률을 0%로 처리합니다."
                )
            pre_add_avg_price = _safe_float(
                receipt_snapshot.get("pre_add_avg_price"), 0.0
            )
            pre_add_qty = _safe_int(receipt_snapshot.get("pre_add_qty"), 0)
            position_runner_qty = _safe_int(getattr(record, "buy_qty", 0), 0)
            if position_runner_qty <= 0:
                position_runner_qty = _safe_int(receipt_snapshot.get("buy_qty"), 0)
            completed_runner_qty = _safe_int(
                receipt_snapshot.get("sell_execution_cumulative_qty"), 0
            )
            if position_runner_qty <= 0 or completed_runner_qty != position_runner_qty:
                log_error(
                    f"[SELL_RECEIPT_DB_RECONCILE_BLOCKED] ID {target_id} "
                    f"filled={completed_runner_qty} position={position_runner_qty}"
                )
                return False
            runner_sell_amount = _safe_int(
                receipt_snapshot.get("sell_execution_cumulative_amount"), 0
            )
            if runner_sell_amount <= 0:
                log_error(
                    f"[SELL_RECEIPT_DB_RECONCILE_BLOCKED] ID {target_id} "
                    "cumulative sell amount missing"
                )
                return False
            runner_weighted_sell_price = runner_sell_amount / completed_runner_qty
            record.status = "COMPLETED"
            record.sell_time = now
            cumulative_includes_partial = bool(
                partial_qty > 0 and completed_runner_qty == position_runner_qty
            )
            completed_buy_qty = (
                completed_runner_qty
                if cumulative_includes_partial
                else completed_runner_qty + partial_qty
            )
            position_weighted_sell_price = int(round(runner_weighted_sell_price))
            runner_realized_pnl_krw = _safe_float(
                receipt_snapshot.get("sell_execution_cumulative_net_pnl_krw"),
                calculate_net_realized_pnl(
                    safe_buy_price,
                    runner_weighted_sell_price,
                    completed_runner_qty,
                ),
            )
            partial_realized_pnl_krw = 0
            if (
                not cumulative_includes_partial
                and partial_qty > 0
                and partial_amount > 0
                and safe_buy_price > 0
            ):
                partial_avg_sell_price = partial_amount / partial_qty
                partial_realized_pnl_krw = calculate_net_realized_pnl(
                    safe_buy_price,
                    partial_avg_sell_price,
                    partial_qty,
                )
                total_sell_amount = partial_amount + (runner_sell_amount)
                position_weighted_sell_price = int(
                    round(total_sell_amount / max(1, completed_buy_qty))
                )
                total_notional = safe_buy_price * completed_buy_qty
                profit_rate = (
                    (partial_realized_pnl_krw + runner_realized_pnl_krw)
                    / total_notional
                    * 100.0
                    if total_notional > 0
                    else 0.0
                )
            elif safe_buy_price > 0 and completed_runner_qty > 0:
                profit_rate = (
                    runner_realized_pnl_krw
                    / (safe_buy_price * completed_runner_qty)
                    * 100.0
                )
            if pre_add_avg_price > 0 and pre_add_qty > 0:
                no_scale_in_counterfactual_profit_pct = calculate_net_profit_rate(
                    pre_add_avg_price, position_weighted_sell_price
                )
                receipt_snapshot["no_scale_in_counterfactual_profit_pct"] = round(
                    float(no_scale_in_counterfactual_profit_pct), 4
                )
                receipt_snapshot["scale_in_incremental_realized_delta_pct"] = round(
                    float(profit_rate) - float(no_scale_in_counterfactual_profit_pct),
                    4,
                )
            record.buy_qty = completed_buy_qty
            record.sell_price = position_weighted_sell_price
            record.profit_rate = profit_rate
            completed_position_tag = normalize_position_tag(
                strategy,
                getattr(record, "position_tag", None)
                or receipt_snapshot.get("position_tag"),
            )
            realized_pnl_krw = partial_realized_pnl_krw + runner_realized_pnl_krw
            receipt_snapshot.update(
                {
                    "buy_price": safe_buy_price,
                    "buy_qty": completed_buy_qty,
                    "position_tag": completed_position_tag,
                    "strategy": strategy,
                    "realized_pnl_krw": realized_pnl_krw,
                    "runner_realized_pnl_krw": runner_realized_pnl_krw,
                    "partial_realized_pnl_krw": partial_realized_pnl_krw,
                    "partial_realized_qty": partial_qty,
                    "runner_realized_qty": completed_runner_qty,
                    "position_weighted_sell_price": position_weighted_sell_price,
                    "actual_order_submitted": True,
                    "broker_order_forbidden": False,
                }
            )

            # Commit custody truth before emitting completion notifications or
            # source-only lifecycle evidence.  A crash after those emissions
            # but before the transaction committed could otherwise advertise a
            # completed position while the durable DB row remained active.
            session.flush()
            session.commit()

            log_info(
                f"🎉 [매매 완료: ID {target_id}] {receipt_snapshot.get('code')} "
                f"실매도가: {position_weighted_sell_price:,}원 / 수익률: {profit_rate}%"
            )

            _publish_sell_execution_message(
                name=receipt_snapshot.get("name") or "-",
                pending_msg=receipt_snapshot.get("pending_sell_msg") or "",
                audience=_receipt_audience(receipt_snapshot),
                exec_price=position_weighted_sell_price,
                profit_rate=profit_rate,
            )
            final_leg_qty = _safe_int(
                receipt_snapshot.get("sell_execution_final_leg_qty"), 0
            )
            final_leg_price = _safe_float(
                receipt_snapshot.get("sell_execution_final_leg_price"), 0.0
            )
            final_leg_net_pnl_krw = _safe_float(
                receipt_snapshot.get("sell_execution_final_leg_net_pnl_krw"), 0.0
            )
            final_leg_economics = (
                _main_lifecycle_exit_economics_fields(
                    receipt_snapshot,
                    buy_price=safe_buy_price,
                    sell_price=final_leg_price,
                    sell_qty=final_leg_qty,
                    realized_net_pnl_krw=final_leg_net_pnl_krw,
                )
                if receipt_snapshot.get("sell_execution_receipt_economics_complete")
                is True
                else {}
            )
            _log_holding_pipeline(
                receipt_snapshot.get("name"),
                str(receipt_snapshot.get("code", "")).strip()[:6],
                target_id,
                "sell_completed",
                candidate_stock=receipt_snapshot,
                observed_at=now,
                order_no=receipt_snapshot.get("sell_execution_order_no") or "-",
                execution_no=(
                    receipt_snapshot.get("sell_execution_execution_no") or "-"
                ),
                sell_price=position_weighted_sell_price,
                last_sell_fill_price=round(final_leg_price, 4),
                sell_qty=completed_buy_qty,
                main_lifecycle_exit_qty=final_leg_qty,
                main_lifecycle_exit_price=round(final_leg_price, 4),
                main_lifecycle_broker_reconciled=True,
                main_lifecycle_reconciled_final_exit=True,
                sell_execution_receipt_economics_complete=bool(
                    receipt_snapshot.get(
                        "sell_execution_receipt_economics_complete", False
                    )
                ),
                sell_execution_receipt_quantity_contract_complete=bool(
                    receipt_snapshot.get(
                        "sell_execution_receipt_quantity_contract_complete", False
                    )
                ),
                sell_execution_receipt_unit_fill_consistent=bool(
                    receipt_snapshot.get(
                        "sell_execution_receipt_unit_fill_consistent", False
                    )
                ),
                position_weighted_sell_price=position_weighted_sell_price,
                profit_rate=f"{profit_rate:+.2f}",
                exit_rule=receipt_snapshot.get("last_exit_rule") or "-",
                exit_decision_source=receipt_snapshot.get("last_exit_decision_source")
                or "MANUAL",
                revive=bool(is_scalp_revive),
                smoothing_non_revive_post_sell_registered=bool(
                    receipt_snapshot.get(
                        "smoothing_non_revive_post_sell_registered", False
                    )
                ),
                smoothing_non_revive_post_sell_registration_status=(
                    receipt_snapshot.get(
                        "smoothing_non_revive_post_sell_registration_status"
                    )
                    or "not_applicable"
                ),
                smoothing_non_revive_post_sell_active_arm_count=_safe_int(
                    receipt_snapshot.get(
                        "smoothing_non_revive_post_sell_active_arm_count"
                    ),
                    0,
                ),
                smoothing_non_revive_post_sell_expires_at_epoch=(
                    receipt_snapshot.get(
                        "smoothing_non_revive_post_sell_expires_at_epoch"
                    )
                ),
                strategy=strategy,
                position_tag=completed_position_tag,
                buy_price=f"{safe_buy_price:.2f}",
                buy_qty=completed_buy_qty,
                realized_pnl_krw=realized_pnl_krw,
                partial_realized_pnl_krw=partial_realized_pnl_krw,
                runner_realized_pnl_krw=runner_realized_pnl_krw,
                partial_realized_qty=partial_qty,
                runner_realized_qty=completed_runner_qty,
                broker_route=receipt_snapshot.get(
                    "last_sell_execution_broker_route", "-"
                ),
                broker_route_resolution=receipt_snapshot.get(
                    "last_sell_execution_broker_route_resolution", "-"
                ),
                effective_venue=receipt_snapshot.get("last_sell_execution_cohort", "-"),
                actual_order_submitted=True,
                **_broker_execution_provenance_fields(receipt_snapshot),
                **final_leg_economics,
                **scout_ai_execution_attribution_fields(
                    receipt_snapshot,
                    stage="sell_completed",
                    actual_order_submitted=True,
                ),
                broker_order_forbidden=False,
                no_scale_in_counterfactual_profit_pct=receipt_snapshot.get(
                    "no_scale_in_counterfactual_profit_pct", "-"
                ),
                scale_in_incremental_realized_delta_pct=receipt_snapshot.get(
                    "scale_in_incremental_realized_delta_pct", "-"
                ),
                pre_add_avg_price=receipt_snapshot.get("pre_add_avg_price", "-"),
                post_add_avg_price=receipt_snapshot.get("post_add_avg_price", "-"),
                pre_add_qty=receipt_snapshot.get("pre_add_qty", "-"),
                post_add_qty=receipt_snapshot.get("post_add_qty", "-"),
                opening_rotation_entry_time_bucket=receipt_snapshot.get(
                    "opening_rotation_entry_time_bucket", "-"
                ),
                opening_rotation_window_version=receipt_snapshot.get(
                    "opening_rotation_window_version", "-"
                ),
                opening_rotation_episode_id=receipt_snapshot.get(
                    "opening_rotation_episode_id", "-"
                ),
                opening_rotation_episode_promotion_id=receipt_snapshot.get(
                    "opening_rotation_episode_promotion_id", "-"
                ),
                opening_rotation_profile_id=receipt_snapshot.get(
                    "opening_rotation_profile_id", "-"
                ),
                opening_rotation_policy_hash=receipt_snapshot.get(
                    "opening_rotation_policy_hash", "-"
                ),
                opening_rotation_policy_schema_version=receipt_snapshot.get(
                    "opening_rotation_policy_schema_version", "-"
                ),
                opening_rotation_margin_one_share_authorized=bool(
                    receipt_snapshot.get(
                        "opening_rotation_margin_one_share_authorized", False
                    )
                ),
                opening_rotation_margin_authority_reason=receipt_snapshot.get(
                    "opening_rotation_margin_authority_reason", "not_evaluated"
                ),
                opening_rotation_margin_rate=receipt_snapshot.get(
                    "opening_rotation_margin_rate", 0
                ),
                opening_rotation_margin_orderable_amount=receipt_snapshot.get(
                    "opening_rotation_margin_orderable_amount", 0
                ),
                opening_rotation_margin_orderable_qty_cap=receipt_snapshot.get(
                    "opening_rotation_margin_orderable_qty_cap", 0
                ),
                opening_rotation_margin_requested_unit_price=receipt_snapshot.get(
                    "opening_rotation_margin_requested_unit_price", 0
                ),
                opening_rotation_margin_cash_guard_bypassed=bool(
                    receipt_snapshot.get(
                        "opening_rotation_margin_cash_guard_bypassed", False
                    )
                ),
                opening_rotation_margin_order_api=receipt_snapshot.get(
                    "opening_rotation_margin_order_api"
                ),
                opening_rotation_margin_credit_order_api_used=receipt_snapshot.get(
                    "opening_rotation_margin_credit_order_api_used"
                ),
                mae_pct=receipt_snapshot.get("mae_pct", "-"),
                mfe_pct=receipt_snapshot.get("mfe_pct", "-"),
                **_trailing_continuation_receipt_fields(receipt_snapshot),
                **_sell_completion_contract_fields(completed_position_tag),
            )
            try:
                record_post_sell_candidate(
                    recommendation_id=target_id,
                    stock=receipt_snapshot,
                    code=str(receipt_snapshot.get("code", "")).strip()[:6],
                    sell_time=now,
                    buy_price=safe_buy_price,
                    sell_price=position_weighted_sell_price,
                    profit_rate=profit_rate,
                    buy_qty=int(
                        float(
                            getattr(record, "buy_qty", 0)
                            or receipt_snapshot.get("buy_qty", 0)
                            or 0
                        )
                    ),
                    exit_rule=receipt_snapshot.get("last_exit_rule") or "-",
                    strategy=strategy,
                    revive=bool(is_scalp_revive),
                    peak_profit=receipt_snapshot.get("last_exit_peak_profit"),
                    held_sec=receipt_snapshot.get("last_exit_held_sec"),
                    current_ai_score=receipt_snapshot.get("last_exit_current_ai_score"),
                    soft_stop_threshold_pct=receipt_snapshot.get(
                        "last_exit_soft_stop_threshold_pct"
                    ),
                    same_symbol_soft_stop_cooldown_would_block=receipt_snapshot.get(
                        "last_exit_same_symbol_soft_stop_cooldown_would_block"
                    ),
                )
            except Exception as exc:
                log_error(
                    f"[POST_SELL] candidate record failed (id={target_id}): {exc}"
                )
        # Same-symbol re-entry is released only after the DB session has
        # committed the completed receipt.  A failed commit must never grant
        # a new entry while the old custody row is still active.
        if strategy == "SCALPING" and callable(_scalp_exit_completed_callback):
            try:
                callback_result = _scalp_exit_completed_callback(
                    str(receipt_snapshot.get("code", "")).strip()[:6],
                    profit_rate=profit_rate,
                    exit_price=position_weighted_sell_price,
                    exit_rule=receipt_snapshot.get("last_exit_rule") or "-",
                    completed_at=now.timestamp(),
                    position_tag=completed_position_tag,
                )
                opening_rotation = (
                    completed_position_tag == OPENING_ROTATION_POSITION_TAG
                )
                reconciliation_failed = bool(
                    not isinstance(callback_result, dict)
                    or (
                        callback_result.get("reconciled") is False
                        and callback_result.get("reason")
                        != "active_reentry_context_missing"
                    )
                )
                if reconciliation_failed:
                    prefix = (
                        "OPENING_ROTATION_REENTRY"
                        if opening_rotation
                        else "RISING_MISSED_REENTRY"
                    )
                    log_error(
                        f"[{prefix}] completed receipt did not release the symbol "
                        f"(id={target_id}, result={callback_result})"
                    )
            except Exception as exc:
                log_error(
                    "[SELL_COMPLETED_REENTRY] post-commit reconciliation failed "
                    f"(id={target_id}, error={exc})"
                )
        return True
    except Exception as e:
        log_error(f"🚨 [DB 에러] ID {target_id} SELL 처리 중 에러: {e}")
        return False


def _handle_add_buy_execution(
    *,
    target_id: int,
    target_stock: dict[str, Any],
    code: str,
    order_no: str,
    exec_price: int,
    exec_qty: int,
    now: datetime,
    order_qty: int | None = None,
    remaining_qty: int | None = None,
    cumulative_exec_amount: int | None = None,
    execution_no: str = "",
    unit_exec_price: int | None = None,
    unit_exec_qty: int | None = None,
) -> None:
    add_receipt = _resolve_add_effective_fill(
        target_stock=target_stock,
        code=code,
        order_no=order_no,
        exec_price=exec_price,
        exec_qty=exec_qty,
        order_qty=order_qty,
        remaining_qty=remaining_qty,
        cumulative_exec_amount=cumulative_exec_amount,
        execution_no=execution_no,
        unit_exec_price=unit_exec_price,
        unit_exec_qty=unit_exec_qty,
    )
    if add_receipt.get("status") == "invalid":
        log_error(
            f"[ADD_RECEIPT_RECONCILE_BLOCKED] {target_stock.get('name')}({code}) "
            f"ord_no={order_no or '-'} reason={add_receipt.get('reason')} "
            f"raw_qty={exec_qty} order_qty={order_qty} remaining_qty={remaining_qty}"
        )
        _request_broker_snapshot_refresh(
            code, reason="scale_in_buy_receipt_reconcile_blocked"
        )
        return
    if add_receipt.get("status") == "duplicate":
        return
    order_no = str(add_receipt.get("order_no") or order_no or "").strip()
    effective_qty = int(add_receipt["incremental_qty"])
    if effective_qty <= 0:
        return
    effective_price = float(add_receipt["incremental_price"])
    incremental_amount = int(add_receipt["incremental_amount"])
    requested_qty = int(add_receipt.get("bundle_requested_qty") or 0)
    filled_qty = int(add_receipt.get("bundle_filled_qty") or 0)
    order_requested_qty = int(add_receipt.get("order_requested_qty") or 0)
    order_filled_qty = int(add_receipt.get("order_filled_qty") or 0)
    reconciled_before_ordno_bind = bool(add_receipt.get("reconciled_before_ordno_bind"))
    exec_qty = effective_qty
    exec_price = effective_price
    add_type = (target_stock.get("pending_add_type") or "").upper()
    old_price = float(target_stock.get("buy_price") or 0)
    old_qty = int(target_stock.get("buy_qty") or 0)
    if "pending_add_initial_buy_price" not in target_stock:
        target_stock["pending_add_initial_buy_price"] = old_price
    if "pending_add_initial_buy_qty" not in target_stock:
        target_stock["pending_add_initial_buy_qty"] = old_qty
    if _safe_int(target_stock.get("initial_buy_qty"), 0) <= 0:
        target_stock["initial_buy_qty"] = max(
            0,
            _safe_int(target_stock.get("pending_add_initial_buy_qty"), old_qty),
        )
    target_stock["scale_in_filled_qty"] = max(
        0,
        _safe_int(target_stock.get("scale_in_filled_qty"), 0) + int(exec_qty or 0),
    )
    request_qty = int(requested_qty or target_stock.get("pending_add_qty", 0) or 0)
    pending_ord_no = str(target_stock.get("pending_add_ord_no", "") or "").strip()
    pending_ord_nos = {
        part.strip() for part in pending_ord_no.split(",") if part.strip()
    }
    history_order_no = (
        order_no if order_no in pending_ord_nos else (pending_ord_no or order_no)
    )
    new_qty = old_qty + exec_qty
    if old_qty > 0:
        total_qty = old_qty + exec_qty
        new_avg = _avg_from_totals(
            (old_price * old_qty) + incremental_amount, total_qty
        )
    else:
        new_avg = exec_price
    add_reference_avg_price = float(
        target_stock.get("pending_add_initial_buy_price") or old_price or 0.0
    )
    if add_type == "AVG_DOWN" and add_reference_avg_price > 0:
        if float(exec_price) < add_reference_avg_price:
            add_economic_direction = "averaging_down"
        elif float(exec_price) > add_reference_avg_price:
            add_economic_direction = "recovery_add_above_average"
        else:
            add_economic_direction = "recovery_add_at_average"
    elif add_type == "PYRAMID":
        add_economic_direction = "pyramid"
    else:
        add_economic_direction = "unclassified"
    avg_price_improved = bool(
        add_type == "AVG_DOWN"
        and add_reference_avg_price > 0
        and float(new_avg) < add_reference_avg_price
    )

    target_stock["status"] = "HOLDING"
    target_stock["buy_price"] = new_avg
    target_stock["buy_qty"] = new_qty
    pre_add_avg_price = float(
        target_stock.get("pending_add_initial_buy_price") or old_price or 0.0
    )
    pre_add_qty = _safe_int(target_stock.get("pending_add_initial_buy_qty"), old_qty)
    target_stock["pre_add_avg_price"] = round(pre_add_avg_price, 4)
    target_stock["post_add_avg_price"] = round(float(new_avg or 0.0), 4)
    target_stock["pre_add_qty"] = int(pre_add_qty or 0)
    target_stock["post_add_qty"] = int(new_qty or 0)
    target_stock["last_add_type"] = add_type
    pending_add_reason = str(target_stock.get("pending_add_reason") or "").strip()
    winner_recovery_ai_fields = _winner_recovery_ai_receipt_fields(target_stock)
    target_stock["last_add_reason"] = pending_add_reason
    target_stock["last_add_economic_direction"] = add_economic_direction
    target_stock["last_add_avg_price_improved"] = avg_price_improved
    target_stock["last_add_at"] = now
    target_stock["last_add_fill_price"] = round(float(exec_price or 0), 4)
    target_stock["last_add_receipt_execution_no"] = execution_no or "-"
    target_stock["last_add_receipt_economics_complete"] = bool(
        add_receipt.get("economics_complete")
    )
    now_ts = time.time()
    target_stock["last_add_time"] = now_ts
    if add_type == "AVG_DOWN" and pending_add_reason in {
        "reversal_add_ok",
        "aggressive_reversal_add_ok",
        "shallow_volatility_avg_down",
    }:
        target_stock["reversal_add_state"] = "POST_ADD_EVAL"
        target_stock["reversal_add_executed_at"] = now.timestamp()
    if not target_stock.get("holding_started_at"):
        target_stock["holding_started_at"] = now
    if isinstance(highest_prices, dict):
        # 추가매수 후 포지션 평단/수량이 바뀌면 기존 고점 기준 trailing은 새 포지션에 과민하다.
        highest_prices[code] = max(float(exec_price or 0), float(new_avg or 0))
    _request_broker_snapshot_refresh(code, reason="scale_in_buy_execution")

    count_increment = False
    if not target_stock.get("pending_add_counted"):
        target_stock["add_count"] = int(target_stock.get("add_count", 0) or 0) + 1
        if add_type == "AVG_DOWN":
            target_stock["avg_down_count"] = (
                int(target_stock.get("avg_down_count", 0) or 0) + 1
            )
            if pending_add_reason == "shallow_volatility_avg_down":
                target_stock["shallow_volatility_avg_down_count"] = (
                    int(target_stock.get("shallow_volatility_avg_down_count", 0) or 0)
                    + 1
                )
                target_stock["shallow_volatility_avg_down_last_at"] = now_ts
        elif add_type == "PYRAMID":
            target_stock["pyramid_count"] = (
                int(target_stock.get("pyramid_count", 0) or 0) + 1
            )
        target_stock["pending_add_counted"] = True
        count_increment = True

    if count_increment:
        target_stock["pending_add_execution_notice_pending"] = True

    pending_qty = int(target_stock.get("pending_add_qty", 0) or 0)
    add_bundle_completed = pending_qty <= 0 or filled_qty >= pending_qty
    publish_add_notification = (
        bool(target_stock.get("pending_add_execution_notice_pending"))
        and add_bundle_completed
    )

    protection_ok = _apply_scale_in_protection(target_stock, add_type)
    strategy = normalize_strategy(target_stock.get("strategy"))
    pos_tag = normalize_position_tag(strategy, target_stock.get("position_tag"))
    if strategy == "SCALPING" and is_default_position_tag(strategy, pos_tag):
        base_buy_price = int(target_stock.get("buy_price") or exec_price or 0)
        target_stock["preset_tp_price"] = kiwoom_utils.get_target_price_up(
            base_buy_price, 1.5
        )
        protection_ok = (
            _refresh_scalp_preset_exit_order(target_stock, code, new_qty)
            and protection_ok
        )

    if not protection_ok:
        target_stock["scale_in_locked"] = True
        log_error(
            f"⚠️ [ADD_PROTECT] {target_stock.get('name')}({code}) 보호선 재설정 실패로 "
            "scale_in_locked=True"
        )

    add_receipt_snapshot = _receipt_snapshot(target_stock, _ADD_RECEIPT_SNAPSHOT_KEYS)
    fill_event_ts = time.time()
    split_leg_meta = _add_receipt_leg_meta(target_stock, order_no)
    split_leg_fields = _split_receipt_leg_meta_fields(
        split_leg_meta, filled_at_ts=fill_event_ts
    )
    # The probe/entry provenance and the exact scale-in leg metadata both carry
    # route fields.  Merge them before the pipeline call so a valid scale-in
    # receipt cannot raise at call binding time on duplicate keyword names.
    # Exact split-leg metadata is the final authority for the executed leg.
    entry_route_fields = _probe_venue_provenance_fields(target_stock)
    if (
        split_leg_fields.get("broker_route") in {None, "", "-"}
        and entry_route_fields.get("broker_route")
    ):
        split_leg_fields["broker_route"] = entry_route_fields["broker_route"]
        split_leg_fields["broker_route_resolution"] = entry_route_fields.get(
            "broker_route_resolution", "recorded_at_successful_entry_submit"
        )
    scale_in_execution_provenance = {
        **entry_route_fields,
        **_broker_execution_provenance_fields(target_stock),
        **split_leg_fields,
    }
    history_note = _split_receipt_history_note(split_leg_fields)
    _update_db_for_add(
        target_id,
        exec_price,
        exec_qty,
        now,
        add_receipt_snapshot,
        add_type,
        count_increment,
        publish_notification=publish_add_notification,
    )
    record_add_history_event(
        DB,
        recommendation_id=target_id,
        stock_code=code,
        stock_name=target_stock.get("name"),
        strategy=target_stock.get("strategy"),
        add_type=add_type,
        event_type="EXECUTED",
        order_no=history_order_no,
        request_qty=request_qty or pending_qty or exec_qty,
        executed_qty=exec_qty,
        executed_price=exec_price,
        prev_buy_price=old_price,
        new_buy_price=new_avg,
        prev_buy_qty=old_qty,
        new_buy_qty=new_qty,
        add_count_after=target_stock.get("add_count", 0),
        reason="receipt_confirmed",
        note=history_note,
    )
    if publish_add_notification:
        target_stock.pop("pending_add_execution_notice_pending", None)
    if pending_qty > 0 and filled_qty >= pending_qty:
        _clear_pending_add_meta(target_stock)
    log_info(
        "[ADD_EXECUTED] "
        f"{target_stock.get('name')}({code}) "
        f"type={add_type} exec={exec_price:,} "
        f"new_avg={new_avg} new_qty={new_qty} add_count={target_stock.get('add_count')}"
    )
    _log_holding_pipeline(
        target_stock.get("name"),
        code,
        target_id,
        "scale_in_executed",
        candidate_stock=target_stock,
        observed_at=now,
        metric_role="execution_quality_real_only",
        decision_authority="broker_receipt_observation_only",
        runtime_effect=False,
        forbidden_uses="runtime_threshold_apply/provider_route_change/bot_restart/sim_execution_quality_claim",
        actual_order_submitted=True,
        broker_order_forbidden=False,
        add_type=add_type,
        order_no=order_no or "-",
        execution_no=execution_no or "-",
        fill_price=round(float(exec_price or 0.0), 4),
        fill_qty=int(exec_qty or 0),
        bundle_requested_qty=int(requested_qty or 0),
        bundle_filled_qty=int(filled_qty or 0),
        order_requested_qty=int(order_requested_qty or 0),
        order_filled_qty=int(order_filled_qty or 0),
        remaining_qty=int(add_receipt.get("remaining_qty") or 0),
        cumulative_exec_amount=int(add_receipt.get("cumulative_amount") or 0),
        receipt_economics_complete=bool(add_receipt.get("economics_complete")),
        receipt_quantity_contract_complete=bool(
            add_receipt.get("quantity_contract_complete")
        ),
        receipt_unit_fill_consistent=bool(
            add_receipt.get("unit_fill_consistent", True)
        ),
        receipt_unit_qty_matches_delta=add_receipt.get("unit_qty_matches_delta"),
        **scale_in_execution_provenance,
        scale_in_receipt_reconciled_before_ordno_bind=bool(
            reconciled_before_ordno_bind
            or target_stock.get("scale_in_receipt_reconciled_before_ordno_bind")
        ),
        new_avg_price=f"{float(new_avg or 0):.2f}",
        new_buy_qty=int(new_qty or 0),
        add_count=int(target_stock.get("add_count", 0) or 0),
        avg_down_count=int(target_stock.get("avg_down_count", 0) or 0),
        add_reason=pending_add_reason or "-",
        add_economic_direction=add_economic_direction,
        avg_price_improved=avg_price_improved,
        add_reference_avg_price=f"{add_reference_avg_price:.2f}",
        pre_add_avg_price=f"{pre_add_avg_price:.2f}",
        pre_add_qty=int(pre_add_qty or 0),
        post_add_qty=int(new_qty or 0),
        post_add_avg_price=f"{float(new_avg or 0):.2f}",
        shallow_volatility_avg_down_count=int(
            target_stock.get("shallow_volatility_avg_down_count", 0) or 0
        ),
        shallow_volatility_avg_down_last_at=target_stock.get(
            "shallow_volatility_avg_down_last_at", "-"
        ),
        reversal_add_state=target_stock.get("reversal_add_state", "-"),
        reversal_add_executed_at=target_stock.get("reversal_add_executed_at", "-"),
        **_probe_residual_scale_in_receipt_fields(
            target_stock,
            now_ts=fill_event_ts,
        ),
        **winner_recovery_ai_fields,
    )


def _handle_entry_buy_execution(
    *,
    target_id: int,
    target_stock: dict[str, Any],
    code: str,
    order_no: str,
    exec_price: int,
    exec_qty: int,
    now: datetime,
    order_qty: int | None = None,
    remaining_qty: int | None = None,
    cumulative_exec_amount: int | None = None,
    execution_no: str = "",
    unit_exec_price: int | None = None,
    unit_exec_qty: int | None = None,
) -> None:
    entry_receipt = _resolve_entry_effective_fill_qty(
        target_stock=target_stock,
        code=code,
        order_no=order_no,
        exec_price=exec_price,
        exec_qty=exec_qty,
        order_qty=order_qty,
        remaining_qty=remaining_qty,
        cumulative_exec_amount=cumulative_exec_amount,
        execution_no=execution_no,
        unit_exec_price=unit_exec_price,
        unit_exec_qty=unit_exec_qty,
    )
    if entry_receipt.get("status") == "invalid":
        log_error(
            f"[ENTRY_RECEIPT_RECONCILE_BLOCKED] {target_stock.get('name')}({code}) "
            f"ord_no={order_no or '-'} reason={entry_receipt.get('reason')} "
            f"raw_qty={exec_qty} order_qty={order_qty} remaining_qty={remaining_qty}"
        )
        _request_broker_snapshot_refresh(
            code, reason="entry_buy_receipt_reconcile_blocked"
        )
        return
    if entry_receipt.get("status") == "duplicate":
        return
    order_no = str(entry_receipt.get("order_no") or order_no or "").strip()
    effective_exec_qty = int(entry_receipt["incremental_qty"])
    if effective_exec_qty <= 0:
        return
    incremental_exec_amount = int(entry_receipt["incremental_amount"])
    effective_exec_price = float(entry_receipt["incremental_price"])
    order_requested_qty = int(entry_receipt.get("requested_qty") or 0)
    order_filled_qty = int(entry_receipt.get("cumulative_qty") or 0)
    exec_price = effective_exec_price

    old_qty = int(target_stock.get("buy_qty") or 0)
    old_price = float(target_stock.get("buy_price") or 0)
    if old_qty <= 0:
        _prepare_new_position_exit_authority(
            target_stock,
            code=code,
            target_id=target_id,
            order_no=order_no,
        )
        _clear_split_entry_shadow_state(target_stock)
    new_qty = old_qty + effective_exec_qty
    if old_qty > 0:
        new_avg = _avg_from_totals(
            (old_price * old_qty) + incremental_exec_amount,
            old_qty + effective_exec_qty,
        )
    else:
        new_avg = exec_price
    entry_mode = str(target_stock.get("entry_mode", "normal") or "normal")

    pending_entry_orders = target_stock.get("pending_entry_orders") or []
    if pending_entry_orders and order_no:
        for pending_order in pending_entry_orders:
            if str(pending_order.get("ord_no", "") or "").strip() != order_no:
                continue
            requested_qty = int(pending_order.get("qty", 0) or 0)
            if pending_order.get("general_entry_margin_scale_in_forbidden"):
                for key in _GENERAL_ENTRY_MARGIN_POSITION_KEYS:
                    if key in pending_order:
                        target_stock[key] = pending_order[key]
                target_stock["probe_expand_forbidden"] = True
                target_stock["entry_split_probe_residual_expand_forbidden"] = True
                target_stock["entry_split_probe_scale_in_forbidden"] = True
            pending_order["last_fill_price"] = exec_price
            pending_order["last_fill_at"] = time.time()
            log_info(
                f"[ENTRY_FILL] {target_stock.get('name')}({code}) "
                f"tag={pending_order.get('tag')} ord_no={order_no} "
                f"fill_qty={effective_exec_qty} raw_fill_qty={exec_qty} "
                f"filled={pending_order.get('filled_qty')}/{requested_qty} "
                f"fill_price={exec_price}"
            )
            break

    target_stock["status"] = "HOLDING"
    target_stock["buy_price"] = new_avg
    target_stock["buy_qty"] = new_qty
    target_stock["entry_filled_qty"] = (
        int(target_stock.get("entry_filled_qty", 0) or 0) + effective_exec_qty
    )
    target_stock["entry_fill_amount"] = (
        int(target_stock.get("entry_fill_amount", 0) or 0) + incremental_exec_amount
    )
    target_stock["last_entry_receipt_execution_no"] = execution_no or "-"
    target_stock["last_entry_receipt_economics_complete"] = bool(
        entry_receipt.get("economics_complete")
    )
    if entry_receipt.get("terminal_entry_order_receipt") is True:
        _cancel_replacement_buys_after_late_parent_fill(
            target_stock,
            code=code,
            filled_order_no=str(entry_receipt.get("order_no") or order_no or ""),
        )
    target_stock["buy_time"] = now
    if not target_stock.get("holding_started_at"):
        target_stock["holding_started_at"] = now
    highest_prices[code] = max(highest_prices.get(code, 0), exec_price)
    _request_broker_snapshot_refresh(code, reason="entry_buy_execution")

    probe_phase = str(target_stock.get("entry_split_probe_phase") or "").strip()
    if probe_phase in {"probe_submitting", "probe_submitted"}:
        probe_contract_recovery = recover_probe_submit_contract_for_fill(
            target_stock,
            order_no=order_no,
            now=now,
        )
        if probe_contract_recovery.get("recovered"):
            _log_holding_pipeline(
                target_stock.get("name"),
                code,
                target_id,
                "probe_fill_submit_contract_recovered",
                candidate_stock=target_stock,
                probe_bundle_id=(probe_contract_recovery.get("bundle_id") or "-"),
                broker_order_no=order_no or "-",
                recovered_bundle_phase=(
                    probe_contract_recovery.get("bundle_phase") or "-"
                ),
                recovered_field_count=len(
                    probe_contract_recovery.get("restored_fields") or ()
                ),
                recovered_fields="|".join(
                    probe_contract_recovery.get("restored_fields") or ()
                )
                or "-",
                metric_role="source_quality_reconciliation",
                decision_authority="probe_fill_submit_contract_recovery_only",
                window_policy="same_broker_accepted_probe_fill",
                sample_floor="one_exact_code_target_and_unique_persisted_bundle",
                primary_decision_metric="probe_submit_contract_recovered",
                source_quality_gate=(
                    "exact_code_target_id_unique_nonterminal_probe_bundle_and_order_match"
                ),
                runtime_effect=True,
                actual_order_submitted=True,
                broker_order_forbidden=True,
                allowed_runtime_apply=False,
                forbidden_uses=(
                    "new_order_submit|residual_authority_grant|quantity_increase|"
                    "broker_guard_bypass|stale_quote_bypass|provider_route_change|"
                    "hard_safety_bypass"
                ),
            )
        elif probe_contract_recovery.get("reason") not in {
            "submit_contract_already_hydrated",
            "not_probe_fill_phase",
        }:
            _log_holding_pipeline(
                target_stock.get("name"),
                code,
                target_id,
                "probe_fill_submit_contract_recovery_failed",
                candidate_stock=target_stock,
                reason=probe_contract_recovery.get("reason") or "unknown",
                broker_order_no=order_no or "-",
                metric_role="source_quality_blocker",
                decision_authority="probe_fill_submit_contract_fail_closed",
                window_policy="same_broker_accepted_probe_fill",
                sample_floor="one_probe_fill_with_missing_submit_contract",
                primary_decision_metric="probe_submit_contract_recovered",
                source_quality_gate=(
                    "exact_code_target_id_unique_nonterminal_probe_bundle_and_order_match"
                ),
                runtime_effect=True,
                actual_order_submitted=True,
                broker_order_forbidden=True,
                allowed_runtime_apply=False,
                forbidden_uses=(
                    "residual_submit|scale_in_submit|quantity_increase|"
                    "broker_guard_bypass|stale_quote_bypass|provider_route_change|"
                    "hard_safety_bypass"
                ),
            )
        bundle_id = str(target_stock.get("entry_split_probe_bundle_id") or "").strip()
        probe_order_no = str(
            target_stock.get("entry_split_probe_order_no") or ""
        ).strip()
        if probe_order_no and order_no and probe_order_no != order_no:
            trip_probe_runtime_circuit("probe_receipt_order_number_mismatch")
            target_stock["entry_split_probe_phase"] = "aborted"
            target_stock["entry_split_probe_abort_reason"] = (
                "probe_receipt_order_number_mismatch"
            )
            target_stock["entry_split_probe_scale_in_forbidden"] = True
            target_stock["probe_expand_forbidden"] = True
            if bundle_id:
                update_probe_runtime_bundle(
                    bundle_id,
                    phase="aborted",
                    reason="probe_receipt_order_number_mismatch",
                    target_id=target_id,
                    observed_order_no=order_no,
                    filled_qty=int(new_qty or 0),
                    entry_split_probe_scale_in_forbidden=True,
                    probe_expand_forbidden=True,
                )
        elif effective_exec_qty != 1 or int(new_qty or 0) != 1:
            trip_probe_runtime_circuit("probe_fill_quantity_invariant")
            target_stock["entry_split_probe_phase"] = "aborted"
            target_stock["entry_split_probe_abort_reason"] = (
                "probe_fill_quantity_invariant"
            )
            target_stock["entry_split_probe_scale_in_forbidden"] = True
            target_stock["probe_expand_forbidden"] = True
            if bundle_id:
                update_probe_runtime_bundle(
                    bundle_id,
                    phase="aborted",
                    reason="probe_fill_quantity_invariant",
                    target_id=target_id,
                    filled_qty=int(new_qty or 0),
                    entry_split_probe_scale_in_forbidden=True,
                    probe_expand_forbidden=True,
                )
        else:
            filled_at_ts = time.time()
            target_stock["entry_split_probe_phase"] = "probe_filled"
            target_stock["entry_split_probe_order_no"] = order_no
            target_stock["entry_split_probe_fill_price"] = exec_price
            target_stock["entry_split_probe_filled_at"] = filled_at_ts
            target_stock["entry_split_probe_scale_in_forbidden"] = True
            target_stock["probe_expand_forbidden"] = bool(
                target_stock.get("entry_lifecycle_conflict")
            )
            update_probe_runtime_bundle(
                bundle_id,
                phase="probe_filled",
                order_no=order_no,
                fill_price=exec_price,
                filled_at=filled_at_ts,
                fill_qty=effective_exec_qty,
                entry_split_probe_scale_in_forbidden=True,
                probe_expand_forbidden=bool(
                    target_stock.get("entry_lifecycle_conflict")
                ),
                entry_lifecycle_conflict=bool(
                    target_stock.get("entry_lifecycle_conflict")
                ),
                entry_lifecycle_conflict_fields=(
                    target_stock.get("entry_lifecycle_conflict_fields") or "-"
                ),
            )
            submit_best_ask = _safe_int(
                target_stock.get("entry_split_probe_submit_best_ask"), 0
            )
            slippage_bps = (
                ((float(exec_price) - float(submit_best_ask)) / float(submit_best_ask))
                * 10000.0
                if submit_best_ask > 0
                else 0.0
            )
            _log_holding_pipeline(
                target_stock.get("name"),
                code,
                target_id,
                "probe_filled",
                candidate_stock=target_stock,
                probe_bundle_id=bundle_id or "-",
                order_no=order_no or "-",
                fill_qty=effective_exec_qty,
                fill_price=exec_price,
                probe_submit_best_ask=submit_best_ask,
                probe_submit_to_fill_ms=round(
                    max(
                        0.0,
                        filled_at_ts
                        - _safe_float(
                            target_stock.get("entry_split_probe_submitted_at")
                            or target_stock.get("entry_split_probe_submitting_at"),
                            filled_at_ts,
                        ),
                    )
                    * 1000.0,
                    3,
                ),
                probe_fill_slippage_bps=round(slippage_bps, 4),
                actual_order_submitted=True,
                broker_order_forbidden=False,
                runtime_effect=True,
                **_probe_observation_contract_fields(target_stock),
                **scout_ai_execution_attribution_fields(
                    target_stock,
                    stage="probe_filled",
                    actual_order_submitted=True,
                ),
            )
            if _probe_fill_continuation_callback is not None:
                threading.Thread(
                    target=_run_probe_fill_continuation,
                    args=(target_stock, code),
                    daemon=True,
                    name=f"probe-residual-{code}",
                ).start()

    submit_ai_score = _resolve_entry_submit_ai_score(target_stock, order_no)
    holding_ai_seeded = False
    if submit_ai_score is not None:
        target_stock["entry_submit_ai_score"] = round(float(submit_ai_score), 2)
        target_stock["holding_entry_ai_score"] = round(float(submit_ai_score), 2)
        if old_qty <= 0:
            target_stock["rt_ai_prob"] = max(
                0.0, min(1.0, float(submit_ai_score) / 100.0)
            )
            target_stock["holding_ai_score_seeded_from_entry"] = True
            holding_ai_seeded = True

    requested_entry_qty = int(
        target_stock.get(
            "entry_requested_qty", target_stock.get("requested_buy_qty", 0)
        )
        or 0
    )
    cum_filled_qty = int(target_stock.get("entry_filled_qty", 0) or 0)
    remaining_qty = (
        max(0, requested_entry_qty - cum_filled_qty) if requested_entry_qty > 0 else 0
    )
    fill_quality = (
        "FULL_FILL"
        if requested_entry_qty > 0 and cum_filled_qty >= requested_entry_qty
        else ("PARTIAL_FILL" if requested_entry_qty > 0 else "UNKNOWN")
    )
    target_stock["entry_fill_quality"] = fill_quality
    if (
        max(
            _safe_int(target_stock.get("add_count"), 0),
            _safe_int(target_stock.get("avg_down_count"), 0),
            _safe_int(target_stock.get("pyramid_count"), 0),
            _safe_int(target_stock.get("scale_in_filled_qty"), 0),
        )
        <= 0
    ):
        # Persist the cumulative initial bundle as fills arrive. A restart
        # between partial fills must not freeze the baseline at zero or at the
        # first partial quantity.
        target_stock["initial_buy_qty"] = max(
            _safe_int(target_stock.get("initial_buy_qty"), 0),
            max(0, new_qty),
        )

    preset_tp_price = int(target_stock.get("preset_tp_price") or 0)
    preset_tp_ord_no_before = str(
        target_stock.get("preset_tp_ord_no", "") or ""
    ).strip()
    preset_tp_ord_no_after = preset_tp_ord_no_before
    preset_sync_status = "NOT_APPLICABLE"
    preset_sync_reason = "non_scalping_or_non_default_tag"
    if requested_entry_qty > 0 and cum_filled_qty >= requested_entry_qty:
        probe_bundle_id = str(
            target_stock.get("entry_split_probe_bundle_id") or ""
        ).strip()
        probe_bundle_completed = bool(
            probe_bundle_id
            and str(target_stock.get("entry_split_probe_phase") or "")
            in {
                "residual_claimed",
                "residual_submitting",
                "residual_submitted",
                "residual_partial_submitted",
            }
        )
        log_info(
            f"[ENTRY_BUNDLE_FILLED] {target_stock.get('name')}({code}) "
            f"mode={target_stock.get('entry_mode', 'normal')} "
            f"filled_qty={new_qty}/{requested_entry_qty} avg_buy={new_avg}"
        )
        move_orders_to_terminal(target_stock, reason="entry_bundle_filled")
        target_stock.pop("pending_entry_orders", None)
        target_stock.pop("entry_requested_qty", None)
        target_stock.pop("requested_buy_qty", None)
        target_stock.pop("entry_filled_qty", None)
        target_stock.pop("entry_fill_amount", None)
        target_stock.pop("entry_bundle_id", None)
        target_stock.pop("rising_missed_scout_upgrade_order_pending", None)
        if probe_bundle_completed:
            rebaseline_mark = max(
                float(new_avg or 0.0),
                float(exec_price or 0.0),
            )
            if isinstance(highest_prices, dict):
                # The execution receipt is the first fresh post-fill mark.  Reset
                # synchronously so the 250ms monitor cannot consume the probe-only
                # peak before the next holding-loop pass.
                highest_prices[code] = rebaseline_mark
            target_stock["entry_split_probe_phase"] = "complete"
            target_stock["peak_rebaseline_pending"] = False
            target_stock["peak_basis_qty"] = int(new_qty or 0)
            target_stock["peak_basis_avg_price"] = round(float(new_avg or 0.0), 4)
            target_stock["peak_basis_mark_price"] = round(rebaseline_mark, 4)
            target_stock["peak_basis_at"] = time.time()
            target_stock.pop("entry_split_probe_residual_claimed", None)
            target_stock.pop("entry_split_probe_scale_in_forbidden", None)
            target_stock.pop("probe_expand_forbidden", None)
            update_probe_runtime_bundle(
                probe_bundle_id,
                phase="complete",
                requested_qty=requested_entry_qty,
                filled_qty=cum_filled_qty,
                avg_buy_price=round(float(new_avg or 0.0), 4),
                entry_split_probe_scale_in_forbidden=False,
                probe_expand_forbidden=False,
            )
            _log_holding_pipeline(
                target_stock.get("name"),
                code,
                target_id,
                "bundle_completed",
                candidate_stock=target_stock,
                probe_bundle_id=probe_bundle_id,
                requested_qty=requested_entry_qty,
                filled_qty=cum_filled_qty,
                avg_buy_price=round(float(new_avg or 0.0), 4),
                actual_order_submitted=True,
                broker_order_forbidden=False,
                runtime_effect=True,
                **_probe_observation_contract_fields(target_stock),
            )
        if target_stock.get("rising_missed_one_share_scout"):
            target_stock["rising_missed_scout_upgraded"] = True

    strategy = normalize_strategy(target_stock.get("strategy"))
    pos_tag = normalize_position_tag(strategy, target_stock.get("position_tag"))
    target_stock["position_tag"] = pos_tag
    if pos_tag == OPENING_ROTATION_POSITION_TAG:
        target_stock.setdefault(
            "opening_rotation_entry_time_bucket",
            opening_rotation_entry_time_bucket(now),
        )
        target_stock.setdefault(
            "opening_rotation_window_version",
            opening_rotation_entry_window_version(),
        )
        target_stock.update(
            {
                "opening_rotation_episode_phase": "BUY_FILLED",
                "opening_rotation_buy_fill_price": int(new_avg or exec_price or 0),
                "opening_rotation_buy_filled_at": now.isoformat(),
                "opening_rotation_buy_order_no": order_no or "-",
                "opening_rotation_buy_submit_to_fill_ms": round(
                    max(
                        0.0,
                        time.time()
                        - _safe_float(target_stock.get("order_time"), time.time()),
                    )
                    * 1000.0,
                    3,
                ),
                # Opening removes only the strategy soft stop.  These values
                # keep the common hard/protect emergency surfaces visible to
                # both the fast monitor and the regular holding loop.
                "hard_stop_pct": float(
                    getattr(TRADING_RULES, "SCALP_HARD_STOP", -2.5) or -2.5
                ),
                "hard_stop_emergency_pct": float(
                    getattr(
                        TRADING_RULES,
                        "SCALP_PROTECT_TRAILING_EMERGENCY_PCT",
                        -2.0,
                    )
                    or -2.0
                ),
                "hard_stop_grace_sec": 0,
                "protect_profit_pct": None,
                "scale_in_locked": True,
            }
        )
        if requested_entry_qty > 0 and cum_filled_qty >= requested_entry_qty:
            _submit_opening_rotation_profit_order(
                target_stock,
                code=code,
                buy_fill_price=int(new_avg or exec_price or 0),
                filled_qty=int(new_qty or 0),
            )

    if strategy == "SCALPING" and is_default_position_tag(strategy, pos_tag):
        target_stock["exit_mode"] = "SCALP_PRESET_TP"

        base_buy_price = int(target_stock.get("buy_price") or exec_price or 0)
        if base_buy_price <= 0:
            base_buy_price = exec_price

        target_stock["preset_tp_price"] = 0
        preset_tp_ord_no_before = str(
            target_stock.get("preset_tp_ord_no", "") or ""
        ).strip()
        preset_hard_stop_pct = float(
            getattr(TRADING_RULES, "SCALP_PRESET_HARD_STOP_PCT", -0.7) or -0.7
        )
        preset_hard_stop_grace_sec = int(
            getattr(TRADING_RULES, "SCALP_PRESET_HARD_STOP_GRACE_SEC", 0) or 0
        )
        preset_hard_stop_emergency_pct = float(
            getattr(
                TRADING_RULES,
                "SCALP_PRESET_HARD_STOP_EMERGENCY_PCT",
                min(preset_hard_stop_pct - 0.5, -1.2),
            )
            or min(preset_hard_stop_pct - 0.5, -1.2)
        )
        target_stock["hard_stop_pct"] = preset_hard_stop_pct
        target_stock["hard_stop_grace_sec"] = preset_hard_stop_grace_sec
        target_stock["hard_stop_emergency_pct"] = preset_hard_stop_emergency_pct
        target_stock["protect_profit_pct"] = None
        target_stock["ai_review_done"] = False
        target_stock["ai_review_score"] = None
        target_stock["ai_review_action"] = None
        target_stock["last_ai_reviewed_at"] = None
        if not target_stock.get("entry_lifecycle_conflict"):
            target_stock["exit_requested"] = False
            target_stock["exit_order_type"] = None
            target_stock["exit_order_time"] = None

        sell_qty = int(target_stock.get("buy_qty") or exec_qty or 0)
        refreshed = _refresh_scalp_preset_exit_order(target_stock, code, sell_qty)
        preset_tp_ord_no_after = str(
            target_stock.get("preset_tp_ord_no", "") or ""
        ).strip()
        preset_tp_price = int(target_stock.get("preset_tp_price") or 0)

        if not refreshed:
            preset_sync_status = "REFRESH_FAILED"
            preset_sync_reason = "legacy_preset_cancel_failed"
        else:
            preset_sync_status = "DISABLED_TRAILING_UNIFIED"
            preset_sync_reason = "preset_tp_removed_trailing_unified"

        log_info(
            f"[SCALP_TRAILING_UNIFIED] {target_stock.get('name')} "
            f"preset TP setup skipped; scalp_trailing_take_profit owns exit."
        )
        _log_holding_pipeline(
            target_stock.get("name"),
            code,
            target_id,
            "preset_exit_setup_disabled_trailing_unified",
            preset_tp_price=int(preset_tp_price or 0),
            qty=int(sell_qty or 0),
            ord_no=preset_tp_ord_no_before or "-",
            sync_status=preset_sync_status,
            sync_reason=preset_sync_reason,
        )

    _log_holding_pipeline(
        target_stock.get("name"),
        code,
        target_id,
        "position_rebased_after_fill",
        candidate_stock=target_stock,
        observed_at=now,
        order_no=order_no or "-",
        execution_no=execution_no or "-",
        fill_price=round(float(exec_price or 0.0), 4),
        fill_qty=int(effective_exec_qty or 0),
        raw_fill_qty=int(exec_qty or 0),
        order_requested_qty=int(order_requested_qty or 0),
        order_filled_qty=int(order_filled_qty or 0),
        order_remaining_qty=int(entry_receipt.get("remaining_qty") or 0),
        cumulative_exec_amount=int(entry_receipt.get("cumulative_amount") or 0),
        receipt_economics_complete=bool(entry_receipt.get("economics_complete")),
        receipt_quantity_contract_complete=bool(
            entry_receipt.get("quantity_contract_complete")
        ),
        receipt_unit_fill_consistent=bool(
            entry_receipt.get("unit_fill_consistent", True)
        ),
        receipt_unit_qty_matches_delta=entry_receipt.get("unit_qty_matches_delta"),
        cum_filled_qty=int(cum_filled_qty or 0),
        requested_qty=int(requested_entry_qty or 0),
        remaining_qty=int(remaining_qty or 0),
        avg_buy_price=f"{float(new_avg or 0):.2f}",
        entry_mode=entry_mode,
        fill_quality=fill_quality,
        preset_tp_price=int(preset_tp_price or 0),
        preset_tp_ord_no_before=preset_tp_ord_no_before or "-",
        preset_tp_ord_no_after=preset_tp_ord_no_after or "-",
        sync_status=preset_sync_status,
        **_broker_execution_provenance_fields(target_stock),
        **_probe_venue_provenance_fields(target_stock),
    )
    if strategy == "SCALPING" and is_default_position_tag(strategy, pos_tag):
        if preset_sync_status == "DISABLED_TRAILING_UNIFIED":
            sync_stage = "preset_exit_sync_disabled_trailing_unified"
        else:
            sync_stage = (
                "preset_exit_sync_ok"
                if preset_sync_status == "OK"
                else "preset_exit_sync_mismatch"
            )
        _log_holding_pipeline(
            target_stock.get("name"),
            code,
            target_id,
            sync_stage,
            entry_mode=entry_mode,
            fill_quality=fill_quality,
            requested_qty=int(requested_entry_qty or 0),
            buy_qty=int(new_qty or 0),
            preset_tp_qty=int(target_stock.get("preset_tp_qty", 0) or 0),
            preset_tp_price=int(preset_tp_price or 0),
            preset_tp_ord_no_before=preset_tp_ord_no_before or "-",
            preset_tp_ord_no_after=preset_tp_ord_no_after or "-",
            sync_status=preset_sync_status,
            sync_reason=preset_sync_reason,
        )

    _log_holding_pipeline(
        target_stock.get("name"),
        code,
        target_id,
        "holding_started",
        candidate_stock=target_stock,
        observed_at=now,
        metric_role="execution_quality_real_only",
        decision_authority="broker_receipt_observation_only",
        runtime_effect=False,
        forbidden_uses="runtime_threshold_apply/provider_route_change/bot_restart/sim_execution_quality_claim",
        actual_order_submitted=True,
        broker_order_forbidden=False,
        execution_no=execution_no or "-",
        strategy=target_stock.get("strategy"),
        position_tag=target_stock.get("position_tag"),
        opening_rotation_entry_time_bucket=target_stock.get(
            "opening_rotation_entry_time_bucket", "-"
        ),
        opening_rotation_entry_best_bid=target_stock.get(
            "opening_rotation_entry_best_bid", "-"
        ),
        opening_rotation_window_version=target_stock.get(
            "opening_rotation_window_version", "-"
        ),
        opening_rotation_episode_id=target_stock.get(
            "opening_rotation_episode_id", "-"
        ),
        opening_rotation_episode_promotion_id=target_stock.get(
            "opening_rotation_episode_promotion_id", "-"
        ),
        opening_rotation_profile_id=target_stock.get(
            "opening_rotation_profile_id", "-"
        ),
        opening_rotation_policy_hash=target_stock.get(
            "opening_rotation_policy_hash", "-"
        ),
        opening_rotation_policy_schema_version=target_stock.get(
            "opening_rotation_policy_schema_version", "-"
        ),
        opening_rotation_margin_one_share_authorized=bool(
            target_stock.get("opening_rotation_margin_one_share_authorized", False)
        ),
        opening_rotation_margin_authority_reason=target_stock.get(
            "opening_rotation_margin_authority_reason", "not_evaluated"
        ),
        opening_rotation_margin_rate=target_stock.get(
            "opening_rotation_margin_rate", 0
        ),
        opening_rotation_margin_orderable_amount=target_stock.get(
            "opening_rotation_margin_orderable_amount", 0
        ),
        opening_rotation_margin_orderable_qty_cap=target_stock.get(
            "opening_rotation_margin_orderable_qty_cap", 0
        ),
        opening_rotation_margin_requested_unit_price=target_stock.get(
            "opening_rotation_margin_requested_unit_price", 0
        ),
        opening_rotation_margin_cash_guard_bypassed=bool(
            target_stock.get("opening_rotation_margin_cash_guard_bypassed", False)
        ),
        opening_rotation_margin_order_api=target_stock.get(
            "opening_rotation_margin_order_api"
        ),
        opening_rotation_margin_credit_order_api_used=target_stock.get(
            "opening_rotation_margin_credit_order_api_used"
        ),
        **_receipt_snapshot(target_stock, _GENERAL_ENTRY_MARGIN_POSITION_KEYS),
        buy_price=f"{float(new_avg or 0):.2f}",
        buy_qty=int(new_qty or 0),
        fill_price=round(float(exec_price or 0.0), 4),
        fill_qty=int(effective_exec_qty or 0),
        raw_fill_qty=int(exec_qty or 0),
        order_requested_qty=int(order_requested_qty or 0),
        order_filled_qty=int(order_filled_qty or 0),
        order_remaining_qty=int(entry_receipt.get("remaining_qty") or 0),
        cumulative_exec_amount=int(entry_receipt.get("cumulative_amount") or 0),
        receipt_economics_complete=bool(entry_receipt.get("economics_complete")),
        receipt_quantity_contract_complete=bool(
            entry_receipt.get("quantity_contract_complete")
        ),
        receipt_unit_fill_consistent=bool(
            entry_receipt.get("unit_fill_consistent", True)
        ),
        entry_mode=entry_mode,
        entry_submit_ai_score=(
            f"{float(submit_ai_score):.1f}" if submit_ai_score is not None else "-"
        ),
        holding_ai_score_seeded_from_entry=holding_ai_seeded,
        **_broker_execution_provenance_fields(target_stock),
        **_probe_venue_provenance_fields(target_stock),
        **scout_ai_execution_attribution_fields(
            target_stock,
            stage="holding_started",
            actual_order_submitted=True,
        ),
    )

    buy_receipt_snapshot = _receipt_snapshot(target_stock, _BUY_RECEIPT_SNAPSHOT_KEYS)
    entry_partial_fill_pending = (
        requested_entry_qty > 0 and cum_filled_qty < requested_entry_qty
    )
    buy_receipt_snapshot.update(
        {
            "entry_fill_quality": fill_quality,
            "entry_requested_qty": int(requested_entry_qty or 0),
            "entry_cum_filled_qty": int(cum_filled_qty or 0),
            "entry_remaining_qty": int(remaining_qty or 0),
            "entry_partial_fill_pending": entry_partial_fill_pending,
        }
    )
    buy_receipt_snapshot["buy_execution_notified"] = (
        bool(buy_receipt_snapshot.get("buy_execution_notified", False))
        or entry_partial_fill_pending
    )
    if entry_partial_fill_pending:
        partial_notice_sent = _publish_entry_partial_fill_message(
            target_stock,
            avg_buy_price=float(new_avg or exec_price or 0),
            cum_filled_qty=int(cum_filled_qty or 0),
            requested_entry_qty=int(requested_entry_qty or 0),
            remaining_qty=int(remaining_qty or 0),
        )
        log_info(
            f"[ENTRY_PARTIAL_FILL_NOTICE_DEFERRED] {target_stock.get('name')}({code}) "
            f"filled={cum_filled_qty}/{requested_entry_qty} remaining={remaining_qty} "
            f"partial_notice_sent={partial_notice_sent} "
            "reason=wait_full_entry_bundle_before_buy_execution_telegram"
        )
    elif not buy_receipt_snapshot.get("buy_execution_notified"):
        target_stock["buy_execution_notified"] = True
        target_stock.pop("entry_partial_fill_notified_qty", None)
        target_stock.pop("entry_partial_fill_deferred_notice", None)
        target_stock.pop("entry_partial_fill_deferred_at", None)
        target_stock.pop("pending_buy_msg", None)

    threading.Thread(
        target=_update_db_for_buy,
        args=(target_id, exec_price, now, buy_receipt_snapshot),
        daemon=True,
    ).start()


def handle_real_execution(exec_data):
    """
    웹소켓에서 주문 체결(00) 통보가 오면 이 함수가 즉시 실행됩니다.
    고유 ID(id)를 추적하여 해당 매매 건의 실제 체결가를 정확히 기록합니다.
    """
    code = str(exec_data.get("code", "")).strip()[:6]
    exec_type = str(exec_data.get("type", "")).upper()
    order_no = str(exec_data.get("order_no", "") or "").strip()

    if exec_type not in {"BUY", "SELL"}:
        log_error(
            f"[EXECUTION_SIDE_BLOCKED] code={code or '-'} "
            f"order_no={order_no or '-'} type={exec_type or '-'}"
        )
        return

    exec_price = _optional_abs_int(exec_data.get("price")) or 0
    exec_qty = _optional_abs_int(exec_data.get("qty")) or 0

    order_qty = _optional_abs_int(exec_data.get("order_qty"))
    remaining_qty = _optional_abs_int(exec_data.get("remaining_qty"))
    cumulative_exec_amount = _optional_abs_int(exec_data.get("cumulative_exec_amount"))
    execution_no = str(exec_data.get("execution_no", "") or "").strip()
    unit_exec_price = _optional_abs_int(exec_data.get("unit_exec_price"))
    unit_exec_qty = _optional_abs_int(exec_data.get("unit_exec_qty"))

    if not code or exec_qty <= 0:
        return

    received_at = datetime.now(_KST)
    broker_observed_at, broker_execution_fields = _broker_execution_context(
        exec_data, received_at=received_at
    )
    state = _get_fast_state(code)
    if state and exec_qty > 0:
        with state["lock"]:
            matched = False

            if exec_type == "BUY":
                if order_no and order_no == str(state.get("buy_ord_no", "")):
                    prior_buy_qty = max(
                        0,
                        int(
                            state.get(
                                "last_buy_receipt_cumulative_qty",
                                state.get("cum_buy_qty", 0),
                            )
                            or 0
                        ),
                    )
                    prior_buy_amount = max(
                        0,
                        int(
                            state.get(
                                "last_buy_receipt_cumulative_amount",
                                state.get("cum_buy_amount", 0),
                            )
                            or 0
                        ),
                    )
                    buy_executions = state.get("buy_receipt_executions_by_no")
                    buy_executions = (
                        dict(buy_executions) if isinstance(buy_executions, dict) else {}
                    )
                    buy_signature = _execution_receipt_signature(
                        cumulative_qty=exec_qty,
                        order_qty=order_qty,
                        remaining_qty=remaining_qty,
                        cumulative_exec_amount=cumulative_exec_amount,
                        unit_exec_price=unit_exec_price,
                        unit_exec_qty=unit_exec_qty,
                    )
                    execution_conflict = _execution_number_conflict_reason(
                        {order_no: buy_executions},
                        order_key=order_no,
                        execution_no=execution_no,
                        signature=buy_signature,
                    )
                    fast_buy_receipt = (
                        {
                            "status": "invalid",
                            "reason": execution_conflict,
                        }
                        if execution_conflict
                        else _resolve_cumulative_buy_order_receipt(
                            raw_price=exec_price,
                            raw_cumulative_qty=exec_qty,
                            requested_qty=max(0, int(state.get("req_buy_qty", 0) or 0)),
                            previous_qty=prior_buy_qty,
                            previous_amount=prior_buy_amount,
                            previous_economics_complete=bool(
                                state.get("buy_receipt_economics_complete", True)
                            ),
                            order_qty=order_qty,
                            remaining_qty=remaining_qty,
                            cumulative_exec_amount=cumulative_exec_amount,
                            unit_exec_price=unit_exec_price,
                            unit_exec_qty=unit_exec_qty,
                        )
                    )
                    if fast_buy_receipt.get("status") == "invalid":
                        state["buy_receipt_source_gap"] = str(
                            fast_buy_receipt.get("reason") or "fast_buy_receipt_invalid"
                        )
                        log_error(
                            f"[FAST_BUY_RECEIPT_RECONCILE_BLOCKED] {code} "
                            f"ord_no={order_no} reason={fast_buy_receipt.get('reason')}"
                        )
                        _request_broker_snapshot_refresh(
                            code, reason="fast_buy_receipt_reconcile_blocked"
                        )
                    else:
                        holder = {order_no: buy_executions}
                        _remember_execution_number(
                            holder,
                            order_key=order_no,
                            execution_no=execution_no,
                            signature=buy_signature,
                        )
                        state["buy_receipt_executions_by_no"] = holder[order_no]
                        if fast_buy_receipt.get("status") != "duplicate":
                            state["cum_buy_qty"] += int(
                                fast_buy_receipt["incremental_qty"]
                            )
                            state["cum_buy_amount"] += int(
                                fast_buy_receipt["incremental_amount"]
                            )
                            state["avg_buy_price"] = _avg_from_totals(
                                state["cum_buy_amount"], state["cum_buy_qty"]
                            )
                            state["last_buy_receipt_cumulative_qty"] = int(
                                fast_buy_receipt["cumulative_qty"]
                            )
                            state["last_buy_receipt_cumulative_amount"] = int(
                                fast_buy_receipt["cumulative_amount"]
                            )
                            state["buy_receipt_economics_complete"] = bool(
                                fast_buy_receipt.get("economics_complete")
                            )
                    state["updated_at"] = _now_ts()
                    matched = True

            elif exec_type == "SELL":
                valid_sell_ord_nos = {
                    str(state.get("sell_ord_no", "") or ""),
                    str(state.get("pending_cancel_ord_no", "") or ""),
                }
                if order_no and order_no in valid_sell_ord_nos:
                    fast_sell_receipt = _resolve_fast_sell_execution_receipt(
                        state,
                        order_no=order_no,
                        exec_price=exec_price,
                        cumulative_exec_qty=exec_qty,
                        order_qty=order_qty,
                        remaining_qty=remaining_qty,
                        cumulative_exec_amount=cumulative_exec_amount,
                        execution_no=execution_no,
                        unit_exec_price=unit_exec_price,
                        unit_exec_qty=unit_exec_qty,
                    )
                    if fast_sell_receipt.get("status") == "invalid":
                        state["sell_receipt_source_gap"] = str(
                            fast_sell_receipt.get("reason")
                            or "fast_sell_receipt_invalid"
                        )
                        log_error(
                            f"[FAST_SELL_RECEIPT_RECONCILE_BLOCKED] {code} "
                            f"ord_no={order_no} "
                            f"reason={fast_sell_receipt.get('reason')}"
                        )
                        _request_broker_snapshot_refresh(
                            code, reason="fast_sell_receipt_reconcile_blocked"
                        )
                    state["updated_at"] = _now_ts()
                    matched = True

            if matched:
                state.update(broker_execution_fields)

        if matched:
            persisted = True
            if callable(_persist_fast_state_callback):
                persisted = bool(_persist_fast_state_callback(code, state))
            if not persisted:
                with state["lock"]:
                    state["status"] = "RECOVERY_REQUIRED"
                    state["s15_recovery_reason"] = "receipt_persistence_failed"
                return
            if exec_type == "SELL" and callable(_finalize_fast_state_callback):
                _finalize_fast_state_callback(code, state)
            return

    now = broker_observed_at
    now_t = now.time()

    with _active_state_lock():
        target_stock = _find_execution_target(
            code,
            exec_type,
            order_no,
            order_qty=order_qty,
            remaining_qty=remaining_qty,
            cumulative_exec_qty=exec_qty,
        )
        if not target_stock:
            ignore_context = _execution_ignore_context(code, exec_type, order_no)
            log_info(
                f"[EXEC_IGNORED] no matching active order. code={code}, "
                f"type={exec_type}, order_no={order_no} {ignore_context}"
            )
            return

        target_id = target_stock.get("id")
        if not target_id:
            log_error(
                f"🚨 [영수증] 종목 {code}의 고유 ID가 메모리에 없습니다. DB 업데이트가 불가능합니다."
            )
            return
        target_stock.update(broker_execution_fields)
        is_scalp_revive = False

        # ==========================================
        # 1️⃣ DB 상태 업데이트 (ID 기반 정밀 타격)
        # ==========================================
        if exec_type == "BUY":
            pending_add = bool(target_stock.get("pending_add_order"))
            pending_ord_no = str(
                target_stock.get("pending_add_ord_no", "") or ""
            ).strip()
            pending_ord_nos = {
                part.strip() for part in pending_ord_no.split(",") if part.strip()
            }
            is_add_fill = pending_add and (
                not order_no or order_no in pending_ord_nos or not pending_ord_nos
            )

            if is_add_fill:
                _handle_add_buy_execution(
                    target_id=target_id,
                    target_stock=target_stock,
                    code=code,
                    order_no=order_no,
                    exec_price=exec_price,
                    exec_qty=exec_qty,
                    now=now,
                    order_qty=order_qty,
                    remaining_qty=remaining_qty,
                    cumulative_exec_amount=cumulative_exec_amount,
                    execution_no=execution_no,
                    unit_exec_price=unit_exec_price,
                    unit_exec_qty=unit_exec_qty,
                )
            elif pending_add and str(target_stock.get("status") or "") == "HOLDING":
                log_info(
                    f"[ADD_FILL_IGNORED] {target_stock.get('name')}({code}) "
                    f"ord_no={order_no or '-'} pending_add_ord_no={pending_ord_no or '-'} "
                    "reason=order_not_in_pending_add_bundle"
                )
                _request_broker_snapshot_refresh(
                    code, reason="scale_in_buy_receipt_order_identity_blocked"
                )
            else:
                _handle_entry_buy_execution(
                    target_id=target_id,
                    target_stock=target_stock,
                    code=code,
                    order_no=order_no,
                    exec_price=exec_price,
                    exec_qty=exec_qty,
                    now=now,
                    order_qty=order_qty,
                    remaining_qty=remaining_qty,
                    cumulative_exec_amount=cumulative_exec_amount,
                    execution_no=execution_no,
                    unit_exec_price=unit_exec_price,
                    unit_exec_qty=unit_exec_qty,
                )

        elif exec_type == "SELL":
            sell_context = _resolve_sell_execution_context(
                target_id, target_stock, exec_price, now_t
            )
            if not sell_context:
                return
            record, safe_buy_price, profit_rate, strategy, is_scalp_revive = (
                sell_context
            )

            if target_stock.get("nxt_rising_missed_tp1_partial_pending"):
                _handle_nxt_rising_missed_tp1_partial_sell_execution(
                    target_id=target_id,
                    target_stock=target_stock,
                    code=code,
                    order_no=order_no,
                    exec_price=exec_price,
                    exec_qty=exec_qty,
                    now=now,
                    safe_buy_price=safe_buy_price,
                    order_qty=order_qty,
                    remaining_qty=remaining_qty,
                    cumulative_exec_amount=cumulative_exec_amount,
                    execution_no=execution_no,
                    unit_exec_price=unit_exec_price,
                    unit_exec_qty=unit_exec_qty,
                )
                return

            sell_receipt = _resolve_sell_execution_receipt(
                target_stock,
                order_no=order_no,
                exec_price=exec_price,
                cumulative_exec_qty=exec_qty,
                expected_position_qty=(
                    _safe_int(getattr(record, "buy_qty", 0), 0)
                    or _safe_int(target_stock.get("buy_qty"), 0)
                ),
                buy_price=safe_buy_price,
                order_qty=order_qty,
                remaining_qty=remaining_qty,
                cumulative_exec_amount=cumulative_exec_amount,
                execution_no=execution_no,
                unit_exec_price=unit_exec_price,
                unit_exec_qty=unit_exec_qty,
            )
            if sell_receipt.get("status") == "invalid":
                log_error(
                    f"[SELL_RECEIPT_RECONCILE_BLOCKED] "
                    f"{target_stock.get('name')}({code}) ord_no={order_no or '-'} "
                    f"reason={sell_receipt.get('reason')} raw_qty={exec_qty} "
                    f"order_qty={order_qty} remaining_qty={remaining_qty}"
                )
                _request_broker_snapshot_refresh(
                    code, reason="sell_receipt_reconcile_blocked"
                )
                return
            if sell_receipt.get("status") == "duplicate":
                return
            if order_no and target_stock.get("sell_submit_pending"):
                target_stock["sell_odno"] = order_no
                target_stock.pop("sell_submit_pending", None)
                target_stock.pop("sell_submit_requested_qty", None)
                target_stock.pop("sell_submit_started_at", None)
            if sell_receipt.get("status") == "replacement_reconcile_required":
                replacement_order_no = str(
                    target_stock.get(_SELL_EXECUTION_RECEIPT_STATE_KEY, {}).get(
                        "replacement_order_no", ""
                    )
                    or ""
                ).strip()
                cancel_confirmed = False
                if replacement_order_no:
                    try:
                        from src.engine import sniper_trade_utils

                        cancel_result = (
                            sniper_trade_utils.send_cancel_order_with_exchange_retry(
                                code=code,
                                orig_ord_no=replacement_order_no,
                                token=KIWOOM_TOKEN,
                                qty=0,
                            )
                        )
                        cancel_confirmed = _is_ok_response(cancel_result)
                    except Exception as exc:
                        log_error(
                            f"[SELL_REPLACEMENT_CANCEL_FAILED] {code} "
                            f"ord_no={replacement_order_no}: {exc}"
                        )
                target_stock.update(
                    {
                        "status": "SELL_ORDERED",
                        "sell_odno": replacement_order_no,
                        "sell_cancel_reconciliation_required": True,
                        "sell_cancel_reconciliation_source": (
                            "late_prior_fill_replacement_cancel_acknowledged"
                            if cancel_confirmed
                            else "late_prior_fill_replacement_cancel_unconfirmed"
                        ),
                        "sell_cancel_reconciliation_retry_at": time.time() + 1.0,
                    }
                )
                _persist_sell_receipt_recovery_or_interlock(
                    target_stock,
                    code=code,
                    reason="late_prior_fill_replacement_cancel",
                )
                _request_broker_snapshot_refresh(
                    code,
                    reason="late_prior_fill_replacement_reconciliation",
                )
                return
            if sell_receipt.get("status") == "partial":
                _log_standard_sell_partial_execution(
                    target_stock,
                    code=code,
                    target_id=target_id,
                    now=now,
                    receipt=sell_receipt,
                    buy_price=safe_buy_price,
                )
                return
            if not all(
                (
                    sell_receipt.get("economics_complete") is True,
                    sell_receipt.get("quantity_contract_complete") is True,
                )
            ):
                log_error(
                    f"[SELL_RECEIPT_FINAL_CONTRACT_BLOCKED] "
                    f"{target_stock.get('name')}({code}) ord_no={order_no or '-'} "
                    f"economics_complete={sell_receipt.get('economics_complete')} "
                    f"quantity_contract_complete="
                    f"{sell_receipt.get('quantity_contract_complete')}"
                )
                _request_broker_snapshot_refresh(
                    code, reason="sell_receipt_final_contract_incomplete"
                )
                return

            effective_exec_price = int(
                round(float(sell_receipt.get("incremental_price") or 0.0))
            )
            if effective_exec_price <= 0:
                _request_broker_snapshot_refresh(
                    code, reason="sell_receipt_effective_price_missing"
                )
                return

            if is_scalp_revive:
                if not _handle_scalp_revive_sell_execution(
                    target_id=target_id,
                    target_stock=target_stock,
                    code=code,
                    exec_price=effective_exec_price,
                    exec_qty=exec_qty,
                    now=now,
                    profit_rate=profit_rate,
                    safe_buy_price=safe_buy_price,
                    strategy=strategy,
                    sell_receipt=sell_receipt,
                    order_no=order_no,
                ):
                    return
            else:
                _finalize_standard_sell_execution(
                    target_id=target_id,
                    exec_price=effective_exec_price,
                    now=now,
                    target_stock=target_stock,
                    strategy=strategy,
                    is_scalp_revive=is_scalp_revive,
                    code=code,
                    sell_receipt=sell_receipt,
                    order_no=order_no,
                )

    # 메모리 업데이트는 각 조건문 내에서 이미 수행됨
