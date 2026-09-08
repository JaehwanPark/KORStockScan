"""Source-only Pattern Lab feedback receipts; no trading policy authority.

Shared by the offline payload producer and the postclose audit. This belongs
to automation contracts, not a new engine-root producer or tuning axis.
"""

import hashlib
import json
from datetime import date
from pathlib import Path

RECEIPT_SCHEMA = "pattern_lab_feedback_receipt_v1"


def read_feedback(path: Path | None, source_date: str | None, target_date: str):
    """Validate and summarize the same bytes whose hash is recorded."""
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "path": str(path) if path else None,
        "source_date": source_date,
        "target_date": target_date,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "validation_status": "invalid",
    }
    try:
        target = date.fromisoformat(target_date)
        source = date.fromisoformat(source_date or "")
        if source > target or (
            target_date >= "2026-06-05" and source_date < "2026-06-05"
        ):
            raise ValueError("source_date_outside_allowed_window")
        if path is None:
            raise ValueError("source_missing")
        content = path.read_bytes()
        payload = json.loads(content)
        if not isinstance(payload, dict) or not payload:
            raise ValueError("source_not_nonempty_object")
        payload_date = payload.get("date") or payload.get("target_date")
        if payload_date != source_date:
            raise ValueError("source_payload_date_mismatch")
        summary = payload.get("summary")
        summary = summary if isinstance(summary, dict) else {}
        status = payload.get("status") or summary.get("status")
        if str(status or "").lower() in {
            "fail",
            "failed",
            "error",
            "invalid",
            "running",
        }:
            raise ValueError("source_not_usable_terminal")
        receipt.update(
            validation_status="valid",
            sha256=hashlib.sha256(content).hexdigest(),
            status=status,
            warnings=payload.get("warnings") or summary.get("warnings") or [],
        )
    except (OSError, ValueError, TypeError, UnicodeError) as exc:
        receipt["reason"] = str(exc)
    return receipt
