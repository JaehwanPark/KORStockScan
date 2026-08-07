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


def canonical_entry_edge_state(ai_result: dict[str, Any] | None) -> str:
    """Resolve the canonical entry edge state across normalized payload shapes."""

    result = ai_result if isinstance(ai_result, dict) else {}
    return (
        str(
            result.get("edge_state")
            or result.get("decision_quality_model_edge_state")
            or ""
        )
        .strip()
        .upper()
    )


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
    source_excluded_reason = ""
    if fallback_50:
        source_excluded_reason = "fallback_score_50"
    elif parse_fail or not parse_ok:
        source_excluded_reason = "parse_fail_or_not_ok"
    elif unusable_source:
        source_excluded_reason = f"unusable_source:{source}"

    excluded_reason = source_excluded_reason or (
        "stale_quote_or_context" if stale else ""
    )
    usable = not excluded_reason
    # Direct submission remains fail-closed on stale input.  A canonical WAIT
    # recheck may retain only source/parse eligibility because its single owner
    # refreshes the quote and re-applies freshness before granting probe access.
    recheck_source_usable = not source_excluded_reason
    score = _safe_float(ai_score if ai_score is not None else result.get("score"), 0.0)
    action = str(ai_action or result.get("action") or "").strip().upper()
    evidence = (
        result.get("evidence") if isinstance(result.get("evidence"), dict) else {}
    )
    contract_status = (
        str(result.get("decision_quality_contract_status") or "").strip().lower()
    )
    edge_state = canonical_entry_edge_state(result)
    probe_intent = _truthy(result.get("entry_probe_intent"))
    probe_intent_status = (
        str(result.get("entry_probe_intent_status") or "").strip().lower()
    )
    recovery_trigger = str(evidence.get("trigger") or "").strip().lower()
    adverse_risk = str(evidence.get("adverse_risk") or "").strip().lower()
    recheck_usable = bool(
        recheck_source_usable
        and action in {"WAIT", "WAIT_REQUOTE"}
        and contract_status == "pass"
        and edge_state == "EDGE"
        and probe_intent
        and probe_intent_status == "eligible_wait_probe"
        and recovery_trigger == "recovery_required"
        and adverse_risk != "blocking"
    )
    prior = evaluate_ai_score_prior(action, score, usable=usable)
    return {
        "entry_score_role_gate": "usable" if usable else "excluded",
        "entry_score_source": source,
        "entry_score_source_stage": str(source_stage or ""),
        "entry_score_action": action or "-",
        "entry_score_value": round(score, 3),
        "entry_score_usable_for_entry_submit": bool(usable),
        "entry_score_usable_for_recheck": recheck_usable,
        "entry_recheck_source_usable": recheck_source_usable,
        "entry_recheck_freshness_refresh_required": bool(stale and recheck_usable),
        "entry_recheck_excluded_reason": source_excluded_reason or "-",
        "entry_score_usable_for_state_history": bool(usable),
        "entry_score_excluded_reason": excluded_reason or "-",
        "entry_recheck_contract_status": contract_status or "unreported",
        "entry_recheck_edge_state": edge_state or "-",
        "entry_recheck_probe_intent": probe_intent,
        "entry_recheck_probe_intent_status": probe_intent_status or "not_reported",
        "entry_recheck_recovery_trigger": recovery_trigger or "-",
        "entry_recheck_adverse_risk": adverse_risk or "not_reported",
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
        "entry_recheck_source_usable": bool(
            gate.get("entry_recheck_source_usable", False)
        ),
        "entry_recheck_freshness_refresh_required": bool(
            gate.get("entry_recheck_freshness_refresh_required", False)
        ),
        "entry_recheck_excluded_reason": gate.get("entry_recheck_excluded_reason", "-"),
        "entry_score_usable_for_state_history": bool(
            gate.get("entry_score_usable_for_state_history", False)
        ),
        "entry_score_excluded_reason": gate.get("entry_score_excluded_reason", "-"),
        "entry_recheck_contract_status": gate.get(
            "entry_recheck_contract_status", "unreported"
        ),
        "entry_recheck_edge_state": gate.get("entry_recheck_edge_state", "-"),
        "entry_recheck_probe_intent": bool(
            gate.get("entry_recheck_probe_intent", False)
        ),
        "entry_recheck_probe_intent_status": gate.get(
            "entry_recheck_probe_intent_status", "not_reported"
        ),
        "entry_recheck_recovery_trigger": gate.get(
            "entry_recheck_recovery_trigger", "-"
        ),
        "entry_recheck_adverse_risk": gate.get(
            "entry_recheck_adverse_risk", "not_reported"
        ),
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
