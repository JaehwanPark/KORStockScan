"""Past-only micro-reversion sidecar for Exact V2 AI quality replay.

This module deliberately stays outside the live AI and order paths.  It joins
immutable Exact V2 request provenance to already-persisted 0B/0D observations,
builds a compact tactical context, and keeps future outcomes in a separate
label.  The original provider payload and its hash are never modified.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import os
import tempfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from src.utils.constants import DATA_DIR

from .contracts import CLEAN_BASELINE_DATE, normalize_symbol, normalize_venue
from .depth_join import validate_depth_row
from .p2_replay import (
    DEFAULT_SOURCE_EXCLUSION_MANIFEST,
    load_source_exclusion_manifest,
)
from .path_journal import (
    MARKET_STREAM_CONTRACT_ID,
    validate_market_stream_path_provenance,
)

TACTICAL_EVIDENCE_SCHEMA = "tactical_micro_reversion_evidence_v1"
LIFECYCLE_PROJECTION_SCHEMA = "micro_reversion_fast_lifecycle_projection_v1"
OUTCOME_SCHEMA = "micro_reversion_ai_quality_outcome_v1"
THREE_ARM_SCHEMA = "micro_reversion_ai_quality_three_arm_manifest_v1"
REPORT_SCHEMA = "micro_reversion_ai_quality_bridge_v1"

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
        "exact_v2_scope_nonfuture_monotonic_fresh_bbo_depth_no_imputation"
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


@dataclass(frozen=True, slots=True)
class BridgeConfig:
    context_lookback_sec: int = 30
    active_wave_max_age_sec: int = 180
    max_market_age_ms: int = 2_500
    max_depth_age_ms: int = 1_000
    max_quote_age_ms: int = 1_000
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
    cost_profile_source: str = "missing_verified_instrument_cost_profile"
    cost_profile_verified: bool = False

    def __post_init__(self) -> None:
        if self.context_lookback_sec <= 0 or self.active_wave_max_age_sec <= 0:
            raise ValueError("context windows must be positive")
        if (
            self.max_market_age_ms < 0
            or self.max_depth_age_ms < 0
            or self.max_quote_age_ms < 0
        ):
            raise ValueError("freshness limits must not be negative")
        if self.tape_capacity_window_sec <= 0 or self.target_liquidation_sec <= 0:
            raise ValueError("liquidation windows must be positive")
        if (
            not self.participation_grid
            or tuple(sorted(set(self.participation_grid)))
            != self.participation_grid
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
            if getattr(self, field) < 0:
                raise ValueError(f"{field} must not be negative")
        if self.statutory_sell_tax_bps is not None and (
            self.statutory_sell_tax_bps < 0
        ):
            raise ValueError("statutory_sell_tax_bps must not be negative")
        if self.adverse_label_bps >= 0:
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
            or self.outcome_horizons_sec[0] <= 0
        ):
            raise ValueError("outcome horizons must be sorted unique positive values")


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
    stage = str(
        trace.get("decision_stage") or trace.get("endpoint") or ""
    ).strip().lower()
    if stage in {
        "entry",
        "entry_screen",
        "analyze_target",
        "entry_price",
        "post_probe",
        "scale_in",
    }:
        return ENTRY_CONTEXT_SCHEMA
    if stage in {
        "holding",
        "holding_score",
        "holding_flow",
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

    contexts = []
    for row in _walk_objects(exact_payload):
        if row.get("schema") == expected_schema:
            contexts.append(row)
    if len(contexts) != 1:
        findings.append(
            "canonical_context_missing"
            if not contexts
            else "canonical_context_ambiguous"
        )
        return tuple(sorted(set(findings)))
    context = contexts[0]
    candle = (
        context.get("candle")
        if expected_schema == HOLDING_CONTEXT_SCHEMA
        else context
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
            "is_forming"
            if expected_schema == HOLDING_CONTEXT_SCHEMA
            else "forming"
        )
        if not any(
            isinstance(bar, Mapping) and not bool(bar.get(forming_key, False))
            for bar in bars
        ):
            findings.append("canonical_completed_bars_missing")
    trace_venue = normalize_venue(trace.get("effective_venue"))
    trace_session = _session(trace.get("session_bucket"))
    scope_context = (
        context if expected_schema == HOLDING_CONTEXT_SCHEMA else candle
    )
    if normalize_venue(scope_context.get("venue")) != trace_venue:
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
    trace_replay_present = trace.get("replay_context_present") is True
    payload_replay_present = payload.get("replay_context_present") is True
    if trace_replay_present != payload_replay_present:
        blockers.append("replay_context_presence_mismatch")
    if payload_replay_present and (
        payload.get("replay_context_exact") is not True
        or trace.get("replay_context_exact") is not True
    ):
        blockers.append("replay_context_not_exact")
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
    for row in _walk_objects(source):
        if row.get("schema") != "ai_market_snapshot_v1":
            continue
        snapshot_symbol = normalize_symbol(row.get("stock_code"))
        if not snapshot_symbol:
            continue
        if trace_symbol and snapshot_symbol != trace_symbol:
            continue
        try:
            captured_at_ms = _timestamp_ms(row.get("captured_at"))
            captured_at_us = _timestamp_us(row.get("captured_at"))
        except (TypeError, ValueError):
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
    payload_venue = normalize_venue(payload.get("effective_venue"))
    payload_session = _session(payload.get("session_bucket"))
    if payload_venue != normalize_venue(trace.get("effective_venue")):
        blockers.append("payload_trace_venue_mismatch")
    if payload_session != trace_session:
        blockers.append("payload_trace_session_mismatch")
    return {
        "snapshot_id": snapshot.get("snapshot_id") or trace.get("snapshot_id"),
        "captured_at": snapshot.get("captured_at"),
        "captured_at_ms": captured_at_ms,
        "captured_at_us": captured_at_us,
        "stock_code": trace_symbol,
        "effective_venue": snapshot_venue,
        "session_bucket": snapshot_session,
    }, tuple(sorted(set(blockers)))


def _valid_market_row(row: Mapping[str, Any]) -> tuple[bool, str | None]:
    expected_contract = MARKET_CONTRACT_BY_SCHEMA.get(str(row.get("schema") or ""))
    if expected_contract is None or row.get("metric_contract_id") != expected_contract:
        return False, "market_schema_invalid"
    if (
        row.get("actual_order_submitted") is not False
        or row.get("broker_order_forbidden") is not True
        or row.get("trading_runtime_effect") is not False
    ):
        return False, "market_authority_invalid"
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
    if (
        int(row.get("sequence_epoch") or 0) <= 0
        or int(row.get("event_detected_at_ms") or 0) <= 0
        or not str(row.get("parent_wave_id") or "").strip()
    ):
        return False, "event_reference_identity_invalid"
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
        if receive_ms < previous_receive_ms:
            findings.append(f"{prefix}_local_receive_time_regressed")
        previous_sequence = sequence
        previous_receive_ms = receive_ms
    return tuple(sorted(set(findings)))


def _liquidity_projection(
    *,
    depth: Mapping[str, Any] | None,
    recent_rows: Sequence[Mapping[str, Any]],
    config: BridgeConfig,
    upstream_quantity: int | None,
) -> dict[str, Any]:
    if depth is None:
        return {
            "capacity_quality_status": "depth_unavailable_not_imputed",
            "counterfactual_liquidity_qty_grid": [],
            "counterfactual_liquidity_qty_ceiling": None,
            "existing_position_formula_candidate_qty": upstream_quantity,
            "existing_quantity_owner": "position_sizing_dynamic_formula",
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
        depth_capacity = (
            None
            if bid_capacity is None or ask_capacity is None
            else math.floor(min(bid_capacity, ask_capacity) * participation)
        )
        tape_capacity = (
            None
            if aggressive_buy_qty <= 0
            else math.floor(
                aggressive_buy_qty
                / config.tape_capacity_window_sec
                * config.target_liquidation_sec
                * participation
            )
        )
        full_capacity = (
            None
            if depth_capacity is None or tape_capacity is None
            else min(depth_capacity, tape_capacity)
        )
        bounded_capacity = full_capacity
        if bounded_capacity is not None and upstream_quantity is not None:
            bounded_capacity = min(bounded_capacity, upstream_quantity)
        entry_vwap = (
            None
            if bounded_capacity is None
            else _sweep_vwap(ask_levels, bounded_capacity)
        )
        exit_vwap = (
            None
            if bounded_capacity is None
            else _sweep_vwap(bid_levels, bounded_capacity)
        )
        grid.append(
            {
                "participation_rate": participation,
                "entry_ask_capacity_qty": ask_capacity,
                "depth_only_fast_exit_capacity_qty": bid_capacity,
                "tape_absorption_capacity_qty": tape_capacity,
                "full_fast_exit_capacity_qty": full_capacity,
                "counterfactual_liquidity_bounded_qty": bounded_capacity,
                "counterfactual_entry_sweep_vwap": entry_vwap,
                "counterfactual_exit_sweep_vwap": exit_vwap,
                "counterfactual_roundtrip_execution_bps": (
                    None
                    if entry_vwap is None or exit_vwap is None
                    else round((entry_vwap / exit_vwap - 1.0) * 10_000.0, 6)
                ),
            }
        )
    conservative_index = min(1, len(grid) - 1)
    ceiling = grid[conservative_index]["counterfactual_liquidity_bounded_qty"]
    return {
        "capacity_quality_status": (
            "full_depth_and_aggressive_buy_tape_capacity_observed"
            if aggressive_buy_qty > 0 and ceiling is not None
            else "depth_only_unconfirmed_turnover"
        ),
        "target_liquidation_sec": config.target_liquidation_sec,
        "recent_tape_window_sec": config.tape_capacity_window_sec,
        "recent_aggressive_buy_qty": (
            aggressive_buy_qty if aggressive_buy_qty > 0 else None
        ),
        "counterfactual_liquidity_qty_grid": grid,
        "counterfactual_liquidity_qty_ceiling": ceiling,
        "existing_position_formula_candidate_qty": upstream_quantity,
        "existing_quantity_owner": "position_sizing_dynamic_formula",
        "future_candidate_composition_rule": (
            "min(existing_position_formula_qty,verified_fast_exit_capacity)"
        ),
    }


def _economics(
    *, liquidity: Mapping[str, Any], config: BridgeConfig
) -> dict[str, Any]:
    grid = liquidity.get("counterfactual_liquidity_qty_grid")
    grid = grid if isinstance(grid, list) else []
    conservative = grid[min(1, len(grid) - 1)] if grid else {}
    execution_bps = _finite_float(
        conservative.get("counterfactual_roundtrip_execution_bps")
    )
    cost_ready = config.statutory_sell_tax_bps is not None
    fixed_cost = (
        None
        if not cost_ready
        else config.buy_fee_bps
        + config.sell_fee_bps
        + float(config.statutory_sell_tax_bps)
        + config.uncertainty_buffer_bps
    )
    all_in = (
        None
        if fixed_cost is None or execution_bps is None
        else fixed_cost + execution_bps
    )
    return {
        "cost_profile_source": config.cost_profile_source,
        "cost_profile_verified": config.cost_profile_verified,
        "buy_fee_bps": config.buy_fee_bps if cost_ready else None,
        "sell_fee_bps": config.sell_fee_bps if cost_ready else None,
        "statutory_sell_tax_bps": config.statutory_sell_tax_bps,
        "uncertainty_buffer_bps": (
            config.uncertainty_buffer_bps if cost_ready else None
        ),
        "counterfactual_roundtrip_execution_bps": execution_bps,
        "spread_double_counted": False,
        "all_in_cost_bps": None if all_in is None else round(all_in, 6),
        "minimum_net_profit_bps": config.minimum_net_profit_bps,
        "minimum_gross_target_bps": (
            None
            if all_in is None
            else round(all_in + config.minimum_net_profit_bps, 6)
        ),
        "economic_source_quality_status": (
            "verified_cost_profile"
            if cost_ready and config.cost_profile_verified
            else (
                "research_cost_assumption_not_promotion_grade"
                if cost_ready
                else "cost_profile_unavailable_no_net_target"
            )
        ),
    }


def _position_context(payload: Mapping[str, Any]) -> tuple[int | None, float | None]:
    source = payload.get("sanitized_replay_context")
    if source is None:
        source = payload.get("sanitized_user_input")
    candidates = []
    for row in _walk_objects(source):
        if "buy_qty" not in row and "position_qty" not in row:
            continue
        quantity = _nonnegative_int(row.get("buy_qty") or row.get("position_qty"))
        price = _positive_float(row.get("buy_price") or row.get("average_price"))
        if quantity is not None or price is not None:
            candidates.append((quantity, price))
    return candidates[0] if candidates else (None, None)


def _lifecycle_projection(
    *,
    trace: Mapping[str, Any],
    payload: Mapping[str, Any],
    latest_market: Mapping[str, Any],
    liquidity: Mapping[str, Any],
    economics: Mapping[str, Any],
) -> dict[str, Any]:
    position_qty, buy_price = _position_context(payload)
    fast_capacity = _nonnegative_int(
        liquidity.get("counterfactual_liquidity_qty_ceiling")
    )
    best_bid = _positive_float(latest_market.get("best_bid"))
    gross_exit_bps = (
        None
        if buy_price is None or best_bid is None
        else (best_bid / buy_price - 1.0) * 10_000.0
    )
    fixed_cost = None
    if economics.get("statutory_sell_tax_bps") is not None:
        fixed_cost = sum(
            float(economics.get(field) or 0.0)
            for field in (
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
            "minimum_gross_target_bps": economics.get(
                "minimum_gross_target_bps"
            ),
            "counterfactual_fast_exit_capacity_qty": fast_capacity,
            "live_price_or_order_effect": False,
        },
        "holding_projection": {
            "review_cadence": "each_new_0b_or_0d_state_change_not_synchronous_llm",
            "observed_position_qty": position_qty,
            "counterfactual_fast_exit_capacity_qty": fast_capacity,
            "counterfactual_capacity_coverage_ratio": (
                None
                if position_qty in (None, 0) or fast_capacity is None
                else fast_capacity / position_qty
            ),
            "counterfactual_capacity_excess_qty": (
                None
                if position_qty is None or fast_capacity is None
                else max(0, position_qty - fast_capacity)
            ),
            "counterfactual_net_executable_pnl_bps": (
                None if net_exit_bps is None else round(net_exit_bps, 6)
            ),
            "scale_in_requires_fresh_recovery_and_verified_exit_capacity": True,
            "hard_protect_emergency_exit_priority_unchanged": True,
        },
        "exit_projection": {
            "profit_basis": "net_executable_bid_after_tax_fee_and_slippage",
            "minimum_net_profit_bps": economics.get("minimum_net_profit_bps"),
            "counterfactual_net_target_reached": (
                None
                if net_exit_bps is None
                else net_exit_bps
                >= float(economics.get("minimum_net_profit_bps") or 0.0)
            ),
            "counterfactual_immediately_executable_qty": fast_capacity,
            "hard_protect_emergency_exit_priority_unchanged": True,
            "live_sell_or_cancel_effect": False,
        },
        **AUTHORITY_CONTRACT,
    }


def _upstream_quantity(payload: Mapping[str, Any]) -> int | None:
    source = payload.get("sanitized_replay_context")
    if source is None:
        source = payload.get("sanitized_user_input")
    for row in _walk_objects(source):
        for field in (
            "effective_qty",
            "planned_qty",
            "order_qty",
            "requested_qty",
            "buy_qty",
        ):
            quantity = _nonnegative_int(row.get(field))
            if quantity is not None and quantity > 0:
                return quantity
    return None


def build_tactical_evidence(
    *,
    trace: Mapping[str, Any],
    payload: Mapping[str, Any],
    market_rows: Iterable[Mapping[str, Any]],
    depth_rows: Iterable[Mapping[str, Any]],
    event_references: Iterable[Mapping[str, Any]],
    config: BridgeConfig | None = None,
    excluded_scopes: set[tuple[str, str, str, int]] | None = None,
) -> dict[str, Any]:
    """Build one nonfuture sidecar without changing the exact provider payload."""

    selected_config = config or BridgeConfig()
    watermark, blockers = exact_snapshot_watermark(trace, payload)
    blocker_list = list(blockers)
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

    accepted_market: list[Mapping[str, Any]] = []
    rejected_market = Counter()
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
        if received_us > watermark_us:
            continue
        valid, reason = _valid_market_row(row)
        if not valid:
            rejected_market[reason or "market_invalid"] += 1
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
        market_age_ms = (
            watermark_us - _timestamp_us(latest_market.get("local_receive_timestamp"))
        ) / 1_000.0
        if market_age_ms < 0:
            blocker_list.append("future_market_row_selected")
        elif market_age_ms > selected_config.max_market_age_ms:
            blocker_list.append("market_row_stale")
        accepted_market = [
            row
            for row in accepted_market
            if int(row.get("sequence_epoch") or 0) == selected_epoch
        ]
        blocker_list.extend(
            _series_sequence_findings(accepted_market, prefix="market")
        )
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
    for row in depth_rows:
        if _scope_key(row) != (symbol, scope.venue, scope.session_bucket, selected_epoch):
            continue
        try:
            received_us = _timestamp_us(row.get("local_receive_timestamp"))
        except (TypeError, ValueError):
            continue
        if received_us > watermark_us:
            continue
        valid, reason = _valid_depth_row(row)
        if not valid:
            rejected_depth[reason or "depth_invalid"] += 1
            continue
        accepted_depth.append(row)
    accepted_depth.sort(
        key=lambda row: (
            _timestamp_us(row.get("local_receive_timestamp")),
            int(row.get("source_sequence") or 0),
        )
    )
    latest_depth = accepted_depth[-1] if accepted_depth else None
    depth_age_ms = None
    if latest_depth is None:
        blocker_list.append("same_epoch_past_depth_missing")
    else:
        depth_age_ms = (
            watermark_us - _timestamp_us(latest_depth.get("local_receive_timestamp"))
        ) / 1_000.0
        if depth_age_ms < 0:
            blocker_list.append("future_depth_row_selected")
        elif depth_age_ms > selected_config.max_depth_age_ms:
            blocker_list.append("depth_row_stale")
        blocker_list.extend(_series_sequence_findings(accepted_depth, prefix="depth"))
        if latest_market is not None:
            market_bid = _positive_float(latest_market.get("best_bid"))
            market_ask = _positive_float(latest_market.get("best_ask"))
            depth_bid = _positive_float(latest_depth.get("best_bid"))
            depth_ask = _positive_float(latest_depth.get("best_ask"))
            if market_bid != depth_bid or market_ask != depth_ask:
                blocker_list.append("market_depth_bbo_conflict")

    references: list[Mapping[str, Any]] = []
    rejected_references = Counter()
    for row in event_references:
        if _scope_key(row) != (symbol, scope.venue, scope.session_bucket, selected_epoch):
            continue
        try:
            detected_ms = int(row.get("event_detected_at_ms"))
        except (TypeError, ValueError):
            continue
        if detected_ms * 1_000 > watermark_us:
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
        depth=latest_depth,
        recent_rows=(),
        config=selected_config,
        upstream_quantity=_upstream_quantity(payload),
    )
    economics = _economics(liquidity=liquidity, config=selected_config)
    if active_reference is not None and latest_market is not None:
        event_ms = int(active_reference.get("event_detected_at_ms") or 0)
        lookback_ms = selected_config.context_lookback_sec * 1_000
        context_rows = [
            row
            for row in accepted_market
            if event_ms - lookback_ms
            <= _timestamp_ms(row.get("local_receive_timestamp"))
            <= watermark_ms
        ]
        pre_rows = [
            row
            for row in context_rows
            if _timestamp_ms(row.get("local_receive_timestamp")) < event_ms
            and _positive_float(row.get("trade_price")) is not None
        ]
        post_rows = [
            row
            for row in context_rows
            if _timestamp_ms(row.get("local_receive_timestamp")) >= event_ms
            and _positive_float(row.get("trade_price")) is not None
        ]
        if not pre_rows or not post_rows:
            blocker_list.append("event_price_path_incomplete")
        else:
            horizon_ms = int(active_reference.get("shock_horizon_ms") or 0)
            target_reference_ms = event_ms - horizon_ms
            reference_candidates = [
                row
                for row in pre_rows
                if _timestamp_ms(row.get("local_receive_timestamp"))
                <= target_reference_ms
            ]
            reference_row = reference_candidates[-1] if reference_candidates else None
            shock_row = min(
                post_rows,
                key=lambda row: abs(
                    _timestamp_ms(row.get("local_receive_timestamp")) - event_ms
                ),
            )
            reference_price = (
                _positive_float(reference_row.get("trade_price"))
                if reference_row is not None
                else None
            )
            shock_price = _positive_float(shock_row.get("trade_price"))
            if reference_price is None or shock_price is None or (
                reference_price <= shock_price
            ):
                blocker_list.append("shock_reference_price_invalid")
            else:
                post_low_row = min(
                    post_rows,
                    key=lambda row: float(row.get("trade_price") or math.inf),
                )
                post_low = float(post_low_row["trade_price"])
                latest_price = _positive_float(latest_market.get("trade_price"))
                if latest_price is None:
                    blocker_list.append("asof_trade_price_missing")
                else:
                    shock_size = reference_price - post_low
                    reclaim_fraction = (
                        (latest_price - post_low) / shock_size if shock_size > 0 else 0.0
                    )
                    split = max(1, len(post_rows) // 2)
                    early_tape = _aggressor_quantities(post_rows[:split])
                    late_tape = _aggressor_quantities(post_rows[split:])
                    recent_start_ms = (
                        watermark_ms
                        - selected_config.tape_capacity_window_sec * 1_000
                    )
                    recent_rows = [
                        row
                        for row in accepted_market
                        if recent_start_ms
                        <= _timestamp_ms(row.get("local_receive_timestamp"))
                        <= watermark_ms
                    ]
                    tape = {
                        "early": early_tape,
                        "recent": late_tape,
                        "sell_pressure_deceleration": (
                            None
                            if early_tape["sell_ratio"] is None
                            or late_tape["sell_ratio"] is None
                            else round(
                                early_tape["sell_ratio"]
                                - late_tape["sell_ratio"],
                                6,
                            )
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
                        (latest_depth or {}).get("bid_depth")
                    )
                    first_bid_depth = _nonnegative_int(
                        (first_depth or {}).get("bid_depth")
                    )
                    same_price_depth = bool(
                        first_depth is not None
                        and latest_depth is not None
                        and _positive_float(first_depth.get("best_bid"))
                        == _positive_float(latest_depth.get("best_bid"))
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
                            (latest_depth or {}).get("best_bid_qty")
                        ),
                        "best_ask_qty": _nonnegative_int(
                            (latest_depth or {}).get("best_ask_qty")
                        ),
                        "bid_depth": latest_bid_depth,
                        "ask_depth": _nonnegative_int(
                            (latest_depth or {}).get("ask_depth")
                        ),
                        "spread_bps": (
                            None if spread_bps is None else round(spread_bps, 6)
                        ),
                        "same_epoch_bid_depth_change_qty": bid_replenishment,
                        "bid_replenishment_same_price_basis": same_price_depth,
                        "depth_age_ms": depth_age_ms,
                        "depth_join_status": (
                            "joined_fresh_past_same_epoch"
                            if latest_depth is not None
                            and depth_age_ms is not None
                            and depth_age_ms <= selected_config.max_depth_age_ms
                            else "depth_unavailable_or_stale"
                        ),
                    }
                    new_low_at_latest = latest_price <= post_low
                    late_buy_support = (late_tape.get("buy_ratio") or 0.0) >= 0.5
                    sell_decelerated = (tape["sell_pressure_deceleration"] or 0.0) > 0
                    bid_supported = bid_replenishment is not None and bid_replenishment > 0
                    if new_low_at_latest:
                        status = "continuation_blocked"
                    elif reclaim_fraction >= 0.5 and (
                        late_buy_support or sell_decelerated or bid_supported
                    ):
                        status = "reversion_confirmed"
                    elif reclaim_fraction > 0 or sell_decelerated:
                        status = "reversion_candidate"
                    else:
                        status = "shock_active"
                    event_metrics = {
                        "parent_wave_id": active_reference.get("parent_wave_id"),
                        "path_segment_id": active_reference.get("path_segment_id"),
                        "shock_event_id": active_reference.get("shock_event_id"),
                        "shock_horizon_ms": horizon_ms,
                        "event_sequence_in_wave": active_reference.get(
                            "event_sequence_in_wave"
                        ),
                        "event_detected_at_ms": event_ms,
                        "reference_price": reference_price,
                        "shock_price": shock_price,
                        "post_shock_low_price": post_low,
                        "asof_trade_price": latest_price,
                        "shock_bps": round(
                            (shock_price / reference_price - 1.0) * 10_000.0,
                            6,
                        ),
                        "reclaim_from_low_bps": round(
                            (latest_price / post_low - 1.0) * 10_000.0, 6
                        ),
                        "reclaim_fraction": round(reclaim_fraction, 6),
                        "remaining_to_reference_bps": round(
                            (reference_price / latest_price - 1.0) * 10_000.0,
                            6,
                        ),
                        "new_low_after_confirmation": new_low_at_latest,
                    }
                    liquidity = _liquidity_projection(
                        depth=latest_depth,
                        recent_rows=recent_rows,
                        config=selected_config,
                        upstream_quantity=_upstream_quantity(payload),
                    )
                    economics = _economics(
                        liquidity=liquidity, config=selected_config
                    )
    if blocker_list:
        status = "source_unavailable"
    latest_market_payload = latest_market or {}
    source_quality_status = "pass" if not blocker_list else "blocked"
    evidence_without_hash = {
        "schema": TACTICAL_EVIDENCE_SCHEMA,
        "evidence_version": 1,
        "decision_trace_id": trace.get("decision_trace_id"),
        "request_id": trace.get("request_id"),
        "source_provider_payload_sha256": trace.get("payload_sha256"),
        "source_exact_payload_sha256": source_exact_payload_sha256,
        "source_request_envelope_sha256": trace.get("request_envelope_sha256"),
        "snapshot_id": (watermark or {}).get("snapshot_id"),
        "stock_code": symbol,
        "trace_effective_venue": trace.get("effective_venue"),
        "trace_session_bucket": trace.get("session_bucket"),
        "micro_venue": scope.venue,
        "micro_session_bucket": scope.session_bucket,
        "sequence_epoch": selected_epoch or None,
        "snapshot_captured_at": (watermark or {}).get("captured_at"),
        "snapshot_captured_at_ms": watermark_ms or None,
        "decision_watermark": {
            "local_receive_timestamp": latest_market_payload.get(
                "local_receive_timestamp"
            ),
            "source_sequence": latest_market_payload.get("source_sequence"),
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
        latest_market=latest_market_payload,
        liquidity=liquidity,
        economics=economics,
    )
    context_without_hash = {
        **evidence_without_hash,
        LIFECYCLE_PROJECTION_SCHEMA: lifecycle,
    }
    return {**context_without_hash, "evidence_sha256": _sha256(context_without_hash)}


def build_future_outcome(
    *,
    evidence: Mapping[str, Any],
    market_rows: Iterable[Mapping[str, Any]],
    config: BridgeConfig | None = None,
) -> dict[str, Any]:
    """Label post-watermark executable paths; never include this in AI input."""

    selected_config = config or BridgeConfig()
    start_ms = int(evidence.get("snapshot_captured_at_ms") or 0)
    symbol = normalize_symbol(evidence.get("stock_code"))
    venue = normalize_venue(evidence.get("micro_venue"))
    session = _session(evidence.get("micro_session_bucket"))
    epoch = int(evidence.get("sequence_epoch") or 0)
    entry_ask = _positive_float((evidence.get("orderbook") or {}).get("best_ask"))
    rows = []
    for row in market_rows:
        valid, _ = _valid_market_row(row)
        if not valid or _scope_key(row) != (symbol, venue, session, epoch):
            continue
        received_ms = _timestamp_ms(row.get("local_receive_timestamp"))
        if start_ms < received_ms <= (
            start_ms + selected_config.outcome_horizons_sec[-1] * 1_000
        ):
            rows.append(row)
    rows.sort(key=lambda row: _timestamp_ms(row.get("local_receive_timestamp")))
    fixed_cost = (
        None
        if selected_config.statutory_sell_tax_bps is None
        else selected_config.buy_fee_bps
        + selected_config.sell_fee_bps
        + selected_config.statutory_sell_tax_bps
        + selected_config.uncertainty_buffer_bps
    )
    horizons = []
    target_first_ms = None
    adverse_first_ms = None
    for horizon in selected_config.outcome_horizons_sec:
        bounded = [
            row
            for row in rows
            if _timestamp_ms(row.get("local_receive_timestamp"))
            <= start_ms + horizon * 1_000
            and _positive_float(row.get("best_bid")) is not None
        ]
        net_returns = (
            []
            if entry_ask is None or fixed_cost is None
            else [
                (float(row["best_bid"]) / entry_ask - 1.0) * 10_000.0
                - fixed_cost
                for row in bounded
            ]
        )
        if net_returns:
            for row, net_return in zip(bounded, net_returns, strict=True):
                received_ms = _timestamp_ms(row.get("local_receive_timestamp"))
                if (
                    target_first_ms is None
                    and net_return >= selected_config.minimum_net_profit_bps
                ):
                    target_first_ms = received_ms
                if (
                    adverse_first_ms is None
                    and net_return <= selected_config.adverse_label_bps
                ):
                    adverse_first_ms = received_ms
        endpoint_target_ms = start_ms + horizon * 1_000
        endpoint_lag_ms = (
            None
            if not bounded
            else endpoint_target_ms
            - _timestamp_ms(bounded[-1].get("local_receive_timestamp"))
        )
        mature = bool(
            bounded
            and endpoint_lag_ms is not None
            and endpoint_lag_ms <= selected_config.max_outcome_endpoint_lag_ms
        )
        horizons.append(
            {
                "horizon_sec": horizon,
                "mature": mature,
                "endpoint_lag_ms": endpoint_lag_ms,
                "executable_bid_observation_count": len(bounded),
                "counterfactual_net_mfe_bps": (
                    None if not net_returns else round(max(net_returns), 6)
                ),
                "counterfactual_net_mae_bps": (
                    None if not net_returns else round(min(net_returns), 6)
                ),
            }
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
    return {
        "schema": OUTCOME_SCHEMA,
        "decision_trace_id": evidence.get("decision_trace_id"),
        "evidence_sha256": evidence.get("evidence_sha256"),
        "label_role": "counterfactual_outcome_only_never_prompt_input",
        "first_hit": first_hit,
        "target_first_delay_ms": (
            None if target_first_ms is None else target_first_ms - start_ms
        ),
        "adverse_first_delay_ms": (
            None if adverse_first_ms is None else adverse_first_ms - start_ms
        ),
        "horizons": horizons,
        **METRIC_CONTRACT,
        **AUTHORITY_CONTRACT,
    }


def build_three_arm_manifest(
    *, evidence: Mapping[str, Any], control_prompt_version: str
) -> dict[str, Any]:
    """Describe a fair input-vs-prompt comparison without calling a provider."""

    exact_hash = str(evidence.get("source_exact_payload_sha256") or "")
    evidence_hash = str(evidence.get("evidence_sha256") or "")
    enriched_identity = {
        "source_exact_payload_sha256": exact_hash,
        "tactical_micro_reversion_evidence_sha256": evidence_hash,
    }
    combined_hash = _sha256(enriched_identity)
    return {
        "schema": THREE_ARM_SCHEMA,
        "decision_trace_id": evidence.get("decision_trace_id"),
        "arms": [
            {
                "arm": "natural_control",
                "prompt_version": control_prompt_version,
                "source_exact_payload_sha256": exact_hash,
                "tactical_micro_reversion_evidence_sha256": None,
                "input_identity_sha256": exact_hash,
            },
            {
                "arm": "current_prompt_plus_micro",
                "prompt_version": control_prompt_version,
                **enriched_identity,
                "input_identity_sha256": combined_hash,
            },
            {
                "arm": "candidate_prompt_plus_micro",
                "prompt_version": None,
                "status": "candidate_prompt_selection_required",
                **enriched_identity,
                "input_identity_sha256": combined_hash,
            },
        ],
        "identical_exact_payload_across_arms": True,
        "identical_micro_context_between_enriched_arms": True,
        "provider_call_performed": False,
        "replay_context_eligible": bool(
            (evidence.get("source_quality") or {}).get("status") == "pass"
            and evidence.get("state")
            not in {"not_applicable", "source_unavailable"}
            and (evidence.get("economics") or {}).get("minimum_gross_target_bps")
            is not None
        ),
        **AUTHORITY_CONTRACT,
    }


def attach_micro_context_to_replay_request(
    request: Mapping[str, Any], evidence: Mapping[str, Any]
) -> dict[str, Any]:
    """Opt-in replay enrichment; default Exact V2 request remains unchanged."""

    expected_trace = str(request.get("decision_trace_id") or "")
    if expected_trace != str(evidence.get("decision_trace_id") or ""):
        raise ValueError("decision_trace_id_mismatch")
    exact_payload = request.get("exact_payload")
    if not isinstance(exact_payload, dict):
        raise ValueError("exact_payload_missing")
    if _sha256(exact_payload) != str(
        request.get("source_exact_payload_sha256")
        or evidence.get("source_exact_payload_sha256")
        or ""
    ):
        raise ValueError("exact_payload_sha256_mismatch")
    if (evidence.get("source_quality") or {}).get("status") != "pass":
        raise ValueError("micro_context_source_quality_not_pass")
    outcome_keys = {"horizons", "first_hit", "mfe", "mae", "future_outcome"}
    if any(
        key in row
        for row in _walk_objects(evidence)
        for key in outcome_keys
    ):
        raise ValueError("future_outcome_field_forbidden_in_context")
    candidate_input = request.get("candidate_input")
    candidate_input = dict(candidate_input) if isinstance(candidate_input, dict) else {
        "exact_payload": exact_payload
    }
    candidate_input[TACTICAL_EVIDENCE_SCHEMA] = dict(evidence)
    return {
        **request,
        "exact_payload": exact_payload,
        "candidate_input": candidate_input,
        "candidate_input_sha256": _sha256(candidate_input),
        "tactical_micro_reversion_evidence_sha256": evidence.get(
            "evidence_sha256"
        ),
        "micro_reversion_replay_opt_in": True,
        **AUTHORITY_CONTRACT,
    }


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
) -> dict[str, Any]:
    date_value = date.fromisoformat(target_date)
    if date_value < CLEAN_BASELINE_DATE:
        raise ValueError("target date is before clean tuning baseline")
    selected_config = config or BridgeConfig()
    trace_rows = [row for row in traces if isinstance(row, Mapping)]
    payload_rows = [row for row in payloads if isinstance(row, Mapping)]
    market = [row for row in market_rows if isinstance(row, Mapping)]
    depth = [row for row in depth_rows if isinstance(row, Mapping)]
    references = [row for row in event_references if isinstance(row, Mapping)]
    payload_groups: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for payload_row in payload_rows:
        if payload_row.get("request_id"):
            payload_groups[str(payload_row.get("request_id"))].append(payload_row)
    payload_by_request = {
        request_id: grouped[0]
        for request_id, grouped in payload_groups.items()
        if len(grouped) == 1
    }
    market_by_scope: dict[tuple[str, str, str], list[Mapping[str, Any]]] = (
        defaultdict(list)
    )
    for row in market:
        market_by_scope[
            (
                normalize_symbol(row.get("symbol")),
                normalize_venue(row.get("venue")),
                _session(row.get("session_bucket")),
            )
        ].append(row)
    depth_by_scope: dict[tuple[str, str, str], list[Mapping[str, Any]]] = (
        defaultdict(list)
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
    rows = []
    exclusions = Counter()
    primary_wave_seen: set[tuple[str, str, str, str, str]] = set()
    for trace in trace_rows:
        request_id = str(trace.get("request_id") or trace.get("decision_trace_id") or "")
        payload = payload_by_request.get(request_id)
        if payload is None:
            exclusions[
                "payload_request_join_ambiguous"
                if request_id in payload_groups
                else "payload_request_join_missing"
            ] += 1
            continue
        resolved_scope = resolve_micro_scope(trace)
        scope_key = (
            normalize_symbol(trace.get("stock_code")),
            resolved_scope.venue,
            resolved_scope.session_bucket,
        )
        evidence = build_tactical_evidence(
            trace=trace,
            payload=payload,
            market_rows=market_by_scope.get(scope_key, ()),
            depth_rows=depth_by_scope.get(scope_key, ()),
            event_references=references_by_scope.get(scope_key, ()),
            config=selected_config,
            excluded_scopes=excluded_scopes,
        )
        state = str(evidence.get("state") or "source_unavailable")
        wave_id = str((evidence.get("event") or {}).get("parent_wave_id") or "")
        wave_key = (
            normalize_symbol(evidence.get("stock_code")),
            str(evidence.get("micro_venue") or ""),
            str(evidence.get("micro_session_bucket") or ""),
            str(trace.get("decision_stage") or ""),
            wave_id,
        )
        primary_episode_row = bool(wave_id and wave_key not in primary_wave_seen)
        if primary_episode_row:
            primary_wave_seen.add(wave_key)
        outcome = build_future_outcome(
            evidence=evidence,
            market_rows=market,
            config=selected_config,
        )
        row = {
            "decision_trace_id": trace.get("decision_trace_id"),
            "decision_stage": trace.get("decision_stage"),
            "provider_actual": trace.get("provider_actual"),
            "prompt_version": trace.get("prompt_version"),
            "primary_parent_wave_stage_row": primary_episode_row,
            "same_parent_wave_repeat": bool(wave_id and not primary_episode_row),
            TACTICAL_EVIDENCE_SCHEMA: evidence,
            "future_outcome": outcome,
            "three_arm_manifest": build_three_arm_manifest(
                evidence=evidence,
                control_prompt_version=str(trace.get("prompt_version") or "unknown"),
            ),
        }
        rows.append(row)
        if state == "source_unavailable":
            for reason in (evidence.get("source_quality") or {}).get("blockers") or []:
                exclusions[str(reason)] += 1
    state_counts = Counter(
        str((row[TACTICAL_EVIDENCE_SCHEMA] or {}).get("state") or "unknown")
        for row in rows
    )
    stage_counts = Counter(str(row.get("decision_stage") or "unknown") for row in rows)
    context_eligible = sum(
        (row[TACTICAL_EVIDENCE_SCHEMA].get("source_quality") or {}).get("status")
        == "pass"
        and row[TACTICAL_EVIDENCE_SCHEMA].get("state")
        not in {"not_applicable", "source_unavailable"}
        and row.get("primary_parent_wave_stage_row") is True
        for row in rows
    )
    generated = generated_at or datetime.now().astimezone()
    return {
        "schema": REPORT_SCHEMA,
        "target_date": target_date,
        "generated_at": generated.isoformat(),
        "status": "pass" if rows else "warning",
        "decision": (
            "micro_three_arm_replay_context_ready"
            if context_eligible
            else "micro_context_keep_collecting_or_source_gap"
        ),
        "optimization_direction": {
            "objective": (
                "maximize_after_cost_net_profit_with_fast_frequent_bounded_exposure"
            ),
            "primary_metrics": [
                "source_quality_adjusted_net_ev_per_all_detected_signal",
                "notional_weighted_net_ev_pct",
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
            "micro_context_eligible_primary_episode_count": context_eligible,
            "same_parent_wave_repeat_count": sum(
                row.get("same_parent_wave_repeat") is True for row in rows
            ),
            "state_counts": dict(state_counts),
            "stage_counts": dict(stage_counts),
            "exclusion_counts": dict(exclusions),
        },
        "rows": rows,
        "source_exact_payload_mutated": False,
        "future_outcomes_separate_from_prompt_context": True,
        "default_exact_v2_cohort_unchanged": True,
        "provider_call_performed": False,
        **METRIC_CONTRACT,
        **AUTHORITY_CONTRACT,
    }


def _iter_jsonl(paths: Iterable[Path]) -> Iterable[dict[str, Any]]:
    for path in paths:
        opener = gzip.open if path.suffix == ".gz" else open
        with opener(path, "rt", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                payload = json.loads(line)
                if isinstance(payload, dict):
                    yield payload


def _partition_paths(root: Path, target_date: str, name: str) -> list[Path]:
    partition = root / f"trade_date={target_date}"
    selected: list[Path] = []
    for directory in sorted(partition.glob("venue=*/session=*")):
        plain = directory / f"{name}.jsonl"
        compressed = plain.with_suffix(f"{plain.suffix}.gz")
        if compressed.exists():
            selected.append(compressed)
        elif plain.exists():
            selected.append(plain)
    return selected


def _relevant_windows(
    traces: Sequence[Mapping[str, Any]],
    payloads: Sequence[Mapping[str, Any]],
    *,
    config: BridgeConfig,
) -> dict[tuple[str, str, str], tuple[int, int]]:
    payload_by_request = {
        str(row.get("request_id") or ""): row
        for row in payloads
        if row.get("request_id")
    }
    windows: dict[tuple[str, str, str], tuple[int, int]] = {}
    for trace in traces:
        request_id = str(trace.get("request_id") or trace.get("decision_trace_id") or "")
        payload = payload_by_request.get(request_id)
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
        start_ms = watermark_ms - (
            config.active_wave_max_age_sec + config.context_lookback_sec
        ) * 1_000
        end_ms = watermark_ms + config.outcome_horizons_sec[-1] * 1_000
        previous = windows.get(key)
        windows[key] = (
            start_ms if previous is None else min(start_ms, previous[0]),
            end_ms if previous is None else max(end_ms, previous[1]),
        )
    return windows


def _filter_relevant_rows(
    rows: Iterable[Mapping[str, Any]],
    windows: Mapping[tuple[str, str, str], tuple[int, int]],
    *,
    reference_rows: bool = False,
) -> list[Mapping[str, Any]]:
    selected = []
    for row in rows:
        key = (
            normalize_symbol(row.get("symbol")),
            normalize_venue(row.get("venue")),
            _session(row.get("session_bucket")),
        )
        window = windows.get(key)
        if window is None:
            continue
        try:
            timestamp_ms = (
                int(row.get("event_detected_at_ms") or 0)
                if reference_rows
                else _timestamp_ms(row.get("local_receive_timestamp"))
            )
        except (TypeError, ValueError):
            continue
        if window[0] <= timestamp_ms <= window[1]:
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
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


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
    parser.add_argument("--cost-profile-source", default="operator_supplied_research")
    parser.add_argument("--cost-profile-verified", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    target = date.fromisoformat(args.date)
    if target < CLEAN_BASELINE_DATE:
        parser.error("date is before clean tuning baseline")
    trace_path = DATA_DIR / "ai_decision_trace" / f"ai_decision_trace_{args.date}.jsonl"
    payload_path = (
        DATA_DIR / "ai_decision_payloads" / f"ai_decision_payloads_{args.date}.jsonl"
    )
    if not trace_path.exists() or not payload_path.exists():
        parser.error("exact trace or payload artifact is missing")
    exclusion_payload = load_source_exclusion_manifest(args.source_exclusion_manifest)
    config = BridgeConfig(
        statutory_sell_tax_bps=args.statutory_sell_tax_bps,
        buy_fee_bps=args.buy_fee_bps,
        sell_fee_bps=args.sell_fee_bps,
        uncertainty_buffer_bps=args.uncertainty_buffer_bps,
        cost_profile_source=args.cost_profile_source,
        cost_profile_verified=args.cost_profile_verified,
    )
    traces = list(_iter_jsonl((trace_path,)))
    payloads = list(_iter_jsonl((payload_path,)))
    windows = _relevant_windows(traces, payloads, config=config)
    market_paths = _partition_paths(
        args.observation_root, args.date, "market_stream"
    )
    depth_paths = _partition_paths(
        args.observation_root, args.date, "market_depth_stream"
    )
    reference_paths = _partition_paths(
        args.observation_root, args.date, "market_stream_event_references"
    )
    market_rows = _filter_relevant_rows(_iter_jsonl(market_paths), windows)
    depth_rows = _filter_relevant_rows(_iter_jsonl(depth_paths), windows)
    reference_rows = _filter_relevant_rows(
        _iter_jsonl(reference_paths), windows, reference_rows=True
    )
    report = build_bridge_report(
        target_date=args.date,
        traces=traces,
        payloads=payloads,
        market_rows=market_rows,
        depth_rows=depth_rows,
        event_references=reference_rows,
        config=config,
        excluded_scopes=_excluded_scopes(exclusion_payload),
    )
    output = (
        DATA_DIR
        / "report"
        / "micro_reversion_ai_quality_bridge"
        / f"micro_reversion_ai_quality_bridge_{args.date}.json"
    )
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
