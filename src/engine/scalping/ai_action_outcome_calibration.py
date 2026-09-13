"""Cumulative exact-trace action/outcome calibration and OFI attribution audit.

This producer replaces the legacy WATCHING numeric-score smoothing diagnostic.
It never changes a live score or action.  It accumulates mature paired replay
outcomes keyed by exact decision trace, then reports action transitions, EV,
error taxonomy, and OFI runtime postprocessor attribution coverage.
"""

from __future__ import annotations

import argparse
import gzip
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
from src.trading.order.tick_utils import get_tick_size
from src.engine.scalping.entry_setup_evidence import (
    MECHANISTIC_ENTRY_FLOW_OBSERVATION_SCHEMA,
    MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1,
    build_mechanistic_entry_flow_observation,
    mechanistic_entry_action_core,
    mechanistic_entry_policy_decision,
)

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
MECHANISTIC_REFINEMENT_SCHEMA = "mechanistic_entry_clean_baseline_refinement_v1"
MECHANISTIC_REFINEMENT_POLICY_VERSION = (
    "mechanistic_entry_common_feature_chronological_v1"
)
HIERARCHICAL_ENTRY_QUALITY_SCHEMA = "hierarchical_entry_quality_walk_forward_v1"
ENTRY_GROUP_OBSERVATION_SCHEMA = "entry_predecision_group_observation_v1"
ENTRY_QUALITY_PATH_SCHEMA = "entry_quality_path_v1"
MARKET_PATH_OPPORTUNITY_ANCHOR_SCHEMA = "market_path_opportunity_anchor_study_v1"
MECHANISTIC_FLOW_GROUP_STUDY_SCHEMA = "mechanistic_entry_flow_group_study_v1"
MECHANISTIC_FLOW_BOUNDARY_FREEZE_DATE = "2026-09-11"
ENTRY_QUALITY_LABELS = frozenset(
    {
        "CLEAN_FAST_PROFIT",
        "PROFITABLE_BUT_LATE",
        "PROFIT_AFTER_DEEP_ADVERSE",
        "PROFIT_AFTER_SIDEWAYS",
        "CLEAN_FAST_LOSS_OR_ADVERSE",
        "CENSORED_OR_SOURCE_GAP",
    }
)
HIERARCHICAL_ENTRY_QUALITY_GATE = {
    "minimum_group_terminal_count": 5,
    "minimum_group_source_date_count": 3,
    "minimum_walk_forward_fold_count": 2,
    "minimum_cost_adjusted_ev_pct": 0.10,
    "symbol_residual_minimum_terminal_count": 15,
    "symbol_residual_minimum_source_date_count": 5,
    "symbol_residual_shrinkage_prior_count": 20,
}
MECHANISTIC_FLOW_RECHECK_GATE = {
    "minimum_cost_adjusted_mfe_pct": 0.10,
    "minimum_calibration_terminal_count": 20,
    "minimum_calibration_source_date_count": 5,
    "minimum_calibration_positive_count": 3,
    "minimum_calibration_positive_source_date_count": 3,
    "minimum_calibration_positive_rate_lift": 1.15,
    "minimum_holdout_terminal_count": 5,
    "minimum_holdout_source_date_count": 2,
    "minimum_holdout_positive_count": 1,
    "minimum_holdout_positive_source_date_count": 2,
    "minimum_holdout_positive_rate_lift": 1.05,
    "sealed_holdout_source_date_count": 3,
}
LEGACY_COHORT_KEY_VERSION = "v1"
ROUTE_SESSION_COHORT_KEY_VERSION = "v2"
DUAL_AFTERMARKET_SESSION = "KRX_NXT_AFTERMARKET"
DUAL_AFTERMARKET_SCOPE = "INTEGRATED"
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

# Keep this grid deliberately small and limited to fields that exist with the
# same meaning across the historical entry-setup evidence versions.  Newer
# micro-recovery fields are reported separately and are never backfilled into
# an older exact snapshot.
MECHANISTIC_COMMON_FEATURE_GRID = {
    "maximum_spread_bp": (40.0, 60.0, 80.0, 100.0),
    "minimum_fillability_score": (15.0, 30.0, 45.0, 60.0),
    "maximum_top3_ask_to_bid_ratio": (1.0, 1.5, 2.0, 3.0, 5.0),
}
MECHANISTIC_REFINEMENT_GATE = {
    "minimum_cost_adjusted_ev_pct": 0.10,
    "minimum_calibration_exposure_count": 10,
    "minimum_calibration_symbol_count": 5,
    "minimum_calibration_source_date_count": 5,
    "minimum_calibration_terminal_evaluable_count": 10,
    "minimum_holdout_exposure_count": 3,
    "minimum_holdout_source_date_count": 2,
    "minimum_holdout_terminal_evaluable_count": 3,
    "holdout_source_date_count": 3,
}


def _number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


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
        if path.suffix == ".gz":
            with gzip.open(path, "rt", encoding="utf-8") as handle:
                value = json.load(handle)
        else:
            value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _observed_file_sha256(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


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


def _cohort_route_scope(venue: str, session: str, route: str) -> str:
    """Keep legacy keys stable; version dual keys by explicit route."""
    if session == DUAL_AFTERMARKET_SESSION:
        return "|".join(
            (ROUTE_SESSION_COHORT_KEY_VERSION, venue, session, route or "UNKNOWN")
        )
    return f"{venue}:{session}"


def _unpack_cohort_route_scope(scope: str) -> tuple[str, str, str, str]:
    parts = scope.split("|")
    if len(parts) == 4 and parts[0] == ROUTE_SESSION_COHORT_KEY_VERSION:
        return parts[0], parts[1], parts[2], parts[3]
    if ":" in scope:
        venue, session = scope.split(":", 1)
        return LEGACY_COHORT_KEY_VERSION, venue, session, ""
    return "", "", "", ""


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
    routes = (
        cohort.get("market_data_routes")
        if isinstance(cohort.get("market_data_routes"), list)
        else []
    )
    route = _normalized_venue(routes[0]) if len(routes) == 1 else ""
    is_dual_aftermarket = session == DUAL_AFTERMARKET_SESSION
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
    if is_dual_aftermarket:
        if venue != DUAL_AFTERMARKET_SCOPE or not route:
            errors.append("dual_route_session_contract_missing")
        elif not (
            isinstance(cohort_filter, dict)
            and _normalized_venue(cohort_filter.get("market_data_route")) == route
        ):
            errors.append("dual_route_cohort_filter_mismatch")

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
        elif (
            not is_dual_aftermarket
            and _normalized_venue(row.get("effective_venue")) != venue
        ):
            exclusions["venue_mismatch"] += 1
        elif _normalized_session(row.get("session_bucket")) != session:
            exclusions["session_mismatch"] += 1
        elif (
            is_dual_aftermarket
            and _normalized_venue(row.get("market_data_route")) != route
        ):
            exclusions["dual_market_data_route_mismatch"] += 1
        elif is_dual_aftermarket and _normalized_venue(
            row.get("actual_execution_venue")
        ) not in {"KRX", "NXT"}:
            exclusions["dual_actual_execution_venue_unknown"] += 1
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
        elif is_dual_aftermarket and any(
            str(row.get(f"{actor}_action") or "").upper() in EXPOSURE_ACTIONS
            and (
                row.get("candidate_execution_cost_contract_applied") is not True
                or (cost := _number(row.get(f"{actor}_execution_cost_pct"))) is None
                or cost < 0
            )
            for actor in ("control", "candidate")
        ):
            exclusions["dual_exposure_cost_missing_or_invalid"] += 1
        else:
            comparisons.append(row)

    identity = (
        candidate_version,
        candidate_prompt_sha256,
        candidate_contract_sha256,
        stage,
        _cohort_route_scope(venue, session, route),
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
        "market_data_route": route or None,
        "cohort_key_version": (
            ROUTE_SESSION_COHORT_KEY_VERSION
            if is_dual_aftermarket
            else LEGACY_COHORT_KEY_VERSION
        ),
        "authority_state": "OBSERVE_ONLY" if is_dual_aftermarket else "LEGACY",
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
        rows_by_cohort.setdefault(identity, {})
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
                    "market_data_route": metadata["market_data_route"],
                    "cohort_key_version": metadata["cohort_key_version"],
                    "authority_state": metadata["authority_state"],
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


def _mechanistic_terminal_proxy_pct(row: dict[str, Any]) -> float | None:
    """Return an existing-path terminal proxy without inventing an exit.

    Same-bar ambiguous and neither-hit rows are censored.  The thresholds come
    from the paired replay row, and the conservative execution cost is charged
    exactly once.  This remains counterfactual path evidence, not realized PnL.
    """

    comparison = row["comparison"]
    first_hit = str(comparison.get("entry_path_first_hit") or "")
    execution_cost = _number(comparison.get("conservative_execution_cost_pct"))
    if execution_cost is None or execution_cost < 0:
        return None
    if first_hit == "target_first":
        boundary = _number(comparison.get("entry_path_target_pct"))
        if boundary is None or boundary <= 0:
            return None
    elif first_hit == "adverse_first":
        boundary = _number(comparison.get("entry_path_adverse_pct"))
        if boundary is None or boundary >= 0:
            return None
    else:
        return None
    return boundary - execution_cost


def _legacy_entry_group_projection(
    *,
    request: dict[str, Any],
    evidence: dict[str, Any],
    inputs: dict[str, float | None],
) -> dict[str, Any]:
    """Project only reconstructable pre-decision fields from older evidence."""

    price = _number(request.get("reference_price")) or _number(request.get("best_ask"))
    tick_size = (
        _number(get_tick_size(price)) if price is not None and price > 0 else None
    )
    tick_pct = (
        tick_size / price * 100.0
        if tick_size is not None and tick_size > 0 and price is not None
        else None
    )
    price_tick_band = (
        "LT_5BP"
        if tick_pct is not None and tick_pct < 0.05
        else (
            "5_TO_10BP"
            if tick_pct is not None and tick_pct < 0.10
            else "GE_10BP" if tick_pct is not None else "UNKNOWN"
        )
    )
    spread = inputs.get("spread_bp")
    fillability = inputs.get("fillability_score")
    ratio = inputs.get("top3_ask_to_bid_ratio")
    if spread is None or fillability is None or ratio is None:
        liquidity_band = "UNKNOWN"
    elif spread <= 40.0 and fillability >= 45.0 and ratio <= 2.0:
        liquidity_band = "SUPPORTIVE"
    elif spread <= 100.0 and fillability >= 15.0 and ratio <= 5.0:
        liquidity_band = "BOUNDED"
    else:
        liquidity_band = "FRAGILE"
    timing = _as_dict(evidence.get("entry_timing_observation_v1"))
    watch_age = _number(timing.get("watch_age_sec"))
    watch_age_band = (
        "LT_180S"
        if watch_age is not None and watch_age < 180.0
        else (
            "180_TO_600S"
            if watch_age is not None and watch_age < 600.0
            else "GE_600S" if watch_age is not None else "UNKNOWN"
        )
    )
    extension = _number(timing.get("price_delta_since_first_watch_pct"))
    extension_band = (
        "RESET_OR_NEGATIVE"
        if extension is not None and extension < 0.0
        else (
            "LT_1PCT"
            if extension is not None and extension < 1.0
            else "GE_1PCT" if extension is not None else "UNKNOWN"
        )
    )
    key_parts = {
        "price_tick_band": price_tick_band,
        "liquidity_band": liquidity_band,
        "volatility_band": "UNKNOWN",
        "structure_phase": str(evidence.get("structure_phase") or "UNKNOWN"),
        "watch_age_band": watch_age_band,
        "extension_band": extension_band,
        "venue": _normalized_venue(request.get("effective_venue")) or "UNKNOWN",
        "session_bucket": _normalized_session(request.get("session_bucket"))
        or "UNKNOWN",
    }
    return {
        "schema": ENTRY_GROUP_OBSERVATION_SCHEMA,
        "group_key": "|".join(key_parts.values()),
        "key_parts": key_parts,
        "missing_dimensions": sorted(
            key for key, value in key_parts.items() if value == "UNKNOWN"
        ),
        "provenance": "legacy_reconstructable_predecision_projection",
        "future_outcome_fields_used": False,
    }


def _entry_group_observation(
    *,
    request: dict[str, Any],
    evidence: dict[str, Any],
    inputs: dict[str, float | None],
) -> tuple[dict[str, Any], bool]:
    observed = request.get(ENTRY_GROUP_OBSERVATION_SCHEMA)
    if not isinstance(observed, dict):
        observed = evidence.get(ENTRY_GROUP_OBSERVATION_SCHEMA)
    if not isinstance(observed, dict):
        return (
            _legacy_entry_group_projection(
                request=request, evidence=evidence, inputs=inputs
            ),
            True,
        )
    body = {
        key: value
        for key, value in observed.items()
        if key != "group_observation_sha256"
    }
    valid = bool(
        observed.get("schema") == ENTRY_GROUP_OBSERVATION_SCHEMA
        and observed.get("group_observation_sha256") == _canonical_sha256(body)
        and observed.get("future_outcome_fields_forbidden") is True
        and observed.get("runtime_effect") is False
        and observed.get("allowed_runtime_apply") is False
        and isinstance(observed.get("group_key"), str)
        and bool(str(observed.get("group_key") or "").strip())
    )
    if not valid:
        return {
            "schema": ENTRY_GROUP_OBSERVATION_SCHEMA,
            "group_key": "INVALID",
            "key_parts": {},
            "missing_dimensions": [],
            "provenance": "invalid_native_group_observation",
            "future_outcome_fields_used": False,
        }, False
    return dict(observed), True


def _mechanistic_source_rows(
    paired_dir: Path,
    *,
    target_date: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Load common-feature entry rows from clean-baseline detailed replays."""

    rows_by_trace: dict[str, dict[str, Any]] = {}
    conflicted_traces: set[str] = set()
    exclusions: Counter[str] = Counter()
    evidence_versions: Counter[str] = Counter()
    group_provenance_counts: Counter[str] = Counter()
    flow_observation_status_counts: Counter[str] = Counter()
    entry_quality_label_counts: Counter[str] = Counter()
    accepted_source_dates: set[str] = set()
    discovered_report_count = 0
    accepted_report_count = 0
    legacy_hashless_report_count = 0
    identical_duplicate_count = 0
    accepted_source_artifacts: list[dict[str, Any]] = []

    for path in sorted(paired_dir.glob("ai_prompt_detailed_paired_replay_*.json")):
        observed_file_sha256 = _observed_file_sha256(path)
        if observed_file_sha256 is None:
            exclusions["source_file_hash_unavailable"] += 1
            continue
        report = _load_json(path)
        source_date = _report_date(path, report)
        if (
            not source_date
            or source_date < CLEAN_BASELINE_DATE
            or source_date > target_date
        ):
            continue
        cohort_filter = report.get("cohort_filter")
        if not (
            isinstance(cohort_filter, dict)
            and _normalized_venue(cohort_filter.get("effective_venue")) == "KRX"
            and _normalized_session(cohort_filter.get("session_bucket"))
            == "KRX_REGULAR"
        ):
            continue
        discovered_report_count += 1
        if report.get("schema") != DETAILED_PAIRED_SCHEMA:
            exclusions["report_schema_invalid"] += 1
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
            exclusions["report_authority_invalid"] += 1
            continue
        report_hash_declared = report.get("artifact_content_sha256") is not None
        report_hash_verified = _artifact_content_sha256_valid(report)
        if report_hash_declared and not report_hash_verified:
            exclusions["report_content_hash_mismatch"] += 1
            continue
        if not report_hash_declared:
            if source_date >= DETAILED_SELF_HASH_CUTOVER_DATE:
                exclusions["report_content_hash_missing_after_cutover"] += 1
                continue
            legacy_hashless_report_count += 1
        accepted_report_count += 1
        accepted_source_dates.add(source_date)
        accepted_source_artifacts.append(
            {
                "file_name": path.name,
                "source_date": source_date,
                "observed_file_sha256": observed_file_sha256,
                "embedded_content_sha256_verified": report_hash_verified,
                "provenance_tier": (
                    "embedded_content_hash_and_observed_file_hash"
                    if report_hash_verified
                    else "legacy_row_self_hash_and_observed_file_hash"
                ),
            }
        )

        comparisons = {
            str(row.get("decision_trace_id") or ""): row
            for row in report.get("paired_comparisons") or []
            if isinstance(row, dict) and row.get("decision_trace_id")
        }
        for request in report.get("requests") or []:
            if not isinstance(request, dict):
                exclusions["request_not_object"] += 1
                continue
            trace_id = str(request.get("decision_trace_id") or "").strip()
            evidence = request.get("entry_setup_evidence")
            comparison = comparisons.get(trace_id)
            row_date = _kst_date_from_aware_timestamp(request.get("decision_ts"))
            if not trace_id:
                exclusions["decision_trace_id_missing"] += 1
            elif trace_id in conflicted_traces:
                continue
            elif not isinstance(evidence, dict) or not isinstance(comparison, dict):
                exclusions["request_comparison_or_evidence_join_missing"] += 1
            elif (
                _normalized_stage(request.get("stage")) != "entry"
                or _normalized_venue(request.get("effective_venue")) != "KRX"
                or _normalized_session(request.get("session_bucket")) != "KRX_REGULAR"
            ):
                exclusions["request_scope_mismatch"] += 1
            elif not row_date or row_date != source_date:
                exclusions["decision_date_mismatch"] += 1
            elif evidence.get("schema") != "entry_setup_evidence_v1":
                exclusions["evidence_schema_invalid"] += 1
            elif request.get("entry_setup_evidence_sha256") != evidence.get(
                "evidence_sha256"
            ):
                exclusions["request_evidence_hash_mismatch"] += 1
            elif evidence.get("evidence_sha256") != _canonical_sha256(
                {
                    key: value
                    for key, value in evidence.items()
                    if key != "evidence_sha256"
                }
            ):
                exclusions["evidence_self_hash_mismatch"] += 1
            elif _as_dict(evidence.get("source_quality")).get("status") != (
                "fresh_consistent"
            ):
                exclusions["evidence_source_quality_invalid"] += 1
            elif any(
                evidence.get(key) is not expected
                for key, expected in (
                    ("runtime_effect", False),
                    ("allowed_runtime_apply", False),
                    ("actual_order_submitted", False),
                    ("broker_order_forbidden", True),
                )
            ):
                exclusions["evidence_authority_invalid"] += 1
            elif (
                execution_cost := _number(
                    comparison.get("conservative_execution_cost_pct")
                )
            ) is None or execution_cost < 0:
                exclusions["conservative_execution_cost_missing"] += 1
            else:
                inputs = _as_dict(
                    _as_dict(evidence.get("tail_risk_assessment")).get("inputs")
                )
                numeric_inputs = {
                    "spread_bp": _number(inputs.get("spread_bp")),
                    "fillability_score": _number(inputs.get("fillability_score")),
                    "top3_ask_to_bid_ratio": _number(
                        inputs.get("top3_ask_to_bid_ratio")
                    ),
                }
                if any(value is None for value in numeric_inputs.values()):
                    exclusions["common_liquidity_input_missing"] += 1
                    continue
                try:
                    mechanistic_entry_action_core(evidence)
                except ValueError as exc:
                    reason = str(exc).split(":", 1)[0]
                    exclusions[f"mechanistic_evidence_invalid:{reason}"] += 1
                    continue
                group_observation, group_contract_valid = _entry_group_observation(
                    request=request,
                    evidence=evidence,
                    inputs=numeric_inputs,
                )
                exact_analysis = request.get("exact_payload_analysis")
                exact_analysis_body = (
                    {
                        key: value
                        for key, value in exact_analysis.items()
                        if key != "analysis_sha256"
                    }
                    if isinstance(exact_analysis, dict)
                    else {}
                )
                exact_analysis_hash = (
                    exact_analysis.get("analysis_sha256")
                    if isinstance(exact_analysis, dict)
                    else None
                )
                exact_analysis_valid = bool(
                    isinstance(exact_analysis, dict)
                    and exact_analysis.get("schema") == "exact_payload_analysis_v1"
                    and exact_analysis_hash == _canonical_sha256(exact_analysis_body)
                    and request.get("exact_payload_analysis_sha256")
                    == exact_analysis_hash
                )
                if exact_analysis_valid:
                    flow_observation = build_mechanistic_entry_flow_observation(
                        exact_analysis
                    )
                    flow_body = {
                        key: value
                        for key, value in flow_observation.items()
                        if key != "flow_observation_sha256"
                    }
                    flow_observation_contract_valid = bool(
                        flow_observation.get("schema")
                        == MECHANISTIC_ENTRY_FLOW_OBSERVATION_SCHEMA
                        and flow_observation.get("flow_observation_sha256")
                        == _canonical_sha256(flow_body)
                        and flow_observation.get("source_analysis_sha256")
                        == exact_analysis_hash
                        and flow_observation.get("future_outcome_fields_used") is False
                        and flow_observation.get("flow_match_authorizes_recheck_only")
                        is True
                        and flow_observation.get("runtime_effect") is False
                        and flow_observation.get("allowed_runtime_apply") is False
                    )
                    flow_observation_status = (
                        "valid_predecision_projection"
                        if flow_observation_contract_valid
                        else "projection_contract_invalid"
                    )
                else:
                    flow_observation = {
                        "schema": MECHANISTIC_ENTRY_FLOW_OBSERVATION_SCHEMA,
                        "status": "exact_payload_analysis_missing_or_invalid",
                        "matched_families": [],
                        "future_outcome_fields_used": False,
                        "runtime_effect": False,
                        "allowed_runtime_apply": False,
                    }
                    flow_observation_contract_valid = False
                    flow_observation_status = (
                        "exact_payload_analysis_missing_or_invalid"
                    )
                entry_quality_path = comparison.get("entry_quality_path")
                if not isinstance(entry_quality_path, dict):
                    entry_quality_path = {
                        "schema": ENTRY_QUALITY_PATH_SCHEMA,
                        "status": "source_gap",
                        "entry_quality_label": "CENSORED_OR_SOURCE_GAP",
                        "label_reason": "entry_quality_path_not_emitted_by_source_generation",
                    }
                entry_quality_contract_valid = bool(
                    entry_quality_path.get("schema") == ENTRY_QUALITY_PATH_SCHEMA
                    and entry_quality_path.get("entry_quality_label")
                    in ENTRY_QUALITY_LABELS
                    and entry_quality_path.get("runtime_effect") is not True
                    and entry_quality_path.get("allowed_runtime_apply") is not True
                )
                row = {
                    "decision_trace_id": trace_id,
                    "source_date": source_date,
                    "decision_ts": request.get("decision_ts"),
                    "stock_code": str(request.get("stock_code") or ""),
                    "reference_price": _number(request.get("reference_price")),
                    "control_action": str(
                        comparison.get("control_action") or ""
                    ).upper(),
                    "evidence_version": str(evidence.get("version") or "UNKNOWN"),
                    "evidence_sha256": evidence.get("evidence_sha256"),
                    "setup_state": str(evidence.get("setup_state") or "").upper(),
                    "invalidation_facts": sorted(
                        map(str, evidence.get("invalidation_facts") or [])
                    ),
                    "setup_evidence": evidence,
                    "common_inputs": numeric_inputs,
                    "micro_recovery_observed": isinstance(
                        evidence.get("micro_recovery_observation"), dict
                    ),
                    "entry_group_observation": group_observation,
                    "entry_group_contract_valid": group_contract_valid,
                    "mechanistic_flow_observation": flow_observation,
                    "mechanistic_flow_observation_contract_valid": (
                        flow_observation_contract_valid
                    ),
                    "mechanistic_flow_observation_status": flow_observation_status,
                    "entry_quality_path": entry_quality_path,
                    "entry_quality_contract_valid": entry_quality_contract_valid,
                    "comparison": {
                        "control_action": str(
                            comparison.get("control_action") or ""
                        ).upper(),
                        "entry_path_first_hit": str(
                            comparison.get("entry_path_first_hit") or ""
                        ),
                        "entry_path_target_pct": _number(
                            comparison.get("entry_path_target_pct")
                        ),
                        "entry_path_adverse_pct": _number(
                            comparison.get("entry_path_adverse_pct")
                        ),
                        "conservative_execution_cost_pct": execution_cost,
                        "probe_cost_adjusted_mfe_pct": _number(
                            comparison.get("probe_cost_adjusted_mfe_pct")
                        ),
                        "probe_cost_adjusted_mae_pct": _number(
                            comparison.get("probe_cost_adjusted_mae_pct")
                        ),
                        "outcome_mfe_pct": _number(comparison.get("outcome_mfe_pct")),
                        "outcome_mae_pct": _number(comparison.get("outcome_mae_pct")),
                        "directional_pre_profit_mae_pct": _number(
                            comparison.get(
                                "directional_pre_profit_mae_estimate_ex_initial_spread_pct"
                            )
                        ),
                        "drawdown_recovery_observed": (
                            comparison.get("drawdown_recovery_observed") is True
                        ),
                        "path_basis": comparison.get("path_basis"),
                    },
                    "source_report_hash_verified": report_hash_verified,
                    "source_provenance_verified": True,
                }
                fingerprint = _canonical_sha256(
                    {
                        key: value
                        for key, value in row.items()
                        if key
                        not in {
                            "source_report_hash_verified",
                            "source_provenance_verified",
                        }
                    }
                )
                existing = rows_by_trace.get(trace_id)
                if existing is None:
                    rows_by_trace[trace_id] = {**row, "fingerprint": fingerprint}
                elif existing["fingerprint"] == fingerprint:
                    identical_duplicate_count += 1
                    existing["source_report_hash_verified"] = bool(
                        existing["source_report_hash_verified"] or report_hash_verified
                    )
                    existing["source_provenance_verified"] = bool(
                        existing["source_provenance_verified"]
                        or row["source_provenance_verified"]
                    )
                else:
                    rows_by_trace.pop(trace_id, None)
                    conflicted_traces.add(trace_id)
                    exclusions["conflicting_duplicate_trace"] += 1

    rows = sorted(
        rows_by_trace.values(),
        key=lambda row: (row["source_date"], row["decision_trace_id"]),
    )
    for row in rows:
        evidence_versions[row["evidence_version"]] += 1
        group_provenance_counts[
            str(row["entry_group_observation"].get("provenance") or "native")
        ] += 1
        entry_quality_label_counts[
            str(
                row["entry_quality_path"].get("entry_quality_label")
                or "INVALID_OR_MISSING"
            )
        ] += 1
        flow_observation_status_counts[
            str(row.get("mechanistic_flow_observation_status") or "missing")
        ] += 1
    return rows, {
        "discovered_report_count": discovered_report_count,
        "accepted_report_count": accepted_report_count,
        "legacy_hashless_report_count": legacy_hashless_report_count,
        "accepted_unique_trace_count": len(rows),
        "accepted_hash_verified_unique_trace_count": sum(
            row["source_report_hash_verified"] for row in rows
        ),
        "accepted_provenance_verified_unique_trace_count": sum(
            row["source_provenance_verified"] for row in rows
        ),
        "accepted_source_artifacts": accepted_source_artifacts,
        "accepted_rows_sha256": _canonical_sha256(
            [
                {
                    "decision_trace_id": row["decision_trace_id"],
                    "fingerprint": row["fingerprint"],
                }
                for row in rows
            ]
        ),
        "accepted_source_dates": sorted(accepted_source_dates),
        "identical_duplicate_trace_count": identical_duplicate_count,
        "conflicting_duplicate_trace_count": len(conflicted_traces),
        "conflicting_duplicate_traces_excluded": True,
        "row_exclusion_reason_counts": dict(exclusions),
        "evidence_version_counts": dict(sorted(evidence_versions.items())),
        "group_provenance_counts": dict(sorted(group_provenance_counts.items())),
        "flow_observation_status_counts": dict(
            sorted(flow_observation_status_counts.items())
        ),
        "entry_quality_label_counts": dict(sorted(entry_quality_label_counts.items())),
        "pre_baseline_rows_forbidden": True,
        "missing_micro_fields_imputed": False,
    }


def build_market_path_opportunity_anchor_study(
    source_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    """Preserve rising/rebound entry anchors even when no order was filled.

    Detailed paired replay is the existing bounded projection of the pipeline
    raw price path. Reusing it avoids rescanning multi-gigabyte archives while
    retaining exact trace, route, source date and conservative execution cost.
    These anchors are counterfactual diagnostics and never claim a fill or
    realized PnL.
    """

    anchors: list[dict[str, Any]] = []
    rejection_counts: Counter[str] = Counter()
    for row in source_rows:
        comparison = _as_dict(row.get("comparison"))
        if comparison.get("entry_path_first_hit") != "target_first":
            rejection_counts["net_target_not_first"] += 1
            continue
        net_mfe = _number(comparison.get("probe_cost_adjusted_mfe_pct"))
        if net_mfe is None:
            rejection_counts["cost_adjusted_mfe_missing"] += 1
            continue
        if net_mfe < HIERARCHICAL_ENTRY_QUALITY_GATE["minimum_cost_adjusted_ev_pct"]:
            rejection_counts["cost_adjusted_mfe_below_10bp"] += 1
            continue
        pre_profit_mae = _number(comparison.get("directional_pre_profit_mae_pct"))
        rebound = bool(
            comparison.get("drawdown_recovery_observed") is True
            or (pre_profit_mae is not None and pre_profit_mae < 0)
        )
        anchor_type = (
            "rebound_after_drawdown"
            if rebound
            else (
                "target_first_path_detail_gap"
                if pre_profit_mae is None
                else "direct_continuation"
            )
        )
        group = _as_dict(row.get("entry_group_observation"))
        anchors.append(
            {
                "decision_trace_id": row.get("decision_trace_id"),
                "source_date": row.get("source_date"),
                "decision_ts": row.get("decision_ts"),
                "stock_code": row.get("stock_code"),
                "reference_price": row.get("reference_price"),
                "anchor_type": anchor_type,
                "control_action": row.get("control_action"),
                "ai_non_entry_observed": row.get("control_action") in {"WAIT", "DROP"},
                "cost_adjusted_mfe_pct": net_mfe,
                "probe_cost_adjusted_mae_pct": _number(
                    comparison.get("probe_cost_adjusted_mae_pct")
                ),
                "pre_profit_mae_pct": pre_profit_mae,
                "group_key": group.get("group_key"),
                "path_basis": comparison.get("path_basis"),
                "actual_fill_claimed": False,
                "realized_pnl_claimed": False,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
            }
        )
    anchors.sort(
        key=lambda row: (
            str(row.get("source_date") or ""),
            str(row.get("decision_ts") or ""),
            str(row.get("decision_trace_id") or ""),
        )
    )
    source_date_summaries: list[dict[str, Any]] = []
    for source_date in sorted(
        {str(row.get("source_date") or "") for row in source_rows}
    ):
        dated_rows = [
            row for row in source_rows if row.get("source_date") == source_date
        ]
        dated_anchors = [
            row for row in anchors if row.get("source_date") == source_date
        ]
        first_hits = Counter(
            str(
                _as_dict(row.get("comparison")).get("entry_path_first_hit") or "missing"
            )
            for row in dated_rows
        )
        source_date_summaries.append(
            {
                "source_date": source_date,
                "exact_trace_count": len(dated_rows),
                "target_first_anchor_count": len(dated_anchors),
                "rebound_anchor_count": sum(
                    row["anchor_type"] == "rebound_after_drawdown"
                    for row in dated_anchors
                ),
                "direct_continuation_anchor_count": sum(
                    row["anchor_type"] == "direct_continuation" for row in dated_anchors
                ),
                "path_detail_gap_anchor_count": sum(
                    row["anchor_type"] == "target_first_path_detail_gap"
                    for row in dated_anchors
                ),
                "ai_non_entry_anchor_count": sum(
                    row["ai_non_entry_observed"] is True for row in dated_anchors
                ),
                "first_hit_counts": dict(sorted(first_hits.items())),
            }
        )
    return {
        "schema": MARKET_PATH_OPPORTUNITY_ANCHOR_SCHEMA,
        "source_contract": (
            "existing_hash_verified_detailed_replay_market_path_projection"
        ),
        "source_price_contract": (
            "kiwoom_completed_1m_with_pipeline_fallback_preserve_row_path_basis"
        ),
        "minimum_cost_adjusted_mfe_pct": HIERARCHICAL_ENTRY_QUALITY_GATE[
            "minimum_cost_adjusted_ev_pct"
        ],
        "anchor_count": len(anchors),
        "unique_symbol_count": len(
            {row["stock_code"] for row in anchors if row.get("stock_code")}
        ),
        "independent_source_date_count": len(
            {row["source_date"] for row in anchors if row.get("source_date")}
        ),
        "rebound_anchor_count": sum(
            row["anchor_type"] == "rebound_after_drawdown" for row in anchors
        ),
        "direct_continuation_anchor_count": sum(
            row["anchor_type"] == "direct_continuation" for row in anchors
        ),
        "path_detail_gap_anchor_count": sum(
            row["anchor_type"] == "target_first_path_detail_gap" for row in anchors
        ),
        "ai_non_entry_anchor_count": sum(
            row["ai_non_entry_observed"] is True for row in anchors
        ),
        "rejection_counts": dict(sorted(rejection_counts.items())),
        "source_date_summaries": source_date_summaries,
        "anchors": anchors,
        "learning_contract": {
            "clean_baseline_start": CLEAN_BASELINE_DATE,
            "all_accepted_source_dates_used": True,
            "positive_label": "target_first_and_cost_adjusted_mfe_at_least_10bp",
            "negative_label": "adverse_first",
            "censored_labels": ["same_bar_ambiguous", "neither_hit"],
            "chronological_evaluation": "expanding_window_and_sealed_holdout",
            "current_consumer": "mechanistic_entry_refinement_common_feature_search",
            "future_consumer": "hierarchical_group_prior_after_complete_group_evidence",
            "daily_append_without_historical_rescan": True,
        },
        "counterfactual_only_not_realized_pnl": True,
        "actual_and_counterfactual_denominators_merged": False,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }


def _flow_anchor_label(row: dict[str, Any]) -> str:
    comparison = _as_dict(row.get("comparison"))
    first_hit = str(comparison.get("entry_path_first_hit") or "")
    if first_hit == "adverse_first":
        return "ADVERSE_FIRST"
    if first_hit != "target_first":
        return "CENSORED"
    net_mfe = _number(comparison.get("probe_cost_adjusted_mfe_pct"))
    if net_mfe is None:
        return "CENSORED"
    if net_mfe >= MECHANISTIC_FLOW_RECHECK_GATE["minimum_cost_adjusted_mfe_pct"]:
        return "NET_10BP_TARGET_FIRST"
    return "TARGET_FIRST_BELOW_NET_10BP"


def _flow_population_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    labels = Counter(_flow_anchor_label(row) for row in rows)
    terminal_count = len(rows) - labels["CENSORED"]
    positive_count = labels["NET_10BP_TARGET_FIRST"]
    direct_terminal_values = [
        value
        for row in rows
        if _flow_anchor_label(row) != "CENSORED"
        and (value := _mechanistic_terminal_proxy_pct(row)) is not None
    ]
    return {
        "row_count": len(rows),
        "terminal_count": terminal_count,
        "positive_count": positive_count,
        "positive_source_date_count": len(
            {
                str(row.get("source_date") or "")
                for row in rows
                if _flow_anchor_label(row) == "NET_10BP_TARGET_FIRST"
            }
        ),
        "positive_rate": positive_count / terminal_count if terminal_count else None,
        "independent_source_date_count": len(
            {str(row.get("source_date") or "") for row in rows}
        ),
        "unique_symbol_count": len({str(row.get("stock_code") or "") for row in rows}),
        "label_counts": dict(sorted(labels.items())),
        "direct_enter_fixed_boundary_terminal_proxy_ev_pct": (
            fmean(direct_terminal_values) if direct_terminal_values else None
        ),
        "direct_enter_proxy_is_not_recheck_acceptance": True,
    }


def _flow_micro_confirmation_source_audit(
    report_root: Path,
    *,
    target_date: str,
    source_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    """Join contract-valid forward ask-depletion bridge rows by exact trace."""

    from src.engine.scalping.ai_decision_quality import (
        _micro_reversion_current_ablation_ready_bridge_rows,
        _micro_reversion_outcome_source_commitment,
    )

    flow_by_trace = {
        str(row.get("decision_trace_id") or ""): row
        for row in source_rows
        if row.get("mechanistic_flow_observation_contract_valid") is True
        and row.get("decision_trace_id")
    }
    boundary_freeze_date = min(target_date, MECHANISTIC_FLOW_BOUNDARY_FREEZE_DATE)
    joined_by_trace: dict[str, dict[str, Any]] = {}
    conflicted_traces: set[str] = set()
    diagnostic_row_level_join_candidates: set[str] = set()
    rejection_counts: Counter[str] = Counter()
    accepted_report_dates: list[str] = []
    discovered_report_count = 0
    for path in sorted(
        (report_root / "micro_reversion_ai_quality_bridge").glob(
            "micro_reversion_ai_quality_bridge_*.json*"
        )
    ):
        report = _load_json(path)
        source_date = str(report.get("target_date") or "")
        if (
            not source_date
            or source_date <= boundary_freeze_date
            or source_date > target_date
        ):
            continue
        discovered_report_count += 1
        report_rows = {
            str(row.get("decision_trace_id") or ""): row
            for row in report.get("rows") or []
            if isinstance(row, dict) and row.get("decision_trace_id")
        }
        diagnostic_eligible, diagnostic_rejected = (
            _micro_reversion_current_ablation_ready_bridge_rows(report_rows)
        )
        diagnostic_row_level_join_candidates.update(
            set(diagnostic_eligible).intersection(flow_by_trace)
        )
        try:
            _micro_reversion_outcome_source_commitment(
                report, expected_target_date=source_date
            )
        except (TypeError, ValueError) as exc:
            rejection_counts[str(exc).split(":", 1)[0]] += 1
            continue
        eligible = diagnostic_eligible
        rejection_counts.update(diagnostic_rejected.values())
        accepted_report_dates.append(source_date)
        for trace_id, row in eligible.items():
            if trace_id not in flow_by_trace or trace_id in conflicted_traces:
                continue
            sidecar = _as_dict(row.get("ask_depletion_sidecar"))
            sidecar_hash = _canonical_sha256(sidecar)
            existing = joined_by_trace.get(trace_id)
            if existing is not None and existing["sidecar_sha256"] != sidecar_hash:
                joined_by_trace.pop(trace_id, None)
                conflicted_traces.add(trace_id)
                rejection_counts["conflicting_ask_depletion_trace"] += 1
                continue
            joined_by_trace[trace_id] = {
                "source_date": source_date,
                "sidecar_sha256": sidecar_hash,
                "row": row,
            }

    horizon_counts: dict[str, Counter[str]] = defaultdict(Counter)
    family_join_counts: Counter[str] = Counter()
    for trace_id, joined in joined_by_trace.items():
        flow = _as_dict(flow_by_trace[trace_id].get("mechanistic_flow_observation"))
        for family in flow.get("matched_families") or []:
            family_join_counts[str(family)] += 1
        sidecar = _as_dict(joined["row"].get("ask_depletion_sidecar"))
        for horizon in sidecar.get("horizons") or []:
            if (
                not isinstance(horizon, dict)
                or horizon.get("eligible_for_feature_ablation") is not True
            ):
                continue
            horizon_key = str(horizon.get("horizon_ms") or "UNKNOWN")
            horizon_counts[horizon_key]["eligible"] += 1
            velocity = _number(horizon.get("best_ask_depletion_velocity_qty_per_sec"))
            if velocity is not None:
                horizon_counts[horizon_key]["velocity_observed"] += 1
            if _number(horizon.get("aggressive_buy_trade_backed_ratio")) is not None:
                horizon_counts[horizon_key]["trade_backing_observed"] += 1
            if _number(horizon.get("refill_ratio")) is not None:
                horizon_counts[horizon_key]["refill_observed"] += 1

    return {
        "schema": "mechanistic_flow_micro_confirmation_source_audit_v1",
        "target_date": target_date,
        "first_eligible_source_date_is_after": boundary_freeze_date,
        "historical_sidecar_backfill_allowed": False,
        "discovered_report_count": discovered_report_count,
        "accepted_report_dates": sorted(set(accepted_report_dates)),
        "valid_flow_trace_count": len(flow_by_trace),
        "diagnostic_row_level_join_candidate_count": len(
            diagnostic_row_level_join_candidates
        ),
        "eligible_same_trace_join_count": len(joined_by_trace),
        "family_join_counts": dict(sorted(family_join_counts.items())),
        "eligible_horizon_field_counts": {
            key: dict(sorted(counts.items()))
            for key, counts in sorted(
                horizon_counts.items(), key=lambda item: int(item[0])
            )
        },
        "rejection_reason_counts": dict(sorted(rejection_counts.items())),
        "same_trace_join_required": True,
        "parent_report_contract_required": True,
        "row_level_candidate_without_parent_contract_is_ineligible": True,
        "missing_micro_imputed": False,
        "micro_threshold_fitted": False,
        "enter_candidate_issued": False,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }


def build_mechanistic_flow_group_study(
    *,
    target_date: str,
    source_rows: list[dict[str, Any]],
    source_contract: dict[str, Any],
    micro_confirmation_audit: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Find stable pre-decision flow families for a no-exposure RECHECK lane.

    Family definitions are fixed in the shared observation builder.  The last
    three source dates provide retrospective validation for this inaugural
    boundary version, not a pristine holdout because boundary design inspected
    the available history.  Neither a family match nor this study can authorize
    ENTER.  Forward dates must validate RECHECK first, and ENTER remains gated
    by same-trace micro confirmation plus at least +10 bp cost-adjusted EV.
    """

    valid_rows = [
        row
        for row in source_rows
        if row.get("mechanistic_flow_observation_contract_valid") is True
    ]
    terminal_rows = [row for row in valid_rows if _flow_anchor_label(row) != "CENSORED"]
    boundary_freeze_date = min(target_date, MECHANISTIC_FLOW_BOUNDARY_FREEZE_DATE)
    historical_rows = [
        row for row in terminal_rows if row.get("source_date") <= boundary_freeze_date
    ]
    forward_rows = [
        row for row in terminal_rows if row.get("source_date") > boundary_freeze_date
    ]
    source_dates = sorted(
        {str(row.get("source_date") or "") for row in historical_rows}
    )
    holdout_date_count = MECHANISTIC_FLOW_RECHECK_GATE[
        "sealed_holdout_source_date_count"
    ]
    holdout_dates = (
        source_dates[-holdout_date_count:]
        if len(source_dates) > holdout_date_count
        else []
    )
    calibration_dates = [day for day in source_dates if day not in holdout_dates]
    calibration_rows = [
        row for row in historical_rows if row.get("source_date") in calibration_dates
    ]
    holdout_rows = [
        row for row in historical_rows if row.get("source_date") in holdout_dates
    ]
    calibration_baseline = _flow_population_metrics(calibration_rows)
    holdout_baseline = _flow_population_metrics(holdout_rows)
    calibration_base_rate = calibration_baseline["positive_rate"]
    holdout_base_rate = holdout_baseline["positive_rate"]

    family_names = sorted(
        {
            str(family)
            for row in valid_rows
            for family in _as_dict(
                _as_dict(row.get("mechanistic_flow_observation")).get(
                    "family_memberships"
                )
            )
        }
    )
    family_results: list[dict[str, Any]] = []
    accepted_families: list[str] = []
    for family in family_names:
        calibration_family_rows = [
            row
            for row in calibration_rows
            if _as_dict(
                _as_dict(row.get("mechanistic_flow_observation")).get(
                    "family_memberships"
                )
            ).get(family)
            is True
        ]
        holdout_family_rows = [
            row
            for row in holdout_rows
            if _as_dict(
                _as_dict(row.get("mechanistic_flow_observation")).get(
                    "family_memberships"
                )
            ).get(family)
            is True
        ]
        calibration_metrics = _flow_population_metrics(calibration_family_rows)
        holdout_metrics = _flow_population_metrics(holdout_family_rows)
        calibration_lift = (
            calibration_metrics["positive_rate"] / calibration_base_rate
            if calibration_metrics["positive_rate"] is not None
            and calibration_base_rate not in {None, 0.0}
            else None
        )
        holdout_lift = (
            holdout_metrics["positive_rate"] / holdout_base_rate
            if holdout_metrics["positive_rate"] is not None
            and holdout_base_rate not in {None, 0.0}
            else None
        )
        calibration_checks = {
            "minimum_terminal_count": (
                calibration_metrics["terminal_count"]
                >= MECHANISTIC_FLOW_RECHECK_GATE["minimum_calibration_terminal_count"]
            ),
            "minimum_source_date_count": (
                calibration_metrics["independent_source_date_count"]
                >= MECHANISTIC_FLOW_RECHECK_GATE[
                    "minimum_calibration_source_date_count"
                ]
            ),
            "minimum_positive_count": (
                calibration_metrics["positive_count"]
                >= MECHANISTIC_FLOW_RECHECK_GATE["minimum_calibration_positive_count"]
            ),
            "minimum_positive_source_date_count": (
                calibration_metrics["positive_source_date_count"]
                >= MECHANISTIC_FLOW_RECHECK_GATE[
                    "minimum_calibration_positive_source_date_count"
                ]
            ),
            "minimum_positive_rate_lift": (
                calibration_lift is not None
                and calibration_lift
                >= MECHANISTIC_FLOW_RECHECK_GATE[
                    "minimum_calibration_positive_rate_lift"
                ]
            ),
        }
        selected_from_calibration = all(calibration_checks.values())
        holdout_checks = {
            "minimum_terminal_count": (
                holdout_metrics["terminal_count"]
                >= MECHANISTIC_FLOW_RECHECK_GATE["minimum_holdout_terminal_count"]
            ),
            "minimum_source_date_count": (
                holdout_metrics["independent_source_date_count"]
                >= MECHANISTIC_FLOW_RECHECK_GATE["minimum_holdout_source_date_count"]
            ),
            "minimum_positive_count": (
                holdout_metrics["positive_count"]
                >= MECHANISTIC_FLOW_RECHECK_GATE["minimum_holdout_positive_count"]
            ),
            "minimum_positive_source_date_count": (
                holdout_metrics["positive_source_date_count"]
                >= MECHANISTIC_FLOW_RECHECK_GATE[
                    "minimum_holdout_positive_source_date_count"
                ]
            ),
            "minimum_positive_rate_lift": (
                holdout_lift is not None
                and holdout_lift
                >= MECHANISTIC_FLOW_RECHECK_GATE["minimum_holdout_positive_rate_lift"]
            ),
        }
        holdout_acceptance_pass = selected_from_calibration and all(
            holdout_checks.values()
        )
        if holdout_acceptance_pass:
            accepted_families.append(family)
        family_results.append(
            {
                "family": family,
                "selected_from_calibration": selected_from_calibration,
                "calibration_checks": calibration_checks,
                "calibration_metrics": calibration_metrics,
                "calibration_positive_rate_lift": calibration_lift,
                "retrospective_validation_checks": holdout_checks,
                "retrospective_validation_metrics": holdout_metrics,
                "retrospective_validation_positive_rate_lift": holdout_lift,
                "retrospective_validation_pass": holdout_acceptance_pass,
            }
        )

    forward_baseline = _flow_population_metrics(forward_rows)
    forward_base_rate = forward_baseline["positive_rate"]
    forward_family_results: list[dict[str, Any]] = []
    forward_accepted_families: list[str] = []
    for family in accepted_families:
        family_rows = [
            row
            for row in forward_rows
            if _as_dict(
                _as_dict(row.get("mechanistic_flow_observation")).get(
                    "family_memberships"
                )
            ).get(family)
            is True
        ]
        metrics = _flow_population_metrics(family_rows)
        lift = (
            metrics["positive_rate"] / forward_base_rate
            if metrics["positive_rate"] is not None
            and forward_base_rate not in {None, 0.0}
            else None
        )
        checks = {
            "minimum_terminal_count": (
                metrics["terminal_count"]
                >= MECHANISTIC_FLOW_RECHECK_GATE["minimum_holdout_terminal_count"]
            ),
            "minimum_source_date_count": (
                metrics["independent_source_date_count"]
                >= MECHANISTIC_FLOW_RECHECK_GATE["sealed_holdout_source_date_count"]
            ),
            "minimum_positive_count": (
                metrics["positive_count"]
                >= MECHANISTIC_FLOW_RECHECK_GATE["minimum_holdout_positive_count"]
            ),
            "minimum_positive_source_date_count": (
                metrics["positive_source_date_count"]
                >= MECHANISTIC_FLOW_RECHECK_GATE[
                    "minimum_holdout_positive_source_date_count"
                ]
            ),
            "minimum_positive_rate_lift": (
                lift is not None
                and lift
                >= MECHANISTIC_FLOW_RECHECK_GATE["minimum_holdout_positive_rate_lift"]
            ),
        }
        passed = all(checks.values())
        if passed:
            forward_accepted_families.append(family)
        forward_family_results.append(
            {
                "family": family,
                "metrics": metrics,
                "positive_rate_lift": lift,
                "checks": checks,
                "forward_acceptance_pass": passed,
            }
        )

    research_candidate_body = (
        {
            "schema": "mechanistic_entry_flow_recheck_research_candidate_v1",
            "target_date": target_date,
            "boundary_freeze_date": boundary_freeze_date,
            "action_ceiling": "RECHECK",
            "accepted_families": accepted_families,
            "source_rows_sha256": source_contract.get("accepted_rows_sha256"),
            "retrospective_only": True,
            "forward_acceptance_required": True,
            "micro_confirmation_required_for_enter": True,
            "minimum_cost_adjusted_enter_ev_pct": 0.10,
            "direct_enter_authority": False,
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
        }
        if accepted_families
        else None
    )
    research_candidate = (
        {
            **research_candidate_body,
            "candidate_content_sha256": _canonical_sha256(research_candidate_body),
        }
        if research_candidate_body is not None
        else None
    )
    recheck_candidate_body = (
        {
            "schema": "mechanistic_entry_flow_recheck_candidate_v1",
            "target_date": target_date,
            "boundary_freeze_date": boundary_freeze_date,
            "action_ceiling": "RECHECK",
            "accepted_families": forward_accepted_families,
            "source_rows_sha256": source_contract.get("accepted_rows_sha256"),
            "micro_confirmation_required_for_enter": True,
            "minimum_cost_adjusted_enter_ev_pct": 0.10,
            "direct_enter_authority": False,
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
        }
        if forward_accepted_families
        else None
    )
    recheck_candidate = (
        {
            **recheck_candidate_body,
            "candidate_content_sha256": _canonical_sha256(recheck_candidate_body),
        }
        if recheck_candidate_body is not None
        else None
    )
    return {
        "schema": MECHANISTIC_FLOW_GROUP_STUDY_SCHEMA,
        "target_date": target_date,
        "scope": {"stage": "entry", "venue": "KRX", "session": "KRX_REGULAR"},
        "flow_observation_schema": MECHANISTIC_ENTRY_FLOW_OBSERVATION_SCHEMA,
        "source_population": {
            "accepted_unique_trace_count": len(source_rows),
            "valid_flow_observation_count": len(valid_rows),
            "terminal_flow_count": len(terminal_rows),
            "censored_flow_count": len(valid_rows) - len(terminal_rows),
            "source_rows_sha256": source_contract.get("accepted_rows_sha256"),
        },
        "chronological_split": {
            "calibration_source_dates": calibration_dates,
            "retrospective_validation_source_dates": holdout_dates,
            "inaugural_boundary_design_observed_full_history": True,
            "retrospective_validation_is_not_forward_holdout": True,
            "calibration_baseline": calibration_baseline,
            "retrospective_validation_baseline": holdout_baseline,
        },
        "gate": dict(MECHANISTIC_FLOW_RECHECK_GATE),
        "family_results": family_results,
        "retrospective_supported_recheck_families": accepted_families,
        "forward_evaluation": {
            "boundary_freeze_date": boundary_freeze_date,
            "source_dates": sorted(
                {str(row.get("source_date") or "") for row in forward_rows}
            ),
            "baseline": forward_baseline,
            "family_results": forward_family_results,
        },
        "forward_accepted_recheck_families": forward_accepted_families,
        "research_candidate": research_candidate,
        "recheck_candidate": recheck_candidate,
        "enter_policy_candidate": None,
        "forward_acceptance_contract": {
            "first_eligible_source_date_is_after": boundary_freeze_date,
            "minimum_independent_source_date_count": 3,
            "boundaries_frozen_during_forward_window": True,
            "same_family_lift_gates_apply": True,
            "candidate_selection_before_forward_evidence": True,
            "runtime_apply_before_forward_acceptance": False,
        },
        "micro_confirmation_upgrade_contract": {
            "sequence": ["FLOW_FAMILY", "RECHECK", "MICRO_CONFIRMATION", "ENTER"],
            "required_same_trace_features": [
                "bid_support_and_rebound",
                "ask_depletion_velocity",
                "actual_buy_trade_backing",
                "same_price_refill",
            ],
            "ablation_arms": [
                "baseline",
                "bid_and_rebound",
                "depletion_trade_backing_refill",
                "combined",
            ],
            "missing_micro_imputed": False,
            "flow_family_alone_can_enter": False,
            "minimum_cost_adjusted_enter_ev_pct": 0.10,
            "actual_terminal_and_fill_evidence_required": True,
        },
        "micro_confirmation_source_audit": (
            dict(micro_confirmation_audit)
            if isinstance(micro_confirmation_audit, dict)
            else {
                "schema": "mechanistic_flow_micro_confirmation_source_audit_v1",
                "status": "not_supplied",
                "first_eligible_source_date_is_after": boundary_freeze_date,
                "historical_sidecar_backfill_allowed": False,
                "eligible_same_trace_join_count": 0,
                "missing_micro_imputed": False,
                "micro_threshold_fitted": False,
                "enter_candidate_issued": False,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
            }
        ),
        "symbol_adaptation_contract": {
            "group_prior_first": True,
            "exact_symbol_threshold_active": False,
            "future_symbol_residual_requires_existing_minimum_sample_and_shrinkage": True,
            "new_symbol_uses_group_prior_only": True,
        },
        "status": (
            "forward_recheck_candidate_available_micro_confirmation_required"
            if forward_accepted_families
            else (
                "retrospective_flow_lift_detected_forward_acceptance_required"
                if accepted_families
                else "no_flow_family_passes_calibration_and_retrospective_validation"
            )
        ),
        "daily_update_owner": "ai_decision_action_outcome_calibration_existing_postclose_producer",
        "daily_recompute_reads_existing_hash_verified_reports": True,
        "new_raw_archive_rescan_required": False,
        "decision_authority": "offline_source_only_recheck_ranking_no_enter",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def _mechanistic_policy_rows(
    rows: Iterable[dict[str, Any]], policy: dict[str, Any]
) -> list[dict[str, Any]]:
    selected = []
    threshold_policy = json.loads(json.dumps(MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1))
    threshold_policy["version"] = MECHANISTIC_REFINEMENT_POLICY_VERSION
    threshold_policy["thresholds"].update(policy)
    for row in rows:
        evidence = row.get("setup_evidence")
        if not isinstance(evidence, dict):
            continue
        decision = mechanistic_entry_policy_decision(
            evidence,
            policy=threshold_policy,
        )
        if decision.get("action") == "ENTER_NOW":
            selected.append(row)
    return selected


def _mechanistic_policy_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    terminal_values = []
    paired_deltas = []
    for row in rows:
        terminal_value = _mechanistic_terminal_proxy_pct(row)
        if terminal_value is None:
            continue
        terminal_values.append(terminal_value)
        control_value = _decision_value(
            row["comparison"]["control_action"], terminal_value
        )
        if control_value is not None:
            paired_deltas.append(terminal_value - control_value)
    dates = {row["source_date"] for row in rows}
    symbols = {row["stock_code"] for row in rows if row["stock_code"]}
    net_ten_bp_opportunities = sum(
        (value := _number(row["comparison"].get("probe_cost_adjusted_mfe_pct")))
        is not None
        and value >= 0.10
        for row in rows
    )
    return {
        "exposure_count": len(rows),
        "source_report_hash_verified_count": sum(
            row["source_report_hash_verified"] for row in rows
        ),
        "source_report_hash_contract_complete": all(
            row["source_report_hash_verified"] for row in rows
        ),
        "source_provenance_verified_count": sum(
            row["source_provenance_verified"] for row in rows
        ),
        "source_provenance_contract_complete": all(
            row["source_provenance_verified"] for row in rows
        ),
        "unique_symbol_count": len(symbols),
        "independent_source_date_count": len(dates),
        "exposures_per_source_date": (len(rows) / len(dates) if dates else None),
        "terminal_evaluable_count": len(terminal_values),
        "censored_or_ambiguous_count": len(rows) - len(terminal_values),
        "cost_adjusted_terminal_proxy_ev_pct": (
            fmean(terminal_values) if terminal_values else None
        ),
        "paired_terminal_proxy_delta_count": len(paired_deltas),
        "paired_terminal_proxy_delta_pct": (
            fmean(paired_deltas) if paired_deltas else None
        ),
        "net_10bp_path_opportunity_count": net_ten_bp_opportunities,
        "net_10bp_path_opportunity_rate_pct": (
            net_ten_bp_opportunities / len(rows) * 100.0 if rows else None
        ),
        "catastrophic_terminal_proxy_count": sum(
            value <= CATASTROPHIC_LOSS_PCT for value in terminal_values
        ),
        "counterfactual_path_only_not_realized_pnl": True,
    }


def _mechanistic_paired_population_metrics(
    population: list[dict[str, Any]], selected: list[dict[str, Any]]
) -> dict[str, Any]:
    selected_trace_ids = {row["decision_trace_id"] for row in selected}
    deltas = []
    terminal_evaluable_count = 0
    for row in population:
        terminal_value = _mechanistic_terminal_proxy_pct(row)
        if terminal_value is None:
            continue
        terminal_evaluable_count += 1
        control_value = _decision_value(
            row["comparison"]["control_action"], terminal_value
        )
        if control_value is None:
            continue
        mechanistic_value = (
            terminal_value if row["decision_trace_id"] in selected_trace_ids else 0.0
        )
        deltas.append(mechanistic_value - control_value)
    return {
        "population_count": len(population),
        "terminal_evaluable_count": terminal_evaluable_count,
        "paired_comparable_count": len(deltas),
        "paired_terminal_proxy_delta_pct": fmean(deltas) if deltas else None,
        "paired_terminal_contract_complete": len(deltas) == terminal_evaluable_count,
    }


def build_clean_baseline_mechanistic_refinement(
    paired_dir: Path,
    *,
    target_date: str,
    source_rows: list[dict[str, Any]] | None = None,
    source_contract: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Tune a common-feature mechanistic challenger with a sealed holdout."""

    target_day = date.fromisoformat(target_date)
    if target_day < date.fromisoformat(CLEAN_BASELINE_DATE):
        raise ValueError("target_date_before_clean_baseline")
    if (source_rows is None) != (source_contract is None):
        raise ValueError("mechanistic_source_bundle_incomplete")
    if source_rows is None or source_contract is None:
        rows, source_contract = _mechanistic_source_rows(
            paired_dir, target_date=target_date
        )
    else:
        rows = source_rows
    source_dates = list(source_contract["accepted_source_dates"])
    holdout_count = MECHANISTIC_REFINEMENT_GATE["holdout_source_date_count"]
    holdout_dates = (
        source_dates[-holdout_count:] if len(source_dates) > holdout_count else []
    )
    calibration_dates = [day for day in source_dates if day not in holdout_dates]
    calibration_rows = [row for row in rows if row["source_date"] in calibration_dates]
    holdout_rows = [row for row in rows if row["source_date"] in holdout_dates]
    holdout_dates_with_accepted_rows = sorted(
        {row["source_date"] for row in holdout_rows}
    )
    path_boundary_counts = Counter(
        (
            row["comparison"].get("entry_path_target_pct"),
            row["comparison"].get("entry_path_adverse_pct"),
        )
        for row in rows
    )
    path_boundary_contract_isolated = len(path_boundary_counts) <= 1

    candidates: list[dict[str, Any]] = []
    seen_selections: set[str] = set()
    grid = MECHANISTIC_COMMON_FEATURE_GRID
    for maximum_spread_bp in grid["maximum_spread_bp"]:
        for minimum_fillability_score in grid["minimum_fillability_score"]:
            for maximum_ratio in grid["maximum_top3_ask_to_bid_ratio"]:
                policy = {
                    "maximum_spread_bp": maximum_spread_bp,
                    "minimum_fillability_score": minimum_fillability_score,
                    "maximum_top3_ask_to_bid_ratio": maximum_ratio,
                }
                selected = _mechanistic_policy_rows(calibration_rows, policy)
                selection_sha256 = _canonical_sha256(
                    [
                        {
                            "decision_trace_id": row["decision_trace_id"],
                            "fingerprint": row["fingerprint"],
                        }
                        for row in selected
                    ]
                )
                if selection_sha256 in seen_selections:
                    continue
                seen_selections.add(selection_sha256)
                metrics = _mechanistic_policy_metrics(selected)
                paired_population = _mechanistic_paired_population_metrics(
                    calibration_rows, selected
                )
                gate_pass = (
                    metrics["exposure_count"]
                    >= MECHANISTIC_REFINEMENT_GATE["minimum_calibration_exposure_count"]
                    and metrics["unique_symbol_count"]
                    >= MECHANISTIC_REFINEMENT_GATE["minimum_calibration_symbol_count"]
                    and metrics["independent_source_date_count"]
                    >= MECHANISTIC_REFINEMENT_GATE[
                        "minimum_calibration_source_date_count"
                    ]
                    and metrics["terminal_evaluable_count"]
                    >= MECHANISTIC_REFINEMENT_GATE[
                        "minimum_calibration_terminal_evaluable_count"
                    ]
                    and metrics["paired_terminal_proxy_delta_count"]
                    == metrics["terminal_evaluable_count"]
                )
                if gate_pass:
                    candidates.append(
                        {
                            "policy": policy,
                            "selection_sha256": selection_sha256,
                            "calibration": metrics,
                            "calibration_paired_population": paired_population,
                        }
                    )

    calibration_floor = MECHANISTIC_REFINEMENT_GATE["minimum_cost_adjusted_ev_pct"]
    calibration_passers = [
        row
        for row in candidates
        if row["calibration"]["cost_adjusted_terminal_proxy_ev_pct"]
        >= calibration_floor
        and row["calibration_paired_population"]["paired_terminal_proxy_delta_pct"]
        is not None
        and row["calibration_paired_population"]["paired_terminal_proxy_delta_pct"] > 0
        and row["calibration_paired_population"]["paired_terminal_contract_complete"]
        is True
        and row["calibration"]["source_provenance_contract_complete"] is True
        and row["calibration"]["catastrophic_terminal_proxy_count"] == 0
    ]
    ranked = calibration_passers or candidates
    ranked.sort(
        key=(
            (
                lambda row: (
                    row["calibration"]["exposures_per_source_date"],
                    row["calibration"]["net_10bp_path_opportunity_rate_pct"],
                    row["calibration"]["cost_adjusted_terminal_proxy_ev_pct"],
                )
            )
            if calibration_passers
            else (
                lambda row: (
                    row["calibration"]["cost_adjusted_terminal_proxy_ev_pct"],
                    row["calibration"]["exposure_count"],
                    -row["calibration"]["catastrophic_terminal_proxy_count"],
                )
            )
        ),
        reverse=True,
    )
    best = ranked[0] if ranked else None
    holdout_metrics = None
    holdout_paired_population = None
    holdout_selection_sha256 = None
    promotion_checks: dict[str, bool] = {}
    if best is not None:
        holdout_selected = _mechanistic_policy_rows(holdout_rows, best["policy"])
        holdout_selection_sha256 = _canonical_sha256(
            [
                {
                    "decision_trace_id": row["decision_trace_id"],
                    "fingerprint": row["fingerprint"],
                }
                for row in holdout_selected
            ]
        )
        holdout_metrics = _mechanistic_policy_metrics(holdout_selected)
        holdout_paired_population = _mechanistic_paired_population_metrics(
            holdout_rows, holdout_selected
        )
        calibration_ev = best["calibration"]["cost_adjusted_terminal_proxy_ev_pct"]
        holdout_ev = holdout_metrics["cost_adjusted_terminal_proxy_ev_pct"]
        promotion_checks = {
            "calibration_cost_adjusted_ev_at_least_10bp": (
                calibration_ev is not None
                and calibration_ev
                >= MECHANISTIC_REFINEMENT_GATE["minimum_cost_adjusted_ev_pct"]
            ),
            "holdout_cost_adjusted_ev_at_least_10bp": (
                holdout_ev is not None
                and holdout_ev
                >= MECHANISTIC_REFINEMENT_GATE["minimum_cost_adjusted_ev_pct"]
            ),
            "calibration_positive_paired_terminal_delta": (
                best["calibration_paired_population"]["paired_terminal_proxy_delta_pct"]
                is not None
                and best["calibration_paired_population"][
                    "paired_terminal_proxy_delta_pct"
                ]
                > 0
            ),
            "holdout_positive_paired_terminal_delta": (
                holdout_paired_population["paired_terminal_proxy_delta_pct"] is not None
                and holdout_paired_population["paired_terminal_proxy_delta_pct"] > 0
            ),
            "holdout_paired_terminal_delta_complete": (
                holdout_paired_population["paired_terminal_contract_complete"] is True
            ),
            "calibration_source_provenance_complete": (
                best["calibration"]["source_provenance_contract_complete"] is True
            ),
            "holdout_source_provenance_complete": (
                holdout_metrics["source_provenance_contract_complete"] is True
            ),
            "holdout_exposure_floor": (
                holdout_metrics["exposure_count"]
                >= MECHANISTIC_REFINEMENT_GATE["minimum_holdout_exposure_count"]
            ),
            "holdout_source_date_floor": (
                holdout_metrics["independent_source_date_count"]
                >= MECHANISTIC_REFINEMENT_GATE["minimum_holdout_source_date_count"]
            ),
            "holdout_terminal_evaluable_floor": (
                holdout_metrics["terminal_evaluable_count"]
                >= MECHANISTIC_REFINEMENT_GATE[
                    "minimum_holdout_terminal_evaluable_count"
                ]
            ),
            "calibration_no_catastrophic_terminal_proxy": (
                best["calibration"]["catastrophic_terminal_proxy_count"] == 0
            ),
            "no_catastrophic_terminal_proxy": (
                holdout_metrics["catastrophic_terminal_proxy_count"] == 0
            ),
        }
    promotion_checks["path_boundary_contract_isolated"] = (
        path_boundary_contract_isolated
    )
    promotion_checks["holdout_source_coverage_complete"] = (
        bool(holdout_dates) and holdout_dates_with_accepted_rows == holdout_dates
    )
    promotion_pass = (
        best is not None and bool(promotion_checks) and all(promotion_checks.values())
    )
    policy_candidate_body = (
        {
            "schema": "mechanistic_entry_common_feature_candidate_v1",
            "policy_version": MECHANISTIC_REFINEMENT_POLICY_VERSION,
            "thresholds": best["policy"],
            "decision_role_contract": {
                "primary_decision_owner": "mechanistic_entry_adjudicator",
                "ai_role": "auxiliary_risk_screen_pass_veto_no_promotion",
                "hard_safety_owner": "existing_runtime_submit_and_order_guards",
            },
            "shared_decision_function": (
                "entry_setup_evidence.mechanistic_entry_policy_decision"
            ),
            "calibration_selection_sha256": best["selection_sha256"],
            "source_contract_sha256": _canonical_sha256(source_contract),
            "calibration_source_dates": calibration_dates,
            "holdout_source_dates": holdout_dates,
            "calibration_metrics": best["calibration"],
            "calibration_paired_population": best["calibration_paired_population"],
            "holdout_metrics": holdout_metrics,
            "holdout_paired_population": holdout_paired_population,
            "holdout_selection_sha256": holdout_selection_sha256,
            "promotion_checks": promotion_checks,
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
        }
        if best is not None and promotion_pass
        else None
    )
    policy_candidate = (
        {
            **policy_candidate_body,
            "candidate_content_sha256": _canonical_sha256(policy_candidate_body),
        }
        if policy_candidate_body is not None
        else None
    )
    return {
        "schema": MECHANISTIC_REFINEMENT_SCHEMA,
        "policy_version": MECHANISTIC_REFINEMENT_POLICY_VERSION,
        "target_date": target_date,
        "clean_tuning_baseline_date": CLEAN_BASELINE_DATE,
        "scope": {"stage": "entry", "venue": "KRX", "session": "KRX_REGULAR"},
        "source_contract": source_contract,
        "chronological_split": {
            "calibration_source_dates": calibration_dates,
            "holdout_source_dates": holdout_dates,
            "holdout_source_dates_with_accepted_rows": (
                holdout_dates_with_accepted_rows
            ),
            "holdout_used_for_candidate_selection": False,
        },
        "common_feature_contract": {
            "setup_state": "READY",
            "invalidation_facts_required_empty": True,
            "decision_function": (
                "entry_setup_evidence.mechanistic_entry_policy_decision"
            ),
            "risk_fact_bindings_and_micro_thresholds_shared_with_runtime": True,
            "features": sorted(
                (
                    "spread_bp",
                    "fillability_score",
                    "top3_ask_to_bid_ratio",
                    "micro_net_aggressive_delta_10t",
                    "micro_price_change_10t_pct",
                )
            ),
            "micro_recovery_missing_imputed": False,
            "micro_enhanced_trace_count": sum(
                row["micro_recovery_observed"] for row in rows
            ),
        },
        "objective": {
            "metric": "existing_first_hit_cost_adjusted_terminal_proxy_ev_pct",
            "minimum_ev_pct": 0.10,
            "same_bar_ambiguous_and_neither_hit": "censored_not_zero",
            "cost_charged_once": True,
            "path_opportunity_not_realized_fill": True,
            "path_boundary_contract_counts": {
                f"target={target}|adverse={adverse}": count
                for (target, adverse), count in sorted(
                    path_boundary_counts.items(), key=lambda item: str(item[0])
                )
            },
            "path_boundary_contract_isolated": path_boundary_contract_isolated,
        },
        "nominal_grid_candidate_count": (
            len(grid["maximum_spread_bp"])
            * len(grid["minimum_fillability_score"])
            * len(grid["maximum_top3_ask_to_bid_ratio"])
        ),
        "grid_candidate_count": len(candidates),
        "calibration_floor_passing_candidate_count": len(calibration_passers),
        "candidate_selection_basis": (
            "frequency_then_net_10bp_opportunity_then_ev_among_calibration_passers"
            if calibration_passers
            else "best_diagnostic_ev_no_calibration_candidate_passed"
        ),
        "best_observed_candidate": best,
        "best_observed_holdout": holdout_metrics,
        "best_observed_holdout_paired_population": holdout_paired_population,
        "best_observed_holdout_selection_sha256": holdout_selection_sha256,
        "promotion_checks": promotion_checks,
        "promotion_pass": promotion_pass,
        "policy_candidate": policy_candidate,
        "status": (
            "offline_policy_candidate_available_requires_existing_review_and_apply_guards"
            if policy_candidate is not None
            else (
                "no_common_feature_candidate_meets_cost_adjusted_10bp_holdout_gate"
                if best is not None
                else "insufficient_clean_common_feature_evidence"
            )
        ),
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def _entry_quality_population_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    labels = Counter(
        str(row["entry_quality_path"].get("entry_quality_label") or "") for row in rows
    )
    clean_count = labels["CLEAN_FAST_PROFIT"]
    dirty_count = sum(
        labels[name]
        for name in (
            "PROFITABLE_BUT_LATE",
            "PROFIT_AFTER_DEEP_ADVERSE",
            "PROFIT_AFTER_SIDEWAYS",
        )
    )
    adverse_count = labels["CLEAN_FAST_LOSS_OR_ADVERSE"]
    terminal_values = [
        value
        for row in rows
        if (value := _mechanistic_terminal_proxy_pct(row)) is not None
    ]
    return {
        "row_count": len(rows),
        "unique_symbol_count": len(
            {row["stock_code"] for row in rows if row.get("stock_code")}
        ),
        "independent_source_date_count": len({row["source_date"] for row in rows}),
        "label_counts": dict(sorted(labels.items())),
        "clean_fast_count": clean_count,
        "dirty_profit_count": dirty_count,
        "adverse_count": adverse_count,
        "enter_clean_fast_precision_pct": (
            clean_count / len(rows) * 100.0 if rows else None
        ),
        "dirty_profit_enter_rate_pct": (
            dirty_count / len(rows) * 100.0 if rows else None
        ),
        "adverse_enter_rate_pct": (adverse_count / len(rows) * 100.0 if rows else None),
        "cost_adjusted_terminal_proxy_ev_pct": (
            fmean(terminal_values) if terminal_values else None
        ),
        "terminal_proxy_evaluable_count": len(terminal_values),
        "counterfactual_only_not_realized_pnl": True,
    }


def _actual_entry_quality_source_audit(
    report_root: Path,
    *,
    target_date: str,
    counterfactual_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    lifecycle_status_counts: Counter[str] = Counter()
    path_status_counts: Counter[str] = Counter()
    path_label_counts: Counter[str] = Counter()
    lifecycle_source_dates: set[str] = set()
    path_source_dates: set[str] = set()
    filled_count = 0
    path_evaluable_count = 0
    economic_acceptance_eligible_count = 0
    accepted_label_report_count = 0
    rejected_label_report_counts: Counter[str] = Counter()
    realized_lifecycle_count = 0
    realized_net_10bp_count = 0
    realized_net_10bp_fast_count = 0
    realized_net_10bp_late_count = 0
    realized_loss_count = 0
    raw_decision_path_join_count = 0
    realized_anchor_ledger: list[dict[str, Any]] = []
    counterfactual_by_trace = {
        str(row.get("decision_trace_id") or ""): row
        for row in counterfactual_rows or []
        if row.get("decision_trace_id")
    }
    for path in sorted(
        (report_root / "main_scalping_lifecycle_paired").glob(
            "main_scalping_lifecycle_paired_*.json"
        )
    ):
        report = _load_json(path)
        source_date = _report_date(path, report)
        if (
            not source_date
            or source_date < CLEAN_BASELINE_DATE
            or source_date > target_date
        ):
            continue
        lifecycle_source_dates.add(source_date)
        lifecycle_rows = report.get("lifecycles") or report.get("rows") or []
        for row in lifecycle_rows:
            if not isinstance(row, dict) or not row.get("first_fill_execution_at"):
                continue
            filled_count += 1
            terminal_state = str(row.get("terminal_state") or "")
            realized_pnl = _number(row.get("realized_net_pnl_krw"))
            entry_notional = _number(row.get("entry_notional_krw"))
            duration_sec = _number(row.get("actual_holding_duration_sec"))
            trace_ids = {
                str(item.get("decision_trace_id") or "")
                for item in row.get("decision_trace_context_path") or []
                if isinstance(item, dict)
                and item.get("stage") == "entry_decision"
                and item.get("decision_trace_id")
            }
            entry_trace_id = next(iter(trace_ids)) if len(trace_ids) == 1 else None
            if (
                terminal_state == "FINAL_EXIT_RECONCILED"
                and realized_pnl is not None
                and entry_notional is not None
                and entry_notional > 0
            ):
                realized_lifecycle_count += 1
                realized_net_pct = realized_pnl / entry_notional * 100.0
                realized_class = "positive_below_net_10bp"
                if realized_net_pct >= 0.10:
                    realized_net_10bp_count += 1
                    if duration_sec is not None and duration_sec <= 180.0:
                        realized_net_10bp_fast_count += 1
                        realized_class = "net_10bp_within_180s_path_quality_unresolved"
                    else:
                        realized_net_10bp_late_count += 1
                        realized_class = "net_10bp_after_180s"
                elif realized_pnl < 0:
                    realized_loss_count += 1
                    realized_class = "realized_loss"
                realized_anchor_ledger.append(
                    {
                        "source_date": source_date,
                        "stock_code": row.get("stock_code"),
                        "first_fill_execution_at": row.get("first_fill_execution_at"),
                        "final_exit_execution_at": row.get("final_exit_execution_at"),
                        "actual_holding_duration_sec": duration_sec,
                        "realized_net_pnl_krw": realized_pnl,
                        "entry_notional_krw": entry_notional,
                        "realized_net_pct": realized_net_pct,
                        "realized_class": realized_class,
                        "reviewed_cost_profile_verified": (
                            row.get("reviewed_cost_profile_verified") is True
                        ),
                        "row_source_quality_gate_pass": (
                            row.get("row_source_quality_gate_pass") is True
                        ),
                        "entry_decision_trace_id": entry_trace_id,
                        "market_path_projection_joined": (
                            entry_trace_id in counterfactual_by_trace
                            if entry_trace_id is not None
                            else False
                        ),
                        "clean_entry_path_claimed": False,
                    }
                )
            if entry_trace_id in counterfactual_by_trace:
                raw_decision_path_join_count += 1
            path_evidence = row.get("actual_entry_quality_path")
            if not isinstance(path_evidence, dict):
                lifecycle_status_counts["missing"] += 1
                continue
            status = str(path_evidence.get("status") or "missing")
            lifecycle_status_counts[status] += 1
    outcome_dir = report_root / "ai_decision_outcome_labels"
    outcome_paths = sorted(outcome_dir.glob("ai_decision_outcome_labels_*.json"))
    outcome_paths.extend(
        path
        for path in sorted(outcome_dir.glob("ai_decision_outcome_labels_*.json.gz"))
        if path.with_suffix("").with_suffix(".json") not in outcome_paths
    )
    for path in outcome_paths:
        report = _load_json(path)
        source_date = _report_date(path, report)
        if (
            not source_date
            or source_date < CLEAN_BASELINE_DATE
            or source_date > target_date
        ):
            continue
        if report.get("schema") != "ai_decision_outcome_labels_v1":
            rejected_label_report_counts["schema_invalid"] += 1
            continue
        if report.get("target_date") != source_date:
            rejected_label_report_counts["target_date_mismatch"] += 1
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
            rejected_label_report_counts["authority_invalid"] += 1
            continue
        accepted_label_report_count += 1
        for label_row in report.get("labels") or []:
            if not isinstance(label_row, dict):
                continue
            path_evidence = _as_dict(
                _as_dict(label_row.get("stage_outcome")).get(
                    "actual_fill_entry_quality_path"
                )
            )
            if (
                not path_evidence
                or path_evidence.get("actual_fill_observed") is not True
            ):
                continue
            path_source_dates.add(source_date)
            status = str(path_evidence.get("status") or "missing")
            label = str(
                path_evidence.get("entry_quality_label") or "CENSORED_OR_SOURCE_GAP"
            )
            path_status_counts[status] += 1
            path_label_counts[label] += 1
            if status == "evaluable" and label in ENTRY_QUALITY_LABELS:
                path_evaluable_count += 1
                if (
                    path_evidence.get("path_authority")
                    == "actual_fill_anchor_executable_bid_path"
                    and path_evidence.get("economic_acceptance_eligible") is True
                    and path_evidence.get("realized_cost_contract_complete") is True
                ):
                    economic_acceptance_eligible_count += 1
    return {
        "schema": "actual_entry_quality_source_audit_v1",
        "lifecycle_source_dates": sorted(lifecycle_source_dates),
        "path_source_dates": sorted(path_source_dates),
        "filled_lifecycle_count": filled_count,
        "path_evaluable_count": path_evaluable_count,
        "economic_acceptance_eligible_count": (economic_acceptance_eligible_count),
        "realized_lifecycle_count": realized_lifecycle_count,
        "realized_net_10bp_count": realized_net_10bp_count,
        "realized_net_10bp_fast_count": realized_net_10bp_fast_count,
        "realized_net_10bp_late_count": realized_net_10bp_late_count,
        "realized_loss_count": realized_loss_count,
        "raw_decision_path_join_count": raw_decision_path_join_count,
        "fast_realized_outcome_is_clean_path_proof": False,
        "realized_anchor_ledger": realized_anchor_ledger,
        "accepted_label_report_count": accepted_label_report_count,
        "rejected_label_report_counts": dict(
            sorted(rejected_label_report_counts.items())
        ),
        "lifecycle_status_counts": dict(sorted(lifecycle_status_counts.items())),
        "path_status_counts": dict(sorted(path_status_counts.items())),
        "path_label_counts": dict(sorted(path_label_counts.items())),
        "actual_and_counterfactual_denominators_merged": False,
        "holding_duration_used_as_time_to_target": False,
        "missing_cost_or_path_imputed": False,
        "status": (
            "actual_economic_source_available"
            if economic_acceptance_eligible_count
            else (
                "actual_path_diagnostic_available"
                if path_evaluable_count
                else (
                    "realized_outcome_available_path_quality_gap"
                    if realized_lifecycle_count
                    else "actual_path_source_gap"
                )
            )
        ),
    }


def build_hierarchical_entry_quality_walk_forward(
    paired_dir: Path,
    *,
    target_date: str,
    source_rows: list[dict[str, Any]],
    source_contract: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate group priors chronologically without symbol threshold fitting."""

    evaluable_rows = [
        row
        for row in source_rows
        if row.get("entry_group_contract_valid") is True
        and row.get("entry_quality_contract_valid") is True
        and row["entry_quality_path"].get("status") == "evaluable"
        and row["entry_quality_path"].get("entry_quality_label")
        != "CENSORED_OR_SOURCE_GAP"
    ]
    group_complete_rows = [
        row
        for row in evaluable_rows
        if not row["entry_group_observation"].get("missing_dimensions")
    ]
    source_dates = sorted({row["source_date"] for row in group_complete_rows})
    folds: list[dict[str, Any]] = []
    all_selected_evaluation_rows: list[dict[str, Any]] = []
    all_evaluation_rows: list[dict[str, Any]] = []
    minimum_train_dates = HIERARCHICAL_ENTRY_QUALITY_GATE[
        "minimum_group_source_date_count"
    ]
    for index in range(minimum_train_dates, len(source_dates)):
        evaluation_date = source_dates[index]
        training_dates = source_dates[:index]
        training_rows = [
            row for row in group_complete_rows if row["source_date"] in training_dates
        ]
        evaluation_rows = [
            row for row in group_complete_rows if row["source_date"] == evaluation_date
        ]
        rows_by_group: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in training_rows:
            rows_by_group[str(row["entry_group_observation"]["group_key"])].append(row)
        eligible_groups: list[str] = []
        group_training_metrics: dict[str, dict[str, Any]] = {}
        for group_key, group_rows in sorted(rows_by_group.items()):
            metrics = _entry_quality_population_metrics(group_rows)
            group_training_metrics[group_key] = metrics
            ev = metrics["cost_adjusted_terminal_proxy_ev_pct"]
            if (
                metrics["row_count"]
                >= HIERARCHICAL_ENTRY_QUALITY_GATE["minimum_group_terminal_count"]
                and metrics["independent_source_date_count"]
                >= HIERARCHICAL_ENTRY_QUALITY_GATE["minimum_group_source_date_count"]
                and ev is not None
                and ev
                >= HIERARCHICAL_ENTRY_QUALITY_GATE["minimum_cost_adjusted_ev_pct"]
                and metrics["clean_fast_count"]
                > metrics["dirty_profit_count"] + metrics["adverse_count"]
            ):
                eligible_groups.append(group_key)
        selected = [
            row
            for row in evaluation_rows
            if row["entry_group_observation"]["group_key"] in eligible_groups
        ]
        all_evaluation_rows.extend(evaluation_rows)
        all_selected_evaluation_rows.extend(selected)
        total_clean = sum(
            row["entry_quality_path"].get("entry_quality_label") == "CLEAN_FAST_PROFIT"
            for row in evaluation_rows
        )
        selected_clean = sum(
            row["entry_quality_path"].get("entry_quality_label") == "CLEAN_FAST_PROFIT"
            for row in selected
        )
        folds.append(
            {
                "evaluation_date": evaluation_date,
                "training_dates": training_dates,
                "training_max_date": max(training_dates),
                "future_rows_used_for_training": False,
                "eligible_group_keys": eligible_groups,
                "group_training_metrics": group_training_metrics,
                "evaluation_population": _entry_quality_population_metrics(
                    evaluation_rows
                ),
                "selected_evaluation": _entry_quality_population_metrics(selected),
                "clean_fast_recall_pct": (
                    selected_clean / total_clean * 100.0 if total_clean else None
                ),
            }
        )

    symbol_counts: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in evaluable_rows:
        if row.get("stock_code"):
            symbol_counts[str(row["stock_code"])].append(row)
    qualifying_symbols = sorted(
        symbol
        for symbol, rows in symbol_counts.items()
        if len(rows)
        >= HIERARCHICAL_ENTRY_QUALITY_GATE["symbol_residual_minimum_terminal_count"]
        and len({row["source_date"] for row in rows})
        >= HIERARCHICAL_ENTRY_QUALITY_GATE["symbol_residual_minimum_source_date_count"]
    )
    aggregate_selected = _entry_quality_population_metrics(all_selected_evaluation_rows)
    aggregate_population = _entry_quality_population_metrics(all_evaluation_rows)
    fold_dates_ordered = all(
        fold["training_max_date"] < fold["evaluation_date"] for fold in folds
    )
    actual_lane = _actual_entry_quality_source_audit(
        paired_dir.parent,
        target_date=target_date,
        counterfactual_rows=source_rows,
    )
    market_path_opportunities = build_market_path_opportunity_anchor_study(source_rows)
    promotion_checks = {
        "minimum_walk_forward_fold_count": (
            len(folds)
            >= HIERARCHICAL_ENTRY_QUALITY_GATE["minimum_walk_forward_fold_count"]
        ),
        "walk_forward_dates_strictly_ordered": fold_dates_ordered,
        "counterfactual_cost_adjusted_ev_at_least_10bp": (
            aggregate_selected["cost_adjusted_terminal_proxy_ev_pct"] is not None
            and aggregate_selected["cost_adjusted_terminal_proxy_ev_pct"]
            >= HIERARCHICAL_ENTRY_QUALITY_GATE["minimum_cost_adjusted_ev_pct"]
        ),
        "counterfactual_clean_fast_recall_nonzero": (
            aggregate_population["clean_fast_count"] > 0
            and aggregate_selected["clean_fast_count"] > 0
        ),
        "actual_path_evidence_available": (
            actual_lane["economic_acceptance_eligible_count"] > 0
        ),
        "source_contract_conflicts_excluded": (
            source_contract.get("conflicting_duplicate_traces_excluded") is True
        ),
    }
    promotion_pass = all(promotion_checks.values())
    # This pass deliberately stops at a reviewed offline study.  A live family
    # projection belongs to the later, separately authorized integration step.
    return {
        "schema": HIERARCHICAL_ENTRY_QUALITY_SCHEMA,
        "target_date": target_date,
        "scope": {"stage": "entry", "venue": "KRX", "session": "KRX_REGULAR"},
        "label_contract": {
            "labels": sorted(ENTRY_QUALITY_LABELS),
            "clean_fast_positive_label": "CLEAN_FAST_PROFIT",
            "profitable_timing_failure_labels": [
                "PROFITABLE_BUT_LATE",
                "PROFIT_AFTER_DEEP_ADVERSE",
                "PROFIT_AFTER_SIDEWAYS",
            ],
            "censored_value_imputed": False,
        },
        "group_contract": {
            "schema": ENTRY_GROUP_OBSERVATION_SCHEMA,
            "symbol_specific_threshold_active": False,
            "symbol_residual_minimum_terminal_count": (
                HIERARCHICAL_ENTRY_QUALITY_GATE[
                    "symbol_residual_minimum_terminal_count"
                ]
            ),
            "symbol_residual_minimum_source_date_count": (
                HIERARCHICAL_ENTRY_QUALITY_GATE[
                    "symbol_residual_minimum_source_date_count"
                ]
            ),
            "symbol_residual_shrinkage": "n/(n+20)",
            "qualifying_symbol_count": len(qualifying_symbols),
            "qualifying_symbols": qualifying_symbols,
            "symbol_residual_active": False,
            "symbol_residual_activation_requires_reviewed_candidate": True,
            "missing_micro_imputed": False,
            "missing_group_dimensions_imputed": False,
            "group_complete_evaluable_count": len(group_complete_rows),
            "group_incomplete_evaluable_count": len(evaluable_rows)
            - len(group_complete_rows),
        },
        "source_population": {
            "accepted_unique_trace_count": len(source_rows),
            "entry_quality_evaluable_count": len(evaluable_rows),
            "entry_quality_censored_or_gap_count": len(source_rows)
            - len(evaluable_rows),
            "label_counts": dict(
                sorted(
                    Counter(
                        str(
                            row["entry_quality_path"].get("entry_quality_label")
                            or "INVALID_OR_MISSING"
                        )
                        for row in source_rows
                    ).items()
                )
            ),
            "source_rows_sha256": source_contract.get("accepted_rows_sha256"),
        },
        "walk_forward": {
            "folds": folds,
            "fold_count": len(folds),
            "fold_dates_strictly_ordered": fold_dates_ordered,
            "aggregate_evaluation_population": aggregate_population,
            "aggregate_selected_evaluation": aggregate_selected,
            "sealed_fold_reselection_allowed": False,
        },
        "actual_entry_lane": actual_lane,
        "market_path_opportunity_anchors": market_path_opportunities,
        "promotion_checks": promotion_checks,
        "promotion_pass": promotion_pass,
        "policy_candidate": None,
        "status": (
            "offline_evidence_pass_live_family_integration_not_authorized"
            if promotion_pass
            else (
                "actual_entry_path_economic_acceptance_gap"
                if actual_lane["economic_acceptance_eligible_count"] == 0
                else "hierarchical_walk_forward_gate_not_met"
            )
        ),
        "decision_authority": "offline_source_only_no_runtime_selection",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def entry_research_progress(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Bound offline search without borrowing the live exposure floor.

    Call only on the hash-verified, conflict-deduplicated cohort. A rotation
    explores another prompt; it is not rejection of an armed recheck policy.
    """
    all_dates = sorted(
        {str(row["source_date"]) for row in rows if row.get("source_date")}
    )
    dates = all_dates[-5:]
    cohort_parent_count = len(rows)
    rows = [row for row in rows if row.get("source_date") in dates]
    traces = sorted({str(row["decision_trace_id"]) for row in rows})
    symbols = {str(row["stock_code"]) for row in rows if row.get("stock_code")}
    exposed = sum(
        str(row.get("candidate_action") or "").upper() in EXPOSURE_ACTIONS
        or row.get("candidate_exposure_selected") is True
        for row in rows
    )
    armed = sum(row.get("candidate_probe_armed") is True for row in rows)
    cases = sorted(
        {
            str(row["decision_trace_id"])
            for row in rows
            if set(row.get("candidate_error_taxonomy") or [])
            & {
                "false_drop_small_profit_execution_proxy",
                "false_wait_small_profit_execution_proxy",
            }
        }
    )
    floor = len(dates) >= 5 and len(traces) >= 5 and len(symbols) >= 3
    rotate = bool(floor and exposed == 0 and cases)
    return {
        "schema": "entry_prompt_research_progress_v1",
        "status": (
            "bounded_offline_rotation_due"
            if rotate
            else (
                "pending_declared_research_window"
                if not floor
                else (
                    "no_observed_small_opportunity"
                    if not cases
                    else "participating_candidate_economic_review"
                )
            )
        ),
        "source_dates": dates,
        "window_policy": "last_five_valid_source_dates_within_exact_candidate_cohort",
        "cohort_exact_parent_count": cohort_parent_count,
        "exact_parent_ids": traces,
        "exact_parent_count": len(traces),
        "unique_symbol_count": len(symbols),
        "candidate_exposure_count": exposed,
        "candidate_probe_arm_count": armed,
        "probe_arm_is_execution": False,
        "recheck_terminal_status": "not_inferred_from_arm",
        "small_opportunity_case_ids": cases,
        "small_opportunity_basis": "execution_proxy_not_fee_tax_verified_net",
        "small_opportunity_cost_cases": cost_aware_opportunity_diagnostic(
            [row for row in rows if str(row["decision_trace_id"]) in cases]
        )["case_ledger"],
        "research_window": {"source_dates": 5, "exact_parents": 5, "symbols": 3},
        "research_window_pass": floor,
        "offline_rotation_due": rotate,
        "rotation_is_economic_rejection": False,
        "positive_net_profit_demonstrated": False,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "provider_budget_increase_allowed": False,
        "decision_authority": "bounded_offline_prompt_search_only",
    }


def cost_aware_opportunity_diagnostic(rows: list[dict[str, Any]]) -> dict[str, Any]:
    verified = []
    gaps: Counter[str] = Counter()
    case_ledger = []
    for row in rows:
        diagnostic = row.get("entry_cost_aware_opportunity")
        case = {
            "decision_trace_id": row.get("decision_trace_id"),
            "source_date": row.get("source_date"),
            "status": "source_unavailable",
            "cost_adjusted_end_return_pct": None,
            "counterfactual_net_target_first": None,
            "runtime_effect": False,
            "allowed_runtime_apply": False,
        }
        case_ledger.append(case)
        if not isinstance(diagnostic, dict):
            reason = (
                "legacy_no_cost_aware_diagnostic"
                if diagnostic is None
                else "invalid_cost_aware_diagnostic"
            )
            gaps[reason] += 1
            case["source_gap_reason"] = reason
            continue
        if (
            diagnostic.get("schema") == "entry_cost_aware_opportunity_v1"
            and diagnostic.get("status") == "verified_counterfactual_after_cost"
            and diagnostic.get("runtime_effect") is False
            and diagnostic.get("allowed_runtime_apply") is False
            and _number(diagnostic.get("cost_adjusted_end_return_pct")) is not None
            and type(diagnostic.get("counterfactual_net_target_first")) is bool
            and diagnostic.get("decision_trace_id") == row.get("decision_trace_id")
            and diagnostic.get("realized_net_pnl_krw") is None
            and all(
                _is_sha256(diagnostic.get(key))
                for key in (
                    "label_content_sha256",
                    "action_neutral_path_sha256",
                    "cost_profile_artifact_sha256",
                    "symbol_master_artifact_sha256",
                )
            )
        ):
            verified.append(diagnostic)
            case.update(
                status="verified_counterfactual_after_cost",
                cost_adjusted_end_return_pct=diagnostic["cost_adjusted_end_return_pct"],
                counterfactual_net_target_first=diagnostic[
                    "counterfactual_net_target_first"
                ],
                label_content_sha256=diagnostic["label_content_sha256"],
            )
        else:
            reason = diagnostic.get("source_gap_reason")
            reason = (
                reason
                if isinstance(reason, str) and reason
                else "invalid_cost_aware_diagnostic"
            )
            gaps[reason] += 1
            case["source_gap_reason"] = reason
        eligibility = diagnostic.get("producer_eligibility")
        if (
            isinstance(eligibility, dict)
            and eligibility.get("schema") == "entry_cost_label_source_eligibility_v1"
            and eligibility.get("decision_trace_id") == row.get("decision_trace_id")
            and eligibility.get("runtime_effect") is False
            and eligibility.get("allowed_runtime_apply") is False
            and _is_sha256(eligibility.get("source_bridge_content_sha256"))
            and _is_sha256(eligibility.get("source_evidence_sha256"))
        ):
            case["producer_eligibility"] = dict(eligibility)
    return {
        "schema": "entry_cost_aware_opportunity_summary_v1",
        "input_count": len(rows),
        "verified_counterfactual_count": len(verified),
        "net_target_first_count": sum(
            item["counterfactual_net_target_first"] for item in verified
        ),
        "source_gap_count": sum(gaps.values()),
        "source_gap_counts": dict(gaps),
        "case_ledger": case_ledger,
        "realized_net_pnl_krw": None,
        "runtime_apply_authority": False,
    }


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
    (
        cohort_key_version,
        effective_venue,
        session_bucket,
        market_data_route,
    ) = _unpack_cohort_route_scope(route_scope)
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
        "market_data_route": market_data_route or None,
        "cohort_key_version": cohort_key_version,
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
        "cost_aware_opportunity_diagnostic": (
            cost_aware_opportunity_diagnostic(values) if stage == "entry" else None
        ),
        "entry_research_progress": (
            entry_research_progress(values) if stage == "entry" else None
        ),
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
            "decision_quality_v2_14_1_timing_aware_setup_risk_adjudicator",
            "decision_quality_v2_14_2_balanced_setup_risk_adjudicator",
            "decision_quality_v2_15_1_timing_aware_bounded_recovery",
            "decision_quality_v2_15_2_balanced_bounded_recovery",
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
    for candidate in candidates:
        if (
            candidate.get("cohort_key_version") == ROUTE_SESSION_COHORT_KEY_VERSION
            and candidate.get("session_bucket") == DUAL_AFTERMARKET_SESSION
        ):
            gate = candidate.get("prompt_review_gate")
            gate = gate if isinstance(gate, dict) else {}
            checks = dict(gate.get("checks") or {})
            checks["dual_aftermarket_observe_only"] = False
            blockers = list(gate.get("blockers") or [])
            if "dual_aftermarket_observe_only" not in blockers:
                blockers.append("dual_aftermarket_observe_only")
            candidate.update(
                authority_state="OBSERVE_ONLY",
                review_classification="dual_aftermarket_observe_only",
                review_ready_for_prompt_candidate=False,
                prompt_review_gate={**gate, "checks": checks, "blockers": blockers},
                runtime_apply_authority=False,
            )
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
        "market_data_route",
        "cohort_key_version",
        "authority_state",
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
    mechanistic_source_rows, mechanistic_source_contract = _mechanistic_source_rows(
        report_root / PAIRED_SUBDIR, target_date=target_date
    )
    mechanistic_refinement = build_clean_baseline_mechanistic_refinement(
        report_root / PAIRED_SUBDIR,
        target_date=target_date,
        source_rows=mechanistic_source_rows,
        source_contract=mechanistic_source_contract,
    )
    mechanistic_flow_micro_audit = _flow_micro_confirmation_source_audit(
        report_root,
        target_date=target_date,
        source_rows=mechanistic_source_rows,
    )
    mechanistic_flow_groups = build_mechanistic_flow_group_study(
        target_date=target_date,
        source_rows=mechanistic_source_rows,
        source_contract=mechanistic_source_contract,
        micro_confirmation_audit=mechanistic_flow_micro_audit,
    )
    hierarchical_entry_quality = build_hierarchical_entry_quality_walk_forward(
        report_root / PAIRED_SUBDIR,
        target_date=target_date,
        source_rows=mechanistic_source_rows,
        source_contract=mechanistic_source_contract,
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
        "mechanistic_entry_refinement": {
            "schema": mechanistic_refinement["schema"],
            "policy_version": mechanistic_refinement["policy_version"],
            "status": mechanistic_refinement["status"],
            "promotion_pass": mechanistic_refinement["promotion_pass"],
            "policy_candidate": mechanistic_refinement["policy_candidate"],
            "decision_authority": "offline_source_only_no_runtime_selection",
            "runtime_effect": False,
            "allowed_runtime_apply": False,
        },
        "hierarchical_entry_quality": {
            "schema": hierarchical_entry_quality["schema"],
            "status": hierarchical_entry_quality["status"],
            "promotion_pass": hierarchical_entry_quality["promotion_pass"],
            "policy_candidate": hierarchical_entry_quality["policy_candidate"],
            "source_rows_sha256": hierarchical_entry_quality["source_population"][
                "source_rows_sha256"
            ],
            "decision_authority": "offline_source_only_no_runtime_selection",
            "runtime_effect": False,
            "allowed_runtime_apply": False,
        },
        "mechanistic_flow_groups": {
            "schema": mechanistic_flow_groups["schema"],
            "status": mechanistic_flow_groups["status"],
            "retrospective_supported_recheck_families": mechanistic_flow_groups[
                "retrospective_supported_recheck_families"
            ],
            "forward_accepted_recheck_families": mechanistic_flow_groups[
                "forward_accepted_recheck_families"
            ],
            "research_candidate": mechanistic_flow_groups["research_candidate"],
            "recheck_candidate": mechanistic_flow_groups["recheck_candidate"],
            "enter_policy_candidate": None,
            "micro_confirmation_source_audit": mechanistic_flow_groups[
                "micro_confirmation_source_audit"
            ],
            "source_rows_sha256": mechanistic_flow_groups["source_population"][
                "source_rows_sha256"
            ],
            "decision_authority": "offline_source_only_recheck_ranking_no_enter",
            "runtime_effect": False,
            "allowed_runtime_apply": False,
        },
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
            "candidate_contract_sha256+stage+cohort_key_version+effective_venue+"
            "session_bucket+market_data_route+"
            "decision_trace_id"
        ),
        "update_policy": (
            "append_hash_verified_cohort_isolated_exact_trace_daily_results_then_"
            "recompute_cumulative_action_outcome"
        ),
        "optimizer_handoff": optimizer_handoff,
        "ofi_smoothing_audit": build_ofi_smoothing_audit(pipeline_path),
        "ofi_action_outcome_calibration": ofi_action_outcome_calibration,
        "mechanistic_entry_refinement": mechanistic_refinement,
        "mechanistic_flow_groups": mechanistic_flow_groups,
        "hierarchical_entry_quality": hierarchical_entry_quality,
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
        from src.engine.scalping.mechanistic_entry_runtime_policy import publish

        publish(path, data_root=args.data_root)
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
