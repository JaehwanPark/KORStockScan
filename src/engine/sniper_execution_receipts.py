"""Order execution receipt handlers for the sniper engine."""

import os
import threading
import time
from datetime import datetime
from typing import Any

from src.database.models import RecommendationHistory
from src.engine.scalping.opening_rotation import (
    POSITION_TAG as OPENING_ROTATION_POSITION_TAG,
    entry_time_bucket as opening_rotation_entry_time_bucket,
    entry_window_version as opening_rotation_entry_window_version,
)
from src.engine.scalping.entry_split_order_plan import (
    trip_probe_runtime_circuit,
    update_probe_runtime_bundle,
)
from src.engine.scalping.early_volatility_partial_tp import (
    POLICY_VERSION as EARLY_VOLATILITY_TP_POLICY_VERSION,
    EarlyTPRuntimeLedger,
)
from src.engine.scalping.position_peak_ledger import POSITION_PEAK_LEDGER
from src.engine.sniper_entry_state import (
    ENTRY_LOCK,
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

# Receipt module의 임시/DB 작업은 독립 락으로 직렬화하고,
# ACTIVE_TARGETS 같은 shared runtime truth는 주입된 _STATE_LOCK(실운영에서는 ENTRY_LOCK)으로만 만집니다.
# 테스트/단독 사용 시에는 _STATE_LOCK이 없을 수 있으므로 RECEIPT_LOCK을 fallback으로 둡니다.
RECEIPT_LOCK = threading.RLock()
_STATE_LOCK = None


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
    return fields


_BUY_RECEIPT_SNAPSHOT_KEYS = (
    "buy_execution_notified",
    "buy_price",
    "buy_qty",
    "initial_buy_qty",
    "scale_in_filled_qty",
    "code",
    "actual_order_submitted",
    "msg_audience",
    "name",
    "opening_rotation_entry_time_bucket",
    "opening_rotation_window_version",
    "pending_buy_msg",
    "scalp_live_simulator",
    "simulation_book",
    "simulation_owner",
    "swing_live_order_dry_run",
)
_SELL_RECEIPT_SNAPSHOT_KEYS = (
    "actual_order_submitted",
    "broker_order_forbidden",
    "buy_price",
    "buy_qty",
    "code",
    "early_volatility_tp_fill_amount",
    "early_volatility_tp_filled_qty",
    "early_volatility_tp_avg_sell_price",
    "early_volatility_tp_realized_pnl_krw",
    "fast_exit_decision_mark_price",
    "fast_exit_decision_executable_sell_price",
    "fast_exit_decision_peak_price",
    "fast_exit_decision_quote_state",
    "fast_exit_decision_quote_reason",
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
    "msg_audience",
    "name",
    "nxt_rising_missed_tp1_partial_fill_amount",
    "nxt_rising_missed_tp1_partial_filled_qty",
    "nxt_rising_missed_tp1_partial_avg_sell_price",
    "nxt_rising_missed_tp1_partial_realized_pnl_krw",
    "no_scale_in_counterfactual_profit_pct",
    "opening_rotation_entry_time_bucket",
    "opening_rotation_window_version",
    "pending_sell_msg",
    "post_add_avg_price",
    "post_add_qty",
    "position_tag",
    "pre_add_avg_price",
    "pre_add_qty",
    "scalp_live_simulator",
    "scale_in_incremental_realized_delta_pct",
    "simulation_book",
    "simulation_owner",
    "strategy",
    "swing_live_order_dry_run",
)
_ADD_RECEIPT_SNAPSHOT_KEYS = (
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
    "_add_receipt_requested_by_order_no",
    "_add_receipt_filled_by_order_no",
    "_add_receipt_filled_amount_by_order_no",
    "pending_add_notice_by_order_no",
    "scale_in_receipt_reconciled_before_ordno_bind",
    "add_order_time",
    "add_odno",
)
_EARLY_VOLATILITY_TP_RESET_KEYS = (
    "early_volatility_tp_state",
    "early_volatility_tp_position_cycle_id",
    "early_volatility_tp_ord_no",
    "early_volatility_tp_requested_qty",
    "early_volatility_tp_filled_qty",
    "early_volatility_tp_fill_amount",
    "early_volatility_tp_avg_sell_price",
    "early_volatility_tp_original_qty",
    "early_volatility_tp_limit_price",
    "early_volatility_tp_submitted_at",
    "early_volatility_tp_expires_at",
    "early_volatility_tp_policy_version",
    "early_volatility_tp_cohort",
    "early_volatility_tp_broker_route",
    "early_volatility_tp_entry_lineage",
    "early_volatility_tp_applied",
    "early_volatility_tp_rearm_forbidden",
    "early_volatility_tp_next_retry_at",
    "early_volatility_tp_reconciled_holding_qty",
    "early_volatility_tp_last_decision_reason",
    "early_volatility_tp_last_error",
    "early_volatility_tp_last_fill_at",
    "early_volatility_tp_completed_at",
    "early_volatility_tp_realized_profit_pct",
    "early_volatility_tp_realized_pnl_krw",
    "early_volatility_tp_runner_peak_reset_pending",
    "early_volatility_tp_runner_peak_price",
    "early_volatility_tp_runner_started_at",
    "early_volatility_tp_exit_recheck_required",
    "early_volatility_tp_scale_in_recheck_required",
    "early_volatility_tp_last_observation_signature",
    "early_volatility_tp_logged_observation_signature",
    "early_volatility_tp_cancel_reason",
    "early_volatility_tp_cancel_requested_at",
    "early_volatility_tp_cancelled_at",
    "early_volatility_tp_notice_status",
    "early_volatility_tp_notice_at",
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
_SELL_REVIVE_RESET_KEYS = (
    "odno",
    "order_time",
    "order_price",
    "buy_time",
    "target_buy_price",
    "pending_buy_msg",
    "pending_sell_msg",
    "sell_odno",
    "sell_order_time",
    "sell_target_price",
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
    "entry_split_probe_scale_in_recheck_reason",
    "entry_split_probe_source_quality_recheck_released",
    "entry_split_probe_source_quality_recheck_released_at",
    "entry_split_probe_source_quality_recheck_unfilled_qty",
    "entry_split_probe_source_quality_recheck_reason",
    "entry_split_probe_source_quality_recheck_pending",
    "entry_split_probe_abort_reason",
    "entry_split_probe_ai_action_at_submit",
    "probe_confirmation_count",
    "probe_confirmation_last_at",
    "probe_confirmation_last_state",
    "probe_confirmation_last_signature",
    "probe_expand_forbidden",
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
    *_FAST_EXIT_DECISION_RESET_KEYS,
    *_EXIT_DECISION_RESET_KEYS,
    *_POSITION_PEAK_RESET_KEYS,
    *_EARLY_VOLATILITY_TP_RESET_KEYS,
    "rising_missed_scout_upgraded",
)
_SELL_COMPLETE_RESET_KEYS = (
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
    "entry_split_probe_scale_in_recheck_reason",
    "entry_split_probe_source_quality_recheck_released",
    "entry_split_probe_source_quality_recheck_released_at",
    "entry_split_probe_source_quality_recheck_unfilled_qty",
    "entry_split_probe_source_quality_recheck_reason",
    "entry_split_probe_source_quality_recheck_pending",
    "entry_split_probe_abort_reason",
    "entry_split_probe_ai_action_at_submit",
    "probe_confirmation_count",
    "probe_confirmation_last_at",
    "probe_confirmation_last_state",
    "probe_confirmation_last_signature",
    "probe_expand_forbidden",
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
    *_FAST_EXIT_DECISION_RESET_KEYS,
    *_EXIT_DECISION_RESET_KEYS,
    *_POSITION_PEAK_RESET_KEYS,
    *_EARLY_VOLATILITY_TP_RESET_KEYS,
    "rising_missed_scout_upgraded",
)
_ENTRY_RECEIPT_FILLED_BY_ORDER_KEY = "_entry_receipt_filled_by_order_no"
_ENTRY_RECEIPT_REQUESTED_BY_ORDER_KEY = "_entry_receipt_requested_by_order_no"
_ENTRY_RECEIPT_NO_ORDER_KEY = "__entry_without_order_no__"
_ADD_RECEIPT_FILLED_BY_ORDER_KEY = "_add_receipt_filled_by_order_no"
_ADD_RECEIPT_REQUESTED_BY_ORDER_KEY = "_add_receipt_requested_by_order_no"
_ADD_RECEIPT_AMOUNT_BY_ORDER_KEY = "_add_receipt_filled_amount_by_order_no"
_ADD_RECEIPT_NO_ORDER_KEY = "__add_without_order_no__"
_EARLY_VOLATILITY_TP_LEDGER = EarlyTPRuntimeLedger()


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
    global _probe_fill_continuation_callback

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


def _log_holding_pipeline(name, code, target_id, stage, **fields):
    emit_pipeline_event(
        "HOLDING_PIPELINE",
        name,
        code,
        stage,
        record_id=target_id,
        fields=fields,
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


def _receipt_snapshot(
    target_stock: dict[str, Any], keys: tuple[str, ...]
) -> dict[str, Any]:
    return {key: target_stock.get(key) for key in keys}


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


def _resolve_entry_effective_fill_qty(
    *,
    target_stock: dict[str, Any],
    code: str,
    order_no: str,
    exec_qty: int,
) -> tuple[int, int, int]:
    """Return the entry fill delta that may be applied to runtime truth.

    Kiwoom execution notices can repeat a final fill or report cumulative
    quantities for the same order number. Entry orders with a known requested
    quantity must therefore be capped by remaining leg quantity before mutating
    buy_qty/avg price. The per-order ledger intentionally survives terminal
    entry-order grace so delayed duplicate receipts do not inflate position size.
    """

    order_key = _entry_receipt_order_key(order_no)
    requested_by_order = _entry_receipt_int_map(
        target_stock, _ENTRY_RECEIPT_REQUESTED_BY_ORDER_KEY
    )
    filled_by_order = _entry_receipt_int_map(
        target_stock, _ENTRY_RECEIPT_FILLED_BY_ORDER_KEY
    )

    pending_order = None
    for order in target_stock.get("pending_entry_orders") or []:
        if str(order.get("ord_no", "") or "").strip() == str(order_no or "").strip():
            pending_order = order
            break

    requested_qty = int(requested_by_order.get(order_key, 0) or 0)
    if pending_order is not None:
        requested_qty = max(requested_qty, int(pending_order.get("qty", 0) or 0))
    if requested_qty <= 0:
        requested_qty = int(
            target_stock.get(
                "entry_requested_qty", target_stock.get("requested_buy_qty", 0)
            )
            or 0
        )

    already_filled = int(filled_by_order.get(order_key, 0) or 0)
    if pending_order is not None:
        already_filled = max(
            already_filled, int(pending_order.get("filled_qty", 0) or 0)
        )

    if requested_qty > 0:
        requested_by_order[order_key] = requested_qty
        remaining_qty = max(0, requested_qty - already_filled)
        if remaining_qty <= 0:
            log_info(
                f"[ENTRY_FILL_IGNORED] {target_stock.get('name')}({code}) "
                f"ord_no={order_no or '-'} raw_fill_qty={exec_qty} "
                f"already_filled={already_filled}/{requested_qty} reason=duplicate_or_cumulative_receipt"
            )
            if pending_order is not None:
                pending_order["filled_qty"] = already_filled
                pending_order["status"] = "FILLED"
            return 0, requested_qty, already_filled

        effective_qty = min(int(exec_qty or 0), remaining_qty)
        if effective_qty < int(exec_qty or 0):
            log_info(
                f"[ENTRY_FILL_CAPPED] {target_stock.get('name')}({code}) "
                f"ord_no={order_no or '-'} raw_fill_qty={exec_qty} "
                f"effective_fill_qty={effective_qty} already_filled={already_filled}/{requested_qty} "
                "reason=cumulative_or_over_requested_receipt"
            )
    else:
        effective_qty = int(exec_qty or 0)

    new_filled = already_filled + effective_qty
    filled_by_order[order_key] = new_filled
    if pending_order is not None:
        pending_order["filled_qty"] = new_filled
        pending_order["status"] = (
            "FILLED" if requested_qty > 0 and new_filled >= requested_qty else "PARTIAL"
        )
        pending_order["last_effective_fill_qty"] = effective_qty
    return effective_qty, requested_qty, new_filled


def _resolve_add_effective_fill(
    *,
    target_stock: dict[str, Any],
    code: str,
    order_no: str,
    exec_price: int,
    exec_qty: int,
) -> tuple[int, int, int, int, int, int, bool]:
    """Return the add-buy fill delta and effective incremental price.

    Kiwoom add-buy execution notices can arrive as cumulative order fill
    quantity/average price. Keep a per-pending-add ledger so a partial notice
    such as 37 shares followed by cumulative 59 shares mutates runtime truth by
    only the remaining 22 shares, with the incremental price reconstructed from
    cumulative notional.
    """

    raw_qty = int(exec_qty or 0)
    raw_price = int(exec_price or 0)
    bundle_requested_qty = int(target_stock.get("pending_add_qty", 0) or 0)
    bundle_already_filled = int(target_stock.get("pending_add_filled_qty", 0) or 0)
    bundle_already_amount = int(target_stock.get("pending_add_filled_amount", 0) or 0)
    if raw_qty <= 0:
        return 0, raw_price, bundle_requested_qty, bundle_already_filled, 0, 0, False

    order_key = _add_receipt_order_key(order_no)
    requested_by_order = _entry_receipt_int_map(
        target_stock, _ADD_RECEIPT_REQUESTED_BY_ORDER_KEY
    )
    filled_by_order = _entry_receipt_int_map(
        target_stock, _ADD_RECEIPT_FILLED_BY_ORDER_KEY
    )
    amount_by_order = _entry_receipt_int_map(
        target_stock, _ADD_RECEIPT_AMOUNT_BY_ORDER_KEY
    )
    pending_ord_nos = set(_pending_add_order_numbers(target_stock))
    reconciled_before_ordno_bind = False

    normalized_order_no = str(order_no or "").strip()
    if (
        normalized_order_no
        and normalized_order_no not in pending_ord_nos
        and not pending_ord_nos
    ):
        _append_pending_add_order_no(target_stock, normalized_order_no)
        pending_ord_nos.add(normalized_order_no)
        reconciled_before_ordno_bind = True
        target_stock["scale_in_receipt_reconciled_before_ordno_bind"] = True

    order_requested_qty = int(requested_by_order.get(order_key, 0) or 0)
    if order_requested_qty <= 0:
        if not normalized_order_no:
            order_requested_qty = bundle_requested_qty
        elif bundle_requested_qty > 0 and raw_qty >= bundle_requested_qty:
            order_requested_qty = bundle_requested_qty
        else:
            order_requested_qty = raw_qty
    elif (
        normalized_order_no
        and bundle_requested_qty > order_requested_qty
        and order_requested_qty < raw_qty <= bundle_requested_qty
    ):
        order_requested_qty = raw_qty
    if order_requested_qty > 0:
        requested_by_order[order_key] = max(
            int(requested_by_order.get(order_key, 0) or 0), order_requested_qty
        )

    order_already_filled = int(filled_by_order.get(order_key, 0) or 0)
    order_already_amount = int(amount_by_order.get(order_key, 0) or 0)

    if bundle_requested_qty <= 0:
        effective_qty = raw_qty
        effective_price = raw_price
    else:
        bundle_remaining_qty = max(0, bundle_requested_qty - bundle_already_filled)
        order_remaining_qty = (
            max(0, order_requested_qty - order_already_filled)
            if order_requested_qty > 0
            else bundle_remaining_qty
        )
        remaining_qty = min(bundle_remaining_qty, order_remaining_qty)
        if remaining_qty <= 0:
            log_info(
                f"[ADD_FILL_IGNORED] {target_stock.get('name')}({code}) "
                f"ord_no={order_no or '-'} raw_fill_qty={raw_qty} "
                f"already_filled={bundle_already_filled}/{bundle_requested_qty} "
                f"order_filled={order_already_filled}/{order_requested_qty} "
                "reason=duplicate_or_cumulative_receipt"
            )
            return (
                0,
                raw_price,
                bundle_requested_qty,
                bundle_already_filled,
                order_requested_qty,
                order_already_filled,
                reconciled_before_ordno_bind,
            )

        effective_qty = min(raw_qty, remaining_qty)
        effective_price = raw_price

        if (
            order_already_filled > 0
            and raw_qty > remaining_qty
            and order_requested_qty > 0
            and raw_qty <= order_requested_qty
        ):
            cumulative_amount = raw_price * raw_qty
            delta_amount = cumulative_amount - order_already_amount
            if delta_amount > 0:
                effective_price = max(1, int(round(delta_amount / effective_qty)))
                log_info(
                    f"[ADD_FILL_CUMULATIVE_NORMALIZED] {target_stock.get('name')}({code}) "
                    f"ord_no={order_no or '-'} raw_fill_qty={raw_qty} effective_fill_qty={effective_qty} "
                    f"raw_avg_price={raw_price} effective_price={effective_price} "
                    f"order_filled={order_already_filled}/{order_requested_qty}"
                )
        elif effective_qty < raw_qty:
            log_info(
                f"[ADD_FILL_CAPPED] {target_stock.get('name')}({code}) "
                f"ord_no={order_no or '-'} raw_fill_qty={raw_qty} "
                f"effective_fill_qty={effective_qty} already_filled={bundle_already_filled}/{bundle_requested_qty} "
                f"order_filled={order_already_filled}/{order_requested_qty} "
                "reason=over_requested_receipt"
            )

    new_order_filled = order_already_filled + effective_qty
    new_bundle_filled = bundle_already_filled + effective_qty
    filled_by_order[order_key] = new_order_filled
    amount_by_order[order_key] = order_already_amount + (
        effective_price * effective_qty
    )
    target_stock["pending_add_filled_qty"] = new_bundle_filled
    target_stock["pending_add_filled_amount"] = bundle_already_amount + (
        effective_price * effective_qty
    )
    return (
        effective_qty,
        effective_price,
        bundle_requested_qty,
        new_bundle_filled,
        order_requested_qty,
        new_order_filled,
        reconciled_before_ordno_bind,
    )


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
            if safe_buy_price > 0:
                profit_rate = calculate_net_profit_rate(safe_buy_price, exec_price)
            else:
                profit_rate = 0.0
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
) -> None:
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
    sell_receipt_snapshot = _receipt_snapshot(target_stock, _SELL_RECEIPT_SNAPSHOT_KEYS)
    _clear_runtime_keys(target_stock, _SELL_COMPLETE_RESET_KEYS)
    target_stock.pop("pending_sell_msg", None)
    threading.Thread(
        target=_update_db_for_sell,
        args=(
            target_id,
            exec_price,
            now,
            sell_receipt_snapshot,
            strategy,
            is_scalp_revive,
        ),
        daemon=True,
    ).start()


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
) -> None:
    requested_qty = max(
        0,
        _safe_int(target_stock.get("nxt_rising_missed_tp1_partial_requested_qty"), 0),
    )
    filled_before = max(
        0,
        _safe_int(target_stock.get("nxt_rising_missed_tp1_partial_filled_qty"), 0),
    )
    remaining_to_fill = max(0, requested_qty - filled_before)
    effective_exec_qty = min(max(0, exec_qty), remaining_to_fill)
    if requested_qty <= 0 or effective_exec_qty <= 0:
        log_error(
            f"⚠️ [NXT_TP1_PARTIAL_RECEIPT] {target_stock.get('name')}({code}) "
            f"invalid fill requested={requested_qty} filled={filled_before} exec_qty={exec_qty}"
        )
        return

    filled_qty = filled_before + effective_exec_qty
    fill_amount = max(
        0,
        _safe_int(target_stock.get("nxt_rising_missed_tp1_partial_fill_amount"), 0),
    ) + (exec_price * effective_exec_qty)
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
    partial_completed = filled_qty >= requested_qty
    try:
        with DB.get_session() as session:
            record = (
                session.query(RecommendationHistory).filter_by(id=target_id).first()
            )
            if record:
                record.status = "HOLDING" if partial_completed else "SELL_ORDERED"
                record.buy_qty = runner_qty
    except Exception as exc:
        log_error(f"🚨 [DB 에러] ID {target_id} NXT TP1 체결수량 반영 실패: {exc}")

    if not partial_completed:
        _log_holding_pipeline(
            target_stock.get("name"),
            code,
            target_id,
            "nxt_rising_missed_tp1_partial_fill_progress",
            ord_no=order_no or "-",
            fill_qty=effective_exec_qty,
            filled_qty=filled_qty,
            requested_qty=requested_qty,
            runner_qty=runner_qty,
            fill_price=exec_price,
            runtime_effect=True,
        )
        return

    avg_sell_price = _safe_int(
        target_stock.get("nxt_rising_missed_tp1_partial_avg_sell_price"),
        exec_price,
    )
    realized_profit_pct = (
        calculate_net_profit_rate(safe_buy_price, avg_sell_price)
        if safe_buy_price > 0
        else 0.0
    )
    realized_pnl_krw = round(
        ((avg_sell_price - safe_buy_price) * filled_qty) if safe_buy_price > 0 else 0.0
    )
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
        ord_no=order_no or "-",
        sell_price=avg_sell_price,
        sold_qty=filled_qty,
        runner_qty=runner_qty,
        realized_profit_pct=f"{realized_profit_pct:+.2f}",
        realized_pnl_krw=realized_pnl_krw,
        exit_rule="nxt_rising_missed_tp1_partial_runner",
        actual_order_submitted=True,
        runtime_effect=True,
        decision_authority="nxt_rising_missed_tp1_partial_runner_canary",
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


def _handle_early_volatility_tp_sell_execution(
    *,
    target_id: int,
    target_stock: dict[str, Any],
    code: str,
    order_no: str,
    exec_price: int,
    exec_qty: int,
    now: datetime,
    safe_buy_price: float,
) -> None:
    requested_qty = max(
        0, _safe_int(target_stock.get("early_volatility_tp_requested_qty"), 0)
    )
    filled_before = max(
        0, _safe_int(target_stock.get("early_volatility_tp_filled_qty"), 0)
    )
    effective_qty = min(max(0, exec_qty), max(0, requested_qty - filled_before))
    if requested_qty <= 0 or effective_qty <= 0:
        log_error(
            f"[EARLY_TP_RECEIPT_INVALID] {target_stock.get('name')}({code}) "
            f"requested={requested_qty} filled={filled_before} exec={exec_qty}"
        )
        return

    filled_qty = filled_before + effective_qty
    fill_amount = max(
        0, _safe_int(target_stock.get("early_volatility_tp_fill_amount"), 0)
    ) + (exec_price * effective_qty)
    current_qty = max(0, _safe_int(target_stock.get("buy_qty"), 0))
    remaining_qty = max(0, current_qty - effective_qty)
    completed = filled_qty >= requested_qty
    target_stock.update(
        {
            "status": "HOLDING",
            "buy_qty": remaining_qty,
            "early_volatility_tp_state": ("FILLED_RUNNER" if completed else "PARTIAL"),
            "early_volatility_tp_filled_qty": filled_qty,
            "early_volatility_tp_fill_amount": fill_amount,
            "early_volatility_tp_avg_sell_price": _avg_from_totals(
                fill_amount, filled_qty
            ),
            "early_volatility_tp_last_fill_at": now.timestamp(),
            "early_volatility_tp_applied": True,
            "early_volatility_tp_runner_peak_reset_pending": filled_before == 0,
            "early_volatility_tp_runner_peak_price": max(
                exec_price,
                _safe_int(
                    target_stock.get("early_volatility_tp_avg_sell_price"),
                    exec_price,
                ),
            ),
        }
    )
    runner_peak_price = _safe_int(
        target_stock.get("early_volatility_tp_runner_peak_price"), exec_price
    )
    if filled_before == 0 and runner_peak_price > 0:
        with _active_state_lock():
            if isinstance(highest_prices, dict):
                highest_prices[code] = runner_peak_price
        try:
            peak_row = POSITION_PEAK_LEDGER.record(
                target_stock,
                peak_price=runner_peak_price,
                observed_at=now.timestamp(),
                reason="early_partial_runner_rebaseline",
                allow_decrease=True,
            )
            if peak_row:
                target_stock["position_peak_cycle_id"] = peak_row["position_cycle_id"]
                target_stock["position_peak_persisted_price"] = peak_row["peak_price"]
                target_stock["position_peak_persisted_at"] = peak_row[
                    "updated_at_epoch"
                ]
                target_stock["early_volatility_tp_runner_peak_reset_pending"] = False
        except Exception as exc:
            log_error(
                f"[SCALP_PEAK_LEDGER] {target_stock.get('name', code)}({code}) "
                f"early partial rebaseline persist failed: {exc}"
            )
    if completed:
        avg_sell_price = _safe_int(
            target_stock.get("early_volatility_tp_avg_sell_price"), exec_price
        )
        target_stock.update(
            {
                "early_volatility_tp_completed_at": now.timestamp(),
                "early_volatility_tp_realized_profit_pct": calculate_net_profit_rate(
                    safe_buy_price, avg_sell_price
                ),
                "early_volatility_tp_realized_pnl_krw": calculate_net_realized_pnl(
                    safe_buy_price, avg_sell_price, filled_qty
                ),
            }
        )
    try:
        with DB.get_session() as session:
            record = (
                session.query(RecommendationHistory).filter_by(id=target_id).first()
            )
            if record:
                record.status = "HOLDING"
                record.buy_qty = remaining_qty
    except Exception as exc:
        log_error(f"[EARLY_TP_DB] ID {target_id} partial receipt update failed: {exc}")

    cycle_id = str(
        target_stock.get("early_volatility_tp_position_cycle_id") or ""
    ).strip()
    if cycle_id:
        try:
            _EARLY_VOLATILITY_TP_LEDGER.upsert(
                cycle_id,
                state="FILLED_RUNNER" if completed else "PARTIAL",
                order_no=order_no,
                filled_qty=filled_qty,
                remaining_holding_qty=remaining_qty,
                avg_sell_price=target_stock.get("early_volatility_tp_avg_sell_price"),
                updated_at=now.timestamp(),
            )
        except Exception as exc:
            target_stock["early_volatility_tp_state"] = "FAILED_RECONCILIATION"
            target_stock["early_volatility_tp_last_error"] = (
                f"receipt_ledger_persist_failed:{type(exc).__name__}"
            )
            log_error(f"[EARLY_TP_LEDGER] {code} receipt persist failed: {exc}")

    _log_holding_pipeline(
        target_stock.get("name"),
        code,
        target_id,
        (
            "early_volatility_tp_sell_completed"
            if completed
            else "early_volatility_tp_fill_progress"
        ),
        policy_version=str(
            target_stock.get("early_volatility_tp_policy_version")
            or EARLY_VOLATILITY_TP_POLICY_VERSION
        ),
        effective_venue=target_stock.get("early_volatility_tp_cohort") or "-",
        broker_route=target_stock.get("early_volatility_tp_broker_route") or "-",
        position_cycle_id=cycle_id or "-",
        ord_no=order_no or "-",
        fill_price=exec_price,
        fill_qty=effective_qty,
        filled_qty=filled_qty,
        requested_qty=requested_qty,
        runner_qty=remaining_qty,
        realized_profit_pct=target_stock.get(
            "early_volatility_tp_realized_profit_pct", "-"
        ),
        realized_pnl_krw=target_stock.get("early_volatility_tp_realized_pnl_krw", "-"),
        actual_order_submitted=True,
        broker_order_forbidden=False,
        runtime_effect=True,
        decision_authority="scalp_early_volatility_partial_tp",
    )


def _handle_scalp_revive_sell_execution(
    *,
    target_id: int,
    target_stock: dict[str, Any],
    code: str,
    exec_price: int,
    now: datetime,
    profit_rate: float,
    safe_buy_price: float,
    strategy: str,
) -> bool:
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
            record.status = "COMPLETED"
            record.sell_price = exec_price
            record.sell_time = now
            record.profit_rate = profit_rate
            log_info(
                f"🎉 [매매 완료: ID {target_id}] {code} 실매도가: {exec_price:,}원 / 수익률: {profit_rate}%"
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

            _publish_sell_execution_message(
                name=target_stock.get("name") or "-",
                pending_msg=target_stock.get("pending_sell_msg") or "",
                audience=_receipt_audience(target_stock),
                exec_price=exec_price,
                profit_rate=profit_rate,
            )
            _log_holding_pipeline(
                target_stock.get("name"),
                code,
                target_id,
                "sell_completed",
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
                sell_price=int(exec_price or 0),
                sell_qty=int(getattr(record, "buy_qty", 0) or 0),
                profit_rate=f"{profit_rate:+.2f}",
                exit_rule=target_stock.get("last_exit_rule") or "-",
                exit_decision_source=target_stock.get("last_exit_decision_source")
                or "MANUAL",
                revive=True,
                new_watch_id=int(new_watch_id or 0),
            )
            try:
                record_post_sell_candidate(
                    recommendation_id=target_id,
                    stock=target_stock,
                    code=code,
                    sell_time=now,
                    buy_price=safe_buy_price,
                    sell_price=exec_price,
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


def _emit_split_entry_followup_shadows(
    *,
    target_stock: dict[str, Any],
    code: str,
    target_id: int,
    now: datetime,
    entry_mode: str,
    fill_quality: str,
    requested_entry_qty: int,
    cum_filled_qty: int,
    remaining_qty: int,
    new_qty: int,
) -> None:
    if not bool(
        getattr(TRADING_RULES, "SPLIT_ENTRY_REBASE_INTEGRITY_SHADOW_ENABLED", False)
    ):
        return

    rebase_count = int(target_stock.get("_split_entry_rebase_shadow_count", 0) or 0) + 1
    target_stock["_split_entry_rebase_shadow_count"] = rebase_count

    emitted_second = now.strftime("%Y-%m-%dT%H:%M:%S")
    last_second = str(target_stock.get("_split_entry_rebase_shadow_last_second") or "")
    if emitted_second == last_second:
        same_second_count = (
            int(
                target_stock.get("_split_entry_rebase_shadow_same_second_count", 0) or 0
            )
            + 1
        )
    else:
        same_second_count = 1
    target_stock["_split_entry_rebase_shadow_last_second"] = emitted_second
    target_stock["_split_entry_rebase_shadow_same_second_count"] = same_second_count

    fill_quality_upper = str(fill_quality or "").upper()
    first_partial_qty = int(target_stock.get("_split_entry_first_partial_qty", 0) or 0)
    if fill_quality_upper == "PARTIAL_FILL" and first_partial_qty <= 0:
        first_partial_qty = max(0, int(cum_filled_qty or 0))
        target_stock["_split_entry_first_partial_qty"] = first_partial_qty

    split_entry_candidate = (
        rebase_count >= 2
        or fill_quality_upper == "PARTIAL_FILL"
        or first_partial_qty > 0
    )
    if not split_entry_candidate:
        return

    integrity_flags: list[str] = []
    if requested_entry_qty > 0 and cum_filled_qty > requested_entry_qty:
        integrity_flags.append("cum_gt_requested")
    if requested_entry_qty == 0 and fill_quality_upper == "UNKNOWN":
        integrity_flags.append("requested0_unknown")
    if same_second_count >= 2:
        integrity_flags.append("same_ts_multi_rebase")

    integrity_flag_text = ",".join(integrity_flags) if integrity_flags else "-"
    _log_holding_pipeline(
        target_stock.get("name"),
        code,
        target_id,
        "split_entry_rebase_integrity_shadow",
        requested_qty=int(requested_entry_qty or 0),
        cum_filled_qty=int(cum_filled_qty or 0),
        remaining_qty=int(remaining_qty or 0),
        fill_quality=fill_quality_upper or "-",
        entry_mode=entry_mode or "-",
        buy_qty_after_rebase=int(new_qty or 0),
        rebase_count=int(rebase_count),
        same_ts_multi_rebase_count=int(same_second_count),
        integrity_flags=integrity_flag_text,
    )

    if not bool(
        getattr(TRADING_RULES, "SPLIT_ENTRY_IMMEDIATE_RECHECK_SHADOW_ENABLED", False)
    ):
        return

    expanded_after_partial = (
        first_partial_qty > 0 and int(new_qty or 0) > first_partial_qty
    )
    if not (expanded_after_partial or rebase_count >= 2):
        return

    last_logged_count = int(
        target_stock.get("_split_entry_last_immediate_recheck_rebase_count", 0) or 0
    )
    if rebase_count <= last_logged_count:
        return
    target_stock["_split_entry_last_immediate_recheck_rebase_count"] = rebase_count

    trigger_reason = "partial_then_expand" if expanded_after_partial else "multi_rebase"
    shadow_window_sec = int(
        getattr(TRADING_RULES, "SPLIT_ENTRY_IMMEDIATE_RECHECK_SHADOW_WINDOW_SEC", 90)
        or 90
    )
    _log_holding_pipeline(
        target_stock.get("name"),
        code,
        target_id,
        "split_entry_immediate_recheck_shadow",
        trigger_reason=trigger_reason,
        shadow_window_sec=int(shadow_window_sec),
        requested_qty=int(requested_entry_qty or 0),
        cum_filled_qty=int(cum_filled_qty or 0),
        remaining_qty=int(remaining_qty or 0),
        buy_qty_after_rebase=int(new_qty or 0),
        first_partial_qty=int(first_partial_qty or 0),
        rebase_count=int(rebase_count),
        fill_quality=fill_quality_upper or "-",
        entry_mode=entry_mode or "-",
        integrity_flags=integrity_flag_text,
    )


def _find_buy_bundle_match(code: str, normalized_order_no: str):
    return next(
        (
            stock
            for stock in ACTIVE_TARGETS
            if str(stock.get("code", "")).strip()[:6] == code
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
    return next(
        (
            stock
            for stock in ACTIVE_TARGETS
            if str(stock.get("code", "")).strip()[:6] == stock_code
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


def _find_execution_target(code, exec_type, order_no):
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
            early_tp_match = next(
                (
                    stock
                    for stock in ACTIVE_TARGETS
                    if str(stock.get("code", "")).strip()[:6] == code
                    and str(stock.get("early_volatility_tp_ord_no") or "").strip()
                    == normalized_order_no
                ),
                None,
            )
            if early_tp_match:
                return early_tp_match
            early_submitting = [
                stock
                for stock in ACTIVE_TARGETS
                if str(stock.get("code", "")).strip()[:6] == code
                and str(stock.get("status") or "") == "HOLDING"
                and str(stock.get("early_volatility_tp_state") or "").strip().upper()
                == "SUBMITTING"
                and not str(stock.get("early_volatility_tp_ord_no") or "").strip()
            ]
            if len(early_submitting) == 1:
                return early_submitting[0]
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
    target = _find_execution_target(code, exec_type, order_no)
    if target:
        return target

    status_key = "BUY_ORDERED" if exec_type == "BUY" else "SELL_ORDERED"
    status_candidates = [
        stock
        for stock in ACTIVE_TARGETS
        if str(stock.get("code", "")).strip()[:6] == code
        and stock.get("status") == status_key
    ]
    if len(status_candidates) == 1:
        return status_candidates[0]
    return None


def _apply_order_notice_to_target(target_stock, *, code, exec_type, order_no, status):
    changed = False

    if exec_type == "BUY":
        if (
            bool(target_stock.get("pending_add_order"))
            and str(target_stock.get("status") or "") == "HOLDING"
        ):
            if order_no:
                _append_pending_add_order_no(target_stock, order_no)
                notices = target_stock.get("pending_add_notice_by_order_no")
                if not isinstance(notices, dict):
                    notices = {}
                    target_stock["pending_add_notice_by_order_no"] = notices
                notices[str(order_no)] = {"status": status, "notice_at": time.time()}
                changed = True
            if changed:
                log_info(
                    f"[ORDER_NOTICE_BOUND] {target_stock.get('name')}({code}) "
                    f"type={exec_type} status={status} order_no={order_no}"
                )
            return

        pending_orders = target_stock.get("pending_entry_orders") or []
        exact_match = None
        blank_match = None

        for order in pending_orders:
            existing_ord_no = str(order.get("ord_no", "") or "").strip()
            if existing_ord_no == order_no:
                exact_match = order
                break
            if not existing_ord_no and blank_match is None:
                blank_match = order

        target_order = exact_match or blank_match
        if target_order:
            if not str(target_order.get("ord_no", "") or "").strip():
                target_order["ord_no"] = order_no
                changed = True
            target_order["notice_status"] = status
            target_order["notice_at"] = time.time()
            changed = True

        if order_no and not str(target_stock.get("odno", "") or "").strip():
            target_stock["odno"] = order_no
            changed = True

    elif exec_type == "SELL":
        early_state = (
            str(target_stock.get("early_volatility_tp_state") or "").strip().upper()
        )
        early_ord_no = str(target_stock.get("early_volatility_tp_ord_no") or "").strip()
        if order_no and (
            early_ord_no == order_no
            or (early_state == "SUBMITTING" and not early_ord_no)
        ):
            target_stock["early_volatility_tp_ord_no"] = order_no
            target_stock["early_volatility_tp_notice_status"] = status
            target_stock["early_volatility_tp_notice_at"] = time.time()
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
        cancel_res = kiwoom_orders.send_cancel_order(
            code=code, orig_ord_no=preset_ord_no, token=KIWOOM_TOKEN, qty=0
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
            session.query(RecommendationHistory).filter_by(id=target_id).update(
                update_fields
            )

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
        with DB.get_session() as session:
            record = (
                session.query(RecommendationHistory).filter_by(id=target_id).first()
            )
            if not record:
                return

            old_price = float(record.buy_price) if record.buy_price is not None else 0.0
            old_qty = int(record.buy_qty or 0)
            new_avg = float(receipt_snapshot.get("buy_price") or exec_price or 0)
            new_qty = int(receipt_snapshot.get("buy_qty") or 0)

            record.buy_price = new_avg
            record.buy_qty = new_qty
            record.add_count = int(
                receipt_snapshot.get("add_count", record.add_count or 0) or 0
            )
            record.avg_down_count = int(
                receipt_snapshot.get("avg_down_count", record.avg_down_count or 0) or 0
            )
            record.pyramid_count = int(
                receipt_snapshot.get("pyramid_count", record.pyramid_count or 0) or 0
            )
            initial_buy_qty = _safe_int(
                receipt_snapshot.get("initial_buy_qty"),
                _safe_int(getattr(record, "initial_buy_qty", 0), 0),
            )
            if initial_buy_qty > 0:
                record.initial_buy_qty = initial_buy_qty
            record.scale_in_filled_qty = _safe_int(
                receipt_snapshot.get("scale_in_filled_qty"),
                _safe_int(getattr(record, "scale_in_filled_qty", 0), 0)
                + int(exec_qty or 0),
            )
            record.last_add_type = add_type
            record.last_add_reason = str(
                receipt_snapshot.get("last_add_reason") or ""
            ).strip()
            record.last_add_at = now
            record.shallow_volatility_avg_down_count = int(
                receipt_snapshot.get(
                    "shallow_volatility_avg_down_count",
                    getattr(record, "shallow_volatility_avg_down_count", 0) or 0,
                )
                or 0
            )
            shallow_last_at = float(
                receipt_snapshot.get("shallow_volatility_avg_down_last_at") or 0.0
            )
            if shallow_last_at > 0:
                record.shallow_volatility_avg_down_last_at = datetime.fromtimestamp(
                    shallow_last_at
                )
            record.scale_in_locked = bool(
                receipt_snapshot.get("scale_in_locked", False)
            )
            add_count_after = int(record.add_count or 0)

            # 보호선 보정값을 DB에도 반영 (있을 때만)
            if receipt_snapshot.get("trailing_stop_price") is not None:
                record.trailing_stop_price = float(
                    receipt_snapshot.get("trailing_stop_price") or 0
                )
            if receipt_snapshot.get("hard_stop_price") is not None:
                record.hard_stop_price = float(
                    receipt_snapshot.get("hard_stop_price") or 0
                )

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
):
    """비동기로 실행되는 SELL 체결 DB 업데이트 및 알림 (스캘핑 부활 제외)"""
    try:
        with DB.get_session() as session:
            record = (
                session.query(RecommendationHistory).filter_by(id=target_id).first()
            )
            if not record:
                return

            safe_buy_price = (
                float(record.buy_price) if record.buy_price is not None else 0.0
            )
            early_partial_qty = _safe_int(
                receipt_snapshot.get("early_volatility_tp_filled_qty"), 0
            )
            early_partial_amount = _safe_int(
                receipt_snapshot.get("early_volatility_tp_fill_amount"), 0
            )
            nxt_partial_qty = _safe_int(
                receipt_snapshot.get("nxt_rising_missed_tp1_partial_filled_qty"), 0
            )
            nxt_partial_amount = _safe_int(
                receipt_snapshot.get("nxt_rising_missed_tp1_partial_fill_amount"), 0
            )
            partial_qty = early_partial_qty or nxt_partial_qty
            partial_amount = early_partial_amount or nxt_partial_amount
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
            if pre_add_avg_price > 0 and pre_add_qty > 0:
                no_scale_in_counterfactual_profit_pct = calculate_net_profit_rate(
                    pre_add_avg_price, exec_price
                )
                receipt_snapshot["no_scale_in_counterfactual_profit_pct"] = round(
                    float(no_scale_in_counterfactual_profit_pct),
                    4,
                )
                receipt_snapshot["scale_in_incremental_realized_delta_pct"] = round(
                    float(profit_rate) - float(no_scale_in_counterfactual_profit_pct),
                    4,
                )

            record.status = "COMPLETED"
            record.sell_time = now
            completed_runner_qty = _safe_int(getattr(record, "buy_qty", 0), 0)
            if completed_runner_qty <= 0:
                completed_runner_qty = _safe_int(receipt_snapshot.get("buy_qty"), 0)
            completed_buy_qty = completed_runner_qty + partial_qty
            position_weighted_sell_price = int(exec_price or 0)
            runner_realized_pnl_krw = calculate_net_realized_pnl(
                safe_buy_price,
                exec_price,
                completed_runner_qty,
            )
            partial_realized_pnl_krw = 0
            if partial_qty > 0 and partial_amount > 0 and safe_buy_price > 0:
                partial_avg_sell_price = partial_amount / partial_qty
                partial_realized_pnl_krw = calculate_net_realized_pnl(
                    safe_buy_price,
                    partial_avg_sell_price,
                    partial_qty,
                )
                total_sell_amount = partial_amount + (
                    int(exec_price or 0) * completed_runner_qty
                )
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

            log_info(
                f"🎉 [매매 완료: ID {target_id}] {receipt_snapshot.get('code')} "
                f"실매도가: {exec_price:,}원 / 수익률: {profit_rate}%"
            )

            _publish_sell_execution_message(
                name=receipt_snapshot.get("name") or "-",
                pending_msg=receipt_snapshot.get("pending_sell_msg") or "",
                audience=_receipt_audience(receipt_snapshot),
                exec_price=exec_price,
                profit_rate=profit_rate,
            )
            _log_holding_pipeline(
                receipt_snapshot.get("name"),
                str(receipt_snapshot.get("code", "")).strip()[:6],
                target_id,
                "sell_completed",
                sell_price=int(exec_price or 0),
                position_weighted_sell_price=position_weighted_sell_price,
                profit_rate=f"{profit_rate:+.2f}",
                exit_rule=receipt_snapshot.get("last_exit_rule") or "-",
                exit_decision_source=receipt_snapshot.get("last_exit_decision_source")
                or "MANUAL",
                revive=bool(is_scalp_revive),
                strategy=strategy,
                position_tag=completed_position_tag,
                buy_price=f"{safe_buy_price:.2f}",
                buy_qty=completed_buy_qty,
                realized_pnl_krw=realized_pnl_krw,
                partial_realized_pnl_krw=partial_realized_pnl_krw,
                runner_realized_pnl_krw=runner_realized_pnl_krw,
                partial_realized_qty=partial_qty,
                runner_realized_qty=completed_runner_qty,
                actual_order_submitted=True,
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
                **_sell_completion_contract_fields(completed_position_tag),
            )
            try:
                record_post_sell_candidate(
                    recommendation_id=target_id,
                    stock=receipt_snapshot,
                    code=str(receipt_snapshot.get("code", "")).strip()[:6],
                    sell_time=now,
                    buy_price=safe_buy_price,
                    sell_price=exec_price,
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
    except Exception as e:
        log_error(f"🚨 [DB 에러] ID {target_id} SELL 처리 중 에러: {e}")


def _handle_add_buy_execution(
    *,
    target_id: int,
    target_stock: dict[str, Any],
    code: str,
    order_no: str,
    exec_price: int,
    exec_qty: int,
    now: datetime,
) -> None:
    (
        effective_qty,
        effective_price,
        requested_qty,
        filled_qty,
        order_requested_qty,
        order_filled_qty,
        reconciled_before_ordno_bind,
    ) = _resolve_add_effective_fill(
        target_stock=target_stock,
        code=code,
        order_no=order_no,
        exec_price=exec_price,
        exec_qty=exec_qty,
    )
    if effective_qty <= 0:
        return
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
            (old_price * old_qty) + (exec_price * exec_qty), total_qty
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
    target_stock["pre_add_avg_price"] = round(float(old_price or 0.0), 4)
    target_stock["post_add_avg_price"] = round(float(new_avg or 0.0), 4)
    target_stock["pre_add_qty"] = int(old_qty or 0)
    target_stock["post_add_qty"] = int(new_qty or 0)
    target_stock["last_add_type"] = add_type
    pending_add_reason = str(target_stock.get("pending_add_reason") or "").strip()
    target_stock["last_add_reason"] = pending_add_reason
    target_stock["last_add_economic_direction"] = add_economic_direction
    target_stock["last_add_avg_price_improved"] = avg_price_improved
    target_stock["last_add_at"] = now
    target_stock["last_add_fill_price"] = int(exec_price or 0)
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
        metric_role="execution_quality_real_only",
        decision_authority="broker_receipt_observation_only",
        runtime_effect=False,
        forbidden_uses="runtime_threshold_apply/provider_route_change/bot_restart/sim_execution_quality_claim",
        actual_order_submitted=True,
        broker_order_forbidden=False,
        add_type=add_type,
        order_no=order_no or "-",
        fill_price=int(exec_price or 0),
        fill_qty=int(exec_qty or 0),
        bundle_requested_qty=int(requested_qty or 0),
        bundle_filled_qty=int(filled_qty or 0),
        order_requested_qty=int(order_requested_qty or 0),
        order_filled_qty=int(order_filled_qty or 0),
        **split_leg_fields,
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
        pre_add_avg_price=f"{float(old_price or 0):.2f}",
        post_add_avg_price=f"{float(new_avg or 0):.2f}",
        shallow_volatility_avg_down_count=int(
            target_stock.get("shallow_volatility_avg_down_count", 0) or 0
        ),
        shallow_volatility_avg_down_last_at=target_stock.get(
            "shallow_volatility_avg_down_last_at", "-"
        ),
        reversal_add_state=target_stock.get("reversal_add_state", "-"),
        reversal_add_executed_at=target_stock.get("reversal_add_executed_at", "-"),
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
) -> None:
    effective_exec_qty, order_requested_qty, order_filled_qty = (
        _resolve_entry_effective_fill_qty(
            target_stock=target_stock,
            code=code,
            order_no=order_no,
            exec_qty=exec_qty,
        )
    )
    if effective_exec_qty <= 0:
        return

    old_qty = int(target_stock.get("buy_qty") or 0)
    old_price = float(target_stock.get("buy_price") or 0)
    if old_qty <= 0:
        _clear_split_entry_shadow_state(target_stock)
    new_qty = old_qty + effective_exec_qty
    if old_qty > 0:
        new_avg = _avg_from_totals(
            (old_price * old_qty) + (exec_price * effective_exec_qty),
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
    target_stock["entry_fill_amount"] = int(
        target_stock.get("entry_fill_amount", 0) or 0
    ) + (exec_price * effective_exec_qty)
    target_stock["buy_time"] = now
    if not target_stock.get("holding_started_at"):
        target_stock["holding_started_at"] = now
    highest_prices[code] = max(highest_prices.get(code, 0), exec_price)

    probe_phase = str(target_stock.get("entry_split_probe_phase") or "").strip()
    if probe_phase in {"probe_submitting", "probe_submitted"}:
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
            if bundle_id:
                update_probe_runtime_bundle(
                    bundle_id,
                    phase="aborted",
                    reason="probe_receipt_order_number_mismatch",
                    target_id=target_id,
                    observed_order_no=order_no,
                    filled_qty=int(new_qty or 0),
                )
        elif effective_exec_qty != 1 or int(new_qty or 0) != 1:
            trip_probe_runtime_circuit("probe_fill_quantity_invariant")
            target_stock["entry_split_probe_phase"] = "aborted"
            target_stock["entry_split_probe_abort_reason"] = (
                "probe_fill_quantity_invariant"
            )
            target_stock["entry_split_probe_scale_in_forbidden"] = True
            if bundle_id:
                update_probe_runtime_bundle(
                    bundle_id,
                    phase="aborted",
                    reason="probe_fill_quantity_invariant",
                    target_id=target_id,
                    filled_qty=int(new_qty or 0),
                )
        else:
            filled_at_ts = time.time()
            target_stock["entry_split_probe_phase"] = "probe_filled"
            target_stock["entry_split_probe_order_no"] = order_no
            target_stock["entry_split_probe_fill_price"] = exec_price
            target_stock["entry_split_probe_filled_at"] = filled_at_ts
            update_probe_runtime_bundle(
                bundle_id,
                phase="probe_filled",
                order_no=order_no,
                fill_price=exec_price,
                filled_at=filled_at_ts,
                fill_qty=effective_exec_qty,
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
            update_probe_runtime_bundle(
                probe_bundle_id,
                phase="complete",
                requested_qty=requested_entry_qty,
                filled_qty=cum_filled_qty,
                avg_buy_price=round(float(new_avg or 0.0), 4),
            )
            _log_holding_pipeline(
                target_stock.get("name"),
                code,
                target_id,
                "bundle_completed",
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
        if str(target_stock.get("entry_mode", "")).strip().lower() == "fallback":
            preset_hard_stop_pct = float(
                getattr(
                    TRADING_RULES,
                    "SCALP_PRESET_HARD_STOP_FALLBACK_BASE_PCT",
                    preset_hard_stop_pct,
                )
                or preset_hard_stop_pct
            )
            preset_hard_stop_grace_sec = int(
                getattr(
                    TRADING_RULES,
                    "SCALP_PRESET_HARD_STOP_FALLBACK_BASE_GRACE_SEC",
                    preset_hard_stop_grace_sec,
                )
                or preset_hard_stop_grace_sec
            )
            preset_hard_stop_emergency_pct = float(
                getattr(
                    TRADING_RULES,
                    "SCALP_PRESET_HARD_STOP_FALLBACK_BASE_EMERGENCY_PCT",
                    preset_hard_stop_emergency_pct,
                )
                or preset_hard_stop_emergency_pct
            )
        target_stock["hard_stop_pct"] = preset_hard_stop_pct
        target_stock["hard_stop_grace_sec"] = preset_hard_stop_grace_sec
        target_stock["hard_stop_emergency_pct"] = preset_hard_stop_emergency_pct
        target_stock["protect_profit_pct"] = None
        target_stock["ai_review_done"] = False
        target_stock["ai_review_score"] = None
        target_stock["ai_review_action"] = None
        target_stock["last_ai_reviewed_at"] = None
        target_stock["exit_requested"] = False
        target_stock["exit_order_type"] = None
        target_stock["exit_order_time"] = None

        sell_qty = int(target_stock.get("buy_qty") or exec_qty or 0)
        refreshed = _refresh_scalp_preset_exit_order(target_stock, code, sell_qty)
        preset_tp_ord_no_after = str(
            target_stock.get("preset_tp_ord_no", "") or ""
        ).strip()
        preset_tp_qty = int(target_stock.get("preset_tp_qty", 0) or 0)
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
        fill_qty=int(effective_exec_qty or 0),
        raw_fill_qty=int(exec_qty or 0),
        order_requested_qty=int(order_requested_qty or 0),
        order_filled_qty=int(order_filled_qty or 0),
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
    )
    _emit_split_entry_followup_shadows(
        target_stock=target_stock,
        code=code,
        target_id=target_id,
        now=now,
        entry_mode=entry_mode,
        fill_quality=fill_quality,
        requested_entry_qty=int(requested_entry_qty or 0),
        cum_filled_qty=int(cum_filled_qty or 0),
        remaining_qty=int(remaining_qty or 0),
        new_qty=int(new_qty or 0),
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
        metric_role="execution_quality_real_only",
        decision_authority="broker_receipt_observation_only",
        runtime_effect=False,
        forbidden_uses="runtime_threshold_apply/provider_route_change/bot_restart/sim_execution_quality_claim",
        actual_order_submitted=True,
        broker_order_forbidden=False,
        strategy=target_stock.get("strategy"),
        position_tag=target_stock.get("position_tag"),
        opening_rotation_entry_time_bucket=target_stock.get(
            "opening_rotation_entry_time_bucket", "-"
        ),
        opening_rotation_window_version=target_stock.get(
            "opening_rotation_window_version", "-"
        ),
        buy_price=f"{float(new_avg or 0):.2f}",
        buy_qty=int(new_qty or 0),
        fill_price=int(exec_price or 0),
        fill_qty=int(effective_exec_qty or 0),
        raw_fill_qty=int(exec_qty or 0),
        order_requested_qty=int(order_requested_qty or 0),
        order_filled_qty=int(order_filled_qty or 0),
        entry_mode=entry_mode,
        entry_submit_ai_score=(
            f"{float(submit_ai_score):.1f}" if submit_ai_score is not None else "-"
        ),
        holding_ai_score_seeded_from_entry=holding_ai_seeded,
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

    try:
        exec_price = int(float(exec_data.get("price", 0) or 0))
    except Exception:
        exec_price = 0

    try:
        exec_qty = int(float(exec_data.get("qty", 0) or 0))
    except Exception:
        exec_qty = 0

    if not code or exec_price <= 0:
        return

    state = _get_fast_state(code)
    if state and exec_qty > 0:
        with state["lock"]:
            matched = False

            if exec_type == "BUY":
                if order_no and order_no == str(state.get("buy_ord_no", "")):
                    state["cum_buy_qty"] += exec_qty
                    state["cum_buy_amount"] += exec_price * exec_qty
                    state["avg_buy_price"] = _avg_from_totals(
                        state["cum_buy_amount"], state["cum_buy_qty"]
                    )
                    state["updated_at"] = _now_ts()
                    matched = True

            elif exec_type == "SELL":
                valid_sell_ord_nos = {
                    str(state.get("sell_ord_no", "") or ""),
                    str(state.get("pending_cancel_ord_no", "") or ""),
                }
                if order_no and order_no in valid_sell_ord_nos:
                    state["cum_sell_qty"] += exec_qty
                    state["cum_sell_amount"] += exec_price * exec_qty
                    state["avg_sell_price"] = _avg_from_totals(
                        state["cum_sell_amount"], state["cum_sell_qty"]
                    )
                    state["updated_at"] = _now_ts()
                    matched = True

        if matched:
            return

    now = datetime.now()
    now_t = now.time()

    with _active_state_lock():
        target_stock = _find_execution_target(code, exec_type, order_no)
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
                )
            elif pending_add and str(target_stock.get("status") or "") == "HOLDING":
                log_info(
                    f"[ADD_FILL_IGNORED] {target_stock.get('name')}({code}) "
                    f"ord_no={order_no or '-'} pending_add_ord_no={pending_ord_no or '-'} "
                    "reason=order_not_in_pending_add_bundle"
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
                )

        elif exec_type == "SELL":
            sell_context = _resolve_sell_execution_context(
                target_id, target_stock, exec_price, now_t
            )
            if not sell_context:
                return
            _, safe_buy_price, profit_rate, strategy, is_scalp_revive = sell_context

            early_state = (
                str(target_stock.get("early_volatility_tp_state") or "").strip().upper()
            )
            early_ord_no = str(
                target_stock.get("early_volatility_tp_ord_no") or ""
            ).strip()
            if order_no and (
                order_no == early_ord_no
                or (early_state == "SUBMITTING" and not early_ord_no)
            ):
                target_stock["early_volatility_tp_ord_no"] = order_no
                _handle_early_volatility_tp_sell_execution(
                    target_id=target_id,
                    target_stock=target_stock,
                    code=code,
                    order_no=order_no,
                    exec_price=exec_price,
                    exec_qty=exec_qty,
                    now=now,
                    safe_buy_price=safe_buy_price,
                )
                return

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
                )
                return

            if is_scalp_revive:
                if not _handle_scalp_revive_sell_execution(
                    target_id=target_id,
                    target_stock=target_stock,
                    code=code,
                    exec_price=exec_price,
                    now=now,
                    profit_rate=profit_rate,
                    safe_buy_price=safe_buy_price,
                    strategy=strategy,
                ):
                    return
            else:
                _finalize_standard_sell_execution(
                    target_id=target_id,
                    exec_price=exec_price,
                    now=now,
                    target_stock=target_stock,
                    strategy=strategy,
                    is_scalp_revive=is_scalp_revive,
                    code=code,
                )

    # 메모리 업데이트는 각 조건문 내에서 이미 수행됨
