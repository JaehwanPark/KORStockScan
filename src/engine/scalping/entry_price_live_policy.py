"""Select the reviewed entry-price V2.5 prompt for KRX regular only.

This module owns prompt selection, not order submission.  It requires an
operator date gate and an immutable successful replay report.  Every missing or
conflicting fact falls back to the existing entry_price_v1 owner.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from src.engine.ai_prompt_contracts import (
    DECISION_QUALITY_ENTRY_PRICE_V2_5_LIVE_KRX_PROMPT_VERSION,
    DECISION_QUALITY_ENTRY_PRICE_V2_5_PROMPT_VERSION,
)

KST = ZoneInfo("Asia/Seoul")
CONTROL_PROMPT_VERSION = "entry_price_v1"
TARGET_VENUE = "KRX"
TARGET_SESSION = "KRX_REGULAR"
ENABLED_ENV = "KORSTOCKSCAN_ENTRY_PRICE_V2_5_KRX_ENABLED"
ACTIVE_DATE_ENV = "KORSTOCKSCAN_ENTRY_PRICE_V2_5_KRX_ACTIVE_DATE"
EVIDENCE_PATH_ENV = "KORSTOCKSCAN_ENTRY_PRICE_V2_5_KRX_EVIDENCE_PATH"
EVIDENCE_SHA256_ENV = "KORSTOCKSCAN_ENTRY_PRICE_V2_5_KRX_EVIDENCE_SHA256"
EXPECTED_REPORT_SCHEMA = "ai_prompt_stage_coverage_replay_v1"
EXPECTED_REPORT_STATUS = "coverage_replay_complete_candidate_quality_pass_offline_only"
EXPECTED_SEMANTIC_VALIDATOR = "entry_price_explicit_fill_value_semantic_v6"
_EVIDENCE_CACHE: dict[tuple[str, int, int, str], tuple[str | None, list[str]]] = {}


def _enabled(value: Any) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _file_sha256(path: Path) -> str | None:
    try:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return None


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _number(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _integer(value: Any) -> int | None:
    number = _number(value)
    if number is None or not float(number).is_integer():
        return None
    return int(number)


def _evidence_errors(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("schema") != EXPECTED_REPORT_SCHEMA:
        errors.append("evidence_schema_invalid")
    if report.get("status") != EXPECTED_REPORT_STATUS:
        errors.append("evidence_status_not_passed")
    if report.get("stage") != "entry_price":
        errors.append("evidence_stage_mismatch")
    if report.get("candidate_prompt_versions") != [
        DECISION_QUALITY_ENTRY_PRICE_V2_5_PROMPT_VERSION
    ]:
        errors.append("evidence_candidate_prompt_mismatch")
    if report.get("candidate_semantic_validator_versions") != [
        EXPECTED_SEMANTIC_VALIDATOR
    ]:
        errors.append("evidence_semantic_validator_mismatch")
    cohort = report.get("cohort_filter")
    cohort = cohort if isinstance(cohort, dict) else {}
    if str(cohort.get("effective_venue") or "").strip().upper() != TARGET_VENUE:
        errors.append("evidence_venue_mismatch")
    if str(cohort.get("session_bucket") or "").strip().upper() != TARGET_SESSION:
        errors.append("evidence_session_mismatch")
    request_count = _integer(report.get("request_count"))
    pass_count = _integer(report.get("pass_count"))
    if request_count is None or request_count <= 0 or request_count != pass_count:
        errors.append("evidence_result_incomplete")
    if _integer(report.get("provider_failed_count")) != 0:
        errors.append("evidence_provider_failure")
    if _integer(report.get("schema_rejected_count")) != 0:
        errors.append("evidence_schema_rejection")
    sample_floor = report.get("coverage_sample_floor")
    sample_floor = sample_floor if isinstance(sample_floor, dict) else {}
    required_rows = _integer(sample_floor.get("required_decision_rows"))
    required_symbols = _integer(sample_floor.get("required_unique_symbols"))
    observed_rows = _integer(sample_floor.get("observed_decision_rows"))
    observed_symbols = _integer(sample_floor.get("observed_unique_symbols"))
    if (
        sample_floor.get("pass") is not True
        or required_rows is None
        or required_rows <= 0
        or required_symbols is None
        or required_symbols <= 0
        or observed_rows is None
        or observed_rows < required_rows
        or observed_symbols is None
        or observed_symbols < required_symbols
    ):
        errors.append("evidence_sample_floor_not_passed")
    if report.get("entry_price_selection_complete") is not True:
        errors.append("evidence_price_selection_incomplete")
    if report.get("entry_price_effect_not_collapsed") is not True:
        errors.append("evidence_price_effect_collapsed")
    selection = report.get("entry_price_selection_outcome_comparison")
    selection = selection if isinstance(selection, dict) else {}
    if selection.get("quality_gate_pass") is not True:
        errors.append("evidence_selection_quality_not_passed")
    outcome = report.get("outcome_comparison")
    outcome = outcome if isinstance(outcome, dict) else {}
    ev_delta = _number(outcome.get("source_quality_adjusted_ev_delta_pct"))
    if ev_delta is None or ev_delta <= 0:
        errors.append("evidence_ev_delta_not_positive")
    if _integer(outcome.get("new_missed_upside_count")) != 0:
        errors.append("evidence_new_missed_upside")
    candidate_tail = _integer(outcome.get("candidate_probe_severe_tail_exposure_count"))
    control_tail = _integer(outcome.get("control_probe_severe_tail_exposure_count"))
    if candidate_tail is None or control_tail is None or candidate_tail > control_tail:
        errors.append("evidence_severe_tail_increased")
    if (
        report.get("runtime_effect") is not False
        or report.get("allowed_runtime_apply") is not False
        or report.get("actual_order_submitted") is not False
        or report.get("broker_order_forbidden") is not True
    ):
        errors.append("evidence_offline_authority_invalid")
    return list(dict.fromkeys(errors))


def _snapshot(candle_context: Any) -> dict[str, Any]:
    context = candle_context if isinstance(candle_context, dict) else {}
    value = context.get("ai_market_snapshot_v1")
    return value if isinstance(value, dict) else {}


def _validated_evidence(
    path: Path, configured_sha: str
) -> tuple[str | None, list[str]]:
    try:
        stat = path.stat()
    except OSError:
        return None, ["evidence_report_missing"]
    key = (str(path), stat.st_mtime_ns, stat.st_size, configured_sha)
    cached = _EVIDENCE_CACHE.get(key)
    if cached is not None:
        return cached
    actual_sha = _file_sha256(path)
    errors = (
        ["evidence_report_hash_mismatch"]
        if not configured_sha or configured_sha != actual_sha
        else _evidence_errors(_read_json(path))
    )
    result = (actual_sha, errors)
    _EVIDENCE_CACHE.clear()
    _EVIDENCE_CACHE[key] = result
    return result


def resolve_entry_price_live_policy(
    candle_context: Any,
    *,
    env: dict[str, str] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Return V2.5 only for a verified, date-scoped KRX regular snapshot."""

    source_env = os.environ if env is None else env
    current = now.astimezone(KST) if now is not None else datetime.now(KST)
    snapshot = _snapshot(candle_context)
    venue = str(snapshot.get("effective_venue") or "").strip().upper()
    session = str(snapshot.get("session_bucket") or "").strip().upper()
    preflight = snapshot.get("ai_input_preflight_v1")
    preflight = preflight if isinstance(preflight, dict) else {}
    result = {
        "status": "control_v1",
        "selected_prompt_version": CONTROL_PROMPT_VERSION,
        "rollback_prompt_version": CONTROL_PROMPT_VERSION,
        "effective_venue": venue or None,
        "session_bucket": session or None,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "blocking_reasons": [],
    }
    blockers: list[str] = []
    if not _enabled(source_env.get(ENABLED_ENV)):
        blockers.append("operator_enable_missing")
    active_date = str(source_env.get(ACTIVE_DATE_ENV) or "").strip()
    if active_date != current.date().isoformat():
        blockers.append("active_date_mismatch")
    if venue != TARGET_VENUE:
        blockers.append("effective_venue_not_krx")
    if session != TARGET_SESSION:
        blockers.append("session_not_krx_regular")
    if preflight.get("allowed") is not True:
        blockers.append("exact_input_preflight_not_allowed")
    if preflight.get("venue_consistent") is False or preflight.get("blockers"):
        blockers.append("exact_input_source_or_route_blocked")
    if blockers:
        result["blocking_reasons"] = list(dict.fromkeys(blockers))
        return result
    raw_path = str(source_env.get(EVIDENCE_PATH_ENV) or "").strip()
    evidence_path = Path(raw_path) if raw_path else Path()
    configured_sha = str(source_env.get(EVIDENCE_SHA256_ENV) or "").strip().lower()
    actual_sha: str | None = None
    if not raw_path or not evidence_path.is_file():
        blockers.append("evidence_report_missing")
    else:
        actual_sha, evidence_errors = _validated_evidence(evidence_path, configured_sha)
        blockers.extend(evidence_errors)
    if blockers:
        result["blocking_reasons"] = list(dict.fromkeys(blockers))
        result["evidence_path"] = raw_path or None
        result["evidence_sha256"] = actual_sha
        return result
    result.update(
        {
            "status": "active_krx_regular_v2_5",
            "selected_prompt_version": (
                DECISION_QUALITY_ENTRY_PRICE_V2_5_LIVE_KRX_PROMPT_VERSION
            ),
            "effective_venue": TARGET_VENUE,
            "session_bucket": TARGET_SESSION,
            "runtime_effect": True,
            "allowed_runtime_apply": True,
            "evidence_path": str(evidence_path),
            "evidence_sha256": actual_sha,
            "blocking_reasons": [],
            "decision_authority": "krx_regular_entry_price_prompt_selection_only",
            "forbidden_uses": [
                "nxt_or_premarket_prompt_selection",
                "provider_model_quantity_threshold_or_cap_change",
                "broker_account_order_cooldown_or_safety_guard_bypass",
                "direct_order_submission",
            ],
        }
    )
    return result
