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
from datetime import date, datetime, time
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
from src.utils.jsonl_io import (
    JsonObjectReadReceipt,
    read_json_object_strict_receipt,
)

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
LEGACY_RUNTIME_AUTHORITY_BLOCKER = (
    "main_ai_quality_legacy_runtime_authority_fail_closed"
)
LEGACY_RUNTIME_AUTHORITY_ENABLED = False
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
        return read_json_object_strict_receipt(path).payload
    except (FileNotFoundError, OSError, ValueError):
        return {}


@lru_cache(maxsize=16)
def _validated_master_symbols(
    payload_json: str,
    expected_sha256: str,
    source_date_text: str,
    target_date_text: str,
) -> frozenset[str]:
    try:
        payload = json.loads(payload_json)
    except (TypeError, ValueError):
        return frozenset()
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
    value: Mapping[str, Any],
    *,
    target_date: str,
    receipt: JsonObjectReadReceipt | None = None,
) -> frozenset[str]:
    path = Path(str(value.get("symbol_master_path") or ""))
    expected = str(value.get("symbol_master_artifact_sha256") or "")
    source_date = str(value.get("symbol_master_source_date") or "")
    try:
        captured = receipt or read_json_object_strict_receipt(path)
    except (FileNotFoundError, OSError, ValueError):
        return frozenset()
    expected_path = (
        DATA_DIR
        / "report"
        / "micro_reversion_economic_reference"
        / f"micro_reversion_symbol_master_{source_date}.json"
    )
    if captured.logical_path != path.absolute() or path.absolute() != expected_path:
        return frozenset()
    return _validated_master_symbols(
        json.dumps(
            captured.payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ),
        expected,
        source_date,
        target_date,
    )


def activation_errors(
    value: Mapping[str, Any],
    *,
    target_date: str,
    selected_path: Path,
    receipt: Mapping[str, Any] | None = None,
    activation_receipt: JsonObjectReadReceipt | None = None,
    apply_receipt_receipt: JsonObjectReadReceipt | None = None,
    handoff_receipt: JsonObjectReadReceipt | None = None,
    master_receipt: JsonObjectReadReceipt | None = None,
) -> list[str]:
    errors: list[str] = []
    try:
        captured_activation = activation_receipt or read_json_object_strict_receipt(
            selected_path
        )
    except (FileNotFoundError, OSError, ValueError):
        captured_activation = None
        errors.append("activation_generation_invalid")
    canonical_activation_path = activation_path(target_date).absolute()
    if selected_path.absolute() != canonical_activation_path:
        errors.append("activation_path_not_canonical")
    if captured_activation is not None:
        if (
            captured_activation.logical_path != canonical_activation_path
            or captured_activation.payload != dict(value)
            or captured_activation.physical_path != captured_activation.logical_path
            or len(captured_activation.generation_census) != 1
        ):
            errors.append("activation_generation_binding_invalid")
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
    if not _activation_master_symbols(
        value,
        target_date=target_date,
        receipt=master_receipt,
    ):
        errors.append("activation_symbol_master_invalid_or_empty")
    receipt_path = Path(str(value.get("apply_receipt_path") or ""))
    expected_receipt_path = (
        DATA_DIR
        / "threshold_cycle"
        / "machine_microstructure_policy"
        / "apply_receipts"
        / f"{target_date}_{str(value.get('candidate_sha256') or '')}_applied.json"
    ).absolute()
    if receipt_path.absolute() != expected_receipt_path:
        errors.append("apply_receipt_path_not_canonical")
    try:
        captured_receipt = apply_receipt_receipt or read_json_object_strict_receipt(
            receipt_path
        )
    except (FileNotFoundError, OSError, ValueError):
        captured_receipt = None
        errors.append("apply_receipt_generation_invalid")
    persisted_receipt = captured_receipt.payload if captured_receipt is not None else {}
    if receipt is not None and dict(receipt) != persisted_receipt:
        errors.append("apply_receipt_snapshot_mismatch")
    receipt = persisted_receipt
    if captured_receipt is not None and (
        captured_receipt.logical_path != expected_receipt_path
        or captured_receipt.physical_path != captured_receipt.logical_path
        or len(captured_receipt.generation_census) != 1
    ):
        errors.append("apply_receipt_generation_binding_invalid")
    receipt_body = {
        key: item for key, item in receipt.items() if key != "receipt_content_sha256"
    }
    if receipt.get("receipt_content_sha256") != content_sha256(receipt_body):
        errors.append("apply_receipt_hash_mismatch")
    for field, expected in (
        ("schema", APPLY_RECEIPT_SCHEMA),
        ("status", "applied_guard_passed"),
        ("applied_at_kst", value.get("applied_at_kst")),
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
        ("preopen_handoff_sha256", value.get("preopen_handoff_sha256")),
        (
            "standing_authorization_sha256",
            value.get("standing_authorization_sha256"),
        ),
        ("activation_artifact_path", str(selected_path)),
        ("activation_artifact_sha256", value.get("artifact_content_sha256")),
        (
            "activation_artifact_raw_sha256",
            captured_activation.raw_sha256 if captured_activation is not None else None,
        ),
        ("symbol_master_source_date", value.get("symbol_master_source_date")),
        ("symbol_master_path", value.get("symbol_master_path")),
        (
            "symbol_master_artifact_sha256",
            value.get("symbol_master_artifact_sha256"),
        ),
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
    try:
        applied_at = datetime.fromisoformat(str(value.get("applied_at_kst") or ""))
        if applied_at.tzinfo is None:
            raise ValueError
        applied_at = applied_at.astimezone(KST)
        if applied_at.date().isoformat() != target_date or applied_at.time() >= time(
            8, 0
        ):
            errors.append("activation_applied_at_outside_preopen_window")
    except (TypeError, ValueError):
        errors.append("activation_applied_at_invalid")

    handoff_path = Path(str(value.get("preopen_handoff") or ""))
    try:
        captured_handoff = handoff_receipt or read_json_object_strict_receipt(
            handoff_path
        )
    except (FileNotFoundError, OSError, ValueError):
        captured_handoff = None
        errors.append("preopen_handoff_generation_invalid")
    if captured_handoff is not None:
        try:
            from src.engine.automation import (
                machine_microstructure_policy_approval as approval,
            )

            expected_handoff = (
                approval.HANDOFF_DIR
                / target_date
                / (
                    f"{approval._safe_id(str(value.get('candidate_id') or 'candidate'))}_"
                    f"{str(value.get('candidate_sha256') or '')[:16]}.json"
                )
            ).absolute()
            expected_registry_sha256 = approval._registry_entry_sha256(
                approval.TRUSTED_RUNTIME_FAMILY_REGISTRY.get(RUNTIME_FAMILY)
            )
        except (ImportError, ValueError):
            expected_handoff = Path("/__invalid_handoff__")
            expected_registry_sha256 = None
        if (
            handoff_path.absolute() != expected_handoff
            or captured_handoff.logical_path != expected_handoff
            or captured_handoff.physical_path != captured_handoff.logical_path
            or len(captured_handoff.generation_census) != 1
            or captured_handoff.raw_sha256 != value.get("preopen_handoff_sha256")
        ):
            errors.append("preopen_handoff_generation_binding_invalid")
        handoff = captured_handoff.payload
        for field, expected in (
            ("schema", "machine_microstructure_policy_preopen_handoff_v1"),
            ("target_date", target_date),
            ("queue_key", value.get("queue_key")),
            ("candidate_id", value.get("candidate_id")),
            ("candidate_sha256", value.get("candidate_sha256")),
            ("runtime_family", RUNTIME_FAMILY),
            ("stage", TARGET_STAGE),
            ("axis", TUNING_AXIS),
            ("effective_venue", TARGET_VENUE),
            ("session_bucket", TARGET_SESSION),
            ("bounded_contract_sha256", BOUNDED_CONTRACT_SHA256),
            ("runtime_registry_entry_sha256", expected_registry_sha256),
            (
                "preopen_consumer",
                "src.engine.automation.main_ai_quality_runtime_family.preopen_apply",
            ),
            ("status", "preopen_authorization_handoff_ready"),
            ("runtime_effect", False),
            ("runtime_apply_performed", False),
            ("allowed_runtime_apply", True),
            ("actual_order_submitted", False),
            ("broker_order_forbidden", True),
        ):
            if handoff.get(field) != expected:
                errors.append(f"preopen_handoff_contract_mismatch:{field}")
        if handoff.get("bounded_values") != {
            "current": CONTROL_PROMPT_SHA256,
            "recommended": RECOMMENDED_PROMPT_SHA256,
        }:
            errors.append("preopen_handoff_bounded_values_mismatch")
        if handoff.get("authorization_mode") not in {
            "first_explicit_operator_approval",
            "enrolled_same_bounded_family_auto_chain",
        }:
            errors.append("preopen_handoff_authorization_mode_invalid")
        if value.get("runtime_registry_entry_sha256") != expected_registry_sha256:
            errors.append("activation_runtime_registry_hash_mismatch")
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
        "runtime_apply_performed": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    # P0-P2 remain source-only until the legacy PREOPEN/runtime authority chain
    # is replaced by a separately reviewed exact-generation contract.  Keep this
    # gate ahead of every artifact read so even previously published authority
    # generations cannot select the candidate prompt.
    if not LEGACY_RUNTIME_AUTHORITY_ENABLED:
        result.update(
            {
                "status": "fallback_legacy_runtime_authority_disabled",
                "blocking_reasons": [LEGACY_RUNTIME_AUTHORITY_BLOCKER],
            }
        )
        return result
    if configured != CONTROL_PROMPT_VERSION:
        result["status"] = "fallback_same_stage_owner_conflict"
        return result
    if venue != TARGET_VENUE or session != TARGET_SESSION:
        result["status"] = "fallback_outside_exact_cohort"
        return result
    selected_path = path or activation_path(target_date)
    try:
        activation_receipt = read_json_object_strict_receipt(selected_path)
        activation = activation_receipt.payload
        apply_receipt_receipt = read_json_object_strict_receipt(
            Path(str(activation.get("apply_receipt_path") or ""))
        )
        handoff_receipt = read_json_object_strict_receipt(
            Path(str(activation.get("preopen_handoff") or ""))
        )
        master_receipt = read_json_object_strict_receipt(
            Path(str(activation.get("symbol_master_path") or ""))
        )
    except (FileNotFoundError, OSError, ValueError):
        result["status"] = "fallback_activation_invalid"
        result["blocking_reasons"] = ["activation_authority_generation_invalid"]
        return result
    errors = activation_errors(
        activation,
        target_date=target_date,
        selected_path=selected_path,
        activation_receipt=activation_receipt,
        apply_receipt_receipt=apply_receipt_receipt,
        handoff_receipt=handoff_receipt,
        master_receipt=master_receipt,
    )
    if errors:
        result["status"] = "fallback_activation_invalid"
        result["blocking_reasons"] = errors
        return result
    if symbol not in _activation_master_symbols(
        activation,
        target_date=target_date,
        receipt=master_receipt,
    ):
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
