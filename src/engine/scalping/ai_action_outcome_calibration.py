"""Cumulative exact-trace action/outcome calibration and OFI attribution audit.

This producer replaces the legacy WATCHING numeric-score smoothing diagnostic.
It never changes a live score or action.  It accumulates mature paired replay
outcomes keyed by exact decision trace, then reports action transitions, EV,
error taxonomy, and OFI runtime postprocessor attribution coverage.
"""

from __future__ import annotations

import argparse
import gzip
import fcntl
import hashlib
from itertools import product
import json
import math
import os
import re
import tempfile
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from statistics import fmean
from typing import Any, Iterable, Mapping
from zoneinfo import ZoneInfo

from src.utils.jsonl_io import existing_or_gzip_path, iter_jsonl
from src.trading.order.tick_utils import get_tick_size
from src.engine.scalping.entry_setup_evidence import (
    MECHANISTIC_ENTRY_FLOW_OBSERVATION_SCHEMA,
    MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1,
    MECHANISTIC_FULL_POPULATION_POLICY_VERSION,
    MECHANISTIC_REFINEMENT_GATE,
    MECHANISTIC_HIERARCHY_SCHEMA,
    MECHANISTIC_PARAMETER_BOUNDS,
    HIERARCHICAL_ENTRY_QUALITY_GATE,
    validate_mechanistic_entry_threshold_policy,
    build_mechanistic_entry_flow_observation,
    mechanistic_entry_action_core,
    mechanistic_entry_policy_decision,
    _mechanistic_micro_pass,
    mechanistic_scope_supported,
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
MACHINE_DECISION_CASE_TABLE_SCHEMA = "mechanistic_entry_decision_case_table_v1"
MAIN_MECHANISTIC_EVALUATION_CONTRACT_VERSION = (
    "main_mechanistic_full_population_operating_scopes_v4"
)
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


def _main_mechanistic_input_fingerprint(
    data_root: Path, target_date: str, incumbent_date: str | None = None
) -> str:
    """Cheap retry fingerprint; large immutable JSONL inputs are never reread."""
    from src.engine.scalping.mechanistic_entry_runtime_policy import digest, load_effective

    def generation(path: Path) -> dict[str, Any]:
        # Compact finalization rewrites its small sealed projection even when
        # the logical input is unchanged.  Binding that file by inode/mtime
        # would force the expensive main evaluator to rerun on every wrapper
        # retry.  Large append-only sources remain stat-bound below.
        if (
            path.parent.name == "ai_entry_setup_paired_replay_batch"
            and path.name.endswith(".source.json")
        ):
            return {
                "path": str(path.resolve()),
                "content_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        stat = path.stat()
        return {
            "path": str(path.resolve()),
            "device": stat.st_dev,
            "inode": stat.st_ino,
            "size_bytes": stat.st_size,
            "mtime_ns": stat.st_mtime_ns,
            "ctime_ns": stat.st_ctime_ns,
        }

    candidates: set[Path] = set()
    patterns = (
        "ai_decision_payloads/*.jsonl*",
        "ai_decision_trace/*.jsonl*",
        "pipeline_events/pipeline_events_*.jsonl*",
        "report/ai_prompt_detailed_paired_replay/*.json",
        "report/micro_reversion_economic_reference/*.json*",
        "report/observation_source_quality_audit/*.json",
        "report/ai_entry_setup_paired_replay_batch/*.source.json",
        "report/entry_split_order_plan/entry_split_order_plan_*.json",
        "report/entry_cancel_wait_tuning/entry_cancel_wait_tuning_*.json",
    )
    for pattern in patterns:
        for path in data_root.glob(pattern):
            match = re.search(r"(\d{4}-\d{2}-\d{2})", path.name)
            if match and CLEAN_BASELINE_DATE <= match.group(1) <= target_date:
                candidates.add(path)
    pricing = data_root / "policy/micro_reversion/provider_pricing.json"
    if pricing.is_file():
        candidates.add(pricing)
    incumbent = load_effective(data_root=data_root, target_date=incumbent_date or target_date)
    from src.engine.scalping.strategy_owner_replay import entry_operating_model_identity
    code_paths = [
        Path(__file__),
        Path(__file__).with_name("ai_decision_quality.py"),
        Path(__file__).with_name("entry_setup_evidence.py"),
        Path(__file__).with_name("entry_strategy_policy.py"),
        Path(__file__).with_name("entry_candle_context.py"),
        Path(__file__).with_name("compact_auxiliary_paired_replay.py"),
        Path(__file__).with_name("strategy_owner_replay.py"),
        Path(__file__).with_name("entry_split_order_plan.py"),
    ]
    body = {
        "contract_version": MAIN_MECHANISTIC_EVALUATION_CONTRACT_VERSION,
        "operating_model_implementation_sha256": entry_operating_model_identity(),
        "target_date": target_date,
        "source_generations": [generation(path) for path in sorted(candidates)],
        "code_sha256": {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in code_paths
        },
        "incumbent_machine_policy_sha256": (
            digest(incumbent["machine_policy"]) if incumbent else None
        ),
        "incumbent_scope_policies_sha256": digest((incumbent or {}).get("scope_policies")),
        "common_grid": MECHANISTIC_COMMON_FEATURE_GRID,
        "refinement_gate": MECHANISTIC_REFINEMENT_GATE,
    }
    return _canonical_sha256(body)


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

    if "operating_comparison_input" in row:
        from src.engine.scalping import compact_auxiliary_paired_replay as compact
        source = row["operating_comparison_input"]
        arm = compact.owner_operating_arm(source.get("owner_replay") or {}, source)
        return arm.get("net_return_pct") * int(source.get("incumbent_verdict") == "PASS") if arm else None
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
    all_supported_cohorts: bool = False,
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
        report_cohort = (
            _normalized_venue(_as_dict(cohort_filter).get("effective_venue")),
            _normalized_session(_as_dict(cohort_filter).get("session_bucket")),
        )
        if not (
            isinstance(cohort_filter, dict)
            and (
                mechanistic_scope_supported(*report_cohort)
                if all_supported_cohorts
                else report_cohort == ("KRX", "KRX_REGULAR")
            )
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
            elif _normalized_stage(request.get("stage")) != "entry" or (
                not mechanistic_scope_supported(
                    _normalized_venue(request.get("effective_venue")),
                    _normalized_session(request.get("session_bucket")),
                )
                if all_supported_cohorts
                else (
                    _normalized_venue(request.get("effective_venue")) != "KRX"
                    or _normalized_session(request.get("session_bucket"))
                    != "KRX_REGULAR"
                )
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
                raw = request.get('exact_payload')
                if report_hash_verified and isinstance(raw, dict) and raw and 'strategy_raw_input' not in evidence:
                    from src.engine.scalping.entry_strategy_policy import digest as strategy_digest
                    evidence = dict(evidence)
                    evidence['strategy_raw_input'] = {**raw, 'strategy_observed_at': request['decision_ts']}
                    evidence['strategy_raw_sha256'] = strategy_digest(evidence['strategy_raw_input'])
                    evidence['evidence_sha256'] = _canonical_sha256({k:v for k,v in evidence.items() if k != 'evidence_sha256'})
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
                    "label_context": {
                        k: request.get(k)
                        for k in (
                            "stock_code",
                            "reference_price",
                            "reference_price_type",
                            "best_ask",
                            "effective_venue",
                            "session_bucket",
                            "market_data_route",
                            "broker_route",
                            "adverse_pct",
                            "adverse_price",
                        )
                    },
                    "entry_quality_contract_valid": entry_quality_contract_valid,
                    "comparison": {
                        "entry_cost_contract": comparison.get("entry_cost_contract"),
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


def _flow_micro_identity_mismatch_reason(
    flow_row: dict[str, Any], bridge_row: dict[str, Any]
) -> str | None:
    """Reject a trace collision across declared market-data dimensions."""

    evidence = _as_dict(bridge_row.get("tactical_micro_reversion_evidence_v1"))
    sidecar_context = _as_dict(
        _as_dict(bridge_row.get("ask_depletion_sidecar")).get("context")
    )
    flow_context = _as_dict(flow_row.get("label_context"))
    expected = {
        "symbol": str(flow_row.get("stock_code") or ""),
        "venue": _normalized_venue(
            flow_context.get("effective_venue") or flow_row.get("effective_venue")
        ),
        "session": _normalized_session(
            flow_context.get("session_bucket") or flow_row.get("session_bucket")
        ),
        "sequence_epoch": _as_dict(flow_row.get("mechanistic_flow_observation")).get(
            "sequence_epoch"
        ),
        "decision_ts": str(flow_row.get("decision_ts") or ""),
        "market_data_route": str(
            flow_context.get("market_data_route")
            or flow_row.get("market_data_route")
            or ""
        ).lower(),
        "source_bundle_sha256": str(flow_row.get("source_bundle_sha256") or ""),
    }
    observed = {
        "symbol": str(
            evidence.get("stock_code") or sidecar_context.get("symbol") or ""
        ),
        "venue": _normalized_venue(
            evidence.get("trace_effective_venue") or sidecar_context.get("venue")
        ),
        "session": _normalized_session(
            evidence.get("trace_session_bucket")
            or sidecar_context.get("session_bucket")
        ),
        "sequence_epoch": evidence.get("sequence_epoch")
        or sidecar_context.get("sequence_epoch"),
        "decision_ts": str(evidence.get("trace_decision_ts") or ""),
        "market_data_route": str(evidence.get("market_data_route") or "").lower(),
        "source_bundle_sha256": str(evidence.get("source_bundle_sha256") or ""),
    }
    for dimension in (
        "symbol",
        "venue",
        "session",
        "sequence_epoch",
        "decision_ts",
        "market_data_route",
        "source_bundle_sha256",
    ):
        if (
            expected[dimension] not in (None, "")
            and observed[dimension] != expected[dimension]
        ):
            return f"same_trace_{dimension}_mismatch"
    one_second = next(
        (
            item
            for item in _as_dict(bridge_row.get("ask_depletion_sidecar")).get(
                "horizons"
            )
            or []
            if isinstance(item, dict) and item.get("horizon_ms") == 1000
        ),
        None,
    )
    if (
        not isinstance(one_second, dict)
        or one_second.get("eligible_for_feature_ablation") is not True
    ):
        return "same_trace_fixed_price_1s_window_missing"
    return None


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
            mismatch = _flow_micro_identity_mismatch_reason(
                flow_by_trace[trace_id], row
            )
            if mismatch:
                rejection_counts[mismatch] += 1
                continue
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
    joined_horizon_features: list[dict[str, Any]] = []
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
            joined_horizon_features.append(
                {
                    "decision_trace_id": trace_id,
                    "source_date": joined["source_date"],
                    "horizon_ms": horizon.get("horizon_ms"),
                    "best_ask_depletion_velocity_qty_per_sec": _number(
                        horizon.get("best_ask_depletion_velocity_qty_per_sec")
                    ),
                    "aggressive_buy_trade_backed_ratio": _number(
                        horizon.get("aggressive_buy_trade_backed_ratio")
                    ),
                    "unexplained_or_cancel_like_depletion_ratio": _number(
                        horizon.get("unexplained_or_cancel_like_depletion_ratio")
                    ),
                    "refill_ratio": _number(horizon.get("refill_ratio")),
                    "bid_support": flow.get("bid_support"),
                    "rebound": flow.get("rebound"),
                    "missing_feature_imputed": False,
                    "runtime_candidate": False,
                }
            )

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
        "joined_horizon_features": joined_horizon_features,
        "diagnostic_candidate_count": len(joined_horizon_features),
        "economic_eligible_count": 0,
        "runtime_candidate_count": 0,
        "rejection_reason_counts": dict(sorted(rejection_counts.items())),
        "same_trace_join_required": True,
        "same_symbol_venue_session_epoch_required_when_declared": True,
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


def _machine_source_contract_valid(row):
    evidence = _as_dict(row.get("setup_evidence"))
    return not (
        row.get("source_provenance_verified") is not True
        or evidence.get("schema") != "entry_setup_evidence_v1"
        or not (row.get("source_report_hash_verified") is True
                or row.get("machine_observation_hash_verified") is True)
        or evidence.get("evidence_sha256") != _canonical_sha256({
            k: v for k, v in evidence.items() if k != "evidence_sha256"
        })
        or _as_dict(evidence.get("source_quality")).get("status") != "fresh_consistent"
        or any(evidence.get(k) is not expected for k, expected in (
            ("runtime_effect", False), ("allowed_runtime_apply", False),
            ("actual_order_submitted", False), ("broker_order_forbidden", True),
        ))
    )


def _common_refinement_population(
    paired_rows: list[dict], natural_rows: list[dict], *,
    target_date: str, source_receipt: dict, paired_contract: dict,
    natural_conflicting_attempt_identity_count: int = 0,
    natural_conflicting_evaluation_keys: list[str] | None = None,
    cohort: tuple[str, str] = ("KRX", "KRX_REGULAR"),
    operating_projection: dict | None = None,
    allow_attempt_identity_fallback: bool = False,
    retain_unevaluated_machine_rows: bool = False,
) -> tuple[list[dict], dict]:
    """Union existing exact CF lanes before selection; no fills/AI required.

    A row from the natural loader still needs #74's machine-specific receipt.
    Full costs and source-time identity remain mandatory. Exclusions preserve
    censored paths rather than manufacturing zero returns or synthetic AI.
    """
    excluded, accepted, seen, conflicted = Counter(), {}, {}, set()
    trace_keys = {}
    if not mechanistic_scope_supported(*cohort):
        raise ValueError("refinement_population_cohort_unsupported")
    gate = _as_dict(source_receipt.get("machine_terminal_tuning_gate"))
    excluded_keys = set(gate.get("excluded_evaluation_keys") or []) | set(
        gate.get("pending_evaluation_keys") or []
    )
    def evaluation_key(row):
        return _machine_evaluation_key(row, allow_attempt_fallback=allow_attempt_identity_fallback)
    observed_conflict_keys = _machine_conflicting_evaluation_keys(natural_rows, allow_attempt_fallback=allow_attempt_identity_fallback)
    conflict_manifest_valid = (
        natural_conflicting_evaluation_keys is None
        or (
            isinstance(natural_conflicting_evaluation_keys, list)
            and all(isinstance(key, str) and key for key in natural_conflicting_evaluation_keys)
            and len(set(natural_conflicting_evaluation_keys)) == len(natural_conflicting_evaluation_keys)
        )
    )
    # The direct caller can omit a manifest when no external conflicts were
    # reported: independently localize its input. A nonzero external count
    # without proven locations remains a global natural-lane blocker.
    conflict_keys = (
        observed_conflict_keys
        if natural_conflicting_evaluation_keys is None
        and natural_conflicting_attempt_identity_count == 0
        else set(natural_conflicting_evaluation_keys or [])
        if conflict_manifest_valid else set()
    )
    effective_conflict_count = (
        len(observed_conflict_keys)
        if natural_conflicting_evaluation_keys is None
        and natural_conflicting_attempt_identity_count == 0
        else natural_conflicting_attempt_identity_count
    )
    conflict_locations_complete = (
        type(natural_conflicting_attempt_identity_count) is int
        and natural_conflicting_attempt_identity_count >= 0
        and conflict_manifest_valid
        and type(effective_conflict_count) is int
        and len(conflict_keys) == effective_conflict_count
        and all(isinstance(key, str) and key for key in conflict_keys)
        and conflict_keys == observed_conflict_keys
    )
    natural_allowed = (
        source_receipt.get("target_date") == target_date
        and source_receipt.get("machine_threshold_tuning_input_allowed") is True
        and conflict_locations_complete
    )
    for lane, originals in (("paired", paired_rows), ("natural", natural_rows)):
        for original in originals:
            row = dict(original)
            operating_source = None
            if operating_projection is not None:
                from src.engine.scalping import compact_auxiliary_paired_replay as compact
                matches = [r for r in operating_projection.get("rows") or []
                           if r.get("evaluation_attempt_id") == row.get("evaluation_attempt_id")]
                # Compact replay is an optional downstream-economic enrichment.
                # It must never redefine the machine counterfactual population:
                # BLOCK/RECHECK and paired lanes are valid machine research rows
                # even though no compact provider call was made for them.
                if (
                    lane == "natural"
                    and compact.valid(operating_projection)
                    and len(matches) == 1
                ):
                    candidate_source = matches[0]
                    if (
                        not candidate_source.get("exclusion_reason")
                        and all(
                            candidate_source.get(k) == row.get(k)
                            for k in (
                                "stock_code",
                                "scanner_promotion_id",
                                "effective_venue",
                                "session_bucket",
                                "source_date",
                            )
                        )
                        and ((candidate_source.get("incumbent_verdict") in {"PASS", "VETO"}
                              and compact.owner_operating_arm(candidate_source.get("owner_replay") or {}, candidate_source))
                             or _machine_nonentry_seed(candidate_source))
                    ):
                        operating_source = candidate_source
                        row["operating_comparison_input"] = operating_source
                        row["operating_model_validation"] = (
                            candidate_source.get("machine_owner_model_validation")
                            or operating_projection.get("owner_execution_model_validation") or {}
                        )
                        row["operating_runtime_cost_receipt"] = (
                            candidate_source.get("machine_runtime_cost_receipt")
                            or operating_projection.get("runtime_inference_cost_receipt") or {}
                        )
            day = str(row.get("source_date") or "")
            evidence = _as_dict(row.get("setup_evidence"))
            parts = _as_dict(_as_dict(row.get("entry_group_observation")).get("key_parts"))
            if (parts.get("venue"), parts.get("session_bucket")) != cohort:
                excluded["different_cohort"] += 1
                continue
            if not CLEAN_BASELINE_DATE <= day <= target_date or (
                _kst_date_from_aware_timestamp(row.get("decision_ts")) != day
            ):
                excluded["decision_date_invalid"] += 1
                continue
            if not _machine_source_contract_valid(row):
                excluded["source_contract_invalid"] += 1
                continue
            if lane == "natural" and (
                not natural_allowed
                or (row.get("effective_venue"), row.get("session_bucket")) != cohort
                or not _is_sha256(row.get("bundle_sha256"))
                or evaluation_key(row) in excluded_keys
                or not all(str(row.get(key) or "").strip() for key in (
                    "evaluation_attempt_id", "stock_code",
                    "effective_venue", "session_bucket", "bundle_sha256",
                ))
                or (not allow_attempt_identity_fallback and not str(row.get("scanner_promotion_id") or "").strip())
            ):
                excluded["natural_machine_receipt_or_identity_invalid"] += 1
                continue
            if evaluation_key(row) in observed_conflict_keys:
                excluded["conflicting_exact_attempt"] += 1
                continue
            comparison = _as_dict(row.get("comparison"))
            if not retain_unevaluated_machine_rows and operating_source is None and row.get("entry_quality_contract_valid") is not True:
                excluded["outcome_contract_invalid"] += 1
                continue
            cost = _as_dict(comparison.get("entry_cost_contract"))
            full_cost = _full_entry_cost_pct(cost, source_date=day)
            if not retain_unevaluated_machine_rows and operating_source is None and (
                full_cost is None
                or (cost.get("effective_venue"), cost.get("session_bucket")) != cohort
                or _number(comparison.get("conservative_execution_cost_pct")) is None
                or not math.isclose(float(comparison["conservative_execution_cost_pct"]), full_cost,
                                    rel_tol=0, abs_tol=1e-9)
            ):
                excluded["full_cost_missing_or_mismatched"] += 1
                continue
            trace = str(row.get("decision_trace_id") or "").strip()
            if not trace or not str(row.get("stock_code") or "").strip():
                excluded["trace_or_symbol_missing"] += 1
                continue
            key = ("natural", evaluation_key(row)) if lane == "natural" else ("paired", trace)
            # One trace must not contribute twice merely because both the
            # paired replay and natural machine materialization consumed it.
            # Exact conflicting receipts are quarantined, never time-joined.
            key = trace_keys.setdefault(trace, key)
            fingerprint = _canonical_sha256({
                "evidence": evidence, "comparison": comparison,
                "decision_ts": row["decision_ts"],
                "operating_source_sha256": _canonical_sha256(operating_source) if operating_source else None,
            })
            if key in conflicted:
                excluded["conflicting_duplicate"] += 1
                continue
            if key in seen:
                if seen[key] != fingerprint:
                    conflicted.add(key)
                    removed = accepted.pop(key, None)
                    excluded["conflicting_duplicate"] += 1 + int(removed is not None)
                else:
                    excluded["identical_duplicate"] += 1
                continue
            seen[key] = fingerprint
            row.update(
                fingerprint=fingerprint,
                refinement_source_lane=lane,
                micro_recovery_observed=isinstance(evidence.get("micro_recovery_observation"), dict),
            )
            accepted[key] = row
    # The provider trace is an explicit alias of the pre-AI machine attempt,
    # not a second opportunity. Prefer the exact natural machine boundary;
    # never transplant the paired SELL/AI result onto its operating path.
    natural_aliases = {(r.get("source_date"), r.get("stock_code"), r.get("ai_decision_trace_id"))
        for r in accepted.values() if r.get("refinement_source_lane") == "natural"
        and r.get("ai_decision_trace_id")}
    for key, row in list(accepted.items()):
        if (row.get("refinement_source_lane") == "paired"
            and (row["source_date"], row["stock_code"], row["decision_trace_id"]) in natural_aliases):
            del accepted[key]
            excluded["paired_alias_of_natural_machine_attempt"] += 1
    result = sorted(accepted.values(), key=lambda r: (r["source_date"], r["decision_trace_id"]))
    sequence_groups = defaultdict(list)
    for row in result:
        key = (row.get("source_date"), row.get("stock_code"), row.get("scanner_promotion_id"))
        sequence_groups[key].append(row)
    for key, rows in sequence_groups.items():
        originals = [r for r in natural_rows if
            (r.get("source_date"), r.get("stock_code"), r.get("scanner_promotion_id")) == key]
        if natural_allowed and all(key):
            for row in rows:
                row['machine_sequence_expected_count'] = len(originals)
        if natural_allowed and len(originals) == len(rows) and all(key):
            members = sorted(r["decision_trace_id"] for r in rows)
            for row in rows:
                row["machine_sequence_members"] = members
    return result, {
        "schema": "machine_common_refinement_population_v1",
        "cohort": list(cohort),
        "paired_source_contract": paired_contract,
        "natural_machine_source_receipt": source_receipt,
        "natural_conflicting_attempt_identity_count": natural_conflicting_attempt_identity_count,
        "effective_natural_conflicting_attempt_identity_count": effective_conflict_count,
        "natural_conflicting_evaluation_keys": sorted(conflict_keys),
        "natural_conflict_locations_complete": conflict_locations_complete,
        "input_lane_counts": {"paired": len(paired_rows), "natural": len(natural_rows)},
        "accepted_lane_counts": dict(Counter(r["refinement_source_lane"] for r in result)),
        "accepted_unique_trace_count": len(result),
        "attempt_identity_fallback_allowed": allow_attempt_identity_fallback,
        "attempt_identity_fallback_count": sum(not bool(r.get("scanner_promotion_id")) for r in result),
        "accepted_source_dates": sorted({r["source_date"] for r in result}),
        "accepted_rows_sha256": _canonical_sha256([
            {"decision_trace_id": r["decision_trace_id"], "fingerprint": r["fingerprint"]}
            for r in result
        ]),
        "row_exclusion_reason_counts": dict(excluded),
        "operating_economic_enrichment_count": sum(
            "operating_comparison_input" in row for row in result
        ),
        "machine_population_independent_of_compact_projection": True,
        "input_row_disposition_complete": (
            len(result) + sum(excluded.values()) == len(paired_rows) + len(natural_rows)
        ),
        "conflicting_duplicate_traces_excluded": True,
        "actual_fills_or_ai_calls_required": False,
        "missing_cost_or_outcome_imputed": False,
    }


def _current_structure_population(rows, contract):
    """Isolate current producer semantics; retain the original case-table history."""
    from src.engine.scalping.entry_candle_context import LOCAL_BREAKOUT_VERSION

    counts = Counter(r["setup_evidence"].get("structure_contract_version")
                     or "legacy_session_high_v1" for r in rows)
    selected = [r for r in rows if r["setup_evidence"].get("structure_contract_version")
                == LOCAL_BREAKOUT_VERSION]
    excluded = dict(contract.get("row_exclusion_reason_counts") or {})
    if len(selected) != len(rows):
        excluded["structure_contract_version_mismatch"] = len(rows) - len(selected)
    return selected, {
        **contract,
        "structure_contract_version": LOCAL_BREAKOUT_VERSION,
        "structure_contract_input_counts": dict(counts),
        "structure_contract_population_count": len(rows),
        "row_exclusion_reason_counts": excluded,
        "accepted_lane_counts": dict(Counter(r["refinement_source_lane"] for r in selected)),
        "accepted_unique_trace_count": len(selected),
        "accepted_source_dates": sorted({r["source_date"] for r in selected}),
        "accepted_rows_sha256": _canonical_sha256([
            {"decision_trace_id": r["decision_trace_id"], "fingerprint": r["fingerprint"]}
            for r in selected]),
        "operating_economic_enrichment_count": sum("operating_comparison_input" in r for r in selected),
    }


def _mechanistic_threshold_policy(policy, parent_policy=None, *, publication=False):
    threshold_policy = json.loads(json.dumps(
        parent_policy or MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1
    ))
    if any(threshold_policy["thresholds"].get(k) != v for k, v in policy.items()):
        threshold_policy.pop("hierarchy", None)
    threshold_policy["version"] = (
        MECHANISTIC_FULL_POPULATION_POLICY_VERSION
        if threshold_policy.get("version") == MECHANISTIC_FULL_POPULATION_POLICY_VERSION
        else MECHANISTIC_REFINEMENT_POLICY_VERSION
    )
    # A live strategy parent may intentionally use the relaxed strategy
    # selection floor (EV 0 / one symbol). The offline refinement and
    # full-population versions have a stricter schema contract, and the action
    # evaluator validates that contract even though it does not use these
    # selection fields. Normalize the copied parent before candidate replay.
    selection = threshold_policy.setdefault("postclose_selection", {})
    selection["minimum_cost_adjusted_ev_pct"] = max(
        float(selection.get("minimum_cost_adjusted_ev_pct", 0.0)),
        MECHANISTIC_REFINEMENT_GATE["minimum_cost_adjusted_ev_pct"],
    )
    selection["minimum_unique_symbol_count"] = max(
        int(selection.get("minimum_unique_symbol_count", 0)),
        3,
    )
    threshold_policy["thresholds"].update(policy)
    if publication:
        threshold_policy.pop("hierarchy", None)
        threshold_policy["version"] = MECHANISTIC_FULL_POPULATION_POLICY_VERSION
        threshold_policy["postclose_selection"]["minimum_cost_adjusted_ev_pct"] = MECHANISTIC_REFINEMENT_GATE["minimum_cost_adjusted_ev_pct"]
    return threshold_policy


def _mechanistic_policy_rows(
    rows: Iterable[dict[str, Any]], policy: dict[str, Any],
    *, parent_policy: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    selected = []
    threshold_policy = _mechanistic_threshold_policy(policy, parent_policy)
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


def _machine_nonentry_seed(source):
    """Validate a producer-owned no-AI anchor; it cannot authorize an entry."""
    from src.engine.scalping import strategy_owner_replay as owner
    replay = source.get("owner_replay") or {}
    seed = replay.get("seed") or {}
    context = seed.get("operating_contract") or {}
    if (replay.get("status") == "nonentry_plan_only"
        and replay.get("auxiliary_called") is False
        and replay.get("replay_sha256") == _canonical_sha256({k:v for k,v in replay.items() if k != "replay_sha256"})
        and owner._entry_seed_valid(seed)
        and seed.get("observed_machine_action") in {"BLOCK", "RECHECK"}
        and context.get("sha256") == _canonical_sha256({k:v for k,v in context.items() if k != "sha256"})
        and (_number(context.get("budget_krw")) or 0) > 0
        and all(source.get(k) == seed.get(k) for k in
            ("evaluation_attempt_id", "source_date", "stock_code", "scanner_promotion_id", "effective_venue", "session_bucket"))):
        return seed
    return None


def _machine_sequence_operating_metrics(population, selected_ids, candidate_policy=None, *, joint_actions=False):
    """Replay exact promotion sequences with frozen quantities and shared cash.

    This is a conditional, fixed-capital experiment, not an account backtest.
    Later verified symbol caps do not change initial capital. External account
    flows require their own witnesses. Every chosen exit is its own owner CF.
    """
    from copy import deepcopy
    from src.engine.scalping import compact_auxiliary_paired_replay as compact
    from src.engine.scalping import entry_split_order_plan as split
    empty = dict(status="source_gap", blocker=None, incumbent=None, candidate=None,
        robust_paired_delta_ev_lower_bound_pct=None, daily_net_profit_delta_krw=None,
        portfolio_daily_net_delta_krw=None, owner="machine_owner_sequence_replay",
        closure_test="complete_promotion_sequence_exact_plan_prior_model_and_frozen_cash_replay")
    groups, seen = defaultdict(list), {}
    try:
        for row in population:
            source = row.get("operating_comparison_input") or {}
            replay = source.get("owner_replay") or {}
            arm = compact.owner_operating_arm(replay, source)
            model = row.get("operating_model_validation") or {}
            plan_only = _machine_nonentry_seed(source)
            if not plan_only and (not arm or not compact.owner_model_scope_valid(model, source)):
                raise ValueError("exact_source_date_operating_model_unverified")
            if arm and any(not compact.finite(arm.get(k)) or arm[k] < 0
                for k in ('capital_krw_minutes', 'reserve_krw_minutes')):
                raise ValueError('owner_capital_or_reserve_measurement_invalid')
            if not plan_only and row.get("operating_runtime_cost_receipt", {}).get("delta_krw") != 0:
                raise ValueError("sequence_nonzero_inference_cost_timeline_unbound")
            seed = replay["seed"]
            proof = None if plan_only else next(p for p in model["validated_scopes"]
                if p["scope_sha256"] == split._entry_operating_scope(seed)
                and compact.owner_model_scope_valid({"validated_scopes": [p]}, source))
            budget = seed["operating_contract"]["budget_krw"] if plan_only else arm["budget_krw"]
            group = (seed["source_date"], seed["stock_code"], seed["scanner_promotion_id"])
            if not all(group):
                raise ValueError("sequence_episode_identity_missing")
            stamp = datetime.fromisoformat(seed["observed_at"])
            ended = None if plan_only else datetime.fromisoformat(arm["modeled_exit_at"])
            if stamp.tzinfo is None or (ended is not None and (ended.tzinfo is None or ended <= stamp)):
                raise ValueError("sequence_owner_clock_invalid")
            old = row["comparison"].get("incumbent_machine_action") or (
                "ENTER_NOW" if row["comparison"].get("control_action") == "BUY" else "BLOCK")
            new = (row['joint_candidate_action'] if joint_actions else mechanistic_entry_policy_decision(row["setup_evidence"], policy=candidate_policy)["action"]
                if candidate_policy is not None else "ENTER_NOW" if row["decision_trace_id"] in selected_ids else "BLOCK")
            if old not in {"ENTER_NOW", "BLOCK", "RECHECK"} or new not in {"ENTER_NOW", "BLOCK", "RECHECK"}:
                raise ValueError("sequence_machine_action_invalid")
            signature = _canonical_sha256([seed["seed_sha256"], old, new, source.get("incumbent_verdict")])
            key = (*group, stamp)
            if key in seen:
                if seen[key] != signature:
                    raise ValueError("sequence_same_clock_conflict")
                continue
            seen[key] = signature
            reserve = sum(leg["qty"] * leg["price"] for leg in seed["legs"])
            if not 0 < reserve <= budget:
                raise ValueError("sequence_frozen_reserve_missing")
            groups[group].append(dict(row=row, seed=seed, arm=arm, old=old, new=new, budget=budget,
                start=stamp, end=ended, reserve=reserve, verdict=source.get("incumbent_verdict"),
                clock_error=0. if plan_only else proof['tolerance']['receipt_clock_error_sec'],
                error=0. if plan_only else max(proof["optimistic_net_error_budget_pct"], proof["tolerance"]["net_error_budget_pct"])))
        if not groups:
            raise ValueError("sequence_population_empty")
        from src.engine.scalping.strategy_owner_replay import entry_conditional_capital_envelope
        day_seeds = defaultdict(list)
        for group, anchors in groups.items():
            day_seeds[group[0]].extend(a['seed'] for a in anchors)
        envelopes = {day: entry_conditional_capital_envelope(seeds) for day, seeds in day_seeds.items()}
        experiments, day_budgets = [], {day: value['initial_budget_krw'] for day, value in envelopes.items()}
        for group, anchors in sorted(groups.items()):
            anchors.sort(key=lambda a: a["start"])
            budget = day_budgets[group[0]]
            # Each reevaluation owns a new frozen quantity. Both policies use
            # that same attempt's quantity; a prior RECHECK is not a sizing lock.
            day = group[0]
            choices = []
            for side in ("old", "new"):
                choice = None
                for anchor in anchors:
                    action = anchor[side]
                    if action == "RECHECK":
                        # The census is created by the population producer; a
                        # calibration/holdout slice cannot close half an episode.
                        members = anchor["row"].get("machine_sequence_members")
                        if members != sorted(a["row"]["decision_trace_id"] for a in anchors):
                            raise ValueError("recheck_sequence_capture_incomplete")
                        continue
                    if action == "ENTER_NOW":
                        if anchor["arm"] is None or anchor["verdict"] not in {"PASS", "VETO"}:
                            raise ValueError("frozen_auxiliary_verdict_missing")
                        choice = anchor if anchor["verdict"] == "PASS" else None
                    break
                else:
                    last = anchors[-1]
                    terminal = (last['row']['operating_comparison_input']['owner_replay'].get('machine_watch_terminal') or {})
                    lifetime = (last['seed'].get('operating_contract') or {}).get('watch_lifetime_contract') or {}
                    if not (terminal.get('owner') == lifetime.get('owner') and terminal.get('owner')
                        and terminal.get('scanner_promotion_id') == group[2]
                        and terminal.get('deadline_epoch') == lifetime.get('deadline_epoch')
                        and terminal.get('terminal_epoch', 0) > terminal.get('deadline_epoch', float('inf')) >= last['start'].timestamp()):
                        raise ValueError("recheck_terminal_pending")
                choices.append(choice)
            experiments.append(dict(key=group, budget=budget, choices=choices))
        outputs = {(scenario, side): {} for scenario in ("base", "stress") for side in (0, 1)}
        rejected = [0, 0]
        peak_committed = {name: {} for name in ('incumbent','candidate')}
        for scenario in ("base", "stress"):
            for side in (0, 1):
                for day, budget in sorted(day_budgets.items()):
                    pending, cash, uncertainty = [], budget, 0.
                    capital_events = []
                    orders = sorted(((e["choices"][side], e) for e in experiments
                        if e["key"][0] == day and e["choices"][side] is not None),
                        key=lambda item: (item[0]["start"], item[1]["key"]))
                    for anchor, experiment in orders:
                        active = []
                        timing_uncertainty = 0.
                        for end, reserved, pnl, error, symbol, releases, clock_error in pending:
                            if clock_error and abs((end-anchor['start']).total_seconds()) <= clock_error:
                                timing_uncertainty += reserved
                            remaining_releases = []
                            for release in releases:
                                if clock_error and abs((release[0]-anchor['start']).total_seconds()) <= clock_error:
                                    timing_uncertainty += release[1]
                                if release[0] <= anchor["start"]:
                                    cash += release[1]
                                    reserved -= release[1]
                                else:
                                    remaining_releases.append(release)
                            if end <= anchor["start"]:
                                cash += reserved + pnl
                                uncertainty += error
                            else:
                                active.append((end, reserved, pnl, error, symbol, remaining_releases, clock_error))
                        pending = active
                        cash = min(budget - sum(item[1] for item in active), cash)
                        # Existing held-symbol guard; a promotion reset does not
                        # authorize another initial position while custody is open.
                        if any(item[4] == experiment["key"][1] for item in active):
                            if scenario == "base": rejected[side] += 1
                            continue
                        if uncertainty + timing_uncertainty and abs(cash-anchor["reserve"]) <= uncertainty + timing_uncertainty:
                            raise ValueError("model_error_can_change_capital_admission")
                        if anchor["reserve"] > cash:
                            if scenario == "base": rejected[side] += 1
                            continue
                        cash -= anchor["reserve"]
                        capital_events.append((anchor['start'], anchor['reserve']))
                        pnl = anchor["arm"]["net_pnl_krw" if scenario == "base" else "stress_net_pnl_krw"]
                        releases = []
                        path = anchor["arm"].get("cash_commitment_path")
                        if path is not None:
                            if (path.get('sha256') != _canonical_sha256({k:v for k,v in path.items() if k != 'sha256'})
                                or path.get('schema') != 'entry_operating_cash_commitment_v1'
                                or path.get('seed_sha256') != anchor['seed']['seed_sha256']
                                or path.get('initial_reserve_krw') != anchor['reserve']):
                                raise ValueError('operating_cash_path_binding_invalid')
                            released = 0.
                            owner_exits = 0
                            previous_clock = anchor['start']
                            for event in path['events']:
                                at = datetime.fromisoformat(event['at'])
                                amount = event['principal_release_krw']
                                if (not compact.finite(amount) or amount < 0 or at.tzinfo is None
                                    or not previous_clock <= at <= anchor['end']
                                    or event['kind'] not in {'fill_transfer','cancel_confirmed','owner_exit'}):
                                    raise ValueError('operating_cash_path_event_invalid')
                                previous_clock = at
                                released += amount
                                capital_events.append((at, -amount))
                                if event['kind'] != 'owner_exit':
                                    releases.append((at, amount))
                                else:
                                    owner_exits += 1
                                    if at != anchor['end']:
                                        raise ValueError('operating_cash_path_exit_clock_invalid')
                            if abs(released-anchor['reserve']) > 1e-8 or owner_exits != 1:
                                raise ValueError('operating_cash_path_conservation_failed')
                        else:
                            capital_events.append((anchor['end'], -anchor['reserve']))
                        pending.append((anchor["end"], anchor["reserve"], pnl,
                            2 * anchor["error"] * anchor['budget'] / 100, experiment["key"][1], releases, anchor['clock_error']))
                        outputs[scenario, side][experiment["key"]] = anchor
                    if scenario == 'base':
                        balances = defaultdict(float)
                        for at, amount in capital_events:
                            balances[at] += amount
                        committed = peak = 0.
                        for at in sorted(balances):
                            committed += balances[at]
                            peak = max(peak, committed)
                        peak_committed[('incumbent','candidate')[side]][day] = peak
        rows, bounds, daily = [], [], defaultdict(lambda: [0., 0.])
        zero = dict(net_pnl_krw=0., stress_net_pnl_krw=0., capital_krw_minutes=0.,
                    reserve_krw_minutes=0., fill_participation_rate=0.)
        for experiment in experiments:
            arms = {}
            for side, name in enumerate(("incumbent", "candidate")):
                anchor = outputs["base", side].get(experiment["key"])
                arms[name] = deepcopy(anchor["arm"]) if anchor else dict(zero)
                if anchor:
                    # Monetary outcomes retain their native cap for provenance;
                    # portfolio return uses the identical INITIAL capital.
                    arms[name]['attempt_budget_krw'] = anchor['budget']
                    arms[name]['net_return_pct'] = arms[name]['net_pnl_krw'] / experiment['budget'] * 100
                    arms[name]['stress_net_return_pct'] = arms[name]['stress_net_pnl_krw'] / experiment['budget'] * 100
                daily[experiment["key"][0]][side] += arms[name]["net_pnl_krw"]
            rows.append(dict(budget_krw=experiment["budget"], arms=arms))
            scenario_bounds = []
            for scenario in ("base", "stress"):
                chosen = [outputs[scenario, side].get(experiment["key"]) for side in (0, 1)]
                field = "net_pnl_krw" if scenario == "base" else "stress_net_pnl_krw"
                pnl = [a["arm"][field] if a else 0. for a in chosen]
                penalty = (0. if chosen[0] is chosen[1] else
                           sum(2 * a["error"] * a['budget'] / experiment['budget'] for a in chosen if a is not None))
                scenario_bounds.append((pnl[1]-pnl[0]) / experiment["budget"] * 100 - penalty)
            bounds.append(min(scenario_bounds))
        deltas = {day: v[1]-v[0] for day,v in sorted(daily.items())}
        return dict(status="supported_operating_comparison", blocker=None,
            incumbent=split._economic_metrics(rows, "incumbent"), candidate=split._economic_metrics(rows, "candidate"),
            robust_paired_delta_ev_lower_bound_pct=fmean(bounds), pair_lower_bounds_pct=bounds,
            lower_bound_method="episode_minimum_base_stress_minus_selected_owner_empirical_error",
            daily_net_profit_delta_krw=fmean(deltas.values()), portfolio_daily_net_delta_krw=deltas,
            economic_episode_count=len(rows), deduplicated_attempt_count=len(population)-len(seen),
            capital_rejection_counts=dict(incumbent=rejected[0], candidate=rejected[1]),
            capital_envelopes=envelopes,
            peak_committed_capital_krw_by_day=peak_committed,
            portfolio_allocation_contract="same_frozen_cash_full_quantity_chronological_no_profit_reinvestment",
            counterfactual_not_realized_pnl=True)
    except (ValueError, KeyError, TypeError, OverflowError) as exc:
        return {**empty, "blocker": str(exc)}


def machine_selection_economics(metrics, paired, *, full_population):
    """Use owner operating economics for live full-population selection.

    Terminal price labels remain diagnostics and legacy research evidence;
    they cannot replace missing operating costs, exits, or model validation.
    """
    if not full_population:
        return (_number(metrics.get("cost_adjusted_terminal_proxy_ev_pct")),
                _number(paired.get("paired_terminal_proxy_delta_pct")))
    operating = _as_dict(paired.get("operating_economic_comparison"))
    if (paired.get("downstream_operating_evidence_complete") is not True
        or operating.get("status") != "supported_operating_comparison"):
        return None, None
    incumbent = _number(_as_dict(operating.get("incumbent")).get("ev_pct"))
    candidate = _number(_as_dict(operating.get("candidate")).get("ev_pct"))
    return candidate, (candidate-incumbent if candidate is not None and incumbent is not None else None)


def _mechanistic_paired_population_metrics(
    population: list[dict[str, Any]], selected: list[dict[str, Any]],
    *, candidate_policy: dict | None = None,
) -> dict[str, Any]:
    selected_trace_ids = {row["decision_trace_id"] for row in selected}
    deltas = []
    candidate_values = []
    incumbent_values = []
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
        candidate_values.append(mechanistic_value)
        incumbent_values.append(control_value)
        deltas.append(mechanistic_value - control_value)
    old_actions = {row["decision_trace_id"]: row["comparison"].get("incumbent_machine_action") or
        ("ENTER_NOW" if row["comparison"].get("control_action") == "BUY" else "BLOCK") for row in population}
    new_actions = {row["decision_trace_id"]: (mechanistic_entry_policy_decision(
        row["setup_evidence"], policy=candidate_policy)["action"] if candidate_policy is not None
        else "ENTER_NOW" if row["decision_trace_id"] in selected_trace_ids else "BLOCK") for row in population}
    changed = [row for row in population if old_actions[row["decision_trace_id"]] != new_actions[row["decision_trace_id"]]]
    recheck_ids = {key for key in old_actions if "RECHECK" in {old_actions[key], new_actions[key]}}
    operating_rows = [row for row in population if "operating_comparison_input" in row]
    operating = (_machine_sequence_operating_metrics(operating_rows, selected_trace_ids, candidate_policy)
                 if operating_rows else None)
    sequence_supported = bool(operating and operating.get("status") == "supported_operating_comparison")
    operating_ids = {row["decision_trace_id"] for row in operating_rows} if sequence_supported else set()
    unsupported_changed = [row for row in changed if row["decision_trace_id"] not in operating_ids]
    if operating is not None and len(operating_rows) != len(population):
        operating = {**operating, "daily_net_profit_delta_krw": None,
            "portfolio_daily_net_delta_krw": None,
            "daily_net_profit_status": "operating_population_incomplete_or_model_unsupported"}
    complete = len(deltas) == terminal_evaluable_count
    downstream_complete = bool(
        population and len(operating_rows) == len(population)
        and operating is not None
        and operating.get("status") == "supported_operating_comparison"
        and operating.get("daily_net_profit_delta_krw") is not None
    )
    operating_promotion_pass = (
        operating is not None
        and downstream_complete
        and operating.get("status") == "supported_operating_comparison"
        and operating.get("robust_paired_delta_ev_lower_bound_pct") is not None
        and operating["robust_paired_delta_ev_lower_bound_pct"] > 0
        and operating["candidate"]["net_pnl_krw"]
        > operating["incumbent"]["net_pnl_krw"]
        and operating["candidate"]["es10"] >= operating["incumbent"]["es10"]
        and operating["candidate"]["worst"] >= operating["incumbent"]["worst"]
    )
    baseline_preserved = bool(complete and deltas and not changed)
    return {
        "population_count": len(population),
        "terminal_evaluable_count": terminal_evaluable_count,
        "paired_comparable_count": len(deltas),
        "paired_terminal_proxy_delta_pct": fmean(deltas) if deltas else None,
        "candidate_opportunity_ev_pct": (
            fmean(candidate_values) if candidate_values else None
        ),
        "incumbent_opportunity_ev_pct": (
            fmean(incumbent_values) if incumbent_values else None
        ),
        "paired_terminal_contract_complete": complete,
        "changed_decision_count": len(changed),
        "unsupported_changed_decision_count": len(unsupported_changed),
        "recheck_sequence_unproven_count": 0 if sequence_supported else len(recheck_ids),
        "operating_population_count": len(operating_rows),
        "operating_population_complete": len(operating_rows) == len(population) and bool(population),
        "changed_decision_evidence": [{
            "evaluation_attempt_id": r.get("evaluation_attempt_id"),
            "decision_trace_id": r.get("decision_trace_id"),
            "source_date": r.get("source_date"), "stock_code": r.get("stock_code"),
            "incumbent_action": r["comparison"].get("control_action"),
            "candidate_admitted": r["decision_trace_id"] in selected_trace_ids,
            "owner_replay_status": "bound" if "operating_comparison_input" in r else "missing_or_unbound",
            "historical_recoverability": "not_established",
        } for r in changed],
        "downstream_operating_evidence_complete": downstream_complete,
        "operating_economic_promotion_pass": operating_promotion_pass,
        "independent_policy_comparison": bool(changed),
        "baseline_preserved": baseline_preserved,
        "daily_net_profit_delta_krw": 0.0 if baseline_preserved and downstream_complete else (
            operating.get("daily_net_profit_delta_krw")
            if operating is not None
            else None
        ),
        "daily_net_profit_status": (
            "baseline_preserved_no_independent_policy_change"
            if baseline_preserved and downstream_complete
            else operating.get("daily_net_profit_status")
            if operating is not None
            else "not_available_without_exact_changed_decision_owner_replay"
        ),
        **({"operating_economic_comparison": operating} if operating is not None else {}),
    }


def build_clean_baseline_mechanistic_refinement(
    paired_dir: Path,
    *,
    target_date: str,
    source_rows: list[dict[str, Any]] | None = None,
    source_contract: dict[str, Any] | None = None,
    parent_policy: dict[str, Any] | None = None,
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
    full_population = source_contract.get("schema") == "machine_common_refinement_population_v1"
    cohort = tuple(source_contract.get("cohort", ["KRX", "KRX_REGULAR"]))
    if not mechanistic_scope_supported(*cohort):
        raise ValueError("common_refinement_scope_unsupported")
    if full_population and parent_policy is None:
        raise ValueError("full_population_refinement_incumbent_missing")
    policy_version = MECHANISTIC_FULL_POPULATION_POLICY_VERSION if full_population else MECHANISTIC_REFINEMENT_POLICY_VERSION
    # The approved live-promotion floor remains the Plan Rebase 10bp gate.
    # Research metrics are still emitted below this floor.
    ev_floor = MECHANISTIC_REFINEMENT_GATE["minimum_cost_adjusted_ev_pct"]
    parent = json.loads(json.dumps(parent_policy or MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1))
    if validate_mechanistic_entry_threshold_policy(parent):
        raise ValueError("mechanistic_refinement_parent_invalid")
    if parent_policy is not None:
        # The exact incumbent, not historical AI BUY/WAIT, is the control.
        # Never mutate the frozen loader rows or relabel this as actual AI.
        rows = [
            {**row, "comparison": {
                **row["comparison"],
                "historical_control_action": row["comparison"].get("control_action"),
                "incumbent_machine_action": mechanistic_entry_policy_decision(row["setup_evidence"], policy=parent).get("action"),
                "control_action": "BUY" if mechanistic_entry_policy_decision(
                    row["setup_evidence"], policy=parent
                ).get("action") == "ENTER_NOW" else "WAIT",
                "control_role": "same_population_current_machine_incumbent",
            }}
            for row in rows
        ]
    source_dates = list(source_contract["accepted_source_dates"])
    frozen = source_contract.get("frozen_selection") or {}
    frozen_valid = bool(frozen.get("incumbent_sha256") == _canonical_sha256(parent)
                        and isinstance(frozen.get("policy"), dict)
                        and set(frozen["policy"]) == set(MECHANISTIC_COMMON_FEATURE_GRID)
                        and all(_number(v) is not None for v in frozen["policy"].values())
                        and isinstance(frozen.get("frozen_date"), str)
                        and frozen.get("economic_kernel_sha256") == source_contract.get("economic_kernel_sha256"))
    holdout_count = MECHANISTIC_REFINEMENT_GATE["holdout_source_date_count"]
    holdout_dates = (
        source_dates[-holdout_count:] if len(source_dates) > holdout_count else []
    )
    if frozen_valid:
        holdout_dates = [day for day in source_dates if day > frozen["frozen_date"]]
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
    structure_contract_counts = Counter(
        row["setup_evidence"].get("structure_contract_version") or "legacy_session_high_v1"
        for row in rows
    )

    candidates: list[dict[str, Any]] = []
    seen_selections: set[str] = set()
    grid = MECHANISTIC_COMMON_FEATURE_GRID
    choices = [dict(zip(grid, values)) for values in product(*grid.values())]
    incumbent_coordinates = {k: parent["thresholds"][k] for k in grid}
    if incumbent_coordinates not in choices:
        choices.append(incumbent_coordinates)
    def policy_distance(policy):
        return sum(abs(policy[k] - incumbent_coordinates[k]) / (max(grid[k]) - min(grid[k])) for k in grid)
    choices.sort(key=lambda policy: (policy_distance(policy), tuple(policy.values())))
    if frozen_valid:
        choices = [frozen["policy"]]
    for policy in choices:
        selected = _mechanistic_policy_rows(calibration_rows, policy, parent_policy=parent)
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
            calibration_rows, selected,
            candidate_policy=_mechanistic_threshold_policy(policy, parent)
        )
        gate_checks = {
            "minimum_exposure_count": metrics["exposure_count"]
            >= MECHANISTIC_REFINEMENT_GATE[
                "minimum_calibration_exposure_count"
            ],
            "minimum_unique_symbol_count": metrics["unique_symbol_count"]
            >= MECHANISTIC_REFINEMENT_GATE[
                "minimum_calibration_symbol_count"
            ],
            "minimum_independent_source_date_count": metrics[
                "independent_source_date_count"
            ]
            >= MECHANISTIC_REFINEMENT_GATE[
                "minimum_calibration_source_date_count"
            ],
            "minimum_terminal_evaluable_count": metrics[
                "terminal_evaluable_count"
            ]
            >= MECHANISTIC_REFINEMENT_GATE[
                "minimum_calibration_terminal_evaluable_count"
            ],
            "paired_terminal_delta_complete": metrics[
                "paired_terminal_proxy_delta_count"
            ]
            == metrics["terminal_evaluable_count"],
            "independent_policy_comparison": paired_population[
                "independent_policy_comparison"
            ]
            is True,
        }
        # Keep every distinct policy evaluation. Sample floors govern
        # promotion, not whether already-computable EV is reported.
        candidates.append(
            {
                "policy": policy,
                "selection_sha256": selection_sha256,
                "calibration": metrics,
                "calibration_paired_population": paired_population,
                "calibration_gate_checks": gate_checks,
                "calibration_gate_pass": all(gate_checks.values()),
            }
        )
    calibration_floor = ev_floor
    calibration_gate_candidates = [
        row for row in candidates if row["calibration_gate_pass"] is True
    ]
    calibration_passers = []
    for row in calibration_gate_candidates:
        metrics, paired = row["calibration"], row["calibration_paired_population"]
        ev, delta = machine_selection_economics(metrics, paired, full_population=full_population)
        if (ev is not None and ev >= calibration_floor and delta is not None and delta > 0
            and paired["paired_terminal_contract_complete"] is True
            and (not full_population or paired["operating_economic_promotion_pass"] is True)
            and metrics["source_provenance_contract_complete"] is True
            and metrics["catastrophic_terminal_proxy_count"] == 0):
            calibration_passers.append(row)
    economically_evaluable_candidates = [
        row
        for row in candidates
        if row["calibration_paired_population"][
            "candidate_opportunity_ev_pct"
        ]
        is not None
        and row["calibration_paired_population"][
            "paired_terminal_proxy_delta_pct"
        ]
        is not None
    ]
    operating_candidates = [r for r in candidates
        if r["calibration_paired_population"].get("downstream_operating_evidence_complete")
        and (r["calibration_paired_population"].get("operating_economic_comparison") or {}).get("status") == "supported_operating_comparison"]
    ranked = calibration_passers or operating_candidates or calibration_gate_candidates or economically_evaluable_candidates
    ranked.sort(key=lambda row: (
        _number(row["calibration_paired_population"].get("daily_net_profit_delta_krw"))
        if row in operating_candidates else -float("inf"),
        _number((row["calibration_paired_population"].get("operating_economic_comparison") or {}).get("robust_paired_delta_ev_lower_bound_pct"))
        if row in operating_candidates else -float("inf"),
        row["calibration_paired_population"].get("candidate_opportunity_ev_pct") or 0.,
        -policy_distance(row["policy"]),
    ), reverse=True)
    best = ranked[0] if ranked else None
    holdout_metrics = None
    holdout_paired_population = None
    holdout_selection_sha256 = None
    promotion_checks: dict[str, bool] = {}
    if best is not None:
        holdout_selected = _mechanistic_policy_rows(holdout_rows, best["policy"], parent_policy=parent)
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
            holdout_rows, holdout_selected,
            candidate_policy=_mechanistic_threshold_policy(best["policy"], parent)
        )
        calibration_ev, calibration_delta = machine_selection_economics(
            best["calibration"], best["calibration_paired_population"], full_population=full_population)
        holdout_ev, holdout_delta = machine_selection_economics(
            holdout_metrics, holdout_paired_population, full_population=full_population)
        promotion_checks = {
            "calibration_sample_and_comparison_floor": (
                best["calibration_gate_pass"] is True
            ),
            "calibration_cost_adjusted_ev_at_least_10bp": (
                calibration_ev is not None
                and calibration_ev >= ev_floor
            ),
            "holdout_cost_adjusted_ev_at_least_10bp": (
                holdout_ev is not None
                and holdout_ev >= ev_floor
            ),
            "calibration_positive_paired_terminal_delta": calibration_delta is not None and calibration_delta > 0,
            "holdout_positive_paired_terminal_delta": holdout_delta is not None and holdout_delta > 0,
            "holdout_paired_terminal_delta_complete": (
                holdout_paired_population["paired_terminal_contract_complete"] is True
            ),
            "calibration_downstream_operating_evidence_complete": (
                not full_population
                or best["calibration_paired_population"][
                    "downstream_operating_evidence_complete"
                ]
                is True
            ),
            "holdout_downstream_operating_evidence_complete": (
                not full_population
                or holdout_paired_population["downstream_operating_evidence_complete"]
                is True
            ),
            "calibration_operating_economic_promotion_pass": (
                not full_population
                or best["calibration_paired_population"][
                    "operating_economic_promotion_pass"
                ]
                is True
            ),
            "holdout_operating_economic_promotion_pass": (
                not full_population
                or holdout_paired_population["operating_economic_promotion_pass"]
                is True
            ),
            "calibration_source_provenance_complete": (
                best["calibration"]["source_provenance_contract_complete"] is True
            ),
            "calibration_selected_outcomes_complete": (
                best["calibration"]["terminal_evaluable_count"]
                == best["calibration"]["exposure_count"]
            ),
            "holdout_selected_outcomes_complete": (
                holdout_metrics["terminal_evaluable_count"]
                == holdout_metrics["exposure_count"]
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
    promotion_checks["incumbent_scope_verified"] = source_contract.get("incumbent_scope_verified", True) is True
    promotion_checks["path_boundary_contract_isolated"] = (
        path_boundary_contract_isolated
    )
    promotion_checks["structure_contract_isolated"] = len(structure_contract_counts) <= 1
    promotion_checks["holdout_source_coverage_complete"] = (
        bool(holdout_dates) and holdout_dates_with_accepted_rows == holdout_dates
    )
    forward_selection = frozen if frozen_valid else None
    if source_contract.get("forward_holdout_required") is True:
        promotion_checks["unseen_forward_holdout"] = bool(
            frozen_valid and holdout_dates and min(holdout_dates) > frozen["frozen_date"])
        if not frozen_valid and calibration_passers:
            forward_selection = {"policy": best["policy"],
                "incumbent_sha256": _canonical_sha256(parent),
                "frozen_date": datetime.now(KST).date().isoformat(),
                "calibration_rows_sha256": source_contract.get("accepted_rows_sha256"),
                "economic_contract": "machine_operating_daily_net_v1",
                "economic_kernel_sha256": source_contract.get("economic_kernel_sha256")}
    promotion_pass = (
        best is not None and bool(promotion_checks) and all(promotion_checks.values())
    )
    policy_candidate_body = (
        {
            "schema": "mechanistic_entry_common_feature_candidate_v1",
            "policy_version": policy_version,
            "evaluation_contract": "full_population_cost_adjusted_10bp_paired_delta_v3" if full_population else "legacy_absolute_net_10bp_v1",
            "thresholds": best["policy"],
            "incumbent_machine_policy": parent,
            "incumbent_machine_policy_sha256": _canonical_sha256(parent),
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
        "policy_version": policy_version,
        "target_date": target_date,
        "clean_tuning_baseline_date": CLEAN_BASELINE_DATE,
        "scope": {"stage": "entry", "venue": cohort[0], "session": cohort[1]},
        "incumbent_machine_policy_sha256": _canonical_sha256(parent),
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
            "minimum_ev_pct": ev_floor,
            "strictly_positive_net_ev_required": True,
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
            "structure_contract_counts": dict(structure_contract_counts),
        },
        "search_direction": "within_existing_bounds_incumbent_first",
        "calibration_source_dates": calibration_dates,
        "holdout_source_dates": holdout_dates,
        "evaluated_candidates": candidates,
        "nominal_grid_candidate_count": (
            len(grid["maximum_spread_bp"])
            * len(grid["minimum_fillability_score"])
            * len(grid["maximum_top3_ask_to_bid_ratio"])
        ),
        "evaluated_distinct_policy_count": len(candidates),
        "grid_candidate_count": len(economically_evaluable_candidates),
        "economically_evaluable_candidate_count": len(
            economically_evaluable_candidates
        ),
        "independent_policy_comparison_candidate_count": sum(
            row["calibration_paired_population"][
                "independent_policy_comparison"
            ]
            is True
            for row in economically_evaluable_candidates
        ),
        "calibration_gate_passing_candidate_count": len(
            calibration_gate_candidates
        ),
        "calibration_floor_passing_candidate_count": len(calibration_passers),
        "forward_selection": forward_selection,
        "candidate_selection_basis": (
            "operating_daily_net_then_paired_ev_then_minimum_policy_change"
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
                (
                    "no_common_feature_candidate_meets_positive_net_paired_holdout_gate"
                    if full_population
                    else "no_common_feature_candidate_meets_cost_adjusted_10bp_holdout_gate"
                )
                if best is not None and calibration_gate_candidates
                else "insufficient_mature_sample"
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


def _select_lifecycle_entry_trace(row: dict[str, Any]) -> tuple[str | None, str]:
    by_stage: dict[str, set[str]] = defaultdict(set)
    for item in row.get("decision_trace_context_path") or []:
        if not isinstance(item, dict) or not item.get("decision_trace_id"):
            continue
        by_stage[str(item.get("stage") or "").strip().lower()].add(
            str(item["decision_trace_id"])
        )
    entry_ids = set().union(
        *(
            by_stage.get(stage, set())
            for stage in ("entry", "entry_ai", "entry_decision")
        )
    )
    execution_ids = set().union(
        *(by_stage.get(stage, set()) for stage in ("submit", "fill"))
    )
    intersection = entry_ids.intersection(execution_ids)
    if len(intersection) == 1:
        return next(iter(intersection)), "unique_entry_submit_fill_intersection"
    if len(entry_ids) == 1:
        return next(iter(entry_ids)), "unique_entry_decision_trace"
    return None, "entry_trace_ambiguous_or_missing"


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
    entry_trace_selection_counts: Counter[str] = Counter()
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
            entry_trace_id, entry_trace_selection = _select_lifecycle_entry_trace(row)
            entry_trace_selection_counts[entry_trace_selection] += 1
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
                        "entry_trace_selection_basis": entry_trace_selection,
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
        "entry_trace_selection_counts": dict(
            sorted(entry_trace_selection_counts.items())
        ),
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


def _full_entry_cost_pct(contract: Any, *, source_date: str) -> float | None:
    """Do not relabel the legacy half-spread/age proxy as net economics."""
    c = _as_dict(contract)
    components = _as_dict(c.get("components_pct"))
    if (
        c.get("schema") != "entry_round_trip_cost_v1"
        or c.get("source_date") != source_date
        or not mechanistic_scope_supported(
            c.get("effective_venue"), c.get("session_bucket")
        )
        or c.get("basis") not in {"source_bound_estimate", "reconciled_execution_cost"}
        or not _is_sha256(c.get("source_sha256"))
        or set(components) != {"buy_fee", "sell_fee", "sell_tax", "slippage"}
        or any((n := _number(v)) is None or n < 0 for v in components.values())
    ):
        return None
    return sum(float(v) for v in components.values())


def _entry_cost_evidence(contract: Any, *, source_date: str) -> dict[str, Any]:
    """Expose comparison, executable estimate, and broker cost without conflation."""

    c = _as_dict(contract)
    components = _as_dict(c.get("components_pct"))
    full_cost = _full_entry_cost_pct(c, source_date=source_date)
    comparison_cost = None
    if full_cost is not None:
        comparison_cost = sum(
            float(components[name]) for name in ("buy_fee", "sell_fee", "sell_tax")
        )
    basis = str(c.get("basis") or "missing")
    broker_cost = full_cost if basis == "reconciled_execution_cost" else None
    executable_cost = full_cost if basis == "source_bound_estimate" else None
    selected_cost = broker_cost if broker_cost is not None else executable_cost
    selected_basis = (
        "broker_reconciled_cost_pct"
        if broker_cost is not None
        else (
            "executable_estimated_cost_pct"
            if executable_cost is not None
            else (
                "comparison_cost_pct_only_not_economic"
                if comparison_cost is not None
                else "missing"
            )
        )
    )
    return {
        "schema": "entry_cost_evidence_layers_v1",
        "comparison_cost_pct": comparison_cost,
        "executable_estimated_cost_pct": executable_cost,
        "broker_reconciled_cost_pct": broker_cost,
        "selected_economic_cost_pct": selected_cost,
        "cost_basis": selected_basis,
        "selected_cost_basis": selected_basis,
        "cost_components": components if full_cost is not None else {},
        "cost_components_pct": components if full_cost is not None else {},
        "cost_source_sha256": c.get("source_sha256") if full_cost is not None else None,
        "missing_cost_imputed": False,
        "comparison_cost_is_not_live_economic_acceptance": True,
    }


def _hierarchy_cost_profiles(
    data_root: Path, day: str, venue: str = "KRX"
) -> dict[str, dict]:
    """Read the existing exact-date main economic owner; never infer tax class."""
    from src.engine.scalping.micro_reversion.economic_reference import content_sha256

    path = existing_or_gzip_path(
        data_root
        / "report"
        / "micro_reversion_economic_reference"
        / f"micro_reversion_economic_reference_{day}.json"
    )
    artifact = _load_json(path) if path else {}
    if (
        artifact.get("schema")
        != "micro_reversion_economic_reference_daily_resolution_v2"
        or artifact.get("target_date") != day
        or artifact.get("verified") is not True
        or artifact.get("tuning_input_allowed") is not True
        or artifact.get("artifact_content_sha256")
        != content_sha256(
            {k: v for k, v in artifact.items() if k != "artifact_content_sha256"}
        )
    ):
        return {}
    sources = artifact.get("source_artifacts") or []
    if (
        not isinstance(sources, list)
        or not sources
        or any(not isinstance(s, dict) for s in sources)
    ):
        return {}
    if {s.get("kind") for s in sources} != {
        "broker_fee",
        "statutory_tax",
        "symbol_product_master",
    } or any(
        s.get("verified") is not True
        or _observed_file_sha256(Path(str(s.get("resolved_path") or "")))
        != s.get("expected_sha256")
        for s in sources
    ):
        return {}
    catalog = _as_dict(artifact.get("canonical_reviewed_cost_payload"))
    if catalog.get("content_sha256") != content_sha256(
        {k: v for k, v in catalog.items() if k != "content_sha256"}
    ):
        return {}
    profiles = {p["profile_id"]: p for p in catalog.get("profiles", [])}
    return {
        r["symbol"]: {
            **profiles[r["reviewed_cost_profile_id"]],
            "economic_source_sha256": artifact["artifact_content_sha256"],
        }
        for r in artifact.get("coverage_rows", [])
        if r.get("status") == "eligible"
        and r.get("venue") == venue
        and r.get("reviewed_cost_profile_id") in profiles
    }


def _hierarchy_cost_contract(
    profile: dict,
    day: str,
    friction: Any,
    cohort: tuple[str, str] = ("KRX", "KRX_REGULAR"),
) -> dict | None:
    friction = _number(friction)
    if not profile or friction is None or friction < 0:
        return None
    fields = (
        "buy_fee_bps",
        "sell_fee_bps",
        "statutory_sell_tax_bps",
        "uncertainty_buffer_bps",
    )
    values = [_number(profile.get(k)) for k in fields]
    if any(v is None or v < 0 for v in values):
        return None
    return {
        "schema": "entry_round_trip_cost_v1",
        "source_date": day,
        "effective_venue": cohort[0],
        "session_bucket": cohort[1],
        "basis": "source_bound_estimate",
        "source_sha256": profile["economic_source_sha256"],
        "profile_id": profile["profile_id"],
        "components_pct": {
            "buy_fee": values[0] / 100,
            "sell_fee": values[1] / 100,
            "sell_tax": values[2] / 100,
            "slippage": friction + values[3] / 100,
        },
    }


def relabel_hierarchy_source_rows(
    source_rows: list[dict],
    data_root: Path,
    *,
    cohort: tuple[str, str] = ("KRX", "KRX_REGULAR"),
    pipeline_prices_by_day: dict[str, dict[str, list[dict]]] | None = None,
) -> tuple[list[dict], dict]:
    """Reprice existing CF paths with full costs, preserving original reports."""
    from src.engine.scalping import ai_decision_quality as quality

    result, counts, by_day = [], Counter(), defaultdict(list)
    for row in source_rows:
        if row.get("source_provenance_verified") is not None and not _machine_source_contract_valid(row):
            counts["source_contract_invalid_no_reprice"] += 1
            result.append(row)
            continue
        by_day[row["source_date"]].append(row)
    for day, rows in sorted(by_day.items()):
        profiles = _hierarchy_cost_profiles(data_root, day, cohort[0])
        if not profiles:
            counts["economic_owner_missing_or_unverified"] += len(rows)
            result.extend(rows)
            continue
        if not any(
            r["stock_code"] in profiles
            and (r.get("label_context") or {}).get("reference_price_type")
            == "executable_ask"
            for r in rows
        ):
            counts["executable_reference_missing"] += len(rows)
            result.extend(rows)
            continue
        if all(_full_entry_cost_pct(r["comparison"].get("entry_cost_contract"), source_date=day) is not None for r in rows):
            result.extend(rows)
            continue
        if pipeline_prices_by_day is None:
            pipeline = existing_or_gzip_path(
                data_root / "pipeline_events" / f"pipeline_events_{day}.jsonl"
            )
            prices, _ = quality.load_pipeline_price_and_lifecycle_rows(
                iter_jsonl(pipeline) if pipeline and pipeline.is_file() else [],
                stock_codes={r["stock_code"] for r in rows},
            )
            prices_by_symbol = defaultdict(list)
            for price in prices:
                prices_by_symbol[price.get("stock_code")].append(price)
        else:
            prices_by_symbol = pipeline_prices_by_day.get(day, {})
        for row in rows:
            comparison = row["comparison"]
            if (
                _full_entry_cost_pct(
                    comparison.get("entry_cost_contract"), source_date=day
                )
                is not None
            ):
                result.append(row)
                continue
            cost = _hierarchy_cost_contract(
                profiles.get(row["stock_code"], {}),
                day,
                comparison.get("conservative_execution_cost_pct"),
                cohort,
            )
            context = dict(row.get("label_context") or {})
            if cost is None or context.get("reference_price_type") != "executable_ask":
                counts["cost_or_executable_reference_missing"] += 1
                result.append(row)
                continue
            full_cost = _full_entry_cost_pct(cost, source_date=day)
            pending = {
                **context,
                "stock_code": row["stock_code"],
                "decision_ts": row["decision_ts"],
                "decision_trace_id": row["decision_trace_id"],
                "decision_stage": "entry",
                "invalid_reasons": [],
                "adverse_pct": quality.ENTRY_PATH_ADVERSE_PCT,
                "entry_conservative_execution_cost_pct": full_cost,
            }
            labeled = quality.mature_outcome_labels(
                pending_labels=[pending],
                price_rows=prices_by_symbol.get(row["stock_code"], []),
                lifecycle_rows=[],
                as_of=datetime.fromisoformat(day + "T23:59:59+09:00"),
            )[0]
            metric = labeled.get("horizon_metrics", {}).get("10m", {})
            path = metric.get("entry_quality_path")
            if not isinstance(path, dict) or path.get("status") != "evaluable":
                counts["raw_path_missing"] += 1
                result.append(row)
                continue
            result.append(
                {
                    **row,
                    "entry_quality_path": path,
                    "entry_quality_contract_valid": True,
                    "exit_cohort": "existing_fixed_boundary_counterfactual",
                    "comparison": {
                        **comparison,
                        "entry_cost_contract": cost,
                        "conservative_execution_cost_pct": full_cost,
                        **{
                            k: metric.get(k)
                            for k in (
                                "entry_path_first_hit",
                                "entry_path_target_pct",
                                "entry_path_adverse_pct",
                            )
                        },
                    },
                }
            )
            counts["full_cost_path_relabeled"] += 1
    return result, dict(counts)


def _hierarchy_pipeline_price_cache(
    source_rows: list[dict], data_root: Path
) -> dict[str, dict[str, list[dict]]]:
    """Read each daily pipeline once for all supported hierarchy scopes."""
    from src.engine.scalping import ai_decision_quality as quality

    symbols_by_day: dict[str, set[str]] = defaultdict(set)
    for row in source_rows:
        day = str(row.get("source_date") or "")
        stock_code = str(row.get("stock_code") or "")
        if day and stock_code:
            symbols_by_day[day].add(stock_code)
    result: dict[str, dict[str, list[dict]]] = {}
    for day, stock_codes in sorted(symbols_by_day.items()):
        pipeline = existing_or_gzip_path(
            data_root / "pipeline_events" / f"pipeline_events_{day}.jsonl"
        )
        prices, _ = quality.load_pipeline_price_and_lifecycle_rows(
            iter_jsonl(pipeline) if pipeline and pipeline.is_file() else [],
            stock_codes=stock_codes,
        )
        prices_by_symbol: dict[str, list[dict]] = defaultdict(list)
        for price in prices:
            prices_by_symbol[str(price.get("stock_code") or "")].append(price)
        result[day] = dict(prices_by_symbol)
    return result


def _machine_ai_trace_index(data_root: Path, day: str) -> dict[str, list[dict]]:
    """Index the existing AI trace by its exact input snapshot.

    A machine observation is captured immediately before the composed AI
    decision.  Snapshot identity is therefore the only safe attempt-level join;
    symbol and a nearby timestamp alone are intentionally insufficient.
    """

    path = existing_or_gzip_path(
        data_root / "ai_decision_trace" / f"ai_decision_trace_{day}.jsonl"
    )
    result: dict[str, list[dict]] = defaultdict(list)
    if path is None or not path.is_file():
        return result
    for row in iter_jsonl(path):
        snapshot_id = str(row.get("snapshot_id") or "").strip()
        if (
            row.get("schema") != "ai_decision_trace_v1"
            or row.get("decision_stage") != "entry_screen"
            or not snapshot_id
        ):
            continue
        result[snapshot_id].append(row)
    return result


def _match_machine_ai_trace(
    capture: dict, context: dict, trace_index: dict[str, list[dict]]
) -> tuple[dict, str]:
    snapshot_id = str(context.get("snapshot_id") or "").strip()
    if not snapshot_id:
        return {}, "machine_snapshot_id_missing"

    def aware_timestamp(value: Any) -> datetime | None:
        try:
            parsed = datetime.fromisoformat(str(value or "").replace("Z", "+00:00"))
        except ValueError:
            return None
        return parsed if parsed.utcoffset() is not None else None

    capture_ts = aware_timestamp(capture.get("captured_at"))
    capture_promotion_id = str(context.get("scanner_promotion_id") or "").strip()
    candidates = []
    for row in trace_index.get(snapshot_id, []):
        trace_ts = aware_timestamp(row.get("decision_ts"))
        trace_promotion_id = str(row.get("scanner_promotion_id") or "").strip()
        if (
            str(row.get("stock_code") or "") != str(context.get("stock_code") or "")
            or _normalized_venue(row.get("effective_venue"))
            != _normalized_venue(context.get("effective_venue"))
            or _normalized_session(row.get("session_bucket"))
            != _normalized_session(context.get("session_bucket"))
            or capture_ts is None
            or trace_ts is None
            or not -1.0 <= (trace_ts - capture_ts).total_seconds() <= 120.0
            or (
                capture_promotion_id
                and trace_promotion_id
                and trace_promotion_id != capture_promotion_id
            )
        ):
            continue
        machine_bundle = str(capture.get("bundle_sha256") or "")
        trace_bundle = str(row.get("machine_bundle_sha256") or "")
        if trace_bundle and machine_bundle and trace_bundle != machine_bundle:
            continue
        candidates.append(row)
    expected_action = str(
        _as_dict(_as_dict(capture.get("source")).get("assessment")).get("action") or ""
    ).upper()
    matching_action = [
        row
        for row in candidates
        if str(row.get("entry_mechanistic_action") or "").upper() == expected_action
    ]
    if len(matching_action) == 1:
        return matching_action[0], "exact_snapshot_machine_action_join"
    if candidates:
        # A snapshot is not a sufficient substitute when the composed trace
        # reports a different mechanistic action.  Keep that mismatch visible
        # in the capture census but exclude it from learning rather than
        # silently using the nearby trace as a policy row.
        return {}, "machine_action_mismatch_for_exact_snapshot"
    if not candidates:
        return {}, "ai_trace_missing_for_exact_snapshot"
    return {}, "ai_trace_ambiguous_for_exact_snapshot"


def _compact_machine_horizon_metrics(metrics: Any) -> dict[str, dict]:
    result = {}
    for horizon in ("1m", "3m", "5m", "10m", "20m", "30m", "60m"):
        metric = _as_dict(_as_dict(metrics).get(horizon))
        if not metric:
            result[horizon] = {
                "status": "pending_or_source_gap",
                "sample_count": 0,
                "mfe_pct": None,
                "mae_pct": None,
                "end_return_pct": None,
                "entry_path_first_hit": None,
                "entry_quality_status": None,
                "entry_quality_label": None,
                "cost_adjusted_target_pct": None,
                "time_to_net_target_sec": None,
                "pre_target_mae_pct": None,
                "pre_target_underwater_ratio": None,
            }
            continue
        path = _as_dict(metric.get("entry_quality_path"))
        result[horizon] = {
            "status": "observed",
            "sample_count": metric.get("sample_count"),
            "mfe_pct": metric.get("mfe_pct"),
            "mae_pct": metric.get("mae_pct"),
            "end_return_pct": metric.get("end_return_pct"),
            "entry_path_first_hit": metric.get("entry_path_first_hit"),
            "entry_quality_status": path.get("status"),
            "entry_quality_label": path.get("entry_quality_label"),
            "cost_adjusted_target_pct": path.get("gross_net_target_pct"),
            "time_to_net_target_sec": path.get("time_to_net_target_sec"),
            "pre_target_mae_pct": path.get("pre_target_mae_pct"),
            "pre_target_underwater_ratio": path.get("pre_target_underwater_ratio"),
        }
    return result



def _machine_capture_cost_reference_venue(capture: dict, cohort: tuple[str, str]) -> str | None:
    """Economic catalog venue is not the integrated market-data scope label."""
    if cohort[0] in {"KRX", "NXT"}:
        return cohort[0]
    context = _as_dict(capture.get("label_context"))
    payload = _as_dict(_as_dict(capture.get("source")).get("exact_payload"))
    snapshot = _as_dict(payload.get("ai_market_snapshot_v1"))
    route = str(context.get("broker_route") or "").upper()
    if (
        route in {"KRX", "NXT", "SOR"}
        and route == str(snapshot.get("broker_route") or "").upper()
        and context.get("snapshot_id") == snapshot.get("snapshot_id")
        and context.get("snapshot_id")
        and context.get("market_data_route") == "krx_nxt_integrated"
        and snapshot.get("market_data_route") == "krx_nxt_integrated"
    ):
        return route
    return None


def load_machine_observation_rows(
    data_root: Path, *, target_date: str, materialized_labels_only: bool = False, independent_machine: bool = False
) -> tuple[list[dict], dict]:
    """Reuse the payload archive and existing path labeler, with no AI calls."""
    from src.engine.scalping import ai_decision_quality as quality
    from src.engine.scalping.entry_setup_evidence import validate_entry_setup_evidence
    from src.engine.scalping.ai_decision_trace import _json_bytes
    from src.engine.scalping.microstructure_reaction_context import bind_machine_microstructure_source, summarize_machine_capture_population

    result, counts = [], Counter()
    capture_populations = []
    for path in sorted((data_root / "ai_decision_payloads").glob("*.jsonl*")):
        match = re.search(r"(\d{4}-\d{2}-\d{2})\.jsonl", path.name)
        # Machine-only capture started on 9/13. The clean-baseline paired
        # replay loader supplies older evidence; opening every prior payload
        # archive here would add postclose I/O without creating a valid capture.
        if not match or not "2026-09-13" <= match[1] <= target_date:
            continue
        if path.suffix == ".gz" and path.with_suffix("").is_file():
            continue
        # Snapshot files contain both real provider inputs and machine-only
        # observations. Never convert one schema into the other's authority.
        captures = [
            r
            for r in iter_jsonl(path)
            if r.get("schema") == "mechanistic_entry_observation_v1"
        ]
        if not captures:
            continue
        by_day = defaultdict(list)
        for capture in captures:
            counts["captured"] += 1
            day = _kst_date_from_aware_timestamp(capture.get("captured_at"))
            source = _as_dict(capture.get("source"))
            evidence = source.get("setup_evidence")
            if (
                not day
                or not CLEAN_BASELINE_DATE <= day <= target_date
                or capture.get("machine_observation_sha256")
                != hashlib.sha256(
                    _json_bytes(
                        {
                            k: v
                            for k, v in capture.items()
                            if k != "machine_observation_sha256"
                        }
                    )
                ).hexdigest()
                or capture.get("redacted") is not False
                or capture.get("provider_called") is not False
                or any(
                    capture.get(k) is not v
                    for k, v in (
                        ("runtime_effect", False),
                        ("allowed_runtime_apply", False),
                        ("actual_order_submitted", False),
                        ("broker_order_forbidden", True),
                    )
                )
                or validate_entry_setup_evidence(evidence)
            ):
                counts["invalid_capture"] += 1
                continue
            by_day[day].append(capture)
        capture_populations.append(summarize_machine_capture_population([capture for observations in by_day.values() for capture in observations]))
        for day, observations in by_day.items():
            cost_profiles_by_venue = {}
            ai_trace_index = {} if independent_machine else _machine_ai_trace_index(data_root, day)
            materialized_by_trace: dict[str, dict] = {}
            if materialized_labels_only:
                label_path = (
                    data_root
                    / "report/ai_decision_outcome_labels"
                    / f"ai_decision_outcome_labels_{day}.json"
                )
                control_path = (
                    data_root
                    / "runtime"
                    / f"ai_decision_quality_control_{day}.json"
                )
                label_report = _load_json(label_path)
                control = _load_json(control_path)
                errors = quality.validate_daily_materialization_reports(
                    target_date=day,
                    reports={"control": control, "mature": label_report},
                )
                label_rows = label_report.get("labels") or []
                label_counts = Counter(
                    str(row.get("decision_trace_id") or "") for row in label_rows
                )
                if not errors:
                    materialized_by_trace = {
                        str(row["decision_trace_id"]): row
                        for row in label_rows
                        if row.get("decision_trace_id")
                        and label_counts[str(row["decision_trace_id"])] == 1
                    }
                else:
                    counts["materialized_label_contract_invalid"] += len(
                        observations
                    )
                prices, lifecycle = [], []
            else:
                pipeline = existing_or_gzip_path(
                    data_root / "pipeline_events" / f"pipeline_events_{day}.jsonl"
                )
                prices, lifecycle = quality.load_pipeline_price_and_lifecycle_rows(
                    iter_jsonl(pipeline) if pipeline and pipeline.is_file() else [],
                    stock_codes={
                        str(c.get("label_context", {}).get("stock_code") or "")
                        for c in observations
                    },
                )
            prices_by_symbol = defaultdict(list)
            for price in prices:
                prices_by_symbol[price.get("stock_code")].append(price)
            lifecycle_by_symbol = defaultdict(list)
            for event in lifecycle:
                lifecycle_by_symbol[event.get("stock_code")].append(event)
            for capture in observations:
                context = dict(capture.get("label_context") or {})
                ai_trace, ai_trace_join_status = ({}, 'independent_machine_no_ai_join') if independent_machine else _match_machine_ai_trace(
                    capture, context, ai_trace_index
                )
                counts[ai_trace_join_status] += 1
                if ai_trace_join_status == "machine_action_mismatch_for_exact_snapshot":
                    counts["machine_action_mismatch_excluded"] += 1
                    continue
                # Runtime capture stores the canonical label context exactly as
                # observed.  Session labels are lower-case there while the
                # mechanistic scope registry is upper-case.  Normalize only for
                # scope/cost-owner lookup; keep the captured context unchanged
                # for provenance and hash verification.
                cohort = (
                    _normalized_venue(context.get("effective_venue")),
                    _normalized_session(context.get("session_bucket")),
                )
                if not mechanistic_scope_supported(*cohort):
                    counts["unsupported_cohort"] += 1
                    continue
                cost_reference_venue = _machine_capture_cost_reference_venue(capture, cohort)
                if cost_reference_venue not in cost_profiles_by_venue:
                    cost_profiles_by_venue[cost_reference_venue] = (
                        _hierarchy_cost_profiles(data_root, day, cost_reference_venue)
                        if cost_reference_venue else {}
                    )
                cost_profiles = cost_profiles_by_venue[cost_reference_venue]
                cost_contract = capture["source"]["exact_payload"].get(
                    "entry_cost_contract"
                )
                if cost_contract is None:
                    friction = context.get("entry_conservative_execution_cost_pct")
                    if friction is None:
                        spread = _number(
                            _as_dict(
                                _as_dict(
                                    capture["source"]["setup_evidence"].get(
                                        "tail_risk_assessment"
                                    )
                                ).get("inputs")
                            ).get("spread_bp")
                        )
                        friction = spread / 200 if spread is not None else None
                    cost_contract = _hierarchy_cost_contract(
                        cost_profiles.get(context.get("stock_code"), {}),
                        day,
                        friction,
                        cohort,
                    )
                full_cost = _full_entry_cost_pct(cost_contract, source_date=day)
                if (
                    _as_dict(cost_contract).get("effective_venue"),
                    _as_dict(cost_contract).get("session_bucket"),
                ) != cohort:
                    full_cost = None
                if full_cost is None:
                    counts["full_round_trip_cost_missing"] += 1
                    if not independent_machine:
                        continue
                context["entry_conservative_execution_cost_pct"] = full_cost
                # Fixed-exit CF cohort, not an assertion about the user's live stop.
                context["adverse_pct"] = quality.ENTRY_PATH_ADVERSE_PCT
                if context.get("reference_price_type") != "executable_ask":
                    counts["executable_reference_missing"] += 1
                    if not independent_machine:
                        continue
                pending = {
                    **context,
                    "decision_ts": capture["captured_at"],
                    # Use the exact composed-AI trace only for downstream
                    # lifecycle correlation. The machine digest remains the
                    # immutable case identity below.
                    "decision_trace_id": ai_trace.get("decision_trace_id"),
                    "record_id": context.get("record_id") or ai_trace.get("record_id"),
                    "decision_stage": "entry",
                    "invalid_reasons": [],
                }
                if materialized_labels_only:
                    labeled = materialized_by_trace.get(
                        str(ai_trace.get("decision_trace_id") or "")
                    )
                    if (
                        not isinstance(labeled, dict)
                        or labeled.get("snapshot_id") != context.get("snapshot_id")
                        or str(labeled.get("stock_code") or "")
                        != str(context.get("stock_code") or "")
                    ):
                        counts["materialized_exact_label_missing"] += 1
                        continue
                    counts["materialized_exact_label_reused"] += 1
                else:
                    labeled = quality.mature_outcome_labels(
                        pending_labels=[pending],
                        price_rows=prices_by_symbol[context.get("stock_code")],
                        lifecycle_rows=lifecycle_by_symbol[context.get("stock_code")],
                        as_of=datetime.fromisoformat(
                            target_date + "T23:59:59+09:00"
                        ),
                    )[0]
                horizon_metrics = labeled.get("horizon_metrics", {})
                metric = horizon_metrics.get("10m", {})
                entry_path = metric.get("entry_quality_path")
                if (
                    not isinstance(entry_path, dict)
                    or entry_path.get("status") != "evaluable"
                ):
                    counts["path_or_cost_missing"] += 1
                    if not independent_machine:
                        continue
                evidence = dict(capture["source"]["setup_evidence"])
                if "strategy_raw_input" not in evidence:
                    from src.engine.scalping.entry_strategy_policy import digest as strategy_digest
                    raw = capture["source"].get("exact_payload")
                    if isinstance(raw, dict) and raw:
                        raw = {**raw, 'strategy_observed_at': capture['captured_at']}
                        evidence["strategy_raw_input"] = raw
                        evidence["strategy_raw_sha256"] = strategy_digest(raw)
                        evidence["evidence_sha256"] = _canonical_sha256({k: v for k, v in evidence.items() if k != "evidence_sha256"})
                assessment = _as_dict(capture["source"].get("assessment"))
                machine_action = str(assessment.get("action") or "").upper()
                if machine_action not in {"BLOCK", "RECHECK", "ENTER_NOW"}:
                    counts["machine_action_invalid"] += 1
                    continue
                mc = evidence.get("mechanistic_context") or {}
                cost = context.get("entry_conservative_execution_cost_pct")
                correlation = _as_dict(labeled.get("correlation"))
                pipeline_joined = correlation.get("status") == "exact_matched"
                counts[
                    (
                        "pipeline_lifecycle_exact_join"
                        if pipeline_joined
                        else "pipeline_lifecycle_unresolved"
                    )
                ] += 1
                scanner_promotion_ids = list(
                    correlation.get("scanner_promotion_ids") or []
                )
                if context.get("scanner_promotion_id") not in (None, "", "-"):
                    scanner_promotion_ids.append(str(context["scanner_promotion_id"]))
                scanner_promotion_ids = sorted(set(scanner_promotion_ids))
                scanner_promotion_id = str(
                    context.get("scanner_promotion_id") or ""
                ).strip()
                scanner_promotion_identity_source = (
                    "machine_capture"
                    if scanner_promotion_id
                    else (
                        "pipeline_exact_match"
                        if pipeline_joined and len(scanner_promotion_ids) == 1
                        else "missing_or_ambiguous"
                    )
                )
                if (
                    not scanner_promotion_id
                    and pipeline_joined
                    and len(scanner_promotion_ids) == 1
                ):
                    scanner_promotion_id = scanner_promotion_ids[0]
                evaluation_attempt_id = str(
                    context.get("evaluation_attempt_id")
                    or context.get("snapshot_id")
                    or capture["machine_observation_sha256"]
                )
                result.append(
                    {
                        "decision_trace_id": capture["machine_observation_sha256"],
                        "ai_decision_trace_id": ai_trace.get("decision_trace_id"),
                        "evaluation_attempt_id": evaluation_attempt_id,
                        "evaluation_attempt_identity_source": (
                            "exact_market_snapshot"
                            if context.get("snapshot_id")
                            else "machine_observation_digest_fallback"
                        ),
                        "record_id": context.get("record_id")
                        or ai_trace.get("record_id"),
                        "scanner_promotion_id": scanner_promotion_id or None,
                        "scanner_promotion_identity_source": (
                            scanner_promotion_identity_source
                        ),
                        "scanner_promotion_ids": scanner_promotion_ids,
                        "decision_ts": capture["captured_at"],
                        "source_date": day,
                        "stock_code": context.get("stock_code"),
                        "decision_snapshot_id": context.get("snapshot_id"),
                        "effective_venue": cohort[0],
                        "session_bucket": cohort[1],
                        "bundle_sha256": capture.get("bundle_sha256"),
                        "machine_action": machine_action,
                        "machine_reason": assessment.get("reason"),
                        "machine_hierarchy_selection": assessment.get(
                            "hierarchy_selection"
                        ),
                        "machine_core_comparison": assessment.get("core_comparison"),
                        "machine_applied_thresholds": assessment.get(
                            "applied_thresholds"
                        ),
                        "machine_liquidity_inputs": assessment.get("liquidity_inputs"),
                        "setup_evidence": evidence,
                        "entry_group_observation": mc.get("group", {}),
                        "entry_group_contract_valid": True,
                        "mechanistic_flow_observation": mc.get("flow", {}),
                        "mechanistic_flow_observation_contract_valid": True,
                        "entry_quality_path": entry_path,
                        "outcome_horizon_metrics": (
                            _compact_machine_horizon_metrics(horizon_metrics)
                        ),
                        "entry_quality_contract_valid": bool(isinstance(entry_path, dict) and entry_path.get('status') == 'evaluable'
                            and full_cost is not None and context.get('reference_price_type') == 'executable_ask'),
                        "source_report_hash_verified": False,
                        "microstructure_evaluation_binding": bind_machine_microstructure_source(capture),
                        "machine_observation_hash_verified": True,
                        "source_provenance_verified": True,
                        "comparison": {
                            "entry_cost_contract": cost_contract,
                            "cost_reference_venue": cost_reference_venue,
                            "cost_reference_identity_source": ("exact_market_venue" if cohort[0] in {"KRX", "NXT"} else "hash_verified_exact_snapshot_broker_route"),
                            "cost_evidence": _entry_cost_evidence(
                                cost_contract, source_date=day
                            ),
                            "control_action": "WAIT",
                            "entry_path_first_hit": metric.get("entry_path_first_hit"),
                            "entry_path_target_pct": metric.get(
                                "entry_path_target_pct"
                            ),
                            "entry_path_adverse_pct": metric.get(
                                "entry_path_adverse_pct"
                            ),
                            "conservative_execution_cost_pct": cost,
                        },
                        "watch_timing": {
                            "first_watch_epoch": context.get("first_watch_epoch"),
                            "watch_age_sec": context.get("watch_age_sec"),
                            "first_watch_price": context.get("first_watch_price"),
                            "price_delta_since_first_watch_pct": context.get(
                                "price_delta_since_first_watch_pct"
                            ),
                        },
                        "ai_and_final_guard": {
                            "join_status": ai_trace_join_status,
                            "ai_action": ai_trace.get("action"),
                            "ai_result_source": ai_trace.get("result_source"),
                            "provider_called": ai_trace.get("provider_called"),
                            "ai_screen_status": ai_trace.get("entry_ai_screen_status"),
                            "ai_screen_pass": ai_trace.get("entry_ai_screen_pass"),
                            "ai_risk_verdict": ai_trace.get("entry_ai_risk_verdict"),
                            "decision_quality_contract_status": ai_trace.get(
                                "decision_quality_contract_status"
                            ),
                            "semantic_validation_status": ai_trace.get(
                                "semantic_validation_status"
                            ),
                            "ai_veto_corroborated": ai_trace.get(
                                "entry_ai_veto_corroborated"
                            ),
                            "prompt_version": ai_trace.get("prompt_version"),
                            "prompt_sha256": ai_trace.get("prompt_sha256"),
                            "auxiliary_system_prompt_sha256": ai_trace.get(
                                "auxiliary_system_prompt_sha256"
                            ),
                            "entry_ai_prompt_variant": ai_trace.get(
                                "entry_ai_prompt_variant"
                            ),
                            "followup_disposition": ai_trace.get(
                                "entry_ai_followup_disposition"
                            ),
                            "pipeline_lifecycle_status": correlation.get("status"),
                            "matched_stage_counts": correlation.get(
                                "matched_stage_counts"
                            ),
                            "observed_actual_order_submitted": correlation.get(
                                "actual_order_submitted"
                            ),
                            "fill_observed": correlation.get("fill_observed"),
                            "realized_profit_pct": correlation.get(
                                "realized_profit_pct"
                            ),
                        },
                        "source_lane": "machine_observation_counterfactual_no_provider",
                        "exit_cohort": "existing_fixed_boundary_counterfactual",
                    }
                )
                counts["evaluable" if result[-1]["entry_quality_contract_valid"] else "retained_without_economic_outcome"] += 1
    population = {
        key: sum(part[key] for part in capture_populations)
        for key in ("verified_capture_count", "unique_verified_capture_count", "duplicate_capture_collapsed_count")
    }
    population["partitions"] = [partition for part in capture_populations for partition in part["partitions"]]
    population["economic_exclusions_do_not_erase_capture_population"] = True
    return result, {**dict(counts), "microstructure_capture_population": population}


def _machine_ai_natural_source_receipt(data_root: Path, target_date: str) -> dict:
    """Load #74's compact archive manifest without treating it as policy authority."""
    path = (
        data_root
        / "report"
        / "observation_source_quality_audit"
        / f"observation_source_quality_audit_{target_date}.json"
    )
    try:
        report = _load_json(path)
    except (OSError, ValueError, json.JSONDecodeError):
        report = {}
    consumption = report.get("machine_ai_natural_source_consumption")
    consumption = consumption if isinstance(consumption, dict) else {}
    manifest = consumption.get("source_manifest")
    manifest = manifest if isinstance(manifest, dict) else {}
    compact_measurement = consumption.get("compact_auxiliary_policy_measurement")
    compact_measurement = (
        compact_measurement if isinstance(compact_measurement, dict) else {}
    )
    terminal_tuning_gate = consumption.get("machine_terminal_tuning_gate")
    terminal_tuning_gate = (
        terminal_tuning_gate if isinstance(terminal_tuning_gate, dict) else {}
    )
    return {
        "path": str(path),
        "target_date": target_date,
        "schema": consumption.get("schema"),
        "status": consumption.get("status", "missing"),
        "source_manifest_sha256": manifest.get("source_manifest_sha256"),
        "tuning_input_allowed": consumption.get("tuning_input_allowed"),
        "machine_attempt_conservation": consumption.get("machine_attempt_conservation"),
        "machine_threshold_tuning_input_allowed": consumption.get(
            "machine_threshold_tuning_input_allowed"
        ),
        "machine_threshold_tuning_blocked_reason": consumption.get(
            "machine_threshold_tuning_blocked_reason"
        ),
        "compact_auxiliary_policy_measurement": compact_measurement,
        "machine_terminal_tuning_gate": terminal_tuning_gate,
        "authority": "source_quality_receipt_only_no_runtime_apply",
    }


def _machine_evaluation_key(row: Mapping[str, Any], *, allow_attempt_fallback: bool = False) -> str:
    values = (
        row.get("scanner_promotion_id"),
        row.get("evaluation_attempt_id") or row.get("decision_trace_id"),
        row.get("stock_code"),
        row.get("effective_venue"),
        row.get("session_bucket"),
        row.get("bundle_sha256"),
    )
    if allow_attempt_fallback and not str(values[0] or '').strip() and all(str(v or '').strip() for v in values[1:]) and row.get('source_date'):
        return 'machine-attempt:' + _canonical_sha256([row['source_date'], *values[1:]])
    if not all(str(value or "").strip() for value in values):
        return ""
    return "machine:" + "|".join(str(value).strip() for value in values)


def _machine_learning_fingerprint(row: Mapping[str, Any]) -> str:
    """Compare decision/outcome bodies, not duplicate arrival metadata."""
    return _canonical_sha256({key: row.get(key) for key in (
        "decision_trace_id", "source_date", "machine_action", "machine_reason",
        "setup_evidence", "comparison", "entry_quality_path",
        "machine_applied_thresholds", "machine_core_comparison",
        "machine_hierarchy_selection", "machine_liquidity_inputs",
        "ai_and_final_guard", "outcome_horizon_metrics", "microstructure_evaluation_binding",
    )})


def _machine_conflicting_evaluation_keys(rows: list[dict], *, allow_attempt_fallback: bool = False) -> set[str]:
    """Locate whole conflicting attempts before either arm contributes EV."""
    seen, conflicts = {}, set()
    for row in rows:
        key = _machine_evaluation_key(row, allow_attempt_fallback=allow_attempt_fallback)
        if not key:
            continue
        fingerprint = _machine_learning_fingerprint(row)
        if key in seen and seen[key] != fingerprint:
            conflicts.add(key)
        else:
            seen[key] = fingerprint
    return conflicts


def _compact_history_receipt(
    data_root: Path,
    target_date: str,
    rows: list[dict],
    incumbent: dict | None,
    receipt: dict,
) -> dict:
    """Admit historical partitions only with their own final source receipt.

    A new dated bundle is compatible only when its machine policy and issued
    AI policy are identical to the incumbent. No historical source is relabelled.
    """
    from src.engine.scalping.mechanistic_entry_runtime_policy import (
        load_effective,
        digest,
    )
    from src.engine.observation_source_quality_audit import _raw_generation

    def same_source(source: dict) -> bool:
        path = existing_or_gzip_path(Path(source["path"]))
        before = _raw_generation(path)
        if before and before == source.get("generation"):
            return True
        expected = source.get("logical_content_sha256")
        if not before or not expected:
            return False
        # Verified compression is not a new source generation. Compare logical
        # bytes only when the original filesystem generation no longer exists.
        content_hash = hashlib.sha256()
        opener = gzip.open if path.suffix == ".gz" else open
        with opener(path, "rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                content_hash.update(chunk)
        return before == _raw_generation(path) and content_hash.hexdigest() == expected

    result = json.loads(json.dumps(receipt))
    measurement = result.setdefault("compact_auxiliary_policy_measurement", {})
    partitions = measurement.setdefault("partitions", [])
    for partition in partitions:
        partition["source_date"] = target_date
    history = []
    if not incumbent:
        result["compact_history_receipts"] = history
        return result
    measurement["prompt_version"] = incumbent["ai_policy"].get("prompt_version")
    measurement["measurement_allowed"] = any(
        partition.get("prompt_version") == measurement["prompt_version"]
        and partition.get("measurement_allowed") is True
        for partition in partitions
    )
    dates = sorted(
        {
            str(row.get("source_date") or "")
            for row in rows
            if CLEAN_BASELINE_DATE <= str(row.get("source_date") or "") < target_date
        }
    )[-19:]
    for day in dates:
        path = (
            data_root
            / "report"
            / "observation_source_quality_audit"
            / f"observation_source_quality_audit_{day}.json"
        )
        entry = {"source_date": day, "path": str(path), "allowed": False}
        try:
            audit = _load_json(path)
            consumption = audit.get("machine_ai_natural_source_consumption") or {}
            manifest = consumption.get("source_manifest") or {}
            sources = consumption.get("sources") or {}
            prior = load_effective(data_root=data_root, target_date=day)
            valid = bool(
                audit.get("audit_phase") == "final"
                and consumption.get("target_date") == day
                and consumption.get("tuning_input_allowed") is True
                and manifest.get("source_manifest_sha256")
                == _canonical_sha256(manifest.get("sources") or {})
                and sources
                and all(
                    same_source(source)
                    for source in sources.values()
                    if source.get("exists")
                )
                and prior
                and digest(prior["machine_policy"])
                == digest(incumbent["machine_policy"])
                and prior["ai_policy"] == incumbent["ai_policy"]
            )
            entry.update(
                allowed=valid,
                source_manifest_sha256=manifest.get("source_manifest_sha256"),
                audit_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            )
            if valid:
                for partition in (
                    consumption.get("compact_auxiliary_policy_measurement") or {}
                ).get("partitions") or []:
                    if (
                        partition.get("measurement_allowed") is True
                        and partition.get("machine_bundle_sha256")
                        == prior["bundle_sha256"]
                    ):
                        partitions.append({**partition, "source_date": day})
        except (OSError, EOFError, ValueError, KeyError, TypeError):
            entry["reason"] = "historical_source_or_policy_invalid"
        history.append(entry)
    result["compact_history_receipts"] = history
    result["compact_history_receipts_sha256"] = _canonical_sha256(history)
    result["compact_window_policy"] = (
        "current_date_plus_latest_19_observed_dates_same_machine_and_ai_policy"
    )
    return result


def build_machine_decision_case_table(
    rows: list[dict],
    *,
    capture_census: dict | None = None,
    source_receipt: dict | None = None,
) -> dict:
    """Classify machine timing outcomes without creating trading authority.

    Rows are exact runtime machine captures matured by the existing
    action-neutral entry path labeler. Exact snapshot identity connects the
    machine decision to the composed AI trace and downstream lifecycle without
    merging their separate authorities.
    """

    from src.engine.ai_prompt_contracts import (
        ENTRY_MACHINE_AUXILIARY_COMPACT_OPPORTUNITY_PROMPT_VERSION,
        ENTRY_MACHINE_AUXILIARY_COMPACT_PROMPT_VERSION,
        ENTRY_MACHINE_AUXILIARY_COMPACT_RISK_PROMPT_VERSION,
        MACHINE_AUXILIARY_COMPACT_ENTRY_PROMPT_VERSIONS,
    )

    source_receipt = dict(source_receipt or {})
    terminal_tuning_gate = _as_dict(source_receipt.get("machine_terminal_tuning_gate"))
    terminal_lineage_excluded_keys = {
        str(key)
        for key in (
            list(terminal_tuning_gate.get("excluded_evaluation_keys") or [])
            + list(terminal_tuning_gate.get("pending_evaluation_keys") or [])
        )
        if str(key)
    }
    compact_measurement = _as_dict(
        source_receipt.get("compact_auxiliary_policy_measurement")
    )
    measured_compact_version = str(compact_measurement.get("prompt_version") or "")
    incumbent_compact_version = (
        measured_compact_version
        if measured_compact_version in MACHINE_AUXILIARY_COMPACT_ENTRY_PROMPT_VERSIONS
        else ENTRY_MACHINE_AUXILIARY_COMPACT_PROMPT_VERSION
    )
    declared_compact_partitions = [
        partition
        for partition in compact_measurement.get("partitions") or []
        if isinstance(partition, dict)
    ]
    allowed_compact_partition_keys = {
        (
            str(
                partition.get("source_date") or source_receipt.get("target_date") or ""
            ),
            str(partition.get("prompt_version") or ""),
            str(partition.get("effective_venue") or "UNKNOWN").upper(),
            str(partition.get("session_bucket") or "UNKNOWN").upper(),
            str(partition.get("machine_bundle_sha256") or "UNKNOWN"),
        )
        for partition in declared_compact_partitions
        if partition.get("measurement_allowed") is True
    }

    classifications: Counter[str] = Counter()
    action_counts: Counter[str] = Counter()
    source_date_counts: Counter[str] = Counter()
    hierarchy_selection_counts: Counter[str] = Counter()
    compact_screen_outcomes: Counter[str] = Counter()
    compact_exclusions: Counter[str] = Counter()
    compact_current_version_screened_count = 0
    compact_provider_called_count = 0
    compact_provider_not_called_count = 0
    compact_semantic_valid_count = 0
    compact_verdict_counts: Counter[str] = Counter()
    machine_enter_now_count = 0
    ai_screen_routing_counts: Counter[str] = Counter()
    compact_outcome_evaluable_count = 0
    compact_prompt_version_counts: Counter[str] = Counter()
    selected_child_rule_ids: set[str] = set()
    cases: list[dict] = []
    seen_attempts: dict[tuple[str, str, str, str, str, str], set[str]] = {}
    duplicate_same_action_collapsed_count = 0
    conflicting_evaluation_keys = _machine_conflicting_evaluation_keys(rows)
    conflicting_attempt_identity_count = len(conflicting_evaluation_keys)
    incomplete_attempt_identity_count = 0
    for row in sorted(rows, key=lambda item: str(item.get("decision_ts") or "")):
        action = str(row.get("machine_action") or "").upper()
        exact_attempt_identity_complete = all(
            str(value or "").strip()
            for value in (
                row.get("scanner_promotion_id"),
                row.get("evaluation_attempt_id") or row.get("decision_trace_id"),
                row.get("stock_code"),
                row.get("effective_venue"),
                row.get("session_bucket"),
                row.get("bundle_sha256"),
            )
        )
        if not exact_attempt_identity_complete:
            incomplete_attempt_identity_count += 1
        attempt_key = (
            str(row.get("scanner_promotion_id") or ""),
            str(row.get("evaluation_attempt_id") or row.get("decision_trace_id") or ""),
            str(row.get("stock_code") or ""),
            str(row.get("effective_venue") or ""),
            str(row.get("session_bucket") or ""),
            str(row.get("bundle_sha256") or ""),
        )
        previous = seen_attempts.setdefault(attempt_key, set())
        current_identity = _machine_learning_fingerprint(row)
        evaluation_key = _machine_evaluation_key(row)
        conflict_excluded = evaluation_key in conflicting_evaluation_keys
        policy_learning_excluded = (
            evaluation_key in terminal_lineage_excluded_keys or conflict_excluded
        )
        if previous:
            if current_identity in previous:
                duplicate_same_action_collapsed_count += 1
                continue
            if not evaluation_key:
                conflicting_attempt_identity_count += 1
        previous.add(current_identity)
        path = _as_dict(row.get("entry_quality_path"))
        label = str(path.get("entry_quality_label") or "CENSORED_OR_SOURCE_GAP")
        if path.get("status") != "evaluable" or label == "CENSORED_OR_SOURCE_GAP":
            classification = "source_gap"
        elif action == "ENTER_NOW":
            classification = {
                "CLEAN_FAST_PROFIT": "good_entry_candidate",
                "PROFITABLE_BUT_LATE": "late_entry_candidate",
                "PROFIT_AFTER_DEEP_ADVERSE": "deep_adverse_entry_candidate",
                "PROFIT_AFTER_SIDEWAYS": "sideways_entry_candidate",
                "CLEAN_FAST_LOSS_OR_ADVERSE": "false_positive_entry_candidate",
            }.get(label, "source_gap")
        elif action in {"BLOCK", "RECHECK"}:
            classification = {
                "CLEAN_FAST_PROFIT": "missed_opportunity_candidate",
                "PROFITABLE_BUT_LATE": "delayed_opportunity_candidate",
                "PROFIT_AFTER_DEEP_ADVERSE": "poor_timing_avoidance_candidate",
                "PROFIT_AFTER_SIDEWAYS": "sideways_avoidance_candidate",
                "CLEAN_FAST_LOSS_OR_ADVERSE": "correct_avoidance_candidate",
            }.get(label, "source_gap")
        else:
            classification = "source_gap"
        action_counts[action or "UNKNOWN"] += 1
        source_date_counts[str(row.get("source_date") or "UNKNOWN")] += 1
        classifications[classification] += 1
        hierarchy = _as_dict(row.get("machine_hierarchy_selection"))
        hierarchy_level = str(hierarchy.get("level") or "unknown")
        hierarchy_selection_counts[hierarchy_level] += 1
        rule_id = str(hierarchy.get("rule_id") or "").strip()
        if rule_id and hierarchy_level != "common":
            selected_child_rule_ids.add(rule_id)
        ai_guard = _as_dict(row.get("ai_and_final_guard"))
        if action == "ENTER_NOW":
            machine_enter_now_count += 1
            observed_prompt_version = str(ai_guard.get("prompt_version") or "")
            if observed_prompt_version == incumbent_compact_version:
                ai_screen_routing_counts["current_compact_prompt"] += 1
            elif (
                observed_prompt_version
                in MACHINE_AUXILIARY_COMPACT_ENTRY_PROMPT_VERSIONS
            ):
                ai_screen_routing_counts["other_registered_compact_prompt"] += 1
            elif observed_prompt_version:
                ai_screen_routing_counts["legacy_or_unknown_prompt"] += 1
            else:
                ai_screen_routing_counts["prompt_version_missing"] += 1
            if (
                observed_prompt_version
                in MACHINE_AUXILIARY_COMPACT_ENTRY_PROMPT_VERSIONS
            ):
                compact_prompt_version_counts[observed_prompt_version] += 1
                # Never let an older compact or legacy prompt generation tune
                # the current compact contract. Each successor starts with a
                # fresh exact-version denominator.
                if observed_prompt_version == incumbent_compact_version:
                    compact_current_version_screened_count += 1
                    if ai_guard.get("provider_called") is True:
                        compact_provider_called_count += 1
                    else:
                        compact_provider_not_called_count += 1
                    partition_key = (
                        (
                            str(row.get("source_date") or "")
                            if source_receipt.get("target_date")
                            else ""
                        ),
                        observed_prompt_version,
                        str(row.get("effective_venue") or "UNKNOWN").upper(),
                        str(row.get("session_bucket") or "UNKNOWN").upper(),
                        str(row.get("bundle_sha256") or "UNKNOWN"),
                    )
                    partition_allowed = bool(
                        not declared_compact_partitions
                        or partition_key in allowed_compact_partition_keys
                    )
                    if policy_learning_excluded:
                        compact_screen_outcomes[
                            "|".join((
                                "CONFLICTING_EXACT_ATTEMPT" if conflict_excluded
                                else "TERMINAL_LINEAGE_EXCLUDED", label
                            ))
                        ] += 1
                        compact_exclusions[
                            "conflicting_exact_attempt" if conflict_excluded
                            else "terminal_lineage_unresolved"
                        ] += 1
                    elif not partition_allowed:
                        compact_screen_outcomes[
                            "|".join(("SOURCE_PARTITION_NOT_ALLOWED", label))
                        ] += 1
                        compact_exclusions["source_partition_not_allowed"] += 1
                    elif ai_guard.get("provider_called") is not True:
                        compact_screen_outcomes["|".join(("NOT_EVALUATED", label))] += 1
                        compact_exclusions["provider_not_called"] += 1
                    else:
                        semantic_valid = bool(
                            ai_guard.get("decision_quality_contract_status") == "pass"
                            and ai_guard.get("semantic_validation_status")
                            in {None, "pass"}
                        )
                        compact_verdict = str(
                            ai_guard.get("ai_risk_verdict") or ""
                        ).upper()
                        semantic_valid = bool(
                            semantic_valid
                            and compact_verdict
                            in {"PASS", "VETO", "CAUTION", "INSUFFICIENT"}
                        )
                        if semantic_valid:
                            compact_semantic_valid_count += 1
                            compact_verdict_counts[compact_verdict] += 1
                        compact_screen_outcomes[
                            "|".join(
                                (
                                    (
                                        compact_verdict
                                        if semantic_valid
                                        else "SEMANTIC_INVALID"
                                    )
                                    or "UNCLASSIFIED",
                                    label,
                                )
                            )
                        ] += 1
                        if not semantic_valid:
                            compact_exclusions["semantic_invalid"] += 1
                        elif compact_verdict == "INSUFFICIENT":
                            compact_exclusions["source_gap_router_verdict"] += 1
                        elif compact_verdict == "CAUTION" and (
                            ai_guard.get("followup_disposition") != "ai_caution_bounded_recheck"
                            or ai_guard.get("observed_actual_order_submitted") is not False
                        ):
                            compact_exclusions["bounded_recheck_nonexposure_unproven"] += 1
                        elif path.get("status") != "evaluable":
                            compact_exclusions["outcome_not_evaluable"] += 1
                        elif label == "CENSORED_OR_SOURCE_GAP":
                            compact_exclusions["outcome_censored_or_source_gap"] += 1
                        else:
                            compact_outcome_evaluable_count += 1
                            if (
                                _number(path.get("conservative_execution_cost_pct"))
                                is None
                            ):
                                compact_exclusions["cost_contract_missing"] += 1
                            elif path.get("first_hit") not in {
                                "net_target_first",
                                "exact_stop_first",
                            }:
                                compact_exclusions["terminal_path_not_evaluable"] += 1
        cases.append(
            {
                "evaluation_key": evaluation_key or None,
                "decision_trace_id": row.get("decision_trace_id"),
                "ai_decision_trace_id": row.get("ai_decision_trace_id"),
                "evaluation_attempt_id": row.get("evaluation_attempt_id"),
                "evaluation_attempt_identity_source": row.get(
                    "evaluation_attempt_identity_source"
                ),
                "record_id": row.get("record_id"),
                "scanner_promotion_id": row.get("scanner_promotion_id"),
                "scanner_promotion_identity_source": row.get(
                    "scanner_promotion_identity_source"
                ),
                "exact_attempt_identity_complete": exact_attempt_identity_complete,
                "scanner_promotion_ids": row.get("scanner_promotion_ids") or [],
                "decision_snapshot_id": row.get("decision_snapshot_id"),
                "decision_ts": row.get("decision_ts"),
                "source_date": row.get("source_date"),
                "stock_code": row.get("stock_code"),
                "effective_venue": row.get("effective_venue"),
                "session_bucket": row.get("session_bucket"),
                "bundle_sha256": row.get("bundle_sha256"),
                "machine_action": action,
                "machine_reason": row.get("machine_reason"),
                "machine_core_comparison": row.get("machine_core_comparison"),
                "machine_applied_thresholds": row.get("machine_applied_thresholds"),
                "machine_liquidity_inputs": row.get("machine_liquidity_inputs"),
                "microstructure_evaluation_binding": row.get("microstructure_evaluation_binding") or {},
                "hierarchy_selection": row.get("machine_hierarchy_selection"),
                "entry_quality_label": label,
                "entry_quality_path": path,
                "case_classification": classification,
                "cost_evidence": _as_dict(row.get("comparison")).get("cost_evidence"),
                "cost_adjusted_target_pct": path.get("gross_net_target_pct"),
                "time_to_net_target_sec": path.get("time_to_net_target_sec"),
                "time_to_exact_stop_sec": path.get("time_to_exact_stop_sec"),
                "pre_target_mae_pct": path.get("pre_target_mae_pct"),
                "pre_target_underwater_ratio": path.get("pre_target_underwater_ratio"),
                "pre_target_neutral_dwell_ratio": path.get(
                    "pre_target_neutral_dwell_ratio"
                ),
                "checkpoint_metrics": path.get("checkpoints"),
                "outcome_horizon_metrics": row.get("outcome_horizon_metrics") or {},
                "watch_timing": row.get("watch_timing") or {},
                "path_authority": path.get("path_authority"),
                "ai_and_final_guard_join_status": _as_dict(
                    row.get("ai_and_final_guard")
                ).get("join_status"),
                "ai_and_final_guard": row.get("ai_and_final_guard") or {},
                "compact_partition_eligible": (
                    not declared_compact_partitions
                    or (
                        (
                            str(row.get("source_date") or "")
                            if source_receipt.get("target_date")
                            else ""
                        ),
                        str(ai_guard.get("prompt_version") or ""),
                        str(row.get("effective_venue") or "UNKNOWN").upper(),
                        str(row.get("session_bucket") or "UNKNOWN").upper(),
                        str(row.get("bundle_sha256") or "UNKNOWN"),
                    )
                    in allowed_compact_partition_keys
                ),
                "policy_learning_excluded": policy_learning_excluded,
                "policy_learning_exclusion_reason": (
                    "conflicting_exact_attempt" if conflict_excluded
                    else "terminal_lineage_unresolved" if policy_learning_excluded
                    else None
                ),
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
            }
        )
    source_tuning_allowed = source_receipt.get("tuning_input_allowed") is True
    machine_tuning_allowed = (
        source_receipt.get("machine_threshold_tuning_input_allowed") is True
    )
    receipt_target_date = str(source_receipt.get("target_date") or "")
    terminal_gate_required = receipt_target_date >= "2026-09-15"
    from src.engine.scalping.mechanistic_entry_runtime_policy import compact_terminal_gate_allowed

    terminal_gate_allowed = compact_terminal_gate_allowed(source_receipt)
    compact_tuning_input_allowed = bool(
        source_tuning_allowed
        and terminal_gate_allowed
        and compact_measurement.get("measurement_allowed") is True
    )
    compact_screened_count = sum(compact_screen_outcomes.values())
    compact_unclassified_count = sum(
        count
        for key, count in compact_screen_outcomes.items()
        if key.startswith(("UNCLASSIFIED|", "SEMANTIC_INVALID|", "NOT_EVALUATED|"))
    )
    missed_veto_count = compact_screen_outcomes.get("VETO|CLEAN_FAST_PROFIT", 0)
    dangerous_pass_count = sum(
        compact_screen_outcomes.get(key, 0)
        for key in (
            "PASS|CLEAN_FAST_LOSS_OR_ADVERSE",
            "PASS|PROFIT_AFTER_DEEP_ADVERSE",
        )
    )
    economic_outcomes = Counter()
    economic_values: list[float] = []
    opportunity_values: list[float] = []
    outcome_times_sec: list[float] = []
    pass_loss_values: list[float] = []
    missed_profit_values: list[float] = []
    missed_caution_values: list[float] = []
    avoided_nonentry_loss_values: list[float] = []
    for row in cases:
        ai_guard = _as_dict(row.get("ai_and_final_guard"))
        path = _as_dict(row.get("entry_quality_path"))
        version = str(ai_guard.get("prompt_version") or "")
        verdict = str(ai_guard.get("ai_risk_verdict") or "").upper()
        semantic_valid = bool(
            ai_guard.get("decision_quality_contract_status") == "pass"
            and ai_guard.get("semantic_validation_status") in {None, "pass"}
        )
        if (
            row.get("policy_learning_excluded") is True
            or (
                terminal_gate_required
                and row.get("exact_attempt_identity_complete") is not True
            )
            or row.get("machine_action") != "ENTER_NOW"
            or ai_guard.get("provider_called") is not True
            or version != incumbent_compact_version
            or row.get("compact_partition_eligible") is not True
            or not semantic_valid
            or verdict not in {"PASS", "VETO", "CAUTION"}
            or (verdict == "CAUTION" and (
                ai_guard.get("followup_disposition") != "ai_caution_bounded_recheck"
                or ai_guard.get("observed_actual_order_submitted") is not False
            ))
            or path.get("status") != "evaluable"
            or _number(path.get("conservative_execution_cost_pct")) is None
            or path.get("first_hit") not in {"net_target_first", "exact_stop_first"}
        ):
            continue
        execution_cost = _number(path.get("conservative_execution_cost_pct"))
        boundary_value = (
            _number(path.get("gross_net_target_pct"))
            if path.get("first_hit") == "net_target_first"
            else _number(path.get("exact_stop_distance_pct"))
        )
        if boundary_value is None or execution_cost is None:
            compact_exclusions["economic_value_missing"] += 1
            continue
        value = boundary_value - execution_cost
        economic_outcomes[f"{verdict}|{row.get('entry_quality_label')}"] += 1
        opportunity_values.append(value)
        economic_values.append(value if verdict == "PASS" else 0.0)
        if verdict in {"VETO", "CAUTION"} and value < 0:
            avoided_nonentry_loss_values.append(-value)
        outcome_time = _number(
            path.get("time_to_net_target_sec")
            if path.get("first_hit") == "net_target_first"
            else path.get("time_to_exact_stop_sec")
        )
        if outcome_time is not None:
            outcome_times_sec.append(outcome_time)
        if verdict == "PASS" and value < 0:
            pass_loss_values.append(value)
        if (
            verdict == "VETO"
            and value > 0
            and row.get("entry_quality_label") == "CLEAN_FAST_PROFIT"
        ):
            missed_profit_values.append(value)
        if verdict == "CAUTION" and value > 0 and row.get("entry_quality_label") == "CLEAN_FAST_PROFIT":
            missed_caution_values.append(value)
    economic_eligible_count = sum(economic_outcomes.values())
    evaluable_veto_count = sum(
        count for key, count in economic_outcomes.items() if key.startswith("VETO|")
    )
    evaluable_pass_count = sum(
        count for key, count in economic_outcomes.items() if key.startswith("PASS|")
    )
    evaluable_caution_count = sum(
        count for key, count in economic_outcomes.items() if key.startswith("CAUTION|")
    )
    economic_missed_veto_count = economic_outcomes.get("VETO|CLEAN_FAST_PROFIT", 0)
    economic_dangerous_pass_count = sum(
        economic_outcomes.get(key, 0)
        for key in (
            "PASS|CLEAN_FAST_LOSS_OR_ADVERSE",
            "PASS|PROFIT_AFTER_DEEP_ADVERSE",
        )
    )
    missed_veto_rate = (
        economic_missed_veto_count / evaluable_veto_count
        if evaluable_veto_count
        else None
    )
    dangerous_pass_rate = (
        economic_dangerous_pass_count / evaluable_pass_count
        if evaluable_pass_count
        else None
    )
    minimum_economic_count = 20
    minimum_error_count = 3
    minimum_relevant_denominator = 5
    minimum_error_rate = 0.25
    minimum_rate_margin = 0.10
    material_tail_loss_pct = -1.0
    material_tail_pass_count = sum(
        value <= material_tail_loss_pct for value in pass_loss_values
    )
    incumbent_partition_ids = sorted(
        str(partition.get("partition_id") or "")
        for partition in compact_measurement.get("partitions") or []
        if isinstance(partition, dict)
        and partition.get("prompt_version") == incumbent_compact_version
        and partition.get("measurement_allowed") is True
        and partition.get("partition_id")
    )
    economic_outcome_counts = dict(sorted(economic_outcomes.items()))
    economic_outcome_counts_sha256 = _canonical_sha256(economic_outcome_counts)
    selected_compact_version = incumbent_compact_version
    if not source_tuning_allowed:
        compact_tuning_direction = "repair_source_quality_before_automatic_selection"
    elif compact_measurement.get("measurement_status") == "not_observed_on_source_date":
        compact_tuning_direction = "carry_incumbent_compact_not_observed"
    elif not compact_tuning_input_allowed:
        compact_tuning_direction = "isolate_invalid_compact_partition_and_carry"
    elif economic_eligible_count < minimum_economic_count:
        compact_tuning_direction = "collect_current_version_natural_evidence"
    else:
        compact_tuning_direction = "carry_balanced_compact_contract"
    compact_selection_eligible = bool(
        compact_tuning_input_allowed
        and economic_eligible_count >= minimum_economic_count
        and conflicting_attempt_identity_count == len(conflicting_evaluation_keys)
    )
    if not compact_selection_eligible:
        selected_compact_version = incumbent_compact_version
    from src.engine.scalping.mechanistic_entry_runtime_policy import (
        compact_economic_direction,
    )

    economic_direction_inputs = {
        "schema": "compact_auxiliary_router_economic_selection_v3",
        "verdict_x_action_neutral_outcome_counts": economic_outcome_counts,
        "economic_eligible_count": economic_eligible_count,
        "evaluable_veto_count": evaluable_veto_count,
        "evaluable_pass_count": evaluable_pass_count,
        "missed_profit_veto_count": economic_missed_veto_count,
        "dangerous_pass_count": economic_dangerous_pass_count,
        "missed_veto_rate": missed_veto_rate,
        "dangerous_pass_rate": dangerous_pass_rate,
        "material_tail_pass_count": material_tail_pass_count,
        "missed_profit_veto_net_sum_pct": sum(missed_profit_values),
        "dangerous_pass_loss_sum_pct": -sum(pass_loss_values),
        "evaluable_caution_count": evaluable_caution_count,
        "missed_profit_caution_count": len(missed_caution_values),
        "missed_profit_caution_net_sum_pct": sum(missed_caution_values),
        "avoided_nonentry_loss_sum_pct": sum(avoided_nonentry_loss_values),
        "caution_opportunity_cost_role": "exact_enter_checkpoint_foregone_opportunity_not_terminal_episode_loss",
        "caution_is_not_veto": True,
        "insufficient_is_source_repair_only": True,
    }
    if compact_selection_eligible:
        compact_tuning_direction = compact_economic_direction(economic_direction_inputs)
        selected_compact_version = {
            "select_opportunity_preservation_variant": ENTRY_MACHINE_AUXILIARY_COMPACT_OPPORTUNITY_PROMPT_VERSION,
            "select_material_risk_specificity_variant": ENTRY_MACHINE_AUXILIARY_COMPACT_RISK_PROMPT_VERSION,
        }.get(compact_tuning_direction, incumbent_compact_version)
    from src.engine.scalping.microstructure_reaction_context import summarize_machine_microstructure_evaluation

    return {
        "schema": MACHINE_DECISION_CASE_TABLE_SCHEMA,
        "microstructure_evaluation": summarize_machine_microstructure_evaluation(
            cases,
            source_receipt={
                **source_receipt,
                "machine_threshold_tuning_input_allowed": machine_tuning_allowed and conflicting_attempt_identity_count == len(conflicting_evaluation_keys),
                "tuning_input_allowed": compact_tuning_input_allowed,
            },
            capture_census=capture_census,
        ),
        "status": (
            "evaluable"
            if cases
            else (
                "source_gap_blocked_no_evaluable_cases"
                if int(_as_dict(capture_census).get("captured") or 0) > 0
                else "source_gap_no_machine_captures"
            )
        ),
        "input_evaluable_observation_count": len(rows),
        "case_count": len(cases),
        "duplicate_same_action_collapsed_count": (
            duplicate_same_action_collapsed_count
        ),
        "conflicting_attempt_identity_count": conflicting_attempt_identity_count,
        "conflicting_evaluation_keys": sorted(conflicting_evaluation_keys),
        "conflict_locations_complete": (
            conflicting_attempt_identity_count == len(conflicting_evaluation_keys)
        ),
        "incomplete_attempt_identity_count": incomplete_attempt_identity_count,
        "policy_learning_eligible_observation_count": (
            sum(
                case.get("exact_attempt_identity_complete") is True
                and case.get("policy_learning_excluded") is not True
                for case in cases
            )
            if conflicting_attempt_identity_count == len(conflicting_evaluation_keys)
            and machine_tuning_allowed
            else 0
        ),
        "terminal_lineage_exclusion": {
            "source_gate": terminal_tuning_gate,
            "excluded_case_count": sum(
                case.get("policy_learning_excluded") is True for case in cases
            ),
            "denominator_preserved": len(cases)
            == sum(case.get("policy_learning_excluded") is True for case in cases)
            + sum(case.get("policy_learning_excluded") is not True for case in cases),
            "unresolved_terminal_is_not_imputed": True,
        },
        "machine_capture_census": dict(capture_census or {}),
        "machine_ai_natural_source_receipt": source_receipt,
        "compact_auxiliary_policy_measurement": compact_measurement,
        "compact_auxiliary_screen_outcomes": {
            "current_prompt_version": incumbent_compact_version,
            "screened_enter_now_count": compact_screened_count,
            "enter_now_requiring_ai_screen_count": (
                compact_current_version_screened_count
            ),
            "provider_called_count": compact_provider_called_count,
            "provider_not_called_count": compact_provider_not_called_count,
            "terminal_verdict_counts": dict(sorted(compact_verdict_counts.items())),
            "screen_attempt_conservation": {
                "expected_enter_now_count": compact_current_version_screened_count,
                "terminal_classified_count": compact_screened_count,
                "provider_called_count": compact_provider_called_count,
                "provider_not_called_count": compact_provider_not_called_count,
                "denominator_preserved": (
                    compact_current_version_screened_count == compact_screened_count
                ),
                "not_evaluated_is_not_veto": True,
            },
            "all_machine_enter_ai_routing": {
                "machine_enter_now_count": machine_enter_now_count,
                "routing_counts": dict(sorted(ai_screen_routing_counts.items())),
                "denominator_preserved": (
                    machine_enter_now_count == sum(ai_screen_routing_counts.values())
                ),
                "mixed_prompt_generations_are_not_merged": True,
            },
            "observed_compact_prompt_version_counts": dict(
                sorted(compact_prompt_version_counts.items())
            ),
            "verdict_x_action_neutral_outcome_counts": dict(
                sorted(compact_screen_outcomes.items())
            ),
            "missed_veto_count": missed_veto_count,
            "dangerous_pass_count": dangerous_pass_count,
            "semantic_unclassified_count": compact_unclassified_count,
            "economic_contract": {
                **economic_direction_inputs,
                "primary_decision_metric": "foregone_nonentry_net_sum_pct_vs_dangerous_pass_and_avoided_nonentry_loss_sum_pct",
                "rate_margin_used_for_selection": False,
                "material_tail_alert": material_tail_pass_count > 0,
                "schema": "compact_auxiliary_router_economic_selection_v3",
                "screened_total": compact_current_version_screened_count,
                "denominator_preserved": (
                    compact_current_version_screened_count
                    == economic_eligible_count + sum(compact_exclusions.values())
                ),
                "semantic_valid_count": compact_semantic_valid_count,
                "outcome_evaluable_count": compact_outcome_evaluable_count,
                "economic_eligible_count": economic_eligible_count,
                "verdict_x_action_neutral_outcome_counts": economic_outcome_counts,
                "verdict_x_action_neutral_outcome_counts_sha256": (
                    economic_outcome_counts_sha256
                ),
                "exclusion_counts": dict(sorted(compact_exclusions.items())),
                "evaluable_veto_count": evaluable_veto_count,
                "evaluable_pass_count": evaluable_pass_count,
                "missed_profit_veto_count": economic_missed_veto_count,
                "dangerous_pass_count": economic_dangerous_pass_count,
                "missed_veto_rate": missed_veto_rate,
                "dangerous_pass_rate": dangerous_pass_rate,
                "material_tail_loss_pct": material_tail_loss_pct,
                "material_tail_pass_count": material_tail_pass_count,
                "worst_pass_counterfactual_net_pct": (
                    min(pass_loss_values) if pass_loss_values else None
                ),
                "mean_time_to_boundary_sec": (
                    sum(outcome_times_sec) / len(outcome_times_sec)
                    if outcome_times_sec
                    else None
                ),
                "screened_policy_counterfactual_net_ev_pct": (
                    sum(economic_values) / len(economic_values)
                    if economic_values
                    else None
                ),
                "available_opportunity_counterfactual_net_ev_pct": (
                    sum(opportunity_values) / len(opportunity_values)
                    if opportunity_values
                    else None
                ),
                "counterfactual_not_realized_pnl": True,
                "missing_economics_imputed": False,
            },
            "tuning_interpretation": (
                "measure_exact_compact_version_auxiliary_pass_veto_quality; "
                "machine_threshold_challenger_remains_under_existing_cost_"
                "holdout_gate"
            ),
            "automatic_successor_selection": {
                "economic_direction_rule": "cost_weighted_nonentry_router_feedback_v2",
                "history_receipts_sha256": source_receipt.get(
                    "compact_history_receipts_sha256"
                ),
                "recommendation_id": "compact_auxiliary_prompt_automatic_successor_v2",
                "contract_version": "compact_auxiliary_router_economic_selection_v3",
                "incumbent_prompt_version": incumbent_compact_version,
                "selected_prompt_version": selected_compact_version,
                "source_manifest_sha256": source_receipt.get("source_manifest_sha256"),
                "incumbent_partition_ids": incumbent_partition_ids,
                "economic_outcome_counts_sha256": economic_outcome_counts_sha256,
                "minimum_economic_eligible_count": minimum_economic_count,
                "minimum_error_count": minimum_error_count,
                "minimum_relevant_denominator": minimum_relevant_denominator,
                "minimum_error_rate": minimum_error_rate,
                "minimum_rate_margin": minimum_rate_margin,
                "eligible": compact_selection_eligible,
                "direction": compact_tuning_direction,
                "runtime_effect": True,
                "allowed_runtime_apply": True,
                "effective_date_owner": (
                    "mechanistic_entry_runtime_policy_next_trading_date_publisher"
                ),
                "selection_contract": (
                    "bounded_registered_variant_exact_incumbent_only_no_freeform_edit"
                ),
            },
            "prompt_body_tuning": "bounded_automatic_versioned_successor_enabled",
            "legacy_or_prior_compact_rows_affect_current_direction": False,
        },
        "machine_action_counts": dict(sorted(action_counts.items())),
        "case_classification_counts": dict(sorted(classifications.items())),
        "source_date_counts": dict(sorted(source_date_counts.items())),
        "hierarchy_selection_counts": dict(sorted(hierarchy_selection_counts.items())),
        "observed_selected_child_rule_count": len(selected_child_rule_ids),
        "observed_selected_child_rule_ids": sorted(selected_child_rule_ids),
        "policy_learning_exact_enter_keys": (
            sorted(
                {
                    str(case.get("evaluation_key"))
                    for case in cases
                    if case.get("machine_action") == "ENTER_NOW"
                    and case.get("policy_learning_excluded") is not True
                    and case.get("exact_attempt_identity_complete") is True
                    and case.get("evaluation_key")
                }
            )
            if terminal_gate_allowed
            else []
        ),
        "case_unit": "exact_market_snapshot_attempt_x_venue_x_session_x_bundle",
        "legacy_60_second_same_action_collapse_disabled": True,
        "comparison_objective": (
            "cost_adjusted_net_edge_at_least_0.10pct_with_fast_target_"
            "deep_adverse_and_sideways_separated"
        ),
        "ai_and_final_guard_are_separate_consumers": True,
        "ai_and_final_guard_exact_join_attempted": True,
        "machine_ai_populations_are_separate": True,
        "rows": cases[-200:],
        "row_export_limit": 200,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def validate_hierarchy_candidate(
    extension: dict,
    *,
    source_date: str,
    cohort: tuple[str, str] = ("KRX", "KRX_REGULAR"),
) -> list[str]:
    if not isinstance(extension.get("evaluations"), list):
        return ["candidate_evaluations_invalid"]
    candidate = extension.get("policy_candidate")
    if not isinstance(candidate, dict):
        return ["candidate_missing"]
    body = {k: v for k, v in candidate.items() if k != "candidate_content_sha256"}
    full_population = candidate.get("evaluation_contract") == (
        "hierarchy_full_population_cost_adjusted_10bp_paired_v3"
    )
    if (
        _as_dict(candidate.get("threshold_policy")).get("version") == MECHANISTIC_FULL_POPULATION_POLICY_VERSION
        and not full_population
    ):
        return ["candidate_full_population_evaluation_contract_missing"]
    if full_population:
        parent = _as_dict(candidate.get("incumbent_machine_policy"))
        contract = _as_dict(candidate.get("population_source_contract"))
        if (
            not mechanistic_scope_supported(*cohort)
            or contract.get("cohort", ["KRX", "KRX_REGULAR"]) != list(cohort)
            or validate_mechanistic_entry_threshold_policy(parent)
            or candidate.get("incumbent_machine_policy_sha256") != _canonical_sha256(parent)
            or contract.get("schema") != "machine_common_refinement_population_v1"
            or contract.get("input_row_disposition_complete") is not True
            or candidate.get("population_source_contract_sha256") != _canonical_sha256(contract)
            or _as_dict(candidate.get("threshold_policy")).get("version") != MECHANISTIC_FULL_POPULATION_POLICY_VERSION
            or _as_dict(candidate.get("threshold_policy")).get("thresholds") != parent.get("thresholds")
        ):
            return ["candidate_full_population_source_or_parent_invalid"]
    errors = validate_mechanistic_entry_threshold_policy(
        candidate.get("threshold_policy")
    )
    if (
        not mechanistic_scope_supported(*cohort)
        or extension.get("cohort", ["KRX", "KRX_REGULAR"]) != list(cohort)
        or candidate.get("cohort", ["KRX", "KRX_REGULAR"]) != list(cohort)
    ):
        errors.append("candidate_cohort_invalid")
    train, test = candidate.get("calibration_dates"), candidate.get("holdout_dates")
    if (
        extension.get("schema") != MECHANISTIC_HIERARCHY_SCHEMA
        or extension.get("promotion_pass") is not True
        or candidate.get("source_date") != source_date
        or candidate.get("candidate_content_sha256") != _canonical_sha256(body)
        or candidate.get("evaluations_sha256")
        != _canonical_sha256(extension.get("evaluations"))
        or not isinstance(train, list)
        or not isinstance(test, list)
        or len(train) < 3
        or len(test) < 2
        or not all(
            isinstance(d, str) and CLEAN_BASELINE_DATE <= d <= source_date
            for d in train + test
        )
        or sorted(set(train)) != train
        or sorted(set(test)) != test
        or max(train) >= min(test)
        or min(test) <= MECHANISTIC_FLOW_BOUNDARY_FREEZE_DATE
        or any(
            candidate.get(k) is not v
            for k, v in (
                ("runtime_effect", False),
                ("allowed_runtime_apply", False),
                ("actual_order_submitted", False),
                ("broker_order_forbidden", True),
            )
        )
    ):
        errors.append("candidate_source_or_authority_invalid")
    rules = _as_dict(_as_dict(candidate.get("threshold_policy")).get("hierarchy")).get(
        "rules"
    )
    qualified = [
        e.get("rule")
        for e in extension.get("evaluations", [])
        if isinstance(e, dict) and e.get("status") == "qualified"
    ]
    if not rules or rules != qualified:
        errors.append("candidate_rule_lineage_invalid")
    if isinstance(rules, list) and any(
        (
            _as_dict(_as_dict(r).get("match")).get("venue"),
            _as_dict(_as_dict(r).get("match")).get("session_bucket"),
        )
        != cohort
        for r in rules
    ):
        errors.append("candidate_rule_cohort_invalid")
    if any(
        any(v is not True for v in _as_dict(e.get("symbol_holdout_checks")).values())
        for e in extension["evaluations"]
        if isinstance(e, dict) and e.get("status") == "qualified"
    ):
        errors.append("candidate_symbol_holdout_invalid")
    reviewed_metrics = [candidate.get("holdout")] + [
        e.get("holdout")
        for e in extension.get("evaluations", [])
        if isinstance(e, dict) and e.get("status") == "qualified"
    ]
    for metrics in reviewed_metrics:
        m = _as_dict(metrics)
        ev, _ = machine_selection_economics(m, _as_dict(m.get("paired_population")), full_population=full_population)
        if (
            ev is None
            or (ev <= 0 if full_population else ev
                < HIERARCHICAL_ENTRY_QUALITY_GATE["minimum_cost_adjusted_ev_pct"] - 1e-9)
            or (_number(m.get("row_count")) or 0) < 3
            or (_number(m.get("independent_source_date_count")) or 0) < 2
            or m.get("terminal_proxy_evaluable_count") != m.get("row_count")
            or m.get("unusable_label_count") != 0
            or (_number(m.get("clean_fast_count")) or 0)
            <= (_number(m.get("dirty_profit_count")) or 0)
            + (_number(m.get("adverse_count")) or 0)
        ):
            errors.append("candidate_holdout_invalid")
    if full_population:
        for phase, metrics_list in (
            ("holdout", reviewed_metrics),
            ("calibration", [candidate.get("calibration")] + [
                e.get("calibration") for e in extension["evaluations"]
                if isinstance(e, dict) and e.get("status") == "qualified"
            ]),
        ):
            for raw in metrics_list:
                m = _as_dict(raw)
                paired = _as_dict(m.get("paired_population"))
                ev, delta = machine_selection_economics(m, paired, full_population=True)
                minimum_rows, minimum_dates = (5, 3) if phase == "calibration" else (3, 2)
                if (
                    ev is None or ev <= 0 or delta is None or delta <= 0
                    or (_number(m.get("row_count")) or 0) < minimum_rows
                    or (_number(m.get("independent_source_date_count")) or 0) < minimum_dates
                    or m.get("terminal_proxy_evaluable_count") != m.get("row_count")
                    or m.get("unusable_label_count") != 0
                    or type(m.get("catastrophic_terminal_proxy_count")) is not int
                    or m.get("catastrophic_terminal_proxy_count") != 0
                    or paired.get("paired_terminal_contract_complete") is not True
                    or paired.get("terminal_evaluable_count") != paired.get("population_count")
                    or paired.get("paired_comparable_count") != paired.get("population_count")
                    or paired.get("operating_economic_promotion_pass") is not True
                    or paired.get("downstream_operating_evidence_complete") is not True
                    or (_number(paired.get("daily_net_profit_delta_krw")) or 0) <= 0
                ):
                    errors.append("candidate_full_population_economic_proof_invalid")
    return sorted(set(errors))


def build_mechanistic_hierarchy_candidate(
    source_rows: list[dict],
    *,
    target_date: str,
    parent_policy: dict | None = None,
    cohort: tuple[str, str] = ("KRX", "KRX_REGULAR"),
    population_source_contract: dict | None = None,
) -> dict:
    """Bounded group/symbol fitting using the same runtime decision function.

    The old flow research is not promoted by relabeling. Every selected rule
    is re-evaluated with current confirmation, quality labels and sealed dates.
    Counterfactual evidence never certifies real fills or realized economics.
    """
    if not mechanistic_scope_supported(*cohort):
        raise ValueError("hierarchy_cohort_unsupported")
    parent = json.loads(
        json.dumps(parent_policy or MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1)
    )
    full_population = population_source_contract is not None
    frozen = (population_source_contract or {}).get("frozen_hierarchy") or {}
    frozen_valid = bool(frozen.get("incumbent_sha256") == _canonical_sha256(parent)
                        and frozen.get("rules") and isinstance(frozen.get("frozen_date"), str)
                        and frozen.get("economic_kernel_sha256") == (population_source_contract or {}).get("economic_kernel_sha256"))
    frozen_rules = {r["id"]: r for r in frozen.get("rules", [])} if frozen_valid else {}
    if not full_population:
        parent.pop("hierarchy", None)
        parent["postclose_selection"].update(
            minimum_unique_symbol_count=MECHANISTIC_REFINEMENT_GATE[
                "minimum_calibration_symbol_count"
            ],
            minimum_independent_source_date_count=MECHANISTIC_REFINEMENT_GATE[
                "minimum_calibration_source_date_count"
            ],
        )
    if validate_mechanistic_entry_threshold_policy(parent):
        raise ValueError("hierarchy_parent_invalid")
    if full_population and (
        not mechanistic_scope_supported(*cohort)
        or population_source_contract.get("cohort", ["KRX", "KRX_REGULAR"]) != list(cohort)
        or population_source_contract.get("schema") != "machine_common_refinement_population_v1"
        or population_source_contract.get("input_row_disposition_complete") is not True
        or population_source_contract.get("accepted_rows_sha256") != _canonical_sha256([
            {"decision_trace_id": r["decision_trace_id"], "fingerprint": r["fingerprint"]}
            for r in source_rows
        ])
    ):
        raise ValueError("hierarchy_full_population_source_contract_invalid")
    rows, excluded, seen, last_anchor = [], Counter(), set(), {}
    for original in sorted(source_rows, key=lambda r: str(r.get("decision_ts") or "")):
        parts = _as_dict(
            _as_dict(original.get("entry_group_observation")).get("key_parts")
        )
        if (parts.get("venue"), parts.get("session_bucket")) != cohort:
            excluded["different_cohort"] += 1
            continue
        if (
            not CLEAN_BASELINE_DATE
            <= str(original.get("source_date") or "")
            <= target_date
            or original.get("entry_group_contract_valid") is not True
            or original.get("mechanistic_flow_observation_contract_valid") is not True
            or original.get("entry_quality_contract_valid") is not True
            or original.get("source_provenance_verified") is not True
            or not (
                original.get("source_report_hash_verified") is True
                or original.get("machine_observation_hash_verified") is True
            )
        ):
            excluded["source_contract"] += 1
            continue
        try:
            stamp = datetime.fromisoformat(original["decision_ts"])
            if (
                stamp.utcoffset() is None
                or _kst_date_from_aware_timestamp(original["decision_ts"])
                != original["source_date"]
            ):
                raise ValueError("timestamp")
            epoch = stamp.timestamp()
        except (KeyError, TypeError, ValueError):
            excluded["decision_timestamp"] += 1
            continue
        symbol = original.get("stock_code")
        key = (symbol, original["source_date"])
        trace = original.get("decision_trace_id")
        if (
            not trace
            or trace in seen
            or epoch - last_anchor.get(key, -float("inf")) < 300
        ):
            excluded["duplicate_or_overlapping_anchor"] += 1
            continue
        seen.add(trace)
        last_anchor[key] = epoch
        row = {**original, "setup_evidence": dict(original["setup_evidence"])}
        full_cost = _full_entry_cost_pct(
            row["comparison"].get("entry_cost_contract"), source_date=row["source_date"]
        )
        cost_scope = _as_dict(row["comparison"].get("entry_cost_contract"))
        if (
            cost_scope.get("effective_venue"),
            cost_scope.get("session_bucket"),
        ) != cohort:
            full_cost = None
        if full_cost is None or any(
            value is None or not math.isclose(value, full_cost, rel_tol=0, abs_tol=1e-9)
            for value in (
                _number(row["comparison"].get("conservative_execution_cost_pct")),
                _number(
                    row["entry_quality_path"].get("conservative_execution_cost_pct")
                ),
            )
        ):
            excluded["full_cost_or_relabel_required"] += 1
            continue
        captured = _as_dict(row["setup_evidence"].get("mechanistic_context"))
        if captured and captured.get("context_sha256") != _canonical_sha256(
            {k: v for k, v in captured.items() if k != "context_sha256"}
        ):
            excluded["context_hash_invalid"] += 1
            continue
        body = {
            "symbol": symbol,
            "group": row["entry_group_observation"],
            "flow": row["mechanistic_flow_observation"],
            "micro_window": captured.get("micro_window"),
        }
        context = {**body, "context_sha256": _canonical_sha256(body)}
        row["source_evidence_sha256"] = row["setup_evidence"].get("evidence_sha256")
        row["setup_evidence"]["mechanistic_context"] = context
        row["setup_evidence"]["evidence_sha256"] = _canonical_sha256(
            {k: v for k, v in row["setup_evidence"].items() if k != "evidence_sha256"}
        )
        if full_population:
            # Both arms see the same past-only group/flow projection. An
            # incumbent child must not lose its context while challengers
            # receive it, creating a synthetic opportunity recovery.
            row["comparison"] = {
                **original["comparison"],
                "incumbent_machine_action": mechanistic_entry_policy_decision(row["setup_evidence"], policy=parent).get("action"),
                "control_action": "BUY" if mechanistic_entry_policy_decision(
                    row["setup_evidence"], policy=parent
                )["action"] == "ENTER_NOW" else "WAIT",
                "control_role": "same_population_current_machine_incumbent",
            }
        rows.append(row)
    dates = sorted({r["source_date"] for r in rows})
    # Existing family boundaries were examined through 9/11. Do not reuse
    # those same dates as prospective holdout for this semantic expansion.
    forward = [d for d in dates if d > MECHANISTIC_FLOW_BOUNDARY_FREEZE_DATE]
    holdout_dates = forward[-3:] if len(forward) >= 2 else []
    if frozen_valid:
        holdout_dates = [day for day in dates if day > frozen["frozen_date"]]
    train = [
        r for r in rows if not holdout_dates or r["source_date"] < holdout_dates[0]
    ]
    holdout = [r for r in rows if r["source_date"] in holdout_dates]
    parent_hash = _canonical_sha256(parent["thresholds"])

    def policy_for(rules):
        policy = {
            **parent,
            "hierarchy": {
                "schema": MECHANISTIC_HIERARCHY_SCHEMA,
                "parent_sha256": parent_hash,
                "rules": rules,
            },
        }
        if full_population:
            policy["version"] = MECHANISTIC_FULL_POPULATION_POLICY_VERSION
            policy["postclose_selection"] = {
                **parent["postclose_selection"],
                "minimum_cost_adjusted_ev_pct": MECHANISTIC_REFINEMENT_GATE[
                    "minimum_cost_adjusted_ev_pct"
                ],
            }
        return policy

    def selected(population, rules):
        policy = policy_for(rules)
        return [
            r
            for r in population
            if mechanistic_entry_policy_decision(r["setup_evidence"], policy=policy)[
                "action"
            ]
            == "ENTER_NOW"
        ]

    def metrics(selected_rows, *, population=None, rules=None):
        result = _entry_quality_population_metrics(selected_rows)
        result["unusable_label_count"] = sum(
            r["entry_quality_path"].get("status") != "evaluable" for r in selected_rows
        )
        if full_population and population is not None:
            result["paired_population"] = _mechanistic_paired_population_metrics(
                population, selected_rows, candidate_policy=policy_for(rules or []))
            result["catastrophic_terminal_proxy_count"] = _mechanistic_policy_metrics(selected_rows)["catastrophic_terminal_proxy_count"]
        return result

    def qualifies(m, *, validation=False):
        ev, delta = machine_selection_economics(m, _as_dict(m.get("paired_population")), full_population=full_population)
        return (
            m["row_count"]
            >= (
                MECHANISTIC_REFINEMENT_GATE["minimum_holdout_exposure_count"]
                if validation
                else HIERARCHICAL_ENTRY_QUALITY_GATE["minimum_group_terminal_count"]
            )
            and m["independent_source_date_count"]
            >= (
                MECHANISTIC_REFINEMENT_GATE["minimum_holdout_source_date_count"]
                if validation
                else HIERARCHICAL_ENTRY_QUALITY_GATE["minimum_group_source_date_count"]
            )
            and m["unusable_label_count"] == 0
            and m["terminal_proxy_evaluable_count"] == m["row_count"]
            and ev is not None
            and ev
            >= HIERARCHICAL_ENTRY_QUALITY_GATE[
                "minimum_cost_adjusted_ev_pct"
            ]
            - 1e-9
            and m["clean_fast_count"] > m["dirty_profit_count"] + m["adverse_count"]
            and (not full_population or (
                delta is not None and delta > 0
                and _as_dict(m.get("paired_population")).get("paired_terminal_contract_complete") is True
                and _as_dict(m.get("paired_population")).get("terminal_evaluable_count") == _as_dict(m.get("paired_population")).get("population_count")
                and m.get("catastrophic_terminal_proxy_count") == 0
                and _as_dict(m.get("paired_population")).get("operating_economic_promotion_pass") is True
                and _as_dict(m.get("paired_population")).get("downstream_operating_evidence_complete") is True
            ))
        )

    def rank(m):
        # Predeclared ranking; holdout is never used for parameter selection.
        if full_population:
            return (
                _number(_as_dict(m.get("paired_population")).get("daily_net_profit_delta_krw")) or -float("inf"),
                _number(_as_dict(_as_dict(m.get("paired_population")).get("operating_economic_comparison")).get("robust_paired_delta_ev_lower_bound_pct")) or -float("inf"),
                m["cost_adjusted_terminal_proxy_ev_pct"] or -float("inf"), m["row_count"],
            )
        return (
            m["clean_fast_count"] - m["dirty_profit_count"] - m["adverse_count"],
            m["cost_adjusted_terminal_proxy_ev_pct"] or -float("inf"),
            m["row_count"],
        )

    groups = {}
    for row in train:
        parts = row["entry_group_observation"]["key_parts"]
        # Three dimensions, not a Cartesian expansion of all eight bands.
        match = {
            k: parts.get(k)
            for k in ("venue", "session_bucket", "price_tick_band", "volatility_band")
        }
        if (match["venue"], match["session_bucket"]) != cohort or any(
            v in (None, "UNKNOWN", "") for v in match.values()
        ):
            continue
        for family in row["mechanistic_flow_observation"].get("matched_families", []):
            identity = _canonical_sha256([match, family])[:20]
            groups.setdefault(identity, (match, family))
    if frozen_valid:
        groups = {k: (r["match"], r["flow_family"]) for k, r in frozen_rules.items()}
    evaluations, accepted = [], []
    for identity, (match, family) in sorted(groups.items())[:64]:
        base = {
            "id": identity,
            "match": match,
            "flow_family": family,
            "thresholds": {
                k: parent["thresholds"][k] for k in MECHANISTIC_PARAMETER_BOUNDS
            },
            "symbols": {},
            "micro": None,
        }
        scoped = [
            r
            for r in train
            if all(
                r["entry_group_observation"]["key_parts"].get(k) == v
                for k, v in match.items()
            )
            and family in r["mechanistic_flow_observation"].get("matched_families", [])
        ]
        # One-coordinate refinements reuse the existing bounded grid.
        variants = [base]
        for key, values in MECHANISTIC_COMMON_FEATURE_GRID.items():
            variants.extend(
                {**base, "thresholds": {**base["thresholds"], key: v}} for v in values
            )
        micro_base = {
            "minimum_depletion_fraction_per_sec": 0.0,
            "minimum_trade_backed_ratio": 0.5,
            "maximum_refill_ratio": 0.5,
        }
        micro_variants = [micro_base]
        for key, values in {
            "minimum_depletion_fraction_per_sec": (0.1, 0.25, 0.5),
            "minimum_trade_backed_ratio": (0.75, 1.0),
            "maximum_refill_ratio": (0.0, 0.25),
        }.items():
            micro_variants.extend({**micro_base, key: value} for value in values)
        for micro_thresholds in micro_variants:
            variants.append(
                {
                    **base,
                    "micro": micro_thresholds,
                }
            )
        # A valid incumbent may be outside the bounded challenger envelope.
        # Such inherited coordinates are not permission to publish an invalid
        # residual, and must not crash evaluation of the valid alternatives.
        if frozen_valid:
            variants = [frozen_rules[identity]]
        fits = [
            (rule, metrics(selected(scoped, [rule]), population=scoped, rules=[rule]))
            for rule in variants
            if not validate_mechanistic_entry_threshold_policy(policy_for([rule]))
        ]
        passing = [(rule, m) for rule, m in fits if qualifies(m)]
        if not passing:
            evaluations.append({"id": identity, "status": "calibration_not_qualified"})
            continue
        best, train_metrics = max(passing, key=lambda pair: rank(pair[1]))
        best = json.loads(json.dumps(best))
        # Fit symbol residuals on train only, then validate the entire policy.
        for symbol in ([] if frozen_valid else sorted({r["stock_code"] for r in scoped})):
            symbol_rows = [r for r in scoped if r["stock_code"] == symbol]
            n = len(symbol_rows)
            if (
                n
                < HIERARCHICAL_ENTRY_QUALITY_GATE[
                    "symbol_residual_minimum_terminal_count"
                ]
                or len({r["source_date"] for r in symbol_rows})
                < HIERARCHICAL_ENTRY_QUALITY_GATE[
                    "symbol_residual_minimum_source_date_count"
                ]
            ):
                continue
            best_metric = metrics(selected(symbol_rows, [best]), population=symbol_rows, rules=[best])
            fitted = None
            for key, values in MECHANISTIC_COMMON_FEATURE_GRID.items():
                for v in values:
                    delta = {k: 0.0 for k in MECHANISTIC_PARAMETER_BOUNDS}
                    delta[key] = v - best["thresholds"][key]
                    residual = {"count": n, "delta": delta}
                    rule = {**best, "symbols": {**best["symbols"], symbol: residual}}
                    if validate_mechanistic_entry_threshold_policy(policy_for([rule])):
                        continue
                    m = metrics(selected(symbol_rows, [rule]), population=symbol_rows, rules=[rule])
                    if qualifies(m) and rank(m) > rank(best_metric):
                        fitted, best_metric = residual, m
            if fitted is not None:
                best["symbols"][symbol] = fitted
        validation_rows = [
            r
            for r in holdout
            if all(
                r["entry_group_observation"]["key_parts"].get(k) == v
                for k, v in match.items()
            )
            and family in r["mechanistic_flow_observation"].get("matched_families", [])
        ]
        validation = metrics(selected(validation_rows, [best]), population=validation_rows, rules=[best])
        baseline = metrics(
            [
                r
                for r in validation_rows
                if mechanistic_entry_policy_decision(
                    r["setup_evidence"], policy=parent
                )["action"]
                == "ENTER_NOW"
            ]
        )
        # No per-group fallback after a failed holdout. Rejected rule remains
        # evidence only; the existing live parent is retained by the publisher.
        passed = qualifies(validation, validation=True) and (full_population or (
            validation["clean_fast_count"]
            - validation["dirty_profit_count"]
            - validation["adverse_count"]
            > baseline["clean_fast_count"]
            - baseline["dirty_profit_count"]
            - baseline["adverse_count"]
        ))
        residual_checks = {}
        for symbol in best["symbols"]:
            symbol_holdout = [r for r in validation_rows if r["stock_code"] == symbol]
            m = metrics(selected(symbol_holdout, [best]), population=symbol_holdout, rules=[best])
            without = {
                **best,
                "symbols": {k: v for k, v in best["symbols"].items() if k != symbol},
            }
            baseline_symbol = metrics(selected(symbol_holdout, [without]), population=symbol_holdout, rules=[without])
            residual_checks[symbol] = qualifies(m, validation=True) and rank(m) > rank(
                baseline_symbol
            )
        passed = passed and all(residual_checks.values())
        train_metrics = metrics(selected(scoped, [best]), population=scoped, rules=[best])
        passed = passed and (not full_population or qualifies(train_metrics))
        # Same complete-window population and exit/cost contract in all arms.
        # This is a diagnostic, never a holdout-driven alternative selector.
        ablation = {}
        for lane, population in (("calibration", scoped), ("holdout", validation_rows)):
            structural = selected(population, [{**best, "micro": None}])
            complete = [
                r
                for r in structural
                if _mechanistic_micro_pass(
                    r["setup_evidence"]["mechanistic_context"],
                    best["micro"] or micro_base,
                    diagnostic_arm="baseline",
                )[0]
            ]
            ablation[lane] = {
                "intersection_count": len(complete),
                "intersection_sha256": _canonical_sha256(
                    [r["decision_trace_id"] for r in complete]
                ),
                "arms": {
                    arm: metrics(
                        [
                            r
                            for r in complete
                            if _mechanistic_micro_pass(
                                r["setup_evidence"]["mechanistic_context"],
                                best["micro"] or micro_base,
                                diagnostic_arm=arm,
                            )[0]
                        ]
                    )
                    for arm in (
                        "baseline",
                        "bid_rebound",
                        "depletion_trade_refill",
                        "combined",
                    )
                },
            }
        evaluations.append(
            {
                "id": identity,
                "rule": best,
                "calibration": train_metrics,
                "holdout": validation,
                "baseline_holdout": baseline,
                "symbol_holdout_checks": residual_checks,
                "feature_ablation_study": ablation,
                "status": "qualified" if passed else "holdout_not_qualified",
            }
        )
        if full_population or passed:
            accepted.append(best)
    combined = metrics(selected(holdout, accepted), population=holdout, rules=accepted) if accepted else metrics([])
    combined_train = metrics(selected(train, accepted), population=train, rules=accepted) if accepted else metrics([])
    passes = (population_source_contract or {}).get("incumbent_scope_verified", True) is True and bool(accepted) and qualifies(combined, validation=True) and (
        not full_population or (qualifies(combined_train) and all(e.get("status") == "qualified" for e in evaluations if "rule" in e))
    )
    forward_selection = frozen if frozen_valid else None
    if (population_source_contract or {}).get("forward_holdout_required") is True:
        if not frozen_valid and accepted and qualifies(combined_train):
            forward_selection = {"incumbent_sha256": _canonical_sha256(parent),
                "rules": accepted, "frozen_date": datetime.now(KST).date().isoformat(),
                "economic_contract": "machine_operating_daily_net_v1",
                "economic_kernel_sha256": population_source_contract.get("economic_kernel_sha256")}
        passes = passes and bool(frozen_valid and holdout_dates
                                  and min(holdout_dates) > frozen["frozen_date"])
    candidate = (
        {
            "threshold_policy": policy_for(accepted),
            "operating_contract_version": "machine_operating_daily_net_v1" if full_population else None,
            "source_date": target_date,
            "cohort": list(cohort),
            "calibration_dates": sorted({r["source_date"] for r in train}),
            "holdout_dates": holdout_dates,
            "source_rows_sha256": _canonical_sha256(rows),
            "evaluations_sha256": _canonical_sha256(evaluations),
            "holdout": combined,
            "calibration": combined_train,
            **({
                "evaluation_contract": (
                    "hierarchy_full_population_cost_adjusted_10bp_paired_v3"
                ),
                "population_source_contract": population_source_contract,
                "population_source_contract_sha256": _canonical_sha256(population_source_contract),
                "incumbent_machine_policy": parent,
                "incumbent_machine_policy_sha256": _canonical_sha256(parent),
            } if full_population else {}),
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
        }
        if passes
        else None
    )
    if candidate:
        candidate["candidate_content_sha256"] = _canonical_sha256(candidate)
    return {
        "schema": MECHANISTIC_HIERARCHY_SCHEMA,
        "forward_selection": forward_selection,
        "policy_candidate": candidate,
        "cohort": list(cohort),
        "status": "candidate_ready" if passes else "incumbent_carry_no_qualified_child",
        "promotion_pass": passes,
        "evaluations": evaluations,
        "source_count": len(rows),
        "excluded": dict(excluded),
        "economic_contract_diagnostics": {
            "lane": "fixed_boundary_counterfactual_not_realized_pnl",
            "evaluation_contract": (
                "hierarchy_full_population_cost_adjusted_10bp_paired_v3"
                if full_population
                else "legacy_absolute_net_10bp_v1"
            ),
            "minimum_cost_adjusted_ev_pct": HIERARCHICAL_ENTRY_QUALITY_GATE[
                "minimum_cost_adjusted_ev_pct"
            ],
            "rows_whose_gross_target_cannot_clear_net_ev_floor": sum(
                (
                    (_number(r["comparison"].get("entry_path_target_pct")) or 0)
                    - (_number(r["comparison"].get("conservative_execution_cost_pct")) or 0)
                    <= 0.0
                ) if full_population else (
                    (_number(r["comparison"].get("entry_path_target_pct")) or 0)
                    - (_number(r["comparison"].get("conservative_execution_cost_pct")) or 0)
                    < HIERARCHICAL_ENTRY_QUALITY_GATE["minimum_cost_adjusted_ev_pct"] - 1e-9
                )
                for r in rows
            ),
            "ceiling_is_reported_not_used_to_remove_losing_rows": True,
        },
        "calibration_dates": sorted({r["source_date"] for r in train}),
        "holdout_dates": holdout_dates,
        "counterfactual_only_not_realized_pnl": True,
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


def _machine_full_evaluation_projection(
    mechanistic_refinement: dict[str, Any], refinement_contract: dict[str, Any]
) -> dict[str, Any]:
    best = mechanistic_refinement.get("best_observed_candidate") or {}
    best_paired = best.get("calibration_paired_population") or {}
    holdout_paired = (
        mechanistic_refinement.get("best_observed_holdout_paired_population") or {}
    )
    accepted_count = int(refinement_contract.get("accepted_unique_trace_count") or 0)
    input_counts = refinement_contract.get("input_lane_counts") or {}
    refinement_status = str(mechanistic_refinement.get("status") or "")
    operating = holdout_paired.get('operating_economic_comparison') or best_paired.get('operating_economic_comparison') or {}
    operating_blocker = operating.get('blocker')
    unsupported = {'frozen_auxiliary_verdict_missing', 'sequence_nonzero_inference_cost_timeline_unbound',
        'shared_cash_envelope_changed_without_cashflow_witness', 'sequence_frozen_quantity_or_budget_changed',
        'model_error_can_change_capital_admission', 'capital_external_flow_or_settlement_basis_unreconciled'}
    full_state = (
        "validated_edge"
        if mechanistic_refinement.get("promotion_pass") is True
        else "pending_maturity"
        if operating_blocker == 'recheck_terminal_pending'
        else "unsupported_scope"
        if operating_blocker in unsupported
        else "source_gap"
        if (operating_blocker or holdout_paired.get("unsupported_changed_decision_count", 0) > 0
            or (accepted_count and holdout_paired.get("operating_population_complete") is not True))
        else "insufficient_mature_sample"
        if refinement_status == "insufficient_mature_sample"
        else "evaluated_no_edge"
        if best
        else "source_gap"
        if not accepted_count and sum(int(v or 0) for v in input_counts.values()) > 0
        else "insufficient_mature_sample"
    )
    return {
        "schema": "main_mechanistic_entry_full_evaluation_v1",
        "source_date": mechanistic_refinement.get("target_date"),
        "structural_blocker": (operating_blocker or ("machine_operating_population_unbound"
            if accepted_count and refinement_contract.get("operating_economic_enrichment_count", 0) == 0 else None)),
        "operating_comparison_status": operating.get('status'),
        "operating_economics": operating if holdout_paired.get('downstream_operating_evidence_complete') is True else None,
        "operating_blocker_owner": operating.get('owner'),
        "operating_closure_test": operating.get('closure_test'),
        "state": full_state,
        "full_population_count": refinement_contract.get("structure_contract_population_count", accepted_count),
        "current_structure_eligible_count": accepted_count,
        "structure_contract_input_counts": refinement_contract.get("structure_contract_input_counts"),
        "population_unit": "exact_machine_attempt",
        "metric_role": "sim_probe_ev",
        "economic_basis": "terminal_path_proxy_unless_operating_proof_present",
        "holdout_incumbent_ev_pct": holdout_paired.get("incumbent_opportunity_ev_pct"),
        "paired_comparable_count": holdout_paired.get("paired_comparable_count"),
        "unsupported_changed_decision_count": holdout_paired.get("unsupported_changed_decision_count"),
        "input_lane_counts": refinement_contract.get("input_lane_counts"),
        "accepted_lane_counts": refinement_contract.get("accepted_lane_counts"),
        "row_exclusion_reason_counts": refinement_contract.get(
            "row_exclusion_reason_counts"
        ),
        "independent_candidate_count": mechanistic_refinement.get(
            "independent_policy_comparison_candidate_count"
        ),
        "evaluated_distinct_policy_count": mechanistic_refinement.get(
            "evaluated_distinct_policy_count"
        ),
        "calibration_gate_passing_candidate_count": mechanistic_refinement.get(
            "calibration_gate_passing_candidate_count"
        ),
        "promotion_pass": mechanistic_refinement.get("promotion_pass") is True,
        "calibration_cost_adjusted_ev_pct": best_paired.get("candidate_opportunity_ev_pct"),
        "calibration_paired_delta_ev_pct": best_paired.get("paired_terminal_proxy_delta_pct"),
        "holdout_cost_adjusted_ev_pct": holdout_paired.get("candidate_opportunity_ev_pct"),
        "selected_trade_terminal_proxy_ev_pct": (mechanistic_refinement.get("best_observed_holdout") or {}).get("cost_adjusted_terminal_proxy_ev_pct"),
        "holdout_paired_delta_ev_pct": holdout_paired.get(
            "paired_terminal_proxy_delta_pct"
        ),
        "daily_net_profit_delta_krw": (holdout_paired.get("daily_net_profit_delta_krw")
            if holdout_paired.get("operating_population_complete") is True else None),
        "daily_net_profit_status": holdout_paired.get(
            "daily_net_profit_status",
            "not_available_without_exact_changed_decision_owner_replay",
        ),
        "baseline_preserved": holdout_paired.get("baseline_preserved") is True,
        "downstream_operating_evidence_complete": holdout_paired.get(
            "downstream_operating_evidence_complete"
        ),
        "self_comparison_counted_as_improvement": False,
        "compact_projection_controls_machine_population": False,
        "policy_candidate": mechanistic_refinement.get("policy_candidate"),
    }


def _machine_operating_projection(data_root: Path, days: list[str]) -> dict:
    """Consume each day's existing sealed owner projection, without rerunning AI.

    A latest-day compact projection cannot enrich older machine attempts.
    The day-specific model and pricing proofs remain attached to their rows.
    """
    from src.engine.scalping import compact_auxiliary_paired_replay as compact
    rows, sources, missing = [], [], []
    for day in sorted(set(days)):
        path = compact.report_path(data_root, day).with_suffix(".source.json")
        source = compact.read(path)
        cost = compact.runtime_inference_cost_receipt(data_root, day)
        if compact.valid(source) and source.get("target_date") == day:
            sources.append({"source_date": day, "artifact_content_sha256": source["artifact_content_sha256"]})
            for row in source.get("rows") or []:
                if row.get("source_date") == day:
                    rows.append({**row,
                        "machine_owner_model_validation": source.get("owner_execution_model_validation") or {},
                        "machine_runtime_cost_receipt": cost})
        else:
            missing.append(day)
        # The existing split producer owns pre-AI plans as well as executable
        # owner paths. No compact trace or synthetic auxiliary call is needed.
        split = compact.read(data_root / "report/entry_split_order_plan" / f"entry_split_order_plan_{day}.json")
        replay = (split.get("input_summary") or {}).get("compact_pre_ai_execution_replay") or {}
        if (replay.get("source_date") == day and replay.get("sha256") == compact.digest(
                {k:v for k,v in replay.items() if k != "sha256"})):
            sources.append({"source_date": day, "nonentry_replay_sha256": replay["sha256"]})
            for owner_row in replay.get("rows") or []:
                seed = owner_row.get("seed") or {}
                row = {k: seed.get(k) for k in ("evaluation_attempt_id", "source_date", "stock_code",
                    "scanner_promotion_id", "effective_venue", "session_bucket")}
                row.update(owner_replay=owner_row, incumbent_verdict=None)
                if _machine_nonentry_seed(row) and row["source_date"] == day:
                    rows.append(row)
    return compact.sealed({"rows": rows, "sources": sources, "missing_source_dates": missing})


def _machine_joint_scope_metrics(population, policies, parents):
    """Apply a frozen whole bundle over one capital timeline, including carry scopes."""
    rows, selected = [], set()
    for row in population:
        parts = (row.get('entry_group_observation') or {}).get('key_parts') or {}
        scope = str(parts.get('venue')) + '|' + str(parts.get('session_bucket'))
        if scope not in parents or scope not in policies:
            return {'status': 'source_gap', 'blocker': 'joint_scope_policy_missing'}
        old = mechanistic_entry_policy_decision(row['setup_evidence'], policy=parents[scope])['action']
        new = mechanistic_entry_policy_decision(row['setup_evidence'], policy=policies[scope])['action']
        rows.append({**row, 'comparison': {**row['comparison'], 'incumbent_machine_action': old},
                     'joint_candidate_action': new})
        if new == 'ENTER_NOW': selected.add(row['decision_trace_id'])
    groups = defaultdict(list)
    for row in rows:
        groups[(row.get('source_date'), row.get('stock_code'), row.get('scanner_promotion_id'))].append(row)
    for group in groups.values():
        if all(r.get('machine_sequence_expected_count') == len(group) for r in group):
            for row in group:
                row['machine_sequence_members'] = sorted(r['decision_trace_id'] for r in group)
    return _machine_sequence_operating_metrics(rows, selected, joint_actions=True)


def _machine_joint_scope_gate(metrics):
    candidate, incumbent = metrics.get('candidate') or {}, metrics.get('incumbent') or {}
    return bool(metrics.get('status') == 'supported_operating_comparison'
        and (_number(metrics.get('robust_paired_delta_ev_lower_bound_pct')) or 0) > 0
        and (_number(metrics.get('daily_net_profit_delta_krw')) or 0) > 0
        and (_number(candidate.get('ev_pct')) or 0) >= MECHANISTIC_REFINEMENT_GATE['minimum_cost_adjusted_ev_pct']
        and candidate.get('es10', -float('inf')) >= incumbent.get('es10', float('inf'))
        and candidate.get('worst', -float('inf')) >= incumbent.get('worst', float('inf')))


def _machine_joint_scope_evaluation(population, parents, refinements, extensions, previous, kernel, target_date):
    import copy
    proposals = copy.deepcopy(parents)
    for scope, parent in parents.items():
        common = (refinements.get(scope) or {}).get('forward_selection') or {}
        hierarchy = (extensions.get(scope) or {}).get('forward_selection') or {}
        if common.get('incumbent_sha256') == _canonical_sha256(parent) and common.get('policy'):
            proposals[scope] = _mechanistic_threshold_policy(common['policy'], parent, publication=True)
        elif hierarchy.get('incumbent_sha256') == _canonical_sha256(parent) and hierarchy.get('rules'):
            proposals[scope] = {**parent, 'version': MECHANISTIC_FULL_POPULATION_POLICY_VERSION,
                'hierarchy': {'schema': MECHANISTIC_HIERARCHY_SCHEMA,
                    'parent_sha256': _canonical_sha256(parent['thresholds']), 'rules': hierarchy['rules']},
                'postclose_selection': {**parent['postclose_selection'],
                    'minimum_cost_adjusted_ev_pct': MECHANISTIC_REFINEMENT_GATE['minimum_cost_adjusted_ev_pct']}}
    changed = sorted(s for s in parents if proposals[s] != parents[s])
    result = dict(status='not_applicable_single_or_no_scope_change', promotion_pass=False,
                  changed_scopes=changed, forward_selection=None)
    if len(changed) < 2:
        return result
    frozen = (previous or {}).get('forward_selection') or {}
    valid = (frozen.get('parents') == parents and frozen.get('policies') == proposals
             and frozen.get('economic_kernel_sha256') == kernel
             and isinstance(frozen.get('frozen_date'), str))
    # The bundle is chosen from calibration freezes. It is never assembled from
    # the subset that happened to pass a candidate holdout.
    if not valid:
        metrics = _machine_joint_scope_metrics(population, proposals, parents)
        result.update(status='joint_calibration_not_qualified', calibration=metrics)
        if _machine_joint_scope_gate(metrics):
            result.update(status='joint_forward_holdout_pending', forward_selection=dict(
                parents=parents, policies=proposals, changed_scopes=changed,
                frozen_date=datetime.now(KST).date().isoformat(), economic_kernel_sha256=kernel,
                calibration_rows_sha256=_canonical_sha256(population)))
        return result
    held = [r for r in population if frozen['frozen_date'] < r['source_date'] <= target_date]
    metrics = _machine_joint_scope_metrics(held, proposals, parents)
    dates = sorted({r['source_date'] for r in held})
    qualified = sorted(s for s in changed if (refinements.get(s) or {}).get('policy_candidate')
                       or (extensions.get(s) or {}).get('policy_candidate'))
    checks = dict(entire_frozen_bundle_qualified=qualified == changed,
        independent_dates=len(dates) >= MECHANISTIC_REFINEMENT_GATE['minimum_holdout_source_date_count'],
        independent_samples=len(held) >= MECHANISTIC_REFINEMENT_GATE['minimum_holdout_terminal_evaluable_count'],
        joint_economics=_machine_joint_scope_gate(metrics))
    result.update(status='joint_holdout_evaluated', forward_selection=frozen,
        holdout_rows=held, holdout_source_dates=dates, holdout=metrics,
        promotion_checks=checks, promotion_pass=all(checks.values()))
    result['sha256'] = _canonical_sha256(result)
    return result


def machine_joint_scope_evidence_valid(report, scopes):
    """Publisher recomputes allocation; summary flags do not grant authority."""
    proof = report.get('joint_scope_economics') or {}
    frozen = proof.get('forward_selection') or {}
    try:
        rows = proof['holdout_rows']
        if (proof.get('sha256') != _canonical_sha256({k:v for k,v in proof.items() if k != 'sha256'})
            or proof.get('promotion_pass') is not True
            or not proof.get('promotion_checks') or not all(v is True for v in proof['promotion_checks'].values())
            or len(rows) < MECHANISTIC_REFINEMENT_GATE['minimum_holdout_terminal_evaluable_count']
            or len({r['source_date'] for r in rows}) < MECHANISTIC_REFINEMENT_GATE['minimum_holdout_source_date_count']
            or sorted(scopes) != frozen['changed_scopes']
            or proof['holdout_source_dates'] != sorted({r['source_date'] for r in rows})
            or not all(frozen['frozen_date'] < r['source_date'] <= report['target_date'] for r in rows)):
            return False
        expected = _machine_joint_scope_metrics(rows, frozen['policies'], frozen['parents'])
        if expected != proof['holdout'] or not _machine_joint_scope_gate(expected):
            return False
        for scope in scopes:
            common = (report.get('mechanistic_refinements_by_scope') or {}).get(scope) or {}
            hierarchy = ((report.get('hierarchical_entry_quality') or {}).get('runtime_extensions_by_scope') or {}).get(scope) or {}
            candidate = common.get('policy_candidate') or hierarchy.get('policy_candidate') or {}
            if (common.get('source_contract') or {}).get('economic_kernel_sha256') != frozen.get('economic_kernel_sha256'):
                return False
            proposed = (candidate.get('threshold_policy') or
                _mechanistic_threshold_policy(candidate['thresholds'], frozen['parents'][scope], publication=True))
            if proposed != frozen['policies'][scope]: return False
        return True
    except (ValueError, KeyError, TypeError):
        return False


def _machine_opportunity_id(row):
    return _canonical_sha256([row['source_date'], row.get('stock_code'),
                              row.get('scanner_promotion_id') or row['decision_trace_id']])


def _machine_admission_rank(economy, *, node_count=1, complexity=0):
    from src.engine.scalping.entry_strategy_policy import machine_admission_rank
    return machine_admission_rank(economy, node_count=node_count, complexity=complexity)


def _machine_path_value(row):
    """Resolve the policy-independent cost-bound path once per frozen row."""
    comparison = row.get('comparison') or {}
    cost = _full_entry_cost_pct(comparison.get('entry_cost_contract'), source_date=row['source_date'])
    contract = comparison.get('entry_cost_contract') or {}
    if (contract.get('effective_venue'), contract.get('session_bucket')) != (row.get('effective_venue'), row.get('session_bucket')):
        return None, 'full_cost_scope_mismatch'
    charged = _number(comparison.get('conservative_execution_cost_pct'))
    if cost is None or charged is None or not math.isclose(cost, charged, abs_tol=1e-9):
        return None, 'full_cost_missing_or_mismatched'
    # The existing quality path binds its gross target to full round-trip
    # cost. The legacy gross 0.3% target can be below that cost and cannot
    # measure a profitable missed opportunity. Never infer an AI verdict.
    path = row.get('entry_quality_path') or {}
    path_cost = _number(path.get('conservative_execution_cost_pct'))
    if (row.get('entry_quality_contract_valid') is not True
        or path.get('schema') != 'entry_quality_path_v1'
        or path_cost is None or not math.isclose(path_cost, cost, rel_tol=0, abs_tol=1e-9)):
        return None, 'quality_path_cost_missing_or_mismatched'
    hit = path.get('first_hit')
    boundary = _number(path.get('gross_net_target_pct' if hit == 'net_target_first' else 'exact_stop_distance_pct'))
    if (path.get('status') != 'evaluable' or hit not in {'net_target_first', 'exact_stop_first'}
        or boundary is None or (hit == 'net_target_first' and boundary < 0)
        or (hit == 'exact_stop_first' and boundary >= 0)):
        return None, 'terminal_path_censored'
    return round(boundary - cost, 12), None


def _machine_admission_metrics(rows, actions, *, prepared_paths=None, full_population=True):
    """Equal-opportunity immediate exposure study; no AI or realized PnL."""
    from src.engine.scalping import entry_strategy_policy as strategy
    if len(rows) != len(actions):
        raise ValueError('machine_action_population_mismatch')
    paths = prepared_paths if prepared_paths is not None else [_machine_path_value(row) for row in rows]
    if len(paths) != len(rows):
        raise ValueError('machine_path_population_mismatch')
    groups, transitions, excluded = defaultdict(list), Counter(), Counter()
    transition_ids = defaultdict(set)
    selected, manifest, success, lost, avoided = [], [], [], [], []
    unknown_changes = []
    historical = Counter()
    for row, action, (value, reason) in zip(rows, actions, paths):
        baseline = (row.get('comparison') or {}).get('incumbent_machine_action')
        old, new = baseline == 'ENTER_NOW', action == 'ENTER_NOW'
        if baseline not in {'ENTER_NOW', 'BLOCK', 'RECHECK'}:
            reason = 'incumbent_action_unsupported'
        if not full_population and old:
            excluded['outside_nonentry_population'] += 1
            continue
        if reason:
            excluded[reason] += 1
            if old and not new:
                unknown_changes.append(row.get('decision_trace_id'))
            continue
        key = _machine_opportunity_id(row)
        groups[key].append((value if old else 0., value if new else 0., new))
        manifest.append([key, row.get('decision_trace_id'), value, baseline])
        outcome = 'success' if value > 0 else 'failure' if value < 0 else 'neutral'
        historical[(row.get('comparison') or {}).get('historical_machine_action', baseline) + ':' + outcome] += 1
        category = ('existing_' + outcome + ('_retained' if new else '_avoided' if value < 0 else '_missed')
                    if old else 'nonentry_' + outcome + ('_recovered' if new else '_unselected'))
        transitions[category] += 1
        transition_ids[category].add(key)
        if old and value > 0:
            success.append(new)
            if not new:
                lost.append(value)
        if old and not new and value < 0:
            avoided.append(-value)
        if new:
            selected.append(value)
    old_values = [fmean(v[0] for v in values) for values in groups.values()]
    new_values = [fmean(v[1] for v in values) for values in groups.values()]
    selected_episodes = [[v[1] for v in values if v[2]] for values in groups.values()]
    selected_episodes = [values for values in selected_episodes if values]
    result = dict(status='supported_machine_admission' if groups else 'machine_path_unavailable',
        basis='full_population_cost_bound_quality_path' if full_population else 'nonentry_to_enter_now_cost_bound_quality_path',
        evaluation_basis=strategy.MACHINE_EVALUATION_BASIS if full_population else 'machine_nonentry_opportunity_v1',
        comparison_unit='equal_episode_weighted_immediate_attempts',
        comparable_population_sha256=strategy.digest(sorted(manifest)),
        comparable_opportunity_count=len(groups), comparable_attempt_count=sum(map(len, groups.values())),
        excluded_attempt_counts=dict(excluded), selected_attempt_count=len(selected),
        unevaluated_existing_entry_changes=unknown_changes,
        evaluated_existing_entry_changed_count=sum(v for k,v in transitions.items() if k.startswith('existing_') and not k.endswith('_retained')),
        transition_attempt_counts=dict(transitions),
        transition_opportunity_counts={k: len(v) for k,v in transition_ids.items()},
        historical_action_outcome_counts=dict(historical),
        existing_success_retention_rate_pct=100 * fmean(success) if success else None,
        missed_success_simple_sum_path_pct=sum(lost), avoided_loss_simple_sum_path_pct=sum(avoided),
        incumbent_admission_value_pct=fmean(old_values) if old_values else None,
        candidate_admission_value_pct=fmean(new_values) if new_values else None,
        paired_admission_delta_pct=fmean(b-a for a,b in zip(old_values,new_values)) if old_values else None,
        selected_path_ev_pct=fmean(fmean(values) for values in selected_episodes) if selected_episodes else None,
        selected_opportunity_count=len(selected_episodes),
        win_rate_pct=100 * fmean(fmean(value > 0 for value in values) for values in selected_episodes) if selected_episodes else None,
        episode_positive_mean_rate_pct=100 * fmean(fmean(values) > 0 for values in selected_episodes) if selected_episodes else None,
        worst_selected_path_pct=min(selected) if selected else None,
        auxiliary_ai_required=False, realized_pnl=False, portfolio_pnl=False)
    result.update(support_adjusted_win_rate_pct=strategy.machine_support_adjusted_win_rate(result),
        selection_score_version=strategy.MACHINE_SELECTION_VERSION if full_population else 'support_adjusted_win_rate_preserve_entries_v3')
    return result


def build_main_strategy_refinement(population, *, parent, scope, source_contract, previous=None, limit=96, machine_policy_only=False, checkpoint=None, training_through_date=None):
    """Select on train only, then evaluate one frozen joint policy on holdout."""
    from copy import deepcopy
    from src.engine.scalping import entry_strategy_policy as strategy
    result = dict(schema="main_entry_strategy_refinement_v2", scope=list(scope),
        status="source_gap", promotion_pass=False, candidate=None,
        incumbent_machine_policy_sha256=strategy.digest(parent),
        source_contract_sha256=_canonical_sha256(source_contract), population_count=len(population),
        evaluated_candidate_count=0, search_complete=False)
    if not population:
        return {**result, "blocker": "strategy_population_empty"}
    supported, exclusions = [], []
    for row in population:
        setup = row.get('setup_evidence') or {}
        raw = setup.get('strategy_raw_input')
        try:
            reason = ('strategy_predecision_primitives_missing' if not isinstance(raw, dict) or not raw
                else 'strategy_predecision_hash_invalid' if setup.get('strategy_raw_sha256') != strategy.digest(raw) else None)
            if not reason:
                strategy.features(raw, setup)
                if (raw.get('entry_candle_context') or {}).get('strategy_completed_bars'):
                    strategy.completed_bar_rows(raw, observed_at=row.get('decision_ts'))
        except (ValueError, TypeError, KeyError, OverflowError) as exc:
            reason = 'strategy_invalid_primitive:' + str(exc)
        if reason:
            exclusions.append(dict(decision_trace_id=row.get('decision_trace_id'), reason=reason))
        else:
            supported.append(row)
    result.update(source_exclusions=exclusions, supported_population_count=len(supported))
    population = supported
    if not population:
        return {**result, 'blocker': 'strategy_no_supported_predecision_rows'}
    input_sha256 = strategy.digest([source_contract, parent, population, strategy.SEARCH_VERSION, strategy.MACHINE_SELECTION_VERSION, training_through_date] if machine_policy_only else [source_contract, parent, population])
    result['input_sha256'] = input_sha256
    # Same input/selection is immutable; retries do not optimize on used holdout.
    if previous and previous.get('input_sha256') == input_sha256 and previous.get('candidate') and previous.get('selection_state') in {'holdout_evaluated', 'published'}:
        return previous
    dates = sorted({r["source_date"] for r in population})
    if training_through_date and training_through_date < dates[0]:
        raise ValueError("strategy_training_boundary_outside_sources")
    # Machine replay replaces comparison only; kernels copy nested evidence
    # before changes. Isolate the top-level setup without duplicating raw bars.
    def working_row(row):
        return ({**row, 'setup_evidence': dict(row['setup_evidence'])}
                if machine_policy_only else deepcopy(row))
    train = [working_row(r) for r in population if len(dates) == 1 or r["source_date"] < dates[-1]]
    holdout = [working_row(r) for r in population if len(dates) > 1 and r["source_date"] == dates[-1]]
    if training_through_date:
        train = [working_row(r) for r in population if r['source_date'] <= training_through_date]
        holdout = [working_row(r) for r in population if r['source_date'] > training_through_date]
    result['training_through_date'] = training_through_date or max(r['source_date'] for r in train)
    result['holdout_boundary_basis'] = 'explicit_forward_boundary' if training_through_date else 'last_source_date'

    identity = _machine_opportunity_id
    # Floors govern publication only; one valid raw opportunity can be researched.
    baseline_policy = parent if 'strategy' in parent else strategy.seed(parent, scope)
    baseline_exclusions = []
    for row in train + holdout:
        try:
            incumbent_setup = row["setup_evidence"]
            if 'strategy' not in parent:
                incumbent_setup, _, _ = strategy.rebuild(incumbent_setup, baseline_policy)
            # Rebuild facts while retaining every actual incumbent hierarchy rule.
            baseline = mechanistic_entry_policy_decision(incumbent_setup, policy=parent)
            action = baseline['action']
        except (ValueError, TypeError, KeyError) as exc:
            baseline_exclusions.append(dict(decision_trace_id=row['decision_trace_id'], reason=str(exc)))
            continue
        row["comparison"] = {**(row.get("comparison") or {}), "historical_machine_action": row.get("machine_action") or (row.get("comparison") or {}).get("incumbent_machine_action") or action, "incumbent_machine_action": action,
                             "control_action": "BUY" if action == "ENTER_NOW" else "WAIT", "incumbent_machine_reason": baseline.get("reason")}
    excluded_ids = {item['decision_trace_id'] for item in baseline_exclusions}
    train = [r for r in train if r['decision_trace_id'] not in excluded_ids]
    holdout = [r for r in holdout if r['decision_trace_id'] not in excluded_ids]
    result['source_exclusions'].extend(baseline_exclusions)
    result['supported_population_count'] = len(train) + len(holdout)
    if not train:
        return {**result, 'blocker': 'strategy_no_replayable_training_rows'}
    support_blocker = ('strategy_chronological_holdout_missing' if len(dates) < 2 else
        'strategy_supported_opportunity_floor' if len({identity(r) for r in train}) < 10 or len({identity(r) for r in holdout}) < 3 else None)
    operating_count = sum('operating_comparison_input' in r for r in train + holdout)
    result['operating_population_count'] = operating_count
    operating_complete = operating_count == len(train) + len(holdout)
    if not operating_complete and not machine_policy_only:
        result.update(blocker_owner='entry_setup_paired_replay_batch/strategy_owner_replay',
            closure_test='same_opportunities_candidate_auxiliary_exact_setup_and_complete_owner_cost_capital_replay')
    prepared_paths = {id(row): _machine_path_value(row) for row in train + holdout} if machine_policy_only else {}
    evaluation_cache = {}
    def evaluate(rows, candidate):
        cache_key = (tuple(id(r) for r in rows), strategy.digest(candidate))
        if machine_policy_only and cache_key in evaluation_cache:
            return evaluation_cache[cache_key]
        selected, changed, downstream, actions = [], set(), True, []
        fallback_counts = Counter()
        transitions, changed_attempts = Counter(), []
        skipped = Counter()
        for row in rows:
            old = row["comparison"]["incumbent_machine_action"]
            # A cost/path exclusion is policy-independent. Keep it in the
            # economic denominator manifest, but do not invent a replay action.
            # Every existing entry still replays, including unpriced entries:
            # their changed admission must continue to block promotion.
            reason = prepared_paths[id(row)][1] if machine_policy_only else None
            if reason and old in {"BLOCK", "RECHECK"}:
                actions.append(None)
                skipped[reason] += 1
                continue
            decision = (dict(action=row['comparison']['incumbent_machine_action']) if machine_policy_only and candidate == parent
                        else mechanistic_entry_policy_decision(row["setup_evidence"], policy=candidate))
            actions.append(decision['action'])
            fallback_counts[(decision.get('strategy_selection') or {}).get('fallback_reason', 'legacy')] += 1
            old = row["comparison"]["incumbent_machine_action"]
            transitions[old + '->' + decision['action']] += 1
            if decision["action"] != old:
                changed.add(identity(row))
                changed_attempts.append(dict(decision_trace_id=row['decision_trace_id'],
                    raw_sha256=row['setup_evidence']['strategy_raw_sha256'],
                    incumbent_action=old, candidate_action=decision['action'],
                    candidate_setup_sha256=(decision.get('effective_setup_evidence') or row['setup_evidence'])['evidence_sha256']))
            if decision["action"] == "ENTER_NOW" and not machine_policy_only:
                selected.append(row)
                # The auxiliary screen consumes strategy-dependent facts. An
                # incumbent verdict must never be relabeled as candidate PASS.
                operating = row.get("operating_comparison_input") or {}
                frozen_setup = (operating.get("input") or {}).get("entry_setup_evidence_v1") or {}
                rebuilt = decision.get("effective_setup_evidence") or row["setup_evidence"]
                def fact_hash(value):
                    return strategy.digest({k:v for k,v in value.items() if k not in {
                        'evidence_sha256', 'strategy_raw_input', 'strategy_raw_sha256', 'strategy_selection'}})
                # Exact unchanged AI facts can reuse the frozen actual screen.
                # Changed facts require the downstream owner's paired replay.
                frozen_assessment = (operating.get('input') or {}).get('mechanistic_entry_assessment')
                provider_assessment = {k:v for k,v in decision.items() if k not in {'strategy_selection', 'effective_setup_evidence'}}
                downstream = (downstream and bool(frozen_setup) and fact_hash(frozen_setup) == fact_hash(rebuilt)
                    and isinstance(frozen_assessment, dict) and frozen_assessment == provider_assessment)
        economics = (_machine_admission_metrics(rows, actions, prepared_paths=[prepared_paths[id(r)] for r in rows]) if machine_policy_only else
            _machine_sequence_operating_metrics(rows, {r["decision_trace_id"] for r in selected}, candidate))
        arm = dict(source_dates=sorted({r["source_date"] for r in rows}),
            opportunity_ids=sorted({identity(r) for r in rows}), changed_opportunity_ids=sorted(changed),
            source_complete=all("operating_comparison_input" in r for r in rows),
            downstream_context_bound=downstream, economics=economics,
            action_transition_counts=dict(transitions), changed_attempts=changed_attempts,
            fallback_counts=dict(fallback_counts),
            incumbent_enter_now_changed_count=sum(v for k,v in transitions.items() if k.startswith('ENTER_NOW->') and k != 'ENTER_NOW->ENTER_NOW'))
        if machine_policy_only:
            arm['replay_coverage'] = dict(
                version='machine_economic_replay_v1', population_count=len(rows),
                replayed_count=len(rows) - sum(skipped.values()),
                excluded_nonentry_count=sum(skipped.values()),
                excluded_nonentry_reason_counts=dict(skipped),
                all_existing_entries_replayed=True,
                transition_scope='replayed_rows_only')
            # Candidates are unique; retaining all detailed arms provides no
            # reuse and grows memory with candidate_count * population_count.
            evaluation_cache.clear()
            evaluation_cache[cache_key] = arm
        return arm
    selectors = [None]
    # Boundaries are derived only from predecision training features, never outcomes.
    values = defaultdict(list)
    for row in train:
        setup = row["setup_evidence"]
        for name, value in strategy.features(setup["strategy_raw_input"], setup).items():
            if value is not None:
                values[name].append(value)
    for name, observations in sorted(values.items()):
        unique = sorted(set(observations))
        if len(unique) > 1:
            for boundary in sorted({unique[len(unique)//3], unique[2*len(unique)//3]}):
                selectors.extend((name, boundary, side) for side in ("lt", "ge"))
    domains = {k: sorted(set(v[1]) | {strategy.default_profile(parent)[k]}) for k,v in strategy.REGISTRY.items()}
    support = {name: sum(strategy.coordinate_supported(name, r['setup_evidence']['strategy_raw_input']) for r in train)
               for name in domains}
    unsupported_coordinates = [name for name, count in support.items() if not count]
    for name in unsupported_coordinates:
        domains[name] = [strategy.default_profile(parent)[name]]
    result.update(unsupported_coordinates=unsupported_coordinates, coordinate_support_counts=support,
                  registry_contract=strategy.registry_contract(), domain_source='train_only',
                  unsupported_source_contracts=['ordered_large_sell_event_and_recovery_ticks_not_captured'])
    # Expand the initial seed by one bounded step on both edges. This domain is
    # frozen before inspecting holdout outcomes; the grid is not a permanent cap.
    for name, grid in domains.items():
        if len(grid) > 1:
            low, high = strategy.coordinate_bounds(name)
            step = max(1, (max(grid)-min(grid)) // 2) if isinstance(strategy.REGISTRY[name][0], int) else (max(grid)-min(grid))/2
            domains[name] = sorted(set(grid) | {max(low,min(grid)-step), min(high,max(grid)+step)})
    # Priority uses only predecision blockers/source support, never path labels.
    blocker_text = ' '.join(str(r['comparison'].get('incumbent_machine_reason') or '') + ' ' +
        json.dumps(r['setup_evidence'].get('hard_blockers') or []) for r in train).lower()
    prior_single = set((((previous or {}).get('train_checkpoint') or {}).get('group_counts') or {}).get('single', {}).get('coordinates') or [])
    priority_coordinates = sorted((k for k in domains if len(domains[k]) > 1), key=lambda k: (
        -int(any(token in blocker_text for token in k.split('_') if len(token) > 4)),
        k in prior_single, -support[k], strategy.digest([input_sha256, k])))
    result['search_domain'] = dict(domains=domains, selectors=selectors, priority_coordinates=priority_coordinates,
        budget=strategy.SEARCH_BUDGET, version=strategy.SEARCH_VERSION, search_seed=input_sha256,
        priority_basis='predecision_blockers_unvisited_source_support')
    start = ((previous or {}).get('search') or {}).get('cursor', 0) if (previous or {}).get('input_sha256') == input_sha256 else 0
    if machine_policy_only and start:
        frozen_domain = previous.get('search_domain') or {}
        priority_coordinates = frozen_domain.get('priority_coordinates', priority_coordinates)
        result['search_domain']['priority_coordinates'] = priority_coordinates
        result['evaluated_candidate_count'] = previous.get('evaluated_candidate_count', 0)
    frozen = (previous or {}).get('candidate') or {}
    if ((not machine_policy_only or (previous or {}).get('selection_basis') == strategy.MACHINE_SELECTION_VERSION)
        and not training_through_date and frozen.get('parent_sha256') == strategy.digest(parent)
        and frozen.get('evidence', {}).get('holdout', {}).get('source_dates')
        and max(frozen['evidence']['holdout']['source_dates']) >= dates[-1]):
        frozen = deepcopy(frozen)
        try:
            frozen['evidence'] = {**frozen['evidence'], 'train': evaluate(train, frozen['policy']), 'holdout': evaluate(holdout, frozen['policy'])}
            if machine_policy_only:
                frozen['evidence']['incumbent_train'] = evaluate(train, parent)
        except (ValueError, TypeError, KeyError) as exc:
            return {**result, 'status': 'unsupported_strategy_replay', 'blocker': str(exc),
                'selection_status': 'frozen_candidate_replay_failed'}
        frozen['evidence_sha256'] = strategy.digest(frozen['evidence'])
        errors = strategy.promotion_errors(frozen, parent, scope)
        if machine_policy_only:
            result.update(schema='main_entry_machine_policy_selection_v1',
                machine_policy=frozen['policy'], machine_policy_sha256=frozen['policy_sha256'],
                machine_evidence=frozen['evidence'], auxiliary_ai_required=False,
                selection_basis=strategy.MACHINE_SELECTION_VERSION,
                holdout_status='evaluated_after_selection',
                runtime_effect=False, allowed_runtime_apply=False)
        return {**result, 'candidate': frozen, 'promotion_pass': not errors,
            'promotion_errors': errors, 'status': 'eligible' if not errors else 'hold_candidate',
            'selection_status': 'frozen_before_same_holdout_revision'}
    saved = (previous or {}).get('train_checkpoint') or {} if start else {}
    best, best_evidence, best_score = saved.get('best'), saved.get('best_evidence'), saved.get('best_score')
    best_score = tuple(best_score) if isinstance(best_score, (tuple, list)) else best_score
    if machine_policy_only:
        incumbent_evidence = evaluate(train, parent)
        result['incumbent_evidence'] = dict(train=incumbent_evidence)
        incumbent_score = _machine_admission_rank(incumbent_evidence['economics'],
            node_count=len(parent.get('strategy', {}).get('nodes') or {'root': {}}))
        if all(v is not None for v in incumbent_score[:3]) and (best_score is None or incumbent_score >= best_score):
            best, best_evidence, best_score = deepcopy(parent), incumbent_evidence, incumbent_score
    blockers = Counter((previous or {}).get('candidate_blockers') or {}) if start else Counter()
    visited = set(saved.get('visited_hashes') or [])
    group_counts = deepcopy(saved.get('group_counts') or {})
    result['selection_state'] = 'searching_train'
    machine_scores = list((previous or {}).get('machine_candidate_scores') or []) if machine_policy_only and start else []
    research_candidates = deepcopy((previous or {}).get('research_candidates') or []) if (previous or {}).get('input_sha256') == input_sha256 else []
    for candidate, progress in strategy.joint_candidates(parent, scope, domains=domains, selectors=selectors, start=start, limit=limit,
            **({'local_first': True, 'priority_coordinates': priority_coordinates, 'search_seed': input_sha256} if machine_policy_only else {})):
        result["search"] = progress
        counts = group_counts.setdefault(progress.get('group', 'legacy'), dict(attempted=0, invalid=0, evaluated=0, deduplicated=0, coordinates=[]))
        counts['attempted'] += 1
        counts['coordinates'] = sorted(set(counts['coordinates']) | set(progress.get('changed_coordinates') or []))
        if candidate is None:
            counts['invalid'] += 1
            continue
        candidate_hash = strategy.digest(candidate)
        if candidate_hash in visited:
            counts['deduplicated'] += 1
            continue
        visited.add(candidate_hash)
        try:
            evidence = evaluate(train, candidate)
        except (ValueError, TypeError, KeyError) as exc:
            blockers[str(exc)] += 1
            counts['replay_failed'] = counts.get('replay_failed', 0) + 1
            continue
        result["evaluated_candidate_count"] += 1
        counts["evaluated"] += 1
        if evidence['changed_attempts']:
            research_candidates.append(dict(policy=candidate, policy_sha256=strategy.digest(candidate),
                action_transition_counts=evidence['action_transition_counts'], changed_attempts=evidence['changed_attempts'],
                changed_opportunity_count=len(evidence['changed_opportunity_ids']),
                downstream_context_bound=evidence['downstream_context_bound'],
                runtime_effect=False, allowed_runtime_apply=False, metric_role='funnel_count'))
            research_candidates.sort(key=lambda item: (-item['changed_opportunity_count'], item['policy_sha256']))
            del research_candidates[3:]
        economy = evidence["economics"]
        if machine_policy_only:
            delta = economy.get('paired_admission_delta_pct')
            selected_ev = economy.get('selected_path_ev_pct')
            worst = economy.get('worst_selected_path_pct')
            win_rate = economy.get('win_rate_pct')
            complexity = sum(sum(v != node.get('fallback_profile', strategy.default_profile(parent))[k] for k,v in node['profile'].items()) for node in candidate['strategy']['nodes'].values())
            score = _machine_admission_rank(economy, node_count=len(candidate['strategy']['nodes']), complexity=complexity)
            machine_scores.append(dict(policy_sha256=strategy.digest(candidate),
                search_group=progress.get('group'), node_count=len(candidate['strategy']['nodes']),
                fallback_counts=evidence['fallback_counts'],
                replay_coverage=evidence['replay_coverage'],
                profile_changes={k:v for k,v in strategy.default_profile(candidate).items()
                                 if v != strategy.default_profile(parent)[k]},
                economics=economy, action_transition_counts=evidence['action_transition_counts']))
            if (delta is not None and selected_ev is not None and win_rate is not None
                and worst is not None and score[0] is not None
                and not economy['unevaluated_existing_entry_changes']
                and (best_score is None or score > best_score)):
                best, best_evidence, best_score = candidate, evidence, score
            result['train_checkpoint'] = dict(best=best, best_evidence=best_evidence, best_score=best_score,
                visited_hashes=sorted(visited), group_counts=group_counts)
            result['machine_candidate_scores'] = machine_scores
            if checkpoint:
                checkpoint(result)
            continue
        if (economy.get("status") != "supported_operating_comparison"
            or not evidence["source_complete"] or not evidence["downstream_context_bound"]):
            blockers[economy.get("blocker") or "strategy_candidate_auxiliary_context_unbound"] += 1
            continue
        score = economy.get("daily_net_profit_delta_krw")
        if score is not None and score > 0 and (best_score is None or score > best_score):
            best, best_evidence, best_score = candidate, evidence, score
    result['train_checkpoint'] = dict(best=best, best_evidence=best_evidence, best_score=best_score,
        visited_hashes=sorted(visited), group_counts=group_counts)
    result["search_complete"] = result.get("search", {}).get("search_complete", False)
    result['selection_state'] = 'selection_frozen' if result['search_complete'] else 'searching_train'
    if machine_policy_only and not result['search_complete']:
        # Persist a promising train candidate without consuming the holdout.
        result.update(machine_candidate_scores=machine_scores, candidate_blockers=dict(blockers),
                      research_candidates=research_candidates, status='searching_train')
        if checkpoint:
            checkpoint(result)
        return result
    result["candidate_blockers"] = dict(blockers)
    result['research_candidates'] = research_candidates
    result['research_only'] = True
    result['research_status'] = ('action_changes_found' if research_candidates else
        'no_action_change_in_search_space' if result['search_complete'] else 'search_incomplete')
    if machine_policy_only:
        machine_evidence = dict(train=best_evidence, incumbent_train=incumbent_evidence,
            evaluation_contract=dict(selection_version=strategy.MACHINE_SELECTION_VERSION,
                evaluation_basis=strategy.MACHINE_EVALUATION_BASIS, input_sha256=input_sha256,
                source_contract_sha256=result['source_contract_sha256'], parent_sha256=strategy.digest(parent),
                scope=list(scope), training_through_date=result['training_through_date']))
        holdout_status = 'unavailable_or_no_candidate'
        if best is not None and holdout:
            try:
                machine_evidence['holdout'] = evaluate(holdout, best)
                holdout_status = 'evaluated_after_selection'
            except (ValueError, TypeError, KeyError) as exc:
                holdout_status = 'unsupported'
                machine_evidence['holdout'] = {'blocker': str(exc)}
        candidate = (dict(schema='main_entry_strategy_candidate_v2',
            evaluation_basis=strategy.MACHINE_EVALUATION_BASIS, selection_score_version=strategy.MACHINE_SELECTION_VERSION, scope=list(scope),
            parent_policy=deepcopy(parent), parent_sha256=strategy.digest(parent),
            policy=best, policy_sha256=strategy.digest(best), evidence=machine_evidence,
            evidence_sha256=strategy.digest(machine_evidence), selected_without_holdout=True)
            if best is not None else None)
        if best is not None and holdout:
            result['incumbent_evidence']['holdout'] = evaluate(holdout, parent)
        errors = strategy.promotion_errors(candidate, parent, scope) if candidate else ['no_evaluable_machine_candidate']
        return {**result, 'schema': 'main_entry_machine_policy_selection_v1',
            'status': 'selected_machine_policy' if best is not None else 'no_evaluable_machine_candidate',
            'machine_policy': best, 'machine_policy_sha256': strategy.digest(best) if best is not None else None,
            'machine_evidence': machine_evidence, 'auxiliary_ai_required': False,
            'machine_candidate_scores': machine_scores,
            'candidate': candidate, 'promotion_pass': not errors, 'promotion_errors': errors,
            'selection_basis': strategy.MACHINE_SELECTION_VERSION,
            'holdout_status': holdout_status, 'selection_state': 'holdout_evaluated',
            'runtime_effect': False, 'allowed_runtime_apply': False}
    if support_blocker:
        return {**result, 'status': 'hold_sample', 'blocker': support_blocker}
    if result['evaluated_candidate_count'] == 0 and blockers:
        return {**result, 'status': 'unsupported_strategy_replay', 'blocker': 'strategy_candidates_not_replayable'}
    if best is None:
        status = ('unsupported_downstream' if blockers or not operating_complete else
                  'search_incomplete' if not result['search_complete'] else 'evaluated_no_edge')
        return {**result, 'status': status,
                'blocker': 'strategy_candidate_economic_support_missing' if blockers else 'no_train_improvement'}
    # Exactly one selected vector reaches the independent chronological holdout.
    try:
        evidence = dict(train=best_evidence, holdout=evaluate(holdout, best))
    except (ValueError, TypeError, KeyError) as exc:
        return {**result, 'status': 'unsupported_strategy_replay', 'blocker': str(exc)}
    candidate = dict(schema="main_entry_strategy_candidate_v2", scope=list(scope),
        parent_policy=deepcopy(parent), parent_sha256=strategy.digest(parent), policy=best, policy_sha256=strategy.digest(best),
        evidence=evidence, evidence_sha256=strategy.digest(evidence), selected_without_holdout=True)
    errors = strategy.promotion_errors(candidate, parent, scope)
    return {**result, "candidate": candidate, "promotion_pass": not errors,
            "research_only": bool(errors),
            "promotion_errors": errors, "status": "eligible" if not errors else "hold_candidate"}


def build_machine_policy_report(rows, *, source_receipt, target_date, data_root=Path('data'), limit=96, write_checkpoints=False, training_through_date=None):
    """Generate a machine policy artifact only; no downstream or publication loop."""
    from src.engine.scalping import entry_strategy_policy as strategy
    from src.engine.scalping.mechanistic_entry_runtime_policy import load_effective, for_cohort
    incumbent = load_effective(data_root=data_root, target_date=datetime.now(KST).date().isoformat())
    prior = _load_json(data_root / 'report' / 'ai_decision_action_outcome_calibration' / f'machine_policy_{target_date}.json')
    prior = prior.get('selections', {}) if _artifact_content_sha256_valid(prior) else {}
    published_hash = (incumbent or {}).get('source_file_sha256')
    published = (_load_json(data_root / 'runtime' / 'mechanistic_entry_policy' / 'sources' / f'{published_hash}.json')
                 if _is_sha256(published_hash) else {})
    published_scopes = published.get('selections') or published.get('strategy_refinements_by_scope') or {}

    if training_through_date and not CLEAN_BASELINE_DATE <= training_through_date <= target_date:
        raise ValueError('strategy_training_boundary_invalid')
    scopes = sorted({(r['effective_venue'], r['session_bucket']) for r in rows})
    selections = {}
    for cohort in scopes:
        if not mechanistic_scope_supported(*cohort):
            continue
        scoped = for_cohort(incumbent, cohort) if incumbent else None
        parent = (scoped or {}).get('machine_policy') or MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1
        scoped_rows = [r for r in rows if (r['effective_venue'], r['session_bucket']) == cohort]
        population, contract = _common_refinement_population([], scoped_rows,
            target_date=target_date, source_receipt=source_receipt, paired_contract={}, cohort=cohort, allow_attempt_identity_fallback=True, retain_unevaluated_machine_rows=True)
        contract['economic_kernel_sha256'] = _canonical_sha256({
            name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
            for name in ('ai_action_outcome_calibration.py', 'entry_strategy_policy.py',
                         'ai_decision_quality.py', 'entry_setup_evidence.py', 'entry_candle_context.py')})
        checkpoint_path = data_root / 'report' / 'ai_decision_action_outcome_calibration' / f"machine_train_checkpoint_{target_date}_{'_'.join(cohort)}.json"
        saved = _load_json(checkpoint_path)
        prior_selection = prior.get('|'.join(cohort))
        # A source day used for training cannot later become a fresh holdout
        # merely because the scheduled CLI omitted an operator's boundary.
        published_selection = published_scopes.get('|'.join(cohort)) or {}
        consumed_days = (((published_selection.get('candidate') or {}).get('evidence') or {}).get('train') or {}).get('source_dates') or []
        prior_boundary = (prior_selection or {}).get('training_through_date') if (prior_selection or {}).get('holdout_boundary_basis') == 'explicit_forward_boundary' else None
        consumed_through = max([*consumed_days, *([prior_boundary] if prior_boundary else [])], default=None)
        effective_boundary = training_through_date
        if consumed_through:
            if training_through_date and training_through_date < min(consumed_through, target_date):
                raise ValueError('strategy_training_boundary_reuses_consumed_holdout')
            if effective_boundary is None and scoped_rows and consumed_through >= max(r['source_date'] for r in scoped_rows):
                effective_boundary = min(consumed_through, target_date)

        if _artifact_content_sha256_valid(saved) and saved.get('selection_state') == 'searching_train':
            prior_selection = saved
        def save_progress(value):
            if write_checkpoints:
                _atomic_write_json(checkpoint_path, _with_artifact_content_sha256(value))
        selections['|'.join(cohort)] = build_main_strategy_refinement(population,
            parent=parent, scope=cohort, source_contract=contract, previous=prior_selection, limit=limit, machine_policy_only=True, checkpoint=save_progress, training_through_date=effective_boundary)
        selections['|'.join(cohort)]['source_acceptance'] = {k:v for k,v in contract.items() if k not in {'natural_machine_source_receipt', 'paired_source_contract'}}
        save_progress(selections['|'.join(cohort)])
    policy = {scope: selection['machine_policy'] for scope, selection in selections.items()
              if selection.get('machine_policy') is not None and selection.get('promotion_pass') is True}
    return _with_artifact_content_sha256(dict(schema='main_machine_policy_report_v1',
        target_date=target_date, generated_at=datetime.now(KST).isoformat(),
        evaluation_basis=strategy.MACHINE_EVALUATION_BASIS, selection_score_version=strategy.MACHINE_SELECTION_VERSION,
        policy_by_scope=policy, policy_sha256=strategy.digest(policy), selections=selections,
        report_scope='main_mechanistic_entry', noncompact_sections_refreshed=True,
        strategy_refinements_by_scope=selections,
        status='machine_policy_generated' if policy else 'no_evaluable_machine_candidate',
        metric_role='sim_probe_ev', decision_authority='machine_policy_selection_only',
        window_policy='chronological_train_then_holdout_diagnostic', sample_floor='one_valid_episode_for_selection',
        primary_decision_metric=strategy.MACHINE_SELECTION_VERSION, source_quality_gate='verified_raw_full_cost_terminal_path',
        auxiliary_ai_required=False, runtime_effect=False, allowed_runtime_apply=False,
        forbidden_uses=['realized_pnl', 'portfolio_pnl', 'auxiliary_ai_pass']))


def build_main_mechanistic_report(
    *, target_date: str, data_root: Path = Path("data"), incumbent_date: str | None = None
) -> dict[str, Any]:
    """Build only the active main-machine evaluation and publisher source."""
    report_root = data_root / "report"
    paired_rows, paired_contract = _mechanistic_source_rows(
        report_root / PAIRED_SUBDIR,
        target_date=target_date, all_supported_cohorts=True,
    )
    from src.engine.scalping.mechanistic_entry_runtime_policy import load_effective

    incumbent = load_effective(data_root=data_root, target_date=incumbent_date or target_date)
    parent = (incumbent or {}).get("machine_policy") or MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1
    # The compact materialization contains only the provider-screened subset.
    # Main-machine tuning also needs BLOCK/RECHECK outcomes, so reuse the
    # existing bounded path labeler over the verified machine captures rather
    # than allowing compact coverage to redefine this population.
    machine_rows, machine_capture_census = load_machine_observation_rows(
        data_root, target_date=target_date
    )
    source_receipt = _machine_ai_natural_source_receipt(data_root, target_date)
    source_receipt = _compact_history_receipt(
        data_root, target_date, machine_rows, incumbent, source_receipt
    )
    case_table = build_machine_decision_case_table(
        machine_rows,
        capture_census=machine_capture_census,
        source_receipt=source_receipt,
    )
    case_table["ai_quality_diagnostics"] = materialized_quality_diagnostics(
        data_root, target_date
    )
    from src.engine.scalping import compact_auxiliary_paired_replay as compact

    operating_projection = _machine_operating_projection(
        data_root, [r["source_date"] for r in machine_rows] + [target_date])
    from src.engine.scalping.entry_setup_scalping_rollout import AUTO_PROMOTION_SCOPES
    from src.engine.scalping.mechanistic_entry_runtime_policy import for_cohort
    previous_selections, previous_hierarchy, previous_joint = {}, {}, {}
    previous_strategy = {}
    joint_population, joint_parents = [], {}
    for prior_path in sorted((report_root / "ai_decision_action_outcome_calibration").glob("ai_decision_action_outcome_calibration_*.json")):
        prior = compact.read(prior_path)
        if (_artifact_content_sha256_valid(prior) and prior.get("target_date", "9999") <= target_date):
            previous_strategy.update(prior.get("strategy_refinements_by_scope") or {})
            if (prior.get('joint_scope_economics') or {}).get('forward_selection'):
                previous_joint = prior['joint_scope_economics']
            for scope, evaluated in (prior.get("mechanistic_refinements_by_scope") or {}).items():
                frozen = evaluated.get("forward_selection")
                if frozen and frozen.get("economic_contract") == "machine_operating_daily_net_v1":
                    previous_selections[scope] = frozen
            for scope, extension in ((prior.get("hierarchical_entry_quality") or {}).get("runtime_extensions_by_scope") or {}).items():
                frozen = extension.get("forward_selection")
                if frozen and frozen.get("economic_contract") == "machine_operating_daily_net_v1":
                    previous_hierarchy[scope] = frozen
    scope_evaluations, extensions = {}, {}
    # Reuse the existing cross-scope cache, only for paths that actually need
    # cost relabeling. Already priced or unsupported historical rows need no
    # second full pipeline scan.
    repricing_rows = [r for r in paired_rows if _machine_source_contract_valid(r)
        and _full_entry_cost_pct(r["comparison"].get("entry_cost_contract"), source_date=r["source_date"]) is None
        and (r.get("label_context") or {}).get("reference_price_type") == "executable_ask"]
    repricing_profiles = {(day, venue): _hierarchy_cost_profiles(data_root, day, venue)
        for day, venue in {(r["source_date"], r["entry_group_observation"]["key_parts"]["venue"]) for r in repricing_rows}}
    repricing_rows = [r for r in repricing_rows
        if r["stock_code"] in repricing_profiles[(r["source_date"], r["entry_group_observation"]["key_parts"]["venue"])]]
    price_cache = _hierarchy_pipeline_price_cache(repricing_rows, data_root) if repricing_rows else {}
    strategy_evaluations = {}
    for scope in AUTO_PROMOTION_SCOPES:
        cohort = tuple(scope.split("|"))
        scoped_incumbent = for_cohort(incumbent, cohort) if incumbent else None
        scope_parent = (scoped_incumbent or {}).get("machine_policy") or parent
        scoped_paired = [r for r in paired_rows if tuple(
            _as_dict(_as_dict(r.get("entry_group_observation")).get("key_parts")).get(k)
            for k in ("venue", "session_bucket")) == cohort]
        repriced, cost_census = relabel_hierarchy_source_rows(
            scoped_paired, data_root, cohort=cohort, pipeline_prices_by_day=price_cache)
        population, contract = _common_refinement_population(
            repriced, machine_rows, target_date=target_date,
            source_receipt=source_receipt, paired_contract=paired_contract,
            natural_conflicting_attempt_identity_count=case_table["conflicting_attempt_identity_count"],
            natural_conflicting_evaluation_keys=case_table["conflicting_evaluation_keys"],
            cohort=cohort, operating_projection=operating_projection)
        strategy_population, strategy_contract = population, contract
        population, contract = _current_structure_population(population, contract)
        contract["economic_kernel_sha256"] = _canonical_sha256({
            name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
            for name in ("ai_action_outcome_calibration.py", "entry_setup_evidence.py", "entry_candle_context.py",
                         "compact_auxiliary_paired_replay.py", "strategy_owner_replay.py", "entry_strategy_policy.py")})
        joint_population.extend(population)
        joint_parents[scope] = scope_parent
        contract["incumbent_scope_verified"] = scoped_incumbent is not None
        contract["forward_holdout_required"] = True
        contract["frozen_selection"] = previous_selections.get(scope)
        contract["frozen_hierarchy"] = previous_hierarchy.get(scope)
        strategy_evaluations[scope] = build_main_strategy_refinement(
            strategy_population, parent=scope_parent, scope=cohort, source_contract={**strategy_contract, "economic_kernel_sha256": contract["economic_kernel_sha256"]}, previous=previous_strategy.get(scope), machine_policy_only=True)
        evaluated = build_clean_baseline_mechanistic_refinement(
            report_root / PAIRED_SUBDIR, target_date=target_date,
            source_rows=population, source_contract=contract, parent_policy=scope_parent)
        extension = build_mechanistic_hierarchy_candidate(
            population, target_date=target_date, parent_policy=scope_parent,
            cohort=cohort, population_source_contract=contract)
        extension["full_cost_relabel_census"] = cost_census
        extension["machine_capture_census"] = machine_capture_census
        extensions[scope] = extension
        scope_evaluations[scope] = evaluated
        if scope == "KRX|KRX_REGULAR":
            refinement, refinement_contract, hierarchy = evaluated, contract, extension
    hierarchical = {
        "schema": "main_mechanistic_entry_machine_only_hierarchy_v1",
        "status": hierarchy.get("status"),
        "promotion_pass": hierarchy.get("promotion_pass") is True,
        "policy_candidate": hierarchy.get("policy_candidate"),
        "runtime_extension": hierarchy,
        "runtime_extensions_by_scope": extensions,
        "machine_decision_case_table": case_table,
        "diagnostic_sections_reused": False,
    }
    report = {
        "schema": SCHEMA,
        "policy_version": POLICY_VERSION,
        "target_date": target_date,
        "evaluation_source_date": target_date,
        "generated_at": datetime.now(KST).isoformat(),
        "status": "main_mechanistic_entry_full_evaluation_complete",
        "clean_tuning_baseline_date": CLEAN_BASELINE_DATE,
        "report_scope": "main_mechanistic_entry",
        "noncompact_sections_refreshed": True,
        "evaluation_contract_version": (
            MAIN_MECHANISTIC_EVALUATION_CONTRACT_VERSION
        ),
        "evaluation_fingerprint": _main_mechanistic_input_fingerprint(
            data_root, target_date, incumbent_date=incumbent_date
        ),
        "candidate_count": 0,
        "selected_review_candidate": None,
        "ofi_smoothing_audit": {"status": "not_recomputed_machine_only"},
        "mechanistic_entry_refinement": refinement,
        "machine_full_evaluation": {
            **_machine_full_evaluation_projection(refinement, refinement_contract),
            "summary_scope": "KRX|KRX_REGULAR",
            "scope_evaluations": {key: _machine_full_evaluation_projection(value, value["source_contract"])
                                  for key, value in scope_evaluations.items()},
            "registered_scope_count": len(AUTO_PROMOTION_SCOPES),
            "scope_disposition_complete": len(scope_evaluations) == len(AUTO_PROMOTION_SCOPES),
        },
        "mechanistic_refinements_by_scope": scope_evaluations,
        "strategy_refinements_by_scope": strategy_evaluations,
        "operating_source_handoff": {k: v for k, v in operating_projection.items() if k != "rows"},
        "post_apply_decision_version_performance": compact.applied_decision_version_performance(
            compact.read(data_root / "report/entry_split_order_plan" / f"entry_split_order_plan_{target_date}.json"), day=target_date),
        "joint_scope_economics": _machine_joint_scope_evaluation(joint_population, joint_parents,
            scope_evaluations, extensions, previous_joint, contract['economic_kernel_sha256'], target_date),
        "mechanistic_flow_groups": {
            "status": "not_recomputed_machine_only",
            "source_population": {
                "accepted_unique_trace_count": refinement_contract.get(
                    "accepted_unique_trace_count"
                )
            },
        },
        "hierarchical_entry_quality": hierarchical,
        **OFFLINE_CONTRACT,
    }
    return _with_artifact_content_sha256(report)


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
    hierarchy_parent = json.loads(json.dumps(MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1))
    from src.engine.scalping.mechanistic_entry_runtime_policy import load_effective

    incumbent = load_effective(data_root=data_root, target_date=target_date)
    if incumbent is not None:
        hierarchy_parent = json.loads(json.dumps(incumbent["machine_policy"]))
    machine_observations, machine_capture_census = load_machine_observation_rows(
        data_root, target_date=target_date
    )
    machine_source_receipt = _machine_ai_natural_source_receipt(data_root, target_date)
    machine_source_receipt = _compact_history_receipt(
        data_root, target_date, machine_observations, incumbent, machine_source_receipt
    )
    machine_decision_case_table = build_machine_decision_case_table(
        machine_observations,
        capture_census=machine_capture_census,
        source_receipt=machine_source_receipt,
    )
    machine_decision_case_table["ai_quality_diagnostics"] = materialized_quality_diagnostics(data_root, target_date)
    from src.engine.scalping import compact_auxiliary_paired_replay as compact
    paired = compact.read(compact.report_path(data_root, target_date))
    if compact.valid(paired) and paired.get("source_manifest_sha256") == machine_source_receipt.get("source_manifest_sha256"):
        machine_decision_case_table["compact_auxiliary_screen_outcomes"]["paired_economic_evaluation"] = paired
    all_scope_rows, all_scope_contract = _mechanistic_source_rows(
        report_root / PAIRED_SUBDIR, target_date=target_date, all_supported_cohorts=True
    )
    pipeline_prices_by_day = _hierarchy_pipeline_price_cache(
        all_scope_rows + mechanistic_source_rows, data_root
    )
    hierarchy_rows, hierarchy_cost_census = relabel_hierarchy_source_rows(
        mechanistic_source_rows,
        data_root,
        pipeline_prices_by_day=pipeline_prices_by_day,
    )
    operating_projection = compact.read(compact.report_path(data_root, target_date).with_suffix(".source.json"))
    if compact.valid(operating_projection):
        operating_projection = compact.sealed({**operating_projection,
            "runtime_inference_cost_receipt": compact.runtime_inference_cost_receipt(data_root, target_date)})
    refinement_rows, refinement_contract = _common_refinement_population(
        hierarchy_rows, machine_observations,
        target_date=target_date, source_receipt=machine_source_receipt,
        paired_contract=mechanistic_source_contract,
        natural_conflicting_attempt_identity_count=machine_decision_case_table["conflicting_attempt_identity_count"],
        natural_conflicting_evaluation_keys=machine_decision_case_table["conflicting_evaluation_keys"],
        operating_projection=operating_projection,
    )
    mechanistic_refinement = build_clean_baseline_mechanistic_refinement(
        report_root / PAIRED_SUBDIR, target_date=target_date,
        source_rows=refinement_rows, source_contract=refinement_contract,
        parent_policy=(incumbent or {}).get("machine_policy") or MECHANISTIC_ENTRY_THRESHOLD_POLICY_V1,
    )
    if mechanistic_refinement.get("policy_candidate"):
        hierarchy_parent.pop("hierarchy", None)
        hierarchy_parent["thresholds"].update(mechanistic_refinement["policy_candidate"]["thresholds"])
        hierarchy_parent["version"] = MECHANISTIC_FULL_POPULATION_POLICY_VERSION
        hierarchy_parent["postclose_selection"]["minimum_cost_adjusted_ev_pct"] = (
            MECHANISTIC_REFINEMENT_GATE["minimum_cost_adjusted_ev_pct"]
        )
    hierarchical_entry_quality["runtime_extension"] = (
        build_mechanistic_hierarchy_candidate(
            refinement_rows,
            target_date=target_date,
            parent_policy=hierarchy_parent,
            population_source_contract=refinement_contract,
        )
    )
    if mechanistic_refinement.get("promotion_pass") is not True:
        hierarchical_entry_quality["runtime_extension"]["policy_candidate"] = None
        hierarchical_entry_quality["runtime_extension"]["promotion_pass"] = False
        hierarchical_entry_quality["runtime_extension"]["status"] = (
            "diagnostic_only_parent_economic_gate_not_passed"
        )
    hierarchical_entry_quality["runtime_extension"][
        "machine_capture_census"
    ] = machine_capture_census
    hierarchical_entry_quality["runtime_extension"][
        "full_cost_relabel_census"
    ] = hierarchy_cost_census
    from src.engine.scalping.entry_setup_scalping_rollout import AUTO_PROMOTION_SCOPES

    extensions = {"KRX|KRX_REGULAR": hierarchical_entry_quality["runtime_extension"]}
    for scope in AUTO_PROMOTION_SCOPES:
        if scope == "KRX|KRX_REGULAR":
            continue
        cohort = tuple(scope.split("|"))
        scoped_rows = [
            r
            for r in all_scope_rows
            if tuple(
                _as_dict(
                    _as_dict(r.get("entry_group_observation")).get("key_parts")
                ).get(k)
                for k in ("venue", "session_bucket")
            )
            == cohort
        ]
        repriced, census = relabel_hierarchy_source_rows(
            scoped_rows,
            data_root,
            cohort=cohort,
            pipeline_prices_by_day=pipeline_prices_by_day,
        )
        scoped_incumbent = _as_dict(
            _as_dict((incumbent or {}).get("scope_policies")).get(scope)
        )
        scoped_population, scoped_contract = _common_refinement_population(
            repriced, machine_observations, target_date=target_date,
            source_receipt=machine_source_receipt, paired_contract=all_scope_contract,
            natural_conflicting_attempt_identity_count=machine_decision_case_table["conflicting_attempt_identity_count"],
            natural_conflicting_evaluation_keys=machine_decision_case_table["conflicting_evaluation_keys"],
            cohort=cohort,
        )
        extension = build_mechanistic_hierarchy_candidate(
            scoped_population,
            target_date=target_date,
            parent_policy=scoped_incumbent.get("machine_policy"),
            cohort=cohort,
            population_source_contract=scoped_contract,
        )
        extension["full_cost_relabel_census"] = census
        extensions[scope] = extension
    hierarchical_entry_quality["runtime_extensions_by_scope"] = extensions
    hierarchical_entry_quality["machine_decision_case_table"] = (
        machine_decision_case_table
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
            "runtime_extension": hierarchical_entry_quality["runtime_extension"],
            "runtime_extensions_by_scope": hierarchical_entry_quality[
                "runtime_extensions_by_scope"
            ],
            "machine_decision_case_table": machine_decision_case_table,
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
    machine_full_evaluation = _machine_full_evaluation_projection(
        mechanistic_refinement, refinement_contract
    )
    report = {
        "schema": SCHEMA,
        "policy_version": POLICY_VERSION,
        "target_date": target_date,
        "evaluation_source_date": target_date,
        "report_scope": "main_mechanistic_entry",
        "noncompact_sections_refreshed": True,
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
        "machine_full_evaluation": machine_full_evaluation,
        "mechanistic_flow_groups": mechanistic_flow_groups,
        "hierarchical_entry_quality": hierarchical_entry_quality,
        **OFFLINE_CONTRACT,
    }
    return _with_artifact_content_sha256(report)


def _runtime_policy_publication_errors(
    published_policy: dict | None,
    source_report: dict,
    *,
    publication_date: str | None = None,
) -> list[str]:
    """Verify the canonical next-date receipt emitted by the bounded publisher."""

    from src.engine.scalping.mechanistic_entry_runtime_policy import next_target
    from src.engine.scalping.entry_setup_evidence import (
        MECHANISTIC_PRIMARY_ROLE_CONTRACT,
    )

    if not isinstance(published_policy, dict):
        return ["mechanistic_entry_runtime_policy_not_published"]
    errors = []
    expected_target = next_target(
        publication_date or str(source_report.get("target_date") or "")
    )
    if published_policy.get("target_date") != expected_target:
        errors.append("mechanistic_entry_runtime_policy_target_date_mismatch")
    machine_source = published_policy.get("machine_evaluation_source") or {
        "source_date": published_policy.get("source_date"),
        "artifact_content_sha256": published_policy.get("source_artifact_sha256")
    }
    if machine_source.get("source_date") != source_report.get("target_date"):
        errors.append("mechanistic_entry_runtime_policy_source_date_mismatch")
    if machine_source.get("artifact_content_sha256") != source_report.get(
        "artifact_content_sha256"
    ):
        errors.append("mechanistic_entry_runtime_policy_source_hash_mismatch")
    if published_policy.get("role_contract") != MECHANISTIC_PRIMARY_ROLE_CONTRACT:
        errors.append("mechanistic_entry_runtime_policy_role_contract_mismatch")
    if published_policy.get("actual_order_submitted") is not False:
        errors.append("mechanistic_entry_runtime_policy_order_authority_leak")
    if published_policy.get("all_continuous_adopted") is not True:
        errors.append("mechanistic_entry_runtime_policy_scope_coverage_missing")
    return errors



def ensure_machine_economic_reference(*, data_root: Path, target_date: str) -> dict:
    """Decouple the full-cost source prerequisite from provider replay gates."""
    from zoneinfo import ZoneInfo
    from src.engine.scalping.micro_reversion.economic_reference import build_daily_resolution, atomic_write_json
    from src.engine.scalping.micro_reversion.economic_reference_owner import build_daily_sources

    # Source manifests resolve relative entries against their own directory.
    # Keep generated source paths absolute even when the CLI uses ./data.
    data_root = data_root.resolve()
    root = data_root / "report" / "micro_reversion_economic_reference"
    path = root / f"micro_reversion_economic_reference_{target_date}.json"
    existing = existing_or_gzip_path(path)
    if existing and _hierarchy_cost_profiles(data_root, target_date):
        return {"status": "existing_verified_sources_preserved", "path": str(existing)}
    if datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat() != target_date:
        return {"status": "source_gap_historical_official_master_unavailable", "target_date": target_date, "path": str(path)}
    try:
        private = root / "machine_source_inputs" / target_date
        build_daily_sources(target_date=target_date, policy_path=data_root / "config" / "micro_reversion_economic_policy.json", output_root=private)
        report = build_daily_resolution(target_date=target_date, source_manifest_path=private / "economic_reference_sources.json")
        atomic_write_json(path, report)
        return {"status": report.get("status"), "verified": report.get("verified"), "path": str(path)}
    except (OSError, ValueError, RuntimeError) as exc:
        return {"status": "source_gap_cost_prerequisite_failed", "reason": str(exc), "path": str(path)}


def materialized_quality_diagnostics(data_root: Path, source_day: str) -> dict:
    from src.engine.scalping import ai_decision_quality as quality
    from src.engine.scalping.compact_auxiliary_paired_replay import digest
    path = Path(data_root) / "report/ai_decision_outcome_labels" / f"ai_decision_outcome_labels_{source_day}.json"
    control_path = Path(data_root) / "runtime" / f"ai_decision_quality_control_{source_day}.json"
    labels, control = _load_json(path), _load_json(control_path)
    errors = quality.validate_daily_materialization_reports(
        target_date=source_day, reports={"control": control, "mature": labels})
    return {
        "schema": "ai_quality_materialized_diagnostics_v1", "source_date": source_day,
        "status": "source_gap" if errors else "diagnostic_available",
        "source_label_report_path": str(path), "source_label_report_sha256": digest(labels) if labels else None,
        "source_label_quality_contract_sha256": quality._sha256(labels) if labels else None,
        "original_label_report_sha256": labels.get("original_label_report_sha256"),
        "source_manifest_sha256": (control.get("materialization_inputs") or {}).get("source_manifest_sha256"),
        "diagnostic_price_path_summary": labels.get("diagnostic_price_path_summary") if not errors else None,
        "label_contract_status_counts": labels.get("label_contract_status_counts") if not errors else None,
        "source_label_migration": control.get("source_label_migration"),
        "reasons": errors, "owner": "ai_decision_quality_source_label_materialization",
        "closure_test": "current_source_label_contract_and_exact_content_hash_pass",
        "economic_acceptance_eligible": False, "diagnostic_net_is_realized_profit": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build cumulative exact-trace action/outcome calibration."
    )
    parser.add_argument("--target-date", required=True)
    parser.add_argument("--data-root", type=Path, default=Path("data"))
    parser.add_argument("--write", action="store_true")
    parser.add_argument('--machine-policy-only', action='store_true', help='Generate only the pre-AI machine threshold policy artifact')
    parser.add_argument('--training-through-date', help='Explicit train cutoff; later sources only are diagnostic holdout')
    parser.add_argument('--search-limit', type=int, default=96, help='Machine policy candidate traversal budget')
    parser.add_argument(
        "--machine-only",
        action="store_true",
        help="Refresh only the active main mechanistic evaluator and publisher source",
    )
    parser.add_argument(
        "--publication-date",
        help="KST publication day; effective date is its next KRX trading day",
    )
    parser.add_argument("--ensure-economic-reference-only", action="store_true", help="Prepare only the existing full-cost source before lengthy research; no policy publication")
    parser.add_argument(
        "--require-policy-publication",
        action="store_true",
        help="Fail unless the canonical next-trading-date policy is hash-bound",
    )
    parser.add_argument("--activate-now", action="store_true", help="Activate an eligible strategy generation immediately and carry until superseded")
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args(argv)
    if args.machine_policy_only:
        if (args.machine_only or (args.activate_now and not args.write) or args.require_policy_publication
            or args.ensure_economic_reference_only or args.publication_date or args.search_limit < 1):
            parser.error('--machine-policy-only is a standalone policy-generation action')
        output = args.data_root / 'report' / 'ai_decision_action_outcome_calibration' / f'machine_policy_{args.target_date}.json'
        output.parent.mkdir(parents=True, exist_ok=True)
        with (output.parent / f'machine_policy_{args.target_date}.lock').open('a') as stage_lock:
            fcntl.flock(stage_lock, fcntl.LOCK_EX)
            # Validate current policy before expensive source loading.
            from src.engine.scalping.mechanistic_entry_runtime_policy import load_effective
            load_effective(data_root=args.data_root, target_date=datetime.now(KST).date().isoformat())
            cost_source = ensure_machine_economic_reference(data_root=args.data_root, target_date=args.target_date) if args.write else {}
            rows, source_counts = load_machine_observation_rows(args.data_root, target_date=args.target_date, independent_machine=True)
            result = build_machine_policy_report(rows,
                source_receipt=_machine_ai_natural_source_receipt(args.data_root, args.target_date),
                target_date=args.target_date, data_root=args.data_root, limit=args.search_limit,
                write_checkpoints=args.write, training_through_date=args.training_through_date)
            result = _with_artifact_content_sha256({**result, 'observation_source_counts': source_counts, 'cost_source': cost_source})
            if args.write:
                _atomic_write_json(output, result)
            activation = None
            if args.activate_now:
                from src.engine.scalping.mechanistic_entry_runtime_policy import activate_strategy_report
                activation = activate_strategy_report(output, data_root=args.data_root)
            terminal = _with_artifact_content_sha256(dict(schema='main_machine_policy_terminal_v1',
                target_date=args.target_date, completed_at=datetime.now(KST).isoformat(),
                status='searching_train' if any(r.get('selection_state') == 'searching_train' for r in result['selections'].values()) else 'completed',
                report_sha256=result['artifact_content_sha256'], policy_sha256=result['policy_sha256'],
                evaluation_basis=result.get('evaluation_basis'), selection_score_version=result.get('selection_score_version'),
                selected_scopes=list(result['policy_by_scope']), activation=activation,
                independent_of=['auxiliary_ai', 'widget', 'episode', 'holding', 'exit'], actual_pid_consumed=False))
            if args.write:
                _atomic_write_json(output.with_name(f'machine_policy_terminal_{args.target_date}.json'), terminal)
            print(json.dumps(dict(status=result['status'], policy_sha256=result['policy_sha256'],
                selected_scopes=list(result['policy_by_scope']), strategy_activation=activation,
                path=str(output) if args.write else None)))
        return 0

    if args.ensure_economic_reference_only:
        if not args.write or args.require_policy_publication or args.publication_date:
            parser.error("--ensure-economic-reference-only requires --write and forbids policy publication")
        receipt = ensure_machine_economic_reference(data_root=args.data_root, target_date=args.target_date)
        print(json.dumps(receipt))
        return 0 if receipt.get("verified") is True or receipt.get("status") == "existing_verified_sources_preserved" else 2
    if args.activate_now and not (args.machine_only and args.write):
        parser.error("--activate-now requires --machine-only --write")
    economic_reference_prerequisite = (
        ensure_machine_economic_reference(data_root=args.data_root, target_date=args.target_date)
        if args.write else {"status": "not_requested_read_only"}
    )
    incumbent_date = datetime.now(KST).date().isoformat() if args.activate_now else None
    path = report_path(args.target_date, args.data_root / "report")
    def prepare_report() -> tuple[dict[str, Any], bool]:
        existing = _load_json(path) if args.machine_only and args.write else {}
        current_fingerprint = (
            _main_mechanistic_input_fingerprint(args.data_root, args.target_date, **({"incumbent_date": incumbent_date} if incumbent_date else {}))
            if args.machine_only
            else None
        )
        reused = bool(
            args.machine_only
            and args.write
            and _artifact_content_sha256_valid(existing)
            and existing.get("report_scope") == "main_mechanistic_entry"
            and existing.get("noncompact_sections_refreshed") is True
            and existing.get("evaluation_contract_version")
            == MAIN_MECHANISTIC_EVALUATION_CONTRACT_VERSION
            and existing.get("evaluation_fingerprint") == current_fingerprint
        )
        if reused:
            return existing, True
        prepared = (
            build_main_mechanistic_report(
                target_date=args.target_date, data_root=args.data_root, **({"incumbent_date": incumbent_date} if incumbent_date else {})
            )
            if args.machine_only
            else build_report(target_date=args.target_date, data_root=args.data_root)
        )
        prepared["machine_economic_reference_prerequisite"] = (
            economic_reference_prerequisite
        )
        prepared = _with_artifact_content_sha256(prepared)
        if args.write:
            _atomic_write_json(path, prepared)
        return prepared, False

    if args.machine_only and args.write:
        path.parent.mkdir(parents=True, exist_ok=True)
        with (path.parent / "main_mechanistic_evaluation.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            report, evaluation_reused = prepare_report()
    else:
        report, evaluation_reused = prepare_report()
    published_policy = None
    if args.write:
        from src.engine.scalping.microstructure_reaction_context import refresh_machine_evaluation_link

        machine_table = _as_dict(_as_dict(report.get("hierarchical_entry_quality")).get("machine_decision_case_table"))
        if machine_table.get("microstructure_evaluation") is not None:
            refresh_machine_evaluation_link(path, report_root=args.data_root / "report")
        from src.engine.scalping.mechanistic_entry_runtime_policy import publish

        published_policy = publish(
            path,
            data_root=args.data_root,
            publication_day=args.publication_date,
        )
    if args.activate_now:
        from src.engine.scalping.mechanistic_entry_runtime_policy import activate_strategy_report
        activation_receipt = activate_strategy_report(path, data_root=args.data_root)
        print(json.dumps({"strategy_activation": activation_receipt}))
    if args.require_policy_publication:
        if not args.write:
            parser.error("--require-policy-publication requires --write")
        publication_errors = _runtime_policy_publication_errors(
            published_policy,
            report,
            publication_date=args.publication_date,
        )
        if publication_errors:
            raise RuntimeError(",".join(publication_errors))
    if args.print_summary:
        print(
            json.dumps(
                {
                    "status": report["status"],
                    "candidate_count": report["candidate_count"],
                    "selected_review_candidate": report["selected_review_candidate"],
                    "ofi_smoothing_audit": report["ofi_smoothing_audit"],
                    "machine_full_evaluation": report.get(
                        "machine_full_evaluation"
                    ),
                    "evaluation_reused": evaluation_reused,
                    "runtime_policy_publication": (
                        {
                            "status": "published_or_idempotent",
                            "target_date": published_policy.get("target_date"),
                            "bundle_sha256": published_policy.get("bundle_sha256"),
                            "machine_disposition": published_policy.get(
                                "machine_disposition"
                            ),
                            "hierarchy_disposition": published_policy.get(
                                "hierarchy_disposition"
                            ),
                            "hierarchy_adopted": published_policy.get(
                                "hierarchy_adopted"
                            ),
                            "all_continuous_adopted": published_policy.get(
                                "all_continuous_adopted"
                            ),
                        }
                        if published_policy is not None
                        else {
                            "status": (
                                "not_enabled_no_bootstrapped_policy"
                                if args.write
                                else "not_requested_without_write"
                            )
                        }
                    ),
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
