from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from src.engine.lifecycle_decision_matrix_runtime import (
    apply_lifecycle_decision_to_payload,
    resolve_lifecycle_decision,
)
from src.utils.constants import DATA_DIR, TRADING_RULES


ADM_DIR = DATA_DIR / "report" / "scalp_entry_action_decision_matrix"
ADM_FILE_RE = re.compile(r"scalp_entry_action_decision_matrix_(\d{4}-\d{2}-\d{2})\.json$")


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _time_bucket(value: datetime | None) -> str:
    if value is None:
        return "time_unknown"
    minute = value.hour * 60 + value.minute
    if minute < 9 * 60 or minute >= 15 * 60 + 30:
        return "time_outside_regular"
    if minute < 9 * 60 + 30:
        return "time_0900_0930"
    if minute < 10 * 60 + 30:
        return "time_0930_1030"
    if minute < 14 * 60:
        return "time_1030_1400"
    return "time_1400_1530"


def _score_bucket(value: Any) -> str:
    score = _safe_float(value, -1.0)
    if score < 0:
        return "score_unknown"
    if score < 50:
        return "score_lt50"
    if score < 65:
        return "score50_64"
    if score < 75:
        return "score65_74"
    if score < 85:
        return "score75_84"
    return "score85_plus"


def _risk_context_bucket(ws_data: dict[str, Any] | None) -> str:
    ws = ws_data or {}
    pre_ai = ws.get("scalp_pre_ai_gate_context") if isinstance(ws.get("scalp_pre_ai_gate_context"), dict) else {}
    for key in ("source_quality_block_reason", "source_quality_status"):
        raw = str(pre_ai.get(key) or ws.get(key) or "").strip().lower()
        if raw and raw not in {"ok", "pass", "fresh", "-"}:
            return "source_quality_blocker"
    strength = _safe_float(ws.get("latest_strength") or ws.get("strength"), -1.0)
    buy_pressure = _safe_float(ws.get("buy_pressure_10t") or ws.get("buy_pressure"), -1.0)
    if strength < 0 and buy_pressure < 0:
        return "risk_unknown"
    if (0 <= strength < 80) or (0 <= buy_pressure < 40):
        return "weak_strength_momentum"
    if strength >= 140 or buy_pressure >= 70:
        return "strong_strength_momentum"
    return "neutral_strength_momentum"


def _stale_bucket(ws_data: dict[str, Any] | None) -> str:
    ws = ws_data or {}
    quote_age = _safe_float(ws.get("quote_age_ms") or ws.get("tick_latest_age_ms"), -1.0)
    if quote_age < 0:
        return "stale_unknown"
    if quote_age > 3000:
        return "stale_high"
    if quote_age > 1000:
        return "stale_watch"
    return "fresh"


def _liquidity_bucket(ws_data: dict[str, Any] | None) -> str:
    ws = ws_data or {}
    curr = _safe_float(ws.get("curr") or ws.get("curr_price"), 0.0)
    volume = _safe_float(ws.get("volume") or ws.get("today_vol") or ws.get("acc_volume"), 0.0)
    notional = curr * volume
    if notional <= 0:
        return "liquidity_unknown"
    if notional < 100_000_000:
        return "liquidity_low"
    if notional < 500_000_000:
        return "liquidity_mid"
    return "liquidity_high"


def _overbought_bucket(ws_data: dict[str, Any] | None) -> str:
    ws = ws_data or {}
    intraday_range = _safe_float(ws.get("intraday_range_pct"), -1.0)
    distance_high = _safe_float(ws.get("distance_from_day_high_pct"), -99.0)
    if intraday_range < 0:
        return "overbought_unknown"
    if intraday_range >= 18 and distance_high > -1.0:
        return "overbought_chase_risk"
    if intraday_range >= 10:
        return "overbought_watch"
    return "overbought_normal"


def _price_resolution_bucket(ws_data: dict[str, Any] | None) -> str:
    ws = ws_data or {}
    if ws.get("resolved_order_price") or ws.get("entry_price"):
        return "resolved_price"
    if ws.get("best_ask") or ws.get("best_bid"):
        return "quote_based"
    return "price_unknown"


def _session_cutoff_source_date(now: datetime) -> date:
    if now.hour >= 16:
        return now.date()
    return now.date() - timedelta(days=1)


def _latest_matrix_path_on_or_before(target_date: date) -> Path | None:
    best_date: date | None = None
    best_path: Path | None = None
    if not ADM_DIR.exists():
        return None
    for path in ADM_DIR.glob("scalp_entry_action_decision_matrix_*.json"):
        match = ADM_FILE_RE.match(path.name)
        if not match:
            continue
        try:
            current_date = date.fromisoformat(match.group(1))
        except ValueError:
            continue
        if current_date > target_date:
            continue
        if best_date is None or current_date > best_date:
            best_date = current_date
            best_path = path
    return best_path


def _read_payload(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _bucket_token(buckets: dict[str, str]) -> str:
    return "|".join(
        buckets.get(key, "-")
        for key in (
            "score_bucket",
            "risk_context_bucket",
            "stale_bucket",
            "price_resolution_bucket",
            "liquidity_bucket",
            "overbought_bucket",
            "time_bucket",
        )
    )


def _matched_bucket(payload: dict[str, Any], token: str) -> dict[str, Any]:
    buckets = payload.get("bucket_summary") if isinstance(payload.get("bucket_summary"), list) else []
    for item in buckets:
        if isinstance(item, dict) and str(item.get("bucket_token") or "") == token:
            return item
    return {}


def _prompt_context(payload: dict[str, Any], bucket_token: str, bucket: dict[str, Any]) -> str:
    return "\n".join(
        [
            "[Entry ADM Advisory Context]",
            "- source: scalp entry action decision matrix. operator override may force WAIT/DROP, while existing safety guards always win.",
            f"- matrix_version: {payload.get('matrix_version', '-')}",
            f"- source_date: {payload.get('date', '-')}",
            f"- bucket_token: {bucket_token}",
            f"- matched_bucket_sample: {bucket.get('sample_count', 0)} / joined: {bucket.get('joined_sample', 0)}",
            f"- dominant_action: {bucket.get('dominant_action', 'unmapped')}",
            f"- source_quality_adjusted_ev_pct: {bucket.get('source_quality_adjusted_ev_pct')}",
            "- rules: keep the existing BUY/WAIT/DROP schema; if quote/context is stale prefer WAIT_REQUOTE; do not bypass liquidity, overbought, stale quote, or latency pre-submit safety guards.",
        ]
    )


def _alignment_for_action(action_label: str, bucket: dict[str, Any]) -> str:
    action = str(action_label or "").upper()
    dominant = str(bucket.get("dominant_action") or "unmapped").upper()
    if not action:
        return "unknown_action"
    if dominant == "UNMAPPED":
        return "neutral_unmapped_bucket"
    if action == "BUY" and dominant in {"BUY_NOW", "BUY_DEFENSIVE"}:
        return "aligned_buy_bucket"
    if action in {"WAIT", "DROP", "NO_BUY"} and dominant not in {"BUY_NOW", "BUY_DEFENSIVE"}:
        return "aligned_skip_or_wait_bucket"
    return "against_adm_bucket_bias"


def _entry_adm_runtime_bias(
    *,
    action_label: str,
    context: dict[str, Any],
) -> dict[str, Any]:
    bucket = context.get("matched_bucket") if isinstance(context.get("matched_bucket"), dict) else {}
    fields = context.get("fields") if isinstance(context.get("fields"), dict) else {}
    original_action = str(action_label or "").upper()
    runtime_enabled = bool(getattr(TRADING_RULES, "SCALP_ENTRY_ADM_RUNTIME_BIAS_ENABLED", False))
    hypothesis_enabled = bool(getattr(TRADING_RULES, "SCALP_ENTRY_ADM_HYPOTHESIS_FALLBACK_ENABLED", False))
    hypothesis_force_enabled = bool(getattr(TRADING_RULES, "SCALP_ENTRY_ADM_HYPOTHESIS_FORCE_ENABLED", False))
    sample = _safe_int(bucket.get("sample_count"), 0)
    joined = _safe_int(bucket.get("joined_sample"), 0)
    sq_ev = _safe_float(bucket.get("source_quality_adjusted_ev_pct"), 0.0)
    dominant = str(bucket.get("dominant_action") or "").upper()
    min_sample = max(0, int(getattr(TRADING_RULES, "SCALP_ENTRY_ADM_MIN_BUCKET_SAMPLE", 1) or 0))
    min_joined = max(0, int(getattr(TRADING_RULES, "SCALP_ENTRY_ADM_MIN_JOINED_SAMPLE", 0) or 0))
    result = {
        "entry_adm_runtime_bias_enabled": runtime_enabled,
        "entry_adm_runtime_bias_applied": False,
        "entry_adm_runtime_effect": "none",
        "entry_adm_original_action": original_action or "-",
        "entry_adm_forced_action": "-",
        "entry_adm_runtime_reason": "no_runtime_bias",
        "entry_adm_bucket_sample_count": sample,
        "entry_adm_bucket_joined_sample": joined,
        "entry_adm_bucket_source_quality_adjusted_ev_pct": sq_ev,
        "entry_adm_hypothesis_fallback_enabled": hypothesis_enabled,
        "entry_adm_hypothesis_force_enabled": hypothesis_force_enabled,
    }
    if not runtime_enabled:
        result["entry_adm_runtime_reason"] = "runtime_bias_disabled"
        return result
    if not original_action:
        result["entry_adm_runtime_reason"] = "missing_ai_action"
        return result
    if not bool(context.get("applied")):
        result["entry_adm_runtime_reason"] = f"context_{context.get('status') or 'not_applied'}"
        return result
    if original_action not in {"BUY", "BUY_NOW"}:
        result["entry_adm_runtime_reason"] = "non_buy_action_passthrough"
        return result

    enough_sample = bool(bucket) and sample >= min_sample and joined >= min_joined
    forced_action = ""
    effect = "none"
    reason = ""
    if enough_sample:
        if dominant in {"WAIT_REQUOTE", "SKIP_STALE"}:
            forced_action = "WAIT"
            effect = "force_wait"
            reason = f"bucket_dominant_{dominant.lower()}"
        elif dominant in {"NO_BUY_AI", "SKIP_SOURCE_QUALITY", "SKIP_PRE_SUBMIT_SAFETY"}:
            forced_action = "DROP"
            effect = "force_drop"
            reason = f"bucket_dominant_{dominant.lower()}"
        elif (
            bool(getattr(TRADING_RULES, "SCALP_ENTRY_ADM_NEGATIVE_EV_BLOCK_ENABLED", True))
            and dominant in {"BUY_NOW", "BUY_DEFENSIVE"}
            and sq_ev < float(getattr(TRADING_RULES, "SCALP_ENTRY_ADM_NEGATIVE_EV_FORCE_WAIT_THRESHOLD_PCT", 0.0) or 0.0)
        ):
            forced_action = "WAIT"
            effect = "force_wait"
            reason = "bucket_negative_source_quality_adjusted_ev"
        elif dominant == "BUY_DEFENSIVE":
            forced_action = "BUY"
            effect = "buy_defensive_bias"
            reason = "bucket_dominant_buy_defensive"

    if not forced_action and hypothesis_enabled:
        risk_bucket = str(fields.get("entry_adm_risk_context_bucket") or "").lower()
        stale_bucket = str(fields.get("entry_adm_stale_bucket") or "").lower()
        liquidity_bucket = str(fields.get("entry_adm_liquidity_bucket") or "").lower()
        overbought_bucket = str(fields.get("entry_adm_overbought_bucket") or "").lower()
        hypothesis_action = ""
        hypothesis_effect = "none"
        hypothesis_reason = ""
        if risk_bucket == "source_quality_blocker":
            hypothesis_action = "DROP"
            hypothesis_effect = "force_drop"
            hypothesis_reason = "hypothesis_source_quality_blocker"
        elif stale_bucket == "stale_high":
            hypothesis_action = "WAIT"
            hypothesis_effect = "force_wait"
            hypothesis_reason = "hypothesis_stale_quote_wait_requote"
        elif liquidity_bucket == "liquidity_low":
            hypothesis_action = "WAIT"
            hypothesis_effect = "force_wait"
            hypothesis_reason = "hypothesis_low_liquidity_wait"
        elif risk_bucket == "weak_strength_momentum" and overbought_bucket in {
            "overbought_watch",
            "overbought_chase_risk",
        }:
            hypothesis_action = "WAIT"
            hypothesis_effect = "force_wait"
            hypothesis_reason = "hypothesis_weak_momentum_chase_risk"
        if hypothesis_action:
            if hypothesis_force_enabled:
                forced_action = hypothesis_action
                effect = hypothesis_effect
                reason = hypothesis_reason
            else:
                result["entry_adm_runtime_reason"] = f"{hypothesis_reason}_provenance_only"
                return result

    if not forced_action:
        result["entry_adm_runtime_reason"] = "bucket_sample_below_floor" if bucket and not enough_sample else "no_matching_runtime_bias"
        return result
    result.update(
        {
            "entry_adm_runtime_bias_applied": effect in {"force_wait", "force_drop", "buy_defensive_bias"},
            "entry_adm_runtime_effect": effect,
            "entry_adm_forced_action": forced_action,
            "entry_adm_runtime_reason": reason,
        }
    )
    return result


def build_scalp_entry_adm_runtime_context(
    *,
    prompt_profile: str,
    ws_data: dict[str, Any] | None,
    advisory_enabled: bool,
    now: datetime | None = None,
    ai_score: Any = None,
) -> dict[str, Any]:
    profile = str(prompt_profile or "shared").strip().lower()
    current_dt = now or datetime.now()
    buckets = {
        "score_bucket": _score_bucket(ai_score if ai_score is not None else (ws_data or {}).get("ai_score")),
        "risk_context_bucket": _risk_context_bucket(ws_data),
        "stale_bucket": _stale_bucket(ws_data),
        "price_resolution_bucket": _price_resolution_bucket(ws_data),
        "liquidity_bucket": _liquidity_bucket(ws_data),
        "overbought_bucket": _overbought_bucket(ws_data),
        "time_bucket": _time_bucket(current_dt),
    }
    token = _bucket_token(buckets)
    if profile not in {"watching", "entry", "scalping_entry"}:
        return {
            "applied": False,
            "status": "excluded_non_entry_prompt",
            "cache_token": f"entry_adm:excluded:non_entry:{token}",
            "prompt_context": "",
            "fields": _fields(False, "excluded_non_entry_prompt", "", "", "", token, buckets, "-"),
            "matched_bucket": {},
        }

    matrix_path = _latest_matrix_path_on_or_before(_session_cutoff_source_date(current_dt))
    payload = _read_payload(matrix_path)
    if not payload:
        status = "matrix_missing_or_invalid"
        return {
            "applied": False,
            "status": status,
            "cache_token": f"entry_adm:missing:{token}",
            "prompt_context": "",
            "fields": _fields(bool(advisory_enabled), status, "", "", str(matrix_path) if matrix_path else "", token, buckets, "-"),
            "matched_bucket": {},
        }

    bucket = _matched_bucket(payload, token)
    status = "advisory_prompt_applied" if advisory_enabled else "loaded_feature_disabled"
    matrix_version = str(payload.get("matrix_version") or "-")
    source_date = str(payload.get("date") or "-")
    cache_token = f"entry_adm:{matrix_version}:{token}"
    fields = _fields(
        bool(advisory_enabled),
        status,
        matrix_version,
        source_date,
        str(matrix_path),
        token,
        buckets,
        str(bucket.get("dominant_action") or "-"),
    )
    return {
        "applied": bool(advisory_enabled),
        "status": status,
        "cache_token": cache_token,
        "prompt_context": _prompt_context(payload, token, bucket) if advisory_enabled else "",
        "fields": fields,
        "matched_bucket": bucket,
    }


def _fields(
    feature_enabled: bool,
    status: str,
    version: str,
    source_date: str,
    loaded_from: str,
    token: str,
    buckets: dict[str, str],
    dominant_action: str,
) -> dict[str, Any]:
    return {
        "entry_adm_feature_enabled": bool(feature_enabled),
        "entry_adm_prompt_applied": bool(feature_enabled and status == "advisory_prompt_applied"),
        "entry_adm_status": status,
        "entry_adm_version": version or "-",
        "entry_adm_source_date": source_date or "-",
        "entry_adm_application_mode": "operator_override_advisory_prompt",
        "entry_adm_loaded_from": loaded_from or "-",
        "entry_adm_cache_token": f"entry_adm:{version or status}:{token}",
        "entry_adm_bucket_token": token,
        "entry_adm_score_bucket": buckets.get("score_bucket", "-"),
        "entry_adm_risk_context_bucket": buckets.get("risk_context_bucket", "-"),
        "entry_adm_stale_bucket": buckets.get("stale_bucket", "-"),
        "entry_adm_price_resolution_bucket": buckets.get("price_resolution_bucket", "-"),
        "entry_adm_liquidity_bucket": buckets.get("liquidity_bucket", "-"),
        "entry_adm_overbought_bucket": buckets.get("overbought_bucket", "-"),
        "entry_adm_time_bucket": buckets.get("time_bucket", "-"),
        "entry_adm_recommended_action": dominant_action or "-",
        "entry_adm_runtime_bias_enabled": bool(getattr(TRADING_RULES, "SCALP_ENTRY_ADM_RUNTIME_BIAS_ENABLED", False)),
        "entry_adm_runtime_bias_applied": False,
        "entry_adm_runtime_effect": "none",
        "entry_adm_original_action": "-",
        "entry_adm_forced_action": "-",
        "entry_adm_runtime_reason": "not_evaluated",
    }


def merge_scalp_entry_adm_result_fields(
    result: dict[str, Any] | None,
    runtime_context: dict[str, Any] | None,
) -> dict[str, Any]:
    payload = dict(result or {})
    context = runtime_context or {}
    fields = dict(context.get("fields") or {})
    action = payload.get("action") or payload.get("action_v2") or ""
    runtime_bias = _entry_adm_runtime_bias(action_label=str(action or ""), context=context)
    fields.update(runtime_bias)
    forced_action = str(runtime_bias.get("entry_adm_forced_action") or "").upper()
    if runtime_bias.get("entry_adm_runtime_effect") in {"force_wait", "force_drop"} and forced_action in {"WAIT", "DROP"}:
        if "action" in payload or not payload.get("action_v2"):
            payload["action"] = forced_action
        if "action_v2" in payload:
            payload["action_v2"] = forced_action
    fields["entry_adm_decision_alignment"] = _alignment_for_action(
        str(payload.get("action") or payload.get("action_v2") or action or ""),
        context.get("matched_bucket") if isinstance(context.get("matched_bucket"), dict) else {},
    )
    payload.update(fields)
    lifecycle_context = {
        **fields,
        "source_quality_block_reason": fields.get("entry_adm_status"),
        "stale_quote_submit_block": fields.get("entry_adm_stale_bucket") == "stale_high",
    }
    lifecycle_decision = resolve_lifecycle_decision(
        stage="entry",
        original_action=str(payload.get("action") or payload.get("action_v2") or action or ""),
        context=lifecycle_context,
    )
    payload = apply_lifecycle_decision_to_payload(payload, lifecycle_decision)
    return payload
