"""Entry split order plan report and bounded runtime allocator."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import threading
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Any

from src.engine.automation.source_quality_clean_baseline import (
    clean_baseline_policy,
    is_date_allowed,
)
from src.trading.order.tick_utils import clamp_price_to_tick, get_tick_size
from src.utils.constants import DATA_DIR, PROJECT_ROOT
from src.utils.jsonl_io import existing_or_gzip_path, iter_jsonl, open_text_auto

SCHEMA_VERSION = "entry_split_order_plan_v1"
POLICY_SCHEMA_VERSION = "entry_split_order_policy_v1"
REPORT_TYPE = "entry_split_order_plan"
RUNTIME_FAMILY = "entry_split_order_plan"
REPORT_DIR = DATA_DIR / "report" / REPORT_TYPE
POLICY_DIR = DATA_DIR / "threshold_cycle" / "entry_split_order_policy"
SAMPLE_FLOOR_REAL = 20
SAMPLE_FLOOR_SIM = 10
CUMULATIVE_LEARNING_SAMPLE_FLOOR = 1
SPLIT_VARIANT_OUTCOME_FLOOR_REAL = 20
POST_SUBMIT_TICK_BAND_FLOOR_REAL = 20
POST_SUBMIT_LOW_WINDOW_MINUTES = 10
POLICY_MODE_REAL_PRIMARY_EV = "real_primary_ev_optimized"
POLICY_MODE_BOUNDED_EQUAL_BASELINE = "bounded_equal_split_baseline"
POLICY_MODE_POST_SUBMIT_TICK_BAND = "post_submit_tick_band_seed"
RUNTIME_APPLY_COMPATIBILITY_SEMANTICS = (
    "union_of_exploration_seed_allowed_and_ev_validated_runtime_apply_allowed"
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
        "entry_split_order_variant_id",
        "entry_split_order_leg_count",
        "entry_split_order_price_offsets_ticks",
        "entry_split_order_qty_weight_min",
        "entry_split_order_qty_weight_max",
        "entry_split_order_runtime_default_policy_applied",
        "entry_split_order_operator_fallback_authorized",
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
        missing_contract = {
            key: value
            for key, value in recovered_contract.items()
            if stock.get(key) in (None, "")
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
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


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
    clean_policy = clean_baseline_policy()
    source_quality = _source_quality_summary(target_date)
    hard_blocking_stages = set(source_quality.get("hard_blocking_stages") or [])
    events: list[dict[str, Any]] = []
    excluded_pre_baseline = 0
    source_paths = {
        "pipeline_events": _pipeline_events_path(target_date),
        "threshold_events": _threshold_events_path(target_date),
    }
    for source_name, path in source_paths.items():
        for event in _iter_entry_split_input_rows(
            path, hard_blocking_stages=hard_blocking_stages
        ):
            fields = _event_fields(event)
            event_date = _event_date(fields) or target_date
            if not is_date_allowed(event_date, clean_policy):
                excluded_pre_baseline += 1
                continue
            stage = str(fields.get("stage") or fields.get("event") or "").strip()
            has_post_submit_price = bool(
                fields.get("record_id")
                and fields.get("stock_code")
                and any(
                    _safe_int(fields.get(key), 0) > 0
                    for key in (
                        "current_price_observed",
                        "current_price",
                        "latest_price",
                        "holding_ws_recovered_curr",
                        "curr_price",
                        "mark_price_at_submit",
                        "submitted_mark_price",
                    )
                )
            )
            calibration_relevant = bool(
                stage.startswith("scalp_sim_")
                or stage in hard_blocking_stages
                or stage
                in {
                    "order_bundle_submitted",
                    "order_leg_sent",
                    "order_leg_fail",
                    "order_bundle_failed",
                }
                or has_post_submit_price
            )
            if not calibration_relevant:
                continue
            fields = {
                key: value
                for key, value in fields.items()
                if key in CALIBRATION_EVENT_KEYS
            }
            fields["source_name"] = source_name
            fields["source_date"] = event_date
            events.append(fields)
    return events, {
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
        "order_bundle_submitted",
        "order_leg_sent",
        "order_leg_fail",
        "order_bundle_failed",
        *hard_blocking_stages,
    }
    price_tokens = (
        '"current_price_observed"',
        '"current_price"',
        '"latest_price"',
        '"holding_ws_recovered_curr"',
        '"curr_price"',
        '"mark_price_at_submit"',
        '"submitted_mark_price"',
    )
    with open_text_auto(actual_path) as handle:
        for raw_line in handle:
            if (
                "scalp_sim_" not in raw_line
                and not any(token in raw_line for token in stage_tokens)
                and not any(token in raw_line for token in price_tokens)
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


def _iter_cumulative_input_events(
    target_date: str,
) -> tuple[
    list[dict[str, Any]],
    dict[str, Any],
    dict[str, dict[str, Any]],
]:
    events: list[dict[str, Any]] = []
    source_quality_by_date: dict[str, dict[str, Any]] = {}
    source_paths_by_date: dict[str, Any] = {}
    excluded_pre_baseline = 0
    for source_date in _available_calibration_dates(target_date):
        source_quality_by_date[source_date] = _source_quality_summary(source_date)
        if source_date == target_date:
            daily_events, daily_summary = _iter_input_events(source_date)
            events.extend(daily_events)
            source_paths_by_date[source_date] = daily_summary.get("source_paths") or {}
            excluded_pre_baseline += _safe_int(
                daily_summary.get("excluded_pre_baseline_count"), 0
            )
        else:
            source_paths_by_date[source_date] = {
                "pipeline_events": _existing_jsonl_source(
                    _pipeline_events_path(source_date)
                ),
                "threshold_events": _existing_jsonl_source(
                    _threshold_events_path(source_date)
                ),
                "read_mode": "post_sell_outcome_only_for_cumulative_rebuild",
            }
    return (
        events,
        {
            "source_paths": source_paths_by_date.get(target_date, {}),
            "source_paths_by_date": source_paths_by_date,
            "source_dates": sorted(source_quality_by_date),
            "source_date_count": len(source_quality_by_date),
            "excluded_pre_baseline_count": excluded_pre_baseline,
            "clean_tuning_baseline": clean_baseline_policy(),
        },
        source_quality_by_date,
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
    "entry_split_order_variant_id",
    "entry_split_order_leg_count",
    "entry_split_order_price_offsets_ticks",
    "entry_split_order_qty_weight_min",
    "entry_split_order_qty_weight_max",
    "entry_split_order_runtime_default_policy_applied",
    "entry_split_order_operator_fallback_authorized",
)


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
        _event_fields(item)
        for item in iter_jsonl(_real_post_sell_candidate_path(target_date))
    ]
    evaluations = [
        _event_fields(item) for item in iter_jsonl(_real_post_sell_path(target_date))
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
        state = (
            payload.get("cumulative_state")
            if isinstance(payload.get("cumulative_state"), dict)
            else {}
        )
        if (
            payload.get("schema_version") == SCHEMA_VERSION
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
            try:
                report_mtime = path.stat().st_mtime
            except OSError:
                continue
            state_is_current = True
            for state_source_date in source_dates:
                quality = _source_quality_summary(state_source_date)
                quality_path = _source_quality_path(state_source_date)
                if quality.get("tuning_input_allowed") is not True:
                    state_is_current = False
                    break
                try:
                    if quality_path.stat().st_mtime > report_mtime:
                        state_is_current = False
                        break
                except OSError:
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
        if not _split_variant_id_from_fields(next_row):
            recommendation_id = _identifier(
                next_row.get("recommendation_id") or next_row.get("record_id")
            )
            provenance = provenance_by_recommendation.get(
                (_provenance_date(next_row), recommendation_id)
            )
            if provenance:
                next_row.update(provenance)
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
    explicit = str(fields.get("entry_split_order_variant_id") or "").strip()
    if explicit:
        return explicit
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


def _load_real_split_variant_ev_values(
    target_date: str, rows: list[dict[str, Any]] | None = None
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
        if not _safe_bool(fields.get("actual_order_submitted")):
            continue
        variant_id = _split_variant_id_from_fields(fields)
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


def _pct_price_offset(base_price: int, offset_pct: float) -> int:
    if base_price <= 0:
        return 0
    raw_price = int(
        round(float(base_price) * max(0.0, 1.0 - (float(offset_pct or 0.0) / 100.0)))
    )
    return clamp_price_to_tick(max(1, raw_price))


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


def _build_post_submit_low_tick_bands(
    events: list[dict[str, Any]],
    *,
    source_quality: dict[str, Any] | None = None,
    window_minutes: int = POST_SUBMIT_LOW_WINDOW_MINUTES,
) -> dict[str, dict[str, Any]]:
    blocked_stages = set((source_quality or {}).get("hard_blocking_stages") or [])
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for fields in events:
        stage = str(fields.get("stage") or fields.get("event") or "").strip()
        if stage in blocked_stages:
            continue
        record_id = str(fields.get("record_id") or "").strip()
        code = str(fields.get("stock_code") or "").strip()
        if not record_id or not code:
            continue
        grouped[(record_id, code)].append(fields)

    down_ticks_by_bucket: dict[str, list[int]] = defaultdict(list)
    down_pct_by_bucket: dict[str, list[float]] = defaultdict(list)
    for group in grouped.values():
        dated = [(item, _event_dt(item)) for item in group]
        for submit, submit_dt in dated:
            stage = str(submit.get("stage") or submit.get("event") or "").strip()
            if stage != "order_bundle_submitted":
                continue
            if not _safe_bool(submit.get("actual_order_submitted")):
                continue
            if submit_dt is None:
                continue
            submit_price = _submit_order_price(submit)
            if submit_price <= 0:
                continue
            observed_prices: list[int] = []
            for item, item_dt in dated:
                if item_dt is None:
                    continue
                if item_dt < submit_dt:
                    continue
                if item_dt > submit_dt + timedelta(minutes=window_minutes):
                    continue
                observed_prices.extend(_post_submit_observed_prices(item))
            if not observed_prices:
                continue
            low_price = min(observed_prices)
            tick = max(1, int(get_tick_size(submit_price) or 1))
            down_ticks = max(0, int(math.ceil((submit_price - low_price) / tick)))
            down_pct = max(0.0, ((submit_price - low_price) / submit_price) * 100.0)
            bucket = _context_bucket(submit)
            down_ticks_by_bucket[bucket].append(down_ticks)
            down_pct_by_bucket[bucket].append(down_pct)

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


def _is_real_submit_event(fields: dict[str, Any]) -> bool:
    stage = str(fields.get("stage") or fields.get("event") or "").strip()
    return bool(
        _safe_bool(fields.get("actual_order_submitted"))
        and stage in {"order_bundle_submitted", "order_leg_sent"}
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
        if _is_real_submit_event(fields):
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
        if _safe_bool(fields.get("actual_order_submitted")) and stage in {
            "order_leg_fail",
            "order_bundle_failed",
        }:
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
    post_submit_low_tick_bands: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    grid: list[dict[str, Any]] = []
    real_split_variant_ev_values = real_split_variant_ev_values or {}
    post_submit_low_tick_bands = post_submit_low_tick_bands or {}
    split_variant_buckets = {
        bucket for bucket, _variant_id in real_split_variant_ev_values
    }
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
        real_count = max(event_real_count, real_bucket_outcome_count)
        total = max(1, real_count + sim_count)
        real_bucket_ev = round(mean(real_ev_list), 4) if real_ev_list else None
        sim_ev = round(mean(sim_ev_list), 4) if sim_ev_list else None
        split_variant_id = ""
        if bucket != "guarded_or_stale":
            template = _post_submit_tick_band_template(bucket, tick_band)
            split_variant_id = BASELINE_SPLIT_VARIANT_ID
            if template.get("split_variant_id"):
                split_variant_id = str(
                    template.get("split_variant_id") or BASELINE_SPLIT_VARIANT_ID
                )
        split_variant_ev_list = (
            real_split_variant_ev_values.get((bucket, split_variant_id))
            if split_variant_id
            else []
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
                        and variant_ev > 0
                        and variant_downside_p10 is not None
                        and variant_downside_p10 > -2.0
                    ),
                    "runtime_promotion_requires_shape_provenance": True,
                }
            )
        observed_split_outcome_count = sum(
            _safe_int(item.get("sample_count"), 0) for item in observed_split_variants
        )
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
            bucket != "guarded_or_stale"
            and real_count >= SAMPLE_FLOOR_REAL
            and split_variant_outcome_ready
            and split_variant_ev is not None
            and split_variant_ev > 0
            and downside > -2.0
        )
        execution_shape_seed_passed = (
            bucket != "guarded_or_stale"
            and real_count >= SAMPLE_FLOOR_REAL
            and not split_variant_outcome_ready
            and cancel_rate <= 20.0
            and late_fill_rate <= 20.0
        )
        policy_mode = ""
        policy_generation_reason = ""
        if ev_passed:
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
        elif split_variant_outcome_ready:
            floor_status = "hold_no_split_variant_edge"
            primary_sample_book = "real_split_variant"
        elif sim_count >= SAMPLE_FLOOR_SIM and sim_ev is not None:
            floor_status = "hold_real_outcome_pending"
            primary_sample_book = "sim_diagnostic"
        else:
            floor_status = "hold_real_outcome_pending"
            primary_sample_book = "real_outcome_pending"
        passed = ev_passed or execution_shape_seed_passed
        runtime_apply_scope = (
            "ev_optimized_variant" if ev_passed else "baseline_split_structure"
        )
        runtime_apply_authority_class = (
            "ev_validated_variant"
            if ev_passed
            else ("bounded_exploration_seed" if execution_shape_seed_passed else "none")
        )
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
                "sim_sample_count": sim_count,
                "real_outcome_joined_sample": real_bucket_outcome_count,
                "real_bucket_outcome_ev_pct": real_bucket_ev,
                "real_split_variant_outcome_joined_sample": split_variant_outcome_count,
                "real_split_variant_ev_pct": split_variant_ev,
                "observed_real_split_outcome_count": observed_split_outcome_count,
                "observed_real_split_variants": observed_split_variants,
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
                    },
                    "split_variant_quality": split_variant_judgment_quality,
                    "learning_floor_grants_runtime_promotion": False,
                },
                "split_variant_id": split_variant_id,
                "optimization_basis": (
                    "split_variant_outcome"
                    if ev_passed
                    else (
                        "post_submit_observed_low_tick_band"
                        if policy_mode == POLICY_MODE_POST_SUBMIT_TICK_BAND
                        else "bounded_execution_shape_seed"
                    )
                ),
                "post_submit_low_tick_band": tick_band,
                "primary_sample_book": primary_sample_book,
                "fill_quality": round(
                    (
                        _safe_int(counts.get("real_submitted_count"), 0)
                        + _safe_int(counts.get("sim_fill_count"), 0)
                    )
                    / total,
                    4,
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
                "exploration_seed_allowed": execution_shape_seed_passed,
                "ev_validated_runtime_apply_allowed": ev_passed,
                "runtime_apply_allowed": passed,
                "runtime_apply_scope": runtime_apply_scope if passed else "none",
                "runtime_apply_authority_class": runtime_apply_authority_class,
                "runtime_apply_reason": (
                    "positive_split_variant_ev_passed"
                    if ev_passed
                    else (
                        "qty_preserving_execution_shape_seed_passed"
                        if execution_shape_seed_passed
                        else floor_status
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
            "cancel_rate_delta",
            "missed_upside_rate_delta",
            "source_quality_adjusted_ev_pct_delta",
        ],
        "separate_partial_and_full_fill": True,
    }
    rollback_guard = {
        "action": "carry_forward_previous_runtime_policy",
        "triggers": [
            "worse_fill_rate_without_ev_gain",
            "higher_cancel_rate",
            "higher_missed_upside_rate",
            "negative_post_apply_source_quality_adjusted_ev_delta",
            "source_quality_or_provenance_breach",
        ],
    }
    return {
        "schema_version": POLICY_SCHEMA_VERSION,
        "policy_version": policy_version,
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
        "baseline_runtime_defaults_enabled": any(
            item.get("runtime_apply_scope") == "baseline_split_structure"
            for item in passed
        ),
        "explicit_bucket_count": len(explicit_bucket_candidates),
        "preopen_guard_required": True,
        "runtime_apply_scope": runtime_apply_scopes,
        "post_apply_attribution": post_apply_attribution,
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


def build_report(target_date: str, *, write: bool = True) -> dict[str, Any]:
    target_date = str(target_date).strip()
    source_quality = _source_quality_summary(target_date)
    daily_events, daily_load_summary = _iter_input_events(target_date)
    daily_allowed_events, daily_excluded_source_quality = (
        _source_quality_filtered_events(daily_events, {target_date: source_quality})
    )
    daily_counts, _ = _quality_counts(
        daily_allowed_events, {"tuning_input_allowed": True}
    )
    prior_state, prior_state_path = _latest_prior_cumulative_state(target_date)
    if prior_state:
        events = daily_events
        calibration_events = daily_allowed_events
        excluded_source_quality = daily_excluded_source_quality
        counts = _merge_count_maps(prior_state.get("counts") or {}, daily_counts)
        sim_ev_values = _deserialize_value_map(prior_state.get("sim_ev_values"))
        real_ev_values = _deserialize_value_map(prior_state.get("real_ev_values"))
        real_split_variant_ev_values = _deserialize_variant_value_map(
            prior_state.get("real_split_variant_ev_values")
        )
        real_post_sell_summary = {
            key: _safe_int(value, 0)
            for key, value in (prior_state.get("real_post_sell_summary") or {}).items()
        }
        source_dates = list(prior_state.get("source_dates") or [])
        reconstructed_provenance_count = _safe_int(
            prior_state.get("reconstructed_split_provenance_count"), 0
        )
        if source_quality.get("tuning_input_allowed") is True:
            _extend_value_map(sim_ev_values, _load_sim_ev_values(target_date))
            real_post_sell_rows, source_summary = _load_real_post_sell_rows(target_date)
            real_post_sell_rows, reconstructed_today = (
                _enrich_real_post_sell_provenance(
                    real_post_sell_rows, calibration_events
                )
            )
            reconstructed_provenance_count += reconstructed_today
            for key, value in source_summary.items():
                real_post_sell_summary[key] = _safe_int(
                    real_post_sell_summary.get(key), 0
                ) + _safe_int(value, 0)
            _extend_value_map(
                real_ev_values,
                _load_real_ev_values(target_date, real_post_sell_rows),
            )
            _extend_value_map(
                real_split_variant_ev_values,
                _load_real_split_variant_ev_values(target_date, real_post_sell_rows),
            )
            if target_date not in source_dates:
                source_dates.append(target_date)
        load_summary = {
            "aggregation_mode": "incremental_from_prior_cumulative_state",
            "prior_cumulative_state_path": prior_state_path,
            "source_paths": daily_load_summary.get("source_paths") or {},
            "source_paths_by_date": {
                target_date: daily_load_summary.get("source_paths") or {}
            },
            "source_dates": sorted(source_dates),
            "source_date_count": len(set(source_dates)),
            "excluded_pre_baseline_count": _safe_int(
                daily_load_summary.get("excluded_pre_baseline_count"), 0
            ),
            "clean_tuning_baseline": clean_baseline_policy(),
        }
    else:
        events, load_summary, source_quality_by_date = _iter_cumulative_input_events(
            target_date
        )
        calibration_events, excluded_source_quality = _source_quality_filtered_events(
            events, source_quality_by_date
        )
        counts, _ = _quality_counts(calibration_events, {"tuning_input_allowed": True})
        sim_ev_values: dict[str, list[float]] = defaultdict(list)
        real_post_sell_rows: list[dict[str, Any]] = []
        real_post_sell_summary = {
            "candidate_count": 0,
            "evaluation_count": 0,
            "matched_evaluation_count": 0,
            "pending_evaluation_count": 0,
            "merged_count": 0,
        }
        included_source_dates: list[str] = []
        for source_date in load_summary.get("source_dates") or []:
            source_date_quality = source_quality_by_date.get(source_date) or {}
            if source_date_quality.get("tuning_input_allowed") is not True:
                continue
            included_source_dates.append(source_date)
            _extend_value_map(sim_ev_values, _load_sim_ev_values(source_date))
            source_rows, source_summary = _load_real_post_sell_rows(source_date)
            real_post_sell_rows.extend(source_rows)
            for key in real_post_sell_summary:
                real_post_sell_summary[key] += _safe_int(source_summary.get(key), 0)
        real_post_sell_rows, reconstructed_provenance_count = (
            _enrich_real_post_sell_provenance(real_post_sell_rows, calibration_events)
        )
        real_ev_values = defaultdict(list)
        real_split_variant_ev_values = defaultdict(list)
        for source_date in included_source_dates:
            source_rows = [
                row
                for row in real_post_sell_rows
                if _provenance_date(row) == source_date
            ]
            _extend_value_map(
                real_ev_values, _load_real_ev_values(source_date, source_rows)
            )
            _extend_value_map(
                real_split_variant_ev_values,
                _load_real_split_variant_ev_values(source_date, source_rows),
            )
        load_summary["aggregation_mode"] = "full_clean_baseline_rebuild"
        load_summary["source_dates"] = included_source_dates
        load_summary["source_date_count"] = len(included_source_dates)
    post_submit_low_tick_bands = _build_post_submit_low_tick_bands(
        daily_allowed_events,
        source_quality={"hard_blocking_stages": []},
    )
    candidate_grid = _build_candidate_grid(
        counts,
        sim_ev_values,
        real_ev_values,
        real_split_variant_ev_values,
        post_submit_low_tick_bands,
    )
    for item in candidate_grid:
        bucket = str(item.get("context_bucket") or "")
        target_counts = daily_counts.get(bucket) or {}
        item["target_date_contribution"] = {
            "date": target_date,
            "real_sample_count": _safe_int(target_counts.get("real_sample_count"), 0),
            "sim_sample_count": _safe_int(target_counts.get("sim_sample_count"), 0),
        }
    json_path, md_path = report_paths(target_date)
    policy_json = policy_path(target_date)
    source_quality_allowed = source_quality.get("tuning_input_allowed") is True
    policy = _policy_payload(
        target_date, json_path, candidate_grid if source_quality_allowed else []
    )
    recommended_candidates = [
        item
        for item in candidate_grid
        if source_quality_allowed and item.get("candidate_passed")
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
                "or entry_split_order_variant_id is observed; record-level opportunity EV alone cannot claim "
                "split-policy execution quality."
            ),
            "primary_decision_metric": "source_quality_adjusted_ev_pct",
            "primary_decision_metric_scope": "ev_validated_variant_only",
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
            "policy_modes": {
                POLICY_MODE_REAL_PRIMARY_EV: "real split-variant outcome EV-positive optimized split",
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
                "entry_split_order_variant_id. Bucket-only sell outcome is diagnostic."
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
            "real_post_sell_summary": real_post_sell_summary,
            "reconstructed_split_provenance_count": (reconstructed_provenance_count),
        },
        "input_summary": {
            **load_summary,
            "loaded_event_count": len(events),
            "included_calibration_event_count": len(calibration_events),
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
            "rollback_guard": policy.get("rollback_guard") or {},
            "baseline_runtime_defaults_enabled": policy.get(
                "baseline_runtime_defaults_enabled"
            )
            is True,
            "explicit_bucket_count": _safe_int(policy.get("explicit_bucket_count"), 0),
            "preopen_guard_required": True,
            "policy_file": str(policy_json),
            "policy_version": policy["policy_version"],
            "candidate_count": len(recommended_candidates),
            "candidates": recommended_candidates,
        },
    }
    if write:
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
        f"- baseline_runtime_defaults_enabled: `{rec.get('baseline_runtime_defaults_enabled')}`",
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
    authority_valid, authority_reason = runtime_apply_authority_contract_status(payload)
    if not authority_valid:
        return {}, f"invalid_policy_authority_contract:{authority_reason}"
    payload = {**payload, "runtime_apply_authority_contract": authority_reason}
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


def _max_legs_for_qty(qty: int) -> int:
    if qty <= 1:
        return 1
    if qty == 2:
        return 2
    if 3 <= qty <= 5:
        return 2
    return 3


def _split_qty(total_qty: int, leg_count: int, first_weight: float) -> list[int]:
    leg_count = min(max(1, leg_count), total_qty)
    if leg_count <= 1:
        return [total_qty]
    first_qty = max(
        1, min(total_qty - (leg_count - 1), int(round(total_qty * first_weight)))
    )
    remaining = total_qty - first_qty
    quantities = [first_qty]
    for idx in range(leg_count - 1):
        legs_left = leg_count - 1 - idx
        qty = max(1, remaining // legs_left)
        quantities.append(qty)
        remaining -= qty
    if sum(quantities) != total_qty:
        quantities[-1] += total_qty - sum(quantities)
    return quantities


def _tick_size(price: int) -> int:
    try:
        from src.utils import kiwoom_utils

        return max(1, int(kiwoom_utils.get_tick_size(price) or 1))
    except Exception:
        return 1


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
        bucket_policy = _runtime_default_bucket_policy(bucket)
        fallback_policy_applied = True
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
    args = parser.parse_args(argv)
    build_report(args.target_date, write=not args.no_write)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
