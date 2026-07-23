"""Append-only AI decision trace and pending outcome-label instrumentation.

This module has no trading authority.  Failures are intentionally isolated from the
provider and runtime decision paths.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from src.utils.constants import DATA_DIR
from src.utils.logger import log_error

TRACE_SCHEMA = "ai_decision_trace_v1"
PAYLOAD_SCHEMA = "ai_decision_payload_v1"
PROMPT_SCHEMA = "ai_decision_prompt_v1"
OUTCOME_SCHEMA = "ai_decision_outcome_label_v1"
OUTCOME_HORIZONS_MIN = (1, 3, 5, 10, 20, 30, 60)

OBSERVATION_CONTRACT = {
    "metric_role": "ai_decision_quality_observation",
    "decision_authority": "offline_replay_and_attribution_only",
    "window_policy": "clean_baseline_exact_provenance_stage_venue_separated",
    "sample_floor": "row_level_not_applicable_aggregation_floor_required",
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "source_quality_gate": "exact_snapshot_and_mature_forward_window",
    "runtime_effect": False,
    "allowed_runtime_apply": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
    "forbidden_uses": (
        "standalone_live_prompt_promotion|provider_change|threshold_relaxation|"
        "order_or_quantity_change|broker_guard_bypass|hard_safety_bypass|"
        "counterfactual_realized_pnl_merge"
    ),
}

_WRITE_LOCK = threading.RLock()
_SEEN_PAYLOAD_HASHES: dict[str, set[str]] = {}
_SEEN_PROMPT_HASHES: dict[str, set[str]] = {}
_SEEN_TRACE_IDS: dict[str, set[str]] = {}
_SENSITIVE_KEY = re.compile(
    r"(?:api[_-]?key|authorization|access[_-]?token|secret|password|"
    r"account[_-]?(?:no|number)|acct[_-]?(?:no|number))",
    re.IGNORECASE,
)
_BEARER_VALUE = re.compile(r"^\s*bearer\s+\S+", re.IGNORECASE)
_STAGE_BY_PROMPT_TYPE = {
    "scalping_entry": "entry_screen",
    "scalping_shared": "entry_screen",
    "entry_price": "entry_price",
    "scalping_holding_score": "holding_score",
    "holding_exit_flow": "holding_flow",
    "scalping_holding": "holding_flow",
    "scalping_overnight": "overnight",
    "realtime_gatekeeper": "gatekeeper",
}
_SCALPING_ENDPOINTS = {
    "analyze_target",
    "entry_price",
    "holding_score",
    "holding_flow",
    "overnight",
    "realtime_report",
}


def trace_enabled() -> bool:
    default = "false" if os.getenv("PYTEST_CURRENT_TEST") else "true"
    return str(
        os.getenv("KORSTOCKSCAN_AI_DECISION_TRACE_ENABLED", default)
    ).strip().lower() in {"1", "true", "yes", "y", "on"}


def _now() -> datetime:
    return datetime.now().astimezone()


def _date_text(value: datetime | None = None) -> str:
    return (value or _now()).strftime("%Y-%m-%d")


def _trace_path(target_date: str) -> Path:
    return DATA_DIR / "ai_decision_trace" / f"ai_decision_trace_{target_date}.jsonl"


def _payload_path(target_date: str) -> Path:
    return (
        DATA_DIR / "ai_decision_payloads" / f"ai_decision_payloads_{target_date}.jsonl"
    )


def _prompt_path(target_date: str) -> Path:
    return DATA_DIR / "ai_decision_prompts" / f"ai_decision_prompts_{target_date}.jsonl"


def _outcome_path(target_date: str) -> Path:
    return (
        DATA_DIR / "ai_decision_outcomes" / f"ai_decision_outcomes_{target_date}.jsonl"
    )


def _json_bytes(value: Any) -> bytes:
    if isinstance(value, bytes):
        return value
    if isinstance(value, str):
        return value.encode("utf-8")
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str
    ).encode("utf-8")


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = (
        json.dumps(payload, ensure_ascii=False, separators=(",", ":"), default=str)
        + "\n"
    )
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line)


def _load_seen(path: Path, field: str) -> set[str]:
    values: set[str] = set()
    if not path.exists():
        return values
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                try:
                    row = json.loads(line)
                except Exception:
                    continue
                value = str((row or {}).get(field) or "").strip()
                if value:
                    values.add(value)
    except Exception:
        return values
    return values


def _sanitize(value: Any, *, key: str = "") -> tuple[Any, bool]:
    if _SENSITIVE_KEY.search(str(key or "")):
        return "[REDACTED]", True
    if isinstance(value, dict):
        cleaned: dict[str, Any] = {}
        redacted = False
        for child_key, child_value in value.items():
            safe_value, child_redacted = _sanitize(child_value, key=str(child_key))
            cleaned[str(child_key)] = safe_value
            redacted = redacted or child_redacted
        return cleaned, redacted
    if isinstance(value, (list, tuple)):
        cleaned_list = []
        redacted = False
        for child_value in value:
            safe_value, child_redacted = _sanitize(child_value, key=key)
            cleaned_list.append(safe_value)
            redacted = redacted or child_redacted
        return cleaned_list, redacted
    if isinstance(value, str) and _BEARER_VALUE.match(value):
        return "[REDACTED]", True
    return value, False


def _parse_user_input(user_input: Any) -> tuple[str, Any]:
    if not isinstance(user_input, str):
        return "structured", user_input
    stripped = user_input.strip()
    if stripped.startswith(("{", "[")):
        try:
            return "json_text", json.loads(stripped)
        except Exception:
            pass
    return "plain_text", user_input


def _walk(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def _first_value(value: Any, keys: tuple[str, ...]) -> Any:
    for row in _walk(value):
        for key in keys:
            if key in row and row.get(key) not in (None, "", "-", "None", "null"):
                return row.get(key)
    return None


def _safe_number(value: Any) -> int | float | None:
    if value in (None, "", "-", "None", "null"):
        return None
    try:
        number = float(value)
    except Exception:
        return None
    return int(number) if number.is_integer() else number


def _normalize_stock_code(value: Any) -> str:
    text = str(value or "").strip().upper()
    match = re.search(r"(?<!\d)(\d{6})(?!\d)", text)
    return match.group(1) if match else "-"


def _request_context(user_input: Any, metadata: dict[str, Any]) -> dict[str, Any]:
    _, parsed = _parse_user_input(user_input)
    context = {
        "stock_code": _first_value(parsed, ("stock_code", "code", "종목코드"))
        or metadata.get("stock_code"),
        "record_id": _first_value(parsed, ("record_id", "recommendation_id"))
        or metadata.get("record_id"),
        "recommendation_id": _first_value(parsed, ("recommendation_id",)),
        "probe_bundle_id": _first_value(
            parsed,
            (
                "probe_bundle_id",
                "entry_split_probe_bundle_id",
                "entry_split_order_probe_bundle_id",
            ),
        )
        or metadata.get("probe_bundle_id"),
        "position_cycle_id": _first_value(
            parsed,
            (
                "position_cycle_id",
                "early_volatility_tp_position_cycle_id",
            ),
        )
        or metadata.get("position_cycle_id"),
        "broker_order_no": _first_value(
            parsed, ("broker_order_no", "order_no", "ord_no")
        ),
        "snapshot_id": _first_value(parsed, ("snapshot_id",)),
        "effective_venue": _first_value(parsed, ("effective_venue",)),
        "session_bucket": _first_value(
            parsed, ("session_bucket", "market_session_bucket")
        ),
        "broker_route": _first_value(parsed, ("broker_route",)),
        "market_data_route": _first_value(parsed, ("market_data_route",)),
        "reference_price": _safe_number(
            _first_value(
                parsed,
                (
                    "resolved_order_price",
                    "executable_ask",
                    "best_ask",
                    "current_price",
                    "curr_price",
                    "price",
                ),
            )
        ),
        "best_bid": _safe_number(_first_value(parsed, ("best_bid",))),
        "best_ask": _safe_number(_first_value(parsed, ("best_ask", "executable_ask"))),
        "target_price": _safe_number(_first_value(parsed, ("target_price",))),
        "adverse_price": _safe_number(
            _first_value(parsed, ("adverse_price", "stop_price"))
        ),
        "target_pct": _safe_number(_first_value(parsed, ("target_pct",))),
        "adverse_pct": _safe_number(_first_value(parsed, ("adverse_pct", "stop_pct"))),
    }
    return context


def capture_ai_request(
    *,
    prompt: Any,
    user_input: Any,
    endpoint_name: str,
    symbol: str,
    request_id: str,
    model: str,
    schema_name: str | None,
    require_json: bool,
    temperature: float | None = None,
    max_output_tokens: int | None = None,
    reasoning_effort: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Persist a sanitized replay payload and return fields propagated to the result."""
    if not trace_enabled():
        return {}
    try:
        if str(endpoint_name or "") not in _SCALPING_ENDPOINTS:
            return {}
        strategy = str((metadata or {}).get("ai_trace_strategy") or "").upper()
        if strategy in {"KOSPI_ML", "KOSDAQ_ML", "SWING"}:
            return {}
        if str(endpoint_name or "") == "realtime_report" and strategy not in {
            "SCALP",
            "SCALPING",
        }:
            return {}
        now = _now()
        target_date = _date_text(now)
        metadata_row = dict(metadata or {})
        raw_input = _json_bytes(user_input)
        payload_sha256 = hashlib.sha256(raw_input).hexdigest()
        prompt_sha256 = hashlib.sha256(_json_bytes(prompt)).hexdigest()
        request_envelope_sha256 = hashlib.sha256(
            _json_bytes(
                {
                    "endpoint": str(endpoint_name or "generic"),
                    "model": str(model or "-"),
                    "schema_name": str(schema_name or "-"),
                    "require_json": bool(require_json),
                    "temperature": temperature,
                    "max_output_tokens": max_output_tokens,
                    "reasoning_effort": reasoning_effort,
                    "prompt_sha256": prompt_sha256,
                    "user_input_sha256": payload_sha256,
                }
            )
        ).hexdigest()
        input_format, parsed_input = _parse_user_input(user_input)
        sanitized_input, redacted = _sanitize(parsed_input)
        sanitized_prompt, prompt_redacted = _sanitize(str(prompt or ""))
        context = _request_context(parsed_input, metadata_row)
        trace_id = str(request_id or "").strip() or f"aidt-{uuid.uuid4().hex}"
        payload_row = {
            "schema": PAYLOAD_SCHEMA,
            "captured_at": now.isoformat(),
            "payload_sha256": payload_sha256,
            "payload_bytes": len(raw_input),
            "request_envelope_sha256": request_envelope_sha256,
            "prompt_sha256": prompt_sha256,
            "endpoint": str(endpoint_name or "generic"),
            "model": str(model or "-"),
            "schema_name": str(schema_name or "-"),
            "require_json": bool(require_json),
            "temperature": temperature,
            "max_output_tokens": max_output_tokens,
            "reasoning_effort": reasoning_effort,
            "input_format": input_format,
            "redacted": bool(redacted),
            "replay_exact": not redacted,
            "sanitized_user_input": sanitized_input,
            **OBSERVATION_CONTRACT,
        }
        prompt_row = {
            "schema": PROMPT_SCHEMA,
            "captured_at": now.isoformat(),
            "prompt_sha256": prompt_sha256,
            "endpoint": str(endpoint_name or "generic"),
            "model": str(model or "-"),
            "schema_name": str(schema_name or "-"),
            "redacted": bool(prompt_redacted),
            "replay_exact": not prompt_redacted,
            "sanitized_prompt": sanitized_prompt,
            **OBSERVATION_CONTRACT,
        }
        with _WRITE_LOCK:
            seen = _SEEN_PAYLOAD_HASHES.get(target_date)
            if seen is None:
                path = _payload_path(target_date)
                seen = _load_seen(path, "request_envelope_sha256")
                _SEEN_PAYLOAD_HASHES[target_date] = seen
            if request_envelope_sha256 not in seen:
                _append_jsonl(_payload_path(target_date), payload_row)
                seen.add(request_envelope_sha256)
            seen_prompts = _SEEN_PROMPT_HASHES.get(target_date)
            if seen_prompts is None:
                prompt_path = _prompt_path(target_date)
                seen_prompts = _load_seen(prompt_path, "prompt_sha256")
                _SEEN_PROMPT_HASHES[target_date] = seen_prompts
            if prompt_sha256 not in seen_prompts:
                _append_jsonl(_prompt_path(target_date), prompt_row)
                seen_prompts.add(prompt_sha256)
        return {
            "ai_decision_trace_id": trace_id,
            "ai_prompt_sha256": prompt_sha256,
            "ai_prompt_store_date": target_date,
            "ai_prompt_redacted": bool(prompt_redacted),
            "ai_prompt_replay_exact": not prompt_redacted,
            "ai_input_payload_sha256": payload_sha256,
            "ai_input_payload_bytes": len(raw_input),
            "ai_request_envelope_sha256": request_envelope_sha256,
            "ai_request_temperature": temperature,
            "ai_request_max_output_tokens": max_output_tokens,
            "ai_request_reasoning_effort": reasoning_effort,
            "ai_input_payload_store_date": target_date,
            "ai_input_payload_redacted": bool(redacted),
            "ai_input_payload_replay_exact": not redacted,
            "ai_trace_stock_code": context.get("stock_code") or symbol or None,
            "ai_trace_record_id": context.get("record_id"),
            "ai_trace_recommendation_id": context.get("recommendation_id"),
            "ai_trace_probe_bundle_id": context.get("probe_bundle_id"),
            "ai_trace_position_cycle_id": context.get("position_cycle_id"),
            "ai_trace_broker_order_no": context.get("broker_order_no"),
            "ai_trace_snapshot_id": context.get("snapshot_id"),
            "ai_trace_effective_venue": context.get("effective_venue"),
            "ai_trace_session_bucket": context.get("session_bucket"),
            "ai_trace_broker_route": context.get("broker_route"),
            "ai_trace_market_data_route": context.get("market_data_route"),
            "ai_trace_reference_price": context.get("reference_price"),
            "ai_trace_best_bid": context.get("best_bid"),
            "ai_trace_best_ask": context.get("best_ask"),
            "ai_trace_target_price": context.get("target_price"),
            "ai_trace_adverse_price": context.get("adverse_price"),
            "ai_trace_target_pct": context.get("target_pct"),
            "ai_trace_adverse_pct": context.get("adverse_pct"),
        }
    except Exception as exc:
        log_error(f"[AI_DECISION_TRACE] request capture failed: {exc}")
        return {}


def _decision_stage(prompt_type: str, explicit_stage: str | None = None) -> str:
    if explicit_stage:
        return str(explicit_stage)
    return _STAGE_BY_PROMPT_TYPE.get(
        str(prompt_type or ""), str(prompt_type or "unknown")
    )


def _optional(payload: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = payload.get(key)
        if value not in (None, "", "-", "None", "null"):
            return value
    return None


def _provider_actual(payload: dict[str, Any], provider_called: bool) -> str | None:
    if not provider_called:
        return None
    explicit = _optional(payload, "provider", "provider_actual")
    if explicit:
        return str(explicit)
    if payload.get("bedrock_primary_used"):
        return "bedrock"
    if payload.get("bedrock_fallback_used"):
        return "bedrock"
    if payload.get("bedrock_failback_used"):
        return "openai"
    if provider_called:
        return "openai"
    return None


def _provider_decision_origin(payload: dict[str, Any]) -> str | None:
    explicit = _optional(payload, "provider", "provider_actual")
    if explicit:
        return str(explicit)
    if payload.get("bedrock_primary_used") or payload.get("bedrock_fallback_used"):
        return "bedrock"
    if _optional(payload, "openai_model", "ai_model"):
        return "openai"
    return None


def _model_actual(payload: dict[str, Any]) -> str | None:
    if payload.get("bedrock_primary_used") or payload.get("bedrock_fallback_used"):
        return _optional(
            payload,
            "bedrock_model_family",
            "bedrock_fallback_family",
        )
    value = _optional(payload, "ai_model", "openai_model")
    return str(value) if value is not None else None


def _reason_codes(payload: dict[str, Any]) -> list[str]:
    raw = payload.get("reason_codes")
    if isinstance(raw, list):
        return [str(item) for item in raw if str(item).strip()]
    value = payload.get("reason_code")
    return [str(value)] if value not in (None, "", "-") else []


def record_ai_decision_trace(
    result: dict[str, Any] | None,
    *,
    prompt_type: str,
    prompt_version: str,
    result_source: str,
    input_contract_fields: dict[str, Any] | None = None,
    decision_stage: str | None = None,
    stock_code: str | None = None,
    provider_called: bool | None = None,
) -> dict[str, Any]:
    """Append the immutable final decision and create its pending outcome row."""
    if not trace_enabled():
        return {}
    try:
        if str(prompt_type or "") not in _STAGE_BY_PROMPT_TYPE:
            return {}
        now = _now()
        target_date = _date_text(now)
        payload = dict(result or {})
        contract = dict(input_contract_fields or {})
        merged = {**contract, **payload}
        if str(prompt_type or "") == "realtime_gatekeeper" and str(
            _optional(merged, "ai_trace_strategy", "selected_mode") or ""
        ).upper() not in {"SCALP", "SCALPING"}:
            return {}
        decision_result_sha256 = hashlib.sha256(_json_bytes(payload)).hexdigest()
        trace_id = (
            str(
                _optional(merged, "ai_decision_trace_id", "openai_request_id") or ""
            ).strip()
            or f"aidt-{uuid.uuid4().hex}"
        )
        if provider_called is None:
            provider_called = bool(
                payload.get("provider_called")
                if "provider_called" in payload
                else str(result_source or "") == "live"
            )
        stage = _decision_stage(prompt_type, decision_stage)
        stock_identifier = str(
            stock_code
            or _optional(
                merged,
                "ai_trace_stock_code",
                "ai_market_snapshot_stock_code",
                "ai_input_stock_code",
            )
            or "-"
        ).strip()
        trace_row = {
            "schema": TRACE_SCHEMA,
            "decision_trace_id": trace_id,
            "decision_ts": now.isoformat(),
            "decision_stage": stage,
            "stock_code": _normalize_stock_code(stock_identifier),
            "stock_identifier": stock_identifier[:40],
            "effective_venue": _optional(
                merged,
                "ai_trace_effective_venue",
                "ai_market_snapshot_effective_venue",
                "ai_input_effective_venue",
            ),
            "session_bucket": _optional(
                merged,
                "ai_trace_session_bucket",
                "ai_market_snapshot_session_bucket",
            ),
            "broker_route": _optional(
                merged,
                "ai_trace_broker_route",
                "ai_market_snapshot_broker_route",
                "ai_input_broker_route",
            ),
            "market_data_route": _optional(
                merged,
                "ai_trace_market_data_route",
                "ai_market_snapshot_market_data_route",
                "ai_input_market_data_route",
            ),
            "record_id": _optional(merged, "ai_trace_record_id", "record_id"),
            "recommendation_id": _optional(
                merged, "ai_trace_recommendation_id", "recommendation_id"
            ),
            "probe_bundle_id": _optional(
                merged, "ai_trace_probe_bundle_id", "probe_bundle_id"
            ),
            "position_cycle_id": _optional(
                merged, "ai_trace_position_cycle_id", "position_cycle_id"
            ),
            "broker_order_no": _optional(
                merged, "ai_trace_broker_order_no", "broker_order_no"
            ),
            "snapshot_id": _optional(
                merged,
                "ai_trace_snapshot_id",
                "ai_input_snapshot_id",
                "ai_market_snapshot_id",
            ),
            "endpoint": _optional(merged, "openai_endpoint_name") or prompt_type,
            "provider_expected": _optional(
                merged,
                "holding_context_provider_expected",
                "provider_expected",
            ),
            "provider_actual": _provider_actual(merged, bool(provider_called)),
            "provider_decision_origin": _provider_decision_origin(merged),
            "model": _model_actual(merged),
            "model_requested": _optional(merged, "openai_model", "ai_model"),
            "prompt_type": str(prompt_type or "-"),
            "prompt_version": str(prompt_version or "-"),
            "prompt_sha256": _optional(merged, "ai_prompt_sha256"),
            "prompt_store_date": _optional(merged, "ai_prompt_store_date"),
            "prompt_redacted": bool(merged.get("ai_prompt_redacted", False)),
            "prompt_replay_exact": bool(merged.get("ai_prompt_replay_exact", False)),
            "payload_sha256": _optional(merged, "ai_input_payload_sha256"),
            "payload_bytes": _safe_number(_optional(merged, "ai_input_payload_bytes")),
            "payload_store_date": _optional(merged, "ai_input_payload_store_date"),
            "request_envelope_sha256": _optional(merged, "ai_request_envelope_sha256"),
            "request_temperature": _safe_number(
                _optional(merged, "ai_request_temperature")
            ),
            "request_max_output_tokens": _safe_number(
                _optional(merged, "ai_request_max_output_tokens")
            ),
            "request_reasoning_effort": _optional(
                merged, "ai_request_reasoning_effort"
            ),
            "payload_redacted": bool(merged.get("ai_input_payload_redacted", False)),
            "payload_replay_exact": bool(
                merged.get("ai_input_payload_replay_exact", False)
            ),
            "provider_called": bool(provider_called),
            "transport": _optional(merged, "openai_transport_mode"),
            "response_ms": _safe_number(
                _optional(merged, "ai_response_ms", "openai_ws_roundtrip_ms")
            ),
            "cache_hit": bool(merged.get("cache_hit", False)),
            "timeout": bool(
                merged.get("openai_transport_fail_closed")
                or merged.get("openai_ws_http_fallback_fail_closed")
            ),
            "parse_ok": bool(merged.get("ai_parse_ok", False)),
            "result_source": str(result_source or "-"),
            "action": _optional(
                merged, "action_v2", "action", "action_key", "action_label"
            ),
            "score": _safe_number(_optional(merged, "score", "ai_score")),
            "confidence": _safe_number(_optional(merged, "confidence")),
            "reason": str(_optional(merged, "reason", "report") or "")[:500],
            "reason_codes": _reason_codes(merged),
            "decision_result_sha256": decision_result_sha256,
            "parent_decision_trace_id": _optional(
                merged, "ai_decision_parent_trace_id"
            ),
            "input_preflight_status": _optional(merged, "ai_input_preflight_status"),
            "input_preflight_allowed": (
                bool(merged.get("ai_input_preflight_allowed"))
                if "ai_input_preflight_allowed" in merged
                else None
            ),
            "input_blockers": merged.get("ai_input_preflight_blockers", []),
            "missing_sources": merged.get("ai_input_preflight_missing_sources", []),
            "venue_consistent": (
                bool(merged.get("ai_input_preflight_venue_consistent"))
                if "ai_input_preflight_venue_consistent" in merged
                else None
            ),
            "max_source_skew_ms": _safe_number(
                merged.get("ai_input_preflight_max_source_skew_ms")
            ),
            "reference_price_type": (
                "executable_ask"
                if _optional(merged, "ai_trace_best_ask") is not None
                else "best_available_input_price"
            ),
            "reference_price": _safe_number(
                _optional(merged, "ai_trace_reference_price")
            ),
            "best_bid": _safe_number(_optional(merged, "ai_trace_best_bid")),
            "best_ask": _safe_number(_optional(merged, "ai_trace_best_ask")),
            "target_price": _safe_number(_optional(merged, "ai_trace_target_price")),
            "adverse_price": _safe_number(_optional(merged, "ai_trace_adverse_price")),
            "target_pct": _safe_number(_optional(merged, "ai_trace_target_pct")),
            "adverse_pct": _safe_number(_optional(merged, "ai_trace_adverse_pct")),
            "actual_order_authority": bool(merged.get("actual_order_authority", False)),
            **OBSERVATION_CONTRACT,
        }
        pending_row = {
            "schema": OUTCOME_SCHEMA,
            "label_id": f"{trace_id}:v1",
            "decision_trace_id": trace_id,
            "label_version": 1,
            "created_at": now.isoformat(),
            "label_status": "pending",
            "decision_stage": stage,
            "stock_code": trace_row["stock_code"],
            "stock_identifier": trace_row["stock_identifier"],
            "decision_ts": trace_row["decision_ts"],
            "effective_venue": trace_row["effective_venue"],
            "session_bucket": trace_row["session_bucket"],
            "broker_route": trace_row["broker_route"],
            "market_data_route": trace_row["market_data_route"],
            "record_id": trace_row["record_id"],
            "recommendation_id": trace_row["recommendation_id"],
            "probe_bundle_id": trace_row["probe_bundle_id"],
            "position_cycle_id": trace_row["position_cycle_id"],
            "broker_order_no": trace_row["broker_order_no"],
            "snapshot_id": trace_row["snapshot_id"],
            "action": trace_row["action"],
            "score": trace_row["score"],
            "result_source": trace_row["result_source"],
            "reference_price": trace_row["reference_price"],
            "best_bid": trace_row["best_bid"],
            "best_ask": trace_row["best_ask"],
            "target_price": trace_row["target_price"],
            "adverse_price": trace_row["adverse_price"],
            "target_pct": trace_row["target_pct"],
            "adverse_pct": trace_row["adverse_pct"],
            "matured_horizons_min": [],
            "pending_horizons_min": list(OUTCOME_HORIZONS_MIN),
            "source_quality_status": (
                "pending_future_window"
                if trace_row["reference_price"] is not None
                else "pending_reference_price_gap"
            ),
            "invalid_reasons": (
                []
                if trace_row["reference_price"] is not None
                else ["reference_price_missing"]
            ),
            **OBSERVATION_CONTRACT,
        }
        with _WRITE_LOCK:
            seen = _SEEN_TRACE_IDS.get(target_date)
            if seen is None:
                path = _trace_path(target_date)
                seen = _load_seen(path, "decision_trace_id")
                _SEEN_TRACE_IDS[target_date] = seen
            if trace_id not in seen:
                _append_jsonl(_trace_path(target_date), trace_row)
                _append_jsonl(_outcome_path(target_date), pending_row)
                seen.add(trace_id)
        return {
            "ai_decision_trace_schema": TRACE_SCHEMA,
            "ai_decision_trace_id": trace_id,
            "ai_decision_outcome_label_status": "pending",
        }
    except Exception as exc:
        log_error(f"[AI_DECISION_TRACE] decision append failed: {exc}")
        return {}
