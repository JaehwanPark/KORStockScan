"""Historical read-only helpers; no active policy publisher or CLI.

Only existing forensic consumers retain these calculations. Live callers use
their native role owners and permanent retirement fences.
"""

from __future__ import annotations


import json


import math


import re


from collections import Counter, defaultdict


from dataclasses import dataclass


from datetime import date, datetime, timedelta


from pathlib import Path


from typing import Any, Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[4]


OBSERVATION_PLAN_SCHEMA_VERSION = "ldm_hypothesis_observation_plan_v1"


SWING_POLICY_DIR = PROJECT_ROOT / "data" / "threshold_cycle" / "swing_sim_policies"


MAX_FEATURE_CARDINALITY = 40


MAX_MISSING_RATE = 0.80


MIN_SAMPLE_WEIGHT = 3


FORBIDDEN_USES = [
    "buy_sell_hold_live_rule",
    "threshold_apply",
    "provider_route_change",
    "bot_restart",
    "sizing_formula_runtime_apply_without_guard",
    "broker_order",
    "hard_safety_bypass",
]


IDENTITY_KEY_RE = re.compile(
    r"(?:^|_)(id|uuid|hash|code|name|record|candidate|sim_record|odno|order_no)(?:$|_)",
    re.I,
)


FUTURE_KEY_RE = re.compile(
    r"(profit|ev|pnl|return|mfe|mae|win|loss|outcome|result|future|label|sell|exit|close|joined_sample|sample|rate|count|generated|date|time|at$)",
    re.I,
)


FUTURE_VALUE_RE = re.compile(
    r"(profit|outcome|mfe|mae|sell|exit|loss|winner|missed|good_exit|bad_exit)", re.I
)


EXCLUDED_EXACT_FEATURE_KEYS = {
    "source_section",
    "decision_authority",
    "recommended_route",
    "recommended_resolution",
    "runtime_effect",
    "allowed_runtime_apply",
    "live_runtime_effect",
    "actual_order_submitted",
    "broker_order_forbidden",
    "source_quality_gate",
    "source_quality_status",
    "source_quality",
    "schema_version",
    "buy_price",
    "buy_qty",
    "qty",
    "curr_price",
    "current_price",
    "limit_price",
    "best_bid",
    "best_ask",
    "resolved_order_price",
}


RUNTIME_OBSERVABLE_REQUIREMENT_FIELDS = {
    "entry_score_parent",
    "entry_source_parent",
    "submit_quality_parent",
    "event_stage",
}


ARMING_OBSERVABLE_REQUIREMENT_FIELDS = {
    "entry_score_parent",
    "entry_source_parent",
}


@dataclass(frozen=True)
class SourceRow:
    source: str
    source_date: str
    features: dict[str, Any]
    profit_pct: float | None
    source_quality: str
    weight: int = 1


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _safe_float(value: Any, default: float | None = None) -> float | None:
    try:
        if value in (None, "", "-"):
            return default
        number = float(value)
        if math.isnan(number) or math.isinf(number):
            return default
        return number
    except Exception:
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, "", "-"):
            return default
        return int(float(value))
    except Exception:
        return default


def _is_forbidden_feature_key(key: str) -> bool:
    if not key:
        return True
    if key in EXCLUDED_EXACT_FEATURE_KEYS:
        return True
    tail = key.rsplit(".", 1)[-1]
    if tail in EXCLUDED_EXACT_FEATURE_KEYS:
        return True
    if IDENTITY_KEY_RE.search(key):
        return True
    if FUTURE_KEY_RE.search(key):
        return True
    return False


def _is_forbidden_feature_value(value: Any) -> bool:
    text = str(value or "").strip()
    if not text or text.lower() in {"none", "null", "nan"}:
        return True
    lowered = text.lower()
    if lowered in {
        "missing",
        "unknown",
        "unobserved",
        "not_evaluated",
        "not_instrumented",
        "-",
    }:
        return True
    if lowered.endswith(("_missing", "_unobserved")):
        return True
    if len(text) > 160:
        return True
    if FUTURE_VALUE_RE.search(text):
        return True
    return False


def _feature_items(
    rows: list[SourceRow],
) -> tuple[list[set[str]], dict[str, dict[str, Any]]]:
    raw_by_key: dict[str, list[Any]] = defaultdict(list)
    for row in rows:
        for key, value in row.features.items():
            if _is_forbidden_feature_key(key) or _is_forbidden_feature_value(value):
                continue
            raw_by_key[key].append(value)

    numeric_bins: dict[str, tuple[float, float]] = {}
    allowed_keys: set[str] = set()
    diagnostics: dict[str, dict[str, Any]] = {}
    total = max(1, len(rows))
    for key, values in raw_by_key.items():
        missing_rate = 1.0 - (len(values) / total)
        string_values = [str(v).strip() for v in values if str(v).strip()]
        unique_count = len(set(string_values))
        numeric_values = [
            _safe_float(v, None) for v in values if _safe_float(v, None) is not None
        ]
        is_numeric = len(numeric_values) >= max(3, int(len(values) * 0.8))
        diagnostics[key] = {
            "observed_count": len(values),
            "missing_rate": round(missing_rate, 4),
            "unique_count": unique_count,
            "numeric": is_numeric,
        }
        if len(values) < MIN_SAMPLE_WEIGHT:
            diagnostics[key]["excluded_reason"] = "observed_sample_floor"
            continue
        if (
            missing_rate > MAX_MISSING_RATE
            and key not in RUNTIME_OBSERVABLE_REQUIREMENT_FIELDS
        ):
            diagnostics[key]["excluded_reason"] = "missing_rate_cap"
            continue
        if is_numeric:
            ordered = sorted(numeric_values)
            low = ordered[int((len(ordered) - 1) * 0.33)]
            high = ordered[int((len(ordered) - 1) * 0.66)]
            numeric_bins[key] = (low, high)
            allowed_keys.add(key)
            continue
        if unique_count > MAX_FEATURE_CARDINALITY:
            diagnostics[key]["excluded_reason"] = "cardinality_cap"
            continue
        allowed_keys.add(key)

    itemsets: list[set[str]] = []
    for row in rows:
        items: set[str] = set()
        for key, value in row.features.items():
            if key not in allowed_keys or _is_forbidden_feature_value(value):
                continue
            if key in numeric_bins:
                numeric = _safe_float(value, None)
                if numeric is None:
                    continue
                low, high = numeric_bins[key]
                bucket = (
                    "low" if numeric <= low else "high" if numeric >= high else "mid"
                )
                items.add(f"{key}#bin={bucket}")
            else:
                items.add(f"{key}={str(value).strip()}")
        itemsets.append(items)
    return itemsets, diagnostics


def _validate_hypothesis_contract(hypothesis: dict[str, Any]) -> bool:
    if hypothesis.get("runtime_effect") is not False:
        return False
    if hypothesis.get("allowed_runtime_apply") is not False:
        return False
    if hypothesis.get("actual_order_submitted") is not False:
        return False
    if hypothesis.get("broker_order_forbidden") is not True:
        return False
    requirements = hypothesis.get("observable_requirements")
    if not requirements:
        return False
    if any(
        not isinstance(item, dict)
        or str(item.get("field") or "").strip()
        not in ARMING_OBSERVABLE_REQUIREMENT_FIELDS
        for item in requirements
    ):
        return False
    forbidden = set(hypothesis.get("forbidden_uses") or [])
    return set(FORBIDDEN_USES).issubset(forbidden)


def _validate_observation_plan_contract(plan: dict[str, Any]) -> bool:
    if plan.get("schema_version") != OBSERVATION_PLAN_SCHEMA_VERSION:
        return False
    if plan.get("runtime_effect") is not False:
        return False
    if plan.get("live_runtime_effect") is not False:
        return False
    if plan.get("allowed_runtime_apply") is not False:
        return False
    if plan.get("actual_order_submitted") is not False:
        return False
    if plan.get("broker_order_forbidden") is not True:
        return False
    forbidden = set(plan.get("forbidden_uses") or [])
    if not set(FORBIDDEN_USES).issubset(forbidden):
        return False
    hypotheses = plan.get("hypotheses")
    if not isinstance(hypotheses, list):
        return False
    if plan.get("hypothesis_count") is not None and _safe_int(
        plan.get("hypothesis_count"), -1
    ) != len(hypotheses):
        return False
    return all(
        isinstance(item, dict) and _validate_hypothesis_contract(item)
        for item in hypotheses
    )


def _merge_catalog(path: Path, plan: dict[str, Any], *, domain: str) -> bool:
    return False


def merge_sim_policy_catalogs(source_date: str, plan: dict[str, Any]) -> dict[str, Any]:
    paths = {
        "swing": SWING_POLICY_DIR / f"swing_sim_policy_catalog_{source_date}.json",
    }
    result: dict[str, Any] = {}
    for domain, path in paths.items():
        result[domain] = {
            "path": str(path),
            "merged": (
                _merge_catalog(path, plan, domain=domain) if path.exists() else False
            ),
        }
    return result
