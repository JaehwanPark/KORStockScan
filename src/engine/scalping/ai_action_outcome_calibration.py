"""Cumulative exact-trace action/outcome calibration and OFI attribution audit.

This producer replaces the legacy WATCHING numeric-score smoothing diagnostic.
It never changes a live score or action.  It accumulates mature paired replay
outcomes keyed by exact decision trace, then reports action transitions, EV,
error taxonomy, and OFI runtime postprocessor attribution coverage.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import tempfile
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from statistics import fmean
from typing import Any, Iterable
from zoneinfo import ZoneInfo

from src.utils.jsonl_io import existing_or_gzip_path, iter_jsonl

KST = ZoneInfo("Asia/Seoul")
CLEAN_BASELINE_DATE = "2026-06-05"
SCHEMA = "ai_decision_action_outcome_calibration_v2"
POLICY_VERSION = "exact_decision_trace_cumulative_action_outcome_v5"
PROBE_RISK_GATE_VERSION = "bounded_probe_recovery_risk_v2"
DETAILED_PAIRED_SCHEMA = "ai_prompt_detailed_paired_replay_v1"
DETAILED_SELF_HASH_CUTOVER_DATE = "2026-09-07"
MAXIMUM_BOUNDED_PROBE_LOSS_PCT = 2.0
SEVERE_TAIL_ADVERSE_PCT = -2.0
CATASTROPHIC_LOSS_PCT = -5.0
MAXIMUM_LOSS_BUDGET_BREACH_RATE_PCT = 20.0
MAXIMUM_SEVERE_TAIL_RATE_PCT = 20.0
OFI_LEDGER_SCHEMA = "ofi_exact_trace_action_outcome_calibration_v2"
ACTION_OUTCOME_OPTIMIZER_HANDOFF_SCHEMA = "ai_action_outcome_optimizer_handoff_v1"
REPORT_SUBDIR = "ai_decision_action_outcome_calibration"
PAIRED_SUBDIR = "ai_prompt_detailed_paired_replay"
OFI_STAGES = {
    "entry_ai_price_ofi_skip_demoted",
    "holding_flow_ofi_smoothing_applied",
}
EXPOSURE_ACTIONS = {
    "BUY",
    "ADD",
    "CONTINUE",
    "HOLD",
    "HOLD_OVERNIGHT",
    "USE_DEFENSIVE",
    "USE_REFERENCE",
    "IMPROVE_LIMIT",
}
NO_EXPOSURE_ACTIONS = {
    "DROP",
    "WAIT",
    "NO_ADD",
    "STOP",
    "EXIT",
    "SELL",
    "SELL_TODAY",
    "EXIT_BEFORE_CLOSE",
    "SKIP",
}
OFFLINE_CONTRACT = {
    "metric_role": "ai_decision_action_outcome_calibration",
    "decision_authority": "offline_prompt_calibration_only_no_runtime_change",
    "window_policy": "clean_baseline_through_target_date_exact_trace_mature_outcome",
    "sample_floor": "one_eligible_exact_trace_updates_cumulative_learning",
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "source_quality_gate": "exact_trace_same_venue_session_mature_outcome",
    "runtime_effect": False,
    "runtime_authority": False,
    "order_authority": False,
    "provider_authority": False,
    "allowed_runtime_apply": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
    "forbidden_uses": [
        "standalone_live_action_or_score_mutation",
        "prompt_promotion_without_reviewed_paired_replay",
        "provider_or_model_change",
        "threshold_price_quantity_or_cap_change",
        "broker_or_hard_safety_bypass",
        "counterfactual_realized_pnl_merge",
        "bot_restart",
    ],
}

PROMPT_REVIEW_GATE = {
    "minimum_exact_trace_count": 30,
    "minimum_unique_symbol_count": 10,
    "minimum_independent_source_date_count": 2,
    "minimum_candidate_exposure_count": 5,
    "diagnostic_minimum_candidate_exposure_rate_pct": 2.0,
    "maximum_false_drop_rate_pct": 10.0,
    "maximum_schema_rejection_rate_pct": 1.0,
    "require_positive_candidate_ev": True,
    "require_positive_candidate_exposure_ev": True,
    "require_positive_probe_cost_adjusted_ev": True,
    "require_positive_ev_delta": True,
    "maximum_bounded_probe_loss_pct": MAXIMUM_BOUNDED_PROBE_LOSS_PCT,
    "maximum_loss_budget_breach_rate_pct": (MAXIMUM_LOSS_BUDGET_BREACH_RATE_PCT),
    "maximum_severe_tail_rate_pct": MAXIMUM_SEVERE_TAIL_RATE_PCT,
    "catastrophic_loss_threshold_pct": CATASTROPHIC_LOSS_PCT,
}
R3_HANDOFF_EVIDENCE_FLOOR = {
    "minimum_candidate_exposure_count": 10,
    "minimum_candidate_exposure_unique_symbol_count": 3,
    "authority": "evidence_handoff_only_separate_r3_required",
}
DOWNSTREAM_RUNTIME_GUARDS = [
    "separate_runtime_apply_candidate_required",
    "one_share_probe_first",
    "fresh_quote_and_stale_conflict_guard",
    "broker_account_order_quantity_cooldown_guards",
    "post_probe_direction_and_price_resolver",
    "hard_protect_emergency_exit_guards",
    "post_apply_action_outcome_attribution",
]


def _number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _native_nonnegative_int(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value


def _canonical_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _artifact_content_sha256_valid(payload: dict[str, Any]) -> bool:
    declared = payload.get("artifact_content_sha256")
    if not _is_sha256(declared):
        return False
    body = {
        key: value for key, value in payload.items() if key != "artifact_content_sha256"
    }
    return declared == _canonical_sha256(body)


def _with_artifact_content_sha256(payload: dict[str, Any]) -> dict[str, Any]:
    body = {
        key: value for key, value in payload.items() if key != "artifact_content_sha256"
    }
    return {**body, "artifact_content_sha256": _canonical_sha256(body)}


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temp_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    try:
        with os.fdopen(file_descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp_name, 0o600)
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise


def report_path(target_date: str, report_root: Path = Path("data/report")) -> Path:
    return (
        report_root
        / REPORT_SUBDIR
        / f"ai_decision_action_outcome_calibration_{target_date}.json"
    )


def _report_date(path: Path, report: dict[str, Any]) -> str:
    target_date = str(report.get("target_date") or "")
    try:
        date.fromisoformat(target_date)
    except ValueError:
        return ""
    match = re.search(r"\d{4}-\d{2}-\d{2}", path.name)
    if match is None or match.group(0) != target_date:
        return ""
    return target_date


def _normalized_stage(value: Any) -> str:
    return str(value or "").strip().lower()


def _normalized_venue(value: Any) -> str:
    return str(value or "").strip().upper()


def _normalized_session(value: Any) -> str:
    return str(value or "").strip().upper()


def _probe_worst_loss(row: dict[str, Any], actor: str) -> float | None:
    actor_value = row.get(f"{actor}_probe_worst_loss_pct")
    if actor_value is not None:
        return _number(actor_value)
    return _number(row.get("probe_worst_loss_pct"))


def _kst_date_from_aware_timestamp(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return ""
    if parsed.tzinfo is None:
        return ""
    return parsed.astimezone(KST).date().isoformat()


def _candidate_source_contract(
    path: Path,
    report: dict[str, Any],
    *,
    target_date: str,
) -> tuple[
    tuple[str, str, str, str, str] | None,
    list[dict[str, Any]],
    dict[str, Any],
]:
    """Validate and isolate one detailed replay report.

    Historical hashless reports remain visible as diagnostic learning sources,
    but they cannot create a review candidate. New reports at/after the cutover
    must carry a valid embedded content hash.
    """

    source_date = _report_date(path, report)
    errors: list[str] = []
    warnings: list[str] = []
    exclusions: Counter[str] = Counter()
    if report.get("schema") != DETAILED_PAIRED_SCHEMA:
        errors.append("schema_invalid")
    if not source_date:
        errors.append("target_date_or_filename_mismatch")
    elif source_date < CLEAN_BASELINE_DATE or source_date > target_date:
        errors.append("source_date_outside_clean_window")
    if (
        isinstance(report.get("model_comparison_contract"), dict)
        and report["model_comparison_contract"].get("enabled") is True
    ):
        errors.append("model_comparison_artifact_excluded")
    for key, expected in (
        ("runtime_effect", False),
        ("allowed_runtime_apply", False),
        ("actual_order_submitted", False),
        ("broker_order_forbidden", True),
    ):
        if report.get(key) is not expected:
            errors.append(f"{key}_contract_invalid")
    learning_contract = report.get("calibration_source_contract")
    if learning_contract is not None:
        learning_contract = (
            learning_contract if isinstance(learning_contract, dict) else {}
        )
        retained = _native_nonnegative_int(learning_contract.get("retained_pair_count"))
        excluded = _native_nonnegative_int(
            learning_contract.get("excluded_request_count")
        )
        requested = _native_nonnegative_int(learning_contract.get("request_count"))
        if not (
            learning_contract.get("schema") == "ai_paired_calibration_source_v1"
            and learning_contract.get("global_integrity_pass") is True
            and learning_contract.get("decision_authority")
            == "calibration_learning_only"
            and learning_contract.get("runtime_apply_authority") is False
            and retained is not None
            and excluded is not None
            and requested is not None
            and retained + excluded == requested
            and requested == _native_nonnegative_int(report.get("request_count"))
            and isinstance(report.get("paired_comparisons"), list)
            and retained == len(report["paired_comparisons"])
            and learning_contract.get("retained_pairs_sha256")
            == _canonical_sha256(report["paired_comparisons"])
        ):
            errors.append("calibration_source_contract_invalid")
    elif report.get("promotion_report_integrity_pass") is not True:
        errors.append("promotion_report_integrity_not_pass")

    cohort = report.get("promotion_cohort_scope")
    cumulative = report.get("cumulative_learning")
    cohort = cohort if isinstance(cohort, dict) else {}
    cumulative = cumulative if isinstance(cumulative, dict) else {}
    stages = cohort.get("stages") if isinstance(cohort.get("stages"), list) else []
    venues = (
        cohort.get("effective_venues")
        if isinstance(cohort.get("effective_venues"), list)
        else []
    )
    sessions = (
        cohort.get("session_buckets")
        if isinstance(cohort.get("session_buckets"), list)
        else []
    )
    stage = _normalized_stage(stages[0]) if len(stages) == 1 else ""
    venue = _normalized_venue(venues[0]) if len(venues) == 1 else ""
    session = _normalized_session(sessions[0]) if len(sessions) == 1 else ""
    if (
        not stage
        or not venue
        or not session
        or cohort.get("isolated") is not True
        or cohort.get("candidate_contract_isolated") is not True
        or cohort.get("cross_cohort_promotion_forbidden") is not True
    ):
        errors.append("stage_venue_session_cohort_not_isolated")
    cohort_filter = report.get("cohort_filter")
    if not (
        isinstance(cohort_filter, dict)
        and _normalized_venue(cohort_filter.get("effective_venue")) == venue
        and _normalized_session(cohort_filter.get("session_bucket")) == session
    ):
        errors.append("cohort_filter_mismatch")

    candidate_version = str(cumulative.get("candidate_prompt_version") or "").strip()
    candidate_contract_sha256 = str(
        report.get("candidate_contract_sha256") or ""
    ).strip()
    if not candidate_version:
        errors.append("candidate_prompt_version_missing")
    if not _is_sha256(candidate_contract_sha256):
        errors.append("candidate_contract_sha256_invalid")
    if (
        cumulative.get("as_of_date") != source_date
        or cumulative.get("clean_tuning_baseline_date") != CLEAN_BASELINE_DATE
    ):
        errors.append("cumulative_window_contract_invalid")
    if (
        cumulative.get("candidate_contract_sha256") != candidate_contract_sha256
        or cohort.get("candidate_contract_sha256") != candidate_contract_sha256
    ):
        errors.append("candidate_contract_binding_mismatch")

    candidate_requests = [
        row.get("candidate")
        for row in report.get("requests") or []
        if isinstance(row, dict) and isinstance(row.get("candidate"), dict)
    ]
    request_versions = {
        str(candidate.get("prompt_version") or "").strip()
        for candidate in candidate_requests
    }
    prompt_hashes = {
        str(candidate.get("system_prompt_sha256") or "").strip()
        for candidate in candidate_requests
    }
    contract_hashes = {
        str(candidate.get("contract_sha256") or "").strip()
        for candidate in candidate_requests
    }
    if (
        not candidate_requests
        or len(request_versions) != 1
        or not all(
            version == candidate_version or version.startswith(f"{candidate_version}_")
            for version in request_versions
        )
        or len(prompt_hashes) != 1
        or not all(_is_sha256(value) for value in prompt_hashes)
        or contract_hashes != {candidate_contract_sha256}
    ):
        errors.append("candidate_request_contract_mismatch")
    candidate_prompt_sha256 = next(iter(prompt_hashes), "")

    hash_declared = report.get("artifact_content_sha256") is not None
    hash_verified = _artifact_content_sha256_valid(report)
    if hash_declared and not hash_verified:
        errors.append("artifact_content_sha256_mismatch")
    elif not hash_declared:
        if source_date >= DETAILED_SELF_HASH_CUTOVER_DATE:
            errors.append("artifact_content_sha256_missing_after_cutover")
        else:
            warnings.append("legacy_hashless_source_diagnostic_only")

    raw_comparisons = report.get("paired_comparisons")
    if not isinstance(raw_comparisons, list):
        errors.append("paired_comparisons_missing")
        raw_comparisons = []
    declared_count = report.get("paired_comparable_count")
    if (
        isinstance(declared_count, bool)
        or not isinstance(declared_count, int)
        or declared_count != len(raw_comparisons)
    ):
        errors.append("paired_comparable_count_mismatch")
    comparisons: list[dict[str, Any]] = []
    for row in raw_comparisons:
        if not isinstance(row, dict):
            exclusions["row_not_object"] += 1
            continue
        trace_id = str(row.get("decision_trace_id") or "").strip()
        row_date = _kst_date_from_aware_timestamp(row.get("decision_ts"))
        if not trace_id:
            exclusions["decision_trace_id_missing"] += 1
        elif _normalized_stage(row.get("stage")) != stage:
            exclusions["stage_mismatch"] += 1
        elif _normalized_venue(row.get("effective_venue")) != venue:
            exclusions["venue_mismatch"] += 1
        elif _normalized_session(row.get("session_bucket")) != session:
            exclusions["session_mismatch"] += 1
        elif not row_date:
            exclusions["decision_timestamp_invalid_or_naive"] += 1
        elif row_date != source_date:
            exclusions["decision_date_mismatch"] += 1
        elif _number(row.get("outcome_return_pct")) is None:
            exclusions["mature_outcome_missing"] += 1
        elif row.get("candidate_execution_cost_contract_applied") is True and any(
            str(row.get(f"{actor}_action") or "").upper() in EXPOSURE_ACTIONS
            and (
                (cost := _number(row.get(f"{actor}_execution_cost_pct"))) is None
                or cost < 0
            )
            for actor in ("control", "candidate")
        ):
            exclusions["exposure_execution_cost_missing_or_invalid"] += 1
        else:
            comparisons.append(row)

    identity = (
        candidate_version,
        candidate_prompt_sha256,
        candidate_contract_sha256,
        stage,
        f"{venue}:{session}",
    )
    count_fields: dict[str, int] = {}
    for source_key, output_key in (
        ("schema_rejected_count", "schema_rejected_count"),
        ("provider_failed_count", "provider_failed_count"),
        ("candidate_provider_none_count", "provider_none_count"),
    ):
        count = _native_nonnegative_int(report.get(source_key))
        if count is None:
            errors.append(f"{source_key}_invalid")
            count = 0
        count_fields[output_key] = count

    metadata = {
        "path": str(path),
        "source_date": source_date,
        "candidate_prompt_version": candidate_version,
        "candidate_prompt_sha256": candidate_prompt_sha256,
        "candidate_contract_sha256": candidate_contract_sha256,
        "stage": stage,
        "effective_venue": venue,
        "session_bucket": session,
        "paired_comparable_count": len(comparisons),
        "raw_paired_comparable_count": len(raw_comparisons),
        "row_exclusion_count": sum(exclusions.values()),
        "row_exclusion_reason_counts": dict(exclusions),
        **count_fields,
        "artifact_content_sha256": report.get("artifact_content_sha256"),
        "artifact_content_sha256_verified": hash_verified,
        "candidate_selection_eligible": hash_verified,
        "warnings": warnings,
        "errors": errors,
        "generated_at": report.get("generated_at"),
    }
    return (None if errors else identity), comparisons, metadata


def _transition_rows(
    paired_dir: Path,
    *,
    target_date: str,
) -> tuple[
    dict[tuple[str, str, str, str, str], dict[str, dict[str, Any]]],
    list[dict[str, Any]],
    dict[str, Any],
    Counter[tuple[str, str, str, str, str]],
]:
    rows_by_cohort: dict[tuple[str, str, str, str, str], dict[str, dict[str, Any]]] = (
        defaultdict(dict)
    )
    source_reports: list[dict[str, Any]] = []
    rejected_reports: list[dict[str, Any]] = []
    duplicate_identical_count = 0
    duplicate_conflict_count = 0
    current_duplicate_conflict_count = 0
    legacy_hashless_diagnostic_row_count = 0
    cohort_conflicts: Counter[tuple[str, str, str, str, str]] = Counter()
    conflicted_traces: dict[tuple[str, str, str, str, str], set[str]] = defaultdict(set)
    discovered_count = 0
    for path in sorted(paired_dir.glob("ai_prompt_detailed_paired_replay_*.json")):
        report = _load_json(path)
        source_date = _report_date(path, report)
        if source_date and (
            source_date < CLEAN_BASELINE_DATE or source_date > target_date
        ):
            continue
        discovered_count += 1
        identity, comparisons, metadata = _candidate_source_contract(
            path, report, target_date=target_date
        )
        if identity is None:
            rejected_reports.append(metadata)
            continue
        source_reports.append(metadata)
        if metadata.get("candidate_selection_eligible") is not True:
            legacy_hashless_diagnostic_row_count += len(comparisons)
            continue
        for row in comparisons:
            trace_id = str(row["decision_trace_id"])
            if trace_id in conflicted_traces[identity]:
                continue
            enriched = dict(row)
            enriched.update(
                {
                    "source_date": metadata["source_date"],
                    "candidate_prompt_version": identity[0],
                    "candidate_prompt_sha256": identity[1],
                    "candidate_contract_sha256": identity[2],
                    "stage": identity[3],
                    "effective_venue": metadata["effective_venue"],
                    "session_bucket": metadata["session_bucket"],
                }
            )
            existing = rows_by_cohort[identity].get(trace_id)
            if existing is None:
                rows_by_cohort[identity][trace_id] = enriched
                continue
            comparable_existing = {
                key: value
                for key, value in existing.items()
                if key not in {"source_date"}
            }
            comparable_new = {
                key: value
                for key, value in enriched.items()
                if key not in {"source_date"}
            }
            if _canonical_sha256(comparable_existing) == _canonical_sha256(
                comparable_new
            ):
                duplicate_identical_count += 1
                continue
            rows_by_cohort[identity].pop(trace_id, None)
            conflicted_traces[identity].add(trace_id)
            cohort_conflicts[identity] += 1
            duplicate_conflict_count += 1
            if target_date in {
                str(existing.get("source_date") or ""),
                str(enriched.get("source_date") or ""),
            }:
                current_duplicate_conflict_count += 1
    current_reports = [
        row for row in source_reports if row.get("source_date") == target_date
    ]
    current_rejected = [
        row for row in rejected_reports if row.get("source_date") == target_date
    ]
    rejection_reasons = Counter(
        reason for row in rejected_reports for reason in row.get("errors") or []
    )
    source_contract_summary = {
        "discovered_report_count": discovered_count,
        "accepted_report_count": len(source_reports),
        "rejected_report_count": len(rejected_reports),
        "accepted_hash_verified_report_count": sum(
            row.get("artifact_content_sha256_verified") is True
            for row in source_reports
        ),
        "accepted_legacy_hashless_report_count": sum(
            row.get("artifact_content_sha256_verified") is not True
            for row in source_reports
        ),
        "legacy_hashless_diagnostic_row_count": (legacy_hashless_diagnostic_row_count),
        "accepted_row_count": sum(len(rows) for rows in rows_by_cohort.values()),
        "row_exclusion_count": sum(
            int(row.get("row_exclusion_count") or 0) for row in source_reports
        ),
        "identical_duplicate_trace_count": duplicate_identical_count,
        "conflicting_duplicate_trace_count": duplicate_conflict_count,
        "conflicting_duplicate_traces_excluded": True,
        "rejection_reason_counts": dict(rejection_reasons),
        "current_date_accepted_report_count": len(current_reports),
        "current_date_rejected_report_count": len(current_rejected),
        "current_date_row_exclusion_count": sum(
            int(row.get("row_exclusion_count") or 0) for row in current_reports
        ),
        "current_date_conflicting_duplicate_trace_count": (
            current_duplicate_conflict_count
        ),
        "current_date_accepted_row_count": sum(
            row.get("source_date") == target_date
            for rows in rows_by_cohort.values()
            for row in rows.values()
        ),
        "cross_cohort_aggregation_forbidden": True,
        "invalid_sources_excluded_before_calibration": True,
        "candidate_selection_requires_verified_source_hash": True,
        "rejected_reports": rejected_reports,
    }
    return rows_by_cohort, source_reports, source_contract_summary, cohort_conflicts


def _transition_summary(
    candidate_identity: tuple[str, str, str, str, str],
    rows: Iterable[dict[str, Any]],
    source_reports: list[dict[str, Any]],
    *,
    conflicting_duplicate_trace_count: int = 0,
) -> dict[str, Any]:
    (
        candidate_version,
        candidate_prompt_sha256,
        candidate_contract_sha256,
        stage,
        route_scope,
    ) = candidate_identity
    effective_venue, session_bucket = route_scope.split(":", 1)
    values = list(rows)
    raw_value_pairs: list[tuple[float, float]] = []
    for row in values:
        control_value = _number(row.get("control_decision_value_pct"))
        candidate_raw_value = _number(row.get("candidate_decision_value_pct"))
        if (
            candidate_raw_value is None
            and row.get("candidate_execution_cost_contract_applied") is not True
        ):
            candidate_raw_value = _number(
                row.get("candidate_primary_decision_value_pct")
            )
        if control_value is not None and candidate_raw_value is not None:
            raw_value_pairs.append((control_value, candidate_raw_value))
    control_raw_values = [control for control, _ in raw_value_pairs]
    candidate_raw_values = [candidate for _, candidate in raw_value_pairs]
    candidate_primary_values = [
        value
        for row in values
        if (value := _number(row.get("candidate_primary_decision_value_pct")))
        is not None
    ]
    delta_values = [
        value for row in values if (value := _number(row.get("delta_pct"))) is not None
    ]
    exposure_rows = [
        row
        for row in values
        if str(row.get("candidate_action") or "").upper() in EXPOSURE_ACTIONS
    ]
    candidate_exposure_values = [
        value
        for row in exposure_rows
        if (value := _number(row.get("candidate_primary_decision_value_pct")))
        is not None
    ]
    candidate_probe_losses = []
    candidate_probe_risk_missing_count = 0
    for row in exposure_rows:
        probe_loss = _number(row.get("candidate_probe_worst_loss_pct"))
        if probe_loss is None:
            probe_loss = _number(row.get("probe_worst_loss_pct"))
        if probe_loss is None:
            outcome_mae = _number(row.get("outcome_mae_pct"))
            if outcome_mae is not None:
                probe_loss = min(0.0, outcome_mae)
        if probe_loss is None:
            candidate_probe_risk_missing_count += 1
            continue
        candidate_probe_losses.append(probe_loss)
    control_exposure_rows = [
        row
        for row in values
        if str(row.get("control_action") or "").upper() in EXPOSURE_ACTIONS
    ]
    control_severe_tail = sum(
        row.get("control_probe_severe_tail_exposure") is True
        or (
            (probe_loss := _probe_worst_loss(row, "control")) is not None
            and probe_loss < SEVERE_TAIL_ADVERSE_PCT
        )
        for row in control_exposure_rows
    )
    candidate_severe_tail = sum(
        row.get("candidate_probe_severe_tail_exposure") is True
        or (
            (probe_loss := _probe_worst_loss(row, "candidate")) is not None
            and probe_loss < SEVERE_TAIL_ADVERSE_PCT
        )
        for row in exposure_rows
    )
    control_recovery_capture = sum(
        row.get("control_drawdown_recovery_captured") is True
        or (row.get("profit_opportunity_sequence") == "drawdown_then_profit_recovery")
        for row in control_exposure_rows
    )
    candidate_recovery_capture = sum(
        row.get("candidate_drawdown_recovery_captured") is True
        or (row.get("profit_opportunity_sequence") == "drawdown_then_profit_recovery")
        for row in exposure_rows
    )
    control_adverse = sum(
        str(row.get("first_hit") or "") == "adverse"
        and str(row.get("control_action") or "").upper() in EXPOSURE_ACTIONS
        for row in values
    )
    candidate_adverse = sum(
        str(row.get("first_hit") or "") == "adverse"
        and str(row.get("candidate_action") or "").upper() in EXPOSURE_ACTIONS
        for row in values
    )
    transitions = Counter(
        f"{str(row.get('control_action') or 'UNKNOWN').upper()}->"
        f"{str(row.get('candidate_action') or 'UNKNOWN').upper()}"
        for row in values
    )
    identity_reports = [
        row
        for row in source_reports
        if row.get("candidate_prompt_version") == candidate_version
        and row.get("candidate_prompt_sha256") == candidate_prompt_sha256
        and row.get("candidate_contract_sha256") == candidate_contract_sha256
        and row.get("stage") == stage
        and row.get("effective_venue") == effective_venue
        and row.get("session_bucket") == session_bucket
    ]
    reports = [
        row
        for row in identity_reports
        if row.get("artifact_content_sha256_verified") is True
    ]
    schema_rejected_count = sum(row["schema_rejected_count"] for row in reports)
    schema_evaluated_count = len(values) + schema_rejected_count
    schema_rejection_rate_pct = (
        (schema_rejected_count / schema_evaluated_count) * 100.0
        if schema_evaluated_count
        else 0.0
    )
    provider_failed_count = sum(row["provider_failed_count"] for row in reports)
    provider_none_count = sum(row["provider_none_count"] for row in reports)
    primary_ev_delta = fmean(delta_values) if delta_values else None
    source_quality_ev_delta = (
        fmean(candidate - control for control, candidate in raw_value_pairs)
        if raw_value_pairs
        else None
    )
    adverse_not_increased = candidate_adverse <= control_adverse
    candidate_probe_loss_budget_breach_count = sum(
        loss < -MAXIMUM_BOUNDED_PROBE_LOSS_PCT for loss in candidate_probe_losses
    )
    candidate_probe_loss_budget_breach_rate_pct = (
        candidate_probe_loss_budget_breach_count / len(candidate_probe_losses) * 100.0
        if candidate_probe_losses
        else None
    )
    candidate_catastrophic_loss_count = sum(
        loss < CATASTROPHIC_LOSS_PCT for loss in candidate_probe_losses
    )
    candidate_severe_tail_rate_pct = (
        candidate_severe_tail / len(exposure_rows) * 100.0 if exposure_rows else None
    )
    control_severe_tail_rate_pct = (
        control_severe_tail / len(control_exposure_rows) * 100.0
        if control_exposure_rows
        else None
    )
    probe_loss_budget_pass = (
        bool(exposure_rows)
        and candidate_probe_risk_missing_count == 0
        and len(candidate_probe_losses) == len(exposure_rows)
        and candidate_probe_loss_budget_breach_rate_pct is not None
        and candidate_probe_loss_budget_breach_rate_pct
        <= MAXIMUM_LOSS_BUDGET_BREACH_RATE_PCT
        and candidate_severe_tail_rate_pct is not None
        and candidate_severe_tail_rate_pct <= MAXIMUM_SEVERE_TAIL_RATE_PCT
        and candidate_catastrophic_loss_count == 0
    )
    severe_tail_rate_not_increased = (
        candidate_severe_tail_rate_pct <= control_severe_tail_rate_pct
        if candidate_severe_tail_rate_pct is not None
        and control_severe_tail_rate_pct is not None
        else None
    )
    recovery_opportunity_count = sum(
        row.get("profit_opportunity_sequence") == "drawdown_then_profit_recovery"
        or row.get("drawdown_recovery_observed") is True
        for row in values
    )
    control_recovery_capture_rate_pct = (
        control_recovery_capture / recovery_opportunity_count * 100.0
        if recovery_opportunity_count
        else None
    )
    candidate_recovery_capture_rate_pct = (
        candidate_recovery_capture / recovery_opportunity_count * 100.0
        if recovery_opportunity_count
        else None
    )
    recovery_capture_rate_not_decreased = (
        candidate_recovery_capture_rate_pct >= control_recovery_capture_rate_pct
        if candidate_recovery_capture_rate_pct is not None
        and control_recovery_capture_rate_pct is not None
        else None
    )
    # Conflicts have already been removed by exact trace. They are not a
    # permanent veto on the remaining independently verified cohort.
    source_integrity_complete = bool(reports and values)
    unique_symbol_count = len(
        {str(row.get("stock_code") or "") for row in values if row.get("stock_code")}
    )
    source_dates = sorted(
        {str(row.get("source_date")) for row in values if row.get("source_date")}
    )
    candidate_ev = fmean(candidate_primary_values) if candidate_primary_values else None
    candidate_exposure_ev = (
        fmean(candidate_exposure_values) if candidate_exposure_values else None
    )
    candidate_exposure_unique_symbol_count = len(
        {
            str(row.get("stock_code") or "")
            for row in exposure_rows
            if row.get("stock_code")
        }
    )
    probe_cost_contract_complete = bool(exposure_rows) and all(
        row.get("candidate_execution_cost_contract_applied") is True
        and (cost := _number(row.get("candidate_execution_cost_pct"))) is not None
        and cost >= 0
        for row in exposure_rows
    )
    candidate_probe_cost_adjusted_ev = (
        candidate_exposure_ev if probe_cost_contract_complete else None
    )
    candidate_exposure_rate_pct = (
        (len(exposure_rows) / len(values)) * 100.0 if values else 0.0
    )
    false_drop_count = sum(
        "false_drop"
        in {str(error) for error in row.get("candidate_error_taxonomy") or []}
        for row in values
    )
    false_drop_rate_pct = (false_drop_count / len(values)) * 100.0 if values else 0.0
    # Diagnostic only: do not promote a spread/age execution proxy to full net
    # economics or silently change the existing false-drop review ceiling.
    small_opportunity_rows = [
        row
        for row in values
        if isinstance(row.get("entry_small_profit_opportunity"), dict)
        and row["entry_small_profit_opportunity"].get("schema")
        == "entry_small_profit_opportunity_v1"
        and row["entry_small_profit_opportunity"].get(
            "positive_target_first_after_execution_proxy"
        )
        is True
    ]
    small_opportunity_diagnostic = {
        "opportunity_count": len(small_opportunity_rows),
        "control_missed_count": sum(
            row.get("control_action") in {"WAIT", "DROP"}
            for row in small_opportunity_rows
        ),
        "candidate_missed_count": sum(
            row.get("candidate_action") in {"WAIT", "DROP"}
            for row in small_opportunity_rows
        ),
        "fee_tax_net_profit_verified": False,
        "decision_authority": "diagnostic_only_no_promotion_gate",
    }
    review_gate_checks = {
        "source_integrity_complete": source_integrity_complete,
        "paired_economic_values_complete": bool(values)
        and len(candidate_primary_values) == len(values)
        and len(delta_values) == len(values),
        "exact_trace_floor": len(values)
        >= PROMPT_REVIEW_GATE["minimum_exact_trace_count"],
        "unique_symbol_floor": unique_symbol_count
        >= PROMPT_REVIEW_GATE["minimum_unique_symbol_count"],
        "independent_source_date_floor": len(source_dates)
        >= PROMPT_REVIEW_GATE["minimum_independent_source_date_count"],
        "candidate_exposure_floor": len(exposure_rows)
        >= PROMPT_REVIEW_GATE["minimum_candidate_exposure_count"],
        "false_drop_rate_ceiling": false_drop_rate_pct
        <= PROMPT_REVIEW_GATE["maximum_false_drop_rate_pct"],
        "positive_candidate_ev": candidate_ev is not None and candidate_ev > 0,
        "positive_candidate_exposure_ev": candidate_exposure_ev is not None
        and candidate_exposure_ev > 0,
        "positive_probe_cost_adjusted_ev": (
            candidate_probe_cost_adjusted_ev is not None
            and candidate_probe_cost_adjusted_ev > 0
        ),
        "positive_ev_delta": primary_ev_delta is not None and primary_ev_delta > 0,
        "bounded_probe_risk_budget": probe_loss_budget_pass,
        "schema_rejection_rate_ceiling": schema_rejection_rate_pct
        <= PROMPT_REVIEW_GATE["maximum_schema_rejection_rate_pct"],
    }
    review_ready = bool(values and all(review_gate_checks.values()))
    review_gate_blockers = [
        name for name, passed in review_gate_checks.items() if not passed
    ]
    diagnostic_checks = {
        "provider_transport_clean": provider_failed_count == 0
        and provider_none_count == 0,
        "candidate_exposure_rate_at_least_2pct": candidate_exposure_rate_pct
        >= PROMPT_REVIEW_GATE["diagnostic_minimum_candidate_exposure_rate_pct"],
        "severe_tail_rate_not_increased": severe_tail_rate_not_increased,
        "drawdown_recovery_capture_rate_not_decreased": (
            recovery_capture_rate_not_decreased
        ),
    }
    thin_positive_review = bool(
        source_integrity_complete
        and exposure_rows
        and candidate_probe_cost_adjusted_ev is not None
        and candidate_probe_cost_adjusted_ev > 0
        and primary_ev_delta is not None
        and primary_ev_delta > 0
        and probe_loss_budget_pass
        and not review_ready
        and all(
            passed
            for name, passed in review_gate_checks.items()
            if name
            not in {
                "exact_trace_floor",
                "unique_symbol_floor",
                "independent_source_date_floor",
                "candidate_exposure_floor",
            }
        )
    )
    r3_handoff_evidence_checks = {
        "review_ready": review_ready,
        "candidate_exposure_floor": len(exposure_rows)
        >= R3_HANDOFF_EVIDENCE_FLOOR["minimum_candidate_exposure_count"],
        "candidate_exposure_unique_symbol_floor": candidate_exposure_unique_symbol_count
        >= R3_HANDOFF_EVIDENCE_FLOOR["minimum_candidate_exposure_unique_symbol_count"],
    }
    return {
        "candidate_prompt_version": candidate_version,
        "candidate_prompt_sha256": candidate_prompt_sha256,
        "candidate_contract_sha256": candidate_contract_sha256,
        "stage": stage,
        "effective_venue": effective_venue,
        "session_bucket": session_bucket,
        "cohort_isolated": True,
        "exact_trace_count": len(values),
        "unique_symbol_count": unique_symbol_count,
        "source_date_count": len(source_dates),
        "source_dates": source_dates,
        "candidate_exposure_count": len(exposure_rows),
        "candidate_exposure_unique_symbol_count": (
            candidate_exposure_unique_symbol_count
        ),
        "candidate_exposure_rate_pct": candidate_exposure_rate_pct,
        "candidate_exposure_ev_pct": candidate_exposure_ev,
        "false_drop_count": false_drop_count,
        "false_drop_rate_pct": false_drop_rate_pct,
        "small_profit_opportunity_diagnostic": small_opportunity_diagnostic,
        "control_source_quality_adjusted_ev_pct": (
            fmean(control_raw_values) if control_raw_values else None
        ),
        "candidate_source_quality_adjusted_ev_pct": (
            fmean(candidate_raw_values) if candidate_raw_values else None
        ),
        "candidate_primary_decision_ev_pct": (
            fmean(candidate_primary_values) if candidate_primary_values else None
        ),
        "source_quality_adjusted_ev_delta_pct": source_quality_ev_delta,
        "candidate_primary_decision_ev_delta_pct": primary_ev_delta,
        "candidate_primary_decision_metric": (
            "candidate_execution_cost_adjusted_ev_pct"
            if any(
                row.get("candidate_execution_cost_contract_applied") is True
                for row in values
            )
            else "source_quality_adjusted_ev_pct"
        ),
        "control_adverse_first_exposure_count": control_adverse,
        "candidate_adverse_first_exposure_count": candidate_adverse,
        "probe_risk_gate_version": PROBE_RISK_GATE_VERSION,
        "candidate_probe_cost_adjusted_ev_pct": candidate_probe_cost_adjusted_ev,
        "probe_cost_contract_complete": probe_cost_contract_complete,
        "candidate_probe_loss_budget_breach_count": (
            candidate_probe_loss_budget_breach_count
        ),
        "candidate_probe_loss_budget_breach_rate_pct": (
            candidate_probe_loss_budget_breach_rate_pct
        ),
        "candidate_probe_catastrophic_loss_count": candidate_catastrophic_loss_count,
        "candidate_probe_risk_missing_count": candidate_probe_risk_missing_count,
        "control_probe_severe_tail_exposure_count": control_severe_tail,
        "candidate_probe_severe_tail_exposure_count": candidate_severe_tail,
        "control_probe_severe_tail_rate_pct": control_severe_tail_rate_pct,
        "candidate_probe_severe_tail_rate_pct": candidate_severe_tail_rate_pct,
        "control_drawdown_recovery_capture_count": control_recovery_capture,
        "candidate_drawdown_recovery_capture_count": candidate_recovery_capture,
        "drawdown_recovery_opportunity_count": recovery_opportunity_count,
        "control_drawdown_recovery_capture_rate_pct": (
            control_recovery_capture_rate_pct
        ),
        "candidate_drawdown_recovery_capture_rate_pct": (
            candidate_recovery_capture_rate_pct
        ),
        "candidate_error_taxonomy_counts": dict(
            Counter(
                error
                for row in values
                for error in row.get("candidate_error_taxonomy") or []
            )
        ),
        "control_action_counts": dict(
            Counter(str(row.get("control_action") or "UNKNOWN") for row in values)
        ),
        "candidate_action_counts": dict(
            Counter(str(row.get("candidate_action") or "UNKNOWN") for row in values)
        ),
        "action_transition_counts": dict(transitions),
        "schema_rejected_count": schema_rejected_count,
        "schema_evaluated_count": schema_evaluated_count,
        "schema_rejection_rate_pct": schema_rejection_rate_pct,
        "provider_failed_count": provider_failed_count,
        "provider_none_count": provider_none_count,
        "adverse_first_exposure_not_increased": adverse_not_increased,
        "adverse_first_role": "diagnostic_not_absolute_quality_veto",
        "source_integrity_complete": source_integrity_complete,
        "source_report_count": len(identity_reports),
        "verified_source_report_count": len(reports),
        "legacy_hashless_source_report_count": sum(
            row.get("artifact_content_sha256_verified") is not True
            for row in identity_reports
        ),
        "conflicting_duplicate_trace_count": conflicting_duplicate_trace_count,
        "review_classification": (
            "review_ready"
            if review_ready
            else (
                "thin_positive_review"
                if thin_positive_review
                else "learning_only_or_rejected"
            )
        ),
        "review_ready_for_prompt_candidate": review_ready,
        "prompt_review_gate": {
            "policy": PROMPT_REVIEW_GATE,
            "checks": review_gate_checks,
            "blockers": review_gate_blockers,
            "alignment": ("bounded_opportunity_exploration_with_downstream_safety"),
            "required_runtime_conversion_guards": DOWNSTREAM_RUNTIME_GUARDS,
        },
        "diagnostic_checks_not_review_veto": diagnostic_checks,
        "r3_handoff_evidence": {
            "policy": R3_HANDOFF_EVIDENCE_FLOOR,
            "checks": r3_handoff_evidence_checks,
            "pass": all(r3_handoff_evidence_checks.values()),
            "runtime_apply_authority": False,
            "separate_exact_r3_candidate_required": True,
            "legacy_r3_runtime_path_available": False,
            "interpretation": "research_floor_only_not_legacy_family_activation",
        },
        "runtime_review_route": runtime_review_route(
            candidate_version, stage, effective_venue, session_bucket
        ),
        "learning_update_floor": {
            "required_exact_trace_rows": 1,
            "observed_exact_trace_rows": len(values),
            "pass": bool(values),
            "role": "cumulative_learning_update_only",
        },
        "runtime_apply_authority": False,
    }


def runtime_review_route(
    version: str, stage: str, venue: str, session: str
) -> dict[str, Any]:
    registered = (
        stage == "entry"
        and venue == "KRX"
        and session == "KRX_REGULAR"
        and version
        in {
            "decision_quality_v2_14_setup_risk_adjudicator",
            "decision_quality_v2_15_bounded_recovery",
        }
    )
    return {
        "owner": (
            "entry_setup_live_policy" if registered else "main_ai_prompt_optimizer"
        ),
        "status": (
            "separate_registered_owner_guards_required"
            if registered
            else "source_only_no_registered_runtime_route"
        ),
        "legacy_main_ai_quality_family_available": False,
        "next_action": (
            "use_existing_isolated_detailed_batch_candidate_and_preopen_owner_guards"
            if registered
            else "offline_research_or_explicit_runtime_design_workorder"
        ),
        "runtime_apply_authority": False,
        "calibration_can_bypass_owner_guards": False,
    }


def _fields(event: dict[str, Any]) -> dict[str, Any]:
    value = event.get("fields")
    return value if isinstance(value, dict) else {}


def build_ofi_smoothing_audit(
    pipeline_path: Path,
) -> dict[str, Any]:
    if not pipeline_path.exists():
        return {
            "status": "source_unavailable",
            "source_path": str(pipeline_path),
            "event_count": 0,
            "runtime_action_change_count": 0,
            "exact_trace_linked_count": 0,
        }
    events: list[dict[str, Any]] = []
    for event in iter_jsonl(pipeline_path):
        stage = str(event.get("stage") or "")
        if stage in OFI_STAGES:
            events.append(event)
    action_counter: Counter[str] = Counter()
    trace_linked = 0
    snapshot_linked = 0
    explicit_contract = 0
    runtime_action_changes = 0
    usable_count = 0
    regime_counter: Counter[str] = Counter()
    for event in events:
        stage = str(event.get("stage") or "")
        fields = _fields(event)
        smoothing_action = str(
            fields.get("smoothing_action")
            or ("DEMOTE_SKIP" if stage == "entry_ai_price_ofi_skip_demoted" else "")
            or "UNKNOWN"
        )
        action_counter[f"{stage}:{smoothing_action}"] += 1
        raw_action = str(
            fields.get("raw_flow_action") or fields.get("raw_action") or ""
        )
        final_action = str(
            fields.get("final_flow_action") or fields.get("final_action") or ""
        )
        if raw_action and final_action and raw_action != final_action:
            runtime_action_changes += 1
        if fields.get("ai_decision_trace_id") not in (None, "", "-"):
            trace_linked += 1
        if fields.get("ai_input_snapshot_id") not in (None, "", "-"):
            snapshot_linked += 1
        if fields.get("metric_role") and fields.get("decision_authority"):
            explicit_contract += 1
        usable = fields.get("holding_flow_ofi_usable")
        if usable is None:
            usable = fields.get("entry_ai_price_ofi_usable")
        if usable is True or str(usable).lower() == "true":
            usable_count += 1
        regime = str(
            fields.get("holding_flow_ofi_regime")
            or fields.get("entry_ai_price_ofi_regime")
            or ""
        )
        if regime:
            regime_counter[regime] += 1
    defects: list[str] = []
    if events and trace_linked < len(events):
        defects.append("exact_decision_trace_attribution_incomplete")
    if events and snapshot_linked < len(events):
        defects.append("exact_snapshot_attribution_incomplete")
    if events and explicit_contract < len(events):
        defects.append("runtime_authority_contract_incomplete")
    if events and usable_count == 0:
        defects.append("ofi_usability_provenance_missing")
    return {
        "status": "pass" if not defects else "warning",
        "source_path": str(pipeline_path),
        "event_count": len(events),
        "action_counts": dict(action_counter),
        "runtime_action_change_count": runtime_action_changes,
        "exact_trace_linked_count": trace_linked,
        "exact_snapshot_linked_count": snapshot_linked,
        "explicit_contract_count": explicit_contract,
        "usable_provenance_count": usable_count,
        "regime_counts": dict(regime_counter),
        "defects": defects,
        "finding": (
            "OFI is an action postprocessor, not a replacement for exact-trace "
            "outcome calibration."
        ),
    }


def _outcome_index(
    rows_by_cohort: dict[tuple[str, str, str, str, str], dict[str, dict[str, Any]]],
) -> tuple[dict[str, dict[str, Any]], int]:
    outcomes: dict[str, dict[str, Any]] = {}
    conflicted_trace_ids: set[str] = set()
    conflict_count = 0
    for rows in rows_by_cohort.values():
        for trace_id, row in rows.items():
            if trace_id in conflicted_trace_ids:
                continue
            candidate = {
                "outcome_return_pct": _number(row.get("outcome_return_pct")),
                "outcome_mfe_pct": _number(row.get("outcome_mfe_pct")),
                "outcome_mae_pct": _number(row.get("outcome_mae_pct")),
                "first_hit": str(row.get("first_hit") or ""),
            }
            existing = outcomes.get(trace_id)
            if existing is None:
                outcomes[trace_id] = candidate
            elif _canonical_sha256(existing) != _canonical_sha256(candidate):
                outcomes.pop(trace_id, None)
                conflicted_trace_ids.add(trace_id)
                conflict_count += 1
    return outcomes, conflict_count


def _decision_value(action: str, outcome_return_pct: float) -> float | None:
    normalized = str(action or "").upper()
    if normalized in EXPOSURE_ACTIONS:
        return outcome_return_pct
    if normalized in NO_EXPOSURE_ACTIONS:
        return 0.0
    return None


def _attach_ofi_outcome(
    row: dict[str, Any],
    outcome: dict[str, Any] | None,
) -> None:
    if not outcome or outcome.get("outcome_return_pct") is None:
        row["outcome_status"] = "pending"
        return
    outcome_return = float(outcome["outcome_return_pct"])
    raw_value = _decision_value(str(row.get("raw_action") or ""), outcome_return)
    final_value = _decision_value(str(row.get("final_action") or ""), outcome_return)
    row.update(outcome)
    row["raw_action_decision_value_pct"] = raw_value
    row["final_action_decision_value_pct"] = final_value
    if raw_value is None or final_value is None:
        row["outcome_status"] = "mature_not_comparable"
        row["outcome_not_comparable_reason"] = (
            "action_value_requires_exact_quantity_or_cashflow_contract"
        )
        row["ofi_action_adjustment_delta_pct"] = None
        return
    row["outcome_status"] = "mature"
    row["outcome_not_comparable_reason"] = None
    row["ofi_action_adjustment_delta_pct"] = final_value - raw_value


def _is_effective_ofi_transition(row: dict[str, Any]) -> bool:
    raw_action = str(row.get("raw_action") or "").strip().upper()
    final_action = str(row.get("final_action") or "").strip().upper()
    return bool(raw_action and final_action and raw_action != final_action)


def _current_ofi_outcome_rows(
    pipeline_path: Path,
    *,
    outcome_by_trace: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], Counter[str]]:
    rows: dict[str, dict[str, Any]] = {}
    conflicted_ledger_keys: set[str] = set()
    exclusions: Counter[str] = Counter()
    if not pipeline_path.exists():
        return [], exclusions
    for event in iter_jsonl(pipeline_path):
        stage = str(event.get("stage") or "")
        if stage not in OFI_STAGES:
            continue
        fields = _fields(event)
        trace_id = str(fields.get("ai_decision_trace_id") or "").strip()
        snapshot_id = str(fields.get("ai_input_snapshot_id") or "").strip()
        if trace_id in {"", "-"}:
            exclusions["exact_decision_trace_missing"] += 1
            continue
        if snapshot_id in {"", "-"}:
            exclusions["exact_snapshot_missing"] += 1
            continue
        raw_action = str(
            fields.get("raw_flow_action") or fields.get("raw_action") or ""
        ).upper()
        final_action = str(
            fields.get("final_flow_action") or fields.get("final_action") or ""
        ).upper()
        if not raw_action or not final_action:
            exclusions["action_transition_missing"] += 1
            continue
        outcome = outcome_by_trace.get(trace_id)
        ledger_key = f"{stage}:{trace_id}"
        if ledger_key in conflicted_ledger_keys:
            continue
        row = {
            "ledger_key": ledger_key,
            "decision_trace_id": trace_id,
            "ai_input_snapshot_id": snapshot_id,
            "stage": stage,
            "stock_code": str(event.get("stock_code") or ""),
            "emitted_at": event.get("emitted_at"),
            "raw_action": raw_action,
            "final_action": final_action,
            "smoothing_action": str(fields.get("smoothing_action") or ""),
            "ofi_regime": str(
                fields.get("holding_flow_ofi_regime")
                or fields.get("entry_ai_price_ofi_regime")
                or ""
            ),
            "ofi_reason": str(
                fields.get("holding_flow_ofi_reason")
                or fields.get("entry_ai_price_ofi_reason")
                or ""
            ),
            "ofi_snapshot_age_ms": _number(
                fields.get("holding_flow_ofi_snapshot_age_ms")
                if fields.get("holding_flow_ofi_snapshot_age_ms") is not None
                else fields.get("entry_ai_price_ofi_snapshot_age_ms")
            ),
            "outcome_status": "mature" if outcome else "pending",
            **(outcome or {}),
        }
        _attach_ofi_outcome(row, outcome)
        existing = rows.get(ledger_key)
        if existing is None:
            rows[ledger_key] = row
        elif _canonical_sha256(existing) == _canonical_sha256(row):
            exclusions["identical_duplicate_ledger_row"] += 1
        else:
            rows.pop(ledger_key, None)
            conflicted_ledger_keys.add(ledger_key)
            exclusions["conflicting_duplicate_ledger_row"] += 1
    return list(rows.values()), exclusions


def _prior_ofi_outcome_rows(
    report_root: Path,
    *,
    target_date: str,
) -> tuple[list[dict[str, Any]], Counter[str]]:
    rows: dict[str, dict[str, Any]] = {}
    exclusions: Counter[str] = Counter()
    conflicted_keys: set[str] = set()
    directory = report_root / REPORT_SUBDIR
    for path in sorted(directory.glob("ai_decision_action_outcome_calibration_*.json")):
        report = _load_json(path)
        source_date = _report_date(path, report)
        if not source_date or source_date >= target_date:
            continue
        if report.get("schema") != SCHEMA:
            exclusions["legacy_or_invalid_prior_schema"] += 1
            continue
        if not _artifact_content_sha256_valid(report):
            exclusions["prior_artifact_content_sha256_invalid"] += 1
            continue
        if any(
            report.get(key) is not expected
            for key, expected in (
                ("runtime_effect", False),
                ("allowed_runtime_apply", False),
                ("actual_order_submitted", False),
                ("broker_order_forbidden", True),
            )
        ):
            exclusions["prior_authority_contract_invalid"] += 1
            continue
        ledger = report.get("ofi_action_outcome_calibration")
        if not isinstance(ledger, dict) or ledger.get("schema") != OFI_LEDGER_SCHEMA:
            exclusions["prior_ofi_ledger_invalid"] += 1
            continue
        for row in ledger.get("rows") or []:
            if not isinstance(row, dict) or not row.get("ledger_key"):
                exclusions["prior_ofi_row_invalid"] += 1
                continue
            ledger_key = str(row["ledger_key"])
            if ledger_key in conflicted_keys:
                continue
            candidate = dict(row)
            existing = rows.get(ledger_key)
            if existing is None:
                rows[ledger_key] = candidate
            elif _canonical_sha256(existing) == _canonical_sha256(candidate):
                exclusions["identical_prior_ofi_row"] += 1
            else:
                rows.pop(ledger_key, None)
                conflicted_keys.add(ledger_key)
                exclusions["conflicting_prior_ofi_row"] += 1
    return list(rows.values()), exclusions


def build_ofi_action_outcome_calibration(
    *,
    report_root: Path,
    target_date: str,
    pipeline_path: Path,
    outcome_by_trace: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    prior_outcome_rows, prior_exclusions = _prior_ofi_outcome_rows(
        report_root, target_date=target_date
    )
    prior_rows = {str(row.get("ledger_key")): row for row in prior_outcome_rows}
    current_rows, exclusions = _current_ofi_outcome_rows(
        pipeline_path,
        outcome_by_trace=outcome_by_trace,
    )
    for row in current_rows:
        ledger_key = str(row["ledger_key"])
        prior = prior_rows.get(ledger_key)
        if prior is not None:
            identity_fields = (
                "decision_trace_id",
                "ai_input_snapshot_id",
                "stage",
                "stock_code",
                "raw_action",
                "final_action",
                "smoothing_action",
            )
            if any(prior.get(field) != row.get(field) for field in identity_fields):
                prior_rows.pop(ledger_key, None)
                exclusions["prior_current_ledger_identity_conflict"] += 1
                continue
        prior_rows[ledger_key] = row
    rows = list(prior_rows.values())
    for row in rows:
        trace_id = str(row.get("decision_trace_id") or "")
        _attach_ofi_outcome(row, outcome_by_trace.get(trace_id))
    comparable_mature_rows = [
        row
        for row in rows
        if row.get("outcome_status") == "mature"
        and _number(row.get("ofi_action_adjustment_delta_pct")) is not None
    ]
    pending_rows = [row for row in rows if row.get("outcome_status") == "pending"]
    not_comparable_rows = [
        row for row in rows if row.get("outcome_status") == "mature_not_comparable"
    ]
    effective_transition_rows = [
        row for row in rows if _is_effective_ofi_transition(row)
    ]
    no_change_control_rows = [
        row for row in rows if not _is_effective_ofi_transition(row)
    ]
    mature_effective_rows = [
        row for row in comparable_mature_rows if _is_effective_ofi_transition(row)
    ]
    pending_effective_rows = [
        row for row in pending_rows if _is_effective_ofi_transition(row)
    ]
    not_comparable_effective_rows = [
        row for row in not_comparable_rows if _is_effective_ofi_transition(row)
    ]
    deltas = [
        float(row["ofi_action_adjustment_delta_pct"]) for row in mature_effective_rows
    ]
    return {
        "schema": OFI_LEDGER_SCHEMA,
        "status": (
            "cumulative_learning_updated"
            if mature_effective_rows
            else (
                "exact_trace_rows_waiting_for_mature_outcome"
                if pending_effective_rows
                else (
                    "mature_outcome_not_comparable_keep_collecting"
                    if not_comparable_effective_rows
                    else "sample_floor_keep_collecting"
                )
            )
        ),
        "exact_trace_row_count": len(rows),
        "effective_transition_row_count": len(effective_transition_rows),
        "no_change_control_row_count": len(no_change_control_rows),
        "mature_outcome_row_count": len(comparable_mature_rows),
        "mature_effective_transition_outcome_row_count": len(mature_effective_rows),
        "pending_outcome_row_count": len(pending_rows),
        "pending_effective_transition_outcome_row_count": len(pending_effective_rows),
        "mature_not_comparable_outcome_row_count": len(not_comparable_rows),
        "mature_not_comparable_effective_transition_outcome_row_count": len(
            not_comparable_effective_rows
        ),
        "mature_not_comparable_reason_counts": dict(
            Counter(
                str(row.get("outcome_not_comparable_reason") or "unknown")
                for row in not_comparable_rows
            )
        ),
        "raw_to_final_transition_counts": dict(
            Counter(
                f"{row.get('raw_action')}->{row.get('final_action')}"
                for row in mature_effective_rows
            )
        ),
        "effective_transition_lane_counts": dict(
            Counter(
                f"{row.get('stage')}:{row.get('raw_action')}->{row.get('final_action')}"
                for row in effective_transition_rows
            )
        ),
        "no_change_control_outcome_status_counts": dict(
            Counter(
                str(row.get("outcome_status") or "unknown")
                for row in no_change_control_rows
            )
        ),
        "smoothing_action_counts": dict(
            Counter(str(row.get("smoothing_action") or "UNKNOWN") for row in rows)
        ),
        "source_quality_adjusted_ev_delta_pct": (fmean(deltas) if deltas else None),
        "positive_adjustment_count": sum(value > 0 for value in deltas),
        "negative_adjustment_count": sum(value < 0 for value in deltas),
        "zero_adjustment_count": sum(value == 0 for value in deltas),
        "current_date_exclusion_counts": dict(exclusions),
        "prior_ledger_exclusion_counts": dict(prior_exclusions),
        "learning_update_floor": {
            "required_mature_exact_trace_rows": 1,
            "observed_mature_exact_trace_rows": len(mature_effective_rows),
            "required_mature_effective_transition_rows": 1,
            "observed_mature_effective_transition_rows": len(mature_effective_rows),
            "pass": bool(mature_effective_rows),
            "role": "effective_transition_cumulative_learning_update_only",
        },
        "runtime_authority_expansion_allowed": False,
        "rows": rows,
    }


def build_report(
    *,
    target_date: str,
    data_root: Path = Path("data"),
) -> dict[str, Any]:
    target_day = date.fromisoformat(target_date)
    if target_day < date.fromisoformat(CLEAN_BASELINE_DATE):
        raise ValueError("target_date_before_clean_baseline")
    report_root = data_root / "report"
    (
        rows_by_cohort,
        source_reports,
        source_contract_summary,
        cohort_conflicts,
    ) = _transition_rows(
        report_root / PAIRED_SUBDIR,
        target_date=target_date,
    )
    candidates = [
        _transition_summary(
            identity,
            rows.values(),
            source_reports,
            conflicting_duplicate_trace_count=cohort_conflicts[identity],
        )
        for identity, rows in sorted(rows_by_cohort.items())
        if rows or cohort_conflicts[identity]
    ]
    review_ready = [
        row for row in candidates if row["review_ready_for_prompt_candidate"]
    ]
    thin_positive = [
        row
        for row in candidates
        if row.get("review_classification") == "thin_positive_review"
    ]
    selected = review_ready[0] if len(review_ready) == 1 else None
    candidate_identity_fields = (
        "candidate_prompt_version",
        "candidate_prompt_sha256",
        "candidate_contract_sha256",
        "stage",
        "effective_venue",
        "session_bucket",
    )

    def identity_summary(row: dict[str, Any]) -> dict[str, Any]:
        return {
            **{field: row.get(field) for field in candidate_identity_fields},
            "review_classification": row.get("review_classification"),
            "candidate_primary_decision_ev_delta_pct": row.get(
                "candidate_primary_decision_ev_delta_pct"
            ),
            "candidate_probe_cost_adjusted_ev_pct": row.get(
                "candidate_probe_cost_adjusted_ev_pct"
            ),
            "runtime_apply_authority": False,
        }

    pipeline_path = existing_or_gzip_path(
        data_root / "pipeline_events" / f"pipeline_events_{target_date}.jsonl"
    )
    outcome_by_trace, cross_cohort_outcome_conflict_count = _outcome_index(
        rows_by_cohort
    )
    source_contract_summary["cross_cohort_outcome_conflict_count"] = (
        cross_cohort_outcome_conflict_count
    )
    source_contract_summary["cross_cohort_outcome_conflicts_excluded"] = True
    ofi_action_outcome_calibration = build_ofi_action_outcome_calibration(
        report_root=report_root,
        target_date=target_date,
        pipeline_path=pipeline_path,
        outcome_by_trace=outcome_by_trace,
    )
    current_result_count = int(
        source_contract_summary.get("current_date_accepted_row_count") or 0
    )
    current_rejected_count = int(
        source_contract_summary.get("current_date_rejected_report_count") or 0
    )
    current_excluded_row_count = int(
        source_contract_summary.get("current_date_row_exclusion_count") or 0
    ) + int(
        source_contract_summary.get("current_date_conflicting_duplicate_trace_count")
        or 0
    )
    status = (
        "cumulative_action_outcome_calibration_updated"
        if current_result_count
        else (
            "current_input_excluded_cumulative_unchanged"
            if current_rejected_count or current_excluded_row_count
            else (
                "cumulative_unchanged_no_new_exact_results"
                if candidates
                else "sample_floor_keep_collecting"
            )
        )
    )
    optimizer_handoff_body = {
        "schema": ACTION_OUTCOME_OPTIMIZER_HANDOFF_SCHEMA,
        "target_date": target_date,
        "selected_review_candidate": (
            identity_summary(selected) if selected is not None else None
        ),
        "review_ready_candidates": [identity_summary(row) for row in review_ready],
        "thin_positive_review_candidates": [
            identity_summary(row) for row in thin_positive
        ],
        "source_contract_pass": (
            source_contract_summary.get("conflicting_duplicate_traces_excluded") is True
            and source_contract_summary.get("cross_cohort_outcome_conflicts_excluded")
            is True
        ),
        "decision_authority": "optimizer_source_only_advisory_no_runtime_selection",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    optimizer_handoff = {
        **optimizer_handoff_body,
        "handoff_content_sha256": _canonical_sha256(optimizer_handoff_body),
    }
    report = {
        "schema": SCHEMA,
        "policy_version": POLICY_VERSION,
        "target_date": target_date,
        "generated_at": datetime.now(KST).isoformat(),
        "status": status,
        "clean_tuning_baseline_date": CLEAN_BASELINE_DATE,
        "new_current_result_count": current_result_count,
        "candidate_count": len(candidates),
        "review_candidate_count": len(review_ready),
        "thin_positive_review_candidate_count": len(thin_positive),
        "prompt_review_gate_policy": PROMPT_REVIEW_GATE,
        "r3_handoff_evidence_floor": R3_HANDOFF_EVIDENCE_FLOOR,
        "required_runtime_conversion_guards": DOWNSTREAM_RUNTIME_GUARDS,
        "candidate_summaries": candidates,
        "selected_review_candidate": (identity_summary(selected) if selected else None),
        "review_ready_candidates": [identity_summary(row) for row in review_ready],
        "selection_status": (
            "review_candidate_available_no_runtime_authority"
            if selected
            else (
                "multiple_isolated_review_candidates_no_cross_cohort_selection"
                if review_ready
                else "no_candidate_passes_bounded_exploration_and_ev_gate"
            )
        ),
        "thin_positive_review_candidates": [
            identity_summary(row) for row in thin_positive
        ],
        "source_reports": source_reports,
        "source_contract_summary": source_contract_summary,
        "dedupe_key": (
            "candidate_prompt_version+candidate_prompt_sha256+"
            "candidate_contract_sha256+stage+effective_venue+session_bucket+"
            "decision_trace_id"
        ),
        "update_policy": (
            "append_hash_verified_cohort_isolated_exact_trace_daily_results_then_"
            "recompute_cumulative_action_outcome"
        ),
        "optimizer_handoff": optimizer_handoff,
        "ofi_smoothing_audit": build_ofi_smoothing_audit(pipeline_path),
        "ofi_action_outcome_calibration": ofi_action_outcome_calibration,
        **OFFLINE_CONTRACT,
    }
    return _with_artifact_content_sha256(report)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build cumulative exact-trace action/outcome calibration."
    )
    parser.add_argument("--target-date", required=True)
    parser.add_argument("--data-root", type=Path, default=Path("data"))
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args(argv)
    report = build_report(target_date=args.target_date, data_root=args.data_root)
    path = report_path(args.target_date, args.data_root / "report")
    if args.write:
        _atomic_write_json(path, report)
    if args.print_summary:
        print(
            json.dumps(
                {
                    "status": report["status"],
                    "candidate_count": report["candidate_count"],
                    "selected_review_candidate": report["selected_review_candidate"],
                    "ofi_smoothing_audit": report["ofi_smoothing_audit"],
                    "path": str(path),
                },
                ensure_ascii=False,
            )
        )
    else:
        print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
