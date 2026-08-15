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

# Only these existing live pipeline stages may become lifecycle transitions.
# The map is intentionally exact: the postclose producer must never infer a
# stage from a nearby timestamp, symbol, similarly named event, or free-form
# reason text.
PIPELINE_STAGE_MAP: dict[tuple[str, str], str] = {
    ("ENTRY_PIPELINE", "scalping_scanner_fast_precheck"): "scanner",
    ("ENTRY_PIPELINE", "scanner_async_result_commit"): "scanner",
    ("ENTRY_PIPELINE", "ai_confirmed"): "entry_decision",
    ("ENTRY_PIPELINE", "order_bundle_submitted"): "submit",
    ("HOLDING_PIPELINE", "position_rebased_after_fill"): "fill",
    ("HOLDING_PIPELINE", "holding_started"): "holding",
    ("HOLDING_PIPELINE", "ai_holding_review"): "holding",
    ("HOLDING_PIPELINE", "stat_action_decision_snapshot"): "scale_in",
    ("HOLDING_PIPELINE", "scale_in_order_submitted"): "scale_in",
    ("HOLDING_PIPELINE", "scale_in_executed"): "scale_in",
    ("HOLDING_PIPELINE", "exit_signal"): "exit",
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
        "payload_sha256",
        "paired_replay_parent_id",
        "paired_replay_arm",
        "actual_broker_order_submitted",
        "broker_order_no",
        "broker_order_no_list",
        "broker_reconciled",
        "broker_execution_no",
        "broker_execution_order_no",
        "broker_execution_time_source",
        "broker_execution_time_raw",
        "broker_actual_execution_venue",
        "broker_sor_flag",
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
        "session_exposure_start_at",
        "session_exposure_end_at",
        "heartbeat",
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


def _pipeline_explicit_venue(
    stock: Mapping[str, Any], source_fields: Mapping[str, Any]
) -> str:
    for source in (stock, source_fields):
        for key in (
            "effective_venue",
            "rising_missed_effective_venue",
            "entry_setup_live_policy_effective_venue",
            "venue",
        ):
            value = str(source.get(key) or "").strip().upper()
            if value in {"KRX", "NXT", "PREMARKET_KRX_LIKE"}:
                return value
    return "UNKNOWN"


def _pipeline_explicit_session_bucket(
    stock: Mapping[str, Any], source_fields: Mapping[str, Any]
) -> str:
    for source in (stock, source_fields):
        for key in (
            "market_session_bucket",
            "rising_missed_market_session_bucket",
            "entry_setup_live_policy_session_bucket",
            "session_bucket",
        ):
            value = str(source.get(key) or "").strip().lower()
            if value and value not in {"-", "none", "null", "unknown"}:
                return value[:80]
    return "unknown"


def _pipeline_decision_trace_id(
    stock: Mapping[str, Any], source_fields: Mapping[str, Any]
) -> str:
    for source, keys in (
        (
            source_fields,
            (
                "ai_decision_trace_id",
                "decision_trace_id",
                "scanner_async_ai_decision_trace_id",
            ),
        ),
        (
            stock,
            (
                "last_watching_ai_decision_trace_id",
                "last_watching_ai_attempt_decision_trace_id",
            ),
        ),
    ):
        for key in keys:
            value = str(source.get(key) or "").strip()
            if value and value not in {"-", "None", "none", "null"}:
                return value[:MAX_DATA_STRING_LENGTH]
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
        orderbook_state = str(
            source_fields.get("market_data_orderbook_state") or ""
        ).strip().lower()
        depth_observed = _pipeline_truthy(
            source_fields.get("holding_ai_orderbook_usable")
        ) or _pipeline_nonnegative_number_present(
            source_fields.get("top3_depth_ratio")
        ) or orderbook_state in {"ws", "rest_enriched", "fresh", "usable"}
    if not bbo_observed and _pipeline_nonnegative_number_present(
        source_fields.get("spread_bps")
    ):
        bbo_observed = True
    return {
        "main_lifecycle_market_observation_expected": source_stage
        in {
            "scalping_scanner_fast_precheck",
            "ai_confirmed",
            "order_bundle_submitted",
            "ai_holding_review",
            "stat_action_decision_snapshot",
            "scale_in_order_submitted",
            "exit_signal",
            "sell_order_sent",
        },
        "main_lifecycle_bbo_observed": bbo_observed,
        "main_lifecycle_depth_observed": depth_observed,
        # Holding/scale/exit observations carry exact aware timestamps and are
        # therefore usable lifecycle exposure heartbeats.  Scanner/entry rows
        # still require an explicit heartbeat and cannot inflate exposure by
        # merely repeating.
        "main_lifecycle_heartbeat": lifecycle_stage
        in {"holding", "scale_in", "exit"}
        or _pipeline_truthy(
            source_fields.get("main_lifecycle_heartbeat")
            or source_fields.get("lifecycle_heartbeat")
            or source_fields.get("heartbeat")
        ),
    }


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
        attempt_id = str(stock.get("scanner_generation_id") or "").strip()
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
        timestamp = _aware_datetime(observed_at).astimezone(KST)
        lifecycle_id = mint_main_lifecycle_id(**lineage)
        decision_trace_id = _pipeline_decision_trace_id(stock, fields)
        result: dict[str, Any] = {
            "main_lifecycle_identity_schema": PIPELINE_IDENTITY_SCHEMA,
            "main_lifecycle_id": lifecycle_id,
            "attempt_id": lineage["attempt_id"],
            "main_lifecycle_attempt_id": lineage["attempt_id"],
            "main_lifecycle_record_id": lineage["record_id"],
            "main_lifecycle_stock_code": lineage["stock_code"],
            "main_lifecycle_trade_date": timestamp.date().isoformat(),
            "main_lifecycle_observed_at": timestamp.isoformat(timespec="microseconds"),
            "main_lifecycle_venue": _pipeline_explicit_venue(stock, fields),
            "main_lifecycle_session_bucket": _pipeline_explicit_session_bucket(
                stock, fields
            ),
            "main_lifecycle_source_pipeline": normalized_pipeline,
            "main_lifecycle_source_stage": normalized_source_stage,
            "main_lifecycle_stage": lifecycle_stage,
            "main_lifecycle_decision_authority": (
                "source_only_lifecycle_observation"
            ),
            "main_lifecycle_runtime_effect": False,
            "main_lifecycle_order_authority": False,
            "main_lifecycle_provider_authority": False,
            **_pipeline_market_coverage_fields(
                fields,
                lifecycle_stage=lifecycle_stage,
                source_stage=normalized_source_stage,
            ),
        }
        if decision_trace_id:
            result["main_lifecycle_decision_trace_id"] = decision_trace_id
        return result
    except Exception as exc:
        try:
            log_error(f"[MAIN_LIFECYCLE_PIPELINE] identity bind failed: {exc}")
        except Exception:
            pass
        return {}


def _aware_datetime(value: datetime | str | None) -> datetime:
    parsed = value or datetime.now().astimezone()
    if isinstance(parsed, str):
        parsed = datetime.fromisoformat(parsed)
    if not isinstance(parsed, datetime) or parsed.tzinfo is None:
        raise ValueError("observed_at_must_be_timezone_aware")
    return parsed


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
    if timestamp.astimezone(KST).date().isoformat() != target_date:
        raise ValueError("observed_at_trade_date_mismatch")
    event_data = _sanitize_data(data)

    if normalized_stage == "submit":
        if _positive_number(event_data.get("requested_qty")) is None:
            raise ValueError("submit_requested_qty_invalid")
        if event_data.get("terminal_no_fill") is not True:
            if event_data.get("actual_broker_order_submitted") is not True:
                raise ValueError("submit_actual_broker_order_required")
            broker_order_no = str(event_data.get("broker_order_no") or "").strip()
            if broker_order_no.lower() in {"", "-", "none", "null"}:
                raise ValueError("submit_broker_order_no_required")
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

    execution_provenance_keys = {
        "broker_execution_no",
        "broker_execution_order_no",
        "broker_execution_time_source",
        "broker_execution_time_raw",
        "broker_actual_execution_venue",
        "broker_sor_flag",
    }
    if execution_provenance_keys.intersection(event_data):
        required_execution_keys = execution_provenance_keys - {"broker_sor_flag"}
        if not required_execution_keys.issubset(event_data):
            raise ValueError("broker_execution_provenance_incomplete")
        execution_stage = bool(
            normalized_stage == "fill"
            or (
                normalized_stage == "scale_in"
                and event_data.get("scale_in_decision") == "ADD"
                and "fill_qty" in event_data
            )
            or (
                normalized_stage == "exit"
                and "exit_qty" in event_data
                and "exit_price" in event_data
            )
        )
        if not execution_stage:
            raise ValueError("broker_execution_provenance_stage_invalid")
        execution_no = str(event_data.get("broker_execution_no") or "").strip()
        if (
            not execution_no
            or len(execution_no) > 128
            or any(character in execution_no for character in "\r\n\x00")
        ):
            raise ValueError("broker_execution_no_invalid")
        execution_order_no = str(
            event_data.get("broker_execution_order_no") or ""
        ).strip()
        if (
            not execution_order_no
            or len(execution_order_no) > 128
            or any(character in execution_order_no for character in "\r\n\x00,")
        ):
            raise ValueError("broker_execution_order_no_invalid")
        if event_data.get("broker_execution_time_source") != "official_fid_908":
            raise ValueError("broker_execution_time_source_invalid")
        raw_execution_time = str(
            event_data.get("broker_execution_time_raw") or ""
        ).strip()
        try:
            if not re.fullmatch(r"\d{6}", raw_execution_time):
                raise ValueError
            datetime.strptime(raw_execution_time, "%H%M%S")
        except ValueError:
            raise ValueError("broker_execution_time_raw_invalid") from None
        if event_data.get("broker_actual_execution_venue") not in {"KRX", "NXT"}:
            raise ValueError("broker_actual_execution_venue_invalid")

    row: dict[str, Any] = {
        "schema": JOURNAL_SCHEMA,
        "trade_date": target_date,
        "observed_at": timestamp.isoformat(timespec="microseconds"),
        "main_lifecycle_id": main_lifecycle_id,
        **lineage,
        "stage": normalized_stage,
        "venue": str(venue or "UNKNOWN").strip().upper() or "UNKNOWN",
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
    "JOURNAL_SCHEMA",
    "MAX_TRANSITION_BYTES",
    "PIPELINE_IDENTITY_SCHEMA",
    "PIPELINE_STAGE_MAP",
    "VALID_FILL_STATES",
    "VALID_SCALE_IN_DECISIONS",
    "VALID_STAGES",
    "append_transition_safe",
    "build_transition",
    "journal_path",
    "lineage_payload",
    "mint_main_lifecycle_id",
    "pipeline_lifecycle_fields_safe",
    "start_scanner_attempt_safe",
    "transition_content_sha256",
    "validate_main_lifecycle_id",
]
