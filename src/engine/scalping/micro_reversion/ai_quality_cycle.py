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
import stat
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import asdict
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from statistics import fmean, median
from typing import Any, Callable, Iterable, Mapping, Sequence
from zoneinfo import ZoneInfo

from src.engine.scalping import ai_decision_quality as quality
from src.engine.scalping.main_lifecycle_journal import (
    BROKER_EXECUTION_OCCURRENCE_TIME_SOURCE,
    BROKER_EXECUTION_ORDERING_TIME_SOURCE,
    BROKER_EXECUTION_PROVENANCE_SCHEMA,
    BROKER_EXECUTION_RAW_ENVELOPE_SCHEMA,
    BROKER_EXECUTION_RECEIVE_TIME_SOURCE,
    BROKER_EXECUTION_TIMING_SCHEMA,
    CARRY_IN_CUSTODY_SCHEMA,
    CARRY_IN_CUSTODY_REQUIRED_DATE,
    JOURNAL_SCHEMA,
    KIWOOM_OFFICIAL_REFERENCE_SHA,
    PIPELINE_IDENTITY_SCHEMA,
)
from src.engine.scalping.main_lifecycle_paired import (
    HISTORICAL_FILL_BEFORE_SUBMIT_DIAGNOSTIC_RECOVERY_SCHEMA,
    HISTORICAL_LEGACY_EXIT_SUBMISSION_DIAGNOSTIC_RECOVERY_SCHEMA,
)
from src.engine.scalping.micro_reversion.contracts import CLEAN_BASELINE_DATE
from src.engine.scalping.micro_reversion import (
    counterfactual_entry_diagnostic as entry_diagnostic,
)
from src.engine.scalping.micro_reversion.ai_quality_bridge import (
    CONFIRMATION_WINDOW_METRIC_CONTRACT,
    _validate_confirmation_window_axis,
)
from src.engine.scalping.micro_reversion.provider_budget import (
    AUTHORITY_CONTRACT as PROVIDER_BUDGET_AUTHORITY_CONTRACT,
)
from src.engine.scalping.micro_reversion.provider_budget import BUDGET_SUMMARY_SCHEMA
from src.engine.scalping.micro_reversion.replay_ablation_contract import (
    CURRENT_DESIGN_ACTIVATION_DATE,
    CURRENT_DESIGN_VERSION,
    LEGACY_ARMS,
    LEGACY_DESIGN_VERSION,
    PROVIDER_ABLATION_FLOOR_SOURCE_CONTRACT_ACTIVATION_DATE,
    PROVIDER_ABLATION_FLOOR_LOOKBACK_CALENDAR_DAYS,
    PROVIDER_ABLATION_FLOOR_REQUIRED_COMMON_PARENTS,
    PROVIDER_ABLATION_FLOOR_REQUIRED_TRADING_DAYS,
    PROVIDER_ABLATION_FLOOR_REQUIRED_UNIQUE_SYMBOLS,
    PROVIDER_ABLATION_SAMPLE_FLOOR_SCHEMA,
    SOURCE_ONLY_AUTHORITY_CONTRACT,
    SOURCE_ONLY_FALSE_AUTHORITY_ALIASES,
    arm_set_for_design,
    comparison_roles_for_design,
    resolve_replay_ablation_design_version,
    validate_exact_one_design_per_parent,
)
from src.engine.scalping.micro_reversion.storage_maintenance import (
    STORAGE_CAPACITY_GROWTH_GATE_SCHEMA,
    evaluate_large_artifact_capacity_gate,
)
from src.utils.constants import DATA_DIR
from src.utils.jsonl_io import (
    existing_or_gzip_path,
    json_artifact_generation_lock,
    read_json_object_strict,
    write_json_object_generation_safe,
)
from src.utils.market_day import is_krx_trading_day

KST = ZoneInfo("Asia/Seoul")

CYCLE_SCHEMA = "main_ai_quality_postclose_r0_r3_cycle_v1"
PREPARED_SCHEMA = quality.MICRO_REVERSION_PREPARED_REQUEST_ARTIFACT_SCHEMA
ROLLING_SCHEMA = "main_ai_quality_rolling_paired_evaluation_v1"
R3_SCHEMA = "main_ai_quality_source_only_candidate_manifest_v1"
LIFECYCLE_REPORT_SCHEMA = "main_scalping_lifecycle_paired_daily_v2"
LIFECYCLE_WINDOW_EXCLUSION_MANIFEST_SCHEMA = (
    "main_scalping_lifecycle_window_exclusion_manifest_v1"
)
PIPELINE_OWNER_EXCLUSION_MANIFEST_SCHEMA = (
    "main_scalping_pipeline_owner_exclusion_manifest_v1"
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

PIPELINE_OWNER_EXCLUSION_AUTHORITY_CONTRACT: dict[str, Any] = {
    "metric_role": "source_quality_gate",
    "decision_authority": "pipeline_owner_window_exclusion_only",
    "window_policy": "exact_trade_date_record_id_and_stock_code",
    "sample_floor": "not_applicable_source_quality_manifest",
    "primary_decision_metric": "excluded_pipeline_owner_count",
    "source_quality_gate": "missing_explicit_lifecycle_identity_owner_quarantine",
    "exclusion_scope": "exact_pipeline_owner_window",
    "runtime_effect": False,
    "runtime_authority": False,
    "order_authority": False,
    "provider_authority": False,
    "allowed_runtime_apply": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
    "forbidden_uses": [
        "infer_or_reconstruct_main_lifecycle_id",
        "join_by_symbol_or_timestamp_proximity",
        "exclude_other_clean_pipeline_owner_windows",
        "direct_runtime_or_order_apply",
    ],
}

OFFLINE_AUTHORITY: dict[str, Any] = {
    "decision_authority": "postclose_source_only_ai_quality_research",
    **SOURCE_ONLY_AUTHORITY_CONTRACT,
}

SUPPORTED_ECONOMIC_STAGES = frozenset({"entry", "holding", "exit"})
# Compatibility alias for historical artifacts and tests.  Current artifacts
# resolve their arm census from their explicit ablation design version.
EXPECTED_ARMS = LEGACY_ARMS
MIN_TRADING_DAYS = 5
MIN_COMMON_PARENTS = 20
MIN_UNIQUE_SYMBOLS = 10
MIN_BBO_COVERAGE_PCT = 95.0
MIN_DEPTH_COVERAGE_PCT = 90.0
MIN_RELATIVE_UPLIFT_PCT = 1.0
MAX_LIFECYCLE_FINDINGS = 200
PIPELINE_OWNER_SCOPED_GAP_HARD_BLOCK_MIN_ROWS = 1_000
LIFECYCLE_POPULATION_REAL_SUBMITTED = "real_submitted"
LIFECYCLE_POPULATION_CANDIDATE_OBSERVATION = "candidate_observation"
LIFECYCLE_POPULATION_SCOPES = frozenset(
    {
        LIFECYCLE_POPULATION_REAL_SUBMITTED,
        LIFECYCLE_POPULATION_CANDIDATE_OBSERVATION,
    }
)
PIPELINE_SOURCE_POPULATION_SCOPES = frozenset(
    {"real_record_bound", "sim_observation_only"}
)
LEGACY_UNATTESTED_RECEIVE_CLOCK_DIAGNOSTIC_LAST_DATE = "2026-08-25"

LIFECYCLE_PROMOTION_ESTIMATOR_ID = (
    "earliest_decision_divergence_per_lifecycle_censor_no_divergence_v2"
)
LIFECYCLE_PROMOTION_ESTIMATOR_CONTRACT: dict[str, Any] = {
    "metric_role": "lifecycle_clustered_promotion_economics",
    "decision_authority": "postclose_source_only_promotion_estimator",
    "window_policy": "exact_trade_date_and_main_lifecycle_id_across_all_stages",
    "sample_floor": (
        "at_most_one_deterministic_divergence_representative_per_unique_lifecycle"
    ),
    "primary_decision_metric": "candidate_total_notional_net_profit_krw",
    "source_quality_gate": (
        "exact_lifecycle_identity_stage_and_aware_decision_timestamp"
    ),
    "estimator_id": LIFECYCLE_PROMOTION_ESTIMATOR_ID,
    "selection_input_fields": [
        "target_date",
        "main_lifecycle_id",
        "decision_ts",
        "control_action",
        "candidate_action",
        "control_signal_selected",
        "candidate_signal_selected",
        "decision_trace_id",
        "paired_replay_parent_id",
    ],
    "runtime_effect": False,
    "runtime_authority": False,
    "order_authority": False,
    "provider_authority": False,
    "allowed_runtime_apply": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
    "forbidden_uses": [
        "select_representative_from_future_outcome_or_ev",
        "sum_multiple_decision_parents_for_one_lifecycle_stage",
        "sum_holding_scale_in_or_exit_stages_for_one_lifecycle",
        "count_no_divergence_lifecycle_as_promotion_economics",
        "replace_decision_level_ev_diagnostics",
        "direct_runtime_order_provider_or_threshold_apply",
    ],
}

REPORT_ROOT = DATA_DIR / "report" / "main_ai_quality_r0_r3"
ECONOMIC_REPORT_ROOT = DATA_DIR / "report" / "micro_reversion_economic_reference"
LIFECYCLE_REPORT_ROOT = DATA_DIR / "report" / "main_scalping_lifecycle_paired"
BRIDGE_REPORT_ROOT = DATA_DIR / "report" / "micro_reversion_ai_quality_bridge"
MICRO_REPORT_ROOT = (
    DATA_DIR / "report" / "ai_micro_reversion_materialized_replay_requests"
)
SOURCE_POLICY_ROOT = DATA_DIR / "policy" / "micro_reversion"
ECONOMIC_POLICY_PATH = DATA_DIR / "config" / "micro_reversion_economic_policy.json"
OBSERVER_CANARY_LATEST_PATH = (
    DATA_DIR / "runtime" / "scalp_micro_reversion_forward_collector" / "latest.json"
)
OBSERVER_CANARY_DAILY_ROOT = (
    DATA_DIR / "source_quality" / "scalp_micro_reversion_canary_daily"
)
DEFAULT_DAILY_ATTEMPT_CAP = 390
DEFAULT_PARENT_CAP = 130
DEFAULT_DAILY_USD_CAP = Decimal("1.0")
PROVIDER_AUTHORITY_BINDING_SCHEMA = "micro_reversion_provider_authority_binding_v1"


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


def _declared_design_and_arms(
    declared_design_version: Any | None,
    observed_arms: Iterable[Any],
) -> tuple[str, tuple[str, str, str]]:
    """Resolve one legacy/current census without guessing current metadata."""

    version = resolve_replay_ablation_design_version(
        declared_design_version=(
            None
            if declared_design_version in (None, "")
            else str(declared_design_version)
        ),
        arms=observed_arms,
    )
    return version, arm_set_for_design(version)


def _request_design_and_arms(
    rows: Sequence[Mapping[str, Any]],
    *,
    declared_design_version: Any | None,
) -> tuple[str, tuple[str, str, str]]:
    bindings = validate_exact_one_design_per_parent(rows)
    versions = {binding.design_version for binding in bindings}
    if len(versions) != 1:
        raise ValueError("micro_reversion_artifact_mixed_ablation_designs")
    version = next(iter(versions))
    if declared_design_version in (None, ""):
        if version != LEGACY_DESIGN_VERSION:
            raise ValueError("micro_reversion_current_ablation_design_missing")
    elif str(declared_design_version) != version:
        raise ValueError("micro_reversion_ablation_design_mismatch")
    return version, arm_set_for_design(version)


def _content_hash(value: Mapping[str, Any], hash_field: str) -> str:
    return _sha256({key: item for key, item in value.items() if key != hash_field})


def _validate_materialized_step_artifact(
    report: Mapping[str, Any],
    *,
    target_date: str,
    source_bundle_report: Mapping[str, Any] | None = None,
    prepared_artifact: Mapping[str, Any] | None = None,
    source_bridge_report: Mapping[str, Any] | None = None,
    paired_report: Mapping[str, Any] | None = None,
) -> int:
    """Validate materialization shape and required current-source lineage.

    A current-design empty receipt is terminal only after the canonical
    materializer is rebuilt from all four persisted companions.  Shape-only
    validation must never turn a detached empty JSON object into authority.
    """

    if (
        not isinstance(report, Mapping)
        or report.get("schema") != quality.MICRO_REVERSION_MATERIALIZED_REQUEST_SCHEMA
    ):
        raise ValueError("materialized_step_schema_invalid")
    if report.get("target_date") != target_date:
        raise ValueError("materialized_step_target_date_mismatch")
    if (
        target_date >= CURRENT_DESIGN_ACTIVATION_DATE
        and report.get("ablation_design_version") != CURRENT_DESIGN_VERSION
    ):
        raise ValueError("materialized_step_current_design_required")
    if str(report.get("report_content_sha256") or "") != _content_hash(
        report, "report_content_sha256"
    ):
        raise ValueError("materialized_step_content_hash_mismatch")
    for field, expected in (
        ("provider_call_performed", False),
        ("runtime_effect", False),
        ("allowed_runtime_apply", False),
        ("actual_order_submitted", False),
        ("broker_order_forbidden", True),
    ):
        if report.get(field) is not expected:
            raise ValueError(f"materialized_step_authority_invalid:{field}")
    if report.get("ablation_design_version") == CURRENT_DESIGN_VERSION and (
        _current_ablation_execution_authority_findings(report)
    ):
        raise ValueError("materialized_step_current_authority_invalid")
    requests = report.get("requests")
    materializations = report.get("materializations")
    if not isinstance(requests, list) or not isinstance(materializations, list):
        raise ValueError("materialized_step_rows_invalid")
    if report.get("request_count") != len(requests) or report.get(
        "materialization_count"
    ) != len(materializations):
        raise ValueError("materialized_step_census_mismatch")
    if not requests:
        if (
            report.get("status") != "no_micro_reversion_eligible_requests"
            or materializations
            or report.get("request_ids") != []
        ):
            raise ValueError("materialized_step_empty_contract_invalid")
    else:
        quality._validate_micro_reversion_materialized_report(dict(report))
    if target_date >= CURRENT_DESIGN_ACTIVATION_DATE:
        if not all(
            isinstance(companion, Mapping)
            for companion in (
                source_bundle_report,
                prepared_artifact,
                source_bridge_report,
                paired_report,
            )
        ):
            raise ValueError("materialized_step_current_lineage_companions_missing")
        _validate_current_materialized_source_lineage(
            materialized_report=report,
            source_bundle_report=source_bundle_report,
            prepared_artifact=prepared_artifact,
            source_bridge_report=source_bridge_report,
            paired_report=paired_report,
        )
    return len(requests)


def _atomic_write_json(path: Path, value: Mapping[str, Any]) -> None:
    write_json_object_generation_safe(
        path,
        value,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        trailing_newline=True,
    )


def _load_json_auto(path: Path) -> dict[str, Any]:
    """Read one stable logical JSON artifact and reject conflicting dual copies."""
    return read_json_object_strict(path)


def _artifact_path_present(path: Path) -> bool:
    """Census a directory entry without following a possibly broken symlink."""

    return path.exists() or path.is_symlink()


def _load_json_with_raw_artifact(
    path: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Read one logical JSON generation and its physical provenance together."""

    with json_artifact_generation_lock(path, exclusive=False, blocking=True) as logical:
        validated_payload = read_json_object_strict(logical)
        resolved = existing_or_gzip_path(logical)
        expected_stat = resolved.lstat()
        expected_identity = (
            expected_stat.st_dev,
            expected_stat.st_ino,
            expected_stat.st_size,
            expected_stat.st_mtime_ns,
        )
        if not stat.S_ISREG(expected_stat.st_mode):
            raise ValueError(f"json_artifact_path_type_invalid:{resolved}")
        descriptor = os.open(
            resolved,
            os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0),
        )
        try:
            before = os.fstat(descriptor)
            before_identity = (
                before.st_dev,
                before.st_ino,
                before.st_size,
                before.st_mtime_ns,
            )
            if before_identity != expected_identity or not stat.S_ISREG(before.st_mode):
                raise ValueError(f"json_artifact_changed_during_read:{resolved}")
            chunks: list[bytes] = []
            while True:
                chunk = os.read(descriptor, 1024 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
            after = os.fstat(descriptor)
            after_identity = (
                after.st_dev,
                after.st_ino,
                after.st_size,
                after.st_mtime_ns,
            )
        finally:
            os.close(descriptor)
        raw = b"".join(chunks)
        if (
            before_identity != after_identity
            or len(raw) != before.st_size
            or existing_or_gzip_path(logical) != resolved
        ):
            raise ValueError(f"json_artifact_changed_during_read:{resolved}")
        decoded = gzip.decompress(raw) if resolved.suffix == ".gz" else raw
        try:
            raw_payload = json.loads(decoded.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"json_artifact_payload_invalid:{resolved}") from exc
        if (
            not isinstance(raw_payload, dict)
            or raw_payload != validated_payload
            or read_json_object_strict(logical) != validated_payload
        ):
            raise ValueError(f"json_artifact_generation_mismatch:{resolved}")
        final_stat = resolved.lstat()
        final_identity = (
            final_stat.st_dev,
            final_stat.st_ino,
            final_stat.st_size,
            final_stat.st_mtime_ns,
        )
        if final_identity != expected_identity:
            raise ValueError(f"json_artifact_changed_during_read:{resolved}")
    provenance = {
        "logical_path": str(logical),
        "resolved_path": str(resolved),
        "compression": "gzip" if resolved.suffix == ".gz" else "plain",
        "stored_sha256": hashlib.sha256(raw).hexdigest(),
        "stored_size_bytes": len(raw),
        "mtime_ns": final_stat.st_mtime_ns,
        "logical_content_sha256": _sha256(validated_payload),
    }
    return validated_payload, provenance


def _capacity_gate_fail_closed(
    *, target: date, target_date: str, selected_paths: Mapping[str, Path]
) -> dict[str, Any]:
    """Evaluate one storage-growth checkpoint without weakening on errors."""

    try:
        return evaluate_large_artifact_capacity_gate(
            target_date=target,
            capacity_status_path=selected_paths["capacity_status"],
            storage_path=selected_paths["prepared"].parent,
        )
    except (OSError, TypeError, ValueError) as exc:
        return {
            "schema": STORAGE_CAPACITY_GROWTH_GATE_SCHEMA,
            "target_date": target_date,
            "status": "blocked_capacity_gate_evaluation_failed",
            "large_artifact_growth_allowed": False,
            "effective_capacity_state": "unknown",
            "artifact_status": "unknown",
            "capacity_status_artifact_path": str(
                selected_paths["capacity_status"].absolute()
            ),
            "direct_snapshot_provenance": "unavailable",
            "direct_capacity_state": "unknown",
            "direct_disk_snapshot": None,
            "direct_disk_snapshot_error": f"{type(exc).__name__}:{exc}",
            "reason_codes": ["capacity_gate_evaluation_failed"],
            "decision_authority": "storage_capacity_growth_gate_only",
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "provider_route_change_allowed": False,
            "network_call_performed_by_module": False,
            "forbidden_uses": [
                "broker_order_submission_or_cancel",
                "provider_route_or_model_change",
                "strategy_threshold_quantity_cap_or_bot_change",
                "automatic_purge_or_deletion_authority",
            ],
        }


def _pre_provider_capacity_recheck(
    *, target: date, target_date: str, selected_paths: Mapping[str, Path]
) -> tuple[dict[str, Any], str | None]:
    """Recheck storage immediately before the only expensive Provider step."""

    gate = _capacity_gate_fail_closed(
        target=target,
        target_date=target_date,
        selected_paths=selected_paths,
    )
    if gate.get("large_artifact_growth_allowed") is True:
        return gate, None
    return (
        gate,
        "large_artifact_growth_blocked_pre_provider:"
        f"{str(gate.get('status') or 'unknown')}",
    )


def _provider_ablation_sample_floor_from_reports(
    *,
    target_date: str,
    materialized_reports: Sequence[
        tuple[str, Path, Mapping[str, Any], Mapping[str, Any]]
    ],
) -> dict[str, Any]:
    """Build the hash-bound current-design floor required before Provider replay."""

    target = date.fromisoformat(target_date)
    activation = date.fromisoformat(CURRENT_DESIGN_ACTIVATION_DATE)
    source_contract_activation = date.fromisoformat(
        PROVIDER_ABLATION_FLOOR_SOURCE_CONTRACT_ACTIVATION_DATE
    )
    if target < activation:
        body = {
            "schema": PROVIDER_ABLATION_SAMPLE_FLOOR_SCHEMA,
            "target_date": target_date,
            "current_design_activation_date": CURRENT_DESIGN_ACTIVATION_DATE,
            "eligible_source_contract_activation_date": (
                PROVIDER_ABLATION_FLOOR_SOURCE_CONTRACT_ACTIVATION_DATE
            ),
            "lookback_calendar_days": PROVIDER_ABLATION_FLOOR_LOOKBACK_CALENDAR_DAYS,
            "ablation_design_version": LEGACY_DESIGN_VERSION,
            "required_trading_days": 0,
            "required_common_parent_count": 0,
            "required_unique_symbol_count": 0,
            "observed_trading_days": 0,
            "observed_common_parent_count": 0,
            "observed_unique_symbol_count": 0,
            "observed_dates": [],
            "parent_census_sha256": _sha256([]),
            "symbol_census_sha256": _sha256([]),
            "included_artifacts": [],
            "excluded_pre_source_contract_artifact_dates": [],
            "contract_findings": [],
            "pass": True,
            "status": "not_applicable_before_current_design",
            "provider_call_performed": False,
            **OFFLINE_AUTHORITY,
        }
        return {**body, "floor_content_sha256": _sha256(body)}
    parents: dict[str, tuple[str, str]] = {}
    included_artifacts: list[dict[str, Any]] = []
    excluded_pre_source_contract_artifact_dates: list[str] = []
    findings: list[str] = []
    expected_arms = set(arm_set_for_design(CURRENT_DESIGN_VERSION))
    for expected_date, logical_path, raw_report, companions in sorted(
        materialized_reports, key=lambda item: (item[0], str(item[1]))
    ):
        try:
            report_date = date.fromisoformat(expected_date)
        except ValueError:
            findings.append(f"materialized_expected_date_invalid:{expected_date}")
            continue
        if report_date < activation or report_date > target:
            findings.append(f"materialized_date_outside_current_design:{expected_date}")
            continue
        if report_date < source_contract_activation:
            excluded_pre_source_contract_artifact_dates.append(expected_date)
            continue
        try:
            report = dict(raw_report)
            required_companions = {
                "source_bundle",
                "prepared",
                "bridge",
                "paired",
                "paths",
            }
            if set(companions) != required_companions or not all(
                isinstance(companions.get(field), Mapping)
                for field in (
                    "source_bundle",
                    "prepared",
                    "bridge",
                    "paired",
                    "paths",
                )
            ):
                raise ValueError("provider_floor_lineage_companions_missing")
            request_count = _validate_materialized_step_artifact(
                report,
                target_date=expected_date,
                source_bundle_report=companions["source_bundle"],
                prepared_artifact=companions["prepared"],
                source_bridge_report=companions["bridge"],
                paired_report=companions["paired"],
            )
            requests = list(report.get("requests") or [])
            if request_count and not is_krx_trading_day(report_date):
                raise ValueError("provider_floor_nontrading_sample_invalid")
        except (TypeError, ValueError) as exc:
            findings.append(
                f"materialized_contract_invalid:{expected_date}:{type(exc).__name__}:{exc}"
            )
            continue
        if request_count == 0:
            included_artifacts.append(
                {
                    "target_date": expected_date,
                    "logical_path": str(logical_path.absolute()),
                    "report_content_sha256": report.get("report_content_sha256"),
                    "artifact_sha256": _sha256(report),
                    "parent_count": 0,
                    "unique_symbol_count": 0,
                    "parent_census_sha256": _sha256([]),
                    "materialized_request_census_sha256": (
                        quality._micro_reversion_materialized_request_census_sha256(
                            report
                        )
                    ),
                    "companion_paths": {
                        field: str(Path(path).absolute())
                        for field, path in companions["paths"].items()
                    },
                    "companion_artifact_sha256s": {
                        field: _sha256(companions[field])
                        for field in ("source_bundle", "prepared", "bridge", "paired")
                    },
                    "lineage_status": (
                        "full_current_empty_source_lineage_validated_not_counted"
                    ),
                }
            )
            continue
        if (
            report.get("target_date") != expected_date
            or report.get("ablation_design_version") != CURRENT_DESIGN_VERSION
        ):
            findings.append(f"materialized_identity_invalid:{expected_date}")
            continue
        by_parent: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
        for request in requests:
            by_parent[str(request.get("paired_replay_parent_id") or "")].append(request)
        artifact_parent_ids: list[str] = []
        artifact_symbols: set[str] = set()
        artifact_parents: dict[str, tuple[str, str]] = {}
        artifact_invalid = False
        for parent_id, parent_rows in sorted(by_parent.items()):
            symbols = {str(row.get("stock_code") or "").strip() for row in parent_rows}
            arms = {
                str(row.get("micro_reversion_replay_arm") or "") for row in parent_rows
            }
            if (
                not parent_id
                or len(parent_rows) != len(expected_arms)
                or arms != expected_arms
                or len(symbols) != 1
                or not next(iter(symbols), "")
            ):
                findings.append(
                    f"materialized_parent_census_invalid:{expected_date}:{parent_id or 'missing'}"
                )
                artifact_invalid = True
                continue
            symbol = next(iter(symbols))
            if parent_id in parents or parent_id in artifact_parents:
                findings.append(f"materialized_parent_duplicate:{parent_id}")
                artifact_invalid = True
                continue
            artifact_parents[parent_id] = (expected_date, symbol)
            artifact_parent_ids.append(parent_id)
            artifact_symbols.add(symbol)
        if artifact_invalid:
            continue
        parents.update(artifact_parents)
        included_artifacts.append(
            {
                "target_date": expected_date,
                "logical_path": str(logical_path.absolute()),
                "report_content_sha256": report.get("report_content_sha256"),
                "artifact_sha256": _sha256(report),
                "parent_count": len(artifact_parent_ids),
                "unique_symbol_count": len(artifact_symbols),
                "parent_census_sha256": _sha256(artifact_parent_ids),
                "materialized_request_census_sha256": (
                    quality._micro_reversion_materialized_request_census_sha256(report)
                ),
                "companion_paths": {
                    field: str(Path(path).absolute())
                    for field, path in companions["paths"].items()
                },
                "companion_artifact_sha256s": {
                    field: _sha256(companions[field])
                    for field in ("source_bundle", "prepared", "bridge", "paired")
                },
                "lineage_status": "full_current_source_lineage_validated",
            }
        )

    trading_dates = sorted({value[0] for value in parents.values()})
    symbols = sorted({value[1] for value in parents.values()})
    parent_ids = sorted(parents)
    passed = bool(
        not findings
        and len(trading_dates) >= PROVIDER_ABLATION_FLOOR_REQUIRED_TRADING_DAYS
        and len(parent_ids) >= PROVIDER_ABLATION_FLOOR_REQUIRED_COMMON_PARENTS
        and len(symbols) >= PROVIDER_ABLATION_FLOOR_REQUIRED_UNIQUE_SYMBOLS
    )
    body = {
        "schema": PROVIDER_ABLATION_SAMPLE_FLOOR_SCHEMA,
        "target_date": target_date,
        "current_design_activation_date": CURRENT_DESIGN_ACTIVATION_DATE,
        "eligible_source_contract_activation_date": (
            PROVIDER_ABLATION_FLOOR_SOURCE_CONTRACT_ACTIVATION_DATE
        ),
        "lookback_calendar_days": PROVIDER_ABLATION_FLOOR_LOOKBACK_CALENDAR_DAYS,
        "ablation_design_version": CURRENT_DESIGN_VERSION,
        "required_trading_days": PROVIDER_ABLATION_FLOOR_REQUIRED_TRADING_DAYS,
        "required_common_parent_count": PROVIDER_ABLATION_FLOOR_REQUIRED_COMMON_PARENTS,
        "required_unique_symbol_count": PROVIDER_ABLATION_FLOOR_REQUIRED_UNIQUE_SYMBOLS,
        "observed_trading_days": len(trading_dates),
        "observed_common_parent_count": len(parent_ids),
        "observed_unique_symbol_count": len(symbols),
        "observed_dates": trading_dates,
        "parent_census_sha256": _sha256(parent_ids),
        "symbol_census_sha256": _sha256(symbols),
        "included_artifacts": included_artifacts,
        "excluded_pre_source_contract_artifact_dates": sorted(
            set(excluded_pre_source_contract_artifact_dates)
        ),
        "contract_findings": sorted(set(findings)),
        "pass": passed,
        "status": (
            "pass_provider_ablation_floor_met"
            if passed
            else (
                "blocked_invalid_materialized_history"
                if findings
                else "keep_collecting_provider_ablation_floor"
            )
        ),
        "provider_call_performed": False,
        **OFFLINE_AUTHORITY,
    }
    return {**body, "floor_content_sha256": _sha256(body)}


def _collect_provider_ablation_sample_floor(
    *,
    target_date: str,
    current_materialized: Mapping[str, Any],
    current_companions: Mapping[str, Any],
    selected_paths: Mapping[str, Path],
) -> dict[str, Any]:
    """Load each current-design daily materialization through strict custody."""

    target = date.fromisoformat(target_date)
    activation = date.fromisoformat(CURRENT_DESIGN_ACTIVATION_DATE)
    reports: list[tuple[str, Path, Mapping[str, Any], Mapping[str, Any]]] = []
    window_start = max(
        activation,
        target - timedelta(days=PROVIDER_ABLATION_FLOOR_LOOKBACK_CALENDAR_DAYS - 1),
    )
    for offset in range((target - window_start).days + 1):
        current = window_start + timedelta(days=offset)
        date_key = current.isoformat()
        daily_paths = _default_paths(date_key)
        logical = daily_paths["materialized"]
        if date_key == target_date:
            reports.append(
                (
                    date_key,
                    selected_paths["materialized"],
                    current_materialized,
                    current_companions,
                )
            )
            continue
        resolved = existing_or_gzip_path(logical)
        if not _artifact_path_present(resolved):
            continue
        try:
            historical_report = _load_json_auto(logical)
            companion_paths = {
                "source_bundle": daily_paths["source_bundle"],
                "prepared": daily_paths["prepared"],
                "bridge": daily_paths["bridge_report"],
                "paired": daily_paths["paired_report"],
            }
            reports.append(
                (
                    date_key,
                    logical,
                    historical_report,
                    {
                        **{
                            field: _load_json_auto(path)
                            for field, path in companion_paths.items()
                        },
                        "paths": {
                            field: str(path) for field, path in companion_paths.items()
                        },
                    },
                )
            )
        except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
            reports.append(
                (
                    date_key,
                    logical,
                    {
                        "schema": "invalid_materialized_generation",
                        "load_error": f"{type(exc).__name__}:{exc}",
                    },
                    {},
                )
            )
    return _provider_ablation_sample_floor_from_reports(
        target_date=target_date,
        materialized_reports=reports,
    )


def _raw_artifact(
    path: Path, *, expected_payload: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    """Return exact raw provenance, optionally bound to an earlier payload.

    ``run_cycle`` consumes :func:`_load_json_with_raw_artifact` directly so its
    semantic validation and raw-byte provenance always describe one locked
    generation.  The optional expectation keeps this compatibility helper
    fail-closed for callers that already hold a parsed object.
    """

    payload, provenance = _load_json_with_raw_artifact(path)
    if expected_payload is not None and payload != dict(expected_payload):
        raise ValueError(f"json_artifact_generation_mismatch:{path}")
    return provenance


def cycle_report_path(target_date: str) -> Path:
    return REPORT_ROOT / f"main_ai_quality_r0_r3_cycle_{target_date}.json"


def prepared_request_path(target_date: str) -> Path:
    return quality.micro_reversion_prepared_request_path(target_date)


def control_driver_path(target_date: str) -> Path:
    return REPORT_ROOT / f"main_ai_quality_micro_control_driver_{target_date}.json"


def rolling_report_path(target_date: str) -> Path:
    return REPORT_ROOT / f"main_ai_quality_rolling_paired_{target_date}.json"


def r3_manifest_path(target_date: str) -> Path:
    return REPORT_ROOT / f"main_ai_quality_r3_source_candidates_{target_date}.json"


def action_neutral_label_path(target_date: str) -> Path:
    return quality.micro_reversion_action_neutral_label_path(target_date)


def provider_ablation_floor_path(target_date: str) -> Path:
    return quality.micro_reversion_provider_ablation_floor_path(target_date)


def counterfactual_entry_diagnostic_path(target_date: str) -> Path:
    return REPORT_ROOT / f"main_ai_quality_counterfactual_entry_{target_date}.json"


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


def _current_ablation_execution_authority_findings(
    value: Mapping[str, Any],
) -> list[str]:
    findings: list[str] = []
    for field, expected in SOURCE_ONLY_AUTHORITY_CONTRACT.items():
        if value.get(field) is not expected:
            findings.append(f"current_source_only_authority_invalid:{field}")
    if value.get("selection_authority") is not False:
        findings.append("current_selection_authority_invalid")
    if value.get("decision_authority") != "offline_replay_and_attribution_only":
        findings.append("current_decision_authority_invalid")
    for field in SOURCE_ONLY_FALSE_AUTHORITY_ALIASES:
        if field == "selection_authority":
            continue
        if field in value and value.get(field) is not False:
            findings.append(f"current_authority_alias_invalid:{field}")
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
    if target_date >= CURRENT_DESIGN_ACTIVATION_DATE and source.get(
        "logical_content_sha256"
    ) != _sha256(paired_report):
        raise ValueError("paired_report_raw_provenance_content_mismatch")
    rows = paired_report.get("requests")
    if not isinstance(rows, list):
        raise ValueError("paired_report_requests_missing")
    prepared, exclusions = (
        quality.micro_reversion_prepared_request_census_from_paired_report(
            paired_report=paired_report,
            target_date=target_date,
        )
    )

    body = {
        "schema": PREPARED_SCHEMA,
        "target_date": target_date,
        "generated_at": datetime.now(KST).isoformat(),
        "status": (
            "prepared_requests_ready" if prepared else "no_supported_prepared_requests"
        ),
        "source_paired_report": dict(source),
        "source_paired_report_content_sha256": _sha256(paired_report),
        "source_request_count": len(prepared) + len(exclusions),
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
    quality.validate_micro_reversion_prepared_artifact(value)


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

    declared_design_version = report.get("ablation_design_version")
    design_declared = declared_design_version is not None
    design_version = (
        str(declared_design_version) if design_declared else LEGACY_DESIGN_VERSION
    )
    try:
        strict_current_metrics = bool(
            design_version == CURRENT_DESIGN_VERSION
            and date.fromisoformat(str(report.get("target_date") or ""))
            >= date.fromisoformat(CURRENT_DESIGN_ACTIVATION_DATE)
        )
    except ValueError:
        # The outer execution-report validator owns the target-date error.  Do
        # not accidentally impose a post-activation schema on a malformed or
        # historical compatibility artifact before that owner reports it.
        strict_current_metrics = False
    try:
        expected_arms = arm_set_for_design(design_version)
    except ValueError:
        _execution_census_error("ablation_design_invalid")
    if report.get("ablation_design_version") is None:
        if design_version != LEGACY_DESIGN_VERSION or report.get(
            "ablation_arms"
        ) not in (None, list(expected_arms)):
            _execution_census_error("ablation_design_missing")
    elif report.get("ablation_arms") != list(expected_arms):
        _execution_census_error("ablation_arm_declaration_mismatch")
    request_count = _native_nonnegative_int(report.get("request_count"))
    parent_count = _native_nonnegative_int(report.get("parent_count"))
    result_count = len(results)
    committed_parent_count = _native_nonnegative_int(
        report.get("committed_parent_count")
    )
    if (
        request_count is None
        or request_count <= 0
        or request_count % len(expected_arms) != 0
        or parent_count != request_count // len(expected_arms)
        or committed_parent_count is None
        or committed_parent_count <= 0
        or result_count != committed_parent_count * len(expected_arms)
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
    request_source_event_stages_by_parent: dict[str, set[str | None]] = defaultdict(set)
    request_exact_hashes_by_parent: dict[str, list[str | None]] = defaultdict(list)
    for raw_ref in request_refs_raw:
        if not isinstance(raw_ref, Mapping):
            _execution_census_error("request_ref_not_object")
        parent_id = str(raw_ref.get("paired_replay_parent_id") or "").strip()
        request_id = str(raw_ref.get("paired_replay_id") or "").strip()
        arm = str(raw_ref.get("micro_reversion_replay_arm") or "").strip()
        trace_id = str(raw_ref.get("decision_trace_id") or "").strip()
        source_event_stage = raw_ref.get("source_event_stage")
        source_exact_hash = raw_ref.get("source_exact_payload_sha256")
        if (
            not parent_id
            or not request_id
            or request_id in request_by_id
            or arm not in expected_arms
            or (
                design_declared
                and raw_ref.get("ablation_design_version") != design_version
            )
            or (
                not design_declared
                and raw_ref.get("ablation_design_version")
                not in (None, LEGACY_DESIGN_VERSION)
            )
            or not trace_id
            or (
                source_event_stage is not None
                and (
                    not isinstance(source_event_stage, str)
                    or not source_event_stage
                    or source_event_stage != source_event_stage.strip()
                )
            )
            or (
                source_event_stage in _SCALE_IN_SOURCE_EVENT_STAGES
                and raw_ref.get("decision_stage") != "holding"
            )
            or (
                isinstance(source_event_stage, str)
                and source_event_stage.lower() in _SCALE_IN_SOURCE_EVENT_STAGES
                and source_event_stage not in _SCALE_IN_SOURCE_EVENT_STAGES
            )
            or (
                (design_declared or source_exact_hash is not None)
                and not _valid_sha256(source_exact_hash)
            )
            or (
                design_version == CURRENT_DESIGN_VERSION
                and (
                    not _valid_sha256(
                        raw_ref.get("tactical_micro_reversion_evidence_sha256")
                    )
                    or not str(raw_ref.get("outcome_join_key") or "").strip()
                )
            )
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
        request_source_event_stages_by_parent[parent_id].add(source_event_stage)
        request_exact_hashes_by_parent[parent_id].append(
            str(source_exact_hash) if source_exact_hash is not None else None
        )
    if len(request_ids_by_parent) != parent_count or any(
        len(request_ids_by_parent[parent_id]) != len(expected_arms)
        or request_arms_by_parent[parent_id] != set(expected_arms)
        or len(request_trace_by_parent[parent_id]) != 1
        or len(request_source_event_stages_by_parent[parent_id]) != 1
        for parent_id in request_ids_by_parent
    ):
        _execution_census_error("request_parent_arm_census_mismatch")
    for parent_id, exact_hashes in request_exact_hashes_by_parent.items():
        present_hashes = [value for value in exact_hashes if value is not None]
        if (
            (design_declared and len(present_hashes) != len(expected_arms))
            or (
                not design_declared
                and present_hashes
                and len(present_hashes) != len(expected_arms)
            )
            or (present_hashes and len(set(present_hashes)) != 1)
        ):
            _execution_census_error(
                f"request_parent_source_exact_hash_mismatch:{parent_id}"
            )
    if design_version == CURRENT_DESIGN_VERSION:
        for parent_id, request_ids in request_ids_by_parent.items():
            refs_by_arm = {
                str(request_by_id[request_id].get("micro_reversion_replay_arm")): (
                    request_by_id[request_id]
                )
                for request_id in request_ids
            }
            base_ref = refs_by_arm[expected_arms[0]]
            ask_control_ref = refs_by_arm[expected_arms[1]]
            ask_candidate_ref = refs_by_arm[expected_arms[2]]
            if (
                base_ref.get("ask_depletion_context_sha256") is not None
                or base_ref.get("ask_depletion_contract_sha256") is not None
                or not _valid_sha256(
                    ask_control_ref.get("ask_depletion_contract_sha256")
                )
                or not _valid_sha256(
                    ask_control_ref.get("ask_depletion_context_sha256")
                )
                or ask_control_ref.get("ask_depletion_contract_sha256")
                != ask_candidate_ref.get("ask_depletion_contract_sha256")
                or ask_control_ref.get("ask_depletion_context_sha256")
                != ask_candidate_ref.get("ask_depletion_context_sha256")
            ):
                _execution_census_error(
                    f"ask_depletion_parent_binding_invalid:{parent_id}"
                )

    result_ids: list[str] = []
    result_request_ids: list[str] = []
    result_by_parent: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    result_arms_by_parent: dict[str, set[str]] = defaultdict(set)
    result_exact_hashes_by_parent: dict[str, set[str]] = defaultdict(set)
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
            or result.get("ablation_design_version")
            != request_ref.get("ablation_design_version")
            or result.get("decision_trace_id") != request_ref.get("decision_trace_id")
            or (
                request_ref.get("decision_stage") is not None
                and quality._stage(result.get("stage"))
                != request_ref.get("decision_stage")
            )
            or result.get("source_event_stage") != request_ref.get("source_event_stage")
            or result.get("candidate_input_sha256")
            != request_ref.get("candidate_input_sha256")
            or result.get("tactical_micro_reversion_evidence_sha256")
            != request_ref.get("tactical_micro_reversion_evidence_sha256")
            or (
                design_version == CURRENT_DESIGN_VERSION
                and result.get("outcome_join_key")
                != request_ref.get("outcome_join_key")
            )
            or result.get("prompt_sha256") != request_ref.get("prompt_sha256")
            or result.get("prompt_contract_sha256")
            != request_ref.get("prompt_contract_sha256")
            or result.get("ask_depletion_contract_sha256")
            != request_ref.get("ask_depletion_contract_sha256")
            or result.get("ask_depletion_context_sha256")
            != request_ref.get("ask_depletion_context_sha256")
            or not _valid_sha256(result.get("source_exact_payload_sha256"))
            or not _valid_sha256(result.get("outcome_label_content_sha256"))
            or not str(result.get("outcome_join_key") or "").strip()
            or not isinstance(replay_result, Mapping)
            or replay_result.get("status") != "pass"
            or not isinstance(candidate_response, Mapping)
            or result.get("candidate_response_content_sha256")
            != _sha256(candidate_response)
            or _authority_findings(result)
            or (
                design_version == CURRENT_DESIGN_VERSION
                and _current_ablation_execution_authority_findings(result)
            )
        ):
            _execution_census_error("result_identity_content_or_hash_invalid")
        request_exact_hash = request_ref.get("source_exact_payload_sha256")
        if (
            request_exact_hash is not None
            and result.get("source_exact_payload_sha256") != request_exact_hash
        ):
            _execution_census_error("result_source_exact_hash_binding_mismatch")
        rebound_label_hash = result.get("outcome_label_rebound_from_sha256")
        if rebound_label_hash is not None and (
            not _valid_sha256(rebound_label_hash)
            or rebound_label_hash == result.get("outcome_label_content_sha256")
        ):
            _execution_census_error("result_outcome_label_rebind_invalid")
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
        result_exact_hashes_by_parent[parent_id].add(
            str(result.get("source_exact_payload_sha256"))
        )
    if len(result_by_parent) != committed_parent_count or any(
        len(parent_results) != len(expected_arms)
        or result_arms_by_parent[parent_id] != set(expected_arms)
        for parent_id, parent_results in result_by_parent.items()
    ):
        _execution_census_error("result_parent_arm_census_mismatch")
    for parent_id, exact_hashes in result_exact_hashes_by_parent.items():
        request_exact_hashes = {
            value
            for value in request_exact_hashes_by_parent[parent_id]
            if value is not None
        }
        if len(exact_hashes) != 1 or (
            request_exact_hashes and exact_hashes != request_exact_hashes
        ):
            _execution_census_error(
                f"result_parent_source_exact_hash_mismatch:{parent_id}"
            )
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
    provisional_failed_result_count = _native_nonnegative_int(
        report.get("provisional_failed_result_count", 0)
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
        or provisional_failed_result_count is None
        or max_new_requests is None
        or max_new_requests <= 0
        or new_result_count > max_new_requests
        or report.get("candidate_model_call_attempted")
        is not bool(new_results or provisional_failed_result_count)
    ):
        _execution_census_error("checkpoint_selected_or_reused_census_mismatch")

    exclusions = report.get("execution_exclusions")
    if not isinstance(exclusions, list):
        _execution_census_error("execution_exclusions_invalid")
    seen_excluded_request_ids: set[str] = set()
    candidate_execution_exclusion_count = 0
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
        exclusion_reason = str(exclusion.get("reason") or "")
        if exclusion_reason.startswith("candidate_execution_"):
            if exclusion_reason not in {
                "candidate_execution_provider_failed",
                "candidate_execution_provider_provenance_rejected",
                "candidate_execution_schema_rejected",
            }:
                _execution_census_error("execution_exclusion_reason_invalid")
            candidate_execution_exclusion_count += 1
        seen_excluded_request_ids.add(request_id)
    if candidate_execution_exclusion_count != provisional_failed_result_count:
        _execution_census_error("provisional_failed_result_census_mismatch")

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
            or (
                design_version == CURRENT_DESIGN_VERSION
                and (
                    outcome_join.get("target_date") != report.get("target_date")
                    or outcome_join.get("materialized_report_content_sha256")
                    != report.get("materialized_report_content_sha256")
                    or not _valid_sha256(outcome_join.get("evidence_sha256"))
                )
            )
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
        or (
            design_version == CURRENT_DESIGN_VERSION
            and result.get("tactical_micro_reversion_evidence_sha256")
            != outcome_by_key[str(result.get("outcome_join_key"))].get(
                "evidence_sha256"
            )
        )
        for result in results
    ):
        _execution_census_error("outcome_join_result_binding_mismatch")

    evaluation_rows = evaluation.get("rows")
    evaluation_exclusions = evaluation.get("exclusions")
    expected_economic_exclusions: list[dict[str, Any]] = []
    for parent_id, parent_results in result_by_parent.items():
        result_by_arm = {
            str(result.get("micro_reversion_replay_arm") or ""): result
            for result in parent_results
        }
        unsupported_arm_actions: list[dict[str, Any]] = []
        for arm in expected_arms:
            replay_result = result_by_arm[arm].get("replay_result")
            replay_result = replay_result if isinstance(replay_result, Mapping) else {}
            response = replay_result.get("candidate_response")
            response = response if isinstance(response, Mapping) else {}
            action = str(response.get("action") or "UNKNOWN").upper()
            exposure_role, _ = quality._micro_reversion_action_exposure(
                str(replay_result.get("stage") or ""),
                action,
                dict(response),
                trim_retains_existing_position=(strict_current_metrics),
            )
            if exposure_role == "economic_exposure_not_applicable":
                unsupported_arm_actions.append(
                    {
                        "arm": arm,
                        "action": action,
                        "exposure_role": exposure_role,
                    }
                )
        if unsupported_arm_actions:
            expected_economic_exclusions.append(
                {
                    "paired_replay_parent_id": parent_id,
                    "reason": "unsupported_economic_exposure",
                    "unsupported_arm_actions": unsupported_arm_actions,
                }
            )
    expected_evaluation_row_count = committed_parent_count - len(
        expected_economic_exclusions
    )
    expected_evaluation_status = (
        "evaluated"
        if expected_evaluation_row_count
        else "no_comparable_economic_parents"
    )
    if (
        evaluation.get("schema") != "ai_micro_reversion_three_arm_evaluation_v1"
        or evaluation.get("ablation_design_version", LEGACY_DESIGN_VERSION)
        != design_version
        or (
            design_version == CURRENT_DESIGN_VERSION
            and evaluation.get("ablation_arms") != list(expected_arms)
        )
        or evaluation.get("status") != expected_evaluation_status
        or _authority_findings(evaluation)
        or (
            design_version == CURRENT_DESIGN_VERSION
            and _current_ablation_execution_authority_findings(evaluation)
        )
        or not isinstance(evaluation_rows, list)
        or not isinstance(evaluation_exclusions, list)
        or evaluation_exclusions != expected_economic_exclusions
        or _native_nonnegative_int(evaluation.get("complete_parent_count"))
        != len(evaluation_rows)
        or _native_nonnegative_int(evaluation.get("excluded_parent_count"))
        != len(expected_economic_exclusions)
        or len(evaluation_rows) != expected_evaluation_row_count
    ):
        _execution_census_error("evaluation_top_level_census_mismatch")
    evaluation_by_parent: dict[str, Mapping[str, Any]] = {}
    for raw_row in evaluation_rows:
        if not isinstance(raw_row, Mapping):
            _execution_census_error("evaluation_row_not_object")
        try:
            _validate_confirmation_window_axis(raw_row.get("confirmation_window_axis"))
        except ValueError:
            _execution_census_error("evaluation_confirmation_window_axis_invalid")
        parent_id = str(raw_row.get("paired_replay_parent_id") or "").strip()
        parent_results = result_by_parent.get(parent_id)
        arms = raw_row.get("arms")
        if (
            not parent_id
            or parent_id in evaluation_by_parent
            or parent_results is None
            or not isinstance(arms, Mapping)
            or set(arms) != set(expected_arms)
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
        mfe_pct = _finite_number(raw_row.get("mfe_pct"))
        mae_pct = _finite_number(raw_row.get("mae_pct"))
        first_hit = str(raw_row.get("first_hit") or "")
        target_first_delay_sec = _finite_number(raw_row.get("target_first_delay_sec"))
        outcome_ev_basis = str(raw_row.get("cost_adjusted_outcome_basis") or "")
        if (
            row_stage not in SUPPORTED_ECONOMIC_STAGES
            or cost_adjusted_outcome is None
            or mae_pct is None
            or (
                strict_current_metrics
                and (
                    mfe_pct is None
                    or outcome_ev_basis
                    not in {
                        "source_quality_adjusted_ev_pct",
                        "probe_cost_adjusted_ev_pct",
                        "cost_adjusted_end_return_pct",
                        "liquidity_adjusted_incremental_exit_value_pct",
                        "net_return_pct",
                    }
                    or _finite_number(raw_row.get("action_neutral_outcome_ev_pct"))
                    != cost_adjusted_outcome
                    or raw_row.get("action_neutral_outcome_ev_basis")
                    != outcome_ev_basis
                    or _finite_number(raw_row.get("action_neutral_mfe_pct")) != mfe_pct
                    or _finite_number(raw_row.get("action_neutral_mae_pct")) != mae_pct
                    or str(raw_row.get("action_neutral_first_hit") or "") != first_hit
                    or (
                        target_first_delay_sec is None
                        and raw_row.get("action_neutral_target_first_delay_sec")
                        is not None
                    )
                    or (
                        target_first_delay_sec is not None
                        and _finite_number(
                            raw_row.get("action_neutral_target_first_delay_sec")
                        )
                        != target_first_delay_sec
                    )
                )
            )
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
        for arm in expected_arms:
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
                trim_retains_existing_position=(strict_current_metrics),
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
            expected_comparable_ev = (
                expected_probe_ev if standardized_probe else expected_ev
            )
            expected_comparable_basis = (
                "standardized_probe_observation_ev_pct"
                if standardized_probe
                else (
                    "source_quality_adjusted_ev_pct"
                    if exposure_fraction is not None
                    else None
                )
            )

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
                or (
                    strict_current_metrics
                    and arm_value.get("runtime_normalized_action")
                    != (
                        "HOLD"
                        if response_action == "TRIM"
                        and exposure_role == "existing_position_exposure"
                        else response_action
                    )
                )
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
                or (
                    strict_current_metrics
                    and (
                        not same_optional_number(
                            arm_value.get("comparable_ev_pct"),
                            expected_comparable_ev,
                        )
                        or arm_value.get("comparable_ev_basis")
                        != expected_comparable_basis
                    )
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
    excluded_economic_parent_ids = {
        str(exclusion["paired_replay_parent_id"])
        for exclusion in expected_economic_exclusions
    }
    if (
        set(evaluation_by_parent)
        != set(result_by_parent) - excluded_economic_parent_ids
    ):
        _execution_census_error("evaluation_result_parent_set_mismatch")

    sample_floor = evaluation.get("sample_floor")
    arm_metrics = evaluation.get("arm_metrics")
    partitions = evaluation.get("stage_venue_partitions")
    sample_floor_valid = sample_floor == quality.OFFLINE_CONTRACT["sample_floor"] or (
        isinstance(sample_floor, Mapping)
        and _native_nonnegative_int(sample_floor.get("observed_rows"))
        == len(evaluation_rows)
    )
    if (
        not sample_floor_valid
        or not isinstance(arm_metrics, Mapping)
        or set(arm_metrics) != set(expected_arms)
        or any(
            not isinstance(arm_metrics[arm], Mapping)
            or _native_nonnegative_int(arm_metrics[arm].get("row_count"))
            != len(evaluation_rows)
            for arm in expected_arms
        )
        or not isinstance(partitions, list)
        or (bool(evaluation_rows) and not partitions)
        or (not evaluation_rows and partitions != [])
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
            or set(partition_metrics) != set(expected_arms)
            or any(
                not isinstance(partition_metrics[arm], Mapping)
                or _native_nonnegative_int(partition_metrics[arm].get("row_count"))
                != complete_count
                for arm in expected_arms
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


def _validate_execution_external_companion_bindings(
    report: Mapping[str, Any],
    *,
    materialized_report: Mapping[str, Any] | None,
    outcome_label_artifact: Mapping[str, Any] | None,
) -> None:
    """Reject a supplied companion from any generation but the executed one.

    Current-design reports have a wider canonical source-lineage validator below.
    This smaller binding applies to every clean-baseline report, including legacy
    reports whose persisted materialization or outcome companion was replaced
    after Provider execution.  Missing legacy companions remain archive-compatible;
    once supplied, however, they may never be consumed from a different generation.
    """

    if materialized_report is not None:
        declared_content_sha256 = str(
            materialized_report.get("report_content_sha256") or ""
        )
        if (
            materialized_report.get("schema")
            != quality.MICRO_REVERSION_MATERIALIZED_REQUEST_SCHEMA
            or materialized_report.get("target_date") != report.get("target_date")
            or not _valid_sha256(declared_content_sha256)
            or declared_content_sha256
            != _content_hash(materialized_report, "report_content_sha256")
            or report.get("materialized_report_content_sha256")
            != declared_content_sha256
            or report.get("materialized_report_artifact_sha256")
            != _sha256(materialized_report)
            or report.get("materialized_request_census_sha256")
            != quality._micro_reversion_materialized_request_census_sha256(
                materialized_report
            )
        ):
            raise ValueError("execution_report_materialized_companion_binding_mismatch")
    if outcome_label_artifact is not None and report.get(
        "outcome_label_artifact_sha256"
    ) != _sha256(outcome_label_artifact):
        raise ValueError("execution_report_outcome_companion_hash_mismatch")


def _validated_execution_rows(
    report: Mapping[str, Any],
    *,
    outcome_label_artifact: Mapping[str, Any] | None = None,
    source_bridge_report: Mapping[str, Any] | None = None,
    materialized_report: Mapping[str, Any] | None = None,
    source_bundle_report: Mapping[str, Any] | None = None,
    prepared_artifact: Mapping[str, Any] | None = None,
    paired_report: Mapping[str, Any] | None = None,
    checkpoint_artifact: Mapping[str, Any] | None = None,
    provider_ablation_floor_artifact: Mapping[str, Any] | None = None,
    provider_floor_validation_cache: (
        quality.MicroReversionProviderFloorValidationCache | None
    ) = None,
) -> list[dict[str, Any]]:
    if report.get("schema") != quality.MICRO_REVERSION_EXECUTION_RESULT_SCHEMA:
        raise ValueError("execution_report_schema_invalid")
    if report.get("report_content_sha256") != _content_hash(
        report, "report_content_sha256"
    ):
        raise ValueError("execution_report_content_hash_mismatch")
    design_version = str(report.get("ablation_design_version") or LEGACY_DESIGN_VERSION)
    try:
        expected_arms = arm_set_for_design(design_version)
    except ValueError as exc:
        raise ValueError("execution_report_ablation_design_invalid") from exc
    if report.get("ablation_design_version") is not None and report.get(
        "ablation_arms"
    ) != list(expected_arms):
        raise ValueError("execution_report_ablation_arms_mismatch")
    prompt_comparison = comparison_roles_for_design(design_version)[1]
    if _authority_findings(report):
        raise ValueError("execution_report_authority_invalid")
    if design_version == CURRENT_DESIGN_VERSION and (
        _current_ablation_execution_authority_findings(report)
    ):
        raise ValueError("execution_report_current_authority_invalid")
    try:
        report_date = date.fromisoformat(str(report.get("target_date") or ""))
    except ValueError as exc:
        raise ValueError("execution_report_target_date_invalid") from exc
    if report_date < CLEAN_BASELINE_DATE:
        raise ValueError("execution_report_before_clean_baseline")
    if (
        report_date >= date.fromisoformat(CURRENT_DESIGN_ACTIVATION_DATE)
        and design_version != CURRENT_DESIGN_VERSION
    ):
        raise ValueError("execution_report_current_design_required")
    strict_current_metrics = bool(
        design_version == CURRENT_DESIGN_VERSION
        and report_date >= date.fromisoformat(CURRENT_DESIGN_ACTIVATION_DATE)
    )
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
    _validate_execution_external_companion_bindings(
        report,
        materialized_report=materialized_report,
        outcome_label_artifact=outcome_label_artifact,
    )
    validated_materialized_report: dict[str, Any] | None = None
    materialized_requests: list[dict[str, Any]] | None = None
    captured_control_action_by_parent: dict[str, str] = {}
    if design_version == CURRENT_DESIGN_VERSION and report_date >= date.fromisoformat(
        CURRENT_DESIGN_ACTIVATION_DATE
    ):
        if not isinstance(materialized_report, Mapping):
            raise ValueError("execution_report_materialized_companion_missing")
        validated_materialized_report = dict(materialized_report)
        if validated_materialized_report.get("target_date") != report.get(
            "target_date"
        ):
            raise ValueError("execution_report_materialized_target_date_mismatch")
        materialized_requests = quality._validate_micro_reversion_materialized_report(
            validated_materialized_report
        )
        if not isinstance(source_bundle_report, Mapping):
            raise ValueError("execution_report_source_bundle_companion_missing")
        if not isinstance(prepared_artifact, Mapping):
            raise ValueError("execution_report_prepared_companion_missing")
        if not isinstance(paired_report, Mapping):
            raise ValueError("execution_report_paired_companion_missing")
        _validate_current_materialized_source_lineage(
            materialized_report=validated_materialized_report,
            source_bundle_report=source_bundle_report,
            prepared_artifact=prepared_artifact,
            source_bridge_report=source_bridge_report,
            paired_report=paired_report,
        )
        _validate_current_provider_preflight_commitments(
            report=report,
            target_date=report_date.isoformat(),
            materialized_report=validated_materialized_report,
            provider_ablation_floor_artifact=provider_ablation_floor_artifact,
            checkpoint_artifact=checkpoint_artifact,
            provider_floor_validation_cache=provider_floor_validation_cache,
        )
        if (
            report.get("materialized_report_content_sha256")
            != validated_materialized_report.get("report_content_sha256")
            or report.get("materialized_report_artifact_sha256")
            != _sha256(validated_materialized_report)
            or report.get("materialized_request_census_sha256")
            != quality._micro_reversion_materialized_request_census_sha256(
                validated_materialized_report
            )
        ):
            raise ValueError("execution_report_materialized_companion_binding_mismatch")
        actions_by_parent: dict[str, set[str]] = defaultdict(set)
        arms_by_parent: dict[str, set[str]] = defaultdict(set)
        for materialized_request in materialized_requests:
            parent_id = materialized_request.get("paired_replay_parent_id")
            arm = materialized_request.get("micro_reversion_replay_arm")
            control = materialized_request.get("control")
            captured_action = (
                control.get("captured_action") if isinstance(control, Mapping) else None
            )
            if (
                not isinstance(parent_id, str)
                or not parent_id
                or parent_id != parent_id.strip()
                or not isinstance(arm, str)
                or arm not in expected_arms
                or not isinstance(captured_action, str)
                or not captured_action
                or captured_action != captured_action.strip()
            ):
                raise ValueError(
                    "execution_report_materialized_control_action_binding_invalid"
                )
            actions_by_parent[parent_id].add(captured_action.upper())
            arms_by_parent[parent_id].add(arm)
        if not actions_by_parent or any(
            len(actions_by_parent[parent_id]) != 1
            or arms_by_parent[parent_id] != set(expected_arms)
            for parent_id in actions_by_parent
        ):
            raise ValueError(
                "execution_report_materialized_control_action_binding_invalid"
            )
        captured_control_action_by_parent = {
            parent_id: next(iter(actions))
            for parent_id, actions in actions_by_parent.items()
        }
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
    provisional_failed_result_count = _native_nonnegative_int(
        report.get("provisional_failed_result_count", 0)
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
        or _native_nonnegative_int(report.get("result_count")) != result_count
        or isinstance(request_count, bool)
        or not isinstance(request_count, int)
        or request_count < result_count
        or (
            materialized_requests is not None
            and request_count != len(materialized_requests)
        )
        or result_count <= 0
        or result_count % len(expected_arms) != 0
        or _native_nonnegative_int(report.get("execution_failed_count")) != 0
        or not isinstance(execution_exclusions, list)
        or _native_nonnegative_int(report.get("execution_exclusion_count"))
        != len(execution_exclusions)
        or not isinstance(blocking_execution_exclusions, list)
        or _native_nonnegative_int(report.get("blocking_execution_exclusion_count"))
        != len(blocking_execution_exclusions)
        or bool(blocking_execution_exclusions)
        or uncommitted_result_count != 0
        or provisional_failed_result_count is None
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
                or report.get("candidate_model_call_attempted")
                is not bool(provisional_failed_result_count)
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
    if design_version == CURRENT_DESIGN_VERSION and report_date >= date.fromisoformat(
        CURRENT_DESIGN_ACTIVATION_DATE
    ):
        if not isinstance(outcome_label_artifact, Mapping):
            raise ValueError("execution_report_outcome_companion_missing")
        outcome_label_artifact = dict(outcome_label_artifact)
        if report.get("outcome_label_artifact_sha256") != _sha256(
            outcome_label_artifact
        ):
            raise ValueError("execution_report_outcome_companion_hash_mismatch")
        quality._validate_micro_reversion_outcome_label_artifact(
            outcome_label_artifact,
            source_bridge_report=source_bridge_report,
            expected_design_version=CURRENT_DESIGN_VERSION,
            expected_target_date=str(report.get("target_date") or ""),
            expected_materialized_report_content_sha256=str(
                report.get("materialized_report_content_sha256") or ""
            ),
            expected_materialized_report=validated_materialized_report,
        )
        parent_bindings = outcome_label_artifact.get("materialized_parent_bindings")
        request_refs = report.get("request_refs")
        if not isinstance(parent_bindings, list) or not isinstance(request_refs, list):
            raise ValueError("execution_report_outcome_parent_census_missing")
        refs_by_parent: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
        for request_ref in request_refs:
            if not isinstance(request_ref, Mapping):
                raise ValueError("execution_report_request_ref_invalid")
            refs_by_parent[
                str(request_ref.get("paired_replay_parent_id") or "")
            ].append(request_ref)
        if set(refs_by_parent) != {
            str(binding.get("paired_replay_parent_id") or "")
            for binding in parent_bindings
            if isinstance(binding, Mapping)
        }:
            raise ValueError("execution_report_outcome_parent_census_mismatch")
        for binding in parent_bindings:
            if not isinstance(binding, Mapping):
                raise ValueError("execution_report_outcome_parent_binding_invalid")
            parent_id = str(binding.get("paired_replay_parent_id") or "")
            parent_refs = refs_by_parent.get(parent_id, [])
            if (
                len(parent_refs) != len(EXPECTED_ARMS)
                or {str(ref.get("paired_replay_id") or "") for ref in parent_refs}
                != set(binding.get("request_ids") or [])
                or {
                    str(ref.get("micro_reversion_replay_arm") or "")
                    for ref in parent_refs
                }
                != set(binding.get("arms") or [])
                or any(
                    any(
                        ref.get(ref_field) != binding.get(binding_field)
                        for ref_field, binding_field in (
                            ("decision_trace_id", "decision_trace_id"),
                            ("decision_stage", "decision_stage"),
                            ("stock_code", "stock_code"),
                            ("effective_venue", "effective_venue"),
                            ("session_bucket", "session_bucket"),
                            ("outcome_join_key", "outcome_join_key"),
                            (
                                "tactical_micro_reversion_evidence_sha256",
                                "tactical_micro_reversion_evidence_sha256",
                            ),
                            (
                                "outcome_source_commitment_sha256",
                                "outcome_source_commitment_sha256",
                            ),
                            (
                                "future_outcome_source_pool_content_sha256",
                                "future_outcome_source_pool_content_sha256",
                            ),
                        )
                    )
                    for ref in parent_refs
                )
            ):
                raise ValueError("execution_report_outcome_parent_binding_mismatch")
        outcome_label_proofs = outcome_label_artifact.get("labels")
        if not isinstance(outcome_label_proofs, list):
            raise ValueError("execution_report_outcome_companion_labels_invalid")
        proof_by_join_key: dict[str, dict[str, Any]] = {}
        for proof in outcome_label_proofs:
            if not isinstance(proof, dict):
                raise ValueError("execution_report_outcome_proof_invalid")
            quality._validate_micro_reversion_action_neutral_label(proof)
            join_key = str(proof.get("label_id") or "")
            if (
                not join_key
                or join_key in proof_by_join_key
                or proof.get("target_date") != report.get("target_date")
                or proof.get("materialized_report_content_sha256")
                != report.get("materialized_report_content_sha256")
            ):
                raise ValueError("execution_report_outcome_proof_binding_invalid")
            proof_by_join_key[join_key] = proof
        expected_join_keys = {
            str(result.get("outcome_join_key") or "") for result in results
        }
        if not expected_join_keys or not expected_join_keys.issubset(proof_by_join_key):
            raise ValueError("execution_report_outcome_proof_join_census_invalid")
        for result in results:
            proof = proof_by_join_key[str(result.get("outcome_join_key") or "")]
            if result.get("outcome_label_content_sha256") != _sha256(
                proof
            ) or result.get("tactical_micro_reversion_evidence_sha256") != proof.get(
                "evidence_sha256"
            ):
                raise ValueError("execution_report_outcome_proof_result_mismatch")
        rebuilt_evaluation = quality.build_micro_reversion_three_arm_evaluation(
            results=[dict(result) for result in results],
            outcome_labels=outcome_label_proofs,
            ablation_design_version=CURRENT_DESIGN_VERSION,
        )
        if rebuilt_evaluation != evaluation_without_hash:
            raise ValueError("three_arm_evaluation_canonical_rebuild_mismatch")
        if not isinstance(checkpoint_artifact, Mapping):
            raise ValueError("execution_report_checkpoint_companion_missing")
        assert validated_materialized_report is not None
        quality.validate_current_micro_reversion_checkpoint_companion(
            report=report,
            checkpoint_artifact=checkpoint_artifact,
            materialized_report=validated_materialized_report,
            outcome_labels=outcome_label_proofs,
        )
    rows = _validate_execution_exact_census(
        report=report,
        results=results,
        evaluation=evaluation,
    )

    result_contracts: dict[str, dict[str, str]] = defaultdict(dict)
    result_prompt_hashes: dict[str, dict[str, str]] = defaultdict(dict)
    result_source_event_stages: dict[str, set[str | None]] = defaultdict(set)
    result_decision_timestamps: dict[str, set[str]] = defaultdict(set)
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
        prompt_hash = str(result.get("prompt_sha256") or "")
        decision_at = _aware_artifact_datetime(result.get("decision_ts"))
        if decision_at is None or decision_at.date() != report_date:
            _execution_census_error("result_decision_timestamp_invalid")
        if parent and arm and contract_hash and _valid_sha256(prompt_hash):
            result_contracts[parent][arm] = contract_hash
            result_prompt_hashes[parent][arm] = prompt_hash
            result_decision_timestamps[parent].add(decision_at.isoformat())
            source_event_stage = result.get("source_event_stage")
            if source_event_stage is not None and (
                not isinstance(source_event_stage, str)
                or not source_event_stage
                or source_event_stage != source_event_stage.strip()
            ):
                _execution_census_error("result_source_event_stage_invalid")
            result_source_event_stages[parent].add(source_event_stage)
    completed_parent_ids = {
        parent_id
        for parent_id, contracts in result_contracts.items()
        if set(contracts) == set(expected_arms)
    }
    for exclusion in execution_exclusions:
        if (
            not isinstance(exclusion, Mapping)
            or not str(exclusion.get("paired_replay_parent_id") or "")
            or str(exclusion.get("paired_replay_parent_id") or "")
            in completed_parent_ids
        ):
            raise ValueError("execution_report_exclusion_scope_invalid")

    report_request_refs = report.get("request_refs")
    if not isinstance(report_request_refs, list):
        _execution_census_error("execution_request_refs_missing_after_validation")
    request_refs_by_parent: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for request_ref in report_request_refs:
        if not isinstance(request_ref, Mapping):
            _execution_census_error("execution_request_ref_invalid_after_validation")
        request_refs_by_parent[
            str(request_ref.get("paired_replay_parent_id") or "")
        ].append(request_ref)

    normalized: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, Mapping):
            _execution_census_error("evaluation_row_not_object_after_validation")
        parent = str(row.get("paired_replay_parent_id") or "")
        arms = row.get("arms")
        contracts = result_contracts.get(parent, {})
        prompt_hashes = result_prompt_hashes.get(parent, {})
        source_event_stages = result_source_event_stages.get(parent, set())
        if not parent or not isinstance(arms, Mapping):
            _execution_census_error("evaluation_row_shape_invalid")
        captured_control_action = captured_control_action_by_parent.get(parent)
        if (
            design_version == CURRENT_DESIGN_VERSION
            and report_date >= date.fromisoformat(CURRENT_DESIGN_ACTIVATION_DATE)
            and not captured_control_action
        ):
            _execution_census_error("evaluation_control_action_binding_missing")
        if len(result_decision_timestamps.get(parent, set())) != 1:
            _execution_census_error("result_parent_decision_timestamp_mismatch")
        if (
            set(arms) != set(expected_arms)
            or set(contracts) != set(expected_arms)
            or set(prompt_hashes) != set(expected_arms)
            or len(source_event_stages) != 1
        ):
            _execution_census_error("evaluation_result_arm_binding_mismatch")
        source_event_stage = next(iter(source_event_stages))
        decision_ts = next(iter(result_decision_timestamps[parent]))
        evaluation_decision_ts = row.get("decision_ts")
        if evaluation_decision_ts is not None:
            evaluation_decision_at = _aware_artifact_datetime(evaluation_decision_ts)
            if (
                evaluation_decision_at is None
                or evaluation_decision_at.isoformat() != decision_ts
            ):
                _execution_census_error("evaluation_result_decision_timestamp_mismatch")
        baseline = arms[expected_arms[0]]
        micro_control = arms[expected_arms[1]]
        candidate = arms[expected_arms[2]]
        if (
            not isinstance(baseline, Mapping)
            or not isinstance(micro_control, Mapping)
            or not isinstance(candidate, Mapping)
        ):
            _execution_census_error("evaluation_economic_arm_invalid")

        def comparable_ev(
            arm_value: Mapping[str, Any],
        ) -> tuple[float, str]:
            full_exposure_ev = _finite_number(
                arm_value.get("source_quality_adjusted_ev_pct")
            )
            probe_ev = _finite_number(
                arm_value.get("standardized_probe_observation_ev_pct")
            )
            if full_exposure_ev is not None and probe_ev is None:
                value = full_exposure_ev
                basis = "full_exposure_ev_pct"
                persisted_basis = "source_quality_adjusted_ev_pct"
            elif probe_ev is not None and full_exposure_ev is None:
                value = probe_ev
                basis = "standardized_one_share_probe_ev_pct"
                persisted_basis = "standardized_probe_observation_ev_pct"
            else:
                _execution_census_error("evaluation_economic_metric_invalid")
                raise AssertionError("unreachable")
            if strict_current_metrics and (
                _finite_number(arm_value.get("comparable_ev_pct")) != value
                or arm_value.get("comparable_ev_basis") != persisted_basis
            ):
                _execution_census_error("evaluation_comparable_ev_binding_invalid")
            return value, basis

        baseline_ev, baseline_ev_basis = comparable_ev(baseline)
        control_ev, control_ev_basis = comparable_ev(micro_control)
        candidate_ev, candidate_ev_basis = comparable_ev(candidate)
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
        current_baseline_values: dict[str, Any] = {}
        if design_version == CURRENT_DESIGN_VERSION:
            current_baseline_values = {
                "baseline_action": str(baseline.get("action") or "UNKNOWN"),
                "baseline_ev_pct": baseline_ev,
                "baseline_ev_basis": baseline_ev_basis,
                "feature_ev_delta_pct": control_ev - baseline_ev,
                "composite_ev_delta_pct": candidate_ev - baseline_ev,
                "baseline_notional_value_krw": _finite_number(
                    baseline.get("notional_incremental_value_krw")
                ),
                "baseline_severe_tail": baseline.get("severe_tail_exposure") is True,
                "baseline_signal_selected": (
                    baseline.get("economic_signal_selected") is True
                ),
            }
        full_parent_census = {
            "paired_replay_parent_id": parent,
            "arms": [
                {
                    "arm": arm,
                    "prompt_contract_sha256": contracts[arm],
                    "prompt_sha256": prompt_hashes[arm],
                }
                for arm in expected_arms
            ],
        }
        parent_results = [
            result
            for result in results
            if str(result.get("paired_replay_parent_id") or "") == parent
        ]
        parent_request_refs = request_refs_by_parent.get(parent, [])
        execution_source_commitment_content = {
            "schema": "main_ai_quality_counterfactual_entry_execution_source_v1",
            "target_date": str(report.get("target_date") or ""),
            "paired_replay_parent_id": parent,
            "decision_trace_id": str(row.get("decision_trace_id") or ""),
            "execution_report_content_sha256": report.get("report_content_sha256"),
            "execution_report_artifact_sha256": _sha256(report),
            "three_arm_evaluation_content_sha256": evaluation.get(
                "evaluation_content_sha256"
            ),
            "evaluation_parent_row_sha256": _sha256(row),
            "execution_parent_request_refs_sha256": _sha256(parent_request_refs),
            "execution_parent_results_sha256": _sha256(parent_results),
            "outcome_label_content_sha256": row.get("outcome_label_content_sha256"),
            "outcome_label_artifact_sha256": report.get(
                "outcome_label_artifact_sha256"
            ),
            "materialized_report_content_sha256": report.get(
                "materialized_report_content_sha256"
            ),
            "materialized_report_artifact_sha256": report.get(
                "materialized_report_artifact_sha256"
            ),
            **(
                {
                    "provider_ablation_sample_floor_content_sha256": report.get(
                        "provider_ablation_sample_floor_content_sha256"
                    ),
                    "provider_ablation_sample_floor_artifact_sha256": report.get(
                        "provider_ablation_sample_floor_artifact_sha256"
                    ),
                }
                if strict_current_metrics
                else {}
            ),
            "full_parent_census_sha256": _sha256(full_parent_census),
        }
        required_execution_commitment_hash_fields = [
            "execution_report_content_sha256",
            "execution_report_artifact_sha256",
            "three_arm_evaluation_content_sha256",
            "evaluation_parent_row_sha256",
            "execution_parent_request_refs_sha256",
            "execution_parent_results_sha256",
            "outcome_label_content_sha256",
            "outcome_label_artifact_sha256",
            "materialized_report_content_sha256",
            "materialized_report_artifact_sha256",
            "full_parent_census_sha256",
        ]
        if strict_current_metrics:
            required_execution_commitment_hash_fields.extend(
                [
                    "provider_ablation_sample_floor_content_sha256",
                    "provider_ablation_sample_floor_artifact_sha256",
                ]
            )
        if any(
            not _valid_sha256(execution_source_commitment_content.get(field))
            for field in required_execution_commitment_hash_fields
        ):
            _execution_census_error("execution_diagnostic_source_commitment_invalid")
        execution_source_commitment = {
            **execution_source_commitment_content,
            "commitment_sha256": _sha256(execution_source_commitment_content),
        }
        normalized.append(
            {
                "target_date": str(report.get("target_date") or ""),
                "ablation_design_version": design_version,
                "comparison_role": prompt_comparison.comparison_role,
                "changed_axis": prompt_comparison.changed_axis,
                "r3_tuning_axis": (
                    "prompt_contract_effect_on_ask_depletion_context"
                    if design_version == CURRENT_DESIGN_VERSION
                    else "prompt_contract_effect"
                ),
                "paired_replay_parent_id": parent,
                "decision_trace_id": str(row.get("decision_trace_id") or ""),
                "decision_ts": decision_ts,
                "decision_stage": str(row.get("decision_stage") or "").lower(),
                "source_event_stage": source_event_stage,
                "effective_venue": str(row.get("effective_venue") or ""),
                "session_bucket": str(row.get("session_bucket") or ""),
                "stock_code": str(row.get("stock_code") or ""),
                "captured_control_action": captured_control_action,
                "control_contract_sha256": contracts[expected_arms[1]],
                "candidate_contract_sha256": contracts[expected_arms[2]],
                "control_prompt_sha256": prompt_hashes[expected_arms[1]],
                "candidate_prompt_sha256": prompt_hashes[expected_arms[2]],
                "control_action": str(micro_control.get("action") or "UNKNOWN"),
                "candidate_action": str(candidate.get("action") or "UNKNOWN"),
                "control_ev_pct": control_ev,
                "candidate_ev_pct": candidate_ev,
                "control_ev_basis": control_ev_basis,
                "candidate_ev_basis": candidate_ev_basis,
                "paired_ev_delta_pct": candidate_ev - control_ev,
                "action_neutral_outcome_ev_pct": _finite_number(
                    row.get("action_neutral_outcome_ev_pct")
                ),
                "action_neutral_outcome_ev_basis": str(
                    row.get("action_neutral_outcome_ev_basis") or ""
                ),
                "action_neutral_mfe_pct": _finite_number(
                    row.get("action_neutral_mfe_pct")
                ),
                "action_neutral_mae_pct": _finite_number(
                    row.get("action_neutral_mae_pct")
                ),
                "action_neutral_first_hit": str(
                    row.get("action_neutral_first_hit") or ""
                ),
                "action_neutral_target_first_delay_sec": _finite_number(
                    row.get("action_neutral_target_first_delay_sec")
                ),
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
                "full_parent_arm_count": len(expected_arms),
                "full_parent_arms": list(expected_arms),
                "full_parent_census_verified": True,
                "full_parent_census": full_parent_census,
                "full_parent_census_sha256": _sha256(full_parent_census),
                "execution_source_commitment": execution_source_commitment,
                "execution_source_commitment_sha256": (
                    execution_source_commitment["commitment_sha256"]
                ),
                **current_baseline_values,
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


def _validate_current_materialized_source_lineage(
    *,
    materialized_report: Mapping[str, Any],
    source_bundle_report: Mapping[str, Any],
    prepared_artifact: Mapping[str, Any],
    source_bridge_report: Mapping[str, Any] | None,
    paired_report: Mapping[str, Any],
) -> None:
    """Rebuild current A/B/C from independently persisted source artifacts."""

    if not isinstance(source_bridge_report, Mapping):
        raise ValueError("materialized_source_lineage_bridge_companion_missing")
    quality.validate_current_materialized_source_lineage(
        materialized_report=materialized_report,
        source_bundle_report=source_bundle_report,
        prepared_artifact=prepared_artifact,
        source_bridge_report=source_bridge_report,
        paired_report=paired_report,
    )


def _validate_current_provider_preflight_commitments(
    *,
    report: Mapping[str, Any],
    target_date: str,
    materialized_report: Mapping[str, Any],
    provider_ablation_floor_artifact: Mapping[str, Any] | None,
    checkpoint_artifact: Mapping[str, Any] | None,
    provider_floor_validation_cache: (
        quality.MicroReversionProviderFloorValidationCache | None
    ) = None,
) -> None:
    """Bind a current execution to its independently rebuilt Provider gates."""

    if not isinstance(provider_ablation_floor_artifact, Mapping):
        raise ValueError("current_execution_provider_floor_companion_missing")
    floor_target_date = str(provider_ablation_floor_artifact.get("target_date") or "")
    validated_floor = quality.validate_micro_reversion_provider_ablation_floor_artifact(
        provider_ablation_floor_artifact,
        expected_target_date=floor_target_date,
        current_materialized_report=materialized_report,
        expected_materialized_target_date=target_date,
        validation_cache=provider_floor_validation_cache,
    )
    provider_budget = report.get("provider_budget")
    try:
        physical_execution_date = date.fromisoformat(
            str(
                provider_budget.get("execution_date")
                if isinstance(provider_budget, Mapping)
                else ""
            )
        )
        execution_target = date.fromisoformat(target_date)
        floor_target = date.fromisoformat(floor_target_date)
    except ValueError as exc:
        raise ValueError(
            "current_execution_provider_floor_time_binding_invalid"
        ) from exc
    if not execution_target <= floor_target <= physical_execution_date:
        raise ValueError("current_execution_provider_floor_time_binding_invalid")
    expected_floor_path = provider_ablation_floor_path(floor_target_date).absolute()
    if (
        Path(str(report.get("provider_ablation_sample_floor_path") or "")).absolute()
        != expected_floor_path
        or report.get("provider_ablation_sample_floor_content_sha256")
        != validated_floor.get("floor_content_sha256")
        or report.get("provider_ablation_sample_floor_artifact_sha256")
        != _sha256(validated_floor)
    ):
        raise ValueError("current_execution_provider_floor_binding_mismatch")
    try:
        capacity_gate = quality.validate_micro_reversion_provider_capacity_gate_receipt(
            report.get("provider_capacity_gate"),
            expected_target_date=target_date,
        )
        preflight_gate = (
            quality.validate_micro_reversion_provider_capacity_gate_receipt(
                report.get("provider_capacity_preflight_gate"),
                expected_target_date=target_date,
            )
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("current_execution_provider_capacity_binding_invalid") from exc
    if report.get("provider_capacity_gate_content_sha256") != _sha256(
        capacity_gate
    ) or report.get("provider_capacity_preflight_gate_content_sha256") != _sha256(
        preflight_gate
    ):
        raise ValueError("current_execution_provider_capacity_binding_invalid")
    raw_call_receipts = report.get("provider_call_capacity_receipts")
    declared_call_receipt_count = report.get("provider_call_capacity_receipt_count")
    reused_call_receipt_count = report.get(
        "provider_call_capacity_reused_receipt_count"
    )
    new_call_receipt_count = report.get("provider_call_capacity_new_receipt_count")
    if (
        not isinstance(raw_call_receipts, list)
        or isinstance(declared_call_receipt_count, bool)
        or not isinstance(declared_call_receipt_count, int)
        or declared_call_receipt_count != len(raw_call_receipts)
        or isinstance(reused_call_receipt_count, bool)
        or not isinstance(reused_call_receipt_count, int)
        or reused_call_receipt_count < 0
        or isinstance(new_call_receipt_count, bool)
        or not isinstance(new_call_receipt_count, int)
        or new_call_receipt_count < 0
        or reused_call_receipt_count + new_call_receipt_count
        != declared_call_receipt_count
        or report.get("provider_call_capacity_receipts_sha256")
        != _sha256(raw_call_receipts)
    ):
        raise ValueError("current_execution_provider_capacity_receipts_invalid")
    call_receipt_hash_by_attempt: dict[tuple[str, int], str] = {}
    for raw_receipt in raw_call_receipts:
        if not isinstance(raw_receipt, Mapping):
            raise ValueError("current_execution_provider_capacity_receipts_invalid")
        request_id = str(raw_receipt.get("paired_replay_id") or "")
        attempt_number = raw_receipt.get("offline_provider_attempt_number")
        try:
            receipt = quality.validate_micro_reversion_provider_capacity_gate_receipt(
                raw_receipt.get("provider_capacity_gate"),
                expected_target_date=target_date,
            )
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "current_execution_provider_capacity_receipts_invalid"
            ) from exc
        receipt_hash = str(
            raw_receipt.get("provider_capacity_gate_content_sha256") or ""
        )
        if (
            set(raw_receipt)
            != {
                "paired_replay_id",
                "offline_provider_attempt_number",
                "provider_capacity_gate",
                "provider_capacity_gate_content_sha256",
            }
            or not request_id
            or isinstance(attempt_number, bool)
            or not isinstance(attempt_number, int)
            or attempt_number <= 0
            or (request_id, attempt_number) in call_receipt_hash_by_attempt
            or receipt_hash != _sha256(receipt)
        ):
            raise ValueError("current_execution_provider_capacity_receipts_invalid")
        call_receipt_hash_by_attempt[(request_id, attempt_number)] = receipt_hash
    if not isinstance(checkpoint_artifact, Mapping):
        raise ValueError("current_execution_provider_capacity_checkpoint_missing")
    checkpoint_results = checkpoint_artifact.get("results")
    if not isinstance(checkpoint_results, list):
        raise ValueError("current_execution_provider_capacity_checkpoint_invalid")
    attempted_request_ids = list(
        dict.fromkeys(
            str(receipt.get("paired_replay_id") or "") for receipt in raw_call_receipts
        )
    )
    current_attempt_results = (
        checkpoint_results[-len(attempted_request_ids) :]
        if attempted_request_ids
        else []
    )
    if [
        str(result.get("paired_replay_id") or "") if isinstance(result, Mapping) else ""
        for result in current_attempt_results
    ] != attempted_request_ids:
        raise ValueError(
            "current_execution_provider_capacity_checkpoint_census_invalid"
        )
    expected_call_receipts: list[Mapping[str, Any]] = []
    for result in current_attempt_results:
        if not isinstance(result, Mapping):
            raise ValueError(
                "current_execution_provider_capacity_checkpoint_census_invalid"
            )
        attempt_receipts = result.get("provider_attempt_capacity_receipts")
        if not isinstance(attempt_receipts, list):
            raise ValueError(
                "current_execution_provider_capacity_result_binding_invalid"
            )
        expected_call_receipts.extend(attempt_receipts)
    if raw_call_receipts != expected_call_receipts:
        raise ValueError("current_execution_provider_capacity_result_binding_invalid")
    scope = report.get("provider_capacity_gate_scope")
    if (
        declared_call_receipt_count > 0 and scope != "selected_batch_preflight_core"
    ) or (declared_call_receipt_count == 0 and scope != "no_new_call_outer_preflight"):
        raise ValueError("current_execution_provider_capacity_scope_invalid")


def _validate_current_execution_artifact(
    *,
    report: dict[str, Any],
    target_date: str,
    materialized_report: dict[str, Any],
    source_bundle_report: dict[str, Any] | None = None,
    prepared_artifact: dict[str, Any] | None = None,
    paired_report: dict[str, Any] | None = None,
    outcome_label_artifact: dict[str, Any],
    expected_max_new_requests: int,
    expected_daily_attempt_cap: int,
    expected_daily_usd_cap: Decimal,
    expected_pricing_content_sha256: str,
    expected_provider_authority_binding: Mapping[str, Any] | None = None,
    source_bridge_report: dict[str, Any] | None = None,
    checkpoint_artifact: dict[str, Any] | None = None,
    provider_ablation_floor_artifact: dict[str, Any] | None = None,
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
    if expected_provider_authority_binding is not None and report.get(
        "provider_authority_binding"
    ) != dict(expected_provider_authority_binding):
        raise ValueError("current_execution_provider_authority_binding_mismatch")
    pricing_coverage_hash = ""
    if expected_provider_authority_binding is not None:
        pricing_coverage = report.get("provider_pricing_batch_coverage")
        pricing_coverage_hash = str(
            report.get("provider_pricing_batch_coverage_sha256") or ""
        )
        expected_coverage_by_key: dict[tuple[str, str, str, str], dict[str, Any]] = {}
        for request in materialized_report.get("requests") or []:
            if not isinstance(request, Mapping) or not isinstance(
                request.get("candidate"), Mapping
            ):
                raise ValueError("current_execution_provider_pricing_census_invalid")
            candidate = request["candidate"]
            provider = str(candidate.get("provider") or "").strip().lower()
            model = str(candidate.get("model") or "").strip()
            physical_model_id: str | None = None
            region_name: str | None = None
            if provider == "bedrock":
                profile = candidate.get("bedrock_request_profile")
                if not isinstance(profile, Mapping):
                    raise ValueError("current_execution_bedrock_pricing_route_missing")
                physical_model_id = str(profile.get("model_id") or "").strip()
                region_name = str(profile.get("region_name") or "").strip().lower()
                if not physical_model_id or not region_name:
                    raise ValueError("current_execution_bedrock_pricing_route_missing")
            key = (provider, model, physical_model_id or "", region_name or "")
            expected_coverage_by_key[key] = {
                "provider": provider,
                "model": model,
                "physical_model_id": physical_model_id,
                "region_name": region_name,
            }
        expected_pricing_coverage = [
            expected_coverage_by_key[key] for key in sorted(expected_coverage_by_key)
        ]
        if (
            pricing_coverage != expected_pricing_coverage
            or pricing_coverage_hash != _sha256(expected_pricing_coverage)
        ):
            raise ValueError("current_execution_provider_pricing_census_mismatch")
    if expected_provider_authority_binding is not None and isinstance(
        checkpoint_artifact, Mapping
    ):
        for checkpoint_result in checkpoint_artifact.get("results") or []:
            if not isinstance(checkpoint_result, Mapping):
                continue
            replay_result = checkpoint_result.get("replay_result")
            if not isinstance(replay_result, Mapping):
                continue
            for attempt in replay_result.get("candidate_attempts") or []:
                if not isinstance(attempt, Mapping):
                    continue
                provenance = attempt.get("provider_provenance")
                if not isinstance(provenance, Mapping) or not provenance.get(
                    "provider_budget_reservation_id"
                ):
                    continue
                if (
                    provenance.get("provider_authority_binding")
                    != dict(expected_provider_authority_binding)
                    or provenance.get("provider_pricing_batch_coverage_sha256")
                    != pricing_coverage_hash
                ):
                    raise ValueError(
                        "current_execution_checkpoint_provider_authority_binding_mismatch"
                    )
    requests = quality._validate_micro_reversion_materialized_report(
        materialized_report
    )
    request_ids = [str(request.get("paired_replay_id") or "") for request in requests]
    request_by_id = {
        str(request.get("paired_replay_id") or ""): request for request in requests
    }
    quality._validate_micro_reversion_outcome_label_artifact(
        outcome_label_artifact,
        source_bridge_report=source_bridge_report,
        expected_design_version=str(
            materialized_report.get("ablation_design_version") or LEGACY_DESIGN_VERSION
        ),
        expected_target_date=target_date,
        expected_materialized_report_content_sha256=(
            materialized_report.get("report_content_sha256")
        ),
        expected_materialized_report=materialized_report,
    )
    labels_by_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for label in outcome_label_artifact.get("labels") or []:
        if isinstance(label, dict) and label.get("label_id"):
            labels_by_id[str(label["label_id"])].append(label)
    expected_execution_exclusions = [
        {
            "paired_replay_parent_id": request.get("paired_replay_parent_id"),
            "paired_replay_id": request.get("paired_replay_id"),
            "micro_reversion_replay_arm": request.get("micro_reversion_replay_arm"),
            "stage": request.get("stage"),
            "provider": (request.get("candidate") or {}).get("provider"),
            "model": (request.get("candidate") or {}).get("model"),
            "reason": quality._micro_reversion_executor_exclusion(
                request,
                strict_current_response_chain=(
                    str(materialized_report.get("ablation_design_version") or "")
                    == CURRENT_DESIGN_VERSION
                    and target_date >= CURRENT_DESIGN_ACTIVATION_DATE
                ),
            ),
        }
        for request in requests
        if quality._micro_reversion_executor_exclusion(
            request,
            strict_current_response_chain=(
                str(materialized_report.get("ablation_design_version") or "")
                == CURRENT_DESIGN_VERSION
                and target_date >= CURRENT_DESIGN_ACTIVATION_DATE
            ),
        )
        is not None
    ]
    expected_execution_exclusions.extend(
        {
            "paired_replay_parent_id": request.get("paired_replay_parent_id"),
            "paired_replay_id": request.get("paired_replay_id"),
            "micro_reversion_replay_arm": request.get("micro_reversion_replay_arm"),
            "stage": request.get("stage"),
            "provider": (request.get("candidate") or {}).get("provider"),
            "model": (request.get("candidate") or {}).get("model"),
            "reason": "action_neutral_outcome_label_missing_or_ambiguous",
        }
        for request in requests
        if len(labels_by_id.get(str(request.get("outcome_join_key") or ""), [])) != 1
    )
    actual_execution_exclusions = report.get("execution_exclusions")
    if (
        not isinstance(actual_execution_exclusions, list)
        or actual_execution_exclusions[: len(expected_execution_exclusions)]
        != expected_execution_exclusions
    ):
        raise ValueError("current_execution_exclusion_census_mismatch")
    dynamically_excluded_request_ids: set[str] = set()
    for exclusion in actual_execution_exclusions[len(expected_execution_exclusions) :]:
        if not isinstance(exclusion, Mapping):
            raise ValueError("current_execution_exclusion_census_mismatch")
        request_id = str(exclusion.get("paired_replay_id") or "")
        request = request_by_id.get(request_id)
        if (
            request is None
            or request_id in dynamically_excluded_request_ids
            or exclusion.get("paired_replay_parent_id")
            != request.get("paired_replay_parent_id")
            or exclusion.get("micro_reversion_replay_arm")
            != request.get("micro_reversion_replay_arm")
            or exclusion.get("stage") != request.get("stage")
            or exclusion.get("provider")
            != (request.get("candidate") or {}).get("provider")
            or exclusion.get("model") != (request.get("candidate") or {}).get("model")
            or exclusion.get("reason")
            not in {
                "candidate_execution_provider_failed",
                "candidate_execution_provider_provenance_rejected",
                "candidate_execution_schema_rejected",
            }
        ):
            raise ValueError("current_execution_exclusion_census_mismatch")
        dynamically_excluded_request_ids.add(request_id)
    expected_execution_exclusions = list(actual_execution_exclusions)
    bound_results = quality._micro_reversion_reusable_results(
        existing_artifact=report,
        materialized_report=materialized_report,
        requests=requests,
        labels_by_id=labels_by_id,
        provider_ablation_sample_floor_content_sha256=str(
            report.get("provider_ablation_sample_floor_content_sha256") or ""
        ),
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
    ) != len(
        expected_blocking_exclusions
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

    rows = _validated_execution_rows(
        report,
        outcome_label_artifact=outcome_label_artifact,
        source_bridge_report=source_bridge_report,
        materialized_report=materialized_report,
        source_bundle_report=source_bundle_report,
        prepared_artifact=prepared_artifact,
        paired_report=paired_report,
        checkpoint_artifact=checkpoint_artifact,
        provider_ablation_floor_artifact=provider_ablation_floor_artifact,
    )
    evaluation = report.get("three_arm_evaluation")
    economic_exclusions = (
        evaluation.get("exclusions") if isinstance(evaluation, Mapping) else None
    )
    if not isinstance(economic_exclusions, list) or len(rows) + len(
        economic_exclusions
    ) != len(complete_parent_ids):
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


def _pipeline_owner_exclusion_manifest_findings(
    report: Mapping[str, Any], *, rows: Sequence[Any]
) -> list[str]:
    """Validate conservative owner-window quarantine without inferring attempts."""

    findings: list[str] = []
    manifest = report.get("pipeline_owner_exclusion_manifest")
    if not isinstance(manifest, Mapping):
        return ["pipeline_owner_exclusion_manifest_missing"]
    if manifest.get("schema") != PIPELINE_OWNER_EXCLUSION_MANIFEST_SCHEMA:
        findings.append("pipeline_owner_exclusion_manifest_schema_invalid")
    for field, expected in PIPELINE_OWNER_EXCLUSION_AUTHORITY_CONTRACT.items():
        if manifest.get(field) != expected:
            findings.append(f"pipeline_owner_exclusion_authority_invalid:{field}")
    if manifest.get("target_date") != report.get("target_date"):
        findings.append("pipeline_owner_exclusion_target_date_mismatch")

    entries = manifest.get("entries")
    if not isinstance(entries, list):
        return [*findings, "pipeline_owner_exclusion_entries_invalid"]
    expected_reason_counts: Counter[str] = Counter()
    owner_keys: set[str] = set()
    owner_pairs: set[tuple[str, str]] = set()
    total_gap_count = 0
    for entry in entries:
        if not isinstance(entry, Mapping):
            findings.append("pipeline_owner_exclusion_entry_invalid")
            continue
        record_id = str(entry.get("record_id") or "").strip()
        stock_code = str(entry.get("stock_code") or "").strip()
        owner_payload = {
            "target_date": report.get("target_date"),
            "record_id": record_id,
            "stock_code": stock_code,
        }
        owner_key = str(entry.get("owner_key_sha256") or "")
        gap_count = _native_nonnegative_int(entry.get("gap_count"))
        reason_counts = entry.get("reason_code_counts")
        if (
            not record_id
            or not re.fullmatch(r"[0-9]{6}", stock_code)
            or owner_key != _sha256(owner_payload)
            or owner_key in owner_keys
            or gap_count is None
            or gap_count <= 0
            or not isinstance(reason_counts, Mapping)
        ):
            findings.append("pipeline_owner_exclusion_entry_invalid")
            continue
        normalized_reason_counts: dict[str, int] = {}
        for raw_reason, raw_count in reason_counts.items():
            reason = str(raw_reason or "").strip()
            count = _native_nonnegative_int(raw_count)
            if (
                reason != "pipeline_lifecycle_identity_missing"
                or count is None
                or count <= 0
            ):
                findings.append("pipeline_owner_exclusion_reason_invalid")
                normalized_reason_counts = {}
                break
            normalized_reason_counts[reason] = count
        if (
            not normalized_reason_counts
            or sum(normalized_reason_counts.values()) != gap_count
        ):
            findings.append("pipeline_owner_exclusion_gap_census_invalid")
            continue
        owner_keys.add(owner_key)
        owner_pairs.add((record_id, stock_code))
        total_gap_count += gap_count
        expected_reason_counts.update(normalized_reason_counts)

    excluded_owner_count = _native_nonnegative_int(manifest.get("excluded_owner_count"))
    if excluded_owner_count is None or excluded_owner_count != len(entries):
        findings.append("pipeline_owner_exclusion_owner_census_mismatch")
    if manifest.get("gap_count") != total_gap_count:
        findings.append("pipeline_owner_exclusion_gap_census_mismatch")
    if manifest.get("reason_code_counts") != dict(
        sorted(expected_reason_counts.items())
    ):
        findings.append("pipeline_owner_exclusion_reason_census_mismatch")
    if report.get("pipeline_lifecycle_owner_scoped_gap_count") != total_gap_count:
        findings.append("pipeline_owner_exclusion_report_gap_census_mismatch")

    excluded_row_count = 0
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        if (str(row.get("record_id")), str(row.get("stock_code"))) not in owner_pairs:
            continue
        excluded_row_count += 1
        if (
            "pipeline_owner_window_missing_explicit_lifecycle_identity"
            not in (row.get("promotion_blockers") or [])
            or row.get("promotion_evidence_eligible") is not False
        ):
            findings.append("pipeline_owner_exclusion_row_not_quarantined")
    if manifest.get("excluded_lifecycle_count") != excluded_row_count:
        findings.append("pipeline_owner_exclusion_lifecycle_census_mismatch")

    scoped = _native_nonnegative_int(
        report.get("pipeline_lifecycle_owner_scoped_gap_count")
    )
    exact_scoped = _native_nonnegative_int(
        report.get("pipeline_lifecycle_exact_scoped_gap_count")
    )
    unscoped = _native_nonnegative_int(
        report.get("pipeline_lifecycle_unscoped_gap_count")
    )
    total = _native_nonnegative_int(
        report.get("pipeline_lifecycle_instrumentation_gap_count")
    )
    if (
        scoped is None
        or exact_scoped is None
        or unscoped is None
        or total is None
        or scoped + exact_scoped + unscoped != total
    ):
        findings.append("pipeline_owner_exclusion_total_gap_census_mismatch")
    missing_identity_count = _native_nonnegative_int(
        report.get("pipeline_lifecycle_missing_identity_count")
    )
    if (
        missing_identity_count is None
        or scoped is None
        or total is None
        or not scoped <= missing_identity_count <= total
    ):
        findings.append("pipeline_owner_exclusion_missing_identity_census_mismatch")
    accepted_row_count = _native_nonnegative_int(
        report.get("pipeline_lifecycle_accepted_row_count")
    )
    if accepted_row_count is None:
        findings.append("pipeline_owner_exclusion_accepted_census_invalid")
    else:
        expected_high_volume_block = bool(
            scoped is not None
            and scoped >= PIPELINE_OWNER_SCOPED_GAP_HARD_BLOCK_MIN_ROWS
            and scoped > accepted_row_count
        )
        if report.get("pipeline_owner_scoped_gap_high_volume_min_rows") != (
            PIPELINE_OWNER_SCOPED_GAP_HARD_BLOCK_MIN_ROWS
        ):
            findings.append("pipeline_owner_exclusion_high_volume_floor_mismatch")
        if report.get("pipeline_owner_scoped_gap_high_volume_blocked") is not (
            expected_high_volume_block
        ):
            findings.append("pipeline_owner_exclusion_high_volume_status_mismatch")
        if expected_high_volume_block and (
            "pipeline_owner_scoped_gap_high_volume"
            not in (report.get("global_source_quality_gate_blockers") or [])
        ):
            findings.append("pipeline_owner_exclusion_high_volume_gate_missing")
    return findings


def _historical_lifecycle_diagnostic_recovery_findings(
    report: Mapping[str, Any],
) -> list[str]:
    """Permanently exclude every archived diagnostic reconstruction from R2/R3."""

    findings: list[str] = []
    contracts = (
        (
            "historical_fill_before_submit_diagnostic_recovery_count",
            "historical_fill_before_submit_diagnostic_recovery_contract",
            HISTORICAL_FILL_BEFORE_SUBMIT_DIAGNOSTIC_RECOVERY_SCHEMA,
        ),
        (
            "historical_legacy_exit_submission_diagnostic_recovery_count",
            "historical_legacy_exit_submission_diagnostic_recovery_contract",
            HISTORICAL_LEGACY_EXIT_SUBMISSION_DIAGNOSTIC_RECOVERY_SCHEMA,
        ),
    )
    for count_field, contract_field, expected_schema in contracts:
        contract = report.get(contract_field)
        if _native_nonnegative_int(report.get(count_field)) != 0:
            findings.append(
                f"historical_lifecycle_diagnostic_recovery_count_nonzero:{count_field}"
            )
        if (
            not isinstance(contract, Mapping)
            or contract.get("schema") != expected_schema
            or contract.get("enabled") is not False
            or contract.get("promotion_evidence_eligible") is not False
            or contract.get("r2_r3_evidence_eligible") is not False
            or contract.get("raw_source_mutated") is not False
            or contract.get("runtime_effect") is not False
            or contract.get("order_authority") is not False
        ):
            findings.append(
                f"historical_lifecycle_diagnostic_recovery_contract_invalid:{contract_field}"
            )
    return findings


def _lifecycle_report_contract_findings(
    report: Mapping[str, Any], *, rows: Sequence[Any]
) -> list[str]:
    findings: list[str] = []
    try:
        carry_contract_required = date.fromisoformat(
            str(report.get("target_date") or "")
        ) >= date.fromisoformat(CARRY_IN_CUSTODY_REQUIRED_DATE)
    except ValueError:
        carry_contract_required = True
    carry_top_level_fields = {
        "custody_carry_schema",
        "custody_carry_lifecycle_count",
        "custody_carry_final_exit_reconciled_count",
    }
    present_carry_top_level_fields = {
        field for field in carry_top_level_fields if field in report
    }
    carry_top_level_contract_declared = bool(present_carry_top_level_fields)
    if (
        carry_top_level_contract_declared
        and present_carry_top_level_fields != carry_top_level_fields
    ):
        findings.append("custody_carry_top_level_contract_incomplete")
    findings.extend(_pipeline_owner_exclusion_manifest_findings(report, rows=rows))
    findings.extend(_historical_lifecycle_diagnostic_recovery_findings(report))
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
        ("broker_execution_timing_schema", BROKER_EXECUTION_TIMING_SCHEMA),
        (
            "broker_execution_ordering_time_source",
            BROKER_EXECUTION_ORDERING_TIME_SOURCE,
        ),
        (
            "broker_execution_occurrence_time_source",
            BROKER_EXECUTION_OCCURRENCE_TIME_SOURCE,
        ),
        (
            "broker_execution_receive_time_source",
            BROKER_EXECUTION_RECEIVE_TIME_SOURCE,
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
    if (
        report.get("legacy_unattested_receive_clock_diagnostic") is not False
        or report.get("legacy_unattested_receive_clock_diagnostic_last_date")
        != LEGACY_UNATTESTED_RECEIVE_CLOCK_DIAGNOSTIC_LAST_DATE
        or _native_nonnegative_int(
            report.get("legacy_unattested_receive_clock_recovery_count")
        )
        != 0
    ):
        findings.append("legacy_receive_clock_diagnostic_forbidden_for_r2_r3")

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
        "pipeline_lifecycle_unscoped_gap_count",
        "broker_order_no_cross_lifecycle_conflict_count",
        "broker_execution_cross_lifecycle_identity_conflict_count",
        "broker_late_arrival_outside_window_count",
    ):
        if _native_nonnegative_int(report.get(field)) != 0:
            findings.append(f"top_level_zero_census_invalid:{field}")

    row_dicts = [row for row in rows if isinstance(row, Mapping)]
    if len(row_dicts) != len(rows) or report.get("lifecycle_count") != len(rows):
        findings.append("lifecycle_row_census_mismatch")
    expected_population_counts: Counter[str] = Counter()
    expected_sim_scope_real_order_violation_count = 0
    expected_custody_carry_count = 0
    expected_custody_carry_final_exit_count = 0
    carry_row_fields = {
        "carry_in_custody_schema",
        "lifecycle_origin",
        "carry_in_entry_observed_at",
        "carry_in_entry_source",
    }
    for row in row_dicts:
        lifecycle_id = str(row.get("main_lifecycle_id") or "missing")
        population_scope = str(row.get("lifecycle_population_scope") or "")
        real_order_evidence = row.get("observed_real_order_evidence")
        source_population_scopes = row.get("source_population_scopes")
        concrete_broker_evidence = bool(
            row.get("observed_actual_broker_order_submitted") is True
            or any(
                (_native_nonnegative_int(row.get(field)) or 0) > 0
                for field in (
                    "broker_execution_unique_count",
                    "broker_submitted_order_count",
                    "broker_submission_custody_order_count",
                )
            )
            or any(
                (_finite_number(row.get(field)) or 0.0) > 0.0
                for field in (
                    "broker_execution_entry_covered_qty",
                    "broker_execution_exit_covered_qty",
                )
            )
            or any(
                isinstance(row.get(field), Mapping) and bool(row.get(field))
                for field in (
                    "broker_execution_provenance_state_counts",
                    "broker_submitted_requested_qty_by_order_no",
                    "broker_executed_order_qty_by_phase",
                )
            )
        )
        if population_scope not in LIFECYCLE_POPULATION_SCOPES:
            findings.append(f"lifecycle_population_scope_invalid:{lifecycle_id}")
            continue
        expected_population_counts[population_scope] += 1
        if real_order_evidence is not (
            population_scope == LIFECYCLE_POPULATION_REAL_SUBMITTED
        ):
            findings.append(f"lifecycle_population_evidence_mismatch:{lifecycle_id}")
        if concrete_broker_evidence is not (
            population_scope == LIFECYCLE_POPULATION_REAL_SUBMITTED
        ):
            findings.append(
                f"lifecycle_population_concrete_broker_evidence_mismatch:{lifecycle_id}"
            )
        if (
            not isinstance(source_population_scopes, list)
            or not all(isinstance(scope, str) for scope in source_population_scopes)
            or source_population_scopes != sorted(source_population_scopes)
            or len(source_population_scopes) != len(set(source_population_scopes))
            or any(
                scope not in PIPELINE_SOURCE_POPULATION_SCOPES
                for scope in source_population_scopes
            )
        ):
            findings.append(f"lifecycle_source_population_scope_invalid:{lifecycle_id}")
        if (
            population_scope == LIFECYCLE_POPULATION_CANDIDATE_OBSERVATION
            and row.get("promotion_evidence_eligible") is True
        ):
            findings.append(f"candidate_observation_promotion_eligible:{lifecycle_id}")
        sim_scope_real_order_violation = bool(
            real_order_evidence is True
            and isinstance(source_population_scopes, list)
            and "sim_observation_only" in source_population_scopes
        )
        expected_row_violation_count = int(sim_scope_real_order_violation)
        if sim_scope_real_order_violation:
            expected_sim_scope_real_order_violation_count += 1
        promotion_blockers = row.get("promotion_blockers")
        row_has_violation_blocker = bool(
            isinstance(promotion_blockers, list)
            and "sim_scope_real_order_contract_violation" in promotion_blockers
        )
        if (
            _native_nonnegative_int(
                row.get("sim_scope_real_order_contract_violation_count")
            )
            != expected_row_violation_count
            or row_has_violation_blocker is not sim_scope_real_order_violation
            or (
                sim_scope_real_order_violation
                and (
                    row.get("promotion_evidence_eligible") is not False
                    or row.get("row_source_quality_gate_pass") is not False
                )
            )
        ):
            findings.append(
                "lifecycle_sim_scope_real_order_incident_contract_invalid:"
                f"{lifecycle_id}"
            )
        present_carry_row_fields = {field for field in carry_row_fields if field in row}
        carry_row_contract_declared = bool(present_carry_row_fields)
        if carry_row_contract_declared and present_carry_row_fields != carry_row_fields:
            findings.append(
                f"lifecycle_custody_carry_contract_incomplete:{lifecycle_id}"
            )
        carry_in_custody = row.get("carry_in_custody_schema") == (
            CARRY_IN_CUSTODY_SCHEMA
        )
        if carry_in_custody:
            expected_custody_carry_count += 1
            try:
                carry_entry_at = datetime.fromisoformat(
                    str(row.get("carry_in_entry_observed_at") or "")
                )
                if carry_entry_at.tzinfo is None:
                    raise ValueError("carry_in_timestamp_not_timezone_aware")
                carry_entry_at = carry_entry_at.astimezone(KST)
                carry_entry_before_target = carry_entry_at.date() < date.fromisoformat(
                    str(report.get("target_date") or "")
                )
            except (TypeError, ValueError):
                carry_entry_before_target = False
            carry_terminal_state = row.get("terminal_state")
            carry_final_reconciled = carry_terminal_state == (
                "CUSTODY_CARRY_FINAL_EXIT_RECONCILED"
            )
            carry_exit_qty = _finite_number(row.get("exit_qty"))
            carry_exit_covered_qty = _finite_number(
                row.get("broker_execution_exit_covered_qty")
            )
            carry_broker_execution_count = _native_nonnegative_int(
                row.get("broker_execution_unique_count")
            )
            carry_terminal_contract_valid = bool(
                (
                    carry_final_reconciled
                    and (carry_exit_qty or 0.0) > 0.0
                    and (carry_exit_covered_qty or 0.0) >= (carry_exit_qty or 0.0)
                    and (carry_broker_execution_count or 0) > 0
                    and row.get("observed_real_order_evidence") is True
                    and population_scope == LIFECYCLE_POPULATION_REAL_SUBMITTED
                    and row.get("right_censored") is False
                )
                or (
                    carry_terminal_state == "CUSTODY_CARRY_HELD"
                    and row.get("right_censored") is True
                )
            )
            if carry_final_reconciled:
                expected_custody_carry_final_exit_count += 1
            if (
                row.get("lifecycle_origin") != "preexisting_position_custody"
                or row.get("carry_in_entry_source")
                not in {"stock.holding_started_at", "stock.buy_time"}
                or not carry_entry_before_target
                or carry_terminal_state
                not in {
                    "CUSTODY_CARRY_HELD",
                    "CUSTODY_CARRY_FINAL_EXIT_RECONCILED",
                }
                or not carry_terminal_contract_valid
                or (_finite_number(row.get("entry_fill_qty")) or 0.0) != 0.0
                or row.get("promotion_evidence_eligible") is not False
                or row.get("row_source_quality_gate_pass") is not False
                or not isinstance(promotion_blockers, list)
                or "custody_carry_in_entry_lifecycle_non_promotable"
                not in promotion_blockers
            ):
                findings.append(
                    f"lifecycle_custody_carry_contract_invalid:{lifecycle_id}"
                )
        elif carry_contract_required or carry_row_contract_declared:
            if (
                present_carry_row_fields != carry_row_fields
                or row.get("carry_in_custody_schema") is not None
                or row.get("lifecycle_origin") != "same_trade_date_lifecycle"
                or row.get("carry_in_entry_observed_at") is not None
                or row.get("carry_in_entry_source") is not None
                or str(row.get("terminal_state") or "").startswith("CUSTODY_CARRY_")
            ):
                findings.append(f"lifecycle_noncarry_contract_invalid:{lifecycle_id}")
    canonical_population_counts = {
        scope: expected_population_counts.get(scope, 0)
        for scope in sorted(LIFECYCLE_POPULATION_SCOPES)
    }
    if report.get("lifecycle_population_scope_counts") != (canonical_population_counts):
        findings.append("lifecycle_population_scope_census_mismatch")
    if report.get("real_submitted_lifecycle_count") != (
        canonical_population_counts[LIFECYCLE_POPULATION_REAL_SUBMITTED]
    ):
        findings.append("real_submitted_lifecycle_census_mismatch")
    if report.get("candidate_observation_lifecycle_count") != (
        canonical_population_counts[LIFECYCLE_POPULATION_CANDIDATE_OBSERVATION]
    ):
        findings.append("candidate_observation_lifecycle_census_mismatch")
    if report.get("sim_scope_real_order_contract_violation_count") != (
        expected_sim_scope_real_order_violation_count
    ):
        findings.append("sim_scope_real_order_contract_violation_census_mismatch")
    if (
        carry_contract_required
        or carry_top_level_contract_declared
        or expected_custody_carry_count > 0
    ) and (
        present_carry_top_level_fields != carry_top_level_fields
        or report.get("custody_carry_schema") != CARRY_IN_CUSTODY_SCHEMA
        or report.get("custody_carry_lifecycle_count") != expected_custody_carry_count
        or report.get("custody_carry_final_exit_reconciled_count")
        != expected_custody_carry_final_exit_count
    ):
        findings.append("custody_carry_top_level_census_mismatch")
    global_blockers = report.get("global_source_quality_gate_blockers")
    global_has_sim_scope_blocker = bool(
        isinstance(global_blockers, list)
        and "sim_scope_real_order_contract_violation" in global_blockers
    )
    if global_has_sim_scope_blocker is not bool(
        expected_sim_scope_real_order_violation_count
    ):
        findings.append("sim_scope_real_order_global_blocker_mismatch")
    if (
        report.get("lifecycle_population_partition_complete") is not True
        or sum(canonical_population_counts.values()) != len(row_dicts)
        or report.get("promotion_ready_population_scope")
        != f"{LIFECYCLE_POPULATION_REAL_SUBMITTED}_only"
    ):
        findings.append("lifecycle_population_partition_invalid")
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
        "broker_execution_receipt_companion_conflict_count",
        "broker_execution_receipt_companion_replay_duplicate_count",
        "broker_execution_order_progress_conflict_count",
        "broker_execution_submission_link_conflict_count",
        "broker_order_no_cross_lifecycle_conflict_count",
        "broker_execution_cross_lifecycle_identity_conflict_count",
        "broker_execution_replay_duplicate_count",
        "broker_execution_unique_count",
        "legacy_unattested_receive_clock_recovery_count",
        "historical_fill_before_submit_diagnostic_recovery_count",
        "historical_legacy_exit_submission_diagnostic_recovery_count",
        "broker_submission_custody_order_count",
        "broker_submission_custody_pending_order_count",
        "sim_scope_real_order_contract_violation_count",
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
        "pipeline_lifecycle_owner_scoped_gap_count",
        "pipeline_lifecycle_exact_scoped_gap_count",
        "broker_execution_provenance_gap_count",
        "broker_execution_conflict_count",
        "broker_execution_receipt_companion_conflict_count",
        "broker_execution_order_progress_conflict_count",
        "broker_execution_submission_link_conflict_count",
        "broker_order_no_cross_lifecycle_conflict_count",
        "broker_execution_cross_lifecycle_identity_conflict_count",
        "lifecycle_accumulator_overflow_row_count",
        "transition_event_identity_overflow_row_count",
        "broker_late_arrival_outside_window_count",
        "sim_scope_real_order_contract_violation_count",
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
    trace_context_path = row.get("decision_trace_context_path")
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
        or not isinstance(trace_context_path, list)
        or not trace_context_path
    ):
        findings.append("row_exact_lifecycle_identity_invalid")
    if isinstance(trace_ids, list) and isinstance(trace_context_path, list):
        trace_id_set = {str(trace_id or "") for trace_id in trace_ids}
        context_keys: set[tuple[str, str, str, str, str, str]] = set()
        for context in trace_context_path:
            if not isinstance(context, Mapping):
                findings.append("row_decision_trace_context_invalid")
                continue
            context_key = (
                str(context.get("decision_trace_id") or ""),
                str(context.get("stage") or ""),
                str(context.get("venue") or "").strip().upper(),
                quality._session(context.get("session_bucket")),
                str(context.get("venue_source") or ""),
                str(context.get("session_bucket_source") or ""),
            )
            if (
                not all(context_key)
                or context_key[0] not in trace_id_set
                or _native_nonnegative_int(context.get("transition_count")) in {None, 0}
                or context_key in context_keys
            ):
                findings.append("row_decision_trace_context_invalid")
            context_keys.add(context_key)
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
        ("broker_execution_timing_schema", BROKER_EXECUTION_TIMING_SCHEMA),
        (
            "broker_execution_ordering_time_source",
            BROKER_EXECUTION_ORDERING_TIME_SOURCE,
        ),
        (
            "broker_execution_occurrence_time_source",
            BROKER_EXECUTION_OCCURRENCE_TIME_SOURCE,
        ),
        (
            "broker_execution_receive_time_source",
            BROKER_EXECUTION_RECEIVE_TIME_SOURCE,
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
    try:
        first_execution_at = datetime.fromisoformat(
            str(row.get("first_fill_execution_at") or "")
        )
        final_execution_at = datetime.fromisoformat(
            str(row.get("final_exit_execution_at") or "")
        )
        if first_execution_at.tzinfo is None or final_execution_at.tzinfo is None:
            raise ValueError("execution_timestamp_timezone_missing")
        execution_dates_match = (
            first_execution_at.astimezone(KST).date().isoformat()
            == str(row.get("trade_date") or "")
            == str(report.get("target_date") or "")
            == final_execution_at.astimezone(KST).date().isoformat()
        )
        official_duration = (final_execution_at - first_execution_at).total_seconds()
    except (TypeError, ValueError):
        execution_dates_match = False
        official_duration = None
    declared_duration = _finite_number(row.get("actual_holding_duration_sec"))
    if (
        official_duration is None
        or not execution_dates_match
        or official_duration < 0
        or declared_duration is None
        or not math.isclose(
            declared_duration,
            official_duration,
            rel_tol=0.0,
            abs_tol=1e-6,
        )
        or row.get("duration_source")
        != "official_fid_908_first_fill_to_reconciled_final_exit"
        or row.get("label_horizon_used") is not False
    ):
        findings.append("row_official_execution_duration_contract_invalid")
    if row.get("broker_execution_provenance_gap_reasons") != []:
        findings.append("row_broker_execution_gap_reasons_present")
    for field in (
        "invalid_transition_count",
        "broker_execution_provenance_gap_count",
        "broker_execution_conflict_count",
        "broker_execution_receipt_companion_conflict_count",
        "broker_execution_order_progress_conflict_count",
        "broker_execution_submission_link_conflict_count",
        "broker_order_no_cross_lifecycle_conflict_count",
        "broker_execution_cross_lifecycle_identity_conflict_count",
        "broker_execution_unreconciled_order_count",
        "legacy_unattested_receive_clock_recovery_count",
        "historical_fill_before_submit_diagnostic_recovery_count",
        "historical_legacy_exit_submission_diagnostic_recovery_count",
    ):
        if _native_nonnegative_int(row.get(field)) != 0:
            findings.append(f"row_zero_census_invalid:{field}")
    for field in (
        "historical_fill_before_submit_diagnostic_recovery_provenance",
        "historical_legacy_exit_submission_diagnostic_recovery_provenance",
    ):
        if row.get(field) != []:
            findings.append(f"row_historical_diagnostic_provenance_present:{field}")

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

    custody_count = _native_nonnegative_int(
        row.get("broker_submission_custody_order_count")
    )
    custody_pending_count = _native_nonnegative_int(
        row.get("broker_submission_custody_pending_order_count")
    )
    raw_custody_by_order = row.get("broker_submission_custody_by_order_no")
    if (
        custody_count is None
        or custody_pending_count != 0
        or not isinstance(raw_custody_by_order, Mapping)
        or custody_count != len(raw_custody_by_order)
    ):
        findings.append("row_submission_custody_census_invalid")
    elif submitted_by_order is not None:
        for raw_order_no, raw_binding in raw_custody_by_order.items():
            order_no = str(raw_order_no or "")
            if not isinstance(raw_binding, Mapping):
                findings.append("row_submission_custody_binding_invalid")
                continue
            order_qty = _native_nonnegative_int(raw_binding.get("broker_order_qty"))
            cumulative_qty = _native_nonnegative_int(
                raw_binding.get("broker_cumulative_qty")
            )
            remaining_qty = _native_nonnegative_int(
                raw_binding.get("broker_remaining_qty")
            )
            unit_qty = _native_nonnegative_int(raw_binding.get("broker_unit_qty"))
            execution_no = str(raw_binding.get("broker_execution_no") or "")
            try:
                causal_upper_bound_at = datetime.fromisoformat(
                    str(raw_binding.get("causal_upper_bound_at") or "")
                )
            except ValueError:
                causal_upper_bound_at = None
            if (
                raw_binding.get("binding_schema")
                != "broker_execution_inferred_submission_binding_v1"
                or raw_binding.get("causal_upper_bound_source")
                != BROKER_EXECUTION_OCCURRENCE_TIME_SOURCE
                or raw_binding.get("ordering_clock") != "broker_execution_received_at"
                or raw_binding.get("submission_time_source")
                != BROKER_EXECUTION_RECEIVE_TIME_SOURCE
                or order_no not in submitted_by_order
                or order_qty is None
                or order_qty <= 0
                or order_qty != submitted_by_order.get(order_no)
                or cumulative_qty is None
                or cumulative_qty <= 0
                or remaining_qty is None
                or unit_qty is None
                or unit_qty <= 0
                or cumulative_qty + remaining_qty != order_qty
                or unit_qty > cumulative_qty
                or not execution_no
                or len(execution_no) > 128
                or any(char in execution_no for char in "\r\n\x00")
                or causal_upper_bound_at is None
                or causal_upper_bound_at.tzinfo is None
                or causal_upper_bound_at.microsecond != 0
            ):
                findings.append("row_submission_custody_binding_invalid")

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
    *,
    contract_invalid_trace_keys_out: set[tuple[str, str]] | None = None,
    contract_invalid_report_dates_out: set[str] | None = None,
) -> tuple[dict[tuple[str, str], dict[str, Any]], list[str]]:
    index: dict[tuple[str, str], dict[str, Any]] = {}
    ambiguous_keys: set[tuple[str, str]] = set()
    raw_trace_row_hashes: dict[tuple[str, str], str] = {}
    findings: list[str] = []
    finding_overflow_count = 0
    finding_overflow_scope_counts: Counter[str] = Counter()
    current_activation_day = date.fromisoformat(CURRENT_DESIGN_ACTIVATION_DATE)
    invalid_trace_keys = (
        contract_invalid_trace_keys_out
        if contract_invalid_trace_keys_out is not None
        else set()
    )
    invalid_report_dates = (
        contract_invalid_report_dates_out
        if contract_invalid_report_dates_out is not None
        else set()
    )

    def retain(*values: str) -> None:
        nonlocal finding_overflow_count
        for value in values:
            if len(findings) < MAX_LIFECYCLE_FINDINGS - 1:
                findings.append(value)
            else:
                finding_overflow_count += 1
                finding_dates = re.findall(r"\d{4}-\d{2}-\d{2}", value)
                parsed_dates: list[date] = []
                try:
                    parsed_dates = [
                        date.fromisoformat(finding_date)
                        for finding_date in finding_dates
                    ]
                except ValueError:
                    parsed_dates = []
                if not parsed_dates:
                    scope = "undated"
                elif any(
                    finding_date >= current_activation_day
                    for finding_date in parsed_dates
                ):
                    scope = "current_design"
                else:
                    scope = "pre_current_design"
                finding_overflow_scope_counts[scope] += 1

    for report in lifecycle_reports:
        target_date = str(report.get("target_date") or "")
        rows = report.get("rows")
        if report.get("schema") != LIFECYCLE_REPORT_SCHEMA:
            retain(f"lifecycle_report_schema_invalid:{target_date or 'missing'}")
            if target_date:
                invalid_report_dates.add(target_date)
            continue
        if not target_date or not isinstance(rows, list):
            retain(f"lifecycle_report_shape_invalid:{target_date or 'missing'}")
            if target_date:
                invalid_report_dates.add(target_date)
            continue
        if not _lifecycle_report_hash_valid(report):
            retain(f"lifecycle_report_hash_invalid:{target_date}")
            invalid_report_dates.add(target_date)
            continue
        report_findings = _lifecycle_report_contract_findings(report, rows=rows)
        if report_findings:
            retain(
                *(
                    f"lifecycle_report_contract_invalid:{target_date}:{reason}"
                    for reason in report_findings
                )
            )
            invalid_report_dates.add(target_date)
            continue
        trace_owner: dict[str, str] = {}
        trace_row_hash: dict[str, str] = {}
        report_ambiguous_traces: set[str] = set()
        for raw_row in rows:
            if not isinstance(raw_row, Mapping):
                continue
            if raw_row.get("lifecycle_population_scope") != (
                LIFECYCLE_POPULATION_REAL_SUBMITTED
            ):
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
                row_hash = _sha256(raw_row)
                previous_row_hash = trace_row_hash.setdefault(trace_id, row_hash)
                if trace_id and previous_row_hash != row_hash:
                    report_ambiguous_traces.add(trace_id)
                global_key = (target_date, trace_id)
                previous_global_hash = raw_trace_row_hashes.setdefault(
                    global_key, row_hash
                )
                if trace_id and previous_global_hash != row_hash:
                    report_ambiguous_traces.add(trace_id)
        for trace_id in sorted(report_ambiguous_traces):
            key = (target_date, trace_id)
            index.pop(key, None)
            if key not in ambiguous_keys:
                retain(f"lifecycle_trace_identity_ambiguous:{target_date}:{trace_id}")
            ambiguous_keys.add(key)
            invalid_trace_keys.add(key)
        for row in rows:
            assert isinstance(row, Mapping)
            if row.get("lifecycle_population_scope") == (
                LIFECYCLE_POPULATION_CANDIDATE_OBSERVATION
            ):
                # Candidate observations are retained in the daily census and
                # exclusion manifest, but they are not broker lifecycles and
                # cannot become exact R2 joins or invalidate unrelated real
                # lifecycle trace keys.
                continue
            raw_trace_ids = row.get("decision_trace_ids")
            if isinstance(raw_trace_ids, list) and any(
                (target_date, str(trace_id or "")) in ambiguous_keys
                for trace_id in raw_trace_ids
            ):
                continue
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
                invalid_row_trace_ids = row.get("decision_trace_ids")
                if not isinstance(invalid_row_trace_ids, list):
                    single_trace_id = row.get("decision_trace_id")
                    invalid_row_trace_ids = (
                        [single_trace_id]
                        if isinstance(single_trace_id, str) and single_trace_id
                        else []
                    )
                native_trace_ids = [
                    trace_id
                    for trace_id in invalid_row_trace_ids
                    if isinstance(trace_id, str) and trace_id
                ]
                if len(native_trace_ids) != len(invalid_row_trace_ids) or not (
                    native_trace_ids
                ):
                    invalid_report_dates.add(target_date)
                else:
                    invalid_trace_keys.update(
                        (target_date, trace_id) for trace_id in native_trace_ids
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
                    invalid_trace_keys.add(key)
                    continue
                index[key] = dict(row)
    if finding_overflow_count:
        findings.append(
            "lifecycle_findings_truncated:"
            + ",".join(
                f"{scope}={finding_overflow_scope_counts.get(scope, 0)}"
                for scope in ("pre_current_design", "current_design", "undated")
            )
        )
    return index, findings


def _lifecycle_gate_findings(row: Mapping[str, Any] | None) -> list[str]:
    if not isinstance(row, Mapping):
        return ["lifecycle_exact_join_missing"]
    findings: list[str] = []
    if row.get("promotion_evidence_eligible") is not True:
        findings.append("lifecycle_promotion_evidence_not_eligible")
    for field in (
        "historical_fill_before_submit_diagnostic_recovery_count",
        "historical_legacy_exit_submission_diagnostic_recovery_count",
    ):
        if _native_nonnegative_int(row.get(field)) != 0:
            findings.append(f"lifecycle_historical_diagnostic_recovery:{field}")
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


_DECISION_STAGE_LIFECYCLE_STAGE = {
    "entry": "entry_decision",
    "holding": "holding",
    "exit": "exit",
}

_SCALE_IN_SOURCE_EVENT_STAGES = frozenset(
    {
        "first_touch_avgdown_submit_authority_retry",
        "scale_in_submit_authority_retry",
    }
)
_SCALE_IN_SOURCE_EVENT_STAGE_PREFIXES = (
    "first_touch_avgdown_",
    "scale_in_",
)


def _execution_lifecycle_stage(execution_row: Mapping[str, Any]) -> str | None:
    """Resolve the exact lifecycle owner behind a provider-normalized stage."""

    decision_stage = str(execution_row.get("decision_stage") or "").strip().lower()
    raw_source_event_stage = execution_row.get("source_event_stage")
    if raw_source_event_stage is None:
        source_event_stage = ""
    elif (
        not isinstance(raw_source_event_stage, str)
        or not raw_source_event_stage
        or raw_source_event_stage != raw_source_event_stage.strip()
    ):
        return None
    else:
        source_event_stage = raw_source_event_stage
    if source_event_stage in _SCALE_IN_SOURCE_EVENT_STAGES:
        return "scale_in" if decision_stage == "holding" else None
    if source_event_stage.lower().startswith(_SCALE_IN_SOURCE_EVENT_STAGE_PREFIXES):
        # A newly introduced scale-in producer must be deliberately added to
        # the exact allowlist above.  Treating an unknown retry as ordinary
        # holding could silently join it to the wrong mutable context.
        return None
    return _DECISION_STAGE_LIFECYCLE_STAGE.get(decision_stage)


def _lifecycle_trace_context_findings(
    lifecycle: Mapping[str, Any], execution_row: Mapping[str, Any]
) -> list[str]:
    """Bind one replay decision to its exact mutable lifecycle context."""

    trace_id = str(execution_row.get("decision_trace_id") or "").strip()
    lifecycle_stage = _execution_lifecycle_stage(execution_row)
    if not trace_id or lifecycle_stage is None:
        return ["daily_lifecycle_trace_context_stage_invalid"]
    raw_path = lifecycle.get("decision_trace_context_path")
    if not isinstance(raw_path, list):
        return ["daily_lifecycle_trace_context_missing"]
    matches = [
        context
        for context in raw_path
        if isinstance(context, Mapping)
        and str(context.get("decision_trace_id") or "").strip() == trace_id
        and str(context.get("stage") or "").strip().lower() == lifecycle_stage
    ]
    if not matches:
        return ["daily_lifecycle_trace_context_missing"]
    if len(matches) != 1:
        return ["daily_lifecycle_trace_context_ambiguous"]
    context = matches[0]
    expected_venue = str(context.get("venue") or "").strip().upper()
    expected_session = quality._session(context.get("session_bucket"))
    if (
        not expected_venue
        or not expected_session
        or not str(context.get("venue_source") or "").strip()
        or not str(context.get("session_bucket_source") or "").strip()
        or _native_nonnegative_int(context.get("transition_count")) in {None, 0}
    ):
        return ["daily_lifecycle_trace_context_invalid"]
    if (
        str(execution_row.get("effective_venue") or "").strip().upper()
        != expected_venue
        or quality._session(execution_row.get("session_bucket")) != expected_session
    ):
        return ["daily_lifecycle_trace_context_mismatch"]
    return []


def _date_or_none(value: Any) -> date | None:
    try:
        return date.fromisoformat(str(value or ""))
    except ValueError:
        return None


def _date_window_rows(
    rows: Sequence[dict[str, Any]], *, target_date: str, trading_days: int
) -> tuple[list[dict[str, Any]], list[str]]:
    target = date.fromisoformat(target_date)
    dates = sorted(
        {
            candidate.isoformat()
            for row in rows
            for candidate in [_date_or_none(row.get("target_date"))]
            if candidate is not None
            and candidate <= target
            and is_krx_trading_day(candidate)
        }
    )
    selected_dates = dates[-trading_days:]
    return (
        [row for row in rows if row.get("target_date") in selected_dates],
        selected_dates,
    )


def _lifecycle_promotion_estimator(
    rows: Sequence[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Choose one causal promotion-economics row per exact lifecycle.

    Decision-level EV diagnostics intentionally remain outside this estimator.
    Representative selection uses only decision-time outputs and stable
    identities; outcome EV, notional profit, holding duration, and other future
    lifecycle metrics never participate in the ordering.
    """

    cluster_rows: dict[tuple[str, str, str], list[tuple[dict[str, Any], str, bool]]] = (
        defaultdict(list)
    )
    lifecycle_rows: dict[tuple[str, str], list[tuple[dict[str, Any], str, bool]]] = (
        defaultdict(list)
    )
    lifecycle_census: dict[tuple[str, str], dict[str, str]] = {}
    decision_identities: set[tuple[str, str]] = set()
    for row in rows:
        lifecycle = row.get("lifecycle")
        target_date = str(row.get("target_date") or "")
        target_day = _date_or_none(target_date)
        lifecycle_id = str(row.get("main_lifecycle_id") or "").strip()
        lifecycle_stage = str(row.get("lifecycle_stage") or "").strip().lower()
        parent_id = str(row.get("paired_replay_parent_id") or "").strip()
        trace_id = str(row.get("decision_trace_id") or "").strip()
        stock_code = str(row.get("stock_code") or "").strip()
        decision_at = _aware_artifact_datetime(row.get("decision_ts"))
        expected_stage = _execution_lifecycle_stage(row)
        control_action = str(row.get("control_action") or "").strip().upper()
        candidate_action = str(row.get("candidate_action") or "").strip().upper()
        control_signal = row.get("control_signal_selected")
        candidate_signal = row.get("candidate_signal_selected")
        lifecycle_sha256 = _sha256(lifecycle) if isinstance(lifecycle, Mapping) else ""
        if (
            not isinstance(lifecycle, Mapping)
            or target_day is None
            or decision_at is None
            or decision_at.date() != target_day
            or not re.fullmatch(r"mlc-[0-9a-f]{32}", lifecycle_id)
            or lifecycle_id != str(lifecycle.get("main_lifecycle_id") or "")
            or lifecycle_stage not in {"entry_decision", "holding", "scale_in", "exit"}
            or lifecycle_stage != expected_stage
            or lifecycle.get("trade_date") != target_date
            or lifecycle.get("stock_code") != stock_code
            or row.get("lifecycle_source_row_sha256") != lifecycle_sha256
            or not parent_id
            or not trace_id
            or not control_action
            or not candidate_action
            or not isinstance(control_signal, bool)
            or not isinstance(candidate_signal, bool)
        ):
            raise ValueError("rolling_lifecycle_promotion_estimator_binding_invalid")
        decision_identity = (target_date, parent_id)
        if decision_identity in decision_identities:
            raise ValueError("rolling_lifecycle_promotion_decision_identity_duplicate")
        decision_identities.add(decision_identity)

        lifecycle_key = (target_date, lifecycle_id)
        lifecycle_identity = {
            "target_date": target_date,
            "main_lifecycle_id": lifecycle_id,
            "stock_code": stock_code,
            "lifecycle_source_row_sha256": lifecycle_sha256,
        }
        previous_lifecycle_identity = lifecycle_census.setdefault(
            lifecycle_key, lifecycle_identity
        )
        if previous_lifecycle_identity != lifecycle_identity:
            raise ValueError("rolling_lifecycle_promotion_identity_cluster_conflict")

        decision_divergence = bool(
            control_action != candidate_action or control_signal != candidate_signal
        )
        cluster_rows[(target_date, lifecycle_id, lifecycle_stage)].append(
            (row, decision_at.isoformat(), decision_divergence)
        )
        lifecycle_rows[(target_date, lifecycle_id)].append(
            (row, decision_at.isoformat(), decision_divergence)
        )

    cluster_census: list[dict[str, Any]] = []
    for cluster_key in sorted(cluster_rows):
        ordered = sorted(
            cluster_rows[cluster_key],
            key=lambda item: (
                item[1],
                str(item[0].get("decision_trace_id") or ""),
                str(item[0].get("paired_replay_parent_id") or ""),
            ),
        )
        decision_parent_census = [
            {
                "decision_ts": decision_ts,
                "decision_trace_id": str(row.get("decision_trace_id") or ""),
                "paired_replay_parent_id": str(
                    row.get("paired_replay_parent_id") or ""
                ),
                "decision_divergence": decision_divergence,
            }
            for row, decision_ts, decision_divergence in ordered
        ]
        cluster_census.append(
            {
                "target_date": cluster_key[0],
                "main_lifecycle_id": cluster_key[1],
                "lifecycle_stage": cluster_key[2],
                "lifecycle_source_row_sha256": lifecycle_census[
                    (cluster_key[0], cluster_key[1])
                ]["lifecycle_source_row_sha256"],
                "decision_parent_count": len(ordered),
                "decision_parent_census_sha256": _sha256(decision_parent_census),
            }
        )

    representatives: list[dict[str, Any]] = []
    selected_parent_census: list[dict[str, Any]] = []
    no_divergence_lifecycle_count = 0
    for lifecycle_key in sorted(lifecycle_rows):
        ordered = sorted(
            lifecycle_rows[lifecycle_key],
            key=lambda item: (
                item[1],
                str(item[0].get("decision_trace_id") or ""),
                str(item[0].get("paired_replay_parent_id") or ""),
            ),
        )
        divergent = [item for item in ordered if item[2]]
        if divergent:
            selected_row, selected_ts, _ = divergent[0]
            selection_reason = "earliest_decision_divergence_across_lifecycle"
            representatives.append(selected_row)
            selected_parent = {
                "target_date": lifecycle_key[0],
                "main_lifecycle_id": lifecycle_key[1],
                "lifecycle_stage": str(selected_row.get("lifecycle_stage") or ""),
                "decision_ts": selected_ts,
                "decision_trace_id": str(selected_row.get("decision_trace_id") or ""),
                "paired_replay_parent_id": str(
                    selected_row.get("paired_replay_parent_id") or ""
                ),
                "selection_reason": selection_reason,
            }
        else:
            no_divergence_lifecycle_count += 1
            selected_parent = {
                "target_date": lifecycle_key[0],
                "main_lifecycle_id": lifecycle_key[1],
                "lifecycle_stage": None,
                "decision_ts": None,
                "decision_trace_id": None,
                "paired_replay_parent_id": None,
                "selection_reason": "no_decision_divergence_censored",
            }
        selected_parent_census.append(selected_parent)

    unique_lifecycle_census = [
        lifecycle_census[key] for key in sorted(lifecycle_census)
    ]
    promotion_economics_input_census = sorted(
        (
            {
                "target_date": str(row.get("target_date") or ""),
                "main_lifecycle_id": str(row.get("main_lifecycle_id") or ""),
                "lifecycle_stage": str(row.get("lifecycle_stage") or ""),
                "lifecycle_source_row_sha256": str(
                    row.get("lifecycle_source_row_sha256") or ""
                ),
                "decision_ts": decision_ts,
                "decision_trace_id": str(row.get("decision_trace_id") or ""),
                "paired_replay_parent_id": str(
                    row.get("paired_replay_parent_id") or ""
                ),
                "decision_divergence": decision_divergence,
                "candidate_notional_value_krw": _finite_number(
                    row.get("candidate_notional_value_krw")
                ),
            }
            for lifecycle_parent_rows in lifecycle_rows.values()
            for row, decision_ts, decision_divergence in lifecycle_parent_rows
        ),
        key=lambda item: (
            item["target_date"],
            item["main_lifecycle_id"],
            item["decision_ts"],
            item["decision_trace_id"],
            item["paired_replay_parent_id"],
        ),
    )
    contract_sha256 = _sha256(LIFECYCLE_PROMOTION_ESTIMATOR_CONTRACT)
    return representatives, {
        "lifecycle_promotion_estimator_id": LIFECYCLE_PROMOTION_ESTIMATOR_ID,
        "lifecycle_promotion_estimator_contract_sha256": contract_sha256,
        "decision_level_parent_count": len(rows),
        "unique_lifecycle_count": len(unique_lifecycle_census),
        "unique_lifecycle_census_sha256": _sha256(unique_lifecycle_census),
        "promotion_economics_input_census_sha256": _sha256(
            promotion_economics_input_census
        ),
        "unique_lifecycle_stage_cluster_count": len(cluster_census),
        "lifecycle_stage_cluster_census_sha256": _sha256(cluster_census),
        "lifecycle_promotion_estimated_parent_count": len(representatives),
        "lifecycle_promotion_censored_parent_count": len(rows) - len(representatives),
        "lifecycle_no_divergence_count": no_divergence_lifecycle_count,
        "lifecycle_selected_parent_census_sha256": _sha256(selected_parent_census),
    }


def _window_metrics(
    rows: Sequence[dict[str, Any]], *, target_date: str, trading_days: int
) -> dict[str, Any]:
    selected, selected_dates = _date_window_rows(
        rows, target_date=target_date, trading_days=trading_days
    )
    promotion_rows, promotion_census = _lifecycle_promotion_estimator(selected)
    candidate_evs = [float(row["candidate_ev_pct"]) for row in selected]
    control_evs = [float(row["control_ev_pct"]) for row in selected]
    deltas = [float(row["paired_ev_delta_pct"]) for row in selected]
    decision_level_candidate_notional = [
        float(value)
        for row in selected
        if (value := row.get("candidate_notional_value_krw")) is not None
    ]
    candidate_notional = [
        float(value)
        for row in promotion_rows
        if (value := row.get("candidate_notional_value_krw")) is not None
    ]
    session_exposure_sec = sum(
        float((row.get("lifecycle") or {}).get("session_exposure_sec") or 0.0)
        for row in promotion_rows
    )
    capital_hours = sum(
        float((row.get("lifecycle") or {}).get("capital_time_krw_hours") or 0.0)
        for row in promotion_rows
    )
    candidate_signal_count = sum(
        row.get("candidate_signal_selected") is True for row in promotion_rows
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
    metrics = {
        "window_trading_days": trading_days,
        "observed_trading_days": len(selected_dates),
        "selected_dates": selected_dates,
        "common_parent_count": len(selected),
        **promotion_census,
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
        "decision_level_candidate_notional_eligible_count": len(
            decision_level_candidate_notional
        ),
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
                for row in promotion_rows
            )
            if promotion_rows
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
                for row in promotion_rows
            )
            if promotion_rows
            else None
        ),
        "depth_coverage_pct": (
            fmean(
                float((row.get("lifecycle") or {})["depth_coverage_pct"])
                for row in promotion_rows
            )
            if promotion_rows
            else None
        ),
        "invalid_transition_count": sum(
            int((row.get("lifecycle") or {}).get("invalid_transition_count") or 0)
            for row in promotion_rows
        ),
    }
    design_versions = {
        str(row.get("ablation_design_version") or LEGACY_DESIGN_VERSION) for row in rows
    }
    if design_versions == {CURRENT_DESIGN_VERSION}:
        baseline_evs = [
            value
            for row in selected
            if (value := _finite_number(row.get("baseline_ev_pct"))) is not None
        ]
        feature_deltas = [
            float(row["control_ev_pct"]) - float(row["baseline_ev_pct"])
            for row in selected
            if _finite_number(row.get("baseline_ev_pct")) is not None
        ]
        composite_deltas = [
            float(row["candidate_ev_pct"]) - float(row["baseline_ev_pct"])
            for row in selected
            if _finite_number(row.get("baseline_ev_pct")) is not None
        ]
        composite_relative_uplifts = [
            delta / max(abs(baseline), 0.01) * 100.0
            for delta, baseline in zip(composite_deltas, baseline_evs)
        ]
        metrics.update(
            {
                "ablation_design_version": CURRENT_DESIGN_VERSION,
                "baseline_metric_parent_count": len(baseline_evs),
                "baseline_source_quality_adjusted_ev_pct": (
                    fmean(baseline_evs) if baseline_evs else None
                ),
                "feature_ev_delta_pct": (
                    fmean(feature_deltas) if feature_deltas else None
                ),
                "composite_ev_delta_pct": (
                    fmean(composite_deltas) if composite_deltas else None
                ),
                "composite_relative_uplift_pct": (
                    fmean(composite_relative_uplifts)
                    if composite_relative_uplifts
                    else None
                ),
                "baseline_p10_ev_pct": _percentile(baseline_evs, 0.10),
                "baseline_severe_tail_count": sum(
                    row.get("baseline_severe_tail") is True for row in selected
                ),
                "baseline_deferred_count": sum(
                    str(row.get("baseline_action") or "") in {"WAIT", "HOLD"}
                    for row in selected
                ),
            }
        )
    return metrics


def _window_gate_findings(metrics: Mapping[str, Any]) -> list[str]:
    findings: list[str] = []
    expected_days = int(metrics.get("window_trading_days") or 0)
    common_parent_count = _native_nonnegative_int(metrics.get("common_parent_count"))
    decision_level_parent_count = _native_nonnegative_int(
        metrics.get("decision_level_parent_count")
    )
    unique_lifecycle_count = _native_nonnegative_int(
        metrics.get("unique_lifecycle_count")
    )
    lifecycle_stage_cluster_count = _native_nonnegative_int(
        metrics.get("unique_lifecycle_stage_cluster_count")
    )
    estimated_parent_count = _native_nonnegative_int(
        metrics.get("lifecycle_promotion_estimated_parent_count")
    )
    censored_parent_count = _native_nonnegative_int(
        metrics.get("lifecycle_promotion_censored_parent_count")
    )
    no_divergence_lifecycle_count = _native_nonnegative_int(
        metrics.get("lifecycle_no_divergence_count")
    )
    if (
        metrics.get("lifecycle_promotion_estimator_id")
        != LIFECYCLE_PROMOTION_ESTIMATOR_ID
        or metrics.get("lifecycle_promotion_estimator_contract_sha256")
        != _sha256(LIFECYCLE_PROMOTION_ESTIMATOR_CONTRACT)
        or any(
            not _valid_sha256(metrics.get(field))
            for field in (
                "unique_lifecycle_census_sha256",
                "promotion_economics_input_census_sha256",
                "lifecycle_stage_cluster_census_sha256",
                "lifecycle_selected_parent_census_sha256",
            )
        )
        or common_parent_count is None
        or decision_level_parent_count != common_parent_count
        or unique_lifecycle_count is None
        or lifecycle_stage_cluster_count is None
        or estimated_parent_count is None
        or censored_parent_count is None
        or no_divergence_lifecycle_count is None
        or unique_lifecycle_count > lifecycle_stage_cluster_count
        or unique_lifecycle_count
        != estimated_parent_count + no_divergence_lifecycle_count
        or lifecycle_stage_cluster_count < estimated_parent_count
        or estimated_parent_count > decision_level_parent_count
        or censored_parent_count != decision_level_parent_count - estimated_parent_count
        or int(metrics.get("candidate_notional_eligible_count") or 0)
        > estimated_parent_count
    ):
        findings.append("lifecycle_promotion_estimator_census_invalid")
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
    if metrics.get("ablation_design_version") == CURRENT_DESIGN_VERSION:
        baseline_parent_count = _native_nonnegative_int(
            metrics.get("baseline_metric_parent_count")
        )
        common_parent_count = _native_nonnegative_int(
            metrics.get("common_parent_count")
        )
        if (
            baseline_parent_count is None
            or common_parent_count is None
            or baseline_parent_count != common_parent_count
        ):
            findings.append("current_baseline_metric_census_invalid")
        feature_ev_delta = _finite_number(metrics.get("feature_ev_delta_pct"))
        if feature_ev_delta is None or feature_ev_delta < 0:
            findings.append("feature_ev_noninferiority_failed")
        composite_ev_delta = _finite_number(metrics.get("composite_ev_delta_pct"))
        if composite_ev_delta is None or composite_ev_delta <= 0:
            findings.append("composite_ev_delta_not_positive")
        composite_relative_uplift = _finite_number(
            metrics.get("composite_relative_uplift_pct")
        )
        if (
            composite_relative_uplift is None
            or composite_relative_uplift < MIN_RELATIVE_UPLIFT_PCT
        ):
            findings.append("composite_relative_uplift_below_floor")
        baseline_p10 = _finite_number(metrics.get("baseline_p10_ev_pct"))
        if (
            baseline_p10 is None
            or candidate_p10 is None
            or candidate_p10 < baseline_p10
        ):
            findings.append("composite_p10_worsened_or_missing")
        if int(metrics.get("candidate_severe_tail_count") or 0) > int(
            metrics.get("baseline_severe_tail_count") or 0
        ):
            findings.append("composite_severe_tail_worsened")
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


def _confirmation_window_tuning_census(
    rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    direction_counts: dict[str, Counter[str]] = defaultdict(Counter)
    classification_eligible_counts: Counter[str] = Counter()
    tuning_outcome_eligible_counts: Counter[str] = Counter()
    net_returns_bps: dict[str, list[float]] = defaultdict(list)
    net_mfe_bps: dict[str, list[float]] = defaultdict(list)
    net_mae_bps: dict[str, list[float]] = defaultdict(list)
    confirmation_delays_ms: dict[str, list[float]] = defaultdict(list)
    entry_deadline_lags_ms: dict[str, list[float]] = defaultdict(list)
    missing_axis_count = 0
    for row in rows:
        axis = row.get("confirmation_window_axis")
        if not isinstance(axis, Mapping):
            missing_axis_count += 1
            continue
        _validate_confirmation_window_axis(axis)
        for observation in axis.get("observations") or []:
            horizon = str(observation.get("horizon_sec") or "unknown")
            direction_counts[horizon][
                str(observation.get("direction_state") or "unknown")
            ] += 1
            if observation.get("classification_eligible") is True:
                classification_eligible_counts[horizon] += 1
            for fixed_outcome in observation.get("fixed_followthrough_outcomes") or []:
                if fixed_outcome.get("tuning_outcome_eligible") is not True:
                    continue
                followthrough = str(fixed_outcome.get("followthrough_sec") or "unknown")
                policy_key = f"confirm_{horizon}s_follow_{followthrough}s"
                tuning_outcome_eligible_counts[policy_key] += 1
                for field, target in (
                    ("standardized_one_share_net_return_bps", net_returns_bps),
                    ("standardized_one_share_net_mfe_bps", net_mfe_bps),
                    ("standardized_one_share_net_mae_bps", net_mae_bps),
                    ("entry_delay_from_confirmation_ms", entry_deadline_lags_ms),
                ):
                    value = _finite_number(fixed_outcome.get(field))
                    if value is not None:
                        target[policy_key].append(value)
                active_delay = _finite_number(
                    observation.get("active_confirmation_delay_ms")
                )
                if active_delay is not None:
                    confirmation_delays_ms[policy_key].append(active_delay)
    observed_policies = sorted(
        set(tuning_outcome_eligible_counts) | set(net_returns_bps),
        key=lambda value: tuple(int(part) for part in re.findall(r"\d+", value)),
    )
    outcome_metrics = {}
    for policy_key in observed_policies:
        returns = net_returns_bps[policy_key]
        mfes = net_mfe_bps[policy_key]
        maes = net_mae_bps[policy_key]
        delays = confirmation_delays_ms[policy_key]
        deadline_lags = entry_deadline_lags_ms[policy_key]
        outcome_metrics[policy_key] = {
            "sample_count": len(returns),
            "equal_weight_avg_profit_pct": (
                None if not returns else round(fmean(returns) / 100.0, 6)
            ),
            "diagnostic_win_rate_pct": (
                None
                if not returns
                else round(
                    sum(value > 0 for value in returns) / len(returns) * 100.0,
                    6,
                )
            ),
            "mean_standardized_one_share_net_mfe_pct": (
                None if not mfes else round(fmean(mfes) / 100.0, 6)
            ),
            "mean_standardized_one_share_net_mae_pct": (
                None if not maes else round(fmean(maes) / 100.0, 6)
            ),
            "median_active_confirmation_delay_ms": (
                None if not delays else round(median(delays), 3)
            ),
            "median_entry_deadline_lag_ms": (
                None if not deadline_lags else round(median(deadline_lags), 3)
            ),
        }
    return {
        **CONFIRMATION_WINDOW_METRIC_CONTRACT,
        "direction_counts": {
            horizon: dict(counts)
            for horizon, counts in sorted(
                direction_counts.items(),
                key=lambda item: int(item[0]) if item[0].isdigit() else math.inf,
            )
        },
        "classification_eligible_counts": dict(
            sorted(
                classification_eligible_counts.items(),
                key=lambda item: int(item[0]) if item[0].isdigit() else math.inf,
            )
        ),
        "tuning_outcome_eligible_counts": dict(
            sorted(tuning_outcome_eligible_counts.items())
        ),
        "outcome_metrics": outcome_metrics,
        "missing_legacy_axis_count": missing_axis_count,
        "policy_ev_evaluation_status": (
            "standardized_one_share_source_only_outcome_observed"
            if sum(tuning_outcome_eligible_counts.values()) > 0
            else "awaiting_eligible_post_confirmation_outcomes"
        ),
        "selection_authority": False,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def _validate_exact_offline_authority(value: Mapping[str, Any], *, label: str) -> None:
    if value.get("decision_authority") != OFFLINE_AUTHORITY["decision_authority"]:
        raise ValueError(f"{label}_decision_authority_invalid")
    for field, expected in SOURCE_ONLY_AUTHORITY_CONTRACT.items():
        if value.get(field) is not expected:
            raise ValueError(f"{label}_source_only_authority_invalid:{field}")
    for field in SOURCE_ONLY_FALSE_AUTHORITY_ALIASES:
        if field in value and value.get(field) is not False:
            raise ValueError(f"{label}_authority_alias_invalid:{field}")


def _r3_evidence_contract(design_version: str) -> dict[str, Any]:
    contract: dict[str, Any] = {
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
        "lifecycle_promotion_estimator_id": LIFECYCLE_PROMOTION_ESTIMATOR_ID,
        "lifecycle_promotion_estimator_contract_sha256": _sha256(
            LIFECYCLE_PROMOTION_ESTIMATOR_CONTRACT
        ),
        "requires_at_most_one_promotion_economics_row_per_lifecycle": True,
        "requires_no_divergence_lifecycle_censor": True,
    }
    if design_version == CURRENT_DESIGN_VERSION:
        contract.update(
            {
                "requires_ask_depletion_feature_ev_noninferiority_against_current_micro": True,
                "requires_composite_ev_improvement_against_current_micro": True,
                "requires_composite_nonworse_p10_and_severe_tail_against_current_micro": True,
            }
        )
    return contract


def _validated_r2_partition_candidate_state(
    partition: Mapping[str, Any],
    *,
    target_date: str,
    global_candidate_blockers: Sequence[str],
) -> bool:
    """Rebuild one partition's promotion gate from its persisted R2 metrics."""

    if not isinstance(partition, Mapping):
        raise ValueError("r2_partition_not_object")
    windows = partition.get("windows")
    if not isinstance(windows, Mapping) or set(windows) != {"5", "10", "20"}:
        raise ValueError("r2_partition_window_contract_invalid")
    expected_findings: dict[str, list[str]] = {}
    for window in ("5", "10", "20"):
        metrics = windows.get(window)
        if not isinstance(metrics, Mapping):
            raise ValueError(f"r2_partition_window_not_object:{window}")
        if _native_nonnegative_int(metrics.get("window_trading_days")) != int(window):
            raise ValueError(f"r2_partition_window_identity_invalid:{window}")
        expected_findings[window] = _window_gate_findings(metrics)

    try:
        target_day = date.fromisoformat(target_date)
    except ValueError as exc:
        raise ValueError("r2_partition_target_date_invalid") from exc
    design_version = str(partition.get("ablation_design_version") or "")
    if design_version not in {LEGACY_DESIGN_VERSION, CURRENT_DESIGN_VERSION}:
        raise ValueError("r2_partition_ablation_design_invalid")
    for window in ("5", "10", "20"):
        window_design = windows[window].get("ablation_design_version")
        if design_version == CURRENT_DESIGN_VERSION:
            if window_design != CURRENT_DESIGN_VERSION:
                raise ValueError(
                    f"r2_partition_window_ablation_design_mismatch:{window}"
                )
        elif window_design not in (None, LEGACY_DESIGN_VERSION):
            raise ValueError(f"r2_partition_window_ablation_design_mismatch:{window}")
    source_dates = partition.get("source_dates")
    if (
        not isinstance(source_dates, list)
        or any(not isinstance(value, str) or not value for value in source_dates)
        or source_dates != sorted(set(source_dates))
    ):
        raise ValueError("r2_partition_source_date_census_invalid")
    parsed_source_dates: list[date] = []
    for value in source_dates:
        try:
            parsed_source_dates.append(date.fromisoformat(value))
        except ValueError as exc:
            raise ValueError("r2_partition_source_date_invalid") from exc
    if any(
        value > target_day or value < CLEAN_BASELINE_DATE
        for value in parsed_source_dates
    ):
        raise ValueError("r2_partition_source_date_scope_invalid")
    if target_day >= date.fromisoformat(CURRENT_DESIGN_ACTIVATION_DATE):
        if design_version != CURRENT_DESIGN_VERSION:
            expected_findings["activation_design"] = [
                "post_activation_r3_requires_current_ablation_design"
            ]
        if any(
            value < date.fromisoformat(CURRENT_DESIGN_ACTIVATION_DATE)
            for value in parsed_source_dates
        ):
            expected_findings["activation_window"] = [
                "current_r3_evidence_requires_post_activation_source_dates"
            ]
    if global_candidate_blockers:
        expected_findings["global_execution_artifact"] = list(global_candidate_blockers)
    gate_findings = partition.get("gate_findings")
    if isinstance(gate_findings, Mapping) and "identity" in gate_findings:
        identity_findings = gate_findings.get("identity")
        if identity_findings not in (
            ["economic_reference_binding_incomplete"],
            ["latest_symbol_master_artifact_binding_not_unique"],
        ):
            raise ValueError("r2_partition_identity_gate_invalid")
        expected_findings["identity"] = list(identity_findings)
    if (
        not isinstance(gate_findings, Mapping)
        or dict(gate_findings) != expected_findings
    ):
        raise ValueError("r2_partition_gate_findings_semantic_mismatch")
    expected_eligible = not global_candidate_blockers and all(
        not values for values in expected_findings.values()
    )
    if partition.get("r3_source_candidate_eligible") is not expected_eligible:
        raise ValueError("r2_partition_candidate_eligibility_mismatch")
    return expected_eligible


def canonical_r3_candidate_from_r2_partition(
    partition: Mapping[str, Any],
    *,
    provider_ablation_floor_bindings_sha256: str,
) -> dict[str, Any]:
    """Project one already-gated R2 partition into its one canonical R3 row."""

    design_version = str(partition.get("ablation_design_version") or "")
    if design_version not in {LEGACY_DESIGN_VERSION, CURRENT_DESIGN_VERSION}:
        raise ValueError("r2_partition_ablation_design_invalid")
    expected_axis = (
        "prompt_contract_effect_on_ask_depletion_context"
        if design_version == CURRENT_DESIGN_VERSION
        else "prompt_contract_effect"
    )
    required_nonempty = (
        "decision_stage",
        "effective_venue",
        "session_bucket",
        "selected_cost_profile_id",
        "latest_symbol_master_source_date",
    )
    if any(
        not isinstance(partition.get(field), str)
        or not str(partition.get(field) or "").strip()
        for field in required_nonempty
    ):
        raise ValueError("r2_partition_candidate_identity_missing")
    decision_stage = str(partition.get("decision_stage") or "")
    if decision_stage not in SUPPORTED_ECONOMIC_STAGES:
        raise ValueError("r2_partition_candidate_stage_invalid")
    if str(partition.get("effective_venue") or "") not in {"KRX", "NXT"}:
        raise ValueError("r2_partition_candidate_venue_invalid")
    if partition.get("tuning_axis") != expected_axis:
        raise ValueError("r2_partition_candidate_tuning_axis_invalid")
    required_hashes = (
        "control_contract_sha256",
        "candidate_contract_sha256",
        "current_prompt_sha256",
        "recommended_prompt_sha256",
        "selected_cost_profile_content_sha256",
        "economic_reference_bindings_sha256",
        "latest_symbol_master_artifact_sha256",
    )
    if any(not _valid_sha256(partition.get(field)) for field in required_hashes):
        raise ValueError("r2_partition_candidate_hash_binding_invalid")
    if not _valid_sha256(provider_ablation_floor_bindings_sha256):
        raise ValueError("r2_partition_provider_floor_binding_invalid")
    reference_count = _native_nonnegative_int(
        partition.get("economic_reference_binding_count")
    )
    source_row_count = _native_nonnegative_int(partition.get("source_row_count"))
    source_dates = partition.get("source_dates")
    if (
        reference_count is None
        or reference_count < 1
        or source_row_count is None
        or source_row_count < 1
        or reference_count > source_row_count
        or not isinstance(source_dates, list)
        or not source_dates
        or partition.get("latest_symbol_master_source_date") != max(source_dates)
    ):
        raise ValueError("r2_partition_economic_reference_census_invalid")
    try:
        date.fromisoformat(str(partition["latest_symbol_master_source_date"]))
    except ValueError as exc:
        raise ValueError("r2_partition_latest_symbol_master_date_invalid") from exc
    windows = partition.get("windows")
    if not isinstance(windows, Mapping) or set(windows) != {"5", "10", "20"}:
        raise ValueError("r2_partition_candidate_windows_invalid")

    candidate_content = {
        "candidate_family": "main_ai_quality_prompt_contract",
        "ablation_design_version": design_version,
        "decision_stage": partition["decision_stage"],
        "effective_venue": partition["effective_venue"],
        "session_bucket": partition["session_bucket"],
        "tuning_axis": partition["tuning_axis"],
        "current_contract_sha256": partition["control_contract_sha256"],
        "recommended_contract_sha256": partition["candidate_contract_sha256"],
        "current_prompt_sha256": partition["current_prompt_sha256"],
        "recommended_prompt_sha256": partition["recommended_prompt_sha256"],
        "selected_cost_profile_id": partition["selected_cost_profile_id"],
        "selected_cost_profile_content_sha256": partition[
            "selected_cost_profile_content_sha256"
        ],
        "economic_reference_bindings_sha256": partition[
            "economic_reference_bindings_sha256"
        ],
        "economic_reference_binding_count": reference_count,
        "latest_symbol_master_source_date": partition[
            "latest_symbol_master_source_date"
        ],
        "latest_symbol_master_artifact_sha256": partition[
            "latest_symbol_master_artifact_sha256"
        ],
        "rolling_window_sha256": _sha256(windows),
        "provider_ablation_floor_bindings_sha256": (
            provider_ablation_floor_bindings_sha256
        ),
        "evidence_contract": _r3_evidence_contract(design_version),
        "runtime_design_status": "design_required_no_registered_consumer",
        "first_exact_candidate_approval_required": True,
        "continuous_auto_chain_eligible": False,
        "provider_or_order_authority": False,
        **OFFLINE_AUTHORITY,
    }
    candidate_sha256 = _sha256(candidate_content)
    return {
        "candidate_id": f"main-ai-quality-{candidate_sha256[:24]}",
        "candidate_sha256": candidate_sha256,
        **candidate_content,
    }


def project_r3_candidates_from_validated_r2(
    rolling: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Return the exact ordered R3 candidate list implied by one valid R2."""

    target_date = str(rolling.get("target_date") or "")
    global_candidate_blockers = rolling.get("global_candidate_blockers")
    if (
        not isinstance(global_candidate_blockers, list)
        or any(
            not isinstance(value, str) or not value
            for value in global_candidate_blockers
        )
        or global_candidate_blockers != sorted(set(global_candidate_blockers))
    ):
        raise ValueError("r2_global_candidate_blocker_census_invalid")
    partitions = rolling.get("partitions")
    if not isinstance(partitions, list):
        raise ValueError("r2_partition_census_invalid")
    floor_bindings_sha256 = str(
        rolling.get("provider_ablation_floor_bindings_sha256") or ""
    )
    candidates: list[dict[str, Any]] = []
    for partition in partitions:
        if not isinstance(partition, Mapping):
            raise ValueError("r2_partition_not_object")
        eligible = _validated_r2_partition_candidate_state(
            partition,
            target_date=target_date,
            global_candidate_blockers=global_candidate_blockers,
        )
        if eligible:
            candidates.append(
                canonical_r3_candidate_from_r2_partition(
                    partition,
                    provider_ablation_floor_bindings_sha256=floor_bindings_sha256,
                )
            )
    candidate_ids = [candidate["candidate_id"] for candidate in candidates]
    if len(candidate_ids) != len(set(candidate_ids)):
        raise ValueError("r2_candidate_projection_duplicate")
    return candidates


def validate_r2_partition_candidate_state(
    partition: Mapping[str, Any],
    *,
    target_date: str,
    global_candidate_blockers: Sequence[str],
) -> bool:
    """Publicly revalidate one persisted R2 partition's gate semantics."""

    return _validated_r2_partition_candidate_state(
        partition,
        target_date=target_date,
        global_candidate_blockers=global_candidate_blockers,
    )


def validate_r2_rolling_artifact(rolling: Mapping[str, Any]) -> None:
    """Validate the rolling evidence generation bound by the R3 manifest."""

    if rolling.get("schema") != ROLLING_SCHEMA:
        raise ValueError("r2_rolling_schema_invalid")
    if rolling.get("artifact_content_sha256") != _content_hash(
        rolling, "artifact_content_sha256"
    ):
        raise ValueError("r2_rolling_content_hash_invalid")
    _validate_exact_offline_authority(rolling, label="r2_rolling")
    try:
        date.fromisoformat(str(rolling.get("target_date") or ""))
    except ValueError as exc:
        raise ValueError("r2_rolling_target_date_invalid") from exc
    floor_bindings_sha256 = rolling.get("provider_ablation_floor_bindings_sha256")
    if not _valid_sha256(floor_bindings_sha256):
        raise ValueError("r2_provider_floor_binding_hash_missing")
    if floor_bindings_sha256 != _sha256(
        rolling.get("provider_ablation_floor_bindings")
    ):
        raise ValueError("r2_provider_floor_binding_hash_invalid")
    current_run_blockers = rolling.get("current_run_global_blockers")
    if (
        not isinstance(current_run_blockers, list)
        or any(
            not isinstance(value, str) or not value for value in current_run_blockers
        )
        or current_run_blockers != sorted(set(current_run_blockers))
        or rolling.get("current_run_global_blockers_sha256")
        != _sha256(current_run_blockers)
    ):
        raise ValueError("r2_current_run_blocker_binding_invalid")
    global_candidate_blockers = rolling.get("global_candidate_blockers")
    if (
        not isinstance(global_candidate_blockers, list)
        or any(
            not isinstance(value, str) or not value
            for value in global_candidate_blockers
        )
        or global_candidate_blockers != sorted(set(global_candidate_blockers))
    ):
        raise ValueError("r2_global_candidate_blocker_census_invalid")
    if any(
        f"current_run_composed_chain_blocked:{blocker}" not in global_candidate_blockers
        for blocker in current_run_blockers
    ):
        raise ValueError("r2_current_run_global_blocker_projection_invalid")
    expected_statuses = (
        {"source_quality_or_composed_chain_blocked"}
        if current_run_blockers
        else (
            {"historical_execution_contract_blocked"}
            if global_candidate_blockers
            else {"rolling_evaluated", "no_joined_lifecycle_rows"}
        )
    )
    if rolling.get("status") not in expected_statuses:
        raise ValueError("r2_rolling_status_semantic_mismatch")
    blocked_pre_clear_candidate_count = _native_nonnegative_int(
        rolling.get("blocked_pre_clear_candidate_count")
    )
    if blocked_pre_clear_candidate_count != 0:
        raise ValueError("r2_blocked_pre_clear_candidate_census_invalid")
    partitions = rolling.get("partitions")
    if not isinstance(partitions, list):
        raise ValueError("r2_partition_census_invalid")
    for partition in partitions:
        validate_r2_partition_candidate_state(
            partition,
            target_date=str(rolling.get("target_date") or ""),
            global_candidate_blockers=global_candidate_blockers,
        )


def _validate_r2_rolling_artifact(rolling: Mapping[str, Any]) -> None:
    """Compatibility alias for the public R2 semantic validator."""

    validate_r2_rolling_artifact(rolling)


def validate_r3_source_only_manifest(
    manifest: Mapping[str, Any],
    *,
    source_rolling_artifact: Mapping[str, Any] | None = None,
) -> None:
    """Validate R3 identity and its exact immutable R2 evidence generation."""

    if manifest.get("schema") != R3_SCHEMA:
        raise ValueError("r3_manifest_schema_invalid")
    if manifest.get("artifact_content_sha256") != _content_hash(
        manifest, "artifact_content_sha256"
    ):
        raise ValueError("r3_manifest_content_hash_invalid")
    _validate_exact_offline_authority(manifest, label="r3_manifest")
    if not isinstance(source_rolling_artifact, Mapping):
        raise ValueError("r3_manifest_source_rolling_artifact_missing")
    _validate_r2_rolling_artifact(source_rolling_artifact)
    try:
        manifest_date = date.fromisoformat(str(manifest.get("target_date") or ""))
    except ValueError as exc:
        raise ValueError("r3_manifest_target_date_invalid") from exc
    if (
        str(source_rolling_artifact.get("target_date") or "")
        != manifest_date.isoformat()
    ):
        raise ValueError("r3_manifest_source_rolling_target_date_mismatch")
    source_rolling_sha256 = manifest.get("source_rolling_artifact_sha256")
    if not _valid_sha256(source_rolling_sha256):
        raise ValueError("r3_manifest_source_rolling_hash_invalid")
    if source_rolling_sha256 != source_rolling_artifact.get("artifact_content_sha256"):
        raise ValueError("r3_manifest_source_rolling_binding_mismatch")
    candidates = manifest.get("candidates")
    candidate_count = manifest.get("candidate_count")
    if (
        not isinstance(candidates, list)
        or isinstance(candidate_count, bool)
        or not isinstance(candidate_count, int)
        or candidate_count < 0
        or candidate_count != len(candidates)
    ):
        raise ValueError("r3_manifest_candidate_census_invalid")
    if manifest.get("first_runtime_candidate_auto_apply_performed") is not False:
        raise ValueError("r3_manifest_runtime_auto_apply_state_invalid")
    floor_bindings_sha256 = manifest.get(
        "source_provider_ablation_floor_bindings_sha256"
    )
    if not _valid_sha256(floor_bindings_sha256):
        raise ValueError("r3_manifest_provider_floor_binding_missing")
    if floor_bindings_sha256 != source_rolling_artifact.get(
        "provider_ablation_floor_bindings_sha256"
    ):
        raise ValueError("r3_manifest_r2_provider_floor_binding_mismatch")
    current_run_blockers = source_rolling_artifact.get("current_run_global_blockers")
    current_run_blockers_sha256 = source_rolling_artifact.get(
        "current_run_global_blockers_sha256"
    )
    if (
        manifest.get("source_current_run_global_blockers_sha256")
        != current_run_blockers_sha256
    ):
        raise ValueError("r3_manifest_r2_current_blocker_binding_mismatch")
    global_candidate_blockers = source_rolling_artifact.get("global_candidate_blockers")
    if manifest.get("global_candidate_blockers") != global_candidate_blockers:
        raise ValueError("r3_manifest_r2_global_blocker_binding_mismatch")
    projected_candidates = project_r3_candidates_from_validated_r2(
        source_rolling_artifact
    )
    if candidates != projected_candidates:
        raise ValueError("r3_manifest_candidate_projection_mismatch")
    if candidate_count != len(projected_candidates):
        raise ValueError("r3_manifest_candidate_projection_census_mismatch")
    blocked_pre_clear_candidate_count = source_rolling_artifact.get(
        "blocked_pre_clear_candidate_count"
    )
    if (
        manifest.get("blocked_pre_clear_candidate_count")
        != blocked_pre_clear_candidate_count
    ):
        raise ValueError("r3_manifest_r2_blocked_pre_clear_census_mismatch")
    expected_status = (
        "source_only_candidate_blocked_current_run"
        if current_run_blockers
        else (
            "source_only_candidate_blocked_invalid_historical_execution"
            if global_candidate_blockers
            else (
                "source_only_candidates_ready"
                if projected_candidates
                else "no_source_only_candidate_passed_all_gates"
            )
        )
    )
    if manifest.get("status") != expected_status:
        raise ValueError("r3_manifest_status_semantic_mismatch")
    if global_candidate_blockers and (candidate_count != 0 or candidates):
        raise ValueError("r3_manifest_global_blocked_candidate_invalid")
    for candidate in candidates:
        if not isinstance(candidate, Mapping):
            raise ValueError("r3_candidate_not_object")
        _validate_exact_offline_authority(candidate, label="r3_candidate")
        if (
            manifest_date >= date.fromisoformat(CURRENT_DESIGN_ACTIVATION_DATE)
            and candidate.get("ablation_design_version") != CURRENT_DESIGN_VERSION
        ):
            raise ValueError("r3_candidate_current_design_required")
        if (
            manifest_date >= date.fromisoformat(CURRENT_DESIGN_ACTIVATION_DATE)
            and candidate.get("provider_ablation_floor_bindings_sha256")
            != floor_bindings_sha256
        ):
            raise ValueError("r3_candidate_provider_floor_binding_mismatch")
        candidate_content = {
            key: value
            for key, value in candidate.items()
            if key not in {"candidate_id", "candidate_sha256"}
        }
        candidate_sha256 = _sha256(candidate_content)
        if (
            candidate.get("candidate_sha256") != candidate_sha256
            or candidate.get("candidate_id")
            != f"main-ai-quality-{candidate_sha256[:24]}"
        ):
            raise ValueError("r3_candidate_identity_hash_invalid")


def _validate_r3_source_only_manifest(
    manifest: Mapping[str, Any],
    *,
    source_rolling_artifact: Mapping[str, Any] | None = None,
) -> None:
    """Compatibility alias for the public R3/R2 semantic validator."""

    validate_r3_source_only_manifest(
        manifest,
        source_rolling_artifact=source_rolling_artifact,
    )


def build_rolling_source_only_candidates(
    *,
    target_date: str,
    execution_reports: Iterable[Mapping[str, Any]],
    lifecycle_reports: Iterable[Mapping[str, Any]],
    source_quality_pass_by_date: Mapping[str, bool],
    economic_reference_pass_by_date: Mapping[str, bool],
    outcome_label_artifacts_by_date: Mapping[str, Mapping[str, Any]] | None = None,
    outcome_bridge_artifacts_by_date: Mapping[str, Mapping[str, Any]] | None = None,
    input_diagnostics: Iterable[Mapping[str, Any]] = (),
    current_run_global_blockers: Iterable[str] = (),
    counterfactual_entry_diagnostic_out: dict[str, Any] | None = None,
    counterfactual_entry_output_path: Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build strict rolling R2 evidence and an R3 source-only manifest."""

    try:
        target_day = date.fromisoformat(target_date)
    except ValueError as exc:
        raise ValueError("rolling_target_date_invalid") from exc
    current_activation_day = date.fromisoformat(CURRENT_DESIGN_ACTIVATION_DATE)

    invalid_lifecycle_trace_keys: set[tuple[str, str]] = set()
    invalid_lifecycle_report_dates: set[str] = set()
    lifecycle_index, lifecycle_findings = _lifecycle_index(
        lifecycle_reports,
        contract_invalid_trace_keys_out=invalid_lifecycle_trace_keys,
        contract_invalid_report_dates_out=invalid_lifecycle_report_dates,
    )
    joined_rows: list[dict[str, Any]] = []
    counterfactual_entry_rows: list[dict[str, Any]] = []
    counterfactual_entry_exclusions: list[dict[str, Any]] = []
    exclusions: list[dict[str, Any]] = []
    source_dates: set[str] = set()
    provider_floor_bindings_by_date: dict[str, dict[str, Any]] = {}
    provider_floor_validation_cache = (
        quality.MicroReversionProviderFloorValidationCache()
    )

    def relevant_current_design_date(value: Any) -> bool:
        if target_day < current_activation_day:
            return True
        try:
            return date.fromisoformat(str(value or "")) >= current_activation_day
        except ValueError:
            return True

    current_run_blockers = sorted(
        {
            str(blocker).strip()
            for blocker in current_run_global_blockers
            if str(blocker).strip()
        }
    )
    current_run_blockers_sha256 = _sha256(current_run_blockers)
    global_candidate_blockers = [
        f"current_run_composed_chain_blocked:{blocker}"
        for blocker in current_run_blockers
    ]
    for diagnostic in input_diagnostics:
        if (
            not isinstance(diagnostic, Mapping)
            or diagnostic.get("status") != "invalid"
            or not relevant_current_design_date(diagnostic.get("target_date"))
        ):
            continue
        artifact = diagnostic.get("artifact")
        if artifact not in {"execution", "lifecycle"}:
            continue
        global_candidate_blockers.append(
            f"historical_{artifact}_artifact_collection_invalid:"
            f"{str(diagnostic.get('target_date') or 'missing')}:"
            f"{str(diagnostic.get('reason') or 'unknown')}"
        )
    outcome_label_artifacts_by_date = outcome_label_artifacts_by_date or {}
    outcome_bridge_artifacts_by_date = outcome_bridge_artifacts_by_date or {}
    for report in execution_reports:
        report_target_date = str(report.get("target_date") or "")
        try:
            companion = outcome_label_artifacts_by_date.get(report_target_date)
            outcome_label_artifact: Mapping[str, Any] | None = None
            source_bridge_report: Mapping[str, Any] | None = (
                outcome_bridge_artifacts_by_date.get(report_target_date)
            )
            materialized_report: Mapping[str, Any] | None = None
            source_bundle_report: Mapping[str, Any] | None = None
            prepared_artifact: Mapping[str, Any] | None = None
            paired_report: Mapping[str, Any] | None = None
            checkpoint_artifact: Mapping[str, Any] | None = None
            provider_ablation_floor_artifact: Mapping[str, Any] | None = None
            if isinstance(companion, Mapping) and (
                "outcome_label_artifact" in companion
                or "source_bridge_report" in companion
                or "materialized_report" in companion
                or "source_bundle_report" in companion
                or "prepared_artifact" in companion
                or "paired_report" in companion
                or "checkpoint_artifact" in companion
                or "provider_ablation_floor_artifact" in companion
                or "outcome_label_path" in companion
                or "source_bridge_path" in companion
                or "materialized_report_path" in companion
                or "source_bundle_path" in companion
                or "prepared_artifact_path" in companion
                or "paired_report_path" in companion
                or "checkpoint_artifact_path" in companion
                or "provider_ablation_floor_artifact_path" in companion
            ):
                embedded_label = companion.get("outcome_label_artifact")
                embedded_bridge = companion.get("source_bridge_report")
                embedded_materialized = companion.get("materialized_report")
                embedded_source_bundle = companion.get("source_bundle_report")
                embedded_prepared = companion.get("prepared_artifact")
                embedded_paired = companion.get("paired_report")
                embedded_checkpoint = companion.get("checkpoint_artifact")
                embedded_provider_floor = companion.get(
                    "provider_ablation_floor_artifact"
                )
                if isinstance(embedded_label, Mapping):
                    outcome_label_artifact = embedded_label
                if isinstance(embedded_bridge, Mapping):
                    source_bridge_report = embedded_bridge
                if isinstance(embedded_materialized, Mapping):
                    materialized_report = embedded_materialized
                if isinstance(embedded_source_bundle, Mapping):
                    source_bundle_report = embedded_source_bundle
                if isinstance(embedded_prepared, Mapping):
                    prepared_artifact = embedded_prepared
                if isinstance(embedded_paired, Mapping):
                    paired_report = embedded_paired
                if isinstance(embedded_checkpoint, Mapping):
                    checkpoint_artifact = embedded_checkpoint
                if isinstance(embedded_provider_floor, Mapping):
                    provider_ablation_floor_artifact = embedded_provider_floor
                label_path = companion.get("outcome_label_path")
                bridge_path = companion.get("source_bridge_path")
                materialized_path = companion.get("materialized_report_path")
                source_bundle_path = companion.get("source_bundle_path")
                prepared_path = companion.get("prepared_artifact_path")
                paired_path = companion.get("paired_report_path")
                checkpoint_path = companion.get("checkpoint_artifact_path")
                provider_floor_path = companion.get(
                    "provider_ablation_floor_artifact_path"
                )
                if outcome_label_artifact is None and label_path:
                    outcome_label_artifact = _load_json_auto(Path(str(label_path)))
                if source_bridge_report is None and bridge_path:
                    source_bridge_report = _load_json_auto(Path(str(bridge_path)))
                if materialized_report is None and materialized_path:
                    materialized_report = _load_json_auto(Path(str(materialized_path)))
                if source_bundle_report is None and source_bundle_path:
                    source_bundle_report = _load_json_auto(
                        Path(str(source_bundle_path))
                    )
                if prepared_artifact is None and prepared_path:
                    prepared_artifact = _load_json_auto(Path(str(prepared_path)))
                if paired_report is None and paired_path:
                    paired_report = _load_json_auto(Path(str(paired_path)))
                if checkpoint_artifact is None and checkpoint_path:
                    checkpoint_artifact = quality._load_micro_reversion_checkpoint(
                        Path(str(checkpoint_path)),
                        repair_manifest=False,
                    )
                if provider_ablation_floor_artifact is None and provider_floor_path:
                    provider_ablation_floor_artifact = _load_json_auto(
                        Path(str(provider_floor_path))
                    )
            elif isinstance(companion, Mapping):
                outcome_label_artifact = companion
            rows = _validated_execution_rows(
                report,
                outcome_label_artifact=outcome_label_artifact,
                source_bridge_report=source_bridge_report,
                materialized_report=materialized_report,
                source_bundle_report=source_bundle_report,
                prepared_artifact=prepared_artifact,
                paired_report=paired_report,
                checkpoint_artifact=checkpoint_artifact,
                provider_ablation_floor_artifact=(provider_ablation_floor_artifact),
                provider_floor_validation_cache=provider_floor_validation_cache,
            )
            if report.get(
                "ablation_design_version"
            ) == CURRENT_DESIGN_VERSION and isinstance(
                provider_ablation_floor_artifact, Mapping
            ):
                provider_floor_bindings_by_date[report_target_date] = {
                    "target_date": report_target_date,
                    "floor_content_sha256": (
                        provider_ablation_floor_artifact.get("floor_content_sha256")
                    ),
                    "floor_artifact_sha256": _sha256(provider_ablation_floor_artifact),
                    "observed_trading_days": (
                        provider_ablation_floor_artifact.get("observed_trading_days")
                    ),
                    "observed_common_parent_count": (
                        provider_ablation_floor_artifact.get(
                            "observed_common_parent_count"
                        )
                    ),
                    "observed_unique_symbol_count": (
                        provider_ablation_floor_artifact.get(
                            "observed_unique_symbol_count"
                        )
                    ),
                    "parent_census_sha256": (
                        provider_ablation_floor_artifact.get("parent_census_sha256")
                    ),
                    "symbol_census_sha256": (
                        provider_ablation_floor_artifact.get("symbol_census_sha256")
                    ),
                }
        except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
            blocker = (
                "historical_execution_artifact_contract_invalid:"
                f"{str(report.get('target_date') or 'missing')}:"
                f"{str(exc)}"
            )
            if relevant_current_design_date(report.get("target_date")):
                global_candidate_blockers.append(blocker)
            exclusions.append(
                {"reason": str(exc), "target_date": report.get("target_date")}
            )
            continue
        report_date = str(report.get("target_date") or "")
        try:
            report_day = date.fromisoformat(report_date)
        except ValueError:
            report_day = None
        post_activation_current_design = bool(
            report.get("ablation_design_version") == CURRENT_DESIGN_VERSION
            and report_day is not None
            and report_day >= current_activation_day
        )
        source_dates.add(report_date)
        if source_quality_pass_by_date.get(report_date) is not True:
            if post_activation_current_design:
                counterfactual_entry_exclusions.extend(
                    {
                        "source_row": row,
                        "reason": "source_quality_audit_not_pass",
                        "findings": ["source_quality_audit_not_pass"],
                    }
                    for row in rows
                    if row.get("decision_stage") == "entry"
                    and row.get("captured_control_action") in {"WAIT", "DROP"}
                )
            exclusions.append(
                {"reason": "source_quality_audit_not_pass", "target_date": report_date}
            )
            continue
        if economic_reference_pass_by_date.get(report_date) is not True:
            if post_activation_current_design:
                counterfactual_entry_exclusions.extend(
                    {
                        "source_row": row,
                        "reason": "economic_reference_not_verified",
                        "findings": ["economic_reference_not_verified"],
                    }
                    for row in rows
                    if row.get("decision_stage") == "entry"
                    and row.get("captured_control_action") in {"WAIT", "DROP"}
                )
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
            if not findings and row.get("stock_code") != (lifecycle or {}).get(
                "stock_code"
            ):
                findings.append("daily_lifecycle_identity_binding_mismatch")
            if not findings:
                findings.extend(_lifecycle_trace_context_findings(lifecycle or {}, row))
            if not findings and (
                row.get("cost_profile_artifact_sha256")
                != (lifecycle or {}).get("reviewed_cost_profile_sha256")
                or row.get("symbol_master_artifact_sha256")
                != (lifecycle or {}).get("symbol_master_artifact_sha256")
            ):
                findings.append("daily_economic_reference_binding_mismatch")
            if findings:
                lifecycle_key = (
                    report_date,
                    str(row.get("decision_trace_id") or ""),
                )
                natural_entry_non_order_absence = bool(
                    findings == ["lifecycle_exact_join_missing"]
                    and row.get("decision_stage") == "entry"
                    and row.get("captured_control_action") in {"WAIT", "DROP"}
                )
                if (
                    post_activation_current_design
                    and natural_entry_non_order_absence
                    and report_date not in invalid_lifecycle_report_dates
                    and lifecycle_key not in invalid_lifecycle_trace_keys
                ):
                    counterfactual_entry_rows.append(
                        {
                            **row,
                            "lifecycle_findings": ["lifecycle_exact_join_missing"],
                        }
                    )
                elif post_activation_current_design and (
                    row.get("decision_stage") == "entry"
                    and row.get("captured_control_action") in {"WAIT", "DROP"}
                ):
                    diagnostic_findings = list(findings)
                    if (
                        report_date in invalid_lifecycle_report_dates
                        or lifecycle_key in invalid_lifecycle_trace_keys
                    ):
                        diagnostic_findings.append(
                            "lifecycle_artifact_or_trace_invalid"
                        )
                    counterfactual_entry_exclusions.append(
                        {
                            "source_row": row,
                            "reason": "counterfactual_entry_contract_not_eligible",
                            "findings": diagnostic_findings,
                        }
                    )
                if post_activation_current_design and (
                    report_date in invalid_lifecycle_report_dates
                    or lifecycle_key in invalid_lifecycle_trace_keys
                    or (
                        findings[0] == "lifecycle_exact_join_missing"
                        and not natural_entry_non_order_absence
                    )
                ):
                    global_candidate_blockers.append(
                        "current_lifecycle_exact_census_invalid:"
                        f"{report_date}:"
                        f"{str(row.get('paired_replay_parent_id') or 'missing')}:"
                        f"{findings[0]}"
                    )
                exclusions.append(
                    {
                        "target_date": report_date,
                        "paired_replay_parent_id": row.get("paired_replay_parent_id"),
                        "decision_trace_id": row.get("decision_trace_id"),
                        "reason": (
                            "lifecycle_not_applicable_non_order_entry"
                            if natural_entry_non_order_absence
                            else findings[0]
                        ),
                        "findings": findings,
                        "lifecycle_join_requirement": (
                            "not_applicable_non_order_entry"
                            if natural_entry_non_order_absence
                            else "required"
                        ),
                        "repair_required": not natural_entry_non_order_absence,
                    }
                )
                continue
            lifecycle_row = dict(lifecycle or {})
            joined_rows.append(
                {
                    **row,
                    "main_lifecycle_id": str(
                        lifecycle_row.get("main_lifecycle_id") or ""
                    ),
                    "lifecycle_stage": _execution_lifecycle_stage(row),
                    "lifecycle_source_row_sha256": _sha256(lifecycle_row),
                    "lifecycle": lifecycle_row,
                }
            )

    global_candidate_blockers = sorted(set(global_candidate_blockers))
    provider_floor_bindings = [
        provider_floor_bindings_by_date[date_key]
        for date_key in sorted(provider_floor_bindings_by_date)
    ]
    provider_floor_bindings_sha256 = _sha256(provider_floor_bindings)
    counterfactual_entry_blockers = list(global_candidate_blockers)
    counterfactual_entry_blockers.extend(
        f"invalid_lifecycle_report:{report_date}"
        for report_date in sorted(invalid_lifecycle_report_dates)
        if relevant_current_design_date(report_date)
    )
    counterfactual_entry_blockers.extend(
        f"invalid_lifecycle_trace:{report_date}:{trace_id}"
        for report_date, trace_id in sorted(invalid_lifecycle_trace_keys)
        if relevant_current_design_date(report_date)
    )
    for finding in lifecycle_findings:
        if finding.startswith("lifecycle_findings_truncated:"):
            scope_counts: dict[str, int] = {}
            try:
                scope_counts = {
                    scope: int(raw_count)
                    for token in finding.partition(":")[2].split(",")
                    for scope, separator, raw_count in [token.partition("=")]
                    if separator
                }
            except ValueError:
                scope_counts = {}
            if (
                set(scope_counts) == {"pre_current_design", "current_design", "undated"}
                and scope_counts["pre_current_design"] > 0
                and scope_counts["current_design"] == 0
                and scope_counts["undated"] == 0
            ):
                continue
            counterfactual_entry_blockers.append(
                f"invalid_lifecycle_artifact:{finding}"
            )
            continue
        finding_dates = re.findall(r"\d{4}-\d{2}-\d{2}", finding)
        if not finding_dates or any(
            relevant_current_design_date(finding_date) for finding_date in finding_dates
        ):
            counterfactual_entry_blockers.append(
                f"invalid_lifecycle_artifact:{finding}"
            )
    diagnostic_output_path = (
        counterfactual_entry_output_path
        or counterfactual_entry_diagnostic_path(target_date)
    )
    counterfactual_entry_artifact: dict[str, Any] = {}
    if target_day >= current_activation_day:
        counterfactual_entry_artifact = (
            entry_diagnostic.build_counterfactual_entry_diagnostic(
                target_date=target_date,
                rows=counterfactual_entry_rows,
                exclusions=counterfactual_entry_exclusions,
                global_blockers=sorted(set(counterfactual_entry_blockers)),
            )
        )
        counterfactual_entry_provenance = {
            "schema": counterfactual_entry_artifact["schema"],
            "path": str(diagnostic_output_path),
            "artifact_content_sha256": counterfactual_entry_artifact[
                "artifact_content_sha256"
            ],
            "status": counterfactual_entry_artifact["status"],
            "eligible_parent_count": counterfactual_entry_artifact[
                "eligible_parent_count"
            ],
            "full_parent_census_count": counterfactual_entry_artifact[
                "full_parent_census_count"
            ],
            "candidate_count": 0,
            "actual_lifecycle_r2_r3_join_unchanged": True,
            "runtime_candidate_eligible": False,
            "provider_or_order_authority": False,
        }
    else:
        counterfactual_entry_provenance = {
            "schema": entry_diagnostic.COUNTERFACTUAL_ENTRY_DIAGNOSTIC_SCHEMA,
            "path": str(diagnostic_output_path),
            "artifact_content_sha256": None,
            "status": "not_applicable_before_current_design",
            "eligible_parent_count": 0,
            "full_parent_census_count": 0,
            "candidate_count": 0,
            "actual_lifecycle_r2_r3_join_unchanged": True,
            "runtime_candidate_eligible": False,
            "provider_or_order_authority": False,
        }
    if counterfactual_entry_diagnostic_out is not None:
        counterfactual_entry_diagnostic_out.clear()
        counterfactual_entry_diagnostic_out.update(counterfactual_entry_artifact)

    grouped: dict[
        tuple[str, str, str, str, str, str, str, str, str, str, str],
        list[dict[str, Any]],
    ] = defaultdict(list)
    for row in joined_rows:
        key = (
            str(row.get("decision_stage") or ""),
            str(row.get("effective_venue") or ""),
            str(row.get("session_bucket") or ""),
            str(row.get("control_contract_sha256") or ""),
            str(row.get("candidate_contract_sha256") or ""),
            str(row.get("selected_cost_profile_id") or ""),
            str(row.get("selected_cost_profile_content_sha256") or ""),
            str(row.get("control_prompt_sha256") or ""),
            str(row.get("candidate_prompt_sha256") or ""),
            str(row.get("ablation_design_version") or LEGACY_DESIGN_VERSION),
            str(row.get("r3_tuning_axis") or "prompt_contract_effect"),
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
        if target_day >= current_activation_day:
            if key[9] != CURRENT_DESIGN_VERSION:
                gate_findings["activation_design"] = [
                    "post_activation_r3_requires_current_ablation_design"
                ]
            pre_activation_source_dates = sorted(
                {
                    str(row.get("target_date") or "")
                    for row in rows
                    if str(row.get("target_date") or "")
                    < CURRENT_DESIGN_ACTIVATION_DATE
                }
            )
            if pre_activation_source_dates:
                gate_findings["activation_window"] = [
                    "current_r3_evidence_requires_post_activation_source_dates"
                ]
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
        latest_reference_date = max(
            (row["target_date"] for row in reference_binding_rows), default=""
        )
        latest_symbol_master_hashes = {
            row["symbol_master_artifact_sha256"]
            for row in reference_binding_rows
            if row["target_date"] == latest_reference_date
        }
        latest_symbol_master_artifact_sha256 = (
            next(iter(latest_symbol_master_hashes))
            if len(latest_symbol_master_hashes) == 1
            else ""
        )
        if (
            not latest_reference_date
            or len(latest_symbol_master_hashes) != 1
            or not _valid_sha256(latest_symbol_master_artifact_sha256)
        ):
            all_gates_pass = False
            gate_findings["identity"] = [
                "latest_symbol_master_artifact_binding_not_unique"
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
            "current_prompt_sha256": key[7],
            "recommended_prompt_sha256": key[8],
            "ablation_design_version": key[9],
            "tuning_axis": key[10],
            "economic_reference_bindings_sha256": reference_bindings_sha256,
            "economic_reference_binding_count": len(reference_binding_rows),
            "latest_symbol_master_source_date": latest_reference_date,
            "latest_symbol_master_artifact_sha256": (
                latest_symbol_master_artifact_sha256
            ),
            "source_row_count": len(rows),
            "source_dates": sorted({row["target_date"] for row in rows}),
            "confirmation_window_tuning_axis": (
                _confirmation_window_tuning_census(rows)
            ),
            "windows": windows,
            "gate_findings": gate_findings,
            "r3_source_candidate_eligible": all_gates_pass,
        }
        partitions.append(partition)
        if not all_gates_pass:
            continue
        source_candidates.append(
            canonical_r3_candidate_from_r2_partition(
                partition,
                provider_ablation_floor_bindings_sha256=(
                    provider_floor_bindings_sha256
                ),
            )
        )

    blocked_pre_clear_candidate_count = (
        len(source_candidates) if global_candidate_blockers else 0
    )
    if global_candidate_blockers:
        # The current blocked-day artifact remains publishable diagnostic
        # evidence, but no candidate identity may survive into R3.
        source_candidates = []

    rolling_body = {
        "schema": ROLLING_SCHEMA,
        "target_date": target_date,
        "generated_at": datetime.now(KST).isoformat(),
        "status": (
            "source_quality_or_composed_chain_blocked"
            if current_run_blockers
            else (
                "historical_execution_contract_blocked"
                if global_candidate_blockers
                else (
                    "rolling_evaluated" if joined_rows else "no_joined_lifecycle_rows"
                )
            )
        ),
        "clean_tuning_baseline_date": CLEAN_BASELINE_DATE.isoformat(),
        "source_execution_dates": sorted(source_dates),
        "ablation_design_versions": sorted(
            {
                str(row.get("ablation_design_version") or LEGACY_DESIGN_VERSION)
                for row in joined_rows
            }
        ),
        "joined_parent_count": len(joined_rows),
        "excluded_parent_count": len(exclusions),
        "partitions": partitions,
        "exclusions": exclusions,
        "global_candidate_blockers": global_candidate_blockers,
        "current_run_global_blockers": current_run_blockers,
        "current_run_global_blockers_sha256": current_run_blockers_sha256,
        "blocked_pre_clear_candidate_count": blocked_pre_clear_candidate_count,
        "lifecycle_report_findings": lifecycle_findings,
        "counterfactual_entry_diagnostic": counterfactual_entry_provenance,
        "provider_ablation_floor_bindings": provider_floor_bindings,
        "provider_ablation_floor_bindings_sha256": (provider_floor_bindings_sha256),
        "lifecycle_promotion_estimator_contract": (
            LIFECYCLE_PROMOTION_ESTIMATOR_CONTRACT
        ),
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
            "sum_multiple_decision_parents_for_one_lifecycle_stage",
            "sum_multiple_stages_for_one_lifecycle_promotion_economics",
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
            "source_only_candidate_blocked_current_run"
            if current_run_blockers
            else (
                "source_only_candidate_blocked_invalid_historical_execution"
                if global_candidate_blockers
                else (
                    "source_only_candidates_ready"
                    if source_candidates
                    else "no_source_only_candidate_passed_all_gates"
                )
            )
        ),
        "source_rolling_artifact_sha256": rolling["artifact_content_sha256"],
        "source_provider_ablation_floor_bindings_sha256": (
            provider_floor_bindings_sha256
        ),
        "candidate_count": len(source_candidates),
        "candidates": source_candidates,
        "global_candidate_blockers": global_candidate_blockers,
        "source_current_run_global_blockers_sha256": current_run_blockers_sha256,
        "blocked_pre_clear_candidate_count": blocked_pre_clear_candidate_count,
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
    quality.finalize_micro_reversion_provider_floor_validation_cache(
        provider_floor_validation_cache
    )
    _validate_r3_source_only_manifest(
        manifest,
        source_rolling_artifact=rolling,
    )
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


def _scheduled_bridge_command(
    *,
    target_date: str,
    selected_paths: Mapping[str, Path],
    prepared_artifact: Mapping[str, Any],
    write: bool,
) -> list[str]:
    """Build the fail-closed scheduled bridge command for one prepared census."""

    prepared_count = prepared_artifact.get("prepared_request_count")
    if (
        prepared_artifact.get("target_date") != target_date
        or isinstance(prepared_count, bool)
        or not isinstance(prepared_count, int)
        or prepared_count <= 0
    ):
        raise ValueError("scheduled_bridge_prepared_census_invalid")
    command = [
        sys.executable,
        "-m",
        "src.engine.scalping.micro_reversion.ai_quality_bridge",
        "--date",
        target_date,
        "--verified-cost-profile",
        str(selected_paths["cost_profile"]),
        "--symbol-master",
        str(selected_paths["symbol_master"]),
        "--storage-capacity-status",
        str(selected_paths["capacity_status"]),
        "--prepared-requests",
        str(selected_paths["prepared"]),
        "--prepared-artifact-sha256",
        _sha256(prepared_artifact),
        "--prepared-request-count",
        str(prepared_count),
    ]
    if write:
        command.append("--write")
    return command


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
        "economic_policy": ECONOMIC_POLICY_PATH,
        "economic_owner_report": SOURCE_POLICY_ROOT
        / "daily"
        / target_date
        / "owner_report.json",
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
        "counterfactual_entry_diagnostic": counterfactual_entry_diagnostic_path(
            target_date
        ),
        "capacity_status": DATA_DIR
        / "report"
        / "micro_reversion_storage_capacity"
        / f"micro_reversion_storage_capacity_{target_date}.json",
        "provider_ablation_floor": provider_ablation_floor_path(target_date),
        "execution": quality.micro_reversion_execution_result_path(target_date),
        "execution_checkpoint": quality.micro_reversion_execution_checkpoint_path(
            target_date
        ),
        "lifecycle": LIFECYCLE_REPORT_ROOT
        / f"main_scalping_lifecycle_paired_{target_date}.json",
        "observer_canary_latest": OBSERVER_CANARY_LATEST_PATH,
        "observer_canary_daily": OBSERVER_CANARY_DAILY_ROOT
        / f"scalp_micro_reversion_canary_snapshot_{target_date}.json",
    }


def _aware_artifact_datetime(value: Any) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value or "").replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed.astimezone(KST)


def _observer_canary_diagnostic(
    *, target_date: str, latest_path: Path, daily_path: Path
) -> dict[str, Any]:
    """Load exact-date observer health without granting tuning authority."""

    selected_path: Path | None = None
    payload: dict[str, Any] | None = None
    source_sha256: str | None = None
    for candidate in (latest_path, daily_path):
        try:
            resolved = existing_or_gzip_path(candidate)
            raw = resolved.read_bytes()
            decoded = gzip.decompress(raw) if resolved.suffix == ".gz" else raw
            candidate_payload = json.loads(decoded.decode("utf-8"))
            if not isinstance(candidate_payload, dict):
                raise ValueError(f"json_artifact_not_object:{resolved}")
        except (
            FileNotFoundError,
            OSError,
            TypeError,
            ValueError,
            json.JSONDecodeError,
        ):
            continue
        generated_at = _aware_artifact_datetime(candidate_payload.get("generated_at"))
        if generated_at is None or generated_at.date().isoformat() != target_date:
            continue
        selected_path = resolved
        payload = candidate_payload
        source_sha256 = hashlib.sha256(raw).hexdigest()
        break
    base = {
        "schema": "main_ai_quality_observer_canary_diagnostic_v1",
        "target_date": target_date,
        "status": "missing_exact_date_canary",
        "source_path": None,
        "source_sha256": None,
        "guard_status": None,
        "stop_required": None,
        "stop_reasons": [],
        "raw_row_exclusion_required": None,
        "source_quality_row_exclusions": [],
        "queue_loss_census": {},
        **OFFLINE_AUTHORITY,
    }
    if selected_path is None or payload is None:
        return base
    guard = payload.get("canary_guard")
    collector = payload.get("collector_snapshot")
    if (
        payload.get("schema") != "scalp_micro_reversion_canary_monitor_v1"
        or not isinstance(guard, Mapping)
        or not isinstance(collector, Mapping)
    ):
        return {
            **base,
            "status": "invalid_exact_date_canary_contract",
            "source_path": str(selected_path),
            "source_sha256": source_sha256,
        }
    stop_reasons = guard.get("stop_reasons")
    row_exclusions = guard.get("source_quality_row_exclusions")
    guard_status = str(guard.get("status") or "")
    collector_lifecycle = str(collector.get("collector_lifecycle") or "")
    lifecycle_contract_valid = bool(
        (
            guard_status
            in {
                "healthy_observer_canary",
                "healthy_observer_canary_with_source_row_exclusions",
                "warming_up",
            }
            and collector_lifecycle == "running"
        )
        or (
            guard_status == "stopped_clean"
            and collector_lifecycle == "closed"
            and collector.get("reference_reconciliation_completed") is True
        )
        or guard_status == "stop_required"
    )
    guard_contract_valid = bool(
        guard.get("status")
        in {
            "warming_up",
            "healthy_observer_canary",
            "healthy_observer_canary_with_source_row_exclusions",
            "stop_required",
            "stopped_clean",
        }
        and isinstance(guard.get("stop_required"), bool)
        and isinstance(guard.get("raw_row_exclusion_required"), bool)
        and isinstance(stop_reasons, (list, tuple))
        and not isinstance(stop_reasons, (str, bytes))
        and all(isinstance(item, str) and item for item in stop_reasons)
        and isinstance(row_exclusions, (list, tuple))
        and not isinstance(row_exclusions, (str, bytes))
        and all(isinstance(item, str) and item for item in row_exclusions)
        and lifecycle_contract_valid
    )
    authority_valid = all(
        (
            collector.get("selection_authority") is False,
            collector.get("trading_runtime_effect") is False,
            collector.get("actual_order_submitted") is False,
            collector.get("broker_order_forbidden") is True,
        )
    )
    stop_required = guard.get("stop_required") is True
    row_exclusion_required = guard.get("raw_row_exclusion_required") is True
    status = (
        "invalid_exact_date_canary_contract"
        if not guard_contract_valid
        else (
            "invalid_exact_date_canary_authority"
            if not authority_valid
            else (
                "stop_required"
                if stop_required
                else (
                    "row_exclusion_required"
                    if row_exclusion_required
                    else ("warming_up" if guard_status == "warming_up" else "pass")
                )
            )
        )
    )
    queue_fields = (
        "observation_queue_full_count",
        "observation_dropped_envelope_count",
        "depth_queue_full_count",
        "depth_dropped_envelope_count",
    )
    queue_loss_census: dict[str, int] = {}
    for field in queue_fields:
        value = collector.get(field)
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
            queue_loss_census[field] = value
    return {
        **base,
        "status": status,
        "source_path": str(selected_path),
        "source_sha256": source_sha256,
        "generated_at": payload.get("generated_at"),
        "guard_status": guard_status,
        "stop_required": stop_required,
        "stop_reasons": list(stop_reasons or []),
        "raw_row_exclusion_required": row_exclusion_required,
        "source_quality_row_exclusions": list(row_exclusions or []),
        "queue_loss_census": queue_loss_census,
        "collector_lifecycle": collector_lifecycle,
    }


def _observer_provider_gate_blocker(
    observer_canary: Mapping[str, Any],
) -> str | None:
    status = str(observer_canary.get("status") or "")
    if status == "missing_exact_date_canary":
        return "micro_observer_canary_missing_exact_date_canary"
    if not observer_canary.get("source_path"):
        return None
    if status in {
        "invalid_exact_date_canary_contract",
        "invalid_exact_date_canary_authority",
        "warming_up",
        "stop_required",
        "row_exclusion_required",
    }:
        return f"micro_observer_canary_{status}"
    return None


def _observer_source_only_stage_gate(
    observer_canary: Mapping[str, Any],
) -> dict[str, Any]:
    """Separate deterministic label work from Provider/promotion authority.

    Exact bridge/materialized companions are sufficient to build an
    action-neutral label without a network call.  An unscoped observer gap
    must still hold Provider replay and R3 promotion, but it must not suppress
    that independently validated local artifact.
    """

    blocker = _observer_provider_gate_blocker(observer_canary)
    return {
        "schema": "main_ai_quality_observer_source_only_stage_gate_v1",
        "observer_blocks_action_neutral_label_generation": False,
        "observer_blocks_provider_floor_materialization": False,
        "observer_blocks_provider_replay": blocker is not None,
        "observer_blocks_r3_promotion": blocker is not None,
        "blocker_code": blocker,
        **OFFLINE_AUTHORITY,
    }


def _source_only_gap_diagnostics(
    *,
    target_date: str,
    observer_canary: Mapping[str, Any],
    bridge_report: Mapping[str, Any] | None,
    lifecycle_report: Mapping[str, Any] | None,
    rolling_exclusions: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Make producer gaps durable and actionable without runtime authority."""

    contract_findings: list[str] = []

    def artifact_valid(value: Mapping[str, Any] | None, label: str) -> bool:
        if not isinstance(value, Mapping) or value.get("target_date") != target_date:
            return False
        artifact_hash = str(value.get("artifact_content_sha256") or "")
        report_hash = str(value.get("report_content_sha256") or "")
        hash_valid = bool(
            (
                artifact_hash
                and artifact_hash == _content_hash(value, "artifact_content_sha256")
            )
            or (
                not artifact_hash
                and report_hash
                and report_hash == _content_hash(value, "report_content_sha256")
            )
        )
        authority_valid = all(
            (
                value.get("runtime_effect") is False,
                value.get("allowed_runtime_apply") is False,
                value.get("actual_order_submitted") is False,
                value.get("broker_order_forbidden") is True,
            )
        )
        if not hash_valid:
            contract_findings.append(f"{label}_content_hash_invalid")
        if not authority_valid:
            contract_findings.append(f"{label}_authority_invalid")
        return hash_valid and authority_valid

    def nonnegative_int(
        value: Any, field: str, *, missing_is_zero: bool = False
    ) -> int:
        if value is None and missing_is_zero:
            return 0
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            contract_findings.append(f"diagnostic_census_invalid:{field}")
            return 0
        return value

    bridge_summary = (
        bridge_report.get("summary")
        if isinstance(bridge_report, Mapping)
        and isinstance(bridge_report.get("summary"), Mapping)
        else {}
    )
    bridge_available = artifact_valid(bridge_report, "bridge")
    exclusion_counts = (
        bridge_summary.get("exclusion_counts")
        if isinstance(bridge_summary.get("exclusion_counts"), Mapping)
        else {}
    )
    micro_eligible = (
        nonnegative_int(
            bridge_summary.get("micro_context_eligible_primary_episode_count"),
            "micro_context_eligible_primary_episode_count",
        )
        if bridge_available
        else 0
    )
    past_market_missing = (
        nonnegative_int(
            exclusion_counts.get("past_market_row_missing"),
            "past_market_row_missing",
            missing_is_zero=True,
        )
        if bridge_available
        else 0
    )
    route_proof_missing = (
        nonnegative_int(
            exclusion_counts.get("integrated_route_proof_missing"),
            "integrated_route_proof_missing",
            missing_is_zero=True,
        )
        if bridge_available
        else 0
    )
    lifecycle_available = artifact_valid(lifecycle_report, "lifecycle")
    lifecycle_gap = (
        nonnegative_int(
            (lifecycle_report or {}).get("broker_execution_provenance_gap_count"),
            "broker_execution_provenance_gap_count",
        )
        if lifecycle_available
        else 0
    )
    lifecycle_eligible = (
        nonnegative_int(
            (lifecycle_report or {}).get("promotion_evidence_eligible_count"),
            "promotion_evidence_eligible_count",
        )
        if lifecycle_available
        else 0
    )
    lifecycle_pipeline_gap = (
        nonnegative_int(
            (lifecycle_report or {}).get(
                "pipeline_lifecycle_instrumentation_gap_count"
            ),
            "pipeline_lifecycle_instrumentation_gap_count",
            missing_is_zero=True,
        )
        if lifecycle_available
        else 0
    )
    lifecycle_real_submitted = (
        nonnegative_int(
            (lifecycle_report or {}).get("real_submitted_lifecycle_count"),
            "real_submitted_lifecycle_count",
            missing_is_zero=True,
        )
        if lifecycle_available
        else 0
    )
    lifecycle_broker_execution_unique = (
        nonnegative_int(
            (lifecycle_report or {}).get("broker_execution_unique_count"),
            "broker_execution_unique_count",
            missing_is_zero=True,
        )
        if lifecycle_available
        else 0
    )
    lifecycle_receipt_custody_gap_examples: list[dict[str, Any]] = []
    lifecycle_rows = (lifecycle_report or {}).get("rows") if lifecycle_available else []
    if isinstance(lifecycle_rows, list):
        for lifecycle_row in lifecycle_rows:
            if (
                len(lifecycle_receipt_custody_gap_examples) >= 10
                or not isinstance(lifecycle_row, Mapping)
                or lifecycle_row.get("lifecycle_population_scope")
                != LIFECYCLE_POPULATION_REAL_SUBMITTED
                or lifecycle_row.get("broker_execution_unique_count") != 0
            ):
                continue
            lifecycle_receipt_custody_gap_examples.append(
                {
                    "main_lifecycle_id": lifecycle_row.get("main_lifecycle_id"),
                    "attempt_id": lifecycle_row.get("attempt_id"),
                    "record_id": lifecycle_row.get("record_id"),
                    "stock_code": lifecycle_row.get("stock_code"),
                    "venue": lifecycle_row.get("venue"),
                    "session_bucket": lifecycle_row.get("session_bucket"),
                    "observed_actual_broker_order_submitted": lifecycle_row.get(
                        "observed_actual_broker_order_submitted"
                    ),
                    "observed_real_order_evidence": lifecycle_row.get(
                        "observed_real_order_evidence"
                    ),
                    "invalid_transition_reasons": list(
                        lifecycle_row.get("invalid_transition_reasons") or []
                    ),
                    "source_population_scopes": list(
                        lifecycle_row.get("source_population_scopes") or []
                    ),
                }
            )
    rolling_reason_counts = Counter(
        str(row.get("reason") or "")
        for row in rolling_exclusions
        if isinstance(row, Mapping) and str(row.get("reason") or "")
    )
    companion_binding_mismatch_count = int(
        rolling_reason_counts.get(
            "execution_report_materialized_companion_binding_mismatch", 0
        )
    )
    companion_binding_mismatch_dates = sorted(
        {
            str(row.get("target_date") or "")
            for row in rolling_exclusions
            if isinstance(row, Mapping)
            and row.get("reason")
            == "execution_report_materialized_companion_binding_mismatch"
            and str(row.get("target_date") or "")
        }
    )
    lifecycle_exact_join_missing_count = sum(
        1
        for row in rolling_exclusions
        if isinstance(row, Mapping)
        and row.get("reason") == "lifecycle_exact_join_missing"
        and row.get("repair_required") is not False
    )
    lifecycle_exact_join_missing_dates = sorted(
        {
            str(row.get("target_date") or "")
            for row in rolling_exclusions
            if isinstance(row, Mapping)
            and row.get("reason") == "lifecycle_exact_join_missing"
            and row.get("repair_required") is not False
            and str(row.get("target_date") or "")
        }
    )
    natural_entry_non_order_lifecycle_not_applicable_count = int(
        rolling_reason_counts.get("lifecycle_not_applicable_non_order_entry", 0)
    )
    workorders: list[dict[str, Any]] = []
    blocker_codes: list[str] = []

    def add_workorder(
        owner: str, reason_codes: list[str], acceptance_test: str
    ) -> None:
        content = {
            "target_date": target_date,
            "owner": owner,
            "reason_codes": reason_codes,
            "acceptance_test": acceptance_test,
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
        }
        workorders.append(
            {
                "schema": "main_ai_quality_source_only_gap_workorder_v1",
                "workorder_id": f"main-ai-gap-{_sha256(content)[:24]}",
                "status": "open_source_producer_repair",
                **content,
            }
        )

    observer_status = str(observer_canary.get("status") or "")
    if bridge_available and observer_status in {
        "missing_exact_date_canary",
        "invalid_exact_date_canary_contract",
        "invalid_exact_date_canary_authority",
        "warming_up",
        "stop_required",
        "row_exclusion_required",
    }:
        blocker_codes.append(f"micro_observer_canary_{observer_status}")
        add_workorder(
            "MicroReversionForwardCollectorContinuity",
            [observer_status, f"past_market_row_missing={past_market_missing}"],
            (
                "exact-date canary remains pass or row-exclusion-only through close; "
                "later clean windows continue collecting; provider replay remains held until "
                "queue-loss scope has an exact exclusion receipt or the next clean date"
            ),
        )
    if bridge_available and micro_eligible <= 0 and route_proof_missing > 0:
        blocker_codes.append(
            f"micro_integrated_route_proof_missing:{route_proof_missing}"
        )
        add_workorder(
            "MicroReversionIntegratedRouteProof",
            [f"integrated_route_proof_missing={route_proof_missing}"],
            (
                "same-request exact snapshot carries verified integrated-route proof; "
                "ambiguous SOR rows remain excluded without inferred venue"
            ),
        )
    current_lifecycle_receipt_gap = bool(
        lifecycle_available
        and lifecycle_eligible <= 0
        and (
            lifecycle_gap > 0
            or lifecycle_pipeline_gap > 0
            or (lifecycle_real_submitted > 0 and lifecycle_broker_execution_unique <= 0)
        )
    )
    if current_lifecycle_receipt_gap:
        if lifecycle_gap > 0:
            blocker_codes.append(
                f"main_lifecycle_broker_execution_provenance_gap:{lifecycle_gap}"
            )
        else:
            blocker_codes.append(
                "main_lifecycle_execution_receipt_custody_gap:"
                f"{max(lifecycle_pipeline_gap, lifecycle_real_submitted)}"
            )
    if current_lifecycle_receipt_gap or lifecycle_exact_join_missing_count > 0:
        reason_codes = []
        if current_lifecycle_receipt_gap and lifecycle_gap > 0:
            reason_codes.append(
                f"broker_execution_provenance_gap_count={lifecycle_gap}"
            )
        if current_lifecycle_receipt_gap and lifecycle_pipeline_gap > 0:
            reason_codes.append(
                f"pipeline_lifecycle_instrumentation_gap_count={lifecycle_pipeline_gap}"
            )
        if current_lifecycle_receipt_gap and lifecycle_real_submitted > 0:
            reason_codes.extend(
                [
                    f"real_submitted_lifecycle_count={lifecycle_real_submitted}",
                    "broker_execution_unique_count="
                    f"{lifecycle_broker_execution_unique}",
                ]
            )
        if lifecycle_exact_join_missing_count > 0:
            reason_codes.append(
                "lifecycle_exact_join_missing_count="
                f"{lifecycle_exact_join_missing_count}"
            )
            if lifecycle_exact_join_missing_dates:
                reason_codes.append(
                    "lifecycle_exact_join_missing_dates="
                    + ",".join(lifecycle_exact_join_missing_dates)
                )
        add_workorder(
            "RuntimeExecutionReceiptCustodyRepair",
            reason_codes,
            (
                "official raw execution envelope/order/execution identity is complete for "
                "each repair-required lifecycle or the affected row remains explicitly "
                "excluded; custody and order authority remain unchanged"
            ),
        )
    if companion_binding_mismatch_count > 0:
        companion_reason_codes = [
            "execution_report_materialized_companion_binding_mismatch_count="
            f"{companion_binding_mismatch_count}"
        ]
        if companion_binding_mismatch_dates:
            companion_reason_codes.append(
                "execution_report_materialized_companion_binding_mismatch_dates="
                + ",".join(companion_binding_mismatch_dates)
            )
        add_workorder(
            "MainAIQualityMaterializedCompanionBindingRepair",
            companion_reason_codes,
            (
                "each affected execution report binds the exact materialized request and "
                "response companion hashes for its own source date; unchanged immutable "
                "historical rows remain excluded and no runtime or order authority changes"
            ),
        )
    if contract_findings:
        blocker_codes.append("source_gap_diagnostics_contract_invalid")
    return {
        "schema": "main_ai_quality_source_only_gap_diagnostics_v1",
        "target_date": target_date,
        "bridge_micro_eligible_count": micro_eligible,
        "past_market_row_missing_count": past_market_missing,
        "integrated_route_proof_missing_count": route_proof_missing,
        "lifecycle_promotion_eligible_count": lifecycle_eligible,
        "broker_execution_provenance_gap_count": lifecycle_gap,
        "pipeline_lifecycle_instrumentation_gap_count": lifecycle_pipeline_gap,
        "real_submitted_lifecycle_count": lifecycle_real_submitted,
        "broker_execution_unique_count": lifecycle_broker_execution_unique,
        "lifecycle_receipt_custody_gap_example_count": len(
            lifecycle_receipt_custody_gap_examples
        ),
        "lifecycle_receipt_custody_gap_examples": (
            lifecycle_receipt_custody_gap_examples
        ),
        "lifecycle_receipt_custody_gap_examples_sha256": _sha256(
            lifecycle_receipt_custody_gap_examples
        ),
        "lifecycle_source_path": (
            (lifecycle_report or {}).get("source_path") if lifecycle_available else None
        ),
        "lifecycle_source_raw_sha256": (
            (lifecycle_report or {}).get("source_raw_sha256")
            if lifecycle_available
            else None
        ),
        "execution_report_materialized_companion_binding_mismatch_count": (
            companion_binding_mismatch_count
        ),
        "execution_report_materialized_companion_binding_mismatch_dates": (
            companion_binding_mismatch_dates
        ),
        "lifecycle_exact_join_missing_count": lifecycle_exact_join_missing_count,
        "lifecycle_exact_join_missing_dates": lifecycle_exact_join_missing_dates,
        "natural_entry_non_order_lifecycle_not_applicable_count": (
            natural_entry_non_order_lifecycle_not_applicable_count
        ),
        "contract_findings": sorted(set(contract_findings)),
        "blocker_codes": blocker_codes,
        "workorders": workorders,
        **OFFLINE_AUTHORITY,
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
    profiles = cost.get("profiles")
    if not isinstance(profiles, list) or not profiles:
        raise ValueError("economic_reference_cost_profiles_missing")
    for profile in profiles:
        if not isinstance(profile, Mapping):
            raise ValueError("economic_reference_cost_profile_invalid")
        if (
            float(profile.get("buy_fee_bps")) != 1.5
            or float(profile.get("sell_fee_bps")) != 1.5
            or float(profile.get("statutory_sell_tax_bps")) != 20.0
            or float(profile.get("uncertainty_buffer_bps")) != 0.0
            or profile.get("listing_markets") not in (["KOSPI"], ["KOSDAQ"])
            or profile.get("instrument_types") != ["EQUITY"]
            or profile.get("instrument_tax_classes")
            != ["ordinary_taxable_equity_20bps"]
        ):
            raise ValueError("economic_reference_cost_policy_mismatch")
    records = master.get("records")
    if not isinstance(records, list) or not records:
        raise ValueError("economic_reference_symbol_records_missing")
    for record in records:
        if not isinstance(record, Mapping) or (
            record.get("listing_market") not in {"KOSPI", "KOSDAQ"}
            or record.get("instrument_type") != "EQUITY"
            or record.get("instrument_tax_class") != "ordinary_taxable_equity_20bps"
        ):
            raise ValueError("economic_reference_symbol_scope_mismatch")
    return dict(cost), dict(master)


def _validate_economic_owner_report(
    report: Mapping[str, Any],
    *,
    target_date: str,
    policy_path: Path,
    manifest_path: Path,
    pricing_path: Path,
    owner_report_path: Path | None = None,
) -> dict[str, Any]:
    from src.engine.scalping.micro_reversion.economic_reference import content_sha256
    from src.engine.scalping.micro_reversion.economic_reference_owner import (
        OWNER_REPORT_SCHEMA,
    )

    if report.get("schema") != OWNER_REPORT_SCHEMA:
        raise ValueError("economic_owner_report_schema_invalid")
    if report.get("target_date") != target_date or report.get("status") != "pass":
        raise ValueError("economic_owner_report_target_or_status_invalid")
    try:
        generated_at = datetime.fromisoformat(str(report.get("generated_at") or ""))
    except ValueError as exc:
        raise ValueError("economic_owner_report_generated_at_invalid") from exc
    if generated_at.tzinfo is None or generated_at.astimezone(
        KST
    ).date().isoformat() != (target_date):
        raise ValueError("economic_owner_report_generated_at_invalid")
    declared_hash = str(report.get("artifact_content_sha256") or "")
    body = {
        key: item for key, item in report.items() if key != "artifact_content_sha256"
    }
    if not declared_hash or declared_hash != content_sha256(body):
        raise ValueError("economic_owner_report_content_hash_mismatch")
    if (
        report.get("decision_authority") != "offline_economic_reference_source_only"
        or _authority_findings(report)
        or report.get("provider_call_performed") is not False
    ):
        raise ValueError("economic_owner_report_authority_invalid")
    validated_sources: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
    for field, path, hash_field, size_field in (
        (
            "policy_path",
            policy_path,
            "policy_sha256",
            None,
        ),
        (
            "economic_manifest_path",
            manifest_path,
            "economic_manifest_sha256",
            "economic_manifest_size_bytes",
        ),
        (
            "provider_pricing_path",
            pricing_path,
            "provider_pricing_sha256",
            "provider_pricing_size_bytes",
        ),
    ):
        logical_path = path.absolute()
        if Path(str(report.get(field) or "")).absolute() != logical_path:
            raise ValueError(f"economic_owner_report_path_mismatch:{field}")
        payload, provenance = _load_json_with_raw_artifact(logical_path)
        validated_sources[field] = (payload, provenance)
        if report.get(hash_field) != provenance.get("stored_sha256"):
            raise ValueError(f"economic_owner_report_hash_mismatch:{field}")
        if size_field is not None and report.get(size_field) != provenance.get(
            "stored_size_bytes"
        ):
            raise ValueError(f"economic_owner_report_size_mismatch:{field}")
    if (
        not isinstance(report.get("eligible_common_stock_count"), int)
        or report.get("eligible_common_stock_count", 0) <= 0
        or report.get("eligible_common_stock_count")
        != report.get("eligible_kospi_count", -1)
        + report.get("eligible_kosdaq_count", -1)
    ):
        raise ValueError("economic_owner_report_symbol_census_invalid")
    budget_basis = report.get("provider_budget_basis")
    if not isinstance(budget_basis, Mapping) or (
        budget_basis.get("evaluated_call_median") != 781
        or budget_basis.get("target_share_of_evaluated_median_pct") != 50.0
        or budget_basis.get("daily_parent_cap") != DEFAULT_PARENT_CAP
        or budget_basis.get("logical_requests_per_parent") != len(EXPECTED_ARMS)
        or budget_basis.get("maximum_logical_request_count")
        != DEFAULT_PARENT_CAP * len(EXPECTED_ARMS)
        or budget_basis.get("daily_attempt_cap") != DEFAULT_DAILY_ATTEMPT_CAP
        or not isinstance(budget_basis.get("source_artifacts"), list)
        or len(budget_basis["source_artifacts"]) != 5
    ):
        raise ValueError("economic_owner_report_budget_basis_invalid")
    pricing_payload, pricing_provenance = validated_sources["provider_pricing_path"]
    pricing_content_sha256 = str(pricing_payload.get("artifact_content_sha256") or "")
    if (
        not _valid_sha256(pricing_content_sha256)
        or report.get("provider_pricing_content_sha256") != pricing_content_sha256
    ):
        raise ValueError("economic_owner_report_pricing_content_hash_mismatch")
    return {
        "schema": PROVIDER_AUTHORITY_BINDING_SCHEMA,
        "target_date": target_date,
        "economic_owner_report_path": (
            str(owner_report_path.absolute()) if owner_report_path is not None else ""
        ),
        "economic_owner_report_artifact_content_sha256": declared_hash,
        "provider_pricing_logical_path": str(pricing_path.absolute()),
        "provider_pricing_file_sha256": str(pricing_provenance["stored_sha256"]),
        "provider_pricing_file_size_bytes": int(
            pricing_provenance["stored_size_bytes"]
        ),
        "provider_pricing_artifact_content_sha256": pricing_content_sha256,
    }


def _validate_existing_economic_reference(
    report: Mapping[str, Any],
    *,
    target_date: str,
    manifest_path: Path,
) -> None:
    if report.get("target_date") != target_date or report.get("status") not in {
        "pass",
        "partial",
    }:
        raise ValueError("existing_economic_reference_target_or_status_invalid")
    if report.get("tuning_input_allowed") is not True:
        raise ValueError("existing_economic_reference_tuning_input_blocked")
    _economic_outputs(report)
    source_manifest = report.get("source_manifest")
    if not isinstance(source_manifest, Mapping):
        raise ValueError("existing_economic_reference_source_manifest_missing")
    raw = manifest_path.read_bytes()
    if (
        Path(str(source_manifest.get("resolved_path") or "")).resolve()
        != manifest_path.resolve()
        or source_manifest.get("sha256") != _sha256(raw)
        or source_manifest.get("size_bytes") != len(raw)
    ):
        raise ValueError("existing_economic_reference_source_manifest_mismatch")


def _execution_provider_floor_logical_path(
    report: Mapping[str, Any], *, execution_target_date: str
) -> Path | None:
    """Resolve only a canonical same/later-date floor referenced by a result."""

    declared = str(report.get("provider_ablation_sample_floor_path") or "")
    match = re.fullmatch(
        r"micro_reversion_provider_ablation_sample_floor_(\d{4}-\d{2}-\d{2})\.json",
        Path(declared).name,
    )
    if not declared or match is None:
        return None
    floor_target_date = match.group(1)
    try:
        if date.fromisoformat(floor_target_date) < date.fromisoformat(
            execution_target_date
        ):
            return None
    except ValueError:
        return None
    expected = provider_ablation_floor_path(floor_target_date).absolute()
    if Path(declared).absolute() != expected:
        return None
    return expected


def _collect_rolling_inputs(
    *, target_date: str, lookback_calendar_days: int = 60
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, bool],
    dict[str, bool],
    dict[str, dict[str, Any]],
    list[dict[str, Any]],
]:
    target = date.fromisoformat(target_date)
    execution_reports: list[dict[str, Any]] = []
    lifecycle_reports: list[dict[str, Any]] = []
    source_quality_pass: dict[str, bool] = {}
    economic_reference_pass: dict[str, bool] = {}
    outcome_label_artifacts: dict[str, dict[str, Any]] = {}
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
            if not _artifact_path_present(resolved):
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
            elif name == "economic_reference":
                try:
                    _economic_outputs(artifact)
                    economic_reference_pass[date_key] = bool(
                        artifact.get("status") in {"pass", "partial"}
                        and artifact.get("tuning_input_allowed") is True
                    )
                except (TypeError, ValueError):
                    economic_reference_pass[date_key] = False
        label_path = existing_or_gzip_path(action_neutral_label_path(date_key))
        bridge_path = existing_or_gzip_path(
            BRIDGE_REPORT_ROOT / f"micro_reversion_ai_quality_bridge_{date_key}.json"
        )
        materialized_path = existing_or_gzip_path(
            quality.micro_reversion_materialized_request_path(date_key)
        )
        source_bundle_path = existing_or_gzip_path(
            quality.micro_reversion_source_bundle_path(date_key)
        )
        prepared_path = existing_or_gzip_path(prepared_request_path(date_key))
        paired_path = existing_or_gzip_path(
            quality.PAIRED_REPORT_DIR / f"ai_prompt_paired_replay_{date_key}.json"
        )
        checkpoint_path = existing_or_gzip_path(
            quality.micro_reversion_execution_checkpoint_path(date_key)
        )
        execution_report_for_date = next(
            (
                report
                for report in execution_reports
                if str(report.get("target_date") or "") == date_key
            ),
            None,
        )
        execution_collected_for_date = execution_report_for_date is not None
        provider_floor_logical_path = (
            _execution_provider_floor_logical_path(
                execution_report_for_date,
                execution_target_date=date_key,
            )
            if execution_report_for_date is not None
            else None
        )
        provider_floor_path = (
            existing_or_gzip_path(provider_floor_logical_path)
            if provider_floor_logical_path is not None
            else None
        )
        if execution_collected_for_date and (
            _artifact_path_present(label_path)
            or _artifact_path_present(bridge_path)
            or _artifact_path_present(materialized_path)
            or _artifact_path_present(source_bundle_path)
            or _artifact_path_present(prepared_path)
            or _artifact_path_present(paired_path)
            or _artifact_path_present(checkpoint_path)
            or (
                provider_floor_path is not None
                and _artifact_path_present(provider_floor_path)
            )
        ):
            outcome_label_artifacts[date_key] = {
                "outcome_label_path": (
                    str(label_path) if _artifact_path_present(label_path) else None
                ),
                "source_bridge_path": (
                    str(bridge_path) if _artifact_path_present(bridge_path) else None
                ),
                "materialized_report_path": (
                    str(materialized_path)
                    if _artifact_path_present(materialized_path)
                    else None
                ),
                "source_bundle_path": (
                    str(source_bundle_path)
                    if _artifact_path_present(source_bundle_path)
                    else None
                ),
                "prepared_artifact_path": (
                    str(prepared_path)
                    if _artifact_path_present(prepared_path)
                    else None
                ),
                "paired_report_path": (
                    str(paired_path) if _artifact_path_present(paired_path) else None
                ),
                "checkpoint_artifact_path": (
                    str(quality.micro_reversion_execution_checkpoint_path(date_key))
                    if _artifact_path_present(checkpoint_path)
                    else None
                ),
                "provider_ablation_floor_artifact_path": (
                    str(provider_floor_logical_path)
                    if provider_floor_path is not None
                    and _artifact_path_present(provider_floor_path)
                    else None
                ),
                "lazy_load_one_date_at_a_time": True,
            }
    return (
        execution_reports,
        lifecycle_reports,
        source_quality_pass,
        economic_reference_pass,
        outcome_label_artifacts,
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


def _historical_backfill_dates(
    *,
    provider_floor: Mapping[str, Any],
    current_target_date: str,
    daily_attempt_cap: int,
    parent_cap: int,
) -> list[str]:
    """Return the oldest bounded dates that can receive one A/B/C parent.

    Capacity is applied after exact covered-date discovery so older completed
    dates cannot starve the next missing date.  The physical KST ledger remains
    the authoritative attempt/USD/parent guard.  Discover from the union of
    canonical passing floors in the reviewed 30-calendar-day window: otherwise
    an unfinished date disappears as soon as it rolls out of today's five-day
    floor and can never be resumed.
    """

    if (
        provider_floor.get("pass") is not True
        or provider_floor.get("status") != "pass_provider_ablation_floor_met"
        or provider_floor.get("target_date") != current_target_date
    ):
        return []
    if daily_attempt_cap <= 0 or parent_cap <= 0:
        return []
    current = date.fromisoformat(current_target_date)
    activation = date.fromisoformat(CURRENT_DESIGN_ACTIVATION_DATE)
    scan_start = max(
        activation,
        current - timedelta(days=PROVIDER_ABLATION_FLOOR_LOOKBACK_CALENDAR_DAYS - 1),
    )
    floors: list[Mapping[str, Any]] = []
    for offset in range((current - scan_start).days + 1):
        floor_date = (scan_start + timedelta(days=offset)).isoformat()
        logical_path = provider_ablation_floor_path(floor_date).absolute()
        if floor_date == current_target_date:
            floor = provider_floor
        elif _artifact_path_present(existing_or_gzip_path(logical_path)):
            floor = _load_json_auto(logical_path)
        else:
            continue
        if not isinstance(floor, Mapping):
            raise ValueError("historical_backfill_floor_not_object")
        if floor.get("target_date") != floor_date or floor.get(
            "floor_content_sha256"
        ) != _content_hash(floor, "floor_content_sha256"):
            raise ValueError("historical_backfill_floor_hash_or_date_mismatch")
        if (
            floor.get("pass") is True
            and floor.get("status") == "pass_provider_ablation_floor_met"
        ):
            floors.append(floor)

    candidates: list[str] = []
    for floor in floors:
        for entry in floor.get("included_artifacts") or []:
            if not isinstance(entry, Mapping) or not entry.get("parent_count"):
                continue
            date_key = str(entry.get("target_date") or "")
            try:
                eligible = activation <= date.fromisoformat(date_key) < current
            except ValueError:
                eligible = False
            if eligible:
                candidates.append(date_key)
    return sorted(set(candidates))


def _historical_backfill_parent_slot_limit(
    *, daily_attempt_cap: int, parent_cap: int
) -> int:
    """Reserve one retry-worst-case complete parent for the current date."""

    worst_case_attempts_per_parent = (
        len(arm_set_for_design(CURRENT_DESIGN_VERSION))
        * quality.CANDIDATE_SCHEMA_MAX_ATTEMPTS
    )
    return min(
        max(0, parent_cap - 1),
        max(0, daily_attempt_cap // worst_case_attempts_per_parent - 1),
    )


def _provider_execute_command(
    *,
    target_date: str,
    selected_paths: Mapping[str, Path],
    provider_authority_binding: Mapping[str, Any],
    provider_floor_path: Path,
    daily_attempt_cap: int,
    daily_usd_cap_text: str,
    max_new_requests: int,
    write: bool,
) -> list[str]:
    command = [
        sys.executable,
        "-m",
        "src.engine.scalping.ai_decision_quality",
        "--date",
        target_date,
        "--mode",
        "micro_reversion_execute",
        "--micro-reversion-materialized-requests",
        str(selected_paths["materialized"]),
        "--micro-reversion-paired-report",
        str(selected_paths["paired_report"]),
        "--micro-reversion-prepared-requests",
        str(selected_paths["prepared"]),
        "--micro-reversion-source-bundle",
        str(selected_paths["source_bundle"]),
        "--micro-reversion-outcome-labels",
        str(selected_paths["labels"]),
        "--micro-reversion-bridge-report",
        str(selected_paths["bridge_report"]),
        "--micro-reversion-provider-pricing",
        str(selected_paths["provider_pricing"]),
        "--micro-reversion-economic-owner-report",
        str(provider_authority_binding["economic_owner_report_path"]),
        "--micro-reversion-economic-owner-report-content-sha256",
        str(
            provider_authority_binding["economic_owner_report_artifact_content_sha256"]
        ),
        "--micro-reversion-provider-pricing-file-sha256",
        str(provider_authority_binding["provider_pricing_file_sha256"]),
        "--micro-reversion-provider-pricing-content-sha256",
        str(provider_authority_binding["provider_pricing_artifact_content_sha256"]),
        "--micro-reversion-provider-ablation-floor",
        str(provider_floor_path),
        "--micro-reversion-storage-capacity-status",
        str(selected_paths["capacity_status"]),
        "--micro-reversion-provider-daily-attempt-cap",
        str(daily_attempt_cap),
        "--micro-reversion-provider-daily-usd-cap",
        daily_usd_cap_text,
        "--execute-candidate",
        "--candidate-workers",
        "1",
        "--candidate-max-new-requests",
        str(max_new_requests),
    ]
    if write:
        command.append("--write")
    return command


def _load_historical_backfill_context(
    *,
    target_date: str,
    provider_floor: Mapping[str, Any],
    include_provider_authority: bool = True,
) -> dict[str, Any]:
    """Strictly capture one frozen historical execution generation."""

    selected_paths = _default_paths(target_date)
    materialized = _load_json_auto(selected_paths["materialized"])
    source_bundle = _load_json_auto(selected_paths["source_bundle"])
    prepared = _load_json_auto(selected_paths["prepared"])
    bridge = _load_json_auto(selected_paths["bridge_report"])
    paired = _load_json_auto(selected_paths["paired_report"])
    labels = _load_json_auto(selected_paths["labels"])
    _validate_materialized_step_artifact(
        materialized,
        target_date=target_date,
        source_bundle_report=source_bundle,
        prepared_artifact=prepared,
        source_bridge_report=bridge,
        paired_report=paired,
    )
    floor_target_date = str(provider_floor.get("target_date") or "")
    quality.validate_micro_reversion_provider_ablation_floor_artifact(
        provider_floor,
        expected_target_date=floor_target_date,
        current_materialized_report=materialized,
        expected_materialized_target_date=target_date,
    )
    quality._validate_micro_reversion_outcome_label_artifact(
        labels,
        source_bridge_report=bridge,
        expected_design_version=CURRENT_DESIGN_VERSION,
        expected_target_date=target_date,
        expected_materialized_report_content_sha256=materialized.get(
            "report_content_sha256"
        ),
        expected_materialized_report=materialized,
    )
    provider_binding: dict[str, Any] | None = None
    if include_provider_authority:
        owner_report = _load_json_auto(selected_paths["economic_owner_report"])
        provider_binding = _validate_economic_owner_report(
            owner_report,
            target_date=target_date,
            owner_report_path=selected_paths["economic_owner_report"],
            policy_path=selected_paths["economic_policy"],
            manifest_path=selected_paths["economic_source_manifest"],
            pricing_path=selected_paths["provider_pricing"],
        )
    checkpoint_path = selected_paths["execution_checkpoint"]
    checkpoint_record_dir = quality._micro_reversion_checkpoint_record_dir(
        checkpoint_path
    )
    checkpoint_present = any(
        candidate.exists() or candidate.is_symlink()
        for candidate in (
            checkpoint_path,
            checkpoint_path.with_name(checkpoint_path.name + ".gz"),
            checkpoint_record_dir,
        )
    )
    checkpoint = (
        quality._load_micro_reversion_checkpoint(
            checkpoint_path,
            repair_manifest=False,
        )
        if checkpoint_present
        else None
    )
    return {
        "paths": selected_paths,
        "materialized": materialized,
        "source_bundle": source_bundle,
        "prepared": prepared,
        "bridge": bridge,
        "paired": paired,
        "labels": labels,
        "checkpoint": checkpoint,
        "provider_authority_binding": provider_binding,
    }


def _checkpoint_provider_reservation_bindings(
    *,
    target_date: str,
    context: Mapping[str, Any],
    provider_floor: Mapping[str, Any],
) -> dict[tuple[str, str], dict[str, Any]]:
    """Delegate exact checkpoint custody to the leaf execution owner."""

    materialized = context.get("materialized")
    labels = context.get("labels")
    if not isinstance(materialized, dict) or not isinstance(labels, Mapping):
        raise ValueError("historical_backfill_checkpoint_companions_missing")
    return quality._micro_reversion_provider_checkpoint_bindings(
        target_date=target_date,
        materialized_report=materialized,
        outcome_label_artifact=labels,
        checkpoint_artifact=context.get("checkpoint"),
        provider_ablation_sample_floor_content_sha256=str(
            provider_floor.get("floor_content_sha256") or ""
        ),
    )


def _historical_backfill_orphan_reservation_findings(
    *,
    target_date: str,
    context: Mapping[str, Any],
    provider_floor: Mapping[str, Any],
    daily_attempt_cap: int,
    daily_usd_cap: Decimal,
    physical_execution_date: date | None = None,
) -> list[str]:
    """Use the common leaf/cycle cross-physical-day idempotency gate."""

    materialized = context.get("materialized")
    labels = context.get("labels")
    selected_paths = context.get("paths")
    if (
        not isinstance(materialized, dict)
        or not isinstance(labels, Mapping)
        or not isinstance(selected_paths, Mapping)
        or not isinstance(selected_paths.get("provider_pricing"), Path)
    ):
        raise ValueError("historical_backfill_orphan_scan_context_invalid")
    return quality._micro_reversion_prior_physical_ledger_findings(
        target_date=target_date,
        materialized_report=materialized,
        outcome_label_artifact=labels,
        checkpoint_artifact=context.get("checkpoint"),
        provider_ablation_sample_floor_content_sha256=str(
            provider_floor.get("floor_content_sha256") or ""
        ),
        reviewed_pricing_path=selected_paths["provider_pricing"],
        daily_attempt_cap=daily_attempt_cap,
        daily_usd_cap=daily_usd_cap,
        physical_execution_date=physical_execution_date,
    )


def _historical_backfill_floor(
    *,
    target_date: str,
    current_target_date: str,
    current_floor: Mapping[str, Any],
) -> tuple[Path, dict[str, Any]]:
    """Select the oldest exact floor, preserving any persisted hash binding."""

    selected_paths = _default_paths(target_date)
    bound_floor_path: Path | None = None
    bound_floor_hashes: set[str] = set()
    execution_path = selected_paths["execution"]
    if _artifact_path_present(existing_or_gzip_path(execution_path)):
        existing_report = _load_json_auto(execution_path)
        if existing_report.get("report_content_sha256") != _content_hash(
            existing_report, "report_content_sha256"
        ):
            raise ValueError("historical_backfill_execution_hash_mismatch")
        bound_floor_path = _execution_provider_floor_logical_path(
            existing_report,
            execution_target_date=target_date,
        )
        declared_floor_hash = str(
            existing_report.get("provider_ablation_sample_floor_content_sha256") or ""
        )
        if bound_floor_path is None or not _valid_sha256(declared_floor_hash):
            raise ValueError("historical_backfill_execution_floor_binding_invalid")
        bound_floor_hashes.add(declared_floor_hash)

    checkpoint_path = selected_paths["execution_checkpoint"]
    checkpoint_record_dir = quality._micro_reversion_checkpoint_record_dir(
        checkpoint_path
    )
    checkpoint_present = any(
        candidate.exists() or candidate.is_symlink()
        for candidate in (
            checkpoint_path,
            checkpoint_path.with_name(checkpoint_path.name + ".gz"),
            checkpoint_record_dir,
        )
    )
    if checkpoint_present:
        checkpoint = quality._load_micro_reversion_checkpoint(
            checkpoint_path,
            repair_manifest=False,
        )
        checkpoint_results = checkpoint.get("results") or []
        if not isinstance(checkpoint_results, list):
            raise ValueError("historical_backfill_checkpoint_result_census_invalid")
        for result in checkpoint_results:
            value = (
                str(result.get("provider_ablation_sample_floor_content_sha256") or "")
                if isinstance(result, Mapping)
                else ""
            )
            if not _valid_sha256(value):
                raise ValueError("historical_backfill_checkpoint_floor_binding_invalid")
            bound_floor_hashes.add(value)
        if len(bound_floor_hashes) > 1:
            raise ValueError("historical_backfill_checkpoint_floor_binding_conflict")

    target = date.fromisoformat(target_date)
    current = date.fromisoformat(current_target_date)
    candidates: list[tuple[Path, dict[str, Any]]] = []
    for offset in range((current - target).days + 1):
        floor_date = (target + timedelta(days=offset)).isoformat()
        logical_path = provider_ablation_floor_path(floor_date).absolute()
        if bound_floor_path is not None and logical_path != bound_floor_path:
            continue
        if floor_date == current_target_date:
            floor = dict(current_floor)
        elif _artifact_path_present(existing_or_gzip_path(logical_path)):
            floor = _load_json_auto(logical_path)
        else:
            continue
        content_hash = str(floor.get("floor_content_sha256") or "")
        if floor.get("target_date") != floor_date or content_hash != _content_hash(
            floor, "floor_content_sha256"
        ):
            raise ValueError("historical_backfill_floor_hash_or_date_mismatch")
        if bound_floor_hashes and content_hash not in bound_floor_hashes:
            if bound_floor_path is not None:
                raise ValueError("historical_backfill_floor_hash_binding_mismatch")
            continue
        if floor.get("pass") is not True:
            continue
        included_dates = {
            str(entry.get("target_date") or "")
            for entry in floor.get("included_artifacts") or []
            if isinstance(entry, Mapping) and int(entry.get("parent_count") or 0) > 0
        }
        if target_date not in included_dates:
            continue
        candidates.append((logical_path, floor))
        break
    if not candidates:
        raise ValueError("historical_backfill_exact_floor_unavailable")
    return candidates[0]


def _historical_backfill_already_covered(
    *,
    target_date: str,
    context: Mapping[str, Any],
    provider_floor: Mapping[str, Any],
) -> bool:
    execution_path = context["paths"]["execution"]
    if not _artifact_path_present(existing_or_gzip_path(execution_path)):
        return False
    report = _load_json_auto(execution_path)
    try:
        _validated_execution_rows(
            report,
            outcome_label_artifact=context["labels"],
            source_bridge_report=context["bridge"],
            materialized_report=context["materialized"],
            source_bundle_report=context["source_bundle"],
            prepared_artifact=context["prepared"],
            paired_report=context["paired"],
            checkpoint_artifact=context["checkpoint"],
            provider_ablation_floor_artifact=provider_floor,
        )
    except ValueError as exc:
        if (
            str(exc) != "execution_report_not_complete_provider_verified"
            or report.get("status")
            != "offline_three_arm_execution_complete_with_failures_or_exclusions"
            or not isinstance(context.get("checkpoint"), Mapping)
        ):
            raise
        # A failed/excluded terminal report is resumable only from its external
        # append-only checkpoint.  The general validator above already rebuilt
        # its exact materialized/source/floor lineage before reaching the
        # terminal-status rejection; this companion validator now proves the
        # committed/deferred census against that same immutable journal.
        quality.validate_current_micro_reversion_checkpoint_companion(
            report=report,
            checkpoint_artifact=context["checkpoint"],
            materialized_report=context["materialized"],
            outcome_labels=list(context["labels"].get("labels") or []),
        )
        if str(report.get("target_date") or "") != target_date:
            raise ValueError("historical_backfill_execution_target_mismatch")
        return False
    if str(report.get("target_date") or "") != target_date:
        raise ValueError("historical_backfill_execution_target_mismatch")
    status = str(report.get("status") or "")
    if status == "offline_three_arm_execution_complete":
        return True
    if status == "offline_three_arm_execution_batch_complete":
        return False
    raise ValueError("historical_backfill_execution_status_not_resumable")


def _run_bounded_historical_provider_backfill(
    *,
    current_target_date: str,
    current_floor: Mapping[str, Any],
    write: bool,
    daily_attempt_cap: int,
    daily_usd_cap: Decimal,
    daily_usd_cap_text: str,
    parent_cap: int,
    command_runner: CommandRunner,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int, bool, list[str]]:
    """Backfill one oldest missing full parent per floor-building date."""

    steps: list[dict[str, Any]] = []
    admissions: list[dict[str, Any]] = []
    selected_parent_slots = 0
    any_provider_call_performed = False
    blockers: list[str] = []
    if not write:
        return steps, admissions, selected_parent_slots, False, blockers

    parent_slot_limit = _historical_backfill_parent_slot_limit(
        daily_attempt_cap=daily_attempt_cap,
        parent_cap=parent_cap,
    )
    if parent_slot_limit <= 0:
        return steps, admissions, 0, False, blockers
    try:
        historical_dates = _historical_backfill_dates(
            provider_floor=current_floor,
            current_target_date=current_target_date,
            daily_attempt_cap=daily_attempt_cap,
            parent_cap=parent_cap,
        )
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        blockers.append(
            f"historical_provider_backfill_discovery_blocked:{type(exc).__name__}:{exc}"
        )
        return steps, admissions, 0, False, blockers

    for historical_date in historical_dates:
        try:
            floor_path, provider_floor = _historical_backfill_floor(
                target_date=historical_date,
                current_target_date=current_target_date,
                current_floor=current_floor,
            )
            context = _load_historical_backfill_context(
                target_date=historical_date,
                provider_floor=provider_floor,
                include_provider_authority=False,
            )
            admission_body = {
                "schema": "micro_reversion_historical_provider_backfill_admission_v1",
                "evaluation_target_date": historical_date,
                "floor_as_of_date": provider_floor.get("target_date"),
                "provider_floor_path": str(floor_path),
                "provider_floor_content_sha256": provider_floor.get(
                    "floor_content_sha256"
                ),
                "provider_floor_artifact_sha256": _sha256(provider_floor),
                "materialized_report_content_sha256": context["materialized"].get(
                    "report_content_sha256"
                ),
                "materialized_report_artifact_sha256": _sha256(context["materialized"]),
                "materialized_request_census_sha256": (
                    quality._micro_reversion_materialized_request_census_sha256(
                        context["materialized"]
                    )
                ),
                "companion_artifact_sha256s": {
                    role: _sha256(context[role])
                    for role in (
                        "source_bundle",
                        "prepared",
                        "bridge",
                        "paired",
                        "labels",
                    )
                },
                "provider_authority_binding": None,
                "provider_call_performed": False,
                "status": "validated_pending_execution",
                **OFFLINE_AUTHORITY,
            }
            admission = {
                **admission_body,
                "admission_content_sha256": _sha256(admission_body),
            }
            orphan_findings = _historical_backfill_orphan_reservation_findings(
                target_date=historical_date,
                context=context,
                provider_floor=provider_floor,
                daily_attempt_cap=daily_attempt_cap,
                daily_usd_cap=daily_usd_cap,
            )
            if orphan_findings:
                raise ValueError(orphan_findings[0])
            if _historical_backfill_already_covered(
                target_date=historical_date,
                context=context,
                provider_floor=provider_floor,
            ):
                admission_body = {
                    **admission_body,
                    "status": "already_covered_exact_no_call",
                }
                admission = {
                    **admission_body,
                    "admission_content_sha256": _sha256(admission_body),
                }
                admissions.append(admission)
                continue

            if selected_parent_slots >= parent_slot_limit:
                break

            provider_authority_binding = context.get("provider_authority_binding")
            if not isinstance(provider_authority_binding, Mapping):
                owner_report = _load_json_auto(
                    context["paths"]["economic_owner_report"]
                )
                provider_authority_binding = _validate_economic_owner_report(
                    owner_report,
                    target_date=historical_date,
                    owner_report_path=context["paths"]["economic_owner_report"],
                    policy_path=context["paths"]["economic_policy"],
                    manifest_path=context["paths"]["economic_source_manifest"],
                    pricing_path=context["paths"]["provider_pricing"],
                )
            admission_body = {
                **admission_body,
                "provider_authority_binding": provider_authority_binding,
            }

            _capacity_gate, capacity_blocker = _pre_provider_capacity_recheck(
                target=date.fromisoformat(historical_date),
                target_date=historical_date,
                selected_paths=context["paths"],
            )
            if capacity_blocker:
                raise ValueError(capacity_blocker)
            selected_parent_slots += 1
            command = _provider_execute_command(
                target_date=historical_date,
                selected_paths=context["paths"],
                provider_authority_binding=provider_authority_binding,
                provider_floor_path=floor_path,
                daily_attempt_cap=daily_attempt_cap,
                daily_usd_cap_text=daily_usd_cap_text,
                max_new_requests=len(arm_set_for_design(CURRENT_DESIGN_VERSION)),
                write=write,
            )
            step = _command_step(
                name=f"bounded_provider_backfill:{historical_date}",
                command=command,
                runner=command_runner,
            )
            steps.append(step)
            if step["returncode"] not in {0, 2}:
                raise ValueError("historical_provider_backfill_command_failed")
            refreshed = _load_historical_backfill_context(
                target_date=historical_date,
                provider_floor=provider_floor,
            )
            execution_report = _load_json_auto(refreshed["paths"]["execution"])
            _validate_current_execution_artifact(
                report=execution_report,
                target_date=historical_date,
                materialized_report=refreshed["materialized"],
                source_bundle_report=refreshed["source_bundle"],
                prepared_artifact=refreshed["prepared"],
                paired_report=refreshed["paired"],
                outcome_label_artifact=refreshed["labels"],
                source_bridge_report=refreshed["bridge"],
                checkpoint_artifact=refreshed["checkpoint"],
                provider_ablation_floor_artifact=provider_floor,
                expected_max_new_requests=len(
                    arm_set_for_design(CURRENT_DESIGN_VERSION)
                ),
                expected_daily_attempt_cap=daily_attempt_cap,
                expected_daily_usd_cap=daily_usd_cap,
                expected_pricing_content_sha256=str(
                    refreshed["provider_authority_binding"].get(
                        "provider_pricing_artifact_content_sha256"
                    )
                    or ""
                ),
                expected_provider_authority_binding=refreshed[
                    "provider_authority_binding"
                ],
            )
            performed = bool(
                int(execution_report.get("new_result_count") or 0) > 0
                and execution_report.get("provider_call_performed") is True
            )
            any_provider_call_performed = any_provider_call_performed or performed
            admission_body = {
                **admission_body,
                "provider_call_performed": performed,
                "status": "backfill_parent_committed",
            }
            admissions.append(
                {
                    **admission_body,
                    "admission_content_sha256": _sha256(admission_body),
                }
            )
        except (
            FileNotFoundError,
            OSError,
            TypeError,
            ValueError,
            json.JSONDecodeError,
        ) as exc:
            blockers.append(
                "historical_provider_backfill_blocked:"
                f"{historical_date}:{type(exc).__name__}:{exc}"
            )
            break
    return (
        steps,
        admissions,
        selected_parent_slots,
        any_provider_call_performed,
        blockers,
    )


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


def _load_provider_bound_r0_generation(
    *,
    target_date: str,
    selected_paths: Mapping[str, Path],
) -> dict[str, Any] | None:
    """Load an immutable R0 generation once Provider results depend on it.

    A repeated cycle may refresh mutable daily inputs before it reaches the
    materialize/execute leaf.  Once at least one Provider result is committed,
    doing so would strand that receipt against a mixed generation.  Reuse the
    complete exact companion set, or fail closed without rewriting it.
    """

    def positive_native_count(field: str) -> bool:
        value = execution.get(field)
        return isinstance(value, int) and not isinstance(value, bool) and value > 0

    execution_path = selected_paths["execution"]
    execution: dict[str, Any] = {}
    execution_committed = False
    if _artifact_path_present(existing_or_gzip_path(execution_path)):
        execution = _load_json_auto(execution_path)
        execution_content = {
            key: value
            for key, value in execution.items()
            if key != "report_content_sha256"
        }
        if (
            execution.get("schema")
            != quality.MICRO_REVERSION_EXECUTION_RESULT_SCHEMA
            or execution.get("target_date") != target_date
            or execution.get("report_content_sha256") != _sha256(execution_content)
        ):
            raise ValueError("provider_bound_execution_receipt_invalid")
        execution_committed = bool(
            execution.get("provider_call_performed") is True
            or positive_native_count("result_count")
            or positive_native_count("committed_parent_count")
        )

    checkpoint: dict[str, Any] = {}
    checkpoint_results: list[Mapping[str, Any]] = []
    if not execution_committed:
        checkpoint_path = selected_paths.get("execution_checkpoint")
        if checkpoint_path is not None:
            checkpoint_record_dir = quality._micro_reversion_checkpoint_record_dir(
                checkpoint_path
            )
            checkpoint_present = any(
                candidate.exists() or candidate.is_symlink()
                for candidate in (
                    checkpoint_path,
                    checkpoint_path.with_name(f"{checkpoint_path.name}.gz"),
                    checkpoint_record_dir,
                )
            )
            if checkpoint_present:
                try:
                    checkpoint = quality._load_micro_reversion_checkpoint(
                        checkpoint_path,
                        repair_manifest=False,
                    )
                except ValueError as exc:
                    if str(exc) == "micro_reversion_checkpoint_manifest_missing":
                        checkpoint = quality._load_micro_reversion_checkpoint(
                            checkpoint_path,
                            repair_manifest=True,
                        )
                    else:
                        raise
                raw_results = checkpoint.get("results")
                if not isinstance(raw_results, list) or any(
                    not isinstance(result, Mapping) for result in raw_results
                ):
                    raise ValueError("provider_bound_checkpoint_result_census_invalid")
                if any(
                    not str(result.get("outcome_join_key") or "")
                    or not _valid_sha256(
                        result.get("outcome_label_content_sha256")
                    )
                    for result in raw_results
                ):
                    raise ValueError(
                        "provider_bound_checkpoint_outcome_binding_invalid"
                    )
                checkpoint_results = list(raw_results)
                if checkpoint_results and checkpoint.get(
                    "provider_call_performed"
                ) is not True:
                    raise ValueError("provider_bound_checkpoint_call_census_invalid")
    if not execution_committed and not checkpoint_results:
        return None

    materialized = _load_json_auto(selected_paths["materialized"])
    labels = _load_json_auto(selected_paths["labels"])
    source_bundle = _load_json_auto(selected_paths["source_bundle"])
    prepared = _load_json_auto(selected_paths["prepared"])
    bridge = _load_json_auto(selected_paths["bridge_report"])
    paired = _load_json_auto(selected_paths["paired_report"])
    if execution_committed:
        _validate_execution_external_companion_bindings(
            execution,
            materialized_report=materialized,
            outcome_label_artifact=labels,
        )
    elif checkpoint.get("materialized_report_content_sha256") != (
        quality._micro_reversion_materialized_request_census_sha256(materialized)
    ):
        raise ValueError("provider_bound_checkpoint_materialized_mismatch")
    quality.validate_current_materialized_source_lineage(
        materialized_report=materialized,
        source_bundle_report=source_bundle,
        prepared_artifact=prepared,
        source_bridge_report=bridge,
        paired_report=paired,
    )

    path_bindings = [
        (materialized.get("source_bundle_path"), selected_paths["source_bundle"]),
        (
            materialized.get("prepared_request_artifact_path"),
            selected_paths["prepared"],
        ),
    ]
    if execution_committed:
        path_bindings.extend(
            (
                (
                    execution.get("materialized_artifact_path"),
                    selected_paths["materialized"],
                ),
                (execution.get("outcome_label_artifact_path"), selected_paths["labels"]),
            )
        )
    if any(
        not str(declared or "").strip()
        or quality._json_companion_logical_path(Path(str(declared)))
        != quality._json_companion_logical_path(expected)
        for declared, expected in path_bindings
    ):
        raise ValueError("provider_bound_r0_companion_path_mismatch")

    source_commitment = source_bundle.get("outcome_source_commitment")
    if not isinstance(source_commitment, Mapping) or (
        source_commitment.get("bridge_report_content_sha256")
        != bridge.get("artifact_content_sha256")
        or source_commitment.get("bridge_report_artifact_sha256")
        != _sha256(bridge)
    ):
        raise ValueError("provider_bound_bridge_companion_mismatch")
    if prepared.get("source_paired_report_content_sha256") != _sha256(paired):
        raise ValueError("provider_bound_paired_companion_mismatch")

    if checkpoint_results:
        label_rows = labels.get("labels")
        if not isinstance(label_rows, list) or any(
            not isinstance(row, Mapping) for row in label_rows
        ):
            raise ValueError("provider_bound_checkpoint_outcome_census_invalid")
        label_by_id = {
            str(row.get("label_id") or ""): row
            for row in label_rows
            if str(row.get("label_id") or "")
        }
        for result in checkpoint_results:
            join_key = str(result.get("outcome_join_key") or "")
            proof = label_by_id.get(join_key)
            if (
                proof is None
                or result.get("outcome_label_content_sha256") != _sha256(proof)
            ):
                raise ValueError("provider_bound_checkpoint_outcome_mismatch")

    floor_path = (
        _execution_provider_floor_logical_path(
            execution,
            execution_target_date=target_date,
        )
        if execution_committed
        else selected_paths.get("provider_ablation_floor")
    )
    if floor_path is None:
        raise ValueError("provider_bound_floor_companion_path_missing")
    provider_floor = _load_json_auto(floor_path)
    if execution_committed and (
        execution.get("provider_ablation_sample_floor_content_sha256")
        != provider_floor.get("floor_content_sha256")
        or execution.get("provider_ablation_sample_floor_artifact_sha256")
        != _sha256(provider_floor)
    ):
        raise ValueError("provider_bound_floor_companion_mismatch")
    if checkpoint_results:
        quality._micro_reversion_provider_checkpoint_bindings(
            target_date=target_date,
            materialized_report=materialized,
            outcome_label_artifact=labels,
            checkpoint_artifact=checkpoint,
            provider_ablation_sample_floor_content_sha256=str(
                provider_floor.get("floor_content_sha256") or ""
            ),
        )

    return {
        "execution": execution,
        "materialized": materialized,
        "labels": labels,
        "source_bundle": source_bundle,
        "prepared": prepared,
        "bridge": bridge,
        "paired": paired,
        "provider_floor": provider_floor,
        "provider_floor_path": floor_path,
        "checkpoint": checkpoint,
    }


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
    if daily_attempt_cap > DEFAULT_DAILY_ATTEMPT_CAP:
        raise ValueError("daily_attempt_cap_exceeds_reviewed_upper_bound")
    canonical_daily_usd_cap, canonical_daily_usd_cap_text = _canonical_daily_usd_cap(
        daily_usd_cap
    )
    if canonical_daily_usd_cap > DEFAULT_DAILY_USD_CAP:
        raise ValueError("daily_usd_cap_exceeds_reviewed_upper_bound")
    if isinstance(parent_cap, bool) or parent_cap <= 0:
        raise ValueError("parent_cap_must_be_positive")
    if parent_cap > DEFAULT_PARENT_CAP:
        raise ValueError("parent_cap_exceeds_reviewed_upper_bound")

    overrides = dict(paths or {})
    selected_paths = {**_default_paths(target_date), **overrides}
    if "economic_source_manifest" in overrides:
        owner_root = selected_paths["economic_source_manifest"].parent
        if "economic_owner_report" not in overrides:
            selected_paths["economic_owner_report"] = (
                owner_root / "daily" / target_date / "owner_report.json"
            )
        if "provider_pricing" not in overrides:
            selected_paths["provider_pricing"] = owner_root / "provider_pricing.json"
    observer_canary = _observer_canary_diagnostic(
        target_date=target_date,
        latest_path=selected_paths["observer_canary_latest"],
        daily_path=selected_paths["observer_canary_daily"],
    )
    observer_stage_gate = _observer_source_only_stage_gate(observer_canary)
    steps: list[dict[str, Any]] = []
    blockers: list[str] = []
    prepared: dict[str, Any] = {}
    source_bundle: dict[str, Any] = {}
    bridge: dict[str, Any] = {}
    paired_report: dict[str, Any] = {}
    materialized: dict[str, Any] = {}
    labels: dict[str, Any] = {}
    current_execution_report: dict[str, Any] = {}
    current_checkpoint_artifact: dict[str, Any] = {}
    provider_authority_binding: dict[str, Any] = {}
    current_provider_replay_complete = False
    provider_ablation_sample_floor: dict[str, Any] = {
        "schema": PROVIDER_ABLATION_SAMPLE_FLOOR_SCHEMA,
        "target_date": target_date,
        "status": "not_evaluated_provider_replay_not_requested",
        "pass": False,
        "provider_call_performed": False,
        **OFFLINE_AUTHORITY,
    }
    provider_capacity_recheck: dict[str, Any] | None = None
    historical_backfill_admissions: list[dict[str, Any]] = []
    historical_backfill_selected_parent_slots = 0
    historical_backfill_provider_call_performed = False
    provider_bound_r0_generation: dict[str, Any] | None = None
    provider_bound_r0_locked = False

    storage_capacity_gate = _capacity_gate_fail_closed(
        target=target,
        target_date=target_date,
        selected_paths=selected_paths,
    )
    if storage_capacity_gate.get("large_artifact_growth_allowed") is not True:
        blockers.append(
            "large_artifact_growth_blocked:"
            f"{str(storage_capacity_gate.get('status') or 'unknown')}"
        )

    try:
        audit, audit_source = _load_json_with_raw_artifact(
            selected_paths["source_audit"]
        )
        audit_findings = validate_source_quality_audit(audit, target_date=target_date)
        if audit_findings:
            blockers.extend(audit_findings)
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

    try:
        provider_bound_r0_generation = _load_provider_bound_r0_generation(
            target_date=target_date,
            selected_paths=selected_paths,
        )
        if provider_bound_r0_generation is not None:
            provider_bound_r0_locked = True
            current_execution_report = provider_bound_r0_generation["execution"]
            materialized = provider_bound_r0_generation["materialized"]
            labels = provider_bound_r0_generation["labels"]
            source_bundle = provider_bound_r0_generation["source_bundle"]
            prepared = provider_bound_r0_generation["prepared"]
            bridge = provider_bound_r0_generation["bridge"]
            paired_report = provider_bound_r0_generation["paired"]
            provider_ablation_sample_floor = provider_bound_r0_generation[
                "provider_floor"
            ]
            current_checkpoint_artifact = provider_bound_r0_generation["checkpoint"]
            steps.append(
                {
                    "name": "provider_bound_r0_generation",
                    "status": "pass",
                    "returncode": 0,
                    "artifact_reused": True,
                }
            )
    except (
        FileNotFoundError,
        OSError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        provider_bound_r0_locked = True
        blockers.append(
            "provider_bound_r0_generation_invalid:"
            f"{type(exc).__name__}:{exc}"
        )

    owner_command = [
        sys.executable,
        "-m",
        "src.engine.scalping.micro_reversion.economic_reference_owner",
        "--target-date",
        target_date,
        "--policy",
        str(selected_paths["economic_policy"]),
        "--output-root",
        str(selected_paths["economic_source_manifest"].parent),
    ]
    reuse_existing_economic_chain = False
    if write and not blockers:
        try:
            existing_owner_report = _load_json_auto(
                selected_paths["economic_owner_report"]
            )
            provider_authority_binding = _validate_economic_owner_report(
                existing_owner_report,
                target_date=target_date,
                owner_report_path=selected_paths["economic_owner_report"],
                policy_path=selected_paths["economic_policy"],
                manifest_path=selected_paths["economic_source_manifest"],
                pricing_path=selected_paths["provider_pricing"],
            )
            existing_economic = _load_json_auto(selected_paths["economic_reference"])
            _validate_existing_economic_reference(
                existing_economic,
                target_date=target_date,
                manifest_path=selected_paths["economic_source_manifest"],
            )
            reuse_existing_economic_chain = True
        except (
            FileNotFoundError,
            OSError,
            TypeError,
            ValueError,
            json.JSONDecodeError,
        ):
            reuse_existing_economic_chain = False
    if provider_bound_r0_locked and not reuse_existing_economic_chain:
        blockers.append("provider_bound_economic_chain_invalid")
    if not write:
        blockers.append("write_required_for_composed_r0_r3_artifact_chain")
    elif not blockers and reuse_existing_economic_chain:
        steps.append(
            {
                "name": "economic_reference_owner",
                "status": "pass",
                "returncode": 0,
                "artifact_reused": True,
            }
        )
    elif not blockers:
        steps.append(
            _command_step(
                name="economic_reference_owner",
                command=owner_command,
                runner=command_runner,
            )
        )
        if steps[-1]["returncode"] != 0:
            blockers.append("economic_reference_owner_failed_or_not_effective")
        else:
            try:
                owner_report = _load_json_auto(selected_paths["economic_owner_report"])
                provider_authority_binding = _validate_economic_owner_report(
                    owner_report,
                    target_date=target_date,
                    owner_report_path=selected_paths["economic_owner_report"],
                    policy_path=selected_paths["economic_policy"],
                    manifest_path=selected_paths["economic_source_manifest"],
                    pricing_path=selected_paths["provider_pricing"],
                )
            except (
                OSError,
                TypeError,
                ValueError,
                json.JSONDecodeError,
            ) as exc:
                blockers.append(
                    f"economic_reference_owner_report_invalid:{type(exc).__name__}"
                )

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
    if write and not blockers and reuse_existing_economic_chain:
        steps.append(
            {
                "name": "economic_reference",
                "status": "pass",
                "returncode": 0,
                "artifact_reused": True,
            }
        )
    elif write and not blockers:
        steps.append(
            _command_step(
                name="economic_reference",
                command=economic_command,
                runner=command_runner,
            )
        )
        if steps[-1]["returncode"] != 0:
            blockers.append("economic_reference_command_failed")

    economic: dict[str, Any] = {}
    cost_profile: dict[str, Any] = {}
    symbol_master: dict[str, Any] = {}
    if not blockers and selected_paths["economic_reference"].exists():
        try:
            economic = _load_json_auto(selected_paths["economic_reference"])
            if (
                economic.get("status") not in {"pass", "partial"}
                or economic.get("tuning_input_allowed") is not True
            ):
                blockers.append("economic_reference_not_verified")
            cost_profile, symbol_master = _economic_outputs(economic)
            if write and not provider_bound_r0_locked:
                _atomic_write_json(selected_paths["cost_profile"], cost_profile)
                _atomic_write_json(selected_paths["symbol_master"], symbol_master)
        except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
            blockers.append(f"economic_reference_invalid:{type(exc).__name__}")
    elif not blockers:
        blockers.append("economic_reference_artifact_missing")

    if not blockers and provider_bound_r0_generation is None:
        try:
            paired_report, paired_source = _load_json_with_raw_artifact(
                selected_paths["paired_report"]
            )
            prepared = build_prepared_request_artifact(
                target_date=target_date,
                paired_report=paired_report,
                source=paired_source,
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

    if not blockers and provider_bound_r0_generation is not None:
        steps.append(
            {
                "name": "bridge",
                "status": "pass",
                "returncode": 0,
                "artifact_reused": True,
            }
        )
    elif not blockers:
        bridge_command = _scheduled_bridge_command(
            target_date=target_date,
            selected_paths=selected_paths,
            prepared_artifact=prepared,
            write=write,
        )
        steps.append(
            _command_step(name="bridge", command=bridge_command, runner=command_runner)
        )
        if steps[-1]["returncode"] != 0:
            blockers.append("bridge_command_failed")

    if not blockers and provider_bound_r0_generation is not None:
        steps.append(
            {
                "name": "source_bundle",
                "status": "pass",
                "returncode": 0,
                "artifact_reused": True,
            }
        )
    elif not blockers:
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
            "--micro-reversion-bridge-report",
            str(selected_paths["bridge_report"]),
            "--micro-reversion-storage-capacity-status",
            str(selected_paths["capacity_status"]),
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

    if not blockers and provider_bound_r0_generation is not None:
        steps.append(
            {
                "name": "materialize",
                "status": "pass",
                "returncode": 0,
                "artifact_reused": True,
            }
        )
    elif not blockers:
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
            "--micro-reversion-bridge-report",
            str(selected_paths["bridge_report"]),
            "--micro-reversion-storage-capacity-status",
            str(selected_paths["capacity_status"]),
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
        else:
            try:
                materialized = _load_json_auto(selected_paths["materialized"])
                if target_date >= CURRENT_DESIGN_ACTIVATION_DATE:
                    prepared = _load_json_auto(selected_paths["prepared"])
                    source_bundle = _load_json_auto(selected_paths["source_bundle"])
                    bridge = _load_json_auto(selected_paths["bridge_report"])
                materialized_request_count = _validate_materialized_step_artifact(
                    materialized,
                    target_date=target_date,
                    source_bundle_report=(
                        source_bundle
                        if target_date >= CURRENT_DESIGN_ACTIVATION_DATE
                        else None
                    ),
                    prepared_artifact=(
                        prepared
                        if target_date >= CURRENT_DESIGN_ACTIVATION_DATE
                        else None
                    ),
                    source_bridge_report=(
                        bridge
                        if target_date >= CURRENT_DESIGN_ACTIVATION_DATE
                        else None
                    ),
                    paired_report=(
                        paired_report
                        if target_date >= CURRENT_DESIGN_ACTIVATION_DATE
                        else None
                    ),
                )
                if materialized_request_count <= 0:
                    blockers.append("no_micro_reversion_eligible_requests")
            except (
                FileNotFoundError,
                OSError,
                TypeError,
                ValueError,
                json.JSONDecodeError,
            ) as exc:
                blockers.append(
                    f"materialized_artifact_invalid:{type(exc).__name__}:{exc}"
                )

    if not blockers and provider_bound_r0_generation is None:
        try:
            bridge = _load_json_auto(selected_paths["bridge_report"])
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

    if (
        execute_provider_replay
        and not blockers
        and provider_bound_r0_generation is None
    ):
        try:
            provider_ablation_sample_floor = _collect_provider_ablation_sample_floor(
                target_date=target_date,
                current_materialized=materialized,
                current_companions={
                    "source_bundle": source_bundle,
                    "prepared": prepared,
                    "bridge": bridge,
                    "paired": paired_report,
                    "paths": {
                        "source_bundle": str(selected_paths["source_bundle"]),
                        "prepared": str(selected_paths["prepared"]),
                        "bridge": str(selected_paths["bridge_report"]),
                        "paired": str(selected_paths["paired_report"]),
                    },
                },
                selected_paths=selected_paths,
            )
            if write:
                _atomic_write_json(
                    selected_paths["provider_ablation_floor"],
                    provider_ablation_sample_floor,
                )
            if provider_ablation_sample_floor.get("pass") is not True:
                blockers.append(
                    "ask_depletion_provider_ablation_sample_floor_not_met:"
                    f"{provider_ablation_sample_floor.get('status') or 'unknown'}"
                )
        except (
            FileNotFoundError,
            OSError,
            TypeError,
            ValueError,
            json.JSONDecodeError,
        ) as exc:
            blockers.append(
                "ask_depletion_provider_ablation_sample_floor_failed:"
                f"{type(exc).__name__}:{exc}"
            )

    observer_blocker = observer_stage_gate.get("blocker_code")
    if observer_blocker and observer_blocker not in blockers:
        blockers.append(str(observer_blocker))

    if execute_provider_replay and not blockers:
        if provider_authority_binding.get(
            "schema"
        ) != PROVIDER_AUTHORITY_BINDING_SCHEMA or not provider_authority_binding.get(
            "economic_owner_report_path"
        ):
            blockers.append("provider_authority_binding_missing")

    if execute_provider_replay and not blockers:
        (
            historical_backfill_steps,
            historical_backfill_admissions,
            historical_backfill_selected_parent_slots,
            historical_backfill_provider_call_performed,
            historical_backfill_blockers,
        ) = _run_bounded_historical_provider_backfill(
            current_target_date=target_date,
            current_floor=provider_ablation_sample_floor,
            write=write,
            daily_attempt_cap=daily_attempt_cap,
            daily_usd_cap=canonical_daily_usd_cap,
            daily_usd_cap_text=canonical_daily_usd_cap_text,
            parent_cap=parent_cap,
            command_runner=command_runner,
        )
        steps.extend(historical_backfill_steps)
        blockers.extend(historical_backfill_blockers)

    if execute_provider_replay and not blockers:
        provider_capacity_recheck, provider_capacity_blocker = (
            _pre_provider_capacity_recheck(
                target=target,
                target_date=target_date,
                selected_paths=selected_paths,
            )
        )
        if provider_capacity_blocker:
            blockers.append(provider_capacity_blocker)

    if execute_provider_replay and not blockers:
        max_new_requests = (
            parent_cap - historical_backfill_selected_parent_slots
        ) * len(EXPECTED_ARMS)
        execute_command = _provider_execute_command(
            target_date=target_date,
            selected_paths=selected_paths,
            provider_authority_binding=provider_authority_binding,
            provider_floor_path=selected_paths["provider_ablation_floor"],
            daily_attempt_cap=daily_attempt_cap,
            daily_usd_cap_text=canonical_daily_usd_cap_text,
            max_new_requests=max_new_requests,
            write=write,
        )
        steps.append(
            _command_step(
                name="bounded_provider_replay",
                command=execute_command,
                runner=command_runner,
            )
        )
        if steps[-1]["returncode"] not in {0, 2}:
            blockers.append("bounded_provider_replay_failed_or_deferred")
        else:
            try:
                current_execution_report = _load_json_auto(selected_paths["execution"])
                partial_terminal_status = (
                    "offline_three_arm_execution_complete_with_failures_or_exclusions"
                )
                if (steps[-1]["returncode"] == 2) != (
                    current_execution_report.get("status") == partial_terminal_status
                ):
                    raise ValueError(
                        "bounded_provider_replay_exit_status_contract_mismatch"
                    )
                current_checkpoint_artifact = quality._load_micro_reversion_checkpoint(
                    selected_paths["execution_checkpoint"],
                    repair_manifest=False,
                )
                _validate_current_execution_artifact(
                    report=current_execution_report,
                    target_date=target_date,
                    materialized_report=materialized,
                    source_bundle_report=source_bundle,
                    prepared_artifact=prepared,
                    paired_report=paired_report,
                    outcome_label_artifact=labels,
                    source_bridge_report=bridge,
                    checkpoint_artifact=current_checkpoint_artifact,
                    provider_ablation_floor_artifact=(provider_ablation_sample_floor),
                    expected_max_new_requests=max_new_requests,
                    expected_daily_attempt_cap=daily_attempt_cap,
                    expected_daily_usd_cap=canonical_daily_usd_cap,
                    expected_pricing_content_sha256=str(
                        provider_authority_binding.get(
                            "provider_pricing_artifact_content_sha256"
                        )
                        or ""
                    ),
                    expected_provider_authority_binding=(provider_authority_binding),
                )
                current_provider_replay_complete = True
                if steps[-1]["returncode"] == 2:
                    steps[-1]["status"] = "pass_with_bounded_failures_or_exclusions"
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

    bridge_diagnostic_report: dict[str, Any] | None = None
    lifecycle_diagnostic_report: dict[str, Any] | None = None
    try:
        candidate_bridge = _load_json_auto(selected_paths["bridge_report"])
        if candidate_bridge.get("target_date") == target_date:
            bridge_diagnostic_report = candidate_bridge
    except (FileNotFoundError, OSError, TypeError, ValueError, json.JSONDecodeError):
        pass
    try:
        candidate_lifecycle = _load_json_auto(selected_paths["lifecycle"])
        if candidate_lifecycle.get("target_date") == target_date:
            lifecycle_diagnostic_report = candidate_lifecycle
    except (FileNotFoundError, OSError, TypeError, ValueError, json.JSONDecodeError):
        pass
    source_gap_diagnostics = _source_only_gap_diagnostics(
        target_date=target_date,
        observer_canary=observer_canary,
        bridge_report=bridge_diagnostic_report,
        lifecycle_report=lifecycle_diagnostic_report,
    )
    for blocker in source_gap_diagnostics["blocker_codes"]:
        if blocker not in blockers:
            blockers.append(blocker)

    rolling_diagnostics: list[dict[str, Any]] = []
    counterfactual_entry_artifact: dict[str, Any] = {}
    try:
        (
            execution_reports,
            lifecycle_reports,
            source_quality_pass,
            economic_reference_pass,
            outcome_label_artifacts,
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
        if current_provider_replay_complete:
            outcome_label_artifacts[target_date] = {
                "outcome_label_artifact": labels,
                "source_bridge_report": bridge,
                "materialized_report": materialized,
                "source_bundle_report": source_bundle,
                "prepared_artifact": prepared,
                "paired_report": paired_report,
                "checkpoint_artifact": current_checkpoint_artifact,
                "lazy_load_one_date_at_a_time": True,
            }
        else:
            outcome_label_artifacts.pop(target_date, None)
        rolling, r3_manifest = build_rolling_source_only_candidates(
            target_date=target_date,
            execution_reports=execution_reports,
            lifecycle_reports=lifecycle_reports,
            source_quality_pass_by_date=source_quality_pass,
            economic_reference_pass_by_date=economic_reference_pass,
            outcome_label_artifacts_by_date=outcome_label_artifacts,
            input_diagnostics=rolling_diagnostics,
            current_run_global_blockers=blockers,
            counterfactual_entry_diagnostic_out=(counterfactual_entry_artifact),
            counterfactual_entry_output_path=selected_paths[
                "counterfactual_entry_diagnostic"
            ],
        )
        source_gap_diagnostics = _source_only_gap_diagnostics(
            target_date=target_date,
            observer_canary=observer_canary,
            bridge_report=bridge_diagnostic_report,
            lifecycle_report=lifecycle_diagnostic_report,
            rolling_exclusions=(rolling.get("exclusions") or []),
        )
        for blocker in source_gap_diagnostics["blocker_codes"]:
            if blocker not in blockers:
                blockers.append(blocker)
        if write:
            # Persist the referenced companion before either consumer.  A
            # diagnostic write failure must not leave a newly published
            # rolling/R3 artifact pointing at an absent generation.
            if counterfactual_entry_artifact:
                _atomic_write_json(
                    selected_paths["counterfactual_entry_diagnostic"],
                    counterfactual_entry_artifact,
                )
            _atomic_write_json(rolling_report_path(target_date), rolling)
            _atomic_write_json(r3_manifest_path(target_date), r3_manifest)
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        rolling = {}
        r3_manifest = {}
        counterfactual_entry_artifact = {}
        blockers.append(f"rolling_r2_r3_failed:{type(exc).__name__}:{exc}")

    provider_call_performed = bool(
        historical_backfill_provider_call_performed
        or (
            current_provider_replay_complete
            and int(current_execution_report.get("new_result_count") or 0) > 0
            and current_execution_report.get("candidate_model_call_attempted") is True
            and current_execution_report.get("provider_call_performed") is True
        )
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
        "storage_capacity_gate": storage_capacity_gate,
        "provider_capacity_recheck": provider_capacity_recheck,
        "provider_ablation_sample_floor": provider_ablation_sample_floor,
        "historical_provider_backfill": {
            "schema": "micro_reversion_historical_provider_backfill_batch_v1",
            "selection_order": "oldest_missing_date_first_one_complete_parent",
            "selected_parent_slot_count": historical_backfill_selected_parent_slots,
            "admission_count": len(historical_backfill_admissions),
            "admissions": historical_backfill_admissions,
            "provider_call_performed": (historical_backfill_provider_call_performed),
            **OFFLINE_AUTHORITY,
        },
        "observer_canary": observer_canary,
        "observer_source_only_stage_gate": observer_stage_gate,
        "source_gap_diagnostics": source_gap_diagnostics,
        "source_only_gap_workorders": source_gap_diagnostics["workorders"],
        "economic_reference_path": str(selected_paths["economic_reference"]),
        "economic_policy_path": str(selected_paths["economic_policy"]),
        "economic_owner_report_path": str(selected_paths["economic_owner_report"]),
        "prepared_request_path": str(selected_paths["prepared"]),
        "bridge_report_path": str(selected_paths["bridge_report"]),
        "source_bundle_path": str(selected_paths["source_bundle"]),
        "materialized_request_path": str(selected_paths["materialized"]),
        "action_neutral_label_path": str(selected_paths["labels"]),
        "execution_result_path": str(selected_paths["execution"]),
        "main_lifecycle_report_path": str(selected_paths["lifecycle"]),
        "rolling_report_path": str(rolling_report_path(target_date)),
        "r3_manifest_path": str(r3_manifest_path(target_date)),
        "counterfactual_entry_diagnostic_path": str(
            selected_paths["counterfactual_entry_diagnostic"]
        ),
        "rolling_status": rolling.get("status"),
        "r3_status": r3_manifest.get("status"),
        "r3_source_candidate_count": int(r3_manifest.get("candidate_count") or 0),
        "counterfactual_entry_diagnostic_status": (
            counterfactual_entry_artifact.get("status")
        ),
        "counterfactual_entry_eligible_parent_count": int(
            counterfactual_entry_artifact.get("eligible_parent_count") or 0
        ),
        "counterfactual_entry_candidate_count": 0,
        "counterfactual_entry_artifact_sha256": (
            counterfactual_entry_artifact.get("artifact_content_sha256")
        ),
        "rolling_input_diagnostics": rolling_diagnostics,
        "provider_execution_requested": execute_provider_replay,
        "current_provider_replay_complete": current_provider_replay_complete,
        "provider_authority_binding": (provider_authority_binding or None),
        "provider_budget": {
            "daily_attempt_cap": daily_attempt_cap,
            "daily_usd_cap": canonical_daily_usd_cap_text,
            "parent_cap": parent_cap,
            "maximum_logical_requests": parent_cap * len(EXPECTED_ARMS),
            "maximum_schema_attempts_per_request": quality.CANDIDATE_SCHEMA_MAX_ATTEMPTS,
            "reviewed_pricing_artifact_required": True,
            "pricing_basis": "operator_accounting_zero_cost",
            "capacity_basis": "2026-08-10_to_2026-08-14_evaluated_call_median_781",
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
    parser.add_argument(
        "--daily-attempt-cap", type=int, default=DEFAULT_DAILY_ATTEMPT_CAP
    )
    parser.add_argument("--daily-usd-cap", type=Decimal, default=DEFAULT_DAILY_USD_CAP)
    parser.add_argument("--parent-cap", type=int, default=DEFAULT_PARENT_CAP)
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
