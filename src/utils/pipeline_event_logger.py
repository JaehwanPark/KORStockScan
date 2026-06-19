"""Common pipeline-event logger for text logs and structured JSONL events."""

from __future__ import annotations

import json
import os
import threading
import atexit
import hashlib
from datetime import datetime
from pathlib import Path

from src.utils.constants import DATA_DIR, TRADING_RULES
from src.utils.logger import log_error, log_info
from src.utils.threshold_cycle_registry import threshold_family_for_stage
from src.engine.pipeline_event_summary import ProducerSummaryCompactor


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
    "microstructure_reaction_",
    "liquidity_guard_",
    "overbought_guard_",
)
_COMPACT_FIELD_LIMIT = 40


def _event_dir() -> Path:
    path = DATA_DIR / "pipeline_events"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _event_path(target_date: str) -> Path:
    return _event_dir() / f"pipeline_events_{target_date}.jsonl"


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
        str(getattr(TRADING_RULES, "PIPELINE_EVENT_HIGH_VOLUME_COMPACTION_MODE", "shadow") or "shadow"),
    )
    normalized = str(value).strip().lower()
    return normalized if normalized in {"off", "shadow", "suppress"} else "off"


def _compaction_flush_sec() -> int:
    value = os.getenv(
        "PIPELINE_EVENT_COMPACTION_FLUSH_SEC",
        str(getattr(TRADING_RULES, "PIPELINE_EVENT_COMPACTION_FLUSH_SEC", 5) or 5),
    )
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 5


def _compaction_sample_per_bucket() -> int:
    value = os.getenv(
        "PIPELINE_EVENT_COMPACTION_SAMPLE_PER_BUCKET",
        str(getattr(TRADING_RULES, "PIPELINE_EVENT_COMPACTION_SAMPLE_PER_BUCKET", 6) or 6),
    )
    try:
        return max(1, int(value))
    except (TypeError, ValueError):
        return 6


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
    return "sim_" in lowered_stage or "_probe_" in lowered_stage or lowered_stage.startswith("swing_probe_")


def _should_emit_text_info(stage: str, fields: dict | None) -> bool:
    if bool(getattr(TRADING_RULES, "PIPELINE_EVENT_TEXT_INFO_LOG_ENABLED", False)):
        return True

    safe_stage = str(stage or "").strip()
    raw_fields = fields or {}
    if _is_non_real_observation(safe_stage, raw_fields):
        return False

    allowlist = tuple(getattr(TRADING_RULES, "PIPELINE_EVENT_TEXT_INFO_STAGE_ALLOWLIST", ()) or ())
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


def _project_fields_for_compact_stream(stage: str, fields: dict[str, str]) -> dict[str, str]:
    if stage not in _SUBMIT_STAGE_COMPACT_STREAMS or len(fields) <= _COMPACT_FIELD_LIMIT:
        return fields

    selected: dict[str, str] = {}
    for key in _COMPACT_FIELD_PRIORITY:
        if key in fields:
            selected[key] = fields[key]
        if len(selected) >= _COMPACT_FIELD_LIMIT:
            break
    if len(selected) < _COMPACT_FIELD_LIMIT:
        for key in sorted(fields):
            if key in selected:
                continue
            if any(key.startswith(prefix) for prefix in _COMPACT_FIELD_PREFIXES):
                selected[key] = fields[key]
            if len(selected) >= _COMPACT_FIELD_LIMIT:
                break
    omitted_field_count = max(0, len(fields) - len(selected))
    if omitted_field_count <= 0:
        return fields
    selected = dict(selected)
    selected["field_projection"] = "submit_compact_v1"
    selected["full_field_count"] = str(len(fields))
    selected["omitted_field_count"] = str(omitted_field_count)
    selected["full_fields_hash"] = _fields_hash(fields)
    return selected


def _project_fields_for_text(stage: str, fields: dict[str, str]) -> dict[str, str]:
    if stage not in _SUBMIT_STAGE_COMPACT_STREAMS or len(fields) <= 18:
        return fields
    selected: dict[str, str] = {}
    if "id" in fields:
        selected["id"] = fields["id"]
    for key in _COMPACT_FIELD_PRIORITY:
        if key in fields:
            selected[key] = fields[key]
        if len(selected) >= 18:
            break
    return selected or fields


def _append_jsonl(path: Path, line: str) -> None:
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(line)


def emit_pipeline_event(
    pipeline: str,
    name: str,
    code: str,
    stage: str,
    *,
    record_id=None,
    fields: dict | None = None,
) -> dict:
    """Emit legacy text log + structured JSONL event with a shared schema."""
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
    parts = [f"{key}={sanitize_pipeline_field(value)}" for key, value in text_fields.items()]
    suffix = f" {' '.join(parts)}" if parts else ""
    text_payload = f"[{safe_pipeline}] {safe_name}({safe_code}) stage={safe_stage}{suffix}"
    if _should_emit_text_info(safe_stage, normalized_fields):
        log_info(text_payload)

    emitted_dt = datetime.now()
    event_payload = {
        "schema_version": int(getattr(TRADING_RULES, "PIPELINE_EVENT_SCHEMA_VERSION", 1) or 1),
        "event_type": "pipeline_event",
        "pipeline": safe_pipeline,
        "stage": safe_stage,
        "stock_name": safe_name,
        "stock_code": safe_code,
        "record_id": int(record_id) if record_id not in (None, "", 0) else None,
        "fields": normalized_fields,
        "emitted_at": emitted_dt.isoformat(),
        "emitted_date": emitted_dt.strftime("%Y-%m-%d"),
        "text_payload": text_payload,
    }

    if not bool(getattr(TRADING_RULES, "PIPELINE_EVENT_JSONL_ENABLED", True)):
        return event_payload

    threshold_family = threshold_family_for_stage(safe_stage, event_payload["fields"])
    raw_line = json.dumps(event_payload, ensure_ascii=False, separators=(",", ":"), default=str) + "\n"
    compact_line = None
    compact_fields = None
    if threshold_family:
        compact_fields = _project_fields_for_compact_stream(safe_stage, event_payload["fields"])
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
        compact_line = json.dumps(compact_payload, ensure_ascii=False, separators=(",", ":"), default=str) + "\n"

    compaction_result = {"suppress_raw": False}
    try:
        with _WRITE_LOCK:
            compactor = _get_producer_compactor()
            if compactor is not None:
                compaction_result = compactor.submit(event_payload, threshold_family=threshold_family)
            if not compaction_result.get("suppress_raw"):
                _append_jsonl(_event_path(event_payload["emitted_date"]), raw_line)
            if compact_line is not None:
                _append_jsonl(_threshold_cycle_event_path(event_payload["emitted_date"]), compact_line)
    except Exception as exc:
        log_error(f"[PIPELINE_EVENT] structured append failed: {exc}")

    return event_payload
