"""Build the V1 offline entry-odds observer report.

The observer is a read-only sidecar.  Raw odds are produced outside this
module and must be linked to an immutable entry AI trace by payload SHA-256.
Calibration is chronological, exact-signature-only temperature scaling.  No
result from this module is an entry action or runtime-apply instruction.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import tempfile
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import fmean
from typing import Any, Iterable, Mapping, Sequence
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")
CLEAN_BASELINE_TS = datetime.fromisoformat("2026-06-05T00:00:00+09:00")

SCHEMA = "entry_odds_observer_v1"
ROW_SCHEMA = "entry_odds_observer_row_v1"
RAW_PREDICTION_SCHEMA = "entry_odds_raw_prediction_v1"
CALIBRATION_ROW_SCHEMA = "entry_odds_calibration_row_v1"
POLICY_VERSION = "offline_entry_odds_observer_v1"
COUNTERFACTUAL_EXECUTION_POLICY = "one_share_reference_horizon_close_v1"
LEGACY_FIXED_COST_COMPARISON_BPS = 23.0

OUTCOME_LABELS = (
    "TARGET_FIRST",
    "ADVERSE_FIRST",
    "NEITHER_POSITIVE",
    "NEITHER_NONPOSITIVE",
)
AMBIGUOUS_OUTCOME = "SAME_BAR_AMBIGUOUS"
ASSESSMENTS = ("WOULD_BET", "WOULD_NO_BET", "ABSTAIN")
COUNTERFACTUAL_FILL_STATES = ("FULL", "PARTIAL", "NO_FILL", "UNKNOWN")

DEFAULT_MIN_CALIBRATION_ROWS = 30
DEFAULT_MIN_UNIQUE_SYMBOLS = 10
DEFAULT_MIN_CALIBRATION_DATES = 2
DEFAULT_MIN_EVALUATION_ROWS = 30
DEFAULT_MIN_EVALUATION_DATES = 2
TEMPERATURE_GRID = tuple(value / 20.0 for value in range(10, 61))

METRIC_DECISION_CONTRACT: dict[str, Any] = {
    "metric_role": "entry_odds_calibration_and_counterfactual_veto_observation",
    "metric_definition": (
        "Exact-trace raw and temperature-calibrated market-path odds, explicit "
        "one-share reference execution cost, and mature counterfactual 10-minute "
        "horizon-close attribution."
    ),
    "decision_authority": "counterfactual_only",
    "window_policy": (
        "clean_baseline_chronological_prior_only_exact_signature_calibration_"
        "with_mature_10m_same_route_outcome"
    ),
    "sample_floor": {
        "calibration_rows_per_signature": DEFAULT_MIN_CALIBRATION_ROWS,
        "calibration_unique_symbols_per_signature": DEFAULT_MIN_UNIQUE_SYMBOLS,
        "calibration_source_dates_per_signature": DEFAULT_MIN_CALIBRATION_DATES,
        "oos_evaluation_rows": DEFAULT_MIN_EVALUATION_ROWS,
        "oos_evaluation_source_dates": DEFAULT_MIN_EVALUATION_DATES,
    },
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "secondary_diagnostics": [
        "multiclass_brier_score",
        "multiclass_log_loss",
        "top_label_ece",
        "hypothetical_buy_retention_pct",
        "avoided_loser_count",
        "foregone_winner_count",
    ],
    "source_quality_gate": (
        "exact_entry_trace_payload_sha_match_fresh_consistent_prediction_"
        "mature_10m_outcome_and_exact_calibration_signature"
    ),
    "runtime_effect": False,
    "allowed_runtime_apply": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
    "forbidden_uses": [
        "live_entry_action_or_score_mutation",
        "runtime_env_or_threshold_change",
        "provider_or_model_route_change",
        "order_price_quantity_or_cap_change",
        "broker_or_hard_safety_guard_bypass",
        "counterfactual_realized_pnl_merge",
        "standalone_live_or_sim_auto_promotion",
        "bot_restart",
    ],
}

REQUIRED_PROVENANCE_FIELDS = (
    "provider_actual",
    "model_id",
    "prompt_sha256",
    "input_schema_version",
    "odds_policy_version",
    "outcome_label_version",
    "outcome_horizon",
    "outcome_target_bps",
    "outcome_adverse_bps",
    "cost_model_version",
    "execution_venue",
    "effective_venue",
    "session_bucket",
    "risk_regime",
    "liquidity_bucket",
)

REQUIRED_COST_FIELDS = (
    "tax_bps",
    "commission_buy_bps",
    "commission_sell_bps",
    "entry_spread_bps",
    "exit_spread_bps",
    "slippage_buy_bps",
    "slippage_sell_bps",
    "market_impact_bps",
)
REQUIRED_COST_CONTEXT_FIELDS = (
    "listing_market",
    "execution_venue",
    "instrument_tax_class",
    "effective_from",
    "effective_to",
)
HURDLE_COMPONENT_FIELDS = (
    "model_uncertainty",
    "tail_risk",
    "operational_buffer",
)


def _number(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _parse_ts(value: Any) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        return None
    return parsed


def _round(value: float | None, digits: int = 10) -> float | None:
    return round(value, digits) if value is not None and math.isfinite(value) else None


def _sha256(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _is_sha256(value: Any) -> bool:
    text = str(value or "")
    return len(text) == 64 and all(
        character in "0123456789abcdef" for character in text.lower()
    )


def _normalized_probabilities(value: Any) -> tuple[dict[str, float] | None, list[str]]:
    if not isinstance(value, Mapping):
        return None, ["raw_probabilities_missing"]
    errors: list[str] = []
    probabilities: dict[str, float] = {}
    for label in OUTCOME_LABELS:
        probability = _number(value.get(label))
        if probability is None:
            errors.append(f"probability_missing_or_invalid:{label}")
        elif probability < 0.0 or probability > 1.0:
            errors.append(f"probability_out_of_range:{label}")
        else:
            probabilities[label] = probability
    extra = sorted(set(value) - set(OUTCOME_LABELS))
    if extra:
        errors.append("unexpected_probability_labels:" + "|".join(extra))
    if errors:
        return None, errors
    total = sum(probabilities.values())
    if not math.isclose(total, 1.0, rel_tol=0.0, abs_tol=1e-6):
        return None, ["probability_sum_not_one"]
    return {label: probabilities[label] / total for label in OUTCOME_LABELS}, []


def _calibration_signature(
    row: Mapping[str, Any],
) -> tuple[str | None, dict[str, Any], list[str]]:
    provenance = row.get("odds_provenance")
    if not isinstance(provenance, Mapping):
        return None, {}, ["odds_provenance_missing"]
    components = {field: provenance.get(field) for field in REQUIRED_PROVENANCE_FIELDS}
    errors = [
        f"calibration_signature_field_missing:{field}"
        for field, value in components.items()
        if value in (None, "")
    ]
    if components.get("prompt_sha256") and not _is_sha256(components["prompt_sha256"]):
        errors.append("calibration_signature_prompt_sha256_invalid")
    if errors:
        return None, components, errors
    return _sha256(components), components, []


def _temperature_scale(
    probabilities: Mapping[str, float], temperature: float
) -> dict[str, float]:
    epsilon = 1e-15
    logits = [
        math.log(max(probabilities[label], epsilon)) / temperature
        for label in OUTCOME_LABELS
    ]
    maximum = max(logits)
    weights = [math.exp(value - maximum) for value in logits]
    total = sum(weights)
    return {label: weights[index] / total for index, label in enumerate(OUTCOME_LABELS)}


def _log_loss(rows: Sequence[tuple[Mapping[str, float], str]]) -> float | None:
    if not rows:
        return None
    epsilon = 1e-15
    return fmean(
        -math.log(max(probabilities[outcome], epsilon))
        for probabilities, outcome in rows
    )


def _brier_score(rows: Sequence[tuple[Mapping[str, float], str]]) -> float | None:
    if not rows:
        return None
    return fmean(
        sum(
            (probabilities[label] - (1.0 if label == outcome else 0.0)) ** 2
            for label in OUTCOME_LABELS
        )
        for probabilities, outcome in rows
    )


def _top_label_ece(
    rows: Sequence[tuple[Mapping[str, float], str]], bins: int = 10
) -> float | None:
    if not rows:
        return None
    grouped: dict[int, list[tuple[float, float]]] = defaultdict(list)
    for probabilities, outcome in rows:
        predicted = max(OUTCOME_LABELS, key=lambda label: probabilities[label])
        confidence = probabilities[predicted]
        index = min(bins - 1, int(confidence * bins))
        grouped[index].append((confidence, 1.0 if predicted == outcome else 0.0))
    return sum(
        (len(values) / len(rows))
        * abs(fmean(value[0] for value in values) - fmean(value[1] for value in values))
        for values in grouped.values()
    )


def _fit_calibrators(
    rows: Iterable[Mapping[str, Any]],
    *,
    evaluation_start: datetime,
    min_rows: int,
    min_symbols: int,
    min_dates: int,
) -> tuple[dict[str, dict[str, Any]], Counter[str]]:
    input_rows = [dict(row) for row in rows]
    trace_id_counts = Counter(
        str(row.get("decision_trace_id") or "") for row in input_rows
    )
    eligible: dict[str, list[tuple[dict[str, float], str, str, datetime]]] = (
        defaultdict(list)
    )
    exclusions: Counter[str] = Counter()
    for row in input_rows:
        if row.get("schema") != CALIBRATION_ROW_SCHEMA:
            exclusions["calibration_schema_invalid"] += 1
            continue
        trace_id = str(row.get("decision_trace_id") or "")
        if not trace_id:
            exclusions["calibration_decision_trace_id_missing"] += 1
            continue
        if trace_id_counts[trace_id] > 1:
            exclusions["calibration_duplicate_decision_trace_id"] += 1
            continue
        if row.get("exact_trace_verified") is not True:
            exclusions["calibration_exact_trace_not_verified"] += 1
            continue
        if row.get("outcome_contract_verified") is not True:
            exclusions["calibration_outcome_contract_not_verified"] += 1
            continue
        decision_ts = _parse_ts(row.get("decision_ts"))
        if decision_ts is None:
            exclusions["calibration_decision_ts_invalid"] += 1
            continue
        if decision_ts < CLEAN_BASELINE_TS:
            exclusions["calibration_pre_clean_baseline"] += 1
            continue
        if decision_ts >= evaluation_start:
            exclusions["calibration_not_strictly_prior"] += 1
            continue
        if str(row.get("source_quality_status") or "").lower() != "pass":
            exclusions["calibration_source_quality_not_pass"] += 1
            continue
        outcome = str(row.get("observed_outcome_label") or "")
        if outcome == AMBIGUOUS_OUTCOME:
            exclusions["calibration_same_bar_ambiguous"] += 1
            continue
        if outcome not in OUTCOME_LABELS:
            exclusions["calibration_outcome_invalid"] += 1
            continue
        probabilities, probability_errors = _normalized_probabilities(
            row.get("raw_probabilities")
        )
        signature, _components, signature_errors = _calibration_signature(row)
        provenance = row.get("odds_provenance")
        if not isinstance(provenance, Mapping) or not provenance.get(
            "source_payload_sha256"
        ):
            signature_errors.append("calibration_source_payload_sha256_missing")
        elif not _is_sha256(provenance.get("source_payload_sha256")):
            signature_errors.append("calibration_source_payload_sha256_invalid")
        if (
            probability_errors
            or signature_errors
            or probabilities is None
            or signature is None
        ):
            for error in probability_errors + signature_errors:
                exclusions[error] += 1
            continue
        eligible[signature].append(
            (probabilities, outcome, str(row.get("stock_code") or ""), decision_ts)
        )

    fitted: dict[str, dict[str, Any]] = {}
    for signature, signature_rows in eligible.items():
        symbols = {row[2] for row in signature_rows if row[2]}
        dates = {row[3].astimezone(KST).date().isoformat() for row in signature_rows}
        blockers: list[str] = []
        if len(signature_rows) < min_rows:
            blockers.append("calibration_row_floor")
        if len(symbols) < min_symbols:
            blockers.append("calibration_unique_symbol_floor")
        if len(dates) < min_dates:
            blockers.append("calibration_source_date_floor")
        if blockers:
            fitted[signature] = {
                "status": "insufficient_sample",
                "sample_count": len(signature_rows),
                "unique_symbol_count": len(symbols),
                "source_date_count": len(dates),
                "blockers": blockers,
                "temperature": None,
            }
            continue
        base_rows = [
            (probabilities, outcome)
            for probabilities, outcome, _symbol, _ts in signature_rows
        ]
        scored: list[tuple[float, float]] = []
        for temperature in TEMPERATURE_GRID:
            scaled = [
                (_temperature_scale(probabilities, temperature), outcome)
                for probabilities, outcome in base_rows
            ]
            loss = _log_loss(scaled)
            if loss is not None:
                scored.append((loss, temperature))
        best_loss, temperature = min(
            scored, key=lambda item: (item[0], abs(item[1] - 1.0))
        )
        calibrated_rows = [
            (_temperature_scale(probabilities, temperature), outcome)
            for probabilities, outcome in base_rows
        ]
        fitted[signature] = {
            "status": "fitted",
            "sample_count": len(signature_rows),
            "unique_symbol_count": len(symbols),
            "source_date_count": len(dates),
            "blockers": [],
            "temperature": temperature,
            "raw_log_loss": _round(_log_loss(base_rows)),
            "calibrated_log_loss": _round(best_loss),
            "raw_brier_score": _round(_brier_score(base_rows)),
            "calibrated_brier_score": _round(_brier_score(calibrated_rows)),
        }
    return fitted, exclusions


def _cost_breakdown(row: Mapping[str, Any]) -> tuple[dict[str, Any], list[str]]:
    value = row.get("cost_inputs")
    if not isinstance(value, Mapping):
        return {"status": "incomplete", "total_cost_bps": None}, ["cost_inputs_missing"]
    errors: list[str] = []
    provenance = row.get("odds_provenance")
    cost_model_version = (
        provenance.get("cost_model_version")
        if isinstance(provenance, Mapping)
        else None
    )
    if not cost_model_version:
        errors.append("cost_model_version_missing")
    components: dict[str, float] = {}
    for field in REQUIRED_COST_FIELDS:
        number = _number(value.get(field))
        if number is None:
            errors.append(f"cost_field_missing_or_invalid:{field}")
        elif number < 0.0:
            errors.append(f"cost_field_negative:{field}")
        else:
            components[field] = number
    context: dict[str, str] = {}
    for field in REQUIRED_COST_CONTEXT_FIELDS:
        context_value = str(value.get(field) or "").strip()
        if not context_value:
            errors.append(f"cost_context_missing:{field}")
        else:
            context[field] = context_value
    effective_from = _parse_ts(f"{context.get('effective_from')}T00:00:00+09:00")
    effective_to = _parse_ts(f"{context.get('effective_to')}T23:59:59+09:00")
    decision_ts = _parse_ts(row.get("decision_ts"))
    if context.get("effective_from") and effective_from is None:
        errors.append("cost_effective_from_invalid")
    if context.get("effective_to") and effective_to is None:
        errors.append("cost_effective_to_invalid")
    if effective_from is not None and effective_to is not None:
        if effective_to < effective_from:
            errors.append("cost_schedule_window_invalid")
        elif decision_ts is not None and not (
            effective_from <= decision_ts.astimezone(KST) <= effective_to
        ):
            errors.append("cost_schedule_not_effective_at_decision")
    price_basis = str(value.get("entry_price_basis") or "")
    if not price_basis:
        errors.append("entry_price_basis_missing")
    includes_spread = value.get("price_basis_includes_entry_spread")
    if not isinstance(includes_spread, bool):
        errors.append("price_basis_includes_entry_spread_missing")
    elif includes_spread and components.get("entry_spread_bps", 0.0) > 0.0:
        errors.append("entry_spread_cost_double_count")
    if errors:
        return {
            "status": "incomplete",
            "cost_model_version": (cost_model_version),
            "entry_price_basis": price_basis or None,
            "price_basis_includes_entry_spread": includes_spread,
            "cost_context": context,
            "components_bps": components,
            "total_cost_bps": None,
            "legacy_fixed_cost_comparison_bps": LEGACY_FIXED_COST_COMPARISON_BPS,
        }, errors
    total = sum(components.values())
    return {
        "status": "complete",
        "cost_model_version": cost_model_version,
        "entry_price_basis": price_basis,
        "price_basis_includes_entry_spread": includes_spread,
        "cost_context": context,
        "components_bps": components,
        "total_cost_bps": _round(total),
        "legacy_fixed_cost_comparison_bps": LEGACY_FIXED_COST_COMPARISON_BPS,
        "legacy_comparison_delta_bps": _round(total - LEGACY_FIXED_COST_COMPARISON_BPS),
    }, []


def _outcome(label: Mapping[str, Any]) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    stage_outcome = label.get("stage_outcome")
    horizon = label.get("horizon_metrics")
    horizon_10m = horizon.get("10m") if isinstance(horizon, Mapping) else None
    if label.get("decision_stage") not in {"entry", "entry_screen"}:
        errors.append("outcome_not_entry_stage")
    if label.get("label_status") != "mature":
        errors.append("outcome_10m_not_mature")
    if str(label.get("source_quality_status") or "").lower() != "pass":
        errors.append("outcome_source_quality_not_pass")
    if label.get("primary_cohort_eligible") is not True:
        errors.append("outcome_primary_cohort_ineligible")
    if label.get("invalid_reasons"):
        errors.append("outcome_invalid_reasons_present")
    if not isinstance(stage_outcome, Mapping) or not isinstance(horizon_10m, Mapping):
        errors.append("outcome_10m_metrics_missing")
        return {"status": "invalid"}, errors
    first_hit = str(stage_outcome.get("entry_path_first_hit") or "")
    end_return_pct = _number(horizon_10m.get("end_return_pct"))
    if first_hit == "target_first":
        market_path = "TARGET_FIRST"
    elif first_hit == "adverse_first":
        market_path = "ADVERSE_FIRST"
    elif first_hit == "same_bar_ambiguous":
        market_path = AMBIGUOUS_OUTCOME
    elif first_hit == "neither_hit" and end_return_pct is not None:
        market_path = (
            "NEITHER_POSITIVE" if end_return_pct > 0.0 else "NEITHER_NONPOSITIVE"
        )
    else:
        market_path = None
        errors.append("outcome_market_path_invalid")
    if end_return_pct is None:
        errors.append("outcome_end_return_missing")
    return {
        "status": "mature" if not errors else "invalid",
        "decision_ts": label.get("decision_ts"),
        "primary_payload_sha256": label.get("primary_payload_sha256"),
        "market_path_label": market_path,
        "entry_path_label_version": stage_outcome.get("entry_path_label_version"),
        "horizon": stage_outcome.get("entry_path_primary_horizon"),
        "target_bps": (
            _round(_number(stage_outcome.get("entry_path_target_pct")) * 100.0)
            if _number(stage_outcome.get("entry_path_target_pct")) is not None
            else None
        ),
        "adverse_bps": (
            _round(_number(stage_outcome.get("entry_path_adverse_pct")) * 100.0)
            if _number(stage_outcome.get("entry_path_adverse_pct")) is not None
            else None
        ),
        "horizon_end_return_pct": end_return_pct,
        "counterfactual_only": True,
        "actual_order_submitted": (
            bool((label.get("correlation") or {}).get("actual_order_submitted", False))
            if isinstance(label.get("correlation"), Mapping)
            else False
        ),
        "realized_profit_pct": (
            (label.get("correlation") or {}).get("realized_profit_pct")
            if isinstance(label.get("correlation"), Mapping)
            else None
        ),
        "realized_separate_from_counterfactual": True,
    }, errors


def _trace_errors(prediction: Mapping[str, Any], trace: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if not trace:
        return ["exact_trace_missing"]
    if trace.get("decision_stage") not in {"entry", "entry_screen"}:
        errors.append("trace_not_entry_stage")
    if trace.get("payload_replay_exact") is not True:
        errors.append("trace_payload_not_exact")
    if trace.get("input_preflight_allowed") is not True:
        errors.append("trace_input_preflight_not_allowed")
    if str(trace.get("input_preflight_status") or "").lower() not in {
        "fresh_consistent",
        "pass",
    }:
        errors.append("trace_input_not_fresh_consistent")
    provenance = prediction.get("odds_provenance")
    source_payload_sha = (
        provenance.get("source_payload_sha256")
        if isinstance(provenance, Mapping)
        else None
    )
    if not source_payload_sha:
        errors.append("source_payload_sha256_missing")
    elif not _is_sha256(source_payload_sha):
        errors.append("source_payload_sha256_invalid")
    elif source_payload_sha != trace.get("payload_sha256"):
        errors.append("source_payload_sha256_mismatch")
    if prediction.get("decision_ts") != trace.get("decision_ts"):
        errors.append("prediction_trace_decision_ts_mismatch")
    if prediction.get("stock_code") != trace.get("stock_code"):
        errors.append("prediction_trace_stock_code_mismatch")
    if isinstance(provenance, Mapping):
        if (
            str(provenance.get("execution_venue") or "").upper()
            != str(trace.get("broker_route") or "").upper()
        ):
            errors.append("prediction_trace_execution_venue_mismatch")
        if (
            str(provenance.get("effective_venue") or "").upper()
            != str(trace.get("effective_venue") or "").upper()
        ):
            errors.append("prediction_trace_effective_venue_mismatch")
        if (
            str(provenance.get("session_bucket") or "").upper()
            != str(trace.get("session_bucket") or "").upper()
        ):
            errors.append("prediction_trace_session_bucket_mismatch")
    return errors


def _expected_value(
    probabilities: Mapping[str, float],
    prediction: Mapping[str, Any],
    total_cost_bps: float,
) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    payoff_value = prediction.get("payoff_bps")
    payoff: dict[str, float] = {}
    if not isinstance(payoff_value, Mapping):
        errors.append("payoff_bps_missing")
    else:
        for label in OUTCOME_LABELS:
            number = _number(payoff_value.get(label))
            if number is None:
                errors.append(f"payoff_missing_or_invalid:{label}")
            else:
                payoff[label] = number
    if len(payoff) == len(OUTCOME_LABELS):
        if payoff["TARGET_FIRST"] <= 0.0:
            errors.append("target_first_payoff_not_positive")
        if payoff["ADVERSE_FIRST"] >= 0.0:
            errors.append("adverse_first_payoff_not_negative")
        if payoff["NEITHER_POSITIVE"] <= 0.0:
            errors.append("neither_positive_payoff_not_positive")
        if payoff["NEITHER_NONPOSITIVE"] > 0.0:
            errors.append("neither_nonpositive_payoff_positive")
    fill_probability = _number(prediction.get("counterfactual_fill_probability"))
    if fill_probability is None or not 0.0 <= fill_probability <= 1.0:
        errors.append("counterfactual_fill_probability_invalid")
    fill_state = str(prediction.get("counterfactual_fill_state") or "")
    if fill_state not in COUNTERFACTUAL_FILL_STATES:
        errors.append("counterfactual_fill_state_invalid")
    hurdle_bps = _number(prediction.get("uncertainty_hurdle_bps", 0.0))
    if hurdle_bps is None or hurdle_bps < 0.0:
        errors.append("uncertainty_hurdle_bps_invalid")
    hurdle_value = prediction.get("uncertainty_hurdle_components_bps")
    hurdle_components: dict[str, float] = {}
    if not isinstance(hurdle_value, Mapping):
        errors.append("uncertainty_hurdle_components_missing")
    else:
        unexpected_hurdle_fields = sorted(
            set(hurdle_value) - set(HURDLE_COMPONENT_FIELDS)
        )
        if unexpected_hurdle_fields:
            errors.append(
                "unexpected_uncertainty_hurdle_components:"
                + "|".join(unexpected_hurdle_fields)
            )
        for field in HURDLE_COMPONENT_FIELDS:
            number = _number(hurdle_value.get(field))
            if number is None or number < 0.0:
                errors.append(f"uncertainty_hurdle_component_invalid:{field}")
            else:
                hurdle_components[field] = number
    if (
        hurdle_bps is not None
        and len(hurdle_components) == len(HURDLE_COMPONENT_FIELDS)
        and not math.isclose(
            sum(hurdle_components.values()), hurdle_bps, rel_tol=0.0, abs_tol=1e-6
        )
    ):
        errors.append("uncertainty_hurdle_component_sum_mismatch")
    if errors:
        return {
            "status": "invalid",
            "counterfactual_execution_policy": COUNTERFACTUAL_EXECUTION_POLICY,
        }, errors
    gross_bps = sum(probabilities[label] * payoff[label] for label in OUTCOME_LABELS)
    conditional_net_bps = gross_bps - total_cost_bps
    per_signal_net_bps = fill_probability * conditional_net_bps
    return {
        "status": "complete",
        "counterfactual_execution_policy": COUNTERFACTUAL_EXECUTION_POLICY,
        "reference_quantity_shares": 1,
        "payoff_bps": payoff,
        "counterfactual_fill_probability": fill_probability,
        "counterfactual_fill_state": fill_state,
        "expected_gross_edge_bps": _round(gross_bps),
        "expected_total_cost_bps": _round(total_cost_bps),
        "expected_conditional_net_edge_bps": _round(conditional_net_bps),
        "expected_net_edge_per_signal_bps": _round(per_signal_net_bps),
        "uncertainty_hurdle_bps": _round(hurdle_bps),
        "uncertainty_hurdle_components_bps": hurdle_components,
    }, []


def _evaluation_metrics(rows: Sequence[dict[str, Any]], key: str) -> dict[str, Any]:
    scored = [
        (row["probabilities"][key], row["outcome"]["market_path_label"])
        for row in rows
        if row.get("outcome", {}).get("market_path_label") in OUTCOME_LABELS
        and isinstance(row.get("probabilities", {}).get(key), Mapping)
    ]
    return {
        "sample_count": len(scored),
        "multiclass_log_loss": _round(_log_loss(scored)),
        "multiclass_brier_score": _round(_brier_score(scored)),
        "top_label_ece": _round(_top_label_ece(scored)),
    }


def _veto_attribution(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    original_buys = [row for row in rows if row.get("original_action") == "BUY"]
    vetoed = [
        row
        for row in original_buys
        if row.get("observer_assessment") == "WOULD_NO_BET"
        and row.get("counterfactual_net_return_pct") is not None
    ]
    avoided_losers = [
        row for row in vetoed if row["counterfactual_net_return_pct"] < 0.0
    ]
    foregone_winners = [
        row for row in vetoed if row["counterfactual_net_return_pct"] > 0.0
    ]
    delta = sum(-row["counterfactual_net_return_pct"] for row in vetoed)
    monetary_deltas = [
        -row["counterfactual_net_profit_krw_one_share"]
        for row in vetoed
        if row.get("counterfactual_net_profit_krw_one_share") is not None
    ]
    retained = len(original_buys) - len(vetoed)
    ordered_buys = sorted(original_buys, key=lambda row: str(row.get("decision_ts")))
    baseline_returns = [row["counterfactual_net_return_pct"] for row in ordered_buys]
    candidate_returns = [
        (
            0.0
            if row.get("observer_assessment") == "WOULD_NO_BET"
            else row["counterfactual_net_return_pct"]
        )
        for row in ordered_buys
    ]

    def _max_additive_drawdown(values: Sequence[float]) -> float | None:
        if not values:
            return None
        cumulative = 0.0
        peak = 0.0
        maximum_drawdown = 0.0
        for value in values:
            cumulative += value
            peak = max(peak, cumulative)
            maximum_drawdown = max(maximum_drawdown, peak - cumulative)
        return _round(maximum_drawdown)

    baseline_ev = _round(fmean(baseline_returns)) if baseline_returns else None
    candidate_ev = _round(fmean(candidate_returns)) if candidate_returns else None
    veto_symbols = {str(row.get("stock_code") or "") for row in vetoed}
    veto_dates = {str(row.get("decision_ts") or "")[:10] for row in vetoed}
    baseline_worst = min(baseline_returns) if baseline_returns else None
    candidate_worst = min(candidate_returns) if candidate_returns else None
    baseline_drawdown = _max_additive_drawdown(baseline_returns)
    candidate_drawdown = _max_additive_drawdown(candidate_returns)
    gate_checks = {
        "minimum_veto_count": len(vetoed) >= 5,
        "minimum_veto_unique_symbols": len(veto_symbols) >= 5,
        "minimum_veto_source_dates": len(veto_dates) >= 2,
        "oos_net_ev_improved": (
            baseline_ev is not None
            and candidate_ev is not None
            and candidate_ev > baseline_ev
        ),
        "worst_loss_not_worse": (
            baseline_worst is not None
            and candidate_worst is not None
            and candidate_worst >= baseline_worst
        ),
        "max_drawdown_not_worse": (
            baseline_drawdown is not None
            and candidate_drawdown is not None
            and candidate_drawdown <= baseline_drawdown
        ),
    }
    gate_blockers = [name for name, passed in gate_checks.items() if not passed]
    return {
        "scope": "hypothetical_negative_veto_on_existing_buy_actions_only",
        "original_buy_count": len(original_buys),
        "hypothetical_veto_count": len(vetoed),
        "hypothetical_retained_buy_count": retained,
        "hypothetical_buy_retention_pct": (
            _round((retained / len(original_buys)) * 100.0) if original_buys else None
        ),
        "avoided_loser_count": len(avoided_losers),
        "foregone_winner_count": len(foregone_winners),
        "hypothetical_cumulative_return_delta_pct_one_share_reference_sum": _round(
            delta
        ),
        "hypothetical_net_profit_delta_krw_one_share_reference": (
            _round(sum(monetary_deltas), 4) if monetary_deltas else None
        ),
        "monetary_attribution_missing_reference_price_count": len(vetoed)
        - len(monetary_deltas),
        "baseline_source_quality_adjusted_ev_pct": baseline_ev,
        "hypothetical_veto_source_quality_adjusted_ev_pct": candidate_ev,
        "baseline_worst_loss_pct": _round(baseline_worst),
        "hypothetical_veto_worst_loss_pct": _round(candidate_worst),
        "baseline_max_additive_drawdown_pct": baseline_drawdown,
        "hypothetical_veto_max_additive_drawdown_pct": candidate_drawdown,
        "veto_unique_symbol_count": len(veto_symbols),
        "veto_source_date_count": len(veto_dates),
        "sim_candidate_gate": {
            "pass": not gate_blockers,
            "checks": gate_checks,
            "blockers": gate_blockers,
            "authority_if_passed": "sim_candidate_only_no_runtime_apply",
        },
        "submit_drought_decision_status": "not_evaluated_without_submit_and_budget_join",
        "runtime_effect": False,
    }


def _predicted_vs_oos(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    buckets = (
        ("lt_0bp", None, 0.0),
        ("0_5bp", 0.0, 5.0),
        ("5_10bp", 5.0, 10.0),
        ("10_15bp", 10.0, 15.0),
        ("gte_15bp", 15.0, None),
    )
    output: list[dict[str, Any]] = []
    nonempty_observed: list[float] = []
    for name, lower, upper in buckets:
        selected: list[tuple[float, float]] = []
        for row in rows:
            predicted = _number(
                row.get("predicted_value", {}).get("expected_net_edge_per_signal_bps")
            )
            observed_pct = _number(row.get("counterfactual_net_return_pct"))
            if predicted is None or observed_pct is None:
                continue
            if lower is not None and predicted < lower:
                continue
            if upper is not None and predicted >= upper:
                continue
            selected.append((predicted, observed_pct * 100.0))
        observed_average = (
            _round(fmean(value[1] for value in selected)) if selected else None
        )
        if observed_average is not None:
            nonempty_observed.append(observed_average)
        output.append(
            {
                "predicted_ev_bucket": name,
                "sample_count": len(selected),
                "avg_predicted_net_ev_bps": (
                    _round(fmean(value[0] for value in selected)) if selected else None
                ),
                "source_quality_adjusted_ev_bps": observed_average,
            }
        )
    monotonic = all(
        later >= earlier
        for earlier, later in zip(nonempty_observed, nonempty_observed[1:])
    )
    return {
        "rows": output,
        "nonempty_bucket_count": len(nonempty_observed),
        "observed_ev_monotonic_non_decreasing": (
            monotonic if len(nonempty_observed) >= 2 else None
        ),
        "economic_outcome_type": "counterfactual_not_realized",
    }


def _fill_cohort_attribution(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for fill_state in COUNTERFACTUAL_FILL_STATES:
        selected = [
            row
            for row in rows
            if row.get("predicted_value", {}).get("counterfactual_fill_state")
            == fill_state
        ]
        output[fill_state] = {
            "sample_count": len(selected),
            "source_quality_adjusted_ev_pct": (
                _round(fmean(row["counterfactual_net_return_pct"] for row in selected))
                if selected
                else None
            ),
        }
    return {
        "cohorts": output,
        "full_and_partial_merged": False,
        "actual_and_counterfactual_merged": False,
    }


def build_report(
    *,
    target_date: str,
    predictions: Iterable[Mapping[str, Any]],
    calibration_rows: Iterable[Mapping[str, Any]],
    traces: Iterable[Mapping[str, Any]],
    outcome_labels: Iterable[Mapping[str, Any]],
    min_calibration_rows: int = DEFAULT_MIN_CALIBRATION_ROWS,
    min_unique_symbols: int = DEFAULT_MIN_UNIQUE_SYMBOLS,
    min_calibration_dates: int = DEFAULT_MIN_CALIBRATION_DATES,
    min_evaluation_rows: int = DEFAULT_MIN_EVALUATION_ROWS,
    min_evaluation_dates: int = DEFAULT_MIN_EVALUATION_DATES,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    """Return one counterfactual-only V1 report without writing or model calls."""

    for name, value in (
        ("min_calibration_rows", min_calibration_rows),
        ("min_unique_symbols", min_unique_symbols),
        ("min_calibration_dates", min_calibration_dates),
        ("min_evaluation_rows", min_evaluation_rows),
        ("min_evaluation_dates", min_evaluation_dates),
    ):
        if value <= 0:
            raise ValueError(f"{name} must be positive")
    if generated_at is not None and generated_at.tzinfo is None:
        raise ValueError("generated_at must be timezone-aware")
    prediction_rows = [dict(row) for row in predictions]
    target_start = _parse_ts(f"{target_date}T00:00:00+09:00")
    target_end = _parse_ts(f"{target_date}T23:59:59.999999+09:00")
    if target_start is None or target_end is None:
        raise ValueError(f"invalid target_date: {target_date}")
    prediction_counts = Counter(
        str(row.get("decision_trace_id") or "") for row in prediction_rows
    )
    evaluation_times = [
        value
        for row in prediction_rows
        if (value := _parse_ts(row.get("decision_ts"))) and value >= CLEAN_BASELINE_TS
    ]
    evaluation_start = min(evaluation_times) if evaluation_times else target_start
    calibrators, calibration_exclusions = _fit_calibrators(
        calibration_rows,
        evaluation_start=evaluation_start,
        min_rows=min_calibration_rows,
        min_symbols=min_unique_symbols,
        min_dates=min_calibration_dates,
    )
    trace_rows = [dict(row) for row in traces]
    label_rows = [dict(row) for row in outcome_labels]
    trace_counts = Counter(
        str(row.get("decision_trace_id") or "") for row in trace_rows
    )
    label_counts = Counter(
        str(row.get("decision_trace_id") or "") for row in label_rows
    )
    trace_by_id = {
        str(row.get("decision_trace_id")): row
        for row in trace_rows
        if row.get("decision_trace_id")
    }
    label_by_id = {
        str(row.get("decision_trace_id")): row
        for row in label_rows
        if row.get("decision_trace_id")
    }
    ledger: list[dict[str, Any]] = []
    assessment_exclusion_counts: Counter[str] = Counter()
    evaluation_exclusion_counts: Counter[str] = Counter()
    for prediction in prediction_rows:
        trace_id = str(prediction.get("decision_trace_id") or "")
        assessment_errors: list[str] = []
        evaluation_errors: list[str] = []
        if prediction.get("schema") != RAW_PREDICTION_SCHEMA:
            assessment_errors.append("prediction_schema_invalid")
        if not trace_id:
            assessment_errors.append("decision_trace_id_missing")
        elif prediction_counts[trace_id] > 1:
            assessment_errors.append("duplicate_prediction_trace_id")
        decision_ts = _parse_ts(prediction.get("decision_ts"))
        if decision_ts is None:
            assessment_errors.append("prediction_decision_ts_invalid")
        elif decision_ts < CLEAN_BASELINE_TS:
            assessment_errors.append("prediction_pre_clean_baseline")
        elif decision_ts > target_end:
            assessment_errors.append("prediction_after_target_date")
        if str(prediction.get("source_quality_status") or "").lower() != "pass":
            assessment_errors.append("prediction_source_quality_not_pass")

        probabilities, probability_errors = _normalized_probabilities(
            prediction.get("raw_probabilities")
        )
        signature, signature_components, signature_errors = _calibration_signature(
            prediction
        )
        assessment_errors.extend(probability_errors)
        assessment_errors.extend(signature_errors)
        trace = trace_by_id.get(trace_id, {})
        assessment_errors.extend(_trace_errors(prediction, trace))
        if trace_counts[trace_id] > 1:
            assessment_errors.append("duplicate_exact_trace")
        outcome, outcome_errors = _outcome(label_by_id.get(trace_id, {}))
        evaluation_errors.extend(outcome_errors)
        if label_counts[trace_id] > 1:
            evaluation_errors.append("duplicate_outcome_label")
        if outcome.get("decision_ts") != prediction.get("decision_ts"):
            evaluation_errors.append("outcome_prediction_decision_ts_mismatch")
        if outcome.get("primary_payload_sha256") != trace.get("payload_sha256"):
            evaluation_errors.append("outcome_trace_payload_sha256_mismatch")
        if outcome.get("entry_path_label_version") and signature_components.get(
            "outcome_label_version"
        ) != outcome.get("entry_path_label_version"):
            evaluation_errors.append("outcome_label_version_mismatch")
        if outcome.get("horizon") and signature_components.get(
            "outcome_horizon"
        ) != outcome.get("horizon"):
            evaluation_errors.append("outcome_horizon_mismatch")
        if outcome.get("target_bps") is not None and _number(
            signature_components.get("outcome_target_bps")
        ) != outcome.get("target_bps"):
            evaluation_errors.append("outcome_target_bps_mismatch")
        if outcome.get("adverse_bps") is not None and _number(
            signature_components.get("outcome_adverse_bps")
        ) != outcome.get("adverse_bps"):
            evaluation_errors.append("outcome_adverse_bps_mismatch")
        if outcome.get("market_path_label") == AMBIGUOUS_OUTCOME:
            evaluation_errors.append("outcome_same_bar_ambiguous")
        calibration_update = None
        if not assessment_errors and not evaluation_errors:
            calibration_update = {
                "schema": CALIBRATION_ROW_SCHEMA,
                "decision_trace_id": trace_id,
                "decision_ts": prediction.get("decision_ts"),
                "stock_code": prediction.get("stock_code"),
                "source_quality_status": "pass",
                "exact_trace_verified": True,
                "outcome_contract_verified": True,
                "odds_provenance": dict(prediction.get("odds_provenance") or {}),
                "raw_probabilities": probabilities,
                "observed_outcome_label": outcome.get("market_path_label"),
                "actual_order_submitted": outcome.get("actual_order_submitted"),
                "realized_separate_from_counterfactual": True,
                "runtime_effect": False,
            }
        cost, cost_errors = _cost_breakdown(prediction)
        assessment_errors.extend(cost_errors)
        if (
            cost.get("cost_context", {}).get("execution_venue")
            and str(cost["cost_context"]["execution_venue"]).upper()
            != str(trace.get("broker_route") or "").upper()
        ):
            assessment_errors.append("cost_execution_venue_trace_mismatch")
        if cost.get("entry_price_basis") and cost.get("entry_price_basis") != trace.get(
            "reference_price_type"
        ):
            assessment_errors.append("entry_price_basis_trace_mismatch")

        calibrator = calibrators.get(signature or "")
        calibrated: dict[str, float] | None = None
        if signature and calibrator is None:
            assessment_errors.append("calibration_signature_unseen")
        elif calibrator and calibrator.get("status") != "fitted":
            assessment_errors.extend(
                str(value) for value in calibrator.get("blockers") or []
            )
        elif calibrator and probabilities is not None:
            calibrated = _temperature_scale(
                probabilities, float(calibrator["temperature"])
            )

        expected_value: dict[str, Any] = {"status": "not_evaluated"}
        if calibrated is not None and cost.get("total_cost_bps") is not None:
            expected_value, value_errors = _expected_value(
                calibrated, prediction, float(cost["total_cost_bps"])
            )
            assessment_errors.extend(value_errors)

        assessment = "ABSTAIN"
        if not assessment_errors and expected_value.get("status") == "complete":
            assessment = (
                "WOULD_BET"
                if expected_value["expected_net_edge_per_signal_bps"]
                > expected_value["uncertainty_hurdle_bps"]
                else "WOULD_NO_BET"
            )

        counterfactual_net_return_pct: float | None = None
        counterfactual_net_profit_krw: float | None = None
        if not evaluation_errors and cost.get("total_cost_bps") is not None:
            fill_probability = _number(
                prediction.get("counterfactual_fill_probability")
            )
            end_return_pct = _number(outcome.get("horizon_end_return_pct"))
            if (
                fill_probability is not None
                and 0.0 <= fill_probability <= 1.0
                and end_return_pct is not None
            ):
                counterfactual_net_return_pct = _round(
                    fill_probability
                    * (end_return_pct - (float(cost["total_cost_bps"]) / 100.0))
                )
                reference_price = _number(trace.get("reference_price"))
                if reference_price is not None and reference_price > 0.0:
                    counterfactual_net_profit_krw = _round(
                        reference_price * counterfactual_net_return_pct / 100.0, 4
                    )

        assessment_errors = sorted(set(assessment_errors))
        evaluation_errors = sorted(set(evaluation_errors))
        for error in assessment_errors:
            assessment_exclusion_counts[error] += 1
        for error in evaluation_errors:
            evaluation_exclusion_counts[error] += 1
        ledger.append(
            {
                "schema": ROW_SCHEMA,
                "decision_trace_id": trace_id or None,
                "decision_ts": prediction.get("decision_ts"),
                "stock_code": prediction.get("stock_code"),
                "original_action": trace.get("action"),
                "original_score": trace.get("score"),
                "observer_assessment": assessment,
                "observer_assessment_namespace": "offline_entry_odds_observer",
                "assessment_eligible": not assessment_errors,
                "assessment_exclusion_reasons": assessment_errors,
                "evaluation_eligible": not assessment_errors
                and not evaluation_errors
                and counterfactual_net_return_pct is not None,
                "evaluation_exclusion_reasons": evaluation_errors,
                "calibration_signature": signature,
                "calibration_signature_components": signature_components,
                "calibration": calibrator or {"status": "signature_unseen"},
                "calibration_update": calibration_update,
                "probabilities": {
                    "raw": probabilities,
                    "calibrated": calibrated,
                    "labels": list(OUTCOME_LABELS),
                },
                "cost": cost,
                "predicted_value": expected_value,
                "outcome": outcome,
                "counterfactual_net_return_pct": counterfactual_net_return_pct,
                "counterfactual_net_profit_krw_one_share": (
                    counterfactual_net_profit_krw
                ),
                "counterfactual_execution_policy": COUNTERFACTUAL_EXECUTION_POLICY,
                "actual_order_submitted_by_observer": False,
                "runtime_effect": False,
            }
        )

    scored_rows = [
        row
        for row in ledger
        if row["evaluation_eligible"]
        and row["outcome"].get("market_path_label") in OUTCOME_LABELS
        and row.get("counterfactual_net_return_pct") is not None
    ]
    raw_metrics = _evaluation_metrics(scored_rows, "raw")
    calibrated_metrics = _evaluation_metrics(scored_rows, "calibrated")
    predicted_vs_oos = _predicted_vs_oos(scored_rows)
    veto_attribution = _veto_attribution(scored_rows)
    ev_pct = (
        _round(fmean(row["counterfactual_net_return_pct"] for row in scored_rows))
        if scored_rows
        else None
    )
    source_dates = {
        str(row.get("decision_ts") or "")[:10]
        for row in scored_rows
        if row.get("decision_ts")
    }
    evaluation_blockers: list[str] = []
    if len(scored_rows) < min_evaluation_rows:
        evaluation_blockers.append("oos_evaluation_row_floor")
    if len(source_dates) < min_evaluation_dates:
        evaluation_blockers.append("oos_evaluation_source_date_floor")
    if predicted_vs_oos["observed_ev_monotonic_non_decreasing"] is not True:
        evaluation_blockers.append("predicted_ev_observed_ev_monotonicity_unproven")
    if veto_attribution["sim_candidate_gate"]["pass"] is not True:
        evaluation_blockers.append("negative_veto_sim_candidate_gate_not_closed")
    raw_loss = raw_metrics["multiclass_log_loss"]
    calibrated_loss = calibrated_metrics["multiclass_log_loss"]
    calibration_worse = (
        raw_loss is not None
        and calibrated_loss is not None
        and calibrated_loss > raw_loss
    )
    assessment_eligible_count = sum(row["assessment_eligible"] for row in ledger)
    if (
        ledger
        and assessment_eligible_count == 0
        and any(
            error.startswith("cost_") or error == "entry_spread_cost_double_count"
            for error in assessment_exclusion_counts
        )
    ):
        final_state = "cost_model_incomplete"
    elif calibration_worse and not evaluation_blockers:
        final_state = "calibration_failed"
    elif evaluation_blockers:
        final_state = "hold_sample"
    elif ev_pct is not None and ev_pct > 0.0:
        final_state = "sim_candidate_ready"
    else:
        final_state = "observe_only_continue"

    assessment_counts = Counter(row["observer_assessment"] for row in ledger)
    generated = generated_at or datetime.now(KST)
    report: dict[str, Any] = {
        "schema": SCHEMA,
        "policy_version": POLICY_VERSION,
        "target_date": target_date,
        "generated_at": generated.astimezone(KST).isoformat(),
        "final_state": final_state,
        "decision": {
            "identified": bool(scored_rows),
            "applied_to_sim": False,
            "remaining_for_real_runtime": [
                "reviewed_sim_policy_catalog_candidate",
                "PREOPEN_runtime_selection",
                "live_auto_and_same_stage_owner_contract",
                "post_apply_attribution",
                "explicit_real_authority_approval",
            ],
        },
        "summary": {
            "prediction_count": len(ledger),
            "assessment_eligible_count": sum(
                row["assessment_eligible"] for row in ledger
            ),
            "eligible_count": len(scored_rows),
            "excluded_count": len(ledger) - len(scored_rows),
            "assessment_counts": {
                assessment: assessment_counts.get(assessment, 0)
                for assessment in ASSESSMENTS
            },
            "calibration_signature_count": len(calibrators),
            "fitted_calibration_signature_count": sum(
                value.get("status") == "fitted" for value in calibrators.values()
            ),
            "source_quality_adjusted_ev_pct": ev_pct,
            "evaluation_source_date_count": len(source_dates),
            "evaluation_blockers": evaluation_blockers,
        },
        "calibration_evaluation": {
            "raw": raw_metrics,
            "calibrated": calibrated_metrics,
            "calibrated_log_loss_worse_than_raw": calibration_worse,
            "strictly_prior_to_first_evaluation_ts": evaluation_start.isoformat(),
        },
        "calibrators": calibrators,
        "calibration_updates": [
            row["calibration_update"]
            for row in ledger
            if row.get("calibration_update") is not None
        ],
        "predicted_vs_oos_outcome": predicted_vs_oos,
        "fill_cohort_attribution": _fill_cohort_attribution(scored_rows),
        "cost_attribution": {
            "required_components": list(REQUIRED_COST_FIELDS),
            "required_context": list(REQUIRED_COST_CONTEXT_FIELDS),
            "legacy_fixed_cost_comparison_bps": LEGACY_FIXED_COST_COMPARISON_BPS,
            "legacy_fixed_cost_is_comparison_only": True,
            "spread_double_count_guard": True,
        },
        "negative_veto_attribution": veto_attribution,
        "source_quality_and_exclusion_manifest": {
            "assessment_exclusion_counts": dict(
                sorted(assessment_exclusion_counts.items())
            ),
            "evaluation_exclusion_counts": dict(
                sorted(evaluation_exclusion_counts.items())
            ),
            "calibration_exclusion_counts": dict(
                sorted(calibration_exclusions.items())
            ),
            "same_bar_ambiguous_is_excluded_from_ev": True,
            "pre_clean_baseline_is_archive_only": True,
        },
        "ledger": ledger,
        **METRIC_DECISION_CONTRACT,
    }
    report["sample_floor"] = {
        "calibration_rows_per_signature": min_calibration_rows,
        "calibration_unique_symbols_per_signature": min_unique_symbols,
        "calibration_source_dates_per_signature": min_calibration_dates,
        "oos_evaluation_rows": min_evaluation_rows,
        "oos_evaluation_source_dates": min_evaluation_dates,
    }
    return report


def render_markdown(report: Mapping[str, Any]) -> str:
    summary = report.get("summary") or {}
    calibration = report.get("calibration_evaluation") or {}
    veto = report.get("negative_veto_attribution") or {}
    decision = report.get("decision") or {}
    lines = [
        f"# Offline Entry Odds Observer V1 — {report.get('target_date')}",
        "",
        "## Decision",
        "",
        f"- Final state: `{report.get('final_state')}`",
        f"- Identified with valid evidence: `{decision.get('identified')}`",
        f"- Applied to simulation: `{decision.get('applied_to_sim')}`",
        "- Runtime effect: `false`",
        f"- Source quality: `{report.get('source_quality_status', 'eligible_rows_only')}`",
        f"- Evaluation blockers: `{json.dumps(summary.get('evaluation_blockers', []), ensure_ascii=False)}`",
        "",
        "## Evidence",
        "",
        f"- Predictions / eligible / excluded: {summary.get('prediction_count', 0)} / {summary.get('eligible_count', 0)} / {summary.get('excluded_count', 0)}",
        f"- Source-quality-adjusted EV: {summary.get('source_quality_adjusted_ev_pct')}",
        f"- Assessment counts: `{json.dumps(summary.get('assessment_counts', {}), ensure_ascii=False, sort_keys=True)}`",
        f"- Raw calibration: `{json.dumps(calibration.get('raw', {}), sort_keys=True)}`",
        f"- Calibrated: `{json.dumps(calibration.get('calibrated', {}), sort_keys=True)}`",
        f"- Hypothetical avoided losers / foregone winners: {veto.get('avoided_loser_count', 0)} / {veto.get('foregone_winner_count', 0)}",
        f"- Hypothetical buy retention: {veto.get('hypothetical_buy_retention_pct')}",
        "",
        "## Next action",
        "",
    ]
    remaining = decision.get("remaining_for_real_runtime") or []
    lines.extend(f"- {item}" for item in remaining)
    lines.extend(
        [
            "",
            "> This report is counterfactual-only. `WOULD_BET` and `WOULD_NO_BET` are observer assessments, not trading actions.",
            "",
        ]
    )
    return "\n".join(lines)


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    descriptor, temp_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
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


def write_report(
    report: Mapping[str, Any], *, report_root: Path = Path("data/report")
) -> tuple[Path, Path]:
    target_date = str(report.get("target_date") or "")
    directory = report_root / "entry_odds_observer"
    json_path = directory / f"entry_odds_observer_{target_date}.json"
    markdown_path = directory / f"entry_odds_observer_{target_date}.md"
    _atomic_write(
        json_path,
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    _atomic_write(markdown_path, render_markdown(report))
    return json_path, markdown_path


def _read_json_rows(
    path: Path,
    *,
    collection_key: str | None = None,
    allow_missing: bool = False,
) -> list[dict[str, Any]]:
    if not path.exists():
        if allow_missing:
            return []
        raise FileNotFoundError(f"required offline odds input missing: {path}")
    if path.suffix == ".jsonl":
        rows: list[dict[str, Any]] = []
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
                if isinstance(value, dict):
                    rows.append(value)
                else:
                    raise ValueError(f"JSONL row is not an object: {path}")
        return rows
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON document: {path}: {exc.msg}") from exc
    if collection_key and isinstance(value, dict):
        value = value.get(collection_key)
    if not isinstance(value, list):
        raise ValueError(f"JSON input collection is not a list: {path}")
    if any(not isinstance(row, dict) for row in value):
        raise ValueError(f"JSON input collection contains non-object rows: {path}")
    return [dict(row) for row in value]


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-date", required=True)
    parser.add_argument("--predictions", type=Path)
    parser.add_argument("--calibration", type=Path)
    parser.add_argument("--trace", type=Path)
    parser.add_argument("--outcomes", type=Path)
    parser.add_argument("--report-root", type=Path, default=Path("data/report"))
    parser.add_argument(
        "--allow-missing-odds-inputs",
        action="store_true",
        help=(
            "write a hold_sample bootstrap report when raw predictions or "
            "calibration history is missing; trace and outcome inputs remain required"
        ),
    )
    args = parser.parse_args(argv)
    predictions_path = args.predictions or Path(
        f"data/entry_odds_observer/raw/entry_odds_raw_predictions_{args.target_date}.jsonl"
    )
    calibration_path = args.calibration or Path(
        "data/entry_odds_observer/calibration/entry_odds_calibration_history.jsonl"
    )
    trace_path = args.trace or Path(
        f"data/ai_decision_trace/ai_decision_trace_{args.target_date}.jsonl"
    )
    outcomes_path = (
        args.outcomes
        or Path("data/report/ai_decision_outcome_labels")
        / f"ai_decision_outcome_labels_{args.target_date}.json"
    )
    prediction_rows = _read_json_rows(
        predictions_path, allow_missing=args.allow_missing_odds_inputs
    )
    calibration_rows = _read_json_rows(
        calibration_path, allow_missing=args.allow_missing_odds_inputs
    )
    trace_rows = _read_json_rows(trace_path)
    outcome_rows = _read_json_rows(outcomes_path, collection_key="labels")
    report = build_report(
        target_date=args.target_date,
        predictions=prediction_rows,
        calibration_rows=calibration_rows,
        traces=trace_rows,
        outcome_labels=outcome_rows,
    )
    missing_odds_inputs = [
        name
        for name, path in (
            ("raw_predictions", predictions_path),
            ("calibration_history", calibration_path),
        )
        if not path.exists()
    ]
    if missing_odds_inputs:
        report["final_state"] = "hold_sample"
        report["source_quality_status"] = "blocked_missing_offline_odds_input"
        report["decision"]["identified"] = False
        report["summary"]["evaluation_blockers"] = sorted(
            set(report["summary"]["evaluation_blockers"])
            | {f"missing_{name}" for name in missing_odds_inputs}
        )
        report["source_quality_and_exclusion_manifest"][
            "required_input_gaps"
        ] = missing_odds_inputs
    report["input_manifest"] = {
        name: {
            "path": str(path),
            "status": "present" if path.exists() else "missing",
            "sha256": _file_sha256(path) if path.exists() else None,
            "row_count": len(rows),
        }
        for name, path, rows in (
            ("raw_predictions", predictions_path, prediction_rows),
            ("calibration_history", calibration_path, calibration_rows),
            ("immutable_ai_traces", trace_path, trace_rows),
            ("mature_outcome_labels", outcomes_path, outcome_rows),
        )
    }
    json_path, markdown_path = write_report(report, report_root=args.report_root)
    print(
        json.dumps(
            {
                "json": str(json_path),
                "markdown": str(markdown_path),
                "final_state": report["final_state"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
