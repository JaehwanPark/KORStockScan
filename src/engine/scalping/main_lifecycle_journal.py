"""Compact, source-only lifecycle telemetry for the main scalping bot.

The live path mints exact identity fields for the existing pipeline stream and
does not create a second synchronous file write.  Canonical transition builders
and optional append APIs remain available for audit/tests.  Telemetry failure is
fail-open and never changes an order, provider, threshold, quantity, or bot
state.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import math
import os
import re
import threading
from datetime import date, datetime
from pathlib import Path
from typing import Any, Mapping
from zoneinfo import ZoneInfo

from src.utils.constants import DATA_DIR
from src.utils.logger import log_error

JOURNAL_SCHEMA = "main_scalping_lifecycle_transition_v1"
JOURNAL_DIR = DATA_DIR / "main_lifecycle_journal"
MAIN_LIFECYCLE_ID_PREFIX = "mlc-"
MAIN_LIFECYCLE_ID_RE = re.compile(r"^mlc-[0-9a-f]{32}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
KST = ZoneInfo("Asia/Seoul")
MAX_TRANSITION_BYTES = 16 * 1024
MAX_DATA_STRING_LENGTH = 2_048
PIPELINE_IDENTITY_SCHEMA = "main_scalping_lifecycle_pipeline_identity_v1"
BROKER_EXECUTION_PROVENANCE_SCHEMA = "kiwoom_ws_order_execution_provenance_v2"
BROKER_EXECUTION_PROVENANCE_LEGACY_SCHEMA = "kiwoom_ws_order_execution_provenance_v1"
BROKER_EXECUTION_RAW_ENVELOPE_SCHEMA = "kiwoom_websocket_order_execution_00_values_v1"
BROKER_EXECUTION_TIMING_SCHEMA = "kiwoom_ws_order_execution_timing_v2"
KIWOOM_OFFICIAL_REFERENCE_SHA = "69642586f7d84ba9fd8a6faf1f1537c7fda6568b"
BROKER_EXECUTION_SOURCE_TYPE = "00"
BROKER_EXECUTION_ORDERING_TIME_SOURCE = "broker_execution_received_at"
BROKER_EXECUTION_OCCURRENCE_TIME_SOURCE = "official_fid_908"
BROKER_EXECUTION_RECEIVE_TIME_SOURCE = "websocket_packet_ingress"
CARRY_IN_CUSTODY_SCHEMA = "main_lifecycle_carry_in_custody_v1"
CARRY_IN_CUSTODY_REQUIRED_DATE = "2026-08-27"
BROKER_EXECUTION_MAX_RECEIVE_LAG_SEC = 60.0
BROKER_EXECUTION_MAX_NEGATIVE_LAG_SEC = 2.0
_BROKER_EXECUTION_V2_ONLY_FIELDS = frozenset(
    {
        "broker_execution_reported_venue_scope",
        "broker_execution_actual_venue",
        "broker_execution_venue_resolution_state",
        "broker_execution_identity_complete",
        "broker_execution_actual_venue_complete",
    }
)

# Official WebSocket type ``00`` is the reviewed per-event order/execution
# source.  Promotion proof requires the explicit raw-envelope marker and the
# exact native FIDs below; lifecycle-derived or generic aliases are never
# allowed to manufacture native broker provenance.  ``ka10075`` remains an
# unfilled-order reconciliation source only: its ``tm`` is order time and an
# order disappears after full fill, so it cannot independently prove this
# terminal execution ledger.
BROKER_EXECUTION_NATIVE_FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "raw_envelope_schema": (
        "main_lifecycle_broker_raw_envelope_schema",
        "broker_raw_envelope_schema",
    ),
    "source_type": (
        "main_lifecycle_broker_raw_source_type",
        "broker_raw_source_type",
    ),
    "order_no": ("9203",),
    "stock_code": ("9001",),
    "order_status": ("913",),
    "order_qty": ("900",),
    "remaining_qty": ("902",),
    "cumulative_fill_amount_krw": ("903",),
    "order_side_text": ("905",),
    "order_side_code": ("907",),
    "execution_time": ("908",),
    "execution_no": ("909",),
    "execution_price": ("910",),
    "cumulative_fill_qty": ("911",),
    "unit_execution_price": ("914",),
    "unit_fill_qty": ("915",),
    "execution_venue_code": ("2134",),
    "execution_venue_text": ("2135",),
    "sor_yn": ("2136",),
}

# Only these existing live pipeline stages may become lifecycle transitions.
# The map is intentionally exact: the postclose producer must never infer a
# stage from a nearby timestamp, symbol, similarly named event, or free-form
# reason text.
PIPELINE_STAGE_MAP: dict[tuple[str, str], str] = {
    ("ENTRY_PIPELINE", "scalping_scanner_fast_precheck"): "scanner",
    ("ENTRY_PIPELINE", "scanner_async_result_commit"): "scanner",
    ("ENTRY_PIPELINE", "ai_confirmed"): "entry_decision",
    ("ENTRY_PIPELINE", "order_leg_sent"): "submit",
    ("ENTRY_PIPELINE", "order_bundle_submitted"): "submit",
    ("HOLDING_PIPELINE", "entry_execution_receipt_submission_custody"): "submit",
    ("HOLDING_PIPELINE", "position_rebased_after_fill"): "fill",
    ("HOLDING_PIPELINE", "holding_started"): "holding",
    ("HOLDING_PIPELINE", "ai_holding_review"): "holding",
    ("HOLDING_PIPELINE", "stat_action_decision_snapshot"): "scale_in",
    ("HOLDING_PIPELINE", "scale_in_order_leg_submitted"): "scale_in",
    ("HOLDING_PIPELINE", "scale_in_execution_receipt_submission_custody"): ("scale_in"),
    ("HOLDING_PIPELINE", "scale_in_order_submitted"): "scale_in",
    ("HOLDING_PIPELINE", "scale_in_executed"): "scale_in",
    ("HOLDING_PIPELINE", "exit_signal"): "exit",
    ("HOLDING_PIPELINE", "exit_execution_receipt_submission_custody"): "exit",
    ("HOLDING_PIPELINE", "sell_order_sent"): "exit",
    ("HOLDING_PIPELINE", "sell_partial_fill_progress"): "exit",
    ("HOLDING_PIPELINE", "nxt_rising_missed_tp1_partial_fill_progress"): "exit",
    ("HOLDING_PIPELINE", "nxt_rising_missed_tp1_partial_sell_completed"): "exit",
    ("HOLDING_PIPELINE", "sell_completed"): "exit",
}

VALID_STAGES = frozenset(
    {
        "scanner",
        "entry_decision",
        "submit",
        "fill",
        "holding",
        "scale_in",
        "exit",
    }
)
VALID_FILL_STATES = frozenset({"partial", "full"})
VALID_SCALE_IN_DECISIONS = frozenset({"ADD", "NO_ADD", "NOT_APPLICABLE"})
NO_FILL_TERMINAL_STAGES = frozenset({"scanner", "entry_decision", "submit", "exit"})

AUTHORITY_CONTRACT: dict[str, Any] = {
    "metric_role": "main_scalping_lifecycle_source_quality",
    "decision_authority": "source_only_lifecycle_observation",
    "window_policy": "exact_scanner_attempt_through_terminal_or_right_censor",
    "sample_floor": "one_explicit_scanner_attempt_starts_observation",
    "primary_decision_metric": "complete_reconciled_lifecycle_coverage",
    "source_quality_gate": (
        "exact_main_lifecycle_id_record_stock_attempt_and_aware_timestamp"
    ),
    "runtime_effect": False,
    "allowed_runtime_apply": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
    "forbidden_uses": [
        "runtime_decision_or_prompt_selection",
        "broker_order_submission_or_cancellation",
        "provider_model_or_bot_change",
        "threshold_price_quantity_or_cap_change",
        "hard_safety_or_broker_guard_bypass",
        "cross_attempt_symbol_or_timestamp_inference",
    ],
}

_ALLOWED_DATA_FIELDS = frozenset(
    {
        "action",
        "reason",
        "decision_trace_id",
        "source_population_scope",
        "payload_sha256",
        "paired_replay_parent_id",
        "paired_replay_arm",
        "actual_broker_order_submitted",
        "broker_order_no",
        "broker_order_no_list",
        "broker_order_qty_list",
        "submission_leg_contract",
        "submission_leg_self_summarizing",
        "submission_contract_legacy_unattested",
        "submission_summary_only",
        "submission_summary_expected_leg_count",
        "submission_time_source",
        "submission_ordering_clock",
        "submission_causal_upper_bound_at",
        "submission_causal_upper_bound_source",
        "submission_custody_binding_schema",
        "submission_custody_broker_order_no",
        "submission_custody_broker_execution_no",
        "submission_custody_broker_order_qty",
        "submission_custody_broker_cumulative_qty",
        "submission_custody_broker_remaining_qty",
        "submission_custody_broker_unit_qty",
        "broker_reconciled",
        "broker_execution_provenance_schema",
        "broker_execution_official_reference_sha",
        "broker_execution_provenance_state",
        "broker_execution_provenance_error",
        "broker_execution_raw_envelope_schema",
        "broker_execution_source_type",
        "broker_execution_order_no",
        "broker_execution_no",
        "broker_execution_stock_code",
        "broker_execution_order_status",
        "broker_execution_side",
        "broker_execution_order_qty",
        "broker_execution_cumulative_fill_qty",
        "broker_execution_cumulative_fill_amount_krw",
        "broker_execution_remaining_qty",
        "broker_execution_price",
        "broker_execution_reported_price",
        "broker_execution_unit_fill_qty",
        "broker_execution_time_hhmmss",
        "broker_execution_timing_schema",
        "broker_execution_received_at",
        "broker_execution_occurred_at",
        "broker_execution_receive_time_source",
        "broker_execution_ordering_time_source",
        "broker_execution_occurrence_time_source",
        "broker_execution_receive_lag_ms",
        "broker_execution_lifecycle_observed_at_rebound",
        "legacy_unattested_receive_clock_recovered",
        "broker_execution_receipt_companion",
        "broker_execution_receipt_companion_of_identity",
        "broker_execution_venue",
        "broker_execution_reported_venue_scope",
        "broker_execution_actual_venue",
        "broker_execution_venue_resolution_state",
        "broker_execution_identity_complete",
        "broker_execution_actual_venue_complete",
        "broker_execution_sor_yn",
        "broker_execution_fill_state",
        "broker_execution_identity",
        "broker_execution_content_sha256",
        "fill_state",
        "fill_qty",
        "fill_price",
        "requested_qty",
        "scale_in_decision",
        "exit_qty",
        "exit_price",
        "reconciled_final_exit",
        "terminal_no_fill",
        "terminal_reason",
        "market_observation_expected",
        "bbo_observed",
        "depth_observed",
        "depth_capacity_qty_5pct",
        "fees_taxes_krw",
        "slippage_krw",
        "slippage_basis_price",
        "slippage_basis_source",
        "realized_net_pnl_krw",
        "cost_artifact_sha256",
        "cost_artifact_verified",
        "symbol_master_sha256",
        "symbol_master_verified",
        "venue_source",
        "venue_provenance_status",
        "session_bucket_source",
        "session_provenance_status",
        "session_exposure_start_at",
        "session_exposure_end_at",
        "heartbeat",
        "carry_in_custody_schema",
        "lifecycle_origin",
        "carry_in_entry_observed_at",
        "carry_in_entry_source",
    }
)
_SENSITIVE_KEY_PARTS = (
    "token",
    "secret",
    "password",
    "authorization",
    "account_no",
    "account_number",
    "app_key",
    "appkey",
)
_WRITE_LOCK = threading.RLock()


def journal_path(target_date: str | date) -> Path:
    """Return the logical, uncompressed transition path for a trade date."""

    value = (
        target_date.isoformat() if isinstance(target_date, date) else str(target_date)
    )
    value = date.fromisoformat(value).isoformat()
    return JOURNAL_DIR / f"main_lifecycle_journal_{value}.jsonl"


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
        allow_nan=False,
    ).encode("utf-8")


def _canonical_sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _raw_text(value: Any) -> str | None:
    if value is None or isinstance(value, bool):
        return None
    text = str(value).strip()
    if text.lower() in {"", "-", "none", "null", "not_available"}:
        return None
    if len(text) > 128 or any(char in text for char in "\r\n\x00"):
        raise ValueError("broker_execution_raw_text_invalid")
    return text


def _raw_wire_text(value: Any) -> str:
    """Return one exact Kiwoom wire token without lossy normalization."""

    if not isinstance(value, str) or value != value.strip():
        raise ValueError("broker_execution_raw_wire_text_invalid")
    text = _raw_text(value)
    if text is None:
        raise ValueError("broker_execution_raw_wire_text_missing")
    return text


def _required_raw_text(value: Any) -> str:
    return _raw_wire_text(value)


def _raw_value_supplied(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return True
    text = str(value).strip()
    return text.lower() not in {"", "-", "none", "null", "not_available"}


def _raw_integer(value: Any, *, positive: bool) -> int:
    if not isinstance(value, str) or value != value.strip():
        raise ValueError("broker_execution_integer_invalid")
    if not re.fullmatch(r"[0-9]+", value):
        raise ValueError("broker_execution_integer_invalid")
    number = int(value)
    if number < 0 or (positive and number == 0) or number > 10**15:
        raise ValueError("broker_execution_integer_out_of_range")
    return number


def _expected_integer(value: Any, *, positive: bool) -> int:
    if isinstance(value, bool):
        raise ValueError("broker_execution_expected_integer_invalid")
    if isinstance(value, float):
        if not math.isfinite(value) or not value.is_integer():
            raise ValueError("broker_execution_expected_integer_invalid")
        value = int(value)
    if isinstance(value, int):
        number = value
    elif isinstance(value, str) and re.fullmatch(r"[0-9]+", value):
        number = int(value)
    else:
        raise ValueError("broker_execution_expected_integer_invalid")
    if number < 0 or (positive and number == 0) or number > 10**15:
        raise ValueError("broker_execution_expected_integer_out_of_range")
    return number


def _raw_order_no(value: Any) -> str:
    try:
        text = _raw_wire_text(value)
    except ValueError as exc:
        raise ValueError("broker_execution_order_no_invalid") from exc
    if not re.fullmatch(r"[0-9]{7}", text) or int(text) == 0:
        raise ValueError("broker_execution_order_no_invalid")
    return text


def _raw_execution_no(value: Any) -> str:
    try:
        text = _raw_wire_text(value)
    except ValueError as exc:
        raise ValueError("broker_execution_execution_no_invalid") from exc
    # FID 909 is documented as an opaque String without a fixed length.  Live
    # receipts include shorter positive decimal identifiers (for example
    # ``7207`` and ``53289``), so preserve the exact wire text instead of
    # manufacturing a seven-digit value.  The bounded decimal contract keeps
    # empty, zero, signed, coerced, and unreasonably large values fail-closed.
    if not re.fullmatch(r"[0-9]{1,20}", text) or int(text) == 0:
        raise ValueError("broker_execution_execution_no_invalid")
    return text


def _raw_stock_code(value: Any) -> str:
    try:
        text = _raw_wire_text(value)
    except ValueError as exc:
        raise ValueError("broker_execution_stock_code_invalid") from exc
    if not re.fullmatch(r"[0-9]{6}", text):
        raise ValueError("broker_execution_stock_code_invalid")
    return text


def _raw_order_status(value: Any) -> str:
    text = _raw_wire_text(value)
    if text != "체결":
        raise ValueError("broker_execution_order_status_not_execution")
    return text


def _raw_side_text(value: Any) -> str:
    text = _raw_wire_text(value)
    side = {"+매수": "BUY", "-매도": "SELL"}.get(text)
    if side is None:
        raise ValueError("broker_execution_side_text_invalid")
    return side


def _raw_side_code(value: Any) -> str:
    text = _raw_wire_text(value)
    side = {"1": "SELL", "2": "BUY"}.get(text)
    if side is None:
        raise ValueError("broker_execution_side_code_invalid")
    return side


def _raw_execution_time(value: Any) -> str:
    text = _raw_wire_text(value)
    if not re.fullmatch(r"[0-9]{6}", text):
        raise ValueError("broker_execution_time_invalid")
    hours, minutes, seconds = (
        int(text[:2]),
        int(text[2:4]),
        int(text[4:]),
    )
    if hours > 23 or minutes > 59 or seconds > 59:
        raise ValueError("broker_execution_time_invalid")
    return text


def _raw_venue_code(value: Any) -> str:
    text = _raw_wire_text(value)
    venue = {
        "1": "KRX",
        "2": "NXT",
        "0": "SOR",
    }.get(text)
    if venue is None:
        raise ValueError("broker_execution_venue_code_invalid")
    return venue


def _raw_venue_text(value: Any) -> str:
    text = _raw_wire_text(value)
    # The official type-00 contract documents the integrated value as
    # ``통합``.  Production receipts have also emitted the route token
    # ``SOR`` for the same field.  Accept that observed wire alias only as an
    # integrated-route identity; it must never be promoted to an inferred KRX
    # or NXT execution venue.
    venue = {"KRX": "KRX", "NXT": "NXT", "통합": "SOR", "SOR": "SOR"}.get(text)
    if venue is None:
        raise ValueError("broker_execution_venue_text_invalid")
    return venue


def _raw_sor_yn(value: Any) -> str:
    text = _raw_wire_text(value)
    if text not in {"Y", "N"}:
        raise ValueError("broker_execution_sor_yn_invalid")
    return text


def _resolve_raw_alias(
    source_fields: Mapping[str, Any],
    canonical_name: str,
    normalizer: Any,
) -> tuple[Any | None, bool]:
    values: list[Any] = []
    present = False
    for key in BROKER_EXECUTION_NATIVE_FIELD_ALIASES[canonical_name]:
        if key not in source_fields:
            continue
        raw_value = source_fields.get(key)
        if not _raw_value_supplied(raw_value):
            continue
        present = True
        values.append(normalizer(raw_value))
    if not values:
        return None, present
    first = values[0]
    if any(value != first for value in values[1:]):
        raise ValueError(f"broker_execution_native_alias_conflict:{canonical_name}")
    return first, True


def _execution_venue_matches(*, lifecycle_venue: Any, raw_venue: str) -> bool:
    lifecycle = str(lifecycle_venue or "").strip().upper()
    if raw_venue == "SOR":
        # Official SOR/integrated responses do not identify the underlying
        # execution exchange, so they are evidence but not promotion proof.
        return False
    if lifecycle == "PREMARKET_KRX_LIKE":
        return raw_venue == "KRX"
    return lifecycle == raw_venue


def _execution_venue_resolution_state(*, lifecycle_venue: Any, raw_venue: str) -> str:
    if raw_venue == "SOR":
        # Official FIDs 2134/2135 define this as the integrated execution
        # scope.  They do not identify which underlying KRX/NXT venue filled
        # the order, so retain the route-scoped receipt identity while keeping
        # venue-specific evidence fail-closed.
        return "integrated_sor_underlying_venue_unresolved"
    if _execution_venue_matches(
        lifecycle_venue=lifecycle_venue,
        raw_venue=raw_venue,
    ):
        return "exact_underlying_venue"
    raise ValueError("broker_execution_venue_mismatch")


def build_broker_execution_provenance(
    source_fields: Mapping[str, Any] | None,
    *,
    expected_qty: Any,
    expected_price: Any,
    expected_stock_code: Any,
    expected_side: Any,
    lifecycle_venue: Any,
    expected_fill_state: Any | None = None,
) -> dict[str, Any]:
    """Canonicalize one complete official Kiwoom WebSocket execution proof.

    Missing or malformed raw fields are preserved as a bounded source-quality
    state.  They never fall back to lifecycle-derived quantities and never
    grant R2/R3 evidence.
    """

    fields = source_fields if isinstance(source_fields, Mapping) else {}
    result: dict[str, Any] = {
        "broker_execution_provenance_schema": (BROKER_EXECUTION_PROVENANCE_SCHEMA),
        "broker_execution_official_reference_sha": (KIWOOM_OFFICIAL_REFERENCE_SHA),
    }
    raw_key_present = any(
        key in fields and _raw_value_supplied(fields.get(key))
        for aliases in BROKER_EXECUTION_NATIVE_FIELD_ALIASES.values()
        for key in aliases
    )
    if not raw_key_present:
        result.update(
            {
                "broker_execution_provenance_state": "missing",
                "broker_execution_provenance_error": (
                    "official_broker_execution_raw_fields_missing"
                ),
            }
        )
        return result

    try:
        raw_envelope_schema, _ = _resolve_raw_alias(
            fields,
            "raw_envelope_schema",
            _required_raw_text,
        )
        source_type, _ = _resolve_raw_alias(
            fields,
            "source_type",
            _required_raw_text,
        )
        order_no, _ = _resolve_raw_alias(fields, "order_no", _raw_order_no)
        stock_code, _ = _resolve_raw_alias(fields, "stock_code", _raw_stock_code)
        order_status, _ = _resolve_raw_alias(fields, "order_status", _raw_order_status)
        side_text, _ = _resolve_raw_alias(fields, "order_side_text", _raw_side_text)
        side_code, _ = _resolve_raw_alias(fields, "order_side_code", _raw_side_code)
        execution_no, _ = _resolve_raw_alias(fields, "execution_no", _raw_execution_no)
        order_qty, _ = _resolve_raw_alias(
            fields,
            "order_qty",
            lambda value: _raw_integer(value, positive=True),
        )
        cumulative_fill_qty, _ = _resolve_raw_alias(
            fields,
            "cumulative_fill_qty",
            lambda value: _raw_integer(value, positive=True),
        )
        cumulative_fill_amount, _ = _resolve_raw_alias(
            fields,
            "cumulative_fill_amount_krw",
            lambda value: _raw_integer(value, positive=True),
        )
        remaining_qty, _ = _resolve_raw_alias(
            fields,
            "remaining_qty",
            lambda value: _raw_integer(value, positive=False),
        )
        execution_price, _ = _resolve_raw_alias(
            fields,
            "execution_price",
            lambda value: _raw_integer(value, positive=True),
        )
        unit_execution_price, _ = _resolve_raw_alias(
            fields,
            "unit_execution_price",
            lambda value: _raw_integer(value, positive=True),
        )
        unit_fill_qty, _ = _resolve_raw_alias(
            fields,
            "unit_fill_qty",
            lambda value: _raw_integer(value, positive=True),
        )
        execution_time, _ = _resolve_raw_alias(
            fields, "execution_time", _raw_execution_time
        )
        execution_venue_code, _ = _resolve_raw_alias(
            fields, "execution_venue_code", _raw_venue_code
        )
        execution_venue_text, _ = _resolve_raw_alias(
            fields, "execution_venue_text", _raw_venue_text
        )
        sor_yn, _ = _resolve_raw_alias(fields, "sor_yn", _raw_sor_yn)
    except (TypeError, ValueError) as exc:
        result.update(
            {
                "broker_execution_provenance_state": "invalid",
                "broker_execution_provenance_error": str(exc)[:256],
            }
        )
        return result

    required = {
        "raw_envelope_schema": raw_envelope_schema,
        "source_type": source_type,
        "order_no": order_no,
        "execution_no": execution_no,
        "stock_code": stock_code,
        "order_status": order_status,
        "order_side_text": side_text,
        "order_side_code": side_code,
        "order_qty": order_qty,
        "cumulative_fill_qty": cumulative_fill_qty,
        "cumulative_fill_amount_krw": cumulative_fill_amount,
        "remaining_qty": remaining_qty,
        "execution_price": execution_price,
        "unit_execution_price": unit_execution_price,
        "unit_fill_qty": unit_fill_qty,
        "execution_time": execution_time,
        "execution_venue_code": execution_venue_code,
        "execution_venue_text": execution_venue_text,
        "sor_yn": sor_yn,
    }
    missing = sorted(key for key, value in required.items() if value is None)
    if missing:
        result.update(
            {
                "broker_execution_provenance_state": "incomplete",
                "broker_execution_provenance_error": (
                    "official_broker_execution_fields_incomplete:" + ",".join(missing)
                )[:256],
            }
        )
        return result

    assert isinstance(raw_envelope_schema, str)
    assert isinstance(source_type, str)
    assert isinstance(order_no, str)
    assert isinstance(execution_no, str)
    assert isinstance(stock_code, str)
    assert isinstance(order_status, str)
    assert isinstance(side_text, str)
    assert isinstance(side_code, str)
    assert isinstance(order_qty, int)
    assert isinstance(cumulative_fill_qty, int)
    assert isinstance(cumulative_fill_amount, int)
    assert isinstance(remaining_qty, int)
    assert isinstance(execution_price, int)
    assert isinstance(unit_execution_price, int)
    assert isinstance(unit_fill_qty, int)
    assert isinstance(execution_time, str)
    assert isinstance(execution_venue_code, str)
    assert isinstance(execution_venue_text, str)
    assert isinstance(sor_yn, str)

    try:
        expected_quantity = _expected_integer(expected_qty, positive=True)
        expected_execution_price = _expected_integer(expected_price, positive=True)
        normalized_stock_code = _raw_stock_code(expected_stock_code)
        normalized_side = str(expected_side or "").strip().upper()
        if raw_envelope_schema != BROKER_EXECUTION_RAW_ENVELOPE_SCHEMA:
            raise ValueError("broker_execution_raw_envelope_schema_invalid")
        if source_type != BROKER_EXECUTION_SOURCE_TYPE:
            raise ValueError("broker_execution_source_type_not_full_proof")
        if normalized_side not in {"BUY", "SELL"}:
            raise ValueError("broker_execution_expected_side_invalid")
        if stock_code != normalized_stock_code:
            raise ValueError("broker_execution_stock_code_mismatch")
        if side_text != side_code or side_code != normalized_side:
            raise ValueError("broker_execution_side_mismatch")
        if execution_venue_code != execution_venue_text:
            raise ValueError("broker_execution_venue_native_fields_conflict")
        if cumulative_fill_qty + remaining_qty != order_qty:
            raise ValueError("broker_execution_quantity_reconciliation_failed")
        if unit_fill_qty > cumulative_fill_qty:
            raise ValueError("broker_execution_unit_qty_exceeds_cumulative")
        if execution_price != unit_execution_price:
            raise ValueError("broker_execution_native_price_fields_conflict")
        if cumulative_fill_amount < unit_fill_qty * unit_execution_price:
            raise ValueError("broker_execution_cumulative_amount_too_small")
        if expected_quantity != unit_fill_qty:
            raise ValueError("broker_execution_unit_qty_mismatch")
        if expected_execution_price != unit_execution_price:
            raise ValueError("broker_execution_price_mismatch")
        venue_resolution_state = _execution_venue_resolution_state(
            lifecycle_venue=lifecycle_venue,
            raw_venue=execution_venue_code,
        )
        derived_fill_state = "full" if remaining_qty == 0 else "partial"
        normalized_expected_state = str(expected_fill_state or "").strip().lower()
        if normalized_expected_state and normalized_expected_state not in {
            "partial",
            "full",
        }:
            raise ValueError("broker_execution_expected_fill_state_invalid")
        if (
            normalized_expected_state
            and normalized_expected_state != derived_fill_state
        ):
            raise ValueError("broker_execution_fill_state_mismatch")
    except (TypeError, ValueError) as exc:
        result.update(
            {
                "broker_execution_provenance_state": "invalid",
                "broker_execution_provenance_error": str(exc)[:256],
            }
        )
        return result

    canonical_raw = {
        "raw_envelope_schema": raw_envelope_schema,
        "source_type": source_type,
        "order_no": order_no,
        "execution_no": execution_no,
        "stock_code": stock_code,
        "order_status": order_status,
        "side": side_code,
        "order_qty": order_qty,
        "cumulative_fill_qty": cumulative_fill_qty,
        "cumulative_fill_amount_krw": cumulative_fill_amount,
        "remaining_qty": remaining_qty,
        "reported_execution_price": execution_price,
        "unit_execution_price": unit_execution_price,
        "unit_fill_qty": unit_fill_qty,
        "execution_time_hhmmss": execution_time,
        "execution_venue": execution_venue_code,
        "sor_yn": sor_yn,
        "fill_state": derived_fill_state,
    }
    identity_payload = {
        "source_type": source_type,
        "order_no": order_no,
        "execution_no": execution_no,
    }
    venue_resolved = venue_resolution_state == "exact_underlying_venue"
    provenance_state = (
        "complete" if venue_resolved else "identity_complete_venue_unresolved"
    )
    result.update(
        {
            "broker_execution_provenance_state": provenance_state,
            "broker_execution_provenance_error": (
                None
                if venue_resolved
                else "broker_execution_underlying_venue_unresolved_from_integrated_sor"
            ),
            "broker_execution_raw_envelope_schema": raw_envelope_schema,
            "broker_execution_source_type": source_type,
            "broker_execution_order_no": order_no,
            "broker_execution_no": execution_no,
            "broker_execution_stock_code": stock_code,
            "broker_execution_order_status": order_status,
            "broker_execution_side": side_code,
            "broker_execution_order_qty": order_qty,
            "broker_execution_cumulative_fill_qty": cumulative_fill_qty,
            "broker_execution_cumulative_fill_amount_krw": (cumulative_fill_amount),
            "broker_execution_remaining_qty": remaining_qty,
            "broker_execution_price": unit_execution_price,
            "broker_execution_reported_price": execution_price,
            "broker_execution_unit_fill_qty": unit_fill_qty,
            "broker_execution_time_hhmmss": execution_time,
            "broker_execution_venue": execution_venue_code,
            "broker_execution_reported_venue_scope": execution_venue_code,
            "broker_execution_actual_venue": (
                execution_venue_code if venue_resolved else None
            ),
            "broker_execution_venue_resolution_state": venue_resolution_state,
            "broker_execution_identity_complete": True,
            "broker_execution_actual_venue_complete": venue_resolved,
            "broker_execution_sor_yn": sor_yn,
            "broker_execution_fill_state": derived_fill_state,
            "broker_execution_identity": (
                "bex-" + _canonical_sha256(identity_payload)[:32]
            ),
            "broker_execution_content_sha256": _canonical_sha256(canonical_raw),
        }
    )
    return result


def validate_broker_execution_provenance(
    data: Mapping[str, Any],
    *,
    expected_qty: Any,
    expected_price: Any,
    expected_stock_code: Any,
    expected_side: Any,
    lifecycle_venue: Any,
    expected_fill_state: Any | None = None,
) -> str | None:
    """Return a stable validation error for canonical identity-complete proof."""

    source_schema = str(data.get("broker_execution_provenance_schema") or "")
    if source_schema not in {
        BROKER_EXECUTION_PROVENANCE_SCHEMA,
        BROKER_EXECUTION_PROVENANCE_LEGACY_SCHEMA,
    }:
        return "broker_execution_provenance_schema_invalid"
    if source_schema == BROKER_EXECUTION_PROVENANCE_LEGACY_SCHEMA and any(
        key in data for key in _BROKER_EXECUTION_V2_ONLY_FIELDS
    ):
        return "broker_execution_legacy_schema_semantic_drift"
    provenance_state = str(data.get("broker_execution_provenance_state") or "")
    if provenance_state not in {
        "complete",
        "identity_complete_venue_unresolved",
    }:
        return "broker_execution_provenance_not_identity_complete"
    if (
        source_schema == BROKER_EXECUTION_PROVENANCE_LEGACY_SCHEMA
        and provenance_state != "complete"
    ):
        return "broker_execution_legacy_schema_semantic_drift"
    side = str(data.get("broker_execution_side") or "").strip().upper()
    venue = str(data.get("broker_execution_venue") or "").strip().upper()
    native_projection = {
        "broker_raw_envelope_schema": data.get("broker_execution_raw_envelope_schema"),
        "broker_raw_source_type": data.get("broker_execution_source_type"),
        "9203": data.get("broker_execution_order_no"),
        "9001": data.get("broker_execution_stock_code"),
        "913": data.get("broker_execution_order_status"),
        "900": str(data.get("broker_execution_order_qty", "")),
        "902": str(data.get("broker_execution_remaining_qty", "")),
        "903": str(data.get("broker_execution_cumulative_fill_amount_krw", "")),
        "905": {"BUY": "+매수", "SELL": "-매도"}.get(side),
        "907": {"BUY": "2", "SELL": "1"}.get(side),
        "908": data.get("broker_execution_time_hhmmss"),
        "909": data.get("broker_execution_no"),
        "910": str(data.get("broker_execution_reported_price", "")),
        "911": str(data.get("broker_execution_cumulative_fill_qty", "")),
        "914": str(data.get("broker_execution_price", "")),
        "915": str(data.get("broker_execution_unit_fill_qty", "")),
        "2134": {"KRX": "1", "NXT": "2", "SOR": "0"}.get(venue),
        "2135": {"KRX": "KRX", "NXT": "NXT", "SOR": "통합"}.get(venue),
        "2136": data.get("broker_execution_sor_yn"),
    }
    rebuilt = build_broker_execution_provenance(
        native_projection,
        expected_qty=expected_qty,
        expected_price=expected_price,
        expected_stock_code=expected_stock_code,
        expected_side=expected_side,
        lifecycle_venue=lifecycle_venue,
        expected_fill_state=expected_fill_state,
    )
    if rebuilt.get("broker_execution_provenance_state") != provenance_state:
        return str(
            rebuilt.get("broker_execution_provenance_error")
            or "broker_execution_provenance_state_rebuild_mismatch"
        )
    legacy_ignored_fields = {
        "broker_execution_provenance_schema",
        "broker_execution_provenance_error",
        *_BROKER_EXECUTION_V2_ONLY_FIELDS,
    }
    for key, value in rebuilt.items():
        if (
            source_schema == BROKER_EXECUTION_PROVENANCE_LEGACY_SCHEMA
            and key in legacy_ignored_fields
        ):
            continue
        if data.get(key) != value:
            return f"broker_execution_canonical_field_mismatch:{key}"
    return None


def _normalize_record_id(value: Any) -> str:
    if isinstance(value, bool):
        raise ValueError("record_id_invalid")
    text = str(value if value is not None else "").strip()
    if not text or len(text) > 128:
        raise ValueError("record_id_invalid")
    return text


def _normalize_stock_code(value: Any) -> str:
    text = str(value or "").strip()
    if not re.fullmatch(r"[0-9]{6}", text):
        raise ValueError("stock_code_invalid")
    return text


def _normalize_submitted_order_numbers(data: Mapping[str, Any]) -> list[str]:
    primary = str(data.get("broker_order_no") or "").strip()
    list_text = str(data.get("broker_order_no_list") or "").strip()
    raw_values = list_text.split(",") if list_text else ([primary] if primary else [])
    order_numbers: list[str] = []
    for raw_value in raw_values:
        order_no = _raw_order_no(raw_value)
        if order_no not in order_numbers:
            order_numbers.append(order_no)
    if not order_numbers:
        raise ValueError("submitted_broker_order_no_required")
    if primary and primary not in order_numbers:
        raise ValueError("submitted_primary_order_not_in_order_list")
    return order_numbers


def normalize_submitted_order_quantities(
    data: Mapping[str, Any],
    order_numbers: list[str],
    requested_qty: Any,
) -> dict[str, int]:
    """Return an exact per-order requested-quantity map.

    A bundle total is unambiguous only for one broker order.  Split submissions
    must carry ``broker_order_qty_list`` as ``ORDER_NO:QTY`` pairs so a later
    execution receipt can be bound to the exact leg without dividing or
    otherwise inferring quantity from the aggregate.
    """

    requested_number = _positive_number(requested_qty)
    if requested_number is None or not requested_number.is_integer():
        raise ValueError("submitted_requested_qty_must_be_positive_integer")
    requested_int = int(requested_number)
    raw_text = str(data.get("broker_order_qty_list") or "").strip()
    if not raw_text:
        if len(order_numbers) != 1:
            raise ValueError("submitted_order_qty_list_required_for_split_bundle")
        return {order_numbers[0]: requested_int}

    quantities: dict[str, int] = {}
    for raw_pair in raw_text.split(","):
        pair = raw_pair.strip()
        if pair.count(":") != 1:
            raise ValueError("submitted_order_qty_pair_invalid")
        raw_order_no, raw_qty = (part.strip() for part in pair.split(":", 1))
        order_no = _raw_order_no(raw_order_no)
        if order_no in quantities:
            raise ValueError("submitted_order_qty_duplicate_order_no")
        if re.fullmatch(r"[1-9][0-9]*", raw_qty) is None:
            raise ValueError("submitted_order_qty_invalid")
        quantities[order_no] = int(raw_qty)

    if set(quantities) != set(order_numbers):
        raise ValueError("submitted_order_qty_order_set_mismatch")
    if sum(quantities.values()) != requested_int:
        raise ValueError("submitted_order_qty_total_mismatch")
    return quantities


def canonical_submitted_order_qty_list(quantities: Mapping[str, int]) -> str:
    """Serialize an already validated quantity map in broker-order order."""

    return ",".join(f"{order_no}:{int(qty)}" for order_no, qty in quantities.items())


def _validate_submission_contract_fields(
    data: Mapping[str, Any],
    order_numbers: list[str],
    *,
    allow_single_order_leg: bool = False,
    required_leg_contract: str | None = None,
) -> bool:
    summary_only = data.get("submission_summary_only")
    leg_contract = data.get("submission_leg_contract")
    if summary_only not in {None, True, False}:
        raise ValueError("submission_summary_only_invalid")
    if leg_contract not in {
        None,
        "exact_broker_order_leg_v1",
        "exact_broker_single_order_leg_v1",
    }:
        raise ValueError("submission_leg_contract_invalid")
    self_summarizing = data.get("submission_leg_self_summarizing")
    if leg_contract == "exact_broker_single_order_leg_v1":
        if (
            not allow_single_order_leg
            or len(order_numbers) != 1
            or self_summarizing is not True
            or summary_only is True
        ):
            raise ValueError("submission_single_order_leg_contract_invalid")
    elif self_summarizing is not None:
        raise ValueError("submission_leg_self_summarizing_without_contract")
    if summary_only is True:
        if leg_contract is not None:
            raise ValueError("submission_summary_leg_contract_conflict")
        expected = _positive_number(data.get("submission_summary_expected_leg_count"))
        if (
            expected is None
            or not expected.is_integer()
            or int(expected) != len(order_numbers)
        ):
            raise ValueError("submission_summary_expected_leg_count_mismatch")
        return True
    if "submission_summary_expected_leg_count" in data:
        raise ValueError("submission_summary_expected_leg_count_without_summary")
    if required_leg_contract is not None and leg_contract is None:
        return False
    if required_leg_contract is not None and leg_contract != required_leg_contract:
        raise ValueError("submission_leg_contract_required")
    return True


def _normalize_attempt_id(value: Any) -> str:
    if isinstance(value, bool):
        raise ValueError("attempt_id_invalid")
    text = str(value or "").strip()
    if not text or len(text) > 160 or any(char in text for char in "\r\n\x00"):
        raise ValueError("attempt_id_invalid")
    return text


def lineage_payload(
    *, record_id: Any, stock_code: Any, attempt_id: Any
) -> dict[str, str]:
    """Build the canonical scanner-attempt lineage used by every stage."""

    return {
        "record_id": _normalize_record_id(record_id),
        "stock_code": _normalize_stock_code(stock_code),
        "attempt_id": _normalize_attempt_id(attempt_id),
    }


def mint_main_lifecycle_id(*, record_id: Any, stock_code: Any, attempt_id: Any) -> str:
    """Mint a deterministic identity for one exact scanner attempt."""

    lineage = lineage_payload(
        record_id=record_id,
        stock_code=stock_code,
        attempt_id=attempt_id,
    )
    return MAIN_LIFECYCLE_ID_PREFIX + _canonical_sha256(lineage)[:32]


def validate_main_lifecycle_id(
    main_lifecycle_id: Any,
    *,
    record_id: Any,
    stock_code: Any,
    attempt_id: Any,
) -> bool:
    """Return true only for the ID derived from the supplied exact lineage."""

    value = str(main_lifecycle_id or "").strip()
    if not MAIN_LIFECYCLE_ID_RE.fullmatch(value):
        return False
    try:
        expected = mint_main_lifecycle_id(
            record_id=record_id,
            stock_code=stock_code,
            attempt_id=attempt_id,
        )
    except ValueError:
        return False
    return value == expected


def pipeline_lifecycle_stage_mapped(*, pipeline: Any, source_stage: Any) -> bool:
    """Return whether the exact pipeline/stage pair owns lifecycle identity.

    ``attempt_id`` is reserved lifecycle provenance only on mapped stages.  On
    every other pipeline event it can belong to an existing producer contract
    and must not be discarded while lifecycle telemetry is added.
    """

    return (
        str(pipeline or "").strip().upper(),
        str(source_stage or "").strip(),
    ) in PIPELINE_STAGE_MAP


def _pipeline_explicit_venue_with_source(
    stock: Mapping[str, Any], source_fields: Mapping[str, Any]
) -> tuple[str, str]:
    # Prefer exact stage-local execution/context fields over the long-lived
    # stock snapshot.  A stale stock.effective_venue must not hide the broker
    # execution venue or the venue attached to the current holding decision.
    for key in (
        "broker_actual_execution_venue",
        "holding_context_venue",
        "entry_execution_cohort",
        "effective_venue",
        "rising_missed_effective_venue",
        "entry_setup_live_policy_effective_venue",
        "venue",
    ):
        for source_name, source in (
            ("source_fields", source_fields),
            ("stock", stock),
        ):
            value = str(source.get(key) or "").strip().upper()
            if value in {"KRX", "NXT", "PREMARKET_KRX_LIKE"}:
                return value, f"{source_name}.{key}"
    return "UNKNOWN", "not_available_explicit_tradable_venue"


def _pipeline_explicit_session_bucket_with_source(
    stock: Mapping[str, Any], source_fields: Mapping[str, Any]
) -> tuple[str, str]:
    for key in (
        "holding_context_session",
        "market_session_bucket",
        "rising_missed_market_session_bucket",
        "entry_setup_live_policy_session_bucket",
        "session_bucket",
    ):
        for source_name, source in (
            ("source_fields", source_fields),
            ("stock", stock),
        ):
            value = str(source.get(key) or "").strip().lower()
            if value and value not in {
                "-",
                "nan",
                "none",
                "null",
                "unknown",
            }:
                return value[:80], f"{source_name}.{key}"
    return "unknown", "not_available_explicit_session_bucket"


def _pipeline_decision_trace_id(
    stock: Mapping[str, Any],
    source_fields: Mapping[str, Any],
    *,
    lifecycle_stage: str,
) -> str:
    source_keys = (
        "ai_decision_trace_id",
        "scale_in_ai_decision_trace_id",
        "pending_add_ai_decision_trace_id",
        "decision_trace_id",
        "scanner_async_ai_decision_trace_id",
    )
    explicit_values: list[str] = []
    for key in source_keys:
        value = str(source_fields.get(key) or "").strip()
        if value and value not in {"-", "None", "none", "null"}:
            if len(value) > MAX_DATA_STRING_LENGTH or "\x00" in value:
                return ""
            explicit_values.append(value)
    if len(set(explicit_values)) > 1:
        return ""
    if explicit_values:
        return explicit_values[0]
    # Position-level watching state is a valid fallback only for the original
    # entry decision and its submit descendants.  Holding/scale-in/exit receipt
    # rows need an explicit current-stage trace; otherwise a stale entry trace
    # would falsely bind unrelated decisions and venues to the same context.
    if lifecycle_stage not in {"entry_decision", "submit"}:
        return ""
    for key in (
        "last_watching_ai_decision_trace_id",
        "last_watching_ai_attempt_decision_trace_id",
    ):
        value = str(stock.get(key) or "").strip()
        if value and value not in {"-", "None", "none", "null"}:
            if len(value) > MAX_DATA_STRING_LENGTH or "\x00" in value:
                return ""
            return value
    return ""


def _pipeline_truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _pipeline_positive(value: Any) -> bool:
    try:
        number = float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return False
    return math.isfinite(number) and number > 0


def _pipeline_nonnegative_number_present(value: Any) -> bool:
    normalized = str(value if value is not None else "").strip()
    if normalized.lower() in {"", "-", "none", "null", "not_available"}:
        return False
    try:
        number = float(normalized.replace(",", ""))
    except (TypeError, ValueError):
        return False
    return math.isfinite(number) and number >= 0


def _pipeline_market_coverage_fields(
    source_fields: Mapping[str, Any], *, lifecycle_stage: str, source_stage: str
) -> dict[str, bool]:
    bbo_observed = _pipeline_truthy(source_fields.get("bbo_observed"))
    depth_observed = _pipeline_truthy(source_fields.get("depth_observed"))
    if not bbo_observed:
        bbo_observed = _pipeline_truthy(
            source_fields.get("holding_ai_orderbook_present")
        ) or any(
            _pipeline_positive(source_fields.get(bid_key))
            and _pipeline_positive(source_fields.get(ask_key))
            for bid_key, ask_key in (
                ("best_bid_at_submit", "best_ask_at_submit"),
                (
                    "scanner_promotion_reanchor_best_bid",
                    "scanner_promotion_reanchor_best_ask",
                ),
                ("market_data_effective_best_bid", "market_data_effective_best_ask"),
                ("effective_best_bid", "effective_best_ask"),
            )
        )
    if not depth_observed:
        orderbook_state = (
            str(source_fields.get("market_data_orderbook_state") or "").strip().lower()
        )
        depth_observed = (
            _pipeline_truthy(source_fields.get("holding_ai_orderbook_usable"))
            or _pipeline_nonnegative_number_present(
                source_fields.get("top3_depth_ratio")
            )
            or orderbook_state in {"ws", "rest_enriched", "fresh", "usable"}
        )
    if not bbo_observed and _pipeline_nonnegative_number_present(
        source_fields.get("spread_bps")
    ):
        bbo_observed = True
    return {
        "main_lifecycle_market_observation_expected": source_stage
        in {
            "scalping_scanner_fast_precheck",
            "ai_confirmed",
            "order_leg_sent",
            "order_bundle_submitted",
            "entry_execution_receipt_submission_custody",
            "ai_holding_review",
            "stat_action_decision_snapshot",
            "scale_in_order_leg_submitted",
            "scale_in_execution_receipt_submission_custody",
            "scale_in_order_submitted",
            "exit_signal",
            "exit_execution_receipt_submission_custody",
            "sell_order_sent",
        },
        "main_lifecycle_bbo_observed": bbo_observed,
        "main_lifecycle_depth_observed": depth_observed,
        # Holding/scale/exit observations carry exact aware timestamps and are
        # therefore usable lifecycle exposure heartbeats.  Scanner/entry rows
        # still require an explicit heartbeat and cannot inflate exposure by
        # merely repeating.
        "main_lifecycle_heartbeat": lifecycle_stage in {"holding", "scale_in", "exit"}
        or _pipeline_truthy(
            source_fields.get("main_lifecycle_heartbeat")
            or source_fields.get("lifecycle_heartbeat")
            or source_fields.get("heartbeat")
        ),
    }


def _pipeline_execution_clock_fields(
    source_fields: Mapping[str, Any], *, fallback_timestamp: datetime
) -> tuple[datetime, dict[str, Any]]:
    """Bind receipt ordering to receive time while retaining FID 908 time.

    This helper is intentionally tolerant on the live telemetry path.  It
    rewrites the lifecycle ordering timestamp only when both source timestamps
    are timezone-aware.  The postclose producer performs the strict raw-FID,
    source, equality, and lag validation and quarantines malformed rows.
    """

    source_type = str(
        source_fields.get("broker_raw_source_type")
        or source_fields.get("main_lifecycle_broker_raw_source_type")
        or ""
    ).strip()
    raw_execution_time = str(source_fields.get("908") or "").strip()
    if source_type != BROKER_EXECUTION_SOURCE_TYPE or not raw_execution_time:
        return fallback_timestamp, {
            "main_lifecycle_ordering_time_source": "source_observed_at"
        }

    timing_fields: dict[str, Any] = {
        "main_lifecycle_broker_execution_timing_expected": True,
    }
    try:
        received_value = source_fields.get("broker_execution_received_at")
        occurred_value = source_fields.get("broker_execution_observed_at")
        if received_value in (None, "") or occurred_value in (None, ""):
            raise ValueError("broker_execution_timing_source_missing")
        received_at = _aware_datetime(received_value).astimezone(KST)
        occurred_at = _aware_datetime(occurred_value).astimezone(KST)
    except (TypeError, ValueError):
        # Preserve exact lineage and the original source timestamp so the live
        # event remains fail-open.  Postclose sees the timing-required marker
        # plus raw type-00 proof and rejects the non-recoverable transition.
        timing_fields["main_lifecycle_ordering_time_source"] = (
            "broker_execution_timing_invalid"
        )
        return fallback_timestamp, timing_fields

    timing_fields.update(
        {
            "main_lifecycle_execution_received_at": received_at.isoformat(
                timespec="microseconds"
            ),
            "main_lifecycle_execution_occurred_at": occurred_at.isoformat(
                timespec="microseconds"
            ),
            "main_lifecycle_execution_trade_date": occurred_at.date().isoformat(),
            "main_lifecycle_execution_receive_time_source": str(
                source_fields.get("broker_execution_receive_time_source") or ""
            ).strip(),
            "main_lifecycle_ordering_time_source": (
                BROKER_EXECUTION_ORDERING_TIME_SOURCE
            ),
            "main_lifecycle_execution_occurrence_time_source": str(
                source_fields.get("broker_execution_time_source") or ""
            ).strip(),
        }
    )
    return received_at, timing_fields


def pipeline_lifecycle_fields_safe(
    stock: Mapping[str, Any] | None,
    stock_code: Any,
    *,
    pipeline: str,
    source_stage: str,
    source_fields: Mapping[str, Any] | None = None,
    observed_at: datetime | str | None = None,
) -> dict[str, Any]:
    """Return exact pipeline lineage without writing or changing live state.

    Missing or malformed scanner lineage returns an empty mapping so the
    existing pipeline event still emits normally.  Postclose records such a
    mapped row as an instrumentation gap; trading behavior remains fail-open.
    """

    try:
        if not isinstance(stock, Mapping):
            return {}
        normalized_pipeline = str(pipeline or "").strip().upper()
        normalized_source_stage = str(source_stage or "").strip()
        lifecycle_stage = PIPELINE_STAGE_MAP.get(
            (normalized_pipeline, normalized_source_stage)
        )
        if lifecycle_stage is None:
            return {}
        fields = source_fields if isinstance(source_fields, Mapping) else {}
        record_id = stock.get("id")
        normalized_stock_code = str(stock_code or "").strip()
        # ``scanner_promotion_id`` is the stable identity already propagated
        # by both the legacy direct scanner and the deadline scheduler. The
        # scheduler generation can be absent on the direct path and can also
        # appear only after the first precheck, so preferring it would split a
        # single lifecycle across two IDs. Use it only when no promotion
        # identity exists at all.
        stock_promotion_id = str(stock.get("scanner_promotion_id") or "").strip()
        field_promotion_id = str(fields.get("scanner_promotion_id") or "").strip()
        stock_generation_id = str(stock.get("scanner_generation_id") or "").strip()
        field_generation_id = str(fields.get("scanner_generation_id") or "").strip()
        if (
            stock_promotion_id
            and field_promotion_id
            and stock_promotion_id != field_promotion_id
        ) or (
            not (stock_promotion_id or field_promotion_id)
            and stock_generation_id
            and field_generation_id
            and stock_generation_id != field_generation_id
        ):
            return {}
        attempt_id = (
            stock_promotion_id
            or field_promotion_id
            or stock_generation_id
            or field_generation_id
        )
        # A mapped legacy/non-scanner row without exact lineage is expected to
        # remain observable as a postclose instrumentation gap.  Do not turn
        # that ordinary absence into a hot-path error-log storm.
        if (
            record_id in (None, "", 0)
            or not re.fullmatch(r"[0-9]{6}", normalized_stock_code)
            or not attempt_id
        ):
            return {}
        lineage = lineage_payload(
            record_id=record_id,
            stock_code=normalized_stock_code,
            attempt_id=attempt_id,
        )
        source_timestamp = _aware_datetime(observed_at).astimezone(KST)
        timestamp, execution_clock_fields = _pipeline_execution_clock_fields(
            fields,
            fallback_timestamp=source_timestamp,
        )
        lifecycle_trade_date = str(
            execution_clock_fields.get("main_lifecycle_execution_trade_date")
            or source_timestamp.date().isoformat()
        )
        lifecycle_id = mint_main_lifecycle_id(**lineage)
        decision_trace_id = _pipeline_decision_trace_id(
            stock,
            fields,
            lifecycle_stage=lifecycle_stage,
        )
        lifecycle_venue, lifecycle_venue_source = _pipeline_explicit_venue_with_source(
            stock, fields
        )
        lifecycle_session, lifecycle_session_source = (
            _pipeline_explicit_session_bucket_with_source(stock, fields)
        )
        result: dict[str, Any] = {
            "main_lifecycle_identity_schema": PIPELINE_IDENTITY_SCHEMA,
            "main_lifecycle_id": lifecycle_id,
            "attempt_id": lineage["attempt_id"],
            "main_lifecycle_attempt_id": lineage["attempt_id"],
            "main_lifecycle_record_id": lineage["record_id"],
            "main_lifecycle_stock_code": lineage["stock_code"],
            "main_lifecycle_trade_date": lifecycle_trade_date,
            "main_lifecycle_observed_at": timestamp.isoformat(timespec="microseconds"),
            "main_lifecycle_venue": lifecycle_venue,
            "main_lifecycle_venue_source": lifecycle_venue_source,
            "main_lifecycle_venue_provenance_status": (
                "resolved"
                if lifecycle_venue != "UNKNOWN"
                else "not_available_explicit_source"
            ),
            "main_lifecycle_session_bucket": lifecycle_session,
            "main_lifecycle_session_bucket_source": lifecycle_session_source,
            "main_lifecycle_session_provenance_status": (
                "resolved"
                if lifecycle_session != "unknown"
                else "not_available_explicit_source"
            ),
            "main_lifecycle_source_pipeline": normalized_pipeline,
            "main_lifecycle_source_stage": normalized_source_stage,
            "main_lifecycle_stage": lifecycle_stage,
            "main_lifecycle_decision_authority": ("source_only_lifecycle_observation"),
            "main_lifecycle_runtime_effect": False,
            "main_lifecycle_order_authority": False,
            "main_lifecycle_provider_authority": False,
            **execution_clock_fields,
            **_pipeline_market_coverage_fields(
                fields,
                lifecycle_stage=lifecycle_stage,
                source_stage=normalized_source_stage,
            ),
        }
        result.update(
            _pipeline_carry_in_custody_fields(
                stock,
                lifecycle_stage=lifecycle_stage,
                lifecycle_trade_date=lifecycle_trade_date,
            )
        )
        if decision_trace_id:
            result["main_lifecycle_decision_trace_id"] = decision_trace_id
        return result
    except Exception as exc:
        try:
            log_error(f"[MAIN_LIFECYCLE_PIPELINE] identity bind failed: {exc}")
        except Exception:
            pass
        return {}


def _pipeline_carry_in_custody_fields(
    stock: Mapping[str, Any],
    *,
    lifecycle_stage: str,
    lifecycle_trade_date: str,
) -> dict[str, Any]:
    """Attest prior-day custody without reconstructing an entry fill."""

    if lifecycle_stage not in {"holding", "exit"}:
        return {}
    try:
        trade_date = date.fromisoformat(lifecycle_trade_date)
    except ValueError:
        return {}
    for source_field in ("holding_started_at", "buy_time"):
        raw_value = stock.get(source_field)
        if raw_value in (None, "", 0, "0"):
            continue
        try:
            if isinstance(raw_value, datetime):
                entry_at = raw_value
            elif isinstance(raw_value, (int, float)) and not isinstance(
                raw_value, bool
            ):
                entry_at = datetime.fromtimestamp(float(raw_value), tz=KST)
            else:
                entry_at = datetime.fromisoformat(str(raw_value).strip())
            entry_at = (
                entry_at.replace(tzinfo=KST)
                if entry_at.tzinfo is None
                else entry_at.astimezone(KST)
            )
        except (OSError, OverflowError, TypeError, ValueError):
            continue
        if entry_at.date() >= trade_date:
            continue
        return {
            "main_lifecycle_carry_in_custody_schema": CARRY_IN_CUSTODY_SCHEMA,
            "main_lifecycle_origin": "preexisting_position_custody",
            "main_lifecycle_carry_in_entry_observed_at": entry_at.isoformat(
                timespec="microseconds"
            ),
            "main_lifecycle_carry_in_entry_source": f"stock.{source_field}",
        }
    return {}


def _aware_datetime(value: datetime | str | None) -> datetime:
    parsed = value or datetime.now().astimezone()
    if isinstance(parsed, str):
        parsed = datetime.fromisoformat(parsed)
    if not isinstance(parsed, datetime) or parsed.tzinfo is None:
        raise ValueError("observed_at_must_be_timezone_aware")
    return parsed


def validate_broker_execution_timing(
    data: Mapping[str, Any], *, observed_at: datetime | str
) -> str | None:
    """Validate receive-time ordering against the official FID 908 instant."""

    if data.get("broker_execution_timing_schema") != BROKER_EXECUTION_TIMING_SCHEMA:
        return "broker_execution_timing_schema_invalid"
    if data.get("broker_execution_ordering_time_source") != (
        BROKER_EXECUTION_ORDERING_TIME_SOURCE
    ):
        return "broker_execution_ordering_time_source_invalid"
    if data.get("broker_execution_occurrence_time_source") != (
        BROKER_EXECUTION_OCCURRENCE_TIME_SOURCE
    ):
        return "broker_execution_occurrence_time_source_invalid"
    if data.get("broker_execution_receive_time_source") != (
        BROKER_EXECUTION_RECEIVE_TIME_SOURCE
    ):
        return "broker_execution_receive_time_source_invalid"
    received_value = data.get("broker_execution_received_at")
    occurred_value = data.get("broker_execution_occurred_at")
    if received_value in (None, ""):
        return "broker_execution_received_at_missing"
    if occurred_value in (None, ""):
        return "broker_execution_occurred_at_missing"
    try:
        ordering_at = _aware_datetime(observed_at).astimezone(KST)
        received_at = _aware_datetime(received_value).astimezone(KST)
        occurred_at = _aware_datetime(occurred_value).astimezone(KST)
    except (TypeError, ValueError):
        return "broker_execution_timing_timestamp_invalid"
    if ordering_at != received_at:
        return "broker_execution_ordering_timestamp_not_receive_time"
    if occurred_at.microsecond != 0:
        return "broker_execution_occurrence_time_precision_invalid"
    execution_hhmmss = str(data.get("broker_execution_time_hhmmss") or "").strip()
    if occurred_at.strftime("%H%M%S") != execution_hhmmss:
        return "broker_execution_occurrence_time_fid908_mismatch"
    lag_sec = (received_at - occurred_at).total_seconds()
    if lag_sec < -BROKER_EXECUTION_MAX_NEGATIVE_LAG_SEC:
        return "broker_execution_receive_time_precedes_occurrence"
    if lag_sec > BROKER_EXECUTION_MAX_RECEIVE_LAG_SEC:
        return "broker_execution_receive_lag_exceeds_bound"
    try:
        declared_lag_ms = float(data.get("broker_execution_receive_lag_ms"))
    except (TypeError, ValueError):
        return "broker_execution_receive_lag_ms_invalid"
    if (
        not math.isfinite(declared_lag_ms)
        or abs(declared_lag_ms - lag_sec * 1000.0) > 0.001
    ):
        return "broker_execution_receive_lag_ms_mismatch"
    if not isinstance(data.get("broker_execution_lifecycle_observed_at_rebound"), bool):
        return "broker_execution_lifecycle_observed_at_rebound_invalid"
    return None


def _safe_scalar(value: Any) -> Any:
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, str):
        if len(value) > MAX_DATA_STRING_LENGTH or "\x00" in value:
            raise ValueError("transition_data_string_invalid")
        return value
    if isinstance(value, int):
        if abs(value) > 10**18:
            raise ValueError("transition_data_number_invalid")
        return value
    if isinstance(value, float):
        if not math.isfinite(value) or abs(value) > 10**18:
            raise ValueError("transition_data_number_invalid")
        return value
    raise ValueError("transition_data_value_invalid")


def _sanitize_data(data: Mapping[str, Any] | None) -> dict[str, Any]:
    if data is None:
        return {}
    if not isinstance(data, Mapping):
        raise ValueError("transition_data_invalid")
    sanitized: dict[str, Any] = {}
    for raw_key, value in data.items():
        key = str(raw_key)
        key_lower = key.lower()
        if any(part in key_lower for part in _SENSITIVE_KEY_PARTS):
            raise ValueError("sensitive_transition_data_forbidden")
        if key not in _ALLOWED_DATA_FIELDS:
            continue
        sanitized[key] = _safe_scalar(value)
    return sanitized


def transition_content_sha256(row: Mapping[str, Any]) -> str:
    """Hash a transition without its self-authenticating hash fields."""

    content = {
        key: value
        for key, value in row.items()
        if key not in {"event_id", "transition_content_sha256"}
    }
    return _canonical_sha256(content)


def build_transition(
    *,
    main_lifecycle_id: str,
    record_id: Any,
    stock_code: Any,
    attempt_id: Any,
    trade_date: str | date,
    stage: str,
    observed_at: datetime | str | None = None,
    venue: str = "UNKNOWN",
    session_bucket: str = "unknown",
    data: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build and strictly validate one source-only transition record."""

    lineage = lineage_payload(
        record_id=record_id,
        stock_code=stock_code,
        attempt_id=attempt_id,
    )
    if not validate_main_lifecycle_id(main_lifecycle_id, **lineage):
        raise ValueError("main_lifecycle_id_lineage_mismatch")
    normalized_stage = str(stage or "").strip().lower()
    if normalized_stage not in VALID_STAGES:
        raise ValueError("lifecycle_stage_invalid")
    target_date = (
        trade_date.isoformat() if isinstance(trade_date, date) else str(trade_date)
    )
    target_date = date.fromisoformat(target_date).isoformat()
    timestamp = _aware_datetime(observed_at)
    event_data = _sanitize_data(data)
    normalized_venue = str(venue or "UNKNOWN").strip().upper() or "UNKNOWN"

    if normalized_stage == "submit":
        if _positive_number(event_data.get("requested_qty")) is None:
            raise ValueError("submit_requested_qty_invalid")
        if event_data.get("terminal_no_fill") is not True:
            if event_data.get("actual_broker_order_submitted") is not True:
                raise ValueError("submit_actual_broker_order_required")
            order_numbers = _normalize_submitted_order_numbers(event_data)
            order_quantities = normalize_submitted_order_quantities(
                event_data,
                order_numbers,
                event_data.get("requested_qty"),
            )
            submission_contract_attested = _validate_submission_contract_fields(
                event_data,
                order_numbers,
                required_leg_contract="exact_broker_order_leg_v1",
            )
            if not submission_contract_attested:
                event_data["submission_contract_legacy_unattested"] = True
            event_data["broker_order_no"] = order_numbers[0]
            event_data["broker_order_no_list"] = ",".join(order_numbers)
            event_data["broker_order_qty_list"] = canonical_submitted_order_qty_list(
                order_quantities
            )
    if normalized_stage == "fill":
        if event_data.get("fill_state") not in VALID_FILL_STATES:
            raise ValueError("fill_state_invalid")
        if _positive_number(event_data.get("fill_qty")) is None:
            raise ValueError("fill_qty_invalid")
        if _positive_number(event_data.get("fill_price")) is None:
            raise ValueError("fill_price_invalid")
    if normalized_stage == "scale_in":
        decision = str(event_data.get("scale_in_decision") or "").upper()
        if decision not in VALID_SCALE_IN_DECISIONS:
            raise ValueError("scale_in_decision_required")
        event_data["scale_in_decision"] = decision
        if decision == "ADD" and (
            ("fill_qty" in event_data) != ("fill_price" in event_data)
            or (
                "fill_qty" in event_data
                and (
                    _positive_number(event_data.get("fill_qty")) is None
                    or _positive_number(event_data.get("fill_price")) is None
                )
            )
        ):
            raise ValueError("scale_in_add_fill_pair_invalid")
        if decision != "ADD" and (
            "fill_qty" in event_data or "fill_price" in event_data
        ):
            raise ValueError("scale_in_non_add_fill_forbidden")
        if (
            decision == "ADD"
            and "fill_qty" not in event_data
            and event_data.get("actual_broker_order_submitted") is True
        ):
            if _positive_number(event_data.get("requested_qty")) is None:
                raise ValueError("scale_in_submit_requested_qty_invalid")
            order_numbers = _normalize_submitted_order_numbers(event_data)
            order_quantities = normalize_submitted_order_quantities(
                event_data,
                order_numbers,
                event_data.get("requested_qty"),
            )
            submission_contract_attested = _validate_submission_contract_fields(
                event_data,
                order_numbers,
                required_leg_contract="exact_broker_order_leg_v1",
            )
            if not submission_contract_attested:
                event_data["submission_contract_legacy_unattested"] = True
            event_data["broker_order_no"] = order_numbers[0]
            event_data["broker_order_no_list"] = ",".join(order_numbers)
            event_data["broker_order_qty_list"] = canonical_submitted_order_qty_list(
                order_quantities
            )
    if event_data.get("terminal_no_fill") is True:
        if normalized_stage not in NO_FILL_TERMINAL_STAGES:
            raise ValueError("terminal_no_fill_stage_invalid")
        if event_data.get("reconciled_final_exit") is True:
            raise ValueError("terminal_modes_conflict")
    if event_data.get("reconciled_final_exit") is True:
        if normalized_stage != "exit":
            raise ValueError("reconciled_final_exit_stage_invalid")
        if event_data.get("broker_reconciled") is not True:
            raise ValueError("final_exit_broker_reconciliation_required")
        if _positive_number(event_data.get("exit_qty")) is None:
            raise ValueError("final_exit_qty_invalid")
        if _positive_number(event_data.get("exit_price")) is None:
            raise ValueError("final_exit_price_invalid")
    if normalized_stage == "exit" and (
        "exit_qty" in event_data or "exit_price" in event_data
    ):
        if _positive_number(event_data.get("exit_qty")) is None:
            raise ValueError("exit_qty_invalid")
        if _positive_number(event_data.get("exit_price")) is None:
            raise ValueError("exit_price_invalid")
    if (
        normalized_stage == "exit"
        and "exit_qty" not in event_data
        and event_data.get("actual_broker_order_submitted") is True
    ):
        if _positive_number(event_data.get("requested_qty")) is None:
            raise ValueError("exit_submit_requested_qty_invalid")
        order_numbers = _normalize_submitted_order_numbers(event_data)
        order_quantities = normalize_submitted_order_quantities(
            event_data,
            order_numbers,
            event_data.get("requested_qty"),
        )
        submission_contract_attested = _validate_submission_contract_fields(
            event_data,
            order_numbers,
            allow_single_order_leg=True,
            required_leg_contract="exact_broker_single_order_leg_v1",
        )
        if not submission_contract_attested:
            event_data["submission_contract_legacy_unattested"] = True
        event_data["broker_order_no"] = order_numbers[0]
        event_data["broker_order_no_list"] = ",".join(order_numbers)
        event_data["broker_order_qty_list"] = canonical_submitted_order_qty_list(
            order_quantities
        )

    execution_qty: Any | None = None
    execution_price: Any | None = None
    execution_fill_state: Any | None = None
    if normalized_stage == "fill":
        execution_qty = event_data.get("fill_qty")
        execution_price = event_data.get("fill_price")
        execution_fill_state = event_data.get("fill_state")
    elif (
        normalized_stage == "scale_in"
        and event_data.get("scale_in_decision") == "ADD"
        and "fill_qty" in event_data
    ):
        execution_qty = event_data.get("fill_qty")
        execution_price = event_data.get("fill_price")
    elif normalized_stage == "exit" and "exit_qty" in event_data:
        execution_qty = event_data.get("exit_qty")
        execution_price = event_data.get("exit_price")

    execution_timing_validated = False
    if execution_qty is not None:
        state = (
            str(event_data.get("broker_execution_provenance_state") or "")
            .strip()
            .lower()
        )
        if not state:
            event_data.update(
                {
                    "broker_execution_provenance_schema": (
                        BROKER_EXECUTION_PROVENANCE_SCHEMA
                    ),
                    "broker_execution_official_reference_sha": (
                        KIWOOM_OFFICIAL_REFERENCE_SHA
                    ),
                    "broker_execution_provenance_state": "missing",
                    "broker_execution_provenance_error": (
                        "official_broker_execution_raw_fields_missing"
                    ),
                }
            )
            state = "missing"
        provenance_schema = str(
            event_data.get("broker_execution_provenance_schema") or ""
        )
        if provenance_schema not in {
            BROKER_EXECUTION_PROVENANCE_SCHEMA,
            BROKER_EXECUTION_PROVENANCE_LEGACY_SCHEMA,
        }:
            raise ValueError("broker_execution_provenance_schema_invalid")
        if event_data.get("broker_execution_official_reference_sha") != (
            KIWOOM_OFFICIAL_REFERENCE_SHA
        ):
            raise ValueError("broker_execution_official_reference_sha_invalid")
        if state not in {
            "complete",
            "identity_complete_venue_unresolved",
            "missing",
            "incomplete",
            "invalid",
        }:
            raise ValueError("broker_execution_provenance_state_invalid")
        if provenance_schema == BROKER_EXECUTION_PROVENANCE_LEGACY_SCHEMA:
            if state == "identity_complete_venue_unresolved" or any(
                key in event_data for key in _BROKER_EXECUTION_V2_ONLY_FIELDS
            ):
                raise ValueError("broker_execution_legacy_schema_semantic_drift")
        if state == "complete":
            if str(event_data.get("broker_execution_provenance_error") or "").strip():
                raise ValueError("broker_execution_complete_with_error")
        elif state == "identity_complete_venue_unresolved":
            if not str(
                event_data.get("broker_execution_provenance_error") or ""
            ).strip():
                raise ValueError("broker_execution_provenance_error_required")
        else:
            provenance_error = str(
                event_data.get("broker_execution_provenance_error") or ""
            ).strip()
            if not provenance_error:
                raise ValueError("broker_execution_provenance_error_required")
        if state in {"complete", "identity_complete_venue_unresolved"}:
            provenance_error = validate_broker_execution_provenance(
                event_data,
                expected_qty=execution_qty,
                expected_price=execution_price,
                expected_stock_code=lineage["stock_code"],
                expected_side="SELL" if normalized_stage == "exit" else "BUY",
                lifecycle_venue=normalized_venue,
                expected_fill_state=execution_fill_state,
            )
            if provenance_error is not None:
                raise ValueError(
                    f"broker_execution_provenance_invalid:{provenance_error}"
                )
            timing_error = validate_broker_execution_timing(
                event_data,
                observed_at=timestamp,
            )
            if timing_error is not None:
                raise ValueError(f"broker_execution_timing_invalid:{timing_error}")
            execution_timing_validated = True

    has_execution_timing = any(
        key in event_data
        for key in (
            "broker_execution_timing_schema",
            "broker_execution_received_at",
            "broker_execution_occurred_at",
            "broker_execution_receive_time_source",
            "broker_execution_ordering_time_source",
            "broker_execution_occurrence_time_source",
            "broker_execution_receive_lag_ms",
            "broker_execution_lifecycle_observed_at_rebound",
            "broker_execution_receipt_companion",
            "broker_execution_receipt_companion_of_identity",
        )
    )
    if execution_qty is None and has_execution_timing:
        if normalized_stage != "holding":
            raise ValueError("broker_execution_companion_stage_invalid")
        if event_data.get("broker_execution_receipt_companion") is not True:
            raise ValueError("broker_execution_timing_non_execution_forbidden")
        companion_identity = str(
            event_data.get("broker_execution_identity") or ""
        ).strip()
        companion_of_identity = str(
            event_data.get("broker_execution_receipt_companion_of_identity") or ""
        ).strip()
        if not companion_identity or companion_of_identity != companion_identity:
            raise ValueError("broker_execution_companion_identity_binding_invalid")
        if str(event_data.get("broker_execution_side") or "").strip() != "BUY":
            raise ValueError("broker_execution_companion_side_invalid")
        companion_state = str(
            event_data.get("broker_execution_provenance_state") or ""
        ).strip()
        if companion_state not in {
            "complete",
            "identity_complete_venue_unresolved",
        }:
            raise ValueError("broker_execution_companion_provenance_not_complete")
        companion_error = validate_broker_execution_provenance(
            event_data,
            expected_qty=event_data.get("broker_execution_unit_fill_qty"),
            expected_price=event_data.get("broker_execution_price"),
            expected_stock_code=lineage["stock_code"],
            expected_side=event_data.get("broker_execution_side"),
            lifecycle_venue=normalized_venue,
            expected_fill_state=event_data.get("broker_execution_fill_state"),
        )
        if companion_error is not None:
            raise ValueError(
                f"broker_execution_companion_provenance_invalid:{companion_error}"
            )
        timing_error = validate_broker_execution_timing(
            event_data,
            observed_at=timestamp,
        )
        if timing_error is not None:
            raise ValueError(f"broker_execution_timing_invalid:{timing_error}")
        execution_timing_validated = True

    if has_execution_timing and not execution_timing_validated:
        # A partial timing fragment must never switch logical trade-date
        # validation to an absent or synthesized occurrence clock.  Exact
        # receipt timing is usable only together with identity-complete raw
        # provenance (or its explicitly bound non-economic companion).
        raise ValueError("broker_execution_timing_without_validated_receipt")

    logical_timestamp = timestamp
    if execution_timing_validated:
        logical_timestamp = _aware_datetime(
            event_data.get("broker_execution_occurred_at")
        )
    if logical_timestamp.astimezone(KST).date().isoformat() != target_date:
        raise ValueError("observed_at_trade_date_mismatch")

    row: dict[str, Any] = {
        "schema": JOURNAL_SCHEMA,
        "trade_date": target_date,
        "observed_at": timestamp.isoformat(timespec="microseconds"),
        "main_lifecycle_id": main_lifecycle_id,
        **lineage,
        "stage": normalized_stage,
        "venue": normalized_venue,
        "session_bucket": str(session_bucket or "unknown").strip().lower() or "unknown",
        "data": event_data,
        **AUTHORITY_CONTRACT,
    }
    if len(_canonical_json(row)) > MAX_TRANSITION_BYTES:
        raise ValueError("transition_payload_too_large")
    digest = transition_content_sha256(row)
    row["event_id"] = f"mle-{digest[:32]}"
    row["transition_content_sha256"] = digest
    return row


def _positive_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number <= 0 or number != number or number in {float("inf"), float("-inf")}:
        return None
    return number


def _append_jsonl(path: Path, row: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(path.parent, 0o700)
    except OSError:
        pass
    payload = json.dumps(
        row,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
        allow_nan=False,
    )
    with _WRITE_LOCK, path.open("a", encoding="utf-8") as handle:
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            handle.write(payload + "\n")
            handle.flush()
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def append_transition_safe(
    *,
    main_lifecycle_id: str,
    record_id: Any,
    stock_code: Any,
    attempt_id: Any,
    trade_date: str | date,
    stage: str,
    observed_at: datetime | str | None = None,
    venue: str = "UNKNOWN",
    session_bucket: str = "unknown",
    data: Mapping[str, Any] | None = None,
    output_path: Path | None = None,
) -> bool:
    """Append one transition and return false on every telemetry failure."""

    try:
        row = build_transition(
            main_lifecycle_id=main_lifecycle_id,
            record_id=record_id,
            stock_code=stock_code,
            attempt_id=attempt_id,
            trade_date=trade_date,
            stage=stage,
            observed_at=observed_at,
            venue=venue,
            session_bucket=session_bucket,
            data=data,
        )
        _append_jsonl(output_path or journal_path(trade_date), row)
        return True
    except Exception as exc:  # telemetry must never affect the live caller
        try:
            log_error(f"[MAIN_LIFECYCLE_JOURNAL] append failed: {exc}")
        except Exception:
            pass
        return False


def start_scanner_attempt_safe(
    *,
    record_id: Any,
    stock_code: Any,
    attempt_id: Any,
    trade_date: str | date,
    observed_at: datetime | str | None = None,
    venue: str = "UNKNOWN",
    session_bucket: str = "unknown",
    data: Mapping[str, Any] | None = None,
    output_path: Path | None = None,
) -> dict[str, str] | None:
    """Mint, persist, and return the exact scanner-attempt context fail-open."""

    try:
        lineage = lineage_payload(
            record_id=record_id,
            stock_code=stock_code,
            attempt_id=attempt_id,
        )
        lifecycle_id = mint_main_lifecycle_id(**lineage)
        append_transition_safe(
            main_lifecycle_id=lifecycle_id,
            **lineage,
            trade_date=trade_date,
            stage="scanner",
            observed_at=observed_at,
            venue=venue,
            session_bucket=session_bucket,
            data=data,
            output_path=output_path,
        )
        return {"main_lifecycle_id": lifecycle_id, **lineage}
    except Exception as exc:
        try:
            log_error(f"[MAIN_LIFECYCLE_JOURNAL] scanner bind failed: {exc}")
        except Exception:
            pass
        return None


__all__ = [
    "AUTHORITY_CONTRACT",
    "BROKER_EXECUTION_NATIVE_FIELD_ALIASES",
    "BROKER_EXECUTION_PROVENANCE_SCHEMA",
    "BROKER_EXECUTION_RAW_ENVELOPE_SCHEMA",
    "BROKER_EXECUTION_RECEIVE_TIME_SOURCE",
    "BROKER_EXECUTION_SOURCE_TYPE",
    "CARRY_IN_CUSTODY_SCHEMA",
    "CARRY_IN_CUSTODY_REQUIRED_DATE",
    "JOURNAL_SCHEMA",
    "KIWOOM_OFFICIAL_REFERENCE_SHA",
    "MAX_TRANSITION_BYTES",
    "PIPELINE_IDENTITY_SCHEMA",
    "PIPELINE_STAGE_MAP",
    "VALID_FILL_STATES",
    "VALID_SCALE_IN_DECISIONS",
    "VALID_STAGES",
    "append_transition_safe",
    "build_broker_execution_provenance",
    "build_transition",
    "journal_path",
    "lineage_payload",
    "mint_main_lifecycle_id",
    "pipeline_lifecycle_fields_safe",
    "start_scanner_attempt_safe",
    "transition_content_sha256",
    "validate_broker_execution_provenance",
    "validate_main_lifecycle_id",
]
