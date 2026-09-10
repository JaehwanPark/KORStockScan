"""Preserve the morning owner's existing NXT-zero-fill -> SOR entry contract.

This is a handoff to its existing guarded BUY loop, not an adaptive entry rule.
No default service, new price/quantity rule or broker implementation lives here.
"""

from copy import deepcopy
from dataclasses import asdict
from datetime import datetime

from src.trading.config.machine_adaptive_exit_policy import canonical_sha256
from .episode_pending_buy import (
    KEY as BUY_KEY,
    EpisodePendingBuyServices,
    validate_projection,
)

KEY = "adaptive_sor_fallback"
PLAN_KEY = "adaptive_sor_fallback_submit"
SCHEMA = "episode_adaptive_sor_fallback_v1"


def _seal(value):
    value["canonical_sha256"] = canonical_sha256(value)
    return value


def prepare(machine, now, leg):
    """Called inside the pending-BUY atomic projection; contains no broker I/O."""
    _policy_payload(machine)
    if (
        leg.get("route") != "NXT"
        or leg.get("status") != "NO_FILL"
        or leg.get("buy_filled_qty") != 0
        or leg.get("position_qty") != 0
        or KEY in leg
        or PLAN_KEY in leg
    ):
        raise ValueError("adaptive_sor_original_zero_fill_required")
    validate_projection(machine, leg)
    source = deepcopy(leg)
    receipt = source["adaptive_sibling_full_buy_receipt"]
    if not receipt.get("cancel_order"):
        raise ValueError("adaptive_sor_exact_cancel_child_required")
    handoff = _seal(
        {
            "schema": SCHEMA,
            "source_leg": source,
            "source_leg_sha256": canonical_sha256(source),
            "policy": _policy_payload(machine),
            "policy_sha256": _policy_hash(machine),
            "prepared_at": now.isoformat(),
            "successor_attempt": source["buy_submit_attempt_count"] + 1,
        }
    )
    _authorize(machine, leg, handoff, "PREPARE_SOR_FALLBACK")
    leg[KEY] = handoff
    leg.pop(BUY_KEY)
    leg.pop("adaptive_sibling_full_buy_receipt")
    leg["buy_owner_registry_intent_id"] = ""
    # This original owner method records/saves the transition. No second entry
    # recipe is copied here and its next opening/confirmation remains required.
    machine._move_to_sor(now, leg)


def _policy_payload(machine):
    # The morning package exports its machine from __init__; import only after
    # that package and this integration module have finished loading.
    from src.trading.samsung_morning_one_share.policy import MorningOneSharePolicy

    if not isinstance(machine.policy, MorningOneSharePolicy):
        raise ValueError("adaptive_sor_original_morning_policy_required")
    # dataclass windows include time values, so use their canonical strings.
    policy = asdict(machine.policy)
    for route in ("nxt", "sor"):
        policy[route]["open_time"] = policy[route]["open_time"].isoformat()
        policy[route]["deadline"] = policy[route]["deadline"].isoformat()
    return policy


def _policy_hash(machine):
    return canonical_sha256(_policy_payload(machine))


def _authorize(machine, leg, handoff, action):
    services = getattr(machine.adaptive_exit_services, "pending_buy", None)
    state = machine._state
    state_hash = canonical_sha256(state)
    before = canonical_sha256(leg)
    request = {
        "schema": SCHEMA,
        "action": action,
        "handoff_sha256": handoff["canonical_sha256"],
        "source_leg_sha256": handoff["source_leg_sha256"],
        "policy_sha256": handoff["policy_sha256"],
        "leg": deepcopy(leg),
        "signal_features": deepcopy(machine._state.get("signal_features", {})),
    }
    if (
        not isinstance(services, EpisodePendingBuyServices)
        or not machine._adaptive_authority_current()
        or not any(row is leg for row in machine._state["legs"])
        or services.authorize(request) is not True
        or getattr(machine.adaptive_exit_services, "pending_buy", None) is not services
        or not machine._adaptive_authority_current()
        or not any(row is leg for row in machine._state["legs"])
        or machine._state is not state
        or canonical_sha256(machine._state) != state_hash
        or canonical_sha256(leg) != before
        or _policy_hash(machine) != handoff["policy_sha256"]
    ):
        raise PermissionError("adaptive_sor_original_owner_authority_required")


def validate(machine, now, leg):
    handoff = leg.get(KEY)
    if (
        not isinstance(handoff, dict)
        or handoff.get("schema") != SCHEMA
        or handoff.get("canonical_sha256") != canonical_sha256(handoff)
        or not isinstance(handoff.get("source_leg"), dict)
        or handoff.get("source_leg_sha256") != canonical_sha256(handoff["source_leg"])
        or handoff.get("policy_sha256") != _policy_hash(machine)
        or handoff.get("policy") != _policy_payload(machine)
    ):
        raise ValueError("adaptive_sor_handoff_binding_invalid")
    source = handoff["source_leg"]
    prepared = datetime.fromisoformat(handoff.get("prepared_at", ""))
    receipt = source.get("adaptive_sibling_full_buy_receipt")
    if (
        source.get("route") != "NXT"
        or source.get("status") != "NO_FILL"
        or source.get("buy_filled_qty") != 0
        or source.get("position_qty") != 0
        or source.get("buy_order_date") != now.date().isoformat()
        or source.get("buy_order_date") != machine._state.get("trade_date")
        or prepared.tzinfo is None
        or prepared.utcoffset() != now.utcoffset()
        or prepared.date() != now.date()
        or prepared > now
        or not isinstance(source.get(BUY_KEY), dict)
        or not isinstance(receipt, dict)
        or not receipt.get("cancel_order")
        or leg.get("route") != "SOR"
        or any(
            leg.get(k) != source.get(k) for k in ("leg_id", "price_role", "quantity")
        )
        or type(source.get("buy_submit_attempt_count")) is not int
        or type(handoff.get("successor_attempt")) is not int
        or handoff.get("successor_attempt") != source["buy_submit_attempt_count"] + 1
    ):
        raise ValueError("adaptive_sor_handoff_original_leg_invalid")
    validate_projection(machine, source)
    attempt = leg.get("buy_submit_attempt_count")
    if type(attempt) is not int or attempt not in {
        source["buy_submit_attempt_count"],
        handoff["successor_attempt"],
    }:
        raise ValueError("adaptive_sor_successor_attempt_invalid")
    if leg.get("status") == "PLANNED" and (
        attempt != source["buy_submit_attempt_count"]
        or PLAN_KEY in leg
        or leg.get("buy_order_no")
        or leg.get("buy_owner_registry_intent_id")
    ):
        raise ValueError("adaptive_sor_spent_submit_requires_recovery")
    if attempt == handoff["successor_attempt"]:
        plan = leg.get(PLAN_KEY)
        if (
            not isinstance(plan, dict)
            or plan.get("schema") != "episode_adaptive_sor_submit_v1"
            or plan.get("canonical_sha256") != canonical_sha256(plan)
            or plan.get("handoff_sha256") != handoff["canonical_sha256"]
            or plan.get("price") != leg.get("entry_price")
            or plan.get("quantity") != leg.get("quantity")
            or type(plan.get("quantity")) is not int
            or plan.get("attempt") != attempt
            or plan.get("route") != "SOR"
            or type(plan.get("price")) is not int
            or plan["price"] <= 0
        ):
            raise ValueError("adaptive_sor_submit_plan_invalid")
        submitted = datetime.fromisoformat(plan.get("at", ""))
        if (
            submitted.tzinfo is None
            or submitted.utcoffset() != now.utcoffset()
            or submitted.date() != now.date()
            or not prepared <= submitted <= now
            or not machine.policy.sor.open_time
            <= submitted.time()
            < machine.policy.sor.deadline
        ):
            raise ValueError("adaptive_sor_submit_time_invalid")
        context = machine._episode_owner_context(
            leg=leg, action="NEW", ordinal=f"BUY:SOR:{attempt}"
        )
        row = machine.owner_registry.intent_for_client(context=context)
        if not row or (
            row.get("intent_id") != leg.get("buy_owner_registry_intent_id")
            or row.get("route") != "SOR"
            or row.get("action") != "NEW"
            or row.get("side") != "BUY"
            or row.get("quantity") != leg["quantity"]
            or row.get("symbol") != machine.policy.symbol
            or row.get("order_date") != now.date().isoformat()
            or (
                leg.get("buy_order_no")
                and row.get("broker_order_no") != leg["buy_order_no"]
            )
        ):
            raise ValueError("adaptive_sor_successor_registry_required")
    return handoff


def step_planned(machine, now):
    """Validate every historic handoff, then reuse only its original entry loop."""
    legs = [leg for leg in machine._state["legs"] if KEY in leg]
    for leg in legs:
        handoff = validate(machine, now, leg)
        _authorize(machine, leg, handoff, "RESUME_SOR_FALLBACK")
    planned = [leg for leg in legs if leg.get("status") == "PLANNED"]
    if planned and now.time() >= machine.policy.sor.open_time:
        if any(
            leg.get("status") == "PLANNED" and KEY not in leg
            for leg in machine._state["legs"]
        ):
            raise ValueError("adaptive_sor_unrelated_planned_entry_forbidden")
        machine._submit_planned_buys(now)
        if machine._state.get("status") != "BLOCKED":
            machine._sync_aggregate()
        # Existing BUY_SUBMITTING/registry reservations must survive a write
        # failure. Never roll the whole broker transaction back to PLANNED.
        machine._save()
    return {leg["leg_id"] for leg in legs}


def before_buy(machine, now, leg, *, reserved=False):
    """Repeat the original owner's authority immediately around reservation."""
    if not any("adaptive_exit_session" in row for row in machine._state["legs"]):
        return
    handoff = validate(machine, now, leg)
    _authorize(machine, leg, handoff, "SUBMIT_SOR_FALLBACK")
    if not machine.policy.sor.open_time <= now.time() < machine.policy.sor.deadline:
        raise ValueError("adaptive_sor_original_entry_window_closed")
    attempt = handoff["successor_attempt"]
    context = machine._episode_owner_context(
        leg=leg, action="NEW", ordinal=f"BUY:SOR:{attempt}"
    )
    row = machine.owner_registry.intent_for_client(context=context)
    if reserved:
        if (
            leg.get("status") != "BUY_SUBMITTING"
            or not isinstance(row, dict)
            or row.get("state") != "INTENT_RESERVED"
        ):
            raise ValueError("adaptive_sor_reserved_submit_required")
        stored = machine._load_state()
        if (
            next((r for r in stored["legs"] if r["leg_id"] == leg["leg_id"]), None)
            != leg
        ):
            raise ValueError("adaptive_sor_durable_submit_required")
    else:
        if row is not None or leg.get("status") != "PLANNED" or PLAN_KEY in leg:
            raise ValueError("adaptive_sor_submit_slot_already_spent")
        leg[PLAN_KEY] = _seal(
            {
                "schema": "episode_adaptive_sor_submit_v1",
                "handoff_sha256": handoff["canonical_sha256"],
                "attempt": attempt,
                "route": "SOR",
                "quantity": leg["quantity"],
                "price": leg["entry_price"],
                "at": now.isoformat(),
            }
        )
