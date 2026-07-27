"""Offline decision-quality control, outcome maturity, and paired replay.

This module consumes redacted exact payloads and future market observations.
It never sends an order and never mutates runtime prompts, models, providers,
thresholds, prices, quantities, broker guards, safety guards, or bot state.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import tempfile
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from statistics import fmean
from typing import Any, Callable, Iterable
from zoneinfo import ZoneInfo

from src.engine.ai_prompt_contracts import (
    DECISION_QUALITY_V2_RESPONSE_SCHEMA,
    decision_quality_v2_system_prompt,
)
from src.utils.constants import DATA_DIR
from src.utils.jsonl_io import open_text_auto

KST = ZoneInfo("Asia/Seoul")
CONTROL_SCHEMA = "ai_decision_quality_control_v1"
LABEL_REPORT_SCHEMA = "ai_decision_outcome_labels_v1"
BASELINE_SCHEMA = "ai_decision_quality_baseline_v1"
PAIRED_SCHEMA = "ai_prompt_paired_replay_v1"
INPUT_BUNDLE_VERSION = "scalping_multi_timeframe_context_v1"
ENTRY_CONTEXT_SCHEMA = "entry_candle_context_v1"
HOLDING_CONTEXT_SCHEMA = "holding_decision_context_v1"
HORIZONS_MIN = (1, 3, 5, 10, 20, 30, 60)
HORIZON_END_MAX_LAG_SEC = 90
PIPELINE_FORWARD_DAYS = 7
PRIMARY_HORIZON_BY_STAGE = {
    "entry": "10m",
    "entry_price": "10m",
    "post_probe": "10m",
    "scale_in": "20m",
    "holding": "30m",
    "exit": "30m",
    "overnight": "60m",
}

TRACE_DIR = DATA_DIR / "ai_decision_trace"
PAYLOAD_DIR = DATA_DIR / "ai_decision_payloads"
OUTCOME_DIR = DATA_DIR / "ai_decision_outcomes"
PIPELINE_DIR = DATA_DIR / "pipeline_events"
RUNTIME_DIR = DATA_DIR / "runtime"
LABEL_REPORT_DIR = DATA_DIR / "report" / "ai_decision_outcome_labels"
BASELINE_REPORT_DIR = DATA_DIR / "report" / "ai_decision_quality_baseline"
PAIRED_REPORT_DIR = DATA_DIR / "report" / "ai_prompt_paired_replay"

OFFLINE_CONTRACT = {
    "metric_role": "ai_decision_quality_observation",
    "decision_authority": "offline_replay_and_attribution_only",
    "window_policy": "exact_snapshot_stage_venue_session_mature_forward_window",
    "sample_floor": "eligible_exact_rows_with_mature_outcomes",
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "source_quality_gate": "exact_payload_fresh_same_route_mature_window",
    "runtime_effect": False,
    "allowed_runtime_apply": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
    "forbidden_uses": [
        "live_prompt_promotion_without_separate_review",
        "provider_or_model_change",
        "threshold_price_quantity_or_cap_change",
        "broker_or_safety_guard_bypass",
        "counterfactual_realized_pnl_merge",
        "bot_restart",
    ],
}

STAGE_ALIASES = {
    "analyze_target": "entry",
    "gatekeeper": "entry",
    "entry": "entry",
    "entry_price": "entry_price",
    "post_probe": "post_probe",
    "scale_in": "scale_in",
    "holding_score": "holding",
    "holding_flow": "holding",
    "holding": "holding",
    "exit": "exit",
    "overnight": "overnight",
}

REASON_EVIDENCE_KEYS = ("trend", "liquidity", "tape", "risk", "uncertainty")
STAGE_ACTIONS = {
    "entry": {"BUY", "WAIT", "DROP"},
    "entry_price": {"USE_DEFENSIVE", "USE_REFERENCE", "IMPROVE_LIMIT", "SKIP"},
    "post_probe": {"CONTINUE", "STOP"},
    "scale_in": {"ADD", "NO_ADD"},
    "holding": {"HOLD", "TRIM", "EXIT"},
    "exit": {"HOLD", "TRIM", "EXIT"},
    "overnight": {"HOLD_OVERNIGHT", "EXIT_BEFORE_CLOSE"},
}
EXPOSURE_ACTIONS = {
    "BUY",
    "ADD",
    "CONTINUE",
    "HOLD",
    "HOLD_OVERNIGHT",
    "USE_DEFENSIVE",
    "USE_REFERENCE",
    "IMPROVE_LIMIT",
}
NO_EXPOSURE_ACTIONS = {
    "DROP",
    "WAIT",
    "NO_ADD",
    "STOP",
    "EXIT",
    "SELL",
    "SELL_TODAY",
    "EXIT_BEFORE_CLOSE",
    "SKIP",
}
REASON_CODE_PATTERN = re.compile(r"^[a-z][a-z0-9_]{1,63}$")
EVIDENCE_VALUES = {
    "trend": {"supportive", "mixed", "adverse", "insufficient"},
    "liquidity": {"supportive", "mixed", "adverse", "insufficient"},
    "tape": {"supportive", "mixed", "adverse", "insufficient"},
    "risk": {"low", "medium", "high", "insufficient"},
    "uncertainty": {"low", "medium", "high"},
}


def control_path(target_date: str) -> Path:
    return RUNTIME_DIR / f"ai_decision_quality_control_{target_date}.json"


def label_report_path(target_date: str) -> Path:
    return LABEL_REPORT_DIR / f"ai_decision_outcome_labels_{target_date}.json"


def baseline_path(target_date: str) -> Path:
    return BASELINE_REPORT_DIR / f"ai_decision_quality_baseline_{target_date}.json"


def paired_path(target_date: str) -> Path:
    return PAIRED_REPORT_DIR / f"ai_prompt_paired_replay_{target_date}.json"


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")


def _sha256(value: Any) -> str:
    return hashlib.sha256(
        value if isinstance(value, bytes) else _canonical_bytes(value)
    ).hexdigest()


def _atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with open(fd, "w", encoding="utf-8", closefd=True) as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.flush()
        Path(tmp_name).replace(path)
    finally:
        Path(tmp_name).unlink(missing_ok=True)


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}
    return value if isinstance(value, dict) else {}


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with open_text_auto(path) as handle:
        for line in handle:
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict):
                rows.append(value)
    return rows


def _parse_ts(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=KST)
    return parsed.astimezone(KST)


def _number(value: Any) -> float | None:
    try:
        parsed = float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _normalize_stock_code(value: Any) -> str:
    raw = str(value or "").strip().upper()
    for suffix in ("_NX", "_AL"):
        if raw.endswith(suffix):
            raw = raw[:-3]
    if raw.startswith("A"):
        raw = raw[1:]
    digits = "".join(char for char in raw if char.isdigit())
    return digits[-6:].zfill(6) if digits else raw


def _walk(value: Any):
    yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def _payload_contract(payload: dict[str, Any]) -> dict[str, Any]:
    schemas: set[str] = set()
    bundles: set[str] = set()
    canonical_contexts: list[dict[str, Any]] = []
    for item in _walk(payload.get("sanitized_user_input")):
        if not isinstance(item, dict):
            continue
        schema = str(item.get("schema") or "")
        if schema in {ENTRY_CONTEXT_SCHEMA, HOLDING_CONTEXT_SCHEMA}:
            schemas.add(schema)
            candle = item.get("candle") if schema == HOLDING_CONTEXT_SCHEMA else item
            candle = candle if isinstance(candle, dict) else {}
            bars = candle.get("bars") if isinstance(candle.get("bars"), list) else None
            candle_bundle = str(candle.get("input_bundle_version") or "")
            if candle_bundle:
                bundles.add(candle_bundle)
            forming_key = (
                "is_forming" if schema == HOLDING_CONTEXT_SCHEMA else "forming"
            )
            canonical_contexts.append(
                {
                    "schema": schema,
                    "input_bundle_version": str(
                        candle.get("input_bundle_version") or ""
                    )
                    or None,
                    "raw_bar_count": len(bars) if bars is not None else None,
                    "completed_bar_count": sum(
                        1
                        for bar in (bars or [])
                        if isinstance(bar, dict)
                        and not bool(bar.get(forming_key, False))
                    ),
                    "forming_bar_present": any(
                        isinstance(bar, dict) and bool(bar.get(forming_key, False))
                        for bar in (bars or [])
                    ),
                }
            )
        bundle = str(item.get("input_bundle_version") or "")
        if bundle:
            bundles.add(bundle)
    return {
        "context_schemas": sorted(schemas),
        "input_bundle_versions": sorted(bundles),
        "canonical_contexts": canonical_contexts,
    }


def _payload_indexes(
    payloads: list[dict[str, Any]],
) -> tuple[
    dict[tuple[str, str], dict[str, Any]],
    dict[str, dict[str, Any]],
]:
    counts = Counter(
        str(row.get("payload_sha256")) for row in payloads if row.get("payload_sha256")
    )
    by_key = {
        (str(row.get("payload_sha256")), str(row.get("endpoint") or "")): row
        for row in payloads
        if row.get("payload_sha256")
    }
    by_unique_hash = {
        str(row.get("payload_sha256")): row
        for row in payloads
        if row.get("payload_sha256") and counts[str(row.get("payload_sha256"))] == 1
    }
    return by_key, by_unique_hash


def _stage(value: Any, endpoint: Any = None) -> str:
    for candidate in (value, endpoint):
        normalized = str(candidate or "").strip().lower()
        if normalized in STAGE_ALIASES:
            return STAGE_ALIASES[normalized]
        for key, result in STAGE_ALIASES.items():
            if key in normalized:
                return result
    return "unknown"


def _exact_trace_payload_findings(
    *,
    trace: dict[str, Any],
    payload: dict[str, Any],
    promoted_at: datetime | None,
) -> list[str]:
    findings: list[str] = []
    decision_ts = _parse_ts(trace.get("decision_ts"))
    if promoted_at is None:
        findings.append("promotion_timestamp_missing")
    elif decision_ts is None or decision_ts < promoted_at:
        findings.append("pre_promotion")
    if trace.get("payload_replay_exact") is not True:
        findings.append("not_exact")
    if trace.get("request_capture_status") != "captured":
        findings.append("request_not_captured")
    if not trace.get("payload_sha256"):
        findings.append("payload_hash_missing")
    if not payload or payload.get("replay_exact") is not True:
        findings.append("payload_store_not_exact")
    if str(trace.get("provider_actual") or "none").lower() == "none":
        findings.append("provider_none")
    if trace.get("input_preflight_allowed") is not True:
        findings.append("source_quality_not_allowed")
    if trace.get("venue_consistent") is not True:
        findings.append("venue_not_consistent")
    if str(trace.get("input_preflight_mode") or "") != "exact_v2":
        findings.append("input_preflight_not_exact_v2")
    if trace.get("input_blockers"):
        findings.append("source_quality_blockers_present")
    contract = _payload_contract(payload)
    expected_schema = (
        ENTRY_CONTEXT_SCHEMA
        if _stage(trace.get("decision_stage"), trace.get("endpoint"))
        in {"entry", "entry_price"}
        else HOLDING_CONTEXT_SCHEMA
    )
    if expected_schema not in contract["context_schemas"]:
        findings.append("context_schema_missing")
    expected_contexts = [
        context
        for context in contract["canonical_contexts"]
        if context["schema"] == expected_schema
    ]
    if not expected_contexts or not any(
        context["input_bundle_version"] == INPUT_BUNDLE_VERSION
        for context in expected_contexts
    ):
        findings.append("input_bundle_missing")
    contexts_with_raw_bars = [
        context for context in expected_contexts if context["raw_bar_count"] is not None
    ]
    if not contexts_with_raw_bars:
        findings.append("canonical_bars_missing")
    elif not any(
        context["completed_bar_count"] > 0 for context in contexts_with_raw_bars
    ):
        findings.append("canonical_completed_bars_missing")
    capture_status = str(trace.get("canonical_context_capture_status") or "")
    if capture_status and capture_status != "exact_completed_bars_captured":
        findings.append(f"canonical_context_capture_{capture_status}")
    return findings


def build_control_manifest(
    *,
    target_date: str,
    promotion: dict[str, Any],
    traces: list[dict[str, Any]],
    payloads: list[dict[str, Any]],
) -> dict[str, Any]:
    """Freeze actual current prompts/routes on post-promotion exact requests."""

    promoted_at = _parse_ts(promotion.get("promoted_at"))
    payload_by_key, payload_by_unique_hash = _payload_indexes(payloads)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    excluded = Counter()
    for trace in traces:
        payload_hash = str(trace.get("payload_sha256") or "")
        endpoint = str(trace.get("endpoint") or trace.get("decision_stage") or "")
        payload = payload_by_key.get(
            (payload_hash, endpoint),
            payload_by_unique_hash.get(payload_hash, {}),
        )
        exact_findings = _exact_trace_payload_findings(
            trace=trace,
            payload=payload,
            promoted_at=promoted_at,
        )
        if exact_findings:
            excluded.update(exact_findings)
            continue
        if not all(
            str(trace.get(key) or "").strip()
            for key in ("prompt_version", "prompt_sha256", "model")
        ):
            excluded["control_signature_incomplete"] += 1
            continue
        grouped[
            str(trace.get("endpoint") or trace.get("decision_stage") or "unknown")
        ].append(trace)
    controls: list[dict[str, Any]] = []
    conflicts: list[str] = []
    for endpoint, rows in sorted(grouped.items()):
        signatures: dict[str, dict[str, Any]] = {}
        for row in rows:
            signature = {
                "decision_stage": _stage(
                    row.get("decision_stage"), row.get("endpoint")
                ),
                "endpoint": endpoint,
                "prompt_version": row.get("prompt_version"),
                "prompt_sha256": row.get("prompt_sha256"),
                "provider_actual": row.get("provider_actual"),
                "model": row.get("model"),
                "request_temperature": row.get("request_temperature"),
                "request_reasoning_effort": row.get("request_reasoning_effort"),
                "response_schema": row.get("schema_name")
                or row.get("response_schema")
                or "captured_runtime_contract",
            }
            signatures[_sha256(signature)] = signature
        if len(signatures) != 1:
            conflicts.append(f"control_signature_conflict:{endpoint}")
            continue
        control = next(iter(signatures.values()))
        control["sample_count"] = len(rows)
        controls.append(control)
    required_stages = {"entry", "entry_price", "holding", "overnight"}
    observed_stages = {row["decision_stage"] for row in controls}
    missing_stages = sorted(required_stages - observed_stages)
    promotion_ready = (
        promotion.get("decision") == "promoted_all_market_sessions_full"
        and promotion.get("runtime_activation") is True
        and promotion.get("transaction_status") == "committed"
    )
    status = (
        "control_manifest_frozen_collect_exact_samples"
        if promotion_ready and controls and not conflicts
        else (
            "promotion_failed_no_control_reset"
            if not promotion_ready
            else "control_manifest_gap_fix_required"
        )
    )
    manifest = {
        "schema": CONTROL_SCHEMA,
        "target_date": target_date,
        "generated_at": datetime.now(KST).isoformat(),
        "status": status,
        "input_preflight_mode": "exact_v2",
        "entry_context_schema": ENTRY_CONTEXT_SCHEMA,
        "holding_context_schema": HOLDING_CONTEXT_SCHEMA,
        "input_bundle_version": INPUT_BUNDLE_VERSION,
        "promotion_artifact": str(
            RUNTIME_DIR / f"ai_multi_timeframe_context_promotion_{target_date}.json"
        ),
        "promotion_sha256": _sha256(promotion) if promotion else None,
        "controls": controls,
        "missing_natural_stages": missing_stages,
        "conflicts": conflicts,
        "excluded_counts": dict(excluded),
        "prompt_model_provider_change_count": len(conflicts),
        **OFFLINE_CONTRACT,
    }
    manifest["control_manifest_sha256"] = _sha256(manifest)
    return manifest


def annotate_primary_cohort_eligibility(
    *,
    labels: list[dict[str, Any]],
    traces: list[dict[str, Any]],
    payloads: list[dict[str, Any]],
    promotion: dict[str, Any],
) -> list[dict[str, Any]]:
    """Join exact trace/payload evidence before labels enter the primary cohort."""

    promoted_at = _parse_ts(promotion.get("promoted_at"))
    traces_by_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for trace in traces:
        trace_id = str(trace.get("decision_trace_id") or "")
        if trace_id:
            traces_by_id[trace_id].append(trace)
    payload_by_key, payload_by_unique_hash = _payload_indexes(payloads)
    annotated: list[dict[str, Any]] = []
    for label in labels:
        trace_id = str(label.get("decision_trace_id") or "")
        trace_rows = traces_by_id.get(trace_id, [])
        findings: list[str] = []
        if len(trace_rows) != 1:
            findings.append(
                "decision_trace_missing"
                if not trace_rows
                else "decision_trace_ambiguous"
            )
            trace: dict[str, Any] = {}
            payload: dict[str, Any] = {}
        else:
            trace = trace_rows[0]
            payload_hash = str(trace.get("payload_sha256") or "")
            endpoint = str(trace.get("endpoint") or trace.get("decision_stage") or "")
            payload = payload_by_key.get(
                (payload_hash, endpoint),
                payload_by_unique_hash.get(payload_hash, {}),
            )
            findings.extend(
                _exact_trace_payload_findings(
                    trace=trace,
                    payload=payload,
                    promoted_at=promoted_at,
                )
            )
            if _venue(label.get("effective_venue")) != _venue(
                trace.get("effective_venue")
            ):
                findings.append("label_trace_venue_mismatch")
            if _session(label.get("session_bucket")) != _session(
                trace.get("session_bucket")
            ):
                findings.append("label_trace_session_mismatch")
        annotated.append(
            {
                **label,
                "primary_cohort_eligible": not findings,
                "primary_cohort_exclusion_reasons": sorted(set(findings)),
                "primary_payload_sha256": trace.get("payload_sha256"),
                "primary_context_contract": _payload_contract(payload),
            }
        )
    return annotated


def load_pipeline_price_and_lifecycle_rows(
    rows: Iterable[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    prices: list[dict[str, Any]] = []
    lifecycle: list[dict[str, Any]] = []
    price_keys = (
        "current_price",
        "curr",
        "price",
        "observed_price",
        "current_price_observed",
        "trade_price",
        "fill_price",
    )
    for row in rows:
        fields = row.get("fields")
        fields = fields if isinstance(fields, dict) else {}
        timestamp = _parse_ts(row.get("emitted_at") or fields.get("event_ts"))
        code = _normalize_stock_code(row.get("stock_code") or fields.get("stock_code"))
        price = next(
            (
                parsed
                for key in price_keys
                if (parsed := _number(fields.get(key))) is not None and parsed > 0
            ),
            None,
        )
        venue = str(
            fields.get("effective_venue")
            or fields.get("ai_market_snapshot_effective_venue")
            or fields.get("market_venue")
            or ""
        ).upper()
        session = str(
            fields.get("session_bucket")
            or fields.get("ai_market_snapshot_session_bucket")
            or ""
        ).upper()
        if timestamp and code and price:
            prices.append(
                {
                    "timestamp": timestamp.isoformat(),
                    "stock_code": code,
                    "price": price,
                    "effective_venue": venue or None,
                    "session_bucket": session or None,
                    "source_quality": str(
                        fields.get("source_quality_status")
                        or fields.get("source_quality")
                        or "not_recorded"
                    ),
                }
            )
        lifecycle.append(
            {
                "timestamp": timestamp.isoformat() if timestamp else None,
                "stage": row.get("stage"),
                "stock_code": code,
                "record_id": row.get("record_id") or fields.get("record_id"),
                "recommendation_id": fields.get("recommendation_id"),
                "probe_bundle_id": fields.get("probe_bundle_id"),
                "position_cycle_id": fields.get("position_cycle_id"),
                "broker_order_no": fields.get("broker_order_no")
                or fields.get("order_no"),
                "actual_order_submitted": _bool(fields.get("actual_order_submitted")),
                "filled": "fill" in str(row.get("stage") or "").lower()
                or _bool(fields.get("filled")),
                "realized_profit_pct": _number(
                    fields.get("realized_profit_pct")
                    if fields.get("realized_profit_pct") is not None
                    else fields.get("profit_rate")
                ),
            }
        )
    return prices, lifecycle


def _venue(value: Any) -> str:
    text = str(value or "").strip().upper()
    if text in {"PREMARKET", "PREMARKET_KRX_LIKE"}:
        return "PREMARKET_KRX_LIKE"
    if "NXT" in text:
        return "NXT"
    if "KRX" in text:
        return "KRX"
    return text


def _session(value: Any) -> str:
    text = str(value or "").strip().upper()
    aliases = {
        "REGULAR": "KRX_REGULAR",
        "AFTERMARKET": "NXT_AFTERMARKET",
        "PREMARKET": "PREMARKET_KRX_LIKE",
    }
    return aliases.get(text, text)


def _price_source_usable(price: dict[str, Any]) -> bool:
    quality = str(price.get("source_quality") or "").strip().lower()
    if not quality or any(
        token in quality
        for token in (
            "conflict",
            "duplicate",
            "invalid",
            "stale",
            "missing",
            "unavailable",
            "not_recorded",
            "unknown",
        )
    ):
        return False
    return any(
        token in quality
        for token in ("pass", "fresh", "usable", "valid", "event_observed")
    )


def _same_route(label: dict[str, Any], price: dict[str, Any]) -> bool:

    venue = _venue(label.get("effective_venue"))
    observed_venue = _venue(price.get("effective_venue"))
    if venue and (not observed_venue or venue != observed_venue):
        return False
    session = _session(label.get("session_bucket"))
    observed_session = _session(price.get("session_bucket"))
    if session and (not observed_session or session != observed_session):
        return False
    return _price_source_usable(price)


def _correlation(
    label: dict[str, Any], lifecycle_rows: list[dict[str, Any]]
) -> dict[str, Any]:
    label_code = _normalize_stock_code(label.get("stock_code"))
    decision_ts = _parse_ts(label.get("decision_ts"))
    identifiers = {
        str(label.get(key))
        for key in (
            "record_id",
            "recommendation_id",
            "probe_bundle_id",
            "position_cycle_id",
            "broker_order_no",
        )
        if label.get(key) not in (None, "", "-")
    }
    matched = []
    for row in lifecycle_rows:
        row_code = _normalize_stock_code(row.get("stock_code"))
        row_ts = _parse_ts(row.get("timestamp"))
        if not label_code or not row_code or row_code != label_code:
            continue
        if decision_ts is None or row_ts is None or row_ts < decision_ts:
            continue
        values = {
            str(row.get(key))
            for key in (
                "record_id",
                "recommendation_id",
                "probe_bundle_id",
                "position_cycle_id",
                "broker_order_no",
            )
            if row.get(key) not in (None, "", "-")
        }
        if identifiers and identifiers.intersection(values):
            matched.append(row)
    matched.sort(
        key=lambda row: _parse_ts(row.get("timestamp"))
        or datetime.min.replace(tzinfo=KST)
    )
    realized = [
        row["realized_profit_pct"]
        for row in matched
        if row.get("realized_profit_pct") is not None
    ]
    matched_event_count = len(matched)
    return {
        "status": "exact_matched" if matched else "open_unresolved",
        "matched_event_count": matched_event_count,
        "actual_order_submitted": (
            any(row.get("actual_order_submitted") for row in matched)
            if matched
            else None
        ),
        "fill_observed": (
            any(row.get("filled") for row in matched) if matched else None
        ),
        "realized_profit_pct": realized[-1] if realized else None,
        "realized_separate_from_counterfactual": True,
    }


def mature_outcome_labels(
    *,
    pending_labels: list[dict[str, Any]],
    price_rows: list[dict[str, Any]],
    lifecycle_rows: list[dict[str, Any]],
    as_of: datetime,
) -> list[dict[str, Any]]:
    prices_by_code: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in price_rows:
        timestamp = _parse_ts(row.get("timestamp"))
        price = _number(row.get("price"))
        code = _normalize_stock_code(row.get("stock_code"))
        if timestamp and price and price > 0 and code:
            prices_by_code[code].append(
                {**row, "_timestamp": timestamp, "_price": price}
            )
    for rows in prices_by_code.values():
        rows.sort(key=lambda row: row["_timestamp"])
    matured: list[dict[str, Any]] = []
    for pending in pending_labels:
        decision_ts = _parse_ts(pending.get("decision_ts"))
        reference = _number(pending.get("reference_price"))
        code = _normalize_stock_code(pending.get("stock_code"))
        stage = _stage(pending.get("decision_stage"))
        invalid = list(pending.get("invalid_reasons") or [])
        horizon_metrics: dict[str, dict[str, Any]] = {}
        matured_horizons: list[int] = []
        pending_horizons: list[int] = []
        if not decision_ts:
            invalid.append("decision_ts_invalid")
        if reference is None or reference <= 0:
            invalid.append("reference_price_missing")
        if not str(pending.get("effective_venue") or "").strip():
            invalid.append("effective_venue_missing")
        if not str(pending.get("session_bucket") or "").strip():
            invalid.append("session_bucket_missing")
        next_session_start: datetime | None = None
        next_session_date = ""
        next_session_venue = ""
        next_session_bucket = ""
        if stage == "overnight" and decision_ts:
            next_session_candidates = [
                row
                for row in prices_by_code.get(code, [])
                if row["_timestamp"].date() > decision_ts.date()
                and _venue(row.get("effective_venue"))
                and _session(row.get("session_bucket"))
                and _price_source_usable(row)
            ]
            if next_session_candidates:
                first = next_session_candidates[0]
                next_session_start = first["_timestamp"]
                next_session_date = first["_timestamp"].date().isoformat()
                next_session_venue = _venue(first.get("effective_venue"))
                next_session_bucket = _session(first.get("session_bucket"))
        for horizon in HORIZONS_MIN:
            window_start = next_session_start if stage == "overnight" else decision_ts
            horizon_end = (
                window_start + timedelta(minutes=horizon) if window_start else None
            )
            if not horizon_end or as_of < horizon_end:
                pending_horizons.append(horizon)
                continue
            if stage == "overnight":
                window = [
                    row
                    for row in prices_by_code.get(code, [])
                    if window_start <= row["_timestamp"] <= horizon_end
                    and row["_timestamp"].date().isoformat() == next_session_date
                    and _venue(row.get("effective_venue")) == next_session_venue
                    and _session(row.get("session_bucket")) == next_session_bucket
                    and _price_source_usable(row)
                ]
            else:
                window = [
                    row
                    for row in prices_by_code.get(code, [])
                    if decision_ts < row["_timestamp"] <= horizon_end
                    and _same_route(pending, row)
                ]
            if not window or reference is None or reference <= 0:
                pending_horizons.append(horizon)
                continue
            if (
                horizon_end - window[-1]["_timestamp"]
            ).total_seconds() > HORIZON_END_MAX_LAG_SEC:
                pending_horizons.append(horizon)
                continue
            returns = [
                round(((row["_price"] / reference) - 1.0) * 100.0, 10) for row in window
            ]
            target_price = _number(pending.get("target_price"))
            adverse_price = _number(pending.get("adverse_price"))
            target_hit = next(
                (
                    row["_timestamp"].isoformat()
                    for row in window
                    if target_price is not None and row["_price"] >= target_price
                ),
                None,
            )
            adverse_hit = next(
                (
                    row["_timestamp"].isoformat()
                    for row in window
                    if adverse_price is not None and row["_price"] <= adverse_price
                ),
                None,
            )
            first_hit = (
                "target"
                if target_hit and (not adverse_hit or target_hit <= adverse_hit)
                else ("adverse" if adverse_hit else "neither")
            )
            horizon_metrics[f"{horizon}m"] = {
                "sample_count": len(window),
                "mfe_pct": max(returns),
                "mae_pct": min(returns),
                "end_return_pct": returns[-1],
                "target_hit_at": target_hit,
                "adverse_hit_at": adverse_hit,
                "first_hit": first_hit,
                "counterfactual_only": True,
                "window_basis": (
                    "next_session_from_first_observation"
                    if stage == "overnight"
                    else "post_decision_same_route"
                ),
                "window_start": window_start.isoformat(),
                "observed_venue": (
                    next_session_venue
                    if stage == "overnight"
                    else _venue(pending.get("effective_venue"))
                ),
                "observed_session_bucket": (
                    next_session_bucket
                    if stage == "overnight"
                    else _session(pending.get("session_bucket"))
                ),
                "first_price": window[0]["_price"],
                "gap_from_reference_pct": (
                    round(((window[0]["_price"] / reference) - 1.0) * 100.0, 10)
                    if stage == "overnight"
                    else None
                ),
            }
            matured_horizons.append(horizon)
        correlation = _correlation(pending, lifecycle_rows)
        longest = (
            horizon_metrics[f"{max(matured_horizons)}m"] if matured_horizons else {}
        )
        stage_outcome: dict[str, Any] = {}
        if stage == "post_probe":
            stage_outcome = {
                "residual_submitted": correlation["actual_order_submitted"],
                "fill_observed": correlation["fill_observed"],
                "incremental_mfe_pct": longest.get("mfe_pct"),
                "incremental_mae_pct": longest.get("mae_pct"),
            }
        elif stage == "scale_in":
            stage_outcome = {
                "incremental_return_pct": longest.get("end_return_pct"),
                "incremental_ev_pct": None,
                "incremental_ev_status": (
                    "not_available_without_add_no_add_notional_join"
                ),
                "additional_downside_pct": longest.get("mae_pct"),
            }
        elif stage == "holding":
            stage_outcome = {
                "secured_upside_pct": longest.get("mfe_pct"),
                "enlarged_loss_pct": longest.get("mae_pct"),
            }
        elif stage == "exit":
            stage_outcome = {
                "realized_profit_pct": correlation["realized_profit_pct"],
                "post_sell_mfe_pct": longest.get("mfe_pct"),
                "post_sell_mae_pct": longest.get("mae_pct"),
                "peak_giveback_pct": (
                    longest.get("mfe_pct", 0) - longest.get("end_return_pct", 0)
                    if longest
                    else None
                ),
            }
        elif stage == "overnight":
            shortest = (
                horizon_metrics[f"{min(matured_horizons)}m"] if matured_horizons else {}
            )
            stage_outcome = {
                "next_session_date": next_session_date or None,
                "next_session_venue": next_session_venue or None,
                "next_session_bucket": next_session_bucket or None,
                "next_session_gap_pct": shortest.get("gap_from_reference_pct"),
                "next_session_return_pct": longest.get("end_return_pct"),
                "next_session_mfe_pct": longest.get("mfe_pct"),
                "next_session_mae_pct": longest.get("mae_pct"),
            }
        status = (
            "mature"
            if len(matured_horizons) == len(HORIZONS_MIN)
            else ("partial" if matured_horizons else "pending")
        )
        source_quality = (
            "pass"
            if matured_horizons and not invalid
            else ("partial" if matured_horizons else "source_quality_blocked")
        )
        matured.append(
            {
                **pending,
                "label_status": status,
                "matured_at": as_of.isoformat() if matured_horizons else None,
                "matured_horizons_min": matured_horizons,
                "pending_horizons_min": pending_horizons,
                "horizon_metrics": horizon_metrics,
                "stage_outcome": stage_outcome,
                "correlation": correlation,
                "source_quality_status": source_quality,
                "invalid_reasons": sorted(set(invalid)),
                **OFFLINE_CONTRACT,
            }
        )
    return matured


def _primary_metric(label: dict[str, Any]) -> dict[str, Any] | None:
    metrics = label.get("horizon_metrics")
    if not isinstance(metrics, dict):
        return None
    horizon = PRIMARY_HORIZON_BY_STAGE.get(_stage(label.get("decision_stage")))
    metric = metrics.get(horizon) if horizon else None
    return metric if isinstance(metric, dict) else None


def _taxonomy(label: dict[str, Any]) -> list[str]:
    action = str(label.get("action") or "").upper()
    preferred = _primary_metric(label) or {}
    mfe = _number(preferred.get("mfe_pct")) or 0.0
    mae = _number(preferred.get("mae_pct")) or 0.0
    end_return = _number(preferred.get("end_return_pct")) or 0.0
    first_hit = str(preferred.get("first_hit") or "")
    stage = _stage(label.get("decision_stage"))
    errors: list[str] = []
    if action == "DROP" and mfe >= 1.0:
        errors.append("false_drop")
    if action == "WAIT" and mfe >= 1.0:
        errors.append("false_wait")
    if action == "BUY" and (first_hit == "adverse" or mae <= -1.0):
        errors.append("false_buy")
    if stage == "scale_in" and action in {"ADD", "BUY", "SUPPORT"} and end_return < 0:
        errors.append("bad_scale_support")
    if stage in {"holding", "exit"} and action == "HOLD" and end_return <= -1.0:
        errors.append("bad_exit_defer")
    if stage == "exit" and action in {"EXIT", "SELL", "TRIM"} and mfe >= 1.0:
        errors.append("early_exit_support")
    confidence = _number(label.get("confidence")) or 0.0
    if confidence >= 80 and label.get("source_quality_status") != "pass":
        errors.append("unsupported_confidence")
    return errors


def _decision_value(action: Any, outcome: float | None) -> float | None:
    normalized = str(action or "").strip().upper()
    if outcome is None:
        return None
    if normalized in EXPOSURE_ACTIONS:
        return outcome
    if normalized in NO_EXPOSURE_ACTIONS:
        return 0.0
    return None


def build_quality_baseline(
    *, target_date: str, labels: list[dict[str, Any]]
) -> dict[str, Any]:
    source_eligible = [
        row
        for row in labels
        if row.get("label_status") in {"partial", "mature"}
        and row.get("source_quality_status") == "pass"
        and row.get("primary_cohort_eligible") is True
    ]
    primary_ineligible_count = sum(
        row.get("label_status") in {"partial", "mature"}
        and row.get("source_quality_status") == "pass"
        and row.get("primary_cohort_eligible") is not True
        for row in labels
    )
    eligible = [row for row in source_eligible if _primary_metric(row) is not None]
    buckets: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    enriched = []
    taxonomy_counts = Counter()
    for row in eligible:
        errors = _taxonomy(row)
        taxonomy_counts.update(errors)
        preferred = _primary_metric(row) or {}
        outcome = _number(preferred.get("end_return_pct"))
        decision_value = _decision_value(row.get("action"), outcome)
        enriched_row = {
            "decision_trace_id": row.get("decision_trace_id"),
            "decision_stage": _stage(row.get("decision_stage")),
            "effective_venue": row.get("effective_venue"),
            "session_bucket": row.get("session_bucket"),
            "action": row.get("action"),
            "outcome_return_pct": outcome,
            "decision_value_pct": decision_value,
            "errors": errors,
        }
        enriched.append(enriched_row)
        buckets[
            (
                enriched_row["decision_stage"],
                str(enriched_row["effective_venue"] or "UNKNOWN"),
                str(enriched_row["session_bucket"] or "UNKNOWN"),
            )
        ].append(enriched_row)
    bucket_rows = []
    for (stage, venue, session), rows in sorted(buckets.items()):
        decision_values = [
            row["decision_value_pct"]
            for row in rows
            if row["decision_value_pct"] is not None
        ]
        bucket_rows.append(
            {
                "decision_stage": stage,
                "effective_venue": venue,
                "session_bucket": session,
                "sample_count": len(rows),
                "source_quality_adjusted_ev_pct": (
                    fmean(decision_values) if decision_values else None
                ),
                "diagnostic_win_rate": (
                    sum(value > 0 for value in decision_values)
                    / len(decision_values)
                    * 100.0
                    if decision_values
                    else None
                ),
                "error_counts": dict(
                    Counter(error for row in rows for error in row["errors"])
                ),
            }
        )
    decision_values = [
        row["decision_value_pct"]
        for row in enriched
        if row["decision_value_pct"] is not None
    ]
    status = (
        "control_error_baseline_ready" if eligible else "partial_horizons_keep_maturing"
    )
    return {
        "schema": BASELINE_SCHEMA,
        "target_date": target_date,
        "generated_at": datetime.now(KST).isoformat(),
        "status": status,
        "eligible_sample_count": len(eligible),
        "source_eligible_sample_count": len(source_eligible),
        "primary_horizon_pending_count": len(source_eligible) - len(eligible),
        "primary_cohort_ineligible_count": primary_ineligible_count,
        "source_quality_adjusted_ev_pct": (
            fmean(decision_values) if decision_values else None
        ),
        "diagnostic_win_rate": (
            sum(value > 0 for value in decision_values) / len(decision_values) * 100.0
            if decision_values
            else None
        ),
        "taxonomy_counts": dict(taxonomy_counts),
        "buckets": bucket_rows,
        "rows": enriched,
        **OFFLINE_CONTRACT,
    }


def validate_candidate_response(response: dict[str, Any], *, stage: str) -> list[str]:
    errors: list[str] = []
    normalized_stage = str(stage or "").strip().lower()
    if response.get("edge_state") not in {
        "EDGE",
        "NO_EDGE",
        "INSUFFICIENT_DATA",
    }:
        errors.append("edge_state_invalid")
    action = str(response.get("action") or "").strip().upper()
    if not action:
        errors.append("action_missing")
    elif action not in STAGE_ACTIONS.get(normalized_stage, set()):
        errors.append("action_invalid_for_stage")
    for field in ("expected_upside_pct", "expected_downside_pct"):
        if field not in response:
            errors.append(f"{field}_missing")
        elif response.get(field) is not None and _number(response.get(field)) is None:
            errors.append(f"{field}_invalid")
    confidence = _number(response.get("confidence"))
    if confidence is None or not 0 <= confidence <= 100:
        errors.append("confidence_invalid")
    codes = response.get("reason_codes")
    if (
        not isinstance(codes, list)
        or not codes
        or any(not REASON_CODE_PATTERN.fullmatch(str(code)) for code in codes)
    ):
        errors.append("reason_codes_invalid")
    evidence = response.get("evidence")
    if not isinstance(evidence, dict):
        errors.append("evidence_missing")
    else:
        for key in REASON_EVIDENCE_KEYS:
            value = str(evidence.get(key) or "").strip().lower()
            if not value:
                errors.append(f"evidence_{key}_missing")
            elif value not in EVIDENCE_VALUES[key]:
                errors.append(f"evidence_{key}_invalid")
    if normalized_stage not in STAGE_ACTIONS:
        errors.append("stage_unsupported")
    return errors


def prepare_paired_replay_requests(
    *,
    control_manifest: dict[str, Any],
    traces: list[dict[str, Any]],
    payloads: list[dict[str, Any]],
    labels: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if (
        control_manifest.get("status")
        != "control_manifest_frozen_collect_exact_samples"
    ):
        return []
    controls = {
        str(row.get("endpoint") or ""): row
        for row in control_manifest.get("controls") or []
        if isinstance(row, dict) and row.get("endpoint")
    }
    label_by_trace = {
        str(row.get("decision_trace_id")): row
        for row in labels
        if row.get("label_status") in {"partial", "mature"}
        and row.get("source_quality_status") == "pass"
        and row.get("primary_cohort_eligible") is True
        and _primary_metric(row) is not None
    }
    payload_by_key, payload_by_unique_hash = _payload_indexes(payloads)
    requests = []
    for trace in traces:
        trace_id = str(trace.get("decision_trace_id") or "")
        label = label_by_trace.get(trace_id)
        payload_hash = str(trace.get("payload_sha256") or "")
        endpoint = str(trace.get("endpoint") or trace.get("decision_stage") or "")
        payload = payload_by_key.get(
            (payload_hash, endpoint),
            payload_by_unique_hash.get(payload_hash),
        )
        if (
            not label
            or not payload
            or not trace.get("payload_replay_exact")
            or payload.get("replay_exact") is not True
            or label.get("primary_cohort_eligible") is not True
        ):
            continue
        stage = _stage(trace.get("decision_stage"), trace.get("endpoint"))
        if stage == "unknown":
            continue
        control = controls.get(endpoint)
        if not control:
            continue
        signature_fields = (
            ("prompt_version", "prompt_version"),
            ("prompt_sha256", "prompt_sha256"),
            ("provider_actual", "provider_actual"),
            ("model", "model"),
            ("request_temperature", "request_temperature"),
            ("request_reasoning_effort", "request_reasoning_effort"),
        )
        if any(
            trace.get(trace_key) != control.get(control_key)
            for trace_key, control_key in signature_fields
        ):
            continue
        requests.append(
            {
                "paired_replay_id": f"pair-{_sha256((trace_id, trace.get('payload_sha256')))[:24]}",
                "decision_trace_id": trace_id,
                "stage": stage,
                "effective_venue": trace.get("effective_venue"),
                "session_bucket": trace.get("session_bucket"),
                "payload_sha256": trace.get("payload_sha256"),
                "exact_payload": payload.get("sanitized_user_input"),
                "control": {
                    "prompt_version": control.get("prompt_version"),
                    "prompt_sha256": control.get("prompt_sha256"),
                    "provider": control.get("provider_actual"),
                    "model": control.get("model"),
                    "temperature": control.get("request_temperature"),
                    "reasoning_effort": control.get("request_reasoning_effort"),
                    "captured_action": trace.get("action"),
                },
                "candidate": {
                    "prompt_version": f"decision_quality_v2_{stage}",
                    "system_prompt": decision_quality_v2_system_prompt(stage),
                    "system_prompt_sha256": _sha256(
                        decision_quality_v2_system_prompt(stage)
                    ),
                    "response_schema": DECISION_QUALITY_V2_RESPONSE_SCHEMA,
                    "provider": trace.get("provider_actual"),
                    "model": trace.get("model"),
                    "temperature": trace.get("request_temperature"),
                    "reasoning_effort": trace.get("request_reasoning_effort"),
                },
                "outcome_join_key": label.get("label_id"),
                **OFFLINE_CONTRACT,
            }
        )
    return requests


def run_paired_replay(
    requests: list[dict[str, Any]],
    *,
    control_runner: Callable[[dict[str, Any]], dict[str, Any]],
    candidate_runner: Callable[[dict[str, Any]], dict[str, Any]],
) -> list[dict[str, Any]]:
    """Execute both prompts on the same payload through injected offline runners."""

    results = []
    for request in requests:
        control_response = control_runner(request)
        candidate_response = candidate_runner(request)
        candidate_errors = validate_candidate_response(
            candidate_response, stage=str(request["stage"])
        )
        results.append(
            {
                "paired_replay_id": request["paired_replay_id"],
                "decision_trace_id": request["decision_trace_id"],
                "stage": request["stage"],
                "effective_venue": request.get("effective_venue"),
                "session_bucket": request.get("session_bucket"),
                "payload_sha256": request["payload_sha256"],
                "same_payload_confirmed": True,
                "control_response": control_response,
                "candidate_response": candidate_response,
                "candidate_schema_errors": candidate_errors,
                "status": "pass" if not candidate_errors else "schema_rejected",
                **OFFLINE_CONTRACT,
            }
        )
    return results


def build_paired_replay_report(
    *,
    target_date: str,
    requests: list[dict[str, Any]],
    results: list[dict[str, Any]] | None = None,
    labels: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    results = list(results or [])
    label_by_trace = {
        str(row.get("decision_trace_id")): row
        for row in labels or []
        if row.get("source_quality_status") == "pass"
    }
    comparable_rows: list[dict[str, Any]] = []
    for result in results:
        if (
            result.get("status") != "pass"
            or result.get("same_payload_confirmed") is not True
        ):
            continue
        label = label_by_trace.get(str(result.get("decision_trace_id") or ""))
        preferred = _primary_metric(label) if isinstance(label, dict) else None
        preferred = preferred or {}
        outcome = _number(preferred.get("end_return_pct"))
        if outcome is None:
            continue
        control_action = str(
            (result.get("control_response") or {}).get("action") or ""
        ).upper()
        candidate_action = str(
            (result.get("candidate_response") or {}).get("action") or ""
        ).upper()

        control_value = _decision_value(control_action, outcome)
        candidate_value = _decision_value(candidate_action, outcome)
        if control_value is None or candidate_value is None:
            continue
        comparable_rows.append(
            {
                "decision_trace_id": result.get("decision_trace_id"),
                "stage": result.get("stage"),
                "effective_venue": result.get("effective_venue"),
                "session_bucket": result.get("session_bucket"),
                "control_action": control_action,
                "candidate_action": candidate_action,
                "outcome_return_pct": outcome,
                "control_decision_value_pct": control_value,
                "candidate_decision_value_pct": candidate_value,
                "delta_pct": candidate_value - control_value,
                "control_missed_upside": (
                    control_action in NO_EXPOSURE_ACTIONS and outcome > 0
                ),
                "candidate_missed_upside": (
                    candidate_action in NO_EXPOSURE_ACTIONS and outcome > 0
                ),
                "first_hit": preferred.get("first_hit"),
            }
        )
    rejected = sum(row.get("status") != "pass" for row in results)
    completed_pair_ids = {
        str(row.get("paired_replay_id") or "")
        for row in results
        if row.get("paired_replay_id")
    }
    missing_result_count = sum(
        str(row.get("paired_replay_id") or "") not in completed_pair_ids
        for row in requests
    )
    buckets: list[dict[str, Any]] = []
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in comparable_rows:
        grouped[
            (
                str(row.get("stage") or "unknown"),
                str(row.get("effective_venue") or "UNKNOWN"),
                str(row.get("session_bucket") or "UNKNOWN"),
            )
        ].append(row)
    for (stage, venue, session), rows in sorted(grouped.items()):
        buckets.append(
            {
                "stage": stage,
                "effective_venue": venue,
                "session_bucket": session,
                "sample_count": len(rows),
                "control_source_quality_adjusted_ev_pct": fmean(
                    row["control_decision_value_pct"] for row in rows
                ),
                "candidate_source_quality_adjusted_ev_pct": fmean(
                    row["candidate_decision_value_pct"] for row in rows
                ),
                "source_quality_adjusted_ev_delta_pct": fmean(
                    row["delta_pct"] for row in rows
                ),
                "missed_upside_reduction_count": sum(
                    row["control_missed_upside"] and not row["candidate_missed_upside"]
                    for row in rows
                ),
                "adverse_first_candidate_exposure_count": sum(
                    row["first_hit"] == "adverse"
                    and row["candidate_action"] in EXPOSURE_ACTIONS
                    for row in rows
                ),
            }
        )
    status = (
        "candidate_rejected_no_runtime_apply"
        if rejected or (results and missing_result_count)
        else (
            "paired_replay_ready_build_stage_candidate"
            if requests
            else "sample_floor_keep_collecting"
        )
    )
    return {
        "schema": PAIRED_SCHEMA,
        "target_date": target_date,
        "generated_at": datetime.now(KST).isoformat(),
        "status": status,
        "request_count": len(requests),
        "result_count": len(results),
        "schema_rejected_count": rejected,
        "missing_result_count": missing_result_count,
        "paired_comparable_count": len(comparable_rows),
        "control_source_quality_adjusted_ev_pct": (
            fmean(row["control_decision_value_pct"] for row in comparable_rows)
            if comparable_rows
            else None
        ),
        "candidate_source_quality_adjusted_ev_pct": (
            fmean(row["candidate_decision_value_pct"] for row in comparable_rows)
            if comparable_rows
            else None
        ),
        "source_quality_adjusted_ev_delta_pct": (
            fmean(row["delta_pct"] for row in comparable_rows)
            if comparable_rows
            else None
        ),
        "missed_upside_reduction_count": sum(
            row["control_missed_upside"] and not row["candidate_missed_upside"]
            for row in comparable_rows
        ),
        "adverse_first_candidate_exposure_count": sum(
            row["first_hit"] == "adverse"
            and row["candidate_action"] in EXPOSURE_ACTIONS
            for row in comparable_rows
        ),
        "net_profit_status": "not_available_without_notional_and_fill_join",
        "buckets": buckets,
        "paired_comparisons": comparable_rows,
        "requests": requests,
        "results": results,
        **OFFLINE_CONTRACT,
    }


def _default_sources(target_date: str) -> dict[str, list[dict[str, Any]]]:
    traces = _load_jsonl(TRACE_DIR / f"ai_decision_trace_{target_date}.jsonl")
    payloads = _load_jsonl(PAYLOAD_DIR / f"ai_decision_payloads_{target_date}.jsonl")
    pending = _load_jsonl(OUTCOME_DIR / f"ai_decision_outcomes_{target_date}.jsonl")
    target = datetime.strptime(target_date, "%Y-%m-%d").date()
    pipeline = []
    for offset in range(PIPELINE_FORWARD_DAYS + 1):
        source_date = (target + timedelta(days=offset)).isoformat()
        pipeline.extend(
            _load_jsonl(PIPELINE_DIR / f"pipeline_events_{source_date}.jsonl")
        )
    return {
        "traces": traces,
        "payloads": payloads,
        "pending": pending,
        "pipeline": pipeline,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build offline exact AI decision-quality artifacts."
    )
    parser.add_argument("--date", required=True)
    parser.add_argument(
        "--mode",
        choices=("control", "mature", "baseline", "paired"),
        required=True,
    )
    parser.add_argument("--as-of")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    sources = _default_sources(args.date)
    promotion = _load_json(
        RUNTIME_DIR / f"ai_multi_timeframe_context_promotion_{args.date}.json"
    )
    if args.mode == "control":
        report = build_control_manifest(
            target_date=args.date,
            promotion=promotion,
            traces=sources["traces"],
            payloads=sources["payloads"],
        )
        path = control_path(args.date)
    else:
        prices, lifecycle = load_pipeline_price_and_lifecycle_rows(sources["pipeline"])
        as_of = _parse_ts(args.as_of) or datetime.now(KST)
        labels = mature_outcome_labels(
            pending_labels=sources["pending"],
            price_rows=prices,
            lifecycle_rows=lifecycle,
            as_of=as_of,
        )
        labels = annotate_primary_cohort_eligibility(
            labels=labels,
            traces=sources["traces"],
            payloads=sources["payloads"],
            promotion=promotion,
        )
        label_report = {
            "schema": LABEL_REPORT_SCHEMA,
            "target_date": args.date,
            "generated_at": datetime.now(KST).isoformat(),
            "status": (
                "mature_label_rows_available"
                if any(row["label_status"] in {"partial", "mature"} for row in labels)
                else "partial_horizons_keep_maturing"
            ),
            "summary": dict(Counter(row["label_status"] for row in labels)),
            "labels": labels,
            **OFFLINE_CONTRACT,
        }
        if args.mode == "mature":
            report = label_report
            path = label_report_path(args.date)
        elif args.mode == "baseline":
            report = build_quality_baseline(target_date=args.date, labels=labels)
            path = baseline_path(args.date)
        else:
            requests = prepare_paired_replay_requests(
                control_manifest=_load_json(control_path(args.date)),
                traces=sources["traces"],
                payloads=sources["payloads"],
                labels=labels,
            )
            report = build_paired_replay_report(
                target_date=args.date, requests=requests, labels=labels
            )
            path = paired_path(args.date)
    if args.write:
        _atomic_write_json(path, report)
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
