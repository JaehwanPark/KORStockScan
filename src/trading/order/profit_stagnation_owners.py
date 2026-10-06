"""Small adapters for the two ORIGINAL machine journals and service locks.

No independent process, enrollment service, market subscription or entry
policy. Old adaptive sessions remain exclusive. Existing EXIT has priority.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import os

from src.engine.risk.manual_control_exclusion import (
    _env_codes,
    _file_exclusion_snapshot,
    independent_machine_ownership_source,
)
from src.trading.config.machine_profit_stagnation_policy import (
    FAMILY,
    PATH_ENV,
    HASH_ENV,
    load_policy,
)
from src.trading.market.profit_stagnation_quote import executable_quote
from src.trading.order.adaptive_exit.reducer import OrderKey
from src.trading.order.owner_custody_registry import OwnerRegistryError
from src.trading.order.profit_stagnation_exit import (
    KEY,
    evaluate_candidate,
    initial_state,
    order_history,
    policy_digest,
    step_exit,
)

OBSERVATION_KEY = "profit_stagnation_observation"






def _original_target_fill_facts(registry, order, filled, *, owner_id, symbol):
    """Return exact registry-backed price/time for the original target fill.

    The profit-exit reducer intentionally tracks quantities only.  Shared WS
    reconciliation can already have persisted the exact cumulative fill amount
    in the immutable owner registry, so project it into the original episode
    journal without inventing a target-price proxy.  Multi-price fills whose
    exact average is not an integer remain unresolved.
    """
    if type(filled) is not int or filled <= 0:
        return None
    row = registry.order_owner(
        order_date=order.trading_date, broker_order_no=order.order_no
    )
    if (
        not row
        or row.get("side") != "SELL"
        or row.get("action") != "NEW"
        or row.get("broker_order_no") != order.order_no
        or row.get("order_date") != order.trading_date
        or row.get("owner_type") != "episode"
        or row.get("owner_id") != owner_id
        or row.get("position_id") != owner_id
        or row.get("symbol") != symbol
        or row.get("quantity") != filled
        or row.get("filled_qty") != filled
        or type(row.get("fill_amount")) is not int
        or row["fill_amount"] <= 0
        or row["fill_amount"] % filled
    ):
        return None
    observed_at = row.get("fill_observed_at_kst")
    try:
        observed = datetime.fromisoformat(observed_at)
    except (TypeError, ValueError):
        return None
    if observed.tzinfo is None or observed.date().isoformat() != order.trading_date:
        return None
    return row["fill_amount"] // filled, observed.isoformat()




def policy_for(now, owner, entered_at, diagnostic=None):
    if not os.getenv(PATH_ENV) and not os.getenv(HASH_ENV):
        if diagnostic is not None:
            diagnostic["profit_exit_policy_status"] = "off_no_policy_pin"
        return None
    try:
        selected = load_policy(
            now=now, owner=owner, entered_at=datetime.fromisoformat(entered_at)
        )
        if diagnostic is not None:
            diagnostic["profit_exit_policy_status"] = (
                "selected" if selected else "inactive_or_position_outside_scope"
            )
        return selected
    except (ValueError, TypeError, KeyError, OSError, AttributeError) as exc:
        if diagnostic is not None:
            diagnostic["profit_exit_policy_status"] = (
                "invalid_or_missing_evidence:" + type(exc).__name__
            )
        return None


def _save_initial(owner):
    try:
        owner._save()
    except BaseException:
        owner._profit_exit_reload_required = True
        raise


def guard(owner, *, symbol, owner_type, now):
    """Write gate separate from entry eligibility and independent of research."""
    held = getattr(owner, "profit_exit_lock_held", lambda: False)
    kinds, error = _file_exclusion_snapshot(symbol)
    return bool(
        owner_type == "episode"
        and held() is True
        and not getattr(owner, "_profit_exit_reload_required", False)
        and owner.live_enabled
        and not error
        and symbol not in _env_codes()
        and not (kinds - {"machine_owner_scope", "legacy_machine_owner_scope"})
        and independent_machine_ownership_source(
            symbol, owner=owner_type, target_date=now.date(), new_entry=False
        )
    )


def _drive(owner, state, *, adapter, symbol, now, authorized, write_guard, persist):
    def candidate_current():
        current = policy_for(
            datetime.fromtimestamp(adapter.now_ms() / 1000, now.tzinfo),
            adapter.context.owner_type,
            state["policy"]["valid_from"],
        )
        return bool(
            authorized
            and current
            and current == (state["policy"], state["policy_hash"])
        )

    def durable(payload):
        # A failed fsync/rename must not be treated as an ordinary source gap.
        try:
            if symbol == "005930":
                from src.engine.monitoring.machine_entry_confirmation_study import (
                    instrumentation_call,
                    record_programme_transition,
                )

                instrumentation_call(
                    owner._state,
                    record_programme_transition,
                    payload,
                    clock=adapter.now_ms,
                )
            persist(payload)
        except BaseException:
            owner._profit_exit_reload_required = True
            raise

    route = adapter.new_route(adapter._owned(OrderKey(**state["current"]))["route"])
    try:
        step_exit(
            state,
            adapter=adapter,
            now=now.timestamp(),
            quote_loader=lambda qty: executable_quote(
                symbol=symbol,
                route=route,
                quantity=qty,
                now=datetime.fromtimestamp(adapter.now_ms() / 1000, now.tzinfo),
            ),
            persist=durable,
            owner_guard=write_guard,
            new_candidate_authorized=candidate_current,
        )
    except (
        ValueError,
        TypeError,
        KeyError,
        PermissionError,
        OwnerRegistryError,
    ) as exc:
        if getattr(owner, "_profit_exit_reload_required", False):
            raise
        # Keep the durable pre-write phase for restart recovery. Never replace
        # it with the stale caller snapshot after an interrupted broker write.
        owner._state["profit_exit_last_error"] = type(exc).__name__
        owner._save()


def episode_leg(machine, leg, now):
    """True means normal target reconciliation must not also touch this leg."""
    from src.trading.order.target_ratchet import episode

    if episode(machine, leg, now):
        return True
    if getattr(machine, "_profit_exit_reload_required", False):
        raise OSError("profit_exit_owner_reload_required")
    prior = leg.get(KEY)
    if KEY in leg and (not isinstance(prior, dict) or not prior):
        raise ValueError("profit_exit_leg_claim_invalid")
    selected = policy_for(
        now,
        "episode",
        (machine._state.get("signal_features") or {}).get("signal_decision_at", ""),
        diagnostic=machine._state,
    )
    if getattr(machine, "profit_exit_lock_held", lambda: False)() is not True:
        return prior is not None
    if prior and prior.get("phase") == "FLAT":
        return True
    if prior is None and (not selected or leg.get("status") != "TARGET_OPEN"):
        return False
    if any(
        item.get("status")
        in {
            "PLANNED",
            "BUY_SUBMITTING",
            "BUY_OPEN",
            "BUY_CANCEL_SUBMITTING",
            "BUY_CANCEL_PENDING",
            "POSITION_OPEN",
            "TARGET_SUBMITTING",
        }
        for item in machine._state.get("legs", [])
    ):
        return prior is not None
    symbol = machine.policy.symbol

    def allowed():
        return bool(
            guard(machine, symbol=symbol, owner_type="episode", now=now)
            and machine._state.get("status") != "BLOCKED"
            and not machine._state.get("owner_registry_reconciliation_required")
            and not any(
                v
                for item in machine._state["legs"]
                for k, v in item.items()
                if k.endswith("owner_registry_reconciliation_required")
            )
        )

    if prior is None and not allowed():
        return False
    policy, pin = (prior["policy"], prior["policy_hash"]) if prior else selected
    context = machine._episode_owner_context(leg=leg, action="profit_exit", ordinal=1)
    if prior and (
        prior["root"]
        != OrderKey(leg["target_order_date"], leg["target_order_no"]).__dict__
        or prior["original_target"] != leg["target_price"]
        or prior["entry_price"] != leg["fill_price"]
        or prior["quantity"] != leg["target_quantity"]
        or prior["identity"] != f"{context.position_id}:{leg['leg_id']}:{pin}"
    ):
        raise ValueError("profit_exit_original_leg_binding_changed")
    adapter = machine.gateway.adaptive_exit_adapter(
        registry=machine.owner_registry,
        context=context,
        policy_hash=pin,
        write_guard=lambda _: False,
        authority_policy_id=FAMILY,
    )
    if prior is None:
        prior = initial_state(
            policy=policy,
            policy_hash=pin,
            target=OrderKey(leg["target_order_date"], leg["target_order_no"]),
            quantity=leg["target_quantity"],
            filled=leg["target_filled_qty"],
            original_target=leg["target_price"],
            entry_price=leg["fill_price"],
            identity=f"{context.position_id}:{leg['leg_id']}:{pin}",
        )
        leg[KEY] = prior
        _save_initial(machine)

    def persist(payload):
        leg[KEY] = payload
        records = order_history(payload)
        leg["target_filled_qty"] = records[0]["filled"]
        original = records[0]["order"]
        facts = _original_target_fill_facts(
            adapter.registry,
            OrderKey(original["trading_date"], original["order_no"]),
            records[0]["filled"],
            owner_id=context.owner_id,
            symbol=symbol,
        )
        if facts is not None:
            leg["target_fill_price"], leg["target_filled_at"] = facts
        leg["profit_stagnation_filled_qty"] = sum(r["filled"] for r in records[1:])
        leg["position_qty"] = leg["buy_filled_qty"] - sum(r["filled"] for r in records)
        leg["status"] = "COMPLETE" if leg["position_qty"] == 0 else "TARGET_OPEN"
        for row in records:
            machine._own_order(row["order"]["order_no"])
        machine._sync_aggregate()
        machine._save()

    _drive(
        machine,
        prior,
        adapter=adapter,
        symbol=symbol,
        now=now,
        authorized=bool(selected and selected[1] == pin),
        write_guard=allowed,
        persist=persist,
    )
    return True
