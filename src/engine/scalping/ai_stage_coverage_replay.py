"""Offline Prompt V2 coverage replay for exact stage captures.

This lane measures candidate decision coverage before forward outcomes mature.
It never changes a live prompt, provider route, order, price, or runtime setting.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from src.engine.ai_prompt_contracts import (
    DECISION_QUALITY_HOLDING_V2_3_PROMPT_VERSION,
    DECISION_QUALITY_V2_8_CANDIDATE_PROMPT_VERSION,
    DECISION_QUALITY_V2_PROMPT_VERSION,
    DECISION_QUALITY_V2_RESPONSE_SCHEMA,
    decision_quality_holding_v2_3_system_prompt,
    decision_quality_v2_8_detailed_system_prompt,
    decision_quality_v2_system_prompt,
)
from src.engine.bedrock_nova_provider import (
    BedrockNovaProvider,
    qwen3_32b_profile_from_env,
)
from src.engine.scalping import ai_decision_quality as quality
from src.utils.constants import DATA_DIR

SCHEMA = "ai_prompt_stage_coverage_replay_v1"
REPORT_DIR = DATA_DIR / "report" / "ai_prompt_stage_coverage_replay"
CONTRACT = {
    "metric_role": "ai_decision_quality_coverage_observation",
    "decision_authority": "offline_replay_no_runtime_change",
    "window_policy": "captured_exact_snapshot_chronological_frozen_cohort",
    "sample_floor": "report_observed_rows_and_unique_symbols_without_promotion",
    "primary_decision_metric": "candidate_action_transition_counts",
    "source_quality_gate": "exact_v2_fresh_same_route_conflict_free",
    "runtime_effect": False,
    "allowed_runtime_apply": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
    "forbidden_uses": [
        "live_prompt_promotion",
        "provider_or_model_change",
        "threshold_price_quantity_or_cap_change",
        "broker_or_safety_guard_bypass",
        "performance_claim_before_outcome_maturity",
        "bot_restart",
    ],
}
SUPPLEMENTAL_CONTRACT = {
    **CONTRACT,
    "decision_authority": "offline_supplemental_replay_no_runtime_change",
    "window_policy": (
        "captured_snapshot_approved_nondecision_cache_redaction_chronological_cohort"
    ),
    "sample_floor": (
        "supplemental_semantic_rows_and_unique_symbols_without_primary_authority"
    ),
    "source_quality_gate": (
        "exact_v2_fresh_same_route_conflict_free_except_approved_cache_redaction"
    ),
}


def _load_rows(source_dir: Path, stem: str, dates: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for target_date in dates:
        rows.extend(quality._load_jsonl(source_dir / f"{stem}_{target_date}.jsonl"))
    return rows


def _control_by_endpoint(
    manifest: dict[str, Any], *, field: str = "controls"
) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("endpoint") or ""): dict(row)
        for row in manifest.get(field) or []
        if isinstance(row, dict) and row.get("endpoint")
    }


def prepare_stage_requests(
    *,
    stage: str,
    dates: list[str],
    max_rows: int,
    control_manifest: dict[str, Any],
    promotion: dict[str, Any],
    traces: list[dict[str, Any]],
    payloads: list[dict[str, Any]],
    eligible_trace_ids: set[str] | None = None,
    allow_approved_cache_redaction_supplemental: bool = False,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Freeze the first exact eligible rows and preserve every exclusion reason."""

    normalized_stage = str(stage or "").strip().lower()
    if normalized_stage not in {"entry", "holding", "entry_price"}:
        raise ValueError("unsupported_stage")
    endpoint = {
        "entry": "analyze_target",
        "holding": "holding_score",
        "entry_price": "entry_price",
    }[normalized_stage]
    control_field = (
        "supplemental_semantic_controls"
        if allow_approved_cache_redaction_supplemental
        else "controls"
    )
    control = _control_by_endpoint(control_manifest, field=control_field).get(endpoint)
    if not control:
        raise ValueError(f"control_missing:{endpoint}")
    promoted_at = quality._parse_ts(promotion.get("promoted_at"))
    payload_by_key, payload_by_unique_hash = quality._payload_indexes(payloads)
    exclusions: Counter[str] = Counter()
    exact_exclusions: Counter[str] = Counter()
    eligible: list[dict[str, Any]] = []
    exact_source_count = 0
    supplemental_source_count = 0
    signature_fields = (
        ("prompt_version", "prompt_version"),
        ("prompt_sha256", "prompt_sha256"),
        ("provider_actual", "provider_actual"),
        ("model", "model"),
        ("request_temperature", "request_temperature"),
        ("request_reasoning_effort", "request_reasoning_effort"),
    )
    for trace in sorted(traces, key=lambda row: str(row.get("decision_ts") or "")):
        if str(trace.get("endpoint") or "") != endpoint:
            continue
        trace_id = str(trace.get("decision_trace_id") or "")
        if eligible_trace_ids is not None and trace_id not in eligible_trace_ids:
            exclusions["mature_outcome_not_eligible"] += 1
            continue
        if trace.get("payload_replay_exact") is True:
            exact_source_count += 1
        payload_hash = str(trace.get("payload_sha256") or "")
        payload = payload_by_key.get(
            (payload_hash, endpoint),
            payload_by_unique_hash.get(payload_hash, {}),
        )
        findings = quality._exact_trace_payload_findings(
            trace=trace,
            payload=payload,
            promoted_at=promoted_at,
        )
        supplemental = False
        if (
            allow_approved_cache_redaction_supplemental
            and set(findings).issuperset({"not_exact", "payload_store_not_exact"})
            and quality._approved_cache_redaction_supplemental(payload)
        ):
            findings = [
                finding
                for finding in findings
                if finding not in {"not_exact", "payload_store_not_exact"}
            ]
            supplemental = True
            supplemental_source_count += 1
        if any(
            trace.get(trace_key) != control.get(control_key)
            for trace_key, control_key in signature_fields
        ):
            findings.append("control_signature_mismatch")
        if findings:
            exclusions.update(set(findings))
            if trace.get("payload_replay_exact") is True:
                exact_exclusions.update(set(findings))
            continue
        eligible.append(
            {
                "trace": trace,
                "payload": payload,
                "semantic_replay_supplemental": supplemental,
            }
        )

    selected = eligible[:max_rows]
    exclusions["eligible_after_frozen_cohort_limit"] += max(
        0, len(eligible) - len(selected)
    )
    prompt = {
        "entry": decision_quality_v2_8_detailed_system_prompt("entry"),
        "holding": decision_quality_holding_v2_3_system_prompt(),
        "entry_price": decision_quality_v2_system_prompt("entry_price"),
    }[normalized_stage]
    if normalized_stage == "entry_price":
        prompt += """

Entry-price replay extension:
1. Return selected_price as a positive integer limit price, or null only for SKIP.
2. Return price_basis as BEST_BID, BEST_ASK, DEFENSIVE, REFERENCE, RESOLVED, or NONE.
3. Use only prices present in the exact payload. Do not invent a price.
4. USE_DEFENSIVE selects defensive_order_price when it is positive; otherwise use
   the fresh best bid. USE_REFERENCE selects a positive reference_target_price.
   IMPROVE_LIMIT selects a positive resolved_order_price or fresh best ask.
5. SKIP requires selected_price=null and price_basis=NONE.
""".strip()
    candidate = {
        "prompt_version": (
            DECISION_QUALITY_HOLDING_V2_3_PROMPT_VERSION
            if normalized_stage == "holding"
            else (
                DECISION_QUALITY_V2_8_CANDIDATE_PROMPT_VERSION
                if normalized_stage == "entry"
                else f"{DECISION_QUALITY_V2_PROMPT_VERSION}_{normalized_stage}"
            )
        ),
        "system_prompt": prompt,
        "system_prompt_sha256": quality._sha256(prompt),
        "response_schema": DECISION_QUALITY_V2_RESPONSE_SCHEMA,
        "response_schema_sha256": quality._sha256(DECISION_QUALITY_V2_RESPONSE_SCHEMA),
        "provider": control.get("provider_actual"),
        "model": control.get("model"),
        "temperature": control.get("request_temperature"),
        "reasoning_effort": control.get("request_reasoning_effort"),
    }
    if normalized_stage == "holding":
        candidate["semantic_validator_version"] = (
            quality.HOLDING_SEMANTIC_VALIDATOR_VERSION
        )
    candidate["contract_sha256"] = quality._candidate_contract_sha256(candidate)
    requests: list[dict[str, Any]] = []
    for row in selected:
        trace = row["trace"]
        payload = row["payload"]
        trace_id = str(trace.get("decision_trace_id") or "")
        exact_payload = quality._replay_exact_payload(
            payload.get("sanitized_user_input")
        )
        supplemental = bool(row.get("semantic_replay_supplemental"))
        authority_contract = SUPPLEMENTAL_CONTRACT if supplemental else CONTRACT
        request = {
            "paired_replay_id": (
                f"coverage-{quality._sha256((trace_id, trace.get('payload_sha256')))[:24]}"
            ),
            "decision_trace_id": trace_id,
            "decision_ts": trace.get("decision_ts"),
            "source_date": str(trace.get("decision_ts") or "")[:10],
            "stage": normalized_stage,
            "stock_code": trace.get("stock_code"),
            "effective_venue": trace.get("effective_venue"),
            "session_bucket": trace.get("session_bucket"),
            "payload_sha256": trace.get("payload_sha256"),
            "exact_payload": exact_payload,
            "control": {
                "prompt_version": control.get("prompt_version"),
                "prompt_sha256": control.get("prompt_sha256"),
                "provider": control.get("provider_actual"),
                "model": control.get("model"),
                "temperature": control.get("request_temperature"),
                "reasoning_effort": control.get("request_reasoning_effort"),
                "captured_action": trace.get("action"),
                "captured_score": trace.get("score"),
                "captured_reason": trace.get("reason"),
                "captured_selected_price": trace.get("reference_price"),
                "captured_selected_price_type": trace.get("reference_price_type"),
            },
            "candidate": dict(candidate),
            "source_exactness": (
                "non_exact_approved_cache_token_redaction"
                if supplemental
                else "byte_exact"
            ),
            "primary_exact_cohort_eligible": not supplemental,
            "supplemental_semantic_replay": supplemental,
            **authority_contract,
        }
        if normalized_stage == "entry":
            exact_analysis = quality.build_exact_payload_analysis_v1(
                exact_payload,
                stage="entry",
            )
            candidate_input = {
                "exact_payload": exact_payload,
                quality.EXACT_PAYLOAD_ANALYSIS_SCHEMA: exact_analysis,
            }
            request["candidate_input"] = candidate_input
            request["candidate_input_sha256"] = quality._sha256(candidate_input)
            request["exact_payload_analysis_sha256"] = exact_analysis["analysis_sha256"]
        elif normalized_stage == "holding":
            holding_facts = quality._holding_contract_facts(
                payload.get("sanitized_user_input")
            )
            candidate_input = {
                "exact_payload": payload.get("sanitized_user_input"),
                "holding_exact_contract_facts_v1": holding_facts,
            }
            request["candidate_input"] = candidate_input
            request["candidate_input_sha256"] = quality._sha256(candidate_input)
        requests.append(request)
    summary = {
        "exact_source_count": exact_source_count,
        "supplemental_semantic_source_count": supplemental_source_count,
        "exact_source_excluded_count": sum(
            1
            for trace in traces
            if str(trace.get("endpoint") or "") == endpoint
            and trace.get("payload_replay_exact") is True
        )
        - sum(not row.get("semantic_replay_supplemental") for row in eligible),
        "supplemental_semantic_eligible_count": sum(
            row.get("semantic_replay_supplemental") is True for row in eligible
        ),
        "strict_eligible_count": len(eligible),
        "selected_frozen_cohort_count": len(requests),
        **{
            f"exact_exclusion:{reason}": count
            for reason, count in exact_exclusions.items()
        },
        **dict(exclusions),
    }
    return requests, summary


def execute_bedrock_candidate(
    request: dict[str, Any],
    *,
    provider: BedrockNovaProvider | None = None,
) -> dict[str, Any]:
    """Run the entry-price candidate on the captured Qwen3 control route only."""

    if any(
        (
            request.get("runtime_effect") is not False,
            request.get("allowed_runtime_apply") is not False,
            request.get("actual_order_submitted") is not False,
            request.get("broker_order_forbidden") is not True,
        )
    ):
        raise ValueError("offline_authority_contract_invalid")
    control = request.get("control") or {}
    candidate = request.get("candidate") or {}
    if (
        str(control.get("provider") or "").lower() != "bedrock"
        or str(candidate.get("provider") or "").lower() != "bedrock"
        or str(control.get("model") or "") != str(candidate.get("model") or "")
        or str(candidate.get("model") or "") != "qwen3_32b"
    ):
        raise ValueError("provider_or_model_control_mismatch")
    profile = qwen3_32b_profile_from_env()
    result = (provider or BedrockNovaProvider()).converse(
        prompt=str(candidate.get("system_prompt") or ""),
        user_input=quality._canonical_bytes(request.get("exact_payload")).decode(
            "utf-8"
        ),
        profile=profile,
    )
    payload = dict(result.payload)
    action = str(payload.get("action") or "").upper()
    selected_price = quality._number(payload.get("selected_price"))
    price_basis = str(payload.get("price_basis") or "").upper()
    valid_bases = {
        "BEST_BID",
        "BEST_ASK",
        "DEFENSIVE",
        "REFERENCE",
        "RESOLVED",
    }
    selection_valid = (
        action == "SKIP" and selected_price is None and price_basis == "NONE"
    ) or (
        action != "SKIP"
        and selected_price is not None
        and selected_price > 0
        and float(selected_price).is_integer()
        and price_basis in valid_bases
        and selected_price
        in {
            value
            for item in quality._walk(request.get("exact_payload"))
            if isinstance(item, dict)
            for key, raw in item.items()
            if "price" in str(key).lower()
            and (value := quality._number(raw)) is not None
            and value > 0
        }
    )
    if not selection_valid:
        payload["action"] = "INVALID_ENTRY_PRICE_SELECTION"
    provenance = result.transport_meta()
    provenance.update(
        {
            "model": "qwen3_32b",
            "model_id": result.model_id,
            "transport": "bedrock_converse_offline",
            "provider_none": False,
            "failback_chain": [],
            "entry_price_selection_valid": selection_valid,
        }
    )
    return {
        "candidate_response": payload,
        "provider_provenance": provenance,
    }


def build_report(
    *,
    target_date: str,
    stage: str,
    dates: list[str],
    requested_max_rows: int,
    source_summary: dict[str, int],
    requests: list[dict[str, Any]],
    results: list[dict[str, Any]],
) -> dict[str, Any]:
    passed = [row for row in results if row.get("status") == "pass"]
    symbol_count = len(
        {
            str(request.get("stock_code") or "")
            for request in requests
            if request.get("stock_code")
        }
    )
    selection_complete = stage != "entry_price" or all(
        (
            str((row.get("candidate_response") or {}).get("action") or "").upper()
            == "SKIP"
            and (row.get("candidate_response") or {}).get("selected_price") is None
        )
        or quality._number((row.get("candidate_response") or {}).get("selected_price"))
        is not None
        for row in passed
    )
    transitions = Counter(
        (
            str((row.get("control_response") or {}).get("action") or "UNKNOWN"),
            str(
                (row.get("candidate_response") or {}).get("action") or "UNKNOWN"
            ).upper(),
        )
        for row in passed
    )
    candidate_actions = Counter(
        str((row.get("candidate_response") or {}).get("action") or "UNKNOWN").upper()
        for row in passed
    )
    dominant_action_ratio = (
        max(candidate_actions.values()) / len(passed) if passed else None
    )
    action_not_collapsed = (
        dominant_action_ratio is not None and dominant_action_ratio <= 0.90
    )
    coverage_sample_floor = {
        "required_decision_rows": quality.PAIRED_REPLAY_MIN_ROWS,
        "required_unique_symbols": quality.PAIRED_REPLAY_MIN_SYMBOLS,
        "observed_decision_rows": len(requests),
        "observed_unique_symbols": symbol_count,
        "pass": (
            len(requests) >= quality.PAIRED_REPLAY_MIN_ROWS
            and symbol_count >= quality.PAIRED_REPLAY_MIN_SYMBOLS
        ),
    }
    attempts = [
        attempt
        for row in results
        for attempt in row.get("candidate_attempts") or []
        if isinstance(attempt, dict)
    ]
    execution_complete = (
        bool(requests) and len(passed) == len(requests) and selection_complete
    )
    supplemental_count = sum(
        request.get("supplemental_semantic_replay") is True for request in requests
    )
    primary_exact_count = len(requests) - supplemental_count
    if not execution_complete:
        status = "coverage_replay_incomplete"
    elif not action_not_collapsed:
        status = "coverage_replay_complete_candidate_action_collapsed"
    elif not coverage_sample_floor["pass"]:
        status = "coverage_replay_complete_sample_floor_keep_collecting"
    else:
        status = "coverage_replay_complete_outcome_comparison_pending"
    base_status = status
    if supplemental_count and primary_exact_count == 0:
        status = f"supplemental_semantic_{base_status}"
    report_contract = SUPPLEMENTAL_CONTRACT if supplemental_count else CONTRACT
    return {
        "schema": SCHEMA,
        "target_date": target_date,
        "generated_at": datetime.now(quality.KST).isoformat(),
        "stage": stage,
        "source_dates": dates,
        "requested_max_rows": requested_max_rows,
        "candidate_prompt_versions": sorted(
            {
                str((request.get("candidate") or {}).get("prompt_version") or "")
                for request in requests
                if (request.get("candidate") or {}).get("prompt_version")
            }
        ),
        "candidate_prompt_sha256": sorted(
            {
                str((request.get("candidate") or {}).get("system_prompt_sha256") or "")
                for request in requests
                if (request.get("candidate") or {}).get("system_prompt_sha256")
            }
        ),
        "candidate_semantic_validator_versions": sorted(
            {
                str(
                    (request.get("candidate") or {}).get("semantic_validator_version")
                    or ""
                )
                for request in requests
                if (request.get("candidate") or {}).get("semantic_validator_version")
            }
        ),
        "status": status,
        "base_status": base_status,
        "primary_exact_request_count": primary_exact_count,
        "supplemental_semantic_request_count": supplemental_count,
        "primary_quality_authority": supplemental_count == 0,
        "source_summary": source_summary,
        "request_count": len(requests),
        "result_count": len(results),
        "pass_count": len(passed),
        "provider_failed_count": sum(
            row.get("status") == "provider_failed" for row in results
        ),
        "schema_rejected_count": sum(
            row.get("status") == "schema_rejected" for row in results
        ),
        "provider_attempt_count": len(attempts),
        "corrected_schema_attempt_count": sum(
            attempt.get("status") == "schema_rejected" for attempt in attempts
        ),
        "attempt_schema_error_counts": dict(
            Counter(
                str(error)
                for attempt in attempts
                for error in attempt.get("schema_errors") or []
            )
        ),
        "unique_symbol_count": symbol_count,
        "coverage_sample_floor": coverage_sample_floor,
        "control_action_counts": dict(
            Counter(
                str((row.get("control_response") or {}).get("action") or "UNKNOWN")
                for row in passed
            )
        ),
        "candidate_action_counts": dict(candidate_actions),
        "candidate_dominant_action_ratio": dominant_action_ratio,
        "candidate_action_not_collapsed": action_not_collapsed,
        "action_transition_counts": {
            f"{control}->{candidate}": count
            for (control, candidate), count in sorted(transitions.items())
        },
        "entry_price_selection_counts": dict(
            Counter(
                str(
                    (row.get("candidate_response") or {}).get("price_basis")
                    or "NOT_RECORDED"
                )
                for row in passed
            )
        ),
        "entry_price_selection_complete": selection_complete,
        "entry_price_control_exact_match_count": sum(
            quality._number((row.get("candidate_response") or {}).get("selected_price"))
            == quality._number(
                next(
                    (
                        request.get("control", {}).get("captured_selected_price")
                        for request in requests
                        if request.get("paired_replay_id")
                        == row.get("paired_replay_id")
                    ),
                    None,
                )
            )
            for row in passed
            if stage == "entry_price"
        ),
        "outcome_comparison_status": "pending_mature_outcome_join",
        "performance_claim_allowed": False,
        "requests": [
            {
                key: value
                for key, value in request.items()
                if key not in {"exact_payload", "candidate", "candidate_input"}
            }
            for request in requests
        ],
        "results": results,
        **report_contract,
    }


def reusable_pass_results(
    *,
    existing_report: dict[str, Any],
    requests: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Reuse only results bound to the same payload, candidate, and input."""

    request_by_pair = {
        str(request.get("paired_replay_id") or ""): request for request in requests
    }
    reusable: list[dict[str, Any]] = []
    for row in existing_report.get("results") or []:
        if not isinstance(row, dict) or row.get("status") != "pass":
            continue
        pair_id = str(row.get("paired_replay_id") or "")
        request = request_by_pair.get(pair_id)
        if not request:
            continue
        candidate = request.get("candidate") or {}
        if any(
            (
                row.get("payload_sha256") != request.get("payload_sha256"),
                row.get("candidate_prompt_sha256")
                != candidate.get("system_prompt_sha256"),
                row.get("candidate_contract_sha256")
                != candidate.get("contract_sha256"),
                row.get("candidate_input_sha256")
                != request.get("candidate_input_sha256"),
                row.get("exact_payload_analysis_sha256")
                != request.get("exact_payload_analysis_sha256"),
            )
        ):
            continue
        if quality.validate_candidate_response(
            dict(row.get("candidate_response") or {}),
            stage=str(request.get("stage") or ""),
            exact_payload=request.get("exact_payload"),
        ):
            continue
        reusable.append(row)
    order = {
        str(request.get("paired_replay_id") or ""): index
        for index, request in enumerate(requests)
    }
    reusable.sort(
        key=lambda row: order.get(str(row.get("paired_replay_id") or ""), len(order))
    )
    return reusable


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    parser.add_argument("--source-date", action="append", required=True)
    parser.add_argument(
        "--stage",
        choices=("entry", "holding", "entry_price"),
        required=True,
    )
    parser.add_argument("--max-rows", type=int, required=True)
    parser.add_argument("--execute-candidate", action="store_true")
    parser.add_argument("--candidate-workers", type=int, default=4)
    parser.add_argument(
        "--mature-outcomes-only",
        action="store_true",
        help=(
            "Restrict requests to exact traces with a source-quality-passing "
            "primary outcome metric, and attach paired outcome comparison."
        ),
    )
    parser.add_argument(
        "--allow-approved-cache-redaction-supplemental",
        action="store_true",
        help=(
            "Replay only approved non-decision cache-token redactions as a "
            "separate non-exact supplemental cohort."
        ),
    )
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    if args.max_rows <= 0:
        parser.error("--max-rows must be positive")
    if args.execute_candidate and not args.write:
        parser.error("--execute-candidate requires --write")
    promotion, _, _ = quality.load_promotion_for_target_date(args.source_date[0])
    control = quality._load_json(quality.control_path(args.source_date[0]))
    traces = _load_rows(quality.TRACE_DIR, "ai_decision_trace", args.source_date)
    payloads = _load_rows(quality.PAYLOAD_DIR, "ai_decision_payloads", args.source_date)
    labels: list[dict[str, Any]] = []
    for source_date in args.source_date:
        labels.extend(
            quality._load_json(quality.label_report_path(source_date)).get("labels")
            or []
        )
    eligible_trace_ids = None
    if args.mature_outcomes_only:
        eligible_trace_ids = {
            str(row.get("decision_trace_id") or "")
            for row in labels
            if row.get("label_status") in {"partial", "mature"}
            and row.get("source_quality_status") == "pass"
            and row.get("primary_cohort_eligible") is True
            and quality._primary_metric(row) is not None
            and row.get("decision_trace_id")
        }
        if not eligible_trace_ids:
            parser.error("--mature-outcomes-only found no eligible outcome labels")
    requests, source_summary = prepare_stage_requests(
        stage=args.stage,
        dates=args.source_date,
        max_rows=args.max_rows,
        control_manifest=control,
        promotion=promotion,
        traces=traces,
        payloads=payloads,
        eligible_trace_ids=eligible_trace_ids,
        allow_approved_cache_redaction_supplemental=(
            args.allow_approved_cache_redaction_supplemental
        ),
    )
    path = REPORT_DIR / f"ai_prompt_stage_coverage_replay_{args.date}_{args.stage}.json"
    results = reusable_pass_results(
        existing_report=quality._load_json(path),
        requests=requests,
    )
    if args.execute_candidate:
        runner = (
            execute_bedrock_candidate
            if args.stage == "entry_price"
            else quality.execute_openai_prompt_v2_candidate
        )

        def captured_control(request: dict[str, Any]) -> dict[str, Any]:
            control_row = request.get("control") or {}
            return {
                "action": control_row.get("captured_action"),
                "score": control_row.get("captured_score"),
                "reason": control_row.get("captured_reason"),
                "result_source": "captured_natural_control",
            }

        completed_pair_ids = {str(row.get("paired_replay_id") or "") for row in results}
        pending_requests = [
            request
            for request in requests
            if str(request.get("paired_replay_id") or "") not in completed_pair_ids
        ]
        results += quality.run_paired_replay_parallel(
            pending_requests,
            control_runner=captured_control,
            candidate_runner=runner,
            max_workers=args.candidate_workers,
        )
        order = {
            str(request.get("paired_replay_id") or ""): index
            for index, request in enumerate(requests)
        }
        results.sort(
            key=lambda row: order.get(
                str(row.get("paired_replay_id") or ""), len(order)
            )
        )
    report = build_report(
        target_date=args.date,
        stage=args.stage,
        dates=args.source_date,
        requested_max_rows=args.max_rows,
        source_summary=source_summary,
        requests=requests,
        results=results,
    )
    if args.mature_outcomes_only:
        report["mature_outcomes_only"] = True
        stage_endpoint = {
            "entry": "analyze_target",
            "holding": "holding_score",
            "entry_price": "entry_price",
        }[args.stage]
        stage_trace_ids = {
            str(row.get("decision_trace_id") or "")
            for row in traces
            if str(row.get("endpoint") or "") == stage_endpoint
            and row.get("decision_trace_id")
        }
        report["mature_outcome_eligible_trace_count"] = len(
            (eligible_trace_ids or set()).intersection(stage_trace_ids)
        )
        report["outcome_comparison_status"] = "attached_mature_outcomes"
        report["outcome_comparison"] = quality.build_paired_replay_report(
            target_date=args.date,
            requests=requests,
            results=results,
            labels=labels,
        )
    if args.write:
        quality._atomic_write_json(path, report)
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
