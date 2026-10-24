"""Source-only bridge from an issued Main entry plan to trailing research.

Owns no order, subscription or writer. The existing entry pipeline persists
the receipt; native machine observations remain immutable. Missing successor
plans, depth, holding AI or forward observations are never reconstructed.
"""

from datetime import datetime
from zoneinfo import ZoneInfo
import json
import math
import re

from .pre_submit_delay_initial_policy import digest

SCHEMA = "main_trailing_entry_plan_source_v1"
MAX_BYTES = 32 * 1024
AUTHORITY = dict(
    actual_order_submitted=False,
    allowed_runtime_apply=False,
    runtime_effect=False,
    decision_authority="research_source_only",
)


def runtime_account_scope():
    """Local real-provider journal namespace, never a broker-number/token hash."""
    try:
        from src.trading.order.owner_custody_registry import broker_account_key
        from src.utils import kiwoom_utils

        if kiwoom_utils.KIWOOM_BASE_URL != "https://api.kiwoom.com":
            return None
        source = getattr(kiwoom_utils, "KIWOOM_BASE_URL_PROVENANCE", None)
        if (
            not isinstance(source, dict)
            or source.get("status") != "observed"
            or source.get("explicit_origin") is not True
            or source.get("credential_present") is not True
            or source.get("origin") != kiwoom_utils.KIWOOM_BASE_URL
        ):
            return None
        return digest(["broker_account", broker_account_key(require_explicit=True)])
    except (ValueError, RuntimeError, OSError, TypeError, AttributeError, ImportError):
        return None


def epoch(value):
    if isinstance(value, str):
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            raise ValueError("trailing_plan_clock_timezone_missing")
        value = parsed.timestamp()
    if type(value) not in (float, int) or not math.isfinite(value) or value <= 0:
        raise ValueError("trailing_plan_clock_invalid")
    return float(value)


def _sha(value):
    return isinstance(value, str) and re.fullmatch(r"[a-f0-9]{64}", value) is not None


def decode(value):
    if isinstance(value, str):
        if len(value.encode()) > MAX_BYTES:
            raise ValueError("trailing_plan_receipt_budget")
        value = json.loads(value)
    if not isinstance(value, dict) or len(json.dumps(value).encode()) > MAX_BYTES:
        raise ValueError("trailing_plan_receipt_shape")
    return value


def validate(value):
    from .entry_execution_sizing_plan import _content_sha256

    value = decode(value)
    if (
        value.get("schema") != SCHEMA
        or not _sha(value.get("receipt_sha256"))
        or value["receipt_sha256"]
        != digest({k: v for k, v in value.items() if k != "receipt_sha256"})
        or any(value.get(k) != v for k, v in AUTHORITY.items())
        or any(
            type(value.get(k)) is not bool
            for k in (
                "actual_order_submitted",
                "allowed_runtime_apply",
                "runtime_effect",
            )
        )
        or not _sha(value.get("machine_observation_sha256"))
        or not _sha(value.get("machine_bundle_sha256"))
        or not isinstance(value.get("evaluation_attempt_id"), str)
        or not value["evaluation_attempt_id"]
        or not isinstance(value.get("symbol"), str)
        or not isinstance(value.get("position_key"), str)
        or not value["position_key"]
    ):
        raise ValueError("trailing_plan_receipt_identity")
    known = epoch(value.get("known_at"))
    plan = value.get("execution_plan") or {}
    if (
        plan.get("valid") is not True
        or plan.get("stage") != "entry"
        or plan.get("action_owner") != "mechanistic_entry_adjudicator"
        or plan.get("action_receipt_id") != value["evaluation_attempt_id"]
        or plan.get("policy_bundle_hash") != value["machine_bundle_sha256"]
        or any(
            type(plan.get(k)) is not int or plan[k] < 0
            for k in ("total_qty", "immediate_qty", "deferred_probe_residual_qty")
        )
        or plan["total_qty"] <= 0
        or plan["immediate_qty"] <= 0
        or _content_sha256(plan) != value.get("execution_plan_sha256")
        or plan.get("quantity_conservation_holds") is not True
    ):
        raise ValueError("trailing_plan_execution_binding")
    cost = value.get("cost_model") or {}
    if (
        not _sha(cost.get("source_sha256"))
        or epoch(cost.get("known_at")) > known
        or type(cost.get("buy_cost_krw")) not in (int, float)
        or cost["buy_cost_krw"] != 0
        or type(cost.get("sell_cost_rate")) not in (int, float)
        or not math.isfinite(cost["sell_cost_rate"])
        or not 0 <= cost["sell_cost_rate"] < 0.05
        or cost.get("actual_broker_cost") is not False
    ):
        raise ValueError("trailing_plan_model_cost_invalid")
    return value


def capture(
    *,
    symbol,
    position_key,
    action_receipt,
    sizing_fields,
    cap_context,
    cost_model,
    entry_context,
    known_at,
    account_scope_sha256=None,
):
    """Freeze supplied, already-issued inputs; no data access or execution."""
    try:
        if (
            action_receipt.get("entry_mechanistic_action") != "ENTER_NOW"
            or action_receipt.get("entry_ai_screen_pass") is not True
            or sizing_fields.get("entry_execution_sizing_valid") is not True
        ):
            raise ValueError("trailing_plan_original_authority_missing")
        body = dict(
            schema=SCHEMA,
            symbol=str(symbol),
            position_key=position_key,
            evaluation_attempt_id=action_receipt.get("evaluation_attempt_id"),
            machine_observation_sha256=action_receipt.get("machine_observation_sha256"),
            machine_bundle_sha256=action_receipt.get("machine_bundle_sha256")
            or action_receipt.get("policy_bundle_hash"),
            known_at=epoch(known_at),
            execution_plan=sizing_fields.get("entry_execution_sizing_plan"),
            execution_plan_sha256=sizing_fields.get(
                "entry_execution_sizing_plan_sha256"
            ),
            ask_depth_source=(cap_context or {}).get("ask_depth_source"),
            cost_model=cost_model,
            entry_context=entry_context,
            account_scope_sha256=account_scope_sha256,
            **AUTHORITY,
        )
        # Round-trip detaches the mutable runtime dictionaries and validates
        # finite JSON before they are handed to the existing logger.
        body = json.loads(json.dumps(body, allow_nan=False))
        return validate({**body, "receipt_sha256": digest(body)})
    except (ValueError, TypeError, KeyError, AttributeError, OverflowError) as exc:
        return dict(
            schema=SCHEMA, status="source_gap", reason=str(exc)[:160], **AUTHORITY
        )


def clear(stock):
    """Clear diagnostic lineage at initial-submit and completed-position boundaries."""
    for key in ("_trailing_entry_plan_receipt_sha256", "_trailing_entry_plan_binding"):
        stock.pop(key, None)


def install(stock, receipt):
    clear(stock)
    if receipt.get("receipt_sha256"):
        stock["_trailing_entry_plan_receipt_sha256"] = receipt["receipt_sha256"]
        stock["_trailing_entry_plan_binding"] = dict(
            plan=receipt["receipt_sha256"],
            position_key=receipt["position_key"],
            plan_known_at=receipt["known_at"],
        )


def holding_link(
    stock,
    *,
    position_key,
    buy_fill_identity,
    known_at,
    account_scope_sha256=None,
    automatic_management_allowed=None,
):
    """Bind only the initial actual BUY generation; ADD/reentry never inherit it."""
    binding = stock.get("_trailing_entry_plan_binding")
    if not isinstance(binding, dict):
        return None
    try:
        bought = stock.get("buy_time")
        if isinstance(bought, str):
            bought = datetime.fromisoformat(bought)
        if isinstance(bought, datetime):
            # recommendation_history.buy_time is local-KST SQL DateTime.
            bought = (
                bought.replace(tzinfo=ZoneInfo("Asia/Seoul"))
                if bought.tzinfo is None
                else bought
            ).timestamp()
        bought = epoch(bought)
        if (
            position_key != binding["position_key"]
            or not _sha(buy_fill_identity)
            or binding["plan"] != stock.get("_trailing_entry_plan_receipt_sha256")
            or not epoch(binding["plan_known_at"]) <= bought <= epoch(known_at)
        ):
            raise ValueError("trailing_plan_holding_identity")
        generation = (buy_fill_identity, bought)
        if binding.get("generation") is None:
            binding["generation"] = generation
        elif tuple(binding["generation"]) != generation:
            raise ValueError("trailing_plan_holding_generation_changed")
        link = dict(
            schema="main_trailing_plan_holding_link_v2",
            plan_receipt_sha256=binding["plan"],
            position_key=position_key,
            buy_fill_identity=buy_fill_identity,
            first_buy_at=bought,
            known_at=epoch(known_at),
            account_scope_sha256=account_scope_sha256,
            buy_qty=stock.get("buy_qty"),
            buy_price=stock.get("buy_price"),
            entry_cost_model=stock.get("_trailing_entry_cost_model"),
            automatic_management_allowed=automatic_management_allowed,
            **AUTHORITY,
        )
        link["sha256"] = digest(link)
        return link
    except (ValueError, TypeError, KeyError, OverflowError):
        clear(stock)
        return None


def validate_holding_link(link, *, receipt, quote):
    link = decode(link)
    if (
        link.get("schema")
        not in {
            "main_trailing_plan_holding_link_v1",
            "main_trailing_plan_holding_link_v2",
        }
        or link.get("sha256")
        != digest({k: v for k, v in link.items() if k != "sha256"})
        or link.get("plan_receipt_sha256") != receipt["receipt_sha256"]
        or link.get("position_key") != receipt["position_key"]
        or not _sha(link.get("buy_fill_identity"))
        or any(link.get(k) != v for k, v in AUTHORITY.items())
        or any(
            type(link.get(k)) is not bool
            for k in (
                "actual_order_submitted",
                "allowed_runtime_apply",
                "runtime_effect",
            )
        )
        or epoch(link.get("known_at")) != epoch(quote.get("known_at"))
        or not epoch(receipt["known_at"])
        <= epoch(link.get("first_buy_at"))
        <= epoch(link["known_at"])
    ):
        raise ValueError("trailing_plan_holding_link_invalid")
    return link


def equivalent_holding_link(link, *, receipt, position, original, source):
    """Prove original holding inputs belong to this unchanged modeled entry.

    A record/BUY-generation alias alone does not make a hypothetical entry
    equivalent to the original position. Missing historical v2 context is a
    research gap, never permission to reuse a different AI question.
    """
    if link.get("schema") != "main_trailing_plan_holding_link_v2":
        raise ValueError("cf_holding_context_unobserved")
    if (
        not _sha(receipt.get("account_scope_sha256"))
        or link.get("account_scope_sha256") != receipt["account_scope_sha256"]
    ):
        raise ValueError("cf_holding_account_mismatch")
    if (
        link.get("automatic_management_allowed") is not True
        or original.get("automatic_management_allowed") is not True
        or original.get("owner") != "main"
    ):
        raise ValueError("cf_holding_custody_unproven")
    if (
        not isinstance(source, dict)
        or source.get("position_key") != link["position_key"]
        or source.get("buy_fill_identity") != link["buy_fill_identity"]
        or source.get("required") is not True
        or source.get("path_id", "EXIT_TRAILING_TP") != "EXIT_TRAILING_TP"
    ):
        raise ValueError("cf_holding_vote_identity_mismatch")
    if (
        epoch(link["first_buy_at"]) != position["entry_at"]
        or original.get("entry_at") != position["entry_at"]
    ):
        raise ValueError("cf_holding_entry_clock_mismatch")
    if (
        type(link.get("buy_qty")) is not int
        or link["buy_qty"] != position["qty"]
        or type(original.get("qty")) is not int
        or original["qty"] != position["qty"]
    ):
        raise ValueError("cf_holding_quantity_mismatch")
    price = link.get("buy_price")
    if (
        type(price) not in (int, float)
        or not math.isfinite(price)
        or price * link["buy_qty"] != position["buy_basis_krw"]
        or original.get("buy_basis_krw") != position["buy_basis_krw"]
    ):
        raise ValueError("cf_holding_basis_mismatch")
    if (
        original.get("route") != position["route"]
        or original.get("item") != position["item"]
    ):
        raise ValueError("cf_holding_route_mismatch")

    def cost(value):
        if not isinstance(value, dict):
            raise ValueError("cf_holding_cost_mismatch")
        # Preserve every original model field; only the supported ISO/epoch
        # clock normalization differs between the two existing consumers.
        normalized = {k: v for k, v in value.items() if k != "known_at_original"}
        normalized["known_at"] = epoch(normalized.get("known_at"))
        return normalized

    if cost(link.get("entry_cost_model")) != cost(position["cost_model"]) or cost(
        original.get("cost_model")
    ) != cost(position["cost_model"]):
        raise ValueError("cf_holding_cost_mismatch")
    return True


def model_entry(
    receipt,
    *,
    symbol,
    attempt,
    observation_sha,
    bundle_sha,
    route,
    signal_at,
    pass_at,
    as_of,
):
    """Model only a complete immediate plan against its frozen visible depth.

    Conditional probe/sequential successors need their own observed transitions.
    This model entry is neither a broker fill nor evidence of future AI decisions.
    """
    from .initial_quantity_policy import canonical_epoch
    from .entry_execution_sizing_plan import PRICE_OWNER

    value = validate(receipt)
    if (
        value["symbol"] != symbol
        or value["evaluation_attempt_id"] != attempt
        or value["machine_observation_sha256"] != observation_sha
        or value["machine_bundle_sha256"] != bundle_sha
    ):
        raise ValueError("trailing_plan_native_join_mismatch")
    known = epoch(value["known_at"])
    clock = max(known, epoch(signal_at), epoch(pass_at))
    if as_of is not None and clock > epoch(as_of):
        raise ValueError("trailing_plan_after_cutoff")
    depth, plan = value.get("ask_depth_source") or {}, value["execution_plan"]
    if not isinstance(depth, dict):
        raise ValueError("trailing_plan_depth_shape")
    observed = epoch(depth.get("observed_epoch"))
    if (
        depth.get("market_route") != route
        or not isinstance(depth.get("item"), str)
        or depth["item"].split("_", 1)[0] != symbol
        or type(depth.get("transport_epoch")) is not int
        or depth["transport_epoch"] < 0
        or depth.get("source_type") != "ws_0D_bound_snapshot"
        or observed > known
        or not 0 <= clock - observed <= 0.7
    ):
        raise ValueError("trailing_plan_depth_route_or_clock")
    legs, prices = plan.get("legs"), plan.get("price_candidates")
    if (
        not isinstance(legs, list)
        or not 1 <= len(legs) <= 16
        or not isinstance(prices, list)
        or len(prices) != len(legs)
        or any(
            not isinstance(leg, dict) or leg.get("execution_phase") != "immediate"
            for leg in legs
        )
        or any(not isinstance(price, dict) for price in prices)
        or plan.get("deferred_probe_residual_qty") != 0
    ):
        raise ValueError("trailing_plan_conditional_successor_unobserved")
    levels = depth.get("levels")
    if not isinstance(levels, list) or not 1 <= len(levels) <= 5:
        raise ValueError("trailing_plan_ask_depth_missing")
    remaining_depth = []
    previous = 0
    for row in levels:
        if not isinstance(row, dict):
            raise ValueError("trailing_plan_ask_depth_invalid")
        price, qty = row.get("price_krw"), row.get("quantity")
        if (
            type(price) is not int
            or price <= previous
            or type(qty) is not int
            or qty < 0
        ):
            raise ValueError("trailing_plan_ask_depth_invalid")
        remaining_depth.append([price, qty])
        previous = price
    total, amount = 0, 0
    for index, (leg, price_leg) in enumerate(zip(legs, prices), start=1):
        quantity = leg.get("qty")
        if (
            type(quantity) is not int
            or quantity <= 0
            or type(leg.get("leg_index")) is not int
            or leg["leg_index"] != index
            or not isinstance(leg.get("price_candidate_id"), str)
            or not leg["price_candidate_id"]
            or leg.get("price_candidate_id") != price_leg.get("price_candidate_id")
            or not isinstance(leg.get("price_leg_id"), str)
            or not leg["price_leg_id"]
            or leg["price_leg_id"] != price_leg.get("price_leg_id")
            or plan.get("price_policy_owner") != PRICE_OWNER
            or price_leg.get("source") != PRICE_OWNER
            or not _sha(price_leg.get("source_receipt_sha256"))
            or price_leg["source_receipt_sha256"]
            != plan.get("price_source_receipt_sha256")
            or price_leg.get("route") != route
            or canonical_epoch(price_leg.get("epoch")) != depth["transport_epoch"]
        ):
            raise ValueError("trailing_plan_leg_identity")
        # The runtime price owner emits a decimal epoch string, whereas the
        # native depth receipt retains its integer. Compare their strict
        # canonical identities without rewriting either original receipt.
        captured = epoch(price_leg.get("captured_at"))
        if captured > known or not 0 <= clock - captured <= 0.7:
            raise ValueError("trailing_plan_price_clock")
        limit = leg.get("numeric_price")
        order_type = price_leg.get("order_type_code")
        if order_type not in ("0", "00", "3", "03"):
            raise ValueError("trailing_plan_order_type_unmodeled")
        market = order_type in {"3", "03"}
        if (
            type(limit) is not int
            or limit < 0
            or (not market and limit == 0)
            or type(price_leg.get("numeric_price")) is not int
            or price_leg["numeric_price"] != limit
        ):
            raise ValueError("trailing_plan_limit_invalid")
        unfilled = quantity
        for level in remaining_depth:
            if not market and level[0] > limit:
                break
            filled = min(unfilled, level[1])
            amount += filled * level[0]
            level[1] -= filled
            unfilled -= filled
        if unfilled:
            raise ValueError("trailing_plan_full_entry_depth_unobserved")
        total += quantity
    if total != plan.get("total_qty") or total != plan.get("immediate_qty"):
        raise ValueError("trailing_plan_quantity_mismatch")
    cost = dict(value["cost_model"])
    cost["known_at_original"] = cost["known_at"]
    cost["known_at"] = epoch(cost["known_at"])
    return dict(
        entry_at=clock,
        qty=total,
        buy_basis_krw=amount,
        cost_model=cost,
        route=route,
        item=depth["item"],
        entry_context=value.get("entry_context"),
        execution_plan_sha256=value["execution_plan_sha256"],
        entry_depth_verified=True,
        entry_plan_receipt_sha256=value["receipt_sha256"],
        entry_model="frozen_visible_ask_depth_immediate_plan_v1",
    )
