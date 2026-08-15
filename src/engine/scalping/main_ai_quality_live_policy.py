"""Resolve the first exact-bound AI quality prompt policy at runtime.

The module is a prompt selector only.  It consumes a date-scoped PREOPEN
activation that is bound to the approval handoff, standing intent, exact R3
candidate, and trusted registry entry.  Any mismatch returns the configured
control prompt.  It never submits an order or changes provider, quantity,
threshold, bot, cap, or hard-safety state.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping
from zoneinfo import ZoneInfo

from src.engine.ai_prompt_contracts import (
    DECISION_QUALITY_V2_PROMPT_VERSION,
    SCALPING_WATCHING_HOT_SYSTEM_PROMPT,
    decision_quality_v2_system_prompt,
)
from src.utils.constants import DATA_DIR

KST = ZoneInfo("Asia/Seoul")
ACTIVATION_SCHEMA = "main_ai_quality_prompt_contract_preopen_activation_v1"
TARGET_STAGE = "entry"
TARGET_VENUE = "KRX"
TARGET_SESSION = "KRX_REGULAR"
RUNTIME_FAMILY = "main_ai_quality_entry_prompt_contract_v1"
TUNING_AXIS = "prompt_contract_effect"
BOUNDED_CONTRACT_SHA256 = (
    "8d6cfa74efa8cba403047bab2bbbeebb547f6f6936db799c238eab8c128e7a29"
)
APPLY_RECEIPT_SCHEMA = "machine_microstructure_policy_family_apply_receipt_v1"
APPLY_RECEIPT_OWNER = "main_ai_quality_runtime_family_preopen_apply"
CONTROL_PROMPT_VERSION = "hot_v1"
RECOMMENDED_PROMPT_VERSION = DECISION_QUALITY_V2_PROMPT_VERSION
CONTROL_PROMPT_SHA256 = hashlib.sha256(
    SCALPING_WATCHING_HOT_SYSTEM_PROMPT.encode("utf-8")
).hexdigest()
RECOMMENDED_PROMPT_SHA256 = hashlib.sha256(
    decision_quality_v2_system_prompt(TARGET_STAGE).encode("utf-8")
).hexdigest()
ACTIVATION_DIR = DATA_DIR / "runtime" / "main_ai_quality_prompt_contract"
SYMBOL_PATTERN = re.compile(r"^[0-9]{6}$")


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def content_sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _economic_payload_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def activation_path(target_date: str) -> Path:
    return ACTIVATION_DIR / f"main_ai_quality_prompt_contract_{target_date}.json"


def _load_regular_json(path: Path) -> dict[str, Any]:
    try:
        if path.is_symlink() or not path.is_file():
            return {}
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


@lru_cache(maxsize=16)
def _validated_master_symbols(
    path_text: str,
    expected_sha256: str,
    source_date_text: str,
    target_date_text: str,
    device_id: int,
    inode: int,
    mtime_ns: int,
    ctime_ns: int,
    size_bytes: int,
) -> frozenset[str]:
    del device_id, inode, mtime_ns, ctime_ns, size_bytes
    path = Path(path_text)
    payload = _load_regular_json(path)
    try:
        source_day = date.fromisoformat(source_date_text)
        target_day = date.fromisoformat(target_date_text)
    except ValueError:
        return frozenset()
    body = {key: value for key, value in payload.items() if key != "content_sha256"}
    if (
        source_day >= target_day
        or payload.get("schema") != "scalp_micro_reversion_symbol_master_v1"
        or payload.get("verified") is not True
        or payload.get("verification_status") != "verified"
        or payload.get("content_sha256") != _economic_payload_sha256(body)
        or _economic_payload_sha256(payload) != expected_sha256
        or payload.get("runtime_effect") is not False
        or payload.get("allowed_runtime_apply") is not False
        or payload.get("actual_order_submitted") is not False
        or payload.get("broker_order_forbidden") is not True
    ):
        return frozenset()
    records = payload.get("records")
    if not isinstance(records, list) or not records:
        return frozenset()
    eligible: set[str] = set()
    for record in records:
        if not isinstance(record, Mapping):
            return frozenset()
        symbol = str(record.get("symbol") or "")
        try:
            effective_from = date.fromisoformat(str(record.get("effective_from") or ""))
            effective_to_raw = record.get("effective_to")
            effective_to = (
                date.fromisoformat(str(effective_to_raw)) if effective_to_raw else None
            )
        except ValueError:
            return frozenset()
        if (
            not SYMBOL_PATTERN.fullmatch(symbol)
            or record.get("listing_market") not in {"KOSPI", "KOSDAQ"}
            or record.get("instrument_type") != "EQUITY"
            or record.get("instrument_tax_class") != "ordinary_taxable_equity_20bps"
            or record.get("metadata_source") != "official_symbol_product_master_v2"
            or record.get("conflict_status") != "clean"
            or effective_from > target_day
            or (effective_to is not None and target_day > effective_to)
        ):
            return frozenset()
        eligible.add(symbol)
    return frozenset(eligible)


def _activation_master_symbols(
    value: Mapping[str, Any], *, target_date: str
) -> frozenset[str]:
    path = Path(str(value.get("symbol_master_path") or ""))
    expected = str(value.get("symbol_master_artifact_sha256") or "")
    source_date = str(value.get("symbol_master_source_date") or "")
    try:
        if path.is_symlink() or not path.is_file():
            return frozenset()
        stat = path.stat()
    except OSError:
        return frozenset()
    return _validated_master_symbols(
        str(path),
        expected,
        source_date,
        target_date,
        stat.st_dev,
        stat.st_ino,
        stat.st_mtime_ns,
        stat.st_ctime_ns,
        stat.st_size,
    )


def activation_errors(
    value: Mapping[str, Any], *, target_date: str, selected_path: Path
) -> list[str]:
    errors: list[str] = []
    body = {
        key: item for key, item in value.items() if key != "artifact_content_sha256"
    }
    if value.get("schema") != ACTIVATION_SCHEMA:
        errors.append("activation_schema_invalid")
    if value.get("artifact_content_sha256") != content_sha256(body):
        errors.append("activation_hash_mismatch")
    for field, expected in (
        ("target_date", target_date),
        ("stage", TARGET_STAGE),
        ("runtime_family", RUNTIME_FAMILY),
        ("axis", TUNING_AXIS),
        ("effective_venue", TARGET_VENUE),
        ("session_bucket", TARGET_SESSION),
        ("current_prompt_version", CONTROL_PROMPT_VERSION),
        ("current_prompt_sha256", CONTROL_PROMPT_SHA256),
        ("recommended_prompt_version", RECOMMENDED_PROMPT_VERSION),
        ("recommended_prompt_sha256", RECOMMENDED_PROMPT_SHA256),
        ("bounded_contract_sha256", BOUNDED_CONTRACT_SHA256),
        ("status", "applied_guard_passed"),
        ("runtime_effect", True),
        ("runtime_apply_performed", True),
        ("allowed_runtime_apply", True),
        ("actual_order_submitted", False),
        ("broker_order_forbidden", True),
        ("same_stage_owner_conflict_free", True),
        ("hard_safety_and_broker_guards_preserved", True),
    ):
        if value.get(field) != expected:
            errors.append(f"activation_contract_mismatch:{field}")
    if not str(value.get("candidate_id") or "").strip():
        errors.append("activation_candidate_id_missing")
    if not str(value.get("queue_key") or "").strip():
        errors.append("activation_queue_key_missing")
    for field in (
        "candidate_sha256",
        "standing_authorization_sha256",
        "preopen_handoff_sha256",
        "runtime_registry_entry_sha256",
        "bounded_contract_sha256",
        "symbol_master_artifact_sha256",
    ):
        raw = str(value.get(field) or "")
        if len(raw) != 64 or any(char not in "0123456789abcdef" for char in raw):
            errors.append(f"activation_sha256_invalid:{field}")
    if value.get("activation_artifact_path") != str(selected_path):
        errors.append("activation_artifact_path_mismatch")
    if not _activation_master_symbols(value, target_date=target_date):
        errors.append("activation_symbol_master_invalid_or_empty")
    receipt_path = Path(str(value.get("apply_receipt_path") or ""))
    receipt = _load_regular_json(receipt_path)
    receipt_body = {
        key: item for key, item in receipt.items() if key != "receipt_content_sha256"
    }
    if receipt.get("receipt_content_sha256") != content_sha256(receipt_body):
        errors.append("apply_receipt_hash_mismatch")
    for field, expected in (
        ("schema", APPLY_RECEIPT_SCHEMA),
        ("status", "applied_guard_passed"),
        ("target_date", target_date),
        ("candidate_sha256", value.get("candidate_sha256")),
        ("candidate_id", value.get("candidate_id")),
        ("queue_key", value.get("queue_key")),
        ("runtime_family", RUNTIME_FAMILY),
        ("stage", TARGET_STAGE),
        ("axis", TUNING_AXIS),
        ("bounded_contract_sha256", BOUNDED_CONTRACT_SHA256),
        ("runtime_registry_entry_sha256", value.get("runtime_registry_entry_sha256")),
        ("preopen_handoff", value.get("preopen_handoff")),
        ("activation_artifact_path", str(selected_path)),
        ("activation_artifact_sha256", value.get("artifact_content_sha256")),
        ("receipt_owner", APPLY_RECEIPT_OWNER),
        ("same_stage_owner_conflict_free", True),
        ("hard_safety_and_broker_guards_preserved", True),
        ("runtime_effect", True),
        ("runtime_apply_performed", True),
        ("actual_order_submitted", False),
        ("broker_order_forbidden", True),
    ):
        if receipt.get(field) != expected:
            errors.append(f"apply_receipt_contract_mismatch:{field}")
    return sorted(set(errors))


def resolve_main_ai_quality_live_policy(
    *,
    configured_prompt_version: str,
    effective_venue: Any,
    session_bucket: Any,
    stock_code: Any,
    now: datetime | None = None,
    path: Path | None = None,
) -> dict[str, Any]:
    """Select the reviewed prompt only for the exact activated cohort/date."""

    current = (now or datetime.now(KST)).astimezone(KST)
    target_date = current.date().isoformat()
    venue = str(effective_venue or "").strip().upper()
    session = str(session_bucket or "").strip().upper()
    symbol = str(stock_code or "").strip()
    configured = str(configured_prompt_version or "").strip()
    result = {
        "enabled": False,
        "status": "fallback_configured_prompt",
        "selected_prompt_version": configured,
        "target_date": target_date,
        "effective_venue": venue or None,
        "session_bucket": session or None,
        "stock_code": symbol or None,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    if configured != CONTROL_PROMPT_VERSION:
        result["status"] = "fallback_same_stage_owner_conflict"
        return result
    if venue != TARGET_VENUE or session != TARGET_SESSION:
        result["status"] = "fallback_outside_exact_cohort"
        return result
    selected_path = path or activation_path(target_date)
    activation = _load_regular_json(selected_path)
    errors = activation_errors(
        activation, target_date=target_date, selected_path=selected_path
    )
    if errors:
        result["status"] = "fallback_activation_invalid"
        result["blocking_reasons"] = errors
        return result
    if symbol not in _activation_master_symbols(activation, target_date=target_date):
        result["status"] = "fallback_outside_verified_common_stock_master"
        return result
    result.update(
        {
            "enabled": True,
            "status": "active_exact_bound_prompt_contract",
            "selected_prompt_version": RECOMMENDED_PROMPT_VERSION,
            "activation_path": str(selected_path),
            "activation_artifact_sha256": activation.get("artifact_content_sha256"),
            "candidate_id": activation.get("candidate_id"),
            "candidate_sha256": activation.get("candidate_sha256"),
            "runtime_effect": True,
            "decision_authority": "exact_date_prompt_selection_only",
            "forbidden_uses": [
                "direct_order_submission",
                "provider_model_quantity_threshold_bot_cap_or_safety_change",
                "cross_stage_cross_venue_or_cross_session_apply",
            ],
        }
    )
    return result
