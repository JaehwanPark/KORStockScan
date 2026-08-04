"""Report-only intraday probe for scalping entry AI context quality."""

from __future__ import annotations

import argparse
import ast
import gzip
import hashlib
import inspect
import json
import os
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

from src.engine import scalp_entry_action_decision_matrix as adm_mod
from src.engine.scalping.ai_decision_trace import (
    CONTEXT_CANDIDATE_SCHEMA,
    record_ai_decision_trace,
)
from src.engine.scalping.holding_decision_context import (
    OBSERVATION_CONTRACT as HOLDING_CONTEXT_OBSERVATION_CONTRACT,
)
from src.engine.sniper_config import CONF
from src.utils.jsonl_io import existing_or_gzip_path, iter_jsonl

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data"
REPORT_DIR = DATA_DIR / "report"
PROBE_REPORT_DIR = REPORT_DIR / "entry_context_intraday_probe"
PIPELINE_EVENTS_DIR = DATA_DIR / "pipeline_events"
CONTEXT_CANDIDATE_DIR = DATA_DIR / "ai_canonical_context_candidates"
CLEAN_BASELINE_POLICY_PATH = DATA_DIR / "source_quality" / "clean_baseline_policy.json"
AI_MARKET_SNAPSHOT_SCHEMA_INTRODUCED_DATE = "2026-07-23"
HOLDING_FLOW_EXACT_CONTEXT_RECOVERY_CONTRACT = {
    "metric_role": "holding_flow_exact_context_recovery",
    "decision_authority": "forensics_only_no_runtime_change",
    "window_policy": "same_decision_event_exact_logged_context_only",
    "sample_floor": "one_hash_verified_row_per_symbol_venue_session",
    "primary_decision_metric": "exact_context_recovery_status",
    "source_quality_gate": (
        "hash_verified_same_event_fresh_venue_consistent_position_reconciled"
    ),
    "runtime_effect": False,
    "allowed_runtime_apply": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
    "forbidden_uses": (
        "symbol_only_join|future_event_join|cross_venue_join|live_prompt_mutation|"
        "order_or_exit_authority|provider_or_threshold_change"
    ),
}
HOLDING_FLOW_ENTRY_CONTEXT_FEATURES = {
    "entry_context_quality",
    "entry_liquidity_score",
    "fillability_score",
    "order_flow_pressure_score",
    "entry_momentum_score",
}
PREPROMOTION_EXACT_CAPTURE_CONTRACT = {
    "metric_role": "ai_input_source_quality",
    "decision_authority": "forensics_only_no_runtime_change",
    "window_policy": "same_natural_decision_context_explicit_provider_call",
    "sample_floor": "one_valid_row_per_symbol_venue_session_endpoint",
    "primary_decision_metric": "required_source_field_match_status",
    "source_quality_gate": "fresh_same_basis_conflict_free",
    "runtime_effect": False,
    "allowed_runtime_apply": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
    "forbidden_uses": (
        "runtime_decision|order_submit|provider_route_change|threshold_change|"
        "price_or_quantity_change|bot_restart|live_promotion_without_review"
    ),
}

PROBE_FEATURE_KEYS = (
    "source_stage",
    "stage",
    "event_time",
    "time_bucket",
    "score_bucket",
    "risk_context_bucket",
    "stale_bucket",
    "price_resolution_bucket",
    "liquidity_bucket",
    "overbought_bucket",
    "latency_state",
    "latency_reason",
    "ai_input_schema",
    "ai_input_contract_mode",
    "ai_input_source_quality_status",
    "ai_input_source_quality_reason",
    "entry_liquidity_score",
    "entry_liquidity_status",
    "fillability_score",
    "would_fill_now",
    "top1_bid_notional",
    "top1_ask_notional",
    "top3_bid_notional",
    "top3_ask_notional",
    "quote_depth_present",
    "quote_fresh_for_entry",
    "order_flow_pressure_score",
    "entry_order_flow_status",
    "order_flow_pressure_source",
    "entry_momentum_score",
    "entry_momentum_status",
    "entry_context_quality",
    "entry_context_missing_features",
    "latest_strength",
    "buy_pressure_10t",
    "net_aggressive_delta_10t",
    "tick_acceleration_ratio",
    "curr_vs_micro_vwap_bp",
    "micro_vwap_available",
    "minute_candle_window_fresh",
    "quote_age_ms",
    "quote_stale",
    "top3_depth_ratio",
    "spread_bp",
    "microstructure_reaction_entry_reaction_quality",
    "microstructure_reaction_source_quality",
)

REQUIRED_CONTEXT_KEYS = (
    "entry_liquidity_score",
    "entry_liquidity_status",
    "fillability_score",
    "order_flow_pressure_score",
    "entry_order_flow_status",
    "entry_momentum_score",
    "entry_momentum_status",
    "entry_context_quality",
)

AI_DECISION_POINT_CONTRACTS = {
    "entry_screen": {
        "schemas": {
            "entry_screen_hot_v1",
            "entry_screen_v2",
            "entry_screen_compact_v1",
        },
        "required_features": {
            "entry_liquidity_score",
            "fillability_score",
            "order_flow_pressure_score",
            "entry_momentum_score",
            "entry_context_quality",
        },
        "authority": "entry_action_classifier_only",
    },
    "entry_price": {
        "schemas": {"entry_price_compact_v1", "entry_price_v2", "entry_price_raw_v1"},
        "required_features": {
            "entry_context_features",
            "price_context",
            "quote_freshness",
        },
        "authority": "pre_submit_price_classifier_only",
    },
    "holding_score": {
        "schemas": {"holding_score_v2", "holding_score_v2_submit_authority_retry"},
        "required_features": {
            "position_context",
            "pnl_context",
            "source_quality",
            "entry_time_context",
        },
        "authority": "holding_quality_score_only",
    },
    "holding_flow": {
        "schemas": {"holding_flow_text_v1", "holding_flow_v2"},
        "required_features": {"position_context", "flow_state", "entry_time_context"},
        "authority": "bounded_exit_defer_classifier_only",
    },
}

VENUE_PREFLIGHT_REQUIRED_ROWS = {
    "PREMARKET_KRX_LIKE": (
        "entry_screen",
        "gatekeeper",
        "entry_price",
        "post_probe",
    ),
    "KRX": (
        "entry_screen",
        "gatekeeper",
        "entry_price",
        "post_probe",
        "holding_score",
        "holding_flow",
    ),
    "NXT_REGULAR_OVERLAP": (
        "entry_screen",
        "gatekeeper",
        "entry_price",
        "post_probe",
        "holding_score",
        "holding_flow",
    ),
    "NXT_AFTERMARKET": (
        "entry_screen",
        "gatekeeper",
        "entry_price",
        "post_probe",
        "holding_score",
        "holding_flow",
    ),
    "OVERNIGHT": ("overnight",),
}


def _today() -> str:
    return datetime.now().date().isoformat()


def _nonempty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, (list, dict)):
        return bool(value)
    return str(value).strip() not in {"", "-", "None", "none", "null"}


def _api_keys() -> list[str]:
    raw = os.getenv("OPENAI_API_KEYS") or os.getenv("OPENAI_API_KEY") or ""
    keys = [part.strip() for part in raw.split(",") if part.strip()]
    keys.extend(
        v
        for key, v in sorted(CONF.items())
        if str(key).startswith("OPENAI_API_KEY") and v
    )
    return keys


def _read_adm_report(target_date: str, *, build_adm: bool) -> dict[str, Any]:
    if build_adm:
        return adm_mod.build_scalp_entry_action_decision_matrix_report(target_date)
    json_path, _md_path = adm_mod.report_paths(target_date)
    if not json_path.exists():
        return {
            "status": "missing_adm_report",
            "date": target_date,
            "rows": [],
            "artifact": str(json_path),
        }
    try:
        return json.loads(json_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {
            "status": "invalid_adm_report",
            "date": target_date,
            "rows": [],
            "artifact": str(json_path),
            "error": str(exc),
        }


def _pipeline_events_path(target_date: str) -> Path:
    return PIPELINE_EVENTS_DIR / f"pipeline_events_{target_date}.jsonl"


def _read_pipeline_events(target_date: str) -> dict[str, Any]:
    path = _pipeline_events_path(target_date)
    if not path.exists():
        return {"status": "missing_pipeline_events", "artifact": str(path), "rows": []}
    rows = []
    errors = 0
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except Exception:
            errors += 1
            continue
        if isinstance(payload, dict):
            rows.append(payload)
    return {
        "status": "ok" if errors == 0 else "partial_parse_error",
        "artifact": str(path),
        "rows": rows,
        "parse_error_count": errors,
    }


def _clean_baseline_date() -> str:
    try:
        payload = json.loads(CLEAN_BASELINE_POLICY_PATH.read_text(encoding="utf-8"))
    except Exception:
        payload = {}
    return str(payload.get("clean_tuning_baseline_date") or "2026-06-05")


def _read_clean_baseline_pipeline_events(target_date: str) -> dict[str, Any]:
    baseline = _clean_baseline_date()
    exact_provenance_start = max(baseline, AI_MARKET_SNAPSHOT_SCHEMA_INTRODUCED_DATE)
    rows: list[dict[str, Any]] = []
    artifacts: list[str] = []
    parse_errors = 0
    paths = sorted(
        set(PIPELINE_EVENTS_DIR.glob("pipeline_events_*.jsonl"))
        | set(PIPELINE_EVENTS_DIR.glob("pipeline_events_*.jsonl.gz"))
    )
    for path in paths:
        date_token = path.name.removeprefix("pipeline_events_").split(".jsonl", 1)[0]
        if not (exact_provenance_start <= date_token <= target_date):
            continue
        artifacts.append(str(path))
        opener = gzip.open if path.suffix == ".gz" else open
        with opener(path, "rt", encoding="utf-8", errors="replace") as stream:
            for line in stream:
                if "ai_market_snapshot_id" not in line:
                    continue
                try:
                    payload = json.loads(line)
                except Exception:
                    parse_errors += 1
                    continue
                if isinstance(payload, dict):
                    rows.append(payload)
    return {
        "baseline_date": baseline,
        "exact_provenance_start_date": exact_provenance_start,
        "target_date": target_date,
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "parse_error_count": parse_errors,
        "rows": rows,
    }


def _event_fields(row: dict[str, Any]) -> dict[str, Any]:
    fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
    merged = dict(fields)
    for key in (
        "stage",
        "event",
        "record_id",
        "recommendation_id",
        "sim_record_id",
        "sim_parent_record_id",
        "position_cycle_id",
        "stock_code",
        "stock_name",
        "timestamp",
        "event_time",
        "emitted_at",
    ):
        if key in row and not _nonempty(merged.get(key)):
            merged[key] = row.get(key)
    return merged


def _event_schema(fields: dict[str, Any]) -> str:
    for key in (
        "ai_input_schema",
        "holding_score_input_schema",
        "entry_price_input_schema",
        "holding_flow_input_schema",
    ):
        value = fields.get(key)
        if _nonempty(value):
            return str(value)
    return "-"


def _classify_decision_point(fields: dict[str, Any]) -> str | None:
    schema = _event_schema(fields)
    stage = str(fields.get("stage") or fields.get("event") or "").lower()
    endpoint = str(
        fields.get("openai_endpoint_name") or fields.get("bedrock_endpoint_name") or ""
    ).lower()
    if (
        schema.startswith("entry_screen")
        or stage == "scalp_entry_action_decision_snapshot"
    ):
        return "entry_screen"
    if (
        schema.startswith("entry_price")
        or endpoint == "entry_price"
        or "entry_ai_price_canary" in stage
    ):
        return "entry_price"
    if schema.startswith("holding_score") or endpoint == "holding_score":
        return "holding_score"
    if (
        schema.startswith("holding_flow")
        or endpoint == "holding_flow"
        or "holding_flow_override" in stage
    ):
        return "holding_flow"
    return None


def _classify_preflight_decision_point(fields: dict[str, Any]) -> str | None:
    point = _classify_decision_point(fields)
    if point:
        return point
    stage = str(fields.get("stage") or fields.get("event") or "").lower()
    endpoint = str(
        fields.get("openai_endpoint_name") or fields.get("bedrock_endpoint_name") or ""
    ).lower()
    if "gatekeeper" in stage or endpoint == "gatekeeper":
        return "gatekeeper"
    if "post_probe" in stage or "probe_recheck" in stage or "leg_reprice" in stage:
        return "post_probe"
    if "overnight" in stage or endpoint == "overnight":
        return "overnight"
    return None


def _preflight_cohort(fields: dict[str, Any], point: str) -> str | None:
    if point == "overnight":
        return "OVERNIGHT"
    venue = str(
        fields.get("ai_market_snapshot_effective_venue")
        or fields.get("entry_candle_venue")
        or fields.get("holding_context_venue")
        or ""
    ).upper()
    session = str(
        fields.get("ai_market_snapshot_session_bucket")
        or fields.get("entry_candle_session")
        or fields.get("holding_context_session")
        or ""
    ).lower()
    if "premarket" in session or venue == "PREMARKET_KRX_LIKE":
        return "PREMARKET_KRX_LIKE"
    if venue == "NXT" and ("aftermarket" in session or "nxt_entry_window" in session):
        return "NXT_AFTERMARKET"
    if venue == "NXT":
        return "NXT_REGULAR_OVERLAP"
    if venue in {"SOR", "INTEGRATED", "KRX_NXT_INTEGRATED"} and "krx" in session:
        return "KRX"
    if venue == "KRX":
        return "KRX"
    return None


def _truth_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _venue_preflight_matrix(
    pipeline_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    exact_rows = 0
    for row in pipeline_rows:
        if not isinstance(row, dict):
            continue
        fields = _event_fields(row)
        point = _classify_preflight_decision_point(fields)
        if point is None:
            continue
        cohort = _preflight_cohort(fields, point)
        if cohort is None:
            continue
        if _nonempty(fields.get("ai_market_snapshot_id")):
            exact_rows += 1
        grouped.setdefault((cohort, point), []).append(fields)

    matrix_rows = []
    not_ready_rows = []
    for cohort, points in VENUE_PREFLIGHT_REQUIRED_ROWS.items():
        for point in points:
            rows = grouped.get((cohort, point), [])
            exact = [
                row
                for row in rows
                if _nonempty(row.get("ai_market_snapshot_id"))
                and _nonempty(row.get("ai_market_snapshot_captured_at"))
                and _nonempty(row.get("ai_market_snapshot_effective_venue"))
                and _nonempty(row.get("ai_market_snapshot_session_bucket"))
                and _nonempty(row.get("ai_market_snapshot_broker_route"))
                and _nonempty(row.get("ai_market_snapshot_market_data_route"))
                and _nonempty(row.get("ai_market_snapshot_venue_resolution"))
                and _nonempty(
                    row.get("ai_market_snapshot_underlying_event_venue_source")
                )
            ]
            valid = [
                row
                for row in exact
                if _truth_value(
                    row.get(
                        "ai_input_preflight_source_allowed",
                        row.get("ai_input_preflight_allowed"),
                    )
                )
            ]
            blocked = [
                row
                for row in exact
                if not _truth_value(row.get("ai_input_preflight_allowed"))
            ]
            contamination = [
                row
                for row in exact
                if not _truth_value(row.get("ai_input_preflight_venue_consistent"))
            ]
            provider_while_blocked = [
                row
                for row in blocked
                if _truth_value(row.get("provider_called"))
                or _nonempty(row.get("openai_transport_mode"))
                or _nonempty(row.get("bedrock_transport_mode"))
            ]
            provider_rows = [
                row
                for row in exact
                if _truth_value(row.get("provider_called"))
                or _nonempty(row.get("openai_transport_mode"))
                or _nonempty(row.get("bedrock_transport_mode"))
            ]
            payload_contract_missing = [
                row
                for row in provider_rows
                if not _nonempty(row.get("ai_input_payload_sha256"))
                or not _nonempty(row.get("ai_input_payload_bytes"))
            ]
            duplicate_candle_contract_missing = [
                row
                for row in provider_rows
                if "ai_input_duplicate_candle_views_omitted" not in row
            ]
            duplicate_candle_views_present = [
                row
                for row in provider_rows
                if not _truth_value(row.get("ai_input_duplicate_candle_views_omitted"))
            ]
            missing_as_zero = [
                row
                for row in exact
                if _truth_value(row.get("ai_market_snapshot_missing_as_zero"))
            ]
            missing_as_zero_unknown = [
                row for row in exact if "ai_market_snapshot_missing_as_zero" not in row
            ]
            requires_broker = point in {
                "holding_flow",
                "overnight",
            }
            reconciled = [
                row
                for row in valid
                if _truth_value(row.get("ai_input_preflight_position_reconciled"))
            ]
            broker_route_counts: dict[str, int] = {}
            market_data_route_counts: dict[str, int] = {}
            underlying_event_venue_counts: dict[str, int] = {}
            for row in exact:
                for field, target in (
                    ("ai_market_snapshot_broker_route", broker_route_counts),
                    (
                        "ai_market_snapshot_market_data_route",
                        market_data_route_counts,
                    ),
                    (
                        "ai_market_snapshot_underlying_event_venue",
                        underlying_event_venue_counts,
                    ),
                ):
                    value = str(row.get(field) or "UNKNOWN").strip().upper()
                    target[value] = target.get(value, 0) + 1
            ready = bool(
                valid
                and not contamination
                and not provider_while_blocked
                and not payload_contract_missing
                and not duplicate_candle_contract_missing
                and not duplicate_candle_views_present
                and not missing_as_zero
                and not missing_as_zero_unknown
                and (not requires_broker or reconciled)
            )
            status = "ready" if ready else "not_ready"
            row_id = f"{cohort}:{point}"
            if not ready:
                not_ready_rows.append(row_id)
            matrix_rows.append(
                {
                    "row_id": row_id,
                    "cohort": cohort,
                    "decision_point": point,
                    "status": status,
                    "valid_rows": len(valid),
                    "blocked_rows": len(blocked),
                    "cross_venue_contamination": len(contamination),
                    "missing_as_zero": len(missing_as_zero),
                    "missing_as_zero_unknown": len(missing_as_zero_unknown),
                    "provider_called_while_blocked": len(provider_while_blocked),
                    "provider_rows": len(provider_rows),
                    "payload_contract_missing": len(payload_contract_missing),
                    "duplicate_candle_contract_missing": len(
                        duplicate_candle_contract_missing
                    ),
                    "duplicate_candle_views_present": len(
                        duplicate_candle_views_present
                    ),
                    "broker_reconciled_rows": len(reconciled),
                    "observed_rows": len(rows),
                    "exact_provenance_rows": len(exact),
                    "broker_route_counts": dict(sorted(broker_route_counts.items())),
                    "market_data_route_counts": dict(
                        sorted(market_data_route_counts.items())
                    ),
                    "underlying_event_venue_counts": dict(
                        sorted(underlying_event_venue_counts.items())
                    ),
                }
            )
    return {
        "source_scope": "all_clean_baseline_exact_provenance_rows",
        "overall_status": "ready" if not not_ready_rows else "not_ready",
        "required_row_count": len(matrix_rows),
        "ready_row_count": len(matrix_rows) - len(not_ready_rows),
        "exact_provenance_row_count": exact_rows,
        "not_ready_rows": not_ready_rows,
        "rows": matrix_rows,
    }


def _event_has_required_feature(fields: dict[str, Any], feature: str) -> bool:
    if _nonempty(fields.get(feature)):
        return True
    schema = _event_schema(fields)
    if feature == "entry_context_features":
        return schema.startswith("entry_price") and any(
            _nonempty(fields.get(key))
            for key in (
                "entry_liquidity_score",
                "fillability_score",
                "order_flow_pressure_score",
                "entry_context_quality",
            )
        )
    if feature == "price_context":
        return any(
            _nonempty(fields.get(key))
            for key in (
                "order_price",
                "resolved_order_price",
                "best_bid",
                "best_ask",
                "entry_price_input_resolved_order_price",
                "entry_price_input_best_bid",
                "entry_price_input_best_ask",
            )
        )
    if feature == "quote_freshness":
        return any(
            _nonempty(fields.get(key))
            for key in ("quote_age_ms", "quote_stale", "quote_fresh_for_entry")
        )
    if feature == "position_context":
        return any(
            _nonempty(fields.get(key))
            for key in ("profit_rate", "peak_profit", "held_sec", "current_ai_score")
        )
    if feature == "pnl_context":
        return any(
            _nonempty(fields.get(key))
            for key in ("profit_rate", "peak_profit", "drawdown")
        )
    if feature == "source_quality":
        return any(
            _nonempty(fields.get(key))
            for key in (
                "ai_input_source_quality_status",
                "holding_score_data_quality",
                "data_quality",
            )
        )
    if feature == "entry_time_context":
        if _nonempty(fields.get("holding_context_entry_time_context")):
            _recovered, provenance = _recover_holding_flow_exact_context(fields)
            if provenance.get("status") == "exact_recovered":
                return True
        return any(
            _nonempty(fields.get(key))
            for key in (
                "entry_time_context",
                "entry_context_quality",
                "entry_liquidity_score",
                "last_watching_ai_feature_probe_age_sec",
            )
        )
    return False


def _decision_contract_probe(
    adm_rows: list[dict[str, Any]],
    pipeline_rows: list[dict[str, Any]],
    *,
    sample_limit: int,
) -> dict[str, Any]:
    rows_by_point = _decision_point_rows(adm_rows, pipeline_rows)
    summary = {}
    for point, contract in AI_DECISION_POINT_CONTRACTS.items():
        rows = rows_by_point.get(point, [])
        schema_counts = Counter(_event_schema(row) for row in rows)
        action_counts = Counter(
            str(
                row.get("action")
                or row.get("ai_action")
                or row.get("flow_action")
                or "-"
            )
            for row in rows
        )
        missing_counts = {
            feature: sum(
                1 for row in rows if not _event_has_required_feature(row, feature)
            )
            for feature in contract["required_features"]
        }
        summary[point] = {
            "row_count": len(rows),
            "authority": contract["authority"],
            "allowed_schemas": sorted(contract["schemas"]),
            "schema_counts": dict(schema_counts),
            "action_counts": dict(action_counts),
            "missing_required_feature_counts": missing_counts,
            "coverage_status": (
                "ok"
                if rows and all(count == 0 for count in missing_counts.values())
                else "missing_rows" if not rows else "missing_required_features"
            ),
            "sample_rows": [
                {
                    "stage": row.get("stage"),
                    "stock_code": row.get("stock_code"),
                    "stock_name": row.get("stock_name"),
                    "schema": _event_schema(row),
                    "action": row.get("action")
                    or row.get("ai_action")
                    or row.get("flow_action"),
                    "score": row.get("score")
                    or row.get("ai_score")
                    or row.get("current_ai_score"),
                    "source_quality": row.get("ai_input_source_quality_status")
                    or row.get("holding_score_data_quality")
                    or row.get("data_quality"),
                }
                for row in rows[: max(1, int(sample_limit or 1))]
            ],
        }
    return {
        "decision_points": summary,
        "overall_status": (
            "ok"
            if all(item["coverage_status"] == "ok" for item in summary.values())
            else "missing_rows_or_features"
        ),
    }


def _decision_point_rows(
    adm_rows: list[dict[str, Any]],
    pipeline_rows: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    rows_by_point: dict[str, list[dict[str, Any]]] = {
        key: [] for key in AI_DECISION_POINT_CONTRACTS
    }
    for row in adm_rows:
        if not isinstance(row, dict):
            continue
        stage = str(row.get("stage") or "")
        source_stage = str(row.get("source_stage") or "")
        if (
            stage == "scalp_entry_action_decision_snapshot"
            or source_stage == "ai_confirmed"
        ):
            rows_by_point["entry_screen"].append(row)
    for row in pipeline_rows:
        if not isinstance(row, dict):
            continue
        fields = _event_fields(row)
        point = _classify_decision_point(fields)
        if point:
            rows_by_point[point].append(fields)
    for rows in rows_by_point.values():
        rows.sort(
            key=lambda item: str(
                item.get("event_time")
                or item.get("timestamp")
                or item.get("emitted_at")
                or ""
            ),
            reverse=True,
        )
    return rows_by_point


def _probe_payload(row: dict[str, Any], index: int) -> dict[str, Any]:
    context = {
        key: row.get(key) for key in PROBE_FEATURE_KEYS if _nonempty(row.get(key))
    }
    return {
        "case_id": f"intraday_entry_context_{index:02d}",
        "authority": "forensics_only_no_runtime_change",
        "stock_code": row.get("stock_code"),
        "stock_name": row.get("stock_name"),
        "entry_context": context,
        "withheld_field_policy": "No realized outcome or realized PnL is available intraday.",
        "allowed_actions": ["BUY", "WAIT", "DROP"],
    }


def _candidate_rows(rows: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    candidates = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        stage = str(row.get("stage") or "")
        source_stage = str(row.get("source_stage") or "")
        if (
            stage != "scalp_entry_action_decision_snapshot"
            and source_stage != "ai_confirmed"
        ):
            continue
        if not any(_nonempty(row.get(key)) for key in REQUIRED_CONTEXT_KEYS):
            continue
        candidates.append(row)
    candidates.sort(key=lambda item: str(item.get("event_time") or ""), reverse=True)
    return candidates[: max(1, int(limit or 1))]


def _coverage(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(rows)
    field_counts = {
        key: sum(1 for row in rows if _nonempty(row.get(key)))
        for key in REQUIRED_CONTEXT_KEYS
    }
    quality_counts = Counter(
        str(row.get("entry_context_quality") or "-") for row in rows
    )
    liquidity_counts = Counter(
        str(row.get("entry_liquidity_status") or "-") for row in rows
    )
    flow_counts = Counter(
        str(row.get("entry_order_flow_status") or "-") for row in rows
    )
    momentum_counts = Counter(
        str(row.get("entry_momentum_status") or "-") for row in rows
    )
    missing_counts: Counter[str] = Counter()
    for row in rows:
        for item in (
            str(row.get("entry_context_missing_features") or "")
            .replace("|", ",")
            .split(",")
        ):
            token = item.strip()
            if token:
                missing_counts[token] += 1
    complete_or_partial = sum(
        1
        for row in rows
        if str(row.get("entry_context_quality") or "") in {"complete", "partial"}
    )
    return {
        "row_count": total,
        "complete_or_partial_count": complete_or_partial,
        "complete_or_partial_rate_pct": (
            round((complete_or_partial / total) * 100.0, 2) if total else 0.0
        ),
        "required_field_counts": field_counts,
        "entry_context_quality_counts": dict(quality_counts),
        "entry_liquidity_status_counts": dict(liquidity_counts),
        "entry_order_flow_status_counts": dict(flow_counts),
        "entry_momentum_status_counts": dict(momentum_counts),
        "entry_context_missing_feature_counts": dict(missing_counts),
    }


class _RulesProxy:
    def __init__(self, base: Any, **overrides: Any):
        self._base = base
        self._overrides = overrides

    def __getattr__(self, name: str) -> Any:
        if name in self._overrides:
            return self._overrides[name]
        return getattr(self._base, name)


FORENSIC_ENTRY_MISSING_FEATURES = {
    "current_price",
    "bbo",
    "orderbook",
    "quote_freshness",
    "signed_tape",
    "micro_vwap",
    "minute_candles",
    "multi_timeframe_bars",
    "session_vwap",
    "opening_range",
    "previous_day_levels",
    "program_flow",
    "investor_flow",
    "market_regime",
    "sector_relative_trend",
    "execution_strength",
    "buy_ratio",
}
FORENSIC_ENTRY_ISSUES = {
    "bad_entry",
    "insufficient_context",
    "acceptable_risk",
    "source_quality_gap",
}


def _forensic_response_errors(result: Any) -> list[str]:
    if not isinstance(result, dict):
        return ["response_not_object"]
    errors: list[str] = []
    action = str(result.get("action") or "")
    if action not in {"BUY", "WAIT", "DROP"}:
        errors.append("action_invalid")
    try:
        score = int(float(result.get("score")))
    except (TypeError, ValueError):
        score = -1
        errors.append("score_invalid")
    if not 0 <= score <= 100:
        errors.append("score_out_of_range")
    elif (
        (action == "DROP" and score > 39)
        or (action == "WAIT" and not 40 <= score <= 69)
        or (action == "BUY" and score < 70)
    ):
        errors.append("action_score_contract_mismatch")
    if str(result.get("issue") or "") not in FORENSIC_ENTRY_ISSUES:
        errors.append("issue_invalid")
    confidence = result.get("confidence")
    try:
        confidence_value = float(confidence)
    except (TypeError, ValueError):
        confidence_value = -1.0
    if not 0.0 <= confidence_value <= 1.0:
        errors.append("confidence_invalid")
    missing = result.get("missing_features")
    if not isinstance(missing, list) or any(
        not isinstance(item, str) or item not in FORENSIC_ENTRY_MISSING_FEATURES
        for item in (missing or [])
    ):
        errors.append("missing_features_semantic_invalid")
    reason = str(result.get("reason") or "")
    try:
        reason.encode("ascii")
    except UnicodeEncodeError:
        errors.append("reason_non_ascii")
    if not reason.strip() or len(reason) > 120:
        errors.append("reason_invalid")
    return sorted(set(errors))


def _forensic_provider(transport_meta: dict[str, Any], *, called: bool) -> str:
    explicit = str(
        transport_meta.get("provider") or transport_meta.get("provider_actual") or ""
    ).strip()
    if explicit and explicit.lower() != "none":
        return explicit
    if transport_meta.get("bedrock_primary_used") or transport_meta.get(
        "bedrock_fallback_used"
    ):
        return "bedrock"
    if transport_meta.get("bedrock_failback_used"):
        return "openai"
    if called and (
        transport_meta.get("openai_transport_mode")
        or transport_meta.get("openai_model")
    ):
        return "openai"
    return "none"


def _physical_provider_called(
    transport_meta: dict[str, Any],
    *,
    response_returned: bool,
) -> bool:
    if response_returned:
        return True
    explicit = (
        str(
            transport_meta.get("provider")
            or transport_meta.get("provider_actual")
            or ""
        )
        .strip()
        .lower()
    )
    if explicit and explicit != "none":
        return True
    if any(
        transport_meta.get(key)
        for key in (
            "bedrock_primary_used",
            "bedrock_fallback_used",
            "bedrock_failback_used",
            "openai_ws_used",
            "openai_response_id",
            "provider_response_id",
            "bedrock_response_id",
        )
    ):
        return True
    try:
        return int(transport_meta.get("openai_http_attempt_count") or 0) > 0
    except (TypeError, ValueError):
        return False


def _finalize_forensic_entry_attempt(
    *,
    result: dict[str, Any],
    transport_meta: dict[str, Any],
    row: dict[str, Any],
    semantic_errors: list[str],
    attempt: int,
    final_attempt: bool,
    provider_called: bool,
) -> None:
    merged = {
        **dict(transport_meta or {}),
        **dict(result or {}),
        "provider_called": bool(provider_called),
        "provider": _forensic_provider(
            transport_meta,
            called=provider_called,
        ),
        "ai_parse_ok": not semantic_errors,
        "ai_trace_stock_code": row.get("stock_code"),
        "ai_trace_record_id": row.get("record_id"),
        "actual_order_authority": False,
        "ai_decision_outcome_eligible": not semantic_errors,
        "forensic_attempt": int(attempt),
        "forensic_attempt_final": bool(final_attempt),
        "forensic_semantic_errors": list(semantic_errors),
    }
    result_source = (
        "forensic_observation_accepted"
        if not semantic_errors
        else (
            "schema_semantic_rejected"
            if final_attempt
            else "schema_semantic_rejected_retry"
        )
    )
    record_ai_decision_trace(
        merged,
        prompt_type="scalping_entry",
        prompt_version="entry_context_intraday_probe_forensics_v1",
        result_source=result_source,
        decision_stage="entry_screen_forensics",
        stock_code=str(row.get("stock_code") or "-"),
        provider_called=provider_called,
    )


def _call_openai(
    rows: list[dict[str, Any]], *, model: str, effort: str
) -> list[dict[str, Any]]:
    from src.engine import ai_engine_openai as openai_module
    from src.engine.ai_engine_openai import GPTSniperEngine

    keys = _api_keys()
    if not keys:
        return [{"status": "skipped", "reason": "OPENAI_API_KEY not configured"}]
    original_rules = openai_module.TRADING_RULES
    openai_module.TRADING_RULES = _RulesProxy(
        original_rules,
        OPENAI_TRANSPORT_MODE="http",
        OPENAI_REASONING_EFFORT=effort,
        OPENAI_ANALYZE_TARGET_TIMEOUT_MS=10000,
        OPENAI_RESPONSES_MAX_OUTPUT_TOKENS=512,
    )
    try:
        engine = GPTSniperEngine(keys[:1], announce_startup=False)
        prompt = (
            "You are evaluating a KORStockScan intraday entry candidate using only pre-entry/source fields. "
            "No realized outcome or realized PnL is available. Return exactly one valid minified JSON object "
            "with keys action, score, issue, confidence, missing_features, reason. action must be BUY, WAIT, "
            "or DROP as if this candidate appeared now with the same observable facts. score is entry suitability "
            "from 0 to 100. Use DROP only when score is 0-39, WAIT only when score is 40-69, BUY only when "
            "score is 70-100. issue must be bad_entry, insufficient_context, acceptable_risk, or "
            "source_quality_gap. missing_features must contain only canonical names from this list: "
            + ",".join(sorted(FORENSIC_ENTRY_MISSING_FEATURES))
            + ". reason must contain English ASCII only and be at most 120 characters. "
            "Do not emit stop, exit, realized outcome, broker, threshold, bot, provider, or cap fields."
        )
        results = []
        for index, row in enumerate(rows, start=1):
            started = time.perf_counter()
            payload_text = json.dumps(
                _probe_payload(row, index),
                ensure_ascii=True,
                separators=(",", ":"),
            )
            result: dict[str, Any] = {}
            errors: list[str] = []
            transport_meta: dict[str, Any] = {}
            attempts = 0
            call_error_type = None
            provider_was_called = False
            for attempt in range(2):
                attempts = attempt + 1
                active_prompt = prompt
                if attempt:
                    active_prompt += (
                        " Correction retry: the previous response violated these contract rules: "
                        + ",".join(errors)
                        + ". Return a corrected object only."
                    )
                try:
                    candidate = engine._call_openai_safe(
                        active_prompt,
                        payload_text,
                        require_json=True,
                        context_name=(
                            f"INTRADAY_ENTRY_CONTEXT_PROBE:{model}:{effort}:"
                            f"{row.get('stock_code')}:attempt{attempt + 1}"
                        ),
                        model_override=model,
                        endpoint_name="analyze_target",
                        symbol=str(row.get("stock_code") or "INTRADAY_PROBE"),
                        cache_key=(
                            f"intraday-entry-context-probe:{model}:{effort}:"
                            f"{row.get('candidate_id')}:{row.get('event_time')}:"
                            f"attempt{attempt + 1}"
                        ),
                    )
                except Exception as exc:
                    candidate = None
                    call_error_type = type(exc).__name__
                if hasattr(engine, "_consume_last_transport_meta"):
                    transport_meta = engine._consume_last_transport_meta()
                elif isinstance(candidate, dict):
                    transport_meta = {
                        "provider": "openai",
                        "openai_model": model,
                        "openai_transport_mode": "test_double",
                    }
                provider_was_called = _physical_provider_called(
                    transport_meta,
                    response_returned=call_error_type is None,
                )
                if call_error_type:
                    result = {}
                    errors = [f"provider_call_failed:{call_error_type}"]
                    if (
                        _forensic_provider(
                            transport_meta,
                            called=provider_was_called,
                        )
                        == "none"
                    ):
                        errors.append("provider_none")
                    errors = sorted(set(errors))
                    _finalize_forensic_entry_attempt(
                        result=result,
                        transport_meta=transport_meta,
                        row=row,
                        semantic_errors=errors,
                        attempt=attempts,
                        final_attempt=True,
                        provider_called=provider_was_called,
                    )
                    break
                result = dict(candidate) if isinstance(candidate, dict) else {}
                errors = _forensic_response_errors(result)
                provider = _forensic_provider(
                    transport_meta,
                    called=provider_was_called,
                )
                if provider == "none":
                    errors = sorted(set([*errors, "provider_none"]))
                final_attempt = bool(not errors or attempt == 1)
                _finalize_forensic_entry_attempt(
                    result=result,
                    transport_meta=transport_meta,
                    row=row,
                    semantic_errors=errors,
                    attempt=attempts,
                    final_attempt=final_attempt,
                    provider_called=provider_was_called,
                )
                if not errors:
                    break
            try:
                score = int(float(result.get("score", 0) or 0))
            except (TypeError, ValueError):
                score = 0
            action = str(result.get("action") or "")
            mismatch = (
                (action == "DROP" and score > 39)
                or (action == "WAIT" and not (40 <= score <= 69))
                or (action == "BUY" and score < 70)
            )
            results.append(
                {
                    "stock_code": row.get("stock_code"),
                    "stock_name": row.get("stock_name"),
                    "event_time": row.get("event_time"),
                    "entry_context_quality": row.get("entry_context_quality"),
                    "entry_liquidity_status": row.get("entry_liquidity_status"),
                    "entry_order_flow_status": row.get("entry_order_flow_status"),
                    "entry_momentum_status": row.get("entry_momentum_status"),
                    "model": model,
                    "effort": effort,
                    "status": (
                        "accepted" if not errors else "schema_semantic_rejected"
                    ),
                    "semantic_errors": errors,
                    "provider_call_error_type": call_error_type,
                    "correction_attempted": attempts > 1,
                    "attempt_count": attempts,
                    "request_id": transport_meta.get("openai_request_id"),
                    "provider": _forensic_provider(
                        transport_meta,
                        called=provider_was_called,
                    ),
                    "provider_response_id": transport_meta.get("openai_response_id")
                    or transport_meta.get("provider_response_id"),
                    "transport": transport_meta.get("openai_transport_mode"),
                    "response_sha256": transport_meta.get("openai_response_sha256")
                    or hashlib.sha256(
                        json.dumps(
                            result,
                            ensure_ascii=False,
                            sort_keys=True,
                            separators=(",", ":"),
                        ).encode("utf-8")
                    ).hexdigest(),
                    "input_tokens": transport_meta.get("openai_input_tokens"),
                    "output_tokens": transport_meta.get("openai_output_tokens"),
                    "total_tokens": transport_meta.get("openai_total_tokens"),
                    "failback_chain": [
                        key
                        for key in (
                            "bedrock_primary_used",
                            "bedrock_fallback_used",
                            "bedrock_failback_used",
                            "openai_ws_http_fallback",
                        )
                        if transport_meta.get(key)
                    ],
                    "elapsed_ms": int((time.perf_counter() - started) * 1000),
                    "action": action,
                    "score": score,
                    "action_score_mismatch": bool(mismatch),
                    "issue": str(result.get("issue") or ""),
                    "confidence": result.get("confidence"),
                    "missing_features": result.get("missing_features"),
                    "reason": str(result.get("reason") or "")[:160],
                }
            )
        return results
    finally:
        openai_module.TRADING_RULES = original_rules


def _first_nonempty(row: dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        value = row.get(key)
        if _nonempty(value):
            return value
    return default


def _float_or_zero(value: Any) -> float:
    try:
        return float(str(value).replace(",", "").strip())
    except Exception:
        return 0.0


def _int_or_zero(value: Any) -> int:
    return int(_float_or_zero(value))


def _boolish(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _structured_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return list(value)
    if isinstance(value, tuple):
        return list(value)
    if not isinstance(value, str) or not value.strip():
        return []
    for loader in (json.loads, ast.literal_eval):
        try:
            parsed = loader(value)
        except (TypeError, ValueError, SyntaxError, json.JSONDecodeError):
            continue
        if isinstance(parsed, (list, tuple)):
            return list(parsed)
    return []


def _structured_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if not isinstance(value, str) or not value.strip():
        return {}
    for loader in (json.loads, ast.literal_eval):
        try:
            parsed = loader(value)
        except (TypeError, ValueError, SyntaxError, json.JSONDecodeError):
            continue
        if isinstance(parsed, dict):
            return dict(parsed)
    return {}


def _canonical_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()


def _recover_holding_flow_exact_context(
    fields: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    recovered = dict(fields)
    logged = _structured_dict(fields.get("holding_context_entry_time_context"))
    embedded = _structured_dict(fields.get("entry_time_context"))
    context = logged or embedded
    expected_hash = str(
        fields.get("holding_context_entry_time_context_sha256") or ""
    ).strip()
    actual_hash = _canonical_sha256(context) if context else ""
    producer_status = str(
        fields.get(
            "holding_context_entry_time_context_status"
            if logged
            else "entry_time_context_status"
        )
        or ""
    ).strip()
    source = (
        "holding_context_same_event_log"
        if logged
        else ("entry_time_context_same_event_log" if embedded else "unavailable")
    )
    if not context:
        status = "source_unavailable"
    elif producer_status != "exact_captured":
        status = "producer_status_unverified"
    elif not expected_hash:
        status = "hash_missing"
    elif expected_hash and expected_hash != actual_hash:
        status = "hash_mismatch"
    elif not (
        str(context.get("entry_context_quality") or "").strip().lower()
        in {"complete", "partial"}
        or any(
            _nonempty(context.get(key))
            for key in (HOLDING_FLOW_ENTRY_CONTEXT_FEATURES - {"entry_context_quality"})
        )
    ):
        status = "required_features_missing"
    else:
        status = "exact_recovered"
        recovered["entry_time_context"] = context
    provenance = {
        "status": status,
        "source": source,
        "context_sha256": actual_hash or None,
        "expected_sha256": expected_hash or None,
        "producer_status": producer_status or None,
        "record_id": _first_nonempty(
            fields,
            "record_id",
            "sim_parent_record_id",
            "sim_record_id",
            default=None,
        ),
        **HOLDING_FLOW_EXACT_CONTEXT_RECOVERY_CONTRACT,
    }
    recovered["holding_flow_exact_context_recovery"] = provenance
    return recovered, provenance


def _temporary_env(overrides: dict[str, str]) -> dict[str, str | None]:
    original = {key: os.environ.get(key) for key in overrides}
    for key, value in overrides.items():
        os.environ[key] = value
    return original


def _restore_env(original: dict[str, str | None]) -> None:
    for key, value in original.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


def _fields_to_ws_data(fields: dict[str, Any]) -> dict[str, Any]:
    curr = _first_nonempty(
        fields,
        "curr",
        "current_price",
        "entry_price_input_current_price",
        "order_price",
        "resolved_order_price",
        "entry_price_input_resolved_order_price",
        default=0,
    )
    best_bid = _first_nonempty(
        fields,
        "best_bid",
        "entry_price_input_best_bid",
        "top_bid",
        "bid_price",
        default=0,
    )
    best_ask = _first_nonempty(
        fields,
        "best_ask",
        "entry_price_input_best_ask",
        "top_ask",
        "ask_price",
        default=0,
    )
    ws_data = {
        "curr": _int_or_zero(curr),
        "current_price": _int_or_zero(curr),
        "v_pw": _float_or_zero(
            _first_nonempty(
                fields, "v_pw", "latest_strength", "execution_strength", default=0
            )
        ),
        "buy_ratio": _float_or_zero(
            _first_nonempty(fields, "buy_ratio", "buy_pressure_10t", default=0)
        ),
        "buy_exec_volume": _float_or_zero(
            _first_nonempty(fields, "buy_exec_volume", default=0)
        ),
        "sell_exec_volume": _float_or_zero(
            _first_nonempty(fields, "sell_exec_volume", default=0)
        ),
        "ask_tot": _float_or_zero(
            _first_nonempty(fields, "ask_tot", "top3_ask_notional", default=0)
        ),
        "bid_tot": _float_or_zero(
            _first_nonempty(fields, "bid_tot", "top3_bid_notional", default=0)
        ),
        "quote_age_ms": _float_or_zero(
            _first_nonempty(fields, "quote_age_ms", default=0)
        ),
        "quote_stale": _boolish(_first_nonempty(fields, "quote_stale", default=False)),
    }
    if _nonempty(best_bid) or _nonempty(best_ask):
        ws_data["orderbook"] = {
            "bids": [
                {
                    "price": _int_or_zero(best_bid),
                    "qty": _int_or_zero(
                        _first_nonempty(fields, "best_bid_qty", default=0)
                    ),
                }
            ],
            "asks": [
                {
                    "price": _int_or_zero(best_ask),
                    "qty": _int_or_zero(
                        _first_nonempty(fields, "best_ask_qty", default=0)
                    ),
                }
            ],
        }
    return ws_data


def _fields_to_price_ctx(fields: dict[str, Any]) -> dict[str, Any]:
    current_price = _first_nonempty(
        fields,
        "curr",
        "current_price",
        "entry_price_input_current_price",
        "order_price",
        "resolved_order_price",
        "entry_price_input_resolved_order_price",
        default=0,
    )
    order_price = _first_nonempty(
        fields,
        "order_price",
        "resolved_order_price",
        "entry_price_input_resolved_order_price",
        "candidate_order_price",
        "candidate_price",
        "original_order_price",
        default=current_price,
    )
    return {
        "resolved_order_price": _int_or_zero(order_price),
        "defensive_order_price": _int_or_zero(
            _first_nonempty(fields, "defensive_order_price", default=order_price)
        ),
        "reference_target_price": _int_or_zero(
            _first_nonempty(fields, "reference_target_price", default=order_price)
        ),
        "entry_price_guard": _first_nonempty(
            fields, "entry_price_guard", "price_resolution_reason", default="-"
        ),
        "quote_age_ms": _first_nonempty(fields, "quote_age_ms", default=0),
        "quote_stale": _boolish(_first_nonempty(fields, "quote_stale", default=False)),
        "ws_age_ms": _first_nonempty(fields, "ws_age_ms", "quote_age_ms", default=0),
        "latency_state": _first_nonempty(fields, "latency_state", default="-"),
        "entry_liquidity_score": _first_nonempty(
            fields, "entry_liquidity_score", default=None
        ),
        "fillability_score": _first_nonempty(fields, "fillability_score", default=None),
        "order_flow_pressure_score": _first_nonempty(
            fields, "order_flow_pressure_score", default=None
        ),
        "entry_context_quality": _first_nonempty(
            fields, "entry_context_quality", default=None
        ),
        "best_bid": _int_or_zero(
            _first_nonempty(fields, "best_bid", "entry_price_input_best_bid", default=0)
        ),
        "best_ask": _int_or_zero(
            _first_nonempty(fields, "best_ask", "entry_price_input_best_ask", default=0)
        ),
        "orderbook_micro": {
            "spread_bp": _first_nonempty(fields, "spread_bp", default=None),
            "top_depth_ratio": _first_nonempty(
                fields, "top3_depth_ratio", default=None
            ),
            "ofi": _first_nonempty(fields, "order_flow_pressure_score", default=None),
            "qi": _first_nonempty(fields, "fillability_score", default=None),
        },
    }


def _fields_to_entry_candle_context(fields: dict[str, Any]) -> dict[str, Any]:
    """Rehydrate the common schema for report-only provider comparisons."""
    embedded = fields.get("entry_candle_context")
    if isinstance(embedded, dict) and embedded.get("schema"):
        return dict(embedded)
    quality = str(
        _first_nonempty(
            fields,
            "entry_candle_source_quality_status",
            default="observation_summary_only",
        )
    )
    return {
        "schema": str(
            _first_nonempty(
                fields,
                "entry_candle_context_schema",
                default="entry_candle_context_v1",
            )
        ),
        "enabled": True,
        "venue": _first_nonempty(fields, "entry_candle_venue", default="unknown"),
        "session": _first_nonempty(fields, "entry_candle_session", default="unknown"),
        "current_session_bar_count": _int_or_zero(
            _first_nonempty(fields, "entry_candle_current_session_bar_count", default=0)
        ),
        "completed_bar_count": _int_or_zero(
            _first_nonempty(fields, "entry_candle_completed_bar_count", default=0)
        ),
        "forming_bar_present": _boolish(
            _first_nonempty(fields, "entry_candle_forming_bar_present", default=False)
        ),
        "latest_bar_age_sec": _first_nonempty(
            fields, "entry_candle_latest_bar_age_sec", default=None
        ),
        "sample_mode": _first_nonempty(
            fields, "entry_candle_sample_mode", default="unknown"
        ),
        "bars": [],
        "structure": {},
        "regime": _first_nonempty(fields, "entry_candle_regime", default="unknown"),
        "alignment": _first_nonempty(
            fields, "entry_candle_alignment", default="unknown"
        ),
        "risk_flags": ["provider_compare_missing_raw_bar_path"],
        "source_quality": {
            "status": quality,
            "blockers": ["provider_compare_missing_raw_bar_path"],
        },
    }


def _entry_context_to_recent_candles(
    context: dict[str, Any],
) -> list[dict[str, Any]]:
    rows = []
    for bar in context.get("bars") or []:
        if not isinstance(bar, dict):
            continue
        rows.append(
            {
                "time": bar.get("t", bar.get("minute")),
                "open": bar.get("o", bar.get("open")),
                "high": bar.get("h", bar.get("high")),
                "low": bar.get("l", bar.get("low")),
                "close": bar.get("c", bar.get("close")),
                "volume": bar.get("v", bar.get("volume")),
                "forming": bool(bar.get("forming", bar.get("is_forming"))),
                "partial_volume": bool(
                    bar.get("partial_volume", bar.get("volume_is_partial"))
                ),
            }
        )
    return rows


def _fields_to_holding_decision_context(
    fields: dict[str, Any],
) -> dict[str, Any]:
    """Rehydrate compact report evidence without inventing trade direction."""

    embedded = fields.get("holding_decision_context")
    if isinstance(embedded, dict) and embedded.get("schema"):
        return dict(embedded)
    entry_context = _fields_to_entry_candle_context(fields)
    model_bars = _structured_list(fields.get("holding_context_model_bars"))
    model_structure = _structured_dict(fields.get("holding_context_model_structure"))
    market_snapshot = _structured_dict(fields.get("holding_context_ai_market_snapshot"))
    source_status = str(
        _first_nonempty(
            fields,
            "holding_context_source_quality_status",
            default="observation_summary_only",
        )
    )
    blockers = _structured_list(fields.get("holding_context_blockers"))
    if not blockers and source_status != "fresh_consistent":
        blockers = ["provider_compare_missing_full_holding_source"]
    context = {
        "schema": "holding_decision_context_v1",
        "enabled": _boolish(
            _first_nonempty(fields, "holding_context_enabled", default=False)
        ),
        "decision_kind": "intraday_probe_compare",
        "venue": _first_nonempty(
            fields, "holding_context_venue", "entry_candle_venue", default="unknown"
        ),
        "session": _first_nonempty(
            fields,
            "holding_context_session",
            "entry_candle_session",
            default="unknown",
        ),
        "rest_route": _first_nonempty(
            fields, "holding_context_rest_route", default="unknown"
        ),
        "ws_route": _first_nonempty(
            fields, "holding_context_ws_route", default="unknown"
        ),
        "candle": {
            "current_session_bar_count": _int_or_zero(
                _first_nonempty(
                    fields,
                    "holding_context_candle_bar_count",
                    "entry_candle_current_session_bar_count",
                    default=0,
                )
            ),
            "latest_bar_age_sec": _first_nonempty(
                fields,
                "holding_context_candle_latest_age_sec",
                "entry_candle_latest_bar_age_sec",
                default=None,
            ),
            "bars": model_bars or list(entry_context.get("bars") or []),
            "structure": model_structure or dict(entry_context.get("structure") or {}),
            "regime": _first_nonempty(
                fields,
                "holding_context_candle_regime",
                "entry_candle_regime",
                default="unknown",
            ),
            "alignment": _first_nonempty(
                fields,
                "holding_context_candle_alignment",
                "entry_candle_alignment",
                default="unknown",
            ),
            "risk_flags": _structured_list(
                fields.get("holding_context_candle_risk_flags")
            ),
        },
        "signed_tape": {
            "state": _first_nonempty(
                fields, "holding_context_tape_state", default="missing"
            ),
            "source": _first_nonempty(
                fields, "holding_context_tape_source", default="missing"
            ),
            "sample_count": _int_or_zero(
                _first_nonempty(fields, "holding_context_tape_sample_count", default=0)
            ),
            "age_ms": _first_nonempty(
                fields, "holding_context_tape_age_ms", default=None
            ),
        },
        "microstructure": {
            "best_bid": _int_or_zero(
                _first_nonempty(fields, "holding_context_best_bid", default=0)
            ),
            "best_ask": _int_or_zero(
                _first_nonempty(fields, "holding_context_best_ask", default=0)
            ),
            "quote_age_ms": _first_nonempty(
                fields, "holding_context_quote_age_ms", default=None
            ),
            "bbo_fresh": _boolish(
                _first_nonempty(fields, "holding_context_bbo_fresh", default=False)
            ),
            "spread_bps": _first_nonempty(
                fields, "holding_context_spread_bps", default=None
            ),
            "ofi_regime": _first_nonempty(
                fields, "holding_context_ofi_regime", default=None
            ),
        },
        "execution_pnl": {
            "mark_pnl_pct": _first_nonempty(
                fields, "holding_context_mark_pnl_pct", default=None
            ),
            "executable_pnl_pct": _first_nonempty(
                fields, "holding_context_executable_pnl_pct", default=None
            ),
        },
        "position_lifecycle": {
            "memory_qty": _int_or_zero(
                _first_nonempty(fields, "holding_context_memory_qty", default=0)
            ),
            "broker_qty": _int_or_zero(
                _first_nonempty(fields, "holding_context_broker_qty", default=0)
            ),
        },
        "order_reconciliation": {
            "exit_token_active": _boolish(
                _first_nonempty(
                    fields, "holding_context_exit_token_active", default=False
                )
            ),
            "order_or_quantity_conflict": _boolish(
                _first_nonempty(fields, "holding_context_order_conflict", default=False)
            ),
        },
        "source_quality": {
            "status": source_status,
            "hold_defer_allowed": _boolish(
                _first_nonempty(
                    fields,
                    "holding_context_hold_defer_allowed",
                    default=False,
                )
            ),
            "blockers": blockers,
        },
        "observation_contract": HOLDING_CONTEXT_OBSERVATION_CONTRACT,
    }
    if market_snapshot:
        context["ai_market_snapshot_v1"] = market_snapshot
    return context


def _fields_to_position_ctx(fields: dict[str, Any]) -> dict[str, Any]:
    profit_rate = _float_or_zero(
        _first_nonempty(fields, "profit_rate", "pnl_pct", default=0.0)
    )
    peak_profit = _float_or_zero(
        _first_nonempty(fields, "peak_profit", default=profit_rate)
    )
    exact_entry_time_context = _structured_dict(fields.get("entry_time_context"))
    return {
        "record_id": _first_nonempty(fields, "record_id", default=None),
        "buy_price": _int_or_zero(
            _first_nonempty(
                fields, "buy_price", "avg_price", "average_entry_price", default=0
            )
        ),
        "curr_price": _int_or_zero(
            _first_nonempty(fields, "curr", "current_price", default=0)
        ),
        "profit_rate": profit_rate,
        "peak_profit": peak_profit,
        "drawdown": max(0.0, peak_profit - profit_rate),
        "held_sec": _int_or_zero(_first_nonempty(fields, "held_sec", default=0)),
        "current_ai_score": _float_or_zero(
            _first_nonempty(fields, "current_ai_score", "score", "ai_score", default=0)
        ),
        "exit_rule": _first_nonempty(
            fields, "exit_rule", "candidate_exit_rule", default="-"
        ),
        "flow_state": _first_nonempty(fields, "flow_state", default="-"),
        "reason": _first_nonempty(fields, "reason", default="-"),
        "entry_time_context": exact_entry_time_context,
    }


def _endpoint_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    ok_rows = [row for row in results if row.get("status") == "ok"]
    return {
        "row_count": len(ok_rows),
        "skipped_count": sum(1 for row in results if row.get("status") == "skipped"),
        "error_count": sum(1 for row in results if row.get("status") == "error"),
        "provider_none_count": sum(
            1 for row in results if row.get("provider") == "none"
        ),
        "provider_response_id_count": sum(
            1 for row in ok_rows if row.get("provider_response_id")
        ),
        "action_changed_count": sum(1 for row in ok_rows if row.get("action_changed")),
        "order_price_changed_count": sum(
            1 for row in ok_rows if row.get("order_price_changed")
        ),
        "flow_state_changed_count": sum(
            1 for row in ok_rows if row.get("flow_state_changed")
        ),
        "bedrock_primary_used_count": sum(
            1 for row in ok_rows if row.get("bedrock_primary_used")
        ),
        "bedrock_failback_used_count": sum(
            1 for row in ok_rows if row.get("bedrock_failback_used")
        ),
        "bedrock_fallback_used_count": sum(
            1 for row in ok_rows if row.get("bedrock_fallback_used")
        ),
    }


def _endpoint_provider_env(provider_mode: str) -> dict[str, str]:
    if provider_mode == "bedrock_primary":
        return {
            "KORSTOCKSCAN_BEDROCK_ENTRY_PRICE_ROUTE_MODE": "primary",
            "KORSTOCKSCAN_BEDROCK_ENTRY_PRICE_PRIMARY_FAMILY": "qwen3_32b",
            "KORSTOCKSCAN_BEDROCK_ENTRY_PRICE_FAILBACK_FAMILY": "lite_v2",
            "KORSTOCKSCAN_BEDROCK_ENTRY_PRICE_FAILBACK_ENABLED": "true",
            "KORSTOCKSCAN_BEDROCK_NOVA_LITE_ROUTE_MODE": "primary",
            "KORSTOCKSCAN_BEDROCK_NOVA_LITE_PRIMARY_FAMILY": "lite_v2",
            "KORSTOCKSCAN_BEDROCK_NOVA_LITE_PRIMARY_ENDPOINTS": "holding_flow",
        }
    if provider_mode == "openai_primary_bedrock_fallback":
        return {
            "KORSTOCKSCAN_BEDROCK_ENTRY_PRICE_ROUTE_MODE": "off",
            "KORSTOCKSCAN_BEDROCK_NOVA_LITE_ROUTE_MODE": "off",
            "KORSTOCKSCAN_OPENAI_PRIMARY_BEDROCK_FALLBACK_ENDPOINTS": "entry_price",
            "KORSTOCKSCAN_OPENAI_PRIMARY_BEDROCK_FALLBACK_FAMILY": "lite_v2",
            "KORSTOCKSCAN_OPENAI_PRIMARY_BEDROCK_FALLBACK_PRIMARY_TIMEOUT_MS": "7000",
            "KORSTOCKSCAN_OPENAI_PRIMARY_BEDROCK_FALLBACK_TIMEOUT_MS": "7000",
            "KORSTOCKSCAN_OPENAI_ENTRY_PRICE_TIMEOUT_MS": "15000",
        }
    return {
        "KORSTOCKSCAN_BEDROCK_ENTRY_PRICE_ROUTE_MODE": "off",
        "KORSTOCKSCAN_BEDROCK_NOVA_LITE_ROUTE_MODE": "off",
    }


def _endpoint_result_key(row: dict[str, Any]) -> tuple[str, str]:
    return (
        str(row.get("stock_code") or "-"),
        str(row.get("event_time") or "-"),
    )


def _provider_result_provenance(result: dict[str, Any]) -> dict[str, Any]:
    explicit_provider = str(result.get("provider") or "").strip().lower()
    response_id = (
        result.get("openai_response_id")
        or result.get("bedrock_response_id")
        or result.get("provider_response_id")
    )
    response_sha256 = (
        result.get("openai_response_sha256")
        or result.get("bedrock_response_sha256")
        or result.get("ai_response_sha256")
    )
    openai_response_evidence = bool(
        result.get("openai_response_id") or result.get("openai_response_sha256")
    )
    bedrock_response_evidence = bool(
        result.get("bedrock_response_id") or result.get("bedrock_response_sha256")
    )
    if bedrock_response_evidence:
        provider = "bedrock"
    elif openai_response_evidence:
        provider = "openai"
    elif (
        explicit_provider
        and explicit_provider != "none"
        and (response_id or response_sha256)
    ):
        provider = explicit_provider
    else:
        provider = "none"
    total_tokens = result.get("openai_total_tokens")
    if total_tokens is None and (
        result.get("bedrock_total_input_tokens") is not None
        or result.get("bedrock_output_tokens") is not None
    ):
        total_tokens = _int_or_zero(
            result.get("bedrock_total_input_tokens")
        ) + _int_or_zero(result.get("bedrock_output_tokens"))
    return {
        "request_id": result.get("openai_request_id")
        or result.get("ai_decision_trace_id"),
        "provider": provider,
        "provider_response_id": response_id,
        "model_id": result.get("bedrock_model_id")
        or result.get("openai_model")
        or result.get("ai_model"),
        "transport": result.get("openai_transport_mode")
        or ("bedrock_converse" if provider == "bedrock" else None),
        "response_sha256": response_sha256,
        "input_tokens": result.get("openai_input_tokens")
        or result.get("bedrock_input_tokens"),
        "output_tokens": result.get("openai_output_tokens")
        or result.get("bedrock_output_tokens"),
        "total_tokens": total_tokens,
        "failback_chain": [
            key
            for key in (
                "bedrock_primary_used",
                "bedrock_fallback_used",
                "bedrock_failback_used",
                "openai_ws_http_fallback",
            )
            if result.get(key)
        ],
    }


def _pair_provider_endpoint_results(
    bedrock_results: dict[str, Any],
    openai_results: dict[str, Any],
) -> dict[str, Any]:
    paired: dict[str, Any] = {}
    for point in ("entry_price", "holding_flow"):
        bedrock_rows = [
            row
            for row in (bedrock_results.get(point, {}) or {}).get("results", [])
            if isinstance(row, dict) and row.get("status") == "ok"
        ]
        openai_rows_by_key = {
            _endpoint_result_key(row): row
            for row in (openai_results.get(point, {}) or {}).get("results", [])
            if isinstance(row, dict) and row.get("status") == "ok"
        }
        rows = []
        for bedrock_row in bedrock_rows:
            key = _endpoint_result_key(bedrock_row)
            openai_row = openai_rows_by_key.get(key)
            if not openai_row:
                continue
            pair = {
                "stock_code": bedrock_row.get("stock_code"),
                "stock_name": bedrock_row.get("stock_name"),
                "event_time": bedrock_row.get("event_time"),
                "bedrock_action": bedrock_row.get("provider_action"),
                "openai_action": openai_row.get("provider_action"),
                "action_diff": bool(
                    bedrock_row.get("provider_action")
                    != openai_row.get("provider_action")
                ),
                "bedrock_primary_used": bool(bedrock_row.get("bedrock_primary_used")),
                "bedrock_failback_used": bool(bedrock_row.get("bedrock_failback_used")),
            }
            if point == "entry_price":
                pair.update(
                    {
                        "bedrock_order_price": bedrock_row.get("provider_order_price"),
                        "openai_order_price": openai_row.get("provider_order_price"),
                        "order_price_diff": bool(
                            bedrock_row.get("provider_order_price")
                            and openai_row.get("provider_order_price")
                            and bedrock_row.get("provider_order_price")
                            != openai_row.get("provider_order_price")
                        ),
                    }
                )
            else:
                pair.update(
                    {
                        "bedrock_flow_state": bedrock_row.get("provider_flow_state"),
                        "openai_flow_state": openai_row.get("provider_flow_state"),
                        "flow_state_diff": bool(
                            bedrock_row.get("provider_flow_state")
                            and openai_row.get("provider_flow_state")
                            and bedrock_row.get("provider_flow_state")
                            != openai_row.get("provider_flow_state")
                        ),
                    }
                )
            rows.append(pair)
        paired[point] = {
            "results": rows,
            "summary": {
                "pair_count": len(rows),
                "action_diff_count": sum(1 for row in rows if row.get("action_diff")),
                "order_price_diff_count": sum(
                    1 for row in rows if row.get("order_price_diff")
                ),
                "flow_state_diff_count": sum(
                    1 for row in rows if row.get("flow_state_diff")
                ),
                "bedrock_primary_used_pair_count": sum(
                    1 for row in rows if row.get("bedrock_primary_used")
                ),
                "bedrock_failback_used_pair_count": sum(
                    1 for row in rows if row.get("bedrock_failback_used")
                ),
            },
        }
    return paired


def _run_endpoint_provider_compare(
    rows_by_point: dict[str, list[dict[str, Any]]],
    *,
    provider_mode: str,
    provider_label: str,
    model: str,
    effort: str,
    sample_limit: int,
    points: tuple[str, ...] = ("entry_price", "holding_flow"),
    fallback_endpoints: tuple[str, ...] = (),
) -> dict[str, Any]:
    from src.engine import ai_engine_openai as openai_module

    keys = _api_keys()
    if not keys:
        return {
            point: {
                "results": [
                    {"status": "skipped", "reason": "OPENAI_API_KEY not configured"}
                ],
                "summary": _endpoint_summary([{"status": "skipped"}]),
            }
            for point in points
        }

    point_results: dict[str, list[dict[str, Any]]] = {point: [] for point in points}
    valid_rows_by_point: dict[str, list[dict[str, Any]]] = {
        point: [] for point in points
    }
    for point in points:
        contract = AI_DECISION_POINT_CONTRACTS[point]
        valid_sample_limit = max(1, int(sample_limit or 1))
        source_rows = rows_by_point.get(point, [])
        for source_fields in source_rows:
            fields = dict(source_fields)
            exact_context_recovery: dict[str, Any] = {}
            if point == "holding_flow":
                fields, exact_context_recovery = _recover_holding_flow_exact_context(
                    fields
                )
            schema = _event_schema(fields)
            missing_features = [
                feature
                for feature in contract["required_features"]
                if (
                    point == "holding_flow"
                    and feature == "entry_time_context"
                    and exact_context_recovery.get("status") != "exact_recovered"
                )
                or (
                    not (point == "holding_flow" and feature == "entry_time_context")
                    and not _event_has_required_feature(fields, feature)
                )
            ]
            source_quality = (
                str(
                    fields.get("ai_input_source_quality_status")
                    or fields.get("holding_score_data_quality")
                    or fields.get("data_quality")
                    or fields.get("holding_context_source_quality_status")
                    or ""
                )
                .strip()
                .lower()
            )
            quote_stale_raw = fields.get("quote_stale")
            quote_stale_text = str(quote_stale_raw).strip().lower()
            quote_stale = _boolish(quote_stale_raw)
            quote_stale_known = isinstance(
                quote_stale_raw, bool
            ) or quote_stale_text in {
                "0",
                "1",
                "false",
                "true",
                "no",
                "yes",
                "n",
                "y",
                "off",
                "on",
            }
            quote_fresh = _boolish(fields.get("quote_fresh_for_entry"))
            quote_freshness_invalid = bool(
                point == "entry_price"
                and (quote_stale or (not quote_stale_known and not quote_fresh))
            )
            holding_flow_preflight_invalid = bool(
                point == "holding_flow"
                and (
                    source_quality not in {"fresh", "fresh_consistent"}
                    or not _truth_value(fields.get("ai_input_preflight_allowed"))
                    or not _truth_value(
                        fields.get("ai_input_preflight_position_reconciled")
                    )
                    or not _truth_value(
                        fields.get("ai_input_preflight_venue_consistent")
                    )
                )
            )
            if (
                schema not in contract["schemas"]
                or missing_features
                or quote_freshness_invalid
                or holding_flow_preflight_invalid
                or not source_quality
                or source_quality
                in {
                    "blocked",
                    "conflicted",
                    "stale",
                    "missing",
                    "insufficient",
                    "error",
                    "unknown",
                    "not_evaluated",
                }
            ):
                if len(point_results[point]) < valid_sample_limit:
                    point_results[point].append(
                        {
                            "status": "skipped",
                            "reason": (
                                "holding_flow_exact_context_unavailable"
                                if (
                                    point == "holding_flow"
                                    and exact_context_recovery.get("status")
                                    != "exact_recovered"
                                )
                                else "source_quality_contract_missing"
                            ),
                            "stock_code": fields.get("stock_code"),
                            "event_time": fields.get("event_time")
                            or fields.get("timestamp")
                            or fields.get("emitted_at"),
                            "schema": schema,
                            "missing_features": missing_features,
                            "source_quality": source_quality or "not_recorded",
                            "quote_stale": quote_stale,
                            "quote_freshness_invalid": quote_freshness_invalid,
                            "holding_flow_preflight_invalid": (
                                holding_flow_preflight_invalid
                            ),
                            "holding_flow_exact_context_recovery": (
                                exact_context_recovery
                            ),
                        }
                    )
                continue
            valid_rows_by_point[point].append(fields)
            if len(valid_rows_by_point[point]) >= valid_sample_limit:
                break
    if not any(valid_rows_by_point.values()):
        return {
            point: {
                "results": point_results[point],
                "summary": _endpoint_summary(point_results[point]),
            }
            for point in points
        }

    original_rules = openai_module.TRADING_RULES
    original_env = _temporary_env(_endpoint_provider_env(provider_mode))
    openai_module.TRADING_RULES = _RulesProxy(
        original_rules,
        GPT_REPORT_MODEL=model,
        OPENAI_TRANSPORT_MODE="http",
        OPENAI_REASONING_EFFORT=effort,
        OPENAI_ENTRY_PRICE_TIMEOUT_MS=(
            15000 if "entry_price" in fallback_endpoints else 10000
        ),
        OPENAI_HOLDING_FLOW_TIMEOUT_MS=10000,
        OPENAI_PRIMARY_BEDROCK_FALLBACK_ENDPOINTS=fallback_endpoints,
        OPENAI_PRIMARY_BEDROCK_FALLBACK_FAMILY="lite_v2",
        OPENAI_PRIMARY_BEDROCK_FALLBACK_PRIMARY_TIMEOUT_MS=7000,
        OPENAI_PRIMARY_BEDROCK_FALLBACK_TIMEOUT_MS=7000,
        OPENAI_RESPONSES_MAX_OUTPUT_TOKENS=512,
    )
    try:
        engine = openai_module.GPTSniperEngine(keys[:1], announce_startup=False)
        for point in points:
            for index, fields in enumerate(valid_rows_by_point[point], start=1):
                started = time.perf_counter()
                stock_code = str(
                    _first_nonempty(
                        fields, "stock_code", default=f"{point.upper()}_{index}"
                    )
                )
                stock_name = str(
                    _first_nonempty(fields, "stock_name", default=stock_code)
                )
                baseline_action = str(
                    _first_nonempty(
                        fields, "action", "ai_action", "flow_action", default="-"
                    )
                    or "-"
                ).upper()
                try:
                    if point == "entry_price":
                        entry_price_kwargs = {
                            "metadata_extra": {
                                "source_event_stage": "entry_context_intraday_probe_provider_compare",
                            }
                        }
                        if (
                            "candle_context"
                            in inspect.signature(
                                engine.evaluate_scalping_entry_price
                            ).parameters
                        ):
                            entry_price_kwargs["candle_context"] = (
                                _fields_to_entry_candle_context(fields)
                            )
                        result = engine.evaluate_scalping_entry_price(
                            stock_name,
                            stock_code,
                            _fields_to_ws_data(fields),
                            [],
                            [],
                            _fields_to_price_ctx(fields),
                            **entry_price_kwargs,
                        )
                        openai_action = str(result.get("action") or "-").upper()
                        provider_provenance = _provider_result_provenance(result)
                        baseline_order_price = _int_or_zero(
                            _first_nonempty(
                                fields,
                                "order_price",
                                "resolved_order_price",
                                "entry_price_input_resolved_order_price",
                                "candidate_price",
                                "original_order_price",
                                default=0,
                            )
                        )
                        provider_order_price = _int_or_zero(result.get("order_price"))
                        point_results[point].append(
                            {
                                "status": (
                                    "ok"
                                    if provider_provenance["provider"] != "none"
                                    else "error"
                                ),
                                "error_type": (
                                    None
                                    if provider_provenance["provider"] != "none"
                                    else "provider_none"
                                ),
                                "provider_label": provider_label,
                                "provider_mode": provider_mode,
                                "input_variant": "enriched_probe_context_v1",
                                "stock_code": stock_code,
                                "stock_name": stock_name,
                                "event_time": fields.get("event_time")
                                or fields.get("timestamp")
                                or fields.get("emitted_at"),
                                "model": model,
                                "effort": effort,
                                "elapsed_ms": int(
                                    (time.perf_counter() - started) * 1000
                                ),
                                "baseline_action": baseline_action,
                                "provider_action": openai_action,
                                "baseline_order_price": baseline_order_price,
                                "provider_order_price": provider_order_price,
                                "action_changed": bool(
                                    baseline_action != "-"
                                    and openai_action != baseline_action
                                ),
                                "order_price_changed": bool(
                                    baseline_order_price > 0
                                    and provider_order_price > 0
                                    and provider_order_price != baseline_order_price
                                ),
                                "confidence": result.get("confidence"),
                                "reason": str(result.get("reason") or "")[:160],
                                "transport_mode": result.get("openai_transport_mode"),
                                "bedrock_primary_used": bool(
                                    result.get("bedrock_primary_used", False)
                                ),
                                "bedrock_failback_used": bool(
                                    result.get("bedrock_failback_used", False)
                                ),
                                "bedrock_fallback_used": bool(
                                    result.get("bedrock_fallback_used", False)
                                ),
                                **provider_provenance,
                            }
                        )
                    elif point == "holding_score":
                        holding_context = _fields_to_holding_decision_context(fields)
                        probe_candles = _entry_context_to_recent_candles(
                            holding_context.get("candle") or {}
                        )
                        result = engine.evaluate_scalping_holding_score(
                            stock_name,
                            stock_code,
                            _fields_to_ws_data(fields),
                            [],
                            probe_candles,
                            _fields_to_position_ctx(fields),
                            holding_context=holding_context,
                            metadata_extra={
                                "source_event_stage": (
                                    "entry_context_intraday_probe_provider_compare"
                                ),
                            },
                        )
                        openai_action = str(result.get("action") or "-").upper()
                        provider_provenance = _provider_result_provenance(result)
                        point_results[point].append(
                            {
                                "status": (
                                    "ok"
                                    if provider_provenance["provider"] != "none"
                                    else "error"
                                ),
                                "error_type": (
                                    None
                                    if provider_provenance["provider"] != "none"
                                    else "provider_none"
                                ),
                                "provider_label": provider_label,
                                "provider_mode": provider_mode,
                                "input_variant": "enriched_probe_context_v1",
                                "stock_code": stock_code,
                                "stock_name": stock_name,
                                "event_time": fields.get("event_time")
                                or fields.get("timestamp")
                                or fields.get("emitted_at"),
                                "model": model,
                                "effort": effort,
                                "elapsed_ms": int(
                                    (time.perf_counter() - started) * 1000
                                ),
                                "baseline_action": baseline_action,
                                "provider_action": openai_action,
                                "action_changed": bool(
                                    baseline_action != "-"
                                    and openai_action != baseline_action
                                ),
                                "score": result.get("score"),
                                "confidence": result.get("confidence"),
                                "reason": str(result.get("reason") or "")[:160],
                                **provider_provenance,
                            }
                        )
                    else:
                        holding_context = _fields_to_holding_decision_context(fields)
                        probe_candles = _entry_context_to_recent_candles(
                            holding_context.get("candle") or {}
                        )
                        holding_flow_kwargs = {
                            "flow_history": [],
                            "decision_kind": "intraday_probe_compare",
                            "metadata_extra": {
                                "source_event_stage": "entry_context_intraday_probe_provider_compare",
                            },
                        }
                        if (
                            "holding_context"
                            in inspect.signature(
                                engine.evaluate_scalping_holding_flow
                            ).parameters
                        ):
                            holding_flow_kwargs["holding_context"] = holding_context
                        result = engine.evaluate_scalping_holding_flow(
                            stock_name,
                            stock_code,
                            _fields_to_ws_data(fields),
                            [],
                            probe_candles,
                            _fields_to_position_ctx(fields),
                            **holding_flow_kwargs,
                        )
                        openai_action = str(result.get("action") or "-").upper()
                        provider_provenance = _provider_result_provenance(result)
                        baseline_flow_state = str(
                            _first_nonempty(fields, "flow_state", default="-") or "-"
                        )
                        openai_flow_state = str(result.get("flow_state") or "-")
                        point_results[point].append(
                            {
                                "status": (
                                    "ok"
                                    if provider_provenance["provider"] != "none"
                                    else "error"
                                ),
                                "error_type": (
                                    None
                                    if provider_provenance["provider"] != "none"
                                    else "provider_none"
                                ),
                                "provider_label": provider_label,
                                "provider_mode": provider_mode,
                                "input_variant": "enriched_probe_context_v1",
                                "stock_code": stock_code,
                                "stock_name": stock_name,
                                "event_time": fields.get("event_time")
                                or fields.get("timestamp")
                                or fields.get("emitted_at"),
                                "model": model,
                                "effort": effort,
                                "elapsed_ms": int(
                                    (time.perf_counter() - started) * 1000
                                ),
                                "baseline_action": baseline_action,
                                "provider_action": openai_action,
                                "baseline_flow_state": baseline_flow_state,
                                "provider_flow_state": openai_flow_state,
                                "action_changed": bool(
                                    baseline_action != "-"
                                    and openai_action != baseline_action
                                ),
                                "flow_state_changed": bool(
                                    baseline_flow_state != "-"
                                    and openai_flow_state != "-"
                                    and openai_flow_state != baseline_flow_state
                                ),
                                "score": result.get("score"),
                                "next_review_sec": result.get("next_review_sec"),
                                "reason": str(result.get("reason") or "")[:160],
                                "transport_mode": result.get("openai_transport_mode"),
                                "bedrock_primary_used": bool(
                                    result.get("bedrock_primary_used", False)
                                ),
                                "bedrock_failback_used": bool(
                                    result.get("bedrock_failback_used", False)
                                ),
                                "bedrock_fallback_used": bool(
                                    result.get("bedrock_fallback_used", False)
                                ),
                                "holding_flow_exact_context_recovery": fields.get(
                                    "holding_flow_exact_context_recovery"
                                ),
                                **provider_provenance,
                            }
                        )
                except Exception as exc:
                    point_results[point].append(
                        {
                            "status": "error",
                            "provider_label": provider_label,
                            "provider_mode": provider_mode,
                            "input_variant": "enriched_probe_context_v1",
                            "stock_code": stock_code,
                            "stock_name": stock_name,
                            "event_time": fields.get("event_time")
                            or fields.get("timestamp")
                            or fields.get("emitted_at"),
                            "model": model,
                            "effort": effort,
                            "elapsed_ms": int((time.perf_counter() - started) * 1000),
                            "error_type": type(exc).__name__,
                            "reason": str(exc)[:160],
                            "holding_flow_exact_context_recovery": fields.get(
                                "holding_flow_exact_context_recovery"
                            ),
                        }
                    )
        return {
            point: {
                "results": point_results[point],
                "summary": _endpoint_summary(point_results[point]),
            }
            for point in points
        }
    finally:
        openai_module.TRADING_RULES = original_rules
        _restore_env(original_env)


def _call_provider_endpoint_compare(
    rows_by_point: dict[str, list[dict[str, Any]]],
    *,
    model: str,
    effort: str,
    sample_limit: int,
) -> dict[str, Any]:
    bedrock_primary = _run_endpoint_provider_compare(
        rows_by_point,
        provider_mode="bedrock_primary",
        provider_label="bedrock_primary_enriched",
        model=model,
        effort=effort,
        sample_limit=sample_limit,
    )
    openai_gpt54_mini = _run_endpoint_provider_compare(
        rows_by_point,
        provider_mode="openai_only",
        provider_label="openai_gpt54_mini_enriched",
        model=model,
        effort=effort,
        sample_limit=sample_limit,
    )
    entry_price_candidate_route = _run_endpoint_provider_compare(
        rows_by_point,
        provider_mode="openai_primary_bedrock_fallback",
        provider_label="openai_primary_nova_lite_v2_fallback",
        model=model,
        effort=effort,
        sample_limit=sample_limit,
        points=("entry_price",),
        fallback_endpoints=("entry_price",),
    )
    return {
        "input_variant": "enriched_probe_context_v1",
        "bedrock_primary": {
            "provider_env": _endpoint_provider_env("bedrock_primary"),
            "decision_points": bedrock_primary,
        },
        "openai_gpt54_mini": {
            "provider_env": _endpoint_provider_env("openai_only"),
            "decision_points": openai_gpt54_mini,
        },
        "entry_price_candidate_route": {
            "provider_env": _endpoint_provider_env("openai_primary_bedrock_fallback"),
            "decision_points": entry_price_candidate_route,
        },
        "pairwise": _pair_provider_endpoint_results(bedrock_primary, openai_gpt54_mini),
        "candidate_pairwise": _pair_provider_endpoint_results(
            bedrock_primary, entry_price_candidate_route
        ),
    }


def _call_openai_endpoint_compare(
    rows_by_point: dict[str, list[dict[str, Any]]],
    *,
    model: str,
    effort: str,
    sample_limit: int,
) -> dict[str, Any]:
    return _run_endpoint_provider_compare(
        rows_by_point,
        provider_mode="openai_only",
        provider_label="openai_gpt54_mini_enriched",
        model=model,
        effort=effort,
        sample_limit=sample_limit,
    )


def _load_context_candidates(target_date: str) -> Iterator[dict[str, Any]]:
    path = existing_or_gzip_path(
        CONTEXT_CANDIDATE_DIR / f"ai_canonical_context_candidates_{target_date}.jsonl"
    )
    if not path.exists():
        return
    for row in iter_jsonl(path):
        if isinstance(row, dict) and row.get("schema") == CONTEXT_CANDIDATE_SCHEMA:
            yield row


def _validation_only_source_context(
    context: dict[str, Any],
    *,
    promotion_disabled_only: bool = False,
) -> dict[str, Any]:
    source = json.loads(json.dumps(context, ensure_ascii=False, default=str))
    source["enabled"] = True
    if source.get("schema") == "holding_decision_context_v1":
        candle = source.get("candle") if isinstance(source.get("candle"), dict) else {}
        candle["multi_timeframe_ai_input_enabled"] = True
        source["candle"] = candle
        if promotion_disabled_only:
            quality = (
                dict(source.get("source_quality") or {})
                if isinstance(source.get("source_quality"), dict)
                else {}
            )
            quality["status"] = "fresh_consistent"
            quality["hold_defer_allowed"] = True
            quality["promotion_validation_transform"] = (
                "feature_disabled_to_enabled_no_source_blockers"
            )
            source["source_quality"] = quality
    else:
        source["multi_timeframe_ai_input_enabled"] = True
    source["validation_only_contract"] = dict(PREPROMOTION_EXACT_CAPTURE_CONTRACT)
    return source


def run_prepromotion_exact_context_capture(
    target_date: str,
    *,
    symbols: list[str] | None = None,
    sample_limit: int = 1,
    max_candidate_age_sec: float = 120.0,
) -> dict[str, Any]:
    """Call real endpoints with captured context; never return into runtime state."""

    from src.engine import ai_engine_openai as openai_module

    now = datetime.now().astimezone()
    symbol_filter = {str(item).strip() for item in (symbols or []) if str(item).strip()}
    latest: dict[tuple[str, str], dict[str, Any]] = {}
    exclusions: Counter[str] = Counter()
    for row in _load_context_candidates(target_date):
        symbol = str(row.get("symbol") or "").strip()
        endpoint = str(row.get("endpoint") or "").strip()
        if symbol_filter and symbol not in symbol_filter:
            continue
        if row.get("validation_only_eligible") is not True:
            exclusions["candidate_ineligible"] += 1
            continue
        try:
            captured_at = datetime.fromisoformat(str(row.get("captured_at") or ""))
            if captured_at.tzinfo is None:
                captured_at = captured_at.astimezone()
            age_sec = (now - captured_at.astimezone()).total_seconds()
        except (TypeError, ValueError):
            exclusions["captured_at_invalid"] += 1
            continue
        if age_sec < -5.0:
            exclusions["candidate_future_timestamp"] += 1
            continue
        if age_sec > max(1.0, float(max_candidate_age_sec)):
            exclusions["candidate_stale"] += 1
            continue
        key = (endpoint, symbol)
        if key not in latest or str(row.get("captured_at")) > str(
            latest[key].get("captured_at")
        ):
            latest[key] = row
    per_endpoint: Counter[str] = Counter()
    selected = []
    for key in sorted(latest):
        endpoint = key[0]
        if per_endpoint[endpoint] >= max(1, int(sample_limit)):
            continue
        selected.append(latest[key])
        per_endpoint[endpoint] += 1
    if not selected:
        return {
            "status": "no_fresh_candidates",
            "results": [],
            "endpoint_counts": {},
            "excluded_counts": dict(exclusions),
            **PREPROMOTION_EXACT_CAPTURE_CONTRACT,
        }
    keys = _api_keys()
    if not keys:
        return {
            "status": "provider_unavailable",
            "reason": "OPENAI_API_KEY_not_configured",
            "results": [],
            "endpoint_counts": {},
            "excluded_counts": dict(exclusions),
            **PREPROMOTION_EXACT_CAPTURE_CONTRACT,
        }
    engine = openai_module.GPTSniperEngine(keys[:1], announce_startup=False)
    results: list[dict[str, Any]] = []
    for candidate in selected:
        endpoint = str(candidate.get("endpoint") or "")
        symbol = str(candidate.get("symbol") or "-")
        source = candidate.get("source_context")
        source = source if isinstance(source, dict) else {}
        context = _validation_only_source_context(
            source,
            promotion_disabled_only=bool(candidate.get("promotion_disabled_only")),
        )
        call_inputs = candidate.get("call_inputs")
        call_inputs = call_inputs if isinstance(call_inputs, dict) else {}
        call_contract = candidate.get("call_inputs_contract")
        call_contract = call_contract if isinstance(call_contract, dict) else {}
        if not call_inputs or call_contract.get("ready") is not True:
            exclusions["exact_call_inputs_missing"] += 1
            continue
        metadata = {
            "source_event_stage": "prepromotion_validation_only_exact_capture",
            "validation_only_context_candidate_sha256": candidate.get(
                "candidate_sha256"
            ),
            **PREPROMOTION_EXACT_CAPTURE_CONTRACT,
        }
        started = time.perf_counter()
        try:
            if endpoint == "analyze_target":
                result = engine.analyze_target(
                    call_inputs["target_name"],
                    call_inputs["ws_data"],
                    call_inputs["recent_ticks"],
                    call_inputs["recent_candles"],
                    strategy=call_inputs["strategy"],
                    program_net_qty=call_inputs["program_net_qty"],
                    cache_profile=call_inputs["cache_profile"],
                    prompt_profile=call_inputs["prompt_profile"],
                    metadata_extra=metadata,
                    candle_context=context,
                )
            elif endpoint == "entry_price":
                result = engine.evaluate_scalping_entry_price(
                    call_inputs["stock_name"],
                    call_inputs["stock_code"],
                    call_inputs["ws_data"],
                    call_inputs["recent_ticks"],
                    call_inputs["recent_candles"],
                    call_inputs["price_ctx"],
                    metadata_extra=metadata,
                    candle_context=context,
                )
            elif endpoint == "holding_score":
                result = engine.evaluate_scalping_holding_score(
                    call_inputs["stock_name"],
                    call_inputs["stock_code"],
                    call_inputs["ws_data"],
                    call_inputs["recent_ticks"],
                    call_inputs["recent_candles"],
                    call_inputs["position_ctx"],
                    metadata_extra=metadata,
                    holding_context=context,
                )
            elif endpoint == "holding_flow":
                result = engine.evaluate_scalping_holding_flow(
                    call_inputs["stock_name"],
                    call_inputs["stock_code"],
                    call_inputs["ws_data"],
                    call_inputs["recent_ticks"],
                    call_inputs["recent_candles"],
                    call_inputs["position_ctx"],
                    flow_history=call_inputs["flow_history"],
                    decision_kind=call_inputs["decision_kind"],
                    metadata_extra=metadata,
                    holding_context=context,
                )
            else:
                exclusions["endpoint_not_supported"] += 1
                continue
            provenance = _provider_result_provenance(
                result if isinstance(result, dict) else {}
            )
            results.append(
                {
                    "endpoint": endpoint,
                    "symbol": symbol,
                    "candidate_sha256": candidate.get("candidate_sha256"),
                    "status": (
                        "called"
                        if provenance.get("provider") != "none"
                        else "provider_none"
                    ),
                    "elapsed_ms": int((time.perf_counter() - started) * 1000),
                    **provenance,
                }
            )
        except Exception as exc:
            results.append(
                {
                    "endpoint": endpoint,
                    "symbol": symbol,
                    "candidate_sha256": candidate.get("candidate_sha256"),
                    "status": "call_failed",
                    "error_type": type(exc).__name__,
                }
            )
    status = (
        "exact_provider_calls_captured"
        if results and all(row.get("status") == "called" for row in results)
        else ("no_fresh_candidates" if not results else "provider_call_gap")
    )
    return {
        "status": status,
        "results": results,
        "endpoint_counts": dict(
            Counter(
                str(row.get("endpoint"))
                for row in results
                if row.get("status") == "called"
            )
        ),
        "excluded_counts": dict(exclusions),
        **PREPROMOTION_EXACT_CAPTURE_CONTRACT,
    }


def build_probe_report(
    target_date: str,
    *,
    build_adm: bool = False,
    sample_limit: int = 12,
    live_openai: bool = False,
    model: str = "gpt-5-nano",
    effort: str = "minimal",
    compare_openai_endpoints: bool = False,
    endpoint_compare_model: str = "gpt-5.4-mini",
    endpoint_compare_effort: str = "low",
    live_holding_score: bool = False,
    probe_symbols: list[str] | None = None,
    capture_prepromotion_exact: bool = False,
    context_candidate_max_age_sec: float = 120.0,
) -> dict[str, Any]:
    adm_report = _read_adm_report(target_date, build_adm=build_adm)
    rows = adm_report.get("rows") if isinstance(adm_report.get("rows"), list) else []
    pipeline_report = _read_pipeline_events(target_date)
    pipeline_rows = (
        pipeline_report.get("rows")
        if isinstance(pipeline_report.get("rows"), list)
        else []
    )
    clean_pipeline_report = _read_clean_baseline_pipeline_events(target_date)
    clean_pipeline_rows = (
        clean_pipeline_report.get("rows")
        if isinstance(clean_pipeline_report.get("rows"), list)
        else []
    )
    symbol_filter = {
        str(item).strip() for item in (probe_symbols or []) if str(item).strip()
    }
    filtered_rows = (
        [
            row
            for row in rows
            if str(row.get("stock_code") or "").strip() in symbol_filter
        ]
        if symbol_filter
        else rows
    )
    candidates = _candidate_rows(filtered_rows, sample_limit)
    live_results = (
        _call_openai(candidates, model=model, effort=effort) if live_openai else []
    )
    rows_by_point = _decision_point_rows(rows, pipeline_rows)
    if symbol_filter:
        rows_by_point = {
            point: [
                row
                for row in point_rows
                if str(row.get("stock_code") or "").strip() in symbol_filter
            ]
            for point, point_rows in rows_by_point.items()
        }
    holding_score_compare = (
        _run_endpoint_provider_compare(
            rows_by_point,
            provider_mode="openai_only",
            provider_label="openai_holding_score_forensics",
            model=model,
            effort=effort,
            sample_limit=sample_limit,
            points=("holding_score",),
        )
        if live_holding_score
        else {}
    )
    provider_endpoint_compare = (
        _call_provider_endpoint_compare(
            rows_by_point,
            model=endpoint_compare_model,
            effort=endpoint_compare_effort,
            sample_limit=sample_limit,
        )
        if compare_openai_endpoints
        else {}
    )
    openai_endpoint_compare = (
        provider_endpoint_compare.get("openai_gpt54_mini", {}).get(
            "decision_points", {}
        )
        if compare_openai_endpoints
        else {}
    )
    decision_results = [
        item
        for item in live_results
        if item.get("status") == "accepted"
        and str(item.get("action") or "") in {"BUY", "WAIT", "DROP"}
    ]
    prepromotion_exact_capture = (
        run_prepromotion_exact_context_capture(
            target_date,
            symbols=probe_symbols,
            sample_limit=max(1, min(sample_limit, 4)),
            max_candidate_age_sec=context_candidate_max_age_sec,
        )
        if capture_prepromotion_exact
        else {
            "status": "not_requested",
            "results": [],
            **PREPROMOTION_EXACT_CAPTURE_CONTRACT,
        }
    )
    return {
        "report_type": "entry_context_intraday_probe",
        "date": target_date,
        "status": "ok" if candidates else "no_probe_rows",
        "runtime_effect": False,
        "decision_authority": "forensics_only_no_runtime_change",
        "allowed_runtime_apply": False,
        "forbidden_uses": (
            "runtime_threshold_apply/order_submit/provider_route_change/bot_restart/"
            "broker_guard_bypass/live_auto_promotion"
        ),
        "source": {
            "adm_status": adm_report.get("status"),
            "adm_artifact": adm_report.get("artifact")
            or str(adm_mod.report_paths(target_date)[0]),
            "build_adm": bool(build_adm),
            "pipeline_events_status": pipeline_report.get("status"),
            "pipeline_events_artifact": pipeline_report.get("artifact"),
            "pipeline_events_parse_error_count": pipeline_report.get(
                "parse_error_count", 0
            ),
        },
        "prepromotion_exact_context_capture": prepromotion_exact_capture,
        "coverage": _coverage(candidates),
        "venue_preflight_matrix": _venue_preflight_matrix(clean_pipeline_rows),
        "venue_preflight_source": {
            key: clean_pipeline_report.get(key)
            for key in (
                "baseline_date",
                "exact_provenance_start_date",
                "target_date",
                "artifact_count",
                "parse_error_count",
            )
        },
        "ai_decision_contract_probe": _decision_contract_probe(
            rows,
            pipeline_rows,
            sample_limit=sample_limit,
        ),
        "sample_rows": [
            {
                "candidate_id": row.get("candidate_id"),
                "record_id": row.get("record_id"),
                "stock_code": row.get("stock_code"),
                "stock_name": row.get("stock_name"),
                "event_time": row.get("event_time"),
                "chosen_action": row.get("chosen_action"),
                "ai_action": row.get("ai_action"),
                "ai_score": row.get("ai_score"),
                "features": _probe_payload(row, index + 1)["entry_context"],
            }
            for index, row in enumerate(candidates)
        ],
        "live_openai": {
            "enabled": bool(live_openai),
            "model": model if live_openai else None,
            "effort": effort if live_openai else None,
            "results": live_results,
            "summary": {
                "row_count": len(decision_results),
                "skipped_count": len(live_results) - len(decision_results),
                "schema_semantic_rejected_count": sum(
                    1
                    for item in live_results
                    if item.get("status") == "schema_semantic_rejected"
                ),
                "provider_none_count": sum(
                    1 for item in live_results if item.get("provider") == "none"
                ),
                "buy_count": sum(
                    1 for item in decision_results if item.get("action") == "BUY"
                ),
                "wait_count": sum(
                    1 for item in decision_results if item.get("action") == "WAIT"
                ),
                "drop_count": sum(
                    1 for item in decision_results if item.get("action") == "DROP"
                ),
                "action_score_mismatch_count": sum(
                    1 for item in decision_results if item.get("action_score_mismatch")
                ),
                "insufficient_context_count": sum(
                    1
                    for item in decision_results
                    if item.get("issue") == "insufficient_context"
                ),
            },
        },
        "live_holding_score": {
            "enabled": bool(live_holding_score),
            "runtime_effect": False,
            "decision_authority": "forensics_only_no_runtime_change",
            "result": holding_score_compare,
        },
        "openai_endpoint_compare": {
            "enabled": bool(compare_openai_endpoints),
            "model": endpoint_compare_model if compare_openai_endpoints else None,
            "effort": endpoint_compare_effort if compare_openai_endpoints else None,
            "provider_override": (
                {
                    "KORSTOCKSCAN_BEDROCK_ENTRY_PRICE_ROUTE_MODE": "off",
                    "KORSTOCKSCAN_BEDROCK_NOVA_LITE_ROUTE_MODE": "off",
                    "runtime_effect": False,
                }
                if compare_openai_endpoints
                else {}
            ),
            "decision_points": openai_endpoint_compare,
        },
        "provider_endpoint_compare": {
            "enabled": bool(compare_openai_endpoints),
            "model": endpoint_compare_model if compare_openai_endpoints else None,
            "effort": endpoint_compare_effort if compare_openai_endpoints else None,
            "runtime_effect": False,
            "decision_authority": "forensics_only_no_runtime_change",
            "forbidden_uses": (
                "runtime_threshold_apply/order_submit/provider_route_change/bot_restart/"
                "broker_guard_bypass/live_auto_promotion"
            ),
            "result": provider_endpoint_compare,
        },
    }


def _write_report(report: dict[str, Any]) -> Path:
    PROBE_REPORT_DIR.mkdir(parents=True, exist_ok=True)
    target_date = str(report.get("date") or _today())
    path = PROBE_REPORT_DIR / f"entry_context_intraday_probe_{target_date}.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Probe intraday scalping entry context quality."
    )
    parser.add_argument("--date", dest="target_date", default=_today())
    parser.add_argument(
        "--build-adm",
        action="store_true",
        help="Build same-day scalp entry ADM before probing.",
    )
    parser.add_argument("--sample-limit", type=int, default=12)
    parser.add_argument(
        "--live-openai",
        action="store_true",
        help="Run live OpenAI for selected probe rows.",
    )
    parser.add_argument("--model", default="gpt-5-nano")
    parser.add_argument("--effort", default="minimal")
    parser.add_argument(
        "--symbols",
        default="",
        help="Optional comma-separated forensic sample symbols.",
    )
    parser.add_argument(
        "--live-holding-score",
        action="store_true",
        help="Run one or more observation-only OpenAI holding_score calls.",
    )
    parser.add_argument(
        "--compare-openai-endpoints",
        action="store_true",
        help="Compare entry_price and holding_flow endpoint rows with Bedrock primary and OpenAI.",
    )
    parser.add_argument(
        "--compare-provider-endpoints",
        action="store_true",
        help="Alias for --compare-openai-endpoints with clearer provider-comparison naming.",
    )
    parser.add_argument(
        "--capture-prepromotion-exact",
        action="store_true",
        help=(
            "Call fresh canonical-context candidates through their real endpoint "
            "for validation only; results never enter runtime decisions."
        ),
    )
    parser.add_argument(
        "--context-candidate-max-age-sec",
        type=float,
        default=120.0,
        help="Reject validation-only context candidates older than this many seconds.",
    )
    parser.add_argument("--endpoint-compare-model", default="gpt-5.4-mini")
    parser.add_argument("--endpoint-compare-effort", default="low")
    parser.add_argument(
        "--write", action="store_true", help="Write probe report artifact."
    )
    args = parser.parse_args(argv)

    report = build_probe_report(
        args.target_date,
        build_adm=args.build_adm,
        sample_limit=args.sample_limit,
        live_openai=args.live_openai,
        model=args.model,
        effort=args.effort,
        compare_openai_endpoints=bool(
            args.compare_openai_endpoints or args.compare_provider_endpoints
        ),
        endpoint_compare_model=args.endpoint_compare_model,
        endpoint_compare_effort=args.endpoint_compare_effort,
        live_holding_score=args.live_holding_score,
        probe_symbols=[
            item.strip() for item in args.symbols.split(",") if item.strip()
        ],
        capture_prepromotion_exact=args.capture_prepromotion_exact,
        context_candidate_max_age_sec=args.context_candidate_max_age_sec,
    )
    if args.write:
        report["artifact"] = str(_write_report(report))
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
