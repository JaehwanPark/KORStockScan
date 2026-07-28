"""Pure state transitions for post-block adverse-micro recovery observation.

This module is deliberately observation-only.  It never selects a candidate,
changes a guard, or has broker authority; the runtime owner supplies fresh WS
snapshots and emits the returned records.
"""

from __future__ import annotations

from typing import Any

CHECKPOINTS_SEC = (15, 30, 60)


def create_observation(
    *,
    observation_id: str,
    stock_code: str,
    reference_price: float,
    registered_at: float,
    effective_venue: str,
    source_block_reason: str,
) -> dict[str, Any]:
    """Create one bounded, source-only observation state."""

    return {
        "observation_id": str(observation_id),
        "stock_code": str(stock_code),
        "reference_price": float(reference_price),
        "registered_at": float(registered_at),
        "effective_venue": str(effective_venue),
        "source_block_reason": str(source_block_reason),
        "next_checkpoint_index": 0,
        "next_scanner_loop_rechecked": False,
        "next_scanner_loop_recheck_count": 0,
        "reentry_candidate_allowed": False,
        "reentry_candidate_allowed_at": None,
        "max_move_pct": None,
        "min_move_pct": None,
        "recovery_observed": False,
        "recovery_first_at": None,
    }


def record_next_scanner_loop(state: dict[str, Any], *, now_ts: float) -> bool:
    """Mark that the blocked symbol returned to the scanner path."""

    if float(now_ts) <= float(state.get("registered_at") or 0.0):
        return False
    state["next_scanner_loop_rechecked"] = True
    state["next_scanner_loop_recheck_count"] = (
        int(state.get("next_scanner_loop_recheck_count") or 0) + 1
    )
    return True


def record_reentry_candidate_decision(
    state: dict[str, Any], *, allowed: bool, now_ts: float
) -> None:
    """Keep candidate re-entry separate from actual broker submission."""

    if not allowed or float(now_ts) <= float(state.get("registered_at") or 0.0):
        return
    state["reentry_candidate_allowed"] = True
    if state.get("reentry_candidate_allowed_at") is None:
        state["reentry_candidate_allowed_at"] = float(now_ts)


def consume_due_checkpoints(
    state: dict[str, Any],
    *,
    now_ts: float,
    price: float | None,
    price_fresh: bool,
    price_source: str,
    source_reason: str,
) -> tuple[list[dict[str, Any]], bool]:
    """Return all due 15/30/60-second observation records exactly once.

    A late runtime pass may satisfy multiple checkpoints with the same fresh
    snapshot; each record preserves its scheduled checkpoint and observed age.
    """

    output: list[dict[str, Any]] = []
    index = int(state.get("next_checkpoint_index") or 0)
    registered_at = float(state.get("registered_at") or 0.0)
    reference_price = float(state.get("reference_price") or 0.0)
    elapsed_sec = max(0.0, float(now_ts) - registered_at)
    while index < len(CHECKPOINTS_SEC) and elapsed_sec >= CHECKPOINTS_SEC[index]:
        checkpoint_sec = CHECKPOINTS_SEC[index]
        move_pct = None
        if (
            price_fresh
            and price is not None
            and float(price) > 0
            and reference_price > 0
        ):
            move_pct = ((float(price) - reference_price) / reference_price) * 100.0
            previous_max = state.get("max_move_pct")
            previous_min = state.get("min_move_pct")
            state["max_move_pct"] = (
                move_pct if previous_max is None else max(float(previous_max), move_pct)
            )
            state["min_move_pct"] = (
                move_pct if previous_min is None else min(float(previous_min), move_pct)
            )
            if move_pct > 0 and not state.get("recovery_observed"):
                state["recovery_observed"] = True
                state["recovery_first_at"] = float(now_ts)
        output.append(
            {
                "checkpoint_sec": checkpoint_sec,
                "elapsed_sec": elapsed_sec,
                "price_fresh": bool(price_fresh),
                "current_price": int(float(price)) if price_fresh and price else None,
                "move_pct": move_pct,
                "price_source": str(price_source),
                "source_reason": str(source_reason),
                "next_scanner_loop_rechecked": bool(
                    state.get("next_scanner_loop_rechecked")
                ),
                "next_scanner_loop_recheck_count": int(
                    state.get("next_scanner_loop_recheck_count") or 0
                ),
                "reentry_candidate_allowed": bool(
                    state.get("reentry_candidate_allowed")
                ),
                "reentry_candidate_allowed_at": state.get(
                    "reentry_candidate_allowed_at"
                ),
                "recovery_observed": bool(state.get("recovery_observed")),
                "recovery_first_at": state.get("recovery_first_at"),
                "max_move_pct": state.get("max_move_pct"),
                "min_move_pct": state.get("min_move_pct"),
            }
        )
        index += 1
    state["next_checkpoint_index"] = index
    return output, index >= len(CHECKPOINTS_SEC)
