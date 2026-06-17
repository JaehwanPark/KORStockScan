"""Build a report-only action decision matrix for scalping entries."""

from __future__ import annotations

import argparse
import gzip
import json
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable

from src.engine.scalping.entry_adm_bucket_contract import (
    ENTRY_ADM_BUCKET_DIMENSIONS,
    ENTRY_ADM_BUCKET_SCHEMA_VERSION,
    entry_adm_bucket_token,
    entry_adm_market_regime_continuous_bucket,
    entry_adm_time_bucket,
)
from src.utils.jsonl_io import existing_or_gzip_path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
REPORT_DIR = DATA_DIR / "report"
ADM_REPORT_DIR = REPORT_DIR / "scalp_entry_action_decision_matrix"
PIPELINE_EVENT_DIR = DATA_DIR / "pipeline_events"
THRESHOLD_EVENT_DIR = DATA_DIR / "threshold_cycle"
THRESHOLD_SNAPSHOT_DIR = THRESHOLD_EVENT_DIR / "snapshots"
POST_SELL_DIR = DATA_DIR / "post_sell"

REPORT_SCHEMA_VERSION = 1
MATRIX_VERSION_PREFIX = "scalp_entry_adm_v1"
SAMPLE_FLOOR = 20

ACTION_ORDER = [
    "BUY_NOW",
    "WAIT_REQUOTE",
    "SKIP_STALE",
    "BUY_DEFENSIVE",
    "NO_BUY_AI",
    "SKIP_SOURCE_QUALITY",
    "SKIP_PRE_SUBMIT_SAFETY",
]

RELEVANT_STAGES = {
    "scalp_entry_action_decision_snapshot",
    "ai_confirmed",
    "blocked_ai_score",
    "latency_block",
    "latency_pass",
    "entry_submit_revalidation_warning",
    "entry_submit_revalidation_block",
    "pre_submit_liquidity_guard_block",
    "pre_submit_overbought_pullback_guard_block",
    "order_bundle_submitted",
    "scalp_sim_entry_armed",
    "scalp_sim_entry_ai_price_applied",
    "scalp_sim_entry_ai_price_skip_order",
    "scalp_sim_pre_submit_liquidity_guard_would_block",
    "scalp_sim_pre_submit_liquidity_guard_would_pass",
    "scalp_sim_pre_submit_liquidity_guard_unknown",
    "scalp_sim_pre_submit_overbought_guard_would_block",
    "scalp_sim_pre_submit_overbought_guard_would_pass",
    "scalp_sim_buy_order_virtual_pending",
    "scalp_sim_entry_submit_revalidation_warning",
    "scalp_sim_entry_submit_revalidation_block",
    "scalp_sim_buy_order_assumed_filled",
    "scalp_sim_sell_order_assumed_filled",
}

PRE_SUBMIT_CONTEXT_OPTIONAL_STAGES = {
    "blocked_ai_score",
    "latency_block",
    "entry_submit_revalidation_warning",
    "entry_submit_revalidation_block",
    "pre_submit_liquidity_guard_block",
    "pre_submit_overbought_pullback_guard_block",
    "scalp_sim_entry_armed",
    "scalp_sim_entry_ai_price_skip_order",
    "scalp_sim_pre_submit_liquidity_guard_would_block",
    "scalp_sim_pre_submit_liquidity_guard_unknown",
    "scalp_sim_pre_submit_overbought_guard_would_block",
    "scalp_sim_buy_order_virtual_pending",
    "scalp_sim_entry_submit_revalidation_warning",
    "scalp_sim_entry_submit_revalidation_block",
}

SCORE_CONTEXT_NOT_AVAILABLE_STAGES = {
    "scalp_sim_sell_order_assumed_filled",
    "scalp_sim_holding_started",
    "scalp_sim_scale_in_order_assumed_filled",
    "scalp_sim_scale_in_order_unfilled",
    "scalp_sim_overnight_decision",
    "scalp_sim_overnight_sell_today",
    "scalp_sim_overnight_hold",
    "scalp_sim_overnight_carry_restored",
}

SCORE_CONTEXT_BACKFILL_ELIGIBLE_STAGES = {
    "order_bundle_submitted",
    "pre_submit_liquidity_guard_block",
    "pre_submit_overbought_pullback_guard_block",
    "scalp_sim_pre_submit_liquidity_guard_would_block",
    "scalp_sim_pre_submit_liquidity_guard_unknown",
    "scalp_sim_pre_submit_overbought_guard_would_block",
}

SCORE_BACKFILL_MAX_PAST_SECONDS = 180.0
SCORE_BACKFILL_KEY_FIELDS = (
    "sim_record_id",
    "candidate_id",
    "record_id",
    "submit_attempt_id",
    "broker_order_no",
    "order_no",
    "ord_no",
    "order_response_ord_no",
)


def report_paths(target_date: str) -> tuple[Path, Path]:
    base = ADM_REPORT_DIR / f"scalp_entry_action_decision_matrix_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, default: float | None = 0.0) -> float | None:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    raw = str(value or "").strip().lower()
    if raw in {"1", "true", "yes", "y", "on"}:
        return True
    if raw in {"0", "false", "no", "n", "off"}:
        return False
    return default


def _nonempty(value: Any) -> str:
    raw = str(value or "").strip()
    return "" if raw in {"", "-", "None", "none", "null"} else raw


def _optional_flag_reason(value: Any) -> str:
    if isinstance(value, bool):
        return "flagged" if value else ""
    raw = _nonempty(value)
    if raw.lower() in {"false", "0", "no", "off"}:
        return ""
    return raw


def _open_text(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8", errors="ignore")
    return path.open("r", encoding="utf-8", errors="ignore")


def _event_paths(target_date: str) -> list[Path]:
    paths: list[Path] = []
    for path in [
        existing_or_gzip_path(THRESHOLD_EVENT_DIR / f"threshold_events_{target_date}.jsonl"),
        PIPELINE_EVENT_DIR / f"pipeline_events_{target_date}.jsonl",
        PIPELINE_EVENT_DIR / f"pipeline_events_{target_date}.jsonl.gz",
    ]:
        if path.exists():
            paths.append(path)
    paths.extend(sorted(THRESHOLD_SNAPSHOT_DIR.glob(f"pipeline_events_{target_date}_*.jsonl")))
    paths.extend(sorted(THRESHOLD_SNAPSHOT_DIR.glob(f"pipeline_events_{target_date}_*.jsonl.gz")))
    paths.extend(sorted(THRESHOLD_SNAPSHOT_DIR.glob(f"threshold_events_{target_date}_*.jsonl")))
    paths.extend(sorted(THRESHOLD_SNAPSHOT_DIR.glob(f"threshold_events_{target_date}_*.jsonl.gz")))
    return paths


def _iter_jsonl(path: Path, *, filter_entry_tokens: bool = True) -> Iterable[dict[str, Any]]:
    try:
        with _open_text(path) as handle:
            for line in handle:
                if not line:
                    continue
                if filter_entry_tokens and not any(
                    token in line
                    for token in (
                        "scalp",
                        "ENTRY_PIPELINE",
                        "ai_",
                        "entry_submit",
                        "pre_submit",
                        "order_bundle",
                    )
                ):
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(payload, dict):
                    fields = payload.get("fields") if isinstance(payload.get("fields"), dict) else {}
                    if str(fields.get("runtime_family") or "") == "entry_cancel_wait_runtime":
                        continue
                    yield payload
    except OSError:
        return


def _event_fields(event: dict[str, Any]) -> dict[str, Any]:
    fields = event.get("fields")
    if isinstance(fields, dict):
        return fields
    return {}


def _is_early_accel_recheck_retry_event(event: dict[str, Any]) -> bool:
    fields = _event_fields(event)
    return (
        str(fields.get("ai_call_trigger_reason") or "") == "early_accel_recheck"
        or str(fields.get("tuning_authority_excluded_reason") or "")
        == "early_accel_recheck_operator_retry"
    )


def _record_key(event: dict[str, Any]) -> str:
    fields = _event_fields(event)
    for key in ("candidate_id", "entry_adm_candidate_id", "sim_record_id", "record_id"):
        value = _nonempty(fields.get(key) or event.get(key))
        if value:
            return value
    return f"{event.get('stock_code') or ''}:{event.get('stage') or ''}:{event.get('emitted_at') or ''}"


def _iter_relevant_events(target_date: str) -> Iterable[dict[str, Any]]:
    seen: set[str] = set()
    for path in _event_paths(target_date):
        for event in _iter_jsonl(path):
            stage = str(event.get("stage") or "").strip()
            if stage not in RELEVANT_STAGES:
                continue
            if _is_early_accel_recheck_retry_event(event):
                continue
            if str(event.get("emitted_date") or target_date)[:10] != target_date:
                continue
            key = "|".join(
                [
                    str(stage),
                    str(event.get("stock_code") or ""),
                    str(event.get("record_id") or ""),
                    str(event.get("emitted_at") or ""),
                    _record_key(event),
                ]
            )
            if key in seen:
                continue
            seen.add(key)
            event["_source_path"] = str(path)
            yield event


def _score_bucket(score: Any, *, stage: str = "") -> str:
    value = _safe_float(score, None)
    if value is None:
        if stage in SCORE_CONTEXT_NOT_AVAILABLE_STAGES:
            return "score_not_available"
        return "score_unknown"
    if value < 50:
        return "score_lt50"
    if value < 65:
        return "score50_64"
    if value < 75:
        return "score65_74"
    if value < 85:
        return "score75_84"
    return "score85_plus"


def _score_source(fields: dict[str, Any]) -> Any:
    for key in (
        "ai_score",
        "ai_score_after_bonus",
        "current_ai_score",
        "ai_score_raw",
        "entry_score",
        "score",
        "swing_entry_recovery_gate_score",
    ):
        value = fields.get(key)
        if _safe_float(value, None) is not None:
            return value
    return None


def _time_bucket(value: Any) -> str:
    return entry_adm_time_bucket(value)


def _stale_bucket(fields: dict[str, Any]) -> str:
    if _safe_bool(fields.get("entry_submit_revalidation_block")) or _safe_bool(fields.get("quote_stale")):
        return "stale_block"
    quote_age = _safe_float(fields.get("quote_age_ms") or fields.get("context_age_ms"), None)
    if quote_age is None:
        return "stale_not_available"
    if quote_age > 3000:
        return "stale_high"
    if quote_age > 1000:
        return "stale_watch"
    return "fresh"


def _liquidity_bucket(fields: dict[str, Any]) -> str:
    sim_action = _nonempty(fields.get("sim_pre_submit_liquidity_guard_action")).upper()
    sim_reason = _nonempty(fields.get("sim_pre_submit_liquidity_reason"))
    if sim_action == "WOULD_BLOCK":
        return sim_reason or "liquidity_blocked"
    if sim_action == "WOULD_PASS" and sim_reason == "liquidity_ok":
        return "liquidity_ok"
    if sim_action == "WOULD_PASS" and sim_reason in {"liquidity_unknown", "liquidity_not_available"}:
        return "liquidity_not_available"
    if sim_action == "WOULD_UNKNOWN":
        return "liquidity_not_available" if not sim_reason or sim_reason == "liquidity_unknown" else sim_reason
    if _safe_bool(fields.get("liquidity_blocked")) or "liquidity" in str(fields.get("blocked_reason") or ""):
        return "liquidity_blocked"
    value = _safe_float(
        fields.get("sim_liquidity_value")
        or fields.get("liquidity_value")
        or fields.get("trade_value_krw")
        or fields.get("liquidity_score"),
        None,
    )
    min_liquidity = _safe_float(fields.get("sim_min_liquidity") or fields.get("min_liquidity"), None)
    if value is None:
        return "liquidity_not_available"
    if min_liquidity is not None and value < min_liquidity:
        return "below_min_liquidity"
    if value < 100_000_000:
        return "liquidity_low"
    if value < 500_000_000:
        return "liquidity_mid"
    return "liquidity_high"


def _overbought_bucket(fields: dict[str, Any]) -> str:
    sim_action = _nonempty(fields.get("sim_pre_submit_overbought_guard_action")).upper()
    sim_reason = _nonempty(fields.get("sim_pre_submit_overbought_reason"))
    if sim_action == "WOULD_BLOCK":
        return sim_reason or "overbought_blocked"
    if sim_action == "WOULD_PASS" and sim_reason == "overbought_ok":
        return "overbought_ok"
    if sim_action == "WOULD_PASS" and sim_reason in {"overbought_unknown", "overbought_not_available"}:
        return "overbought_not_available"
    if _safe_bool(fields.get("overbought_blocked")) or "overbought" in str(fields.get("blocked_reason") or ""):
        return "overbought_blocked"
    risk_state = _nonempty(fields.get("sim_overbought_risk_state") or fields.get("overbought_risk_state"))
    if risk_state in {"pullback_observed", "rebreak_candidate"}:
        return "overbought_ok"
    if risk_state:
        return risk_state
    intraday_range = _safe_float(fields.get("intraday_range_pct"), None)
    distance_high = _safe_float(fields.get("distance_from_day_high_pct"), None)
    if intraday_range is None:
        return "overbought_not_available"
    if intraday_range >= 18 and (distance_high is None or distance_high > -1.0):
        return "overbought_chase_risk"
    if intraday_range >= 10:
        return "overbought_watch"
    return "overbought_normal"


def _risk_context_bucket(fields: dict[str, Any], *, stage: str = "") -> str:
    if _safe_bool(fields.get("source_quality_blocked")) or _nonempty(fields.get("source_quality_block_reason")):
        return "source_quality_blocker"
    strength = _safe_float(fields.get("latest_strength") or fields.get("strength_momentum"), None)
    buy_pressure = _safe_float(fields.get("buy_pressure_10t") or fields.get("buy_pressure"), None)
    vpw = _safe_float(fields.get("vpw"), None)
    if strength is None and buy_pressure is None and vpw is None:
        if stage in PRE_SUBMIT_CONTEXT_OPTIONAL_STAGES:
            return "risk_context_not_available"
        return "risk_unknown"
    if (strength is not None and strength < 80) or (buy_pressure is not None and buy_pressure < 40):
        return "weak_strength_momentum"
    if (strength is not None and strength >= 140) or (buy_pressure is not None and buy_pressure >= 70):
        return "strong_strength_momentum"
    return "neutral_strength_momentum"


def _market_regime_continuous_bucket(fields: dict[str, Any]) -> str | None:
    bucket = entry_adm_market_regime_continuous_bucket(
        label=fields.get("market_regime_continuous_label"),
        score=fields.get("market_regime_continuous_score"),
    )
    if bucket == "-":
        return None
    return bucket


def _price_resolution_bucket(fields: dict[str, Any], *, stage: str = "") -> str:
    action = _nonempty(fields.get("ai_entry_price_canary_action"))
    reason = _nonempty(fields.get("price_resolution_reason") or fields.get("entry_price_resolution_reason"))
    if action == "USE_DEFENSIVE" or "defensive" in reason.lower():
        return "defensive_limit"
    if _nonempty(fields.get("resolved_order_price")):
        return "resolved_price"
    if _nonempty(fields.get("best_ask")) or _nonempty(fields.get("best_bid")):
        return "quote_based"
    if stage in PRE_SUBMIT_CONTEXT_OPTIONAL_STAGES:
        return "price_not_available_pre_submit"
    return "price_unknown"


def _chosen_action(stage: str, fields: dict[str, Any]) -> str:
    source_stage = _nonempty(fields.get("source_stage"))
    effective_stage = source_stage if stage == "scalp_entry_action_decision_snapshot" and source_stage else stage
    explicit = _nonempty(fields.get("chosen_action") or fields.get("entry_adm_chosen_action"))
    if explicit in ACTION_ORDER:
        if (
            effective_stage in {"latency_pass", "order_bundle_submitted"}
            and explicit not in {"BUY_NOW", "BUY_DEFENSIVE"}
        ):
            return "BUY_DEFENSIVE" if _price_resolution_bucket(fields) == "defensive_limit" else "BUY_NOW"
        return explicit
    stage = effective_stage
    if stage in {
        "pre_submit_liquidity_guard_block",
        "pre_submit_overbought_pullback_guard_block",
        "scalp_sim_entry_ai_price_skip_order",
        "scalp_sim_pre_submit_liquidity_guard_would_block",
        "scalp_sim_pre_submit_overbought_guard_would_block",
    }:
        return "SKIP_PRE_SUBMIT_SAFETY"
    if stage == "scalp_sim_pre_submit_liquidity_guard_unknown":
        return "SKIP_SOURCE_QUALITY"
    if stage in {"entry_submit_revalidation_block", "scalp_sim_entry_submit_revalidation_block"}:
        return "SKIP_STALE"
    if stage in {"entry_submit_revalidation_warning", "scalp_sim_entry_submit_revalidation_warning", "latency_block"}:
        return "WAIT_REQUOTE"
    if stage == "blocked_ai_score":
        reason = str(fields.get("ai_input_source_quality_reason") or fields.get("blocked_reason") or "")
        return "SKIP_SOURCE_QUALITY" if "source" in reason or "stale" in reason else "NO_BUY_AI"
    if stage == "ai_confirmed":
        action = str(fields.get("action") or "").upper()
        score = _safe_float(fields.get("ai_score") or fields.get("ai_score_after_bonus"), 0.0) or 0.0
        return "BUY_NOW" if action == "BUY" and score >= 75 else "NO_BUY_AI"
    if stage in {
        "order_bundle_submitted",
        "scalp_sim_entry_ai_price_applied",
        "scalp_sim_buy_order_assumed_filled",
        "scalp_sim_pre_submit_liquidity_guard_would_pass",
        "scalp_sim_pre_submit_overbought_guard_would_pass",
    }:
        return "BUY_DEFENSIVE" if _price_resolution_bucket(fields) == "defensive_limit" else "BUY_NOW"
    if stage in {"scalp_sim_entry_armed", "latency_pass"}:
        return "BUY_DEFENSIVE" if _price_resolution_bucket(fields) == "defensive_limit" else "BUY_NOW"
    return "NO_BUY_AI"


def _raw_chosen_action(fields: dict[str, Any]) -> str:
    return _nonempty(fields.get("chosen_action") or fields.get("entry_adm_chosen_action"))


def _action_normalization_reason(stage: str, fields: dict[str, Any], action: str) -> str:
    raw_action = _raw_chosen_action(fields)
    source_stage = _nonempty(fields.get("source_stage"))
    effective_stage = source_stage if stage == "scalp_entry_action_decision_snapshot" and source_stage else stage
    if (
        raw_action
        and raw_action != action
        and effective_stage in {"latency_pass", "order_bundle_submitted"}
        and action in {"BUY_NOW", "BUY_DEFENSIVE"}
    ):
        return "submitted_or_latency_pass_non_buy_action_normalized"
    return ""


def _eligible_actions(action: str, fields: dict[str, Any]) -> list[str]:
    explicit = _nonempty(fields.get("eligible_actions"))
    if explicit:
        return [item for item in explicit.replace("|", ",").split(",") if item]
    if action in {"BUY_NOW", "BUY_DEFENSIVE"}:
        return ["BUY_NOW", "BUY_DEFENSIVE", "WAIT_REQUOTE", "NO_BUY_AI"]
    if action in {"WAIT_REQUOTE", "SKIP_STALE"}:
        return ["WAIT_REQUOTE", "SKIP_STALE", "NO_BUY_AI"]
    if action == "SKIP_PRE_SUBMIT_SAFETY":
        return ["SKIP_PRE_SUBMIT_SAFETY", "NO_BUY_AI"]
    return ["NO_BUY_AI"]


def _adm_source_bucket_value(fields: dict[str, Any], adm_key: str, fallback_value: str) -> tuple[str, str]:
    adm_value = _nonempty(fields.get(adm_key))
    if adm_value:
        return adm_value, "adm_field"
    return fallback_value, "raw_recomputed"


def _base_row(event: dict[str, Any]) -> dict[str, Any]:
    fields = _event_fields(event)
    stage = str(event.get("stage") or "")
    action = _chosen_action(stage, fields)
    raw_action = _raw_chosen_action(fields)
    source_stage = _nonempty(fields.get("source_stage")) or stage
    effective_bucket_stage = source_stage if stage == "scalp_entry_action_decision_snapshot" else stage
    normalization_reason = _action_normalization_reason(stage, fields, action)
    candidate_id = (
        _nonempty(fields.get("entry_adm_candidate_id"))
        or _nonempty(fields.get("candidate_id"))
        or _nonempty(fields.get("sim_record_id"))
        or _nonempty(event.get("record_id"))
        or _record_key(event)
    )
    sim_record_id = _nonempty(fields.get("sim_record_id"))

    raw_score_value = _score_source(fields)
    raw_score_bucket = _score_bucket(raw_score_value, stage=effective_bucket_stage)
    raw_risk_bucket = _risk_context_bucket(fields, stage=effective_bucket_stage)
    raw_stale = _stale_bucket(fields)
    raw_price = _price_resolution_bucket(fields, stage=effective_bucket_stage)
    raw_liquidity = _liquidity_bucket(fields)
    raw_overbought = _overbought_bucket(fields)
    raw_market_regime_continuous = _market_regime_continuous_bucket(fields) or "-"

    score_bucket, score_prov = _adm_source_bucket_value(fields, "entry_adm_score_bucket", raw_score_bucket)
    risk_context_bucket, risk_prov = _adm_source_bucket_value(fields, "entry_adm_risk_context_bucket", raw_risk_bucket)
    market_regime_continuous_bucket, market_prov = _adm_source_bucket_value(
        fields,
        "entry_adm_market_regime_continuous_bucket",
        raw_market_regime_continuous,
    )
    stale_bucket, stale_prov = _adm_source_bucket_value(fields, "entry_adm_stale_bucket", raw_stale)
    price_resolution_bucket, price_prov = _adm_source_bucket_value(fields, "entry_adm_price_resolution_bucket", raw_price)
    liquidity_bucket, liquidity_prov = _adm_source_bucket_value(fields, "entry_adm_liquidity_bucket", raw_liquidity)
    overbought_bucket, overbought_prov = _adm_source_bucket_value(fields, "entry_adm_overbought_bucket", raw_overbought)

    raw_entry_adm_bucket_token = _nonempty(fields.get("entry_adm_bucket_token"))
    row = {
        "candidate_id": candidate_id,
        "record_id": _nonempty(event.get("record_id") or fields.get("record_id")),
        "sim_record_id": sim_record_id,
        "stock_code": _nonempty(event.get("stock_code") or fields.get("stock_code")),
        "stock_name": _nonempty(event.get("stock_name") or fields.get("stock_name")),
        "stage": stage,
        "source_stage": source_stage,
        "event_time": _nonempty(event.get("emitted_at")),
        "source_path": event.get("_source_path"),
        "ai_score": _safe_float(fields.get("ai_score") or fields.get("ai_score_after_bonus"), None),
        "score_source_value": _safe_float(raw_score_value, None),
        "ai_action": _nonempty(fields.get("action") or fields.get("ai_action")),
        "chosen_action": action,
        "raw_chosen_action": raw_action,
        "action_normalized": bool(normalization_reason),
        "action_normalization_reason": normalization_reason,
        "eligible_actions": _eligible_actions(action, fields),
        "rejected_actions": [item for item in ACTION_ORDER if item not in _eligible_actions(action, fields)],
        "score_bucket": score_bucket,
        "risk_context_bucket": risk_context_bucket,
        "market_regime_continuous_bucket": market_regime_continuous_bucket,
        "market_regime": _nonempty(fields.get("market_regime")),
        "market_regime_continuous_score": _safe_float(fields.get("market_regime_continuous_score"), None),
        "market_regime_continuous_label": _nonempty(fields.get("market_regime_continuous_label")),
        "market_regime_component_scores": (
            fields.get("market_regime_component_scores")
            if isinstance(fields.get("market_regime_component_scores"), dict)
            else None
        ),
        "swing_entry_recovery_gate_score": _safe_float(fields.get("swing_entry_recovery_gate_score"), None),
        "market_regime_score_version": _nonempty(fields.get("market_regime_score_version")),
        "market_regime_source_quality": _nonempty(fields.get("market_regime_source_quality")),
        "risk_context_owner": _nonempty(fields.get("risk_context_owner")),
        "stale_bucket": stale_bucket,
        "price_resolution_bucket": price_resolution_bucket,
        "liquidity_bucket": liquidity_bucket,
        "overbought_bucket": overbought_bucket,
        "time_bucket": _time_bucket(event.get("emitted_at") or fields.get("tick_latest_time")),
        "actual_order_submitted": _safe_bool(fields.get("actual_order_submitted"), stage == "order_bundle_submitted"),
        "broker_order_forbidden": _safe_bool(fields.get("broker_order_forbidden"), stage.startswith("scalp_sim_") or action not in {"BUY_NOW", "BUY_DEFENSIVE"}),
        "broker_order_submitted": _safe_bool(fields.get("broker_order_submitted"), stage == "order_bundle_submitted"),
        "broker_order_no": _nonempty(fields.get("broker_order_no")),
        "order_no": _nonempty(fields.get("order_no")),
        "ord_no": _nonempty(fields.get("ord_no")),
        "broker_order_no_list": _nonempty(fields.get("broker_order_no_list")),
        "order_response_ord_no": _nonempty(fields.get("order_response_ord_no")),
        "submit_attempt_id": _nonempty(fields.get("submit_attempt_id")),
        "context_age_ms": _safe_float(fields.get("context_age_ms") or fields.get("tick_latest_age_ms"), None),
        "quote_age_ms": _safe_float(fields.get("quote_age_ms") or fields.get("quote_age_at_submit_ms"), None),
        "latency_state": _nonempty(fields.get("latency_state") or fields.get("latency")),
        "latency_reason": _nonempty(fields.get("latency_reason") or fields.get("latency_danger_reasons") or fields.get("reason")),
        "entry_submit_revalidation_warning": _optional_flag_reason(fields.get("entry_submit_revalidation_warning")),
        "entry_submit_revalidation_block": _optional_flag_reason(fields.get("entry_submit_revalidation_block")),
        "best_bid": _safe_float(fields.get("best_bid") or fields.get("best_bid_at_submit"), None),
        "best_ask": _safe_float(fields.get("best_ask") or fields.get("best_ask_at_submit"), None),
        "resolved_order_price": _safe_float(
            fields.get("resolved_order_price") or fields.get("submitted_order_price") or fields.get("order_price"),
            None,
        ),
        "would_limit_fill": _safe_bool(fields.get("would_limit_fill")),
        "pre_submit_quote_refresh_enabled": _safe_bool(fields.get("pre_submit_quote_refresh_enabled")),
        "pre_submit_quote_refresh_applied": _safe_bool(fields.get("pre_submit_quote_refresh_applied")),
        "pre_submit_quote_refresh_reason": _nonempty(fields.get("pre_submit_quote_refresh_reason")),
        "pre_submit_quote_refresh_source": _nonempty(fields.get("pre_submit_quote_refresh_source")),
        "pre_submit_quote_refresh_quote_age_ms": _safe_float(fields.get("pre_submit_quote_refresh_quote_age_ms"), None),
        "pre_submit_quote_refresh_strategy_id": _nonempty(fields.get("pre_submit_quote_refresh_strategy_id")),
        "pre_submit_quote_refresh_env_value": _nonempty(fields.get("pre_submit_quote_refresh_env_value")),
        "pre_submit_ws_snapshot_refresh_enabled": _safe_bool(fields.get("pre_submit_ws_snapshot_refresh_enabled")),
        "pre_submit_ws_snapshot_refresh_applied": _safe_bool(fields.get("pre_submit_ws_snapshot_refresh_applied")),
        "pre_submit_ws_snapshot_refresh_reason": _nonempty(fields.get("pre_submit_ws_snapshot_refresh_reason")),
        "pre_submit_ws_snapshot_refresh_source": _nonempty(fields.get("pre_submit_ws_snapshot_refresh_source")),
        "pre_submit_ws_snapshot_refresh_age_ms": _safe_float(fields.get("pre_submit_ws_snapshot_refresh_age_ms"), None),
        "source_quality_block_reason": _nonempty(fields.get("source_quality_block_reason") or fields.get("ai_input_source_quality_reason")),
        "gate_action": _nonempty(fields.get("gate_action")),
        "entry_adm_prompt_applied": _safe_bool(fields.get("entry_adm_prompt_applied")),
        "entry_adm_version": _nonempty(fields.get("entry_adm_version")),
        "entry_adm_source_date": _nonempty(fields.get("entry_adm_source_date")),
        "entry_adm_bucket_token": raw_entry_adm_bucket_token,
        "entry_adm_decision_alignment": _nonempty(fields.get("entry_adm_decision_alignment")),
        "entry_adm_runtime_effect": _nonempty(fields.get("entry_adm_runtime_effect")),
        "entry_adm_forced_action": _nonempty(fields.get("entry_adm_forced_action")),
        "entry_adm_runtime_reason": _nonempty(fields.get("entry_adm_runtime_reason")),
        "entry_adm_runtime_bias_applied": _safe_bool(fields.get("entry_adm_runtime_bias_applied")),
        "entry_adm_bucket_lookup_status": _nonempty(fields.get("entry_adm_bucket_lookup_status")),
        "entry_adm_bucket_sample_count": _safe_int(fields.get("entry_adm_bucket_sample_count"), 0),
        "entry_adm_bucket_joined_sample": _safe_int(fields.get("entry_adm_bucket_joined_sample"), 0),
        "bucket_field_provenance": {
            "score_bucket": score_prov,
            "risk_context_bucket": risk_prov,
            "market_regime_continuous_bucket": market_prov,
            "stale_bucket": stale_prov,
            "price_resolution_bucket": price_prov,
            "liquidity_bucket": liquidity_prov,
            "overbought_bucket": overbought_prov,
        },
    }
    row["entry_adm_bucket_token_recomputed"] = entry_adm_bucket_token(row)
    row["entry_adm_bucket_schema_version"] = ENTRY_ADM_BUCKET_SCHEMA_VERSION
    row["raw_token_preserved"] = bool(raw_entry_adm_bucket_token)
    row["adm_token_backfill_applied"] = bool(
        raw_entry_adm_bucket_token
        and raw_entry_adm_bucket_token != row["entry_adm_bucket_token_recomputed"]
    )
    if not row["sim_record_id"] and str(stage).startswith("scalp_sim_"):
        row["sim_record_id"] = candidate_id if str(candidate_id).startswith("SCALPSIM-") else ""
    return row


def _load_sim_evaluations(target_date: str) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    path = existing_or_gzip_path(POST_SELL_DIR / f"sim_post_sell_evaluations_{target_date}.jsonl")
    by_key: dict[str, dict[str, Any]] = {}
    total = 0
    joined_keys: set[str] = set()
    if not path.exists():
        return by_key, {"artifact": None, "rows": 0, "join_keys": 0}
    for item in _iter_jsonl(path, filter_entry_tokens=False):
        total += 1
        for key in (
            _nonempty(item.get("candidate_id")),
            _nonempty(item.get("entry_adm_candidate_id")),
            _nonempty(item.get("sim_record_id")),
        ):
            if key:
                by_key[key] = item
                joined_keys.add(key)
    return by_key, {"artifact": str(path), "rows": total, "join_keys": len(joined_keys)}


def _load_prior_adm_bucket_summary(target_date: str) -> dict[str, dict[str, Any]]:
    try:
        target_dt = date.fromisoformat(target_date)
    except ValueError:
        return {}
    prior_date = target_dt - __import__("datetime").timedelta(days=1)
    prior_path = ADM_REPORT_DIR / f"scalp_entry_action_decision_matrix_{prior_date.isoformat()}.json"
    gz_path = prior_path.with_suffix(prior_path.suffix + ".gz")
    for path in (prior_path, gz_path):
        real_path = existing_or_gzip_path(path)
        if real_path.exists():
            try:
                with _open_text(real_path) as handle:
                    payload = json.loads(handle.read())
            except Exception:
                return {}
            if not isinstance(payload, dict):
                return {}
            bucket_list = payload.get("bucket_summary") if isinstance(payload.get("bucket_summary"), list) else []
            by_token: dict[str, dict[str, Any]] = {}
            for item in bucket_list:
                if isinstance(item, dict):
                    token = str(item.get("bucket_token") or "").strip()
                    if token:
                        by_token[token] = item
            return by_token
    return {}


def _backfill_adm_lookup_status(rows: list[dict[str, Any]], prior_summary: dict[str, dict[str, Any]]) -> None:
    if not prior_summary:
        return
    for row in rows:
        existing = str(row.get("entry_adm_bucket_lookup_status") or "").strip()
        if existing and existing not in {"-", ""}:
            continue
        token = str(
            row.get("entry_adm_bucket_token_recomputed")
            or row.get("entry_adm_bucket_token")
            or ""
        ).strip()
        if not token:
            continue
        prior_bucket = prior_summary.get(token)
        if prior_bucket is None:
            row["entry_adm_bucket_lookup_status"] = "new_or_unseen_token_vs_prior_adm"
            row["entry_adm_bucket_sample_count"] = 0
            row["entry_adm_bucket_joined_sample"] = 0
            continue
        sample = _safe_int(prior_bucket.get("sample_count"), -1)
        joined = _safe_int(prior_bucket.get("joined_sample"), -1)
        row["entry_adm_bucket_lookup_status"] = (
            "matched_prior_bucket" if sample > 0 or joined > 0
            else "prior_bucket_present_but_runtime_sample_missing"
        )
        row["entry_adm_bucket_sample_count"] = max(0, sample)
        row["entry_adm_bucket_joined_sample"] = max(0, joined)


def _classify_adm_lookup_not_applicable(rows: list[dict[str, Any]]) -> None:
    advisory_only_stages = {"ai_confirmed", "blocked_ai_score"}
    for row in rows:
        existing = str(row.get("entry_adm_bucket_lookup_status") or "").strip()
        if existing and existing not in {"-", "None"}:
            continue
        if str(row.get("stage") or "") not in advisory_only_stages:
            continue
        if not row.get("entry_adm_bucket_token_recomputed") and not row.get("entry_adm_bucket_token"):
            continue
        row["entry_adm_bucket_lookup_status"] = "advisory_only_stage_without_prior_lookup"
        row["entry_adm_bucket_lookup_not_applicable_reason"] = (
            "adm_prompt_context_stage_without_prior_bucket_lookup"
        )
        row["entry_adm_bucket_sample_count"] = 0
        row["entry_adm_bucket_joined_sample"] = 0


def _adm_lookup_closure_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts: Counter[str] = Counter()
    stage_counts: Counter[str] = Counter()
    producer_context_missing_counts: Counter[str] = Counter()
    for row in rows:
        status = str(row.get("entry_adm_bucket_lookup_status") or "").strip()
        if status != "new_or_unseen_token_vs_prior_adm":
            continue
        token = str(
            row.get("entry_adm_bucket_token_recomputed")
            or row.get("entry_adm_bucket_token")
            or ""
        )
        stage = str(row.get("stage") or "-")
        stage_counts[stage] += 1
        missing_contexts = []
        if "risk_context_not_available" in token:
            missing_contexts.append("risk_context_not_available")
        if "price_not_available_pre_submit" in token:
            missing_contexts.append("price_not_available_pre_submit")
        if "liquidity_not_available" in token:
            missing_contexts.append("liquidity_not_available")
        if missing_contexts:
            status_counts["producer_context_missing"] += 1
            for context in missing_contexts:
                producer_context_missing_counts[context] += 1
        elif stage in {"ai_confirmed", "blocked_ai_score"}:
            status_counts["advisory_or_not_applicable_stage"] += 1
        else:
            status_counts["new_bucket_candidate_waiting_prior_rollup"] += 1
    total = sum(status_counts.values())
    followup_required = status_counts.get("producer_context_missing", 0) > 0
    return {
        "new_or_unseen_total": total,
        "closure_status": "closed_with_producer_followup" if followup_required else "closed",
        "followup_required": followup_required,
        "status_counts": dict(status_counts),
        "producer_context_missing_counts": dict(producer_context_missing_counts),
        "top_stages": [[stage, count] for stage, count in stage_counts.most_common(10)],
        "decision_authority": "entry_adm_lookup_closure_diagnostic_only",
        "runtime_effect": False,
    }


def _apply_outcome(row: dict[str, Any], evaluations: dict[str, dict[str, Any]]) -> dict[str, Any]:
    evaluation = {}
    for key in (
        row.get("candidate_id"),
        row.get("sim_record_id"),
    ):
        if key and str(key) in evaluations:
            evaluation = evaluations[str(key)]
            break
    row = dict(row)
    row["outcome_joined"] = bool(evaluation)
    row["profit_rate"] = _safe_float(evaluation.get("profit_rate"), None) if evaluation else None
    row["exit_rule"] = _nonempty(evaluation.get("exit_rule")) if evaluation else ""
    row["sim_post_sell_outcome"] = _nonempty(evaluation.get("outcome")) if evaluation else ""
    for horizon in (10, 30, 60):
        metrics = evaluation.get(f"metrics_{horizon}m") if isinstance(evaluation.get(f"metrics_{horizon}m"), dict) else {}
        row[f"mfe_{horizon}m_pct"] = _safe_float(metrics.get("mfe_pct"), None) if metrics else None
        row[f"mae_{horizon}m_pct"] = _safe_float(metrics.get("mae_pct"), None) if metrics else None
        row[f"close_{horizon}m_pct"] = _safe_float(metrics.get("close_ret_pct"), None) if metrics else None
    mfe_30 = row.get("mfe_30m_pct")
    profit = row.get("profit_rate")
    row["missed_winner"] = bool(profit is not None and profit < 0 and mfe_30 is not None and mfe_30 >= 1.0)
    row["avoided_loser"] = bool(profit is not None and profit < 0 and row.get("chosen_action") in {"NO_BUY_AI", "SKIP_STALE", "SKIP_PRE_SUBMIT_SAFETY", "SKIP_SOURCE_QUALITY"})
    return row


def _dedupe_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    priority = {
        "scalp_sim_entry_ai_price_skip_order": -1,
        "scalp_sim_pre_submit_liquidity_guard_would_block": -1,
        "scalp_sim_pre_submit_overbought_guard_would_block": -1,
        "scalp_sim_pre_submit_liquidity_guard_unknown": -1,
        "scalp_entry_action_decision_snapshot": 0,
        "order_bundle_submitted": 1,
        "scalp_sim_buy_order_assumed_filled": 2,
        "scalp_sim_pre_submit_liquidity_guard_would_pass": 3,
        "scalp_sim_pre_submit_overbought_guard_would_pass": 3,
        "scalp_sim_buy_order_virtual_pending": 3,
        "pre_submit_liquidity_guard_block": 3,
        "pre_submit_overbought_pullback_guard_block": 3,
        "entry_submit_revalidation_block": 4,
        "scalp_sim_entry_submit_revalidation_block": 4,
        "scalp_sim_entry_submit_revalidation_warning": 5,
        "blocked_ai_score": 5,
        "ai_confirmed": 6,
    }
    grouped: dict[str, dict[str, Any]] = {}
    for row in rows:
        key = str(row.get("candidate_id") or row.get("record_id") or f"{row.get('stock_code')}:{row.get('event_time')}")
        current = grouped.get(key)
        if not current or priority.get(str(row.get("stage")), 99) < priority.get(str(current.get("stage")), 99):
            grouped[key] = row
    return sorted(grouped.values(), key=lambda item: str(item.get("event_time") or ""))


def _avg(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 4)


def _action_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for action in ACTION_ORDER:
        subset = [row for row in rows if row.get("chosen_action") == action]
        joined = [row for row in subset if row.get("outcome_joined") and row.get("profit_rate") is not None]
        profits = [float(row["profit_rate"]) for row in joined if row.get("profit_rate") is not None]
        join_rate = (len(joined) / len(subset)) if subset else 0.0
        outcomes = Counter(str(row.get("sim_post_sell_outcome") or "unjoined") for row in subset)
        summaries.append(
            {
                "action": action,
                "sample_count": len(subset),
                "joined_sample": len(joined),
                "diagnostic_win_rate_pct": round((sum(1 for value in profits if value > 0) / len(profits)) * 100.0, 2) if profits else 0.0,
                "simple_sum_profit_pct": round(sum(profits), 4),
                "equal_weight_avg_profit_pct": _avg(profits),
                "source_quality_adjusted_ev_pct": round((_avg(profits) or 0.0) * join_rate, 4) if subset else None,
                "missed_winner_count": sum(1 for row in subset if row.get("missed_winner")),
                "avoided_loser_count": sum(1 for row in subset if row.get("avoided_loser")),
                "outcome_counts": dict(outcomes),
            }
        )
    return summaries


def _bucket_token(row: dict[str, Any]) -> str:
    return entry_adm_bucket_token(row)


def _bucket_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[_bucket_token(row)].append(row)
    summaries: list[dict[str, Any]] = []
    for token, subset in grouped.items():
        joined = [row for row in subset if row.get("outcome_joined") and row.get("profit_rate") is not None]
        profits = [float(row["profit_rate"]) for row in joined if row.get("profit_rate") is not None]
        summaries.append(
            {
                "bucket_token": token,
                "sample_count": len(subset),
                "joined_sample": len(joined),
                "dominant_action": Counter(str(row.get("chosen_action")) for row in subset).most_common(1)[0][0],
                "equal_weight_avg_profit_pct": _avg(profits),
                "source_quality_adjusted_ev_pct": round((_avg(profits) or 0.0) * (len(joined) / len(subset)), 4) if subset else None,
                "missed_winner_count": sum(1 for row in subset if row.get("missed_winner")),
                "avoided_loser_count": sum(1 for row in subset if row.get("avoided_loser")),
            }
        )
    return sorted(summaries, key=lambda item: (-_safe_int(item.get("sample_count")), item.get("bucket_token") or ""))[:50]


def _parse_event_ts(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return None


def _score_backfill_keys(row: dict[str, Any]) -> set[str]:
    keys: set[str] = set()
    for key in SCORE_BACKFILL_KEY_FIELDS:
        value = _nonempty(row.get(key))
        if value:
            keys.add(f"{key}:{value}")
    return keys


def _prior_score_candidate(
    candidates: Iterable[dict[str, Any]],
    *,
    event_ts: datetime,
) -> tuple[dict[str, Any] | None, float | None]:
    best_row = None
    best_seconds = None
    for scored in candidates:
        scored_ts = _parse_event_ts(scored.get("event_time"))
        if scored_ts is None:
            continue
        seconds_since_source = (event_ts - scored_ts).total_seconds()
        if seconds_since_source < 0 or seconds_since_source > SCORE_BACKFILL_MAX_PAST_SECONDS:
            continue
        if best_seconds is None or seconds_since_source < best_seconds:
            best_row = scored
            best_seconds = seconds_since_source
    return best_row, best_seconds


def _backfill_score_context(rows: list[dict[str, Any]], source_rows: list[dict[str, Any]] | None = None) -> None:
    scored_by_stock: dict[str, list[dict[str, Any]]] = defaultdict(list)
    scored_by_key: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in source_rows or rows:
        score = _safe_float(row.get("score_source_value"), None)
        stock_code = _nonempty(row.get("stock_code"))
        event_ts = _parse_event_ts(row.get("event_time"))
        if score is None or not stock_code or event_ts is None:
            continue
        scored_by_stock[stock_code].append(row)
        for key in _score_backfill_keys(row):
            scored_by_key[key].append(row)

    for scored_rows in scored_by_stock.values():
        scored_rows.sort(key=lambda item: item.get("event_time") or "")
    for scored_rows in scored_by_key.values():
        scored_rows.sort(key=lambda item: item.get("event_time") or "")

    for row in rows:
        if row.get("score_source_value") is not None:
            continue
        stage = str(row.get("stage") or "")
        if stage not in SCORE_CONTEXT_BACKFILL_ELIGIBLE_STAGES:
            continue
        stock_code = _nonempty(row.get("stock_code"))
        event_ts = _parse_event_ts(row.get("event_time"))
        if not stock_code or event_ts is None:
            continue
        key_candidates: list[dict[str, Any]] = []
        for key in _score_backfill_keys(row):
            key_candidates.extend(scored_by_key.get(key, []))
        best_row, best_seconds = _prior_score_candidate(key_candidates, event_ts=event_ts)
        match_type = "exact_key" if best_row is not None else "prior_same_stock_time"
        if best_row is None:
            best_row, best_seconds = _prior_score_candidate(
                scored_by_stock.get(stock_code, []),
                event_ts=event_ts,
            )
        if best_row is None:
            continue
        score = _safe_float(best_row.get("score_source_value"), None)
        if score is None:
            continue
        provenance = row.get("bucket_field_provenance")
        if not isinstance(provenance, dict):
            provenance = {}
            row["bucket_field_provenance"] = provenance
        row["score_source_value"] = score
        row["score_bucket"] = _score_bucket(score)
        row["score_backfill_source"] = "prior_score_event"
        row["score_backfill_match_type"] = match_type
        row["score_backfill_source_stage"] = best_row.get("stage")
        row["score_backfill_source_event_time"] = best_row.get("event_time")
        row["score_backfill_source_candidate_id"] = best_row.get("candidate_id")
        row["score_backfill_seconds_since_source"] = round(float(best_seconds or 0.0), 3)
        row["score_backfill_abs_seconds"] = round(float(best_seconds or 0.0), 3)
        provenance["score_bucket"] = "backfilled"
        row["entry_adm_bucket_token_recomputed"] = entry_adm_bucket_token(row)


def _is_not_available_bucket(value: str) -> bool:
    return "not_available" in str(value or "").lower()


def _is_unknown_bucket(value: str) -> bool:
    compact = str(value or "").lower()
    return "unknown" in compact and "not_available" not in compact


def _context_unknown_reason(row: dict[str, Any], key: str, provenance_value: str) -> str:
    stage = str(row.get("stage") or "").strip()
    if stage and stage not in {"scalp_entry_action_decision_snapshot", "entry"}:
        return "post_submit_or_exit_not_required"
    if provenance_value == "adm_field":
        return "producer_context_missing"
    if key == "risk_context_bucket":
        context_values = [
            row.get("risk_regime_mode"),
            row.get("panic_regime_mode"),
            row.get("panic_buy_regime_mode"),
        ]
        return "source_field_missing" if not any(v not in (None, "") for v in context_values) else "backfilled"
    if key == "price_resolution_bucket":
        price_values = [
            row.get("order_price"),
            row.get("curr_price"),
            row.get("current_price"),
            row.get("best_bid"),
            row.get("best_ask"),
        ]
        return "source_field_missing" if not any(v not in (None, "") for v in price_values) else "backfilled"
    return "source_field_missing"


def _unknown_bucket_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    dimensions = ENTRY_ADM_BUCKET_DIMENSIONS
    total = len(rows)
    dimension_counts: dict[str, int] = {}
    not_available_counts: dict[str, int] = {}
    unknown_affected_row_count = 0
    not_available_affected_row_count = 0
    stage_counts: Counter[str] = Counter()
    unknown_root_causes: Counter[str] = Counter()
    unknown_root_cause_detail_counts: Counter[str] = Counter()
    unknown_resolution_route_counts: Counter[str] = Counter()
    score_root_cause_counts: Counter[str] = Counter()
    score_backfill_match_type_counts: Counter[str] = Counter()
    examples: list[dict[str, Any]] = []
    adm_source_count = 0
    raw_recomputed_count = 0
    adm_source_total = 0
    for row in rows:
        provenance = row.get("bucket_field_provenance")
        if isinstance(provenance, dict):
            adm_count = sum(1 for v in provenance.values() if v == "adm_field")
            raw_count = sum(1 for v in provenance.values() if v == "raw_recomputed")
            adm_source_total += adm_count
            raw_recomputed_count += raw_count
            if adm_count > 0:
                adm_source_count += 1
            if (
                row.get("score_source_value") is not None
                and provenance.get("score_bucket") in {"raw_recomputed", "backfilled"}
            ):
                score_root_cause_counts["backfilled"] += 1
                if provenance.get("score_bucket") == "backfilled":
                    score_backfill_match_type_counts[str(row.get("score_backfill_match_type") or "unknown")] += 1
        unknown_dimensions = [
            key for key in dimensions if _is_unknown_bucket(row.get(key) or "")
        ]
        not_available_dimensions = [
            key for key in dimensions if _is_not_available_bucket(row.get(key) or "")
        ]
        if not unknown_dimensions and not not_available_dimensions:
            continue
        if unknown_dimensions:
            unknown_affected_row_count += 1
        if not_available_dimensions:
            not_available_affected_row_count += 1
        for key in unknown_dimensions:
            dimension_counts[key] = dimension_counts.get(key, 0) + 1
            provenance_value = ""
            if isinstance(provenance, dict):
                provenance_value = str(provenance.get(key) or "")
            if provenance_value == "adm_field":
                unknown_root_causes[f"{key}:adm_field_unknown"] += 1
                if key == "score_bucket":
                    score_root_cause_counts["missing"] += 1
            elif key == "score_bucket" and row.get("score_source_value") is None:
                unknown_root_causes[f"{key}:source_score_missing"] += 1
                score_root_cause_counts["missing"] += 1
            elif key == "risk_context_bucket":
                reason = _context_unknown_reason(row, key, provenance_value)
                unknown_root_causes[f"{key}:{reason}"] += 1
                unknown_root_cause_detail_counts[f"{key}:{reason}"] += 1
                unknown_resolution_route_counts[reason] += 1
            elif key == "price_resolution_bucket":
                reason = _context_unknown_reason(row, key, provenance_value)
                unknown_root_causes[f"{key}:{reason}"] += 1
                unknown_root_cause_detail_counts[f"{key}:{reason}"] += 1
                unknown_resolution_route_counts[reason] += 1
            else:
                unknown_root_causes[f"{key}:raw_recomputed_unknown"] += 1
                if key == "score_bucket":
                    score_root_cause_counts["missing"] += 1
        for key in not_available_dimensions:
            not_available_counts[key] = not_available_counts.get(key, 0) + 1
            if key == "score_bucket":
                score_root_cause_counts["not_applicable"] += 1
        stage_counts[str(row.get("stage") or "-")] += 1
        if len(examples) < 10:
            examples.append(
                {
                    "stage": row.get("stage"),
                    "stock_code": row.get("stock_code"),
                    "event_time": row.get("event_time"),
                    "unknown_dimensions": unknown_dimensions,
                    "not_available_dimensions": not_available_dimensions,
                    "bucket_token": entry_adm_bucket_token(row),
                    "bucket_provenance": provenance if isinstance(provenance, dict) else None,
                }
            )
    unknown_dimension_occurrence = sum(dimension_counts.values())
    not_available_dimension_occurrence = sum(not_available_counts.values())
    actionable_unknown_roots = {
        key: value
        for key, value in unknown_root_causes.items()
        if not key.endswith(":post_submit_or_exit_not_required") and not key.endswith(":backfilled")
    }
    unknown_source_quality_gate = (
        "source_quality_blocker"
        if actionable_unknown_roots
        else "classified_non_actionable"
        if unknown_affected_row_count
        else "pass"
    )
    unknown_recommended_route = (
        "source_quality_workorder"
        if actionable_unknown_roots
        else "classified_not_applicable_no_workorder"
        if unknown_affected_row_count
        else "none"
    )
    return {
        "affected_rows": unknown_affected_row_count,
        "not_available_affected_rows": not_available_affected_row_count,
        "unknown_dimension_occurrence_count": unknown_dimension_occurrence,
        "not_available_dimension_occurrence_count": not_available_dimension_occurrence,
        "total_rows": total,
        "affected_rate": round(unknown_affected_row_count / total, 4) if total else 0.0,
        "not_available_affected_rate": round(not_available_affected_row_count / total, 4) if total else 0.0,
        "dimension_counts": dimension_counts,
        "not_available_dimension_counts": not_available_counts,
        "stage_counts": dict(stage_counts),
        "unknown_root_cause_counts": dict(unknown_root_causes),
        "unknown_root_cause_detail_counts": dict(unknown_root_cause_detail_counts),
        "unknown_resolution_route_counts": dict(unknown_resolution_route_counts),
        "score_root_cause_counts": {
            "missing": score_root_cause_counts.get("missing", 0),
            "not_applicable": score_root_cause_counts.get("not_applicable", 0),
            "backfilled": score_root_cause_counts.get("backfilled", 0),
        },
        "score_backfill_match_type_counts": dict(score_backfill_match_type_counts),
        "examples": examples,
        "source_quality_gate": unknown_source_quality_gate,
        "recommended_route": unknown_recommended_route,
        "actionable_unknown_route_counts": dict(actionable_unknown_roots),
        "recomputed_unknown_count": raw_recomputed_count,
        "adm_source_bucket_used_count": adm_source_count,
        "adm_source_bucket_field_count": adm_source_total,
        "not_available_route": "field_legitimately_unavailable_no_workorder",
    }


def build_scalp_entry_action_decision_matrix_report(target_date: str) -> dict[str, Any]:
    target_date = str(target_date).strip()
    evaluations, eval_summary = _load_sim_evaluations(target_date)
    raw_rows = [_base_row(event) for event in _iter_relevant_events(target_date)]
    deduped_rows = _dedupe_rows(raw_rows)
    _backfill_score_context(deduped_rows, source_rows=raw_rows)
    rows = [_apply_outcome(row, evaluations) for row in deduped_rows]

    prior_summary = _load_prior_adm_bucket_summary(target_date)
    _backfill_adm_lookup_status(rows, prior_summary)
    _classify_adm_lookup_not_applicable(rows)

    action_counts = Counter(str(row.get("chosen_action")) for row in rows)
    raw_action_counts = Counter(str(row.get("raw_chosen_action") or "-") for row in rows)
    action_normalization_counts = Counter(
        str(row.get("action_normalization_reason") or "-")
        for row in rows
        if row.get("action_normalized")
    )
    zero_sample_actions = [action for action in ACTION_ORDER if action_counts.get(action, 0) == 0]
    missing_actions: list[str] = []
    joined_sample = sum(1 for row in rows if row.get("outcome_joined"))
    prompt_applied = sum(1 for row in rows if row.get("entry_adm_prompt_applied"))
    runtime_bias_applied = sum(1 for row in rows if row.get("entry_adm_runtime_bias_applied"))
    adm_bucket_lookup_status_counts = Counter(
        str(row.get("entry_adm_bucket_lookup_status") or "-") for row in rows
    )
    new_or_unseen_tokens = [
        row for row in rows
        if str(row.get("entry_adm_bucket_lookup_status") or "") == "new_or_unseen_token_vs_prior_adm"
    ]
    prior_bucket_sample_missing_rows = [
        row for row in rows
        if str(row.get("entry_adm_bucket_lookup_status") or "") == "prior_bucket_present_but_runtime_sample_missing"
    ]
    advisory_only_lookup_rows = [
        row for row in rows
        if str(row.get("entry_adm_bucket_lookup_status") or "")
        == "advisory_only_stage_without_prior_lookup"
    ]
    new_or_unseen_top_tokens = Counter(
        str(row.get("entry_adm_bucket_token_recomputed") or row.get("entry_adm_bucket_token") or "-")
        for row in new_or_unseen_tokens
    ).most_common(20)
    new_or_unseen_top_stages = Counter(
        str(row.get("stage") or "-") for row in new_or_unseen_tokens
    ).most_common(10)
    prior_missing_top_tokens = Counter(
        str(row.get("entry_adm_bucket_token_recomputed") or row.get("entry_adm_bucket_token") or "-")
        for row in prior_bucket_sample_missing_rows
    ).most_common(20)
    prior_missing_top_stages = Counter(
        str(row.get("stage") or "-") for row in prior_bucket_sample_missing_rows
    ).most_common(10)
    adm_lookup_closure = _adm_lookup_closure_summary(rows)
    raw_token_preserved_count = sum(1 for row in rows if row.get("raw_token_preserved"))
    adm_token_backfill_applied_count = sum(1 for row in rows if row.get("adm_token_backfill_applied"))
    runtime_effect_counts = Counter(str(row.get("entry_adm_runtime_effect") or "-") for row in rows)
    forced_action_counts = Counter(str(row.get("entry_adm_forced_action") or "-") for row in rows)
    unknown_summary = _unknown_bucket_summary(rows)
    warnings = []
    if joined_sample < SAMPLE_FLOOR:
        warnings.append("joined_sample_below_sample_floor")
    action_summary = _action_summary(rows)
    action_summary_actions = {str(item.get("action") or "") for item in action_summary if isinstance(item, dict)}
    missing_action_summary_rows = [action for action in ACTION_ORDER if action not in action_summary_actions]
    if missing_action_summary_rows:
        warnings.append("missing_action_bucket_summary_row")
    if any(row.get("risk_context_bucket") == "source_quality_blocker" for row in rows):
        warnings.append("source_quality_gap")
    if _safe_int(unknown_summary.get("affected_rows"), 0) > 0 and unknown_summary.get("source_quality_gate") == "source_quality_blocker":
        warnings.append("unknown_bucket_source_quality_gap")
    if prior_bucket_sample_missing_rows:
        warnings.append("prior_bucket_present_but_runtime_sample_missing")
    if rows and prompt_applied == 0:
        warnings.append("prompt_context_not_loaded")
    status = "pass" if not warnings else "warning"
    report = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "report_type": "scalp_entry_action_decision_matrix",
        "status": status,
        "runtime_effect": False,
        "decision_authority": "entry_advisory_prompt_context_only",
        "application_mode": "operator_override_advisory_prompt",
        "metric_role": "action_decision_matrix",
        "window_policy": "same_day_intraday_events_plus_postclose_sim_post_sell_join",
        "sample_floor": SAMPLE_FLOOR,
        "primary_decision_metric": "source_quality_adjusted_ev_pct",
        "source_quality_gate": "entry pipeline event + post-sell sim evaluation join when available",
        "forbidden_uses": [
            "threshold mutation",
            "order guard mutation",
            "provider change",
            "bot restart",
            "broker order submit",
        ],
        "matrix_version": f"{MATRIX_VERSION_PREFIX}_{target_date}",
        "bucket_schema_version": ENTRY_ADM_BUCKET_SCHEMA_VERSION,
        "actions": list(ACTION_ORDER),
        "bucket_dimensions": list(ENTRY_ADM_BUCKET_DIMENSIONS),
        "summary": {
            "total_candidates": len(rows),
            "joined_sample": joined_sample,
            "sample_floor": SAMPLE_FLOOR,
            "prompt_applied_count": prompt_applied,
            "runtime_bias_applied_count": runtime_bias_applied,
            "raw_token_preserved_count": raw_token_preserved_count,
            "adm_token_backfill_applied_count": adm_token_backfill_applied_count,
            "raw_token_preserved": raw_token_preserved_count > 0,
            "adm_token_backfill_applied": adm_token_backfill_applied_count > 0,
            "runtime_effect_counts": dict(runtime_effect_counts),
            "forced_action_counts": dict(forced_action_counts),
            "action_counts": dict(action_counts),
            "raw_action_counts": dict(raw_action_counts),
            "action_normalized_count": sum(action_normalization_counts.values()),
            "action_normalization_counts": dict(action_normalization_counts),
            "missing_actions": missing_actions,
            "zero_sample_actions": zero_sample_actions,
            "missing_action_summary_rows": missing_action_summary_rows,
            "adm_bucket_lookup_status_counts": dict(adm_bucket_lookup_status_counts),
            "new_or_unseen_token_count": len(new_or_unseen_tokens),
            "advisory_only_stage_without_prior_lookup_count": len(advisory_only_lookup_rows),
            "prior_bucket_sample_missing_count": len(prior_bucket_sample_missing_rows),
            "new_or_unseen_top_tokens": [[token, count] for token, count in new_or_unseen_top_tokens],
            "new_or_unseen_top_stages": [[stage, count] for stage, count in new_or_unseen_top_stages],
            "adm_bucket_lookup_closure": adm_lookup_closure,
            "adm_bucket_lookup_closure_status": adm_lookup_closure.get("closure_status"),
            "adm_bucket_lookup_followup_required": bool(adm_lookup_closure.get("followup_required")),
            "prior_missing_top_tokens": [[token, count] for token, count in prior_missing_top_tokens],
            "prior_missing_top_stages": [[stage, count] for stage, count in prior_missing_top_stages],
            "unknown_bucket_summary": unknown_summary,
            "status": status,
            "warnings": warnings,
            "post_sell_evaluation": eval_summary,
        },
        "action_summary": action_summary,
        "bucket_summary": _bucket_summary(rows),
        "rows": rows,
        "examples": rows[:50],
        "sources": {
            "events": [str(path) for path in _event_paths(target_date)],
            "sim_post_sell_evaluations": eval_summary.get("artifact"),
        },
        "warnings": warnings,
    }
    ADM_REPORT_DIR.mkdir(parents=True, exist_ok=True)
    json_path, md_path = report_paths(target_date)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_scalp_entry_action_decision_matrix_markdown(report), encoding="utf-8")
    return report


def render_scalp_entry_action_decision_matrix_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    unknown_summary = (
        summary.get("unknown_bucket_summary")
        if isinstance(summary.get("unknown_bucket_summary"), dict)
        else {}
    )
    lines = [
        f"# Scalp Entry Action Decision Matrix - {report.get('date')}",
        "",
        "## Contract",
        f"- status: `{report.get('status')}`",
        f"- runtime_effect: `{report.get('runtime_effect')}`",
        f"- decision_authority: `{report.get('decision_authority')}`",
        f"- application_mode: `{report.get('application_mode')}`",
        f"- primary_decision_metric: `{report.get('primary_decision_metric')}`",
        "",
        "## Summary",
        f"- total_candidates: `{summary.get('total_candidates')}`",
        f"- joined_sample/sample_floor: `{summary.get('joined_sample')}` / `{summary.get('sample_floor')}`",
        f"- prompt_applied_count: `{summary.get('prompt_applied_count')}`",
        f"- runtime_bias_applied_count: `{summary.get('runtime_bias_applied_count')}`",
        f"- runtime_effect_counts: `{summary.get('runtime_effect_counts') or {}}`",
        f"- forced_action_counts: `{summary.get('forced_action_counts') or {}}`",
        f"- action_counts: `{summary.get('action_counts')}`",
        f"- missing_actions: `{summary.get('missing_actions')}`",
        f"- zero_sample_actions: `{summary.get('zero_sample_actions')}`",
        f"- unknown_bucket_affected_rows: `{unknown_summary.get('affected_rows', 0)}`",
        f"- unknown_dimension_occurrence_count: `{unknown_summary.get('unknown_dimension_occurrence_count', 0)}`",
        f"- unknown_bucket_not_available_rows: `{unknown_summary.get('not_available_affected_rows', 0)}`",
        f"- not_available_dimension_occurrence_count: `{unknown_summary.get('not_available_dimension_occurrence_count', 0)}`",
        f"- unknown_bucket_dimension_counts: `{unknown_summary.get('dimension_counts') or {}}`",
        f"- unknown_bucket_not_available_dimension_counts: `{unknown_summary.get('not_available_dimension_counts') or {}}`",
        f"- adm_source_bucket_used_count: `{unknown_summary.get('adm_source_bucket_used_count', 0)}`",
        f"- recomputed_unknown_count: `{unknown_summary.get('recomputed_unknown_count', 0)}`",
        "",
        "## Action Summary",
        "| action | sample | joined | sq_adjusted_ev_pct | equal_weight_avg_profit_pct | missed_winner | avoided_loser |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for item in report.get("action_summary") or []:
        if not isinstance(item, dict):
            continue
        lines.append(
            f"| `{item.get('action')}` | {item.get('sample_count')} | {item.get('joined_sample')} | {item.get('source_quality_adjusted_ev_pct')} | {item.get('equal_weight_avg_profit_pct')} | {item.get('missed_winner_count')} | {item.get('avoided_loser_count')} |"
        )
    bucket_summary = report.get("bucket_summary") if isinstance(report.get("bucket_summary"), list) else []
    lines.extend(["", "## Top Buckets"])
    for item in bucket_summary[:10]:
        if isinstance(item, dict):
            lines.append(
                f"- `{item.get('bucket_token')}` sample=`{item.get('sample_count')}` joined=`{item.get('joined_sample')}` action=`{item.get('dominant_action')}` sq_ev=`{item.get('source_quality_adjusted_ev_pct')}`"
            )
    warnings = report.get("warnings") if isinstance(report.get("warnings"), list) else []
    if warnings:
        lines.extend(["", "## Warnings"])
        lines.extend(f"- `{warning}`" for warning in warnings)
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build scalp entry action decision matrix report.")
    parser.add_argument("--date", dest="target_date", default=date.today().isoformat())
    args = parser.parse_args(argv)
    report = build_scalp_entry_action_decision_matrix_report(args.target_date)
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
