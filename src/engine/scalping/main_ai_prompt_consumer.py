"""Close Main AI optimizer request paths with exact, source-only bindings.

The optimizer decides what should be compared.  This consumer proves where
each Entry/Holding base request and optional prompt/input factorial cell goes:
an exact connected path, an explicit blocker with owner/acceptance test, or an
existing R0-R3 duplicate.  It performs no provider call and has no runtime or
order authority.
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import tempfile
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable, Mapping

from src.engine.scalping import ai_decision_quality as quality
from src.engine.scalping import entry_setup_paired_replay_batch as entry_batch
from src.engine.scalping import main_ai_holding_base_replay_batch as holding_batch
from src.engine.scalping.micro_reversion import main_ai_prompt_optimizer as optimizer
from src.engine.scalping.micro_reversion import replay_ablation_contract as ablation

SCHEMA = "main_ai_prompt_consumer_v1"
REPORT_DIR = quality.DATA_DIR / "report" / "main_ai_prompt_consumer"

CONNECTED = "connected_and_hash_bound"
BLOCKED = "intentionally_blocked_with_owner_and_acceptance_test"
R0_DUPLICATE = "retired_as_duplicate_of_existing_r0_r3"
VALID_PATH_STATUSES = frozenset({CONNECTED, BLOCKED, R0_DUPLICATE})

SOURCE_ONLY_CONTRACT = {
    "metric_role": "main_ai_prompt_and_input_consumer_closure",
    "decision_authority": "postclose_source_only_request_routing",
    "window_policy": "exact_date_stage_venue_session_and_exact_hash",
    "sample_floor": "all_discovered_request_paths_must_have_one_terminal_routing_state",
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "source_quality_gate": "clean_baseline_exact_payload_hash_and_cohort_isolation",
    "provider_call_performed": False,
    "runtime_effect": False,
    "runtime_authority": False,
    "order_authority": False,
    "provider_authority": False,
    "allowed_runtime_apply": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
    "forbidden_uses": [
        "provider_call_from_consumer_report",
        "runtime_prompt_or_provider_route_change",
        "cross_stage_or_cross_cohort_evidence_pooling",
        "threshold_price_quantity_cap_or_order_change",
        "broker_or_hard_safety_guard_bypass",
        "bot_restart",
    ],
}


def report_paths(target_date: str) -> tuple[Path, Path]:
    base = REPORT_DIR / f"main_ai_prompt_consumer_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def _read_json(path: Path) -> dict[str, Any]:
    candidates = [
        candidate
        for candidate in (path, path.with_name(f"{path.name}.gz"))
        if candidate.exists() or candidate.is_symlink()
    ]
    payloads: list[dict[str, Any]] = []
    for candidate in candidates:
        try:
            if candidate.suffix == ".gz":
                with gzip.open(candidate, "rt", encoding="utf-8") as stream:
                    payload = json.load(stream)
            else:
                payload = json.loads(candidate.read_text(encoding="utf-8"))
        except (FileNotFoundError, OSError, json.JSONDecodeError):
            return {}
        if isinstance(payload, dict):
            payloads.append(payload)
        else:
            return {}
    if not payloads or any(payload != payloads[0] for payload in payloads[1:]):
        return {}
    return payloads[0]


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(
                dict(payload),
                stream,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
                allow_nan=False,
            )
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _valid_source_only(payload: Mapping[str, Any]) -> bool:
    return bool(
        payload.get("runtime_effect") is False
        and payload.get("allowed_runtime_apply") is False
        and payload.get("actual_order_submitted") is False
        and payload.get("broker_order_forbidden") is True
        and payload.get("runtime_authority") is not True
        and payload.get("order_authority") is not True
        and payload.get("provider_authority") is not True
    )


def _valid_self_hash(payload: Mapping[str, Any]) -> bool:
    declared = str(payload.get("artifact_content_sha256") or "")
    content = {
        key: value
        for key, value in payload.items()
        if key != "artifact_content_sha256"
    }
    return bool(declared and optimizer._canonical_sha256(content) == declared)


def _cohort_key(value: Mapping[str, Any]) -> tuple[str, str]:
    return (
        str(value.get("effective_venue") or "").upper(),
        str(value.get("session_bucket") or "").upper(),
    )


def _blocked(
    *, reason: str, owner: str, acceptance_test: str, **extra: Any
) -> dict[str, Any]:
    return {
        "path_status": BLOCKED,
        "blocking_reason": reason,
        "owner": owner,
        "acceptance_test": acceptance_test,
        "terminality": "requires_retry_or_owner_closure",
        **extra,
    }


def _desired_prompt_identity(
    *, stage: str, cohort: Mapping[str, Any]
) -> tuple[str, str]:
    selected = cohort.get("selected_challenger")
    selected = selected if isinstance(selected, Mapping) else {}
    version = str(selected.get("prompt_version") or "")
    if stage == "entry":
        return version, optimizer.ENTRY_CANDIDATE_PROMPT_SHA256.get(version, "")
    legacy = cohort.get("legacy_r0_challenger")
    legacy = legacy if isinstance(legacy, Mapping) else {}
    if version == str(legacy.get("prompt_version") or ""):
        return version, str(legacy.get("prompt_sha256") or "")
    return version, ""


def _entry_base_paths(
    target_date: str,
    *,
    optimizer_report: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], dict[tuple[str, str, str], dict[str, Any]]]:
    batch_path = entry_batch.batch_status_path(target_date)
    batch = _read_json(batch_path)
    optimizer_sha = str(optimizer_report.get("artifact_content_sha256") or "")
    batch_source = batch.get("candidate_prompt_selection_source")
    batch_source = batch_source if isinstance(batch_source, Mapping) else {}
    source_bound = bool(
        batch_source.get("status")
        == "optimizer_candidate_plan_applied_offline_only"
        and batch_source.get("artifact_content_sha256") == optimizer_sha
    )
    batch_cohorts = {
        _cohort_key(row): row
        for row in batch.get("cohorts") or []
        if isinstance(row, Mapping)
    }
    declared_plan = batch.get("candidate_prompt_versions_by_cohort")
    declared_plan = declared_plan if isinstance(declared_plan, Mapping) else {}
    paths: list[dict[str, Any]] = []
    request_index: dict[tuple[str, str, str], dict[str, Any]] = {}
    entry_optimizer = (
        (optimizer_report.get("stage_optimizers") or {}).get("entry") or {}
    )
    for cohort in entry_optimizer.get("cohort_optimizers") or []:
        if not isinstance(cohort, Mapping):
            continue
        venue, session = _cohort_key(cohort)
        version, prompt_sha = _desired_prompt_identity(stage="entry", cohort=cohort)
        row: dict[str, Any] = {
            "stage": "entry",
            "effective_venue": venue,
            "session_bucket": session,
            "selected_prompt_version": version,
            "selected_prompt_sha256": prompt_sha or None,
            "batch_path": str(batch_path),
        }
        batch_cohort = batch_cohorts.get((venue, session))
        if (
            batch.get("schema") != entry_batch.BATCH_SCHEMA
            or batch.get("target_date") != target_date
            or not _valid_source_only(batch)
        ):
            row.update(
                _blocked(
                    reason="entry_batch_missing_or_invalid",
                    owner="AIEntrySetupPairedReplayBatch",
                    acceptance_test="produce an exact-date source-only terminal batch",
                )
            )
            paths.append(row)
            continue
        if not source_bound:
            row.update(
                _blocked(
                    reason="entry_batch_optimizer_hash_binding_missing",
                    owner="AIEntrySetupPairedReplayBatch",
                    acceptance_test=(
                        "batch candidate selection must bind the exact optimizer "
                        "artifact_content_sha256"
                    ),
                )
            )
            paths.append(row)
            continue
        declared_version = str(declared_plan.get(f"{venue}/{session}") or "")
        if (
            isinstance(batch_cohort, Mapping)
            and batch_cohort.get("status")
            in {"hold_no_exact_entry_control", "hold_no_mature_exact_request"}
            and declared_version == version
            and str(batch_cohort.get("candidate_prompt_version") or "") == version
        ):
            row.update(
                _blocked(
                    reason=str(batch_cohort.get("status")),
                    owner="AIEntrySetupPairedReplayBatch",
                    acceptance_test=(
                        "retain the exact target-date no-sample observation and "
                        "wait for a future natural cohort"
                    ),
                    terminality="terminal_source_observation",
                )
            )
            paths.append(row)
            continue
        if (
            not isinstance(batch_cohort, Mapping)
            or declared_version != version
            or str(batch_cohort.get("candidate_prompt_version") or "") != version
        ):
            row.update(
                _blocked(
                    reason="entry_batch_selected_prompt_mismatch",
                    owner="AIEntrySetupPairedReplayBatch",
                    acceptance_test=(
                        "batch and cohort prompt versions must equal the optimizer "
                        "selection for the same venue/session"
                    ),
                )
            )
            paths.append(row)
            continue
        detailed_path = Path(str(batch_cohort.get("report_path") or ""))
        expected_detailed_path = quality.detailed_paired_path(
            target_date,
            candidate_prompt_version=version,
            effective_venue=venue,
            session_bucket=session,
        )
        if (
            not detailed_path.is_absolute()
            or detailed_path.resolve() != expected_detailed_path.resolve()
        ):
            row.update(
                _blocked(
                    reason="entry_detailed_report_path_not_canonical",
                    owner="AIEntrySetupPairedReplayBatch",
                    acceptance_test=(
                        "batch cohort must reference the canonical exact-date, "
                        "prompt, venue, and session detailed report path"
                    ),
                )
            )
            paths.append(row)
            continue
        detailed = _read_json(detailed_path)
        requests = [
            request
            for request in detailed.get("requests") or []
            if isinstance(request, Mapping)
        ]
        observed_versions = {
            str(((request.get("candidate") or {}).get("prompt_version") or ""))
            .removesuffix("_entry")
            for request in requests
        }
        observed_hashes = {
            str((request.get("candidate") or {}).get("system_prompt_sha256") or "")
            for request in requests
        }
        observed_input_hashes_valid = bool(requests) and all(
            request.get("decision_trace_id")
            and request.get("payload_sha256")
            and request.get("candidate_input_sha256")
            and (request.get("candidate") or {}).get("contract_sha256")
            for request in requests
        )
        if (
            detailed.get("schema") != "ai_prompt_detailed_paired_replay_v1"
            or detailed.get("target_date") != target_date
            or not _valid_source_only(detailed)
            or observed_versions != {version}
            or observed_hashes != {prompt_sha}
            or not observed_input_hashes_valid
        ):
            row.update(
                _blocked(
                    reason="entry_detailed_request_hash_binding_invalid",
                    owner="AIEntrySetupPairedReplayBatch",
                    acceptance_test=(
                        "all detailed requests must preserve the selected prompt, "
                        "payload, input, and candidate contract hashes"
                    ),
                    detailed_report_path=str(detailed_path),
                )
            )
            paths.append(row)
            continue
        row.update(
            {
                "path_status": CONNECTED,
                "blocking_reason": None,
                "owner": "AIEntrySetupPairedReplayBatch",
                "acceptance_test": "passed_optimizer_to_detailed_exact_hash_binding",
                "detailed_report_path": str(detailed_path),
                "request_count": len(requests),
                "request_trace_ids_sha256": optimizer._canonical_sha256(
                    sorted(str(request.get("decision_trace_id")) for request in requests)
                ),
            }
        )
        for request in requests:
            trace_id = str(request.get("decision_trace_id") or "")
            request_index[(venue, session, trace_id)] = dict(request)
        paths.append(row)
    return paths, request_index


def _holding_base_paths(
    target_date: str,
    *,
    optimizer_report: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], dict[tuple[str, str, str], dict[str, Any]]]:
    path = holding_batch.report_path(target_date)
    batch = _read_json(path)
    valid_batch = bool(
        batch.get("schema") == holding_batch.SCHEMA
        and batch.get("target_date") == target_date
        and batch.get("status") == "ready_source_only_holding_base_manifest"
        and _valid_source_only(batch)
        and _valid_self_hash(batch)
        and (batch.get("source_bindings") or {}).get(
            "optimizer_artifact_content_sha256"
        )
        == optimizer_report.get("artifact_content_sha256")
    )
    batch_cohorts = {
        _cohort_key(row): row
        for row in batch.get("cohorts") or []
        if isinstance(row, Mapping)
    }
    paths: list[dict[str, Any]] = []
    request_index: dict[tuple[str, str, str], dict[str, Any]] = {}
    holding_optimizer = (
        (optimizer_report.get("stage_optimizers") or {}).get("holding") or {}
    )
    for cohort in holding_optimizer.get("cohort_optimizers") or []:
        if not isinstance(cohort, Mapping):
            continue
        venue, session = _cohort_key(cohort)
        version, prompt_sha = _desired_prompt_identity(stage="holding", cohort=cohort)
        row: dict[str, Any] = {
            "stage": "holding",
            "effective_venue": venue,
            "session_bucket": session,
            "selected_prompt_version": version,
            "selected_prompt_sha256": prompt_sha or None,
            "batch_path": str(path),
        }
        batch_cohort = batch_cohorts.get((venue, session))
        if not valid_batch or not isinstance(batch_cohort, Mapping):
            row.update(
                _blocked(
                    reason="holding_base_manifest_missing_or_invalid",
                    owner="MainAIHoldingBaseReplayConsumer",
                    acceptance_test=(
                        "generate the exact-date Holding manifest after the optimizer"
                    ),
                )
            )
            paths.append(row)
            continue
        if batch_cohort.get("path_status") != CONNECTED:
            row.update(
                _blocked(
                    reason=str(
                        batch_cohort.get("blocking_reason")
                        or "holding_cohort_not_connected"
                    ),
                    owner=str(
                        batch_cohort.get("owner")
                        or "MainAIHoldingBaseReplayConsumer"
                    ),
                    acceptance_test=str(
                        batch_cohort.get("acceptance_test")
                        or "pass exact Holding cohort hash binding"
                    ),
                )
            )
            paths.append(row)
            continue
        requests = [
            request
            for request in batch_cohort.get("requests") or []
            if isinstance(request, Mapping)
        ]
        request_trace_ids = [
            str(request.get("decision_trace_id") or "") for request in requests
        ]
        if (
            batch_cohort.get("selected_prompt_version") != version
            or batch_cohort.get("selected_prompt_sha256") != prompt_sha
            or not requests
            or batch_cohort.get("request_count") != len(requests)
            or batch_cohort.get("optimizer_exact_parent_count") != len(requests)
            or len(request_trace_ids) != len(set(request_trace_ids))
            or any(
                request.get("candidate_prompt_version") != version
                or request.get("candidate_prompt_sha256") != prompt_sha
                or not request.get("candidate_input_sha256")
                or not request.get("candidate_contract_sha256")
                for request in requests
            )
        ):
            row.update(
                _blocked(
                    reason="holding_manifest_optimizer_or_request_hash_mismatch",
                    owner="MainAIHoldingBaseReplayConsumer",
                    acceptance_test=(
                        "optimizer and every Holding request fingerprint must share "
                        "the exact selected prompt and input contract hashes"
                    ),
                )
            )
            paths.append(row)
            continue
        row.update(
            {
                "path_status": CONNECTED,
                "blocking_reason": None,
                "owner": "MainAIHoldingBaseReplayConsumer",
                "acceptance_test": "passed_optimizer_to_holding_manifest_hash_binding",
                "request_count": len(requests),
                "provider_execution_state": batch_cohort.get(
                    "provider_execution_state"
                ),
            }
        )
        for request in requests:
            trace_id = str(request.get("decision_trace_id") or "")
            request_index[(venue, session, trace_id)] = dict(request)
        paths.append(row)
    return paths, request_index


def _request_prompt_identity(request: Mapping[str, Any]) -> tuple[str, str]:
    candidate = request.get("candidate")
    candidate = candidate if isinstance(candidate, Mapping) else {}
    return (
        str(candidate.get("prompt_version") or "").removesuffix("_entry"),
        str(candidate.get("system_prompt_sha256") or ""),
    )


def _base_request_input_sha(request: Mapping[str, Any]) -> str:
    return str(
        request.get("candidate_input_sha256")
        or request.get("candidate_input_hash")
        or ""
    )


def _factorial_cells(
    *,
    optimizer_report: Mapping[str, Any],
    prepared: Mapping[str, Any],
    bridge: Mapping[str, Any],
    materialized: Mapping[str, Any],
    execution: Mapping[str, Any],
    entry_request_index: Mapping[tuple[str, str, str], Mapping[str, Any]],
    holding_request_index: Mapping[tuple[str, str, str], Mapping[str, Any]],
) -> list[dict[str, Any]]:
    prepared_rows = [
        row
        for row in prepared.get("prepared_requests") or []
        if isinstance(row, Mapping)
    ]
    enriched = optimizer._enriched_trace_ids_by_stage(bridge)
    materialized_by_trace: dict[str, dict[str, Mapping[str, Any]]] = defaultdict(dict)
    for request in materialized.get("requests") or []:
        if not isinstance(request, Mapping):
            continue
        trace_id = str(request.get("decision_trace_id") or "")
        arm = str(request.get("micro_reversion_replay_arm") or "")
        if trace_id and arm:
            materialized_by_trace[trace_id][arm] = request
    passed_ids = {
        str(row.get("paired_replay_id") or "")
        for row in execution.get("results") or []
        if isinstance(row, Mapping) and row.get("status") == "pass"
    }

    cells: list[dict[str, Any]] = []
    stage_optimizers = optimizer_report.get("stage_optimizers") or {}
    for stage in ("entry", "holding"):
        stage_optimizer = stage_optimizers.get(stage) or {}
        base_index = (
            entry_request_index if stage == "entry" else holding_request_index
        )
        for cohort in stage_optimizer.get("cohort_optimizers") or []:
            if not isinstance(cohort, Mapping):
                continue
            venue, session = _cohort_key(cohort)
            selected_version, selected_sha = _desired_prompt_identity(
                stage=stage, cohort=cohort
            )
            champion = cohort.get("champion")
            champion = champion if isinstance(champion, Mapping) else {}
            champion_version = str(champion.get("prompt_version") or "")
            champion_sha = str(champion.get("prompt_sha256") or "")
            cohort_trace_ids = {
                str(row.get("decision_trace_id") or "")
                for row in prepared_rows
                if str(row.get("stage") or "").lower() == stage
                and str(row.get("effective_venue") or "").upper() == venue
                and str(row.get("session_bucket") or "").upper() == session
                and row.get("decision_trace_id")
            }
            for trace_id in sorted(cohort_trace_ids & enriched.get(stage, set())):
                r0 = materialized_by_trace.get(trace_id, {})
                p0d0 = r0.get(ablation.CURRENT_BASE_CONTROL_ARM)
                p0d0_input_sha = _base_request_input_sha(p0d0 or {})
                arm_specs = (
                    (
                        "P0D0_champion_base_input",
                        ablation.CURRENT_BASE_CONTROL_ARM,
                        champion_version,
                        champion_sha,
                    ),
                    (
                        "P0D1_champion_enriched_micro_input",
                        ablation.CURRENT_ASK_CONTROL_ARM,
                        champion_version,
                        champion_sha,
                    ),
                    (
                        "P1D1_challenger_enriched_micro_input",
                        ablation.CURRENT_ASK_CANDIDATE_ARM,
                        selected_version,
                        selected_sha,
                    ),
                )
                for cell_name, arm, expected_version, expected_sha in arm_specs:
                    request = r0.get(arm)
                    common = {
                        "stage": stage,
                        "effective_venue": venue,
                        "session_bucket": session,
                        "decision_trace_id": trace_id,
                        "cell": cell_name,
                        "expected_prompt_version": expected_version,
                        "expected_prompt_sha256": expected_sha or None,
                        "existing_owner": "main_ai_quality_r0_r3",
                    }
                    if request is None:
                        cells.append(
                            {
                                **common,
                                **_blocked(
                                    reason="r0_r3_parent_not_materialized",
                                    owner="MainAIQualityR0R3Materializer",
                                    acceptance_test=(
                                        "materialize the exact common parent only "
                                        "after the existing R0 provider floor passes"
                                    ),
                                ),
                                "execution_state": "not_materialized",
                            }
                        )
                        continue
                    observed_version, observed_sha = _request_prompt_identity(request)
                    request_id = str(request.get("paired_replay_id") or "")
                    if (
                        not expected_version
                        or not expected_sha
                        or observed_version != expected_version
                        or observed_sha != expected_sha
                        or not _base_request_input_sha(request)
                    ):
                        cells.append(
                            {
                                **common,
                                **_blocked(
                                    reason="existing_r0_r3_cell_prompt_or_input_mismatch",
                                    owner="MainAIQualityR0R3Materializer",
                                    acceptance_test=(
                                        "re-materialize a new immutable generation "
                                        "whose prompt/input hashes equal the optimizer"
                                    ),
                                ),
                                "observed_prompt_version": observed_version,
                                "observed_prompt_sha256": observed_sha or None,
                                "request_id": request_id,
                                "execution_state": (
                                    "pass_reusable"
                                    if request_id in passed_ids
                                    else "existing_r0_r3_pending"
                                ),
                            }
                        )
                        continue
                    cells.append(
                        {
                            **common,
                            "path_status": R0_DUPLICATE,
                            "blocking_reason": None,
                            "owner": "MainAIQualityR0R3Materializer",
                            "acceptance_test": "passed_exact_existing_r0_r3_cell_binding",
                            "request_id": request_id,
                            "candidate_input_sha256": _base_request_input_sha(request),
                            "execution_state": (
                                "pass_reusable"
                                if request_id in passed_ids
                                else "existing_r0_r3_pending"
                            ),
                        }
                    )

                base_request = base_index.get((venue, session, trace_id))
                base_common = {
                    "stage": stage,
                    "effective_venue": venue,
                    "session_bucket": session,
                    "decision_trace_id": trace_id,
                    "cell": "P1D0_challenger_base_input",
                    "expected_prompt_version": selected_version,
                    "expected_prompt_sha256": selected_sha or None,
                    "existing_owner": (
                        "ai_entry_setup_paired_replay_batch"
                        if stage == "entry"
                        else "main_ai_holding_base_replay_batch"
                    ),
                }
                if base_request is None:
                    cells.append(
                        {
                            **base_common,
                            **_blocked(
                                reason="challenger_base_cell_not_prepared",
                                owner=(
                                    "AIEntrySetupPairedReplayBatch"
                                    if stage == "entry"
                                    else "MainAIHoldingBaseReplayConsumer"
                                ),
                                acceptance_test=(
                                    "prepare the selected challenger on the exact "
                                    "same P0D0 input hash for this common parent"
                                ),
                            ),
                            "execution_state": "not_prepared",
                        }
                    )
                    continue
                if stage == "entry":
                    base_version, base_prompt_sha = _request_prompt_identity(base_request)
                else:
                    base_version = str(
                        base_request.get("candidate_prompt_version") or ""
                    )
                    base_prompt_sha = str(
                        base_request.get("candidate_prompt_sha256") or ""
                    )
                base_input_sha = _base_request_input_sha(base_request)
                if (
                    base_version != selected_version
                    or base_prompt_sha != selected_sha
                    or not p0d0_input_sha
                    or base_input_sha != p0d0_input_sha
                ):
                    cells.append(
                        {
                            **base_common,
                            **_blocked(
                                reason="challenger_base_cell_exact_input_mismatch",
                                owner=(
                                    "AIEntrySetupPairedReplayBatch"
                                    if stage == "entry"
                                    else "MainAIHoldingBaseReplayConsumer"
                                ),
                                acceptance_test=(
                                    "P1D0 must use the exact P0D0 input SHA and the "
                                    "optimizer-selected challenger prompt SHA"
                                ),
                            ),
                            "observed_prompt_version": base_version,
                            "observed_prompt_sha256": base_prompt_sha or None,
                            "observed_input_sha256": base_input_sha or None,
                            "expected_input_sha256": p0d0_input_sha or None,
                            "execution_state": (
                                "existing_base_result_or_manifest_not_causally_reusable"
                            ),
                        }
                    )
                    continue
                cells.append(
                    {
                        **base_common,
                        "path_status": CONNECTED,
                        "blocking_reason": None,
                        "owner": base_common["existing_owner"],
                        "acceptance_test": "passed_exact_p1d0_prompt_and_input_binding",
                        "candidate_input_sha256": base_input_sha,
                        "execution_state": (
                            "existing_entry_result_reusable"
                            if stage == "entry"
                            else "provider_execution_budget_checkpoint_pending"
                        ),
                    }
                )
    return cells


def _render_markdown(report: Mapping[str, Any]) -> str:
    paths = report.get("request_paths") or {}
    factorial = paths.get("optional_micro_enriched_2x2") or {}
    status_counts = factorial.get("cell_path_status_counts") or {}
    evidence = report.get("performance_evidence") or {}
    lines = [
        f"# Main AI Prompt Consumer - {report.get('target_date')}",
        "",
        "## Decision",
        f"- status: `{report.get('status')}`",
        f"- decision: `{report.get('decision')}`",
        f"- unclassified_request_path_count: `{report.get('unclassified_request_path_count')}`",
        f"- entry_followup_terminal_ready: `{report.get('entry_followup_terminal_ready')}`",
        f"- runtime_prompt_update_allowed: `{evidence.get('runtime_prompt_update_allowed')}`",
        f"- profit_improvement_demonstrated: `{evidence.get('profit_improvement_demonstrated')}`",
        f"- future_profit_improving_output_likelihood: `{evidence.get('future_profit_improving_output_likelihood')}`",
        "",
        "## Base Consumers",
    ]
    for name in ("entry_base", "holding_base"):
        path = paths.get(name) or {}
        lines.append(
            f"- `{name}`: connected=`{path.get('connected_count')}`, "
            f"blocked=`{path.get('intentionally_blocked_count')}`"
        )
        for row in path.get("cohorts") or []:
            lines.append(
                f"  - `{row.get('effective_venue')}/{row.get('session_bucket')}` "
                f"status=`{row.get('path_status')}` reason=`{row.get('blocking_reason')}`"
            )
    lines.extend(
        [
            "",
            "## Optional 2x2 Prompt/Input Cells",
            f"- cell_count: `{factorial.get('cell_count')}`",
            f"- status_counts: `{status_counts}`",
            "- Existing exact R0-R3 cells are routed as duplicates; they are not queued by this consumer.",
            "",
            "## Runtime Guard",
            "- Runtime prompt update remains blocked until isolated 5/10/20-day EV, net-profit, p10-tail, HELD, and post-apply guards pass.",
        ]
    )
    return "\n".join(lines) + "\n"


def _path_summary(cohorts: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    rows = [dict(row) for row in cohorts]
    counts = Counter(str(row.get("path_status") or "") for row in rows)
    blocked_count = counts.get(BLOCKED, 0)
    return {
        "path_status": BLOCKED if blocked_count else CONNECTED,
        "blocking_reason": (
            "one_or_more_cohort_paths_intentionally_blocked"
            if blocked_count
            else None
        ),
        "owner": "MainAIPromptConsumer",
        "acceptance_test": (
            "every cohort reaches connected_and_hash_bound or remains explicitly "
            "blocked with its own owner and acceptance test"
        ),
        "cohorts": rows,
        "connected_count": counts.get(CONNECTED, 0),
        "intentionally_blocked_count": blocked_count,
        "retired_duplicate_count": counts.get(R0_DUPLICATE, 0),
    }


def build_report(target_date: str, *, write: bool = False) -> dict[str, Any]:
    parsed_date = date.fromisoformat(target_date)
    if parsed_date < optimizer.CLEAN_BASELINE_DATE:
        raise ValueError("target_date_before_clean_tuning_baseline")

    optimizer_path, _ = optimizer.report_paths(target_date)
    optimizer_report = _read_json(optimizer_path)
    prepared_path = quality.micro_reversion_prepared_request_path(target_date)
    bridge_path = quality.micro_reversion_bridge_report_path(target_date)
    materialized_path = quality.micro_reversion_materialized_request_path(target_date)
    execution_path = quality.micro_reversion_execution_result_path(target_date)
    prepared = _read_json(prepared_path)
    bridge = _read_json(bridge_path)
    materialized = _read_json(materialized_path)
    execution = _read_json(execution_path)
    blockers: list[str] = []
    if not (
        optimizer_report.get("schema") == optimizer.SCHEMA
        and optimizer_report.get("target_date") == target_date
        and optimizer_report.get("status") == "ready_source_only_continuous_search"
        and _valid_source_only(optimizer_report)
        and _valid_self_hash(optimizer_report)
    ):
        blockers.append("optimizer_artifact_missing_or_invalid")
    if not (
        prepared.get("schema") == "main_ai_quality_micro_prepared_requests_v1"
        and prepared.get("target_date") == target_date
        and prepared.get("status") == "prepared_requests_ready"
        and optimizer._embedded_content_sha256_valid(
            prepared, "artifact_content_sha256"
        )
        and _valid_source_only(prepared)
    ):
        blockers.append("prepared_request_artifact_missing_or_invalid")
    if not (
        bridge.get("schema") == "micro_reversion_ai_quality_bridge_v1"
        and bridge.get("target_date") == target_date
        and bridge.get("status") == "pass"
        and _valid_source_only(bridge)
    ):
        blockers.append("micro_bridge_artifact_missing_or_invalid")
    optimizer_sources = optimizer_report.get("source_bindings")
    optimizer_sources = (
        optimizer_sources if isinstance(optimizer_sources, Mapping) else {}
    )
    if prepared and optimizer_sources.get("prepared_request_sha256") != (
        optimizer._canonical_sha256(prepared)
    ):
        blockers.append("optimizer_prepared_request_hash_binding_mismatch")
    if bridge and optimizer_sources.get("micro_bridge_sha256") != (
        optimizer._canonical_sha256(bridge)
    ):
        blockers.append("optimizer_micro_bridge_hash_binding_mismatch")
    if materialized and not (
        materialized.get("schema") == quality.MICRO_REVERSION_MATERIALIZED_REQUEST_SCHEMA
        and materialized.get("target_date") == target_date
        and _valid_source_only(materialized)
        and materialized.get("provider_call_performed") is False
    ):
        blockers.append("r0_r3_materialized_artifact_invalid")
    if materialized and "r0_r3_materialized_artifact_invalid" not in blockers:
        try:
            quality._validate_micro_reversion_materialized_report(materialized)
        except (TypeError, ValueError):
            blockers.append("r0_r3_materialized_deep_contract_invalid")
    if execution and not (
        execution.get("schema") == quality.MICRO_REVERSION_EXECUTION_RESULT_SCHEMA
        and execution.get("target_date") == target_date
        and _valid_source_only(execution)
        and execution.get("report_content_sha256")
        == quality._sha256(
            {
                key: value
                for key, value in execution.items()
                if key != "report_content_sha256"
            }
        )
    ):
        blockers.append("r0_r3_execution_artifact_invalid")

    entry_paths: list[dict[str, Any]] = []
    holding_paths: list[dict[str, Any]] = []
    entry_index: dict[tuple[str, str, str], dict[str, Any]] = {}
    holding_index: dict[tuple[str, str, str], dict[str, Any]] = {}
    cells: list[dict[str, Any]] = []
    if not blockers:
        entry_paths, entry_index = _entry_base_paths(
            target_date, optimizer_report=optimizer_report
        )
        holding_paths, holding_index = _holding_base_paths(
            target_date, optimizer_report=optimizer_report
        )
        cells = _factorial_cells(
            optimizer_report=optimizer_report,
            prepared=prepared,
            bridge=bridge,
            materialized=materialized,
            execution=execution,
            entry_request_index=entry_index,
            holding_request_index=holding_index,
        )

    all_terminal_rows: list[Mapping[str, Any]] = [
        *entry_paths,
        *holding_paths,
        *cells,
    ]
    unclassified = sum(
        str(row.get("path_status") or "") not in VALID_PATH_STATUSES
        for row in all_terminal_rows
    )
    terminal_contract_invalid_count = sum(
        not row.get("owner")
        or not row.get("acceptance_test")
        or (
            row.get("path_status") == BLOCKED
            and not row.get("blocking_reason")
        )
        for row in all_terminal_rows
    )
    if unclassified:
        blockers.append("unclassified_request_path")
    if terminal_contract_invalid_count:
        blockers.append("terminal_request_path_contract_invalid")
    cell_counts = Counter(str(row.get("path_status") or "") for row in cells)
    optimizer_feasibility = optimizer_report.get("result_feasibility") or {}
    profit_demonstrated = bool(
        optimizer_feasibility.get(
            "profit_improving_candidate_currently_demonstrated"
        )
    )
    connected_entry_count = sum(
        row.get("path_status") == CONNECTED for row in entry_paths
    )
    connected_holding_manifest_count = sum(
        row.get("path_status") == CONNECTED for row in holding_paths
    )
    holding_provider_ready_count = sum(
        row.get("path_status") == CONNECTED
        and row.get("provider_execution_state")
        not in {None, "blocked_pending_shared_budget_checkpoint_consumer"}
        for row in holding_paths
    )
    entry_followup_terminal_ready = bool(entry_paths) and all(
        row.get("path_status") == CONNECTED
        or (
            row.get("path_status") == BLOCKED
            and row.get("terminality") == "terminal_source_observation"
        )
        for row in entry_paths
    )
    body: dict[str, Any] = {
        "schema": SCHEMA,
        "target_date": target_date,
        "generated_at": datetime.now(quality.KST).isoformat(timespec="seconds"),
        "status": (
            "blocked_source_contract"
            if blockers
            else "ready_source_only_consumer_closure"
        ),
        "decision": (
            "all_main_ai_request_paths_classified_runtime_update_still_blocked"
            if not blockers
            else "main_ai_consumer_closure_blocked_source_contract"
        ),
        "source_bindings": {
            "optimizer_path": str(optimizer_path),
            "optimizer_artifact_content_sha256": optimizer_report.get(
                "artifact_content_sha256"
            ),
            "prepared_request_path": str(prepared_path),
            "prepared_request_artifact_content_sha256": prepared.get(
                "artifact_content_sha256"
            ),
            "micro_bridge_path": str(bridge_path),
            "micro_bridge_canonical_sha256": (
                optimizer._canonical_sha256(bridge) if bridge else None
            ),
            "r0_r3_materialized_path": str(materialized_path),
            "r0_r3_materialized_canonical_sha256": (
                optimizer._canonical_sha256(materialized) if materialized else None
            ),
            "r0_r3_execution_path": str(execution_path),
            "r0_r3_execution_canonical_sha256": (
                optimizer._canonical_sha256(execution) if execution else None
            ),
        },
        "request_paths": {
            "entry_base": _path_summary(entry_paths),
            "holding_base": _path_summary(holding_paths),
            "optional_micro_enriched_2x2": {
                "path_status": BLOCKED if cell_counts.get(BLOCKED, 0) else CONNECTED,
                "blocking_reason": (
                    "one_or_more_factorial_cells_intentionally_blocked"
                    if cell_counts.get(BLOCKED, 0)
                    else None
                ),
                "owner": "MainAIPromptFactorialCellRouter",
                "acceptance_test": (
                    "every cell is exact-hash connected, explicitly blocked, or "
                    "retired as an existing R0-R3 duplicate"
                ),
                "design_version": optimizer.FACTORIAL_DESIGN_VERSION,
                "cell_count": len(cells),
                "cell_path_status_counts": dict(sorted(cell_counts.items())),
                "cells_sha256": optimizer._canonical_sha256(cells),
                "cells": cells,
                "provider_execution_policy": (
                    "existing R0-R3 exact cells are never queued here; only an "
                    "exact missing/changed cell may proceed after its owner and "
                    "shared budget/checkpoint acceptance test close"
                ),
            },
        },
        "path_status_contract": sorted(VALID_PATH_STATUSES),
        "unclassified_request_path_count": unclassified,
        "terminal_request_path_contract_invalid_count": (
            terminal_contract_invalid_count
        ),
        "entry_followup_terminal_ready": entry_followup_terminal_ready,
        "blockers": sorted(set(blockers)),
        "performance_evidence": {
            "connected_entry_result_cohort_count": connected_entry_count,
            "connected_holding_manifest_cohort_count": (
                connected_holding_manifest_count
            ),
            "holding_provider_ready_cohort_count": holding_provider_ready_count,
            "all_requested_evaluation_results_generation_ready": bool(
                connected_entry_count
                and holding_provider_ready_count == len(holding_paths)
                and cell_counts.get(BLOCKED, 0) == 0
            ),
            "profit_improvement_demonstrated": profit_demonstrated,
            "runtime_prompt_update_allowed": False,
            "runtime_prompt_update_blockers": [
                "isolated_5d_ev_and_net_profit_guard_not_closed",
                "isolated_10d_ev_and_net_profit_guard_not_closed",
                "isolated_20d_ev_and_net_profit_guard_not_closed",
                "p10_tail_guard_not_closed",
                "held_and_post_apply_attribution_guard_not_closed",
                "new_prompt_live_family_not_registered",
            ],
            "future_profit_improving_output_likelihood": (
                "evidence_supported"
                if profit_demonstrated
                else (
                    "partial_entry_only_plausible_holding_and_factorial_provider_blocked"
                    if connected_entry_count
                    else (
                        "blocked_pending_entry_hash_refresh_and_holding_provider_checkpoint"
                    )
                )
            ),
            "interpretation": (
                "Request generation and duplicate suppression are now testable. "
                "Holding and missing factorial result generation remain blocked by "
                "the shared provider-budget/checkpoint acceptance test, and "
                "profitability remains unproven until mature economic outcomes "
                "close every rolling and tail-risk guard."
            ),
        },
        **SOURCE_ONLY_CONTRACT,
    }
    report = {**body, "artifact_content_sha256": optimizer._canonical_sha256(body)}
    if write:
        json_path, markdown_path = report_paths(target_date)
        _atomic_write_json(json_path, report)
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(_render_markdown(report), encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-date", required=True)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--print-summary", action="store_true")
    parser.add_argument(
        "--require-entry-terminal",
        action="store_true",
        help=(
            "Return non-zero until every Entry cohort is exact-hash connected or "
            "a terminal no-source observation."
        ),
    )
    args = parser.parse_args(argv)
    report = build_report(args.target_date, write=args.write)
    if args.print_summary:
        evidence = report["performance_evidence"]
        print(
            json.dumps(
                {
                    "target_date": report["target_date"],
                    "status": report["status"],
                    "unclassified_request_path_count": report[
                        "unclassified_request_path_count"
                    ],
                    "entry_followup_terminal_ready": report[
                        "entry_followup_terminal_ready"
                    ],
                    "profit_improvement_demonstrated": evidence[
                        "profit_improvement_demonstrated"
                    ],
                    "future_profit_improving_output_likelihood": evidence[
                        "future_profit_improving_output_likelihood"
                    ],
                },
                ensure_ascii=False,
            )
        )
    if report["status"] == "blocked_source_contract":
        return 2
    if args.require_entry_terminal and not report["entry_followup_terminal_ready"]:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
