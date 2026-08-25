"""Common pipeline-event logger for text logs and structured JSONL events."""

from __future__ import annotations

import atexit
import fcntl
import hashlib
import json
import os
import re
import stat
import threading
from datetime import date, datetime
from pathlib import Path

from src.utils.constants import DATA_DIR, TRADING_RULES
from src.utils.logger import log_error, log_info
from src.utils.threshold_cycle_registry import threshold_family_for_stage
from src.engine.pipeline_event_summary import (
    HIGH_VOLUME_OBSERVATION_STAGES,
    HIGH_VOLUME_SUMMARY_FIELD_PRIORITY,
    ProducerSummaryCompactor,
)

_WRITE_LOCK = threading.RLock()
_PRODUCER_COMPACTOR: ProducerSummaryCompactor | None = None

_TEXT_INFO_STAGE_KEYWORDS = (
    "order_submitted",
    "order_bundle_submitted",
    "order_sent",
    "order_cancel",
    "order_failed",
    "order_rejected",
    "sell_order",
    "hard_stop",
    "protect",
    "emergency",
)

_SUBMIT_STAGE_COMPACT_STREAMS = frozenset(
    {
        "latency_pass",
        "entry_submit_revalidation_warning",
        "entry_submit_revalidation_block",
        "pre_submit_liquidity_guard_block",
        "pre_submit_overbought_pullback_guard_block",
        "pre_submit_price_guard_block",
        "order_leg_request",
        "order_leg_sent",
        "order_bundle_failed",
        "order_bundle_submitted",
        "swing_sim_order_bundle_assumed_filled",
    }
)
_TEXT_COMPACT_STAGES = _SUBMIT_STAGE_COMPACT_STREAMS | HIGH_VOLUME_OBSERVATION_STAGES
_COMPACT_FIELD_PRIORITY = (
    "threshold_family",
    "actual_order_submitted",
    "broker_order_forbidden",
    "runtime_effect",
    "decision_authority",
    "entry_mode",
    "requested_qty",
    "legs",
    "tag",
    "qty",
    "price",
    "ord_no",
    "reason",
    "block_reason",
    "latency",
    "latency_state",
    "policy_decision",
    "policy_reason",
    "effective_decision",
    "effective_reason",
    "entry_price_guard",
    "entry_price_defensive_ticks",
    "entry_price_gap_profile",
    "entry_price_gap_profile_bps",
    "entry_price_gap_profile_reason",
    "entry_price_gap_profile_context",
    "aggressive_entry_price_override_applied",
    "aggressive_entry_price_override_type",
    "aggressive_entry_price_override_reason",
    "aggressive_entry_price_override_skip_reason",
    "aggressive_entry_price_original_profile",
    "aggressive_entry_price_original_bps",
    "aggressive_entry_price_target_mode",
    "aggressive_entry_price_order_price",
    "conditional_1tick_real_override_applied",
    "conditional_1tick_real_override_reason",
    "conditional_1tick_real_override_context",
    "order_price",
    "submitted_order_price",
    "best_bid_at_submit",
    "best_ask_at_submit",
    "price_below_bid_bps",
    "quote_stale",
    "quote_age_at_submit_ms",
    "price_decision_context_age_ms",
    "market_data_signed_tape_state",
    "market_data_signed_tape_sample_count",
    "market_data_rest_signed_tape_pressure_usable",
    "rest_signed_trade_ticks",
    "latency_true_ofi_direct_canary_signed_tape_sample_count",
    "latency_true_ofi_direct_canary_signed_tape_sell_dominated",
    "latency_true_ofi_direct_canary_signed_tape_net_buy_volume",
    "latency_true_ofi_direct_canary_tape_block_reason",
    "entry_order_lifecycle",
    "entry_passive_probe_applied",
    "entry_submit_revalidation_warning",
    "entry_submit_revalidation_block",
    "liquidity_guard_action",
    "overbought_guard_action",
    "microstructure_reaction_context_version",
    "microstructure_reaction_context_status",
    "microstructure_reaction_entry_reaction_quality",
    "microstructure_reaction_source_quality",
    "microstructure_reaction_context_hash",
    "simulation_owner",
    "would_submit_stage",
)
_COMPACT_FIELD_PREFIXES = (
    "ka10046_strength_",
    "ka10003_buy_dominance_observation_",
    "latency_true_ofi_direct_canary_signed_tape_",
    "latency_true_ofi_direct_canary_tape_",
    "market_data_signed_tape_",
    "market_data_rest_signed_tape_",
    "microstructure_reaction_",
    "rest_signed_trade_ticks",
    "v_pw_",
    "liquidity_guard_",
    "overbought_guard_",
)
_COMPACT_FIELD_LIMIT = 40
_HIGH_VOLUME_COMPACT_FIELD_PRIORITY = HIGH_VOLUME_SUMMARY_FIELD_PRIORITY + (
    "threshold_family",
    "forbidden_uses",
    "source_stage",
    "selector_reason",
    "selector_deferred",
    "market_session_bucket",
    "rising_missed_market_session_bucket",
    "rising_missed_tp1_evaluation_id",
    "rising_missed_tp1_selector_active",
    "rising_missed_tp1_candidate_allowed",
    "rising_missed_tp1_candidate_deferred",
    "rising_missed_tp1_candidate_lane",
    "rising_missed_tp1_candidate_reason",
    "rising_missed_tp1_counterfactual_submit_safety_action",
    "rising_missed_tp1_counterfactual_submit_safety_risks",
    "rising_missed_tp1_input_ready",
    "rising_missed_tp1_input_reason",
    "rising_missed_tp1_effective_price",
    "rising_missed_tp1_effective_quote_age_ms",
    "rising_missed_tp1_actual_watch_delta_pct",
    "rising_missed_tp1_low_rebound_pct",
    "rising_missed_tp1_positive_support_count",
    "rising_missed_tp1_positive_support_families",
    "rising_missed_tp1_hard_negative_reasons",
    "rising_missed_tp1_micro_source_state",
    "rising_missed_tp1_micro_confidence",
    "rising_missed_tp1_true_ofi_ewma",
    "rising_missed_tp1_pressure_ewma",
    "rising_missed_tp1_depth_imbalance_ewma",
    "rising_missed_tp1_top_depth_ratio",
    "rising_missed_tp1_tick_acceleration",
    "rising_missed_tp1_tick_acceleration_fresh",
    "rising_missed_tp1_ws_fast_tape_sample_count",
    "rising_missed_tp1_ws_fast_tape_buy_ratio",
    "rising_missed_tp1_ws_fast_tape_fresh",
    "rising_missed_tp1_ws_0b_trade_fresh",
    "rising_missed_tp1_ws_0d_depth_fresh",
    "market_data_freshness_state",
    "market_data_orderbook_state",
    "market_data_tick_context_state",
    "market_data_effective_price_source",
    "market_data_effective_best_bid",
    "market_data_effective_best_ask",
    "market_data_effective_quote_age_ms",
    "market_data_signed_tape_state",
    "market_data_signed_tape_sample_count",
    "market_data_rest_signed_tape_pressure_usable",
)
_HIGH_VOLUME_COMPACT_FIELD_LIMIT = 96
_MAIN_LIFECYCLE_IDENTITY_SCHEMA = "main_scalping_lifecycle_pipeline_identity_v1"


def _event_dir() -> Path:
    path = DATA_DIR / "pipeline_events"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _event_path(target_date: str) -> Path:
    return _event_dir() / f"pipeline_events_{target_date}.jsonl"


def _event_storage_partition_date(fields: dict[str, str], *, emitted_date: str) -> str:
    """Route exact lifecycle rows by their official logical trade date.

    Packet ingress can cross midnight after a FID 908 execution.  Only an
    explicit lifecycle identity may move by one adjacent calendar day; all
    other events retain the wall-clock emission partition.
    """

    if (
        fields.get("main_lifecycle_identity_schema") != _MAIN_LIFECYCLE_IDENTITY_SCHEMA
        or re.fullmatch(r"mlc-[0-9a-f]{32}", fields.get("main_lifecycle_id") or "")
        is None
        or fields.get("main_lifecycle_decision_authority")
        != "source_only_lifecycle_observation"
        or fields.get("main_lifecycle_runtime_effect") != "False"
        or fields.get("main_lifecycle_order_authority") != "False"
        or fields.get("main_lifecycle_provider_authority") != "False"
    ):
        return emitted_date
    candidate = str(fields.get("main_lifecycle_trade_date") or "").strip()
    try:
        emitted_day = date.fromisoformat(emitted_date)
        candidate_day = date.fromisoformat(candidate)
    except ValueError:
        return emitted_date
    if abs((candidate_day - emitted_day).days) > 1:
        return emitted_date
    return candidate_day.isoformat()


def _summary_dir() -> Path:
    path = DATA_DIR / "pipeline_event_summaries"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _threshold_cycle_dir() -> Path:
    path = DATA_DIR / "threshold_cycle"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _threshold_cycle_event_path(target_date: str) -> Path:
    return _threshold_cycle_dir() / f"threshold_events_{target_date}.jsonl"


def _compaction_mode() -> str:
    value = os.getenv(
        "PIPELINE_EVENT_HIGH_VOLUME_COMPACTION_MODE",
        str(
            getattr(
                TRADING_RULES, "PIPELINE_EVENT_HIGH_VOLUME_COMPACTION_MODE", "shadow"
            )
            or "shadow"
        ),
    )
    normalized = str(value).strip().lower()
    return normalized if normalized in {"off", "shadow", "suppress"} else "off"


def _compaction_flush_sec() -> int:
    value = os.getenv(
        "PIPELINE_EVENT_COMPACTION_FLUSH_SEC",
        str(getattr(TRADING_RULES, "PIPELINE_EVENT_COMPACTION_FLUSH_SEC", 60) or 60),
    )
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 60


def _compaction_sample_per_bucket() -> int:
    value = os.getenv(
        "PIPELINE_EVENT_COMPACTION_SAMPLE_PER_BUCKET",
        str(
            getattr(TRADING_RULES, "PIPELINE_EVENT_COMPACTION_SAMPLE_PER_BUCKET", 2)
            or 2
        ),
    )
    try:
        return max(1, int(value))
    except (TypeError, ValueError):
        return 2


def _get_producer_compactor() -> ProducerSummaryCompactor | None:
    global _PRODUCER_COMPACTOR
    mode = _compaction_mode()
    if mode == "off":
        return None
    if _PRODUCER_COMPACTOR is None or _PRODUCER_COMPACTOR.mode != mode:
        _PRODUCER_COMPACTOR = ProducerSummaryCompactor(
            summary_dir=_summary_dir(),
            mode=mode,
            flush_sec=_compaction_flush_sec(),
            sample_per_bucket=_compaction_sample_per_bucket(),
        )
    return _PRODUCER_COMPACTOR


def flush_pipeline_event_producer_summary(target_date: str | None = None) -> dict:
    if _PRODUCER_COMPACTOR is None:
        return {"enabled": False, "status": "disabled", "flushed_rows": 0}
    return _PRODUCER_COMPACTOR.flush(target_date=target_date)


def _flush_producer_summary_at_exit() -> None:
    try:
        flush_pipeline_event_producer_summary()
    except Exception as exc:
        log_error(f"[PIPELINE_EVENT] producer summary atexit flush failed: {exc}")


atexit.register(_flush_producer_summary_at_exit)


def sanitize_pipeline_field(value) -> str:
    return str(value).replace(" ", "|")


def _truthy(value) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _falsey(value) -> bool:
    return str(value).strip().lower() in {"0", "false", "no", "n", "off"}


def _is_non_real_observation(stage: str, fields: dict | None) -> bool:
    raw_fields = fields or {}
    lowered_stage = str(stage or "").strip().lower()
    if _falsey(raw_fields.get("actual_order_submitted")):
        return True
    if _truthy(raw_fields.get("broker_order_forbidden")):
        return True
    if _truthy(raw_fields.get("simulated_order")):
        return True
    if raw_fields.get("simulation_book") or raw_fields.get("simulation_owner"):
        return True
    if _truthy(raw_fields.get("swing_intraday_probe")):
        return True
    if raw_fields.get("probe_id") or raw_fields.get("probe_origin_stage"):
        return True
    return (
        "sim_" in lowered_stage
        or "_probe_" in lowered_stage
        or lowered_stage.startswith("swing_probe_")
    )


def _should_emit_text_info(stage: str, fields: dict | None) -> bool:
    if bool(getattr(TRADING_RULES, "PIPELINE_EVENT_TEXT_INFO_LOG_ENABLED", False)):
        return True

    safe_stage = str(stage or "").strip()
    raw_fields = fields or {}
    if _is_non_real_observation(safe_stage, raw_fields):
        return False

    allowlist = tuple(
        getattr(TRADING_RULES, "PIPELINE_EVENT_TEXT_INFO_STAGE_ALLOWLIST", ()) or ()
    )
    if safe_stage in allowlist:
        return True

    lowered_stage = safe_stage.lower()
    if any(keyword in lowered_stage for keyword in _TEXT_INFO_STAGE_KEYWORDS):
        return True

    if _truthy(raw_fields.get("actual_order_submitted")):
        return True
    if _truthy(raw_fields.get("broker_order_submitted")):
        return True

    return False


def _fields_hash(fields: dict[str, str]) -> str:
    raw = json.dumps(fields, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _project_fields_for_compact_stream(
    stage: str, fields: dict[str, str]
) -> dict[str, str]:
    high_volume = stage in HIGH_VOLUME_OBSERVATION_STAGES
    submit_stage = stage in _SUBMIT_STAGE_COMPACT_STREAMS
    if not high_volume and not submit_stage:
        return fields

    field_limit = (
        _HIGH_VOLUME_COMPACT_FIELD_LIMIT if high_volume else _COMPACT_FIELD_LIMIT
    )
    if len(fields) <= field_limit:
        return fields
    field_priority = (
        _HIGH_VOLUME_COMPACT_FIELD_PRIORITY if high_volume else _COMPACT_FIELD_PRIORITY
    )

    selected: dict[str, str] = {}
    for key in field_priority:
        if key in fields:
            selected[key] = fields[key]
        if len(selected) >= field_limit:
            break
    if len(selected) < field_limit:
        for key in sorted(fields):
            if key in selected:
                continue
            if any(key.startswith(prefix) for prefix in _COMPACT_FIELD_PREFIXES):
                selected[key] = fields[key]
            if len(selected) >= field_limit:
                break
    omitted_field_count = max(0, len(fields) - len(selected))
    if omitted_field_count <= 0:
        return fields
    selected = dict(selected)
    selected["field_projection"] = (
        "high_volume_compact_v1" if high_volume else "submit_compact_v1"
    )
    selected["full_field_count"] = str(len(fields))
    selected["omitted_field_count"] = str(omitted_field_count)
    selected["full_fields_hash"] = _fields_hash(fields)
    return selected


def _project_fields_for_text(stage: str, fields: dict[str, str]) -> dict[str, str]:
    if stage not in _TEXT_COMPACT_STAGES or len(fields) <= 18:
        return fields
    selected: dict[str, str] = {}
    if "id" in fields:
        selected["id"] = fields["id"]
    for key in _COMPACT_FIELD_PRIORITY:
        if key in fields:
            selected[key] = fields[key]
        if len(selected) >= 18:
            break
    if not selected:
        return fields
    omitted_field_count = max(0, len(fields) - len(selected))
    if omitted_field_count <= 0:
        return fields
    selected = dict(selected)
    selected["text_field_projection"] = "diagnostic_compact_v1"
    selected["full_field_count"] = str(len(fields))
    selected["omitted_field_count"] = str(omitted_field_count)
    return selected


def _late_pipeline_event_path(path: Path) -> Path:
    if path.suffix != ".jsonl":
        raise ValueError("pipeline event logical path must end in .jsonl")
    return path.with_name(f"{path.stem}.late.jsonl")


def _pipeline_event_partition_lock_path(path: Path) -> Path:
    return path.with_name(f".{path.name}.partition.lock")


def _prepare_jsonl_parent(path: Path) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        parent_metadata = path.parent.lstat()
    except OSError as exc:
        raise OSError(f"pipeline event parent is unavailable: {path.parent}") from exc
    if not stat.S_ISDIR(parent_metadata.st_mode):
        raise OSError(f"pipeline event parent is not a real directory: {path.parent}")
    directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    directory_flags |= getattr(os, "O_CLOEXEC", 0)
    directory_flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path.parent, directory_flags)
    opened_metadata = os.fstat(descriptor)
    if not stat.S_ISDIR(opened_metadata.st_mode) or (
        opened_metadata.st_dev,
        opened_metadata.st_ino,
    ) != (parent_metadata.st_dev, parent_metadata.st_ino):
        os.close(descriptor)
        raise OSError(f"pipeline event parent changed before open: {path.parent}")
    return descriptor


def _write_all(descriptor: int, payload: bytes, *, target: Path) -> None:
    offset = 0
    while offset < len(payload):
        written = os.write(descriptor, payload[offset:])
        if written <= 0:
            raise OSError(f"pipeline event append made no progress: {target}")
        offset += written


def _fsync_parent_directory(directory_descriptor: int, *, target: Path) -> None:
    if not stat.S_ISDIR(os.fstat(directory_descriptor).st_mode):
        raise OSError(f"pipeline event parent is not a directory: {target.parent}")
    os.fsync(directory_descriptor)


def _append_partition_jsonl(
    logical_path: Path,
    physical_path: Path,
    line: str,
    *,
    durable_every_append: bool,
) -> None:
    """Append one row under the logical partition lock.

    Base and late physical parts share this exact exclusive lock namespace.
    The no-follow regular-file checks keep a replaced path from redirecting
    event custody, while the complete write closes short-write gaps.  The
    high-volume base/threshold path fsyncs only its first physical-file row;
    exact-lifecycle late sidecars retain per-append durable custody.
    """

    payload = line.encode("utf-8")
    if physical_path.parent != logical_path.parent:
        raise ValueError("pipeline event physical part must share logical parent")
    parent_descriptor = _prepare_jsonl_parent(logical_path)
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    close_on_exec = getattr(os, "O_CLOEXEC", 0)
    nonblocking = getattr(os, "O_NONBLOCK", 0)
    try:
        lock_descriptor = os.open(
            _pipeline_event_partition_lock_path(logical_path).name,
            os.O_RDWR | os.O_CREAT | nofollow | close_on_exec | nonblocking,
            0o640,
            dir_fd=parent_descriptor,
        )
        try:
            if not stat.S_ISREG(os.fstat(lock_descriptor).st_mode):
                raise OSError("pipeline event partition lock is not a regular file")
            # The logical path-level lock closes discovery/open races with readers
            # and the storage compactor for both the base and late physical parts.
            fcntl.flock(lock_descriptor, fcntl.LOCK_EX)
            append_flags = (
                os.O_WRONLY | os.O_APPEND | nofollow | close_on_exec | nonblocking
            )
            created = False
            try:
                descriptor = os.open(
                    physical_path.name,
                    append_flags | os.O_CREAT | os.O_EXCL,
                    0o640,
                    dir_fd=parent_descriptor,
                )
                created = True
            except FileExistsError:
                descriptor = os.open(
                    physical_path.name,
                    append_flags,
                    dir_fd=parent_descriptor,
                )
            try:
                metadata = os.fstat(descriptor)
                if not stat.S_ISREG(metadata.st_mode):
                    raise OSError("pipeline event physical part is not a regular file")
                fcntl.flock(descriptor, fcntl.LOCK_EX)
                _write_all(descriptor, payload, target=physical_path)
                if created or durable_every_append:
                    os.fsync(descriptor)
                    _fsync_parent_directory(parent_descriptor, target=physical_path)
            finally:
                try:
                    fcntl.flock(descriptor, fcntl.LOCK_UN)
                finally:
                    os.close(descriptor)
        finally:
            try:
                fcntl.flock(lock_descriptor, fcntl.LOCK_UN)
            finally:
                os.close(lock_descriptor)
    finally:
        os.close(parent_descriptor)


def _append_jsonl(path: Path, line: str) -> None:
    _append_partition_jsonl(
        path,
        path,
        line,
        durable_every_append=False,
    )


def _append_late_pipeline_event_jsonl(path: Path, line: str) -> None:
    """Append a cross-midnight row without mutating a verified base archive.

    The late sidecar is a separate append-only physical part of the logical
    trade-date partition. ``main_lifecycle_paired`` consumes the immutable base
    first and this late part second under the shared logical partition lock.
    """

    _append_partition_jsonl(
        path,
        _late_pipeline_event_path(path),
        line,
        durable_every_append=True,
    )


def _append_pipeline_event_jsonl(
    path: Path,
    line: str,
    *,
    late_partition: bool,
) -> None:
    if late_partition:
        _append_late_pipeline_event_jsonl(path, line)
        return
    _append_jsonl(path, line)


def emit_pipeline_event(
    pipeline: str,
    name: str,
    code: str,
    stage: str,
    *,
    record_id=None,
    fields: dict | None = None,
) -> dict:
    """Emit legacy text plus a structured event and return persistence outcome.

    ``structured_append_succeeded`` means the lossless raw JSONL row reached
    its physical append boundary.  JSONL-disabled and compaction-suppressed
    calls return distinct non-success statuses; call-local outcome fields are
    not embedded back into the canonical event row.
    """
    safe_pipeline = str(pipeline or "").strip() or "PIPELINE"
    safe_name = str(name or "").strip() or "-"
    safe_code = str(code or "").strip()[:6] or "-"
    safe_stage = str(stage or "").strip() or "-"

    normalized_fields = {str(key): str(value) for key, value in (fields or {}).items()}
    merged_fields = {}
    if record_id not in (None, "", 0):
        merged_fields["id"] = record_id
    merged_fields.update(normalized_fields)

    text_fields = _project_fields_for_text(safe_stage, merged_fields)
    parts = [
        f"{key}={sanitize_pipeline_field(value)}" for key, value in text_fields.items()
    ]
    suffix = f" {' '.join(parts)}" if parts else ""
    text_payload = (
        f"[{safe_pipeline}] {safe_name}({safe_code}) stage={safe_stage}{suffix}"
    )
    if _should_emit_text_info(safe_stage, normalized_fields):
        log_info(text_payload)

    emitted_dt = datetime.now()
    emitted_date = emitted_dt.strftime("%Y-%m-%d")
    storage_partition_date = _event_storage_partition_date(
        normalized_fields,
        emitted_date=emitted_date,
    )
    event_payload = {
        "schema_version": int(
            getattr(TRADING_RULES, "PIPELINE_EVENT_SCHEMA_VERSION", 1) or 1
        ),
        "event_type": "pipeline_event",
        "pipeline": safe_pipeline,
        "stage": safe_stage,
        "stock_name": safe_name,
        "stock_code": safe_code,
        "record_id": int(record_id) if record_id not in (None, "", 0) else None,
        "fields": normalized_fields,
        "emitted_at": emitted_dt.isoformat(),
        "emitted_date": emitted_date,
        "storage_partition_date": storage_partition_date,
        "text_payload": text_payload,
    }

    if not bool(getattr(TRADING_RULES, "PIPELINE_EVENT_JSONL_ENABLED", True)):
        event_payload.update(
            {
                "structured_append_attempted": False,
                "structured_append_succeeded": False,
                "structured_raw_append_attempted": False,
                "structured_compaction_suppressed": False,
                "structured_compact_append_succeeded": None,
                "structured_append_status": "jsonl_disabled",
                "structured_append_error_type": None,
            }
        )
        return event_payload

    threshold_family = threshold_family_for_stage(safe_stage, event_payload["fields"])
    raw_line = (
        json.dumps(
            event_payload, ensure_ascii=False, separators=(",", ":"), default=str
        )
        + "\n"
    )
    compact_line = None
    compact_fields = None
    if threshold_family:
        compact_fields = _project_fields_for_compact_stream(
            safe_stage, event_payload["fields"]
        )
        compact_payload = {
            "schema_version": 1,
            "event_type": "threshold_cycle_event",
            "family": threshold_family,
            "pipeline": safe_pipeline,
            "stage": safe_stage,
            "stock_name": safe_name,
            "stock_code": safe_code,
            "record_id": int(record_id) if record_id not in (None, "", 0) else None,
            "fields": compact_fields,
            "emitted_at": event_payload["emitted_at"],
            "emitted_date": event_payload["emitted_date"],
        }
        compact_line = (
            json.dumps(
                compact_payload, ensure_ascii=False, separators=(",", ":"), default=str
            )
            + "\n"
        )

    compaction_result = {"suppress_raw": False}
    raw_append_attempted = False
    raw_append_succeeded = False
    compact_append_attempted = False
    compact_append_succeeded = compact_line is None
    compaction_suppressed = False
    append_error: Exception | None = None
    try:
        with _WRITE_LOCK:
            compactor = _get_producer_compactor()
            if compactor is not None:
                compaction_result = compactor.submit(
                    event_payload, threshold_family=threshold_family
                )
            compaction_suppressed = bool(compaction_result.get("suppress_raw"))
            if not compaction_suppressed:
                raw_append_attempted = True
                _append_pipeline_event_jsonl(
                    _event_path(storage_partition_date),
                    raw_line,
                    late_partition=storage_partition_date != emitted_date,
                )
                raw_append_succeeded = True
            if compact_line is not None:
                compact_append_attempted = True
                _append_jsonl(
                    _threshold_cycle_event_path(event_payload["emitted_date"]),
                    compact_line,
                )
                compact_append_succeeded = True
    except Exception as exc:
        append_error = exc
        log_error(f"[PIPELINE_EVENT] structured append failed: {exc}")

    if raw_append_succeeded:
        append_status = (
            "raw_appended" if append_error is None else "raw_appended_companion_failed"
        )
    elif compaction_suppressed:
        append_status = (
            "raw_suppressed_by_compaction"
            if append_error is None
            else "raw_suppressed_companion_failed"
        )
    elif raw_append_attempted:
        append_status = "raw_append_failed"
    else:
        append_status = "structured_append_failed"
    event_payload.update(
        {
            "structured_append_attempted": True,
            "structured_append_succeeded": raw_append_succeeded,
            "structured_raw_append_attempted": raw_append_attempted,
            "structured_compaction_suppressed": compaction_suppressed,
            "structured_compact_append_succeeded": (
                compact_append_succeeded if compact_append_attempted else None
            ),
            "structured_append_status": append_status,
            "structured_append_error_type": (
                type(append_error).__name__ if append_error is not None else None
            ),
        }
    )

    return event_payload
