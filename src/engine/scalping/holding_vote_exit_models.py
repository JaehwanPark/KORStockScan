"""Native completed-ADD generation and the existing POST_EVAL predicate.

Observation and replay only; no new exit rule, order, or account request.
"""

from .main_stop_policy import digest, finite
from .main_stop_replay import cost_known_epoch
from .position_peak_ledger import position_cycle_id


def post_add_failure(
    *,
    profit,
    floor,
    elapsed,
    eval_sec,
    feature_usable,
    large_sell_print,
    tick_acceleration,
):
    return (
        profit < floor - 0.05
        or (feature_usable and large_sell_print)
        or (feature_usable and tick_acceleration < 0.90)
    ) and elapsed < eval_sec


def record_generation(stock, receipt, *, at, completed):
    """Called by the existing authoritative ADD receipt consumer."""
    stock.pop("post_add_economic_generation", None)
    model = stock.get("_trailing_entry_cost_model") or {}
    known_at = cost_known_epoch(model.get("known_at"))
    qty, basis = stock.get("buy_qty"), stock.get("buy_price")
    if (
        not completed
        or receipt.get("economics_complete") is not True
        or stock.get("pending_add_type") != "AVG_DOWN"
        or type(qty) is not int
        or qty <= 0
        or not finite(basis)
        or basis <= 0
        or not finite(at)
        or known_at is None
        or known_at > at
        or not finite(model.get("buy_cost_krw"))
        or model["buy_cost_krw"] != 0
        or model.get("allocation")
        != "frozen_configured_round_trip_rate_on_sell_model_only"
        or not model.get("source_sha256")
    ):
        return None
    value = dict(
        schema="verified_post_add_generation_v1",
        position_key=position_cycle_id(stock),
        quantity=qty,
        buy_basis_krw=basis * qty,
        cost_source_sha256=model["source_sha256"],
        completed_at=at,
        add_receipt_sha256=digest(receipt),
        pending_add=False,
        partial_fill=False,
        cost_role="frozen_configured_model_not_actual_cost",
        actual_profit_verified=False,
    )
    value["sha256"] = digest(value)
    stock["post_add_economic_generation"] = value
    return value
