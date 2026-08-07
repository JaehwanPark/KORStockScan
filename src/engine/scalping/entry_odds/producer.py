"""Produce outcome-blind raw entry odds from immutable historical payloads.

This module is an offline-only data producer.  It selects mature-label-capable
traces only to avoid spending calls on rows that cannot be evaluated, but it
never includes the observed label, original action, score, or later market
data in the model request.  The request contains only the immutable exact AI
payload captured at the decision timestamp and the fixed V1 odds contract.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import tempfile
import time
from collections import Counter
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence
from zoneinfo import ZoneInfo

from src.engine.scalping.entry_odds.observer import (
    OUTCOME_LABELS,
    RAW_PREDICTION_SCHEMA,
)
from src.utils.constants import CONFIG_PATH, DEV_PATH

KST = ZoneInfo("Asia/Seoul")

PRODUCER_SCHEMA = "entry_odds_raw_prediction_producer_v1"
INPUT_SCHEMA_VERSION = "entry_odds_exact_historical_payload_v1"
ODDS_POLICY_VERSION = "entry_odds_raw_probability_policy_v1"
OUTCOME_LABEL_VERSION = "tight_stop_entry_path_v1"
OUTCOME_HORIZON = "10m"
OUTCOME_TARGET_BPS = 30.0
OUTCOME_ADVERSE_BPS = -70.0
COST_MODEL_VERSION = "explicit_2026_tax_quote_spread_assumption_v1"
DEFAULT_MODEL = "gpt-5-nano"
DEFAULT_MAX_OUTPUT_TOKENS = 1200

MODEL_INSTRUCTIONS = """You are an offline market-path odds estimator.
Estimate a four-class probability distribution and conditional 10-minute
horizon-close gross returns from only the immutable decision-time payload.
Do not infer from or reproduce the prior trading action. Do not decide BUY,
BET, NO_BET, position size, order price, or runtime policy. Do not assume any
future observation. The four probabilities must be finite, non-negative, and
sum to 1. TARGET_FIRST payoff must be positive; ADVERSE_FIRST payoff must be
negative; NEITHER_POSITIVE payoff must be positive; NEITHER_NONPOSITIVE payoff
must be zero or negative. Fill probability is for a counterfactual one-share
entry at the captured reference price. Return exactly the requested JSON.
"""

OPENAI_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "raw_probabilities": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                label: {"type": "number", "minimum": 0.0, "maximum": 1.0}
                for label in OUTCOME_LABELS
            },
            "required": list(OUTCOME_LABELS),
        },
        "payoff_bps": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                label: {"type": "number", "minimum": -1000.0, "maximum": 1000.0}
                for label in OUTCOME_LABELS
            },
            "required": list(OUTCOME_LABELS),
        },
        "counterfactual_fill_probability": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0,
        },
        "counterfactual_fill_state": {
            "type": "string",
            "enum": ["FULL", "PARTIAL", "NO_FILL", "UNKNOWN"],
        },
    },
    "required": [
        "raw_probabilities",
        "payoff_bps",
        "counterfactual_fill_probability",
        "counterfactual_fill_state",
    ],
}

PROMPT_SHA256 = hashlib.sha256(
    json.dumps(
        {"instructions": MODEL_INSTRUCTIONS, "schema": OPENAI_RESPONSE_SCHEMA},
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
).hexdigest()


def _number(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _nested(value: Any, *path: str) -> Any:
    current = value
    for key in path:
        if not isinstance(current, Mapping):
            return None
        current = current.get(key)
    return current


def _iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"invalid JSONL row at {path}:{line_number}: {exc.msg}"
                ) from exc
            if not isinstance(value, dict):
                raise ValueError(f"JSONL row is not an object: {path}:{line_number}")
            yield value


def _read_labels(path: Path) -> list[dict[str, Any]]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid outcome label JSON: {path}: {exc.msg}") from exc
    rows = value.get("labels") if isinstance(value, dict) else None
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError(f"outcome label collection is invalid: {path}")
    return [dict(row) for row in rows]


def _eligible_label_ids(
    rows: Iterable[Mapping[str, Any]],
) -> tuple[set[str], Counter[str]]:
    input_rows = [dict(row) for row in rows]
    counts = Counter(str(row.get("decision_trace_id") or "") for row in input_rows)
    eligible: set[str] = set()
    exclusions: Counter[str] = Counter()
    for row in input_rows:
        trace_id = str(row.get("decision_trace_id") or "")
        stage = str(row.get("decision_stage") or "")
        outcome = row.get("stage_outcome")
        if not trace_id:
            exclusions["label_trace_id_missing"] += 1
        elif counts[trace_id] > 1:
            exclusions["label_trace_id_duplicate"] += 1
        elif stage not in {"entry", "entry_screen"}:
            exclusions["label_not_entry_stage"] += 1
        elif row.get("label_status") != "mature":
            exclusions["label_not_mature"] += 1
        elif str(row.get("source_quality_status") or "").lower() != "pass":
            exclusions["label_source_quality_not_pass"] += 1
        elif row.get("primary_cohort_eligible") is not True:
            exclusions["label_primary_cohort_ineligible"] += 1
        elif row.get("invalid_reasons"):
            exclusions["label_invalid_reasons_present"] += 1
        elif not isinstance(outcome, Mapping):
            exclusions["label_stage_outcome_missing"] += 1
        elif outcome.get("entry_path_label_version") != OUTCOME_LABEL_VERSION:
            exclusions["label_contract_version_mismatch"] += 1
        elif outcome.get("entry_path_primary_horizon") != OUTCOME_HORIZON:
            exclusions["label_contract_horizon_mismatch"] += 1
        elif _number(outcome.get("entry_path_target_pct")) != (
            OUTCOME_TARGET_BPS / 100.0
        ):
            exclusions["label_contract_target_mismatch"] += 1
        elif _number(outcome.get("entry_path_adverse_pct")) != (
            OUTCOME_ADVERSE_BPS / 100.0
        ):
            exclusions["label_contract_adverse_mismatch"] += 1
        elif outcome.get("entry_path_first_hit") == "same_bar_ambiguous":
            exclusions["label_same_bar_ambiguous"] += 1
        else:
            eligible.add(trace_id)
    return eligible, exclusions


def _trace_eligible(row: Mapping[str, Any], target_date: str) -> str | None:
    if row.get("decision_stage") not in {"entry", "entry_screen"}:
        return "trace_not_entry_stage"
    if str(row.get("decision_ts") or "")[:10] != target_date:
        return "trace_target_date_mismatch"
    if row.get("payload_replay_exact") is not True:
        return "trace_payload_not_exact"
    if row.get("input_preflight_allowed") is not True:
        return "trace_input_preflight_not_allowed"
    if str(row.get("input_preflight_status") or "").lower() not in {
        "fresh_consistent",
        "pass",
    }:
        return "trace_input_not_fresh_consistent"
    if not row.get("payload_sha256"):
        return "trace_payload_sha256_missing"
    if not row.get("request_envelope_sha256"):
        return "trace_request_envelope_sha256_missing"
    return None


def select_exact_payload_jobs(
    *,
    target_date: str,
    traces: Iterable[Mapping[str, Any]],
    payloads: Iterable[Mapping[str, Any]],
    outcome_labels: Iterable[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Return outcome-blind model jobs bound to unique exact source payloads."""

    label_ids, exclusions = _eligible_label_ids(outcome_labels)
    trace_rows = [dict(row) for row in traces]
    trace_counts = Counter(
        str(row.get("decision_trace_id") or "") for row in trace_rows
    )
    trace_by_request: dict[str, dict[str, Any]] = {}
    duplicate_trace_requests: set[str] = set()
    for trace in trace_rows:
        trace_id = str(trace.get("decision_trace_id") or "")
        if trace_id not in label_ids:
            continue
        if trace_counts[trace_id] > 1:
            exclusions["trace_id_duplicate"] += 1
            continue
        if error := _trace_eligible(trace, target_date):
            exclusions[error] += 1
            continue
        request_sha = str(trace.get("request_envelope_sha256") or "")
        if request_sha in duplicate_trace_requests:
            continue
        if request_sha in trace_by_request:
            exclusions["trace_request_envelope_duplicate"] += 1
            trace_by_request.pop(request_sha, None)
            duplicate_trace_requests.add(request_sha)
            continue
        trace_by_request[request_sha] = trace

    jobs: list[dict[str, Any]] = []
    matched_requests: Counter[str] = Counter()
    for payload in payloads:
        request_sha = str(payload.get("request_envelope_sha256") or "")
        trace = trace_by_request.get(request_sha)
        if trace is None:
            continue
        matched_requests[request_sha] += 1
        if matched_requests[request_sha] > 1:
            continue
        if payload.get("replay_exact") is not True:
            exclusions["payload_replay_not_exact"] += 1
            continue
        if (
            payload.get("redacted") is not False
            or payload.get("raw_secret_storage") is not False
            or payload.get("sensitive_value_policy")
            != "key_and_embedded_credential_redaction_v2"
            or payload.get("storage_security_policy") != "ai_trace_payload_security_v2"
        ):
            exclusions["payload_redaction_contract_invalid"] += 1
            continue
        if str(payload.get("payload_sha256") or "") != str(
            trace.get("payload_sha256") or ""
        ):
            exclusions["payload_sha256_mismatch"] += 1
            continue
        exact_input = payload.get("sanitized_user_input")
        if not isinstance(exact_input, (dict, list, str)):
            exclusions["payload_sanitized_user_input_missing"] += 1
            continue
        jobs.append(
            {
                "trace": trace,
                "payload": dict(payload),
                "exact_input": exact_input,
            }
        )

    duplicate_payload_requests = {
        request_sha for request_sha, count in matched_requests.items() if count > 1
    }
    if duplicate_payload_requests:
        exclusions["payload_request_envelope_duplicate"] += len(
            duplicate_payload_requests
        )
        jobs = [
            job
            for job in jobs
            if str(job["payload"].get("request_envelope_sha256") or "")
            not in duplicate_payload_requests
        ]
    matched = {str(job["payload"].get("request_envelope_sha256") or "") for job in jobs}
    exclusions["exact_payload_missing"] += len(set(trace_by_request) - matched)
    jobs.sort(key=lambda job: str(job["trace"].get("decision_ts") or ""))
    return jobs, dict(sorted(exclusions.items()))


def _cohort_value(exact_input: Any, *paths: tuple[str, ...]) -> str:
    for path in paths:
        value = _nested(exact_input, *path)
        if value not in (None, ""):
            return str(value).strip().upper()
    return "UNCLASSIFIED"


def _spread_bps(exact_input: Any) -> float | None:
    for path in (
        ("exact_payload", "quote", "spread_bp"),
        ("exact_payload", "features", "spread_bp"),
        ("exact_payload_analysis_v1", "executable_liquidity", "spread_bp"),
    ):
        value = _number(_nested(exact_input, *path))
        if value is not None and value >= 0.0:
            return value
    return None


def _cost_inputs(trace: Mapping[str, Any], exact_input: Any) -> dict[str, Any]:
    spread = _spread_bps(exact_input)
    if spread is None:
        raise ValueError("exact_payload_spread_bps_missing")
    price_basis = str(trace.get("reference_price_type") or "")
    includes_entry_spread = price_basis in {"executable_ask", "resolved_order_price"}
    return {
        "tax_bps": 20.0,
        "commission_buy_bps": 0.0,
        "commission_sell_bps": 0.0,
        "entry_spread_bps": 0.0 if includes_entry_spread else round(spread / 2.0, 6),
        "exit_spread_bps": round(spread / 2.0, 6),
        "slippage_buy_bps": 0.0,
        "slippage_sell_bps": 0.0,
        "market_impact_bps": 0.0,
        "entry_price_basis": price_basis,
        "price_basis_includes_entry_spread": includes_entry_spread,
        "listing_market": "KOSPI_OR_KOSDAQ_NOT_DISTINGUISHED",
        "execution_venue": str(trace.get("broker_route") or "").upper(),
        "instrument_tax_class": "taxable_listed_common_stock_assumed",
        "effective_from": "2026-01-01",
        "effective_to": "2026-12-31",
        "cost_source_quality_status": "assumption_only",
        "assumption_flags": [
            "listing_market_not_distinguished_same_20bp_2026_tax_rate",
            "commission_assumed_zero",
            "slippage_assumed_zero_beyond_observed_spread",
            "one_share_market_impact_assumed_zero",
            "exit_half_spread_uses_decision_time_quote",
        ],
        "source_spread_bps": round(spread, 6),
    }


def _normalize_model_payload(value: Mapping[str, Any]) -> dict[str, Any]:
    probabilities_value = value.get("raw_probabilities")
    if not isinstance(probabilities_value, Mapping):
        raise ValueError("model_probabilities_missing")
    probabilities: dict[str, float] = {}
    for label in OUTCOME_LABELS:
        number = _number(probabilities_value.get(label))
        if number is None or number < 0.0 or number > 1.0:
            raise ValueError(f"model_probability_invalid:{label}")
        probabilities[label] = number
    total = sum(probabilities.values())
    if total <= 0.0:
        raise ValueError("model_probability_sum_zero")
    normalized = {label: probabilities[label] / total for label in OUTCOME_LABELS}

    payoff_value = value.get("payoff_bps")
    if not isinstance(payoff_value, Mapping):
        raise ValueError("model_payoff_missing")
    payoff: dict[str, float] = {}
    for label in OUTCOME_LABELS:
        number = _number(payoff_value.get(label))
        if number is None:
            raise ValueError(f"model_payoff_invalid:{label}")
        payoff[label] = number
    if payoff["TARGET_FIRST"] <= 0.0:
        raise ValueError("model_target_payoff_not_positive")
    if payoff["ADVERSE_FIRST"] >= 0.0:
        raise ValueError("model_adverse_payoff_not_negative")
    if payoff["NEITHER_POSITIVE"] <= 0.0:
        raise ValueError("model_neither_positive_payoff_not_positive")
    if payoff["NEITHER_NONPOSITIVE"] > 0.0:
        raise ValueError("model_neither_nonpositive_payoff_positive")

    fill_probability = _number(value.get("counterfactual_fill_probability"))
    if fill_probability is None or not 0.0 <= fill_probability <= 1.0:
        raise ValueError("model_fill_probability_invalid")
    fill_state = str(value.get("counterfactual_fill_state") or "")
    if fill_state not in {"FULL", "PARTIAL", "NO_FILL", "UNKNOWN"}:
        raise ValueError("model_fill_state_invalid")

    entropy = -sum(
        probability * math.log(probability)
        for probability in normalized.values()
        if probability > 0.0
    )
    normalized_entropy = entropy / math.log(len(OUTCOME_LABELS))
    hurdle_components = {
        "model_uncertainty": round(12.0 * normalized_entropy, 6),
        "tail_risk": 0.0,
        "operational_buffer": 3.0,
    }
    return {
        "raw_probabilities": {
            label: round(normalized[label], 10) for label in OUTCOME_LABELS
        },
        "probability_normalization_scale": round(total, 10),
        "payoff_bps": {label: round(payoff[label], 6) for label in OUTCOME_LABELS},
        "counterfactual_fill_probability": round(fill_probability, 10),
        "counterfactual_fill_state": fill_state,
        "uncertainty_hurdle_components_bps": hurdle_components,
        "uncertainty_hurdle_bps": round(sum(hurdle_components.values()), 6),
        "prediction_entropy_normalized": round(normalized_entropy, 10),
    }


def build_prediction_row(
    *,
    job: Mapping[str, Any],
    model_payload: Mapping[str, Any],
    provider_provenance: Mapping[str, Any],
    model: str,
) -> dict[str, Any]:
    trace = job.get("trace")
    payload = job.get("payload")
    exact_input = job.get("exact_input")
    if not isinstance(trace, Mapping) or not isinstance(payload, Mapping):
        raise ValueError("invalid_exact_payload_job")
    normalized = _normalize_model_payload(model_payload)
    execution_venue = str(trace.get("broker_route") or "").upper()
    effective_venue = str(trace.get("effective_venue") or "").upper()
    session_bucket = str(trace.get("session_bucket") or "").upper()
    if not execution_venue or not effective_venue or not session_bucket:
        raise ValueError("trace_route_or_session_missing")
    row = {
        "schema": RAW_PREDICTION_SCHEMA,
        "decision_trace_id": trace.get("decision_trace_id"),
        "decision_ts": trace.get("decision_ts"),
        "stock_code": trace.get("stock_code"),
        "source_quality_status": "pass",
        "odds_provenance": {
            "provider_actual": "openai",
            "model_id": model,
            "prompt_sha256": PROMPT_SHA256,
            "input_schema_version": INPUT_SCHEMA_VERSION,
            "odds_policy_version": ODDS_POLICY_VERSION,
            "outcome_label_version": OUTCOME_LABEL_VERSION,
            "outcome_horizon": OUTCOME_HORIZON,
            "outcome_target_bps": OUTCOME_TARGET_BPS,
            "outcome_adverse_bps": OUTCOME_ADVERSE_BPS,
            "cost_model_version": COST_MODEL_VERSION,
            "execution_venue": execution_venue,
            "effective_venue": effective_venue,
            "session_bucket": session_bucket,
            "risk_regime": _cohort_value(
                exact_input,
                ("exact_payload", "entry_candle_context", "regime"),
                ("exact_payload_analysis_v1", "completed_structure", "regime"),
            ),
            "liquidity_bucket": _cohort_value(
                exact_input,
                ("exact_payload", "features", "entry_liquidity_status"),
            ),
            "source_payload_sha256": trace.get("payload_sha256"),
            "source_request_envelope_sha256": trace.get("request_envelope_sha256"),
            "source_payload_store_schema": payload.get("schema"),
            "source_payload_replay_exact": payload.get("replay_exact"),
            "model_request_outcome_blind": True,
            "original_action_excluded_from_model_input": True,
        },
        **normalized,
        "cost_inputs": _cost_inputs(trace, exact_input),
        "provider_provenance": dict(provider_provenance),
        "metric_role": "offline_entry_odds_raw_probability_source",
        "decision_authority": "counterfactual_source_only",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    return row


def _request_input(job: Mapping[str, Any]) -> str:
    trace = job["trace"]
    value = {
        "contract": {
            "labels": list(OUTCOME_LABELS),
            "horizon": OUTCOME_HORIZON,
            "target_bps": OUTCOME_TARGET_BPS,
            "adverse_bps": OUTCOME_ADVERSE_BPS,
            "payoff_definition": (
                "gross 10-minute horizon-close return conditional on each label"
            ),
            "costs_excluded": True,
            "counterfactual_quantity_shares": 1,
        },
        "immutable_source": {
            "decision_trace_id": trace.get("decision_trace_id"),
            "decision_ts": trace.get("decision_ts"),
            "stock_code": trace.get("stock_code"),
            "payload_sha256": trace.get("payload_sha256"),
            "execution_venue": trace.get("broker_route"),
            "effective_venue": trace.get("effective_venue"),
            "session_bucket": trace.get("session_bucket"),
            "reference_price": trace.get("reference_price"),
            "reference_price_type": trace.get("reference_price_type"),
        },
        "exact_historical_ai_payload": job["exact_input"],
    }
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def _usage_value(response: Any, name: str) -> int | None:
    usage = getattr(response, "usage", None)
    if usage is None and isinstance(response, Mapping):
        usage = response.get("usage")
    value = getattr(usage, name, None)
    if value is None and isinstance(usage, Mapping):
        value = usage.get(name)
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _response_text(response: Any) -> str:
    value = getattr(response, "output_text", None)
    if value is None and isinstance(response, Mapping):
        value = response.get("output_text")
    if not isinstance(value, str) or not value.strip():
        raise ValueError("openai_response_output_text_missing")
    return value


def _call_openai(
    *,
    job: Mapping[str, Any],
    api_key: str,
    model: str,
    timeout_sec: float,
    max_output_tokens: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    from openai import OpenAI

    started = time.perf_counter()
    client = OpenAI(api_key=api_key, max_retries=0)
    response = client.responses.create(
        model=model,
        instructions=MODEL_INSTRUCTIONS,
        input=_request_input(job),
        text={
            "format": {
                "type": "json_schema",
                "name": "entry_odds_raw_probability_v1",
                "strict": True,
                "schema": OPENAI_RESPONSE_SCHEMA,
            },
            "verbosity": "low",
        },
        reasoning={"effort": "low"},
        max_output_tokens=max_output_tokens,
        store=False,
        metadata={
            "decision_trace_id_sha256": hashlib.sha256(
                str(job["trace"].get("decision_trace_id") or "").encode("utf-8")
            ).hexdigest(),
            "odds_policy_version": ODDS_POLICY_VERSION,
            "runtime_effect": "false",
        },
        timeout=max(1.0, timeout_sec),
    )
    raw_text = _response_text(response)
    try:
        model_payload = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ValueError("openai_response_json_invalid") from exc
    if not isinstance(model_payload, dict):
        raise ValueError("openai_response_not_object")
    response_id = getattr(response, "id", None)
    if response_id is None and isinstance(response, Mapping):
        response_id = response.get("id")
    provenance = {
        "provider": "openai",
        "model": model,
        "transport": "openai_responses_http_offline",
        "reasoning_effort": "low",
        "response_id": str(response_id or "") or None,
        "response_sha256": hashlib.sha256(raw_text.encode("utf-8")).hexdigest(),
        "latency_ms": int((time.perf_counter() - started) * 1000),
        "input_tokens": _usage_value(response, "input_tokens"),
        "output_tokens": _usage_value(response, "output_tokens"),
        "total_tokens": _usage_value(response, "total_tokens"),
        "store": False,
    }
    return model_payload, provenance


def _configured_api_keys() -> list[str]:
    target = CONFIG_PATH if CONFIG_PATH.exists() else DEV_PATH
    try:
        value = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(value, dict):
        return []
    return [
        str(item)
        for name, item in sorted(value.items())
        if str(name).startswith("OPENAI_API_KEY") and item not in (None, "", "-")
    ]


def _atomic_write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    descriptor, temp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp_name, 0o600)
        os.replace(temp_name, path)
    finally:
        Path(temp_name).unlink(missing_ok=True)


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _append_jsonl(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    with os.fdopen(descriptor, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.chmod(path, 0o600)


def _run_one(
    *,
    job: Mapping[str, Any],
    keys: Sequence[str],
    key_start: int,
    model: str,
    timeout_sec: float,
    max_output_tokens: int,
    retry_attempts: int,
    caller: Callable[..., tuple[dict[str, Any], dict[str, Any]]],
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    trace_id = str(job["trace"].get("decision_trace_id") or "")
    last_error = ""
    for attempt in range(1, retry_attempts + 1):
        try:
            model_payload, provenance = caller(
                job=job,
                api_key=keys[(key_start + attempt - 1) % len(keys)],
                model=model,
                timeout_sec=timeout_sec,
                max_output_tokens=max_output_tokens,
            )
            row = build_prediction_row(
                job=job,
                model_payload=model_payload,
                provider_provenance={**provenance, "attempt": attempt},
                model=model,
            )
            return row, {
                "decision_trace_id": trace_id,
                "status": "success",
                "attempts": attempt,
            }
        except Exception as exc:
            error_text = re.sub(r"sk-[A-Za-z0-9_-]{8,}", "[REDACTED_API_KEY]", str(exc))
            last_error = f"{type(exc).__name__}:{error_text[:300]}"
            if attempt < retry_attempts:
                time.sleep(min(2.0**attempt, 8.0))
    return None, {
        "decision_trace_id": trace_id,
        "status": "failed",
        "attempts": retry_attempts,
        "error": last_error,
    }


def produce(
    *,
    target_date: str,
    traces_path: Path,
    payloads_path: Path,
    outcomes_path: Path,
    output_path: Path,
    manifest_path: Path,
    execute_openai: bool,
    model: str = DEFAULT_MODEL,
    max_rows: int = 0,
    workers: int = 4,
    timeout_sec: float = 90.0,
    max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS,
    retry_attempts: int = 3,
    caller: Callable[..., tuple[dict[str, Any], dict[str, Any]]] = _call_openai,
) -> dict[str, Any]:
    for path in (traces_path, payloads_path, outcomes_path):
        if not path.exists():
            raise FileNotFoundError(f"required raw-odds source missing: {path}")
    jobs, exclusions = select_exact_payload_jobs(
        target_date=target_date,
        traces=_iter_jsonl(traces_path),
        payloads=_iter_jsonl(payloads_path),
        outcome_labels=_read_labels(outcomes_path),
    )
    existing_rows = list(_iter_jsonl(output_path)) if output_path.exists() else []
    for row in existing_rows:
        if row.get("schema") != RAW_PREDICTION_SCHEMA:
            raise ValueError("existing raw prediction schema mismatch")
        if not row.get("decision_trace_id"):
            raise ValueError("existing raw prediction trace ID missing")
        if str(row.get("decision_ts") or "")[:10] != target_date:
            raise ValueError("existing raw prediction target date mismatch")
        provenance = row.get("odds_provenance")
        if not isinstance(provenance, Mapping):
            raise ValueError("existing raw prediction provenance missing")
        if provenance.get("model_id") != model:
            raise ValueError("existing raw prediction model mismatch")
        if provenance.get("prompt_sha256") != PROMPT_SHA256:
            raise ValueError("existing raw prediction prompt mismatch")
        if provenance.get("odds_policy_version") != ODDS_POLICY_VERSION:
            raise ValueError("existing raw prediction odds policy mismatch")
    existing_counts = Counter(
        str(row.get("decision_trace_id") or "") for row in existing_rows
    )
    duplicate_existing = sum(count > 1 for count in existing_counts.values())
    if duplicate_existing:
        raise ValueError("existing raw prediction file contains duplicate trace IDs")
    job_by_trace_id = {
        str(job["trace"].get("decision_trace_id") or ""): job for job in jobs
    }
    for row in existing_rows:
        trace_id = str(row.get("decision_trace_id") or "")
        job = job_by_trace_id.get(trace_id)
        if job is None:
            raise ValueError("existing raw prediction is outside current exact jobs")
        provenance = row["odds_provenance"]
        if provenance.get("source_payload_sha256") != job["trace"].get(
            "payload_sha256"
        ):
            raise ValueError("existing raw prediction source payload mismatch")
        if provenance.get("source_request_envelope_sha256") != job["trace"].get(
            "request_envelope_sha256"
        ):
            raise ValueError("existing raw prediction source request mismatch")
    pending = [
        job
        for job in jobs
        if str(job["trace"].get("decision_trace_id") or "") not in existing_counts
    ]
    if max_rows > 0:
        pending = pending[:max_rows]
    input_bytes = sum(len(_request_input(job).encode("utf-8")) for job in pending)
    hard_gap_names = {
        "exact_payload_missing",
        "payload_redaction_contract_invalid",
        "payload_sha256_mismatch",
        "payload_sanitized_user_input_missing",
        "payload_request_envelope_duplicate",
        "trace_id_duplicate",
        "trace_request_envelope_duplicate",
    }
    selection_hard_gap_count = sum(
        count for name, count in exclusions.items() if name in hard_gap_names
    )
    manifest: dict[str, Any] = {
        "schema": PRODUCER_SCHEMA,
        "target_date": target_date,
        "generated_at": datetime.now(KST).isoformat(),
        "mode": "execute_openai" if execute_openai else "dry_run",
        "model": model,
        "prompt_sha256": PROMPT_SHA256,
        "eligible_exact_payload_count": len(jobs),
        "existing_prediction_count": len(existing_rows),
        "planned_prediction_count": len(pending),
        "estimated_input_bytes": input_bytes,
        "estimated_input_tokens_rough": math.ceil(input_bytes / 3.0),
        "selection_exclusion_counts": exclusions,
        "selection_hard_gap_count": selection_hard_gap_count,
        "success_count": 0,
        "failure_count": 0,
        "failures": [],
        "provider_usage": {
            name: sum(
                int(value)
                for row in existing_rows
                if isinstance(
                    value := (row.get("provider_provenance") or {}).get(name), int
                )
            )
            for name in ("input_tokens", "output_tokens", "total_tokens")
        },
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    manifest["output_prediction_count"] = len(existing_rows)
    manifest["output_sha256"] = (
        _file_sha256(output_path) if output_path.exists() else None
    )
    manifest["complete"] = selection_hard_gap_count == 0 and len(existing_rows) == len(
        jobs
    )
    manifest["source_quality_status"] = (
        "pass" if selection_hard_gap_count == 0 else "exact_payload_contract_gap"
    )
    manifest["status"] = "complete" if manifest["complete"] else "dry_run_or_incomplete"
    if not execute_openai or not pending:
        _atomic_write_json(manifest_path, manifest)
        return manifest

    keys = _configured_api_keys()
    if not keys:
        raise RuntimeError("OPENAI_API_KEY not configured")
    if workers <= 0 or retry_attempts <= 0 or timeout_sec <= 0:
        raise ValueError("workers, retry_attempts, and timeout_sec must be positive")

    future_to_job: dict[Future[tuple[dict[str, Any] | None, dict[str, Any]]], int] = {}
    with ThreadPoolExecutor(max_workers=workers) as executor:
        for index, job in enumerate(pending):
            future = executor.submit(
                _run_one,
                job=job,
                keys=keys,
                key_start=index % len(keys),
                model=model,
                timeout_sec=timeout_sec,
                max_output_tokens=max_output_tokens,
                retry_attempts=retry_attempts,
                caller=caller,
            )
            future_to_job[future] = index
        for future in as_completed(future_to_job):
            row, result = future.result()
            if row is None:
                manifest["failure_count"] += 1
                manifest["failures"].append(result)
                continue
            _append_jsonl(output_path, row)
            manifest["success_count"] += 1
            provenance = row.get("provider_provenance") or {}
            for name in ("input_tokens", "output_tokens", "total_tokens"):
                value = provenance.get(name)
                if isinstance(value, int):
                    manifest["provider_usage"][name] += value

    manifest["completed_at"] = datetime.now(KST).isoformat()
    manifest["output_prediction_count"] = (
        len(list(_iter_jsonl(output_path))) if output_path.exists() else 0
    )
    manifest["output_sha256"] = (
        _file_sha256(output_path) if output_path.exists() else None
    )
    manifest["complete"] = (
        manifest["failure_count"] == 0
        and selection_hard_gap_count == 0
        and manifest["output_prediction_count"] == len(jobs)
    )
    manifest["status"] = "complete" if manifest["complete"] else "incomplete"
    manifest["failures"] = sorted(
        manifest["failures"], key=lambda row: str(row.get("decision_trace_id") or "")
    )
    _atomic_write_json(manifest_path, manifest)
    return manifest


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-date", required=True)
    parser.add_argument("--traces", type=Path)
    parser.add_argument("--payloads", type=Path)
    parser.add_argument("--outcomes", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--execute-openai", action="store_true")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--max-rows", type=int, default=0)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--timeout-sec", type=float, default=90.0)
    parser.add_argument(
        "--max-output-tokens", type=int, default=DEFAULT_MAX_OUTPUT_TOKENS
    )
    parser.add_argument("--retry-attempts", type=int, default=3)
    args = parser.parse_args(argv)
    date = args.target_date
    output = args.output or Path(
        f"data/entry_odds_observer/raw/entry_odds_raw_predictions_{date}.jsonl"
    )
    manifest = args.manifest or Path(
        f"data/entry_odds_observer/raw/entry_odds_raw_predictions_{date}.manifest.json"
    )
    report = produce(
        target_date=date,
        traces_path=args.traces
        or Path(f"data/ai_decision_trace/ai_decision_trace_{date}.jsonl"),
        payloads_path=args.payloads
        or Path(f"data/ai_decision_payloads/ai_decision_payloads_{date}.jsonl"),
        outcomes_path=args.outcomes
        or Path("data/report/ai_decision_outcome_labels")
        / f"ai_decision_outcome_labels_{date}.json",
        output_path=output,
        manifest_path=manifest,
        execute_openai=args.execute_openai,
        model=args.model,
        max_rows=args.max_rows,
        workers=args.workers,
        timeout_sec=args.timeout_sec,
        max_output_tokens=args.max_output_tokens,
        retry_attempts=args.retry_attempts,
    )
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report.get("failure_count", 0) == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
