"""Build deterministic LDM soft hypotheses for sim observation planning."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Iterable

from src.engine.daily_threshold_cycle_report import REPORT_DIR
from src.utils.jsonl_io import iter_jsonl


PROJECT_ROOT = Path(__file__).resolve().parents[3]
REPORT_TYPE = "ldm_hypothesis_discovery"
REPORT_SCHEMA_VERSION = "ldm_hypothesis_discovery_v1"
OBSERVATION_PLAN_SCHEMA_VERSION = "ldm_hypothesis_observation_plan_v1"
REPORT_OUT_DIR = REPORT_DIR / REPORT_TYPE
POST_SELL_DIR = PROJECT_ROOT / "data" / "post_sell"
PIPELINE_EVENTS_DIR = PROJECT_ROOT / "data" / "pipeline_events"
PLAN_DIR = PROJECT_ROOT / "data" / "threshold_cycle" / "ldm_hypothesis_observation_plans"
SCALP_POLICY_DIR = PROJECT_ROOT / "data" / "threshold_cycle" / "scalp_sim_policies"
SWING_POLICY_DIR = PROJECT_ROOT / "data" / "threshold_cycle" / "swing_sim_policies"

MAX_JSONL_ROWS_PER_FILE = 20000
MAX_CANDIDATES = 120
MAX_OUTPUT_HYPOTHESES = 24
MAX_FEATURE_CARDINALITY = 40
MAX_MISSING_RATE = 0.80
MIN_SAMPLE_WEIGHT = 3
MIN_CONTRAST_GROUPS = 2
MAX_ITEMSET_SIZE = 3

FORBIDDEN_USES = [
    "buy_sell_hold_live_rule",
    "threshold_apply",
    "provider_route_change",
    "bot_restart",
    "sizing_formula_runtime_apply_without_guard",
    "broker_order",
    "hard_safety_bypass",
]
ALLOWED_DOWNSTREAM_EFFECTS = [
    "sim_budget_allocation",
    "contrastive_sample_collection",
    "source_quality_gap_surfacing",
    "runtime_effect_false_workorder_candidate",
]
IDENTITY_KEY_RE = re.compile(r"(?:^|_)(id|uuid|hash|code|name|record|candidate|sim_record|odno|order_no)(?:$|_)", re.I)
FUTURE_KEY_RE = re.compile(
    r"(profit|ev|pnl|return|mfe|mae|win|loss|outcome|result|future|label|sell|exit|close|joined_sample|sample|rate|count|generated|date|time|at$)",
    re.I,
)
FUTURE_VALUE_RE = re.compile(r"(profit|outcome|mfe|mae|sell|exit|loss|winner|missed|good_exit|bad_exit)", re.I)
OK_QUALITY_VALUES = {"", "-", "ok", "pass", "passed", "ready", "true"}
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


def report_paths(target_date: str) -> tuple[Path, Path]:
    base = REPORT_OUT_DIR / f"{REPORT_TYPE}_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def observation_plan_path(apply_date: str) -> Path:
    return PLAN_DIR / f"ldm_hypothesis_observation_plan_{apply_date}.json"


def _date_range(start: str, end: str) -> list[str]:
    start_d = date.fromisoformat(start)
    end_d = date.fromisoformat(end)
    days: list[str] = []
    current = start_d
    while current <= end_d:
        days.append(current.isoformat())
        current += timedelta(days=1)
    return days


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


def _first_present(*values: Any) -> Any:
    for value in values:
        if value not in (None, ""):
            return value
    return None


def _quality_from_mapping(payload: dict[str, Any]) -> str:
    probes = (
        payload.get("source_quality_status"),
        payload.get("source_quality"),
        payload.get("risk_regime_context_status"),
        payload.get("source_quality_gate"),
    )
    for value in probes:
        text = str(value or "").strip()
        if text:
            return text
    return "unknown"


def _outcome_group(row: SourceRow) -> str:
    quality = row.source_quality.lower()
    if quality and quality not in OK_QUALITY_VALUES and any(token in quality for token in ("block", "fail", "warning", "unknown")):
        return "source_quality_blocked"
    outcome_text = " ".join(
        f"{key}={value}"
        for key, value in row.features.items()
        if any(token in str(key).lower() for token in ("outcome", "result", "exit", "sell"))
    ).lower()
    if "missed_upside" in outcome_text:
        return "missed_upside"
    profit = row.profit_pct
    if profit is None:
        return "source_quality_blocked"
    if profit <= -2.0:
        return "severe_loss"
    if profit < -0.15:
        return "negative"
    if -0.15 <= profit <= 0.15:
        return "neutral_flat"
    return "positive"


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
    if lowered in {"missing", "unknown", "unobserved", "not_evaluated", "not_instrumented", "-"}:
        return True
    if lowered.endswith(("_missing", "_unobserved")):
        return True
    if len(text) > 160:
        return True
    if FUTURE_VALUE_RE.search(text):
        return True
    return False


def _flatten_features(payload: dict[str, Any], *, prefix: str = "") -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, value in payload.items():
        key_text = str(key or "").strip()
        if not key_text:
            continue
        full_key = f"{prefix}.{key_text}" if prefix else key_text
        if isinstance(value, dict):
            output.update(_flatten_features(value, prefix=full_key))
        elif isinstance(value, (str, int, float, bool)) or value is None:
            output[full_key] = value
    return output


def _feature_items(rows: list[SourceRow]) -> tuple[list[set[str]], dict[str, dict[str, Any]]]:
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
        numeric_values = [_safe_float(v, None) for v in values if _safe_float(v, None) is not None]
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
        if missing_rate > MAX_MISSING_RATE and key not in RUNTIME_OBSERVABLE_REQUIREMENT_FIELDS:
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
                bucket = "low" if numeric <= low else "high" if numeric >= high else "mid"
                items.add(f"{key}#bin={bucket}")
            else:
                items.add(f"{key}={str(value).strip()}")
        itemsets.append(items)
    return itemsets, diagnostics


def _extract_metric_row(section: str, source_date: str, row: dict[str, Any]) -> SourceRow | None:
    profit = _safe_float(
        row.get("source_quality_adjusted_ev_pct")
        if row.get("source_quality_adjusted_ev_pct") is not None
        else row.get("equal_weight_avg_profit_pct"),
        None,
    )
    features = _flatten_features(row)
    features["source_section"] = section
    weight = max(1, _safe_int(row.get("joined_sample") or row.get("sample"), 1))
    return SourceRow(
        source=section,
        source_date=source_date,
        features=features,
        profit_pct=profit,
        source_quality=_quality_from_mapping(row),
        weight=weight,
    )


def _load_ldm_rows(target_date: str) -> list[SourceRow]:
    rows: list[SourceRow] = []
    ldm_path = REPORT_DIR / "lifecycle_decision_matrix" / f"lifecycle_decision_matrix_{target_date}.json"
    payload = _load_json(ldm_path)
    for section in (
        "lifecycle_flow_bucket_attribution",
        "entry_bucket_attribution",
        "submit_bucket_attribution",
        "holding_bucket_attribution",
        "exit_bucket_attribution",
        "scale_in_bucket_attribution",
        "overnight_bucket_attribution",
    ):
        body = payload.get(section) if isinstance(payload.get(section), dict) else {}
        for bucket in body.get("buckets") or []:
            if isinstance(bucket, dict):
                item = _extract_metric_row(section, target_date, bucket)
                if item:
                    rows.append(item)
    discovery_path = REPORT_DIR / "lifecycle_bucket_discovery" / f"lifecycle_bucket_discovery_{target_date}.json"
    discovery = _load_json(discovery_path)
    for parent in discovery.get("parent_bucket_summaries") or []:
        if not isinstance(parent, dict):
            continue
        features = {}
        dimensions = parent.get("dimension_filters") if isinstance(parent.get("dimension_filters"), dict) else {}
        features.update(dimensions)
        features["source_parent_family"] = parent.get("parent_bucket_family") or parent.get("bucket_type")
        rows.append(
            SourceRow(
                source="lifecycle_bucket_discovery_parent",
                source_date=target_date,
                features=features,
                profit_pct=_safe_float(parent.get("parent_source_quality_adjusted_ev_pct"), None),
                source_quality=_quality_from_mapping(parent),
                weight=max(1, _safe_int(parent.get("parent_joined_sample") or parent.get("sample"), 1)),
            )
        )
    swing_path = REPORT_DIR / "swing_lifecycle_decision_matrix" / f"swing_lifecycle_decision_matrix_{target_date}.json"
    swing = _load_json(swing_path)
    for section in (
        "swing_lifecycle_flow_bucket_attribution",
        "entry_bucket_attribution",
        "holding_exit_bucket_attribution",
        "scale_in_bucket_attribution",
        "discovery_arm_attribution",
    ):
        body = swing.get(section) if isinstance(swing.get(section), dict) else {}
        for bucket in body.get("buckets") or []:
            if isinstance(bucket, dict):
                item = _extract_metric_row(f"swing_{section}", target_date, bucket)
                if item:
                    rows.append(item)
    return rows


def _load_jsonl_rows(path: Path, source: str, source_date: str) -> list[SourceRow]:
    rows: list[SourceRow] = []
    if not path.exists():
        return rows
    for index, payload in enumerate(iter_jsonl(path)):
        if index >= MAX_JSONL_ROWS_PER_FILE:
            break
        if not isinstance(payload, dict):
            continue
        fields = payload.get("fields") if isinstance(payload.get("fields"), dict) else payload
        profit = _safe_float(
            _first_present(fields.get("profit_rate"), fields.get("trigger_profit_rate"), payload.get("profit_rate")),
            None,
        )
        features = _flatten_features(fields)
        features["source_section"] = source
        if payload.get("stage") is not None:
            features["event_stage"] = payload.get("stage")
        rows.append(
            SourceRow(
                source=source,
                source_date=source_date,
                features=features,
                profit_pct=profit,
                source_quality=_quality_from_mapping(fields),
                weight=1,
            )
        )
    return rows


def load_source_rows(source_start: str, target_date: str) -> tuple[list[SourceRow], list[dict[str, Any]]]:
    rows: list[SourceRow] = []
    diagnostics: list[dict[str, Any]] = []
    for day in _date_range(source_start, target_date):
        before = len(rows)
        rows.extend(_load_ldm_rows(day))
        for name in (
            "sim_post_sell_candidates",
            "sim_post_sell_evaluations",
            "post_sell_candidates",
            "post_sell_evaluations",
        ):
            rows.extend(_load_jsonl_rows(POST_SELL_DIR / f"{name}_{day}.jsonl", name, day))
        rows.extend(_load_jsonl_rows(PIPELINE_EVENTS_DIR / f"pipeline_events_{day}.jsonl", "pipeline_events", day))
        diagnostics.append({"date": day, "loaded_rows": len(rows) - before})
    return rows, diagnostics


def _signature_for_items(items: tuple[str, ...]) -> str:
    raw = "|".join(sorted(items))
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def _requirements_from_items(items: Iterable[str], *, allowed_fields: set[str] | None = None) -> list[dict[str, str]]:
    requirements: list[dict[str, str]] = []
    for item in sorted(items):
        if "#bin=" in item:
            field, value = item.split("#bin=", 1)
            if allowed_fields is not None and field not in allowed_fields:
                continue
            requirements.append({"field": field, "op": "bin_eq", "value": value})
        elif "=" in item:
            field, value = item.split("=", 1)
            if allowed_fields is not None and field not in allowed_fields:
                continue
            requirements.append({"field": field, "op": "eq", "value": value})
    return requirements


def _requirement_signature(requirements: list[dict[str, str]]) -> str:
    raw = "|".join(
        f"{item.get('field')}:{item.get('op')}:{item.get('value')}"
        for item in sorted(requirements, key=lambda item: (item.get("field") or "", item.get("op") or "", item.get("value") or ""))
    )
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def _has_runtime_observable_requirement(items: Iterable[str]) -> bool:
    for item in items:
        field = item.split("#bin=", 1)[0] if "#bin=" in item else item.split("=", 1)[0]
        if field in RUNTIME_OBSERVABLE_REQUIREMENT_FIELDS:
            return True
    return False


def _evaluate_itemset(items: tuple[str, ...], rows: list[SourceRow], row_items: list[set[str]]) -> dict[str, Any] | None:
    selected: list[SourceRow] = [row for row, itemset in zip(rows, row_items) if set(items).issubset(itemset)]
    sample_weight = sum(row.weight for row in selected)
    if sample_weight < MIN_SAMPLE_WEIGHT:
        return None
    groups = Counter()
    weighted_profit = 0.0
    profit_weight = 0
    dates = set()
    downside_weight = 0
    for row in selected:
        group = _outcome_group(row)
        groups[group] += row.weight
        dates.add(row.source_date)
        if row.profit_pct is not None:
            weighted_profit += row.profit_pct * row.weight
            profit_weight += row.weight
            if row.profit_pct < 0:
                downside_weight += row.weight
    contrast_group_count = len([group for group, count in groups.items() if count > 0])
    runtime_observable = _has_runtime_observable_requirement(items)
    if contrast_group_count < MIN_CONTRAST_GROUPS and not runtime_observable:
        return None
    ev = weighted_profit / profit_weight if profit_weight else 0.0
    positive = groups.get("positive", 0)
    negative = groups.get("negative", 0) + groups.get("severe_loss", 0)
    contrast_delta = ev - ((negative / sample_weight) * abs(ev) if sample_weight else 0.0)
    drift_score = 1.0 / max(1, len(dates))
    score = abs(contrast_delta) * math.log(sample_weight + 1) * max(1, len(dates))
    return {
        "items": items,
        "sample_weight": sample_weight,
        "source_quality_adjusted_ev_pct": round(ev, 4),
        "repeated_date_count": len(dates),
        "contrast_group_counts": dict(sorted(groups.items())),
        "contrast_coverage_status": "pass" if contrast_group_count >= MIN_CONTRAST_GROUPS else "needs_opposite_sample",
        "contrast_ev_delta_pct": round(contrast_delta, 4),
        "downside_rate": round(downside_weight / sample_weight, 4) if sample_weight else 0.0,
        "drift_score": round(drift_score, 4),
        "positive_weight": positive,
        "negative_weight": negative,
        "score": round(score, 4),
    }


def build_hypotheses(rows: list[SourceRow]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    row_items, feature_diagnostics = _feature_items(rows)
    singleton_counts: Counter[str] = Counter()
    for row, items in zip(rows, row_items):
        for item in items:
            singleton_counts[item] += max(1, row.weight)
    level_items = [
        (item,)
        for item, count in singleton_counts.items()
        if count >= MIN_SAMPLE_WEIGHT
    ]
    evaluated: list[dict[str, Any]] = []
    candidates = level_items
    seen: set[tuple[str, ...]] = set()
    for size in range(1, MAX_ITEMSET_SIZE + 1):
        next_level: set[tuple[str, ...]] = set()
        for itemset in candidates:
            normalized = tuple(sorted(itemset))
            if normalized in seen:
                continue
            seen.add(normalized)
            result = _evaluate_itemset(normalized, rows, row_items)
            if not result:
                continue
            evaluated.append(result)
            if size < MAX_ITEMSET_SIZE:
                for item in singleton_counts:
                    if item not in normalized:
                        combo = tuple(sorted((*normalized, item)))
                        if len(combo) == size + 1:
                            next_level.add(combo)
        candidates = sorted(next_level)[:MAX_CANDIDATES]
        if len(evaluated) >= MAX_CANDIDATES:
            break
    evaluated.sort(key=lambda item: (item.get("score", 0), item.get("sample_weight", 0)), reverse=True)
    hypotheses: list[dict[str, Any]] = []
    runtime_observable = [item for item in evaluated if _has_runtime_observable_requirement(item["items"])]
    hypotheses_by_match_signature: dict[str, dict[str, Any]] = {}
    for item in runtime_observable:
        signature = _signature_for_items(tuple(item["items"]))
        all_requirements = _requirements_from_items(item["items"])
        observable_requirements = _requirements_from_items(
            item["items"],
            allowed_fields=ARMING_OBSERVABLE_REQUIREMENT_FIELDS,
        )
        if not observable_requirements:
            continue
        match_signature = _requirement_signature(observable_requirements)
        if match_signature in hypotheses_by_match_signature:
            existing = hypotheses_by_match_signature[match_signature]
            existing_dimensions = {
                _requirement_signature([dimension])
                for dimension in existing.get("observation_dimensions") or []
                if isinstance(dimension, dict)
            }
            for dimension in all_requirements:
                dimension_signature = _requirement_signature([dimension])
                if dimension_signature not in existing_dimensions:
                    existing.setdefault("observation_dimensions", []).append(dimension)
                    existing_dimensions.add(dimension_signature)
            continue
        if len(hypotheses) >= MAX_OUTPUT_HYPOTHESES:
            continue
        hypothesis = {
            "soft_hypothesis_id": f"ldm_hypothesis_{signature}",
            "feature_signature_hash": signature,
            "runtime_match_signature_hash": match_signature,
            "rank": len(hypotheses) + 1,
            "observable_requirements": observable_requirements,
            "observation_dimensions": all_requirements,
            "evidence_summary": {
                "sample_weight": item["sample_weight"],
                "source_quality_adjusted_ev_pct": item["source_quality_adjusted_ev_pct"],
                "repeated_date_count": item["repeated_date_count"],
                "downside_rate": item["downside_rate"],
            },
            "contrast_summary": {
                "group_counts": item["contrast_group_counts"],
                "contrast_coverage_status": item["contrast_coverage_status"],
                "contrast_ev_delta_pct": item["contrast_ev_delta_pct"],
            },
            "drift_summary": {"drift_score": item["drift_score"]},
            "observation_budget_hint": {
                "policy": "sim_observation_budget_hint_v1",
                "priority": (
                    "collect_contrary_sample"
                    if item["contrast_coverage_status"] != "pass"
                    else "increase_contrastive_sim_collection"
                    if item["contrast_ev_delta_pct"] > 0
                    else "collect_contrary_sample"
                ),
                "max_daily_share_pct": 15,
            },
            "live_runtime_effect": False,
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "forbidden_uses": FORBIDDEN_USES,
            "allowed_downstream_effects": ALLOWED_DOWNSTREAM_EFFECTS,
        }
        hypotheses.append(hypothesis)
        hypotheses_by_match_signature[match_signature] = hypothesis
    diagnostics = {
        "input_row_count": len(rows),
        "feature_count": len(feature_diagnostics),
        "candidate_count": len(evaluated),
        "feature_diagnostics": feature_diagnostics,
    }
    return hypotheses, diagnostics


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
        or str(item.get("field") or "").strip() not in ARMING_OBSERVABLE_REQUIREMENT_FIELDS
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
    if plan.get("hypothesis_count") is not None and _safe_int(plan.get("hypothesis_count"), -1) != len(hypotheses):
        return False
    return all(isinstance(item, dict) and _validate_hypothesis_contract(item) for item in hypotheses)


def build_observation_plan(report: dict[str, Any], apply_date: str) -> dict[str, Any]:
    hypotheses = [item for item in report.get("hypotheses") or [] if isinstance(item, dict) and _validate_hypothesis_contract(item)]
    return {
        "schema_version": OBSERVATION_PLAN_SCHEMA_VERSION,
        "source_report_type": REPORT_TYPE,
        "source_report_date": report.get("date"),
        "apply_date": apply_date,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "decision_authority": "sim_observation_planning",
        "runtime_effect": False,
        "live_runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "allowed_downstream_effects": ALLOWED_DOWNSTREAM_EFFECTS,
        "forbidden_uses": FORBIDDEN_USES,
        "hypotheses": hypotheses,
        "hypothesis_count": len(hypotheses),
    }


def _merge_catalog(path: Path, plan: dict[str, Any], *, domain: str) -> bool:
    payload = _load_json(path)
    expected_schema = f"{domain}_sim_policy_catalog_v1"
    if payload.get("schema_version") != expected_schema:
        return False
    if not _validate_observation_plan_contract(plan):
        return False
    payload["hypothesis_observation_plan"] = {
        **plan,
        "catalog_merge": {
            "merged_at": datetime.now().isoformat(timespec="seconds"),
            "catalog_path": str(path),
            "domain": domain,
            "catalog_applied_runtime_pending": domain == "swing",
        },
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return True


def merge_sim_policy_catalogs(source_date: str, plan: dict[str, Any]) -> dict[str, Any]:
    paths = {
        "scalp": SCALP_POLICY_DIR / f"scalp_sim_policy_catalog_{source_date}.json",
        "swing": SWING_POLICY_DIR / f"swing_sim_policy_catalog_{source_date}.json",
    }
    result: dict[str, Any] = {}
    for domain, path in paths.items():
        result[domain] = {
            "path": str(path),
            "merged": _merge_catalog(path, plan, domain=domain) if path.exists() else False,
        }
    return result


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# LDM Hypothesis Discovery - {report.get('date')}",
        "",
        "## Contract",
        "",
        "- decision_authority: `sim_observation_planning`",
        "- runtime_effect: `false`",
        "- allowed_runtime_apply: `false`",
        "- broker_order_forbidden: `true`",
        "- core statement: LDM does not create buy/sell/hold live rules; it allocates sim observation budget and contrastive sample collection.",
        "",
        "## Summary",
        "",
    ]
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    for key in ("source_start", "source_end", "input_row_count", "hypothesis_count", "candidate_count"):
        lines.append(f"- {key}: `{summary.get(key)}`")
    lines.extend(["", "## Top Hypotheses", ""])
    for item in (report.get("hypotheses") or [])[:10]:
        evidence = item.get("evidence_summary") if isinstance(item.get("evidence_summary"), dict) else {}
        contrast = item.get("contrast_summary") if isinstance(item.get("contrast_summary"), dict) else {}
        lines.append(
            f"- `{item.get('soft_hypothesis_id')}` sample=`{evidence.get('sample_weight')}` "
            f"ev=`{evidence.get('source_quality_adjusted_ev_pct')}` "
            f"contrast_delta=`{contrast.get('contrast_ev_delta_pct')}`"
        )
    lines.extend(["", "## Forbidden Uses", ""])
    for use in FORBIDDEN_USES:
        lines.append(f"- `{use}`")
    return "\n".join(lines) + "\n"


def build_report(target_date: str, source_start: str, apply_date: str) -> dict[str, Any]:
    rows, source_diagnostics = load_source_rows(source_start, target_date)
    hypotheses, diagnostics = build_hypotheses(rows)
    report = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "date": target_date,
        "apply_date": apply_date,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "report_type": REPORT_TYPE,
        "decision_authority": "sim_observation_planning",
        "metric_role": "primary_ev",
        "window_policy": "historical_source_window_to_apply_date_sim_observation",
        "primary_decision_metric": "source_quality_adjusted_ev_pct",
        "source_quality_gate": "contrast_group_preserved",
        "runtime_effect": False,
        "live_runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "allowed_downstream_effects": ALLOWED_DOWNSTREAM_EFFECTS,
        "forbidden_uses": FORBIDDEN_USES,
        "core_contract": (
            "LDM does not create buy/sell/hold live rules. It finds deterministic data-driven soft hypotheses "
            "for next-day sim observation budget allocation and contrastive sample collection."
        ),
        "ai_review": {
            "role": "review_only_not_candidate_generation",
            "status": "not_requested_non_blocking",
            "can_create_seed_promote_or_remove_candidates": False,
            "can_change_sim_budget_allocation": False,
        },
        "summary": {
            "source_start": source_start,
            "source_end": target_date,
            "apply_date": apply_date,
            "input_row_count": diagnostics["input_row_count"],
            "feature_count": diagnostics["feature_count"],
            "candidate_count": diagnostics["candidate_count"],
            "hypothesis_count": len(hypotheses),
        },
        "source_diagnostics": source_diagnostics,
        "feature_diagnostics": diagnostics["feature_diagnostics"],
        "hypotheses": hypotheses,
    }
    return report


def write_report(report: dict[str, Any], *, merge_catalog: bool) -> dict[str, str]:
    target_date = str(report.get("date") or "")
    apply_date = str(report.get("apply_date") or "")
    REPORT_OUT_DIR.mkdir(parents=True, exist_ok=True)
    PLAN_DIR.mkdir(parents=True, exist_ok=True)
    json_path, md_path = report_paths(target_date)
    plan_path = observation_plan_path(apply_date)
    plan = build_observation_plan(report, apply_date)
    if merge_catalog:
        report["catalog_merge"] = merge_sim_policy_catalogs(target_date, plan)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return {"json": str(json_path), "markdown": str(md_path), "plan": str(plan_path)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build LDM hypothesis discovery sim observation plan.")
    parser.add_argument("--date", dest="target_date", default=date.today().isoformat())
    parser.add_argument("--source-start", dest="source_start", required=True)
    parser.add_argument("--apply-date", dest="apply_date", required=True)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--merge-sim-policy-catalog", action="store_true")
    args = parser.parse_args(argv)
    report = build_report(args.target_date, args.source_start, args.apply_date)
    if args.write:
        paths = write_report(report, merge_catalog=bool(args.merge_sim_policy_catalog))
        print(json.dumps(paths, ensure_ascii=True))
    else:
        print(json.dumps(report.get("summary") or {}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
