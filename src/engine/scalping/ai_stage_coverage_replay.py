"""Offline Prompt V2 coverage replay for exact stage captures.

This lane measures candidate decision coverage before forward outcomes mature.
It never changes a live prompt, provider route, order, price, or runtime setting.
"""

from __future__ import annotations

import argparse
import ast
import base64
import hashlib
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from statistics import fmean
from typing import Any

from src.engine.ai_prompt_contracts import (
    DECISION_QUALITY_ENTRY_PRICE_V2_5_PROMPT_VERSION,
    DECISION_QUALITY_HOLDING_FLOW_V2_2_PROMPT_VERSION,
    DECISION_QUALITY_HOLDING_V2_3_PROMPT_VERSION,
    DECISION_QUALITY_V2_8_CANDIDATE_PROMPT_VERSION,
    decision_quality_entry_price_v2_5_system_prompt,
    decision_quality_holding_flow_v2_2_system_prompt,
    decision_quality_holding_v2_3_system_prompt,
    decision_quality_v2_8_detailed_system_prompt,
)
from src.engine.ai_response_contracts import build_openai_response_text_format
from src.engine.bedrock_nova_provider import (
    BedrockNovaModelProfile,
    BedrockNovaProvider,
    lite_v2_profile_from_env,
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
    effective_venue: str | None = None,
    session_bucket: str | None = None,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Freeze the first exact eligible rows and preserve every exclusion reason."""

    normalized_stage = str(stage or "").strip().lower()
    if normalized_stage not in {"entry", "holding", "holding_flow", "entry_price"}:
        raise ValueError("unsupported_stage")
    endpoint = {
        "entry": "analyze_target",
        "holding": "holding_score",
        "holding_flow": "holding_flow",
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
        if (
            effective_venue
            and str(trace.get("effective_venue") or "").upper()
            != str(effective_venue).upper()
        ):
            exclusions["cohort_venue_filter_excluded"] += 1
            continue
        if (
            session_bucket
            and str(trace.get("session_bucket") or "").lower()
            != str(session_bucket).lower()
        ):
            exclusions["cohort_session_filter_excluded"] += 1
            continue
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
        "holding_flow": decision_quality_holding_flow_v2_2_system_prompt(),
        "entry_price": decision_quality_entry_price_v2_5_system_prompt(),
    }[normalized_stage]
    candidate_schema_name = {
        "entry": "decision_quality_v2_entry_candidate",
        "holding": "decision_quality_holding_v2_3_candidate",
        "holding_flow": "decision_quality_holding_flow_v2_2_candidate",
        "entry_price": "entry_price_explicit_fill_value_v1",
    }[normalized_stage]
    response_schema = (
        build_openai_response_text_format(candidate_schema_name)["schema"]
        if normalized_stage == "entry_price"
        else quality._prompt_v2_openai_schema(
            "entry" if normalized_stage == "entry" else "holding"
        )
    )
    candidate = {
        "prompt_version": (
            DECISION_QUALITY_HOLDING_V2_3_PROMPT_VERSION
            if normalized_stage == "holding"
            else (
                DECISION_QUALITY_HOLDING_FLOW_V2_2_PROMPT_VERSION
                if normalized_stage == "holding_flow"
                else (
                    DECISION_QUALITY_V2_8_CANDIDATE_PROMPT_VERSION
                    if normalized_stage == "entry"
                    else DECISION_QUALITY_ENTRY_PRICE_V2_5_PROMPT_VERSION
                )
            )
        ),
        "system_prompt": prompt,
        "system_prompt_sha256": quality._sha256(prompt),
        "response_schema": response_schema,
        "response_schema_sha256": quality._sha256(response_schema),
        "provider": control.get("provider_actual"),
        "model": control.get("model"),
        "temperature": control.get("request_temperature"),
        "reasoning_effort": control.get("request_reasoning_effort"),
        "schema_name": candidate_schema_name,
        "require_json": True,
    }
    if normalized_stage == "holding_flow":
        candidate["semantic_validator_version"] = (
            quality.HOLDING_FLOW_BOUNDED_DEFER_SEMANTIC_VALIDATOR_VERSION
        )
    elif normalized_stage == "holding":
        candidate["semantic_validator_version"] = (
            quality.HOLDING_SEMANTIC_VALIDATOR_VERSION
        )
    elif normalized_stage == "entry_price":
        candidate["semantic_validator_version"] = (
            quality.ENTRY_PRICE_SEMANTIC_VALIDATOR_VERSION
        )
    else:
        candidate["semantic_validator_version"] = (
            quality.DECISION_QUALITY_V2_SEMANTIC_VALIDATOR_VERSION
        )
    candidate["contract_sha256"] = quality._candidate_contract_sha256(candidate)
    requests: list[dict[str, Any]] = []
    for row in selected:
        trace = row["trace"]
        payload = row["payload"]
        trace_id = str(trace.get("decision_trace_id") or "")
        source_input = quality.replay_source_input(payload)
        exact_payload = quality._replay_exact_payload(source_input)
        supplemental = bool(row.get("semantic_replay_supplemental"))
        authority_contract = SUPPLEMENTAL_CONTRACT if supplemental else CONTRACT
        request_candidate = {
            **candidate,
            "transport": trace.get("transport"),
            "max_output_tokens": payload.get("max_output_tokens"),
            "response_schema_mode": trace.get("openai_response_schema_mode"),
            "response_schema_application": (
                "provider_enforced_openai"
                if str(trace.get("provider_actual") or "").strip().lower() == "openai"
                else "local_expected_only_not_sent_to_bedrock"
            ),
            "response_schema_registry_used": trace.get(
                "openai_response_schema_registry_used"
            ),
        }
        request_candidate["contract_sha256"] = quality._candidate_contract_sha256(
            request_candidate
        )
        request = {
            "paired_replay_id": (
                f"coverage-{quality._sha256((trace_id, trace.get('payload_sha256')))[:24]}"
            ),
            "decision_trace_id": trace_id,
            "record_id": trace.get("record_id"),
            "decision_ts": trace.get("decision_ts"),
            "source_date": str(trace.get("decision_ts") or "")[:10],
            "stage": (
                "holding" if normalized_stage == "holding_flow" else normalized_stage
            ),
            "coverage_stage": normalized_stage,
            "endpoint": endpoint,
            "stock_code": trace.get("stock_code"),
            "effective_venue": trace.get("effective_venue"),
            "session_bucket": trace.get("session_bucket"),
            "payload_sha256": trace.get("payload_sha256"),
            "request_envelope_sha256": trace.get("request_envelope_sha256"),
            "exact_payload": exact_payload,
            "source_exact_payload_sha256": quality._sha256(exact_payload),
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
                "captured_edge_state": trace.get("decision_quality_model_edge_state"),
                "captured_evidence": trace.get("decision_quality_model_evidence"),
                "captured_entry_probe_intent": trace.get("entry_probe_intent"),
                "captured_entry_probe_intent_status": trace.get(
                    "entry_probe_intent_status"
                ),
                "captured_entry_probe_intent_eligibility_path": trace.get(
                    "entry_probe_intent_eligibility_path"
                ),
                "captured_entry_probe_intent_after_cost_reward_risk": trace.get(
                    "entry_probe_intent_after_cost_reward_risk"
                ),
            },
            "candidate": request_candidate,
            "source_exactness": (
                "non_exact_approved_cache_token_redaction"
                if supplemental
                else "byte_exact"
            ),
            "primary_exact_cohort_eligible": not supplemental,
            "supplemental_semantic_replay": supplemental,
            **authority_contract,
        }
        if normalized_stage == "entry_price":
            request["control"].update(
                {
                    "captured_selected_price": (
                        None
                        if str(trace.get("action") or "").strip().upper() == "SKIP"
                        else trace.get("reference_price")
                    ),
                    "captured_reference_price": trace.get("reference_price"),
                    "captured_selected_price_type": trace.get("reference_price_type"),
                }
            )
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
        elif normalized_stage in {"holding", "holding_flow"}:
            holding_facts = quality._holding_contract_facts(exact_payload)
            candidate_input = {
                "exact_payload": exact_payload,
                "holding_exact_contract_facts_v1": holding_facts,
            }
            request["candidate_input"] = candidate_input
            request["candidate_input_sha256"] = quality._sha256(candidate_input)
        elif normalized_stage == "entry_price":
            captured_action = str(trace.get("action") or "").strip().upper()
            control_selected_price = (
                None
                if captured_action == "SKIP"
                else quality._number(trace.get("reference_price"))
            )
            if (
                control_selected_price is not None
                and control_selected_price > 0
                and float(control_selected_price).is_integer()
            ):
                control_selected_price = int(control_selected_price)
            else:
                control_selected_price = None
            entry_price_facts = quality.build_entry_price_explicit_fill_value_contract(
                exact_payload,
                control_selected_price=control_selected_price,
                control_exposure_selected=captured_action != "SKIP",
            )
            candidate_input = {
                "exact_payload": exact_payload,
                "entry_price_exact_contract_facts_v1": entry_price_facts,
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
    profile: BedrockNovaModelProfile | None = None,
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
    profile = profile or qwen3_32b_profile_from_env()
    prompt = str(candidate.get("system_prompt") or "")
    correction_errors = [
        str(value)
        for value in request.get("candidate_schema_correction_errors") or []
        if value
    ]
    if correction_errors:
        correction_rules: list[str] = []
        if "reason_codes_invalid" in correction_errors:
            correction_rules.append(
                "Remove every non-canonical reason code. Never use spread_bp, "
                "wide_spread, price_basis, or setup_continuation as a reason "
                "code. Represent a continuation setup only as "
                "evidence.setup=continuation. Use liquidity_adverse or "
                "fillability_adverse when supported"
            )
        if "expected_edge_values_required" in correction_errors:
            correction_rules.append(
                "NO_EDGE requires numeric expected_upside_pct and "
                "expected_downside_pct; use bounded numeric estimates and never "
                "null. Only INSUFFICIENT_DATA may use null values"
            )
        if any(error.startswith("entry_price_") for error in correction_errors):
            correction_rules.append(
                "For USE_DEFENSIVE select DEFENSIVE and its exact value, or "
                "BEST_BID only when DEFENSIVE is null. For USE_REFERENCE select "
                "REFERENCE. For IMPROVE_LIMIT select RESOLVED or BEST_ASK. Never "
                "return selected_price=null or price_basis=NONE for a non-SKIP "
                "action. A non-defensive action must select a price distinct "
                "from control_selected_price. A more aggressive price requires "
                "confirmed immediate edge and expected_upside_pct at or above "
                "minimum_upside_for_aggressive_basis_pct. Otherwise return the "
                "exact DEFENSIVE price with USE_DEFENSIVE. Positive chase cost "
                "must not exceed max_incremental_chase_cost_bp and requires a "
                "strictly negative expected_downside_pct whose magnitude covers "
                "the incremental cost. expected_upside_pct divided by absolute "
                "expected_downside_pct must meet "
                "minimum_reward_risk_for_aggressive_basis. For every non-SKIP "
                "response include all five fill-value fields and reproduce the "
                "incremental fill, chase-cost, and fill-adjusted-edge formulas "
                "exactly. A positive chase cost requires positive incremental "
                "fill probability and positive fill_adjusted_edge_pct"
            )
        aggressive_economic_errors = {
            "entry_price_aggressive_limit_without_confirmed_edge",
            "entry_price_aggressive_limit_insufficient_edge_buffer",
            "entry_price_aggressive_limit_exceeds_chase_cost_bound",
            "entry_price_aggressive_limit_requires_negative_downside",
            "entry_price_aggressive_limit_downside_below_chase_cost",
            "entry_price_aggressive_limit_reward_risk_below_floor",
            "entry_price_aggressive_limit_no_fill_improvement",
            "entry_price_aggressive_limit_nonpositive_fill_value",
        }
        if aggressive_economic_errors.intersection(correction_errors):
            correction_rules.append(
                "The prior aggressive selection failed the deterministic economic "
                "gate. For this correction do not retry REFERENCE, RESOLVED, or "
                "BEST_ASK. Return USE_DEFENSIVE with price_basis=DEFENSIVE and "
                "the exact DEFENSIVE candidate price; use BEST_BID only when the "
                "DEFENSIVE candidate is null"
            )
        prompt += (
            "\n\nCorrection retry: the prior response violated: "
            + ",".join(correction_errors)
            + ". Re-read entry_price_exact_contract_facts_v1. SKIP is valid only "
            "when skip_permitted=true. Match action, price_basis, and the exact "
            "candidate_prices value. "
            + "; ".join(correction_rules)
            + ". Return one corrected JSON object only."
        )
    result = (provider or BedrockNovaProvider()).converse(
        prompt=prompt,
        user_input=quality._canonical_bytes(
            request.get("candidate_input", request.get("exact_payload"))
        ).decode("utf-8"),
        profile=profile,
    )
    payload, action_canonicalization = (
        canonicalize_entry_price_economically_equivalent_action(
            dict(result.payload),
            contract_facts=(
                (request.get("candidate_input") or {}).get(
                    "entry_price_exact_contract_facts_v1"
                )
            ),
        )
    )
    payload, fill_value_normalization = normalize_entry_price_fill_value_ledger(
        payload,
        contract_facts=(
            (request.get("candidate_input") or {}).get(
                "entry_price_exact_contract_facts_v1"
            )
        ),
    )
    selection_errors = quality._entry_price_response_errors(
        payload,
        exact_payload=request.get("exact_payload"),
        contract_facts=(
            (request.get("candidate_input") or {}).get(
                "entry_price_exact_contract_facts_v1"
            )
        ),
        require_fill_adjusted_distinct_limit=True,
        require_explicit_fill_value_ledger=True,
    )
    selection_valid = not selection_errors
    provenance = result.transport_meta()
    provenance.update(
        {
            "provider": "bedrock",
            "model": "qwen3_32b",
            "model_id": result.model_id,
            "transport": "bedrock_converse_offline",
            "source_transport_contract": candidate.get("transport"),
            "provider_none": False,
            "provider_call_attempted": True,
            "provider_call_succeeded": True,
            "canonical_response_sha256": quality._sha256(payload),
            "response_id_unavailable_reason": (
                None
                if provenance.get("response_id")
                else "bedrock_transport_response_id_not_exposed"
            ),
            "failback_chain": [],
            "entry_price_selection_valid": selection_valid,
            "entry_price_selection_errors": selection_errors,
            **action_canonicalization,
            **fill_value_normalization,
        }
    )
    return {
        "candidate_response": payload,
        "provider_provenance": provenance,
    }


def execute_bedrock_lifecycle_candidate(
    request: dict[str, Any],
    *,
    provider: BedrockNovaProvider | None = None,
    profile: BedrockNovaModelProfile | None = None,
) -> dict[str, Any]:
    """Run one source-only Nova lifecycle attempt with replayable raw output."""

    if any(
        (
            request.get("runtime_effect") is not False,
            request.get("allowed_runtime_apply") is not False,
            request.get("actual_order_submitted") is not False,
            request.get("broker_order_forbidden") is not True,
        )
    ):
        raise ValueError("offline_authority_contract_invalid")
    candidate = request.get("candidate")
    candidate = candidate if isinstance(candidate, dict) else {}
    stage = quality._stage(request.get("stage"), request.get("endpoint"))
    if (
        stage not in {"holding", "exit"}
        or str(candidate.get("provider") or "").strip().lower() != "bedrock"
        or str(candidate.get("model") or "").strip() != "nova_lite_v2"
    ):
        raise ValueError("bedrock_lifecycle_provider_model_stage_mismatch")
    response_schema = candidate.get("response_schema")
    if not isinstance(response_schema, dict) or candidate.get(
        "response_schema_sha256"
    ) != quality._sha256(response_schema):
        raise ValueError("bedrock_lifecycle_response_schema_invalid")
    schema_instance_sha256 = quality._sha256(response_schema)
    expected_schema_instance_sha256 = str(
        candidate.get("response_schema_instance_sha256") or ""
    )
    if (
        expected_schema_instance_sha256
        and expected_schema_instance_sha256 != schema_instance_sha256
    ):
        raise ValueError("bedrock_lifecycle_response_schema_instance_mismatch")
    selected_profile = profile or lite_v2_profile_from_env()
    reserved_max_output_tokens = candidate.get("max_output_tokens")
    if (
        isinstance(reserved_max_output_tokens, bool)
        or not isinstance(reserved_max_output_tokens, int)
        or reserved_max_output_tokens <= 0
    ):
        raise ValueError("bedrock_lifecycle_profile_output_tokens_invalid")
    if selected_profile.max_output_tokens > reserved_max_output_tokens:
        raise ValueError("bedrock_lifecycle_profile_exceeds_reserved_output_tokens")
    if selected_profile.max_output_tokens < reserved_max_output_tokens:
        raise ValueError("bedrock_lifecycle_profile_output_tokens_drift")
    prompt, user_input, provider_request_projection = (
        quality._current_bedrock_lifecycle_provider_request(
            request,
            selected_profile=selected_profile,
        )
    )
    result = (provider or BedrockNovaProvider(key_rotation_enabled=False)).converse(
        prompt=prompt,
        user_input=user_input,
        profile=selected_profile,
    )
    if result.attempted_key_count != 1:
        raise ValueError("bedrock_lifecycle_single_network_attempt_violated")
    if (
        result.model_id != selected_profile.model_id
        or result.region_name != selected_profile.region_name
    ):
        raise ValueError("bedrock_lifecycle_result_profile_drift")
    payload = dict(result.payload)
    raw_bytes = result.raw_text.encode("utf-8")
    raw_sha256 = hashlib.sha256(raw_bytes).hexdigest()
    response_id = str(result.response_id or "").strip() or None
    receipt_content = {
        "schema": quality.MICRO_REVERSION_BEDROCK_ATTEMPT_RECEIPT_SCHEMA,
        "paired_replay_parent_id": request.get("paired_replay_parent_id"),
        "paired_replay_id": request.get("paired_replay_id"),
        "micro_reversion_replay_arm": request.get("micro_reversion_replay_arm"),
        "candidate_input_sha256": request.get("candidate_input_sha256"),
        "candidate_contract_sha256": (
            candidate.get("contract_sha256")
            or quality._candidate_contract_sha256(candidate)
        ),
        "offline_provider_attempt_number": request.get(
            "offline_provider_attempt_number"
        ),
        "provider": "bedrock",
        "model": candidate.get("model"),
        "model_id": result.model_id,
        "region_name": result.region_name,
        "response_id": response_id,
        "provider_output_projection": "bedrock_nova_result_raw_text",
        "provider_output_encoding": "utf-8+base64",
        "provider_output_bytes_b64": base64.b64encode(raw_bytes).decode("ascii"),
        "provider_output_size_bytes": len(raw_bytes),
        "provider_output_bytes_sha256": raw_sha256,
        "parse_transform_version": (
            quality.MICRO_REVERSION_BEDROCK_PARSE_TRANSFORM_VERSION
        ),
        "parse_status": "pass" if result.parse_ok else result.parse_error,
        "parsed_candidate_payload": payload if result.parse_ok else None,
        "parsed_candidate_payload_sha256": (
            quality._sha256(payload) if result.parse_ok else None
        ),
        "response_schema_instance_sha256": schema_instance_sha256,
        "provider_request_projection": provider_request_projection,
        "provider_request_projection_sha256": quality._sha256(
            provider_request_projection
        ),
    }
    provenance = result.transport_meta()
    provenance.update(
        {
            "provider": "bedrock",
            "model": candidate.get("model"),
            "model_id": result.model_id,
            "transport": "bedrock_converse_offline",
            "source_transport_contract": candidate.get("transport"),
            "response_id": response_id,
            "response_id_unavailable_reason": (
                None if response_id else "bedrock_transport_response_id_not_exposed"
            ),
            "response_sha256": raw_sha256,
            "provider_request_projection_sha256": quality._sha256(
                provider_request_projection
            ),
            "canonical_response_sha256": quality._sha256(payload),
            "provider_none": False,
            "provider_call_attempted": True,
            "provider_call_succeeded": True,
            "failback_chain": [],
        }
    )
    return {
        "candidate_response": payload,
        "provider_attempt_receipt": {
            **receipt_content,
            "attempt_receipt_content_sha256": quality._sha256(receipt_content),
        },
        "provider_provenance": provenance,
    }


def execute_bedrock_candidate_single_network_attempt(
    request: dict[str, Any],
) -> dict[str, Any]:
    """Run one budgeted offline attempt without internal key rotation.

    The caller reserves one provider attempt before entering this function.
    Disabling the provider's otherwise-valid key rotation keeps that reservation
    in one-to-one correspondence with at most one Bedrock ``converse`` request.
    The shared provider default remains unchanged for non-budgeted/live callers.
    """

    candidate = request.get("candidate") or {}
    reserved_max_output_tokens = candidate.get("max_output_tokens")
    if (
        isinstance(reserved_max_output_tokens, bool)
        or not isinstance(reserved_max_output_tokens, int)
        or reserved_max_output_tokens <= 0
    ):
        raise ValueError("bedrock_budgeted_max_output_tokens_invalid")
    stage = quality._stage(request.get("stage"), request.get("endpoint"))
    candidate_model = str(candidate.get("model") or "")
    profile = (
        lite_v2_profile_from_env()
        if stage in {"holding", "exit"} and candidate_model == "nova_lite_v2"
        else qwen3_32b_profile_from_env()
    )
    expected_profile_family = (
        "lite_v2" if candidate_model == "nova_lite_v2" else candidate_model
    )
    if profile.family != expected_profile_family:
        raise ValueError("bedrock_budgeted_profile_family_mismatch")
    if profile.max_output_tokens > reserved_max_output_tokens:
        raise ValueError("bedrock_budgeted_profile_exceeds_reserved_output_tokens")
    if (
        request.get("ablation_design_version") == quality.CURRENT_DESIGN_VERSION
        and stage in {"holding", "exit"}
        and candidate_model == "nova_lite_v2"
        and profile.max_output_tokens < reserved_max_output_tokens
    ):
        raise ValueError("bedrock_budgeted_profile_output_tokens_drift")
    provider = BedrockNovaProvider(key_rotation_enabled=False)
    if stage in {"holding", "exit"}:
        return execute_bedrock_lifecycle_candidate(
            request,
            provider=provider,
            profile=profile,
        )
    return execute_bedrock_candidate(request, provider=provider, profile=profile)


def canonicalize_entry_price_economically_equivalent_action(
    response: dict[str, Any], *, contract_facts: dict[str, Any] | None
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Canonicalize only a label when Control, defensive, and selected prices match."""

    return quality.canonicalize_entry_price_economically_equivalent_action(
        response,
        contract_facts=contract_facts,
    )


def normalize_entry_price_fill_value_ledger(
    response: dict[str, Any], *, contract_facts: dict[str, Any] | None
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Derive arithmetic ledger fields while preserving model probability estimates."""

    return quality.normalize_entry_price_fill_value_ledger(
        response,
        contract_facts=contract_facts,
    )


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
    request_by_pair = {
        str(request.get("paired_replay_id") or ""): request for request in requests
    }
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
    action_collapse_evaluable = coverage_sample_floor["pass"]
    action_not_collapsed = (
        dominant_action_ratio <= 0.90
        if action_collapse_evaluable and dominant_action_ratio is not None
        else None
    )
    entry_price_effect_rows: list[dict[str, Any]] = []
    if stage == "entry_price":
        for row in passed:
            pair_id = str(row.get("paired_replay_id") or "")
            request = request_by_pair.get(pair_id) or {}
            control = request.get("control") or {}
            candidate = row.get("candidate_response") or {}
            control_price = quality._number(control.get("captured_selected_price"))
            candidate_price = (
                None
                if str(candidate.get("action") or "").upper() == "SKIP"
                else quality._number(candidate.get("selected_price"))
            )
            price_delta_bp = (
                ((candidate_price - control_price) / control_price) * 10000.0
                if candidate_price is not None
                and control_price is not None
                and control_price > 0
                else None
            )
            action_changed = (
                str(candidate.get("action") or "").upper()
                != str(control.get("captured_action") or "").upper()
            )
            control_exposure_selected = bool(
                str(control.get("captured_action") or "").upper() != "SKIP"
                and control_price is not None
            )
            candidate_exposure_selected = bool(
                str(candidate.get("action") or "").upper() != "SKIP"
                and candidate_price is not None
            )
            exposure_selection_changed = (
                control_exposure_selected != candidate_exposure_selected
            )
            entry_price_effect_rows.append(
                {
                    "stock_code": request.get("stock_code"),
                    "control_price": control_price,
                    "candidate_price": candidate_price,
                    "price_delta_bp": price_delta_bp,
                    "economically_distinct": bool(
                        exposure_selection_changed
                        or (price_delta_bp is not None and abs(price_delta_bp) > 1e-9)
                    ),
                    "action_only_relabel": bool(
                        action_changed
                        and not exposure_selection_changed
                        and price_delta_bp is not None
                        and abs(price_delta_bp) <= 1e-9
                    ),
                }
            )
    economically_distinct_count = sum(
        row["economically_distinct"] for row in entry_price_effect_rows
    )
    action_only_relabel_count = sum(
        row["action_only_relabel"] for row in entry_price_effect_rows
    )
    economically_distinct_symbol_count = len(
        {
            str(row.get("stock_code") or "")
            for row in entry_price_effect_rows
            if row["economically_distinct"] and row.get("stock_code")
        }
    )
    entry_price_effect_not_collapsed = (
        economically_distinct_count > 0 if stage == "entry_price" and passed else None
    )
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
    elif not coverage_sample_floor["pass"]:
        status = "coverage_replay_complete_sample_floor_keep_collecting"
    elif stage != "entry_price" and action_not_collapsed is False:
        status = "coverage_replay_complete_candidate_action_collapsed"
    elif stage == "entry_price" and entry_price_effect_not_collapsed is False:
        status = "coverage_replay_complete_candidate_price_effect_collapsed"
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
        "candidate_action_collapse_evaluable": action_collapse_evaluable,
        "candidate_action_not_collapsed": action_not_collapsed,
        "candidate_action_collapse_decision_authority": (
            "diagnostic_only_price_effect_gate_owns_decision"
            if stage == "entry_price"
            else "quality_gate"
        ),
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
        "entry_price_economically_distinct_count": economically_distinct_count,
        "entry_price_economically_distinct_unique_symbol_count": (
            economically_distinct_symbol_count
        ),
        "entry_price_action_only_relabel_count": action_only_relabel_count,
        "entry_price_effect_not_collapsed": entry_price_effect_not_collapsed,
        "entry_price_control_exact_match_count": sum(
            row["candidate_price"] == row["control_price"]
            for row in entry_price_effect_rows
            if row["candidate_price"] is not None and row["control_price"] is not None
        ),
        "entry_price_comparable_price_count": sum(
            row["candidate_price"] is not None and row["control_price"] is not None
            for row in entry_price_effect_rows
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
        if quality.validate_replay_candidate_response(
            request,
            dict(row.get("candidate_response") or {}),
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


def reusable_pass_results_from_reports(
    *,
    existing_reports: list[tuple[str, dict[str, Any]]],
    requests: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Deduplicate hash-validated PASS checkpoints across replay reports."""

    reusable: list[dict[str, Any]] = []
    seen_pair_ids: set[str] = set()
    sources: list[dict[str, Any]] = []
    for source_path, report in existing_reports:
        matched = reusable_pass_results(existing_report=report, requests=requests)
        added = 0
        for row in matched:
            pair_id = str(row.get("paired_replay_id") or "")
            if not pair_id or pair_id in seen_pair_ids:
                continue
            reusable.append(row)
            seen_pair_ids.add(pair_id)
            added += 1
        sources.append(
            {
                "source_path": source_path,
                "source_report_sha256": quality._sha256(report),
                "target_date": report.get("target_date"),
                "generated_at": report.get("generated_at"),
                "candidate_prompt_versions": report.get("candidate_prompt_versions"),
                "matched_pass_count": len(matched),
                "reused_pass_count": added,
            }
        )
    order = {
        str(request.get("paired_replay_id") or ""): index
        for index, request in enumerate(requests)
    }
    reusable.sort(
        key=lambda row: order.get(str(row.get("paired_replay_id") or ""), len(order))
    )
    return reusable, sources


def build_holding_flow_outcome_attribution(
    *,
    requests: list[dict[str, Any]],
    results: list[dict[str, Any]],
    labels: list[dict[str, Any]],
) -> dict[str, Any]:
    """Join holding-flow actions to the observed path without claiming causality."""

    request_by_trace = {
        str(row.get("decision_trace_id") or ""): row for row in requests
    }
    label_by_trace = {
        str(row.get("decision_trace_id") or ""): row
        for row in labels
        if row.get("source_quality_status") == "pass"
        and row.get("primary_cohort_eligible") is True
    }
    rows: list[dict[str, Any]] = []
    for result in results:
        if (
            result.get("status") != "pass"
            or result.get("same_payload_confirmed") is not True
        ):
            continue
        trace_id = str(result.get("decision_trace_id") or "")
        request = request_by_trace.get(trace_id)
        label = label_by_trace.get(trace_id)
        metric = quality._primary_metric(label or {})
        if request is None or label is None or metric is None:
            continue
        stage_outcome = label.get("stage_outcome")
        stage_outcome = stage_outcome if isinstance(stage_outcome, dict) else {}
        mfe = quality._number(metric.get("mfe_pct"))
        end_return = quality._number(metric.get("end_return_pct"))
        rows.append(
            {
                "decision_trace_id": trace_id,
                "stock_code": request.get("stock_code"),
                "effective_venue": request.get("effective_venue"),
                "session_bucket": request.get("session_bucket"),
                "control_action": (result.get("control_response") or {}).get("action"),
                "candidate_action": (result.get("candidate_response") or {}).get(
                    "action"
                ),
                "primary_horizon": quality.PRIMARY_HORIZON_BY_STAGE["holding"],
                "observed_post_decision_end_return_pct": end_return,
                "observed_post_decision_mfe_pct": mfe,
                "observed_post_decision_mae_pct": quality._number(
                    metric.get("mae_pct")
                ),
                "observed_first_hit": metric.get("first_hit"),
                "full_maturity_secured_upside_pct": quality._number(
                    stage_outcome.get("secured_upside_pct")
                ),
                "full_maturity_enlarged_loss_pct": quality._number(
                    stage_outcome.get("enlarged_loss_pct")
                ),
                "full_maturity_horizon": (
                    f"{max(label.get('matured_horizons_min') or [])}m"
                    if label.get("matured_horizons_min")
                    else None
                ),
                "observed_peak_giveback_pct": (
                    round(mfe - end_return, 10)
                    if mfe is not None and end_return is not None
                    else None
                ),
                "outcome_interpretation": (
                    "same_observed_path_not_action_counterfactual"
                ),
            }
        )

    symbol_count = len(
        {str(row.get("stock_code") or "") for row in rows if row.get("stock_code")}
    )
    sample_floor_pass = (
        len(rows) >= quality.PAIRED_REPLAY_MIN_ROWS
        and symbol_count >= quality.PAIRED_REPLAY_MIN_SYMBOLS
    )

    def action_summary(action: str) -> dict[str, Any]:
        cohort = [row for row in rows if row.get("candidate_action") == action]
        summary: dict[str, Any] = {"count": len(cohort)}
        for field in (
            "observed_post_decision_end_return_pct",
            "observed_post_decision_mfe_pct",
            "observed_post_decision_mae_pct",
            "observed_peak_giveback_pct",
        ):
            values = [quality._number(row.get(field)) for row in cohort]
            values = [value for value in values if value is not None]
            summary[f"equal_weight_avg_{field}"] = fmean(values) if values else None
        return summary

    return {
        "schema": "holding_flow_outcome_attribution_v1",
        "status": (
            "outcome_observation_ready_no_counterfactual_claim"
            if sample_floor_pass
            else "sample_floor_keep_collecting"
        ),
        "sample_floor": {
            "required_decision_rows": quality.PAIRED_REPLAY_MIN_ROWS,
            "required_unique_symbols": quality.PAIRED_REPLAY_MIN_SYMBOLS,
            "observed_decision_rows": len(rows),
            "observed_unique_symbols": symbol_count,
            "pass": sample_floor_pass,
        },
        "candidate_action_counts": dict(
            Counter(str(row.get("candidate_action") or "UNKNOWN") for row in rows)
        ),
        "candidate_action_outcomes": {
            action: action_summary(action) for action in ("HOLD", "TRIM", "EXIT")
        },
        "rows": rows,
        "metric_role": "holding_flow_action_outcome_observation",
        "decision_authority": "offline_replay_no_runtime_change",
        "window_policy": "same_exact_snapshot_30m_same_venue_session",
        "primary_decision_metric": (
            "equal_weight_avg_observed_post_decision_end_return_pct_by_action"
        ),
        "source_quality_gate": "exact_v2_same_route_mature_30m_window",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "forbidden_uses": [
            "claim_observed_path_as_action_counterfactual",
            "live_holding_or_exit_promotion",
            "provider_model_route_change",
            "broker_or_hard_safety_guard_bypass",
        ],
    }


def _boolish(value: Any) -> bool:
    return value is True or str(value or "").strip().lower() in {"1", "true", "yes"}


def load_holding_flow_checkpoint_evidence(
    *,
    pipeline_path: Path,
    requests: list[dict[str, Any]],
    checkpoints_sec: tuple[int, ...] = (30, 60, 90),
    max_target_lag_sec: float = 15.0,
) -> dict[str, dict[str, Any]]:
    """Read exact executable-bid checkpoints without bar-price inference."""

    ledgers: dict[str, dict[str, Any]] = {}
    for request in requests:
        trace_id = str(request.get("decision_trace_id") or "")
        decision_at = quality._parse_ts(request.get("decision_ts"))
        if not trace_id or decision_at is None:
            continue
        ledgers[trace_id] = {
            "decision_trace_id": trace_id,
            "stock_code": str(request.get("stock_code") or ""),
            "record_id": str(request.get("record_id") or ""),
            "effective_venue": str(request.get("effective_venue") or ""),
            "session_bucket": str(request.get("session_bucket") or ""),
            "decision_at": decision_at,
            "quotes": [],
            "position_mutations": [],
        }
    if not ledgers:
        return {}

    with pipeline_path.open(encoding="utf-8") as handle:
        for line in handle:
            try:
                event = json.loads(line)
            except (TypeError, ValueError):
                continue
            if event.get("pipeline") != "HOLDING_PIPELINE":
                continue
            stock_code = str(event.get("stock_code") or "")
            event_record_id = str(event.get("record_id") or "")
            emitted_at = quality._parse_ts(event.get("emitted_at"))
            if emitted_at is None:
                continue
            fields = event.get("fields")
            fields = fields if isinstance(fields, dict) else {}
            stage = str(event.get("stage") or "")
            for ledger in ledgers.values():
                if stock_code != ledger["stock_code"]:
                    continue
                if (
                    ledger["record_id"]
                    and event_record_id
                    and event_record_id != ledger["record_id"]
                ):
                    continue
                elapsed_emitted = (emitted_at - ledger["decision_at"]).total_seconds()
                if elapsed_emitted < 0 or elapsed_emitted > max(checkpoints_sec) + 30:
                    continue
                if _boolish(fields.get("actual_order_submitted")) or stage == (
                    "scale_in_executed"
                ):
                    ledger["position_mutations"].append(
                        {
                            "stage": stage,
                            "emitted_at": emitted_at.isoformat(),
                            "elapsed_sec": round(elapsed_emitted, 6),
                            "order_no": fields.get("order_no")
                            or fields.get("ord_no")
                            or fields.get("broker_order_no"),
                            "submitted_qty": quality._number(
                                fields.get("submitted_qty") or fields.get("qty")
                            ),
                            "fill_qty": quality._number(fields.get("fill_qty")),
                            "fill_price": quality._number(fields.get("fill_price")),
                            "new_buy_qty": quality._number(fields.get("new_buy_qty")),
                            "new_avg_price": quality._number(
                                fields.get("new_avg_price")
                            ),
                        }
                    )
                if stage != "ai_holding_review":
                    continue
                if (
                    str(fields.get("holding_context_venue") or "")
                    != ledger["effective_venue"]
                ):
                    continue
                if (
                    str(fields.get("holding_context_session") or "")
                    != ledger["session_bucket"]
                ):
                    continue
                snapshot = fields.get("holding_context_ai_market_snapshot")
                if isinstance(snapshot, str):
                    try:
                        snapshot = ast.literal_eval(snapshot)
                    except (SyntaxError, ValueError):
                        continue
                if not isinstance(snapshot, dict):
                    continue
                bbo = (snapshot.get("sources") or {}).get("bbo")
                bbo = bbo if isinstance(bbo, dict) else {}
                value = bbo.get("value")
                value = value if isinstance(value, dict) else {}
                observed_at = quality._parse_ts(bbo.get("observed_at"))
                best_bid = quality._number(value.get("best_bid"))
                if (
                    str(bbo.get("quality") or "") != "fresh"
                    or observed_at is None
                    or best_bid is None
                    or best_bid <= 0
                ):
                    continue
                elapsed_observed = (observed_at - ledger["decision_at"]).total_seconds()
                if elapsed_observed < 0 or elapsed_observed > max(checkpoints_sec) + (
                    max_target_lag_sec
                ):
                    continue
                ledger["quotes"].append(
                    {
                        "observed_at": observed_at.isoformat(),
                        "emitted_at": emitted_at.isoformat(),
                        "elapsed_sec": round(elapsed_observed, 6),
                        "best_bid": best_bid,
                        "source": bbo.get("source"),
                        "quality": bbo.get("quality"),
                        "market_route": bbo.get("market_route"),
                    }
                )

    evidence: dict[str, dict[str, Any]] = {}
    for trace_id, ledger in ledgers.items():
        quotes = sorted(ledger.pop("quotes"), key=lambda row: row["elapsed_sec"])
        checkpoints: list[dict[str, Any]] = []
        for target_sec in checkpoints_sec:
            match = next(
                (
                    quote
                    for quote in quotes
                    if target_sec
                    <= quote["elapsed_sec"]
                    <= target_sec + max_target_lag_sec
                ),
                None,
            )
            checkpoints.append(
                {
                    "target_sec": target_sec,
                    "status": "available" if match else "source_unavailable",
                    "target_max_lag_sec": max_target_lag_sec,
                    "quote": (
                        {
                            **match,
                            "target_lag_sec": round(
                                match["elapsed_sec"] - target_sec, 6
                            ),
                        }
                        if match
                        else None
                    ),
                    "bar_price_inference_used": False,
                }
            )
        evidence[trace_id] = {
            **ledger,
            "decision_at": ledger["decision_at"].isoformat(),
            "checkpoints": checkpoints,
            "checkpoint_available_count": sum(
                row["status"] == "available" for row in checkpoints
            ),
            "checkpoint_required_count": len(checkpoints),
            "position_mutation_observed": bool(ledger["position_mutations"]),
        }
    return evidence


def build_holding_flow_bounded_defer_v2_2_report(
    *,
    requests: list[dict[str, Any]],
    results: list[dict[str, Any]],
    checkpoint_evidence: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Build a non-authoritative one-time defer comparison with strict provenance."""

    result_by_trace = {str(row.get("decision_trace_id") or ""): row for row in results}
    rows: list[dict[str, Any]] = []
    for request in requests:
        trace_id = str(request.get("decision_trace_id") or "")
        result = result_by_trace.get(trace_id, {})
        evidence = checkpoint_evidence.get(trace_id, {})
        immediate_bid = quality._number(
            (request.get("control") or {}).get("captured_selected_price")
        )
        checkpoints = []
        for checkpoint in evidence.get("checkpoints") or []:
            row = dict(checkpoint)
            quote = row.get("quote")
            quote = dict(quote) if isinstance(quote, dict) else None
            if quote is not None:
                quote["executable_bid_delta_pct_vs_immediate"] = (
                    round((quote["best_bid"] / immediate_bid - 1.0) * 100.0, 10)
                    if immediate_bid
                    else None
                )
            row["quote"] = quote
            checkpoints.append(row)
        complete = bool(checkpoints) and all(
            row.get("status") == "available" for row in checkpoints
        )
        mutation = evidence.get("position_mutation_observed") is True
        pure_eligible = bool(complete and not mutation and immediate_bid)
        rows.append(
            {
                "decision_trace_id": trace_id,
                "stock_code": request.get("stock_code"),
                "effective_venue": request.get("effective_venue"),
                "session_bucket": request.get("session_bucket"),
                "decision_at": request.get("decision_ts"),
                "immediate_executable_bid": immediate_bid,
                "control_action": (result.get("control_response") or {}).get("action"),
                "candidate_action": (result.get("candidate_response") or {}).get(
                    "action"
                ),
                "provider_replay_status": result.get("status"),
                "checkpoints": checkpoints,
                "checkpoint_available_count": evidence.get(
                    "checkpoint_available_count", 0
                ),
                "checkpoint_required_count": evidence.get(
                    "checkpoint_required_count", 3
                ),
                "source_runtime_position_mutation_observed": mutation,
                "source_runtime_position_mutations": evidence.get(
                    "position_mutations", []
                ),
                "pure_defer_counterfactual_eligible": pure_eligible,
                "cost_adjusted_defer_ev_pct": None,
                "cost_adjusted_defer_ev_status": (
                    "not_computed_policy_definition_pending"
                    if pure_eligible
                    else "not_available_incomplete_checkpoint_or_position_mutation"
                ),
            }
        )
    complete_rows = [row for row in rows if row["pure_defer_counterfactual_eligible"]]
    return {
        "schema": "holding_flow_bounded_defer_v2_2_manual_replay_v1",
        "status": (
            "checkpoint_source_ready_policy_definition_pending"
            if complete_rows
            else "checkpoint_source_partial_keep_collecting"
        ),
        "rows": rows,
        "eligible_counterfactual_row_count": len(complete_rows),
        "metric_role": "holding_flow_bounded_defer_counterfactual_source_quality",
        "decision_authority": "one_time_offline_replay_no_runtime_change",
        "window_policy": (
            "first_fresh_same_venue_session_executable_bid_at_or_after_"
            "30_60_90s_target_within_15s"
        ),
        "sample_floor": "one_exact_soft_exit_row_with_all_30_60_90_checkpoints",
        "primary_decision_metric": "cost_adjusted_defer_ev_pct",
        "source_quality_gate": (
            "exact_v2_fresh_quote_provenance_complete_checkpoints_no_position_mutation"
        ),
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "forbidden_uses": [
            "live_exit_delay",
            "hard_protect_emergency_or_broker_guard_bypass",
            "actual_pnl_claim",
            "completed_bar_checkpoint_price_inference",
            "provider_model_route_change",
        ],
    }


def build_entry_price_selection_outcome_comparison(
    *,
    requests: list[dict[str, Any]],
    results: list[dict[str, Any]],
    labels: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compare exact selected limits without claiming that a touch was a fill."""

    request_by_trace = {
        str(row.get("decision_trace_id") or ""): row for row in requests
    }
    label_by_trace = {
        str(row.get("decision_trace_id") or ""): row
        for row in labels
        if row.get("source_quality_status") == "pass"
        and row.get("primary_cohort_eligible") is True
    }
    rows: list[dict[str, Any]] = []

    def price_path(
        *,
        selected_price: float | None,
        reference_price: float,
        metric: dict[str, Any],
        best_bid: float | None,
        best_ask: float | None,
    ) -> dict[str, Any]:
        if selected_price is None or selected_price <= 0:
            return {
                "selected_price": None,
                "limit_touch_observed": False,
                "limit_touch_end_return_pct": 0.0,
                "limit_touch_mfe_pct": None,
                "limit_touch_mae_pct": None,
                "discount_to_best_ask_bp": None,
                "premium_to_best_bid_bp": None,
            }
        mfe = quality._number(metric.get("mfe_pct"))
        mae = quality._number(metric.get("mae_pct"))
        end_return = quality._number(metric.get("end_return_pct"))
        if mfe is None or mae is None or end_return is None:
            raise ValueError("entry_price_10m_path_metric_missing")
        observed_high = reference_price * (1.0 + mfe / 100.0)
        observed_low = reference_price * (1.0 + mae / 100.0)
        observed_end = reference_price * (1.0 + end_return / 100.0)
        touched = observed_low <= selected_price
        return {
            "selected_price": selected_price,
            "limit_touch_observed": touched,
            "limit_touch_end_return_pct": (
                ((observed_end / selected_price) - 1.0) * 100.0 if touched else 0.0
            ),
            "limit_touch_mfe_pct": (
                ((observed_high / selected_price) - 1.0) * 100.0 if touched else None
            ),
            "limit_touch_mae_pct": (
                ((observed_low / selected_price) - 1.0) * 100.0 if touched else None
            ),
            "discount_to_best_ask_bp": (
                ((best_ask - selected_price) / best_ask) * 10000.0
                if best_ask is not None and best_ask > 0
                else None
            ),
            "premium_to_best_bid_bp": (
                ((selected_price - best_bid) / best_bid) * 10000.0
                if best_bid is not None and best_bid > 0
                else None
            ),
        }

    for result in results:
        if (
            result.get("status") != "pass"
            or result.get("same_payload_confirmed") is not True
        ):
            continue
        trace_id = str(result.get("decision_trace_id") or "")
        request = request_by_trace.get(trace_id)
        label = label_by_trace.get(trace_id)
        if not request or not label:
            continue
        metric = (label.get("horizon_metrics") or {}).get("10m")
        metric = metric if isinstance(metric, dict) else {}
        reference_price = quality._number(label.get("reference_price"))
        if reference_price is None or reference_price <= 0 or not metric:
            continue
        control = request.get("control") or {}
        candidate = result.get("candidate_response") or {}
        control_price = quality._number(control.get("captured_selected_price"))
        candidate_price = (
            None
            if str(candidate.get("action") or "").upper() == "SKIP"
            else quality._number(candidate.get("selected_price"))
        )
        facts = quality._entry_price_contract_facts(request.get("exact_payload"))
        best_bid = quality._number(facts["candidate_prices"].get("BEST_BID"))
        best_ask = quality._number(facts["candidate_prices"].get("BEST_ASK"))
        control_path = price_path(
            selected_price=control_price,
            reference_price=reference_price,
            metric=metric,
            best_bid=best_bid,
            best_ask=best_ask,
        )
        candidate_path = price_path(
            selected_price=candidate_price,
            reference_price=reference_price,
            metric=metric,
            best_bid=best_bid,
            best_ask=best_ask,
        )
        profit_opportunity = bool(metric.get("profit_opportunity_observed"))
        control_exposure_selected = bool(
            str(control.get("captured_action") or "").upper() != "SKIP"
            and control_price is not None
        )
        candidate_exposure_selected = bool(
            str(candidate.get("action") or "").upper() != "SKIP"
            and candidate_price is not None
        )
        rows.append(
            {
                "decision_trace_id": trace_id,
                "stock_code": request.get("stock_code"),
                "effective_venue": request.get("effective_venue"),
                "session_bucket": request.get("session_bucket"),
                "control_action": control.get("captured_action"),
                "candidate_action": candidate.get("action"),
                "candidate_price_basis": candidate.get("price_basis"),
                "control_exposure_selected": control_exposure_selected,
                "candidate_exposure_selected": candidate_exposure_selected,
                "exposure_selection_changed": (
                    control_exposure_selected != candidate_exposure_selected
                ),
                "reference_price": reference_price,
                "observed_10m_mfe_pct_from_reference": quality._number(
                    metric.get("mfe_pct")
                ),
                "observed_10m_mae_pct_from_reference": quality._number(
                    metric.get("mae_pct")
                ),
                "control": control_path,
                "candidate": candidate_path,
                "candidate_vs_control_price_bp": (
                    ((candidate_price - control_price) / control_price) * 10000.0
                    if candidate_price is not None
                    and control_price is not None
                    and control_price > 0
                    else None
                ),
                "control_missed_touch_opportunity": bool(
                    profit_opportunity and not control_path["limit_touch_observed"]
                ),
                "candidate_missed_touch_opportunity": bool(
                    profit_opportunity and not candidate_path["limit_touch_observed"]
                ),
            }
        )

    def aggregate(values: list[dict[str, Any]]) -> dict[str, Any]:
        if not values:
            return {"comparable_count": 0}
        control_values = [
            float(row["control"]["limit_touch_end_return_pct"]) for row in values
        ]
        candidate_values = [
            float(row["candidate"]["limit_touch_end_return_pct"]) for row in values
        ]
        control_discounts = [
            quality._number(row["control"].get("discount_to_best_ask_bp"))
            for row in values
        ]
        control_discounts = [value for value in control_discounts if value is not None]
        candidate_discounts = [
            quality._number(row["candidate"].get("discount_to_best_ask_bp"))
            for row in values
        ]
        candidate_discounts = [
            value for value in candidate_discounts if value is not None
        ]
        price_deltas = [
            quality._number(row.get("candidate_vs_control_price_bp")) for row in values
        ]
        price_deltas = [value for value in price_deltas if value is not None]
        return {
            "comparable_count": len(values),
            "control_limit_touch_count": sum(
                row["control"]["limit_touch_observed"] for row in values
            ),
            "candidate_limit_touch_count": sum(
                row["candidate"]["limit_touch_observed"] for row in values
            ),
            "control_equal_weight_avg_10m_limit_touch_end_return_pct": fmean(
                control_values
            ),
            "candidate_equal_weight_avg_10m_limit_touch_end_return_pct": fmean(
                candidate_values
            ),
            "delta_equal_weight_avg_10m_limit_touch_end_return_pct": (
                fmean(candidate_values) - fmean(control_values)
            ),
            "control_avg_discount_to_best_ask_bp": (
                fmean(control_discounts) if control_discounts else None
            ),
            "candidate_avg_discount_to_best_ask_bp": (
                fmean(candidate_discounts) if candidate_discounts else None
            ),
            "candidate_more_aggressive_price_count": sum(
                value > 0 for value in price_deltas
            ),
            "candidate_same_price_count": sum(value == 0 for value in price_deltas),
            "candidate_more_passive_price_count": sum(
                value < 0 for value in price_deltas
            ),
            "candidate_economically_distinct_price_count": sum(
                abs(value) > 1e-9 for value in price_deltas
            ),
            "candidate_exposure_selection_change_count": sum(
                row["exposure_selection_changed"] for row in values
            ),
            "candidate_economic_decision_change_count": sum(
                row["exposure_selection_changed"]
                or (
                    quality._number(row.get("candidate_vs_control_price_bp"))
                    is not None
                    and abs(float(row["candidate_vs_control_price_bp"])) > 1e-9
                )
                for row in values
            ),
            "candidate_action_only_relabel_count": sum(
                str(row.get("candidate_action") or "").upper()
                != str(row.get("control_action") or "").upper()
                and not row["exposure_selection_changed"]
                and quality._number(row.get("candidate_vs_control_price_bp"))
                is not None
                and abs(float(row["candidate_vs_control_price_bp"])) <= 1e-9
                for row in values
            ),
            "control_missed_touch_opportunity_count": sum(
                row["control_missed_touch_opportunity"] for row in values
            ),
            "candidate_missed_touch_opportunity_count": sum(
                row["candidate_missed_touch_opportunity"] for row in values
            ),
        }

    venue_rows: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        venue_rows.setdefault(str(row.get("effective_venue") or "UNKNOWN"), []).append(
            row
        )
    summary = aggregate(rows)
    venue_summary = {
        venue: aggregate(cohort) for venue, cohort in sorted(venue_rows.items())
    }
    quality_checks = {
        "all_results_comparable": bool(rows) and len(rows) == len(requests),
        "limit_touch_end_return_improved": bool(
            quality._number(
                summary.get("delta_equal_weight_avg_10m_limit_touch_end_return_pct")
            )
            is not None
            and summary["delta_equal_weight_avg_10m_limit_touch_end_return_pct"] > 0
        ),
        "missed_touch_opportunity_not_increased": bool(
            summary.get("candidate_missed_touch_opportunity_count", 0)
            <= summary.get("control_missed_touch_opportunity_count", 0)
        ),
        "limit_touch_count_not_decreased": bool(
            summary.get("candidate_limit_touch_count", 0)
            >= summary.get("control_limit_touch_count", 0)
        ),
        "all_venue_end_return_not_decreased": bool(venue_summary)
        and all(
            quality._number(
                value.get("delta_equal_weight_avg_10m_limit_touch_end_return_pct")
            )
            is not None
            and value["delta_equal_weight_avg_10m_limit_touch_end_return_pct"] >= 0
            for value in venue_summary.values()
        ),
        "price_selection_effect_observed": bool(
            summary.get("candidate_economic_decision_change_count", 0) > 0
        ),
        "action_only_relabel_absent": bool(
            summary.get("candidate_action_only_relabel_count", 0) == 0
        ),
    }
    quality_gate_pass = all(quality_checks.values())
    return {
        "schema": "entry_price_selection_outcome_comparison_v1",
        "status": (
            "candidate_quality_pass_offline_only"
            if quality_gate_pass
            else "candidate_quality_rejected" if rows else "no_comparable_rows"
        ),
        "quality_gate_pass": quality_gate_pass,
        "quality_checks": quality_checks,
        "summary": summary,
        "venue_summary": venue_summary,
        "rows": rows,
        "metric_role": "entry_price_selection_counterfactual",
        "decision_authority": "offline_replay_no_runtime_change",
        "window_policy": "same_exact_snapshot_10m_same_venue_session",
        "sample_floor": "one_source_quality_passing_10m_label_for_observation",
        "primary_decision_metric": ("equal_weight_avg_10m_limit_touch_end_return_pct"),
        "source_quality_gate": "exact_v2_same_route_mature_10m_window",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "limit_touch_semantics": (
            "price_path_touch_is_counterfactual_fill_opportunity_not_fill_proof"
        ),
        "forbidden_uses": [
            "claim_limit_touch_as_actual_fill",
            "live_prompt_or_price_promotion",
            "provider_model_route_change",
            "broker_or_safety_guard_bypass",
        ],
    }


def apply_entry_price_outcome_status(
    report: dict[str, Any], comparison: dict[str, Any]
) -> None:
    """Promote outcome status only after candidate execution fully completed."""

    selection_status = str(comparison.get("status") or "no_comparable_rows")
    report["entry_price_selection_outcome_status"] = selection_status
    if report.get("status") == "coverage_replay_complete_outcome_comparison_pending":
        report["status"] = f"coverage_replay_complete_{selection_status}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    parser.add_argument("--source-date", action="append", required=True)
    parser.add_argument(
        "--stage",
        choices=("entry", "holding", "holding_flow", "entry_price"),
        required=True,
    )
    parser.add_argument("--max-rows", type=int, required=True)
    parser.add_argument("--execute-candidate", action="store_true")
    parser.add_argument("--candidate-workers", type=int, default=4)
    parser.add_argument("--effective-venue")
    parser.add_argument("--session-bucket")
    parser.add_argument(
        "--reuse-report",
        action="append",
        type=Path,
        default=[],
        help=(
            "Reuse only PASS rows whose pair, payload, candidate, and input hashes "
            "match the current frozen cohort. May be supplied more than once."
        ),
    )
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
    parser.add_argument(
        "--holding-flow-checkpoint-source",
        type=Path,
        help=(
            "Attach strict 30/60/90-second same-route executable-bid evidence "
            "for a one-time holding-flow V2.2 replay."
        ),
    )
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    if args.max_rows <= 0:
        parser.error("--max-rows must be positive")
    if args.execute_candidate and not args.write:
        parser.error("--execute-candidate requires --write")
    if args.holding_flow_checkpoint_source and args.stage != "holding_flow":
        parser.error("--holding-flow-checkpoint-source requires --stage holding_flow")
    if args.holding_flow_checkpoint_source and not args.mature_outcomes_only:
        parser.error("--holding-flow-checkpoint-source requires --mature-outcomes-only")
    if (
        args.holding_flow_checkpoint_source
        and not args.holding_flow_checkpoint_source.is_file()
    ):
        parser.error("--holding-flow-checkpoint-source must be an existing file")
    missing_reuse_reports = [path for path in args.reuse_report if not path.is_file()]
    if missing_reuse_reports:
        parser.error(
            "--reuse-report must be an existing file: "
            + ",".join(str(path) for path in missing_reuse_reports)
        )
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
        effective_venue=args.effective_venue,
        session_bucket=args.session_bucket,
    )
    path = REPORT_DIR / f"ai_prompt_stage_coverage_replay_{args.date}_{args.stage}.json"
    reuse_reports: list[tuple[str, dict[str, Any]]] = [
        (str(path), quality._load_json(path))
    ]
    reuse_reports.extend(
        (str(reuse_path), quality._load_json(reuse_path))
        for reuse_path in args.reuse_report
        if reuse_path != path
    )
    results, reuse_sources = reusable_pass_results_from_reports(
        existing_reports=reuse_reports,
        requests=requests,
    )
    reused_pass_count = len(results)
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
    report["candidate_checkpoint_reuse"] = {
        "schema": "ai_prompt_stage_checkpoint_reuse_v1",
        "policy": "same_pair_payload_candidate_input_hash_validated_pass_only",
        "reused_pass_count": reused_pass_count,
        "sources": reuse_sources,
        "decision_authority": "offline_replay_cost_avoidance_only",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    report["cohort_filter"] = {
        "effective_venue": args.effective_venue,
        "session_bucket": args.session_bucket,
        "policy": "exact_match_before_frozen_cohort_limit",
    }
    if args.mature_outcomes_only:
        report["mature_outcomes_only"] = True
        stage_endpoint = {
            "entry": "analyze_target",
            "holding": "holding_score",
            "holding_flow": "holding_flow",
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
        if args.stage == "holding_flow":
            report["outcome_comparison_status"] = (
                "attached_dedicated_holding_flow_outcomes"
            )
            report["holding_flow_outcome_attribution"] = (
                build_holding_flow_outcome_attribution(
                    requests=requests,
                    results=results,
                    labels=labels,
                )
            )
            if (
                report["holding_flow_outcome_attribution"].get("status")
                == "sample_floor_keep_collecting"
            ):
                report["status"] = (
                    "coverage_replay_complete_sample_floor_keep_collecting"
                )
        else:
            report["outcome_comparison_status"] = "attached_mature_outcomes"
            report["outcome_comparison"] = quality.build_paired_replay_report(
                target_date=args.date,
                requests=requests,
                results=results,
                labels=labels,
            )
        if args.stage == "entry_price":
            report["entry_price_selection_outcome_comparison"] = (
                build_entry_price_selection_outcome_comparison(
                    requests=requests,
                    results=results,
                    labels=labels,
                )
            )
            apply_entry_price_outcome_status(
                report,
                report["entry_price_selection_outcome_comparison"],
            )
    if args.holding_flow_checkpoint_source:
        checkpoint_evidence = load_holding_flow_checkpoint_evidence(
            pipeline_path=args.holding_flow_checkpoint_source,
            requests=requests,
        )
        report["holding_flow_bounded_defer_v2_2"] = (
            build_holding_flow_bounded_defer_v2_2_report(
                requests=requests,
                results=results,
                checkpoint_evidence=checkpoint_evidence,
            )
        )
        report["status"] = (
            "coverage_replay_complete_"
            + report["holding_flow_bounded_defer_v2_2"]["status"]
        )
    if args.write:
        quality._atomic_write_json(path, report)
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
