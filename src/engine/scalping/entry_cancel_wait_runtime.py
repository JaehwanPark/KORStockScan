"""Independent runtime and counterfactual contracts for BUY cancel wait tuning."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


RUNTIME_FAMILY = "entry_cancel_wait_runtime"
POLICY_VERSION = "entry_cancel_wait_runtime_v1"
COUNTERFACTUAL_AUTHORITY = "entry_cancel_wait_counterfactual_only"
DEFAULT_THRESHOLDS = {
    "standard": 60,
    "breakout": 120,
    "pullback": 600,
    "reserve": 1200,
}


def resolve_profile(position_tag: Any = "", entry_mode: Any = "") -> str:
    text = f"{position_tag or ''}|{entry_mode or ''}".upper()
    if "RESERVE" in text:
        return "reserve"
    if "PULLBACK" in text:
        return "pullback"
    if "BREAKOUT" in text:
        return "breakout"
    return "standard"


def candidate_thresholds(profile: str, selected_timeout_sec: int) -> list[int]:
    selected = max(5, min(1200, int(selected_timeout_sec or DEFAULT_THRESHOLDS[profile])))
    if profile in {"standard", "breakout"}:
        step = 30
    else:
        step = max(30, int(round(selected * 0.10)))
    return sorted({max(5, selected - step), selected, min(1200, selected + step)})


def new_counterfactual_observation(
    *,
    order_no: str,
    submitted_at: float,
    cancelled_at: float,
    submitted_price: int,
    qty: int,
    profile: str,
    actual_timeout_sec: int,
    selected_timeout_sec: int,
) -> dict[str, Any]:
    return {
        "runtime_family": RUNTIME_FAMILY,
        "policy_version": POLICY_VERSION,
        "order_no": str(order_no or ""),
        "submitted_at": float(submitted_at or cancelled_at),
        "cancelled_at": float(cancelled_at),
        "submitted_price": int(submitted_price or 0),
        "qty": int(qty or 0),
        "profile": profile,
        "actual_timeout_sec": int(actual_timeout_sec or 0),
        "selected_timeout_sec": int(selected_timeout_sec or 0),
        "candidate_timeout_secs": candidate_thresholds(profile, selected_timeout_sec),
        "candidates": {},
        "completed": False,
    }


def observe_counterfactual(
    observation: dict[str, Any], *, now_ts: float, current_price: int
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Advance one observation without creating order or lifecycle authority."""
    state = dict(observation or {})
    candidates = dict(state.get("candidates") or {})
    events: list[dict[str, Any]] = []
    submitted_at = float(state.get("submitted_at") or now_ts)
    order_price = int(state.get("submitted_price") or 0)
    qty = int(state.get("qty") or 0)
    elapsed = max(0.0, float(now_ts) - submitted_at)
    for timeout in state.get("candidate_timeout_secs") or []:
        key = str(int(timeout))
        candidate = dict(candidates.get(key) or {})
        if not candidate.get("evaluated") and elapsed >= int(timeout):
            would_fill = bool(order_price > 0 and current_price > 0 and current_price <= order_price)
            candidate.update({
                "evaluated": True,
                "would_fill": would_fill,
                "fill_price": order_price if would_fill else 0,
                "evaluated_at": float(now_ts),
                "evaluation_price": int(current_price or 0),
            })
            events.append({"stage": "entry_cancel_wait_counterfactual_threshold", "timeout_sec": int(timeout), **candidate})
        if candidate.get("would_fill") and not candidate.get("completed"):
            fill_at = float(candidate.get("evaluated_at") or now_ts)
            if now_ts - fill_at >= 60:
                fill_price = int(candidate.get("fill_price") or 0)
                pnl_pct = ((current_price - fill_price) / fill_price * 100.0) if fill_price > 0 else 0.0
                candidate.update({"completed": True, "mark_price_60s": int(current_price or 0), "counterfactual_ev_pct": round(pnl_pct, 6)})
                events.append({"stage": "entry_cancel_wait_counterfactual_completed", "timeout_sec": int(timeout), **candidate})
        candidates[key] = candidate
    max_timeout = max((int(x) for x in state.get("candidate_timeout_secs") or [0]), default=0)
    all_evaluated = all((candidates.get(str(int(x))) or {}).get("evaluated") for x in state.get("candidate_timeout_secs") or [])
    all_fills_completed = all(
        not item.get("would_fill") or item.get("completed")
        for item in candidates.values()
    )
    state["candidates"] = candidates
    state["completed"] = bool(all_evaluated and all_fills_completed and elapsed >= max_timeout)
    return state, events
