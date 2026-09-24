"""Value and provenance contract for the live scalping trailing exit.

This scalping-owned module is shared by the bootstrap producer and the live
consumer.  It never selects a new value or grants order authority.
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Mapping

from src.utils.constants import TradingConfig

THRESHOLD_KEYS = (
    "SCALP_TRAILING_START_PCT",
    "SCALP_TRAILING_STRONG_AI_SCORE",
    "SCALP_TRAILING_LIMIT_WEAK",
    "SCALP_TRAILING_LIMIT_STRONG",
)
GRID_VERSION = "scalp_trailing_grid_0p1pct_5score_v1"
MAX_POSITION_SAMPLES = 256


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
    return {
        "schema": "scalp_trailing_threshold_receipt_v1",
        "decision_authority": "incumbent_values_only_no_candidate_apply",
        "values": values,
        "sources": sources,
        "value_sha256": value_hash(values),
    }
