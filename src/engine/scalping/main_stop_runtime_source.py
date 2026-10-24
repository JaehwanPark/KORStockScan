"""Pure receipts for actual Main stop evaluation stages; no execution authority.

A quote observation is not evidence that any stop rule ran. These receipts bind
an actual caller/stage to the original shared quote and its immutable policy.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import fields
from datetime import date, datetime
from itertools import count
import math
import os
import re
from uuid import uuid4

from .main_stop_policy import (
    StopValues,
    digest,
    finite,
    next_source_observation_generation,
)

EVALUATION_SCHEMA = "main_stop_evaluation_source_v1"
STAGES = {"preset_safety", "common_soft"}

# Only the pure source builders and their native identity/clock helpers consume
# this view. Quote contexts and prior source receipts have their own bounded
# capture in the caller; arbitrary trading state is never copied.
SOURCE_VIEW_KEYS = frozenset(
    {
        "id",
        "record_id",
        "code",
        "stock_code",
        "strategy",
        "status",
        "position_tag",
        "position_peak_cycle_id",
        "buy_time",
        "holding_started_at",
        "order_time",
        "entry_split_probe_filled_at",
        "scalp_holding_source_position_token",
        "scalp_live_simulator",
        "simulation_book",
        "buy_qty",
        "buy_price",
        "main_stop_policy_pin",
        "main_stop_pin_persistence",
        "main_stop_clock_unobserved",
        "_main_stop_typed_values",
        "_main_stop_position_key",
        "_main_stop_source_values",
        "manual_control_exclusion_blocked",
        "manual_control_hard_stop_handoff_pending",
        "manual_control_hard_stop_handoff_inflight",
        "exit_requested",
        "exit_token",
        "exit_mode",
        "hard_stop_pct",
        "hard_stop_emergency_pct",
        "hard_stop_grace_sec",
        "protect_profit_pct",
        "trailing_stop_price",
        "pyramid_count",
        "last_add_type",
        "add_count",
        "pending_add_qty",
        "pending_add_ord_no",
        "pending_add_order",
        "pending_add_ord_nos",
        "scale_in_submit_reserved_qty",
        "entry_cancel_terminal_reconciliation_required",
        "entry_reprice_cancel_terminal_pending",
        "owner_registry_reconciliation_required",
        "entry_partial_fill_deferred_notice",
        "post_add_economic_generation",
        "last_reversal_features",
        "reversal_add_state",
        "reversal_add_executed_at",
        "reversal_add_profit_floor",
        "reversal_add_used",
        "soft_stop_micro_grace_started_at",
        "_trailing_entry_cost_model",
        "_entry_receipt_filled_by_order_no",
        "_entry_receipt_executions_by_order_no",
        "_entry_receipt_requested_by_order_no",
        "_entry_receipt_filled_amount_by_order_no",
        "_entry_receipt_economics_complete_by_order_no",
        "holding_buy_fill_legs",
        "_add_receipt_filled_by_order_no",
        "_add_receipt_executions_by_order_no",
        "entry_filled_qty",
        "add_filled_qty",
        "initial_quantity_bundle",
        "initial_quantity_last_terminal_bundle",
        "_main_stop_quantity_source",
        "pending_entry_orders",
        "entry_requested_qty",
        "requested_buy_qty",
        "entry_split_probe_bundle_id",
        "entry_split_order_probe_first_applied",
        "entry_split_probe_requested_qty",
        "entry_split_probe_target_qty",
        "entry_split_probe_phase",
        "entry_split_probe_abort_reason",
        "entry_split_probe_partial_complete_qty",
        "holding_path_vote_ledger",
        "holding_vote_coverage_started_at",
        "holding_vote_coverage_checked_at",
        "holding_vote_coverage_birth_at",
        "holding_vote_coverage_pid",
        "holding_path_vote_store_gap",
        "holding_vote_coverage_store_gap",
        "holding_vote_coverage_generation",
        "main_stop_source_rejected_count",
        "main_stop_evaluation_rejected_count",
        "_main_stop_quote_generation",
        "_main_stop_evaluation_generation",
        "_main_stop_source_observation_generation",
        "_main_stop_observation_epoch",
        "_main_stop_evaluation_lane_generations",
    }
)
SOURCE_FEATURE_KEYS = frozenset(
    {
        "tick_context_quality",
        "tick_context_stale",
        "quote_stale",
        "tick_latest_age_ms",
        "quote_age_ms",
        "buy_pressure_10t",
        "net_aggressive_delta_10t",
        "large_sell_print_detected",
        "same_price_buy_absorption",
        "curr_vs_micro_vwap_bp",
        "micro_vwap_bp",
        "tick_aggressor_pressure_usable",
        "tick_aggressor_trusted_count",
        "micro_vwap_available",
        "minute_candle_window_fresh",
        "minute_candle_context_quality",
        "tick_acceleration_ratio",
    }
)

# Native quantity trees admit 4096 nodes/depth 12/256 children/1024 characters.
# A complete quote adds an envelope around that proof. The aggregate byte
# admission matches the existing bounded BUY runtime receipt (256 KiB), using
# an upper bound without JSON encoding, hashing, I/O or arbitrary __deepcopy__.
OBSERVATION_MAX_BYTES = 262144
OBSERVATION_MAX_NODES = 8192
OBSERVATION_MAX_DEPTH = 16
_ESCAPED_CHARACTERS = re.compile(r'[\x00-\x1f"\\\x7f-\U0010ffff]')
_OBSERVATION_EPOCHS = count(1)
EVALUATION_LANE_SCOPE = "native_evaluator_lifecycle_v1"
RUNTIME_SOURCE_PID = os.getpid()
RUNTIME_SOURCE_INCARNATION = uuid4().hex


def ensure_observation_epoch(stock):
    """Assign an in-process lifecycle ticket under the caller's state lock.

    Native lifecycle reset removes this field, including same-ID resets. The
    ticket is source concurrency metadata, not a broker/order identity or a
    persisted cross-process identity.
    """
    if type(stock) is not dict:
        raise ValueError("native_observation_stock_invalid")
    if "_main_stop_observation_epoch" not in stock:
        stock["_main_stop_observation_epoch"] = next(_OBSERVATION_EPOCHS)
    value = stock["_main_stop_observation_epoch"]
    if type(value) is not int or value <= 0:
        raise ValueError("native_observation_epoch_invalid")
    return value


def reserve_evaluation_lane(stock, view, evaluator):
    """Reserve one actual caller lane; keep original global IDs and clocks.

    The caller owns ENTRY_LOCK and reserves the global evaluation generation
    in the same section. Only two native evaluator lanes can exist. A complete
    counts vector lets consumers check global presence independently of the
    order imposed by the callers' original decision-clock arguments.
    """
    if (
        type(stock) is not dict
        or type(view) is not dict
        or stock is view
        or type(evaluator) is not str
        or evaluator not in ("normal", "fast")
    ):
        raise ValueError("native_evaluation_lane_invalid")
    epoch = stock.get("_main_stop_observation_epoch")
    if (
        type(epoch) is not int
        or epoch <= 0
        or view.get("_main_stop_observation_epoch") != epoch
    ):
        raise ValueError("native_evaluation_lane_epoch_invalid")
    prior = stock.get(
        "_main_stop_evaluation_lane_generations", {"normal": 0, "fast": 0}
    )
    if (
        type(prior) is not dict
        or set(prior) != {"normal", "fast"}
        or any(type(value) is not int or value < 0 for value in prior.values())
    ):
        raise ValueError("native_evaluation_lane_generation_invalid")
    identity = observation_source_identity(view)
    current = dict(prior)
    current[evaluator] += 1
    global_generation = stock.get("_main_stop_evaluation_generation")
    if type(global_generation) is not int or global_generation != sum(current.values()):
        raise ValueError("native_evaluation_lane_global_generation_unbound")
    stock["_main_stop_evaluation_lane_generations"] = current
    view["_main_stop_evaluation_lane_generations"] = dict(current)
    return dict(
        identity,
        evaluation_lane_generation=current[evaluator],
        evaluation_lane_generations=dict(current),
    )


def observation_source_identity(view):
    """Name this actual runtime/lifecycle scope; never infer a historical one."""
    epoch = view.get("_main_stop_observation_epoch") if type(view) is dict else None
    if type(epoch) is not int or epoch <= 0:
        raise ValueError("native_evaluation_lane_epoch_invalid")
    return dict(
        evaluation_lane_scope=EVALUATION_LANE_SCOPE,
        source_lifecycle_epoch=epoch,
        source_runtime_pid=RUNTIME_SOURCE_PID,
        source_runtime_incarnation=RUNTIME_SOURCE_INCARNATION,
    )


def _string_size(value):
    # Every escaped code point takes at most twelve ASCII bytes (a surrogate
    # pair); ordinary ASCII takes one. No serializer runs in the state lock.
    return 2 + len(value) + 11 * len(_ESCAPED_CHARACTERS.findall(value))


def _copy_observation_tree(value, budget, *, max_nodes, max_depth, path="$"):
    remaining = max_nodes
    failure = [path, type(value).__name__]

    def charge(size):
        budget[0] -= size
        if budget[0] < 0:
            raise ValueError("native_observation_budget_exceeded")

    def copy_value(item, depth=0, where=path):
        nonlocal remaining
        failure[:] = [where, type(item).__name__]
        remaining -= 1
        if remaining < 0 or depth > max_depth:
            raise ValueError("native_observation_budget_exceeded")
        kind = type(item)
        if kind is dict:
            if len(item) > 256:
                raise ValueError("native_observation_budget_exceeded")
            charge(2 + len(item) * 2)
            result = {}
            for key, child in item.items():
                if type(key) is not str or len(key) > 240:
                    raise ValueError("native_observation_key_invalid")
                failure[:] = [where + "." + key[:80], type(child).__name__]
                charge(_string_size(key))
                result[key] = copy_value(child, depth + 1, where + "." + key[:80])
            return result
        if kind in (list, tuple):
            if len(item) > 256:
                raise ValueError("native_observation_budget_exceeded")
            charge(2 + len(item))
            children = [
                copy_value(child, depth + 1, where + "[" + str(index) + "]")
                for index, child in enumerate(item)
            ]
            return tuple(children) if kind is tuple else children
        if kind is str:
            if len(item) > 1024:
                raise ValueError("native_observation_budget_exceeded")
            charge(_string_size(item))
        elif kind is int:
            charge(2 + item.bit_length() // 3)
        elif kind is float:
            if not math.isfinite(item):
                raise ValueError("native_observation_value_invalid")
            charge(32)
        elif item is None or kind is bool:
            charge(5)
        elif kind in (date, datetime):
            charge(128)
        elif kind is StopValues:
            for field in fields(StopValues):
                scalar = getattr(item, field.name)
                if type(scalar) not in (int, float) or not finite(scalar):
                    raise ValueError("native_observation_value_invalid")
                copy_value(scalar, depth + 1, where + "." + field.name)
        else:
            raise ValueError("native_observation_value_invalid")
        return item

    try:
        return copy_value(value)
    except ValueError as exc:
        # Preserve the failing input/type without serializing its value or
        # calling arbitrary repr/deepcopy hooks on the trading thread.
        raise ValueError(
            str(exc) + ":" + str(failure[0])[:120] + ":" + failure[1]
        ) from exc


def bounded_observation_copy(value):
    """Detach one source envelope under fixed admission limits; no authority."""
    return _copy_observation_tree(
        value,
        [OBSERVATION_MAX_BYTES],
        max_nodes=OBSERVATION_MAX_NODES,
        max_depth=OBSERVATION_MAX_DEPTH,
    )


def observation_view(stock):
    """Capture declared inputs while the caller holds its short state lock.

    The vote source consumes only each ledger row's persisted_at. Preserve that
    exact projection, including missing values, without copying AI responses or
    rewriting the original ledger. The native runtime tail admits 192 rows.
    Every other retained field is copied without interpreting its semantics.
    """
    if type(stock) is not dict:
        raise ValueError("native_observation_stock_invalid")
    budget = [OBSERVATION_MAX_BYTES]
    result = {}
    for key in SOURCE_VIEW_KEYS:
        if key not in stock:
            continue
        value = stock[key]
        if key == "pending_entry_orders":
            from .main_stop_quantity_source import order_source_projection

            value = order_source_projection(value)
        elif key in {"pending_add_order", "entry_partial_fill_deferred_notice"}:
            value = bool(value)  # Every native source consumer reads truthiness only.
        elif key == "last_reversal_features" and value is not None:
            if type(value) is not dict:
                raise ValueError(
                    "native_observation_feature_map_invalid:last_reversal_features"
                )
            value = {name: value[name] for name in SOURCE_FEATURE_KEYS if name in value}
        if key == "holding_path_vote_ledger" and value is not None:
            if (
                type(value) is not list
                or len(value) > 192
                or any(type(row) is not dict for row in value)
            ):
                raise ValueError("native_observation_vote_ledger_invalid")
            value = [
                {k: row[k] for k in ("persisted_at",) if k in row} for row in value
            ]
        budget[0] -= 2 + _string_size(key)
        result[key] = _copy_observation_tree(
            value, budget, max_nodes=4096, max_depth=12, path=key
        )
    return result


def reserve_observation_generations(
    stock, view, *, quote=False, evaluation=False, minimum=0
):
    """Reserve unique live counters under the caller's lock, before pure work.

    Validation is atomic: an invalid counter never partially mutates either
    mapping. A later builder failure leaves the reservation visible as a gap.
    Local builders receive reserved-1 and retain their existing increment API.
    """
    if (
        type(stock) is not dict
        or type(view) is not dict
        or stock is view
        or type(quote) is not bool
        or type(evaluation) is not bool
        or quote == evaluation
        or type(minimum) is not int
        or minimum < 0
    ):
        raise ValueError("native_observation_reservation_invalid")
    keys = (
        "_main_stop_quote_generation",
        "_main_stop_evaluation_generation",
        "_main_stop_source_observation_generation",
    )
    current = {key: stock.get(key, 0) for key in keys}
    if any(type(value) is not int or value < 0 for value in current.values()):
        raise ValueError("native_observation_generation_invalid")
    key = keys[0] if quote else keys[1]
    generation = current[key] + 1
    observation = max(current[keys[2]], minimum) + 1
    stock[key] = generation
    stock[keys[2]] = observation
    view[key] = generation - 1
    view[keys[2]] = observation - 1
    return {key: generation, keys[2]: observation}


PREDECESSOR_SCHEMA = "main_stop_evaluation_reference_v1"
PREDECESSOR_KEYS = (
    "evaluation_id",
    "source_sha256",
    "at",
    "evaluator",
    "stage",
    "position_key",
    "pin_sha256",
)


def evaluation_reference(receipt):
    if (
        not isinstance(receipt, dict)
        or receipt.get("schema") != EVALUATION_SCHEMA
        or receipt.get("source_sha256")
        != digest({k: v for k, v in receipt.items() if k != "source_sha256"})
        or receipt.get("stage") != "preset_safety"
        or receipt.get("evaluator") != "normal"
    ):
        raise ValueError("native_preset_predecessor_invalid")
    return dict(
        schema=PREDECESSOR_SCHEMA, **{key: receipt[key] for key in PREDECESSOR_KEYS}
    )


QUANTITY_REFERENCE_SCHEMA = "main_stop_quantity_reference_v1"
_QUANTITY_IDENTITY = (
    "generation_sha256",
    "status",
    "position_key",
    "quantity",
    "buy_basis_krw",
    "buy_fill_identity",
)


def _quantity_reference(current, quote, *, at):
    original = quote.get("quantity_source")
    if (
        not isinstance(original, dict)
        or current.get("status") not in {"full_fill", "settled_partial"}
        or original.get("schema") != "main_stop_quantity_source_v1"
        or original.get("source_sha256")
        != digest({k: v for k, v in original.items() if k != "source_sha256"})
        or any(not finite(original.get(k)) for k in ("known_at", "captured_at"))
        or not 0 < original["known_at"] <= original["captured_at"] <= at
        or original.get("allowed_runtime_apply") is not False
        or original.get("actual_order_submitted") is not False
        or any(current.get(key) != original.get(key) for key in _QUANTITY_IDENTITY)
        or current.get("proof") != original.get("proof")
    ):
        return current
    body = dict(
        schema=QUANTITY_REFERENCE_SCHEMA,
        quote_source_sha256=quote["source_sha256"],
        quantity_source_sha256=original["source_sha256"],
        observed_at=at,
        **{key: current[key] for key in _QUANTITY_IDENTITY},
        runtime_effect=False,
        allowed_runtime_apply=False,
        actual_order_submitted=False,
    )
    return dict(body, source_sha256=digest(body))


def resolve_quantity_source(receipt, quote, *, at):
    """Resolve only an exact existing quote proof; never repair an unknown one."""
    from .main_stop_quantity_source import validate_quantity_source

    identity = dict(
        position_key=quote["position_key"],
        at=at,
        quantity=quote["quantity"],
        buy_basis_krw=quote["buy_basis_krw"],
    )
    if not isinstance(receipt, dict):
        raise ValueError("quantity_terminal_source_missing")
    if receipt.get("schema") != QUANTITY_REFERENCE_SCHEMA:
        return receipt
    original = quote.get("quantity_source")
    if (
        quote.get("source_sha256")
        != digest({k: v for k, v in quote.items() if k != "source_sha256"})
        or receipt.get("source_sha256")
        != digest({k: v for k, v in receipt.items() if k != "source_sha256"})
        or receipt.get("observed_at") != at
        or receipt.get("quote_source_sha256") != quote.get("source_sha256")
        or not isinstance(original, dict)
        or receipt.get("quantity_source_sha256") != original.get("source_sha256")
        or any(receipt.get(key) != original.get(key) for key in _QUANTITY_IDENTITY)
        or any(
            receipt.get(key) is not False
            for key in (
                "runtime_effect",
                "allowed_runtime_apply",
                "actual_order_submitted",
            )
        )
        or not validate_quantity_source(original, **identity)
    ):
        raise ValueError("quantity_source_reference_unbound")
    return original


def evaluation_source(
    stock,
    *,
    quote_source,
    at,
    evaluator,
    stage,
    decision_price,
    decision_price_basis,
    decision_profit_pct,
    priority_status,
    preset_stop=None,
    preset_predecessor=None,
    legacy_broker_recovered=False,
    quote_max_age_sec=None,
    decision_inputs=None,
    seal=True,
):
    from .position_peak_ledger import position_cycle_id

    q = quote_source
    quote_supported = bool(
        isinstance(q, dict)
        and q.get("coverage_complete") is True
        and isinstance(q.get("item"), str)
        and q["item"]
        and isinstance(q.get("route"), str)
        and q["route"]
        and type(q.get("transport_epoch")) is int
        and q["transport_epoch"] > 0
        and finite(q.get("quote_at"))
        and q["quote_at"] > 0
        and finite(at)
        and finite(quote_max_age_sec)
        and quote_max_age_sec > 0
        and 0 <= at - q["quote_at"] <= quote_max_age_sec
        and finite(q.get("bid"))
        and q["bid"] > 0
    )
    if (
        not isinstance(q, dict)
        or q.get("schema") != "main_stop_source_v1"
        or q.get("source_sha256")
        != digest({k: v for k, v in q.items() if k != "source_sha256"})
        or q.get("position_key") != position_cycle_id(stock)
        or q.get("pin_sha256")
        != (stock.get("main_stop_policy_pin") or {}).get("pin_sha256")
        or q.get("quantity") != stock.get("buy_qty")
        or q.get("buy_basis_krw") != stock.get("buy_qty", 0) * stock.get("buy_price", 0)
        or type(q.get("coverage_complete")) is not bool
        or not finite(q.get("at"))
        or not finite(at)
        or not q["at"] <= at
        or not finite(quote_max_age_sec)
        or quote_max_age_sec <= 0
        or type(legacy_broker_recovered) is not bool
        or evaluator not in {"normal", "fast"}
        or stage not in STAGES
        or (stage == "common_soft" and evaluator != "normal")
        or priority_status not in {"reached", "blocked_legacy"}
        or (priority_status == "blocked_legacy" and stage != "preset_safety")
        or decision_price_basis not in {"mark_price", "executable_bid"}
        or not finite(decision_price)
        or decision_price <= 0
        or not finite(decision_profit_pct)
        or (decision_price_basis == "executable_bid" and decision_price != q["bid"])
    ):
        raise ValueError("native_stop_evaluation_binding_invalid")
    prior_generation = stock.get("_main_stop_evaluation_generation", 0)
    if type(prior_generation) is not int or prior_generation < 0:
        raise ValueError("native_stop_evaluation_generation_invalid")
    generation = prior_generation + 1
    from .main_stop_quantity_source import build_quantity_source

    quantity_source = _quantity_reference(build_quantity_source(stock, at=at), q, at=at)
    if stage == "common_soft" and (
        not isinstance(decision_inputs, dict)
        or any(
            type(decision_inputs.get(k)) is not bool
            for k in (
                "grace_enabled",
                "after_add",
                "handoff_enabled",
                "holding_ai_required",
            )
        )
    ):
        raise ValueError("native_soft_decision_inputs_missing")
    if stage == "preset_safety" and (
        not isinstance(decision_inputs, dict)
        or type(decision_inputs.get("handoff_enabled")) is not bool
    ):
        raise ValueError("native_preset_decision_inputs_missing")
    if preset_predecessor is not None:
        if preset_predecessor.get("schema") == EVALUATION_SCHEMA:
            preset_predecessor = evaluation_reference(preset_predecessor)
        if (
            set(preset_predecessor) != {"schema", *PREDECESSOR_KEYS}
            or preset_predecessor.get("schema") != PREDECESSOR_SCHEMA
            or preset_predecessor.get("at") != at
            or preset_predecessor.get("position_key") != q["position_key"]
            or preset_predecessor.get("pin_sha256") != q["pin_sha256"]
            or preset_predecessor.get("evaluator") != "normal"
            or preset_predecessor.get("stage") != "preset_safety"
        ):
            raise ValueError("native_preset_predecessor_invalid")
    anchor = dict(
        position_key=q["position_key"],
        pin_sha256=q["pin_sha256"],
        evaluator=evaluator,
        stage=stage,
        at=at,
        generation=generation,
    )
    body = dict(
        schema=EVALUATION_SCHEMA,
        evaluation_id=digest(anchor),
        evaluation_generation=generation,
        source_observation_generation=next_source_observation_generation(
            stock, minimum=q.get("source_observation_generation", 0)
        ),
        **{
            key: q[key]
            for key in (
                "position_key",
                "record_id",
                "role",
                "market",
                "pin_sha256",
                "source_stop_values",
                "parent_values_sha256",
                "quantity",
                "buy_basis_krw",
            )
        },
        evaluator=evaluator,
        decision_owner="main_scalping",
        stage=stage,
        rule_scope=[stage],
        at=at,
        decision_price=decision_price,
        decision_price_basis=decision_price_basis,
        decision_profit_pct=decision_profit_pct,
        decision_price_observation="native_gate_argument",
        independently_verified_mark_clock=False,
        quote_source_sha256=q["source_sha256"],
        quote_at=q["quote_at"],
        quote_binding_status="supported" if quote_supported else "source_gap",
        quote_observation_at=q["at"],
        quote_max_age_sec=quote_max_age_sec,
        quote_validated_at=at,
        legacy_broker_recovered=legacy_broker_recovered,
        route=q["route"],
        item=q["item"],
        transport_epoch=q["transport_epoch"],
        priority_status=priority_status,
        preset_stop=preset_stop,
        preset_predecessor=preset_predecessor,
        quantity_source=quantity_source,
        decision_inputs=deepcopy(decision_inputs),
        capture_rejected_count=stock.get("main_stop_source_rejected_count", 0),
        evaluation_rejected_count=stock.get("main_stop_evaluation_rejected_count", 0),
        runtime_effect=False,
        allowed_runtime_apply=False,
        actual_order_submitted=False,
    )
    stock["_main_stop_evaluation_generation"] = generation
    return dict(body, source_sha256=digest(body)) if seal else body
