"""Build the hash-bound Holding base-prompt replay manifest.

This producer consumes the stage/cohort selection emitted by the Main AI
prompt optimizer and freezes only exact Holding requests.  It deliberately
does not call a model provider: provider execution remains behind the shared
budget/checkpoint gate and the resulting report has no runtime authority.
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from datetime import date, datetime
from pathlib import Path
from typing import Any, Mapping

from src.engine.ai_prompt_contracts import (
    DECISION_QUALITY_HOLDING_V2_3_PROMPT_VERSION,
)
from src.engine.scalping import ai_decision_quality as quality
from src.engine.scalping import ai_stage_coverage_replay as coverage
from src.engine.scalping.micro_reversion import main_ai_prompt_optimizer as optimizer

SCHEMA = "main_ai_holding_base_replay_batch_v1"
REPORT_DIR = quality.DATA_DIR / "report" / "main_ai_holding_base_replay_batch"

SOURCE_ONLY_CONTRACT = {
    "metric_role": "main_ai_holding_base_prompt_replay_manifest",
    "decision_authority": "postclose_source_only_request_manifest",
    "window_policy": "exact_target_date_stage_venue_session_frozen_cohort",
    "sample_floor": "one_exact_hash_bound_parent_prepares_evaluation",
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "source_quality_gate": "clean_baseline_exact_payload_and_optimizer_hash_binding",
    "provider_call_performed": False,
    "runtime_effect": False,
    "runtime_authority": False,
    "order_authority": False,
    "provider_authority": False,
    "allowed_runtime_apply": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
    "forbidden_uses": [
        "provider_call_without_shared_budget_and_checkpoint",
        "live_holding_prompt_or_provider_route_change",
        "threshold_price_quantity_cap_or_order_change",
        "broker_or_hard_safety_guard_bypass",
        "bot_restart",
    ],
}


def report_path(target_date: str) -> Path:
    return REPORT_DIR / f"main_ai_holding_base_replay_batch_{target_date}.json"


def report_paths(target_date: str) -> tuple[Path, Path]:
    json_path = report_path(target_date)
    return json_path, json_path.with_suffix(".md")


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


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


def _valid_optimizer_report(payload: Mapping[str, Any], target_date: str) -> bool:
    declared_hash = str(payload.get("artifact_content_sha256") or "")
    content = {
        key: value
        for key, value in payload.items()
        if key != "artifact_content_sha256"
    }
    return bool(
        payload.get("schema") == optimizer.SCHEMA
        and payload.get("target_date") == target_date
        and payload.get("status") == "ready_source_only_continuous_search"
        and declared_hash
        and optimizer._canonical_sha256(content) == declared_hash
        and payload.get("runtime_effect") is False
        and payload.get("runtime_authority") is False
        and payload.get("allowed_runtime_apply") is False
        and payload.get("actual_order_submitted") is False
        and payload.get("broker_order_forbidden") is True
    )


def _request_fingerprint(request: Mapping[str, Any]) -> dict[str, Any]:
    candidate = request.get("candidate")
    candidate = candidate if isinstance(candidate, Mapping) else {}
    control = request.get("control")
    control = control if isinstance(control, Mapping) else {}
    return {
        "paired_replay_id": request.get("paired_replay_id"),
        "decision_trace_id": request.get("decision_trace_id"),
        "source_date": request.get("source_date"),
        "stage": request.get("stage"),
        "endpoint": request.get("endpoint"),
        "stock_code": request.get("stock_code"),
        "effective_venue": request.get("effective_venue"),
        "session_bucket": request.get("session_bucket"),
        "payload_sha256": request.get("payload_sha256"),
        "source_exact_payload_sha256": request.get("source_exact_payload_sha256"),
        "candidate_input_sha256": request.get("candidate_input_sha256"),
        "control_prompt_version": control.get("prompt_version"),
        "control_prompt_sha256": control.get("prompt_sha256"),
        "candidate_prompt_version": candidate.get("prompt_version"),
        "candidate_prompt_sha256": candidate.get("system_prompt_sha256"),
        "candidate_contract_sha256": candidate.get("contract_sha256"),
        "source_exactness": request.get("source_exactness"),
    }


def _intentionally_blocked(reason: str) -> dict[str, Any]:
    return {
        "path_status": "intentionally_blocked_with_owner_and_acceptance_test",
        "blocking_reason": reason,
        "owner": "MainAIHoldingBaseReplayConsumer",
        "acceptance_test": (
            "a non-empty exact target-date Holding cohort must preserve optimizer "
            "prompt version/SHA, candidate contract SHA, payload SHA, and input SHA"
        ),
    }


def _render_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        f"# Main AI Holding Base Replay Manifest - {report.get('target_date')}",
        "",
        "## Decision",
        f"- status: `{report.get('status')}`",
        f"- decision: `{report.get('decision')}`",
        f"- exact request fingerprints: `{report.get('request_count')}`",
        f"- provider_call_performed: `{report.get('provider_call_performed')}`",
        "",
        "## Cohorts",
    ]
    for cohort in report.get("cohorts") or []:
        lines.append(
            f"- `{cohort.get('effective_venue')}/{cohort.get('session_bucket')}` "
            f"status=`{cohort.get('path_status')}`, requests="
            f"`{cohort.get('request_count')}`, future provider candidate/deferred="
            f"`{cohort.get('future_provider_candidate_count')}/"
            f"{cohort.get('future_provider_deferred_count')}`, "
            f"reason=`{cohort.get('blocking_reason')}`"
        )
    lines.extend(
        [
            "",
            "## Authority",
            "- This manifest makes no provider call and cannot change a runtime prompt, provider route, order, threshold, price, quantity, cap, bot, broker guard, or hard safety.",
            "- New Holding execution remains blocked until the shared provider-budget and durable-checkpoint acceptance test passes.",
        ]
    )
    return "\n".join(lines) + "\n"


def build_report(
    target_date: str,
    *,
    max_rows_per_cohort: int = 30,
    write: bool = False,
) -> dict[str, Any]:
    parsed_date = date.fromisoformat(target_date)
    if parsed_date < optimizer.CLEAN_BASELINE_DATE:
        raise ValueError("target_date_before_clean_tuning_baseline")
    if max_rows_per_cohort <= 0:
        raise ValueError("max_rows_per_cohort_must_be_positive")

    optimizer_path, _ = optimizer.report_paths(target_date)
    optimizer_report = _read_json(optimizer_path)
    blockers: list[str] = []
    if not _valid_optimizer_report(optimizer_report, target_date):
        blockers.append("optimizer_artifact_missing_or_invalid")

    prepared_path = quality.micro_reversion_prepared_request_path(target_date)
    prepared = _read_json(prepared_path)
    prepared_valid = bool(
        prepared.get("schema") == "main_ai_quality_micro_prepared_requests_v1"
        and prepared.get("target_date") == target_date
        and prepared.get("status") == "prepared_requests_ready"
        and optimizer._embedded_content_sha256_valid(
            prepared, "artifact_content_sha256"
        )
        and optimizer._source_only_authority_valid(prepared)
    )
    if not prepared_valid:
        blockers.append("prepared_request_artifact_missing_or_invalid")
    optimizer_sources = optimizer_report.get("source_bindings")
    optimizer_sources = (
        optimizer_sources if isinstance(optimizer_sources, Mapping) else {}
    )
    if prepared_valid and optimizer_sources.get("prepared_request_sha256") != (
        optimizer._canonical_sha256(prepared)
    ):
        blockers.append("optimizer_prepared_request_hash_binding_mismatch")

    holding_optimizer = (
        (optimizer_report.get("stage_optimizers") or {}).get("holding") or {}
        if not blockers
        else {}
    )
    optimizer_cohorts = holding_optimizer.get("cohort_optimizers") or []
    if not optimizer_cohorts and not blockers:
        blockers.append("holding_optimizer_cohort_missing")

    promotion: dict[str, Any] = {}
    control: dict[str, Any] = {}
    traces: list[dict[str, Any]] = []
    payloads: list[dict[str, Any]] = []
    if not blockers:
        promotion, _, _ = quality.load_promotion_for_target_date(target_date)
        control = quality._load_json(quality.control_path(target_date))
        traces = coverage._load_rows(
            quality.TRACE_DIR, "ai_decision_trace", [target_date]
        )
        payloads = coverage._load_rows(
            quality.PAYLOAD_DIR, "ai_decision_payloads", [target_date]
        )

    prepared_rows = [
        row
        for row in prepared.get("prepared_requests") or []
        if isinstance(row, Mapping) and str(row.get("stage") or "").lower() == "holding"
    ]
    cohorts: list[dict[str, Any]] = []
    for optimizer_cohort in optimizer_cohorts:
        if not isinstance(optimizer_cohort, Mapping):
            blockers.append("holding_optimizer_cohort_invalid")
            continue
        venue = str(optimizer_cohort.get("effective_venue") or "").upper()
        session = str(optimizer_cohort.get("session_bucket") or "").upper()
        selected = optimizer_cohort.get("selected_challenger")
        selected = selected if isinstance(selected, Mapping) else {}
        selected_version = str(selected.get("prompt_version") or "")
        legacy = optimizer_cohort.get("legacy_r0_challenger")
        legacy = legacy if isinstance(legacy, Mapping) else {}
        selected_sha = (
            str(legacy.get("prompt_sha256") or "")
            if selected_version == str(legacy.get("prompt_version") or "")
            else ""
        )
        cohort_rows = [
            row
            for row in prepared_rows
            if str(row.get("effective_venue") or "").upper() == venue
            and str(row.get("session_bucket") or "").upper() == session
        ]
        trace_ids = {
            str(row.get("decision_trace_id") or "")
            for row in cohort_rows
            if row.get("decision_trace_id")
        }
        cohort: dict[str, Any] = {
            "effective_venue": venue,
            "session_bucket": session,
            "selected_prompt_version": selected_version,
            "selected_prompt_sha256": selected_sha or None,
            "optimizer_exact_parent_count": len(cohort_rows),
            "optimizer_exact_trace_ids_sha256": optimizer._canonical_sha256(
                sorted(trace_ids)
            ),
            "requests": [],
        }
        if selected_version != DECISION_QUALITY_HOLDING_V2_3_PROMPT_VERSION:
            cohort.update(_intentionally_blocked("unsupported_holding_challenger"))
            cohort["acceptance_test"] = (
                "register the selected Holding prompt/schema in the exact replay "
                "builder and prove its SHA before creating any provider request"
            )
            cohorts.append(cohort)
            continue
        if not selected_sha:
            cohort.update(_intentionally_blocked("selected_prompt_sha_missing"))
            cohorts.append(cohort)
            continue
        try:
            requests, source_summary = coverage.prepare_stage_requests(
                stage="holding",
                dates=[target_date],
                # The manifest classifies the complete exact-parent census.
                # ``max_rows_per_cohort`` caps only the future provider queue.
                max_rows=max(1, len(trace_ids)),
                control_manifest=control,
                promotion=promotion,
                traces=traces,
                payloads=payloads,
                eligible_trace_ids=trace_ids,
                effective_venue=venue,
                session_bucket=session,
            )
        except Exception as exc:
            cohort.update(
                _intentionally_blocked(
                    f"holding_request_prepare_failed:{type(exc).__name__}:"
                    f"{str(exc).splitlines()[0][:160]}"
                )
            )
            cohorts.append(cohort)
            continue
        fingerprints = [_request_fingerprint(request) for request in requests]
        for index, fingerprint in enumerate(fingerprints):
            fingerprint["future_provider_selection_state"] = (
                "candidate_within_daily_selection_cap"
                if index < max_rows_per_cohort
                else "deferred_by_daily_selection_cap"
            )
        observed_versions = {
            str(row.get("candidate_prompt_version") or "") for row in fingerprints
        }
        observed_hashes = {
            str(row.get("candidate_prompt_sha256") or "") for row in fingerprints
        }
        invalid_fingerprints = [
            row
            for row in fingerprints
            if not row.get("decision_trace_id")
            or not row.get("payload_sha256")
            or not row.get("candidate_input_sha256")
            or not row.get("candidate_contract_sha256")
            or row.get("source_exactness") != "byte_exact"
        ]
        fingerprint_trace_ids = [
            str(row.get("decision_trace_id") or "") for row in fingerprints
        ]
        missing_trace_ids = sorted(trace_ids - set(fingerprint_trace_ids))
        cohort.update(
            {
                "source_summary": source_summary,
                "request_count": len(fingerprints),
                "missing_exact_parent_count": len(missing_trace_ids),
                "missing_exact_parent_trace_ids_sha256": (
                    optimizer._canonical_sha256(missing_trace_ids)
                ),
                "future_provider_candidate_count": min(
                    len(fingerprints), max_rows_per_cohort
                ),
                "future_provider_deferred_count": max(
                    0, len(fingerprints) - max_rows_per_cohort
                ),
                "request_fingerprints_sha256": optimizer._canonical_sha256(
                    fingerprints
                ),
                "requests": fingerprints,
                "provider_execution_state": (
                    "blocked_pending_shared_budget_checkpoint_consumer"
                ),
                "new_or_changed_cell_only": True,
            }
        )
        if not fingerprints:
            cohort.update(_intentionally_blocked("no_exact_holding_request"))
        elif (
            len(trace_ids) != len(cohort_rows)
            or len(fingerprint_trace_ids) != len(set(fingerprint_trace_ids))
            or set(fingerprint_trace_ids) != trace_ids
        ):
            cohort.update(
                _intentionally_blocked(
                    "holding_exact_parent_census_not_fully_materialized"
                )
            )
            cohort["acceptance_test"] = (
                "each optimizer exact parent must produce exactly one hash-bound "
                "Holding request fingerprint or remain a parent-specific exclusion"
            )
        elif invalid_fingerprints:
            cohort.update(_intentionally_blocked("request_hash_binding_invalid"))
        elif observed_versions != {selected_version} or observed_hashes != {
            selected_sha
        }:
            cohort.update(_intentionally_blocked("optimizer_prompt_identity_mismatch"))
        else:
            cohort.update(
                {
                    "path_status": "connected_and_hash_bound",
                    "blocking_reason": None,
                    "owner": "MainAIHoldingBaseReplayConsumer",
                    "acceptance_test": "passed_exact_prompt_payload_input_hash_binding",
                }
            )
        cohorts.append(cohort)

    path_statuses = [str(row.get("path_status") or "") for row in cohorts]
    unclassified = sum(
        status
        not in {
            "connected_and_hash_bound",
            "intentionally_blocked_with_owner_and_acceptance_test",
            "retired_as_duplicate_of_existing_r0_r3",
        }
        for status in path_statuses
    )
    if unclassified:
        blockers.append("unclassified_holding_request_path")
    body: dict[str, Any] = {
        "schema": SCHEMA,
        "target_date": target_date,
        "generated_at": datetime.now(quality.KST).isoformat(timespec="seconds"),
        "status": (
            "blocked_source_contract"
            if blockers
            else "ready_source_only_holding_base_manifest"
        ),
        "decision": (
            "holding_base_request_path_hash_bound_provider_execution_gated"
            if not blockers
            else "holding_base_request_path_blocked_source_contract"
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
            "control_path": str(quality.control_path(target_date)),
        },
        "future_provider_selection_cap_per_cohort": max_rows_per_cohort,
        "cohorts": cohorts,
        "request_count": sum(int(row.get("request_count") or 0) for row in cohorts),
        "connected_cohort_count": sum(
            row.get("path_status") == "connected_and_hash_bound" for row in cohorts
        ),
        "intentionally_blocked_cohort_count": sum(
            row.get("path_status")
            == "intentionally_blocked_with_owner_and_acceptance_test"
            for row in cohorts
        ),
        "unclassified_request_path_count": unclassified,
        "blockers": sorted(set(blockers)),
        "next_action": (
            "execute only new or changed Holding request hashes after the shared "
            "provider-budget and durable checkpoint acceptance test passes"
        ),
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
    parser.add_argument("--date", required=True)
    parser.add_argument("--max-rows-per-cohort", type=int, default=30)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args(argv)
    report = build_report(
        args.date,
        max_rows_per_cohort=args.max_rows_per_cohort,
        write=args.write,
    )
    if args.print_summary:
        print(
            json.dumps(
                {
                    "target_date": report["target_date"],
                    "status": report["status"],
                    "request_count": report["request_count"],
                    "connected_cohort_count": report["connected_cohort_count"],
                },
                ensure_ascii=False,
            )
        )
    return 2 if report["status"] == "blocked_source_contract" else 0


if __name__ == "__main__":
    raise SystemExit(main())
