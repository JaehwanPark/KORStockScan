"""Historical read-only helpers; no active policy publisher or CLI.

Only existing forensic consumers retain these calculations. Live callers use
their native role owners and permanent retirement fences.
"""

from __future__ import annotations


from src.engine.lifecycle.retirement import RETIREMENT_ID, retired_status


from datetime import date, datetime, timedelta


from typing import Any, Iterable

STAGES = ("entry", "submit", "holding", "scale_in", "exit")


def _stage_for_prompt(prompt_profile: str, requested_stage: str | None = None) -> str:
    stage = str(requested_stage or "").strip().lower()
    if stage in STAGES:
        return stage
    profile = str(prompt_profile or "").strip().lower()
    if profile in {"holding", "scalping_holding"}:
        return "holding"
    if profile == "exit":
        return "exit"
    if profile in {"watching", "entry", "scalping_entry", "shared", ""}:
        return "entry"
    return "entry"


def build_lifecycle_ai_runtime_context(
    *,
    prompt_profile: str,
    stage: str | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    stage_name = _stage_for_prompt(prompt_profile, stage)
    return {
        "applied": False,
        "status": "retired",
        "cache_token": RETIREMENT_ID,
        "prompt_context": "",
        "fields": {
            "lifecycle_ai_context_enabled": False,
            "lifecycle_ai_context_applied": False,
            "lifecycle_ai_context_status": "retired",
            "lifecycle_ai_context_version": "-",
            "lifecycle_ai_context_source_date": "-",
            "lifecycle_ai_context_stage": stage_name,
            "lifecycle_ai_context_policy_key": "-",
            "lifecycle_ai_context_hash": "-",
            "lifecycle_ai_context_alignment_hint": "NO_CHANGE",
            "lifecycle_ai_context_decision_authority": "archive_only",
            "lifecycle_ai_context_runtime_effect": "none",
            "lifecycle_ai_context_actual_order_submitted": False,
            "lifecycle_ai_context_broker_order_forbidden": True,
        },
    }


def merge_lifecycle_ai_context_fields(
    result: dict[str, Any] | None,
    runtime_context: dict[str, Any] | None,
) -> dict[str, Any]:
    payload = dict(result or {})
    context = runtime_context or {}
    fields = dict(context.get("fields") or {})
    payload.update(fields)
    return payload
