"""Exact-bound R3 -> approval -> PREOPEN runtime family for AI prompt quality.

The postclose phase converts only one standing-intent-matched R3 candidate
into the existing policy approval contract.  The PREOPEN phase consumes only
the resulting exact handoff and writes a date-scoped prompt activation plus an
apply receipt.  The family never submits an order and cannot alter provider,
model, price, quantity, threshold, bot, cap, or hard-safety settings.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Mapping
from zoneinfo import ZoneInfo

from src.engine.automation import main_ai_quality_standing_authorization as standing
from src.engine.automation import machine_microstructure_policy_approval as approval
from src.engine.scalping import main_ai_quality_live_policy as live_policy
from src.engine.scalping.micro_reversion import ai_quality_cycle
from src.utils.constants import DATA_DIR
from src.utils.market_day import is_krx_trading_day

KST = ZoneInfo("Asia/Seoul")
REPORT_SCHEMA = "main_ai_quality_runtime_family_cycle_v1"
SOURCE_REPORT_SCHEMA = "main_ai_quality_runtime_promotion_source_v1"
STANDING_AUTHORIZATION_PATH = (
    DATA_DIR / "config" / "main_ai_quality_first_candidate_standing_authorization.json"
)
SOURCE_REPORT_DIR = DATA_DIR / "threshold_cycle" / "main_ai_quality_runtime_family"
REPORT_DIR = DATA_DIR / "report" / "main_ai_quality_runtime_family"
PREOPEN_CONSUMER = "src.engine.automation.main_ai_quality_runtime_family.preopen_apply"
APPLY_RECEIPT_OWNER = "main_ai_quality_runtime_family_preopen_apply"
ATTRIBUTION_RECEIPT_OWNER = "main_ai_quality_runtime_family_post_apply_attribution"
OPERATOR_INSTRUCTION = (
    "Implement postclose AI quality R0-R3 automation; automatically apply "
    "the first exact candidate and continue tuning, while retaining all "
    "runtime/order safety gates."
)
OPERATOR_INSTRUCTION_SHA256 = hashlib.sha256(
    OPERATOR_INSTRUCTION.encode("utf-8")
).hexdigest()


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha256(value: Any) -> str:
    raw = value if isinstance(value, bytes) else _canonical_bytes(value)
    return hashlib.sha256(raw).hexdigest()


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


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        Path(temporary).unlink(missing_ok=True)


def source_report_path(target_date: str) -> Path:
    return SOURCE_REPORT_DIR / f"main_ai_quality_runtime_source_{target_date}.json"


def report_path(target_date: str, phase: str) -> Path:
    return REPORT_DIR / f"main_ai_quality_runtime_family_{phase}_{target_date}.json"


def _registry_entry() -> Mapping[str, Any]:
    return approval.TRUSTED_RUNTIME_FAMILY_REGISTRY[
        approval.MAIN_AI_QUALITY_RUNTIME_FAMILY
    ]


def _registry_sha256() -> str:
    digest = approval._registry_entry_sha256(_registry_entry())
    if not digest:
        raise ValueError("runtime_registry_entry_hash_missing")
    return digest


def _exact_enrolled_continuation(queue: Mapping[str, Any]) -> bool:
    enrollment = (queue.get("family_enrollments") or {}).get(
        approval.MAIN_AI_QUALITY_RUNTIME_FAMILY
    )
    if not isinstance(enrollment, Mapping):
        return False
    matches = [
        entry
        for entry in queue.get("candidates") or []
        if isinstance(entry, Mapping)
        and entry.get("queue_key") == enrollment.get("first_approved_queue_key")
    ]
    if len(matches) != 1:
        return False
    entry = matches[0]
    candidate = entry.get("candidate")
    candidate = candidate if isinstance(candidate, Mapping) else {}
    design = candidate.get("runtime_design")
    design = design if isinstance(design, Mapping) else {}
    return bool(
        enrollment.get("runtime_family") == approval.MAIN_AI_QUALITY_RUNTIME_FAMILY
        and enrollment.get("stage") == "entry"
        and enrollment.get("axis") == "prompt_contract_effect"
        and enrollment.get("bounded_contract_sha256")
        == approval.MAIN_AI_QUALITY_BOUNDED_CONTRACT_SHA256
        and enrollment.get("runtime_registry_entry_sha256") == _registry_sha256()
        and enrollment.get("enrolled_after_guarded_apply") is True
        and enrollment.get("enrolled_after_post_apply_attribution") is True
        and bool(str(enrollment.get("first_approved_queue_key") or "").strip())
        and bool(str(enrollment.get("first_apply_receipt") or "").strip())
        and bool(str(enrollment.get("post_apply_attribution_receipt") or "").strip())
        and entry.get("state") == approval.STATE_POST_APPLY_ATTRIBUTED
        and approval._candidate_runtime_family(candidate)
        == approval.MAIN_AI_QUALITY_RUNTIME_FAMILY
        and approval.runtime_design_errors(candidate) == []
        and entry.get("family_apply_receipt") == enrollment.get("first_apply_receipt")
        and entry.get("post_apply_attribution_receipt")
        == enrollment.get("post_apply_attribution_receipt")
        and design.get("bounded_contract_sha256")
        == approval.MAIN_AI_QUALITY_BOUNDED_CONTRACT_SHA256
    )


def _artifact_hash_valid(value: Mapping[str, Any]) -> bool:
    declared = str(value.get("artifact_content_sha256") or "")
    return bool(
        declared
        and declared
        == _sha256(
            {
                key: item
                for key, item in value.items()
                if key != "artifact_content_sha256"
            }
        )
    )


def _cli_now_for_phase(*, phase: str, target_day: date, current: datetime) -> datetime:
    """Keep runtime PREOPEN authority bound to the real KST calendar day."""

    if current.tzinfo is None:
        raise ValueError("runtime_family_now_must_be_timezone_aware")
    current_kst = current.astimezone(KST)
    if phase == "preopen" and current_kst.date() != target_day:
        raise ValueError("preopen_runtime_target_date_not_current_kst_date")
    return current_kst


def _matching_partition(
    r3_candidate: Mapping[str, Any], rolling: Mapping[str, Any]
) -> Mapping[str, Any]:
    if (
        rolling.get("schema") != ai_quality_cycle.ROLLING_SCHEMA
        or not _artifact_hash_valid(rolling)
        or rolling.get("global_candidate_blockers") != []
    ):
        raise ValueError("rolling_artifact_contract_invalid")
    matches = [
        row
        for row in rolling.get("partitions") or []
        if isinstance(row, Mapping)
        and row.get("decision_stage") == r3_candidate.get("decision_stage")
        and str(row.get("effective_venue") or "").upper()
        == str(r3_candidate.get("effective_venue") or "").upper()
        and str(row.get("session_bucket") or "").upper()
        == str(r3_candidate.get("session_bucket") or "").upper()
        and row.get("control_contract_sha256")
        == r3_candidate.get("current_contract_sha256")
        and row.get("candidate_contract_sha256")
        == r3_candidate.get("recommended_contract_sha256")
        and row.get("current_prompt_sha256")
        == r3_candidate.get("current_prompt_sha256")
        and row.get("recommended_prompt_sha256")
        == r3_candidate.get("recommended_prompt_sha256")
        and row.get("latest_symbol_master_source_date")
        == r3_candidate.get("latest_symbol_master_source_date")
        and row.get("latest_symbol_master_artifact_sha256")
        == r3_candidate.get("latest_symbol_master_artifact_sha256")
        and row.get("r3_source_candidate_eligible") is True
        and all(not values for values in (row.get("gate_findings") or {}).values())
    ]
    if len(matches) != 1:
        raise ValueError("rolling_exact_partition_not_unique")
    return matches[0]


def build_promotion_candidate(
    *,
    authorization: Mapping[str, Any],
    r3_manifest: Mapping[str, Any],
    rolling: Mapping[str, Any],
    approval_queue: Mapping[str, Any],
    now: datetime,
) -> dict[str, Any]:
    """Materialize one exact machine-policy candidate or fail closed."""

    enrolled_continuation = _exact_enrolled_continuation(approval_queue)
    resolution = standing.resolve_standing_authorization(
        authorization,
        r3_manifest,
        approval_queue=approval_queue,
        runtime_registry=approval.TRUSTED_RUNTIME_FAMILY_REGISTRY,
        now=now,
        enrolled_continuation=enrolled_continuation,
    )
    binding = resolution.get("candidate_binding")
    if (
        authorization.get("operator_instruction") != OPERATOR_INSTRUCTION
        or hashlib.sha256(
            str(authorization.get("operator_instruction") or "").encode("utf-8")
        ).hexdigest()
        != OPERATOR_INSTRUCTION_SHA256
    ):
        raise ValueError("standing_intent_operator_instruction_mismatch")
    if not isinstance(binding, Mapping):
        raise ValueError(
            "standing_intent_exact_candidate_not_bound:"
            + ",".join(resolution.get("blocker_codes") or [])
        )
    matches = [
        row
        for row in r3_manifest.get("candidates") or []
        if isinstance(row, Mapping)
        and row.get("candidate_id") == binding.get("candidate_id")
        and row.get("candidate_sha256") == binding.get("candidate_sha256")
    ]
    if len(matches) != 1:
        raise ValueError("r3_bound_candidate_not_unique")
    r3_candidate = matches[0]
    if (
        r3_candidate.get("decision_stage") != "entry"
        or str(r3_candidate.get("effective_venue") or "").upper() != "KRX"
        or str(r3_candidate.get("session_bucket") or "").upper() != "KRX_REGULAR"
        or r3_candidate.get("current_prompt_sha256")
        != live_policy.CONTROL_PROMPT_SHA256
        or r3_candidate.get("recommended_prompt_sha256")
        != live_policy.RECOMMENDED_PROMPT_SHA256
    ):
        raise ValueError("r3_candidate_outside_registered_prompt_transition")
    partition = _matching_partition(r3_candidate, rolling)
    windows = partition.get("windows")
    if not isinstance(windows, Mapping) or set(windows) != {"5", "10", "20"}:
        raise ValueError("rolling_window_contract_invalid")
    window_5 = windows["5"]
    window_20 = windows["20"]
    if not isinstance(window_5, Mapping) or not isinstance(window_20, Mapping):
        raise ValueError("rolling_window_value_invalid")
    source_date = str(r3_manifest.get("target_date") or "")
    source_day = date.fromisoformat(source_date)
    if (
        r3_candidate.get("latest_symbol_master_source_date") != source_date
        or len(str(r3_candidate.get("latest_symbol_master_artifact_sha256") or ""))
        != 64
    ):
        raise ValueError("r3_candidate_latest_symbol_master_binding_invalid")
    first_approval = not enrolled_continuation
    candidate_id = f"main-ai-entry-prompt:{r3_candidate['candidate_id']}"
    candidate: dict[str, Any] = {
        "schema": approval.CANDIDATE_SCHEMA,
        "candidate_id": candidate_id,
        "source_date": source_date,
        "evidence_valid_through": (source_day + timedelta(days=31)).isoformat(),
        "owner": "main_ai_quality_runtime_family",
        "owner_scope_id": "entry:KRX:KRX_REGULAR:prompt_contract_effect",
        "first_operator_approval_required": first_approval,
        "evidence": {
            "observed_trading_days": window_20.get("observed_trading_days"),
            "matched_entry_anchors": window_20.get("common_parent_count"),
            "bbo_complete_rate_pct": window_20.get("bbo_coverage_pct"),
            "depth_window_coverage_pct": window_20.get("depth_coverage_pct"),
            "invalid_contract_row_count": window_20.get("invalid_transition_count"),
            "rolling_source_quality_adjusted_ev_pct": {
                f"{key}d": windows[key].get("candidate_source_quality_adjusted_ev_pct")
                for key in ("5", "10", "20")
            },
            "relative_primary_ev_uplift_pct": min(
                float(windows[key].get("relative_uplift_pct"))
                for key in ("5", "10", "20")
            ),
            "primary_20d_net_profit": window_20.get(
                "candidate_total_notional_net_profit_krw"
            ),
            "costs_included": True,
            "source_quality_pass": True,
            "paired_p10_not_worse": all(
                float(windows[key]["candidate_p10_ev_pct"])
                >= float(windows[key]["control_p10_ev_pct"])
                for key in ("5", "10", "20")
            ),
            "held_unresolved_not_increased": all(
                int(windows[key]["candidate_deferred_count"])
                <= int(windows[key]["control_deferred_count"])
                for key in ("5", "10", "20")
            ),
            "expected_candidate_p10_5d": window_5.get("candidate_p10_ev_pct"),
            "expected_candidate_severe_tail_5d": window_5.get(
                "candidate_severe_tail_count"
            ),
            "expected_candidate_deferred_5d": window_5.get("candidate_deferred_count"),
        },
        "runtime_design": {
            "runtime_family": approval.MAIN_AI_QUALITY_RUNTIME_FAMILY,
            "stage": "entry",
            "axis": "prompt_contract_effect",
            "effective_venue": live_policy.TARGET_VENUE,
            "session_bucket": live_policy.TARGET_SESSION,
            "mapping_status": "registered",
            "runtime_registry_verified": True,
            "same_stage_owner_conflict_free": True,
            "preopen_consumer": PREOPEN_CONSUMER,
            "bounded_values": {
                "current": r3_candidate.get("current_prompt_sha256"),
                "recommended": r3_candidate.get("recommended_prompt_sha256"),
            },
            "bounded_contract_sha256": (
                approval.MAIN_AI_QUALITY_BOUNDED_CONTRACT_SHA256
            ),
            "rollback": {
                "trigger": "any_activation_contract_or_post_apply_guard_failure",
                "value": live_policy.CONTROL_PROMPT_VERSION,
                "automatic_fallback": True,
            },
            "post_apply_attribution": {
                "owner": ATTRIBUTION_RECEIPT_OWNER,
                "window": "first_complete_applied_session_then_rolling_5d_10d_20d",
            },
            "forbidden_uses": list(
                approval.MAIN_AI_QUALITY_BOUNDED_CONTRACT["forbidden_changes"]
            ),
        },
        "source_bindings": {
            "r3_manifest_sha256": r3_manifest.get("artifact_content_sha256"),
            "r3_candidate_id": r3_candidate.get("candidate_id"),
            "r3_candidate_sha256": r3_candidate.get("candidate_sha256"),
            "rolling_artifact_sha256": rolling.get("artifact_content_sha256"),
            "rolling_partition_sha256": _sha256(partition),
            "standing_authorization_sha256": authorization.get(
                "artifact_content_sha256"
            ),
            "operator_instruction_sha256": OPERATOR_INSTRUCTION_SHA256,
            "current_contract_sha256": r3_candidate.get("current_contract_sha256"),
            "recommended_contract_sha256": r3_candidate.get(
                "recommended_contract_sha256"
            ),
            "current_prompt_sha256": r3_candidate.get("current_prompt_sha256"),
            "recommended_prompt_sha256": r3_candidate.get("recommended_prompt_sha256"),
            "symbol_master_source_date": r3_candidate.get(
                "latest_symbol_master_source_date"
            ),
            "symbol_master_artifact_sha256": r3_candidate.get(
                "latest_symbol_master_artifact_sha256"
            ),
        },
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    candidate["candidate_sha256"] = approval.candidate_sha256(candidate)
    errors = [
        *approval.evidence_readiness_errors(candidate),
        *approval.runtime_design_errors(candidate),
    ]
    if errors:
        raise ValueError("promotion_candidate_contract_invalid:" + ",".join(errors))
    return candidate


def build_post_apply_continuation_candidate(
    *,
    entry: Mapping[str, Any],
    attribution: Mapping[str, Any],
    attribution_path: Path,
    rolling: Mapping[str, Any],
    target_date: str,
) -> dict[str, Any]:
    """Carry the exact applied policy one day after a passing R6 receipt."""

    prior = entry.get("candidate")
    prior = prior if isinstance(prior, Mapping) else {}
    if (
        entry.get("state")
        not in {approval.STATE_APPLIED, approval.STATE_POST_APPLY_ATTRIBUTED}
        or approval._candidate_runtime_family(prior)
        != approval.MAIN_AI_QUALITY_RUNTIME_FAMILY
        or approval.evidence_readiness_errors(prior)
        or approval.runtime_design_errors(prior)
        or attribution.get("receipt_content_sha256")
        != _sha256(
            {
                key: value
                for key, value in attribution.items()
                if key != "receipt_content_sha256"
            }
        )
        or attribution.get("status") != "post_apply_attribution_complete"
        or attribution.get("candidate_sha256") != entry.get("candidate_sha256")
        or attribution.get("queue_key") != entry.get("queue_key")
        or attribution.get("runtime_registry_entry_sha256") != _registry_sha256()
        or attribution.get("post_apply_attribution_complete") is not True
        or attribution.get("runtime_effect") is not False
        or attribution.get("actual_order_submitted") is not False
        or attribution.get("broker_order_forbidden") is not True
        or rolling.get("artifact_content_sha256")
        != attribution.get("source_rolling_artifact_sha256")
        or attribution.get("source_symbol_master_date") != target_date
        or len(str(attribution.get("source_symbol_master_artifact_sha256") or "")) != 64
    ):
        raise ValueError("post_apply_continuation_source_contract_invalid")
    source_day = date.fromisoformat(target_date)
    candidate = {
        key: value
        for key, value in prior.items()
        if key not in {"candidate_id", "candidate_sha256"}
    }
    candidate.update(
        {
            "candidate_id": (
                f"main-ai-entry-prompt-continuation:{target_date}:"
                f"{str(entry.get('candidate_sha256') or '')[:16]}"
            ),
            "source_date": target_date,
            "evidence_valid_through": (source_day + timedelta(days=31)).isoformat(),
            "first_operator_approval_required": False,
            "source_bindings": {
                **dict(prior.get("source_bindings") or {}),
                "prior_applied_candidate_sha256": entry.get("candidate_sha256"),
                "post_apply_attribution_receipt": str(attribution_path),
                "post_apply_attribution_receipt_sha256": attribution.get(
                    "receipt_content_sha256"
                ),
                "continuation_rolling_artifact_sha256": rolling.get(
                    "artifact_content_sha256"
                ),
                "symbol_master_source_date": attribution.get(
                    "source_symbol_master_date"
                ),
                "symbol_master_artifact_sha256": attribution.get(
                    "source_symbol_master_artifact_sha256"
                ),
            },
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
        }
    )
    candidate["candidate_sha256"] = approval.candidate_sha256(candidate)
    errors = [
        *approval.evidence_readiness_errors(candidate),
        *approval.runtime_design_errors(candidate),
    ]
    if errors:
        raise ValueError("continuation_candidate_contract_invalid:" + ",".join(errors))
    return candidate


def _handoff_sha256(path: Path, handoff: Mapping[str, Any]) -> str:
    if not path.is_file() or path.is_symlink():
        raise ValueError("preopen_handoff_file_invalid")
    if json.loads(path.read_text(encoding="utf-8")) != dict(handoff):
        raise ValueError("preopen_handoff_snapshot_changed")
    return _file_sha256(path)


def build_preopen_activation(
    *,
    handoff_path: Path,
    handoff: Mapping[str, Any],
    candidate: Mapping[str, Any],
    authorization: Mapping[str, Any],
    now: datetime,
    activation_artifact_path: Path,
    apply_receipt_path: Path,
    symbol_master_path: Path | None = None,
) -> dict[str, Any]:
    target_date = now.astimezone(KST).date().isoformat()
    design = candidate.get("runtime_design")
    design = design if isinstance(design, Mapping) else {}
    sources = candidate.get("source_bindings")
    sources = sources if isinstance(sources, Mapping) else {}
    master_source_date = str(sources.get("symbol_master_source_date") or "")
    master_expected_sha256 = str(sources.get("symbol_master_artifact_sha256") or "")
    selected_master_path = symbol_master_path or (
        ai_quality_cycle.ECONOMIC_REPORT_ROOT
        / f"micro_reversion_symbol_master_{master_source_date}.json"
    )
    symbol_master = _load_json(selected_master_path)
    errors = [
        *standing._authorization_errors(authorization),
        *approval.evidence_readiness_errors(candidate),
        *approval.runtime_design_errors(candidate),
    ]
    symbol_master_body = {
        key: value for key, value in symbol_master.items() if key != "content_sha256"
    }
    if (
        selected_master_path.is_symlink()
        or not selected_master_path.is_file()
        or symbol_master.get("schema") != "scalp_micro_reversion_symbol_master_v1"
        or symbol_master.get("verified") is not True
        or symbol_master.get("verification_status") != "verified"
        or symbol_master.get("content_sha256")
        != _economic_payload_sha256(symbol_master_body)
        or _economic_payload_sha256(symbol_master) != master_expected_sha256
        or master_source_date != str(candidate.get("source_date") or "")
        or not isinstance(symbol_master.get("records"), list)
        or not symbol_master.get("records")
        or any(
            not isinstance(record, Mapping)
            or record.get("listing_market") not in {"KOSPI", "KOSDAQ"}
            or record.get("instrument_type") != "EQUITY"
            or record.get("instrument_tax_class") != "ordinary_taxable_equity_20bps"
            for record in symbol_master.get("records") or []
        )
        or symbol_master.get("runtime_effect") is not False
        or symbol_master.get("allowed_runtime_apply") is not False
        or symbol_master.get("actual_order_submitted") is not False
        or symbol_master.get("broker_order_forbidden") is not True
    ):
        errors.append("preopen_symbol_master_contract_invalid")
    authorization_mode = str(handoff.get("authorization_mode") or "")
    if authorization_mode == "first_explicit_operator_approval":
        try:
            if now.astimezone(KST) >= standing._aware_kst(
                str(authorization.get("expires_at_kst") or "")
            ):
                errors.append("standing_authorization_expired_before_preopen")
        except ValueError:
            errors.append("standing_authorization_expiry_invalid_before_preopen")
    if now.astimezone(KST).time() >= approval.PREOPEN_HANDOFF_CUTOFF_KST:
        errors.append("preopen_apply_at_or_after_market_open_cutoff")
    if not is_krx_trading_day(now.astimezone(KST).date()):
        errors.append("preopen_apply_target_not_trading_day")
    for field, expected in (
        ("schema", approval.HANDOFF_SCHEMA),
        ("target_date", target_date),
        ("candidate_id", candidate.get("candidate_id")),
        ("candidate_sha256", candidate.get("candidate_sha256")),
        ("runtime_family", approval.MAIN_AI_QUALITY_RUNTIME_FAMILY),
        ("stage", "entry"),
        ("axis", "prompt_contract_effect"),
        ("effective_venue", live_policy.TARGET_VENUE),
        ("session_bucket", live_policy.TARGET_SESSION),
        ("bounded_contract_sha256", approval.MAIN_AI_QUALITY_BOUNDED_CONTRACT_SHA256),
        ("runtime_registry_entry_sha256", _registry_sha256()),
        ("preopen_consumer", PREOPEN_CONSUMER),
        ("status", "preopen_authorization_handoff_ready"),
        ("allowed_runtime_apply", True),
        ("actual_order_submitted", False),
        ("broker_order_forbidden", True),
    ):
        if handoff.get(field) != expected:
            errors.append(f"preopen_handoff_contract_mismatch:{field}")
    if handoff.get("bounded_values") != design.get("bounded_values"):
        errors.append("preopen_handoff_bounded_values_mismatch")
    if authorization_mode == "first_explicit_operator_approval":
        if sources.get("standing_authorization_sha256") != authorization.get(
            "artifact_content_sha256"
        ) or handoff.get("operator_authorization_id") != authorization.get(
            "operator_authorization_id"
        ):
            errors.append("first_apply_standing_intent_binding_mismatch")
    elif authorization_mode != "enrolled_same_bounded_family_auto_chain":
        errors.append("preopen_handoff_authorization_mode_invalid")
    if errors:
        raise ValueError("preopen_apply_blocked:" + ",".join(sorted(set(errors))))
    handoff_hash = _handoff_sha256(handoff_path, handoff)
    body = {
        "schema": live_policy.ACTIVATION_SCHEMA,
        "target_date": target_date,
        "applied_at_kst": now.astimezone(KST).isoformat(timespec="microseconds"),
        "status": "applied_guard_passed",
        "queue_key": handoff.get("queue_key"),
        "candidate_id": candidate.get("candidate_id"),
        "candidate_sha256": candidate.get("candidate_sha256"),
        "standing_authorization_sha256": sources.get("standing_authorization_sha256"),
        "preopen_handoff": str(handoff_path),
        "preopen_handoff_sha256": handoff_hash,
        "activation_artifact_path": str(activation_artifact_path),
        "apply_receipt_path": str(apply_receipt_path),
        "runtime_family": approval.MAIN_AI_QUALITY_RUNTIME_FAMILY,
        "runtime_registry_entry_sha256": _registry_sha256(),
        "bounded_contract_sha256": approval.MAIN_AI_QUALITY_BOUNDED_CONTRACT_SHA256,
        "stage": "entry",
        "axis": "prompt_contract_effect",
        "effective_venue": live_policy.TARGET_VENUE,
        "session_bucket": live_policy.TARGET_SESSION,
        "current_prompt_version": live_policy.CONTROL_PROMPT_VERSION,
        "current_prompt_sha256": live_policy.CONTROL_PROMPT_SHA256,
        "recommended_prompt_version": live_policy.RECOMMENDED_PROMPT_VERSION,
        "recommended_prompt_sha256": live_policy.RECOMMENDED_PROMPT_SHA256,
        "symbol_master_source_date": master_source_date,
        "symbol_master_path": str(selected_master_path),
        "symbol_master_artifact_sha256": master_expected_sha256,
        "same_stage_owner_conflict_free": True,
        "hard_safety_and_broker_guards_preserved": True,
        "runtime_effect": True,
        "runtime_apply_performed": True,
        "allowed_runtime_apply": True,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    return {**body, "artifact_content_sha256": _sha256(body)}


def apply_receipt(activation: Mapping[str, Any]) -> dict[str, Any]:
    body = {
        "schema": approval.APPLY_RECEIPT_SCHEMA,
        "status": "applied_guard_passed",
        "applied_at_kst": activation.get("applied_at_kst"),
        "target_date": activation.get("target_date"),
        "queue_key": activation.get("queue_key"),
        "candidate_id": activation.get("candidate_id"),
        "candidate_sha256": activation.get("candidate_sha256"),
        "runtime_family": activation.get("runtime_family"),
        "stage": activation.get("stage"),
        "axis": activation.get("axis"),
        "bounded_contract_sha256": activation.get("bounded_contract_sha256"),
        "runtime_registry_entry_sha256": activation.get(
            "runtime_registry_entry_sha256"
        ),
        "preopen_handoff": activation.get("preopen_handoff"),
        "activation_artifact_path": activation.get("activation_artifact_path"),
        "activation_artifact_sha256": activation.get("artifact_content_sha256"),
        "receipt_owner": APPLY_RECEIPT_OWNER,
        "same_stage_owner_conflict_free": True,
        "hard_safety_and_broker_guards_preserved": True,
        "runtime_effect": True,
        "runtime_apply_performed": True,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    return {**body, "receipt_content_sha256": _sha256(body)}


def apply_receipt_errors(
    receipt: Mapping[str, Any], *, activation: Mapping[str, Any]
) -> list[str]:
    errors: list[str] = []
    if receipt.get("receipt_content_sha256") != _sha256(
        {
            key: value
            for key, value in receipt.items()
            if key != "receipt_content_sha256"
        }
    ):
        errors.append("apply_receipt_hash_mismatch")
    for field, expected in (
        ("schema", approval.APPLY_RECEIPT_SCHEMA),
        ("status", "applied_guard_passed"),
        ("target_date", activation.get("target_date")),
        ("queue_key", activation.get("queue_key")),
        ("candidate_id", activation.get("candidate_id")),
        ("candidate_sha256", activation.get("candidate_sha256")),
        ("runtime_family", approval.MAIN_AI_QUALITY_RUNTIME_FAMILY),
        ("stage", "entry"),
        ("axis", "prompt_contract_effect"),
        ("bounded_contract_sha256", approval.MAIN_AI_QUALITY_BOUNDED_CONTRACT_SHA256),
        ("runtime_registry_entry_sha256", _registry_sha256()),
        ("preopen_handoff", activation.get("preopen_handoff")),
        ("activation_artifact_path", activation.get("activation_artifact_path")),
        ("activation_artifact_sha256", activation.get("artifact_content_sha256")),
        ("receipt_owner", APPLY_RECEIPT_OWNER),
        ("runtime_effect", True),
        ("runtime_apply_performed", True),
        ("actual_order_submitted", False),
        ("broker_order_forbidden", True),
    ):
        if receipt.get(field) != expected:
            errors.append(f"apply_receipt_contract_mismatch:{field}")
    return sorted(set(errors))


def build_post_apply_attribution_receipt(
    *,
    entry: Mapping[str, Any],
    rolling: Mapping[str, Any],
    target_date: str,
    now: datetime,
) -> dict[str, Any]:
    """Close R6 only after one complete applied session passes continuation guards."""

    if entry.get("state") != approval.STATE_APPLIED:
        raise ValueError("post_apply_candidate_not_applied")
    candidate = entry.get("candidate")
    candidate = candidate if isinstance(candidate, Mapping) else {}
    design = candidate.get("runtime_design")
    design = design if isinstance(design, Mapping) else {}
    evidence = candidate.get("evidence")
    evidence = evidence if isinstance(evidence, Mapping) else {}
    bounded = design.get("bounded_values")
    bounded = bounded if isinstance(bounded, Mapping) else {}
    source_apply_receipt = _load_json(
        Path(str(entry.get("family_apply_receipt") or ""))
    )
    activation_path = Path(
        str(source_apply_receipt.get("activation_artifact_path") or "")
    )
    activation = _load_json(activation_path)
    if (
        approval._candidate_runtime_family(candidate)
        != approval.MAIN_AI_QUALITY_RUNTIME_FAMILY
        or entry.get("preopen_target_date") != target_date
        or rolling.get("schema") != ai_quality_cycle.ROLLING_SCHEMA
        or not _artifact_hash_valid(rolling)
        or rolling.get("target_date") != target_date
        or rolling.get("global_candidate_blockers") != []
        or apply_receipt_errors(source_apply_receipt, activation=activation)
        or live_policy.activation_errors(
            activation,
            target_date=target_date,
            selected_path=activation_path,
        )
    ):
        raise ValueError("post_apply_source_contract_invalid")
    partitions = [
        row
        for row in rolling.get("partitions") or []
        if isinstance(row, Mapping)
        and row.get("decision_stage") == "entry"
        and str(row.get("effective_venue") or "").upper() == "KRX"
        and str(row.get("session_bucket") or "").upper() == "KRX_REGULAR"
        and row.get("current_prompt_sha256") == bounded.get("recommended")
        and target_date in (row.get("source_dates") or [])
    ]
    if len(partitions) != 1:
        raise ValueError("post_apply_exact_partition_not_unique")
    partition = partitions[0]
    if (
        partition.get("latest_symbol_master_source_date") != target_date
        or len(str(partition.get("latest_symbol_master_artifact_sha256") or "")) != 64
    ):
        raise ValueError("post_apply_symbol_master_binding_invalid")
    metrics = (partition.get("windows") or {}).get("5")
    if not isinstance(metrics, Mapping):
        raise ValueError("post_apply_window_missing")
    candidate_p10 = metrics.get("control_p10_ev_pct")
    expected_p10 = evidence.get("expected_candidate_p10_5d")
    checks = {
        "complete_applied_session_present": (
            int(metrics.get("observed_trading_days") or 0) >= 1
            and int(metrics.get("common_parent_count") or 0) >= 20
        ),
        "source_quality_adjusted_ev_positive": (
            float(metrics.get("control_source_quality_adjusted_ev_pct") or 0) > 0
        ),
        "paired_p10_continuation_not_worse": (
            isinstance(candidate_p10, (int, float))
            and not isinstance(candidate_p10, bool)
            and isinstance(expected_p10, (int, float))
            and not isinstance(expected_p10, bool)
            and float(candidate_p10) >= float(expected_p10)
        ),
        "severe_tail_continuation_not_worse": (
            int(metrics.get("control_severe_tail_count") or 0)
            <= int(evidence.get("expected_candidate_severe_tail_5d") or 0)
        ),
        "held_unresolved_continuation_not_worse": (
            int(metrics.get("control_deferred_count") or 0)
            <= int(evidence.get("expected_candidate_deferred_5d") or 0)
        ),
    }
    if not all(checks.values()):
        raise ValueError(
            "post_apply_continuation_gate_failed:"
            + ",".join(key for key, passed in checks.items() if not passed)
        )
    body = {
        "schema": approval.APPLY_RECEIPT_SCHEMA,
        "status": "post_apply_attribution_complete",
        "attributed_at_kst": now.astimezone(KST).isoformat(timespec="microseconds"),
        "target_date": target_date,
        "queue_key": entry.get("queue_key"),
        "candidate_sha256": entry.get("candidate_sha256"),
        "runtime_family": approval.MAIN_AI_QUALITY_RUNTIME_FAMILY,
        "stage": "entry",
        "axis": "prompt_contract_effect",
        "bounded_contract_sha256": approval.MAIN_AI_QUALITY_BOUNDED_CONTRACT_SHA256,
        "runtime_registry_entry_sha256": _registry_sha256(),
        "preopen_handoff": entry.get("preopen_handoff"),
        "source_apply_receipt": entry.get("family_apply_receipt"),
        "source_rolling_artifact_sha256": rolling.get("artifact_content_sha256"),
        "source_symbol_master_date": partition.get("latest_symbol_master_source_date"),
        "source_symbol_master_artifact_sha256": partition.get(
            "latest_symbol_master_artifact_sha256"
        ),
        "continuation_checks": checks,
        "post_apply_attribution_complete": True,
        "receipt_owner": ATTRIBUTION_RECEIPT_OWNER,
        "same_stage_owner_conflict_free": True,
        "hard_safety_and_broker_guards_preserved": True,
        "runtime_effect": False,
        "runtime_apply_performed": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    return {**body, "receipt_content_sha256": _sha256(body)}


def _postclose(
    *,
    target_date: str,
    write: bool,
    now: datetime,
    queue_path: Path,
    approval_dir: Path = approval.APPROVAL_DIR,
    apply_receipt_dir: Path = approval.APPLY_RECEIPT_DIR,
) -> dict[str, Any]:
    if write and now.astimezone(KST).date().isoformat() != target_date:
        raise ValueError("postclose_runtime_family_write_target_date_not_current")
    authorization = _load_json(STANDING_AUTHORIZATION_PATH)
    r3_path = ai_quality_cycle.r3_manifest_path(target_date)
    rolling_path = ai_quality_cycle.rolling_report_path(target_date)
    r3 = _load_json(r3_path)
    rolling = _load_json(rolling_path)
    queue = approval.load_queue(queue_path, now=now)
    queue, _ = approval.sync_queue(
        queue,
        source_candidates=[],
        source_path=None,
        as_of_date=date.fromisoformat(target_date),
        now=now,
        apply_receipt_dir=apply_receipt_dir,
        runtime_registry=approval.TRUSTED_RUNTIME_FAMILY_REGISTRY,
    )
    attribution_records: list[tuple[Mapping[str, Any], dict[str, Any], Path]] = []
    attribution_paths: list[Path] = []
    attribution_blockers: list[dict[str, str]] = []
    # Recover idempotently when a prior run durably wrote the attribution
    # receipt but exited before persisting the queue/carry-forward candidate.
    for entry in queue.get("candidates") or []:
        if (
            not isinstance(entry, Mapping)
            or entry.get("state") != approval.STATE_POST_APPLY_ATTRIBUTED
            or approval._candidate_runtime_family(entry.get("candidate") or {})
            != approval.MAIN_AI_QUALITY_RUNTIME_FAMILY
        ):
            continue
        attribution_path = Path(str(entry.get("post_apply_attribution_receipt") or ""))
        attribution = _load_json(attribution_path)
        if attribution.get("target_date") != target_date:
            continue
        attribution_records.append((entry, attribution, attribution_path))
        attribution_paths.append(attribution_path)
    for entry in queue.get("candidates") or []:
        if (
            not isinstance(entry, Mapping)
            or entry.get("state") != approval.STATE_APPLIED
        ):
            continue
        if approval._candidate_runtime_family(entry.get("candidate") or {}) != (
            approval.MAIN_AI_QUALITY_RUNTIME_FAMILY
        ):
            continue
        try:
            attribution = build_post_apply_attribution_receipt(
                entry=entry,
                rolling=rolling,
                target_date=target_date,
                now=now,
            )
        except (TypeError, ValueError) as exc:
            attribution_blockers.append(
                {
                    "candidate_sha256": str(entry.get("candidate_sha256") or ""),
                    "reason": str(exc),
                }
            )
            continue
        attribution_path = apply_receipt_dir / (
            f"{target_date}_{str(entry.get('candidate_sha256') or '')[:16]}_"
            "post_apply.json"
        )
        if write:
            _atomic_write_json(attribution_path, attribution)
        attribution_records.append((entry, attribution, attribution_path))
        attribution_paths.append(attribution_path)
    if len(attribution_records) > 1:
        raise ValueError("post_apply_attribution_candidate_not_unique")
    if attribution_paths:
        queue, _ = approval.sync_queue(
            queue,
            source_candidates=[],
            source_path=None,
            as_of_date=date.fromisoformat(target_date),
            now=now,
            apply_receipt_dir=apply_receipt_dir,
            runtime_registry=approval.TRUSTED_RUNTIME_FAMILY_REGISTRY,
        )
        # Persist the POST_APPLY_ATTRIBUTED transition before attempting to
        # materialize a later candidate.  A missing next candidate must never
        # erase the completed attribution or leave auto-chain state ambiguous.
        if write:
            approval._atomic_write_json(queue_path, queue)
    continuation = bool(attribution_records)
    if continuation:
        if write and not _exact_enrolled_continuation(queue):
            raise ValueError("post_apply_enrollment_not_validated")
        attributed_entry, attribution, attribution_path = attribution_records[0]
        candidate = build_post_apply_continuation_candidate(
            entry=attributed_entry,
            attribution=attribution,
            attribution_path=attribution_path,
            rolling=rolling,
            target_date=target_date,
        )
        candidate_source_path = rolling_path
    else:
        candidate = build_promotion_candidate(
            authorization=authorization,
            r3_manifest=r3,
            rolling=rolling,
            approval_queue=queue,
            now=now,
        )
        candidate_source_path = r3_path
    queue, rejections = approval.sync_queue(
        queue,
        source_candidates=[candidate],
        source_path=candidate_source_path,
        as_of_date=date.fromisoformat(target_date),
        now=now,
        apply_receipt_dir=apply_receipt_dir,
        runtime_registry=approval.TRUSTED_RUNTIME_FAMILY_REGISTRY,
    )
    if rejections:
        raise ValueError(
            "promotion_candidate_intake_rejected:" + json.dumps(rejections)
        )
    if continuation and write:
        scheduled = [
            entry
            for entry in queue.get("candidates") or []
            if isinstance(entry, Mapping)
            and entry.get("candidate_sha256") == candidate.get("candidate_sha256")
        ]
        if (
            len(scheduled) != 1
            or scheduled[0].get("state") != approval.STATE_AUTO_CHAIN_ELIGIBLE
        ):
            raise ValueError("post_apply_continuation_not_auto_chain_eligible")
    decision_path: Path | None = None
    first_approval_required = candidate.get("first_operator_approval_required") is True
    if first_approval_required and write:
        queue, decision_path = approval.record_operator_decision(
            queue,
            candidate_id=str(candidate["candidate_id"]),
            expected_candidate_sha256=str(candidate["candidate_sha256"]),
            decision="approve",
            operator_authorization_id=str(
                authorization.get("operator_authorization_id") or ""
            ),
            operator_instruction=str(authorization.get("operator_instruction") or ""),
            approval_dir=approval_dir,
            apply_receipt_dir=apply_receipt_dir,
            now=now,
            runtime_registry=approval.TRUSTED_RUNTIME_FAMILY_REGISTRY,
        )
    source_body = {
        "schema": SOURCE_REPORT_SCHEMA,
        "target_date": target_date,
        "candidate_count": 1,
        "policy_promotion_candidates": [candidate],
        "standing_authorization_sha256": authorization.get("artifact_content_sha256"),
        "source_r3_manifest_sha256": r3.get("artifact_content_sha256"),
        "source_rolling_artifact_sha256": rolling.get("artifact_content_sha256"),
        "post_apply_continuation": continuation,
        "post_apply_attribution_receipts": [str(path) for path in attribution_paths],
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    source_report = {**source_body, "artifact_content_sha256": _sha256(source_body)}
    if write:
        _atomic_write_json(source_report_path(target_date), source_report)
        approval._atomic_write_json(queue_path, queue)
    return {
        "status": (
            "post_apply_continuation_queued"
            if continuation and write
            else (
                "post_apply_continuation_ready_dry_run"
                if continuation
                else (
                    "first_exact_candidate_approved_for_next_preopen"
                    if decision_path
                    else (
                        "first_exact_candidate_ready_for_auto_approval_dry_run"
                        if first_approval_required
                        else "bounded_family_candidate_queued"
                    )
                )
            )
        ),
        "candidate_id": candidate["candidate_id"],
        "candidate_sha256": candidate["candidate_sha256"],
        "operator_decision_artifact": str(decision_path) if decision_path else None,
        "post_apply_attribution_receipts": [str(path) for path in attribution_paths],
        "post_apply_attribution_blockers": attribution_blockers,
        "runtime_effect": False,
        "actual_order_submitted": False,
    }


def _preopen(
    *, target_date: str, write: bool, now: datetime, queue_path: Path
) -> dict[str, Any]:
    queue = approval.load_queue(queue_path, now=now)
    matches = [
        row
        for row in queue.get("candidates") or []
        if isinstance(row, Mapping)
        and row.get("state") == approval.STATE_PREOPEN_SCHEDULED
        and row.get("preopen_target_date") == target_date
        and approval._candidate_runtime_family(row.get("candidate") or {})
        == approval.MAIN_AI_QUALITY_RUNTIME_FAMILY
    ]
    if not matches:
        raise ValueError("preopen_exact_family_candidate_missing")
    if len(matches) > 1:
        raise ValueError("preopen_exact_family_candidate_multiple")
    entry = matches[0]
    handoff_path = Path(str(entry.get("preopen_handoff") or ""))
    handoff = _load_json(handoff_path)
    authorization = _load_json(STANDING_AUTHORIZATION_PATH)
    activation_artifact_path = live_policy.activation_path(target_date)
    receipt_path = approval.APPLY_RECEIPT_DIR / (
        f"{target_date}_{str(entry.get('candidate_sha256') or '')[:16]}_applied.json"
    )
    activation = build_preopen_activation(
        handoff_path=handoff_path,
        handoff=handoff,
        candidate=entry.get("candidate") or {},
        authorization=authorization,
        now=now,
        activation_artifact_path=activation_artifact_path,
        apply_receipt_path=receipt_path,
    )
    receipt = apply_receipt(activation)
    if write:
        _atomic_write_json(activation_artifact_path, activation)
        _atomic_write_json(receipt_path, receipt)
    return {
        "status": "applied_guard_passed",
        "activation_path": str(activation_artifact_path),
        "apply_receipt_path": str(receipt_path),
        "candidate_sha256": entry.get("candidate_sha256"),
        "runtime_effect": True,
        "actual_order_submitted": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("postclose", "preopen"), required=True)
    parser.add_argument("--target-date", required=True)
    parser.add_argument("--queue-path", type=Path, default=approval.DEFAULT_QUEUE_PATH)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    target_day = date.fromisoformat(args.target_date)
    current = _cli_now_for_phase(
        phase=args.phase,
        target_day=target_day,
        current=datetime.now(KST),
    )
    exit_code = 0
    try:
        result = (
            _postclose(
                target_date=args.target_date,
                write=args.write,
                now=current,
                queue_path=args.queue_path,
            )
            if args.phase == "postclose"
            else _preopen(
                target_date=args.target_date,
                write=args.write,
                now=current,
                queue_path=args.queue_path,
            )
        )
    except (OSError, TypeError, ValueError) as exc:
        result = {
            "status": "blocked_fail_closed",
            "reason": str(exc),
            "runtime_effect": False,
            "actual_order_submitted": False,
        }
        exit_code = 2
    body = {
        "schema": REPORT_SCHEMA,
        "phase": args.phase,
        "target_date": args.target_date,
        "generated_at_kst": current.isoformat(timespec="seconds"),
        **result,
    }
    if args.write:
        _atomic_write_json(report_path(args.target_date, args.phase), body)
    print(json.dumps(body, ensure_ascii=False))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
