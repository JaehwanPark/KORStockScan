"""Entry split order plan report and bounded runtime allocator."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import tempfile
import threading
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Any

from src.engine.automation.source_quality_clean_baseline import (
    clean_baseline_policy,
    is_date_allowed,
)
from src.trading.order.split_execution_math import (
    pct_price_offset as _pct_price_offset,
    split_qty as _split_qty,
    tick_size as _tick_size,
)
from src.trading.order.tick_utils import clamp_price_to_tick, get_tick_size
from src.utils.constants import DATA_DIR, PROJECT_ROOT
from src.utils.jsonl_io import existing_or_gzip_path, iter_jsonl, open_text_auto

SCHEMA_VERSION = "entry_split_order_plan_v1"
POLICY_SCHEMA_VERSION = "entry_split_order_policy_v1"
CUMULATIVE_STATE_SCHEMA_VERSION = "entry_split_cumulative_state_v2"
GENERATION_BINDING_SCHEMA_VERSION = "entry_split_report_policy_generation_v1"
GENERATION_BINDING_REQUIRED_FROM_DATE = date(2026, 9, 4)
ATOMIC_EXECUTION_SIZING_REQUIRED_FROM_DATE = date(2026, 9, 15)
ATOMIC_PRICE_PLAN_REQUIRED_FROM_DATE = date(2026, 9, 16)
ATOMIC_EXECUTION_SIZING_SCHEMA = "entry_execution_sizing_plan_v1"
ATOMIC_EXECUTION_SIZING_BASELINE_POLICY = "execution_sizing_baseline_v1"
ATOMIC_PRICE_PLAN_SCHEMA = "entry_price_plan_v1"
QUANTITY_LEG_FOUR_ARM_SCHEMA = "entry_quantity_leg_four_arm_evaluation_v1"
QUANTITY_LEG_SELECTION_CONTRACT = "quantity_leg_chronological_paired_v2"
QUANTITY_LEG_FOUR_ARM_IDS = (
    "incumbent_qty_x_incumbent_leg",
    "candidate_qty_x_incumbent_leg",
    "incumbent_qty_x_candidate_leg",
    "candidate_qty_x_candidate_leg",
)
QUANTITY_LEG_FOUR_ARM_MIN_COMPLETE_ATTEMPTS = 30
QUANTITY_LEG_FOUR_ARM_MIN_JOIN_COVERAGE = 0.80
QUANTITY_LEG_FOUR_ARM_SHARED_CONTRACT_FIELDS = (
    "entry_price_receipt_sha256",
    "exit_policy_sha256",
    "cost_contract_sha256",
    "terminal_contract_version",
    "terminal_observed_at",
)
REPORT_TYPE = "entry_split_order_plan"
RUNTIME_FAMILY = "entry_split_order_plan"
REPORT_DIR = DATA_DIR / "report" / REPORT_TYPE
POLICY_DIR = DATA_DIR / "threshold_cycle" / "entry_split_order_policy"
SAMPLE_FLOOR_REAL = 20
SAMPLE_FLOOR_SIM = 10
CUMULATIVE_LEARNING_SAMPLE_FLOOR = 1
SPLIT_VARIANT_OUTCOME_FLOOR_REAL = 20
SPLIT_VARIANT_CONTINUATION_FLOOR_REAL = 10
CHILD_SHAPE_SEED_OUTCOME_FLOOR_REAL = 3
CHILD_SHAPE_SEED_MIN_EV_PCT = 0.1
RUNTIME_PROMOTION_MIN_COST_ADJUSTED_EV_PCT = 0.1
CHILD_SHAPE_SEED_MAX_DOWNSIDE_P10_PCT = -2.0
POST_SUBMIT_TICK_BAND_FLOOR_REAL = 20
POST_SUBMIT_LOW_WINDOW_MINUTES = 10
POST_SUBMIT_PRICE_TOKENS = (
    '"current_price_observed"',
    '"current_price"',
    '"latest_price"',
    '"holding_ws_recovered_curr"',
    '"curr_price"',
    '"mark_price_at_submit"',
    '"submitted_mark_price"',
)
RAW_RECORD_ID_PATTERN = re.compile(
    r'"record_id"\s*:\s*(?:"([^"\\]*(?:\\.[^"\\]*)*)"|([^,}\s]+))'
)
POLICY_MODE_REAL_PRIMARY_EV = "real_primary_ev_optimized"
POLICY_MODE_BOUNDED_EQUAL_BASELINE = "bounded_equal_split_baseline"
POLICY_MODE_POST_SUBMIT_TICK_BAND = "post_submit_tick_band_seed"
POLICY_MODE_CHILD_SHAPE_EV_SEED = "child_shape_positive_ev_seed"
RUNTIME_APPLY_COMPATIBILITY_SEMANTICS = (
    "union_of_exploration_seed_allowed_and_ev_validated_runtime_apply_allowed_"
    "with_scoped_bucket_fallback_v2"
)
BASELINE_SPLIT_VARIANT_ID = "equal_50_50_offset_0pct_0_3pct"
PCT_BAND_3LEG_VARIANT_ID = "equal_3leg_offset_0pct_0_3pct_0_8pct"
RUNTIME_FALLBACK_POLICY_MODE = "runtime_default_passive_center_40_60_0_3pct"
RUNTIME_FALLBACK_VARIANT_ID = "runtime_default_passive_center_40_60_offset_0pct_0_3pct"
RUNTIME_FALLBACK_THREE_LEG_POLICY_MODE = (
    "runtime_default_market_first_50_residual_25_25_3leg"
)
RUNTIME_FALLBACK_THREE_LEG_VARIANT_ID = (
    "runtime_default_50_25_25_offset_0pct_0_3pct_0_8pct"
)
PASSIVE_CENTER_MAX_FIRST_WEIGHT = 0.40
PASSIVE_BIAS_WAIT_WARNING_FIRST_WEIGHT = 0.20
ALLOWED_PRICE_CANDIDATES = {
    "resolved_order_price",
    "best_bid",
    "bid-1tick",
    "bid-2tick",
    "reference_target",
    "AI_candidate",
}
PROBE_RUNTIME_STATE_SCHEMA_VERSION = "entry_split_probe_runtime_state_v1"
PROBE_RUNTIME_STATE_PATH = PROJECT_ROOT / "tmp" / "entry_split_probe_runtime_state.json"
PROBE_VARIANT_SUFFIX = "probe1_fill_clamped_bbo"
DAILY_ACTIVE_DATE_TOKEN = "DAILY"
CALIBRATION_EVENT_KEYS = frozenset(
    {
        "stage",
        "event",
        "date",
        "entry_date",
        "signal_date",
        "sell_date",
        "emitted_at",
        "timestamp",
        "created_at",
        "ts",
        "record_id",
        "recommendation_id",
        "stock_code",
        "code",
        "order_id",
        "bundle_id",
        "order_bundle_id",
        "entry_split_order_bundle_id",
        "actual_order_submitted",
        "broker_order_submitted",
        "broker_order_no",
        "ord_no",
        "effective_venue",
        "market_session_bucket",
        "broker_order_forbidden",
        "decision_authority",
        "fill_status",
        "filled_qty",
        "late_fill",
        "late_fill_detected",
        "spread_bps",
        "spread_ratio",
        "buy_pressure_10t",
        "tick_buy_pressure_10t",
        "orderbook_micro_state",
        "micro_state",
        "latency_state",
        "quote_stale",
        "stale_quote_submit_block",
        "current_price_observed",
        "current_price",
        "latest_price",
        "holding_ws_recovered_curr",
        "curr_price",
        "mark_price_at_submit",
        "submitted_mark_price",
        "order_price",
        "submitted_order_price",
        "resolved_order_price",
        "price",
        "submitted_price",
        "entry_split_order_policy_applied",
        "entry_split_order_bucket",
        "entry_split_order_policy_version",
        "entry_split_order_policy_mode",
        "entry_split_order_policy_variant_id",
        "entry_split_order_variant_id",
        "entry_split_order_original_qty",
        "entry_split_order_skip_reason",
        "requested_qty",
        "submitted_qty",
        "entry_split_order_leg_count",
        "entry_split_order_price_offsets_ticks",
        "entry_split_order_qty_weight_min",
        "entry_split_order_qty_weight_max",
        "entry_split_order_runtime_default_policy_applied",
        "entry_split_order_operator_fallback_authorized",
        "entry_execution_sizing_plan_schema",
        "entry_execution_sizing_plan_id",
        "entry_execution_sizing_policy",
        "entry_execution_sizing_action_receipt_id",
        "entry_execution_sizing_quantity_policy_version",
        "entry_execution_sizing_split_policy_version",
        "entry_execution_sizing_total_qty",
        "entry_execution_sizing_immediate_qty",
        "entry_execution_sizing_deferred_qty",
        "entry_execution_sizing_leg_count",
        "entry_execution_sizing_quantity_conservation_holds",
        "entry_execution_sizing_quantity_increase_forbidden",
        "entry_execution_sizing_migration_baseline",
        "entry_execution_sizing_plan_emitted",
        "entry_execution_sizing_valid",
        "entry_execution_sizing_blockers",
        "entry_execution_sizing_plan_sha256",
        "entry_price_plan_schema",
        "entry_price_plan_id",
        "entry_price_plan_owner",
        "entry_price_plan_sha256",
        "entry_quantity_leg_four_arm_evaluation",
    }
)
# An aborted probe can still be restored on restart to preserve its
# scale-in-forbidden holding state, so recovery deliberately has a narrower
# terminal set.  Capacity, however, must release as soon as no order bundle is
# in flight.
PROBE_CAPACITY_TERMINAL_PHASES = frozenset(
    {"aborted", "complete", "bundle_completed", "partial_complete"}
)
PROBE_RECOVERY_TERMINAL_PHASES = frozenset(
    {"complete", "bundle_completed", "partial_complete"}
)
_PROBE_RUNTIME_STATE_LOCK = threading.RLock()


def _kst_date(now: datetime | None = None) -> str:
    current = now or datetime.now(timezone(timedelta(hours=9)))
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone(timedelta(hours=9)))
    return current.astimezone(timezone(timedelta(hours=9))).date().isoformat()


def _probe_runtime_config(*, now: datetime | None = None) -> dict[str, Any]:
    active_date = str(
        os.environ.get("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ACTIVE_DATE") or ""
    ).strip()
    enabled = _safe_bool(os.environ.get("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ENABLED"))
    return {
        "enabled": bool(
            enabled and active_date.upper() in {_kst_date(now), DAILY_ACTIVE_DATE_TOKEN}
        ),
        "configured_enabled": enabled,
        "active_date": active_date,
        "probe_qty": max(
            1,
            _safe_int(os.environ.get("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_QTY"), 1),
        ),
        "timeout_sec": max(
            1,
            _safe_int(os.environ.get("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_TIMEOUT_SEC"), 3),
        ),
        "max_bundles": max(
            0,
            _safe_int(os.environ.get("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_MAX_BUNDLES"), 5),
        ),
        "max_slippage_bps": max(
            0.0,
            float(
                _safe_float(
                    os.environ.get("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_MAX_SLIPPAGE_BPS"),
                    50.0,
                )
                or 0.0
            ),
        ),
        "anchor_mode": str(
            os.environ.get("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_ANCHOR_MODE")
            or "fill_clamped_to_fresh_bbo"
        ).strip(),
    }


def _empty_probe_runtime_state(target_date: str) -> dict[str, Any]:
    return {
        "schema_version": PROBE_RUNTIME_STATE_SCHEMA_VERSION,
        "target_date": target_date,
        "submitted_bundle_count": 0,
        "circuit_open": False,
        "circuit_reason": "",
        "bundles": {},
    }


def _load_probe_runtime_state(target_date: str) -> dict[str, Any]:
    payload = _load_json(PROBE_RUNTIME_STATE_PATH)
    if not PROBE_RUNTIME_STATE_PATH.exists():
        return _empty_probe_runtime_state(target_date)
    if (
        not payload
        or payload.get("schema_version") != PROBE_RUNTIME_STATE_SCHEMA_VERSION
    ):
        state = _empty_probe_runtime_state(target_date)
        state["circuit_open"] = True
        state["circuit_reason"] = "runtime_state_unreadable_or_schema_mismatch"
        return state
    if str(payload.get("target_date") or "") != target_date:
        return _empty_probe_runtime_state(target_date)
    if not isinstance(payload.get("bundles"), dict):
        payload["bundles"] = {}
    return payload


def _write_probe_runtime_state(payload: dict[str, Any]) -> None:
    PROBE_RUNTIME_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    temp_path = PROBE_RUNTIME_STATE_PATH.with_suffix(".tmp")
    temp_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temp_path, PROBE_RUNTIME_STATE_PATH)


def probe_runtime_state_snapshot(*, now: datetime | None = None) -> dict[str, Any]:
    target_date = _kst_date(now)
    with _PROBE_RUNTIME_STATE_LOCK:
        return dict(_load_probe_runtime_state(target_date))


def recover_probe_submit_contract_for_fill(
    stock: dict[str, Any],
    *,
    order_no: str = "",
    now: datetime | None = None,
) -> dict[str, Any]:
    """Hydrate immutable submit fields when a probe fill wins the submit race.

    Kiwoom can deliver the execution receipt immediately after accepting the
    order, before the submit thread has staged the returned order number and
    pending-order row.  The probe reservation is persisted before that broker
    call, so it is the only safe recovery source for the missing submit
    contract.  This helper never changes the probe phase and never grants
    residual submission authority.
    """

    code = str(stock.get("code") or stock.get("stock_code") or "").strip()[:6]
    target_id = str(stock.get("id") or "").strip()
    observed_order_no = str(order_no or "").strip()
    phase = str(stock.get("entry_split_probe_phase") or "").strip()
    if phase not in {"probe_submitting", "probe_submitted", "probe_filled"}:
        return {"recovered": False, "reason": "not_probe_fill_phase"}
    if not code or not target_id:
        return {"recovered": False, "reason": "probe_fill_identity_missing"}

    submit_ai_action = (
        str(stock.get("entry_split_probe_ai_action_at_submit") or "").strip().upper()
    )
    submit_ai_result_source = (
        str(stock.get("entry_split_probe_ai_result_source_at_submit") or "")
        .strip()
        .lower()
    )
    immutable_ai_contract_present = bool(
        submit_ai_action in {"BUY", "WAIT"}
        and submit_ai_result_source in {"live", "prior_valid"}
        and _safe_float(stock.get("entry_split_probe_ai_confirmed_at_submit"), 0.0) > 0
        and str(stock.get("entry_split_probe_ai_action_source_at_submit") or "")
        .strip()
        .lower()
        not in {"", "-", "none", "not_available", "not_evaluated"}
        and str(stock.get("entry_split_probe_ai_decision_trace_id") or "")
        .strip()
        .lower()
        not in {"", "-", "none", "not_available", "not_evaluated"}
        and "entry_split_probe_wait_contract_at_submit" in stock
    )
    required_present = bool(
        str(stock.get("entry_split_probe_bundle_id") or "").strip()
        and _safe_int(stock.get("entry_split_probe_requested_qty"), 0) > 1
        and isinstance(stock.get("entry_split_probe_continuation"), dict)
        and _safe_int(stock.get("entry_split_probe_submit_best_ask"), 0) > 0
        and immutable_ai_contract_present
    )
    if required_present:
        return {"recovered": False, "reason": "submit_contract_already_hydrated"}

    target_date = _kst_date(now)
    hydrated_bundle_id = str(stock.get("entry_split_probe_bundle_id") or "").strip()
    with _PROBE_RUNTIME_STATE_LOCK:
        payload = _load_probe_runtime_state(target_date)
        bundles = payload.get("bundles") or {}
        if hydrated_bundle_id:
            raw_candidates = [bundles.get(hydrated_bundle_id)]
        else:
            raw_candidates = list(bundles.values())
        candidates = []
        for raw_bundle in raw_candidates:
            if not isinstance(raw_bundle, dict):
                continue
            bundle = dict(raw_bundle)
            bundle_code = str(bundle.get("code") or "").strip()[:6]
            bundle_target_id = str(bundle.get("target_id") or "").strip()
            bundle_phase = str(bundle.get("phase") or "").strip()
            bundle_order_no = str(bundle.get("order_no") or "").strip()
            if bundle_code != code or bundle_target_id != target_id:
                continue
            if bundle_phase not in {
                "probe_submitting",
                "probe_submitted",
                "probe_filled",
            }:
                continue
            if (
                observed_order_no
                and bundle_order_no
                and (observed_order_no != bundle_order_no)
            ):
                continue
            candidates.append(bundle)

    if not candidates:
        return {"recovered": False, "reason": "probe_submit_bundle_not_found"}
    if len(candidates) != 1:
        return {"recovered": False, "reason": "probe_submit_bundle_ambiguous"}

    bundle = candidates[0]
    bundle_id = str(bundle.get("bundle_id") or "").strip()
    requested_qty = _safe_int(bundle.get("requested_qty"), 0)
    continuation = bundle.get("continuation")
    submit_best_ask = _safe_int(bundle.get("probe_submit_best_ask"), 0)
    if (
        not bundle_id
        or requested_qty <= 1
        or not isinstance(continuation, dict)
        or submit_best_ask <= 0
    ):
        return {"recovered": False, "reason": "probe_submit_bundle_incomplete"}

    recovery_fields = {
        "entry_split_probe_bundle_id": bundle_id,
        "entry_split_probe_requested_qty": requested_qty,
        "entry_split_probe_continuation": dict(continuation),
        "entry_split_probe_submit_best_ask": submit_best_ask,
        "entry_split_probe_timeout_sec": bundle.get("timeout_sec"),
        "entry_split_probe_max_slippage_bps": bundle.get("max_slippage_bps"),
        "entry_split_probe_anchor_mode": bundle.get("anchor_mode"),
        "entry_split_probe_submitting_at": bundle.get("submitting_at"),
        "entry_split_probe_submitted_at": bundle.get("submitted_at"),
        "entry_split_probe_order_no": (
            bundle.get("order_no") or observed_order_no or None
        ),
        "entry_split_probe_ai_action_at_submit": bundle.get("ai_action_at_submit"),
        "entry_split_probe_ai_result_source_at_submit": bundle.get(
            "ai_result_source_at_submit"
        ),
        "entry_split_probe_ai_confirmed_at_submit": bundle.get(
            "ai_confirmed_at_submit"
        ),
        "entry_split_probe_ai_action_source_at_submit": bundle.get(
            "ai_action_source_at_submit"
        ),
        "entry_split_probe_ai_decision_trace_id": bundle.get("ai_decision_trace_id"),
        "probe_confirmation_count": bundle.get("probe_confirmation_count", 0),
        "probe_confirmation_last_at": bundle.get("probe_confirmation_last_at", 0.0),
        "probe_confirmation_last_state": bundle.get(
            "probe_confirmation_last_state", "UNKNOWN"
        ),
        "probe_confirmation_last_signature": bundle.get(
            "probe_confirmation_last_signature", ""
        ),
    }
    if "wait_contract_at_submit" in bundle:
        recovery_fields["entry_split_probe_wait_contract_at_submit"] = _safe_bool(
            bundle.get("wait_contract_at_submit")
        )
    restored_fields = []
    for key, value in recovery_fields.items():
        if value is None:
            continue
        current_value = stock.get(key)
        required_value_invalid = bool(
            (
                key == "entry_split_probe_bundle_id"
                and not str(current_value or "").strip()
            )
            or (
                key == "entry_split_probe_requested_qty"
                and _safe_int(current_value, 0) <= 1
            )
            or (
                key == "entry_split_probe_continuation"
                and not isinstance(current_value, dict)
            )
            or (
                key == "entry_split_probe_submit_best_ask"
                and _safe_int(current_value, 0) <= 0
            )
            or (
                key == "entry_split_probe_ai_action_at_submit"
                and str(current_value or "").strip().upper() not in {"BUY", "WAIT"}
            )
            or (
                key == "entry_split_probe_ai_result_source_at_submit"
                and str(current_value or "").strip().lower()
                not in {"live", "prior_valid"}
            )
            or (
                key == "entry_split_probe_ai_confirmed_at_submit"
                and _safe_float(current_value, 0.0) <= 0
            )
            or (
                key
                in {
                    "entry_split_probe_ai_action_source_at_submit",
                    "entry_split_probe_ai_decision_trace_id",
                }
                and str(current_value or "").strip().lower()
                in {"", "-", "none", "not_available", "not_evaluated"}
            )
        )
        if current_value not in (None, "") and not required_value_invalid:
            continue
        stock[key] = value
        restored_fields.append(key)
    recovered_ai_action = (
        str(stock.get("entry_split_probe_ai_action_at_submit") or "").strip().upper()
    )
    recovered_ai_result_source = (
        str(stock.get("entry_split_probe_ai_result_source_at_submit") or "")
        .strip()
        .lower()
    )
    recovered_contract_complete = bool(
        recovered_ai_action in {"BUY", "WAIT"}
        and recovered_ai_result_source in {"live", "prior_valid"}
        and _safe_float(stock.get("entry_split_probe_ai_confirmed_at_submit"), 0.0) > 0
        and str(stock.get("entry_split_probe_ai_action_source_at_submit") or "")
        .strip()
        .lower()
        not in {"", "-", "none", "not_available", "not_evaluated"}
        and str(stock.get("entry_split_probe_ai_decision_trace_id") or "")
        .strip()
        .lower()
        not in {"", "-", "none", "not_available", "not_evaluated"}
        and "entry_split_probe_wait_contract_at_submit" in stock
    )
    if not recovered_contract_complete:
        return {
            "recovered": False,
            "reason": "probe_submit_bundle_missing_immutable_ai_contract",
            "bundle_id": bundle_id,
            "bundle_phase": str(bundle.get("phase") or "unknown"),
            "restored_fields": tuple(restored_fields),
        }
    return {
        "recovered": True,
        "reason": "probe_submit_contract_recovered_for_fill",
        "bundle_id": bundle_id,
        "bundle_phase": str(bundle.get("phase") or "unknown"),
        "restored_fields": tuple(restored_fields),
    }


def _probe_recovered_execution_provenance(
    bundle: dict[str, Any],
) -> dict[str, Any]:
    """Restore only broker-confirmed entry provenance from a persisted bundle."""

    broker_route = str(bundle.get("broker_route") or "").strip().upper()
    effective_venue = str(bundle.get("effective_venue") or "").strip().upper()
    if broker_route not in {"KRX", "NXT", "SOR"}:
        return {}
    fields: dict[str, Any] = {
        "entry_execution_broker_route": broker_route,
        "entry_execution_broker_route_resolution": str(
            bundle.get("broker_route_resolution") or "persisted_probe_bundle"
        ).strip(),
        "entry_execution_route_recorded_at": (
            bundle.get("submitted_at") or bundle.get("filled_at")
        ),
    }
    if effective_venue in {"KRX", "NXT", "PREMARKET_KRX_LIKE"}:
        fields["effective_venue"] = effective_venue
        fields["entry_execution_cohort"] = effective_venue
    return {key: value for key, value in fields.items() if value not in (None, "")}


def recover_probe_runtime_bundle_for_stock(
    stock: dict[str, Any], *, now: datetime | None = None
) -> dict[str, Any]:
    """Restore an incomplete probe bundle onto a broker-recovered holding.

    Recovery never re-opens submission authority by itself.  It restores the
    persisted phase so the normal holding tick can either reconcile/cancel the
    known residual orders or fail closed.  Any quantity disagreement opens the
    session circuit breaker.
    """
    code = str(stock.get("code") or stock.get("stock_code") or "").strip()[:6]
    stock_target_id = str(stock.get("id") or "").strip()
    actual_qty = max(0, _safe_int(stock.get("buy_qty"), 0))
    if not code or actual_qty <= 0:
        return {"recovered": False, "reason": "no_live_holding"}
    hydrated_bundle_id = str(stock.get("entry_split_probe_bundle_id") or "").strip()
    if hydrated_bundle_id:
        target_date = _kst_date(now)
        with _PROBE_RUNTIME_STATE_LOCK:
            payload = _load_probe_runtime_state(target_date)
            bundle = dict((payload.get("bundles") or {}).get(hydrated_bundle_id) or {})
        stock_code = str(stock.get("code") or stock.get("stock_code") or "").strip()[:6]
        bundle_code = str(bundle.get("code") or "").strip()[:6]
        if bundle and stock_code and bundle_code and stock_code != bundle_code:
            return {"recovered": False, "reason": "hydrated_bundle_code_mismatch"}
        bundle_target_id = str(bundle.get("target_id") or "").strip()
        if bundle_target_id and stock_target_id and bundle_target_id != stock_target_id:
            return {"recovered": False, "reason": "hydrated_bundle_target_mismatch"}
        recovered_provenance = (
            _probe_recovered_execution_provenance(bundle)
            if stock.get("entry_execution_broker_route") in (None, "")
            else {}
        )
        missing_provenance = {
            key: value
            for key, value in recovered_provenance.items()
            if stock.get(key) in (None, "")
        }
        recovered_contract: dict[str, Any] = {}
        if "wait_contract_at_submit" in bundle:
            recovered_contract["entry_split_probe_wait_contract_at_submit"] = (
                _safe_bool(bundle.get("wait_contract_at_submit"))
            )
        abort_detail_reason = str(
            bundle.get("terminal_abort_detail_reason") or ""
        ).strip()
        if abort_detail_reason:
            recovered_contract.update(
                {
                    "entry_split_probe_abort_detail_reason": abort_detail_reason,
                    "entry_split_probe_terminal_abort_detail_reason": (
                        abort_detail_reason
                    ),
                }
            )
        # A hydrated identity is not proof that terminal guards survived.
        exploration_terminal = str(bundle.get("terminal_abort_reason") or "") == (
            "entry_setup_bounded_exploration_probe_only"
        )
        if exploration_terminal:
            recovered_contract["entry_split_probe_terminal_abort_reason"] = (
                "entry_setup_bounded_exploration_probe_only"
            )
        for key in (
            "entry_split_probe_scale_in_forbidden",
            "entry_split_probe_residual_expand_forbidden",
            "probe_expand_forbidden",
        ):
            if exploration_terminal or _safe_bool(bundle.get(key)):
                recovered_contract[key] = True
        missing_contract = {
            key: value
            for key, value in recovered_contract.items()
            if stock.get(key) in (None, "")
            or (value is True and not _safe_bool(stock.get(key)))
        }
        if missing_provenance or missing_contract:
            stock.update(missing_provenance)
            stock.update(missing_contract)
            return {
                "recovered": True,
                "reason": (
                    "already_hydrated_provenance_restored"
                    if missing_provenance
                    else "already_hydrated_contract_restored"
                ),
                "phase": str(bundle.get("phase") or "unknown"),
            }
        return {"recovered": False, "reason": "already_hydrated"}
    target_date = _kst_date(now)
    with _PROBE_RUNTIME_STATE_LOCK:
        payload = _load_probe_runtime_state(target_date)
        candidates = [
            dict(bundle)
            for bundle in (payload.get("bundles") or {}).values()
            if isinstance(bundle, dict)
            and str(bundle.get("code") or "").strip()[:6] == code
            and (
                not str(bundle.get("target_id") or "").strip()
                or not stock_target_id
                or str(bundle.get("target_id") or "").strip() == stock_target_id
            )
            and str(bundle.get("phase") or "") not in PROBE_RECOVERY_TERMINAL_PHASES
        ]
        if not candidates:
            return {"recovered": False, "reason": "no_incomplete_bundle"}
        candidates.sort(key=lambda item: str(item.get("updated_at") or ""))
        bundle = candidates[-1]
        bundle_id = str(bundle.get("bundle_id") or "").strip()
        phase = str(bundle.get("phase") or "").strip()
        requested_qty = _safe_int(bundle.get("requested_qty"), 0)
        persisted_fill_qty = _safe_int(bundle.get("fill_qty"), 0)
        if phase == "probe_recheck_pending" and actual_qty == 1:
            close_reason = "post_probe_recheck_cleared_on_restart"
            recovered_at = datetime.now(timezone.utc)
            source_quality_recheck = _safe_bool(
                bundle.get("source_quality_recheck_pending")
            )
            confirmation_count = max(
                0, _safe_int(bundle.get("probe_confirmation_count"), 0)
            )
            scale_in_forbidden = not source_quality_recheck
            probe_expand_forbidden = not source_quality_recheck
            terminal_direction_state = (
                str(bundle.get("post_probe_direction_state") or "UNKNOWN")
                .strip()
                .upper()
            )
            terminal_direction_reason = str(
                bundle.get("post_probe_direction_reason") or close_reason
            ).strip()
            terminal_continuation_action = (
                str(bundle.get("post_probe_continuation_action") or "BLOCK")
                .strip()
                .upper()
            )
            terminal_positive_groups = str(
                bundle.get("post_probe_direction_positive_groups") or "-"
            ).strip()
            terminal_negative_groups = str(
                bundle.get("post_probe_direction_negative_groups") or "-"
            ).strip()
            terminal_failure_signature = "|".join(
                (
                    close_reason,
                    terminal_direction_state,
                    terminal_direction_reason,
                    terminal_negative_groups,
                    f"{confirmation_count}/2",
                )
            )
            bundle.update(
                {
                    "phase": "aborted",
                    "reason": close_reason,
                    "soft_abort": source_quality_recheck,
                    "entry_split_probe_scale_in_forbidden": scale_in_forbidden,
                    "probe_expand_forbidden": probe_expand_forbidden,
                    "entry_split_probe_residual_expand_forbidden": (
                        probe_expand_forbidden
                    ),
                    "probe_confirmation_count": confirmation_count,
                    "probe_confirmation_last_at": bundle.get(
                        "probe_confirmation_last_at", 0.0
                    ),
                    "probe_confirmation_last_state": bundle.get(
                        "probe_confirmation_last_state", "UNKNOWN"
                    ),
                    "probe_confirmation_last_signature": bundle.get(
                        "probe_confirmation_last_signature", ""
                    ),
                    "scale_in_recheck_allowed": source_quality_recheck,
                    "scale_in_recheck_origin": (
                        "source_quality_restart_recovery"
                        if source_quality_recheck
                        else "-"
                    ),
                    "scale_in_recheck_reason": (
                        f"{close_reason}:source_quality_recovery"
                        if source_quality_recheck
                        else "hard_or_non_directional_abort"
                    ),
                    "source_quality_recheck_released": source_quality_recheck,
                    "source_quality_recheck_unfilled_qty": (
                        max(0, requested_qty - actual_qty)
                        if source_quality_recheck
                        else 0
                    ),
                    "recovered_actual_qty": actual_qty,
                    "terminal_at": recovered_at.timestamp(),
                    "terminal_outcome": "residual_not_submitted",
                    "terminal_abort_reason": close_reason,
                    "terminal_direction_state": terminal_direction_state,
                    "terminal_direction_reason": terminal_direction_reason,
                    "terminal_continuation_action": terminal_continuation_action,
                    "terminal_positive_groups": terminal_positive_groups,
                    "terminal_negative_groups": terminal_negative_groups,
                    "terminal_confirmation_count": confirmation_count,
                    "terminal_failure_signature": terminal_failure_signature,
                    "restart_recovered_at": recovered_at.isoformat(),
                    "updated_at": recovered_at.isoformat(),
                }
            )
            payload.setdefault("bundles", {})[bundle_id] = bundle
            _write_probe_runtime_state(payload)
            stock.update(
                {
                    "entry_split_probe_phase": "aborted",
                    "entry_split_probe_bundle_id": bundle_id,
                    "entry_split_probe_abort_reason": close_reason,
                    "entry_split_probe_scale_in_forbidden": scale_in_forbidden,
                    "probe_expand_forbidden": probe_expand_forbidden,
                    "entry_split_probe_residual_expand_forbidden": (
                        probe_expand_forbidden
                    ),
                    "probe_confirmation_count": confirmation_count,
                    "probe_confirmation_last_at": bundle["probe_confirmation_last_at"],
                    "probe_confirmation_last_state": bundle[
                        "probe_confirmation_last_state"
                    ],
                    "probe_confirmation_last_signature": bundle[
                        "probe_confirmation_last_signature"
                    ],
                    "entry_split_probe_soft_abort": source_quality_recheck,
                    "entry_split_probe_scale_in_recheck_allowed": (
                        source_quality_recheck
                    ),
                    "entry_split_probe_scale_in_recheck_origin": bundle[
                        "scale_in_recheck_origin"
                    ],
                    "entry_split_probe_scale_in_recheck_reason": bundle[
                        "scale_in_recheck_reason"
                    ],
                    "entry_split_probe_source_quality_recheck_released": (
                        source_quality_recheck
                    ),
                    "entry_split_probe_source_quality_recheck_unfilled_qty": bundle[
                        "source_quality_recheck_unfilled_qty"
                    ],
                    "entry_split_probe_source_quality_recheck_pending": False,
                    "entry_split_probe_terminal_at": bundle["terminal_at"],
                    "entry_split_probe_terminal_outcome": bundle["terminal_outcome"],
                    "entry_split_probe_terminal_abort_reason": bundle[
                        "terminal_abort_reason"
                    ],
                    "entry_split_probe_terminal_direction_state": bundle[
                        "terminal_direction_state"
                    ],
                    "entry_split_probe_terminal_direction_reason": bundle[
                        "terminal_direction_reason"
                    ],
                    "entry_split_probe_terminal_continuation_action": bundle[
                        "terminal_continuation_action"
                    ],
                    "entry_split_probe_terminal_positive_groups": bundle[
                        "terminal_positive_groups"
                    ],
                    "entry_split_probe_terminal_negative_groups": bundle[
                        "terminal_negative_groups"
                    ],
                    "entry_split_probe_terminal_confirmation_count": bundle[
                        "terminal_confirmation_count"
                    ],
                    "entry_split_probe_terminal_failure_signature": bundle[
                        "terminal_failure_signature"
                    ],
                    "entry_requested_qty": actual_qty,
                    "requested_buy_qty": actual_qty,
                    **_probe_recovered_execution_provenance(bundle),
                }
            )
            return {
                "recovered": True,
                "reason": close_reason,
                "phase": "aborted",
            }
        quantity_matches = bool(
            requested_qty > 1
            and actual_qty <= requested_qty
            and (
                (phase in {"probe_filled", "residual_claimed"} and actual_qty == 1)
                or (
                    phase
                    in {
                        "residual_submitting",
                        "residual_submitted",
                        "residual_partial_submitted",
                        "aborted",
                    }
                    and actual_qty >= max(1, persisted_fill_qty)
                )
            )
        )
        if not quantity_matches:
            # The phase/quantity disagreement must keep the probe circuit
            # fail-closed, but it does not invalidate broker-confirmed route
            # provenance captured from the successful submit response.  In
            # particular, a restart can observe one filled share while the
            # durable bundle still says ``probe_submitted``.  Dropping the
            # confirmed route here leaves holding submit-authority Exact V2
            # preflight permanently unable to prove its execution venue.
            # Restore provenance only; never restore residual-submit
            # authority from a mismatched bundle.
            recovered_execution_provenance = {
                key: value
                for key, value in _probe_recovered_execution_provenance(bundle).items()
                if stock.get(key) in (None, "")
            }
            payload["circuit_open"] = True
            payload["circuit_reason"] = "probe_restart_recovery_quantity_mismatch"
            payload["circuit_opened_at"] = datetime.now(timezone.utc).isoformat()
            bundle["phase"] = "aborted"
            bundle["reason"] = "probe_restart_recovery_quantity_mismatch"
            bundle["recovered_actual_qty"] = actual_qty
            bundle["entry_split_probe_scale_in_forbidden"] = True
            bundle["probe_expand_forbidden"] = True
            bundle["updated_at"] = datetime.now(timezone.utc).isoformat()
            payload.setdefault("bundles", {})[bundle_id] = bundle
            _write_probe_runtime_state(payload)
            stock.update(
                {
                    "entry_split_probe_phase": "aborted",
                    "entry_split_probe_bundle_id": bundle_id,
                    "entry_split_probe_abort_reason": (
                        "probe_restart_recovery_quantity_mismatch"
                    ),
                    "entry_split_probe_scale_in_forbidden": True,
                    "probe_expand_forbidden": True,
                    **recovered_execution_provenance,
                }
            )
            return {
                "recovered": False,
                "reason": "probe_restart_recovery_quantity_mismatch",
                "circuit_open": True,
            }

        soft_abort = _safe_bool(bundle.get("soft_abort"))
        scale_in_forbidden = (
            _safe_bool(bundle.get("entry_split_probe_scale_in_forbidden"))
            if "entry_split_probe_scale_in_forbidden" in bundle
            else bool(phase != "complete" and not soft_abort)
        )
        probe_expand_forbidden = (
            _safe_bool(bundle.get("probe_expand_forbidden"))
            if "probe_expand_forbidden" in bundle
            else bool(phase == "aborted" and not soft_abort)
        )
        residual_expand_forbidden = (
            _safe_bool(bundle.get("entry_split_probe_residual_expand_forbidden"))
            if "entry_split_probe_residual_expand_forbidden" in bundle
            else probe_expand_forbidden
        )
        confirmation_count = max(
            0, _safe_int(bundle.get("probe_confirmation_count"), 0)
        )
        terminal_abort_reason = None
        terminal_direction_state = None
        terminal_direction_reason = None
        terminal_continuation_action = None
        terminal_positive_groups = None
        terminal_negative_groups = None
        if phase == "aborted":
            terminal_abort_reason = (
                bundle.get("terminal_abort_reason")
                or bundle.get("reason")
                or "restart_recovered_aborted_bundle"
            )
            terminal_direction_state = bundle.get(
                "terminal_direction_state"
            ) or bundle.get("post_probe_direction_state")
            terminal_direction_reason = bundle.get(
                "terminal_direction_reason"
            ) or bundle.get("post_probe_direction_reason")
            terminal_continuation_action = bundle.get(
                "terminal_continuation_action"
            ) or bundle.get("post_probe_continuation_action")
            terminal_positive_groups = bundle.get(
                "terminal_positive_groups"
            ) or bundle.get("post_probe_direction_positive_groups")
            terminal_negative_groups = bundle.get(
                "terminal_negative_groups"
            ) or bundle.get("post_probe_direction_negative_groups")
        recovery_fields = {
            "entry_split_probe_phase": phase,
            "entry_split_probe_bundle_id": bundle_id,
            "entry_split_probe_abort_reason": (
                bundle.get("reason") if phase == "aborted" else None
            ),
            "entry_split_probe_requested_qty": requested_qty,
            "entry_split_probe_continuation": bundle.get("continuation"),
            "entry_split_probe_submit_best_ask": bundle.get("probe_submit_best_ask"),
            "entry_split_probe_timeout_sec": bundle.get("timeout_sec"),
            "entry_split_probe_max_slippage_bps": bundle.get("max_slippage_bps"),
            "entry_split_probe_anchor_mode": bundle.get("anchor_mode"),
            "entry_split_probe_submitting_at": bundle.get("submitting_at"),
            "entry_split_probe_submitted_at": bundle.get("submitted_at"),
            "entry_split_probe_order_no": bundle.get("order_no"),
            "entry_split_probe_fill_price": bundle.get("fill_price"),
            "entry_split_probe_filled_at": bundle.get("filled_at"),
            "entry_split_probe_residual_claimed": phase
            in {
                "residual_claimed",
                "residual_submitting",
                "residual_submitted",
                "residual_partial_submitted",
            },
            "entry_split_probe_scale_in_forbidden": scale_in_forbidden,
            "probe_expand_forbidden": probe_expand_forbidden,
            "entry_split_probe_residual_expand_forbidden": (residual_expand_forbidden),
            "probe_confirmation_count": confirmation_count,
            "probe_confirmation_last_at": bundle.get("probe_confirmation_last_at", 0.0),
            "probe_confirmation_last_state": bundle.get(
                "probe_confirmation_last_state", "UNKNOWN"
            ),
            "probe_confirmation_last_signature": bundle.get(
                "probe_confirmation_last_signature", ""
            ),
            "entry_split_probe_soft_abort": soft_abort,
            "entry_split_probe_scale_in_recheck_allowed": _safe_bool(
                bundle.get("scale_in_recheck_allowed")
            ),
            "entry_split_probe_scale_in_recheck_origin": bundle.get(
                "scale_in_recheck_origin"
            ),
            "entry_split_probe_scale_in_recheck_reason": bundle.get(
                "scale_in_recheck_reason"
            ),
            "entry_split_probe_source_quality_recheck_released": _safe_bool(
                bundle.get("source_quality_recheck_released")
            ),
            "entry_split_probe_source_quality_recheck_released_at": bundle.get(
                "source_quality_recheck_released_at"
            ),
            "entry_split_probe_source_quality_recheck_unfilled_qty": bundle.get(
                "source_quality_recheck_unfilled_qty"
            ),
            "entry_split_probe_source_quality_recheck_reason": bundle.get(
                "source_quality_recheck_reason"
            ),
            "entry_split_probe_source_quality_recheck_pending": False,
            "entry_split_probe_ai_action_at_submit": bundle.get("ai_action_at_submit"),
            "entry_split_probe_ai_result_source_at_submit": bundle.get(
                "ai_result_source_at_submit"
            ),
            "entry_split_probe_ai_confirmed_at_submit": bundle.get(
                "ai_confirmed_at_submit"
            ),
            "entry_split_probe_ai_action_source_at_submit": bundle.get(
                "ai_action_source_at_submit"
            ),
            "entry_split_probe_terminal_at": bundle.get("terminal_at"),
            "entry_split_probe_terminal_outcome": (
                bundle.get("terminal_outcome")
                or ("residual_not_submitted" if phase == "aborted" else None)
            ),
            "entry_split_probe_terminal_abort_reason": terminal_abort_reason,
            "entry_split_probe_abort_detail_reason": bundle.get(
                "terminal_abort_detail_reason"
            ),
            "entry_split_probe_terminal_abort_detail_reason": bundle.get(
                "terminal_abort_detail_reason"
            ),
            "entry_split_probe_terminal_direction_state": terminal_direction_state,
            "entry_split_probe_terminal_direction_reason": terminal_direction_reason,
            "entry_split_probe_terminal_continuation_action": (
                terminal_continuation_action
            ),
            "entry_split_probe_terminal_positive_groups": terminal_positive_groups,
            "entry_split_probe_terminal_negative_groups": terminal_negative_groups,
            "entry_split_probe_terminal_confirmation_count": (
                bundle.get("terminal_confirmation_count", confirmation_count)
                if phase == "aborted"
                else None
            ),
            "entry_split_probe_terminal_failure_signature": bundle.get(
                "terminal_failure_signature"
            ),
            "entry_requested_qty": actual_qty if soft_abort else requested_qty,
            "requested_buy_qty": actual_qty if soft_abort else requested_qty,
            **_probe_recovered_execution_provenance(bundle),
        }
        if "wait_contract_at_submit" in bundle:
            recovery_fields["entry_split_probe_wait_contract_at_submit"] = _safe_bool(
                bundle.get("wait_contract_at_submit")
            )
        stock.update(
            {key: value for key, value in recovery_fields.items() if value is not None}
        )
        persisted_orders = bundle.get("residual_orders")
        if isinstance(persisted_orders, list) and persisted_orders:
            stock["pending_entry_orders"] = [
                dict(order)
                for order in persisted_orders
                if isinstance(order, dict) and str(order.get("ord_no") or "").strip()
            ]
        bundle["restart_recovered_at"] = datetime.now(timezone.utc).isoformat()
        bundle["recovered_actual_qty"] = actual_qty
        bundle["entry_split_probe_scale_in_forbidden"] = scale_in_forbidden
        bundle["probe_expand_forbidden"] = probe_expand_forbidden
        bundle["entry_split_probe_residual_expand_forbidden"] = (
            residual_expand_forbidden
        )
        bundle["probe_confirmation_count"] = confirmation_count
        bundle.setdefault("probe_confirmation_last_at", 0.0)
        bundle.setdefault("probe_confirmation_last_state", "UNKNOWN")
        bundle.setdefault("probe_confirmation_last_signature", "")
        payload.setdefault("bundles", {})[bundle_id] = bundle
        _write_probe_runtime_state(payload)
        return {
            "recovered": True,
            "reason": "incomplete_bundle_restored",
            "phase": phase,
        }


def update_probe_runtime_bundle(
    bundle_id: str,
    *,
    phase: str,
    now: datetime | None = None,
    **fields: Any,
) -> dict[str, Any]:
    target_date = _kst_date(now)
    with _PROBE_RUNTIME_STATE_LOCK:
        payload = _load_probe_runtime_state(target_date)
        bundles = payload.setdefault("bundles", {})
        bundle = dict(bundles.get(bundle_id) or {})
        countable_phase = phase in {
            "probe_submitted",
            "probe_filled",
            "residual_claimed",
            "residual_submitted",
            "complete",
        }
        if countable_phase and not _safe_bool(bundle.get("counted_submitted")):
            payload["submitted_bundle_count"] = (
                _safe_int(payload.get("submitted_bundle_count"), 0) + 1
            )
            bundle["counted_submitted"] = True
        bundle.update(fields)
        bundle.update(
            {
                "bundle_id": bundle_id,
                "phase": phase,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        bundles[bundle_id] = bundle
        _write_probe_runtime_state(payload)
        return dict(bundle)


def trip_probe_runtime_circuit(reason: str, *, now: datetime | None = None) -> None:
    target_date = _kst_date(now)
    with _PROBE_RUNTIME_STATE_LOCK:
        payload = _load_probe_runtime_state(target_date)
        payload["circuit_open"] = True
        payload["circuit_reason"] = str(reason or "invariant_violation")
        payload["circuit_opened_at"] = datetime.now(timezone.utc).isoformat()
        _write_probe_runtime_state(payload)


def _reserve_probe_runtime_bundle(
    *,
    stock: dict[str, Any],
    total_qty: int,
    submit_contract: dict[str, Any],
    now: datetime | None = None,
) -> tuple[str, str]:
    config = _probe_runtime_config(now=now)
    if not config["enabled"]:
        return "", "probe_runtime_inactive"
    if config["probe_qty"] != 1:
        return "", "probe_qty_must_equal_one"
    if not isinstance(submit_contract, dict):
        return "", "probe_submit_contract_invalid"
    contract = dict(submit_contract)
    continuation = contract.get("continuation")
    continuation = continuation if isinstance(continuation, dict) else {}
    continuation_requested_qty = _safe_int(continuation.get("requested_qty"), 0)
    continuation_residual_qty = _safe_int(continuation.get("residual_qty"), 0)
    continuation_quantities = [
        _safe_int(value, 0) for value in continuation.get("residual_quantities") or []
    ]
    if (
        continuation_requested_qty != total_qty
        or continuation_residual_qty != total_qty - 1
        or not continuation_quantities
        or any(value <= 0 for value in continuation_quantities)
        or sum(continuation_quantities) != continuation_residual_qty
        or _safe_int(contract.get("probe_submit_best_ask"), 0) <= 0
    ):
        return "", "probe_submit_contract_invalid"
    target_date = _kst_date(now)
    with _PROBE_RUNTIME_STATE_LOCK:
        payload = _load_probe_runtime_state(target_date)
        if _safe_bool(payload.get("circuit_open")):
            return "", "probe_circuit_open"
        current_count = _safe_int(payload.get("submitted_bundle_count"), 0)
        active_bundle_count = sum(
            1
            for bundle in (payload.get("bundles") or {}).values()
            if isinstance(bundle, dict)
            # Unknown/missing phase is conservatively treated as in-flight;
            # only explicit terminal phases release a probe slot.
            and str(bundle.get("phase") or "") not in PROBE_CAPACITY_TERMINAL_PHASES
        )
        # `MAX_BUNDLES` bounds concurrent probe reservations, not the number of
        # initial entries that may use probe-first over a day.  A cumulative
        # cap silently reverted every later real SCALPING initial entry to
        # direct multi-leg submission once the early probe budget was consumed.
        # Every non-terminal phase, including fill/recheck/residual phases,
        # consumes capacity.  Completed/aborted bundles retain recovery
        # provenance but no longer occupy a live probe slot.
        if active_bundle_count >= config["max_bundles"]:
            return "", "probe_active_bundle_cap_reached"
        code = str(stock.get("code") or stock.get("stock_code") or "unknown")[:6]
        nonce = f"{target_date}:{code}:{time_ns()}:{current_count + 1}"
        bundle_id = f"{code}-probe-{hashlib.sha1(nonce.encode()).hexdigest()[:12]}"
        payload.setdefault("bundles", {})[bundle_id] = {
            **contract,
            "bundle_id": bundle_id,
            "phase": "planned",
            "code": code,
            "target_id": stock.get("id"),
            "requested_qty": int(total_qty),
            "reserved_at": datetime.now(timezone.utc).isoformat(),
        }
        _write_probe_runtime_state(payload)
        return bundle_id, "reserved"


def time_ns() -> int:
    """Small indirection kept patchable in deterministic tests."""
    import time

    return time.time_ns()


def report_paths(target_date: str) -> tuple[Path, Path]:
    base = REPORT_DIR / f"{REPORT_TYPE}_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def policy_path(target_date: str) -> Path:
    return POLICY_DIR / f"entry_split_order_policy_{target_date}.json"


def generation_report_path(target_date: str, generation_id: str) -> Path:
    """Return the immutable report snapshot path for one bound generation."""

    return (
        REPORT_DIR
        / "generations"
        / (f"{REPORT_TYPE}_{target_date}_{generation_id}.json")
    )


def generation_policy_path(target_date: str, generation_id: str) -> Path:
    """Return the immutable policy snapshot path for one bound generation."""

    return (
        POLICY_DIR
        / "generations"
        / (f"entry_split_order_policy_{target_date}_{generation_id}.json")
    )


def generation_policy_snapshot_path(report: dict[str, Any]) -> Path | None:
    """Resolve a generated report's immutable policy without trusting an alias."""

    binding = report.get("artifact_generation_binding")
    binding = binding if isinstance(binding, dict) else {}
    target_date = str(report.get("date") or "").strip()
    generation_id = str(binding.get("generation_id") or "").strip()
    if not _valid_iso_date(target_date) or not _valid_generation_id(generation_id):
        return None
    return generation_policy_path(target_date, generation_id)


def _pipeline_events_path(target_date: str) -> Path:
    return DATA_DIR / "pipeline_events" / f"pipeline_events_{target_date}.jsonl"


def _threshold_events_path(target_date: str) -> Path:
    return DATA_DIR / "threshold_cycle" / f"threshold_events_{target_date}.jsonl"


def _sim_post_sell_path(target_date: str) -> Path:
    return DATA_DIR / "post_sell" / f"sim_post_sell_evaluations_{target_date}.jsonl"


def _real_post_sell_path(target_date: str) -> Path:
    return DATA_DIR / "post_sell" / f"post_sell_evaluations_{target_date}.jsonl"


def _real_post_sell_candidate_path(target_date: str) -> Path:
    return DATA_DIR / "post_sell" / f"post_sell_candidates_{target_date}.jsonl"


def _threshold_cycle_ev_path(target_date: str) -> Path:
    return (
        DATA_DIR
        / "report"
        / "threshold_cycle_ev"
        / f"threshold_cycle_ev_{target_date}.json"
    )


def _source_quality_path(target_date: str) -> Path:
    return (
        DATA_DIR
        / "report"
        / "observation_source_quality_audit"
        / f"observation_source_quality_audit_{target_date}.json"
    )


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _write_immutable_json(path: Path, payload: dict[str, Any]) -> None:
    """Create a content-addressed snapshot, rejecting an identity collision."""

    if path.exists():
        if _load_json(path) != payload:
            raise RuntimeError(f"immutable_generation_collision:{path}")
        return
    _write_json(path, payload)


def _canonical_sha256(payload: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _valid_generation_id(value: Any) -> bool:
    text = str(value or "").strip()
    return bool(
        len(text) == 64 and all(character in "0123456789abcdef" for character in text)
    )


def _valid_iso_date(value: Any) -> bool:
    text = str(value or "").strip()
    try:
        return date.fromisoformat(text).isoformat() == text
    except ValueError:
        return False


def _without_generation_binding(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in payload.items()
        if key != "artifact_generation_binding"
    }


def bind_report_policy_generation(
    report: dict[str, Any], policy: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Bind one report/policy pair without introducing a circular digest."""

    report_payload = _without_generation_binding(report)
    policy_payload = _without_generation_binding(policy)
    report_sha256 = _canonical_sha256(report_payload)
    policy_sha256 = _canonical_sha256(policy_payload)
    identity = {
        "schema_version": GENERATION_BINDING_SCHEMA_VERSION,
        "target_date": str(report_payload.get("date") or ""),
        "policy_version": str(policy_payload.get("policy_version") or ""),
        "report_content_sha256": report_sha256,
        "policy_content_sha256": policy_sha256,
    }
    generation_id = _canonical_sha256(identity)
    binding = {**identity, "generation_id": generation_id}
    return (
        {**report_payload, "artifact_generation_binding": binding},
        {**policy_payload, "artifact_generation_binding": binding},
    )


def validate_report_policy_generation(
    report: dict[str, Any], policy: dict[str, Any]
) -> tuple[bool, str]:
    """Validate exact report/policy lineage before a policy can be consumed."""

    report_binding = report.get("artifact_generation_binding")
    policy_binding = policy.get("artifact_generation_binding")
    if not isinstance(report_binding, dict) or not isinstance(policy_binding, dict):
        return False, "generation_binding_missing"
    if report_binding != policy_binding:
        return False, "generation_binding_pair_mismatch"
    expected_report, expected_policy = bind_report_policy_generation(report, policy)
    expected_binding = expected_report["artifact_generation_binding"]
    if expected_binding != report_binding:
        return False, "generation_binding_digest_mismatch"
    if expected_policy["artifact_generation_binding"] != policy_binding:
        return False, "generation_binding_policy_digest_mismatch"
    if report.get("schema_version") != SCHEMA_VERSION:
        return False, "generation_source_report_schema_invalid"
    if policy.get("schema_version") != POLICY_SCHEMA_VERSION:
        return False, "generation_policy_schema_invalid"
    if report.get("date") != policy.get("source_date"):
        return False, "generation_target_date_mismatch"
    recommended = report.get("recommended_policy")
    if not isinstance(recommended, dict):
        return False, "generation_recommended_policy_missing"
    if recommended.get("policy_version") != policy.get("policy_version"):
        return False, "generation_recommended_policy_version_mismatch"
    try:
        source_date = date.fromisoformat(str(policy.get("source_date") or ""))
    except ValueError:
        return False, "generation_source_date_invalid"
    atomic_contract_required = source_date >= ATOMIC_EXECUTION_SIZING_REQUIRED_FROM_DATE
    if atomic_contract_required:
        expected_atomic = {
            "entry_execution_sizing_plan_schema": (ATOMIC_EXECUTION_SIZING_SCHEMA),
            "entry_execution_sizing_policy": (ATOMIC_EXECUTION_SIZING_BASELINE_POLICY),
        }
        if any(policy.get(key) != value for key, value in expected_atomic.items()):
            return False, "generation_atomic_execution_sizing_policy_invalid"
        if any(recommended.get(key) != value for key, value in expected_atomic.items()):
            return False, "generation_atomic_execution_sizing_handoff_invalid"
    if source_date >= ATOMIC_PRICE_PLAN_REQUIRED_FROM_DATE:
        if policy.get("entry_price_plan_schema") != ATOMIC_PRICE_PLAN_SCHEMA:
            return False, "generation_atomic_price_plan_policy_invalid"
        if recommended.get("entry_price_plan_schema") != ATOMIC_PRICE_PLAN_SCHEMA:
            return False, "generation_atomic_price_plan_handoff_invalid"
    if (report.get("execution_model_validation") or policy.get("execution_model_validation_contract")
            or (policy.get("runtime_apply_allowed") is True and str(policy.get("source_date") or "") >= "2026-09-17")):
        valid, reason = execution_model_policy_contract_status(report, policy)
        if not valid:
            return False, reason
    return True, "generation_binding_valid"


def policy_report_generation_contract_status(
    policy: dict[str, Any],
) -> tuple[bool, str]:
    """Load and validate the source report named by a generated policy."""

    source_date = str(policy.get("source_date") or "").strip()
    try:
        binding_required = (
            date.fromisoformat(source_date) >= GENERATION_BINDING_REQUIRED_FROM_DATE
        )
    except ValueError:
        return False, "generation_source_date_invalid"
    binding_present = isinstance(policy.get("artifact_generation_binding"), dict)
    if not binding_present:
        return (
            (False, "generation_binding_required")
            if binding_required
            else (True, "legacy_policy_before_generation_binding_activation")
        )
    binding = policy.get("artifact_generation_binding")
    binding = binding if isinstance(binding, dict) else {}
    generation_id = str(binding.get("generation_id") or "").strip()
    if not _valid_generation_id(generation_id):
        return False, "generation_id_invalid"
    immutable_report = generation_report_path(source_date, generation_id)
    source_report = str(policy.get("source_report") or "").strip()
    if not source_report:
        return False, "generation_source_report_path_missing"
    # New generations must be consumed from the immutable snapshot.  The date
    # alias fallback exists only for pre-migration evidence.
    if immutable_report.is_file():
        report = _load_json(immutable_report)
    elif binding_required:
        return False, "immutable_generation_source_report_missing"
    else:
        report = _load_json(Path(source_report))
    if not report:
        return False, "generation_source_report_missing_or_invalid"
    return validate_report_policy_generation(report, policy)


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, default: float | None = 0.0) -> float | None:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _runtime_shape_gate_contract_status(gate: Any) -> tuple[bool, str]:
    """Validate shape gates before PREOPEN can select their policy file."""

    if gate is None:
        return True, "no_runtime_shape_gate"
    if not isinstance(gate, dict):
        return False, "runtime_shape_gate_not_object"
    if gate.get("schema") != "entry_split_runtime_shape_gate_v1":
        return False, "runtime_shape_gate_schema_invalid"
    parent_id = str(gate.get("required_policy_split_variant_id") or "").strip()
    child_id = str(gate.get("observed_child_variant_id") or "").strip()
    requested_legs = _safe_int(gate.get("required_requested_legs"), 0)
    desired_legs = _safe_int(gate.get("required_desired_legs"), 0)
    first_weight = _safe_float(gate.get("required_runtime_first_weight"), None)
    if not parent_id or not child_id.startswith(f"{parent_id}__"):
        return False, "runtime_shape_gate_variant_identity_invalid"
    if requested_legs < 2 or desired_legs < 2 or desired_legs > requested_legs:
        return False, "runtime_shape_gate_leg_contract_invalid"
    if first_weight is None or not 0.0 < first_weight <= 1.0:
        return False, "runtime_shape_gate_first_weight_invalid"
    for key in (
        "require_runtime_weight_adjusted",
        "require_market_first_leg_disabled",
        "require_probe_first_enabled",
        "require_probe_first_eligible",
    ):
        if not isinstance(gate.get(key), bool):
            return False, f"runtime_shape_gate_{key}_not_boolean"
    return True, "runtime_shape_gate_contract_valid"


def runtime_apply_authority_contract_status(
    payload: dict[str, Any],
) -> tuple[bool, str]:
    """Validate the explicit exploration-vs-EV authority split when present."""

    authority_fields = {
        "exploration_seed_allowed",
        "ev_validated_runtime_apply_allowed",
        "runtime_apply_compatibility_semantics",
    }
    if not authority_fields.intersection(payload):
        return True, "legacy_policy_without_explicit_authority_split"
    if (
        payload.get("runtime_apply_compatibility_semantics")
        != RUNTIME_APPLY_COMPATIBILITY_SEMANTICS
    ):
        return False, "runtime_apply_compatibility_semantics_invalid"
    for field in (
        "runtime_apply_allowed",
        "exploration_seed_allowed",
        "ev_validated_runtime_apply_allowed",
    ):
        if not isinstance(payload.get(field), bool):
            return False, f"{field}_not_boolean"
    if "baseline_runtime_defaults_enabled" in payload and not isinstance(
        payload.get("baseline_runtime_defaults_enabled"), bool
    ):
        return False, "baseline_runtime_defaults_enabled_not_boolean"
    missing_bucket_action = payload.get("missing_bucket_action")
    if missing_bucket_action is not None:
        expected_action = (
            "runtime_default_fallback"
            if _safe_bool(payload.get("baseline_runtime_defaults_enabled"))
            else "keep_original_order"
        )
        if missing_bucket_action != expected_action:
            return False, "missing_bucket_action_inconsistent_with_baseline_scope"
    for field in ("exploration_seed_count", "ev_validated_bucket_count"):
        if field not in payload:
            continue
        value = payload.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            return False, f"{field}_not_nonnegative_integer"
    exploration_allowed = payload["exploration_seed_allowed"]
    ev_validated_allowed = payload["ev_validated_runtime_apply_allowed"]
    compatibility_allowed = payload["runtime_apply_allowed"]
    if compatibility_allowed != (exploration_allowed or ev_validated_allowed):
        return False, "runtime_apply_authority_union_mismatch"
    if (
        _safe_bool(payload.get("baseline_runtime_defaults_enabled"))
        and not exploration_allowed
    ):
        return False, "baseline_runtime_without_exploration_seed_authority"
    if (
        _safe_int(payload.get("exploration_seed_count"), 0) > 0
        and not exploration_allowed
    ):
        return False, "exploration_seed_count_without_authority"
    if (
        _safe_int(payload.get("ev_validated_bucket_count"), 0) > 0
        and not ev_validated_allowed
    ):
        return False, "ev_validated_bucket_count_without_authority"
    expected_classes = {
        authority_class
        for authority_class, allowed in (
            ("bounded_exploration_seed", exploration_allowed),
            ("ev_validated_variant", ev_validated_allowed),
        )
        if allowed
    }
    if "runtime_apply_authority_classes" in payload:
        raw_classes = payload.get("runtime_apply_authority_classes")
        if not isinstance(raw_classes, list) or not all(
            isinstance(value, str) and value.strip() for value in raw_classes
        ):
            return False, "runtime_apply_authority_classes_not_string_list"
        actual_classes = {
            str(value).strip() for value in raw_classes if str(value).strip()
        }
        if actual_classes != expected_classes:
            return False, "runtime_apply_authority_classes_mismatch"
    buckets = payload.get("buckets")
    if isinstance(buckets, dict):
        explicit_bucket_count = payload.get("explicit_bucket_count")
        if explicit_bucket_count is not None and (
            isinstance(explicit_bucket_count, bool)
            or not isinstance(explicit_bucket_count, int)
            or explicit_bucket_count != len(buckets)
        ):
            return False, "explicit_bucket_count_mismatch"
        if (
            payload.get("runtime_apply_allowed") is True
            and not _safe_bool(payload.get("baseline_runtime_defaults_enabled"))
            and not buckets
        ):
            return False, "scoped_runtime_policy_has_no_selected_buckets"
        for bucket, bucket_policy in buckets.items():
            if not isinstance(bucket_policy, dict):
                return False, f"runtime_bucket_policy_invalid:{bucket}"
            gate_valid, gate_reason = _runtime_shape_gate_contract_status(
                bucket_policy.get("runtime_shape_gate")
            )
            if not gate_valid:
                return False, gate_reason
    return True, "explicit_runtime_apply_authority_split_valid"


def _event_fields(event: dict[str, Any]) -> dict[str, Any]:
    fields = event.get("fields") if isinstance(event.get("fields"), dict) else {}
    return {**event, **fields}


def _event_date(event: dict[str, Any]) -> str:
    for key in ("date", "target_date", "source_date", "trading_date", "signal_date"):
        value = str(event.get(key) or "").strip()
        if len(value) >= 10:
            return value[:10]
    ts = str(
        event.get("timestamp") or event.get("created_at") or event.get("ts") or ""
    ).strip()
    return ts[:10] if len(ts) >= 10 else ""


def _event_dt(event: dict[str, Any]) -> datetime | None:
    for key in ("emitted_at", "timestamp", "created_at", "ts"):
        value = str(event.get(key) or "").strip()
        if not value:
            continue
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            continue
        if parsed.tzinfo is not None:
            return parsed.astimezone(timezone(timedelta(hours=9))).replace(tzinfo=None)
        return parsed
    return None


def _hard_blocking_stages(source_quality: dict[str, Any]) -> set[str]:
    summary = (
        source_quality.get("summary")
        if isinstance(source_quality.get("summary"), dict)
        else {}
    )
    raw = (
        summary.get("hard_blocking_stages")
        or source_quality.get("hard_blocking_stages")
        or []
    )
    if not isinstance(raw, list):
        raw = [raw]
    return {str(item).strip() for item in raw if str(item).strip()}


def _source_quality_summary(target_date: str) -> dict[str, Any]:
    path = _source_quality_path(target_date)
    payload = _load_json(path)
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    status = str(
        payload.get("status") or ("missing" if not path.exists() else "loaded")
    )
    hard_gap_count = _safe_int(summary.get("hard_blocking_contract_gap_count"), 0)
    tuning_input_allowed = summary.get("tuning_input_allowed")
    if tuning_input_allowed is None:
        tuning_input_allowed = (
            status not in {"fail", "missing", "invalid"} and hard_gap_count <= 0
        )
    if status == "fail" or hard_gap_count > 0:
        tuning_input_allowed = False
    return {
        "artifact": str(path) if path.exists() else None,
        "status": status,
        "tuning_input_allowed": bool(tuning_input_allowed),
        "hard_blocking_contract_gap_count": hard_gap_count,
        "hard_blocking_excluded_row_count": _safe_int(
            summary.get("hard_blocking_excluded_row_count"), 0
        ),
        "raw_row_exclusion_applied": bool(
            summary.get("raw_row_exclusion_applied") or payload.get("raw_row_exclusion")
        ),
        "hard_blocking_stages": sorted(_hard_blocking_stages(payload)),
    }


def _iter_input_events(target_date: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    from src.engine.sniper_missed_entry_counterfactual import _load_entry_events
    native_plan_events = []
    clean_policy = clean_baseline_policy()
    source_quality = _source_quality_summary(target_date)
    hard_blocking_stages = set(source_quality.get("hard_blocking_stages") or [])
    events: list[dict[str, Any]] = []
    excluded_pre_baseline = 0
    source_paths = {
        "pipeline_events": _pipeline_events_path(target_date),
        "threshold_events": _threshold_events_path(target_date),
    }
    execution_projection = None
    for source_name, path in source_paths.items():
        actual = existing_or_gzip_path(path)
        if actual.exists() and actual.stat().st_size > 64 * 1024 * 1024:
            source_rows, execution_projection = _bounded_execution_projection(target_date)
        else:
            source_rows = _iter_entry_split_input_rows(path, hard_blocking_stages=hard_blocking_stages)
        for event in source_rows:
            if event.get("stage") == "entry_execution_sizing_plan":
                native_plan_events.extend(_load_entry_events(target_date, rows=[event]))
            fields = _event_fields(event)
            event_date = _event_date(fields) or target_date
            if not is_date_allowed(event_date, clean_policy):
                excluded_pre_baseline += 1
                continue
            stage = str(fields.get("stage") or fields.get("event") or "").strip()
            calibration_relevant = bool(
                stage.startswith("scalp_sim_")
                or stage in hard_blocking_stages
                or stage
                in {
                    "entry_execution_sizing_plan",
                    "entry_execution_sizing_plan_block",
                    "entry_quantity_leg_four_arm_evaluation",
                    "order_bundle_submitted",
                    "order_leg_sent",
                    "order_leg_fail",
                    "order_bundle_failed",
                }
            )
            if not calibration_relevant:
                continue
            fields = {
                key: value
                for key, value in fields.items()
                if key in CALIBRATION_EVENT_KEYS
            }
            fields["stock_code"] = event.get("stock_code") or fields.get("stock_code")
            fields["emitted_at"] = event.get("emitted_at") or fields.get("emitted_at")
            fields["source_name"] = source_name
            fields["source_date"] = event_date
            events.append(fields)
    return events, {
        "_entry_opportunity_plan_events": native_plan_events,
        "execution_projection": execution_projection,
        "source_paths": {
            name: _existing_jsonl_source(path) for name, path in source_paths.items()
        },
        "excluded_pre_baseline_count": excluded_pre_baseline,
        "clean_tuning_baseline": clean_policy,
    }


def _iter_entry_split_input_rows(path: Path, *, hard_blocking_stages: set[str]):
    actual_path = existing_or_gzip_path(path)
    if not actual_path.exists():
        return
    stage_tokens = {
        "entry_execution_sizing_plan",
        "entry_execution_sizing_plan_block",
        "entry_quantity_leg_four_arm_evaluation",
        "order_bundle_submitted",
        "order_leg_sent",
        "order_leg_fail",
        "order_bundle_failed",
        *hard_blocking_stages,
    }
    with open_text_auto(actual_path) as handle:
        for raw_line in handle:
            if "scalp_sim_" not in raw_line and not any(
                token in raw_line for token in stage_tokens
            ):
                continue
            try:
                payload = json.loads(raw_line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                yield payload


def _available_calibration_dates(target_date: str) -> list[str]:
    """Return clean-baseline source dates available through ``target_date``."""
    clean_policy = clean_baseline_policy()
    baseline_date = str(clean_policy.get("clean_tuning_baseline_date") or "2026-06-05")
    dates = {target_date}
    source_specs = (
        (DATA_DIR / "pipeline_events", "pipeline_events_"),
        (DATA_DIR / "threshold_cycle", "threshold_events_"),
        (DATA_DIR / "post_sell", "post_sell_evaluations_"),
        (DATA_DIR / "post_sell", "post_sell_candidates_"),
        (DATA_DIR / "post_sell", "sim_post_sell_evaluations_"),
    )
    for directory, prefix in source_specs:
        for pattern in (f"{prefix}*.jsonl", f"{prefix}*.jsonl.gz"):
            for path in directory.glob(pattern):
                name = path.name
                suffix = ".jsonl.gz" if name.endswith(".jsonl.gz") else ".jsonl"
                source_date = name[len(prefix) : -len(suffix)]
                if baseline_date <= source_date <= target_date:
                    dates.add(source_date)
    return sorted(
        source_date
        for source_date in dates
        if is_date_allowed(source_date, clean_policy)
    )


def _existing_jsonl_source(path: Path) -> str | None:
    if path.exists():
        return str(path)
    gzip_path = Path(f"{path}.gz")
    return str(gzip_path) if gzip_path.exists() else None


ENTRY_SPLIT_PROVENANCE_KEYS = (
    "entry_split_order_policy_applied",
    "entry_split_order_bucket",
    "entry_split_order_policy_version",
    "entry_split_order_policy_mode",
    "entry_split_order_policy_variant_id",
    "entry_split_order_variant_id",
    "entry_split_order_leg_count",
    "entry_split_order_price_offsets_ticks",
    "entry_split_order_qty_weight_min",
    "entry_split_order_qty_weight_max",
    "entry_split_order_runtime_default_policy_applied",
    "entry_split_order_operator_fallback_authorized",
)


def _source_quality_contract(summary: dict[str, Any]) -> dict[str, Any]:
    """Return only source-quality semantics consumed by this report.

    File mtimes are deliberately excluded: the final postclose audit may rewrite
    an equivalent artifact after this report without invalidating its cumulative
    state. A semantic contract change still invalidates the state.
    """

    return {
        "status": str(summary.get("status") or "missing"),
        "tuning_input_allowed": summary.get("tuning_input_allowed") is True,
        "hard_blocking_contract_gap_count": _safe_int(
            summary.get("hard_blocking_contract_gap_count"), 0
        ),
        "hard_blocking_excluded_row_count": _safe_int(
            summary.get("hard_blocking_excluded_row_count"), 0
        ),
        "raw_row_exclusion_applied": summary.get("raw_row_exclusion_applied") is True,
        "hard_blocking_stages": sorted(
            str(value)
            for value in (summary.get("hard_blocking_stages") or [])
            if str(value)
        ),
    }


def _source_quality_contract_sha256(summary: dict[str, Any]) -> str:
    encoded = json.dumps(
        _source_quality_contract(summary),
        sort_keys=True,
        ensure_ascii=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _source_quality_contract_bindings(
    source_dates: list[str],
) -> dict[str, dict[str, Any]]:
    bindings: dict[str, dict[str, Any]] = {}
    for source_date in sorted(set(source_dates)):
        summary = _source_quality_summary(source_date)
        bindings[source_date] = {
            "contract": _source_quality_contract(summary),
            "contract_sha256": _source_quality_contract_sha256(summary),
        }
    return bindings


def _identifier(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    try:
        return str(int(float(text)))
    except (TypeError, ValueError):
        return text


def _load_real_post_sell_rows(
    target_date: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    candidates = [
        {
            **_event_fields(item),
            "post_sell_evaluation_joined": False,
            "terminal_outcome_state": "pending_evaluation",
        }
        for item in iter_jsonl(_real_post_sell_candidate_path(target_date))
    ]
    evaluations = [
        {
            **_event_fields(item),
            "post_sell_evaluation_joined": True,
            # The evaluation publisher emits terminal post-sell outcomes; keep
            # that provenance explicit so a candidate-only record can never
            # enter a cost-adjusted EV sample.
            "terminal_outcome_state": "COMPLETED",
        }
        for item in iter_jsonl(_real_post_sell_path(target_date))
    ]
    merged: list[dict[str, Any]] = []
    by_post_sell_id: dict[str, int] = {}
    for row in candidates:
        post_sell_id = str(row.get("post_sell_id") or "").strip()
        if post_sell_id and post_sell_id in by_post_sell_id:
            merged[by_post_sell_id[post_sell_id]].update(row)
            continue
        if post_sell_id:
            by_post_sell_id[post_sell_id] = len(merged)
        merged.append(dict(row))
    matched_evaluation_count = 0
    for row in evaluations:
        post_sell_id = str(row.get("post_sell_id") or "").strip()
        if post_sell_id and post_sell_id in by_post_sell_id:
            merged[by_post_sell_id[post_sell_id]].update(row)
            matched_evaluation_count += 1
            continue
        if post_sell_id:
            by_post_sell_id[post_sell_id] = len(merged)
        merged.append(dict(row))
    for row in merged:
        row.setdefault("source_date", target_date)
    return merged, {
        "candidate_count": len(candidates),
        "evaluation_count": len(evaluations),
        "matched_evaluation_count": matched_evaluation_count,
        "pending_evaluation_count": max(0, len(candidates) - matched_evaluation_count),
        "merged_count": len(merged),
    }


def _extend_value_map(
    destination: dict[Any, list[float]], source: dict[Any, list[float]]
) -> None:
    for key, values in source.items():
        destination[key].extend(values)


def _merge_count_maps(
    prior: dict[str, dict[str, Any]],
    current: dict[str, dict[str, Any]],
) -> dict[str, dict[str, int]]:
    merged: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for source in (prior, current):
        for bucket, metrics in source.items():
            if not isinstance(metrics, dict):
                continue
            for metric, value in metrics.items():
                merged[str(bucket)][str(metric)] += _safe_int(value, 0)
    return {bucket: dict(metrics) for bucket, metrics in merged.items()}


def _latest_prior_cumulative_state(target_date: str) -> tuple[dict[str, Any], str]:
    policy = clean_baseline_policy()
    baseline_date = str(policy.get("clean_tuning_baseline_date") or "")
    for path in sorted(
        REPORT_DIR.glob(f"{REPORT_TYPE}_*.json"),
        reverse=True,
    ):
        source_date = path.stem.removeprefix(f"{REPORT_TYPE}_")
        if not source_date or source_date >= target_date:
            continue
        payload = _load_json(path)
        try:
            generation_binding_required = (
                date.fromisoformat(source_date) >= GENERATION_BINDING_REQUIRED_FROM_DATE
            )
        except ValueError:
            continue
        if generation_binding_required:
            prior_policy_path = (
                POLICY_DIR / f"entry_split_order_policy_{source_date}.json"
            )
            prior_policy = _load_json(prior_policy_path)
            generation_valid, _generation_reason = validate_report_policy_generation(
                payload, prior_policy
            )
            if not generation_valid:
                continue
        state = (
            payload.get("cumulative_state")
            if isinstance(payload.get("cumulative_state"), dict)
            else {}
        )
        if (
            payload.get("schema_version") == SCHEMA_VERSION
            and state.get("schema_version") == CUMULATIVE_STATE_SCHEMA_VERSION
            and state.get("window_policy")
            == "clean_baseline_cumulative_through_target_date"
            and str(state.get("through_date") or "") == source_date
            and str(state.get("clean_tuning_baseline_date") or "") == baseline_date
        ):
            source_dates = [
                str(value) for value in (state.get("source_dates") or []) if str(value)
            ]
            if not source_dates or max(source_dates) != source_date:
                continue
            expected_source_dates = [
                value
                for value in _available_calibration_dates(source_date)
                if _source_quality_summary(value).get("tuning_input_allowed") is True
            ]
            if sorted(set(source_dates)) != sorted(set(expected_source_dates)):
                # Do not perpetuate a cumulative state that skipped dates. An
                # older complete state can then replay the entire missing gap.
                continue
            bindings = (
                state.get("source_quality_contract_bindings")
                if isinstance(state.get("source_quality_contract_bindings"), dict)
                else {}
            )
            state_is_current = set(bindings) == set(source_dates)
            for state_source_date in source_dates:
                if not state_is_current:
                    break
                quality = _source_quality_summary(state_source_date)
                if quality.get("tuning_input_allowed") is not True:
                    state_is_current = False
                    break
                binding = bindings.get(state_source_date)
                if not isinstance(binding, dict):
                    state_is_current = False
                    break
                stored_contract = binding.get("contract")
                stored_hash = str(binding.get("contract_sha256") or "")
                if (
                    not isinstance(stored_contract, dict)
                    or stored_hash != _source_quality_contract_sha256(stored_contract)
                    or stored_hash != _source_quality_contract_sha256(quality)
                ):
                    state_is_current = False
                    break
            if not state_is_current:
                continue
            return state, str(path)
    return {}, ""


def _deserialize_value_map(payload: Any) -> dict[str, list[float]]:
    result: dict[str, list[float]] = defaultdict(list)
    if not isinstance(payload, dict):
        return result
    for key, values in payload.items():
        if isinstance(values, list):
            result[str(key)].extend(
                float(value) for value in values if _safe_float(value, None) is not None
            )
    return result


def _deserialize_variant_value_map(
    payload: Any,
) -> dict[tuple[str, str], list[float]]:
    result: dict[tuple[str, str], list[float]] = defaultdict(list)
    if not isinstance(payload, dict):
        return result
    for bucket, variants in payload.items():
        if not isinstance(variants, dict):
            continue
        for variant_id, values in variants.items():
            if isinstance(values, list):
                result[(str(bucket), str(variant_id))].extend(
                    float(value)
                    for value in values
                    if _safe_float(value, None) is not None
                )
    return result


def _serialize_variant_value_map(
    values: dict[tuple[str, str], list[float]],
) -> dict[str, dict[str, list[float]]]:
    payload: dict[str, dict[str, list[float]]] = defaultdict(dict)
    for (bucket, variant_id), samples in values.items():
        payload[str(bucket)][str(variant_id)] = [float(value) for value in samples]
    return {bucket: dict(variants) for bucket, variants in payload.items()}


def _source_quality_filtered_events(
    events: list[dict[str, Any]],
    source_quality_by_date: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], int]:
    included: list[dict[str, Any]] = []
    excluded = 0
    for fields in events:
        source_date = str(fields.get("source_date") or _event_date(fields) or "")[:10]
        quality = source_quality_by_date.get(
            source_date, {"tuning_input_allowed": False}
        )
        stage = str(fields.get("stage") or fields.get("event") or "").strip()
        if quality.get("tuning_input_allowed") is not True or stage in set(
            quality.get("hard_blocking_stages") or []
        ):
            excluded += 1
            continue
        included.append(fields)
    return included, excluded


def _enrich_real_post_sell_provenance(
    rows: list[dict[str, Any]], events: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], int]:
    provenance_by_recommendation: dict[tuple[str, str], dict[str, Any]] = {}
    for fields in events:
        if (
            str(fields.get("stage") or fields.get("event") or "").strip()
            != "order_bundle_submitted"
        ):
            continue
        if not (
            _safe_bool(fields.get("entry_split_order_policy_applied"))
            or str(fields.get("entry_split_order_policy_variant_id") or "").strip()
            or str(fields.get("entry_split_order_variant_id") or "").strip()
            or str(fields.get("entry_split_order_policy_mode") or "").strip()
        ):
            continue
        provenance = {
            key: fields.get(key)
            for key in ENTRY_SPLIT_PROVENANCE_KEYS
            if fields.get(key) not in (None, "", "-", "None", "none", "null")
        }
        if not provenance:
            continue
        recommendation_id = _identifier(
            fields.get("recommendation_id") or fields.get("record_id")
        )
        if recommendation_id:
            provenance_by_recommendation[
                (_provenance_date(fields), recommendation_id)
            ] = provenance

    enriched: list[dict[str, Any]] = []
    reconstructed_count = 0
    for row in rows:
        next_row = dict(row)
        recommendation_id = _identifier(
            next_row.get("recommendation_id") or next_row.get("record_id")
        )
        provenance = provenance_by_recommendation.get(
            (_provenance_date(next_row), recommendation_id)
        )
        if provenance:
            filled_any = False
            for key, value in provenance.items():
                if next_row.get(key) in (None, "", "-", "None", "none", "null"):
                    next_row[key] = value
                    filled_any = True
            if filled_any:
                reconstructed_count += 1
        enriched.append(next_row)
    return enriched, reconstructed_count


def _provenance_date(fields: dict[str, Any]) -> str:
    return str(
        fields.get("source_date")
        or _event_date(fields)
        or fields.get("entry_date")
        or fields.get("signal_date")
        or fields.get("sell_date")
        or ""
    )[:10]


def _load_sim_ev_values(target_date: str) -> dict[str, list[float]]:
    if not is_date_allowed(target_date, clean_baseline_policy()):
        return {}
    values: dict[str, list[float]] = defaultdict(list)
    path = _sim_post_sell_path(target_date)
    for event in iter_jsonl(path):
        fields = _event_fields(event)
        event_date = _event_date(fields) or str(fields.get("entry_date") or "")[:10]
        if event_date and event_date != target_date:
            continue
        profit = _safe_float(
            (
                fields.get("profit_rate")
                if fields.get("profit_rate") is not None
                else (
                    fields.get("sim_profit_rate")
                    if fields.get("sim_profit_rate") is not None
                    else fields.get("post_sell_profit_rate")
                )
            ),
            None,
        )
        if profit is None:
            continue
        values[_context_bucket(fields)].append(float(profit))
    return values


def _load_real_ev_values(
    target_date: str, rows: list[dict[str, Any]] | None = None
) -> dict[str, list[float]]:
    if not is_date_allowed(target_date, clean_baseline_policy()):
        return {}
    values: dict[str, list[float]] = defaultdict(list)
    source_rows = (
        rows if rows is not None else _load_real_post_sell_rows(target_date)[0]
    )
    for fields in source_rows:
        event_date = (
            _event_date(fields)
            or str(fields.get("entry_date") or fields.get("sell_date") or "")[:10]
        )
        if event_date and event_date != target_date:
            continue
        if not _safe_bool(fields.get("post_sell_evaluation_joined")):
            continue
        if not _safe_bool(fields.get("actual_order_submitted")):
            continue
        profit = _safe_float(
            (
                fields.get("profit_rate")
                if fields.get("profit_rate") is not None
                else fields.get("post_sell_profit_rate")
            ),
            None,
        )
        if profit is None:
            continue
        values[_context_bucket(fields)].append(float(profit))
    return values


def _split_variant_id_from_fields(fields: dict[str, Any]) -> str:
    explicit_parent = str(
        fields.get("entry_split_order_policy_variant_id") or ""
    ).strip()
    if explicit_parent:
        return explicit_parent
    historical_child = str(fields.get("entry_split_order_variant_id") or "").strip()
    if historical_child:
        runtime_suffix_markers = (
            "__qty_clipped_legs",
            "__runtime_first_weight_",
            f"__{PROBE_VARIANT_SUFFIX}",
        )
        suffix_offsets = [
            historical_child.find(marker)
            for marker in runtime_suffix_markers
            if marker in historical_child
        ]
        return (
            historical_child[: min(suffix_offsets)]
            if suffix_offsets
            else historical_child
        )
    if not (
        _safe_bool(fields.get("entry_split_order_policy_applied"))
        or str(fields.get("entry_split_order_policy_mode") or "").strip()
    ):
        return ""
    mode = (
        str(fields.get("entry_split_order_policy_mode") or "").strip() or "unknown_mode"
    )
    leg_count = _safe_int(fields.get("entry_split_order_leg_count"), 0)
    offsets = (
        str(fields.get("entry_split_order_price_offsets_ticks") or "").strip()
        or "unknown_offsets"
    )
    weight = (
        str(fields.get("entry_split_order_qty_weight_min") or "").strip()
        or "unknown_weight"
    )
    return f"{mode}:legs{leg_count}:offsets{offsets}:w{weight}"


def _split_child_variant_id_from_fields(fields: dict[str, Any]) -> str:
    return str(fields.get("entry_split_order_variant_id") or "").strip()


def _load_real_split_variant_ev_values(
    target_date: str,
    rows: list[dict[str, Any]] | None = None,
    *,
    child_variant: bool = False,
) -> dict[tuple[str, str], list[float]]:
    if not is_date_allowed(target_date, clean_baseline_policy()):
        return {}
    values: dict[tuple[str, str], list[float]] = defaultdict(list)
    source_rows = (
        rows if rows is not None else _load_real_post_sell_rows(target_date)[0]
    )
    for fields in source_rows:
        event_date = (
            _event_date(fields)
            or str(fields.get("entry_date") or fields.get("sell_date") or "")[:10]
        )
        if event_date and event_date != target_date:
            continue
        if not _safe_bool(fields.get("post_sell_evaluation_joined")):
            continue
        if not _safe_bool(fields.get("actual_order_submitted")):
            continue
        variant_id = (
            _split_child_variant_id_from_fields(fields)
            if child_variant
            else _split_variant_id_from_fields(fields)
        )
        if not variant_id:
            continue
        profit = _safe_float(
            (
                fields.get("profit_rate")
                if fields.get("profit_rate") is not None
                else fields.get("post_sell_profit_rate")
            ),
            None,
        )
        if profit is None:
            continue
        values[(_context_bucket(fields), variant_id)].append(float(profit))
    return values


def _context_bucket(fields: dict[str, Any]) -> str:
    explicit_bucket = str(fields.get("entry_split_order_bucket") or "").strip()
    if explicit_bucket in {
        "guarded_or_stale",
        "urgent_tight_spread",
        "passive_wide_or_weak",
        "balanced_normal",
    }:
        return explicit_bucket
    spread_bps = _safe_float(fields.get("spread_bps"), None)
    if spread_bps is None:
        spread_ratio = _safe_float(fields.get("spread_ratio"), None)
        spread_bps = (
            float(spread_ratio or 0.0) * 10000.0 if spread_ratio is not None else 0.0
        )
    buy_pressure = (
        _safe_float(
            fields.get("buy_pressure_10t") or fields.get("tick_buy_pressure_10t"), 0.0
        )
        or 0.0
    )
    micro_state = str(
        fields.get("orderbook_micro_state") or fields.get("micro_state") or ""
    ).lower()
    latency_state = str(fields.get("latency_state") or "").upper()
    quote_stale = _safe_bool(fields.get("quote_stale")) or _safe_bool(
        fields.get("stale_quote_submit_block")
    )
    if quote_stale or latency_state == "DANGER":
        return "guarded_or_stale"
    if spread_bps <= 12.0 and buy_pressure >= 60.0 and "weak" not in micro_state:
        return "urgent_tight_spread"
    if spread_bps >= 35.0 or buy_pressure <= 45.0 or "weak" in micro_state:
        return "passive_wide_or_weak"
    return "balanced_normal"


def _template_for_bucket(bucket: str) -> dict[str, Any]:
    templates = {
        "urgent_tight_spread": {
            "leg_count": 2,
            "price_offsets_ticks": [0, 1],
            "price_offsets_pct": [0.0, 0.3],
            "qty_weight_min": 0.65,
            "qty_weight_max": 0.85,
            "urgency_score": 0.82,
            "passive_edge_score": 0.28,
            "price_candidates": ["resolved_order_price", "best_bid", "bid-1tick"],
        },
        "balanced_normal": {
            "leg_count": 2,
            "price_offsets_ticks": [0, 1],
            "price_offsets_pct": [0.0, 0.3],
            "qty_weight_min": 0.55,
            "qty_weight_max": 0.70,
            "urgency_score": 0.55,
            "passive_edge_score": 0.52,
            "price_candidates": [
                "resolved_order_price",
                "best_bid",
                "bid-1tick",
                "reference_target",
                "AI_candidate",
            ],
        },
        "passive_wide_or_weak": {
            "leg_count": 3,
            "price_offsets_ticks": [0, 1, 2],
            "price_offsets_pct": [0.0, 0.3, 0.8],
            "qty_weight_min": 0.30,
            "qty_weight_max": 0.50,
            "urgency_score": 0.30,
            "passive_edge_score": 0.78,
            "price_candidates": [
                "best_bid",
                "bid-1tick",
                "bid-2tick",
                "reference_target",
            ],
        },
        "guarded_or_stale": {
            "leg_count": 1,
            "price_offsets_ticks": [0],
            "price_offsets_pct": [0.0],
            "qty_weight_min": 1.0,
            "qty_weight_max": 1.0,
            "urgency_score": 0.0,
            "passive_edge_score": 0.0,
            "price_candidates": ["resolved_order_price"],
        },
    }
    return dict(templates.get(bucket) or templates["balanced_normal"])


def _bounded_equal_split_template(bucket: str) -> dict[str, Any]:
    template = _template_for_bucket(bucket)
    template.update(
        {
            "leg_count": 2,
            "price_offsets_ticks": [0, 1],
            "price_offsets_pct": [0.0, 0.3],
            "qty_weight_min": 0.5,
            "qty_weight_max": 0.5,
            "price_candidates": ["resolved_order_price", "best_bid", "bid-1tick"],
            "split_variant_id": BASELINE_SPLIT_VARIANT_ID,
        }
    )
    return template


def _post_submit_tick_band_template(
    bucket: str, tick_band: dict[str, Any]
) -> dict[str, Any]:
    template = _bounded_equal_split_template(bucket)
    sample = _safe_int(tick_band.get("sample_count"), 0)
    p75 = _safe_float(tick_band.get("p75_down_ticks"), 0.0) or 0.0
    touch2 = _safe_float(tick_band.get("touch_2tick_rate"), 0.0) or 0.0
    if sample >= POST_SUBMIT_TICK_BAND_FLOOR_REAL and p75 >= 2.0 and touch2 >= 50.0:
        template.update(
            {
                "leg_count": 3,
                "price_offsets_ticks": [0, 1, 2],
                "price_offsets_pct": [0.0, 0.3, 0.8],
                "qty_weight_min": 0.34,
                "qty_weight_max": 0.34,
                "price_candidates": [
                    "resolved_order_price",
                    "best_bid",
                    "bid-1tick",
                    "bid-2tick",
                ],
                "split_variant_id": PCT_BAND_3LEG_VARIANT_ID,
            }
        )
    return template


def _child_shape_seed_template(
    bucket: str, child_variant_id: str
) -> dict[str, Any] | None:
    """Return a policy only when the observed child maps to one exact runtime shape.

    Parent variants can contain materially different runtime children (quantity
    clipping, passive-bias weight and probe state).  A positive child must not
    silently authorize the other shapes under the same parent.
    """

    parent_id = RUNTIME_FALLBACK_THREE_LEG_VARIANT_ID
    expected_child = (
        f"{parent_id}__qty_clipped_legs2__runtime_first_weight_20"
        f"__{PROBE_VARIANT_SUFFIX}"
    )
    if bucket != "passive_wide_or_weak" or child_variant_id != expected_child:
        return None
    template = _template_for_bucket(bucket)
    template.update(
        {
            "leg_count": 3,
            "price_offsets_ticks": [0, 1, 2],
            "price_offsets_pct": [0.0, 0.3, 0.8],
            "qty_weight_min": 0.5,
            "qty_weight_max": 0.5,
            "price_candidates": [
                "resolved_order_price",
                "best_bid",
                "bid-1tick",
                "bid-2tick",
            ],
            "split_variant_id": parent_id,
            "runtime_shape_gate": {
                "schema": "entry_split_runtime_shape_gate_v1",
                "required_policy_split_variant_id": parent_id,
                "required_requested_legs": 3,
                "required_desired_legs": 2,
                "required_runtime_first_weight": 0.2,
                "require_runtime_weight_adjusted": True,
                "require_market_first_leg_disabled": True,
                "require_probe_first_enabled": True,
                "require_probe_first_eligible": True,
                "observed_child_variant_id": child_variant_id,
            },
        }
    )
    return template


def _child_shape_seed_evidence(
    bucket: str,
    values_by_child_variant: dict[tuple[str, str], list[float]],
) -> dict[str, Any] | None:
    """Pick the highest-EV exact child that has bounded seed evidence.

    This intentionally supports only known, reproducible runtime shapes.  New
    child suffixes remain observation-only until a separate contract maps their
    fields to a fail-closed runtime gate.
    """

    eligible: list[dict[str, Any]] = []
    for (observed_bucket, child_variant_id), values in values_by_child_variant.items():
        if observed_bucket != bucket or not values:
            continue
        template = _child_shape_seed_template(bucket, child_variant_id)
        if template is None:
            continue
        sample_count = len(values)
        downside_p10 = sorted(values)[max(0, int(sample_count * 0.10) - 1)]
        equal_weight_ev = round(mean(values), 4)
        if (
            sample_count < CHILD_SHAPE_SEED_OUTCOME_FLOOR_REAL
            or equal_weight_ev < CHILD_SHAPE_SEED_MIN_EV_PCT
            or downside_p10 <= CHILD_SHAPE_SEED_MAX_DOWNSIDE_P10_PCT
        ):
            continue
        eligible.append(
            {
                "child_variant_id": child_variant_id,
                "values": list(values),
                "sample_count": sample_count,
                "equal_weight_avg_profit_pct": equal_weight_ev,
                "downside_p10_profit_rate": round(downside_p10, 4),
                "template": template,
            }
        )
    return max(
        eligible,
        key=lambda item: (
            float(item["equal_weight_avg_profit_pct"]),
            int(item["sample_count"]),
            str(item["child_variant_id"]),
        ),
        default=None,
    )


def _percentile(values: list[int], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(int(value) for value in values)
    if len(ordered) == 1:
        return float(ordered[0])
    rank = (len(ordered) - 1) * max(0.0, min(100.0, float(pct))) / 100.0
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    if lower == upper:
        return float(ordered[lower])
    weight = rank - lower
    return (ordered[lower] * (1.0 - weight)) + (ordered[upper] * weight)


def _post_submit_observed_prices(fields: dict[str, Any]) -> list[int]:
    prices: list[int] = []
    for key in (
        "current_price_observed",
        "current_price",
        "latest_price",
        "holding_ws_recovered_curr",
        "curr_price",
        "mark_price_at_submit",
        "submitted_mark_price",
    ):
        value = _safe_int(fields.get(key), 0)
        if value > 0:
            prices.append(value)
    return prices


def _submit_order_price(fields: dict[str, Any]) -> int:
    return _safe_int(
        fields.get("order_price")
        or fields.get("submitted_order_price")
        or fields.get("resolved_order_price")
        or fields.get("price")
        or fields.get("submitted_price"),
        0,
    )


def _summarize_post_submit_low_tick_bands(
    down_ticks_by_bucket: dict[str, list[int]],
    down_pct_by_bucket: dict[str, list[float]],
    *,
    window_minutes: int,
) -> dict[str, dict[str, Any]]:
    """Preserve the established tick-band report schema for streamed inputs."""

    result: dict[str, dict[str, Any]] = {}
    for bucket, values in down_ticks_by_bucket.items():
        sample = len(values)
        pct_values = down_pct_by_bucket.get(bucket) or []
        result[bucket] = {
            "sample_count": sample,
            "window_minutes": int(window_minutes),
            "source": "runtime_post_submit_observed_prices",
            "p50_down_ticks": round(_percentile(values, 50), 3),
            "p75_down_ticks": round(_percentile(values, 75), 3),
            "p90_down_ticks": round(_percentile(values, 90), 3),
            "max_down_ticks": max(values) if values else 0,
            "touch_1tick_rate": _pct(sum(1 for value in values if value >= 1), sample),
            "touch_2tick_rate": _pct(sum(1 for value in values if value >= 2), sample),
            "p50_down_pct": (
                round(
                    _percentile([int(value * 10000) for value in pct_values], 50)
                    / 10000.0,
                    4,
                )
                if pct_values
                else 0.0
            ),
            "p75_down_pct": (
                round(
                    _percentile([int(value * 10000) for value in pct_values], 75)
                    / 10000.0,
                    4,
                )
                if pct_values
                else 0.0
            ),
            "p90_down_pct": (
                round(
                    _percentile([int(value * 10000) for value in pct_values], 90)
                    / 10000.0,
                    4,
                )
                if pct_values
                else 0.0
            ),
            "touch_0_3pct_rate": _pct(
                sum(1 for value in pct_values if value >= 0.3), sample
            ),
            "touch_0_5pct_rate": _pct(
                sum(1 for value in pct_values if value >= 0.5), sample
            ),
            "touch_0_8pct_rate": _pct(
                sum(1 for value in pct_values if value >= 0.8), sample
            ),
            "touch_1_0pct_rate": _pct(
                sum(1 for value in pct_values if value >= 1.0), sample
            ),
            "touch_1_5pct_rate": _pct(
                sum(1 for value in pct_values if value >= 1.5), sample
            ),
            "no_pullback_rate": _pct(sum(1 for value in values if value <= 0), sample),
        }
    return result


def _raw_record_id(raw_line: str) -> str:
    match = RAW_RECORD_ID_PATTERN.search(raw_line)
    if match is None:
        return ""
    raw_value = match.group(1) if match.group(1) is not None else match.group(2)
    return _identifier(raw_value)


def _build_post_submit_low_tick_bands_from_sources(
    target_date: str,
    submit_events: list[dict[str, Any]],
    *,
    source_quality: dict[str, Any] | None = None,
    window_minutes: int = POST_SUBMIT_LOW_WINDOW_MINUTES,
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """Join submit lows without retaining every intraday price event in RAM."""

    blocked_stages = set((source_quality or {}).get("hard_blocking_stages") or [])
    submissions: list[dict[str, Any]] = []
    submissions_by_record_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for fields in submit_events:
        stage = str(fields.get("stage") or fields.get("event") or "").strip()
        if stage != "order_bundle_submitted" or stage in blocked_stages:
            continue
        if not _safe_bool(fields.get("actual_order_submitted")):
            continue
        if not _has_split_eligible_quantity_or_provenance(fields):
            continue
        record_id = _identifier(fields.get("record_id"))
        code = str(fields.get("stock_code") or "").strip()
        submit_dt = _event_dt(fields)
        submit_price = _submit_order_price(fields)
        if not record_id or not code or submit_dt is None or submit_price <= 0:
            continue
        observed_prices = _post_submit_observed_prices(fields)
        submission = {
            "record_id": record_id,
            "stock_code": code,
            "submit_dt": submit_dt,
            "submit_price": submit_price,
            "context_bucket": _context_bucket(fields),
            "observed_low": min(observed_prices) if observed_prices else None,
        }
        submissions.append(submission)
        submissions_by_record_id[record_id].append(submission)

    raw_line_count = 0
    price_token_line_count = 0
    record_candidate_line_count = 0
    parsed_observation_count = 0
    matched_observation_count = 0
    if submissions_by_record_id:
        source_paths = (
            _pipeline_events_path(target_date),
            _threshold_events_path(target_date),
        )
        for source_path in source_paths:
            actual_path = existing_or_gzip_path(source_path)
            if not actual_path.exists():
                continue
            with open_text_auto(actual_path) as handle:
                for raw_line in handle:
                    raw_line_count += 1
                    if not any(token in raw_line for token in POST_SUBMIT_PRICE_TOKENS):
                        continue
                    price_token_line_count += 1
                    record_id = _raw_record_id(raw_line)
                    if record_id not in submissions_by_record_id:
                        continue
                    record_candidate_line_count += 1
                    try:
                        payload = json.loads(raw_line)
                    except json.JSONDecodeError:
                        continue
                    if not isinstance(payload, dict):
                        continue
                    fields = _event_fields(payload)
                    parsed_observation_count += 1
                    stage = str(
                        fields.get("stage") or fields.get("event") or ""
                    ).strip()
                    if stage in blocked_stages:
                        continue
                    event_date = _event_date(fields) or target_date
                    if event_date != target_date:
                        continue
                    code = str(fields.get("stock_code") or "").strip()
                    observed_dt = _event_dt(fields)
                    observed_prices = _post_submit_observed_prices(fields)
                    if not code or observed_dt is None or not observed_prices:
                        continue
                    for submission in submissions_by_record_id[record_id]:
                        if code != submission["stock_code"]:
                            continue
                        submit_dt = submission["submit_dt"]
                        if not (
                            submit_dt
                            <= observed_dt
                            <= submit_dt + timedelta(minutes=window_minutes)
                        ):
                            continue
                        observed_low = min(observed_prices)
                        current_low = submission.get("observed_low")
                        submission["observed_low"] = (
                            observed_low
                            if current_low is None
                            else min(int(current_low), observed_low)
                        )
                        matched_observation_count += 1

    down_ticks_by_bucket: dict[str, list[int]] = defaultdict(list)
    down_pct_by_bucket: dict[str, list[float]] = defaultdict(list)
    for submission in submissions:
        low_price = _safe_int(submission.get("observed_low"), 0)
        submit_price = _safe_int(submission.get("submit_price"), 0)
        if low_price <= 0 or submit_price <= 0:
            continue
        tick = max(1, int(get_tick_size(submit_price) or 1))
        down_ticks = max(0, int(math.ceil((submit_price - low_price) / tick)))
        down_pct = max(0.0, ((submit_price - low_price) / submit_price) * 100.0)
        bucket = str(submission.get("context_bucket") or "balanced_normal")
        down_ticks_by_bucket[bucket].append(down_ticks)
        down_pct_by_bucket[bucket].append(down_pct)

    result = _summarize_post_submit_low_tick_bands(
        down_ticks_by_bucket,
        down_pct_by_bucket,
        window_minutes=window_minutes,
    )
    return result, {
        "mode": "record_id_prefiltered_streaming_v1",
        "submit_count": len(submissions),
        "raw_line_count": raw_line_count,
        "price_token_line_count": price_token_line_count,
        "record_candidate_line_count": record_candidate_line_count,
        "parsed_observation_count": parsed_observation_count,
        "matched_observation_count": matched_observation_count,
        "retained_price_event_count": 0,
    }


def _is_real_submit_event(fields: dict[str, Any]) -> bool:
    stage = str(fields.get("stage") or fields.get("event") or "").strip()
    return bool(
        _safe_bool(fields.get("actual_order_submitted"))
        and stage in {"order_bundle_submitted", "order_leg_sent"}
    )


def _has_split_eligible_quantity_or_provenance(fields: dict[str, Any]) -> bool:
    if (
        _safe_bool(fields.get("entry_split_order_policy_applied"))
        or str(fields.get("entry_split_order_policy_variant_id") or "").strip()
        or str(fields.get("entry_split_order_variant_id") or "").strip()
    ):
        return True
    return any(
        _safe_int(fields.get(key), 0) > 1
        for key in (
            "entry_split_order_original_qty",
            "requested_qty",
            "submitted_qty",
        )
    )


def _is_split_eligible_real_event(fields: dict[str, Any]) -> bool:
    return _is_real_submit_event(fields) and _has_split_eligible_quantity_or_provenance(
        fields
    )


def _is_sim_event(fields: dict[str, Any]) -> bool:
    stage = str(fields.get("stage") or fields.get("event") or "").strip()
    if str(stage).startswith("scalp_sim_"):
        return True
    decision_authority = str(fields.get("decision_authority") or "").strip()
    if decision_authority in {"sim_observation_only", "swing_sim_exploration_only"}:
        return True
    if _safe_bool(fields.get("broker_order_forbidden")) and (
        "sim" in stage or "probe" in stage
    ):
        return True
    return False


def _quality_counts(
    events: list[dict[str, Any]],
    source_quality: dict[str, Any],
    *,
    source_quality_by_date: dict[str, dict[str, Any]] | None = None,
) -> tuple[dict[str, dict[str, Any]], int]:
    sample_keys: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    excluded_source_quality = 0
    for event_index, fields in enumerate(events):
        stage = str(fields.get("stage") or fields.get("event") or "").strip()
        row_source_quality = source_quality
        source_date = str(fields.get("source_date") or _event_date(fields) or "")[:10]
        if source_quality_by_date and source_date:
            row_source_quality = source_quality_by_date.get(
                source_date, {"tuning_input_allowed": False}
            )
        if row_source_quality.get("tuning_input_allowed") is not True:
            excluded_source_quality += 1
            continue
        blocked_stages = set(row_source_quality.get("hard_blocking_stages") or [])
        if stage in blocked_stages:
            excluded_source_quality += 1
            continue
        bucket = _context_bucket(fields)
        stable_id = _identifier(
            fields.get("entry_split_order_bundle_id")
            or fields.get("order_bundle_id")
            or fields.get("bundle_id")
            or fields.get("recommendation_id")
            or fields.get("record_id")
            or fields.get("order_id")
        )
        stock_code = str(fields.get("stock_code") or fields.get("code") or "").strip()
        execution_key = (
            f"{source_date}:{stable_id}:{stock_code}"
            if stable_id
            else f"{source_date}:{stage}:row:{event_index}"
        )
        row = sample_keys[bucket]
        atomic_plan_id = _identifier(fields.get("entry_execution_sizing_plan_id"))
        if stage in {
            "entry_execution_sizing_plan",
            "entry_execution_sizing_plan_block",
        }:
            atomic_key = (
                f"{source_date}:{atomic_plan_id}"
                if atomic_plan_id
                else f"{source_date}:{stage}:row:{event_index}"
            )
            row["atomic_plan_observed_count"].add(atomic_key)
            if _safe_bool(fields.get("entry_execution_sizing_valid")):
                row["atomic_plan_valid_count"].add(atomic_key)
            else:
                row["atomic_plan_invalid_count"].add(atomic_key)
        if _is_real_submit_event(fields):
            row["real_observed_entry_count"].add(execution_key)
            if atomic_plan_id:
                row["atomic_plan_submit_count"].add(execution_key)
            else:
                row["atomic_plan_missing_submit_count"].add(execution_key)
            if _is_split_eligible_real_event(fields):
                row["real_sample_count"].add(execution_key)
                if stage == "order_leg_sent" or _safe_bool(
                    fields.get("broker_order_submitted")
                ):
                    row["real_submitted_count"].add(execution_key)
                if (
                    str(fields.get("fill_status") or "").upper() == "PARTIAL"
                    or _safe_int(fields.get("filled_qty"), 0) > 0
                ):
                    row["partial_fill_count"].add(execution_key)
                if _safe_bool(fields.get("late_fill")) or _safe_bool(
                    fields.get("late_fill_detected")
                ):
                    row["late_fill_count"].add(execution_key)
        if (
            _safe_bool(fields.get("actual_order_submitted"))
            and stage
            in {
                "order_leg_fail",
                "order_bundle_failed",
            }
            and _has_split_eligible_quantity_or_provenance(fields)
        ):
            row["cancel_or_fail_count"].add(execution_key)
        if _is_sim_event(fields):
            row["sim_sample_count"].add(execution_key)
            if stage in {
                "scalp_sim_buy_order_assumed_filled",
                "scalp_sim_sell_order_assumed_filled",
            }:
                row["sim_fill_count"].add(execution_key)
            if stage in {"scalp_sim_entry_expired", "scalp_sim_entry_unpriced"}:
                row["cancel_or_fail_count"].add(execution_key)
    return (
        {
            bucket: {metric: len(keys) for metric, keys in metrics.items()}
            for bucket, metrics in sample_keys.items()
        },
        excluded_source_quality,
    )


def _pct(count: int, total: int) -> float:
    return round((count / total) * 100.0, 4) if total > 0 else 0.0


def _build_candidate_grid(
    buckets: dict[str, dict[str, Any]],
    sim_ev_values: dict[str, list[float]],
    real_ev_values: dict[str, list[float]],
    real_split_variant_ev_values: dict[tuple[str, str], list[float]] | None = None,
    real_split_child_variant_ev_values: (
        dict[tuple[str, str], list[float]] | None
    ) = None,
    post_submit_low_tick_bands: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    grid: list[dict[str, Any]] = []
    real_split_variant_ev_values = real_split_variant_ev_values or {}
    real_split_child_variant_ev_values = real_split_child_variant_ev_values or {}
    post_submit_low_tick_bands = post_submit_low_tick_bands or {}
    split_variant_buckets = {
        bucket for bucket, _variant_id in real_split_variant_ev_values
    } | {bucket for bucket, _variant_id in real_split_child_variant_ev_values}
    for bucket in sorted(
        set(buckets)
        | set(sim_ev_values)
        | set(real_ev_values)
        | split_variant_buckets
        | set(post_submit_low_tick_bands)
    ):
        counts = buckets.get(bucket) or {}
        template = _template_for_bucket(bucket)
        tick_band = post_submit_low_tick_bands.get(bucket) or {}
        event_real_count = _safe_int(counts.get("real_sample_count"), 0)
        sim_count = _safe_int(counts.get("sim_sample_count"), 0)
        real_ev_list = real_ev_values.get(bucket) or []
        sim_ev_list = sim_ev_values.get(bucket) or []
        real_bucket_outcome_count = len(real_ev_list)
        real_bucket_ev = round(mean(real_ev_list), 4) if real_ev_list else None
        sim_ev = round(mean(sim_ev_list), 4) if sim_ev_list else None
        child_shape_seed = _child_shape_seed_evidence(
            bucket, real_split_child_variant_ev_values
        )
        split_variant_id = ""
        if child_shape_seed is not None:
            template = dict(child_shape_seed["template"])
            split_variant_id = str(template["split_variant_id"])
        elif bucket != "guarded_or_stale":
            template = _post_submit_tick_band_template(bucket, tick_band)
            split_variant_id = BASELINE_SPLIT_VARIANT_ID
            if template.get("split_variant_id"):
                split_variant_id = str(
                    template.get("split_variant_id") or BASELINE_SPLIT_VARIANT_ID
                )
        split_variant_ev_list = (
            list(child_shape_seed["values"])
            if child_shape_seed is not None
            else (
                real_split_variant_ev_values.get((bucket, split_variant_id))
                if split_variant_id
                else []
            )
        )
        observed_split_variants = [
            {
                "split_variant_id": observed_variant_id,
                "sample_count": len(observed_values),
                "equal_weight_avg_profit_pct": round(mean(observed_values), 4),
            }
            for (observed_bucket, observed_variant_id), observed_values in sorted(
                real_split_variant_ev_values.items()
            )
            if observed_bucket == bucket and observed_values
        ]
        split_variant_judgment_quality = []
        for item in observed_split_variants:
            variant_id = str(item.get("split_variant_id") or "")
            variant_values = (
                real_split_variant_ev_values.get((bucket, variant_id)) or []
            )
            variant_sample_count = len(variant_values)
            variant_downside_p10 = (
                sorted(variant_values)[max(0, int(len(variant_values) * 0.10) - 1)]
                if variant_values
                else None
            )
            variant_ev = round(mean(variant_values), 4) if variant_values else None
            split_variant_judgment_quality.append(
                {
                    **item,
                    "learning_sample_floor": CUMULATIVE_LEARNING_SAMPLE_FLOOR,
                    "learning_updated": (
                        variant_sample_count >= CUMULATIVE_LEARNING_SAMPLE_FLOOR
                    ),
                    "runtime_promotion_sample_floor": (
                        SPLIT_VARIANT_OUTCOME_FLOOR_REAL
                    ),
                    "runtime_promotion_sample_ready": (
                        variant_sample_count >= SPLIT_VARIANT_OUTCOME_FLOOR_REAL
                    ),
                    "downside_p10_profit_rate": (
                        round(variant_downside_p10, 4)
                        if variant_downside_p10 is not None
                        else None
                    ),
                    "runtime_evidence_ready": bool(
                        bucket != "guarded_or_stale"
                        and variant_sample_count >= SPLIT_VARIANT_OUTCOME_FLOOR_REAL
                        and variant_ev is not None
                        and variant_ev >= RUNTIME_PROMOTION_MIN_COST_ADJUSTED_EV_PCT
                        and variant_downside_p10 is not None
                        and variant_downside_p10 > -2.0
                    ),
                    "runtime_promotion_requires_shape_provenance": True,
                }
            )
        observed_split_outcome_count = sum(
            _safe_int(item.get("sample_count"), 0) for item in observed_split_variants
        )
        real_count = max(event_real_count, observed_split_outcome_count)
        total = max(1, real_count + sim_count)
        split_variant_outcome_count = len(split_variant_ev_list or [])
        split_variant_ev = (
            round(mean(split_variant_ev_list), 4) if split_variant_ev_list else None
        )
        primary_ev = split_variant_ev if split_variant_ev is not None else None
        cumulative_learning_sample_count = observed_split_outcome_count
        cumulative_learning_updated = (
            cumulative_learning_sample_count >= CUMULATIVE_LEARNING_SAMPLE_FLOOR
        )
        notional_ev = primary_ev
        partial_fill_rate = _pct(
            _safe_int(counts.get("partial_fill_count"), 0), max(real_count, 1)
        )
        cancel_rate = _pct(_safe_int(counts.get("cancel_or_fail_count"), 0), total)
        late_fill_rate = _pct(
            _safe_int(counts.get("late_fill_count"), 0), max(real_count, 1)
        )
        downside_source = split_variant_ev_list or []
        downside = (
            sorted(downside_source)[max(0, int(len(downside_source) * 0.10) - 1)]
            if downside_source
            else 0.0
        )
        split_variant_outcome_ready = (
            split_variant_outcome_count >= SPLIT_VARIANT_OUTCOME_FLOOR_REAL
        )
        ev_passed = (
            child_shape_seed is None
            and bucket != "guarded_or_stale"
            and real_count >= SAMPLE_FLOOR_REAL
            and split_variant_outcome_ready
            and split_variant_ev is not None
            and split_variant_ev >= RUNTIME_PROMOTION_MIN_COST_ADJUSTED_EV_PCT
            and downside > -2.0
        )
        mature_variant_quality = [
            item
            for item in split_variant_judgment_quality
            if item.get("runtime_promotion_sample_ready") is True
        ]
        mature_parent_evidence_supportive = any(
            item.get("runtime_evidence_ready") is True
            for item in mature_variant_quality
        )
        mature_parent_evidence_contradictory = bool(
            mature_variant_quality and not mature_parent_evidence_supportive
        )
        seed_observation_phase = (
            "initial_seed"
            if split_variant_outcome_count < SPLIT_VARIANT_CONTINUATION_FLOOR_REAL
            else (
                "early_continuation"
                if split_variant_outcome_count < SPLIT_VARIANT_OUTCOME_FLOOR_REAL
                else "promotion_evaluation"
            )
        )
        early_continuation_edge_pass = bool(
            split_variant_outcome_count >= SPLIT_VARIANT_CONTINUATION_FLOOR_REAL
            and not split_variant_outcome_ready
            and split_variant_ev is not None
            and split_variant_ev > 0
            and downside > -2.0
            and not mature_parent_evidence_contradictory
        )
        initial_seed_evidence_pass = bool(
            split_variant_outcome_count < SPLIT_VARIANT_CONTINUATION_FLOOR_REAL
            and not mature_parent_evidence_contradictory
        )
        continuation_gate_pass = bool(
            initial_seed_evidence_pass or early_continuation_edge_pass
        )
        execution_shape_seed_passed = (
            child_shape_seed is None
            and bucket != "guarded_or_stale"
            and real_count >= SAMPLE_FLOOR_REAL
            and not split_variant_outcome_ready
            and cancel_rate <= 20.0
            and late_fill_rate <= 20.0
            and continuation_gate_pass
        )
        child_shape_seed_passed = bool(
            child_shape_seed is not None
            and bucket != "guarded_or_stale"
            and real_count >= SAMPLE_FLOOR_REAL
            and cancel_rate <= 20.0
            and late_fill_rate <= 20.0
        )
        if child_shape_seed_passed:
            continuation_action = "continue_child_shape_positive_ev_seed"
        elif ev_passed:
            continuation_action = "promote_ev_validated_variant"
        elif execution_shape_seed_passed:
            continuation_action = "continue_bounded_seed"
        elif real_count < SAMPLE_FLOOR_REAL:
            continuation_action = "hold_observation"
        elif bucket != "guarded_or_stale" and (
            mature_parent_evidence_contradictory
            or (
                split_variant_outcome_count >= SPLIT_VARIANT_CONTINUATION_FLOOR_REAL
                and not early_continuation_edge_pass
            )
        ):
            continuation_action = "disable_previous_policy_next_preopen"
        else:
            continuation_action = "hold_observation"
        policy_mode = ""
        policy_generation_reason = ""
        if child_shape_seed_passed:
            floor_status = "pass_child_shape_positive_ev_seed"
            primary_sample_book = "real_split_child_variant"
            policy_mode = POLICY_MODE_CHILD_SHAPE_EV_SEED
            policy_generation_reason = (
                "exact runtime child shape passed bounded seed EV, tail, and "
                "execution guards; parent variants with different runtime shapes "
                "remain excluded"
            )
        elif ev_passed:
            floor_status = "pass_real_primary_ev"
            primary_sample_book = "real_split_variant"
            policy_mode = POLICY_MODE_REAL_PRIMARY_EV
            policy_generation_reason = (
                "real split variant outcome EV passed sample/downside guards"
            )
        elif execution_shape_seed_passed:
            tick_sample = _safe_int(tick_band.get("sample_count"), 0)
            if (
                template.get("leg_count") == 3
                and tick_sample >= POST_SUBMIT_TICK_BAND_FLOOR_REAL
            ):
                floor_status = "pass_post_submit_tick_band_seed"
                primary_sample_book = "real_submit_post_submit_observed_low"
                policy_mode = POLICY_MODE_POST_SUBMIT_TICK_BAND
                policy_generation_reason = (
                    "real submit sample floor and post-submit observed low tick-band passed; "
                    "open a qty-preserving 3-leg 0/0.3/0.8pct seed"
                )
            else:
                floor_status = "pass_bounded_equal_split_baseline"
                primary_sample_book = "real_submit_execution_shape"
                policy_mode = POLICY_MODE_BOUNDED_EQUAL_BASELINE
                policy_generation_reason = (
                    "real submit sample floor passed, split-variant outcome is pending, and execution guards allow "
                    "a qty-preserving 2-leg 50/50 0.3pct baseline"
                )
        elif real_count < SAMPLE_FLOOR_REAL:
            floor_status = "hold_sample"
            primary_sample_book = "none"
        elif mature_parent_evidence_contradictory:
            floor_status = "hold_mature_parent_split_edge_contradicted"
            primary_sample_book = "real_split_variant"
        elif (
            split_variant_outcome_count >= SPLIT_VARIANT_CONTINUATION_FLOOR_REAL
            and not split_variant_outcome_ready
            and not early_continuation_edge_pass
        ):
            floor_status = "hold_early_split_variant_edge_not_positive"
            primary_sample_book = "real_split_variant"
        elif split_variant_outcome_ready:
            floor_status = "hold_no_split_variant_edge"
            primary_sample_book = "real_split_variant"
        elif sim_count >= SAMPLE_FLOOR_SIM and sim_ev is not None:
            floor_status = "hold_real_outcome_pending"
            primary_sample_book = "sim_diagnostic"
        else:
            floor_status = "hold_real_outcome_pending"
            primary_sample_book = "real_outcome_pending"
        passed = ev_passed or execution_shape_seed_passed or child_shape_seed_passed
        runtime_apply_scope = (
            "child_shape_bounded_seed"
            if child_shape_seed_passed
            else ("ev_optimized_variant" if ev_passed else "baseline_split_structure")
        )
        runtime_apply_authority_class = (
            "ev_validated_variant"
            if ev_passed
            else (
                "bounded_exploration_seed"
                if execution_shape_seed_passed or child_shape_seed_passed
                else "none"
            )
        )
        if child_shape_seed_passed:
            continuation_reason = (
                "exact_child_shape_positive_ev_tail_and_execution_gate_passed"
            )
        elif ev_passed:
            continuation_reason = "full_ev_and_tail_gate_passed"
        elif execution_shape_seed_passed:
            continuation_reason = "bounded_seed_execution_and_edge_gates_passed"
        elif real_count < SAMPLE_FLOOR_REAL:
            continuation_reason = "real_submit_sample_floor_not_reached"
        elif mature_parent_evidence_contradictory:
            continuation_reason = (
                "mature_parent_variants_have_no_positive_tail_safe_edge"
            )
        elif split_variant_outcome_count >= SPLIT_VARIANT_CONTINUATION_FLOOR_REAL:
            continuation_reason = "early_variant_ev_or_tail_gate_failed"
        else:
            continuation_reason = "execution_shape_gate_failed"
        grid.append(
            {
                "context_bucket": bucket,
                **template,
                "price_candidates": [
                    item
                    for item in template["price_candidates"]
                    if item in ALLOWED_PRICE_CANDIDATES
                ],
                "real_sample_count": real_count,
                "real_observed_entry_count": _safe_int(
                    counts.get("real_observed_entry_count"), 0
                ),
                "sim_sample_count": sim_count,
                "real_outcome_joined_sample": real_bucket_outcome_count,
                "real_bucket_outcome_ev_pct": real_bucket_ev,
                "real_split_variant_outcome_joined_sample": split_variant_outcome_count,
                "real_split_variant_ev_pct": split_variant_ev,
                "observed_real_split_outcome_count": observed_split_outcome_count,
                "observed_real_split_variants": observed_split_variants,
                "observed_real_split_child_variants": [
                    {
                        "split_child_variant_id": observed_variant_id,
                        "sample_count": len(observed_values),
                        "equal_weight_avg_profit_pct": round(mean(observed_values), 4),
                    }
                    for (
                        observed_bucket,
                        observed_variant_id,
                    ), observed_values in sorted(
                        real_split_child_variant_ev_values.items()
                    )
                    if observed_bucket == bucket and observed_values
                ],
                "selected_child_shape_evidence": (
                    {
                        "child_variant_id": child_shape_seed["child_variant_id"],
                        "sample_count": child_shape_seed["sample_count"],
                        "equal_weight_avg_profit_pct": child_shape_seed[
                            "equal_weight_avg_profit_pct"
                        ],
                        "downside_p10_profit_rate": child_shape_seed[
                            "downside_p10_profit_rate"
                        ],
                        "minimum_seed_sample": CHILD_SHAPE_SEED_OUTCOME_FLOOR_REAL,
                        "minimum_seed_ev_pct": CHILD_SHAPE_SEED_MIN_EV_PCT,
                        "maximum_seed_downside_p10_pct": (
                            CHILD_SHAPE_SEED_MAX_DOWNSIDE_P10_PCT
                        ),
                        "runtime_shape_gate": template.get("runtime_shape_gate"),
                    }
                    if child_shape_seed is not None
                    else None
                ),
                "cumulative_judgment_quality": {
                    "learning_sample_floor": CUMULATIVE_LEARNING_SAMPLE_FLOOR,
                    "learning_sample_count": cumulative_learning_sample_count,
                    "learning_updated": cumulative_learning_updated,
                    "learning_update_policy": (
                        "one_mature_split_variant_outcome_updates_cumulative_judgment_quality"
                    ),
                    "equal_weight_avg_profit_pct": (
                        round(
                            mean(
                                value
                                for (
                                    observed_bucket,
                                    _variant_id,
                                ), values in real_split_variant_ev_values.items()
                                if observed_bucket == bucket
                                for value in values
                            ),
                            4,
                        )
                        if cumulative_learning_updated
                        else None
                    ),
                    "runtime_promotion_sample_floor": {
                        "real_submit": SAMPLE_FLOOR_REAL,
                        "real_split_variant_outcome": SPLIT_VARIANT_OUTCOME_FLOOR_REAL,
                        "minimum_cost_adjusted_ev_pct": (
                            RUNTIME_PROMOTION_MIN_COST_ADJUSTED_EV_PCT
                        ),
                    },
                    "split_variant_quality": split_variant_judgment_quality,
                    "learning_floor_grants_runtime_promotion": False,
                },
                "post_apply_continuation_gate": {
                    "phase": seed_observation_phase,
                    "minimum_early_review_sample": (
                        SPLIT_VARIANT_CONTINUATION_FLOOR_REAL
                    ),
                    "minimum_promotion_sample": SPLIT_VARIANT_OUTCOME_FLOOR_REAL,
                    "exact_variant_sample_count": split_variant_outcome_count,
                    "exact_variant_equal_weight_avg_profit_pct": split_variant_ev,
                    "exact_variant_downside_p10_profit_rate": (
                        round(float(downside), 4) if split_variant_ev_list else None
                    ),
                    "mature_parent_variant_count": len(mature_variant_quality),
                    "mature_parent_evidence_supportive": (
                        mature_parent_evidence_supportive
                    ),
                    "mature_parent_evidence_contradictory": (
                        mature_parent_evidence_contradictory
                    ),
                    "mature_parent_tail_applies_to_selected_child_shape": (
                        False if child_shape_seed is not None else True
                    ),
                    "pass": passed,
                    "economic_evidence_pass": (
                        True
                        if ev_passed or child_shape_seed_passed
                        else continuation_gate_pass
                    ),
                    "runtime_candidate_pass": passed,
                    "action": continuation_action,
                    "reason": continuation_reason,
                    "sample_shortfall_holds_but_negative_edge_disables_next_preopen": (
                        True
                    ),
                    "negative_or_missing_edge_is_calibration_freeze_not_safety_rollback": (
                        False
                    ),
                },
                "split_variant_id": split_variant_id,
                "selected_child_variant_id": (
                    child_shape_seed["child_variant_id"]
                    if child_shape_seed is not None
                    else ""
                ),
                "runtime_shape_gate": template.get("runtime_shape_gate"),
                "optimization_basis": (
                    "real_split_child_variant_outcome"
                    if child_shape_seed_passed
                    else (
                        "split_variant_outcome"
                        if ev_passed
                        else (
                            "post_submit_observed_low_tick_band"
                            if policy_mode == POLICY_MODE_POST_SUBMIT_TICK_BAND
                            else "bounded_execution_shape_seed"
                        )
                    )
                ),
                "post_submit_low_tick_band": tick_band,
                "primary_sample_book": primary_sample_book,
                "real_submit_count": _safe_int(counts.get("real_submitted_count"), 0),
                "real_submit_rate_pct": (
                    _pct(
                        _safe_int(counts.get("real_submitted_count"), 0),
                        event_real_count,
                    )
                    if event_real_count > 0
                    else None
                ),
                "sim_fill_count": _safe_int(counts.get("sim_fill_count"), 0),
                "sim_fill_rate_pct": (
                    _pct(_safe_int(counts.get("sim_fill_count"), 0), sim_count)
                    if sim_count > 0
                    else None
                ),
                "cost_adjusted_positive_terminal_count": sum(
                    1 for value in split_variant_ev_list or [] if value > 0
                ),
                "cost_adjusted_positive_terminal_rate_pct": (
                    _pct(
                        sum(1 for value in split_variant_ev_list or [] if value > 0),
                        split_variant_outcome_count,
                    )
                    if split_variant_outcome_count > 0
                    else None
                ),
                "fill_quality": round(
                    (
                        _safe_int(counts.get("real_submitted_count"), 0)
                        + _safe_int(counts.get("sim_fill_count"), 0)
                    )
                    / total,
                    4,
                ),
                "fill_quality_scope": (
                    "legacy_mixed_real_submit_and_sim_fill_diagnostic_not_runtime_gate"
                ),
                "missed_upside": round(max(0.0, primary_ev or 0.0), 4),
                "source_quality_adjusted_ev_pct": primary_ev,
                "real_source_quality_adjusted_ev_pct": split_variant_ev,
                "diagnostic_sim_ev_pct": sim_ev,
                "notional_weighted_ev_pct": notional_ev,
                "partial_fill_rate": partial_fill_rate,
                "cancel_rate": cancel_rate,
                "late_fill_rate": late_fill_rate,
                "downside_p10_profit_rate": round(float(downside), 4),
                "sample_floor_status": floor_status,
                "policy_mode": policy_mode,
                "policy_generation_reason": policy_generation_reason,
                "candidate_passed": passed,
                "exploration_seed_allowed": (
                    execution_shape_seed_passed or child_shape_seed_passed
                ),
                "ev_validated_runtime_apply_allowed": ev_passed,
                "runtime_apply_allowed": passed,
                "runtime_apply_scope": runtime_apply_scope if passed else "none",
                "runtime_apply_authority_class": runtime_apply_authority_class,
                "runtime_apply_reason": (
                    "positive_child_shape_ev_seed_passed"
                    if child_shape_seed_passed
                    else (
                        "positive_split_variant_ev_passed"
                        if ev_passed
                        else (
                            "qty_preserving_execution_shape_seed_passed"
                            if execution_shape_seed_passed
                            else floor_status
                        )
                    )
                ),
            }
        )
    return grid


def _policy_payload(
    target_date: str, report_json: Path, candidate_grid: list[dict[str, Any]]
) -> dict[str, Any]:
    passed = [item for item in candidate_grid if item.get("candidate_passed")]
    explicit_bucket_candidates = [
        item
        for item in passed
        if item.get("runtime_apply_scope") == "ev_optimized_variant"
        or item.get("runtime_apply_scope") == "child_shape_bounded_seed"
        or item.get("policy_mode") == POLICY_MODE_POST_SUBMIT_TICK_BAND
    ]
    exploration_seed_candidates = [
        item for item in passed if item.get("exploration_seed_allowed") is True
    ]
    ev_validated_candidates = [
        item
        for item in passed
        if item.get("ev_validated_runtime_apply_allowed") is True
    ]
    version_seed = json.dumps(passed, sort_keys=True, ensure_ascii=False)
    digest = hashlib.sha1(version_seed.encode("utf-8")).hexdigest()[:10]
    policy_version = f"{RUNTIME_FAMILY}:{target_date}:{digest}"
    runtime_apply_scopes = sorted(
        {
            str(item.get("runtime_apply_scope") or "")
            for item in passed
            if str(item.get("runtime_apply_scope") or "")
        }
    )
    post_apply_attribution = {
        "required": True,
        "minimum_observed_split_outcome_sample": SPLIT_VARIANT_OUTCOME_FLOOR_REAL,
        "metrics": [
            "fill_rate_delta",
            "real_submit_rate_pct_delta",
            "sim_fill_rate_pct_delta",
            "cost_adjusted_positive_terminal_rate_pct_delta",
            "cancel_rate_delta",
            "missed_upside_rate_delta",
            "source_quality_adjusted_ev_pct_delta",
        ],
        "fill_rate_delta_scope": (
            "legacy_compatibility_only_use_explicit_real_and_sim_metrics"
        ),
        "separate_partial_and_full_fill": True,
    }
    continuation_gate = {
        "active": True,
        "minimum_early_review_sample": SPLIT_VARIANT_CONTINUATION_FLOOR_REAL,
        "minimum_promotion_sample": SPLIT_VARIANT_OUTCOME_FLOOR_REAL,
        "negative_ev_or_tail_action": "disable_previous_policy_next_preopen",
        "mature_parent_contradiction_action": ("disable_previous_policy_next_preopen"),
        "negative_economic_disable_is_not_hard_safety_rollback": True,
        "freeze_is_not_safety_rollback": False,
        "evaluated_bucket_count": len(candidate_grid),
        "continued_bucket_count": len(passed),
        "disabled_next_preopen_buckets": [
            str(item.get("context_bucket") or "")
            for item in candidate_grid
            if (item.get("post_apply_continuation_gate") or {}).get("action")
            == "disable_previous_policy_next_preopen"
        ],
        "frozen_buckets": [],
    }
    rollback_guard = {
        "action": "fail_closed_to_existing_operator_or_runtime_fallback",
        "triggers": [
            "source_quality_or_provenance_breach",
            "immutable_generation_contract_breach",
            "hard_safety_or_submit_contract_breach",
            "catastrophic_tail_loss",
        ],
        "ordinary_negative_ev_action": "disable_previous_policy_next_preopen",
        "ordinary_sample_shortfall_action": "hold_observation",
    }
    baseline_runtime_defaults_enabled = any(
        item.get("runtime_apply_scope") == "baseline_split_structure" for item in passed
    )
    return {
        "schema_version": POLICY_SCHEMA_VERSION,
        "policy_version": policy_version,
        "entry_price_plan_schema": ATOMIC_PRICE_PLAN_SCHEMA,
        "entry_execution_sizing_plan_schema": ATOMIC_EXECUTION_SIZING_SCHEMA,
        "entry_execution_sizing_policy": ATOMIC_EXECUTION_SIZING_BASELINE_POLICY,
        "source_date": target_date,
        "source_report": str(report_json),
        "runtime_apply_allowed": bool(passed),
        "runtime_apply_compatibility_semantics": RUNTIME_APPLY_COMPATIBILITY_SEMANTICS,
        "exploration_seed_allowed": bool(exploration_seed_candidates),
        "exploration_seed_count": len(exploration_seed_candidates),
        "ev_validated_runtime_apply_allowed": bool(ev_validated_candidates),
        "ev_validated_bucket_count": len(ev_validated_candidates),
        "runtime_apply_authority_classes": sorted(
            {
                str(item.get("runtime_apply_authority_class") or "")
                for item in passed
                if str(item.get("runtime_apply_authority_class") or "")
            }
        ),
        "baseline_runtime_defaults_enabled": baseline_runtime_defaults_enabled,
        # A scoped policy is authoritative only for the buckets it explicitly
        # selected.  Falling back in another bucket would turn a bounded,
        # cost-reviewed seed into an unreviewed runtime split.
        "missing_bucket_action": (
            "runtime_default_fallback"
            if baseline_runtime_defaults_enabled
            else "keep_original_order"
        ),
        "explicit_bucket_count": len(explicit_bucket_candidates),
        "preopen_guard_required": True,
        "runtime_apply_scope": runtime_apply_scopes,
        "post_apply_attribution": post_apply_attribution,
        "post_apply_continuation_gate": continuation_gate,
        "rollback_guard": rollback_guard,
        "decision_authority": "next_preopen_bounded_entry_split_policy",
        "forbidden_uses": [
            "increase_requested_qty",
            "cap_release",
            "broker_guard_relief",
            "intraday_mutation",
            "provider_route_change",
        ],
        "buckets": {
            str(item["context_bucket"]): {
                "context_bucket": item["context_bucket"],
                "leg_count": item["leg_count"],
                "price_offsets_ticks": item["price_offsets_ticks"],
                "price_offsets_pct": item.get("price_offsets_pct"),
                "qty_weight_min": item["qty_weight_min"],
                "qty_weight_max": item["qty_weight_max"],
                "urgency_score": item["urgency_score"],
                "passive_edge_score": item["passive_edge_score"],
                "policy_mode": item.get("policy_mode") or POLICY_MODE_REAL_PRIMARY_EV,
                "policy_generation_reason": item.get("policy_generation_reason") or "",
                "primary_sample_book": item.get("primary_sample_book"),
                "real_sample_count": item.get("real_sample_count"),
                "real_outcome_joined_sample": item.get("real_outcome_joined_sample"),
                "real_split_variant_outcome_joined_sample": item.get(
                    "real_split_variant_outcome_joined_sample"
                ),
                "observed_real_split_outcome_count": item.get(
                    "observed_real_split_outcome_count"
                ),
                "observed_real_split_variants": item.get(
                    "observed_real_split_variants"
                ),
                "split_variant_id": item.get("split_variant_id"),
                "selected_child_variant_id": item.get("selected_child_variant_id"),
                "runtime_shape_gate": item.get("runtime_shape_gate"),
                "selected_child_shape_evidence": item.get(
                    "selected_child_shape_evidence"
                ),
                "optimization_basis": item.get("optimization_basis"),
                "runtime_apply_scope": item.get("runtime_apply_scope"),
                "runtime_apply_reason": item.get("runtime_apply_reason"),
                "runtime_apply_authority_class": item.get(
                    "runtime_apply_authority_class"
                ),
                "exploration_seed_allowed": item.get("exploration_seed_allowed"),
                "ev_validated_runtime_apply_allowed": item.get(
                    "ev_validated_runtime_apply_allowed"
                ),
                "post_apply_continuation_gate": item.get(
                    "post_apply_continuation_gate"
                ),
                "post_submit_low_tick_band": item.get("post_submit_low_tick_band"),
                "source_quality_adjusted_ev_pct": item[
                    "source_quality_adjusted_ev_pct"
                ],
                "notional_weighted_ev_pct": item["notional_weighted_ev_pct"],
                "downside_p10_profit_rate": item["downside_p10_profit_rate"],
            }
            for item in explicit_bucket_candidates
        },
    }


def quantity_leg_promotion_evidence_valid(evaluation: object) -> bool:
    """Recheck new four-arm selection evidence, not its claimed passed flag."""
    if not isinstance(evaluation, dict):
        return False
    try:
        if evaluation.get("selection_contract") != QUANTITY_LEG_SELECTION_CONTRACT:
            return False
        if evaluation.get("schema") != QUANTITY_LEG_FOUR_ARM_SCHEMA:
            return False
        count = evaluation["complete_exact_attempt_count"]
        denominator = evaluation["eligible_attempt_count"]
        hashes = evaluation["validated_source_receipt_sha256s"]
        if (
            type(count) is not int or count < QUANTITY_LEG_FOUR_ARM_MIN_COMPLETE_ATTEMPTS
            or type(denominator) is not int or denominator < count
            or not isinstance(hashes, list) or len(hashes) != count
            or len(set(hashes)) != count
            or not all(re.fullmatch(r"[0-9a-f]{64}", value) for value in hashes)
            or isinstance(evaluation["exact_attempt_join_coverage"], bool)
            or not math.isclose(evaluation["exact_attempt_join_coverage"], count / denominator)
            or count / denominator < QUANTITY_LEG_FOUR_ARM_MIN_JOIN_COVERAGE
        ):
            return False
        partitions = evaluation["chronological_partitions"]
        calibration, holdout = partitions["calibration"], partitions["holdout"]
        partition_hashes = (calibration["validated_source_receipt_sha256s"]
                            + holdout["validated_source_receipt_sha256s"])
        if sorted(partition_hashes) != sorted(hashes) or len(set(partition_hashes)) != count:
            return False
        cal_dates, hold_dates = calibration["source_dates"], holdout["source_dates"]
        census = evaluation.get("native_source_counts")
        if census is not None:
            if (not isinstance(census, dict) or any(type(n) is not int or n < 0
                    or date.fromisoformat(d).isoformat() != d or d < "2026-06-05"
                    for d, n in census.items())
                or (any(census.values()) and (not hold_dates or hold_dates[-1] < max(d for d, n in census.items() if n)))):
                return False
            census_applies = any(census.values()) or any(d in census for d in cal_dates + hold_dates)
            if census_applies and (sum(census.values()) != denominator
                or any(p["complete_exact_attempt_count"] > sum(census.get(d, 0)
                           for d in p["source_dates"]) for p in (calibration, holdout))):
                return False
        if (
            not cal_dates or len(hold_dates) != 1
            or cal_dates != sorted(set(cal_dates))
            or max(cal_dates) >= hold_dates[0]
            or any(date.fromisoformat(day).isoformat() != day or day < "2026-06-05"
                   or day > date.today().isoformat()
                   for day in cal_dates + hold_dates)
            or any(type(p["complete_exact_attempt_count"]) is not int
                   or p["complete_exact_attempt_count"] <= 0
                   for p in (calibration, holdout))
            or calibration["complete_exact_attempt_count"]
            + holdout["complete_exact_attempt_count"] != count
        ):
            return False
        comparisons = {
            "cost_adjusted_net_ev_pct": lambda c, i: c > 0 and c > i,
            "net_pnl_krw": lambda c, i: c > i,
            "positive_terminal_frequency": lambda c, i: 0 <= i <= c <= 1,
            "net_profit_per_capital_minute_pct": lambda c, i: c >= i and c > 0,
            "downside_p10_net_pct": lambda c, i: c >= i,
            "expected_shortfall_10pct": lambda c, i: c >= i,
            "fill_participation_rate": lambda c, i: 0 <= c <= 1 and 0 <= i <= 1 and c >= i - 0.05,
        }
        for sample in (evaluation, calibration, holdout):
            arms = sample["arms"]
            if set(arms) != set(QUANTITY_LEG_FOUR_ARM_IDS):
                return False
            for arm in arms.values():
                if (type(arm["paired_sample_count"]) is not int
                    or arm["paired_sample_count"] != sample["complete_exact_attempt_count"]):
                    return False
                for field in comparisons:
                    value = arm[field]
                    if isinstance(value, bool) or not math.isfinite(float(value)):
                        return False
                if any(not 0 <= arm[field] <= 1 for field in
                       ("positive_terminal_frequency", "fill_participation_rate")):
                    return False
            if len(sample.get("validated_source_receipt_sha256s", [])) != sample["complete_exact_attempt_count"]:
                return False
            control, challenger = arms[QUANTITY_LEG_FOUR_ARM_IDS[0]], arms[QUANTITY_LEG_FOUR_ARM_IDS[-1]]
            if any(not predicate(challenger[field], control[field])
                   for field, predicate in comparisons.items()):
                return False
        if evaluation["arms"][QUANTITY_LEG_FOUR_ARM_IDS[-1]]["cost_adjusted_net_ev_pct"] < 0.10:
            return False
        for arm_id in QUANTITY_LEG_FOUR_ARM_IDS:
            whole = evaluation["arms"][arm_id]
            cal, held = calibration["arms"][arm_id], holdout["arms"][arm_id]
            for field in ("cost_adjusted_net_ev_pct", "positive_terminal_frequency", "fill_participation_rate"):
                weighted = (cal[field] * calibration["complete_exact_attempt_count"]
                            + held[field] * holdout["complete_exact_attempt_count"]) / count
                if not math.isclose(whole[field], weighted, abs_tol=1e-9):
                    return False
            if not math.isclose(whole["net_pnl_krw"], cal["net_pnl_krw"] + held["net_pnl_krw"], abs_tol=1e-9):
                return False
        gate = evaluation["promotion_gate"]
        return bool(gate.get("passed") is True and not gate.get("blockers")
                    and gate.get("chronological_holdout_required") is True
                    and gate.get("minimum_candidate_cost_adjusted_net_ev_pct") == 0.10)
    except (KeyError, TypeError, ValueError, OverflowError):
        return False


def quantity_leg_policy_selection_evidence_valid(policy: dict[str, Any]) -> bool:
    """Preserve frozen legacy policies; validate newly published selection proof."""
    evidence = policy.get("quantity_leg_selection_evidence")
    split_policy = {}
    if str(policy.get("source_date") or "") < "2026-09-17" and not evidence:
        return True
    if str(policy.get("source_date") or "") >= "2026-09-17":
        # PREOPEN and the atomic runtime loader share this predicate. A signed
        # research quartet cannot bypass the execution-model gate via U9/U10.
        try:
            path = Path(str(policy.get("split_policy_file") or ""))
            if not path.is_file() or path.stat().st_size > 64 * 1024 * 1024:
                return False
            encoded = path.read_bytes()
            split_policy = json.loads(encoded)
            if (hashlib.sha256(encoded).hexdigest() != policy.get("split_policy_sha256")
                    or split_policy.get("runtime_apply_allowed") is not True
                    or not policy_report_generation_contract_status(split_policy)[0]):
                return False
        except (OSError, ValueError, TypeError, AttributeError):
            return False
    if not quantity_leg_promotion_evidence_valid(evidence):
        return False
    identity = evidence.get("paired_policy_identity")
    return bool(
        isinstance(identity, dict)
        and identity == policy.get("paired_policy_identity")
        and identity.get("candidate_leg_policy_version") == split_policy.get("selection_leg_template_version",policy.get("split_policy_version"))
        and policy.get("selected_arm") == QUANTITY_LEG_FOUR_ARM_IDS[-1]
        and policy.get("promotion_gate") == evidence.get("promotion_gate")
        and evidence["chronological_partitions"]["holdout"]["source_dates"][-1]
        <= str(policy.get("source_date") or "")
    )


def build_quantity_leg_four_arm_evaluation(
    events: list[dict[str, Any]], *, source_counts: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Evaluate quantity and leg changes only on complete exact-attempt quartets."""

    def quantile(values: list[float], fraction: float) -> float | None:
        if not values:
            return None
        ordered = sorted(values)
        index = max(0, min(len(ordered) - 1, math.ceil(len(ordered) * fraction) - 1))
        return ordered[index]

    receipt_rows = [
        (
            event.get("entry_quantity_leg_four_arm_evaluation"),
            str(event.get("source_date") or "undated").strip() or "undated",
        )
        for event in events
        if isinstance(event.get("entry_quantity_leg_four_arm_evaluation"), dict)
    ]
    receipts = [receipt for receipt, _ in receipt_rows]
    complete: list[dict[str, Any]] = []
    excluded: defaultdict[str, int] = defaultdict(int)
    seen: set[tuple[str, ...]] = set()
    receipt_hashes: dict[tuple[str, ...], str] = {}
    conflicting_attempts: set[tuple[str, ...]] = set()
    policy_identities: set[tuple[str, ...]] = set()
    declared_eligible_by_source: defaultdict[str, set[int]] = defaultdict(set)
    for receipt, source_date in receipt_rows:
        declared_value = receipt.get("eligible_attempt_count")
        declared_number = _safe_float(declared_value, None)
        declared_eligible = (
            int(declared_number)
            if not isinstance(declared_value, bool)
            and declared_number is not None
            and math.isfinite(declared_number)
            and declared_number.is_integer()
            and declared_number > 0
            else 0
        )
        identity = tuple(
            str(receipt.get(field) or "").strip()
            for field in (
                "scanner_promotion_id",
                "evaluation_attempt_id",
                "stock_code",
                "effective_venue",
                "session_bucket",
                "policy_bundle_sha256",
            )
        )
        if not all(identity):
            excluded["exact_attempt_identity_missing"] += 1
            continue
        seen.add(identity)
        arms = receipt.get("arms")
        if receipt.get("schema") != QUANTITY_LEG_FOUR_ARM_SCHEMA or not isinstance(
            arms, dict
        ):
            excluded["schema_invalid"] += 1
            continue
        receipt_body = {
            key: value for key, value in receipt.items() if key != "receipt_sha256"
        }
        expected_receipt_sha256 = hashlib.sha256(
            json.dumps(
                receipt_body,
                ensure_ascii=True,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("ascii")
        ).hexdigest()
        if receipt.get("receipt_sha256") != expected_receipt_sha256:
            excluded["immutable_receipt_hash_invalid"] += 1
            continue
        signed_date = str(receipt.get("source_date") or "").strip()
        if signed_date:
            try:
                parsed_date = date.fromisoformat(signed_date)
                valid_date = (
                    parsed_date.isoformat() == signed_date
                    and signed_date >= "2026-06-05"
                    and parsed_date <= datetime.now(timezone(timedelta(hours=9))).date()
                    and source_date in {"undated", signed_date}
                )
            except ValueError:
                valid_date = False
            if not valid_date:
                excluded["source_date_contract_invalid"] += 1
                continue
            source_date = signed_date
        if declared_eligible > 0:
            declared_eligible_by_source[source_date].add(declared_eligible)
        previous_hash = receipt_hashes.get(identity)
        if previous_hash is not None:
            if previous_hash == expected_receipt_sha256:
                excluded["duplicate_exact_attempt"] += 1
            else:
                conflicting_attempts.add(identity)
                excluded["conflicting_exact_attempt_receipt"] += 1
            continue
        receipt_hashes[identity] = expected_receipt_sha256
        if set(arms) != set(QUANTITY_LEG_FOUR_ARM_IDS):
            excluded["four_arm_incomplete"] += 1
            continue
        policy_identity = tuple(
            str(receipt.get(field) or "").strip()
            for field in (
                "incumbent_quantity_policy_version",
                "candidate_quantity_policy_version",
                "incumbent_leg_policy_version",
                "candidate_leg_policy_version",
                "entry_price_policy_sha256",
            )
        )
        if not all(policy_identity) or not re.fullmatch(
            r"[0-9a-f]{64}", policy_identity[-1]
        ):
            excluded["policy_identity_missing_or_invalid"] += 1
            continue
        arm_contract_valid = True
        shared_contract: tuple[str, ...] | None = None
        for arm_id in QUANTITY_LEG_FOUR_ARM_IDS:
            arm = arms[arm_id]
            if not isinstance(arm, dict) or any(
                isinstance(arm.get(field), bool)
                or _safe_float(arm.get(field), None) is None
                or not math.isfinite(float(arm[field]))
                for field in (
                    "net_return_pct",
                    "net_pnl_krw",
                    "capital_krw_minutes",
                    "fill_participation_rate",
                )
            ):
                arm_contract_valid = False
                break
            if (
                float(arm["capital_krw_minutes"]) < 0
                or not 0 <= float(arm["fill_participation_rate"]) <= 1
                or (
                    float(arm["capital_krw_minutes"]) == 0
                    and (
                        float(arm["net_pnl_krw"]) != 0
                        or float(arm["net_return_pct"]) != 0
                    )
                )
            ):
                arm_contract_valid = False
                break
            arm_shared_contract = tuple(
                str(arm.get(field) or "").strip()
                for field in QUANTITY_LEG_FOUR_ARM_SHARED_CONTRACT_FIELDS
            )
            if not all(arm_shared_contract) or not all(
                re.fullmatch(r"[0-9a-f]{64}", value)
                for value in arm_shared_contract[:3]
            ):
                arm_contract_valid = False
                break
            try:
                terminal_at = datetime.fromisoformat(arm_shared_contract[-1])
                terminal_time_valid = (
                    terminal_at.utcoffset() is not None
                    and terminal_at <= datetime.now(timezone.utc)
                    and (not signed_date or terminal_at.astimezone(
                        timezone(timedelta(hours=9))).date().isoformat() >= signed_date)
                )
            except (TypeError, ValueError, OverflowError):
                terminal_time_valid = False
            if not terminal_time_valid:
                arm_contract_valid = False
                break
            if shared_contract is None:
                shared_contract = arm_shared_contract
            elif arm_shared_contract != shared_contract:
                arm_contract_valid = False
                break
            if (
                arm.get("terminal_conservation_holds") is not True
                or arm.get("cost_complete") is not True
                or arm.get("counterfactual_executable") is not True
            ):
                arm_contract_valid = False
                break
        if not arm_contract_valid:
            excluded["arm_economics_or_executability_invalid"] += 1
            continue
        policy_identities.add(policy_identity)
        complete.append(
            {
                "identity": identity,
                "source_date": source_date,
                "arms": arms,
                "policy_identity": policy_identity,
                "signed_source_date": signed_date or None,
                "receipt_sha256": expected_receipt_sha256,
            }
        )

    if source_counts is not None:
        for census_date, census_count in source_counts.items():
            try:
                if (date.fromisoformat(census_date).isoformat() != census_date
                    or census_date < "2026-06-05" or type(census_count) is not int or census_count < 0):
                    raise ValueError("source_census_invalid")
                # Zero is a producer declaration, not an absent census value.
                declared_eligible_by_source[census_date].add(census_count)
            except (TypeError, ValueError):
                excluded["source_census_invalid"] += 1
                declared_eligible_by_source["invalid"].update({0, 1})
    if conflicting_attempts:
        quarantined = [
            item for item in complete if item["identity"] in conflicting_attempts
        ]
        excluded["conflicting_exact_attempt_quarantined"] += len(quarantined)
        complete = [
            item for item in complete if item["identity"] not in conflicting_attempts
        ]
        policy_identities = {item["policy_identity"] for item in complete}
    if len(policy_identities) != 1:
        if complete:
            excluded["paired_policy_identity_conflict"] += len(complete)
        complete = []

    def arm_metrics(items: list[dict[str, Any]], arm_id: str) -> dict[str, Any]:
        rows = [item["arms"][arm_id] for item in items]
        net_returns = [float(row["net_return_pct"]) for row in rows]
        net_pnls = [float(row["net_pnl_krw"]) for row in rows]
        capital_krw_minutes = [float(row["capital_krw_minutes"]) for row in rows]
        fill = [float(row["fill_participation_rate"]) for row in rows]
        p10 = quantile(net_returns, 0.10)
        worst_count = max(1, math.ceil(len(net_returns) * 0.10)) if net_returns else 0
        expected_shortfall = (
            mean(sorted(net_returns)[:worst_count]) if worst_count else None
        )
        return {
            "paired_sample_count": len(rows),
            "cost_adjusted_net_ev_pct": mean(net_returns) if net_returns else None,
            "net_pnl_krw": sum(net_pnls) if net_pnls else None,
            "positive_terminal_frequency": (
                sum(value > 0 for value in net_returns) / len(net_returns)
                if net_returns
                else None
            ),
            "net_profit_per_capital_minute_pct": (
                sum(net_pnls) / sum(capital_krw_minutes) * 100.0
                if capital_krw_minutes and sum(capital_krw_minutes) > 0
                else None
            ),
            "downside_p10_net_pct": p10,
            "expected_shortfall_10pct": expected_shortfall,
            "fill_participation_rate": mean(fill) if fill else None,
        }
    metrics = {arm: arm_metrics(complete, arm) for arm in QUANTITY_LEG_FOUR_ARM_IDS}
    source_dates = sorted({item["signed_source_date"] for item in complete
                           if item["signed_source_date"]})
    chronology_proven = bool(
        len(source_dates) >= 2
        and all(item["signed_source_date"] for item in complete)
    )
    census_dates = sorted(d for d, n in (source_counts or {}).items() if type(n) is int and n > 0)
    latest_date = max(source_dates + census_dates) if chronology_proven else None
    partitions = {}
    for name, items in (
        ("calibration", [item for item in complete
                         if chronology_proven and item["signed_source_date"] < latest_date]),
        ("holdout", [item for item in complete
                     if chronology_proven and item["signed_source_date"] == latest_date]),
    ):
        partitions[name] = {
            "source_dates": sorted({item["signed_source_date"] for item in items}),
            "complete_exact_attempt_count": len(items),
            "validated_source_receipt_sha256s": sorted(item["receipt_sha256"] for item in items),
            "arms": {arm: arm_metrics(items, arm) for arm in QUANTITY_LEG_FOUR_ARM_IDS},
        }
    incumbent = metrics[QUANTITY_LEG_FOUR_ARM_IDS[0]]
    candidate = metrics[QUANTITY_LEG_FOUR_ARM_IDS[-1]]
    conflicting_eligible_sources = sorted(
        source_date
        for source_date, values in declared_eligible_by_source.items()
        if len(values) != 1
    )
    eligible_attempt_count = (
        sum(next(iter(values)) for values in declared_eligible_by_source.values())
        if declared_eligible_by_source and not conflicting_eligible_sources
        else 0
    )
    if conflicting_eligible_sources:
        excluded["eligible_population_contract_conflicting_source_date"] += len(
            conflicting_eligible_sources
        )
    if source_counts is not None and any(source_counts.values()) and any(
        source_counts.get(item["source_date"]) is None
        or source_counts.get(item["source_date"]) not in
            declared_eligible_by_source[item["source_date"]]
        for item in complete
    ):
        excluded["eligible_population_source_date_missing"] += 1
        eligible_attempt_count = 0
    complete_by_date = Counter(item["source_date"] for item in complete)
    if any(len(declared_eligible_by_source[d]) != 1
           or n > next(iter(declared_eligible_by_source[d]))
           for d, n in complete_by_date.items()):
        excluded["eligible_population_source_date_underflow"] += 1
        eligible_attempt_count = 0
    if eligible_attempt_count and eligible_attempt_count < len(seen):
        excluded["eligible_population_count_underflow"] += 1
        eligible_attempt_count = 0
    if receipts and not eligible_attempt_count:
        excluded["eligible_population_contract_missing_or_conflicting"] += len(receipts)
    coverage = (
        len(complete) / eligible_attempt_count if eligible_attempt_count > 0 else None
    )
    blockers: list[str] = []
    if len(complete) < QUANTITY_LEG_FOUR_ARM_MIN_COMPLETE_ATTEMPTS:
        blockers.append("paired_sample_floor")
    if coverage is None or coverage < QUANTITY_LEG_FOUR_ARM_MIN_JOIN_COVERAGE:
        blockers.append("exact_attempt_join_coverage")
    if not chronology_proven:
        blockers.append("independent_chronological_source_dates_unproven")
    comparisons = (
        ("cost_adjusted_net_ev_pct", lambda c, i: c >= 0.10 and c > i),
        ("net_pnl_krw", lambda c, i: c > i),
        ("positive_terminal_frequency", lambda c, i: c >= i),
        ("net_profit_per_capital_minute_pct", lambda c, i: c >= i and c > 0),
        ("downside_p10_net_pct", lambda c, i: c >= i),
        ("expected_shortfall_10pct", lambda c, i: c >= i),
        ("fill_participation_rate", lambda c, i: c >= i - 0.05),
    )
    if complete:
        for field, predicate in comparisons:
            c_value = candidate.get(field)
            i_value = incumbent.get(field)
            if c_value is None or i_value is None or not predicate(c_value, i_value):
                blockers.append(field)
    if chronology_proven:
        for name, partition in partitions.items():
            control = partition["arms"][QUANTITY_LEG_FOUR_ARM_IDS[0]]
            challenger = partition["arms"][QUANTITY_LEG_FOUR_ARM_IDS[-1]]
            for field, predicate in comparisons:
                c_value, i_value = challenger.get(field), control.get(field)
                passed = (
                    c_value is not None and i_value is not None
                    and (c_value > 0 and c_value > i_value
                         if field == "cost_adjusted_net_ev_pct"
                         else predicate(c_value, i_value))
                )
                if not passed:
                    blockers.append(f"{name}:{field}")
    promotion_pass = not blockers
    return {
        "schema": QUANTITY_LEG_FOUR_ARM_SCHEMA,
        "selection_contract": QUANTITY_LEG_SELECTION_CONTRACT,
        "validated_source_receipt_sha256s": sorted(item["receipt_sha256"] for item in complete),
        "chronological_partitions": partitions,
        "status": "promotion_pass" if promotion_pass else "evidence_pending_or_blocked",
        "source_receipt_count": len(receipts),
        "eligible_attempt_count": eligible_attempt_count,
        "eligible_source_date_count": len(declared_eligible_by_source),
        "native_source_counts": source_counts,
        "complete_exact_attempt_count": len(complete),
        "exact_attempt_join_coverage": coverage,
        "excluded_counts": dict(sorted(excluded.items())),
        "paired_policy_identity": (
            dict(
                zip(
                    (
                        "incumbent_quantity_policy_version",
                        "candidate_quantity_policy_version",
                        "incumbent_leg_policy_version",
                        "candidate_leg_policy_version",
                        "entry_price_policy_sha256",
                    ),
                    next(iter(policy_identities)),
                )
            )
            if len(policy_identities) == 1
            else None
        ),
        "arms": metrics,
        "incremental_effects": {
            "quantity_only_net_ev_delta_pct": (
                metrics[QUANTITY_LEG_FOUR_ARM_IDS[1]]["cost_adjusted_net_ev_pct"]
                - incumbent["cost_adjusted_net_ev_pct"]
                if complete
                else None
            ),
            "leg_only_net_ev_delta_pct": (
                metrics[QUANTITY_LEG_FOUR_ARM_IDS[2]]["cost_adjusted_net_ev_pct"]
                - incumbent["cost_adjusted_net_ev_pct"]
                if complete
                else None
            ),
            "combined_net_ev_delta_pct": (
                candidate["cost_adjusted_net_ev_pct"]
                - incumbent["cost_adjusted_net_ev_pct"]
                if complete
                else None
            ),
        },
        "promotion_gate": {
            "applies_to": "challenger_automatic_promotion_only",
            "initial_baseline_activation_blocked_by_this_gate": False,
            "window_policy": "clean_baseline_cumulative_open_ended",
            "minimum_complete_exact_attempts": (
                QUANTITY_LEG_FOUR_ARM_MIN_COMPLETE_ATTEMPTS
            ),
            "minimum_exact_attempt_join_coverage": (
                QUANTITY_LEG_FOUR_ARM_MIN_JOIN_COVERAGE
            ),
            "minimum_candidate_cost_adjusted_net_ev_pct": 0.10,
            "maximum_fill_participation_decline": 0.05,
            "same_paired_population_required": True,
            "chronological_holdout_required": True,
            "same_entry_price_exit_cost_terminal_contract_required": True,
            "cost_complete_required": True,
            "terminal_conservation_required": True,
            "non_degradation_metrics": [
                "positive_terminal_frequency",
                "net_profit_per_capital_minute_pct",
                "downside_p10_net_pct",
                "expected_shortfall_10pct",
                "fill_participation_rate",
            ],
            "blockers": sorted(set(blockers)),
            "passed": promotion_pass,
        },
        "floor_attainability": {
            "bounded_observation_window": False,
            "observed_eligible_attempt_count": eligible_attempt_count,
            "remaining_complete_attempts_to_floor": max(
                0, QUANTITY_LEG_FOUR_ARM_MIN_COMPLETE_ATTEMPTS - len(complete)
            ),
            "status": (
                "source_receipt_missing"
                if not receipts
                else "floor_reached"
                if len(complete) >= QUANTITY_LEG_FOUR_ARM_MIN_COMPLETE_ATTEMPTS
                else "rolling_accumulation"
            ),
            "reason": (
                "No natural four-arm receipt is available; sample-floor tuning is not the first blocker."
                if not receipts
                else "The challenger gate accumulates exact terminal attempts across clean-baseline dates and has no fixed daily deadline."
            ),
        },
        "counterfactual_missing_is_null": True,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }



# Observation only: shared with existing durable BUY/SELL receipt snapshots.
ENTRY_SPLIT_ECONOMIC_RECEIPT_KEYS = (
    "entry_split_initial_entry_seed","entry_split_initial_entry_lineage_conflict",
    "entry_split_order_policy_sha256","entry_split_order_runtime_pid","entry_split_order_runtime_consumed",
    "entry_split_order_policy_applied","entry_split_order_policy_version","entry_split_order_bucket",
    "entry_split_order_policy_mode","entry_split_order_policy_variant_id","entry_split_order_variant_id",
    "entry_split_order_leg_count","entry_split_order_price_offsets_ticks","entry_split_order_qty_weight_min",
    "entry_split_order_qty_weight_max","entry_split_order_runtime_default_policy_applied",
    "entry_split_order_operator_fallback_authorized",
)


OPERATING_SELECTION_CONTRACT = "entry_split_operating_paired_selection_v1"


def _economic_metrics(rows, arm_id):
    arms = [row["arms"][arm_id] for row in rows]
    if not arms:
        return {key: None for key in ("ev_pct", "net_pnl_krw", "p10", "es10", "worst",
            "capital_krw_minutes", "reserve_krw_minutes", "fill_participation", "positive_frequency", "capital_efficiency")}
    returns = sorted(a["net_pnl_krw"] / r["budget_krw"] * 100 for a, r in zip(arms, rows))
    capital = sum(a["capital_krw_minutes"] + a["reserve_krw_minutes"] for a in arms)
    pnl = sum(a["net_pnl_krw"] for a in arms)
    n = max(1, math.ceil(len(arms) * .1))
    return dict(ev_pct=pnl / sum(r["budget_krw"] for r in rows) * 100,
        equal_weight_avg_profit_pct=mean(returns), net_pnl_krw=pnl,
        p10=returns[n-1], es10=mean(returns[:n]), worst=returns[0],
        capital_krw_minutes=sum(a["capital_krw_minutes"] for a in arms),
        reserve_krw_minutes=sum(a["reserve_krw_minutes"] for a in arms),
        fill_participation=mean(a["fill_participation_rate"] for a in arms),
        positive_frequency=sum(a["net_pnl_krw"] > 0 for a in arms) / len(arms),
        capital_efficiency=pnl / capital if capital > 0 else None)


def evaluate_entry_split_operating_economics(rows, model_rows, source_counts, *, target_date, consumed_holdouts=None):
    """Fit once on actual calibration errors, then validate on later dates.

    Candidate calibration/holdout are strictly AFTER model holdout. All metrics
    are recomputed from immutable witnesses by producer and policy consumers.
    """
    from src.engine.scalping.strategy_owner_replay import ENTRY_MODEL_SELECTION
    numeric = lambda x: type(x) in (int, float) and math.isfinite(x)
    output = dict(contract=OPERATING_SELECTION_CONTRACT, status="source_gap",
        valid_no_edge=False, primary_operating_ev_pct=None, robust_paired_delta_ev_lower_bound_pct=None,
        source_date=target_date, candidates=[], model_scopes=[], cohort_checks=[],
        source_counts=source_counts, input_rows=rows, model_rows=model_rows,
        source_gap_owner="entry_execution_sizing_plan->owner_custody_registry->strategy_owner_replay",
        closure_test="same frozen submitted-order scope; independent completed-cost model calibration/holdout followed by complete paired candidate calibration/holdout",
        model_dispositions=dict(Counter(r.get("model_support_status") or r.get("status","source_gap") for r in model_rows)),
        input_dispositions=dict(Counter(a.get("status","source_gap") for r in rows for a in r.get("arms",{}).values())),
        consumed_holdouts=dict(consumed_holdouts or {}), blockers=[],
        metric_role="primary_ev", decision_authority="next_preopen_bounded_entry_split_policy",
        sample_floor={"actual_model":20, "paired_complete":30, "coverage":.8},
        window_policy="frozen_actual_model_calibration_then_model_holdout_then_candidate_calibration_then_latest_source_day_holdout",
        primary_decision_metric="same_frozen_budget_net_ev_and_error_stress_adjusted_paired_lower_bound",
        lower_bound_method="observed_minimum_stressed_paired_net_minus_both_arm_empirical_error_envelopes_not_statistical_confidence_bound",
        source_quality_gate="exact_plan_order_terminal_cost_policy_scope_and_chronological_witnesses",
        forbidden_uses=["actual_profit_claim_from_cf", "increase_quantity_or_budget", "actual_sell_reused_for_cf_exit", "guard_bypass"])
    try:
        if any(date.fromisoformat(day).isoformat()!=day or day < "2026-06-05" or day > target_date
               or type(n) is not int or n < 0 for day,n in source_counts.items()):
            raise ValueError("opportunity_source_census_invalid")
        indexed, conflicts = {}, set()
        for row in rows:
            key=row["attempt_id"]
            if key in indexed and indexed[key]!=row:conflicts.add(key)
            indexed[key]=row
        retained=[r for key,r in indexed.items() if key not in conflicts]
        scopes=sorted({r["scope_sha256"] for r in retained})
        for scope in scopes:
            cohort=[r for r in retained if r["scope_sha256"]==scope]
            actual_index, actual_conflicts={},set()
            for r in model_rows:
                if r.get("scope_sha256")!=scope:continue
                key=r.get("episode_id")
                if not key:continue
                if key in actual_index and actual_index[key]!=r:actual_conflicts.add(key)
                actual_index[key]=r
            actual=[r for key,r in actual_index.items() if key not in actual_conflicts
                and r.get("status") in {"COMPLETED","ORDER_NO_FILL"} and r.get("origin")=="real"
                and r.get("cost_complete") is True and r.get("exact_lineage") is True
                and r.get("owner")=="main_scalping"
                and "2026-06-05" <= str(r.get("source_date")) <= target_date
                and all(numeric(r.get(k)) for k in ("vwap_error_bps", "receipt_clock_error_sec", "quantity_error",
                    "net_error_budget_pct", "capital_error_minutes", "reserve_error_minutes"))]
            declared=[r for key,r in actual_index.items() if key not in actual_conflicts
                and "2026-06-05"<=str(r.get("source_date"))<=target_date]
            model_days=sorted({r["source_date"] for r in declared})
            check=dict(scope_sha256=scope, status="insufficient_sample", blockers=[], candidates=[])
            output["cohort_checks"].append(check)
            if any(r.get("false_fill") is True or r.get("missed_fill") is True
                or r.get("quantity_error") not in (None,0) for r in declared):
                check.update(status="model_validation_failed",blockers=["known_incumbent_false_missed_or_quantity_fill_failure"]);continue
            if len(model_days)<2 or len(actual)<20:
                check["blockers"].append("independent_actual_model_sample_floor");continue
            # Earliest fixed chronological source days establish the model; later
            # candidate dates can never refit the calibration tolerance.
            cal=[r for r in actual if r["source_date"]==model_days[0]]
            held=[r for r in actual if r["source_date"]==model_days[1]]
            if len(cal)+len(held)<20:
                check["blockers"].append("independent_actual_model_sample_floor");continue
            coverage={day:sum(r["source_date"]==day for r in cal+held)/sum(r["source_date"]==day for r in declared) for day in model_days[:2]}
            if any(value<.8 for value in coverage.values()):
                check.update(status="source_gap",blockers=["actual_model_scope_coverage_below_owner_floor"]);continue
            dimensions=("vwap_error_bps", "receipt_clock_error_sec", "quantity_error", "net_error_budget_pct", "capital_error_minutes", "reserve_error_minutes")
            tolerance={k:max(abs(r[k]) for r in cal) for k in dimensions}
            model=dict(contract=ENTRY_MODEL_SELECTION, scope_sha256=scope,
                calibration_dates=[model_days[0]], holdout_dates=[model_days[1]],
                calibration_attempt_count=len(cal), holdout_attempt_count=len(held),
                available_after_date=max(str(r.get("completion_date") or r["source_date"]) for r in cal+held),
                tolerance=tolerance, tolerance_basis="empirical_max_absolute_actual_calibration_error_frozen_before_holdout",
                sample_floor=20, coverage=coverage, actual_rows_sha256=_canonical_sha256(cal+held),
                validated=not any(r.get("false_fill") is not False or r.get("missed_fill") is not False
                    or r["quantity_error"]!=0 or any(abs(r[k]) > tolerance[k]+1e-12 for k in dimensions)
                    for r in held),
                optimistic_net_error_budget_pct=max([0.]+[r["net_error_budget_pct"] for r in held]),
                calibration_rows=cal, holdout_rows=held)
            # Calibration must also satisfy exact quantity/no invented fills.
            model["validated"] &= not any(r.get("false_fill") is not False or r.get("missed_fill") is not False or r["quantity_error"]!=0 for r in cal)
            model["sha256"]=_canonical_sha256(model);output["model_scopes"].append(model)
            if not model["validated"]:
                check.update(status="model_validation_failed",blockers=["independent_incumbent_fidelity_failed"]);continue
            model_episodes={r["episode_id"] for r in cal+held}
            availability=max(str(r.get("completion_date") or r["source_date"]) for r in cal+held)
            candidate_days=sorted(day for day,n in source_counts.items() if n and day>availability)
            if len(candidate_days)<2:
                check["blockers"].append("independent_candidate_holdout_missing");continue
            latest=candidate_days[-1]
            eligible=sum(source_counts[d] for d in candidate_days)
            usable=[]
            for r in cohort:
                if r["source_date"] not in candidate_days or r.get("episode_id") in model_episodes:continue
                if (r.get("origin")!="counterfactual" or r.get("owner")!="main_scalping"
                    or r.get("sha256")!=_canonical_sha256({k:v for k,v in r.items() if k!="sha256"})
                    or not numeric(r.get("budget_krw")) or r["budget_krw"]<=0
                    or set(r.get("arms",{}))!=set(QUANTITY_LEG_FOUR_ARM_IDS)):
                    continue
                declared_template=_entry_operating_input_rows([dict(seed=r.get("seed") or {},operating_arms=r["arms"])])
                valid=bool(declared_template and declared_template[0]["candidate_template"]==r["candidate_template"]
                    and declared_template[0]["scope_sha256"]==scope and declared_template[0]["budget_krw"]==r["budget_krw"])
                for arm in r["arms"].values():
                    if (arm.get("status")!="completed_source_only" or arm.get("actual_fill_evidence") is not False
                        or arm.get("requested_qty")!=r.get("total_qty") or arm.get("budget_krw")!=r["budget_krw"]
                        or any(arm.get(k) is not v for k,v in {"actual_order_submitted":False,"broker_order_forbidden":True,"runtime_effect":False,"allowed_runtime_apply":False}.items())
                        or arm.get("cost_policy_version")!=r["seed"]["operating_contract"].get("cost_policy_version")
                        or arm.get("cost_provenance")!=r["seed"]["operating_contract"].get("cost_provenance")
                        or arm.get("exit_policy_sha256")!=r["seed"]["operating_contract"].get("exit_policy_version")
                        or arm.get("contract_sha256")!=r["seed"]["operating_contract"].get("sha256")
                        or not _valid_generation_id(arm.get("terminal_evidence_sha256"))
                        or any(not numeric(arm.get(k)) for k in ("net_pnl_krw", "stress_net_pnl_krw", "capital_krw_minutes", "reserve_krw_minutes", "fill_participation_rate"))
                        or arm["capital_krw_minutes"]<0 or arm["reserve_krw_minutes"]<0
                        or not 0<=arm["fill_participation_rate"]<=1
                        or arm.get("sha256")!=_canonical_sha256({k:v for k,v in arm.items() if k!="sha256"})):
                        valid=False;break
                if valid:usable.append(r)
            if not usable and eligible:
                dispositions=Counter(a.get("status","source_gap") for r in cohort for a in r.get("arms",{}).values())
                check.update(status="unsupported_scope" if dispositions.get("unsupported_scope") else "pending" if dispositions.get("terminal_pending") else "source_gap",blockers=["paired_operating_support_or_contract_coverage_missing"])
                continue
            checks={}
            # One existing quantity-fixed hypothesis per bucket, selected only on
            # calibration; no second candidate is tried after holdout rejection.
            for bucket in sorted({r["context_bucket"] for r in usable}):
                sample=[r for r in usable if r["context_bucket"]==bucket]
                calibration=[r for r in sample if r["source_date"]<latest]
                holdout=[r for r in sample if r["source_date"]==latest]
                if len(sample)<30 or len(usable)/eligible<.8 or not calibration or not holdout:
                    checks[bucket]=dict(status="source_gap" if eligible and len(usable)/eligible<.8 else "insufficient_sample",blockers=["paired_sample_coverage_or_latest_holdout_floor"]);continue
                identity={_canonical_sha256(r["candidate_template"]) for r in sample}
                if len(identity)!=1:
                    checks[bucket]=dict(status="source_gap",blockers=["paired_candidate_template_conflict"]);continue
                partitions={}
                for name,half in (("calibration",calibration),("holdout",holdout)):
                    i=_economic_metrics(half,QUANTITY_LEG_FOUR_ARM_IDS[0]);c=_economic_metrics(half,QUANTITY_LEG_FOUR_ARM_IDS[2])
                    deltas=[(r["arms"][QUANTITY_LEG_FOUR_ARM_IDS[2]]["net_pnl_krw"]-r["arms"][QUANTITY_LEG_FOUR_ARM_IDS[0]]["net_pnl_krw"])/r["budget_krw"]*100 for r in half]
                    stress=[(r["arms"][QUANTITY_LEG_FOUR_ARM_IDS[2]]["stress_net_pnl_krw"]-r["arms"][QUANTITY_LEG_FOUR_ARM_IDS[0]]["net_pnl_krw"])/r["budget_krw"]*100 for r in half]
                    error=2*max(model["optimistic_net_error_budget_pct"],model["tolerance"]["net_error_budget_pct"])
                    # Conservative observed paired envelope, not a confidence
                    # interval or a proof that incumbent errors cover new scopes.
                    lower=min(deltas+stress)-error
                    blockers=[]
                    for field,predicate in {"ev_pct":lambda c,i:c>=.1 and c>i,
                        "net_pnl_krw":lambda c,i:c>i, "p10":lambda c,i:c>=i,
                        "es10":lambda c,i:c>=i, "worst":lambda c,i:c>=i,
                        "positive_frequency":lambda c,i:c>=i,
                        "fill_participation":lambda c,i:c>=i-.05,
                        "capital_efficiency":lambda c,i:c>=i and c>0}.items():
                        if c[field] is None or i[field] is None or not predicate(c[field],i[field]):blockers.append(field)
                    if lower<=0:blockers.append("robust_paired_lower_bound_nonpositive")
                    partitions[name]=dict(source_dates=sorted({r["source_date"] for r in half}), attempt_count=len(half),
                        incumbent=i,candidate=c,paired_delta_ev_pct=mean(deltas), stress_paired_delta_ev_pct=mean(stress),
                        robust_paired_delta_ev_lower_bound_pct=lower, model_error_penalty_pct=error, blockers=blockers)
                key=_canonical_sha256([scope,bucket,next(iter(identity)),latest])
                witness=_canonical_sha256([model["sha256"],sample])
                previous=output["consumed_holdouts"].get(key)
                blockers=list(partitions["calibration"]["blockers"])
                if not blockers:
                    blockers += ["holdout:"+b for b in partitions["holdout"]["blockers"]]
                    if previous is not None and previous!=witness:blockers.append("candidate_holdout_already_consumed_with_different_input")
                    output["consumed_holdouts"][key]=witness
                status="positive_candidate" if not blockers else "valid_no_edge"
                if any("consumed" in b for b in blockers):status="source_gap"
                candidate=dict(scope_sha256=scope,context_bucket=bucket,status=status,
                    model_contract_sha256=model["sha256"],partitions=partitions,blockers=blockers,
                    sample_count=len(sample),eligible_attempt_count=eligible,coverage=len(usable)/eligible,
                    selected_arm=QUANTITY_LEG_FOUR_ARM_IDS[2],candidate_template=sample[0]["candidate_template"],
                    validated_attempt_sha256s=[r["sha256"] for r in sample],holdout_key=key)
                candidate["sha256"]=_canonical_sha256(candidate);checks[bucket]=candidate
                if not blockers:output["candidates"].append(candidate)
            check["candidates"]=list(checks.values())
            states={c["status"] for c in checks.values()}
            check["status"]="positive_candidate" if "positive_candidate" in states else "source_gap" if "source_gap" in states else "insufficient_sample" if "insufficient_sample" in states or not states else "valid_no_edge"
        if output["candidates"]:
            output["status"]="positive_candidate"
            output["primary_operating_ev_pct"]=min(c["partitions"]["holdout"]["candidate"]["ev_pct"] for c in output["candidates"])
            output["robust_paired_delta_ev_lower_bound_pct"]=min(c["partitions"]["holdout"]["robust_paired_delta_ev_lower_bound_pct"] for c in output["candidates"])
        elif output["cohort_checks"]:
            states={c["status"] for c in output["cohort_checks"]}
            output["status"]="model_validation_failed" if "model_validation_failed" in states else "source_gap" if "source_gap" in states else "unsupported_scope" if "unsupported_scope" in states else "pending" if "pending" in states else "insufficient_sample" if "insufficient_sample" in states else "valid_no_edge"
            output["valid_no_edge"]=states=={"valid_no_edge"}
        measured=[c for check in output["cohort_checks"] for c in check.get("candidates",[]) if c.get("partitions")]
        if measured and not output["candidates"]:
            output["primary_operating_ev_pct"]=min(c["partitions"]["holdout"]["candidate"]["ev_pct"] for c in measured)
            output["robust_paired_delta_ev_lower_bound_pct"]=min(c["partitions"]["holdout"]["robust_paired_delta_ev_lower_bound_pct"] for c in measured)
        if conflicts:output["blockers"].append("conflicting_attempt_quarantined")
        output["blockers"]+=sorted({b for c in output["cohort_checks"] for b in c.get("blockers",[])})
        if not retained:output["blockers"].append("operating_paired_source_missing")
        if not output["candidates"] and output["status"]=="insufficient_sample":
            dispositions=output["input_dispositions"]
            if dispositions.get("source_gap") or output["model_dispositions"].get("source_gap"):output["status"]="source_gap"
            elif dispositions.get("unsupported_scope") or output["model_dispositions"].get("unsupported_scope"):output["status"]="unsupported_scope"
            elif dispositions.get("terminal_pending") or output["model_dispositions"].get("terminal_pending"):output["status"]="pending"
    except (KeyError,ValueError,TypeError,OverflowError) as exc:
        output.update(status="source_gap",candidates=[],valid_no_edge=False)
        output["blockers"].append("operating_contract_invalid:"+str(exc))
    output["sha256"]=_canonical_sha256(output)
    return output


def build_entry_split_post_apply_performance(actual_rows, *, target_date, rolling_days=20):
    """One real completed episode per applied version/scope; no modeled uplift."""
    unique, conflicts={},set()
    for row in actual_rows:
        identity=str(row.get("episode_id") or "")
        if not identity:continue
        if identity in unique and unique[identity]!=row:conflicts.add(identity)
        unique[identity]=row
    numeric=lambda x:type(x) in (int,float) and math.isfinite(x)
    valid=[r for key,r in unique.items() if key not in conflicts and r.get("status")=="COMPLETED"
        and r.get("origin")=="real" and r.get("owner")=="main_scalping" and r.get("cost_complete") is True
        and r.get("exact_lineage") is True and r.get("pid_consumed") is True and r.get("policy_applied") is True
        and r.get("policy_version") and re.fullmatch(r"[a-f0-9]{64}",str(r.get("policy_sha256") or ""))
        and "2026-06-05"<=str(r.get("completion_date"))<=target_date
        and all(numeric(r.get(k)) for k in ("net_pnl_krw","profit_rate","budget_krw"))
        and r["budget_krw"]>0]
    exposure_fields=("capital_krw_minutes", "reserve_krw_minutes")
    exposure_valid=lambda row,key:numeric(row.get(key)) and row[key]>=0
    exposure_gaps=sorted(r["episode_id"] for r in valid if any(not exposure_valid(r,key) for key in exposure_fields))
    dates=sorted({r["completion_date"] for r in valid})
    rolling=set(dates[-rolling_days:]);groups=[]
    for key in sorted({(r["policy_version"],r["policy_sha256"],r["scope_sha256"],r.get("fill_class")) for r in valid}):
        sample=[r for r in valid if (r["policy_version"],r["policy_sha256"],r["scope_sha256"],r.get("fill_class"))==key]
        def metrics(half):
            if not half:return dict(completed_episodes=0,net_pnl_krw=None,cost_adjusted_ev_pct=None,tail=None,exposure=None,model_error=None)
            values=sorted(r["profit_rate"] for r in half);n=max(1,math.ceil(len(values)*.1))
            return dict(completed_episodes=len(half),net_pnl_krw=sum(r["net_pnl_krw"] for r in half),
                cost_adjusted_ev_pct=sum(r["net_pnl_krw"] for r in half)/sum(r["budget_krw"] for r in half)*100,
                equal_weight_avg_profit_pct=mean(values),tail=dict(p10=values[n-1],es10=mean(values[:n]),worst=values[0]),
                exposure=dict(**{key:sum(r[key] for r in half) if all(exposure_valid(r,key) for r in half) else None for key in exposure_fields},
                    covered_episodes={key:sum(exposure_valid(r,key) for r in half) for key in exposure_fields},
                    status="complete" if all(exposure_valid(r,key) for r in half for key in exposure_fields) else "source_gap",
                    owner="owner_custody_registry->entry_split_exact_order_capital_join",
                    closure_test="verified chronological submitted/cumulative-fill/terminal journal through independent completed SELL"),
                model_error=dict(comparable_episodes=sum(numeric(r.get("net_error_budget_pct")) for r in half),
                    mean_signed_budget_pct=mean(r["net_error_budget_pct"] for r in half if numeric(r.get("net_error_budget_pct"))) if any(numeric(r.get("net_error_budget_pct")) for r in half) else None,
                    maximum_absolute_budget_pct=max(abs(r["net_error_budget_pct"]) for r in half if numeric(r.get("net_error_budget_pct"))) if any(numeric(r.get("net_error_budget_pct")) for r in half) else None))
        groups.append(dict(policy_version=key[0],policy_sha256=key[1],scope_sha256=key[2],fill_class=key[3],
            cumulative=metrics(sample),rolling=metrics([r for r in sample if r["completion_date"] in rolling])))
    return dict(status="observed" if valid else "waiting_natural_applied_completed_cost_evidence",
        groups=groups,quarantined_episodes=sorted(conflicts),exposure_gap_episodes=exposure_gaps,rolling_completed_source_days=rolling_days,
        model_delta_ev_is_actual_profit=False,new_incremental_profit_claimed=False)


def _entry_operating_scope(seed):
    from src.engine.lifecycle.avg_down_replay import replay_policy_cohort_digest
    context=seed.get("operating_contract") or {}
    snapshot=dict(context.get("policy_snapshot") or {})
    snapshot["environment"]={k:v for k,v in snapshot.get("environment",{}).items()
        if not k.startswith(("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_","KORSTOCKSCAN_ENTRY_EXECUTION_SIZING_POLICY_"))}
    return _canonical_sha256({"broker_route":context.get("broker_route"),"exit_cohort":context.get("exit_cohort_digest") or replay_policy_cohort_digest(snapshot),
        "cost_version":context.get("cost_policy_version"),"model":"native_full_depth_no_passive_queue_v1",
        "venue":seed.get("effective_venue"),"session":seed.get("session_bucket"),
        "order_types":sorted({x.get("order_type_code") for x in seed.get("legs",[])}),
        "price_policy":seed.get("entry_price_policy_sha256"),
        "model_implementation":context.get("model_implementation_sha256")})


def _compact_operating_seed(seed):
    """Retain economic witnesses; exact snapshots stay in dated native generations.

    This does not replace a frozen interpreter input. Incremental model joins
    need the immutable scope/cost/quantity and incumbent output, not another copy
    of the same full rule blobs for every report section and historical attempt.
    """
    context=seed.get("operating_contract") or {}
    if not context or context.get("exit_cohort_digest"):return seed
    from src.engine.lifecycle.avg_down_replay import replay_policy_cohort_digest
    snapshot=dict(context.get("policy_snapshot") or {})
    snapshot["environment"]={k:v for k,v in snapshot.get("environment",{}).items()
        if not k.startswith(("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_","KORSTOCKSCAN_ENTRY_EXECUTION_SIZING_POLICY_"))}
    witness={k:v for k,v in context.items() if k not in {"policy_snapshot","initial_policy_state"}}
    witness["exit_cohort_digest"]=replay_policy_cohort_digest(snapshot)
    witness["context_bucket"]=context.get("context_bucket") or _context_bucket((context.get("initial_policy_state") or {}).get("stock") or {})
    return {**seed,"operating_contract":witness,"frozen_interpreter_input_role":"original_atomic_seed_and_dated_native_generation_only"}


def _entry_operating_input_rows(replays):
    rows=[]
    from src.trading.order.split_execution_math import split_qty
    for replay in replays:
        seed=replay.get("seed") or {};arms=replay.get("operating_arms") or {}
        if not seed.get("operating_contract") or not arms:continue
        context=seed["operating_contract"];legs=seed.get("candidate_legs") or seed["legs"]
        n=len(legs);base=seed["legs"][0]["price"]
        offsets=[];price=base
        # Only the existing 0/1/2-tick menu is publishable; the price binder
        # remains the sole numeric owner in the future invocation.
        for x in legs:
            offset=next((i for i in range(3) if clamp_price_to_tick(base-i*_tick_size(base))==x["price"]),None)
            if offset is None:break
            offsets.append(offset)
        if len(offsets)!=n or [x["qty"] for x in legs]!=split_qty(seed["total_qty"],n,min(1/n,PASSIVE_CENTER_MAX_FIRST_WEIGHT)):continue
        template=dict(leg_count=n,price_offsets_ticks=offsets,qty_weight_min=min(1/n,PASSIVE_CENTER_MAX_FIRST_WEIGHT),qty_weight_max=min(1/n,PASSIVE_CENTER_MAX_FIRST_WEIGHT),
            urgency_score=0.,passive_edge_score=0.,policy_mode=POLICY_MODE_REAL_PRIMARY_EV,
            candidate_leg_policy_version=seed["candidate_leg_policy_version"],
            effective_venue=seed["effective_venue"],session_bucket=seed["session_bucket"],
            order_types=[x.get("order_type_code") for x in legs])
        row=dict(attempt_id=seed["seed_sha256"],episode_id=seed["plan_sha256"],
            plan_sha256=seed["plan_sha256"],source_date=seed["source_date"],scope_sha256=_entry_operating_scope(seed),
            context_bucket=context.get("context_bucket") or _context_bucket((context.get("initial_policy_state") or {}).get("stock") or {}),
            total_qty=seed["total_qty"],budget_krw=context["budget_krw"],arms=arms,
            candidate_template=template,origin="counterfactual",owner="main_scalping",
            seed=_compact_operating_seed(seed),native_replay_sha256=replay.get("replay_sha256"))
        row["sha256"]=_canonical_sha256(row);rows.append(row)
    return rows


def _bounded_actual_entry_outcomes(target_date):
    try:return _read_bounded_actual_entry_outcomes(target_date)
    except (OSError,ValueError,TypeError,SyntaxError) as exc:
        return [],{"status":"source_gap","path":str(_real_post_sell_candidate_path(target_date)),"reason":str(exc),"sha256":None,
            "owner":"post_sell_completed_cost_receipt","closure_test":"sealed bounded original receipt parse/hash/lineage"}


def _read_bounded_actual_entry_outcomes(target_date):
    path=existing_or_gzip_path(_real_post_sell_candidate_path(target_date))
    if not path.is_file():return [],{"path":str(path),"status":"missing","sha256":None}
    before=path.stat()
    if path.is_symlink() or before.st_size>64*1024*1024:return [],{"path":str(path),"status":"bounded_source_required","sha256":None}
    rows=[];hasher=hashlib.sha256();size=0
    with open_text_auto(path) as handle:
        for line in handle:
            size+=len(line.encode());hasher.update(line.encode())
            if size>64*1024*1024 or not line.endswith("\n"):raise ValueError("actual_entry_outcome_source_unbounded_or_partial")
            row=_event_fields(json.loads(line))
            value=row.get("entry_split_actual_economics")
            if isinstance(value,str):
                import ast
                if len(value)>2*1024*1024:raise ValueError("actual_entry_receipt_too_large")
                try:value=json.loads(value)
                except ValueError:value=ast.literal_eval(value)
            if isinstance(value,dict):rows.append(value)
    after=path.stat()
    if (before.st_ino,before.st_size,before.st_mtime_ns)!=(after.st_ino,after.st_size,after.st_mtime_ns):raise ValueError("actual_entry_outcome_source_changed")
    return rows,{"path":str(path.resolve()),"status":"ready","sha256":hasher.hexdigest()}



def _actual_entry_capital(diagnostic,completed_at):
    """Integrate signed cumulative fills and outstanding reserve independently."""
    terminal=datetime.fromisoformat(completed_at)
    if terminal.utcoffset() is None:raise ValueError("actual_completion_clock_missing")
    capital=reserve=0.
    for leg in diagnostic.get("actual_journal_legs") or []:
        qty=leg["quantity"];price=leg["submitted_price"]
        if type(qty) is not int or qty<=0 or type(price) not in (int,float) or price<=0:raise ValueError("actual_reserve_price_or_quantity_missing")
        clock=datetime.fromisoformat(leg["submitted_at"])
        if clock.utcoffset() is None:raise ValueError("actual_submit_clock_missing")
        previous_qty=0;previous_amount=0.;seen=set()
        for fill in leg["fills"]:
            identity=fill.get("event_hash")
            if identity in seen:continue
            seen.add(identity)
            at=datetime.fromisoformat(fill["observed_at_kst"])
            cumulative=fill["filled_qty"];amount=fill["fill_amount"]
            if at.utcoffset() is None or at<clock or at>terminal or cumulative<previous_qty or cumulative>qty or amount<previous_amount:raise ValueError("actual_fill_conservation_or_clock_invalid")
            reserve+=(qty-previous_qty)*price*(at-clock).total_seconds()/60
            capital+=(amount-previous_amount)*(terminal-at).total_seconds()/60
            clock=at;previous_qty=cumulative;previous_amount=amount
        ended=datetime.fromisoformat(leg["terminal_at"])
        if ended.utcoffset() is None or ended<clock or ended>terminal:raise ValueError("actual_order_terminal_clock_invalid")
        reserve+=(qty-previous_qty)*price*(ended-clock).total_seconds()/60
    if not diagnostic.get("actual_journal_legs"):raise ValueError("actual_capital_journal_missing")
    return capital,reserve

def _attach_operating_model_outcomes(validation,replays,actual_outcomes):
    replay_index={};replay_conflicts=set()
    for replay in replays:
        key=(replay.get("seed") or {}).get("plan_sha256")
        if key in replay_index and replay_index[key]!=replay:replay_conflicts.add(key)
        replay_index[key]=replay
    actual_index={};conflicts=set(replay_conflicts)
    for actual in actual_outcomes:
        key=actual.get("plan_sha256")
        if key in actual_index and actual_index[key]!=actual:conflicts.add(key)
        actual_index[key]=actual
    model_rows=[]
    for diagnostic in validation["rows"]:
        plan=(diagnostic.get("scope") or {}).get("plan_sha256")
        replay=replay_index.get(plan) or {};seed=replay.get("seed") or {}
        actual=actual_index.get(plan) or {};arm=(replay.get("operating_arms") or {}).get(QUANTITY_LEG_FOUR_ARM_IDS[0]) or {}
        if (seed.get("operating_contract") and diagnostic.get("actual_filled_qty")==0
            and diagnostic.get("actual_journal_legs") and arm.get("status")=="completed_source_only"):
            try:
                completed=max(x["terminal_at"] for x in diagnostic["actual_journal_legs"])
                capital,reserve=_actual_entry_capital(diagnostic,completed)
                clock=abs((datetime.fromisoformat(completed)-datetime.fromisoformat(seed["observed_at"])).total_seconds()-seed["research_entry_ttl_sec"])
                model_rows.append(dict(episode_id="no-fill:"+plan,scope_sha256=_entry_operating_scope(seed),source_date=seed["source_date"],
                    completion_date=completed[:10],completed_at=completed,status="ORDER_NO_FILL",origin="real",owner="main_scalping",
                    cost_complete=True,exact_lineage=True,vwap_error_bps=0.,receipt_clock_error_sec=clock,
                    quantity_error=diagnostic["modeled_filled_qty"],false_fill=diagnostic["false_fill"],missed_fill=False,
                    net_error_budget_pct=arm["net_pnl_krw"]/seed["operating_contract"]["budget_krw"]*100,
                    capital_error_minutes=arm["capital_krw_minutes"]-capital,reserve_error_minutes=arm["reserve_krw_minutes"]-reserve,
                    net_pnl_krw=0.,profit_rate=None,cost_provenance="verified_zero_fill_zero_inventory_no_completed_trade_profit_claim"))
                continue
            except (KeyError,ValueError,TypeError):pass
        if (not seed or not actual or plan in conflicts
            or actual.get("sha256")!=_canonical_sha256({k:v for k,v in actual.items() if k!="sha256"})
            or actual.get("source_date")!=seed.get("source_date") or actual.get("scope_sha256")!=_entry_operating_scope(seed)
            or actual.get("entry_qty")!=diagnostic.get("actual_filled_qty")
            or actual.get("cost_complete") is not True or actual.get("exact_lineage") is not True
            or actual.get("origin")!="real" or actual.get("owner")!="main_scalping"
            or actual.get("status")!="COMPLETED" or actual.get("cost_policy_version")!=seed.get("operating_contract",{}).get("cost_policy_version")
            or actual.get("budget_krw")!=seed.get("operating_contract",{}).get("budget_krw")):
            if seed.get("operating_contract"):
                model_rows.append(dict(episode_id=actual.get("episode_id") or plan,scope_sha256=_entry_operating_scope(seed),
                    source_date=seed["source_date"],status="terminal_pending" if not actual else "source_gap",
                    blocker="completed_original_cost_receipt_or_supported_incumbent_join_missing",
                    false_fill=diagnostic.get("false_fill"),missed_fill=diagnostic.get("missed_fill"),
                    quantity_error=diagnostic["modeled_filled_qty"]-diagnostic["actual_filled_qty"]
                        if diagnostic.get("modeled_filled_qty") is not None and diagnostic.get("actual_filled_qty") is not None else None))
            continue
        try:
            if round(actual["actual_entry_vwap"],4)!=round(diagnostic["actual_entry_vwap"],4):
                raise ValueError("actual_initial_entry_vwap_does_not_match_completed_inventory")
        except (KeyError,ValueError,TypeError):
            diagnostic["reason"]="actual_initial_entry_vwap_missing_or_conflicting"
            model_rows.append(dict(episode_id=actual["episode_id"],scope_sha256=_entry_operating_scope(seed),source_date=seed["source_date"],status="source_gap",blocker=diagnostic["reason"]))
            continue
        numeric=lambda x:type(x) in (int,float) and math.isfinite(x)
        if not all(numeric(actual.get(k)) for k in ("net_pnl_krw","profit_rate")):continue
        try:
            capital,reserve=_actual_entry_capital(diagnostic,actual["completed_at"])
            if not all(numeric(x) and x>=0 for x in (capital,reserve)):
                raise ValueError("actual_exposure_nonfinite_or_negative")
        except (KeyError,ValueError,TypeError):
            diagnostic["reason"]="actual_capital_or_reservation_source_missing"
            model_rows.append({**actual,"capital_krw_minutes":None,"reserve_krw_minutes":None,
                "net_error_budget_pct":None,"model_support_status":"source_gap","blocker":diagnostic["reason"]})
            continue
        actual={**actual,"capital_krw_minutes":capital,"reserve_krw_minutes":reserve}
        if arm.get("status")!="completed_source_only":
            model_rows.append({**actual,"net_error_budget_pct":None,"model_support_status":arm.get("status") or "source_gap",
                "blocker":arm.get("blocker") or "incumbent_operating_replay_unsupported"})
            continue
        price=diagnostic.get("actual_entry_vwap");error=diagnostic.get("vwap_error_krw");clock=diagnostic.get("receipt_clock_error_sec")
        if not price or not numeric(error) or not numeric(clock):continue
        value={**actual,"vwap_error_bps":error/price*10000,"receipt_clock_error_sec":clock,
            "quantity_error":diagnostic["modeled_filled_qty"]-diagnostic["actual_filled_qty"],
            "net_error_budget_pct":(arm["net_pnl_krw"]-actual["net_pnl_krw"])/actual["budget_krw"]*100,
            "capital_error_minutes":arm["capital_krw_minutes"]-actual["capital_krw_minutes"],
            "reserve_error_minutes":arm["reserve_krw_minutes"]-actual["reserve_krw_minutes"],
            "false_fill":diagnostic["false_fill"],"missed_fill":diagnostic["missed_fill"],
            "modeled_net_pnl_krw":arm["net_pnl_krw"]}
        model_rows.append(value)
        diagnostic.update(actual_net_pnl_krw=actual["net_pnl_krw"],model_net_error_krw=arm["net_pnl_krw"]-actual["net_pnl_krw"],
            capital_error=value["capital_error_minutes"],reserve_error=value["reserve_error_minutes"],reason="independent_scope_validation_required")
    validation["actual_completed_net_comparable_count"]=sum(type(r.get("net_error_budget_pct")) in (int,float) and math.isfinite(r["net_error_budget_pct"]) for r in model_rows if r.get("status")=="COMPLETED")
    return model_rows


def _operating_owner_source_blockers(validation):
    return ["operating_owner_source_invalid:"+key for key,value in (validation.get("source_contract") or {}).items()
        if isinstance(value,dict) and value.get("status") in {"source_gap","bounded_source_required"}]


def _apply_operating_model_support(validation,economics):
    scopes=[s for s in economics["model_scopes"] if s["validated"]]
    source_blockers=_operating_owner_source_blockers(validation)
    if source_blockers:
        validation.update(status="source_gap",allowed_runtime_apply=False,primary_blockers=source_blockers)
        return validation
    if scopes:
        validation["sample_floor"].update(model_scope_floor=20,model_scope_floor_status="empirical_actual_chronological_owner_contract")
        validation.update(status="validated_scope",allowed_runtime_apply=True,primary_blockers=[],
            validated_scopes=scopes,tolerance_contract={"status":"frozen_actual_calibration","contracts":scopes},
            model_validation_holdout={"status":"validated","contracts":scopes,"candidate_holdout_reusable":False})
    else:
        validation["status"]="model_validation_failed" if economics["status"]=="model_validation_failed" else validation["status"]
    return validation


def _operating_policy(target_date,report_json,economics):
    grid=[]
    for candidate in economics["candidates"]:
        item={**candidate["candidate_template"],"context_bucket":candidate["context_bucket"],"candidate_passed":True,
            "runtime_apply_scope":"ev_optimized_variant","runtime_apply_authority_class":"ev_validated_variant",
            "exploration_seed_allowed":False,"ev_validated_runtime_apply_allowed":True,
            "source_quality_adjusted_ev_pct":candidate["partitions"]["holdout"]["candidate"]["ev_pct"],
            "notional_weighted_ev_pct":candidate["partitions"]["holdout"]["candidate"]["ev_pct"],
            "downside_p10_profit_rate":candidate["partitions"]["holdout"]["candidate"]["p10"],
            "real_sample_count":next(m["calibration_attempt_count"]+m["holdout_attempt_count"] for m in economics["model_scopes"] if m["scope_sha256"]==candidate["scope_sha256"]),
            "real_outcome_joined_sample":next(m["calibration_attempt_count"]+m["holdout_attempt_count"] for m in economics["model_scopes"] if m["scope_sha256"]==candidate["scope_sha256"]),
            "operating_scope_sha256":candidate["scope_sha256"],"operating_selection_sha256":candidate["sha256"]}
        grid.append(item)
    policy=_policy_payload(target_date,report_json,grid)
    for item in grid:
        bucket=policy["buckets"][item["context_bucket"]]
        bucket.update(supported_total_quantities=sorted({r["total_qty"] for r in economics["input_rows"] if r["scope_sha256"]==item["operating_scope_sha256"]}),
            operating_scope_sha256=item["operating_scope_sha256"],
            operating_selection_sha256=item["operating_selection_sha256"],operating_template={key:item[key] for key in
                ("effective_venue","session_bucket","order_types","leg_count","price_offsets_ticks","qty_weight_min","qty_weight_max")})
    policy["selection_leg_template_version"]="entry_split_quantity_fixed_guarded_weights_v1"
    policy["operating_economic_contract"]=OPERATING_SELECTION_CONTRACT
    policy["operating_economic_sha256"]=economics["sha256"]
    return policy,grid


def _operating_economic_policy_valid(report,policy):
    evidence=report.get("economic_acceptance") or {}
    if evidence.get("contract")!=OPERATING_SELECTION_CONTRACT:return False
    from src.engine.scalping.strategy_owner_replay import entry_operating_model_identity
    current=entry_operating_model_identity()
    if policy.get("runtime_apply_allowed") is True and any(
        (r.get("seed",{}).get("operating_contract") or {}).get("model_implementation_sha256")!=current
        for r in evidence.get("input_rows",[]) if r.get("scope_sha256") in {c["scope_sha256"] for c in evidence.get("candidates",[])}):return False
    recomputed=evaluate_entry_split_operating_economics(evidence.get("input_rows") or [],evidence.get("model_rows") or [],
        evidence.get("source_counts") or {},target_date=policy["source_date"],consumed_holdouts=evidence.get("consumed_holdouts") or {})
    source_blockers=_operating_owner_source_blockers(report.get("execution_model_validation") or {})
    if source_blockers:
        recomputed.update(status="source_gap",candidates=[],valid_no_edge=False)
        recomputed["blockers"]+=source_blockers
        recomputed.pop("sha256");recomputed["sha256"]=_canonical_sha256(recomputed)
    # Existing consumed witnesses are idempotent; changed holdout bytes are not.
    events=_operating_four_arm_events(recomputed)
    proof=build_quantity_leg_four_arm_evaluation(events,source_counts={d:n for d,n in recomputed["source_counts"].items()
        if any(s["validated"] and d>s["available_after_date"] for s in recomputed["model_scopes"])})
    if recomputed["candidates"] and not quantity_leg_promotion_evidence_valid(proof):
        recomputed.update(status="source_gap",candidates=[],valid_no_edge=False)
        recomputed["blockers"].append("existing_four_arm_owner_contract_not_passed")
        recomputed.pop("sha256");recomputed["sha256"]=_canonical_sha256(recomputed)
    if recomputed!=evidence or policy.get("operating_economic_sha256")!=evidence.get("sha256"):return False
    if report.get("operating_quantity_leg_four_arm_evaluation") != proof:return False
    if policy.get("runtime_apply_allowed") is not True:return True
    expected,_=_operating_policy(policy["source_date"],Path(policy["source_report"]),evidence)
    if not evidence.get("candidates") or expected["buckets"]!=policy.get("buckets"):return False
    allowed={s["sha256"] for s in (report.get("execution_model_validation") or {}).get("validated_scopes",[]) if s.get("validated") is True}
    return all(c["model_contract_sha256"] in allowed for c in evidence["candidates"])


def _operating_four_arm_events(economics):
    rows=economics.get("input_rows") or []
    scopes={s["scope_sha256"]:s for s in economics.get("model_scopes",[]) if s["validated"]}
    result=[]
    for row in rows:
        model=scopes.get(row["scope_sha256"])
        if not model or row["source_date"]<=model["available_after_date"]:continue
        seed=row.get("seed") or {};context=seed.get("operating_contract") or {}
        if not seed or any(a.get("status")!="completed_source_only" for a in row["arms"].values()):continue
        terminal=max([a.get("modeled_exit_at") or seed["observed_at"] for a in row["arms"].values()])
        common=dict(entry_price_receipt_sha256=seed["entry_price_receipt_sha256"],
            exit_policy_sha256=_canonical_sha256(context["exit_policy_version"]),
            cost_contract_sha256=_canonical_sha256([context["cost_policy_version"],context["cost_provenance"]]),
            terminal_contract_version="full_frozen_holding_initial_only_v1",terminal_observed_at=terminal,
            terminal_conservation_holds=True,cost_complete=True,counterfactual_executable=True)
        arms={key:{**a,**common,"net_return_pct":a["net_pnl_krw"]/row["budget_krw"]*100,
            "capital_krw_minutes":a["capital_krw_minutes"]+a["reserve_krw_minutes"]} for key,a in row["arms"].items()}
        receipt={key:seed[key] for key in ("source_date","scanner_promotion_id","evaluation_attempt_id",
            "stock_code","effective_venue","session_bucket","policy_bundle_sha256",
            "incumbent_quantity_policy_version","candidate_quantity_policy_version",
            "incumbent_leg_policy_version","candidate_leg_policy_version","entry_price_policy_sha256")}
        receipt.update(schema=QUANTITY_LEG_FOUR_ARM_SCHEMA,arms=arms,
            eligible_attempt_count=economics["source_counts"][row["source_date"]],
            operating_row_sha256=row["sha256"])
        receipt["receipt_sha256"]=_canonical_sha256(receipt)
        result.append(dict(source_date=row["source_date"],entry_quantity_leg_four_arm_evaluation=receipt))
    return result


def _previous_operating_state(target_date):
    for path in sorted(REPORT_DIR.glob(f"{REPORT_TYPE}_????-??-??.json"),reverse=True):
        day=path.stem[-10:]
        if day>=target_date or day<"2026-06-05":continue
        if path.is_symlink() or path.stat().st_size>64*1024*1024:continue
        state=(_load_json(path) or {}).get("operating_economic_state") or {}
        if not state:continue
        if state.get("through_date")!=day or state.get("sha256")!=_canonical_sha256({k:v for k,v in state.items() if k!="sha256"}):
            raise ValueError("operating_predecessor_state_hash_or_date_invalid")
        for source,binding in state.get("source_quality_bindings",{}).items():
            quality=_source_quality_summary(source)
            if quality.get("tuning_input_allowed") is not True or _source_quality_contract_sha256(quality)!=binding:
                raise ValueError("operating_predecessor_source_quality_changed:"+source)
        return state
    return {}


def _refresh_operating_economics(report,validation,replay,actual_outcomes,*,target_date,events=(),registry=()):
    if events:
        from src.engine.sniper_missed_entry_counterfactual import _load_entry_events
        from src.engine.scalping.strategy_owner_replay import build_entry_opportunity_replays
        report.setdefault("input_summary", {})["compact_pre_ai_execution_replay"] = build_entry_opportunity_replays(
            target_date, _load_entry_events(target_date, rows=events),
            source_stage="entry_ai_economic_plan_observed")
    predecessor=_previous_operating_state(target_date)
    previous=report.get("operating_economic_state") or predecessor
    if predecessor and previous.get("predecessor_sha256")!=predecessor.get("sha256") and previous is not predecessor:
        previous={**predecessor,"consumed_holdouts":{**predecessor.get("consumed_holdouts",{}),**previous.get("consumed_holdouts",{})},
            "actual_outcomes":predecessor.get("actual_outcomes",[])+[r for r in previous.get("actual_outcomes",[]) if r.get("completion_date")==target_date]}
    if previous.get("sha256") and previous.get("sha256")!=_canonical_sha256({k:v for k,v in previous.items() if k!="sha256"}):
        # A merged predecessor is recomputed below; stored unchanged state must match.
        if not predecessor or previous.get("through_date")==target_date:raise ValueError("operating_current_state_hash_invalid")
    new_rows=_entry_operating_input_rows(replay["rows"])
    old_rows=[r for r in previous.get("rows",[]) if r["source_date"]!=target_date]
    retained_replays=[r for r in previous.get("replays",[]) if (r.get("seed") or {}).get("source_date")!=target_date]+[
        {**r,"seed":_compact_operating_seed(r.get("seed") or {})} for r in replay["rows"]]
    retained_events=[e for e in previous.get("submission_events",[]) if _event_date(_event_fields(e))!=target_date]+[
        {**e,"fields":{k:v for k,v in e.get("fields",{}).items() if k not in {"entry_split_initial_entry_seed","entry_opportunity_replay_seed"}}}
        for e in events if _event_fields(e).get("stage")=="order_leg_sent"]
    outcome_index={r["episode_id"]:r for r in previous.get("actual_outcomes",[])}
    for row in actual_outcomes:
        key=row.get("episode_id")
        if key in outcome_index and outcome_index[key]!=row:
            # Keep both; exact episode disagreement is quarantined downstream.
            outcome_index[key+":conflict:"+_canonical_sha256(row)]=row
        else:outcome_index[key]=row
    actual=list(outcome_index.values())
    if events or registry:
        validation=build_execution_model_validation(target_date,retained_events,retained_replays,registry,
            source_contract=validation.get("source_contract"))
    model_rows=_attach_operating_model_outcomes(validation,retained_replays,actual)
    # Existing exact completed witnesses survive a later journal projection gap.
    old_models=[r for r in previous.get("model_rows",[]) if r["episode_id"] not in {m["episode_id"] for m in model_rows}
        and r.get("plan_sha256") not in {m.get("plan_sha256") for m in model_rows if m.get("plan_sha256")}]
    census=replay["counts"]
    unique_census=census.get("unique_retained",census["raw_plan_rows"])+sum(census.get("excluded",{}).get(k,0) for k in ("original_plan_or_frozen_seed_missing_or_invalid","conflicting_exact_plan"))
    counts={**previous.get("source_counts",{}),target_date:unique_census}
    economics=evaluate_entry_split_operating_economics(old_rows+new_rows,old_models+model_rows,counts,
        target_date=target_date,consumed_holdouts=previous.get("consumed_holdouts") or {})
    validation=_apply_operating_model_support(validation,economics)
    source_blockers=_operating_owner_source_blockers(validation)
    if source_blockers:
        economics.update(status="source_gap",candidates=[],valid_no_edge=False)
        economics["blockers"]+=source_blockers
        economics.pop("sha256");economics["sha256"]=_canonical_sha256(economics)
    bindings={**previous.get("source_quality_bindings",{}),target_date:_source_quality_contract_sha256(_source_quality_summary(target_date))}
    state=dict(through_date=target_date,predecessor_sha256=predecessor.get("sha256"),rows=old_rows+new_rows,model_rows=old_models+model_rows,
        replays=retained_replays,submission_events=retained_events,actual_outcomes=actual,
        source_quality_bindings=bindings,source_counts=counts,consumed_holdouts=economics["consumed_holdouts"])
    state["sha256"]=_canonical_sha256(state)
    report["operating_economic_state"]=state
    report["economic_acceptance"]=economics
    report["post_apply_version_performance"]=build_entry_split_post_apply_performance(old_models+model_rows,target_date=target_date)
    events=_operating_four_arm_events(economics)
    proof=build_quantity_leg_four_arm_evaluation(events,source_counts={d:n for d,n in counts.items()
        if any(s["validated"] and d>s["available_after_date"] for s in economics["model_scopes"])})
    report["operating_quantity_leg_four_arm_evaluation"]=proof
    report["operating_quantity_leg_four_arm_events"]=events
    if economics["candidates"] and not quantity_leg_promotion_evidence_valid(proof):
        economics.update(status="source_gap",candidates=[],valid_no_edge=False)
        economics["blockers"].append("existing_four_arm_owner_contract_not_passed")
        economics.pop("sha256",None);economics["sha256"]=_canonical_sha256(economics)
    return validation,economics

EXECUTION_MODEL_CONTRACT = "entry_split_execution_model_validation_v1"
EXECUTION_SOURCE_STAGES = frozenset({
    "entry_execution_sizing_plan", "entry_execution_sizing_plan_block",
    "entry_ai_economic_plan_observed", "entry_ai_economic_source_gap",
    "entry_ai_economic_decision_available",
    "entry_quantity_leg_four_arm_evaluation", "order_leg_sent", "order_leg_fail",
    "order_leg_no_response", "order_bundle_submitted", "order_bundle_failed",
})


def _execution_projection_census(target_date, events):
    """Reconcile retained raw identities against the existing producer census."""
    from src.engine.pipeline_event_summary import (producer_summary_paths,
        EXECUTION_SUMMARY_STAGES, IDENTITY_CONTRACT, IDENTITY_MODULUS, execution_projection_identity)
    directory = DATA_DIR / "pipeline_event_summaries"
    path, manifest_path = producer_summary_paths(directory, target_date)
    manifest = _load_json(manifest_path) or {}
    if (not EXECUTION_SUMMARY_STAGES <= set(manifest.get("summary_stages") or [])
        or manifest.get("identity_contract") != IDENTITY_CONTRACT or not path.is_file()):
        return {"status": "source_gap", "reason": "execution_producer_census_missing",
                "coverage_scope": "declared_execution_stage_producer_census"}
    before = path.stat()
    if path.is_symlink() or before.st_size > 64 * 1024 * 1024 or manifest.get("summary_storage_size_bytes") != before.st_size:
        return {"status": "source_gap", "reason": "execution_producer_census_unsealed"}
    expected = Counter(); expected_hash = Counter()
    for row in iter_jsonl(path):
        stage = row.get("stage")
        if stage not in EXECUTION_SUMMARY_STAGES:
            continue
        if row.get("target_date") != target_date or row.get("identity_contract") != IDENTITY_CONTRACT:
            raise ValueError("execution_producer_census_contract_invalid")
        if row.get("execution_projection_identity_contract") != "lossless_execution_projection_v1":
            raise ValueError("execution_producer_lossless_identity_missing")
        expected[stage] += int(row["event_count"])
        expected_hash[stage] = (expected_hash[stage] + int(row["execution_projection_hash_sum"], 16)) % IDENTITY_MODULUS
    observed = Counter(); observed_hash = Counter(); missing = 0
    for event in events:
        stage = event["stage"]
        observed[stage] += 1
        value = event.get("execution_source_event_sha256")
        if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
            missing += 1
        else:
            if value != execution_projection_identity(event):
                raise ValueError("execution_projection_content_identity_mismatch")
            observed_hash[stage] = (observed_hash[stage] + int(value, 16)) % IDENTITY_MODULUS
    after = path.stat()
    if (before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_ino, after.st_size, after.st_mtime_ns) or manifest != (_load_json(manifest_path) or {}):
        raise ValueError("execution_producer_census_changed")
    ready = not missing and expected == observed and expected_hash == observed_hash
    return {"status": "ready" if ready else "source_gap",
        "reason": None if ready else "execution_projection_census_mismatch",
        "expected_stage_counts": dict(expected), "observed_stage_counts": dict(observed),
        "missing_identity_count": missing, "identity_conservation_holds": ready,
        "manifest_sha256": _canonical_sha256(manifest),
        "coverage_scope": "declared_execution_stage_producer_census"}


def _bounded_execution_projection(target_date: str):
    """Use the existing compact family; never silently scan a multi-GB day."""
    directory = DATA_DIR / "threshold_cycle" / f"date={target_date}" / "family=dynamic_entry_price_resolver"
    partition_paths = sorted(directory.glob("part-*.jsonl*"))
    flat_path = existing_or_gzip_path(_threshold_events_path(target_date))
    flat_available = flat_path.is_file() and flat_path.stat().st_size <= 64 * 1024 * 1024
    paths = ([flat_path] if flat_available else []) + partition_paths
    rows, identities, sources = [], {}, []
    total_bytes = 0
    for path in paths:
        before = path.stat()
        if path.is_symlink():
            raise ValueError("execution_partition_final_symlink")
        if before.st_size > 64 * 1024 * 1024:
            return [], {"status": "source_gap", "reason": "bounded_execution_partition_required"}
        hasher = hashlib.sha256()
        with open_text_auto(path) as handle:
            for line in handle:
                total_bytes += len(line.encode())
                if total_bytes > 64 * 1024 * 1024:
                    raise ValueError("execution_partition_decoded_byte_budget_exceeded")
                hasher.update(line.encode())
                if not line.endswith("\n"):
                    raise ValueError("execution_partition_incomplete_line")
                event = json.loads(line)
                if event.get("stage") not in EXECUTION_SOURCE_STAGES:
                    continue
                if event.get("emitted_date") != target_date:
                    raise ValueError("execution_partition_date_mismatch")
                identity = _canonical_sha256({key: event.get(key) for key in
                    ("stage", "pipeline", "stock_code", "record_id", "emitted_at", "fields")})
                if identity not in identities:
                    identities[identity] = event
                    rows.append(event)
        after = path.stat()
        if (before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_ino, after.st_size, after.st_mtime_ns):
            raise ValueError("execution_partition_changed_during_read")
        sources.append({"path": str(path.resolve()), "sha256": hasher.hexdigest()})
    if sorted(directory.glob("part-*.jsonl*")) != partition_paths:
        raise ValueError("execution_partition_inventory_changed_during_read")
    census = _execution_projection_census(target_date, rows)
    ready = census["status"] == "ready"
    # Pre-contract partitions never imply an empty raw opportunity population.
    return rows, {"status": "ready" if ready else "source_gap",
        "reason": None if ready else ("execution_compact_coverage_unproven" if not rows else census["reason"]),
        "full_population_coverage_verified": ready,
        "coverage_scope": "declared_execution_stage_producer_census",
        "producer_census": census,
        "sources": sources, "retained_event_count": len(rows),
        "raw_not_read": True, "flat_compact_included": flat_available,
        "projection_contract": EXECUTION_MODEL_CONTRACT}


def _entry_replay_maturity_revision(events, *, now):
    import ast
    from src.engine.scalping.strategy_owner_replay import ENTRY_REPLAY_EXIT
    revision = set()
    for event in events:
        try:
            seed = _event_fields(event).get("entry_opportunity_replay_seed")
            if isinstance(seed, str):
                try:
                    seed = json.loads(seed)
                except ValueError:
                    seed = ast.literal_eval(seed)
            if isinstance(seed, dict):
                observed = datetime.fromisoformat(seed["observed_at"])
                if observed.utcoffset() is not None:
                    revision.add((str(seed.get("seed_sha256")), observed.timestamp() + ENTRY_REPLAY_EXIT["horizon_sec"] <= now))
        except (KeyError, TypeError, ValueError, SyntaxError, OverflowError):
            continue  # Invalid seeds cannot become ready merely as time passes.
    return sorted(revision)


def _execution_registry_snapshot():
    from src.trading.order.owner_custody_registry import OrderOwnerRegistry, OwnerRegistryError
    try:
        events = OrderOwnerRegistry().verified_events_snapshot()
        return events, {"status": "verified", "tail_hash": events[-1]["event_hash"] if events else "0" * 64}
    except (OwnerRegistryError, OSError) as exc:
        return [], {"status": "source_gap", "reason": str(exc)}


def build_execution_model_validation(target_date, events, replays, registry_events, *, source_contract=None):
    """Compare the incumbent model to exact owner receipts, not selected winners."""
    target = date.fromisoformat(target_date)
    submitted = {}
    conflicts = set()
    def order_key(fields):
        source_date = str(fields.get("order_date") or fields.get("source_date")
            or fields.get("emitted_date") or fields.get("date") or fields.get("emitted_at") or "")[:10]
        return source_date, str(fields.get("broker_order_no") or fields.get("ord_no") or "").strip()
    def submission_identity(fields):
        return tuple(str(fields.get(key) or "") for key in (
            "entry_execution_sizing_plan_id", "entry_execution_sizing_plan_sha256",
            "entry_execution_sizing_action_receipt_id", "stock_code", "submitted_qty",
            "requested_qty", "effective_venue", "market_session_bucket"))
    for event in events:
        fields = _event_fields(event)
        if fields.get("stage") != "order_leg_sent" or not _safe_bool(fields.get("actual_order_submitted")):
            continue
        order_no = order_key(fields)
        if not order_no[1] or not order_no[0]:
            continue
        if order_no in submitted and submission_identity(submitted[order_no]) != submission_identity(fields):
            conflicts.add(order_no)
        submitted[order_no] = fields
    inventory, fills, bound = {}, defaultdict(list), set()
    for event in registry_events:
        if (event.get("side") != "BUY" or event.get("action") != "NEW"
                or event.get("owner_type") != "main_scalping"
                or not "2026-06-05" <= str(event.get("order_date") or "") <= target_date):
            continue
        identity = str(event.get("intent_id") or "")
        if not identity:
            continue
        inventory.setdefault(identity, {}).update(event)
        if event.get("event") == "ORDER_BOUND":
            bound.add(identity)
        if event.get("event") == "FILL_RECORDED":
            fills[identity].append(event)
    replay_index = {}
    replay_conflicts = set()
    for row in replays:
        seed = row.get("seed") or {}
        identity = seed.get("plan_sha256")
        if identity:
            if identity in replay_index and replay_index[identity] != row:
                replay_conflicts.add(identity)
                replay_index[identity] = None
            elif identity not in replay_conflicts:
                replay_index[identity] = row
    account_scopes = defaultdict(set)
    for actual in inventory.values():
        if actual.get("broker_order_no"):
            account_scopes[order_key(actual)].add(actual.get("account_key"))
    conflicts.update(key for key, accounts in account_scopes.items() if len(accounts) != 1)
    parents = defaultdict(list)
    for identity, actual in inventory.items():
        # Unbound rejected/ambiguous attempts remain in the actual census too.
        fields = submitted.get(order_key(actual)) or {}
        parent = str(fields.get("entry_execution_sizing_plan_id") or f"unjoined:{identity}")
        parents[parent].append((identity, actual, fields))
    results, optimistic_errors = [], []
    for parent, legs in sorted(parents.items()):
        entry = {"parent_id": parent, "order_intent_ids": [x[0] for x in legs],
            "source_dates": sorted({str(x[1].get("order_date")) for x in legs}),
            "actual_net_pnl_krw": None, "model_net_error_krw": None,
            "capital_error": None, "reason": None,
            "cohort": "initial_entry_atomic_join" if not parent.startswith("unjoined:") else "unclassified_main_buy_not_assumed_initial_entry"}
        plan_hashes = {str(x[2].get("entry_execution_sizing_plan_sha256") or "") for x in legs}
        if (any(not fields for _, _, fields in legs) or len(plan_hashes) != 1
                or not re.fullmatch(r"[0-9a-f]{64}", next(iter(plan_hashes), ""))
                or any(order_key(actual) in conflicts for _, actual, _ in legs)):
            entry.update(status="source_gap", reason="exact_parent_plan_order_join_missing_or_conflicting")
        elif any(actual.get("state") not in {"ORDER_TERMINAL", "INTENT_REJECTED"} for _, actual, _ in legs):
            entry.update(status="terminal_pending", reason="actual_order_terminal_pending")
        else:
            modeled = replay_index.get(next(iter(plan_hashes)))
            arm = (modeled or {}).get("incumbent_execution_arm") or {}
            expected = sum(_safe_int(actual.get("quantity"), 0) for _, actual, _ in legs)
            actual_qty = sum(_safe_int(actual.get("filled_qty"), 0) for _, actual, _ in legs)
            actual_amount = sum(_safe_float(actual.get("fill_amount"), 0.) for _, actual, _ in legs)
            seed = (modeled or {}).get("seed") or {}
            if (not modeled or modeled.get("status") != "completed_source_only"
                    or seed.get("total_qty") != expected
                    or any(actual.get("symbol") != seed.get("stock_code")
                        or fields.get("effective_venue") != seed.get("effective_venue")
                        or fields.get("market_session_bucket") != seed.get("session_bucket")
                        or _safe_int(fields.get("submitted_qty"), -1) != actual.get("quantity")
                        for _, actual, fields in legs)
                    or not arm or expected <= 0 or actual_qty > expected or actual_qty < 0
                    or not math.isfinite(actual_amount)
                    or (actual_qty > 0 and actual_amount <= 0)
                    or (actual_qty == 0 and actual_amount != 0)):
                entry.update(status="source_gap", reason="incumbent_replay_or_actual_economics_unproven")
            else:
                modeled_qty = arm.get("modeled_filled_qty")
                modeled_price = arm.get("modeled_entry_vwap")
                actual_price = actual_amount / actual_qty if actual_qty else None
                model_times = [arm.get("modeled_entry_at"), arm.get("modeled_last_fill_at")]
                actual_times = sorted(e.get("observed_at_kst", "") for identity, _, _ in legs for e in fills[identity])
                clock_error = None
                if actual_qty and actual_times and all(model_times):
                    try:
                        pairs = [(datetime.fromisoformat(a), datetime.fromisoformat(b))
                            for a, b in zip((actual_times[0], actual_times[-1]), model_times)]
                        if all(a.utcoffset() is not None and b.utcoffset() is not None for a, b in pairs):
                            clock_error = max(abs((a - b).total_seconds()) for a, b in pairs)
                    except (TypeError, ValueError, OverflowError):
                        pass
                price_error = modeled_price - actual_price if actual_price and type(modeled_price) in (int, float) else None
                quantity_matches = type(modeled_qty) is int and modeled_qty == actual_qty
                # Quote continuity is not a broker fill-clock tolerance. Until a
                # scope owner freezes tolerances, retain errors without a PASS.
                diagnostic_ready = quantity_matches and (not actual_qty or
                    (price_error is not None and math.isfinite(price_error) and clock_error is not None))
                entry.update(status="ready_for_validation" if diagnostic_ready else "validation_failed",
                    reason="tolerance_contract_missing" if diagnostic_ready else "incumbent_fill_quantity_price_or_receipt_clock_mismatch",
                    requested_qty=expected, actual_filled_qty=actual_qty, modeled_filled_qty=modeled_qty,
                    actual_entry_vwap=actual_price, modeled_entry_vwap=modeled_price,
                    vwap_error_krw=price_error, receipt_clock_error_sec=clock_error,
                    false_fill=bool(modeled_qty and not actual_qty), missed_fill=bool(actual_qty and not modeled_qty),
                    actual_journal_legs=[dict(quantity=actual.get("quantity"),submitted_price=_safe_float(fields.get("entry_split_submitted_price"),None),
                        submitted_at=fields.get("entry_split_submitted_at"),terminal_at=actual.get("observed_at_kst"),fills=fills[identity]) for identity,actual,fields in legs],
                    scope={"venue": seed.get("effective_venue"), "session": seed.get("session_bucket"),
                        "model": (modeled or {}).get("schema"), "plan_sha256": seed.get("plan_sha256")})
                if price_error is not None:
                    optimistic_errors.append(max(0., -price_error * actual_qty))
        results.append(entry)
    counts = Counter(row["status"] for row in results)
    diagnostics = [row for row in results if row.get("modeled_filled_qty") is not None]
    confusion = {key: sum(row.get(key) is True for row in diagnostics) for key in ("false_fill", "missed_fill")}
    return {"contract_version": EXECUTION_MODEL_CONTRACT, "source_date": target.isoformat(),
        "metric_role": "execution_quality_real_only", "decision_authority": "model_support_gate_only",
        "sample_floor": {"real_outcome_owner_floor": 20, "four_arm_complete_owner_floor": 30,
            "model_scope_floor": 20, "model_scope_floor_status": "defined_requires_independent_actual_scope_validation"},
        "model_version":"entry_split_empirical_model_holdout_v1",
        "support_scope":{"owner":"main_scalping","native_fill":"full_marketability_and_full_depth_at_each_frozen_arrival",
            "exit":"unchanged_isolated_full_holding_policy_initial_inventory_only",
            "unsupported":["passive_queue_or_unknown_partial_fill","unacknowledged_cf_cancel_or_late_fill","subsequent_add_or_partial_sell","missing_state_specific_ai_or_market_input"]},
        "primary_decision_metric": "signed_incumbent_execution_error_not_research_ev",
        "source_quality_gate": "verified_owner_journal_exact_frozen_plan_order_scope_terminal_join",
        "forbidden_uses": ["standalone_live_promotion", "research_exit_as_actual_net_pnl",
            "increase_quantity_or_budget", "replace_missing_outcomes_with_zero", "guard_or_operator_bypass"],
        "window_policy": "clean_baseline_main_buy_inventory_initial_cohort_requires_atomic_join",
        "actual_attempt_count": len(results), "actual_order_intent_count": len(inventory),
        "actual_census_scope": "verified_owner_journal_only_not_complete_historical_main_orders",
        "full_actual_attempt_count": None,
        "submitted_order_intent_count": len(bound), "counts": dict(counts), "rows": results,
        "census_conserved": sum(counts.values()) == len(results),
        "fill_confusion_counts": confusion,
        "actual_completed_net_comparable_count": 0,
        "source_contract": source_contract or {},
        "tolerance_contract": {"status": "missing", "owner": "entry_split_execution_model_scope",
            "clock_role": "receipt_observation_clock_not_exchange_clock",
            "quote_continuity_is_not_fill_tolerance": True},
        "initial_entry_joined_parent_count": sum(not x["parent_id"].startswith("unjoined:") for x in results),
        "unclassified_main_buy_parent_count": sum(x["parent_id"].startswith("unjoined:") for x in results),
        "model_validation_holdout": {"status": "missing", "calibration_dates": [], "holdout_dates": [],
            "candidate_holdout_reusable": False},
        "maximum_observed_optimistic_entry_cost_error_krw": max(optimistic_errors) if optimistic_errors else None,
        "actual_net_ev_pct": None, "model_net_error_krw": None, "tail": None, "exposure": None,
        "status": "source_gap", "allowed_runtime_apply": False,
        "primary_blockers": ([((source_contract or {}).get("projection") or {}).get("reason")]
            if ((source_contract or {}).get("projection") or {}).get("status") == "source_gap" else [])
            + ["tolerance_contract_missing", "operating_exit_cost_capital_replay_unvalidated", "independent_model_holdout_missing"]
            + (["actual_main_buy_attempts_missing"] if not inventory else []),
        "source_gap_owner": "entry_execution_sizing_plan->owner_custody_registry->strategy_owner_replay",
        "closure_test": "exact frozen parent/attempt->broker order->terminal fill; incumbent fidelity and independent operating exit/cost/capital validation",
        "eta": None}


def execution_model_policy_contract_status(report, policy):
    section = report.get("execution_model_validation")
    marker = policy.get("execution_model_validation_contract")
    if marker != EXECUTION_MODEL_CONTRACT or not isinstance(section, dict):
        return False, "execution_model_validation_contract_missing"
    if (section.get("contract_version") != marker or section.get("source_date") != policy.get("source_date")
            or policy.get("execution_model_validation_sha256") != _canonical_sha256(section)):
        return False, "execution_model_validation_hash_or_date_invalid"
    if policy.get("runtime_apply_allowed") is True:
        if section.get("allowed_runtime_apply") is not True or not _operating_economic_policy_valid(report, policy):
            return False, "operating_execution_model_not_validated"
        return True, "validated_operating_execution_model_and_independent_paired_economics"
    if section.get("allowed_runtime_apply") is not False and not _operating_economic_policy_valid(report, policy):
        return False, "execution_model_authority_invalid"
    return True, "validated_inactive_execution_model_disposition"


def refresh_execution_model_only(target_date, *, prepared_effective_date=None, write=True):
    import fcntl
    date.fromisoformat(target_date)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    with (REPORT_DIR / f".entry_split_model_refresh_{target_date}.lock").open("a") as lock:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError("entry_split_model_refresh_already_running") from exc
        return _refresh_execution_model_only(target_date, prepared_effective_date=prepared_effective_date, write=write)


def _refresh_execution_model_only(target_date, *, prepared_effective_date=None, write=True):
    """Bounded subsection successor; preserve original as-of and cumulative inputs."""
    json_path, md_path = report_paths(target_date)
    if not json_path.is_file() or json_path.stat().st_size > 64 * 1024 * 1024:
        raise ValueError("bounded_entry_split_predecessor_missing")
    predecessor_bytes = json_path.read_bytes()
    report = json.loads(predecessor_bytes)
    if report.get("date") != target_date:
        raise ValueError("entry_split_predecessor_date_invalid")
    prepared_effective_date = prepared_effective_date or report.get("recommended_policy", {}).get("prepared_effective_date")
    if prepared_effective_date is not None:
        if date.fromisoformat(prepared_effective_date).isoformat() != prepared_effective_date or prepared_effective_date <= target_date:
            raise ValueError("entry_split_prepared_effective_date_invalid")
    try:
        events, projection = _bounded_execution_projection(target_date)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        events, projection = [], dict(status="source_gap",reason=str(exc),raw_not_read=True,
            full_population_coverage_verified=False,owner="existing_execution_projection_and_producer_census",
            closure_test="atomic_date_hash_census_conservation_before_model_or_policy_consumption")
    actual_outcomes, actual_source = _bounded_actual_entry_outcomes(target_date)
    registry, registry_contract = _execution_registry_snapshot()
    from src.engine.sniper_missed_entry_counterfactual import _load_entry_events
    from src.engine.scalping.strategy_owner_replay import build_entry_opportunity_replays
    from src.engine.monitoring import machine_microstructure_attribution as micro
    native_generation = micro._source_generation_contract({}, extra_paths=[
        micro.OBSERVATION_ROOT / f"trade_date={target_date}", micro.DEFAULT_SOURCE_EXCLUSION_MANIFEST,
        micro.DEFAULT_CANARY_SNAPSHOT_PATH, micro.daily_canary_snapshot_path(date.fromisoformat(target_date), root=micro.CANARY_DAILY_SNAPSHOT_DIR)])
    implementation = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in
        (Path(__file__), Path(__file__).with_name("strategy_owner_replay.py"))}
    predecessor=_previous_operating_state(target_date)
    precheck_sha256 = _canonical_sha256({"operating_predecessor_sha256":predecessor.get("sha256"),"projection": projection, "registry": registry_contract,
        "actual_events": registry, "actual_outcomes": actual_source, "model": implementation, "native_source": native_generation,
        "effective_date": prepared_effective_date, "clean_baseline": clean_baseline_policy(),
        "source_quality": _source_quality_summary(target_date),
        "maturity": _entry_replay_maturity_revision(events, now=datetime.now(timezone.utc).timestamp())})
    prior = report.get("execution_model_refresh") or {}
    if prior.get("precheck_sha256") == precheck_sha256:
        current_policy = _load_json(policy_path(target_date))
        immutable_policy = generation_policy_snapshot_path(report)
        if (not validate_report_policy_generation(report, current_policy)[0]
                or not policy_report_generation_contract_status(current_policy)[0]
                or immutable_policy is None or not immutable_policy.is_file()
                or _load_json(immutable_policy) != current_policy):
            raise ValueError("execution_model_cached_generation_invalid")
        return report
    native = _load_entry_events(target_date, rows=events)
    replay = build_entry_opportunity_replays(target_date, native)
    validation = build_execution_model_validation(target_date, events, replay["rows"], registry,
        source_contract={"projection": projection, "registry": registry_contract,"actual_outcomes":actual_source})
    validation, economics = _refresh_operating_economics(report, validation, replay, actual_outcomes, target_date=target_date,events=events,registry=registry)
    fingerprint = _canonical_sha256({"model_revision": 2, "validation": validation,
        "replay": replay, "effective_date": prepared_effective_date})
    prior = report.get("execution_model_refresh") or {}
    validation["source_inventory"] = {
        "original_atomic_contract": report.get("input_summary", {}).get("atomic_execution_sizing"),
        "original_native_replay_counts": report.get("input_summary", {}).get("daily_diagnostic", {}).get("entry_opportunity_executable_replay", {}).get("counts"),
        "historical_invalid_row_first_reason": "unknown_not_reconstructed_from_lossy_projection",
        "original_parent_asof": report.get("generated_at"),
        "projection_gap_is_not_zero_opportunity": True,
    }
    # The inventory is immutable predecessor context and belongs in reuse identity.
    fingerprint = _canonical_sha256({"input": fingerprint, "inventory": validation["source_inventory"]})
    report["execution_model_validation"] = validation
    report["execution_model_refresh"] = {"input_sha256": fingerprint,
        "generated_at": datetime.now(timezone(timedelta(hours=9))).isoformat(),
        "phase": "postclose", "raw_not_read": True, "parent_asof_preserved": True,
        "precheck_sha256": precheck_sha256, "native_source_generation": native_generation,
        "model_implementation_sha256": implementation}
    report["input_summary"]["entry_opportunity_executable_replay_refresh"] = replay
    policy, operating_grid = _operating_policy(target_date, json_path, economics)
    report["operating_candidate_grid"] = operating_grid
    policy["policy_version"] = f"entry_split_order_plan:{target_date}:{_canonical_sha256([validation,economics])[:10]}"
    policy.update(execution_model_validation_contract=EXECUTION_MODEL_CONTRACT,
        execution_model_validation_sha256=_canonical_sha256(validation),
        prepared_effective_date=prepared_effective_date,
        execution_model_disposition=validation["status"], primary_economic_blockers=validation["primary_blockers"])
    recommended = report["recommended_policy"]
    report["execution_model_refresh"]["prior_recommendation_preserved_for_audit"] = dict(recommended)
    for key in ("runtime_apply_allowed", "exploration_seed_allowed", "ev_validated_runtime_apply_allowed", "baseline_runtime_defaults_enabled"):
        recommended[key] = False
    for key in ("candidate_count", "exploration_seed_count", "ev_validated_bucket_count", "explicit_bucket_count"):
        recommended[key] = 0
    recommended.update(candidates=[], runtime_apply_scope=[], runtime_apply_authority_classes=[],
        missing_bucket_action="keep_original_order", policy_version=policy["policy_version"],
        execution_model_validation_contract=EXECUTION_MODEL_CONTRACT,
        execution_model_validation_sha256=policy["execution_model_validation_sha256"],
        execution_model_disposition=validation["status"], prepared_effective_date=prepared_effective_date)
    recommended.update({key:policy[key] for key in ("runtime_apply_allowed","exploration_seed_allowed","exploration_seed_count","ev_validated_runtime_apply_allowed","ev_validated_bucket_count","explicit_bucket_count","runtime_apply_scope","runtime_apply_authority_classes","missing_bucket_action","policy_version")})
    recommended.update(candidate_count=len(operating_grid),candidates=operating_grid,policy_file=str(policy_path(target_date)),operating_economic_sha256=economics["sha256"])
    report, policy = bind_report_policy_generation(report, policy)
    valid, reason = validate_report_policy_generation(report, policy)
    if not valid:
        raise ValueError(reason)
    if write:
        if json_path.read_bytes() != predecessor_bytes:
            raise ValueError("entry_split_predecessor_changed_during_refresh")
        generation = report["artifact_generation_binding"]["generation_id"]
        _write_immutable_json(generation_report_path(target_date, generation), report)
        _write_immutable_json(generation_policy_path(target_date, generation), policy)
        _write_json(json_path, report)
        _write_json(policy_path(target_date), policy)
        md_path.write_text(_render_markdown(report), encoding="utf-8")
    return report


def build_report(target_date: str, *, write: bool = True) -> dict[str, Any]:
    target_date = str(target_date).strip()
    predecessor = report_paths(target_date)[0]
    if target_date >= "2026-09-17" and predecessor.is_file():
        if predecessor.stat().st_size > 64 * 1024 * 1024:
            raise ValueError("bounded_entry_split_predecessor_required")
        prior_report = _load_json(predecessor)
        if prior_report.get("date") == target_date and prior_report.get("cumulative_state"):
            # The research-only kernel cannot establish primary operating EV.
            # Refresh exact execution revisions without re-running its grid.
            return refresh_execution_model_only(target_date, write=write)
    source_quality = _source_quality_summary(target_date)
    daily_events, daily_load_summary = _iter_input_events(target_date)
    from src.engine.scalping.strategy_owner_replay import build_entry_opportunity_replays
    executable_replay = build_entry_opportunity_replays(target_date,
        daily_load_summary.pop("_entry_opportunity_plan_events", []))
    daily_load_summary["entry_opportunity_executable_replay"] = executable_replay
    daily_events.extend(executable_replay["quantity_leg_events"])
    daily_allowed_events, daily_excluded_source_quality = (
        _source_quality_filtered_events(daily_events, {target_date: source_quality})
    )
    daily_counts, _ = _quality_counts(
        daily_allowed_events, {"tuning_input_allowed": True}
    )
    daily_four_arm_events = [
        event
        for event in daily_allowed_events
        if isinstance(event.get("entry_quantity_leg_four_arm_evaluation"), dict)
    ]
    daily_quantity_leg_four_arm_evaluation = build_quantity_leg_four_arm_evaluation(
        daily_four_arm_events
    )
    daily_atomic_plan_events = [
        event
        for event in daily_allowed_events
        if str(event.get("stage") or event.get("event") or "")
        in {
            "entry_execution_sizing_plan",
            "entry_execution_sizing_plan_block",
        }
    ]
    first_atomic_plan_at = min(
        (
            value
            for value in (_event_dt(event) for event in daily_atomic_plan_events)
            if value is not None
        ),
        default=None,
    )
    post_contract_submit_events = [
        event
        for event in daily_allowed_events
        if _is_real_submit_event(event)
        and first_atomic_plan_at is not None
        and _event_dt(event) is not None
        and _event_dt(event) >= first_atomic_plan_at
    ]
    daily_atomic_plan_observed_count = len(daily_atomic_plan_events)
    daily_atomic_plan_valid_count = sum(
        1
        for event in daily_atomic_plan_events
        if _safe_bool(event.get("entry_execution_sizing_valid"))
    )
    daily_atomic_plan_invalid_count = (
        daily_atomic_plan_observed_count - daily_atomic_plan_valid_count
    )
    daily_atomic_plan_submit_count = sum(
        1
        for event in post_contract_submit_events
        if str(event.get("entry_execution_sizing_plan_id") or "").strip()
    )
    daily_atomic_plan_missing_submit_count = (
        len(post_contract_submit_events) - daily_atomic_plan_submit_count
    )
    if daily_atomic_plan_invalid_count or daily_atomic_plan_missing_submit_count:
        atomic_contract_status = "fail"
    elif daily_atomic_plan_observed_count:
        atomic_contract_status = "pass"
    else:
        atomic_contract_status = "natural_first_use_pending"
    prior_state, prior_state_path = _latest_prior_cumulative_state(target_date)
    native_source_counts = dict((prior_state or {}).get("entry_opportunity_replay_source_counts") or {})
    if source_quality.get("tuning_input_allowed") is True:
        native_source_counts[target_date] = executable_replay["counts"]["unique_retained"]
    if prior_state:
        cumulative_four_arm_events = [
            event
            for event in (prior_state.get("quantity_leg_four_arm_events") or [])
            if isinstance(event, dict)
            and isinstance(event.get("entry_quantity_leg_four_arm_evaluation"), dict)
        ]
        loaded_event_count = 0
        included_calibration_event_count = 0
        excluded_source_quality = 0
        counts = _merge_count_maps(prior_state.get("counts") or {}, {})
        sim_ev_values = _deserialize_value_map(prior_state.get("sim_ev_values"))
        real_ev_values = _deserialize_value_map(prior_state.get("real_ev_values"))
        real_split_variant_ev_values = _deserialize_variant_value_map(
            prior_state.get("real_split_variant_ev_values")
        )
        real_split_child_variant_ev_values = _deserialize_variant_value_map(
            prior_state.get("real_split_child_variant_ev_values")
        )
        real_post_sell_summary = {
            key: _safe_int(value, 0)
            for key, value in (prior_state.get("real_post_sell_summary") or {}).items()
        }
        source_dates = list(prior_state.get("source_dates") or [])
        reconstructed_provenance_count = _safe_int(
            prior_state.get("reconstructed_split_provenance_count"), 0
        )
        replay_dates = [
            value
            for value in _available_calibration_dates(target_date)
            if value not in set(source_dates)
            and _source_quality_summary(value).get("tuning_input_allowed") is True
        ]
        source_paths_by_date: dict[str, Any] = {}
        for replay_date in replay_dates:
            if replay_date == target_date:
                replay_events = daily_events
                replay_summary = daily_load_summary
                allowed_events = daily_allowed_events
                excluded_count = daily_excluded_source_quality
            else:
                replay_events, replay_summary = _iter_input_events(replay_date)
                replay_quality = _source_quality_summary(replay_date)
                if replay_date >= "2026-09-17" and replay_quality.get("tuning_input_allowed") is True:
                    native = build_entry_opportunity_replays(replay_date, replay_summary.pop("_entry_opportunity_plan_events", []))
                    replay_events.extend(native["quantity_leg_events"])
                    native_source_counts[replay_date] = native["counts"]["unique_retained"]
                allowed_events, excluded_count = _source_quality_filtered_events(
                    replay_events, {replay_date: replay_quality}
                )
            replay_counts, _ = _quality_counts(
                allowed_events, {"tuning_input_allowed": True}
            )
            cumulative_four_arm_events.extend(
                event
                for event in allowed_events
                if isinstance(event.get("entry_quantity_leg_four_arm_evaluation"), dict)
            )
            counts = _merge_count_maps(counts, replay_counts)
            loaded_event_count += len(replay_events)
            included_calibration_event_count += len(allowed_events)
            excluded_source_quality += excluded_count
            source_paths_by_date[replay_date] = replay_summary.get("source_paths") or {}
            _extend_value_map(sim_ev_values, _load_sim_ev_values(replay_date))
            real_post_sell_rows, source_summary = _load_real_post_sell_rows(replay_date)
            real_post_sell_rows, reconstructed_today = (
                _enrich_real_post_sell_provenance(real_post_sell_rows, allowed_events)
            )
            reconstructed_provenance_count += reconstructed_today
            for key, value in source_summary.items():
                real_post_sell_summary[key] = _safe_int(
                    real_post_sell_summary.get(key), 0
                ) + _safe_int(value, 0)
            _extend_value_map(
                real_ev_values,
                _load_real_ev_values(replay_date, real_post_sell_rows),
            )
            _extend_value_map(
                real_split_variant_ev_values,
                _load_real_split_variant_ev_values(replay_date, real_post_sell_rows),
            )
            _extend_value_map(
                real_split_child_variant_ev_values,
                _load_real_split_variant_ev_values(
                    replay_date, real_post_sell_rows, child_variant=True
                ),
            )
            source_dates.append(replay_date)
        load_summary = {
            "aggregation_mode": "incremental_gap_replay_from_prior_cumulative_state",
            "prior_cumulative_state_path": prior_state_path,
            "replayed_source_dates": replay_dates,
            "source_paths": source_paths_by_date.get(target_date) or {},
            "source_paths_by_date": source_paths_by_date,
            "source_dates": sorted(source_dates),
            "source_date_count": len(set(source_dates)),
            "excluded_pre_baseline_count": _safe_int(
                daily_load_summary.get("excluded_pre_baseline_count"), 0
            ),
            "clean_tuning_baseline": clean_baseline_policy(),
        }
    else:
        cumulative_four_arm_events: list[dict[str, Any]] = []
        loaded_event_count = 0
        included_calibration_event_count = 0
        excluded_source_quality = 0
        counts: dict[str, dict[str, int]] = {}
        sim_ev_values: dict[str, list[float]] = defaultdict(list)
        real_ev_values: dict[str, list[float]] = defaultdict(list)
        real_split_variant_ev_values: dict[tuple[str, str], list[float]] = defaultdict(
            list
        )
        real_split_child_variant_ev_values: dict[tuple[str, str], list[float]] = (
            defaultdict(list)
        )
        reconstructed_provenance_count = 0
        real_post_sell_summary = {
            "candidate_count": 0,
            "evaluation_count": 0,
            "matched_evaluation_count": 0,
            "pending_evaluation_count": 0,
            "merged_count": 0,
        }
        included_source_dates: list[str] = []
        source_paths_by_date: dict[str, Any] = {}
        excluded_pre_baseline_count = 0
        for source_date in _available_calibration_dates(target_date):
            source_date_quality = _source_quality_summary(source_date)
            if source_date == target_date:
                source_events = daily_events
                source_summary = daily_load_summary
                allowed_events = daily_allowed_events
                excluded_count = daily_excluded_source_quality
            else:
                source_events, source_summary = _iter_input_events(source_date)
                if source_date >= "2026-09-17" and source_date_quality.get("tuning_input_allowed") is True:
                    native = build_entry_opportunity_replays(source_date, source_summary.pop("_entry_opportunity_plan_events", []))
                    source_events.extend(native["quantity_leg_events"])
                    native_source_counts[source_date] = native["counts"]["unique_retained"]
                allowed_events, excluded_count = _source_quality_filtered_events(
                    source_events, {source_date: source_date_quality}
                )
            loaded_event_count += len(source_events)
            excluded_source_quality += excluded_count
            excluded_pre_baseline_count += _safe_int(
                source_summary.get("excluded_pre_baseline_count"), 0
            )
            source_paths_by_date[source_date] = source_summary.get("source_paths") or {}
            if source_date_quality.get("tuning_input_allowed") is not True:
                continue
            included_source_dates.append(source_date)
            included_calibration_event_count += len(allowed_events)
            cumulative_four_arm_events.extend(
                event
                for event in allowed_events
                if isinstance(event.get("entry_quantity_leg_four_arm_evaluation"), dict)
            )
            source_counts, _ = _quality_counts(
                allowed_events, {"tuning_input_allowed": True}
            )
            counts = _merge_count_maps(counts, source_counts)
            _extend_value_map(sim_ev_values, _load_sim_ev_values(source_date))
            source_rows, post_sell_summary = _load_real_post_sell_rows(source_date)
            source_rows, reconstructed_today = _enrich_real_post_sell_provenance(
                source_rows, allowed_events
            )
            reconstructed_provenance_count += reconstructed_today
            for key in real_post_sell_summary:
                real_post_sell_summary[key] += _safe_int(post_sell_summary.get(key), 0)
            _extend_value_map(
                real_ev_values, _load_real_ev_values(source_date, source_rows)
            )
            _extend_value_map(
                real_split_variant_ev_values,
                _load_real_split_variant_ev_values(source_date, source_rows),
            )
            _extend_value_map(
                real_split_child_variant_ev_values,
                _load_real_split_variant_ev_values(
                    source_date, source_rows, child_variant=True
                ),
            )
        load_summary = {
            "aggregation_mode": "full_clean_baseline_rebuild",
            "rebuild_memory_mode": "date_streaming",
            "prior_cumulative_state_path": "",
            "streamed_source_dates": included_source_dates,
            "source_paths": source_paths_by_date.get(target_date) or {},
            "source_paths_by_date": source_paths_by_date,
            "source_dates": included_source_dates,
            "source_date_count": len(included_source_dates),
            "excluded_pre_baseline_count": excluded_pre_baseline_count,
            "clean_tuning_baseline": clean_baseline_policy(),
        }
    quantity_leg_four_arm_evaluation = build_quantity_leg_four_arm_evaluation(
        cumulative_four_arm_events, source_counts=native_source_counts
    )
    quantity_leg_four_arm_evaluation["daily_diagnostic"] = {
        "source_receipt_count": daily_quantity_leg_four_arm_evaluation.get(
            "source_receipt_count", 0
        ),
        "eligible_attempt_count": daily_quantity_leg_four_arm_evaluation.get(
            "eligible_attempt_count", 0
        ),
        "complete_exact_attempt_count": daily_quantity_leg_four_arm_evaluation.get(
            "complete_exact_attempt_count", 0
        ),
        "exact_attempt_join_coverage": daily_quantity_leg_four_arm_evaluation.get(
            "exact_attempt_join_coverage"
        ),
        "target_date": target_date,
    }
    (
        post_submit_low_tick_bands,
        post_submit_low_tick_band_scan,
    ) = _build_post_submit_low_tick_bands_from_sources(
        target_date,
        daily_allowed_events,
        source_quality=source_quality,
    )
    candidate_grid = _build_candidate_grid(
        counts,
        sim_ev_values,
        real_ev_values,
        real_split_variant_ev_values,
        real_split_child_variant_ev_values,
        post_submit_low_tick_bands,
    )
    for item in candidate_grid:
        bucket = str(item.get("context_bucket") or "")
        target_counts = daily_counts.get(bucket) or {}
        item["target_date_contribution"] = {
            "date": target_date,
            "real_sample_count": _safe_int(target_counts.get("real_sample_count"), 0),
            "real_observed_entry_count": _safe_int(
                target_counts.get("real_observed_entry_count"), 0
            ),
            "sim_sample_count": _safe_int(target_counts.get("sim_sample_count"), 0),
        }
    json_path, md_path = report_paths(target_date)
    policy_json = policy_path(target_date)
    source_quality_allowed = source_quality.get("tuning_input_allowed") is True
    model_validation = None
    if date.fromisoformat(target_date) >= date(2026, 9, 17):
        registry, registry_contract = _execution_registry_snapshot()
        model_validation = build_execution_model_validation(target_date, daily_allowed_events,
            executable_replay["rows"], registry,
            source_contract={"projection": daily_load_summary.get("execution_projection"),
                             "registry": registry_contract})
    selection_input_allowed = bool(
        source_quality_allowed and atomic_contract_status != "fail"
        and (model_validation is None or model_validation.get("allowed_runtime_apply") is True)
    )
    policy = _policy_payload(
        target_date, json_path, candidate_grid if selection_input_allowed else []
    )
    recommended_candidates = [
        item
        for item in candidate_grid
        if selection_input_allowed and item.get("candidate_passed")
    ]
    runtime_apply_allowed = bool(recommended_candidates)
    report = {
        "schema_version": SCHEMA_VERSION,
        "date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "report_type": REPORT_TYPE,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "execution_contract": {
            "schedule": "daily_postclose",
            "wrapper_default_enabled": True,
            "calibration_window": "clean_baseline_cumulative_through_target_date",
        },
        "split_domain_ownership": {
            "stage": "initial_entry",
            "evidence_owner": "entry_split_order_plan",
            "policy_owner": "entry_split_order_plan",
            "shared_execution_math": "src.trading.order.split_execution_math",
            "shared_execution_math_authority": "pure_qty_and_tick_math_only",
            "scale_in_evidence_or_policy_accepted": False,
            "independent_machine_evidence_or_policy_accepted": False,
        },
        "quantity_leg_four_arm_evaluation": quantity_leg_four_arm_evaluation,
        "metric_contract": {
            "metric_role": "authority_split_primary_ev_and_execution_shape_seed",
            "decision_authority": "next_preopen_bounded_entry_split_policy",
            "window_policy": "clean_baseline_cumulative_with_daily_diagnostic",
            "sample_floor": {
                "cumulative_learning": CUMULATIVE_LEARNING_SAMPLE_FLOOR,
                "runtime_promotion_real": SAMPLE_FLOOR_REAL,
                "runtime_promotion_sim_diagnostic": SAMPLE_FLOOR_SIM,
                "runtime_promotion_split_variant_outcome": (
                    SPLIT_VARIANT_OUTCOME_FLOOR_REAL
                ),
            },
            "learning_update_policy": (
                "one_mature_split_variant_outcome_updates_cumulative_judgment_quality"
            ),
            "probe_attribution_contract": (
                "A one-share entry intent is attributed to this owner only when entry_split_probe_bundle_id "
                "or an entry split parent/child variant ID is observed; record-level opportunity EV alone cannot claim "
                "split-policy execution quality."
            ),
            "primary_decision_metric": "source_quality_adjusted_ev_pct",
            "minimum_runtime_promotion_cost_adjusted_ev_pct": (
                RUNTIME_PROMOTION_MIN_COST_ADJUSTED_EV_PCT
            ),
            "primary_decision_metric_scope": (
                "ev_validated_variant_or_exact_child_shape_bounded_seed"
            ),
            "child_shape_seed_metric_contract": {
                "metric_role": "primary_ev",
                "primary_decision_metric": "source_quality_adjusted_ev_pct",
                "decision_authority": "bounded_exploration_seed_only",
                "minimum_seed_sample": CHILD_SHAPE_SEED_OUTCOME_FLOOR_REAL,
                "minimum_seed_ev_pct": CHILD_SHAPE_SEED_MIN_EV_PCT,
                "maximum_seed_downside_p10_pct": (
                    CHILD_SHAPE_SEED_MAX_DOWNSIDE_P10_PCT
                ),
                "runtime_shape_match_required": True,
                "forbidden_uses": [
                    "increase_requested_qty",
                    "cap_release",
                    "bypass_submit_or_hard_safety",
                    "claim_parent_variant_ev_from_child_ev",
                ],
            },
            "exploration_seed_metric_contract": {
                "metric_role": "execution_shape_seed",
                "primary_decision_metric": "qty_preserving_execution_shape_guard",
                "decision_authority": "bounded_exploration_seed_only",
                "forbidden_uses": [
                    "claim_positive_split_variant_ev",
                    "increase_requested_qty",
                    "bypass_submit_or_hard_safety",
                ],
            },
            "source_quality_gate": "observation_source_quality_audit_hard_block_rows_excluded",
            "atomic_execution_sizing_contract": {
                "schema_version": ATOMIC_EXECUTION_SIZING_SCHEMA,
                "policy_version": ATOMIC_EXECUTION_SIZING_BASELINE_POLICY,
                "same_attempt_quantity_and_leg_binding_required": True,
                "quantity_conservation_required": True,
                "quantity_increase_forbidden": True,
                "natural_first_use_status": atomic_contract_status,
            },
            "policy_modes": {
                POLICY_MODE_REAL_PRIMARY_EV: "real split-variant outcome EV-positive optimized split",
                POLICY_MODE_CHILD_SHAPE_EV_SEED: (
                    "exact runtime child-shape EV-positive bounded seed; "
                    "parent variants and other child shapes remain excluded"
                ),
                POLICY_MODE_BOUNDED_EQUAL_BASELINE: "real-submit-backed qty-preserving 2-leg 50/50 0.3pct baseline",
                POLICY_MODE_POST_SUBMIT_TICK_BAND: "post-submit observed-low tick-band qty-preserving seed",
            },
            "post_submit_low_tick_band_contract": {
                "metric_role": "execution_shape_seed",
                "decision_authority": "next_preopen_bounded_entry_split_policy",
                "window_policy": f"same_day_submit_plus_{POST_SUBMIT_LOW_WINDOW_MINUTES}m_runtime_observed_prices",
                "sample_floor": {
                    "real_submit_observed_low": POST_SUBMIT_TICK_BAND_FLOOR_REAL
                },
                "primary_decision_metric": "p75_down_ticks",
                "source_quality_gate": "actual_order_submitted=true and post-submit runtime observed prices present",
                "forbidden_uses": [
                    "claim_split_variant_ev_without_variant_outcome",
                    "increase_requested_qty",
                    "broker_guard_relief",
                    "intraday_mutation",
                ],
            },
            "optimization_contract": (
                "Post-sell profit_rate is only split-policy primary EV when it is joined to an applied "
                "entry_split_order_policy_variant_id (with the runtime child variant retained separately). "
                "Bucket-only sell outcome is diagnostic."
            ),
            "baseline_apply_contract": (
                "A qty-preserving execution-shape seed may open at next PREOPEN after real-submit sample and "
                "execution guards pass. This is structural activation under exploration_seed_allowed, not an "
                "EV-positive variant claim. Only ev_validated_runtime_apply_allowed asserts split-variant EV."
            ),
            "forbidden_uses": [
                "requested_qty_increase",
                "real_execution_quality_approval_from_sim",
                "intraday_threshold_mutation",
                "broker_guard_relief",
            ],
        },
        "source_quality": source_quality,
        "cumulative_state": {
            "schema_version": CUMULATIVE_STATE_SCHEMA_VERSION,
            "window_policy": "clean_baseline_cumulative_through_target_date",
            "through_date": target_date,
            "clean_tuning_baseline_date": clean_baseline_policy().get(
                "clean_tuning_baseline_date"
            ),
            "source_dates": load_summary.get("source_dates") or [],
            "counts": counts,
            "sim_ev_values": {
                bucket: list(values) for bucket, values in sim_ev_values.items()
            },
            "real_ev_values": {
                bucket: list(values) for bucket, values in real_ev_values.items()
            },
            "real_split_variant_ev_values": _serialize_variant_value_map(
                real_split_variant_ev_values
            ),
            "real_split_child_variant_ev_values": _serialize_variant_value_map(
                real_split_child_variant_ev_values
            ),
            "quantity_leg_four_arm_events": cumulative_four_arm_events,
            "entry_opportunity_replay_source_counts": native_source_counts,
            "source_quality_contract_bindings": _source_quality_contract_bindings(
                list(load_summary.get("source_dates") or [])
            ),
            "real_post_sell_summary": real_post_sell_summary,
            "reconstructed_split_provenance_count": (reconstructed_provenance_count),
        },
        "input_summary": {
            **load_summary,
            "loaded_event_count": loaded_event_count,
            "included_calibration_event_count": included_calibration_event_count,
            "excluded_source_quality_event_count": excluded_source_quality,
            "daily_diagnostic": {
                **daily_load_summary,
                "loaded_event_count": len(daily_events),
                "included_event_count": len(daily_allowed_events),
                "excluded_source_quality_event_count": (daily_excluded_source_quality),
            },
            "sim_post_sell_path": (
                str(_sim_post_sell_path(target_date))
                if _sim_post_sell_path(target_date).exists()
                else None
            ),
            "real_post_sell_path": (
                str(_real_post_sell_path(target_date))
                if _real_post_sell_path(target_date).exists()
                else None
            ),
            "real_post_sell_candidate_path": (
                str(_real_post_sell_candidate_path(target_date))
                if _real_post_sell_candidate_path(target_date).exists()
                else None
            ),
            "real_post_sell_join": {
                **real_post_sell_summary,
                "reconstructed_split_provenance_count": reconstructed_provenance_count,
            },
            "threshold_cycle_ev_path": (
                str(_threshold_cycle_ev_path(target_date))
                if _threshold_cycle_ev_path(target_date).exists()
                else None
            ),
            "post_submit_low_tick_band_bucket_count": len(post_submit_low_tick_bands),
            "post_submit_low_tick_band_scan": post_submit_low_tick_band_scan,
            "atomic_execution_sizing": {
                "status": atomic_contract_status,
                "daily_plan_observed_count": daily_atomic_plan_observed_count,
                "daily_plan_valid_count": daily_atomic_plan_valid_count,
                "daily_plan_invalid_count": daily_atomic_plan_invalid_count,
                "daily_real_submit_with_plan_count": daily_atomic_plan_submit_count,
                "daily_real_submit_missing_plan_count": (
                    daily_atomic_plan_missing_submit_count
                ),
                "selection_blocked": atomic_contract_status == "fail",
                "natural_first_use_pending": (
                    atomic_contract_status == "natural_first_use_pending"
                ),
            },
        },
        "candidate_grid": candidate_grid,
        "recommended_policy": {
            "runtime_apply_allowed": runtime_apply_allowed,
            "runtime_apply_compatibility_semantics": policy.get(
                "runtime_apply_compatibility_semantics"
            ),
            "exploration_seed_allowed": policy.get("exploration_seed_allowed") is True,
            "exploration_seed_count": _safe_int(
                policy.get("exploration_seed_count"), 0
            ),
            "ev_validated_runtime_apply_allowed": policy.get(
                "ev_validated_runtime_apply_allowed"
            )
            is True,
            "ev_validated_bucket_count": _safe_int(
                policy.get("ev_validated_bucket_count"), 0
            ),
            "runtime_apply_authority_classes": policy.get(
                "runtime_apply_authority_classes"
            )
            or [],
            "runtime_apply_scope": policy.get("runtime_apply_scope") or [],
            "post_apply_attribution": policy.get("post_apply_attribution") or {},
            "post_apply_continuation_gate": policy.get("post_apply_continuation_gate")
            or {},
            "rollback_guard": policy.get("rollback_guard") or {},
            "baseline_runtime_defaults_enabled": policy.get(
                "baseline_runtime_defaults_enabled"
            )
            is True,
            "missing_bucket_action": policy.get("missing_bucket_action"),
            "explicit_bucket_count": _safe_int(policy.get("explicit_bucket_count"), 0),
            "preopen_guard_required": True,
            "entry_execution_sizing_policy": (ATOMIC_EXECUTION_SIZING_BASELINE_POLICY),
            "entry_price_plan_schema": ATOMIC_PRICE_PLAN_SCHEMA,
            "entry_execution_sizing_plan_schema": (ATOMIC_EXECUTION_SIZING_SCHEMA),
            "atomic_execution_sizing_contract_status": atomic_contract_status,
            "policy_file": str(policy_json),
            "policy_version": policy["policy_version"],
            "candidate_count": len(recommended_candidates),
            "candidates": recommended_candidates,
        },
    }
    if model_validation is not None:
        actual_outcomes, actual_source = _bounded_actual_entry_outcomes(target_date)
        model_validation["source_contract"]["actual_outcomes"]=actual_source
        model_validation, economics = _refresh_operating_economics(report,model_validation,executable_replay,actual_outcomes,target_date=target_date,events=daily_allowed_events,registry=registry)
        policy, operating_grid = _operating_policy(target_date,json_path,economics)
        report["operating_candidate_grid"] = operating_grid
        report["recommended_policy"].update({key:policy[key] for key in ("runtime_apply_allowed","exploration_seed_allowed","exploration_seed_count","ev_validated_runtime_apply_allowed","ev_validated_bucket_count","explicit_bucket_count","runtime_apply_scope","runtime_apply_authority_classes","missing_bucket_action","policy_version")})
        report["recommended_policy"].update(candidate_count=len(operating_grid),candidates=operating_grid)
        report["execution_model_validation"] = model_validation
        model_fields = {"execution_model_validation_contract": EXECUTION_MODEL_CONTRACT,
                        "execution_model_validation_sha256": _canonical_sha256(model_validation),
                        "execution_model_disposition": model_validation["status"]}
        policy.update(model_fields)
        report["recommended_policy"].update(model_fields)
    report, policy = bind_report_policy_generation(report, policy)
    if write:
        generation_id = str(
            (report.get("artifact_generation_binding") or {}).get("generation_id") or ""
        )
        immutable_report = generation_report_path(target_date, generation_id)
        immutable_policy = generation_policy_path(target_date, generation_id)
        _write_immutable_json(immutable_report, report)
        _write_immutable_json(immutable_policy, policy)
        _write_json(json_path, report)
        _write_json(policy_json, policy)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(_render_markdown(report), encoding="utf-8")
    return report


def _render_markdown(report: dict[str, Any]) -> str:
    rec = (
        report.get("recommended_policy")
        if isinstance(report.get("recommended_policy"), dict)
        else {}
    )
    lines = [
        f"# Entry Split Order Plan - {report.get('date')}",
        "",
        "## Summary",
        f"- schema_version: `{report.get('schema_version')}`",
        f"- runtime_effect: `{report.get('runtime_effect')}`",
        f"- recommended_policy_candidates: `{rec.get('candidate_count')}`",
        f"- runtime_apply_allowed: `{rec.get('runtime_apply_allowed')}`",
        f"- exploration_seed_allowed: `{rec.get('exploration_seed_allowed')}` / count: `{rec.get('exploration_seed_count')}`",
        f"- ev_validated_runtime_apply_allowed: `{rec.get('ev_validated_runtime_apply_allowed')}` / count: `{rec.get('ev_validated_bucket_count')}`",
        f"- runtime_apply_authority_classes: `{rec.get('runtime_apply_authority_classes') or []}`",
        f"- policy_version: `{rec.get('policy_version') or '-'}`",
        f"- artifact_generation_id: `{(report.get('artifact_generation_binding') or {}).get('generation_id') or '-'}`",
        f"- baseline_runtime_defaults_enabled: `{rec.get('baseline_runtime_defaults_enabled')}`",
        f"- missing_bucket_action: `{rec.get('missing_bucket_action') or '-'}`",
        f"- explicit_bucket_count: `{rec.get('explicit_bucket_count')}`",
        f"- policy_file: `{rec.get('policy_file') or '-'}`",
        "",
        "## Candidate Grid",
    ]
    for item in report.get("candidate_grid") or []:
        if not isinstance(item, dict):
            continue
        lines.append(
            "- "
            f"`{item.get('context_bucket')}` legs=`{item.get('leg_count')}` "
            f"mode=`{item.get('policy_mode') or '-'}` "
            f"real/sim=`{item.get('real_sample_count')}/{item.get('sim_sample_count')}` "
            f"ev=`{item.get('source_quality_adjusted_ev_pct')}` "
            f"bucket_ev=`{item.get('real_bucket_outcome_ev_pct')}` "
            f"observed_split_outcomes=`{item.get('observed_real_split_outcome_count')}` "
            f"apply_scope=`{item.get('runtime_apply_scope')}` "
            f"apply_authority=`{item.get('runtime_apply_authority_class')}` "
            f"p75_down_ticks=`{((item.get('post_submit_low_tick_band') or {}).get('p75_down_ticks'))}` "
            f"cancel=`{item.get('cancel_rate')}` "
            f"pass=`{item.get('candidate_passed')}`"
        )
    return "\n".join(lines) + "\n"


def _load_policy_from_env(
    policy_file: str | None = None,
    *,
    now: datetime | None = None,
) -> tuple[dict[str, Any], str]:
    configured_enabled = (
        str(os.environ.get("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED", ""))
        .strip()
        .lower()
    )
    enabled = configured_enabled in {"1", "true", "yes", "on"}
    daily_baseline = bool(
        not enabled
        and _safe_bool(
            os.environ.get("KORSTOCKSCAN_ENTRY_SPLIT_DAILY_OPERATOR_CONTRACT_ENABLED")
        )
    )
    if not enabled and not daily_baseline:
        return {}, "policy_disabled"
    active_date = str(
        os.environ.get(
            (
                "KORSTOCKSCAN_ENTRY_SPLIT_DAILY_BASELINE_ACTIVE_DATE"
                if daily_baseline
                else "KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ACTIVE_DATE"
            )
        )
        or ""
    ).strip()
    if active_date:
        now_date = _kst_date(now)
        if active_date.upper() not in {now_date, DAILY_ACTIVE_DATE_TOKEN}:
            return {}, "policy_inactive_date"
    path_text = str(
        policy_file
        or os.environ.get(
            (
                "KORSTOCKSCAN_ENTRY_SPLIT_DAILY_BASELINE_POLICY_FILE"
                if daily_baseline
                else "KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_FILE"
            )
        )
        or ""
    ).strip()
    if not path_text:
        return {}, "policy_file_missing"
    path = Path(path_text)
    if not path.exists():
        return {}, "policy_file_not_found"
    payload = _load_json(path)
    if payload.get("schema_version") != POLICY_SCHEMA_VERSION:
        return {}, "invalid_policy_schema"
    if not isinstance(payload.get("buckets"), dict):
        return {}, "invalid_policy_buckets"
    version_key = (
        "KORSTOCKSCAN_ENTRY_SPLIT_DAILY_BASELINE_POLICY_VERSION"
        if daily_baseline
        else "KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_VERSION"
    )
    expected_version = str(os.environ.get(version_key) or "").strip()
    # PREOPEN requires this version field.  Runtime independently compares it
    # when present so a later alias rewrite cannot silently change selection.
    if expected_version and payload.get("policy_version") != expected_version:
        return {}, "policy_version_mismatch"
    authority_valid, authority_reason = runtime_apply_authority_contract_status(payload)
    if not authority_valid:
        return {}, f"invalid_policy_authority_contract:{authority_reason}"
    generation_valid, generation_reason = policy_report_generation_contract_status(
        payload
    )
    if not generation_valid:
        return {}, f"invalid_policy_generation_contract:{generation_reason}"
    payload = {**payload, "runtime_apply_authority_contract": authority_reason}
    payload["artifact_generation_contract"] = generation_reason
    if "runtime_apply_allowed" in payload and not _safe_bool(
        payload.get("runtime_apply_allowed")
    ):
        if not _entry_split_operator_fallback_active(now=now):
            return {}, "policy_runtime_apply_not_allowed"
        payload = {
            **payload,
            "entry_split_order_operator_fallback_authorized": True,
        }
    if daily_baseline:
        payload = {
            **payload,
            "entry_split_order_daily_baseline_fallback_applied": True,
        }
    return payload, "loaded"


def _policy_is_stale(
    policy: dict[str, Any], *, now: datetime | None = None, max_age_days: int = 5
) -> bool:
    source_date = str(policy.get("source_date") or "").strip()
    if not source_date:
        return True
    now_date = (now or datetime.now(timezone(timedelta(hours=9)))).date()
    try:
        policy_date = date.fromisoformat(source_date)
    except ValueError:
        return True
    return now_date - policy_date > timedelta(days=max_age_days)


def _daily_operator_contract_enabled() -> bool:
    return _safe_bool(
        os.environ.get("KORSTOCKSCAN_ENTRY_SPLIT_DAILY_OPERATOR_CONTRACT_ENABLED")
    )


def _stale_baseline_policy_operator_authorized(policy: dict[str, Any]) -> bool:
    return bool(
        _daily_operator_contract_enabled()
        and _safe_bool(policy.get("entry_split_order_daily_baseline_fallback_applied"))
        and _safe_bool(policy.get("baseline_runtime_defaults_enabled"))
        and not (policy.get("buckets") or {})
    )


def _runtime_default_bucket_fallback_authorized(policy: dict[str, Any]) -> bool:
    """Return whether a missing bucket may use the legacy default split.

    A deliberately bucketless baseline may retain its approved fallback.  A
    standard dated policy is instead scoped to its explicit buckets; it can
    use a fallback only when the separately date-bounded operator fallback
    contract has been loaded.
    """

    explicit_authority_contract = bool(
        {
            "runtime_apply_compatibility_semantics",
            "exploration_seed_allowed",
            "ev_validated_runtime_apply_allowed",
            "missing_bucket_action",
        }.intersection(policy)
    )
    return bool(
        (
            _safe_bool(policy.get("baseline_runtime_defaults_enabled"))
            and not (policy.get("buckets") or {})
        )
        or _safe_bool(policy.get("entry_split_order_operator_fallback_authorized"))
        # Policies from before the explicit authority split were deliberately
        # bucketless.  Keep their compatibility path; a policy that declares
        # the newer authority contract never receives this implicit fallback.
        or not explicit_authority_contract
    )


def _max_legs_for_qty(qty: int) -> int:
    if qty <= 1:
        return 1
    if qty == 2:
        return 2
    if 3 <= qty <= 5:
        return 2
    return 3


def _runtime_default_bucket_policy(bucket: str) -> dict[str, Any]:
    if bucket == "passive_wide_or_weak":
        return {
            "context_bucket": bucket,
            "leg_count": 3,
            "price_offsets_ticks": [0, 1, 2],
            "price_offsets_pct": [0.0, 0.3, 0.8],
            "qty_weight_min": 0.5,
            "qty_weight_max": 0.5,
            "policy_mode": RUNTIME_FALLBACK_THREE_LEG_POLICY_MODE,
            "split_variant_id": RUNTIME_FALLBACK_THREE_LEG_VARIANT_ID,
            "policy_generation_reason": (
                "runtime fallback for passive bucket gap; 50pct market-first plus two resolver residual legs"
            ),
        }
    return {
        "context_bucket": bucket,
        "leg_count": 2,
        "price_offsets_ticks": [0, 1],
        "price_offsets_pct": [0.0, 0.3],
        "qty_weight_min": 0.5,
        "qty_weight_max": 0.5,
        "policy_mode": RUNTIME_FALLBACK_POLICY_MODE,
        "split_variant_id": RUNTIME_FALLBACK_VARIANT_ID,
        "policy_generation_reason": "runtime fallback for policy bucket gap; qty-preserving passive-centered 0.3pct seed",
    }


def _has_present_value(fields: dict[str, Any], key: str) -> bool:
    value = fields.get(key)
    return value not in (None, "", "-", "unknown", "not_available")


def _split_allocator_stale_quote_blocked(fields: dict[str, Any]) -> bool:
    if _safe_bool(fields.get("stale_quote_submit_block")):
        return True
    for key in ("quote_stale_at_submit", "pre_submit_effective_quote_stale"):
        if _safe_bool(fields.get(key)):
            return True
    if any(
        _has_present_value(fields, key)
        for key in ("quote_stale_at_submit", "pre_submit_effective_quote_stale")
    ):
        return False
    return _safe_bool(fields.get("quote_stale"))


def _spread_bps_from_fields(fields: dict[str, Any]) -> float:
    spread_bps = _safe_float(fields.get("spread_bps"), None)
    if spread_bps is not None:
        return float(spread_bps)
    spread_ratio = _safe_float(fields.get("spread_ratio"), None)
    return float(spread_ratio or 0.0) * 10000.0 if spread_ratio is not None else 0.0


def _entry_split_passive_bias_reason(fields: dict[str, Any]) -> str:
    action_tokens = {
        str(fields.get(key) or "").strip().upper()
        for key in (
            "ai_action",
            "action",
            "chosen_action",
            "entry_ai_action",
            "entry_ai_submit_authority_action",
            "last_watching_ai_action",
        )
    }
    if "WAIT" not in action_tokens:
        return ""
    reasons: list[str] = []
    if _safe_bool(fields.get("quote_stale")) or _safe_bool(
        fields.get("ai_input_quote_stale")
    ):
        reasons.append("quote_stale_warning")
    if _spread_bps_from_fields(fields) >= 35.0:
        reasons.append("high_spread")
    text = " ".join(
        str(fields.get(key) or "").lower()
        for key in (
            "reason",
            "block_reason",
            "policy_reason",
            "latency_danger_reasons",
            "latency_danger_detail_reason",
            "entry_submit_revalidation_warning",
            "entry_price_gap_profile_reason",
            "ai_entry_price_canary_reason",
            "entry_ai_submit_authority_reason",
            "submit_quality_parent",
        )
    )
    text_markers = {
        "stale_quote": (
            "stale quote",
            "quote_stale",
            "stale_snapshot",
            "diagnostic_quote_age_stale",
        ),
        "high_spread": ("high spread", "wide spread", "spread_too_wide", "spread=wide"),
    }
    for reason, markers in text_markers.items():
        if any(marker in text for marker in markers) and reason not in reasons:
            reasons.append(reason)
    if not reasons:
        return ""
    return "ai_wait_with_" + "+".join(reasons)


def _entry_split_passive_bias_first_weight(
    policy_first_weight: float,
    fields: dict[str, Any],
) -> tuple[float, str]:
    reason = _entry_split_passive_bias_reason(fields)
    if reason:
        return min(policy_first_weight, PASSIVE_BIAS_WAIT_WARNING_FIRST_WEIGHT), reason
    passive_center_weight = min(policy_first_weight, PASSIVE_CENTER_MAX_FIRST_WEIGHT)
    if passive_center_weight < policy_first_weight:
        return passive_center_weight, "passive_center_first_leg_cap"
    return policy_first_weight, ""


def _runtime_shape_gate_status(
    gate: Any,
    *,
    policy_split_variant_id: str,
    requested_legs: int,
    desired_legs: int,
    first_weight: float,
    runtime_weight_adjusted: bool,
    market_first_leg_active: bool,
    probe_enabled: bool,
    probe_eligible: bool,
) -> tuple[bool, str]:
    """Fail closed unless an observed child shape exactly matches at runtime."""

    if gate is None:
        return True, ""
    if not isinstance(gate, dict) or gate.get("schema") != (
        "entry_split_runtime_shape_gate_v1"
    ):
        return False, "invalid_runtime_shape_gate"
    checks: tuple[tuple[bool, str], ...] = (
        (
            str(gate.get("required_policy_split_variant_id") or "")
            == policy_split_variant_id,
            "policy_variant",
        ),
        (
            _safe_int(gate.get("required_requested_legs"), 0) == requested_legs,
            "requested_legs",
        ),
        (
            _safe_int(gate.get("required_desired_legs"), 0) == desired_legs,
            "desired_legs",
        ),
        (
            abs(
                (_safe_float(gate.get("required_runtime_first_weight"), -1.0) or -1.0)
                - float(first_weight)
            )
            <= 0.000001,
            "first_weight",
        ),
        (
            _safe_bool(gate.get("require_runtime_weight_adjusted"))
            == bool(runtime_weight_adjusted),
            "runtime_weight_adjusted",
        ),
        (
            _safe_bool(gate.get("require_market_first_leg_disabled"))
            == (not market_first_leg_active),
            "market_first_leg",
        ),
        (
            _safe_bool(gate.get("require_probe_first_enabled")) == bool(probe_enabled),
            "probe_first_enabled",
        ),
        (
            _safe_bool(gate.get("require_probe_first_eligible"))
            == bool(probe_eligible),
            "probe_first_eligible",
        ),
    )
    for passed, reason in checks:
        if not passed:
            return False, reason
    return True, ""


def _market_first_leg_active(*, now: datetime | None = None) -> bool:
    if not _safe_bool(
        os.environ.get("KORSTOCKSCAN_ENTRY_SPLIT_MARKET_FIRST_LEG_ENABLED")
    ):
        return False
    active_date = str(
        os.environ.get("KORSTOCKSCAN_ENTRY_SPLIT_MARKET_FIRST_LEG_ACTIVE_DATE") or ""
    ).strip()
    if not active_date:
        return False
    now_date = (now or datetime.now(timezone(timedelta(hours=9)))).date().isoformat()
    return active_date == now_date


def _entry_split_operator_fallback_active(*, now: datetime | None = None) -> bool:
    if not _safe_bool(
        os.environ.get("KORSTOCKSCAN_ENTRY_SPLIT_OPERATOR_FALLBACK_ENABLED")
    ):
        return False
    active_date = str(
        os.environ.get("KORSTOCKSCAN_ENTRY_SPLIT_OPERATOR_FALLBACK_ACTIVE_DATE") or ""
    ).strip()
    if not active_date:
        return False
    now_date = (now or datetime.now(timezone(timedelta(hours=9)))).date().isoformat()
    return active_date == now_date


def _market_first_leg_reference_price(fields: dict[str, Any], base_price: int) -> int:
    for key in (
        "best_ask_at_submit",
        "executable_buy_price",
        "best_ask",
        "latest_price",
        "canonical_mark_price",
    ):
        value = _safe_int(fields.get(key), 0)
        if value > 0:
            return value
    return max(0, int(base_price or 0))


def _probe_first_eligible(stock: dict[str, Any], total_qty: int) -> tuple[bool, str]:
    """Allow probe-first for every real SCALPING initial-entry source."""

    if total_qty <= 1:
        return False, "qty_lte_1"
    if str(stock.get("strategy") or "").strip().upper() not in {"SCALP", "SCALPING"}:
        return False, "non_scalping"
    if any(
        _safe_bool(stock.get(key))
        for key in (
            "scalp_live_simulator",
            "simulation_book",
            "swing_live_order_dry_run",
        )
    ):
        return False, "simulated_entry_excluded"
    if stock.get("simulation_owner") or stock.get("actual_order_submitted") is False:
        return False, "simulated_entry_excluded"

    has_existing_position = bool(
        _safe_int(stock.get("buy_qty"), 0) > 0
        or str(stock.get("status") or "").strip().upper() in {"HOLDING", "SELL_ORDERED"}
    )
    forced_rising_missed_initial = bool(
        _safe_bool(stock.get("rising_missed_one_share_entry_forced"))
        and _safe_bool(stock.get("rising_missed_one_share_scout"))
        and not has_existing_position
        and not _safe_bool(stock.get("rising_missed_scout_upgrade_order_pending"))
        and not _safe_bool(stock.get("pending_add_order"))
    )
    if (
        has_existing_position
        or _safe_bool(stock.get("rising_missed_scout_upgrade_order_pending"))
        or _safe_bool(stock.get("pending_add_order"))
        or (
            _safe_bool(stock.get("rising_missed_scout_upgrade_pending"))
            and not forced_rising_missed_initial
        )
    ):
        return False, "non_initial_entry_excluded"
    return True, "eligible"


def _build_probe_continuation(
    *,
    base_order: dict[str, Any],
    total_qty: int,
    desired_legs: int,
    first_weight: float,
    applied_offsets: list[int],
    pct_offsets: list[float],
    common_fields: dict[str, Any],
) -> dict[str, Any]:
    remaining_qty = total_qty - 1
    residual_leg_count = min(desired_legs, remaining_qty)
    residual_quantities = _split_qty(remaining_qty, residual_leg_count, first_weight)
    return {
        "base_order": {
            "tag": str(base_order.get("tag") or "normal"),
            "tif": str(base_order.get("tif") or "DAY"),
            "order_type_code": "00",
        },
        "requested_qty": total_qty,
        "residual_qty": remaining_qty,
        "residual_leg_count": residual_leg_count,
        "residual_quantities": residual_quantities,
        "price_offsets_ticks": applied_offsets[:residual_leg_count],
        "price_offsets_pct": pct_offsets[:residual_leg_count] if pct_offsets else [],
        "common_fields": common_fields,
    }


def build_probe_residual_orders(
    continuation: dict[str, Any],
    *,
    probe_fill_price: int,
    best_bid: int,
    best_ask: int,
    resolved_leg_prices: list[int] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Allocate residual legs after a verified one-share probe fill.

    When P1 supplies ``resolved_leg_prices`` this allocator preserves those
    prices exactly and owns quantity distribution only.  The legacy offset
    calculation remains for the disabled capability path.
    """
    requested_qty = _safe_int(continuation.get("requested_qty"), 0)
    residual_qty = _safe_int(continuation.get("residual_qty"), 0)
    quantities = [
        _safe_int(value, 0) for value in continuation.get("residual_quantities") or []
    ]
    if (
        requested_qty <= 1
        or residual_qty != requested_qty - 1
        or sum(quantities) != residual_qty
    ):
        return [], {"allowed": False, "reason": "residual_quantity_invariant"}
    if probe_fill_price <= 0 or best_bid <= 0 or best_ask <= 0 or best_bid > best_ask:
        return [], {"allowed": False, "reason": "invalid_fresh_bbo"}
    anchor = min(max(int(probe_fill_price), int(best_bid)), int(best_ask))
    offsets = [
        _safe_int(value, 0) for value in continuation.get("price_offsets_ticks") or []
    ]
    pct_offsets = [
        max(0.0, float(_safe_float(value, 0.0) or 0.0))
        for value in continuation.get("price_offsets_pct") or []
    ]
    common_fields = dict(continuation.get("common_fields") or {})
    base_order = dict(continuation.get("base_order") or {})
    p1_prices = [_safe_int(value, 0) for value in (resolved_leg_prices or [])]
    if resolved_leg_prices is not None and (
        len(p1_prices) != len(quantities) or any(price <= 0 for price in p1_prices)
    ):
        return [], {"allowed": False, "reason": "invalid_p1_residual_prices"}
    tick = _tick_size(anchor)
    orders: list[dict[str, Any]] = []
    for idx, qty in enumerate(quantities):
        offset_ticks = offsets[idx] if idx < len(offsets) else idx
        offset_pct = pct_offsets[idx] if idx < len(pct_offsets) else None
        price = (
            p1_prices[idx]
            if resolved_leg_prices is not None
            else (
                _pct_price_offset(anchor, offset_pct)
                if offset_pct is not None
                else clamp_price_to_tick(max(1, anchor - (tick * offset_ticks)))
            )
        )
        orders.append(
            {
                **base_order,
                **common_fields,
                "tag": f"entry_split_probe_residual_{idx + 1}",
                "qty": qty,
                "price": price,
                "order_type_code": "00",
                "entry_split_order_leg_index": idx + 1,
                "entry_split_order_execution_mode": "probe_fill_resolver_limit",
                "entry_split_order_probe_first_applied": True,
                "entry_split_order_probe_anchor_price": anchor,
                "entry_split_order_probe_fill_price": probe_fill_price,
                "entry_split_order_price_authority": (
                    "dynamic_entry_price_resolver_p1"
                    if resolved_leg_prices is not None
                    else "legacy_probe_offset"
                ),
                "price_candidate_id": (f"probe_residual_resolver:leg{idx + 2}"),
                "split_leg_role": "primary" if idx == 0 else "passive",
                "split_price_offset_ticks": offset_ticks,
                "split_price_offset_pct": offset_pct if offset_pct is not None else "",
            }
        )
    if 1 + sum(_safe_int(order.get("qty"), 0) for order in orders) != requested_qty:
        return [], {"allowed": False, "reason": "total_quantity_invariant"}
    first_price = _safe_int(orders[0].get("price"), 0) if orders else 0
    gap_bps = (
        ((float(probe_fill_price) - float(first_price)) / float(probe_fill_price))
        * 10000.0
        if probe_fill_price > 0 and first_price > 0
        else 0.0
    )
    return orders, {
        "allowed": True,
        "reason": "probe_fill_anchor_ready",
        "probe_anchor_price": anchor,
        "probe_fill_to_first_residual_limit_gap_bps": round(gap_bps, 4),
        "residual_qty": residual_qty,
        "residual_leg_count": len(orders),
        "residual_price_authority": (
            "dynamic_entry_price_resolver_p1"
            if resolved_leg_prices is not None
            else "legacy_probe_offset"
        ),
    }


def apply_entry_split_order_policy(
    planned_orders: list[dict[str, Any]] | tuple[dict[str, Any], ...] | None,
    *,
    stock: dict[str, Any] | None = None,
    latency_gate: dict[str, Any] | None = None,
    policy_file: str | None = None,
    now: datetime | None = None,
    operating_context: dict | None = None,
    observation_only: bool = False,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    orders = [dict(item) for item in (planned_orders or []) if isinstance(item, dict)]
    latency_gate = latency_gate if isinstance(latency_gate, dict) else {}
    stock = stock if isinstance(stock, dict) else {}
    total_qty = sum(_safe_int(item.get("qty"), 0) for item in orders)
    fields: dict[str, Any] = {
        "entry_split_order_policy_applied": False,
        "entry_split_order_original_order_count": len(orders),
        "entry_split_order_original_qty": total_qty,
    }
    if total_qty <= 1:
        fields["entry_split_order_skip_reason"] = "qty_lte_1"
        return orders, fields
    if len(orders) != 1:
        fields["entry_split_order_skip_reason"] = "multi_order_input_not_supported_v1"
        return orders, fields
    if _split_allocator_stale_quote_blocked(latency_gate):
        fields["entry_split_order_skip_reason"] = "stale_quote"
        return orders, fields
    if str(
        latency_gate.get("latency_state") or ""
    ).upper() == "DANGER" and not _safe_bool(
        latency_gate.get("latency_canary_applied")
    ):
        fields["entry_split_order_skip_reason"] = (
            "danger_latency_without_approved_relief"
        )
        return orders, fields
    policy, load_status = _load_policy_from_env(policy_file, now=now)
    if not policy:
        fields["entry_split_order_skip_reason"] = load_status
        return orders, fields
    fields.update(entry_split_order_policy_sha256=_canonical_sha256(policy),
                  entry_split_order_runtime_pid=os.getpid(), entry_split_order_runtime_consumed=True)
    fields["entry_execution_sizing_plan_schema"] = str(
        policy.get("entry_execution_sizing_plan_schema")
        or ATOMIC_EXECUTION_SIZING_SCHEMA
    )
    fields["entry_execution_sizing_policy"] = str(
        policy.get("entry_execution_sizing_policy")
        or ATOMIC_EXECUTION_SIZING_BASELINE_POLICY
    )
    fields["entry_price_plan_schema"] = str(
        policy.get("entry_price_plan_schema") or ATOMIC_PRICE_PLAN_SCHEMA
    )
    policy_stale = _policy_is_stale(policy, now=now)
    daily_operator_contract = _daily_operator_contract_enabled()
    stale_policy_authorized = _stale_baseline_policy_operator_authorized(policy)
    if policy_stale and not stale_policy_authorized:
        fields["entry_split_order_skip_reason"] = "stale_policy"
        return orders, fields
    fields["entry_split_order_daily_operator_contract_enabled"] = (
        daily_operator_contract
    )
    fields["entry_split_order_daily_baseline_fallback_applied"] = _safe_bool(
        policy.get("entry_split_order_daily_baseline_fallback_applied")
    )
    fields["entry_split_order_stale_policy_operator_authorized"] = bool(
        policy_stale and stale_policy_authorized
    )
    context_fields = {**stock, **latency_gate}
    bucket = _context_bucket(context_fields)
    bucket_policy = (policy.get("buckets") or {}).get(bucket)
    fallback_policy_applied = False
    if not isinstance(bucket_policy, dict):
        if not _runtime_default_bucket_fallback_authorized(policy):
            fields.update(
                {
                    "entry_split_order_bucket": bucket,
                    "entry_split_order_policy_version": policy.get("policy_version"),
                    "entry_split_order_runtime_default_policy_applied": False,
                    "entry_split_order_skip_reason": "policy_bucket_not_selected",
                }
            )
            return orders, fields
        bucket_policy = _runtime_default_bucket_policy(bucket)
        fallback_policy_applied = True
    operating_template = bucket_policy.get("operating_template")
    if operating_template:
        venue = str(context_fields.get("effective_venue") or context_fields.get("entry_effective_venue") or "")
        session = str(context_fields.get("market_session_bucket") or context_fields.get("session_bucket") or "")
        price_hashes={x.get("entry_price_policy_sha256") for x in orders}
        types=[str(x.get("order_type_code") or "00") for x in orders]
        current_scope=_entry_operating_scope(dict(operating_contract=operating_context or {},
            effective_venue=venue,session_bucket=session,legs=[dict(order_type_code=t) for t in types],
            entry_price_policy_sha256=next(iter(price_hashes)) if len(price_hashes)==1 else None))
        if (not operating_context or current_scope!=bucket_policy.get("operating_scope_sha256")
            or total_qty not in bucket_policy.get("supported_total_quantities",[])
            or venue != operating_template["effective_venue"] or session != operating_template["session_bucket"]):
            fields["entry_split_order_skip_reason"] = "operating_model_scope_mismatch"
            return orders, fields
    policy_mode = str(bucket_policy.get("policy_mode") or "").strip()
    policy_split_variant_id = str(
        bucket_policy.get("split_variant_id") or ""
    ).strip() or _split_variant_id_from_fields(
        {
            "entry_split_order_policy_applied": True,
            "entry_split_order_policy_mode": policy_mode,
            "entry_split_order_leg_count": bucket_policy.get("leg_count"),
            "entry_split_order_price_offsets_ticks": ",".join(
                str(item) for item in (bucket_policy.get("price_offsets_ticks") or [])
            ),
            "entry_split_order_qty_weight_min": bucket_policy.get("qty_weight_min"),
        }
    )
    requested_legs = max(1, _safe_int(bucket_policy.get("leg_count"), 1))
    max_legs = _max_legs_for_qty(total_qty)
    desired_legs = min(requested_legs, max_legs, total_qty)
    if desired_legs <= 1:
        fields["entry_split_order_skip_reason"] = "single_leg_policy"
        fields["entry_split_order_bucket"] = bucket
        return orders, fields
    base_order = orders[0]
    base_price = _safe_int(
        base_order.get("price")
        or latency_gate.get("order_price")
        or latency_gate.get("resolved_order_price")
        or latency_gate.get("best_bid")
        or stock.get("curr_price"),
        0,
    )
    if base_price <= 0:
        fields["entry_split_order_skip_reason"] = "invalid_base_price"
        fields["entry_split_order_bucket"] = bucket
        return orders, fields
    tick = _tick_size(base_price)
    offsets = [
        _safe_int(item, 0)
        for item in (bucket_policy.get("price_offsets_ticks") or [0])
        if _safe_int(item, 0) in {0, 1, 2}
    ][:desired_legs]
    while len(offsets) < desired_legs:
        offsets.append(offsets[-1] + 1 if offsets else 0)
    policy_first_weight = _safe_float(bucket_policy.get("qty_weight_min"), 0.5) or 0.5
    market_first_leg_active = _market_first_leg_active(now=now)
    if market_first_leg_active:
        first_weight = policy_first_weight
        passive_bias_reason = ""
    else:
        first_weight, passive_bias_reason = _entry_split_passive_bias_first_weight(
            policy_first_weight,
            context_fields,
        )
    runtime_weight_adjusted = (
        abs(float(first_weight) - float(policy_first_weight)) > 0.000001
    )
    split_variant_id = policy_split_variant_id
    leg_count_clipped = desired_legs != requested_legs
    if leg_count_clipped:
        split_variant_id = f"{split_variant_id}__qty_clipped_legs{desired_legs}"
    if runtime_weight_adjusted:
        split_variant_id = f"{split_variant_id}__runtime_first_weight_{int(round(first_weight * 100)):02d}"
    quantities = _split_qty(total_qty, desired_legs, first_weight)
    applied_offsets = offsets[:desired_legs]
    raw_pct_offsets = bucket_policy.get("price_offsets_pct")
    pct_offsets = (
        [max(0.0, _safe_float(item, 0.0) or 0.0) for item in raw_pct_offsets][
            :desired_legs
        ]
        if isinstance(raw_pct_offsets, list)
        else []
    )
    while pct_offsets and len(pct_offsets) < desired_legs:
        pct_offsets.append(pct_offsets[-1])
    market_first_reference_price = _market_first_leg_reference_price(
        context_fields, base_price
    )
    probe_config = _probe_runtime_config(now=now)
    probe_eligible, probe_eligibility_reason = _probe_first_eligible(stock, total_qty)
    runtime_shape_gate = bucket_policy.get("runtime_shape_gate")
    shape_gate_passed, shape_gate_reason = _runtime_shape_gate_status(
        runtime_shape_gate,
        policy_split_variant_id=policy_split_variant_id,
        requested_legs=requested_legs,
        desired_legs=desired_legs,
        first_weight=first_weight,
        runtime_weight_adjusted=runtime_weight_adjusted,
        market_first_leg_active=market_first_leg_active,
        probe_enabled=_safe_bool(probe_config.get("enabled")),
        probe_eligible=probe_eligible,
    )
    if operating_template and (market_first_leg_active or probe_config["enabled"] or runtime_weight_adjusted
            or desired_legs != operating_template["leg_count"] or applied_offsets != operating_template["price_offsets_ticks"]):
        fields["entry_split_order_operating_shape_mismatch"] = dict(market_first=market_first_leg_active,probe=probe_config["enabled"],weight_adjusted=runtime_weight_adjusted,weight=first_weight,legs=desired_legs,offsets=applied_offsets)
        fields["entry_split_order_skip_reason"] = "operating_verified_shape_changed_by_runtime_guard"
        return orders, fields
    if not shape_gate_passed:
        fields.update(
            {
                "entry_split_order_bucket": bucket,
                "entry_split_order_policy_variant_id": policy_split_variant_id,
                "entry_split_order_runtime_shape_gate": runtime_shape_gate,
                "entry_split_order_skip_reason": (
                    f"runtime_shape_gate_mismatch:{shape_gate_reason}"
                ),
            }
        )
        return orders, fields
    if probe_config["enabled"] and probe_eligible:
        probe_variant_id = f"{split_variant_id}__{PROBE_VARIANT_SUFFIX}"
        common_fields = {
            "entry_split_order_policy_applied": True,
            "entry_split_order_policy_version": policy.get("policy_version"),
            "entry_split_order_policy_mode": policy_mode,
            "entry_split_order_variant_id": probe_variant_id,
            "entry_split_order_policy_variant_id": policy_split_variant_id,
            "entry_split_order_bucket": bucket,
            "entry_split_order_runtime_default_policy_applied": fallback_policy_applied,
            "entry_split_order_operator_fallback_authorized": bool(
                policy.get("entry_split_order_operator_fallback_authorized")
            ),
            "entry_split_order_price_offsets_ticks": ",".join(
                str(item) for item in applied_offsets
            ),
            "entry_split_order_price_offsets_pct": (
                ",".join(str(item) for item in pct_offsets) if pct_offsets else ""
            ),
            "entry_split_order_qty_weight_min": first_weight,
            "entry_split_order_qty_weight_max": min(
                _safe_float(bucket_policy.get("qty_weight_max"), first_weight)
                or first_weight,
                first_weight,
            ),
        }
        continuation = _build_probe_continuation(
            base_order=base_order,
            total_qty=total_qty,
            desired_legs=desired_legs,
            first_weight=first_weight,
            applied_offsets=applied_offsets,
            pct_offsets=pct_offsets,
            common_fields=common_fields,
        )
        submit_ai_action = (
            str(latency_gate.get("entry_ai_submit_authority_action") or "")
            .strip()
            .upper()
        )
        submit_ai_result_source = (
            str(latency_gate.get("entry_ai_submit_authority_result_source") or "")
            .strip()
            .lower()
        )
        submit_ai_confirmed_at = _safe_float(
            latency_gate.get("entry_ai_submit_authority_confirmed_at"), 0.0
        )
        submit_ai_action_source = str(
            latency_gate.get("entry_ai_submit_authority_action_source") or ""
        ).strip()
        submit_ai_decision_trace_id = str(
            latency_gate.get("entry_ai_submit_authority_decision_trace_id") or ""
        ).strip()
        submit_ai_contract_trusted = bool(
            not _safe_bool(latency_gate.get("entry_ai_submit_authority_blocked", True))
            and submit_ai_action in {"BUY", "WAIT"}
            and submit_ai_result_source in {"live", "prior_valid"}
            and submit_ai_confirmed_at > 0
            and submit_ai_action_source.lower()
            not in {"", "-", "none", "not_available", "not_evaluated"}
            and submit_ai_decision_trace_id.lower()
            not in {"", "-", "none", "not_available", "not_evaluated"}
        )
        probe_submit_ai_contract = (
            {
                "ai_action_at_submit": submit_ai_action,
                "ai_result_source_at_submit": submit_ai_result_source,
                "ai_confirmed_at_submit": submit_ai_confirmed_at,
                "ai_action_source_at_submit": submit_ai_action_source,
                "wait_contract_at_submit": bool(
                    submit_ai_action == "WAIT"
                    and _safe_bool(
                        latency_gate.get(
                            "entry_ai_submit_authority_wait_probe_required"
                        )
                    )
                ),
                "ai_decision_trace_id": submit_ai_decision_trace_id,
            }
            if submit_ai_contract_trusted
            else {}
        )
        if observation_only:
            return [], {**fields, "entry_split_order_skip_reason":
                        "unsupported_pre_ai_probe_reservation_scope"}
        bundle_id, reservation_reason = _reserve_probe_runtime_bundle(
            stock=stock,
            total_qty=total_qty,
            submit_contract={
                "continuation": continuation,
                "probe_submit_best_ask": market_first_reference_price,
                "timeout_sec": probe_config["timeout_sec"],
                "max_slippage_bps": probe_config["max_slippage_bps"],
                "anchor_mode": probe_config["anchor_mode"],
                # Freeze the same trusted Entry-AI contract that the submit
                # owner will attach to stock state.  Kiwoom can return a fill
                # before that later mutation completes; the reservation is
                # therefore the only race-safe recovery source for a WAIT
                # probe and must not degrade it to an unverified stale action.
                **probe_submit_ai_contract,
            },
            now=now,
        )
        if bundle_id:
            probe_order = {
                **base_order,
                **common_fields,
                "tag": "entry_split_probe_0",
                "qty": 1,
                "price": market_first_reference_price or base_price,
                "order_type_code": "3",
                "entry_split_order_leg_index": 0,
                "entry_split_order_execution_mode": "probe_first_market",
                "entry_split_order_probe_first_applied": True,
                "entry_split_order_probe_qty": 1,
                "entry_split_order_probe_bundle_id": bundle_id,
                "entry_split_order_probe_timeout_sec": probe_config["timeout_sec"],
                "entry_split_order_probe_max_slippage_bps": probe_config[
                    "max_slippage_bps"
                ],
                "entry_split_order_probe_anchor_mode": probe_config["anchor_mode"],
                "entry_split_order_probe_submit_best_ask": market_first_reference_price,
                "entry_split_order_probe_continuation": continuation,
                "entry_split_order_market_first_leg_applied": False,
                "entry_split_order_market_reference_price": market_first_reference_price,
                "split_leg_role": "probe",
                "split_price_offset_ticks": 0,
                "split_price_offset_pct": 0.0,
            }
            fields.update(
                {
                    **common_fields,
                    "entry_split_order_policy_applied": True,
                    "entry_split_order_skip_reason": "",
                    "entry_split_order_probe_first_enabled": True,
                    "entry_split_order_probe_first_applied": True,
                    "entry_split_order_probe_first_active_date": probe_config[
                        "active_date"
                    ],
                    "entry_split_order_probe_bundle_id": bundle_id,
                    "entry_split_order_probe_qty": 1,
                    "entry_split_order_probe_timeout_sec": probe_config["timeout_sec"],
                    "entry_split_order_probe_max_bundles": probe_config["max_bundles"],
                    "entry_split_order_probe_max_slippage_bps": probe_config[
                        "max_slippage_bps"
                    ],
                    "entry_split_order_probe_anchor_mode": probe_config["anchor_mode"],
                    "entry_split_order_probe_reservation_reason": reservation_reason,
                    "entry_split_order_market_first_leg_enabled": False,
                    "entry_split_order_market_first_leg_applied": False,
                    "entry_split_order_leg_count": 1
                    + _safe_int(continuation.get("residual_leg_count"), 0),
                    "entry_split_order_split_qty": total_qty,
                    "entry_split_order_price_offsets_ticks": ",".join(
                        str(item) for item in applied_offsets
                    ),
                    "entry_split_order_price_offsets_pct": (
                        ",".join(str(item) for item in pct_offsets)
                        if pct_offsets
                        else ""
                    ),
                    "entry_split_order_passive_bias_applied": bool(passive_bias_reason),
                    "entry_split_order_passive_bias_reason": passive_bias_reason,
                    "entry_split_order_policy_original_qty_weight_min": policy_first_weight,
                    "entry_split_order_passive_center_max_first_weight": PASSIVE_CENTER_MAX_FIRST_WEIGHT,
                    "entry_split_order_runtime_weight_adjustment_applied": runtime_weight_adjusted,
                }
            )
            return [probe_order], fields
        # Probe-first is the real SCALPING initial-entry contract.  Capacity
        # and circuit conditions defer the candidate to its next scanner-loop
        # evaluation; they must never fall through to a direct multi-leg order.
        fields.update(
            {
                "entry_split_order_skip_reason": reservation_reason,
                "entry_split_order_probe_first_enabled": True,
                "entry_split_order_probe_first_required": True,
                "entry_split_order_probe_first_applied": False,
                "entry_split_order_probe_first_skip_reason": reservation_reason,
                "entry_split_order_probe_capacity_deferred": True,
                "entry_split_order_probe_max_bundles": probe_config["max_bundles"],
                "entry_split_order_bucket": bucket,
                "entry_split_order_policy_version": policy.get("policy_version"),
                "entry_split_order_policy_mode": policy_mode,
            }
        )
        return [], fields
    elif probe_config["configured_enabled"]:
        fields["entry_split_order_probe_first_skip_reason"] = probe_eligibility_reason
    split_orders: list[dict[str, Any]] = []
    for idx, qty in enumerate(quantities):
        price = (
            _pct_price_offset(base_price, pct_offsets[idx])
            if pct_offsets
            else clamp_price_to_tick(max(1, base_price - (tick * offsets[idx])))
        )
        split_orders.append(
            {
                **base_order,
                "tag": (
                    "entry_split_primary" if idx == 0 else f"entry_split_passive_{idx}"
                ),
                "qty": qty,
                "price": price,
                "order_type_code": (
                    "3"
                    if market_first_leg_active and idx == 0
                    else base_order.get("order_type_code", "00")
                ),
                "entry_split_order_execution_mode": (
                    "market_first"
                    if market_first_leg_active and idx == 0
                    else "resolver_limit"
                ),
                "entry_split_order_market_first_leg_applied": bool(
                    market_first_leg_active and idx == 0
                ),
                "entry_split_order_market_reference_price": (
                    market_first_reference_price
                    if market_first_leg_active and idx == 0
                    else 0
                ),
                "entry_split_order_leg_index": idx + 1,
                "entry_split_order_policy_version": policy.get("policy_version"),
                "entry_split_order_policy_mode": policy_mode,
                "entry_split_order_variant_id": split_variant_id,
                "entry_split_order_policy_variant_id": policy_split_variant_id,
                "entry_split_order_bucket": bucket,
                "entry_split_order_runtime_default_policy_applied": fallback_policy_applied,
                "entry_split_order_operator_fallback_authorized": bool(
                    policy.get("entry_split_order_operator_fallback_authorized")
                ),
                "entry_split_order_price_offsets_ticks": ",".join(
                    str(item) for item in applied_offsets
                ),
                "entry_split_order_price_offsets_pct": (
                    ",".join(str(item) for item in pct_offsets) if pct_offsets else ""
                ),
                "entry_split_order_price_offset_ticks": applied_offsets[idx],
                "entry_split_order_price_offset_pct": (
                    pct_offsets[idx] if pct_offsets else ""
                ),
                "split_price_offset_ticks": applied_offsets[idx],
                "split_price_offset_pct": pct_offsets[idx] if pct_offsets else "",
                "split_leg_role": "primary" if idx == 0 else "passive",
                "entry_split_order_qty_weight_min": first_weight,
                "entry_split_order_qty_weight_max": min(
                    _safe_float(bucket_policy.get("qty_weight_max"), first_weight)
                    or first_weight,
                    first_weight,
                ),
                "entry_split_order_runtime_weight_adjustment_applied": runtime_weight_adjusted,
            }
        )
    if sum(_safe_int(item.get("qty"), 0) for item in split_orders) != total_qty:
        fields["entry_split_order_skip_reason"] = "quantity_conservation_failed"
        return orders, fields
    fields.update(
        {
            "entry_split_order_policy_applied": True,
            "entry_split_order_skip_reason": "",
            "entry_split_order_bucket": bucket,
            "entry_split_order_policy_version": policy.get("policy_version"),
            "entry_split_order_policy_mode": policy_mode,
            "entry_split_order_variant_id": split_variant_id,
            "entry_split_order_policy_variant_id": policy_split_variant_id,
            "entry_split_order_policy_requested_leg_count": requested_legs,
            "entry_split_order_max_leg_count_for_qty": max_legs,
            "entry_split_order_leg_count_clipped": leg_count_clipped,
            "entry_split_order_runtime_default_policy_applied": fallback_policy_applied,
            "entry_split_order_operator_fallback_authorized": bool(
                policy.get("entry_split_order_operator_fallback_authorized")
            ),
            "entry_split_order_market_first_leg_enabled": market_first_leg_active,
            "entry_split_order_market_first_leg_applied": market_first_leg_active,
            "entry_split_order_market_first_leg_active_date": str(
                os.environ.get("KORSTOCKSCAN_ENTRY_SPLIT_MARKET_FIRST_LEG_ACTIVE_DATE")
                or ""
            ),
            "entry_split_order_market_first_leg_qty": (
                quantities[0] if market_first_leg_active else 0
            ),
            "entry_split_order_market_reference_price": (
                market_first_reference_price if market_first_leg_active else 0
            ),
            "entry_split_order_policy_file": policy_file
            or os.environ.get("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_FILE"),
            "entry_split_order_leg_count": len(split_orders),
            "entry_split_order_split_qty": sum(
                _safe_int(item.get("qty"), 0) for item in split_orders
            ),
            "entry_split_order_price_offsets_ticks": ",".join(
                str(item) for item in applied_offsets
            ),
            "entry_split_order_price_offsets_pct": (
                ",".join(str(item) for item in pct_offsets) if pct_offsets else ""
            ),
            "entry_split_order_qty_weight_min": first_weight,
            "entry_split_order_qty_weight_max": min(
                _safe_float(bucket_policy.get("qty_weight_max"), first_weight)
                or first_weight,
                first_weight,
            ),
            "entry_split_order_passive_bias_applied": bool(passive_bias_reason),
            "entry_split_order_passive_bias_reason": passive_bias_reason,
            "entry_split_order_policy_original_qty_weight_min": policy_first_weight,
            "entry_split_order_passive_center_max_first_weight": PASSIVE_CENTER_MAX_FIRST_WEIGHT,
            "entry_split_order_runtime_weight_adjustment_applied": runtime_weight_adjusted,
        }
    )
    return split_orders, fields


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--date",
        "--target-date",
        dest="target_date",
        default=datetime.now().strftime("%Y-%m-%d"),
    )
    parser.add_argument("--no-write", action="store_true")
    parser.add_argument("--refresh-execution-model-only", action="store_true",
                        help="Refresh the existing exact-date model section without raw/grid replay.")
    parser.add_argument("--prepared-effective-date", default=None)
    args = parser.parse_args(argv)
    if args.refresh_execution_model_only:
        report = refresh_execution_model_only(args.target_date,
            prepared_effective_date=args.prepared_effective_date, write=not args.no_write)
        print(json.dumps({"date": args.target_date,
            "model_status": report["execution_model_validation"]["status"],
            "runtime_apply_allowed": report["recommended_policy"]["runtime_apply_allowed"],
            "generation": report["artifact_generation_binding"]["generation_id"]}))
    else:
        build_report(args.target_date, write=not args.no_write)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
