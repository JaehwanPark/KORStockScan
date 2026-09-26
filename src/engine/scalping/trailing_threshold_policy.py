"""Value and provenance contract for the live scalping trailing exit.

This scalping-owned module is shared by the bootstrap producer and the live
consumer.  It never selects a new value or grants order authority.
"""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime
from typing import Any, Mapping
from zoneinfo import ZoneInfo

from src.trading.market import session_contract
from src.utils.constants import TradingConfig

THRESHOLD_KEYS = (
    "SCALP_TRAILING_START_PCT",
    "SCALP_TRAILING_STRONG_AI_SCORE",
    "SCALP_TRAILING_LIMIT_WEAK",
    "SCALP_TRAILING_LIMIT_STRONG",
)
GRID_VERSION = "scalp_trailing_grid_0p1pct_5score_v1"
MAX_POSITION_SAMPLES = 256
START_MARKETS = ("PREMARKET", "REGULAR", "INTEGRATED_AFTERMARKET")
START_GRID_PCT = tuple(round(step / 10, 1) for step in range(3, 13))
START_MARKET_ENV_KEYS = {
    market: f"KORSTOCKSCAN_SCALP_TRAILING_START_PCT_{market}"
    for market in START_MARKETS
}
MARKET_ENV_KEYS = {
    key: {market: f"KORSTOCKSCAN_{key}_{market}" for market in START_MARKETS}
    for key in THRESHOLD_KEYS
}
MARKET_VECTOR_SHA_ENV_KEY = "KORSTOCKSCAN_SCALP_TRAILING_MARKET_VECTOR_SHA256"
SELECTED_POLICY_SCHEMA = "scalp_trailing_four_axis_selected_policy_v1"


def market_type_at(epoch: float) -> str | None:
    """Classify an evaluation clock using the versioned session contract."""

    try:
        observed = datetime.fromtimestamp(float(epoch), ZoneInfo("Asia/Seoul"))
    except (TypeError, ValueError, OverflowError):
        return None
    context = session_contract.resolve_market_session(observed)
    if context.blocker:
        return None
    regime = context.session_regime
    if regime == session_contract.MARKET_SESSION_REGIME_LEGACY_PREMARKET:
        return "PREMARKET"
    if regime in {
        session_contract.MARKET_SESSION_REGIME_LEGACY_KRX_ONLY,
        session_contract.MARKET_SESSION_REGIME_KRX_REGULAR,
    }:
        return "REGULAR"
    if regime in {
        session_contract.MARKET_SESSION_REGIME_LEGACY_NXT_ONLY,
        session_contract.MARKET_SESSION_REGIME_KRX_NXT_AFTERMARKET,
        session_contract.MARKET_SESSION_REGIME_KRX_NXT_AFTERMARKET_CLOSE_ONLY,
        session_contract.MARKET_SESSION_REGIME_KRX_NXT_AFTERMARKET_TERMINAL_EXIT,
    }:
        return "INTEGRATED_AFTERMARKET"
    return None


def closed_exit_gap(previous_epoch: float, current_epoch: float) -> bool:
    """Allow skipped observations only while every intervening clock is closed."""

    if current_epoch <= previous_epoch + 2:
        return False
    cursor = previous_epoch + 2
    last = current_epoch - 2
    while cursor <= last:
        context = session_contract.resolve_market_session(
            datetime.fromtimestamp(cursor, ZoneInfo("Asia/Seoul"))
        )
        if context.blocker or context.exit_allowed_by_clock:
            return False
        cursor += 30
    context = session_contract.resolve_market_session(
        datetime.fromtimestamp(last, ZoneInfo("Asia/Seoul"))
    )
    return not context.blocker and not context.exit_allowed_by_clock


def start_values_from_env(
    env_values: Mapping[str, Any], incumbent_start: float
) -> dict[str, float]:
    """Fill absent market overrides from the existing scalar, never from zero."""

    values: dict[str, float] = {}
    for market, key in START_MARKET_ENV_KEYS.items():
        raw = env_values.get(key, incumbent_start)
        if isinstance(raw, bool):
            raise ValueError(f"{key}:boolean_value")
        value = float(raw)
        if not math.isfinite(value) or not 0 < value <= 100:
            raise ValueError(f"{key}:invalid_percent")
        values[market] = value
    return values


def start_values_hash(values: Mapping[str, Any]) -> str:
    if set(values) != set(START_MARKETS):
        raise ValueError("start_market_keys_mismatch")
    normalized = start_values_from_env(
        {START_MARKET_ENV_KEYS[key]: values[key] for key in START_MARKETS}, 0.4
    )
    payload = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("ascii")).hexdigest()


def market_values_from_env(
    env_values: Mapping[str, Any], scalar_values: Mapping[str, Any]
) -> dict[str, dict[str, float | int]]:
    """Resolve all four axes for each session from explicit or scalar values."""

    scalar = normalize_values(scalar_values)
    market_values = {
        market: normalize_values({
            key: env_values.get(MARKET_ENV_KEYS[key][market], scalar[key])
            for key in THRESHOLD_KEYS
        })
        for market in START_MARKETS
    }
    return _validate_market_widths(market_values)


def _validate_market_widths(values: dict[str, dict[str, float | int]]) -> dict[str, dict[str, float | int]]:
    for market, vector in values.items():
        if vector["SCALP_TRAILING_LIMIT_STRONG"] < vector["SCALP_TRAILING_LIMIT_WEAK"]:
            raise ValueError(f"{market}:strong_width_narrower_than_weak")
    return values


def market_values_hash(values: Mapping[str, Mapping[str, Any]]) -> str:
    if set(values) != set(START_MARKETS):
        raise ValueError("market_keys_mismatch")
    normalized = _validate_market_widths({
        market: normalize_values(values[market]) for market in START_MARKETS
    })
    payload = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("ascii")).hexdigest()


def selected_policy_env(
    policy: Mapping[str, Any], report: Mapping[str, Any], *,
    target_date: str, report_sha256: str,
) -> dict[str, str]:
    """Validate an explicit next-date selection against its immutable report."""

    if (policy.get("schema") != SELECTED_POLICY_SCHEMA
            or policy.get("family") != "scalp_trailing_four_axis_selector"
            or policy.get("target_date") != target_date
            or policy.get("allowed_runtime_apply") is not True
            or policy.get("runtime_effect") is not True
            or policy.get("apply_scope") != "one_stage_canary"):
        raise ValueError("selection_authority_invalid")
    source_date = str(policy.get("source_date") or "")
    try:
        if datetime.fromisoformat(source_date).date().isoformat() != source_date:
            raise ValueError("source_date_format")
        if datetime.fromisoformat(target_date).date().isoformat() != target_date:
            raise ValueError("target_date_format")
    except (TypeError, ValueError) as exc:
        raise ValueError("selection_date_invalid") from exc
    if (not source_date or source_date >= target_date
            or source_date < "2026-06-05"
            or report.get("date") != source_date
            or policy.get("source_report_sha256") != report_sha256):
        raise ValueError("source_report_binding_invalid")
    population = report.get("completed_population_quality") or {}
    research = report.get("trailing_four_axis_market_tuning") or {}
    candidate = research.get("research_candidate") or {}
    if (population.get("complete") is not True
            or research.get("population_complete") is not True
            or research.get("status") != "research_candidate_holdout_positive_review_required"
            or not candidate or candidate.get("decision_authority")
                != "research_candidate_requires_policy_selection"):
        raise ValueError("research_candidate_not_eligible")
    values = policy.get("market_values")
    if (not isinstance(values, dict)
            or values != candidate.get("values")
            or market_values_hash(values) != policy.get("market_values_sha256")
            or policy.get("market_values_sha256")
                != candidate.get("market_values_sha256")):
        raise ValueError("selected_vector_mismatch")
    evidence = research.get("joint_selection_evidence") or {}
    if (evidence.get("winner_sha256") != policy.get("market_values_sha256")
            or evidence.get("tail_review_required") is not False
            or not isinstance(evidence.get("holdout_conservative_delta_krw"), (int, float))
            or evidence["holdout_conservative_delta_krw"] <= 0
            or not isinstance(
                evidence.get("holdout_conservative_worst_slippage_delta_krw"),
                (int, float),
            )
            or evidence["holdout_conservative_worst_slippage_delta_krw"] <= 0
            or not isinstance(
                evidence.get("holdout_worst_slippage_min_day_ev_pct"), (int, float)
            )
            or evidence["holdout_worst_slippage_min_day_ev_pct"] <= 0):
        raise ValueError("selection_safety_evidence_invalid")
    parent = str(policy.get("rollback_market_values_sha256") or "")
    if len(parent) != 64 or any(char not in "0123456789abcdef" for char in parent):
        raise ValueError("rollback_parent_hash_invalid")
    review = policy.get("selection_review") or {}
    if (not isinstance(review, dict)
            or review.get("status") != "reviewed_one_stage_canary"
            or review.get("candidate_sha256") != policy.get("market_values_sha256")
            or review.get("source_quality") != "pass"
            or review.get("execution_model") != "pass"
            or review.get("same_stage_owner") != "scalp_trailing_take_profit"
            or review.get("rollback_sha256") != parent):
        raise ValueError("selection_review_missing_or_invalid")
    return {
        MARKET_ENV_KEYS[key][market]: str(values[market][key])
        for market in START_MARKETS for key in THRESHOLD_KEYS
    }


def default_values() -> dict[str, float | int]:
    defaults = TradingConfig()
    return {key: getattr(defaults, key) for key in THRESHOLD_KEYS}


def normalize_values(values: Mapping[str, Any]) -> dict[str, float | int]:
    """Reject malformed values without silently changing a live threshold."""

    normalized: dict[str, float | int] = {}
    for key in THRESHOLD_KEYS:
        raw = values[key]
        if isinstance(raw, bool):
            raise ValueError(f"{key}:boolean_value")
        number = float(raw)
        if not math.isfinite(number):
            raise ValueError(f"{key}:non_finite_value")
        if key == "SCALP_TRAILING_STRONG_AI_SCORE":
            if not number.is_integer() or not 0 < number <= 100:
                raise ValueError(f"{key}:invalid_score")
            normalized[key] = int(number)
        else:
            if not 0 < number <= 100:
                raise ValueError(f"{key}:invalid_percent")
            normalized[key] = number
    return normalized


def value_hash(values: Mapping[str, Any]) -> str:
    normalized = normalize_values(values)
    payload = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("ascii")).hexdigest()


def bootstrap_receipt(
    env_values: Mapping[str, str], env_owners: Mapping[str, str]
) -> dict[str, Any]:
    defaults = default_values()
    values = normalize_values(
        {
            key: env_values.get(f"KORSTOCKSCAN_{key}", defaults[key])
            for key in THRESHOLD_KEYS
        }
    )
    sources = {
        key: env_owners.get(f"KORSTOCKSCAN_{key}", "code_default")
        for key in THRESHOLD_KEYS
    }
    start_by_market = start_values_from_env(
        env_values, float(values["SCALP_TRAILING_START_PCT"])
    )
    market_values = market_values_from_env(env_values, values)
    return {
        "schema": "scalp_trailing_threshold_receipt_v3",
        "decision_authority": "incumbent_values_only_no_candidate_apply",
        "values": values,
        "sources": sources,
        "value_sha256": value_hash(values),
        "start_by_market": start_by_market,
        "start_by_market_sources": {
            market: env_owners.get(
                START_MARKET_ENV_KEYS[market],
                sources["SCALP_TRAILING_START_PCT"],
            )
            for market in START_MARKETS
        },
        "start_by_market_sha256": start_values_hash(start_by_market),
        "market_values": market_values,
        "market_value_sources": {
            market: {
                key: env_owners.get(MARKET_ENV_KEYS[key][market], sources[key])
                for key in THRESHOLD_KEYS
            }
            for market in START_MARKETS
        },
        "market_values_sha256": market_values_hash(market_values),
    }
