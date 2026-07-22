"""Report-only intraday probe for scalping entry AI context quality."""

from __future__ import annotations

import argparse
import json
import os
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from src.engine import scalp_entry_action_decision_matrix as adm_mod
from src.engine.sniper_config import CONF

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data"
REPORT_DIR = DATA_DIR / "report"
PROBE_REPORT_DIR = REPORT_DIR / "entry_context_intraday_probe"
PIPELINE_EVENTS_DIR = DATA_DIR / "pipeline_events"

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


def _event_fields(row: dict[str, Any]) -> dict[str, Any]:
    fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
    merged = dict(fields)
    for key in (
        "stage",
        "event",
        "stock_code",
        "stock_name",
        "timestamp",
        "event_time",
        "emitted_at",
    ):
        if key in row and key not in merged:
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
            "score is 70-100. issue must be bad_entry, stop_loss_timing, insufficient_context, or acceptable_risk. "
            "missing_features must be an array of pre-entry market/source fields only. reason must be Korean "
            "and at most 6 words. Do not recommend broker, threshold, bot, provider, or cap changes."
        )
        results = []
        for index, row in enumerate(rows, start=1):
            started = time.perf_counter()
            result = engine._call_openai_safe(
                prompt,
                json.dumps(
                    _probe_payload(row, index),
                    ensure_ascii=False,
                    separators=(",", ":"),
                ),
                require_json=True,
                context_name=f"INTRADAY_ENTRY_CONTEXT_PROBE:{model}:{effort}:{row.get('stock_code')}",
                model_override=model,
                endpoint_name="analyze_target",
                symbol=str(row.get("stock_code") or "INTRADAY_PROBE"),
                cache_key=(
                    f"intraday-entry-context-probe:{model}:{effort}:"
                    f"{row.get('candidate_id')}:{row.get('event_time')}"
                ),
            )
            score = int(float(result.get("score", 0) or 0))
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
        "curr": curr,
        "current_price": curr,
        "v_pw": _first_nonempty(
            fields, "v_pw", "latest_strength", "execution_strength", default=0
        ),
        "buy_ratio": _first_nonempty(
            fields, "buy_ratio", "buy_pressure_10t", default=0
        ),
        "buy_exec_volume": _first_nonempty(fields, "buy_exec_volume", default=0),
        "sell_exec_volume": _first_nonempty(fields, "sell_exec_volume", default=0),
        "ask_tot": _first_nonempty(fields, "ask_tot", "top3_ask_notional", default=0),
        "bid_tot": _first_nonempty(fields, "bid_tot", "top3_bid_notional", default=0),
        "quote_age_ms": _first_nonempty(fields, "quote_age_ms", default=0),
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


def _fields_to_position_ctx(fields: dict[str, Any]) -> dict[str, Any]:
    profit_rate = _float_or_zero(
        _first_nonempty(fields, "profit_rate", "pnl_pct", default=0.0)
    )
    peak_profit = _float_or_zero(
        _first_nonempty(fields, "peak_profit", default=profit_rate)
    )
    return {
        "record_id": _first_nonempty(fields, "record_id", default=None),
        "buy_price": _first_nonempty(
            fields, "buy_price", "avg_price", "average_entry_price", default=0
        ),
        "curr_price": _first_nonempty(fields, "curr", "current_price", default=0),
        "profit_rate": profit_rate,
        "peak_profit": peak_profit,
        "drawdown": max(0.0, peak_profit - profit_rate),
        "held_sec": _int_or_zero(_first_nonempty(fields, "held_sec", default=0)),
        "current_ai_score": _first_nonempty(
            fields, "current_ai_score", "score", "ai_score", default=0
        ),
        "exit_rule": _first_nonempty(
            fields, "exit_rule", "candidate_exit_rule", default="-"
        ),
        "flow_state": _first_nonempty(fields, "flow_state", default="-"),
        "reason": _first_nonempty(fields, "reason", default="-"),
        "entry_time_context": {
            "entry_context_quality": _first_nonempty(
                fields, "entry_context_quality", default=None
            ),
            "entry_liquidity_score": _first_nonempty(
                fields, "entry_liquidity_score", default=None
            ),
            "fillability_score": _first_nonempty(
                fields, "fillability_score", default=None
            ),
            "order_flow_pressure_score": _first_nonempty(
                fields, "order_flow_pressure_score", default=None
            ),
            "entry_momentum_score": _first_nonempty(
                fields, "entry_momentum_score", default=None
            ),
        },
    }


def _endpoint_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    ok_rows = [row for row in results if row.get("status") == "ok"]
    return {
        "row_count": len(ok_rows),
        "skipped_count": sum(1 for row in results if row.get("status") == "skipped"),
        "error_count": sum(1 for row in results if row.get("status") == "error"),
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
        source_rows = rows_by_point.get(point, [])[: max(1, int(sample_limit or 1))]
        for fields in source_rows:
            schema = _event_schema(fields)
            missing_features = [
                feature
                for feature in contract["required_features"]
                if not _event_has_required_feature(fields, feature)
            ]
            source_quality = (
                str(fields.get("ai_input_source_quality_status") or "").strip().lower()
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
            if (
                schema not in contract["schemas"]
                or missing_features
                or quote_freshness_invalid
                or not source_quality
                or source_quality
                in {
                    "stale",
                    "missing",
                    "insufficient",
                    "error",
                    "unknown",
                    "not_evaluated",
                }
            ):
                point_results[point].append(
                    {
                        "status": "skipped",
                        "reason": "source_quality_contract_missing",
                        "stock_code": fields.get("stock_code"),
                        "event_time": fields.get("event_time")
                        or fields.get("timestamp")
                        or fields.get("emitted_at"),
                        "schema": schema,
                        "missing_features": missing_features,
                        "source_quality": source_quality or "not_recorded",
                        "quote_stale": quote_stale,
                        "quote_freshness_invalid": quote_freshness_invalid,
                    }
                )
                continue
            valid_rows_by_point[point].append(fields)
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
                        result = engine.evaluate_scalping_entry_price(
                            stock_name,
                            stock_code,
                            _fields_to_ws_data(fields),
                            [],
                            [],
                            _fields_to_price_ctx(fields),
                            metadata_extra={
                                "source_event_stage": "entry_context_intraday_probe_provider_compare",
                            },
                        )
                        openai_action = str(result.get("action") or "-").upper()
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
                                "status": "ok",
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
                            }
                        )
                    else:
                        result = engine.evaluate_scalping_holding_flow(
                            stock_name,
                            stock_code,
                            _fields_to_ws_data(fields),
                            [],
                            [],
                            _fields_to_position_ctx(fields),
                            flow_history=[],
                            decision_kind="intraday_probe_compare",
                            metadata_extra={
                                "source_event_stage": "entry_context_intraday_probe_provider_compare",
                            },
                        )
                        openai_action = str(result.get("action") or "-").upper()
                        baseline_flow_state = str(
                            _first_nonempty(fields, "flow_state", default="-") or "-"
                        )
                        openai_flow_state = str(result.get("flow_state") or "-")
                        point_results[point].append(
                            {
                                "status": "ok",
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
) -> dict[str, Any]:
    adm_report = _read_adm_report(target_date, build_adm=build_adm)
    rows = adm_report.get("rows") if isinstance(adm_report.get("rows"), list) else []
    pipeline_report = _read_pipeline_events(target_date)
    pipeline_rows = (
        pipeline_report.get("rows")
        if isinstance(pipeline_report.get("rows"), list)
        else []
    )
    candidates = _candidate_rows(rows, sample_limit)
    live_results = (
        _call_openai(candidates, model=model, effort=effort) if live_openai else []
    )
    rows_by_point = _decision_point_rows(rows, pipeline_rows)
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
        if str(item.get("action") or "") in {"BUY", "WAIT", "DROP"}
    ]
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
        "coverage": _coverage(candidates),
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
        "--compare-openai-endpoints",
        action="store_true",
        help="Compare entry_price and holding_flow endpoint rows with Bedrock primary and OpenAI.",
    )
    parser.add_argument(
        "--compare-provider-endpoints",
        action="store_true",
        help="Alias for --compare-openai-endpoints with clearer provider-comparison naming.",
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
    )
    if args.write:
        report["artifact"] = str(_write_report(report))
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
