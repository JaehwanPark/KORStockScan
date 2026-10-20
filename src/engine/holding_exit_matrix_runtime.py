from __future__ import annotations

from src.engine.lifecycle.retirement import RETIREMENT_ID

import re
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from src.engine.lifecycle.neutral_decision_context import (
    apply_lifecycle_decision_to_payload,
    resolve_lifecycle_decision,
)
from src.utils.constants import DATA_DIR, TRADING_RULES as TRADING_RULES

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


def _resolve_intraday_volume(
    ws_data: dict[str, Any] | None, recent_candles: list[dict[str, Any]] | None
) -> Any:
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


def _alignment_for_action(
    action_label: str, matched_entries: list[dict[str, Any]]
) -> str:
    action = str(action_label or "").upper()
    biases = {
        str(entry.get("recommended_bias") or "no_clear_edge")
        for entry in matched_entries
    }
    if not action:
        return "action_not_available"
    if biases == {"no_clear_edge"}:
        return "neutral_no_clear_edge"
    if "prefer_exit" in biases and action in {"EXIT", "TRIM", "DROP", "SELL"}:
        return "aligned_exit_bias"
    if biases & {"prefer_avg_down_wait", "prefer_pyramid_wait"} and action in {
        "HOLD",
        "WAIT",
    }:
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
    return str(value).strip().lower() in {
        "1",
        "true",
        "yes",
        "y",
        "on",
        "blocked",
        "block",
    }


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


def _runtime_bias_from_entries(
    *,
    action_label: str,
    matched_entries: list[dict[str, Any]],
    position_ctx: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "holding_exit_matrix_runtime_bias_enabled": False,
        "holding_exit_matrix_runtime_bias_applied": False,
        "holding_exit_matrix_runtime_effect": "none",
        "holding_exit_matrix_original_action": action_label or "-",
        "holding_exit_matrix_forced_action": "-",
        "holding_exit_matrix_runtime_reason": "retired",
        "holding_exit_matrix_scale_in_bias": "-",
    }


def resolve_holding_exit_matrix_scale_in_bias(
    *,
    strategy: str,
    profit_rate: float,
    peak_profit: float,
    current_ai_score: float,
    held_sec: int,
    safety_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "should_add": False,
        "reason": "holding_exit_matrix_retired",
        "holding_exit_matrix_scale_in_bias": "-",
    }


def build_holding_exit_matrix_runtime_context(
    *,
    prompt_profile: str,
    ws_data: dict[str, Any] | None,
    recent_candles: list[dict[str, Any]] | None,
    advisory_enabled: bool,
    now: datetime | None = None,
) -> dict[str, Any]:
    current_dt = now or datetime.now()
    price_bucket = _price_bucket(
        (ws_data or {}).get("curr") or (ws_data or {}).get("curr_price")
    )
    volume_bucket = _volume_bucket(_resolve_intraday_volume(ws_data, recent_candles))
    time_bucket = _time_bucket(current_dt)
    return {
        "applied": False,
        "status": "retired",
        "cohort": "excluded",
        "cache_token": RETIREMENT_ID,
        "prompt_context": "",
        "fields": {
            "holding_exit_matrix_feature_enabled": False,
            "holding_exit_matrix_applied": False,
            "holding_exit_matrix_status": "retired",
            "holding_exit_matrix_cohort": "excluded",
            "holding_exit_matrix_version": "-",
            "holding_exit_matrix_source_date": "-",
            "holding_exit_matrix_valid_for_date": "-",
            "holding_exit_matrix_application_mode": "-",
            "holding_exit_matrix_loaded_from": "-",
            "holding_exit_matrix_cache_token": RETIREMENT_ID,
            "holding_exit_matrix_price_bucket": price_bucket,
            "holding_exit_matrix_volume_bucket": volume_bucket,
            "holding_exit_matrix_time_bucket": time_bucket,
            "holding_exit_matrix_recommended_biases": "-",
            "holding_exit_matrix_policy_hints": "-",
            "holding_exit_matrix_runtime_bias_enabled": False,
            "holding_exit_matrix_runtime_bias_applied": False,
            "holding_exit_matrix_runtime_effect": "none",
            "holding_exit_matrix_original_action": "-",
            "holding_exit_matrix_forced_action": "-",
            "holding_exit_matrix_runtime_reason": "not_evaluated",
            "holding_exit_matrix_scale_in_bias": "-",
        },
        "matched_entries": [],
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
    forced_action = str(
        runtime_bias.get("holding_exit_matrix_forced_action") or ""
    ).upper()
    if runtime_bias.get("holding_exit_matrix_runtime_effect") in {
        "force_hold",
        "force_exit",
    } and forced_action in {
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
        "hard_safety_veto": has_holding_exit_matrix_safety_veto(
            {**fields, **(position_ctx or {})}
        ),
    }
    lifecycle_decision = resolve_lifecycle_decision(
        stage="holding",
        original_action=str(
            payload.get("action_v2") or payload.get("action") or action or ""
        ),
        context=lifecycle_context,
    )
    payload = apply_lifecycle_decision_to_payload(payload, lifecycle_decision)
    return payload
