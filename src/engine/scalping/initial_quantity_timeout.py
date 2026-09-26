"""Pure timeout schedule and terminal gate for initial entry bundles.

The functions here do not submit, cancel, or confirm broker orders. Runtime
activation requires a separately validated quantity policy and owner handoff.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from datetime import datetime
from typing import Any

from src.engine.scalping.initial_quantity_type import QUANTITY_TYPES, kst_timestamp

MAX_BUNDLE_WAIT_SEC = 1200
SCHEDULE_SCHEMA = "initial_quantity_bundle_timeout_schedule_v1"
_TERMINAL_STATES = {"TERMINAL_FILLED", "TERMINAL_CANCELLED", "TERMINAL_SKIPPED"}
_OPEN_STATES = {"OPEN", "PARTIAL", "CANCEL_REQUESTED"}


def _nonnegative_int(value: Any) -> bool:
    return type(value) is int and value >= 0


def _identity(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _terminal_proof_valid(item: dict[str, Any], state: str, slot: dict[str, Any],
                          now_epoch: float) -> bool:
    confirmed_at = item.get("terminal_confirmed_at_epoch")
    if (item.get("terminal_confirmed") is not True
            or isinstance(confirmed_at, bool)
            or not isinstance(confirmed_at, (int, float))
            or not math.isfinite(confirmed_at)
            or not slot["slot_start_epoch"] <= confirmed_at <= now_epoch):
        return False
    if state == "TERMINAL_SKIPPED":
        return bool(confirmed_at >= slot["cancel_request_by_epoch"]
                and item.get("order_absence_confirmed") is True
                and _identity(item.get("order_absence_receipt_id"))
                and _identity(item.get("owner_registry_receipt_id"))
                and not str(item.get("broker_order_no") or "").strip()
                and item.get("skip_reason") == "insufficient_time_for_cancel_confirmation")
    ordered = item.get("ordered_qty")
    filled = item.get("filled_qty")
    cancelled = item.get("cancelled_qty")
    return bool(
        _identity(item.get("broker_order_no"))
        and _identity(item.get("broker_terminal_receipt_id"))
        and _identity(item.get("owner_registry_receipt_id"))
        and _identity(item.get("account_position_receipt_id"))
        and _nonnegative_int(item.get("broker_unfilled_qty"))
        and item["broker_unfilled_qty"] == 0
        and item.get("owner_registry_terminal") is True
        and item.get("account_position_reconciled") is True
        and _nonnegative_int(ordered) and ordered > 0
        and _nonnegative_int(filled) and _nonnegative_int(cancelled)
        and filled + cancelled == ordered
        and ((state == "TERMINAL_FILLED" and filled == ordered)
             or (state == "TERMINAL_CANCELLED" and cancelled > 0)))


def _digest(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=True).encode("ascii")).hexdigest()


def build_bundle_timeout_schedule(
    *, quantity_type: str, policy_sha256: str, decision_at: str,
    order_start_at: str,
    total_wait_sec: int, leg_count: int, cancel_confirm_reserve_sec: int,
) -> dict[str, Any]:
    """Partition a bounded post-start budget into sequential leg slots."""
    decision = kst_timestamp(decision_at)
    start = kst_timestamp(order_start_at)
    try:
        decision_source_clock = datetime.fromisoformat(str(decision_at))
        start_source_clock = datetime.fromisoformat(str(order_start_at))
    except ValueError:
        decision_source_clock = None
        start_source_clock = None
    if (quantity_type not in QUANTITY_TYPES
            or not re.fullmatch(r"[0-9a-f]{64}", str(policy_sha256 or ""))
            or decision is None or start is None or start < decision
            or decision_source_clock is None or decision_source_clock.tzinfo is None
            or start_source_clock is None or start_source_clock.tzinfo is None
            or type(total_wait_sec) is not int or not 1 <= total_wait_sec <= MAX_BUNDLE_WAIT_SEC
            or type(leg_count) is not int or not 1 <= leg_count <= 4
            or type(cancel_confirm_reserve_sec) is not int
            or cancel_confirm_reserve_sec < 1
            or total_wait_sec / leg_count <= cancel_confirm_reserve_sec):
        raise ValueError("initial_quantity_timeout_contract_invalid")
    slot_sec = total_wait_sec / leg_count
    start_epoch = start.timestamp()
    slots = []
    for index in range(leg_count):
        slot_start = start_epoch + index * slot_sec
        slot_end = start_epoch + (index + 1) * slot_sec
        slots.append({
            "leg_index": index,
            "slot_start_epoch": slot_start,
            "cancel_request_by_epoch": slot_end - cancel_confirm_reserve_sec,
            "terminal_confirm_by_epoch": slot_end,
        })
    body = {
        "schema": SCHEDULE_SCHEMA,
        "quantity_type": quantity_type,
        "policy_sha256": policy_sha256,
        "decision_at": decision.isoformat(),
        "decision_at_epoch": decision.timestamp(),
        "order_start_at": start.isoformat(),
        "order_start_at_epoch": start_epoch,
        "total_wait_sec": total_wait_sec,
        "leg_count": leg_count,
        "per_leg_slot_sec": slot_sec,
        "cancel_confirm_reserve_sec": cancel_confirm_reserve_sec,
        "bundle_deadline_epoch": start_epoch + total_wait_sec,
        "probe_included_in_leg_count": True,
        "sequential_activation": True,
        "slots": slots,
    }
    return {**body, "schedule_sha256": _digest(body)}


def timeout_schedule_valid(schedule: Any) -> bool:
    if not isinstance(schedule, dict):
        return False
    try:
        expected = build_bundle_timeout_schedule(
            quantity_type=schedule["quantity_type"],
            policy_sha256=schedule["policy_sha256"],
            decision_at=schedule["decision_at"],
            order_start_at=schedule["order_start_at"],
            total_wait_sec=schedule["total_wait_sec"],
            leg_count=schedule["leg_count"],
            cancel_confirm_reserve_sec=schedule["cancel_confirm_reserve_sec"],
        )
    except (KeyError, TypeError, ValueError, OverflowError, OSError):
        return False
    return schedule == expected


def next_bundle_timeout_action(
    schedule: dict[str, Any], leg_states: list[dict[str, Any]], *, now_epoch: float,
) -> dict[str, Any]:
    """Require terminal proof before a later leg may be submitted.

    A late broker confirmation can exceed the target deadline externally. In
    that case this gate remains in RECONCILE and forbids successor BUY orders.
    """
    if (not timeout_schedule_valid(schedule)
            or not isinstance(leg_states, list)
            or len(leg_states) != schedule["leg_count"]
            or isinstance(now_epoch, bool)
            or not isinstance(now_epoch, (int, float))
            or not math.isfinite(now_epoch)):
        return {"action": "BLOCK_INVALID_TIMEOUT_CONTRACT"}
    overdue = now_epoch > schedule["bundle_deadline_epoch"]
    for index, (slot, item) in enumerate(zip(schedule["slots"], leg_states)):
        if not isinstance(item, dict):
            return {"action": "BLOCK_INVALID_LEG_STATE", "leg_index": index}
        state = item.get("state")
        if state in _TERMINAL_STATES:
            if not _terminal_proof_valid(item, state, slot, now_epoch):
                return {"action": "RECONCILE", "leg_index": index,
                        "reason": "terminal_proof_missing", "budget_breached": overdue}
            confirmed_at = item["terminal_confirmed_at_epoch"]
            if confirmed_at > slot["terminal_confirm_by_epoch"]:
                return {"action": "BLOCK_LATE_TERMINAL", "leg_index": index,
                        "reason": "leg_confirmation_exceeded_slot", "budget_breached": overdue}
            continue
        if state in _OPEN_STATES and not _identity(item.get("broker_order_no")):
            return {"action": "RECONCILE", "leg_index": index,
                    "reason": "broker_order_identity_missing", "budget_breached": overdue}
        if state == "CANCEL_REQUESTED":
            return {"action": "RECONCILE", "leg_index": index,
                    "reason": "cancel_terminal_pending", "budget_breached": overdue}
        if state in {"OPEN", "PARTIAL"}:
            if now_epoch >= slot["cancel_request_by_epoch"]:
                return {"action": "CANCEL", "leg_index": index,
                        "reason": "leg_cancel_request_deadline", "budget_breached": overdue}
            return {"action": "WAIT", "leg_index": index,
                    "until_epoch": slot["cancel_request_by_epoch"]}
        if state != "NOT_SUBMITTED":
            return {"action": "BLOCK_INVALID_LEG_STATE", "leg_index": index}
        if now_epoch < slot["slot_start_epoch"]:
            return {"action": "WAIT", "leg_index": index,
                    "until_epoch": slot["slot_start_epoch"]}
        if now_epoch >= slot["cancel_request_by_epoch"]:
            return {"action": "SKIP_LEG", "leg_index": index,
                    "reason": "insufficient_time_for_cancel_confirmation",
                    "budget_breached": overdue}
        return {"action": "SUBMIT", "leg_index": index,
                "submit_before_epoch": slot["cancel_request_by_epoch"]}
    return {"action": "DONE", "budget_breached": overdue}
