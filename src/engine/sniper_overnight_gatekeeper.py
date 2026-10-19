"""Scalping overnight gatekeeper helpers."""

import time
from dataclasses import dataclass
from datetime import datetime

from src.database.models import RecommendationHistory
from src.utils import kiwoom_utils
from src.utils.constants import TRADING_RULES
from src.utils.logger import log_error, log_info
from src.utils.pipeline_event_logger import emit_pipeline_event
from src.engine.ai_response_contracts import normalize_flow_state_label
from src.engine.scalping.holding_decision_context import (
    count_holding_context_changes,
    holding_decision_context_log_fields,
)

KIWOOM_TOKEN = None
DUAL_PERSONA_ENGINE = None


@dataclass(frozen=True)
class OvernightRecordSnapshot:
    id: int
    stock_code: str
    stock_name: str
    status: str
    buy_qty: float
    buy_price: float
    buy_time: object


def _log_holding_pipeline(name, code, stage, **fields):
    emit_pipeline_event(
        "HOLDING_PIPELINE",
        name,
        code,
        stage,
        fields=fields,
    )


def _safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _safe_int(value, default=0):
    try:
        if value is None:
            return default
        return int(float(value))
    except Exception:
        return default


def _retired_entry_overnight_forbidden(mem_stock):
    source_tokens = {
        token.strip().upper()
        for token in str(
            (mem_stock or {}).get("source_signature")
            or (mem_stock or {}).get("scanner_source_signature")
            or ""
        )
        .replace("|", ",")
        .split(",")
        if token.strip()
    }
    return "LIMIT_DOWN_LIVE_UNLOCK" in source_tokens


def _entry_time_context_from_mem_stock(mem_stock):
    if not isinstance(mem_stock, dict):
        return {}
    source_quality = (
        mem_stock.get("last_watching_ai_source_quality_fields")
        if isinstance(mem_stock.get("last_watching_ai_source_quality_fields"), dict)
        else {}
    )
    feature_probe = (
        mem_stock.get("last_watching_ai_feature_probe")
        if isinstance(mem_stock.get("last_watching_ai_feature_probe"), dict)
        else {}
    )
    keys = (
        "entry_liquidity_score",
        "entry_liquidity_status",
        "fillability_score",
        "would_fill_now",
        "quote_depth_present",
        "quote_fresh_for_entry",
        "order_flow_pressure_score",
        "entry_order_flow_status",
        "order_flow_pressure_source",
        "entry_momentum_score",
        "entry_momentum_status",
        "entry_context_quality",
        "entry_context_missing_features",
        "ai_input_source_quality_status",
        "ai_input_source_quality_reason",
        "tick_context_quality",
        "tick_context_stale",
        "quote_age_ms",
        "quote_stale",
        "buy_pressure_10t",
        "net_aggressive_delta_10t",
        "tick_acceleration_ratio",
        "curr_vs_micro_vwap_bp",
        "micro_vwap_available",
        "minute_candle_window_fresh",
        "top3_depth_ratio",
        "spread_bp",
    )
    context = {}
    for key in keys:
        for source in (source_quality, feature_probe, mem_stock):
            if isinstance(source, dict) and key in source:
                value = source.get(key)
                if value is not None and str(value).strip() not in {
                    "",
                    "-",
                    "None",
                    "none",
                    "null",
                }:
                    context[key] = value
                    break
    observed_at = _safe_float(mem_stock.get("last_watching_ai_feature_probe_at"), 0.0)
    if observed_at > 0:
        context["observed_at"] = observed_at
        context["age_sec"] = f"{max(0.0, time.time() - observed_at):.3f}"
    if context:
        context["source"] = "last_watching_ai_source_quality_fields"
        context["context_role"] = "entry_time_provenance_only"
        context["current_flow_evidence"] = False
    return context


def _eod_label() -> str:
    raw = str(
        getattr(TRADING_RULES, "SCALPING_OVERNIGHT_DECISION_TIME", "15:10:00")
        or "15:10:00"
    )
    return raw[:5] if len(raw) >= 5 else "15:10"


def _overnight_gatekeeper_enabled() -> bool:
    # Permanently retired by scalping_overnight_retirement_20260906.  Keep the
    # compatibility module importable for historical tests and audit tooling,
    # but never let an environment/config override restore real-order authority.
    return False


def _snapshot_record(record: RecommendationHistory) -> OvernightRecordSnapshot:
    return OvernightRecordSnapshot(
        id=int(getattr(record, "id")),
        stock_code=str(getattr(record, "stock_code", "") or ""),
        stock_name=str(getattr(record, "stock_name", "") or ""),
        status=str(getattr(record, "status", "") or ""),
        buy_qty=float(getattr(record, "buy_qty", 0) or 0),
        buy_price=float(getattr(record, "buy_price", 0) or 0),
        buy_time=getattr(record, "buy_time", None),
    )


def _log_overnight_dual_persona_shadow_result(stock_name, code, strategy, payload):
    if not isinstance(payload, dict):
        _log_holding_pipeline(
            stock_name,
            code,
            "dual_persona_shadow_error",
            strategy=strategy,
            decision_type="overnight",
            error="invalid_shadow_payload",
        )
        return

    if payload.get("error"):
        _log_holding_pipeline(
            stock_name,
            code,
            "dual_persona_shadow_error",
            strategy=strategy,
            decision_type=payload.get("decision_type", "overnight"),
            error=payload.get("error", "unknown"),
            shadow_extra_ms=payload.get("shadow_extra_ms", 0),
        )
        return

    _log_holding_pipeline(
        stock_name,
        code,
        "dual_persona_shadow",
        strategy=strategy,
        decision_type=payload.get("decision_type", "overnight"),
        dual_mode=payload.get("mode", "shadow"),
        gemini_action=payload.get("gemini_action", ""),
        gemini_score=payload.get("gemini_score", 0),
        aggr_action=payload.get("aggr_action", ""),
        aggr_score=payload.get("aggr_score", 0),
        cons_action=payload.get("cons_action", ""),
        cons_score=payload.get("cons_score", 0),
        cons_veto=str(bool(payload.get("cons_veto", False))).lower(),
        fused_action=payload.get("fused_action", ""),
        fused_score=payload.get("fused_score", 0),
        winner=payload.get("winner", ""),
        agreement_bucket=payload.get("agreement_bucket", ""),
        hard_flags=",".join(payload.get("hard_flags", []) or []) or "-",
        shadow_extra_ms=payload.get("shadow_extra_ms", 0),
    )


def _submit_overnight_dual_persona_shadow(stock_name, code, realtime_ctx, decision):
    if (
        not bool(getattr(TRADING_RULES, "OPENAI_DUAL_PERSONA_ENABLED", False))
        or DUAL_PERSONA_ENGINE is None
    ):
        return
    try:
        DUAL_PERSONA_ENGINE.submit_overnight_shadow(
            stock_name=stock_name,
            stock_code=code,
            strategy="SCALPING",
            realtime_ctx=realtime_ctx,
            gemini_result=decision,
            callback=lambda payload: _log_overnight_dual_persona_shadow_result(
                stock_name, code, "SCALPING", payload
            ),
        )
    except Exception as e:
        log_error(
            f"🚨 [{_eod_label()} EOD 듀얼 페르소나 shadow 제출 실패] {stock_name}({code}): {e}"
        )


def _format_order_error(res) -> str:
    if isinstance(res, dict):
        msg = str(res.get("return_msg") or "").strip()
        code = str(res.get("return_code") or "").strip()
        if msg and code:
            return f"{_clean_telegram_text(msg)} (code={code})"
        if msg:
            return _clean_telegram_text(msg)
    return _clean_telegram_text(str(res))


def _clean_telegram_text(text) -> str:
    # Markdown 이스케이프 흔적(예: \\(, \\., \\])을 사람이 읽기 쉬운 일반 문자열로 복원
    cleaned = str(text or "")
    replacements = {
        r"\(": "(",
        r"\)": ")",
        r"\[": "[",
        r"\]": "]",
        r"\.": ".",
        r"\_": "_",
        r"\-": "-",
        r"\+": "+",
    }
    for src, dst in replacements.items():
        cleaned = cleaned.replace(src, dst)
    return cleaned


def _humanize_eod_action(action) -> str:
    normalized = str(action or "").upper().strip()
    if normalized == "SELL_TODAY":
        return "당일 청산"
    if normalized == "HOLD_OVERNIGHT":
        return "오버나이트 유지"
    return str(action or "")


def _flow_evidence_text(flow_result: dict) -> str:
    evidence = flow_result.get("evidence") if isinstance(flow_result, dict) else None
    if isinstance(evidence, list):
        cleaned = [
            str(item).replace("\n", " ").strip()
            for item in evidence
            if str(item).strip()
        ]
        return "|".join(cleaned[:5]) if cleaned else "-"
    return str(evidence or "-").replace("\n", " ")


def _append_mem_flow_history(
    mem_stock, *, exit_rule, profit_rate, flow_result, holding_context=None
):
    if mem_stock is None:
        return
    flow_state = normalize_flow_state_label(flow_result.get("flow_state", "-"))
    history = list(mem_stock.get("holding_flow_review_history") or [])
    history.append(
        {
            "time": datetime.now().strftime("%H:%M:%S"),
            "action": str(flow_result.get("action", "-") or "-"),
            "flow_state": flow_state,
            "score": _safe_int(flow_result.get("score"), 0),
            "profit_rate": f"{float(profit_rate or 0.0):+.2f}",
            "exit_rule": exit_rule,
            "reason": str(flow_result.get("reason", "-") or "-")[:120],
            "holding_context_signature": (
                dict(holding_context.get("flow_signature") or {})
                if isinstance(holding_context, dict)
                else {}
            ),
        }
    )
    mem_stock["holding_flow_review_history"] = history[-5:]


def _apply_overnight_flow_override(
    record, mem_stock, ws_data, ctx, decision, ai_engine
):
    """Re-check a SELL_TODAY overnight decision through the holding flow override."""
    action = str((decision or {}).get("action", "SELL_TODAY") or "SELL_TODAY").upper()
    if action != "SELL_TODAY":
        return decision
    if not bool(getattr(TRADING_RULES, "HOLDING_FLOW_OVERRIDE_ENABLED", True)):
        return decision
    if ai_engine is None or not hasattr(ai_engine, "evaluate_scalping_holding_flow"):
        return decision

    code = str(record.stock_code).strip()[:6]
    name = getattr(record, "stock_name", code)
    avg_price = _safe_float(ctx.get("avg_price", getattr(record, "buy_price", 0)), 0.0)
    curr_price = _safe_float((ws_data or {}).get("curr", ctx.get("curr_price", 0)), 0.0)
    expected_qty = _safe_int(
        getattr(record, "buy_qty", 0)
        or ((mem_stock or {}).get("buy_qty") if mem_stock else 0),
        0,
    )
    if avg_price <= 0 or curr_price <= 0 or expected_qty <= 0:
        _log_holding_pipeline(
            name,
            code,
            "overnight_flow_override_skip",
            skip_reason="invalid_position_or_price",
            avg_price=f"{avg_price:.2f}",
            curr_price=f"{curr_price:.2f}",
            expected_qty=expected_qty,
        )
        return decision

    if str(getattr(record, "status", "") or "").upper() == "SELL_ORDERED":
        ord_no = (
            (mem_stock or {}).get("sell_odno")
            or (mem_stock or {}).get("sell_ord_no")
            or ""
        )
        if not ord_no:
            _log_holding_pipeline(
                name,
                code,
                "overnight_flow_override_skip",
                skip_reason="sell_ordered_without_order_no",
            )
            return decision

    tick_limit = max(
        1, _safe_int(getattr(TRADING_RULES, "HOLDING_FLOW_REVIEW_TICK_LIMIT", 30), 30)
    )
    candle_limit = max(
        1, _safe_int(getattr(TRADING_RULES, "HOLDING_FLOW_REVIEW_CANDLE_LIMIT", 60), 60)
    )
    holding_context = (
        ctx.get("_holding_decision_context")
        if isinstance(ctx.get("_holding_decision_context"), dict)
        else None
    )
    recent_ticks = list(ctx.get("_holding_recent_ticks") or [])
    recent_candles = list(ctx.get("_holding_recent_candles") or [])
    if holding_context is None:
        try:
            recent_ticks = kiwoom_utils.get_tick_history_ka10003(
                KIWOOM_TOKEN, code, limit=tick_limit
            )
            recent_candles = kiwoom_utils.get_minute_candles_ka10080(
                KIWOOM_TOKEN, code, limit=candle_limit
            )
        except Exception as exc:
            _log_holding_pipeline(
                name,
                code,
                "overnight_flow_override_skip",
                skip_reason="context_fetch_failed",
                error=str(exc)[:160],
            )
            return decision
    if not recent_ticks:
        _log_holding_pipeline(
            name, code, "overnight_flow_override_skip", skip_reason="no_recent_ticks"
        )
        return decision

    worsen_pct = max(
        0.0,
        _safe_float(
            getattr(TRADING_RULES, "HOLDING_FLOW_OVERRIDE_WORSEN_PCT", 0.80), 0.80
        ),
    )
    pnl_pct = _safe_float(ctx.get("pnl_pct"), 0.0)
    position_ctx = {
        "exit_rule": "overnight_sell_today",
        "sell_reason_type": "OVERNIGHT",
        "reason": str((decision or {}).get("reason") or "SELL_TODAY"),
        "buy_price": avg_price,
        "avg_price": avg_price,
        "curr_price": curr_price,
        "profit_rate": pnl_pct,
        "pnl_pct": pnl_pct,
        "peak_profit": _safe_float((mem_stock or {}).get("peak_profit"), pnl_pct),
        "drawdown": 0.0,
        "held_minutes": _safe_float(ctx.get("held_minutes"), 0.0),
        "current_ai_score": _safe_float(ctx.get("score"), 0.0),
        "day_high": _safe_float(ctx.get("day_high", ctx.get("high_price")), 0.0),
        "worsen_pct": worsen_pct,
        "eod_liquidity_risk": ctx.get(
            "liquidity_risk", ctx.get("order_status_note", "-")
        ),
        "entry_time_context": _entry_time_context_from_mem_stock(mem_stock),
    }
    flow_kwargs = {
        "flow_history": (mem_stock or {}).get("holding_flow_review_history") or [],
        "decision_kind": "overnight_sell_today",
        "metadata_extra": {
            "record_id": (mem_stock or {}).get("record_id")
            or (mem_stock or {}).get("id"),
            "sim_record_id": (mem_stock or {}).get("sim_record_id"),
            "sim_parent_record_id": (mem_stock or {}).get("sim_parent_record_id")
            or (mem_stock or {}).get("record_id")
            or (mem_stock or {}).get("id"),
            "entry_adm_candidate_id": (mem_stock or {}).get("entry_adm_candidate_id")
            or (mem_stock or {}).get("candidate_id"),
            "source_event_stage": "overnight_holding_flow",
        },
    }
    if holding_context is not None:
        flow_kwargs["holding_context"] = holding_context
    flow_result = ai_engine.evaluate_scalping_holding_flow(
        name,
        code,
        ws_data or {},
        recent_ticks,
        recent_candles,
        position_ctx,
        **flow_kwargs,
    )
    prior_history = list((mem_stock or {}).get("holding_flow_review_history") or [])
    prior_review = (
        prior_history[-1]
        if prior_history and isinstance(prior_history[-1], dict)
        else {}
    )
    prior_action = str(prior_review.get("action") or "").upper()
    raw_flow_action = str(flow_result.get("action", "EXIT") or "EXIT").upper()
    context_change_count, context_change_groups = count_holding_context_changes(
        prior_review.get("holding_context_signature"),
        (
            holding_context.get("flow_signature")
            if isinstance(holding_context, dict)
            else {}
        ),
    )
    context_reversal_clamped = bool(
        isinstance(holding_context, dict)
        and holding_context.get("enabled")
        and prior_action in {"HOLD", "TRIM", "EXIT"}
        and raw_flow_action in {"HOLD", "TRIM", "EXIT"}
        and raw_flow_action != prior_action
        and context_change_count < 2
    )
    if context_reversal_clamped:
        flow_result = dict(flow_result)
        flow_result["action"] = prior_action
        flow_result["reason"] = (
            "Retain prior action; fewer than two independent context changes"
        )
    _append_mem_flow_history(
        mem_stock,
        exit_rule="overnight_sell_today",
        profit_rate=pnl_pct,
        flow_result=flow_result,
        holding_context=holding_context,
    )
    flow_action = str(flow_result.get("action", "EXIT") or "EXIT").upper()
    flow_state = normalize_flow_state_label(flow_result.get("flow_state", "-"))
    parse_failed = bool(flow_result.get("ai_parse_fail")) or flow_action not in {
        "HOLD",
        "TRIM",
        "EXIT",
    }
    _log_holding_pipeline(
        name,
        code,
        "overnight_flow_override_review",
        original_action="SELL_TODAY",
        flow_action=flow_action,
        flow_state=flow_state,
        flow_score=_safe_int(flow_result.get("score"), 0),
        flow_reason=flow_result.get("reason", "-"),
        flow_evidence=_flow_evidence_text(flow_result),
        profit_rate=f"{pnl_pct:+.2f}",
        ai_parse_fail=parse_failed,
        holding_context_raw_flow_action=raw_flow_action,
        holding_context_change_count=context_change_count,
        holding_context_change_groups=context_change_groups,
        holding_context_reversal_clamped=context_reversal_clamped,
        **holding_decision_context_log_fields(holding_context),
    )
    if parse_failed or flow_action in {"EXIT", "TRIM"}:
        _log_holding_pipeline(
            name,
            code,
            "overnight_flow_override_exit_confirmed",
            flow_action=flow_action,
            force_reason=(
                "parse_fail"
                if parse_failed
                else ("flow_trim_unsupported" if flow_action == "TRIM" else "flow_exit")
            ),
            profit_rate=f"{pnl_pct:+.2f}",
        )
        return decision
    if (
        isinstance(holding_context, dict)
        and holding_context.get("enabled")
        and not bool(
            (holding_context.get("source_quality") or {}).get(
                "hold_defer_allowed", False
            )
        )
    ):
        _log_holding_pipeline(
            name,
            code,
            "overnight_flow_override_exit_confirmed",
            flow_action=flow_action,
            force_reason="holding_context_cannot_defer",
            profit_rate=f"{pnl_pct:+.2f}",
            **holding_decision_context_log_fields(holding_context),
        )
        return decision

    overridden = dict(decision or {})
    overridden["action"] = "HOLD_OVERNIGHT"
    overridden["confidence"] = _safe_int(
        flow_result.get("score"), _safe_int(overridden.get("confidence"), 0)
    )
    overridden["reason"] = (
        f"flow override {flow_action}: {flow_result.get('reason', '-')}"
    )
    overridden["risk_note"] = (
        f"SELL_TODAY 재검문에서 {flow_state} 흐름. "
        f"추가악화 {worsen_pct:.2f}%p 도달 시 당일청산 복귀."
    )
    if mem_stock is not None:
        mem_stock["overnight_flow_override_hold"] = True
        mem_stock["overnight_flow_override_started_at"] = time.time()
        mem_stock["overnight_flow_override_candidate_profit"] = pnl_pct
        mem_stock["overnight_flow_override_worsen_pct"] = worsen_pct
        mem_stock["overnight_flow_override_flow_action"] = flow_action
        mem_stock["overnight_flow_override_flow_state"] = flow_state
    _log_holding_pipeline(
        name,
        code,
        "overnight_flow_override_hold",
        original_action="SELL_TODAY",
        final_action="HOLD_OVERNIGHT",
        flow_action=flow_action,
        flow_state=flow_state,
        flow_score=_safe_int(flow_result.get("score"), 0),
        profit_rate=f"{pnl_pct:+.2f}",
        worsen_pct=f"{worsen_pct:.2f}",
    )
    return overridden


def run_scalping_overnight_gatekeeper(ai_engine=None):
    """Retired compatibility entrypoint; it never evaluates or submits orders."""
    log_info(
        f"ℹ️ [{_eod_label()} EOD] 실 runtime 오버나이트 gatekeeper 비활성화: "
        "KORSTOCKSCAN_SCALPING_OVERNIGHT_GATEKEEPER_ENABLED=false"
    )
    return False
