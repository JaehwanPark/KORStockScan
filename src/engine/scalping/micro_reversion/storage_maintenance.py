"""Post-session compression and opt-in retention for forward observations.

The default CLI is dry-run.  ``--apply`` is required before any file changes.
Only validated ``trade_date=YYYY-MM-DD`` descendants of the configured root
are eligible, and the current trade date is never compressed or removed.
Compression and deletion are separate authorities: expired trade-date
partitions are removed only when ``--purge-expired`` is supplied explicitly.
"""

from __future__ import annotations

import argparse
import fcntl
import gzip
import hashlib
import json
import os
import re
import shutil
import stat
import tempfile
from collections.abc import Sequence
from contextlib import ExitStack, contextmanager, nullcontext
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from src.utils.jsonl_io import (
    ArtifactGenerationLease,
    JSON_GENERATION_LOCK_SUFFIX,
    JSONL_GENERATION_LOCK_SUFFIX,
    iter_jsonl_objects_strict,
    json_artifact_generation_lock,
    jsonl_artifact_generation_lock,
)

from .path_journal import PathStoragePolicy, partition_maintenance_lock
from .provider_budget import AUTHORITY_CONTRACT as PROVIDER_BUDGET_AUTHORITY_CONTRACT
from .replay_ablation_contract import (
    CURRENT_DESIGN_ACTIVATION_DATE,
    CURRENT_DESIGN_VERSION,
    LEGACY_PROVIDER_ABLATION_SAMPLE_FLOOR_SCHEMA,
    PROVIDER_ABLATION_SAMPLE_FLOOR_SCHEMA,
    SOURCE_ONLY_AUTHORITY_CONTRACT as CURRENT_P2_SOURCE_ONLY_AUTHORITY_CONTRACT,
    SOURCE_ONLY_FALSE_AUTHORITY_ALIASES as CURRENT_P2_FALSE_AUTHORITY_ALIASES,
)

MAINTENANCE_SCHEMA = "scalp_micro_reversion_storage_maintenance_v1"
MAINTENANCE_AUTHORITY = "post_session_storage_only_no_trading_authority"
SOURCE_EXCLUSION_PURGE_SCHEMA = "scalp_micro_reversion_source_exclusion_purge_v1"
REPORT_ARTIFACT_MAINTENANCE_SCHEMA = (
    "scalp_micro_reversion_report_artifact_storage_maintenance_v1"
)
STORAGE_CAPACITY_STATUS_SCHEMA = "scalp_micro_reversion_storage_capacity_status_v1"
STORAGE_CAPACITY_GROWTH_GATE_SCHEMA = (
    "scalp_micro_reversion_storage_capacity_growth_gate_v1"
)
STORAGE_UNLINK_CLAIM_MARKER = ".storage-unlink-claim."
STORAGE_TARGET_CUSTODY_MARKER = ".storage-target-custody."
REPORT_ARTIFACT_DEFAULT_RETENTION_DAYS = 90
EXACT_AI_ARTIFACT_MAINTENANCE_SCHEMA = (
    "scalp_micro_reversion_exact_ai_artifact_storage_maintenance_v1"
)
MICRO_REVERSION_DAILY_OWNER_CENSUS_SCHEMA = (
    "scalp_micro_reversion_daily_owner_storage_census_v1"
)
KST = ZoneInfo("Asia/Seoul")
_DEFAULT_PATH_STORAGE_POLICY = PathStoragePolicy()
STORAGE_LOW_DISK_WATERMARK_BYTES = _DEFAULT_PATH_STORAGE_POLICY.low_disk_watermark_bytes
STORAGE_CRITICAL_DISK_WATERMARK_BYTES = (
    _DEFAULT_PATH_STORAGE_POLICY.critical_disk_watermark_bytes
)
MAINTENANCE_METRIC_CONTRACT = {
    "metric_role": "source_quality_and_storage_retention",
    "decision_authority": MAINTENANCE_AUTHORITY,
    "window_policy": "closed_trade_dates_only",
    "sample_floor": "not_applicable_storage_operation",
    "primary_decision_metric": "retained_uncompressed_bytes",
    "source_quality_gate": "verified_trade_date_path_and_gzip_roundtrip_sha256",
    "forbidden_uses": [
        "current_trade_date_mutation",
        "retention_purge_without_explicit_opt_in",
        "broker_order_submission",
        "strategy_or_threshold_change",
        "provider_or_bot_mutation",
        "economic_edge_claim",
    ],
}

# These exact-date artifacts contain the immutable evidence and chain receipts
# needed to independently validate the bridge, materialization, provider
# replay, rolling evaluation, and source-only diagnostics.  Only these owned
# basenames are eligible for automatic compression; arbitrary JSON descendants
# of a report directory are never inferred as safe.
REPORT_ARTIFACT_NAME_PATTERNS = tuple(
    re.compile(pattern)
    for pattern in (
        r"ai_micro_reversion_replay_source_bundle_(\d{4}-\d{2}-\d{2})\.json",
        r"ai_micro_reversion_materialized_replay_requests_(\d{4}-\d{2}-\d{2})\.json",
        r"ai_micro_reversion_action_neutral_outcome_labels_(\d{4}-\d{2}-\d{2})\.json",
        r"ai_micro_reversion_three_arm_offline_results_(\d{4}-\d{2}-\d{2})\.json",
        r"micro_reversion_ai_quality_bridge_(\d{4}-\d{2}-\d{2})\.json",
        r"main_ai_quality_micro_prepared_requests_(\d{4}-\d{2}-\d{2})\.json",
        r"main_ai_quality_micro_control_driver_(\d{4}-\d{2}-\d{2})\.json",
        r"main_ai_quality_rolling_paired_(\d{4}-\d{2}-\d{2})\.json",
        r"main_ai_quality_r3_source_candidates_(\d{4}-\d{2}-\d{2})\.json",
        r"main_ai_quality_r0_r3_cycle_(\d{4}-\d{2}-\d{2})\.json",
        r"main_ai_quality_counterfactual_entry_(\d{4}-\d{2}-\d{2})\.json",
        r"micro_reversion_provider_ablation_sample_floor_(\d{4}-\d{2}-\d{2})\.json",
        r"micro_reversion_storage_capacity_(\d{4}-\d{2}-\d{2})\.json",
        r"ai_prompt_paired_replay_(\d{4}-\d{2}-\d{2})\.json",
        r"micro_reversion_economic_reference_(\d{4}-\d{2}-\d{2})\.json",
        r"micro_reversion_reviewed_cost_profile_(\d{4}-\d{2}-\d{2})\.json",
        r"micro_reversion_symbol_master_(\d{4}-\d{2}-\d{2})\.json",
    )
)
EXACT_AI_ARTIFACT_ROOT_CONTRACTS = {
    "ai_decision_payloads": (
        re.compile(r"ai_decision_payloads_(\d{4}-\d{2}-\d{2})\.jsonl"),
        "jsonl",
        "ai_decision_payload_v1",
        "captured_at",
    ),
    "ai_decision_trace": (
        re.compile(r"ai_decision_trace_(\d{4}-\d{2}-\d{2})\.jsonl"),
        "jsonl",
        "ai_decision_trace_v1",
        "decision_ts",
    ),
    "ai_decision_outcomes": (
        re.compile(r"ai_decision_outcomes_(\d{4}-\d{2}-\d{2})\.jsonl"),
        "jsonl",
        "ai_decision_outcome_label_v1",
        "created_at",
    ),
    "ai_decision_requests": (
        re.compile(r"ai_decision_requests_(\d{4}-\d{2}-\d{2})\.jsonl"),
        "jsonl",
        "ai_decision_request_provenance_v1",
        "captured_at",
    ),
    "ai_decision_prompts": (
        re.compile(r"ai_decision_prompts_(\d{4}-\d{2}-\d{2})\.jsonl"),
        "jsonl",
        "ai_decision_prompt_v1",
        "captured_at",
    ),
    "ai_decision_outcome_labels": (
        re.compile(r"ai_decision_outcome_labels_(\d{4}-\d{2}-\d{2})\.json"),
        "json",
        "ai_decision_outcome_labels_v1",
        "target_date",
    ),
}
# The general paired-replay input predates the current P2 ablation contract,
# and the capacity artifact is an operational storage receipt.  All other
# allowlisted decision/evaluation artifacts produced on or after the current
# design activation date must carry the exact seven-field P2 authority surface.
CURRENT_P2_STRICT_AUTHORITY_NAME_PATTERNS = tuple(
    re.compile(pattern)
    for pattern in (
        r"ai_micro_reversion_replay_source_bundle_(\d{4}-\d{2}-\d{2})\.json",
        r"ai_micro_reversion_materialized_replay_requests_(\d{4}-\d{2}-\d{2})\.json",
        r"ai_micro_reversion_action_neutral_outcome_labels_(\d{4}-\d{2}-\d{2})\.json",
        r"ai_micro_reversion_three_arm_offline_results_(\d{4}-\d{2}-\d{2})\.json",
        r"micro_reversion_ai_quality_bridge_(\d{4}-\d{2}-\d{2})\.json",
        r"main_ai_quality_micro_prepared_requests_(\d{4}-\d{2}-\d{2})\.json",
        r"main_ai_quality_micro_control_driver_(\d{4}-\d{2}-\d{2})\.json",
        r"main_ai_quality_rolling_paired_(\d{4}-\d{2}-\d{2})\.json",
        r"main_ai_quality_r3_source_candidates_(\d{4}-\d{2}-\d{2})\.json",
        r"main_ai_quality_r0_r3_cycle_(\d{4}-\d{2}-\d{2})\.json",
        r"main_ai_quality_counterfactual_entry_(\d{4}-\d{2}-\d{2})\.json",
        r"micro_reversion_provider_ablation_sample_floor_(\d{4}-\d{2}-\d{2})\.json",
    )
)
IMMUTABLE_SOURCE_ARTIFACT_CONTRACTS = tuple(
    (re.compile(pattern), schema, hash_field)
    for pattern, schema, hash_field in (
        (
            r"ai_micro_reversion_replay_source_bundle_(\d{4}-\d{2}-\d{2})\.json",
            "ai_micro_reversion_replay_source_bundle_v1",
            "source_bundle_content_sha256",
        ),
        (
            r"ai_micro_reversion_materialized_replay_requests_(\d{4}-\d{2}-\d{2})\.json",
            "ai_micro_reversion_materialized_replay_requests_v1",
            "report_content_sha256",
        ),
        (
            r"ai_micro_reversion_action_neutral_outcome_labels_(\d{4}-\d{2}-\d{2})\.json",
            "ai_micro_reversion_action_neutral_outcome_labels_v1",
            "artifact_content_sha256",
        ),
        (
            r"micro_reversion_ai_quality_bridge_(\d{4}-\d{2}-\d{2})\.json",
            "micro_reversion_ai_quality_bridge_v1",
            "report_content_sha256",
        ),
        (
            r"main_ai_quality_micro_prepared_requests_(\d{4}-\d{2}-\d{2})\.json",
            "main_ai_quality_micro_prepared_requests_v1",
            "artifact_content_sha256",
        ),
        (
            r"main_ai_quality_micro_control_driver_(\d{4}-\d{2}-\d{2})\.json",
            "main_ai_quality_micro_control_driver_v1",
            "artifact_content_sha256",
        ),
        (
            r"main_ai_quality_rolling_paired_(\d{4}-\d{2}-\d{2})\.json",
            "main_ai_quality_rolling_paired_evaluation_v1",
            "artifact_content_sha256",
        ),
        (
            r"main_ai_quality_r3_source_candidates_(\d{4}-\d{2}-\d{2})\.json",
            "main_ai_quality_source_only_candidate_manifest_v1",
            "artifact_content_sha256",
        ),
        (
            r"main_ai_quality_r0_r3_cycle_(\d{4}-\d{2}-\d{2})\.json",
            "main_ai_quality_postclose_r0_r3_cycle_v1",
            "artifact_content_sha256",
        ),
        (
            r"main_ai_quality_counterfactual_entry_(\d{4}-\d{2}-\d{2})\.json",
            "main_ai_quality_counterfactual_entry_r3_diagnostic_v1",
            "artifact_content_sha256",
        ),
        (
            r"micro_reversion_provider_ablation_sample_floor_(\d{4}-\d{2}-\d{2})\.json",
            frozenset(
                {
                    LEGACY_PROVIDER_ABLATION_SAMPLE_FLOOR_SCHEMA,
                    PROVIDER_ABLATION_SAMPLE_FLOOR_SCHEMA,
                }
            ),
            "floor_content_sha256",
        ),
        (
            r"micro_reversion_storage_capacity_(\d{4}-\d{2}-\d{2})\.json",
            STORAGE_CAPACITY_STATUS_SCHEMA,
            "artifact_content_sha256",
        ),
        (
            r"ai_prompt_paired_replay_(\d{4}-\d{2}-\d{2})\.json",
            "ai_prompt_paired_replay_v1",
            None,
        ),
        (
            r"micro_reversion_economic_reference_(\d{4}-\d{2}-\d{2})\.json",
            "micro_reversion_economic_reference_daily_resolution_v2",
            "artifact_content_sha256",
        ),
        (
            r"micro_reversion_reviewed_cost_profile_(\d{4}-\d{2}-\d{2})\.json",
            "micro_reversion_reviewed_cost_catalog_v2",
            "content_sha256",
        ),
        (
            r"micro_reversion_symbol_master_(\d{4}-\d{2}-\d{2})\.json",
            "scalp_micro_reversion_symbol_master_v1",
            "content_sha256",
        ),
    )
)
CHECKPOINT_RECORD_DIRECTORY_PATTERN = re.compile(
    r"ai_micro_reversion_three_arm_offline_results_"
    r"(\d{4}-\d{2}-\d{2})\.checkpoint\.json\.records"
)
CHECKPOINT_RECORD_FILE_PATTERN = re.compile(r"(\d{8})-([0-9a-f]{64})\.json(?:\.gz)?")
PROVIDER_BUDGET_LEDGER_PATTERN = re.compile(
    r"ai_micro_reversion_provider_budget_(\d{4}-\d{2}-\d{2})\.jsonl(?:\.gz)?"
)
CHECKPOINT_MANIFEST_SCHEMA = "ai_micro_reversion_execution_checkpoint_manifest_v1"
CHECKPOINT_RECORD_SCHEMA = "ai_micro_reversion_execution_checkpoint_record_v1"
CHECKPOINT_RECONSTRUCTED_SCHEMA = (
    "ai_micro_reversion_execution_checkpoint_reconstructed_v1"
)
PROVIDER_BUDGET_LEDGER_RECORD_SCHEMA = "ai_provider_budget_ledger_record_v1"
PROVIDER_BUDGET_LEDGER_MANIFEST_SCHEMA = "ai_provider_budget_ledger_manifest_v1"
PROVIDER_BUDGET_SUMMARY_SCHEMA = "ai_provider_budget_summary_v1"
PROVIDER_BUDGET_RECORD_COMMON_FIELDS = frozenset(
    {
        "schema",
        "sequence",
        "previous_record_sha256",
        "record_content_sha256",
        "event_type",
        "recorded_at",
        "execution_date",
        "reservation_id",
        "attempt_identity",
        "attempt_identity_sha256",
        "budget_contract",
        "budget_contract_sha256",
        "pricing_artifact_id",
        "pricing_artifact_content_sha256",
        "pricing_artifact_file_sha256",
        "raw_pricing_source_bytes_sha256",
        "raw_pricing_source_path",
        "raw_pricing_source_size_bytes",
        "pricing_effective_from",
        "pricing_effective_to",
        *PROVIDER_BUDGET_AUTHORITY_CONTRACT,
    }
)
PROVIDER_BUDGET_RESERVATION_RECORD_FIELDS = PROVIDER_BUDGET_RECORD_COMMON_FIELDS | {
    "token_ceiling",
    "model_pricing",
    "reserved_cost_usd",
    "reservation_status",
    "unknown_or_crashed_call_refund_allowed",
}
PROVIDER_BUDGET_SETTLEMENT_RECORD_FIELDS = PROVIDER_BUDGET_RECORD_COMMON_FIELDS | {
    "actual_input_tokens",
    "actual_output_tokens",
    "actual_cost_usd",
    "reserved_cost_usd",
    "provider_response_sha256",
    "settlement_status",
    "actual_cost_exceeded_reservation",
    "actual_token_ceiling_exceeded",
    "actual_exceeded_reservation",
    "circuit_breaker_open",
}
PROVIDER_BUDGET_MANIFEST_FIELDS = frozenset(
    {
        "schema",
        "manifest_content_sha256",
        "updated_at",
        "execution_date",
        "ledger_file",
        "ledger_size_bytes",
        "ledger_bytes_sha256",
        "record_count",
        "head_record_sha256",
        "budget_contract_sha256",
        *PROVIDER_BUDGET_AUTHORITY_CONTRACT,
    }
)
PROVIDER_BUDGET_SUMMARY_FIELDS = frozenset(
    {
        "schema",
        "summary_content_sha256",
        "generated_at",
        "execution_date",
        "status",
        "daily_attempt_cap",
        "daily_usd_cap",
        "reservation_count",
        "settlement_count",
        "outstanding_reservation_count",
        "actual_cost_usd",
        "outstanding_reserved_cost_usd",
        "committed_cost_usd",
        "remaining_attempt_count",
        "remaining_usd",
        "circuit_breaker_open",
        "ledger_record_count",
        "ledger_head_sha256",
        "ledger_bytes_sha256",
        "budget_contract_sha256",
        "pricing_artifact_id",
        "pricing_artifact_content_sha256",
        "pricing_artifact_file_sha256",
        "pricing_basis",
        "raw_pricing_source_bytes_sha256",
        "raw_pricing_source_path",
        "raw_pricing_source_size_bytes",
        "pricing_effective_from",
        "pricing_effective_to",
        "provider_model_attempt_counts",
        *PROVIDER_BUDGET_AUTHORITY_CONTRACT,
    }
)
CHECKPOINT_RECONSTRUCTED_CONTRACT = {
    "metric_role": "ai_decision_quality_observation",
    "decision_authority": "offline_replay_and_attribution_only",
    "window_policy": "exact_snapshot_stage_venue_session_mature_forward_window",
    "sample_floor": "eligible_exact_rows_with_mature_outcomes",
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "source_quality_gate": "exact_payload_fresh_same_route_mature_window",
    "runtime_effect": False,
    "allowed_runtime_apply": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
    "forbidden_uses": [
        "live_prompt_promotion_without_separate_review",
        "provider_or_model_change",
        "threshold_price_quantity_or_cap_change",
        "broker_or_safety_guard_bypass",
        "counterfactual_realized_pnl_merge",
        "bot_restart",
    ],
}
TERMINAL_EXECUTION_RESULT_SCHEMA = "ai_micro_reversion_three_arm_offline_results_v1"
TERMINAL_EXECUTION_STATUS = "offline_three_arm_execution_complete"
RESUMABLE_EXECUTION_STATUSES = frozenset(
    {
        "offline_three_arm_execution_batch_complete",
        "offline_three_arm_execution_complete_with_failures_or_exclusions",
        "provider_execution_not_authorized",
    }
)
SOURCE_ONLY_AUTHORITY_FIELDS = {
    "runtime_effect": False,
    "allowed_runtime_apply": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
}
PROVIDER_SOURCE_ONLY_AUTHORITY_FIELDS = {
    **SOURCE_ONLY_AUTHORITY_FIELDS,
    "provider_route_change_allowed": False,
    "network_call_performed_by_module": False,
}


@dataclass(frozen=True, slots=True)
class StorageMaintenanceAction:
    action: str
    path: str
    trade_date: str
    source_bytes: int
    applied: bool


@dataclass(frozen=True, slots=True)
class SourceExclusionPurgeAction:
    trade_date: str
    venue: str
    session_bucket: str
    sequence_epochs: tuple[int, ...]
    stream_rows_removed: int
    event_reference_rows_removed: int
    source_bytes_before: int
    source_bytes_after: int
    applied: bool


def _validate_capacity_watermarks(
    *,
    low_disk_watermark_bytes: int,
    critical_disk_watermark_bytes: int,
) -> None:
    for field, value in (
        ("low_disk_watermark_bytes", low_disk_watermark_bytes),
        ("critical_disk_watermark_bytes", critical_disk_watermark_bytes),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"{field} must be a non-negative integer")
    if low_disk_watermark_bytes < critical_disk_watermark_bytes:
        raise ValueError("low disk watermark must not be below critical disk watermark")


def _capacity_anchor(path: Path) -> Path:
    candidate = Path(path).absolute()
    while not candidate.exists():
        parent = candidate.parent
        if parent == candidate:
            break
        candidate = parent
    return candidate


def _disk_capacity_snapshot(path: Path) -> dict[str, int]:
    usage = shutil.disk_usage(_capacity_anchor(path))
    return {
        "disk_total_bytes": int(usage.total),
        "disk_used_bytes": int(usage.used),
        "disk_free_bytes": int(usage.free),
    }


def _capacity_state(
    free_bytes: int,
    *,
    low_disk_watermark_bytes: int,
    critical_disk_watermark_bytes: int,
) -> str:
    if free_bytes < critical_disk_watermark_bytes:
        return "critical"
    if free_bytes < low_disk_watermark_bytes:
        return "low_warning"
    return "healthy"


def _capacity_reason_codes(state: str) -> list[str]:
    if state == "critical":
        return ["disk_free_below_critical_watermark"]
    if state == "low_warning":
        return ["disk_free_below_low_watermark"]
    return []


def _regular_file_bytes(roots: Sequence[Path]) -> int:
    """Return physical regular-file bytes below roots without following links."""

    total = 0
    seen: set[tuple[int, int]] = set()
    for raw_root in roots:
        root = Path(raw_root)
        if root.is_symlink() or not root.exists():
            continue
        candidates = [root] if root.is_file() else root.rglob("*")
        for candidate in candidates:
            try:
                state = candidate.lstat()
            except OSError:
                continue
            if not stat.S_ISREG(state.st_mode):
                continue
            identity = (state.st_dev, state.st_ino)
            if identity in seen:
                continue
            seen.add(identity)
            total += state.st_size
    return total


_COMPRESSED_TARGET_ACTIONS = frozenset(
    {
        "compress_jsonl",
        "finalize_verified_compression",
        "publish_verified_gzip_source_preserved",
        "compress_json_artifact",
        "finalize_verified_json_artifact_compression",
        "publish_verified_json_artifact_gzip_source_preserved",
        "compress_checkpoint_record_json",
        "finalize_verified_checkpoint_record_compression",
        "publish_verified_checkpoint_record_gzip_source_preserved",
        "compress_provider_budget_jsonl",
        "finalize_verified_provider_budget_compression",
        "publish_verified_provider_budget_gzip_source_preserved",
        "compress_exact_ai_jsonl",
        "finalize_verified_exact_ai_jsonl_compression",
        "publish_verified_exact_ai_jsonl_gzip_source_preserved",
        "compress_exact_ai_json",
        "finalize_verified_exact_ai_json_compression",
        "publish_verified_exact_ai_json_gzip_source_preserved",
    }
)


def _compressed_target_bytes(
    actions: Sequence[StorageMaintenanceAction],
) -> int:
    targets: set[Path] = set()
    for action in actions:
        if not action.applied or action.action not in _COMPRESSED_TARGET_ACTIONS:
            continue
        source = Path(action.path)
        targets.add(source.with_suffix(f"{source.suffix}.gz"))
    total = 0
    for target in targets:
        try:
            state = target.lstat()
        except OSError:
            continue
        if stat.S_ISREG(state.st_mode):
            total += state.st_size
    return total


def _capacity_metrics(
    *,
    disk_before: dict[str, int],
    disk_after: dict[str, int],
    retained_physical_bytes_before: int,
    retained_physical_bytes_after: int,
    compressed_target_bytes: int,
    low_disk_watermark_bytes: int,
    critical_disk_watermark_bytes: int,
) -> dict[str, object]:
    state = _capacity_state(
        disk_after["disk_free_bytes"],
        low_disk_watermark_bytes=low_disk_watermark_bytes,
        critical_disk_watermark_bytes=critical_disk_watermark_bytes,
    )
    return {
        "disk_total_bytes": disk_after["disk_total_bytes"],
        "disk_used_bytes_after": disk_after["disk_used_bytes"],
        "disk_free_bytes_before": disk_before["disk_free_bytes"],
        "disk_free_bytes_after": disk_after["disk_free_bytes"],
        "disk_free_bytes_delta": (
            disk_after["disk_free_bytes"] - disk_before["disk_free_bytes"]
        ),
        "retained_physical_bytes_before": retained_physical_bytes_before,
        "retained_physical_bytes_after": retained_physical_bytes_after,
        "retained_physical_bytes_delta": (
            retained_physical_bytes_after - retained_physical_bytes_before
        ),
        "compressed_target_bytes": compressed_target_bytes,
        "bytes_reclaimed": max(
            0,
            retained_physical_bytes_before - retained_physical_bytes_after,
        ),
        "low_disk_watermark_bytes": low_disk_watermark_bytes,
        "critical_disk_watermark_bytes": critical_disk_watermark_bytes,
        "capacity_state": state,
        "capacity_warning": state == "low_warning",
        "capacity_failure": state == "critical",
        "capacity_workorder_required": state != "healthy",
        "capacity_reason_codes": _capacity_reason_codes(state),
    }


def _report_artifact_trade_date(file_name: str) -> date | None:
    logical_name = file_name.removesuffix(".gz")
    for pattern in REPORT_ARTIFACT_NAME_PATTERNS:
        matched = pattern.fullmatch(logical_name)
        if matched is not None:
            try:
                return date.fromisoformat(matched.group(1))
            except ValueError:
                return None
    return None


def _canonical_sha256(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _provider_canonical_sha256(value: object) -> str:
    """Match the provider ledger owner's UTF-8 canonical JSON contract."""

    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _json_loads_strict(payload: bytes, *, context: str) -> object:
    """Reject duplicate keys and non-finite values in custody artifacts."""

    def object_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
        parsed: dict[str, object] = {}
        for key, value in pairs:
            if key in parsed:
                raise ValueError(f"duplicate_json_key:{context}:{key}")
            parsed[key] = value
        return parsed

    def reject_constant(value: str) -> None:
        raise ValueError(f"non_finite_json_number:{context}:{value}")

    try:
        return json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=object_pairs,
            parse_constant=reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"json_invalid:{context}") from exc


def _validate_source_only_authority(
    payload: dict[str, object],
    *,
    provider_contract: bool = False,
    current_p2_contract: bool = False,
) -> None:
    if current_p2_contract and provider_contract:
        raise ValueError("source_only_authority_contract_scope_conflict")
    if current_p2_contract:
        expected_fields = CURRENT_P2_SOURCE_ONLY_AUTHORITY_CONTRACT
    else:
        expected_fields = (
            PROVIDER_SOURCE_ONLY_AUTHORITY_FIELDS
            if provider_contract
            else SOURCE_ONLY_AUTHORITY_FIELDS
        )
    for field, expected in expected_fields.items():
        if payload.get(field) is not expected:
            raise ValueError(f"source_only_authority_invalid:{field}")
    if current_p2_contract:
        for field in CURRENT_P2_FALSE_AUTHORITY_ALIASES:
            if field in payload and payload.get(field) is not False:
                raise ValueError(f"source_only_authority_alias_invalid:{field}")
        return
    for field in (
        "runtime_authority",
        "order_authority",
        "provider_authority",
        "selection_authority",
    ):
        if payload.get(field) not in (None, False):
            raise ValueError(f"source_only_authority_escalation:{field}")


def _read_owned_json_with_raw_sha256(
    logical_path: Path,
) -> tuple[dict[str, object], str]:
    compressed_path = logical_path.with_suffix(f"{logical_path.suffix}.gz")
    if logical_path.is_symlink() or compressed_path.is_symlink():
        raise OSError(f"owned_json_symlink_forbidden:{logical_path}")
    available = [path for path in (logical_path, compressed_path) if path.exists()]
    if not available:
        raise FileNotFoundError(f"owned_json_missing:{logical_path}")
    decoded_payloads: list[bytes] = []
    for path in available:
        snapshot = _capture_stable_file(path)
        if path.suffix == ".gz":
            try:
                with gzip.open(path, "rb") as handle:
                    payload = handle.read()
            except (gzip.BadGzipFile, EOFError, OSError) as exc:
                raise ValueError(f"owned_json_gzip_invalid:{path}") from exc
        else:
            payload = path.read_bytes()
        _assert_source_unchanged_and_closed(
            path,
            snapshot,
            phase="during_owned_json_read",
        )
        decoded_payloads.append(payload)
    if any(payload != decoded_payloads[0] for payload in decoded_payloads[1:]):
        raise ValueError(f"owned_json_plain_gzip_mismatch:{logical_path}")
    try:
        parsed = _json_loads_strict(
            decoded_payloads[0],
            context=str(logical_path),
        )
    except ValueError as exc:
        raise ValueError(f"owned_json_invalid:{logical_path}:{exc}") from exc
    if not isinstance(parsed, dict):
        raise ValueError(f"owned_json_not_object:{logical_path}")
    return parsed, hashlib.sha256(decoded_payloads[0]).hexdigest()


def _read_owned_json(logical_path: Path) -> dict[str, object]:
    return _read_owned_json_with_raw_sha256(logical_path)[0]


def _validate_content_hash(
    payload: dict[str, object],
    *,
    hash_field: str,
) -> None:
    declared_hash = payload.get(hash_field)
    content = {key: value for key, value in payload.items() if key != hash_field}
    if (
        not isinstance(declared_hash, str)
        or re.fullmatch(r"[0-9a-f]{64}", declared_hash) is None
        or declared_hash != _canonical_sha256(content)
    ):
        raise ValueError(f"content_hash_invalid:{hash_field}")


def _validate_provider_content_hash(
    payload: dict[str, object],
    *,
    hash_field: str,
) -> None:
    declared_hash = payload.get(hash_field)
    content = {key: value for key, value in payload.items() if key != hash_field}
    if (
        not isinstance(declared_hash, str)
        or re.fullmatch(r"[0-9a-f]{64}", declared_hash) is None
        or declared_hash != _provider_canonical_sha256(content)
    ):
        raise ValueError(f"provider_content_hash_invalid:{hash_field}")


def _validated_sha256_field(
    payload: dict[str, object],
    *,
    field: str,
) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValueError(f"sha256_field_invalid:{field}")
    return value


def _validate_immutable_source_artifact(
    logical_path: Path,
    *,
    trade_date: date,
) -> tuple[dict[str, object], str]:
    contract = next(
        (
            (schema, hash_field)
            for pattern, schema, hash_field in IMMUTABLE_SOURCE_ARTIFACT_CONTRACTS
            if pattern.fullmatch(logical_path.name) is not None
        ),
        None,
    )
    if contract is None:
        raise ValueError("immutable_source_artifact_contract_missing")
    expected_schema, hash_field = contract
    payload, raw_sha256 = _read_owned_json_with_raw_sha256(logical_path)
    actual_schema = payload.get("schema")
    expected_schemas = (
        expected_schema
        if isinstance(expected_schema, frozenset)
        else frozenset({expected_schema})
    )
    if not isinstance(actual_schema, str) or actual_schema not in expected_schemas:
        raise ValueError("immutable_source_artifact_schema_invalid")
    embedded_target_date = payload.get("target_date")
    if actual_schema == "scalp_micro_reversion_symbol_master_v1":
        if (
            embedded_target_date not in (None, "")
            or payload.get("artifact_id")
            != f"main-ai-economic-reference-{trade_date}-symbol-master"
        ):
            raise ValueError("immutable_source_artifact_date_invalid")
    elif embedded_target_date != trade_date.isoformat():
        raise ValueError("immutable_source_artifact_date_invalid")
    _validate_source_only_authority(
        payload,
        current_p2_contract=(
            trade_date >= date.fromisoformat(CURRENT_DESIGN_ACTIVATION_DATE)
            and any(
                pattern.fullmatch(logical_path.name) is not None
                for pattern in CURRENT_P2_STRICT_AUTHORITY_NAME_PATTERNS
            )
        ),
    )
    if hash_field is not None:
        _validate_content_hash(payload, hash_field=hash_field)
    return payload, raw_sha256


def _validate_current_r2_r3_pair(
    payloads: dict[Path, dict[str, object]],
    *,
    trade_date: date,
) -> None:
    """Require every current R3 manifest to bind one exact validated R2 file."""

    if trade_date < date.fromisoformat(CURRENT_DESIGN_ACTIVATION_DATE):
        return
    rolling_name = f"main_ai_quality_rolling_paired_{trade_date}.json"
    manifest_name = f"main_ai_quality_r3_source_candidates_{trade_date}.json"
    rolling = [
        payload for path, payload in payloads.items() if path.name == rolling_name
    ]
    manifests = [
        payload for path, payload in payloads.items() if path.name == manifest_name
    ]
    if not manifests:
        return
    if len(manifests) != 1 or len(rolling) != 1:
        raise ValueError("current_r2_r3_artifact_pair_census_invalid")
    rolling_sha256 = _validated_sha256_field(
        rolling[0],
        field="artifact_content_sha256",
    )
    manifest_source_sha256 = _validated_sha256_field(
        manifests[0],
        field="source_rolling_artifact_sha256",
    )
    if manifest_source_sha256 != rolling_sha256:
        raise ValueError("current_r2_r3_exact_artifact_binding_invalid")
    # Local import avoids the cycle module's compatibility import of this
    # storage owner while making semantic candidate projection part of archive
    # validity rather than trusting self-consistent hashes alone.
    from .ai_quality_cycle import validate_r3_source_only_manifest

    validate_r3_source_only_manifest(
        manifests[0],
        source_rolling_artifact=rolling[0],
    )


def _checkpoint_paths(record_dir: Path) -> tuple[Path, Path]:
    checkpoint_path = record_dir.with_name(record_dir.name.removesuffix(".records"))
    result_path = record_dir.with_name(
        record_dir.name.replace(".checkpoint.json.records", ".json")
    )
    return checkpoint_path, result_path


def _checkpoint_record_logical_paths(record_dir: Path) -> list[Path]:
    logical: dict[str, Path] = {}
    for child in sorted(record_dir.iterdir()):
        if (
            child.name.startswith(".")
            and child.name.endswith(JSON_GENERATION_LOCK_SUFFIX)
            and child.is_file()
            and not child.is_symlink()
        ):
            continue
        if child.is_symlink() or not child.is_file():
            raise OSError(f"checkpoint_record_entry_invalid:{child}")
        matched = CHECKPOINT_RECORD_FILE_PATTERN.fullmatch(child.name)
        if matched is None:
            raise ValueError(f"checkpoint_record_filename_invalid:{child.name}")
        logical_name = child.name.removesuffix(".gz")
        logical.setdefault(logical_name, record_dir / logical_name)
    return [logical[name] for name in sorted(logical)]


def _validate_checkpoint_journal(
    record_dir: Path,
    *,
    trade_date: date,
    explicitly_superseded: bool,
) -> tuple[str, list[Path]]:
    checkpoint_path, result_path = _checkpoint_paths(record_dir)
    manifest = _read_owned_json(checkpoint_path)
    if manifest.get("schema") != CHECKPOINT_MANIFEST_SCHEMA:
        raise ValueError("checkpoint_manifest_schema_invalid")
    _validate_content_hash(
        manifest,
        hash_field="checkpoint_manifest_content_sha256",
    )
    _validate_source_only_authority(manifest)
    if manifest.get("record_directory") != record_dir.name:
        raise ValueError("checkpoint_record_directory_binding_invalid")
    # The producer's legacy manifest/record field name says "report_content",
    # but its value is the stable materialized *request census* hash. Keep the
    # persisted compatibility name while comparing it only within that domain.
    materialized_request_census_hash = _validated_sha256_field(
        manifest,
        field="materialized_report_content_sha256",
    )
    record_count = manifest.get("checkpoint_record_count")
    if (
        isinstance(record_count, bool)
        or not isinstance(record_count, int)
        or record_count < 0
    ):
        raise ValueError("checkpoint_record_count_invalid")
    logical_records = _checkpoint_record_logical_paths(record_dir)
    if record_count != len(logical_records):
        raise ValueError("checkpoint_record_count_mismatch")

    previous_hash: str | None = None
    checkpoint_results: list[dict[str, object]] = []
    for sequence, record_path in enumerate(logical_records, start=1):
        record = _read_owned_json(record_path)
        if record.get("schema") != CHECKPOINT_RECORD_SCHEMA:
            raise ValueError("checkpoint_record_schema_invalid")
        _validate_content_hash(
            record,
            hash_field="checkpoint_record_content_sha256",
        )
        _validate_source_only_authority(record)
        record_hash = str(record["checkpoint_record_content_sha256"])
        expected_name = f"{sequence:08d}-{record_hash}.json"
        if record_path.name != expected_name:
            raise ValueError("checkpoint_record_filename_binding_invalid")
        if (
            record.get("checkpoint_record_sequence") != sequence
            or record.get("previous_checkpoint_record_sha256") != previous_hash
            or record.get("materialized_report_content_sha256")
            != materialized_request_census_hash
        ):
            raise ValueError("checkpoint_record_chain_invalid")
        embedded_result = record.get("result")
        if (
            record.get("provider_call_performed") is not True
            or not isinstance(embedded_result, dict)
            or not str(record.get("result_id") or "")
            or embedded_result.get("result_id") != record.get("result_id")
        ):
            raise ValueError("checkpoint_record_result_binding_invalid")
        checkpoint_results.append(embedded_result)
        previous_hash = record_hash
    if manifest.get("checkpoint_head_sha256") != previous_hash:
        raise ValueError("checkpoint_manifest_head_mismatch")
    if manifest.get("provider_call_performed") is not bool(record_count):
        raise ValueError("checkpoint_provider_call_census_invalid")

    if explicitly_superseded:
        return "superseded", logical_records
    result_available = (
        result_path.exists()
        or result_path.with_suffix(f"{result_path.suffix}.gz").exists()
    )
    if not result_available:
        return "incomplete_resumable", logical_records
    result = _read_owned_json(result_path)
    if result.get("schema") != TERMINAL_EXECUTION_RESULT_SCHEMA:
        raise ValueError("checkpoint_sibling_result_schema_invalid")
    _validate_content_hash(result, hash_field="report_content_sha256")
    _validate_source_only_authority(result)
    if result.get("target_date") != trade_date.isoformat():
        raise ValueError("checkpoint_sibling_result_date_invalid")
    _validated_sha256_field(
        result,
        field="materialized_report_content_sha256",
    )
    result_request_census_hash = _validated_sha256_field(
        result,
        field="materialized_request_census_sha256",
    )
    if result_request_census_hash != materialized_request_census_hash:
        return "superseded", logical_records
    if result.get("status") != TERMINAL_EXECUTION_STATUS:
        return "incomplete_resumable", logical_records
    request_count = result.get("request_count")
    result_count = result.get("result_count")
    deferred_count = result.get("deferred_request_count")
    if (
        isinstance(request_count, bool)
        or not isinstance(request_count, int)
        or request_count < 0
        or isinstance(result_count, bool)
        or not isinstance(result_count, int)
        or result_count != request_count
        or deferred_count != 0
    ):
        raise ValueError("checkpoint_terminal_result_census_invalid")
    if (
        trade_date >= date.fromisoformat(CURRENT_DESIGN_ACTIVATION_DATE)
        and result.get("ablation_design_version") != CURRENT_DESIGN_VERSION
    ):
        raise ValueError("checkpoint_current_terminal_design_required")
    if result.get("ablation_design_version") == CURRENT_DESIGN_VERSION:
        if any(
            record_result.get("ablation_design_version") != CURRENT_DESIGN_VERSION
            for record_result in checkpoint_results
        ):
            raise ValueError("checkpoint_current_record_design_invalid")
        for record_path in logical_records:
            record = _read_owned_json(record_path)
            if any(
                record.get(field) != expected
                for field, expected in CHECKPOINT_RECONSTRUCTED_CONTRACT.items()
            ):
                raise ValueError("checkpoint_current_record_contract_invalid")
        reconstructed_content = {
            "schema": CHECKPOINT_RECONSTRUCTED_SCHEMA,
            "materialized_report_content_sha256": materialized_request_census_hash,
            "checkpoint_record_count": record_count,
            "checkpoint_head_sha256": previous_hash,
            "results": checkpoint_results,
            "provider_call_performed": bool(record_count),
            **CHECKPOINT_RECONSTRUCTED_CONTRACT,
        }
        if (
            record_count != request_count
            or result.get("results") != checkpoint_results
            or result.get("result_ids")
            != [row.get("result_id") for row in checkpoint_results]
            or result.get("checkpoint_journal_schema")
            != CHECKPOINT_RECONSTRUCTED_SCHEMA
            or result.get("checkpoint_journal_record_count") != record_count
            or result.get("checkpoint_journal_head_sha256") != previous_hash
            or result.get("checkpoint_journal_reconstructed_content_sha256")
            != _canonical_sha256(reconstructed_content)
        ):
            raise ValueError("checkpoint_current_terminal_companion_binding_invalid")
    return "terminal", logical_records


def _classify_report_artifact_set(
    candidates: Sequence[Path],
    *,
    trade_date: date,
    explicitly_superseded: bool,
) -> tuple[str, dict[Path, str]]:
    if not candidates:
        raise ValueError("report_artifact_set_empty")
    validated_raw_sha256s: dict[Path, str] = {}
    current_p2_contract = trade_date >= date.fromisoformat(
        CURRENT_DESIGN_ACTIVATION_DATE
    )

    def read_candidate(path: Path) -> dict[str, object]:
        payload, raw_sha256 = _read_owned_json_with_raw_sha256(path)
        validated_raw_sha256s[path] = raw_sha256
        return payload

    if explicitly_superseded:
        for path in candidates:
            read_candidate(path)
        return "explicitly_superseded", validated_raw_sha256s
    result_paths = [
        path
        for path in candidates
        if path.name
        == f"ai_micro_reversion_three_arm_offline_results_{trade_date}.json"
    ]
    if not result_paths:
        return "incomplete_resumable", validated_raw_sha256s
    if len(result_paths) != 1:
        raise ValueError("report_artifact_set_execution_result_ambiguous")
    result = read_candidate(result_paths[0])
    if result.get("schema") != TERMINAL_EXECUTION_RESULT_SCHEMA:
        raise ValueError("report_artifact_set_execution_result_schema_invalid")
    _validate_content_hash(result, hash_field="report_content_sha256")
    _validate_source_only_authority(
        result,
        current_p2_contract=current_p2_contract,
    )
    if result.get("target_date") != trade_date.isoformat():
        raise ValueError("report_artifact_set_execution_result_date_invalid")
    status = result.get("status")
    if status in RESUMABLE_EXECUTION_STATUSES:
        return "incomplete_resumable", validated_raw_sha256s
    if status != TERMINAL_EXECUTION_STATUS:
        raise ValueError("report_artifact_set_execution_result_status_invalid")
    request_count = result.get("request_count")
    result_count = result.get("result_count")
    if (
        isinstance(request_count, bool)
        or not isinstance(request_count, int)
        or request_count < 0
        or isinstance(result_count, bool)
        or not isinstance(result_count, int)
        or result_count != request_count
        or result.get("deferred_request_count") != 0
    ):
        raise ValueError("report_artifact_set_terminal_census_invalid")
    materialized_paths = [
        path
        for path in candidates
        if path.name
        == f"ai_micro_reversion_materialized_replay_requests_{trade_date}.json"
    ]
    if not materialized_paths:
        return "incomplete_resumable", validated_raw_sha256s
    if len(materialized_paths) != 1:
        raise ValueError("report_artifact_set_materialized_ambiguous")
    materialized = read_candidate(materialized_paths[0])
    if materialized.get("schema") != (
        "ai_micro_reversion_materialized_replay_requests_v1"
    ):
        raise ValueError("report_artifact_set_materialized_schema_invalid")
    _validate_content_hash(materialized, hash_field="report_content_sha256")
    _validate_source_only_authority(
        materialized,
        current_p2_contract=current_p2_contract,
    )
    if materialized.get("target_date") != trade_date.isoformat() or result.get(
        "materialized_report_content_sha256"
    ) != materialized.get("report_content_sha256"):
        raise ValueError("report_artifact_set_materialized_binding_invalid")
    source_bundle_paths = [
        path
        for path in candidates
        if path.name == f"ai_micro_reversion_replay_source_bundle_{trade_date}.json"
    ]
    if len(source_bundle_paths) > 1:
        raise ValueError("report_artifact_set_source_bundle_ambiguous")
    if source_bundle_paths:
        source_bundle = read_candidate(source_bundle_paths[0])
        if source_bundle.get("schema") != "ai_micro_reversion_replay_source_bundle_v1":
            raise ValueError("report_artifact_set_source_bundle_schema_invalid")
        _validate_content_hash(
            source_bundle,
            hash_field="source_bundle_content_sha256",
        )
        _validate_source_only_authority(
            source_bundle,
            current_p2_contract=current_p2_contract,
        )
        if source_bundle.get("target_date") != trade_date.isoformat():
            raise ValueError("report_artifact_set_source_bundle_date_invalid")
        if materialized.get("source_bundle_content_sha256") != source_bundle.get(
            "source_bundle_content_sha256"
        ) or materialized.get("source_bundle_artifact_sha256") != _canonical_sha256(
            source_bundle
        ):
            raise ValueError("report_artifact_set_source_bundle_binding_invalid")
    return "terminal", validated_raw_sha256s


def _provider_budget_paths(ledger_path: Path) -> tuple[Path, Path]:
    return (
        ledger_path.with_suffix(".manifest.json"),
        ledger_path.with_suffix(".json"),
    )


@contextmanager
def _provider_budget_archive_lock(ledger_path: Path):
    lock_path = ledger_path.with_suffix(".lock")
    if lock_path.is_symlink() or not lock_path.is_file():
        raise OSError("provider budget archive lock must be a regular file")
    descriptor = os.open(
        lock_path,
        os.O_RDWR
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0),
    )
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise OSError("provider budget archive lock must be a regular file")
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise OSError("provider_budget_archive_lock_busy") from exc
        yield
    finally:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        finally:
            os.close(descriptor)


def _read_owned_bytes(logical_path: Path) -> bytes:
    compressed_path = logical_path.with_suffix(f"{logical_path.suffix}.gz")
    if logical_path.is_symlink() or compressed_path.is_symlink():
        raise OSError(f"owned_bytes_symlink_forbidden:{logical_path}")
    available = [path for path in (logical_path, compressed_path) if path.exists()]
    if not available:
        raise FileNotFoundError(f"owned_bytes_missing:{logical_path}")
    payloads: list[bytes] = []
    for path in available:
        snapshot = _capture_stable_file(path)
        if path.suffix == ".gz":
            try:
                with gzip.open(path, "rb") as handle:
                    payload = handle.read()
            except (gzip.BadGzipFile, EOFError, OSError) as exc:
                raise ValueError(f"owned_gzip_invalid:{path}") from exc
        else:
            payload = path.read_bytes()
        _assert_source_unchanged_and_closed(
            path,
            snapshot,
            phase="during_owned_bytes_read",
        )
        payloads.append(payload)
    if any(payload != payloads[0] for payload in payloads[1:]):
        raise ValueError(f"owned_plain_gzip_mismatch:{logical_path}")
    return payloads[0]


def _validate_current_provider_budget_semantics(
    *,
    records: Sequence[dict[str, object]],
    manifest: dict[str, object],
    summary: dict[str, object],
) -> None:
    """Cross-bind current provider records, manifest, and summary contracts."""

    if not records:
        raise ValueError("provider_budget_current_ledger_empty")
    if set(manifest) != PROVIDER_BUDGET_MANIFEST_FIELDS:
        raise ValueError("provider_budget_current_manifest_fields_invalid")
    if set(summary) != PROVIDER_BUDGET_SUMMARY_FIELDS:
        raise ValueError("provider_budget_current_summary_fields_invalid")
    for payload in (*records, manifest, summary):
        if any(
            payload.get(field) != expected
            for field, expected in PROVIDER_BUDGET_AUTHORITY_CONTRACT.items()
        ):
            raise ValueError("provider_budget_current_authority_contract_invalid")
    first = records[0]
    common_fields = (
        "budget_contract_sha256",
        "pricing_artifact_id",
        "pricing_artifact_content_sha256",
        "pricing_artifact_file_sha256",
        "raw_pricing_source_bytes_sha256",
        "raw_pricing_source_path",
        "raw_pricing_source_size_bytes",
        "pricing_effective_from",
        "pricing_effective_to",
    )
    budget_contract = first.get("budget_contract")
    if (
        not isinstance(budget_contract, dict)
        or budget_contract.get("schema") != "ai_provider_budget_contract_v1"
        or budget_contract.get("execution_date") != first.get("execution_date")
        or budget_contract.get("pricing_artifact_content_sha256")
        != first.get("pricing_artifact_content_sha256")
        or budget_contract.get("pricing_basis") != summary.get("pricing_basis")
        or first.get("budget_contract_sha256")
        != _provider_canonical_sha256(budget_contract)
    ):
        raise ValueError("provider_budget_contract_hash_invalid")
    try:
        provider_execution_date = date.fromisoformat(str(first.get("execution_date")))
    except ValueError as exc:
        raise ValueError("provider_budget_execution_date_invalid") from exc
    reservations: dict[str, dict[str, object]] = {}
    settlements: dict[str, dict[str, object]] = {}
    reservation_ids: set[str] = set()
    provider_model_counts: dict[tuple[str, str], int] = {}
    previous_recorded_at: datetime | None = None
    for record in records:
        if any(record.get(field) != first.get(field) for field in common_fields):
            raise ValueError("provider_budget_record_contract_conflict")
        if record.get("budget_contract") != budget_contract or record.get(
            "budget_contract_sha256"
        ) != _provider_canonical_sha256(record.get("budget_contract")):
            raise ValueError("provider_budget_record_contract_hash_invalid")
        event_type = record.get("event_type")
        expected_record_fields = (
            PROVIDER_BUDGET_RESERVATION_RECORD_FIELDS
            if event_type == "reservation"
            else (
                PROVIDER_BUDGET_SETTLEMENT_RECORD_FIELDS
                if event_type == "settlement"
                else frozenset()
            )
        )
        if not expected_record_fields or set(record) != expected_record_fields:
            raise ValueError("provider_budget_current_record_fields_invalid")
        identity_hash = str(record.get("attempt_identity_sha256") or "")
        reservation_id = str(record.get("reservation_id") or "")
        attempt_identity = record.get("attempt_identity")
        if (
            event_type not in {"reservation", "settlement"}
            or re.fullmatch(r"[0-9a-f]{64}", identity_hash) is None
            or not reservation_id
            or not isinstance(attempt_identity, dict)
            or set(attempt_identity)
            != {
                "target_date",
                "parent_id",
                "request_id",
                "arm",
                "provider",
                "model",
                "attempt_number",
            }
            or _provider_canonical_sha256(attempt_identity) != identity_hash
        ):
            raise ValueError("provider_budget_record_attempt_identity_invalid")
        try:
            target_date = date.fromisoformat(str(attempt_identity.get("target_date")))
            recorded_at = datetime.fromisoformat(str(record.get("recorded_at")))
        except ValueError as exc:
            raise ValueError("provider_budget_record_time_invalid") from exc
        if (
            target_date > provider_execution_date
            or recorded_at.tzinfo is None
            or recorded_at.utcoffset() is None
            or (previous_recorded_at is not None and recorded_at < previous_recorded_at)
            or isinstance(attempt_identity.get("attempt_number"), bool)
            or not isinstance(attempt_identity.get("attempt_number"), int)
            or int(attempt_identity["attempt_number"]) <= 0
            or any(
                not str(attempt_identity.get(field) or "").strip()
                for field in (
                    "parent_id",
                    "request_id",
                    "arm",
                    "provider",
                    "model",
                )
            )
        ):
            raise ValueError("provider_budget_record_time_or_identity_invalid")
        previous_recorded_at = recorded_at
        if event_type == "reservation":
            expected_reservation_id = (
                "provider-reservation-"
                + _provider_canonical_sha256(
                    {
                        "execution_date": provider_execution_date.isoformat(),
                        "attempt_identity_sha256": identity_hash,
                        "pricing_artifact_content_sha256": first.get(
                            "pricing_artifact_content_sha256"
                        ),
                    }
                )[:32]
            )
            if (
                identity_hash in reservations
                or identity_hash in settlements
                or reservation_id in reservation_ids
                or reservation_id != expected_reservation_id
                or recorded_at.astimezone(KST).date() != provider_execution_date
            ):
                raise ValueError("provider_budget_reservation_duplicate")
            reservations[identity_hash] = record
            reservation_ids.add(reservation_id)
            provider = str(attempt_identity.get("provider") or "")
            model = str(attempt_identity.get("model") or "")
            if not provider or not model:
                raise ValueError("provider_budget_provider_model_missing")
            key = (provider, model)
            provider_model_counts[key] = provider_model_counts.get(key, 0) + 1
        else:
            reservation = reservations.get(identity_hash)
            if (
                reservation is None
                or identity_hash in settlements
                or reservation.get("reservation_id") != reservation_id
            ):
                raise ValueError("provider_budget_settlement_binding_invalid")
            settlements[identity_hash] = record
    if (
        manifest.get("budget_contract_sha256") != first.get("budget_contract_sha256")
        or summary.get("budget_contract_sha256") != first.get("budget_contract_sha256")
        or any(summary.get(field) != first.get(field) for field in common_fields[1:])
        or summary.get("pricing_basis") != budget_contract.get("pricing_basis")
        or summary.get("reservation_count") != len(reservations)
        or summary.get("settlement_count") != len(settlements)
        or summary.get("outstanding_reservation_count")
        != len(reservations) - len(settlements)
    ):
        raise ValueError("provider_budget_manifest_summary_contract_binding_invalid")
    expected_counts = [
        {"provider": key[0], "model": key[1], "attempt_count": count}
        for key, count in sorted(provider_model_counts.items())
    ]
    if summary.get("provider_model_attempt_counts") != expected_counts:
        raise ValueError("provider_budget_summary_attempt_census_invalid")


def _validate_provider_budget_ledger(
    ledger_path: Path,
    *,
    execution_date: date,
) -> None:
    ledger_bytes = _read_owned_bytes(ledger_path)
    if ledger_bytes and not ledger_bytes.endswith(b"\n"):
        raise ValueError("provider_budget_ledger_partial_tail")
    previous_hash: str | None = None
    records: list[dict[str, object]] = []
    for sequence, raw_line in enumerate(ledger_bytes.splitlines(), start=1):
        try:
            record = _json_loads_strict(
                raw_line,
                context=f"{ledger_path}:{sequence}",
            )
        except ValueError as exc:
            raise ValueError("provider_budget_ledger_json_invalid") from exc
        if not isinstance(record, dict):
            raise ValueError("provider_budget_ledger_row_not_object")
        if record.get("schema") != PROVIDER_BUDGET_LEDGER_RECORD_SCHEMA:
            raise ValueError("provider_budget_ledger_record_schema_invalid")
        _validate_provider_content_hash(
            record,
            hash_field="record_content_sha256",
        )
        _validate_source_only_authority(record, provider_contract=True)
        if (
            record.get("sequence") != sequence
            or record.get("previous_record_sha256") != previous_hash
            or record.get("execution_date") != execution_date.isoformat()
        ):
            raise ValueError("provider_budget_ledger_chain_invalid")
        previous_hash = str(record["record_content_sha256"])
        records.append(record)

    manifest_path, summary_path = _provider_budget_paths(ledger_path)
    manifest = _read_owned_json(manifest_path)
    if manifest.get("schema") != PROVIDER_BUDGET_LEDGER_MANIFEST_SCHEMA:
        raise ValueError("provider_budget_manifest_schema_invalid")
    _validate_provider_content_hash(
        manifest,
        hash_field="manifest_content_sha256",
    )
    _validate_source_only_authority(manifest, provider_contract=True)
    expected_ledger_hash = hashlib.sha256(ledger_bytes).hexdigest()
    if (
        manifest.get("execution_date") != execution_date.isoformat()
        or manifest.get("ledger_file") != ledger_path.name
        or manifest.get("ledger_size_bytes") != len(ledger_bytes)
        or manifest.get("ledger_bytes_sha256") != expected_ledger_hash
        or manifest.get("record_count") != len(records)
        or manifest.get("head_record_sha256") != previous_hash
    ):
        raise ValueError("provider_budget_manifest_ledger_binding_invalid")

    summary = _read_owned_json(summary_path)
    if summary.get("schema") != PROVIDER_BUDGET_SUMMARY_SCHEMA:
        raise ValueError("provider_budget_summary_schema_invalid")
    _validate_provider_content_hash(
        summary,
        hash_field="summary_content_sha256",
    )
    _validate_source_only_authority(summary, provider_contract=True)
    if (
        summary.get("execution_date") != execution_date.isoformat()
        or summary.get("ledger_record_count") != len(records)
        or summary.get("ledger_head_sha256") != previous_hash
        or summary.get("ledger_bytes_sha256") != expected_ledger_hash
    ):
        raise ValueError("provider_budget_summary_ledger_binding_invalid")
    if execution_date >= date.fromisoformat(CURRENT_DESIGN_ACTIVATION_DATE):
        _validate_current_provider_budget_semantics(
            records=records,
            manifest=manifest,
            summary=summary,
        )


def _remap_actions(
    actions: Sequence[StorageMaintenanceAction],
    *,
    names: dict[str, str],
) -> list[StorageMaintenanceAction]:
    return [
        StorageMaintenanceAction(
            action=names.get(action.action, action.action),
            path=action.path,
            trade_date=action.trade_date,
            source_bytes=action.source_bytes,
            applied=action.applied,
        )
        for action in actions
    ]


def _maintain_one_provider_budget_ledger(
    ledger_path: Path,
    *,
    trade_date: date,
    as_of_date: date,
    protected_dates: set[date],
    apply: bool,
) -> tuple[list[StorageMaintenanceAction], dict[str, str] | None, int, int]:
    with _provider_budget_archive_lock(ledger_path):
        compressed_path = ledger_path.with_suffix(f"{ledger_path.suffix}.gz")
        physical_paths = [
            path
            for path in (ledger_path, compressed_path)
            if path.exists() and path.is_file() and not path.is_symlink()
        ]
        physical_bytes = sum(path.stat().st_size for path in physical_paths)
        manifest_path, summary_path = _provider_budget_paths(ledger_path)
        sidecar_snapshots = {
            sidecar: _capture_stable_file(sidecar)
            for sidecar in (manifest_path, summary_path)
        }
        _validate_provider_budget_ledger(
            ledger_path,
            execution_date=trade_date,
        )
        age_days = (as_of_date - trade_date).days
        if trade_date in protected_dates or age_days <= 0 or not ledger_path.exists():
            for sidecar, snapshot in sidecar_snapshots.items():
                _assert_source_unchanged_and_closed(
                    sidecar,
                    snapshot,
                    phase="after_provider_budget_validation",
                )
            return [], None, physical_bytes, age_days
        if not apply:
            for sidecar, snapshot in sidecar_snapshots.items():
                _assert_source_unchanged_and_closed(
                    sidecar,
                    snapshot,
                    phase="after_provider_budget_dry_run",
                )
            return (
                [
                    StorageMaintenanceAction(
                        action="compress_provider_budget_jsonl",
                        path=str(ledger_path),
                        trade_date=trade_date.isoformat(),
                        source_bytes=ledger_path.stat().st_size,
                        applied=False,
                    )
                ],
                None,
                physical_bytes,
                age_days,
            )
        _preflight_compression_group([ledger_path], None)
        group_actions, failure = _compress_group_verified(
            [ledger_path],
            manifest_path=None,
            trade_date=trade_date,
            as_of_date=as_of_date,
        )
        for sidecar, snapshot in sidecar_snapshots.items():
            _assert_source_unchanged_and_closed(
                sidecar,
                snapshot,
                phase="after_provider_budget_compression",
            )
        return (
            _remap_actions(
                group_actions,
                names={
                    "compress_jsonl": "compress_provider_budget_jsonl",
                    "finalize_verified_compression": (
                        "finalize_verified_provider_budget_compression"
                    ),
                    "publish_verified_gzip_source_preserved": (
                        "publish_verified_provider_budget_gzip_source_preserved"
                    ),
                },
            ),
            failure,
            physical_bytes,
            age_days,
        )


def _maintain_checkpoint_journal_storage(
    root: Path,
    *,
    as_of_date: date,
    protected_dates: set[date],
    retention_days: int,
    apply: bool,
) -> tuple[list[StorageMaintenanceAction], list[dict[str, str]], dict[str, int]]:
    actions: list[StorageMaintenanceAction] = []
    failures: list[dict[str, str]] = []
    census = {
        "journal_count": 0,
        "journal_bytes": 0,
        "terminal_count": 0,
        "superseded_count": 0,
        "incomplete_resumable_count": 0,
        "retention_candidate_count": 0,
        "retention_candidate_bytes": 0,
        "stale_workorder_count": 0,
        "stale_workorder_bytes": 0,
    }
    try:
        candidates = sorted(
            path
            for path in root.rglob("*.checkpoint.json.records")
            if CHECKPOINT_RECORD_DIRECTORY_PATTERN.fullmatch(path.name) is not None
        )
    except OSError as exc:
        failures.append(
            _failure_row(
                trade_date="unknown",
                path=root,
                exc=exc,
                candidate_count=0,
                candidate_bytes=0,
                recovery_required=False,
            )
        )
        return actions, failures, census
    for raw_record_dir in candidates:
        matched = CHECKPOINT_RECORD_DIRECTORY_PATTERN.fullmatch(raw_record_dir.name)
        if matched is None:
            continue
        try:
            trade_date = date.fromisoformat(matched.group(1))
        except ValueError:
            continue
        record_dir = raw_record_dir
        physical_bytes = 0
        record_count = 0
        checkpoint_locks = ExitStack()
        try:
            record_dir = _validated_descendant(root, record_dir)
            if record_dir.is_symlink() or not record_dir.is_dir():
                raise OSError("checkpoint record journal must be a real directory")
            checkpoint_path, result_path = _checkpoint_paths(record_dir)
            if apply:
                checkpoint_locks.enter_context(
                    json_artifact_generation_lock(
                        checkpoint_path,
                        exclusive=True,
                        blocking=False,
                    )
                )
                checkpoint_locks.enter_context(
                    json_artifact_generation_lock(
                        result_path,
                        exclusive=True,
                        blocking=False,
                    )
                )
                for record_path in _checkpoint_record_logical_paths(record_dir):
                    checkpoint_locks.enter_context(
                        json_artifact_generation_lock(
                            record_path,
                            exclusive=True,
                            blocking=False,
                        )
                    )
            physical_bytes = _tree_bytes(record_dir)
            relative_parts = record_dir.relative_to(root).parts[:-1]
            explicitly_superseded = "superseded" in relative_parts
            state, logical_records = _validate_checkpoint_journal(
                record_dir,
                trade_date=trade_date,
                explicitly_superseded=explicitly_superseded,
            )
            record_count = len(logical_records)
            census["journal_count"] += 1
            census["journal_bytes"] += physical_bytes
            census[f"{state}_count"] += 1
            age_days = (as_of_date - trade_date).days
            if age_days > retention_days:
                census["retention_candidate_count"] += 1
                census["retention_candidate_bytes"] += physical_bytes
                if state == "incomplete_resumable":
                    census["stale_workorder_count"] += 1
                    census["stale_workorder_bytes"] += physical_bytes
            if (
                state == "incomplete_resumable"
                or trade_date in protected_dates
                or age_days <= 0
            ):
                continue
            plain_records = [path for path in logical_records if path.exists()]
            if not plain_records:
                continue
            if not apply:
                actions.extend(
                    StorageMaintenanceAction(
                        action="compress_checkpoint_record_json",
                        path=str(path),
                        trade_date=trade_date.isoformat(),
                        source_bytes=path.stat().st_size,
                        applied=False,
                    )
                    for path in plain_records
                )
                continue
            _preflight_compression_group(plain_records, None)
            group_actions, failure = _compress_group_verified(
                plain_records,
                manifest_path=None,
                trade_date=trade_date,
                as_of_date=as_of_date,
            )
            actions.extend(
                _remap_actions(
                    group_actions,
                    names={
                        "compress_jsonl": "compress_checkpoint_record_json",
                        "finalize_verified_compression": (
                            "finalize_verified_checkpoint_record_compression"
                        ),
                        "publish_verified_gzip_source_preserved": (
                            "publish_verified_checkpoint_record_gzip_source_preserved"
                        ),
                    },
                )
            )
            if failure is not None:
                failures.append(failure)
        except Exception as exc:
            failures.append(
                _failure_row(
                    trade_date=trade_date,
                    path=record_dir,
                    exc=exc,
                    candidate_count=record_count or 1,
                    candidate_bytes=physical_bytes,
                    recovery_required=False,
                )
            )
        finally:
            checkpoint_locks.close()
    return actions, failures, census


def _maintain_provider_budget_ledger_storage(
    root: Path,
    *,
    as_of_date: date,
    protected_dates: set[date],
    retention_days: int,
    apply: bool,
) -> tuple[list[StorageMaintenanceAction], list[dict[str, str]], dict[str, int]]:
    actions: list[StorageMaintenanceAction] = []
    failures: list[dict[str, str]] = []
    census = {
        "ledger_count": 0,
        "ledger_bytes": 0,
        "retention_candidate_count": 0,
        "retention_candidate_bytes": 0,
    }
    logical_ledgers: dict[Path, date] = {}
    try:
        children = sorted(root.iterdir())
    except OSError as exc:
        failures.append(
            _failure_row(
                trade_date="unknown",
                path=root,
                exc=exc,
                candidate_count=0,
                candidate_bytes=0,
                recovery_required=False,
            )
        )
        return actions, failures, census
    for child in children:
        matched = PROVIDER_BUDGET_LEDGER_PATTERN.fullmatch(child.name)
        if matched is None:
            continue
        logical = child.with_suffix("") if child.suffix == ".gz" else child
        try:
            logical_ledgers[logical] = date.fromisoformat(matched.group(1))
        except ValueError:
            continue
    for raw_ledger, trade_date in sorted(
        logical_ledgers.items(), key=lambda item: str(item[0])
    ):
        ledger_path = raw_ledger
        physical_bytes = 0
        try:
            ledger_path = _validated_descendant(root, ledger_path)
            ledger_actions, failure, physical_bytes, age_days = (
                _maintain_one_provider_budget_ledger(
                    ledger_path,
                    trade_date=trade_date,
                    as_of_date=as_of_date,
                    protected_dates=protected_dates,
                    apply=apply,
                )
            )
            actions.extend(ledger_actions)
            if failure is not None:
                failures.append(failure)
            census["ledger_count"] += 1
            census["ledger_bytes"] += physical_bytes
            if age_days > retention_days:
                census["retention_candidate_count"] += 1
                census["retention_candidate_bytes"] += physical_bytes
        except Exception as exc:
            failures.append(
                _failure_row(
                    trade_date=trade_date,
                    path=ledger_path,
                    exc=exc,
                    candidate_count=1,
                    candidate_bytes=physical_bytes,
                    recovery_required=bool(
                        ledger_path.exists()
                        and ledger_path.with_suffix(f"{ledger_path.suffix}.gz").exists()
                    ),
                )
            )
    return actions, failures, census


def _kst_date_from_timestamp(value: object, *, field: str) -> date:
    try:
        parsed = datetime.fromisoformat(str(value or ""))
    except ValueError as exc:
        raise ValueError(f"exact_ai_artifact_timestamp_invalid:{field}") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"exact_ai_artifact_timestamp_timezone_missing:{field}")
    return parsed.astimezone(KST).date()


def _validate_exact_ai_jsonl(
    logical: Path,
    *,
    trade_date: date,
    expected_schema: str,
    timestamp_field: str,
    generation: ArtifactGenerationLease | None = None,
) -> dict[str, object]:
    provenance: dict[str, object] = {}
    row_count = 0
    for row in iter_jsonl_objects_strict(
        logical,
        provenance=provenance,
        generation=generation,
    ):
        row_count += 1
        if row.get("schema") != expected_schema:
            raise ValueError(f"exact_ai_artifact_schema_invalid:{logical}:{row_count}")
        if (
            _kst_date_from_timestamp(
                row.get(timestamp_field),
                field=timestamp_field,
            )
            != trade_date
        ):
            raise ValueError(f"exact_ai_artifact_embedded_date_invalid:{logical}")
    if provenance.get("source_json_object_row_count") != row_count:
        raise ValueError(f"exact_ai_artifact_row_census_mismatch:{logical}")
    return {
        "decoded_content_sha256": provenance["source_content_sha256"],
        "decoded_content_bytes": provenance["source_content_bytes"],
        "json_object_row_count": row_count,
        "physical_representations": provenance["physical_representations"],
    }


def _validate_exact_ai_json(
    logical: Path,
    *,
    trade_date: date,
    expected_schema: str,
    generation: ArtifactGenerationLease | None = None,
) -> dict[str, object]:
    owned_logical = (
        generation.bound_path(logical.name) if generation is not None else logical
    )
    physical_before = _exact_ai_physical_receipts(owned_logical)
    raw = _read_owned_bytes(owned_logical)
    physical_after = _exact_ai_physical_receipts(owned_logical)
    if physical_after != physical_before:
        raise OSError(f"exact_ai_artifact_changed_during_validation:{logical}")
    payload = _json_loads_strict(raw, context=str(logical))
    if not isinstance(payload, dict):
        raise ValueError(f"exact_ai_artifact_json_not_object:{logical}")
    if (
        payload.get("schema") != expected_schema
        or payload.get("target_date") != trade_date.isoformat()
    ):
        raise ValueError(f"exact_ai_artifact_json_contract_invalid:{logical}")
    return {
        "decoded_content_sha256": hashlib.sha256(raw).hexdigest(),
        "decoded_content_bytes": len(raw),
        "json_object_row_count": 1,
        "physical_representations": physical_before,
    }


def _exact_ai_physical_receipts(logical: Path) -> list[dict[str, object]]:
    receipts: list[dict[str, object]] = []
    for compression, physical in (
        ("plain", logical),
        ("gzip", logical.with_suffix(f"{logical.suffix}.gz")),
    ):
        try:
            snapshot = _capture_stable_file(physical)
        except FileNotFoundError:
            continue
        receipts.append(
            {
                "compression": compression,
                "stored_bytes": snapshot[2],
                "stored_sha256": snapshot[4],
            }
        )
    if not receipts:
        raise FileNotFoundError(f"exact_ai_artifact_missing:{logical}")
    return receipts


def _maintain_exact_ai_artifact_storage(
    roots: Sequence[Path],
    *,
    as_of_date: date,
    protected_dates: set[date],
    retention_days: int,
    apply: bool,
) -> tuple[
    list[StorageMaintenanceAction],
    list[dict[str, str]],
    dict[str, object],
    list[Path],
]:
    actions: list[StorageMaintenanceAction] = []
    failures: list[dict[str, str]] = []
    normalized_roots: list[Path] = []
    logical_candidates: dict[
        Path,
        tuple[Path, date, str, str, str],
    ] = {}
    receipts: list[dict[str, object]] = []
    census: dict[str, object] = {
        "schema": EXACT_AI_ARTIFACT_MAINTENANCE_SCHEMA,
        "artifact_count": 0,
        "artifact_bytes": 0,
        "jsonl_artifact_count": 0,
        "json_artifact_count": 0,
        "protected_artifact_count": 0,
        "retention_candidate_count": 0,
        "retention_candidate_bytes": 0,
        "artifact_receipts": receipts,
        "retention_days": retention_days,
        "retention_policy": (
            "verified_gzip_retained_no_automatic_deletion_or_offload_authority"
        ),
        "deletion_performed": False,
        "archive_offload_performed": False,
    }

    for raw_root in roots:
        lexical_root = Path(raw_root).absolute()
        try:
            root_state = lexical_root.lstat()
        except FileNotFoundError:
            continue
        except OSError as exc:
            failures.append(
                _failure_row(
                    trade_date="unknown",
                    path=lexical_root,
                    exc=exc,
                    candidate_count=0,
                    candidate_bytes=0,
                    recovery_required=False,
                )
            )
            continue
        contract = EXACT_AI_ARTIFACT_ROOT_CONTRACTS.get(lexical_root.name)
        if contract is None or not stat.S_ISDIR(root_state.st_mode):
            failures.append(
                _failure_row(
                    trade_date="unknown",
                    path=lexical_root,
                    exc=ValueError("exact AI artifact root contract invalid"),
                    candidate_count=0,
                    candidate_bytes=0,
                    recovery_required=False,
                )
            )
            continue
        root = lexical_root.resolve()
        root_state_after = lexical_root.lstat()
        if (
            not stat.S_ISDIR(root_state_after.st_mode)
            or root_state_after.st_dev != root_state.st_dev
            or root_state_after.st_ino != root_state.st_ino
        ):
            failures.append(
                _failure_row(
                    trade_date="unknown",
                    path=lexical_root,
                    exc=OSError("exact AI artifact root changed during validation"),
                    candidate_count=0,
                    candidate_bytes=0,
                    recovery_required=False,
                )
            )
            continue
        if root in normalized_roots:
            continue
        normalized_roots.append(root)
        pattern, artifact_kind, expected_schema, timestamp_field = contract
        try:
            children = sorted(root.iterdir())
        except OSError as exc:
            failures.append(
                _failure_row(
                    trade_date="unknown",
                    path=root,
                    exc=exc,
                    candidate_count=0,
                    candidate_bytes=0,
                    recovery_required=False,
                )
            )
            continue
        for child in children:
            if child.name.startswith(".") and child.name.endswith(
                (
                    JSON_GENERATION_LOCK_SUFFIX,
                    JSONL_GENERATION_LOCK_SUFFIX,
                )
            ):
                continue
            if child.is_symlink():
                failures.append(
                    _failure_row(
                        trade_date="unknown",
                        path=child,
                        exc=OSError("exact AI artifact symlink forbidden"),
                        candidate_count=1,
                        candidate_bytes=0,
                        recovery_required=False,
                    )
                )
                continue
            logical_name = child.name.removesuffix(".gz")
            matched = pattern.fullmatch(logical_name)
            if matched is None:
                continue
            try:
                trade_date = date.fromisoformat(matched.group(1))
                logical = _validated_descendant(root, root / logical_name)
            except Exception as exc:
                failures.append(
                    _failure_row(
                        trade_date=matched.group(1),
                        path=child,
                        exc=exc,
                        candidate_count=1,
                        candidate_bytes=0,
                        recovery_required=False,
                    )
                )
                continue
            logical_candidates[logical] = (
                root,
                trade_date,
                artifact_kind,
                expected_schema,
                timestamp_field,
            )

    for logical, (
        _,
        trade_date,
        artifact_kind,
        expected_schema,
        timestamp_field,
    ) in sorted(logical_candidates.items(), key=lambda item: str(item[0])):
        physical_bytes = 0
        try:
            if trade_date > as_of_date and trade_date not in protected_dates:
                raise ValueError("exact AI artifact future date invalid")
            is_protected = trade_date in protected_dates
            lock_context = (
                jsonl_artifact_generation_lock(
                    logical,
                    exclusive=not is_protected,
                    blocking=False,
                )
                if artifact_kind == "jsonl"
                else json_artifact_generation_lock(
                    logical,
                    exclusive=not is_protected,
                    blocking=False,
                )
            )
            with lock_context if apply else nullcontext(None) as generation:
                pinned_generation = (
                    generation
                    if isinstance(generation, ArtifactGenerationLease)
                    else None
                )
                owned_logical = (
                    pinned_generation.bound_path(logical.name)
                    if pinned_generation is not None
                    else logical
                )
                validation = (
                    _validate_exact_ai_jsonl(
                        logical,
                        trade_date=trade_date,
                        expected_schema=expected_schema,
                        timestamp_field=timestamp_field,
                        generation=pinned_generation,
                    )
                    if artifact_kind == "jsonl"
                    else _validate_exact_ai_json(
                        logical,
                        trade_date=trade_date,
                        expected_schema=expected_schema,
                        generation=pinned_generation,
                    )
                )
                physical_receipts = list(validation.pop("physical_representations", []))
                if not physical_receipts:
                    physical_receipts = _exact_ai_physical_receipts(owned_logical)
                if trade_date == datetime.now(KST).date() and any(
                    row.get("compression") == "gzip" for row in physical_receipts
                ):
                    raise ValueError(
                        f"runtime_date_exact_ai_gzip_generation_forbidden:{logical}"
                    )
                physical_bytes = sum(
                    int(row["stored_bytes"]) for row in physical_receipts
                )
                receipts.append(
                    {
                        "logical_path": str(logical),
                        "trade_date": trade_date.isoformat(),
                        "artifact_kind": artifact_kind,
                        "generation_state": (
                            "protected_current_or_as_of"
                            if is_protected
                            else "closed_verified"
                        ),
                        "physical_representations": physical_receipts,
                        **validation,
                    }
                )
                census["artifact_count"] = int(census["artifact_count"]) + 1
                census["artifact_bytes"] = int(census["artifact_bytes"]) + (
                    physical_bytes
                )
                kind_field = f"{artifact_kind}_artifact_count"
                census[kind_field] = int(census[kind_field]) + 1
                if is_protected:
                    census["protected_artifact_count"] = (
                        int(census["protected_artifact_count"]) + 1
                    )
                age_days = (as_of_date - trade_date).days
                if age_days > retention_days:
                    census["retention_candidate_count"] = (
                        int(census["retention_candidate_count"]) + 1
                    )
                    census["retention_candidate_bytes"] = (
                        int(census["retention_candidate_bytes"]) + physical_bytes
                    )
                plain_metadata = (
                    pinned_generation.stat_name(logical.name)
                    if pinned_generation is not None
                    else (logical.lstat() if logical.exists() else None)
                )
                if is_protected or age_days <= 0 or plain_metadata is None:
                    continue
                if not apply:
                    actions.append(
                        StorageMaintenanceAction(
                            action=f"compress_exact_ai_{artifact_kind}",
                            path=str(logical),
                            trade_date=trade_date.isoformat(),
                            source_bytes=plain_metadata.st_size,
                            applied=False,
                        )
                    )
                    continue
                group_actions, failure = _compress_group_verified(
                    [owned_logical],
                    manifest_path=None,
                    trade_date=trade_date,
                    as_of_date=as_of_date,
                    expected_source_sha256s={
                        owned_logical: str(validation["decoded_content_sha256"])
                    },
                )
                remapped_actions = _remap_actions(
                    group_actions,
                    names={
                        "compress_jsonl": f"compress_exact_ai_{artifact_kind}",
                        "finalize_verified_compression": (
                            f"finalize_verified_exact_ai_{artifact_kind}_compression"
                        ),
                        "publish_verified_gzip_source_preserved": (
                            f"publish_verified_exact_ai_{artifact_kind}_gzip_source_preserved"
                        ),
                    },
                )
                actions.extend(
                    StorageMaintenanceAction(
                        action=row.action,
                        path=str(logical),
                        trade_date=row.trade_date,
                        source_bytes=row.source_bytes,
                        applied=row.applied,
                    )
                    for row in remapped_actions
                )
                if failure is not None:
                    failure["path"] = str(logical)
                    failures.append(failure)
        except Exception as exc:
            failures.append(
                _failure_row(
                    trade_date=trade_date,
                    path=logical,
                    exc=exc,
                    candidate_count=1,
                    candidate_bytes=physical_bytes,
                    recovery_required=(
                        logical.exists()
                        and logical.with_suffix(f"{logical.suffix}.gz").exists()
                    ),
                )
            )

    census["action_count"] = len(actions)
    census["compressed_count"] = sum(
        action.applied
        and action.action
        in {
            "compress_exact_ai_jsonl",
            "finalize_verified_exact_ai_jsonl_compression",
            "compress_exact_ai_json",
            "finalize_verified_exact_ai_json_compression",
        }
        for action in actions
    )
    census["failure_count"] = len(failures)
    census["status"] = "partial_failure" if failures else "pass"
    return actions, failures, census, normalized_roots


def _micro_reversion_daily_owner_census(
    root: Path | None,
    *,
    as_of_date: date,
    protected_dates: set[date],
    retention_days: int,
) -> tuple[dict[str, object], list[dict[str, str]], list[Path]]:
    census: dict[str, object] = {
        "schema": MICRO_REVERSION_DAILY_OWNER_CENSUS_SCHEMA,
        "root": str(Path(root).absolute()) if root is not None else None,
        "status": "not_configured",
        "failure_count": 0,
        "partition_count": 0,
        "file_count": 0,
        "physical_bytes": 0,
        "exact_date_partition_count": 0,
        "exact_date_file_count": 0,
        "exact_date_bytes": 0,
        "protected_partition_count": 0,
        "retention_candidate_count": 0,
        "retention_candidate_bytes": 0,
        "retention_days": retention_days,
        "partition_receipts": [],
        "automatic_compression_authorized": False,
        "automatic_deletion_authorized": False,
        "archive_offload_authorized": False,
        "durable_archive_offload_owner_status": (
            "open_owner_required_no_automatic_archive_offload_or_deletion"
        ),
    }
    if root is None:
        return census, [], []
    lexical_root = Path(root).absolute()
    try:
        root_state = lexical_root.lstat()
    except FileNotFoundError:
        census["status"] = "not_present"
        return census, [], []
    except OSError as exc:
        failure = _failure_row(
            trade_date="unknown",
            path=lexical_root,
            exc=exc,
            candidate_count=0,
            candidate_bytes=0,
            recovery_required=False,
        )
        census["status"] = "partial_failure"
        census["failure_count"] = 1
        return census, [failure], []
    if not stat.S_ISDIR(root_state.st_mode) or lexical_root.is_symlink():
        failure = _failure_row(
            trade_date="unknown",
            path=lexical_root,
            exc=ValueError("micro-reversion daily owner root must be a real directory"),
            candidate_count=0,
            candidate_bytes=0,
            recovery_required=False,
        )
        census["status"] = "partial_failure"
        census["failure_count"] = 1
        return census, [failure], []
    resolved_root = lexical_root.resolve()
    failures: list[dict[str, str]] = []
    receipts = census["partition_receipts"]
    assert isinstance(receipts, list)
    for child in sorted(resolved_root.iterdir()):
        try:
            trade_date = date.fromisoformat(child.name)
            if trade_date > as_of_date and trade_date not in protected_dates:
                raise ValueError("daily owner future partition date invalid")
            if child.is_symlink() or not child.is_dir():
                raise ValueError("daily owner partition must be a real date directory")
            partition = _validated_descendant(resolved_root, child)
            entries = sorted(partition.rglob("*"))
            files: list[dict[str, object]] = []
            for entry in entries:
                if entry.is_symlink():
                    raise OSError(f"daily owner symlink forbidden:{entry}")
                if entry.is_dir():
                    continue
                snapshot = _capture_stable_file(entry)
                files.append(
                    {
                        "relative_path": str(entry.relative_to(partition)),
                        "stored_bytes": snapshot[2],
                        "stored_sha256": snapshot[4],
                    }
                )
            partition_bytes = sum(int(row["stored_bytes"]) for row in files)
            receipt = {
                "trade_date": trade_date.isoformat(),
                "file_count": len(files),
                "physical_bytes": partition_bytes,
                "file_census_sha256": _canonical_sha256(files),
                "generation_state": (
                    "protected_current_or_as_of"
                    if trade_date in protected_dates
                    else "closed_census_only"
                ),
            }
            receipts.append(receipt)
            census["partition_count"] = int(census["partition_count"]) + 1
            census["file_count"] = int(census["file_count"]) + len(files)
            census["physical_bytes"] = int(census["physical_bytes"]) + (partition_bytes)
            if trade_date == as_of_date:
                census["exact_date_partition_count"] = 1
                census["exact_date_file_count"] = len(files)
                census["exact_date_bytes"] = partition_bytes
            if trade_date in protected_dates:
                census["protected_partition_count"] = (
                    int(census["protected_partition_count"]) + 1
                )
            if (as_of_date - trade_date).days > retention_days:
                census["retention_candidate_count"] = (
                    int(census["retention_candidate_count"]) + 1
                )
                census["retention_candidate_bytes"] = (
                    int(census["retention_candidate_bytes"]) + partition_bytes
                )
        except Exception as exc:
            failures.append(
                _failure_row(
                    trade_date=child.name,
                    path=child,
                    exc=exc,
                    candidate_count=1,
                    candidate_bytes=0,
                    recovery_required=False,
                )
            )
    census["failure_count"] = len(failures)
    census["status"] = "partial_failure" if failures else "pass"
    return census, failures, [resolved_root]


def maintain_report_artifact_storage(
    roots: Sequence[Path],
    *,
    as_of_date: date,
    retention_days: int = REPORT_ARTIFACT_DEFAULT_RETENTION_DAYS,
    apply: bool = False,
    exact_ai_artifact_roots: Sequence[Path] = (),
    micro_reversion_daily_owner_root: Path | None = None,
    low_disk_watermark_bytes: int = STORAGE_LOW_DISK_WATERMARK_BYTES,
    critical_disk_watermark_bytes: int = STORAGE_CRITICAL_DISK_WATERMARK_BYTES,
) -> dict[str, object]:
    """Compress closed-date P2 artifacts and census old audit evidence.

    Compression is automatic only for the explicit basename allowlist above.
    Terminal/superseded checkpoint records and bound daily provider ledgers use
    separate exact-chain gates. Full audit artifacts are retained after
    compression: ``retention_days`` classifies archive candidates but grants no
    deletion authority.
    """

    if not isinstance(apply, bool):
        raise TypeError("report artifact maintenance authority must be native boolean")
    if (
        isinstance(retention_days, bool)
        or not isinstance(retention_days, int)
        or retention_days < 1
    ):
        raise ValueError("report artifact retention days must be a positive integer")
    _validate_capacity_watermarks(
        low_disk_watermark_bytes=low_disk_watermark_bytes,
        critical_disk_watermark_bytes=critical_disk_watermark_bytes,
    )
    capacity_roots = [
        *[Path(root).absolute() for root in roots],
        *[Path(root).absolute() for root in exact_ai_artifact_roots],
        *(
            [Path(micro_reversion_daily_owner_root).absolute()]
            if micro_reversion_daily_owner_root is not None
            else []
        ),
    ]
    capacity_anchor = capacity_roots[0] if capacity_roots else Path.cwd()
    disk_before = _disk_capacity_snapshot(capacity_anchor)
    retained_physical_bytes_before = _regular_file_bytes(capacity_roots)
    runtime_trade_date = datetime.now(KST).date()
    if apply and as_of_date > runtime_trade_date:
        raise ValueError("report artifact as-of date must not be in the future")
    protected_dates = {as_of_date, runtime_trade_date}
    actions: list[StorageMaintenanceAction] = []
    failures: list[dict[str, str]] = []
    retention_candidates: dict[Path, int] = {}
    normalized_roots: list[Path] = []
    valid_maintenance_roots: list[Path] = []
    artifact_candidates_by_set: dict[tuple[str, str, date], dict[Path, Path]] = {}

    for raw_root in roots:
        lexical_root = Path(raw_root).absolute()
        try:
            lexical_state = lexical_root.lstat()
        except FileNotFoundError:
            continue
        except OSError as exc:
            failures.append(
                _failure_row(
                    trade_date="unknown",
                    path=lexical_root,
                    exc=exc,
                    candidate_count=0,
                    candidate_bytes=0,
                    recovery_required=False,
                )
            )
            continue
        if not stat.S_ISDIR(lexical_state.st_mode):
            failures.append(
                _failure_row(
                    trade_date="unknown",
                    path=lexical_root,
                    exc=ValueError("report artifact root must be a real directory"),
                    candidate_count=0,
                    candidate_bytes=0,
                    recovery_required=False,
                )
            )
            continue
        root = lexical_root.resolve()
        try:
            lexical_state_after = lexical_root.lstat()
        except OSError as exc:
            failures.append(
                _failure_row(
                    trade_date="unknown",
                    path=lexical_root,
                    exc=exc,
                    candidate_count=0,
                    candidate_bytes=0,
                    recovery_required=False,
                )
            )
            continue
        if (
            not stat.S_ISDIR(lexical_state_after.st_mode)
            or lexical_state_after.st_dev != lexical_state.st_dev
            or lexical_state_after.st_ino != lexical_state.st_ino
        ):
            failures.append(
                _failure_row(
                    trade_date="unknown",
                    path=lexical_root,
                    exc=OSError("report artifact root changed during validation"),
                    candidate_count=0,
                    candidate_bytes=0,
                    recovery_required=False,
                )
            )
            continue
        if root in normalized_roots:
            continue
        normalized_roots.append(root)
        if not root.is_dir():
            failures.append(
                _failure_row(
                    trade_date="unknown",
                    path=root,
                    exc=ValueError("report artifact root must be a real directory"),
                    candidate_count=0,
                    candidate_bytes=0,
                    recovery_required=False,
                )
            )
            continue
        custody_failures = _report_root_custody_failures(root)
        if custody_failures:
            failures.extend(custody_failures)
            continue
        valid_maintenance_roots.append(root)
        logical_candidates: dict[Path, date] = {}
        try:
            descendants = sorted(root.rglob("*"))
        except OSError as exc:
            failures.append(
                _failure_row(
                    trade_date="unknown",
                    path=root,
                    exc=exc,
                    candidate_count=0,
                    candidate_bytes=0,
                    recovery_required=False,
                )
            )
            continue
        for child in descendants:
            is_active_top_level = child.parent == root
            relative_parts = child.relative_to(root).parts[:-1]
            is_explicit_superseded = "superseded" in relative_parts
            if not is_active_top_level and not is_explicit_superseded:
                continue
            trade_date = _report_artifact_trade_date(child.name)
            if trade_date is None:
                continue
            logical = child.with_suffix("") if child.suffix == ".gz" else child
            try:
                logical = _validated_descendant(root, logical)
                logical_candidates[logical] = trade_date
            except Exception as exc:
                failures.append(
                    _failure_row(
                        trade_date=trade_date,
                        path=logical,
                        exc=exc,
                        candidate_count=1,
                        candidate_bytes=0,
                        recovery_required=False,
                    )
                )
        for logical, trade_date in sorted(
            logical_candidates.items(), key=lambda item: str(item[0])
        ):
            is_explicit_superseded = (
                "superseded" in logical.relative_to(root).parts[:-1]
            )
            set_key = (
                (
                    "superseded",
                    str(logical.parent),
                    trade_date,
                )
                if is_explicit_superseded
                else ("active", "", trade_date)
            )
            artifact_candidates_by_set.setdefault(set_key, {})[logical] = root

    artifact_set_census = {
        "set_count": 0,
        "set_bytes": 0,
        "terminal_count": 0,
        "explicitly_superseded_count": 0,
        "incomplete_resumable_count": 0,
        "retention_candidate_count": 0,
        "retention_candidate_bytes": 0,
        "stale_workorder_count": 0,
        "stale_workorder_bytes": 0,
        "immutable_source_artifact_count": 0,
        "immutable_source_artifact_bytes": 0,
    }
    for (set_lane, _, trade_date), candidate_roots in sorted(
        artifact_candidates_by_set.items()
    ):
        candidates = sorted(candidate_roots)
        physical_bytes = 0
        try:
            with ExitStack() as generation_locks:
                if apply:
                    for logical in candidates:
                        generation_locks.enter_context(
                            json_artifact_generation_lock(
                                logical,
                                exclusive=True,
                                blocking=False,
                            )
                        )
                physical_bytes = sum(
                    path.stat().st_size
                    for logical in candidates
                    for path in (logical, logical.with_suffix(f"{logical.suffix}.gz"))
                    if path.exists() and path.is_file() and not path.is_symlink()
                )
                state, validated_source_sha256s = _classify_report_artifact_set(
                    candidates,
                    trade_date=trade_date,
                    explicitly_superseded=set_lane == "superseded",
                )
                immutable_source_candidates = (
                    [
                        path
                        for path in candidates
                        if any(
                            pattern.fullmatch(path.name) is not None
                            for pattern, _, _ in IMMUTABLE_SOURCE_ARTIFACT_CONTRACTS
                        )
                    ]
                    if set_lane == "active"
                    else []
                )
                validated_source_payloads: dict[Path, dict[str, object]] = {}
                for path in immutable_source_candidates:
                    payload, raw_sha256 = _validate_immutable_source_artifact(
                        path,
                        trade_date=trade_date,
                    )
                    validated_source_payloads[path] = payload
                    previous_sha256 = validated_source_sha256s.get(path)
                    if previous_sha256 is not None and previous_sha256 != raw_sha256:
                        raise OSError("report_artifact_changed_during_set_validation")
                    validated_source_sha256s[path] = raw_sha256
                _validate_current_r2_r3_pair(
                    validated_source_payloads,
                    trade_date=trade_date,
                )
                artifact_set_census["set_count"] += 1
                artifact_set_census["set_bytes"] += physical_bytes
                artifact_set_census[f"{state}_count"] += 1
                artifact_set_census["immutable_source_artifact_count"] += len(
                    immutable_source_candidates
                )
                artifact_set_census["immutable_source_artifact_bytes"] += sum(
                    path.stat().st_size
                    for logical in immutable_source_candidates
                    for path in (logical, logical.with_suffix(f"{logical.suffix}.gz"))
                    if path.exists() and path.is_file() and not path.is_symlink()
                )
                age_days = (as_of_date - trade_date).days
                if age_days > retention_days:
                    artifact_set_census["retention_candidate_count"] += 1
                    artifact_set_census["retention_candidate_bytes"] += physical_bytes
                    if state == "incomplete_resumable":
                        artifact_set_census["stale_workorder_count"] += 1
                        artifact_set_census["stale_workorder_bytes"] += physical_bytes
                for logical in candidates:
                    compressed = logical.with_suffix(f"{logical.suffix}.gz")
                    existing = [path for path in (logical, compressed) if path.exists()]
                    candidate_bytes = sum(
                        path.stat().st_size
                        for path in existing
                        if path.is_file() and not path.is_symlink()
                    )
                    if age_days > retention_days:
                        retention_candidates[logical] = candidate_bytes
                if trade_date in protected_dates or age_days <= 0:
                    continue
                compression_candidates = (
                    immutable_source_candidates
                    if state == "incomplete_resumable"
                    else candidates
                )
                for logical in compression_candidates:
                    if not logical.exists():
                        continue
                    root = candidate_roots[logical]
                    compressed = logical.with_suffix(f"{logical.suffix}.gz")
                    validated = _validated_descendant(root, logical)
                    if validated.is_symlink() or not validated.is_file():
                        raise OSError("report artifact source must be a regular file")
                    if compressed.is_symlink():
                        raise OSError("report artifact gzip target cannot be a symlink")
                    if compressed.exists() and not compressed.is_file():
                        raise OSError(
                            "report artifact gzip target must be a regular file"
                        )
                    if apply:
                        group_actions, failure = _compress_group_verified(
                            [validated],
                            manifest_path=None,
                            trade_date=trade_date,
                            as_of_date=as_of_date,
                            expected_source_sha256s=validated_source_sha256s,
                        )
                        actions.extend(group_actions)
                        if failure is not None:
                            failures.append(failure)
                    else:
                        actions.append(
                            StorageMaintenanceAction(
                                action="compress_json_artifact",
                                path=str(validated),
                                trade_date=trade_date.isoformat(),
                                source_bytes=validated.stat().st_size,
                                applied=False,
                            )
                        )
        except Exception as exc:
            failures.append(
                _failure_row(
                    trade_date=trade_date,
                    path=candidates[0],
                    exc=exc,
                    candidate_count=len(candidates),
                    candidate_bytes=physical_bytes,
                    recovery_required=any(
                        logical.exists()
                        and logical.with_suffix(f"{logical.suffix}.gz").exists()
                        for logical in candidates
                    ),
                )
            )

    checkpoint_census = {
        "journal_count": 0,
        "journal_bytes": 0,
        "terminal_count": 0,
        "superseded_count": 0,
        "incomplete_resumable_count": 0,
        "retention_candidate_count": 0,
        "retention_candidate_bytes": 0,
        "stale_workorder_count": 0,
        "stale_workorder_bytes": 0,
    }
    provider_budget_census = {
        "ledger_count": 0,
        "ledger_bytes": 0,
        "retention_candidate_count": 0,
        "retention_candidate_bytes": 0,
    }
    for root in valid_maintenance_roots:
        checkpoint_actions, checkpoint_failures, root_checkpoint_census = (
            _maintain_checkpoint_journal_storage(
                root,
                as_of_date=as_of_date,
                protected_dates=protected_dates,
                retention_days=retention_days,
                apply=apply,
            )
        )
        actions.extend(checkpoint_actions)
        failures.extend(checkpoint_failures)
        for field, value in root_checkpoint_census.items():
            checkpoint_census[field] += value
        provider_actions, provider_failures, root_provider_census = (
            _maintain_provider_budget_ledger_storage(
                root,
                as_of_date=as_of_date,
                protected_dates=protected_dates,
                retention_days=retention_days,
                apply=apply,
            )
        )
        actions.extend(provider_actions)
        failures.extend(provider_failures)
        for field, value in root_provider_census.items():
            provider_budget_census[field] += value

    (
        exact_ai_actions,
        exact_ai_failures,
        exact_ai_census,
        exact_ai_roots,
    ) = _maintain_exact_ai_artifact_storage(
        exact_ai_artifact_roots,
        as_of_date=as_of_date,
        protected_dates=protected_dates,
        retention_days=retention_days,
        apply=apply,
    )
    actions.extend(exact_ai_actions)
    failures.extend(exact_ai_failures)
    (
        daily_owner_census,
        daily_owner_failures,
        daily_owner_roots,
    ) = _micro_reversion_daily_owner_census(
        micro_reversion_daily_owner_root,
        as_of_date=as_of_date,
        protected_dates=protected_dates,
        retention_days=retention_days,
    )
    failures.extend(daily_owner_failures)

    normalized_actions = []
    action_names = {
        "compress_jsonl": "compress_json_artifact",
        "finalize_verified_compression": (
            "finalize_verified_json_artifact_compression"
        ),
        "publish_verified_gzip_source_preserved": (
            "publish_verified_json_artifact_gzip_source_preserved"
        ),
    }
    for action in actions:
        row = asdict(action)
        row["action"] = action_names.get(action.action, action.action)
        normalized_actions.append(row)
    disk_after = _disk_capacity_snapshot(capacity_anchor)
    all_normalized_roots = [
        *normalized_roots,
        *[root for root in exact_ai_roots if root not in normalized_roots],
        *[
            root
            for root in daily_owner_roots
            if root not in normalized_roots and root not in exact_ai_roots
        ],
    ]
    retained_physical_bytes_after = _regular_file_bytes(all_normalized_roots)
    capacity_metrics = _capacity_metrics(
        disk_before=disk_before,
        disk_after=disk_after,
        retained_physical_bytes_before=retained_physical_bytes_before,
        retained_physical_bytes_after=retained_physical_bytes_after,
        compressed_target_bytes=_compressed_target_bytes(actions),
        low_disk_watermark_bytes=low_disk_watermark_bytes,
        critical_disk_watermark_bytes=critical_disk_watermark_bytes,
    )
    return {
        "schema": REPORT_ARTIFACT_MAINTENANCE_SCHEMA,
        "as_of_date": as_of_date.isoformat(),
        "runtime_trade_date": runtime_trade_date.isoformat(),
        "protected_trade_dates": sorted(day.isoformat() for day in protected_dates),
        "roots": [str(root) for root in all_normalized_roots],
        "mode": "apply" if apply else "dry_run",
        "status": (
            "partial_failure"
            if failures or capacity_metrics["capacity_failure"] is True
            else "pass"
        ),
        "failure_count": len(failures),
        "failures": failures,
        "action_count": len(normalized_actions),
        "source_bytes": sum(action.source_bytes for action in actions),
        "compressed_count": sum(
            row["action"]
            in {
                "compress_json_artifact",
                "finalize_verified_json_artifact_compression",
                "compress_checkpoint_record_json",
                "finalize_verified_checkpoint_record_compression",
                "compress_provider_budget_jsonl",
                "finalize_verified_provider_budget_compression",
                "compress_exact_ai_jsonl",
                "finalize_verified_exact_ai_jsonl_compression",
                "compress_exact_ai_json",
                "finalize_verified_exact_ai_json_compression",
            }
            and row["applied"] is True
            for row in normalized_actions
        ),
        "actions": normalized_actions,
        "retention_days": retention_days,
        "retention_candidate_count": len(retention_candidates),
        "retention_candidate_bytes": sum(retention_candidates.values()),
        "artifact_set_census": artifact_set_census,
        "checkpoint_journal_census": checkpoint_census,
        "provider_budget_ledger_census": provider_budget_census,
        "exact_ai_artifact_maintenance": exact_ai_census,
        "micro_reversion_daily_owner_census": daily_owner_census,
        "retention_policy": (
            "compressed_full_audit_retained_deletion_requires_separate_authority"
        ),
        "deletion_performed": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "trading_runtime_effect": False,
        "provider_runtime_effect": False,
        "provider_route_change_allowed": False,
        "metric_role": "source_quality_and_report_artifact_storage_retention",
        "decision_authority": MAINTENANCE_AUTHORITY,
        "window_policy": (
            "closed_exact_date_immutable_sources_and_terminal_or_superseded_ledgers"
        ),
        "sample_floor": "not_applicable_storage_operation",
        "primary_decision_metric": "retained_uncompressed_bytes",
        "source_quality_gate": (
            "source_only_schema_content_hash_and_verified_gzip_or_bound_ledger_chain"
        ),
        "forbidden_uses": [
            "current_trade_date_mutation",
            "incomplete_checkpoint_record_compression",
            "automatic_audit_artifact_deletion",
            "automatic_exact_ai_artifact_deletion",
            "automatic_micro_reversion_daily_owner_compression_or_deletion",
            "daily_owner_archive_or_offload_without_durable_owner_authority",
            "broker_order_submission",
            "provider_route_or_network_call",
            "strategy_threshold_or_bot_change",
        ],
        **capacity_metrics,
    }


def purge_excluded_forward_scopes(
    root: Path,
    *,
    source_exclusion_manifest_path: Path,
    apply: bool = False,
    runtime_trade_date: date | None = None,
) -> dict[str, object]:
    """Physically remove only exact scopes already barred from P2 consumption.

    This is storage cleanup, not a new source-quality decision. The existing
    exclusion manifest remains the authority and whole-date deletion is never
    inferred from a failed process epoch.
    """

    from .p2_replay import load_source_exclusion_manifest

    if not isinstance(apply, bool):
        raise TypeError("source exclusion purge authority must be a native boolean")
    root_path = Path(root).resolve()
    manifest_path = Path(source_exclusion_manifest_path).resolve()
    manifest = load_source_exclusion_manifest(manifest_path)
    today = runtime_trade_date or datetime.now(KST).date()
    grouped: dict[tuple[str, str, str], list[dict[str, object]]] = {}
    for raw_entry in manifest["exclusions"]:
        entry = dict(raw_entry)
        key = (
            str(entry["trade_date"]),
            str(entry["venue"]),
            str(entry["session_bucket"]),
        )
        grouped.setdefault(key, []).append(entry)

    actions: list[SourceExclusionPurgeAction] = []
    failures: list[dict[str, str]] = []
    if apply:
        for (trade_date_text, venue, session_bucket), entries in sorted(
            grouped.items()
        ):
            leaf = (
                root_path
                / f"trade_date={trade_date_text}"
                / f"venue={venue}"
                / f"session={session_bucket}"
            )
            try:
                trade_date = date.fromisoformat(trade_date_text)
                if trade_date >= today:
                    raise ValueError("current_or_future_trade_date_purge_forbidden")
                leaf = _validated_descendant(root_path, leaf)
                if not leaf.is_dir() or leaf.is_symlink():
                    raise ValueError("source exclusion leaf must be a real directory")
                _assert_tree_stable_and_closed(
                    leaf,
                    phase="source_exclusion_global_preflight",
                )
                _purge_one_excluded_leaf(leaf, entries=entries, apply=False)
            except Exception as exc:
                failures.append(
                    {
                        "trade_date": trade_date_text,
                        "venue": venue,
                        "session_bucket": session_bucket,
                        "path": str(leaf),
                        "error_type": type(exc).__name__,
                        "reason": str(exc),
                    }
                )
        if failures:
            return _source_exclusion_purge_result(
                root_path=root_path,
                manifest_path=manifest_path,
                manifest=manifest,
                today=today,
                apply=apply,
                actions=actions,
                failures=failures,
            )
    for (trade_date_text, venue, session_bucket), entries in sorted(grouped.items()):
        leaf = (
            root_path
            / f"trade_date={trade_date_text}"
            / f"venue={venue}"
            / f"session={session_bucket}"
        )
        try:
            trade_date = date.fromisoformat(trade_date_text)
            if trade_date >= today:
                raise ValueError("current_or_future_trade_date_purge_forbidden")
            leaf = _validated_descendant(root_path, leaf)
            if not leaf.is_dir() or leaf.is_symlink():
                raise ValueError("source exclusion leaf must be a real directory")
            if apply:
                trade_dir = _validated_descendant(
                    root_path, root_path / f"trade_date={trade_date_text}"
                )
                with partition_maintenance_lock(
                    trade_dir,
                    blocking=False,
                    exclusive=True,
                ):
                    action = _purge_one_excluded_leaf(
                        leaf,
                        entries=entries,
                        apply=True,
                    )
            else:
                action = _purge_one_excluded_leaf(
                    leaf,
                    entries=entries,
                    apply=False,
                )
            actions.append(action)
        except Exception as exc:
            failures.append(
                {
                    "trade_date": trade_date_text,
                    "venue": venue,
                    "session_bucket": session_bucket,
                    "path": str(leaf),
                    "error_type": type(exc).__name__,
                    "reason": str(exc),
                }
            )

    return _source_exclusion_purge_result(
        root_path=root_path,
        manifest_path=manifest_path,
        manifest=manifest,
        today=today,
        apply=apply,
        actions=actions,
        failures=failures,
    )


def _source_exclusion_purge_result(
    *,
    root_path: Path,
    manifest_path: Path,
    manifest: dict[str, object],
    today: date,
    apply: bool,
    actions: list[SourceExclusionPurgeAction],
    failures: list[dict[str, str]],
) -> dict[str, object]:
    return {
        "schema": SOURCE_EXCLUSION_PURGE_SCHEMA,
        "generated_at": datetime.now(KST).isoformat(timespec="milliseconds"),
        "root": str(root_path),
        "source_exclusion_manifest": str(manifest_path),
        "source_exclusion_manifest_schema": manifest["schema"],
        "scope_policy": manifest["scope_policy"],
        "runtime_trade_date": today.isoformat(),
        "mode": "apply" if apply else "dry_run",
        "status": "partial_failure" if failures else "pass",
        "failure_count": len(failures),
        "failures": failures,
        "action_count": len(actions),
        "stream_rows_removed": sum(row.stream_rows_removed for row in actions),
        "event_reference_rows_removed": sum(
            row.event_reference_rows_removed for row in actions
        ),
        "source_bytes_before": sum(row.source_bytes_before for row in actions),
        "source_bytes_after": sum(row.source_bytes_after for row in actions),
        "reclaimed_bytes": sum(
            max(0, row.source_bytes_before - row.source_bytes_after) for row in actions
        ),
        "deletion_performed": any(row.applied for row in actions),
        "actions": [asdict(row) for row in actions],
        "metric_role": "source_quality_excluded_raw_storage_cleanup",
        "decision_authority": MAINTENANCE_AUTHORITY,
        "window_policy": "exact_closed_trade_date_venue_session_sequence_epoch",
        "sample_floor": "not_applicable_exact_manifest_scope_cleanup",
        "primary_decision_metric": "stream_rows_removed",
        "source_quality_gate": (
            "validated_existing_exclusion_manifest_and_exact_expected_row_counts"
        ),
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "trading_runtime_effect": False,
        "forbidden_uses": [
            "whole_trade_date_deletion_when_exact_scope_is_available",
            "current_trade_date_mutation",
            "new_source_quality_exclusion_decision",
            "broker_order_submission_or_cancel",
            "threshold_provider_bot_quantity_or_cap_mutation",
        ],
    }


def _purge_one_excluded_leaf(
    leaf: Path,
    *,
    entries: list[dict[str, object]],
    apply: bool,
) -> SourceExclusionPurgeAction:
    epochs = {int(entry["sequence_epoch"]) for entry in entries}
    if len(epochs) != len(entries):
        raise ValueError("duplicate source exclusion sequence epoch")
    expected_stream = sum(int(entry["market_stream_row_count"]) for entry in entries)
    expected_references = sum(int(entry["event_reference_count"]) for entry in entries)
    stream_manifest = leaf / "market_stream.manifest.json"
    stream_files = _manifest_available_sources(stream_manifest)
    reference_files = _available_reference_sources(leaf)
    files = [*stream_files, *reference_files]
    if not files:
        raise FileNotFoundError("source exclusion purge inputs are unavailable")
    source_bytes_before = sum(path.stat().st_size for path in files)
    removed_stream = _count_matching_epoch_rows(stream_files, epochs)
    removed_references = _count_matching_epoch_rows(reference_files, epochs)
    if removed_stream != expected_stream:
        raise ValueError(
            f"excluded stream row count mismatch:{removed_stream}!={expected_stream}"
        )
    if removed_references != expected_references:
        raise ValueError(
            "excluded event reference row count mismatch:"
            f"{removed_references}!={expected_references}"
        )
    if not apply:
        return SourceExclusionPurgeAction(
            trade_date=str(entries[0]["trade_date"]),
            venue=str(entries[0]["venue"]),
            session_bucket=str(entries[0]["session_bucket"]),
            sequence_epochs=tuple(sorted(epochs)),
            stream_rows_removed=removed_stream,
            event_reference_rows_removed=removed_references,
            source_bytes_before=source_bytes_before,
            source_bytes_after=source_bytes_before,
            applied=False,
        )

    _assert_tree_stable_and_closed(leaf, phase="before_source_exclusion_purge")
    snapshots = {path: _capture_stable_file(path) for path in files}
    replacements: dict[Path, Path] = {}
    backups: dict[Path, Path] = {}
    manifest_before = stream_manifest.read_bytes()
    publish_succeeded = False
    try:
        for source in files:
            replacements[source] = _prepare_filtered_epoch_source(source, epochs)
        for source, snapshot in snapshots.items():
            _assert_source_unchanged_and_closed(
                source,
                snapshot,
                phase="before_source_exclusion_publish",
            )
        for source in files:
            backup = source.with_name(f".{source.name}.source-exclusion-backup")
            if backup.exists() or backup.is_symlink():
                raise FileExistsError(f"source exclusion backup exists:{backup}")
            os.link(source, backup)
            backups[source] = backup
        _fsync_directory(leaf)
        for source in files:
            os.replace(replacements[source], source)
            _fsync_directory(leaf)
        _refresh_manifest_current_bytes(
            stream_manifest,
            as_of_date=datetime.now(KST).date(),
        )
        if _count_matching_epoch_rows(stream_files, epochs) != 0:
            raise OSError("excluded stream rows remain after purge")
        if _count_matching_epoch_rows(reference_files, epochs) != 0:
            raise OSError("excluded reference rows remain after purge")
        publish_succeeded = True
    except Exception as publish_error:
        rollback_errors: list[str] = []
        for source, backup in backups.items():
            if backup.exists():
                try:
                    os.replace(backup, source)
                except Exception as exc:
                    rollback_errors.append(
                        f"source={source}:error={type(exc).__name__}:{exc}"
                    )
        if stream_manifest.exists() and stream_manifest.read_bytes() != manifest_before:
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=f".{stream_manifest.name}.",
                suffix=".rollback",
                dir=stream_manifest.parent,
            )
            try:
                with os.fdopen(descriptor, "wb") as handle:
                    handle.write(manifest_before)
                    handle.flush()
                    os.fsync(handle.fileno())
                try:
                    os.replace(temporary_name, stream_manifest)
                except Exception as exc:
                    rollback_errors.append(
                        f"manifest={stream_manifest}:error={type(exc).__name__}:{exc}"
                    )
            finally:
                Path(temporary_name).unlink(missing_ok=True)
        _fsync_directory(leaf)
        if rollback_errors:
            raise RuntimeError(
                "source_exclusion_rollback_failed:" + "|".join(rollback_errors)
            ) from publish_error
        raise
    finally:
        for temporary in replacements.values():
            temporary.unlink(missing_ok=True)
        if publish_succeeded:
            for backup in backups.values():
                backup.unlink(missing_ok=True)
            _fsync_directory(leaf)

    source_bytes_after = sum(path.stat().st_size for path in files)
    return SourceExclusionPurgeAction(
        trade_date=str(entries[0]["trade_date"]),
        venue=str(entries[0]["venue"]),
        session_bucket=str(entries[0]["session_bucket"]),
        sequence_epochs=tuple(sorted(epochs)),
        stream_rows_removed=removed_stream,
        event_reference_rows_removed=removed_references,
        source_bytes_before=source_bytes_before,
        source_bytes_after=source_bytes_after,
        applied=True,
    )


def _manifest_available_sources(manifest_path: Path) -> list[Path]:
    sources: list[Path] = []
    for logical in _manifest_logical_sources(manifest_path):
        compressed = logical.with_suffix(f"{logical.suffix}.gz")
        available = logical if logical.exists() else compressed
        if not available.exists():
            raise FileNotFoundError(f"manifest source is unavailable:{logical}")
        sources.append(available)
    return sources


def _refresh_manifest_current_bytes(
    manifest_path: Path,
    *,
    as_of_date: date,
) -> None:
    payload = _validated_manifest_payload(manifest_path)
    for shard in payload["shards"]:
        declared = manifest_path.parent / str(shard["file"])
        logical = declared.with_suffix("") if declared.suffix == ".gz" else declared
        compressed = logical.with_suffix(f"{logical.suffix}.gz")
        available = logical if logical.exists() else compressed
        if not available.exists():
            raise FileNotFoundError(f"manifest shard is unavailable:{logical}")
        shard["file"] = available.name
        shard["bytes"] = available.stat().st_size
        shard["compressed"] = available.suffix == ".gz"
    payload["storage_maintenance_schema"] = MAINTENANCE_SCHEMA
    payload["storage_maintenance_as_of_date"] = as_of_date.isoformat()
    payload["source_exclusion_purge_schema"] = SOURCE_EXCLUSION_PURGE_SCHEMA
    _write_json_atomic(manifest_path, payload)


def _available_reference_sources(leaf: Path) -> list[Path]:
    plain = leaf / "market_stream_event_references.jsonl"
    compressed = plain.with_suffix(f"{plain.suffix}.gz")
    available = [path for path in (plain, compressed) if path.exists()]
    if len(available) != 1:
        raise ValueError("exactly one event reference source is required")
    if available[0].is_symlink() or not available[0].is_file():
        raise OSError("event reference source must be a regular file")
    return available


def _open_jsonl_text(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8")
    return path.open("r", encoding="utf-8")


def _count_matching_epoch_rows(paths: list[Path], epochs: set[int]) -> int:
    count = 0
    for path in paths:
        with _open_jsonl_text(path) as handle:
            for line_number, line in enumerate(handle, start=1):
                try:
                    row = json.loads(line)
                except Exception as exc:
                    raise ValueError(f"invalid JSONL:{path}:{line_number}") from exc
                if not isinstance(row, dict):
                    raise ValueError(
                        f"JSONL row must be an object:{path}:{line_number}"
                    )
                if int(row.get("sequence_epoch") or -1) in epochs:
                    count += 1
    return count


def _prepare_filtered_epoch_source(source: Path, epochs: set[int]) -> Path:
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{source.name}.", suffix=".source-exclusion.tmp", dir=source.parent
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        opener = gzip.open if source.suffix == ".gz" else open
        kept_row_count = 0
        with (
            _open_jsonl_text(source) as input_handle,
            opener(temporary, "wt", encoding="utf-8") as output_handle,
        ):
            for line_number, line in enumerate(input_handle, start=1):
                try:
                    row = json.loads(line)
                except Exception as exc:
                    raise ValueError(f"invalid JSONL:{source}:{line_number}") from exc
                if not isinstance(row, dict):
                    raise ValueError(
                        f"JSONL row must be an object:{source}:{line_number}"
                    )
                if int(row.get("sequence_epoch") or -1) not in epochs:
                    output_handle.write(line)
                    kept_row_count += 1
        verified_row_count = 0
        with opener(temporary, "rt", encoding="utf-8") as verify_handle:
            for line_number, line in enumerate(verify_handle, start=1):
                try:
                    row = json.loads(line)
                except Exception as exc:
                    raise ValueError(
                        f"invalid filtered JSONL:{source}:{line_number}"
                    ) from exc
                if not isinstance(row, dict):
                    raise ValueError(
                        f"filtered JSONL row must be an object:{source}:{line_number}"
                    )
                if int(row.get("sequence_epoch") or -1) in epochs:
                    raise ValueError(
                        f"excluded epoch remains in filtered source:{source}"
                    )
                verified_row_count += 1
        if verified_row_count != kept_row_count:
            raise OSError(
                f"filtered row count mismatch:{verified_row_count}!={kept_row_count}"
            )
        with temporary.open("rb") as handle:
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o640)
        return temporary
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def maintain_forward_storage(
    root: Path,
    *,
    as_of_date: date,
    storage_policy: PathStoragePolicy | None = None,
    apply: bool = False,
    purge_expired: bool = False,
) -> dict[str, object]:
    if not isinstance(apply, bool) or not isinstance(purge_expired, bool):
        raise TypeError("storage maintenance authorities must be native booleans")
    policy = storage_policy or PathStoragePolicy()
    root_path = Path(root).resolve()
    _validate_capacity_watermarks(
        low_disk_watermark_bytes=policy.low_disk_watermark_bytes,
        critical_disk_watermark_bytes=policy.critical_disk_watermark_bytes,
    )
    disk_before = _disk_capacity_snapshot(root_path)
    retained_physical_bytes_before = _regular_file_bytes([root_path])
    runtime_trade_date = datetime.now(KST).date()
    if apply and as_of_date > runtime_trade_date:
        raise ValueError("storage maintenance as-of date must not be in the future")
    protected_trade_dates = {as_of_date, runtime_trade_date}
    actions: list[StorageMaintenanceAction] = []
    partition_failures: list[dict[str, str]] = []
    purge_candidate_count = 0
    purge_candidate_bytes = 0
    if not root_path.exists():
        return _result(
            root_path,
            as_of_date,
            runtime_trade_date,
            apply,
            purge_expired,
            actions,
            partition_failures=partition_failures,
            purge_candidate_count=purge_candidate_count,
            purge_candidate_bytes=purge_candidate_bytes,
            disk_before=disk_before,
            retained_physical_bytes_before=retained_physical_bytes_before,
            storage_policy=policy,
        )
    for candidate in sorted(root_path.glob("trade_date=????-??-??")):
        candidate_trade_date = candidate.name.removeprefix("trade_date=")
        try:
            trade_dir = _validated_descendant(root_path, candidate)
            if not trade_dir.is_dir() or trade_dir.is_symlink():
                raise ValueError("trade-date maintenance target must be a directory")
            trade_date = date.fromisoformat(candidate_trade_date)
        except Exception as exc:
            partition_failures.append(
                {
                    "trade_date": candidate_trade_date,
                    "path": str(candidate),
                    "error_type": type(exc).__name__,
                    "reason": str(exc),
                    "candidate_count": "1",
                    "candidate_bytes": "0",
                    "published_target_count": "0",
                    "unlinked_source_count": "0",
                    "manifest_update_count": "0",
                    "recovery_required": "false",
                }
            )
            continue
        if trade_date in protected_trade_dates:
            continue
        age_days = (as_of_date - trade_date).days
        if age_days <= 0:
            continue
        try:
            if apply:
                with partition_maintenance_lock(
                    trade_dir,
                    blocking=False,
                    exclusive=True,
                ):
                    partition_actions, purge_count, purge_bytes, group_failures = (
                        _maintain_trade_directory(
                            root_path,
                            trade_dir,
                            trade_date=trade_date,
                            age_days=age_days,
                            as_of_date=as_of_date,
                            policy=policy,
                            apply=True,
                            purge_expired=purge_expired,
                        )
                    )
            else:
                partition_actions, purge_count, purge_bytes, group_failures = (
                    _maintain_trade_directory(
                        root_path,
                        trade_dir,
                        trade_date=trade_date,
                        age_days=age_days,
                        as_of_date=as_of_date,
                        policy=policy,
                        apply=False,
                        purge_expired=purge_expired,
                    )
                )
        except Exception as exc:
            try:
                failed_bytes = _tree_bytes(trade_dir)
            except OSError:
                failed_bytes = 0
            partition_failures.append(
                {
                    "trade_date": trade_date.isoformat(),
                    "path": str(trade_dir),
                    "error_type": type(exc).__name__,
                    "reason": str(exc),
                    "candidate_count": "1",
                    "candidate_bytes": str(failed_bytes),
                    "recovery_required": "false",
                }
            )
            continue
        actions.extend(partition_actions)
        partition_failures.extend(group_failures)
        purge_candidate_count += purge_count
        purge_candidate_bytes += purge_bytes
    return _result(
        root_path,
        as_of_date,
        runtime_trade_date,
        apply,
        purge_expired,
        actions,
        partition_failures=partition_failures,
        purge_candidate_count=purge_candidate_count,
        purge_candidate_bytes=purge_candidate_bytes,
        disk_before=disk_before,
        retained_physical_bytes_before=retained_physical_bytes_before,
        storage_policy=policy,
    )


def _maintain_trade_directory(
    root_path: Path,
    trade_dir: Path,
    *,
    trade_date: date,
    age_days: int,
    as_of_date: date,
    policy: PathStoragePolicy,
    apply: bool,
    purge_expired: bool,
) -> tuple[
    list[StorageMaintenanceAction],
    int,
    int,
    list[dict[str, str]],
]:
    partition_actions: list[StorageMaintenanceAction] = []
    partition_failures = _descendant_symlink_failures(
        trade_dir,
        trade_date=trade_date,
    )
    unlink_claim_failures = _descendant_unlink_claim_failures(
        trade_dir,
        trade_date=trade_date,
    )
    partition_failures.extend(unlink_claim_failures)

    purge_candidate_count = 0
    purge_candidate_bytes = 0
    if age_days > policy.retention_days:
        source_bytes = _tree_bytes(trade_dir)
        purge_candidate_count = 1
        purge_candidate_bytes = source_bytes
        if purge_expired:
            if partition_failures:
                return (
                    partition_actions,
                    purge_candidate_count,
                    purge_candidate_bytes,
                    partition_failures,
                )
            if apply:
                try:
                    _assert_tree_stable_and_closed(trade_dir, phase="before_purge")
                    shutil.rmtree(trade_dir)
                except Exception as exc:
                    remaining_bytes = (
                        _tree_bytes(trade_dir) if trade_dir.exists() else 0
                    )
                    deleted_bytes = max(0, source_bytes - remaining_bytes)
                    if deleted_bytes > 0 or not trade_dir.exists():
                        partition_actions.append(
                            StorageMaintenanceAction(
                                action=(
                                    "purge_trade_date_partial"
                                    if trade_dir.exists()
                                    else "purge_trade_date"
                                ),
                                path=str(trade_dir),
                                trade_date=trade_date.isoformat(),
                                source_bytes=deleted_bytes,
                                applied=True,
                            )
                        )
                    partition_failures.append(
                        _failure_row(
                            trade_date=trade_date,
                            path=trade_dir,
                            exc=exc,
                            candidate_count=int(trade_dir.exists()),
                            candidate_bytes=remaining_bytes,
                            recovery_required=(
                                trade_dir.exists() and deleted_bytes > 0
                            ),
                        )
                    )
                    return (
                        partition_actions,
                        purge_candidate_count,
                        purge_candidate_bytes,
                        partition_failures,
                    )
                else:
                    partition_actions.append(
                        StorageMaintenanceAction(
                            action="purge_trade_date",
                            path=str(trade_dir),
                            trade_date=trade_date.isoformat(),
                            source_bytes=source_bytes,
                            applied=True,
                        )
                    )
                    return (
                        partition_actions,
                        purge_candidate_count,
                        purge_candidate_bytes,
                        partition_failures,
                    )
            else:
                partition_actions.append(
                    StorageMaintenanceAction(
                        action="purge_trade_date",
                        path=str(trade_dir),
                        trade_date=trade_date.isoformat(),
                        source_bytes=source_bytes,
                        applied=False,
                    )
                )
                return (
                    partition_actions,
                    purge_candidate_count,
                    purge_candidate_bytes,
                    partition_failures,
                )
    if age_days < policy.compression_after_days:
        return (
            partition_actions,
            purge_candidate_count,
            purge_candidate_bytes,
            partition_failures,
        )
    if unlink_claim_failures:
        return (
            partition_actions,
            purge_candidate_count,
            purge_candidate_bytes,
            partition_failures,
        )

    compression_actions, compression_failures = _maintain_compression_groups(
        root_path,
        trade_dir,
        trade_date=trade_date,
        as_of_date=as_of_date,
        apply=apply,
    )
    partition_actions.extend(compression_actions)
    partition_failures.extend(compression_failures)
    return (
        partition_actions,
        purge_candidate_count,
        purge_candidate_bytes,
        partition_failures,
    )


def _descendant_symlink_failures(
    trade_dir: Path,
    *,
    trade_date: date,
) -> list[dict[str, str]]:
    return [
        _failure_row(
            trade_date=trade_date,
            path=candidate,
            exc=OSError(f"symlink descendant is forbidden:{candidate}"),
            candidate_count=1,
            candidate_bytes=0,
            recovery_required=False,
        )
        for candidate in sorted(trade_dir.rglob("*"))
        if candidate.is_symlink()
    ]


def _is_storage_unlink_claim_path(path: Path) -> bool:
    return any(
        marker in part
        for part in path.parts
        for marker in (
            STORAGE_UNLINK_CLAIM_MARKER,
            STORAGE_TARGET_CUSTODY_MARKER,
        )
    )


def _descendant_unlink_claim_failures(
    trade_dir: Path,
    *,
    trade_date: date,
) -> list[dict[str, str]]:
    failures: list[dict[str, str]] = []
    for candidate in sorted(trade_dir.rglob("*")):
        if (
            not any(
                marker in candidate.name
                for marker in (
                    STORAGE_UNLINK_CLAIM_MARKER,
                    STORAGE_TARGET_CUSTODY_MARKER,
                )
            )
            or candidate.is_symlink()
            or not candidate.is_dir()
        ):
            continue
        try:
            candidate_bytes = _tree_bytes(candidate)
        except OSError:
            candidate_bytes = 0
        failures.append(
            _failure_row(
                trade_date=trade_date,
                path=candidate,
                exc=OSError(f"storage_unlink_claim_recovery_required:{candidate}"),
                candidate_count=1,
                candidate_bytes=candidate_bytes,
                recovery_required=True,
            )
        )
    return failures


def _report_root_custody_failures(root: Path) -> list[dict[str, str]]:
    """Surface unresolved compaction custody instead of silently orphaning it."""

    failures: list[dict[str, str]] = []
    for candidate in sorted(root.rglob("*")):
        if (
            not candidate.is_dir()
            or candidate.is_symlink()
            or not any(
                marker in candidate.name
                for marker in (
                    STORAGE_UNLINK_CLAIM_MARKER,
                    STORAGE_TARGET_CUSTODY_MARKER,
                )
            )
        ):
            continue
        try:
            candidate_bytes = _tree_bytes(candidate)
        except OSError:
            candidate_bytes = 0
        failures.append(
            _failure_row(
                trade_date="unknown",
                path=candidate,
                exc=OSError(f"storage_custody_recovery_required:{candidate}"),
                candidate_count=1,
                candidate_bytes=candidate_bytes,
                recovery_required=True,
            )
        )
    return failures


def _failure_row(
    *,
    trade_date: date | str,
    path: Path,
    exc: Exception,
    candidate_count: int,
    candidate_bytes: int,
    recovery_required: bool,
    published_target_count: int = 0,
    unlinked_source_count: int = 0,
    manifest_update_count: int = 0,
) -> dict[str, str]:
    return {
        "trade_date": (
            trade_date.isoformat() if isinstance(trade_date, date) else trade_date
        ),
        "path": str(path),
        "error_type": type(exc).__name__,
        "reason": str(exc),
        "candidate_count": str(candidate_count),
        "candidate_bytes": str(candidate_bytes),
        "published_target_count": str(published_target_count),
        "unlinked_source_count": str(unlinked_source_count),
        "manifest_update_count": str(manifest_update_count),
        "recovery_required": str(recovery_required).lower(),
    }


def _validated_descendant(root: Path, candidate: Path) -> Path:
    lexical = candidate.absolute()
    try:
        relative = lexical.relative_to(root)
    except ValueError as exc:
        raise ValueError("storage maintenance target escapes configured root") from exc
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("storage maintenance does not follow symlinks")
    resolved = candidate.resolve()
    if not resolved.is_relative_to(root) or resolved == root:
        raise ValueError("storage maintenance target escapes configured root")
    return resolved


def _path_has_open_fd(path: Path) -> bool:
    try:
        expected = path.stat()
    except FileNotFoundError:
        return False
    proc_root = Path("/proc")
    if not proc_root.is_dir():
        raise OSError("open FD verification requires /proc")
    for process_dir in proc_root.iterdir():
        if not process_dir.name.isdigit():
            continue
        fd_dir = process_dir / "fd"
        try:
            descriptors = tuple(fd_dir.iterdir())
        except OSError:
            continue
        for descriptor in descriptors:
            try:
                opened = descriptor.stat()
            except OSError:
                continue
            if opened.st_dev == expected.st_dev and opened.st_ino == expected.st_ino:
                return True
    return False


def _capture_stable_file(path: Path) -> tuple[int, int, int, int, str]:
    if path.is_symlink():
        raise OSError(f"unsafe_symlink_file:{path}")
    initial = path.lstat()
    if not stat.S_ISREG(initial.st_mode):
        raise OSError(f"unsafe_non_regular_file:{path}")
    if _path_has_open_fd(path):
        raise OSError(f"source_open_fd:{path}")
    flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )
    descriptor = os.open(path, flags)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise OSError(f"unsafe_non_regular_file:{path}")
        digest = hashlib.sha256()
        with os.fdopen(descriptor, "rb", closefd=False) as handle:
            while chunk := handle.read(1024 * 1024):
                digest.update(chunk)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    path_after = path.lstat()
    if not stat.S_ISREG(path_after.st_mode):
        raise OSError(f"unsafe_non_regular_file_after_stability_check:{path}")
    before_metadata = (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
    )
    after_metadata = (
        path_after.st_dev,
        path_after.st_ino,
        path_after.st_size,
        path_after.st_mtime_ns,
    )
    descriptor_after_metadata = (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
    )
    if (
        before_metadata != descriptor_after_metadata
        or before_metadata != after_metadata
    ):
        raise OSError(f"source_changed_during_stability_check:{path}")
    if _path_has_open_fd(path):
        raise OSError(f"source_open_fd_after_stability_check:{path}")
    return (*after_metadata, digest.hexdigest())


def _assert_source_unchanged_and_closed(
    source: Path,
    expected: tuple[int, int, int, int, str],
    *,
    phase: str,
) -> None:
    observed = _capture_stable_file(source)
    if observed != expected:
        raise OSError(f"source_changed_{phase}:{source}")


def _assert_tree_stable_and_closed(
    path: Path,
    *,
    phase: str = "partition_preflight",
) -> None:
    candidates = {
        candidate: _capture_stable_file(candidate)
        for candidate in sorted(path.rglob("*"))
        if candidate.is_file() and not candidate.is_symlink()
    }
    observed_paths = {
        candidate
        for candidate in path.rglob("*")
        if candidate.is_file() and not candidate.is_symlink()
    }
    if observed_paths != set(candidates):
        raise OSError(f"source_tree_changed_before_purge:{path}")
    for candidate, expected in candidates.items():
        _assert_source_unchanged_and_closed(
            candidate,
            expected,
            phase=phase,
        )


def _restored_gzip_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with gzip.open(path, "rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _validated_manifest_payload(manifest_path: Path) -> dict[str, object]:
    manifest_snapshot = _capture_stable_file(manifest_path)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    _assert_source_unchanged_and_closed(
        manifest_path,
        manifest_snapshot,
        phase="during_manifest_read",
    )
    if not isinstance(payload, dict) or not isinstance(payload.get("shards"), list):
        raise ValueError(f"invalid market stream manifest: {manifest_path}")
    for shard in payload["shards"]:
        if not isinstance(shard, dict):
            raise ValueError(f"invalid market stream shard manifest: {manifest_path}")
        file_name = str(shard.get("file") or "").strip()
        if not file_name:
            raise ValueError(f"missing shard filename: {manifest_path}")
        if Path(file_name).name != file_name:
            raise ValueError(
                f"manifest shard must be a local filename: {manifest_path}"
            )
        logical_name = file_name.removesuffix(".gz")
        if not logical_name.endswith(".jsonl"):
            raise ValueError(f"manifest shard must be JSONL: {manifest_path}")
        plain = manifest_path.parent / file_name
        compressed = plain.with_suffix(f"{plain.suffix}.gz")
        if plain.is_symlink() or compressed.is_symlink():
            raise OSError(f"manifest shard cannot be a symlink: {plain}")
        if not plain.exists() and not compressed.exists():
            raise FileNotFoundError(f"manifest shard is unavailable: {plain}")
        available = plain if plain.exists() else compressed
        if not available.is_file():
            raise OSError(f"manifest shard must be a regular file: {available}")
    return payload


def _manifest_logical_sources(manifest_path: Path) -> tuple[Path, ...]:
    payload = _validated_manifest_payload(manifest_path)
    sources: list[Path] = []
    for shard in payload["shards"]:
        file_path = manifest_path.parent / str(shard["file"])
        logical = file_path.with_suffix("") if file_path.suffix == ".gz" else file_path
        if logical.suffix == ".jsonl":
            sources.append(logical)
    return tuple(sources)


def _preflight_compression_group(
    sources: list[Path],
    manifest_path: Path | None,
) -> None:
    if manifest_path is not None:
        _validated_manifest_payload(manifest_path)
    for source in sources:
        source_snapshot = _capture_stable_file(source)
        target = source.with_suffix(f"{source.suffix}.gz")
        if target.is_symlink():
            raise OSError(f"compressed_target_symlink_forbidden:{target}")
        if target.exists():
            target_snapshot = _capture_stable_file(target)
            if _restored_gzip_sha256(target) != source_snapshot[-1]:
                raise OSError(f"existing_compressed_source_mismatch:{source}")
            _assert_source_unchanged_and_closed(
                target,
                target_snapshot,
                phase="group_preflight",
            )


def _maintain_compression_groups(
    root_path: Path,
    trade_dir: Path,
    *,
    trade_date: date,
    as_of_date: date,
    apply: bool,
) -> tuple[list[StorageMaintenanceAction], list[dict[str, str]]]:
    actions: list[StorageMaintenanceAction] = []
    failures: list[dict[str, str]] = []
    directories = sorted(
        {
            path.parent
            for path in (
                *trade_dir.rglob("*.jsonl"),
                *trade_dir.rglob("*.manifest.json"),
            )
            if not path.is_symlink() and not _is_storage_unlink_claim_path(path)
        }
    )
    for directory in directories:
        sources_in_directory = sorted(
            path for path in directory.glob("*.jsonl") if not path.is_symlink()
        )
        manifests = sorted(
            path for path in directory.glob("*.manifest.json") if not path.is_symlink()
        )
        manifest_groups: list[tuple[Path, list[Path]]] = []
        source_owners: dict[Path, Path] = {}
        preflight_errors: list[tuple[Path, Exception]] = []
        for manifest_path in manifests:
            try:
                logical_sources = list(_manifest_logical_sources(manifest_path))
                duplicate_sources = {
                    source
                    for source in logical_sources
                    if logical_sources.count(source) > 1
                }
                overlap = {
                    source for source in logical_sources if source in source_owners
                }
                if duplicate_sources or overlap:
                    conflicts = duplicate_sources | overlap
                    raise ValueError(
                        "multiple manifests claim one shard:"
                        + ",".join(str(path) for path in sorted(conflicts))
                    )
                manifest_groups.append(
                    (
                        manifest_path,
                        [source for source in logical_sources if source.exists()],
                    )
                )
                source_owners.update(
                    {source: manifest_path for source in logical_sources}
                )
            except Exception as exc:
                preflight_errors.append((manifest_path, exc))

        # Ownership is a directory-wide precondition. Processing an earlier
        # valid manifest before discovering a later overlap can strand the
        # latter on a missing plain shard. Reject the whole physical session
        # before publishing any gzip or rewriting any manifest.
        if preflight_errors:
            for manifest_path, exc in preflight_errors:
                failures.append(
                    _failure_row(
                        trade_date=trade_date,
                        path=manifest_path,
                        exc=exc,
                        candidate_count=0,
                        candidate_bytes=(
                            manifest_path.stat().st_size
                            if manifest_path.exists()
                            else 0
                        ),
                        recovery_required=False,
                    )
                )
            failures.append(
                _failure_row(
                    trade_date=trade_date,
                    path=directory,
                    exc=ValueError("directory_manifest_ownership_preflight_failed"),
                    candidate_count=len(sources_in_directory),
                    candidate_bytes=sum(
                        source.stat().st_size for source in sources_in_directory
                    ),
                    recovery_required=False,
                )
            )
            continue

        groups: list[tuple[Path | None, list[Path]]] = list(manifest_groups)
        groups.extend(
            (None, [source])
            for source in sources_in_directory
            if source not in source_owners
        )
        for manifest_path, sources in groups:
            group_path = manifest_path or sources[0]
            candidate_bytes = sum(
                source.stat().st_size for source in sources if source.exists()
            )
            if not apply:
                if manifest_path is not None and not sources:
                    if _manifest_requires_reference_repair(manifest_path):
                        actions.append(
                            StorageMaintenanceAction(
                                action="repair_manifest_reference",
                                path=str(manifest_path),
                                trade_date=trade_date.isoformat(),
                                source_bytes=manifest_path.stat().st_size,
                                applied=False,
                            )
                        )
                    continue
                actions.extend(
                    StorageMaintenanceAction(
                        action=(
                            "finalize_verified_compression"
                            if source.with_suffix(f"{source.suffix}.gz").exists()
                            else "compress_jsonl"
                        ),
                        path=str(source),
                        trade_date=trade_date.isoformat(),
                        source_bytes=source.stat().st_size,
                        applied=False,
                    )
                    for source in sources
                )
                continue
            try:
                if manifest_path is not None and not sources:
                    if _refresh_one_manifest(
                        manifest_path,
                        as_of_date=as_of_date,
                    ):
                        actions.append(
                            StorageMaintenanceAction(
                                action="repair_manifest_reference",
                                path=str(manifest_path),
                                trade_date=trade_date.isoformat(),
                                source_bytes=manifest_path.stat().st_size,
                                applied=True,
                            )
                        )
                    continue
                sources = [
                    _validated_descendant(root_path, source) for source in sources
                ]
                _preflight_compression_group(sources, manifest_path)
                group_actions, group_failure = _compress_group_verified(
                    sources,
                    manifest_path=manifest_path,
                    trade_date=trade_date,
                    as_of_date=as_of_date,
                )
                actions.extend(group_actions)
                if group_failure is not None:
                    failures.append(group_failure)
            except Exception as exc:
                failures.append(
                    _failure_row(
                        trade_date=trade_date,
                        path=group_path,
                        exc=exc,
                        candidate_count=len(sources),
                        candidate_bytes=candidate_bytes,
                        recovery_required=False,
                    )
                )
    return actions, failures


def _manifest_requires_reference_repair(manifest_path: Path) -> bool:
    payload = _validated_manifest_payload(manifest_path)
    for shard in payload["shards"]:
        plain = manifest_path.parent / str(shard["file"])
        if plain.suffix == ".gz" or plain.exists():
            continue
        if plain.with_suffix(f"{plain.suffix}.gz").exists():
            return True
    return False


def _prepare_verified_gzip(
    source: Path,
    target: Path,
    source_snapshot: tuple[int, int, int, int, str],
) -> Path:
    """Build and verify a private gzip without publishing or unlinking source."""

    source_hash = hashlib.sha256()
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}.", suffix=".tmp", dir=target.parent
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        with (
            source.open("rb") as input_handle,
            gzip.open(temporary, "wb", compresslevel=6) as output_handle,
        ):
            while chunk := input_handle.read(1024 * 1024):
                source_hash.update(chunk)
                output_handle.write(chunk)
        if source_hash.hexdigest() != source_snapshot[-1]:
            raise OSError(f"source_changed_during_compression:{source}")
        with temporary.open("rb") as handle:
            os.fsync(handle.fileno())
        verified_hash = hashlib.sha256()
        with gzip.open(temporary, "rb") as handle:
            while chunk := handle.read(1024 * 1024):
                verified_hash.update(chunk)
        if verified_hash.digest() != source_hash.digest():
            raise OSError("compressed JSONL verification failed")
        os.chmod(temporary, 0o640)
        return temporary
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def _fsync_directory(path: Path) -> None:
    directory_descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(directory_descriptor)
    finally:
        os.close(directory_descriptor)


def _publish_gzip_no_clobber(temporary: Path, target: Path) -> None:
    """Atomically publish a prepared gzip without replacing any target inode."""

    try:
        os.link(temporary, target)
    except FileExistsError as exc:
        raise OSError(f"compressed_target_appeared_before_publish:{target}") from exc
    _fsync_directory(target.parent)


def _restore_claim_no_clobber(claim: Path, source: Path) -> str:
    """Restore a claimed inode without replacing a producer-created path.

    The private claim is deliberately preserved.  Removing it after a
    successful hard-link restore would reopen a last-link race if a producer
    replaced ``source`` immediately afterwards.
    """

    try:
        os.link(claim, source, follow_symlinks=False)
    except FileExistsError:
        return "source_path_already_present_claim_preserved"
    except OSError as exc:
        return f"source_restore_failed_claim_preserved:{type(exc).__name__}:{exc}"
    _fsync_directory(source.parent)
    return "source_hardlink_restored_claim_preserved"


def _claim_source_for_verified_unlink(
    source: Path,
    expected: tuple[int, int, int, int, str],
) -> tuple[Path, Path]:
    """Move a pathname into a maintenance-owned namespace before unlinking.

    ``unlink(source)`` can delete a producer's replacement inode after even a
    final stat check.  Instead, atomically move whichever inode owns the source
    pathname into a private same-filesystem directory, then verify that the
    claimed inode is exactly the previously validated source.  A raced-in
    replacement is restored without clobbering and the private claim is kept as
    recovery evidence; only an exact original-inode claim may be unlinked.
    """

    claim_directory = Path(
        tempfile.mkdtemp(
            prefix=f".{source.name}.storage-unlink-claim.",
            dir=source.parent,
        )
    )
    os.chmod(claim_directory, 0o700)
    claim = claim_directory / source.name
    moved = False
    try:
        os.rename(source, claim)
        moved = True
        _fsync_directory(source.parent)
        _fsync_directory(claim_directory)
        observed = _capture_stable_file(claim)
        if observed != expected:
            restore_status = _restore_claim_no_clobber(claim, source)
            raise OSError(
                "source_inode_replaced_before_verified_claim:"
                f"{source}:recovery_path={claim}:restore_status={restore_status}"
            )
        return claim, claim_directory
    except Exception as exc:
        if moved and (claim.exists() or claim.is_symlink()):
            restore_status = _restore_claim_no_clobber(claim, source)
            if "recovery_path=" not in str(exc):
                raise OSError(
                    "source_claim_verification_failed:"
                    f"{source}:recovery_path={claim}:"
                    f"restore_status={restore_status}:{exc}"
                ) from exc
        else:
            try:
                claim_directory.rmdir()
            except OSError:
                pass
        raise


def _assert_source_path_absent_after_claim(source: Path, *, phase: str) -> None:
    """Fail if a producer recreated any inode at the claimed logical path."""

    try:
        source.lstat()
    except FileNotFoundError:
        return
    raise OSError(f"source_path_recreated_{phase}:{source}")


def _create_verified_target_custody(
    target: Path,
    expected: tuple[int, int, int, int, str],
) -> tuple[Path, Path]:
    """Keep an inode-bound verified gzip link until source removal is durable."""

    custody_directory = Path(
        tempfile.mkdtemp(
            prefix=f".{target.name}.storage-target-custody.",
            dir=target.parent,
        )
    )
    os.chmod(custody_directory, 0o700)
    custody = custody_directory / target.name
    linked = False
    try:
        os.link(target, custody, follow_symlinks=False)
        linked = True
        _fsync_directory(custody_directory)
        _fsync_directory(target.parent)
        _assert_source_unchanged_and_closed(
            target,
            expected,
            phase="after_target_custody_link",
        )
        _assert_source_unchanged_and_closed(
            custody,
            expected,
            phase="after_target_custody_link",
        )
        return custody, custody_directory
    except Exception:
        if linked:
            custody.unlink(missing_ok=True)
        try:
            custody_directory.rmdir()
        except OSError:
            pass
        raise


def _restore_target_custody_no_clobber(custody: Path, target: Path) -> str:
    """Restore a missing verified gzip path while preserving custody evidence."""

    try:
        os.link(custody, target, follow_symlinks=False)
    except FileExistsError:
        return "target_path_already_present_custody_preserved"
    except OSError as exc:
        return f"target_restore_failed_custody_preserved:{type(exc).__name__}:{exc}"
    _fsync_directory(target.parent)
    return "target_hardlink_restored_custody_preserved"


def _target_matches_source_content(
    target: Path,
    source_snapshot: tuple[int, int, int, int, str],
) -> bool:
    try:
        target_snapshot = _capture_stable_file(target)
        if _restored_gzip_sha256(target) != source_snapshot[-1]:
            return False
        _assert_source_unchanged_and_closed(
            target,
            target_snapshot,
            phase="during_failure_recovery_target_check",
        )
        return True
    except (FileNotFoundError, OSError, EOFError, gzip.BadGzipFile):
        return False


def _compress_group_verified(
    sources: list[Path],
    *,
    manifest_path: Path | None,
    trade_date: date,
    as_of_date: date,
    expected_source_sha256s: dict[Path, str] | None = None,
) -> tuple[list[StorageMaintenanceAction], dict[str, str] | None]:

    plans: list[
        tuple[
            str,
            Path,
            Path,
            int,
            tuple[int, int, int, int, str],
            tuple[int, int, int, int, str] | None,
            Path | None,
        ]
    ] = []
    temporary_paths: list[Path] = []
    published_targets: set[Path] = set()
    source_claims: dict[Path, tuple[Path, Path]] = {}
    target_custodies: dict[Path, tuple[Path, Path]] = {}
    manifest_before = manifest_path.read_bytes() if manifest_path is not None else None
    try:
        for source in sources:
            target = source.with_suffix(f"{source.suffix}.gz")
            if target.is_symlink():
                raise OSError(f"compressed_target_symlink_forbidden:{target}")
            source_snapshot = _capture_stable_file(source)
            if (
                expected_source_sha256s is not None
                and expected_source_sha256s.get(source) != source_snapshot[-1]
            ):
                raise OSError(f"source_changed_after_contract_validation:{source}")
            source_bytes = source_snapshot[2]
            if target.exists():
                target_snapshot = _capture_stable_file(target)
                if _restored_gzip_sha256(target) != source_snapshot[-1]:
                    raise OSError(f"existing_compressed_source_mismatch:{source}")
                plans.append(
                    (
                        "finalize_verified_compression",
                        source,
                        target,
                        source_bytes,
                        source_snapshot,
                        target_snapshot,
                        None,
                    )
                )
                continue
            temporary = _prepare_verified_gzip(source, target, source_snapshot)
            temporary_paths.append(temporary)
            plans.append(
                (
                    "compress_jsonl",
                    source,
                    target,
                    source_bytes,
                    source_snapshot,
                    None,
                    temporary,
                )
            )

        # A later shard may have opened or changed while an earlier gzip was
        # being prepared. Close that window before publishing any target.
        for _, source, target, _, source_snapshot, target_snapshot, _ in plans:
            _assert_source_unchanged_and_closed(
                source,
                source_snapshot,
                phase="before_partition_publish",
            )
            if target_snapshot is None:
                if target.exists() or target.is_symlink():
                    raise OSError(f"compressed_target_appeared_before_publish:{target}")
            else:
                _assert_source_unchanged_and_closed(
                    target,
                    target_snapshot,
                    phase="before_partition_publish",
                )

        for _, _, target, _, _, _, temporary in plans:
            if temporary is not None:
                try:
                    _publish_gzip_no_clobber(temporary, target)
                finally:
                    if (
                        target.exists()
                        and not target.is_symlink()
                        and temporary.exists()
                    ):
                        target_state = target.lstat()
                        temporary_state = temporary.lstat()
                        if (
                            stat.S_ISREG(target_state.st_mode)
                            and target_state.st_dev == temporary_state.st_dev
                            and target_state.st_ino == temporary_state.st_ino
                        ):
                            published_targets.add(target)

        # Do not remove a source, or rewrite its manifest, if any shard became
        # open/unstable across publication. Valid gzip copies may remain as
        # recoverable evidence; they never replace another inode.
        for _, source, _, _, source_snapshot, _, _ in plans:
            _assert_source_unchanged_and_closed(
                source,
                source_snapshot,
                phase="after_partition_publish",
            )

        if manifest_path is not None:
            _refresh_one_manifest(
                manifest_path,
                as_of_date=as_of_date,
                planned_sources={plan[1] for plan in plans},
            )

        for _, source, target, _, source_snapshot, _, _ in plans:
            _assert_source_unchanged_and_closed(
                source,
                source_snapshot,
                phase="before_finalize_unlink",
            )
            target_snapshot = _capture_stable_file(target)
            if _restored_gzip_sha256(target) != source_snapshot[-1]:
                raise OSError(f"compressed_target_changed_before_unlink:{target}")
            _assert_source_unchanged_and_closed(
                target,
                target_snapshot,
                phase="before_finalize_unlink",
            )
            custody, custody_directory = _create_verified_target_custody(
                target,
                target_snapshot,
            )
            target_custodies[source] = (custody, custody_directory)
            claim, claim_directory = _claim_source_for_verified_unlink(
                source,
                source_snapshot,
            )
            source_claims[source] = (claim, claim_directory)
            _assert_source_path_absent_after_claim(
                source,
                phase="immediately_after_verified_claim",
            )
            # The source pathname is no longer used for deletion.  Recheck the
            # private claim and gzip before removing only the bound original
            # inode from the maintenance-owned namespace.
            _assert_source_unchanged_and_closed(
                claim,
                source_snapshot,
                phase="after_verified_claim",
            )
            _assert_source_unchanged_and_closed(
                target,
                target_snapshot,
                phase="after_verified_claim",
            )
            _assert_source_path_absent_after_claim(
                source,
                phase="before_verified_claim_unlink",
            )
            claim.unlink()
            _fsync_directory(claim_directory)
            claim_directory.rmdir()
            _fsync_directory(source.parent)
            source_claims.pop(source, None)
            _assert_source_unchanged_and_closed(
                target,
                target_snapshot,
                phase="after_verified_source_unlink",
            )
            _assert_source_unchanged_and_closed(
                custody,
                target_snapshot,
                phase="after_verified_source_unlink",
            )
            custody.unlink()
            _fsync_directory(custody_directory)
            custody_directory.rmdir()
            _fsync_directory(target.parent)
            target_custodies.pop(source, None)

        return (
            [
                StorageMaintenanceAction(
                    action=action,
                    path=str(source),
                    trade_date=trade_date.isoformat(),
                    source_bytes=source_bytes,
                    applied=True,
                )
                for action, source, _, source_bytes, _, _, _ in plans
            ],
            None,
        )
    except Exception as exc:
        for source, (claim, _) in source_claims.items():
            if claim.exists() and not claim.is_symlink():
                _restore_claim_no_clobber(claim, source)
        for source, (custody, _) in target_custodies.items():
            if custody.exists() and not custody.is_symlink():
                target = source.with_suffix(f"{source.suffix}.gz")
                _restore_target_custody_no_clobber(custody, target)
        resolved_custodies: list[Path] = []
        source_snapshots = {plan[1]: plan[4] for plan in plans}
        for source, (custody, custody_directory) in target_custodies.items():
            source_snapshot = source_snapshots.get(source)
            target = source.with_suffix(f"{source.suffix}.gz")
            try:
                source_matches = (
                    source_snapshot is not None
                    and _capture_stable_file(source) == source_snapshot
                )
            except (FileNotFoundError, OSError):
                source_matches = False
            if (
                source_snapshot is None
                or not custody.exists()
                or not source_matches
                or not _target_matches_source_content(target, source_snapshot)
            ):
                continue
            custody.unlink()
            _fsync_directory(custody_directory)
            custody_directory.rmdir()
            _fsync_directory(target.parent)
            resolved_custodies.append(source)
        for source in resolved_custodies:
            target_custodies.pop(source, None)
        partial_actions: list[StorageMaintenanceAction] = []
        unlinked_count = 0
        unresolved_plans: list[
            tuple[
                str,
                Path,
                Path,
                int,
                tuple[int, int, int, int, str],
                tuple[int, int, int, int, str] | None,
                Path | None,
            ]
        ] = []
        for plan in plans:
            action, source, target, source_bytes, _, _, _ = plan
            source_exists = source.exists()
            target_exists = target.exists()
            target_verified = target_exists and _target_matches_source_content(
                target,
                plan[4],
            )
            if target_verified and not source_exists:
                unlinked_count += 1
                partial_actions.append(
                    StorageMaintenanceAction(
                        action=action,
                        path=str(source),
                        trade_date=trade_date.isoformat(),
                        source_bytes=source_bytes,
                        applied=True,
                    )
                )
            else:
                unresolved_plans.append(plan)
                if target_exists and source_exists and target in published_targets:
                    partial_actions.append(
                        StorageMaintenanceAction(
                            action="publish_verified_gzip_source_preserved",
                            path=str(source),
                            trade_date=trade_date.isoformat(),
                            source_bytes=source_bytes,
                            applied=True,
                        )
                    )
        manifest_changed = (
            manifest_path is not None
            and manifest_path.exists()
            and manifest_before != manifest_path.read_bytes()
        )
        if manifest_changed:
            partial_actions.append(
                StorageMaintenanceAction(
                    action="repair_manifest_reference",
                    path=str(manifest_path),
                    trade_date=trade_date.isoformat(),
                    source_bytes=manifest_path.stat().st_size,
                    applied=True,
                )
            )
        failure = _failure_row(
            trade_date=trade_date,
            path=manifest_path or sources[0],
            exc=exc,
            candidate_count=len(unresolved_plans),
            candidate_bytes=sum(plan[3] for plan in unresolved_plans),
            recovery_required=any(
                source.exists() and target.exists() for _, source, target, *_ in plans
            )
            or any(claim.exists() for claim, _ in source_claims.values())
            or any(custody.exists() for custody, _ in target_custodies.values()),
            published_target_count=sum(target.exists() for target in published_targets),
            unlinked_source_count=unlinked_count,
            manifest_update_count=int(manifest_changed),
        )
        return partial_actions, failure
    finally:
        for temporary in temporary_paths:
            temporary.unlink(missing_ok=True)


def _refresh_one_manifest(
    manifest_path: Path,
    *,
    as_of_date: date,
    planned_sources: set[Path] | None = None,
) -> bool:
    """Keep one writer manifest discoverable after group-local compression."""

    planned = planned_sources or set()
    payload = _validated_manifest_payload(manifest_path)
    changed = False
    for shard in payload["shards"]:
        file_name = str(shard.get("file") or "").strip()
        plain = manifest_path.parent / file_name
        if plain.suffix == ".gz":
            continue
        compressed = plain.with_suffix(f"{plain.suffix}.gz")
        if plain.exists() and plain not in planned:
            continue
        if not compressed.exists():
            raise FileNotFoundError(f"manifest shard is unavailable: {plain}")
        shard["file"] = compressed.name
        shard["bytes"] = compressed.stat().st_size
        shard["compressed"] = True
        changed = True
    if changed:
        payload["storage_maintenance_schema"] = MAINTENANCE_SCHEMA
        payload["storage_maintenance_as_of_date"] = as_of_date.isoformat()
        _write_json_atomic(manifest_path, payload)
    return changed


def _write_json_atomic(path: Path, payload: dict[str, object]) -> None:
    expected = _capture_stable_file(path)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        encoded = (
            json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n"
        ).encode("utf-8")
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o640)
        _assert_source_unchanged_and_closed(
            path,
            expected,
            phase="before_manifest_publish",
        )
        os.replace(temporary, path)
        directory_descriptor = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    finally:
        temporary.unlink(missing_ok=True)


def _write_capacity_status_atomic(
    path: Path,
    payload: dict[str, object],
) -> None:
    path = Path(path).absolute()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.is_symlink() or not path.parent.is_dir():
        raise OSError("capacity status parent must be a real directory")
    expected = _capture_stable_file(path) if path.exists() else None
    if path.is_symlink():
        raise OSError("capacity status path cannot be a symlink")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        encoded = (
            json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n"
        ).encode("utf-8")
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o640)
        if expected is None:
            if path.exists() or path.is_symlink():
                raise OSError("capacity status target appeared before publish")
        else:
            _assert_source_unchanged_and_closed(
                path,
                expected,
                phase="before_capacity_status_publish",
            )
        os.replace(temporary, path)
        _fsync_directory(path.parent)
        published = json.loads(path.read_text(encoding="utf-8"))
        if published != payload:
            raise OSError("capacity status post-write verification failed")
    finally:
        temporary.unlink(missing_ok=True)


def _capacity_status_artifact(
    result: dict[str, object],
    *,
    target_date: date,
) -> dict[str, object]:
    state = str(result.get("capacity_state") or "critical")
    reason_codes = result.get("capacity_reason_codes")
    if not isinstance(reason_codes, list) or not all(
        isinstance(reason, str) for reason in reason_codes
    ):
        reason_codes = ["storage_capacity_contract_invalid"]
        state = "critical"
    content: dict[str, object] = {
        "schema": STORAGE_CAPACITY_STATUS_SCHEMA,
        "target_date": target_date.isoformat(),
        "generated_at": datetime.now(KST).isoformat(),
        "status": (
            "critical_blocked"
            if state == "critical"
            else ("low_warning_workorder_open" if state == "low_warning" else "healthy")
        ),
        "capacity_state": state,
        "capacity_warning": state == "low_warning",
        "capacity_failure": state == "critical",
        "capacity_workorder": {
            "required": state != "healthy",
            "state": "open" if state != "healthy" else "not_required",
            "reason_codes": reason_codes,
            "owner": "StorageCapacityAndRetentionAuthority",
            "next_action": (
                "verified_closed_date_compression_then_capacity_recheck"
                if state == "low_warning"
                else (
                    "block_large_artifact_growth_and_request_retention_or_capacity_authority"
                    if state == "critical"
                    else "continue_scheduled_capacity_observation"
                )
            ),
        },
        "disk_total_bytes": result.get("disk_total_bytes"),
        "disk_used_bytes_after": result.get("disk_used_bytes_after"),
        "disk_free_bytes_before": result.get("disk_free_bytes_before"),
        "disk_free_bytes_after": result.get("disk_free_bytes_after"),
        "disk_free_bytes_delta": result.get("disk_free_bytes_delta"),
        "retained_physical_bytes_before": result.get("retained_physical_bytes_before"),
        "retained_physical_bytes_after": result.get("retained_physical_bytes_after"),
        "retained_physical_bytes_delta": result.get("retained_physical_bytes_delta"),
        "compressed_target_bytes": result.get("compressed_target_bytes"),
        "bytes_reclaimed": result.get("bytes_reclaimed"),
        "low_disk_watermark_bytes": result.get("low_disk_watermark_bytes"),
        "critical_disk_watermark_bytes": result.get("critical_disk_watermark_bytes"),
        "purge_enabled": result.get("purge_enabled") is True,
        "deletion_performed": result.get("deletion_performed") is True,
        "automatic_deletion_authorized": False,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "trading_runtime_effect": False,
        "provider_runtime_effect": False,
        "provider_route_change_allowed": False,
        "network_call_performed_by_module": False,
        "decision_authority": MAINTENANCE_AUTHORITY,
        "forbidden_uses": [
            "automatic_deletion_or_purge_authorization",
            "broker_order_submission_or_cancel",
            "provider_route_or_network_call",
            "strategy_threshold_quantity_cap_or_bot_change",
        ],
    }
    return {
        **content,
        "artifact_content_sha256": _canonical_sha256(content),
    }


def _validate_capacity_status_payload(
    payload: dict[str, object],
    *,
    target_date: date,
    low_disk_watermark_bytes: int,
    critical_disk_watermark_bytes: int,
) -> str:
    """Validate the exact-date capacity artifact consumed by P2 growth gates."""

    if payload.get("schema") != STORAGE_CAPACITY_STATUS_SCHEMA:
        raise ValueError("capacity_status_schema_invalid")
    if payload.get("target_date") != target_date.isoformat():
        raise ValueError("capacity_status_target_date_invalid")
    _validate_content_hash(payload, hash_field="artifact_content_sha256")
    _validate_source_only_authority(payload)
    for field in (
        "automatic_deletion_authorized",
        "trading_runtime_effect",
        "provider_runtime_effect",
        "provider_route_change_allowed",
        "network_call_performed_by_module",
    ):
        if payload.get(field) is not False:
            raise ValueError(f"capacity_status_authority_invalid:{field}")
    if payload.get("decision_authority") != MAINTENANCE_AUTHORITY:
        raise ValueError("capacity_status_decision_authority_invalid")
    forbidden_uses = payload.get("forbidden_uses")
    required_forbidden_uses = {
        "automatic_deletion_or_purge_authorization",
        "broker_order_submission_or_cancel",
        "provider_route_or_network_call",
        "strategy_threshold_quantity_cap_or_bot_change",
    }
    if (
        not isinstance(forbidden_uses, list)
        or not all(isinstance(value, str) for value in forbidden_uses)
        or not required_forbidden_uses.issubset(set(forbidden_uses))
    ):
        raise ValueError("capacity_status_forbidden_uses_invalid")

    generated_at_raw = payload.get("generated_at")
    if not isinstance(generated_at_raw, str):
        raise ValueError("capacity_status_generated_at_invalid")
    try:
        generated_at = datetime.fromisoformat(generated_at_raw)
    except ValueError as exc:
        raise ValueError("capacity_status_generated_at_invalid") from exc
    if generated_at.tzinfo is None or generated_at.utcoffset() is None:
        raise ValueError("capacity_status_generated_at_naive")

    expected_thresholds = {
        "low_disk_watermark_bytes": low_disk_watermark_bytes,
        "critical_disk_watermark_bytes": critical_disk_watermark_bytes,
    }
    for field, expected in expected_thresholds.items():
        value = payload.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or value != expected:
            raise ValueError(f"capacity_status_watermark_invalid:{field}")
    free_bytes = payload.get("disk_free_bytes_after")
    if (
        isinstance(free_bytes, bool)
        or not isinstance(free_bytes, int)
        or free_bytes < 0
    ):
        raise ValueError("capacity_status_disk_free_invalid")
    state = _capacity_state(
        free_bytes,
        low_disk_watermark_bytes=low_disk_watermark_bytes,
        critical_disk_watermark_bytes=critical_disk_watermark_bytes,
    )
    expected_status = (
        "critical_blocked"
        if state == "critical"
        else ("low_warning_workorder_open" if state == "low_warning" else "healthy")
    )
    if (
        payload.get("capacity_state") != state
        or payload.get("status") != expected_status
        or payload.get("capacity_warning") is not (state == "low_warning")
        or payload.get("capacity_failure") is not (state == "critical")
    ):
        raise ValueError("capacity_status_state_invalid")
    workorder = payload.get("capacity_workorder")
    expected_reasons = _capacity_reason_codes(state)
    if (
        not isinstance(workorder, dict)
        or workorder.get("required") is not (state != "healthy")
        or workorder.get("state") != ("open" if state != "healthy" else "not_required")
        or workorder.get("reason_codes") != expected_reasons
    ):
        raise ValueError("capacity_status_workorder_invalid")
    return state


def evaluate_large_artifact_capacity_gate(
    *,
    target_date: date,
    capacity_status_path: Path | None,
    storage_path: Path,
    low_disk_watermark_bytes: int = STORAGE_LOW_DISK_WATERMARK_BYTES,
    critical_disk_watermark_bytes: int = STORAGE_CRITICAL_DISK_WATERMARK_BYTES,
) -> dict[str, object]:
    """Read-only fail-closed capacity gate for large P2 artifact growth.

    A missing status artifact is not itself a blocker because a current direct
    filesystem snapshot remains authoritative. A present artifact must be an
    exact-date, content-hashed artifact under the same 5 GiB/1 GiB watermarks;
    invalid present evidence is blocked instead of silently ignored. The more
    severe of valid artifact and direct snapshot states is effective.
    """

    if isinstance(target_date, datetime) or not isinstance(target_date, date):
        raise TypeError("target_date must be a date")
    _validate_capacity_watermarks(
        low_disk_watermark_bytes=low_disk_watermark_bytes,
        critical_disk_watermark_bytes=critical_disk_watermark_bytes,
    )
    reason_codes: list[str] = []
    direct_snapshot: dict[str, int] | None = None
    direct_state = "unknown"
    direct_snapshot_error: str | None = None
    try:
        direct_snapshot = _disk_capacity_snapshot(Path(storage_path))
        if any(
            isinstance(direct_snapshot.get(field), bool)
            or not isinstance(direct_snapshot.get(field), int)
            or int(direct_snapshot[field]) < 0
            for field in (
                "disk_total_bytes",
                "disk_used_bytes",
                "disk_free_bytes",
            )
        ):
            raise ValueError("direct_disk_capacity_snapshot_fields_invalid")
        if (
            direct_snapshot["disk_used_bytes"] > direct_snapshot["disk_total_bytes"]
            or direct_snapshot["disk_free_bytes"] > direct_snapshot["disk_total_bytes"]
        ):
            raise ValueError("direct_disk_capacity_snapshot_census_invalid")
        direct_state = _capacity_state(
            direct_snapshot["disk_free_bytes"],
            low_disk_watermark_bytes=low_disk_watermark_bytes,
            critical_disk_watermark_bytes=critical_disk_watermark_bytes,
        )
    except (OSError, KeyError, TypeError, ValueError) as exc:
        direct_snapshot_error = f"{type(exc).__name__}:{exc}"
        reason_codes.append("direct_disk_capacity_snapshot_invalid")

    artifact_status = "missing"
    artifact_state: str | None = None
    artifact_raw_sha256: str | None = None
    artifact_validation_error: str | None = None
    logical_artifact_path: Path | None = None
    if capacity_status_path is not None:
        candidate = Path(capacity_status_path).absolute()
        logical_artifact_path = (
            candidate.with_name(candidate.name.removesuffix(".gz"))
            if candidate.suffix == ".gz"
            else candidate
        )
        compressed_artifact_path = logical_artifact_path.with_suffix(
            f"{logical_artifact_path.suffix}.gz"
        )
        artifact_present = any(
            path.exists() or path.is_symlink()
            for path in (logical_artifact_path, compressed_artifact_path)
        )
        if artifact_present:
            artifact_status = "invalid"
            try:
                payload, artifact_raw_sha256 = _read_owned_json_with_raw_sha256(
                    logical_artifact_path
                )
                artifact_state = _validate_capacity_status_payload(
                    payload,
                    target_date=target_date,
                    low_disk_watermark_bytes=low_disk_watermark_bytes,
                    critical_disk_watermark_bytes=critical_disk_watermark_bytes,
                )
            except (OSError, ValueError) as exc:
                artifact_validation_error = f"{type(exc).__name__}:{exc}"
                reason_codes.append("capacity_status_artifact_invalid")
            else:
                artifact_status = "valid"

    state_severity = {"healthy": 0, "low_warning": 1, "critical": 2}
    valid_states = [direct_state]
    if artifact_status == "valid" and artifact_state is not None:
        valid_states.append(artifact_state)
    effective_state = (
        max(valid_states, key=lambda state: state_severity.get(state, 3))
        if all(state in state_severity for state in valid_states)
        else "unknown"
    )
    if artifact_status == "missing":
        reason_codes.append("capacity_status_artifact_missing_direct_snapshot_used")
    if direct_state == "critical":
        reason_codes.append("direct_disk_free_below_critical_watermark")
    elif direct_state == "low_warning":
        reason_codes.append("direct_disk_free_below_low_watermark")
    if artifact_state == "critical":
        reason_codes.append("capacity_artifact_free_below_critical_watermark")
    elif artifact_state == "low_warning":
        reason_codes.append("capacity_artifact_free_below_low_watermark")

    growth_allowed = (
        artifact_status != "invalid"
        and direct_state != "unknown"
        and effective_state != "critical"
    )
    if not growth_allowed:
        status = (
            "blocked_invalid_capacity_artifact"
            if artifact_status == "invalid"
            else "blocked_critical_or_unknown_capacity"
        )
    elif effective_state == "low_warning":
        status = "allowed_with_low_capacity_warning"
    else:
        status = "allowed"
    return {
        "schema": STORAGE_CAPACITY_GROWTH_GATE_SCHEMA,
        "target_date": target_date.isoformat(),
        "status": status,
        "large_artifact_growth_allowed": growth_allowed,
        "effective_capacity_state": effective_state,
        "artifact_status": artifact_status,
        "artifact_capacity_state": artifact_state,
        "capacity_status_artifact_path": (
            str(logical_artifact_path) if logical_artifact_path is not None else None
        ),
        "capacity_status_artifact_raw_sha256": artifact_raw_sha256,
        "capacity_status_artifact_validation_error": artifact_validation_error,
        "direct_snapshot_provenance": "shutil.disk_usage_at_consumer_gate",
        "direct_capacity_state": direct_state,
        "direct_disk_snapshot": direct_snapshot,
        "direct_disk_snapshot_error": direct_snapshot_error,
        "low_disk_watermark_bytes": low_disk_watermark_bytes,
        "critical_disk_watermark_bytes": critical_disk_watermark_bytes,
        "reason_codes": list(dict.fromkeys(reason_codes)),
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


def _tree_bytes(path: Path) -> int:
    total = 0
    for item in path.rglob("*"):
        state = item.lstat()
        if stat.S_ISREG(state.st_mode):
            total += state.st_size
    return total


def _result(
    root: Path,
    as_of_date: date,
    runtime_trade_date: date,
    apply: bool,
    purge_expired: bool,
    actions: list[StorageMaintenanceAction],
    *,
    partition_failures: list[dict[str, str]],
    purge_candidate_count: int,
    purge_candidate_bytes: int,
    disk_before: dict[str, int],
    retained_physical_bytes_before: int,
    storage_policy: PathStoragePolicy,
) -> dict[str, object]:
    purge_applied_count = sum(
        row.action == "purge_trade_date" and row.applied for row in actions
    )
    purge_partial_applied_count = sum(
        row.action == "purge_trade_date_partial" and row.applied for row in actions
    )
    disk_after = _disk_capacity_snapshot(root)
    capacity_metrics = _capacity_metrics(
        disk_before=disk_before,
        disk_after=disk_after,
        retained_physical_bytes_before=retained_physical_bytes_before,
        retained_physical_bytes_after=_regular_file_bytes([root]),
        compressed_target_bytes=_compressed_target_bytes(actions),
        low_disk_watermark_bytes=storage_policy.low_disk_watermark_bytes,
        critical_disk_watermark_bytes=storage_policy.critical_disk_watermark_bytes,
    )
    return {
        "schema": MAINTENANCE_SCHEMA,
        "root": str(root),
        "as_of_date": as_of_date.isoformat(),
        "runtime_trade_date": runtime_trade_date.isoformat(),
        "protected_trade_dates": sorted(
            {as_of_date.isoformat(), runtime_trade_date.isoformat()}
        ),
        "mode": "apply" if apply else "dry_run",
        "purge_enabled": purge_expired,
        "purge_status": (
            "explicit_opt_in_apply"
            if purge_expired and apply
            else (
                "explicit_opt_in_dry_run"
                if purge_expired
                else "disabled_no_deletion_authority"
            )
        ),
        "purge_candidate_count": purge_candidate_count,
        "purge_candidate_bytes": purge_candidate_bytes,
        "purge_applied_count": purge_applied_count,
        "purge_partial_applied_count": purge_partial_applied_count,
        "deletion_performed": (
            purge_applied_count > 0 or purge_partial_applied_count > 0
        ),
        "status": (
            "partial_failure"
            if partition_failures or capacity_metrics["capacity_failure"] is True
            else "pass"
        ),
        "partition_failure_count": len(partition_failures),
        "partition_failures": partition_failures,
        "failed_candidate_count": sum(
            int(row.get("candidate_count") or 0) for row in partition_failures
        ),
        "failed_candidate_bytes": sum(
            int(row.get("candidate_bytes") or 0) for row in partition_failures
        ),
        "recovery_required_count": sum(
            row.get("recovery_required") == "true" for row in partition_failures
        ),
        "action_count": len(actions),
        "source_bytes": sum(row.source_bytes for row in actions),
        "actions": [asdict(row) for row in actions],
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "trading_runtime_effect": False,
        **MAINTENANCE_METRIC_CONTRACT,
        **capacity_metrics,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument(
        "--as-of-date",
        type=date.fromisoformat,
        default=datetime.now(KST).date(),
    )
    parser.add_argument("--apply", action="store_true")
    parser.add_argument(
        "--report-artifact-root",
        type=Path,
        action="append",
        default=[],
        help=(
            "Compress allowlisted closed-date micro-reversion JSON artifacts. "
            "May be repeated; never grants deletion authority."
        ),
    )
    parser.add_argument(
        "--report-artifact-retention-days",
        type=int,
        default=REPORT_ARTIFACT_DEFAULT_RETENTION_DAYS,
        help=(
            "Classify compressed audit artifacts older than this many days for "
            "retention census only; no automatic deletion is performed."
        ),
    )
    parser.add_argument(
        "--exact-ai-artifact-root",
        type=Path,
        action="append",
        default=[],
        help=(
            "Compress strict logical plain/gzip closed-date AI decision JSONL/JSON "
            "generations. May be repeated; never grants deletion authority."
        ),
    )
    parser.add_argument(
        "--micro-reversion-daily-owner-root",
        type=Path,
        help=(
            "Census exact-date policy-owner bytes and retention candidates only; "
            "automatic compression, deletion, archive, and offload remain blocked."
        ),
    )
    parser.add_argument(
        "--low-disk-watermark-bytes",
        type=int,
        default=STORAGE_LOW_DISK_WATERMARK_BYTES,
    )
    parser.add_argument(
        "--critical-disk-watermark-bytes",
        type=int,
        default=STORAGE_CRITICAL_DISK_WATERMARK_BYTES,
    )
    parser.add_argument(
        "--capacity-status-path",
        type=Path,
        help=(
            "Persist a tiny source-only capacity status/workorder artifact. "
            "Requires --apply and grants no deletion authority."
        ),
    )
    parser.add_argument(
        "--purge-expired",
        action="store_true",
        help=(
            "Explicitly authorize removal of validated trade-date partitions "
            "older than the configured retention window. Disabled by default."
        ),
    )
    parser.add_argument(
        "--purge-source-exclusions",
        type=Path,
        help=(
            "Remove only exact sequence-epoch scopes already present in the "
            "validated source exclusion manifest. Dry-run unless --apply is set."
        ),
    )
    args = parser.parse_args()
    try:
        _validate_capacity_watermarks(
            low_disk_watermark_bytes=args.low_disk_watermark_bytes,
            critical_disk_watermark_bytes=args.critical_disk_watermark_bytes,
        )
    except ValueError as exc:
        parser.error(str(exc))
    if args.capacity_status_path is not None and not args.apply:
        parser.error("--capacity-status-path requires --apply")
    if args.purge_source_exclusions is not None:
        if (
            args.purge_expired
            or args.report_artifact_root
            or args.exact_ai_artifact_root
            or args.micro_reversion_daily_owner_root is not None
            or args.capacity_status_path is not None
        ):
            parser.error(
                "--purge-source-exclusions is a separate authority and cannot "
                "be combined with partition, report artifact, or capacity status "
                "maintenance"
            )
        result = purge_excluded_forward_scopes(
            args.root,
            source_exclusion_manifest_path=args.purge_source_exclusions,
            apply=args.apply,
        )
        exit_code = 0 if result["status"] == "pass" else 1
    else:
        result = maintain_forward_storage(
            args.root,
            as_of_date=args.as_of_date,
            storage_policy=PathStoragePolicy(
                low_disk_watermark_bytes=args.low_disk_watermark_bytes,
                critical_disk_watermark_bytes=args.critical_disk_watermark_bytes,
            ),
            apply=args.apply,
            purge_expired=args.purge_expired,
        )
        if (
            args.report_artifact_root
            or args.exact_ai_artifact_root
            or args.micro_reversion_daily_owner_root is not None
        ):
            artifact_result = maintain_report_artifact_storage(
                args.report_artifact_root,
                as_of_date=args.as_of_date,
                retention_days=args.report_artifact_retention_days,
                apply=args.apply,
                exact_ai_artifact_roots=args.exact_ai_artifact_root,
                micro_reversion_daily_owner_root=(
                    args.micro_reversion_daily_owner_root
                ),
                low_disk_watermark_bytes=args.low_disk_watermark_bytes,
                critical_disk_watermark_bytes=args.critical_disk_watermark_bytes,
            )
            result["report_artifact_maintenance"] = artifact_result
            result["disk_total_bytes"] = artifact_result["disk_total_bytes"]
            result["disk_used_bytes_after"] = artifact_result["disk_used_bytes_after"]
            result["disk_free_bytes_after"] = artifact_result["disk_free_bytes_after"]
            result["disk_free_bytes_delta"] = int(
                result["disk_free_bytes_after"]
            ) - int(result["disk_free_bytes_before"])
            result["retained_physical_bytes_before"] = int(
                result["retained_physical_bytes_before"]
            ) + int(artifact_result["retained_physical_bytes_before"])
            result["retained_physical_bytes_after"] = int(
                result["retained_physical_bytes_after"]
            ) + int(artifact_result["retained_physical_bytes_after"])
            result["retained_physical_bytes_delta"] = int(
                result["retained_physical_bytes_after"]
            ) - int(result["retained_physical_bytes_before"])
            result["compressed_target_bytes"] = int(
                result["compressed_target_bytes"]
            ) + int(artifact_result["compressed_target_bytes"])
            result["bytes_reclaimed"] = max(
                0,
                int(result["retained_physical_bytes_before"])
                - int(result["retained_physical_bytes_after"]),
            )
            final_capacity_state = _capacity_state(
                int(result["disk_free_bytes_after"]),
                low_disk_watermark_bytes=args.low_disk_watermark_bytes,
                critical_disk_watermark_bytes=args.critical_disk_watermark_bytes,
            )
            result["capacity_state"] = final_capacity_state
            result["capacity_warning"] = final_capacity_state == "low_warning"
            result["capacity_failure"] = final_capacity_state == "critical"
            result["capacity_workorder_required"] = final_capacity_state != "healthy"
            result["capacity_reason_codes"] = _capacity_reason_codes(
                final_capacity_state
            )
        operation_failed = bool(result.get("partition_failure_count")) or bool(
            (result.get("report_artifact_maintenance") or {}).get("failure_count")
        )
        result["status"] = (
            "partial_failure"
            if operation_failed or result.get("capacity_failure") is True
            else "pass"
        )
        result["capacity_status_artifact_path"] = (
            str(args.capacity_status_path.absolute())
            if args.capacity_status_path is not None
            else None
        )
        result["capacity_status_written"] = False
        result["capacity_status_write_failure_count"] = 0
        result["capacity_status_write_failure_reason"] = None
        if args.capacity_status_path is not None:
            try:
                _write_capacity_status_atomic(
                    args.capacity_status_path,
                    _capacity_status_artifact(result, target_date=args.as_of_date),
                )
            except Exception as exc:
                result["capacity_status_write_failure_count"] = 1
                result["capacity_status_write_failure_reason"] = (
                    f"{type(exc).__name__}:{exc}"
                )
                result["status"] = "partial_failure"
            else:
                result["capacity_status_written"] = True
        exit_code = 0 if result["status"] == "pass" else 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
