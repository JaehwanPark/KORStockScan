"""Swing-only lifecycle decision matrix for probe and discovery simulation."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable

from src.engine.swing_strategy_discovery_ev_report import _load_rows as _load_discovery_rows
from src.engine.swing_strategy_discovery_ev_report import report_paths as discovery_ev_paths
from src.utils.constants import DATA_DIR, POSTGRES_URL
from src.utils.jsonl_io import iter_jsonl


REPORT_DIR = Path(DATA_DIR) / "report" / "swing_lifecycle_decision_matrix"
PIPELINE_EVENTS_DIR = Path(DATA_DIR) / "pipeline_events"
SWING_LIFECYCLE_AUDIT_DIR = Path(DATA_DIR) / "report" / "swing_lifecycle_audit"
REPORT_TYPE = "swing_lifecycle_decision_matrix"
MATRIX_VERSION = "swing_lifecycle_decision_matrix_v1"
DECISION_AUTHORITY = "swing_ldm_source_only"
SAMPLE_FLOOR = 3
MAX_ROWS_IN_REPORT = 500
SWING_LIFECYCLE_FLOW_REQUIRED_STAGES = ("entry", "holding", "exit")
FORBIDDEN_USES = [
    "real_order_submit",
    "one_share_real_canary",
    "scale_in_real_canary",
    "provider_route_change",
    "bot_restart",
    "runtime_threshold_mutation",
]

PROBE_BOOK = "swing_intraday_live_equiv_probe"
DISCOVERY_BOOK = "swing_strategy_discovery_sim"
ALLOWED_SOURCE_BOOKS = {PROBE_BOOK, DISCOVERY_BOOK}

PROBE_STAGE_BY_EVENT = {
    "swing_probe_entry_candidate": "entry",
    "swing_probe_holding_started": "holding",
    "swing_probe_exit_signal": "exit",
    "swing_probe_sell_order_assumed_filled": "exit",
    "swing_probe_scale_in_order_assumed_filled": "scale_in",
    "swing_sim_buy_order_assumed_filled": "entry",
    "swing_sim_holding_started": "holding",
    "swing_sim_sell_order_assumed_filled": "exit",
    "swing_sim_scale_in_order_assumed_filled": "scale_in",
}
SOURCE_ONLY_ENTRY_STAGE_BY_EVENT = {
    "blocked_swing_score_vpw": "entry",
    "blocked_swing_gap": "entry",
    "blocked_gatekeeper_reject": "entry",
    "market_regime_prior_observed": "entry",
    "swing_entry_policy_evaluated": "entry",
    "swing_entry_micro_context_observed": "entry",
    "latency_block": "entry",
}
SWING_MARKER_TOKEN_RE = re.compile(r"(^|[^a-z0-9])swing([^a-z0-9]|$)")

PRIMARY_METRICS = [
    "equal_weight_avg_profit_pct",
    "notional_weighted_ev_pct",
    "source_quality_adjusted_ev_pct",
]

SOURCE_DIMENSION_FIELD_MAP = {
    "holding_exit_bucket_attribution": {
        "mfe_bucket": "label_fields.mfe_pct",
        "mae_bucket": "label_fields.mae_pct",
        "held_bucket": "label_fields.held_sec",
        "exit_rule": "label_fields.exit_reason",
        "market_regime": "runtime_features.panic_context|runtime_features.market_regime",
        "selection_arm": "runtime_features.entry_policy",
        "sizing_arm": "runtime_features.sizing_policy",
        "exit_arm": "runtime_features.exit_policy",
        "sector": "runtime_features.sector",
        "theme": "runtime_features.theme_tags",
    },
    "discovery_arm_attribution": {
        "selection_arm": "runtime_features.entry_policy",
        "sizing_arm": "runtime_features.sizing_policy",
        "exit_arm": "runtime_features.exit_policy",
        "sector": "runtime_features.sector",
        "theme": "runtime_features.theme_tags",
    },
}


def _date_text(value: str | date | datetime | None) -> str:
    if value is None:
        return date.today().isoformat()
    return str(value)[:10]


def _safe_float(value: Any, default: float | None = None) -> float | None:
    try:
        if value is None or value == "":
            return default
        numeric = float(value)
        return numeric if math.isfinite(numeric) else default
    except Exception:
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value or 0))
    except Exception:
        return default


def _as_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _nested_present(row: dict[str, Any], path: str) -> bool:
    current: Any = row
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return False
        current = current.get(part)
    return current not in (None, "", [], {})


def _field_coverage(rows: list[dict[str, Any]], paths: str) -> dict[str, Any]:
    options = [part.strip() for part in str(paths or "").split("|") if part.strip()]
    present = 0
    for row in rows:
        if any(_nested_present(row, option) for option in options):
            present += 1
    total = len(rows)
    return {
        "paths": options,
        "present_count": present,
        "total_count": total,
        "coverage_ratio": round(present / total, 6) if total else 0.0,
    }


def _source_field_coverage(bucket_type: str, rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        dimension: _field_coverage(rows, paths)
        for dimension, paths in SOURCE_DIMENSION_FIELD_MAP.get(bucket_type, {}).items()
    }


def _unknown_reason_counts(bucket_key: str, coverage: dict[str, dict[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    parts = [part.strip().lower() for part in str(bucket_key or "").split("|")]
    for part in parts:
        if part in {"", "-", "missing", "held_missing", "unknown", "source_unknown"} or "missing" in part:
            counts[f"bucket_value_{part or 'blank'}"] += 1
    for dimension, info in coverage.items():
        if int(info.get("present_count") or 0) <= 0:
            counts[f"source_field_missing:{dimension}"] += 1
    return dict(counts)


def _first(record: dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        value = record.get(key)
        if value not in (None, ""):
            return value
    return default


def _slug(value: Any) -> str:
    text = re.sub(r"[^a-zA-Z0-9가-힣]+", "_", str(value or "").strip().lower()).strip("_")
    return text[:80] or "unknown"


def _slug_digest(value: Any, *, max_len: int = 80) -> str:
    text = re.sub(r"[^a-zA-Z0-9가-힣]+", "_", str(value or "").strip().lower()).strip("_")
    if not text:
        return "unknown"
    if len(text) <= max_len:
        return text
    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:10]
    return f"{text[: max_len - 11].rstrip('_')}_{digest}"


def _bucket_numeric(value: Any, cuts: list[float], labels: list[str], *, missing: str = "missing") -> str:
    numeric = _safe_float(value)
    if numeric is None:
        return missing
    for cut, label in zip(cuts, labels, strict=False):
        if numeric < cut:
            return label
    return labels[-1] if labels else str(numeric)


def _held_bucket(seconds: Any) -> str:
    numeric = _safe_float(seconds)
    if numeric is None:
        return "held_missing"
    if numeric < 30 * 60:
        return "lt_30m"
    if numeric < 2 * 60 * 60:
        return "30m_2h"
    if numeric < 24 * 60 * 60:
        return "2h_1d"
    return "ge_1d"


def report_paths(target_date: str) -> tuple[Path, Path]:
    base = REPORT_DIR / f"swing_lifecycle_decision_matrix_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def _pipeline_event_path(target_date: str) -> Path:
    return PIPELINE_EVENTS_DIR / f"pipeline_events_{target_date}.jsonl"


def _swing_lifecycle_audit_path(target_date: str) -> Path:
    return SWING_LIFECYCLE_AUDIT_DIR / f"swing_lifecycle_audit_{target_date}.json"


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _event_view(record: dict[str, Any]) -> dict[str, Any]:
    fields = record.get("fields") if isinstance(record.get("fields"), dict) else {}
    merged = dict(fields)
    for key, value in record.items():
        if key == "fields" or value in (None, ""):
            continue
        merged[key] = value
    if "event" not in merged and record.get("stage"):
        merged["event"] = record.get("stage")
    return merged


def _has_swing_token(value: Any) -> bool:
    return bool(SWING_MARKER_TOKEN_RE.search(str(value or "").lower()))


def _has_swing_marker(row: dict[str, Any]) -> bool:
    event = str(row.get("event") or row.get("stage") or "").lower()
    if _has_swing_token(event):
        return True
    marker_keys = (
        "simulation_book",
        "probe_book",
        "swing_intraday_probe",
        "probe_id",
        "probe_origin_stage",
        "entry_mode",
        "decision_authority",
        "source_book",
        "source_stage",
        "block_reason",
        "reason",
    )
    return any(_has_swing_token(row.get(key)) for key in marker_keys)


def _is_probe_event(record: dict[str, Any]) -> bool:
    row = _event_view(record)
    event = str(row.get("event") or row.get("stage") or "")
    if event not in PROBE_STAGE_BY_EVENT:
        if event not in SOURCE_ONLY_ENTRY_STAGE_BY_EVENT:
            return False
        return _has_swing_marker(row)
    if event.startswith("swing_sim_"):
        return _has_swing_marker(row)
    if str(row.get("simulation_book") or "") == PROBE_BOOK:
        return True
    return _as_bool(row.get("swing_intraday_probe")) or str(row.get("probe_book") or "") == PROBE_BOOK


def _is_swing_like_event(record: dict[str, Any]) -> bool:
    return _has_swing_marker(_event_view(record))


def _source_quality_status(row: dict[str, Any]) -> str:
    if row.get("source_quality_status"):
        return str(row.get("source_quality_status"))
    runtime_features = row.get("runtime_features") if isinstance(row.get("runtime_features"), dict) else {}
    blockers = [
        "origin",
        "block_reason",
        "position_tag",
        "strategy",
    ]
    if any(str(runtime_features.get(key) or "").strip() in {"", "-"} for key in blockers):
        return "instrumentation_gap"
    return "pass"


def _probe_row(record: dict[str, Any]) -> dict[str, Any]:
    record = _event_view(record)
    event = str(record.get("event") or record.get("stage") or "")
    stage = PROBE_STAGE_BY_EVENT.get(event) or SOURCE_ONLY_ENTRY_STAGE_BY_EVENT.get(event, "carry")
    score = _first(record, "score", "ai_score", "runtime_score_proxy", "model_score")
    vpw = _first(record, "v_pw", "vpw", "vpw_score")
    gap_pct = _first(record, "gap_pct", "gap_rate", "open_gap_pct")
    profit = _first(record, "profit_rate", "profit_pct", "final_return_pct", "realized_exit_return_pct")
    mfe = _first(record, "mfe_pct", "mfe")
    mae = _first(record, "mae_pct", "mae")
    virtual_notional = _first(record, "virtual_notional_krw", "notional_krw", "assumed_notional_krw")
    source_record_id = _first(record, "source_record_id", "record_id")
    runtime_features = {
        "lifecycle_flow_bridge_key": str(_first(record, "lifecycle_flow_bridge_key", default="")),
        "lifecycle_join_bridge_key": str(_first(record, "lifecycle_join_bridge_key", default="")),
        "join_bridge_key": str(_first(record, "join_bridge_key", default="")),
        "source_record_id": str(source_record_id or ""),
        "swing_strategy_discovery_arm_id": str(_first(record, "swing_strategy_discovery_arm_id", "arm_id", default="")),
        "origin": str(_first(record, "probe_origin_stage", "origin_stage", "origin", default="-")),
        "block_reason": str(_first(record, "block_reason", "gate_block_reason", "reason", default="-")),
        "strategy": str(_first(record, "strategy", "strategy_name", "probe_arm", default="-")),
        "position_tag": str(_first(record, "position_tag", "position_type", "tag", default="-")),
        "gap_pct": _safe_float(gap_pct),
        "gap_bucket": _bucket_numeric(gap_pct, [-3.0, 0.0, 3.0, 7.0], ["gap_down_large", "gap_down", "flat_up", "gap_up", "gap_up_large"]),
        "score": _safe_float(score),
        "score_bucket": _bucket_numeric(score, [55, 65, 75, 85], ["lt55", "55_64", "65_74", "75_84", "ge85"]),
        "vpw": _safe_float(vpw),
        "vpw_bucket": _bucket_numeric(vpw, [0.0, 0.5, 1.0, 2.0], ["vpw_neg", "vpw_low", "vpw_mid", "vpw_high", "vpw_extreme"]),
        "qty": _safe_int(_first(record, "qty", "quantity", default=0)),
        "virtual_notional_krw": _safe_float(virtual_notional),
        "qty_source": str(_first(record, "qty_source", "qty_reason", "budget_authority", default="-")),
        "entry_price_provenance": str(_first(record, "entry_price_provenance", "price_source", "assumed_fill_source", default="-")),
        "sizing_policy": str(_first(record, "sizing_policy", "position_sizing_policy", "qty_policy", default="-")),
        "exit_policy": str(_first(record, "exit_policy", "policy_exit_rule", "sell_policy", default="-")),
        "ofi_state": str(_first(record, "ofi_state", "ofi_bucket", "ofi", default="-")),
        "qi_state": str(_first(record, "qi_state", "qi_bucket", "qi", default="-")),
        "panic_context": str(_first(record, "panic_context", "panic_regime_mode", "panic_buy_regime_mode", default="-")),
        "add_type": str(_first(record, "add_type", "last_add_type", "scale_in_type", default="-")),
        "price_policy": str(_first(record, "price_policy", "entry_price_policy", "scale_in_price_policy", default="-")),
    }
    labels = {
        "realized_probe_profit_pct": _safe_float(profit),
        "final_return_pct": _safe_float(_first(record, "final_return_pct", default=profit)),
        "mfe_pct": _safe_float(mfe),
        "mae_pct": _safe_float(mae),
        "exit_reason": str(_first(record, "exit_reason", "exit_rule", "sell_reason", default="-")),
        "policy_exit_return_pct": _safe_float(_first(record, "policy_exit_return_pct", "exit_only_return_pct")),
        "held_sec": _safe_float(_first(record, "held_sec", "holding_sec", "elapsed_sec")),
    }
    return {
        "domain": "swing",
        "source_book": PROBE_BOOK,
        "source_stage": event,
        "lifecycle_stage": stage,
        "stock_code": str(_first(record, "stock_code", "code", "symbol", default="-")),
        "event_time": str(_first(record, "ts", "timestamp", "created_at", default="")),
        "row_id": str(_first(record, "probe_id", "record_id", "position_id", "stock_code", default=f"probe_{event}")),
        "runtime_features": runtime_features,
        "label_fields": labels,
        "source_quality_status": _source_quality_status({"runtime_features": runtime_features}),
        "actual_order_submitted": _as_bool(record.get("actual_order_submitted"), False),
        "broker_order_forbidden": _as_bool(record.get("broker_order_forbidden"), True),
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }


def _load_probe_rows(target_date: str) -> list[dict[str, Any]]:
    rows, _ = _load_probe_rows_with_diagnostics(target_date)
    return rows


def _load_probe_rows_with_diagnostics(target_date: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    path = _pipeline_event_path(target_date)
    rows: list[dict[str, Any]] = []
    raw_swing_event_count = 0
    unmapped_stage_counts: Counter[str] = Counter()
    for record in iter_jsonl(path):
        swing_like = _is_swing_like_event(record)
        mapped = _is_probe_event(record)
        if swing_like:
            raw_swing_event_count += 1
        if mapped:
            rows.append(_probe_row(record))
        elif swing_like:
            view = _event_view(record)
            unmapped_stage_counts[str(view.get("event") or view.get("stage") or "-")] += 1
    diagnostics = {
        "raw_swing_event_count": raw_swing_event_count,
        "ldm_consumed_event_count": len(rows),
        "ldm_event_coverage_rate": round(len(rows) / raw_swing_event_count, 6) if raw_swing_event_count else 0.0,
        "unmapped_swing_stage_counts": dict(unmapped_stage_counts.most_common(20)),
    }
    return rows, diagnostics


def _discovery_row(row: dict[str, Any], *, lifecycle_stage: str | None = None) -> dict[str, Any]:
    status = str(row.get("label_status") or "")
    stage = lifecycle_stage or ("exit" if status == "labeled" else "carry")
    features = {
        "lifecycle_flow_bridge_key": str(row.get("lifecycle_flow_bridge_key") or ""),
        "lifecycle_join_bridge_key": str(row.get("lifecycle_join_bridge_key") or ""),
        "join_bridge_key": str(row.get("join_bridge_key") or ""),
        "swing_strategy_discovery_arm_id": str(row.get("arm_row_id") or row.get("arm_id") or ""),
        "origin": "swing_strategy_discovery_sim_v1",
        "block_reason": str(row.get("block_reason") or "-"),
        "strategy": str(row.get("entry_policy") or row.get("arm_id") or "-"),
        "position_tag": str(row.get("position_tag") or "-"),
        "gap_pct": None,
        "gap_bucket": "discovery_gap_unobserved",
        "score": None,
        "score_bucket": "discovery_score_unobserved",
        "vpw": None,
        "vpw_bucket": "discovery_vpw_unobserved",
        "qty": None,
        "virtual_notional_krw": _safe_float(row.get("virtual_notional_krw")),
        "qty_source": str(row.get("sizing_policy") or "-"),
        "entry_price_provenance": str(row.get("entry_reason") or "-"),
        "ofi_state": "-",
        "qi_state": "-",
        "panic_context": "-",
        "add_type": "-",
        "price_policy": str(row.get("entry_policy") or "-"),
        "arm_id": str(row.get("arm_id") or "-"),
        "entry_policy": str(row.get("entry_policy") or "-"),
        "sizing_policy": str(row.get("sizing_policy") or "-"),
        "exit_policy": str(row.get("exit_policy") or "-"),
        "selection_arm": str(row.get("selection_arm") or "-"),
        "sector": str(row.get("sector") or "-"),
        "theme_tags": str(row.get("theme_tags") or "-"),
        "legacy_ml_cohort": str(row.get("legacy_pick_type") or "-"),
    }
    exit_labels = stage == "exit"
    labels = {
        "realized_probe_profit_pct": _safe_float(row.get("realized_exit_return_pct")) if exit_labels else None,
        "final_return_pct": _safe_float(row.get("final_return_pct")) if exit_labels else None,
        "mfe_pct": _safe_float(row.get("mfe_pct")) if exit_labels else None,
        "mae_pct": _safe_float(row.get("mae_pct")) if exit_labels else None,
        "exit_reason": str(row.get("policy_exit_reason") or "-") if exit_labels else "-",
        "policy_exit_return_pct": _safe_float(row.get("final_return_pct")) if exit_labels else None,
        "held_sec": None,
        "label_status": status,
        "label_maturity_status": row.get("label_maturity_status"),
        "future_quote_count": row.get("future_quote_count"),
    }
    source_stage_by_lifecycle = {
        "entry": "strategy_discovery_entry_policy",
        "holding": "strategy_discovery_holding_policy",
        "exit": "policy_exit_label",
        "carry": "policy_exit_pending_carry",
    }
    return {
        "domain": "swing",
        "source_book": DISCOVERY_BOOK,
        "source_stage": source_stage_by_lifecycle.get(stage, "strategy_discovery_policy"),
        "lifecycle_stage": stage,
        "stock_code": str(row.get("stock_code") or "-"),
        "event_time": str(row.get("source_date") or ""),
        "row_id": f"discovery_{row.get('arm_row_id') or row.get('arm_id') or row.get('candidate_id')}",
        "runtime_features": features,
        "label_fields": labels,
        "source_quality_status": str(row.get("source_quality_status") or "pass"),
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }


def _discovery_lifecycle_rows(row: dict[str, Any]) -> list[dict[str, Any]]:
    status = str(row.get("label_status") or "")
    if status == "labeled":
        # A discovery arm is a synthetic source-only strategy path: entry policy,
        # sizing/holding policy, and policy-exit label share one arm identity.
        return [
            _discovery_row(row, lifecycle_stage="entry"),
            _discovery_row(row, lifecycle_stage="holding"),
            _discovery_row(row, lifecycle_stage="exit"),
        ]
    return [_discovery_row(row, lifecycle_stage="carry")]


def _load_discovery_lifecycle_rows(
    target_date: str,
    *,
    db_url: str,
    lookback_days: int,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    rows, arm_status_counts = _load_discovery_rows(target_date, db_url=db_url, lookback_days=lookback_days)
    lifecycle_rows: list[dict[str, Any]] = []
    for row in rows:
        lifecycle_rows.extend(_discovery_lifecycle_rows(row))
    return lifecycle_rows, arm_status_counts


def _valid_label(row: dict[str, Any]) -> float | None:
    labels = row.get("label_fields") if isinstance(row.get("label_fields"), dict) else {}
    for key in ("final_return_pct", "realized_probe_profit_pct", "policy_exit_return_pct"):
        value = _safe_float(labels.get(key))
        if value is not None:
            return value
    return None


def _metric_contract(bucket_type: str, stage: str, *, sample_floor: int = SAMPLE_FLOOR) -> dict[str, Any]:
    return {
        "metric_role": "swing_sim_source_bucket_attribution",
        "decision_authority": DECISION_AUTHORITY,
        "runtime_effect": False,
        "window_policy": "postclose_rolling_source_only",
        "sample_floor": sample_floor,
        "primary_decision_metric": "source_quality_adjusted_ev_pct",
        "bucket_type": bucket_type,
        "lifecycle_stage": stage,
        "forbidden_uses": FORBIDDEN_USES,
        "source_quality_gate": "pass_or_keep_collecting",
    }


def _bucket_summary(bucket_type: str, bucket_key: str, rows: list[dict[str, Any]], stage: str) -> dict[str, Any]:
    returns: list[float] = []
    source_quality_counts: dict[str, int] = defaultdict(int)
    mfe_values: list[float] = []
    mae_values: list[float] = []
    notional_return_pairs: list[tuple[float, float]] = []
    for row in rows:
        source_quality_counts[_source_quality_status(row)] += 1
        labels = row.get("label_fields") if isinstance(row.get("label_fields"), dict) else {}
        label = _valid_label(row)
        if label is not None:
            returns.append(float(label))
        mfe = _safe_float(labels.get("mfe_pct"))
        mae = _safe_float(labels.get("mae_pct"))
        if mfe is not None:
            mfe_values.append(mfe)
        if mae is not None:
            mae_values.append(mae)
        features = row.get("runtime_features") if isinstance(row.get("runtime_features"), dict) else {}
        notional = max(0.0, _safe_float(features.get("virtual_notional_krw"), 0.0) or 0.0)
        if label is not None and notional > 0:
            notional_return_pairs.append((float(label), notional))
    joined = len(returns)
    avg = sum(returns) / joined if joined else 0.0
    notional_sum = sum(notional for _, notional in notional_return_pairs)
    weighted = (
        sum(value * notional for value, notional in notional_return_pairs) / notional_sum
        if notional_sum > 0
        else avg
    )
    coverage = min(1.0, joined / SAMPLE_FLOOR) if SAMPLE_FLOOR else 1.0
    blocker = any(status not in {"pass", "-", "ok"} for status in source_quality_counts)
    source_gate = "hold_sample" if joined < SAMPLE_FLOOR else "source_quality_blocker" if blocker else "pass"
    adjusted = weighted * coverage * (0.5 if blocker else 1.0)
    if source_gate == "source_quality_blocker":
        route = "code_patch_required"
    elif joined < SAMPLE_FLOOR:
        route = "source_only_keep_collecting"
    else:
        route = "sim_auto_approved"
    field_coverage = _source_field_coverage(bucket_type, rows)
    unknown_counts = _unknown_reason_counts(bucket_key, field_coverage)
    missing_dimensions = [
        dimension
        for dimension, info in field_coverage.items()
        if isinstance(info, dict) and int(info.get("present_count") or 0) <= 0
    ]
    implementation_status = (
        "implemented_source_quality_contract_waiting_sample"
        if field_coverage and (source_gate == "source_quality_blocker" or missing_dimensions)
        else None
    )
    implementation_provenance = {
        "implementation_type": "swing_ldm_source_field_coverage_contract",
        "source_report_type": REPORT_TYPE,
        "source_field_coverage": field_coverage,
        "unknown_reason_counts": unknown_counts,
        "missing_dimensions": missing_dimensions,
        "sample_status": "waiting_source_field_sample" if missing_dimensions else "source_fields_available",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    } if implementation_status else {}
    return {
        "bucket_type": bucket_type,
        "bucket_key": bucket_key,
        "lifecycle_stage": stage,
        "sample_count": len(rows),
        "joined_sample": joined,
        "source_quality_gate": source_gate,
        "source_quality_counts": dict(source_quality_counts),
        "source_field_coverage": field_coverage,
        "unknown_reason_counts": unknown_counts,
        "equal_weight_avg_profit_pct": round(avg, 6),
        "notional_weighted_ev_pct": round(weighted, 6),
        "source_quality_adjusted_ev_pct": round(adjusted, 6),
        "diagnostic_win_rate": round(sum(1 for value in returns if value > 0) / joined, 6) if joined else 0.0,
        "mfe_avg_pct": round(sum(mfe_values) / len(mfe_values), 6) if mfe_values else None,
        "mae_avg_pct": round(sum(mae_values) / len(mae_values), 6) if mae_values else None,
        "recommended_route": route,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "runtime_effect": False,
        "implementation_status": implementation_status,
        "implementation_provenance": implementation_provenance,
    }


def _stable_swing_flow_bucket_id(bucket_key: str) -> str:
    digest = hashlib.sha1(str(bucket_key or "").encode("utf-8")).hexdigest()[:10]
    return f"swing_lifecycle_flow:combo_swing_lifecycle_flow:{_slug_digest(bucket_key, max_len=56)}:{digest}"


def _row_flow_identity(row: dict[str, Any]) -> tuple[str, str]:
    features = row.get("runtime_features") if isinstance(row.get("runtime_features"), dict) else {}
    for key, quality in (
        ("lifecycle_flow_bridge_key", "lifecycle_flow_bridge_key"),
        ("lifecycle_join_bridge_key", "lifecycle_join_bridge_key"),
        ("join_bridge_key", "join_bridge_key"),
    ):
        value = str(features.get(key) or row.get(key) or "").strip()
        if value and value != "-":
            return f"{key}:{value}", quality
    source_record_id = str(features.get("source_record_id") or row.get("source_record_id") or "").strip()
    if source_record_id and source_record_id != "-":
        code = str(row.get("stock_code") or "").strip()
        return f"source_record_id:{code}:{source_record_id}", "source_record_id"
    arm_id = str(features.get("swing_strategy_discovery_arm_id") or row.get("swing_strategy_discovery_arm_id") or "").strip()
    if arm_id and arm_id != "-":
        code = str(row.get("stock_code") or "").strip()
        return f"swing_strategy_discovery_arm_id:{code}:{arm_id}", "swing_strategy_discovery_arm_id"
    candidate_id = str(row.get("candidate_id") or row.get("row_id") or "").strip()
    if candidate_id and candidate_id != "-":
        return f"candidate_id:{candidate_id}", "candidate_id"
    code = str(row.get("stock_code") or "").strip()
    event_time = str(row.get("event_time") or "").strip()
    return f"fallback:{code}:{event_time}", "fallback_incomplete"


def _flow_stage(row: dict[str, Any]) -> str:
    stage = str(row.get("lifecycle_stage") or "")
    return "holding" if stage == "carry" else stage


def _entry_bucket_key(row: dict[str, Any]) -> str:
    f = row.get("runtime_features") if isinstance(row.get("runtime_features"), dict) else {}
    return "|".join(
        [
            str(f.get("origin") or "-"),
            str(f.get("block_reason") or "-"),
            str(f.get("position_tag") or "-"),
            str(f.get("gap_bucket") or "-"),
            str(f.get("score_bucket") or "-"),
            str(f.get("vpw_bucket") or "-"),
            str(f.get("strategy") or "-"),
            str(f.get("entry_price_provenance") or "-"),
            str(f.get("qty_source") or "-"),
        ]
    )


def _holding_exit_bucket_key(row: dict[str, Any]) -> str:
    f = row.get("runtime_features") if isinstance(row.get("runtime_features"), dict) else {}
    labels = row.get("label_fields") if isinstance(row.get("label_fields"), dict) else {}
    return "|".join(
        [
            _bucket_numeric(labels.get("mfe_pct"), [-3, 0, 3, 7], ["mfe_deep_neg", "mfe_neg", "mfe_low", "mfe_mid", "mfe_high"]),
            _bucket_numeric(labels.get("mae_pct"), [-7, -3, 0, 3], ["mae_deep", "mae_mid", "mae_low", "mae_flat", "mae_green"]),
            _held_bucket(labels.get("held_sec")),
            str(labels.get("exit_reason") or "-"),
            str(f.get("sizing_policy") or "-"),
            str(f.get("exit_policy") or "-"),
            str(f.get("panic_context") or "-"),
            str(f.get("ofi_state") or "-"),
            str(f.get("qi_state") or "-"),
        ]
    )


def _scale_in_bucket_key(row: dict[str, Any]) -> str:
    f = row.get("runtime_features") if isinstance(row.get("runtime_features"), dict) else {}
    return "|".join(
        [
            str(f.get("add_type") or "-"),
            _source_quality_status(row),
            str(f.get("qty_source") or "-"),
            str(f.get("price_policy") or "-"),
        ]
    )


def _child_bucket_id(stage: str, bucket_type: str, bucket_key: str) -> str:
    return f"swing_{stage}:{bucket_type}:{_slug_digest(bucket_key)}"


def _first_flow_stage_row(by_stage: dict[str, list[dict[str, Any]]], stage: str) -> dict[str, Any] | None:
    rows = by_stage.get(stage) or []
    if not rows:
        return None
    return sorted(rows, key=lambda item: str(item.get("event_time") or ""))[0]


def _flow_ev(by_stage: dict[str, list[dict[str, Any]]]) -> float | None:
    exit_row = _first_flow_stage_row(by_stage, "exit")
    if exit_row is not None:
        value = _valid_label(exit_row)
        if value is not None:
            return round(float(value), 6)
    values = [
        float(value)
        for rows in by_stage.values()
        for row in rows
        for value in [_valid_label(row)]
        if value is not None
    ]
    return round(sum(values) / len(values), 6) if values else None


def _flow_incomplete_reasons(identity_quality: str, stage_presence: dict[str, bool]) -> list[str]:
    reasons: list[str] = []
    if identity_quality == "fallback_incomplete":
        reasons.append("fallback_identity_incomplete")
    for stage in SWING_LIFECYCLE_FLOW_REQUIRED_STAGES:
        if not stage_presence.get(stage):
            reasons.append(f"missing_{stage}")
    if stage_presence.get("exit") and not stage_presence.get("entry"):
        reasons.append("exit_without_entry")
    return list(dict.fromkeys(reasons))


def _swing_flow_record(attribution_key: str, identity_quality: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_stage: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        stage = _flow_stage(row)
        if stage in {"entry", "holding", "scale_in", "exit"}:
            by_stage[stage].append(row)
    entry_row = _first_flow_stage_row(by_stage, "entry")
    holding_row = _first_flow_stage_row(by_stage, "holding")
    exit_row = _first_flow_stage_row(by_stage, "exit")
    scale_in_rows = by_stage.get("scale_in") or []
    child_bucket_ids = {
        "entry": _child_bucket_id("entry", "entry_bucket_attribution", _entry_bucket_key(entry_row)) if entry_row else None,
        "holding": _child_bucket_id("holding", "holding_exit_bucket_attribution", _holding_exit_bucket_key(holding_row)) if holding_row else None,
        "scale_in": [
            _child_bucket_id("scale_in", "scale_in_bucket_attribution", _scale_in_bucket_key(row))
            for row in scale_in_rows
        ],
        "exit": _child_bucket_id("exit", "holding_exit_bucket_attribution", _holding_exit_bucket_key(exit_row)) if exit_row else None,
    }
    child_bucket_ids["scale_in"] = list(dict.fromkeys(child_bucket_ids["scale_in"]))
    stage_presence = {stage: bool(by_stage.get(stage)) for stage in SWING_LIFECYCLE_FLOW_REQUIRED_STAGES}
    complete = all(stage_presence.values())
    ev = _flow_ev(by_stage)
    if identity_quality == "fallback_incomplete":
        source_quality = "fallback_identity_incomplete"
    elif not complete:
        source_quality = "incomplete_lifecycle_flow"
    elif ev is None:
        source_quality = "outcome_join_missing"
    else:
        source_quality = "pass"
    scale_bucket = child_bucket_ids["scale_in"][0] if child_bucket_ids["scale_in"] else "scale_in:none"
    bucket_key = "|".join(
        [
            f"entry={child_bucket_ids['entry'] or 'entry:missing'}",
            f"holding={child_bucket_ids['holding'] or 'holding:missing'}",
            f"scale_in={scale_bucket}",
            f"exit={child_bucket_ids['exit'] or 'exit:missing'}",
        ]
    )
    return {
        "flow_instance_id": attribution_key,
        "identity_quality": identity_quality,
        "swing_lifecycle_flow_bucket_id": _stable_swing_flow_bucket_id(bucket_key),
        "bucket_type": "combo_swing_lifecycle_flow",
        "bucket_key": bucket_key,
        "attribution_key": attribution_key,
        "lifecycle_stage": "lifecycle_flow",
        "stage_presence": stage_presence,
        "stage_completion_state": "complete" if complete else "incomplete",
        "incomplete_reasons": _flow_incomplete_reasons(identity_quality, stage_presence),
        "entry_bucket_id": child_bucket_ids["entry"],
        "holding_bucket_id": child_bucket_ids["holding"],
        "scale_in_bucket_ids": child_bucket_ids["scale_in"],
        "exit_bucket_id": child_bucket_ids["exit"],
        "child_bucket_ids": child_bucket_ids,
        "stage_contract": {
            stage: {
                "stage": stage,
                "row_count": len(by_stage.get(stage) or []),
                "bucket_id": child_bucket_ids.get(stage),
                "contract_state": "present" if by_stage.get(stage) else "missing_policy",
            }
            for stage in SWING_LIFECYCLE_FLOW_REQUIRED_STAGES
        },
        "sample_count": 1,
        "joined_sample": 1 if ev is not None and complete else 0,
        "source_quality_gate": source_quality,
        "source_quality_adjusted_ev_pct": ev,
        "equal_weight_avg_profit_pct": ev,
        "notional_weighted_ev_pct": ev,
        "diagnostic_win_rate": 1.0 if ev is not None and ev > 0 else 0.0 if ev is not None else None,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "metric_scope": "swing_lifecycle_bundle_ev",
        "rollback_guard": "hard_safety_priority_plus_source_quality_and_post_apply_attribution",
        "decision_authority": "swing_ldm_lifecycle_flow_bucket_attribution_source_only",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "forbidden_uses": FORBIDDEN_USES,
    }


def _swing_lifecycle_flow_bucket_attribution(rows: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if _flow_stage(row) not in {"entry", "holding", "scale_in", "exit"}:
            continue
        identity, quality = _row_flow_identity(row)
        grouped[(identity, quality)].append(row)
    flows = [_swing_flow_record(identity, quality, subset) for (identity, quality), subset in grouped.items()]
    bucket_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for flow in flows:
        bucket_groups[str(flow.get("bucket_key") or "")].append(flow)
    buckets: list[dict[str, Any]] = []
    for bucket_key, subset in bucket_groups.items():
        joined = [item for item in subset if item.get("source_quality_adjusted_ev_pct") is not None]
        ev_values = [float(item["source_quality_adjusted_ev_pct"]) for item in joined]
        avg_ev = round(sum(ev_values) / len(ev_values), 6) if ev_values else None
        fallback_count = sum(1 for item in subset if item.get("identity_quality") == "fallback_incomplete")
        incomplete_count = sum(1 for item in subset if item.get("stage_completion_state") != "complete")
        if incomplete_count:
            source_quality = "join_contract_blocked"
        elif fallback_count:
            source_quality = "fallback_identity_incomplete"
        elif len(joined) < SAMPLE_FLOOR:
            source_quality = "hold_sample"
        else:
            source_quality = "pass"
        recommended_route = (
            "sim_auto_approved"
            if source_quality == "pass" and avg_ev is not None and avg_ev > 0
            else "source_only_keep_collecting"
        )
        first = subset[0]
        buckets.append(
            {
                "swing_lifecycle_flow_bucket_id": first.get("swing_lifecycle_flow_bucket_id"),
                "bucket_type": "combo_swing_lifecycle_flow",
                "bucket_key": bucket_key,
                "lifecycle_stage": "lifecycle_flow",
                "sample_count": len(subset),
                "joined_sample": len(joined),
                "join_rate": round(len(joined) / len(subset), 6) if subset else 0.0,
                "complete_flow_count": len(subset) - incomplete_count,
                "incomplete_flow_count": incomplete_count,
                "fallback_identity_count": fallback_count,
                "source_quality_gate": source_quality,
                "source_quality_adjusted_ev_pct": avg_ev,
                "equal_weight_avg_profit_pct": avg_ev,
                "notional_weighted_ev_pct": avg_ev,
                "diagnostic_win_rate": (
                    round(sum(1 for value in ev_values if value > 0) / len(ev_values), 6)
                    if ev_values
                    else None
                ),
                "recommended_route": recommended_route,
                "metric_scope": "swing_lifecycle_bundle_ev",
                "metric_role": "primary_ev",
                "primary_decision_metric": "source_quality_adjusted_ev_pct",
                "entry_bucket_id": first.get("entry_bucket_id"),
                "holding_bucket_id": first.get("holding_bucket_id"),
                "scale_in_bucket_ids": first.get("scale_in_bucket_ids") or [],
                "exit_bucket_id": first.get("exit_bucket_id"),
                "child_bucket_ids": first.get("child_bucket_ids") or {},
                "stage_contract": first.get("stage_contract") or {},
                "attribution_key": first.get("attribution_key"),
                "rollback_guard": first.get("rollback_guard"),
                "decision_authority": "swing_ldm_lifecycle_flow_bucket_attribution_source_only",
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "forbidden_uses": FORBIDDEN_USES,
            }
        )
    buckets.sort(
        key=lambda item: (
            item.get("recommended_route") != "sim_auto_approved",
            -int(item.get("joined_sample") or 0),
            str(item.get("bucket_key") or ""),
        )
    )
    sim_candidates = _sim_candidates("lifecycle_flow", buckets)
    incomplete_reasons: Counter[str] = Counter()
    for flow in flows:
        incomplete_reasons.update(flow.get("incomplete_reasons") or [])
    source_rows_by_stage = Counter(_flow_stage(row) for row in rows if _flow_stage(row) in {"entry", "holding", "scale_in", "exit"})
    complete_flow_count = sum(1 for item in flows if item.get("stage_completion_state") == "complete")
    identity_present = sum(1 for item in flows if item.get("identity_quality") != "fallback_incomplete")
    return {
        "metric_contract": {
            "metric_role": "primary_ev",
            "decision_authority": "swing_ldm_lifecycle_flow_bucket_attribution_source_only",
            "runtime_effect": False,
            "window_policy": "postclose_rolling_source_only",
            "sample_floor": SAMPLE_FLOOR,
            "primary_decision_metric": "source_quality_adjusted_ev_pct",
            "bucket_type": "combo_swing_lifecycle_flow",
            "lifecycle_stage": "lifecycle_flow",
            "forbidden_uses": FORBIDDEN_USES,
            "source_quality_gate": "entry+holding_or_carry+exit complete flow + stable identity + joined outcome",
        },
        "metric_role": "primary_ev",
        "metric_scope": "swing_lifecycle_bundle_ev",
        "decision_authority": "swing_ldm_lifecycle_flow_bucket_attribution_source_only",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "window_policy": "postclose_rolling_source_only",
        "sample_floor": SAMPLE_FLOOR,
        "primary_decision_metric": "source_quality_adjusted_ev_pct",
        "source_quality_gate": "entry+holding_or_carry+exit complete flow + stable identity + joined outcome",
        "forbidden_uses": FORBIDDEN_USES,
        "summary": {
            "source_row_count": sum(source_rows_by_stage.values()),
            "bucket_count": len(buckets),
            "flow_count": len(flows),
            "complete_flow_count": complete_flow_count,
            "incomplete_flow_count": len(flows) - complete_flow_count,
            "identity_join_rate": round(identity_present / len(flows), 6) if flows else 0.0,
            "complete_flow_rate": round(complete_flow_count / len(flows), 6) if flows else 0.0,
            "join_contract_blocked": bool(incomplete_reasons and complete_flow_count == 0),
            "incomplete_flow_reason_counts": dict(incomplete_reasons),
            "stage_source_counts": dict(source_rows_by_stage),
            "sim_auto_candidate_count": len(sim_candidates),
            "workorder_count": 0,
        },
        "flows": flows[:200],
        "buckets": buckets[:200],
        "sim_auto_approval_candidates": sim_candidates,
        "runtime_approval_candidates": sim_candidates,
        "code_improvement_workorders": [],
    }


def _group(rows: Iterable[dict[str, Any]], bucket_type: str, stage: str, key_fn) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(key_fn(row) or "-")].append(row)
    buckets = [_bucket_summary(bucket_type, key, items, stage) for key, items in grouped.items()]
    return sorted(
        buckets,
        key=lambda item: (
            item.get("recommended_route") != "sim_auto_approved",
            -abs(float(item.get("source_quality_adjusted_ev_pct") or 0.0)),
            -int(item.get("joined_sample") or 0),
        ),
    )


def _sim_candidates(stage: str, buckets: list[dict[str, Any]], *, limit: int = 25) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for item in buckets:
        if item.get("recommended_route") != "sim_auto_approved":
            continue
        bucket_id = f"swing_ldm_{stage}_{_slug(item.get('bucket_type'))}_{_slug_digest(item.get('bucket_key'))}"
        candidates.append(
            {
                "candidate_id": bucket_id,
                "bucket_id": bucket_id,
                "bucket_type": item.get("bucket_type"),
                "bucket_key": item.get("bucket_key"),
                "lifecycle_stage": stage,
                "classification_hint": "sim_auto_approved",
                "source_quality_adjusted_ev_pct": item.get("source_quality_adjusted_ev_pct"),
                "joined_sample": item.get("joined_sample"),
                "decision_authority": DECISION_AUTHORITY,
                "next_route": "next_preopen_swing_sim_policy_input",
                "allowed_runtime_apply": False,
                "runtime_effect": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "human_approval_required": False,
                "forbidden_uses": FORBIDDEN_USES,
            }
        )
    return candidates[:limit]


def _code_workorders(stage: str, buckets: list[dict[str, Any]], *, limit: int = 25) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in buckets:
        if item.get("recommended_route") not in {"code_patch_required"}:
            continue
        implementation_status = item.get("implementation_status")
        out.append(
            {
                "bucket_type": item.get("bucket_type"),
                "bucket_key": item.get("bucket_key"),
                "lifecycle_stage": stage,
                "workorder_id": f"swing_ldm_{stage}_{_slug(item.get('bucket_type'))}_{_slug(item.get('bucket_key'))}",
                "reason": "source_quality_or_instrumentation_gap",
                "target_subsystem": "swing_lifecycle_decision_matrix",
                "decision_authority": DECISION_AUTHORITY,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "forbidden_uses": FORBIDDEN_USES,
                "implementation_status": implementation_status,
                "implementation_provenance": item.get("implementation_provenance") or {},
            }
        )
    return out[:limit]


def _entry_attribution(rows: list[dict[str, Any]]) -> dict[str, Any]:
    stage_rows = [row for row in rows if row.get("lifecycle_stage") in {"selection", "entry", "holding", "carry"}]
    def key(row: dict[str, Any]) -> str:
        f = row.get("runtime_features") if isinstance(row.get("runtime_features"), dict) else {}
        return "|".join(
            [
                str(f.get("origin") or "-"),
                str(f.get("block_reason") or "-"),
                str(f.get("position_tag") or "-"),
                str(f.get("gap_bucket") or "-"),
                str(f.get("score_bucket") or "-"),
                str(f.get("vpw_bucket") or "-"),
                str(f.get("strategy") or "-"),
                str(f.get("entry_price_provenance") or "-"),
                str(f.get("qty_source") or "-"),
            ]
        )

    buckets = _group(stage_rows, "entry_bucket_attribution", "entry", key)
    return _attribution("entry_bucket_attribution", "entry", buckets, len(stage_rows))


def _holding_exit_attribution(rows: list[dict[str, Any]]) -> dict[str, Any]:
    stage_rows = [row for row in rows if row.get("lifecycle_stage") in {"holding", "exit", "carry"}]
    def key(row: dict[str, Any]) -> str:
        return _holding_exit_bucket_key(row)

    buckets = _group(stage_rows, "holding_exit_bucket_attribution", "holding_exit", key)
    return _attribution("holding_exit_bucket_attribution", "holding_exit", buckets, len(stage_rows))


def _scale_in_attribution(rows: list[dict[str, Any]]) -> dict[str, Any]:
    stage_rows = [row for row in rows if row.get("lifecycle_stage") == "scale_in"]
    def key(row: dict[str, Any]) -> str:
        f = row.get("runtime_features") if isinstance(row.get("runtime_features"), dict) else {}
        return "|".join(
            [
                str(f.get("add_type") or "-"),
                _source_quality_status(row),
                str(f.get("qty_source") or "-"),
                str(f.get("price_policy") or "-"),
            ]
        )

    buckets = _group(stage_rows, "scale_in_bucket_attribution", "scale_in", key)
    return _attribution("scale_in_bucket_attribution", "scale_in", buckets, len(stage_rows))


def _discovery_arm_attribution(rows: list[dict[str, Any]]) -> dict[str, Any]:
    stage_rows = [row for row in rows if row.get("source_book") == DISCOVERY_BOOK]
    def key(row: dict[str, Any]) -> str:
        f = row.get("runtime_features") if isinstance(row.get("runtime_features"), dict) else {}
        return "|".join(
            [
                str(f.get("entry_policy") or "-"),
                str(f.get("sizing_policy") or "-"),
                str(f.get("exit_policy") or "-"),
                str(f.get("sector") or "-"),
                str(f.get("theme_tags") or "-"),
                str(f.get("legacy_ml_cohort") or "-"),
            ]
        )

    buckets = _group(stage_rows, "discovery_arm_attribution", "selection", key)
    return _attribution("discovery_arm_attribution", "selection", buckets, len(stage_rows))


def _attribution(name: str, stage: str, buckets: list[dict[str, Any]], source_rows: int) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    workorders = _code_workorders(stage, buckets)
    return {
        "metric_contract": _metric_contract(name, stage),
        "summary": {
            "source_row_count": source_rows,
            "bucket_count": len(buckets),
            "sim_auto_candidate_count": len(candidates),
            "workorder_count": len(workorders),
        },
        "buckets": buckets[:200],
        "sim_auto_approval_candidates": candidates,
        "runtime_approval_candidates": candidates,
        "code_improvement_workorders": workorders,
    }


def _counts(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for row in rows:
        counts[str(row.get(key) or "-")] += 1
    return dict(counts)


def build_swing_lifecycle_decision_matrix(
    target_date: str,
    *,
    db_url: str = POSTGRES_URL,
    lookback_days: int = 90,
) -> dict[str, Any]:
    date_key = _date_text(target_date)
    probe_rows, probe_diagnostics = _load_probe_rows_with_diagnostics(date_key)
    discovery_rows, arm_status_counts = _load_discovery_lifecycle_rows(
        date_key,
        db_url=db_url,
        lookback_days=lookback_days,
    )
    audit_path = _swing_lifecycle_audit_path(date_key)
    audit_report = _load_json(audit_path)
    swing_entry_bottleneck = (
        audit_report.get("swing_entry_bottleneck")
        if isinstance(audit_report.get("swing_entry_bottleneck"), dict)
        else {}
    )
    swing_lifecycle_contract_gaps = (
        audit_report.get("swing_lifecycle_contract_gaps")
        if isinstance(audit_report.get("swing_lifecycle_contract_gaps"), dict)
        else {}
    )
    rows = [*probe_rows, *discovery_rows]
    if any(row.get("source_book") not in ALLOWED_SOURCE_BOOKS for row in rows):
        raise RuntimeError("Swing LDM consumed an unexpected source_book")

    entry = _entry_attribution(rows)
    holding_exit = _holding_exit_attribution(rows)
    scale_in = _scale_in_attribution(rows)
    discovery = _discovery_arm_attribution(rows)
    lifecycle_flow = _swing_lifecycle_flow_bucket_attribution(rows)
    attributions = [lifecycle_flow, entry, holding_exit, scale_in, discovery]
    sim_count = sum(len(item.get("sim_auto_approval_candidates") or []) for item in attributions)
    workorder_count = sum(len(item.get("code_improvement_workorders") or []) for item in attributions)
    labeled_rows = sum(1 for row in rows if _valid_label(row) is not None)
    warnings: list[str] = []
    if not probe_rows:
        warnings.append("swing_intraday_live_equiv_probe_missing")
    if not discovery_rows:
        warnings.append("swing_strategy_discovery_sim_missing")
    if labeled_rows < SAMPLE_FLOOR:
        warnings.append("sample_floor_not_met")
    pending = sum(
        1
        for row in discovery_rows
        if (row.get("label_fields") if isinstance(row.get("label_fields"), dict) else {}).get("label_status")
        == "pending_future_quotes"
    )
    if pending:
        warnings.append("pending_future_quotes")

    json_path, md_path = report_paths(date_key)
    discovery_json, _ = discovery_ev_paths(date_key)
    report = {
        "schema_version": 1,
        "report_type": REPORT_TYPE,
        "date": date_key,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "domain": "swing",
        "matrix_version": MATRIX_VERSION,
        "runtime_effect": False,
        "source_only": True,
        "decision_authority": DECISION_AUTHORITY,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "primary_metrics": PRIMARY_METRICS,
        "input_contract": {
            "allowed_source_books": sorted(ALLOWED_SOURCE_BOOKS),
            "swing_daily_simulation_consumed": False,
            "swing_lifecycle_audit_summary_consumed": bool(audit_report),
            "forbidden_sources": ["swing_daily_simulation"],
        },
        "summary": {
            "status": "pass" if rows else "missing",
            "total_rows": len(rows),
            "probe_rows": len(probe_rows),
            "discovery_rows": len(discovery_rows),
            "labeled_rows": labeled_rows,
            "pending_future_quote_count": pending,
            "raw_swing_event_count": probe_diagnostics.get("raw_swing_event_count", 0),
            "ldm_consumed_event_count": probe_diagnostics.get("ldm_consumed_event_count", 0),
            "ldm_event_coverage_rate": probe_diagnostics.get("ldm_event_coverage_rate", 0.0),
            "unmapped_swing_stage_counts": probe_diagnostics.get("unmapped_swing_stage_counts", {}),
            "stage_counts": _counts(rows, "lifecycle_stage"),
            "source_book_counts": _counts(rows, "source_book"),
            "sim_auto_candidate_count": sim_count,
            "workorder_count": workorder_count,
            "swing_lifecycle_flow_bucket_count": lifecycle_flow.get("summary", {}).get("bucket_count"),
            "complete_flow_count": lifecycle_flow.get("summary", {}).get("complete_flow_count"),
            "incomplete_flow_count": lifecycle_flow.get("summary", {}).get("incomplete_flow_count"),
            "identity_join_rate": lifecycle_flow.get("summary", {}).get("identity_join_rate"),
            "complete_flow_rate": lifecycle_flow.get("summary", {}).get("complete_flow_rate"),
            "join_contract_blocked": lifecycle_flow.get("summary", {}).get("join_contract_blocked"),
            "daily_simulation_consumed": False,
            "swing_entry_bottleneck_primary": swing_entry_bottleneck.get("primary"),
            "swing_lifecycle_contract_gap_count": swing_lifecycle_contract_gaps.get("gap_count"),
            "arm_status_counts": arm_status_counts,
        },
        "swing_entry_bottleneck": swing_entry_bottleneck,
        "swing_lifecycle_contract_gaps": swing_lifecycle_contract_gaps,
        "swing_lifecycle_flow_bucket_attribution": lifecycle_flow,
        "entry_bucket_attribution": entry,
        "holding_exit_bucket_attribution": holding_exit,
        "scale_in_bucket_attribution": scale_in,
        "discovery_arm_attribution": discovery,
        "lifecycle_rows": rows[:MAX_ROWS_IN_REPORT],
        "sources": {
            "pipeline_events": str(_pipeline_event_path(date_key)),
            "swing_strategy_discovery_ev": str(discovery_json) if discovery_json.exists() else None,
            "swing_lifecycle_audit": str(audit_path) if audit_path.exists() else None,
            "swing_daily_simulation": None,
        },
        "artifact_paths": {"json": str(json_path), "markdown": str(md_path)},
        "warnings": warnings,
    }
    return report


def render_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    lines = [
        f"# Swing Lifecycle Decision Matrix {report.get('date')}",
        "",
        "## Summary",
        f"- runtime_effect: `{report.get('runtime_effect')}`",
        f"- decision_authority: `{report.get('decision_authority')}`",
        f"- total_rows: `{summary.get('total_rows')}`",
        f"- probe_rows: `{summary.get('probe_rows')}`",
        f"- discovery_rows: `{summary.get('discovery_rows')}`",
        f"- raw_swing_event_count: `{summary.get('raw_swing_event_count')}`",
        f"- ldm_consumed_event_count: `{summary.get('ldm_consumed_event_count')}`",
        f"- ldm_event_coverage_rate: `{summary.get('ldm_event_coverage_rate')}`",
        f"- unmapped_swing_stage_counts: `{summary.get('unmapped_swing_stage_counts') or {}}`",
        f"- sim_auto_candidate_count: `{summary.get('sim_auto_candidate_count')}`",
        f"- workorder_count: `{summary.get('workorder_count')}`",
        f"- swing_lifecycle_flow_bucket_count: `{summary.get('swing_lifecycle_flow_bucket_count')}`",
        f"- complete_flow_count: `{summary.get('complete_flow_count')}`",
        f"- incomplete_flow_count: `{summary.get('incomplete_flow_count')}`",
        f"- identity_join_rate: `{summary.get('identity_join_rate')}`",
        f"- complete_flow_rate: `{summary.get('complete_flow_rate')}`",
        f"- join_contract_blocked: `{summary.get('join_contract_blocked')}`",
        f"- swing_entry_bottleneck_primary: `{summary.get('swing_entry_bottleneck_primary')}`",
        f"- swing_lifecycle_contract_gap_count: `{summary.get('swing_lifecycle_contract_gap_count')}`",
        f"- daily_simulation_consumed: `{summary.get('daily_simulation_consumed')}`",
        f"- warnings: `{report.get('warnings') or []}`",
        "",
        "## Bucket Attribution",
    ]
    for key in (
        "swing_lifecycle_flow_bucket_attribution",
        "entry_bucket_attribution",
        "holding_exit_bucket_attribution",
        "scale_in_bucket_attribution",
        "discovery_arm_attribution",
    ):
        item = report.get(key) if isinstance(report.get(key), dict) else {}
        item_summary = item.get("summary") if isinstance(item.get("summary"), dict) else {}
        lines.extend(
            [
                f"### {key}",
                f"- source_row_count: `{item_summary.get('source_row_count')}`",
                f"- bucket_count: `{item_summary.get('bucket_count')}`",
                f"- sim_auto_candidate_count: `{item_summary.get('sim_auto_candidate_count')}`",
                f"- workorder_count: `{item_summary.get('workorder_count')}`",
            ]
        )
        for bucket in (item.get("buckets") or [])[:5]:
            lines.append(
                f"- `{bucket.get('bucket_key')}` route=`{bucket.get('recommended_route')}` "
                f"joined=`{bucket.get('joined_sample')}` ev=`{bucket.get('source_quality_adjusted_ev_pct')}`"
            )
    lines.extend(["", "## Contract", "Swing LDM only consumes probe and strategy discovery simulation sources."])
    return "\n".join(lines).rstrip() + "\n"


def write_report(report: dict[str, Any]) -> tuple[Path, Path]:
    json_path, md_path = report_paths(str(report.get("date")))
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return json_path, md_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Swing lifecycle decision matrix.")
    parser.add_argument("--date", dest="target_date", default=date.today().isoformat())
    parser.add_argument("--db-url", default=POSTGRES_URL)
    parser.add_argument("--lookback-days", type=int, default=90)
    args = parser.parse_args()
    report = build_swing_lifecycle_decision_matrix(
        args.target_date,
        db_url=args.db_url,
        lookback_days=args.lookback_days,
    )
    json_path, md_path = write_report(report)
    print(f"[swing-lifecycle-decision-matrix] wrote {json_path} {md_path}")


if __name__ == "__main__":
    main()
