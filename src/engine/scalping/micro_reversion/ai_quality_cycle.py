"""Postclose R0-R3 automation for exact AI decision-quality replay.

The cycle composes the existing Exact-V2 and micro-reversion primitives into a
daily, source-only workflow.  It deliberately stops at an R3 candidate
manifest.  No function in this module changes a live prompt, runtime
environment, order, quantity, provider route, bot process, or safety guard.

The expensive provider step is optional at the API boundary and is enabled by
the scheduled wrapper only with a reviewed pricing artifact plus both a daily
attempt cap and a daily USD cap.  Runtime application remains owned by the
separate exact-candidate approval/PREOPEN receipt chain.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import tempfile
from collections import defaultdict
from dataclasses import asdict
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from statistics import fmean
from typing import Any, Callable, Iterable, Mapping, Sequence
from zoneinfo import ZoneInfo

from src.engine.scalping import ai_decision_quality as quality
from src.engine.scalping.main_lifecycle_journal import (
    BROKER_EXECUTION_PROVENANCE_SCHEMA,
    BROKER_EXECUTION_RAW_ENVELOPE_SCHEMA,
    JOURNAL_SCHEMA,
    KIWOOM_OFFICIAL_REFERENCE_SHA,
    PIPELINE_IDENTITY_SCHEMA,
)
from src.engine.scalping.micro_reversion.contracts import CLEAN_BASELINE_DATE
from src.engine.scalping.micro_reversion.provider_budget import (
    AUTHORITY_CONTRACT as PROVIDER_BUDGET_AUTHORITY_CONTRACT,
)
from src.engine.scalping.micro_reversion.provider_budget import BUDGET_SUMMARY_SCHEMA
from src.utils.constants import DATA_DIR
from src.utils.jsonl_io import existing_or_gzip_path

KST = ZoneInfo("Asia/Seoul")

CYCLE_SCHEMA = "main_ai_quality_postclose_r0_r3_cycle_v1"
PREPARED_SCHEMA = "main_ai_quality_micro_prepared_requests_v1"
ROLLING_SCHEMA = "main_ai_quality_rolling_paired_evaluation_v1"
R3_SCHEMA = "main_ai_quality_source_only_candidate_manifest_v1"
LIFECYCLE_REPORT_SCHEMA = "main_scalping_lifecycle_paired_daily_v1"
LIFECYCLE_WINDOW_EXCLUSION_MANIFEST_SCHEMA = (
    "main_scalping_lifecycle_window_exclusion_manifest_v1"
)

LIFECYCLE_REPORT_AUTHORITY_CONTRACT: dict[str, Any] = {
    "metric_role": "main_scalping_lifecycle_paired_source_quality",
    "decision_authority": "source_only_candidate_evidence",
    "window_policy": "exact_trade_date_scanner_attempt_to_reconciled_final_exit",
    "sample_floor": "one_complete_exact_lineage_lifecycle",
    "primary_decision_metric": "complete_reconciled_lifecycle_coverage",
    "source_quality_gate": (
        "exact_lineage_complete_lifecycle_reconciled_cost_symbol_and_market_depth"
    ),
    "runtime_effect": False,
    "runtime_authority": False,
    "order_authority": False,
    "provider_authority": False,
    "allowed_runtime_apply": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
    "forbidden_uses": [
        "direct_runtime_or_order_apply",
        "provider_model_bot_threshold_price_quantity_or_cap_change",
        "hard_safety_or_broker_guard_bypass",
        "cross_attempt_symbol_or_timestamp_join",
        "label_horizon_as_actual_holding_duration",
        "raw_fallback_without_explicit_main_lifecycle_id_for_promotion",
    ],
}

LIFECYCLE_EXCLUSION_AUTHORITY_CONTRACT: dict[str, Any] = {
    "metric_role": "source_quality_gate",
    "decision_authority": "exact_lifecycle_window_exclusion_only",
    "window_policy": "exact_trade_date_and_main_lifecycle_id",
    "sample_floor": "not_applicable_source_quality_manifest",
    "primary_decision_metric": "excluded_lifecycle_count",
    "source_quality_gate": "row_local_promotion_blocker_taxonomy",
    "evaluation_phase": "before_global_source_contract_gate",
    "exclusion_scope": "exact_main_lifecycle_window",
    "runtime_effect": False,
    "runtime_authority": False,
    "order_authority": False,
    "provider_authority": False,
    "allowed_runtime_apply": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
    "forbidden_uses": [
        "direct_runtime_or_order_apply",
        "provider_model_bot_threshold_price_quantity_or_cap_change",
        "exclude_other_clean_lifecycle_windows",
    ],
}

OFFLINE_AUTHORITY: dict[str, Any] = {
    "decision_authority": "postclose_source_only_ai_quality_research",
    "runtime_effect": False,
    "allowed_runtime_apply": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
}

SUPPORTED_ECONOMIC_STAGES = frozenset({"entry", "holding", "exit"})
EXPECTED_ARMS = (
    "replay_control_exact_no_micro",
    "replay_control_exact_plus_micro",
    "replay_candidate_exact_plus_micro",
)
MIN_TRADING_DAYS = 5
MIN_COMMON_PARENTS = 20
MIN_UNIQUE_SYMBOLS = 10
MIN_BBO_COVERAGE_PCT = 95.0
MIN_DEPTH_COVERAGE_PCT = 90.0
MIN_RELATIVE_UPLIFT_PCT = 1.0
MAX_LIFECYCLE_FINDINGS = 200

REPORT_ROOT = DATA_DIR / "report" / "main_ai_quality_r0_r3"
ECONOMIC_REPORT_ROOT = DATA_DIR / "report" / "micro_reversion_economic_reference"
LIFECYCLE_REPORT_ROOT = DATA_DIR / "report" / "main_scalping_lifecycle_paired"
BRIDGE_REPORT_ROOT = DATA_DIR / "report" / "micro_reversion_ai_quality_bridge"
MICRO_REPORT_ROOT = (
    DATA_DIR / "report" / "ai_micro_reversion_materialized_replay_requests"
)
SOURCE_POLICY_ROOT = DATA_DIR / "policy" / "micro_reversion"


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")


def _sha256(value: Any) -> str:
    raw = value if isinstance(value, bytes) else _canonical_bytes(value)
    return hashlib.sha256(raw).hexdigest()


def _content_hash(value: Mapping[str, Any], hash_field: str) -> str:
    return _sha256({key: item for key, item in value.items() if key != hash_field})


def _atomic_write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, raw_path = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent)
    )
    temp_path = Path(raw_path)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        temp_path.replace(path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise


def _load_json_auto(path: Path) -> dict[str, Any]:
    resolved = existing_or_gzip_path(path)
    if not resolved.exists():
        raise FileNotFoundError(path)
    opener = gzip.open if resolved.suffix == ".gz" else open
    with opener(resolved, "rt", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"json_artifact_not_object:{resolved}")
    return value


def _raw_artifact(path: Path) -> dict[str, Any]:
    resolved = existing_or_gzip_path(path)
    raw = resolved.read_bytes()
    stat = resolved.stat()
    return {
        "logical_path": str(path),
        "resolved_path": str(resolved),
        "compression": "gzip" if resolved.suffix == ".gz" else "plain",
        "stored_sha256": hashlib.sha256(raw).hexdigest(),
        "stored_size_bytes": len(raw),
        "mtime_ns": stat.st_mtime_ns,
    }


def cycle_report_path(target_date: str) -> Path:
    return REPORT_ROOT / f"main_ai_quality_r0_r3_cycle_{target_date}.json"


def prepared_request_path(target_date: str) -> Path:
    return REPORT_ROOT / f"main_ai_quality_micro_prepared_requests_{target_date}.json"


def control_driver_path(target_date: str) -> Path:
    return REPORT_ROOT / f"main_ai_quality_micro_control_driver_{target_date}.json"


def rolling_report_path(target_date: str) -> Path:
    return REPORT_ROOT / f"main_ai_quality_rolling_paired_{target_date}.json"


def r3_manifest_path(target_date: str) -> Path:
    return REPORT_ROOT / f"main_ai_quality_r3_source_candidates_{target_date}.json"


def action_neutral_label_path(target_date: str) -> Path:
    return MICRO_REPORT_ROOT / (
        f"ai_micro_reversion_action_neutral_outcome_labels_{target_date}.json"
    )


def _authority_findings(value: Mapping[str, Any]) -> list[str]:
    findings: list[str] = []
    for field, expected in (
        ("runtime_effect", False),
        ("allowed_runtime_apply", False),
        ("actual_order_submitted", False),
        ("broker_order_forbidden", True),
    ):
        if value.get(field) is not expected:
            findings.append(f"authority_contract_invalid:{field}")
    for field in ("runtime_authority", "order_authority", "provider_authority"):
        if field in value and value.get(field) is not False:
            findings.append(f"authority_contract_invalid:{field}")
    return findings


def validate_source_quality_audit(
    audit: Mapping[str, Any], *, target_date: str
) -> list[str]:
    findings: list[str] = []
    if audit.get("target_date") != target_date:
        findings.append("source_quality_target_date_mismatch")
    summary = audit.get("summary")
    if not isinstance(summary, Mapping):
        return findings + ["source_quality_summary_missing"]
    if summary.get("tuning_input_allowed") is not True:
        findings.append("source_quality_tuning_input_blocked")
    hard_gap_count = int(summary.get("hard_blocking_contract_gap_count") or 0)
    excluded_row_count = int(summary.get("hard_blocking_excluded_row_count") or 0)
    if hard_gap_count != 0:
        findings.append("source_quality_hard_contract_gap")
    if excluded_row_count < 0:
        findings.append("source_quality_exclusion_census_invalid")
    exclusion_receipt_required = hard_gap_count > 0 or excluded_row_count > 0
    if exclusion_receipt_required:
        if summary.get("raw_row_exclusion_applied") is not True:
            findings.append("source_quality_row_exclusion_not_applied")
        manifest = str(summary.get("raw_row_exclusion_manifest") or "").strip()
        if not manifest:
            findings.append("source_quality_exclusion_manifest_missing")
    return findings


def build_prepared_request_artifact(
    *, target_date: str, paired_report: Mapping[str, Any], source: Mapping[str, Any]
) -> dict[str, Any]:
    """Freeze the eligible full request census used by the micro bridge."""

    if target_date < CLEAN_BASELINE_DATE.isoformat():
        raise ValueError("target_date_before_clean_baseline")
    if paired_report.get("schema") != quality.PAIRED_SCHEMA:
        raise ValueError("paired_report_schema_invalid")
    if paired_report.get("target_date") != target_date:
        raise ValueError("paired_report_target_date_mismatch")
    findings = _authority_findings(paired_report)
    if findings:
        raise ValueError(findings[0])
    rows = paired_report.get("requests")
    if not isinstance(rows, list):
        raise ValueError("paired_report_requests_missing")

    prepared: list[dict[str, Any]] = []
    exclusions: list[dict[str, Any]] = []
    seen_trace_ids: set[str] = set()
    for raw in rows:
        if not isinstance(raw, dict):
            exclusions.append({"reason": "prepared_request_not_object"})
            continue
        trace_id = str(raw.get("decision_trace_id") or "").strip()
        stage = str(raw.get("stage") or "").strip().lower()
        reason = ""
        if not trace_id:
            reason = "prepared_request_trace_id_missing"
        elif trace_id in seen_trace_ids:
            reason = "prepared_request_trace_id_duplicate"
        elif stage not in SUPPORTED_ECONOMIC_STAGES:
            reason = "stage_economic_owner_unsupported"
        elif (raw.get("sample_floor") or {}).get("pass") is not True:
            reason = "prepared_request_sample_floor_not_pass"
        elif _authority_findings(raw):
            reason = "prepared_request_authority_invalid"
        elif not str(raw.get("outcome_join_key") or ""):
            reason = "prepared_request_outcome_join_key_missing"
        if reason:
            exclusions.append(
                {
                    "decision_trace_id": trace_id or None,
                    "stage": stage or None,
                    "reason": reason,
                }
            )
            continue
        seen_trace_ids.add(trace_id)
        prepared.append(dict(raw))

    body = {
        "schema": PREPARED_SCHEMA,
        "target_date": target_date,
        "generated_at": datetime.now(KST).isoformat(),
        "status": (
            "prepared_requests_ready" if prepared else "no_supported_prepared_requests"
        ),
        "source_paired_report": dict(source),
        "source_paired_report_content_sha256": _sha256(paired_report),
        "source_request_count": len(rows),
        "prepared_request_count": len(prepared),
        "excluded_request_count": len(exclusions),
        "prepared_requests": prepared,
        "exclusions": exclusions,
        "provider_call_performed": False,
        "metric_role": "r0_exact_prepared_request_census",
        "window_policy": "same_target_date_clean_baseline_exact_v2",
        "primary_decision_metric": "source_quality_adjusted_ev_pct",
        "source_quality_gate": "postclose_audit_and_exact_request_contract",
        "forbidden_uses": [
            "provider_call_without_reviewed_daily_attempt_and_usd_budget",
            "runtime_prompt_apply",
            "order_or_quantity_change",
        ],
        **OFFLINE_AUTHORITY,
    }
    return {**body, "artifact_content_sha256": _sha256(body)}


def _validate_prepared_artifact(value: Mapping[str, Any]) -> None:
    if value.get("schema") != PREPARED_SCHEMA:
        raise ValueError("prepared_artifact_schema_invalid")
    if value.get("artifact_content_sha256") != _content_hash(
        value, "artifact_content_sha256"
    ):
        raise ValueError("prepared_artifact_content_hash_mismatch")
    rows = value.get("prepared_requests")
    if not isinstance(rows, list):
        raise ValueError("prepared_artifact_rows_invalid")
    if value.get("prepared_request_count") != len(rows):
        raise ValueError("prepared_artifact_count_mismatch")
    if _authority_findings(value):
        raise ValueError("prepared_artifact_authority_invalid")


def _finite_number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    result = float(value)
    return result if math.isfinite(result) else None


def _valid_sha256(value: Any) -> bool:
    text = str(value or "")
    return len(text) == 64 and all(
        character in "0123456789abcdef" for character in text
    )


def _percentile(values: Sequence[float], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = max(
        0, min(len(ordered) - 1, math.floor((len(ordered) - 1) * percentile))
    )
    return ordered[position]


def _execution_census_error(reason: str) -> None:
    raise ValueError(f"execution_report_exact_census_invalid:{reason}")


def _execution_string_list(
    value: Any,
    *,
    field: str,
    allow_empty: bool = True,
) -> list[str]:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item.strip() for item in value
    ):
        _execution_census_error(f"{field}_invalid")
    normalized = [str(item) for item in value]
    if (not allow_empty and not normalized) or len(normalized) != len(set(normalized)):
        _execution_census_error(f"{field}_duplicate_or_empty")
    return normalized


def _validate_execution_exact_census(
    *,
    report: Mapping[str, Any],
    results: Sequence[Any],
    evaluation: Mapping[str, Any],
) -> list[Mapping[str, Any]]:
    """Bind one historical result to its exact request/parent/evaluation census."""

    request_count = _native_nonnegative_int(report.get("request_count"))
    parent_count = _native_nonnegative_int(report.get("parent_count"))
    result_count = len(results)
    committed_parent_count = _native_nonnegative_int(
        report.get("committed_parent_count")
    )
    if (
        request_count is None
        or request_count <= 0
        or request_count % len(EXPECTED_ARMS) != 0
        or parent_count != request_count // len(EXPECTED_ARMS)
        or committed_parent_count is None
        or committed_parent_count <= 0
        or result_count != committed_parent_count * len(EXPECTED_ARMS)
    ):
        _execution_census_error("parent_request_result_count_mismatch")

    request_refs_raw = report.get("request_refs")
    if not isinstance(request_refs_raw, list) or len(request_refs_raw) != request_count:
        _execution_census_error("request_refs_count_mismatch")
    request_refs: list[Mapping[str, Any]] = []
    request_by_id: dict[str, Mapping[str, Any]] = {}
    request_ids_by_parent: dict[str, list[str]] = defaultdict(list)
    request_arms_by_parent: dict[str, set[str]] = defaultdict(set)
    request_trace_by_parent: dict[str, set[str]] = defaultdict(set)
    for raw_ref in request_refs_raw:
        if not isinstance(raw_ref, Mapping):
            _execution_census_error("request_ref_not_object")
        parent_id = str(raw_ref.get("paired_replay_parent_id") or "").strip()
        request_id = str(raw_ref.get("paired_replay_id") or "").strip()
        arm = str(raw_ref.get("micro_reversion_replay_arm") or "").strip()
        trace_id = str(raw_ref.get("decision_trace_id") or "").strip()
        if (
            not parent_id
            or not request_id
            or request_id in request_by_id
            or arm not in EXPECTED_ARMS
            or not trace_id
            or any(
                not _valid_sha256(raw_ref.get(field))
                for field in (
                    "candidate_input_sha256",
                    "prompt_sha256",
                    "prompt_contract_sha256",
                )
            )
        ):
            _execution_census_error("request_ref_identity_or_hash_invalid")
        request_refs.append(raw_ref)
        request_by_id[request_id] = raw_ref
        request_ids_by_parent[parent_id].append(request_id)
        request_arms_by_parent[parent_id].add(arm)
        request_trace_by_parent[parent_id].add(trace_id)
    if len(request_ids_by_parent) != parent_count or any(
        len(request_ids_by_parent[parent_id]) != len(EXPECTED_ARMS)
        or request_arms_by_parent[parent_id] != set(EXPECTED_ARMS)
        or len(request_trace_by_parent[parent_id]) != 1
        for parent_id in request_ids_by_parent
    ):
        _execution_census_error("request_parent_arm_census_mismatch")

    result_ids: list[str] = []
    result_request_ids: list[str] = []
    result_by_parent: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    result_arms_by_parent: dict[str, set[str]] = defaultdict(set)
    provider_attempts: list[Mapping[str, Any]] = []
    provider_actual_costs_by_result_id: dict[str, list[Decimal]] = {}
    provider_response_hash_observed = False
    for raw_result in results:
        if not isinstance(raw_result, Mapping):
            _execution_census_error("result_not_object")
        result = raw_result
        result_id = str(result.get("result_id") or "").strip()
        request_id = str(result.get("paired_replay_id") or "").strip()
        parent_id = str(result.get("paired_replay_parent_id") or "").strip()
        arm = str(result.get("micro_reversion_replay_arm") or "").strip()
        request_ref = request_by_id.get(request_id)
        replay_result = result.get("replay_result")
        candidate_response = (
            replay_result.get("candidate_response")
            if isinstance(replay_result, Mapping)
            else None
        )
        candidate_attempts = (
            replay_result.get("candidate_attempts")
            if isinstance(replay_result, Mapping)
            else None
        )
        if not isinstance(candidate_attempts, list) or any(
            not isinstance(attempt, Mapping) for attempt in candidate_attempts
        ):
            _execution_census_error("result_provider_attempt_census_invalid")
        result_provider_attempts = [
            attempt
            for attempt in candidate_attempts
            if str(
                (
                    attempt.get("provider_provenance")
                    if isinstance(attempt.get("provider_provenance"), Mapping)
                    else {}
                ).get("provider")
                or ""
            )
            .strip()
            .lower()
            not in {"", "none", "deterministic_offline_adapter"}
        ]
        if not result_provider_attempts:
            _execution_census_error("result_provider_attempt_missing")
        for attempt in result_provider_attempts:
            provenance = attempt.get("provider_provenance")
            if not isinstance(provenance, Mapping):
                _execution_census_error("result_provider_provenance_invalid")
            response_hash = next(
                (
                    provenance.get(field)
                    for field in (
                        "response_sha256",
                        "canonical_response_sha256",
                        "bedrock_response_sha256",
                    )
                    if provenance.get(field) is not None
                ),
                None,
            )
            try:
                reserved_cost = Decimal(
                    str(provenance.get("provider_budget_reserved_cost_usd"))
                )
                actual_cost = Decimal(
                    str(provenance.get("provider_budget_actual_cost_usd"))
                )
            except (InvalidOperation, TypeError, ValueError):
                reserved_cost = Decimal("NaN")
                actual_cost = Decimal("NaN")
            if (
                not str(provenance.get("provider") or "").strip()
                or not str(provenance.get("model") or "").strip()
                or provenance.get("provider_none") is not False
                or provenance.get("provider_call_attempted") is not True
                or provenance.get("provider_call_succeeded") is not True
                or not str(provenance.get("transport") or "").strip()
                or not str(provenance.get("source_transport_contract") or "").strip()
                or not _valid_sha256(response_hash)
                or (
                    not str(provenance.get("response_id") or "").strip()
                    and not str(
                        provenance.get("response_id_unavailable_reason") or ""
                    ).strip()
                )
                or not str(
                    provenance.get("provider_budget_reservation_id") or ""
                ).strip()
                or not _valid_sha256(
                    provenance.get("provider_budget_attempt_identity_sha256")
                )
                or provenance.get("provider_budget_settled") is not True
                or provenance.get("provider_budget_unknown_usage_reservation_retained")
                is not False
                or provenance.get("provider_budget_circuit_breaker_open") is not False
                or not reserved_cost.is_finite()
                or reserved_cost < 0
                or not actual_cost.is_finite()
                or actual_cost < 0
                or actual_cost > reserved_cost
            ):
                _execution_census_error("result_provider_provenance_invalid")
            provider_response_hash_observed = True
        provider_attempts.extend(result_provider_attempts)
        expected_result_id = (
            "micro-result-"
            + _sha256(
                {key: value for key, value in result.items() if key != "result_id"}
            )[:24]
        )
        if (
            not result_id
            or result_id != expected_result_id
            or result_id in result_ids
            or not request_id
            or request_id in result_request_ids
            or request_ref is None
            or parent_id != request_ref.get("paired_replay_parent_id")
            or arm != request_ref.get("micro_reversion_replay_arm")
            or result.get("decision_trace_id") != request_ref.get("decision_trace_id")
            or result.get("candidate_input_sha256")
            != request_ref.get("candidate_input_sha256")
            or result.get("prompt_sha256") != request_ref.get("prompt_sha256")
            or result.get("prompt_contract_sha256")
            != request_ref.get("prompt_contract_sha256")
            or not _valid_sha256(result.get("source_exact_payload_sha256"))
            or not _valid_sha256(result.get("outcome_label_content_sha256"))
            or not str(result.get("outcome_join_key") or "").strip()
            or not isinstance(replay_result, Mapping)
            or replay_result.get("status") != "pass"
            or not isinstance(candidate_response, Mapping)
            or result.get("candidate_response_content_sha256")
            != _sha256(candidate_response)
            or _authority_findings(result)
        ):
            _execution_census_error("result_identity_content_or_hash_invalid")
        result_ids.append(result_id)
        provider_actual_costs_by_result_id[result_id] = [
            Decimal(
                str(
                    (
                        attempt.get("provider_provenance")
                        if isinstance(attempt.get("provider_provenance"), Mapping)
                        else {}
                    ).get("provider_budget_actual_cost_usd")
                )
            )
            for attempt in result_provider_attempts
        ]
        result_request_ids.append(request_id)
        result_by_parent[parent_id].append(result)
        result_arms_by_parent[parent_id].add(arm)
    if len(result_by_parent) != committed_parent_count or any(
        len(parent_results) != len(EXPECTED_ARMS)
        or result_arms_by_parent[parent_id] != set(EXPECTED_ARMS)
        for parent_id, parent_results in result_by_parent.items()
    ):
        _execution_census_error("result_parent_arm_census_mismatch")
    if report.get("result_ids") != result_ids:
        _execution_census_error("result_ids_order_or_content_mismatch")
    if (
        report.get("provider_call_attempted") is not bool(provider_attempts)
        or report.get("provider_call_performed") is not bool(provider_attempts)
        or report.get("provider_call_succeeded") is not bool(provider_attempts)
        or report.get("provider_response_hash_observed")
        is not provider_response_hash_observed
        or report.get("outcomes_embedded_in_provider_input") is not False
    ):
        _execution_census_error("provider_execution_receipt_census_mismatch")

    deferred_ids = _execution_string_list(
        report.get("deferred_request_ids"),
        field="deferred_request_ids",
    )
    expected_deferred_ids = [
        str(ref.get("paired_replay_id"))
        for ref in request_refs
        if str(ref.get("paired_replay_id")) not in set(result_request_ids)
    ]
    deferred_count = _native_nonnegative_int(report.get("deferred_request_count"))
    if deferred_ids != expected_deferred_ids or deferred_count != len(deferred_ids):
        _execution_census_error("deferred_request_census_mismatch")

    new_result_ids = _execution_string_list(
        report.get("new_result_ids"),
        field="new_result_ids",
    )
    new_result_count = _native_nonnegative_int(report.get("new_result_count"))
    if new_result_count != len(new_result_ids) or any(
        result_id not in set(result_ids) for result_id in new_result_ids
    ):
        _execution_census_error("new_result_census_mismatch")
    provider_budget = report.get("provider_budget")
    if (
        not isinstance(provider_budget, Mapping)
        or provider_budget.get("schema") != BUDGET_SUMMARY_SCHEMA
        or any(
            provider_budget.get(field) != expected
            for field, expected in PROVIDER_BUDGET_AUTHORITY_CONTRACT.items()
        )
        or not _valid_sha256(provider_budget.get("pricing_artifact_content_sha256"))
    ):
        _execution_census_error("provider_budget_reference_hash_invalid")
    try:
        committed_cost = Decimal(str(provider_budget.get("committed_cost_usd")))
    except (InvalidOperation, TypeError, ValueError):
        committed_cost = Decimal("NaN")
    current_result_actual_cost = sum(
        (
            cost
            for result_id in new_result_ids
            for cost in provider_actual_costs_by_result_id[result_id]
        ),
        Decimal(0),
    )
    if not committed_cost.is_finite() or committed_cost < current_result_actual_cost:
        _execution_census_error("provider_budget_current_result_cost_underreported")
    new_results = [
        result
        for result in results
        if str(result.get("result_id") or "") in set(new_result_ids)
    ]
    if new_result_ids != [str(result.get("result_id") or "") for result in new_results]:
        _execution_census_error("new_result_order_mismatch")
    expected_selected_request_ids = [
        str(result.get("paired_replay_id") or "") for result in new_results
    ]
    selected_request_ids = _execution_string_list(
        report.get("selected_request_ids"),
        field="selected_request_ids",
    )
    expected_selected_parent_ids = list(
        dict.fromkeys(
            str(result.get("paired_replay_parent_id") or "") for result in new_results
        )
    )
    selected_parent_ids = _execution_string_list(
        report.get("selected_parent_ids"),
        field="selected_parent_ids",
    )
    new_parent_ids = set(expected_selected_parent_ids)
    checkpoint_resume_count = _native_nonnegative_int(
        report.get("checkpoint_resume_result_count")
    )
    provisional_checkpoint_count = _native_nonnegative_int(
        report.get("provisional_checkpoint_result_count")
    )
    reused_result_count = _native_nonnegative_int(report.get("reused_result_count"))
    newly_committed_parent_count = _native_nonnegative_int(
        report.get("newly_committed_parent_count")
    )
    max_new_requests = _native_nonnegative_int(report.get("max_new_requests"))
    expected_reused_count = sum(
        str(result.get("result_id") or "") not in set(new_result_ids)
        and str(result.get("paired_replay_parent_id") or "") not in new_parent_ids
        for result in results
    )
    expected_provisional_count = sum(
        str(result.get("result_id") or "") not in set(new_result_ids)
        and str(result.get("paired_replay_parent_id") or "") in new_parent_ids
        for result in results
    )
    if (
        selected_request_ids != expected_selected_request_ids
        or selected_parent_ids != expected_selected_parent_ids
        or checkpoint_resume_count != result_count - new_result_count
        or provisional_checkpoint_count != expected_provisional_count
        or reused_result_count != expected_reused_count
        or newly_committed_parent_count != len(new_parent_ids)
        or max_new_requests is None
        or max_new_requests <= 0
        or new_result_count > max_new_requests
        or report.get("candidate_model_call_attempted") is not bool(new_results)
    ):
        _execution_census_error("checkpoint_selected_or_reused_census_mismatch")

    exclusions = report.get("execution_exclusions")
    if not isinstance(exclusions, list):
        _execution_census_error("execution_exclusions_invalid")
    seen_excluded_request_ids: set[str] = set()
    deferred_id_set = set(deferred_ids)
    for exclusion in exclusions:
        if not isinstance(exclusion, Mapping):
            _execution_census_error("execution_exclusion_not_object")
        request_id = str(exclusion.get("paired_replay_id") or "")
        request_ref = request_by_id.get(request_id)
        if (
            request_ref is None
            or request_id not in deferred_id_set
            or request_id in seen_excluded_request_ids
            or exclusion.get("paired_replay_parent_id")
            != request_ref.get("paired_replay_parent_id")
            or exclusion.get("micro_reversion_replay_arm")
            != request_ref.get("micro_reversion_replay_arm")
            or not str(exclusion.get("reason") or "").strip()
        ):
            _execution_census_error("execution_exclusion_binding_invalid")
        seen_excluded_request_ids.add(request_id)

    outcome_joins = report.get("outcome_joins")
    if not isinstance(outcome_joins, list):
        _execution_census_error("outcome_join_census_invalid")
    outcome_by_key: dict[str, Mapping[str, Any]] = {}
    for outcome_join in outcome_joins:
        if not isinstance(outcome_join, Mapping):
            _execution_census_error("outcome_join_not_object")
        join_key = str(outcome_join.get("outcome_join_key") or "").strip()
        if (
            not join_key
            or join_key in outcome_by_key
            or (not _valid_sha256(outcome_join.get("outcome_label_content_sha256")))
            or not str(outcome_join.get("decision_trace_id") or "").strip()
            or not str(outcome_join.get("effective_venue") or "").strip()
            or not str(outcome_join.get("session_bucket") or "").strip()
            or outcome_join.get("label_status") not in {"partial", "mature"}
            or outcome_join.get("outcome_embedded_in_provider_input") is not False
        ):
            _execution_census_error("outcome_join_identity_invalid")
        outcome_by_key[join_key] = outcome_join
    result_outcome_keys = {
        str(result.get("outcome_join_key") or "") for result in results
    }
    if set(outcome_by_key) != result_outcome_keys or any(
        result.get("outcome_label_content_sha256")
        != outcome_by_key[str(result.get("outcome_join_key"))].get(
            "outcome_label_content_sha256"
        )
        or result.get("decision_trace_id")
        != outcome_by_key[str(result.get("outcome_join_key"))].get("decision_trace_id")
        for result in results
    ):
        _execution_census_error("outcome_join_result_binding_mismatch")

    evaluation_rows = evaluation.get("rows")
    evaluation_exclusions = evaluation.get("exclusions")
    if (
        evaluation.get("schema") != "ai_micro_reversion_three_arm_evaluation_v1"
        or evaluation.get("status") != "evaluated"
        or _authority_findings(evaluation)
        or not isinstance(evaluation_rows, list)
        or not isinstance(evaluation_exclusions, list)
        or evaluation_exclusions
        or evaluation.get("complete_parent_count") != len(evaluation_rows)
        or evaluation.get("excluded_parent_count") != 0
        or len(evaluation_rows) != committed_parent_count
    ):
        _execution_census_error("evaluation_top_level_census_mismatch")
    evaluation_by_parent: dict[str, Mapping[str, Any]] = {}
    for raw_row in evaluation_rows:
        if not isinstance(raw_row, Mapping):
            _execution_census_error("evaluation_row_not_object")
        parent_id = str(raw_row.get("paired_replay_parent_id") or "").strip()
        parent_results = result_by_parent.get(parent_id)
        arms = raw_row.get("arms")
        if (
            not parent_id
            or parent_id in evaluation_by_parent
            or parent_results is None
            or not isinstance(arms, Mapping)
            or set(arms) != set(EXPECTED_ARMS)
        ):
            _execution_census_error("evaluation_parent_arm_census_mismatch")
        expected_trace_ids = {
            str(result.get("decision_trace_id") or "") for result in parent_results
        }
        expected_join_keys = {
            str(result.get("outcome_join_key") or "") for result in parent_results
        }
        expected_label_hashes = {
            str(result.get("outcome_label_content_sha256") or "")
            for result in parent_results
        }
        if (
            len(expected_trace_ids) != 1
            or raw_row.get("decision_trace_id") not in expected_trace_ids
            or len(expected_join_keys) != 1
            or raw_row.get("outcome_join_key") not in expected_join_keys
            or len(expected_label_hashes) != 1
            or raw_row.get("outcome_label_content_sha256") not in expected_label_hashes
            or quality._venue(raw_row.get("effective_venue"))
            != quality._venue(
                outcome_by_key[str(raw_row.get("outcome_join_key"))].get(
                    "effective_venue"
                )
            )
            or quality._session(raw_row.get("session_bucket"))
            != quality._session(
                outcome_by_key[str(raw_row.get("outcome_join_key"))].get(
                    "session_bucket"
                )
            )
        ):
            _execution_census_error("evaluation_result_identity_binding_mismatch")

        row_stage = str(raw_row.get("decision_stage") or "").strip().lower()
        cost_adjusted_outcome = _finite_number(raw_row.get("cost_adjusted_outcome_pct"))
        mae_pct = _finite_number(raw_row.get("mae_pct"))
        first_hit = str(raw_row.get("first_hit") or "")
        if (
            row_stage not in SUPPORTED_ECONOMIC_STAGES
            or cost_adjusted_outcome is None
            or mae_pct is None
            or not re.fullmatch(r"[0-9]{6}", str(raw_row.get("stock_code") or ""))
        ):
            _execution_census_error("evaluation_outcome_metric_invalid")
        if not all(
            _valid_sha256(raw_row.get(field))
            for field in (
                "cost_profile_artifact_sha256",
                "cost_catalog_content_sha256",
                "selected_cost_profile_content_sha256",
                "symbol_master_artifact_sha256",
                "symbol_metadata_record_sha256",
            )
        ):
            _execution_census_error("evaluation_economic_reference_hash_invalid")
        if not str(raw_row.get("selected_cost_profile_id") or "").strip():
            _execution_census_error("evaluation_cost_profile_id_missing")
        result_by_arm = {
            str(result.get("micro_reversion_replay_arm") or ""): result
            for result in parent_results
        }
        base_notional_values: list[float] = []
        for arm in EXPECTED_ARMS:
            result = result_by_arm[arm]
            replay_result = result.get("replay_result")
            assert isinstance(replay_result, Mapping)
            response = replay_result.get("candidate_response")
            assert isinstance(response, Mapping)
            result_stage = (
                str(replay_result.get("stage") or result.get("stage") or "")
                .strip()
                .lower()
            )
            response_action = str(response.get("action") or "UNKNOWN").upper()
            exposure_role, exposure_fraction = quality._micro_reversion_action_exposure(
                result_stage,
                response_action,
                dict(response),
            )
            arm_value = arms[arm]
            if not isinstance(arm_value, Mapping):
                _execution_census_error("evaluation_arm_value_not_object")
            standardized_probe = exposure_role == "standardized_probe_observation_only"
            economic_observation = bool(exposure_fraction) or standardized_probe
            expected_signal_selected = exposure_role in {
                "full_entry_exposure",
                "standardized_probe_observation_only",
                "existing_position_exposure",
            }
            expected_ev = (
                cost_adjusted_outcome * exposure_fraction
                if exposure_fraction is not None
                else None
            )
            expected_probe_ev = cost_adjusted_outcome if standardized_probe else None

            def same_optional_number(observed: Any, expected: float | None) -> bool:
                observed_number = _finite_number(observed)
                if expected is None:
                    return observed is None
                return observed_number is not None and math.isclose(
                    observed_number,
                    expected,
                    rel_tol=0.0,
                    abs_tol=1e-12,
                )

            if (
                result_stage != row_stage
                or str(result.get("stage") or "").strip().lower() != row_stage
                or arm_value.get("action") != response_action
                or arm_value.get("exposure_role") != exposure_role
                or not same_optional_number(
                    arm_value.get("exposure_fraction"), exposure_fraction
                )
                or arm_value.get("economic_signal_selected")
                is not expected_signal_selected
                or not same_optional_number(
                    arm_value.get("source_quality_adjusted_ev_pct"), expected_ev
                )
                or not same_optional_number(
                    arm_value.get("standardized_probe_observation_ev_pct"),
                    expected_probe_ev,
                )
                or arm_value.get("adverse_exposure")
                is not bool(economic_observation and mae_pct < 0)
                or arm_value.get("severe_tail_exposure")
                is not bool(economic_observation and mae_pct <= -3.0)
                or arm_value.get("after_cost_target_first")
                is not bool(
                    economic_observation
                    and cost_adjusted_outcome > 0
                    and first_hit in {"target", "target_first", "net_target_first"}
                )
            ):
                _execution_census_error("evaluation_result_semantic_binding_invalid")
            notional_eligible = arm_value.get("notional_net_profit_eligible")
            notional_value = _finite_number(
                arm_value.get("notional_incremental_value_krw")
            )
            if notional_eligible is True:
                if (
                    exposure_fraction is None
                    or exposure_fraction <= 0
                    or notional_value is None
                ):
                    _execution_census_error("evaluation_notional_semantics_invalid")
                base_notional_values.append(notional_value / exposure_fraction)
            elif (
                notional_eligible is not False
                or arm_value.get("notional_incremental_value_krw") is not None
            ):
                _execution_census_error("evaluation_notional_semantics_invalid")
        if base_notional_values and any(
            not math.isclose(
                value,
                base_notional_values[0],
                rel_tol=0.0,
                abs_tol=1e-8,
            )
            for value in base_notional_values[1:]
        ):
            _execution_census_error("evaluation_notional_base_mismatch")
        evaluation_by_parent[parent_id] = raw_row
    if set(evaluation_by_parent) != set(result_by_parent):
        _execution_census_error("evaluation_result_parent_set_mismatch")

    sample_floor = evaluation.get("sample_floor")
    arm_metrics = evaluation.get("arm_metrics")
    partitions = evaluation.get("stage_venue_partitions")
    if (
        not isinstance(sample_floor, Mapping)
        or sample_floor.get("observed_rows") != len(evaluation_rows)
        or not isinstance(arm_metrics, Mapping)
        or set(arm_metrics) != set(EXPECTED_ARMS)
        or any(
            not isinstance(arm_metrics[arm], Mapping)
            or arm_metrics[arm].get("row_count") != len(evaluation_rows)
            for arm in EXPECTED_ARMS
        )
        or not isinstance(partitions, list)
        or not partitions
    ):
        _execution_census_error("evaluation_aggregate_census_mismatch")
    partition_counts: dict[tuple[str, str, str], int] = {}
    for partition in partitions:
        if not isinstance(partition, Mapping):
            _execution_census_error("evaluation_partition_not_object")
        key = (
            str(partition.get("decision_stage") or ""),
            str(partition.get("effective_venue") or ""),
            str(partition.get("session_bucket") or ""),
        )
        complete_count = _native_nonnegative_int(partition.get("complete_parent_count"))
        partition_metrics = partition.get("arm_metrics")
        if (
            not all(key)
            or key in partition_counts
            or complete_count is None
            or complete_count <= 0
            or not isinstance(partition_metrics, Mapping)
            or set(partition_metrics) != set(EXPECTED_ARMS)
            or any(
                not isinstance(partition_metrics[arm], Mapping)
                or partition_metrics[arm].get("row_count") != complete_count
                for arm in EXPECTED_ARMS
            )
        ):
            _execution_census_error("evaluation_partition_census_invalid")
        partition_counts[key] = complete_count
    expected_partition_counts: dict[tuple[str, str, str], int] = defaultdict(int)
    for row in evaluation_rows:
        expected_partition_counts[
            (
                str(row.get("decision_stage") or ""),
                str(row.get("effective_venue") or ""),
                str(row.get("session_bucket") or ""),
            )
        ] += 1
    if partition_counts != dict(expected_partition_counts):
        _execution_census_error("evaluation_partition_parent_census_mismatch")
    return [row for row in evaluation_rows if isinstance(row, Mapping)]


def _validated_execution_rows(report: Mapping[str, Any]) -> list[dict[str, Any]]:
    if report.get("schema") != quality.MICRO_REVERSION_EXECUTION_RESULT_SCHEMA:
        raise ValueError("execution_report_schema_invalid")
    if report.get("report_content_sha256") != _content_hash(
        report, "report_content_sha256"
    ):
        raise ValueError("execution_report_content_hash_mismatch")
    if _authority_findings(report):
        raise ValueError("execution_report_authority_invalid")
    try:
        report_date = date.fromisoformat(str(report.get("target_date") or ""))
    except ValueError as exc:
        raise ValueError("execution_report_target_date_invalid") from exc
    if report_date < CLEAN_BASELINE_DATE:
        raise ValueError("execution_report_before_clean_baseline")
    if any(
        not _valid_sha256(report.get(field))
        for field in (
            "materialized_report_content_sha256",
            "materialized_request_census_sha256",
            "materialized_report_artifact_sha256",
            "outcome_label_artifact_sha256",
        )
    ):
        raise ValueError("execution_report_source_artifact_hash_missing")
    results = report.get("results")
    if not isinstance(results, list):
        raise ValueError("execution_report_results_invalid")
    if any(not isinstance(result, Mapping) for result in results):
        raise ValueError("execution_report_result_invalid")
    result_count = len(results)
    request_count = report.get("request_count")
    status = report.get("status")
    deferred_request_count = _native_nonnegative_int(
        report.get("deferred_request_count")
    )
    uncommitted_result_count = _native_nonnegative_int(
        report.get("uncommitted_result_count")
    )
    newly_committed_parent_count = report.get("newly_committed_parent_count")
    new_result_count = report.get("new_result_count")
    execution_exclusions = report.get("execution_exclusions")
    blocking_execution_exclusions = report.get("blocking_execution_exclusions")
    provider_budget = report.get("provider_budget")
    if (
        status not in quality.MICRO_REVERSION_EXECUTION_SUCCESS_STATUSES
        or report.get("execution_requested") is not True
        or report.get("provider_call_attempted") is not True
        or report.get("provider_call_performed") is not True
        or report.get("provider_call_succeeded") is not True
        or report.get("result_count") != result_count
        or isinstance(request_count, bool)
        or not isinstance(request_count, int)
        or request_count < result_count
        or result_count <= 0
        or result_count % len(EXPECTED_ARMS) != 0
        or _native_nonnegative_int(report.get("execution_failed_count")) != 0
        or not isinstance(execution_exclusions, list)
        or report.get("execution_exclusion_count") != len(execution_exclusions)
        or not isinstance(blocking_execution_exclusions, list)
        or report.get("blocking_execution_exclusion_count")
        != len(blocking_execution_exclusions)
        or bool(blocking_execution_exclusions)
        or uncommitted_result_count != 0
        or _native_nonnegative_int(report.get("provider_provenance_pass_count"))
        != result_count
        or report.get("provider_budget_contract_findings") != []
    ):
        raise ValueError("execution_report_not_complete_provider_verified")
    if not isinstance(provider_budget, Mapping) or (
        quality._micro_reversion_execution_budget_findings(
            report=report,
            budget_summary=provider_budget,
        )
    ):
        raise ValueError("execution_report_provider_budget_invalid")
    if status == "offline_three_arm_execution_complete" and (
        request_count != result_count
        or deferred_request_count != 0
        or bool(execution_exclusions)
    ):
        raise ValueError("execution_report_full_census_invalid")
    if status == "offline_three_arm_execution_batch_complete" and (
        request_count <= result_count
        or deferred_request_count != request_count - result_count
        or isinstance(newly_committed_parent_count, bool)
        or not isinstance(newly_committed_parent_count, int)
        or newly_committed_parent_count < 0
        or isinstance(new_result_count, bool)
        or not isinstance(new_result_count, int)
        or new_result_count < 0
        or (
            newly_committed_parent_count == 0
            and (
                new_result_count != 0
                or report.get("selected_request_ids") != []
                or report.get("candidate_model_call_attempted") is not False
            )
        )
        or (
            newly_committed_parent_count > 0
            and (
                new_result_count <= 0
                or report.get("candidate_model_call_attempted") is not True
            )
        )
    ):
        raise ValueError("execution_report_batch_census_invalid")
    evaluation = report.get("three_arm_evaluation")
    if not isinstance(evaluation, Mapping):
        raise ValueError("three_arm_evaluation_missing")
    declared_evaluation_hash = evaluation.get("evaluation_content_sha256")
    evaluation_without_hash = {
        key: item
        for key, item in evaluation.items()
        if key != "evaluation_content_sha256"
    }
    if declared_evaluation_hash != _sha256(evaluation_without_hash):
        raise ValueError("three_arm_evaluation_content_hash_mismatch")
    rows = _validate_execution_exact_census(
        report=report,
        results=results,
        evaluation=evaluation,
    )

    result_contracts: dict[str, dict[str, str]] = defaultdict(dict)
    for result in results:
        if not isinstance(result, Mapping):
            raise ValueError("execution_report_result_invalid")
        replay_result = result.get("replay_result")
        if (
            not isinstance(replay_result, Mapping)
            or replay_result.get("status") != "pass"
        ):
            raise ValueError("execution_report_result_not_pass")
        parent = str(result.get("paired_replay_parent_id") or "")
        arm = str(result.get("micro_reversion_replay_arm") or "")
        contract_hash = str(result.get("prompt_contract_sha256") or "")
        if parent and arm and contract_hash:
            result_contracts[parent][arm] = contract_hash
    completed_parent_ids = {
        parent_id
        for parent_id, contracts in result_contracts.items()
        if set(contracts) == set(EXPECTED_ARMS)
    }
    for exclusion in execution_exclusions:
        if (
            not isinstance(exclusion, Mapping)
            or not str(exclusion.get("paired_replay_parent_id") or "")
            or str(exclusion.get("paired_replay_parent_id") or "")
            in completed_parent_ids
        ):
            raise ValueError("execution_report_exclusion_scope_invalid")

    normalized: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, Mapping):
            _execution_census_error("evaluation_row_not_object_after_validation")
        parent = str(row.get("paired_replay_parent_id") or "")
        arms = row.get("arms")
        contracts = result_contracts.get(parent, {})
        if not parent or not isinstance(arms, Mapping):
            _execution_census_error("evaluation_row_shape_invalid")
        if set(arms) != set(EXPECTED_ARMS) or set(contracts) != set(EXPECTED_ARMS):
            _execution_census_error("evaluation_result_arm_binding_mismatch")
        micro_control = arms["replay_control_exact_plus_micro"]
        candidate = arms["replay_candidate_exact_plus_micro"]
        if not isinstance(micro_control, Mapping) or not isinstance(candidate, Mapping):
            _execution_census_error("evaluation_economic_arm_invalid")
        control_ev = _finite_number(micro_control.get("source_quality_adjusted_ev_pct"))
        candidate_ev = _finite_number(candidate.get("source_quality_adjusted_ev_pct"))
        if control_ev is None or candidate_ev is None:
            _execution_census_error("evaluation_economic_metric_invalid")
        reference_fields = {
            "cost_profile_artifact_sha256": row.get("cost_profile_artifact_sha256"),
            "cost_catalog_content_sha256": row.get("cost_catalog_content_sha256"),
            "selected_cost_profile_content_sha256": row.get(
                "selected_cost_profile_content_sha256"
            ),
            "symbol_master_artifact_sha256": row.get("symbol_master_artifact_sha256"),
            "symbol_metadata_record_sha256": row.get("symbol_metadata_record_sha256"),
        }
        if not all(_valid_sha256(value) for value in reference_fields.values()):
            _execution_census_error("evaluation_economic_reference_hash_invalid")
        selected_profile_id = str(row.get("selected_cost_profile_id") or "").strip()
        if not selected_profile_id:
            _execution_census_error("evaluation_cost_profile_id_missing")
        normalized.append(
            {
                "target_date": str(report.get("target_date") or ""),
                "paired_replay_parent_id": parent,
                "decision_trace_id": str(row.get("decision_trace_id") or ""),
                "decision_stage": str(row.get("decision_stage") or "").lower(),
                "effective_venue": str(row.get("effective_venue") or ""),
                "session_bucket": str(row.get("session_bucket") or ""),
                "stock_code": str(row.get("stock_code") or ""),
                "control_contract_sha256": contracts["replay_control_exact_plus_micro"],
                "candidate_contract_sha256": contracts[
                    "replay_candidate_exact_plus_micro"
                ],
                "control_action": str(micro_control.get("action") or "UNKNOWN"),
                "candidate_action": str(candidate.get("action") or "UNKNOWN"),
                "control_ev_pct": control_ev,
                "candidate_ev_pct": candidate_ev,
                "paired_ev_delta_pct": candidate_ev - control_ev,
                "control_notional_value_krw": _finite_number(
                    micro_control.get("notional_incremental_value_krw")
                ),
                "candidate_notional_value_krw": _finite_number(
                    candidate.get("notional_incremental_value_krw")
                ),
                "control_severe_tail": micro_control.get("severe_tail_exposure")
                is True,
                "candidate_severe_tail": candidate.get("severe_tail_exposure") is True,
                "control_signal_selected": micro_control.get("economic_signal_selected")
                is True,
                "candidate_signal_selected": candidate.get("economic_signal_selected")
                is True,
                "outcome_label_content_sha256": str(
                    row.get("outcome_label_content_sha256") or ""
                ),
                "selected_cost_profile_id": selected_profile_id,
                **reference_fields,
            }
        )
    if len(normalized) != len(rows):
        _execution_census_error("evaluation_normalized_row_count_mismatch")
    return normalized


def _validate_current_execution_artifact(
    *,
    report: dict[str, Any],
    target_date: str,
    materialized_report: dict[str, Any],
    outcome_label_artifact: dict[str, Any],
    expected_max_new_requests: int,
    expected_daily_attempt_cap: int,
    expected_daily_usd_cap: Decimal,
    expected_pricing_content_sha256: str,
) -> list[dict[str, Any]]:
    """Validate that the current step produced one exact complete A/B/C census."""

    if str(report.get("target_date") or "") != target_date:
        raise ValueError("current_execution_target_date_mismatch")
    if report.get("materialized_report_content_sha256") != materialized_report.get(
        "report_content_sha256"
    ):
        raise ValueError("current_execution_materialized_hash_mismatch")
    if report.get("materialized_request_census_sha256") != (
        quality._micro_reversion_materialized_request_census_sha256(materialized_report)
    ):
        raise ValueError("current_execution_materialized_census_hash_mismatch")
    if report.get("outcome_label_artifact_sha256") != _sha256(outcome_label_artifact):
        raise ValueError("current_execution_outcome_artifact_hash_mismatch")
    if report.get("max_new_requests") != expected_max_new_requests:
        raise ValueError("current_execution_request_bound_mismatch")
    provider_budget = report.get("provider_budget")
    if not isinstance(provider_budget, Mapping):
        raise ValueError("current_execution_provider_budget_missing")
    if provider_budget.get("summary_content_sha256") != _content_hash(
        provider_budget,
        "summary_content_sha256",
    ):
        raise ValueError("current_execution_provider_budget_hash_mismatch")
    if provider_budget.get("daily_attempt_cap") != expected_daily_attempt_cap:
        raise ValueError("current_execution_provider_attempt_cap_mismatch")
    try:
        budget_usd_cap = Decimal(str(provider_budget.get("daily_usd_cap")))
    except (InvalidOperation, TypeError, ValueError):
        budget_usd_cap = Decimal("NaN")
    if not budget_usd_cap.is_finite() or budget_usd_cap != expected_daily_usd_cap:
        raise ValueError("current_execution_provider_usd_cap_mismatch")
    try:
        committed_cost = Decimal(str(provider_budget.get("committed_cost_usd")))
    except (InvalidOperation, TypeError, ValueError):
        committed_cost = Decimal("NaN")
    if (
        provider_budget.get("circuit_breaker_open") is not False
        or not committed_cost.is_finite()
        or committed_cost < 0
        or committed_cost > budget_usd_cap
    ):
        raise ValueError("current_execution_provider_budget_breached")
    if provider_budget.get("pricing_artifact_content_sha256") != (
        expected_pricing_content_sha256
    ) or not _valid_sha256(expected_pricing_content_sha256):
        raise ValueError("current_execution_provider_pricing_hash_mismatch")
    requests = quality._validate_micro_reversion_materialized_report(
        materialized_report
    )
    request_ids = [str(request.get("paired_replay_id") or "") for request in requests]
    request_by_id = {
        str(request.get("paired_replay_id") or ""): request for request in requests
    }
    expected_execution_exclusions = [
        {
            "paired_replay_parent_id": request.get("paired_replay_parent_id"),
            "paired_replay_id": request.get("paired_replay_id"),
            "micro_reversion_replay_arm": request.get("micro_reversion_replay_arm"),
            "stage": request.get("stage"),
            "provider": (request.get("candidate") or {}).get("provider"),
            "model": (request.get("candidate") or {}).get("model"),
            "reason": quality._micro_reversion_executor_exclusion(request),
        }
        for request in requests
        if quality._micro_reversion_executor_exclusion(request) is not None
    ]
    if report.get("execution_exclusions") != expected_execution_exclusions:
        raise ValueError("current_execution_exclusion_census_mismatch")
    quality._validate_micro_reversion_outcome_label_artifact(outcome_label_artifact)
    labels_by_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for label in outcome_label_artifact.get("labels") or []:
        if isinstance(label, dict) and label.get("label_id"):
            labels_by_id[str(label["label_id"])].append(label)
    bound_results = quality._micro_reversion_reusable_results(
        existing_artifact=report,
        materialized_report=materialized_report,
        requests=requests,
        labels_by_id=labels_by_id,
    )
    complete_parent_ids = quality._micro_reversion_complete_parent_ids(
        results=bound_results,
        requests=requests,
    )
    expected_parent_ids = {
        str(request.get("paired_replay_parent_id") or "") for request in requests
    }
    bound_result_request_ids = [
        str(result.get("paired_replay_id") or "") for result in bound_results
    ]
    if any(
        result_id not in request_by_id for result_id in bound_result_request_ids
    ) or len(bound_result_request_ids) != len(set(bound_result_request_ids)):
        raise ValueError("current_execution_result_request_census_invalid")
    expected_deferred_request_ids = [
        request_id
        for request_id in request_ids
        if request_id not in set(bound_result_request_ids)
    ]
    if report.get(
        "deferred_request_ids"
    ) != expected_deferred_request_ids or report.get("deferred_request_count") != len(
        expected_deferred_request_ids
    ):
        raise ValueError("current_execution_deferred_request_census_mismatch")
    selected_request_ids = report.get("selected_request_ids")
    selected_parent_ids = report.get("selected_parent_ids")
    if (
        not isinstance(selected_request_ids, list)
        or any(
            request_id not in bound_result_request_ids
            for request_id in selected_request_ids
        )
        or len(selected_request_ids) != len(set(selected_request_ids))
        or not isinstance(selected_parent_ids, list)
        or selected_parent_ids
        != list(
            dict.fromkeys(
                str(request_by_id[request_id].get("paired_replay_parent_id") or "")
                for request_id in selected_request_ids
            )
        )
    ):
        raise ValueError("current_execution_selected_request_census_mismatch")
    blocking_parent_ids = complete_parent_ids | set(selected_parent_ids)
    expected_blocking_exclusions = [
        exclusion
        for exclusion in expected_execution_exclusions
        if str(exclusion.get("paired_replay_parent_id") or "") in blocking_parent_ids
    ]
    if report.get(
        "blocking_execution_exclusions"
    ) != expected_blocking_exclusions or report.get(
        "blocking_execution_exclusion_count"
    ) != len(expected_blocking_exclusions):
        raise ValueError("current_execution_blocking_exclusion_census_mismatch")
    report_status = report.get("status")
    if (
        len(bound_results) != int(report.get("result_count") or 0)
        or not complete_parent_ids
        or not complete_parent_ids.issubset(expected_parent_ids)
    ):
        raise ValueError("current_execution_exact_parent_census_incomplete")
    if report_status == "offline_three_arm_execution_complete" and (
        complete_parent_ids != expected_parent_ids
    ):
        raise ValueError("current_execution_full_parent_census_incomplete")
    if report_status == "offline_three_arm_execution_batch_complete" and (
        complete_parent_ids == expected_parent_ids
    ):
        raise ValueError("current_execution_batch_deferred_census_missing")

    rows = _validated_execution_rows(report)
    if len(rows) != len(complete_parent_ids):
        raise ValueError("current_execution_evaluation_parent_census_incomplete")
    return rows


def _native_nonnegative_int(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value


def _positive_integer_mapping(value: Any) -> dict[str, int] | None:
    if not isinstance(value, Mapping) or not value:
        return None
    normalized: dict[str, int] = {}
    for raw_key, raw_quantity in value.items():
        key = str(raw_key or "").strip()
        quantity = _native_nonnegative_int(raw_quantity)
        if not key or quantity is None or quantity <= 0:
            return None
        normalized[key] = quantity
    return normalized


def _expected_main_lifecycle_id(
    *, record_id: Any, stock_code: Any, attempt_id: Any
) -> str | None:
    if isinstance(record_id, bool) or isinstance(attempt_id, bool):
        return None
    record = str(record_id if record_id is not None else "").strip()
    stock = str(stock_code or "").strip()
    attempt = str(attempt_id or "").strip()
    if (
        not record
        or len(record) > 128
        or not re.fullmatch(r"[0-9]{6}", stock)
        or not attempt
        or len(attempt) > 160
        or any(char in attempt for char in "\r\n\x00")
    ):
        return None
    lineage = {
        "record_id": record,
        "stock_code": stock,
        "attempt_id": attempt,
    }
    return f"mlc-{_sha256(lineage)[:32]}"


def _lifecycle_report_hash_valid(report: Mapping[str, Any]) -> bool:
    artifact_hash = str(report.get("artifact_content_sha256") or "")
    if not artifact_hash or artifact_hash != _content_hash(
        report, "artifact_content_sha256"
    ):
        return False
    producer_content = {
        key: value
        for key, value in report.items()
        if key
        not in {
            "content_sha256",
            "report_content_sha256",
            "artifact_content_sha256",
        }
    }
    producer_hash = _sha256(producer_content)
    return (
        report.get("content_sha256") == producer_hash
        and report.get("report_content_sha256") == producer_hash
    )


def _lifecycle_exclusion_taxonomies(reason_codes: Sequence[str]) -> list[str]:
    """Mirror the current paired producer's exact-window taxonomy contract."""

    taxonomies: set[str] = set()
    for reason in reason_codes:
        if reason in {
            "broker_order_no_cross_lifecycle_conflict",
            "broker_execution_identity_cross_lifecycle_conflict",
        }:
            taxonomies.add("cross_lifecycle_identity_conflict")
        elif reason.startswith("broker_execution_") or reason == (
            "actual_broker_order_submission_required"
        ):
            taxonomies.add("broker_execution_provenance_or_custody_gap")
        elif reason.startswith(("bbo_", "depth_", "session_exposure_")):
            taxonomies.add("market_observation_coverage_gap")
        elif reason.startswith(("reviewed_cost_", "verified_symbol_")):
            taxonomies.add("economic_reference_gap")
        elif reason.startswith(
            (
                "realized_economics_",
                "fees_taxes_",
                "slippage_",
                "realized_net_pnl_",
            )
        ):
            taxonomies.add("realized_economics_gap")
        else:
            taxonomies.add("lifecycle_completeness_or_consistency_gap")
    return sorted(taxonomies)


def _lifecycle_exclusion_manifest_findings(
    report: Mapping[str, Any], *, rows: Sequence[Mapping[str, Any]]
) -> list[str]:
    findings: list[str] = []
    manifest = report.get("lifecycle_window_exclusion_manifest")
    if not isinstance(manifest, Mapping):
        return ["lifecycle_window_exclusion_manifest_missing"]
    if manifest.get("schema") != LIFECYCLE_WINDOW_EXCLUSION_MANIFEST_SCHEMA:
        findings.append("lifecycle_window_exclusion_manifest_schema_invalid")
    for field, expected in LIFECYCLE_EXCLUSION_AUTHORITY_CONTRACT.items():
        if manifest.get(field) != expected:
            findings.append(f"lifecycle_window_exclusion_authority_invalid:{field}")

    expected_entries: list[dict[str, Any]] = []
    expected_reason_counts: dict[str, int] = defaultdict(int)
    expected_taxonomy_counts: dict[str, int] = defaultdict(int)
    eligible_count = 0
    for row in rows:
        lifecycle_id = str(row.get("main_lifecycle_id") or "")
        raw_reasons = row.get("promotion_blockers")
        if not isinstance(raw_reasons, list) or any(
            not isinstance(reason, str) or not reason.strip() for reason in raw_reasons
        ):
            findings.append(
                f"lifecycle_window_row_reason_codes_invalid:{lifecycle_id or 'missing'}"
            )
            continue
        reason_codes = [str(reason) for reason in raw_reasons]
        if not reason_codes:
            eligible_count += 1
            if row.get("lifecycle_window_source_quality_disposition") != (
                "eligible_before_global_source_contract_gate"
            ):
                findings.append(
                    "lifecycle_window_row_disposition_invalid:"
                    f"{lifecycle_id or 'missing'}"
                )
            if row.get("lifecycle_window_exclusion_taxonomies") != []:
                findings.append(
                    "lifecycle_window_row_taxonomies_invalid:"
                    f"{lifecycle_id or 'missing'}"
                )
            if row.get("promotion_disposition") != "eligible_source_only":
                findings.append(
                    "lifecycle_window_row_promotion_disposition_invalid:"
                    f"{lifecycle_id or 'missing'}"
                )
            continue

        taxonomies = _lifecycle_exclusion_taxonomies(reason_codes)
        if row.get("lifecycle_window_source_quality_disposition") != (
            "excluded_exact_lifecycle_window"
        ):
            findings.append(
                f"lifecycle_window_row_disposition_invalid:{lifecycle_id or 'missing'}"
            )
        if row.get("lifecycle_window_exclusion_taxonomies") != taxonomies:
            findings.append(
                f"lifecycle_window_row_taxonomies_invalid:{lifecycle_id or 'missing'}"
            )
        if row.get("promotion_disposition") != "excluded_exact_lifecycle_window":
            findings.append(
                "lifecycle_window_row_promotion_disposition_invalid:"
                f"{lifecycle_id or 'missing'}"
            )
        for reason in reason_codes:
            expected_reason_counts[reason] += 1
        for taxonomy in taxonomies:
            expected_taxonomy_counts[taxonomy] += 1
        expected_entries.append(
            {
                "main_lifecycle_id": lifecycle_id,
                "exclusion_scope": "exact_main_lifecycle_window",
                "taxonomies": taxonomies,
                "reason_codes_sha256": _sha256(reason_codes),
            }
        )

    if manifest.get("excluded_lifecycle_count") != len(expected_entries):
        findings.append("lifecycle_window_excluded_census_mismatch")
    if manifest.get("eligible_lifecycle_count") != eligible_count:
        findings.append("lifecycle_window_eligible_census_mismatch")
    if manifest.get("taxonomy_counts") != dict(
        sorted(expected_taxonomy_counts.items())
    ):
        findings.append("lifecycle_window_taxonomy_census_mismatch")
    if manifest.get("reason_code_counts") != dict(
        sorted(expected_reason_counts.items())
    ):
        findings.append("lifecycle_window_reason_census_mismatch")
    if manifest.get("entries") != expected_entries:
        findings.append("lifecycle_window_entry_hash_or_binding_mismatch")
    return findings


def _lifecycle_report_contract_findings(
    report: Mapping[str, Any], *, rows: Sequence[Any]
) -> list[str]:
    findings: list[str] = []
    for field, expected in LIFECYCLE_REPORT_AUTHORITY_CONTRACT.items():
        if report.get(field) != expected:
            findings.append(f"top_level_authority_invalid:{field}")
    for field, expected in (
        ("source_transition_schema", JOURNAL_SCHEMA),
        ("source_pipeline_identity_schema", PIPELINE_IDENTITY_SCHEMA),
        (
            "broker_execution_provenance_schema",
            BROKER_EXECUTION_PROVENANCE_SCHEMA,
        ),
        (
            "broker_execution_raw_envelope_schema",
            BROKER_EXECUTION_RAW_ENVELOPE_SCHEMA,
        ),
        (
            "broker_execution_official_reference_sha",
            KIWOOM_OFFICIAL_REFERENCE_SHA,
        ),
    ):
        if report.get(field) != expected:
            findings.append(f"top_level_broker_contract_invalid:{field}")
    for hash_field, verified_field in (
        ("reviewed_cost_profile_sha256", "reviewed_cost_profile_verified"),
        ("symbol_master_artifact_sha256", "symbol_master_artifact_verified"),
    ):
        if not _valid_sha256(report.get(hash_field)):
            findings.append(f"top_level_reference_hash_invalid:{hash_field}")
        if report.get(verified_field) is not True:
            findings.append(f"top_level_reference_not_verified:{verified_field}")
    if report.get("source_kind") not in {
        "pipeline_events_explicit_id_only",
        "transition_journal",
    }:
        findings.append("top_level_source_kind_invalid")

    source_census = report.get("source_raw_census")
    if not isinstance(source_census, Mapping):
        findings.append("source_raw_census_missing")
    else:
        if report.get("source_census_content_sha256") != _sha256(source_census):
            findings.append("source_raw_census_hash_mismatch")
        for field in ("source_raw_sha256", "source_decoded_sha256"):
            if not _valid_sha256(source_census.get(field)):
                findings.append(f"source_raw_census_hash_invalid:{field}")
        if source_census.get("source_exists") is not True:
            findings.append("source_raw_census_source_missing")
        if source_census.get("source_read_error") is not None:
            findings.append("source_raw_census_read_error")
        for field in ("malformed_json_count", "non_object_count"):
            if _native_nonnegative_int(source_census.get(field)) != 0:
                findings.append(f"source_raw_census_not_clean:{field}")
    if report.get("source_raw_sha256") != (
        (source_census or {}).get("source_raw_sha256")
        if isinstance(source_census, Mapping)
        else None
    ):
        findings.append("source_raw_hash_binding_mismatch")
    if report.get("source_content_sha256") != (
        (source_census or {}).get("source_decoded_sha256")
        if isinstance(source_census, Mapping)
        else None
    ):
        findings.append("source_content_hash_binding_mismatch")

    if report.get("global_source_quality_gate_pass") is not True:
        findings.append("global_source_quality_gate_not_pass")
    if report.get("global_source_quality_gate_blockers") != []:
        findings.append("global_source_quality_gate_blockers_present")
    if report.get("reference_contract_blockers") != []:
        findings.append("reference_contract_blockers_present")
    for field in (
        "source_invalid_transition_count",
        "mixed_source_row_count",
        "lifecycle_accumulator_overflow_row_count",
        "transition_event_identity_overflow_row_count",
        "pipeline_lifecycle_instrumentation_gap_count",
        "broker_order_no_cross_lifecycle_conflict_count",
        "broker_execution_cross_lifecycle_identity_conflict_count",
    ):
        if _native_nonnegative_int(report.get(field)) != 0:
            findings.append(f"top_level_zero_census_invalid:{field}")

    row_dicts = [row for row in rows if isinstance(row, Mapping)]
    if len(row_dicts) != len(rows) or report.get("lifecycle_count") != len(rows):
        findings.append("lifecycle_row_census_mismatch")
    eligible_ids = [
        str(row.get("main_lifecycle_id") or "")
        for row in row_dicts
        if row.get("promotion_evidence_eligible") is True
    ]
    if (
        any(not lifecycle_id for lifecycle_id in eligible_ids)
        or len(eligible_ids) != len(set(eligible_ids))
        or report.get("promotion_evidence_eligible_count") != len(eligible_ids)
        or report.get("promotion_ready_lifecycle_ids") != eligible_ids
        or report.get("promotion_ready") is not bool(eligible_ids)
    ):
        findings.append("promotion_row_census_mismatch")

    findings.extend(_lifecycle_exclusion_manifest_findings(report, rows=row_dicts))

    summed_fields = (
        "broker_execution_provenance_gap_count",
        "broker_execution_conflict_count",
        "broker_execution_order_progress_conflict_count",
        "broker_execution_submission_link_conflict_count",
        "broker_order_no_cross_lifecycle_conflict_count",
        "broker_execution_cross_lifecycle_identity_conflict_count",
        "broker_execution_replay_duplicate_count",
        "broker_execution_unique_count",
    )
    for field in summed_fields:
        values = [_native_nonnegative_int(row.get(field)) for row in row_dicts]
        if any(value is None for value in values) or report.get(field) != sum(
            value or 0 for value in values
        ):
            findings.append(f"top_level_row_census_mismatch:{field}")
    invalid_transition_values = [
        _native_nonnegative_int(row.get("invalid_transition_count"))
        for row in row_dicts
    ]
    if any(value is None for value in invalid_transition_values) or report.get(
        "lifecycle_invalid_transition_count"
    ) != sum(value or 0 for value in invalid_transition_values):
        findings.append(
            "top_level_row_census_mismatch:lifecycle_invalid_transition_count"
        )

    candidate_gate_failure_count = sum(
        row.get("terminal_state") == "FINAL_EXIT_RECONCILED"
        and row.get("promotion_evidence_eligible") is not True
        for row in row_dicts
    )
    if report.get("candidate_row_gate_failure_count") != (candidate_gate_failure_count):
        findings.append("candidate_row_gate_failure_census_mismatch")

    fallback_gap_count = 0
    fallback_census = report.get("raw_fallback_census")
    if fallback_census is not None:
        if not isinstance(fallback_census, Mapping):
            findings.append("raw_fallback_census_invalid")
        else:
            fallback_counts = [
                _native_nonnegative_int(fallback_census.get(field))
                for field in (
                    "missing_main_lifecycle_id_count",
                    "malformed_json_count",
                    "non_object_count",
                )
            ]
            if any(value is None for value in fallback_counts):
                findings.append("raw_fallback_census_invalid")
            else:
                fallback_gap_count = sum(value or 0 for value in fallback_counts)
                fallback_gap_count += int(
                    fallback_census.get("source_read_error") is not None
                )
                fallback_gap_count += int(
                    fallback_census.get("source_exists") is not True
                )
            if fallback_gap_count:
                findings.append("raw_fallback_global_gap_present")

    instrumentation_fields = (
        "source_invalid_transition_count",
        "broker_execution_provenance_gap_count",
        "broker_execution_conflict_count",
        "broker_execution_order_progress_conflict_count",
        "broker_execution_submission_link_conflict_count",
        "broker_order_no_cross_lifecycle_conflict_count",
        "broker_execution_cross_lifecycle_identity_conflict_count",
        "lifecycle_accumulator_overflow_row_count",
        "transition_event_identity_overflow_row_count",
    )
    instrumentation_values = [
        _native_nonnegative_int(report.get(field)) for field in instrumentation_fields
    ]
    if any(value is None for value in instrumentation_values):
        findings.append("instrumentation_gap_input_census_invalid")
    elif isinstance(source_census, Mapping):
        expected_instrumentation_gap_count = sum(
            value or 0 for value in instrumentation_values
        )
        expected_instrumentation_gap_count += sum(
            _native_nonnegative_int(source_census.get(field)) or 0
            for field in ("malformed_json_count", "non_object_count")
        )
        expected_instrumentation_gap_count += int(
            source_census.get("source_read_error") is not None
        )
        expected_instrumentation_gap_count += int(
            source_census.get("source_exists") is not True
        )
        expected_instrumentation_gap_count += fallback_gap_count
        expected_instrumentation_gap_count += candidate_gate_failure_count
        expected_instrumentation_gap_count += int(not row_dicts)
        if report.get("instrumentation_gap_count") != (
            expected_instrumentation_gap_count
        ):
            findings.append("instrumentation_gap_census_mismatch")
    return findings


def _lifecycle_broker_row_findings(
    row: Mapping[str, Any], *, report: Mapping[str, Any]
) -> list[str]:
    findings: list[str] = []
    lifecycle_id = str(row.get("main_lifecycle_id") or "")
    trace_ids = row.get("decision_trace_ids")
    expected_lifecycle_id = _expected_main_lifecycle_id(
        record_id=row.get("record_id"),
        stock_code=row.get("stock_code"),
        attempt_id=row.get("attempt_id"),
    )
    try:
        trade_date = date.fromisoformat(str(row.get("trade_date") or ""))
    except ValueError:
        trade_date = None
    if (
        expected_lifecycle_id is None
        or lifecycle_id != expected_lifecycle_id
        or trade_date is None
        or trade_date.isoformat() != str(report.get("target_date") or "")
        or not re.fullmatch(r"[0-9]{6}", str(row.get("stock_code") or ""))
        or not str(row.get("record_id") or "").strip()
        or not str(row.get("attempt_id") or "").strip()
        or not str(row.get("venue") or "").strip()
        or not str(row.get("session_bucket") or "").strip()
        or not isinstance(trace_ids, list)
        or not trace_ids
        or any(not str(trace_id or "").strip() for trace_id in trace_ids)
        or len({str(trace_id) for trace_id in trace_ids}) != len(trace_ids)
    ):
        findings.append("row_exact_lifecycle_identity_invalid")
    for field, expected in LIFECYCLE_REPORT_AUTHORITY_CONTRACT.items():
        if row.get(field) != expected:
            findings.append(f"row_authority_invalid:{field}")
    for field, expected in (
        (
            "broker_execution_provenance_schema",
            BROKER_EXECUTION_PROVENANCE_SCHEMA,
        ),
        (
            "broker_execution_raw_envelope_schema",
            BROKER_EXECUTION_RAW_ENVELOPE_SCHEMA,
        ),
        (
            "broker_execution_official_reference_sha",
            KIWOOM_OFFICIAL_REFERENCE_SHA,
        ),
    ):
        if row.get(field) != expected:
            findings.append(f"row_broker_contract_invalid:{field}")
    if (
        row.get("promotion_evidence_eligible") is not True
        or row.get("row_source_quality_gate_pass") is not True
        or row.get("promotion_blockers") != []
        or row.get("terminal_state") != "FINAL_EXIT_RECONCILED"
    ):
        findings.append("row_promotion_gate_not_current_complete")
    if row.get("observed_actual_broker_order_submitted") is not True:
        findings.append("row_actual_broker_submission_missing")
    if row.get("broker_execution_provenance_gap_reasons") != []:
        findings.append("row_broker_execution_gap_reasons_present")
    for field in (
        "invalid_transition_count",
        "broker_execution_provenance_gap_count",
        "broker_execution_conflict_count",
        "broker_execution_order_progress_conflict_count",
        "broker_execution_submission_link_conflict_count",
        "broker_order_no_cross_lifecycle_conflict_count",
        "broker_execution_cross_lifecycle_identity_conflict_count",
        "broker_execution_unreconciled_order_count",
    ):
        if _native_nonnegative_int(row.get(field)) != 0:
            findings.append(f"row_zero_census_invalid:{field}")

    unique_count = _native_nonnegative_int(row.get("broker_execution_unique_count"))
    partial_count = _native_nonnegative_int(row.get("broker_execution_partial_count"))
    full_count = _native_nonnegative_int(row.get("broker_execution_full_count"))
    state_counts = row.get("broker_execution_provenance_state_counts")
    if (
        unique_count is None
        or unique_count <= 0
        or partial_count is None
        or full_count is None
        or partial_count + full_count != unique_count
        or not isinstance(state_counts, Mapping)
        or state_counts != {"complete": unique_count}
    ):
        findings.append("row_broker_execution_provenance_census_invalid")

    submitted_by_order = _positive_integer_mapping(
        row.get("broker_submitted_requested_qty_by_order_no")
    )
    submitted_by_phase = _positive_integer_mapping(
        row.get("broker_submitted_requested_qty_by_phase")
    )
    executed_raw = row.get("broker_executed_order_qty_by_phase")
    executed_by_phase: dict[str, dict[str, int]] | None = None
    if isinstance(executed_raw, Mapping) and executed_raw:
        candidate: dict[str, dict[str, int]] = {}
        for raw_phase, raw_orders in executed_raw.items():
            phase = str(raw_phase or "").strip()
            orders = _positive_integer_mapping(raw_orders)
            if phase not in {"entry", "scale_in", "exit"} or orders is None:
                candidate = {}
                break
            candidate[phase] = orders
        executed_by_phase = candidate or None
    if (
        submitted_by_order is None
        or submitted_by_phase is None
        or executed_by_phase is None
        or set(submitted_by_phase) != set(executed_by_phase)
        or not {"entry", "exit"}.issubset(submitted_by_phase)
        or row.get("broker_submitted_order_count") != len(submitted_by_order)
        or row.get("broker_submitted_order_coverage_gap_phases") != []
        or row.get("broker_submitted_order_qty_mismatch_phases") != []
    ):
        findings.append("row_broker_order_census_invalid")
    else:
        flattened: dict[str, int] = {}
        order_conflict = False
        for phase, orders in executed_by_phase.items():
            if sum(orders.values()) != submitted_by_phase[phase]:
                order_conflict = True
            for order_no, quantity in orders.items():
                if (
                    not re.fullmatch(r"[0-9]{7}", order_no)
                    or int(order_no) == 0
                    or order_no in flattened
                ):
                    order_conflict = True
                flattened[order_no] = quantity
        if order_conflict or flattened != submitted_by_order:
            findings.append("row_broker_order_quantity_binding_invalid")

    entry_qty = _finite_number(row.get("entry_fill_qty"))
    scale_in_qty = _finite_number(row.get("scale_in_fill_qty"))
    exit_qty = _finite_number(row.get("exit_qty"))
    entry_covered = _finite_number(row.get("broker_execution_entry_covered_qty"))
    exit_covered = _finite_number(row.get("broker_execution_exit_covered_qty"))
    if (
        entry_qty is None
        or entry_qty <= 0
        or scale_in_qty is None
        or scale_in_qty < 0
        or exit_qty is None
        or exit_qty <= 0
        or entry_covered is None
        or exit_covered is None
        or not math.isclose(
            entry_covered,
            entry_qty + scale_in_qty,
            rel_tol=0.0,
            abs_tol=1e-8,
        )
        or not math.isclose(
            exit_covered,
            exit_qty,
            rel_tol=0.0,
            abs_tol=1e-8,
        )
        or not math.isclose(
            entry_qty + scale_in_qty,
            exit_qty,
            rel_tol=0.0,
            abs_tol=1e-8,
        )
        or _finite_number(row.get("open_qty_at_censor")) is None
        or not math.isclose(
            float(row.get("open_qty_at_censor")),
            0.0,
            rel_tol=0.0,
            abs_tol=1e-8,
        )
    ):
        findings.append("row_broker_execution_quantity_coverage_invalid")
    elif executed_by_phase is not None:
        expected_phase_quantities = {
            "entry": entry_qty,
            "exit": exit_qty,
        }
        if scale_in_qty > 0:
            expected_phase_quantities["scale_in"] = scale_in_qty
        if set(expected_phase_quantities) != set(executed_by_phase) or any(
            not math.isclose(
                float(sum(executed_by_phase[phase].values())),
                expected_quantity,
                rel_tol=0.0,
                abs_tol=1e-8,
            )
            for phase, expected_quantity in expected_phase_quantities.items()
        ):
            findings.append("row_broker_execution_phase_quantity_invalid")

    for row_field, report_field in (
        ("reviewed_cost_profile_sha256", "reviewed_cost_profile_sha256"),
        ("symbol_master_artifact_sha256", "symbol_master_artifact_sha256"),
    ):
        value = row.get(row_field)
        if not _valid_sha256(value) or value != report.get(report_field):
            findings.append(f"row_reference_hash_binding_invalid:{row_field}")
    if (
        row.get("reviewed_cost_profile_verified") is not True
        or row.get("symbol_master_artifact_verified") is not True
    ):
        findings.append("row_reference_verification_missing")
    return findings


def _lifecycle_index(
    lifecycle_reports: Iterable[Mapping[str, Any]],
) -> tuple[dict[tuple[str, str], dict[str, Any]], list[str]]:
    index: dict[tuple[str, str], dict[str, Any]] = {}
    ambiguous_keys: set[tuple[str, str]] = set()
    findings: list[str] = []
    finding_overflow_count = 0

    def retain(*values: str) -> None:
        nonlocal finding_overflow_count
        for value in values:
            if len(findings) < MAX_LIFECYCLE_FINDINGS - 1:
                findings.append(value)
            else:
                finding_overflow_count += 1

    for report in lifecycle_reports:
        target_date = str(report.get("target_date") or "")
        rows = report.get("rows")
        if report.get("schema") != LIFECYCLE_REPORT_SCHEMA:
            retain(f"lifecycle_report_schema_invalid:{target_date or 'missing'}")
            continue
        if not target_date or not isinstance(rows, list):
            retain("lifecycle_report_shape_invalid")
            continue
        if not _lifecycle_report_hash_valid(report):
            retain(f"lifecycle_report_hash_invalid:{target_date}")
            continue
        report_findings = _lifecycle_report_contract_findings(report, rows=rows)
        if report_findings:
            retain(
                *(
                    f"lifecycle_report_contract_invalid:{target_date}:{reason}"
                    for reason in report_findings
                )
            )
            continue
        trace_owner: dict[str, str] = {}
        report_ambiguous_traces: set[str] = set()
        for raw_row in rows:
            if not isinstance(raw_row, Mapping):
                continue
            lifecycle_id = str(raw_row.get("main_lifecycle_id") or "")
            trace_ids = raw_row.get("decision_trace_ids")
            if not isinstance(trace_ids, list):
                continue
            for raw_trace_id in trace_ids:
                trace_id = str(raw_trace_id or "")
                previous_owner = trace_owner.setdefault(trace_id, lifecycle_id)
                if trace_id and previous_owner != lifecycle_id:
                    report_ambiguous_traces.add(trace_id)
        for trace_id in sorted(report_ambiguous_traces):
            key = (target_date, trace_id)
            index.pop(key, None)
            if key not in ambiguous_keys:
                retain(f"lifecycle_trace_identity_ambiguous:{target_date}:{trace_id}")
            ambiguous_keys.add(key)
        for row in rows:
            assert isinstance(row, Mapping)
            row_findings = _lifecycle_broker_row_findings(row, report=report)
            lifecycle_id = str(row.get("main_lifecycle_id") or "missing")
            if row_findings:
                retain(
                    *(
                        "lifecycle_row_contract_invalid:"
                        f"{target_date}:{lifecycle_id}:{reason}"
                        for reason in row_findings
                    )
                )
                continue
            trace_ids = row.get("decision_trace_ids")
            if not isinstance(trace_ids, list):
                single = str(row.get("decision_trace_id") or "")
                trace_ids = [single] if single else []
            for trace_id in trace_ids:
                key = (target_date, str(trace_id or ""))
                if not key[1]:
                    continue
                if key in ambiguous_keys:
                    continue
                if key in index and index[key] != row:
                    retain(f"lifecycle_trace_identity_ambiguous:{target_date}:{key[1]}")
                    index.pop(key, None)
                    ambiguous_keys.add(key)
                    continue
                index[key] = dict(row)
    if finding_overflow_count:
        findings.append(f"lifecycle_findings_truncated:{finding_overflow_count}")
    return index, findings


def _lifecycle_gate_findings(row: Mapping[str, Any] | None) -> list[str]:
    if not isinstance(row, Mapping):
        return ["lifecycle_exact_join_missing"]
    findings: list[str] = []
    if row.get("promotion_evidence_eligible") is not True:
        findings.append("lifecycle_promotion_evidence_not_eligible")
    if int(row.get("invalid_transition_count") or 0) != 0:
        findings.append("lifecycle_invalid_transition")
    for field in (
        "actual_holding_duration_sec",
        "session_exposure_sec",
        "capital_time_krw_hours",
        "bbo_coverage_pct",
        "depth_coverage_pct",
    ):
        value = _finite_number(row.get(field))
        if value is None or value < 0:
            findings.append(f"lifecycle_metric_missing:{field}")
    if (_finite_number(row.get("session_exposure_sec")) or 0.0) <= 0:
        findings.append("lifecycle_session_exposure_nonpositive")
    if (_finite_number(row.get("bbo_coverage_pct")) or 0.0) < MIN_BBO_COVERAGE_PCT:
        findings.append("lifecycle_bbo_coverage_below_floor")
    if (_finite_number(row.get("depth_coverage_pct")) or 0.0) < MIN_DEPTH_COVERAGE_PCT:
        findings.append("lifecycle_depth_coverage_below_floor")
    if not str(row.get("reviewed_cost_profile_sha256") or ""):
        findings.append("lifecycle_reviewed_cost_hash_missing")
    if row.get("reviewed_cost_profile_verified") is not True:
        findings.append("lifecycle_reviewed_cost_not_verified")
    if not str(row.get("symbol_master_artifact_sha256") or ""):
        findings.append("lifecycle_symbol_master_hash_missing")
    if row.get("symbol_master_artifact_verified") is not True:
        findings.append("lifecycle_symbol_master_not_verified")
    return findings


def _date_window_rows(
    rows: Sequence[dict[str, Any]], *, target_date: str, trading_days: int
) -> tuple[list[dict[str, Any]], list[str]]:
    dates = sorted(
        {
            str(row.get("target_date") or "")
            for row in rows
            if str(row.get("target_date") or "") <= target_date
        }
    )
    selected_dates = dates[-trading_days:]
    return (
        [row for row in rows if row.get("target_date") in selected_dates],
        selected_dates,
    )


def _window_metrics(
    rows: Sequence[dict[str, Any]], *, target_date: str, trading_days: int
) -> dict[str, Any]:
    selected, selected_dates = _date_window_rows(
        rows, target_date=target_date, trading_days=trading_days
    )
    candidate_evs = [float(row["candidate_ev_pct"]) for row in selected]
    control_evs = [float(row["control_ev_pct"]) for row in selected]
    deltas = [float(row["paired_ev_delta_pct"]) for row in selected]
    candidate_notional = [
        float(value)
        for row in selected
        if (value := row.get("candidate_notional_value_krw")) is not None
    ]
    session_exposure_sec = sum(
        float((row.get("lifecycle") or {}).get("session_exposure_sec") or 0.0)
        for row in selected
    )
    capital_hours = sum(
        float((row.get("lifecycle") or {}).get("capital_time_krw_hours") or 0.0)
        for row in selected
    )
    candidate_signal_count = sum(
        row.get("candidate_signal_selected") is True for row in selected
    )
    relative_uplift_values = [
        delta / max(abs(control), 0.01) * 100.0
        for delta, control in zip(deltas, control_evs)
    ]
    control_deferred = sum(
        str(row.get("control_action") or "") in {"WAIT", "HOLD"} for row in selected
    )
    candidate_deferred = sum(
        str(row.get("candidate_action") or "") in {"WAIT", "HOLD"} for row in selected
    )
    return {
        "window_trading_days": trading_days,
        "observed_trading_days": len(selected_dates),
        "selected_dates": selected_dates,
        "common_parent_count": len(selected),
        "unique_symbol_count": len(
            {str(row.get("stock_code") or "") for row in selected}
        ),
        "control_source_quality_adjusted_ev_pct": (
            fmean(control_evs) if control_evs else None
        ),
        "candidate_source_quality_adjusted_ev_pct": (
            fmean(candidate_evs) if candidate_evs else None
        ),
        "paired_ev_delta_pct": fmean(deltas) if deltas else None,
        "relative_uplift_pct": (
            fmean(relative_uplift_values) if relative_uplift_values else None
        ),
        "control_p10_ev_pct": _percentile(control_evs, 0.10),
        "candidate_p10_ev_pct": _percentile(candidate_evs, 0.10),
        "control_severe_tail_count": sum(
            row.get("control_severe_tail") is True for row in selected
        ),
        "candidate_severe_tail_count": sum(
            row.get("candidate_severe_tail") is True for row in selected
        ),
        "control_deferred_count": control_deferred,
        "candidate_deferred_count": candidate_deferred,
        "candidate_notional_eligible_count": len(candidate_notional),
        "candidate_total_notional_net_profit_krw": (
            sum(candidate_notional) if candidate_notional else None
        ),
        "session_exposure_hours": (
            session_exposure_sec / 3600.0 if session_exposure_sec > 0 else None
        ),
        "eligible_signals_per_session_hour": (
            candidate_signal_count / (session_exposure_sec / 3600.0)
            if session_exposure_sec > 0
            else None
        ),
        "average_actual_holding_duration_sec": (
            fmean(
                float((row.get("lifecycle") or {})["actual_holding_duration_sec"])
                for row in selected
            )
            if selected
            else None
        ),
        "capital_time_krw_hours": capital_hours if capital_hours > 0 else None,
        "net_profit_per_capital_krw_hour": (
            sum(candidate_notional) / capital_hours
            if candidate_notional and capital_hours > 0
            else None
        ),
        "bbo_coverage_pct": (
            fmean(
                float((row.get("lifecycle") or {})["bbo_coverage_pct"])
                for row in selected
            )
            if selected
            else None
        ),
        "depth_coverage_pct": (
            fmean(
                float((row.get("lifecycle") or {})["depth_coverage_pct"])
                for row in selected
            )
            if selected
            else None
        ),
        "invalid_transition_count": sum(
            int((row.get("lifecycle") or {}).get("invalid_transition_count") or 0)
            for row in selected
        ),
    }


def _window_gate_findings(metrics: Mapping[str, Any]) -> list[str]:
    findings: list[str] = []
    expected_days = int(metrics.get("window_trading_days") or 0)
    if int(metrics.get("observed_trading_days") or 0) < expected_days:
        findings.append("rolling_trading_day_floor_not_met")
    if (
        expected_days == 20
        and int(metrics.get("common_parent_count") or 0) < MIN_COMMON_PARENTS
    ):
        findings.append("rolling_common_parent_floor_not_met")
    if (
        expected_days == 20
        and int(metrics.get("unique_symbol_count") or 0) < MIN_UNIQUE_SYMBOLS
    ):
        findings.append("rolling_unique_symbol_floor_not_met")
    if (
        _finite_number(metrics.get("candidate_source_quality_adjusted_ev_pct"))
        or -math.inf
    ) <= 0:
        findings.append("candidate_ev_not_positive")
    if (_finite_number(metrics.get("paired_ev_delta_pct")) or -math.inf) <= 0:
        findings.append("paired_ev_delta_not_positive")
    if (
        _finite_number(metrics.get("relative_uplift_pct")) or -math.inf
    ) < MIN_RELATIVE_UPLIFT_PCT:
        findings.append("relative_uplift_below_floor")
    control_p10 = _finite_number(metrics.get("control_p10_ev_pct"))
    candidate_p10 = _finite_number(metrics.get("candidate_p10_ev_pct"))
    if control_p10 is None or candidate_p10 is None or candidate_p10 < control_p10:
        findings.append("paired_p10_worsened_or_missing")
    if int(metrics.get("candidate_severe_tail_count") or 0) > int(
        metrics.get("control_severe_tail_count") or 0
    ):
        findings.append("severe_tail_worsened")
    if int(metrics.get("candidate_deferred_count") or 0) > int(
        metrics.get("control_deferred_count") or 0
    ):
        findings.append("held_or_unresolved_proxy_worsened")
    if (_finite_number(metrics.get("bbo_coverage_pct")) or 0.0) < MIN_BBO_COVERAGE_PCT:
        findings.append("rolling_bbo_coverage_below_floor")
    if (
        _finite_number(metrics.get("depth_coverage_pct")) or 0.0
    ) < MIN_DEPTH_COVERAGE_PCT:
        findings.append("rolling_depth_coverage_below_floor")
    if int(metrics.get("invalid_transition_count") or 0) != 0:
        findings.append("rolling_invalid_transition_present")
    if metrics.get("eligible_signals_per_session_hour") is None:
        findings.append("session_exposure_denominator_missing")
    if metrics.get("average_actual_holding_duration_sec") is None:
        findings.append("actual_holding_duration_missing")
    if expected_days == 20 and (
        (
            _finite_number(metrics.get("candidate_total_notional_net_profit_krw"))
            or -math.inf
        )
        <= 0
    ):
        findings.append("twenty_day_notional_net_profit_not_positive")
    return findings


def build_rolling_source_only_candidates(
    *,
    target_date: str,
    execution_reports: Iterable[Mapping[str, Any]],
    lifecycle_reports: Iterable[Mapping[str, Any]],
    source_quality_pass_by_date: Mapping[str, bool],
    economic_reference_pass_by_date: Mapping[str, bool],
    input_diagnostics: Iterable[Mapping[str, Any]] = (),
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build strict rolling R2 evidence and an R3 source-only manifest."""

    lifecycle_index, lifecycle_findings = _lifecycle_index(lifecycle_reports)
    joined_rows: list[dict[str, Any]] = []
    exclusions: list[dict[str, Any]] = []
    source_dates: set[str] = set()
    global_candidate_blockers = [
        (
            "historical_execution_artifact_collection_invalid:"
            f"{str(diagnostic.get('target_date') or 'missing')}:"
            f"{str(diagnostic.get('reason') or 'unknown')}"
        )
        for diagnostic in input_diagnostics
        if isinstance(diagnostic, Mapping)
        and diagnostic.get("artifact") == "execution"
        and diagnostic.get("status") == "invalid"
    ]
    for report in execution_reports:
        try:
            rows = _validated_execution_rows(report)
        except (TypeError, ValueError) as exc:
            blocker = (
                "historical_execution_artifact_contract_invalid:"
                f"{str(report.get('target_date') or 'missing')}:"
                f"{str(exc)}"
            )
            global_candidate_blockers.append(blocker)
            exclusions.append(
                {"reason": str(exc), "target_date": report.get("target_date")}
            )
            continue
        report_date = str(report.get("target_date") or "")
        source_dates.add(report_date)
        if source_quality_pass_by_date.get(report_date) is not True:
            exclusions.append(
                {"reason": "source_quality_audit_not_pass", "target_date": report_date}
            )
            continue
        if economic_reference_pass_by_date.get(report_date) is not True:
            exclusions.append(
                {
                    "reason": "economic_reference_not_verified",
                    "target_date": report_date,
                }
            )
            continue
        for row in rows:
            lifecycle = lifecycle_index.get(
                (report_date, str(row.get("decision_trace_id") or ""))
            )
            findings = _lifecycle_gate_findings(lifecycle)
            if not findings and (
                row.get("stock_code") != (lifecycle or {}).get("stock_code")
                or str(row.get("effective_venue") or "").strip().upper()
                != str((lifecycle or {}).get("venue") or "").strip().upper()
                or quality._session(row.get("session_bucket"))
                != quality._session((lifecycle or {}).get("session_bucket"))
            ):
                findings.append("daily_lifecycle_identity_binding_mismatch")
            if not findings and (
                row.get("cost_profile_artifact_sha256")
                != (lifecycle or {}).get("reviewed_cost_profile_sha256")
                or row.get("symbol_master_artifact_sha256")
                != (lifecycle or {}).get("symbol_master_artifact_sha256")
            ):
                findings.append("daily_economic_reference_binding_mismatch")
            if findings:
                exclusions.append(
                    {
                        "target_date": report_date,
                        "paired_replay_parent_id": row.get("paired_replay_parent_id"),
                        "decision_trace_id": row.get("decision_trace_id"),
                        "reason": findings[0],
                        "findings": findings,
                    }
                )
                continue
            joined_rows.append({**row, "lifecycle": dict(lifecycle or {})})

    global_candidate_blockers = sorted(set(global_candidate_blockers))

    grouped: dict[tuple[str, str, str, str, str, str, str], list[dict[str, Any]]] = (
        defaultdict(list)
    )
    for row in joined_rows:
        key = (
            str(row.get("decision_stage") or ""),
            str(row.get("effective_venue") or ""),
            str(row.get("session_bucket") or ""),
            str(row.get("control_contract_sha256") or ""),
            str(row.get("candidate_contract_sha256") or ""),
            str(row.get("selected_cost_profile_id") or ""),
            str(row.get("selected_cost_profile_content_sha256") or ""),
        )
        grouped[key].append(row)

    partitions: list[dict[str, Any]] = []
    source_candidates: list[dict[str, Any]] = []
    for key, rows in sorted(grouped.items()):
        windows = {
            str(days): _window_metrics(rows, target_date=target_date, trading_days=days)
            for days in (5, 10, 20)
        }
        gate_findings = {
            window: _window_gate_findings(metrics)
            for window, metrics in windows.items()
        }
        if global_candidate_blockers:
            gate_findings["global_execution_artifact"] = list(global_candidate_blockers)
        all_gates_pass = not global_candidate_blockers and all(
            not values for values in gate_findings.values()
        )
        reference_bindings = sorted(
            {
                (
                    str(row.get("target_date") or ""),
                    str(row.get("cost_profile_artifact_sha256") or ""),
                    str(row.get("cost_catalog_content_sha256") or ""),
                    str(row.get("symbol_master_artifact_sha256") or ""),
                    str(row.get("symbol_metadata_record_sha256") or ""),
                )
                for row in rows
            }
        )
        if any(not all(binding) for binding in reference_bindings):
            all_gates_pass = False
            gate_findings["identity"] = ["economic_reference_binding_incomplete"]
        reference_binding_rows = [
            {
                "target_date": binding[0],
                "cost_profile_artifact_sha256": binding[1],
                "cost_catalog_content_sha256": binding[2],
                "symbol_master_artifact_sha256": binding[3],
                "symbol_metadata_record_sha256": binding[4],
            }
            for binding in reference_bindings
        ]
        reference_bindings_sha256 = _sha256(reference_binding_rows)
        partition = {
            "decision_stage": key[0],
            "effective_venue": key[1],
            "session_bucket": key[2],
            "control_contract_sha256": key[3],
            "candidate_contract_sha256": key[4],
            "selected_cost_profile_id": key[5],
            "selected_cost_profile_content_sha256": key[6],
            "economic_reference_bindings_sha256": reference_bindings_sha256,
            "economic_reference_binding_count": len(reference_binding_rows),
            "source_row_count": len(rows),
            "source_dates": sorted({row["target_date"] for row in rows}),
            "windows": windows,
            "gate_findings": gate_findings,
            "r3_source_candidate_eligible": all_gates_pass,
        }
        partitions.append(partition)
        if not all_gates_pass:
            continue
        candidate_content = {
            "candidate_family": "main_ai_quality_prompt_contract",
            "decision_stage": key[0],
            "effective_venue": key[1],
            "session_bucket": key[2],
            "tuning_axis": "prompt_contract_effect",
            "current_contract_sha256": key[3],
            "recommended_contract_sha256": key[4],
            "selected_cost_profile_id": key[5],
            "selected_cost_profile_content_sha256": key[6],
            "economic_reference_bindings_sha256": reference_bindings_sha256,
            "economic_reference_binding_count": len(reference_binding_rows),
            "rolling_window_sha256": _sha256(windows),
            "evidence_contract": {
                "clean_baseline_date": CLEAN_BASELINE_DATE.isoformat(),
                "required_trading_days": [5, 10, 20],
                "minimum_common_parents_20d": MIN_COMMON_PARENTS,
                "minimum_unique_symbols_20d": MIN_UNIQUE_SYMBOLS,
                "minimum_bbo_coverage_pct": MIN_BBO_COVERAGE_PCT,
                "minimum_depth_coverage_pct": MIN_DEPTH_COVERAGE_PCT,
                "minimum_relative_uplift_pct": MIN_RELATIVE_UPLIFT_PCT,
                "requires_positive_notional_net_profit_20d": True,
                "requires_nonworse_p10_tail_and_deferred_rate": True,
                "requires_reconciled_actual_lifecycle": True,
            },
            "runtime_design_status": "design_required_no_registered_consumer",
            "first_exact_candidate_approval_required": True,
            "continuous_auto_chain_eligible": False,
            "provider_or_order_authority": False,
            **OFFLINE_AUTHORITY,
        }
        candidate_sha = _sha256(candidate_content)
        source_candidates.append(
            {
                "candidate_id": f"main-ai-quality-{candidate_sha[:24]}",
                "candidate_sha256": candidate_sha,
                **candidate_content,
            }
        )

    rolling_body = {
        "schema": ROLLING_SCHEMA,
        "target_date": target_date,
        "generated_at": datetime.now(KST).isoformat(),
        "status": (
            "historical_execution_contract_blocked"
            if global_candidate_blockers
            else ("rolling_evaluated" if joined_rows else "no_joined_lifecycle_rows")
        ),
        "clean_tuning_baseline_date": CLEAN_BASELINE_DATE.isoformat(),
        "source_execution_dates": sorted(source_dates),
        "joined_parent_count": len(joined_rows),
        "excluded_parent_count": len(exclusions),
        "partitions": partitions,
        "exclusions": exclusions,
        "global_candidate_blockers": global_candidate_blockers,
        "lifecycle_report_findings": lifecycle_findings,
        "metric_role": "r2_rolling_main_lifecycle_ai_quality",
        "window_policy": "last_5_10_20_available_clean_trading_dates_same_partition",
        "primary_decision_metric": "source_quality_adjusted_ev_pct",
        "source_quality_gate": (
            "daily_audit_verified_economic_reference_exact_three_arm_and_"
            "reconciled_lifecycle"
        ),
        "forbidden_uses": [
            "daily_only_live_promotion",
            "label_horizon_as_actual_holding_duration",
            "one_sample_as_3600_signals_per_hour",
            "cross_stage_or_cross_venue_aggregation",
            "runtime_or_order_apply",
        ],
        **OFFLINE_AUTHORITY,
    }
    rolling = {**rolling_body, "artifact_content_sha256": _sha256(rolling_body)}

    manifest_body = {
        "schema": R3_SCHEMA,
        "target_date": target_date,
        "generated_at": datetime.now(KST).isoformat(),
        "status": (
            "source_only_candidate_blocked_invalid_historical_execution"
            if global_candidate_blockers
            else (
                "source_only_candidates_ready"
                if source_candidates
                else "no_source_only_candidate_passed_all_gates"
            )
        ),
        "source_rolling_artifact_sha256": rolling["artifact_content_sha256"],
        "candidate_count": len(source_candidates),
        "candidates": source_candidates,
        "global_candidate_blockers": global_candidate_blockers,
        "first_runtime_candidate_auto_apply_performed": False,
        "runtime_apply_blocker": (
            "exact_candidate_bound_operator_approval_and_trusted_registered_"
            "preopen_consumer_required"
        ),
        "continuous_tuning_contract": (
            "next_mutation_requires_previous_post_apply_attributed_and_"
            "continuation_ev_tail_held_pass"
        ),
        "metric_role": "r3_manifest_only_source_candidate",
        "window_policy": "same_stage_venue_session_single_prompt_axis",
        "primary_decision_metric": "source_quality_adjusted_ev_pct",
        "source_quality_gate": "all_r2_rolling_gates_pass",
        "forbidden_uses": [
            "self_approve_unknown_future_candidate",
            "register_runtime_family_from_source_producer",
            "preopen_or_intraday_apply",
            "order_quantity_threshold_provider_bot_or_safety_change",
        ],
        **OFFLINE_AUTHORITY,
    }
    manifest = {**manifest_body, "artifact_content_sha256": _sha256(manifest_body)}
    return rolling, manifest


CommandRunner = Callable[[Sequence[str]], subprocess.CompletedProcess[str]]


def _default_command_runner(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(command),
        cwd=Path(__file__).resolve().parents[4],
        text=True,
        capture_output=True,
        check=False,
        env={**os.environ, "PYTHONPATH": "."},
    )


def _command_step(
    *, name: str, command: Sequence[str], runner: CommandRunner
) -> dict[str, Any]:
    result = runner(command)
    return {
        "name": name,
        "command": list(command),
        "returncode": int(result.returncode),
        "stdout_tail": str(result.stdout or "")[-4000:],
        "stderr_tail": str(result.stderr or "")[-4000:],
        "status": "pass" if result.returncode == 0 else "failed",
    }


def _bridge_config_from_cost_profile(
    cost_profile_path: Path, *, target_date: str
) -> dict[str, Any]:
    from src.engine.scalping.micro_reversion.ai_quality_bridge import (
        _verified_cost_config_from_path,
    )

    config = _verified_cost_config_from_path(
        cost_profile_path, target_date=date.fromisoformat(target_date)
    )
    return asdict(config)


def _write_control_driver(
    *, target_date: str, bridge_config: Mapping[str, Any], path: Path
) -> dict[str, Any]:
    body = {
        "schema": "main_ai_quality_micro_control_driver_v1",
        "target_date": target_date,
        "bridge_config": dict(bridge_config),
        "excluded_scopes": [],
        "provider_call_performed": False,
        **OFFLINE_AUTHORITY,
    }
    artifact = {**body, "artifact_content_sha256": _sha256(body)}
    _atomic_write_json(path, artifact)
    return artifact


def _default_paths(target_date: str) -> dict[str, Path]:
    return {
        "source_audit": DATA_DIR
        / "report"
        / "observation_source_quality_audit"
        / f"observation_source_quality_audit_{target_date}.json",
        "economic_source_manifest": SOURCE_POLICY_ROOT
        / "economic_reference_sources.json",
        "economic_reference": ECONOMIC_REPORT_ROOT
        / f"micro_reversion_economic_reference_{target_date}.json",
        "cost_profile": ECONOMIC_REPORT_ROOT
        / f"micro_reversion_reviewed_cost_profile_{target_date}.json",
        "symbol_master": ECONOMIC_REPORT_ROOT
        / f"micro_reversion_symbol_master_{target_date}.json",
        "provider_pricing": SOURCE_POLICY_ROOT / "provider_pricing.json",
        "paired_report": quality.PAIRED_REPORT_DIR
        / f"ai_prompt_paired_replay_{target_date}.json",
        "bridge_report": BRIDGE_REPORT_ROOT
        / f"micro_reversion_ai_quality_bridge_{target_date}.json",
        "prepared": prepared_request_path(target_date),
        "control_driver": control_driver_path(target_date),
        "source_bundle": quality.micro_reversion_source_bundle_path(target_date),
        "materialized": quality.micro_reversion_materialized_request_path(target_date),
        "labels": action_neutral_label_path(target_date),
        "execution": quality.micro_reversion_execution_result_path(target_date),
        "lifecycle": LIFECYCLE_REPORT_ROOT
        / f"main_scalping_lifecycle_paired_{target_date}.json",
    }


def _economic_outputs(
    value: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    from src.engine.scalping.micro_reversion.economic_reference import content_sha256

    declared_artifact_hash = str(value.get("artifact_content_sha256") or "")
    top_content = {
        key: item for key, item in value.items() if key != "artifact_content_sha256"
    }
    if not declared_artifact_hash or declared_artifact_hash != content_sha256(
        top_content
    ):
        raise ValueError("economic_reference_artifact_hash_mismatch")
    if _authority_findings(value):
        raise ValueError("economic_reference_authority_invalid")
    cost = value.get("canonical_reviewed_cost_payload")
    master = value.get("canonical_symbol_master_payload")
    if not isinstance(cost, dict) or not isinstance(master, dict):
        raise ValueError("economic_reference_outputs_missing")
    if value.get("canonical_reviewed_cost_payload_sha256") != content_sha256(cost):
        raise ValueError("economic_reference_cost_payload_hash_mismatch")
    if value.get("canonical_symbol_master_payload_sha256") != content_sha256(master):
        raise ValueError("economic_reference_symbol_payload_hash_mismatch")
    for name, payload in (("cost", cost), ("symbol", master)):
        declared_hash = str(payload.get("content_sha256") or "")
        payload_content = {
            key: item for key, item in payload.items() if key != "content_sha256"
        }
        if not declared_hash or declared_hash != content_sha256(payload_content):
            raise ValueError(f"economic_reference_{name}_internal_hash_mismatch")
        if payload.get("verified") is not True or _authority_findings(payload):
            raise ValueError(f"economic_reference_{name}_not_verified")
    return dict(cost), dict(master)


def _collect_rolling_inputs(
    *, target_date: str, lookback_calendar_days: int = 60
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, bool],
    dict[str, bool],
    list[dict[str, Any]],
]:
    target = date.fromisoformat(target_date)
    execution_reports: list[dict[str, Any]] = []
    lifecycle_reports: list[dict[str, Any]] = []
    source_quality_pass: dict[str, bool] = {}
    economic_reference_pass: dict[str, bool] = {}
    diagnostics: list[dict[str, Any]] = []
    seen_artifact_identities: set[tuple[str, str, str]] = set()
    for offset in range(lookback_calendar_days - 1, -1, -1):
        current = target - timedelta(days=offset)
        if current < CLEAN_BASELINE_DATE:
            continue
        date_key = current.isoformat()
        daily_paths = {
            "execution": quality.micro_reversion_execution_result_path(date_key),
            "lifecycle": LIFECYCLE_REPORT_ROOT
            / f"main_scalping_lifecycle_paired_{date_key}.json",
            "source_quality": DATA_DIR
            / "report"
            / "observation_source_quality_audit"
            / f"observation_source_quality_audit_{date_key}.json",
            "economic_reference": ECONOMIC_REPORT_ROOT
            / f"micro_reversion_economic_reference_{date_key}.json",
        }
        for name, logical_path in daily_paths.items():
            resolved = existing_or_gzip_path(logical_path)
            if not resolved.exists():
                continue
            try:
                artifact = _load_json_auto(logical_path)
            except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
                diagnostics.append(
                    {
                        "target_date": date_key,
                        "artifact": name,
                        "status": "invalid",
                        "reason": type(exc).__name__,
                    }
                )
                continue
            embedded_target_date = str(artifact.get("target_date") or "")
            if embedded_target_date != date_key:
                diagnostics.append(
                    {
                        "target_date": date_key,
                        "artifact": name,
                        "status": "invalid",
                        "reason": "artifact_target_date_path_mismatch",
                        "embedded_target_date": embedded_target_date,
                    }
                )
                continue
            declared_identity_hash = str(
                artifact.get("report_content_sha256")
                or artifact.get("artifact_content_sha256")
                or artifact.get("summary_content_sha256")
                or ""
            )
            artifact_identity = (name, date_key, declared_identity_hash)
            if artifact_identity in seen_artifact_identities:
                diagnostics.append(
                    {
                        "target_date": date_key,
                        "artifact": name,
                        "status": "invalid",
                        "reason": "duplicate_daily_artifact_identity",
                    }
                )
                continue
            seen_artifact_identities.add(artifact_identity)
            if name == "execution":
                execution_reports.append(artifact)
            elif name == "lifecycle":
                lifecycle_reports.append(artifact)
            elif name == "source_quality":
                source_quality_pass[date_key] = not validate_source_quality_audit(
                    artifact, target_date=date_key
                )
            else:
                try:
                    _economic_outputs(artifact)
                    economic_reference_pass[date_key] = bool(
                        artifact.get("status") in {"pass", "partial"}
                        and artifact.get("tuning_input_allowed") is True
                    )
                except (TypeError, ValueError):
                    economic_reference_pass[date_key] = False
    return (
        execution_reports,
        lifecycle_reports,
        source_quality_pass,
        economic_reference_pass,
        diagnostics,
    )


def _canonical_daily_usd_cap(
    value: Decimal | float | str,
) -> tuple[Decimal, str]:
    """Canonicalize once so subprocess and receipt validate the same cap."""

    try:
        canonical = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError("daily_usd_cap_must_be_positive") from exc
    if not canonical.is_finite() or canonical <= 0:
        raise ValueError("daily_usd_cap_must_be_positive")
    return canonical, format(canonical, "f")


def _bind_current_run_rolling_inputs(
    *,
    target_date: str,
    execution_reports: Sequence[dict[str, Any]],
    lifecycle_reports: Sequence[dict[str, Any]],
    current_execution_report: dict[str, Any],
    current_provider_replay_complete: bool,
    current_lifecycle_producer_complete: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Exclude same-date artifacts unless this composed run produced them."""

    bound_execution = [
        report
        for report in execution_reports
        if str(report.get("target_date") or "") != target_date
    ]
    if current_provider_replay_complete:
        bound_execution.append(current_execution_report)
    bound_lifecycle = [
        report
        for report in lifecycle_reports
        if str(report.get("target_date") or "") != target_date
        or current_lifecycle_producer_complete
    ]
    return bound_execution, bound_lifecycle


def run_cycle(
    *,
    target_date: str,
    write: bool,
    execute_provider_replay: bool,
    daily_attempt_cap: int,
    daily_usd_cap: Decimal | float | str,
    parent_cap: int,
    paths: Mapping[str, Path] | None = None,
    command_runner: CommandRunner = _default_command_runner,
) -> dict[str, Any]:
    """Run deterministic R0/R1 and optionally bounded offline replay.

    Expected no-data, missing reviewed references, or exhausted provider budget
    produces a terminal source-only status artifact and does not fail unrelated
    postclose work. Contract/hash/authority failures remain explicit failed
    steps for the wrapper/verifier.
    """

    target = date.fromisoformat(target_date)
    if target < CLEAN_BASELINE_DATE:
        raise ValueError("target_date_before_clean_baseline")
    if isinstance(daily_attempt_cap, bool) or daily_attempt_cap <= 0:
        raise ValueError("daily_attempt_cap_must_be_positive")
    canonical_daily_usd_cap, canonical_daily_usd_cap_text = _canonical_daily_usd_cap(
        daily_usd_cap
    )
    if isinstance(parent_cap, bool) or parent_cap <= 0:
        raise ValueError("parent_cap_must_be_positive")

    selected_paths = {**_default_paths(target_date), **dict(paths or {})}
    steps: list[dict[str, Any]] = []
    blockers: list[str] = []
    materialized: dict[str, Any] = {}
    labels: dict[str, Any] = {}
    current_execution_report: dict[str, Any] = {}
    current_provider_replay_complete = False

    try:
        audit = _load_json_auto(selected_paths["source_audit"])
        audit_findings = validate_source_quality_audit(audit, target_date=target_date)
        if audit_findings:
            blockers.extend(audit_findings)
        audit_source = _raw_artifact(selected_paths["source_audit"])
    except (
        FileNotFoundError,
        OSError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        audit = {}
        audit_source = {}
        blockers.append(f"source_quality_audit_unavailable:{type(exc).__name__}")

    economic_command = [
        sys.executable,
        "-m",
        "src.engine.scalping.micro_reversion.economic_reference",
        "--target-date",
        target_date,
        "--source-manifest",
        str(selected_paths["economic_source_manifest"]),
        "--output",
        str(selected_paths["economic_reference"]),
    ]
    if write:
        steps.append(
            _command_step(
                name="economic_reference",
                command=economic_command,
                runner=command_runner,
            )
        )
        if steps[-1]["returncode"] != 0:
            blockers.append("economic_reference_command_failed")
    else:
        blockers.append("write_required_for_composed_r0_r3_artifact_chain")

    economic: dict[str, Any] = {}
    cost_profile: dict[str, Any] = {}
    symbol_master: dict[str, Any] = {}
    if selected_paths["economic_reference"].exists():
        try:
            economic = _load_json_auto(selected_paths["economic_reference"])
            if (
                economic.get("status") not in {"pass", "partial"}
                or economic.get("tuning_input_allowed") is not True
            ):
                blockers.append("economic_reference_not_verified")
            cost_profile, symbol_master = _economic_outputs(economic)
            if write:
                _atomic_write_json(selected_paths["cost_profile"], cost_profile)
                _atomic_write_json(selected_paths["symbol_master"], symbol_master)
        except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
            blockers.append(f"economic_reference_invalid:{type(exc).__name__}")
    else:
        blockers.append("economic_reference_artifact_missing")

    paired_report: dict[str, Any] = {}
    if not blockers:
        try:
            paired_report = _load_json_auto(selected_paths["paired_report"])
            prepared = build_prepared_request_artifact(
                target_date=target_date,
                paired_report=paired_report,
                source=_raw_artifact(selected_paths["paired_report"]),
            )
            if not prepared["prepared_request_count"]:
                blockers.append("prepared_request_census_empty")
            if write:
                _atomic_write_json(selected_paths["prepared"], prepared)
            bridge_config = _bridge_config_from_cost_profile(
                selected_paths["cost_profile"], target_date=target_date
            )
            if write:
                _write_control_driver(
                    target_date=target_date,
                    bridge_config=bridge_config,
                    path=selected_paths["control_driver"],
                )
        except (
            FileNotFoundError,
            OSError,
            TypeError,
            ValueError,
            json.JSONDecodeError,
        ) as exc:
            blockers.append(f"r0_prepared_contract_failed:{type(exc).__name__}:{exc}")

    if not blockers:
        bridge_command = [
            sys.executable,
            "-m",
            "src.engine.scalping.micro_reversion.ai_quality_bridge",
            "--date",
            target_date,
            "--verified-cost-profile",
            str(selected_paths["cost_profile"]),
            "--symbol-master",
            str(selected_paths["symbol_master"]),
        ]
        if write:
            bridge_command.append("--write")
        steps.append(
            _command_step(name="bridge", command=bridge_command, runner=command_runner)
        )
        if steps[-1]["returncode"] != 0:
            blockers.append("bridge_command_failed")

    if not blockers:
        source_command = [
            sys.executable,
            "-m",
            "src.engine.scalping.ai_decision_quality",
            "--date",
            target_date,
            "--mode",
            "micro_reversion_source_bundle",
            "--micro-reversion-prepared-requests",
            str(selected_paths["prepared"]),
            "--micro-reversion-control-contracts",
            str(selected_paths["control_driver"]),
            "--micro-reversion-symbol-master",
            str(selected_paths["symbol_master"]),
        ]
        if write:
            source_command.append("--write")
        steps.append(
            _command_step(
                name="source_bundle", command=source_command, runner=command_runner
            )
        )
        if steps[-1]["returncode"] != 0:
            blockers.append("source_bundle_command_failed")

    if not blockers:
        materialize_command = [
            sys.executable,
            "-m",
            "src.engine.scalping.ai_decision_quality",
            "--date",
            target_date,
            "--mode",
            "micro_reversion_materialize",
            "--micro-reversion-prepared-requests",
            str(selected_paths["prepared"]),
            "--micro-reversion-source-bundle",
            str(selected_paths["source_bundle"]),
        ]
        if write:
            materialize_command.append("--write")
        steps.append(
            _command_step(
                name="materialize", command=materialize_command, runner=command_runner
            )
        )
        if steps[-1]["returncode"] != 0:
            blockers.append("materialize_command_failed")

    if not blockers:
        try:
            bridge = _load_json_auto(selected_paths["bridge_report"])
            materialized = _load_json_auto(selected_paths["materialized"])
            labels = quality.build_micro_reversion_action_neutral_outcome_labels(
                bridge_report=bridge,
                materialized_report=materialized,
            )
            if write:
                _atomic_write_json(selected_paths["labels"], labels)
            if int(labels.get("eligible_label_count") or 0) <= 0:
                blockers.append("action_neutral_label_census_empty")
        except (
            FileNotFoundError,
            OSError,
            TypeError,
            ValueError,
            json.JSONDecodeError,
        ) as exc:
            blockers.append(f"action_neutral_label_failed:{type(exc).__name__}:{exc}")

    if execute_provider_replay and not blockers:
        max_new_requests = parent_cap * len(EXPECTED_ARMS)
        execute_command = [
            sys.executable,
            "-m",
            "src.engine.scalping.ai_decision_quality",
            "--date",
            target_date,
            "--mode",
            "micro_reversion_execute",
            "--micro-reversion-materialized-requests",
            str(selected_paths["materialized"]),
            "--micro-reversion-outcome-labels",
            str(selected_paths["labels"]),
            "--micro-reversion-provider-pricing",
            str(selected_paths["provider_pricing"]),
            "--micro-reversion-provider-daily-attempt-cap",
            str(daily_attempt_cap),
            "--micro-reversion-provider-daily-usd-cap",
            canonical_daily_usd_cap_text,
            "--execute-candidate",
            "--candidate-workers",
            "1",
            "--candidate-max-new-requests",
            str(max_new_requests),
        ]
        if write:
            execute_command.append("--write")
        steps.append(
            _command_step(
                name="bounded_provider_replay",
                command=execute_command,
                runner=command_runner,
            )
        )
        if steps[-1]["returncode"] != 0:
            blockers.append("bounded_provider_replay_failed_or_deferred")
        else:
            try:
                current_execution_report = _load_json_auto(selected_paths["execution"])
                current_pricing = _load_json_auto(selected_paths["provider_pricing"])
                _validate_current_execution_artifact(
                    report=current_execution_report,
                    target_date=target_date,
                    materialized_report=materialized,
                    outcome_label_artifact=labels,
                    expected_max_new_requests=max_new_requests,
                    expected_daily_attempt_cap=daily_attempt_cap,
                    expected_daily_usd_cap=canonical_daily_usd_cap,
                    expected_pricing_content_sha256=str(
                        current_pricing.get("artifact_content_sha256") or ""
                    ),
                )
                current_provider_replay_complete = True
            except (
                FileNotFoundError,
                OSError,
                TypeError,
                ValueError,
                json.JSONDecodeError,
            ) as exc:
                steps[-1]["status"] = "failed_artifact_contract"
                blockers.append(
                    "bounded_provider_replay_artifact_invalid:"
                    f"{type(exc).__name__}:{exc}"
                )

    lifecycle_command = [
        sys.executable,
        "-m",
        "src.engine.scalping.main_lifecycle_paired",
        "--date",
        target_date,
    ]
    if cost_profile and symbol_master:
        reviewed_cost_payload_sha256 = str(
            economic.get("canonical_reviewed_cost_payload_sha256") or ""
        )
        symbol_master_payload_sha256 = str(
            economic.get("canonical_symbol_master_payload_sha256") or ""
        )
        lifecycle_command.extend(
            [
                "--reviewed-cost-profile-sha256",
                reviewed_cost_payload_sha256,
                "--reviewed-cost-profile-verified",
                "--symbol-master-artifact-sha256",
                symbol_master_payload_sha256,
                "--symbol-master-artifact-verified",
            ]
        )
    if write:
        lifecycle_command.append("--write")
    steps.append(
        _command_step(
            name="main_lifecycle_paired",
            command=lifecycle_command,
            runner=command_runner,
        )
    )
    current_lifecycle_producer_complete = bool(write and steps[-1]["returncode"] == 0)
    if not current_lifecycle_producer_complete:
        blockers.append("main_lifecycle_paired_command_failed")

    rolling_diagnostics: list[dict[str, Any]] = []
    try:
        (
            execution_reports,
            lifecycle_reports,
            source_quality_pass,
            economic_reference_pass,
            rolling_diagnostics,
        ) = _collect_rolling_inputs(target_date=target_date)
        # Stale same-date artifacts must not join current evidence when either
        # producer step was skipped, failed, or emitted an invalid receipt.
        execution_reports, lifecycle_reports = _bind_current_run_rolling_inputs(
            target_date=target_date,
            execution_reports=execution_reports,
            lifecycle_reports=lifecycle_reports,
            current_execution_report=current_execution_report,
            current_provider_replay_complete=current_provider_replay_complete,
            current_lifecycle_producer_complete=(current_lifecycle_producer_complete),
        )
        rolling, r3_manifest = build_rolling_source_only_candidates(
            target_date=target_date,
            execution_reports=execution_reports,
            lifecycle_reports=lifecycle_reports,
            source_quality_pass_by_date=source_quality_pass,
            economic_reference_pass_by_date=economic_reference_pass,
            input_diagnostics=rolling_diagnostics,
        )
        if write:
            _atomic_write_json(rolling_report_path(target_date), rolling)
            _atomic_write_json(r3_manifest_path(target_date), r3_manifest)
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        rolling = {}
        r3_manifest = {}
        blockers.append(f"rolling_r2_r3_failed:{type(exc).__name__}:{exc}")

    provider_call_performed = bool(
        current_provider_replay_complete
        and int(current_execution_report.get("new_result_count") or 0) > 0
        and current_execution_report.get("candidate_model_call_attempted") is True
        and current_execution_report.get("provider_call_performed") is True
    )

    body = {
        "schema": CYCLE_SCHEMA,
        "target_date": target_date,
        "generated_at": datetime.now(KST).isoformat(),
        "status": (
            "r0_r1_materialized_provider_replay_bounded"
            if execute_provider_replay and not blockers
            else (
                "r0_r1_materialized_provider_replay_not_requested"
                if not execute_provider_replay and not blockers
                else "source_only_blocked_or_deferred"
            )
        ),
        "steps": steps,
        "blockers": blockers,
        "source_quality_audit": audit_source,
        "economic_reference_path": str(selected_paths["economic_reference"]),
        "prepared_request_path": str(selected_paths["prepared"]),
        "bridge_report_path": str(selected_paths["bridge_report"]),
        "source_bundle_path": str(selected_paths["source_bundle"]),
        "materialized_request_path": str(selected_paths["materialized"]),
        "action_neutral_label_path": str(selected_paths["labels"]),
        "execution_result_path": str(selected_paths["execution"]),
        "main_lifecycle_report_path": str(selected_paths["lifecycle"]),
        "rolling_report_path": str(rolling_report_path(target_date)),
        "r3_manifest_path": str(r3_manifest_path(target_date)),
        "rolling_status": rolling.get("status"),
        "r3_status": r3_manifest.get("status"),
        "r3_source_candidate_count": int(r3_manifest.get("candidate_count") or 0),
        "rolling_input_diagnostics": rolling_diagnostics,
        "provider_execution_requested": execute_provider_replay,
        "current_provider_replay_complete": current_provider_replay_complete,
        "provider_budget": {
            "daily_attempt_cap": daily_attempt_cap,
            "daily_usd_cap": canonical_daily_usd_cap_text,
            "parent_cap": parent_cap,
            "maximum_logical_requests": parent_cap * len(EXPECTED_ARMS),
            "maximum_schema_attempts_per_request": quality.CANDIDATE_SCHEMA_MAX_ATTEMPTS,
            "reviewed_pricing_artifact_required": True,
        },
        "r3_runtime_apply_performed": False,
        "first_exact_candidate_approval_required": True,
        "provider_call_performed": provider_call_performed,
        "forbidden_uses": [
            "source_producer_self_approval",
            "runtime_prompt_or_order_apply",
            "quantity_threshold_provider_route_bot_or_safety_change",
        ],
        **OFFLINE_AUTHORITY,
    }
    report = {**body, "artifact_content_sha256": _sha256(body)}
    if write:
        _atomic_write_json(cycle_report_path(target_date), report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--execute-provider-replay", action="store_true")
    parser.add_argument("--daily-attempt-cap", type=int, default=12)
    parser.add_argument("--daily-usd-cap", type=Decimal, default=Decimal("1.0"))
    parser.add_argument("--parent-cap", type=int, default=1)
    args = parser.parse_args(argv)

    report = run_cycle(
        target_date=args.date,
        write=args.write,
        execute_provider_replay=args.execute_provider_replay,
        daily_attempt_cap=args.daily_attempt_cap,
        daily_usd_cap=args.daily_usd_cap,
        parent_cap=args.parent_cap,
    )
    print(
        json.dumps(
            {
                "schema": report["schema"],
                "target_date": report["target_date"],
                "status": report["status"],
                "blockers": report["blockers"],
                "output": str(cycle_report_path(args.date)) if args.write else None,
                **OFFLINE_AUTHORITY,
            },
            ensure_ascii=False,
        )
    )
    return 0 if not report.get("blockers") else 2


if __name__ == "__main__":
    raise SystemExit(main())
