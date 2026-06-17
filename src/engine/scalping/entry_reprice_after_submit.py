"""Real-only entry reprice decision helper for pending scalping BUY orders."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.trading.order.tick_utils import clamp_price_to_tick, get_tick_size


RUNTIME_FAMILY = "entry_reprice_after_submit_runtime"
POLICY_VERSION = "entry_reprice_after_submit_v1"

DEFAULT_ENABLED = True
DEFAULT_EVAL_SEC = 15
DEFAULT_MAX_ATTEMPTS = 1
DEFAULT_MAX_UPWARD_BPS = 40
DEFAULT_MAX_QUOTE_AGE_MS = 700
DEFAULT_MAX_SPREAD_BPS = 20
DEFAULT_STRONG_SCORE_FLOOR = 75.0
DEFAULT_STRONG_BUY_PRESSURE = 85.0
DEFAULT_TIGHT_SPREAD_TICKS = 2

FORBIDDEN_USES = (
    "adm_ldm_training_input|general_threshold_ev|sim_probe_ev|provider_route_change|"
    "bot_restart|hard_safety_override"
)


@dataclass(frozen=True)
class EntryRepriceDecision:
    allowed: bool
    reason: str
    target_price: int = 0
    fields: dict[str, Any] = field(default_factory=dict)

    def as_log_fields(self) -> dict[str, Any]:
        return {
            "runtime_family": RUNTIME_FAMILY,
            "policy_version": POLICY_VERSION,
            "reprice_allowed": self.allowed,
            "block_reason": "" if self.allowed else self.reason,
            "reprice_order_price": int(self.target_price or 0),
            "forbidden_uses": FORBIDDEN_USES,
            **self.fields,
        }


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(float(str(value).replace(",", "").strip()))
    except Exception:
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(str(value).replace(",", "").strip())
    except Exception:
        return default


def _tick_count(lower: int, upper: int) -> int:
    if lower <= 0 or upper <= lower:
        return 0
    ticks = 0
    price = clamp_price_to_tick(lower)
    while price < upper and ticks < 100:
        price = clamp_price_to_tick(price + get_tick_size(price))
        ticks += 1
    return ticks


def _block(reason: str, fields: dict[str, Any]) -> EntryRepriceDecision:
    return EntryRepriceDecision(False, reason, 0, fields)


def evaluate_entry_reprice_after_submit(
    *,
    order: dict[str, Any],
    strategy: str | None,
    elapsed_sec: float,
    enabled: bool = DEFAULT_ENABLED,
    eval_sec: int = DEFAULT_EVAL_SEC,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    max_upward_bps: int = DEFAULT_MAX_UPWARD_BPS,
    max_quote_age_ms: int = DEFAULT_MAX_QUOTE_AGE_MS,
    max_spread_bps: int = DEFAULT_MAX_SPREAD_BPS,
    strong_score_floor: float = DEFAULT_STRONG_SCORE_FLOOR,
    strong_buy_pressure: float = DEFAULT_STRONG_BUY_PRESSURE,
    tight_spread_ticks: int = DEFAULT_TIGHT_SPREAD_TICKS,
    best_bid: int = 0,
    best_ask: int = 0,
    current_price: int = 0,
    quote_age_ms: float | None = None,
    ai_score: float | None = None,
    chosen_action: str | None = None,
    entry_adm_recommended_action: str | None = None,
    entry_adm_ev_pct: float | None = None,
    lifecycle_matrix_selected_action: str | None = None,
    buy_pressure_10t: float | None = None,
    orderbook_micro_state: str | None = None,
    latency_state: str | None = None,
    simulated_order: bool = False,
) -> EntryRepriceDecision:
    """Return whether a pending real SCALPING BUY may be cancel-resubmitted once."""

    strategy_key = str(strategy or "").strip().upper()
    status = str(order.get("status", "OPEN") or "OPEN").strip().upper()
    order_type = str(order.get("order_type", order.get("order_type_code", "")) or "").strip()
    original_price = _safe_int(order.get("price"))
    qty = _safe_int(order.get("qty"))
    filled_qty = _safe_int(order.get("filled_qty"))
    attempt_count = _safe_int(order.get("entry_reprice_attempt_count", order.get("reprice_attempt_count")), 0)
    order_no = str(order.get("ord_no") or order.get("order_no") or "").strip()
    quote_age = None if quote_age_ms is None else _safe_float(quote_age_ms, -1.0)
    bid = _safe_int(best_bid)
    ask = _safe_int(best_ask)
    tick_size = int(get_tick_size(max(bid, ask, current_price, original_price, 1)) or 1)
    spread_bps = round(((ask - bid) / ask) * 10000.0, 3) if ask > 0 and bid > 0 and ask >= bid else 0.0
    spread_ticks = _tick_count(bid, ask)
    score = _safe_float(ai_score, _safe_float(order.get("ai_score"), 0.0))
    action = str(chosen_action or order.get("entry_reprice_action") or "").strip().upper()
    adm_action = str(entry_adm_recommended_action or order.get("entry_adm_recommended_action") or "").strip().upper()
    adm_ev = _safe_float(entry_adm_ev_pct, _safe_float(order.get("entry_adm_ev_pct"), 0.0))
    ldm_action = str(lifecycle_matrix_selected_action or order.get("lifecycle_matrix_selected_action") or "").strip().upper()
    buy_pressure = _safe_float(buy_pressure_10t, _safe_float(order.get("buy_pressure_10t"), 50.0))
    micro_state = str(orderbook_micro_state or order.get("orderbook_micro_state") or "").strip().lower()
    latency = str(latency_state or order.get("latency_state") or order.get("latency_entry_state") or "").strip().upper()
    mark_price = _safe_int(
        order.get("mark_price_at_submit")
        or order.get("submitted_mark_price")
        or order.get("latest_price_at_submit")
        or current_price
        or ask
        or bid
    )
    fields: dict[str, Any] = {
        "enabled": bool(enabled),
        "strategy": strategy_key or "-",
        "parent_order_no": order_no,
        "original_order_price": original_price,
        "current_price": _safe_int(current_price),
        "best_bid": bid,
        "best_ask": ask,
        "quote_age_ms": "-" if quote_age is None else f"{quote_age:.1f}",
        "elapsed_sec": f"{float(elapsed_sec):.1f}",
        "attempt_count": attempt_count,
        "max_attempts": int(max_attempts),
        "eval_sec": int(eval_sec),
        "max_upward_bps": int(max_upward_bps),
        "spread_bps": f"{spread_bps:.3f}",
        "spread_ticks": spread_ticks,
        "ai_score": f"{score:.1f}",
        "chosen_action": action or "-",
        "entry_adm_recommended_action": adm_action or "-",
        "entry_adm_ev_pct": f"{adm_ev:.4f}",
        "lifecycle_matrix_selected_action": ldm_action or "-",
        "buy_pressure_10t": f"{buy_pressure:.2f}",
        "orderbook_micro_state": micro_state or "-",
        "latency_state": latency or "-",
        "mark_price_at_submit": mark_price,
    }

    if not enabled:
        return _block("disabled", fields)
    if strategy_key != "SCALPING":
        return _block("non_scalping", fields)
    if simulated_order or bool(order.get("simulated_order")):
        return _block("sim_or_probe_order", fields)
    if float(elapsed_sec) < int(eval_sec):
        return _block("wait_eval_window", fields)
    if attempt_count >= int(max_attempts):
        return _block("attempt_limit", fields)
    if status not in {"OPEN", "SENT"}:
        return _block("order_not_open", fields)
    if not order_no:
        return _block("missing_parent_order_no", fields)
    if qty <= 0:
        return _block("invalid_qty", fields)
    if filled_qty > 0:
        return _block("partial_fill", fields)
    if order_type and order_type not in {"00", "LIMIT"}:
        return _block("unsupported_order_type", fields)
    if bid <= 0 or ask <= 0 or ask < bid:
        return _block("invalid_quote", fields)
    if quote_age is None or quote_age < 0 or quote_age > int(max_quote_age_ms):
        return _block("quote_stale", fields)
    if latency not in {"SAFE", "CAUTION"}:
        return _block("latency_state_not_safe", fields)
    if spread_bps > float(max_spread_bps):
        return _block("spread_too_wide", fields)
    if score < float(strong_score_floor):
        return _block("low_ai_score", fields)
    if action not in {"BUY_DEFENSIVE", "BUY_NOW"}:
        return _block("action_not_buy", fields)
    if micro_state in {"bearish", "strong_bearish"}:
        return _block("micro_bearish", fields)

    strong_continuation = (
        spread_ticks <= int(tight_spread_ticks)
        and buy_pressure >= float(strong_buy_pressure)
        and ldm_action in {"BUY_DEFENSIVE", "BUY_NOW", ""}
    )
    if adm_action == "NO_BUY_AI" and adm_ev < 0:
        fields["reprice_candidate"] = (
            "continuation_override_candidate" if strong_continuation else "adm_negative_prior"
        )
        reason = "continuation_override_candidate_report_only" if strong_continuation else "adm_negative_prior"
        return _block(reason, fields)

    target = bid
    if strong_continuation and ask > tick_size:
        target = clamp_price_to_tick(ask - tick_size)
        fields["reprice_price_mode"] = "tight_spread_best_ask_minus_1tick"
    else:
        fields["reprice_price_mode"] = "best_bid"
    target = min(target, ask)
    target = clamp_price_to_tick(target)
    if target <= original_price:
        return _block("price_not_improved", fields)

    cap_base = max(mark_price, original_price, 1)
    cap_price = clamp_price_to_tick(cap_base * (1.0 + (float(max_upward_bps) / 10000.0)))
    fields["max_upward_cap_price"] = cap_price
    if target > cap_price:
        target = clamp_price_to_tick(cap_price)
        if target > ask:
            target = clamp_price_to_tick(ask)
        if target <= original_price:
            return _block("upward_cap", fields)
    if target > ask:
        return _block("target_above_best_ask", fields)

    return EntryRepriceDecision(True, "allow", int(target), fields)
