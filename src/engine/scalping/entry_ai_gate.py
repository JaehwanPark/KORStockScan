"""Shared helpers for scalping entry AI score gate semantics."""

from __future__ import annotations

from typing import Any

from src.utils.constants import TRADING_RULES

UNUSABLE_RESULT_SOURCES = {
    "engine_disabled",
    "exception",
    "error",
    "fallback_score_50",
    "holding_ai_not_called",
    "insufficient",
    "lock_contention",
    "source_quality_insufficient",
    "timeout",
    "unknown",
    "watching_cooldown",
}
UNUSABLE_RESULT_SOURCE_TOKENS = (
    "engine_disabled",
    "fallback_score_50",
    "insufficient",
    "lock_contention",
    "timeout",
)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, "", "null", "none", "-"):
            return default
        return float(value)
    except Exception:
        return default


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return value != 0
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _stale_flag(value: Any) -> bool:
    if _truthy(value):
        return True
    return str(value or "").strip().lower() in {
        "stale",
        "quote_stale",
        "stale_quote",
        "tick_context_stale",
        "context_stale",
    }


def get_entry_buy_score_threshold(config: dict[str, Any] | None = None) -> float:
    if isinstance(config, dict) and config.get("BUY_SCORE_THRESHOLD") not in (None, ""):
        return _safe_float(config.get("BUY_SCORE_THRESHOLD"), 75.0)
    return _safe_float(getattr(TRADING_RULES, "BUY_SCORE_THRESHOLD", 75), 75.0)


def evaluate_ai_score_prior(
    action: Any,
    score: Any,
    config: dict[str, Any] | None = None,
    *,
    threshold_key: str = "BUY_SCORE_THRESHOLD",
    default_threshold: float = 75.0,
    usable: bool = True,
) -> dict[str, Any]:
    threshold = (
        _safe_float(config.get(threshold_key), default_threshold)
        if isinstance(config, dict) and config.get(threshold_key) not in (None, "")
        else _safe_float(
            getattr(TRADING_RULES, threshold_key, default_threshold), default_threshold
        )
    )
    score_value = _safe_float(score, 0.0)
    action_value = str(action or "").strip().upper() or "-"
    if not usable:
        band = "neutral_or_unknown"
        weight = 0.0
        confidence = "unknown"
        reason = "score_unusable_neutral_prior"
    elif score_value >= threshold + 5.0:
        band = "high"
        weight = 1.0
        confidence = "high"
        reason = "score_prior_high"
    elif score_value >= threshold:
        band = "supportive"
        weight = 0.6
        confidence = "medium"
        reason = "score_prior_supportive"
    elif score_value >= threshold - 10.0:
        band = "low"
        weight = -0.3
        confidence = "medium"
        reason = "score_prior_low"
    else:
        band = "very_low"
        weight = -0.6
        confidence = "medium"
        reason = "score_prior_very_low"

    if action_value != "BUY":
        weight = min(weight, 0.0)
        if usable:
            reason = "ai_action_not_buy_score_prior"

    return {
        "score_gate_converted_to_prior": True,
        "hard_gate_veto": False,
        "score_prior_band": band,
        "ai_score_prior_weight": round(float(weight), 4),
        "score_prior_confidence": confidence,
        "score_prior_reason": reason,
        "score_prior_threshold": round(float(threshold), 4),
        "score_prior_action": action_value,
        "score_prior_score": round(float(score_value), 4),
    }


def entry_buy_decision_allowed(
    action: Any, score: Any, config: dict[str, Any] | None = None
) -> bool:
    return str(action or "").strip().upper() == "BUY"


def evaluate_entry_score_role_gate(
    ai_result: dict[str, Any] | None,
    *,
    ws_data: dict[str, Any] | None = None,
    source_stage: str = "",
    ai_score: Any = None,
    ai_action: Any = None,
) -> dict[str, Any]:
    result = ai_result if isinstance(ai_result, dict) else {}
    ws = ws_data if isinstance(ws_data, dict) else {}
    source = (
        str(result.get("ai_result_source") or result.get("result_source") or "").strip()
        or "unknown"
    )
    source_l = source.lower()
    parse_fail = _truthy(result.get("ai_parse_fail"))
    parse_ok_value = result.get("ai_parse_ok")
    parse_ok = True if parse_ok_value in (None, "") else _truthy(parse_ok_value)
    fallback_50 = _truthy(result.get("ai_fallback_score_50"))
    stale = any(
        _stale_flag(value)
        for value in (
            result.get("tick_context_stale"),
            result.get("quote_stale"),
            result.get("context_stale"),
            ws.get("tick_context_stale"),
            ws.get("quote_stale"),
            ws.get("context_stale"),
        )
    )
    unusable_source = source_l in UNUSABLE_RESULT_SOURCES or any(
        token in source_l for token in UNUSABLE_RESULT_SOURCE_TOKENS
    )
    excluded_reason = ""
    if fallback_50:
        excluded_reason = "fallback_score_50"
    elif parse_fail or not parse_ok:
        excluded_reason = "parse_fail_or_not_ok"
    elif unusable_source:
        excluded_reason = f"unusable_source:{source}"
    elif stale:
        excluded_reason = "stale_quote_or_context"

    usable = not excluded_reason
    score = _safe_float(ai_score if ai_score is not None else result.get("score"), 0.0)
    action = str(ai_action or result.get("action") or "").strip().upper()
    prior = evaluate_ai_score_prior(action, score, usable=usable)
    return {
        "entry_score_role_gate": "usable" if usable else "excluded",
        "entry_score_source": source,
        "entry_score_source_stage": str(source_stage or ""),
        "entry_score_action": action or "-",
        "entry_score_value": round(score, 3),
        "entry_score_usable_for_entry_submit": bool(usable),
        "entry_score_usable_for_recheck": bool(usable),
        "entry_score_usable_for_state_history": bool(usable),
        "entry_score_excluded_reason": excluded_reason or "-",
        **prior,
    }


def entry_score_role_log_fields(role_gate: dict[str, Any] | None) -> dict[str, Any]:
    gate = role_gate if isinstance(role_gate, dict) else {}
    return {
        "entry_score_role_gate": gate.get("entry_score_role_gate", "unknown"),
        "entry_score_source": gate.get("entry_score_source", "unknown"),
        "entry_score_source_stage": gate.get("entry_score_source_stage", ""),
        "entry_score_usable_for_entry_submit": bool(
            gate.get("entry_score_usable_for_entry_submit", False)
        ),
        "entry_score_usable_for_recheck": bool(
            gate.get("entry_score_usable_for_recheck", False)
        ),
        "entry_score_usable_for_state_history": bool(
            gate.get("entry_score_usable_for_state_history", False)
        ),
        "entry_score_excluded_reason": gate.get("entry_score_excluded_reason", "-"),
        "score_gate_converted_to_prior": bool(
            gate.get("score_gate_converted_to_prior", True)
        ),
        "hard_gate_veto": bool(gate.get("hard_gate_veto", False)),
        "score_prior_band": gate.get("score_prior_band", "neutral_or_unknown"),
        "ai_score_prior_weight": gate.get("ai_score_prior_weight", 0.0),
        "score_prior_confidence": gate.get("score_prior_confidence", "unknown"),
        "score_prior_reason": gate.get("score_prior_reason", "score_prior_unavailable"),
        "score_prior_threshold": gate.get(
            "score_prior_threshold", get_entry_buy_score_threshold()
        ),
    }
