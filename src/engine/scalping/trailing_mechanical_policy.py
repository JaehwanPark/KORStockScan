"""Three-market take-profit values and mechanical strength identity.

The holding soft-stop AI score belongs to a different consumer. This module
does not grant orders or approve a later economic tuning candidate.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from datetime import date
from functools import lru_cache
from typing import Any, Mapping

from src.engine.scalping.trailing_mechanical_strength import (
    VERSION as CLASSIFIER_VERSION, CONFIG_DEFAULTS, normalize_config,
)
from src.engine.scalping.trailing_threshold_policy import START_MARKETS, market_type_at


TP_KEYS = (
    "SCALP_TRAILING_START_PCT",
    "SCALP_TRAILING_LIMIT_WEAK",
    "SCALP_TRAILING_LIMIT_STRONG",
)
DEFAULTS = {
    "SCALP_TRAILING_START_PCT": 0.4,
    "SCALP_TRAILING_LIMIT_WEAK": 0.4,
    "SCALP_TRAILING_LIMIT_STRONG": 0.8,
}
MARKET_ENV_KEYS = {
    key: {market: f"KORSTOCKSCAN_{key}_{market}" for market in START_MARKETS}
    for key in TP_KEYS
}
VECTOR_SHA_ENV_KEY = "KORSTOCKSCAN_SCALP_TRAILING_MECHANICAL_VECTOR_SHA256"
CLASSIFIER_ENV_KEY = "KORSTOCKSCAN_SCALP_TRAILING_STRENGTH_VERSION"
SELECTED_SCHEMA = "scalp_trailing_mechanical_combined_selected_policy_v2"
BASELINE_SCHEMA = "scalp_trailing_mechanical_baseline_receipt_v2"
SELECTED_RECEIPT_SCHEMA = "scalp_trailing_mechanical_selected_receipt_v2"
CLASSIFIER_PARAMS = dict(CONFIG_DEFAULTS)
CLASSIFIER_MARKET_ENV_KEYS = {
    key: {market: f"KORSTOCKSCAN_SCALP_TRAILING_CLASSIFIER_{key.upper()}_{market}"
          for market in START_MARKETS}
    for key in CONFIG_DEFAULTS
}


def _env_numeric(raw: Any, key: str) -> int | float:
    if isinstance(raw, bool):
        raise ValueError(f"classifier_{key}_boolean_invalid")
    if isinstance(raw, str):
        if not raw or raw.strip() != raw:
            raise ValueError(f"classifier_{key}_env_invalid")
        try:
            raw = float(raw)
        except ValueError as exc:
            raise ValueError(f"classifier_{key}_env_invalid") from exc
    return raw


def market_classifier_from_env(env: Mapping[str, Any]) -> dict[str, dict[str, int | float]]:
    return {
        market: normalize_config({
            key: _env_numeric(env.get(CLASSIFIER_MARKET_ENV_KEYS[key][market], default), key)
            for key, default in CONFIG_DEFAULTS.items()
        }) for market in START_MARKETS
    }


@lru_cache(maxsize=8)
def _loaded_classifier(
    pid: int, vector_sha256: str, bootstrap_date: str, classifier_version: str,
) -> tuple[dict[str, dict[str, int | float]], str]:
    """Pin the process's classifier config at its bootstrap policy identity."""

    values = market_classifier_from_env(os.environ)
    return values, classifier_hash(values)


def runtime_classifier_snapshot() -> tuple[dict[str, dict[str, int | float]], str]:
    return _loaded_classifier(
        os.getpid(), str(os.getenv(VECTOR_SHA_ENV_KEY) or ""),
        str(os.getenv("KORSTOCKSCAN_RUNTIME_POLICY_BOOTSTRAP_DATE") or ""),
        str(os.getenv(CLASSIFIER_ENV_KEY) or CLASSIFIER_VERSION),
    )


def classifier_hash(configs: Mapping[str, Mapping[str, Any]] | None = None) -> str:
    normalized = (
        {market: normalize_config(configs[market]) for market in START_MARKETS}
        if configs is not None else
        {market: dict(CONFIG_DEFAULTS) for market in START_MARKETS}
    )
    if set(normalized) != set(START_MARKETS):
        raise ValueError("classifier_market_keys_invalid")
    payload = {"version": CLASSIFIER_VERSION, "market_parameters": normalized}
    return hashlib.sha256(json.dumps(payload, sort_keys=True,
                                     separators=(",", ":")).encode("ascii")).hexdigest()


def normalize_values(values: Mapping[str, Any]) -> dict[str, float]:
    if not isinstance(values, Mapping) or set(values) != set(TP_KEYS):
        raise ValueError("tp_keys_invalid")
    result = {}
    for key in TP_KEYS:
        raw = values[key]
        if isinstance(raw, bool) or not isinstance(raw, (int, float)):
            raise ValueError(f"{key}:numeric_value_required")
        value = float(raw)
        if not math.isfinite(value) or not 0 < value <= 100:
            raise ValueError(f"{key}:invalid_percent")
        result[key] = value
    if result["SCALP_TRAILING_LIMIT_STRONG"] < result["SCALP_TRAILING_LIMIT_WEAK"]:
        raise ValueError("strong_width_narrower_than_weak")
    return result


def market_values_from_env(
    env: Mapping[str, Any], scalar: Mapping[str, Any] | None = None,
) -> dict[str, dict[str, float]]:
    baseline = normalize_values(scalar or DEFAULTS)
    return {
        market: normalize_values({
            key: _env_numeric(env.get(MARKET_ENV_KEYS[key][market], baseline[key]), key)
            for key in TP_KEYS
        }) for market in START_MARKETS
    }


def market_values_hash(
    values: Mapping[str, Mapping[str, Any]],
    classifier_values: Mapping[str, Mapping[str, Any]] | None = None,
) -> str:
    return market_values_hash_with_classifier_digest(
        values, classifier_hash(classifier_values)
    )


def market_values_hash_with_classifier_digest(
    values: Mapping[str, Mapping[str, Any]], classifier_digest: str,
) -> str:
    """Hash a vector with the process-pinned, already validated M1 digest."""

    if set(values) != set(START_MARKETS):
        raise ValueError("market_keys_mismatch")
    if (not isinstance(classifier_digest, str) or len(classifier_digest) != 64
            or any(ch not in "0123456789abcdef" for ch in classifier_digest)):
        raise ValueError("classifier_digest_invalid")
    normalized = {market: normalize_values(values[market]) for market in START_MARKETS}
    payload = {"classifier_version": CLASSIFIER_VERSION,
               "classifier_sha256": classifier_digest,
               "market_values": normalized}
    return hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(",", ":"), allow_nan=False,
    ).encode("ascii")).hexdigest()


@lru_cache(maxsize=8)
def _loaded_policy_vector(
    pid: int, expected_sha256: str, bootstrap_date: str,
    scalar_items: tuple[tuple[str, float], ...],
) -> tuple[dict[str, dict[str, float]], dict[str, dict[str, int | float]], str, str]:
    scalar = dict(scalar_items)
    values = market_values_from_env(os.environ, scalar)
    classifier_values, classifier_digest = runtime_classifier_snapshot()
    digest = market_values_hash_with_classifier_digest(values, classifier_digest)
    if digest != expected_sha256:
        raise ValueError("runtime_mechanical_vector_hash_mismatch")
    return values, classifier_values, classifier_digest, digest


def runtime_policy_vector_snapshot(
    scalar: Mapping[str, Any],
) -> tuple[dict[str, dict[str, float]], dict[str, dict[str, int | float]], str, str]:
    """Read a verified bootstrap vector once per process; preserve default tests."""

    expected = str(os.getenv(VECTOR_SHA_ENV_KEY) or "")
    if expected:
        scalar_items = tuple(sorted(normalize_values(scalar).items()))
        return _loaded_policy_vector(
            os.getpid(), expected,
            str(os.getenv("KORSTOCKSCAN_RUNTIME_POLICY_BOOTSTRAP_DATE") or ""),
            scalar_items,
        )
    values = market_values_from_env(os.environ, scalar)
    classifier_values, classifier_digest = runtime_classifier_snapshot()
    return (values, classifier_values, classifier_digest,
            market_values_hash_with_classifier_digest(values, classifier_digest))


def value_hash(values: Mapping[str, Any]) -> str:
    return hashlib.sha256(json.dumps(
        normalize_values(values), sort_keys=True,
        separators=(",", ":"), allow_nan=False,
    ).encode("ascii")).hexdigest()


def baseline_receipt(env: Mapping[str, Any], *, source: str) -> dict[str, Any]:
    """Attest the M1 vector under its distinct baseline or selected authority."""

    if source not in {"operator_directed_m1_baseline", "reviewed_selected_candidate",
                      "rollback_incumbent"}:
        raise ValueError("mechanical_receipt_source_invalid")

    scalar = normalize_values({
        key: _env_numeric(env.get(f"KORSTOCKSCAN_{key}", DEFAULTS[key]), key)
        for key in TP_KEYS
    })
    values = market_values_from_env(env, scalar)
    classifier_values = market_classifier_from_env(env)
    if any(key in env for key in (
        "KORSTOCKSCAN_SCALP_TRAILING_STRONG_AI_SCORE_PREMARKET",
        "KORSTOCKSCAN_SCALP_TRAILING_STRONG_AI_SCORE_REGULAR",
        "KORSTOCKSCAN_SCALP_TRAILING_STRONG_AI_SCORE_INTEGRATED_AFTERMARKET",
    )):
        raise ValueError("legacy_tp_score_override_present")
    expected = str(env.get(VECTOR_SHA_ENV_KEY) or "")
    digest = market_values_hash(values, classifier_values)
    if expected and expected != digest:
        raise ValueError("mechanical_market_vector_hash_mismatch")
    version = str(env.get(CLASSIFIER_ENV_KEY) or CLASSIFIER_VERSION)
    if version != CLASSIFIER_VERSION:
        raise ValueError("mechanical_classifier_version_mismatch")
    return {
        "schema": (SELECTED_RECEIPT_SCHEMA if source == "reviewed_selected_candidate"
                   else BASELINE_SCHEMA),
        "classifier_version": CLASSIFIER_VERSION,
        "classifier_sha256": classifier_hash(classifier_values),
        "classifier_parameters": classifier_values,
        "market_values": values,
        "scalar_values": scalar,
        "market_values_sha256": digest,
        "source": source,
        "decision_authority": (
            "reviewed_selected_candidate_with_source_binding"
            if source == "reviewed_selected_candidate"
            else "operator_directed_baseline_replacement_no_tuning_authority"
        ),
        "runtime_effect": True,
    }


def selected_policy_env(
    policy: Mapping[str, Any], report: Mapping[str, Any], *,
    target_date: str, report_sha256: str,
) -> dict[str, str]:
    """A later tuned policy needs direct M1 holdout, review and rollback."""

    if (policy.get("schema") != SELECTED_SCHEMA
            or policy.get("family") != "scalp_trailing_mechanical_three_axis_selector"
            or policy.get("target_date") != target_date
            or policy.get("allowed_runtime_apply") is not True
            or policy.get("runtime_effect") is not True
            or policy.get("apply_scope") != "one_stage_canary"):
        raise ValueError("selection_authority_invalid")
    source_date = str(policy.get("source_date") or "")
    try:
        if (date.fromisoformat(source_date).isoformat() != source_date
                or date.fromisoformat(target_date).isoformat() != target_date
                or not "2026-06-05" <= source_date < target_date):
            raise ValueError
    except ValueError as exc:
        raise ValueError("selection_date_invalid") from exc
    if (report.get("date") != source_date
            or policy.get("source_report_sha256") != report_sha256
            or (report.get("meta") or {}).get("snapshot_profile") != "postclose_exit"
            or (report.get("mechanical_population_quality") or {}).get("complete") is not True):
        raise ValueError("source_report_binding_invalid")
    research = report.get("trailing_mechanical_market_tuning") or {}
    candidate = research.get("research_candidate") or {}
    evidence = research.get("joint_selection_evidence") or {}
    values = policy.get("market_values")
    classifier_values = policy.get("classifier_parameters")
    digest = (market_values_hash(values, classifier_values)
              if isinstance(values, dict) and isinstance(classifier_values, dict) else "")
    if (research.get("schema") != "scalp_trailing_mechanical_market_tuning_v2"
            or research.get("population_complete") is not True
            or research.get("status") != "research_candidate_holdout_positive_review_required"
            or candidate.get("decision_authority") != "research_candidate_requires_policy_selection"
            or candidate.get("values") != values
            or candidate.get("classifier_parameters") != classifier_values
            or candidate.get("market_values_sha256") != digest
            or policy.get("market_values_sha256") != digest
            or policy.get("classifier_version") != CLASSIFIER_VERSION
            or policy.get("classifier_sha256") != classifier_hash(classifier_values)
            or evidence.get("winner_sha256") != digest
            or evidence.get("tail_review_required") is not False):
        raise ValueError("research_candidate_not_eligible")
    for key in (
        "holdout_conservative_delta_krw",
        "holdout_conservative_worst_slippage_delta_krw",
        "holdout_worst_slippage_min_day_ev_pct",
    ):
        value = evidence.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
            raise ValueError("selection_safety_evidence_invalid")
    if len(research.get("holdout_days") or []) < 2:
        raise ValueError("selection_holdout_dates_insufficient")
    classifier_research = research.get("classifier_policy_research") or {}
    classifier_candidate = classifier_research.get("research_candidate") or {}
    if classifier_candidate.get("market_values_sha256") == digest:
        detail = (classifier_research.get("candidates") or {}).get(digest) or {}
        if (detail.get("values") != values
                or detail.get("classifier_parameters") != classifier_values
                or len(detail.get("changed_train_ids") or []) < 10
                or len(detail.get("changed_holdout_ids") or []) < 5
                or detail.get("changed_train_symbol_count", 0) < 2
                or detail.get("changed_holdout_symbol_count", 0) < 2):
            raise ValueError("classifier_candidate_support_invalid")
    else:
        detail = (research.get("joint_three_market") or {}).get(digest) or {}
        if detail.get("values") != values:
            raise ValueError("numeric_candidate_support_invalid")
    train = detail.get("train") or {}
    holdout = detail.get("holdout") or {}
    worst = (holdout.get("execution_slippage_sensitivity") or {}).get("100") or {}
    if (train.get("n", 0) < 30 or holdout.get("n", 0) < 10
            or train.get("paired_ev_pct") is None or train["paired_ev_pct"] <= 0
            or holdout.get("paired_ev_pct") is None or holdout["paired_ev_pct"] <= 0
            or worst.get("paired_ev_pct") is None or worst["paired_ev_pct"] <= 0
            or train.get("large_loss_worsened_ids")
            or holdout.get("large_loss_worsened_ids")):
        raise ValueError("candidate_support_or_safety_invalid")
    parent = str(policy.get("rollback_market_values_sha256") or "")
    review = policy.get("selection_review") or {}
    if (len(parent) != 64 or any(c not in "0123456789abcdef" for c in parent)
            or review.get("status") != "reviewed_one_stage_canary"
            or review.get("candidate_sha256") != digest
            or review.get("source_quality") != "pass"
            or review.get("execution_model") != "pass"
            or review.get("same_stage_owner") != "scalp_trailing_take_profit"
            or review.get("rollback_sha256") != parent):
        raise ValueError("selection_review_missing_or_invalid")
    selected = {MARKET_ENV_KEYS[key][market]: str(values[market][key])
                for market in START_MARKETS for key in TP_KEYS}
    selected.update({
        CLASSIFIER_MARKET_ENV_KEYS[key][market]: str(classifier_values[market][key])
        for market in START_MARKETS for key in CONFIG_DEFAULTS
    })
    return selected
