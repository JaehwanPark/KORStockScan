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
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path
from statistics import fmean
from typing import Any, Callable, Iterable
from zoneinfo import ZoneInfo

from src.engine.ai_prompt_contracts import (
    DECISION_QUALITY_DETAILED_PROMPT_VERSION,
    DECISION_QUALITY_V2_PROMPT_VERSION,
    DECISION_QUALITY_V2_RESPONSE_SCHEMA,
    DECISION_QUALITY_V2_REASON_CODES,
    decision_quality_v2_detailed_system_prompt,
    decision_quality_v2_system_prompt,
)
from src.utils.constants import CONFIG_PATH, DATA_DIR, DEV_PATH
from src.utils.jsonl_io import open_text_auto

KST = ZoneInfo("Asia/Seoul")
CONTROL_SCHEMA = "ai_decision_quality_control_v1"
LABEL_REPORT_SCHEMA = "ai_decision_outcome_labels_v1"
BASELINE_SCHEMA = "ai_decision_quality_baseline_v1"
PAIRED_SCHEMA = "ai_prompt_paired_replay_v1"
DETAILED_PAIRED_SCHEMA = "ai_prompt_detailed_paired_replay_v1"
EXACT_PAYLOAD_ANALYSIS_SCHEMA = "exact_payload_analysis_v1"
SCORE_CORRELATION_SCHEMA = "ai_score_outcome_correlation_v1"
RECOVERY_TRIGGER_SCHEMA = "ai_prompt_recovery_trigger_labels_v1"
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
DETAILED_PAIRED_REPORT_DIR = DATA_DIR / "report" / "ai_prompt_detailed_paired_replay"
SCORE_CORRELATION_REPORT_DIR = DATA_DIR / "report" / "ai_score_outcome_correlation"
RECOVERY_TRIGGER_REPORT_DIR = DATA_DIR / "report" / "ai_prompt_recovery_trigger"
PAIRED_REPLAY_MIN_ROWS = 30
PAIRED_REPLAY_MIN_SYMBOLS = 10
PAIRED_CANDIDATE_EXPOSURE_MIN_ROWS = 10
PAIRED_CANDIDATE_EXPOSURE_MIN_SYMBOLS = 3
CANDIDATE_SCHEMA_MAX_ATTEMPTS = 4
RECOVERY_TRIGGER_MIN_ROWS = 15
RECOVERY_TRIGGER_MIN_SYMBOLS = 10
RECOVERY_TRIGGER_WINDOW_MIN = 5
RECOVERY_OUTCOME_HORIZONS_MIN = (1, 3, 5, 10)

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

RECOVERY_TRIGGER_CONTRACT = {
    "metric_role": "ai_decision_quality_recovery_observation",
    "decision_authority": "offline_counterfactual_recovery_attribution_only",
    "window_policy": (
        "exact_snapshot_same_venue_session_completed_bar_recovery_then_forward"
    ),
    "sample_floor": {
        "decision_rows": RECOVERY_TRIGGER_MIN_ROWS,
        "unique_symbols": RECOVERY_TRIGGER_MIN_SYMBOLS,
    },
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "source_quality_gate": ("exact_payload_fresh_same_route_completed_recovery_window"),
    "runtime_effect": False,
    "allowed_runtime_apply": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
    "forbidden_uses": [
        "standalone_live_prompt_promotion",
        "synthetic_order_or_fill_claim",
        "counterfactual_realized_pnl_merge",
        "provider_model_threshold_price_quantity_or_cap_change",
        "broker_or_safety_guard_bypass",
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

REASON_EVIDENCE_KEYS = (
    "trend",
    "liquidity",
    "tape",
    "risk",
    "uncertainty",
    "setup",
    "positive_edge",
    "adverse_risk",
    "trigger",
)
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
    "setup": {
        "continuation",
        "pullback_recovery",
        "reversal",
        "no_setup",
        "not_applicable",
        "insufficient",
    },
    "positive_edge": {"strong", "moderate", "weak", "none", "insufficient"},
    "adverse_risk": {"low", "moderate", "high", "blocking", "insufficient"},
    "trigger": {
        "confirmed",
        "recovery_required",
        "failed",
        "not_applicable",
        "insufficient",
    },
}
MUTUALLY_EXCLUSIVE_REASON_CODE_GROUPS = (
    {"edge_positive", "edge_absent", "no_positive_edge"},
    {"risk_reward_favorable", "risk_reward_unfavorable"},
    {
        "recovery_trigger_confirmed",
        "recovery_trigger_required",
        "recovery_trigger_failed",
    },
)


def control_path(target_date: str) -> Path:
    return RUNTIME_DIR / f"ai_decision_quality_control_{target_date}.json"


def label_report_path(target_date: str) -> Path:
    return LABEL_REPORT_DIR / f"ai_decision_outcome_labels_{target_date}.json"


def baseline_path(target_date: str) -> Path:
    return BASELINE_REPORT_DIR / f"ai_decision_quality_baseline_{target_date}.json"


def paired_path(target_date: str) -> Path:
    return PAIRED_REPORT_DIR / f"ai_prompt_paired_replay_{target_date}.json"


def detailed_paired_path(target_date: str) -> Path:
    return (
        DETAILED_PAIRED_REPORT_DIR
        / f"ai_prompt_detailed_paired_replay_{target_date}.json"
    )


def score_correlation_path(target_date: str) -> Path:
    return (
        SCORE_CORRELATION_REPORT_DIR
        / f"ai_score_outcome_correlation_{target_date}.json"
    )


def recovery_trigger_path(target_date: str) -> Path:
    return (
        RECOVERY_TRIGGER_REPORT_DIR / f"ai_prompt_recovery_trigger_{target_date}.json"
    )


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


def _offline_openai_api_keys() -> list[str]:
    """Load configured OpenAI keys without exposing names or values."""

    target_path = CONFIG_PATH if CONFIG_PATH.exists() else DEV_PATH
    try:
        payload = json.loads(target_path.read_text(encoding="utf-8"))
    except Exception:
        return []
    if not isinstance(payload, dict):
        return []
    return [
        str(value)
        for name, value in sorted(payload.items())
        if str(name).startswith("OPENAI_API_KEY") and value not in (None, "", "-")
    ]


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
            source_quality = (
                candle.get("source_quality")
                if isinstance(candle.get("source_quality"), dict)
                else {}
            )
            decision_window = (
                source_quality.get("decision_window")
                if isinstance(source_quality.get("decision_window"), dict)
                else {}
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
                    "decision_window_status": (
                        str(decision_window.get("status") or "") or None
                    ),
                    "decision_window_provider_call_allowed": decision_window.get(
                        "provider_call_allowed"
                    ),
                    "decision_window_missing_bar_count": decision_window.get(
                        "missing_bar_count"
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
    if (
        str(trace.get("sim_record_id") or "").strip()
        or str(trace.get("position_reconciliation_mode") or "") == "simulation_book"
    ):
        findings.append("simulation_observation_not_natural_cohort")
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
    contexts_with_decision_quality = [
        context
        for context in expected_contexts
        if context.get("decision_window_status") is not None
    ]
    if contexts_with_decision_quality and not any(
        context.get("decision_window_status") == "fresh_consistent"
        and context.get("decision_window_provider_call_allowed") is True
        and (_number(context.get("decision_window_missing_bar_count")) or 0) == 0
        for context in contexts_with_decision_quality
    ):
        findings.append("canonical_decision_window_source_quality_blocked")
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


def _request_code_for_venue(stock_code: Any, effective_venue: Any) -> str | None:
    code = _normalize_stock_code(stock_code)
    venue = _venue(effective_venue)
    if venue == "NXT":
        return f"{code}_NX"
    if venue == "SOR":
        return f"{code}_AL"
    if venue == "KRX":
        return code
    return None


def _venue_session_consistent(effective_venue: Any, session_bucket: Any) -> bool:
    venue = _venue(effective_venue)
    session = _session(session_bucket)
    allowed_sessions = {
        "KRX": {"KRX_REGULAR"},
        "SOR": {"KRX_REGULAR"},
        "NXT": {
            "NXT_PREMARKET",
            "PREMARKET_KRX_LIKE",
            "NXT_REGULAR_OVERLAP",
            "NXT_AFTERMARKET",
        },
    }
    return session in allowed_sessions.get(venue, set())


def _timestamp_in_session(timestamp: datetime, session_bucket: Any) -> bool:
    minute = timestamp.hour * 60 + timestamp.minute
    session = _session(session_bucket)
    if session in {"PREMARKET_KRX_LIKE", "NXT_PREMARKET"}:
        return 8 * 60 <= minute < 9 * 60
    if session == "KRX_REGULAR":
        return 9 * 60 <= minute <= 15 * 60 + 30
    if session == "NXT_REGULAR_OVERLAP":
        return 9 * 60 <= minute <= 15 * 60 + 30
    if session == "NXT_AFTERMARKET":
        return 15 * 60 + 30 < minute <= 20 * 60
    return False


def load_kiwoom_completed_minute_price_rows(
    *,
    target_date: str,
    labels: Iterable[dict[str, Any]],
    as_of: datetime,
    fetcher: Callable[[str, str], tuple[list[dict[str, Any]], dict[str, Any]]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Load completed ka10080 bars for exact label routes.

    ``fetcher`` receives ``(stock_code, request_code)`` so the CLI can use a
    cached read-only token while tests remain network-independent.  Chart bars
    are an offline outcome source only; they never provide runtime quote
    freshness or order authority.
    """

    routes = sorted(
        {
            (
                _normalize_stock_code(row.get("stock_code")),
                _venue(row.get("effective_venue")),
                _session(row.get("session_bucket")),
            )
            for row in labels
            if _normalize_stock_code(row.get("stock_code"))
            and _venue(row.get("effective_venue"))
            and _session(row.get("session_bucket"))
        }
    )
    target_compact = target_date.replace("-", "")
    current_minute = as_of.replace(second=0, microsecond=0)
    prices: list[dict[str, Any]] = []
    provenance: list[dict[str, Any]] = []
    fetch_cache: dict[tuple[str, str], tuple[list[dict[str, Any]], dict[str, Any]]] = {}
    for code, venue, session in routes:
        request_code = _request_code_for_venue(code, venue)
        if request_code is None or not _venue_session_consistent(venue, session):
            provenance.append(
                {
                    "stock_code": code,
                    "effective_venue": venue,
                    "session_bucket": session,
                    "request_code": request_code,
                    "api_id": "ka10080",
                    "received_count": None,
                    "target_completed_bar_count": 0,
                    "coverage_start": None,
                    "coverage_end": None,
                    "continuation_observed": False,
                    "continuation_page_limit_reached": False,
                    "fetch_error": (
                        "unsupported_effective_venue"
                        if request_code is None
                        else "venue_session_conflict"
                    ),
                    "source_quality_status": "source_quality_blocked",
                }
            )
            continue
        fetch_key = (code, request_code)
        if fetch_key not in fetch_cache:
            try:
                fetch_cache[fetch_key] = fetcher(code, request_code)
            except Exception as exc:
                fetch_cache[fetch_key] = (
                    [],
                    {
                        "fetch_error": type(exc).__name__,
                    },
                )
        candles, source_meta = fetch_cache[fetch_key]
        source_meta = source_meta if isinstance(source_meta, dict) else {}
        route_prices: list[dict[str, Any]] = []
        for candle in candles or []:
            source_timestamp = str(candle.get("source_timestamp") or "").strip()
            if (
                len(source_timestamp) < 14
                or not source_timestamp[:14].isdigit()
                or not source_timestamp.startswith(target_compact)
            ):
                continue
            timestamp = _parse_ts(
                datetime.strptime(source_timestamp[:14], "%Y%m%d%H%M%S")
                .replace(tzinfo=KST)
                .isoformat()
            )
            price = _number(candle.get("현재가"))
            open_price = _number(candle.get("시가"))
            high = _number(candle.get("고가"))
            low = _number(candle.get("저가"))
            if (
                timestamp is None
                or price is None
                or price <= 0
                or timestamp.replace(second=0, microsecond=0) >= current_minute
                or not _timestamp_in_session(timestamp, session)
            ):
                continue
            route_prices.append(
                {
                    "timestamp": timestamp.isoformat(),
                    "stock_code": code,
                    "price": price,
                    "open": (
                        open_price
                        if open_price is not None and open_price > 0
                        else None
                    ),
                    "high": high if high is not None and high > 0 else price,
                    "low": low if low is not None and low > 0 else price,
                    "close": price,
                    "effective_venue": venue,
                    "session_bucket": session,
                    "source_quality": "pass_completed_ka10080_bar",
                    "source_api_id": "ka10080",
                    "source_request_code": request_code,
                    "source_time_basis": "ka10080_cntr_tm_bar_timestamp",
                    "completed_bar_only": True,
                }
            )
        prices.extend(route_prices)
        timestamps = [row["timestamp"] for row in route_prices]
        provenance.append(
            {
                "stock_code": code,
                "effective_venue": venue,
                "session_bucket": session,
                "request_code": request_code,
                "api_id": source_meta.get("api_id") or "ka10080",
                "received_count": source_meta.get("received_count"),
                "target_completed_bar_count": len(route_prices),
                "coverage_start": min(timestamps) if timestamps else None,
                "coverage_end": max(timestamps) if timestamps else None,
                "continuation_observed": bool(source_meta.get("cont_yn_seen")),
                "continuation_page_limit_reached": bool(
                    source_meta.get("continuous_page_limit_reached")
                ),
                "fetch_error": source_meta.get("fetch_error"),
                "source_quality_status": (
                    "pass_target_window_available"
                    if route_prices
                    else "source_quality_blocked"
                ),
            }
        )
    return prices, provenance


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
        key=lambda row: (
            _parse_ts(row.get("timestamp")) or datetime.min.replace(tzinfo=KST)
        )
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
        high = _number(row.get("high"))
        low = _number(row.get("low"))
        close = _number(row.get("close"))
        code = _normalize_stock_code(row.get("stock_code"))
        if timestamp and price and price > 0 and code:
            prices_by_code[code].append(
                {
                    **row,
                    "_timestamp": timestamp,
                    "_price": price,
                    "_high": high if high is not None and high > 0 else price,
                    "_low": low if low is not None and low > 0 else price,
                    "_close": close if close is not None and close > 0 else price,
                }
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
            high_returns = [
                round(((row["_high"] / reference) - 1.0) * 100.0, 10) for row in window
            ]
            low_returns = [
                round(((row["_low"] / reference) - 1.0) * 100.0, 10) for row in window
            ]
            end_return = round(((window[-1]["_close"] / reference) - 1.0) * 100.0, 10)
            target_price = _number(pending.get("target_price"))
            adverse_price = _number(pending.get("adverse_price"))
            target_hit = next(
                (
                    row["_timestamp"].isoformat()
                    for row in window
                    if target_price is not None and row["_high"] >= target_price
                ),
                None,
            )
            adverse_hit = next(
                (
                    row["_timestamp"].isoformat()
                    for row in window
                    if adverse_price is not None and row["_low"] <= adverse_price
                ),
                None,
            )
            first_hit = (
                "ambiguous_same_bar"
                if target_hit and adverse_hit and target_hit == adverse_hit
                else (
                    "target"
                    if target_hit and (not adverse_hit or target_hit < adverse_hit)
                    else ("adverse" if adverse_hit else "neither")
                )
            )
            horizon_metrics[f"{horizon}m"] = {
                "sample_count": len(window),
                "mfe_pct": max(high_returns),
                "mae_pct": min(low_returns),
                "end_return_pct": end_return,
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


def _average_ranks(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=values.__getitem__)
    ranks = [0.0] * len(values)
    index = 0
    while index < len(order):
        end = index + 1
        while end < len(order) and values[order[end]] == values[order[index]]:
            end += 1
        average_rank = (index + 1 + end) / 2.0
        for position in range(index, end):
            ranks[order[position]] = average_rank
        index = end
    return ranks


def _pearson(values_x: list[float], values_y: list[float]) -> float | None:
    if len(values_x) != len(values_y) or len(values_x) < 2:
        return None
    mean_x = fmean(values_x)
    mean_y = fmean(values_y)
    variance_x = sum((value - mean_x) ** 2 for value in values_x)
    variance_y = sum((value - mean_y) ** 2 for value in values_y)
    if variance_x <= 0 or variance_y <= 0:
        return None
    covariance = sum(
        (value_x - mean_x) * (value_y - mean_y)
        for value_x, value_y in zip(values_x, values_y)
    )
    return covariance / math.sqrt(variance_x * variance_y)


def _correlation_pair(
    values_x: list[float], values_y: list[float]
) -> dict[str, float | None]:
    return {
        "spearman": _pearson(_average_ranks(values_x), _average_ranks(values_y)),
        "pearson": _pearson(values_x, values_y),
    }


def build_score_outcome_correlation_report(
    *,
    target_date: str,
    labels: Iterable[dict[str, Any]],
    price_source_provenance: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Measure exact-v2 AI score association with forward MFE and MAE."""

    grouped: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    eligible_label_count = 0
    for row in labels:
        if (
            row.get("primary_cohort_eligible") is not True
            or row.get("source_quality_status") != "pass"
        ):
            continue
        score = _number(row.get("score"))
        metrics = row.get("horizon_metrics")
        if score is None or not isinstance(metrics, dict):
            continue
        eligible_label_count += 1
        for horizon in HORIZONS_MIN:
            metric = metrics.get(f"{horizon}m")
            if not isinstance(metric, dict):
                continue
            mfe = _number(metric.get("mfe_pct"))
            mae = _number(metric.get("mae_pct"))
            if mfe is None or mae is None:
                continue
            grouped[
                (
                    _stage(row.get("decision_stage")),
                    _venue(row.get("effective_venue")),
                    _session(row.get("session_bucket")),
                    f"{horizon}m",
                )
            ].append(
                {
                    "stock_code": _normalize_stock_code(row.get("stock_code")),
                    "score": score,
                    "mfe_pct": mfe,
                    "mae_pct": mae,
                }
            )
    buckets: list[dict[str, Any]] = []
    ready_bucket_count = 0
    grouped_items = sorted(
        grouped.items(),
        key=lambda item: (
            item[0][0],
            item[0][1],
            item[0][2],
            int(item[0][3].removesuffix("m")),
        ),
    )
    for (stage, venue, session, horizon), rows in grouped_items:
        scores = [row["score"] for row in rows]
        mfe_values = [row["mfe_pct"] for row in rows]
        mae_values = [row["mae_pct"] for row in rows]
        adverse_magnitudes = [abs(min(0.0, value)) for value in mae_values]
        symbol_count = len({row["stock_code"] for row in rows})
        sample_floor_pass = len(rows) >= 30 and symbol_count >= 10
        if sample_floor_pass:
            ready_bucket_count += 1
        buckets.append(
            {
                "decision_stage": stage,
                "effective_venue": venue,
                "session_bucket": session,
                "horizon": horizon,
                "sample_count": len(rows),
                "symbol_count": symbol_count,
                "distinct_score_count": len(set(scores)),
                "sample_floor_pass": sample_floor_pass,
                "inference_status": (
                    "exploratory_repeated_symbol_calls"
                    if sample_floor_pass
                    else "sample_floor_keep_collecting"
                ),
                "score_vs_mfe_pct": _correlation_pair(scores, mfe_values),
                "score_vs_mae_pct": _correlation_pair(scores, mae_values),
                "score_vs_adverse_magnitude_pct": _correlation_pair(
                    scores, adverse_magnitudes
                ),
                "interpretation_contract": {
                    "mfe_preferred_direction": "positive",
                    "mae_pct_preferred_direction": "positive_toward_zero",
                    "adverse_magnitude_preferred_direction": "negative",
                    "primary_coefficient": "spearman",
                    "pearson_role": "diagnostic_only",
                },
            }
        )
    return {
        "schema": SCORE_CORRELATION_SCHEMA,
        "target_date": target_date,
        "generated_at": datetime.now(KST).isoformat(),
        "status": (
            "exploratory_score_outcome_correlation_available"
            if ready_bucket_count
            else "sample_floor_keep_collecting"
        ),
        "eligible_label_count": eligible_label_count,
        "bucket_count": len(buckets),
        "sample_floor_ready_bucket_count": ready_bucket_count,
        "sample_floor": {
            "decision_rows": 30,
            "unique_symbols": 10,
            "significance_authority": False,
            "reason": "same_symbol_repeated_calls_are_not_independent",
        },
        "price_source_provenance": list(price_source_provenance or []),
        "buckets": buckets,
        **OFFLINE_CONTRACT,
    }


def _window_value(values: Any, horizon: int) -> float | None:
    if not isinstance(values, dict):
        return None
    return _number(values.get(str(horizon), values.get(horizon)))


def _entry_contract_facts(exact_payload: Any) -> dict[str, bool]:
    exact_payload_supplied = isinstance(exact_payload, dict)
    payload = exact_payload if isinstance(exact_payload, dict) else {}
    context = payload.get("entry_candle_context")
    context = context if isinstance(context, dict) else {}
    structure = context.get("structure")
    structure = structure if isinstance(structure, dict) else {}
    returns = structure.get("returns_pct")
    slopes = structure.get("slopes_pct_per_bar")
    structural_horizons = (5, 10, 20, 60)
    positive_return_count = sum(
        (_window_value(returns, horizon) or 0) > 0 for horizon in structural_horizons
    )
    positive_slope_count = sum(
        (_window_value(slopes, horizon) or 0) > 0 for horizon in structural_horizons
    )
    structural_edge_floor = positive_return_count >= 3 and positive_slope_count >= 2
    features = payload.get("features")
    features = features if isinstance(features, dict) else {}
    current = payload.get("current")
    current = current if isinstance(current, dict) else {}
    daily_runup = _number(current.get("fluctuation_pct"))
    micro_vwap_bp = _number(features.get("curr_vs_micro_vwap_bp"))
    ma5_bp = _number(features.get("curr_vs_ma5_bp"))
    tape_status = str(features.get("entry_order_flow_status") or "").lower()
    tape_source = str(features.get("order_flow_pressure_source") or "").lower()
    momentum_status = str(features.get("entry_momentum_status") or "").lower()
    buy_pressure = _number(features.get("buy_pressure_10t"))
    net_aggressive_delta = _number(features.get("net_aggressive_delta_10t"))
    trusted_tick_count = _number(features.get("tick_aggressor_trusted_count"))
    trusted_tape_usable = features.get("tick_aggressor_pressure_usable") is True
    quote_fresh = features.get("quote_fresh_for_entry") is True
    tick_fresh = features.get("tick_context_stale") is False
    large_sell_print_absent = features.get("large_sell_print_detected") is False
    tick_context_quality = str(features.get("tick_context_quality") or "").lower()
    tick_accel_source = str(features.get("tick_accel_source") or "").lower()
    thin_tape_sample = bool(
        (exact_payload_supplied and trusted_tick_count is None)
        or (trusted_tick_count is not None and trusted_tick_count < 10)
        or "insufficient_ticks" in tick_context_quality
        or tick_accel_source == "insufficient_ticks"
    )
    blocking_overextension = bool(
        structural_edge_floor
        and daily_runup is not None
        and daily_runup >= 15
        and micro_vwap_bp is not None
        and micro_vwap_bp >= 80
        and ma5_bp is not None
        and ma5_bp >= 80
        and tape_status != "supportive"
    )
    regime = str(structure.get("regime") or "").lower()
    alignment = str(structure.get("alignment") or "").lower()
    latest_recovery = (_window_value(returns, 1) or 0) > 0 or (
        _window_value(returns, 3) or 0
    ) > 0
    trusted_supportive_trigger = bool(
        structural_edge_floor
        and not blocking_overextension
        and latest_recovery
        and tape_status == "supportive"
        and tape_source == "trusted_aggressor"
        and momentum_status == "accelerating"
        and buy_pressure is not None
        and buy_pressure >= 60
        and net_aggressive_delta is not None
        and net_aggressive_delta > 0
        and trusted_tape_usable
        and trusted_tick_count is not None
        and trusted_tick_count >= 10
        and not thin_tape_sample
        and quote_fresh
        and tick_fresh
        and large_sell_print_absent
    )
    orderly_pullback_recovery = bool(
        structural_edge_floor
        and not blocking_overextension
        and micro_vwap_bp is not None
        and micro_vwap_bp < 0
        and ma5_bp is not None
        and ma5_bp < 0
        and tape_status in {"adverse", "mixed", "neutral", "unknown"}
        and latest_recovery
        and regime not in {"failed_breakout", "breakdown"}
        and alignment != "adverse"
    )
    return_5m = _window_value(returns, 5)
    return_10m = _window_value(returns, 10)
    peak_drawdown = _number(structure.get("peak_drawdown_pct"))
    high_direction = str(structure.get("high_direction") or "").lower()
    volume_ratio = _number(structure.get("volume_ratio"))
    volume_alignment = str(structure.get("volume_direction_alignment") or "").lower()
    adverse_distribution_no_edge = bool(
        not structural_edge_floor
        and return_5m is not None
        and return_5m <= -0.5
        and return_10m is not None
        and return_10m <= -1.0
        and peak_drawdown is not None
        and peak_drawdown <= -2.0
        and high_direction == "down"
        and (
            (volume_ratio is not None and volume_ratio <= 0.5)
            or volume_alignment == "price_volume_divergence"
        )
    )
    spread_bp = _number(features.get("spread_bp"))
    top1_bid_notional = _number(features.get("top1_bid_notional"))
    top1_ask_notional = _number(features.get("top1_ask_notional"))
    ask_wall_wide_spread = bool(
        spread_bp is not None
        and spread_bp >= 50
        and top1_bid_notional is not None
        and top1_bid_notional > 0
        and top1_ask_notional is not None
        and top1_ask_notional / top1_bid_notional >= 5
    )
    return {
        "structural_edge_floor": structural_edge_floor,
        "blocking_overextension": blocking_overextension,
        "orderly_pullback_recovery": orderly_pullback_recovery,
        "trusted_supportive_trigger": trusted_supportive_trigger,
        "thin_tape_sample": thin_tape_sample,
        "adverse_distribution_no_edge": adverse_distribution_no_edge,
        "ask_wall_wide_spread": ask_wall_wide_spread,
    }


def build_exact_payload_analysis_v1(
    exact_payload: Any,
    *,
    stage: str,
    live_entry: bool = False,
) -> dict[str, Any]:
    """Build a deterministic, non-authoritative evidence ledger."""

    if live_entry and str(stage or "").strip().lower() != "entry":
        raise ValueError("live exact-payload analysis supports entry stage only")
    payload = exact_payload if isinstance(exact_payload, dict) else {}
    current = payload.get("current")
    current = current if isinstance(current, dict) else {}
    features = payload.get("features")
    features = features if isinstance(features, dict) else {}
    candle = payload.get("entry_candle_context")
    candle = candle if isinstance(candle, dict) else {}
    structure = candle.get("structure")
    structure = structure if isinstance(structure, dict) else {}
    returns = structure.get("returns_pct")
    returns = returns if isinstance(returns, dict) else {}
    slopes = structure.get("slopes_pct_per_bar")
    slopes = slopes if isinstance(slopes, dict) else {}
    horizons = (1, 3, 5, 10, 20, 60)
    normalized_returns = {
        f"{horizon}m": _window_value(returns, horizon) for horizon in horizons
    }
    normalized_slopes = {
        f"{horizon}m": _window_value(slopes, horizon) for horizon in horizons
    }
    facts = _entry_contract_facts(payload) if str(stage).lower() == "entry" else {}
    completed_bar_count = _number(candle.get("completed_bar_count"))
    if completed_bar_count is None:
        completed_bar_count = float(
            sum(
                isinstance(row, dict) and not bool(row.get("forming", False))
                for row in candle.get("bars") or []
            )
        )
    forming_bar_count = sum(
        isinstance(row, dict) and bool(row.get("forming", False))
        for row in candle.get("bars") or []
    )
    current_price = _number(current.get("price"))
    trusted_tick_count = _number(features.get("tick_aggressor_trusted_count"))
    net_aggressive_delta = _number(features.get("net_aggressive_delta_10t"))
    tape_notional = (
        abs(net_aggressive_delta) * current_price
        if net_aggressive_delta is not None
        and current_price is not None
        and current_price > 0
        else None
    )
    tape_status = str(features.get("entry_order_flow_status") or "unknown").lower()
    tape_sample_sufficient = bool(
        trusted_tick_count is not None
        and trusted_tick_count >= 10
        and "insufficient_ticks"
        not in str(features.get("tick_context_quality") or "").lower()
        and str(features.get("tick_accel_source") or "").lower() != "insufficient_ticks"
    )
    spread_bp = _number(features.get("spread_bp"))
    top1_bid_notional = _number(features.get("top1_bid_notional"))
    top1_ask_notional = _number(features.get("top1_ask_notional"))
    top1_ask_to_bid_ratio = (
        top1_ask_notional / top1_bid_notional
        if top1_ask_notional is not None
        and top1_bid_notional is not None
        and top1_bid_notional > 0
        else None
    )
    if facts.get("ask_wall_wide_spread"):
        liquidity_state = "blocking"
    elif spread_bp is None:
        liquidity_state = "insufficient"
    elif spread_bp >= 30 or (
        top1_ask_to_bid_ratio is not None and top1_ask_to_bid_ratio >= 2
    ):
        liquidity_state = "adverse"
    elif spread_bp <= 15 and (
        top1_ask_to_bid_ratio is None or top1_ask_to_bid_ratio <= 1.5
    ):
        liquidity_state = "supportive"
    else:
        liquidity_state = "mixed"
    volume_ratio = _number(structure.get("volume_ratio"))
    volume_alignment = str(
        structure.get("volume_direction_alignment") or "unknown"
    ).lower()
    if volume_alignment == "price_volume_divergence" or (
        volume_ratio is not None and volume_ratio <= 0.5
    ):
        volume_state = "confirmation_absent"
    elif volume_ratio is not None and volume_ratio >= 1.0:
        volume_state = "confirmed"
    elif volume_ratio is None:
        volume_state = "insufficient"
    else:
        volume_state = "mixed"
    return_1m = normalized_returns["1m"]
    return_3m = normalized_returns["3m"]
    if facts.get("adverse_distribution_no_edge"):
        structure_phase = "distribution"
        structural_edge = "absent"
    elif str(structure.get("regime") or "").lower() in {
        "failed_breakout",
        "breakdown",
    }:
        structure_phase = "failed_breakout"
        structural_edge = "moderate" if facts.get("structural_edge_floor") else "absent"
    elif facts.get("structural_edge_floor") and (
        (return_1m or 0) > 0 or (return_3m or 0) > 0
    ):
        structure_phase = "continuation"
        structural_edge = "moderate"
    elif facts.get("structural_edge_floor"):
        structure_phase = "pullback"
        structural_edge = "moderate"
    elif (
        (normalized_returns["5m"] or 0) < 0
        and (normalized_returns["10m"] or 0) < 0
        and ((return_1m or 0) > 0 or (return_3m or 0) > 0)
    ):
        structure_phase = "rebound_attempt"
        structural_edge = "weak"
    else:
        structure_phase = "range_or_no_setup"
        structural_edge = "weak"
    contradictions: list[str] = []
    if tape_status == "supportive" and not tape_sample_sufficient:
        contradictions.append("supportive_tape_ratio_from_thin_sample")
    if tape_status == "supportive" and facts.get("adverse_distribution_no_edge"):
        contradictions.append("supportive_micro_tape_vs_adverse_distribution")
    if facts.get("structural_edge_floor") and liquidity_state == "blocking":
        contradictions.append("structural_edge_vs_blocking_liquidity")
    return_signs = {
        "positive" if value > 0 else "negative" if value < 0 else "flat"
        for value in normalized_returns.values()
        if value is not None
    }
    if "positive" in return_signs and "negative" in return_signs:
        contradictions.append("multi_horizon_direction_conflict")
    snapshot = payload.get("ai_market_snapshot_v1")
    snapshot = snapshot if isinstance(snapshot, dict) else {}
    sources = snapshot.get("sources")
    sources = sources if isinstance(sources, dict) else {}
    program = sources.get("program")
    program = program if isinstance(program, dict) else {}
    program_value = program.get("value")
    program_value = program_value if isinstance(program_value, dict) else {}
    program_net_qty = _number(program_value.get("net_qty"))
    if (
        tape_status == "supportive"
        and program_net_qty is not None
        and program_net_qty < 0
    ):
        contradictions.append("supportive_micro_tape_vs_program_net_sell")
    if facts.get("adverse_distribution_no_edge"):
        trigger_state = "failed"
    elif facts.get("trusted_supportive_trigger"):
        trigger_state = "confirmed"
    elif facts.get("orderly_pullback_recovery"):
        trigger_state = "recovery_required"
    elif not tape_sample_sufficient:
        trigger_state = "insufficient_tape_confirmation"
    else:
        trigger_state = "unconfirmed"
    source_quality = candle.get("source_quality")
    source_quality = source_quality if isinstance(source_quality, dict) else {}
    analysis = {
        "schema": EXACT_PAYLOAD_ANALYSIS_SCHEMA,
        "stage": str(stage or "unknown"),
        "source_quality": {
            "status": source_quality.get("status"),
            "completed_bar_count": int(completed_bar_count),
            "forming_bar_count": forming_bar_count,
            "forming_bar_excluded": structure.get("forming_bar_excluded"),
            "risk_flags": list(candle.get("risk_flags") or []),
        },
        "completed_structure": {
            "phase": structure_phase,
            "structural_edge": structural_edge,
            "returns_pct": normalized_returns,
            "slopes_pct_per_bar": normalized_slopes,
            "peak_drawdown_pct": _number(structure.get("peak_drawdown_pct")),
            "high_direction": structure.get("high_direction"),
            "low_direction": structure.get("low_direction"),
            "regime": structure.get("regime"),
            "alignment": structure.get("alignment"),
        },
        "volume_confirmation": {
            "state": volume_state,
            "volume_ratio": volume_ratio,
            "alignment": volume_alignment,
        },
        "tape_sample": {
            "state": "sufficient" if tape_sample_sufficient else "too_thin",
            "raw_status": tape_status,
            "trusted_tick_count": trusted_tick_count,
            "buy_pressure_pct": _number(features.get("buy_pressure_10t")),
            "net_aggressive_delta_shares": net_aggressive_delta,
            "net_aggressive_notional_krw": tape_notional,
            "tick_context_quality": features.get("tick_context_quality"),
            "tick_accel_source": features.get("tick_accel_source"),
        },
        "executable_liquidity": {
            "state": liquidity_state,
            "spread_bp": spread_bp,
            "top1_bid_notional": top1_bid_notional,
            "top1_ask_notional": top1_ask_notional,
            "top1_ask_to_bid_ratio": top1_ask_to_bid_ratio,
            "fillability_score": _number(features.get("fillability_score")),
            "would_fill_now": features.get("would_fill_now"),
        },
        "program_flow": {
            "net_qty": program_net_qty,
            "source": program.get("source"),
        },
        "trigger_state": trigger_state,
        "contradictions": contradictions,
        "deterministic_contract_facts": facts,
        "observation_contract": {
            "metric_role": "ai_input_feature_analysis",
            "decision_authority": (
                "operator_directed_live_entry_prompt_input"
                if live_entry
                else "offline_replay_evidence_organization_only"
            ),
            "window_policy": "same_exact_payload_completed_bar_snapshot",
            "sample_floor": "one_exact_payload_with_completed_bar",
            "primary_decision_metric": "source_quality_adjusted_ev_pct",
            "source_quality_gate": "exact_payload_fresh_same_route",
            "runtime_effect": live_entry,
            "allowed_runtime_apply": live_entry,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "forbidden_uses": (
                (
                    "direct_order_submission|provider_change|"
                    "threshold_price_quantity_change|broker_guard_bypass|"
                    "safety_guard_bypass"
                )
                if live_entry
                else (
                    "standalone_live_action|runtime_prompt_promotion|"
                    "provider_change|threshold_price_quantity_change|"
                    "broker_guard_bypass|bot_restart"
                )
            ),
        },
    }
    analysis["analysis_sha256"] = _sha256(analysis)
    return analysis


def validate_candidate_response(
    response: dict[str, Any],
    *,
    stage: str,
    exact_payload: Any = None,
) -> list[str]:
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
    expected_values: dict[str, float | None] = {}
    for field in ("expected_upside_pct", "expected_downside_pct"):
        if field not in response:
            errors.append(f"{field}_missing")
            expected_values[field] = None
        elif response.get(field) is None:
            expected_values[field] = None
        else:
            expected_values[field] = _number(response.get(field))
            if expected_values[field] is None:
                errors.append(f"{field}_invalid")
    edge_state = str(response.get("edge_state") or "")
    if edge_state in {"EDGE", "NO_EDGE"} and any(
        expected_values.get(field) is None
        for field in ("expected_upside_pct", "expected_downside_pct")
    ):
        errors.append("expected_edge_values_required")
    if edge_state == "INSUFFICIENT_DATA" and any(
        response.get(field) is not None
        for field in ("expected_upside_pct", "expected_downside_pct")
    ):
        errors.append("insufficient_data_expected_values_must_be_null")
    upside = expected_values.get("expected_upside_pct")
    downside = expected_values.get("expected_downside_pct")
    if upside is not None and upside < 0:
        errors.append("expected_upside_pct_negative")
    if downside is not None and downside > 0:
        errors.append("expected_downside_pct_positive")
    confidence = _number(response.get("confidence"))
    if confidence is None or not 0 <= confidence <= 100:
        errors.append("confidence_invalid")
    codes = response.get("reason_codes")
    reason_code_set = set(map(str, codes)) if isinstance(codes, list) else set()
    if (
        not isinstance(codes, list)
        or not codes
        or len(codes) != len(set(map(str, codes)))
        or any(
            not REASON_CODE_PATTERN.fullmatch(str(code))
            or str(code) not in DECISION_QUALITY_V2_REASON_CODES
            for code in codes
        )
    ):
        errors.append("reason_codes_invalid")
    elif any(
        len(set(map(str, codes)) & group) > 1
        for group in MUTUALLY_EXCLUSIVE_REASON_CODE_GROUPS
    ):
        errors.append("reason_codes_conflict")
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
        if normalized_stage == "entry":
            positive_edge = str(evidence.get("positive_edge") or "").lower()
            adverse_risk = str(evidence.get("adverse_risk") or "").lower()
            trigger = str(evidence.get("trigger") or "").lower()
            setup = str(evidence.get("setup") or "").lower()
            trigger_reason_requirements = {
                "recovery_trigger_confirmed": "confirmed",
                "recovery_trigger_required": "recovery_required",
                "recovery_trigger_failed": "failed",
            }
            if any(
                reason_code in reason_code_set and trigger != required_trigger
                for reason_code, required_trigger in trigger_reason_requirements.items()
            ) or (
                "structural_edge_without_trigger" in reason_code_set
                and trigger == "confirmed"
            ):
                errors.append("entry_trigger_reason_evidence_conflict")
            if edge_state == "INSUFFICIENT_DATA":
                if action != "WAIT":
                    errors.append("entry_insufficient_requires_wait")
                if (
                    positive_edge != "insufficient"
                    or adverse_risk != "insufficient"
                    or trigger != "insufficient"
                    or setup != "insufficient"
                ):
                    errors.append("entry_insufficient_evidence_invalid")
            elif edge_state == "NO_EDGE":
                if action != "DROP":
                    errors.append("entry_no_edge_requires_drop")
                if positive_edge not in {"none", "weak"}:
                    errors.append("entry_no_edge_strength_invalid")
                if setup not in {"no_setup", "not_applicable"}:
                    errors.append("entry_no_edge_setup_invalid")
            elif edge_state == "EDGE":
                if positive_edge not in {"moderate", "strong"}:
                    errors.append("entry_edge_strength_invalid")
                if action == "BUY":
                    if trigger != "confirmed":
                        errors.append("entry_buy_requires_confirmed_trigger")
                    if adverse_risk not in {"low", "moderate"}:
                        errors.append("entry_buy_adverse_risk_too_high")
                    if (
                        upside is not None
                        and downside is not None
                        and (downside >= 0 or upside / abs(downside) < 1.25)
                    ):
                        errors.append("entry_buy_reward_risk_below_floor")
                elif action == "WAIT":
                    if trigger != "recovery_required":
                        errors.append("entry_wait_requires_recovery_trigger")
                    if adverse_risk in {"blocking", "insufficient"}:
                        errors.append("entry_wait_adverse_risk_invalid")
                elif action == "DROP":
                    reward_risk_unfavorable = (
                        upside is not None
                        and downside is not None
                        and downside < 0
                        and upside / abs(downside) < 1.25
                    )
                    if not (
                        trigger == "failed"
                        or adverse_risk == "blocking"
                        or reward_risk_unfavorable
                    ):
                        errors.append(
                            "entry_edge_drop_requires_failed_blocking_or_unfavorable"
                        )
            contract_facts = _entry_contract_facts(exact_payload)
            if contract_facts["structural_edge_floor"]:
                if edge_state != "EDGE" or positive_edge not in {
                    "moderate",
                    "strong",
                }:
                    errors.append("entry_structural_edge_floor_misclassified")
            if contract_facts["blocking_overextension"]:
                if adverse_risk != "blocking" or action != "DROP":
                    errors.append("entry_blocking_overextension_misclassified")
            if contract_facts["orderly_pullback_recovery"]:
                if (
                    setup != "pullback_recovery"
                    or trigger != "recovery_required"
                    or action != "WAIT"
                    or adverse_risk in {"blocking", "insufficient"}
                ):
                    errors.append("entry_orderly_pullback_recovery_misclassified")
            if contract_facts["trusted_supportive_trigger"]:
                if (
                    edge_state != "EDGE"
                    or positive_edge not in {"moderate", "strong"}
                    or str(evidence.get("tape") or "").lower() != "supportive"
                    or trigger != "confirmed"
                    or action == "WAIT"
                ):
                    errors.append("entry_trusted_supportive_trigger_misclassified")
            if edge_state != "INSUFFICIENT_DATA" and contract_facts["thin_tape_sample"]:
                if (
                    str(evidence.get("tape") or "").lower() == "supportive"
                    or trigger == "confirmed"
                ):
                    errors.append("entry_thin_tape_sample_overstated")
            if (
                edge_state != "INSUFFICIENT_DATA"
                and contract_facts["adverse_distribution_no_edge"]
            ):
                if (
                    edge_state != "NO_EDGE"
                    or action != "DROP"
                    or str(evidence.get("trend") or "").lower() != "adverse"
                    or setup != "no_setup"
                    or trigger not in {"failed", "not_applicable"}
                    or not {
                        "distribution_adverse",
                        "volume_confirmation_missing",
                    }.issubset(reason_code_set)
                ):
                    errors.append("entry_adverse_distribution_misclassified")
            if (
                edge_state != "INSUFFICIENT_DATA"
                and contract_facts["ask_wall_wide_spread"]
            ):
                if (
                    str(evidence.get("liquidity") or "").lower() != "adverse"
                    or adverse_risk not in {"high", "blocking"}
                    or action == "BUY"
                    or not {
                        "ask_wall_adverse",
                        "liquidity_adverse",
                    }.intersection(reason_code_set)
                ):
                    errors.append("entry_ask_wall_wide_spread_misclassified")
    if normalized_stage not in STAGE_ACTIONS:
        errors.append("stage_unsupported")
    return errors


def _prompt_v2_openai_schema(stage: str) -> dict[str, Any]:
    normalized_stage = str(stage or "").strip().lower()
    actions = sorted(STAGE_ACTIONS.get(normalized_stage, set()))
    if not actions:
        raise ValueError(f"unsupported decision-quality stage: {stage}")
    evidence_properties = {
        key: {"type": "string", "enum": sorted(values)}
        for key, values in EVIDENCE_VALUES.items()
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "edge_state",
            "action",
            "expected_upside_pct",
            "expected_downside_pct",
            "confidence",
            "reason_codes",
            "evidence",
        ],
        "properties": {
            "edge_state": {
                "type": "string",
                "enum": ["EDGE", "NO_EDGE", "INSUFFICIENT_DATA"],
            },
            "action": {"type": "string", "enum": actions},
            "expected_upside_pct": {
                "type": ["number", "null"],
                "minimum": 0,
            },
            "expected_downside_pct": {
                "type": ["number", "null"],
                "maximum": 0,
            },
            "confidence": {"type": "integer", "minimum": 0, "maximum": 100},
            "reason_codes": {
                "type": "array",
                "minItems": 1,
                "maxItems": 8,
                "items": {
                    "type": "string",
                    "enum": list(DECISION_QUALITY_V2_REASON_CODES),
                },
            },
            "evidence": {
                "type": "object",
                "additionalProperties": False,
                "required": list(REASON_EVIDENCE_KEYS),
                "properties": evidence_properties,
            },
        },
    }


def _candidate_contract_sha256(candidate: dict[str, Any]) -> str:
    contract = {
        "prompt_version": candidate.get("prompt_version"),
        "system_prompt_sha256": candidate.get("system_prompt_sha256"),
        "response_schema_sha256": candidate.get("response_schema_sha256"),
    }
    if candidate.get("analysis_schema") is not None:
        contract["analysis_schema"] = candidate.get("analysis_schema")
        contract["analysis_schema_sha256"] = candidate.get("analysis_schema_sha256")
    return _sha256(contract)


def _openai_output_text(response: Any) -> str:
    direct = getattr(response, "output_text", None)
    if direct not in (None, ""):
        return str(direct)
    if isinstance(response, dict):
        direct = response.get("output_text")
        if direct not in (None, ""):
            return str(direct)
    output = getattr(response, "output", None)
    if output is None and isinstance(response, dict):
        output = response.get("output")
    parts: list[str] = []
    for item in output or []:
        content = getattr(item, "content", None)
        if content is None and isinstance(item, dict):
            content = item.get("content")
        for block in content or []:
            text_value = getattr(block, "text", None)
            if text_value is None and isinstance(block, dict):
                text_value = block.get("text")
            if text_value not in (None, ""):
                parts.append(str(text_value))
    return "\n".join(parts)


def _usage_value(value: Any, field: str) -> int | None:
    usage = getattr(value, "usage", None)
    if usage is None and isinstance(value, dict):
        usage = value.get("usage")
    raw = getattr(usage, field, None)
    if raw is None and isinstance(usage, dict):
        raw = usage.get(field)
    try:
        return int(raw) if raw is not None else None
    except (TypeError, ValueError):
        return None


def execute_openai_prompt_v2_candidate(
    request: dict[str, Any],
    *,
    api_keys: list[str] | None = None,
    timeout_sec: float = 45.0,
) -> dict[str, Any]:
    """Run one exact-payload Prompt V2 candidate with no runtime authority."""

    if any(
        (
            request.get("runtime_effect") is not False,
            request.get("allowed_runtime_apply") is not False,
            request.get("actual_order_submitted") is not False,
            request.get("broker_order_forbidden") is not True,
        )
    ):
        raise ValueError("offline_authority_contract_invalid")
    control = request.get("control") or {}
    candidate = request.get("candidate") or {}
    provider = str(candidate.get("provider") or "").strip().lower()
    model = str(candidate.get("model") or "").strip()
    if (
        provider != "openai"
        or provider != str(control.get("provider") or "").strip().lower()
        or model != str(control.get("model") or "").strip()
    ):
        raise ValueError("provider_or_model_control_mismatch")
    keys = list(api_keys or _offline_openai_api_keys())
    if not keys:
        raise RuntimeError("openai_api_key_unavailable")
    try:
        from openai import OpenAI
    except Exception as exc:
        raise RuntimeError("openai_sdk_unavailable") from exc

    pair_id = str(request.get("paired_replay_id") or "")
    key_index = int(hashlib.sha256(pair_id.encode("utf-8")).hexdigest(), 16) % len(keys)
    exact_payload = request.get("candidate_input", request.get("exact_payload"))
    user_input = (
        exact_payload
        if isinstance(exact_payload, str)
        else _canonical_bytes(exact_payload).decode("utf-8")
    )
    if not user_input:
        raise ValueError("exact_payload_missing")
    stage = str(request.get("stage") or "")
    instructions = str(candidate.get("system_prompt") or "")
    correction_errors = [
        str(value)
        for value in request.get("candidate_schema_correction_errors") or []
        if value
    ]
    if correction_errors:
        correction_rules = []
        if "expected_edge_values_required" in correction_errors:
            correction_rules.append(
                "EDGE or NO_EDGE requires numeric expected_upside_pct and "
                "expected_downside_pct; do not return null. For BUY, downside "
                "must be strictly negative"
            )
        if "expected_upside_pct_negative" in correction_errors:
            correction_rules.append("expected_upside_pct must be zero or positive")
        if "expected_downside_pct_positive" in correction_errors:
            correction_rules.append("expected_downside_pct must be zero or negative")
        if "insufficient_data_expected_values_must_be_null" in correction_errors:
            correction_rules.append(
                "INSUFFICIENT_DATA requires null upside and downside"
            )
        if any(error.startswith("entry_") for error in correction_errors):
            correction_rules.append(
                "For entry: NO_EDGE requires DROP; INSUFFICIENT_DATA requires WAIT "
                "with all four edge/risk evidence fields set to insufficient; EDGE "
                "BUY requires a confirmed trigger, low/moderate adverse risk, and "
                "reward/risk >= 1.25; EDGE WAIT requires recovery_required and "
                "non-blocking risk; EDGE DROP requires failed trigger, blocking "
                "risk, or reward/risk below 1.25"
            )
        if "entry_no_edge_requires_drop" in correction_errors:
            correction_rules.append(
                "Set action=DROP for NO_EDGE, with positive_edge none/weak and "
                "setup no_setup/not_applicable; do not retain WAIT"
            )
        if "entry_edge_strength_invalid" in correction_errors:
            correction_rules.append(
                "EDGE requires positive_edge=moderate or strong; otherwise use "
                "NO_EDGE/DROP only when the structural edge floor is not met"
            )
        if "entry_wait_adverse_risk_invalid" in correction_errors:
            correction_rules.append(
                "WAIT cannot carry blocking or insufficient adverse risk. If risk "
                "is blocking, return EDGE/DROP with a failed or confirmed trigger "
                "and numeric unfavorable reward/risk as appropriate"
            )
        if "entry_buy_adverse_risk_too_high" in correction_errors:
            correction_rules.append(
                "BUY cannot carry high or blocking adverse risk. Preserve the "
                "observed risk: use DROP with blocking risk or unfavorable numeric "
                "reward/risk, or WAIT only when the trigger is recovery_required "
                "and risk is non-blocking"
            )
        if "entry_buy_reward_risk_below_floor" in correction_errors:
            correction_rules.append(
                "Do not retain BUY when expected_upside_pct divided by the absolute "
                "strictly negative expected_downside_pct is below 1.25. Use DROP "
                "with risk_reward_unfavorable, or return a supported non-BUY state"
            )
        if (
            "entry_edge_drop_requires_failed_blocking_or_unfavorable"
            in correction_errors
        ):
            correction_rules.append(
                "EDGE/DROP requires trigger=failed, adverse_risk=blocking, or "
                "numeric reward/risk below 1.25. If none applies, use BUY for a "
                "confirmed low/moderate-risk trigger or WAIT for a "
                "recovery_required non-blocking trigger"
            )
        if "entry_no_edge_setup_invalid" in correction_errors:
            correction_rules.append(
                "NO_EDGE requires setup=no_setup or not_applicable; do not use "
                "continuation, pullback_recovery, or reversal"
            )
        if "entry_structural_edge_floor_misclassified" in correction_errors:
            correction_rules.append(
                "The exact completed-bar returns/slopes meet the mandatory "
                "structural edge floor; return EDGE with moderate/strong "
                "positive_edge while assessing adverse risk separately"
            )
        if "entry_blocking_overextension_misclassified" in correction_errors:
            correction_rules.append(
                "The exact payload meets the blocking overextension contract; "
                "preserve EDGE but return DROP with blocking adverse risk"
            )
        if "entry_orderly_pullback_recovery_misclassified" in correction_errors:
            correction_rules.append(
                "The exact payload meets the orderly pullback-recovery contract; "
                "return EDGE/WAIT with pullback_recovery, recovery_required, and "
                "non-blocking adverse risk"
            )
        if "entry_trusted_supportive_trigger_misclassified" in correction_errors:
            correction_rules.append(
                "The exact payload has trusted supportive aggressor tape plus a "
                "completed 1m/3m recovery and structural edge. Return EDGE with "
                "moderate/strong positive_edge, tape=supportive, and "
                "trigger=confirmed. WAIT is prohibited for this contract. Keep "
                "ask-heavy depth or a wide spread in liquidity/adverse_risk. "
                "Return BUY when adverse_risk is low/moderate and numeric "
                "reward/risk is at least 1.25; otherwise return DROP with "
                "blocking risk or numeric unfavorable reward/risk"
            )
        if "entry_thin_tape_sample_overstated" in correction_errors:
            correction_rules.append(
                "The tape sample is too thin for supportive or confirmed evidence. "
                "For otherwise sufficient core data use tape=mixed; do not confirm "
                "the trigger, and include tape_sample_insufficient"
            )
        if "entry_adverse_distribution_misclassified" in correction_errors:
            correction_rules.append(
                "The completed-bar distribution meets the adverse no-edge "
                "contract. Return NO_EDGE/DROP with trend=adverse, setup=no_setup, "
                "trigger=failed or not_applicable, and include "
                "distribution_adverse and volume_confirmation_missing"
            )
        if "entry_ask_wall_wide_spread_misclassified" in correction_errors:
            correction_rules.append(
                "The spread and top1 ask wall meet the adverse liquidity contract. "
                "Use liquidity=adverse, adverse_risk=high or blocking, never BUY, "
                "and include ask_wall_adverse"
            )
        if "reason_codes_conflict" in correction_errors:
            correction_rules.append(
                "Use at most one of edge_positive/edge_absent/no_positive_edge, at "
                "most one of risk_reward_favorable/risk_reward_unfavorable, and at "
                "most one recovery trigger code"
            )
        instructions += (
            "\nCorrection retry: the prior response violated these contract fields: "
            + ",".join(correction_errors)
            + ". "
            + "; ".join(correction_rules)
            + ". Return one corrected JSON object only."
        )
    started = time.perf_counter()
    client = OpenAI(api_key=keys[key_index], max_retries=0)
    response = client.responses.create(
        model=model,
        instructions=instructions,
        input=user_input,
        text={
            "format": {
                "type": "json_schema",
                "name": f"{DECISION_QUALITY_V2_PROMPT_VERSION}_{stage}",
                "strict": True,
                "schema": _prompt_v2_openai_schema(stage),
            },
            "verbosity": "low",
        },
        store=False,
        metadata={
            "paired_replay_id": pair_id,
            "decision_stage": stage,
            "candidate_prompt_version": str(
                candidate.get("prompt_version") or DECISION_QUALITY_V2_PROMPT_VERSION
            ),
            "candidate_contract_sha256": str(
                candidate.get("contract_sha256")
                or _candidate_contract_sha256(candidate)
            ),
            "candidate_input_sha256": str(request.get("candidate_input_sha256") or ""),
            "runtime_effect": "false",
        },
        timeout=max(1.0, float(timeout_sec)),
    )
    raw_text = _openai_output_text(response)
    parse_error = ""
    try:
        payload = json.loads(raw_text)
    except Exception:
        payload = {}
        parse_error = "candidate_response_json_invalid"
    if not isinstance(payload, dict):
        payload = {}
        parse_error = "candidate_response_not_object"
    response_id = getattr(response, "id", None)
    if response_id is None and isinstance(response, dict):
        response_id = response.get("id")
    return {
        "candidate_response": payload,
        "provider_provenance": {
            "provider": "openai",
            "model": model,
            "transport": "openai_responses_http_offline",
            "response_id": str(response_id or "") or None,
            "response_sha256": hashlib.sha256(raw_text.encode("utf-8")).hexdigest(),
            "latency_ms": int((time.perf_counter() - started) * 1000),
            "input_tokens": _usage_value(response, "input_tokens"),
            "output_tokens": _usage_value(response, "output_tokens"),
            "total_tokens": _usage_value(response, "total_tokens"),
            "provider_none": False,
            "store": False,
            "failback_chain": [],
            "parse_error": parse_error or None,
        },
    }


def _candidate_envelope(
    value: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    if isinstance(value.get("candidate_response"), dict):
        return (
            dict(value["candidate_response"]),
            dict(value.get("provider_provenance") or {}),
        )
    return dict(value), {}


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
        candidate_prompt = decision_quality_v2_system_prompt(stage)
        candidate = {
            "prompt_version": f"{DECISION_QUALITY_V2_PROMPT_VERSION}_{stage}",
            "system_prompt": candidate_prompt,
            "system_prompt_sha256": _sha256(candidate_prompt),
            "response_schema": DECISION_QUALITY_V2_RESPONSE_SCHEMA,
            "response_schema_sha256": _sha256(DECISION_QUALITY_V2_RESPONSE_SCHEMA),
            "provider": trace.get("provider_actual"),
            "model": trace.get("model"),
            "temperature": trace.get("request_temperature"),
            "reasoning_effort": trace.get("request_reasoning_effort"),
        }
        candidate["contract_sha256"] = _candidate_contract_sha256(candidate)
        requests.append(
            {
                "paired_replay_id": f"pair-{_sha256((trace_id, trace.get('payload_sha256')))[:24]}",
                "decision_trace_id": trace_id,
                "stage": stage,
                "stock_code": label.get("stock_code"),
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
                    "captured_score": trace.get("score"),
                    "captured_reason": trace.get("reason"),
                },
                "candidate": candidate,
                "outcome_join_key": label.get("label_id"),
                **OFFLINE_CONTRACT,
            }
        )
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for request in requests:
        grouped[
            (
                str(request.get("stage") or "unknown"),
                str(request.get("effective_venue") or "UNKNOWN"),
                str(request.get("session_bucket") or "UNKNOWN"),
            )
        ].append(request)
    for rows in grouped.values():
        symbol_count = len(
            {
                _normalize_stock_code(row.get("stock_code"))
                for row in rows
                if _normalize_stock_code(row.get("stock_code"))
            }
        )
        sample_floor_pass = (
            len(rows) >= PAIRED_REPLAY_MIN_ROWS
            and symbol_count >= PAIRED_REPLAY_MIN_SYMBOLS
        )
        for row in rows:
            row["sample_floor"] = {
                "decision_rows": len(rows),
                "unique_symbols": symbol_count,
                "required_decision_rows": PAIRED_REPLAY_MIN_ROWS,
                "required_unique_symbols": PAIRED_REPLAY_MIN_SYMBOLS,
                "pass": sample_floor_pass,
            }
    return requests


def prepare_detailed_paired_replay_requests(
    requests: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Attach a deterministic analysis ledger to the same exact payload."""

    detailed_requests: list[dict[str, Any]] = []
    for request in requests:
        exact_payload = request.get("exact_payload")
        if not isinstance(exact_payload, dict):
            continue
        stage = str(request.get("stage") or "")
        if stage != "entry":
            sample_floor = request.get("sample_floor")
            sample_floor = sample_floor if isinstance(sample_floor, dict) else {}
            detailed_requests.append(
                {
                    **request,
                    "detailed_analysis_exclusion_reason": (
                        "detailed_analysis_stage_not_implemented"
                    ),
                    "sample_floor": {
                        **sample_floor,
                        "pass": False,
                        "detailed_analysis_stage_supported": False,
                    },
                }
            )
            continue
        analysis = build_exact_payload_analysis_v1(exact_payload, stage=stage)
        candidate_input = {
            "exact_payload": exact_payload,
            EXACT_PAYLOAD_ANALYSIS_SCHEMA: analysis,
        }
        prompt = decision_quality_v2_detailed_system_prompt(stage)
        original_candidate = request.get("candidate")
        original_candidate = (
            original_candidate if isinstance(original_candidate, dict) else {}
        )
        candidate = {
            **original_candidate,
            "prompt_version": (f"{DECISION_QUALITY_DETAILED_PROMPT_VERSION}_{stage}"),
            "system_prompt": prompt,
            "system_prompt_sha256": _sha256(prompt),
            "analysis_schema": EXACT_PAYLOAD_ANALYSIS_SCHEMA,
            "analysis_schema_sha256": _sha256(EXACT_PAYLOAD_ANALYSIS_SCHEMA),
        }
        candidate["contract_sha256"] = _candidate_contract_sha256(candidate)
        detailed_requests.append(
            {
                **request,
                "paired_replay_id": str(request.get("paired_replay_id") or "").replace(
                    "pair-", "detailed-pair-", 1
                ),
                "exact_payload_analysis": analysis,
                "exact_payload_analysis_sha256": analysis["analysis_sha256"],
                "source_exact_payload_sha256": _sha256(exact_payload),
                "candidate_exact_payload_sha256": _sha256(
                    candidate_input["exact_payload"]
                ),
                "candidate_input": candidate_input,
                "candidate_input_sha256": _sha256(candidate_input),
                "candidate": candidate,
                "detailed_analysis_stage_supported": True,
            }
        )
    return detailed_requests


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
        candidate_attempts: list[dict[str, Any]] = []
        candidate_response: dict[str, Any] = {}
        candidate_errors: list[str] = []
        provider_failed = False
        for attempt_number in range(1, CANDIDATE_SCHEMA_MAX_ATTEMPTS + 1):
            attempt_request = dict(request)
            if candidate_errors:
                attempt_request["candidate_schema_correction_errors"] = list(
                    candidate_errors
                )
            try:
                envelope = candidate_runner(attempt_request)
                candidate_response, provider_provenance = _candidate_envelope(envelope)
                candidate_errors = validate_candidate_response(
                    candidate_response,
                    stage=str(request["stage"]),
                    exact_payload=request.get("exact_payload"),
                )
                candidate_attempts.append(
                    {
                        "attempt_number": attempt_number,
                        "status": (
                            "pass" if not candidate_errors else "schema_rejected"
                        ),
                        "schema_errors": list(candidate_errors),
                        "provider_provenance": provider_provenance,
                    }
                )
            except Exception as exc:
                provider_failed = True
                candidate_errors = ["candidate_provider_call_failed"]
                candidate_attempts.append(
                    {
                        "attempt_number": attempt_number,
                        "status": "provider_failed",
                        "schema_errors": list(candidate_errors),
                        "provider_provenance": {
                            "provider": str(
                                (request.get("candidate") or {}).get("provider")
                                or "none"
                            ),
                            "model": (request.get("candidate") or {}).get("model"),
                            "provider_none": (
                                str(
                                    (request.get("candidate") or {}).get("provider")
                                    or "none"
                                ).lower()
                                == "none"
                            ),
                            "error_type": type(exc).__name__,
                            "error_code": "candidate_provider_call_failed",
                        },
                    }
                )
                break
            if not candidate_errors:
                break
        results.append(
            {
                "paired_replay_id": request["paired_replay_id"],
                "decision_trace_id": request["decision_trace_id"],
                "stage": request["stage"],
                "effective_venue": request.get("effective_venue"),
                "session_bucket": request.get("session_bucket"),
                "payload_sha256": request["payload_sha256"],
                "candidate_prompt_sha256": (request.get("candidate") or {}).get(
                    "system_prompt_sha256"
                ),
                "candidate_response_schema_sha256": (
                    request.get("candidate") or {}
                ).get("response_schema_sha256"),
                "candidate_contract_sha256": _candidate_contract_sha256(
                    request.get("candidate") or {}
                ),
                "exact_payload_analysis_schema": (
                    (request.get("candidate") or {}).get("analysis_schema")
                ),
                "exact_payload_analysis_sha256": request.get(
                    "exact_payload_analysis_sha256"
                ),
                "candidate_input_sha256": request.get("candidate_input_sha256"),
                "deterministic_analysis_confirmed": (
                    not request.get("exact_payload_analysis_sha256")
                    or request.get("exact_payload_analysis_sha256")
                    == _sha256(
                        {
                            key: value
                            for key, value in (
                                request.get("exact_payload_analysis") or {}
                            ).items()
                            if key != "analysis_sha256"
                        }
                    )
                ),
                "same_payload_confirmed": (
                    not request.get("candidate_exact_payload_sha256")
                    or request.get("candidate_exact_payload_sha256")
                    == request.get("source_exact_payload_sha256")
                ),
                "control_response": control_response,
                "candidate_response": candidate_response,
                "candidate_schema_errors": candidate_errors,
                "candidate_attempts": candidate_attempts,
                "status": (
                    "provider_failed"
                    if provider_failed
                    else ("pass" if not candidate_errors else "schema_rejected")
                ),
                **OFFLINE_CONTRACT,
            }
        )
    return results


def run_paired_replay_parallel(
    requests: list[dict[str, Any]],
    *,
    control_runner: Callable[[dict[str, Any]], dict[str, Any]],
    candidate_runner: Callable[[dict[str, Any]], dict[str, Any]],
    max_workers: int = 4,
) -> list[dict[str, Any]]:
    if not requests:
        return []
    indexed: dict[str, int] = {
        str(request.get("paired_replay_id") or ""): index
        for index, request in enumerate(requests)
    }
    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max(1, min(int(max_workers), 8))) as executor:
        futures = {
            executor.submit(
                run_paired_replay,
                [request],
                control_runner=control_runner,
                candidate_runner=candidate_runner,
            ): request
            for request in requests
        }
        for future in as_completed(futures):
            results.extend(future.result())
    results.sort(
        key=lambda row: indexed.get(
            str(row.get("paired_replay_id") or ""), len(indexed)
        )
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
    request_by_trace = {
        str(row.get("decision_trace_id") or ""): row
        for row in requests
        if isinstance(row, dict)
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
        trace_id = str(result.get("decision_trace_id") or "")
        request = request_by_trace.get(trace_id) or {}
        mfe = _number(preferred.get("mfe_pct"))
        mae = _number(preferred.get("mae_pct"))
        first_hit = str(preferred.get("first_hit") or "")
        candidate_errors: list[str] = []
        if candidate_action == "DROP" and mfe is not None and mfe >= 1.0:
            candidate_errors.append("false_drop")
        if candidate_action == "WAIT" and mfe is not None and mfe >= 1.0:
            candidate_errors.append("false_wait")
        if candidate_action == "BUY" and (
            first_hit == "adverse" or (mae is not None and mae <= -1.0)
        ):
            candidate_errors.append("false_buy")
        comparable_rows.append(
            {
                "decision_trace_id": trace_id,
                "stock_code": request.get("stock_code"),
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
                "outcome_mfe_pct": mfe,
                "outcome_mae_pct": mae,
                "first_hit": first_hit,
                "candidate_error_taxonomy": candidate_errors,
            }
        )
    rejected = sum(row.get("status") != "pass" for row in results)
    schema_rejected = sum(row.get("status") == "schema_rejected" for row in results)
    provider_failed = sum(row.get("status") == "provider_failed" for row in results)
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
        bucket_control_ev = fmean(row["control_decision_value_pct"] for row in rows)
        bucket_candidate_ev = fmean(row["candidate_decision_value_pct"] for row in rows)
        bucket_ev_delta = fmean(row["delta_pct"] for row in rows)
        bucket_missed_upside_reduction = sum(
            row["control_missed_upside"] and not row["candidate_missed_upside"]
            for row in rows
        )
        bucket_new_missed_upside = sum(
            not row["control_missed_upside"] and row["candidate_missed_upside"]
            for row in rows
        )
        bucket_control_adverse_exposure = sum(
            row["first_hit"] == "adverse" and row["control_action"] in EXPOSURE_ACTIONS
            for row in rows
        )
        bucket_candidate_adverse_exposure = sum(
            row["first_hit"] == "adverse"
            and row["candidate_action"] in EXPOSURE_ACTIONS
            for row in rows
        )
        bucket_exposure_rows = [
            row for row in rows if row["candidate_action"] in EXPOSURE_ACTIONS
        ]
        bucket_exposure_symbols = {
            str(row.get("stock_code") or "")
            for row in bucket_exposure_rows
            if row.get("stock_code")
        }
        bucket_exposure_floor_pass = (
            len(bucket_exposure_rows) >= PAIRED_CANDIDATE_EXPOSURE_MIN_ROWS
            and len(bucket_exposure_symbols) >= PAIRED_CANDIDATE_EXPOSURE_MIN_SYMBOLS
        )
        bucket_action_counter = Counter(row["candidate_action"] for row in rows)
        bucket_dominant_action_ratio = max(bucket_action_counter.values()) / len(rows)
        bucket_quality_checks = {
            "source_quality_adjusted_ev_improved": bucket_ev_delta > 0,
            "candidate_ev_positive": bucket_candidate_ev > 0,
            "missed_upside_reduced": bucket_missed_upside_reduction > 0,
            "new_missed_upside_not_increased": bucket_new_missed_upside == 0,
            "adverse_first_exposure_not_increased": (
                bucket_candidate_adverse_exposure <= bucket_control_adverse_exposure
            ),
            "candidate_action_not_collapsed": bucket_dominant_action_ratio <= 0.90,
            "candidate_exposure_sample_floor_pass": bucket_exposure_floor_pass,
        }
        buckets.append(
            {
                "stage": stage,
                "effective_venue": venue,
                "session_bucket": session,
                "sample_count": len(rows),
                "control_source_quality_adjusted_ev_pct": bucket_control_ev,
                "candidate_source_quality_adjusted_ev_pct": bucket_candidate_ev,
                "source_quality_adjusted_ev_delta_pct": bucket_ev_delta,
                "missed_upside_reduction_count": bucket_missed_upside_reduction,
                "new_missed_upside_count": bucket_new_missed_upside,
                "control_adverse_first_exposure_count": (
                    bucket_control_adverse_exposure
                ),
                "adverse_first_candidate_exposure_count": (
                    bucket_candidate_adverse_exposure
                ),
                "candidate_exposure_decision_count": len(bucket_exposure_rows),
                "candidate_exposure_unique_symbol_count": len(bucket_exposure_symbols),
                "candidate_exposure_sample_floor_pass": (bucket_exposure_floor_pass),
                "candidate_dominant_action_ratio": (bucket_dominant_action_ratio),
                "candidate_quality_checks": bucket_quality_checks,
                "candidate_quality_gate_pass": all(bucket_quality_checks.values()),
                "candidate_error_taxonomy_counts": dict(
                    Counter(
                        error
                        for row in rows
                        for error in row["candidate_error_taxonomy"]
                    )
                ),
            }
        )
    control_ev = (
        fmean(row["control_decision_value_pct"] for row in comparable_rows)
        if comparable_rows
        else None
    )
    candidate_ev = (
        fmean(row["candidate_decision_value_pct"] for row in comparable_rows)
        if comparable_rows
        else None
    )
    ev_delta = (
        fmean(row["delta_pct"] for row in comparable_rows) if comparable_rows else None
    )
    missed_upside_reduction_count = sum(
        row["control_missed_upside"] and not row["candidate_missed_upside"]
        for row in comparable_rows
    )
    new_missed_upside_count = sum(
        not row["control_missed_upside"] and row["candidate_missed_upside"]
        for row in comparable_rows
    )
    control_adverse_first_exposure_count = sum(
        row["first_hit"] == "adverse" and row["control_action"] in EXPOSURE_ACTIONS
        for row in comparable_rows
    )
    candidate_adverse_first_exposure_count = sum(
        row["first_hit"] == "adverse" and row["candidate_action"] in EXPOSURE_ACTIONS
        for row in comparable_rows
    )
    candidate_exposure_rows = [
        row for row in comparable_rows if row["candidate_action"] in EXPOSURE_ACTIONS
    ]
    candidate_exposure_symbol_count = len(
        {
            str(row.get("stock_code") or "")
            for row in candidate_exposure_rows
            if row.get("stock_code")
        }
    )
    candidate_exposure_sample_floor_pass = (
        len(candidate_exposure_rows) >= PAIRED_CANDIDATE_EXPOSURE_MIN_ROWS
        and candidate_exposure_symbol_count >= PAIRED_CANDIDATE_EXPOSURE_MIN_SYMBOLS
        and bool(buckets)
        and all(row["candidate_exposure_sample_floor_pass"] for row in buckets)
    )
    valid_results = [row for row in results if row.get("status") == "pass"]
    candidate_action_counter = Counter(
        str((row.get("candidate_response") or {}).get("action") or "UNKNOWN")
        for row in valid_results
    )
    dominant_candidate_action_ratio = (
        max(candidate_action_counter.values()) / len(valid_results)
        if valid_results
        else None
    )
    quality_checks = {
        "all_pairs_comparable": bool(requests)
        and len(comparable_rows) == len(requests),
        "source_quality_adjusted_ev_improved": ev_delta is not None and ev_delta > 0,
        "candidate_ev_positive": candidate_ev is not None and candidate_ev > 0,
        "missed_upside_reduced": missed_upside_reduction_count > 0,
        "new_missed_upside_not_increased": new_missed_upside_count == 0,
        "adverse_first_exposure_not_increased": (
            candidate_adverse_first_exposure_count
            <= control_adverse_first_exposure_count
        ),
        "candidate_action_not_collapsed": (
            dominant_candidate_action_ratio is not None
            and dominant_candidate_action_ratio <= 0.90
        ),
        "candidate_exposure_sample_floor_pass": (candidate_exposure_sample_floor_pass),
        "all_stage_venue_buckets_quality_pass": bool(buckets)
        and all(row["candidate_quality_gate_pass"] for row in buckets),
    }
    quality_gate_pass = all(quality_checks.values())
    if rejected or (results and missing_result_count):
        status = "candidate_rejected_no_runtime_apply"
    elif not requests:
        status = "sample_floor_keep_collecting"
    elif quality_gate_pass:
        status = "paired_replay_complete_candidate_quality_pass_offline_only"
    else:
        status = "paired_replay_complete_candidate_quality_rejected"
    report_requests = [
        {
            key: value
            for key, value in request.items()
            if key not in {"exact_payload", "candidate_input"}
        }
        for request in requests
    ]
    provider_attempts = [
        attempt
        for result in results
        for attempt in result.get("candidate_attempts") or []
        if isinstance(attempt, dict)
    ]
    return {
        "schema": PAIRED_SCHEMA,
        "target_date": target_date,
        "generated_at": datetime.now(KST).isoformat(),
        "status": status,
        "request_count": len(requests),
        "result_count": len(results),
        "schema_rejected_count": schema_rejected,
        "provider_failed_count": provider_failed,
        "missing_result_count": missing_result_count,
        "paired_comparable_count": len(comparable_rows),
        "control_source_quality_adjusted_ev_pct": control_ev,
        "candidate_source_quality_adjusted_ev_pct": candidate_ev,
        "source_quality_adjusted_ev_delta_pct": ev_delta,
        "missed_upside_reduction_count": missed_upside_reduction_count,
        "new_missed_upside_count": new_missed_upside_count,
        "control_adverse_first_exposure_count": (control_adverse_first_exposure_count),
        "adverse_first_candidate_exposure_count": (
            candidate_adverse_first_exposure_count
        ),
        "candidate_exposure_decision_count": len(candidate_exposure_rows),
        "candidate_exposure_unique_symbol_count": candidate_exposure_symbol_count,
        "candidate_exposure_sample_floor": {
            "decision_rows": PAIRED_CANDIDATE_EXPOSURE_MIN_ROWS,
            "unique_symbols": PAIRED_CANDIDATE_EXPOSURE_MIN_SYMBOLS,
            "pass": candidate_exposure_sample_floor_pass,
        },
        "candidate_error_taxonomy_counts": dict(
            Counter(
                error
                for row in comparable_rows
                for error in row["candidate_error_taxonomy"]
            )
        ),
        "candidate_dominant_action_ratio": dominant_candidate_action_ratio,
        "candidate_quality_gate_pass": quality_gate_pass,
        "candidate_quality_checks": quality_checks,
        "control_action_counts": dict(
            Counter(
                str((row.get("control_response") or {}).get("action") or "UNKNOWN")
                for row in valid_results
            )
        ),
        "candidate_action_counts": dict(candidate_action_counter),
        "candidate_edge_state_counts": dict(
            Counter(
                str(
                    (row.get("candidate_response") or {}).get("edge_state") or "UNKNOWN"
                )
                for row in valid_results
            )
        ),
        "candidate_provider_attempt_count": len(provider_attempts),
        "candidate_provider_none_count": sum(
            (attempt.get("provider_provenance") or {}).get("provider_none") is True
            for attempt in provider_attempts
        ),
        "net_profit_status": "not_available_without_notional_and_fill_join",
        "buckets": buckets,
        "paired_comparisons": comparable_rows,
        "requests": report_requests,
        "results": results,
        **OFFLINE_CONTRACT,
    }


def build_detailed_three_way_comparison(
    *,
    one_pass_report: dict[str, Any],
    detailed_report: dict[str, Any],
) -> dict[str, Any]:
    """Compare control, one-pass V2, and detailed two-pass on common rows."""

    one_pass_by_trace = {
        str(row.get("decision_trace_id") or ""): row
        for row in one_pass_report.get("paired_comparisons") or []
        if isinstance(row, dict) and row.get("decision_trace_id")
    }
    detailed_by_trace = {
        str(row.get("decision_trace_id") or ""): row
        for row in detailed_report.get("paired_comparisons") or []
        if isinstance(row, dict) and row.get("decision_trace_id")
    }
    trace_ids = sorted(set(one_pass_by_trace) & set(detailed_by_trace))
    rows: list[dict[str, Any]] = []
    for trace_id in trace_ids:
        one_pass = one_pass_by_trace[trace_id]
        detailed = detailed_by_trace[trace_id]
        outcome = _number(detailed.get("outcome_return_pct"))
        control_value = _number(detailed.get("control_decision_value_pct"))
        one_pass_value = _number(one_pass.get("candidate_decision_value_pct"))
        detailed_value = _number(detailed.get("candidate_decision_value_pct"))
        if None in {outcome, control_value, one_pass_value, detailed_value}:
            continue
        rows.append(
            {
                "decision_trace_id": trace_id,
                "stock_code": detailed.get("stock_code"),
                "effective_venue": detailed.get("effective_venue"),
                "session_bucket": detailed.get("session_bucket"),
                "outcome_return_pct": outcome,
                "control_action": detailed.get("control_action"),
                "one_pass_action": one_pass.get("candidate_action"),
                "detailed_action": detailed.get("candidate_action"),
                "control_decision_value_pct": control_value,
                "one_pass_decision_value_pct": one_pass_value,
                "detailed_decision_value_pct": detailed_value,
                "detailed_vs_one_pass_delta_pct": detailed_value - one_pass_value,
                "one_pass_error_taxonomy": list(
                    one_pass.get("candidate_error_taxonomy") or []
                ),
                "detailed_error_taxonomy": list(
                    detailed.get("candidate_error_taxonomy") or []
                ),
            }
        )
    comparable_trace_ids = [row["decision_trace_id"] for row in rows]

    def mean_field(field: str) -> float | None:
        return fmean(row[field] for row in rows) if rows else None

    transition_counts = Counter(
        f"{row['one_pass_action']}->{row['detailed_action']}" for row in rows
    )
    one_pass_errors = Counter(
        error for row in rows for error in row["one_pass_error_taxonomy"]
    )
    detailed_errors = Counter(
        error for row in rows for error in row["detailed_error_taxonomy"]
    )
    return {
        "schema": "ai_prompt_three_way_comparison_v1",
        "one_pass_prompt_version": (
            ((one_pass_report.get("requests") or [{}])[0].get("candidate") or {}).get(
                "prompt_version"
            )
            if one_pass_report.get("requests")
            else None
        ),
        "detailed_prompt_version": (
            ((detailed_report.get("requests") or [{}])[0].get("candidate") or {}).get(
                "prompt_version"
            )
            if detailed_report.get("requests")
            else None
        ),
        "common_comparable_count": len(rows),
        "common_cohort_sha256": _sha256(comparable_trace_ids),
        "control_source_quality_adjusted_ev_pct": mean_field(
            "control_decision_value_pct"
        ),
        "one_pass_source_quality_adjusted_ev_pct": mean_field(
            "one_pass_decision_value_pct"
        ),
        "detailed_source_quality_adjusted_ev_pct": mean_field(
            "detailed_decision_value_pct"
        ),
        "detailed_vs_one_pass_ev_delta_pct": mean_field(
            "detailed_vs_one_pass_delta_pct"
        ),
        "action_transition_counts": dict(transition_counts),
        "one_pass_error_taxonomy_counts": dict(one_pass_errors),
        "detailed_error_taxonomy_counts": dict(detailed_errors),
        "rows": rows,
        **OFFLINE_CONTRACT,
    }


def _snapshot_recovery_levels(
    exact_payload: dict[str, Any],
) -> dict[str, float | None]:
    current = exact_payload.get("current")
    current = current if isinstance(current, dict) else {}
    features = exact_payload.get("features")
    features = features if isinstance(features, dict) else {}
    context = exact_payload.get("entry_candle_context")
    context = context if isinstance(context, dict) else {}
    reference_price = _number(current.get("price"))

    def level_from_bp(value: Any) -> float | None:
        basis_points = _number(value)
        if reference_price is None or reference_price <= 0 or basis_points is None:
            return None
        denominator = 1.0 + (basis_points / 10000.0)
        return reference_price / denominator if denominator > 0 else None

    completed_bars = [
        row
        for row in context.get("bars") or []
        if isinstance(row, dict) and not bool(row.get("forming", False))
    ]
    last_completed_close = (
        _number(completed_bars[-1].get("c")) if completed_bars else None
    )
    recent_lows = [
        value
        for value in (_number(row.get("l")) for row in completed_bars[-3:])
        if value is not None and value > 0
    ]
    micro_vwap = level_from_bp(features.get("curr_vs_micro_vwap_bp"))
    ma5 = level_from_bp(features.get("curr_vs_ma5_bp"))
    reclaim_candidates = [
        value
        for value in (micro_vwap, ma5, last_completed_close)
        if value is not None and value > 0
    ]
    return {
        "reference_price": reference_price,
        "micro_vwap_level": micro_vwap,
        "ma5_level": ma5,
        "last_completed_close": last_completed_close,
        "recent_completed_low": min(recent_lows) if recent_lows else None,
        "reclaim_level": max(reclaim_candidates) if reclaim_candidates else None,
    }


def _indexed_completed_price_rows(
    price_rows: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    rows_by_code: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in price_rows:
        timestamp = _parse_ts(row.get("timestamp"))
        code = _normalize_stock_code(row.get("stock_code"))
        open_price = _number(row.get("open"))
        close = _number(row.get("close"))
        high = _number(row.get("high"))
        low = _number(row.get("low"))
        if (
            timestamp is None
            or not code
            or close is None
            or close <= 0
            or not _price_source_usable(row)
        ):
            continue
        rows_by_code[code].append(
            {
                **row,
                "_timestamp": timestamp,
                "_open": (
                    open_price if open_price is not None and open_price > 0 else None
                ),
                "_close": close,
                "_high": high if high is not None and high > 0 else close,
                "_low": low if low is not None and low > 0 else close,
            }
        )
    for rows in rows_by_code.values():
        rows.sort(key=lambda item: item["_timestamp"])
    return rows_by_code


def _forward_metrics_after_recovery(
    *,
    route_rows: list[dict[str, Any]],
    entry_row: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    entry_at = entry_row["_timestamp"]
    entry_price = entry_row["_open"]
    metrics: dict[str, dict[str, Any]] = {}
    for horizon in RECOVERY_OUTCOME_HORIZONS_MIN:
        horizon_end = entry_at + timedelta(minutes=horizon)
        expected_last_bar_at = horizon_end - timedelta(minutes=1)
        window = [
            row for row in route_rows if entry_at <= row["_timestamp"] < horizon_end
        ]
        if (
            not window
            or (expected_last_bar_at - window[-1]["_timestamp"]).total_seconds()
            > HORIZON_END_MAX_LAG_SEC
        ):
            continue
        metrics[f"{horizon}m"] = {
            "sample_count": len(window),
            "mfe_pct": max(
                round(((row["_high"] / entry_price) - 1.0) * 100.0, 10)
                for row in window
            ),
            "mae_pct": min(
                round(((row["_low"] / entry_price) - 1.0) * 100.0, 10) for row in window
            ),
            "end_return_pct": round(
                ((window[-1]["_close"] / entry_price) - 1.0) * 100.0,
                10,
            ),
            "counterfactual_only": True,
            "window_basis": "next_bar_open_after_recovery_same_route",
            "window_end": horizon_end.isoformat(),
        }
    return metrics


def build_recovery_trigger_report(
    *,
    target_date: str,
    paired_report: dict[str, Any],
    labels: list[dict[str, Any]],
    payloads: list[dict[str, Any]],
    price_rows: list[dict[str, Any]],
    price_source_provenance: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Value EDGE+WAIT as retained observation, never as an immediate fill."""

    label_by_trace = {
        str(row.get("decision_trace_id") or ""): row
        for row in labels
        if row.get("source_quality_status") == "pass"
        and row.get("primary_cohort_eligible") is True
    }
    request_by_trace = {
        str(row.get("decision_trace_id") or ""): row
        for row in paired_report.get("requests") or []
        if isinstance(row, dict)
    }
    payload_by_key, payload_by_unique_hash = _payload_indexes(payloads)
    rows_by_code = _indexed_completed_price_rows(price_rows)
    rows: list[dict[str, Any]] = []
    exclusions: list[dict[str, Any]] = []
    for result in paired_report.get("results") or []:
        if not isinstance(result, dict) or result.get("status") != "pass":
            continue
        candidate = result.get("candidate_response")
        candidate = candidate if isinstance(candidate, dict) else {}
        evidence = candidate.get("evidence")
        evidence = evidence if isinstance(evidence, dict) else {}
        if not (
            candidate.get("edge_state") == "EDGE"
            and candidate.get("action") == "WAIT"
            and evidence.get("trigger") == "recovery_required"
        ):
            continue
        trace_id = str(result.get("decision_trace_id") or "")
        request = request_by_trace.get(trace_id) or {}
        label = label_by_trace.get(trace_id)
        payload_hash = str(result.get("payload_sha256") or "")
        payload_row = payload_by_unique_hash.get(payload_hash)
        if payload_row is None:
            payload_row = payload_by_key.get((payload_hash, "analyze_target"))
        exact_payload = (
            payload_row.get("sanitized_user_input")
            if isinstance(payload_row, dict)
            else None
        )
        if not isinstance(label, dict) or not isinstance(exact_payload, dict):
            exclusions.append(
                {
                    "decision_trace_id": trace_id,
                    "reason": (
                        "mature_exact_label_missing"
                        if not isinstance(label, dict)
                        else "exact_payload_missing"
                    ),
                }
            )
            continue
        code = _normalize_stock_code(
            label.get("stock_code") or request.get("stock_code")
        )
        decision_ts = _parse_ts(label.get("decision_ts"))
        levels = _snapshot_recovery_levels(exact_payload)
        if (
            not code
            or decision_ts is None
            or levels["reclaim_level"] is None
            or levels["recent_completed_low"] is None
        ):
            exclusions.append(
                {
                    "decision_trace_id": trace_id,
                    "reason": "recovery_level_contract_missing",
                }
            )
            continue
        recovery_window_end = decision_ts + timedelta(
            minutes=RECOVERY_TRIGGER_WINDOW_MIN
        )
        route_rows = [
            row
            for row in rows_by_code.get(code, [])
            if decision_ts < row["_timestamp"] and _same_route(label, row)
        ]
        recovery_window = [
            row for row in route_rows if row["_timestamp"] <= recovery_window_end
        ]
        window_complete = (
            bool(recovery_window)
            and (
                recovery_window_end - recovery_window[-1]["_timestamp"]
            ).total_seconds()
            <= HORIZON_END_MAX_LAG_SEC
        )
        previous_close = (
            levels["last_completed_close"]
            or levels["reference_price"]
            or levels["reclaim_level"]
        )
        trigger_row = None
        adverse_row = None
        for row in recovery_window:
            if (
                trigger_row is None
                and row["_close"] >= levels["reclaim_level"]
                and row["_close"] > previous_close
            ):
                trigger_row = row
            if adverse_row is None and row["_low"] < levels["recent_completed_low"]:
                adverse_row = row
            previous_close = row["_close"]
        trigger_at = trigger_row["_timestamp"] if trigger_row else None
        adverse_at = adverse_row["_timestamp"] if adverse_row else None
        if trigger_at and adverse_at and trigger_at == adverse_at:
            first_event = "ambiguous_same_bar"
        elif trigger_at and (adverse_at is None or trigger_at < adverse_at):
            first_event = "recovery"
        elif adverse_at:
            first_event = "adverse"
        else:
            first_event = "none"
        recovery_eligible = first_event == "recovery"
        recovery_entry_row = None
        if recovery_eligible:
            next_route_row = next(
                (
                    row
                    for row in route_rows
                    if trigger_at and row["_timestamp"] > trigger_at
                ),
                None,
            )
            if (
                next_route_row is not None
                and next_route_row.get("_open") is not None
                and (next_route_row["_timestamp"] - trigger_at).total_seconds()
                <= HORIZON_END_MAX_LAG_SEC
            ):
                recovery_entry_row = next_route_row
        forward_metrics = (
            _forward_metrics_after_recovery(
                route_rows=route_rows,
                entry_row=recovery_entry_row,
            )
            if recovery_entry_row is not None
            else {}
        )
        primary_recovery_metric = forward_metrics.get("10m")
        decision_value = (
            _number(primary_recovery_metric.get("end_return_pct"))
            if isinstance(primary_recovery_metric, dict)
            else (0.0 if window_complete and not recovery_eligible else None)
        )
        control_action = str(
            (result.get("control_response") or {}).get("action") or ""
        ).upper()
        primary_control_metric = _primary_metric(label) or {}
        control_value = _decision_value(
            control_action,
            _number(primary_control_metric.get("end_return_pct")),
        )
        rows.append(
            {
                "decision_trace_id": trace_id,
                "paired_replay_id": result.get("paired_replay_id"),
                "payload_sha256": payload_hash,
                "stock_code": code,
                "effective_venue": label.get("effective_venue"),
                "session_bucket": label.get("session_bucket"),
                "decision_ts": decision_ts.isoformat(),
                "control_action": control_action,
                "candidate_action": "WAIT",
                "candidate_edge_state": "EDGE",
                "candidate_setup": evidence.get("setup"),
                "candidate_adverse_risk": evidence.get("adverse_risk"),
                "recovery_levels": {
                    key: (
                        round(value, 10) if isinstance(value, (int, float)) else value
                    )
                    for key, value in levels.items()
                },
                "recovery_window_min": RECOVERY_TRIGGER_WINDOW_MIN,
                "recovery_window_complete": window_complete,
                "recovery_trigger_at": (trigger_at.isoformat() if trigger_at else None),
                "adverse_breach_at": (adverse_at.isoformat() if adverse_at else None),
                "first_event": first_event,
                "recovery_entry_price": (
                    recovery_entry_row["_open"] if recovery_entry_row else None
                ),
                "recovery_entry_at": (
                    recovery_entry_row["_timestamp"].isoformat()
                    if recovery_entry_row
                    else None
                ),
                "recovery_trigger_close": (
                    trigger_row["_close"] if recovery_eligible and trigger_row else None
                ),
                "recovery_entry_move_from_snapshot_pct": (
                    round(
                        (
                            (recovery_entry_row["_open"] / levels["reference_price"])
                            - 1.0
                        )
                        * 100.0,
                        10,
                    )
                    if recovery_entry_row and levels["reference_price"]
                    else None
                ),
                "forward_metrics": forward_metrics,
                "control_decision_value_pct": control_value,
                "candidate_conditional_decision_value_pct": decision_value,
                "conditional_delta_pct": (
                    decision_value - control_value
                    if decision_value is not None and control_value is not None
                    else None
                ),
                "counterfactual_only": True,
            }
        )
    symbol_count = len(
        {str(row.get("stock_code") or "") for row in rows if row.get("stock_code")}
    )
    sample_floor_pass = (
        len(rows) >= RECOVERY_TRIGGER_MIN_ROWS
        and symbol_count >= RECOVERY_TRIGGER_MIN_SYMBOLS
    )
    comparable = [
        row
        for row in rows
        if row.get("control_decision_value_pct") is not None
        and row.get("candidate_conditional_decision_value_pct") is not None
    ]
    control_ev = (
        fmean(row["control_decision_value_pct"] for row in comparable)
        if comparable
        else None
    )
    candidate_ev = (
        fmean(row["candidate_conditional_decision_value_pct"] for row in comparable)
        if comparable
        else None
    )
    ev_delta = (
        candidate_ev - control_ev
        if candidate_ev is not None and control_ev is not None
        else None
    )
    missed_upside_reduction_count = sum(
        row["control_action"] in NO_EXPOSURE_ACTIONS
        and row["candidate_conditional_decision_value_pct"] > 0
        for row in comparable
    )
    control_negative_exposure_count = sum(
        row["control_decision_value_pct"] < 0 for row in comparable
    )
    candidate_negative_exposure_count = sum(
        row["candidate_conditional_decision_value_pct"] < 0 for row in comparable
    )
    quality_checks = {
        "sample_floor_pass": sample_floor_pass,
        "all_rows_comparable": bool(rows) and len(comparable) == len(rows),
        "source_quality_adjusted_ev_improved": ev_delta is not None and ev_delta > 0,
        "candidate_ev_positive": candidate_ev is not None and candidate_ev > 0,
        "missed_upside_reduced": missed_upside_reduction_count > 0,
        "negative_exposure_not_increased": (
            candidate_negative_exposure_count <= control_negative_exposure_count
        ),
    }
    quality_gate_pass = all(quality_checks.values())
    status = (
        "sample_floor_keep_collecting"
        if not sample_floor_pass
        else (
            "recovery_counterfactual_quality_pass_offline_only"
            if quality_gate_pass
            else "recovery_counterfactual_quality_rejected"
        )
    )
    return {
        "schema": RECOVERY_TRIGGER_SCHEMA,
        "target_date": target_date,
        "generated_at": datetime.now(KST).isoformat(),
        "status": status,
        "eligible_row_count": len(rows),
        "eligible_symbol_count": symbol_count,
        "excluded_row_count": len(exclusions),
        "comparable_row_count": len(comparable),
        "sample_floor_pass": sample_floor_pass,
        "recovery_trigger_count": sum(
            row.get("first_event") == "recovery" for row in rows
        ),
        "adverse_first_count": sum(row.get("first_event") == "adverse" for row in rows),
        "ambiguous_same_bar_count": sum(
            row.get("first_event") == "ambiguous_same_bar" for row in rows
        ),
        "no_event_count": sum(row.get("first_event") == "none" for row in rows),
        "control_drop_recovery_count": sum(
            row.get("control_action") == "DROP" and row.get("first_event") == "recovery"
            for row in rows
        ),
        "control_source_quality_adjusted_ev_pct": control_ev,
        "candidate_source_quality_adjusted_ev_pct": candidate_ev,
        "source_quality_adjusted_ev_delta_pct": ev_delta,
        "missed_upside_reduction_count": missed_upside_reduction_count,
        "control_negative_exposure_count": control_negative_exposure_count,
        "candidate_negative_exposure_count": candidate_negative_exposure_count,
        "quality_gate_pass": quality_gate_pass,
        "quality_checks": quality_checks,
        "price_source_provenance": list(price_source_provenance or []),
        "rows": rows,
        "exclusions": exclusions,
        **RECOVERY_TRIGGER_CONTRACT,
    }


def _default_sources(
    target_date: str, *, include_pipeline: bool = True
) -> dict[str, list[dict[str, Any]]]:
    traces = _load_jsonl(TRACE_DIR / f"ai_decision_trace_{target_date}.jsonl")
    payloads = _load_jsonl(PAYLOAD_DIR / f"ai_decision_payloads_{target_date}.jsonl")
    pending = _load_jsonl(OUTCOME_DIR / f"ai_decision_outcomes_{target_date}.jsonl")
    pipeline = []
    if include_pipeline:
        target = datetime.strptime(target_date, "%Y-%m-%d").date()
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
        choices=(
            "control",
            "mature",
            "baseline",
            "paired",
            "detailed",
            "correlation",
            "recovery",
        ),
        required=True,
    )
    parser.add_argument("--as-of")
    parser.add_argument(
        "--outcome-price-source",
        choices=("pipeline", "kiwoom_completed_1m"),
        default="pipeline",
        help=(
            "Offline forward-price source. kiwoom_completed_1m reuses only "
            "the valid shared token and never issues a new token."
        ),
    )
    parser.add_argument(
        "--execute-candidate",
        action="store_true",
        help="Execute sample-floor-ready Prompt V2 candidates offline.",
    )
    parser.add_argument("--candidate-timeout-sec", type=float, default=45.0)
    parser.add_argument("--candidate-workers", type=int, default=4)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    if args.execute_candidate and (
        args.mode not in {"paired", "detailed"} or not args.write
    ):
        parser.error("--execute-candidate requires --mode paired|detailed --write")
    sources = _default_sources(
        args.date,
        include_pipeline=(
            args.mode != "control" and args.outcome_price_source == "pipeline"
        ),
    )
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
        as_of = _parse_ts(args.as_of) or datetime.now(KST)
        prices, lifecycle = load_pipeline_price_and_lifecycle_rows(sources["pipeline"])
        price_source_provenance: list[dict[str, Any]] = []
        if args.outcome_price_source == "kiwoom_completed_1m":
            from src.utils import kiwoom_utils

            token = kiwoom_utils.get_cached_kiwoom_token()
            source_route_labels = annotate_primary_cohort_eligibility(
                labels=sources["pending"],
                traces=sources["traces"],
                payloads=sources["payloads"],
                promotion=promotion,
            )
            source_route_labels = [
                row
                for row in source_route_labels
                if row.get("primary_cohort_eligible") is True
            ]

            def fetch_kiwoom_completed(
                _stock_code: str, request_code: str
            ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
                if not token:
                    return [], {"fetch_error": "cached_token_unavailable"}
                return kiwoom_utils.get_minute_candles_ka10080_with_meta(
                    token,
                    request_code,
                    limit=500,
                    explicit_request_code=True,
                    base_dt=args.date.replace("-", ""),
                )

            prices, price_source_provenance = load_kiwoom_completed_minute_price_rows(
                target_date=args.date,
                labels=source_route_labels,
                as_of=as_of,
                fetcher=fetch_kiwoom_completed,
            )
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
            "outcome_price_source": args.outcome_price_source,
            "price_source_provenance": price_source_provenance,
            "labels": labels,
            **OFFLINE_CONTRACT,
        }
        if args.mode == "mature":
            report = label_report
            path = label_report_path(args.date)
        elif args.mode == "baseline":
            report = build_quality_baseline(target_date=args.date, labels=labels)
            report["outcome_price_source"] = args.outcome_price_source
            report["price_source_provenance"] = price_source_provenance
            path = baseline_path(args.date)
        elif args.mode == "correlation":
            report = build_score_outcome_correlation_report(
                target_date=args.date,
                labels=labels,
                price_source_provenance=price_source_provenance,
            )
            report["outcome_price_source"] = args.outcome_price_source
            path = score_correlation_path(args.date)
        elif args.mode == "recovery":
            report = build_recovery_trigger_report(
                target_date=args.date,
                paired_report=_load_json(paired_path(args.date)),
                labels=labels,
                payloads=sources["payloads"],
                price_rows=prices,
                price_source_provenance=price_source_provenance,
            )
            report["outcome_price_source"] = args.outcome_price_source
            path = recovery_trigger_path(args.date)
        else:
            prepared_requests = prepare_paired_replay_requests(
                control_manifest=_load_json(control_path(args.date)),
                traces=sources["traces"],
                payloads=sources["payloads"],
                labels=labels,
            )
            if args.mode == "detailed":
                prepared_requests = prepare_detailed_paired_replay_requests(
                    prepared_requests
                )
            requests = [
                request
                for request in prepared_requests
                if (request.get("sample_floor") or {}).get("pass") is True
            ]
            results: list[dict[str, Any]] = []
            if args.execute_candidate and requests:
                output_path = (
                    detailed_paired_path(args.date)
                    if args.mode == "detailed"
                    else paired_path(args.date)
                )
                existing_report = _load_json(output_path)
                request_by_pair = {
                    str(request.get("paired_replay_id") or ""): request
                    for request in requests
                }
                existing_results = [
                    row
                    for row in existing_report.get("results") or []
                    if isinstance(row, dict)
                    and row.get("status") == "pass"
                    and str(row.get("paired_replay_id") or "") in request_by_pair
                    and row.get("payload_sha256")
                    == request_by_pair[str(row.get("paired_replay_id") or "")].get(
                        "payload_sha256"
                    )
                    and row.get("candidate_prompt_sha256")
                    == (
                        request_by_pair[str(row.get("paired_replay_id") or "")].get(
                            "candidate"
                        )
                        or {}
                    ).get("system_prompt_sha256")
                    and row.get("candidate_contract_sha256")
                    == (
                        request_by_pair[str(row.get("paired_replay_id") or "")].get(
                            "candidate"
                        )
                        or {}
                    ).get("contract_sha256")
                    and row.get("candidate_input_sha256")
                    == request_by_pair[str(row.get("paired_replay_id") or "")].get(
                        "candidate_input_sha256"
                    )
                    and row.get("exact_payload_analysis_sha256")
                    == request_by_pair[str(row.get("paired_replay_id") or "")].get(
                        "exact_payload_analysis_sha256"
                    )
                    and not validate_candidate_response(
                        dict(row.get("candidate_response") or {}),
                        stage=str(
                            request_by_pair[str(row.get("paired_replay_id") or "")].get(
                                "stage"
                            )
                            or ""
                        ),
                        exact_payload=request_by_pair[
                            str(row.get("paired_replay_id") or "")
                        ].get("exact_payload"),
                    )
                ]
                completed_pair_ids = {
                    str(row.get("paired_replay_id") or "") for row in existing_results
                }
                pending_requests = [
                    request
                    for request in requests
                    if str(request.get("paired_replay_id") or "")
                    not in completed_pair_ids
                ]
                api_keys = _offline_openai_api_keys()

                def captured_control(request: dict[str, Any]) -> dict[str, Any]:
                    control = request.get("control") or {}
                    return {
                        "action": control.get("captured_action"),
                        "score": control.get("captured_score"),
                        "reason": control.get("captured_reason"),
                        "result_source": "captured_natural_control",
                    }

                def candidate_runner(request: dict[str, Any]) -> dict[str, Any]:
                    return execute_openai_prompt_v2_candidate(
                        request,
                        api_keys=api_keys,
                        timeout_sec=args.candidate_timeout_sec,
                    )

                results = existing_results + run_paired_replay_parallel(
                    pending_requests,
                    control_runner=captured_control,
                    candidate_runner=candidate_runner,
                    max_workers=args.candidate_workers,
                )
                result_order = {
                    str(request.get("paired_replay_id") or ""): index
                    for index, request in enumerate(requests)
                }
                results.sort(
                    key=lambda row: result_order.get(
                        str(row.get("paired_replay_id") or ""), len(result_order)
                    )
                )
            report = build_paired_replay_report(
                target_date=args.date,
                requests=requests,
                results=results,
                labels=labels,
            )
            if args.mode == "detailed":
                report["schema"] = DETAILED_PAIRED_SCHEMA
                report["analysis_schema"] = EXACT_PAYLOAD_ANALYSIS_SCHEMA
                report["three_way_comparison"] = build_detailed_three_way_comparison(
                    one_pass_report=_load_json(paired_path(args.date)),
                    detailed_report=report,
                )
            floor_groups: dict[tuple[str, str, str], dict[str, Any]] = {}
            for request in prepared_requests:
                key = (
                    str(request.get("stage") or "unknown"),
                    str(request.get("effective_venue") or "UNKNOWN"),
                    str(request.get("session_bucket") or "UNKNOWN"),
                )
                floor_groups[key] = dict(request.get("sample_floor") or {})
            report["prepared_request_count"] = len(prepared_requests)
            report["sample_floor_excluded_request_count"] = len(
                prepared_requests
            ) - len(requests)
            report["sample_floor_buckets"] = [
                {
                    "stage": key[0],
                    "effective_venue": key[1],
                    "session_bucket": key[2],
                    **value,
                }
                for key, value in sorted(floor_groups.items())
            ]
            report["outcome_price_source"] = args.outcome_price_source
            report["price_source_provenance"] = price_source_provenance
            path = (
                detailed_paired_path(args.date)
                if args.mode == "detailed"
                else paired_path(args.date)
            )
    if args.write:
        _atomic_write_json(path, report)
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
