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


MATRIX_DIR = DATA_DIR / "report" / "holding_exit_decision_matrix"
MATRIX_FILE_RE = re.compile(r"holding_exit_decision_matrix_(\d{4}-\d{2}-\d{2})\.json$")


def _price_bucket(value: Any) -> str:
    try:
        price = float(value)
    except Exception:
        price = 0.0
    if price <= 0:
        return "price_unknown"
    if price < 10_000:
        return "price_lt_10k"
    if price < 30_000:
        return "price_10k_30k"
    if price < 70_000:
        return "price_30k_70k"
    return "price_gte_70k"


def _volume_bucket(value: Any) -> str:
    try:
        volume = float(value)
    except Exception:
        volume = 0.0
    if volume <= 0:
        return "volume_unknown"
    if volume < 500_000:
        return "volume_lt_500k"
    if volume < 2_000_000:
        return "volume_500k_2m"
    if volume < 10_000_000:
        return "volume_2m_10m"
    return "volume_gte_10m"


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


def _safe_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"1", "true", "yes", "y", "on"}:
            return True
        if text in {"0", "false", "no", "n", "off", ""}:
            return False
        return default
    return bool(value)


_UNUSABLE_HOLDING_SCORE_SOURCES = {
    "",
    "-",
    "none",
    "null",
    "missing",
    "unknown",
    "not_called",
    "holding_ai_not_called",
    "fallback",
    "fallback_score_50",
    "engine_disabled",
    "lock_contention",
    "timeout",
    "exception",
    "error",
    "insufficient",
    "source_quality_insufficient",
    "watching_cooldown",
}
_UNUSABLE_HOLDING_SCORE_SOURCE_TOKENS = (
    "fallback_score_50",
    "engine_disabled",
    "lock_contention",
    "timeout",
    "exception",
    "error",
    "insufficient",
    "source_quality_insufficient",
)


def _holding_matrix_ai_score_context(position_ctx: dict[str, Any] | None) -> dict[str, Any]:
    ctx = position_ctx if isinstance(position_ctx, dict) else {}
    score = _safe_float(ctx.get("current_ai_score"), 50.0)
    source = str(
        ctx.get("holding_score_source")
        or ctx.get("holding_ai_score_source")
        or ctx.get("current_ai_score_source")
        or ctx.get("ai_score_source")
        or "-"
    ).strip()
    data_quality = str(ctx.get("holding_score_data_quality") or "insufficient").strip().lower()
    if data_quality not in {"fresh", "partial", "stale", "insufficient"}:
        data_quality = "insufficient"
    has_explicit_quality = "holding_score_data_quality" in ctx or "holding_score_effective_usable" in ctx
    microstructure_confirmed = (
        _safe_bool(ctx.get("holding_score_role_microstructure_confirmed"), False)
        or _safe_bool(ctx.get("microstructure_confirmed"), False)
        or _safe_bool(ctx.get("tick_aggressor_pressure_usable"), False)
        or _safe_int(ctx.get("tick_aggressor_trusted_count"), 0) > 0
    )
    usable = True
    excluded_reason = "-"
    source_l = str(source).lower()
    if source_l in _UNUSABLE_HOLDING_SCORE_SOURCES or any(
        token in source_l for token in _UNUSABLE_HOLDING_SCORE_SOURCE_TOKENS
    ):
        usable = False
        excluded_reason = f"holding_score_source_{source or 'missing'}"
    if data_quality in {"stale", "insufficient"}:
        usable = False
        excluded_reason = f"holding_score_data_quality_{data_quality}"
    elif data_quality == "partial" and not microstructure_confirmed:
        usable = False
        excluded_reason = "holding_score_partial_requires_microstructure"
    if "holding_score_effective_usable" in ctx and not _safe_bool(ctx.get("holding_score_effective_usable"), False):
        usable = False
        excluded_reason = str(ctx.get("holding_score_excluded_reason") or "holding_score_unusable")
    if source_l == "holding_ai_not_called":
        age_sec = _safe_float(ctx.get("holding_score_age_sec"), -1.0)
        ttl = max(1.0, _safe_float(getattr(TRADING_RULES, "AI_HOLDING_MAX_COOLDOWN", 180), 180.0))
        if not has_explicit_quality or age_sec < 0 or age_sec > ttl:
            usable = False
            excluded_reason = "holding_ai_not_called_expired_or_unproven"
    return {
        "current_ai_score": score,
        "ai_score_usable": usable,
        "ai_score_source": source or "-",
        "ai_score_data_quality": data_quality or "-",
        "ai_score_excluded_reason": excluded_reason,
        "ai_score_microstructure_confirmed": bool(microstructure_confirmed),
    }


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


def _session_cutoff_source_date(now: datetime) -> date:
    if now.hour >= 16:
        return now.date()
    return now.date() - timedelta(days=1)


def _latest_matrix_path_on_or_before(target_date: date) -> Path | None:
    best_date: date | None = None
    best_path: Path | None = None
    if not MATRIX_DIR.exists():
        return None
    for path in MATRIX_DIR.glob("holding_exit_decision_matrix_*.json"):
        match = MATRIX_FILE_RE.match(path.name)
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


def _read_matrix_payload(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _resolve_intraday_volume(ws_data: dict[str, Any] | None, recent_candles: list[dict[str, Any]] | None) -> Any:
    ws = ws_data or {}
    for key in ("volume", "today_vol", "acc_volume", "trade_volume"):
        value = ws.get(key)
        if value not in (None, "", 0, 0.0):
            return value
    candles = recent_candles or []
    if candles:
        latest = candles[-1] if isinstance(candles[-1], dict) else {}
        for key in ("누적거래량", "누적 거래량", "acc_volume", "volume", "거래량"):
            value = latest.get(key)
            if value not in (None, "", 0, 0.0):
                return value
    return 0


def _matched_entries(payload: dict[str, Any], buckets: dict[str, str]) -> list[dict[str, Any]]:
    by_axis = {
        str(entry.get("axis") or ""): entry
        for entry in (payload.get("entries") or [])
        if isinstance(entry, dict)
    }
    matched: list[dict[str, Any]] = []
    for axis_name in ("price_bucket", "volume_bucket", "time_bucket"):
        bucket = buckets.get(axis_name, f"{axis_name}_unknown")
        entry = by_axis.get(axis_name)
        if entry and str(entry.get("bucket") or "") == bucket:
            matched.append(entry)
            continue
        matched.append(
            {
                "axis": axis_name,
                "bucket": bucket,
                "recommended_bias": "no_clear_edge",
                "policy_hint": "runtime_bucket_unmapped",
                "prompt_hint": f"{axis_name}={bucket} runtime bucket은 matrix entry가 없어 기존 보유/청산 원칙을 우선한다.",
            }
        )
    return matched


def _prompt_context(payload: dict[str, Any], matched_entries: list[dict[str, Any]]) -> str:
    if not payload:
        return ""
    hard_veto = ", ".join(str(item) for item in (payload.get("hard_veto") or [])[:4]) or "-"
    lines = [
        "[ADM Advisory Context]",
        "- source: holding/exit decision matrix. operator override may force HOLD/EXIT or scale-in bias; hard veto and existing runtime safety always win.",
        f"- matrix_version: {payload.get('matrix_version', '-')}",
        f"- source_date: {payload.get('source_date', '-')}",
        f"- hard_veto_first: {hard_veto}",
        "- matched_buckets:",
    ]
    for entry in matched_entries:
        lines.append(
            "  - "
            f"{entry.get('axis')}={entry.get('bucket')} / bias={entry.get('recommended_bias', '-')} / "
            f"policy={entry.get('policy_hint', '-')}"
        )
    lines.append("- prompt_hints:")
    for entry in matched_entries:
        lines.append(f"  - {entry.get('prompt_hint', '-')}")
    lines.append("- rules: keep the existing HOLD/TRIM/EXIT schema. if bias is no_clear_edge, prefer the baseline rule.")
    return "\n".join(lines)


def _alignment_for_action(action_label: str, matched_entries: list[dict[str, Any]]) -> str:
    action = str(action_label or "").upper()
    biases = {str(entry.get("recommended_bias") or "no_clear_edge") for entry in matched_entries}
    if not action:
        return "action_not_available"
    if biases == {"no_clear_edge"}:
        return "neutral_no_clear_edge"
    if "prefer_exit" in biases and action in {"EXIT", "TRIM", "DROP", "SELL"}:
        return "aligned_exit_bias"
    if biases & {"prefer_avg_down_wait", "prefer_pyramid_wait"} and action in {"HOLD", "WAIT"}:
        return "aligned_wait_bias"
    if action in {"HOLD", "WAIT"}:
        return "hold_against_matrix_bias"
    if action in {"EXIT", "TRIM", "DROP", "SELL"}:
        return "exit_against_matrix_bias"
    return "alignment_not_available"


def _truthy_flag(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return value != 0
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on", "blocked", "block"}


def has_holding_exit_matrix_safety_veto(context: dict[str, Any] | None) -> bool:
    """Return True when ADM/LDM runtime bias must never mutate the action."""
    ctx = context or {}
    for key in (
        "hard_safety_veto",
        "safety_veto",
        "broker_guard_block",
        "broker_submit_blocked",
        "broker_order_forbidden",
        "stale_quote_submit_block",
        "quote_stale_at_submit",
        "price_context_stale_at_submit",
        "price_freshness_block",
        "protect_stop",
        "hard_stop",
        "emergency_stop",
        "account_guard_block",
        "order_guard_block",
        "cooldown_guard_block",
        "qty_guard_block",
        "receipt_missing",
        "provenance_missing",
    ):
        if _truthy_flag(ctx.get(key)):
            return True
    reason_blob = " ".join(
        str(ctx.get(key) or "").lower()
        for key in (
            "exit_rule",
            "sell_reason_type",
            "blocked_reason",
            "source_quality_block_reason",
            "entry_submit_revalidation_warning",
            "entry_submit_revalidation_block",
            "order_receipt_status",
            "provenance_status",
        )
    )
    return any(
        token in reason_blob
        for token in (
            "hard_stop",
            "protect_stop",
            "emergency",
            "market_closed",
            "invalid",
            "broker",
            "account_guard",
            "order_guard",
            "cooldown",
            "qty_guard",
            "stale_context",
            "stale_quote",
            "price_freshness",
            "receipt_missing",
            "provenance_missing",
        )
    )


def _exit_to_hold_candidate_actions() -> set[str]:
    actions = {"EXIT", "DROP", "SELL"}
    if bool(getattr(TRADING_RULES, "HOLDING_EXIT_MATRIX_TRIM_TO_HOLD_ENABLED", False)):
        actions.add("TRIM")
    return actions


def _runtime_bias_from_entries(
    *,
    action_label: str,
    matched_entries: list[dict[str, Any]],
    position_ctx: dict[str, Any] | None,
) -> dict[str, Any]:
    runtime_enabled = bool(getattr(TRADING_RULES, "HOLDING_EXIT_MATRIX_RUNTIME_BIAS_ENABLED", False))
    action = str(action_label or "").upper()
    biases = {str(entry.get("recommended_bias") or "no_clear_edge") for entry in matched_entries}
    profit_rate = _safe_float((position_ctx or {}).get("profit_rate"), 0.0)
    peak_profit = _safe_float((position_ctx or {}).get("peak_profit"), profit_rate)
    ai_context = _holding_matrix_ai_score_context(position_ctx)
    current_ai_score = ai_context["current_ai_score"]
    safety_veto = has_holding_exit_matrix_safety_veto(position_ctx)
    result = {
        "holding_exit_matrix_runtime_bias_enabled": runtime_enabled,
        "holding_exit_matrix_runtime_bias_applied": False,
        "holding_exit_matrix_runtime_effect": "none",
        "holding_exit_matrix_original_action": action or "-",
        "holding_exit_matrix_forced_action": "-",
        "holding_exit_matrix_runtime_reason": "no_runtime_bias",
        "holding_exit_matrix_scale_in_bias": "-",
        "holding_exit_matrix_hypothesis_profit_rate": profit_rate,
        "holding_exit_matrix_hypothesis_peak_profit": peak_profit,
        "holding_exit_matrix_hypothesis_ai_score": current_ai_score,
        "holding_exit_matrix_ai_score_usable": ai_context["ai_score_usable"],
        "holding_exit_matrix_ai_score_source": ai_context["ai_score_source"],
        "holding_exit_matrix_ai_score_data_quality": ai_context["ai_score_data_quality"],
        "holding_exit_matrix_ai_score_excluded_reason": ai_context["ai_score_excluded_reason"],
        "holding_exit_matrix_ai_score_microstructure_confirmed": ai_context["ai_score_microstructure_confirmed"],
    }
    if not runtime_enabled:
        result["holding_exit_matrix_runtime_reason"] = "runtime_bias_disabled"
        return result
    if not action:
        result["holding_exit_matrix_runtime_reason"] = "missing_ai_action"
        return result
    if safety_veto:
        result["holding_exit_matrix_runtime_reason"] = "safety_veto_passthrough"
        return result

    forced_action = ""
    effect = "none"
    reason = ""
    if (
        "prefer_exit" in biases
        and action in {"HOLD", "WAIT", "TRIM"}
        and bool(getattr(TRADING_RULES, "HOLDING_EXIT_MATRIX_HOLD_TO_EXIT_ENABLED", True))
    ):
        forced_action = "EXIT"
        effect = "force_exit"
        reason = "matrix_prefer_exit"
    elif (
        biases & {"prefer_avg_down_wait", "prefer_pyramid_wait"}
        and action in _exit_to_hold_candidate_actions()
        and bool(getattr(TRADING_RULES, "HOLDING_EXIT_MATRIX_EXIT_TO_HOLD_ENABLED", True))
        and ai_context["ai_score_usable"]
    ):
        forced_action = "HOLD"
        effect = "force_hold"
        reason = "matrix_scale_in_or_missed_upside_wait"

    if "prefer_avg_down_wait" in biases:
        result["holding_exit_matrix_scale_in_bias"] = "AVG_DOWN"
    elif "prefer_pyramid_wait" in biases:
        result["holding_exit_matrix_scale_in_bias"] = "PYRAMID"

    if not forced_action and position_ctx:
        drawdown_from_peak = float(peak_profit or 0.0) - float(profit_rate or 0.0)
        if (
            action in _exit_to_hold_candidate_actions()
            and bool(getattr(TRADING_RULES, "HOLDING_EXIT_MATRIX_EXIT_TO_HOLD_ENABLED", True))
            and ai_context["ai_score_usable"]
            and current_ai_score >= float(getattr(TRADING_RULES, "HOLDING_EXIT_MATRIX_AVG_DOWN_MIN_AI_SCORE", 65) or 65)
            and profit_rate >= float(getattr(TRADING_RULES, "HOLDING_EXIT_MATRIX_AVG_DOWN_MIN_PROFIT_PCT", -1.2) or -1.2)
            and profit_rate <= float(getattr(TRADING_RULES, "HOLDING_EXIT_MATRIX_AVG_DOWN_MAX_PROFIT_PCT", -0.1) or -0.1)
        ):
            forced_action = "HOLD"
            effect = "force_hold"
            reason = "hypothesis_avg_down_wait_window"
            result["holding_exit_matrix_scale_in_bias"] = "AVG_DOWN"
        elif (
            action in _exit_to_hold_candidate_actions()
            and bool(getattr(TRADING_RULES, "HOLDING_EXIT_MATRIX_EXIT_TO_HOLD_ENABLED", True))
            and ai_context["ai_score_usable"]
            and current_ai_score >= float(getattr(TRADING_RULES, "HOLDING_EXIT_MATRIX_PYRAMID_MIN_AI_SCORE", 75) or 75)
            and profit_rate >= float(getattr(TRADING_RULES, "HOLDING_EXIT_MATRIX_PYRAMID_MIN_PROFIT_PCT", 0.8) or 0.8)
            and drawdown_from_peak <= float(
                getattr(TRADING_RULES, "HOLDING_EXIT_MATRIX_PYRAMID_MAX_DRAWDOWN_FROM_PEAK_PCT", 0.35) or 0.35
            )
        ):
            forced_action = "HOLD"
            effect = "force_hold"
            reason = "hypothesis_pyramid_wait_window"
            result["holding_exit_matrix_scale_in_bias"] = "PYRAMID"

    if not forced_action:
        result["holding_exit_matrix_runtime_reason"] = "no_matching_runtime_bias"
        return result
    result.update(
        {
            "holding_exit_matrix_runtime_bias_applied": True,
            "holding_exit_matrix_runtime_effect": effect,
            "holding_exit_matrix_forced_action": forced_action,
            "holding_exit_matrix_runtime_reason": reason,
        }
    )
    return result


def resolve_holding_exit_matrix_scale_in_bias(
    *,
    strategy: str,
    profit_rate: float,
    peak_profit: float,
    current_ai_score: float,
    held_sec: int,
    safety_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Runtime override hook for ADM-driven avg-down/pyramid proposals."""
    raw_strategy = str(strategy or "").upper()
    if raw_strategy not in {"SCALPING", "SCALP"}:
        return {"should_add": False, "reason": "holding_exit_matrix_scale_in_bias_scalping_only"}
    if has_holding_exit_matrix_safety_veto(safety_context):
        return {"should_add": False, "reason": "holding_exit_matrix_scale_in_safety_veto_passthrough"}
    ai_context = _holding_matrix_ai_score_context(
        {
            **(safety_context or {}),
            "current_ai_score": current_ai_score,
        }
    )
    scale_in_enabled = bool(getattr(TRADING_RULES, "HOLDING_EXIT_MATRIX_SCALE_IN_BIAS_ENABLED", False))
    lifecycle_decision = resolve_lifecycle_decision(
        stage="scale_in",
        original_action="NO_CHANGE",
        context={
            **(safety_context or {}),
            "profit_rate": profit_rate,
            "peak_profit": peak_profit,
            "current_ai_score": current_ai_score,
            "held_sec": held_sec,
        },
    )
    lifecycle_effect = str(lifecycle_decision.get("lifecycle_matrix_runtime_effect") or "")
    if not scale_in_enabled:
        return {
            "should_add": False,
            "reason": "holding_exit_matrix_scale_in_bias_disabled",
            **lifecycle_decision,
        }
    if lifecycle_effect in {"avg_down_bias", "pyramid_bias"}:
        if not ai_context["ai_score_usable"]:
            return {
                "should_add": False,
                "reason": "holding_exit_matrix_ai_score_unusable",
                "ai_score_usable": ai_context["ai_score_usable"],
                "ai_score_source": ai_context["ai_score_source"],
                "ai_score_data_quality": ai_context["ai_score_data_quality"],
                "ai_score_excluded_reason": ai_context["ai_score_excluded_reason"],
                "ai_score_microstructure_confirmed": ai_context["ai_score_microstructure_confirmed"],
                **lifecycle_decision,
            }
        add_type = "AVG_DOWN" if lifecycle_effect == "avg_down_bias" else "PYRAMID"
        return {
            "should_add": True,
            "add_type": add_type,
            "reason": f"lifecycle_decision_matrix_{add_type.lower()}",
            "profit_rate": profit_rate,
            "peak_profit": peak_profit,
            "current_ai_score": current_ai_score,
            "ai_score_usable": ai_context["ai_score_usable"],
            "ai_score_source": ai_context["ai_score_source"],
            "ai_score_data_quality": ai_context["ai_score_data_quality"],
            "ai_score_microstructure_confirmed": ai_context["ai_score_microstructure_confirmed"],
            "held_sec": held_sec,
            "holding_exit_matrix_scale_in_bias": add_type,
            **lifecycle_decision,
        }
    avg_min = float(getattr(TRADING_RULES, "HOLDING_EXIT_MATRIX_AVG_DOWN_MIN_PROFIT_PCT", -1.2) or -1.2)
    avg_max = float(getattr(TRADING_RULES, "HOLDING_EXIT_MATRIX_AVG_DOWN_MAX_PROFIT_PCT", -0.1) or -0.1)
    avg_ai = int(getattr(TRADING_RULES, "HOLDING_EXIT_MATRIX_AVG_DOWN_MIN_AI_SCORE", 65) or 65)
    avg_min_held = int(getattr(TRADING_RULES, "HOLDING_EXIT_MATRIX_AVG_DOWN_MIN_HELD_SEC", 10) or 10)
    avg_max_held = int(getattr(TRADING_RULES, "HOLDING_EXIT_MATRIX_AVG_DOWN_MAX_HELD_SEC", 240) or 240)
    if avg_min <= float(profit_rate or 0.0) <= avg_max and int(held_sec or 0) >= avg_min_held:
        if (
            int(held_sec or 0) <= avg_max_held
            and ai_context["ai_score_usable"]
            and float(current_ai_score or 0.0) >= avg_ai
        ):
            return {
                "should_add": True,
                "add_type": "AVG_DOWN",
                "reason": "holding_exit_matrix_avg_down_bias",
                "profit_rate": profit_rate,
                "peak_profit": peak_profit,
                "current_ai_score": current_ai_score,
                "ai_score_usable": ai_context["ai_score_usable"],
                "ai_score_source": ai_context["ai_score_source"],
                "ai_score_data_quality": ai_context["ai_score_data_quality"],
                "ai_score_microstructure_confirmed": ai_context["ai_score_microstructure_confirmed"],
                "held_sec": held_sec,
                "holding_exit_matrix_scale_in_bias": "AVG_DOWN",
            }
    pyr_min = float(getattr(TRADING_RULES, "HOLDING_EXIT_MATRIX_PYRAMID_MIN_PROFIT_PCT", 0.8) or 0.8)
    pyr_ai = int(getattr(TRADING_RULES, "HOLDING_EXIT_MATRIX_PYRAMID_MIN_AI_SCORE", 75) or 75)
    pyr_max_dd = float(getattr(TRADING_RULES, "HOLDING_EXIT_MATRIX_PYRAMID_MAX_DRAWDOWN_FROM_PEAK_PCT", 0.35) or 0.35)
    drawdown_from_peak = float(peak_profit or 0.0) - float(profit_rate or 0.0)
    if (
        float(profit_rate or 0.0) >= pyr_min
        and ai_context["ai_score_usable"]
        and float(current_ai_score or 0.0) >= pyr_ai
        and drawdown_from_peak <= pyr_max_dd
    ):
        return {
            "should_add": True,
            "add_type": "PYRAMID",
            "reason": "holding_exit_matrix_pyramid_bias",
            "profit_rate": profit_rate,
            "peak_profit": peak_profit,
            "current_ai_score": current_ai_score,
            "ai_score_usable": ai_context["ai_score_usable"],
            "ai_score_source": ai_context["ai_score_source"],
            "ai_score_data_quality": ai_context["ai_score_data_quality"],
            "ai_score_microstructure_confirmed": ai_context["ai_score_microstructure_confirmed"],
            "held_sec": held_sec,
            "holding_exit_matrix_scale_in_bias": "PYRAMID",
        }
    reason = (
        "holding_exit_matrix_ai_score_unusable"
        if not ai_context["ai_score_usable"]
        else "holding_exit_matrix_scale_in_no_match"
    )
    return {
        "should_add": False,
        "reason": reason,
        "ai_score_usable": ai_context["ai_score_usable"],
        "ai_score_source": ai_context["ai_score_source"],
        "ai_score_data_quality": ai_context["ai_score_data_quality"],
        "ai_score_excluded_reason": ai_context["ai_score_excluded_reason"],
        "ai_score_microstructure_confirmed": ai_context["ai_score_microstructure_confirmed"],
    }


def build_holding_exit_matrix_runtime_context(
    *,
    prompt_profile: str,
    ws_data: dict[str, Any] | None,
    recent_candles: list[dict[str, Any]] | None,
    advisory_enabled: bool,
    now: datetime | None = None,
) -> dict[str, Any]:
    profile = str(prompt_profile or "shared").strip().lower()
    current_dt = now or datetime.now()
    price_bucket = _price_bucket((ws_data or {}).get("curr") or (ws_data or {}).get("curr_price"))
    volume_bucket = _volume_bucket(_resolve_intraday_volume(ws_data, recent_candles))
    time_bucket = _time_bucket(current_dt)
    buckets = {
        "price_bucket": price_bucket,
        "volume_bucket": volume_bucket,
        "time_bucket": time_bucket,
    }
    if profile not in {"holding", "exit"}:
        return {
            "applied": False,
            "status": "excluded_non_holding_prompt",
            "cohort": "excluded",
            "cache_token": f"excluded:non_holding:{price_bucket}:{volume_bucket}:{time_bucket}",
            "prompt_context": "",
            "fields": {
                "holding_exit_matrix_feature_enabled": bool(advisory_enabled),
                "holding_exit_matrix_applied": False,
                "holding_exit_matrix_status": "excluded_non_holding_prompt",
                "holding_exit_matrix_cohort": "excluded",
                "holding_exit_matrix_version": "-",
                "holding_exit_matrix_source_date": "-",
                "holding_exit_matrix_valid_for_date": "-",
                "holding_exit_matrix_application_mode": "-",
                "holding_exit_matrix_loaded_from": "-",
                "holding_exit_matrix_cache_token": f"excluded:non_holding:{price_bucket}:{volume_bucket}:{time_bucket}",
                "holding_exit_matrix_price_bucket": price_bucket,
                "holding_exit_matrix_volume_bucket": volume_bucket,
                "holding_exit_matrix_time_bucket": time_bucket,
                "holding_exit_matrix_recommended_biases": "-",
                "holding_exit_matrix_policy_hints": "-",
                "holding_exit_matrix_runtime_bias_enabled": bool(
                    getattr(TRADING_RULES, "HOLDING_EXIT_MATRIX_RUNTIME_BIAS_ENABLED", False)
                ),
                "holding_exit_matrix_runtime_bias_applied": False,
                "holding_exit_matrix_runtime_effect": "none",
                "holding_exit_matrix_original_action": "-",
                "holding_exit_matrix_forced_action": "-",
                "holding_exit_matrix_runtime_reason": "not_evaluated",
                "holding_exit_matrix_scale_in_bias": "-",
            },
            "matched_entries": [],
        }

    matrix_path = _latest_matrix_path_on_or_before(_session_cutoff_source_date(current_dt))
    payload = _read_matrix_payload(matrix_path)
    if not payload:
        status = "matrix_missing_or_invalid"
        cohort = "excluded"
        cache_token = f"excluded:missing:{price_bucket}:{volume_bucket}:{time_bucket}"
        return {
            "applied": False,
            "status": status,
            "cohort": cohort,
            "cache_token": cache_token,
            "prompt_context": "",
            "fields": {
                "holding_exit_matrix_feature_enabled": bool(advisory_enabled),
                "holding_exit_matrix_applied": False,
                "holding_exit_matrix_status": status,
                "holding_exit_matrix_cohort": cohort,
                "holding_exit_matrix_version": "-",
                "holding_exit_matrix_source_date": "-",
                "holding_exit_matrix_valid_for_date": "-",
                "holding_exit_matrix_application_mode": "-",
                "holding_exit_matrix_loaded_from": str(matrix_path) if matrix_path is not None else "-",
                "holding_exit_matrix_cache_token": cache_token,
                "holding_exit_matrix_price_bucket": price_bucket,
                "holding_exit_matrix_volume_bucket": volume_bucket,
                "holding_exit_matrix_time_bucket": time_bucket,
                "holding_exit_matrix_recommended_biases": "-",
                "holding_exit_matrix_policy_hints": "-",
                "holding_exit_matrix_runtime_bias_enabled": bool(
                    getattr(TRADING_RULES, "HOLDING_EXIT_MATRIX_RUNTIME_BIAS_ENABLED", False)
                ),
                "holding_exit_matrix_runtime_bias_applied": False,
                "holding_exit_matrix_runtime_effect": "none",
                "holding_exit_matrix_original_action": "-",
                "holding_exit_matrix_forced_action": "-",
                "holding_exit_matrix_runtime_reason": "not_evaluated",
                "holding_exit_matrix_scale_in_bias": "-",
            },
            "matched_entries": [],
        }

    matched_entries = _matched_entries(payload, buckets)
    cohort = "candidate" if advisory_enabled else "baseline"
    status = "advisory_prompt_applied" if advisory_enabled else "loaded_feature_disabled"
    matrix_version = str(payload.get("matrix_version") or "-")
    source_date = str(payload.get("source_date") or "-")
    valid_for_date = str(payload.get("valid_for_date") or "-")
    application_mode = str(payload.get("application_mode") or "-")
    cache_token = (
        f"{cohort}:{matrix_version}:{price_bucket}:{volume_bucket}:{time_bucket}"
    )
    fields = {
        "holding_exit_matrix_feature_enabled": bool(advisory_enabled),
        "holding_exit_matrix_applied": bool(advisory_enabled),
        "holding_exit_matrix_status": status,
        "holding_exit_matrix_cohort": cohort,
        "holding_exit_matrix_version": matrix_version,
        "holding_exit_matrix_source_date": source_date,
        "holding_exit_matrix_valid_for_date": valid_for_date,
        "holding_exit_matrix_application_mode": application_mode,
        "holding_exit_matrix_loaded_from": str(matrix_path),
        "holding_exit_matrix_cache_token": cache_token,
        "holding_exit_matrix_price_bucket": price_bucket,
        "holding_exit_matrix_volume_bucket": volume_bucket,
        "holding_exit_matrix_time_bucket": time_bucket,
        "holding_exit_matrix_recommended_biases": ",".join(
            str(entry.get("recommended_bias") or "no_clear_edge") for entry in matched_entries
        ),
        "holding_exit_matrix_policy_hints": ",".join(
            str(entry.get("policy_hint") or "-") for entry in matched_entries
        ),
        "holding_exit_matrix_runtime_bias_enabled": bool(
            getattr(TRADING_RULES, "HOLDING_EXIT_MATRIX_RUNTIME_BIAS_ENABLED", False)
        ),
        "holding_exit_matrix_runtime_bias_applied": False,
        "holding_exit_matrix_runtime_effect": "none",
        "holding_exit_matrix_original_action": "-",
        "holding_exit_matrix_forced_action": "-",
        "holding_exit_matrix_runtime_reason": "not_evaluated",
        "holding_exit_matrix_scale_in_bias": "-",
    }
    return {
        "applied": bool(advisory_enabled),
        "status": status,
        "cohort": cohort,
        "cache_token": cache_token,
        "prompt_context": _prompt_context(payload, matched_entries) if advisory_enabled else "",
        "fields": fields,
        "matched_entries": matched_entries,
    }


def merge_holding_exit_matrix_result_fields(
    result: dict[str, Any] | None,
    runtime_context: dict[str, Any] | None,
    position_ctx: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = dict(result or {})
    context = runtime_context or {}
    fields = dict(context.get("fields") or {})
    action = payload.get("action_v2") or payload.get("action") or ""
    runtime_bias = _runtime_bias_from_entries(
        action_label=str(action or ""),
        matched_entries=list(context.get("matched_entries") or []),
        position_ctx=position_ctx,
    )
    fields.update(runtime_bias)
    forced_action = str(runtime_bias.get("holding_exit_matrix_forced_action") or "").upper()
    if runtime_bias.get("holding_exit_matrix_runtime_effect") in {"force_hold", "force_exit"} and forced_action in {
        "HOLD",
        "EXIT",
    }:
        if "action_v2" in payload:
            payload["action_v2"] = forced_action
        payload["action"] = forced_action
    fields["holding_exit_matrix_decision_alignment"] = _alignment_for_action(
        str(payload.get("action_v2") or payload.get("action") or action or ""),
        list(context.get("matched_entries") or []),
    )
    payload.update(fields)
    lifecycle_context = {
        **fields,
        **(position_ctx or {}),
        "hard_safety_veto": has_holding_exit_matrix_safety_veto({**fields, **(position_ctx or {})}),
    }
    lifecycle_decision = resolve_lifecycle_decision(
        stage="holding",
        original_action=str(payload.get("action_v2") or payload.get("action") or action or ""),
        context=lifecycle_context,
    )
    payload = apply_lifecycle_decision_to_payload(payload, lifecycle_decision)
    return payload
