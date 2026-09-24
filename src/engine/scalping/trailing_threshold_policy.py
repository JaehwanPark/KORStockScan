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
        {START_MARKET_ENV_KEYS[key]: values[key] for key in START_MARKETS}, 0.6
    )
    payload = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("ascii")).hexdigest()


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
    return {
        "schema": "scalp_trailing_threshold_receipt_v2",
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
    }
