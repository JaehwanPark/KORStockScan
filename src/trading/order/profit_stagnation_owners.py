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


def active_widget(state):
    return KEY in state


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
        held() is True
        and not getattr(owner, "_profit_exit_reload_required", False)
        and (owner.enabled if owner_type == "widget_auto_trade" else owner.live_enabled)
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


def widget_symbol(trader, state, now):
    """Keep original orders immutable; project exact successor fills separately.

    The caller evaluates its original final EXIT before invoking this hook.
    Revocation/EXIT restores protection and releases the original owner once
    no supplementary SELL or unconfirmed cancellation remains.
    """
    if getattr(trader, "_profit_exit_reload_required", False):
        raise OSError("profit_exit_owner_reload_required")
    orders = state.get("orders", [])
    signal = state.get("entry_signal_id")
    buys = [
        o
        for o in orders
        if o.get("side") == "BUY"
        and (o.get("signal_id") == signal or o.get("parent_entry_signal_id") == signal)
    ]
    entered = min((o.get("intent_created_at", "") for o in buys), default="")
    selected = policy_for(now, "widget_auto_trade", entered, diagnostic=trader._state)
    sessions = state.get(KEY, {})
    if KEY in state and (not isinstance(sessions, dict) or not sessions):
        raise ValueError("profit_exit_widget_claim_invalid")
    if getattr(trader, "profit_exit_lock_held", lambda: False)() is not True:
        return bool(sessions)

    def stop_observing():
        if state.pop(OBSERVATION_KEY, None) is not None:
            _save_initial(trader)
        return False

    if not sessions and not selected:
        return stop_observing()
    symbol = state["code"]
    safe_buys = bool(buys) and all(
        o.get("status") in {"FILLED", "PARTIAL_CANCELED"}
        and o.get("broker_accepted") is True
        and type(o.get("fill_price")) in {int, float}
        and o["fill_price"] > 0
        and type(o.get("filled_qty")) is int
        and 0 < o["filled_qty"] <= o.get("requested_qty", 0)
        for o in buys
    )

    def allowed():
        return bool(
            guard(trader, symbol=symbol, owner_type="widget_auto_trade", now=now)
            and safe_buys
            and not state.get("owner_registry_reconciliation_required")
            and not any(
                v
                for o in orders
                for k, v in o.items()
                if k.endswith("owner_registry_reconciliation_required")
            )
        )

    if not sessions and (not allowed() or state.get("exit_requested")):
        return stop_observing()
    if not sessions:
        policy, pin = selected
        quantity = sum(o["filled_qty"] for o in buys)
        basis = sum(o["fill_price"] * o["filled_qty"] for o in buys) / quantity
        targets = [
            o
            for o in orders
            if o.get("side") == "SELL"
            and o.get("order_role") == "TAKE_PROFIT_SELL"
            and o.get("status") == "SUBMITTED"
            and o.get("parent_entry_signal_id") == signal
            and o.get("broker_accepted") is True
            and not o.get("profit_stagnation_disabled")
        ]
        # Whole currently protected inventory, no pending BUY or unknown SELL.
        if not targets or any(
            o.get("side") == "SELL"
            and o not in targets
            and o.get("status")
            not in {"FILLED", "CANCELED", "PARTIAL_CANCELED", "TERMINAL_UNFILLED"}
            for o in orders
        ):
            return stop_observing()
        if any(
            type(o.get("limit_price")) is not int or o["limit_price"] <= basis
            for o in targets
        ):
            return stop_observing()  # No supplement to a lower incumbent target.
        if sum(
            o["requested_qty"] - o["filled_qty"] for o in targets
        ) != trader._open_qty(state):
            return stop_observing()
        for order in targets:
            key = f"{order['order_date']}:{order['order_no']}"
            sessions[key] = initial_state(
                policy=policy,
                policy_hash=pin,
                target=OrderKey(order["order_date"], order["order_no"]),
                quantity=order["requested_qty"],
                filled=order["filled_qty"],
                original_target=order["limit_price"],
                entry_price=basis,
                identity=f"{order['owner_position_id']}:{key}:{pin}",
            )
            # Observation never owns orders or suppresses the original BUY
            # path. Rebuild its basis/quantity from the original owner each
            # cycle; only an unchanged binding may retain elapsed time.
            observations = state.get(OBSERVATION_KEY)
            old = observations.get(key, {}) if isinstance(observations, dict) else {}
            old = old if isinstance(old, dict) else {}
            if old:
                if old.get("policy_content_sha256") != policy_digest(old.get("policy")):
                    trader._state["profit_exit_last_error"] = "ValueError"
                    return stop_observing()
                if all(
                    old.get(field) == sessions[key][field]
                    for field in (
                        "identity",
                        "entry_price",
                        "quantity",
                        "current_filled",
                        "original_target",
                        "policy_hash",
                    )
                ):
                    sessions[key]["decision"] = deepcopy(old.get("decision", {}))
    for key, session in list(sessions.items()):
        originals = [
            o
            for o in orders
            if o.get("order_date") == session["root"]["trading_date"]
            and o.get("order_no") == session["root"]["order_no"]
        ]
        if len(originals) != 1:
            raise ValueError("profit_exit_original_widget_order_not_unique")
        original = originals[0]
        if (
            key != f"{original['order_date']}:{original['order_no']}"
            or session["quantity"] != original["requested_qty"]
            or session["original_target"] != original["limit_price"]
            or session["identity"]
            != f"{original['owner_position_id']}:{key}:{session['policy_hash']}"
            or original.get("parent_entry_signal_id") != signal
        ):
            raise ValueError("profit_exit_original_widget_binding_changed")
        context = trader._owner_context_from_order(original)
        adapter = trader.gateway.adaptive_exit_adapter(
            registry=trader.owner_registry,
            context=context,
            code=symbol,
            policy_hash=session["policy_hash"],
            write_guard=lambda _: False,
            authority_policy_id=FAMILY,
        )

        if KEY not in state:
            try:
                route = adapter.new_route(
                    adapter._owned(OrderKey(**session["root"]))["route"]
                )
                source = executable_quote(
                    symbol=symbol,
                    route=route,
                    quantity=session["current_quantity"] - session["current_filled"],
                    now=datetime.fromtimestamp(adapter.now_ms() / 1000, now.tzinfo),
                )
                result, window = evaluate_candidate(
                    session,
                    source,
                    now=adapter.now_ms() / 1000,
                    previous=session["decision"],
                )
                mature = bool(
                    result.get("should_exit")
                    and source["executable_bid"] < session["original_target"]
                )
                if source["executable_bid"] >= session["original_target"]:
                    window = {}
            except (
                ValueError,
                TypeError,
                KeyError,
                OSError,
                AttributeError,
                OwnerRegistryError,
            ):
                mature, window = False, {}
            if not mature:
                session["decision"] = window
                state[OBSERVATION_KEY] = sessions
                _save_initial(trader)
                continue

        def persist(payload):
            sessions[key] = payload
            if KEY not in state and payload["phase"] == "TARGET":
                state[OBSERVATION_KEY] = sessions
            else:
                # Persist the exclusive claim before the first cancel write.
                state[KEY] = sessions
                state.pop(OBSERVATION_KEY, None)
            records = order_history(payload)
            for index, record in enumerate(records):
                order_key = OrderKey(**record["order"])
                matches = [
                    o
                    for o in orders
                    if o.get("order_date") == order_key.trading_date
                    and o.get("order_no") == order_key.order_no
                ]
                if len(matches) > 1:
                    raise ValueError("profit_exit_duplicate_widget_order")
                if matches:
                    row = matches[0]
                else:
                    owned = adapter._owned(order_key)
                    row = deepcopy(original)
                    row.update(
                        order_date=order_key.trading_date,
                        order_no=order_key.order_no,
                        requested_qty=record["quantity"],
                        owner_registry_intent_id=owned["intent_id"],
                        owner_client_intent_id=owned["client_intent_id"],
                        limit_price=payload["next_price"],
                        intent_created_at=now.isoformat(),
                        profit_stagnation_root=payload["root"],
                        fill_price=None,
                    )
                    # Never inherit cancellation provenance from the root.
                    for field in list(row):
                        if "cancel" in field:
                            row.pop(field)
                    orders.append(row)
                filled = record["filled"]
                if row.get("filled_qty") != filled:
                    row.update(
                        fill_price=None,
                        fill_amount_krw=None,
                        commission_krw=None,
                        tax_krw=None,
                    )
                terminal = index < len(records) - 1 or payload["phase"] in {
                    "READY",
                    "SUBMITTING",
                    "FLAT",
                }
                row.update(
                    filled_qty=filled,
                    remaining_qty=0 if terminal else record["quantity"] - filled,
                    status=(
                        "FILLED"
                        if filled == record["quantity"]
                        else (
                            ("PARTIAL_CANCELED" if filled else "CANCELED")
                            if terminal
                            else "SUBMITTED"
                        )
                    ),
                )
            trader._save()

        authorized = bool(
            selected
            and selected[1] == session["policy_hash"]
            and not state.get("exit_requested")
        )
        _drive(
            trader,
            session,
            adapter=adapter,
            symbol=symbol,
            now=now,
            authorized=authorized,
            write_guard=allowed,
            persist=persist,
        )
    if KEY not in state:
        return False
    if all(
        s["phase"] == "TARGET"
        and (
            s.get("disabled_for_target")
            or (not s.get("orders") and not s.get("cancel_id"))
        )
        for s in sessions.values()
    ):
        # No transition remains: return ordinary targets to their owner.
        # Disabled restored/rejected targets must not be enrolled repeatedly;
        # untouched targets retain read-only observations, not an entry lock.
        for s in sessions.values():
            if s.get("disabled_for_target"):
                for order in orders:
                    if (order.get("order_date"), order.get("order_no")) == (
                        s["current"]["trading_date"],
                        s["current"]["order_no"],
                    ):
                        order["profit_stagnation_disabled"] = True
        if any(s.get("disabled_for_target") for s in sessions.values()):
            state.setdefault("profit_stagnation_history", []).append(deepcopy(sessions))
        observations = {
            k: s for k, s in sessions.items() if not s.get("disabled_for_target")
        }
        if observations:
            state[OBSERVATION_KEY] = observations
        else:
            state.pop(OBSERVATION_KEY, None)
        state.pop(KEY)
        _save_initial(trader)
        return False
    # Hand back only a confirmed original-price order, never an unprotected
    # residual or an ambiguous pending write. Original EXIT then owns the SELL.
    if all(
        s["phase"] == "FLAT"
        or (state.get("exit_requested") and s["phase"] in {"TARGET", "READY"})
        for s in sessions.values()
    ):
        state.setdefault("profit_stagnation_history", []).append(deepcopy(sessions))
        state.pop(KEY)
        trader._save()
        return False
    return True
