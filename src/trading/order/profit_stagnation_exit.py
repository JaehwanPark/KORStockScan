"""Single-target supplement driven by the ORIGINAL owner's locked loop.

No entry, trailing, loss stop, clock service, enrollment framework or worker.
The registered adapter remains the sole broker transport and quantity guard.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import hashlib
import json

from src.trading.config.machine_profit_stagnation_policy import FAMILY, validate_policy
from src.trading.order.adaptive_exit.reducer import OrderKey
from src.trading.order.profit_stagnation import positive_net_stagnation

KEY = "profit_stagnation_exit"


def policy_digest(policy):
    return hashlib.sha256(
        json.dumps(policy, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def initial_state(
    *,
    policy,
    policy_hash,
    target: OrderKey,
    quantity: int,
    original_target: int,
    entry_price: float,
    identity: str,
    filled: int = 0,
) -> dict:
    validate_policy(policy)
    if (
        type(quantity) is not int
        or quantity <= 0
        or original_target <= entry_price
        or type(filled) is not int
        or not 0 <= filled <= quantity
    ):
        raise ValueError("profit_exit_original_position_invalid")
    return dict(
        policy=deepcopy(policy),
        policy_hash=policy_hash,
        policy_content_sha256=policy_digest(policy),
        identity=identity,
        root=target.__dict__,
        current=target.__dict__,
        quantity=quantity,
        original_target=original_target,
        entry_price=entry_price,
        phase="TARGET",
        orders=[],
        current_quantity=quantity,
        current_filled=filled,
        settled_filled=0,
        decision={},
        mode="target",
        cancel_id=None,
        cancel_order=None,
        next_price=None,
        submitted_at=None,
        realized_pnl=None,
        realized_pnl_status="exact_cost_unreconciled",
    )


def order_history(state):
    """Exact order quantities, never cost/PnL proxies."""
    return state["orders"] + [
        dict(
            order=state["current"],
            quantity=state["current_quantity"],
            filled=state["current_filled"],
        )
    ]


def evaluate_candidate(state, source, *, now, previous):
    """Shared read-only observation and pre-write calculation."""
    args = dict(source)
    epoch = args.pop("source_epoch")
    return positive_net_stagnation(
        identity=state["identity"] + ":" + epoch,
        now=now,
        entry_price=state["entry_price"],
        quantity=state["current_quantity"] - state["current_filled"],
        previous=previous,
        **args,
        **{
            k: state["policy"][k]
            for k in (
                "round_trip_cost_pct",
                "slippage_bps",
                "min_sec",
                "max_profit_move",
                "max_peak_improve",
                "max_observation_gap_sec",
            )
        },
    )


def step_exit(
    state: dict,
    *,
    adapter,
    now: float,
    quote_loader,
    persist,
    owner_guard,
    new_candidate_authorized: bool,
) -> dict:
    """Persist before effects; all quotes are reloaded at each write guard.

    ``persist`` atomically saves the original owner's entire journal. It must
    raise on failure; callers must reload after any ambiguous disk failure.
    ``owner_guard`` is supplied by the original owner, never by the policy.
    Original and successor order histories are retained separately from PnL.
    """
    s = deepcopy(state)
    policy = s["policy"]
    validate_policy(policy)
    if s.get("policy_content_sha256") != policy_digest(policy):
        raise ValueError("profit_exit_frozen_policy_changed")

    def candidate_authorized():
        return (
            new_candidate_authorized()
            if callable(new_candidate_authorized)
            else new_candidate_authorized
        ) is True

    current = OrderKey(**s["current"])
    if adapter.authority_policy_id != FAMILY or adapter.policy_hash != s["policy_hash"]:
        raise ValueError("profit_exit_adapter_binding_invalid")
    root = adapter._owned(OrderKey(**s["root"]))
    if root["quantity"] != s["quantity"]:
        raise ValueError("profit_exit_root_quantity_changed")
    history = order_history(s)
    previous_left = s["quantity"]
    seen = set()
    for record in history:
        key = OrderKey(**record["order"])
        owned = adapter._owned(key)
        if (
            key in seen
            or type(record["filled"]) is not int
            or not 0 <= record["filled"] <= record["quantity"]
            or record["quantity"] != previous_left
            or owned["quantity"] != record["quantity"]
        ):
            raise ValueError("profit_exit_order_chain_invalid")
        seen.add(key)
        previous_left -= record["filled"]
    if (
        history[0]["order"] != s["root"]
        or sum(r["filled"] for r in s["orders"]) != s["settled_filled"]
    ):
        raise ValueError("profit_exit_root_or_settlement_changed")

    def save(**updates):
        s.update(updates)
        persist(deepcopy(s))

    def wait(reason):
        save(last_result=reason)
        return s

    def quote():
        return quote_loader(s["current_quantity"] - s["current_filled"])

    def evaluate(source, previous):
        return evaluate_candidate(
            s,
            source,
            now=adapter.now_ms() / 1000,
            previous=previous,
        )

    def write_guard(request):
        if owner_guard() is not True or request.predecessor != current:
            return False
        if request.quantity != s["current_quantity"] - s["current_filled"]:
            return False
        if request.action == "CANCEL":
            if s["phase"] == "EXIT_CANCEL":
                return True
            try:
                source = quote()
                result, _ = evaluate(source, s["decision"])
                return bool(
                    s["phase"] == "CANCEL"
                    and candidate_authorized()
                    and source["executable_bid"] < s["original_target"]
                    and result.get("should_exit")
                )
            except (ValueError, TypeError, KeyError, OSError, AttributeError):
                return False
        if s["phase"] != "SUBMITTING" or request.limit_price != s["next_price"]:
            return False
        if s["next_mode"] == "target":
            return request.limit_price == s["original_target"]
        if not candidate_authorized():
            return False
        try:
            source = quote()
            # The candidate is priced at the submitted limit, not a better
            # newly observed quote. Both must still cover positive net costs.
            source["executable_bid"] = min(
                source["executable_bid"], request.limit_price
            )
            result, _ = evaluate(source, None)
            return (
                result.get("net_return_pct", 0) > 0
                and request.limit_price <= source["executable_bid"]
                and request.limit_price == s["next_price"]
            )
        except (ValueError, TypeError, KeyError, OSError, AttributeError):
            return False

    adapter.write_guard = write_guard
    if s["phase"] in {"FLAT", "BLOCKED"}:
        return s
    # A persisted SUBMITTING state never permits a second blind submit.
    if s["phase"] == "SUBMITTING":
        found = adapter.recover_replacement(
            current, quantity=s["current_quantity"] - s["current_filled"]
        )
        if found is None:
            row = adapter.registry.intent_for_client(
                context=replace(
                    adapter.context,
                    client_intent_id=adapter._replacement_client_id(current),
                )
            )
            if row is None:
                save(
                    phase="READY",
                    force_restore=True,
                    last_result="unreserved_or_definitively_rejected_write_restore",
                )
                return s
            return wait("submission_reservation_requires_exact_recovery")
        if not found.source_ok:
            return wait("replacement_exact_receipt_pending:" + found.error)
        save(
            orders=s["orders"]
            + [
                dict(
                    order=s["current"],
                    quantity=s["current_quantity"],
                    filled=s["current_filled"],
                )
            ],
            settled_filled=s["settled_filled"] + s["current_filled"],
            current=found.order.__dict__,
            current_quantity=s["current_quantity"] - s["current_filled"],
            current_filled=found.filled_qty,
            phase="TARGET" if s["next_mode"] == "target" else "EXIT",
            mode=s["next_mode"],
            cancel_id=None,
            cancel_order=None,
            decision={},
            disabled_for_target=s["next_mode"] == "target",
        )
        return s
    proof = adapter.reconcile_owned_sell(current)
    if not proof.source_ok:
        return wait("exact_order_reconciliation_pending:" + proof.error)
    if not 0 <= s["current_filled"] <= proof.filled_qty <= s["current_quantity"]:
        return wait("order_fill_conservation_failed")
    if proof.filled_qty != s["current_filled"]:
        save(current_filled=proof.filled_qty, decision={})
    left = s["current_quantity"] - s["current_filled"]
    if left == 0:
        if s.get("cancel_id"):
            child = adapter.registry.intent_for_client(
                context=replace(adapter.context, client_intent_id=s["cancel_id"])
            )
            if child and child["state"] not in {"ORDER_TERMINAL", "INTENT_REJECTED"}:
                return wait("full_fill_cancel_child_terminal_evidence_required")
        save(
            phase="FLAT",
            last_result="all_owned_quantity_filled",
            terminal_receipt_sha256=proof.receipt_hash,
            terminal_observed_at_ms=proof.observed_at_ms,
        )
        return s
    if s["phase"] in {"CANCEL", "EXIT_CANCEL"}:
        context = replace(adapter.context, client_intent_id=s["cancel_id"])
        row = adapter.registry.intent_for_client(context=context)
        if row is None:
            if s["phase"] == "CANCEL" and not candidate_authorized():
                save(
                    phase="TARGET",
                    cancel_id=None,
                    decision={},
                    last_result="candidate_withdrawn_before_cancel",
                )
                return s
            if s["phase"] == "CANCEL":
                try:
                    source = quote()
                    result, window = evaluate(source, s["decision"])
                    still_candidate = bool(
                        result.get("should_exit")
                        and source["executable_bid"] < s["original_target"]
                    )
                except (ValueError, TypeError, KeyError, OSError, AttributeError):
                    still_candidate, window = False, {}
                if not still_candidate:
                    save(
                        phase="TARGET",
                        cancel_id=None,
                        decision=window,
                        last_result="candidate_changed_before_cancel",
                    )
                    return s
            if proof.terminal:
                return wait("external_target_terminal_requires_owner_reconciliation")
            if owner_guard() is not True:
                return wait("owner_guard_blocked")
            # Recovery before the first registry reservation is safe. Never
            # replay a reserved, ambiguous, rejected or acknowledged cancel.
            adapter.cancel_owned_sell(current, quantity=left, action_id=s["cancel_id"])
            return s
        if row["state"] == "INTENT_REJECTED":
            save(
                phase="TARGET" if s["mode"] == "target" else "EXIT",
                disabled_for_target=True,
                last_result="cancel_rejected_original_order_retained",
            )
            return s
        if row["state"] not in {"ORDER_BOUND", "ORDER_TERMINAL"} or not row.get(
            "broker_order_no"
        ):
            return wait("cancel_ack_unresolved")
        child = OrderKey(row["order_date"], row["broker_order_no"])
        if not proof.terminal:
            return wait("cancel_ack_not_terminal")
        proof = adapter.reconcile_terminal_cancel(
            current, child, max_snapshot_age_ms=2000
        )
        if not proof.source_ok:
            return wait("cancel_confirmation_pending:" + proof.error)
        save(
            current_filled=proof.filled_qty, phase="READY", cancel_order=child.__dict__
        )
        return s
    if s["phase"] == "EXIT":
        if proof.terminal:
            return wait("replacement_terminal_requires_exact_cancel_proof")
        if (
            not candidate_authorized()
            or now - s["submitted_at"] >= policy["sell_ttl_sec"]
        ) and not s.get("disabled_for_target"):
            save(
                phase="EXIT_CANCEL",
                cancel_id=f"{FAMILY}:cancel:{s['policy_hash']}:{current.trading_date}:{current.order_no}",
            )
        return s
    if s["phase"] == "TARGET":
        if not candidate_authorized() or s.get("disabled_for_target") or proof.terminal:
            return wait("original_target_retained")
        try:
            source = quote()
            if source["executable_bid"] >= s["original_target"]:
                save(decision={})
                return wait("original_target_already_executable")
            result, window = evaluate(source, s["decision"])
        except (ValueError, TypeError, KeyError, OSError, AttributeError):
            save(decision={})
            return wait("fresh_executable_quote_required")
        save(decision=window, last_result=result["reason"])
        if result["should_exit"] and owner_guard() is True:
            save(
                phase="CANCEL",
                cancel_id=f"{FAMILY}:cancel:{s['policy_hash']}:{current.trading_date}:{current.order_no}",
            )
        return s
    if s["phase"] != "READY":
        raise ValueError("profit_exit_phase_invalid")
    # A failed/partial attempt returns to the original target, not an
    # unbounded sequence of lower prices or a market sell in a loss interval.
    price, mode = s["original_target"], "target"
    if s["mode"] == "target" and candidate_authorized() and not s.get("force_restore"):
        try:
            source = quote()
            result, _ = evaluate(source, s["decision"])
            if result.get("net_return_pct", 0) > 0 and result.get("should_exit"):
                price, mode = int(source["executable_bid"]), "supplement"
        except (ValueError, TypeError, KeyError, OSError, AttributeError):
            pass  # Original target restoration needs no synthetic market quote.
    if owner_guard() is not True:
        return wait("owner_guard_blocked_before_replacement")
    save(phase="SUBMITTING", next_price=price, next_mode=mode, submitted_at=now)
    ack = adapter.submit_owned_sell(
        current, quantity=left, limit_price=price, action_id=f"{FAMILY}:replacement"
    )
    if not ack.accepted and not ack.ambiguous:
        save(
            phase="READY",
            force_restore=True,
            last_result="replacement_rejected_restore_original_target",
        )
    return s
