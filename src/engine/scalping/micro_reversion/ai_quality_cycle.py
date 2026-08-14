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
from src.engine.scalping.micro_reversion.contracts import CLEAN_BASELINE_DATE
from src.utils.constants import DATA_DIR
from src.utils.jsonl_io import existing_or_gzip_path

KST = ZoneInfo("Asia/Seoul")

CYCLE_SCHEMA = "main_ai_quality_postclose_r0_r3_cycle_v1"
PREPARED_SCHEMA = "main_ai_quality_micro_prepared_requests_v1"
ROLLING_SCHEMA = "main_ai_quality_rolling_paired_evaluation_v1"
R3_SCHEMA = "main_ai_quality_source_only_candidate_manifest_v1"
LIFECYCLE_REPORT_SCHEMA = "main_scalping_lifecycle_paired_daily_v1"

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


def _validated_execution_rows(report: Mapping[str, Any]) -> list[dict[str, Any]]:
    if report.get("schema") != quality.MICRO_REVERSION_EXECUTION_RESULT_SCHEMA:
        raise ValueError("execution_report_schema_invalid")
    if report.get("report_content_sha256") != _content_hash(
        report, "report_content_sha256"
    ):
        raise ValueError("execution_report_content_hash_mismatch")
    if _authority_findings(report):
        raise ValueError("execution_report_authority_invalid")
    results = report.get("results")
    if not isinstance(results, list):
        raise ValueError("execution_report_results_invalid")
    result_count = len(results)
    request_count = report.get("request_count")
    status = report.get("status")
    deferred_request_count = int(report.get("deferred_request_count") or 0)
    uncommitted_result_count = int(report.get("uncommitted_result_count") or 0)
    newly_committed_parent_count = report.get("newly_committed_parent_count")
    new_result_count = report.get("new_result_count")
    execution_exclusions = report.get("execution_exclusions")
    blocking_execution_exclusions = report.get(
        "blocking_execution_exclusions"
    )
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
        or int(report.get("execution_failed_count") or 0) != 0
        or not isinstance(execution_exclusions, list)
        or report.get("execution_exclusion_count") != len(execution_exclusions)
        or not isinstance(blocking_execution_exclusions, list)
        or report.get("blocking_execution_exclusion_count")
        != len(blocking_execution_exclusions)
        or bool(blocking_execution_exclusions)
        or uncommitted_result_count != 0
        or int(report.get("provider_provenance_pass_count") or 0) != result_count
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
    rows = evaluation.get("rows")
    if not isinstance(rows, list):
        raise ValueError("three_arm_evaluation_rows_invalid")

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
    completed_parent_ids = set(result_contracts)
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
            continue
        parent = str(row.get("paired_replay_parent_id") or "")
        arms = row.get("arms")
        contracts = result_contracts.get(parent, {})
        if not parent or not isinstance(arms, Mapping):
            continue
        if set(arms) != set(EXPECTED_ARMS) or set(contracts) != set(EXPECTED_ARMS):
            continue
        micro_control = arms["replay_control_exact_plus_micro"]
        candidate = arms["replay_candidate_exact_plus_micro"]
        if not isinstance(micro_control, Mapping) or not isinstance(candidate, Mapping):
            continue
        control_ev = _finite_number(micro_control.get("source_quality_adjusted_ev_pct"))
        candidate_ev = _finite_number(candidate.get("source_quality_adjusted_ev_pct"))
        if control_ev is None or candidate_ev is None:
            continue
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
            continue
        selected_profile_id = str(row.get("selected_cost_profile_id") or "").strip()
        if not selected_profile_id:
            continue
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
        quality._micro_reversion_materialized_request_census_sha256(
            materialized_report
        )
    ):
        raise ValueError("current_execution_materialized_census_hash_mismatch")
    if report.get("outcome_label_artifact_sha256") != _sha256(
        outcome_label_artifact
    ):
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
            "micro_reversion_replay_arm": request.get(
                "micro_reversion_replay_arm"
            ),
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
    quality._validate_micro_reversion_outcome_label_artifact(
        outcome_label_artifact
    )
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
    if (
        any(result_id not in request_by_id for result_id in bound_result_request_ids)
        or len(bound_result_request_ids) != len(set(bound_result_request_ids))
    ):
        raise ValueError("current_execution_result_request_census_invalid")
    expected_deferred_request_ids = [
        request_id
        for request_id in request_ids
        if request_id not in set(bound_result_request_ids)
    ]
    if (
        report.get("deferred_request_ids") != expected_deferred_request_ids
        or report.get("deferred_request_count")
        != len(expected_deferred_request_ids)
    ):
        raise ValueError("current_execution_deferred_request_census_mismatch")
    selected_request_ids = report.get("selected_request_ids")
    selected_parent_ids = report.get("selected_parent_ids")
    if (
        not isinstance(selected_request_ids, list)
        or any(request_id not in bound_result_request_ids for request_id in selected_request_ids)
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
        if str(exclusion.get("paired_replay_parent_id") or "")
        in blocking_parent_ids
    ]
    if (
        report.get("blocking_execution_exclusions")
        != expected_blocking_exclusions
        or report.get("blocking_execution_exclusion_count")
        != len(expected_blocking_exclusions)
    ):
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


def _lifecycle_index(
    lifecycle_reports: Iterable[Mapping[str, Any]],
) -> tuple[dict[tuple[str, str], dict[str, Any]], list[str]]:
    index: dict[tuple[str, str], dict[str, Any]] = {}
    ambiguous_keys: set[tuple[str, str]] = set()
    findings: list[str] = []
    for report in lifecycle_reports:
        target_date = str(report.get("target_date") or "")
        rows = report.get("rows")
        if report.get("schema") != LIFECYCLE_REPORT_SCHEMA:
            findings.append(
                f"lifecycle_report_schema_invalid:{target_date or 'missing'}"
            )
            continue
        if not target_date or not isinstance(rows, list):
            findings.append("lifecycle_report_shape_invalid")
            continue
        if _authority_findings(report):
            findings.append(f"lifecycle_report_authority_invalid:{target_date}")
            continue
        declared_hash = report.get("artifact_content_sha256")
        if not declared_hash or declared_hash != _content_hash(
            report, "artifact_content_sha256"
        ):
            findings.append(f"lifecycle_report_hash_invalid:{target_date}")
            continue
        for row in rows:
            if not isinstance(row, Mapping):
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
                    findings.append(
                        f"lifecycle_trace_identity_ambiguous:{target_date}:{key[1]}"
                    )
                    index.pop(key, None)
                    ambiguous_keys.add(key)
                    continue
                index[key] = dict(row)
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
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build strict rolling R2 evidence and an R3 source-only manifest."""

    lifecycle_index, lifecycle_findings = _lifecycle_index(lifecycle_reports)
    joined_rows: list[dict[str, Any]] = []
    exclusions: list[dict[str, Any]] = []
    source_dates: set[str] = set()
    for report in execution_reports:
        try:
            rows = _validated_execution_rows(report)
        except (TypeError, ValueError) as exc:
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
        all_gates_pass = all(not values for values in gate_findings.values())
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
        "status": "rolling_evaluated" if joined_rows else "no_joined_lifecycle_rows",
        "clean_tuning_baseline_date": CLEAN_BASELINE_DATE.isoformat(),
        "source_execution_dates": sorted(source_dates),
        "joined_parent_count": len(joined_rows),
        "excluded_parent_count": len(exclusions),
        "partitions": partitions,
        "exclusions": exclusions,
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
            "source_only_candidates_ready"
            if source_candidates
            else "no_source_only_candidate_passed_all_gates"
        ),
        "source_rolling_artifact_sha256": rolling["artifact_content_sha256"],
        "candidate_count": len(source_candidates),
        "candidates": source_candidates,
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
    canonical_daily_usd_cap, canonical_daily_usd_cap_text = (
        _canonical_daily_usd_cap(daily_usd_cap)
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
                current_execution_report = _load_json_auto(
                    selected_paths["execution"]
                )
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
    current_lifecycle_producer_complete = bool(
        write and steps[-1]["returncode"] == 0
    )
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
            current_lifecycle_producer_complete=(
                current_lifecycle_producer_complete
            ),
        )
        rolling, r3_manifest = build_rolling_source_only_candidates(
            target_date=target_date,
            execution_reports=execution_reports,
            lifecycle_reports=lifecycle_reports,
            source_quality_pass_by_date=source_quality_pass,
            economic_reference_pass_by_date=economic_reference_pass,
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
