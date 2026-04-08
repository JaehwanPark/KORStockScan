"""Common pipeline-event logger for text logs and structured JSONL events."""

from __future__ import annotations

import json
import threading
from datetime import datetime
from pathlib import Path

from src.utils.constants import DATA_DIR, TRADING_RULES
from src.utils.logger import log_error, log_info


_WRITE_LOCK = threading.RLock()


def _event_dir() -> Path:
    path = DATA_DIR / "pipeline_events"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _event_path(target_date: str) -> Path:
    return _event_dir() / f"pipeline_events_{target_date}.jsonl"


def sanitize_pipeline_field(value) -> str:
    return str(value).replace(" ", "|")


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

    merged_fields = {}
    if record_id not in (None, "", 0):
        merged_fields["id"] = record_id
    merged_fields.update(fields or {})

    parts = [f"{key}={sanitize_pipeline_field(value)}" for key, value in merged_fields.items()]
    suffix = f" {' '.join(parts)}" if parts else ""
    text_payload = f"[{safe_pipeline}] {safe_name}({safe_code}) stage={safe_stage}{suffix}"
    log_info(text_payload)

    event_payload = {
        "schema_version": int(getattr(TRADING_RULES, "PIPELINE_EVENT_SCHEMA_VERSION", 1) or 1),
        "event_type": "pipeline_event",
        "pipeline": safe_pipeline,
        "stage": safe_stage,
        "stock_name": safe_name,
        "stock_code": safe_code,
        "record_id": int(record_id) if record_id not in (None, "", 0) else None,
        "fields": {str(key): str(value) for key, value in (fields or {}).items()},
        "emitted_at": datetime.now().isoformat(),
        "emitted_date": datetime.now().strftime("%Y-%m-%d"),
        "text_payload": text_payload,
    }

    if not bool(getattr(TRADING_RULES, "PIPELINE_EVENT_JSONL_ENABLED", True)):
        return event_payload

    try:
        with _WRITE_LOCK:
            path = _event_path(event_payload["emitted_date"])
            with open(path, "a", encoding="utf-8") as handle:
                handle.write(json.dumps(event_payload, ensure_ascii=False) + "\n")
    except Exception as exc:
        log_error(f"[PIPELINE_EVENT] structured append failed: {exc}")

    return event_payload
